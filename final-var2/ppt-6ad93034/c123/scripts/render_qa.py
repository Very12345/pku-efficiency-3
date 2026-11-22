# -*- coding: utf-8 -*-
"""render_qa.py — render layer: 预览渲染 + 渲染 QA（对齐高分包 render_qa）。

职责（render 轴）：
* preview/slide_NN.png —— PIL 画布复刻页面模型（标题/要点/图表/占位/页脚）；
* preview/preview.pdf —— reportlab 逐页文本式版式预览；
* 两者都是**预览渲染**：文件名与 result.json previews.method 均如实标注
  "非 PowerPoint 导出"（D8：有 LibreOffice 时才可能是 Office 级导出）。
* QA：每页检查 中文乱码风险（CJK 字体可用性）、内容量溢出估计（字符宽度
  模型 vs 槽位）、预览文件存在性，产出 qa 报告供 result.json/CP3 使用。

不包含 PPTX 本身的构建（那是 deck_tool.py）。
"""
import os

from deck_common import LOG, resolve_font, ensure_dir, wrap_text

CANVAS_W, CANVAS_H = 1280, 720
MARGIN = 48

COLOR_BG = (255, 255, 255)
COLOR_TITLE_BAND = (31, 78, 121)
COLOR_TEXT = (38, 38, 38)
COLOR_MUTED = (127, 127, 127)
COLOR_LINE = (200, 205, 214)


def _font(size, family=None, bold=False):
    from PIL import ImageFont
    fam, path = resolve_font(family or "Microsoft YaHei")
    if not path:
        return ImageFont.load_default(), fam
    return ImageFont.truetype(path, size), fam


def _font_path():
    fam, path = resolve_font("Microsoft YaHei")
    return path


def render_png(page, chart_image=None, out_path=None):
    """Render one page preview PNG; returns (img, font_used, warnings)."""
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (CANVAS_W, CANVAS_H), COLOR_BG)
    d = ImageDraw.Draw(img)
    warnings = []

    f_title, fam = _font(44, "Microsoft YaHei", True)
    if fam is None:
        warnings.append("预览未找到 CJK 字体，文字可能为方块（不影响 pptx 本身）")
    f_body, _ = _font(26, "Microsoft YaHei")
    f_small, _ = _font(18, "Microsoft YaHei")
    f_ev, _ = _font(16, "Microsoft YaHei")

    # title band
    d.rectangle([0, 0, CANVAS_W, 118], fill=COLOR_TITLE_BAND)
    d.text((MARGIN, 34), page.get("title", "")[:48], font=f_title, fill=(255, 255, 255))

    const_claims = page.get("claims", [])
    y = 170
    for c in const_claims:
        text = c.get("text", "")
        t = "• " + text
        lines = wrap_text(t, _font_path(), 26, CANVAS_W - MARGIN * 2)
        for ln in lines[:4]:
            d.text((MARGIN, y), ln, font=f_body, fill=COLOR_TEXT)
            y += 36
        y += 10

    # chart / placeholder area on the right side
    if chart_image and os.path.isfile(chart_image) and page.get("figure", {}).get("kind") == "chart_image":
        try:
            from PIL import Image as _I
            with _I.open(chart_image) as im:
                im = im.convert("RGB")
                box_w, box_h = 520, 400
                scale = min(box_w / im.width, box_h / im.height)
                nw, nh = int(im.width * scale), int(im.height * scale)
                im = im.resize((nw, nh))
                img.paste(im, (CANVAS_W - MARGIN - nw, 180))
        except Exception as e:  # noqa: BLE001
            warnings.append("预览贴图失败: %s" % e)

    fig = page.get("figure", {})
    if fig.get("kind") == "placeholder":
        d.rectangle([CANVAS_W - MARGIN - 520, 180, CANVAS_W - MARGIN, 560],
                    outline=COLOR_MUTED, width=2)
        d.text((CANVAS_W - MARGIN - 500, 200), (fig.get("note") or "诚实占位，未重绘")[:30],
               font=f_small, fill=COLOR_MUTED)

    # footer
    d.line([MARGIN, CANVAS_H - 66, CANVAS_W - MARGIN, CANVAS_H - 66], fill=COLOR_LINE, width=1)
    ev = page.get("evidence_footer", "") or ""
    d.text((MARGIN, CANVAS_H - 50), ev[:80], font=f_ev, fill=COLOR_MUTED)
    d.text((CANVAS_W - MARGIN - 60, CANVAS_H - 50), str(page.get("index", "")),
           font=f_ev, fill=COLOR_MUTED)
    d.text((MARGIN, CANVAS_H - 96), "预览渲染（PIL），非 PowerPoint 导出", font=f_ev, fill=(180, 120, 40))

    if out_path:
        img.save(out_path, "PNG")
    return img, fam, warnings


