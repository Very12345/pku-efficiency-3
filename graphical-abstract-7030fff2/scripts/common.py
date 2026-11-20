# -*- coding: utf-8 -*-
"""Shared helpers for the graphical-abstract skill (pku-efficiency-3, figures group).

Everything in this package is deterministic and source-bound:
- UTF-8 everywhere (Windows-safe);
- no hard-coded absolute paths (all paths are resolved against the skill root
  via SCRIPT_DIR / SKILL_ROOT, or passed on the command line);
- small color/geometry utilities shared by the SVG builder and the preview
  renderer so the editable source and the raster preview cannot diverge.
"""
from __future__ import annotations

import hashlib
import json
import os
import re

SKILL_VERSION = "1.0.0"
SCHEMA_VERSION = "1.0"

# ---------------------------------------------------------------------------
# Paths (self-locating; never hard-code skill locations)
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(SCRIPT_DIR)  # skill root == parent of scripts/

DEFAULT_OUT = os.path.join(SKILL_ROOT, "out")


def skill_root() -> str:
    return SKILL_ROOT


# ---------------------------------------------------------------------------
# IO (UTF-8 enforced; Windows default codepage is cp936)
# ---------------------------------------------------------------------------
def load_json(path: str):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: str, obj, indent: int = 2) -> None:
    _ensure_dir(path)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=indent)
        fh.write("\n")


def write_text(path: str, text: str) -> None:
    _ensure_dir(path)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def _ensure_dir(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)


def list_dir_text(path: str, exts=(".md", ".txt", ".json", ".csv", ".tex", ".rst")) -> list:
    """Return all text-like file paths under `path` (file or directory)."""
    if os.path.isfile(path):
        return [path]
    out = []
    for root, _dirs, files in os.walk(path):
        for name in sorted(files):
            low = name.lower()
            if low.endswith(exts):
                out.append(os.path.join(root, name))
    return sorted(out)


# ---------------------------------------------------------------------------
# Hashing (provenance / determinism)
# ---------------------------------------------------------------------------
def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def slug(text: str, fallback: str = "item") -> str:
    """Deterministic id from any label; keeps ASCII + CJK word characters so
    Chinese entity names never collide (e.g. 肿瘤细胞 vs 肿瘤组织)."""
    if not text or not str(text).strip():
        return fallback
    s = re.sub(r"[^\w]+", "_", str(text).strip(), flags=re.UNICODE).strip("_")
    return (s or fallback)[:48]


# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
# Okabe-Ito palette: color-blind safe and grayscale printable.
OKABE_ITO = [
    "#0072B2", "#009E73", "#D55E00", "#CC79A7", "#F0E442",
    "#56B4E9", "#E69F00", "#000000", "#7F7F7F",
]
DEFAULT_PALETTE = OKABE_ITO


def hex_to_rgb(color: str):
    """'#RRGGBB' -> (r, g, b) floats in [0, 1]; tolerates 'RRGGBB'."""
    c = color.strip().lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    if len(c) != 6:
        raise ValueError(f"bad color: {color!r}")
    return tuple(int(c[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def relative_luminance(hex_color: str) -> float:
    r, g, b = hex_to_rgb(hex_color)
    vals = []
    for v in (r, g, b):
        vals.append(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4)
    return 0.2126 * vals[0] + 0.7152 * vals[1] + 0.0722 * vals[2]


def luminance_gap(a: str, b: str) -> float:
    return abs(relative_luminance(a) - relative_luminance(b))


def lighten(hex_color: str, amount: float = 0.35) -> str:
    """Blend toward white; useful for panel fills derived from palette colors."""
    r, g, b = hex_to_rgb(hex_color)
    mix = lambda v: v + (1.0 - v) * amount  # noqa
    return "#%02X%02X%02X" % (round(mix(r) * 255), round(mix(g) * 255), round(mix(b) * 255))


def interpolate(a: str, b: str, t: float) -> str:
    """Linear interpolation between two hex colors, t in [0, 1]."""
    ra, ga, ba = hex_to_rgb(a)
    rb, gb, bb = hex_to_rgb(b)
    t = max(0.0, min(1.0, t))
    mix = lambda x, y: x + (y - x) * t  # noqa
    return "#%02X%02X%02X" % (
        round(mix(ra, rb) * 255), round(mix(ga, gb) * 255), round(mix(ba, bb) * 255))


# ---------------------------------------------------------------------------
# Small text metrics helper (used for overflow checks; shared by renderers)
# ---------------------------------------------------------------------------
def estimate_text_width(text: str, font_size: float) -> float:
    """Rough width in the same units as the canvas (px @ 96dpi-ish).

    Used only for *layout warnings* (auto-shrink / overflow notes), never to
    fabricate exact metrics.
    """
    width = 0.0
    for ch in text:
        if ord(ch) > 0x2E80:  # roughly CJK-wide
            width += font_size
        else:
            width += font_size * 0.58
    return width