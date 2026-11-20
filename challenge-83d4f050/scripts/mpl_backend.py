# -*- coding: utf-8 -*-
"""matplotlib preview renderer (PNG/PDF).

This backend is OPTIONAL: it renders the very same layout/model that the SVG
backend draws, so the PNG/PDF preview is a faithful raster/vector copy of the
editable source (same coordinates, same colors, same arrow semantics).

If matplotlib is not importable the caller (main.py) records a partial preview
status instead of fabricating software state.
"""
import math

import matplotlib
matplotlib.use("Agg")

from model import (SKILL_NAME, CONTRACT_VERSION, NODE_TYPES, EDGE_TYPES,
                   EVIDENCE_WIDTH, data_color, data_scale)

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, Circle

FONT_CANDIDATES = ["SimHei", "Microsoft YaHei", "PingFang SC",
                   "Noto Sans CJK SC", "WenQuanYi Zen Hei", "DejaVu Sans"]


def _setup_fonts():
    import matplotlib.font_manager as fm
    used = None
    for c in FONT_CANDIDATES:
        try:
            used = fm.findfont(fm.FontProperties(family=c),
                               fallback_to_default=False)
            break
        except Exception:
            continue
    if used is None:
        used = fm.findfont(fm.FontProperties(family="sans-serif"))
    return used


