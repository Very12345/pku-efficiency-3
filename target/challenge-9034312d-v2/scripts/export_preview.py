# -*- coding: utf-8 -*-
"""export_preview.py — 从同一布局模型渲染 PNG(PIL) 与 PDF(reportlab) 预览。

可编辑源文件（SVG）→ 预览（PNG/PDF）共用同一 layout 模型与几何换算，
保证「渲染件」与「源文件」视觉一致。全部走本机已确认可用的库：
PIL + 本机中文字体（PNG），reportlab CID 字体（PDF）。

几何换算统一：mm → px = mm / 25.4 * dpi；mm → pt = mm / 25.4 * 72。
"""

from __future__ import annotations

import math
import sys
from typing import Any, Dict, List, Optional, Tuple

import fonts as fonts_mod
from layout import ARROW_LEN_MM

MM2PT = 72.0 / 25.4
ARROW_PT = ARROW_LEN_MM * MM2PT


def _poly_points_pt(layout, scale, ox, oy, pts):
    return [[(p[0] * scale + ox) * MM2PT, (p[1] * scale + oy) * MM2PT] for p in pts]


def _mm2pt(layout, scale, ox, oy, x, y):
    return (x * scale + ox) * MM2PT, (y * scale + oy) * MM2PT


# ================================================================= PNG (PIL)

def render_png(layout: Dict[str, Any], path: str, dpi: int = 200,
               ttf_font: Optional[str] = None) -> Dict[str, Any]:
    """用 PIL 渲染 PNG 预览。返回渲染信息（尺寸/字体/是否成功）。"""
    from PIL import Image, ImageDraw, ImageFont

    canvas = layout["canvas"]
    W, H = canvas["width_mm"], canvas["height_mm"]
    req = layout["requested_canvas"]
    scale = 1.0
    ox = oy = 0.0
    if req["width_mm"] > 0 and req["height_mm"] > 0 and (W > req["width_mm"] or H > req["height_mm"]):
        scale = min(req["width_mm"] / W, req["height_mm"] / H)
        W, H = req["width_mm"], req["height_mm"]

    px_w = max(1, int(W / 25.4 * dpi))
    px_h = max(1, int(H / 25.4 * dpi))
    img = Image.new("RGB", (px_w, px_h), "white")
    draw = ImageDraw.Draw(img)

    font_sz = int(layout["font"]["size_pt"])
    ttf = ttf_font or fonts_mod.find_ttf_font()
    font_obj = None
    if ttf:
        try:
            font_obj = ImageFont.truetype(ttf, font_sz)
        except Exception:  # noqa: BLE001
            font_obj = None
    font_title = None
    if ttf:
        try:
            font_title = ImageFont.truetype(ttf, int(layout["font"]["title_pt"]))
        except Exception:  # noqa: BLE001
            font_title = font_obj
    if font_obj is None:
        font_obj = ImageFont.load_default()

    f = 1.0 / 25.4 * dpi  # mm → px

    # 标题
    draw.text(((W / 2 * f), (8.0 * f)), layout["title"],
              font=font_title or font_obj, fill="#1B3A5C", anchor="ma")

    # 箭头
    for r in layout["relations"]:
        pts = r["points"]
        poly = [((p[0] * scale + ox) * f, (p[1] * scale + oy) * f) for p in pts]
        dash = r["kind"] == "recycle"
        _draw_polyline(draw, poly, width=max(2, int(f * 1.0)), dash=dash,
                       fill="#555555" if not dash else "#8B8B8B")
        # 箭头
        axs = [(r["arrow"][0] * scale + ox) * f, (r["arrow"][1] * scale + oy) * f,
               (r["arrow"][2] * scale + ox) * f, (r["arrow"][3] * scale + oy) * f,
               (r["arrow"][4] * scale + ox) * f, (r["arrow"][5] * scale + oy) * f]
        draw.polygon(axs, fill="#C0392B" if r["kind"] in ("flow", "causation") else "#555555")

    # 实体
    for e in layout["entities"]:
        x, y, w, h = e["x"], e["y"], e["w"], e["h"]
        x0 = (x * scale + ox) * f
        y0 = (y * scale + oy) * f
        w0, h0 = w * scale * f, h * scale * f
        col = e["color"]
        fill, stroke, txt = col.get("fill", "#F4F4F4"), col.get("stroke", "#666"), col.get("text", "#333")
        shape = e.get("shape", "rect")
        if shape == "rounded":
            r_ = min(6.0, h0 / 2.2)
            draw.rounded_rectangle([x0, y0, x0 + w0, y0 + h0], radius=r_, fill=fill, outline=stroke, width=2)
        elif shape == "diamond":
            cx, cy = x0 + w0 / 2, y0 + h0 / 2
            draw.polygon([(cx, y0), (x0 + w0, cy), (cx, y0 + h0), (x0, cy)], fill=fill, outline=stroke)
        else:
            draw.rectangle([x0, y0, x0 + w0, y0 + h0], fill=fill, outline=stroke, width=2)
        lines = e.get("lines") or [e["display_label"]]
        line_h = (font_sz * MM2PT + 3) / 25.4 * dpi
        yy = y0 + h0 / 2 - (len(lines) - 1) * line_h / 2
        for i, ln in enumerate(lines):
            draw.text((x0 + w0 / 2, yy + i * line_h), ln, font=font_obj, fill=txt, anchor="ma")

    # 图例
    ly = (H - 8.0) * f
    lx = 12.0 * f
    for item in layout["legend"]:
        draw.rectangle([lx, ly, lx + 8, ly + 8], fill=item["fill"], outline=item["stroke"], width=1)
        txt = f"{item['label']}  ({item['kind']})"
        draw.text((lx + 12, ly - 1), txt, font=font_obj, fill="#333333", anchor="la")
        t = draw.textlength(txt, font=font_obj)
        lx += 12 + t + 14

    img.save(path, "PNG", dpi=(dpi, dpi))
    return {"file": path, "format": "png", "width_px": px_w, "height_px": px_h,
            "dpi": dpi, "font_ttf": ttf, "font_found": ttf is not None}


