#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""contract_matrix.py — 契约四形态 × 边界值矩阵实测台（v8 轴）

本脚本把 references/OUTPUT_CONTRACT.md §2 里那句「四种形态脚本全部兼容」
从**声明**变成**逐行实测**：

    对每一行契约注入，真的改一份 case.json、真的跑一遍 main.py，
    再让两个独立校验器（figcheck.py 的 G2、check_contract.py）各判一次，
    记录：main 退出码 / status / 契约字段回显 / 是否被校验器捕获 / 是否静默通过。

为什么必须"真的跑"
------------------
`apply_output_contract()` 是一个 40 行的函数，它的行为**不可能靠读代码确定**：
它读 `result` 里已有字段的方式、`if contract:` 的真值语义、以及 main.py 在
契约落地**之后**还会 pop 掉哪些键，三者叠加才决定最终 result.json 的顶层形态。
本台子把这三者的交互全部实测出来。

矩阵（4 族，共 --rows 行；编号可单独用 --only 复核）
---------------------------------------------------
  F*  容器形态        四形态本身 + 混入非字符串 + 顶层额外键
  B*  边界值          空串名 / 空数组 / 0 / 超长名 / 非法类型名 / null / 重复 / 长取值 / 怪键
  A*  别名与内部键    20 个别名一次回显；5 个**会被 main.py pop 掉**的内部瞬态键
  D*  退化与非法形态  缺键 / null / {} / [] / true / 字符串 / 0 / 3.14 / fields 类型错 / 深嵌套

判定口径（每行都落到一个 verdict）
--------------------------------
  run_error       main.py 没产出可解析的 result.json
  echo_complete   声明的字段全部出现在 result.json 顶层且非 null（契约被正确执行）
  caught          有缺口（字段缺失/为 null，或契约形态非法）但被 main exit≠0 /
                  status≠completed / figcheck G2 / check_contract 任一捕获
  silent_pass     ★ 有缺口却**一路绿灯**：main exit 0、status=completed、G2 通过、
                  check_contract 通过、uncertainty 里也没有任何关于契约的说明

`silent_pass` 清单就是本轴要交的东西 —— 契约层"看起来没事"的行必须被点名，
因为回放 Agent 正是靠这些绿灯判断"契约已满足"。

退出码：0 = 全部行跑完且无 silent_pass；2 = 存在 silent_pass；1 = 用法/环境错误。

用法
----
    python "$SKILL_DIR/scripts/contract_matrix.py"                       # 用包内示例案例
    python "$SKILL_DIR/scripts/contract_matrix.py" --case /input/case.json
    python "$SKILL_DIR/scripts/contract_matrix.py" --only A2,A4,D5 --json
    python "$SKILL_DIR/scripts/contract_matrix.py" --out /tmp/cm.json

    --case       基准案例 JSON（缺省 = 本包 examples/case.json）
    --workspace  包外工作目录（缺省系统临时目录；每行一个隔离副本）
    --out        报告路径（缺省 <workspace>/contract_matrix_report.json）
    --only       只跑这些编号（逗号分隔）
    --json       报告同时打印到 stdout
    --keep       保留每行的隔离副本（默认删除，只留报告）
    --timeout    单次 main.py 超时秒数（默认 300）
    --cross      是否跑交叉校验器（默认 on；--no-cross 跳过 figcheck/check_contract）

报告可移植：本机绝对路径在写出前替换为 <WORKSPACE>/<CASEDIR>/<SKILL_DIR>/<TMP>/<ABS>。
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

HERE = os.path.dirname(os.path.abspath(__file__))
PKG_ROOT = os.path.dirname(HERE)
DEFAULT_CASE = os.path.join(PKG_ROOT, "examples", "case.json")
MAIN_PY = os.path.join(HERE, "main.py")
FIGCHECK_PY = os.path.join(HERE, "figcheck.py")
CHECK_CONTRACT_PY = os.path.join(HERE, "check_contract.py")