def render_preview(model, layout, png_path=None, pdf_path=None, dpi=150):
    """Render PNG and/or PDF previews from the shared layout.

    Returns {"png": {...}|None, "pdf": {...}|None, "warnings": [...], "font": str}
    """
    warnings = []
    font_path = _setup_fonts()
    import matplotlib.font_manager as fm
    plt.rcParams["font.sans-serif"] = FONT_CANDIDATES
    plt.rcParams["axes.unicode_minus"] = False

    legend = model["legend"]
    dm = legend.get("data_mapping") or {}
    scale = data_scale(model)
    vmin, vmax = (scale[0], scale[1]) if scale else (0.0, 1.0)

    W, H = layout["canvas"]["width"], layout["canvas"]["height"]
    fig = plt.figure(figsize=(W / dpi, H / dpi), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(H, 0)          # SVG-like top-left origin
    ax.axis("off")

    # compartments ----
    for b in layout["compartments"]:
        x, y, w, h = b["rect"]
        ax.add_patch(Rectangle((x, y), w, h, facecolor=b["fill"],
                               edgecolor=b["stroke"], linewidth=1.4))
        ax.text(x + 8, y + 16, "%s (%s)" % (b["label_zh"], b["label_en"]),
                fontsize=12, color=b["stroke"], fontweight="bold", ha="left", va="top")

    # edges (below nodes) ----
    for rid, r in layout["edges"].items():
        pts = r["points"]
        st = r["style"]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        ls = "--" if st["dash"] else "-"
        ax.plot(xs, ys, color=st["color"], linewidth=st["width"], linestyle=ls,
                solid_capstyle="butt")
        hx, hy = r["head"]
        if not pts:
            continue
        # orientation from the last two points
        p2 = pts[-1]
        p1 = pts[-2] if len(pts) > 1 else (p2[0] + 10, p2[1])
        ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
        _draw_head(ax, hx, hy, ang, st["marker"], st["color"])
        if r.get("label") or r.get("subtype"):
            lx, ly = _label_pos(pts)
            ax.text(lx, ly, r.get("label") or r.get("subtype"), fontsize=9,
                    color=st["color"], fontweight="bold", ha="left", va="bottom")

    # entities ----
    for eid, ed in layout["entities"].items():
        x, y, w, h = ed["rect"]
        fill = data_color({"type": ed["type"], "data": ed["data"]}, legend, vmin, vmax)["fill"]
        stroke = NODE_TYPES.get(ed["type"], NODE_TYPES["other"])["stroke"]
        if ed["type"] == "small_molecule":
            c = Circle((x + w / 2, y + h / 2), min(w, h) / 2,
                       facecolor=fill, edgecolor=stroke, linewidth=1.6)
            ax.add_patch(c)
        else:
            if ed["style"]["type"] in ("protein", "complex", "rna"):
                box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=10",
                                     facecolor=fill, edgecolor=stroke, linewidth=1.6)
            else:
                box = Rectangle((x, y), w, h, facecolor=fill, edgecolor=stroke, linewidth=1.6)
            ax.add_patch(box)
            if ed["style"]["double"]:
                ax.add_patch(Rectangle((x + 3.5, y + 3.5), w - 7, h - 7, fill=False,
                                       edgecolor=stroke, linewidth=1, linestyle=(0, (2, 2))))
            if ed["style"].get("dash"):
                ax.add_patch(Rectangle((x + 3.5, y + 3.5), w - 7, h - 7, fill=False,
                                       edgecolor=stroke, linewidth=1, linestyle=(0, (3, 3))))
        fs = 13 if len(ed["name"]) <= 10 else 11
        style = "italic" if ed["style"]["italic"] else "normal"
        ax.text(x + w / 2, y + h / 2, ed["name"], fontsize=fs, color="#17202A",
                ha="center", va="center", fontstyle=style)

    # title ----
    ax.text(36, 44, model.get("title") or "机制图 / Pathway diagram",
            fontsize=20, fontweight="bold", color="#1B2631", ha="left", va="center")
    sub = "case: %s · skill: %s v%s · contract %s" % (
        model.get("case_id") or "-", SKILL_NAME, "1.0", CONTRACT_VERSION)
    if model.get("example"):
        sub = "【示例，非正式案例】 " + sub
    ax.text(36, 68, sub, fontsize=11, color="#566573", ha="left", va="center")

    # legend (right column) ----
    lx0 = W - 330 + 22
    ly = 150
    ax.text(lx0, ly, legend.get("title", "图例 Legend"), fontsize=14,
            fontweight="bold", color="#1B2631", ha="left", va="top")
    ly += 24
    ax.text(lx0, ly, "实体 styles", fontsize=11, fontweight="bold", color="#34495E",
            ha="left", va="top")
    ly += 4
    used_etypes = sorted({e["type"] for e in model["entities"]})
    used_rtypes = sorted({r["type"] for r in model["edges"]})
    for t in used_etypes or NODE_TYPES.keys():
        spec = NODE_TYPES.get(t, NODE_TYPES["other"])
        if t == "small_molecule":
            c = Circle((lx0 + 13, ly + 10), 8, facecolor=spec["fill"],
                       edgecolor=spec["stroke"], linewidth=1.4)
            ax.add_patch(c)
        else:
            box = (FancyBboxPatch((lx0, ly), 26, 16, boxstyle="round,pad=0,rounding_size=8"
                                  if spec["shape"] == "roundrect" else "square,pad=0",
                                  facecolor=spec["fill"], edgecolor=spec["stroke"], linewidth=1.4)
                   if spec["shape"] == "roundrect" else
                   Rectangle((lx0, ly), 26, 16, facecolor=spec["fill"],
                             edgecolor=spec["stroke"], linewidth=1.4))
            ax.add_patch(box)
        ax.text(lx0 + 34, ly + 12, "%s (%s)" % (spec["zh"], t), fontsize=10,
                color="#17202A", ha="left", va="center")
        ly += 24
    ly += 6
    ax.text(lx0, ly, "相互作用 arrows", fontsize=11, fontweight="bold",
            color="#34495E", ha="left", va="top")
    ly += 4
    for t in used_rtypes or EDGE_TYPES.keys():
        spec = legend.get("edges", {}).get(t, EDGE_TYPES.get(t))
        ax.plot([lx0, lx0 + 40], [ly + 8, ly + 8], color=spec["color"], linewidth=2.2)
        _draw_head(ax, lx0 + 40, ly + 8, 0.0, spec["marker"], spec["color"])
        ax.text(lx0 + 48, ly + 12, "%s (%s)" % (spec["zh"], t), fontsize=10,
                color="#17202A", ha="left", va="center")
        ly += 24
    ly += 2
    for ev, wd in EVIDENCE_WIDTH.items():
        ax.plot([lx0, lx0 + 40], [ly + 8, ly + 8], color="#566573", linewidth=wd)
        ax.text(lx0 + 48, ly + 12, "证据强度 evidence: %s" % ev, fontsize=10,
                color="#17202A", ha="left", va="center")
        ly += 24
    case_zh = legend["dash_note"]["zh"]
    ax.text(lx0, ly, case_zh, fontsize=9, color="#566573", ha="left", va="top")
    ly += 18
    if dm.get("field"):
        import matplotlib.colors as mcolors
        import matplotlib.cm as cm
        from matplotlib.colors import LinearSegmentedColormap
        cmap = LinearSegmentedColormap.from_list(
            "ramp", [dm.get("low", "#FFF7E0"), dm.get("high", "#1F4E79")])
        gx = lx0
        ax.add_patch(Rectangle((gx, ly), 90, 10, facecolor=cmap(0.5),
                               edgecolor="#85929E", linewidth=0.8))
        n = 50
        for i in range(n):
            ax.add_patch(Rectangle((gx + 90.0 * i / n, ly), 90.0 / n + 0.2, 10,
                                   facecolor=cmap(i / (n - 1)), edgecolor="none"))
        ax.text(gx, ly + 22, dm.get("label_zh", "") or dm.get("label_en", ""),
                fontsize=9, color="#17202A", ha="left", va="top")
        ax.text(gx + 96, ly + 9, "低 %s  高 %s" % (dm.get("low", ""), dm.get("high", "")),
                fontsize=9, color="#566573", ha="left", va="center")
        ly += 42
    dirn = legend.get("direction_note", {}).get("zh", "")
    if dirn:
        ax.text(lx0, ly, dirn, fontsize=9, color="#566573", ha="left", va="top")

    # ---- meta footer (sources), mirroring the SVG layer-meta ----
    mly = H - 40
    ax.text(36, mly - 26, "sources / 来源:", fontsize=10, color="#7F8C8D",
            ha="left", va="top")
    refs = []
    for ed in layout["entities"].values():
        for s in ed.get("source", []):
            refs.append((s.get("ref", ""), s.get("kind", ""), s.get("line", ""), ed["id"]))
    for r in layout["edges"].values():
        for s in r.get("source", []):
            refs.append((s.get("ref", ""), s.get("kind", ""), s.get("line", ""), r["id"]))
    seen = set()
    for ref, kind, line, who in refs:
        k = (ref, line)
        if k in seen:
            continue
        seen.add(k)
        ax.text(36, mly, "· %s (kind=%s, line=%s) used by %s" % (ref, kind, line, who),
                fontsize=8, color="#7F8C8D", ha="left", va="top")
        mly += 11
        if mly > H - 6:
            break

    has_cjk = any(ord(ch) > 0x2E7F for s in [model.get("title", "")] +
                  [e["name"] for e in model["entities"]] for ch in s)
    font_lower = (font_path or "").lower()
    if has_cjk and not any(k in font_lower for k in
                           ("simhei", "msyh", "yahei", "pingfang", "noto", "wqy", "wenquanyi")):
        warnings.append("未找到支持中文的字体，预览 PNG/PDF 中的中文可能显示为方框；"
                        "可编辑 SVG 不受影响（字体由查看端决定）。font=%s" % font_path)

    out = {"warnings": warnings, "font": font_path}
    if png_path:
        fig.savefig(png_path, dpi=dpi)
        out["png"] = {"path": png_path, "dpi": dpi,
                      "width_px": int(W), "height_px": int(H)}
    if pdf_path:
        fig.savefig(pdf_path, format="pdf")
        out["pdf"] = {"path": pdf_path}
    plt.close(fig)
    return out


