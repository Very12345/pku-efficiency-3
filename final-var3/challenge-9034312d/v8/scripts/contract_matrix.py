#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""contract_matrix.py — 契约「容器形态 × 边界值」实测矩阵（R3 v8 轴；可直接运行）。

`references/OUTPUT_CONTRACT.md` 声明了 result.json 的 18 个顶层字段、它们的**容器形态**
（字符串 / 列表 / 对象 / 枚举）与一条硬话：「字段缺失或类型不符 ⇒ `scripts/check.py` 报 issue，
status 不能为 success」。声明是一回事，**门会不会真的拦住**是另一回事。
本脚本把两者对齐成一张**实测**矩阵，并给出可复核的差异清单：

  第一段 · 契约面自校验（两种交叉核对）
    * 从 `references/OUTPUT_CONTRACT.md` 的字段块解析字段名 ⇄ 本脚本内置清单；
    * 从 `scripts/check.py` 源码解析 `required_fields` ⇄ 契约的 18 字段
      （差值即「契约声明了、机器门没查」的字段）。

  第二段 · 输入侧注入（in-*）：把 case.json 按非法容器 / 缺字段 / 空容器 / 超长弄坏，
    **跑 scripts/main.py 全流程**，记录：退出码、status、是否写出 result.json、
    契约回显（18 字段缺哪几个、形态是否相符）、uncertainty 条数、explicit 信号强度、
    是否**静默**（违约但 exit 0 且 status=success）。

  第三段 · 输出侧注入（out-*）：拿一次真实运行的 result.json，把**每个契约字段**按边界值
    （缺字段 / null / 空值 / 非法类型 / 超长）逐个替换，跑 `scripts/check.py`（G1–G10），
    记录：退出码、`ok`、被拦下的门、issues 条数、信号强度
    （gate / issues-only / crash / none），以及**是否静默通过**。

  第四段 · 六形态 × 代表字段（form-*）+ 嵌套结构（nest-*）：字符串/列表/对象/数值/布尔/嵌套
    逐个塞进六个代表字段；再打契约四段的内部结构（editable_sources.path、exports、
    data_mapping、element_traceability、evidence.items、verify.ok、uncertainty…）。

判据（判据本身也被测过，见 references/CONTRACT-MATRIX.md）：
  * 每行先声明**期望信号强度**：`gate`（应被某个 G 门拦下）/ `issue`（契约只承诺"报 issue"）/
    `none`（落在 G1–G10 检查面之外 —— 属**未覆盖**，不是缺陷）；
  * `defect` 只统计「期望 gate 或 issue，但实测信号更弱」的行 —— 这类才是**门面内**的真实缺口；
  * `silent_pass` 是**原始观测**（违约但零退出/ok=true），包含 `defect` 与"未覆盖"两类，逐条列出。

产出：机器可读的 `contract_matrix_report.json`（`rows[]` / `silent_pass[]` / `defects[]` /
`surface_gaps[]` / `counts` / `uncovered[]` / `verdict`）。逐行表格与清单落在
`references/CONTRACT-MATRIX.md`。

退出码：0 = 无门面内缺陷；1 = 有门面内缺陷（**实测本包为 1**，逐条见 `defects[]`）；
        2 = 用法/环境错误。`--expect-defects N` 可把"无新增缺陷"做成回归断言。

用法（`$SKILL_DIR` = 含 SKILL.md 的技能根；任何 cwd 都可运行）：
    python "$SKILL_DIR/scripts/contract_matrix.py"
    python "$SKILL_DIR/scripts/contract_matrix.py" --json /tmp/contract_matrix_report.json
    python "$SKILL_DIR/scripts/contract_matrix.py" --section form --only form-03
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

sys.dont_write_bytecode = True
from typing import Any, Callable, Dict, List, Optional, Tuple  # noqa: E402

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(SCRIPTS_DIR)

ALLOWED_EXT = {".md", ".py", ".json", ".txt", ".csv", ".yaml", ".yml"}
SKIP_DIRS = {"__pycache__", ".git", ".venv", "venv", "node_modules", ".mypy_cache"}

