# -*- coding: utf-8 -*-
"""pptx_toolkit.py — shared PPTX template/geometry helpers (v2).

Pure helpers shared by the two-phase workflow:
  * adopt_plan.py  (phase 1: analyse template + produce adaptation plan)
  * adapt_pptx.py  (phase 2: apply the plan, build the editable deck)

Keeps every PPTX decision deterministic and documented — the same input must
produce the same layout assignment and the same geometry, so a reviewer can
re-run the record page by page.  Everything here is a pure function of the
opened Presentation object; no I/O to the skill directories.
"""
from __future__ import annotations

import os
import shutil
import zipfile
import xml.etree.ElementTree as ET

from common import emu_to_pt

# Roles a page type may require from a layout.
ROLES_COVER = ("title", "subtitle")
ROLES_DEFAULT = ("title", "body")

DRAWINGML_NS = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}


# --------------------------------------------------------------------------
# Placeholder introspection -------------------------------------------------
def ph_fragments(ph) -> list:
    """Collect searchable fragments of a placeholder: name, idx, compact name."""
    name = ""
    try:
        name = ph.name or ""
    except Exception:
        pass
    idx = -1
    try:
        idx = ph.placeholder_format.idx if ph.has_placeholder_fmt else -1
    except Exception:
        idx = -1
    frags = [name.lower(), str(idx)]
    if name:
        frags.append(name.lower().replace(" ", ""))
    return frags


def has_any(frags, patterns) -> bool:
    return any(p in f for f in frags for p in patterns)


def layout_scores(prs) -> list:
    """Enumerate masters/layouts/placeholders — the raw inheritance record."""
    out = []
    for li, layout in enumerate(prs.slide_layouts):
        phs = []
        mname = ""
        try:
            mname = layout.slide_master.name or ""
        except Exception:
            mname = ""
        try:
            for ph in layout.placeholders:
                w = h = None
                try:
                    w, h = ph.width, ph.height
                except Exception:
                    pass
                phs.append({"idx": ph.placeholder_format.idx,
                            "name": getattr(ph, "name", None) or "", "w": w, "h": h})
        except Exception:
            phs = []
        out.append({"idx": li, "name": layout.name or f"layout-{li}", "master": mname,
                    "placeholders": phs})
    return out


def layout_fragments(prs, layout) -> list:
    frags = []
    try:
        for ph in layout.placeholders:
            frags.extend(ph_fragments(ph))
    except Exception:
        pass
    return [str(f).lower() for f in frags]


def body_placeholders(prs, layout) -> list:
    """Placeholders treated as a real content body (not side 'text' columns)."""
    out = []
    try:
        for ph in layout.placeholders:
            f = [str(x).lower() for x in ph_fragments(ph)]
            if has_any(f, ("content", "body", "object", "内容")):
                out.append(ph)
    except Exception:
        pass
    return out


def master_name(layout) -> str:
    try:
        return layout.slide_master.name or ""
    except Exception:
        return ""


def best_layout(prs, page_type: str) -> tuple:
    """Pick the layout that truly provides the requested placeholder roles.

    'text' placeholders (Section Header side texts, Comparison side texts) are
    NOT treated as content body; full-width single-body layouts are preferred
    so text is not squeezed into narrow columns.

    Returns (layout, matched, detail, fallback) where:
      matched  = 2 (strong) / 1 (weak) / 0 (none)
      fallback = matched < 2 (manual text box likely)
    """
    best = None
    best_idx = -1
    best_score = -1.0
    for idx, layout in enumerate(prs.slide_layouts):
        frags = layout_fragments(prs, layout)
        has_title = has_any(frags, ("title", "标题"))
        has_sub = has_any(frags, ("subtitle", "副标题"))
        bodies = body_placeholders(prs, layout)
        if page_type in ("cover", "thankyou"):
            score = 0.0
            if has_title and has_sub:
                score += 1000.0
            elif has_title:
                score += 500.0
            score += min(len(getattr(layout, "placeholders", [])), 12)
        else:
            if not (has_title and bodies):
                score = 0.0
            else:
                score = 1000.0
                if len(bodies) == 1:
                    score += 300.0          # single content body (preferred)
                else:
                    score += 30.0           # split bodies: usable but discouraged
                try:
                    sw = prs.slide_width
                    best_bw = max((b.width or 0) for b in bodies)
                    if sw and best_bw and best_bw >= sw * 0.5:
                        score += 200.0      # full-width body
                except Exception:
                    pass
                score += min(len(getattr(layout, "placeholders", [])), 12)
        if score > best_score:
            best_score = score
            best = layout
            best_idx = idx
    matched = 2 if best_score >= 800 else (1 if best_score > 0 else 0)
    name = best.name or f"layout-{best_idx}"
    detail = f"layout='{name}' (idx~{best_idx}) master='{master_name(best)}'"
    return best, matched, detail, matched < 2


def layout_provides(prs, layout, roles) -> tuple:
    """Check a layout provides the roles; returns (ok, missing_roles)."""
    frags = layout_fragments(prs, layout)
    missing = []
    for role in roles:
        if role == "title":
            ok = has_any(frags, ("title", "标题"))
        elif role == "subtitle":
            ok = has_any(frags, ("subtitle", "副标题"))
        else:  # body
            ok = bool(body_placeholders(prs, layout))
        if not ok:
            missing.append(role)
    return (not missing), missing


