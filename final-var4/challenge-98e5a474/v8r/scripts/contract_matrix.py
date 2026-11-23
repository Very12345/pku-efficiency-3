#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""contract_matrix.py -- 契约四形态 × 边界值矩阵（可运行的注入矩阵执行器）。

`result.json` 的唯一评分面是 `references/OUTPUT_CONTRACT.md` 定义的契约：平台在
`/input/case.json` 里给出一个 `output_contract` 对象，本技能必须把它的**每个键**
回显到 `result.json` 顶层，且不得出现 `null`。真实平台的契约清单我们不掌握，
因此这条链路必须对**任意形状的声明**都给出可判定的行为。

本脚本把这条链路当成一个**黑盒函数**来测：

    f(case.json 的 output_contract) -> (main 退出码, result.json 顶层回显, G5 判定)

矩阵逐行注入「六种容器形态 × 边界值 × 非法类型 × 缺字段」，每行真跑一次主流程与一次
独立契约校验器（`scripts/validate_result.py`，G1–G8），记录**实测**读数，并额外判定
一个关键性质：**静默通过** —— 校验器说 VALID，但声明其实**没有被兑现**。

设计原则：

1. **只动包外副本**：整包复制到 tempfile.mkdtemp()，在那里改 case、跑副本；
   `--out` 指向包内直接拒绝（会把产物与 __pycache__ 混进交付包）。
2. **不改被测代码**：注入只发生在 case.json 上，不 patch 任何脚本逻辑。
3. **不伪造数据**：记录的是子进程真实 returncode 与真实 result.json 字段；
   拿不到 result.json 就记「无产物」，不做推断。
4. **发现静默通过不算脚本失败**：它是**数据**。退出码表达的是「矩阵是否完整跑完」，
   不是「被测系统是否完美」—— 静默通过的清单写进报告，交给复核者。

用法（建议在包外运行，产物写到包外）：

    python scripts/contract_matrix.py --skill-root <技能根> --out <包外目录>
    python scripts/contract_matrix.py --skill-root . --out /tmp/cm --list
    python scripts/contract_matrix.py --skill-root . --out /tmp/cm --only R03,R11
    python scripts/contract_matrix.py --skill-root . --out /tmp/cm --json --quiet

