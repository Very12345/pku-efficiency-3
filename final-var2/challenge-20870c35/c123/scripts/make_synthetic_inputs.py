#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_synthetic_inputs.py — regenerate the *example case* binary inputs at run time.

Why this file exists
--------------------
The runtime contract allows only UTF-8 text resources in the package
("at most 50 UTF-8 text files, 500KB each and 2MB total, no symlinks"), so the
example case ships **no** binary: the demo PDF (the PDF-parsing path) and the
demo figure (the figure-binding path) are generated on demand by this script.
Nothing here is real research data — every generated file carries a SYNTHETIC
stamp, and the renderer is pure geometry (no fabricated measurements).

What it writes (default target: <skill>/examples/materials)
  dataset_card.pdf   minimal, dependency-free PDF (hand-built, deterministic)
                     with a synthetic dataset-card text layer so the optional
                     pypdf path of evidence.py has something real to parse
  fig2.png           schematic placeholder figure for "Fig. 2" (pure geometry,
                     clearly stamped as a synthetic sketch)
  synthetic_template.pptx   (only with --template, needs python-pptx) a tiny
                     master/layout deck used to exercise the template-adapt
                     branch of deck_builder.py

Usage:
  python make_synthetic_inputs.py [--out DIR] [--force] [--template] [--quiet]

