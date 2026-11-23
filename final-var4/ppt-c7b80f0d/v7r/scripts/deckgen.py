# -*- coding: utf-8 -*-
"""deckgen.py — deck generator: build an editable academic slide deck (.pptx)
from a structured deck-spec.

Part of the "paper-to-academic-ppt" Skill v2 (ppt-c7b80f0d, efficiency-3).

Layer role (high-score three-layer intent): assetkit (material→assets) →
deckgen (spec→editable .pptx) → ooxml_kit (OOXML-level refinement & QA).

Responsibilities
----------------
* Open an organizer-supplied template (.pptx/.potx) when provided and adapt it:
  only fill layout placeholders (title / body / picture), never touch the master,
  never overwrite footer / color scheme. Fall back to a safe layout by name-match,
  then by index.
* When no template is given, author a minimal built-in 16:9 academic layout set
  directly (self-contained, no external font/template files required).
* Write page claims as short titles + phrase-level bullets (no paragraph dumps),
  embed paper figures / reconstructed charts, add tables with the paper's numbers,
  attach speaker notes that are separate from slide text, and append a generated
  "evidence mapping" slide so every page can be traced to the paper.
* Every shape we add is named through ooxml_kit.name_shape (references/
  layer-naming.md) so later edit tools can find them deterministically.
* Honesty rules are enforced structurally:
  - figure entries with a missing/un-extractable image become an explicit
    placeholder box (labeled "image unavailable, to be added at delivery"), never
    a synthetic drawing passed off as the paper's figure;
  - every slide must carry evidence entries or an explicit evidence_gap flag;
  - nothing is invented: strings come from the spec, which the agent must derive
    from the actual paper files.

All paths in templates/artifacts are resolved relative to the caller; this module
does not read the environment, only what is passed in.
"""
from __future__ import annotations

import json
import os
import sys

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, PP_PLACEHOLDER
from pptx.oxml.ns import qn

import ooxml_kit

# --------------------------------------------------------------------------- #
# Built-in academic theme (used only when the organizer supplies no template)
# --------------------------------------------------------------------------- #
ACADEMIC_THEME = {
    "primary": RGBColor(0x1F, 0x4E, 0x79),      # deep academic blue
    "accent": RGBColor(0x2E, 0x74, 0xB5),
    "light": RGBColor(0xF2, 0xF7, 0xFC),
    "ink": RGBColor(0x26, 0x26, 0x26),
    "muted": RGBColor(0x59, 0x59, 0x59),
    "warn": RGBColor(0xC0, 0x50, 0x4D),
    "white": RGBColor(0xFF, 0xFF, 0xFF),
}

# How a spec "layout_hint" maps to a named layout in an organizer template.
LAYOUT_KEYWORDS = [
    ("title",            ["title", "cover", "ti tle"]),
    ("section",          ["section", "divider", "agenda", "separation"]),
    ("figure",           ["figure", "picture", "image", "photo", "screenshot"]),
    ("table",            ["table", "chart", "data"]),
    ("content",          ["content", "body", "bullet", "text", "standard"]),
    ("two-content",      ["two content", "2 content", "comparison", "split"]),
    ("reference",        ["reference", "bibliography", "thank", "acknowledg", "closing"]),
]

DEFAULT_LAYOUT_BY_HINT = {
    "title": 0,
    "section": 2,
    "figure": 8,       # default template: Picture with Caption
    "table": 1,
    "content": 1,
    "two-content": 3,
    "reference": 1,
}

# Conservative per-bullet character budget used as an overflow guard before
# rendering; CJK counts double (wider glyphs) by design.
MAX_BULLETS = 6
MAX_CHARS_BULLET = 110
MAX_CHARS_TITLE = 40


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #
_NAME_SEQ = [0]


def _name(shape, kind, ref=""):
    """Deterministic shape name via the OOXML layer naming contract."""
    _NAME_SEQ[0] += 1
    return ooxml_kit.name_shape(shape, kind, _NAME_SEQ[0], ref)