_ABS_WIN = re.compile(r"(?<!\w)[A-Za-z]:[\\/](?![\\/])[^\s\"'<>|,;)\]}]*")
_ABS_POSIX = re.compile(r"/(?:app|skills|input|home|Users|mnt|var|tmp)/[^\s\"'<>|,;)\]}]*")
_COPY_SKIP_DIRS = {"out", "work", "__pycache__", ".git", "node_modules"}

LONG_NAME = "L" + "0123456789abcdef" * 256  # 4096+ 字符的字段名
LONG_TITLE = "超长标题：" + ("渠道活性与剂量响应" * 400)  # ~4800 字符


# ---------------------------------------------------------------- 矩阵定义

def _long_alias_map():
    return ["editable_source", "editable_sources", "rendered_preview", "renders",
            "render_png", "render_pdf", "field_mapping", "data_mapping",
            "source_mapping", "data_manifest", "validation_report", "validation",
            "figcheck_report", "mapcheck_report", "sources", "evidence",
            "uncertainty", "change_records", "status", "outputs",
            "checkpoints", "gates"]


ROWS = [
    # ---- F 族：四种容器形态（含等价写法）--------------------------------
    dict(id="F1", family="F 容器形态", title="形态①字段名列表 list[str]",
         kind="set", contract=["case_id", "status", "outputs", "editable_source"],
         expect="四字段全部回显；editable_source 走别名填充为 SVG 名列表"),
    dict(id="F2", family="F 容器形态", title="形态②名称→类型 dict[str,str]",
         kind="set",
         contract={"alpha_s": "string", "beta_a": "array", "gamma_o": "object",
                   "delta_n": "number", "eps_b": "boolean"},
         expect="五个未知名按声明类型给 \"\"/[]/{}/0/false，绝不为 null"),
    dict(id="F3", family="F 容器形态", title="形态③嵌套 fields 列表",
         kind="set", contract={"fields": ["case_id", "sources", "field_mapping"]},
         expect="与形态①等价；field_mapping 走别名给 \"data_manifest.json\""),
    dict(id="F4", family="F 容器形态", title="形态④嵌套 fields 映射",
         kind="set", contract={"fields": {"title": "string", "sources": "array",
                                          "gates": "object"}},
         expect="三字段回显；gates 在契约落地时还是空对象，但最终被真实 gates 覆盖"),
    dict(id="F5", family="F 容器形态", title="嵌套声明：类型位置写成对象",
         kind="set", contract={"fields": {"layer": {"type": "array"}}},
         expect="类型不是字符串 → 落到默认 \"\"（实测确认，不是 []）"),
    dict(id="F6", family="F 容器形态", title="形态①混入非字符串/嵌套项",
         kind="set", contract=["case_id", 123, None, {"x": 1}, True],
         expect="非字符串项被忽略，只有 case_id 生效；不抛异常"),
    dict(id="F7", family="F 容器形态", title="形态④ + 顶层额外键",
         kind="set", contract={"fields": {"title": "string"}, "note": "extra"},
         expect="额外的 note 键被忽略（fields 优先），只有 title 回显"),
    # ---- B 族：边界值 ---------------------------------------------------
    dict(id="B1", family="B 边界值", title="字段名 = 空串",
         kind="set", contract=[""],
         expect="空字段名被跳过；result.json 不应出现空键"),
    dict(id="B2", family="B 边界值", title="空数组（声明 0 个字段）",
         kind="set", contract=[],
         expect="[] 为假值 → main.py 视同「没有契约」，output_contract_applied=False"),
    dict(id="B3", family="B 边界值", title=f"超长字段名（{len(LONG_NAME)} 字符）",
         kind="set", contract=[LONG_NAME],
         expect="要么回显要么报错，但不得静默 + 无诊断"),
    dict(id="B4", family="B 边界值", title="数值声明 {\"n\": 0}",
         kind="set", contract={"n": 0},
         expect="类型值是数字 0（不是类型名）→ 落到默认 \"\"（实测确认）"),
    dict(id="B5", family="B 边界值", title="布尔声明 {\"b\": true}",
         kind="set", contract={"b": True},
         expect="类型值是布尔 → 落到默认 \"\"（实测确认）"),
    dict(id="B6", family="B 边界值", title="非法类型名（数组当类型）{\"x\":[\"array\"]}",
         kind="set", contract={"x": ["array"]},
         expect="非字符串类型 → 默认 \"\"；若静默则点名"),
    dict(id="B7", family="B 边界值", title="未登记的中文类型名 {\"y\":\"数组\"}",
         kind="set", contract={"y": "数组"},
         expect="类型名不在映射表 → 默认 \"\"（测试「四形态+任意类型名」的边界）"),
    dict(id="B8", family="B 边界值", title="列表混入 null",
         kind="set", contract=[None, "case_id"],
         expect="null 被忽略，case_id 仍回显"),
    dict(id="B9", family="B 边界值", title="重复声明同一字段",
         kind="set", contract=["case_id", "case_id"],
         expect="幂等：只有一个 case_id 键，值正确"),
    dict(id="B10", family="B 边界值", title=f"超长取值（title ≈ {len(LONG_TITLE)} 字符）",
         kind="set", contract={"title": "string", "sources": "array"},
         expect="长取值原样回显，result.json 变大但不得截断/丢失"),
    dict(id="B11", family="B 边界值", title="怪键名 {\"a.b/c\":\"string\"}",
         kind="set", contract={"a.b/c": "string"},
         expect="非法标识但合法 JSON 键 → 回显为空串"),
    dict(id="B12", family="B 边界值", title="键与 case.json 已有字段重名（figures）",
         kind="set", contract=["figures"],
         expect="result 顶层被塞进一个 \"\" 的 figures 键（小心：这可能与输入语义冲突）"),
    # ---- A 族：别名与内部瞬态键 ----------------------------------------
    dict(id="A1", family="A 别名", title="20+ 别名一次性回显",
         kind="set", contract=_long_alias_map(),
         expect="全部别名指向真实产物，不得有空串/null"),
    dict(id="A2", family="A 别名", title="声明内部瞬态键 warnings_collected",
         kind="set", contract=["warnings_collected"],
         expect="该键在契约落地后会被 main.py pop 掉 → G2 应当抓到"),
    dict(id="A3", family="A 别名", title="声明内部瞬态键 _pipeline",
         kind="set", contract=["_pipeline"],
         expect="同上（pop 名单：manifest_figures/warnings_collected/adjustments_collected/_pipeline）"),
    dict(id="A4", family="A 别名", title="声明内部瞬态键 manifest_figures",
         kind="set", contract=["manifest_figures"], expect="同上"),
    dict(id="A5", family="A 别名", title="声明内部瞬态键 adjustments_collected",
         kind="set", contract=["adjustments_collected"], expect="同上"),
    dict(id="A6", family="A 别名", title="声明 artifacts_sha256（契约落地前已存在）",
         kind="set", contract=["artifacts_sha256"],
         expect="已存在的真值不得被子默认覆盖 → 回显为真实哈希表"),
    dict(id="A7", family="A 别名", title="声明 output_contract_applied / steps",
         kind="set", contract=["output_contract_applied", "steps"],
         expect="回显为真实布尔值与步骤流水"),
    # ---- D 族：退化与非法形态 -------------------------------------------
    dict(id="D1", family="D 退化形态", title="case.json 里没有 output_contract 键",
         kind="delete", contract=None,
         expect="output_contract_applied=False；契约字段不要求回显（这是合法情形）"),
    dict(id="D2", family="D 退化形态", title="output_contract = null",
         kind="set", contract=None,
         expect="与 D1 等价；应记为未应用"),
    dict(id="D3", family="D 退化形态", title="output_contract = {}（空对象）",
         kind="set", contract={},
         expect="{} 为假值 → 视同没有契约；★ 非法与否需实测"),
    dict(id="D4", family="D 退化形态", title="output_contract = []（空数组）",
         kind="set", contract=[],
         expect="同 B2/D3"),
    dict(id="D5", family="D 退化形态", title="output_contract = true（布尔）",
         kind="set", contract=True,
         expect="真值但非法形态 → ★ 重点看是否静默容忍"),
    dict(id="D6", family="D 退化形态", title="output_contract = \"case_id\"（字符串）",
         kind="set", contract="case_id",
         expect="真值但非法形态 → ★ 重点看是否静默容忍"),
    dict(id="D7", family="D 退化形态", title="output_contract = 0（假值数字）",
         kind="set", contract=0,
         expect="假值 → 视同没有契约"),
    dict(id="D8", family="D 退化形态", title="{\"fields\": \"case_id\"}（fields 是字符串）",
         kind="set", contract={"fields": "case_id"},
         expect="非法 → ★ 看是否有诊断"),
    dict(id="D9", family="D 退化形态", title="{\"fields\": {}}（空映射）",
         kind="set", contract={"fields": {}},
         expect="真值但声明 0 字段 → applied=True 且什么都不回显"),
    dict(id="D10", family="D 退化形态", title="{\"fields\": []}（空列表）",
         kind="set", contract={"fields": []}, expect="同 D9"),
    dict(id="D11", family="D 退化形态", title="深嵌套 {\"fields\":{\"a\":{\"b\":{\"c\":\"array\"}}}}",
         kind="set", contract={"fields": {"a": {"b": {"c": "array"}}}},
         expect="只取第一层键 a；a 的类型值是对象 → 默认 \"\""),
    dict(id="D12", family="D 退化形态", title="output_contract = 3.14（浮点）",
         kind="set", contract=3.14, expect="真值但非法形态 → ★ 重点看是否静默容忍"),
]


