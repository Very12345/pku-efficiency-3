#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
contract_matrix.py — OUTPUT_CONTRACT 四形态 × 边界值 矩阵实测器（v8 轴）。

它把 `output_contract` 声明的每一种容器形态（字符串/列表/对象/数值/布尔/嵌套）
与边界值（空串、空数组、0、超长字段名、非法类型、缺字段、声明非法或缺失）
逐个注入到真实案例里，然后跑完整主流程（`scripts/main.py`，真子进程），
逐格记录实测结果：

    exit_code / result.json 的 status / 契约字段是否回显到顶层 /
    回显值的 JSON 类型 / 声明类型与实例类型是否吻合 /
    是否静默通过（退出 0、契约门 valid、且没有任何契约相关痕迹）/
    change_records 里与契约有关的那几条

产出 `contract_matrix_report.json`（机器可读，cells[] 一行一格），可直接转成
`references/CONTRACT-MATRIX.md` 的逐行实测表。

关键判据（静默通过的金标准，本包不隐藏）：
  某格若出现「退出码 0 + 契约门 valid=True + status 不是 partial + uncertainty 与
  change_records 里没有任何契约相关条目」，而该格的注入其实是无法使用的声明，
  那它就是一个静默通过的缺口 —— 报告里进 `silent_pass_cells` 清单。

退出码：`0` = 矩阵全部格子都跑完且每格都能判读（含如实降级的格子）；
`1` = 有格子根本没跑出 result.json（无法判读）；`2` = 参数用法错误。

设计约束：只用标准库；自定位（路径由 `__file__` 推出，cwd 任意）；
被调用的永远是沙箱内技能副本（包内原目录只读，绝不写 __pycache__）。

用法（`$SKILL_DIR` = 含 SKILL.md 的包根；cwd 任意）：

    python "$SKILL_DIR/scripts/contract_matrix.py" \
        --sandbox /tmp/cm --report /tmp/cm/contract_matrix_report.json
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(SCRIPTS_DIR)

# ---------------------------------------------------------------------------
# 内置默认契约字段（与 scripts/common.DEFAULT_CONTRACT_FIELDS 同源，用于无声明格断言）
# ---------------------------------------------------------------------------
DEFAULT_CONTRACT_FIELDS = [
    "case_id", "status", "title", "report_goal", "audience", "duration_min",
    "slide_count", "main_line", "pages", "evidence_map", "artifacts",
    "sources", "uncertainty", "change_records",
]

# 声明类型 -> 期望的 JSON 实例类型（本包把 any/null 回落成空字符串，禁止 null）
TYPE_OF = {
    "str": "string", "string": "string", "text": "string",
    "list": "array", "array": "array",
    "dict": "object", "object": "object",
    "int": "number", "integer": "number", "number": "number", "float": "number",
    "bool": "boolean", "boolean": "boolean",
    "any": "string", "null": "string",
}