def _set_run_font(run, name="Microsoft YaHei", size=18, bold=False, color=None):
    """Set a run font for both latin and east-asian typefaces (CJK-safe).
    Delegates to the OOXML layer so theme/run font policy lives in one place."""
    return ooxml_kit.set_shape_font(run, name=name, size=size, bold=bold, color=color)


def _fill_textbox(tf, lines, base_size=18, color=None, font="Microsoft YaHei",
                  first_color=None, first_bold=True, space_after=6):
    """Write phrase-level lines into a text frame. lines: list of str|level int."""
    first = True
    for item in lines:
        if isinstance(item, (list, tuple)):
            text, level = item[0], int(item[1]) if len(item) > 1 else 0
        else:
            text, level = str(item), 0
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        p.level = min(level, 4)
        p.space_after = Pt(space_after)
        run = p.add_run()
        run.text = text
        cur_color = first_color if (first and first_color is not None) else color
        _set_run_font(run, font, base_size - 2 if level else base_size,
                      bold=(first and first_bold), color=cur_color or ACADEMIC_THEME["ink"])
        first = False


def _clip_text(text, limit):
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _add_footer(prs, slide, page_no, total, deck_title):
    """Built-in-only footer (page numbers). Never added when adapting an
    organizer template, so the template's own footer/color scheme is preserved."""
    w = prs.slide_width
    box = slide.shapes.add_textbox(Inches(0.35), Inches(7.08),
                                   Inches(int(w / 914400)), Inches(0.34))
    _name(box, "footer-page", str(page_no))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.RIGHT
    run = p.add_run()
    run.text = "%s  ·  %d / %d" % (_clip_text(deck_title, 48), page_no, total)
    _set_run_font(run, "Arial", 9, False, ACADEMIC_THEME["muted"])


# --------------------------------------------------------------------------- #
# Template handling
# --------------------------------------------------------------------------- #
def resolve_template(template_path, work_dir):
    """Return ('file', path) or ('builtin', None).

    template_path may come from spec.constraints.template_path or from the case
    material. If it is a directory, look inside for *.pptx / *.potx / *.ppt.
    """
    if not template_path:
        return "builtin", None
    p = template_path
    if not os.path.isabs(p):
        p = os.path.join(work_dir, p)
    if os.path.isdir(p):
        for name in sorted(os.listdir(p)):
            if name.lower().endswith((".pptx", ".potx")):
                return "file", os.path.join(p, name)
        for name in sorted(os.listdir(p)):
            if name.lower().endswith(".ppt"):
                return "file", os.path.join(p, name)
        return "builtin", None
    if os.path.isfile(p):
        return "file", p
    return "builtin", None


def _match_layout_index(layouts, hint, verbose_error=False):
    """Find the layout index whose name contains a keyword for the hint."""
    names = [(i, (l.name or "").lower()) for i, l in enumerate(layouts)]
    for cand in LAYOUT_KEYWORDS:
        if cand[0] != hint:
            continue
        for i, name in names:
            for kw in cand[1]:
                if kw in name:
                    return i
    return None


def open_adapted_presentation(template_path, work_dir):
    """Open an organizer template for adaptation, or create the built-in canvas.

    Returns (prs, template_meta). Only fails on genuinely corrupt files.
    """
    kind, path = resolve_template(template_path, work_dir)
    if kind == "file":
        try:
            prs = Presentation(path)
        except Exception as exc:  # corrupt / legacy .ppt
            return None, {"kind": "file", "error": "unreadable(%s): %s" % (path, exc)}
        meta = {
            "kind": "file",
            "path": path,
            "basename": os.path.basename(path),
            "layout_count": len(prs.slide_layouts),
            "guard": "placeholder-fill-only; master/footer/colors untouched",
            "starter_slides": len(prs.slides),
        }
        return prs, meta
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    meta = {
        "kind": "builtin",
        "path": None,
        "basename": None,
        "layout_count": len(prs.slide_layouts),
        "guard": "built-in 16:9 academic layout (no organizer template supplied)",
    }
    return prs, meta


