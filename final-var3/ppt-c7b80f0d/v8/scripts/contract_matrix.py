#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""contract_matrix.py — inject every OUTPUT_CONTRACT container form and boundary
value into the real pipeline and record what actually happens.

Axis of this package (v8): the contract (`output_contract`) has **four declared
forms** (field->type hint, field->description, boolean switch, list of names)
and real cases add **boundary values** (empty string, empty array, 0, very long
string, illegal type, missing field). Each combination is injected as a complete
`case.json`, the *unmodified* end-to-end entry is executed once, and the result is
read back field by field:

* exit code of the run,
* whether `result.json` was written at all,
* `status`, `run_meta.self_check`, `uncertainty` of that run,
* whether every declared field is echoed at top level, with which JSON type and
  whether it is null,
* and the verdict for the cell: ``match`` / ``coerced`` / ``dropped`` /
  ``absent`` / ``crash``.

"Silent pass" is the interesting category: the run exits 0, the internal gates
report OK, the echo does **not** match what the declaration implies, and nothing
in `uncertainty` mentions it. Those cells are listed separately, because they are
exactly the cases a reviewer would never notice.

Nothing is asserted from the document: every row of `references/CONTRACT-MATRIX.md`
is produced by `--emit-md` from measured runs (see `contract-matrix-data.json`).

Usage
-----
    python "$SKILL_DIR/scripts/contract_matrix.py" --out <probe dir> \\
        [--case <base case.json>] [--spec <deck-spec.json>] [--entry <main.py>] \\
        [--only A05,A06] [--emit-md <path>] [--json <path>] [--quiet]

Exit codes
----------
    0  every cell wrote a result.json and no cell is a silent pass
    1  at least one silent pass (a mismatch the run neither fixed nor recorded)
    2  parameter/input error
    3  at least one cell crashed (non-zero exit or no result.json)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
DEFAULT_ENTRY = os.path.join(HERE, "main.py")

sys.path.insert(0, HERE)
import check_contract as contract_check          # noqa: E402  (same package)
SCHEMA = "contract-matrix/1"

LONG_STRING = "长" * 8000
MANY_NAMES = ["cell_bulk_%03d" % i for i in range(200)]
# the five semantic fields the example case declares; form (4) replaces the whole
# container, so the list cells include them to keep the 19-field surface complete
SEMANTIC = ["title", "main_claim", "slides", "render_state", "notes_separated"]

