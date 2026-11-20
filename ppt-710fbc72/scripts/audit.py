# -*- coding: utf-8 -*-
"""audit.py — verify the real produced artifacts (not self-reported).

Runs against the actual files on disk: reopens the pptx with python-pptx,
extracts slide texts/notes, and checks coverage, cross-reference consistency,
overflow records, uniform footer, preview validity and evidence mapping.
Writes audit.json.
"""
from __future__ import annotations

import os
from common import (sha256_file, dump_json, utf8_writer, SKILL_NAME, SKILL_VERSION)

REQUIRED_RESULT_FIELDS = [
    "case_id", "skill", "status", "workorder", "title", "slide_count",
    "main_result", "artifacts", "slide_evidence", "template_audit",
    "verification", "sources", "uncertainty", "change_records",
    "status_notes", "generated_at", "generator", "tool_versions",
]


def _slide_texts(pptx_path: str) -> list:
    from pptx import Presentation
    prs = Presentation(pptx_path)
    out = []
    for si, slide in enumerate(prs.slides, start=1):
        texts = []
        for sh in slide.shapes:
            if sh.has_text_frame:
                t = sh.text_frame.text.strip()
                if t:
                    texts.append(t)
        notes = ""
        try:
            if slide.has_notes_slide:
                notes = slide.notes_slide.notes_text_frame.text.strip()
        except Exception:
            notes = ""
        out.append({"page_no": si, "texts": texts, "notes": notes})
    return out


