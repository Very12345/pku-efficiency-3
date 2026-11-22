#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
deck_builder.py — build the editable .pptx with python-pptx.
(render role in the build/extract/render/verify split.)

Two operating modes:
1. No template provided -> create a new deck on the package's built-in
   master/theme (16:9, theme colors, a real master with a bottom accent bar,
   layouts reused for every slide).
2. Template / starting deck provided by the case -> open it with python-pptx,
   keep its master/layouts (the frozen template constraints), drop any sample
   slides it carries, and rebuild every planned page on those layouts so the
   delivered page count equals the frozen slide count.

Every slide carries: title, unique claim, evidence line (source locator),
strength tag, figure (real image when available, honest placeholder box
otherwise) and speaker notes (script one-liner + Q&A prep).

Editable-structure evidence: every element the Skill creates is named with a
deterministic scheme (`page-claim-01`, `page-figure-01`, …) so verify_deck.py
can machine-check "this slide still expresses its claim", and a human can
locate/edit each element in PowerPoint by name.

Dependency handling: python-pptx is imported defensively (`PPTX_AVAILABLE`).
Without it, build_deck() raises a clear RuntimeError and the orchestrator
degrades to `partial` — talk_plan / plan_gates / previews / result.json are
still produced and the limitation is recorded in result.json.uncertainty.
"""

import os

from common import utc_now, resolve_input_path

# python-pptx is the one hard dependency of this module.  It is imported
# defensively so a host without it still gets talk_plan / previews / result.json
# (honest partial) instead of a crashed run: build_deck() then raises a clear
# RuntimeError that the orchestrator records as a dependency degradation.
PPTX_AVAILABLE = True
PPTX_IMPORT_ERROR = ""


class _MissingDependency(object):
    """Attribute- and call-tolerant placeholder used when python-pptx is absent.

    It only has to survive module import time (e.g. `PP_ALIGN.LEFT` appearing as
    a default argument value); build_deck() raises before any of it is used.
    """

    def __init__(self, name="pptx"):
        self._name = name

    def __getattr__(self, item):
        return _MissingDependency("%s.%s" % (self._name, item))

    def __call__(self, *args, **kwargs):
        return _MissingDependency("%s()" % self._name)

    def __repr__(self):
        return "<missing python-pptx: %s>" % self._name


try:
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.oxml.ns import qn
except Exception as _exc:  # noqa: BLE001
    PPTX_AVAILABLE = False
    PPTX_IMPORT_ERROR = str(_exc)
    Presentation = Inches = Pt = RGBColor = PP_ALIGN = MSO_SHAPE = qn = _MissingDependency()


def dependency_status():
    """Which optional third-party libraries are importable right now.
    Never raises — used for honest degradation notes in result.json."""
    status = {}
    for mod, key in (("pptx", "python_pptx"), ("PIL", "pillow"), ("pypdf", "pypdf")):
        try:
            m = __import__(mod)
            status[key] = getattr(m, "__version__", "unknown")
        except Exception:  # noqa: BLE001
            status[key] = None
    status["pptx_import_error"] = PPTX_IMPORT_ERROR
    return status


if PPTX_AVAILABLE:
    PRIMARY = RGBColor(0x1F, 0x4E, 0x79)
    ACCENT = RGBColor(0xC0, 0x50, 0x4D)
    DARK = RGBColor(0x26, 0x26, 0x26)
    GRAY = RGBColor(0x5A, 0x5A, 0x5A)
    LIGHT = RGBColor(0xF2, 0xF5, 0xF9)
    WHITE = RGBColor(0xFF, 0xFF, 0xFF)
    STRENGTH_COLOR = {"strong": RGBColor(0x2E, 0x7D, 0x32),
                      "medium": RGBColor(0xC0, 0x7F, 0x00),
                      "weak": RGBColor(0x8A, 0x8A, 0x8A),
                      None: GRAY}
else:  # pragma: no cover — only reachable on a host without python-pptx
    PRIMARY = ACCENT = DARK = GRAY = LIGHT = WHITE = None
    STRENGTH_COLOR = {}

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff", ".webp"}

FONT_LATIN = "Arial"
FONT_CJK = "Microsoft YaHei"

# deterministic element naming (see references/deck-rules.md)
NAME_TITLE = "page-title-%02d"
NAME_CLAIM = "page-claim-%02d"
NAME_FIGURE = "page-figure-%02d"
NAME_FOOTER = "page-footer-%02d"
NAME_COVER_META = "cover-meta"
NAME_MASTER_BAR = "master-accent-bar"


def _set_font(run, size=None, bold=None, color=None, italic=None, latin=FONT_LATIN, cjk=FONT_CJK):
    f = run.font
    f.name = latin
    if size is not None:
        f.size = Pt(size)
    if bold is not None:
        f.bold = bold
    if italic is not None:
        f.italic = italic
    if color is not None:
        f.color.rgb = color
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn("a:ea"))
    if ea is None:
        ea = rPr.makeelement(qn("a:ea"), {})
        rPr.append(ea)
    ea.set("typeface", cjk)


def _add_para(tf, text, size=16, bold=False, color=DARK, level=0, first=False,
              space_after=6, align=PP_ALIGN.LEFT, italic=None):
    p = tf.paragraphs[0] if (first and not tf.paragraphs[0].runs) else tf.add_paragraph()
    p.alignment = align
    p.level = level
    p.space_after = Pt(space_after)
    run = p.add_run()
    run.text = text
    _set_font(run, size=size, bold=bold, color=color, italic=italic)
    return p


def _pick_layout(prs, kind):
    """Choose a layout with title (and body when possible)."""
    for layout in prs.slide_layouts:
        try:
            has_title = any(ph.placeholder_format.type == 13 for ph in layout.placeholders)  # 13 = TITLE
        except Exception:  # noqa: BLE001
            has_title = False
        if kind == "cover" and has_title:
            return layout, has_title
        if kind == "content" and has_title:
            return layout, has_title
    for layout in prs.slide_layouts:
        return layout, True
    return None, False


def _new_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    try:
        master = prs.slide_masters[0]
        # thin accent bar at the bottom of every slide (master-level decoration)
        bar = master.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(7.28),
                                      prs.slide_width, Inches(0.22))
        bar.name = NAME_MASTER_BAR
        bar.fill.solid()
        bar.fill.fore_color.rgb = ACCENT
        bar.line.fill.background()
        bar.shadow.inherit = False
    except Exception:  # noqa: BLE001 — decoration is best-effort, never fatal
        pass
    return prs


def _verbatim_source(plan):
    return plan.get("case_id") or ""


def _make_cover(prs, plan, case):
    layout, _ = _pick_layout(prs, "cover")
    slide = prs.slides.add_slide(layout)
    # title placeholder
    title_ph = None
    for ph in slide.placeholders:
        if ph.placeholder_format.type == 13:
            title_ph = ph
            break
    if title_ph is not None:
        tf = title_ph.text_frame
        tf.word_wrap = True
        _add_para(tf, str(plan.get("title") or case.get("title") or "学术汇报"),
                  size=36, bold=True, color=PRIMARY, first=True, space_after=4)
        _add_para(tf, "报告目标：%s" % str(plan.get("report_goal") or "(未给出)")
                  if plan.get("report_goal") else "报告目标：见任务说明",
                  size=16, color=GRAY)
    else:
        box = slide.shapes.add_textbox(Inches(0.7), Inches(0.6), Inches(11.9), Inches(1.6))
        box.name = "cover-title"
        tf = box.text_frame
        tf.word_wrap = True
        _add_para(tf, str(plan.get("title") or case.get("title") or "学术汇报"),
                  size=36, bold=True, color=PRIMARY, first=True)
    # meta box
    meta = slide.shapes.add_textbox(Inches(0.7), Inches(4.6), Inches(11.9), Inches(2.0))
    meta.name = NAME_COVER_META
    tf = meta.text_frame
    tf.word_wrap = True
    aud = plan.get("audience", {})
    description = aud.get("description") if isinstance(aud, dict) else str(aud)
    timing = plan.get("timing", {})
    _add_para(tf, "听众：%s" % description, size=16, color=DARK, first=True, space_after=4)
    _add_para(tf, "时长 %s 分钟 · %s 页 · 每页约 %s 秒，叙事模板：%s" % (
        timing.get("duration_min"), timing.get("slide_target"),
        timing.get("seconds_per_slide"), plan.get("narrative", {}).get("report_type")),
        size=14, color=GRAY, space_after=10)
    _add_para(tf, "evidence-traceable 页面：每页主张均带源材料定位（L+行号 · 章节）",
              size=12, italic=True, color=GRAY)
    slide.notes_slide.notes_text_frame.text = (
        "【封面】%s\n【讲解】开场交代汇报目标与时长约定。\n【源材料】case_id=%s"
        % (plan.get("title"), _verbatim_source(plan)))
    return slide


def _add_figure_block(slide, figure_ref, figure_file, x, y, w, h, case_id, page_no,
                      figure_base=None):
    """Insert real image or an honest placeholder box at (x,y,w,h).

    `figure_file` may be absolute (fresh plan) or relative to the case
    directory (a plan re-read from a portable talk_plan.json) — both resolve."""
    inserted = False
    source = None
    figure_file = resolve_input_path(figure_file, figure_base)
    if figure_file and os.path.splitext(figure_file)[1].lower() in IMAGE_EXTS:
        try:
            from PIL import Image
            with Image.open(figure_file) as im:
                im.verify()
            pic = slide.shapes.add_picture(figure_file, Inches(x), Inches(y),
                                           width=Inches(w), height=Inches(h))
            pic.name = NAME_FIGURE % page_no
            inserted = True
            source = os.path.basename(figure_file)
        except Exception:  # noqa: BLE001
            return False, None
    if not inserted:
        box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y),
                                     Inches(w), Inches(h))
        box.name = NAME_FIGURE % page_no
        box.fill.solid()
        box.fill.fore_color.rgb = LIGHT
        box.line.color.rgb = GRAY
        box.line.width = Pt(1)
        tf = box.text_frame
        tf.word_wrap = True
        label = figure_ref or "图/表"
        _add_para(tf, "图占位：%s" % label, size=16, bold=True, color=PRIMARY,
                  first=True, space_after=4)
        _add_para(tf, "材料未提供对应图片文件，此处为诚实占位框（不虚构插图）；"
                      "讲解时请对照源材料的 %s 原图。" % (label or "对应图"),
                  size=11, color=GRAY)
    return inserted, source


def _make_content_slide(prs, plan, case, page, figure_base=None):
    layout, _ = _pick_layout(prs, "content")
    slide = prs.slides.add_slide(layout)
    # ---- title area ----
    title_ph = None
    for ph in slide.placeholders:
        if ph.placeholder_format.type == 13:
            title_ph = ph
            break
    title_text = "%d. %s" % (page["page_no"], page["title"])
    if title_ph is not None:
        tf = title_ph.text_frame
        tf.word_wrap = True
        _add_para(tf, title_text, size=26, bold=True, color=PRIMARY, first=True)
    else:
        box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.3), Inches(0.8))
        box.name = NAME_TITLE % page["page_no"]
        tf = box.text_frame
        tf.word_wrap = True
        _add_para(tf, title_text, size=26, bold=True, color=PRIMARY, first=True)

    # ---- figure area (right) ----
    fig_inserted, fig_source = _add_figure_block(
        slide, page.get("figure_ref"), page.get("figure_file"),
        x=8.1, y=1.35, w=4.7, h=4.6, case_id=case.get("case_id"),
        page_no=page["page_no"], figure_base=figure_base)

    # ---- body text (left) ----
    body = slide.shapes.add_textbox(Inches(0.5), Inches(1.35), Inches(7.4), Inches(5.3))
    body.name = NAME_CLAIM % page["page_no"]
    tf = body.text_frame
    tf.word_wrap = True
    _add_para(tf, "主张（本页唯一结论）", size=12, bold=True, color=ACCENT, first=True, space_after=2)
    _add_para(tf, page.get("claim") or "(无主张)", size=18, bold=True, color=DARK, space_after=8)
    ev = (page.get("evidence") or [{}])[0]
    if ev:
        _add_para(tf, "证据定位：%s" % ev.get("locator", ""), size=13, bold=True, color=GRAY, space_after=2)
        _add_para(tf, "来源：%s" % ev.get("source_file", ""), size=12, color=GRAY, space_after=2)
        _add_para(tf, "引文：%s" % (ev.get("quote") or "")[:200], size=12, color=GRAY, space_after=10)
    if page.get("figure_ref"):
        _add_para(tf, "图表：%s%s" % (page["figure_ref"],
                                      "（已嵌入材料图）" if fig_inserted else "（占位框，见说明）"),
                  size=12, color=GRAY, space_after=6)
    strength = page.get("strength")
    sc = STRENGTH_COLOR.get(strength, GRAY)
    _add_para(tf, "证据强度：%s" % (strength if strength else "不适用"), size=12,
              bold=True, color=sc, space_after=6)
    _add_para(tf, "讲解一句话：%s" % page.get("one_liner", ""), size=13, italic=True,
              color=PRIMARY, space_after=6)
    if strength == "weak":
        _add_para(tf, "※ 上页为源材料间接概括，强度弱，讲解时请以原论文正文为准并说明来源。",
                  size=11, color=ACCENT)

    # ---- footer ----
    foot = slide.shapes.add_textbox(Inches(0.5), Inches(6.9), Inches(12.3), Inches(0.4))
    foot.name = NAME_FOOTER % page["page_no"]
    tf = foot.text_frame
    _add_para(tf, "%d / %d · %s" % (page["page_no"], plan.get("timing", {}).get("slide_target", 0),
                                    _verbatim_source(plan)),
              size=10, color=GRAY, align=PP_ALIGN.RIGHT, first=True)

    notes_lines = [page.get("notes", "")]
    if page.get("qa"):
        for q in page["qa"]:
            notes_lines.append("【备答】%s → %s" % (q["question"], "；".join(q["answer_points"])))
    slide.notes_slide.notes_text_frame.text = "\n".join(notes_lines)
    return slide, {"page_no": page["page_no"], "title": page["title"], "block": page["block"],
                   "figure_inserted": fig_inserted, "figure_source": fig_source}


def _drop_existing_slides(prs):
    """Remove the template/starting deck's own sample slides.

    The frozen page count comes from the *plan* (audience × duration × the
    task's slide_count), so a starting deck that carries sample slides must not
    inflate the delivered deck: keep its masters/layouts (template constraints
    preserved) and rebuild every planned page.  Returns the number dropped.
    """
    try:
        sld_id_lst = prs.slides._sldIdLst
        removed = 0
        for sld in list(sld_id_lst):
            rId = sld.get(qn("r:id"))
            if rId:
                prs.part.drop_rel(rId)
            sld_id_lst.remove(sld)
            removed += 1
        return removed
    except Exception:  # noqa: BLE001 — never fatal: worst case the pages follow
        return 0


def build_deck(plan, out_pptx, template_path=None, figure_base=None):
    """Build the editable deck.  Returns (manifest, change_records).

    Raises RuntimeError with an actionable message when python-pptx is not
    importable on this host (the orchestrator records it as an honest
    dependency degradation instead of failing the whole run).
    """
    if not PPTX_AVAILABLE:
        raise RuntimeError(
            "python-pptx 不可用（%s）：无法生成可编辑 .pptx。"
            "安装：pip install python-pptx；本次运行的其余产物"
            "（talk_plan.json / plan_gates.json / 预览 / result.json）仍会照常产出并记明该限制。"
            % (PPTX_IMPORT_ERROR or "import failed"))
    change_records = []
    case_id = plan.get("case_id")
    template_load_error = None
    if template_path and os.path.exists(template_path) and template_path.lower().endswith(".pptx"):
        try:
            prs = Presentation(template_path)
        except Exception as exc:  # noqa: BLE001
            # 模板文件存在但不是可打开的 OOXML（容器损坏）：按 D5 回落内置主题，
            # 而不是让 deck 生成抛错 —— 否则一次坏模板会把整轮运行降成 failed。
            template_load_error = "%s: %s" % (type(exc).__name__, exc)
            prs = None
    else:
        prs = None
    if template_path and template_load_error:
        prs = _new_deck()
        mode = {"mode": "built-in-theme", "template_path": None,
                "template_expected": os.path.basename(template_path),
                "template_load_error": template_load_error,
                "note": "案例指定的模板存在但无法作为 pptx 打开（容器损坏/非 OOXML）："
                        "按 D5 回落包内内置母版/主题；该降级已写入 change_records 与 uncertainty"}
        change_records.append({"at": utc_now(), "step": "deck-source",
                               "action": "template %s exists but could NOT be opened (%s); "
                                         "fell back to the built-in master/theme (D5)"
                                         % (os.path.basename(template_path), template_load_error)})
    elif prs is not None:
        auto_slides = len(prs.slides)
        dropped = _drop_existing_slides(prs) if auto_slides else 0
        mode = {"mode": "template-adapt", "template_name": os.path.basename(template_path),
                "template_slides_present": auto_slides,
                "template_slides_dropped": dropped,
                "template_load_error": None,
                "note": "沿用题面提供的模板/起始演示文件：保留其母版与版式（模板约束不破坏），"
                        "页数按冻结计划重建；自带示例页已丢弃以免页数超出冻结值"}
        change_records.append({"at": utc_now(), "step": "deck-source",
                               "action": "adapted template %s (master/layout reused; "
                                         "%d pre-existing slide(s) dropped so the deck matches "
                                         "the frozen page count of %d)"
                                         % (os.path.basename(template_path), dropped,
                                            len(plan.get("pages") or []))})
    else:
        prs = _new_deck()
        mode = {"mode": "built-in-theme", "template_path": None,
                "template_expected": None, "template_load_error": None,
                "note": "未提供模板：使用包内内置母版/主题（16:9，主题色 + 底栏）"}
        change_records.append({"at": utc_now(), "step": "deck-source",
                               "action": "created new deck on built-in master/theme (no template supplied)"})

    manifest = []
    for page in plan["pages"]:
        if page["block"] in ("title", "agenda", "qa"):
            if page["block"] == "title":
                slide = _make_cover(prs, plan, {"case_id": case_id, "title": plan.get("title")})
                manifest.append({"page_no": page["page_no"], "block": "title",
                                 "title": page["title"], "figure_inserted": False,
                                 "figure_source": None})
            else:
                layout, _ = _pick_layout(prs, "content")
                slide = prs.slides.add_slide(layout)
                title_ph = None
                for ph in slide.placeholders:
                    if ph.placeholder_format.type == 13:
                        title_ph = ph
                        break
                if title_ph is not None:
                    tf = title_ph.text_frame
                    tf.word_wrap = True
                    _add_para(tf, "%d. %s" % (page["page_no"], page["title"]), size=26,
                              bold=True, color=PRIMARY, first=True)
                else:
                    box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.3), Inches(0.8))
                    box.name = NAME_TITLE % page["page_no"]
                    _add_para(box.text_frame, "%d. %s" % (page["page_no"], page["title"]),
                              size=26, bold=True, color=PRIMARY, first=True)
                body = slide.shapes.add_textbox(Inches(0.5), Inches(1.4), Inches(12.3), Inches(3.0))
                body.name = NAME_CLAIM % page["page_no"]
                tf = body.text_frame
                tf.word_wrap = True
                _add_para(tf, page.get("claim") or "", size=18, color=DARK, first=True, space_after=8)
                _add_para(tf, page.get("one_liner") or "", size=14, italic=True, color=GRAY)
                slide.notes_slide.notes_text_frame.text = page.get("notes", "")
                manifest.append({"page_no": page["page_no"], "block": page["block"],
                                 "title": page["title"], "figure_inserted": False,
                                 "figure_source": None})
            continue
        slide, rec = _make_content_slide(prs, plan, {"case_id": case_id}, page,
                                         figure_base=figure_base)
        manifest.append(rec)

    ensure_out = os.path.dirname(out_pptx)
    if ensure_out:
        os.makedirs(ensure_out, exist_ok=True)
    prs.save(out_pptx)
    # `path` is reported as the file name only — the caller knows the directory,
    # and no local absolute path may travel inside the produced artefacts.
    return {"mode": mode, "manifest": manifest, "path": os.path.basename(out_pptx)}, change_records