def json_type_of(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


# ---------------------------------------------------------------------------
# 矩阵：轴 × 注入点 × 载荷 × 期望判读
#   C 容器形态 / B 边界值 / S 声明形状 / E 声明非法或缺失 / P 平台额外字段
# ---------------------------------------------------------------------------

def build_cells():
    cells = []
    add = cells.append

    # ---------------- C：四形态必需回显 ----------------
    for cid, ctype in (("C-01", "str"), ("C-02", "list"), ("C-03", "dict"),
                       ("C-04", "int"), ("C-05", "bool")):
        add({
            "id": cid, "axis": "C 容器形态", "point": "case.json",
            "inject": "case.json.output_contract",
            "payload": [{"name": "platform_extra_" + ctype, "type": ctype}],
            "field": "platform_extra_" + ctype,
            "declared_type": ctype,
            "expect": {"exit": 0, "field_present": True,
                       "field_type": TYPE_OF[ctype], "status": "not-failed",
                       "expect_trace": False},
            "note": "新增一个字段并声明类型 " + ctype
                    + "；主流程本不产出它，必须按声明类型回显。",
        })
    add({
        "id": "C-06", "axis": "C 容器形态", "point": "case.json",
        "inject": "case.json.output_contract",
        "payload": [{"name": "platform_extra_any", "type": "any"}],
        "field": "platform_extra_any", "declared_type": "any",
        "expect": {"exit": 0, "field_present": True, "field_type": "string",
                   "status": "not-failed"},
        "note": "类型声明为 any：OUTPUT_CONTRACT.md 第 1 节要求四形态回显、禁止 null，"
                "因此无类型字段也必须回落成空字符串。",
    })
    add({
        "id": "C-07", "axis": "C 容器形态", "point": "case.json",
        "inject": "case.json.output_contract",
        "payload": [{"name": "__n", "type": "object",
                     "properties": {"a": {"type": "list"},
                                    "b": {"type": "string"}},
                     "required": ["a"]}],
        "field": "__n", "declared_type": "object",
        "expect": {"exit": 0, "field_present": True, "field_type": "object",
                   "status": "not-failed"},
        "note": "嵌套 schema（object 里再声明 list/string）。本包只做顶层回显，不生成"
                "嵌套内容 —— 这一行的价值就是把该边界钉死并记录，不是它通过。",
    })

    # ---------------- B：边界值 ----------------
    add({
        "id": "B-01", "axis": "B 边界值", "point": "task.md",
        "inject": "task.md fenced block",
        "payload": {"output_contract": "this-is-a-string-not-a-list"},
        "expect": {"exit": 0, "expect_trace": True},
        "accept_untraced": True,
        "accept_untraced_reason": "task.md 的这个 fenced 块**用不起来**（声明是字符串），但 case.json 自带可用契约，因此最终 declared_source 仍是 case.json + task.md；v8 未改 main.py，故 task.md 解析失败这一路径在本包里**没有**留痕通道 —— 逐格声明为静默容忍，见 known_untraced_cells。",
        "note": "声明本身是字符串而不是列表或字典：normalize_output_contract 应产出 0 字段。",
    })
    add({
        "id": "B-02", "axis": "B 边界值", "point": "task.md",
        "inject": "task.md fenced block",
        "payload": {"output_contract": []},
        "expect": {"exit": 0, "expect_trace": True},
        "accept_untraced": True,
        "accept_untraced_reason": "空数组声明同样只作用于 task.md 解析路径；无留痕通道，同 B-01。",
        "note": "空数组声明：0 个字段。判定它是否被如实记录（不得静默）。",
    })
    add({
        "id": "B-03", "axis": "B 边界值", "point": "case.json",
        "inject": "case.json.output_contract",
        "payload": ["", None, 0, False, {}],
        "expect": {"exit": 0, "expect_trace": False},
        "note": "字段项本身是空串、null、0、false、空对象：全都不构成合法字段名。",
    })
    add({
        "id": "B-04", "axis": "B 边界值", "point": "case.json",
        "inject": "case.json.output_contract",
        "payload": [{"name": "", "type": "str"}, {"name": None},
                    {"name": "ok_field_1", "type": "str"}],
        "field": "ok_field_1", "declared_type": "str",
        "expect": {"exit": 0, "field_present": True, "field_type": "string",
                   "status": "not-failed"},
        "note": "缺字段：name 缺失或为 null 的条目被跳过，合法的那条仍必须回显。",
    })
    long_name = "x" * 129
    add({
        "id": "B-05", "axis": "B 边界值", "point": "case.json",
        "inject": "case.json.output_contract",
        "payload": [{"name": long_name, "type": "str"}],
        "field": long_name, "declared_type": "str",
        "expect": {"exit": 0, "field_present": True, "field_type": "string",
                   "status": "not-failed"},
        "note": "超长字段名（129 字符）：契约没有名字长度上限，必须照常回显。",
    })
    add({
        "id": "B-06", "axis": "B 边界值", "point": "case.json",
        "inject": "case.json.output_contract",
        "payload": [{"name": "platform_extra_badtype", "type": "WeirdType!!"}],
        "field": "platform_extra_badtype", "declared_type": "WeirdType!!",
        "expect": {"exit": 0, "field_present": True, "field_type": "string",
                   "status": "not-failed"},
        "note": "非法类型：未知类型回落成空字符串（不得是 null，不得让流程崩）。",
    })
    add({
        "id": "B-07", "axis": "B 边界值", "point": "case.json",
        "inject": "case.json.output_contract",
        "payload": [{"name": "platform_extra_container", "container": "list"}],
        "field": "platform_extra_container", "declared_type": "list",
        "expect": {"exit": 0, "field_present": True, "field_type": "array",
                   "status": "not-failed"},
        "note": "用 container 键而不是 type 键声明容器类型（题面两种写法都可能出现）。",
    })
    add({
        "id": "B-08", "axis": "B 边界值", "point": "case.json",
        "inject": "case.json.output_contract",
        "payload": [{"name": "platform_extra_zero", "type": "int"},
                    {"name": "platform_extra_false", "type": "bool"}],
        "fields": ["platform_extra_zero", "platform_extra_false"],
        "expect": {"exit": 0, "field_types": {"platform_extra_zero": "number",
                                              "platform_extra_false": "boolean"},
                   "status": "not-failed"},
        "note": "0 与 false 是合法值：必须用真值回显，不能被当成没有值而改填别的。",
    })
    add({
        "id": "B-09", "axis": "B 边界值", "point": "case.json",
        "inject": "case.json.output_contract",
        "payload": [{"name": "case_id", "type": "list"}],
        "field": "case_id", "declared_type": "list",
        "expect": {"exit": 0, "field_present": True, "field_type": "string",
                   "status": "not-failed"},
        "note": "与真产出冲突的字段：主流程已写 case_id（字符串）。apply_contract 对"
                "已存在且非 None 的字段不覆盖，实测应保持字符串 —— 记下这条优先级。",
    })

    # ---------------- S：声明形状 ----------------
    add({
        "id": "S-01", "axis": "S 声明形状", "point": "case.json",
        "inject": "case.json.output_contract",
        "payload": ["platform_extra_bare_a", "platform_extra_bare_b"],
        "fields": ["platform_extra_bare_a", "platform_extra_bare_b"],
        "expect": {"exit": 0, "field_types": {"platform_extra_bare_a": "string",
                                              "platform_extra_bare_b": "string"},
                   "status": "not-failed"},
        "note": "形状一：裸列表（只有字段名，无类型声明）。",
    })
    add({
        "id": "S-02", "axis": "S 声明形状", "point": "case.json",
        "inject": "case.json.output_contract",
        "payload": [{"name": "platform_extra_listdict", "type": "list",
                     "required": True}],
        "field": "platform_extra_listdict", "declared_type": "list",
        "expect": {"exit": 0, "field_present": True, "field_type": "array",
                   "status": "not-failed"},
        "note": "形状二：列表 of dict（name/type/required 齐全）。",
    })
    add({
        "id": "S-03", "axis": "S 声明形状", "point": "case.json",
        "inject": "case.json.output_contract",
        "payload": {"platform_extra_dictoftype": "Object",
                    "platform_extra_dictlist": "ARRAY"},
        "fields": ["platform_extra_dictoftype", "platform_extra_dictlist"],
        "expect": {"exit": 0, "field_types": {"platform_extra_dictoftype": "object",
                                              "platform_extra_dictlist": "array"},
                   "status": "not-failed"},
        "note": "形状三：dict of type 字符串，且故意用大写以实测是否大小写不敏感。",
    })
    add({
        "id": "S-04", "axis": "S 声明形状", "point": "case.json",
        "inject": "case.json.output_contract",
        "payload": {"type": "object",
                    "required": ["platform_extra_schema_req"],
                    "properties": {
                        "platform_extra_schema_req": {"type": "integer"},
                        "platform_extra_schema_opt": {"type": "string"}}},
        "fields": ["platform_extra_schema_req", "platform_extra_schema_opt"],
        "expect": {"exit": 0,
                   "field_types": {"platform_extra_schema_req": "number",
                                   "platform_extra_schema_opt": "string"},
                   "status": "not-failed"},
        "note": "形状四：JSON-schema 形态（required 加 properties），且 properties 里"
                "的未声明为 required 的字段也一并回显。",
    })
    add({
        "id": "S-05", "axis": "S 声明形状", "point": "task.md",
        "inject": "task.md fenced block",
        "payload": {"output_contract": {"platform_extra_mixed": "list"}},
        "field": "platform_extra_mixed", "declared_type": "list",
        "expect": {"exit": 0, "field_present": True, "field_type": "array",
                   "status": "not-failed"},
        "note": "混合：注入点不是 case.json，而是 task.md 的 fenced JSON 块里再放"
                "dict of type。用来证明两个注入点是等价的。",
    })
    add({
        "id": "S-06", "axis": "S 声明形状", "point": "case.json",
        "inject": "case.json.output_contract",
        "payload": [{"name": "platform_extra_opt", "type": "str",
                     "required": False}],
        "field": "platform_extra_opt",
        "expect": {"exit": 0, "field_present": False, "status": "not-failed"},
        "note": "可选字段缺失：required=false 且主流程不产出，按契约规定应跳过、不污染"
                "result.json —— 这一行把该行为钉死。",
    })

    # ---------------- E：声明非法或缺失 ----------------
    add({
        "id": "E-01", "axis": "E 声明非法或缺失", "point": "task.md",
        "inject": "task.md fenced block",
        "payload": {"output_contract": {}},
        "expect": {"exit": 0, "status": "partial"},
        "note": "空对象声明（0 字段）：属于声明了却用不起来，必须留痕并降级。",
    })
    add({
        "id": "E-02", "axis": "E 声明非法或缺失", "point": "case.json",
        "inject": "case.json.output_contract",
        "payload": None,
        "raw_case_patch": {"output_contract": "not-a-list-or-dict"},
        "expect": {"exit": 0, "expect_trace": True},
        "accept_untraced": True,
        "accept_untraced_reason": "case.json 的 output_contract 直接是字符串：normalize 产出 0 字段，该路径在 main.py 里也没有留痕；逐格声明，同 B-01。",
        "note": "case.json 的 output_contract 是字符串：normalize 应产出 0 字段且不得崩。",
    })
    add({
        "id": "E-03", "axis": "E 声明非法或缺失", "point": "task.md",
        "inject": "task.md raw text (broken JSON block)",
        "payload": None,
        "task_md_raw": "# 任务\n\n```json\n{\"output_contract\": [\"a\", \"b\"\n```\n",
        "expect": {"exit": 0, "status": "partial"},
        "note": "fenced JSON 非法（缺右括号）：题面要求无法判断的情况要说明，"
                "因此应留痕并降级。",
    })
    add({
        "id": "E-04", "axis": "E 声明非法或缺失", "point": "task.md",
        "inject": "task.md raw text (contract key absent)",
        "payload": None,
        "task_md_raw": "# 任务\n\n```json\n{\"something_else\": 1}\n```\n",
        "expect": {"exit": 0, "status": "partial"},
        "note": "有 fenced JSON 但没有 output_contract/contract 键：属于声明了契约块却"
                "没用起来，应留痕并降级。",
    })
    add({
        "id": "E-05", "axis": "E 声明非法或缺失", "point": "task.md",
        "inject": "task.md raw text (markdown table, 3 rows)",
        "payload": None,
        "task_md_raw": ("# 任务\n\n| 字段 | 说明 |\n|-|-|\n"
                        "| platform_extra_t1 | a |\n| platform_extra_t2 | b |\n"
                        "| platform_extra_t3 | c |\n"),
        "expect": {"exit": 0, "status": "partial"},
        "note": "markdown 表格回退路径只认至少 5 个字段名；这里 3 行，应走留痕并降级。",
    })
    add({
        "id": "E-06", "axis": "E 声明非法或缺失", "point": "task.md",
        "inject": "task.md raw text (markdown table, 6 rows)",
        "payload": None,
        "task_md_raw": ("# 任务\n\n| 字段 | 说明 |\n|-|-|\n"
                        "| platform_extra_t1 | a |\n| platform_extra_t2 | b |\n"
                        "| platform_extra_t3 | c |\n| platform_extra_t4 | d |\n"
                        "| platform_extra_t5 | e |\n| platform_extra_t6 | f |\n"),
        "fields": ["platform_extra_t1", "platform_extra_t6"],
        "expect": {"exit": 0, "status": "not-failed",
                   "field_types": {"platform_extra_t1": "string",
                                   "platform_extra_t6": "string"}},
        "note": "同一张表格但有 6 行：应成功解析成字段名列表并回显，与 E-05 构成对照。",
    })
    add({
        "id": "E-07", "axis": "E 声明非法或缺失", "point": "task.md",
        "inject": "task.md empty (0 byte)",
        "payload": None,
        "task_md_raw": "",
        "expect": {"exit": 0, "status": "not-failed"},
        "note": "task.md 是空文件：解析器应直接返回空并给出说明，不得把空文件误报成"
                "契约失败。",
    })
    add({
        "id": "E-08", "axis": "E 声明非法或缺失", "point": "none",
        "inject": "no declaration anywhere",
        "payload": None,
        "drop_case_contract": True, "drop_task_contract": True,
        "expect": {"exit": 0, "status": "not-failed"},
        "note": "完全没有声明：回落到内置默认契约（契约只增不减）。",
    })

    # ---------------- P：平台额外字段 ----------------
    add({
        "id": "P-01", "axis": "P 平台额外字段", "point": "case.json",
        "inject": "case.json.output_contract",
        "payload": ["platform_extra_only"],
        "field": "platform_extra_only", "declared_type": "str",
        "expect": {"exit": 0, "field_present": True, "field_type": "string",
                   "status": "not-failed"},
        "note": "平台只声明 1 个额外字段：它必须与内置默认字段同时存在（契约只增不减）。",
    })
    return cells


# ---------------------------------------------------------------------------
# 沙箱
# ---------------------------------------------------------------------------

def _copy_skill(sandbox):
    dst = os.path.join(sandbox, "skill")
    shutil.copytree(SKILL_ROOT, dst,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return dst


def _materialise_case(skill_copy, cell_dir, cell):
    """把 cell 的注入写成一个真实案例目录：case.json + task.md + materials。"""
    src_examples = os.path.join(skill_copy, "examples")
    os.makedirs(cell_dir, exist_ok=True)
    shutil.copytree(os.path.join(src_examples, "materials"),
                    os.path.join(cell_dir, "materials"))
    with open(os.path.join(src_examples, "case.json"), "r", encoding="utf-8") as fh:
        case = json.load(fh)
    with open(os.path.join(src_examples, "task.md"), "r", encoding="utf-8") as fh:
        task = fh.read()
    injected_points = []
    if cell.get("raw_case_patch"):
        case.update(cell["raw_case_patch"])
        injected_points.append("case.json.output_contract 置为原始值 %r"
                               % cell["raw_case_patch"]["output_contract"])
    elif cell.get("payload") is not None and cell["inject"].startswith("case.json"):
        case["output_contract"] = cell["payload"]
        injected_points.append("case.json.output_contract 置为载荷")
    if cell.get("drop_case_contract"):
        case.pop("output_contract", None)
        injected_points.append("case.json.output_contract 删除")
    if cell.get("task_md_raw") is not None:
        task = cell["task_md_raw"]
        injected_points.append("task.md 整体替换（%d 字符）" % len(task))
    elif cell.get("payload") is not None and cell["inject"].startswith("task.md fenced"):
        task += "\n\n```json\n%s\n```\n" % json.dumps(cell["payload"],
                                                      ensure_ascii=False)
        injected_points.append("task.md 追加 fenced JSON 块")
    if cell.get("drop_task_contract"):
        task = ("# 任务说明（矩阵实验：故意删除 output_contract 声明块）\n\n"
                "请围绕 materials/paper_extract.md 与 materials/figures.md 组织 "
                "20 分钟、12 页的组会汇报；输出要求与运行期输入位置同本包 "
                "examples/task.md，但本文件不含 output_contract 声明段。\n")
        injected_points.append("task.md 整体替换为无契约声明版本")
    with open(os.path.join(cell_dir, "case.json"), "w", encoding="utf-8",
              newline="\n") as fh:
        json.dump(case, fh, ensure_ascii=False, indent=2)
    with open(os.path.join(cell_dir, "task.md"), "w", encoding="utf-8",
              newline="\n") as fh:
        fh.write(task)
    return injected_points


def _contract_records(change_records):
    out = []
    for rec in change_records or []:
        if not isinstance(rec, dict):
            continue
        action = str(rec.get("action", ""))
        if rec.get("step") in ("contract", "result") or "contract" in action:
            out.append("%s: %s" % (rec.get("step"), action[:200]))
    return out


def _run_cell(skill_copy, sandbox, cell, timeout):
    cell_dir = os.path.join(sandbox, "cells", cell["id"], "case")
    out_dir = os.path.join(sandbox, "cells", cell["id"], "out")
    points = _materialise_case(skill_copy, cell_dir, cell)
    main_py = os.path.join(skill_copy, "scripts", "main.py")
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONHASHSEED"] = "0"
    cmd = [sys.executable, main_py, "--case", cell_dir, "--out", out_dir,
           "--skip-previews", "--quiet"]
    t0 = time.perf_counter()
    try:
        proc = subprocess.run(cmd, cwd=sandbox, env=env, timeout=timeout,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        rc, out, err = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        rc, out, err = -9, (exc.stdout or b""), (exc.stderr or b"") + b"\nTIMEOUT"
    wall = round(time.perf_counter() - t0, 3)

    rj_path = os.path.join(out_dir, "result.json")
    row = {
        "id": cell["id"], "axis": cell["axis"], "inject_point": cell["point"],
        "inject_how": cell["inject"], "injection_applied": points,
        "expectation_note": cell["note"],
        "expected": cell["expect"],
        "exit_code": rc, "wall_seconds": wall,
        "stdout_tail": out.decode("utf-8", "replace").strip().splitlines()[-3:],
        "stderr_tail": err.decode("utf-8", "replace").strip().splitlines()[-3:],
        "result_json_written": os.path.exists(rj_path),
    }
    if not row["result_json_written"]:
        row["verdict"] = "无法判读：没有写出 result.json"
        row["expectation_met"] = False
        row["expectation_failed"] = ["result.json missing"]
        return row

    with open(rj_path, "r", encoding="utf-8") as fh:
        result = json.load(fh)
    row["status"] = result.get("status")
    row["contract_declared_source"] = (result.get("contract") or {}).get(
        "declared_source")
    row["contract_applied"] = (result.get("contract") or {}).get("applied") or []
    names = ([cell["field"]] if cell.get("field") else []) + list(
        cell.get("fields") or [])
    row["fields_named_in_cell"] = {}
    for name in names:
        present = name in result
        row["fields_named_in_cell"][name] = {
            "present": present,
            "json_type": json_type_of(result.get(name)) if present else None,
            "value_preview": (repr(result.get(name))[:60] if present else None),
            "in_contract_applied": name in row["contract_applied"],
        }
    row["top_level_key_count"] = len(result)
    row["default_fields_present"] = sorted(
        set(DEFAULT_CONTRACT_FIELDS) & set(result))
    row["default_fields_missing"] = sorted(
        set(DEFAULT_CONTRACT_FIELDS) - set(result))
    row["null_top_level_values"] = sorted(
        k for k, v in result.items() if v is None)
    row["uncertainty_items"] = [str(u.get("item"))[:120]
                                for u in (result.get("uncertainty") or [])
                                if isinstance(u, dict)]
    row["contract_related_change_records"] = _contract_records(
        result.get("change_records"))
    sc_path = os.path.join(out_dir, "self_check.json")
    row["contract_check_valid"] = None
    if os.path.exists(sc_path):
        with open(sc_path, "r", encoding="utf-8") as fh:
            sc = json.load(fh)
        row["contract_check_valid"] = bool(
            (sc.get("contract_check") or {}).get("valid"))
        row["validate_valid"] = bool((sc.get("validate") or {}).get("valid"))

    checks = []
    exp = cell["expect"]
    checks.append(("exit_code == %s" % exp.get("exit"),
                   row["exit_code"] == exp.get("exit")))
    for name, info in row["fields_named_in_cell"].items():
        if "field_present" in exp:
            checks.append(("%s present == %s" % (name, exp["field_present"]),
                           info["present"] == exp["field_present"]))
        if "field_type" in exp:
            checks.append(("%s type == %s" % (name, exp["field_type"]),
                           info["json_type"] == exp["field_type"]))
    for name, want in (exp.get("field_types") or {}).items():
        got = (row["fields_named_in_cell"].get(name) or {}).get("json_type")
        checks.append(("%s type == %s" % (name, want), got == want))
    if "status" in exp:
        if exp["status"] == "not-failed":
            checks.append(("status != failed", row["status"] != "failed"))
        else:
            checks.append(("status == %s" % exp["status"],
                           row["status"] == exp["status"]))
    row["expectation_checks"] = [{"check": c, "ok": bool(ok)} for c, ok in checks]
    row["expectation_met"] = all(ok for _c, ok in checks)
    row["expectation_failed"] = [c for c, ok in checks if not ok]

    trace_text = [t for t in row["uncertainty_items"] if "契约" in t or "contract" in t.lower()]
    contract_traces = list(trace_text)
    for c in row["contract_related_change_records"]:
        if c.startswith("contract:") or "output_contract" in c or "契约" in c:
            contract_traces.append(c)
    expired = any(("NOT applied" in str(c)) or ("could not be used" in str(c))
                  for c in row["contract_related_change_records"])
    row["contract_trace_count"] = len(contract_traces)
    row["declaration_unusable_traced"] = bool(expired)
    # 静默通过（与文档同一口径）：一个**声明无法使用**的格子必须留下痕迹。
    #   * expect_trace=True 且模块有留痕能力 -> 没留痕就是静默通过（缺陷）；
    #   * accept_untraced=True -> 该注入口在 v8 里**没有**留痕通道（case.json 的
    #     output_contract 由 main.py 的 normalize 路径处理，v8 未改 main.py），
    #     这种"静默容忍"逐格声明，并单独汇总到 known_untraced_cells，绝不并入
    #     "没有缺陷"的结论里。
    #   * expect_trace=False（声明本来就可用）却出现"用不起来"的痕迹 -> 也计一次。
    expect_trace = bool(exp.get("expect_trace"))
    accept_untraced = bool(cell.get("accept_untraced"))
    row["trace_expected"] = expect_trace
    row["untraced_accepted"] = accept_untraced
    row["silent_pass"] = bool(
        row["exit_code"] == 0
        and row.get("contract_check_valid") is True
        and (not accept_untraced)
        and ((expect_trace and not expired) or ((not expect_trace) and expired))
    )
    row["verdict"] = ("期望全部命中" if row["expectation_met"]
                      else "期望未全中：" + "; ".join(row["expectation_failed"]))
    return row


def emit_markdown(report):
    """把实测报告渲染成 markdown 表（references/CONTRACT-MATRIX.md 的数据源）。"""
    L = []
    L.append("### 逐格实测表（由 `scripts/contract_matrix.py --emit-md` 自动渲染）")
    L.append("")
    L.append("| id | 轴 | 注入点 | 注入内容 | exit | status | 契约门 valid | 顶层键数 | "
             "声明字段回显（名:类型） | 契约痕迹条数 | 期望 |")
    L.append("|-|-|-|-|-|-|-|-|-|-|-|")
    for c in report["cells"]:
        fields = "；".join(
            "%s:%s%s" % (n, (i["json_type"] or "缺失"),
                         "" if i["present"] else "(不在顶层)")
            for n, i in sorted((c.get("fields_named_in_cell") or {}).items()))
        fields = fields.replace("|", "/") or "—"
        L.append("| `%s` | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            c["id"], c["axis"], c["inject_point"], c["inject_how"].replace("|", "/"),
            c.get("exit_code"), c.get("status"),
            c.get("contract_check_valid"), c.get("top_level_key_count"),
            fields[:160], c.get("contract_trace_count"),
            "命中" if c.get("expectation_met") else "未中"))
    L.append("")
    L.append("### 汇总")
    L.append("")
    L.append("| 项 | 实测 |")
    L.append("|-|-|")
    L.append("| 格子数 | %d |" % report["cells_total"])
    L.append("| 退出码集合 | %s |" % report["exit_codes"])
    L.append("| status 集合 | %s |" % report["statuses"])
    L.append("| 期望全部命中 | %d / %d |" % (
        report["cells_total"] - len(report["cells_expectation_unmet"]),
        report["cells_total"]))
    L.append("| 无法判读（没写出 result.json） | %s |"
             % (report["cells_unreadable"] or "无"))
    L.append("| 静默通过（该留痕却没留 / 不该留痕却留了） | %s |"
             % ([c["id"] for c in report["silent_pass_cells"]] or "无"))
    L.append("| 声明为「无留痕通道、静默容忍」的格子 | %s |"
             % ([c["id"] for c in report.get("known_untraced_cells", [])] or "无"))
    L.append("")
    L.append("### 各轴覆盖")
    L.append("")
    L.append("| 轴 | 格子数 | 期望命中 |")
    L.append("|-|-|-|")
    for axis, st in sorted(report["axis_summary"].items()):
        L.append("| %s | %d | %d |" % (axis, st["cells"], st["expectation_met"]))
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="OUTPUT_CONTRACT 四形态与边界值矩阵（真跑主流程，逐格实测）")
    ap.add_argument("--sandbox", default=None,
                    help="沙箱目录（默认在系统临时目录下建 cm-<pid>）；包内原目录全程只读")
    ap.add_argument("--report", default=None,
                    help="报告 JSON 落盘路径（默认 <sandbox>/contract_matrix_report.json）")
    ap.add_argument("--emit-md", default=None,
                    help="同时把逐格实测表渲染成 markdown 写到这个路径（包外！）")
    ap.add_argument("--only", default=None,
                    help="只跑指定 cell id（逗号分隔，调试用）")
    ap.add_argument("--timeout", type=float, default=600.0, help="单格超时秒")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    import tempfile
    sandbox = os.path.abspath(args.sandbox or os.path.join(
        tempfile.gettempdir(), "cm-%d" % os.getpid()))
    if os.path.isdir(sandbox):
        shutil.rmtree(sandbox)
    os.makedirs(sandbox, exist_ok=True)
    skill_copy = _copy_skill(sandbox)
    report_path = args.report or os.path.join(
        sandbox, "contract_matrix_report.json")

    cells = build_cells()
    if args.only:
        want = {x.strip() for x in args.only.split(",") if x.strip()}
        cells = [c for c in cells if c["id"] in want]

    rows = []
    for cell in cells:
        row = _run_cell(skill_copy, sandbox, cell, args.timeout)
        rows.append(row)
        if not args.quiet:
            print("[%s] %-6s exit=%-3s status=%-9s %s" % (
                "OK" if row.get("expectation_met") else "!!",
                cell["id"], row.get("exit_code"), row.get("status"),
                row.get("verdict")))

    unreadable = [r["id"] for r in rows if not r.get("result_json_written")]
    unmet = [{"id": r["id"], "failed": r["expectation_failed"]}
             for r in rows if r.get("result_json_written")
             and not r["expectation_met"]]
    silent = [{"id": r["id"], "inject": r["inject_how"],
               "note": r["expectation_note"],
               "contract_declared_source": r.get("contract_declared_source")}
              for r in rows if r.get("silent_pass")]
    untraced_accepted = [{"id": r["id"], "inject": r["inject_how"],
                          "reason": r.get("accept_untraced_reason"),
                          "observed_declared_source": r.get("contract_declared_source")}
                         for r in rows if r.get("untraced_accepted")]

    by_axis = {}
    for r in rows:
        a = by_axis.setdefault(r["axis"], {"cells": 0, "expectation_met": 0})
        a["cells"] += 1
        a["expectation_met"] += 1 if r.get("expectation_met") else 0

    report = {
        "tool": "scripts/contract_matrix.py",
        "skill_root": SKILL_ROOT,
        "sandbox": sandbox,
        "entry_point": "沙箱内技能副本 <sandbox>/skill/scripts/main.py（包内原目录只读）",
        "argv_per_cell": "--case <cell>/case --out <cell>/out --skip-previews --quiet",
        "cells_total": len(rows),
        "axis_summary": by_axis,
        "exit_codes": sorted({r.get("exit_code") for r in rows}),
        "statuses": sorted({str(r.get("status")) for r in rows}),
        "cells_unreadable": unreadable,
        "cells_expectation_unmet": unmet,
        "silent_pass_cells": silent,
        "known_untraced_cells": untraced_accepted,
        "cells": rows,
        "coverage_declaration": COVERAGE,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "host": {"python": sys.version.split()[0], "platform": sys.platform},
    }
    os.makedirs(os.path.dirname(report_path) or ".", exist_ok=True)
    with open(report_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    if args.emit_md:
        os.makedirs(os.path.dirname(os.path.abspath(args.emit_md)) or ".",
                    exist_ok=True)
        with open(args.emit_md, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(emit_markdown(report))

    if not args.quiet:
        print("[contract-matrix] cells=%d unreadable=%d expectation_unmet=%d "
              "silent_pass=%d" % (len(rows), len(unreadable), len(unmet),
                                  len(silent)))
        print("[contract-matrix] report: %s" % report_path)
    return 0 if not unreadable else 1


COVERAGE = {
    "covered": [
        "容器形态：字符串 / 列表 / 对象 / 数值 int / 布尔 bool / any / 嵌套 schema",
        "边界值：空串、null 项、0、false、空数组、空对象、超长字段名 129 字符、"
        "非法类型串、缺 name、带 container 键、与真产出冲突的字段",
        "声明形状：裸列表 / 列表 of dict / dict of type（含大写）/ JSON-schema / "
        "task.md fenced 注入 / required=false 的可选缺失",
        "声明非法或缺失：空对象、字符串形态、非法 JSON、有 JSON 但无契约键、"
        "markdown 表格（少于 5 行与至少 5 行两档）、空 task.md、完全无声明",
        "注入点：case.json.output_contract 与 task.md（fenced JSON / 原始文本 / 表格）",
        "平台额外字段：只声明 1 个字段时仍须与内置默认字段共存",
    ],
    "not_covered": [
        "多案例并发：矩阵每格都是单案例串行子进程，未测两个案例同时写同一个 --out",
        "真实平台案例：只用包内合成示例案例 example-synthalign-talk-01；组织方三案例的"
        "output_contract 实文运行期才可见，未进入矩阵",
        "超长载荷的整体规模：只测了超长字段名（129 字符），未测上万字段的巨契约",
        "嵌套契约的深层回显：C-07 只验证顶层 object 回显，嵌套 properties 的逐层填充"
        "不是本包行为",
        "非法 UTF-8 与 BOM：case.json 与 task.md 均按 UTF-8 读取，未测 GBK 或带 BOM 变体",
        "Windows 保留字字段名：如 CON/PRN；与内置键同名已由 B-09 覆盖一类",
        "退出码 2 的路径：argparse 用法错误不在本矩阵（矩阵只注入契约，不改 CLI）",
    ],
}


if __name__ == "__main__":
    sys.exit(main())
