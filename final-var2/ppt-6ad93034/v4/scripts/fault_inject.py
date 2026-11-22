# -*- coding: utf-8 -*-
"""fault_inject.py — 四族失败注入 + 恢复演练 + 留痕守卫（reliability 轴）。

三件事，全部**真跑**，不靠断言文档：

  1) **注入**（`--pkg <SKILL_DIR> --work <包外目录>`）
     把四族上游输入逐个故意弄坏——输入 / 模板 / 依赖 / 契约——对每个故障各跑一次
     真实的 `scripts/main.py`，记录 `exit` · `result.json.status` · `uncertainty`
     条数 · 留痕字段 · deck 是否可重开 · **是否静默失败**。

  2) **恢复**（`--with-recovery`）
     对每个故障再跑一次**恢复动作**（换回默认模板 / 显式 `--no-chart` / 修正输入 /
     去掉损坏的起始稿 ……），记录恢复后的 exit/status，用来证明"出了问题有出路"。
     无法由包内命令恢复的（环境缺件）如实标为 `unrecoverable`，不假装修好了。

  3) **守卫**（`--guard --out <一次运行的输出目录>`）
     在一次运行**之前**拦掉会硬崩的三类输入，**之后**核对产物是否留下该留的痕：
     结果页图表丢了却没 note、`change_records` 报了降级但 `uncertainty` 为空、
     `status=success` 却有降级记录……这三类正是注入台实测出来的**静默失败**。

判读口径（与 `references/failure-modes.md` §0 一致）：
    0 = success（产物齐备、G1–G8 通过、自检 all_pass）
    1 = partial（有降级/未核验项，且**逐条**写进 uncertainty）
    2 = 输入不可读（只写最小 status=failed result.json）

**为什么必须在包外跑**：脚本会执行被测 Skill，Python 会在被测包的 `scripts/`
下写 `__pycache__`，而平台预检会因此拒收整包。因此默认把被测包
**复制到 `<work>/pkgs/<id>/` 再执行**，原包保持只读干净。

用法:
  python fault_inject.py --list                        # 看故障表（不执行）
  python fault_inject.py --pkg "$SKILL_DIR" --work <包外目录>
  python fault_inject.py --pkg "$SKILL_DIR" --work <包外目录> --with-recovery
  python fault_inject.py --pkg "$SKILL_DIR" --work <包外目录> --shape contract
  python fault_inject.py --pkg "$SKILL_DIR" --work <包外目录> --only F-IN-07,F-DEP-03
  python fault_inject.py --guard --pkg "$SKILL_DIR" --case /input/case.json   # 运行前体检
  python fault_inject.py --guard --out /app/output                           # 运行后核对

退出码: 0 = 全部故障的实测行为与期望一致（且守卫未发现静默失败）；1 = 有偏差/有发现；
        2 = 环境不可用（找不到 SKILL.md、--work 落在包内、--guard 用法错误）。
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PKG = os.path.dirname(HERE)          # 上一级 = 技能根目录（含 SKILL.md）

BASE_CASE = "examples/case.json"
BASE_TASK = "examples/task.md"
BASE_MATERIAL = "examples/material.md"
BASE_CSV = "examples/results.csv"

SHAPES = ("input", "template", "dependency", "contract")
EXIT_OK, EXIT_PARTIAL, EXIT_UNREADABLE = 0, 1, 2

# 恢复动作的三种结局
REC_FIXED = "recovered"            # 恢复命令跑通、状态回到 success/预期
REC_STILL_BAD = "still-degraded"   # 跑通了但仍是 partial（可接受，只要留痕）
REC_IMPOSSIBLE = "unrecoverable"   # 环境缺件，包内命令无法恢复（如实标注）


# ---------------------------------------------------------------------------
# 基础工具
# ---------------------------------------------------------------------------

def read_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_text(path, text):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def dump_json(path, obj):
    write_text(path, json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def copy_pkg(src, dst):
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return dst


def _run(cmd, env=None, timeout=300):
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, env=env, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, timeout=timeout)
        rc, out = proc.returncode, proc.stdout.decode("utf-8", errors="replace")
    except subprocess.TimeoutExpired as e:
        rc, out = "timeout", (e.stdout or b"").decode("utf-8", errors="replace")
    return rc, out, time.time() - t0


_ABS_RE = None


def sanitize(text, limit=48):
    """把机器绝对路径压成占位符（报告要能随包分发，不能带本机路径）。"""
    global _ABS_RE
    import re
    if _ABS_RE is None:
        _ABS_RE = re.compile(r"[A-Za-z]:[\\/][^\s'\"]*")
    text = _ABS_RE.sub("<path>", str(text))
    text = text.replace("\\", "/")
    return text[:limit]


def _trace_blob(out_dir):
    """把一次运行留下的所有可读痕迹拼起来（用于点名字段检索，不用于判静默）。"""
    parts = []
    for rel in ("result.json", "manifest.json", "evidence_map.json", "changelog.jsonl"):
        p = os.path.join(out_dir, rel)
        if os.path.isfile(p):
            try:
                parts.append(read_text(p))
            except Exception:  # noqa: BLE001
                pass
    logdir = os.path.join(out_dir, "logs")
    if os.path.isdir(logdir):
        for name in sorted(os.listdir(logdir)):
            try:
                parts.append(read_text(os.path.join(logdir, name)))
            except Exception:  # noqa: BLE001
                pass
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# 观测：只认**结构化字段**，不靠裸文本匹配（裸匹配会把键名当成留痕）
# ---------------------------------------------------------------------------

def observe(out_dir):
    obs = {"has_result": False, "status": None, "top_keys": 0,
           "uncertainty": 0, "unverified": 0, "material_warnings": 0,
           "change_records": 0, "slide_count": 0, "reopenable": None,
           "preview_warnings": 0, "degraded_figures": 0, "figures_without_note": 0,
           "spec_lint_problems": 0, "gate_errors": 0, "gate_valid": None,
           "error_field": "", "contract_fields": [], "notes": []}
    p = os.path.join(out_dir, "result.json")
    if not os.path.isfile(p):
        obs["notes"].append("没有 result.json（运行在写结果前退出）")
        return obs
    obs["has_result"] = True
    try:
        r = load_json(p)
    except Exception as e:  # noqa: BLE001
        obs["notes"].append("result.json 无法解析: %s" % e)
        return obs
    if not isinstance(r, dict):
        obs["notes"].append("result.json 顶层不是对象: %s" % type(r).__name__)
        return obs
    obs["top_keys"] = len(r)
    obs["status"] = r.get("status")
    obs["error_field"] = str(r.get("error") or "")[:120]
    obs["uncertainty"] = len(r.get("uncertainty") or [])
    obs["change_records"] = len(r.get("change_records") or [])
    deck = r.get("deck") or {}
    obs["slide_count"] = deck.get("slide_count") or 0
    ev = r.get("evidence") or {}
    obs["unverified"] = len(ev.get("unverified_claims") or [])
    obs["material_warnings"] = len(ev.get("material_warnings") or [])
    obs["preview_warnings"] = len((r.get("previews") or {}).get("warnings") or [])
    for sl in (deck.get("slides") or []):
        fig = sl.get("figure") or {}
        kind = fig.get("kind") or "none"
        if kind == "table" and fig.get("note"):
            obs["degraded_figures"] += 1
        if kind == "none" and (sl.get("claims") or []) and not fig.get("note"):
            obs["figures_without_note"] += 1
    meta = r.get("run_meta") or {}
    obs["spec_lint_problems"] = len(((meta.get("spec_lint") or {}).get("problems")) or [])
    gate = meta.get("gate") or {}
    obs["gate_valid"] = gate.get("valid")
    obs["gate_errors"] = len(gate.get("errors") or [])
    editable = deck.get("editable") or ""
    if editable:
        dp = editable if os.path.isabs(editable) else os.path.join(out_dir, editable)
        try:
            from pptx import Presentation
            obs["reopenable"] = len(Presentation(dp).slides._sldIdLst)
        except Exception as e:  # noqa: BLE001
            obs["reopenable"] = "FAILED: %s" % e
    return obs


def trace_hits(fault, obs, blob):
    """留痕判定：**结构化字段非空**才算留痕；只有模块名/键名出现在文本里不算。"""
    hits = [k for k in (fault.get("expect_trace") or ())
            if k and k in blob and k.startswith(("G2 ", "widget", "score", "extras"))]
    if obs.get("uncertainty"):
        hits.append("uncertainty=%d" % obs["uncertainty"])
    if obs.get("material_warnings"):
        hits.append("material_warnings=%d" % obs["material_warnings"])
    if obs.get("unverified"):
        hits.append("unverified_claims=%d" % obs["unverified"])
    if (obs.get("change_records") or 0) > 1:
        hits.append("change_records=%d" % obs["change_records"])
    if obs.get("preview_warnings"):
        hits.append("previews.warnings=%d" % obs["preview_warnings"])
    if obs.get("degraded_figures"):
        hits.append("figure.degraded=%d" % obs["degraded_figures"])
    if obs.get("spec_lint_problems"):
        hits.append("spec_lint.problems=%d" % obs["spec_lint_problems"])
    if obs.get("gate_errors"):
        hits.append("gate.errors=%d" % obs["gate_errors"])
    if obs.get("has_result") and obs.get("gate_valid") is False:
        hits.append("gate.invalid")
    if obs.get("error_field"):
        hits.append("error=%s" % sanitize(obs["error_field"]))
    if "Traceback" in blob:
        hits.append("Traceback")
    return hits


# ---------------------------------------------------------------------------
# case.json 变形器（注入侧）
# ---------------------------------------------------------------------------

def _base_case(pkg):
    return load_json(os.path.join(pkg, BASE_CASE))


def _copy_base_materials(case_dir, pkg=None):
    pkg = pkg or DEFAULT_PKG
    for name, src in (("material.md", BASE_MATERIAL), ("task.md", BASE_TASK),
                      ("results.csv", BASE_CSV)):
        write_text(os.path.join(case_dir, name), read_text(os.path.join(pkg, src)))


def _mutate(build, pkg, case_dir, work_dir):
    return build(_base_case(pkg), case_dir, work_dir, pkg)


# --- 输入族 ---

def b_case_missing(base, case_dir, work_dir, pkg):
    return os.path.join(case_dir, "no-such-case.json")


def b_case_broken_json(base, case_dir, work_dir, pkg):
    p = os.path.join(case_dir, "case.json")
    write_text(p, '{\n  "case_id": "fault-broken-json",\n  "title": "半截 JSON"\n')
    return p


def b_case_not_object(base, case_dir, work_dir, pkg):
    p = os.path.join(case_dir, "case.json")
    dump_json(p, ["这不是一个对象，而是一个数组"])
    return p


def b_case_null(base, case_dir, work_dir, pkg):
    p = os.path.join(case_dir, "case.json")
    write_text(p, "null\n")
    return p


def b_case_no_material(base, case_dir, work_dir, pkg):
    case = json.loads(json.dumps(base))
    case["case_id"] = "fault-missing-material"
    case["inputs"]["material"] = ["does-not-exist.md"]
    p = os.path.join(case_dir, "case.json")
    dump_json(p, case)
    return p


def b_material_empty(base, case_dir, work_dir, pkg):
    case = json.loads(json.dumps(base))
    case["case_id"] = "fault-empty-material"
    p = os.path.join(case_dir, "case.json")
    dump_json(p, case)
    write_text(os.path.join(case_dir, "material.md"), "")
    _copy_base_materials(case_dir, pkg)
    write_text(os.path.join(case_dir, "material.md"), "")
    return p


def b_material_swap(base, case_dir, work_dir, pkg):
    """材料文件被换成与声明用途不符的内容（CSV 位置放散文）。"""
    case = json.loads(json.dumps(base))
    case["case_id"] = "fault-swapped-material"
    p = os.path.join(case_dir, "case.json")
    dump_json(p, case)
    _copy_base_materials(case_dir, pkg)
    write_text(os.path.join(case_dir, "results.csv"),
               "这一段本来应该是数据表，现在是一段散文，没有任何列。\n")
    return p


def b_material_unreadable(base, case_dir, work_dir, pkg):
    case = json.loads(json.dumps(base))
    case["case_id"] = "fault-unreadable-material"
    case["inputs"]["material"] = ["weird.md"]
    p = os.path.join(case_dir, "case.json")
    dump_json(p, case)
    with open(os.path.join(case_dir, "weird.md"), "wb") as f:
        f.write(b"\xff\xfe\x00\x01 \x80\x81 \xc3\x28 not utf-8 at all\n")
    return p


def b_material_dir(base, case_dir, work_dir, pkg):
    case = json.loads(json.dumps(base))
    case["case_id"] = "fault-material-is-dir"
    case["inputs"]["material"] = ["material_dir"]
    p = os.path.join(case_dir, "case.json")
    dump_json(p, case)
    write_text(os.path.join(case_dir, "material_dir", "inner.md"), "# 目录里的文件\n")
    return p


def b_task_missing(base, case_dir, work_dir, pkg):
    case = json.loads(json.dumps(base))
    case["case_id"] = "fault-missing-task"
    p = os.path.join(case_dir, "case.json")
    dump_json(p, case)
    _copy_base_materials(case_dir, pkg)
    os.remove(os.path.join(case_dir, "task.md"))
    return p


# --- 模板族 ---

def b_template_broken(base, case_dir, work_dir, pkg):
    case = json.loads(json.dumps(base))
    case["case_id"] = "fault-broken-template"
    p = os.path.join(case_dir, "case.json")
    dump_json(p, case)
    _copy_base_materials(case_dir, pkg)
    write_text(os.path.join(case_dir, "broken_template.json"),
               '{"colors": {"accent": "#2E7D32",')
    return p


def b_template_missing(base, case_dir, work_dir, pkg):
    case = json.loads(json.dumps(base))
    case["case_id"] = "fault-template-path-gone"
    p = os.path.join(case_dir, "case.json")
    dump_json(p, case)
    _copy_base_materials(case_dir, pkg)
    return p


def b_template_not_object(base, case_dir, work_dir, pkg):
    case = json.loads(json.dumps(base))
    case["case_id"] = "fault-template-not-object"
    p = os.path.join(case_dir, "case.json")
    dump_json(p, case)
    _copy_base_materials(case_dir, pkg)
    dump_json(os.path.join(case_dir, "list_template.json"), ["这不是模板对象"])
    return p


def b_template_pptx_broken(base, case_dir, work_dir, pkg):
    case = json.loads(json.dumps(base))
    case["case_id"] = "fault-broken-template-pptx"
    case["spec"]["template_pptx"] = "broken_master.pptx"
    p = os.path.join(case_dir, "case.json")
    dump_json(p, case)
    _copy_base_materials(case_dir, pkg)
    with open(os.path.join(case_dir, "broken_master.pptx"), "wb") as f:
        f.write(b"NOT-A-ZIP-AT-ALL " * 32)
    return p


def b_template_pptx_missing(base, case_dir, work_dir, pkg):
    case = json.loads(json.dumps(base))
    case["case_id"] = "fault-missing-template-pptx"
    case["spec"]["template_pptx"] = "no_such_master.pptx"
    p = os.path.join(case_dir, "case.json")
    dump_json(p, case)
    _copy_base_materials(case_dir, pkg)
    return p


def b_starting_deck_broken(base, case_dir, work_dir, pkg):
    case = json.loads(json.dumps(base))
    case["case_id"] = "fault-broken-starting-deck"
    case["spec"]["starting_deck"] = "broken_start.pptx"
    p = os.path.join(case_dir, "case.json")
    dump_json(p, case)
    _copy_base_materials(case_dir, pkg)
    with open(os.path.join(case_dir, "broken_start.pptx"), "wb") as f:
        f.write(b"PK\x03\x04 not really a zip " * 16)
    return p


def b_pages_over_limit(base, case_dir, work_dir, pkg):
    case = json.loads(json.dumps(base))
    case["case_id"] = "fault-pages-over-limit"
    case["spec"]["max_slides"] = 3
    p = os.path.join(case_dir, "case.json")
    dump_json(p, case)
    _copy_base_materials(case_dir, pkg)
    return p


# --- 契约族 ---

def b_contract_unknown_type(base, case_dir, work_dir, pkg):
    case = json.loads(json.dumps(base))
    case["case_id"] = "fault-unknown-contract-type"
    case["output_contract"] = {"case_id": "string", "widget": "hologram"}
    p = os.path.join(case_dir, "case.json")
    dump_json(p, case)
    _copy_base_materials(case_dir, pkg)
    return p


def b_contract_bad_type(base, case_dir, work_dir, pkg):
    case = json.loads(json.dumps(base))
    case["case_id"] = "fault-bad-contract-type"
    case["output_contract"] = {"case_id": "string", "score": 7}
    p = os.path.join(case_dir, "case.json")
    dump_json(p, case)
    _copy_base_materials(case_dir, pkg)
    return p


def b_contract_not_object(base, case_dir, work_dir, pkg):
    case = json.loads(json.dumps(base))
    case["case_id"] = "fault-contract-not-object"
    case["output_contract"] = "case_id,deck,evidence"
    p = os.path.join(case_dir, "case.json")
    dump_json(p, case)
    _copy_base_materials(case_dir, pkg)
    return p


def b_contract_list_form(base, case_dir, work_dir, pkg):
    case = json.loads(json.dumps(base))
    case["case_id"] = "fault-contract-list-form"
    case["output_contract"] = ["case_id", "extras"]
    p = os.path.join(case_dir, "case.json")
    dump_json(p, case)
    _copy_base_materials(case_dir, pkg)
    return p


def b_contract_absent(base, case_dir, work_dir, pkg):
    case = json.loads(json.dumps(base))
    case["case_id"] = "fault-contract-absent"
    case.pop("output_contract", None)
    p = os.path.join(case_dir, "case.json")
    dump_json(p, case)
    _copy_base_materials(case_dir, pkg)
    return p


# ---------------------------------------------------------------------------
# 依赖缺失 shim：不改被测代码，只在解释器启动时让指定模块 import 失败
# ---------------------------------------------------------------------------

SHIM = '''# -*- coding: utf-8 -*-
"""演练用 import 屏蔽器（fault_inject.py 生成，跑完随临时目录一起删）。

