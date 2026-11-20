# -*- coding: utf-8 -*-
"""preview.py — honest PNG previews of the built deck via PIL.

Part of the "paper-to-academic-ppt" Skill.

Why honest: without PowerPoint or LibreOffice we cannot run the real rendering
engine, so these previews are an *approximation*: they re-compose the same
content (title / claim / bullets / figure box / footer) with PIL so a reviewer
can inspect structure and spot overflow. Every preview file is named
"preview-approx-*" and carries a watermark, and run_meta.rendered_with records
"pil-approximation (no PowerPoint/LibreOffice)". They are NOT screenshots of the
.pptx rendered by PowerPoint.

Also exposed here: make_chart() — render a bar/line chart from numbers that the
spec explicitly declares as reconstructed from a paper table (kind=
"reconstructed_chart"); the PNG is embedded in the deck and the evidence entry
records "reconstructed_from_table". matplotlib is optional; if missing the chart
is skipped and recorded honestly.
"""
from __future__ import annotations

import io
import os

from PIL import Image, ImageDraw, ImageFont

from deck_builder import ACADEMIC_THEME, _clip_text


# --------------------------------------------------------------------------- #
# Font discovery (Windows + common Linux paths, then PIL default)
# --------------------------------------------------------------------------- #
FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyh.ttc",        # 微软雅黑 (Windows)
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\simsun.ttc",
    r"C:\Windows\Fonts\arial.ttf",
    r"C:\Windows\Fonts\times.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/truetype/arphic/uming.ttc",
]


def find_fonts():
    """Return dict of resolved PIL fonts for preview rendering."""
    path = None
    for cand in FONT_CANDIDATES:
        if os.path.isfile(cand):
            path = cand
            break
    fonts = {}
    try:
        if path:
            fonts["title"] = ImageFont.truetype(path, 34)
            fonts["claim"] = ImageFont.truetype(path, 18)
            fonts["body"] = ImageFont.truetype(path, 20)
            fonts["small"] = ImageFont.truetype(path, 12)
            fonts["font_path"] = path
        else:
            fonts["title"] = ImageFont.load_default(size=34)
            fonts["claim"] = ImageFont.load_default(size=18)
            fonts["body"] = ImageFont.load_default(size=20)
            fonts["small"] = ImageFont.load_default(size=12)
            fonts["font_path"] = None
    except Exception:
        fonts["title"] = ImageFont.load_default(size=34)
        fonts["claim"] = ImageFont.load_default(size=18)
        fonts["body"] = ImageFont.load_default(size=20)
        fonts["small"] = ImageFont.load_default(size=12)
        fonts["font_path"] = None
    return fonts


def _wrap(draw, text, font, max_w):
    lines = []
    for chunk in (text or "").split("\n"):
        if not chunk:
            lines.append("")
            continue
        cur = ""
        for ch in chunk:
            if draw.textlength(cur + ch, font=font) <= max_w:
                cur += ch
            else:
                lines.append(cur)
                cur = ch
        lines.append(cur)
    return lines


def _norm_color(c):
    if isinstance(c, tuple):
        return c
    if hasattr(c, "__iter__"):
        v = list(c)
        return (v[0], v[1], v[2])
    return (38, 38, 38)


