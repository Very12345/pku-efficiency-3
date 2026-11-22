#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Editable layered SVG builder for relationship schematics.

Produces a hand-authored, truly editable SVG source file:

* every label is a <text> element (selectable / searchable text),
* every element carries an id (nodes: node-<id>, edges: edge-<id>, …),
* semantic layers are separate <g> groups (background, groups, edges,
  nodes, legend, footer) so the figure can be ungrouped in any editor,
* the ER manifest itself is embedded in <metadata id="er-manifest"> so a
  later edit request can operate on the source (scripts/edit.py) without
  any external state,
* data-* attributes (data-entity, data-relation, data-source) make the
  figure machine-verifiable against the original materials.

Only the Python standard library is used.
"""

import json
import os
import html

from layout import compute_layout, edge_endpoints


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def esc(text):
    return html.escape(str(text if text is not None else ""), quote=True)


def rounded_rect_path(x, y, w, h, r=10):
    r = min(r, w / 2, h / 2)
    return ("M{x0},{y0} h{w0} a{r},{r} 0 0 1 {r},{r} v{h0} "
            "a{r},{r} 0 0 1 -{r},{r} h{w1} a{r},{r} 0 0 1 -{r},-{r} v{h1} "
            "a{r},{r} 0 0 1 {r},-{r} z").format(
        x0=x + r, y0=y, w0=w - 2 * r, r=r, h0=h - 2 * r,
        w1=-(w - 2 * r), h1=-(h - 2 * r))


def wrap_text_lines(text, maxw, font_px, width):
    """Greedy line wrap so long node labels fit their box."""
    words = str(text or "").split()
    if not words:
        return [""]
    lines, line = [], ""
    for w in words:
        trial = (line + " " + w).strip()
        if len(trial) * font_px * 0.62 <= max(60, width - 16) or not line:
            line = trial
        else:
            lines.append(line)
            line = w
    lines.append(line)
    return lines


# ---------------------------------------------------------------------------
# Arrow marker definitions
# ---------------------------------------------------------------------------

def markers_svg():
    return """  <defs>
    <marker id="arrow-activation" viewBox="0 0 12 12" refX="11" refY="6"
            markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M1,1 L11,6 L1,11 z" fill="#0072B2" stroke="#0072B2"
            stroke-width="1"/>
    </marker>
    <marker id="arrow-open" viewBox="0 0 12 12" refX="10" refY="6"
            markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse">
      <path d="M3,1.5 L10.5,6 L3,10.5" fill="none" stroke="#009E73"
            stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
    </marker>
    <marker id="arrow-inhibition" viewBox="0 0 14 14" refX="13" refY="7"
            markerWidth="9" markerHeight="9" orient="auto-start-reverse">
      <line x1="2" y1="1" x2="2" y2="13" stroke="#D55E00" stroke-width="2.4"/>
    </marker>
  </defs>"""


EDGE_STYLES = {
    "activation": {"stroke": "#0072B2", "marker": "url(#arrow-activation)",
                   "dash": None, "width": 2.6},
    "recruitment": {"stroke": "#009E73", "marker": "url(#arrow-open)",
                    "dash": None, "width": 2.2},
    "process": {"stroke": "#0072B2", "marker": "url(#arrow-open)",
                "dash": None, "width": 2.2},
    "transcriptional": {"stroke": "#CC79A7", "marker": "url(#arrow-open)",
                        "dash": "7,4", "width": 2.2},
    "causal": {"stroke": "#666666", "marker": "url(#arrow-open)",
               "dash": None, "width": 2.0},
    "inhibition": {"stroke": "#D55E00", "marker": "url(#arrow-inhibition)",
                   "dash": None, "width": 2.4},
}


# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------

TYPE_FILLS = {
    "protein": "#DEEBF7", "receptor": "#FCE4D6", "gene": "#FFF2CC",
    "small_molecule": "#E2EFDA", "process": "#EDEDED", "cell": "#F9E7E7",
    "organ": "#FBE5D6", "pathway": "#E4DFEC", "default": "#F2F2F2",
}


def build_schematic_svg(manifest, layout, footer_notes=None):
    """Return the full SVG XML string for a relationship schematic.

    :param manifest: normalized ER manifest (scripts/manifest.py)
    :param layout:   layout dict from scripts/layout.py
    :param footer_notes: optional list of provenance strings for the footer
    """
    nodes = layout["nodes"]
    groups = layout["groups"]
    canv = layout["canvas"]
    edges = layout["edges"]
    W, H = canv["width"], canv["height"]
    font_px = layout["text_px"]

    footer_notes = footer_notes or []
    if not footer_notes:
        srcs = sorted({n["source"] for n in nodes.values() if n.get("source")})
        if srcs:
            footer_notes.append("Sources: " + "; ".join(srcs))

    L = []
    L.append('<?xml version="1.0" encoding="UTF-8"?>')
    L.append('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
             'viewBox="0 0 %d %d" font-family="Arial, Helvetica, \'Microsoft '
             'YaHei\', \'Noto Sans CJK SC\', sans-serif" font-size="%d">'
             % (W, H, W, H, font_px))
    L.append("  <title>%s</title>" % esc(manifest.get("title", "")))
    L.append("  <desc>Scientific schematic generated by "
             "scientific-schematic-editor. Editable: every label is a text "
             "element, every element carries an id, semantic layers are "
             "grouped. ER manifest embedded for source-preserving edit.</desc>")
    L.append('  <metadata id="er-manifest">%s</metadata>'
             % esc(json.dumps(manifest, ensure_ascii=False)))
    L.append(markers_svg())

    # ---- layer: background ----
    L.append('  <g id="layer-background">')
    L.append('    <rect id="bg-canvas" x="0" y="0" width="%d" height="%d" '
             'fill="#FFFFFF"/>' % (W, H))
    L.append("  </g>")

    # ---- layer: group boxes ----
    L.append('  <g id="layer-groups">')
    for gid, g in sorted(groups.items()):
        dash = "10,6"
        L.append('    <g id="group-%s" data-group="%s">' % (esc(gid), esc(gid)))
        L.append('      <rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" '
                 'rx="12" fill="#FAFAFA" stroke="#8C8C8C" stroke-width="1.6" '
                 'stroke-dasharray="%s"/>' % (g["x"], g["y"], g["w"], g["h"], dash))
        if g.get("label"):
            L.append('      <text x="%.1f" y="%.1f" font-size="%d" fill="#595959" '
                     'font-weight="bold">%s</text>'
                     % (g["x"] + 16, g["y"] + 24, int(font_px * 0.9),
                        esc(g["label"])))
        L.append("    </g>")
    L.append("  </g>")

    # ---- layer: edges ----
    L.append('  <g id="layer-edges" fill="none">')
    for e in edges:
        s, t = nodes[e["from"]], nodes[e["to"]]
        scx, scy = s["x"] + s["w"] / 2, s["y"] + s["h"] / 2
        tcx, tcy = t["x"] + t["w"] / 2, t["y"] + t["h"] / 2
        # simple two-bend routing for layered layouts to reduce overlap
        bend = 24.0
        sx1, sy1 = scx, scy
        tx1, ty1 = tcx, tcy
        if s["layer"] != t["layer"]:
            midx = (scx + tcx) / 2
            d = "M %.1f,%.1f C %.1f,%.1f %.1f,%.1f %.1f,%.1f" % (
                sx1, sy1, midx, sy1 + (ty1 - sy1) * 0.25 + bend,
                midx, ty1 - (ty1 - sy1) * 0.25 - bend, tx1, ty1)
            p1 = (sx1, sy1)
            p2 = (tx1, ty1)
            msx = sx1 + (midx - sx1) * 0.5
            msy = sy1 + (ty1 - sy1) * 0.5
        else:
            d = "M %.1f,%.1f L %.1f,%.1f" % (sx1, sy1, tx1, ty1)
            msx, msy = (sx1 + tx1) / 2, (sy1 + ty1) / 2
            p1, p2 = (sx1, sy1), (tx1, ty1)
        style = EDGE_STYLES.get(e["canon"], EDGE_STYLES["process"])
        marker = ' marker-end="%s"' % style["marker"] if e["arrow"] != "none" else ""
        dash = ' stroke-dasharray="%s"' % style["dash"] if style["dash"] else ""
        L.append('    <g id="edge-%s" data-relation="%s" data-from="%s" '
                 'data-to="%s" data-canon="%s" data-source="%s">'
                 % (esc(e["id"]), esc(e["id"]), esc(e["from"]), esc(e["to"]),
                    esc(e["canon"] or ""), esc(e.get("source", "") or "")))
        L.append('      <path d="%s" stroke="%s" stroke-width="%g"%s%s/>'
                 % (d, style["stroke"], style["width"], dash, marker))
        if e.get("label"):
            L.append('      <text x="%.1f" y="%.1f" font-size="%d" fill="#404040" '
                     'text-anchor="middle" paint-order="stroke" stroke="#FFFFFF" '
                     'stroke-width="3">%s</text>'
                     % (msx, msy - 6, int(font_px * 0.78), esc(e["label"])))
        L.append("    </g>")
    L.append("  </g>")

    # ---- layer: nodes ----
    L.append('  <g id="layer-nodes">')
    for nid, n in sorted(nodes.items()):
        fill = TYPE_FILLS.get(n.get("type"), TYPE_FILLS["default"])
        txt = n.get("text") or nid
        lines = wrap_text_lines(txt, max(40, n["w"] - 20), font_px, n["w"])
        y0 = n["y"] + n["h"] / 2 - (len(lines) - 1) * font_px / 2
        L.append('    <g id="node-%s" data-entity="%s" data-type="%s" '
                 'data-source="%s">' % (esc(nid), esc(nid), esc(n.get("type", "")),
                                        esc(n.get("source", "") or "")))
        L.append('      <path d="%s" fill="%s" stroke="#404040" '
                 'stroke-width="1.6"/>' % (rounded_rect_path(n["x"], n["y"],
                                                              n["w"], n["h"]),
                                            fill))
        for i, ln in enumerate(lines):
            L.append('      <text x="%.1f" y="%.1f" text-anchor="middle" '
                     'fill="#1A1A1A" font-size="%d">%s</text>'
                     % (n["x"] + n["w"] / 2, y0 + i * font_px + font_px * 0.35,
                        font_px, esc(ln)))
        L.append("    </g>")
    L.append("  </g>")

    # ---- layer: legend ----
    L.append('  <g id="layer-legend">')
    legend = manifest.get("legend") or []
    if legend:
        lx, ly = W - 44, 40
        L.append('    <rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" '
                 'rx="8" fill="#FFFFFF" stroke="#BFBFBF" stroke-width="1"/>'
                 % (lx - 16, ly - 26, 360, len(legend) * 30 + 40))
        L.append('    <text x="%.1f" y="%.1f" font-size="%d" font-weight="bold" '
                 'fill="#1A1A1A">Legend</text>'
                 % (lx, ly, int(font_px * 0.95)))
        for i, item in enumerate(legend):
            key = item.get("key") or item.get("arrow") or item.get("label") or ""
            style = EDGE_STYLES.get(key, EDGE_STYLES["process"])
            yy = ly + 24 + i * 30
            dash = ' stroke-dasharray="%s"' % style["dash"] if style["dash"] else ""
            rel = ' data-source="%s"' % esc(item.get("source", "") or "") \
                if item.get("source") else ""
            L.append('    <g id="legend-item-%s"%s>' % (esc(item.get("id") or str(i)),
                                                        rel))
            if style["marker"] == "url(#arrow-inhibition)":
                L.append('      <line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" '
                         'stroke="%s" stroke-width="2.4"/>'
                         % (lx, yy - 5, lx + 26, yy - 5, style["stroke"]))
                L.append('      <line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" '
                         'stroke="%s" stroke-width="2.2"/>'
                         % (lx + 26, yy - 9, lx + 26, yy - 1, style["stroke"]))
            else:
                L.append('      <line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" '
                         'stroke="%s" stroke-width="2.4"%s marker-end="%s"/>'
                         % (lx, yy - 5, lx + 26, yy - 5, style["stroke"],
                            dash, style["marker"]))
            L.append('      <text x="%.1f" y="%.1f" font-size="%d" fill="#404040">'
                     '%s</text>'
                     % (lx + 36, yy + 2, int(font_px * 0.82),
                        esc(item.get("label") or key)))
            L.append("    </g>")
    L.append("  </g>")

    # ---- layer: footer (provenance) ----
    L.append('  <g id="layer-footer">')
    L.append('    <text id="provenance" x="16" y="%d" font-size="%d" '
             'fill="#8C8C8C">%s</text>'
             % (H - 14, int(font_px * 0.72),
                esc(" | ".join(footer_notes)[:400])))
    L.append("  </g>")

    L.append("</svg>")
    return "\n".join(L)


def write_svg(out_path, xml, header_note=None):
    """Persist SVG with LF line endings + optional generator header note
    placed inside the <desc> element."""
    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        if header_note:
            xml = xml.replace("</desc>", header_note + " </desc>", 1)
        fh.write(xml + "\n")
    return os.path.abspath(out_path)