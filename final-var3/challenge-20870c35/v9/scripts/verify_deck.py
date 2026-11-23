#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_deck.py — machine checks on the produced editable .pptx.
(verify role in the build/extract/render/verify split.)

Checks (write-back into deck_audit.json, embedded in result.json.audit.deck):
  * the .pptx opens with python-pptx (a real parse, not a stat)
  * OPC package integrity: every [Content_Types].xml-referenced part exists
    (best-effort zip scan), and the file is a valid zip
  * slide count == len(plan.pages)
  * every slide carries non-empty speaker notes (讲稿/备注)
  * every content slide carries the Skill's deterministically named
    claim element (page-claim-NN) — the "page expresses its unique claim"
    invariant
  * figure binding state per page (image embedded vs honest placeholder)
  * normalized sha256 (zip payload excluding docProps/core.xml timestamps)
    for the determinism probe (G9)

CLI: python verify_deck.py <deck.pptx> [--expect-pages N] [--plan plan.json]
Exit code 0 when all checks pass.
"""

import hashlib
import json
import os
import re
import sys
import zipfile

from common import read_json

_CLAIM_NAME_RE = re.compile(r"^page-claim-\d+$")
_STRUCTURAL = {"title", "agenda", "qa"}


def normalize_pptx_sha(path):
    """sha256 over the pptx zip payload excluding docProps/core.xml (which may
    carry timestamps across tools).  Deterministic across identical content."""
    h = hashlib.sha256()
    with zipfile.ZipFile(path, "r") as zf:
        for name in sorted(zf.namelist()):
            if name == "docProps/core.xml":
                continue
            h.update(name.encode("utf-8"))
            h.update(b"\x00")
            h.update(zf.read(name))
    return h.hexdigest()


def _opc_integrity(path):
    """Verify every part referenced by [Content_Types].xml exists in the zip."""
    issues = []
    try:
        with zipfile.ZipFile(path, "r") as zf:
            names = set(zf.namelist())
            if "[Content_Types].xml" not in names:
                return False, ["[Content_Types].xml missing"]
            ct = zf.read("[Content_Types].xml").decode("utf-8", "replace")
            for m in re.finditer(r'PartName="([^"]+)"', ct):
                part = m.group(1).lstrip("/")
                if part and part not in names:
                    issues.append(part)
        return len(issues) == 0, issues
    except zipfile.BadZipFile as exc:
        return False, ["bad zip: %s" % exc]
    except Exception as exc:  # noqa: BLE001
        return False, ["opc scan failed: %s" % exc]


def verify_deck(path, expect_pages=None, plan=None):
    """Return a deck-audit report dict."""
    checks = []
    errors = []
    slides = []

    def _chk(name, ok, detail=""):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})
        if not ok:
            errors.append(name + " " + str(detail)[:200])

    from pptx import Presentation
    if not os.path.exists(path):
        _chk("opens", False, "file missing: %s" % path)
        return {"valid": False, "checks": checks, "errors": errors,
                "slides": slides, "normalized_sha256": None}

    try:
        prs = Presentation(path)
        _chk("opens", True, "python-pptx parse ok")
    except Exception as exc:  # noqa: BLE001
        _chk("opens", False, str(exc))
        return {"valid": False, "checks": checks, "errors": errors,
                "slides": slides, "normalized_sha256": normalize_pptx_sha(path)}

    slides_list = list(prs.slides)
    n = len(slides_list)
    if expect_pages is not None:
        _chk("slide_count_matches_plan", n == expect_pages,
             "slides=%d expect=%d" % (n, expect_pages))
    _chk("slide_count_positive", n > 0, "slides=%d" % n)

    # map plan pages by index for expectation
    plan_pages = (plan or {}).get("pages") or []

    notes_missing = []
    claim_missing = []
    text_missing = []
    for i, slide in enumerate(slides_list):
        rec = {"slide_index": i + 1}
        try:
            notes = slide.notes_slide.notes_text_frame.text or ""
        except Exception:  # noqa: BLE001
            notes = ""
        rec["notes_nonempty"] = bool(notes and notes.strip())
        if not rec["notes_nonempty"]:
            notes_missing.append(i + 1)
        # claim element naming (cover is exempt: it carries title+meta instead)
        if i < len(plan_pages):
            is_cover = plan_pages[i].get("block") == "title"
        else:
            is_cover = (i == 0)
        claim_names = [sh.name for sh in slide.shapes
                       if _CLAIM_NAME_RE.match(getattr(sh, "name", "") or "")]
        rec["claim_element"] = bool(claim_names)
        if not claim_names and not is_cover:
            claim_missing.append(i + 1)
        # figure element
        fig_names = [sh.name for sh in slide.shapes
                     if re.match(r"^page-figure-\d+$", getattr(sh, "name", "") or "")]
        rec["figure_element"] = bool(fig_names)
        # title text
        texts = []
        for sh in slide.shapes:
            if sh.has_text_frame:
                t = sh.text_frame.text or ""
                if t.strip():
                    texts.append(t.strip()[:40])
        rec["has_any_text"] = bool(texts)
        if not rec["has_any_text"]:
            text_missing.append(i + 1)
        # planned block for this slide (if plan supplied)
        if i < len(plan_pages):
            rec["planned_block"] = plan_pages[i].get("block")
            rec["planned_title"] = plan_pages[i].get("title")
        slides.append(rec)
    _chk("notes_on_every_slide", len(notes_missing) == 0,
         "slides_without_notes=%s" % notes_missing)
    _chk("claim_element_on_every_slide", len(claim_missing) == 0,
         "slides_without_claim_element=%s" % claim_missing)
    _chk("text_on_every_slide", len(text_missing) == 0,
         "slides_without_text=%s" % text_missing)

    opc_ok, opc_issues = _opc_integrity(path)
    _chk("opc_integrity", opc_ok, "missing_parts=%s" % opc_issues[:5])

    norm_sha = normalize_pptx_sha(path)
    _chk("deterministic_sha_available", bool(norm_sha), "normalized sha256 computed")

    return {
        "valid": len(errors) == 0,
        "checks": checks,
        "errors": errors,
        "slides": slides,
        "slide_count": n,
        "normalized_sha256": norm_sha,
        "summary": "checks=%d errors=%d" % (len(checks), len(errors)),
    }


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if len(args) < 2:
        print(json.dumps({"error": "usage: verify_deck.py <deck.pptx> "
                                   "[--expect-pages N] [--plan plan.json]"},
                         ensure_ascii=False))
        return 2
    deck = args[1]
    expect = None
    plan = None
    if "--expect-pages" in argv:
        try:
            expect = int(argv[argv.index("--expect-pages") + 1])
        except (ValueError, IndexError):
            pass
    if "--plan" in argv:
        plan_path = argv[argv.index("--plan") + 1]
        if os.path.exists(plan_path):
            plan = read_json(plan_path)
    report = verify_deck(deck, expect_pages=expect, plan=plan)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))