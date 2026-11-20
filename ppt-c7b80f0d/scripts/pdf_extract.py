# -*- coding: utf-8 -*-
"""pdf_extract.py — extract text (page-tagged) and figures from a paper PDF.

Part of the "paper-to-academic-ppt" Skill.

Used by main.py so the Skill reads the *actual* PDF file instead of assuming
content from labels (Runtime contract). Library strategy (first available wins):
    1. PyMuPDF (fitz)  — best text + image extraction
    2. pypdf           — text extraction only (pypdf>=3.11 also exposes images)
    3. pdfplumber      — text extraction only
If none of them is installed the caller is told honestly; the agent may then
extract text with the harness's own PDF reader and pass it in.

Outputs under out_dir:
    text/<basename>.txt        page-tagged text, page markers "[PAGE n]"
    images/fig-p<page>-<i>.*   extracted figure images (per page, xref order)
    extract_report.json        honest record: pages, chars, images, tool, errors

No scientific claims are made here: this is a mechanical extraction layer.
"""
from __future__ import annotations

import json
import os
import sys


def _tool_snapshot():
    saw = {"fitz": False, "pypdf": False, "pdfplumber": False}
    try:
        import fitz  # noqa: F401
        saw["fitz"] = True
    except Exception:
        pass
    try:
        import pypdf  # noqa: F401
        saw["pypdf"] = True
    except Exception:
        pass
    try:
        import pdfplumber  # noqa: F401
        saw["pdfplumber"] = True
    except Exception:
        pass
    return saw


def extract_pdf(pdf_path, out_dir):
    """Extract page-tagged text + images. Returns a JSON-able report dict."""
    out_dir = os.path.abspath(out_dir)
    tools = _tool_snapshot()
    os.makedirs(os.path.join(out_dir, "text"), exist_ok=True)
    os.makedirs(os.path.join(out_dir, "images"), exist_ok=True)
    report = {
        "pdf": os.path.abspath(pdf_path),
        "pages_parsed": 0,
        "text_chars": 0,
        "images_extracted": 0,
        "tool": None,
        "tool_available": tools,
        "errors": [],
        "note": "mechanical extraction only; numbers/claims must still be checked against the original",
    }
    if not os.path.isfile(pdf_path):
        report["errors"].append("pdf_not_found: %s" % pdf_path)
        report["status"] = "failed_pdf_not_found"
        return report

    base = os.path.splitext(os.path.basename(pdf_path))[0]
    text_path = os.path.join(out_dir, "text", base + ".txt")

    try:
        import fitz  # PyMuPDF

        doc = fitz.open(pdf_path)
        report["tool"] = "pymupdf"
        if doc.is_encrypted:
            try:
                doc.authenticate("")
            except Exception:
                report["errors"].append("pdf_encrypted: cannot open encrypted pdf")
                report["status"] = "failed_pdf_encrypted"
                return report
        parts = []
        for pno in range(len(doc)):
            page = doc[pno]
            parts.append("[PAGE %d]" % (pno + 1))
            parts.append(page.get_text("text"))
        clean = "\n".join(parts)
        with open(text_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(clean)
        report["pages_parsed"] = len(doc)
        report["text_chars"] = len(clean)
        # image extraction
        idx = 0
        for pno in range(len(doc)):
            for img in doc[pno].get_images(full=True):
                try:
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    if pix.n - pix.alpha > 3:  # CMYK -> RGB
                        pix = fitz.Pixmap(fitz.csRGB, pix)
                    ext = "png" if pix.alpha else "png"
                    out_img = os.path.join(out_dir, "images",
                                           "fig-p%02d-%02d.png" % (pno + 1, idx))
                    pix.save(out_img)
                    idx += 1
                except Exception as exc:
                    report["errors"].append("image_xref_%s: %s" % (img[0], exc))
        report["images_extracted"] = idx
        doc.close()
        report["status"] = "ok"
        report["text_file"] = os.path.relpath(text_path, out_dir)
        report["image_dir"] = "images"
        return report
    except Exception as exc:
        report["errors"].append("pymupdf_error: %s" % exc)

    try:
        import pypdf

        reader = pypdf.PdfReader(pdf_path)
        report["tool"] = "pypdf"
        if reader.is_encrypted:
            report["errors"].append("pdf_encrypted")
            report["status"] = "failed_pdf_encrypted"
            return report
        parts = []
        for i, page in enumerate(reader.pages):
            parts.append("[PAGE %d]" % (i + 1))
            parts.append(page.extract_text() or "")
        clean = "\n".join(parts)
        with open(text_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(clean)
        report["pages_parsed"] = len(reader.pages)
        report["text_chars"] = len(clean)
        report["images_extracted"] = 0  # pypdf image API varies by version
        report["note"] = "pypdf text layer only; image extraction skipped (see limitations)"
        report["status"] = "ok"
        report["text_file"] = os.path.relpath(text_path, out_dir)
        return report
    except Exception as exc:
        report["errors"].append("pypdf_error: %s" % exc)

    try:
        import pdfplumber

        report["tool"] = "pdfplumber"
        parts = []
        n_pages = 0
        with pdfplumber.open(pdf_path) as pdf:
            n_pages = len(pdf.pages)
            for i, page in enumerate(pdf.pages):
                parts.append("[PAGE %d]" % (i + 1))
                parts.append(page.extract_text() or "")
        clean = "\n".join(parts)
        with open(text_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(clean)
        report["pages_parsed"] = n_pages
        report["text_chars"] = len(clean)
        report["status"] = "ok"
        report["text_file"] = os.path.relpath(text_path, out_dir)
        return report
    except Exception as exc:
        report["errors"].append("pdfplumber_error: %s" % exc)

    report["status"] = "failed_no_pdf_library"
    report["errors"].append(
        "no pdf library available (tried fitz/pypdf/pdfplumber); "
        "extract text with the harness PDF reader and pass it via a .txt material")
    return report


def main(argv=None):
    import argparse

    ap = argparse.ArgumentParser(description="extract text+images from a paper PDF")
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    rep = extract_pdf(args.pdf, args.out)
    print(json.dumps(rep, ensure_ascii=False, indent=2, default=str))
    if not (rep["status"] == "ok" and rep["text_chars"] > 0):
        print("WARNING: extraction incomplete — see status/errors above", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())