#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Standalone contract validator for result.json.

Checks a produced result.json against references/OUTPUT_CONTRACT.md:

* required top-level keys exist with non-degenerate values,
* case_id is present,
* every listed artifact file actually exists under the output directory,
* status is one of success / partial / failed,
* verification.checks carries the check summary,
* sources / uncertainty / change_records are present and well-typed.

Exit codes: 0 = valid, 1 = invalid, 2 = usage error.
"""

import argparse
import json
import os
import sys

REQUIRED = [
    "case_id", "skill", "status", "workorder", "figure_type", "title",
    "main_result", "artifacts", "evidence", "legend_mapping",
    "data_mapping", "verification", "sources", "uncertainty",
    "change_records", "generated_at", "tool_versions",
]

# Keys that must exist AND carry a non-degenerate value (the core result).
NONEMPTY = [
    "case_id", "status", "main_result", "artifacts", "evidence",
    "verification", "generated_at", "tool_versions",
]

# Keys that legitimately stay empty (e.g. no edits were requested, no
# uncertainty was encountered) — presence is enough.
EMPTY_OK = {"sources", "uncertainty", "change_records", "legend_mapping",
            "data_mapping", "title"}

STATUSES = ("success", "partial", "failed")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case", help="path to the original case.json "
                                   "(optional)")
    ap.add_argument("--result", required=True,
                    help="path to the produced result.json")
    ap.add_argument("--out", help="output directory containing the "
                                  "artifacts (default: dirname of "
                                  "--result)")
    args = ap.parse_args(argv)

    result_path = os.path.abspath(args.result)
    if not os.path.isfile(result_path):
        print("INVALID: result.json not found: %s" % result_path)
        return 1
    with open(result_path, "r", encoding="utf-8") as fh:
        result = json.load(fh)

    errors = []
    for key in REQUIRED:
        if key not in result:
            errors.append("missing required key: %s" % key)
        elif key in NONEMPTY and result[key] in (None, "", []):
            errors.append("required key %s is empty/degenerate" % key)

    if not result.get("case_id"):
        errors.append("case_id missing or empty")

    status = result.get("status")
    if status and status not in STATUSES:
        errors.append("invalid status %r (allowed: %s)"
                      % (status, ", ".join(STATUSES)))

    artifacts = result.get("artifacts")
    out_dir = os.path.abspath(args.out or os.path.dirname(result_path))
    if isinstance(artifacts, list):
        for art in artifacts:
            if not isinstance(art, dict):
                errors.append("artifact entry is not an object")
                continue
            rel = art.get("path")
            if not rel:
                errors.append("artifact without path: %r" % art)
                continue
            apath = rel if os.path.isabs(rel) else os.path.join(out_dir, rel)
            if not os.path.isfile(apath):
                errors.append("artifact file missing: %s" % rel)
    else:
        errors.append("artifacts is not a list")

    if not isinstance(result.get("evidence"), dict):
        errors.append("evidence is not an object")
    if not isinstance(result.get("uncertainty"), list):
        errors.append("uncertainty is not a list")
    if not isinstance(result.get("change_records"), list):
        errors.append("change_records is not a list")
    if not isinstance(result.get("sources"), list):
        errors.append("sources is not a list")
    vf = result.get("verification")
    if not isinstance(vf, dict) or "checks" not in vf:
        errors.append("verification.checks missing")

    if args.case:
        case_path = os.path.abspath(args.case)
        if not os.path.isfile(case_path):
            errors.append("--case file not found: %s" % case_path)
        else:
            with open(case_path, "r", encoding="utf-8") as fh:
                case = json.load(fh)
            cid = case.get("case_id") or case.get("id")
            if cid and result.get("case_id") != str(cid):
                errors.append("case_id mismatch: case=%r result=%r"
                              % (cid, result.get("case_id")))

    if errors:
        print("INVALID (%d problems):" % len(errors))
        for e in errors:
            print("  - " + e)
        return 1
    print("VALID: result.json at %s satisfies OUTPUT_CONTRACT (required "
          "keys present, artifacts exist, statuses coherent)."
          % result_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())