# --------------------------------------------------------------------------- #
# Cells: (id, form, boundary, declaration, patch)
# `patch` is applied to the base case; ("delete",) removes output_contract.
# `expect` maps each declared field to the value the contract document implies.
# --------------------------------------------------------------------------- #
CELLS = [
    # ---- form ①: field -> type hint, values carry the container type --------
    dict(id="A01", form="① 字段→类型提示", boundary="普通字符串提示",
         decl={"cell_title_hint": "字符串"},
         expect={"cell_title_hint": ""},
         note="无真实值 → 按容器给空串"),
    dict(id="A02", form="① 字段→类型提示", boundary="列表提示",
         decl={"cell_list_hint": ["每页 {page,title,claim}（列表）"]},
         expect={"cell_list_hint": []},
         note="声明值是 list → 回显 []"),
    dict(id="A03", form="① 字段→类型提示", boundary="对象（嵌套）提示",
         decl={"cell_obj_hint": {"a": "b"}},
         expect={"cell_obj_hint": {}},
         note="声明值是 dict → 回显 {}（嵌套结构本身不回显）"),
    dict(id="A04", form="① 字段→类型提示", boundary="**数值 0**",
         decl={"cell_num_hint": 0},
         expect={"cell_num_hint": 0},
         note="数值型声明的类型忠实性（0 是边界）"),
    dict(id="A05", form="① 字段→类型提示", boundary="空串",
         decl={"cell_empty_str": ""},
         expect={"cell_empty_str": ""},
         note="空串边界"),
    dict(id="A06", form="① 字段→类型提示", boundary="空数组",
         decl={"cell_empty_list": []},
         expect={"cell_empty_list": []},
         note="空数组边界"),
    dict(id="A07", form="① 字段→类型提示", boundary="**非法类型 null**",
         decl={"cell_null": None},
         expect={"cell_null": ""},
         note="声明的值本身是 null：禁止把 null 回显出去"),
    dict(id="A08", form="① 字段→类型提示", boundary="超长字符串（8000 字）",
         decl={"cell_long": LONG_STRING},
         expect={"cell_long": ""},
         note="超长声明：只取容器类型，不把声明原文抄进 result"),
    dict(id="A09", form="① 字段→类型提示", boundary="与真实键同名（status/deck）",
         decl={"status": "字符串", "deck": "字符串"},
         expect=None,
         note="真实值优先，声明不得覆盖运行结果"),
    dict(id="A10", form="① 字段→类型提示", boundary="语义字段（title/main_claim/slides/render_state）",
         decl={"title": "字符串", "main_claim": "字符串",
               "slides": ["每页 {page,title,claim}（列表）"], "render_state": "说明"},
         expect=None,
         note="语义字段必须取本次运行的真实值"),
    dict(id="A11", form="① 字段→类型提示", boundary="布尔 true（未知字段名）",
         decl={"cell_bool_true": True},
         expect={"cell_bool_true": True},
         note="未知布尔字段：如实回显声明值"),
    dict(id="A12", form="① 字段→类型提示", boundary="布尔 false（未知字段名）",
         decl={"cell_bool_false": False},
         expect={"cell_bool_false": False},
         note="未知布尔字段的 false 分支"),
    dict(id="A13", form="① 字段→类型提示", boundary="布尔 true（语义字段 notes_separated）",
         decl={"notes_separated": True},
         expect={"notes_separated": True},
         note="语义布尔：回显 deck 的真实状态"),
    dict(id="A14", form="① 字段→类型提示", boundary="布尔 false（语义字段 notes_separated）",
         decl={"notes_separated": False},
         expect={"notes_separated": True},
         note="真实状态为 true 时，声明 false 不得把结果改成 false"),
    # ---- form ②: field -> description --------------------------------------
    dict(id="B01", form="② 字段→说明", boundary="普通说明文本",
         decl={"cell_desc": "渲染与版本记录（字符串或对象）"},
         expect={"cell_desc": ""},
         note="说明形态无真实值 → 空串"),
    dict(id="B02", form="② 字段→说明", boundary="非法类型（说明位写了数字）",
         decl={"cell_desc_num": 123},
         expect={"cell_desc_num": 123},
         note="说明位出现数字：类型忠实 vs 一律空串，用实测判定"),
    # ---- form ③: boolean switches ------------------------------------------
    dict(id="C01", form="③ 布尔开关", boundary="仅布尔字段",
         decl={"notes_separated": True},
         expect={"notes_separated": True},
         note="③ 形态与 ① 形态在同一字段上的行为应一致"),
    # ---- form ④: list of names ---------------------------------------------
    dict(id="D01", form="④ 字段清单", boundary="两个名称",
         decl=SEMANTIC + ["cell_a", "cell_b"], mode="replace",
         expect={"cell_a": ("", []), "cell_b": ("", [])},
         note="每个名称按容器给空值"),
    dict(id="D02", form="④ 字段清单", boundary="空清单（只列语义字段）",
         decl=SEMANTIC, mode="replace",
         expect={},
         note="空清单：不添加任何字段，顶层 19 字段仍须齐全"),
    dict(id="D03", form="④ 字段清单", boundary="**非法元素（数字/null 混入）**",
         decl=SEMANTIC + ["cell_c", 7, None], mode="replace",
         expect={"cell_c": ("", [])},
         note="非法元素：不得静默丢弃（要么回显要么记录）"),
    dict(id="D04", form="④ 字段清单", boundary="与真实键同名",
         decl=SEMANTIC + ["status", "case_id"], mode="replace",
         expect=None,
         note="真实值优先"),
    dict(id="D05", form="④ 字段清单", boundary="重复名称",
         decl=SEMANTIC + ["dup_name", "dup_name"], mode="replace",
         expect={"dup_name": ("", [])},
         note="重复名称只应产生一个字段"),
    dict(id="D06", form="④ 字段清单", boundary="超长清单（200 个名称）",
         decl=SEMANTIC + MANY_NAMES, mode="replace",
         expect={n: ("", []) for n in MANY_NAMES},
         note="体量边界：200 个声明字段全部回显"),
    # ---- D: missing / malformed contract containers ------------------------
    dict(id="E01", form="契约容器", boundary="**缺字段（无 output_contract 键）**",
         decl=None, patch="delete", expect={},
         note="缺字段边界：容器给 {}，19 个顶层契约字段仍须齐全"),
    dict(id="E02", form="契约容器", boundary="**非法容器（字符串）**",
         decl="这是一段说明", mode="replace", expect={},
         note="非法容器：不得静默当成空契约"),
    dict(id="E03", form="契约容器", boundary="非法容器（null）",
         decl=None, patch="null", expect={},
         note="null 容器：同上"),
    dict(id="E04", form="契约容器", boundary="空容器（{}）",
         decl={}, mode="replace", expect={},
         note="空契约：合法，等价于没有声明字段"),
    dict(id="E05", form="契约容器", boundary="**声明不全（只声明 1 个未知字段）**",
         decl={"cell_only_one": "字符串"}, mode="replace",
         expect={"cell_only_one": ""},
         note="顶层 19 字段的完整性是否依赖案例的声明：只声明 1 个字段时是否仍写全 19 个"),
]

