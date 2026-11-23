#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fault_inject.py — 四形态故障注入与恢复演练（可靠体验 / 运行稳定性专项）。

它做一件与"正常跑一遍"相反的事：**把输入 / 模板 / 依赖 / 契约四类形态逐个故意弄坏**，
然后照样跑主流程，只观测与判决有关的量——退出码、`status`、
`uncertainty[].scope`、`verify.ok`、`verify.errors[]/warnings[]`、
`check.py` 的失败门号、以及产物清单。据此回答三个问题：

1. 坏了以后**有没有人管**（机器可判的信号出现了吗）？
2. 管得**对不对**（是否按 SKILL.md 的决策规则降级，而不是抛栈或假装成功）？
3. 哪几条是**静默失败**（退出码 0、`status=success`、`uncertainty` 空，
   产物看起来完全正常，故障只在人读细节时才看得见）？

设计约束（与包内其它脚本一致）：
- 自定位（`os.path.dirname(__file__)`），任何 cwd 都可运行；
- **绝不写技能包**：每次注入都把技能根复制到 `--out` 下的沙箱副本，只改副本；
  被测脚本也用 `PYTHONDONTWRITEBYTECODE=1` 调用，包内不会落 `__pycache__`/`.pyc`；
- 只用 `main.py` / `check.py` 的**正规 CLI**（subprocess），不 import 包内模块，
  避免探针与被测对象耦合；只读产物，不修复产物；
- 报告里的路径一律相对化（技能根记作 `<SKILL_DIR>`、探针输出根记作 `<OUT>`），
  因此报告可以随包发布，不会泄漏本机绝对路径。

用法:
    python "$SKILL_DIR/scripts/fault_inject.py" [--out <目录>] [--json <report.json>]
                                               [--only F1-01,F2-*] [--timeout 300]
                                               [--list] [--clean]

退出码: 0 = 演练跑完（**不代表**所有注入都应失败，逐行期望见 --list）；
        1 = 探针自身出错（找不到 main.py / 无法复制沙箱 / 参数错误）。
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

sys.dont_write_bytecode = True  # 本脚本自身也不落 .pyc

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(HERE)
MAIN_PY = "scripts/main.py"
CHECK_PY = "scripts/check.py"

COPY_IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".git", ".venv", "venv")

# 静默失败的判据：故障存在，但下面这些**机器可判信号**一个都没出现。
SILENT_SIGNALS = ("exit!=0", "status=partial", "status=failed",
                  "uncertainty", "verify.ok=false", "rule-errors", "check_exit!=0")

# ----------------------------------------------------------------- 观测工具


def _rel(base: str, p: str) -> str:
    return os.path.relpath(p, base).replace("\\", "/")


def _mkdir(p: str) -> str:
    os.makedirs(p, exist_ok=True)
    return p


def _write_json(path: str, obj) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)


def _copy_skill(dst: str) -> str:
    """把技能根复制成沙箱副本（被测对象始终是副本，原包只读）。"""
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(SKILL_ROOT, dst, ignore=COPY_IGNORE)
    return dst


