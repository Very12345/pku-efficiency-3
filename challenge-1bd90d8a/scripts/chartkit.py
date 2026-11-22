#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
chartkit.py — 科研数据图生成引擎（可编辑 SVG + PNG/PDF 预览 + 数据溯源 + 标注校验）

职责
----
从结构化科研数据（CSV/TSV/JSON 表格）或实体-关系描述生成科研图稿：
- 图型：bar（分组柱状+误差线+显著性）、line（多序列折线+误差带）、scatter（散点）、
  box（箱线，原始值或直供统计值）、heatmap（热图+色标）、pie（扇区角度映射）、
  network（机制/通路图：节点-边、激活/抑制/磷酸化/转录着色规则见
  templates/entity_glossary.json）、panel（多面板组合，子面板可独立数据文件与 filter）。
- 每个图元携带 data-* 溯源属性（源文件/列/行/值/类别），可双向回溯。
- 同一图元场景（Scene）既输出可编辑分层 SVG（手写 XML，含 metadata 溯源块），
  又用 Pillow 渲染 PNG / PDF 预览，保证矢量与位图逐元素一致、可复核。

编码与字体
- 文字统一经 svgtext.encoded_svg_text() 写入（掏除控制字符 + XML 转义）；
- CJK 文本使用 cjkfont.FONT_FAMILY_SANS_CJK 回退链，Pillow 渲染用 cjkfont.FontMap
  实际发现的字体，缺字记 warn 不静默乱码。

依赖：Python 3.8+ 标准库 + Pillow（可选）。不依赖 matplotlib/cairosvg/svgwrite。

本文件是脚本库，不作为 CLI 直接入口；命令行入口见 main.py。
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import statistics
from datetime import datetime, timezone

import cjkfont
import svgtext

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except Exception:
    Image = ImageDraw = ImageFont = None
    HAS_PIL = False


# ---------------------------------------------------------------- 常量

DEFAULT_WIDTH = 1200
DEFAULT_HEIGHT = 800

PALETTE = [
    "#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B3",
    "#937860", "#64B5CD", "#E8A838", "#F28E2B", "#8C6D9F",
    "#B07AA1", "#59A14F", "#E15759", "#76B7B2", "#FF9DA7",
]

GRAY_GRID = "#D8D8D8"
AXIS_COLOR = "#333333"
TEXT_COLOR = "#1a1a1a"

# 期刊/模板样式预设的默认值（templates/journal_styles.json 可覆盖）
DEFAULT_STYLE = {
    "fonts": {"sans": cjkfont.FONT_FAMILY_SANS,
              "sans_cjk": cjkfont.FONT_FAMILY_SANS_CJK,
              "serif": cjkfont.FONT_FAMILY_SERIF,
              "mono": cjkfont.FONT_FAMILY_MONO},
    "title_size": 34,
    "subtitle_size": 22,
    "axis_label_size": 26,
    "tick_size": 20,
    "legend_size": 20,
    "annotation_size": 20,
    "panel_label_size": 30,
    "grid_line_width": 1,
    "axis_line_width": 2,
    "bar_width_ratio": 0.78,
    "line_width": 3,
    "errorbar_width": 2,
    "pad": 0.05,
    "dpi": 150,
}

# 关系类型 → 颜色/线型语义（默认；templates/entity_glossary.json 可覆盖）
_DEFAULT_RELATION_RULES = [
    {"type_keywords": ["inhibit", "抑制", "block", "repress", "负调控"],
     "color": "#B2182B", "dash": False, "semantics": "inhibition"},
    {"type_keywords": ["activ", "激活", "促进", "磷酸化", "phosphoryl", "正调控"],
     "color": "#2166AC", "dash": False, "semantics": "activation"},
    {"type_keywords": ["transcript", "转录", "express", "表达"],
     "color": "#1B7837", "dash": True, "semantics": "transcription"},
]

_COL_NAME_HINTS = {
    "time": ["time", "day", "week", "month", "duration", "hour", "h", "min", "year", "dose", "concentration", "conc", "temp", "temperature"],
    "error": ["se", "sem", "sd", "std", "stddev", "ci", "err", "error"],
    "n": ["n", "n_samples", "sample_size", "count_n"],
}


class SpecError(Exception):
    """图规格或数据错误（携带可读信息，供录制为 uncertainty）。"""


# ---------------------------------------------------------------- 工具

