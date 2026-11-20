#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_result.py — structural + honesty checks on a produced result.json.

Verifies, from the result itself and the files on disk next to it:
  * case_id / status are present and sane
  * a completed result has a non-empty page list, every page has a unique
    claim and at least one evidence locator (except structural pages)
  * every evidence source_file is declared in `sources`
  * declared artifacts (editable deck, previews) actually exist on disk
  * numeric claim tokens are traceable to some source text (warning level:
    this is a faithfulness hint for the human/grader, not a hard gate)

CLI:  python validate_result.py <result.json> [--strict]
Exit code 0 when valid (errors empty); 1 otherwise.  Prints a JSON report.
"""

import json
import os
import re
import sys

from evidence import number_tokens

DEBUG = False


def _load_sources_text(sources, result_dir):
    """Best effort: collect source text from the result record first, then from
    disk (source absolute path, or result_dir-relative candidates)."""
    text = ""
    for s in sources:
        if not isinstance(s, dict):
            continue
        t = s.get("text") or ""
        if isinstance(t, str) and t:
            text += t + "\n"
            continue
        for cand in [s.get("path"), os.path.join(result_dir, s.get("path") or s.get("file") or ""),
                     os.path.join(result_dir, s.get("file") or "")]:
            if cand and os.path.exists(cand):
                try:
                    raw = open(cand, "r", encoding="utf-8", errors="replace").read()
                    if raw:
                        text += raw + "\n"
                        break
                except Exception:  # noqa: BLE001
                    continue
    return text


def validate(result, result_dir, strict=False):
    errors = []
    warnings = []
    checks = []

    def check(name, ok, detail=""):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})
        return bool(ok)

    if not isinstance(result, dict):
        errors.append("result.json is not a JSON object")
        return {"valid": False, "errors": errors, "warnings": warnings, "checks": checks}

    case_id = result.get("case_id")
    check("case_id present", isinstance(case_id, str) and len(case_id) > 0,
          "case_id=%r" % (case_id,))
    status = result.get("status")
    check("status valid", status in ("completed", "partial", "failed"),
          "status=%r" % (status,))
    if strict and status == "failed":
        errors.append("strict mode: status is 'failed'")

    pages = result.get("pages")
    if status == "completed":
        check("pages non-empty", isinstance(pages, list) and len(pages) > 0,
              "n_pages=%s" % (len(pages) if isinstance(pages, list) else None))
        if isinstance(pages, list):
            page_errs = 0
            for p in pages:
                if not isinstance(p, dict):
                    page_errs += 1
                    continue
                if not (p.get("title") and p.get("claim")):
                    page_errs += 1
                    warnings.append("page %s lacks title or claim" % p.get("page_no"))
                block = p.get("block")
                if block not in ("title", "agenda", "qa"):
                    ev = p.get("evidence")
                    if not (isinstance(ev, list) and ev and ev[0].get("locator")):
                        page_errs += 1
                        warnings.append("page %s has no evidence locator (block=%s)"
                                        % (p.get("page_no"), block))
            check("pages have claim+evidence", page_errs == 0,
                  "issue_pages=%d" % page_errs)
            if page_errs:
                errors.append("%d page(s) missing claim or evidence locator" % page_errs)

    # sources declaration
    sources = result.get("sources")
    if isinstance(sources, list) and sources:
        declared = {str(s.get("file") or "") for s in sources if isinstance(s, dict)}
        ok = len(declared) >= 1
        check("sources declared", ok, "n_sources=%d" % len(declared))
    else:
        declared = set()
        check("sources declared", False, "sources missing or empty")
        errors.append("sources missing or empty")

    # evidence source files are declared
    missing_src = set()
    if isinstance(pages, list):
        for p in pages:
            for ev in p.get("evidence") or []:
                if ev.get("source_file") and ev["source_file"] not in declared:
                    missing_src.add(ev["source_file"])
    check("evidence sources declared", len(missing_src) == 0,
          "undeclared=%s" % sorted(missing_src))
    if missing_src:
        errors.append("evidence references undeclared sources: %s" % sorted(missing_src))

    # artifacts on disk
    artifacts = result.get("artifacts") or {}
    rel_checks = []
    deck = artifacts.get("editable_deck")
    if deck:
        rel_checks.append(("editable_deck", deck))
    previews = artifacts.get("previews") or {}
    for key in ("cover", "grid", "manifest"):
        val = previews.get(key) if isinstance(previews, dict) else None
        if val:
            rel_checks.append(("previews.%s" % key, val))
    missing_files = []
    for label, rel in rel_checks:
        full = os.path.join(result_dir, rel) if not os.path.isabs(rel) else rel
        if not os.path.exists(full):
            missing_files.append((label, rel))
        elif DEBUG:
            print("  ok:", full)
    check("artifacts exist on disk", len(missing_files) == 0,
          "missing=%s" % [(a, r) for a, r in missing_files])
    for label, rel in missing_files:
        errors.append("artifact missing on disk: %s (%s)" % (label, rel))

    # numeric faithfulness hint (warning only)
    src_text = _load_sources_text(sources, result_dir)
    src_numbers = number_tokens(src_text)
    suspected = []

    def _flag_worthy(num):
        # ignore tiny integers (page numbers, counts) and tokens created by
        # truncation ("92" from "92.3%"); flag real decimal/percent/stat tokens
        if re.fullmatch(r"\d{1,3}", num):
            return False
        return len(num) >= 4 or any(ch in num for ch in ".%‰pP<>=±")

    if isinstance(pages, list):
        for p in pages:
            for field in ("claim", "one_liner"):
                t = p.get(field) or ""
                for num in number_tokens(t):
                    if _flag_worthy(num) and num not in src_numbers and (p.get("page_no"), field, num) not in suspected:
                        suspected.append((p.get("page_no"), field, num))
    if suspected:
        warnings.append("numeric tokens in pages not found verbatim in any source: %s"
                        % suspected[:10])
    else:
        check("claim numbers traceable to sources", True, "all page numbers present in sources")

    return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings,
            "checks": checks, "summary": "checks=%d errors=%d warnings=%d"
            % (len(checks), len(errors), len(warnings))}


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    strict = "--strict" in argv
    if len(args) < 2:
        print(json.dumps({"error": "usage: validate_result.py <result.json> [--strict]"},
                         ensure_ascii=False))
        return 2
    path = args[1]
    with open(path, "r", encoding="utf-8") as fh:
        result = json.load(fh)
    result_dir = os.path.dirname(os.path.abspath(path)) or "."
    report = validate(result, result_dir, strict=strict)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))