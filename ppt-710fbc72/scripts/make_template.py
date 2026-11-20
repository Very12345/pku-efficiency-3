# -*- coding: utf-8 -*-
"""make_template.py — regenerate the builtin fallback template deterministically.

Builtin template = default python-pptx template forced to 16:9 with clean
document properties.  It provides real masters/layouts with placeholders that
the template-adapter can inherit from; layouts: 0 Title Slide (title+subtitle),
1 Title and Content (title+body), 2 Blank.

Regenerate after any change:

  python scripts/make_template.py --out templates/builtin.pptx
"""
from __future__ import annotations

import os
import sys
from common import utf8_writer, skill_root


def make(out_path: str) -> str:
    from pptx import Presentation
    from pptx.util import Emu

    prs = Presentation()  # default: 4:3; force 16:9
    prs.slide_width = Emu(12192000)
    prs.slide_height = Emu(6858000)

    prs.core_properties.title = "Builtin Academic Deck Template (16:9)"
    prs.core_properties.author = "ppt-710fbc72 skill"
    prs.core_properties.subject = "Builtin fallback template for academic slide adaptation"
    prs.core_properties.comments = (
        "Fallback template committed inside the skill; used only when the case "
        "provides no template and no starting deck.")

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    prs.save(out_path)
    return out_path


def main(argv=None):
    utf8_writer()
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=os.path.join(skill_root(), "templates", "builtin.pptx"))
    a = ap.parse_args(argv)
    p = make(a.out)
    print(f"builtin template written: {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())