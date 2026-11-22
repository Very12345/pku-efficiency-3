# -*- coding: utf-8 -*-
"""assetkit.py — material & asset extraction layer for paper-to-academic-ppt.

Part of the "paper-to-academic-ppt" Skill v2 (ppt-c7b80f0d, efficiency-3).

Layer role (mirrors the high-score 80.00 package intent: assetkit / deckgen /
ooxml_kit three-layer split):
    assetkit   = everything that turns *source material* into workable assets:
                 locate the actual paper file(s), extract page-tagged text +
                 images from a PDF, read text materials, and rebuild charts
                 from numbers the spec declares reconstructed from a table.
    deckgen    = turn a structured deck-spec into an editable .pptx.
    ooxml_kit  = OOXML-level refinement and export QA.

Honesty invariants held here:
* nothing is invented — text comes from the actual file; chart numbers come
  from spec (which the agent derived from the paper);
* PDF extraction is mechanical; tool choice and failures are recorded;
* a missing chart backend is a recorded skip, never a hand-drawn stand-in.
"""
from __future__ import annotations

import json
import os
import re
import sys


# --------------------------------------------------------------------------- #
# PDF extraction (PyMuPDF -> pypdf -> pdfplumber, then honest failure)
# --------------------------------------------------------------------------- #
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
        idx = 0
        for pno in range(len(doc)):
            for img in doc[pno].get_images(full=True):
                try:
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    if pix.n - pix.alpha > 3:  # CMYK -> RGB
                        pix = fitz.Pixmap(fitz.csRGB, pix)
                    ext = "png"
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
        report["images_extracted"] = 0
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


# --------------------------------------------------------------------------- #
# Material discovery (actual files only, never labels)
# --------------------------------------------------------------------------- #
def _looks_like_paper_file(name):
    return name.lower().endswith((".pdf", ".txt", ".md", ".tex", ".rst"))


def discover_materials(case, materials_override, work_dir, case_dir=None):
    """Return a list of candidate paper material paths (real, readable files)."""
    paths = []
    if materials_override:
        if os.path.isdir(materials_override):
            for n in sorted(os.listdir(materials_override)):
                p = os.path.join(materials_override, n)
                if os.path.isfile(p) and _looks_like_paper_file(n):
                    paths.append(p)
        elif os.path.isfile(materials_override):
            paths.append(materials_override)

    bases = [work_dir]
    if case_dir:
        bases.append(case_dir)

    def _resolve(candidate):
        if not candidate:
            return None
        if os.path.isabs(candidate):
            return candidate if os.path.exists(candidate) else None
        for base in bases:
            joined = os.path.join(base, candidate)
            if os.path.exists(joined):
                return joined
        return None

    for key in ("material", "materials", "paper", "document", "source_pdf", "pdf"):
        val = case.get(key)
        if isinstance(val, str):
            p = _resolve(val)
            if p and p not in paths:
                paths.append(p)
        elif isinstance(val, dict):
            for sub in ("path", "paths", "path_pdf", "file", "files"):
                v = val.get(sub)
                if isinstance(v, str):
                    p = _resolve(v)
                    if p and p not in paths:
                        paths.append(p)
                elif isinstance(v, list):
                    for x in v:
                        if isinstance(x, str):
                            p = _resolve(x)
                            if p and p not in paths:
                                paths.append(p)
        elif isinstance(val, list):
            for x in val:
                if isinstance(x, str):
                    p = _resolve(x)
                    if p and p not in paths:
                        paths.append(p)
    # pdfs first, then text
    paths.sort(key=lambda p: (not p.lower().endswith(".pdf"), os.path.basename(p)))
    return paths


def read_material_text(path, work_dir):
    """Read a text-like material with page markers from a PDF if possible."""
    low = path.lower()
    if low.endswith(".pdf"):
        extract_dir = os.path.join(work_dir, "extract")
        rep = extract_pdf(path, extract_dir)
        if rep.get("status") == "ok" and rep.get("text_chars", 0) > 0:
            txt = rep.get("text_file")
            full = os.path.join(extract_dir, txt)
            with open(full, encoding="utf-8", errors="replace") as fh:
                return fh.read(), rep
        return "", rep
    with open(path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    rep = {"pdf": path, "status": "ok_text", "tool": "direct-read",
           "text_chars": len(text), "pages_parsed": 0, "images_extracted": 0,
           "errors": [], "text_file": os.path.relpath(path, work_dir)}
    return text, rep


# --------------------------------------------------------------------------- #
# Reconstructed charts (matplotlib, optional; numbers come from spec)
# --------------------------------------------------------------------------- #
def make_chart(spec_fig, out_dir, width_in=6.4, height_in=4.2, dpi=110):
    """Render a chart from numbers the spec declares reconstructed from a paper
    table (kind="reconstructed_chart"). Returns {"file","png","svg"} or None."""
    data = spec_fig.get("data") or {}
    cats = data.get("categories") or []
    series = data.get("series") or []
    if not cats or not series:
        return {"file": None, "png": False, "svg": False,
                "reason": "no chart data in spec (figure may be a paper image instead)"}
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as exc:
        return {"file": None, "png": False, "svg": False, "reason": "matplotlib missing: %s" % exc}
    try:
        safe_ref = re.sub(r"[^\x00-\x7F]+", "", str(spec_fig.get("ref") or ""))
        title = safe_ref or "Reconstructed chart"
        fig, ax = plt.subplots(figsize=(width_in, height_in))
        for s in series:
            vals = s.get("values") or []
            kw = {}
            if s.get("kind") == "line":
                ax.plot(cats, vals, marker="o", label=s.get("name"), **kw)
            else:
                ax.bar(cats, vals, label=s.get("name"), alpha=0.8)
        ax.set_xlabel(" ".join(cats).title() if len(cats) > 6 else "")
        ax.set_title(_clip_text(str(title), 50), fontsize=10)
        if len(series) > 1:
            ax.legend(fontsize=8)
        ax.grid(axis="y", alpha=0.3)
        fig.tight_layout()
        base = "chart-%s" % (safe_ref or "fig").replace(" ", "_").replace(".", "")
        png_path = os.path.join(out_dir, base + ".png")
        fig.savefig(png_path, dpi=dpi)
        svg_path = None
        try:
            svg_path = os.path.join(out_dir, base + ".svg")
            fig.savefig(svg_path, format="svg")
        except Exception:
            svg_path = None
        import matplotlib as _m
        _m.pyplot.close(fig)
        return {"file": png_path, "png": True,
                "svg": os.path.basename(svg_path) if svg_path else None,
                "note": "reconstructed_from_table; numbers are those declared in spec and must match the paper table",
                "title_used": str(title)}
    except Exception as exc:
        return {"file": None, "png": False, "svg": False, "reason": "chart error: %s" % exc}


def _clip_text(text, limit):
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


# -- PDF extraction CLI (back-compat with the base package's entry point) -----
def main(argv=None):
    import argparse

    import cli_io
    cli_io.harden_console()

    ap = argparse.ArgumentParser(description="extract text+images from a paper PDF (assetkit)")
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