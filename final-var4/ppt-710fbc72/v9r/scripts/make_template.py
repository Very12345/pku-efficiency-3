# -*- coding: utf-8 -*-
"""make_template.py — generate the builtin fallback template deterministically.

The skill ships **no** .pptx file: Skill resources must be UTF-8 text only
(at most 50 files, 500KB each / 2MB total).  The fallback template is therefore
regenerated at run time by this script:

  * `make(out_path)`            — write the 16:9 template (real masters/layouts
                                  with placeholders) and normalise the zip so the
                                  same code produces byte-identical output;
  * `ensure_builtin(...)`       — used by `main.py`: reuse the shipped template
                                  when one exists, otherwise generate into
                                  `<out>/_runtime/builtin.pptx`, falling back to
                                  the system temp dir; returns an honest note
                                  instead of raising when python-pptx is absent.

Template content: default python-pptx template forced to 16:9 with clean
document properties.  Layouts: 0 Title Slide (title+subtitle), 1 Title and
Content (title+body), 2 Blank — enough for the cover / content / thankyou page
types of the deck planner.

Standalone use (e.g. to inspect the fallback template by hand):

  python scripts/make_template.py --out <dir>/builtin.pptx
"""
from __future__ import annotations

import os
import sys
import tempfile

from common import utf8_writer, portable_path


def make(out_path: str) -> str:
    """Write the fallback template to out_path (byte-identical for equal code)."""
    from pptx import Presentation
    from pptx.util import Emu

    prs = Presentation()  # default: 4:3; force 16:9
    prs.slide_width = Emu(12192000)
    prs.slide_height = Emu(6858000)

    prs.core_properties.title = "Builtin Academic Deck Template (16:9)"
    prs.core_properties.author = "ppt-710fbc72 skill"
    prs.core_properties.subject = "Builtin fallback template for academic slide adaptation"
    prs.core_properties.comments = (
        "Fallback template generated at run time by scripts/make_template.py; used only "
        "when the case provides no template and no starting deck.")

    d = os.path.dirname(out_path)
    if d:
        os.makedirs(d, exist_ok=True)
    prs.save(out_path)
    try:                      # fixed zip entry dates -> reproducible template
        import pptx_toolkit as tk
        tk.deterministic_zip(out_path, out_path + ".dztmp")
    except Exception:
        pass
    return out_path


def ensure_builtin(shipped: str = "", cache_dir: str = "", force: bool = False) -> tuple:
    """Return (path, note) for the builtin fallback template.

    Order: shipped file (if the package carries one) -> already generated copy
    in cache_dir -> generate into cache_dir -> generate into the temp dir.
    Never raises: on failure it returns ("", reason) so the caller can record
    an honest uncertainty entry and continue with the case template chain.
    """
    if shipped and os.path.exists(shipped) and not force:
        return shipped, "shipped-in-package"

    targets = []
    if cache_dir:
        targets.append(os.path.join(cache_dir, "builtin.pptx"))
    targets.append(os.path.join(tempfile.gettempdir(), "academic-slide-adapt", "builtin.pptx"))

    for target in targets:
        if os.path.exists(target) and not force:
            return target, f"reused-generated:{portable_path(target)}"
    for target in targets:
        try:
            make(target)
            return target, f"generated-at-runtime:{portable_path(target)}"
        except Exception as exc:
            last = f"{type(exc).__name__}: {exc}"
    return "", (f"builtin fallback template unavailable ({last}); the template chain then "
                "contains only the case template / starting deck")


def main(argv=None):
    utf8_writer()
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="",
                    help="output .pptx path (default: <out-dir>/builtin.pptx in the temp dir)")
    ap.add_argument("--cache-dir", default="",
                    help="use ensure_builtin() with this cache dir instead of --out")
    ap.add_argument("--force", action="store_true", help="regenerate even if a file exists")
    a = ap.parse_args(argv)

    if a.cache_dir:
        p, note = ensure_builtin(cache_dir=a.cache_dir, force=a.force)
        if not p:
            print(f"make-template FAILED: {note}", file=sys.stderr)
            return 1
        print(f"builtin template ready: {portable_path(p)} ({note})")
        return 0

    out = a.out or os.path.join(tempfile.gettempdir(), "academic-slide-adapt", "builtin.pptx")
    make(out)
    print(f"builtin template written: {portable_path(out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
