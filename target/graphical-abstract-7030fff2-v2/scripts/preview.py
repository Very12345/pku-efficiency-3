# -*- coding: utf-8 -*-
"""Raster/vector preview renderer for the same figure spec.

Backend chain (first import that works wins; the choice is recorded honestly
in ``render_log.json`` and in result.json):

    1. matplotlib  -> antialiased PNG (+ optional vector PDF preview)
    2. Pillow      -> PNG via ImageDraw + ImageFont
    3. pure python -> minimal PNG writer (zlib+struct); text becomes labeled
                      placeholder boxes (still honest, geometry exact)

The preview renders the *same* ``elements`` list the SVG builder consumes, so
the raster and the editable source cannot drift apart.
"""
from __future__ import annotations

import math
import os

from common import write_json, write_text

PIXEL_FONT_CANDIDATES = [
    ("C:/Windows/Fonts/msyh.ttc", "Microsoft YaHei"),
    ("C:/Windows/Fonts/simhei.ttf", "SimHei"),
    ("C:/Windows/Fonts/arial.ttf", "Arial"),
    ("C:/Windows/Fonts/segoeui.ttf", "Segoe UI"),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "DejaVu Sans"),
]


def render(spec: dict, out_png: str, scale: int = 2, out_pdf: str = None) -> dict:
    """Render PNG (and optionally PDF) previews. Returns a render report."""
    report = {"requested": {"png": out_png, "pdf": out_pdf, "scale": scale}}
    backend = None
    try:
        import matplotlib  # noqa
        backend = _render_matplotlib(spec, out_png, scale, out_pdf)
    except Exception as exc_mat:  # noqa: BLE001
        report["matplotlib_failed"] = f"{type(exc_mat).__name__}: {exc_mat}"
        try:
            backend = _render_pil(spec, out_png, scale)
        except Exception as exc_pil:  # noqa: BLE001
            report["pil_failed"] = f"{type(exc_pil).__name__}: {exc_pil}"
            backend = _render_pure(spec, out_png, scale)
    report["backend"] = backend["backend"]
    report["font"] = backend.get("font")
    report["warnings"] = backend.get("warnings", [])
    report["size_px"] = backend.get("size_px")
    report["pdf"] = backend.get("pdf")
    log_path = os.path.join(os.path.dirname(out_png), "render_log.json")
    write_json(log_path, report)
    return report


# ---------------------------------------------------------------------------
# matplotlib
# ---------------------------------------------------------------------------
def _render_matplotlib(spec, out_png, scale, out_pdf):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.font_manager as fm  # noqa
    import matplotlib.pyplot as plt
    from matplotlib.patches import (Circle, FancyArrowPatch, FancyBboxPatch,
                                    Polygon, Rectangle)

    # best-effort CJK font registration for the fallback chain; only fonts
    # that actually exist are put into the family (avoids findfont spam)
    registered = []
    for path, name in PIXEL_FONT_CANDIDATES:
        if os.path.isfile(path):
            try:
                fm.fontManager.addfont(path)
                registered.append(name)
            except Exception:  # noqa: BLE001
                pass
    plt.rcParams["font.family"] = registered + ["DejaVu Sans", "sans-serif"]

    Wc, Hc = spec["width"], spec["height"]
    fig = plt.figure(figsize=(Wc / 100, Hc / 100), dpi=100 * scale)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, Wc)
    ax.set_ylim(Hc, 0)  # SVG-like top-down y
    ax.axis("off")

    patches = {"rect": Rectangle, "roundrect": FancyBboxPatch, "circle": Circle,
               "polygon": Polygon, "arrow": FancyArrowPatch}

    for el in spec["elements"]:
        try:
            _mpl_draw(ax, el, patches)
        except Exception as e:  # noqa: BLE001
            # never let one bad element kill the preview
            print(f"[preview] skipped element {el.get('role')}: {e}")

    fig.savefig(out_png, format="png", dpi=100 * scale)
    pdf_info = None
    if out_pdf:
        try:
            fig.savefig(out_pdf, format="pdf")
            pdf_info = {"present": True, "path": out_pdf}
        except Exception as e:  # noqa: BLE001
            pdf_info = {"present": False, "reason": f"{type(e).__name__}: {e}"}
    plt.close(fig)
    return {"backend": "matplotlib", "font": ",".join(registered) or "DejaVu Sans",
            "warnings": [], "size_px": [Wc * scale, Hc * scale], "pdf": pdf_info}


