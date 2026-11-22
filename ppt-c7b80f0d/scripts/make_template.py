# -*- coding: utf-8 -*-
"""make_template.py — generate a fallback "organizer-style" .pptx template at
RUNTIME, so the Skill package ships only text resources.

Part of the "paper-to-academic-ppt" Skill (ppt-c7b80f0d, efficiency-3).

Why runtime generation
----------------------
The runtime contract allows only UTF-8 text Skill resources, so no binary
template can travel inside this package. Official cases supply their own
template, but the bundled example (and any smoke test) needs one, and a
template is also the honest fallback when an organizer template is missing or
corrupt. This script authors that template with python-pptx: a 16:9 canvas
whose layouts carry the names the generator matches by keyword
("Title Slide" / "Section Header" / "Title and Content" / "Figure Slide" /
"Reference Slide"), plus one starter slide so that
`spec.constraints.template_mode = "replace"` has something real to remove.

Nothing here is scientific content: it is an empty layout shell.

Usage
-----
    python make_template.py [--out DIR] [--name template-example.pptx] [--no-starter]

`--out` defaults to the Skill's own `examples/` directory. When python-pptx is
unavailable the script exits 2 and prints an honest JSON reason; callers must
then fall back to the built-in layout (deckgen.template.kind = "builtin"),
which is a normal, recorded path — not an error.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)

# Layout names the generator matches by keyword (see deckgen.LAYOUT_KEYWORDS).
# index_in_default_template -> desired name
LAYOUT_RENAMES = {
    8: "Figure Slide",        # was "Picture with Caption"  -> figure hint
    5: "Reference Slide",     # was "Title Only"           -> reference/closing hint
}
REQUIRED_LAYOUT_NAMES = ["Title Slide", "Title and Content", "Figure Slide", "Reference Slide"]


def build(out_dir, name="template-example.pptx", with_starter=True):
    """Create the template. Returns an honest JSON-able report dict."""
    out_dir = os.path.abspath(out_dir)
    report = {
        "status": "ok",
        "file": None,
        "name": name,
        "out_dir": out_dir,
        "layouts": [],
        "renamed_layouts": [],
        "starter_slides": 0,
        "bytes": 0,
        "notice": ("generated at runtime from an empty layout shell; contains no "
                   "scientific content and is not an organizer template"),
        "errors": [],
    }
    try:
        from pptx import Presentation
        from pptx.util import Inches, Pt
    except Exception as exc:
        report["status"] = "unavailable"
        report["errors"].append("python-pptx not importable: %s" % exc)
        return report

    try:
        os.makedirs(out_dir, exist_ok=True)
        prs = Presentation()
        prs.slide_width = Inches(13.333)
        prs.slide_height = Inches(7.5)

        layouts = list(prs.slide_layouts)
        for idx, new_name in LAYOUT_RENAMES.items():
            if idx < len(layouts):
                cSld = getattr(layouts[idx]._element, "cSld", None)
                if cSld is not None:
                    old = layouts[idx].name
                    cSld.set("name", new_name)
                    if layouts[idx].name == new_name and old != new_name:
                        report["renamed_layouts"].append({"index": idx, "from": old,
                                                          "to": new_name})
        report["layouts"] = [l.name for l in prs.slide_layouts]

        if with_starter:
            slide = prs.slides.add_slide(prs.slide_layouts[0])
            title = subtitle = None
            for ph in slide.placeholders:
                if ph.placeholder_format.idx == 0:
                    title = ph
                elif ph.placeholder_format.idx == 1:
                    subtitle = ph
            if title is not None:
                title.text_frame.text = "Organizer template (runtime-generated)"
            if subtitle is not None:
                subtitle.text_frame.text = ("starter slide — remove with "
                                            "template_mode=replace; layouts/master kept")
                for p in subtitle.text_frame.paragraphs:
                    for r in p.runs:
                        r.font.size = Pt(14)
            report["starter_slides"] = len(prs.slides)

        prs.core_properties.title = "Organizer template (runtime-generated)"
        prs.core_properties.subject = "paper-to-academic-ppt fallback template"
        prs.core_properties.comments = report["notice"]

        path = os.path.join(out_dir, name)
        prs.save(path)
        report["file"] = path
        report["bytes"] = os.path.getsize(path)
    except Exception as exc:  # noqa: BLE001
        report["status"] = "failed"
        report["errors"].append("template generation failed: %s" % exc)
    return report


def main(argv=None):
    import cli_io
    cli_io.harden_console()
    ap = argparse.ArgumentParser(description="generate the fallback .pptx template at runtime")
    ap.add_argument("--out", default=os.path.join(SKILL_DIR, "examples"),
                    help="output directory (default: <skill>/examples)")
    ap.add_argument("--name", default="template-example.pptx")
    ap.add_argument("--no-starter", action="store_true",
                    help="do not add the single starter slide")
    args = ap.parse_args(argv)

    rep = build(args.out, args.name, with_starter=not args.no_starter)
    missing = [n for n in REQUIRED_LAYOUT_NAMES if n not in (rep.get("layouts") or [])]
    if missing:
        rep["warnings"] = ["layout name(s) not present after generation: %s" % ", ".join(missing)]
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    if rep["status"] != "ok":
        print("WARNING: template not generated — the generator will fall back to its "
              "built-in layout and record template.kind=builtin", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
