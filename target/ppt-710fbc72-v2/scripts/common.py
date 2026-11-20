# -*- coding: utf-8 -*-
"""common.py — ppt-710fbc72 v2 Skill (slides group) shared utilities.

Path self-location, version stamping, hashing, fonts probing, color/number
helpers.  No hard-coded absolute paths anywhere in this skill: every script
locates the skill root via os.path.dirname(__file__) and all real I/O paths
come from the command line.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

SKILL_NAME = "academic-slide-adapt"
SKILL_VERSION = "2.0.0"          # v2: two-phase workflow (adopt-plan -> adapt)
DISPLAY_NAME = "Academic PPT Template & Format Adaptation（学术PPT模板与格式适配）"
WORKORDER = "academic_slide_deck"


def _root() -> str:
    """Skill root = parent of scripts/."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def skill_root() -> str:
    return _root()


def utf8_writer():
    """Reconfigure stdout/stderr to UTF-8 (Windows console safety)."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str) -> str:
    with open(path, "rb") as fh:
        return sha256_bytes(fh.read())


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_text(path: str) -> str:
    """Read a UTF-8 text file; tolerates BOM; raises FileNotFoundError."""
    with open(path, "r", encoding="utf-8-sig", newline="") as fh:
        return fh.read()


def write_text(path: str, text: str) -> None:
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:  # LF on every OS
        fh.write(text)


def load_json(path: str):
    with open(path, "r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def dump_json(path: str, obj, indent: int = 2) -> None:
    write_text(path, json.dumps(obj, ensure_ascii=False, indent=indent) + "\n")


def emu_to_pt(value) -> float:
    return (value or 0) / 12700.0


def emu_to_in(value) -> float:
    return (value or 0) / 914400.0


def now_iso() -> str:
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def tool_versions() -> dict:
    out = {}
    try:
        import platform
        out["python"] = platform.python_version()
    except Exception:
        out["python"] = "?"
    for mod, attr in (("pptx", "__version__"), ("PIL", "PIL"), ("numpy", "__version__"),
                      ("matplotlib", "__version__"), ("reportlab", "Version")):
        try:
            m = __import__(mod)
            out[mod] = str(getattr(m, attr, "?"))
        except Exception:
            out[mod] = "unavailable"
    return out


# --------------------------------------------------------------------------
# Typographic helpers -------------------------------------------------------
def char_effective_len(text: str) -> float:
    """Weighted length: CJK chars count 1.0, ASCII etc. 0.55 of full width."""
    n = 0.0
    for ch in text:
        if ord(ch) > 0x2E7F:  # CJK / full-width
            n += 1.0
        else:
            n += 0.55
    return max(n, 0.0)


def estimate_lines(text: str, font_pt: float, box_width_pt: float) -> int:
    """Rough wrapped line count for a single paragraph inside a box."""
    if box_width_pt <= 0 or font_pt <= 0:
        return 1
    per_line = max(2, int(box_width_pt / font_pt))
    total = char_effective_len(text)
    import math
    return max(1, int(math.ceil(total / per_line)))


FONT_LADDER = [32, 28, 26, 24, 22, 20, 18, 16, 14, 12]  # pt, descending


def fit_font_size(paragraphs, box_width_pt: int, box_height_pt: int,
                  start_size: float, min_size: float = 12.0,
                  line_spacing: float = 1.28) -> tuple:
    """Pick the largest FONT_LADDER size that fits paragraphs in the box.

    Returns (size_pt, overflow_est_lines).  Paragraphs is a list of strings.
    Never returns below min_size; if even min_size overflows, the overflow
    line count is reported for the audit instead of shrinking invisibly.
    """
    import math
    allowed = [s for s in FONT_LADDER if s <= start_size + 0.001] or [min_size]
    allowed = sorted(set([min_size] + allowed), reverse=True)
    best = None
    best_overflow = 0
    for size in allowed:
        lines = 0
        for p in paragraphs:
            lines += estimate_lines(p, size, box_width_pt)
        need = lines * line_spacing * size
        overflow = max(0, int(math.ceil(need - box_height_pt)))
        if overflow <= 0:
            return size, 0
        if best is None or overflow < best_overflow:
            best, best_overflow = size, overflow
    return min_size, best_overflow


# --------------------------------------------------------------------------
# Fonts (PIL preview only) --------------------------------------------------
def probe_font_candidates():
    """Return (list of truetype paths/pairs tried, chosen path, chosen idx)."""
    candidates = []
    win_dir = r"C:\Windows\Fonts"
    known = [
        ("msyh.ttc", 0), ("msyh.ttc", 1), ("msyhbd.ttc", 0), ("simhei.ttf", 0),
        ("simsun.ttc", 0), ("Microsoft YaHei UI.ttf", 0), ("arial.ttf", 0),
        ("segoeui.ttf", 0), ("times.ttf", 0),
    ]
    for name, idx in known:
        p = os.path.join(win_dir, name)
        candidates.append((p, idx))
    for p, idx in candidates:
        try:
            from PIL import ImageFont
            ImageFont.truetype(p, 16, index=idx)
            return candidates, p, idx
        except Exception:
            continue
    return candidates, None, 0


def pil_font(size: int, bold: bool = False):
    """Load a PIL font with graceful fallback to load_default(size)."""
    from PIL import ImageFont
    _, path, idx = probe_font_candidates()
    if path and os.path.exists(path):
        try:
            return ImageFont.truetype(path, size, index=idx)
        except Exception:
            pass
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


# Deterministic colour palette (Okabe-Ito-ish, slide-safe).
PALETTE = {
    "ink": "#1F3864",      # deep navy (titles)
    "body": "#333333",
    "muted": "#666666",
    "accent": "#C55A11",    # burnt orange accent
    "accent2": "#2E75B6",   # steel blue
    "paper": "#FFFFFF",
    "rule": "#D9D9D9",
    "ok": "#70AD47",
    "warn": "#BF9000",
    "fail": "#C00000",
}


def hex_to_rgb(hexstr: str) -> tuple:
    h = hexstr.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))