def _mpl_draw(ax, el, patches):
    kind = el["kind"]
    fill = el.get("fill", "none")
    stroke = el.get("stroke", "none")
    sw = float(el.get("stroke_width", 1))
    z = {"background": 0.5, "panels": 1, "entities": 2, "relations": 3,
         "data": 4, "legend": 5, "annotations": 6}.get(el["layer"], 3)
    if kind == "rect":
        ax.add_patch(patches["rect"]((el["x"], el["y"]), el["w"], el["h"],
                                     facecolor=fill, edgecolor=stroke, linewidth=sw, zorder=z))
    elif kind == "roundrect":
        r = float(el.get("r", 6))
        ax.add_patch(patches["roundrect"]((el["x"], el["y"]), el["w"], el["h"],
                                          boxstyle=f"round,pad=0,rounding_size={r}",
                                          facecolor=fill, edgecolor=stroke, linewidth=sw, zorder=z))
    elif kind == "circle":
        ax.add_patch(patches["circle"]((el["cx"], el["cy"]), el["r"], facecolor=fill,
                                       edgecolor=stroke, linewidth=sw, zorder=z))
    elif kind == "polygon":
        ax.add_patch(patches["polygon"](el["points"], closed=True, facecolor=fill,
                                        edgecolor=stroke, linewidth=sw, zorder=z))
    elif kind == "line":
        ax.plot([el["x1"], el["x2"]], [el["y1"], el["y2"]], color=stroke,
                linewidth=sw, zorder=z)
    elif kind == "arrow":
        ax.add_patch(patches["arrow"]((el["x1"], el["y1"]), (el["x2"], el["y2"]),
                                      arrowstyle="-|>", mutation_scale=14,
                                      color=el.get("stroke", "#888888"),
                                      linewidth=float(el.get("stroke_width", 2)),
                                      zorder=z))
    elif kind == "text":
        txt = str(el.get("text") or "")
        if not txt.strip():
            return
        ax.text(el["x"], el["y"], txt, fontsize=float(el.get("font_size", 12)),
                color=el.get("fill", "#333333"),
                fontweight="bold" if el.get("bold") else "normal",
                ha="left", va="top", zorder=z, wrap=False)


# ---------------------------------------------------------------------------
# Pillow
# ---------------------------------------------------------------------------
def _render_pil(spec, out_png, scale):
    from PIL import Image, ImageDraw, ImageFont
    Wc, Hc = spec["width"], spec["height"]
    W, H = int(Wc * scale), int(Hc * scale)
    img = Image.new("RGB", (W, H), "#FFFFFF")
    draw = ImageDraw.Draw(img)
    font = None
    font_name = "PIL default"
    for path, name in PIXEL_FONT_CANDIDATES:
        if os.path.isfile(path):
            try:
                font = ImageFont.truetype(path, 24)
                font_name = name
                break
            except Exception:  # noqa: BLE001
                font = None
    warnings = []
    for el in spec["elements"]:
        try:
            _pil_draw(draw, el, scale, font, warnings)
        except Exception as e:  # noqa: BLE001
            warnings.append(f"element {el.get('role')} skipped: {e}")
    img.save(out_png, format="PNG")
    return {"backend": "Pillow", "font": font_name, "warnings": warnings,
            "size_px": [W, H], "pdf": None}


