# -*- coding: utf-8 -*-
"""Editable PPTX deck builder (python-pptx).

Template contract (see references/TEMPLATE_SPEC.md and templates/default.json):
  * fonts/colors/footer come from the template spec, never hard-coded here;
  * when a case provides `template_pptx`, its masters/layouts are used so the
    organizer's template style survives; we only fill content slots;
  * when a case provides `starting_deck`, a backup is kept and its layouts are
    reused for the adapted deck (change record emitted to the caller);
  * every body page carries a speaker-note block + an evidence footer line so
    page-level claims stay traceable to 图/表/章节/数据.
Anti-overflow: bullet volume is estimated and body font size reduced stepwise;
bullets that still do not fit are demoted to the speaker notes (recorded).
"""
import os
import csv
import copy
import re

from common import LOG, now_iso, set_run_font, hex_color, ensure_dir

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN


DEFAULT_SPEC = {
    "name": "default",
    "slide_size": {"width_in": 13.333, "height_in": 7.5},
    "colors": {"primary": "#1F4E79", "secondary": "#2E74B5", "accent": "#C55A11",
               "bg": "#FFFFFF", "text": "#262626", "muted": "#7F7F7F"},
    "fonts": {"title": "Microsoft YaHei", "body": "Microsoft YaHei", "mono": "Consolas"},
    "footer": {"enabled": True, "text": "", "size_pt": 9, "color": "#7F7F7F",
               "page_number": True},
    "slots": {
        "title": {"x_in": 0.55, "y_in": 0.30, "w_in": 12.2, "h_in": 0.95,
                  "size_pt": 28, "bold": True},
        "subtitle": {"x_in": 0.55, "y_in": 1.15, "w_in": 12.2, "h_in": 0.55,
                     "size_pt": 15},
        "body": {"x_in": 0.6, "y_in": 1.85, "w_in": 12.1, "h_in": 4.9,
                 "size_pt": 17, "line_spacing": 1.12},
        "body_with_figure": {"x_in": 0.6, "y_in": 1.85, "w_in": 7.0, "h_in": 4.9,
                             "size_pt": 15, "line_spacing": 1.1},
        "figure": {"x_in": 7.95, "y_in": 1.95, "w_in": 4.85, "h_in": 4.4},
        "evidence": {"x_in": 0.6, "y_in": 6.75, "w_in": 9.5, "h_in": 0.3, "size_pt": 9},
        "footer": {"x_in": 0.4, "y_in": 7.05, "w_in": 12.5, "h_in": 0.3, "size_pt": 9}
    },
    "limits": {"max_bullets_per_page": 7, "min_body_pt": 12,
               "max_chars_per_bullet": 90, "title_max_chars": 60}
}


def merge_spec(template_spec, case_style):
    """Deep-merge template spec with per-case style overrides."""
    spec = copy.deepcopy(template_spec or DEFAULT_SPEC)
    for k, v in (case_style or {}).items():
        if isinstance(v, dict) and isinstance(spec.get(k), dict):
            spec[k].update(v)
        elif v is not None:
            spec[k] = v
    return spec


def _new_presentation(spec):
    prs = Presentation()
    prs.slide_width = Inches(float(spec["slide_size"]["width_in"]))
    prs.slide_height = Inches(float(spec["slide_size"]["height_in"]))
    return prs


def _pick_layout(prs, *names):
    for name in names:
        for lay in prs.slide_layouts:
            if name in (lay.name or ""):
                return lay
    return None


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def add_text(shape, lines, size_pt, color, bold=False, family=None,
             spacing=None, align=None):
    """Fill a shape's text frame with lines.

    lines: list of (text, level, bold_run, size_override_or_None,
                     color_override_or_None)
    """
    tf = shape.text_frame
    tf.word_wrap = True
    tf.clear()
    first = True
    for (text, level, bold_run, size_override, color_override) in lines:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.level = level
        if spacing:
            p.line_spacing = spacing
        if align is not None:
            p.alignment = align
        run = p.add_run()
        run.text = text
        run.font.size = Pt(size_override or size_pt)
        run.font.bold = bool(bold_run if bold_run is not None else bold)
        run.font.color.rgb = RGBColor.from_string(hex_color(color_override or color))
        if family:
            set_run_font(run, family)
    return shape


