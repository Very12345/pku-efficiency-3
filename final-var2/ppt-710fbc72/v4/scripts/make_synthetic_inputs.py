# -*- coding: utf-8 -*-
"""make_synthetic_inputs.py — synthesise the example case's placeholder figures.

The skill ships no images (Skill resources must be UTF-8 text only), so the
figures referenced by `examples/case.json` are drawn on demand.  They are
**deliberately schematic**: plain geometry (frames, axes, bars, curves) with a
visible `SCHEMATIC / 示意` watermark and no fabricated measurement labels, so
nobody can mistake them for real published data.  Real cases receive their own
material from the platform; nothing here is a prepared answer.

Usage:

  python scripts/make_synthetic_inputs.py --dir examples

  # explicit files / force regeneration
  python scripts/make_synthetic_inputs.py --out-dir <run>/examples/figs --force
"""
from __future__ import annotations

import os
import sys

from common import utf8_writer, portable_path

# (file name, width, height, watermark text)
FIGURES = [
    ("fig1.png", 1000, 700, "SCHEMATIC / 示意 — placeholder, not real data"),
    ("fig2.png", 1000, 700, "SCHEMATIC / 示意 — placeholder, not real data"),
]


def _font(size: int):
    from PIL import ImageFont
    try:
        return ImageFont.load_default(size=size)
    except TypeError:          # Pillow < 9.2
        return ImageFont.load_default()


def _draw_fig1(w: int, h: int, note: str):
    """Left: particle-size distribution histogram. Right: phase-index bars.

    Pure geometry: no numeric labels, no claim of a measured value.
    """
    from PIL import Image, ImageDraw
    ink, accent, muted = (31, 56, 100), (197, 90, 17), (110, 110, 110)
    img = Image.new("RGB", (w, h), (255, 255, 255))
    d = ImageDraw.Draw(img)
    f = _font(18)
    fs = _font(14)

    d.rectangle([30, 30, w // 2 - 20, h - 60], outline=ink, width=2)
    d.text((44, 40), "size distribution (schematic)", font=f, fill=ink)
    for i, frac in enumerate([0.25, 0.55, 0.9, 0.7, 0.4, 0.2]):
        bw = (w // 2 - 110) // 6
        x = 60 + i * bw
        y = h - 90 - int(frac * (h - 220))
        d.rectangle([x, y, x + bw - 10, h - 90], fill=accent)
    d.line([55, h - 90, w // 2 - 35, h - 90], fill=ink, width=2)

    d.rectangle([w // 2 + 20, 30, w - 30, h - 60], outline=ink, width=2)
    d.text((w // 2 + 34, 40), "phase index (schematic)", font=f, fill=ink)
    ys = [0.35, 0.6, 0.8, 0.5]
    for i, v in enumerate(ys):
        y = 110 + i * 80
        d.rectangle([w // 2 + 50, y, w // 2 + 50 + int(v * (w // 2 - 140)), y + 26], fill=ink)
        d.text((w // 2 + 50, y + 30), "—", font=fs, fill=muted)

    d.text((34, h - 40), note, font=fs, fill=muted)
    return img


def _draw_fig2(w: int, h: int, note: str):
    """Two schematic response curves over a temperature-like x axis."""
    from PIL import Image, ImageDraw
    ink, accent, accent2, muted = (31, 56, 100), (197, 90, 17), (46, 117, 182), (110, 110, 110)
    img = Image.new("RGB", (w, h), (255, 255, 255))
    d = ImageDraw.Draw(img)
    f = _font(18)
    fs = _font(14)

    x0, y0, x1, y1 = 90, 60, w - 60, h - 90
    d.rectangle([x0, y0, x1, y1], outline=ink, width=2)
    d.text((x0 + 12, y0 + 10), "response vs. control variable (schematic)", font=f, fill=ink)
    for i in range(1, 5):                      # gridlines only
        y = y0 + i * (y1 - y0) // 5
        d.line([x0, y, x1, y], fill=(230, 230, 230), width=1)
    pts_a, pts_b = [], []
    for i in range(0, 21):
        t = i / 20.0
        x = x0 + 20 + int(t * (x1 - x0 - 40))
        pts_a.append((x, y1 - 30 - int((1 - (t - 0.55) ** 2 * 3.2) * (y1 - y0 - 80) * 0.75)))
        pts_b.append((x, y1 - 30 - int((0.55 + 0.35 * t) * (y1 - y0 - 80) * 0.75)))
    d.line(pts_a, fill=accent, width=4)
    d.line(pts_b, fill=accent2, width=4)
    d.text((x0 + 14, y1 - 30), "○ series A (schematic)", font=fs, fill=accent)
    d.text((x0 + 220, y1 - 30), "○ series B (schematic)", font=fs, fill=accent2)
    d.text((34, h - 40), note, font=fs, fill=muted)
    return img


def make_figures(out_dir: str, force: bool = False) -> list:
    """Write the placeholder figures into out_dir; return the written paths."""
    from PIL import Image
    os.makedirs(out_dir, exist_ok=True)
    written = []
    for name, w, h, note in FIGURES:
        path = os.path.join(out_dir, name)
        if os.path.exists(path) and not force:
            written.append(path)
            continue
        img = _draw_fig1(w, h, note) if name == "fig1.png" else _draw_fig2(w, h, note)
        img.save(path, format="PNG", optimize=True)
        written.append(path)
    return written


def main(argv=None):
    utf8_writer()
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", default="",
                    help="example dir (figures go to <dir>/figs) — e.g. --dir examples")
    ap.add_argument("--out-dir", default="", help="explicit figure directory")
    ap.add_argument("--force", action="store_true", help="redraw existing figures")
    a = ap.parse_args(argv)

    out_dir = a.out_dir or (os.path.join(a.dir, "figs") if a.dir else "")
    if not out_dir:
        print("make-synthetic-inputs FAILED: pass --dir <example dir> or --out-dir <figs dir>",
              file=sys.stderr)
        return 2
    try:
        written = make_figures(out_dir, force=a.force)
    except Exception as exc:
        print(f"make-synthetic-inputs FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    for p in written:
        print(f"figure ready: {portable_path(p)} ({os.path.getsize(p)} B)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
