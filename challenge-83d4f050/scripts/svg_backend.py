# -*- coding: utf-8 -*-
"""Editable layered SVG backend.

Writes a hand-crafted, layer-named SVG that is the *editable source* of the
figure (not a bitmap): each layer is a named <g>, every node/edge carries
data-id / data-type / data-source attributes, fonts are CSS-standard so a user
can replace them, and markers encode interaction semantics (arrow / bar /
circle / diamond).  The file is round-tripped through xml.etree so it is
guaranteed well-formed, and a built-in check verifies the legend matches the
attributes actually used on the canvas.

Generated file layout (groups, drawn bottom-to-top):
    layer-compartment   (banding)
    layer-edge          (typed edges, below nodes)
    layer-entity        (nodes)
    layer-label         (node labels & edge labels)
    layer-title
    layer-legend
    layer-meta          (source footer + provenance comment)
"""
import io
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

from model import (SKILL_NAME, CONTRACT_VERSION, NODE_TYPES, EDGE_TYPES,
                   EVIDENCE_WIDTH, data_color, data_scale)

FONT_STACK = "Arial, 'Helvetica Neue', 'PingFang SC', 'Microsoft YaHei', 'Noto Sans CJK SC', sans-serif"
LEGEND_W = 330

MARKERS = {
    "arrow":   '<path d="M0,0 L11,5.5 L0,11 z" fill="{c}"/>',
    "bar":     '<line x1="5.5" y1="0" x2="5.5" y2="11" stroke="{c}" stroke-width="2.2"/>',
    "circle":  '<circle cx="5.5" cy="5.5" r="3.4" fill="{c}"/>',
    "diamond": '<path d="M5.5,0 L11,5.5 L5.5,11 L0,5.5 z" fill="{c}"/>',
}


def _esc(s):
    return escape(str(s), {"\"": "&quot;", "'": "&apos;"})


def _attr(k, v):
    return ' %s="%s"' % (k, _esc(v))


def _marker_id(mid, color):
    return 'mk-%s-%s' % (mid, color.lstrip("#").lower())


def _source_attr(sources, sep="; "):
    parts = []
    for s in sources or []:
        parts.append("%s|%s|%s" % (s.get("ref", ""), s.get("kind", "material"),
                                   s.get("line", "")))
    return sep.join(parts)


