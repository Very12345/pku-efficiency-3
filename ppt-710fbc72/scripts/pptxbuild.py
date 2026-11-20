# -*- coding: utf-8 -*-
"""pptxbuild.py — template-aware editable PPTX builder (python-pptx).

Template adaptation layer:
  1. resolve template = case template -> starting deck -> builtin (skill asset);
  2. inspect master/layouts/placeholders, best-fit a layout per page type;
  3. fill placeholders (theme fonts/colours inherited), manual textboxes only
     when a required placeholder is missing (fallback recorded);
  4. contain-fit figures (never stretch), native tables, uniform footer +
     page number, speaker notes per page;
  5. font-size ladder against real box geometry (no silent shrink below 12pt).

All geometry decisions are deterministic given the plan.
"""
from __future__ import annotations

import os
from common import (PALETTE, hex_to_rgb, emu_to_pt, fit_font_size, dump_json,
                    utf8_writer, SKILL_NAME, SKILL_VERSION)

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

EMU_16x9 = (12192000, 6858000)

# page_type -> required placeholder name fragments (matched case-insensitively)
_REQUIRED = {
    "cover": (("title",), ("subtitle",)),
    "thankyou": (("title",), ("subtitle",)),
    "default": (("title",), ("body", "content", "placeholder")),
}


def _ph_fragments(ph) -> list[str]:
    name = ""
    try:
        name = ph.name or ""
    except Exception:
        pass
    idx = -1
    try:
        idx = ph.placeholder_format.idx if ph.has_placeholder_fmt else -1
    except Exception:
        idx = -1
    frags = [name.lower(), str(idx)]
    if name:
        frags.append(name.lower().replace(" ", ""))
    return frags


def layout_scores(prs) -> list[dict]:
    out = []
    for li, layout in enumerate(prs.slide_layouts):
        phs = []
        mname = ""
        try:
            mname = layout.slide_master.name or ""
        except Exception:
            mname = ""
        try:
            for ph in layout.placeholders:
                w = h = None
                try:
                    w, h = ph.width, ph.height
                except Exception:
                    pass
                phs.append({"idx": ph.placeholder_format.idx,
                            "name": getattr(ph, "name", None) or "", "w": w, "h": h})
        except Exception:
            phs = []
        out.append({"idx": li, "name": layout.name or f"layout-{li}", "master": mname,
                    "placeholders": phs})
    return out


def _best_layout(prs, scores: list[dict], page_type: str) -> tuple:
    """Pick the layout that truly provides the requested placeholders.

    "text" placeholders (Section Header side texts, Comparison side texts) are
    NOT treated as content body; full-width single-body layouts are preferred
    so text is not squeezed into narrow columns.
    """

    def name_frags(layout):
        frags = []
        for ph in getattr(layout, "placeholders", []):
            frags.extend(_ph_fragments(ph))
        return [str(f).lower() for f in frags]

    def has_any(frags, patterns):
        return any(p in f for f in frags for p in patterns)

    def body_phs(layout):
        out = []
        for ph in getattr(layout, "placeholders", []):
            f = [str(x).lower() for x in _ph_fragments(ph)]
            if has_any(f, ("content", "body", "object", "内容")):
                out.append(ph)
        return out

    best = None
    best_idx = -1
    best_score = -1.0
    for idx, layout in enumerate(prs.slide_layouts):
        frags = name_frags(layout)
        has_title = has_any(frags, ("title", "标题"))
        has_sub = has_any(frags, ("subtitle", "副标题"))
        bodies = body_phs(layout)
        if page_type in ("cover", "thankyou"):
            score = 0.0
            if has_title and has_sub:
                score += 1000.0
            elif has_title:
                score += 500.0
            score += min(len(getattr(layout, "placeholders", [])), 12)
        else:
            if not (has_title and bodies):
                score = 0.0
            else:
                score = 1000.0
                if len(bodies) == 1:
                    score += 300.0          # single content body (preferred)
                else:
                    score += 30.0           # split bodies: usable but discouraged
                try:
                    sw = prs.slide_width
                    best_bw = max((b.width or 0) for b in bodies)
                    if sw and best_bw and best_bw >= sw * 0.5:
                        score += 200.0      # full-width body
                except Exception:
                    pass
                score += min(len(getattr(layout, "placeholders", [])), 12)
        if score > best_score:
            best_score = score
            best = layout
            best_idx = idx
    matched = 2 if best_score >= 800 else (1 if best_score > 0 else 0)
    name = best.name or f"layout-{best_idx}"
    detail = f"layout='{name}' (idx~{best_idx}) master='{_master_name(best)}'"
    fallback = best_score < 800
    return best, matched, detail, fallback


