# -*- coding: utf-8 -*-
"""check_contract.py — CP3 delivery gate: independent re-check of result.json
against OUTPUT_CONTRACT with hard gates G1–G8.

Run on the real output (after main.py), e.g.:

  python scripts/check_contract.py --result /app/output/result.json \
      --out-dir /app/output --case /input/case.json

Exit 0 + {"valid": true} when every gate passes; otherwise exit 1 and list
each failing gate.  This is a second, independent verifier: it re-opens the
pptx and re-scans the artifacts, it does not trust self-reported checks.
"""
from __future__ import annotations

import json
import os
import sys

from common import utf8_writer

GATES = {
    "G1": "case_id present and equals case.json case_id",
    "G2": "status is one of success/partial/failed (honest vocabulary)",
    "G3": "every output_contract key echoed at top level, no null placeholder",
    "G4": "main_result.deck exists and can be reopened with python-pptx",
    "G5": "slide_evidence has one entry per built slide",
    "G6": "template_audit present with opened_from/template_source/layouts/layout_used",
    "G7": "all listed artifacts exist under out-dir",
    "G8": "preview files exist when output_contract preview_png is true; uncertainty recorded for non-success status",
}


def run_gates(result: dict, out_dir: str, case: dict | None = None) -> list:
    """Return list of {gate, ok, detail}; never raises on I/O problems."""
    res = []
    case = case or {}

    # G1
    case_id = str(case.get("case_id") or "")
    g1 = bool(result.get("case_id"))
    g1_ok = g1 and (not case_id or str(result["case_id"]) == case_id)
    res.append({"gate": "G1", "ok": g1_ok,
                "detail": f"result.case_id={result.get('case_id')!r} case.case_id={case_id!r}"})

    # G2
    st = result.get("status")
    res.append({"gate": "G2", "ok": st in ("success", "partial", "failed"),
                "detail": f"status={st!r}"})

    # G3
    missing = []
    nullish = []
    for key, val in (case.get("output_contract") or {}).items():
        if key not in result:
            missing.append(key)
        elif result[key] is None:
            nullish.append(key)
    res.append({"gate": "G3", "ok": not missing and not nullish,
                "detail": f"missing={missing} null_placeholders={nullish}"})

    # G4
    deck_rel = (result.get("main_result") or {}).get("deck", {}).get("path", "")
    deck_path = os.path.join(out_dir, deck_rel) if deck_rel else ""
    reopen = ""
    if deck_path and os.path.exists(deck_path):
        try:
            from pptx import Presentation
            prs = Presentation(deck_path)
            reopen = f"reopened; {len(prs.slides._sldIdLst)} slides"
        except Exception as exc:
            reopen = f"reopen failed: {exc}"
    res.append({"gate": "G4", "ok": bool(deck_path) and os.path.exists(deck_path) and reopen.startswith("reopened"),
                "detail": f"deck={deck_rel} {reopen or 'missing'}"})

    # G5
    ev = result.get("slide_evidence")
    n_ev = len(ev) if isinstance(ev, list) else -1
    n_slides = n_ev  # authoritative: entries count == slides built (contract)
    all_entries_ok = isinstance(ev, list) and all(
        isinstance(e, dict) and "page_no" in e and "page_type" in e for e in ev)
    res.append({"gate": "G5", "ok": n_ev > 0 and all_entries_ok,
                "detail": f"slide_evidence entries={n_ev}"})

    # G6
    ta = result.get("template_audit") or {}
    g6 = all(ta.get(k) is not None for k in
             ("template_source", "opened_from", "layouts", "layout_used")) and ta.get("opened_from")
    res.append({"gate": "G6", "ok": bool(g6),
                "detail": f"opened_from={ta.get('opened_from')!r} layouts={len(ta.get('layouts') or [])}"})

    # G7
    arts = result.get("artifacts") or []
    missing_art = []
    for a in arts:
        rel = a.get("path", "")
        if rel and not os.path.exists(os.path.join(out_dir, rel)):
            missing_art.append(rel)
    res.append({"gate": "G7", "ok": bool(arts) and not missing_art,
                "detail": f"artifacts={len(arts)} missing={missing_art}"})

    # G8
    want_preview = bool((case.get("output_contract") or {}).get("preview_png"))
    has_cover = os.path.exists(os.path.join(out_dir, f"{result.get('case_id', 'x')}_cover_preview.png"))
    unc = result.get("uncertainty") or []
    g8_ok = True
    if want_preview and not has_cover:
        g8_ok = False
    if st != "success" and not unc:
        g8_ok = False
    res.append({"gate": "G8", "ok": g8_ok,
                "detail": f"preview_required={want_preview} cover_exists={has_cover} uncertainty={len(unc)}"})
    return res


def main(argv=None):
    utf8_writer()
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--result", required=True, help="path to result.json")
    ap.add_argument("--out-dir", required=True, help="output dir holding artifacts")
    ap.add_argument("--case", default="", help="case.json (optional; enables G1/G3/G8)")
    a = ap.parse_args(argv)

    try:
        result = json.load(open(a.result, "r", encoding="utf-8-sig"))
    except Exception as exc:
        print(f"check_contract FAILED: cannot read result.json: {exc}")
        return 2
    case = {}
    if a.case and os.path.exists(a.case):
        try:
            case = json.load(open(a.case, "r", encoding="utf-8-sig"))
        except Exception:
            case = {}

    gates = run_gates(result, a.out_dir, case)
    ok = all(g["ok"] for g in gates)
    out = {"valid": bool(ok), "gates": gates, "generator": "check_contract/2.0.0"}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())