def find_ph(slide_or_layout, *patterns):
    """Find a placeholder whose name/idx contains any pattern (case-insensitive)."""
    for ph in getattr(slide_or_layout, "placeholders", []):
        frags = ph_fragments(ph)
        for pat in patterns:
            for f in frags:
                if pat and pat.lower() in str(f).lower():
                    return ph
    return None


# --------------------------------------------------------------------------
# Geometry ------------------------------------------------------------------
def contain_fit(img_w: int, img_h: int, box_w_emu: int, box_h_emu: int) -> tuple:
    """Return (w_emu, h_emu, scale) preserving aspect ratio (contain-fit)."""
    if img_w <= 0 or img_h <= 0 or box_w_emu <= 0 or box_h_emu <= 0:
        return box_w_emu, box_h_emu, 1.0
    scale = min(box_w_emu / img_w, box_h_emu / img_h)
    return int(img_w * scale), int(img_h * scale), scale


def col_widths(n_cols: int, width_pt: float) -> list:
    return [width_pt / n_cols] * n_cols


def drop_slides(prs) -> int:
    """Remove every existing slide (starting-deck edit mode); returns removed count."""
    xml_slides = prs.slides._sldIdLst
    slides = list(xml_slides)
    for s in slides:
        xml_slides.remove(s)
    return len(slides)


def deterministic_zip(src: str, tmp: str) -> None:
    """Rewrite the saved pptx as a zip with fixed entry timestamps so the same
    input produces byte-identical pptx (content bytes are already a pure
    function of the plan; only zip entry dates varied run-to-run)."""
    with zipfile.ZipFile(src, "r") as zin, \
         zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            n = zipfile.ZipInfo(item.filename, date_time=(1980, 1, 1, 0, 0, 0))
            n.compress_type = zipfile.ZIP_DEFLATED
            n.comment = item.comment
            zout.writestr(n, zin.read(item.filename))
    shutil.move(tmp, src)


# --------------------------------------------------------------------------
# Theme introspection (best-effort, from the package XML) -------------------
def read_theme(prs_path: str) -> dict:
    """Read theme fonts + colour scheme from ppt/theme/theme1.xml.

    Returns {"latin_font", "ea_font", "accent_colors", "error"} — everything
    best-effort; a missing/corrupt theme never aborts the pipeline.
    """
    out = {"latin_font": None, "ea_font": None, "accent_colors": [], "error": None}
    try:
        with zipfile.ZipFile(prs_path) as z:
            names = [n for n in z.namelist() if n.startswith("ppt/theme/") and n.endswith(".xml")]
            if not names:
                out["error"] = "no theme xml in package"
                return out
            root = ET.fromstring(z.read(names[0]))

        def _find(path):
            el = root.find(path, DRAWINGML_NS)
            return el.get("typeface") if el is not None else None

        out["latin_font"] = _find(".//a:fontScheme/a:majorFont/a:latin") or \
            _find(".//a:fontScheme/a:minorFont/a:latin")
        out["ea_font"] = _find(".//a:fontScheme/a:majorFont/a:ea") or \
            _find(".//a:fontScheme/a:minorFont/a:ea")

        clr = root.find(".//a:clrScheme", DRAWINGML_NS)
        if clr is not None:
            for child in clr:
                val = None
                sc = child.find("a:srgbClr", DRAWINGML_NS)
                if sc is not None:
                    val = sc.get("val")
                if val is None:
                    sysc = child.find("a:sysClr", DRAWINGML_NS)
                    if sysc is not None:
                        val = sysc.get("lastClr") or sysc.get("val")
                if val:
                    out["accent_colors"].append({"name": child.tag.split("}")[-1], "value": val})
    except Exception as exc:  # pragma: no cover - best effort
        out["error"] = f"theme read failed: {exc}"
    return out


# --------------------------------------------------------------------------
# Template resolution -------------------------------------------------------
def resolve_template(template_path: str, starting_deck: str,
                     builtin_template: str, limit_label: str | None = None) -> tuple:
    """Open the first usable template in the chain:
    case template -> starting deck -> builtin.

    Returns (prs, opened_from, source_path, errors).  Raises RuntimeError when
    every candidate fails (main.py converts to an honest failed result.json).
    """
    candidates = []
    if limit_label in (None, "case_template") and template_path and os.path.exists(template_path):
        candidates.append(("case_template", template_path))
    if limit_label in (None, "starting_deck") and starting_deck and os.path.exists(starting_deck):
        candidates.append(("starting_deck", starting_deck))
    if builtin_template and os.path.exists(builtin_template):
        candidates.append(("builtin", builtin_template))

    errors = []
    for label, path in candidates:
        try:
            from pptx import Presentation
            prs = Presentation(path)
            return prs, label, path, errors
        except Exception as exc:
            errors.append(f"{label}: {exc}")
    raise RuntimeError(
        "no usable template (case template / starting deck / builtin all failed): "
        + "; ".join(errors or ["no candidate templates at all"]))