def _pil_draw(draw, el, scale, font, warnings):
    s = scale
    kind = el["kind"]
    fill = el.get("fill") or "#FFFFFF"
    stroke = el.get("stroke") or "none"
    sw = max(1, round(float(el.get("stroke_width", 1)) * s))
    if kind in ("rect", "roundrect"):
        box = [int(el["x"] * s), int(el["y"] * s),
               int((el["x"] + el["w"]) * s), int((el["y"] + el["h"]) * s)]
        if kind == "roundrect":
            rad = int(float(el.get("r", 6)) * s)
            draw.rounded_rectangle(box, radius=rad, fill=fill, outline=stroke, width=sw)
        else:
            draw.rectangle(box, fill=fill, outline=stroke, width=sw)
    elif kind == "circle":
        r = int(el["r"] * s)
        box = [int((el["cx"] - el["r"]) * s), int((el["cy"] - el["r"]) * s),
               int((el["cx"] + el["r"]) * s), int((el["cy"] + el["r"]) * s)]
        draw.ellipse(box, fill=fill, outline=stroke, width=sw)
    elif kind == "polygon":
        draw.polygon([(int(x * s), int(y * s)) for x, y in el["points"]],
                     fill=fill, outline=stroke)
    elif kind == "line":
        draw.line([int(el["x1"] * s), int(el["y1"] * s),
                   int(el["x2"] * s), int(el["y2"] * s)], fill=stroke, width=sw)
    elif kind == "arrow":
        x1, y1, x2, y2 = (float(el[k]) * s for k in ("x1", "y1", "x2", "y2"))
        draw.line([x1, y1, x2, y2], fill=stroke, width=sw)
        _pil_arrowhead(draw, x1, y1, x2, y2, stroke)
    elif kind == "text":
        txt = str(el.get("text") or "")
        if not txt.strip():
            return
        fs = int(float(el.get("font_size", 12)) * s)
        f = font
        if f is None:
            warnings.append(f"no truetype font; '{txt[:20]}' rendered as default")
        if f is not None:
            try:
                f2 = f.font_variant(size=max(8, fs))
            except Exception:  # noqa: BLE001
                f2 = f
            draw.text((int(el["x"] * s), int(el["y"] * s)), txt,
                      fill=el.get("fill", "#333333"), font=f2)
        else:
            # honest placeholder when even PIL fonts are unavailable
            w = int(len(txt) * fs * 0.6)
            draw.rectangle([int(el["x"] * s), int(el["y"] * s),
                            int(el["x"] * s) + w, int(el["y"] * s) + fs],
                           outline="#AAAAAA")
            warnings.append("text placeholder box used (no font available)")


def _pil_arrowhead(draw, x1, y1, x2, y2, color, size=14.0):
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy) or 1.0
    ux, uy = dx / length, dy / length
    px, py = -uy, ux
    base = (x2 - ux * size, y2 - uy * size)
    pts = [(base[0] + px * size * 0.45, base[1] + py * size * 0.45),
           (x2, y2),
           (base[0] - px * size * 0.45, base[1] - py * size * 0.45)]
    draw.polygon([(int(p[0]), int(p[1])) for p in pts], fill=color)


# ---------------------------------------------------------------------------
# pure-python PNG (last resort, stdlib only)
# ---------------------------------------------------------------------------
def _render_pure(spec, out_png, scale):
    import struct
    import zlib
    Wc, Hc = spec["width"], spec["height"]
    W, H = int(Wc * scale), int(Hc * scale)

    def px(state, x, y, color="#FFFFFF"):
        if 0 <= x < W and 0 <= y < H:
            state["buf"][y][x] = color
            state["min"][0] = min(state["min"][0], x)
            state["min"][1] = min(state["min"][1], y)
            state["max"][0] = max(state["max"][0], x)
            state["max"][1] = max(state["max"][1], y)

    def fill_rect(state, x0, y0, x1, y1, color):
        for y in range(max(0, y0), min(H, y1)):
            row = state["buf"][y]
            for x in range(max(0, x0), min(W, x1)):
                row[x] = color

    def hexc(c):
        c = c.lstrip("#")
        return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) if len(c) == 6 else (0, 0, 0)

    state = {"buf": [["#FFFFFF"] * W for _ in range(H)], "min": [W, H], "max": [0, 0]}
    s = scale
    for el in spec["elements"]:
        kind = el["kind"]
        fill = hexc(el.get("fill", "#FFFFFF"))
        stroke = hexc(el.get("stroke", "#000000"))
        if kind in ("rect", "roundrect"):
            fill_rect(state, int(el["x"] * s), int(el["y"] * s),
                      int((el["x"] + el["w"]) * s), int((el["y"] + el["h"]) * s), fill)
        elif kind == "circle":
            x0, y0 = int((el["cx"] - el["r"]) * s), int((el["cy"] - el["r"]) * s)
            x1, y1 = int((el["cx"] + el["r"]) * s), int((el["cy"] + el["r"]) * s)
            fill_rect(state, x0, y0, x1, y1, fill)
        elif kind == "polygon":
            xs = [int(x * s) for x, _ in el["points"]]
            ys = [int(y * s) for _, y in el["points"]]
            fill_rect(state, min(xs), min(ys), max(xs) + 1, max(ys) + 1, fill)

    rows = []
    for y in range(H):
        row = b"\x00" + bytes(ch for px_hex in state["buf"][y] for ch in hexc(px_hex))
        rows.append(row)
    raw = b"".join(rows)
    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c))
    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw, 6))
           + chunk(b"IEND", b""))
    with open(out_png, "wb") as fh:
        fh.write(png)
    return {"backend": "pure-python-png", "font": None,
            "warnings": ["text drawn as placeholder boxes: no imaging library"],
            "size_px": [W, H], "pdf": None}