def _master_name(layout) -> str:
    try:
        return layout.slide_master.name or ""
    except Exception:
        return ""


def _find_ph(slide_or_layout, *patterns) -> object | None:
    """Find a placeholder whose name/idx contains any pattern (case-insensitive)."""
    for ph in getattr(slide_or_layout, "placeholders", []):
        frags = _ph_fragments(ph)
        for pat in patterns:
            for f in frags:
                if pat and pat.lower() in str(f).lower():
                    return ph
    return None


def _set_or_add_text(slide, layout, page_type: str, role: str, text: str,
                     size_start: int, box_w: int, box_h: int, min_size=12.0,
                     color: str | None = None, align=None, bold=False,
                     parts: list | None = None) -> dict:
    """Fill a title/body through the layout placeholder when present, else a
    manual text box. Returns {used: 'placeholder'|'textbox', idx, size_pt}."""
    if role == "title":
        ph = _find_ph(slide, "title") or _find_ph(layout, "title")
    elif role == "subtitle":
        ph = _find_ph(slide, "subtitle")
        if ph is None:
            ph = _find_ph(layout, "subtitle")
    else:  # body
        ph = _find_ph(slide, "content", "body", "object", "内容")
        if ph is None:
            ph = _find_ph(layout, "content", "body", "object", "内容")

    if ph is not None:
        try:
            w = emu_to_pt(ph.width) if ph.width else box_w
            h = emu_to_pt(ph.height) if ph.height else box_h
        except Exception:
            w, h = box_w, box_h
        used = "placeholder"
    else:
        w, h = box_w, box_h
        used = "textbox"

    paras = []
    if parts:  # [(text, level, bold)]
        paras = [p[0] for p in parts]
    else:
        paras = [text]

    size, overflow = fit_font_size(paras, w, h, size_start, min_size)

    if ph is not None:
        tf = ph.text_frame
        tf.clear()
    else:
        box = slide.shapes.add_textbox(0, 0, Emu(int(w * 12700)), Emu(int(h * 12700)))
        tf = box.text_frame

    tf.word_wrap = True
    if parts:
        first = True
        for ptext, level, is_bold, psize in parts:
            para = tf.paragraphs[0] if first else tf.add_paragraph()
            first = False
            para.level = min(level or 0, 4)
            if align is not None:
                para.alignment = align
            run = para.add_run()
            prefix = "• " if (level or 0) == 0 else ("– " if (level or 0) == 1 else "")
            run.text = prefix + ptext
            run.font.size = Pt(psize if psize else size)
            run.font.bold = is_bold or (role == "title")
            if color:
                run.font.color.rgb = RGBColor(*hex_to_rgb(color))
    else:
        para = tf.paragraphs[0]
        if align is not None:
            para.alignment = align
        run = para.add_run()
        run.text = text
        run.font.size = Pt(size)
        run.font.bold = bold
        if color:
            run.font.color.rgb = RGBColor(*hex_to_rgb(color))
    return {"used": used, "idx": ph.placeholder_format.idx if ph is not None else None,
            "size_pt": size, "overflow_lines": overflow}


