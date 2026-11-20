# -*- coding: utf-8 -*-
"""spec_lint.py — structural lint of a deck-spec.json (page-level plan).

Part of the "paper-to-academic-ppt" Skill v2 (ppt-c7b80f0d, efficiency-3).

This is the "先 lint 再生成" checkpoint (CP1): before deckgen builds anything,
the page plan must satisfy the structural rules that keep the deck academic
rather than a paragraph dump:

* every page carries a one-line `claim` and (evidence list OR evidence_gap);
* bullets are phrase-level, <= MAX_BULLETS per page, <= MAX_CHARS_BULLET each
  (CJK characters count double);
* layout_hint comes from the documented vocabulary;
* figure/table entries keep the paper's own ref numbering (non-empty ref);
* page numbers are unique and 1-based;
* takeaway / limitations are present for the closing slide.

The linter is advisory-for-the-agent but hard for the deck: a spec that cannot
pass lint must not be built silently — build may continue only with the
problems explicitly recorded in result.json uncertainty/change_records.
"""
from __future__ import annotations

import json
import os
import sys

LAYOUT_HINTS = frozenset(
    ["title", "section", "content", "figure", "table", "two-content", "reference"])
MAX_BULLETS = 6
MAX_CHARS_BULLET = 110   # CJK counts double, enforced in _bullet_len
MAX_CHARS_TITLE = 40
MAX_CHARS_CLAIM = 220


def _bullet_len(item) -> int:
    """Character budget for a bullet; CJK glyphs count double (wider)."""
    text = item[0] if isinstance(item, (list, tuple)) else str(item)
    return sum(2 if ord(ch) > 0x2E7F else 1 for ch in text)


def lint(spec: dict) -> dict:
    """Return {"valid": bool, "problems": [...], "counts": {...}}."""
    problems = []
    spec = spec or {}
    slides = spec.get("slides")
    if not isinstance(slides, list) or not slides:
        problems.append("spec has no slides list (cannot plan a deck)")
        return {"valid": False, "problems": problems,
                "counts": {"slides": 0, "evidence_gaps": 0, "unmapped": 0}}

    pages = []
    n_gap = 0
    n_unmapped = 0
    seen_pages = set()
    for i, s in enumerate(slides, start=1):
        if not isinstance(s, dict):
            problems.append("slide #%d is not an object" % i)
            continue
        page = s.get("page")
        try:
            page = int(page)
        except (TypeError, ValueError):
            problems.append("slide #%d has invalid page: %r" % (i, s.get("page")))
            page = None
        if page is not None:
            if page in seen_pages:
                problems.append("duplicate page number %d" % page)
            seen_pages.add(page)
            pages.append(page)

        if not (s.get("title") or "").strip():
            problems.append("slide #%d: empty title" % i)
        elif _bullet_len(s["title"]) > MAX_CHARS_TITLE * 2:
            problems.append("slide #%d: title too long (CJK-weighted > %d)" % (i, MAX_CHARS_TITLE * 2))

        claim = (s.get("claim") or "").strip()
        if not claim:
            problems.append("slide #%d: missing one-line claim" % i)
        elif _bullet_len(claim) > MAX_CHARS_CLAIM * 2:
            problems.append("slide #%d: claim too long (CJK-weighted > %d)" % (i, MAX_CHARS_CLAIM * 2))

        hint = s.get("layout_hint") or "content"
        if hint not in LAYOUT_HINTS:
            problems.append("slide #%d: layout_hint %r not in vocabulary %s"
                            % (i, hint, sorted(LAYOUT_HINTS)))

        bullets = s.get("bullets") or []
        if len(bullets) > MAX_BULLETS:
            problems.append("slide #%d: %d bullets > %d"
                            % (i, len(bullets), MAX_BULLETS))
        for b in bullets:
            if _bullet_len(b) > MAX_CHARS_BULLET * 2:
                problems.append("slide #%d: bullet too long (CJK-weighted > %d): %r"
                                % (i, MAX_CHARS_BULLET * 2, str(b)[:40]))
                break

        ev = s.get("evidence") or []
        gap = bool(s.get("evidence_gap"))
        if not ev and not gap:
            problems.append("slide #%d: no evidence entries and evidence_gap not set "
                            "(must be one of them)" % i)
            n_unmapped += 1
        elif gap:
            n_gap += 1
        for e in ev:
            if not isinstance(e, dict) or not (e.get("ref") or "").strip():
                problems.append("slide #%d: evidence entry without ref" % i)
                break

        fig = s.get("figure")
        if isinstance(fig, dict) and not (fig.get("ref") or "").strip():
            problems.append("slide #%d: figure entry without paper ref" % i)
        tab = s.get("table")
        if isinstance(tab, dict) and not (tab.get("ref") or "").strip():
            problems.append("slide #%d: table entry without paper ref" % i)

    if not (spec.get("takeaway") or "").strip():
        problems.append("missing deck takeaway sentence (closing slide)")
    if not (spec.get("limitations") or "").strip():
        problems.append("missing limitations sentence (closing slide)")

    return {"valid": not problems, "problems": problems,
            "counts": {"slides": len(slides), "evidence_gaps": n_gap,
                       "unmapped": n_unmapped}}


def main(argv=None):
    ap = __import__("argparse").ArgumentParser(description="lint a deck-spec.json")
    ap.add_argument("--spec", required=True)
    args = ap.parse_args(argv)
    with open(args.spec, encoding="utf-8") as fh:
        spec = json.load(fh)
    rep = lint(spec)
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    return 0 if rep["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())