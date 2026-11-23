#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""contract_matrix.py — 契约四形态 × 边界值矩阵（v8 轴 · 只依赖标准库）。

它把 `references/OUTPUT_CONTRACT.md` §3 的「四形态回显」与 §7 的 G1–G8 门
从"文档承诺"变成**逐行实测**：把每种容器形态（字符串 / 列表 / 对象 / 数值 / 布尔 /
带 `type` 的类型化声明 / 嵌套）与每个边界值（空串、空数组、0、false、超长值、
非法类型名、缺字段、显式 null、键名与信封或内部键重名、契约容器本身非法、
case.json 缺失或不是对象）**逐个注入**一份真实的 case.json，跑**真实主流程**，
然后同时看三层判定：

  第 1 层  主流程 `scripts/main.py`：退出码 / status / `gates.g2_contract_echo`
  第 2 层  独立检查器 `scripts/check_contract.py`：退出码 / 失败检查项
  第 3 层  产物本身 `result.json`：声明字段是否出现、回显值的 JSON 类型、
           是否仍是 null、是否有任何留痕（uncertainty / change_records）

据此把每行判成四类之一：

  ok                声明键全出现、回显类型与声明形态一致、且有留痕（或本来就无需留痕）
  fill_documented   按文档允许的空值填充（如 "hello" → ""），但**没有任何留痕**
  silent_gap        **形态违规**（键丢失 / 类型不符 / 契约整体被忽略）而三层**全部 pass**
  flagged           同样的形态违规**被某一层抓到**（g2 fail 或 check_contract 非零或 status 降级）

用法
----
  export SKILL_DIR=/skills/weekly-skill
  python3 "$SKILL_DIR/scripts/contract_matrix.py" \
      --work /tmp/cm --report "$SKILL_DIR/contract_matrix_report.json"
  python3 "$SKILL_DIR/scripts/contract_matrix.py" --only struct-oc-list   # 只跑一行

退出码
------
  0 = 矩阵完整跑完（行内出现 silent_gap 不影响本脚本退出码，它是被测对象的行为）
  2 = 探针自身无法完成（技能包缺件、主流程在**控制行**上就不通）
  4 = 参数错误
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SKILL_ROOT = os.path.dirname(HERE)
TOOL_VERSION = "1.0"

# 「未覆盖声明」：矩阵明确不覆盖的情形（写进报告，避免把没测的当测过）
NOT_COVERED = [
    "非 UTF-8 编码的 case.json（load_json 固定 utf-8，非 UTF-8 等价于「非法 JSON」行，未单列）",
    "JSON 重复键（解析器保留最后一个；本矩阵不构造重复键）",
    "平台固定正式案例的真实 output_contract（不可见，不猜测）",
    "CLI 参数轴的边界（--materials-dir 传 list 等）：属 CLI 轴，本矩阵只用 --case/--model-file/--out/--formats",
    "result.json 落盘后的下游消费者（评分器）如何解释这些字段：本矩阵只测本包的三层检查",
    "并发写同一输出目录、磁盘写满、只读目录：属故障注入轴（v4 FAULT-MATRIX），不在契约轴内",
]

DECLARED_TYPE_MAP = {
    "str": "str", "string": "str",
    "list": "array", "array": "array",
    "dict": "object", "object": "object",
    "bool": "bool", "boolean": "bool",
    "number": "number", "int": "number", "integer": "number", "float": "number",
}