# 契约清单（与 references/OUTPUT_CONTRACT.md 的字段块逐字对应；第一段自校验）
CONTRACT_FIELDS = [
    "case_id", "title", "status", "workorder", "figure_type", "extraction",
    "entities", "relations", "output_contract", "evidence", "verify",
    "canvas", "fonts", "sources", "uncertainty", "change_record", "execution", "checksum",
]
FIELD_FORMS: Dict[str, str] = {
    "case_id": "str", "title": "str", "status": "enum", "workorder": "str",
    "figure_type": "enum", "extraction": "enum", "entities": "list",
    "relations": "list", "output_contract": "object", "evidence": "object",
    "verify": "object", "canvas": "object", "fonts": "list", "sources": "list",
    "uncertainty": "list", "change_record": "list", "execution": "object",
    "checksum": "str",
}
FORMS = ["str", "list", "object", "number", "bool", "nested"]
FORM_VALUES: Dict[str, Any] = {
    "str": "x", "list": [], "object": {}, "number": 0, "bool": False,
    "nested": {"a": [1, {"b": None}]},
}
FormValues = FORM_VALUES  # 供 lambda 内引用

# 每个声明形态的「非法类型」取自哪种形态（容器形态互换）
CROSS_FORMS: Dict[str, List[str]] = {
    "str": ["number", "bool", "list", "object"],
    "enum": ["number", "bool", "list", "object"],
    "list": ["str", "number", "object", "bool"],
    "object": ["str", "number", "list", "bool"],
}
LONG_STR = "字" * 12000  # 超长（单值 >10KB）
EMPTY_BY_FORM = {"str": "", "enum": "", "list": [], "object": {}, "number": 0,
                 "bool": False, "nested": {}}

# 期望信号强度：check.py 的 G1 只看 case_id 真值性与 status 枚举值，故这两项按 gate 期望
GATE_EXPECT = {
    ("case_id", "missing"), ("case_id", "null"), ("case_id", "empty"), ("case_id", "wrong-type"),
    ("status", "missing"), ("status", "null"), ("status", "empty"), ("status", "wrong-type"),
    ("entities", "missing"), ("entities", "null"), ("entities", "empty"), ("entities", "wrong-type"),
    ("output_contract", "missing"), ("output_contract", "null"),
}
# 「仅报 issue」的期望（缺字段时 check.py 会往 issues 里写一条，但不影响 ok/退出码）
ISSUE_EXPECT = {("title", "missing"), ("figure_type", "missing"),
                ("case_id", "missing"), ("status", "missing"),
                ("output_contract", "missing"), ("sources", "missing"),
                ("uncertainty", "missing"), ("change_record", "missing"), ("checksum", "missing")}


# ---------------------------------------------------------------- 工具
def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def sandbox_copy(skill_root: str, dest: str) -> Dict[str, Any]:
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    os.makedirs(dest, exist_ok=True)
    rows: List[Tuple[str, str]] = []
    for root, dirs, files in os.walk(skill_root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for name in sorted(files):
            if os.path.splitext(name)[1].lower() not in ALLOWED_EXT:
                continue
            src = os.path.join(root, name)
            rel = os.path.relpath(src, skill_root).replace("\\", "/")
            dst = os.path.join(dest, rel.replace("/", os.sep))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)
            rows.append((rel, sha256_file(src)))
    digest = hashlib.sha256()
    for rel, sha in sorted(rows):
        digest.update(f"{rel}\t{sha}\n".encode("utf-8"))
    return {"files": len(rows), "tree_sha256": digest.hexdigest()}


def parse_contract_fields(md_path: str) -> List[str]:
    if not os.path.isfile(md_path):
        return []
    txt = open(md_path, encoding="utf-8").read()
    m = re.search(r"##\s*顶层字段清单[^\n]*\n+```[a-z]*\n(.*?)```", txt, re.S)
    if not m:
        return []
    return [w for w in re.split(r"\s+", m.group(1).strip()) if w]


def parse_check_required(py_path: str) -> List[str]:
    """从 scripts/check.py 源码里解析 required_fields 列表（机器门的实际检查面）。"""
    if not os.path.isfile(py_path):
        return []
    txt = open(py_path, encoding="utf-8").read()
    m = re.search(r"required_fields\s*=\s*\[(.*?)\]", txt, re.S)
    if not m:
        return []
    return re.findall(r'"([^"]+)"', m.group(1))


def run_cli(argv: List[str], cwd: str, timeout: int) -> Dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    t0 = time.time()
    try:
        proc = subprocess.Popen(argv, cwd=cwd, env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True,
                                encoding="utf-8", errors="replace")
        out, err = proc.communicate(timeout=timeout)
        rc = proc.returncode
    except subprocess.TimeoutExpired:  # noqa: PERF203
        proc.kill()
        out, err = proc.communicate()
        rc = 124
    return {"exit": rc, "stdout": out or "", "stderr": err or "",
            "elapsed_s": round(time.time() - t0, 3)}


