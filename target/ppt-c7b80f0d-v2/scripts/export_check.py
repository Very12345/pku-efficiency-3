# -*- coding: utf-8 -*-
"""export_check.py — final export checker for a produced result.json + artifacts.

Part of the "paper-to-academic-ppt" Skill v2 (ppt-c7b80f0d, efficiency-3).

Purpose
-------
This is the CP3 gate before a run is considered finished. It verifies, on the
actual produced files:

* result.json contract: required top-level keys, status vocabulary, case_id,
  and every field the case's output_contract declares echoed at top level with
  never-null type-appropriate empty values;
* deck artifact exists, reopens with python-pptx, and its OOXML container is
  sane (zip + required parts + well-formed XML — via ooxml_kit.zip_sanity);
* every declared preview exists and is honestly marked pil-approximation;
* evidence mapping file exists and its markdown table row count matches the
  declared entries and gap count (per-slide evidence mapping table consistency);
* speaker notes are present and separated (informational);
* honesty invariants: status in (completed|partial|failed); nothing marked
  completed when the material was unreadable.

Same CLI as the base package's validate.py so existing pipelines keep working:
    python export_check.py --result <result.json> [--out-dir <dir>] [--case <case.json>]
"""
from __future__ import annotations

import json
import os
import re
import sys

import ooxml_kit

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


def _count_md_table_rows(path):
    """Count data rows of the first markdown table in the evidence mapping."""
    try:
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    except Exception:
        return None
    rows = 0
    in_table = False
    for ln in lines:
        if ln.strip().startswith("|"):
            if not in_table:
                in_table = True
                header = True
            parts = [c.strip() for c in ln.strip().strip("|").split("|")]
            if header:
                header = False
                continue
            if set(parts) == {"---"} or all(re.fullmatch(r":?-{3,}:?", p) for p in parts):
                continue
            if any(p for p in parts):
                rows += 1
        elif ln.strip():
            in_table = False
    return rows


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

    # -- deck artifact: OOXML container sanity + reopen -----------------------
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
                zrec = ooxml_kit.zip_sanity(full)
                if zrec.get("errors"):
                    errors.append("OOXML sanity failed: %s" % "; ".join(zrec["errors"]))
                naudit = ooxml_kit.naming_audit(prs)
                if naudit.get("unnamed"):
                    warnings.append("unnamed/auto shapes: %d (see layer-naming.md)"
                                    % len(naudit["unnamed"]))
                notes_missing = [i for i, t in ooxml_kit.iter_notes(prs) if not t.strip()]
                if notes_missing:
                    warnings.append("slides without speaker notes: %s (notes should be "
                                    "separate from page text)" % notes_missing)
            except Exception as exc:
                errors.append("deck not reopenable with python-pptx: %s" % exc)

    # -- previews ---------------------------------------------------------------
    for p in result.get("previews", []):
        f = p.get("file", "")
        if p.get("kind") != "pil-approximation":
            warnings.append("preview kind not marked approximation: %s" % f)
        full = f if os.path.isabs(f) else os.path.join(base, f)
        if not os.path.isfile(full):
            errors.append("preview artifact missing: %s" % full)

    # -- evidence mapping table --------------------------------------------------
    ev = result.get("evidence_mapping") or {}
    if ev.get("file"):
        full = ev["file"] if os.path.isabs(ev["file"]) else os.path.join(base, ev["file"])
        if not os.path.isfile(full):
            errors.append("evidence mapping missing: %s" % full)
        else:
            rows = _count_md_table_rows(full)
            declared = ev.get("entries")
            if rows is not None and isinstance(declared, int) and rows != declared:
                warnings.append("evidence mapping table rows=%s != declared entries=%s"
                                % (rows, declared))
            gaps = ev.get("gaps") or []
            if isinstance(gaps, list):
                for g in gaps:
                    gstr = str(g)
                    found = gstr in open(full, encoding="utf-8").read()
                    if not found:
                        warnings.append("evidence mapping table lacks declared gap row: %s" % gstr)

    rendered = (result.get("run_meta") or {}).get("rendered_with")
    if not rendered:
        warnings.append("run_meta.rendered_with not recorded")
    return _report(result, errors, warnings)


def main(argv=None):
    import argparse

    ap = argparse.ArgumentParser(description="export checker for a produced result.json")
    ap.add_argument("--result", required=True)
    ap.add_argument("--out-dir", default=".", help="directory where artifacts live")
    ap.add_argument("--case", default=None, help="optional original case.json to check contract echo")
    args = ap.parse_args(argv)

    with open(args.result, encoding="utf-8") as fh:
        result = json.load(fh)
    case = None
    if args.case and os.path.isfile(args.case):
        with open(args.case, encoding="utf-8") as fh:
            case = json.load(fh)
    rep = validate(result, args.out_dir, case)
    return 0 if rep["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())