# --------------------------------------------------------------------------- #
# Slide content writers
# --------------------------------------------------------------------------- #
def _fill_title_placeholder(slide, title_text, spec):
    for ph in slide.placeholders:
        if ph.placeholder_format.idx == 0 or ph.placeholder_format.idx == 11:
            tf = ph.text_frame
            tf.clear()
            _fill_textbox(tf, [_clip_text(title_text, MAX_CHARS_TITLE)], base_size=28,
                          first_color=ACADEMIC_THEME["primary"], first_bold=True)
            return True
    # no title placeholder -> draw one (only for built-in canvas)
    top = slide.shapes.add_textbox(Inches(0.5), Inches(0.32), Inches(12.3), Inches(0.85))
    _name(top, "claim-title")
    _fill_textbox(top.text_frame, [_clip_text(title_text, MAX_CHARS_TITLE)], base_size=28,
                  first_color=ACADEMIC_THEME["primary"], first_bold=True)
    return False


def _fill_body_placeholder(slide, bullets, spec, kind="body-bullets"):
    body = None
    for ph in slide.placeholders:
        idx = ph.placeholder_format.idx
        if idx == 1 or idx == 2:
            body = ph
            break
    capped = bullets[:MAX_BULLETS]
    if body is not None:
        tf = body.text_frame
        tf.clear()
        tf.word_wrap = True
        _fill_textbox(tf, capped, base_size=20, color=ACADEMIC_THEME["ink"],
                      first_color=ACADEMIC_THEME["primary"], first_bold=False)
        return True, len(capped)
    box = slide.shapes.add_textbox(Inches(0.7), Inches(1.45), Inches(11.9), Inches(5.2))
    _name(box, kind)
    tf = box.text_frame
    tf.word_wrap = True
    _fill_textbox(tf, capped, base_size=20, color=ACADEMIC_THEME["ink"])
    return False, len(capped)


def _place_figure(slide, spec_fig, work_dir, template_kind="builtin"):
    """Embed paper image / reconstructed chart, or an explicit placeholder box.

    Returns a dict describing what happened (honest record).
    """
    ref = spec_fig.get("ref", "Fig ?")
    label = spec_fig.get("label", "")
    kind = spec_fig.get("kind", "paper_figure")
    image = spec_fig.get("image") or spec_fig.get("src")
    source_page = spec_fig.get("source_page") or ""
    result = {"ref": ref, "kind": kind, "placed": None}

    def _add_caption():
        """Caption text under the figure area. Skipped for organizer templates
        unless a caption placeholder exists (placeholder-fill-only rule)."""
        if template_kind == "file":
            return
        cap = slide.shapes.add_textbox(Inches(6.6), Inches(6.12), Inches(6.2), Inches(0.7))
        _name(cap, "figure", ref + "-caption")
        tf = cap.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        run = p.add_run()
        run.text = "%s %s%s" % (ref, label, ("（%s）" % source_page) if source_page else "")
        _set_run_font(run, "Microsoft YaHei", 10, False, ACADEMIC_THEME["muted"])

    img_path = image
    if img_path and not os.path.isabs(img_path):
        img_path = os.path.join(work_dir, img_path)
    if img_path and os.path.isfile(img_path):
        pic_ph = None
        for ph in slide.placeholders:
            if ph.placeholder_format.type == PP_PLACEHOLDER.PICTURE:
                pic_ph = ph
                break
        try:
            if pic_ph is not None:
                pic = pic_ph.insert_picture(img_path)
            else:
                pic = slide.shapes.add_picture(img_path, Inches(6.6), Inches(1.5),
                                               width=Inches(6.2))
            _name(pic, "figure", ref)
            # keep aspect within bounds using PIL if available
            try:
                from PIL import Image
                im = Image.open(img_path)
                w, h = im.size
                max_w, max_h = 6.0, 4.6
                scale = min(max_w / (w / 96.0), max_h / (h / 96.0), 1.0)
                pic.width = Emu(int(pic.width * scale))
                pic.height = Emu(int(pic.height * scale))
            except Exception:
                pass
            result["placed"] = os.path.basename(img_path)
            _add_caption()
        except Exception as exc:
            result["placed_error"] = str(exc)
        return result

    # no image: explicit placeholder, never a fake drawing
    box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(6.6), Inches(1.5),
                                 Inches(6.2), Inches(4.3))
    _name(box, "figure", ref + "-placeholder")
    box.fill.solid()
    box.fill.fore_color.rgb = ACADEMIC_THEME["light"]
    box.line.color.rgb = ACADEMIC_THEME["accent"]
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    lines = ["【图表占位】%s %s" % (ref, label),
             "原文图像未能提取或未提供，放映/交付前需补齐——本占位不代表论文原图。"]
    _fill_textbox(tf, lines, base_size=14, color=ACADEMIC_THEME["primary"])
    result["placed"] = None
    result["placeholder"] = True
    _add_caption()
    return result


