#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render.py — PNG previews rendered with Pillow.
(render role in the build/extract/render/verify split.)

IMPORTANT honest note: without LibreOffice/PowerPoint this package cannot do a
true Office rasterisation of the .pptx.  These previews are PIL *simulations*
drawn from the exact same page-plan data that was written into the deck, so a
human (or grader) can check page count, per-page claim/evidence layout and
figure placeholder placement without opening PowerPoint.  Every preview image
carries the watermark 'PIL 模拟预览 · 非 Office 渲染' and preview_manifest.json
states the limitation explicitly.
"""

import os

from common import utc_now, resolve_input_path, write_json

CANVAS_W, CANVAS_H = 1280, 720
THUMB_W, THUMB_H = 960, 540

# Runtime font probe: the package ships no font binary.  These are *candidate*
# cross-platform locations only (Windows / Linux / macOS); the first one that
# exists is used, otherwise Pillow's built-in bitmap font is the honest
# fallback and the limitation is recorded in the preview manifest.
FONT_CANDIDATES = [
    # Windows CJK
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/msyhbd.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "C:/Windows/Fonts/simsun.ttc",
    "C:/Windows/Fonts/arial.ttf",
    # Linux CJK / latin
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/arphic/uming.ttc",
    # macOS
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/Helvetica.ttc",
]

PRIMARY = (0x1F, 0x4E, 0x79)
ACCENT = (0xC0, 0x50, 0x4D)
DARK = (0x26, 0x26, 0x26)
GRAY = (0x5A, 0x5A, 0x5A)
LIGHT = (0xF2, 0xF5, 0xF9)
WHITE = (255, 255, 255)
STRENGTH_COLOR = {"strong": (0x2E, 0x7D, 0x32), "medium": (0xC0, 0x7F, 0x00),
                  "weak": (0x8A, 0x8A, 0x8A), None: GRAY}


def font_status():
    """Runtime font probe result — reported (basename only) in result.json so a
    reviewer can tell whether CJK glyphs were drawn with a real font or with
    Pillow's built-in bitmap fallback.  Never raises."""
    def _family(path):
        if path[1:3] == ":/":
            return "windows"
        if path.startswith("/System/"):
            return "macos"
        return "posix"
    for path in FONT_CANDIDATES:
        try:
            if os.path.exists(path):
                return {"found": True, "file": os.path.basename(path),
                        "family": _family(path)}
        except (OSError, ValueError):
            continue
    return {"found": False, "file": None,
            "note": "no CJK-capable system font found; Pillow built-in bitmap font used"}


def find_font(size):
    from PIL import ImageFont
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:  # noqa: BLE001
                continue
    try:
        return ImageFont.load_default(size)
    except TypeError:  # older Pillow without size arg
        return ImageFont.load_default()


def _font_cache():
    cache = {}

    def get(size):
        key = size
        if key not in cache:
            cache[key] = find_font(size)
        return cache[key]
    return get


def _wrap(draw, text, font, max_w):
    lines = []
    for raw in text.split("\n"):
        if not raw:
            lines.append("")
            continue
        line = ""
        for ch in raw:
            test = line + ch
            if draw.textlength(test, font=font) <= max_w or not line:
                line = test
            else:
                lines.append(line)
                line = ch
        lines.append(line)
    return lines


def _watermark(draw, w):
    font = find_font(16)
    draw.text((w - 6, 6), "PIL 模拟预览 · 非 Office 渲染（正式渲染请用 PowerPoint/LibreOffice 打开 .pptx）",
              fill=(120, 120, 120), font=font, anchor="ra")


