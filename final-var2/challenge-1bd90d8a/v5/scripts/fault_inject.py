#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fault_inject.py — 四形态故障注入台（输入 / 依赖模板 / 运行期依赖 / 契约）

设计意图
--------
"异常处理写了吗"这句话只能靠**证据**回答。本脚本把四类可能的故障
**逐个真的弄坏**，再跑一遍主流程，把**实测**的

    退出码 · result.json 是否存在 · status · error/uncertainty 落痕 · 关键字段值

记录下来，交给 `references/FAULT-MATRIX.md` 逐行对照"期望行为"。
凡实测与期望不符的（含**静默失败**：出了问题却仍报 completed），
一律在矩阵里标出来，不做粉饰。

四形态（与 references/FAULT-MATRIX.md 的 4 个族一一对应）
----------------------------------------------------------
  I*  输入形态      案例 JSON / 源数据表 / 材料文件本身损坏或缺失
  T*  模板形态      templates/*.json 缺失或损坏；style 预设名不存在
  D*  依赖形态      scripts/ 模块缺失、Pillow 不可导入、字体目录不可用
  K*  契约形态      output_contract 四形态 + 无契约 + 非法形态

隔离原则（很重要）
------------------
1. **绝不改调用者给定的包**：每一次注入都把包复制到 `--workdir` 下的独立目录，
   注入只发生在副本上。
2. **绝不在包里跑脚本**：所有 `main.py` 调用都以"临时的包副本"为 `$SKILL_DIR`，
   因此包内不会产生 `__pycache__`（打包预检硬门之一）。
3. 每次注入把临时副本删掉、只保留 `result.json` 快照与关键中间产物，
   磁盘占用 = 单份包大小 × 并发 1。

用法
----
    python scripts/fault_inject.py --src <skill-dir> --workdir <dir> [--out report.json]
                                   [--only I1,K2] [--keep] [--timeout 180]

  --src      被测 Skill 包的根目录（**只读**；缺省 = 本脚本的父目录）
  --workdir  包外工作目录（缺省 = 系统临时目录下的 fault_inject_work）
  --out      报告 JSON 路径（缺省 = <workdir>/fault_inject_report.json）
  --only     只跑指定编号（逗号分隔），便于定点复核
  --keep     保留每次注入的临时副本目录（默认删除，只留产物快照）
  --timeout  单次主流程超时秒数（缺省 180）

退出码语义（与包内其他脚本一致：1 = 用法/运行错误；2 = 有"结果与期望不符"）：
  0  全部用例"实测 == 期望"，且报告已写出
  2  至少一条用例实测与期望不符（**注入台自身的判定失败**，不是被测包的失败；
     逐条原因见报告 `mismatches`）
  1  用法错误 / 源目录不可读 / 写不出报告
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PKG_ROOT = os.path.dirname(HERE)
MAIN = os.path.join("scripts", "main.py")

# 统计里不当作"运行失败"的退出码集合（main.py 的合法语义：0/2/1）
VALID_EXITS = (0, 1, 2)


# ------------------------------------------------------------------ 小工具

def _jload(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def _jdump(path, obj):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _write_text(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def _read_text(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return f.read()


def pick(obj, dotted, default=None):
    """按 'a.b.c' 取值；任一层缺失返回 default。"""
    cur = obj
    for seg in str(dotted).split("."):
        if isinstance(cur, dict) and seg in cur:
            cur = cur[seg]
        elif isinstance(cur, list) and seg.isdigit() and int(seg) < len(cur):
            cur = cur[int(seg)]
        else:
            return default
    return cur


def _hits(result, needles):
    """在 uncertainty / error / spec_lint.errors 里找关键字（用于判定"有没有留痕"）。"""
    if not isinstance(result, dict):
        return []
    blob = json.dumps({
        "uncertainty": result.get("uncertainty"),
        "error": result.get("error"),
        "failed_figures": result.get("failed_figures"),
        "spec_lint": pick(result, "spec_lint.errors"),
        "environment": result.get("environment"),
        "status": result.get("status"),
    }, ensure_ascii=False)
    return [n for n in needles if n and n in blob]


# ------------------------------------------------------------ 注入原语

def rm_path(rel):
    def _f(pkg):
        p = os.path.join(pkg, rel)
        if os.path.isdir(p):
            shutil.rmtree(p)
        elif os.path.exists(p):
            os.remove(p)
        return f"删除 {rel}"
    return _f


def write_text(rel, text):
    def _f(pkg):
        p = os.path.join(pkg, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        _write_text(p, text)
        return f"重写 {rel}（{len(text)} 字符）"
    return _f


def patch_json(rel, fn):
    def _f(pkg):
        p = os.path.join(pkg, rel)
        obj = _jload(p)
        obj = fn(obj)
        _jdump(p, obj)
        return f"改写 {rel}"
    return _f


def write_case(fn):
    return patch_json(os.path.join("examples", "case.json"), fn)


def make_stub(rel, text):
    """在副本里放一个会遮蔽真实模块的 stub（依赖形态注入用）。"""
    return write_text(rel, text)


# ------------------------------------------------------------ 用例定义

def build_cases():
    """返回用例列表。每条含 id/family/title/inject/expect/run 参数。"""
    C = []

    # ---------------- I* 输入形态 ----------------
    C.append(dict(
        id="I1", family="input", title="case.json 整个不存在",
        inject=rm_path(os.path.join("examples", "case.json")),
        case_arg="<副本>/examples/case.json",
        expect=dict(exit=1, result_exists=True, status="failed",
                    must_include=[], note="入口异常 → 最小诚实信封 + exit 1"),
        needles=["No such file", "FileNotFoundError"],
    ))
    C.append(dict(
        id="I2", family="input", title="case.json 非法 JSON（尾随逗号，语法坏）",
        inject=write_text(os.path.join("examples", "case.json"),
                          '{"case_id": "fault-i2", "figures": [{"id": "f1", "type": "bar",},],}\n'),
        case_arg="<副本>/examples/case.json",
        expect=dict(exit=1, result_exists=True, status="failed",
                    note="JSON 解析失败 → 最小诚实信封 + exit 1"),
        needles=["JSONDecodeError", "Expecting"],
    ))
    C.append(dict(
        id="I3", family="input", title="源数据表 data.csv 被删除（材料缺失）",
        inject=rm_path(os.path.join("examples", "data.csv")),
        case_arg="<副本>/examples/case.json",
        expect=dict(exit=2, result_exists=True, status="partial",
                    note="数值图拿不到行 → SpecError → partial，且必须在 uncertainty/失败图里出现"),
        needles=["data.csv", "源数据为空", "fig-01"],
    ))
    C.append(dict(
        id="I4", family="input", title="data.csv 被清空（存在但 0 行）",
        inject=write_text(os.path.join("examples", "data.csv"), ""),
        case_arg="<副本>/examples/case.json",
        expect=dict(exit=2, result_exists=True, status="partial",
                    note="空表 → partial；不得报 completed"),
        needles=["源数据为空", "fig-01"],
    ))
    C.append(dict(
        id="I5", family="input", title="case.json 顶层是数组且含两个案例",
        inject=write_text(os.path.join("examples", "case.json"), ""),  # 占位，下面单独处理
        case_arg="<副本>/examples/case.json",
        expect=dict(exit=0, result_exists=True, status="completed",
                    note="数组取第一项（脚本兼容形态）→ 正常完成"),
        needles=[],
    ))
    C.append(dict(
        id="I6", family="input", title="case.json 合法但没有任何 figures / figure / figure_spec",
        inject=write_case(lambda o: {k: v for k, v in o.items()
                                     if k not in ("figures", "figure", "figure_spec")}),
        case_arg="<副本>/examples/case.json",
        expect=dict(exit=1, result_exists=True, status="failed",
                    note="案例没有任何图规格 → P8 起不臆造占位图：图规格为空列表，"
                         "如实写 uncertainty 并以 status=failed / exit 1 收口"
                         "（没有任何图产出正是 failed 的定义）。关键：既不得报 "
                         "completed（静默成功），也不得凭空画一张案例没要求的图"),
        needles=["图规格", "figures"],
    ))
    C.append(dict(
        id="I7", family="input", title="数据列名整体改错（x.column 指向不存在的列）",
        inject=patch_json(os.path.join("examples", "data.csv"), lambda s: s),  # 占位，下面单独处理
        case_arg="<副本>/examples/case.json",
        expect=dict(exit=2, result_exists=True, status="partial",
                    note="spec_lint E3 error → 生成门拦住 → partial；或降级后由 mapcheck 报 mismatch"),
        needles=["E3", "不存在"],
    ))

    # ---------------- T* 模板形态 ----------------
    C.append(dict(
        id="T1", family="template", title="templates/journal_styles.json 缺失",
        inject=rm_path(os.path.join("templates", "journal_styles.json")),
        case_arg="<副本>/examples/case.json",
        expect=dict(exit=0, result_exists=True, status="completed",
                    note="回退内置 DEFAULT_STYLE，继续出图；属有意的静默回退，不阻断交付"),
        needles=[],
    ))
    C.append(dict(
        id="T2", family="template", title="templates/journal_styles.json 内容损坏（非 JSON）",
        inject=write_text(os.path.join("templates", "journal_styles.json"), "{ this is not json "),
        case_arg="<副本>/examples/case.json",
        expect=dict(exit=0, result_exists=True, status="completed",
                    note="同 T1：解析异常被吞掉后回退内置默认 —— **静默**（未写入 uncertainty）"),
        needles=[],
    ))
    C.append(dict(
        id="T3", family="template", title="templates/entity_glossary.json 缺失（关系规则字典）",
        inject=rm_path(os.path.join("templates", "entity_glossary.json")),
        case_arg="<副本>/examples/case.json",
        expect=dict(exit=0, result_exists=True, status="completed",
                    note="回退内置关系规则表，机制图照常出图（有意回退）"),
        needles=[],
    ))
    C.append(dict(
        id="T4", family="template", title="templates/figure_map.schema.json 缺失（纯文档模板）",
        inject=rm_path(os.path.join("templates", "figure_map.schema.json")),
        case_arg="<副本>/examples/case.json",
        expect=dict(exit=0, result_exists=True, status="completed",
                    note="运行期不读取该文件（只作文档）→ 完全无影响；属**已知边界**，非缺陷"),
        needles=[],
    ))
    C.append(dict(
        id="T5", family="template", title="--style 指向不存在的预设名（拼错期刊名）",
        inject=lambda pkg: "不改包：以 --style nonexistent-journal 运行",
        case_arg="<副本>/examples/case.json",
        run=dict(style="nonexistent-journal"),
        expect=dict(exit=0, result_exists=True, status="completed",
                    note="回退 default；environment.style 如实记为传入值。"
                         "P3 修正后 additional uncertainty 会点名该预设名不是已知预设并列出可用预设"),
        needles=[],
    ))

    # ---------------- D* 依赖形态 ----------------
    C.append(dict(
        id="D1", family="dependency", title="scripts/chartkit.py 被删除（核心模块缺失）",
        inject=rm_path(os.path.join("scripts", "chartkit.py")),
        case_arg="<副本>/examples/case.json",
        expect=dict(exit=1, result_exists=False, status=None,
                    note="import 阶段即失败：不产出半成品 result.json；由调用方按退出码判定"),
        needles=["ModuleNotFoundError", "chartkit"],
    ))
    C.append(dict(
        id="D2", family="dependency", title="Pillow 不可导入（PIL 被 stub 遮蔽）",
        inject=make_stub(os.path.join("_stubs", "PIL", "__init__.py"),
                         'raise ImportError("fault_inject: PIL blocked on purpose")\n'),
        case_arg="<副本>/examples/case.json",
        env_extra={"PYTHONPATH": "<副本>/_stubs"},
        expect=dict(exit=1, result_exists=True, status="failed",
                    note="实测（非设计预期）：chartkit 由 HAS_PIL 优雅降级，但 "
                         "figcheck.py 顶层 from PIL import Image 未做保护 → 校验阶段抛 "
                         "ImportError → 整体 FATAL，只留下 6 键最小信封，"
                         "SVG/JSON 降级路径根本走不到。这是真实韧性缺口，"
                         "已在 FAULT-MATRIX.md 的【已知缺陷】中如实登记"),
        needles=["Pillow", "figcheck", "PIL"],
    ))
    C.append(dict(
        id="D3", family="dependency", title="字体目录不可用（FONT_PATHS 指向空目录）",
        inject=lambda pkg: "不改包：以 FONT_PATHS=<workdir>/empty_fonts 运行",
        case_arg="<副本>/examples/case.json",
        env_extra={"FONT_PATHS": "<workdir>/empty_fonts"},
        expect=dict(exit=0, result_exists=True, status="completed",
                    note="SVG 走回退字体族照常；PNG 若缺 CJK 记 warn；必须能在 environment.fonts 看到实测结果"),
        needles=[],
    ))
    C.append(dict(
        id="D4", family="dependency", title="scripts/extract.py 被删除（CP2 抽取模块缺失）",
        inject=rm_path(os.path.join("scripts", "extract.py")),
        case_arg="<副本>/examples/case.json",
        expect=dict(exit=1, result_exists=False, status=None,
                    note="同 D1：import 失败 → 无半成品结果，退出码 1"),
        needles=["ModuleNotFoundError", "extract"],
    ))

    # ---------------- K* 契约形态 ----------------
    C.append(dict(
        id="K1", family="contract", title="契约形态①：字段名列表 + 两个非法项（数字 / 空串）",
        inject=write_case(lambda o: {**o, "output_contract":
                                     ["case_id", "status", 12345, "", "uncertainty"]}),
        case_arg="<副本>/examples/case.json",
        expect=dict(exit=0, result_exists=True, status="completed",
                    note="跳过非法项，其余照常回显；缺失项按容器类型补值，禁 null"),
        needles=[],
        probe=["output_contract_applied", "status", "uncertainty"],
    ))
    C.append(dict(
        id="K2", family="contract", title="契约形态②：名称→类型，含未知类型名 'weirdtype'",
        inject=write_case(lambda o: {**o, "output_contract":
                                     {"case_id": "string", "status": "string",
                                      "extra_note": "weirdtype", "extra_list": "array",
                                      "extra_obj": "object", "extra_num": "number",
                                      "extra_flag": "boolean"}}),
        case_arg="<副本>/examples/case.json",
        expect=dict(exit=0, result_exists=True, status="completed",
                    note="未知类型退化为字符串容器 ""，其余按声明容器类型给默认值；禁 null"),
        needles=[],
        probe=["extra_note", "extra_list", "extra_obj", "extra_num", "extra_flag"],
    ))
    C.append(dict(
        id="K3", family="contract", title="契约形态③：嵌套 fields 列表（含非字符串项）",
        inject=write_case(lambda o: {**o, "output_contract":
                                     {"fields": ["case_id", "status", {"oops": 1}, "sources"]}}),
        case_arg="<副本>/examples/case.json",
        expect=dict(exit=0, result_exists=True, status="completed",
                    note="非字符串项跳过；合法项照常回显"),
        needles=[],
        probe=["sources", "status"],
    ))
    C.append(dict(
        id="K4", family="contract", title="契约形态④：嵌套 fields 映射（含未知类型）",
        inject=write_case(lambda o: {**o, "output_contract":
                                     {"fields": {"case_id": "string", "status": "string",
                                                 "custom_block": "object", "custom_rows": "array",
                                                 "custom_flag": "boolean", "custom_label": "string"}}}),
        case_arg="<副本>/examples/case.json",
        expect=dict(exit=0, result_exists=True, status="completed",
                    note="四种容器默认值各就各位；禁 null"),
        needles=[],
        probe=["custom_block", "custom_rows", "custom_flag", "custom_label"],
    ))
    C.append(dict(
        id="K5", family="contract", title="完全没有 output_contract（合法输入）",
        inject=write_case(lambda o: {k: v for k, v in o.items() if k != "output_contract"}),
        case_arg="<副本>/examples/case.json",
        expect=dict(exit=0, result_exists=True, status="completed",
                    note="output_contract_applied=false，且**不臆造**契约字段"),
        needles=[],
        probe=["output_contract_applied"],
    ))
    C.append(dict(
        id="K6", family="contract", title="契约形态非法：裸字符串（四形态之外）",
        inject=write_case(lambda o: {**o, "output_contract": "case_id,status,outputs"}),
        case_arg="<副本>/examples/case.json",
        expect=dict(exit=0, result_exists=True, status="completed",
                    note="非 dict / list 的契约不参与回显；P4 修正后 output_contract_applied=false "
                         "且 uncertainty 说明形态无法解释（此前会谎报 true）"),
        needles=["output_contract"],
        probe=["output_contract_applied"],
    ))
    C.append(dict(
        id="K7", family="contract", title="契约声明了本 Skill 不产出的字段（要求不做假映射）",
        inject=write_case(lambda o: {**o, "output_contract":
                                     {"case_id": "string", "status": "string",
                                      "raw_readme_text": "string", "video_preview": "array"}}),
        case_arg="<副本>/examples/case.json",
        expect=dict(exit=0, result_exists=True, status="completed",
                    note="给声明容器类型的空值 + 不编造内容；字段必须存在且非 null"),
        needles=[],
        probe=["raw_readme_text", "video_preview"],
    ))
    return C


# ---------------------------------------------------------- 特殊注入实现

def _inject_i5(pkg):
    """数组形态 + 第二个案例（用来验证'取第一项'）。"""
    o = _jload(os.path.join(pkg, "examples", "case.json"))
    second = dict(o)
    second["case_id"] = "should-be-ignored"
    second["figures"] = []
    _jdump(os.path.join(pkg, "examples", "case.json"), [o, second])
    return "把 case.json 改成 [example, 一个 case_id=should-be-ignored 的干扰项]"


def _inject_i7(pkg):
    """把两个面板的 x.column 改成不存在的列。"""
    def fn(o):
        for fig in o.get("figures") or []:
            if isinstance(fig, dict) and fig.get("type") == "panel":
                for sub in fig.get("panels") or []:
                    if isinstance(sub.get("x"), dict):
                        sub["x"]["column"] = "dose_typo_column"
        return o
    _jdump(os.path.join(pkg, "examples", "case.json"), fn(_jload(
        os.path.join(pkg, "examples", "case.json"))))
    return "把 panel 子图的 x.column 改成 dose_typo_column（不存在的列）"


SPECIAL_INJECTS = {"I5": _inject_i5, "I7": _inject_i7}


# ------------------------------------------------------------ 用例执行

def run_case(case, src, workdir, timeout, keep):
    cid = case["id"]
    cdir = os.path.join(workdir, "cases", cid)
    pkg = os.path.join(cdir, "pkg")
    if os.path.isdir(cdir):
        shutil.rmtree(cdir)
    os.makedirs(cdir, exist_ok=True)

    rec = {"id": cid, "family": case["family"], "title": case["title"]}

    # 1) 复制包副本（被注入对象永远是副本，源包只读）
    shutil.copytree(src, pkg)

    # 2) 注入
    if cid in SPECIAL_INJECTS:
        rec["injected"] = SPECIAL_INJECTS[cid](pkg)
    else:
        rec["injected"] = case["inject"](pkg)

    # 3) 组命令
    out_dir = os.path.join(cdir, "out")
    work_out = os.path.join(cdir, "work")
    case_arg = case["case_arg"].replace("<副本>", pkg)
    cmd = [sys.executable, os.path.join(pkg, MAIN), "--case", case_arg,
           "--out", out_dir, "--work", work_out]
    rprops = case.get("run") or {}
    if rprops.get("style"):
        cmd += ["--style", rprops["style"]]

    env = dict(os.environ)
    env.pop("MAIN_DEBUG", None)
    for k, v in (case.get("env_extra") or {}).items():
        env[k] = v.replace("<副本>", pkg).replace("<workdir>", workdir)
    if case["id"] == "D3":
        empty = os.path.join(workdir, "empty_fonts")
        os.makedirs(empty, exist_ok=True)

    rec["cmd"] = " ".join(f'"{c}"' if " " in c else c for c in cmd)
    rec["env_extra"] = {k: env[k] for k in (case.get("env_extra") or {})}

    # 4) 跑主流程（cwd 故意设为包外，验证自定位）
    try:
        cp = subprocess.run(cmd, cwd=cdir, env=env, capture_output=True,
                            timeout=timeout)
        rc = cp.returncode
        stdout = cp.stdout.decode("utf-8", "replace")
        stderr = cp.stderr.decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        rc, stdout, stderr = None, "", f"TIMEOUT after {timeout}s"

    rec["exit_code"] = rc
    # 只留最后一条 [main] 状态行与错误首行，避免把整包噪声抄进报告
    tail = [ln for ln in stdout.splitlines() if ln.startswith("[main]")]
    rec["stdout_tail"] = tail
    rec["stderr_head"] = "\n".join(stderr.splitlines()[:4])
    rec["timed_out"] = rc is None

    # 5) 读结果
    res_path = os.path.join(out_dir, "result.json")
    result = None
    if os.path.exists(res_path):
        try:
            result = _jload(res_path)
        except Exception as exc:
            rec["result_parse_error"] = f"{type(exc).__name__}: {exc}"
    rec["result_exists"] = os.path.exists(res_path)
    rec["status"] = pick(result, "status")
    rec["uncertainty_n"] = len(pick(result, "uncertainty", []) or [])
    rec["uncertainty_sample"] = (pick(result, "uncertainty", []) or [])[:3]
    rec["error"] = pick(result, "error")
    rec["output_contract_applied"] = pick(result, "output_contract_applied")
    rec["gates_all_pass"] = pick(result, "gates.all_pass")
    rec["top_keys_n"] = len(result) if isinstance(result, dict) else None
    rec["figure_files"] = sorted(
        [f for f in os.listdir(out_dir) if f.startswith("figure-")]
    ) if os.path.isdir(out_dir) else []
    rec["probe"] = {p: pick(result, p, "<absent>") for p in (case.get("probe") or [])}
    rec["needle_hits"] = _hits(result, case.get("needles") or [])

    # 6) 判定：实测 vs 期望
    exp = case["expect"]
    checks = {
        "exit": (rc == exp["exit"]),
        "result_exists": (rec["result_exists"] == exp["result_exists"]),
        "status": (rec["status"] == exp["status"]) if exp.get("status") else None,
    }
    rec["checks"] = checks
    rec["mismatches"] = [k for k, v in checks.items() if v is False]

    # 7) 清理临时副本（默认），只留 out/ 快照与本条记录
    if not keep:
        shutil.rmtree(pkg, ignore_errors=True)
    rec["pkg_kept"] = bool(keep)
    return rec


# ------------------------------------------------------------ 报告

def summarize(records):
    fams = {}
    for r in records:
        f = fams.setdefault(r["family"], {"n": 0, "exit_codes": {}, "silent_ok": 0})
        f["n"] += 1
        f["exit_codes"][str(r["exit_code"])] = f["exit_codes"].get(str(r["exit_code"]), 0) + 1
    return {
        "n_cases": len(records),
        "families": fams,
        "n_mismatch": sum(1 for r in records if r["mismatches"]),
        "mismatches": {r["id"]: r["mismatches"] for r in records if r["mismatches"]},
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="四形态故障注入台（输入/模板/依赖/契约）")
    ap.add_argument("--src", default=PKG_ROOT, help="被测 Skill 包根目录（只读）")
    ap.add_argument("--workdir", default=None,
                    help="包外工作目录（缺省 = 系统临时目录/fault_inject_work）")
    ap.add_argument("--out", default=None, help="报告 JSON 路径")
    ap.add_argument("--only", default=None, help="只跑这些编号（逗号分隔），如 I1,K2")
    ap.add_argument("--keep", action="store_true", help="保留注入后的临时副本")
    ap.add_argument("--timeout", type=int, default=180, help="单次主流程超时（秒）")
    args = ap.parse_args(argv)

    src = os.path.abspath(args.src)
    if not os.path.isfile(os.path.join(src, MAIN)):
        print(f"[fault] 不是 Skill 包（找不到 {MAIN}）：{src}", file=sys.stderr)
        return 1

    workdir = os.path.abspath(args.workdir) if args.workdir else os.path.join(
        tempfile.gettempdir(), "fault_inject_work")
    os.makedirs(workdir, exist_ok=True)
    out_path = os.path.abspath(args.out) if args.out else os.path.join(
        workdir, "fault_inject_report.json")

    cases = build_cases()
    if args.only:
        want = {s.strip() for s in args.only.split(",") if s.strip()}
        cases = [c for c in cases if c["id"] in want]
        if not cases:
            print(f"[fault] --only 没有任何匹配：{sorted(want)}", file=sys.stderr)
            return 1

    print(f"[fault] src={src}")
    print(f"[fault] workdir={workdir}")
    print(f"[fault] cases={len(cases)} -> {', '.join(c['id'] for c in cases)}")

    records = []
    for c in cases:
        rec = run_case(c, src, workdir, args.timeout, args.keep)
        records.append(rec)
        flag = "OK " if not rec["mismatches"] else "DIFF"
        print(f"[{flag}] {rec['id']:<3} exit={rec['exit_code']} "
              f"result={rec['result_exists']} status={rec['status']} "
              f"unc={rec['uncertainty_n']} — {rec['title']}")
        if rec["mismatches"]:
            print(f"        实测与期望不符：{rec['mismatches']} "
                  f"(expect exit={c['expect']['exit']} status={c['expect'].get('status')})")

    report = {
        "skill_dir": src,
        "workdir": workdir,
        "when": __import__("datetime").datetime.now().astimezone().isoformat(timespec="seconds"),
        "python": sys.version.split()[0],
        "cases": records,
        "summary": summarize(records),
    }
    try:
        _jdump(out_path, report)
    except Exception as exc:
        print(f"[fault] 写报告失败：{exc}", file=sys.stderr)
        return 1
    s = report["summary"]
    print(f"[fault] summary: cases={s['n_cases']} mismatch={s['n_mismatch']} "
          f"families={ {k: v['n'] for k, v in s['families'].items()} }")
    print(f"[fault] report -> {out_path}")
    return 2 if s["n_mismatch"] else 0


if __name__ == "__main__":
    sys.exit(main())