def _draw_polyline(draw, pts, width=2, fill="#555555", dash=False):
    """PIL 折线（支持虚线近似：逐段画）。"""
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        if dash:
            _dashed_line(draw, a, b, width=width)
        else:
            draw.line([a, b], fill=fill, width=width)


def _dashed_line(draw, a, b, width=2, dash_len=8):
    """简单虚线：按线段等分。"""
    x1, y1 = a
    x2, y2 = b
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy)
    if L < 1e-3:
        return
    n = max(1, int(L // (dash_len * 2)))
    for i in range(n):
        t0 = i / n
        t1 = min(1.0, (i + 0.5) / n)
        draw.line([(x1 + dx * t0, y1 + dy * t0), (x1 + dx * t1, y1 + dy * t1)],
                  fill="#8B8B8B", width=width)


# ================================================================= PDF (reportlab)

def render_pdf(layout: Dict[str, Any], path: str) -> Dict[str, Any]:
    """用 reportlab 渲染 PDF 预览（矢量，CID 中文字体）。"""
    from reportlab.lib import colors as rl_colors
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.pdfgen import canvas

    cid = fonts_mod.reportlab_font_name()
    try:
        pdfmetrics.registerFont(UnicodeCIDFont(cid))
    except Exception:  # noqa: BLE001
        cid = "Helvetica"

    canvas_ = layout["canvas"]
    W, H = canvas_["width_mm"], canvas_["height_mm"]
    req = layout["requested_canvas"]
    scale = 1.0
    ox = oy = 0.0
    if req["width_mm"] > 0 and req["height_mm"] > 0 and (W > req["width_mm"] or H > req["height_mm"]):
        scale = min(req["width_mm"] / W, req["height_mm"] / H)
        W, H = req["width_mm"], req["height_mm"]

    c = canvas.Canvas(path, pagesize=(W * MM2PT, H * MM2PT))
    c.setTitle(layout["title"])
    out_path = str(path)  # reportlab 可能把 path 包装成文件对象，先固化字符串

    fs = layout["font"]["size_pt"]

    def P(x, y):
        return (x * scale + ox) * MM2PT, (H - y * scale - oy) * MM2PT  # PDF 原点左下

    # 标题
    c.setFont(cid, layout["font"]["title_pt"])
    c.setFillColor(rl_colors.HexColor("#1B3A5C"))
    cx = W / 2
    c.drawCentredString(cx * MM2PT, (H - 12.0) * MM2PT, layout["title"])

    # 箭头
    for r in layout["relations"]:
        pts = r["points"]
        p0 = P(*pts[0])
        c.setStrokeColor(rl_colors.HexColor("#555555"))
        c.setLineWidth(1.0)
        if r["kind"] == "recycle":
            c.setDash(3, 2)
        c.setLineCap(1)
        path = c.beginPath()
        path.moveTo(p0[0], p0[1])
        for p in pts[1:]:
            pp = P(*p)
            path.lineTo(pp[0], pp[1])
        c.drawPath(path)
        if r["kind"] == "recycle":
            c.setDash()  # reset
        # 箭头三角
        ax, ay, bx, by, tx, ty = [v for v in r["arrow"][:6]]
        tri = [P(ax, ay), P(bx, by), P(tx, ty)]
        tp = c.beginPath()
        tp.moveTo(tri[0][0], tri[0][1])
        tp.lineTo(tri[1][0], tri[1][1])
        tp.lineTo(tri[2][0], tri[2][1])
        tp.close()
        c.setFillColor(rl_colors.HexColor("#C0392B" if r["kind"] in ("flow", "causation") else "#555555"))
        c.setStrokeColor(rl_colors.HexColor("#C0392B" if r["kind"] in ("flow", "causation") else "#555555"))
        c.drawPath(tp, stroke=1, fill=1)

    # 实体
    for e in layout["entities"]:
        x, y, w, h = e["x"], e["y"], e["w"], e["h"]
        x0, y0 = P(x, y + h)   # 左上角
        w0, h0 = w * MM2PT * scale, h * MM2PT * scale
        col = e["color"]
        fill = rl_colors.HexColor(col.get("fill", "#F4F4F4"))
        stroke = rl_colors.HexColor(col.get("stroke", "#666"))
        txt = rl_colors.HexColor(col.get("text", "#333"))
        shape = e.get("shape", "rect")

        c.setFillColor(fill)
        c.setStrokeColor(stroke)
        c.setLineWidth(1.2)
        if shape == "rounded":
            r_ = min(5.0, h0 / 2.2)
            c.roundRect(x0, y0 - h0, w0, h0, r_, stroke=1, fill=1)
        elif shape == "diamond":
            cx_, cy_ = x0 + w0 / 2, y0 - h0 / 2
            d = c.beginPath()
            d.moveTo(cx_, y0)
            d.lineTo(x0 + w0, cy_)
            d.lineTo(cx_, y0 - h0)
            d.lineTo(x0, cy_)
            d.close()
            c.drawPath(d, stroke=1, fill=1)
        else:
            c.rect(x0, y0 - h0, w0, h0, stroke=1, fill=1)

        lines = e.get("lines") or [e["display_label"]]
        line_h = (fs * MM2PT + 3)
        ty = y0 - h0 / 2 + (len(lines) - 1) * line_h / 2
        c.setFont(cid, fs)
        c.setFillColor(txt)
        for i, ln in enumerate(lines):
            c.drawCentredString(x0 + w0 / 2, ty - i * line_h - fs * MM2PT / 2.2, ln)

    # 图例
    c.setFont(cid, 9)
    lx = 12.0 * MM2PT
    ly = (H - 10.0) * MM2PT
    for item in layout["legend"]:
        c.setFillColor(rl_colors.HexColor(item["fill"]))
        c.setStrokeColor(rl_colors.HexColor(item["stroke"]))
        c.rect(lx, ly, 8, 8, stroke=1, fill=1)
        c.setFillColor(rl_colors.HexColor("#333333"))
        c.setFont(cid, 9)
        txt_ = f"{item['label']}  ({item['kind']})"
        c.drawString(lx + 12, ly, txt_)
        lx += 12 + c.stringWidth(txt_, cid, 9) + 14

    c.showPage()
    c.save()
    return {"file": out_path, "format": "pdf",
            "width_pt": W * MM2PT, "height_pt": H * MM2PT,
            "font": cid, "vector": True}