def _run(argv, cwd: str, env: dict, timeout: int):
    t0 = time.time()
    try:
        proc = subprocess.run(argv, cwd=cwd, env=env, timeout=timeout,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        rc, out, err = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        rc, out, err = None, b"", f"TIMEOUT after {timeout}s".encode("utf-8")
    dt = time.time() - t0
    dec = lambda b: b.decode("utf-8", errors="replace")  # noqa: E731
    return rc, dec(out), dec(err), round(dt, 3)


def _find_result(out_root: str):
    hits = glob.glob(os.path.join(out_root, "**", "result.json"), recursive=True)
    if not hits:
        return None
    hits.sort(key=lambda p: (os.path.basename(os.path.dirname(p)) == "failed", len(p)))
    return hits[0]


def _find_verify_report(out_root: str):
    hits = glob.glob(os.path.join(out_root, "**", "verify_report.json"), recursive=True)
    hits.sort(key=len)
    return hits[0] if hits else None


def _observe(out_root: str, rc, stdout: str, stderr: str, elapsed: float) -> dict:
    """只抽取与判决有关的可观测量；不修复、不推断。"""
    obs = {
        "exit": rc, "elapsed_s": elapsed,
        "result_json": None, "status": None, "extraction": None,
        "entities": None, "relations": None,
        "uncertainty_scopes": [], "verify_ok": None,
        "verify_errors": [], "verify_warnings": [],
        "export_kinds": [], "artifacts": [],
        "check_exit": None, "check_gates_false": [], "check_issues": None,
        "gates_false": [], "check_ok": None,
        "stdout_tail": stdout.strip().splitlines()[-1][:200] if stdout.strip() else "",
        "stderr_tail": stderr.strip().splitlines()[-1][:200] if stderr.strip() else "",
    }
    # main.py 会把交付摘要打成 JSON（含 gates/check_ok）——原样解析，不推断
    try:
        summary = json.loads(stdout)
        if isinstance(summary, dict) and "gates" in summary:
            obs["gates_false"] = sorted(k for k, v in (summary.get("gates") or {}).items() if not v)
            obs["check_ok"] = summary.get("check_ok")
            if summary.get("status") is not None:
                obs["status"] = summary.get("status")
            if summary.get("verify_ok") is not None:
                obs["verify_ok"] = summary.get("verify_ok")
            if summary.get("artifacts"):
                obs["artifacts"] = list(summary["artifacts"])
    except Exception:  # noqa: BLE001
        pass
    rp = _find_result(out_root)
    if rp:
        obs["result_json"] = _rel(out_root, rp)
        obs["artifacts"] = sorted(os.listdir(os.path.dirname(rp)))
        try:
            with open(rp, "r", encoding="utf-8") as fh:
                res = json.load(fh)
            obs["status"] = res.get("status")
            obs["extraction"] = res.get("extraction")
            obs["entities"] = len(res.get("entities") or [])
            obs["relations"] = len(res.get("relations") or [])
            obs["uncertainty_scopes"] = sorted({str(u.get("scope")) for u in
                                                (res.get("uncertainty") or []) if isinstance(u, dict)})
            v = res.get("verify") or {}
            if isinstance(v, dict):
                obs["verify_ok"] = v.get("ok")
                obs["verify_errors"] = sorted({str(e.get("rule")) for e in (v.get("errors") or [])
                                               if isinstance(e, dict)})
                obs["verify_warnings"] = sorted({str(w.get("rule")) for w in (v.get("warnings") or [])
                                                 if isinstance(w, dict)})
            oc = res.get("output_contract") or {}
            if isinstance(oc, dict):
                obs["export_kinds"] = sorted({str(e.get("kind")) for e in (oc.get("exports") or [])
                                              if isinstance(e, dict)})
        except Exception as exc:  # noqa: BLE001
            obs["status"] = f"<不可解析: {type(exc).__name__}>"
    vr = _find_verify_report(out_root)
    if vr and obs["verify_ok"] is None:
        try:
            with open(vr, "r", encoding="utf-8") as fh:
                v = json.load(fh)
            obs["verify_ok"] = v.get("ok")
            obs["verify_errors"] = sorted({str(e.get("rule")) for e in (v.get("errors") or [])
                                           if isinstance(e, dict)})
            obs["verify_warnings"] = sorted({str(w.get("rule")) for w in (v.get("warnings") or [])
                                             if isinstance(w, dict)})
        except Exception:  # noqa: BLE001
            pass
    return obs


def _silence(obs: dict) -> tuple:
    """返回 (是否静默失败, 命中的信号清单)。"""
    sig = []
    if obs.get("exit") not in (0, None):
        sig.append("exit!=0")
    if obs.get("status") in ("partial", "failed"):
        sig.append(f"status={obs['status']}")
    if obs.get("uncertainty_scopes"):
        sig.append("uncertainty")
    if obs.get("verify_ok") is False:
        sig.append("verify.ok=false")
    if obs.get("verify_errors") or obs.get("verify_warnings"):
        sig.append("rule-errors")
    if obs.get("check_exit") not in (None, 0):
        sig.append("check_exit!=0")
    return (not sig), sig


def _redact(text: str, roots) -> str:
    """把本机绝对路径换成占位符，报告可随包发布。"""
    if not text:
        return ""
    out = text
    for r in roots:
        if not r:
            continue
        for form in (r, r.replace("\\", "/"), r.replace("/", "\\")):
            out = out.replace(form, "<SKILL_DIR>" if "skill" in r.lower() else "<OUT>")
    home = os.path.expanduser("~")
    for form in (home, home.replace("\\", "/")):
        out = out.replace(form, "<HOME>")
    tmp = tempfile.gettempdir()
    for form in (tmp, tmp.replace("\\", "/")):
        out = out.replace(form, "<TMP>")
    out = re.sub(r"[A-Za-z]:[\\/][^\s\"'<>|]*", "<ABS_PATH>", out)
    return out


# ----------------------------------------------------------------- 注入语料

HEALTHY_CASE = {
    "case_id": "fault-lab-apparatus",
    "title": "故障演练用合成案例（非正式案例）",
    "figure_type": "apparatus",
    "canvas": {"width_mm": 320, "height_mm": 200},
    "text": "合成材料：物料经进料阀进入反应腔，反应腔由加热套控温，产物经出料阀进入收集瓶。",
    "entities": [
        {"id": "M1", "name": "原料气瓶", "kind": "material", "source": "task.md §1"},
        {"id": "D1", "name": "进料阀", "kind": "device", "source": "task.md §1"},
        {"id": "D2", "name": "反应腔", "kind": "device", "source": "task.md §2"},
        {"id": "D3", "name": "加热套", "kind": "device", "source": "task.md §2"},
        {"id": "D4", "name": "出料阀", "kind": "device", "source": "task.md §3"},
        {"id": "P1", "name": "产物收集瓶", "kind": "product", "source": "task.md §3"},
    ],
    "relations": [
        {"id": "R1", "from": "M1", "to": "D1", "kind": "flow", "source": "task.md §1"},
        {"id": "R2", "from": "D1", "to": "D2", "kind": "flow", "source": "task.md §1"},
        {"id": "R3", "from": "D3", "to": "D2", "kind": "connect", "source": "task.md §2"},
        {"id": "R4", "from": "D2", "to": "D4", "kind": "flow", "source": "task.md §3"},
        {"id": "R5", "from": "D4", "to": "P1", "kind": "flow", "source": "task.md §3"},
    ],
}

TEXT_ONLY_CASE = {
    "case_id": "fault-lab-textonly",
    "title": "故障演练：仅自由文本（非正式案例）",
    "figure_type": "flow",
    "canvas": {"width_mm": 300, "height_mm": 180},
    "text": "第一步 称量原料；第二步 升温反应；第三步 冷却结晶；第四步 过滤干燥；第五步 取样送检。",
}


def _specs():
    """注入表。expect_* 是**期望**（写死，不随实测变）；silent 是**期望**的静默与否。"""
    S = []
    add = lambda **kw: S.append(kw)  # noqa: E731

    # ---------------- F1 输入形态 ----------------
    add(id="F1-01", family="输入形态", name="case 文件不存在",
        inject="--case <不存在的路径>（文件与目录都不存在）",
        expect_exit=2, expect_status="（无 result.json）", expect_unc="（无）",
        expect_silent="否", kind="case_missing",
        note="输入都不存在，不应产出任何结果文件（D1）")
    add(id="F1-02", family="输入形态", name="case.json JSON 语法坏",
        inject="case.json 写成非法 JSON（多一个逗号）",
        expect_exit=1, expect_status="failed", expect_unc="pipeline",
        expect_silent="否", kind="raw_case",
        raw='{"case_id":"f1-02","entities":[,,,]}',
        note="兜底写 <out>/failed/result.json（D2/D19）")
    add(id="F1-03", family="输入形态", name="case.json 顶层类型不是对象",
        inject="case.json 内容是 JSON 数组 []",
        expect_exit=1, expect_status="failed", expect_unc="pipeline",
        expect_silent="否", kind="raw_case", raw="[]",
        note="类型错误同样走兜底失败路径，不应把数组当字典用")
    add(id="F1-04", family="输入形态", name="case.json 是空壳对象",
        inject='case.json 只有 {}, 无实体也无文本',
        expect_exit=3, expect_status="failed", expect_unc="relations",
        expect_silent="否", kind="obj_case", obj={"case_id": "f1-04"},
        note="空壳属于「输入不可用」，应诚实降级而不是给一张空图")
    add(id="F1-05", family="输入形态", name="只有自由文本、无结构化实体",
        inject="case.json 只给 text 字段（触发文本解构）",
        expect_exit=0, expect_status="success", expect_unc="relations",
        expect_silent="否", kind="obj_case", obj=TEXT_ONLY_CASE,
        note="文本解构本身不降级，但必须记 uncertainty[scope=relations]（D3）")
    add(id="F1-06", family="输入形态", name="关系端点指向不存在的实体（非孤儿）",
        inject="在健康案例里加一条 from=D2 to=NOPE 的关系（D2 另有连线）",
        expect_exit=0, expect_status="success", expect_unc="（无）",
        expect_silent="是", kind="obj_case", obj=None, mutate="dangling",
        note="断头关系被丢弃（verify.checks.no_dangling=true），但**不记 uncertainty**、"
             "不降级：SKILL.md 的 D3 承诺「记入 uncertainty」，实际只留关系条数差 —— "
             "本行为该口径缺口的实测证据，见 references/FAULT-MATRIX.md §4")
    add(id="F1-07", family="输入形态", name="断头关系导致实体失去全部连接（孤儿）",
        inject="新增一个只有一条断头关系的实体 D5（断头被丢弃后它没有连线）",
        expect_exit=0, expect_status="partial", expect_unc="orphan_entities",
        expect_silent="否", kind="obj_case", obj=None, mutate="dangling_orphan",
        note="D5→D6 串联生效：先丢断头，再由孤儿实体触发降级（与 F1-06 的对照行）")
    add(id="F1-08", family="输入形态", name="实体 id 重复",
        inject="两条实体用同一个 id",
        expect_exit=0, expect_status="partial", expect_unc="orphan_entities",
        expect_silent="否", kind="obj_case", obj=None, mutate="dup_id",
        note="重命名保唯一，改名后产生的孤儿实体必须记 uncertainty（D7→D6）")
    add(id="F1-09", family="输入形态", name="--merge 指向不存在的文件",
        inject="对健康案例追加 --merge <不存在的路径>",
        expect_exit=1, expect_status="failed", expect_unc="pipeline",
        expect_silent="否", kind="merge_missing",
        note="人工修正入口给错路径必须干净失败，不能静默忽略修正")
    add(id="F1-10", family="输入形态", name="--material 指向不存在的文件",
        inject="追加 --material <不存在的路径>（材料被引用但读不到）",
        expect_exit=0, expect_status="success", expect_unc="（无）",
        expect_silent="是", kind="material_missing",
        note="**静默**：缺失材料不进 sources、不记 uncertainty，只看 evidence 条数变少")
    add(id="F1-11", family="输入形态", name="--task 指向不存在的文件",
        inject="显式给一个不存在的 task.md 路径",
        expect_exit=0, expect_status="success", expect_unc="（无）",
        expect_silent="是", kind="task_missing",
        note="**静默**：任务书读不到时照样出图，无任何告警字段")

    # ---------------- F2 模板 / 资产形态 ----------------
    add(id="F2-01", family="模板形态", name="--palette 指向不存在的路径",
        inject="追加 --palette <不存在的路径>",
        expect_exit=0, expect_status="success", expect_unc="（无）",
        expect_silent="是", kind="palette_missing",
        note="**静默**：回落内置配色（layout.load_palette 的容错），无任何留痕")
    add(id="F2-02", family="模板形态", name="--palette 是坏 JSON",
        inject="--palette 指向写坏的 palette.json",
        expect_exit=0, expect_status="success", expect_unc="（无）",
        expect_silent="是", kind="palette_bad",
        note="**静默**：与 F2-01 同路径，坏文件被当成「没有自定义配色」")
    add(id="F2-03", family="模板形态", name="--palette 是空对象",
        inject="--palette 指向内容为 {} 的文件",
        expect_exit=0, expect_status="success", expect_unc="（无）",
        expect_silent="是（合理）", kind="palette_empty", silent_kind="benign",
        note="空对象与内置配色合并，行为不变（合法的「用默认值」写法）")
    add(id="F2-04", family="模板形态", name="--rules 指向不存在的路径",
        inject="追加 --rules <不存在的路径>",
        expect_exit=0, expect_status="success", expect_unc="（无）",
        expect_silent="是", kind="rules_missing",
        note="**静默**：规则集为空 ⇒ 连接语义审计整体空转（--rules 写错=没审）")
    add(id="F2-05", family="模板形态", name="--rules 是坏 JSON",
        inject="--rules 指向写坏的 connection_rules.json",
        expect_exit=0, expect_status="success", expect_unc="（无）",
        expect_silent="是", kind="rules_bad",
        note="**静默**：解析失败按「无规则」处理，审计静默通过")
    add(id="F2-06", family="模板形态", name="包内 templates/palette.json 被删",
        inject="在沙箱副本里删除 templates/palette.json 后运行",
        expect_exit=0, expect_status="success", expect_unc="（无）",
        expect_silent="是", kind="sandbox_delete", target="templates/palette.json",
        note="**静默**：回落代码内 DEFAULT_PALETTE，产物正常、无告警")
    add(id="F2-07", family="模板形态", name="包内 assets/connection_rules.json 被删",
        inject="在沙箱副本里删除 assets/connection_rules.json 后运行",
        expect_exit=0, expect_status="success", expect_unc="（无）",
        expect_silent="是", kind="sandbox_delete", target="assets/connection_rules.json",
        note="**静默**：规则资产缺失 ⇒ 审计空转，退出码仍为 0（与 F2-04 同因不同源）")
    add(id="F2-08", family="模板形态", name="包内 scripts/render_svg.py 被删",
        inject="在沙箱副本里删除 scripts/render_svg.py 后运行",
        expect_exit=None, expect_status="（无 result.json）", expect_unc="（无）",
        expect_silent="否", kind="sandbox_delete", target="scripts/render_svg.py",
        note="硬失败：模块级 import 失败 ⇒ 非零退出、无产物、无兜底结果（与静默类对照）")

    # ---------------- F3 依赖形态 ----------------
    add(id="F3-01", family="依赖形态", name="无 Pillow（PIL 导入失败）",
        inject="PYTHONPATH 前置一个 import 即抛 ImportError 的 PIL 影子模块",
        expect_exit=3, expect_status="partial", expect_unc="png,pdf",
        expect_silent="否", kind="shadow_dep", shadow="PIL",
        note="PNG 渲染失败按 D12 降级 partial 并记 scope=png；**连带发现**：reportlab 内部也 import "
             "PIL，所以 PDF 一起失败 ⇒ 两个导出件都缺失，契约门 G4 判失败、退出码 3")
    add(id="F3-02", family="依赖形态", name="无 reportlab（导入失败）",
        inject="PYTHONPATH 前置一个 import 即抛 ImportError 的 reportlab 影子模块",
        expect_exit=0, expect_status="partial", expect_unc="pdf",
        expect_silent="否", kind="shadow_dep", shadow="reportlab",
        note="PDF 失败按 D12 降级 partial 并记 scope=pdf；PNG 仍在 ⇒ G4 仍可通过（退出码 0）")
    add(id="F3-03", family="依赖形态", name="无中文字体（WINDIR 指向空目录）",
        inject="把 WINDIR 指向空目录，使 4 条 Windows 候选字体路径全部不存在",
        expect_exit=3, expect_status="success", expect_unc="fonts",
        expect_silent="否", kind="no_font", shadow=None,
        note="字体缺失只记 scope=fonts（D14：不改 status）⇒ status 仍 success；"
             "但 check.py 的 G10 把 scope=fonts 列为「降级不确定性」⇒ 退出码 3。"
             "两条口径冲突，见 references/FAULT-MATRIX.md §4（未改脚本）")

    # ---------------- F4 契约形态 ----------------
    add(id="F4-00", family="契约形态", name="[对照] 未注入的健康产物",
        inject="不注入，直接用主流程跑出来的 result.json 过 check.py",
        expect_exit=0, expect_status="success", expect_unc="（无）",
        expect_silent="否", kind="contract_noop", control=True,
        note="对照行（不计入静默统计）：证明后面每一行的失败都来自注入本身")
    add(id="F4-01", family="契约形态", name="output_contract 整段缺失",
        inject="从 result.json 删掉 output_contract 键",
        expect_exit=1, expect_status="（不改）", expect_unc="（不改）",
        expect_silent="否", kind="contract_mutate", mutate="drop_oc",
        note="契约门必须报 G2 并给出 issue（D17）")
    add(id="F4-02", family="契约形态", name="契约某段为 null",
        inject="把 output_contract.exports 置为 null",
        expect_exit=1, expect_status="（不改）", expect_unc="（不改）",
        expect_silent="否", kind="contract_mutate", mutate="null_exports",
        note="null 与「空列表」语义不同：null 必须判失败（D17）")
    add(id="F4-03", family="契约形态", name="契约四段都是空列表",
        inject="editable_sources/exports/data_mapping/element_traceability 全部置 []",
        expect_exit=1, expect_status="（不改）", expect_unc="（不改）",
        expect_silent="否", kind="contract_mutate", mutate="empty_lists",
        note="空列表本身合法，但交付物为零 ⇒ 必须被 G3/G4/G5/G6 拦下")
    add(id="F4-04", family="契约形态", name="契约字段类型不符（字符串）",
        inject='把 output_contract 换成字符串 "ok"',
        expect_exit=1, expect_status="（不改）", expect_unc="（不改）",
        expect_silent="否", kind="contract_mutate", mutate="oc_string",
        note="**退出码非 0 但方式不体面**：check.py 在 oc.get 处抛 AttributeError（str 没有 .get），"
             "只留栈、不给门号/issue 列表。不会假绿，但类型错时应给出可读门号 —— "
             "本行为检查器健壮性缺口的实测证据，见 references/FAULT-MATRIX.md §4")
    add(id="F4-05", family="契约形态", name="exports 指向不存在的文件",
        inject="把 exports[0].path 改成一个不存在的文件名",
        expect_exit=1, expect_status="（不改）", expect_unc="（不改）",
        expect_silent="否", kind="contract_mutate", mutate="export_path",
        note="产物清单必须与实际文件对得上（G4）")
    add(id="F4-06", family="契约形态", name="data_mapping 与实体数不一致",
        inject="从 data_mapping 删掉一行",
        expect_exit=1, expect_status="（不改）", expect_unc="（不改）",
        expect_silent="否", kind="contract_mutate", mutate="drop_dm",
        note="数据映射必须与实体一一对应（G5）")
    add(id="F4-07", family="契约形态", name="element_traceability 漏掉一个箭头",
        inject="删掉一条 element=arrow-* 的溯源行",
        expect_exit=1, expect_status="（不改）", expect_unc="（不改）",
        expect_silent="否", kind="contract_mutate", mutate="drop_et",
        note="每个实体与箭头都要有溯源行（G6）")
    add(id="F4-08", family="契约形态", name="status 自称 success 但校验未全绿",
        inject="把 verify_report.json 的 ok 改成 false，result.json 仍写 success",
        expect_exit=1, expect_status="（不改）", expect_unc="（不改）",
        expect_silent="否", kind="contract_mutate", mutate="dishonest",
        note="状态诚实性是硬门（G9/G10），必须拦住「看起来成功」")
    add(id="F4-09", family="契约形态", name="result.json 不可解析（被截断）",
        inject="把 result.json 截掉一半",
        expect_exit=1, expect_status="（不改）", expect_unc="（不改）",
        expect_silent="否", kind="contract_mutate", mutate="truncate",
        note="第一道门就不该放过坏 JSON（G1）")
    return S


# ----------------------------------------------------------------- 注入执行

def _healthy_source(spec: dict):
    """按 spec 造出注入用的 case.json 内容（obj/raw）。"""
    if spec.get("kind") == "obj_case" and spec.get("obj") is None:
        case = json.loads(json.dumps(HEALTHY_CASE))
        m = spec.get("mutate")
        if m == "dangling":
            case["relations"].append({"id": "R9", "from": "D2", "to": "NOPE", "kind": "flow",
                                      "source": "task.md §4"})
        elif m == "dangling_orphan":
            case["entities"].append({"id": "D5", "name": "备用旁路阀", "kind": "device",
                                     "source": "task.md §4"})
            case["relations"].append({"id": "R9", "from": "D5", "to": "NOPE", "kind": "flow",
                                      "source": "task.md §4"})
        elif m == "dup_id":
            case["entities"].append({"id": "D2", "name": "反应腔（重复 id）", "kind": "device",
                                     "source": "task.md §2b"})
        return case
    return spec.get("obj")


def _prepare(spec: dict, out_root: str):
    """为一条注入准备沙箱、输入与命令行。返回 (skill_dir, case_arg, extra_argv, env)。"""
    fid = spec["id"]
    work = _mkdir(os.path.join(out_root, fid))
    skill = _copy_skill(os.path.join(work, "skill"))
    inp = _mkdir(os.path.join(work, "in"))
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    extra = []
    case_arg = None
    kind = spec["kind"]

    if kind == "case_missing":
        case_arg = os.path.join(inp, "absent-case.json")
    elif kind == "raw_case":
        case_arg = os.path.join(inp, "case.json")
        with open(case_arg, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(spec["raw"])
    elif kind == "obj_case":
        case_arg = os.path.join(inp, "case.json")
        _write_json(case_arg, _healthy_source(spec))
    elif kind == "merge_missing":
        case_arg = os.path.join(inp, "case.json")
        _write_json(case_arg, HEALTHY_CASE)
        extra += ["--merge", os.path.join(inp, "absent-override.json")]
    elif kind == "material_missing":
        case_arg = os.path.join(inp, "case.json")
        _write_json(case_arg, HEALTHY_CASE)
        extra += ["--material", os.path.join(inp, "absent-material.md")]
    elif kind == "task_missing":
        case_arg = os.path.join(inp, "case.json")
        _write_json(case_arg, HEALTHY_CASE)
        extra += ["--task", os.path.join(inp, "absent-task.md")]
    elif kind in ("palette_missing", "palette_bad", "palette_empty"):
        case_arg = os.path.join(inp, "case.json")
        _write_json(case_arg, HEALTHY_CASE)
        if kind == "palette_missing":
            extra += ["--palette", os.path.join(inp, "absent-palette.json")]
        else:
            p = os.path.join(inp, "palette.json")
            with open(p, "w", encoding="utf-8", newline="\n") as fh:
                fh.write("{ broken palette" if kind == "palette_bad" else "{}")
            extra += ["--palette", p]
    elif kind in ("rules_missing", "rules_bad"):
        case_arg = os.path.join(inp, "case.json")
        _write_json(case_arg, HEALTHY_CASE)
        if kind == "rules_missing":
            extra += ["--rules", os.path.join(inp, "absent-rules.json")]
        else:
            p = os.path.join(inp, "rules.json")
            with open(p, "w", encoding="utf-8", newline="\n") as fh:
                fh.write("{ broken rules")
            extra += ["--rules", p]
    elif kind == "sandbox_delete":
        case_arg = os.path.join(inp, "case.json")
        _write_json(case_arg, HEALTHY_CASE)
        victim = os.path.join(skill, spec["target"])
        if os.path.isfile(victim):
            os.remove(victim)
        else:
            raise FileNotFoundError(f"沙箱内未找到注入目标: {spec['target']}")
    elif kind == "shadow_dep":
        case_arg = os.path.join(inp, "case.json")
        _write_json(case_arg, HEALTHY_CASE)
        shadow = _mkdir(os.path.join(work, "shadow"))
        pkg = _mkdir(os.path.join(shadow, spec["shadow"]))
        with open(os.path.join(pkg, "__init__.py"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write("raise ImportError('fault_inject: simulated missing dependency "
                     f"{spec['shadow']}')\n")
        env["PYTHONPATH"] = shadow + os.pathsep + env.get("PYTHONPATH", "")
    elif kind == "no_font":
        case_arg = os.path.join(inp, "case.json")
        _write_json(case_arg, HEALTHY_CASE)
        emptyroot = _mkdir(os.path.join(work, "no-fonts"))
        env["WINDIR"] = emptyroot
        env["SystemRoot"] = emptyroot
    elif kind.startswith("contract_"):
        case_arg = None
    else:
        raise ValueError(f"未知注入类型: {kind}")

    return skill, case_arg, extra, env


def _mutate_contract(target_dir: str, case_id: str, mutate: str) -> str:
    rp = os.path.join(target_dir, case_id, "result.json")
    with open(rp, "r", encoding="utf-8") as fh:
        txt = fh.read()
    if mutate == "truncate":
        with open(rp, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(txt[: max(20, len(txt) // 2)])
        return rp
    res = json.loads(txt)
    if mutate == "drop_oc":
        res.pop("output_contract", None)
    elif mutate == "null_exports":
        res.setdefault("output_contract", {})["exports"] = None
    elif mutate == "empty_lists":
        for k in ("editable_sources", "exports", "data_mapping", "element_traceability"):
            res.setdefault("output_contract", {})[k] = []
    elif mutate == "oc_string":
        res["output_contract"] = "ok"
    elif mutate == "export_path":
        ex = res["output_contract"]["exports"]
        if ex:
            ex[0]["path"] = "figure-not-there.png"
    elif mutate == "drop_dm":
        dm = res["output_contract"]["data_mapping"]
        if dm:
            dm.pop()
    elif mutate == "drop_et":
        et = res["output_contract"]["element_traceability"]
        idx = next((i for i, x in enumerate(et) if str(x.get("element", "")).startswith("arrow-")), None)
        if idx is not None:
            et.pop(idx)
    elif mutate == "dishonest":
        vp = os.path.join(target_dir, case_id, "verify_report.json")
        with open(vp, "r", encoding="utf-8") as fh:
            vr = json.load(fh)
        vr["ok"] = False
        vr.setdefault("errors", []).append({"rule": "fault_inject-simulated", "severity": "error"})
        _write_json(vp, vr)
        res["status"] = "success"
    _write_json(rp, res)
    return rp


def _run_preflight(skill: str, case_arg, extra, env, work, timeout):
    """在沙箱副本里跑 preflight.py（只读检查，不写产物）。返回 (exit, codes)。"""
    pf = os.path.join(skill, "scripts/preflight.py")
    if not os.path.isfile(pf) or not case_arg:
        return None, ["<n/a>"]
    if not os.path.isfile(case_arg):
        return None, ["<n/a：case 本身不存在>"]
    argv = [sys.executable, pf, "--case", case_arg, "--deps"]
    # 把 --rules/--palette/--task/--material/--merge 原样透给闸门
    i = 0
    while i < len(extra):
        if extra[i] in ("--rules", "--palette", "--task", "--material", "--merge"):
            argv += [extra[i], extra[i + 1]]
            i += 2
        else:
            i += 1
    rep = os.path.join(work, "preflight.json")
    argv += ["--json", rep]
    rc, so, se, _dt = _run(argv, cwd=work, env=env, timeout=timeout)
    codes = []
    try:
        with open(rep, "r", encoding="utf-8") as fh:
            obj = json.load(fh)
        codes = sorted({str(f.get("code")) for f in (obj.get("findings") or [])})
    except Exception:  # noqa: BLE001
        codes = ["<未产出可解析报告>"]
    return rc, codes


def run_probe(out_root: str, only=None, timeout: int = 300, use_preflight: bool = True) -> dict:
    if not os.path.isfile(os.path.join(SKILL_ROOT, MAIN_PY)):
        raise SystemExit(f"FATAL: 未找到 {MAIN_PY}（技能根解析错误？）")
    out_root = os.path.abspath(out_root)
    _mkdir(out_root)
    specs = _specs()
    if only:
        pats = [p.strip() for p in only.split(",") if p.strip()]
        specs = [s for s in specs if any(s["id"] == p or s["id"].startswith(p.rstrip("*"))
                                        for p in pats)]

    # 健康产物（契约族注入的基底）：只跑一次，落在 _healthy/
    healthy_root = _mkdir(os.path.join(out_root, "_healthy"))
    h_skill = _copy_skill(os.path.join(healthy_root, "skill"))
    h_in = _mkdir(os.path.join(healthy_root, "in"))
    h_case = os.path.join(h_in, "case.json")
    _write_json(h_case, HEALTHY_CASE)
    h_env = dict(os.environ)
    h_env["PYTHONDONTWRITEBYTECODE"] = "1"
    h_out = _mkdir(os.path.join(healthy_root, "out"))
    rc, so, se, dt = _run([sys.executable, os.path.join(h_skill, MAIN_PY),
                           "--case", h_case, "--out", h_out],
                          cwd=healthy_root, env=h_env, timeout=timeout)
    health = _observe(h_out, rc, so, se, dt)

    roots = (SKILL_ROOT, h_skill)
    rows = []
    for spec in specs:
        skill, case_arg, extra, env = _prepare(spec, out_root)
        rows.append((spec, skill, case_arg, extra, env))
    # 上面的循环只为准备；真正执行在这里（保持报告顺序与注入表一致）
    results = []
    for spec, skill, case_arg, extra, env in rows:
        fid = spec["id"]
        work = os.path.join(out_root, fid)
        main_py = os.path.join(skill, MAIN_PY)
        check_py = os.path.join(skill, CHECK_PY)
        out_dir = _mkdir(os.path.join(work, "out"))
        if spec["kind"].startswith("contract_"):
            target = _mkdir(os.path.join(work, "product"))
            shutil.copytree(os.path.join(healthy_root, "out"),
                            os.path.join(target, "out"), dirs_exist_ok=True)
            rp = _find_result(os.path.join(target, "out"))
            with open(rp, "r", encoding="utf-8") as fh:
                case_id = json.load(fh)["case_id"]
            if spec["kind"] == "contract_mutate":
                rp = _mutate_contract(os.path.join(target, "out"), case_id, spec["mutate"])
            rc, so, se, dt = _run([sys.executable, check_py, rp],
                                  cwd=work, env=env, timeout=timeout)
            obs = _observe(os.path.join(target, "out"), None, "", se, dt)
            obs["preflight_exit"] = None
            obs["preflight_codes"] = ["<n/a：契约形态由 check.py 负责>"]
            obs["check_exit"] = rc
            obs["stdout_tail"] = so.strip().splitlines()[-1][:200] if so.strip() else ""
            try:
                rep = json.loads(so)
                obs["check_gates_false"] = sorted(k for k, v in (rep.get("gates") or {}).items() if not v)
                obs["check_issues"] = len(rep.get("issues") or [])
            except Exception:  # noqa: BLE001
                obs["check_gates_false"] = ["<check.py 未输出可解析 JSON>"]
        else:
            pf_exit, pf_codes = (None, ["<已禁用>"])
            if use_preflight:
                pf_exit, pf_codes = _run_preflight(skill, case_arg, extra, env, work, timeout)
            argv = [sys.executable, main_py, "--case", case_arg, "--out", out_dir] + extra
            rc, so, se, dt = _run(argv, cwd=work, env=env, timeout=timeout)
            obs = _observe(out_dir, rc, so, se, dt)
            obs["preflight_exit"] = pf_exit
            obs["preflight_codes"] = pf_codes
        silent, signals = _silence(obs)
        contract_family = spec["kind"].startswith("contract_")
        observed_exit = obs.get("check_exit") if contract_family else obs.get("exit")
        results.append({
            "id": fid, "family": spec["family"], "name": spec["name"],
            "inject": spec["inject"], "note": spec["note"],
            "expect_exit": spec["expect_exit"], "expect_status": spec["expect_status"],
            "expect_uncertainty": spec["expect_unc"],
            "control": bool(spec.get("control")),
            "expect_silent": spec["expect_silent"].startswith("是"),
            "silent_kind": (spec.get("silent_kind", "defect")
                            if spec["expect_silent"].startswith("是") else None),
            "observed_silent": silent, "silent_signals": signals,
            "silent_matches_expectation": (True if spec.get("control")
                                           else silent == spec["expect_silent"].startswith("是")),
            "observed_exit": observed_exit,
            "exit_matches_expectation": (spec["expect_exit"] is None
                                         or observed_exit == spec["expect_exit"]),
            "observed": {
                "exit": obs.get("exit"), "status": obs.get("status"),
                "extraction": obs.get("extraction"),
                "entities": obs.get("entities"), "relations": obs.get("relations"),
                "uncertainty_scopes": obs.get("uncertainty_scopes"),
                "verify_ok": obs.get("verify_ok"),
                "verify_errors": obs.get("verify_errors"),
                "verify_warnings": obs.get("verify_warnings"),
                "export_kinds": obs.get("export_kinds"),
                "result_json": obs.get("result_json"),
                "artifacts": obs.get("artifacts"),
                "check_exit": obs.get("check_exit"),
                "check_gates_false": obs.get("check_gates_false"),
                "check_issues": obs.get("check_issues"),
                "gates_false": obs.get("gates_false"),
                "preflight_exit": obs.get("preflight_exit"),
                "preflight_codes": obs.get("preflight_codes"),
                "elapsed_s": obs.get("elapsed_s"),
                "stdout_tail": _redact(obs.get("stdout_tail") or "", roots),
                "stderr_tail": _redact(obs.get("stderr_tail") or "", roots),
            },
        })

    report = {
        "_doc": ("fault_inject.py 的实跑报告：四形态故障注入 → 期望行为 → 实测可观测量 → "
                 "是否静默失败。所有路径已相对化（技能根=<SKILL_DIR>，输出根=<OUT>），"
                 "报告可随包发布。本文件由脚本现场生成，不手工编辑数字。"),
        "probe": "scripts/fault_inject.py",
        "skill_root": "<SKILL_DIR>",
        "python": sys.version.split()[0],
        "platform": sys.platform,
        "timeout_s": timeout,
        "healthy_arm": {
            "exit": health.get("exit"), "status": health.get("status"),
            "entities": health.get("entities"), "relations": health.get("relations"),
            "export_kinds": health.get("export_kinds"),
            "uncertainty_scopes": health.get("uncertainty_scopes"),
            "verify_ok": health.get("verify_ok"),
            "artifacts": health.get("artifacts"),
            "stderr_tail": _redact(health.get("stderr_tail") or "", roots),
        },
        "summary": {
            "injections": len(results),
            "controls": sum(1 for r in results if r["control"]),
            "silent_observed": sum(1 for r in results
                                   if r["observed_silent"] and not r["control"]),
            "silent_expected": sum(1 for r in results
                                   if r["expect_silent"] and not r["control"]),
            "silent_defects": sum(1 for r in results
                                  if r["observed_silent"] and r.get("silent_kind") == "defect"),
            "silent_benign": sum(1 for r in results
                                 if r["observed_silent"] and r.get("silent_kind") == "benign"),
            "exit_mismatch": sum(1 for r in results if not r["exit_matches_expectation"]),
            "silent_mismatch": sum(1 for r in results if not r["silent_matches_expectation"]),
            "preflight_ran": sum(1 for r in results
                                 if r["observed"].get("preflight_exit") is not None),
            "preflight_caught": sum(1 for r in results
                                    if r["observed"].get("preflight_exit") in (1, 3)),
            "preflight_missed_silent_defects": sum(
                1 for r in results
                if r["observed_silent"] and r.get("silent_kind") == "defect"
                and r["observed"].get("preflight_exit") == 0),
        },
        "preflight_enabled": use_preflight,
        "rows": results,
    }
    return report


# ----------------------------------------------------------------- 打印

def _fmt(v) -> str:
    if v is None:
        return "—"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (list, tuple)):
        return ",".join(str(x) for x in v) if v else "—"
    return str(v)


def print_table(report: dict) -> None:
    print("=" * 100)
    print("fault_inject.py — 四形态故障注入演练（实测）")
    print(f"  python {report['python']} · {report['platform']} · "
          f"注入 {report['summary']['injections']} 条 · "
          f"静默失败 {report['summary']['silent_observed']} 条")
    h = report["healthy_arm"]
    print(f"  健康臂: exit={_fmt(h['exit'])} status={_fmt(h['status'])} "
          f"实体={_fmt(h['entities'])} 关系={_fmt(h['relations'])} 导出={_fmt(h['export_kinds'])} "
          f"verify.ok={_fmt(h['verify_ok'])}")
    print("=" * 100)
    hdr = (f"{'ID':6s} {'形态':4s} {'注入':30s} {'期望':4s} {'实测':4s} {'status':10s} "
           f"{'uncertainty':20s} {'闸门(PF)':9s} {'静默':4s}")
    print(hdr)
    print("-" * 100)
    for r in report["rows"]:
        o = r["observed"]
        pf = o.get("preflight_exit")
        pf_cell = "n/a" if pf is None else ("拦下" if pf in (1, 3) else "放过")
        print(f"{r['id']:6s} {r['family'][:2]:4s} {r['name'][:28]:30s} "
              f"{_fmt(r['expect_exit']):4s} {_fmt(r['observed_exit']):4s} "
              f"{_fmt(o['status'])[:10]:10s} "
              f"{_fmt(o['uncertainty_scopes'])[:20]:20s} {pf_cell:9s} "
              f"{('是' if r['observed_silent'] and not r['control'] else '否')}"
              f"{('*' if r.get('silent_kind') == 'benign' else '')}")
    print("-" * 100)
    print("静默 = 退出码 0 且 status≠partial/failed 且 uncertainty 空 且 verify.ok≠false "
          "且无规则告警 且 check 退出码 0（即：故障存在但没有任何机器可判信号）")
    s = report["summary"]
    print(f"期望静默 {s['silent_expected']} 条 · 实测静默 {s['silent_observed']} 条 · 与期望不符 "
          f"{s['silent_mismatch']} 条 · 退出码与期望不符 {s['exit_mismatch']} 条")
    print(f"静默中：缺陷型 {s['silent_defects']} 条 · 合理型 {s['silent_benign']} 条"
          f"（带 * = 合理型：空 palette 属文档化的合法写法）")
    print(f"preflight 提前拦住 {s['preflight_caught']} 条 / 实跑 {s['preflight_ran']} 条 · "
          f"仍被放过的静默缺陷 {s['preflight_missed_silent_defects']} 条")


def main(argv) -> int:
    ap = argparse.ArgumentParser(description="四形态故障注入与恢复演练（输入/模板/依赖/契约）")
    ap.add_argument("--out", default=None,
                    help="注入物与沙箱副本的落点（默认系统临时目录；不会写技能包）")
    ap.add_argument("--json", default=None, help="把机器可读报告写到该路径")
    ap.add_argument("--only", default=None, help="只跑部分注入，如 F1-01,F2-*")
    ap.add_argument("--timeout", type=int, default=300, help="单次被测量的超时秒数（默认 300）")
    ap.add_argument("--list", action="store_true", help="只打印注入表，不执行")
    ap.add_argument("--clean", action="store_true", help="先清掉输出目录里本探针自己的子目录")
    ap.add_argument("--no-preflight", action="store_true",
                    help="不跑 scripts/preflight.py（默认每条注入前都跑，记录闸门能否提前拦住）")
    args = ap.parse_args(argv)

    if args.list:
        for s in _specs():
            print(f"{s['id']}  {s['family']}  {s['name']}\n     注入: {s['inject']}\n"
                  f"     期望: 退出码={_fmt(s['expect_exit'])} status={s['expect_status']} "
                  f"uncertainty={s['expect_unc']} 静默={s['expect_silent']}")
        return 0

    out_root = args.out or os.path.join(tempfile.gettempdir(), "fault-inject-run")
    out_root = os.path.abspath(out_root)
    if args.clean and os.path.isdir(out_root):
        for name in os.listdir(out_root):
            if re.match(r"^(F\d|_)", name):
                victim = os.path.join(out_root, name)
                if os.path.isdir(victim):
                    shutil.rmtree(victim)
                else:
                    os.remove(victim)

    report = run_probe(out_root, only=args.only, timeout=args.timeout,
                       use_preflight=not args.no_preflight)
    print_table(report)
    if args.json:
        _write_json(os.path.abspath(args.json), report)
        print(f"\n机器可读报告已写入: {os.path.basename(args.json)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