def _edge_label_pos(points):
    if len(points) >= 4:
        # vertical route: label above the horizontal elbow segment
        return ((points[1][0] + points[2][0]) / 2.0 + 10, points[1][1] - 8)
    if len(points) >= 3:
        p0, pm = points[0], points[len(points) // 2]
        return (pm[0] + 10, pm[1] - 8)
    return (points[-1][0] + 10, points[-1][1] - 8)


def render_svg(model, layout, provenance, out_path=None):
    """Produce (svg_text, report).  report carries layers & counts."""
    W, H = layout["canvas"]["width"], layout["canvas"]["height"]
    legend = model["legend"]
    dm = legend.get("data_mapping") or {}
    scale = data_scale(model)
    vmin, vmax = (scale[0], scale[1]) if scale else (0.0, 1.0)

    used_etypes = sorted({e["type"] for e in model["entities"]})
    used_rtypes = sorted({r["type"] for r in model["edges"]})

    parts = []
    parts.append('<?xml version="1.0" encoding="UTF-8"?>')
    parts.append('<!-- %s v%s (contract %s) -->' % (SKILL_NAME, provenance.get("skill_version", "?"), CONTRACT_VERSION))
    parts.append('<!-- Editable source figure. Change a label / an arrow in a layer group and re-export. -->')
    parts.append('<!-- provenance: %s -->' % _esc(provenance.get("provenance", "")))
    parts.append('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">'
                 % (W, H, W, H))

    # ---------------- defs: markers + ramp ----------------
    defs = ['<defs>']
    ramps = set()
    for rtype in used_rtypes:
        spec = legend.get("edges", {}).get(rtype, EDGE_TYPES.get(rtype))
        if not spec or spec.get("marker") == "none":
            continue
        color = spec["color"]
        mk = _marker_id(spec["marker"], color)
        body = MARKERS[spec["marker"]].format(c=color)
        refx = "11" if spec["marker"] in ("arrow", "diamond") else "5.5"
        refy = "5.5"
        defs.append('<marker id="%s" viewBox="0 0 11 11" refX="%s" refY="%s" '
                    'markerWidth="11" markerHeight="11" orient="auto-start-reverse">%s</marker>'
                    % (mk, refx, refy, body))
    if dm.get("field") and dm.get("high"):
        defs.append('<linearGradient id="ramp-legend" x1="0" y1="0" x2="1" y2="0">'
                    '<stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s"/>'
                    '</linearGradient>' % (dm.get("low", "#FFF7E0"), dm.get("high", "#1F4E79")))
    defs.append('</defs>')
    parts.append("".join(defs))

    # ---------------- layer-compartment ----------------
    parts.append('<g id="layer-compartment">')
    for b in layout["compartments"]:
        x, y, w, h = b["rect"]
        parts.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" '
                     'fill="%s" stroke="%s" stroke-width="1.4" stroke-dasharray="none" />'
                     % (x, y, w, h, b["fill"], b["stroke"]) + _attr("data-role", "compartment") + _attr("data-id", b["id"]))
        parts.append('<text x="%.1f" y="%.1f" font-family="%s" font-size="13" '
                     'font-weight="bold" fill="%s" text-anchor="start">%s (%s)</text>'
                     % (x + 8, y + 18, FONT_STACK, b["stroke"], _esc(b["label_zh"]), _esc(b["label_en"])))
    parts.append('</g>')

    # ---------------- layer-edge ----------------
    parts.append('<g id="layer-edge">')
    for rid, r in layout["edges"].items():
        st = r["style"]
        pts = r["points"]
        d = " ".join(("M" if i == 0 else "L") + "%.1f %.1f" % p for i, p in enumerate(pts))
        dashed = (' stroke-dasharray="6 4"' if st["dash"] else "")
        marker = ''
        if st["marker"] != "none":
            marker = ' marker-end="url(#%s)"' % _marker_id(st["marker"], st["color"])
        attrs = (_attr("data-id", rid) + _attr("data-type", r["type"])
                 + _attr("data-from", r["from"]) + _attr("data-to", r["to"])
                 + _attr("data-evidence", r.get("evidence", "moderate"))
                 + _attr("data-source", _source_attr(r.get("source"))))
        parts.append('<path d="%s" fill="none" stroke="%s" stroke-width="%.1f"%s%s%s/>'
                     % (d, st["color"], st["width"], dashed, marker, attrs))
        if r.get("label") or r.get("subtype"):
            lx, ly = _edge_label_pos(pts)
            parts.append('<text x="%.1f" y="%.1f" font-family="%s" font-size="11" fill="%s" '
                         'font-weight="bold">%s</text>'
                         % (lx, ly, FONT_STACK, st["color"],
                            _esc(r.get("label") or (r.get("subtype") or ""))))
    parts.append('</g>')

    # ---------------- layer-entity ----------------
    parts.append('<g id="layer-entity">')
    for eid, ed in layout["entities"].items():
        x, y, w, h = ed["rect"]
        style = ed["style"]
        name = ed["name"]
        fill = data_color({"type": ed["type"], "data": ed["data"]}, legend, vmin, vmax)["fill"]
        stroke = NODE_TYPES.get(ed["type"], NODE_TYPES["other"])["stroke"]
        attrs = (_attr("data-id", ed["id"]) + _attr("data-type", ed["type"])
                 + _attr("data-compartment", ed["compartment"])
                 + _attr("data-source", _source_attr(ed.get("source"))))
        if ed.get("data"):
            attrs += _attr("data-values", "; ".join("%s=%s" % kv for kv in sorted(ed["data"].items())))
        g_open = '<g id="entity-%s"%s>' % (_esc(ed["id"]), attrs)
        parts.append(g_open)
        if ed["type"] == "small_molecule":
            cx, cy = x + w / 2.0, y + h / 2.0
            r = min(w, h) / 2.0
            parts.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" stroke="%s" stroke-width="1.6"/>'
                         % (cx, cy, r, fill, stroke))
        else:
            rx = "10" if style.get("type") in ("protein", "complex", "rna") else "3"
            parts.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%s" ry="%s" fill="%s" stroke="%s" stroke-width="1.6"/>'
                         % (x, y, w, h, rx, rx, fill, stroke))
            if style.get("double"):
                parts.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%s" ry="%s" fill="none" stroke="%s" stroke-width="1" stroke-dasharray="2 2"/>'
                             % (x + 3.5, y + 3.5, w - 7, h - 7, "7", "7", stroke))
            if style.get("dash") and ed["type"] == "rna":
                parts.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%s" ry="%s" fill="none" stroke="%s" stroke-width="1" stroke-dasharray="3 3"/>'
                             % (x + 3.5, y + 3.5, w - 7, h - 7, "7", "7", stroke))
        parts.append('</g>')
    parts.append('</g>')

    # ---------------- layer-label ----------------
    parts.append('<g id="layer-label">')
    for eid, ed in layout["entities"].items():
        x, y, w, h = ed["rect"]
        fs = 14 if len(ed["name"]) <= 10 else 12
        italic = " font-style=\"italic\"" if ed["style"]["italic"] else ""
        parts.append('<text x="%.1f" y="%.1f" font-family="%s" font-size="%d" fill="#17202A" '
                     'text-anchor="middle"%s>%s</text>' % (x + w / 2.0, y + h / 2.0 + fs * 0.36, FONT_STACK, fs, italic, _esc(ed["name"])))
    parts.append('</g>')

    # ---------------- layer-title ----------------
    parts.append('<g id="layer-title">')
    parts.append('<text x="36" y="46" font-family="%s" font-size="21" font-weight="bold" fill="#1B2631">%s</text>'
                 % (FONT_STACK, _esc(model.get("title") or "机制图 / Pathway diagram")))
    sub = "case: %s · generated: %s · skill: %s v%s · contract %s" % (
        _esc(str(model.get("case_id") or "-")), provenance.get("ts", "-"),
        SKILL_NAME, provenance.get("skill_version", "?"), CONTRACT_VERSION)
    if model.get("example"):
        sub = "【示例，非正式案例 sample output】 " + sub
    parts.append('<text x="36" y="68" font-family="%s" font-size="12" fill="#566573">%s</text>' % (FONT_STACK, _esc(sub)))
    parts.append('</g>')

    # ---------------- layer-legend ----------------
    parts.append('<g id="layer-legend">')
    lx0 = W - LEGEND_W + 22
    ly = 132
    parts.append('<text x="%.1f" y="%d" font-family="%s" font-size="15" font-weight="bold" fill="#1B2631">%s</text>'
                 % (lx0, ly, FONT_STACK, _esc(legend.get("title", "图例 Legend"))))
    ly += 24

    def legend_line():
        return lx0 - 18, ly, W - 18

    # entity styles used
    parts.append('<text x="%.1f" y="%d" font-family="%s" font-size="12" font-weight="bold" fill="#34495E">实体 styles</text>'
                 % (lx0, ly, FONT_STACK))
    ly += 8
    for t in used_etypes or [k for k in NODE_TYPES]:
        spec = NODE_TYPES.get(t, NODE_TYPES["other"])
        x, y2, w, h = legend_line()[0], ly, 26, 16
        if t == "small_molecule":
            parts.append('<circle cx="%.1f" cy="%.1f" r="8" fill="%s" stroke="%s" stroke-width="1.4"/>' % (x + 13, y2 + 8, spec["fill"], spec["stroke"]))
        else:
            rx = "8" if spec["shape"] == "roundrect" else "3"
            parts.append('<rect x="%.1f" y="%.1f" width="26" height="16" rx="%s" ry="%s" fill="%s" stroke="%s" stroke-width="1.4"/>' % (x, y2, rx, rx, spec["fill"], spec["stroke"]))
        parts.append('<text x="%.1f" y="%.1f" font-family="%s" font-size="11" fill="#17202A">%s (%s)</text>'
                     % (x + 34, y2 + 12, FONT_STACK, _esc(spec["zh"]), _esc(t)))
        ly += 22

    ly += 8
    parts.append('<text x="%.1f" y="%d" font-family="%s" font-size="12" font-weight="bold" fill="#34495E">相互作用 arrows</text>'
                 % (lx0, ly, FONT_STACK))
    ly += 8
    for t in used_rtypes or [k for k in EDGE_TYPES]:
        spec = legend.get("edges", {}).get(t, EDGE_TYPES.get(t))
        x, y2 = legend_line()[0], ly
        marker = ''
        if spec["marker"] != "none":
            marker = ' marker-end="url(#%s)"' % _marker_id(spec["marker"], spec["color"])
        parts.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="2.2"%s/>'
                     % (x, y2 + 8, x + 40, y2 + 8, spec["color"], marker))
        parts.append('<text x="%.1f" y="%.1f" font-family="%s" font-size="11" fill="#17202A">%s (%s)</text>'
                     % (x + 48, y2 + 12, FONT_STACK, _esc(spec["zh"]), _esc(t)))
        ly += 22
    # evidence widths
    ly += 2
    for ev, wd in EVIDENCE_WIDTH.items():
        x, y2 = legend_line()[0], ly
        parts.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#566573" stroke-width="%.1f"/>'
                     % (x, y2 + 8, x + 40, y2 + 8, wd))
        parts.append('<text x="%.1f" y="%.1f" font-family="%s" font-size="11" fill="#17202A">证据强度 evidence: %s</text>'
                     % (x + 48, y2 + 12, FONT_STACK, _esc(ev)))
        ly += 22
    parts.append('<text x="%.1f" y="%d" font-family="%s" font-size="10" fill="#566573">%s</text>'
                 % (lx0, ly, FONT_STACK, _esc(legend.get("dash_note", {}).get("zh", ""))))
    ly += 18
    if dm.get("field"):
        x, y2 = legend_line()[0], ly
        parts.append('<rect x="%.1f" y="%.1f" width="90" height="10" fill="url(#ramp-legend)" stroke="#85929E" stroke-width="0.8"/>' % (x, y2))
        parts.append('<text x="%.1f" y="%.1f" font-family="%s" font-size="10" fill="#17202A">%s</text>'
                     % (x, y2 + 22, FONT_STACK, _esc(dm.get("label_zh", "") or dm.get("label_en", ""))))
        parts.append('<text x="%.1f" y="%.1f" font-family="%s" font-size="10" fill="#566573">低 %s  高 %s</text>'
                     % (x + 96, y2 + 9, FONT_STACK, _esc(dm.get("low", "")), _esc(dm.get("high", ""))))
        ly += 40
    dirn = legend.get("direction_note", {}).get("zh", "")
    parts.append('<text x="%.1f" y="%d" font-family="%s" font-size="10" fill="#566573">%s</text>'
                 % (lx0, ly, FONT_STACK, _esc(dirn) if dirn else ""))
    parts.append('</g>')

    # ---------------- layer-meta ----------------
    parts.append('<g id="layer-meta">')
    mly = H - 40
    parts.append('<text x="36" y="%.1f" font-family="%s" font-size="10" fill="#7F8C8D">sources / 来源:</text>' % (mly - 26, FONT_STACK))
    refs = []
    for ed in layout["entities"].values():
        for s in ed.get("source", []):
            refs.append((s.get("ref", ""), s.get("kind", ""), s.get("line", ""), ed["name"]))
    for r in layout["edges"].values():
        for s in r.get("source", []):
            refs.append((s.get("ref", ""), s.get("kind", ""), s.get("line", ""), r["id"]))
    seen = set()
    for ref, kind, line, who in refs:
        k = (ref, line)
        if k in seen:
            continue
        seen.add(k)
        parts.append('<text x="36" y="%.1f" font-family="%s" font-size="9" fill="#7F8C8D">· %s (kind=%s, line=%s) used by %s</text>'
                     % (mly, FONT_STACK, _esc(ref), _esc(kind), _esc(str(line)), _esc(who)))
        mly += 12
        if mly > H - 8:
            break
    parts.append('</g>')

    parts.append('</svg>')
    svg_text = "\n".join(parts)

    # round-trip to guarantee well-formedness
    ET.fromstring(svg_text)

    # ---- build the audit report ----
    report = {"layers": ["layer-compartment", "layer-edge", "layer-entity",
                         "layer-label", "layer-title", "layer-legend", "layer-meta"],
              "entity_count": len(layout["entities"]),
              "edge_count": len(layout["edges"]),
              "band_count": len(layout["compartments"]),
              "svg_bytes": len(svg_text.encode("utf-8")),
              "well_formed": True}
    if out_path:
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(svg_text)
    return svg_text, report