不修改被测代码，只在解释器启动时把指定顶层模块的 import 变成 ModuleNotFoundError，
用来复现"运行环境里真的没有这个库"。
"""
import sys

BLOCKED = %r


class _Blocker(object):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in BLOCKED:
            raise ModuleNotFoundError(
                "No module named %%r (fault-injection shim)" %% fullname,
                name=fullname)
        return None


sys.meta_path.insert(0, _Blocker())
'''


def make_shim(shim_dir, blocked):
    os.makedirs(shim_dir, exist_ok=True)
    write_text(os.path.join(shim_dir, "sitecustomize.py"), SHIM % (tuple(blocked),))


# ---------------------------------------------------------------------------
# 故障表
# ---------------------------------------------------------------------------
# 字段：id / shape / title / build / block / cmd_extra / expect_exit / expect_status
#       expect_trace（点名字段关键词）/ recover（恢复动作）/ note
# `expect_*` 写的是 **failure-modes.md 的设计期望**；实测偏离处会在矩阵里标 ⚠️。

FAULTS = [
    # ---------------- 输入族（输入文件本身坏掉/缺失） ----------------
    dict(id="F-IN-01", needs_trace=True, shape="input", title="case.json 不存在",
         build=b_case_missing, expect_exit=EXIT_UNREADABLE, expect_status="failed",
         expect_trace=(), recover=None,
         note="D1 末列：输入侧问题，重跑无用"),
    dict(id="F-IN-02", needs_trace=True, shape="input", title="case.json 是半截 JSON",
         build=b_case_broken_json, expect_exit=EXIT_UNREADABLE, expect_status="failed",
         expect_trace=(), recover=None),
    dict(id="F-IN-03", needs_trace=True, shape="input", title="case.json 顶层是数组不是对象",
         build=b_case_not_object, expect_exit=EXIT_UNREADABLE, expect_status="failed",
         expect_trace=(), recover=None),
    dict(id="F-IN-04", needs_trace=True, shape="input", title="case.json 内容为 null",
         build=b_case_null, expect_exit=EXIT_UNREADABLE, expect_status="failed",
         expect_trace=(), recover=None),
    dict(id="F-IN-05", needs_trace=True, shape="input", title="材料全部指向不存在的路径",
         build=b_case_no_material, expect_exit=EXIT_PARTIAL, expect_status="partial",
         expect_trace=(), recover="add-material",
         note="D1：只出元信息 result，deck.slide_count=0"),
    dict(id="F-IN-06", needs_trace=True, shape="input", title="材料文件存在但内容为空",
         build=b_material_empty, expect_exit=EXIT_PARTIAL, expect_status="partial",
         expect_trace=(), recover="add-material",
         note="D1/D2：空材料不得凭空生成主张数字"),
    dict(id="F-IN-07", needs_trace=True, shape="input",
         title="材料被换成与声明用途不符的内容（CSV 里是散文）",
         build=b_material_swap, expect_exit=EXIT_PARTIAL, expect_status="partial",
         expect_trace=(), recover="guard-detect",
         note="设计期望 partial：结果页丢图表必须留痕（D5/D9）"),
    dict(id="F-IN-08", needs_trace=True, shape="input", title="材料字节非法（非 UTF-8）",
         build=b_material_unreadable, expect_exit=None, expect_status=None,
         expect_trace=(), recover=None),
    dict(id="F-IN-09", needs_trace=True, shape="input", title="材料指向目录而不是文件",
         build=b_material_dir, expect_exit=None, expect_status=None,
         expect_trace=(), recover=None),
    dict(id="F-IN-10", needs_trace=False, shape="input", title="task.md 缺失（材料齐全）",
         build=b_task_missing, expect_exit=None, expect_status=None,
         expect_trace=(), recover="add-task",
         note="task.md 是可选输入；材料齐全时缺它不构成降级"),

    # ---------------- 模板族 ----------------
    dict(id="F-TPL-01", needs_trace=True, shape="template", title="--template 指向损坏 JSON",
         build=b_template_broken, expect_exit=EXIT_OK, expect_status="success",
         expect_trace=(), recover="drop-bad-template",
         cmd_extra=lambda cd, w: ["--template", os.path.join(cd, "broken_template.json")]),
    dict(id="F-TPL-02", needs_trace=True, shape="template", title="--template 指向不存在的路径",
         build=b_template_missing, expect_exit=EXIT_OK, expect_status="success",
         expect_trace=(), recover="drop-bad-template",
         cmd_extra=lambda cd, w: ["--template", os.path.join(cd, "ghost_template.json")]),
    dict(id="F-TPL-03", needs_trace=True, shape="template", title="--template 是数组不是对象",
         build=b_template_not_object, expect_exit=EXIT_OK, expect_status="success",
         expect_trace=(), recover="drop-bad-template",
         cmd_extra=lambda cd, w: ["--template", os.path.join(cd, "list_template.json")],
         note="设计期望 success：模板形态错误应回落内置模板并留痕，不应硬崩"),
    dict(id="F-TPL-04", needs_trace=True, shape="template",
         title="spec.template_pptx 损坏（非 zip）",
         build=b_template_pptx_broken, expect_exit=EXIT_PARTIAL, expect_status="partial",
         expect_trace=(), recover="drop-bad-master"),
    dict(id="F-TPL-05", needs_trace=True, shape="template", title="spec.template_pptx 不存在",
         build=b_template_pptx_missing, expect_exit=None, expect_status=None,
         expect_trace=(), recover="guard-detect",
         note="设计期望：被指定的母版打不开/不存在必须留痕（D6）"),
    dict(id="F-TPL-06", needs_trace=True, shape="template", title="spec.starting_deck 损坏",
         build=b_starting_deck_broken, expect_exit=EXIT_PARTIAL, expect_status="partial",
         expect_trace=(), recover="guard-detect",
         note="D6 + F5：降级了就要 partial，并写进 uncertainty"),
    dict(id="F-TPL-07", needs_trace=False, shape="template",
         title="页数上限小于必需页数（max_slides=3）",
         build=b_pages_over_limit, expect_exit=None, expect_status=None,
         expect_trace=(), recover="raise-max-slides",
         note="边界探针（不是故障）：照 max_slides=3 出 3 页是正确行为"),

    # ---------------- 依赖族（包外 shim 屏蔽 import） ----------------
    dict(id="F-DEP-01", needs_trace=False, shape="dependency", title="matplotlib 缺失",
         build=None, block=("matplotlib",), expect_exit=EXIT_OK, expect_status="success",
         expect_trace=(), recover="force-no-chart",
         note="降级形态已由 figure.note + kind=table 记录（四态绑定）"),
    dict(id="F-DEP-02", needs_trace=True, shape="dependency", title="reportlab 缺失",
         build=None, block=("reportlab",), expect_exit=EXIT_OK, expect_status="success",
         expect_trace=(), recover=None),
    dict(id="F-DEP-03", needs_trace=True, shape="dependency",
         title="python-pptx 缺失（建稿轮子没了）",
         build=None, block=("pptx",), expect_exit=EXIT_PARTIAL, expect_status="partial",
         expect_trace=(), recover="guard-detect",
         note="设计期望 partial：缺建稿库也要写出最小 partial/failed result，不能空手退出"),
    dict(id="F-DEP-04", needs_trace=True, shape="dependency", title="Pillow 缺失（预览画布没了）",
         build=None, block=("PIL",), expect_exit=None, expect_status=None,
         expect_trace=(), recover="guard-detect",
         note="设计期望：预览不可用要如实降级（G5 error + uncertainty）"),
    dict(id="F-DEP-05", needs_trace=True, shape="dependency",
         title="渲染链整体缺失（PIL + reportlab）",
         build=None, block=("PIL", "reportlab"), expect_exit=None, expect_status=None,
         expect_trace=(), recover="guard-detect"),

    # ---------------- 契约族 ----------------
    dict(id="F-CTR-01", needs_trace=True, shape="contract",
         title="output_contract 声明未知类型",
         build=b_contract_unknown_type, expect_exit=EXIT_OK, expect_status="success",
         expect_trace=("widget",), recover=None,
         note="设计期望：未知类型按四形态兜底并记 uncertainty（D10）"),
    dict(id="F-CTR-02", needs_trace=True, shape="contract",
         title="output_contract 类型名写成数字",
         build=b_contract_bad_type, expect_exit=EXIT_OK, expect_status="success",
         expect_trace=("score",), recover=None),
    dict(id="F-CTR-03", needs_trace=True, shape="contract",
         title="output_contract 是字符串不是对象",
         build=b_contract_not_object, expect_exit=EXIT_OK, expect_status="success",
         expect_trace=(), recover="guard-detect",
         note="设计期望：契约形态错误不得整体静默跳过"),
    dict(id="F-CTR-04", needs_trace=False, shape="contract",
         title="output_contract 是字段名列表",
         build=b_contract_list_form, expect_exit=EXIT_OK, expect_status="success",
         expect_trace=("extras",), recover=None,
         note="列表形态是合法形态，字段已回显即可"),
    dict(id="F-CTR-05", needs_trace=False, shape="contract",
         title="完全没有 output_contract",
         build=b_contract_absent, expect_exit=EXIT_OK, expect_status="success",
         expect_trace=(), recover=None,
         note="缺省形态（不是故障）：没声明就不需要回显"),
    dict(id="F-CTR-06", needs_trace=True, shape="contract",
         title="已声明的契约字段被从 result.json 删除",
         build=None, block=None, expect_exit=1, expect_status=None,
         afters="delete-field", expect_trace=("G2 declared output_contract field missing",),
         recover="rerun",
         note="用 result_tool.py 复验：G2 必须报错"),
]

FAULT_BY_ID = {f["id"]: f for f in FAULTS}


# ---------------------------------------------------------------------------
# 执行：注入
# ---------------------------------------------------------------------------

def _prepare(fault, pkg, work_root):
    """为一条故障准备包外副本、case、输出目录、环境变量。"""
    fid = fault["id"]
    fdir = os.path.join(work_root, "runs", fid)
    if os.path.isdir(fdir):
        shutil.rmtree(fdir)
    os.makedirs(fdir, exist_ok=True)
    run_pkg = copy_pkg(pkg, os.path.join(work_root, "pkgs", fid))
    case_dir = os.path.join(fdir, "case")
    out_dir = os.path.join(fdir, "out")
    os.makedirs(out_dir, exist_ok=True)

    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    blocked = list(fault.get("block") or ())
    if blocked:
        shim = os.path.join(fdir, "shim")
        make_shim(shim, blocked)
        env["PYTHONPATH"] = shim + os.pathsep + env.get("PYTHONPATH", "")

    if fault.get("build") is not None:
        case_path = _mutate(fault["build"], run_pkg, case_dir, fdir)
    else:
        case_path = os.path.join(run_pkg, BASE_CASE)

    cmd = [sys.executable, os.path.join(run_pkg, "scripts", "main.py"),
           "--case", case_path, "--out", out_dir]
    if fault.get("cmd_extra"):
        cmd += list(fault["cmd_extra"](case_dir, fdir))
    return run_pkg, case_dir, out_dir, case_path, env, cmd


def inject(fault, pkg, work_root):
    fid = fault["id"]
    run_pkg, case_dir, out_dir, case_path, env, cmd = _prepare(fault, pkg, work_root)
    rec = {"id": fid, "shape": fault["shape"], "title": fault["title"],
           "blocked_modules": list(fault.get("block") or ()),
           "cmd": "python scripts/main.py " + " ".join(
               [os.path.basename(c) if c.startswith(run_pkg) else c for c in cmd[3:]]),
           "note": fault.get("note", "")}

    if fault.get("afters") == "delete-field":
        rc0, out0, _ = _run(cmd, env=env)
        rec["pre_exit"] = rc0
        rp = os.path.join(out_dir, "result.json")
        target = None
        if os.path.isfile(rp):
            r = load_json(rp)
            declared = list((load_json(case_path).get("output_contract") or {}).keys())
            target = "is_example" if "is_example" in declared else (
                declared[-1] if declared else None)
            if target:
                r.pop(target, None)
                dump_json(rp, r)
        rec["deleted_field"] = target
        cmd2 = [sys.executable, os.path.join(run_pkg, "scripts", "result_tool.py"),
                "--result", rp, "--out-dir", out_dir, "--case", case_path,
                "--envelope", os.path.join(run_pkg, "templates", "result_envelope.json")]
        rc, out, dt = _run(cmd2, env=env)
        rec["cmd"] = ("python scripts/result_tool.py --result <out>/result.json "
                      "--out-dir <out> --case <case> --envelope <pkg>/templates/result_envelope.json")
        rec["obs"] = observe(out_dir)
        try:
            rec["gate"] = json.loads(out.strip().splitlines()[-1])
        except Exception:  # noqa: BLE001
            rec["gate"] = None
        rec["trace_hit"] = trace_hits(fault, rec["obs"], _trace_blob(out_dir) + "\n" + out)
        rec["recovered"] = None
        _finish(rec, fault, rc, dt, out)
        # 恢复动作：把契约字段补回去再验一次（重跑主流程）
        if fault.get("recover") == "rerun":
            rc2, out2, dt2 = _run(cmd, env=env)
            rec["recovery"] = {"action": "重跑 main.py（重新回显契约字段）",
                               "cmd": "python scripts/main.py --case <case> --out <out>",
                               "exit": rc2, "status": observe(out_dir).get("status"),
                               "seconds": round(dt2, 2),
                               "outcome": REC_FIXED if rc2 == 0 else REC_STILL_BAD}
        return rec

    rc, out, dt = _run(cmd, env=env)
    rec["obs"] = observe(out_dir)
    rec["trace_hit"] = trace_hits(fault, rec["obs"], _trace_blob(out_dir) + "\n" + out)
    _finish(rec, fault, rc, dt, out)

    if fault.get("recover"):
        rec["recovery"] = recover(fault, run_pkg, case_dir, out_dir, case_path, env, work_root)
    return rec


def _finish(rec, fault, rc, dt, out):
    rec["exit"] = rc
    rec["seconds"] = round(dt, 2)
    obs = rec["obs"]
    rec["expect_exit"] = fault.get("expect_exit")
    rec["expect_status"] = fault.get("expect_status")
    rec["needs_trace"] = bool(fault.get("needs_trace", False))
    # 只有 stdout 里的 Traceback、没写任何产物 = 下游无法判读，仍算静默（单独标注 trace_kind）
    only_stdout = (rec["trace_hit"] == ["Traceback"] and not obs.get("has_result"))
    rec["trace_kind"] = ("none" if not rec["trace_hit"] else
                         ("stdout-only" if only_stdout else "product"))
    rec["silent"] = bool(rec["needs_trace"] and rec["trace_kind"] != "product")
    rec["stdout_only"] = bool(only_stdout)
    rec["exit_matches_expect"] = (fault.get("expect_exit") is None
                                  or rc == fault.get("expect_exit"))
    rec["status_matches_expect"] = (fault.get("expect_status") is None
                                    or obs.get("status") == fault.get("expect_status"))
    rec["tail"] = [ln for ln in out.strip().splitlines()[-3:]]
    return rec


# ---------------------------------------------------------------------------
# 执行：恢复演练（每条恢复动作都是**真命令**）
# ---------------------------------------------------------------------------

def _rerun(run_pkg, case_path, out_dir, env, extra=None, out_name="out-recovered"):
    out2 = os.path.join(os.path.dirname(out_dir), out_name)
    if os.path.isdir(out2):
        shutil.rmtree(out2)
    os.makedirs(out2, exist_ok=True)
    cmd = [sys.executable, os.path.join(run_pkg, "scripts", "main.py"),
           "--case", case_path, "--out", out2] + list(extra or ())
    rc, out, dt = _run(cmd, env=env)
    return rc, observe(out2), round(dt, 2), cmd, out2


def recover(fault, run_pkg, case_dir, out_dir, case_path, env, work_root):
    """按故障类型执行真实恢复动作，并回读恢复后的状态。"""
    action = fault["recover"]
    try:
        case = load_json(case_path) if os.path.isfile(case_path) else {}
    except Exception:  # noqa: BLE001
        case = {}

    if action == "add-material":
        # 把材料补回（真实恢复：素材到齐即可建稿）
        _copy_base_materials(case_dir, run_pkg)
        for k, v in (case.get("inputs") or {}).items():
            pass
        case.setdefault("inputs", {})["material"] = ["material.md", "results.csv"]
        dump_json(case_path, case)
        rc, obs, dt, cmd, out2 = _rerun(run_pkg, case_path, out_dir, env)
        return {"action": "把缺失材料补到 case 目录并改回 inputs.material",
                "cmd": "python scripts/main.py --case <case> --out <out-recovered>",
                "exit": rc, "status": obs.get("status"), "seconds": dt,
                "uncertainty": obs.get("uncertainty"),
                "outcome": REC_FIXED if rc == 0 else REC_STILL_BAD}

    if action == "add-task":
        write_text(os.path.join(case_dir, "task.md"), read_text(
            os.path.join(run_pkg, BASE_TASK)))
        rc, obs, dt, cmd, out2 = _rerun(run_pkg, case_path, out_dir, env)
        return {"action": "补回被删掉的 task.md", "exit": rc,
                "status": obs.get("status"), "seconds": dt,
                "outcome": REC_FIXED if rc == 0 else REC_STILL_BAD}

    if action == "drop-bad-template":
        # 恢复：不再传 --template（回到内置模板）→ 期望 success 且无 uncertainty
        rc, obs, dt, cmd, out2 = _rerun(run_pkg, case_path, out_dir, env)
        return {"action": "去掉坏 --template，回落到内置 templates/default.json",
                "exit": rc, "status": obs.get("status"), "seconds": dt,
                "uncertainty": obs.get("uncertainty"),
                "outcome": REC_FIXED if (rc == 0 and not obs.get("uncertainty"))
                else REC_STILL_BAD}

    if action == "drop-bad-master":
        case.pop("spec", None)
        case.setdefault("spec", {})
        if os.path.isfile(case_path):
            orig = _base_case(run_pkg)
            case["spec"] = orig.get("spec", {})
            dump_json(case_path, case)
        rc, obs, dt, cmd, out2 = _rerun(run_pkg, case_path, out_dir, env)
        return {"action": "移除损坏的 template_pptx / starting_deck，改用内置模板",
                "exit": rc, "status": obs.get("status"), "seconds": dt,
                "change_records": obs.get("change_records"),
                "outcome": REC_FIXED if rc == 0 else REC_STILL_BAD}

    if action == "force-no-chart":
        # 恢复：把"图表丢了"这件事显式化 → --no-chart 让降级有记录
        rc, obs, dt, cmd, out2 = _rerun(run_pkg, case_path, out_dir, env,
                                       extra=["--no-chart"], out_name="out-nochart")
        return {"action": "改用 --no-chart，把降级显式化（figure.kind=table + note）",
                "cmd": "python scripts/main.py --case <case> --out <out> --no-chart",
                "exit": rc, "status": obs.get("status"), "seconds": dt,
                "degraded_figures": obs.get("degraded_figures"),
                "uncertainty": obs.get("uncertainty"),
                "outcome": REC_FIXED if obs.get("degraded_figures") else REC_STILL_BAD}

    if action == "guard-detect":
        # 恢复动作 = 用守卫把"静默"变成"被报出来"（可发现性恢复）
        findings = guard_preflight(run_pkg, case_path) + guard_postrun(out_dir)
        return {"action": "用 --guard 做运行前体检 + 运行后核对（把静默失败变成可发现的报告）",
                "cmd": "python scripts/fault_inject.py --guard --pkg <pkg> --case <case> 且 --out <out>",
                "findings": ["%s/%s: %s" % (lv, area, msg[:90]) for lv, area, msg in findings],
                "count": len(findings),
                "outcome": REC_FIXED if findings else REC_STILL_BAD}

    if action == "raise-max-slides":
        rc, obs, dt, cmd, out2 = _rerun(run_pkg, case_path, out_dir, env,
                                       extra=["--max-slides", "8"], out_name="out-8slides")
        return {"action": "--max-slides 8 覆盖过紧的上限", "exit": rc,
                "status": obs.get("status"), "slides": obs.get("slide_count"),
                "seconds": dt,
                "outcome": REC_FIXED if obs.get("slide_count") == 8 else REC_STILL_BAD}

    return {"action": str(action), "outcome": REC_IMPOSSIBLE,
            "note": "无包内可行恢复动作（环境缺件），已在矩阵中如实标注"}


# ---------------------------------------------------------------------------
# 守卫：运行前体检 + 运行后核对（关掉实测出来的三类静默失败）
# ---------------------------------------------------------------------------

IMPORT_NEEDS = [("pptx", "python-pptx", "建稿必需（缺则连主流程都启动不了）"),
                ("PIL", "Pillow", "预览 PNG 必需"),
                ("matplotlib", "matplotlib", "图表重绘（缺则降级为原生表格）"),
                ("reportlab", "reportlab", "PDF 预览（可缺，仅降级）")]


def guard_preflight(pkg, case_path, template_path=None):
    """运行前：把会硬崩的输入拦下来（这些在实测里是**静默失败**）。"""
    findings = []
    if not os.path.isfile(case_path):
        findings.append(("BLOCKER", "case", "case.json 不存在: %s" % case_path))
        return findings
    try:
        case = load_json(case_path)
    except Exception as e:  # noqa: BLE001
        findings.append(("BLOCKER", "case", "case.json 无法解析: %s" % e))
        return findings
    if not isinstance(case, dict):
        findings.append(("BLOCKER", "case",
                         "case.json 顶层不是对象（%s）——主流程会 TypeError 硬崩且不写 result.json"
                         % type(case).__name__))
        return findings

    try:
        import importlib.util as iu
        for mod, pkgname, why in IMPORT_NEEDS:
            if iu.find_spec(mod) is None:
                level = "BLOCKER" if mod in ("pptx", "PIL") else "DEGRADE"
                findings.append((level, "dependency",
                                 "缺少 %s（%s）；%s" % (pkgname, mod, why)))
    except Exception as e:  # noqa: BLE001
        findings.append(("WARN", "dependency", "依赖探测失败: %s" % e))

    if template_path:
        if not os.path.isfile(template_path):
            findings.append(("DEGRADE", "template",
                             "--template 指向的文件不存在: %s（会回落内置模板）" % template_path))
        else:
            try:
                if not isinstance(load_json(template_path), dict):
                    findings.append(("BLOCKER", "template",
                                     "--template 的 JSON 顶层不是对象（%s）——merge_spec 会 "
                                     "TypeError 硬崩，而且**不会写出 result.json**"
                                     % type(load_json(template_path)).__name__))
            except Exception as e:  # noqa: BLE001
                findings.append(("DEGRADE", "template",
                                 "--template 无法解析（会回落内置模板）: %s" % e))

    tpl = os.path.join(pkg, "templates", "default.json")
    if not os.path.isfile(tpl):
        findings.append(("DEGRADE", "template", "内置模板缺失: %s" % tpl))
    else:
        try:
            if not isinstance(load_json(tpl), dict):
                findings.append(("BLOCKER", "template",
                                 "内置模板不是 JSON 对象——merge_spec 会硬崩"))
        except Exception as e:  # noqa: BLE001
            findings.append(("BLOCKER", "template", "内置模板无法解析: %s" % e))

    for key in ("template_pptx", "starting_deck"):
        v = (case.get("spec") or {}).get(key)
        if not v:
            continue
        cand = v if os.path.isabs(v) else os.path.join(
            os.path.dirname(os.path.abspath(case_path)), v)
        if not os.path.isfile(cand):
            findings.append(("DEGRADE", key, "%s 指向的文件不存在: %s" % (key, v)))
            continue
        try:
            from pptx import Presentation
            Presentation(cand)
        except Exception as e:  # noqa: BLE001
            findings.append(("BLOCKER" if key == "template_pptx" else "DEGRADE", key,
                             "%s 不是可打开的 PPTX（%s）: %s" % (key, type(e).__name__, v)))

    oc = case.get("output_contract")
    if isinstance(oc, dict):
        allowed = {"string", "str", "list", "array", "dict", "object",
                   "bool", "boolean", "int", "integer", "float", "number"}
        for k, v in oc.items():
            if isinstance(v, str) and v not in allowed:
                findings.append(("DEGRADE", "contract",
                                 "output_contract.%s 声明了未知类型 %r（会按四形态兜底）" % (k, v)))
            if isinstance(v, dict) or isinstance(v, (int, float)) and not isinstance(v, bool):
                findings.append(("DEGRADE", "contract",
                                 "output_contract.%s 的类型声明不是字符串（%r）" % (k, v)))
    elif oc is not None:
        findings.append(("DEGRADE", "contract",
                         "output_contract 不是对象（%s）——契约回显会被整体跳过"
                         % type(oc).__name__))
    return findings


def guard_postrun(out_dir):
    """运行后：核对产物有没有把该记的事记下来（三类静默失败的现实形态）。"""
    findings = []
    rp = os.path.join(out_dir, "result.json")
    if not os.path.isfile(rp):
        findings.append(("BLOCKER", "result", "输出目录里没有 result.json（运行未落盘）"))
        return findings
    try:
        r = load_json(rp)
    except Exception as e:  # noqa: BLE001
        findings.append(("BLOCKER", "result", "result.json 无法解析: %s" % e))
        return findings
    if not isinstance(r, dict):
        findings.append(("BLOCKER", "result", "result.json 顶层不是对象"))
        return findings

    status = r.get("status")
    unc = r.get("uncertainty") or []
    changes = r.get("change_records") or []
    ev = r.get("evidence") or {}
    deck = r.get("deck") or {}

    if status == "success" and not deck.get("slide_count"):
        findings.append(("BLOCKER", "status",
                         "status=success 但 deck.slide_count=0（状态与产物不自洽，F5.3）"))

    degrade_words = ("失败", "降级", "沿用", "跳过", "不可用", "缺失")
    degrading = [c for c in changes
                 if any(w in str(c.get("reason", "")) for w in degrade_words)]
    if degrading and not unc and status == "success":
        findings.append(("WARN", "consistency",
                         "change_records 里有 %d 条降级记录（如 %r），但 uncertainty 为空且 "
                         "status=success —— 按 failure-modes §5 应降 partial 并留 uncertainty"
                         % (len(degrading), str(degrading[0].get("reason", ""))[:60])))

    # 图表静默丢失：以**材料侧事实**为准，而不是"这页没图就报警"（否则健康产物也会被误报）
    silent_figs = []
    for sl in (deck.get("slides") or []):
        fig = sl.get("figure") or {}
        if (fig.get("kind") or "none") == "none" and fig.get("ref") and not fig.get("note"):
            silent_figs.append(sl.get("index"))      # 材料点名了图/表，却既没绑定也没解释
    if silent_figs:
        findings.append(("WARN", "figure",
                         "页 %s 的 figure.ref 非空但 kind=none 且没有 note —— "
                         "材料点了图表却没有落地，也没解释" % silent_figs))

    mv_path = os.path.join(out_dir, "work", "material_view.json")
    if os.path.isfile(mv_path):
        try:
            mv = load_json(mv_path)
        except Exception:  # noqa: BLE001
            mv = {}
        n_tables = len(mv.get("tables") or [])
        kinds = {(sl.get("figure") or {}).get("kind") or "none"
                 for sl in (deck.get("slides") or [])}
        explained = any((sl.get("figure") or {}).get("note")
                        for sl in (deck.get("slides") or []))
        if n_tables and not (kinds - {"none"}) and not explained:
            findings.append(("WARN", "figure",
                             "材料里有 %d 张数据表，但成稿里既没有图表/表格、也没有任何 note "
                             "说明为什么没画 —— 这是**静默降级**（D9 要求留 figure.note）"
                             % n_tables))
        if not mv.get("sections"):
            findings.append(("WARN", "material",
                             "material_view 里没有任何章节（材料可能没读进来）"))


    if status == "partial" and not unc:
        findings.append(("WARN", "consistency",
                         "status=partial 但 uncertainty 为空（F5.4：降级必须逐条留痕）"))
    if (ev.get("unverified_claims") or []) and status == "success":
        findings.append(("WARN", "consistency",
                         "有 %d 条未核验主张却标 success（G4 warning / F5.2）"
                         % len(ev["unverified_claims"])))

    gate = (r.get("run_meta") or {}).get("gate") or {}
    if gate.get("valid") is False:
        findings.append(("BLOCKER", "gate",
                         "G 门未过: %s" % "; ".join((gate.get("errors") or [])[:3])))
    return findings


def _print_findings(findings, title):
    print("== %s ==" % title)
    if not findings:
        print("  OK  未发现问题")
        return 0
    order = {"BLOCKER": 0, "WARN": 1, "DEGRADE": 2}
    bad = 0
    for level, area, msg in sorted(findings, key=lambda x: order.get(x[0], 9)):
        print("  %-8s [%s] %s" % (level, area, msg))
        if level in ("BLOCKER", "WARN"):
            bad += 1
    return bad


# ---------------------------------------------------------------------------
# 汇总渲染
# ---------------------------------------------------------------------------

def render_matrix(records, with_recovery=False):
    L = []
    L.append("# FAULT-MATRIX.md — 四族失败注入与恢复的逐行实测矩阵\n")
    L.append("> **每一行都是真跑出来的**：`scripts/fault_inject.py` 把上游输入逐个弄坏，")
    L.append("> 在包外副本上跑一次完整 `scripts/main.py`，再回读 `result.json` / "
             "`changelog.jsonl` / `logs/`。")
    L.append("> 复现命令：`python \"$SKILL_DIR/scripts/fault_inject.py\" --pkg \"$SKILL_DIR\" "
             "--work <包外目录> --with-recovery`\n")
    L.append("## 0. 判读口径\n")
    L.append("| 列 | 含义 |")
    L.append("|-|-|")
    L.append("| exit | `main.py` 实测退出码（0=success / 1=partial / 2=输入不可读） |")
    L.append("| status | `result.json.status` 实测值（`—` = 没写出 result.json） |")
    L.append("| unc | `uncertainty` 条数 |")
    L.append("| mw | `evidence.material_warnings` 条数 |")
    L.append("| cr | `change_records` 条数（>1 表示除 start 外还有记录） |")
    L.append("| slides | `deck.slide_count`（0 = 未建 deck，D1 的诚实路径） |")
    L.append("| reopen | deck 能否被 python-pptx 重新打开 |")
    L.append("| 留痕 | **结构化**留痕字段（不靠键名文本匹配） |")
    L.append("| 静默 | **Yes = 出了问题却没有任何记录**（最坏情况） |")
    L.append("| 设计期望 | `references/failure-modes.md` 对该情形的期望 exit/status（`-` = 只取证） |")
    L.append("| 一致 | 实测 vs 设计期望 |")
    if with_recovery:
        L.append("| 恢复 | 恢复动作的实测结局（recovered / still-degraded / unrecoverable） |")
    L.append("")
    L.append("## 1. 逐行实测矩阵\n")
    head = ("| # | 族 | 注入什么 | exit | status | unc | mw | cr | slides | reopen | 留痕 | 静默 | 设计期望 | 一致 |")
    sep = "|-|-|-|-|-|-|-|-|-|-|-|-|-|-|"
    if with_recovery:
        head += " 恢复 |"
        sep += "-|"
    L.append(head)
    L.append(sep)
    for r in records:
        o = r.get("obs") or {}
        reopen = o.get("reopenable")
        reopened = "—" if reopen is None else (
            "**失败**" if str(reopen).startswith("FAILED") else str(reopen))
        exp = "%s/%s" % ("-" if r.get("expect_exit") is None else r.get("expect_exit"),
                         "-" if r.get("expect_status") is None else r.get("expect_status"))
        if r.get("expect_exit") is None and r.get("expect_status") is None:
            verdict = "取证"
        else:
            verdict = "✅" if (r.get("exit_matches_expect")
                              and r.get("status_matches_expect")) else "⚠️"
        row = "| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            r["id"], r["shape"], r["title"], r.get("exit"),
            o.get("status") if o.get("status") else "—",
            o.get("uncertainty"), o.get("material_warnings"), o.get("change_records"),
            o.get("slide_count"), reopened,
            " · ".join(r.get("trace_hit") or []) or "—",
            "**Yes**" if r.get("silent") else "No", exp, verdict)
        if with_recovery:
            rec = r.get("recovery") or {}
            row += " %s |" % (rec.get("outcome") or "—")
        L.append(row)
    L.append("")
    return "\n".join(L)


def write_csv(records, path, with_recovery=False):
    cols = ["id", "shape", "title", "exit", "status", "uncertainty", "material_warnings",
            "change_records", "slide_count", "reopenable", "traces", "silent",
            "expect_exit", "expect_status", "consistent", "recovery_outcome"]
    rows = [",".join(cols)]
    for r in records:
        o = r.get("obs") or {}
        consistent = "yes" if (r.get("exit_matches_expect") and r.get("status_matches_expect")) else "no"
        if r.get("expect_exit") is None and r.get("expect_status") is None:
            consistent = "observed-only"
        rec = (r.get("recovery") or {}).get("outcome", "")
        vals = [r["id"], r["shape"], '"%s"' % r["title"], r.get("exit"), o.get("status"),
                o.get("uncertainty"), o.get("material_warnings"), o.get("change_records"),
                o.get("slide_count"), o.get("reopenable"),
                ';'.join(r.get("trace_hit") or []),
                "yes" if r.get("silent") else "no",
                r.get("expect_exit"), r.get("expect_status"), consistent, rec]
        rows.append(",".join(str(x) for x in vals))
    write_text(path, "\n".join(rows) + "\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="四族失败注入 + 恢复演练 + 留痕守卫（输入/模板/依赖/契约）")
    ap.add_argument("--pkg", default=DEFAULT_PKG, help="技能根目录（含 SKILL.md）")
    ap.add_argument("--work", default=None,
                    help="**包外**可写工作目录（默认 <pkg 同级>/fault-work）")
    ap.add_argument("--only", default=None, help="逗号分隔故障号，如 F-IN-07,F-DEP-03")
    ap.add_argument("--shape", default=None, choices=SHAPES, help="只跑某一族")
    ap.add_argument("--with-recovery", action="store_true", help="同时对每条跑恢复动作")
    ap.add_argument("--report-json", default=None, help="完整实测记录 JSON")
    ap.add_argument("--report-md", default=None, help="逐行矩阵 Markdown")
    ap.add_argument("--report-csv", default=None, help="逐行矩阵 CSV")
    ap.add_argument("--list", action="store_true", help="只列出故障表")
    ap.add_argument("--guard", action="store_true",
                    help="守卫模式：--case 做运行前体检，--out 做运行后核对")
    ap.add_argument("--case", default=None, help="[--guard] case.json 路径")
    ap.add_argument("--template", default=None,
                    help="[--guard] 本次要传给 main.py 的 --template 路径（一并体检）")
    ap.add_argument("--out", default=None, help="[--guard] 一次运行的输出目录")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args(argv)

    if args.list:
        print("共 %d 条故障（4 族）：\n" % len(FAULTS))
        for f in FAULTS:
            print("  %-9s [%-10s] %s%s" % (f["id"], f["shape"], f["title"],
                                           "" if f.get("recover") else "   （无包内恢复动作）"))
        print("\n注入： python fault_inject.py --pkg <SKILL_DIR> --work <包外目录> "
              "[--with-recovery]")
        print("守卫： python fault_inject.py --guard --case <case.json>   # 运行前")
        print("       python fault_inject.py --guard --out <输出目录>     # 运行后")
        return 0

    if args.guard:
        if not args.case and not args.out:
            print("ERROR: --guard 需要 --case（运行前）或 --out（运行后）")
            return 2
        bad = 0
        if args.case:
            bad += _print_findings(guard_preflight(
                os.path.abspath(args.pkg), os.path.abspath(args.case),
                os.path.abspath(args.template) if args.template else None),
                                   "运行前体检 preflight（%s）" % os.path.basename(args.case))
        if args.out:
            bad += _print_findings(guard_postrun(os.path.abspath(args.out)),
                                   "运行后核对 postrun（%s）" % args.out)
        print("\n守卫结论: %s" % ("通过" if bad == 0 else "有 %d 项需要处理" % bad))
        return 0 if bad == 0 else 1

    pkg = os.path.abspath(args.pkg)
    if not os.path.isfile(os.path.join(pkg, "SKILL.md")):
        print("ERROR: %s 下没有 SKILL.md，--pkg 应指向技能根目录" % pkg)
        return 2
    work = os.path.abspath(args.work or os.path.join(os.path.dirname(pkg), "fault-work"))
    try:
        inside = os.path.commonpath([work, pkg]) == pkg
    except ValueError:
        inside = False
    if inside:
        print("ERROR: --work 不能落在被测技能包内部（会污染包体）: %s" % work)
        return 2
    os.makedirs(work, exist_ok=True)

    todo = FAULTS
    if args.only:
        want = [x.strip() for x in args.only.split(",") if x.strip()]
        unknown = [x for x in want if x not in FAULT_BY_ID]
        if unknown:
            print("ERROR: 未知故障号 %s" % ", ".join(unknown))
            return 2
        todo = [FAULT_BY_ID[x] for x in want]
    if args.shape:
        todo = [f for f in todo if f["shape"] == args.shape]

    print("被测包: %s" % pkg)
    print("工作区: %s（包外；被测包会复制到该目录下运行）" % work)
    print("故障数: %d  恢复演练: %s\n" % (len(todo), "开" if args.with_recovery else "关"))

    records = []
    for f in todo:
        rec = inject(f, pkg, work)
        records.append(rec)
        o = rec.get("obs") or {}
        line = "  %-9s exit=%-8s status=%-8s unc=%-2s 静默=%-3s" % (
            rec["id"], rec.get("exit"), o.get("status") or "—",
            o.get("uncertainty"), "Yes" if rec.get("silent") else "No")
        if rec.get("recovery"):
            line += " 恢复=%s" % rec["recovery"].get("outcome")
        print(line + "  " + rec["title"])
        sys.stdout.flush()

    if args.report_json:
        dump_json(os.path.abspath(args.report_json),
                  {"package": os.path.basename(pkg),
                   "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                   "with_recovery": bool(args.with_recovery),
                   "faults": records})
    if args.report_md:
        write_text(os.path.abspath(args.report_md),
                   render_matrix(records, with_recovery=args.with_recovery))
    if args.report_csv:
        write_csv(records, os.path.abspath(args.report_csv), with_recovery=args.with_recovery)

    silent = [r["id"] for r in records if r.get("silent")]
    mism = [r["id"] for r in records
            if not (r.get("exit_matches_expect") and r.get("status_matches_expect"))
            and not (r.get("expect_exit") is None and r.get("expect_status") is None)]
    print("\n静默失败（无任何留痕）: %s" % (", ".join(silent) if silent else "无"))
    print("与设计期望不一致: %s" % (", ".join(mism) if mism else "无"))
    return 1 if (mism or silent) else 0


if __name__ == "__main__":
    sys.exit(main())