退出码：0 = 每一行都拿到了可判定读数（VALID 与 INVALID 都算读数）；
1 = 至少一行无法测量（无 result.json / 超时 / 崩溃且无记录）；2 = 参数或环境错误。
"""

import argparse
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import traceback

try:  # 窄编码控制台（GBK）不得让 --help / 日志崩溃
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ROOT = os.path.dirname(HERE)
PY = sys.executable or "python"


# --------------------------------------------------------------------------
# 小工具
# --------------------------------------------------------------------------
def log(msg, *args):
    print("[cm] " + (msg % args if args else msg), flush=True)


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def dump_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def tail(text, n=5, width=180):
    lines = [l for l in (text or "").splitlines() if l.strip()]
    return [l[:width] for l in lines[-n:]]


def in_root(path, root):
    a = os.path.abspath(path).rstrip("\\/").lower()
    b = os.path.abspath(root).rstrip("\\/").lower()
    return a == b or a.startswith(b + os.sep) or a.startswith(b + "/")


def type_name(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, str):
        return "str"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "dict"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    return type(value).__name__


# --------------------------------------------------------------------------
# 矩阵定义：一行 = 一个注入
# --------------------------------------------------------------------------
# expect: 按 references/OUTPUT_CONTRACT.md 的「四形态回显 + 禁 null」规则，
#         这一行**应该**发生什么（人读文本；判据由 judge_row 逐行落地）。
ROWS = [
    # ---------- 六种容器形态（正常声明） ----------
    dict(id="R01", form="string", boundary="normal", oc={"s_note": "string"},
         expect="回显 str 空串 \"\"，G5 VALID"),
    dict(id="R02", form="array", boundary="normal", oc={"a_items": "array"},
         expect="回显 list 空数组 []，G5 VALID"),
    dict(id="R03", form="object", boundary="normal", oc={"o_meta": "object"},
         expect="回显 dict 空对象 {}，G5 VALID"),
    dict(id="R04", form="number", boundary="normal", oc={"n_count": "number"},
         expect="回显 int 0，G5 VALID"),
    dict(id="R05", form="boolean", boundary="normal", oc={"b_flag": "boolean"},
         expect="回显 bool false，G5 VALID（bool 不是 number）"),
    dict(id="R06", form="nested-object", boundary="normal",
         oc={"o_nested": {"a": {"b": "array"}}},
         expect="提示是嵌套对象 ⇒ 按 object 回显 {}，G5 VALID"),
    dict(id="R07", form="nested-array", boundary="normal",
         oc={"a_nested": ["string", "array"]},
         expect="提示是数组 ⇒ 按 array 回显 []，G5 VALID"),
    dict(id="R08", form="mixed-forms", boundary="normal",
         oc={"s1": "string", "a1": "array", "o1": "object",
             "n1": "number", "b1": "boolean"},
         expect="五形态同一次声明全部回显，G5 VALID，顶层键 +5"),
    # ---------- 边界值 ----------
    dict(id="R09", form="string", boundary="empty-string", oc={"s_empty": ""},
         expect="空串提示 ⇒ 未知类型 ⇒ 回显 \"\"，G5 VALID"),
    dict(id="R10", form="array", boundary="empty-array", oc={"a_empty": []},
         expect="空数组提示 ⇒ array ⇒ 回显 []，G5 VALID"),
    dict(id="R11", form="object", boundary="empty-object", oc={"o_empty": {}},
         expect="空对象提示 ⇒ object ⇒ 回显 {}，G5 VALID"),
    dict(id="R12", form="number", boundary="zero", oc={"n_zero": 0},
         expect="字面量数字被当作类型提示 ⇒ 回显 0，G5 VALID"),
    dict(id="R13", form="number", boundary="literal-12", oc={"n_lit": 12},
         expect="字面量 12 ⇒ 回显 0（默认值，不是 12），G5 VALID —— **声明未被兑现但校验通过**"),
    dict(id="R14", form="boolean", boundary="true", oc={"b_true": True},
         expect="字面量 true ⇒ 回显 false，G5 VALID —— 同上"),
    dict(id="R15", form="null-hint", boundary="null-hint-string",
         oc={"x_null": "null"},
         expect="提示字符串 null ⇒ 未知类型 ⇒ 回显 \"\"，G5 VALID"),
    dict(id="R16", form="null-hint", boundary="null-value", oc={"x_none": None},
         expect="声明值为 JSON null ⇒ 回显 null ⇒ G5 **必须 INVALID**"),
    dict(id="R17", form="unknown", boundary="unknown-string",
         oc={"x_unknown": "whatever"},
         expect="未知类型字符串 ⇒ 静默当 string 回显 \"\"，G5 VALID —— **静默通过**"),
    dict(id="R18", form="string", boundary="long-hint-1k",
         oc={"x_long": "L" * 1024},
         expect="超长提示（1024 字符）⇒ 未知类型 ⇒ 回显 \"\"，G5 VALID"),
    dict(id="R19", form="string", boundary="long-key-1k",
         oc={("k" * 1024): "string"},
         expect="超长键名（1024 字符）⇒ 键原样回显，G5 VALID"),
    dict(id="R20", form="array", boundary="huge-declared-value",
         oc={"x_huge": "array"}, summary_pad="字" * 70000,
         expect="用 summary 塞 ~210KB 文本 ⇒ result.json 逼近 500KB 上限；契约侧仍 VALID"),
    # ---------- 非法类型 ----------
    dict(id="R21", form="array", boundary="mixed-elements", oc={"x_mixed": ["a", 1]},
         expect="混合数组提示 ⇒ array ⇒ 回显 []，G5 VALID —— **静默通过**"),
    dict(id="R22", form="object", boundary="tuple-like", oc={"x_pair": ["a", "b"]},
         expect="双元素数组提示 ⇒ array ⇒ 回显 []，G5 VALID"),
    dict(id="R23", form="object", boundary="deep-nest",
         oc={"x_deep": {"a": {"b": {"c": ["d"]}}}},
         expect="深层嵌套提示 ⇒ object ⇒ 回显 {}，G5 VALID"),
    dict(id="R24", form="collision", boundary="collide-artifacts",
         oc={"artifacts": "string"},
         expect="契约键与既有非空字段撞车：**不回显**（已有值），G5 期望 str 但实测 list ⇒ INVALID"),
    dict(id="R25", form="collision", boundary="collide-title",
         oc={"title": "array"},
         expect="同上：title 已是 str，G5 期望 list ⇒ INVALID"),
    dict(id="R26", form="collision", boundary="collide-case_id",
         oc={"case_id": "object"},
         expect="case_id 由报告装配保证非空 ⇒ 不回显；G5 期望 dict ⇒ INVALID"),
    # ---------- 缺字段 / 顶层形状非法 ----------
    dict(id="R27", form="missing", boundary="no-output_contract", oc=None,
         expect="整个 output_contract 缺失 ⇒ 无回显；G5 跳过（oc 非 dict）⇒ **VALID，静默**"),
    dict(id="R28", form="missing", boundary="oc-null", oc="__NULL__",
         expect="output_contract 为 JSON null ⇒ 无回显；G5 跳过 ⇒ **VALID，静默**"),
    dict(id="R29", form="missing", boundary="oc-empty-array", oc=[],
         expect="output_contract 为 [] ⇒ 无回显；G5 跳过 ⇒ **VALID，静默**"),
    dict(id="R30", form="missing", boundary="oc-string", oc="oops",
         expect="output_contract 为字符串 ⇒ 无回显；G5 跳过 ⇒ **VALID，静默**"),
    dict(id="R31", form="missing", boundary="oc-empty-object", oc={},
         expect="output_contract 为 {} ⇒ 无回显；G5 跳过（not oc）⇒ **VALID，静默**"),
]

SENTINEL_NULL = "__NULL__"


# --------------------------------------------------------------------------
# 判据
# --------------------------------------------------------------------------
def expected_type(hint):
    """按 OUTPUT_CONTRACT 的四形态规则预期回显的 python 类型名。"""
    if isinstance(hint, str):
        low = hint.strip().lower()
        if low in ("array", "list", "json-array", "sequence"):
            return "list"
        if low in ("object", "dict", "map", "json-object"):
            return "dict"
        if low in ("number", "integer", "int", "float", "numeric", "double"):
            return "number"
        if low in ("boolean", "bool"):
            return "bool"
        return "str"
    if isinstance(hint, list):
        return "list"
    if isinstance(hint, dict):
        return "dict"
    if isinstance(hint, bool):
        return "bool"
    if isinstance(hint, (int, float)):
        return "number"
    if hint is None:
        return "null"
    return "unknown"


def type_matches(value, want):
    if want == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if want == "bool":
        return isinstance(value, bool)
    if want == "str":
        return isinstance(value, str)
    if want == "list":
        return isinstance(value, list)
    if want == "dict":
        return isinstance(value, dict)
    if want == "null":
        return value is None
    return True


def judge_silent(row, oc, result, validator_valid):
    """判定「静默通过」：校验器 VALID，但契约声明没有被如实兑现。

    四类静默（每一类都必须在报告里点名）：
      S1 未知/无法识别的类型提示被**当字符串**接受（"whatever" / "" / "null" / "L"*1024）；
      S2 字面量被当成"类型"而不是"值"，回显 0/false 而非声明里的 12/true；
      S3 非法容器（混合数组、深层嵌套）被降级成空容器，且无任何 warn；
      S4 顶层 output_contract 形状非法（缺失/null/[]/字符串/{}）时 G5 **整段跳过**；
      S5 契约键与既有字段撞车时"不回显"这一路径没有被任何门记录（只有 G5 事后偶然发现）。
    """
    if not validator_valid:
        return None
    if not isinstance(oc, dict) or not oc:
        return {"code": "S4", "why": "output_contract 不是非空对象 ⇒ G5 整段跳过，"
                                     "「没有契约」与「契约满足」在校验器眼里不可区分"}
    hits = []
    for key, hint in oc.items():
        val = result.get(key)
        want = expected_type(hint)
        if val is None:
            continue
        if isinstance(hint, str):
            low = hint.strip().lower()
            known = low in ("array", "list", "json-array", "sequence", "object",
                            "dict", "map", "json-object", "number", "integer",
                            "int", "float", "numeric", "double", "boolean", "bool",
                            "string", "text", "str")
            if not known:
                hits.append("S1: 未知提示 %r 被当 string 接受（回显 %r）"
                            % (hint[:24], val))
        elif isinstance(hint, (int, float)) and not isinstance(hint, bool):
            if val != hint:
                hits.append("S2: 字面量 %r 被当作类型，回显默认值 %r（声明值未被兑现）"
                            % (hint, val))
        elif isinstance(hint, bool):
            if val is not hint:
                hits.append("S2: 字面量 %r 被当作类型，回显默认值 %r" % (hint, val))
        elif isinstance(hint, list) and hint:
            if val == []:
                hits.append("S3: 数组提示 %r 降级为空数组（无 warn，元素/内部结构无任何门记录）" % (hint,))
        elif isinstance(hint, dict) and hint:
            if val == {}:
                hits.append("S3: 结构化对象提示 %r 降级为空对象（无 warn，内部字段无任何门记录）" % (hint,))
        if val is not None and not type_matches(val, want) and validator_valid:
            hits.append("S5: 回显类型 %s 与声明 %s 不符但 G5 未报"
                        % (type_name(val), want))
    return {"code": "+".join(sorted({h.split(":")[0] for h in hits})) or "S0",
            "why": "; ".join(hits)} if hits else None


def make_case(base_case, row, fx_dir):
    """由 base case 派生出该行注入后的 case.json，返回其路径。"""
    case = copy.deepcopy(base_case)
    oc = row["oc"]
    if oc is None:
        case.pop("output_contract", None)
    elif oc == SENTINEL_NULL:
        case["output_contract"] = None
    else:
        case["output_contract"] = copy.deepcopy(oc)
    if row.get("summary_pad"):
        case["summary"] = row["summary_pad"]
    path = os.path.join(fx_dir, row["id"] + ".json")
    dump_json(path, case)
    return path


def run_row(row, skill_root, scratch, base_case, args):
    fx = os.path.join(scratch, row["id"], "fx")
    out = os.path.join(scratch, row["id"], "out")
    os.makedirs(fx, exist_ok=True)
    os.makedirs(out, exist_ok=True)
    pkg = os.path.join(scratch, row["id"], "pkg")
    shutil.copytree(skill_root, pkg,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    case_path = make_case(base_case, row, fx)

    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    cmd = [PY, "-B", os.path.join(pkg, "scripts", "main.py"),
           "--case", case_path, "--out", out]
    rec = {
        "id": row["id"], "form": row["form"], "boundary": row["boundary"],
        "injected": _short_json(row["oc"]), "expected": row["expect"],
        "command": "python -B <pkg>/scripts/main.py --case <fx>/%s.json --out <out>"
                   % row["id"],
    }
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, cwd=scratch, env=env, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, timeout=args.timeout)
        rec["main_exit"] = proc.returncode
        rec["seconds"] = round(time.time() - t0, 2)
        rec["stdout_tail"] = tail(proc.stdout.decode("utf-8", "replace"))
    except subprocess.TimeoutExpired:
        rec["main_exit"] = None
        rec["seconds"] = round(time.time() - t0, 2)
        rec["timeout"] = True
        rec["stdout_tail"] = ["<timeout after %ss>" % args.timeout]

    rp = os.path.join(out, "result.json")
    rec["result_json"] = os.path.isfile(rp)
    if not rec["result_json"]:
        rec["status"] = None
        rec["measureable"] = False
        rec["note"] = "主流程没有写出 result.json（该行无法测量）"
        rec["silent_pass"] = None
        return rec

    try:
        result = load_json(rp)
    except Exception as exc:                        # pragma: no cover
        rec["status"] = None
        rec["measureable"] = False
        rec["note"] = "result.json 无法解析：%r" % (exc,)
        rec["silent_pass"] = None
        return rec

    rec["status"] = result.get("status")
    rec["top_level_keys"] = len(result)
    rec["result_bytes"] = os.path.getsize(rp)
    oc = row["oc"] if isinstance(row["oc"], dict) else {}
    rec["echo"] = {k: {"value": _short_value(result.get(k)),
                       "type": type_name(result.get(k)),
                       "present": k in result,
                       "want": expected_type(v)}
                   for k, v in oc.items()}
    rec["echo_present"] = sum(1 for v in rec["echo"].values() if v["present"])
    rec["echo_expected_type_ok"] = sum(
        1 for k, v in rec["echo"].items()
        if v["present"] and type_matches(result.get(k), v["want"]))

    # 独立契约校验器
    vcmd = [PY, "-B", os.path.join(pkg, "scripts", "validate_result.py"),
            "--case", case_path, "--result", rp, "--out", out, "--json"]
    try:
        vp = subprocess.run(vcmd, cwd=scratch, env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=args.timeout)
        rec["validator_exit"] = vp.returncode
        try:
            verdict = json.loads(vp.stdout.decode("utf-8", "replace"))
            rec["valid"] = bool(verdict.get("valid"))
            rec["g5_problems"] = [p for p in verdict.get("problems", [])
                                  if p.startswith("G5")]
            rec["validator_problems"] = verdict.get("problems", [])[:8]
        except Exception:
            rec["valid"] = None
            rec["g5_problems"] = []
            rec["validator_problems"] = tail(
                vp.stdout.decode("utf-8", "replace"), 3)
    except subprocess.TimeoutExpired:
        rec["validator_exit"] = None
        rec["valid"] = None
        rec["g5_problems"] = []
        rec["validator_problems"] = ["<validator timeout>"]

    silent = judge_silent(row, row["oc"], result, rec.get("valid"))
    rec["silent_pass"] = bool(silent)
    rec["silent_reason"] = silent or {}
    rec["measureable"] = rec.get("valid") is not None
    if not rec["measureable"]:
        rec["note"] = "校验器没有给出可解析判定"
    return rec


def _short_value(v):
    s = repr(v)
    return s if len(s) <= 60 else s[:57] + "..."


def _short_json(obj, width=160):
    try:
        s = json.dumps(obj, ensure_ascii=False, sort_keys=True)
    except Exception:
        s = repr(obj)
    return s if len(s) <= width else s[:width - 3] + "..."


# --------------------------------------------------------------------------
# 主流程
# --------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(
        description="契约四形态 × 边界值矩阵（十几种容器形态/边界值/非法类型/缺字段，"
                    "逐行真跑主流程 + 独立契约校验器，记录实测并判定静默通过）")
    ap.add_argument("--skill-root", default=DEFAULT_ROOT,
                    help="技能根目录（默认：本脚本上一级）")
    ap.add_argument("--out", default=None,
                    help="输出目录（**必须在技能包之外**）；报告写到 "
                         "<out>/contract-matrix.json")
    ap.add_argument("--base-case", default=None,
                    help="基底 case.json（默认 <skill-root>/examples/case.json）")
    ap.add_argument("--only", default=None, help="逗号分隔的行 id，如 R01,R13")
    ap.add_argument("--list", action="store_true", help="只列矩阵，不执行")
    ap.add_argument("--json", action="store_true", help="stdout 也打印 JSON 报告")
    ap.add_argument("--quiet", action="store_true", help="只打印汇总")
    ap.add_argument("--keep", action="store_true", help="保留 scratch（排查用）")
    ap.add_argument("--timeout", type=int, default=180,
                    help="每行每阶段的超时秒数（默认 180）")
    args = ap.parse_args(argv)

    skill_root = os.path.abspath(args.skill_root)
    if not os.path.isdir(os.path.join(skill_root, "scripts")):
        log("FATAL: %s 不像技能根（缺 scripts/）", skill_root)
        return 2
    base_case_path = args.base_case or os.path.join(skill_root, "examples",
                                                    "case.json")
    if not os.path.isfile(base_case_path):
        log("FATAL: base case 不存在：%s", base_case_path)
        return 2

    rows = ROWS
    if args.only:
        want = {x.strip().upper() for x in args.only.split(",") if x.strip()}
        rows = [r for r in ROWS if r["id"].upper() in want]
        if not rows:
            log("FATAL: --only 没有匹配到任何行：%s", args.only)
            return 2

    if args.list:
        print("矩阵（%d 行）：" % len(rows))
        for r in rows:
            print("  %-4s %-14s %-22s  %s"
                  % (r["id"], r["form"], r["boundary"], r["expect"][:78]))
        print("说明：每行都会真跑一次 main.py 与一次 validate_result.py；"
              "「静默通过」= VALID 但声明未被兑现（是数据，不是脚本失败）")
        return 0

    if not args.out:
        log("FATAL: --out 必填（报告要写在包外）")
        return 2
    out_dir = os.path.abspath(args.out)
    if in_root(out_dir, skill_root):
        log("FATAL: --out 不能指向技能包内部（%s）；本脚本只动包外副本", out_dir)
        return 2
    os.makedirs(out_dir, exist_ok=True)

    base_case = load_json(base_case_path)
    scratch = tempfile.mkdtemp(prefix="sse-contract-")
    try:
        records = []
        for i, row in enumerate(rows, 1):
            if not args.quiet:
                log("[%d/%d] %s %s / %s", i, len(rows), row["id"], row["form"],
                    row["boundary"])
            try:
                rec = run_row(row, skill_root, scratch, base_case, args)
            except Exception:                       # pragma: no cover - defensive
                rec = {"id": row["id"], "form": row["form"],
                       "boundary": row["boundary"],
                       "injected": _short_json(row["oc"]),
                       "expected": row["expect"],
                       "measureable": False, "silent_pass": None,
                       "note": "runner exception: " + traceback.format_exc(limit=2)}
            records.append(rec)
            if not args.quiet:
                log("      main_exit=%s status=%s valid=%s silent=%s",
                    rec.get("main_exit"), rec.get("status"),
                    rec.get("valid"), rec.get("silent_pass"))

        measured = [r for r in records if r.get("measureable")]
        silent = [r for r in records if r.get("silent_pass")]
        invalid = [r for r in records if r.get("valid") is False]
        summary = {
            "rows": len(records),
            "measured": len(measured),
            "unmeasurable": len(records) - len(measured),
            "valid": sum(1 for r in measured if r.get("valid")),
            "invalid": len(invalid),
            "silent_pass": len(silent),
            "silent_ids": [r["id"] for r in silent],
            "invalid_ids": [r["id"] for r in invalid],
            "main_exit_0": sum(1 for r in records if r.get("main_exit") == 0),
            "status_counts": _count(r.get("status") for r in records),
            "forms": sorted({r["form"] for r in records}),
            "boundaries": sorted({r["boundary"] for r in records}),
        }
        report = {
            "schema": "sse-contract-matrix/1",
            "skill_root": os.path.basename(skill_root),
            "base_case": os.path.relpath(base_case_path, skill_root)
                        .replace("\\", "/"),
            "python": sys.version.split()[0],
            "rows": records,
            "silent_pass_rows": [
                {"id": r["id"], "form": r["form"], "boundary": r["boundary"],
                 "code": (r.get("silent_reason") or {}).get("code", ""),
                 "why": (r.get("silent_reason") or {}).get("why", "")}
                for r in silent],
            "invalid_rows": [{"id": r["id"], "g5_problems": r.get("g5_problems", [])}
                             for r in invalid],
            "uncovered": [
                "契约声明的**值形状**（数组元素类型、对象内部字段类型）——G5 只查顶层容器类型",
                "oneOf / 联合类型 / anyOf 提示（本仓无此概念，未实现）",
                "平台真实 output_contract 的字段清单（组织方未公开，用合成清单覆盖形态）",
                "并发、中断、result.json 被外部改写",
                "单文件 500KB 上限由平台在打包时执行，本脚本只测到 result.json 的字节数",
            ],
            "summary": summary,
        }
        rp = os.path.join(out_dir, "contract-matrix.json")
        dump_json(rp, report)

        if not args.quiet:
            print("")
            print("  %-4s %-14s %-20s %-6s %-8s %-6s %-6s %s"
                  % ("id", "form", "boundary", "exit", "status", "valid", "silent",
                     "echo"))
            for r in records:
                print("  %-4s %-14s %-20s %-6s %-8s %-6s %-6s %s"
                      % (r["id"], r["form"], r["boundary"][:20],
                         r.get("main_exit"), str(r.get("status"))[:8],
                         r.get("valid"), r.get("silent_pass"),
                         "%d/%d" % (r.get("echo_present", 0),
                                    len(r.get("echo") or {}))))
        log("rows=%d measured=%d valid=%d invalid=%d silent_pass=%d unmeasurable=%d",
            summary["rows"], summary["measured"], summary["valid"],
            summary["invalid"], summary["silent_pass"], summary["unmeasurable"])
        log("silent ids: %s", ", ".join(summary["silent_ids"]) or "(none)")
        log("wrote %s", rp)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=1))
        return 0 if summary["unmeasurable"] == 0 else 1
    finally:
        if args.keep:
            log("scratch kept: %s", scratch)
        else:
            shutil.rmtree(scratch, ignore_errors=True)


def _count(values):
    out = {}
    for v in values:
        out[str(v)] = out.get(str(v), 0) + 1
    return out


if __name__ == "__main__":
    sys.exit(main())