def render_slide_png(spec_slide, page_no, total, deck_title, fonts, out_path, width=1280):
    """Draw one slide frame. Returns (out_path, overflow_warnings)."""
    from deck_builder import MAX_BULLETS

    scale = width / 1280.0
    height = int(720 * scale)
    img = Image.new("RGB", (width, height), _norm_color(ACADEMIC_THEME["white"]))
    d = ImageDraw.Draw(img)

    f_title, f_claim, f_body, f_small = fonts["title"], fonts["claim"], fonts["body"], fonts["small"]
    warn = []

    # header band
    d.rectangle([0, 0, width, int(88 * scale)], fill=_norm_color(ACADEMIC_THEME["primary"]))
    title = _clip_text(spec_slide.get("title") or "Untitled", 40)
    d.text((int(28 * scale), int(22 * scale)), title, font=f_title, fill=(255, 255, 255))
    claim = spec_slide.get("claim")
    y = int(108 * scale)
    if claim:
        claim_lines = _wrap(d, "主张：" + _clip_text(claim, 110), f_claim, int(1150 * scale))
        for ln in claim_lines:
            d.text((int(30 * scale), y), ln, font=f_claim, fill=_norm_color(ACADEMIC_THEME["accent"]))
            y += int(30 * scale)
    y += int(16 * scale)

    bullets = (spec_slide.get("bullets") or [])[:MAX_BULLETS]
    for b in bullets:
        text = b[0] if isinstance(b, (list, tuple)) else str(b)
        wrapped = _wrap(d, "• " + text, f_body, int(1150 * scale))
        for ln in wrapped:
            d.text((int(30 * scale), y), ln, font=f_body, fill=(38, 38, 38))
            y += int(32 * scale)
        if y > int(600 * scale):
            warn.append("overflow_approx: bullets exceed content area")
            d.text((int(30 * scale), int(610 * scale)), "⚠ 溢出（近似检测）",
                   font=f_small, fill=_norm_color(ACADEMIC_THEME["warn"]))
            break
    if spec_slide.get("figure"):
        fx = int(966 * scale) if False else int(850 * scale)
        d.rectangle([int(870 * scale), int(150 * scale), width - int(30 * scale), int(560 * scale)],
                    outline=_norm_color(ACADEMIC_THEME["accent"]), width=3)
        fig = spec_slide["figure"]
        d.text((int(890 * scale), int(170 * scale)),
               "【%s】" % (fig.get("ref") or "Fig"),
               font=f_body, fill=_norm_color(ACADEMIC_THEME["primary"]))
        d.text((int(890 * scale), int(210 * scale)),
               _clip_text(fig.get("label") or "", 46),
               font=f_small, fill=(90, 90, 90))
        d.text((int(890 * scale), int(480 * scale)),
               "(预览为占位框；实际图像已嵌入 .pptx 或按占位处理)",
               font=f_small, fill=(150, 150, 150))
    if spec_slide.get("table"):
        d.rectangle([int(870 * scale), int(150 * scale), width - int(30 * scale), int(560 * scale)],
                    outline=_norm_color(ACADEMIC_THEME["accent"]), width=3)
        d.text((int(890 * scale), int(170 * scale)),
               "【%s】(表格已嵌入 .pptx)" % (spec_slide["table"].get("ref") or "Table"),
               font=f_body, fill=_norm_color(ACADEMIC_THEME["primary"]))

    # footer with watermark
    y = int(676 * scale)
    d.line([int(30 * scale), y, width - int(30 * scale), y], fill=(200, 200, 200))
    d.text((int(30 * scale), int(688 * scale)),
           "%s  ·  %d / %d" % (_clip_text(deck_title, 40), page_no, total),
           font=f_small, fill=(120, 120, 120))
    d.text((width - int(430 * scale), int(688 * scale)),
           "preview-approx (PIL 近似渲染)", font=f_small, fill=(160, 160, 160))
    img.save(out_path, "PNG")
    return out_path, warn


def render_all(spec, deck_meta, out_dir):
    """Render the cover + every slide frame. Returns previews record list."""
    fonts = find_fonts()
    slides = (spec.get("slides") or [])[:]
    total = deck_meta.get("slide_count") or (len(slides) + 2)
    deck_title = spec.get("deck_title") or "Academic Talk"
    records = []
    # cover
    cover = {
        "page": 0,
        "kind": "cover",
        "title": deck_title,
        "bullets": [],
    }
    f = os.path.join(out_dir, "preview-approx-cover.png")
    ff = {}
    for k in fonts:
        ff[k] = fonts[k]
    _render_single(cover, 0, total, deck_title, ff, f)
    records.append({"slide": 0, "file": os.path.basename(f), "kind": "pil-approximation"})
    for i, s in enumerate(slides, start=1):
        f = os.path.join(out_dir, "preview-approx-%03d.png" % i)
        _, warn = render_slide_png(s, i, total, deck_title, fonts, f)
        rec = {"slide": i, "file": os.path.basename(f), "kind": "pil-approximation"}
        if warn:
            rec["warnings"] = warn
        records.append(rec)
    return records


