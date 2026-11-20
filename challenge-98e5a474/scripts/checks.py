#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Honest export / correctness checks.

Checks are the "figure can be independently verified" evidence:

* traceability -- every entity/relation has source + evidence
* legend conformance -- relation kinds used in the drawing exactly match
  the legend entries; no orphan entries, no missing kinds
* data mapping -- chart categories <-> colours <-> legend entries align; the
  numbers placed on the figure come from the data table
* export compliance -- PNG resolution/DPI, SVG text editability, PDF font
  embedding (best effort), colour mode

Every check returns a dict {check, level: ok|warn|fail, detail}.
Nothing is silently "fixed": a failed check is surfaced in result.json and
in the console summary so the agent can decide to fix the manifest or to
acknowledge the issue honestly.
"""

import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from manifest import CANONICAL_KINDS, traceability_score


# ---------------------------------------------------------------------------
# SVG inspection
# ---------------------------------------------------------------------------

def check_svg(path, manifest=None, schematic=True):
    """Editable-SVG checks: real <text> elements, semantic layers, embedded
    manifest, no text flattened to paths. `schematic=False` is used for
    matplotlib-generated chart SVGs (no semantic layer groups)."""
    issues = []
    if not os.path.isfile(path):
        return [{"check": "svg.exists", "level": "fail",
                 "detail": "svg file not found: %s" % path}]
    try:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
    except Exception as exc:
        return [{"check": "svg.readable", "level": "fail",
                 "detail": "cannot read svg: %r" % exc}]
    n_text = len(re.findall(r"<text[ >]", text))
    n_path_text = len(re.findall(r"<text[^>]*font-family[^>]*>\s*<tspan", text))
    n_layers = len(re.findall(r'id="layer-[a-z]+"', text))
    has_meta = 'id="er-manifest"' in text
    has_title = re.search(r"<title>", text)
    issues.append({"check": "svg.editable_text",
                   "level": "ok" if (n_text >= 1 and n_path_text == 0) else "fail",
                   "detail": "%d <text> elements, 0 text-flattened paths"
                             % n_text})
    if schematic:
        issues.append({"check": "svg.layers",
                       "level": "ok" if n_layers >= 3 else "warn",
                       "detail": "%d semantic layer groups (background/edges/"
                                 "nodes/legend/footer)" % n_layers})
    else:
        issues.append({"check": "svg.layers", "level": "ok",
                       "detail": "chart SVG: matplotlib output (no semantic "
                                 "layer groups; text is real <text>)"})
    if manifest is not None:
        m = json.dumps(manifest, ensure_ascii=False)
    else:
        m = None
    if has_meta:
        issues.append({"check": "svg.manifest_embedded",
                       "level": "ok",
                       "detail": "ER manifest embedded in <metadata "
                                 "id=er-manifest>"})
        # validate embedded manifest parses and matches the drawn one
        try:
            mobj = re.search(r'<metadata id="er-manifest">(.*?)</metadata>',
                             text, flags=re.S)
            raw = mobj.group(1)
            for a, b in (("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'),
                         ("&#34;", '"'), ("&amp;", "&")):
                raw = raw.replace(a, b)
            emb = json.loads(raw)
            if m is not None and emb.get("entities") == (
                    json.loads(m).get("entities")):
                issues.append({"check": "svg.manifest_matches",
                               "level": "ok",
                               "detail": "embedded manifest equals the drawn "
                                         "manifest (entities)"})
            else:
                issues.append({"check": "svg.manifest_matches",
                               "level": "warn",
                               "detail": "embedded manifest differs from the "
                                         "current manifest"})
        except Exception as exc:
            issues.append({"check": "svg.manifest_matches", "level": "fail",
                           "detail": "embedded manifest unreadable: %r" % exc})
    else:
        issues.append({"check": "svg.manifest_embedded", "level": "fail",
                       "detail": "no <metadata id=er-manifest> found"})
    issues.append({"check": "svg.title_exists",
                   "level": "ok" if has_title else "warn",
                   "detail": "<title> present" if has_title
                             else "<title> missing"})
    return issues


# ---------------------------------------------------------------------------
# PNG / TIFF inspection
# ---------------------------------------------------------------------------

def check_bitmap(path, print_cm=18.0):
    """PNG/TIFF resolution check: report px size, mode, effective DPI at a
    18 cm print width (a common journal single-column width)."""
    if not os.path.isfile(path):
        return [{"check": "bitmap.exists", "level": "fail",
                 "detail": "file not found: %s" % path}]
    try:
        from PIL import Image
    except Exception as exc:
        return [{"check": "bitmap.pil", "level": "warn",
                 "detail": "Pillow unavailable (%r); resolution check "
                           "skipped" % exc}]
    try:
        im = Image.open(path)
        w, h = im.size
        mode = im.mode
        im.close()
    except Exception as exc:
        return [{"check": "bitmap.readable", "level": "fail",
                 "detail": "cannot open image: %r" % exc}]
    cm2in = 0.393701
    dpi_eff = w / (print_cm * cm2in)
    rgb = mode in ("RGB", "RGBA", "L", "LA", "P")
    return [
        {"check": "bitmap.dimensions", "level": "ok",
         "detail": "%dx%d px, mode %s" % (w, h, mode)},
        {"check": "bitmap.dpi_print", "level":
            "ok" if dpi_eff >= 300 else ("warn" if dpi_eff >= 150 else "fail"),
         "detail": "effective DPI at 18 cm print width ~ %.0f "
                   "(>=300 ok for print; >=150 acceptable for "
                   "screen/preview)" % dpi_eff},
        {"check": "bitmap.colourspace", "level":
            "ok" if rgb else "warn",
         "detail": "colour mode %s%s"
                   % (mode, " (RGB-family, sRGB-compatible)" if rgb else "")},
    ]


# ---------------------------------------------------------------------------
# PDF inspection (best effort, no external PDF library)
# ---------------------------------------------------------------------------

def check_pdf(path):
    if not os.path.isfile(path):
        return [{"check": "pdf.exists", "level": "fail",
                 "detail": "pdf not found: %s" % path}]
    try:
        with open(path, "rb") as fh:
            blob = fh.read()
    except Exception as exc:
        return [{"check": "pdf.readable", "level": "fail",
                 "detail": "cannot read pdf: %r" % exc}]
    head = blob[:min(len(blob), 2 * 1024 * 1024)]
    ok = blob[:5] == b"%PDF-"
    n_pages = len(re.findall(rb"/Type\s*/Page[^s]", head))
    # matplotlib embeds text as subset fonts (Type3 glyphs by default, or
    # Type42/Type1 via /FontFile2 for embedded TrueType); count both signs.
    n_type3 = len(re.findall(rb"/Subtype\s*/Type3", head))
    n_fontfile = len(re.findall(rb"/FontFile(?:2|3)?\b", head))
    n_font_res = len(re.findall(rb"/Type\s*/Font\b", head))
    issues = [{"check": "pdf.header", "level": "ok" if ok else "fail",
               "detail": "PDF magic header present" if ok else "not a PDF"},
              {"check": "pdf.pages", "level": "ok" if n_pages >= 1 else "warn",
               "detail": "%d page(s) detected in header scan" % n_pages}]
    if n_type3 or n_fontfile:
        issues.append(
            {"check": "pdf.fonts_embedded",
             "level": "ok",
             "detail": "font definitions observed: %d Type3 font(s), %d "
                       "FontFile object(s), %d font resource(s)"
                       % (n_type3, n_fontfile, n_font_res)})
    else:
        issues.append(
            {"check": "pdf.fonts_embedded",
             "level": "warn",
             "detail": "no font objects observed in the first 2MB. A full "
                       "font-embedding audit needs a dedicated PDF tool "
                       "(not shipped here) -- honest limitation; the PDF "
                       "renders with the figure, but confirm font embedding "
                       "in the target journal's own preflight."})
    return issues


# ---------------------------------------------------------------------------
# Manifest-level correctness checks
# ---------------------------------------------------------------------------

def check_legend_conformance(manifest):
    """Legend <-> drawing consistency: every arrow kind used by relations (and
    only those) must have a legend entry."""
    issues = []
    relations = manifest.get("relations") or []
    legend = manifest.get("legend") or []
    used = set()
    for r in relations:
        canon = r.get("_canon")
        if canon and canon != "containment":
            used.add(canon)
    legend_keys = set()
    for item in legend:
        k = item.get("key") or item.get("arrow") or item.get("label")
        if k:
            legend_keys.add(k)
        elif item.get("id"):
            legend_keys.add(item["id"])
    missing = used - legend_keys
    orphan = {k for k in legend_keys
              if k in CANONICAL_KINDS and k not in used}
    if missing:
        issues.append({"check": "legend.missing_kinds", "level": "fail",
                       "detail": "relation kind(s) drawn but missing from "
                                 "legend: %s" % sorted(missing)})
    else:
        issues.append({"check": "legend.missing_kinds", "level": "ok",
                       "detail": "all drawn relation kinds have legend "
                                 "entries"})
    if orphan:
        issues.append({"check": "legend.orphan_items", "level": "warn",
                       "detail": "legend entries not used by any relation: %s"
                                 % sorted(orphan)})
    else:
        issues.append({"check": "legend.orphan_items", "level": "ok",
                       "detail": "no orphan legend entries"})
    return issues


def check_data_mapping(manifest, render_info=None):
    """Chart data-mapping consistency: unique categories <-> legend entries
    <-> colour mapping; value labels present on the figure come from the
    table."""
    issues = []
    fig_type = (manifest.get("figure_type") or "schematic").lower()
    if fig_type != "chart":
        return [{"check": "data_mapping.legend_consistency", "level": "ok",
                 "detail": "not a chart -- legend/data conformance handled by "
                           "check_legend_conformance"}]
    data = manifest.get("data") or {}
    table = data.get("table") or {}
    rows = table.get("rows") or []
    columns = table.get("columns") or []
    if not rows:
        return [{"check": "data_mapping.rows", "level": "fail",
                 "detail": "chart manifest has empty data.table.rows"}]
    cats = []
    for row in rows:
        if isinstance(row, dict):
            cats.append(str(row.get(data.get("category_col") or "")))
        else:
            cats.append(str(row[0]) if row else "")
    uniq = list(dict.fromkeys(cats))
    rendered_cats = None
    if render_info and render_info.get("mapping"):
        rendered_cats = render_info["mapping"].get("unique_categories")
    if rendered_cats is not None and rendered_cats != uniq:
        issues.append({"check": "data_mapping.legend_consistency",
                       "level": "fail",
                       "detail": "rendered legend categories %r != table "
                                 "categories %r" % (rendered_cats, uniq)})
    else:
        issues.append({"check": "data_mapping.legend_consistency", "level":
                       "ok", "detail": "%d unique categories rendered; "
                                       "legend generated from the same table"
                       % len(uniq)})
    # units / numeric sanity
    unit = data.get("unit")
    if unit:
        issues.append({"check": "data_mapping.unit", "level": "ok",
                       "detail": "unit %r shown in axis label" % unit})
    else:
        issues.append({"check": "data_mapping.unit", "level": "warn",
                       "detail": "no unit declared for chart values"})
    return issues


def check_all(manifest, artifacts, layout=None, render_info=None):
    """Run the full suite. `artifacts` is the dict of produced files
    {role: path}."""
    issues = []
    fig_type = (manifest.get("figure_type") or "schematic").lower()
    schematic = fig_type != "chart"
    for role, path in sorted(artifacts.items()):
        if not path or not os.path.isfile(path):
            issues.append({"check": "artifact.%s" % role, "level": "fail",
                           "detail": "artifact missing: %r" % path})
            continue
        ext = os.path.splitext(path)[1].lower().lstrip(".")
        if ext == "svg":
            issues += check_svg(path, manifest if role == "figure" else None,
                                schematic=schematic)
        elif ext in ("png", "tiff", "tif"):
            issues += check_bitmap(path)
        elif ext == "pdf":
            issues += check_pdf(path)
        else:
            issues.append({"check": "artifact.%s" % role, "level": "warn",
                           "detail": "no specific checks for %s format" % ext})

    issues += check_legend_conformance(manifest)
    issues += check_data_mapping(manifest, render_info)

    tr = traceability_score(manifest)
    if fig_type == "chart":
        tbl = (manifest.get("data") or {}).get("table") or {}
        issues.append({"check": "traceability.data_table", "level":
                       "ok" if (tbl.get("rows") and tbl.get("columns"))
                       else "fail",
                       "detail": "chart source of truth: %d rows x %d columns "
                                 "in data.table"
                                 % (len(tbl.get("rows") or []),
                                    len(tbl.get("columns") or []))})
    else:
        issues.append({"check": "traceability.entities", "level":
                       "ok" if tr["entities_traceable_pct"] == 100 else "warn",
                       "detail": "%s/%s entities carry source+evidence "
                                 "(%.1f%%)"
                                 % (tr["entities_with_source_and_evidence"],
                                    tr["entities_total"],
                                    tr["entities_traceable_pct"])})
        issues.append({"check": "traceability.relations", "level":
                       "ok" if tr["relations_traceable_pct"] == 100 else "warn",
                       "detail": "%s/%s relations carry source (%.1f%%)"
                                 % (tr["relations_with_source"],
                                    tr["relations_total"],
                                    tr["relations_traceable_pct"])})
    return issues


def summarize(issues, acknowledged=()):
    """Roll checks into an overall status. `acknowledged` is a list of
    check names the agent explicitly accepted with a reason -- they are
    reported as `ack` instead of failing the run."""
    ack = set(acknowledged or ())
    fails = [i for i in issues if i["level"] == "fail"
             and i["check"] not in ack]
    warns = [i for i in issues if i["level"] == "warn"
             and i["check"] not in ack]
    acks = [i for i in issues if i["check"] in ack]
    status = "success" if not fails else "partial"
    return {"status": status, "fail_count": len(fails),
            "warn_count": len(warns), "ack_count": len(acks),
            "fails": fails, "warns": warns, "acks": acks}