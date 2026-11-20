# -*- coding: utf-8 -*-
"""validate_result.py — check result.json against OUTPUT_CONTRACT.

Exits 0 with VALID when all required fields exist (including the
output_contract echo), otherwise exits 1 and prints the missing fields.
Run it on the real output, e.g.:
  python scripts/validate_result.py --case /input/case.json --result /app/output/result.json
"""
from __future__ import annotations

import json
import os
import sys
from common import utf8_writer

REQUIRED = [
    "case_id", "skill", "status", "workorder", "title", "slide_count",
    "main_result", "artifacts", "slide_evidence", "template_audit",
    "verification", "sources", "uncertainty", "change_records",
    "status_notes", "generated_at", "generator", "tool_versions",
]
STATUS_OK = ("success", "partial", "failed")


def validate(case_path: str, result_path: str | None = None, result: dict | None = None,
             verbose: bool = True) -> tuple:
    if result is None:
        if not result_path:
            raise ValueError("either result_path or result dict required")
        result = json.load(open(result_path, "r", encoding="utf-8-sig"))
    problems = []
    for f in REQUIRED:
        if f not in result:
            problems.append(f"missing required field: {f}")
    if result.get("status") not in STATUS_OK:
        problems.append(f"invalid status: {result.get('status')!r}")
    if not result.get("case_id"):
        problems.append("case_id empty")
    if not isinstance(result.get("slide_evidence"), list):
        problems.append("slide_evidence must be a list")
    if not isinstance(result.get("artifacts"), list):
        problems.append("artifacts must be a list")
    if not isinstance(result.get("uncertainty"), list):
        problems.append("uncertainty must be a list")
    if not isinstance(result.get("change_records"), list):
        problems.append("change_records must be a list")

    # output_contract echo: every key of case output_contract present at top
    if case_path and os.path.exists(case_path):
        case = json.load(open(case_path, "r", encoding="utf-8-sig"))
        contract = case.get("output_contract") or {}
        for key in contract:
            if key not in result:
                problems.append(f"output_contract key not echoed at top level: {key}")

    ok = not problems
    if verbose:
        print("VALID - result.json conforms to OUTPUT_CONTRACT" if ok
              else "INVALID:\n  " + "\n  ".join(problems))
    return ok, problems


def main(argv=None):
    utf8_writer()
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case", default="", help="case.json (to check contract echo); optional")
    ap.add_argument("--result", required=True, help="path to result.json")
    a = ap.parse_args(argv)
    ok, problems = validate(a.case, a.result)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())