def _contain_fit(img_w: int, img_h: int, box_w_emu: int, box_h_emu: int) -> tuple:
    """Return (w_emu, h_emu, scale) preserving aspect ratio (contain-fit)."""
    if img_w <= 0 or img_h <= 0 or box_w_emu <= 0 or box_h_emu <= 0:
        return box_w_emu, box_h_emu, 1.0
    scale = min(box_w_emu / img_w, box_h_emu / img_h)
    return int(img_w * scale), int(img_h * scale), scale


def _add_figure(slide, path: str, box_l, box_t, box_w, box_h, adjust_log: list) -> dict:
    try:
        from PIL import Image
        with Image.open(path) as im:
            pw, ph = im.size
    except Exception:
        pw, ph = 0, 0
    w, h, scale = _contain_fit(pw, ph, box_w, box_h)
    try:
        pic = slide.shapes.add_picture(path, box_l, box_t, width=Emu(w), height=Emu(h))
        log = {"src": os.path.basename(path), "aspect_preserved": True,
               "scale": round(scale, 4), "w_emu": w, "h_emu": h, "placed": True}
    except Exception as exc:
        box = slide.shapes.add_shape(1, box_l, box_t, Emu(box_w), Emu(box_h))
        box.fill.solid()
        box.fill.fore_color.rgb = RGBColor(*hex_to_rgb("#F2F2F2"))
        box.line.color.rgb = RGBColor(*hex_to_rgb(PALETTE["rule"]))
        ctf = box.text_frame
        ctf.word_wrap = True
        ctf.paragraphs[0].text = f"图片无法嵌入：{os.path.basename(path)}（{exc}）"
        ctf.paragraphs[0].font.size = Pt(11)
        ctf.paragraphs[0].font.color.rgb = RGBColor(*hex_to_rgb(PALETTE["muted"]))
        log = {"src": os.path.basename(path), "aspect_preserved": True, "scale": round(scale, 4),
               "w_emu": w, "h_emu": h, "placed": False, "error": str(exc)}
    adjust_log.append(log)
    return log


def _add_table(slide, rows: list, box_l, box_t, box_w, box_h,
               caption: str = "", source: str = "") -> dict:
    from pptx.util import Pt as _Pt
    if not rows:
        return {"rows": 0, "note": "empty table data"}
    n_rows = len(rows)
    n_cols = max(len(r) for r in rows)
    if n_rows == 0 or n_cols == 0:
        return {"rows": 0, "note": "empty table data"}
    tb = slide.shapes.add_table(n_rows, n_cols, box_l, box_t, box_w, box_h).table
    for ci, col_w in enumerate(_col_widths(n_cols, emu_to_pt(box_w))):
        try:
            tb.columns[ci].width = Emu(int(col_w * 12700))
        except Exception:
            pass
    for ri, row in enumerate(rows):
        for ci in range(n_cols):
            val = row[ci] if ci < len(row) else ""
            cell = tb.cell(ri, ci)
            cell.text_frame.text = str(val)
            for para in cell.text_frame.paragraphs:
                for run in para.runs:
                    run.font.size = _Pt(11 if ri == 0 or n_rows > 6 else 12)
                    run.font.bold = ri == 0
            if ri == 0:
                cell.fill.solid()
                cell.fill.fore_color.rgb = RGBColor(*hex_to_rgb(PALETTE["ink"]))
                for para in cell.text_frame.paragraphs:
                    for run in para.runs:
                        run.font.color.rgb = RGBColor(255, 255, 255)
    return {"rows": n_rows, "cols": n_cols, "caption": caption, "source": source}


def _col_widths(n_cols: int, width_pt: float) -> list:
    return [width_pt / n_cols] * n_cols


def _add_footer(slide, text: str, page_no: int, slide_w_emu: int, slide_h_emu: int,
                skip: bool = False) -> None:
    if skip:
        return
    from pptx.util import Inches as _In
    tb = slide.shapes.add_textbox(_In(0.4), slide_h_emu - _In(0.32), _In(6.5), _In(0.24))
    tf = tb.text_frame
    tf.word_wrap = False
    run = tf.paragraphs[0].add_run()
    run.text = text[:45]
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(*hex_to_rgb(PALETTE["muted"]))
    pn = slide.shapes.add_textbox(slide_w_emu - _In(1.1), slide_h_emu - _In(0.32), _In(0.7), _In(0.24))
    pf = pn.text_frame
    pf.paragraphs[0].alignment = PP_ALIGN.RIGHT
    run2 = pf.paragraphs[0].add_run()
    run2.text = str(page_no)
    run2.font.size = Pt(9)
    run2.font.color.rgb = RGBColor(*hex_to_rgb(PALETTE["muted"]))