# Itemised pure-incremental repairs made in this package (see SKILL.md §5 / TEST.md T5)
FIXES = [
    dict(id="F1", where="scripts/main.py: apply_output_contract()",
         what="未知字段名 + 布尔声明：由 `v is True -> semantic.get(k, False)` 改为"
              " `isinstance(v, bool) -> 如实回显声明值`",
         why="实测 A11 声明 true 却回显 false、A12 声明 false 却回显 \"\"，两者都不忠实",
         risk="语义字段（notes_separated 等）仍优先取本次运行真实值：A13/A14 行为不变"),
    dict(id="F2", where="scripts/main.py: apply_output_contract()",
         what="新增数值型声明的忠实回显分支（int/float，且明确排除 bool）",
         why="实测 A04 声明 0 回显 \"\"、B02 声明 123 回显 \"\"，类型不符",
         risk="只在“声明值本身是数字”时生效；str/list/dict/None 分支逻辑未改"),
    dict(id="F3", where="scripts/main.py: apply_output_contract()",
         what="④ 清单形态中的非法元素与非法容器不再静默：写入 result['uncertainty']",
         why="实测 D03 的数字/null 元素、E02/E03 的非法容器此前完全无痕（静默通过）",
         risk="只在输入确实非法时追加一条 uncertainty，正常案例不触发"),
]

FORMS_ORDER = ["① 字段→类型提示", "② 字段→说明", "③ 布尔开关", "④ 字段清单", "契约容器"]