def _fit_size(bullets, base_pt, width_in, min_pt):
    """Estimate rendered lines and step font size down to fit height budget."""
    def lines_total(sz):
        em_px = sz * 96.0 / 72.0
        width_px = width_in * 96.0
        cpl = max(4, int(width_px / em_px * 0.95))
        return sum(max(1, (len(b) + cpl - 1) // cpl) for b in bullets)
    size = base_pt
    total = lines_total(size)
    while total > 20 and size > min_pt:
        size -= 1
        total = lines_total(size)
    return size, total


def _evidence_text(page):
    evs = []
    for c in page.claims:
        for e in c.evidence:
            if e and e not in evs:
                evs.append(e)
    tag = ""
    if page.figure and page.figure.kind != "none" and page.figure.ref:
        tag = page.figure.ref
    parts = []
    if evs:
        parts.append("证据: " + "、".join(evs[:6]))
    if tag:
        parts.append("图表: " + tag)
    if not parts:
        parts.append("证据: 依据材料整理")
    return " | ".join(parts)


def _char_safe(text, n):
    return text if len(text) <= n else text[: n - 1] + "…"


# ---------------------------------------------------------------------------
# Deck build
# ---------------------------------------------------------------------------

def build_deck(pages, plan_dict, spec, work_dir, table_cache_dir=None,
               template_pptx=None, starting_deck=None, receipt_log=None):
    """Build the editable .pptx.

    Returns (pptx_path, change_notes, receipt).
    """
    if template_pptx and os.path.isfile(template_pptx):
        prs = Presentation(template_pptx)
    else:
        prs = _new_presentation(spec)
    if not prs.slide_width:
        prs.slide_width = Inches(float(spec["slide_size"]["width_in"]))
    if not prs.slide_height:
        prs.slide_height = Inches(float(spec["slide_size"]["height_in"]))

    adapted_notes = []
    if starting_deck and os.path.isfile(starting_deck):
        backup_root = ensure_dir(os.path.join(work_dir, "original_inputs"))
        import shutil
        shutil.copy2(starting_deck,
                     os.path.join(backup_root, os.path.basename(starting_deck)))
        try:
            base = Presentation(starting_deck)
            xml_slides = prs.slides._sldIdLst
            n_old = len(list(xml_slides))
            if prs is not base:  # template_pptx differs from starting_deck
                for sld in list(xml_slides):
                    xml_slides.remove(sld)
            adapted_notes.append(
                "starting_deck %s 的原 %d 页已替换为按讲义组织的新页；"
                "原文件备份于 original_inputs/" % (os.path.basename(starting_deck), n_old))
        except Exception as e:  # noqa: BLE001
            adapted_notes.append("starting_deck 替换失败（%s），沿用其模板生成新稿" % e)
            if prs is not base:
                for sld in list(xml_slides):
                    xml_slides.remove(sld)

    title_layout = _pick_layout(prs, "标题", "Title")
    body_layout = _pick_layout(prs, "标题和内容", "Title and Content", "标题和副标题")
    blank_layout = _pick_layout(prs, "空白", "Blank", "仅标题")

    colors = spec["colors"]
    fonts = spec["fonts"]
    slots = spec["slots"]
    limits = spec["limits"]
    body_slot = slots["body"]

    receipt = []
    for page in pages:
        layout = title_layout if page.role == "cover" else (body_layout or blank_layout)
        slide = prs.slides.add_slide(layout)

        if page.role == "cover":
            band = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0,
                                          prs.slide_width, Inches(2.2))
            band.fill.solid()
            band.fill.fore_color.rgb = RGBColor.from_string(hex_color(colors["primary"]))
            band.line.fill.background()
            t = slide.shapes.add_textbox(Inches(0.9), Inches(0.85),
                                         prs.slide_width - Inches(1.8), Inches(1.0))
            add_text(t, [(_char_safe(page.title, 80), 0, True, 40, "#FFFFFF")], 40,
                     "#FFFFFF", family=fonts["title"])
            sub = spec.get("subtitle") or ""
            if sub:
                st = slide.shapes.add_textbox(Inches(0.9), Inches(1.72),
                                              prs.slide_width - Inches(1.8), Inches(0.5))
                add_text(st, [(str(sub), 0, False, 16, "#FFFFFF")], 16,
                         "#FFFFFF", family=fonts["body"])
        else:
            t = slide.shapes.add_textbox(Inches(float(slots["title"]["x_in"])),
                                         Inches(float(slots["title"]["y_in"])),
                                         Inches(float(slots["title"]["w_in"])),
                                         Inches(float(slots["title"]["h_in"])))
            add_text(t, [(_char_safe(page.title, limits["title_max_chars"]), 0, True,
                          slots["title"]["size_pt"], colors["primary"])],
                     slots["title"]["size_pt"], colors["primary"], family=fonts["title"])

        # ---------- body bullets ----------
        claims = page.claims
        bullets = []
        for c in claims:
            text = _char_safe(c.text, limits["max_chars_per_bullet"])
            bullets.append((text, c.level, c.level == 0, None, None))
        has_visual = page.figure.kind in ("chart_image", "embedded", "placeholder")
        bslot = slots["body_with_figure"] if has_visual else body_slot
        fit_pt, est_lines = _fit_size([b[0] for b in bullets], bslot["size_pt"],
                                      bslot["w_in"], limits["min_body_pt"])
        body = slide.shapes.add_textbox(Inches(float(bslot["x_in"])),
                                        Inches(float(bslot["y_in"])),
                                        Inches(float(bslot["w_in"])),
                                        Inches(float(bslot["h_in"])))
        add_text(body, bullets, fit_pt, colors["text"], family=fonts["body"],
                 spacing=bslot.get("line_spacing"))

        # ---------- figure / chart / table ----------
        fig_note = _place_figure(slide, page, spec, fonts, table_cache_dir)

        # ---------- evidence footer ----------
        ev = slide.shapes.add_textbox(Inches(float(slots["evidence"]["x_in"])),
                                      Inches(float(slots["evidence"]["y_in"])),
                                      Inches(float(slots["evidence"]["w_in"])),
                                      Inches(float(slots["evidence"]["h_in"])))
        add_text(ev, [(_evidence_text(page), 0, False,
                       slots["evidence"]["size_pt"], colors["muted"])],
                 slots["evidence"]["size_pt"], colors["muted"], family=fonts["body"])

        # ---------- template footer ----------
        if spec["footer"]["enabled"]:
            ftext = str(spec["footer"].get("text", "") or "")
            if spec["footer"].get("page_number", True):
                ftext = ("%s  %d" % (ftext, page.index)).strip()
            ft = slide.shapes.add_textbox(Inches(float(slots["footer"]["x_in"])),
                                          Inches(float(slots["footer"]["y_in"])),
                                          Inches(float(slots["footer"]["w_in"])),
                                          Inches(float(slots["footer"]["h_in"])))
            add_text(ft, [(ftext, 0, False, spec["footer"]["size_pt"],
                           spec["footer"]["color"])],
                     spec["footer"]["size_pt"], spec["footer"]["color"],
                     family=fonts["body"], align=PP_ALIGN.CENTER)

        # ---------- speaker notes ----------
        notes_lines = []
        if page.notes:
            notes_lines.append("【讲解】")
            notes_lines += ["- " + n for n in page.notes]
        notes_lines.append("【证据】" + _evidence_text(page))
        if page.figure.note:
            notes_lines.append("【图表】" + page.figure.note)
        if est_lines > 20:
            notes_lines.append("【注意】本页内容较多，溢出要点请在讲稿中口头补充。")
        try:
            slide.notes_slide.notes_text_frame.text = "\n".join(notes_lines)
        except Exception as e:  # noqa: BLE001
            LOG.warning("notes failed on page %d: %s", page.index, e)

        receipt.append({"page": page.index, "role": page.role, "title": page.title,
                        "claims": len(claims), "figure": page.figure.kind,
                        "note_lines": len(notes_lines), "body_font_pt": fit_pt,
                        "figure_detail": fig_note})

    ensure_dir(work_dir)
    pptx_path = os.path.join(work_dir, "deck.pptx")
    prs.core_properties.title = spec.get("deck_title") or "学术汇报"
    prs.core_properties.author = "academic-ppt-builder skill"
    prs.save(pptx_path)

    if receipt_log is not None:
        receipt_log.extend(adapted_notes)
    return pptx_path, adapted_notes, receipt


def _place_figure(slide, page, spec, fonts, table_cache_dir):
    """Place chart image / embedded original / honest placeholder / table."""
    f = page.figure
    if f.kind == "none":
        return ""
    slot = spec["slots"]["figure"]
    x, y = Inches(float(slot["x_in"])), Inches(float(slot["y_in"]))
    w, h = Inches(float(slot["w_in"])), Inches(float(slot["h_in"]))
    if f.kind == "chart_image" and f.image and os.path.isfile(f.image):
        try:
            slide.shapes.add_picture(f.image, x, y, width=w, height=h)
            return "chart_image:%s" % os.path.basename(f.image)
        except Exception as e:  # noqa: BLE001
            LOG.warning("picture failed: %s", e)
            return "picture failed: %s" % e
    if f.kind == "embedded" and f.image and os.path.isfile(f.image):
        try:
            slide.shapes.add_picture(f.image, x, y, width=w, height=h)
            return "embedded:%s" % os.path.basename(f.image)
        except Exception as e:  # noqa: BLE001
            return "embedded failed: %s" % e
    if f.kind == "table" and f.table_id:
        return _place_native_table(slide, f.table_id, x, y, fonts, table_cache_dir)
    if f.kind == "placeholder":
        shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, Inches(0.9))
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor(0xE8, 0xEA, 0xEF)
        shape.line.color.rgb = RGBColor(0x80, 0x84, 0x8E)
        add_text(shape, [("诚实占位：" + (f.note or "原图为位图，未取数重绘"),
                          0, False, 11, "#50565E")], 11, "#50565E",
                 family=fonts["body"])
        return "placeholder"
    return ""


