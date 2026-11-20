# -*- coding: utf-8 -*-
"""Shared utilities for the academic-ppt-builder skill.

Self-locating: all paths inside this package are resolved from this file's
location, so the scripts run from any working directory.
"""
import os
import re
import io
import sys
import json
import hashlib
import logging
import datetime
import unicodedata

LOG = logging.getLogger("ppt-builder")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def package_root() -> str:
    """Directory containing this package (SKILL.md's directory)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def scripts_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def resolve_path(path: str, base: str | None = None) -> str:
    """Resolve *path* against *base* (or CWD) when it is relative."""
    if os.path.isabs(path):
        return os.path.abspath(path)
    return os.path.abspath(os.path.join(base or os.getcwd(), path))


def ensure_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path


def now_iso() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_write_text(path: str, text: str) -> None:
    ensure_dir(os.path.dirname(path))
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, path)


def atomic_write_json(path: str, obj) -> None:
    ensure_dir(os.path.dirname(path))
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, path)


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def setup_logging(log_path: str | None = None, verbose: bool = False) -> None:
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_path:
        ensure_dir(os.path.dirname(log_path))
        handlers.append(logging.FileHandler(log_path, encoding="utf-8"))
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=handlers,
        force=True,
    )


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def norm(s: str) -> str:
    """Normalize text for fuzzy comparisons: strip whitespace / unify width."""
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"[\s\u3000]+", "", s)
    return s.lower()


def find_numeric_tokens(text: str):
    """Distinct numeric tokens (with optional trailing % etc.) found in text."""
    tokens = set()
    for m in re.finditer(r"\d+(?:[.,]\d+)*\s*(?:%|％|倍|x|×)?", norm(text)):
        tok = m.group(0).strip()
        if tok and any(ch.isdigit() for ch in tok):
            # keep at most two trailing unit chars
            tokens.add(tok)
    return tokens


def check_claim_numbers(claim: str, material_text: str):
    """Verify every numeric token of *claim* appears in *material_text*.

    Returns (ok, missing_tokens). Missing tokens mean the slide may carry a
    number that the source does not support -> must be reported as uncertainty.
    """
    material = norm(material_text)
    missing = []
    for tok in sorted(find_numeric_tokens(claim)):
        if tok not in material:
            missing.append(tok)
    return not missing, missing


def wrap_text(text: str, font_path: str | None, size: int, max_px: int):
    """Greedy CJK-aware line wrapping for PIL previews. Returns list of lines."""
    from PIL import ImageFont
    if font_path:
        try:
            font = ImageFont.truetype(font_path, size)
        except Exception:
            font = ImageFont.load_default()
    else:
        font = ImageFont.load_default()
    lines, cur = [], ""
    for ch in text:
        trial = cur + ch
        w = font.getlength(trial)
        if w > max_px and cur:
            lines.append(cur)
            cur = ch
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------

_WIN_FONTS = "C:/Windows/Fonts"
_FONT_CANDIDATES = [
    ("Microsoft YaHei", os.path.join(_WIN_FONTS, "msyh.ttc")),
    ("Microsoft YaHei UI", os.path.join(_WIN_FONTS, "msyhl.ttc")),
    ("SimHei", os.path.join(_WIN_FONTS, "simhei.ttf")),
    ("SimSun", os.path.join(_WIN_FONTS, "simsun.ttc")),
    ("Arial", os.path.join(_WIN_FONTS, "arial.ttf")),
    ("DejaVu Sans", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
]
_FONT_CACHE = {}


def resolve_font(preferred: str | None = None):
    """Return (family_name, ttf_path|None) for the first available font.

    Falls back across candidates; returns (None, None) when nothing usable is
    found so callers can fall back to PIL's default font and log a warning.
    """
    if _FONT_CACHE:
        return tuple(_FONT_CACHE.values())  # (family, path)

    def exists(p):
        return p and os.path.isfile(p)

    if preferred:
        cand = [(preferred, resolve_font_path(preferred))]
        cand += [c for c in _FONT_CANDIDATES if c[0] != preferred]
    else:
        cand = _FONT_CANDIDATES
    for family, path in cand:
        if exists(path):
            _FONT_CACHE["family"] = family
            _FONT_CACHE["path"] = path
            return family, path
    _FONT_CACHE["family"] = None
    _FONT_CACHE["path"] = None
    return None, None


def resolve_font_path(family: str) -> str:
    """Best-effort map of a font family name to a known TTF/TTC path."""
    base = _WIN_FONTS
    table = {
        "microsoft yahei": os.path.join(base, "msyh.ttc"),
        "microsoft yahei ui": os.path.join(base, "msyhl.ttc"),
        "simhei": os.path.join(base, "simhei.ttf"),
        "simsun": os.path.join(base, "simsun.ttc"),
        "黑体": os.path.join(base, "simhei.ttf"),
        "宋体": os.path.join(base, "simsun.ttc"),
        "arial": os.path.join(base, "arial.ttf"),
        "consolas": os.path.join(base, "consola.ttf"),
        "times new roman": os.path.join(base, "times.ttf"),
    }
    return table.get(norm(family), os.path.join(base, "msyh.ttc"))


def set_run_font(run, family: str) -> None:
    """Set latin + east-asian + complex-script typefaces on a pptx run."""
    run.font.name = family
    rPr = run._r.get_or_add_rPr()
    from pptx.oxml.ns import qn
    for tag in ("a:ea", "a:cs"):
        el = rPr.find(qn(tag))
        if el is None:
            el = rPr.makeelement(qn(tag), {})
            rPr.append(el)
        el.set("typeface", family)


def hex_color(hexstr: str, fallback="1F4E79") -> str:
    m = re.search(r"[0-9A-Fa-f]{6}", hexstr or "")
    return m.group(0) if m else fallback