# ---------------------------------------------------------------- 工具

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(65536), b""):
            h.update(c)
    return h.hexdigest()


def contract_fields(contract, drop_empty=False):
    """四形态解析（独立重写一遍以免与包内脚本耦合）。

    `drop_empty=False` = **校验器口径**（figcheck.py 的 `_contract_fields` 与
    check_contract.py 的 `contract_fields` 都只过滤非字符串，**不过滤空串**）；
    `drop_empty=True` = **main.py 口径**（`apply_output_contract` 里有
    `if not f: continue`，会跳过空字段名）。两者口径不同 ⇒ 空字段名会成为
    「main 不写、校验器却要求」的缺口，本台子把这种不一致单独点名。
    """
    if isinstance(contract, list):
        return [f for f in contract if isinstance(f, str) and (f or not drop_empty)]
    if isinstance(contract, dict):
        inner = contract.get("fields", contract)
        if isinstance(inner, list):
            return [f for f in inner if isinstance(f, str) and (f or not drop_empty)]
        if isinstance(inner, dict):
            return [k for k in inner.keys() if isinstance(k, str) and (k or not drop_empty)]
    return []


def shape_legal(contract, kind):
    """是否属于契约文档 §2 登记的四形态之一。"""
    if kind == "delete" or contract is None:
        return False
    if isinstance(contract, list):
        return all(isinstance(x, str) for x in contract)
    if isinstance(contract, dict):
        if "fields" not in contract:
            return all(isinstance(v, str) for v in contract.values())
        inner = contract["fields"]
        if isinstance(inner, list):
            return all(isinstance(x, str) for x in inner)
        if isinstance(inner, dict):
            # 形态④要求**类型名是字符串**；写成 {"type":"array"} 这类嵌套对象不在
            # 文档登记的四种形态内 ⇒ 记为非法形态（实测会被静默降级为 ""）。
            return all(isinstance(v, str) for v in inner.values())
        return False
    return False


