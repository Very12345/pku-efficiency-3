# -*- coding: utf-8 -*-
"""deck_tool.py — build layer: 可编辑 PPTX 建稿 + 图表绑定 + 编辑操作
（对齐高分包 deck_tool / edit_ops）。

职责（build 轴）：
* 模板约束：无外部模板用 templates/default.json（颜色/字体/页脚/槽位全部参数
  化，case spec.style 可覆盖）；有 template_pptx/starting_deck 则沿用其母版
  版式只填内容槽位（母版不动），起始稿先备份到 work/original_inputs/；
* 防溢出：要点 ≤7 条、单条 ≤90 字、字号自动收敛 ≥12pt；仍放不下降级讲稿备注；
* 图表绑定（诚实优先四态）：chart_image（数据表→matplotlib 原样重绘）/
  table（PPTX 原生可编辑表格）/ embedded（材料原图）/ placeholder（位图无数据
  灰框占位，绝无凭空曲线）；
* 编辑操作 apply_edits：update_bullet/add_bullet/remove_bullet/add_note/
  retitle/reorder_pages/set_figure + 版本归档（deck_<v>.pptx）+ 数字再核验
  （编辑引入的新数字同样过 evidence_check）。

edit_ops 决策树见 references/EDIT_OPS.md。
"""
import csv
import copy
import os
import re
import shutil
import warnings as _warnings

from deck_common import (LOG, now_iso, set_run_font, hex_color, ensure_dir,
                         atomic_write_json, safe_name)
from evidence_check import build_evidence_footer, check_claim_numbers

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


# ---------------------------------------------------------------------------
# Template / spec helpers
# ---------------------------------------------------------------------------

def merge_spec(template_spec, case_style):
    """Deep-merge template spec with per-case style overrides."""
    spec = copy.deepcopy(template_spec or DEFAULT_SPEC)
    for k, v in (case_style or {}).items():
        if isinstance(v, dict) and isinstance(spec.get(k), dict):
            spec[k].update(v)
        elif v is not None:
            spec[k] = v
    return spec


def cache_tables(material, work_dir):
    """Copy source tables next to the deck for the native-table fallback."""
    cache_dir = ensure_dir(os.path.join(work_dir, "table_cache"))
    for t in material.tables:
        if t.source_file and os.path.isfile(t.source_file):
            dst = os.path.join(cache_dir, os.path.basename(t.source_file))
            if not os.path.exists(dst):
                shutil.copy2(t.source_file, dst)
    return cache_dir


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


def _char_safe(text, n):
    return text if len(text) <= n else text[: n - 1] + "…"


# ---------------------------------------------------------------------------
# Chart regeneration (matplotlib, data-driven; honest placeholder fallback)
# ---------------------------------------------------------------------------

# Font glyph warnings are expected when CJK fonts are missing — silence user
# warnings but keep the fact for `note` (font family recorded).
_warnings.filterwarnings("ignore", category=UserWarning)


def _matplotlib_ready():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        return plt
    except Exception as e:  # noqa: BLE001
        LOG.warning("matplotlib unavailable: %s", e)
        return None


def _apply_font(plt):
    from deck_common import resolve_font
    family, path = resolve_font("Microsoft YaHei")  # (family, ttf_path|None)
    try:
        from matplotlib import font_manager
        if path and os.path.isfile(path):
            font_manager.fontManager.addfont(path)
        fonts = ["Microsoft YaHei", "SimHei", "Arial", "DejaVu Sans"]
        plt.rcParams["font.sans-serif"] = fonts
        plt.rcParams["axes.unicode_minus"] = False
        return family, True
    except Exception as e:  # noqa: BLE001
        LOG.warning("font setup failed: %s", e)
        return family, False


def _numeric_cols(table):
    """Return (key_col, numeric_cols) where numeric_cols is list of col names
    in which all non-empty cells parse as numbers (int/float or percents)."""
    key_col = table.columns[0] if table.columns else None
    numeric = []
    for col in table.columns[1:]:
        vals, ok = [], True
        for row in table.rows:
            v = (row.get(col) or "").strip()
            if not v:
                continue
            vals.append(_parse_num(v))
            if vals[-1] is None:
                ok = False
                break
        if ok and vals:
            numeric.append((col, vals))
    return key_col, numeric