def read_json(path: str) -> Optional[Any]:
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def field_inventory(doc: Any) -> Dict[str, Any]:
    if not isinstance(doc, dict):
        return {"present": [], "missing": CONTRACT_FIELDS, "type_ok": False,
                "wrong_form": [f"{f}:<root-not-object>" for f in CONTRACT_FIELDS]}
    present = [f for f in CONTRACT_FIELDS if f in doc]
    missing = [f for f in CONTRACT_FIELDS if f not in doc]
    wrong: List[str] = []
    for f in present:
        want, v = FIELD_FORMS[f], doc[f]
        got = ("list" if isinstance(v, list) else "object" if isinstance(v, dict)
               else "str" if isinstance(v, str) else "bool" if isinstance(v, bool)
               else "number" if isinstance(v, (int, float)) else type(v).__name__)
        if (want, got) not in (("list", "list"), ("object", "object"),
                               ("str", "str"), ("enum", "str")):
            wrong.append(f"{f}:{got}≠{want}")
    return {"present": present, "missing": missing, "wrong_form": wrong,
            "type_ok": not wrong and not missing}


# ---------------------------------------------------------------- 第二段：输入侧
def input_cases() -> List[Dict[str, Any]]:
    def rep(doc, key, value):
        doc = json.loads(json.dumps(doc, ensure_ascii=False))
        doc[key] = value
        return doc

    cases: List[Dict[str, Any]] = []

    def add(cid, name, intent, violates, mutate, expect="none"):
        cases.append({"id": cid, "name": name, "intent": intent, "violates": violates,
                      "mutate": mutate, "expected_signal": expect})

    add("in-01", "entities=字符串", "容器形态违约：结构段声明为列表却给字符串",
        True, lambda d: rep(d, "entities", "E1,E2"), "none")
    add("in-02", "entities=空数组", "边界：空容器（契约未定空是否合法）",
        False, lambda d: rep(d, "entities", []), "none")
    add("in-03", "entities=对象", "容器形态违约：列表位给对象", True, lambda d: rep(d, "entities", {}))
    add("in-04", "entities=0", "边界：数值 0 冒充容器", True, lambda d: rep(d, "entities", 0))
    add("in-05", "entities=null", "边界：null 冒充列表", True, lambda d: rep(d, "entities", None))
    add("in-06", "case_id=数值", "声明 string 却给数值", True, lambda d: rep(d, "case_id", 12345))
    add("in-07", "case_id=空串", "边界：空串", True, lambda d: rep(d, "case_id", ""))
    add("in-08", "case_id 缺字段", "缺字段：标识缺失", True,
        lambda d: {k: v for k, v in d.items() if k != "case_id"})
    add("in-09", "canvas=数值", "容器形态违约：对象位给数值", True, lambda d: rep(d, "canvas", 0))
    add("in-10", "canvas.width_mm=负值", "边界：负数画布", True,
        lambda d: rep(d, "canvas", {"width_mm": -100, "height_mm": 0}))
    add("in-11", "canvas.width_mm=字符串", "非法类型：数值位给字符串", True,
        lambda d: rep(d, "canvas", {"width_mm": "wide", "height_mm": 100}))
    add("in-12", "figure_type=非法枚举", "枚举越界", True, lambda d: rep(d, "figure_type", "orgChart"))
    add("in-13", "relations=字符串", "容器形态违约：列表位给字符串", True, lambda d: rep(d, "relations", "R1"))
    add("in-14", "relations=空数组", "边界：有实体无关系", False, lambda d: rep(d, "relations", []))
    add("in-15", "title=超长 12k 字", "边界：超长字符串（单值 >10KB；契约未声明上限）", False,
        lambda d: rep(d, "title", LONG_STR))
    add("in-16", "entities[0].id 空串", "边界：实体 id 空串", True,
        lambda d: rep(d, "entities", [dict((d.get("entities") or [{}])[0] or {}, id="")]))
    add("in-17", "relations[0] 缺 from", "缺字段：断头箭头", True,
        lambda d: rep(d, "relations", [{"id": "RX", "to": "E1", "kind": "flow"}]))
    add("in-18", "顶层 JSON 数组", "根容器形态违约：数组而非对象", True, lambda d: [])
    add("in-19", "空对象 {}", "缺字段：契约字段全缺", True, lambda d: {})
    add("in-20", "非 JSON 文本", "不可解析（对照组）", True, lambda d: None)
    add("in-21", "entities=120 条", "边界：超长数组（规模上限探针；契约未声明上限）", False,
        lambda d: rep(d, "entities", [{"id": f"E{i}", "name": f"部件{i}", "kind": "device"}
                                      for i in range(1, 121)]))
    add("in-22", "entities 元素=字符串", "嵌套形态违约：列表元素给字符串", True,
        lambda d: rep(d, "entities", ["E1", "E2"]))
    return cases


