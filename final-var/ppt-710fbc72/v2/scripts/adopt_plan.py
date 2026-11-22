# -*- coding: utf-8 -*-
"""adopt_plan.py — two-phase workflow, phase 1: build the ADAPTATION PLAN.

Reads the extracted content + the deterministic page plan (spec.json) and the
real template file, then produces adopt_plan.json — the machine-readable
"adaptation plan" that states, *before any slide is built*:

  * template structure audit: masters / layouts / placeholders / slide size /
    theme fonts + accent colours (the "inheritance is inspectable" record);
  * page -> layout assignment: which layout serves each page type and which
    placeholder roles it provides (or why a fallback is needed);
  * batch rules evaluation: uniform footer/page numbers/title position/font
    ladder per the whole deck, with deviations recorded, not hidden;
  * figure placement plan: which figure goes to which page and the
    contain-fit scale against the real content region.

adopt_plan.json is consumed by adapt_pptx.py (phase 2); the consistency
between "planned" and "actually applied" layouts is audited after the build.
This phase is a pure function of (content, spec, template) — no timestamps,
so two runs produce byte-identical plans.
"""
from __future__ import annotations

import os

from common import (dump_json, load_json, utf8_writer, SKILL_NAME, SKILL_VERSION,
                    portable_path)
import pptx_toolkit as tk

_VERSION = "2.0.0"


def _page_roles(page_type: str) -> tuple:
    return tk.ROLES_COVER if page_type in ("cover", "thankyou") else tk.ROLES_DEFAULT


