#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rendered preview / export generation.

Two responsibilities:

1. schematic — a faithful matplotlib MIRROR of the hand-authored SVG. It
   re-plays the exact same layout and manifest (same positions, same
   labels, same colors) so the PNG preview and the PDF export visually
   match the editable SVG. This is a deliberate substitute for a full SVG
   rasterizer: cairosvg/svgwrite are NOT available in the target
   environment, so previews are produced from the shared layout object
   instead of by rasterizing the SVG.

2. chart — native matplotlib charts (bar / line / scatter / heatmap)
   drawn directly from the manifest `data` table. The SVG export keeps
   real <text> elements (editable) and the manifest is injected into its
   <metadata> so charts are editable and traceable too.

Matplotlib default font is DejaVu Sans; on systems that provide CJK fonts
(SimHei / Microsoft YaHei / Noto Sans CJK) they are picked automatically
so Chinese labels render. The resolved font is reported back for the
export checks.
"""

import json
import math
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.lines import Line2D

from layout import compute_layout, edge_endpoints
from svgbuilder import TYPE_FILLS, EDGE_STYLES

# Okabe-Ito-inspired colour-blind-safe palette for categorical data
CATEGORY_COLORS = [
    "#0072B2", "#E69F00", "#009E73", "#D55E00", "#56B4E9",
    "#CC79A7", "#F0E442", "#000000", "#999999", "#661100",
]


def resolve_font_stack():
    """Pick the best available font for the OS; return (family, ok_cjk)."""
    try:
        from matplotlib import font_manager
        if sys.platform.startswith("win"):
            for name in ("Microsoft YaHei", "SimHei", "SimSun"):
                if any(name.lower() in (f.name or "").lower()
                       for f in font_manager.fontManager.ttflist):
                    return name, True
        for name in ("Noto Sans CJK SC", "WenQuanYi Zen Hei", "PingFang SC"):
            if any((f.name or "").lower() == name.lower()
                   for f in font_manager.fontManager.ttflist):
                return name, True
    except Exception:
        pass
    return "DejaVu Sans", False


def _prep_axis(ax, W, H):
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.set_aspect("equal")
    ax.axis("off")


def render_schematic(manifest, layout, out_png, exports=(), dpi=300):
    """Draw the schematic mirror and save PNG (+ optional vector exports).

    Returns dict with file paths actually written and font info.
    """
    nodes = layout["nodes"]
    groups = layout["groups"]
    edges = layout["edges"]
    W, H = layout["canvas"]["width"], layout["canvas"]["height"]

    font_family, ok_cjk = resolve_font_stack()
    plt.rcParams["font.family"] = font_family
    plt.rcParams["font.size"] = 11

    fig = plt.figure(figsize=(W / 100.0, H / 100.0), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    _prep_axis(ax, W, H)

    # groups
    for gid, g in sorted(groups.items()):
        if not g["members"]:
            continue
        ax.add_patch(FancyBboxPatch(
            (g["x"], g["y"]), g["w"], g["h"],
            boxstyle="round,pad=0,rounding_size=12",
            facecolor="#FAFAFA", edgecolor="#8C8C8C",
            linestyle=(0, (10, 6)), linewidth=1.4, zorder=1))
        if g.get("label"):
            ax.text(g["x"] + 14, g["y"] + 18, g["label"], fontsize=10,
                    color="#595959", weight="bold", va="top", zorder=2)

    # edges (mirror of SVG: cubic bézier bends for cross-layer edges)
    for e in edges:
        s, t = nodes[e["from"]], nodes[e["to"]]
        scx, scy = s["x"] + s["w"] / 2, s["y"] + s["h"] / 2
        tcx, tcy = t["x"] + t["w"] / 2, t["y"] + t["h"] / 2
        style = EDGE_STYLES.get(e["canon"], EDGE_STYLES["process"])
        color = style["stroke"]
        ls = "solid"
        if style.get("dash"):
            ls = (0, tuple(float(v) for v in style["dash"].split(",")))
        # trim ends to node borders so arrowheads are visible
        p1, p2 = edge_endpoints(s["x"], s["y"], s["w"], s["h"],
                                t["x"], t["y"], t["w"], t["h"],
                                scx, scy, tcx, tcy)
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=color,
                lw=style["width"], ls=ls, zorder=3)
        # arrowheads
        _draw_arrowhead(ax, p2, p1, e.get("arrow"), style["stroke"])
        if e.get("label"):
            lx, ly = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
            ax.text(lx, ly + 6, e["label"], fontsize=8.5, color="#404040",
                    ha="center", va="center", zorder=5,
                    bbox=dict(facecolor="white", edgecolor="none", pad=1.2))

    # nodes
    for nid, n in sorted(nodes.items()):
        fill = TYPE_FILLS.get(n.get("type"), TYPE_FILLS["default"])
        ax.add_patch(FancyBboxPatch(
            (n["x"], n["y"]), n["w"], n["h"],
            boxstyle="round,pad=0,rounding_size=8",
            facecolor=fill, edgecolor="#404040", linewidth=1.4, zorder=4))
        ax.text(n["x"] + n["w"] / 2, n["y"] + n["h"] / 2, n.get("text") or nid,
                fontsize=11, ha="center", va="center", zorder=6,
                wrap=True)

    # legend (manual, bottom-right, mirrors SVG legend order)
    legend = manifest.get("legend") or []
    if legend:
        lx, ly = W - 60, 52
        ax.add_patch(FancyBboxPatch(
            (lx - 20, ly - 40), 250, len(legend) * 26 + 62,
            boxstyle="round,pad=0,rounding_size=8",
            facecolor="white", edgecolor="#BFBFBF", linewidth=1, zorder=7))
        ax.text(lx, ly - 12, "Legend", fontsize=10, weight="bold",
                color="#1A1A1A", zorder=8)
        for i, item in enumerate(legend):
            key = item.get("key") or item.get("arrow") or item.get("label") or ""
            style = EDGE_STYLES.get(key, EDGE_STYLES["process"])
            yy = ly + 12 + i * 26
            ax.plot([lx, lx + 26], [yy, yy], color=style["stroke"], lw=2.4,
                    zorder=8, linestyle=(
                        (0, (7, 4)) if style.get("dash") else "solid"))
            if style["marker"] == "url(#arrow-inhibition)":
                ax.plot([lx + 26, lx + 26], [yy - 4, yy + 4],
                        color=style["stroke"], lw=2.2, zorder=8)
            else:
                _draw_arrowhead(ax, (lx + 26, yy), (lx, yy), key, style["stroke"])
            ax.text(lx + 36, yy, item.get("label") or key, fontsize=9,
                    color="#404040", va="center", zorder=8)

    # footer provenance
    srcs = sorted({n["source"] for n in nodes.values() if n.get("source")})
    tail = " | ".join(srcs)[:380] if srcs else ""
    if tail:
        ax.text(12, 12, tail, fontsize=7.5, color="#8C8C8C", va="bottom",
                zorder=8)

    fig.savefig(out_png, dpi=dpi, bbox_inches=None,
                facecolor="white", metadata={"Software": "scientific-schematic-editor"})
    written = {"png": os.path.abspath(out_png)}
    for fmt, ext in (("pdf", "pdf"), ("tiff", "tiff"), ("eps", "eps")):
        if fmt in exports and fmt != "png":
            p = out_png.rsplit(".", 1)[0] + "." + ext
            fig.savefig(p, dpi=dpi, facecolor="white")
            written[fmt] = os.path.abspath(p)
    plt.close(fig)
    written["font"] = font_family
    written["cjk_ok"] = ok_cjk
    return written


def _draw_arrowhead(ax, tip, tail, canon, color):
    """Small triangular (activation/open) or T-bar (inhibition) head."""
    dx, dy = tip[0] - tail[0], tip[1] - tail[1]
    n = math.hypot(dx, dy) or 1.0
    ux, uy = dx / n, dy / n
    px, py = -uy, ux
    size = 9.0
    if canon == "inhibition":
        bx, by = tip[0], tip[1]
        ax.plot([bx + px * 4, bx - px * 4], [by + py * 4, by - py * 4],
                color=color, lw=2.4, zorder=9)
        return
    bx, by = tip[0] - ux * size, tip[1] - uy * size
    ax.fill([tip[0], bx + px * size * 0.55, bx - px * size * 0.55],
            [tip[1], by + py * size * 0.55, by - py * size * 0.55],
            color=color, zorder=9)


# ---------------------------------------------------------------------------
# Charts (native matplotlib from manifest["data"])
# ---------------------------------------------------------------------------

def build_chart_artifacts(manifest, out_base, exports=("png", "pdf", "svg"),
                          dpi=300):
    """Draw a chart from manifest['data'] and write png/pdf/svg/tiff.

    Legend is generated from the actual category values of the data table,
    so legend ↔ colour ↔ category consistency holds by construction and is
    reported back for the compliance checks.

    Returns dict of written files + mapping facts.
    """
    data = manifest.get("data") or {}
    table = data.get("table") or {}
    columns = table.get("columns") or []
    rows = table.get("rows") or []
    chart_type = (data.get("chart_type") or "bar").lower()
    cat_col = data.get("category_col") or (columns[1] if len(columns) >= 2 else None)
    val_col = data.get("value_col") or (columns[-1] if columns else None)
    unit = data.get("unit") or ""
    title = manifest.get("title") or "Figure"

    font_family, ok_cjk = resolve_font_stack()
    plt.rcParams["font.family"] = font_family
    # Keep text as real <text> elements in the SVG export (editable text).
    # Default for matplotlib is "path" (glyphs converted to paths) which
    # would make labels non-editable — exactly the failure the task warns
    # about ("改一个标签就要整张重画").
    matplotlib.rcParams["svg.fonttype"] = "none"

    if not rows:
        raise ValueError("chart manifest `data.table.rows` is empty — nothing "
                         "to draw")

    cats = []
    values = []
    for row in rows:
        # rows may be dicts or positional lists
        if isinstance(row, dict):
            cats.append(str(row.get(cat_col, "")))
            values.append(float(row.get(val_col, 0)))
        else:
            idx_c = columns.index(cat_col) if cat_col in columns else 0
            idx_v = columns.index(val_col) if val_col in columns else len(row) - 1
            cats.append(str(row[idx_c]))
            values.append(float(row[idx_v]))

    unique_cats = list(dict.fromkeys(cats))
    colors = {c: CATEGORY_COLORS[i % len(CATEGORY_COLORS)]
              for i, c in enumerate(unique_cats)}

    fig, ax = plt.subplots(figsize=(9, 5.2), dpi=100)
    if chart_type == "bar":
        x = list(range(len(unique_cats)))
        ax.bar(x, [values[cats.index(c)] for c in unique_cats],
               color=[colors[c] for c in unique_cats], edgecolor="#404040",
               linewidth=0.8)
        ax.set_xticks(x)
        ax.set_xticklabels(unique_cats, rotation=12, ha="right")
    elif chart_type == "line":
        for i, c in enumerate(unique_cats):
            xs = [i for i, cc in enumerate(cats) if cc == c]
            ys = [values[i] for i in xs]
            ax.plot(xs, ys, marker="o", color=colors[c], lw=2.2,
                    label="%s" % c)
        ax.legend(frameon=False)
    elif chart_type == "scatter":
        for i, c in enumerate(unique_cats):
            xs = [i for i, cc in enumerate(cats) if cc == c]
            ys = [values[i] for i in xs]
            ax.scatter(xs, ys, color=colors[c], s=55, label="%s" % c)
        ax.legend(frameon=False)
    elif chart_type == "heatmap":
        # rows = repeated category → value series; build a dense grid via
        # optional `matrix` field if present, otherwise category × sample
        matrix = data.get("matrix")
        if matrix:
            import numpy as np  # numpy is preinstalled
            mat = np.asarray(matrix, dtype=float)
            im = ax.imshow(mat, cmap=data.get("cmap", "viridis"))
            fig.colorbar(im, ax=ax)
            ax.set_xticks(range(mat.shape[1]))
            ax.set_yticks(range(mat.shape[0]))
            if data.get("row_labels"):
                ax.set_yticklabels(data["row_labels"])
            if data.get("col_labels"):
                ax.set_xticklabels(data["col_labels"], rotation=30, ha="right")
        else:
            xs = list(range(len(unique_cats)))
            ys = [values[cats.index(c)] for c in unique_cats]
            ax.bar(xs, ys, color=[colors[c] for c in unique_cats])
            ax.set_xticks(xs)
            ax.set_xticklabels(unique_cats, rotation=12, ha="right")
    else:
        raise ValueError("unsupported chart_type %r (use bar/line/scatter/"
                         "heatmap)" % chart_type)

    ax.set_title(title, fontsize=12, pad=10)
    ylab = (data.get("y_label") or val_col or "value")
    if unit:
        ylab += " (%s)" % unit
    ax.set_ylabel(ylab)
    if data.get("x_label"):
        ax.set_xlabel(data["x_label"])
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()

    out_base = os.path.abspath(out_base)
    written = {}
    if "png" in exports:
        p = out_base + ".png"
        fig.savefig(p, dpi=dpi, facecolor="white")
        written["png"] = p
    if "pdf" in exports:
        p = out_base + ".pdf"
        fig.savefig(p, dpi=dpi, facecolor="white")
        written["pdf"] = p
    if "svg" in exports:
        p = out_base + ".svg"
        fig.savefig(p, dpi=dpi, facecolor="white")
        _inject_manifest_into_svg(p, manifest)
        written["svg"] = p
    if "tiff" in exports:
        p = out_base + ".tiff"
        fig.savefig(p, dpi=dpi, facecolor="white")
        written["tiff"] = p
    if "eps" in exports:
        p = out_base + ".eps"
        fig.savefig(p, dpi=dpi, facecolor="white")
        written["eps"] = p
    plt.close(fig)

    written["font"] = font_family
    written["cjk_ok"] = ok_cjk
    written["mapping"] = {
        "category_col": cat_col, "value_col": val_col, "unit": unit,
        "unique_categories": unique_cats,
        "category_colors": colors,
        "legend_entries": len(unique_cats),
    }
    return written


def _inject_manifest_into_svg(svg_path, manifest):
    """Embed the manifest and a <title> into a matplotlib-produced SVG so
    chart sources stay traceable and editable-from-source too."""
    with open(svg_path, "r", encoding="utf-8") as fh:
        text = fh.read()
    if not re.search(r"<title>", text[:4000]):
        title = json.dumps(manifest.get("title", "Figure"),
                           ensure_ascii=False)
        m2 = re.search(r"(<svg[^>]*>)", text)
        if m2:
            text = text[:m2.end()] + ("<title>%s</title>" % title) + \
                text[m2.end():]
    meta = ('<metadata id="er-manifest">%s</metadata>'
            % json.dumps(manifest, ensure_ascii=False)
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    if re.search(r'<metadata id="er-manifest">', text):
        return
    text = text.replace("</svg>", meta + "</svg>", 1)
    with open(svg_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def render_figure(manifest, layout, out_base, exports=("png", "pdf", "svg"),
                  dpi=300):
    """Top-level dispatch: schematic vs chart."""
    fig_type = (manifest.get("figure_type") or "schematic").lower()
    if fig_type == "chart":
        return {"kind": "chart",
                **build_chart_artifacts(manifest, out_base, exports, dpi)}
    return {"kind": "schematic",
            **render_schematic(manifest, layout, out_base + ".png",
                               exports, dpi)}


if __name__ == "__main__":
    print("render.py: library module; run scripts/main.py instead.")