# -*- coding: utf-8 -*-
"""check_contract.py — verify a result.json covers EVERY top-level field that
references/OUTPUT_CONTRACT.md section 1 declares.

Part of the "paper-to-academic-ppt" Skill (ppt-c7b80f0d, efficiency-3).

Why this exists
---------------
The runtime contract says the produced result.json must carry all
output_contract fields. Self-narration cannot prove that, so the field list is
kept in ONE place (the contract document) and this checker reads that document
and compares it against the produced JSON. Missing fields are hard failures;
present-but-null fields are reported as warnings because a few of them (deck,
evidence_map_json) are legitimately null when the material was unreadable.

Usage
-----
    python check_contract.py --result <out>/result.json \\
        --contract references/OUTPUT_CONTRACT.md [--case /input/case.json] [--quiet]

Exit codes: 0 = all contracted fields present; 1 = fields missing; 2 = usage /
contract not parseable (never silently "passes").
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

SECTION = "## 1."
STOP = "## 2."
ROW_RE = re.compile(r"^\|\s*`([A-Za-z_][A-Za-z0-9_]*)`\s*\|")


def fields_from_contract(contract_path):
    """Extract the top-level field names listed in section 1 of the contract."""
    with open(contract_path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    inside = False
    names = []
    for ln in lines:
        if ln.startswith(SECTION):
            inside = True
            continue
        if inside and ln.startswith(STOP):
            break
        if inside:
            m = ROW_RE.match(ln)
            if m:
                names.append(m.group(1))
    # keep document order, drop duplicates
    seen, out = set(), []
    for n in names:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


def check(result, fields):
    missing = [f for f in fields if f not in result]
    nulls = [f for f in fields if f in result and result[f] is None]
    return missing, nulls


def main(argv=None):
    import cli_io
    cli_io.harden_console()
    ap = argparse.ArgumentParser(description="check result.json against OUTPUT_CONTRACT.md")
    ap.add_argument("--result", required=True)
    ap.add_argument("--contract", required=True)
    ap.add_argument("--case", default=None,
                    help="optional case.json: also require every declared "
                         "output_contract field at top level")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    if not os.path.isfile(args.contract):
        print(json.dumps({"valid": False, "error": "contract not found: %s" % args.contract},
                         ensure_ascii=False, indent=2))
        return 2
    fields = fields_from_contract(args.contract)
    if not fields:
        print(json.dumps({"valid": False,
                          "error": "no field rows parsed from %s (section %s)"
                                   % (args.contract, SECTION)}, ensure_ascii=False, indent=2))
        return 2
    try:
        with open(args.result, encoding="utf-8") as fh:
            result = json.load(fh)
    except Exception as exc:
        print(json.dumps({"valid": False, "error": "result unreadable: %s" % exc},
                         ensure_ascii=False, indent=2))
        return 2

    missing, nulls = check(result, fields)
    declared_missing = []
    if args.case and os.path.isfile(args.case):
        try:
            with open(args.case, encoding="utf-8") as fh:
                case = json.load(fh)
            contract = case.get("output_contract")
            if isinstance(contract, dict):
                declared_missing = [k for k in contract if k not in result]
            elif isinstance(contract, list):
                declared_missing = [k for k in contract
                                    if isinstance(k, str) and k not in result]
        except Exception as exc:
            print(json.dumps({"valid": False, "error": "case unreadable: %s" % exc},
                             ensure_ascii=False, indent=2))
            return 2

    report = {
        "valid": not missing and not declared_missing,
        "contract": os.path.basename(args.contract),
        "fields_contracted": len(fields),
        "fields_present": len(fields) - len(missing),
        "missing": missing,
        "present_but_null": nulls,
        "case_contract_missing": declared_missing,
        "note": "present_but_null is a warning: deck/evidence_map_json are null "
                "only on honest failure runs, never on a completed run",
    }
    if not args.quiet:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
