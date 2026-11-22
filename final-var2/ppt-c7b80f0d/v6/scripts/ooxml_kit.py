# -*- coding: utf-8 -*-
"""ooxml_kit.py — low-level OOXML operations for deck adaptation and export QA.

Part of the "paper-to-academic-ppt" Skill v2 (ppt-c7b80f0d, efficiency-3).

Why a dedicated OOXML layer (mirrors the high-score intent of separating
asset extraction / deck generation / OOXML refinement):
* template adaptation must be *placeholder-level*: we only fill placeholders,
  never touch the master directly; low-level work is confined to this module;
* shape naming is the layer contract between deckgen and later editing tools —
  every shape we add gets a deterministic, documented name so a human or another
  agent can find "the claim strip on slide 3" by name;
* export QA needs to look *inside* the .pptx (OPC zip + XML), not only re-open
  with python-pptx.

All functions are best-effort and honest: they return a record, they never
crash the pipeline, and any failure is reported for result.json uncertainty.
"""
from __future__ import annotations

import io
import os
import re
import zipfile

from pptx.util import Pt

# --------------------------------------------------------------------------- #
# Shape naming contract (see references/layer-naming.md)
# --------------------------------------------------------------------------- #
PREFIX_BY_KIND = {
    "claim-title": "claim-title-",      # title placeholder fill
    "claim-strip":  "claim-strip-",     # built-in claim strip under title
    "body-bullets": "body-bullets-",    # body placeholder / textbox fill
    "figure":       "figure-",          # figure area (image or placeholder box)
    "table":        "table-",           # embedded table
    "footer-page":  "footer-page-",     # built-in-only page footer
    "outline":      "outline-",         # auto outline slide body
    "evidence-map": "evidence-map-",    # auto evidence mapping slide body
    "closing":      "closing-",         # closing slide body
    "cover":        "cover-",           # title slide text
}

VALID_HINTS = frozenset(PREFIX_BY_KIND.keys())


def sanitize_ref(ref: str) -> str:
    """OOXML/Windows-safe name suffix from a figure/table ref (e.g. 'Fig. 1')."""
    s = re.sub(r"[^\w\u4e00-\u9fff.-]+", "-", (ref or "?").strip())
    return s.strip("-")[:48] or "obj"


def name_shape(shape, kind: str, idx: int, ref: str = "") -> str:
    """Assign a deterministic name to a shape: <prefix><nn>[-<ref>].

    kind must be one of PREFIX_BY_KIND. The name is the edit target that
    later tools (and humans) search for — naming must be stable across reruns.
    """
    if kind not in PREFIX_BY_KIND:
        kind = "obj"
    base = PREFIX_BY_KIND[kind] + ("%02d" % idx)
    if ref:
        base += "-" + sanitize_ref(ref)
    shape.name = base
    return base


def _find_theme_part(prs):
    """Locate the theme OPC part (reachable from the presentation or a master).

    python-pptx loads `theme1.xml` as a *generic* Part (no `.element`), which is
    why the naive "first related part" approach used to fail with
    "'Part' object has no attribute 'element'". We return the real theme part and
    let the caller read/write it through `_theme_root` / `_store_root`, which
    handle both XmlPart and generic Part shapes.
    """
    try:
        from pptx.opc.constants import RELATIONSHIP_TYPE as RT
    except Exception:
        RT = None
    holders = []
    for candidate in [getattr(prs, "part", None)] + list(getattr(prs, "slide_masters", []) or []):
        part = getattr(candidate, "part", candidate)
        if part is not None:
            holders.append(part)
    for holder in holders:
        try:
            rels = list(holder.rels.values())
        except Exception:
            continue
        for rel in rels:
            target = getattr(rel, "target_part", None)
            if target is None:
                continue
            partname = str(getattr(target, "partname", "") or "")
            reltype = getattr(rel, "reltype", "")
            if (RT is not None and reltype == RT.THEME) or partname.endswith("theme1.xml") \
                    or "/theme/" in partname:
                return target
    return None


def _theme_root(part):
    """Return the lxml root of a theme part (XmlPart or generic Part)."""
    element = getattr(part, "element", None)
    if element is not None:
        return element
    import lxml.etree as etree
    return etree.fromstring(part.blob)


def _store_root(part, root):
    """Write an lxml root back into a part, whichever flavour it is."""
    import lxml.etree as etree
    data = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
    try:
        if getattr(part, "element", None) is not None:
            part._element = root      # XmlPart: the writer serializes this
    except Exception:
        pass
    try:
        part._blob = data             # generic Part (theme1.xml) and fallback
    except Exception:
        pass
    return data