Exit codes: 0 = all requested inputs exist after the run; 1 = something failed.
"""
import argparse
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(SCRIPTS_DIR)
DEFAULT_OUT = os.path.join(SKILL_ROOT, "examples", "materials")

SYNTHETIC_STAMP = "SYNTHETIC EXAMPLE - generated placeholder, not real research data"

# ---------------------------------------------------------------------------
# minimal deterministic PDF (no third-party dependency)
# ---------------------------------------------------------------------------

DATASET_CARD_LINES = [
    SYNTHETIC_STAMP,
    "Dataset card - SynthAlign example case (demo artefact)",
    "Purpose: exercise the PDF text-extraction path of this Skill.",
    "Language pairs: de-en, fr-en, zh-en (synthetic sentence pairs).",
    "Training sentence pairs: 18400",
    "Development sentence pairs: 920",
    "Test set: CCAlign-Zh demo subset, 1200 sentence pairs",
    "Annotation: sentence-level alignments, two annotators per pair.",
    "Known issue: abbreviation-heavy samples raise the error rate to about 18%.",
    "Known issue: formula fragments are dropped by the extractor.",
    "Licence: none - this card is fabricated for the demo run only.",
]

_PDF_HEADER = "%PDF-1.4\n"


def _pdf_escape(text):
    return text.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def _pdf_content_stream(lines):
    parts = ["BT", "/F1 11 Tf", "15 TL", "56 760 Td"]
    for line in lines:
        parts.append("(%s) Tj T*" % _pdf_escape(line))
    parts.append("ET")
    return "\n".join(parts) + "\n"


def build_pdf_bytes(lines):
    """Build a one-page PDF with a Helvetica text layer.

    Hand-built on purpose: it is byte-for-byte deterministic (no creation date,
    no font subsetting) and needs no reportlab, so the demo stays reproducible
    on any host.  pypdf/PyPDF2 can extract the text layer normally.
    """
    content = _pdf_content_stream(lines).encode("latin-1", "replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"endstream",
    ]
    out = bytearray(_PDF_HEADER.encode("latin-1"))
    offsets = []
    for i, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += ("%d 0 obj\n" % i).encode("latin-1") + body + b"\nendobj\n"
    xref_at = len(out)
    out += ("xref\n0 %d\n" % (len(objects) + 1)).encode("latin-1")
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += ("%010d 00000 n \n" % off).encode("latin-1")
    out += ("trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n"
            % (len(objects) + 1, xref_at)).encode("latin-1")
    return bytes(out)


# ---------------------------------------------------------------------------
# schematic placeholder figure (pure geometry, no fabricated data)
# ---------------------------------------------------------------------------

def build_figure_png(path):
    """Draw a schematic placeholder for 'Fig. 2'.

    Deliberately NOT a data plot: three empty labelled boxes plus an arrow and a
    SYNTHETIC watermark, so nobody can mistake it for a measured result.  The
    real figure belongs to the case material supplied by the organizer.
    """
    from PIL import Image, ImageDraw

    W, H = 960, 640
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    navy, gray, light = (0x1F, 0x4E, 0x79), (0x5A, 0x5A, 0x5A), (0xF2, 0xF5, 0xF9)

    d.rectangle([0, 0, W, 46], fill=navy)
    d.text((16, 16), "Fig. 2 (schematic placeholder)", fill=(255, 255, 255))
    d.rectangle([24, 70, W - 24, H - 90], outline=gray, fill=light)

    boxes = [("mBERT-only", 70), ("SynthAlign (2k / 5k / 10k)", 360), ("Acc@1 comparison", 650)]
    for label, x in boxes:
        d.rectangle([x, 150, x + 240, 380], outline=navy, width=3)
        d.text((x + 12, 162), label, fill=navy)
        d.text((x + 12, 200), "[figure not supplied]", fill=gray)
        d.text((x + 12, 224), "real image belongs to", fill=gray)
        d.text((x + 12, 248), "the case material", fill=gray)
    for x0, x1 in ((310, 360), (600, 650)):
        d.line([x0, 265, x1, 265], fill=gray, width=3)
        d.polygon([(x1, 265), (x1 - 14, 258), (x1 - 14, 272)], fill=gray)

    d.text((30, H - 74), SYNTHETIC_STAMP, fill=(0xC0, 0x50, 0x4D))
    d.text((30, H - 52), "No measurements are encoded in this image; values live in the source text.",
           fill=gray)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    img.save(path, format="PNG", optimize=True)
    return path


# ---------------------------------------------------------------------------
# optional synthetic template deck (template-adapt branch)
# ---------------------------------------------------------------------------

def build_template_pptx(path):
    """Minimal master/layout deck (16:9) to exercise --template adaptation."""
    try:
        from pptx import Presentation
        from pptx.util import Inches
    except Exception as exc:  # noqa: BLE001
        return None, "python-pptx unavailable (%s) - template not generated" % exc
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(layout)
    slide.shapes.title.text = "SYNTHETIC TEMPLATE (demo only)"
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    prs.save(path)
    return path, ""


def main(argv=None):
    ap = argparse.ArgumentParser(description="regenerate the synthetic example inputs")
    ap.add_argument("--out", default=DEFAULT_OUT,
                    help="target directory (default: <skill>/examples/materials)")
    ap.add_argument("--force", action="store_true", help="overwrite existing files")
    ap.add_argument("--template", action="store_true",
                    help="also write synthetic_template.pptx (needs python-pptx)")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    out_dir = os.path.abspath(args.out)
    os.makedirs(out_dir, exist_ok=True)
    written, skipped, errors = [], [], []

    def _emit(name, data=None, builder=None):
        path = os.path.join(out_dir, name)
        if os.path.exists(path) and not args.force:
            skipped.append(name)
            return
        try:
            if builder is not None:
                builder(path)
            else:
                with open(path, "wb") as fh:
                    fh.write(data)
            written.append(name)
        except Exception as exc:  # noqa: BLE001
            errors.append("%s: %s" % (name, exc))

    _emit("dataset_card.pdf", data=build_pdf_bytes(DATASET_CARD_LINES))
    _emit("fig2.png", builder=build_figure_png)
    if args.template:
        tpl_path, note = build_template_pptx(os.path.join(out_dir, "synthetic_template.pptx"))
        if tpl_path:
            written.append("synthetic_template.pptx")
        else:
            errors.append(note)

    if not args.quiet:
        print("[synthetic-inputs] dir=%s" % out_dir)
        print("[synthetic-inputs] written=%s" % (written or "-"))
        print("[synthetic-inputs] skipped(existing)=%s" % (skipped or "-"))
        print("[synthetic-inputs] note=%s" % SYNTHETIC_STAMP)
        for err in errors:
            print("[synthetic-inputs] ERROR %s" % err)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