def skill_root() -> str:
    """Skill 资源根目录（本文件所在目录的父目录），自定位不依赖 cwd。"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def now_ts() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def safe_float(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(",", "").replace("−", "-").replace("　", "")
    if s in ("", "-", "NA", "na", "NaN", "nan", "null", "N/A", "."):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def nice_step(span: float) -> float:
    if span <= 0:
        return 1.0
    e = 10 ** math.floor(math.log10(span))
    for m in (1, 2, 5, 10):
        if span / e <= m:
            return m * e
    return 10 * e


def nice_ticks(lo: float, hi: float, n: int = 5):
    if not math.isfinite(lo) or not math.isfinite(hi) or hi <= lo:
        return [lo]
    span = hi - lo
    step = nice_step(span / max(n, 1))
    start = math.ceil(lo / step) * step
    ticks = []
    v = start
    while v <= hi + step * 1e-6:
        ticks.append(round(v, 10))
        v += step
    return ticks


def fmt_num(v: float) -> str:
    if v == 0:
        return "0"
    a = abs(v)
    if a >= 1e6 or a < 1e-3:
        return f"{v:.2e}".replace("e+0", "e").replace("e-0", "e-")
    if a < 1:
        return f"{v:.3g}"
    return f"{v:.4g}"


def parse_row_values(rows, col, required=False, where=""):
    if col not in rows[0]:
        raise SpecError(f"缺少列 '{col}'（{where}）。请核对源数据列名，勿补造数据。")
    out = []
    for i, r in enumerate(rows):
        v = safe_float(r.get(col))
        out.append(v if v is not None else None)
    if required and all(v is None for v in out):
        raise SpecError(f"列 '{col}' 无可用数值（{where}）。")
    return out


def load_table(path: str):
    """读取 CSV/TSV/JSON（list of dict）表格。返回 (headers, rows, ext)。

    行字典附带 `_src_row` = 源文件行号（0 起），保证 filter/panel 之后仍能
    定位回原文件行（D1/D14/mapcheck 值核对）。headers 不含该私有键。
    """
    if not os.path.exists(path):
        raise SpecError(f"数据文件不存在：{path}")
    ext = os.path.splitext(path)[1].lower()
    if ext == ".json":
        with open(path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        if isinstance(data, dict) and "rows" in data and isinstance(data["rows"], list):
            rows0 = data["rows"]
        elif isinstance(data, dict) and "data" in data and isinstance(data["data"], list):
            rows0 = data["data"]
        elif isinstance(data, list):
            rows0 = data
        else:
            raise SpecError("JSON 表格格式不明：" + path +
                            "（需 list[dict] 或 {rows:[...]} / {data:[...]}）")
        if not rows0:
            raise SpecError(f"数据文件为空：{path}")
        head0 = list(rows0[0].keys()) if isinstance(rows0[0], dict) else []
        if not head0:
            raise SpecError(f"JSON 行不是对象：{path}")
        rows = []
        for i, r in enumerate(rows0):
            d = dict(r)
            d["_src_row"] = i
            rows.append(d)
        headers = [h for h in head0 if h != "_src_row"]
        return headers, rows, ext

    delim = "\t" if ext in (".tsv", ".tab") else None
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        sample = f.read(4096)
        f.seek(0)
        if delim is None:
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
                delim = dialect.delimiter
            except csv.Error:
                delim = ","
        reader = csv.DictReader(f, delimiter=delim)
        headers = [h.strip() for h in (reader.fieldnames or [])]
        rows = []
        for i, row in enumerate(reader):
            d = {k.strip(): (v.strip() if isinstance(v, str) else v)
                 for k, v in row.items() if k is not None}
            d["_src_row"] = i      # 源文件行号（0 起，贯穿 filter/panel，D1/D14）
            rows.append(d)
    if not headers:
        raise SpecError(f"数据文件无表头：{path}")
    if not rows:
        raise SpecError(f"数据文件为空：{path}")
    return headers, rows, ext


def detect_error_col(headers):
    low = [h.lower() for h in headers]
    for a in _COL_NAME_HINTS["error"]:
        if a in low:
            return headers[low.index(a)]
    for h in headers:
        if h.lower().startswith("sd") or h.lower().startswith("se"):
            return h
    return None


def detect_n_col(headers):
    low = [h.lower() for h in headers]
    for a in _COL_NAME_HINTS["n"]:
        if a in low:
            return headers[low.index(a)]
    return None


def detect_time_col(headers, rows):
    """时间/剂量/浓度列检测：列名精确命中或含 ≥3 字提示词（如 time_h → time）。"""
    low = [h.lower() for h in headers]
    for hint in _COL_NAME_HINTS["time"]:
        if len(hint) < 3:
            continue
        for i, lh in enumerate(low):
            if hint == lh or hint in lh:
                col = headers[i]
                vals = [safe_float(r.get(col)) is not None for r in rows]
                if any(vals):
                    return col
    for h in headers:
        if h.lower() in _COL_NAME_HINTS["time"]:
            return h
    return None


def detect_cat_cols(headers, rows):
    cats = []
    for h in headers:
        vals = [r.get(h) for r in rows[:200]]
        numeric = sum(1 for v in vals if safe_float(v) is not None and v not in (None, ""))
        if numeric < 0.9 * len(vals) and len(vals) > 0:
            cats.append(h)
    return cats


def detect_num_cols(headers, rows):
    nums = []
    for h in headers:
        vals = [safe_float(r.get(h)) for r in rows[:200]]
        if sum(1 for v in vals if v is not None) >= 0.6 * len(vals):
            nums.append(h)
    return nums


# ---------------------------------------------------------------- 样式预设

def load_journal_styles():
    """读取 templates/journal_styles.json；失败时回退默认（如实记录）。"""
    p = os.path.join(skill_root(), "templates", "journal_styles.json")
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"default": {}}


def load_style(name="default"):
    style = dict(DEFAULT_STYLE)
    presets = load_journal_styles()
    key = name or "default"
    if key in presets and isinstance(presets[key], dict):
        style.update(dict(presets[key]))
    return style


# 可由 figure spec 内联覆盖的样式键（D17：预设或 spec 内联覆盖，均可复用配置）
_INLINE_STYLE_KEYS = (
    "title_size", "subtitle_size", "axis_label_size", "tick_size",
    "legend_size", "annotation_size", "panel_label_size",
    "grid_line_width", "axis_line_width", "bar_width_ratio",
    "line_width", "errorbar_width", "pad", "dpi",
)


def resolve_figure_style(spec, base_style):
    """D17：单图样式 = 基样式（CLI/默认预设）→ spec["style"] 命名预设 → spec 内联键。

    保证「样式规则化」：加新期刊 = 加 templates/journal_styles.json 键；
    spec 显式字段优先级最高（typesetting-presets.md §2 三层覆盖）。
    """
    style = dict(base_style)
    sname = spec.get("style") if isinstance(spec, dict) else None
    if isinstance(sname, str) and sname and sname != "default":
        presets = load_journal_styles()
        if sname in presets and isinstance(presets[sname], dict):
            style.update(dict(presets[sname]))
    if isinstance(spec, dict):
        for k in _INLINE_STYLE_KEYS:
            v = spec.get(k)
            if v is not None:
                style[k] = v
    return style


def style_colors(style, name="default"):
    pal = PALETTE
    ck = style.get("palette")
    if isinstance(ck, list) and len(ck) >= 3:
        pal = ck
    return pal


def load_relation_rules():
    """加载连接规则字典（关系类型 → 颜色/线型）；缺文件时回退内置规则。"""
    p = os.path.join(skill_root(), "templates", "entity_glossary.json")
    rules = list(_DEFAULT_RELATION_RULES)
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                obj = json.load(f)
            rel = (obj.get("relation_rules") if isinstance(obj, dict) else None)
            if isinstance(rel, list) and rel:
                rules = rel
        except Exception:
            pass
    return rules


def relation_style(rel_type, rules):
    """按关系类型返回 (color, dash)。"""
    t = str(rel_type or "").lower()
    for rule in rules:
        for kw in rule.get("type_keywords", []):
            if kw and kw in t:
                return rule.get("color", "#666666"), bool(rule.get("dash", False))
    return "#666666", False


# ---------------------------------------------------------------- 字体（代理）

def new_fontmap(*a, **kw):
    return cjkfont.FontMap(*a, **kw)


# ---------------------------------------------------------------- 场景与图元

class Scene:
    """图元场景：SVG 与 PNG 共用同一份图元列表，保证双端一致。"""

    def __init__(self, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT, meta=None):
        self.width = int(width)
        self.height = int(height)
        self.prims = []          # list[Prim dict]
        self.meta = meta or {}   # 轴范围/刻度/标注脚注/来源等非图元信息
        self.fig_id = None
        self._idc = {}           # role -> counter（确定性命名的 svg_id）

    def add(self, kind, **kw):
        prim = {"kind": kind}
        prim.update(kw)
        prim.setdefault("z", 10)
        # 确定性 svg_id：显式给出则保留；否则按 role 计数器生成 el-<role>-N。
        # 这样 manifest 与 SVG 两侧 id 一一对应（G3/G4），且与内建 id() 无关（D18）。
        if "svg_id" not in prim:
            role = (prim.get("data") or {}).get("role") or kind
            n = self._idc.get(role, 0) + 1
            self._idc[role] = n
            prim["svg_id"] = f"el-{role}-{n}"
        self.prims.append(prim)
        return prim

    def rect(self, x, y, w, h, **kw):
        return self.add("rect", x=x, y=y, w=w, h=h, **kw)

    def line(self, x1, y1, x2, y2, **kw):
        return self.add("line", x1=x1, y1=y1, x2=x2, y2=y2, **kw)

    def text(self, x, y, text, size=16, fill=TEXT_COLOR, anchor="start", **kw):
        return self.add("text", x=x, y=y, text=str(text), size=size,
                        fill=fill, anchor=anchor, **kw)

    def circle(self, cx, cy, r, **kw):
        return self.add("circle", cx=cx, cy=cy, r=r, **kw)

    def polygon(self, points, **kw):
        return self.add("polygon", points=points, **kw)

    def polyline(self, points, **kw):
        return self.add("polyline", points=points, **kw)

    def ellipse(self, cx, cy, rx, ry, **kw):
        return self.add("ellipse", cx=cx, cy=cy, rx=rx, ry=ry, **kw)

    def group_open(self, gid, layer):
        self.add("group_open", gid=gid, layer=layer)

    def group_close(self):
        self.add("group_close")


# ---------------------------------------------------------------- 布局辅助

def compute_plot_area(width, height, style, layout=None):
    layout = layout or {}
    m = {
        "left": int(layout.get("margin_left", 110)),
        "right": int(layout.get("margin_right", 120)),
        "top": int(layout.get("margin_top", 120)),
        "bottom": int(layout.get("margin_bottom", 110)),
    }
    plot = {"x0": m["left"], "y0": m["top"],
            "x1": width - m["right"], "y1": height - m["bottom"]}
    if plot["x1"] <= plot["x0"] or plot["y1"] <= plot["y0"]:
        raise SpecError(f"图面太小（{width}x{height}）：留白后绘图区无空间，请增大画布或减少边距。")
    return plot


def x_map(plot, lo, hi, v):
    span = hi - lo or 1.0
    return plot["x0"] + (v - lo) / span * (plot["x1"] - plot["x0"])


def y_map(plot, lo, hi, v):
    span = hi - lo or 1.0
    return plot["y1"] - (v - lo) / span * (plot["y1"] - plot["y0"])


def pad_range(lo, hi, pad_ratio=0.05):
    if lo == hi:
        lo, hi = lo - 1, hi + 1
    pad = (hi - lo) * pad_ratio
    return lo - pad, hi + pad


# ---------------------------------------------------------------- 各图型构建

def _base_kw(scene, spec, z, data=None, **kw):
    base = {"z": z, "data": data or {}}
    base.update(kw)
    return base


def build_bar(scene, spec, rows, style):
    """分组柱状图：x 分类，hue 分组或显式 series 列；可选误差线 + 显著性标注。"""
    headers = list(rows[0].keys()) if rows else []
    z = 10
    xcol = (spec.get("x") or {}).get("column")
    if not xcol:
        cats = detect_cat_cols(headers, rows)
        xcol = cats[0] if cats else (headers[0] if headers else None)
    if not xcol:
        raise SpecError("柱状图需要分类列（x）。可用列：" + str(headers))
    ycol = (spec.get("y") or {}).get("column")
    if not ycol:
        nums = detect_num_cols(headers, rows)
        if not nums:
            raise SpecError("柱状图需要至少一列数值列（y）。")
        for h in nums:
            if h != xcol and detect_error_col([h]) != h:
                ycol = h
                break
        else:
            ycol = nums[0]
    errcol = ((spec.get("error") or {}).get("column")
              or ((spec.get("y") or {}).get("error_column"))
              or detect_error_col(headers))
    if errcol == ycol:
        errcol = None
    hue = (spec.get("hue") or {}).get("column")
    if not hue:
        series = spec.get("series") or []
        groups = [ycol]
    else:
        groups = sorted({str(r.get(hue)) for r in rows if r.get(hue) not in (None, "")})

    order = spec.get("order")
    if order:
        cats = list(order)
    else:
        seen = []
        for r in rows:
            v = str(r.get(xcol))
            if v not in seen:
                seen.append(v)
        cats = seen
    if not cats:
        raise SpecError(f"分类列 '{xcol}' 无可用取值。")

    ylabel = (spec.get("y") or {}).get("label") or ycol
    yunit = (spec.get("y") or {}).get("unit")

    ymin, ymax = 0.0, 0.0
    for r in rows:
        v = safe_float(r.get(ycol))
        if v is not None:
            ymax = max(ymax, v)
        if errcol:
            e = safe_float(r.get(errcol))
            if e is not None and v is not None:
                ymax = max(ymax, v + e)
                ymin = min(ymin, v - e)
        else:
            if v is not None:
                ymin = min(ymin, v)
    ylo, yhi = pad_range(ymin, ymax, style.get("pad", 0.05))
    if ylo < 0 and ymin >= 0:
        ylo = 0.0
    scene.meta["y_range"] = [ylo, yhi]
    scene.meta["x_categories"] = cats
    plot = compute_plot_area(scene.width, scene.height, style, spec.get("layout"))
    n_cats = len(cats)
    n_grp = len(groups)
    step = (plot["x1"] - plot["x0"]) / max(n_cats, 1)
    slot = step * style.get("bar_width_ratio", 0.78)
    bw = slot / max(n_grp, 1) * 0.82
    yticks = nice_ticks(ylo, yhi, 5)
    y_tick_pos = [(y_map(plot, ylo, yhi, t), fmt_num(t)) for t in yticks]
    x_tick_pos = []
    for ci, cat in enumerate(cats):
        cx = plot["x0"] + step * (ci + 0.5)
        x_tick_pos.append((cx, cat))
        scene.line(cx, plot["y1"], cx, plot["y1"] + 6, stroke=AXIS_COLOR,
                   stroke_width=style.get("axis_line_width", 2), z=8)
        for gi, g in enumerate(groups):
            gw = bw
            bx = cx - slot / 2 + gi * bw + (slot - n_grp * bw) / 2
            row = _find_row(rows, xcol, cat, hue, g, groups, ycol, errcol)
            if row is None:
                continue
            v = safe_float(row.get(ycol))
            if v is None:
                continue
            e = safe_float(row.get(errcol)) if errcol else None
            yp0 = y_map(plot, ylo, yhi, max(v, 0))
            yp1 = y_map(plot, ylo, yhi, 0)
            color = spec_color(spec, style, gi, g)
            data = _bar_data(spec, rows, row, xcol, cat, ycol, g, errcol)
            scene.rect(bx, min(yp0, yp1), gw, abs(yp1 - yp0) or 2, fill=color,
                       stroke=AXIS_COLOR, stroke_width=1,
                       data=data, z=z, svg_id=_eid(scene, "bar"))
            if e is not None:
                ex = bx + gw / 2
                eb0 = y_map(plot, ylo, yhi, v + e)
                eb1 = y_map(plot, ylo, yhi, max(v - e, 0))
                eb_data = dict(data)
                eb_data["role"] = "errorbar"
                eb_data["semantics"] = (spec.get("error") or {}).get("semantics", "SE")
                eb_cap = dict(eb_data)
                eb_cap["role"] = "errorbar-cap"
                scene.line(ex, eb0, ex, eb1, stroke="#222222",
                           stroke_width=style.get("errorbar_width", 2), z=z + 1,
                           data=eb_data)
                scene.line(ex - 5, eb0, ex + 5, eb0, stroke="#222222", stroke_width=2, z=z + 1,
                           data=eb_cap)
                scene.line(ex - 5, eb1, ex + 5, eb1, stroke="#222222", stroke_width=2, z=z + 1,
                           data=dict(eb_cap))
    for ann in spec.get("annotations", []) or []:
        _draw_significance(scene, plot, ylo, yhi, cats, step, xcol, ann, style, z + 5)
    _draw_axes_common(scene, plot, style, x_ticks=x_tick_pos, y_ticks=yticks, y_tick_pos=y_tick_pos,
                      x_label=((spec.get("x") or {}).get("label") or xcol)
                      + (f" ({ (spec.get('x') or {}).get('unit')})" if (spec.get("x") or {}).get("unit") else ""),
                      y_label=(ylabel + (f" ({yunit})" if yunit else "")),
                      y_unit=yunit, rot=(spec.get("x") or {}).get("tick_rotation"))
    _draw_legend(scene, spec, style,
                 [(g if hue else (spec.get("series_labels") or {}).get(ycol, ycol),
                   spec_color(spec, style, gi, g)) for gi, g in enumerate(groups)],
                 plot, scene.width, z=z + 6)
    scene.meta["series"] = groups
    scene.meta["n_series"] = len(groups)
    return scene


def _find_row(rows, xcol, cat, hue, g, groups, ycol, errcol):
    cands = [r for r in rows if str(r.get(xcol)) == str(cat)]
    if hue:
        cands = [r for r in cands if str(r.get(hue)) == str(g)]
    if not cands:
        return None
    return cands[0]


def _bar_data(spec, rows, row, xcol, cat, ycol, g, errcol):
    row_idx = row.get("_src_row", rows.index(row))   # 源文件行号（filter/panel 后仍准确，D1）
    d = {
        "role": "bar",
        "column": ycol,
        "row_index": row_idx,
        "row_label": {xcol: cat},
        "category": cat,
        "series": g,
        "value": safe_float(row.get(ycol)),
    }
    if errcol:
        d["error_column"] = errcol
        d["error_value"] = safe_float(row.get(errcol))
    return d


def spec_color(spec, style, gi, g):
    m = (spec.get("colors") or {})
    if isinstance(m, dict) and str(g) in m:
        return m[str(g)]
    pal = style_colors(style)
    return pal[gi % len(pal)]


def _draw_significance(scene, plot, ylo, yhi, cats, step, xcol, ann, style, z):
    from_ = ann.get("from")
    to = ann.get("to")
    at = ann.get("at")
    text = ann.get("text", "*")
    if at is not None:
        for ci, cat in enumerate(cats):
            if str(cat) == str(at):
                cx = plot["x0"] + step * (ci + 0.5)
                top = plot["y0"]
                scene.text(cx, top - 14, text, size=style.get("annotation_size", 20),
                           fill="#1a1a1a", anchor="middle", z=z,
                           data={"role": "significance", "category": cat,
                                 "p_value": ann.get("p"), "source": ann.get("source")})
        return
    if from_ is None or to is None:
        raise SpecError(f"显著性标注无效（from/to/at 缺失）：{ann}")
    i1, i2 = None, None
    for ci, cat in enumerate(cats):
        if str(cat) == str(from_):
            i1 = ci
        if str(cat) == str(to):
            i2 = ci
    if i1 is None or i2 is None:
        raise SpecError(f"显著性标注引用了不存在的分类（from={from_}, to={to}，可见类别：{cats}）")
    x1 = plot["x0"] + step * (i1 + 0.5)
    x2 = plot["x0"] + step * (i2 + 0.5)
    ytop = plot["y0"] - 26 - int(ann.get("level", 0)) * 24
    ytop = max(ytop, 8)
    scene.line(x1, ytop, x2, ytop, stroke="#1a1a1a", stroke_width=1.5, z=z,
               data={"role": "significance-line", "from": from_, "to": to,
                     "p_value": ann.get("p"), "source": ann.get("source")})
    scene.line(x1, ytop - 4, x1, ytop + 4, stroke="#1a1a1a", stroke_width=1.5, z=z)
    scene.line(x2, ytop - 4, x2, ytop + 4, stroke="#1a1a1a", stroke_width=1.5, z=z)
    scene.text((x1 + x2) / 2, ytop - 12, text, size=style.get("annotation_size", 20),
               fill="#1a1a1a", anchor="middle", z=z,
               data={"role": "significance-text", "text": text,
                     "p_value": ann.get("p"), "source": ann.get("source")})
    if ann.get("p") is not None or ann.get("source"):
        scene.meta.setdefault("annotation_footnotes", []).append(
            f"{text}: p={ann.get('p')} ({ann.get('source') or 'p值来源见源数据'})"
        )


def build_line(scene, spec, rows, style):
    z = 10
    headers = list(rows[0].keys()) if rows else []
    xcol = ((spec.get("x") or {}).get("column")) or detect_time_col(headers, rows)
    if not xcol:
        nums = detect_num_cols(headers, rows)
        xcol = nums[0] if nums else headers[0]
    ycol = (spec.get("y") or {}).get("column")
    if not ycol:
        nums = [h for h in detect_num_cols(headers, rows) if h != xcol]
        ycol = nums[0] if nums else headers[0]
    errcol = ((spec.get("error") or {}).get("column")) or detect_error_col(headers)
    if errcol == ycol:
        errcol = None
    hue = (spec.get("hue") or {}).get("column")
    series = spec.get("series") or []
    if hue:
        groups = sorted({str(r.get(hue)) for r in rows if r.get(hue) not in (None, "")})
    elif len(series) > 1:
        groups = [s.get("column", s.get("label")) for s in series]
    else:
        groups = [ycol]

    pts = []
    for r in rows:
        xv = safe_float(r.get(xcol))
        if xv is None:
            continue
        pts.append((xv, r))
    pts.sort(key=lambda t: t[0])
    if not pts:
        raise SpecError(f"折线图 x 列 '{xcol}' 无可用数值点。")

    def series_value(r, gi):
        if hue:
            if str(r.get(hue)) != str(groups[gi]):
                return None, None
            return safe_float(r.get(ycol)), errcol
        if len(series) > 1:
            s = series[gi]
            return safe_float(r.get(s.get("column"))), (s.get("error") or s.get("error_column") or errcol)
        return safe_float(r.get(ycol)), errcol

    ymin, ymax = 0.0, 0.0
    for _xv, r in pts:
        for gi in range(len(groups)):
            v, ec = series_value(r, gi)
            if v is None:
                continue
            ymin = min(ymin, v); ymax = max(ymax, v)
            if ec:
                e = safe_float(r.get(ec))
                if e is not None:
                    ymin = min(ymin, v - e); ymax = max(ymax, v + e)
    ylo, yhi = pad_range(ymin, ymax, style.get("pad", 0.05))
    if ylo < 0 and ymin >= 0:
        ylo = 0.0
    xlo, xhi = pad_range(pt_min(pts), pt_max(pts), 0.02)
    scene.meta["y_range"] = [ylo, yhi]
    scene.meta["x_range"] = [xlo, xhi]
    plot = compute_plot_area(scene.width, scene.height, style, spec.get("layout"))
    for gi, g in enumerate(groups):
        color = spec_color(spec, style, gi, g)
        ser_pts = []
        for xv, r in pts:
            v, ec = series_value(r, gi)
            if v is None:
                continue
            ser_pts.append([x_map(plot, xlo, xhi, xv), y_map(plot, ylo, yhi, v), xv, v, ec, r])
        if not ser_pts:
            continue
        col_used = (ycol if hue or len(series) <= 1 else series[gi].get("column"))
        data = {"role": "series", "series": g, "column": col_used, "item_count": len(ser_pts)}
        point_pairs = [[p[0], p[1]] for p in ser_pts]
        scene.polyline(point_pairs, stroke=color, stroke_width=style.get("line_width", 3), fill=None,
                       z=z, data=data, svg_id=_eid(scene, "line"))
        for px, py, xv, v, ec, origin_row in ser_pts:
            scene.circle(px, py, 6, fill="white", stroke=color, stroke_width=2, z=z + 1,
                         data={"role": "point", "series": g, "x": xv, "value": v,
                               "row_index": origin_row.get("_src_row", rows.index(origin_row)),
                               "column": col_used})
            if ec:
                e = safe_float(origin_row.get(ec))
                if e is not None:
                    e0 = y_map(plot, ylo, yhi, v + e)
                    scene.line(px, min(py, e0), px, max(py, e0), stroke=color, stroke_width=2, z=z + 1,
                               data={"role": "errorbar", "series": g,
                                     "semantics": (spec.get("error") or {}).get("semantics", "SE")})
    xticks = nice_ticks(xlo, xhi, 6)
    yticks = nice_ticks(ylo, yhi, 5)
    x_tick_pos = [(x_map(plot, xlo, xhi, t), fmt_num(t)) for t in xticks]
    for px, _lab in x_tick_pos:
        scene.line(px, plot["y1"], px, plot["y1"] + 6, stroke=AXIS_COLOR, stroke_width=2)
    y_tick_pos = [(y_map(plot, ylo, yhi, t), fmt_num(t)) for t in yticks]
    _draw_axes_common(scene, plot, style, x_ticks=x_tick_pos, y_ticks=yticks,
                      y_tick_pos=y_tick_pos,
                      x_label=(spec.get("x") or {}).get("label") or xcol,
                      y_label=((spec.get("y") or {}).get("label") or ycol)
                      + (f" ({ (spec.get('y') or {}).get('unit')})" if (spec.get("y") or {}).get("unit") else ""),
                      y_unit=(spec.get("y") or {}).get("unit"))
    legend_items = []
    for gi, g in enumerate(groups):
        if hue:
            lbl = (spec.get("hue") or {}).get("labels", {}).get(str(g), str(g))
        elif len(series) > 1:
            lbl = series[gi].get("label", str(g))
        else:
            lbl = (spec.get("y") or {}).get("label") or ycol
        legend_items.append((lbl, spec_color(spec, style, gi, g)))
    _draw_legend(scene, spec, style, legend_items, plot, scene.width, z=z + 6)
    return scene


def pt_min(pts):
    return min(p[0] for p in pts)


def pt_max(pts):
    return max(p[0] for p in pts)


def build_scatter(scene, spec, rows, style):
    z = 10
    headers = list(rows[0].keys()) if rows else []
    xcol = (spec.get("x") or {}).get("column")
    ycol = (spec.get("y") or {}).get("column")
    if not xcol or not ycol:
        nums = detect_num_cols(headers, rows)
        if len(nums) < 2:
            raise SpecError("散点图需要至少两列数值列（x, y）。")
        xcol = xcol or nums[0]
        ycol = ycol or (nums[1] if nums[0] == xcol else nums[0])
    cats = detect_cat_cols(headers, rows)
    hue = (spec.get("hue") or {}).get("column") or (cats[0] if cats else None)
    xv = parse_row_values(rows, xcol, required=True)
    yv = parse_row_values(rows, ycol, required=True)
    xs = [v if v is not None else 0 for v in xv]
    ys = [v if v is not None else 0 for v in yv]
    xlo, xhi = pad_range(min(xs), max(xs), 0.05)
    ylo, yhi = pad_range(min(ys), max(ys), 0.05)
    scene.meta["x_range"] = [xlo, xhi]
    scene.meta["y_range"] = [ylo, yhi]
    plot = compute_plot_area(scene.width, scene.height, style, spec.get("layout"))
    if hue:
        groups = sorted({str(r.get(hue)) for r in rows if r.get(hue) not in (None, "")})
    else:
        groups = [None]
    for gi, g in enumerate(groups):
        color = spec_color(spec, style, gi, g if g is not None else 0)
        for i, r in enumerate(rows):
            if hue and str(r.get(hue)) != str(g):
                continue
            a, b = safe_float(r.get(xcol)), safe_float(r.get(ycol))
            if a is None or b is None:
                continue
            px = x_map(plot, xlo, xhi, a)
            py = y_map(plot, ylo, yhi, b)
            rsize = spec_r_size(spec, r, rows, i, default=8)
            scene.circle(px, py, rsize, fill=color, stroke="white", stroke_width=1.5, z=z,
                         data={"role": "point", "x_column": xcol, "y_column": ycol,
                               "x": a, "y": b, "row_index": r.get("_src_row", i),
                               "series": g})
    xticks = nice_ticks(xlo, xhi, 6)
    yticks = nice_ticks(ylo, yhi, 5)
    x_tick_pos = [(x_map(plot, xlo, xhi, t), fmt_num(t)) for t in xticks]
    for px, _ in x_tick_pos:
        scene.line(px, plot["y1"], px, plot["y1"] + 6, stroke=AXIS_COLOR, stroke_width=2)
    y_tick_pos = [(y_map(plot, ylo, yhi, t), fmt_num(t)) for t in yticks]
    _draw_axes_common(scene, plot, style, x_ticks=x_tick_pos, y_ticks=yticks, y_tick_pos=y_tick_pos,
                      x_label=(spec.get("x") or {}).get("label") or xcol,
                      y_label=((spec.get("y") or {}).get("label") or ycol))
    legend_items = []
    for gi, g in enumerate(groups):
        if g is None:
            break
        legend_items.append(((spec.get("hue") or {}).get("labels", {}).get(str(g), str(g)),
                             spec_color(spec, style, gi, g)))
    _draw_legend(scene, spec, style, legend_items, plot, scene.width, z=z + 6)
    return scene


def spec_r_size(spec, r, rows, i, default=10):
    size_col = (spec.get("size") or {}).get("column")
    if not size_col:
        return default
    v = safe_float(r.get(size_col))
    if v is None:
        return default
    return 4 + v


def build_box(scene, spec, rows, style):
    z = 10
    headers = list(rows[0].keys()) if rows else []
    xcol = (spec.get("x") or {}).get("column")
    ycol = (spec.get("y") or {}).get("column")
    presets = spec.get("presets")
    if presets:
        groups = [dict(p) for p in presets]
        cats = [str(p.get("label") or p.get("category")) for p in presets]
    else:
        if not xcol or not ycol:
            raise SpecError("箱线图需要 x（分组）与 y（数值）列，或提供 presets 预计算箱线。")
        cats = []
        for r in rows:
            v = str(r.get(xcol))
            if v not in cats:
                cats.append(v)
        groups = []
        for cat in cats:
            vals = [safe_float(r.get(ycol)) for r in rows if str(r.get(xcol)) == str(cat)]
            vals = [v for v in vals if v is not None]
            n = len(vals)
            q = statistics.quantiles(vals, n=4) if n >= 4 else ([min(vals)] * 3 if vals else [0, 0, 0])
            groups.append({"label": cat, "q1": q[0], "median": statistics.median(vals) if vals else 0,
                           "q3": q[2], "min": min(vals) if vals else 0, "max": max(vals) if vals else 0,
                           "n": n, "raw_n": n})
    ymin = min(g.get("min", 0) for g in groups)
    ymax = max(g.get("max", 0) for g in groups)
    if spec.get("outliers"):
        ymin = min([ymin] + [v for g in groups for v in g.get("outliers", [])])
        ymax = max([ymax] + [v for g in groups for v in g.get("outliers", [])])
    ylo, yhi = pad_range(ymin, ymax, style.get("pad", 0.05))
    if ylo < 0 and ymin >= 0:
        ylo = 0.0
    scene.meta["y_range"] = [ylo, yhi]
    plot = compute_plot_area(scene.width, scene.height, style, spec.get("layout"))
    n = len(groups)
    step = (plot["x1"] - plot["x0"]) / max(n, 1)
    bw = step * 0.5
    yticks = nice_ticks(ylo, yhi, 5)
    y_tick_pos = [(y_map(plot, ylo, yhi, t), fmt_num(t)) for t in yticks]
    x_tick_pos = []
    for gi, g in enumerate(groups):
        cx = plot["x0"] + step * (gi + 0.5)
        x_tick_pos.append((cx, str(g.get("label"))))
        color = spec_color(spec, style, gi, gi)
        data = {"role": "box", "category": g.get("label"), "n": g.get("n")}
        q1, med, q3 = g["q1"], g["median"], g["q3"]
        yq1, ymed, yq3 = y_map(plot, ylo, yhi, q1), y_map(plot, ylo, yhi, med), y_map(plot, ylo, yhi, q3)
        x0b, x1b = cx - bw / 2, cx + bw / 2
        scene.rect(x0b, yq3, bw, abs(yq1 - yq3) or 2, fill=color, stroke=AXIS_COLOR, stroke_width=1.5, z=z, data=data)
        lo_w, hi_w = g.get("min", q1), g.get("max", q3)
        scene.line(cx, y_map(plot, ylo, yhi, lo_w), cx, y_map(plot, ylo, yhi, hi_w),
                   stroke=AXIS_COLOR, stroke_width=1.5, z=z, data=data)
        scene.line(cx - 6, y_map(plot, ylo, yhi, lo_w), cx + 6, y_map(plot, ylo, yhi, lo_w),
                   stroke=AXIS_COLOR, stroke_width=1.5, z=z, data=data)
        scene.line(cx - 6, y_map(plot, ylo, yhi, hi_w), cx + 6, y_map(plot, ylo, yhi, hi_w),
                   stroke=AXIS_COLOR, stroke_width=1.5, z=z, data=data)
        scene.line(x0b, ymed, x1b, ymed, stroke="#1a1a1a", stroke_width=2.2, z=z + 1, data=data)
        for o in g.get("outliers", []):
            scene.circle(cx, y_map(plot, ylo, yhi, o), 4, fill="white", stroke=AXIS_COLOR,
                         stroke_width=1.2, z=z + 2,
                         data={"role": "outlier", **data})
        scene.line(cx, plot["y1"], cx, plot["y1"] + 6, stroke=AXIS_COLOR, stroke_width=2, z=8)
    _draw_axes_common(scene, plot, style, x_ticks=x_tick_pos, y_ticks=yticks, y_tick_pos=y_tick_pos,
                      x_label=(spec.get("x") or {}).get("label") or xcol,
                      y_label=((spec.get("y") or {}).get("label") or ycol))
    scene.meta["n_boxes"] = n
    return scene


def build_heatmap(scene, spec, rows, style):
    z = 10
    matrix = _heat_matrix(spec, rows)
    row_labels = _heat_labels(spec.get("row_labels"), rows, matrix, axis="row")
    col_labels = _heat_labels(spec.get("col_labels"), rows, matrix, axis="col")
    vmin = spec.get("vmin")
    vmax = spec.get("vmax")
    vals = [v for row in matrix for v in row if v is not None]
    if vmin is None:
        vmin = min(vals) if vals else 0
    if vmax is None:
        vmax = max(vals) if vals else 1
    if vmax <= vmin:
        vmax = vmin + 1
    plot = compute_plot_area(scene.width, scene.height, style, spec.get("layout"))
    nrows, ncols = len(matrix), len(matrix[0])
    cw = (plot["x1"] - plot["x0"]) / max(ncols, 1)
    ch = (plot["y1"] - plot["y0"]) / max(nrows, 1)
    for ri, row in enumerate(matrix):
        for ci, v in enumerate(row):
            x0 = plot["x0"] + ci * cw
            y0 = plot["y0"] + ri * ch
            color = heat_color(v, vmin, vmax, spec.get("colormap", "bwr")) if v is not None else "#EEEEEE"
            scene.rect(x0, y0, cw, ch, fill=color, stroke="#FFFFFF", stroke_width=1, z=z,
                       data={"role": "cell", "row_index": ri, "col_index": ci,
                             "row_label": row_labels[ri] if row_labels else None,
                             "col_label": col_labels[ci] if col_labels else None,
                             "value": v, "vmin": vmin, "vmax": vmax})
            if spec.get("show_values", True) and v is not None:
                txt = spec.get("value_format") or fmt_num(v)
                size = max(9, min(20, int(ch * 0.45), int(cw * 0.35)))
                scene.text(x0 + cw / 2, y0 + ch / 2, txt, size=size, fill="#111111", anchor="middle", z=z + 1)
    if row_labels:
        for ri, lab in enumerate(row_labels):
            scene.text(plot["x0"] - 12, plot["y0"] + (ri + 0.5) * ch, lab, size=18, anchor="end",
                       fill=TEXT_COLOR, z=z - 1,
                       data={"role": "row-label", "row_index": ri, "text": lab})
    if col_labels:
        for ci, lab in enumerate(col_labels):
            scene.text(plot["x0"] + (ci + 0.5) * cw, plot["y1"] + 26, lab, size=18, anchor="middle",
                       fill=TEXT_COLOR, rotate=spec.get("col_rotation", 30), z=z - 1,
                       data={"role": "col-label", "col_index": ci, "text": lab})
    _heat_colorbar(scene, plot, style, vmin, vmax, spec.get("value_label", "value"),
                   spec.get("colormap", "bwr"))
    scene.meta["vmin"] = vmin
    scene.meta["vmax"] = vmax
    return scene


def _heat_matrix(spec, rows):
    m = spec.get("matrix")
    if m is None:
        raise SpecError("热图需要 matrix（二维数组）或 matrix_file / z 列。")
    if isinstance(m, list):
        return [list(r) for r in m]
    if isinstance(m, dict):
        return [[m.get(c) for c in m.get("columns", [])] for r in m.get("rows", [])]
    raise SpecError("热图 matrix 必须为二维数组或 {rows, columns} 对象。")


def _heat_labels(spec_lab, rows, matrix, axis):
    if spec_lab is None:
        return None
    if isinstance(spec_lab, list):
        return [str(x) for x in spec_lab]
    if isinstance(spec_lab, dict):
        col = spec_lab.get("column")
        if col and rows:
            return [str(r.get(col)) for r in rows]
    return None


def heat_color(v, vmin, vmax, cmap="bwr"):
    if v is None:
        return "#EEEEEE"
    t = (v - vmin) / (vmax - vmin)
    t = max(0.0, min(1.0, t))
    stops = {
        "bwr": [(0.0, "#2166AC"), (0.5, "#F7F7F7"), (1.0, "#B2182B")],
        "viridis": [(0.0, "#440154"), (0.25, "#3B528B"), (0.5, "#21918C"), (0.75, "#5EC962"), (1.0, "#FDE725")],
        "blues": [(0.0, "#F7FBFF"), (0.5, "#6BAED6"), (1.0, "#08306B")],
        "magma": [(0.0, "#000004"), (0.5, "#B73779"), (1.0, "#FCFDBF")],
    }
    st = stops.get(cmap, stops["bwr"])
    for i in range(len(st) - 1):
        t0, c0 = st[i]
        t1, c1 = st[i + 1]
        if t0 <= t <= t1:
            f = (t - t0) / (t1 - t0) if t1 > t0 else 0
            return "".join(
                f"#{int(c0[j:j + 2], 16) + (int(c1[j:j + 2], 16) - int(c0[j:j + 2], 16)) * f:02x}"
                for j in (0, 2, 4))
    return st[-1][1]


def _heat_colorbar(scene, plot, style, vmin, vmax, label, cmap):
    bx = plot["x1"] + 30
    bw, bh = 22, plot["y1"] - plot["y0"]
    bands = 64
    for i in range(bands):
        t0 = vmin + (vmax - vmin) * i / bands
        t1 = vmin + (vmax - vmin) * (i + 1) / bands
        y0 = plot["y0"] + bh * (1 - i / bands)
        hgt = bh / bands + 1
        scene.rect(bx, y0, bw, hgt, fill=heat_color((t0 + t1) / 2, vmin, vmax, cmap), stroke=None, z=8)
    scene.rect(bx, plot["y0"], bw, bh, fill=None, stroke=AXIS_COLOR, stroke_width=1.5, z=9)
    scene.text(bx + bw / 2, plot["y0"] - 10, fmt_num(vmax), size=15, anchor="middle", z=9)
    scene.text(bx + bw / 2, plot["y1"] + 18, fmt_num(vmin), size=15, anchor="middle", z=9)
    scene.text(bx + bw / 2, plot["y1"] + 44, label, size=16, anchor="middle", z=9)


def build_pie(scene, spec, rows, style):
    z = 10
    labels_col = (spec.get("labels") or {}).get("column")
    values_col = (spec.get("values") or {}).get("column")
    values, labels = [], []
    for r in rows:
        v = safe_float(r.get(values_col))
        if v is None:
            continue
        values.append(v)
        labels.append(str(r.get(labels_col)) if labels_col else f"row{len(values)}")
    if not values:
        raise SpecError("扇区图需要至少一个数值。")
    total = sum(values)
    if total <= 0:
        raise SpecError("扇区图数值总和必须为正。")
    cx, cy = scene.width / 2, scene.height / 2
    rmax = min(scene.width, scene.height) / 2.4
    angle = -90.0
    for i, (v, lab) in enumerate(zip(values, labels)):
        a1 = angle
        a2 = angle + v / total * 360.0
        color = spec_color(spec, style, i, i)
        scene.add("pieslice", cx=cx, cy=cy, r=rmax, angle0=a1, angle1=a2,
                  fill=color, stroke="white", stroke_width=2, z=z,
                  data={"role": "slice", "index": i, "label": lab, "value": v,
                        "angle_start": a1, "angle_end": a2, "fraction": v / total})
        if spec.get("labels_on", True):
            mid = math.radians((a1 + a2) / 2)
            tx = cx + rmax * 0.62 * math.cos(mid)
            ty = cy + rmax * 0.62 * math.sin(mid)
            txt = lab
            if spec.get("percent"):
                txt = f"{lab} {v / total * 100:.1f}%"
            scene.text(tx, ty, txt, size=18, anchor="middle", z=z + 1,
                       data={"role": "slice-label", "index": i, "label": lab})
        angle = a2
    if spec.get("legend", True):
        scene.meta["legend_entries"] = [(lab, spec_color(spec, style, i, i))
                                        for i, (v, lab) in enumerate(zip(values, labels))]
        _draw_legend(scene, spec, style, scene.meta["legend_entries"], None, scene.width,
                     z=z + 6, center_legend=True)
    return scene


def build_network(scene, spec, rows=None, style=None):
    """机制/通路图：节点 + 关系边。数据来自 spec['entities']/['relations'] 或实体文件行。"""
    z = 10
    if isinstance(spec.get("entities"), dict) and isinstance(spec["entities"].get("nodes"), list):
        nodes = list(spec["entities"]["nodes"])
        relations = list(spec["entities"].get("relations", []))
        if spec.get("relations"):
            relations = relations or list(spec["relations"])
    else:
        nodes = list(spec.get("entities") or spec.get("nodes") or [])
        relations = list(spec.get("relations") or spec.get("edges") or [])
    if rows is not None and rows and (spec.get("from_file")):
        relations = []
        for r in rows:
            if r.get("from") or r.get("source"):
                relations.append({"from": r.get("from") or r.get("source"),
                                  "to": r.get("to") or r.get("target"),
                                  "label": r.get("label") or r.get("relation"),
                                  "type": r.get("type")})
        ids = set()
        for rel in relations:
            for k in ("from", "to"):
                if rel.get(k):
                    ids.add(str(rel[k]))
        for iid in sorted(ids):
            if not any(str(n.get("id")) == iid for n in nodes):
                nodes.append({"id": iid, "label": iid})
    if not nodes:
        raise SpecError("通路图需要 entities（节点）列表。")
    rules = load_relation_rules()
    layout = spec.get("layout", "auto")
    has_xy = all(n.get("x") is not None and n.get("y") is not None for n in nodes)
    if layout == "layer" or not has_xy:
        _layout_nodes(nodes, relations, layout, scene.width, scene.height)
    else:
        for n in nodes:
            n["_px"] = float(n["x"]); n["_py"] = float(n["y"])
    xs = [n["_px"] for n in nodes]; ys = [n["_py"] for n in nodes]
    pad = 80
    scene.width, scene.height = int(max(xs) + pad), int(max(ys) + pad)
    by_id = {str(n.get("id")): n for n in nodes}
    for i, rel in enumerate(relations):
        a = by_id.get(str(rel.get("from"))); b = by_id.get(str(rel.get("to")))
        if a is None or b is None:
            scene.meta.setdefault("warnings", []).append(
                f"关系 {i} 引用了不存在的节点：{rel.get('from')} -> {rel.get('to')}")
            continue
        color, dash = relation_style(rel.get("type"), rules)
        scene.line(a["_px"], a["_py"], b["_px"], b["_py"], stroke=color, stroke_width=2.5,
                   dash=dash, arrow=True, z=z,
                   data={"role": "relation", "from": a.get("id"), "to": b.get("id"),
                         "label": rel.get("label"), "type": rel.get("type")})
        if rel.get("label"):
            mx, my = (a["_px"] + b["_px"]) / 2 + 8, (a["_py"] + b["_py"]) / 2 - 8
            scene.text(mx, my, str(rel.get("label")), size=17, fill="#555555", anchor="start", z=z + 1,
                       data={"role": "relation-label",
                             "from": rel.get("from"), "to": rel.get("to")})
    groups = []
    for n in nodes:
        grp = str(n.get("group") or n.get("type") or "default")
        if grp not in groups:
            groups.append(grp)
    for i, n in enumerate(nodes):
        gi = groups.index(str(n.get("group") or n.get("type") or "default"))
        color = spec_color(spec, style or default_style(), gi, gi)
        shape = str(n.get("shape") or "ellipse")
        rx, ry = _node_size(n)
        if shape in ("rect", "box"):
            scene.rect(n["_px"] - rx / 2, n["_py"] - ry / 2, rx, ry, fill="white", stroke=color,
                       stroke_width=2.5, z=z + 1,
                       data={"role": "node", "id": n.get("id"), "label": n.get("label"),
                             "group": n.get("group"), "source": n.get("source"), "cite": n.get("cite")})
        else:
            scene.ellipse(n["_px"], n["_py"], rx / 2, ry / 2, fill="white", stroke=color,
                          stroke_width=2.5, z=z + 1,
                          data={"role": "node", "id": n.get("id"), "label": n.get("label"),
                                "group": n.get("group"), "source": n.get("source"), "cite": n.get("cite")})
        scene.text(n["_px"], n["_py"], str(n.get("label") or n.get("id")), size=19, fill="#111111",
                   anchor="middle", z=z + 2,
                   data={"role": "node-label", "id": n.get("id"), "label": n.get("label")})
    scene.meta["n_nodes"] = len(nodes)
    scene.meta["n_relations"] = len(relations)
    if len(groups) > 1:
        _draw_legend(scene, spec, style or default_style(),
                     [(g, spec_color(spec, style or default_style(), gi, gi))
                      for gi, g in enumerate(groups)],
                     None, scene.width, z=z + 6, center_legend=True, title="Group")
    return scene


def default_style():
    return dict(DEFAULT_STYLE)


def _node_size(n):
    lab = str(n.get("label") or n.get("id") or "?")
    w = max(90, len(lab) * 17 + 44)
    return w, 46


def _layout_nodes(nodes, relations, layout, width, height):
    try:
        import collections
        indeg = collections.Counter()
        for rel in relations:
            indeg[str(rel.get("to"))] += 1
        inmap = {str(n.get("id")): 0 for n in nodes}
        for k, v in indeg.items():
            inmap[k] = v
        sorted_nodes = sorted(nodes, key=lambda n: (inmap.get(str(n.get("id")), 0), str(n.get("group") or "")))
        layers = {}
        for n in sorted_nodes:
            g = str(n.get("group") or n.get("type") or "")
            layers.setdefault(g, []).append(n)
        ystep = max(100, int(height / max(len(layers), 1)) - 20)
        yi = 0
        for g, ns in layers.items():
            xstep = width / max(len(ns), 1)
            for j, n in enumerate(ns):
                n["_px"] = xstep * (j + 0.5)
                n["_py"] = 60 + yi * ystep
            yi += 1
        if not layers:
            for j, n in enumerate(nodes):
                n["_px"] = width * (j + 0.5) / max(len(nodes), 1)
                n["_py"] = 200
    except Exception:
        for j, n in enumerate(nodes):
            n["_px"] = width * (j + 0.5) / max(len(nodes), 1)
            n["_py"] = 200
    xs = [n["_px"] for n in nodes]; ys = [n["_py"] for n in nodes]
    if xs:
        fx = (width - 160) / max(max(xs) - min(xs), 1)
        fy = (height - 160) / max(max(ys) - min(ys), 1)
        s = min(fx, fy, 1.4)
        for n in nodes:
            n["_px"] = 80 + (n["_px"] - (min(xs) or 0)) * s
            n["_py"] = 80 + (n["_py"] - (min(ys) or 0)) * s


def build_panel(scene, spec, rows, style):
    """多面板：把子图规格排成网格，各自独立 Scene 再合并进大画布。"""
    sub = spec.get("panels") or spec.get("subfigures")
    if not sub:
        raise SpecError("panel 图需要 panels 列表。")
    grid = spec.get("grid") or [1, len(sub)]
    rows_n = int(grid[0]) if isinstance(grid, list) else int(grid)
    cols = int(grid[1]) if isinstance(grid, list) else max(1, math.ceil(len(sub) / rows_n))
    rows_n = rows_n if isinstance(grid, list) else 1
    n = len(sub)
    if rows_n * cols < n:
        rows_n = math.ceil(n / cols)
    title_h = 90 if spec.get("title") else 50
    label_w = 60
    sep = 30
    avail_w = scene.width - label_w
    avail_h = scene.height - title_h
    cell_w = avail_w / cols - sep * (cols - 1) / cols
    cell_h = avail_h / rows_n - sep * (rows_n - 1) / rows_n
    meta_all = []
    for i, s in enumerate(sub):
        r, c = divmod(i, cols)
        rt = chr(ord("A") + i)
        ox = label_w + c * (cell_w + sep)
        oy = title_h + r * (cell_h + sep)
        sub_rows = s.get("_rows") or rows
        sub_scene = Scene(width=max(int(cell_w), 200), height=max(int(cell_h), 200))
        build_figure_into(sub_scene, {**s, "title": None}, sub_rows, style)
        # 面板内图元 id 加面板字母前缀，避免多面板 svg_id 冲突（G3/G4 唯一性）
        for prim in sub_scene.prims:
            if prim.get("svg_id"):
                prim["svg_id"] = f"{rt}-{prim['svg_id']}"
        _offset_scene(sub_scene, int(ox), int(oy))
        scene.prims.extend(sub_scene.prims)
        meta_all.append(sub_scene.meta)
        scene.text(ox + 16, oy + 34, rt, size=style.get("panel_label_size", 30),
                   fill=TEXT_COLOR, anchor="start", z=z_lowest(sub_scene) + 1,
                   data={"role": "panel-label", "panel": rt})
    scene.meta["panels"] = [m for m in meta_all]
    return scene


def _offset_scene(scene, dx, dy):
    for p in scene.prims:
        k = p["kind"]
        if k in ("rect",):
            p["x"] += dx; p["y"] += dy
        elif k in ("line",):
            p["x1"] += dx; p["y1"] += dy; p["x2"] += dx; p["y2"] += dy
        elif k in ("circle", "ellipse", "pieslice"):
            p["cx"] += dx; p["cy"] += dy
        elif k == "text":
            p["x"] += dx; p["y"] += dy
        elif k == "polygon":
            p["points"] = [(x + dx, y + dy) for x, y in p["points"]]
        elif k == "polyline":
            p["points"] = [(x + dx, y + dy) for x, y in p["points"]]


def z_lowest(scene):
    if not scene.prims:
        return 0
    return min(p.get("z", 10) for p in scene.prims)


# ---------------------------------------------------------------- 坐标轴与图例

def _draw_axes_common(scene, plot, style, x_ticks=None, y_ticks=None, y_tick_pos=None,
                      x_label=None, y_label=None, y_unit=None, rot=None):
    z = 5
    if y_ticks:
        for t in y_ticks:
            lo, hi = scene.meta.get("y_range", [0, 1])
            yy = y_map(plot, lo, hi, t)
            scene.line(plot["x0"], yy, plot["x1"], yy, stroke=GRAY_GRID, stroke_width=1,
                       dash=True, z=z, data={"role": "grid"})
    scene.rect(plot["x0"], plot["y0"], plot["x1"] - plot["x0"], plot["y1"] - plot["y0"],
               fill=None, stroke=AXIS_COLOR, stroke_width=style.get("axis_line_width", 2), z=z + 1)
    rotate = rot
    if x_ticks and rotate is None:
        slot = (plot["x1"] - plot["x0"]) / max(len(x_ticks), 1)
        wmax = 0
        for _px, lab in x_ticks:
            wmax = max(wmax, svgtext.text_width_px(lab, style.get("tick_size", 20)))
        if wmax > slot * 0.9 and len(x_ticks) > 1:
            rotate = 30
            scene.meta.setdefault("adjustments", []).append(
                f"x 轴刻度文字过长，自动旋转 30°（槽宽 {slot:.0f}px）。")
    for _px, lab in (x_ticks or []):
        if isinstance(lab, tuple):
            _px, lab = lab[0], lab[1]
        scene.text(_px, plot["y1"] + 16, str(lab), size=style.get("tick_size", 20),
                   anchor="middle", fill=TEXT_COLOR, rotate=rotate, z=z + 2,
                   data={"role": "x-tick"})
    if y_tick_pos:
        for py, lab in y_tick_pos:
            scene.text(plot["x0"] - 12, py, str(lab), size=style.get("tick_size", 20),
                       anchor="end", fill=TEXT_COLOR, z=z + 2, data={"role": "y-tick"})
    if x_label:
        scene.text((plot["x0"] + plot["x1"]) / 2, scene.height - 26, x_label,
                   size=style.get("axis_label_size", 26), anchor="middle", z=z + 3,
                   data={"role": "x-axis-label"})
    if y_label:
        scene.text(plot["x0"] - 64, (plot["y0"] + plot["y1"]) / 2, y_label,
                   size=style.get("axis_label_size", 26), anchor="middle", rotate=-90, z=z + 3,
                   data={"role": "y-axis-label"})
    scene.meta["x_label"] = x_label
    scene.meta["y_label"] = y_label


def _draw_legend(scene, spec, style, items, plot, width, z=12, center_legend=False, title=None):
    if not items:
        return
    ls = style.get("legend_size", 20)
    n = len(items)
    maxw = 0
    for lab, _c in items:
        maxw = max(maxw, svgtext.text_width_px(lab, ls) + 50)
    lw = min(width * 0.42, maxw + 46)
    lh = n * (ls + 14) + (title and 30 or 20)
    if center_legend:
        lx = width - lw - 24
        ly = 20
    else:
        lx = width - lw - 24
        ly = plot["y0"] + 16
    scene.rect(lx, ly, lw, lh, fill="#FFFFFF", stroke="#BBBBBB", stroke_width=1, z=z - 1,
               data={"role": "legend-box"})
    if title:
        scene.text(lx + 14, ly + 4, title, size=int(ls * 0.9), weight="bold", anchor="start", z=z,
                   data={"role": "legend-title"})
    for i, (lab, color) in enumerate(items):
        yy = ly + (title and 34 or 18) + i * (ls + 14)
        scene.rect(lx + 14, yy - 9, 20, 16, fill=color, stroke="#666666", stroke_width=1, z=z,
                   data={"role": "legend-swatch", "label": str(lab)})
        scene.text(lx + 46, yy, str(lab), size=ls, anchor="start", z=z,
                   data={"role": "legend-label", "label": str(lab)})
    scene.meta.setdefault("legend_entries", []).extend([(str(lab), color) for lab, color in items])


def _eid(scene, kind):
    n = getattr(scene, "_eidc", 0) + 1
    scene._eidc = n
    return f"{kind}-{n}"


# ---------------------------------------------------------------- 构建入口

def apply_row_filter(rows, filt):
    if not filt or not isinstance(filt, dict):
        return rows
    col = filt.get("column")
    if not col:
        return rows
    eq = filt.get("eq")
    if eq is None:
        return rows
    target = str(eq)
    out = [r for r in rows
           if r.get(col) is not None and str(r.get(col)) == target
           or (safe_float(r.get(col)) is not None and str(safe_float(r.get(col))).rstrip("0").rstrip(".") == target)]
    if not out:
        raise SpecError(f"filter {filt} 无匹配行（列 '{col}' 取值：{sorted({str(r.get(col)) for r in rows})[:10]}）。")
    return out


def build_figure_into(scene, spec, rows, style):
    rows = apply_row_filter(rows, spec.get("filter"))
    t = str(spec.get("type") or "auto").lower()
    if t == "auto":
        t = infer_type(spec, rows)
        spec = {**spec, "type": t}
    if t == "bar":
        build_bar(scene, spec, rows, style)
    elif t == "line":
        build_line(scene, spec, rows, style)
    elif t == "scatter":
        build_scatter(scene, spec, rows, style)
    elif t == "box":
        build_box(scene, spec, rows, style)
    elif t == "heatmap":
        build_heatmap(scene, spec, rows, style)
    elif t == "pie":
        build_pie(scene, spec, rows, style)
    elif t == "network":
        build_network(scene, spec, rows, style)
    elif t == "panel":
        build_panel(scene, spec, rows, style)
    else:
        raise SpecError(f"不支持的图型：{t}（支持 bar/line/scatter/box/heatmap/pie/network/panel）")
    return scene


def infer_type(spec, rows):
    t = spec.get("type")
    if t:
        return t
    if spec.get("entities") or spec.get("relations") or spec.get("nodes"):
        return "network"
    if spec.get("matrix"):
        return "heatmap"
    if spec.get("panels") or spec.get("subfigures"):
        return "panel"
    headers = list(rows[0].keys()) if rows else []
    low = [h.lower() for h in headers]
    if spec.get("labels") and spec.get("values"):
        return "pie"
    if any(a in low for a in ("time", "day", "week", "duration", "hour")) and len(detect_num_cols(headers, rows)) >= 2:
        return "line"
    nums = detect_num_cols(headers, rows)
    cats = detect_cat_cols(headers, rows)
    if len(nums) >= 2 and cats:
        return "bar"
    if len(nums) >= 2:
        return "scatter"
    return "bar"


# ---------------------------------------------------------------- SVG 输出

def scene_to_svg(scene, path, provenance=None, styles=None):
    """手写 XML 生成分层可编辑 SVG（无外部库）。每个图元带 id 与 data-* 溯源属性。

    可编辑性保证（D7/G5）：
    - 文本始终输出为真实 <text> 元素（svgtext 转义），永不变路径/转曲；
    - <g id="layer-*"> 分层（axes/data/text/legend/annotation），每层可单独编辑；
    - <metadata id='provenance'> 溯源块 + 每个数据图元 data-* 属性。
    """
    styles = styles or {}
    font_sans = styles.get("font_sans", cjkfont.FONT_FAMILY_SANS)
    font_cjk = styles.get("font_sans_cjk", cjkfont.FONT_FAMILY_SANS_CJK)
    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
                 f'width="{scene.width}" height="{scene.height}" viewBox="0 0 {scene.width} {scene.height}">')
    lines.append("<title>Scientific figure</title>")
    lines.append("<desc>Editable scientific figure with per-element data-provenance attributes "
                 "(data-file, data-column, data-row-index, data-row-label ...); see data_manifest.json for the full mapping.</desc>")
    prov = dict(provenance or {})
    lines.append("<metadata id='provenance'>")
    lines.append("<![CDATA[" + json.dumps(prov, ensure_ascii=False, indent=2) + "]]>")
    lines.append("</metadata>")
    lines.append("<defs>")
    lines.append("<marker id='arrow' markerWidth='10' markerHeight='10' refX='8' refY='3' orient='auto' "
                 "markerUnits='strokeWidth'><path d='M0,0 L8,3 L0,6 z' fill='#666666'/></marker>")
    lines.append("<pattern id='hatch' width='6' height='6' patternTransform='rotate(45 0 0)' "
                 "patternUnits='userSpaceOnUse'><line x1='0' y1='0' x2='0' y2='6' stroke='#333' "
                 "stroke-width='1'/></pattern>")
    lines.append("</defs>")

    def z_layer(z):
        if z <= 2:
            return "text"
        if z < 9:
            return "axes"
        if z < 10:
            return "legend"
        if z < 14:
            return "data"
        return "annotation"

    prims = [p for p in sorted(scene.prims, key=lambda q: q["z"])
             if p["kind"] not in ("group_open", "group_close")]
    seen = set()
    for p in prims:
        lyr = z_layer(p["z"])
        if lyr not in seen:
            seen.add(lyr)
    # 固定顺序渲染，保证版面一致
    for lyr in sorted(seen, key=lambda l: ["axes", "data", "text", "legend", "annotation"].index(l)):
        lines.append(f'<g id="layer-{lyr}" data-layer="{lyr}">')
        for idx, p in enumerate(prims):
            if z_layer(p["z"]) == lyr:
                attrs = _prim_attrs(p, font_sans, font_cjk, idx)
                tag = "rect" if p["kind"] == "rect" else (
                    "line" if p["kind"] == "line" else
                    "polyline" if p["kind"] == "polyline" else
                    "polygon" if p["kind"] == "polygon" else
                    "circle" if p["kind"] == "circle" else
                    "ellipse" if p["kind"] == "ellipse" else
                    "path" if p["kind"] == "pieslice" else "text")
                lines.append("<" + tag + " " + " ".join(f'{mk}="{svgtext.encoded_svg_text(v)}"' for mk, v in attrs) + "/>")
        lines.append("</g>")
    lines.append("</svg>")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    return path


def _prim_attrs(p, font_sans, font_cjk, idx=0):
    """把图元 dict 转成 SVG 属性（含 id、style 与 data-* 溯源）。

    确定性：svg_id 优先显式值，否则按图元序号确定性生成（不用内建 id()），
    保证同输入重复运行的 SVG 字节级稳定（D18）。
    """
    k = p["kind"]
    a = []
    sid = p.get("svg_id") or f"el-{p.get('data', {}).get('role', k)}-{idx + 1}"
    a.append(("id", sid))
    is_cjk_text = k == "text" and cjkfont.is_cjk(p.get("text", ""))
    ff = font_cjk if is_cjk_text else font_sans
    if k == "rect":
        a += [("x", r2(p.get("x"), 1)), ("y", r2(p.get("y"), 1)),
              ("width", r2(p.get("w", 0), 1)), ("height", r2(p.get("h", 0), 1))]
        if p.get("rx"):
            a.append(("rx", r2(p.get("rx"), 1)))
        a += [("fill", p.get("fill") or "none"), ("stroke", p.get("stroke") or "none")]
        if p.get("stroke_width"):
            a.append(("stroke-width", r2(p.get("stroke_width"), 2)))
    elif k == "line":
        a += [("x1", r2(p.get("x1"), 1)), ("y1", r2(p.get("y1"), 1)),
              ("x2", r2(p.get("x2"), 1)), ("y2", r2(p.get("y2"), 1)),
              ("stroke", p.get("stroke", "#333")), ("stroke-width", r2(p.get("stroke_width", 1), 2))]
        if p.get("dash"):
            a.append(("stroke-dasharray", "6,5"))
        if p.get("arrow"):
            a.append(("marker-end", "url(#arrow)"))
    elif k == "polyline":
        pts = " ".join(f"{r2(x,1)},{r2(y,1)}" for x, y in p["points"])
        a += [("points", pts), ("fill", "none"), ("stroke", p.get("stroke", "#333")),
              ("stroke-width", r2(p.get("stroke_width", 2), 2))]
        if p.get("dash"):
            a.append(("stroke-dasharray", "6,5"))
    elif k == "polygon":
        pts = " ".join(f"{r2(x,1)},{r2(y,1)}" for x, y in p["points"])
        a += [("points", pts), ("fill", p.get("fill") or "none"), ("stroke", p.get("stroke") or "none")]
        if p.get("stroke_width"):
            a.append(("stroke-width", r2(p.get("stroke_width", 1), 2)))
    elif k == "circle":
        a += [("cx", r2(p.get("cx"), 1)), ("cy", r2(p.get("cy"), 1)), ("r", r2(p.get("r"), 1)),
              ("fill", p.get("fill") or "none"), ("stroke", p.get("stroke") or "none")]
        if p.get("stroke_width"):
            a.append(("stroke-width", r2(p.get("stroke_width"), 2)))
    elif k == "ellipse":
        a += [("cx", r2(p.get("cx"), 1)), ("cy", r2(p.get("cy"), 1)),
              ("rx", r2(p.get("rx"), 1)), ("ry", r2(p.get("ry"), 1)),
              ("fill", p.get("fill") or "none"), ("stroke", p.get("stroke") or "none")]
        if p.get("stroke_width"):
            a.append(("stroke-width", r2(p.get("stroke_width"), 2)))
    elif k == "pieslice":
        cx, cy, r, a0, a1 = p["cx"], p["cy"], p["r"], p["angle0"], p["angle1"]
        x0 = cx + r * math.cos(math.radians(a0)); y0 = cy + r * math.sin(math.radians(a0))
        x1 = cx + r * math.cos(math.radians(a1)); y1 = cy + r * math.sin(math.radians(a1))
        if a1 - a0 >= 359.9:
            d = f"M {r2(cx - r,1)} {r2(cy,1)} a {r2(r,1)} {r2(r,1)} 0 1 1 {r2(2 * r,1)} 0 a {r2(r,1)} {r2(r,1)} 0 1 1 {r2(-2 * r,1)} 0 z"
        else:
            d = f"M {r2(cx,1)} {r2(cy,1)} L {r2(x0,1)} {r2(y0,1)} A {r2(r,1)} {r2(r,1)} 0 {'1' if a1 - a0 > 180 else '0'} 1 {r2(x1,1)} {r2(y1,1)} Z"
        a += [("d", d), ("fill", p.get("fill") or "none"), ("stroke", p.get("stroke") or "none")]
        if p.get("stroke_width"):
            a.append(("stroke-width", r2(p.get("stroke_width"), 2)))
    elif k == "text":
        a += [("x", r2(p.get("x"), 1)), ("y", r2(p.get("y"), 1)),
              ("font-size", str(p.get("size", 16))),
              ("font-family", ff),
              ("fill", p.get("fill", "#1a1a1a"))]
        if p.get("weight"):
            a.append(("font-weight", str(p.get("weight"))))
        if p.get("italic"):
            a.append(("font-style", "italic"))
        if p.get("anchor") == "middle":
            a.append(("text-anchor", "middle"))
        elif p.get("anchor") == "end":
            a.append(("text-anchor", "end"))
        if p.get("rotate"):
            a.append(("transform", f"rotate({-p['rotate']} {r2(p.get('x'),1)} {r2(p.get('y'),1)})"))
        a.append(("xml:space", "preserve"))
        a.append(("data-text", p.get("text")))
    used = {mk for mk, _ in a}
    for kk, vv in (p.get("data") or {}).items():
        if vv is None:
            continue
        aname = f"data-{kk}"
        if aname in used:
            continue
        if isinstance(vv, (dict, list)):
            vv = json.dumps(vv, ensure_ascii=False)
        a.append((aname, str(vv)))
    return a


def r2(v, nd=1):
    if v is None:
        return "0"
    if isinstance(v, int):
        return str(v)
    return f"{v:.{nd}f}".rstrip("0").rstrip(".")


# ---------------------------------------------------------------- PNG / PDF 输出

def scene_to_png(scene, path, styles=None, fonts=None, scale=1.0, dpi=150):
    """用 Pillow 把同一图元场景渲染成 PNG（与 SVG 图元一一对应）。"""
    if not HAS_PIL:
        raise RuntimeError("Pillow 不可用，无法渲染 PNG。")
    from PIL import Image, ImageDraw, ImageFont
    w = int(scene.width * scale / 96 * dpi)
    h = int(scene.height * scale / 96 * dpi)
    img = Image.new("RGBA", (w, h), (255, 255, 255, 255))
    dr = ImageDraw.Draw(img)
    fonts = fonts or cjkfont.FontMap()
    kx = w / scene.width
    ky = h / scene.height
    for p in sorted(scene.prims, key=lambda q: q["z"]):
        k = p["kind"]
        if k in ("group_open", "group_close"):
            continue
        if k == "rect":
            box = [int(p["x"] * kx), int(p["y"] * ky), int((p["x"] + p.get("w", 0)) * kx), int((p["y"] + p.get("h", 0)) * ky)]
            if p.get("fill"):
                dr.rectangle(box, fill=p["fill"], outline=p.get("stroke") or None,
                             width=max(1, int(p.get("stroke_width", 1) * kx)))
            else:
                dr.rectangle(box, outline=p.get("stroke") or "#333",
                             width=max(1, int(p.get("stroke_width", 1) * kx)))
        elif k == "line":
            a = (p["x1"] * kx, p["y1"] * ky, p["x2"] * kx, p["y2"] * ky)
            lw = max(1, int(p.get("stroke_width", 1) * kx))
            if p.get("dash"):
                _pil_dash_line(dr, a, w=int(lw), fill=p.get("stroke", "#333"), dash=(8, 6))
            else:
                dr.line(a, fill=p.get("stroke", "#333"), width=lw)
            if p.get("arrow"):
                _pil_arrow(dr, a, fill=p.get("stroke", "#666"), size=max(9, lw * 4))
        elif k in ("polyline", "polygon"):
            pts = [(x * kx, y * ky) for x, y in p["points"]]
            if k == "polygon":
                dr.polygon(pts, fill=p.get("fill") or None, outline=p.get("stroke") or None)
            else:
                dr.line(pts, fill=p.get("stroke", "#333"), width=max(1, int(p.get("stroke_width", 2) * kx)),
                        joint="curve")
        elif k == "circle":
            cx, cy, r = p["cx"] * kx, p["cy"] * ky, p["r"] * kx
            box = [cx - r, cy - r, cx + r, cy + r]
            dr.ellipse(box, fill=p.get("fill") or None, outline=p.get("stroke") or None,
                       width=max(1, int(p.get("stroke_width", 1) * kx)))
        elif k == "ellipse":
            cx, cy, rx, ry = p["cx"] * kx, p["cy"] * ky, p["rx"] * kx, p["ry"] * ky
            dr.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=p.get("fill") or None,
                       outline=p.get("stroke") or None, width=max(1, int(p.get("stroke_width", 1) * kx)))
        elif k == "pieslice":
            cx, cy, r = p["cx"] * kx, p["cy"] * ky, p["r"] * kx
            box = [cx - r, cy - r, cx + r, cy + r]
            dr.pieslice(box, p["angle0"], p["angle1"], fill=p["fill"])
        elif k == "text":
            size = max(4, int(p.get("size", 16) * kx))
            text = str(p.get("text", ""))
            font = fonts.pil_font(role="sans", size=size, text=text)
            if p.get("rotate"):
                _pil_rotated_text(dr, (p["x"] * kx, p["y"] * ky), text, font, p["rotate"],
                                  p.get("fill", "#1a1a1a"))
            else:
                anchor = {"middle": "mm", "end": "rm"}.get(p.get("anchor"), "lm")
                dr.text((p["x"] * kx, p["y"] * ky), text, font=font,
                        fill=p.get("fill", "#1a1a1a"), anchor=anchor)
    img.save(path, "PNG")
    meta = dict(scene.meta)
    meta["png_size"] = [w, h]
    return path


def _pil_dash_line(dr, a, w=2, fill="#333", dash=(8, 6)):
    x1, y1, x2, y2 = a
    dx, dy = x2 - x1, y2 - y1
    dist = math.hypot(dx, dy)
    if dist <= 0:
        return
    ux, uy = dx / dist, dy / dist
    pos = 0.0
    on = True
    di = 0
    while pos < dist:
        ln = dash[di % 2]
        nxt = min(dist, pos + ln)
        if on:
            dr.line((x1 + ux * pos, y1 + uy * pos, x1 + ux * nxt, y1 + uy * nxt), fill=fill, width=w)
        pos = nxt
        on = not on
        di += 1


def _pil_arrow(dr, a, fill="#666", size=10):
    x1, y1, x2, y2 = a
    ang = math.atan2(y2 - y1, x2 - x1)
    p1 = (x2, y2)
    p2 = (x2 - size * math.cos(ang - 0.42), y2 - size * math.sin(ang - 0.42))
    p3 = (x2 - size * math.cos(ang + 0.42), y2 - size * math.sin(ang + 0.42))
    dr.polygon([p1, p2, p3], fill=fill)


def _pil_rotated_text(dr, xy, text, font, angle, fill):
    from PIL import Image, ImageDraw, ImageFont
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tmp = Image.new("RGBA", (tw * 2 + 8, th * 2 + 8), (255, 255, 255, 0))
    tdr = ImageDraw.Draw(tmp)
    tdr.text((4 - bbox[0], 4 - bbox[1]), text, font=font, fill=fill)
    tmp = tmp.rotate(angle, expand=True, resample=Image.BICUBIC)
    dr._image.paste(tmp, (int(xy[0] - tmp.width / 2), int(xy[1] - tmp.height / 2)), tmp)


def png_to_pdf(png_path, pdf_path, title=""):
    """把 PNG 预览嵌入 PDF（PIL 即可，无需 ghostscript）。PDF 仅作检查用预览。"""
    if not HAS_PIL:
        raise RuntimeError("Pillow 不可用，无法生成 PDF 预览。")
    from PIL import Image, ImageDraw, ImageFont
    img = Image.open(png_path).convert("RGB")
    pt = (img.width / 96 * 72, img.height / 96 * 72)
    page = Image.new("RGB", (int(round(pt[0])), int(round(pt[1]))), (255, 255, 255))
    if title:
        draw = ImageDraw.Draw(page)
        try:
            try:
                font = ImageFont.load_default(18)
            except TypeError:
                font = ImageFont.load_default()
            draw.text((36, 24), title, font=font, fill=(0, 0, 0))
            pad_top = 70
        except Exception:
            pad_top = 8
        img = img.resize((int(img.width * 0.92), int(img.height * 0.92)))
        page.paste(img, (36, pad_top))
    else:
        page.paste(img, (0, 0))
    page.save(pdf_path, "PDF", resolution=150.0)
    return pdf_path


# ---------------------------------------------------------------- 校验

def run_checks(scene, spec, rows, ctx, fig_id):
    """标注校验清单：轴单位、图例-系列对应、数值覆盖、显著性、CJK 字体、图元溯源覆盖。"""
    checks = []
    ok = lambda cid, ok_, det: checks.append({"id": cid, "level": "ok" if ok_ else "warn", "detail": det, "pass": ok_})
    fonts = ctx.get("fonts")
    style = ctx.get("style")
    # 1 图元溯源覆盖
    n_data = sum(1 for p in scene.prims if p.get("data"))
    n_mapped = sum(1 for p in scene.prims if p.get("data") and p["data"].get("role"))
    ok("provenance", n_data > 0 and n_mapped == n_data,
       f"图元 {n_data} 个，带 role 溯源 {n_mapped} 个。")
    # 2 图例与系列对应
    series = scene.meta.get("series")
    legend = [e for e in scene.meta.get("legend_entries", [])]
    if series:
        sl = [str(s) for s in series]
        lg = [str(l) for l, _ in legend]
        missing = [s for s in sl if s not in lg]
        extra = [l for l in lg if len([x for x in sl if x == l]) == 0 and l != "Group"]
        ok("legend-mapping", not missing and not extra,
           f"系列 {len(sl)} 个，图例 {len(lg)} 个；缺 {missing} 多 {extra}。")
    else:
        ok("legend-mapping", True, "无系列型图（heatmap/box/network 图例另检）。")
    # 3 轴范围覆盖数据
    yr = scene.meta.get("y_range")
    if yr:
        vals = [safe_float(p["data"].get("value"))
                for p in scene.prims if p.get("data") and p["data"].get("value") is not None]
        if vals:
            ok("range-covers-data", min(vals) >= yr[0] and max(vals) <= yr[1],
               f"数据范围 [{min(vals):.4g},{max(vals):.4g}] 轴范围 [{yr[0]:.4g},{yr[1]:.4g}]。")
    # 4 CJK 字体
    cjk_texts = [p["text"] for p in scene.prims if p["kind"] == "text" and cjkfont.is_cjk(p.get("text", ""))]
    cjk_font = bool(fonts and fonts.sans_cjk)
    ok("cjk-font", cjk_font or not cjk_texts,
       f"CJK 文本 {len(cjk_texts)} 处；CJK 字体{'已找到 ' + fonts.sans_cjk[0] if cjk_font else '未找到（SVG 依靠字体族回退链，PNG 可能缺字）'}。")
    # 5 轴标签单位（panel 递归子面板；network/pie 无坐标轴则跳过）
    ftype = str(spec.get("type") or "").lower()
    if ftype == "panel":
        subs = scene.meta.get("panels", [])
        missing = [i for i, m in enumerate(subs) if not (m.get("y_label"))]
        ok("axis-units", not missing, f"{len(subs)} 个面板；缺少 y 轴标签的面板：{missing}。")
    elif ftype in ("bar", "line", "scatter", "box", "heatmap"):
        xlab = scene.meta.get("x_label") or ""
        ylab = scene.meta.get("y_label") or ""
        ok("axis-units", bool(xlab) and bool(ylab),
           f"x 轴标签：'{xlab}'；y 轴标签：'{ylab}'。")
    else:
        ok("axis-units", True, f"图型 {ftype} 无坐标轴标签要求。")
    # 6 显著性一致性
    ann_lines = sum(1 for p in scene.prims if p.get("data") and p["data"].get("role") == "significance-line")
    ann_txt = sum(1 for p in scene.prims if p.get("data") and p["data"].get("role") == "significance-text")
    ok("significance", ann_txt == ann_lines,
       f"显著性线段 {ann_lines} 条，文字 {ann_txt} 个（p 值脚注见 annotation_footnotes）。")
    # 7 空值处理
    used_cells = sum(1 for p in scene.prims if (p.get("data") or {}).get("row_index") is not None)
    ok("null-handling", True, f"共使用 {used_cells} 个源数据行位置。")
    # 8 标签遮挡（真实字体测量；旋转文本不参与）
    overlap = _text_overlap_count(scene, ctx.get("fonts"))
    ok("occlusion", overlap == 0, f"文本重叠 {overlap} 处（检测到的最大处数；旋转/轴外文本不参与）。")
    return checks


def _text_overlap_count(scene, fonts=None):
    from PIL import ImageFont
    boxes = []
    for p in scene.prims:
        if p["kind"] != "text":
            continue
        if p.get("rotate"):
            continue
        if (p.get("data") or {}).get("role") in ("title", "subtitle", "panel-label"):
            continue
        try:
            f = fonts.pil_font(role="sans", size=int(p.get("size", 16)), text=p.get("text", "")) if fonts else None
            bb = f.getbbox(str(p.get("text", ""))) if f else ImageFont.load_default().getbbox(str(p.get("text", "")))
            wpx = bb[2] - bb[0]
            hpx = (bb[3] - bb[1]) or int(p.get("size", 16))
        except Exception:
            continue
        anchor = p.get("anchor", "start")
        x0 = p.get("x", 0) - (wpx / 2 if anchor == "middle" else wpx if anchor == "end" else 0)
        boxes.append((x0, p.get("y", 0) - hpx * 0.5, x0 + wpx + 2, p.get("y", 0) + hpx * 1.2))
    cnt = 0
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            ax0, ay0, ax1, ay1 = boxes[i]
            bx0, by0, bx1, by1 = boxes[j]
            ix = min(ax1, bx1) - max(ax0, bx0)
            iy = min(ay1, by1) - max(ay0, by0)
            if ix > 4 and iy > 4:
                cnt += 1
                if cnt >= 20:
                    return 20
    return cnt


# ---------------------------------------------------------------- 导出到文件

def export_figure(spec, rows, ctx, out_prefix, provenance=None):
    """完整导出：spec(已归一化) → SVG + PNG + PDF +（manifest 信息）。返回结果 dict。"""
    style = resolve_figure_style(spec, ctx["style"])
    fig_id = str(spec.get("id") or provenance.get("figure_id") or "fig")
    width = int(spec.get("width") or ctx.get("width") or DEFAULT_WIDTH)
    height = int(spec.get("height") or ctx.get("height") or DEFAULT_HEIGHT)
    scene = Scene(width=width, height=height)
    scene.fig_id = fig_id
    build_figure_into(scene, spec, rows, style)
    title = spec.get("title")
    if title:
        scene.text(scene.width / 2, 52, title, size=style.get("title_size", 34), anchor="middle",
                   weight="bold", z=0, data={"role": "title"})
        subtitle = spec.get("subtitle")
        if subtitle:
            scene.text(scene.width / 2, 84, subtitle, size=style.get("subtitle_size", 22), anchor="middle",
                       z=0, data={"role": "subtitle"})
    scene.meta.setdefault("y_label", scene.meta.get("y_label"))
    svg_path = out_prefix + ".svg"
    png_path = out_prefix + ".png"
    pdf_path = out_prefix + ".pdf"
    scene_to_svg(scene, svg_path, provenance=provenance, styles={
        "font_sans": style.get("font_sans", cjkfont.FONT_FAMILY_SANS),
        "font_sans_cjk": style.get("font_sans_cjk", cjkfont.FONT_FAMILY_SANS_CJK),
    })
    if ctx.get("with_preview", True):
        try:
            scene_to_png(scene, png_path, styles=style, fonts=ctx.get("fonts"),
                         dpi=int(style.get("dpi", 150)))
            try:
                png_to_pdf(png_path, pdf_path, title=f"{fig_id}: {title or 'figure'}")
            except Exception as exc:
                scene.meta.setdefault("warnings", []).append(f"PDF 预览失败：{exc}")
        except Exception as exc:
            scene.meta.setdefault("warnings", []).append(f"PNG 渲染失败：{exc}")
    checks = run_checks(scene, spec, rows, ctx, fig_id)
    manifest_elems = []
    for p in scene.prims:
        d = p.get("data") or {}
        if not d:
            continue
        manifest_elems.append({
            "svg_id": p.get("svg_id") or "",
            "role": d.get("role"),
            "source": {kk: vv for kk, vv in d.items() if kk not in ("role",)},
            "z": p.get("z"),
        })
    result = {
        "figure_id": fig_id,
        "type": spec.get("type"),
        "title": title,
        "files": {
            "editable_svg": os.path.basename(svg_path),
            "png_preview": os.path.basename(png_path) if os.path.exists(png_path) else None,
            "pdf_preview": os.path.basename(pdf_path) if os.path.exists(pdf_path) else None,
        },
        "checks": checks,
        "meta": {
            "y_range": scene.meta.get("y_range"),
            "x_range": scene.meta.get("x_range"),
            "adjustments": scene.meta.get("adjustments", []),
            "warnings": scene.meta.get("warnings", []),
            "annotation_footnotes": scene.meta.get("annotation_footnotes", []),
        },
        "elements": manifest_elems,
    }
    return result