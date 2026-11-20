# -*- coding: utf-8 -*-
"""Validate a result.json produced by this skill against OUTPUT_CONTRACT.md.

Usage:
  python scripts/check_contract.py <path-to-result.json>
  python scripts/check_contract.py <case.json> --result <result.json>   # also
                                                    # mirrors declared contract

Exit code 0 = valid, 1 = contract violations found, 2 = unreadable input.
"""
import json
import os
import sys

REQUIRED_KEYS = [
    "case_id",
    "status",
    "created_at",
    "deck",
    "evidence",
    "previews",
    "sources",
    "uncertainty",
    "change_records",
]

DECK_KEYS = ["editable", "format", "slide_count", "slides"]
EVIDENCE_KEYS = ["map", "unverified_claims"]
PREVIEW_KEYS = ["pngs", "pdf", "method"]
STATUS_VALUES = {"success", "partial", "failed"}


def main(argv=None):
    if not argv:
        argv = sys.argv[1:]
    if not argv:
        print("usage: python check_contract.py <result.json> [<case.json>]")
        return 2
    path = argv[0]
    case_path = argv[1] if len(argv) > 1 else None
    try:
        with open(path, "r", encoding="utf-8") as f:
            result = json.load(f)
    except Exception as e:  # noqa: BLE001
        print("ERROR unreadable result.json: %s" % e)
        return 2
    case = None
    if case_path:
        try:
            with open(case_path, "r", encoding="utf-8") as f:
                case = json.load(f)
        except Exception as e:  # noqa: BLE001
            print("WARN case.json unreadable: %s" % e)

    problems = []
    base = os.path.dirname(os.path.abspath(path))
    for k in REQUIRED_KEYS:
        if k not in result:
            problems.append("missing top-level field: %s" % k)
        elif result[k] is None:
            problems.append("top-level field is null: %s" % k)
    for k in DECK_KEYS:
        if k not in result.get("deck", {}):
            problems.append("deck missing field: %s" % k)
    for k in EVIDENCE_KEYS:
        if k not in result.get("evidence", {}):
            problems.append("evidence missing field: %s" % k)
    for k in PREVIEW_KEYS:
        if k not in result.get("previews", {}):
            problems.append("previews missing field: %s" % k)
    if result.get("status") not in STATUS_VALUES:
        problems.append("invalid status: %r" % result.get("status"))
    for name in ("sources", "uncertainty", "change_records"):
        if not isinstance(result.get(name), list):
            problems.append("%s should be a list" % name)

    editable = result.get("deck", {}).get("editable", "")
    if editable:
        ep = os.path.join(base, editable)
        if not os.path.isfile(ep):
            problems.append("editable deck file missing: %s" % editable)
    pdf = result.get("previews", {}).get("pdf", "")
    if pdf:
        pp = os.path.join(base, pdf)
        if not os.path.isfile(pp):
            problems.append("preview pdf missing: %s" % pdf)
    pngs = result.get("previews", {}).get("pngs", [])
    for p in pngs:
        if not os.path.isfile(os.path.join(base, p)):
            problems.append("preview png missing: %s" % p)
            break

    oc = (case or {}).get("output_contract")
    if isinstance(oc, dict):
        for key in oc:
            if key not in result:
                problems.append("declared output_contract field missing: %s" % key)

    ok = not problems
    print(json.dumps({"valid": ok, "case_id": result.get("case_id"),
                      "status": result.get("status"),
                      "deck_editable": result.get("deck", {}).get("editable", ""),
                      "slide_count": result.get("deck", {}).get("slide_count"),
                      "problems": problems}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())