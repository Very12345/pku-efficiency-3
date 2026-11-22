#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Font stack probing for schematic labels (CJK + Latin + symbol).

Scientific figures mix gene/protein names (Latin), Chinese annotations and
units (CJK), and formula-ish tokens (Greek letters, ×, →, µ, ²…). A label
that renders as tofu boxes is a figure defect, so the pipeline resolves a
font stack that actually exists on the machine BEFORE rendering and reports
the verdict honestly (the editable SVG always keeps the real <text>; only
the bitmap/PDF mirror depends on the OS font).

This module is the counterpart of the high-score pipeline role `textfont`:
it owns everything font-related and is reused by render.py and checks.py so
the resolved family is reported once in result.json.

CLI:
    python textfont.py --list        # list candidate families & verdict
    python textfont.py --probe       # machine-readable probe (JSON)

Only the Python standard library is used (matplotlib font manager).
"""

import argparse
import json
import os
import sys

try:  # narrow Windows consoles (GBK) must not crash --help or log output
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")
except Exception:
    pass


CJK_CANDIDATES = [
    ("Microsoft YaHei", ["microsoft yahei"]),
    ("SimHei", ["simhei"]),
    ("SimSun", ["simsun", "songti"]),
    ("Noto Sans CJK SC", ["noto sans cjk"]),
    ("Noto Sans SC", ["noto sans sc"]),
    ("WenQuanYi Zen Hei", ["wenquanyi"]),
    ("PingFang SC", ["pingfang"]),
]

LATIN_LIKE = ("DejaVu Sans", "Arial", "Helvetica")


def _mpl_ttflist():
    try:
        from matplotlib import font_manager
        if hasattr(font_manager, "fontManager") and \
                hasattr(font_manager.fontManager, "ttflist"):
            return sorted({(f.name or "") for f in
                           font_manager.fontManager.ttflist})
        return []
    except Exception:
        return []


def resolve_font_stack():
    """Return (family, ok_cjk). Picks the best available CJK-capable font
    so Chinese annotations render in PNG/PDF; falls back to a Latin font
    with ok_cjk=False when no CJK font is installed (SVG still keeps all
    text — see SKILL.md D7)."""
    names = _mpl_ttflist()
    low = {n.lower() for n in names}
    # 1) exact CJK candidates in preference order
    for fam, frags in CJK_CANDIDATES:
        if any(x in low for x in frags) or fam.lower() in low:
            return fam, True
    # 2) any installed family containing a CJK fragment
    for n in names:
        nl = n.lower()
        if any(f in nl for f in ("cjk", "hei", "yahei", "song", "kai",
                                 "ming", "wenquanyi", "pingfang", "noto sans sc")):
            return n, True
    # 3) Latin fallback
    for fam in LATIN_LIKE:
        if fam.lower() in low:
            return fam, False
    if names:
        return sorted(names)[0], False
    return "DejaVu Sans", False


def probe():
    """Machine-readable font probe dict (deterministic ordering)."""
    names = _mpl_ttflist()
    fam, ok_cjk = resolve_font_stack()
    latin = sorted(n.lower() for n in names
                   if any(x in n.lower() for x in LATIN_LIKE))
    return {
        "installed_family_count": len(names),
        "installed_family_sample": names[:12],
        "cjk_candidates": [ {"family": fam2, "installed": (
            any(f in {n.lower() for n in names} for f in frags)
            or fam2.lower() in {n.lower() for n in names})}
            for fam2, frags in CJK_CANDIDATES],
        "latin_like": latin[:8],
        "resolved": {"family": fam, "cjk_ok": ok_cjk},
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    grp = ap.add_mutually_exclusive_group()
    grp.add_argument("--list", action="store_true",
                     help="list candidate families & verdict (human)")
    grp.add_argument("--probe", action="store_true",
                     help="machine-readable probe (JSON)")
    args = ap.parse_args(argv)

    if args.list:
        fam, ok = resolve_font_stack()
        names = _mpl_ttflist()
        print("installed font families (matplotlib): %d" % len(names))
        for fam2, frags in CJK_CANDIDATES:
            mark = "[x]" if (any(
                f in {n.lower() for n in names} for f in frags)
                or fam2.lower() in {n.lower() for n in names}) else "[ ]"
            print("  %s %s" % (mark, fam2))
        print("resolved: family=%s cjk_ok=%s" % (fam, ok))
        return 0
    print(json.dumps(probe(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())