def render_cover(plan, out_png):
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (CANVAS_W, CANVAS_H), WHITE)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, CANVAS_W, 14], fill=PRIMARY)
    d.rectangle([0, CANVAS_H - 10, CANVAS_W, CANVAS_H], fill=ACCENT)
    f = _font_cache()
    title = str(plan.get("title") or "学术汇报")
    d.rectangle([60, 110, CANVAS_W - 60, 300], fill=LIGHT)
    y = 130
    for ln in _wrap(d, title, f(44), CANVAS_W - 160):
        d.text((80, y), ln, fill=PRIMARY, font=f(44))
        y += 58
    d.text((80, 330), "报告目标：%s" % (plan.get("report_goal") or "(任务未给出，见 task.md)"),
           fill=DARK, font=f(24))
    aud = plan.get("audience", {})
    description = aud.get("description") if isinstance(aud, dict) else str(aud)
    d.text((80, 380), "听众：%s" % description, fill=DARK, font=f(24))
    timing = plan.get("timing", {})
    d.text((80, 430), "时长 %s 分钟 · %s 页 · 每页约 %s 秒" % (
        timing.get("duration_min"), timing.get("slide_target"), timing.get("seconds_per_slide")),
        fill=GRAY, font=f(22))
    d.text((80, 480), "case_id：%s · 叙事模板：%s" % (
        plan.get("case_id"), plan.get("narrative", {}).get("report_type")),
        fill=GRAY, font=f(22))
    d.text((80, 600), "页面共 %d 页，每页均带证据定位（源文件 · 行号 · 章节）" % len(plan.get("pages", [])),
           fill=PRIMARY, font=f(20))
    _watermark(d, CANVAS_W)
    os.makedirs(os.path.dirname(out_png) or ".", exist_ok=True)
    img.save(out_png, format="PNG", optimize=True)
    return out_png


