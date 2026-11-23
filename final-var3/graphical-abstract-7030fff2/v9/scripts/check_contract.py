# -*- coding: utf-8 -*-
"""check_contract.py — 校验 result.json 是否覆盖输出契约（独立自查工具）。

Part of the "graphical-abstract" Skill v2 (graphical-abstract-7030fff2, efficiency-3).

判据（与 ``references/OUTPUT_CONTRACT.md`` §2–§3 和 ``references/failure-modes.md`` §5 一致）：

1. **信封 18 键齐全**：result.json 顶层必须含
   schema_version / skill / case_id / status / summary / task / deliverables /
   content_summary / provenance / sources / uncertainty / warnings / change_records /
   audit / generated_utc / output_contract_echo / plan / spec_lint；
2. **案例契约字段全覆盖**：`case.json` 的 ``output_contract`` 每个字段必须能在
   result.json 顶层（或冲突时的 ``output_contract_echo``）找到；
3. **禁止 null**（契约四形态）：契约字段的值不得为 ``null``；缺失时应按类型给
   ``""`` / ``[]`` / ``false`` / ``{}``；
4. **硬性门抽检**：`case_id` 非空（G1）、`status` ∈ {success, partial, failed}（G3）、
   `deliverables` 非空、`sources` 非空（G8）、`audit` 为对象。

用法：
    python check_contract.py --result <out>/result.json [--case <case.json>]

退出码：0 = 全部通过；1 = 有缺口（逐条打印）；2 = 用法/文件错误。
本工具只读，不修改任何产物。
"""
from __future__ import annotations

import argparse
import json
import os
import sys

ENVELOPE_KEYS = [
    "schema_version", "skill", "case_id", "status", "summary", "task",
    "deliverables", "content_summary", "provenance", "sources", "uncertainty",
    "warnings", "change_records", "audit", "generated_utc",
    "output_contract_echo", "plan", "spec_lint",
]
VALID_STATUS = ("success", "partial", "failed")


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def check(result: dict, case: dict | None = None) -> dict:
    """Return {"valid": bool, "problems": [...], "checked": {...}}."""
    problems = []
    result = result or {}

    # 1. envelope keys -------------------------------------------------------
    missing_env = [k for k in ENVELOPE_KEYS if k not in result]
    if missing_env:
        problems.append("envelope keys missing: " + ", ".join(missing_env))

    # 2. case output_contract coverage ---------------------------------------
    contract = {}
    if isinstance(case, dict):
        c = case.get("output_contract")
        contract = c if isinstance(c, dict) else {}
    echo = result.get("output_contract_echo")
    echo = echo if isinstance(echo, dict) else {}
    covered, via_echo, absent, nulled = [], [], [], []
    for k, v in contract.items():
        if k in result and result[k] is not None:
            covered.append(k)
            if k in echo:
                via_echo.append(k)
        elif k in echo and echo[k] is not None:
            via_echo.append(k)
        elif k in result or k in echo:
            nulled.append(k)
        else:
            absent.append(k)
    if absent:
        problems.append("case output_contract fields absent from result.json: "
                        + ", ".join(sorted(absent)))
    if nulled:
        problems.append("case output_contract fields present but null (must be "
                        '"" / [] / false / {}): ' + ", ".join(sorted(nulled)))

    # 3. hard gates (G1/G3/G8 + structure) ------------------------------------
    if not str(result.get("case_id") or "").strip():
        problems.append("G1: case_id is empty")
    if result.get("status") not in VALID_STATUS:
        problems.append("G3: status %r not in %s" % (result.get("status"), list(VALID_STATUS)))
    if not isinstance(result.get("deliverables"), list) or not result.get("deliverables"):
        problems.append("deliverables missing or empty")
    if not isinstance(result.get("sources"), list) or not result.get("sources"):
        problems.append("G8: sources missing or empty (needs >=1 source with sha256)")
    if not isinstance(result.get("audit"), dict):
        problems.append("audit missing or not an object")

    return {
        "valid": not problems,
        "problems": problems,
        "checked": {
            "envelope_keys": len(ENVELOPE_KEYS),
            "envelope_missing": missing_env,
            "contract_fields": len(contract),
            "contract_covered_top_level": sorted(covered),
            "contract_via_echo": sorted(set(via_echo)),
            "contract_absent": sorted(absent),
            "contract_null": sorted(nulled),
            "status": result.get("status"),
            "deliverables": len(result.get("deliverables") or []),
            "sources": len(result.get("sources") or []),
        },
    }


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass
    ap = argparse.ArgumentParser(
        prog="check_contract",
        description="verify result.json covers the output contract (envelope + case contract)")
    ap.add_argument("--result", required=True, help="path to result.json")
    ap.add_argument("--case", default=None,
                    help="path to case.json (optional; enables output_contract coverage check)")
    args = ap.parse_args(argv)

    if not os.path.isfile(args.result):
        print(json.dumps({"valid": False,
                          "problems": ["result.json not found: %s" % args.result]},
                         ensure_ascii=False, indent=2))
        return 2
    case = None
    if args.case:
        if not os.path.isfile(args.case):
            print(json.dumps({"valid": False,
                              "problems": ["case.json not found: %s" % args.case]},
                             ensure_ascii=False, indent=2))
            return 2
        case = load_json(args.case)
    rep = check(load_json(args.result), case)
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    return 0 if rep["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