def _render_single(slide, page_no, total, deck_title, fonts, out_path):
    img = Image.new("RGB", (1280, 720), _norm_color(ACADEMIC_THEME["primary"]))
    d = ImageDraw.Draw(img)
    t = (slide.get("title") or deck_title)
    d.text((60, 240), _clip_text(t, 40), font=fonts["title"], fill=(255, 255, 255))
    if slide.get("bullets"):
        d.text((60, 340), " • ".join(str(x[0] if isinstance(x, (list, tuple)) else x)
                                     for x in slide["bullets"]),
               font=fonts["small"], fill=(230, 240, 255))
    d.text((60, 660), "preview-approx (PIL 近似渲染)", font=fonts["small"], fill=(200, 215, 235))
    img.save(out_path, "PNG")


# --------------------------------------------------------------------------- #
# Reconstructed chart (matplotlib, optional)
# --------------------------------------------------------------------------- #
def make_chart(spec_fig, out_dir, width_in=6.4, height_in=4.2, dpi=110):
    """Render a chart from numbers the spec declares reconstructed from a paper
    table. Returns {"file": path, "png": bool, "svg": bool} or None on skip."""
    data = spec_fig.get("data") or {}
    cats = data.get("categories") or []
    series = data.get("series") or []
    if not cats or not series:
        return {"file": None, "png": False, "svg": False,
                "reason": "no chart data in spec (figure may be a paper image instead)"}
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as exc:
        return {"file": None, "png": False, "svg": False, "reason": "matplotlib missing: %s" % exc}
    try:
        import re
        # CJK-friendly chart title: the drawn title is ASCII-safe (ref-based);
        # the full Chinese label lives in the slide caption / evidence mapping.
        safe_ref = re.sub(r'[^\x00-\x7F]+', "", str(spec_fig.get("ref") or ""))
        title = safe_ref or "Reconstructed chart"
        fig, ax = plt.subplots(figsize=(width_in, height_in))
        for s in series:
            vals = s.get("values") or []
            kw = {}
            if s.get("kind") == "line":
                ax.plot(cats, vals, marker="o", label=s.get("name"), **kw)
            else:
                ax.bar(cats, vals, label=s.get("name"), alpha=0.8)
        ax.set_xlabel(" ".join(cats).title() if len(cats) > 6 else "")
        ax.set_title(_clip_text(str(title), 50), fontsize=10)
        if len(series) > 1:
            ax.legend(fontsize=8)
        ax.grid(axis="y", alpha=0.3)
        fig.tight_layout()
        base = "chart-%s" % (safe_ref or "fig").replace(" ", "_").replace(".", "")
        png_path = os.path.join(out_dir, base + ".png")
        fig.savefig(png_path, dpi=dpi)
        svg_path = None
        try:  # editable SVG source (cairosvg not required; SVG is the source file)
            svg_path = os.path.join(out_dir, base + ".svg")
            fig.savefig(svg_path, format="svg")
        except Exception:
            svg_path = None
        import matplotlib as _m
        _m.pyplot.close(fig)
        return {"file": png_path, "png": True, "svg": os.path.basename(svg_path) if svg_path else None,
                "note": "reconstructed_from_table; numbers are those declared in spec and must match the paper table",
                "title_used": str(title)}
    except Exception as exc:
        return {"file": None, "png": False, "svg": False, "reason": "chart error: %s" % exc}


if __name__ == "__main__":
    import json
    import sys

    spec_path, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    spec = json.load(open(spec_path, encoding="utf-8"))
    rec = render_all(spec, {"slide_count": len(spec.get("slides", [])) + 2}, out_dir)
    print(json.dumps(rec, ensure_ascii=False, indent=2))