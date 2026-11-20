# -*- coding: utf-8 -*-
"""validate.py — standalone check of a produced result.json against the contract.

Part of the "paper-to-academic-ppt" Skill.

Usage
-----
    python validate.py --result <result.json> [--out-dir <dir where artifacts live>]
    python validate.py --result out/result.json

Checks (exit code 0 = all pass, 1 = problems found):
* required top-level keys and status vocabulary;
* case_id present and non-empty;
* every field declared by the case's output_contract is echoed at top level
  (unknown declared fields get type-appropriate empty values — never null);
* deck artifact exists on disk and reopens with python-pptx;
* every preview file exists;
* evidence mapping file exists;
* honesty invariants: status in (completed|partial|failed); previews carry
  kind=pil-approximation; run_meta.rendered_with is recorded; nothing is marked
  completed when material was unreadable.

Prints a short JSON report. This validator is itself the "check" the Skill runs
as its self-audit before a run is considered finished.
"""
from __future__ import annotations

import json
import os
import sys

REQUIRED_TOP = ["case_id", "status", "sources", "uncertainty",
                "change_records", "run_meta"]
VALID_STATUS = ("completed", "partial", "failed")


def _report(result, errors, warnings):
    out = {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "case_id": result.get("case_id"),
        "status": result.get("status"),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return out


def validate(result, out_dir=None, case=None):
    errors, warnings = [], []
    if not isinstance(result, dict):
        return _report({}, ["result.json is not a JSON object"], [])

    for k in REQUIRED_TOP:
        if k not in result:
            errors.append("missing required key: %s" % k)
    cid = result.get("case_id")
    if not cid:
        errors.append("case_id empty/missing")
    if result.get("status") not in VALID_STATUS:
        errors.append("status out of vocabulary: %r" % result.get("status"))
    if result.get("status") == "completed":
        if result.get("material_status") == "unreadable":
            errors.append("status=completed but material was unreadable (inconsistent)")
    if result.get("deck_error"):
        warnings.append("deck_error present: %s" % result["deck_error"])

    # contract echo
    if case is not None and isinstance(case.get("output_contract"), dict):
        for k in case["output_contract"]:
            if k not in result:
                errors.append("output_contract field not echoed: %s" % k)
            elif result[k] is None:
                errors.append("output_contract field is null: %s (must be ''/[]/{})" % k)

    # artifact integrity
    base = out_dir or "."
    deck = result.get("deck") or {}
    if deck.get("file"):
        rel = deck.get("path") or deck["file"]
        full = rel if os.path.isabs(rel) else os.path.join(base, rel)
        if not os.path.isfile(full):
            errors.append("deck artifact missing: %s" % full)
        else:
            try:
                from pptx import Presentation
                prs = Presentation(full)
                if len(prs.slides) != deck.get("slide_count"):
                    warnings.append("deck slide_count mismatch: disk=%d json=%s"
                                    % (len(prs.slides), deck.get("slide_count")))
            except Exception as exc:
                errors.append("deck not reopenable with python-pptx: %s" % exc)
    for p in result.get("previews", []):
        f = p.get("file", "")
        if p.get("kind") != "pil-approximation":
            warnings.append("preview kind not marked approximation: %s" % f)
        full = f if os.path.isabs(f) else os.path.join(base, f)
        if not os.path.isfile(full):
            errors.append("preview artifact missing: %s" % full)
    ev = result.get("evidence_mapping") or {}
    if ev.get("file"):
        full = ev["file"] if os.path.isabs(ev["file"]) else os.path.join(base, ev["file"])
        if not os.path.isfile(full):
            errors.append("evidence mapping missing: %s" % full)

    rendered = (result.get("run_meta") or {}).get("rendered_with")
    if not rendered:
        warnings.append("run_meta.rendered_with not recorded")
    return _report(result, errors, warnings)


def main(argv=None):
    import argparse
    import json as _json

    ap = argparse.ArgumentParser(description="validate a produced result.json")
    ap.add_argument("--result", required=True)
    ap.add_argument("--out-dir", default=".", help="directory where artifacts live")
    ap.add_argument("--case", default=None, help="optional original case.json to check contract echo")
    args = ap.parse_args(argv)

    with open(args.result, encoding="utf-8") as fh:
        result = _json.load(fh)
    case = None
    if args.case and os.path.isfile(args.case):
        with open(args.case, encoding="utf-8") as fh:
            case = _json.load(fh)
    rep = validate(result, args.out_dir, case)
    return 0 if rep["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())