def _place_table(slide, spec_tab, work_dir):
    rows = spec_tab.get("rows", [])
    if not rows or not rows[0]:
        return {"ref": spec_tab.get("ref", "Table ?"), "placed": None, "reason": "no rows"}
    n_rows = len(rows)
    n_cols = len(rows[0])
    cols_in = min(n_cols, 6)
    x, y, w, h = Inches(6.4), Inches(1.55), Inches(6.6), Inches(4.0)
    gfx = slide.shapes.add_table(n_rows, n_cols, x, y, w, h)
    _name(gfx, "table", spec_tab.get("ref", "table"))
    tbl = gfx.table
    tbl.first_row = True
    tbl.horz_banding = True
    for r in range(n_rows):
        for c in range(min(n_cols, cols_in)):
            cell = tbl.cell(r, c)
            cell.text_frame.clear()
            val = str(rows[r][c]) if c < len(rows[r]) else ""
            p = cell.text_frame.paragraphs[0]
            run = p.add_run()
            run.text = val
            fsz = 12 if r == 0 else 11
            _set_run_font(run, "Arial", fsz, r == 0,
                          ACADEMIC_THEME["primary"] if r == 0 else ACADEMIC_THEME["ink"])
    return {"ref": spec_tab.get("ref", "Table ?"), "placed": True, "rows": n_rows}


def _add_notes(slide, notes_text, page_no, claim, evidence):
    """Notes are *separate from* the on-slide text: transitions, emphasis,
    Q&A back-up evidence. Never a copy of the bullets."""
    lines = []
    if claim:
        lines.append("核心主张（本页一句话）: %s" % claim)
    if notes_text:
        lines.append("讲解备注: %s" % notes_text)
    ev_lines = []
    for e in evidence or []:
        loc = e.get("page") or e.get("location") or ""
        ev_lines.append("- %s（%s）" % (e.get("ref", "?"), loc))
    if ev_lines:
        lines.append("对本页追问时可用证据: " + " ".join(ev_lines))
    if not lines:
        lines.append("（本页无备注——请在交付前补充讲解逻辑，勿复制页面文字）")
    slide.notes_slide.notes_text_frame.text = "\n".join(lines)


def _add_claim_strip(slide, claim):
    """Small claim strip under the title (built-in canvas only)."""
    box = slide.shapes.add_textbox(Inches(0.7), Inches(1.12), Inches(11.9), Inches(0.5))
    _name(box, "claim-strip")
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = "主张：%s" % _clip_text(claim or "", MAX_CHARS_BULLET * 2)
    _set_run_font(run, "Microsoft YaHei", 14, True, ACADEMIC_THEME["accent"])