def redact_residual_abs(obj):
    if isinstance(obj, dict):
        return {k: redact_residual_abs(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact_residual_abs(v) for v in obj]
    if isinstance(obj, str):
        if obj.startswith("<"):
            return obj
        for rx in (_ABS_WIN, _ABS_POSIX):
            obj = rx.sub("<ABS>", obj)
        return obj
    return obj


def redact(obj, mapping):
    if isinstance(obj, dict):
        return {k: redact(v, mapping) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact(v, mapping) for v in obj]
    if isinstance(obj, str):
        for root, ph in sorted(mapping, key=lambda x: -len(x[0] or "")):
            if not root:
                continue
            for variant in (root, root.replace("\\", "/"), root.replace("/", "\\")):
                if variant and variant in obj:
                    obj = obj.replace(variant, ph)
        return obj
    return obj


def _within(child, parent):
    """child 是否等于 parent 或落在 parent 之内（规范化大小写，Windows 下大小写不敏感）。"""
    c = os.path.normcase(os.path.abspath(child))
    q = os.path.normcase(os.path.abspath(parent))
    return c == q or c.startswith(q + os.sep)


def copy_case_dir(src_dir: str, dst_dir: str):
    os.makedirs(dst_dir, exist_ok=True)
    for name in sorted(os.listdir(src_dir)):
        if name in _COPY_SKIP_DIRS:
            continue
        s, d = os.path.join(src_dir, name), os.path.join(dst_dir, name)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns(*_COPY_SKIP_DIRS))
        else:
            shutil.copy2(s, d)