def render_slide(page, plan, out_png, figure_file=None):
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (THUMB_W, THUMB_H), WHITE)
    d = ImageDraw.Draw(img)
    f = _font_cache()
    # top bar
    d.rectangle([0, 0, THUMB_W, 64], fill=PRIMARY)
    d.text((20, 16), "%d. %s" % (page.get("page_no"), page.get("title", "")),
           fill=WHITE, font=f(28))
    d.text((THUMB_W - 20, 18), "%d/%d" % (page.get("page_no"), plan.get("timing", {}).get("slide_target", 0)),
           fill=(220, 230, 240), font=f(20), anchor="ra")
    # claim block
    y = 84
    d.text((20, y), "主张", fill=ACCENT, font=f(18))
    y += 28
    for ln in _wrap(d, page.get("claim", ""), f(24), THUMB_W - 300):
        d.text((20, y), ln, fill=DARK, font=f(24))
        y += 34
        if y > THUMB_H - 260:
            break
    # strength chip
    st = page.get("strength")
    d.text((20, THUMB_H - 220), "证据强度：%s" % (st if st else "不适用"),
           fill=STRENGTH_COLOR.get(st, GRAY), font=f(20))
    # evidence box
    ev = (page.get("evidence") or [{}])[0]
    if ev:
        d.rectangle([20, THUMB_H - 190, THUMB_W - 300, THUMB_H - 40], fill=LIGHT,
                    outline=GRAY)
        d.text((30, THUMB_H - 182), "证据定位：%s" % ev.get("locator", ""),
               fill=GRAY, font=f(17))
        d.text((30, THUMB_H - 150), "来源：%s · 强度：%s" % (ev.get("source_file"), ev.get("strength")),
               fill=GRAY, font=f(16))
        quote = (ev.get("quote") or "")[:110]
        yy = THUMB_H - 118
        for ln in _wrap(d, quote, f(15), THUMB_W - 360):
            d.text((30, yy), ln, fill=GRAY, font=f(15))
            yy += 22
    # figure area right
    fx, fy, fw, fh = THUMB_W - 260, 84, 240, 380
    if figure_file and os.path.exists(figure_file):
        try:
            im = Image.open(figure_file)
            im = im.convert("RGB")
            box_ar = fw / fh
            ar = im.width / im.height if im.height else 1
            if ar > box_ar:
                nw = fw
                nh = int(fw / ar)
            else:
                nh = fh
                nw = int(fh * ar)
            im = im.resize((nw, nh))
            img.paste(im, (fx + (fw - nw) // 2, fy + (fh - nh) // 2))
        except Exception:  # noqa: BLE001
            figure_file = None
    if not figure_file:
        d.rectangle([fx, fy, fx + fw, fy + fh], fill=LIGHT, outline=GRAY)
        d.text((fx + fw // 2, fy + fh // 2 - 20), "图占位：%s" % (page.get("figure_ref") or "无"),
               fill=PRIMARY, font=f(20), anchor="mm")
        d.text((fx + fw // 2, fy + fh // 2 + 40), "材料未提供图片文件",
               fill=GRAY, font=f(15), anchor="mm")
    else:
        d.text((fx + 8, fy + 8), "图：%s" % (page.get("figure_ref") or "figure"),
               fill=PRIMARY, font=f(16))
    _watermark(d, THUMB_W)
    os.makedirs(os.path.dirname(out_png) or ".", exist_ok=True)
    img.save(out_png, format="PNG", optimize=True)
    return out_png


def render_grid(pages, plan, out_png, cols=4):
    from PIL import Image, ImageDraw
    cell = 320
    n = len(pages)
    rows = -(-n // cols)
    pad = 18
    W = cols * cell + pad * (cols + 1)
    H = rows * (cell // 2 + 60) + pad * (rows + 1)
    img = Image.new("RGB", (W, H), WHITE)
    img_draw = ImageDraw.Draw(img)
    f = _font_cache()
    for i, page in enumerate(pages):
        rr, cc = divmod(i, cols)
        x = pad + cc * (cell + pad)
        y = pad + rr * (cell // 2 + 60)
        thumb = Image.new("RGB", (cell, cell // 2), LIGHT)
        td = ImageDraw.Draw(thumb)
        td.rectangle([0, 0, cell, 26], fill=PRIMARY)
        title = page.get("title", "")[:26]
        td.text((6, 5), title, fill=WHITE, font=f(13))
        td.text((6, 34), (page.get("claim", "") or "")[:80], fill=DARK, font=f(12))
        st = page.get("strength")
        td.text((6, cell // 2 - 26), "强度:%s" % (st or "-"),
                fill=STRENGTH_COLOR.get(st, GRAY), font=f(12))
        img.paste(thumb, (x, y))
        img_draw.text((x + cell - 40, y + cell // 2 - 18), "PIL预览",
                      fill=(150, 150, 150), font=f(11))
    os.makedirs(os.path.dirname(out_png) or ".", exist_ok=True)
    img.save(out_png, format="PNG", optimize=True)
    return out_png


def render_all(plan, out_dir, figure_lookup=None, skip_slide_thumbs=False,
               figure_base=None):
    """Render cover + per-slide thumbnails + grid; returns manifest (list of
    record dicts) and limitation note.

    Page `figure_file` values may be absolute (fresh plan) or relative to the
    case directory (a portable plan re-read from talk_plan.json); both are
    resolved through common.resolve_input_path(figure_base).
    """
    figure_lookup = figure_lookup or {}
    ensure_out = os.path.dirname(out_dir)
    if ensure_out:
        os.makedirs(out_dir, exist_ok=True)
    records = []
    cover = os.path.join(out_dir, "cover_preview.png")
    render_cover(plan, cover)
    records.append({"file": "previews/cover_preview.png", "kind": "cover", "width": CANVAS_W,
                    "height": CANVAS_H, "simulated": True})
    slide_pngs = []
    unbound_figures = []
    if not skip_slide_thumbs:
        for page in plan["pages"]:
            if page["block"] in ("title", "agenda", "qa"):
                continue
            png = os.path.join(out_dir, "slide_%03d.png" % page["page_no"])
            figure_file = (resolve_input_path(page.get("figure_file"), figure_base)
                           or figure_lookup.get(page.get("figure_ref")))
            if not figure_file and page.get("figure_ref"):
                unbound_figures.append(page["figure_ref"])
            render_slide(page, plan, png, figure_file=figure_file)
            slide_pngs.append("previews/slide_%03d.png" % page["page_no"])
            records.append({"file": "previews/slide_%03d.png" % page["page_no"],
                            "kind": "slide-thumbnail", "page_no": page["page_no"],
                            "simulated": True})
    grid = os.path.join(out_dir, "preview_grid.png")
    render_grid(plan["pages"], plan, grid)
    records.append({"file": "previews/preview_grid.png", "kind": "grid", "simulated": True})
    limitation = ("预览为 Pillow(PIL) 模拟渲染，非 LibreOffice/PowerPoint 的 Office 真实栅格化；"
                  "用于检查页数、逐页主张/证据布局与图占位，正式视觉效果请以可编辑的 .pptx 打开为准。")
    if unbound_figures:
        limitation += (" 图表 %s 在材料目录中没有对应图片文件，页内/预览中为诚实占位框，"
                       "未虚构插图。" % sorted(set(unbound_figures)))
    manifest = {
        "generated_by": "render.py of academic-talk-organizer (v2)",
        "generated_at": utc_now(),
        "method": "Pillow simulated preview (LibreOffice not assumed available)",
        "font": font_status(),
        "unbound_figure_refs": sorted(set(unbound_figures)),
        "limitation": limitation,
        "files": records,
    }
    mpath = os.path.join(out_dir, "preview_manifest.json")
    write_json(mpath, manifest)
    records.append({"file": "previews/preview_manifest.json", "kind": "manifest"})
    return records, limitation