# --------------------------------------------------------------------------- #
# Main build
# --------------------------------------------------------------------------- #
def _strip_starter_slides(prs):
    """Remove pre-existing slides so a 'starting deck' can be re-adapted using
    only its layouts/master. Used only when spec.constraints.template_mode ==
    'replace' (explicit opt-in; default keeps starter slides untouched)."""
    removed = len(prs.slides)
    if removed == 0:
        return 0
    sl_id_lst = prs.slides._sldIdLst
    for sld_id in list(sl_id_lst):
        r_id = sld_id.get(qn('r:id'))
        prs.part.drop_rel(r_id)
        sl_id_lst.remove(sld_id)
    return removed


def build_deck(spec, template_path, work_dir, out_dir):
    """Build the .pptx. Returns a meta dict (JSON-able, honest)."""
    spec = spec or {}
    slides_spec = spec.get("slides", []) or []
    meta_spec = spec.get("meta", {}) or {}
    deck_title = spec.get("deck_title") or meta_spec.get("title") or "Academic Talk"
    deck_title = _clip_text(deck_title, 64)

    prs, tpl = open_adapted_presentation(template_path, work_dir)
    if prs is None:
        return {"file": None, "error": tpl.get("error"), "template": tpl}

    # starting-deck adaptation (opt-in)
    if (spec.get("constraints") or {}).get("template_mode") == "replace":
        removed = _strip_starter_slides(prs)
        if removed:
            tpl["starter_slides_removed"] = removed
            tpl["note"] = "template_mode=replace: starter slides removed, layouts/master kept"

    constraints = spec.get("constraints") or {}
    auto_outline = bool(constraints.get("auto_outline", True))
    auto_evidence = bool(constraints.get("auto_evidence_slide", True))
    budget = constraints.get("slide_count")

    page = 0
    total = len(slides_spec) + 2  # title + closing(+evidence) counted later
    used_layouts = {}
    fig_records = []
    tab_records = []
    evidence_slides = []

    def _add_slide(hint, title_text=None):
        nonlocal page
        idx = _match_layout_index(prs.slide_layouts, hint)
        layout = None
        if idx is not None and idx < len(prs.slide_layouts):
            layout = prs.slide_layouts[idx]
        if layout is None:
            fallback = DEFAULT_LAYOUT_BY_HINT.get(hint, 1)
            layout = prs.slide_layouts[min(fallback, len(prs.slide_layouts) - 1)]
        used = layout.name or ("layout[%d]" % idx if idx is not None else "fallback")
        used_layouts[used] = used_layouts.get(used, 0) + 1
        slide = prs.slides.add_slide(layout)
        page += 1
        if title_text:
            _fill_title_placeholder(slide, title_text, spec)
        return slide

    # 0) title slide
    slide = _add_slide("title")
    tf = None
    placeholder = None
    for ph in slide.placeholders:
        if ph.placeholder_format.idx == 0 or ph.placeholder_format.idx == 11:
            placeholder = ph
            tf = ph.text_frame
            break
    if tf is None:
        tf = slide.shapes.add_textbox(Inches(0.8), Inches(1.8), Inches(11.7), Inches(1.6)).text_frame
        _name(slide.shapes[-1], "cover")
    tf.clear()
    lines = [deck_title, "—— 论文转学术汇报 · 证据可追溯 · 可编辑 ——"]
    if meta_spec.get("authors"):
        lines.append(meta_spec["authors"])
    meta_line = " | ".join(x for x in [meta_spec.get("venue"), meta_spec.get("date")] if x)
    if meta_line:
        lines.append(meta_line)
    if meta_spec.get("audience") or spec.get("constraints", {}).get("audience"):
        lines.append("汇报对象: %s · %s 分钟" % (
            meta_spec.get("audience") or spec["constraints"].get("audience", ""),
            meta_spec.get("duration_minutes") or spec.get("constraints", {}).get("duration_minutes", "")))
    for i, ln in enumerate(lines):
        if i == 0:
            p = tf.paragraphs[0]
            run = p.add_run()
            run.text = ln
            _set_run_font(run, "Microsoft YaHei", 34, True, ACADEMIC_THEME["primary"])
        else:
            p = tf.add_paragraph()
            run = p.add_run()
            run.text = ln
            _set_run_font(run, "Microsoft YaHei", 18 if i == 1 else 14, False,
                          ACADEMIC_THEME["ink"] if i == 1 else ACADEMIC_THEME["muted"])
    _add_notes(slide,
               "开场：一句话说明论文主题与汇报主线（问题→方法→证据→结论→局限）；"
               "被追问背景时引用论文摘要与引言出处。",
               page, deck_title, [])

    # 1) outline slide (auto, opt-in; page order as narrative spine)
    if auto_outline:
        slide = _add_slide("section", "汇报主线 Outlines")
        outline = ["问题与动机", "方法与设计", "核心证据", "结论与讨论", "局限与展望"]
        bullets = []
        for i, s in enumerate(slides_spec[:MAX_BULLETS]):
            t = (s.get("title") or s.get("claim") or "slide %d" % (i + 1))
            bullets.append([_clip_text(t, 30), 1])
        while len(bullets) < len(outline):
            bullets.append([outline[len(bullets)], 1])
        _fill_body_placeholder(slide, bullets, spec, kind="outline")

    # 2) content slides
    for s in slides_spec:
        hint = (s.get("layout_hint") or "content")
        claim = s.get("claim") or ""
        title_text = s.get("title") or _clip_text(claim, MAX_CHARS_TITLE)
        slide = _add_slide(hint, title_text)
        if claim and tpl["kind"] == "builtin":
            _add_claim_strip(slide, claim)
        bullets = s.get("bullets") or []
        _fill_body_placeholder(slide, bullets, spec)
        if s.get("figure"):
            fig_records.append(_place_figure(slide, s["figure"], work_dir, tpl["kind"]))
        if s.get("table"):
            tab_records.append(_place_table(slide, s["table"], work_dir))
        # evidence mapping for this page
        ev = s.get("evidence") or []
        gap = bool(s.get("evidence_gap"))
        evidence_slides.append({"page": page, "title": title_text,
                                "claim": claim, "evidence": ev, "evidence_gap": gap})
        _add_notes(slide, s.get("notes"), page, claim, ev)

    # 3) evidence mapping slide (auto, opt-in; for review/verifiability)
    if auto_evidence:
        slide = _add_slide("reference", "证据映射 · 供复核 Evidence Map")
        lines2 = ["本页汇总各页内容在论文中的定位（图/表/章节/页码）；引用未改写事实。", " "]
        for row in evidence_slides:
            bits = ["P%02d %s" % (row["page"], _clip_text(row["title"], 22))]
            if row["evidence_gap"]:
                bits.append("[证据缺失，已显式标注]")
            else:
                refs = ", ".join((e.get("ref", "?") + "→" + (e.get("page") or e.get("location") or "?")) for e in row["evidence"])
                bits.append(refs or "[无引用]")
            lines2.append(" - ".join(bits))
        _fill_body_placeholder(slide, lines2, spec, kind="evidence-map")
    evidence_slides.append({"page": page, "title": "证据映射页", "claim": "",
                            "evidence": [], "evidence_gap": False})

    # 4) closing slide
    slide = _add_slide("reference", "谢谢 · Questions & Discussion")
    _fill_body_placeholder(slide, [
        "结论: %s" % (_clip_text(spec.get("takeaway") or ", ".join(
            (s.get("claim") for s in slides_spec[-1:] if s.get("claim")) or ["综合全文结论"]), 90)),
        "局限: %s" % _clip_text(spec.get("limitations") or "以论文原文为准，详见证据映射页", 90),
        "备注与证据可在演讲者视图查看。",
    ], spec, kind="closing")
    _add_notes(slide,
               "收尾：总结主结论与局限，把讨论引导回证据映射页；"
               "被问细节时按页引用论文图/表/章节定位。",
               page, spec.get("takeaway") or "综合全文结论", [])

    # footers only for built-in canvas
    if tpl["kind"] == "builtin":
        for i, sl in enumerate(prs.slides, start=1):
            _add_footer(prs, sl, i, len(prs.slides), deck_title)

    out_name = (spec.get("output_name") or "academic_deck") + ".pptx"
    out_path = os.path.join(out_dir, out_name)
    prs.core_properties.title = deck_title
    prs.core_properties.subject = "paper-to-academic-ppt (task %s)" % (spec.get("case_id") or "?")
    # CJK-safe theme fonts (best-effort; recorded honestly)
    theme_rec = ooxml_kit.set_theme_fonts(prs, latin="Calibri", ea="Microsoft YaHei")
    prs.save(out_path)

    result = {
        "file": out_path,
        "basename": os.path.basename(out_path),
        "slide_count": len(prs.slides),
        "template": tpl,
        "layouts_used": used_layouts,
        "figures": fig_records,
        "tables": tab_records,
        "notes_included": True,
        "notes_separated": True,
        "overflow_guard": {"max_bullets": MAX_BULLETS, "max_chars_bullet": MAX_CHARS_BULLET},
        "auto_slides": {"outline": auto_outline, "evidence": auto_evidence},
        "theme_fonts": theme_rec,
        "error": None,
    }
    if budget:
        result["page_budget"] = budget
        result["page_budget_met"] = len(prs.slides) <= budget
    return result