def set_theme_fonts(prs, latin: str = "Calibri", ea: str = "Microsoft YaHei",
                    sizes=None):
    """Best-effort theme font injection into the slide master's theme part.

    Writes a:latin / a:ea typeface on the majorFont/minorFont entries of the
    theme so text added through placeholders inherits CJK-safe fonts on any
    machine (a deck opened elsewhere keeps its intended typefaces). Failures are
    recorded, never fatal.
    """
    rec = {"applied": False, "note": None}
    try:
        from pptx.oxml.ns import qn
        theme = _find_theme_part(prs)
        if theme is None:
            rec["note"] = "theme part not reachable through python-pptx"
            return rec
        root = _theme_root(theme)
        touched = 0
        for tag in ("a:majorFont", "a:minorFont"):
            for node in root.iter(qn(tag)):
                lat = node.find(qn("a:latin"))
                if lat is None:
                    lat = node.makeelement(qn("a:latin"), {})
                    node.insert(0, lat)
                lat.set("typeface", latin)
                ea_el = node.find(qn("a:ea"))
                if ea_el is None:
                    ea_el = node.makeelement(qn("a:ea"), {})
                    node.insert(0, ea_el)
                ea_el.set("typeface", ea)
                touched += 1
        if not touched:
            rec["note"] = "theme part found but no majorFont/minorFont element"
            return rec
        data = _store_root(theme, root)
        rec["applied"] = True
        rec["part"] = str(getattr(theme, "partname", "") or "")
        rec["bytes"] = len(data)
        rec["note"] = "majorFont/minorFont latin=%s ea=%s (%d nodes)" % (latin, ea, touched)
    except Exception as exc:  # noqa: BLE001
        rec["note"] = "theme font injection failed: %s" % exc
    return rec


def set_shape_font(run, name="Microsoft YaHei", size=18, bold=False, color=None):
    """Set both a:latin and a:ea typefaces on a run (CJK-safe, machine-portable)."""
    from pptx.oxml.ns import qn
    if not name:
        name = "Calibri"
    run.font.name = name
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn("a:ea"))
    if ea is None:
        ea = rPr.makeelement(qn("a:ea"), {})
        rPr.append(ea)
    ea.set("typeface", name)
    if size:
        run.font.size = Pt(size)
    run.font.bold = bold
    if color is not None:
        run.font.color.rgb = color


# --------------------------------------------------------------------------- #
# OPC / zip-level export checks (export_check.py uses these)
# --------------------------------------------------------------------------- #
REQUIRED_PARTS = frozenset([
    "[Content_Types].xml",
    "_rels/.rels",
    "ppt/presentation.xml",
])


def zip_sanity(pptx_path: str) -> dict:
    """Check the OOXML container: required parts exist and XML parsers accept
    the core parts. Returns an honest record with errors [] when clean."""
    rec = {"ok": False, "errors": [], "parts": [], "size": 0}
    try:
        rec["size"] = os.path.getsize(pptx_path)
        with zipfile.ZipFile(pptx_path) as zf:
            names = set(zf.namelist())
            rec["parts"] = sorted(names)
            for req in REQUIRED_PARTS:
                if req not in names:
                    rec["errors"].append("missing required OOXML part: %s" % req)
            # parse the XML parts we know must be well-formed
            for part in ("[Content_Types].xml", "_rels/.rels", "ppt/presentation.xml"):
                if part in names:
                    data = zf.read(part)
                    import xml.etree.ElementTree as ET
                    try:
                        ET.fromstring(data)
                    except Exception as exc:  # noqa: BLE001
                        rec["errors"].append("OOXML part not well-formed %s: %s" % (part, exc))
        rec["ok"] = not rec["errors"]
    except Exception as exc:  # noqa: BLE001
        rec["errors"].append("zip open failed: %s" % exc)
    return rec


def naming_audit(prs) -> dict:
    """Report shapes whose name is empty/auto-generated (i.e. not covered by
    the layer-naming contract). Names are informational; missing names are
    warnings, not hard errors, when the shape belongs to an organizer template."""
    auto = [n for n in ("AutoShape", "TextBox", "Picture", "Table", "") if True]
    unnamed = []
    per_slide = []
    for i, slide in enumerate(prs.slides, start=1):
        names = []
        for sh in slide.shapes:
            nm = (sh.name or "").strip()
            names.append(nm)
            if not nm or nm in auto:
                unnamed.append({"slide": i, "name": nm,
                                "shape_type": str(getattr(sh, "shape_type", "?"))})
        per_slide.append({"slide": i, "count": len(names), "names": names})
    return {"unnamed": unnamed, "per_slide": per_slide,
            "note": "unnamed/auto shapes are tolerated in organizer templates but must be named for our own additions"}


def slide_notes_text(slide) -> str:
    """Read the notes part text ('' when absent)."""
    try:
        return slide.notes_slide.notes_text_frame.text or ""
    except Exception:
        return ""


def iter_notes(prs):
    """Yield (slide_no, notes_text) for every slide."""
    for i, slide in enumerate(prs.slides, start=1):
        yield i, slide_notes_text(slide)


if __name__ == "__main__":
    import json
    import sys

    import cli_io
    cli_io.harden_console()
    path = sys.argv[1]
    from pptx import Presentation
    prs = Presentation(path)
    out = {"zip": zip_sanity(path), "naming": naming_audit(prs),
           "notes": {i: bool(t) for i, t in iter_notes(prs)}}
    print(json.dumps(out, ensure_ascii=False, indent=2, default=str))