def build_plan(content: dict, spec: dict, template_path: str = "",
               starting_deck: str = "", builtin_template: str = "",
               limit_label: str | None = None, meta: str = "") -> dict:
    """Analyse template + plan; return adopt_plan dict (deterministic)."""
    tpl_path = template_path or content.get("template_path") or ""
    sdeck = starting_deck or content.get("starting_deck_path") or ""

    prs, opened_from, source, tpl_errors = tk.resolve_template(
        tpl_path, sdeck, builtin_template, limit_label)
    try:
        sw, sh = prs.slide_width, prs.slide_height
    except Exception:
        sw, sh = 0, 0

    layouts = tk.layout_scores(prs)
    theme = tk.read_theme(source)
    source_record = portable_path(source)      # recorded portably, never a host path

    lang = content.get("language") or "zh"

    # ---- page -> layout assignment --------------------------------------
    pages = spec.get("pages") or []
    assignments = []
    gaps = []
    for p in pages:
        pt = p["page_type"]
        roles = _page_roles(pt)
        try:
            layout, matched, detail, fallback = tk.best_layout(prs, pt)
            lidx = -1
            lname = ""
            mname = ""
            if layout is not None:
                try:
                    lidx = [prs.slide_layouts.index(x) for x in [layout]][0]
                except Exception:
                    for i, x in enumerate(prs.slide_layouts):
                        if x is layout:
                            lidx = i
                            break
                if lidx < 0:
                    lidx = [i for i, l in enumerate(prs.slide_layouts)
                            if l.name == layout.name][0] if layout.name else -1
                lname = layout.name or f"layout-{lidx}"
                mname = tk.master_name(layout)
            roles_ok, missing = tk.layout_provides(prs, layout, roles)
            if not roles_ok:
                gaps.append({"page_no": p["page_no"], "page_type": pt,
                             "missing_roles": missing, "layout": lname})
            assignments.append({
                "page_no": p["page_no"],
                "page_type": pt,
                "title": p.get("title", ""),
                "recommended_layout_idx": lidx,
                "layout_name": lname,
                "master": mname,
                "roles_required": list(roles),
                "roles_provided": roles_ok,
                "roles_available": [] if roles_ok else list(missing),
                "matched": matched,
                "fallback_needed": fallback,
                "detail": detail,
            })
        except Exception as exc:  # pragma: no cover
            gaps.append({"page_no": p["page_no"], "page_type": pt, "error": str(exc)})
            assignments.append({"page_no": p["page_no"], "page_type": pt,
                                "title": p.get("title", ""),
                                "recommended_layout_idx": -1, "layout_name": "",
                                "master": "", "roles_required": list(roles),
                                "roles_provided": False, "roles_available": list(roles),
                                "matched": 0, "fallback_needed": True,
                                "detail": f"error: {exc}"})

    # ---- batch rules (whole-deck uniformity, with deviations recorded) ---
    body_budget = max(spec.get("target_slides") or 0, len(pages))
    batch_notes = {
        "footer": "uniform footer text (deck title, <=45 chars) on every non-cover page",
        "page_numbers": "right-bottom page number on every non-cover page",
        "title_position": "title placeholder on every non-cover page; manual text box only when placeholder missing (recorded)",
        "font_ladder": "32 -> 28 -> 26 -> 24 -> 22 -> 20 -> 18 -> 16 -> 14 -> 12 pt; floor 12pt; overflow reported, never shrunk below floor",
        "figure_rule": "contain-fit only (never stretch); caption `图N 标题 [来源: loc]`",
        "slide_budget": f"planned {len(pages)} slides against target {spec.get('target_slides')}",
    }
    deviations = []
    planned = len(pages)
    target = spec.get("target_slides") or 0
    if target and planned > target:
        deviations.append({"rule": "slide_budget",
                           "note": f"planned {planned} > target {target}; deckplan trim policy already applied, remaining gap disclosed"})
    for a in assignments:
        if a.get("fallback_needed"):
            deviations.append({"rule": "layout_fallback",
                               "note": f"page {a['page_no']} ({a['page_type']}): layout fallback - {a.get('detail', '')}"})
    if theme.get("error"):
        deviations.append({"rule": "theme", "note": f"theme read error: {theme['error']}"})

    # ---- figure placement plan (contain-fit against real content region) --
    figure_plan = []
    try:
        body_dims = {"w": 0, "h": 0}
        for p in pages:
            if p["page_type"] == "results" and (p.get("figures_on_page") or []):
                for f in p["figures_on_page"]:
                    fpath = f.get("file") or ""
                    iw = ih = 0
                    if f.get("exists") and fpath and os.path.exists(fpath):
                        try:
                            from PIL import Image
                            with Image.open(fpath) as im:
                                iw, ih = im.size
                        except Exception:
                            iw = ih = 0
                    # nominal body region: body placeholder of the recommended layout
                    bw = bh = 6858000
                    lidx = next((a["recommended_layout_idx"] for a in assignments
                                 if a["page_no"] == p["page_no"]), -1)
                    if 0 <= lidx < len(prs.slide_layouts):
                        body = tk.find_ph(prs.slide_layouts[lidx], "content", "body", "object", "内容")
                        if body is not None:
                            bw = body.width or bw
                            bh = body.height or bh
                    scale = 1.0
                    if iw > 0 and ih > 0 and bw > 0 and bh > 0:
                        scale = round(min(bw / iw, bh / ih), 4)
                    figure_plan.append({
                        "fig_id": f.get("id", ""),
                        "page_no": p["page_no"],
                        "page_type": p["page_type"],
                        "source": f.get("source", ""),
                        "file_exists": bool(f.get("exists")),
                        "image_size": [iw, ih],
                        "container_emu": [int(bw), int(bh)],
                        "contain_scale_preview": scale,
                        "aspect_preserved": True,
                        "action": "embed" if f.get("exists") else "placeholder_box",
                    })
    except Exception as exc:  # pragma: no cover
        deviations.append({"rule": "figure_plan", "note": str(exc)})

    # ---- gates (CP1) -------------------------------------------------------
    layout_gaps = len([g for g in gaps])
    batch_bad = len([d for d in deviations if d["rule"] != "figure_plan"])
    gates = {
        "G1_template_open": bool(source),
        "G2_layouts_enumerated": len(layouts) > 0,
        "G3_every_page_has_layout": layout_gaps == 0,
        "G4_batch_rules_ok_or_disclosed": True,   # deviations are disclosed below, never hidden
        "ok": bool(source) and len(layouts) > 0 and layout_gaps == 0,
    }

    plan = {
        "_meta": meta or "adaptation plan (two-phase workflow, phase 1); template structure audit + page->layout assignment + batch rules + figure placement",
        "generator": f"{SKILL_NAME}/{_VERSION}",
        "case_id": content.get("case_id") or spec.get("case_id") or "",
        "language": lang,
        "template": {
            "source": source_record,
            "opened_from": opened_from,
            "slide_size_emu": [int(sw), int(sh)],
            "theme": theme,
            "errors": tpl_errors,
        },
        "layouts": layouts,
        "page_assignments": assignments,
        "layout_gaps": gaps,
        "batch": {"rules": batch_notes, "deviations": deviations},
        "figure_plan": figure_plan,
        "gates": gates,
    }
    return plan


def main(argv=None):
    utf8_writer()
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--content", required=True, help="content.json from extract.py")
    ap.add_argument("--spec", required=True, help="spec.json from deckplan.py")
    ap.add_argument("--template", default="", help="explicit template pptx")
    ap.add_argument("--starting-deck", default="", help="explicit starting deck")
    ap.add_argument("--builtin", default="", help="builtin fallback template path")
    ap.add_argument("--limit", default="", help="limit chain: case_template|starting_deck|builtin")
    ap.add_argument("--meta", default="", help="optional _meta label (e.g. example marker)")
    ap.add_argument("--out", required=True, help="output adopt_plan.json path")
    a = ap.parse_args(argv)

    content = load_json(a.content)
    spec = load_json(a.spec)
    plan = build_plan(content, spec, a.template, a.starting_deck, a.builtin,
                      limit_label=a.limit or None, meta=a.meta)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    dump_json(a.out, plan)
    print(f"adopt-plan ok: pages={len(plan['page_assignments'])} "
          f"gaps={len(plan['layout_gaps'])} batch_deviations={len(plan['batch']['deviations'])} "
          f"opened_from={plan['template']['opened_from']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())