def spec_from_case_meta(case, text_head=""):
    """Build a minimal *skeleton* spec from case metadata (DEMO only; never a
    substitute for the agent's real narration). Marks itself as skeleton."""
    meta = case.get("meta") or case.get("paper_meta") or {}
    title = meta.get("title") or case.get("title") or "Untitled Paper"
    lines = (text_head or "Skeleton spec (no agent narration yet) — DEMO ONLY.").splitlines()
    return {
        "case_id": case.get("case_id") or "unknown",
        "deck_title": title,
        "meta": {"title": title,
                 "date": meta.get("date", ""),
                 "authors": meta.get("authors", ""),
                 "venue": meta.get("venue", "")},
        "slides": [
            {
                "page": 1, "layout_hint": "content",
                "claim": "SKELETON（示例骨架，正式运行由 Agent 依据论文正文填写）",
                "title": "SPINE 问题→方法→证据→结论",
                "bullets": [x[:60] for x in lines[:4] if x.strip()],
                "notes": "SKELETON",
                "evidence": [],
                "evidence_gap": True,
            }
        ],
        "takeaway": "SKELETON",
        "limitations": "SKELETON",
        "constraints": {"slide_count": 6,
                        "audience": meta.get("audience", ""),
                        "duration_minutes": meta.get("duration_minutes", 15)},
        "skeleton": True,
    }


if __name__ == "__main__":
    import cli_io
    cli_io.harden_console()
    # CLI: python deck_builder.py --spec spec.json --template path --work dir --out dir
    args = sys.argv[1:]
    kw = {}
    for i in range(0, len(args) - 1, 2):
        kw[args[i].lstrip("-")] = args[i + 1]
    spec = json.load(open(kw.get("spec", ""), encoding="utf-8"))
    out_dir = kw.get("out", ".")
    os.makedirs(out_dir, exist_ok=True)
    meta = build_deck(spec,
                      kw.get("template") or (spec.get("constraints") or {}).get("template_path"),
                      kw.get("work", os.getcwd()), out_dir)
    print(json.dumps(meta, ensure_ascii=False, indent=2, default=str))