def run_input_matrix(args: argparse.Namespace, skill_dir: str, workdir: str,
                     base_case: Dict[str, Any], case_arg_dir: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    src_task = os.path.join(case_arg_dir, "task.md")
    for spec in input_cases():
        cid = spec["id"]
        if not _selected(cid, args.only):
            continue
        case_dir = os.path.join(workdir, "injected", cid)
        os.makedirs(case_dir, exist_ok=True)
        if os.path.isfile(src_task):
            shutil.copyfile(src_task, os.path.join(case_dir, "task.md"))
        out_root = os.path.join(workdir, "in_out", cid)
        try:
            mutated = spec["mutate"](base_case)
            with open(os.path.join(case_dir, "case.json"), "w", encoding="utf-8",
                      newline="\n") as fh:
                if mutated is None:
                    fh.write("{ this is not json ")
                else:
                    json.dump(mutated, fh, ensure_ascii=False, indent=2)
        except Exception as exc:  # noqa: BLE001
            rows.append({"id": cid, "section": "input", "name": spec["name"],
                         "setup_error": str(exc)})
            continue
        res = run_cli([args.python, os.path.join(skill_dir, "scripts", "main.py"),
                       "--case", case_dir, "--out", out_root],
                      cwd=skill_dir, timeout=args.timeout)
        doc, result_rel = None, None
        if os.path.isdir(out_root):
            for d in sorted(os.listdir(out_root)):
                cand = os.path.join(out_root, d, "result.json")
                if os.path.isdir(os.path.join(out_root, d)) and os.path.isfile(cand):
                    doc, result_rel = read_json(cand), os.path.relpath(cand, out_root).replace("\\", "/")
                    break
            fpath = os.path.join(out_root, "failed", "result.json")
            if doc is None and os.path.isfile(fpath):
                doc, result_rel = read_json(fpath), "failed/result.json"
        inv = field_inventory(doc)
        status = doc.get("status") if isinstance(doc, dict) else None
        extraction = doc.get("extraction") if isinstance(doc, dict) else None
        un = doc.get("uncertainty") if isinstance(doc, dict) else None
        un_n = len(un) if isinstance(un, list) else 0
        if status in ("failed", None) or res["exit"] != 0:
            signal = "failed"
        elif status == "partial":
            signal = "partial"
        elif un_n or extraction == "text-heuristic":
            signal = "success+recorded"
        else:
            signal = "success-zero-signal"
        # 输入侧的「缺陷」判据不是"注入得怪"，而是**产物真的违约**：
        # 契约 status 表写明「存在未解决的 uncertainty（孤儿实体/文本解构/缺字体/预览失败）⇒ partial」，
        # 且 18 个顶层字段的类型形态必须与声明一致。
        contract_violation = bool(
            (not inv["type_ok"])
            or (status not in ("success", "partial", "failed"))
            or (status == "success" and (un_n > 0 or extraction == "text-heuristic")))
        defect = bool(spec["violates"] and contract_violation)
        rows.append({
            "id": cid, "section": "input", "name": spec["name"], "intent": spec["intent"],
            "violates_contract": spec["violates"], "expected_signal": spec["expected_signal"],
            "exit": res["exit"], "status": status, "extraction": extraction,
            "result_json": result_rel,
            "contract_fields_present": len(inv["present"]),
            "contract_fields_missing": inv["missing"],
            "contract_form_violations": inv["wrong_form"],
            "uncertainty_items": un_n, "signal": signal,
            "contract_violation_in_output": contract_violation,
            "silent_pass": bool(spec["violates"] and res["exit"] == 0 and status == "success"),
            "zero_signal": bool(spec["violates"] and res["exit"] == 0 and status == "success"
                                and un_n == 0 and extraction != "text-heuristic"),
            "defect": defect, "elapsed_s": res["elapsed_s"],
            "stderr_tail": res["stderr"][-200:] if res["exit"] != 0 else "",
        })
    return rows


def _selected(cid: str, only: Optional[List[str]]) -> bool:
    """--only 的匹配规则：精确 id / 前缀（`form-03` 也命中 `form-03-list`）/ 通配（`form-03-*`）。"""
    if not only:
        return True
    return any(cid == o or cid.startswith(o + "-") or cid.startswith(o.rstrip("*"))
               for o in only)


# ---------------------------------------------------------------- 第三/四段：输出侧
def output_cases() -> List[Dict[str, Any]]:
    cases: List[Dict[str, Any]] = []

    def add(cid, name, intent, violates, mutate, field, boundary, expect):
        cases.append({"id": cid, "name": name, "intent": intent, "violates": violates,
                      "mutate": mutate, "field": field, "boundary": boundary,
                      "expected_signal": expect, "expected_gate": None})

    for f in CONTRACT_FIELDS:
        want = FIELD_FORMS[f]
        if want in ("str", "enum"):
            huge_val: Any = LONG_STR
        elif want == "list":
            huge_val = [LONG_STR[:200]] * 60
        else:
            huge_val = {LONG_STR[:40]: LONG_STR}
        add(f"out-{f}-missing", f"{f} 缺字段", "契约必填字段被删", True,
            (lambda ff: (lambda d: {k: v for k, v in d.items() if k != ff}))(f),
            f, "missing", "gate" if (f, "missing") in GATE_EXPECT
            else ("issue" if (f, "missing") in ISSUE_EXPECT else "none"))
        add(f"out-{f}-null", f"{f}=null", "边界：null 顶替声明的容器", True,
            (lambda ff: (lambda d: {**d, ff: None}))(f), f, "null",
            "gate" if (f, "null") in GATE_EXPECT else "none")
        add(f"out-{f}-empty", f"{f}=空值({want})", "边界：空容器/空串/0",
            f in ("entities", "relations", "fonts", "sources", "change_record"),
            (lambda ff, w: (lambda d: {**d, ff: EMPTY_BY_FORM[w]}))(f, want), f, "empty",
            "gate" if (f, "empty") in GATE_EXPECT else "none")
        wrong = CROSS_FORMS[want][0]
        add(f"out-{f}-wrongtype", f"{f}={wrong}(≠{want})", "非法类型：容器形态不符", True,
            (lambda ff, v: (lambda d: {**d, ff: FormValues[v]}))(f, wrong), f, "wrong-type",
            "gate" if (f, "wrong-type") in GATE_EXPECT else "none")
        add(f"out-{f}-huge", f"{f}=超长({want})", "边界：超长内容（12k 字/12k 元素）", True,
            (lambda ff, v: (lambda d: {**d, ff: v}))(f, huge_val), f, "overlong", "none")

    reps = ["output_contract", "entities", "evidence", "verify", "checksum", "status"]
    for i, f in enumerate(reps):
        for form in FORMS:
            declared = FIELD_FORMS[f]
            violates = (form != declared) or (f == "status" and form == "str")
            exp = ("gate" if (f in ("entities", "status") and form in ("str", "number", "bool"))
                   else "none")
            add(f"form-{i:02d}-{form}", f"{f}={form}",
                f"六形态矩阵：{form} 塞进声明为 {declared} 的字段", violates,
                (lambda ff, v: (lambda d: {**d, ff: FormValues[v]}))(f, form),
                f, f"form:{form}", exp)

    def set_nested(path: List[Any], value: Any) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
        def _m(doc: Dict[str, Any]) -> Dict[str, Any]:
            doc = json.loads(json.dumps(doc, ensure_ascii=False))
            cur: Any = doc
            for seg in path[:-1]:
                cur = cur[seg]
            cur[path[-1]] = value
            return doc
        return _m

    nested = [
        ("nest-01", "output_contract.editable_sources[0].path=''", True, "G3",
         set_nested(["output_contract", "editable_sources", 0, "path"], "")),
        ("nest-02", "output_contract.exports=[]", True, "G4",
         set_nested(["output_contract", "exports"], [])),
        ("nest-03", "output_contract.data_mapping=[]（实体非空）", True, "G5",
         set_nested(["output_contract", "data_mapping"], [])),
        ("nest-04", "output_contract.element_traceability=[]", True, "G6",
         set_nested(["output_contract", "element_traceability"], [])),
        ("nest-05", "output_contract=字符串", True, "G2",
         (lambda d: {**d, "output_contract": "see figure"})),
        ("nest-06", "evidence.items=字符串", True, "none",
         set_nested(["evidence", "items"], "EV1")),
        ("nest-07", "evidence 缺 source_files", True, "none",
         (lambda d: {**d, "evidence": {k: v for k, v in (d.get("evidence") or {}).items()
                                       if k != "source_files"}})),
        ("nest-08", "verify.ok='true'（字符串真值）", True, "G9",
         set_nested(["verify", "ok"], "true")),
        ("nest-09", "verify.ok=1（数值真值）", True, "G9", set_nested(["verify", "ok"], 1)),
        ("nest-10", "verify={}（ok 缺字段）", True, "G9", set_nested(["verify"], {})),
        ("nest-11", "entities=[] 且 data_mapping=[]（空对空 + status=success）", True, "G5/G10",
         (lambda d: {**d, "entities": [], "relations": [],
                     "output_contract": {**(d.get("output_contract") or {}),
                                         "data_mapping": [], "element_traceability": []}})),
        ("nest-12", "uncertainty={}（应为列表）", True, "none", set_nested(["uncertainty"], {})),
        ("nest-13", "change_record=字符串", True, "none", set_nested(["change_record"], "auto")),
        ("nest-14", "sources=[null]", True, "none", set_nested(["sources"], [None])),
        ("nest-15", "checksum=''（空串）", True, "none", set_nested(["checksum"], "")),
        ("nest-16", "额外未知字段（应被容忍）", False, "none",
         (lambda d: {**d, "_unknown_extra": {"x": 1}})),
    ]
    for cid, name, violates, gate, mut in nested:
        add(cid, name, "嵌套结构内部违约", violates, mut, "(nested)", "nested",
            "none" if gate == "none" else "gate")
        cases[-1]["expected_gate"] = gate
    return cases


def run_output_matrix(args: argparse.Namespace, skill_dir: str, workdir: str,
                      base_out_root: str, base_case_id: str) -> List[Dict[str, Any]]:
    base_case_dir = os.path.join(base_out_root, base_case_id)
    base_result = os.path.join(base_case_dir, "result.json")
    if not os.path.isfile(base_result):
        return [{"id": "out-BASE", "section": "output",
                 "setup_error": f"基线 result.json 不存在: {base_result}"}]
    base_doc = read_json(base_result)
    probe_dir = os.path.join(workdir, "out_probe", base_case_id)
    rows: List[Dict[str, Any]] = []
    for spec in output_cases():
        cid = spec["id"]
        if not _selected(cid, args.only):
            continue
        if os.path.isdir(probe_dir):
            shutil.rmtree(probe_dir)
        shutil.copytree(base_case_dir, probe_dir)
        try:
            with open(os.path.join(probe_dir, "result.json"), "w", encoding="utf-8",
                      newline="\n") as fh:
                json.dump(spec["mutate"](base_doc), fh, ensure_ascii=False, indent=2)
        except Exception as exc:  # noqa: BLE001
            rows.append({"id": cid, "section": "output", "name": spec["name"],
                         "setup_error": str(exc)})
            continue
        res = run_cli([args.python, os.path.join(skill_dir, "scripts", "check.py"),
                       os.path.join(probe_dir, "result.json")],
                      cwd=skill_dir, timeout=args.timeout)
        rep = None
        try:
            rep = json.loads(res["stdout"])
        except Exception:  # noqa: BLE001
            rep = None
        if not isinstance(rep, dict):
            signal, ok, gates_failed, issues = "crash", None, None, None
            first_issue = (res["stderr"].strip().splitlines() or [""])[-1][:160]
        else:
            ok = bool(rep.get("ok"))
            gates_failed = sorted(k for k, v in (rep.get("gates") or {}).items() if not v)
            iss = rep.get("issues") or []
            issues = len(iss)
            first_issue = (iss[0][:160] if iss else "")
            signal = ("gate" if not ok else ("issues-only" if issues else "none"))
        defect = ((spec["expected_signal"] == "gate" and signal not in ("gate", "crash"))
                  or (spec["expected_signal"] == "issue" and signal == "none"))
        row = {
            "id": cid, "section": "form" if cid.startswith("form-") else "output",
            "name": spec["name"], "intent": spec["intent"], "field": spec["field"],
            "boundary": spec["boundary"], "violates_contract": spec["violates"],
            "expected_signal": spec["expected_signal"],
            "expected_gate": spec.get("expected_gate"),
            "check_exit": res["exit"], "check_ok": ok, "signal": signal,
            "gates_failed": gates_failed, "issues": issues, "first_issue": first_issue,
            "silent_pass": bool(spec["violates"] and ok is True),
            "defect": bool(spec["violates"] and defect),
            "elapsed_s": res["elapsed_s"],
        }
        rows.append(row)
    return rows


# ---------------------------------------------------------------- 主流程
def probe(args: argparse.Namespace) -> Dict[str, Any]:
    workdir = os.path.abspath(args.out or tempfile.mkdtemp(prefix="contract-matrix-"))
    os.makedirs(workdir, exist_ok=True)
    if args.no_sandbox:
        skill_dir, sandbox = SKILL_ROOT, {"files": -1, "tree_sha256": "not-copied"}
    else:
        skill_dir = os.path.join(workdir, "skill")
        sandbox = sandbox_copy(SKILL_ROOT, skill_dir)

    doc_fields = parse_contract_fields(os.path.join(skill_dir, "references", "OUTPUT_CONTRACT.md"))
    check_required = parse_check_required(os.path.join(skill_dir, "scripts", "check.py"))
    not_checked = [f for f in CONTRACT_FIELDS if f not in check_required]

    case_arg_dir = os.path.abspath(args.case or os.path.join(skill_dir, "examples"))
    if os.path.isfile(case_arg_dir):
        case_arg_dir = os.path.dirname(case_arg_dir)
    if not os.path.isfile(os.path.join(case_arg_dir, "case.json")):
        raise SystemExit(f"FATAL: 示例 case.json 不存在: {case_arg_dir}")
    base_case = read_json(os.path.join(case_arg_dir, "case.json")) or {}

    base_out_root = os.path.join(workdir, "base_out")
    base_run = run_cli([args.python, os.path.join(skill_dir, "scripts", "main.py"),
                        "--case", case_arg_dir, "--out", base_out_root],
                       cwd=skill_dir, timeout=args.timeout)
    subdirs = [d for d in sorted(os.listdir(base_out_root))
               if os.path.isdir(os.path.join(base_out_root, d))] if os.path.isdir(base_out_root) else []
    base_case_id = subdirs[0] if subdirs else "?"

    rows: List[Dict[str, Any]] = []
    if "input" in args.section:
        rows += run_input_matrix(args, skill_dir, workdir, base_case, case_arg_dir)
    if "output" in args.section or "form" in args.section:
        out_rows = run_output_matrix(args, skill_dir, workdir, base_out_root, base_case_id)
        for r in out_rows:
            r.setdefault("section", "output")
        rows += [r for r in out_rows
                 if ("output" in args.section and r.get("section") == "output")
                 or ("form" in args.section and r.get("section") == "form")]

    silent = [{"id": r["id"], "section": r.get("section"), "name": r.get("name"),
               "signal": r.get("signal"), "defect": bool(r.get("defect")),
               "expected_signal": r.get("expected_signal")} for r in rows if r.get("silent_pass")]
    defects = [s for s in silent if s["defect"]]
    surface_only = [s for s in silent if not s["defect"]]
    counts = {
        "rows": len(rows),
        "input_rows": sum(1 for r in rows if r.get("section") == "input"),
        "output_rows": sum(1 for r in rows if r.get("section") == "output"),
        "form_rows": sum(1 for r in rows if r.get("section") == "form"),
        "violating_rows": sum(1 for r in rows if r.get("violates_contract")),
        "silent_pass": len(silent),
        "defects": len(defects),
        "silent_uncovered": len(surface_only),
        "setup_errors": sum(1 for r in rows if r.get("setup_error")),
    }
    verdict = "pass" if (doc_fields == CONTRACT_FIELDS and not defects
                         and counts["setup_errors"] == 0) else "attention"
    if args.expect_defects is not None:
        verdict = "pass" if counts["defects"] == args.expect_defects else "attention"

    return {
        "probe": "contract_matrix",
        "schema": "contract-matrix-report/1",
        "generated_by": "scripts/contract_matrix.py",
        "skill_root": SKILL_ROOT,
        "sandbox": {"dir": skill_dir, **sandbox},
        "contract_doc": "references/OUTPUT_CONTRACT.md",
        "contract_doc_fields": doc_fields,
        "script_contract_fields": CONTRACT_FIELDS,
        "contract_doc_matches": doc_fields == CONTRACT_FIELDS,
        "check_required_fields": check_required,
        "contract_fields_not_checked": not_checked,
        "field_forms": FIELD_FORMS,
        "base_run": {"exit": base_run["exit"], "case_id": base_case_id,
                     "elapsed_s": base_run["elapsed_s"]},
        "rows": rows,
        "silent_pass": silent,
        "defects": defects,
        "silent_uncovered": surface_only,
        "counts": counts,
        "expect_defects": args.expect_defects,
        "uncovered": [
            "画布真实溢出（需极大实体规模才触发 D8；本矩阵规模上限 120 实体）",
            "并发重入与多进程写同一 --out（本探针串行执行）",
            "SVG 内部结构违约（手改 figure.svg 的 layer/id）—— 归 scripts/svg_verify.py 的 CP2/CP3，不在 G1–G10",
            "PDF/PNG 二进制层面的契约（本矩阵只看 result.json 与 check.py 的 G1–G10）",
            "if/else 分支的覆盖率（本矩阵测的是契约面，不是行覆盖率）",
        ],
        "verdict": verdict,
        "notes": [
            "第二段（in-*）跑 scripts/main.py 全流程；第三/四段（out-*/form-*/nest-*）跑 "
            "scripts/check.py 的 G1–G10。两者只写沙箱副本与工作目录，包本体不动。",
            "silent_pass 是原始观测（违约但 exit 0 / ok=true / status=success）；"
            "defect 只统计**期望 gate 或 issue 但信号更弱**的行，即门面内的真实缺口；"
            "silent_uncovered 是落在 G1–G10 检查面之外的静默（属未覆盖声明，不是缺陷）。",
            "check.py 的 ok = all(gates)，**issues 不计入 ok** —— 所以「只报 issue」的违约"
            "退出码仍是 0，这是本矩阵最重要的结构性发现之一（见 counts 与 defects）。",
        ],
    }


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(
        description="契约「容器形态 × 边界值」实测矩阵（v8）：注入 → 跑主流程/契约门 → 记录实测")
    ap.add_argument("--case", default=None, help="case.json 或其所在目录（默认技能根 examples）")
    ap.add_argument("--out", default=None, help="探针工作目录（默认系统临时目录）")
    ap.add_argument("--json", default=None,
                    help="报告路径（默认 <out>/contract_matrix_report.json）")
    ap.add_argument("--section", action="append", default=None,
                    choices=["input", "output", "form"], help="只跑某一段（可多次；默认全跑）")
    ap.add_argument("--only", action="append", default=None,
                    help="只跑指定用例 id（可多次；支持前缀 *，如 in-01 或 form-*）")
    ap.add_argument("--python", default=sys.executable, help="用于跑主流程的解释器")
    ap.add_argument("--timeout", type=int, default=300, help="单条用例超时秒数（默认 300）")
    ap.add_argument("--expect-defects", type=int, default=None,
                    help="断言门面内缺陷数（用于回归：数量不符则 verdict=attention）")
    ap.add_argument("--no-sandbox", action="store_true", help="不复制沙箱（不推荐）")
    args = ap.parse_args(argv)
    if not args.section:
        args.section = ["input", "output", "form"]

    try:
        report = probe(args)
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        print(f"FATAL: 探针异常: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 2

    json_path = args.json or os.path.join(os.path.abspath(args.out or tempfile.gettempdir()),
                                          "contract_matrix_report.json")
    os.makedirs(os.path.dirname(os.path.abspath(json_path)), exist_ok=True)
    with open(json_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)

    print(json.dumps({
        "verdict": report["verdict"],
        "contract_doc_matches": report["contract_doc_matches"],
        "contract_fields": len(report["script_contract_fields"]),
        "check_required_fields": len(report["check_required_fields"]),
        "contract_fields_not_checked": report["contract_fields_not_checked"],
        "counts": report["counts"],
        "defects": [d["id"] for d in report["defects"]],
        "report": json_path,
    }, ensure_ascii=False, indent=2))
    return 0 if report["verdict"] == "pass" else 1


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass
    sys.exit(main(sys.argv[1:]))