def run_cmd(argv, cwd, timeout, env=None):
    t0 = time.time()
    try:
        p = subprocess.run(argv, cwd=cwd, timeout=timeout, env=env,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return {"exit": p.returncode, "stdout": p.stdout.decode("utf-8", "replace"),
                "stderr": p.stderr.decode("utf-8", "replace"),
                "seconds": round(time.time() - t0, 3)}
    except subprocess.TimeoutExpired:
        return {"exit": -1, "stdout": "", "stderr": f"timeout after {timeout}s",
                "seconds": round(time.time() - t0, 3)}


# ---------------------------------------------------------------- 单行执行

def run_row(row, base_case_path, workspace, timeout, cross=True):
    rec = {"id": row["id"], "family": row["family"], "title": row["title"],
           "expect": row["expect"], "kind": row["kind"],
           "injected_contract": row["contract"] if row["kind"] == "set" else "<deleted>",
           "shape_legal": shape_legal(row["contract"], row["kind"]),
           "declared_validators": contract_fields(row["contract"]),
           "declared_main": contract_fields(row["contract"], drop_empty=True),
           "declared_n": 0, "verdict": None, "silent_kind": None,
           "note_kind": None, "errors": []}

    row_dir = os.path.join(workspace, row["id"])
    if os.path.isdir(row_dir):
        shutil.rmtree(row_dir, ignore_errors=True)
    copy_case_dir(os.path.dirname(base_case_path), row_dir)
    case_path = os.path.join(row_dir, os.path.basename(base_case_path))
    try:
        with open(case_path, "r", encoding="utf-8-sig") as f:
            case = json.load(f)
    except Exception as exc:
        rec["errors"].append(f"基准案例不可解析：{exc}")
        rec["verdict"] = "run_error"
        return rec
    if not isinstance(case, dict):
        rec["errors"].append("基准案例顶层不是对象")
        rec["verdict"] = "run_error"
        return rec
    if row["kind"] == "delete":
        case.pop("output_contract", None)
    else:
        case["output_contract"] = row["contract"]
    if row["id"] == "B10":
        case["title"] = LONG_TITLE
    with open(case_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(case, f, ensure_ascii=False, indent=2)
    rec["declared"] = rec["declared_validators"]
    rec["declared_n"] = len(rec["declared_validators"])
    rec["parser_disagreement"] = (rec["declared_validators"] != rec["declared_main"])
    rec["contract_falsy"] = not bool(row["contract"]) if row["kind"] == "set" else True
    rec["contract_absent"] = (row["kind"] == "delete" or row["contract"] is None)

    out_dir, work_dir = os.path.join(row_dir, "out"), os.path.join(row_dir, "work")
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(work_dir, exist_ok=True)
    # cwd 故意用 workspace（不是技能根）：顺带验证脚本自定位
    m = run_cmd([sys.executable, MAIN_PY, "--case", case_path, "--out", out_dir,
                 "--work", work_dir], workspace, timeout)
    rec["main_exit"] = m["exit"]
    rec["main_seconds"] = m["seconds"]
    if m["exit"] not in (0, 1, 2) or "Traceback" in m["stderr"]:
        rec["main_stderr_tail"] = "\n".join(m["stderr"].splitlines()[-3:])

    rp = os.path.join(out_dir, "result.json")
    rec["result_json_present"] = os.path.exists(rp)
    if not rec["result_json_present"]:
        rec["verdict"] = "run_error"
        rec["errors"].append("main.py 未产出 result.json")
        return rec
    with open(rp, "r", encoding="utf-8-sig") as f:
        res = json.load(f)
    rec["result_json_keys"] = len(res)
    rec["result_json_bytes"] = os.path.getsize(rp)
    rec["main_status"] = res.get("status")
    rec["output_contract_applied"] = res.get("output_contract_applied")
    rec["gates_all_pass"] = bool((res.get("gates") or {}).get("all_pass"))
    rec["echo_present"] = [f for f in rec["declared_validators"] if f in res]
    rec["echo_null"] = [f for f in rec["declared_validators"] if f in res and res[f] is None]
    rec["echo_missing"] = [f for f in rec["declared_validators"] if f not in res]
    rec["violations"] = sorted(set(rec["echo_missing"]) | set(rec["echo_null"]))
    rec["applied_empty"] = bool(rec["output_contract_applied"]) and not rec["declared_main"]
    # 容器类型是否符合声明（只对 {name:type} 形态有效）
    tmap = {}
    if isinstance(row["contract"], dict) and "fields" not in row["contract"]:
        tmap = {k: v for k, v in row["contract"].items() if isinstance(v, str)}
    elif isinstance(row["contract"], dict) and isinstance(row["contract"].get("fields"), dict):
        tmap = {k: v for k, v in row["contract"]["fields"].items() if isinstance(v, str)}
    want = {"array": list, "list": list, "object": dict, "dict": dict,
            "number": (int, float), "float": (int, float), "int": int,
            "boolean": bool, "bool": bool, "string": str, "text": str, "str": str}
    tm = []
    for k, t in tmap.items():
        if k in res and t in want and not isinstance(res[k], want[t]):
            tm.append({"field": k, "declared": t, "actual": type(res[k]).__name__})
    rec["type_mismatches"] = tm
    unc = res.get("uncertainty") or []
    rec["uncertainty_mentions_contract"] = [u for u in unc
                                           if "契约" in str(u) or "contract" in str(u).lower()]

    if cross:
        fc = run_cmd([sys.executable, FIGCHECK_PY, "--dir", out_dir, "--case", case_path,
                      "--json"], workspace, timeout)
        rec["figcheck_exit"] = fc["exit"]
        try:
            fj = json.loads(fc["stdout"])
            rec["figcheck_gates"] = fj.get("gates")
            rec["figcheck_g2"] = (fj.get("gates") or {}).get("G2")
            rec["figcheck_all_pass"] = fj.get("all_pass")
        except Exception:
            rec["figcheck_gates"] = None
            rec["figcheck_g2"] = None
        cc = run_cmd([sys.executable, CHECK_CONTRACT_PY, "--result", rp, "--case", case_path,
                      "--json"], workspace, timeout)
        rec["check_contract_exit"] = cc["exit"]
        try:
            cj = json.loads(cc["stdout"])
            rec["check_contract_all_pass"] = cj.get("all_pass")
            rec["check_contract_contract_missing"] = cj.get("contract_missing")
        except Exception:
            rec["check_contract_all_pass"] = None
            rec["check_contract_contract_missing"] = None

    # ---- verdict ----
    # 先判「这一行到底有没有声明契约」：缺键 / null / 假值 / 声明 0 个字段 =>
    # 没有任何东西需要回显，属合法情形（不得计入静默通过，否则报告会注水）。
    no_decl = (rec["contract_absent"] or rec["contract_falsy"]
               or (not rec["declared_main"] and rec["shape_legal"]
                   and not rec["violations"]))
    if rec["contract_absent"]:
        rec["note_kind"] = "absent"
    elif rec["contract_falsy"]:
        rec["note_kind"] = "falsy_value"
    elif no_decl:
        rec["note_kind"] = "zero_field_declaration"

    gap = False
    if rec["violations"]:
        gap = True
    if not rec["shape_legal"] and not no_decl:
        gap = True
    if tm:
        gap = True

    caught = (m["exit"] != 0 or res.get("status") != "completed"
              or rec.get("figcheck_exit") not in (0, None)
              or rec.get("check_contract_exit") not in (0, None)
              or bool(rec["uncertainty_mentions_contract"]))

    if no_decl and not rec["violations"]:
        rec["verdict"] = "no_contract"
    elif not gap:
        rec["verdict"] = "echo_complete"
    elif caught:
        rec["verdict"] = "caught"
        if rec["violations"] and not rec["shape_legal"]:
            rec["silent_kind"] = "boundary_degraded"
    else:
        rec["verdict"] = "silent_pass"
        if not rec["shape_legal"]:
            rec["silent_kind"] = "illegal_shape_applied_true" if rec["applied_empty"]                 else "illegal_shape_tolerated"
        elif rec["violations"]:
            rec["silent_kind"] = "field_vanished"
        elif tm:
            rec["silent_kind"] = "type_mismatch"
        else:
            rec["silent_kind"] = "boundary_degraded"
    return rec


# ---------------------------------------------------------------- 主流程

def build_report(rows, base_case_path, workspace, timeout, cross=True, quiet=False):
    report = {
        "tool": "contract_matrix.py",
        "axis": "v8 / 契约四形态 × 边界值矩阵",
        "version": 1,
        "case": os.path.abspath(base_case_path),
        "workspace": os.path.abspath(workspace),
        "main": MAIN_PY,
        "cross_validators": bool(cross),
        "rows": [],
        "verdict_counts": {},
        "silent_pass": [],
        "caught": [],
        "echo_complete": [],
        "run_error": [],
        "uncovered": [
            "真实平台案例的 output_contract 具体字段（未知，本台子用自造字段 + 别名集合覆盖）",
            "契约字段**取值语义**是否正确（本台子只判存在性/容器类型/是否 null，不判数值科学含义）",
            "契约声明的嵌套结构深度 > 2 的语义（本台子只测到 D11 的两层）",
            "跨平台换行/编码（CRLF vs LF）对契约回显的影响",
            "并发/重入场景下 apply_output_contract 的行为",
        ],
        "findings": [],
    }
    t0 = time.time()
    for row in rows:
        rec = run_row(row, base_case_path, workspace, timeout, cross=cross)
        report["rows"].append(rec)
        if not quiet:
            print(f"[contract_matrix] {rec['id']:<4} {rec['verdict']:<14} "
                  f"declared={rec['declared_n']:<3} main_exit={rec.get('main_exit')} "
                  f"status={rec.get('main_status')} G2={rec.get('figcheck_g2')} "
                  f"cc_exit={rec.get('check_contract_exit')}")
    counts = {}
    for r in report["rows"]:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
        if r["verdict"] == "silent_pass":
            report["silent_pass"].append(r["id"])
        elif r["verdict"] == "caught":
            report["caught"].append(r["id"])
        elif r["verdict"] == "echo_complete":
            report["echo_complete"].append(r["id"])
        elif r["verdict"] == "run_error":
            report["run_error"].append(r["id"])
    report["verdict_counts"] = counts
    report["rows_total"] = len(report["rows"])
    report["elapsed_seconds"] = round(time.time() - t0, 3)
    h = hashlib.sha256()
    for r in sorted(report["rows"], key=lambda x: x["id"]):
        h.update(r["id"].encode())
        h.update(json.dumps(r["injected_contract"], ensure_ascii=False,
                            sort_keys=True).encode())
    report["matrix_digest"] = h.hexdigest()

    f = report["findings"]
    f.append(f"共 {report['rows_total']} 行：{counts}")
    f.append("静默通过（一路绿灯但存在缺口）：" + (", ".join(report["silent_pass"]) or "无"))
    f.append("静默通过的分型：" + json.dumps(
        {r["id"]: r["silent_kind"] for r in report["rows"] if r["verdict"] == "silent_pass"},
        ensure_ascii=False) if report["silent_pass"] else "静默通过的分型：无")
    f.append("★ `output_contract_applied=true` 但一个声明字段都没回显的行（该标志不可当"
             "契约完整性用）：" + (", ".join(r["id"] for r in report["rows"]
                                          if r.get("applied_empty")) or "无"))
    illegal_kept = [r["id"] for r in report["rows"]
                    if not r["shape_legal"] and r["verdict"] in ("silent_pass", "echo_complete")]
    f.append("契约形态非法却未触发任何红黄灯的行：" + (", ".join(illegal_kept) or "无"))
    f.append("main.py 与校验器对声明字段口径不一致的行：" +
             (", ".join(r["id"] for r in report["rows"] if r.get("parser_disagreement")) or "无"))
    popped = [r["id"] for r in report["rows"]
              if r["declared_n"] and r["echo_missing"]]
    f.append("声明字段在最终 result.json 里消失的行：" + (", ".join(popped) or "无"))
    tm = [r["id"] for r in report["rows"] if r.get("type_mismatches")]
    f.append("声明容器类型与实际值类型不符的行：" + (", ".join(tm) or "无"))
    return report


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(
        description="契约四形态 × 边界值矩阵实测台（真的注入、真的跑主流程）")
    ap.add_argument("--case", default=DEFAULT_CASE, help="基准案例 JSON")
    ap.add_argument("--workspace", default=None, help="包外工作目录")
    ap.add_argument("--out", default=None, help="报告路径")
    ap.add_argument("--only", default=None, help="只跑这些编号（逗号分隔）")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--keep", action="store_true", help="保留每行的隔离副本")
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--no-cross", action="store_true", help="跳过 figcheck/check_contract")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    if not os.path.exists(args.case):
        print(f"[contract_matrix] 基准案例不存在：{args.case}", file=sys.stderr)
        return 1
    rows = ROWS
    if args.only:
        want = {x.strip().upper() for x in args.only.split(",") if x.strip()}
        rows = [r for r in ROWS if r["id"].upper() in want]
        if not rows:
            print(f"[contract_matrix] --only 没有匹配任何行：{args.only}", file=sys.stderr)
            return 1
    workspace = os.path.abspath(args.workspace or tempfile.mkdtemp(prefix="contract-matrix-"))
    # 防呆：workspace 落在案例目录内时，每行的"整目录复制"会把案例目录复制进它自己的
    # 子目录（失控）。直接拒绝并给出可执行的修法。
    if _within(workspace, os.path.dirname(os.path.abspath(args.case))):
        print("[contract_matrix] --workspace 不能落在案例目录内部：会把案例目录复制进"
              "自己的子目录。请指到别处。", file=sys.stderr)
        return 1
    os.makedirs(workspace, exist_ok=True)
    try:
        report = build_report(rows, os.path.abspath(args.case), workspace,
                              args.timeout, cross=not args.no_cross, quiet=args.quiet)
    except Exception as exc:
        print(f"[contract_matrix] FATAL {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    mapping = [(workspace, "<WORKSPACE>"), (os.path.dirname(os.path.abspath(args.case)), "<CASEDIR>"),
               (PKG_ROOT, "<SKILL_DIR>"), (tempfile.gettempdir(), "<TMP>"),
               (sys.executable, "<PYTHON>")]
    payload = redact_residual_abs(redact(report, mapping))
    out = args.out or os.path.join(workspace, "contract_matrix_report.json")
    try:
        with open(out, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
    except Exception as exc:
        print(f"[contract_matrix] 报告写不出：{exc}", file=sys.stderr)
        return 1
    if not args.keep:
        for r in rows:
            shutil.rmtree(os.path.join(workspace, r["id"]), ignore_errors=True)

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"[contract_matrix] 行数={report['rows_total']} 判定={report['verdict_counts']}")
        print(f"[contract_matrix] 静默通过={report['silent_pass'] or '无'}")
        print(f"[contract_matrix] 报告 -> {out}")
    return 2 if report["silent_pass"] else 0


if __name__ == "__main__":
    sys.exit(main())
