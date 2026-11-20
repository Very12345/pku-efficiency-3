# -*- coding: utf-8 -*-
"""Chart regeneration from source data tables (matplotlib only, no network).

Policy (honesty first):
  * charts are *regenerated* only from numeric columns of a real data table
    that arrived in the case inputs; nothing is synthesized or smoothed.
  * a paper figure that is a bitmap and has no extractable data is NOT
    redrawn here — the deck shows an honest placeholder instead.
  * chart labels come from the table header / caption verbatim.
"""
import os
import re
import warnings

from common import LOG, resolve_font, ensure_dir, now_iso, sha256_file

warnings.filterwarnings("ignore", category=UserWarning)  # font glyph warnings


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
    family, path = resolve_font("Microsoft YaHei")
    imports_ok = True
    try:
        from matplotlib import font_manager
        if path and os.path.isfile(path):
            font_manager.fontManager.addfont(path)
        fonts = ["Microsoft YaHei", "SimHei", "Arial", "DejaVu Sans"]
        plt.rcParams["font.sans-serif"] = fonts
        plt.rcParams["axes.unicode_minus"] = False
    except Exception as e:  # noqa: BLE001
        imports_ok = False
        LOG.warning("font setup failed: %s", e)
    return family, imports_ok


def _numeric_cols(table):
    """Return (key_col, numeric_cols) where numeric_cols is list of col names
    in which all non-empty cells parse as numbers (int/float or percents)."""
    key_col = None
    if table.columns:
        key_col = table.columns[0]
    numeric = []
    for col in table.columns[1:]:
        vals = []
        ok = True
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
    Raises on failure so caller can fall back to a native editable table.
    """
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
    png = os.path.join(work_dir, "chart_%s.png" % _safe(table.id))
    fig.savefig(png, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    note = "重绘自数据表 %s（%d 行）；字体=%s；未对数据做修改" % (table.id, len(table.rows), family or "系统默认")
    return png, note


def build_placeholder(work_dir, label):
    """Honest placeholder PNG for a paper figure that cannot be redrawn."""
    from PIL import Image, ImageDraw, ImageFont
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
    png = os.path.join(work_dir, "placeholder_%s.png" % _safe(label or "fig"))
    img.save(png)
    return png


def _shorten_title(s, n=24):
    s = re.sub(r"\s+", " ", (s or "")).strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def _fmt(v):
    return ("%.2f" % v).rstrip("0").rstrip(".") if v == int(v) or abs(v) < 0.001 or abs(v) >= 100 else "%.1f" % v


def _safe(name):
    return re.sub(r"[^\w.-]+", "_", str(name))[:60]