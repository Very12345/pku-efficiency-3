#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_contract.py — verify that result.json covers every field of the
output_contract declared by the case/task.  (verify role.)

Field source priority:
  1. --contract <file.json | inline-json>   (explicit)
  2. sibling self_check.json["contract_applied"] (written by main.py)
  3. build-in default contract of this Skill

Checks presence and container type (list/dict/str/number/bool), recording
missing and wrong-typed fields.  Missing optional fields are reported but do
not fail the check.

CLI: python check_contract.py <result.json> [--contract <file|json>]
"""

import json
import os
import sys

from common import (DEFAULT_CONTRACT_FIELDS, CONTRACT_TYPE_DEFAULTS,
                    normalize_output_contract, parse_output_contract_from_task)


def _load_contract(args):
    specs = []
    note = ""
    if "--contract" in args:
        idx = args.index("--contract")
        if idx + 1 < len(args):
            raw = args[idx + 1]
            try:
                specs = normalize_output_contract(json.loads(raw))
                note = "--contract inline json"
            except json.JSONDecodeError:
                with open(raw, "r", encoding="utf-8") as fh:
                    specs = normalize_output_contract(json.load(fh))
                note = "--contract file %s" % os.path.basename(raw)
    return specs, note


def check(result, specs=None, source_note=""):
    missing = []
    wrong_type = []
    declared = []
    if not specs:
        specs = normalize_output_contract(DEFAULT_CONTRACT_FIELDS)
        source_note = source_note or "built-in default contract"
    for name, required, ctype in specs:
        if name in declared:
            continue
        declared.append(name)
        present = name in result and result[name] is not None
        if not present:
            if required:
                missing.append(name)
            continue
        val = result[name]
        default = CONTRACT_TYPE_DEFAULTS.get(ctype)
        if ctype == "any" or default is None:
            continue
        if isinstance(default, list) and not isinstance(val, list):
            wrong_type.append((name, ctype, type(val).__name__))
        elif isinstance(default, dict) and not isinstance(val, dict):
            wrong_type.append((name, ctype, type(val).__name__))
        elif isinstance(default, str) and not isinstance(val, str):
            wrong_type.append((name, ctype, type(val).__name__))
        elif isinstance(default, bool) and not isinstance(val, (bool, int)):
            wrong_type.append((name, ctype, type(val).__name__))
        elif isinstance(default, (int, float)) and not isinstance(val, (int, float)):
            wrong_type.append((name, ctype, type(val).__name__))
    return {
        "valid": len(missing) == 0 and len(wrong_type) == 0,
        "declared": declared,
        "missing_required": missing,
        "missing_optional": [],
        "wrong_type": wrong_type,
        "checked_against": source_note,
        "summary": "declared=%d missing=%d wrong_type=%d"
                   % (len(declared), len(missing), len(wrong_type)),
    }


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if len(args) < 2 or not args[1].endswith(".json"):
        print(json.dumps({"error": "usage: check_contract.py <result.json> [--contract <file|json>]"},
                         ensure_ascii=False))
        return 2
    path = args[1]
    with open(path, "r", encoding="utf-8") as fh:
        result = json.load(fh)
    specs, note = _load_contract(argv)
    if not specs:
        # fallback: sibling self_check.json
        sibling = os.path.join(os.path.dirname(os.path.abspath(path)), "self_check.json")
        if os.path.exists(sibling):
            try:
                with open(sibling, "r", encoding="utf-8") as fh:
                    sc = json.load(fh)
                applied = sc.get("contract_applied")
                if applied:
                    specs = normalize_output_contract(applied)
                    note = "sibling self_check.json contract_applied"
            except Exception:  # noqa: BLE001
                pass
    report = check(result, specs, note)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))