# --------------------------------------------------------------------------
def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def dump_json(obj, path):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def json_type(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "bool"
    if isinstance(v, (int, float)):
        return "number"
    if isinstance(v, str):
        return "str"
    if isinstance(v, list):
        return "array"
    if isinstance(v, dict):
        return "object"
    return type(v).__name__


def expected_types(decl):
    """声明值 → 允许的回显 JSON 类型集合（依据 OUTPUT_CONTRACT.md §3）。"""
    if isinstance(decl, bool):
        return {"bool"}
    if isinstance(decl, (int, float)):
        return {"number"}
    if isinstance(decl, str):
        return {"str"}
    if isinstance(decl, list):
        return {"array"}
    if isinstance(decl, dict):
        t = decl.get("type")
        if isinstance(t, str):
            mapped = DECLARED_TYPE_MAP.get(t)
            return {mapped} if mapped else {"<unknown-type-name:%s>" % t}
        return {"object"}
    if decl is None:
        return {"<declared-null>"}
    return {"<unknown-declared>"}


def short(v, limit=70):
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    return s if len(s) <= limit else s[:limit] + "…(%d chars)" % len(s)


def portable(text, roots):
    if not isinstance(text, str):
        return text
    out = text
    for root, tag in roots:
        if not root:
            continue
        for variant in (root, root.rstrip("/\\"), root.replace("\\", "/"),
                        root.replace("/", "\\"), root.replace("\\", "\\\\")):
            if variant:
                out = out.replace(variant, tag)
    out = re.sub(
        r"(?<!>)(?:[A-Za-z]:[\\/]|\\\\[?]\\|/(?:Users|home|tmp|skills)/)[^\s\"'<>|,;)\]]*",
        "<ABS>", out)   # 整段绝对路径掩码；(?<!>) 保证幂等
    return out.replace("\\", "/")


def portable_obj(obj, roots):
    if isinstance(obj, dict):
        return {k: portable_obj(v, roots) for k, v in obj.items()}
    if isinstance(obj, list):
        return [portable_obj(v, roots) for v in obj]
    if isinstance(obj, str):
        return portable(obj, roots)
    return obj


def copy_tree(src, dst, skip_dir_names=("__pycache__", ".git", "out"), skip_ext=(".pyc", ".pyo")):
    os.makedirs(dst, exist_ok=True)
    for root, dirs, files in os.walk(src):
        dirs[:] = sorted(d for d in dirs if d not in skip_dir_names)
        rel = os.path.relpath(root, src)
        tgt = dst if rel == "." else os.path.join(dst, rel)
        os.makedirs(tgt, exist_ok=True)
        for f in sorted(files):
            if os.path.splitext(f)[1].lower() in skip_ext:
                continue
            shutil.copy2(os.path.join(root, f), os.path.join(tgt, f))


def safe_reset(work_root, sub):
    target = os.path.abspath(os.path.join(work_root, sub))
    wr = os.path.abspath(work_root)
    # 只允许删除 --work 内部（严格子路径）的目录：绝不碰工作根本身或其父目录
    if target == wr or not target.startswith(wr + os.sep):
        raise SystemExit("拒绝操作（越界）: %s 不在 %s 内部" % (target, wr))
    if os.path.isfile(os.path.join(wr, "SKILL.md")):
        raise SystemExit("拒绝操作：--work 指向技能包内部（%s）" % wr)
    if len(os.path.normpath(wr).split(os.sep)) < 2:
        raise SystemExit("拒绝操作：--work 太靠近盘根（%s）" % wr)
    if os.path.isdir(target):
        shutil.rmtree(target)
    return target


# --------------------------------------------------------------------------
# 矩阵定义
# --------------------------------------------------------------------------
def build_rows():
    R = []

    def add(rid, form, oc, kind="oc-set", note=""):
        R.append({"id": rid, "form": form, "oc": oc, "kind": kind, "note": note})

    # 控制行（对照组）：不改契约，用来证明"三层检查本来都是绿的"
    add("control-base", "控制组：原样 case.json（不注入）", "<KEEP>", kind="oc-keep",
        note="每一行的判定都要与这一行对比，否则无法区分'契约注入造成'与'本来就如此'")

    # ① 标量 / 字符串
    add("form1-str-literal", "①标量 str：非空字面量", {"c_str": "hello"},
        note="文档 §3：真实值优先，无真实值则 ''")
    add("form1-str-empty", "①标量 str：空串（边界）", {"c_str_empty": ""})
    add("form1-str-long", "①标量 str：超长 4096 字符（边界）", {"c_str_long": "x" * 4096})
    add("form1-str-cjk", "①标量 str：非 ASCII 中文", {"c_str_cjk": "机制图—通路 ✓"})
    add("form1-str-key-long", "①标量 str：200 字符键名（边界）", {"k" * 200: "v"})
    add("form1-str-key-dot", "①标量 str：键名含 '.' 与 '[0]'（边界）", {"a.b": "v", "x[0]": "w"})

    # ② 容器 list
    add("form2-list", "②容器 list：非空", {"c_list": ["a", "b"]})
    add("form2-list-empty", "②容器 list：空数组（边界）", {"c_list_empty": []})
    add("form2-list-200", "②容器 list：200 项（边界）", {"c_list_big": list(range(200))})

    # ③ 布尔
    add("form3-bool-true", "③布尔 true", {"c_bool": True})
    add("form3-bool-typed", "③布尔（typed 声明 {type:bool}）", {"c_bool_typed": {"type": "bool"}})

    # ④ 数值 / 字典
    add("form4-num-int", "④数值 int", {"c_num": 150})
    add("form4-num-zero", "④数值 0（边界）", {"c_num_zero": 0})
    add("form4-num-float", "④数值 浮点 1.5（边界）", {"c_num_float": 1.5})
    add("form4-num-typed", "④数值（typed {type:number}）", {"c_num_typed": {"type": "number"}})
    add("form4-dict-literal", "④字典：非空字面量", {"c_obj": {"a": 1}})
    add("form4-dict-empty", "④字典：空对象（边界）", {"c_obj_empty": {}})
    add("form4-dict-typed", "④字典（typed {type:dict}）", {"c_obj_typed": {"type": "dict"}})
    add("typed-str", "typed str 声明", {"c_t_str": {"type": "str"}})
    add("typed-list", "typed list 声明", {"c_t_list": {"type": "list"}})
    add("typed-list-annotated", "typed list + 额外注释键", {"c_t_note": {"type": "list", "note": "x"}})

    # 边界值 / 非法类型
    add("edge-null", "边界：声明值为显式 null", {"c_null": None},
        note="文档 §3 禁止 result.json 顶层 null；声明 null 时填空属文档行为")
    add("edge-nested", "边界：嵌套声明 {a:{b:1}}", {"c_nested": {"a": {"b": 1}}},
        note="文档只描述顶层键→容器；嵌套结构被压平")
    add("edge-typed-invalid", "边界：非法类型名 {type:'tuple'}", {"c_t_bad": {"type": "tuple"}},
        note="文档只列 5 个已知类型名")
    add("edge-typed-empty-obj", "边界：typed 空对象 {}", {"c_t_empty": {}})
    add("edge-collide-envelope", "边界：键与信封字段同名 status", {"status": "CASE_WANTS_THIS"},
        note="文档 §3：真实值优先")
    add("edge-collide-caseid-typed", "边界：case_id 声明为数值 12345", {"case_id": 12345},
        note="信封真实值是字符串 → 与声明类型冲突")
    add("edge-collide-internal", "边界：键与流水线内部临时键同名 _echo_missing",
        {"_echo_missing": "declared"}, note="内部临时键在 g2 判定后被删除")
    add("edge-many-fields", "边界：60 个字段", {"c_%02d" % i: i for i in range(60)})
    add("edge-empty-contract", "边界：output_contract = {} （空对象）", {})

    # 结构性非法（契约容器本身不是映射）
    add("struct-oc-list", "结构非法：output_contract = 数组", ["a", "b"], kind="oc-raw")
    add("struct-oc-str", "结构非法：output_contract = 字符串", "abc", kind="oc-raw")
    add("struct-oc-num", "结构非法：output_contract = 数值 0", 0, kind="oc-raw")
    add("struct-oc-bool", "结构非法：output_contract = 布尔 true", True, kind="oc-raw")
    add("struct-oc-null", "结构非法：output_contract = null", None, kind="oc-raw")
    add("struct-oc-missing", "结构：case.json 没有 output_contract 键", None, kind="oc-drop")

    # 结构性非法（case.json 本身）
    add("struct-case-missing", "结构非法：--case 指向不存在的文件", None, kind="case-missing")
    add("struct-case-notjson", "结构非法：case.json 不是合法 JSON", None, kind="case-notjson")
    add("struct-case-notobject", "结构非法：case.json 是数组（不是对象）", None, kind="case-notobject")
    return R


# --------------------------------------------------------------------------
def run_row(row, pkg, base_case_dir, work, roots, python, fmt, dpi):
    row_dir = safe_reset(work, os.path.join("rows", row["id"]))
    out_dir = os.path.join(row_dir, "out")
    case_path = os.path.join(row_dir, "case.json")
    model_path = os.path.join(row_dir, "model.example.json")
    base_case = os.path.join(base_case_dir, "case.json")
    base_model = os.path.join(base_case_dir, "model.example.json")

    rec = {"id": row["id"], "form": row["form"], "kind": row["kind"], "note": row["note"]}
    os.makedirs(row_dir, exist_ok=True)
    if row["kind"] != "case-missing":
        for name in os.listdir(base_case_dir):
            src = os.path.join(base_case_dir, name)
            if os.path.isfile(src):
                shutil.copy2(src, os.path.join(row_dir, name))
        mat_src = os.path.join(base_case_dir, "materials")
        if os.path.isdir(mat_src):
            shutil.copytree(mat_src, os.path.join(row_dir, "materials"), dirs_exist_ok=True)
        if row["kind"] == "case-notjson":
            with open(case_path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write("{ this is not json ,,,\n")
        else:
            case = load_json(base_case)
            if row["kind"] == "case-notobject":
                case = ["not", "an", "object"]
            elif row["kind"] != "oc-keep":
                if row["kind"] == "oc-drop":
                    case.pop("output_contract", None)
                else:
                    case["output_contract"] = row["oc"]
            rec["injected_contract"] = (None if row["kind"] in ("oc-drop", "case-missing",
                                                               "case-notjson", "case-notobject")
                                        else case.get("output_contract")
                                        if isinstance(case, dict) else case)
            rec["contract_key_present"] = (isinstance(case, dict)
                                          and "output_contract" in case)
            dump_json(case, case_path)

    argv = [python, os.path.join(pkg, "scripts", "main.py"), "--case", case_path,
            "--model-file", model_path, "--out", "out", "--formats", fmt, "--dpi", str(dpi)]
    proc = subprocess.run(argv, cwd=row_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          timeout=900)
    stdout = proc.stdout.decode("utf-8", "replace")
    stderr = proc.stderr.decode("utf-8", "replace")
    rec["main"] = {"exit_code": proc.returncode,
                   "stdout_tail": portable("\n".join(stdout.strip().splitlines()[-3:]), roots),
                   "stderr_tail": portable("\n".join(stderr.strip().splitlines()[-3:]), roots)}
    for line in reversed(stdout.splitlines()):
        if line.startswith("SUMMARY "):
            try:
                rec["main"]["summary"] = json.loads(line[len("SUMMARY "):])
            except Exception:
                pass
            break

    rj_path = os.path.join(out_dir, "result.json")
    rec["result_json"] = os.path.isfile(rj_path)
    rec["deliverables"] = sorted(os.listdir(out_dir)) if os.path.isdir(out_dir) else []

    declared = {}
    injected = rec.get("injected_contract")
    if isinstance(injected, dict):
        declared = injected
    rec["n_declared_keys"] = len(declared)
    rec["contract_is_mapping"] = isinstance(injected, dict)
    # 注意："没有这个键"与"键存在但值是 null"是两种不同情形，必须分开记
    rec.setdefault("contract_key_present", injected is not None)
    rec["contract_present"] = bool(rec["contract_key_present"])

    echo, nulls, trace_hits = {}, [], []
    if rec["result_json"]:
        rj = load_json(rj_path)
        nulls = [k for k, v in rj.items() if v is None]
        for k, decl in declared.items():
            if k not in rj:
                echo[k] = {"present": False, "value": None, "json_type": None,
                           "expected_types": sorted(expected_types(decl)),
                           "form_ok": False, "note": "声明字段未出现在 result.json"}
                continue
            v = rj[k]
            exp = sorted(expected_types(decl))
            jt = json_type(v)
            echo[k] = {"present": True, "value": short(v), "json_type": jt,
                       "expected_types": exp,
                       "form_ok": (jt in exp),
                       "value_preserved": (v == decl) if not isinstance(decl, dict) or "type" not in decl
                       else None}
        blob = json.dumps(rj.get("uncertainty") or [], ensure_ascii=False) + \
            json.dumps(rj.get("change_records") or [], ensure_ascii=False)
        for k in declared:
            if k in blob:
                trace_hits.append(k)
        if not declared and not rec["contract_is_mapping"] and rec["contract_present"]:
            for probe in ("output_contract", "契约"):
                if probe in blob:
                    trace_hits.append(probe)
        rec["gates"] = {k: v.get("pass") for k, v in (rj.get("gates") or {}).items()}
        rec["status"] = rj.get("status")
        rec["uncertainty_n"] = len(rj.get("uncertainty") or [])
        rec["change_records_n"] = len(rj.get("change_records") or [])
    rec["echo"] = echo
    rec["null_top_level"] = nulls
    rec["trace_mentions_contract"] = sorted(set(trace_hits))

    # 第 2 层：独立检查器
    if rec["result_json"]:
        cc = subprocess.run([python, os.path.join(pkg, "scripts", "check_contract.py"),
                             "--result", rj_path, "--case", case_path],
                            cwd=row_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            timeout=300)
        ccout = cc.stdout.decode("utf-8", "replace")
        rec["check_contract"] = {
            "exit_code": cc.returncode,
            "failed_checks": [ln.split()[1] for ln in ccout.splitlines()
                              if ln.startswith("fail ") and len(ln.split()) > 1],
            "stdout_tail": portable("\n".join(ccout.strip().splitlines()[-4:]), roots)}
    else:
        rec["check_contract"] = {"exit_code": None, "failed_checks": [],
                                 "stdout_tail": "无 result.json，跳过"}

    # 第 3 层判定 + 分类
    classify(rec, declared)
    return rec


def classify(rec, declared):
    """三层判定 → 行分类（规则与 references/CONTRACT-MATRIX.md 逐字一致）。"""
    main = rec.get("main", {})
    exit_code = main.get("exit_code")
    status = rec.get("status")
    g2 = (rec.get("gates") or {}).get("g2_contract_echo")
    cc_exit = (rec.get("check_contract") or {}).get("exit_code")
    clean = (exit_code == 0) and (status == "success")
    g2_pass = (g2 is True) or (g2 is None and not rec["result_json"])
    cc_ok = (cc_exit == 0)

    problems = []
    if not rec["result_json"]:
        problems.append("no_result_json")
    if rec["contract_present"] and not rec["contract_is_mapping"]:
        problems.append("contract_container_not_mapping")
    if rec["contract_present"] and rec["contract_is_mapping"] and not declared:
        problems.append("contract_empty_mapping")
    for k, e in (rec.get("echo") or {}).items():
        if not e["present"]:
            problems.append("declared_key_missing:%s" % k)
        elif not e["form_ok"]:
            problems.append("declared_type_violated:%s(declared=%s,echoed=%s)"
                            % (k, "/".join(e["expected_types"]), e["json_type"]))
    if rec["null_top_level"]:
        problems.append("null_at_top_level:%s" % ",".join(rec["null_top_level"]))

    # 严重度：只有「空对象的整体契约」是文档允许的空填充，其余都算形态违规
    shape_gap = [p for p in problems if p != "contract_empty_mapping"]

    if not problems:
        verdict = "ok"
    elif shape_gap:
        verdict = "flagged" if (not clean or g2_pass is False or not cc_ok) else "silent_gap"
    else:
        verdict = "fill_documented"

    # "文档允许但无留痕"：声明了值/形态，却在 result.json 里被丢弃或压平且无任何记录
    untraced = False
    if verdict in ("fill_documented", "ok"):
        for k, e in (rec.get("echo") or {}).items():
            if e["present"] and e.get("value_preserved") is False:
                untraced = True
        if rec.get("contract_is_mapping") and declared and not rec["trace_mentions_contract"]:
            for k, e in (rec.get("echo") or {}).items():
                if e["present"] and e.get("value_preserved") is False:
                    untraced = True
    rec["verdict"] = verdict
    rec["problems"] = problems
    rec["shape_gap_problems"] = shape_gap
    rec["documented_but_untraced"] = bool(untraced)
    rec["three_layer"] = {"pipeline_clean": clean, "exit_code": exit_code, "status": status,
                          "g2_contract_echo_pass": g2, "check_contract_exit": cc_exit,
                          "check_contract_ok": cc_ok}


# --------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(
        description="contract four-form x boundary-value matrix for the pathway-diagram skill")
    ap.add_argument("--skill", default=DEFAULT_SKILL_ROOT)
    ap.add_argument("--case", default=None, help="base case.json（默认 <skill>/examples/case.json）")
    ap.add_argument("--model-file", default=None,
                    help="模型（默认 <skill>/examples/model.example.json）")
    ap.add_argument("--work", default=None)
    ap.add_argument("--report", default=None)
    ap.add_argument("--formats", default="svg,png,pdf")
    ap.add_argument("--dpi", type=int, default=150)
    ap.add_argument("--python", default=None)
    ap.add_argument("--only", default=None, help="只跑 id 匹配的行（逗号分隔或子串）")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    skill_root = os.path.abspath(args.skill)
    if not os.path.isfile(os.path.join(skill_root, "SKILL.md")):
        print("错误：--skill 下没有 SKILL.md：%s" % skill_root, file=sys.stderr)
        return 4
    args.case = args.case or os.path.join(skill_root, "examples", "case.json")
    args.model_file = args.model_file or os.path.join(skill_root, "examples", "model.example.json")
    for p in (args.case, args.model_file):
        if not os.path.isfile(p):
            print("错误：找不到 %s" % p, file=sys.stderr)
            return 4
    if args.work is None:
        import tempfile
        args.work = os.path.join(tempfile.gettempdir(), "cm-%d" % os.getpid())
    work = os.path.abspath(args.work)
    os.makedirs(work, exist_ok=True)
    roots = [(work, "<WORK>"), (skill_root, "<SKILL>")]
    python = args.python or sys.executable

    pkg = safe_reset(work, "pkg")
    copy_tree(skill_root, pkg)
    base_case_dir = safe_reset(work, "base")
    os.makedirs(base_case_dir, exist_ok=True)
    src_dir = os.path.dirname(os.path.abspath(args.case))
    for name in os.listdir(src_dir):
        src = os.path.join(src_dir, name)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(base_case_dir, name))
        elif os.path.isdir(src) and name != "output":
            shutil.copytree(src, os.path.join(base_case_dir, name), dirs_exist_ok=True)
    shutil.copy2(args.model_file, os.path.join(base_case_dir, "model.example.json"))

    rows = build_rows()
    if args.only:
        keys = [k.strip() for k in args.only.split(",") if k.strip()]
        rows = [r for r in rows if any(k in r["id"] for k in keys)]
        if not rows:
            print("错误：--only 没匹配到任何行", file=sys.stderr)
            return 4

    results = []
    for i, row in enumerate(rows, 1):
        rec = run_row(row, pkg, base_case_dir, work, roots, python, args.formats, args.dpi)
        results.append(rec)
        if not args.json:
            print("[%2d/%d] %-28s exit=%s status=%-8s g2=%-5s cc=%-5s -> %s%s" %
                  (i, len(rows), rec["id"], rec["main"]["exit_code"], rec.get("status"),
                   (rec.get("gates") or {}).get("g2_contract_echo"),
                   (rec.get("check_contract") or {}).get("exit_code"),
                   rec["verdict"],
                   "  (无留痕)" if rec.get("documented_but_untraced") else ""))

    control = next((r for r in results if r["id"] == "control-base"), None)
    summary = {
        "rows": len(results),
        "control": ({"exit_code": control["main"]["exit_code"], "status": control.get("status"),
                     "g2": (control.get("gates") or {}).get("g2_contract_echo"),
                     "check_contract_exit": (control.get("check_contract") or {}).get("exit_code")}
                    if control else None),
        "by_verdict": {v: sorted(r["id"] for r in results if r["verdict"] == v)
                       for v in ("ok", "fill_documented", "silent_gap", "flagged")},
        "documented_but_untraced": sorted(r["id"] for r in results
                                          if r.get("documented_but_untraced")),
        "null_at_top_level_rows": sorted(r["id"] for r in results if r["null_top_level"]),
        "undocumented_exit_codes": sorted({r["main"]["exit_code"] for r in results}
                                          - {0, 2, 3}),
    }
    report = portable_obj({
        "probe": "contract-matrix",
        "tool": "scripts/contract_matrix.py",
        "tool_version": TOOL_VERSION,
        "what_this_measures": [
            "OUTPUT_CONTRACT.md §3 四形态（①②③④ + 类型化声明）逐个注入并跑真实主流程",
            "边界值：空串/空数组/0/false/超长/非法类型名/缺字段/显式 null/键名重名/契约容器非法",
            "三层判定：主流程退出码+status+g2 / check_contract.py / result.json 实际回显",
        ],
        "config": {
            "case": portable(os.path.join(work, "base", "case.json"), roots),
            "model_file": portable(os.path.join(work, "base", "model.example.json"), roots),
            "formats": args.formats, "dpi": args.dpi,
            "python": sys.version.split()[0], "platform": sys.platform,
            "skill_version_note": "被测 = 本包 scripts/main.py + scripts/check_contract.py",
        },
        "classification_rules": {
            "ok": "声明键全出现 + 回显类型与声明形态一致（或无声明键）",
            "fill_documented": "只有「空对象契约/文档允许的空填充」类问题，无形态违规",
            "silent_gap": "存在形态违规（键丢失 / 类型不符 / 契约容器非映射 / 无 result.json）"
                          "而主流程(exit 0 + status success + g2 pass)与 check_contract 全 pass",
            "flagged": "同样的形态违规被某一层抓到（g2 fail 或 check_contract 非零或 status 降级）",
            "documented_but_untraced": "声明值被丢弃/压平（文档允许），但 uncertainty 与 "
                                       "change_records 里没有任何与契约/字段相关的留痕",
        },
        "rows": results,
        "summary": summary,
        "not_covered": NOT_COVERED,
    }, roots)
    report_path = args.report or os.path.join(skill_root, "contract_matrix_report.json")
    blob = json.dumps(report, ensure_ascii=False, indent=2)
    with open(report_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(blob + "\n")

    if args.json:
        print(blob)
    else:
        print("=" * 78)
        print("rows=%d  control=%s" % (summary["rows"], summary["control"]))
        for v in ("ok", "fill_documented", "silent_gap", "flagged"):
            print("  %-16s %d  %s" % (v, len(summary["by_verdict"][v]),
                                      ", ".join(summary["by_verdict"][v]) or "-"))
        print("  documented_but_untraced: %s" % (", ".join(summary["documented_but_untraced"]) or "-"))
        print("  undocumented exit codes: %s" % (summary["undocumented_exit_codes"] or "-"))
        print("  report -> %s" % report_path)
    if control and (control["main"]["exit_code"] != 0 or control.get("status") != "success"):
        print("控制行未通过：矩阵结论不可用", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