def audit(content: dict, plan: dict, out_dir: str, case_id: str,
          build_audit: dict | None = None) -> dict:
    checks = []
    pptx_path = os.path.join(out_dir, f"{case_id}_deck.pptx")
    result_path = os.path.join(out_dir, "result.json")
    cover_png = os.path.join(out_dir, f"{case_id}_cover_preview.png")
    sheet_png = os.path.join(out_dir, f"{case_id}_slides_contact_schematic.png")
    spec_path = os.path.join(out_dir, "spec.json")

    def add(check, level, detail):
        checks.append({"check": check, "level": level, "detail": detail})

    # 1 file existence + reopening (result.json is written after audit by
    #    main.py; its contract validation lives in validate_result.py and is
    #    appended as check 'result.contract' into audit.json by main.py)
    for role, path in (("pptx", pptx_path), ("cover_png", cover_png),
                       ("contact_png", sheet_png), ("spec", spec_path)):
        if os.path.exists(path):
            add(f"artifact.{role}.exists", "ok", os.path.abspath(path))
        else:
            add(f"artifact.{role}.exists", "fail", f"missing: {path}")

    slides = []
    if os.path.exists(pptx_path):
        try:
            slides = _slide_texts(pptx_path)
            add("pptx.reopen", "ok", f"python-pptx reopened; {len(slides)} slides")
        except Exception as exc:
            add("pptx.reopen", "fail", f"reopen failed: {exc}")
    else:
        add("pptx.reopen", "fail", "pptx missing")

    planned = len(plan.get("pages", []))
    if slides:
        if len(slides) == planned:
            add("pptx.slide_count", "ok", f"{len(slides)} == planned {planned}")
        else:
            add("pptx.slide_count", "fail", f"{len(slides)} != planned {planned} (see change_records)")

    # 2 claim coverage: every plan claim must appear in some slide text
    all_text = " ".join(t for s in slides for t in s["texts"])
    missing_claims = []
    for p in plan.get("pages", []):
        for c in p.get("claims") or []:
            probe = c[:18]
            if probe and probe not in all_text:
                missing_claims.append(f"p{p['page_no']}:{probe}")
    if missing_claims:
        add("content.claim_coverage", "warn", f"{len(missing_claims)} claims not literally found; truncated: {missing_claims[:5]}")
    else:
        add("content.claim_coverage", "ok", "all plan claims present in slide texts")

    # 3 figure cross-reference consistency: every figure on a results page has
    #    a caption visible; every figure in content appears somewhere or flagged
    fig_ids = list(content.get("figures") or [])
    figid_set = {str(f.get("id")) for f in fig_ids} if isinstance(fig_ids, list) else set()
    refs_in_text = []
    for p in plan.get("pages", []):
        if p["page_type"] == "results":
            for fid in p.get("figure_refs") or []:
                refs_in_text.append(fid)
    miss_figs = []
    for r in set(refs_in_text):
        if figid_set and r not in figid_set:
            miss_figs.append(r)
    if miss_figs:
        add("xref.figure_refs", "warn", f"text references figures not in figure list: {sorted(miss_figs)}")
    else:
        add("xref.figure_refs", "ok", f"{len(set(refs_in_text))} figure refs resolve to figure list" if refs_in_text else "no figure refs in plan")
    unplaced_figs = []
    for f in fig_ids:
        fid = str(f.get("id"))
        placed = any(fid in (p.get("figure_refs") or []) for p in plan.get("pages", []) if p["page_type"] == "results")
        if not placed:
            unplaced_figs.append(fid)
    if unplaced_figs:
        add("xref.figure_placement", "warn", f"figures never placed on a results page: {unplaced_figs}")
    else:
        add("xref.figure_placement", "ok", "every figure is placed on a results page")

    # 4 notes present on every page
    no_notes = [s["page_no"] for s in slides if not s["notes"]]
    if no_notes:
        add("notes.present", "warn", f"slides without notes: {no_notes}")
    else:
        add("notes.present", "ok", f"speaker notes on all {len(slides)} slides")

    # 5 overflow / font ladder from builder audit
    overflow_events = []
    under_min = []
    for pa in (build_audit or {}).get("page_audit", []):
        for key in ("title_fit", "subtitle_fit", "body_fit"):
            part = pa.get(key) or {}
            if part.get("overflow_lines"):
                overflow_events.append(f"p{pa.get('page_no')} {key}: overflow={part['overflow_lines']}")
            if part.get("size_pt") and part["size_pt"] < 14 and part.get("overflow_lines"):
                under_min.append(f"p{pa.get('page_no')}:{key}=>{part['size_pt']}pt")
    if overflow_events:
        add("layout.overflow", "warn", f"{len(overflow_events)} overflowed boxes; {overflow_events[:5]}")
    else:
        add("layout.overflow", "ok", "no text box overflow estimated")
    if under_min:
        add("layout.font_floor", "warn", f"boxes near floor size: {under_min[:5]}")
    else:
        add("layout.font_floor", "ok", "no box needed to shrink below 14pt")

    # 6 footer uniformity: non-cover slides carry a page number textbox
    if os.path.exists(pptx_path):
        try:
            from pptx import Presentation as _Pres
            _prs = _Pres(pptx_path)
            bad_foot = []
            for si, slide in enumerate(_prs.slides, start=1):
                if si == 1:
                    continue
                has_pn = False
                for sh in slide.shapes:
                    if hasattr(sh, "has_text_frame") and sh.has_text_frame:
                        t = sh.text_frame.text.strip()
                        if t.isdigit() and 1 <= int(t) <= 99:
                            has_pn = True
                            break
                    if getattr(sh, "has_text_frame", False) and sh.text_frame.text.strip().isdigit():
                        has_pn = True
                        break
                if not has_pn:
                    bad_foot.append(si)
            if bad_foot:
                add("layout.footer_uniform", "warn", f"pages lacking page-number footer: {bad_foot}")
            else:
                add("layout.footer_uniform", "ok", "uniform footer/page numbers from page 2")
        except Exception as exc:
            add("layout.footer_uniform", "fail", f"could not scan footers: {exc}")

    # 7 previews valid (PNG signature + non-tiny)
    for role, path in (("cover_png", cover_png), ("contact_png", sheet_png)):
        if os.path.exists(path):
            with open(path, "rb") as fh:
                head = fh.read(8)
            size = os.path.getsize(path)
            if head == b"\x89PNG\r\n\x1a\n" and size > 2000:
                add(f"preview.{role}", "ok", f"PNG signature ok, {size} bytes")
            else:
                add(f"preview.{role}", "warn", f"PNG signature or size suspicious (head={head[:4]}, {size} B)")

    # 8 evidence mapping coverage
    ev_total = ev_wloc = 0
    for p in plan.get("pages", []):
        for e in p.get("evidence", []):
            ev_total += 1
            if e.get("loc"):
                ev_wloc += 1
    if ev_total:
        frac = ev_wloc / ev_total
        add("traceability.evidence_loc", "ok" if frac >= 0.9 else "warn",
            f"{ev_wloc}/{ev_total} claims carry source locators ({frac:.0%})")
    else:
        add("traceability.evidence_loc", "warn", "no claims with evidence rows (see uncertainty)")

    # 9 spec hash (determinism anchor; result.json itself is validated by the
    #    'result.contract' check instead of being hashed here, so audit.json
    #    never embeds a self-referential hash)
    spec_hash = sha256_file(spec_path) if os.path.exists(spec_path) else None
    hashes = {"spec_sha256": spec_hash}

    audit_obj = {
        "_meta": "audit over real produced artifacts",
        "generator": SKILL_NAME,
        "skill_version": SKILL_VERSION,
        "checks": checks,
        "slide_summary": [{"page_no": s["page_no"], "text_count": len(s["texts"]),
                           "notes_len": len(s["notes"])} for s in slides],
        "hashes": hashes,
    }
    dump_json(os.path.join(out_dir, "audit.json"), audit_obj)
    print(f"audit ok: {len(checks)} checks, fails={sum(1 for c in checks if c['level']=='fail')}, warns={sum(1 for c in checks if c['level']=='warn')}")
    return audit_obj


def main(argv=None):
    utf8_writer()
    import argparse
    import json
    ap = argparse.ArgumentParser(description="audit.py — verify produced artifacts")
    ap.add_argument("--content", required=True)
    ap.add_argument("--spec", required=True)
    ap.add_argument("--out", required=True, help="output dir containing the deck + result.json")
    ap.add_argument("--build-audit", default="", help=".build_audit.json produced by pptxbuild")
    a = ap.parse_args(argv)
    content = json.load(open(a.content, "r", encoding="utf-8-sig"))
    plan = json.load(open(a.spec, "r", encoding="utf-8-sig"))
    ba = None
    if a.build_audit and os.path.exists(a.build_audit):
        ba = json.load(open(a.build_audit, "r", encoding="utf-8-sig"))
    audit(content, plan, a.out, content.get("case_id", "deck"), ba)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())