def _parse_num(v):
    v = v.replace(",", "").strip()
    m = re.fullmatch(r"(-?\d+(?:\.\d+)?)\s*([%％]?)", v)
    if not m:
        return None
    return float(m.group(1))


def _keys(table):
    return [str((row.get(table.columns[0]) or "")).strip() for row in table.rows]


def build_chart(table, work_dir):
    """Regenerate a chart PNG from *table*; returns (png_path, note).
    Raises on failure so caller can fall back to a native editable table."""
    plt = _matplotlib_ready()
    if plt is None:
        raise RuntimeError("matplotlib 不可用")
    family, _ = _apply_font(plt)
    key_col, numeric = _numeric_cols(table)
    if not numeric:
        raise RuntimeError("数据表没有可绘制的数值列：%s" % table.columns)

    keys = _keys(table)
    ncol = len(numeric)
    if ncol == 1:
        fig, ax = plt.subplots(figsize=(4.6, 3.4), dpi=140)
        col, vals = numeric[0]
        ax.bar(range(len(keys)), vals, color="#2E74B5")
        ax.set_xticks(range(len(keys)))
        ax.set_xticklabels(keys, rotation=20, ha="right", fontsize=8)
        ax.set_ylabel(col, fontsize=9)
        ax.set_title(_shorten_title(table.caption), fontsize=10)
        for i, v in enumerate(vals):
            ax.text(i, v, _fmt(v), ha="center", va="bottom", fontsize=7)
        ax.grid(axis="y", alpha=0.25)
    else:
        fig, ax = plt.subplots(figsize=(4.6, 3.4), dpi=140)
        width = 0.8 / ncol
        for j, (col, vals) in enumerate(numeric):
            xs = [i + (j - (ncol - 1) / 2) * width for i in range(len(keys))]
            ax.bar(xs, vals, width=width, label=_shorten_title(col, 12))
        ax.set_xticks(range(len(keys)))
        ax.set_xticklabels(keys, rotation=20, ha="right", fontsize=8)
        ax.set_ylabel("数值", fontsize=9)
        ax.set_title(_shorten_title(table.caption), fontsize=10)
        ax.legend(fontsize=7)
        ax.grid(axis="y", alpha=0.25)

    fig.tight_layout()
    ensure_dir(work_dir)
    png = os.path.join(work_dir, "chart_%s.png" % safe_name(table.id))
    fig.savefig(png, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    note = ("重绘自数据表 %s（%d 行）；字体=%s；未对数据做修改"
            % (table.id, len(table.rows), family or "系统默认"))
    return png, note


def build_placeholder(work_dir, label):
    """Honest placeholder PNG for a paper figure that cannot be redrawn."""
    from PIL import Image, ImageDraw, ImageFont
    from deck_common import resolve_font
    family, path = resolve_font("Microsoft YaHei")
    img = Image.new("RGB", (460, 220), (240, 242, 246))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(path, 14) if path else ImageFont.load_default()
    except Exception:  # noqa: BLE001
        font = ImageFont.load_default()
    d.rectangle([0, 0, 459, 219], outline=(120, 130, 145), width=2)
    msg = label or "原图为位图，未取数重绘（诚实占位）"
    d.text((18, 90), msg[:36], fill=(90, 100, 115), font=font)
    ensure_dir(work_dir)
    png = os.path.join(work_dir, "placeholder_%s.png" % safe_name(label or "fig"))
    img.save(png)
    return png


def _shorten_title(s, n=24):
    s = re.sub(r"\s+", " ", (s or "")).strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def _fmt(v):
    if v == int(v) or abs(v) < 0.001 or abs(v) >= 100:
        return ("%.2f" % v).rstrip("0").rstrip(".")
    return "%.1f" % v


# ---------------------------------------------------------------------------
# Deck build
# ---------------------------------------------------------------------------

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


def build_deck(pages, spec, work_dir, table_cache_dir=None,
               template_pptx=None, starting_deck=None):
    """Build the editable .pptx.

    Returns (pptx_path, change_notes, receipt).
    Template contract: external template masters/layouts are reused; we only
    add content objects (never modify master). starting_deck is backed up to
    work/original_inputs/ and its pages replaced by the plan.
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
        shutil.copy2(starting_deck, os.path.join(backup_root, os.path.basename(starting_deck)))
        try:
            base = Presentation(starting_deck)
            xml_slides = prs.slides._sldIdLst
            n_old = len(list(prs.slides._sldIdLst))
            # starting_deck 的原页面全部替换为按讲义组织的新页（版式/母版保留）
            for sld in list(xml_slides):
                xml_slides.remove(sld)
            adapted_notes.append(
                "starting_deck %s 的原 %d 页已替换为按讲义组织的新页；"
                "原文件备份于 original_inputs/" % (os.path.basename(starting_deck), n_old))
        except Exception as e:  # noqa: BLE001
            adapted_notes.append("starting_deck 替换失败（%s），沿用其模板生成新稿" % e)
            try:
                for sld in list(prs.slides._sldIdLst):
                    prs.slides._sldIdLst.remove(sld)
            except Exception:  # noqa: BLE001
                pass

    title_layout = _pick_layout(prs, "标题", "Title")
    body_layout = _pick_layout(prs, "标题和内容", "Title and Content", "标题和副标题")
    if body_layout is None:
        body_layout = _pick_layout(prs, "内容", "Content", "仅标题", "Title Only")

    colors = spec["colors"]
    fonts = spec["fonts"]
    slots = spec["slots"]
    limits = spec["limits"]
    body_slot = slots["body"]

    receipt = []
    for page in pages:
        layout = title_layout if page.role == "cover" else (body_layout or _pick_layout(prs, "空白", "Blank"))
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
        add_text(ev, [(build_evidence_footer(page), 0, False,
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

        # ---------- speaker notes (separate from on-page text) ----------
        notes_lines = []
        if page.notes:
            notes_lines.append("【讲解】")
            notes_lines += ["- " + n for n in page.notes]
        notes_lines.append("【证据】" + build_evidence_footer(page))
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
    prs.core_properties.author = "academic-ppt-builder v2"
    prs.save(pptx_path)
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


# ---------------------------------------------------------------------------
# Figure binding (chart_image / table / embedded / placeholder resolution)
# ---------------------------------------------------------------------------

def bind_figures(pages, mat, work_dir, chart_builder=None):
    """Resolve figure slots on result pages.

    chart_builder(table, work_dir) -> (image_path, note); raises -> fallback.
    Returns (pages, chart_log) where chart_log records what was done per page.
    """
    log = []
    for p in pages:
        f = p.figure
        if p.role != "result" or f.kind != "table" or not f.table_id:
            continue
        t = next((x for x in mat.tables if x.id == f.table_id), None)
        if t is None or not t.rows:
            f.kind = "placeholder"
            f.note = "绑定数据表缺失/为空，未重绘（诚实占位）"
            log.append({"page": p.index, "kind": "placeholder", "reason": "数据表缺失"})
            continue
        if chart_builder is None:
            f.kind = "table"
            log.append({"page": p.index, "kind": "table", "reason": "未启用图表重绘"})
            continue
        try:
            img, note = chart_builder(t, work_dir)
            f.kind = "chart_image"
            f.image = img
            f.note = note or "由源数据表用 matplotlib 重绘（可编辑数据在 assets/，脚本可复现）"
            log.append({"page": p.index, "kind": "chart_image", "source": t.id})
        except Exception as e:  # noqa: BLE001
            LOG.warning("chart failed for %s: %s", t.id, e)
            f.kind = "table"  # fall back to a native editable pptx table
            f.note = "图表重绘失败，已降级为原生可编辑表格：" + str(e)
            f.image = ""
            log.append({"page": p.index, "kind": "table", "reason": str(e)})
    return pages, log


# ---------------------------------------------------------------------------
# Plan persistence (plan.json = the editable source of the deck)
# ---------------------------------------------------------------------------

def plan_to_dict(pages):
    out = []
    for p in pages:
        fig = p.figure
        figd = {"ref": fig.ref, "kind": fig.kind, "table_id": fig.table_id,
                "image": fig.image, "note": fig.note}
        out.append({"_type": "page", "index": p.index, "role": p.role,
                    "role_label": _role_label(p.role), "title": p.title,
                    "claims": [{"text": c.text, "evidence": c.evidence,
                                "level": c.level, "verified": c.verified,
                                "missing_numbers": c.missing_numbers}
                               for c in p.claims],
                    "figure": figd, "notes": p.notes,
                    "agenda_item": p.agenda_item})
    return out


def _role_label(role):
    from slide_text import ROLE_LABELS
    return ROLE_LABELS.get(role, role)


def dump_plan(pages, plan_path):
    atomic_write_json(plan_path, {"generated_at": now_iso(),
                                  "schema": "academic-ppt-plan/v2",
                                  "pages": plan_to_dict(pages)})
    return plan_path


def pages_from_dict(list_of_dicts):
    """Rebuild Page objects from plan dicts (used after --edit)."""
    from slide_text import Claim, FigureSlot, Page
    out = []
    for d in list_of_dicts:
        fig = d.get("figure", {})
        p = Page(
            index=int(d["index"]), role=d.get("role", "content"),
            title=d.get("title", ""),
            claims=[Claim(text=c.get("text", ""), evidence=c.get("evidence", []),
                          level=c.get("level", 0), verified=c.get("verified", True),
                          missing_numbers=c.get("missing_numbers", []))
                    for c in d.get("claims", [])],
            figure=FigureSlot(ref=fig.get("ref", ""), kind=fig.get("kind", "none"),
                              table_id=fig.get("table_id", ""),
                              image=fig.get("image", ""), note=fig.get("note", "")),
            notes=list(d.get("notes", [])),
            agenda_item=d.get("agenda_item", ""))
        out.append(p)
    return out


# ---------------------------------------------------------------------------
# Edit operations (演示稿迭代：局部编辑、版本记录、可回退)
# ---------------------------------------------------------------------------

def apply_edits(plan_pages, edits, material_text, changelog, version):
    """Apply JSON edit ops to a plan; returns (pages_dicts, applied, skipped).

    Ops (see references/EDIT_OPS.md): update_bullet / add_bullet /
    remove_bullet / add_note / retitle / reorder_pages / set_figure.
    Every modified/added claim text is re-verified against material_text —
    编辑不得引入材料外数字（不编造红线在编辑链路同样生效）。
    """
    pages = plan_to_dict(plan_pages)  # work on plain dicts
    applied, skipped = [], []
    for op in edits.get("ops", []) or []:
        kind = op.get("op")
        try:
            if kind == "retitle":
                p = _page(pages, op["page"])
                p["title"] = op["title"]
            elif kind == "update_bullet":
                p = _page(pages, op["page"])
                c = p["claims"][op["bullet_index"]]
                c["text"] = op["text"]
                if "evidence" in op:
                    c["evidence"] = op["evidence"]
                ok, missing = check_claim_numbers(op["text"], material_text)
                c["verified"] = ok
                c["missing_numbers"] = missing
            elif kind == "add_bullet":
                p = _page(pages, op["page"])
                ok, missing = check_claim_numbers(op["text"], material_text)
                c = {"text": op["text"], "evidence": op.get("evidence", []),
                     "level": op.get("level", 0), "verified": ok,
                     "missing_numbers": missing}
                p["claims"].append(c)
            elif kind == "remove_bullet":
                p = _page(pages, op["page"])
                idx = op["bullet_index"]
                if 0 <= idx < len(p["claims"]):
                    del p["claims"][idx]
                else:
                    raise IndexError("bullet_index %d out of range" % idx)
            elif kind == "add_note":
                p = _page(pages, op["page"])
                p["notes"].append(op["note"])
            elif kind == "reorder_pages":
                order = list(map(int, op["order"]))
                if sorted(order) == list(range(1, len(pages) + 1)):
                    pages = sorted(pages, key=lambda d: order.index(int(d["index"])))
                    for i, p in enumerate(pages, start=1):
                        p["index"] = i
                else:
                    raise ValueError("order must be a permutation of 1..%d" % len(pages))
            elif kind == "set_figure":
                p = _page(pages, op["page"])
                p["figure"] = {"ref": op.get("ref", ""),
                               "kind": op.get("kind", "none"),
                               "table_id": op.get("table_id", ""),
                               "image": op.get("image", ""),
                               "note": op.get("note", "")}
            else:
                skipped.append({"op": kind, "reason": "未知操作"})
                continue
            applied.append(kind)
            changelog.append({"version": version, "op": kind, "page": op.get("page", ""),
                              "target": op.get("bullet_index", ""),
                              "reason": op.get("reason", "") or edits.get("reason", "")})
        except (KeyError, IndexError, ValueError) as e:
            skipped.append({"op": kind, "reason": str(e)})
    return pages, applied, skipped


def _page(pages, index):
    for p in pages:
        if int(p["index"]) == int(index):
            return p
    raise KeyError("page %s not found" % index)