#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_contract.py — result.json 契约覆盖自查（交付前最后一道门）

职责
----
把「result.json 顶层是否覆盖 references/OUTPUT_CONTRACT.md 声明的全部字段」变成
**一条可复跑的命令**，避免人工目检漏字段。三个判定：

1. **必备字段**：`references/OUTPUT_CONTRACT.md` 中 `REQUIRED-FIELDS` 机器可读块
   列出的字段必须全部出现在 result.json 顶层。
2. **案件契约**：给了 `--case` 时，case.json 的 `output_contract`（四形态任一）
   声明的字段必须全部出现且非 null（契约回显，见 OUTPUT_CONTRACT §2）。
3. **诚实状态**：`status=failed` 时按契约允许的最小信封判定（`case_id`/`status`/
   `uncertainty`/`sources`/`change_records`），其余字段降级为 warn —— 失败时
   不要求把没算出来的字段编出来。

退出码：0 = 覆盖完整；1 = 有缺失或为 null；2 = 用法/文件错误。

用法（任意 cwd，脚本自定位契约路径）：
    python <skill_root>/scripts/check_contract.py --result <out>/result.json
    python <skill_root>/scripts/check_contract.py --result <out>/result.json \
           --case <case.json> [--json]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(HERE)
DEFAULT_CONTRACT = os.path.join(SKILL_ROOT, "references", "OUTPUT_CONTRACT.md")

REQ_BEGIN = "<!-- REQUIRED-FIELDS:BEGIN -->"
REQ_END = "<!-- REQUIRED-FIELDS:END -->"
# status=failed 时契约允许的最小信封（其余字段降级为 warn）
FAILED_ENVELOPE = ["case_id", "status", "uncertainty", "sources", "change_records"]


def parse_fields(path, begin, end):
    """从契约文档的标记块里取出字段清单（每行一个字段名；# 开头为注释）。"""
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    fields, inside = [], False
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if line == begin:
                inside = True
                continue
            if line == end:
                inside = False
                continue
            if inside and line and not line.startswith("#"):
                fields.append(line.strip("`-* "))
    if not fields:
        raise ValueError(f"契约文档缺少机器可读字段块（{begin} … {end}）：{path}")
    return fields


def contract_fields(case):
    """把 case.json 的 output_contract 归一化成字段名列表（四形态兼容）。"""
    c = case.get("output_contract")
    if not c:
        return []
    if isinstance(c, list):
        return [f for f in c if isinstance(f, str)]
    if isinstance(c, dict):
        inner = c.get("fields", c)
        if isinstance(inner, list):
            return [f for f in inner if isinstance(f, str)]
        if isinstance(inner, dict):
            return list(inner.keys())
    return []


def main(argv=None):
    ap = argparse.ArgumentParser(description="result.json 契约覆盖自查")
    ap.add_argument("--result", required=True, help="result.json 路径")
    ap.add_argument("--case", default=None, help="case.json（校验其 output_contract 回显）")
    ap.add_argument("--contract", default=DEFAULT_CONTRACT, help="契约文档路径")
    ap.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    args = ap.parse_args(argv)

    try:
        required = parse_fields(args.contract, REQ_BEGIN, REQ_END)
    except Exception as exc:
        print(f"[check_contract] FATAL 读取契约失败：{exc}", file=sys.stderr)
        return 2
    try:
        with open(args.result, "r", encoding="utf-8-sig") as f:
            res = json.load(f)
    except Exception as exc:
        print(f"[check_contract] FATAL 读取 result.json 失败：{exc}", file=sys.stderr)
        return 2
    if not isinstance(res, dict):
        print("[check_contract] FATAL result.json 顶层不是对象", file=sys.stderr)
        return 2

    case_fields = []
    if args.case:
        try:
            with open(args.case, "r", encoding="utf-8-sig") as f:
                case = json.load(f)
            if isinstance(case, list):
                case = case[0]
            elif isinstance(case, dict) and isinstance(case.get("cases"), list) and case["cases"]:
                case = case["cases"][0]
            case_fields = contract_fields(case or {})
        except Exception as exc:
            print(f"[check_contract] FATAL 读取 case.json 失败：{exc}", file=sys.stderr)
            return 2

    status = str(res.get("status") or "")
    judged = required
    degraded = []
    if status == "failed":
        degraded = [f for f in required if f not in FAILED_ENVELOPE]
        judged = [f for f in required if f in FAILED_ENVELOPE]

    report = {"result": os.path.abspath(args.result), "status": status,
              "required": required, "judged": judged, "missing": [], "nulls": [],
              "degraded_for_failed": degraded, "contract_fields": case_fields,
              "contract_missing": [], "all_pass": True}

    report["missing"] = [f for f in judged if f not in res]
    report["nulls"] = [f for f in judged if f in res and res[f] is None]
    report["contract_missing"] = [f for f in case_fields
                                  if f not in res or res[f] is None]
    report["all_pass"] = not (report["missing"] or report["nulls"]
                              or report["contract_missing"])

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"[check_contract] result={args.result}")
        print(f"[check_contract] status={status or '(缺失)'} 顶层字段={len(res)} "
              f"契约文档={os.path.relpath(os.path.abspath(args.contract), SKILL_ROOT)}")
        for f in required:
            if f in degraded:
                tag = "SKIP(失败信封)"
            elif f in report["missing"]:
                tag = "MISSING"
            elif f in report["nulls"]:
                tag = "NULL"
            else:
                tag = "OK"
            print(f"   [{tag:>12s}] {f}")
        if case_fields:
            print("[check_contract] case.json output_contract 回显：")
            for f in case_fields:
                tag = "MISSING" if f in report["contract_missing"] else "OK"
                print(f"   [{tag:>12s}] {f}")
        print(f"[check_contract] SUMMARY: {'PASS' if report['all_pass'] else 'FAIL'} "
              f"(required={len(judged)} missing={len(report['missing'])} "
              f"null={len(report['nulls'])} contract_missing={len(report['contract_missing'])})")
    return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