def value_type(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "bool"
    if isinstance(v, (int, float)):
        return "number"
    if isinstance(v, str):
        return "str"
    if isinstance(v, list):
        return "list"
    if isinstance(v, dict):
        return "obj"
    return type(v).__name__


def build_case(base_case, cell, base_material):
    """Build the injected case.

    Default mode is **merge**: the cell's declaration is added on top of the
    case's own `output_contract`, so the injected form/boundary is measured
    while the rest of the contract stays valid (otherwise every cell would only
    measure "the case declared too little").
    `mode="replace"` and `patch` produce the whole-container cells (E*), which
    intentionally measure the incomplete-declaration case.
    """
    case = json.loads(json.dumps(base_case))
    patch = cell.get("patch")
    mode = cell.get("mode", "merge")
    base_contract = case.get("output_contract")
    if patch == "delete":
        case.pop("output_contract", None)
    elif patch == "null":
        case["output_contract"] = None
    elif mode == "replace":
        case["output_contract"] = cell["decl"]
    else:
        merged = dict(base_contract) if isinstance(base_contract, dict) else {}
        decl = cell["decl"]
        if isinstance(decl, dict):
            merged.update(decl)
        elif isinstance(decl, list):
            merged.update({k: "" for k in decl if isinstance(k, str)})
        case["output_contract"] = merged
    if base_material:
        case["material"] = base_material          # cells live in their own dir
    return case


def declared_fields(decl):
    if isinstance(decl, dict):
        return list(decl.keys())
    if isinstance(decl, list):
        return [k for k in decl if isinstance(k, str)]
    return []


def run_cell(cell, base_case, base_material, spec, out_dir, python, entry, timeout,
             contract_fields):
    cell_dir = os.path.join(out_dir, "cells", cell["id"])
    os.makedirs(cell_dir, exist_ok=True)
    case_path = os.path.join(cell_dir, "case.json")
    run_out = os.path.join(cell_dir, "out")
    with open(case_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(build_case(base_case, cell, base_material), fh,
                  ensure_ascii=False, indent=2)
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    argv = [python, entry, "--case", case_path, "--out", run_out]
    if spec:
        argv += ["--spec", spec]
    proc = subprocess.run(argv, cwd=cell_dir, env=env, timeout=timeout,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    rec = dict(cell_id=cell["id"], form=cell["form"], boundary=cell["boundary"],
               declaration=cell["decl"], note=cell["note"],
               exit_code=proc.returncode)
    res_path = os.path.join(run_out, "result.json")
    rec["result_written"] = os.path.isfile(res_path)
    if not rec["result_written"]:
        rec["verdict"] = "crash"
        rec["silent_pass"] = False
        rec["stdout_tail"] = proc.stdout.decode("utf-8", "replace").strip().splitlines()[-4:]
        return rec
    with open(res_path, encoding="utf-8") as fh:
        res = json.load(fh)
    rec["status"] = res.get("status")
    rec["output_contract_echo"] = res.get("output_contract")
    self_check = (res.get("run_meta") or {}).get("self_check") or {}
    rec["self_check_ok"] = self_check.get("ok")
    rec["self_check_problems"] = self_check.get("problems")
    uncertainty = res.get("uncertainty") or []
    rec["uncertainty_count"] = len(uncertainty)
    rec["uncertainty"] = uncertainty
    rec["top_level_keys"] = len(res)
    rec["result_bytes"] = os.path.getsize(res_path)

    # ---- per declared field -------------------------------------------------
    fields = []
    for name in declared_fields(cell["decl"]):
        present = name in res
        actual = res.get(name, None) if present else None
        fields.append({"name": name, "present": present,
                       "type": value_type(actual) if present else "absent",
                       "is_null": bool(present and actual is None),
                       "value": (actual if isinstance(actual, (str, int, float, bool))
                                 or actual is None or
                                 (isinstance(actual, (list, dict)) and len(str(actual)) < 200)
                                 else "<large>")})
    rec["declared_fields"] = fields
    # form (4) cannot express the semantic values: record what the semantic
    # names actually echo in list-form cells (title/slides are not real values)
    if cell["form"].startswith("④"):
        rec["semantic_echo_in_list_form"] = {
            n: value_type(res.get(n)) for n in SEMANTIC if n in res}

    # ---- whole contract surface (19 fields from OUTPUT_CONTRACT.md §1) ------
    missing, nulls = contract_check.check(res, contract_fields)
    rec["contract_fields_missing"] = missing
    rec["contract_fields_null"] = nulls
    rec["contract_surface_complete"] = not missing and not nulls

    # ---- verdict ------------------------------------------------------------
    problems = []
    if cell["expect"] is not None:
        for name, want in cell["expect"].items():
            allowed = want if isinstance(want, tuple) else (want,)
            got = res.get(name, "<absent>")
            if got == "<absent>":
                problems.append("%s 未回显" % name)
            elif not any(value_type(got) == value_type(w)
                         and (value_type(w) not in ("str", "bool", "number") or got == w)
                         for w in allowed):
                problems.append("%s 期望 %s，实测 %s=%r"
                                % (name, " 或 ".join("%s=%r" % (value_type(w), w)
                                                     for w in allowed),
                                   value_type(got), got))
    # semantic cells: real values must win
    if cell["id"] in ("A09", "A10", "D04"):
        if cell["id"] == "A09":
            if res.get("status") != "completed":
                problems.append("status 被声明覆盖：%r" % res.get("status"))
            if not isinstance(res.get("deck"), dict):
                problems.append("deck 被声明覆盖：%r" % type(res.get("deck")))
        if cell["id"] == "A10":
            if not isinstance(res.get("title"), str) or not res.get("title"):
                problems.append("title 未取真实值：%r" % res.get("title"))
            if not isinstance(res.get("render_state"), dict):
                problems.append("render_state 未取真实对象：%r"
                                % type(res.get("render_state")))
    # malformed list elements / malformed containers must be recorded
    if cell["id"] == "D03":
        rec["malformed_recorded"] = any(
            "非法" in str(u) or "output_contract" in str(u) for u in uncertainty)
        if not rec["malformed_recorded"]:
            problems.append("清单中的非法元素（7/None）被静默丢弃")
    if cell["id"] in ("E02", "E03"):
        rec["malformed_recorded"] = any("output_contract" in str(u) for u in uncertainty)
        if not rec["malformed_recorded"]:
            problems.append("非法契约容器被静默当成空契约")
    rec["problems_in_cell"] = problems

    declared_names = declared_fields(cell["decl"])
    mentioned = any(any(n in str(u) for n in declared_names) for u in uncertainty)
    rec["uncertainty_mentions_declared"] = bool(mentioned)
    gate_problems = self_check.get("problems") or []
    rec["caught_by_gate"] = bool(gate_problems)
    incomplete = not rec["contract_surface_complete"]
    if not problems:
        rec["verdict"] = "match"
    elif proc.returncode == 0 and self_check.get("ok") is True and not mentioned \
            and not rec.get("malformed_recorded") and not incomplete:
        rec["verdict"] = "silent-pass"
    else:
        rec["verdict"] = "mismatch-recorded"
    rec["silent_pass"] = rec["verdict"] == "silent-pass"
    return rec


# --------------------------------------------------------------------------- #
# markdown emission
# --------------------------------------------------------------------------- #
def emit_md(report, path):
    cells = report["cells"]
    out = []
    out.append("# CONTRACT-MATRIX.md — 契约四形态 × 边界值矩阵（**逐行实测**）\n")
    out.append("> 本文件由 `scripts/contract_matrix.py --emit-md` 从**真实运行**生成，不是手写表格。")
    out.append("> 每个单元 = 一份完整 `case.json`（只替换 `output_contract`）+ 一次**未经修改的**"
               "端到端运行（`scripts/main.py`）。")
    out.append("> 原始逐单元记录见 `references/contract-matrix-data.json`；修复前的对照记录见 "
               "`references/contract-matrix-before-fix.json`。\n")
    out.append("## 0. 运行命令与判据\n")
    out.append("```bash")
    out.append('python "$SKILL_DIR/scripts/contract_matrix.py" --out <探针目录> \\')
    out.append('  --emit-md "$SKILL_DIR/references/CONTRACT-MATRIX.md"')
    out.append("```\n")
    out.append("| 退出码 | 含义 |")
    out.append("|-|-|")
    out.append("| 0 | 每个单元都写出 `result.json`，且**没有静默通过** |")
    out.append("| 1 | 存在静默通过（既没纠正、也没记录的契约违约） |")
    out.append("| 2 | 参数/输入错误 |")
    out.append("| 3 | 有单元让主流程崩溃（非零退出或无 `result.json`） |\n")
    out.append("每行的判据来自 `references/OUTPUT_CONTRACT.md` §2（四形态回显规则，禁止 null）"
               "与 §5（G2）；`期望` 列即按该规则推出的值。\n")
    s = report["summary"]
    out.append("## 1. 汇总（实测 %d 个单元）\n" % s["cells"])
    out.append("| 指标 | 实测 |")
    out.append("|-|-|")
    for k, label in (("exit_zero", "exit 0 的单元"),
                     ("result_written", "写出 result.json 的单元"),
                     ("self_check_ok", "内部自检 OK 的单元"),
                     ("match", "契约回显符合期望（match）"),
                     ("mismatch_recorded", "回显不符但**被记录/被门拦住**（mismatch-recorded）"),
                     ("caught_by_gate", "自检点名问题的单元（caught by gate）"),
                     ("contract_surface_incomplete", "顶层契约面不完整的单元"),
                     ("crash", "崩溃（无 result.json）"),
                     ("silent_pass", "**静默通过**")):
        out.append("| %s | %d |" % (label, s[k]))
    out.append("")
    out.append("## 2. 逐行实测\n")
    out.append("| 单元 | 形态 | 边界值 | 注入内容（截断） | exit | 写出 result | status | "
               "自检 | 契约面完整 | 契约回显 | 判定 |  静默通过 |")
    out.append("|-|-|-|-|-|-|-|-|-|-|-|-|")
    for c in cells:
        echo = c.get("output_contract_echo")
        echo_s = "—" if c.get("verdict") == "crash" else json.dumps(
            echo, ensure_ascii=False)[:70]
        decl = json.dumps(c["declaration"], ensure_ascii=False)[:60]
        out.append("| %s | %s | %s | `%s` | %s | %s | %s | %s | %s | `%s` | %s | %s |" % (
            c["cell_id"], c["form"], c["boundary"], decl,
            c.get("exit_code"), "是" if c.get("result_written") else "**否**",
            c.get("status", "—"),
            ("OK" if c.get("self_check_ok") else str(c.get("self_check_problems"))[:44]),
            ("是" if c.get("contract_surface_complete") else "**否**"),
            echo_s, c["verdict"], "**是**" if c.get("silent_pass") else "否"))
    out.append("")
    out.append("## 3. 静默通过清单\n")
    silent = [c for c in cells if c.get("silent_pass")]
    if not silent:
        out.append("**本版实测：0 条静默通过。**\n")
        out.append("修复前（对照记录 `contract-matrix-before-fix.json`）为 %d 条，逐条如下：\n"
                   % report["summary"].get("before_fix_silent_pass", 0))
        for row in report.get("before_fix_silent", []):
            out.append("- `%s`（%s / %s）：%s" % (row["cell_id"], row["form"],
                                                 row["boundary"], row["why"]))
        out.append("")
    else:
        for c in silent:
            out.append("- `%s`（%s / %s）：%s" % (c["cell_id"], c["form"], c["boundary"],
                                                 "; ".join(c["problems_in_cell"])))
        out.append("")
    out.append("## 4. 单元级细节（逐 declared 字段）\n")
    for c in cells:
        out.append("### %s · %s · %s" % (c["cell_id"], c["form"], c["boundary"]))
        out.append("")
        out.append("- 注入：`%s`" % json.dumps(c["declaration"], ensure_ascii=False)[:200])
        out.append("- exit=`%s`，写出 result.json=%s，status=%s，顶层键数=%s，result 字节=%s"
                   % (c.get("exit_code"), c.get("result_written"), c.get("status"),
                      c.get("top_level_keys"), c.get("result_bytes")))
        out.append("- 契约回显：`%s`" % json.dumps(c.get("output_contract_echo"),
                                                 ensure_ascii=False)[:160])
        if c.get("declared_fields"):
            out.append("- 声明字段回显：%s" % "; ".join(
                "%s=%s(%s)%s" % (f["name"], f["type"], "null!" if f["is_null"] else "非null",
                                 "" if f["present"] else " [absent]")
                for f in c["declared_fields"][:6]) +
                (" …(+%d)" % (len(c["declared_fields"]) - 6)
                 if len(c["declared_fields"]) > 6 else ""))
        out.append("- 不确定性条数=%s%s" % (
            c.get("uncertainty_count"),
            "（未提及任何声明字段）" if not c.get("uncertainty_mentions_declared") else ""))
        noted = [u for u in (c.get("uncertainty") or [])
                 if "output_contract" in str(u) or "非法" in str(u)]
        for u in noted[:2]:
            out.append("  - 已记录：`%s`" % str(u)[:160])
        out.append("- 顶层契约面：%s%s" % (
            "完整（19/19）" if c.get("contract_surface_complete") else
            "**不完整** —— 缺 %s，null %s；自检问题：%s"
            % (c.get("contract_fields_missing"), c.get("contract_fields_null"),
               "; ".join(str(p) for p in (c.get("self_check_problems") or [])[:3])),
            ""))
        if c.get("semantic_echo_in_list_form"):
            out.append("- ④ 清单形态下语义字段的实际回显类型：`%s`"
                       % json.dumps(c["semantic_echo_in_list_form"], ensure_ascii=False))
        out.append("- 判定：**%s**%s" % (c["verdict"],
                                        ("；问题：" + "; ".join(c["problems_in_cell"]))
                                        if c.get("problems_in_cell") else "（与期望一致）"))
        out.append("")
    out.append("## 5. 本版据此做的纯增量修复（逐条点名）\n")
    out.append("脚本改动**只发生在** `scripts/main.py` 的 `apply_output_contract()` 内，"
               "CLI 参数名/默认值/退出码语义未改；既有脚本其余部分逐字节不变。\n")
    out.append("| # | 位置 | 改动 | 依据（实测单元） | 风险控制 |")
    out.append("|-|-|-|-|-|")
    for f in FIXES:
        out.append("| %s | `%s` | %s | %s | %s |" % (f["id"], f["where"], f["what"],
                                                      f["why"], f["risk"]))
    out.append("")
    out.append("## 6. 未覆盖声明（如实列出）\n")
    for line in report["uncovered"]:
        out.append("- %s" % line)
    out.append("")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out))
    return path


def redact(obj, pairs):
    """Replace machine-specific absolute paths with placeholders so the report
    can be shipped inside the Skill package (hashes/values are untouched)."""
    if isinstance(obj, dict):
        return {k: redact(v, pairs) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact(v, pairs) for v in obj]
    if isinstance(obj, str):
        out = obj
        for needle, token in pairs:
            if not needle:
                continue
            for variant in {needle, needle.replace("\\", "/"),
                            needle.replace("/", "\\")}:
                if variant:
                    out = out.replace(variant, token)
        return re.sub(r"[A-Za-z]:[\\/]", "<ABS>/", out)
    return obj


UNCOVERED = [
    "**只覆盖 `output_contract` 一个契约面**：题面要求的页级结构、模板、字体、页数上限等约束"
    "不在本矩阵内（它们由 `spec_lint` / `export_check` 覆盖）。",
    "**只测回显与门的状态，不测“语义是否合理”**：例如声明 200 个字段会全部回显，"
    "但“该不该声明这么多”不是矩阵能判的。",
    "**平台 3 个正式案例未在本地跑**：本矩阵用自带示例案例作基座（`examples/case.json`），"
    "正式案例的 `output_contract` 声明形态可能超出这 4 种（若出现，按同样方式加一行单元即可复测）。",
    "**未覆盖并发/中断**：单元按顺序单进程执行，不测运行期被中断时的契约回显。",
    "**未覆盖 `--demo` 分支与材料不可读分支的契约回显差异**（那两条分支由 "
    "`references/failure-modes.md` 的状态一致性条目覆盖）。",
    "**未做多次重复**：每个单元运行一次；重复运行的字节稳定性由本包另一条轴"
    "（`scripts/determinism.py`，见 v7 版说明）负责，两者互补。",
]


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="inject every output_contract form + boundary value and record reality")
    ap.add_argument("--case", default=None, help="base case.json (default: packaged examples)")
    ap.add_argument("--spec", default=None, help="deck-spec.json (default: packaged examples)")
    ap.add_argument("--entry", default=DEFAULT_ENTRY, help="entry (default scripts/main.py)")
    ap.add_argument("--python", default=sys.executable, help="interpreter for the runs")
    ap.add_argument("--out", required=True, help="probe dir (cells/, report json)")
    ap.add_argument("--only", default=None, help="comma-separated cell ids")
    ap.add_argument("--timeout", type=int, default=900, help="per-cell timeout in seconds")
    ap.add_argument("--emit-md", default=None, help="write the markdown matrix here")
    ap.add_argument("--json", default=None, help="report path (default <out>/contract_matrix.json)")
    ap.add_argument("--before-fix", default=None,
                    help="optional earlier report json, used to list pre-fix silent passes")
    ap.add_argument("--redact-paths", action="store_true",
                    help="replace machine-specific absolute paths with "
                         "<PROBE_DIR>/<SKILL_DIR>/<CASE_DIR>/<PYTHON>/<ABS> in the "
                         "report and the emitted markdown")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    case_path = args.case or os.path.join(SKILL_DIR, "examples", "case.json")
    spec = args.spec or os.path.join(SKILL_DIR, "examples", "deck-spec.json")
    if not os.path.isfile(case_path):
        print("base case not readable: %s" % case_path, file=sys.stderr)
        return 2
    if spec and not os.path.isfile(spec):
        spec = None
    with open(case_path, encoding="utf-8") as fh:
        base_case = json.load(fh)
    base_material = base_case.get("material")
    if base_material and not os.path.isabs(base_material):
        cand = os.path.join(os.path.dirname(os.path.abspath(case_path)), base_material)
        base_material = cand if os.path.exists(cand) else None
    if not os.path.isfile(args.entry):
        print("entry not found: %s" % args.entry, file=sys.stderr)
        return 2
    os.makedirs(args.out, exist_ok=True)
    contract_fields = contract_check.fields_from_contract(
        os.path.join(SKILL_DIR, "references", "OUTPUT_CONTRACT.md"))
    if not contract_fields:
        print("could not read the contract field list from references/OUTPUT_CONTRACT.md",
              file=sys.stderr)
        return 2

    wanted = None
    if args.only:
        wanted = {s.strip() for s in args.only.split(",") if s.strip()}
    cells = [c for c in CELLS if not wanted or c["id"] in wanted]
    if not cells:
        print("no cell matched --only", file=sys.stderr)
        return 2

    records = []
    for cell in cells:
        rec = run_cell(cell, base_case, base_material, spec, args.out,
                       args.python, args.entry, args.timeout, contract_fields)
        records.append(rec)
        if not args.quiet:
            print("[%s] %-14s exit=%s result=%s verdict=%-8s silent=%s"
                  % (rec["cell_id"], rec["form"], rec.get("exit_code"),
                     rec.get("result_written"), rec["verdict"],
                     rec.get("silent_pass")))
    summary = {
        "cells": len(records),
        "exit_zero": sum(1 for r in records if r.get("exit_code") == 0),
        "result_written": sum(1 for r in records if r.get("result_written")),
        "self_check_ok": sum(1 for r in records if r.get("self_check_ok")),
        "match": sum(1 for r in records if r["verdict"] == "match"),
        "mismatch_recorded": sum(1 for r in records
                                 if r["verdict"] == "mismatch-recorded"),
        "caught_by_gate": sum(1 for r in records if r.get("caught_by_gate")),
        "contract_surface_incomplete": sum(1 for r in records
                                           if r.get("result_written")
                                           and not r.get("contract_surface_complete")),
        "crash": sum(1 for r in records if r["verdict"] == "crash"),
        "silent_pass": sum(1 for r in records if r.get("silent_pass")),
    }
    before_silent = []
    if args.before_fix and os.path.isfile(args.before_fix):
        with open(args.before_fix, encoding="utf-8") as fh:
            old = json.load(fh)
        before_silent = [{"cell_id": c["cell_id"], "form": c["form"],
                          "boundary": c["boundary"],
                          "why": "; ".join(c.get("problems_in_cell", []))}
                         for c in old.get("cells", []) if c.get("silent_pass")]
        summary["before_fix_silent_pass"] = len(before_silent)
    report = {"schema": SCHEMA, "tool": "scripts/contract_matrix.py",
              "base_case": case_path, "spec": spec, "entry": args.entry,
              "python": args.python, "cells": records, "summary": summary,
              "before_fix_silent": before_silent, "uncovered": UNCOVERED,
              "fixes": FIXES}
    report_path = args.json or os.path.join(args.out, "contract_matrix.json")
    if args.redact_paths:
        pairs = [(os.path.abspath(args.out), "<PROBE_DIR>"),
                 (os.path.abspath(SKILL_DIR), "<SKILL_DIR>"),
                 (os.path.dirname(os.path.abspath(case_path)), "<CASE_DIR>"),
                 (args.python, "<PYTHON>")]
        report["_redaction"] = {"applied": True,
                                "replaced": ["<PROBE_DIR>", "<SKILL_DIR>", "<CASE_DIR>",
                                             "<PYTHON>",
                                             "<ABS> (remaining drive-letter path)"],
                                "note": "only path strings; verdicts and values are measured"}
        report = redact(report, pairs)
    with open(report_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    if args.emit_md:
        emit_md(report, args.emit_md)
    if not args.quiet:
        print("-" * 64)
        print("report : %s" % report_path)
        print("cells=%d exit0=%d result=%d selfcheck_ok=%d match=%d "
              "mismatch_recorded=%d gate_caught=%d incomplete_surface=%d crash=%d silent=%d"
              % (summary["cells"], summary["exit_zero"], summary["result_written"],
                 summary["self_check_ok"], summary["match"],
                 summary["mismatch_recorded"], summary["caught_by_gate"],
                 summary["contract_surface_incomplete"], summary["crash"],
                 summary["silent_pass"]))
    if summary["crash"]:
        return 3
    return 1 if summary["silent_pass"] else 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    sys.exit(main())