def render_pdf(pages, out_path):
    """Render all pages into one PDF preview (reportlab text render)."""
    try:
        from reportlab.lib.pagesizes import landscape
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib import colors
    except Exception as e:  # noqa: BLE001
        LOG.warning("reportlab unavailable: %s", e)
        return None, ["reportlab 不可用，PDF 预览未生成"]

    pagesize = landscape((10.0 * inch, 5.625 * inch))  # 16:9 text preview
    doc = SimpleDocTemplate(out_path, pagesize=pagesize,
                            leftMargin=0.6 * inch, rightMargin=0.6 * inch,
                            topMargin=0.5 * inch, bottomMargin=0.5 * inch)
    st_title = ParagraphStyle("t", fontName="Helvetica-Bold", fontSize=15,
                              textColor=colors.HexColor("#1F4E79"), spaceAfter=8)
    st_body = ParagraphStyle("b", fontName="Helvetica", fontSize=10,
                             leading=13, spaceAfter=3)
    st_ev = ParagraphStyle("e", fontName="Helvetica", fontSize=7,
                           textColor=colors.HexColor("#7F7F7F"), spaceAfter=16)
    st_note = ParagraphStyle("n", fontName="Helvetica-Oblique", fontSize=8,
                             textColor=colors.HexColor("#444444"), spaceBefore=2)

    story = []
    for idx, page in enumerate(pages):
        story.append(Paragraph("【%d/%d】%s（%s）" % (idx + 1, len(pages),
                                                     page.get("title", ""),
                                                     page.get("role_label", "")),
                               st_title))
        for c in page.get("claims", []):
            mark = "" if c.get("verified", True) else " [未核验]"
            story.append(Paragraph("• " + c.get("text", "") + mark, st_body))
        fig = page.get("figure", {})
        if fig.get("kind") in ("chart_image", "table"):
            story.append(Paragraph("[图表] %s（%s）" % (fig.get("ref", ""), fig.get("note", "")),
                                   st_note))
        if page.get("notes"):
            story.append(Paragraph("[讲解] " + "; ".join(page.get("notes", [])), st_note))
        story.append(Paragraph("证据: %s   |   预览渲染（reportlab），非 PowerPoint 导出"
                               % page.get("evidence_footer", ""), st_ev))
        if idx != len(pages) - 1:
            story.append(PageBreak())
    doc.build(story)
    return out_path, []


# ---------------------------------------------------------------------------
# QA: per-page render quality checks (font / overflow estimate / file exists)
# ---------------------------------------------------------------------------

def qa_report(pages_meta, preview_dir):
    """Render QA: checks and warnings across the produced previews.

    Returns {"checks": [{page, name, ok, detail}], "warnings": [...]}.
    Checks: cjk_font_available, preview_png_exists, overflow_estimate(ok).
    """
    checks = []
    warnings = []
    fam, _ = resolve_font("Microsoft YaHei")
    for p in pages_meta or []:
        idx = p.get("index")
        png = os.path.join(preview_dir, "slide_%02d.png" % (idx or 0))
        # overflow estimate: CJK-weighted bullet width vs min body size budget
        total_w = sum(_cjk_w(c.get("text", "")) * 26 / 2 for c in p.get("claims", []) if c.get("text"))
        slot_px = 6900  # approx body slot height budget in weighted px (4.9in @15-17pt)
        checks.append({"page": idx, "name": "overflow_estimate",
                       "ok": total_w <= slot_px,
                       "detail": "weighted=%d budget=%d" % (total_w, slot_px)})
        checks.append({"page": idx, "name": "cjk_font_available",
                       "ok": fam is not None,
                       "detail": fam or "no CJK font found"})
        checks.append({"page": idx, "name": "preview_png_exists",
                       "ok": os.path.isfile(png),
                       "detail": os.path.basename(png) if os.path.isfile(png) else "missing"})
        if fam is None:
            warnings.append("预览未找到 CJK 字体（可能显示方块，不影响 pptx 本身）")
    return {"checks": checks, "warnings": warnings}


def _cjk_w(s):
    return sum(2 if ord(ch) > 0x2E7F else 1 for ch in (s or ""))


def render_all(pages_with_meta, work_dir, chart_map=None):
    """Render preview PNGs + PDF for a plan; returns (pngs, pdf, warnings)."""
    ensure_dir(os.path.join(work_dir, "preview"))
    pngs, warns = [], []
    for page in pages_with_meta:
        chart = None
        if chart_map and page.get("figure", {}).get("table_id") in chart_map:
            chart = chart_map[page["figure"]["table_id"]]
        out = os.path.join(work_dir, "preview", "slide_%02d.png" % page["index"])
        _, fam, w = render_png(page, chart_image=chart, out_path=out)
        pngs.append(out)
        warns.extend(w)
    pdf, w = render_pdf(pages_with_meta, os.path.join(work_dir, "preview", "preview.pdf"))
    warns.extend(w or [])
    return pngs, pdf, warns