def _deterministic_zip(src: str, tmp: str) -> None:
    """Rewrite the saved pptx as a zip with fixed entry timestamps so the same
    input produces byte-identical pptx (content bytes are already a pure
    function of the plan; only zip entry dates varied run-to-run)."""
    import shutil
    import zipfile
    with zipfile.ZipFile(src, "r") as zin, \
         zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            n = zipfile.ZipInfo(item.filename, date_time=(1980, 1, 1, 0, 0, 0))
            n.compress_type = zipfile.ZIP_DEFLATED
            n.comment = item.comment
            zout.writestr(n, zin.read(item.filename))
    shutil.move(tmp, src)


def _drop_slides(prs) -> int:
    xml_slides = prs.slides._sldIdLst
    slides = list(xml_slides)
    for s in slides:
        xml_slides.remove(s)
    return len(slides)


def build(content: dict, plan: dict, out_pptx: str, template_path: str = "",
          starting_deck: str = "", builtin_template: str = "") -> dict:
    """Assemble the deck. Returns audit object to merge into audit.json."""

    # ---- resolve source deck / template ------------------------------------
    template_source = "builtin"
    prs = None
    tried = []
    candidates = []
    if template_path and os.path.exists(template_path):
        candidates.append(("case_template", template_path))
    if starting_deck and os.path.exists(starting_deck):
        candidates.append(("starting_deck", starting_deck))
    if builtin_template and os.path.exists(builtin_template):
        candidates.append(("builtin", builtin_template))

    opened_from = ""
    template_errors = []
    for label, path in candidates:
        try:
            prs = Presentation(path)
            opened_from = label
            template_source = path
            break
        except Exception as exc:
            template_errors.append(f"{label}: {exc}")
    if prs is None:
        raise RuntimeError(
            "no usable template (case template / starting deck / builtin all failed): "
            + "; ".join(template_errors or ["no candidate templates at all"]))

    before_slides = len(prs.slides._sldIdLst)
    dropped = _drop_slides(prs) if (opened_from in ("case_template", "starting_deck")) else 0

    # ---- geometry ------------------------------------------------------------
    sw, sh = prs.slide_width, prs.slide_height
    if opened_from == "builtin":
        pass  # builtin already 16:9
    scores = layout_scores(prs)

    lang = content.get("language") or "zh"
    deck_title = content.get("title") or "Academic talk"
    cover_meta = []
    for a in (content.get("authors") or [])[:3]:
        cover_meta.append(a if isinstance(a, str) else str(a.get("text", a)))
    aff = content.get("affiliation") or ""
    audience = content.get("audience") or ""
    dur = content.get("duration_minutes") or 15

    pages = plan["pages"]
    page_audit = []
    layout_used = []
    adjust_log = []
    for p in pages:
        page_type = p["page_type"]
        page_no = p["page_no"]

        if page_type == "cover":
            layout, matched, detail, fallback = _best_layout(prs, scores, "cover")
            slide = prs.slides.add_slide(layout)
            title_part = _set_or_add_text(slide, layout, page_type, "title",
                                          p["title"], 32, emu_to_pt(sw - Emu(int(2 * 914400))),
                                          emu_to_pt(Emu(int(1.2 * 914400))), color=PALETTE["ink"],
                                          align=PP_ALIGN.CENTER, bold=True)
            sub_lines = []
            if content.get("subtitle"):
                sub_lines.append(content["subtitle"])
            if cover_meta:
                sub_lines.append(" / ".join(cover_meta))
            if aff:
                sub_lines.append(aff)
            sub_lines.append(f"{audience} · 约{dur}分钟")
            subtitle_txt = "\n".join(sub_lines)
            sub_part = _set_or_add_text(slide, layout, page_type, "subtitle",
                                        subtitle_txt, 18, emu_to_pt(sw - Emu(int(3 * 914400))),
                                        emu_to_pt(Emu(int(1.6 * 914400))), color=PALETTE["body"],
                                        align=PP_ALIGN.CENTER)
            page_audit.append({"page_no": page_no, "page_type": page_type,
                               "title_fit": title_part, "subtitle_fit": sub_part})
            layout_used.append({"page_no": page_no, "layout": detail, "fallback": bool(fallback),
                                "matched": matched})

        elif page_type == "thankyou":
            layout, matched, detail, fallback = _best_layout(prs, scores, "thankyou")
            slide = prs.slides.add_slide(layout)
            _set_or_add_text(slide, layout, page_type, "title", p["title"], 32,
                             emu_to_pt(sw - Emu(int(2 * 914400))), emu_to_pt(Emu(int(1.0 * 914400))),
                             color=PALETTE["ink"], align=PP_ALIGN.CENTER, bold=True)
            meta = p.get("thank_meta", {})
            sub = f"{meta.get('title', '')} · {meta.get('affiliation', '')}"
            _set_or_add_text(slide, layout, page_type, "subtitle", sub, 16,
                             emu_to_pt(sw - Emu(int(3 * 914400))), emu_to_pt(Emu(int(1.0 * 914400))),
                             color=PALETTE["body"], align=PP_ALIGN.CENTER)
            layout_used.append({"page_no": page_no, "layout": detail, "fallback": bool(fallback),
                                "matched": matched})
            page_audit.append({"page_no": page_no, "page_type": page_type})

        elif page_type == "evidence_map":
            layout, matched, detail, fallback = _best_layout(prs, scores, "default")
            slide = prs.slides.add_slide(layout)
            tpart = _set_or_add_text(slide, layout, page_type, "title", p["title"], 24,
                                     emu_to_pt(sw - Emu(int(2 * 914400))), emu_to_pt(Emu(int(0.9 * 914400))),
                                     color=PALETTE["ink"])
            rows = [["页", "页型", "主张", "论文/材料位置"]]
            for row in p.get("evidence_rows", [])[:24]:
                rows.append([str(row["page"]), row["page_type"], row["claim"][:38], row["loc"]])
            body_ph = _find_ph(slide, "content", "body", "object", "text") or _find_ph(layout, "content", "body", "object", "text")
            if body_ph is not None:
                bl = body_ph.left or Emu(int(0.5 * 914400))
                bt = body_ph.top or Emu(int(1.3 * 914400))
                bw = body_ph.width or Emu(int(12 * 914400))
                bh = body_ph.height or Emu(int(5 * 914400))
            else:
                bl, bt, bw, bh = Emu(int(0.5 * 914400)), Emu(int(1.3 * 914400)), Emu(int(12 * 914400)), Emu(int(5 * 914400))
            tab_log = _add_table(slide, rows, bl, bt, bw, bh,
                                 caption="evidence map", source="deckplan evidence rows")
            page_audit.append({"page_no": page_no, "page_type": page_type,
                               "title_fit": tpart, "table": tab_log})
            layout_used.append({"page_no": page_no, "layout": detail, "fallback": bool(fallback),
                                "matched": matched})

        else:
            layout, matched, detail, fallback = _best_layout(prs, scores, "default")
            slide = prs.slides.add_slide(layout)
            tpart = _set_or_add_text(slide, layout, page_type, "title", p["title"], 24,
                                     emu_to_pt(sw - Emu(int(2 * 914400))), emu_to_pt(Emu(int(0.9 * 914400))),
                                     color=PALETTE["ink"])
            is_results = page_type == "results"
            # content region geometry
            body_ph = _find_ph(slide, "content", "body", "object", "text") or _find_ph(layout, "content", "body", "object", "text")
            if body_ph is not None:
                bl, bt = body_ph.left, body_ph.top
                bw, bh = body_ph.width or Emu(int(12 * 914400)), body_ph.height or Emu(int(5 * 914400))
            else:
                bl, bt = Emu(int(0.5 * 914400)), Emu(int(1.3 * 914400))
                bw, bh = Emu(int(12 * 914400)), Emu(int(5 * 914400))

            claims = p.get("claims") or []
            fig_items = p.get("figures_on_page") or []
            tbl_items = p.get("tables_on_page") or []

            if is_results and fig_items:
                # left bullets / right figure
                left_w = Emu(int(bw * 0.42))
                right_w = bw - left_w - Emu(int(0.2 * 914400))
                parts = []
                for c in claims[:5]:
                    parts.append((c, 0, False, 0))
                bpart = _set_or_add_text(slide, layout, page_type, "body",
                                         "", 18, emu_to_pt(left_w), emu_to_pt(bh),
                                         parts=parts, color=PALETTE["body"])
                # up to two figure slots on the right column
                fig_area = list(fig_items[:2])
                n_slots = len(fig_area)
                gap = Emu(int(0.15 * 914400))
                slot_w = Emu(int((right_w - gap * (n_slots - 1)) / max(n_slots, 1)))
                slot_h = Emu(int(bh * 0.72))
                fig_ok = True
                for si, fig in enumerate(fig_area):
                    fbox_l = bl + left_w + Emu(int(0.2 * 914400)) + (gap + slot_w) * si
                    fbox_t = bt
                    if fig.get("exists") and fig.get("file"):
                        _add_figure(slide, fig["file"], fbox_l, fbox_t, slot_w, slot_h, adjust_log)
                    else:
                        fig_ok = False
                        box = slide.shapes.add_shape(1, fbox_l, fbox_t, slot_w, slot_h)
                        box.fill.solid()
                        box.fill.fore_color.rgb = RGBColor(*hex_to_rgb("#F2F2F2"))
                        box.line.color.rgb = RGBColor(*hex_to_rgb(PALETTE["rule"]))
                        ctf = box.text_frame
                        ctf.word_wrap = True
                        ctf.paragraphs[0].text = f"图位 [{fig['id']}]：{fig.get('caption', '')}（源图缺失，见 uncertainty）"[:120]
                        ctf.paragraphs[0].font.size = Pt(11)
                        ctf.paragraphs[0].font.color.rgb = RGBColor(*hex_to_rgb(PALETTE["muted"]))
                    cap = slide.shapes.add_textbox(fbox_l, fbox_t + slot_h + Emu(int(0.05 * 914400)),
                                                   slot_w, Emu(int(0.5 * 914400)))
                    capf = cap.text_frame
                    capf.word_wrap = True
                    ctext = f"{fig['id']}  {fig.get('caption', '')}  [来源: {fig.get('source', '未标注')}]"
                    capf.paragraphs[0].text = ctext
                    capf.paragraphs[0].font.size = Pt(10)
                    capf.paragraphs[0].font.color.rgb = RGBColor(*hex_to_rgb(PALETTE["muted"]))
                page_audit.append({"page_no": page_no, "page_type": page_type,
                                   "title_fit": tpart, "body_fit": bpart,
                                   "figures": [f["id"] for f in fig_area],
                                   "all_figures_placed": fig_ok})
            elif is_results and tbl_items:
                rows = []
                t = tbl_items[0]
                header_row = [t["id"], "值/内容"]
                rows = [header_row]
                for r in (t.get("rows") or [])[:14]:
                    rows.append([str(r[0]) if isinstance(r, list) and r else str(r), ""] if not isinstance(r, (list, tuple)) else [str(r[0]), str(r[1]) if len(r) > 1 else ""])
                body_ph = _find_ph(slide, "content", "body", "object", "text") or _find_ph(layout, "content", "body", "object", "text")
                if body_ph is not None:
                    tbox = body_ph
                else:
                    tbox = None
                tb_log = _add_table(slide, rows, bl, bt, bw, Emu(int(bh * 0.6)),
                                    caption=t["caption"], source=t.get("source", ""))
                cap = slide.shapes.add_textbox(bl, bt + Emu(int(bh * 0.62)) + Emu(int(0.05 * 914400)),
                                               bw, Emu(int(0.5 * 914400)))
                capf = cap.text_frame
                capf.word_wrap = True
                capf.paragraphs[0].text = f"{t['id']}  {t.get('caption', '')}  [来源: {t.get('source', '未标注')}]"
                capf.paragraphs[0].font.size = Pt(10)
                capf.paragraphs[0].font.color.rgb = RGBColor(*hex_to_rgb(PALETTE["muted"]))
                bpart = {"used": "table", "size_pt": 12, "overflow_lines": 0}
                page_audit.append({"page_no": page_no, "page_type": page_type,
                                   "title_fit": tpart, "table": tb_log})
            else:
                parts = []
                for c in (claims or [])[:6]:
                    parts.append((c, 0, False, 0))
                bl2 = bl + Emu(int(0.1 * 914400))
                bw2 = Emu(int(bw * 0.96))
                bpart = _set_or_add_text(slide, layout, page_type, "body",
                                         "", 18, emu_to_pt(bw2), emu_to_pt(bh),
                                         parts=parts, color=PALETTE["body"])
                page_audit.append({"page_no": page_no, "page_type": page_type,
                                   "title_fit": tpart, "body_fit": bpart})

            layout_used.append({"page_no": page_no, "layout": detail, "fallback": bool(fallback),
                                "matched": matched})

        # ---- speaker notes ---------------------------------------------------
        notes = p.get("notes") or ""
        claims_txt = " | ".join(p.get("claims") or [])
        ev_txt = "; ".join(f"{e['claim'][:60]} @ {e['loc']}" for e in (p.get("evidence") or [])[:4])
        note_full = f"PAGE {page_no} [{page_type}]\n{notes}\n主张: {claims_txt or '（无独立主张，承接上一页）'}\n证据: {ev_txt or '（本页为结构页）'}"
        try:
            ns = slide.notes_slide
            ns.notes_text_frame.text = note_full[:3800]
        except Exception as exc:
            page_audit[-1]["notes_error"] = str(exc)

        # ---- footer & page number --------------------------------------------
        _add_footer(slide, deck_title, page_no, sw, sh, skip=(page_type == "cover"))

    os.makedirs(os.path.dirname(os.path.abspath(out_pptx)), exist_ok=True)
    prs.save(out_pptx)
    _deterministic_zip(out_pptx, out_pptx + ".dztmp")

    audit = {
        "template_source": template_source,
        "opened_from": opened_from,
        "template_errors": template_errors,
        "slide_size_emu": [int(sw), int(sh)],
        "layouts": scores,
        "layout_used": layout_used,
        "dropped_original_slides": dropped,
        "before_slides": before_slides,
        "pages_built": len(pages),
        "figure_adjust": adjust_log,
        "page_audit": page_audit,
    }
    return audit


def main(argv=None):
    utf8_writer()
    import argparse
    ap = argparse.ArgumentParser(description="pptxbuild.py — build editable pptx from plan")
    ap.add_argument("--content", required=True)
    ap.add_argument("--spec", required=True)
    ap.add_argument("--out", required=True, help="output pptx path")
    ap.add_argument("--template", default="")
    ap.add_argument("--starting-deck", default="")
    ap.add_argument("--builtin", default="")
    a = ap.parse_args(argv)
    import json
    content = json.load(open(a.content, "r", encoding="utf-8-sig"))
    plan = json.load(open(a.spec, "r", encoding="utf-8-sig"))
    audit = build(content, plan, a.out, a.template, a.starting_deck, a.builtin)
    dump_json(a.out.replace(".pptx", "") + ".build_audit.json", audit)
    print(f"pptxbuild ok: {a.out} pages={audit['pages_built']} opened_from={audit['opened_from']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())