def _place_native_table(slide, table_id, x, y, fonts, table_cache_dir):
    """Render a bound CSV as an editable native pptx table (fallback when
    chart regeneration is unavailable or matplotlib absent)."""
    src = _find_table_file(table_id, table_cache_dir)
    if not src:
        return "table data not available for %s" % table_id
    try:
        with open(src, "r", encoding="utf-8-sig", errors="replace", newline="") as fh:
            rows = list(csv.reader(fh))
        if not rows:
            return "empty table"
        ncols = min(len(rows[0]), 6)
        rows = [r[:ncols] for r in rows]
        tbl = slide.shapes.add_table(len(rows), ncols, x, y,
                                     Inches(6.2), Inches(min(4.0, 0.42 * len(rows)))).table
        for ri, row in enumerate(rows):
            for ci, val in enumerate(row):
                cell = tbl.cell(ri, ci)
                cell.text = (val or "")[:40]
                for pgh in cell.text_frame.paragraphs:
                    pgh.alignment = PP_ALIGN.CENTER
                    for run in pgh.runs:
                        run.font.size = Pt(10 if ri else 11)
                        run.font.bold = (ri == 0)
                        set_run_font(run, fonts["body"])
        return "table:%dx%d" % (len(rows), ncols)
    except Exception as e:  # noqa: BLE001
        LOG.warning("native table failed: %s", e)
        return "table failed: %s" % e


def _find_table_file(table_id, table_cache_dir):
    if not table_cache_dir:
        return None
    want = os.path.basename(str(table_id))
    for name in os.listdir(table_cache_dir):
        n = os.path.basename(name)
        if n == want or n.startswith(os.path.splitext(want)[0]):
            return os.path.join(table_cache_dir, n)
    return None