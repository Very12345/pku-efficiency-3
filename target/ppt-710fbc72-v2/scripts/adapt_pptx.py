# -*- coding: utf-8 -*-
"""adapt_pptx.py — two-phase workflow, phase 2: apply the adaptation plan and
build the editable PPTX (python-pptx).

Full template adaptation layer:
  1. resolve template = case template -> starting deck -> builtin (skill asset);
  2. apply the phase-1 adopt_plan.json page->layout assignments (each page uses
     its recommended layout when it truly provides the required placeholders;
     otherwise best-fit + deviation recorded — nothing is silently changed);
  3. fill placeholders (theme fonts/colours inherited), manual textboxes only
     when a required placeholder is missing (fallback recorded);
  4. contain-fit figures (never stretch), native tables, uniform footer +
     page number, speaker notes per page;
  5. font-size ladder against real box geometry (no silent shrink below 12pt).

Geometry decisions are deterministic given the plan.
"""
from __future__ import annotations

import os

from common import (PALETTE, hex_to_rgb, emu_to_pt, fit_font_size, dump_json,
                    utf8_writer, SKILL_NAME, SKILL_VERSION, load_json)
import pptx_toolkit as tk

from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

_VERSION = "2.0.0"

_REQUIRED = {
    "cover": (("title",), ("subtitle",)),
    "thankyou": (("title",), ("subtitle",)),
    "default": (("title",), ("body", "content", "placeholder")),
}


# --------------------------------------------------------------------------
def _set_or_add_text(slide, layout, page_type: str, role: str, text: str,
                     size_start: int, box_w: int, box_h: int, min_size=12.0,
                     color: str | None = None, align=None, bold=False,
                     parts: list | None = None) -> dict:
    """Fill a title/body through the layout placeholder when present, else a
    manual text box. Returns {used: 'placeholder'|'textbox', idx, size_pt}."""
    if role == "title":
        ph = tk.find_ph(slide, "title") or tk.find_ph(layout, "title")
    elif role == "subtitle":
        ph = tk.find_ph(slide, "subtitle")
        if ph is None:
            ph = tk.find_ph(layout, "subtitle")
    else:  # body
        ph = tk.find_ph(slide, "content", "body", "object", "内容")
        if ph is None:
            ph = tk.find_ph(layout, "content", "body", "object", "内容")

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


def _add_figure(slide, path: str, box_l, box_t, box_w, box_h, adjust_log: list) -> dict:
    try:
        from PIL import Image
        with Image.open(path) as im:
            pw, ph = im.size
    except Exception:
        pw, ph = 0, 0
    w, h, scale = tk.contain_fit(pw, ph, box_w, box_h)
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
    for ci, col_w in enumerate(tk.col_widths(n_cols, emu_to_pt(box_w))):
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


def _add_footer(slide, text: str, page_no: int, slide_w_emu: int, slide_h_emu: int,
                skip: bool = False) -> None:
    if skip:
        return
    tb = slide.shapes.add_textbox(Inches(0.4), slide_h_emu - Inches(0.32), Inches(6.5), Inches(0.24))
    tf = tb.text_frame
    tf.word_wrap = False
    run = tf.paragraphs[0].add_run()
    run.text = text[:45]
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(*hex_to_rgb(PALETTE["muted"]))
    pn = slide.shapes.add_textbox(slide_w_emu - Inches(1.1), slide_h_emu - Inches(0.32), Inches(0.7), Inches(0.24))
    pf = pn.text_frame
    pf.paragraphs[0].alignment = PP_ALIGN.RIGHT
    run2 = pf.paragraphs[0].add_run()
    run2.text = str(page_no)
    run2.font.size = Pt(9)
    run2.font.color.rgb = RGBColor(*hex_to_rgb(PALETTE["muted"]))