def _draw_head(ax, x, y, angle, marker, color):
    """Small marker shapes at (x, y), rotated toward `angle` (radians)."""
    ca, sa = math.cos(angle), math.sin(angle)
    L = 9.0

    def pt(ux, uy):
        # unit point (ux, uy) scaled by L and rotated by `angle`
        return (x + (ux * ca - uy * sa) * L, y + (ux * sa + uy * ca) * L)

    if marker == "arrow":
        ax.fill([pt(-0.15, -0.5)[0], pt(1.0, 0.0)[0], pt(-0.15, 0.5)[0]],
                [pt(-0.15, -0.5)[1], pt(1.0, 0.0)[1], pt(-0.15, 0.5)[1]],
                color=color, edgecolor="none", zorder=5)
    elif marker == "bar":
        ax.plot([pt(0, -0.55)[0], pt(0, 0.55)[0]],
                [pt(0, -0.55)[1], pt(0, 0.55)[1]], color=color,
                linewidth=2.2, zorder=5)
    elif marker == "circle":
        ax.add_patch(Circle((x, y), 3.0, facecolor=color, edgecolor="none", zorder=5))
    elif marker == "diamond":
        ax.fill([pt(-0.2, 0.0)[0], pt(0.0, -0.5)[0], pt(1.0, 0.0)[0], pt(0.0, 0.5)[0]],
                [pt(-0.2, 0.0)[1], pt(0.0, -0.5)[1], pt(1.0, 0.0)[1], pt(0.0, 0.5)[1]],
                color=color, edgecolor="none", zorder=5)


def _label_pos(points):
    if len(points) >= 4:
        return ((points[1][0] + points[2][0]) / 2.0 + 8, points[1][1] - 8)
    mid = points[len(points) // 2]
    return (mid[0] + 8, mid[1] - 8)


if __name__ == "__main__":
    import json, sys
    from layout import compute_layout
    from model import normalize_model, load_json
    model = normalize_model(load_json(sys.argv[1]))
    lay = compute_layout(model)
    out = render_preview(model, lay, sys.argv[2] if len(sys.argv) > 2 else None,
                         sys.argv[3] if len(sys.argv) > 3 else None)
    print(json.dumps(out, ensure_ascii=False, indent=2))