def build(content: dict, plan: dict, out_pptx: str, template_path: str = "",
          starting_deck: str = "", builtin_template: str = "",
          adopt_plan: dict | None = None) -> dict:
    """Assemble the deck (phase 2). Returns audit object for audit.json."""
    prs, opened_from, template_source, tpl_errors = tk.resolve_template(
        template_path, starting_deck, builtin_template)

    before_slides = len(prs.slides._sldIdLst)
    dropped = tk.drop_slides(prs) if (opened_from in ("case_template", "starting_deck")) else 0

    sw, sh = prs.slide_width, prs.slide_height
    scores = tk.layout_scores(prs)
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
    adopt_deviations = []
    adopted_count = 0
    rec_by_page = {}
    if adopt_plan:
        for a in adopt_plan.get("page_assignments", []):
            rec_by_page[a["page_no"]] = a

    for p in pages:
        page_type = p["page_type"]
        page_no = p["page_no"]

        # ---- phase-2 applies the phase-1 recommendation -------------------
        rec = rec_by_page.get(page_no)
        layout = None
        matched = 0
        plan_source = "best_fit"
        if rec is not None and rec.get("recommended_layout_idx", -1) >= 0:
            lidx = rec["recommended_layout_idx"]
            try:
                cand = prs.slide_layouts[lidx]
                roles = tk.ROLES_COVER if page_type in ("cover", "thankyou") else tk.ROLES_DEFAULT
                ok, missing = tk.layout_provides(prs, cand, roles)
                if ok:
                    layout = cand
                    matched = 2
                    plan_source = "adopt_plan"
                    adopted_count += 1
                else:
                    adopt_deviations.append({"page_no": page_no, "page_type": page_type,
                                             "reason": f"recommended layout {lidx} misses roles {missing}"})
            except Exception as exc:
                adopt_deviations.append({"page_no": page_no, "page_type": page_type,
                                         "reason": f"recommended layout {lidx} unusable: {exc}"})
        if layout is None:
            layout, matched, detail, _fb = tk.best_layout(prs, page_type)
            if rec is not None and plan_source != "adopt_plan":
                adopt_deviations.append({"page_no": page_no, "page_type": page_type,
                                         "reason": "best-fit used instead of adopt_plan recommendation"})
            plan_source = "best_fit"
        detail = f"layout='{layout.name}' master='{tk.master_name(layout)}' [applied via {plan_source}]"

        if page_type == "cover":
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
            sub_part = _set_or_add_text(slide, layout, page_type, "subtitle",
                                        "\n".join(sub_lines), 18,
                                        emu_to_pt(sw - Emu(int(3 * 914400))),
                                        emu_to_pt(Emu(int(1.6 * 914400))), color=PALETTE["body"],
                                        align=PP_ALIGN.CENTER)
            page_audit.append({"page_no": page_no, "page_type": page_type,
                               "title_fit": title_part, "subtitle_fit": sub_part})
            layout_used.append({"page_no": page_no, "layout": detail,
                                "fallback": False, "matched": matched,
                                "plan_source": plan_source})

        elif page_type == "thankyou":
            slide = prs.slides.add_slide(layout)
            _set_or_add_text(slide, layout, page_type, "title", p["title"], 32,
                             emu_to_pt(sw - Emu(int(2 * 914400))), emu_to_pt(Emu(int(1.0 * 914400))),
                             color=PALETTE["ink"], align=PP_ALIGN.CENTER, bold=True)
            meta = p.get("thank_meta", {})
            sub = f"{meta.get('title', '')} · {meta.get('affiliation', '')}"
            _set_or_add_text(slide, layout, page_type, "subtitle", sub, 16,
                             emu_to_pt(sw - Emu(int(3 * 914400))), emu_to_pt(Emu(int(1.0 * 914400))),
                             color=PALETTE["body"], align=PP_ALIGN.CENTER)
            layout_used.append({"page_no": page_no, "layout": detail,
                                "fallback": False, "matched": matched,
                                "plan_source": plan_source})
            page_audit.append({"page_no": page_no, "page_type": page_type})

        elif page_type == "evidence_map":
            slide = prs.slides.add_slide(layout)
            tpart = _set_or_add_text(slide, layout, page_type, "title", p["title"], 24,
                                     emu_to_pt(sw - Emu(int(2 * 914400))), emu_to_pt(Emu(int(0.9 * 914400))),
                                     color=PALETTE["ink"])
            rows = [["页", "页型", "主张", "论文/材料位置"]]
            for row in p.get("evidence_rows", [])[:24]:
                rows.append([str(row["page"]), row["page_type"], row["claim"][:38], row["loc"]])
            body_ph = tk.find_ph(slide, "content", "body", "object", "text") or tk.find_ph(layout, "content", "body", "object", "text")
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
            layout_used.append({"page_no": page_no, "layout": detail,
                                "fallback": False, "matched": matched,
                                "plan_source": plan_source})

        else:
            slide = prs.slides.add_slide(layout)
            tpart = _set_or_add_text(slide, layout, page_type, "title", p["title"], 24,
                                     emu_to_pt(sw - Emu(int(2 * 914400))), emu_to_pt(Emu(int(0.9 * 914400))),
                                     color=PALETTE["ink"])
            is_results = page_type == "results"
            body_ph = tk.find_ph(slide, "content", "body", "object", "text") or tk.find_ph(layout, "content", "body", "object", "text")
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
                left_w = Emu(int(bw * 0.42))
                right_w = bw - left_w - Emu(int(0.2 * 914400))
                parts = []
                for c in claims[:5]:
                    parts.append((c, 0, False, 0))
                bpart = _set_or_add_text(slide, layout, page_type, "body",
                                         "", 18, emu_to_pt(left_w), emu_to_pt(bh),
                                         parts=parts, color=PALETTE["body"])
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
                rows = [[t["id"], "值/内容"]]
                for r in (t.get("rows") or [])[:14]:
                    if isinstance(r, (list, tuple)):
                        rows.append([str(r[0]), str(r[1]) if len(r) > 1 else ""])
                    else:
                        rows.append([str(r), ""])
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

            layout_used.append({"page_no": page_no, "layout": detail,
                                "fallback": False, "matched": matched,
                                "plan_source": plan_source})

        notes = p.get("notes") or ""
        claims_txt = " | ".join(p.get("claims") or [])
        ev_txt = "; ".join(f"{e['claim'][:60]} @ {e['loc']}" for e in (p.get("evidence") or [])[:4])
        note_full = f"PAGE {page_no} [{page_type}]\n{notes}\n主张: {claims_txt or '（无独立主张，承接上一页）'}\n证据: {ev_txt or '（本页为结构页）'}"
        try:
            ns = slide.notes_slide
            ns.notes_text_frame.text = note_full[:3800]
        except Exception as exc:
            page_audit[-1]["notes_error"] = str(exc)

        _add_footer(slide, deck_title, page_no, sw, sh, skip=(page_type == "cover"))

    os.makedirs(os.path.dirname(os.path.abspath(out_pptx)), exist_ok=True)
    prs.save(out_pptx)
    tk.deterministic_zip(out_pptx, out_pptx + ".dztmp")

    audit = {
        "template_source": template_source,
        "opened_from": opened_from,
        "template_errors": tpl_errors,
        "slide_size_emu": [int(sw), int(sh)],
        "layouts": scores,
        "layout_used": layout_used,
        "adopt_plan_applied": adopted_count if adopt_plan else None,
        "adopt_plan_total_pages": len(pages) if adopt_plan else None,
        "adopt_plan_deviations": adopt_deviations,
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
    import json
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--content", required=True)
    ap.add_argument("--spec", required=True)
    ap.add_argument("--out", required=True, help="output pptx path")
    ap.add_argument("--template", default="")
    ap.add_argument("--starting-deck", default="")
    ap.add_argument("--builtin", default="")
    ap.add_argument("--adopt-plan", default="", help="adopt_plan.json (phase-1 plan)")
    a = ap.parse_args(argv)
    content = json.load(open(a.content, "r", encoding="utf-8-sig"))
    plan = json.load(open(a.spec, "r", encoding="utf-8-sig"))
    adopt = None
    if a.adopt_plan and os.path.exists(a.adopt_plan):
        adopt = load_json(a.adopt_plan)
    audit = build(content, plan, a.out, a.template, a.starting_deck, a.builtin, adopt)
    dump_json(a.out.replace(".pptx", "") + ".build_audit.json", audit)
    print(f"adapt-pptx ok: {a.out} pages={audit['pages_built']} opened_from={audit['opened_from']} "
          f"adopt_plan_applied={audit['adopt_plan_applied']} deviations={len(audit['adopt_plan_deviations'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())