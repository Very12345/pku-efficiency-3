#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF text extraction for schematic materials.

The high-score pipeline for this topic runs `extract` (material → ER
candidates) after `pdftext` (PDF → clean text). This module owns the PDF
reading step and degrades honestly:

1. pypdf / PyPDF2 / fitz (PyMuPDF) when installed — best quality;
2. pure-standard-library fallback — zlib-decompress content streams and
   collect Tj / TJ text-showing operators. This covers most normal
   (unflattened, uncompressed-or-Flate) PDFs even with zero third-party
   deps, which is the documented runtime for this Skill;
3. encrypted / scanned / malformed PDFs → explicit failure details, no
   fabrication (SKILL D1 / FAILURE_MODES.md).

Output: a UTF-8 text file with [PAGE n] markers plus a probe JSON that
records which backend was used and any warnings, so the figure pipeline
can cite the extraction honestly in result.json.

CLI:
    python pdftext.py --pdf <file.pdf> --out <dir>
    # writes <dir>/<stem>.txt and <dir>/<stem>.extract.json
Only the Python standard library is required.
"""

import argparse
import json
import os
import re
import sys
import zlib

_HEAD_PDF = b"%PDF-"


def _iter_streams(raw):
    """Yield (stream_object_number, raw_stream_bytes) for each stream in a
    raw PDF byte blob using object headers."""
    rx = re.compile(rb"(?:^|\n)\s*(\d+)\s+(\d+)\s+obj\b")
    for mobj in rx.finditer(raw):
        onum = mobj.group(1)
        start = mobj.end()
        endm = re.search(rb"\bendobj\b", raw[start:start + 4_000_000])
        if not endm:
            continue
        yield int(onum), raw[start:start + endm.start()]


def _decode_stream(blob):
    """Return (text, ok) after applying FlateDecode if present."""
    try:
        data = blob
        if b"/FlateDecode" in data or b"/Fl" in data:
            m = re.search(rb"stream\r?\n", data)
            if m:
                start = m.end()
                end = data.find(b"endstream", start)
                if end < 0:
                    return "", False
                try:
                    data = zlib.decompress(data[start:end])
                except zlib.error:
                    return "", False
        return data, True
    except Exception:
        return "", False


_LIT = re.compile(rb"\((?:\\.|[^\\()])*\)")
_TJ_ARR = re.compile(rb"\[([^\]]*)\]\s*TJ")
_HEX_STR = re.compile(rb"<([0-9A-Fa-f\s]+)>")
_ESCAPES = {
    b"\\n": b"\n", b"\\r": b"\r", b"\\t": b"\t",
    b"\\(": b"(", b"\\)": b")", b"\\\\": b"\\",
}


def _unescape_pdf(bs):
    out = []
    i = 0
    while i < len(bs):
        c = bs[i:i + 1]
        if c == b"\\" and i + 1 < len(bs):
            pair = bs[i:i + 2]
            out.append(_ESCAPES.get(pair, pair))
            i += 2
        else:
            out.append(c)
            i += 1
    return b"".join(out)


def _decode_literal(bs):
    """Interpret a PDF literal string's bytes as text (heuristic: try
    UTF-16BE BOM, UTF-16LE BOM, then latin-1 so bytes never fail)."""
    if bs.startswith(b"\xfe\xff"):
        try:
            return bs[2:].decode("utf-16-be", errors="replace")
        except Exception:
            pass
    if bs.startswith(b"\xff\xfe"):
        try:
            return bs[2:].decode("utf-16-le", errors="replace")
        except Exception:
            pass
    try:
        return bs.decode("utf-8", errors="replace")
    except Exception:
        return bs.decode("latin-1", errors="replace")


def _extract_operators(stream_text):
    """Collect text from Tj / TJ operators in a decoded content stream.
    Returns a list of strings in document order."""
    out = []
    # single literals directly followed by a Tj operator
    for m in _LIT.finditer(stream_text):
        nxt = stream_text[m.end():m.end() + 8]
        if b"Tj" in nxt:
            s = _unescape_pdf(m.group(0)[1:-1])
            if s:
                out.append(_decode_literal(s))
    # TJ arrays: concatenate the literals in the array body
    for m in _TJ_ARR.finditer(stream_text):
        body = m.group(1)
        for p in _LIT.finditer(body):
            s = _unescape_pdf(p.group(0)[1:-1])
            if s:
                out.append(_decode_literal(s))
    return out


def stdlib_extract(raw):
    """Pure-stdlib extractor: collect text from every content stream and
    associate it with /Type /Page objects. Content streams are usually
    referenced from a page object via /Contents, so we cannot require
    /Type /Page on the stream's own object — we collect text from all
    FlateDecoded streams instead.
    Returns (pages:list[str], warnings:list[str])."""
    pages = []
    warnings = []
    n_page_objs = 0
    per_stream_text = []
    for onum, blob in _iter_streams(raw):
        if b"/Type /Page" in blob:
            n_page_objs += 1
        decoded, ok = _decode_stream(blob)
        if not ok or not decoded:
            continue
        toks = _extract_operators(decoded)
        if toks:
            per_stream_text.append(" ".join(toks).strip())
    if per_stream_text:
        # streams are in document order; pages == list of joined streams
        # (best effort: if the PDF has N page objects, group stream text
        # into N buckets by round-robin proportional order)
        text_in_order = [t for t in per_stream_text if t]
        if n_page_objs and len(text_in_order) >= n_page_objs:
            step = max(1, len(text_in_order) // n_page_objs)
            for i in range(0, len(text_in_order), step):
                pages.append(" ".join(text_in_order[i:i + step]).strip())
        else:
            pages = text_in_order
    if not pages or not any(p for p in pages):
        warnings.append(
            "no text-showing operators found in any page stream — the PDF "
            "may be scanned images, or text may live in unsupported "
            "compression (e.g. LZW/JPX). OCR/vector parsing is out of "
            "scope; see FAILURE_MODES.md.")
    return [p for p in pages if p], warnings


try:  # third-party backends, best first
    import fitz  # PyMuPDF  # noqa: F401
    _BACKEND = "fitz"
except Exception:
    try:
        import pypdf  # noqa: F401
        _BACKEND = "pypdf"
    except Exception:
        try:
            import PyPDF2  # noqa: F401
            _BACKEND = "PyPDF2"
        except Exception:
            _BACKEND = None


def extract_pdf(path):
    """Return {"pages": [str], "backend": str, "warnings": [str]}."""
    with open(path, "rb") as fh:
        raw = fh.read(24_000_000)
    if not raw.startswith(_HEAD_PDF):
        raise ValueError("not a PDF (missing %%PDF- header): %s" % path)
    if b"/Encrypt" in raw[:400_000]:
        raise ValueError(
            "PDF is encrypted (%s); text extraction without a password is "
            "not attempted. Ask the organizer for a decrypted copy or "
            "extract text with a PDF tool before running this skill."
            % os.path.basename(path))

    if _BACKEND == "fitz":
        import fitz
        doc = fitz.open(path)
        pages = [doc[i].get_text("text") for i in range(len(doc))]
        doc.close()
        warns = (["extraction via PyMuPDF (fitz)"] if pages else
                 ["fitz returned no text — PDF may be scanned images"])
        return {"pages": pages, "backend": "fitz", "warnings": warns}

    if _BACKEND in ("pypdf", "PyPDF2"):
        mod = __import__(_BACKEND)
        reader = mod.PdfReader if _BACKEND == "pypdf" else mod.PdfFileReader
        r = reader(path)
        pages = []
        try:
            n = len(r.pages)
        except Exception:
            n = r.getNumPages()
        for i in range(n):
            try:
                pages.append(r.pages[i].extract_text() or "")
            except Exception:
                try:
                    pages.append(r.getPage(i).extractText() or "")
                except Exception:
                    pages.append("")
        return {"pages": pages, "backend": _BACKEND,
                "warnings": ["extraction via %s" % _BACKEND]}

    pages, warns = stdlib_extract(raw)
    warns.insert(0, "no third-party PDF library found — used the pure-"
                    "standard-library fallback (zlib + Tj/TJ operators); "
                    "layout is NOT reconstructed")
    return {"pages": pages, "backend": "stdlib", "warnings": warns}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pdf", required=True, help="path to the PDF")
    ap.add_argument("--out", required=True,
                    help="output directory for <stem>.txt + <stem>.extract.json")
    args = ap.parse_args(argv)

    pdf = os.path.abspath(args.pdf)
    if not os.path.isfile(pdf):
        print("FATAL: pdf not found: %s" % pdf)
        return 2
    out_dir = os.path.abspath(args.out)
    os.makedirs(out_dir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(pdf))[0]
    try:
        info = extract_pdf(pdf)
    except (ValueError, OSError) as exc:
        print("FATAL: %s" % exc)
        return 2

    body = []
    for i, page in enumerate(info["pages"], 1):
        body.append("[PAGE %d]" % i)
        body.append(page)
    txt_path = os.path.join(out_dir, stem + ".txt")
    with open(txt_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(body) + "\n")
    info["input_pdf"] = os.path.basename(pdf)
    info["output_txt"] = os.path.basename(txt_path)
    info["page_count"] = len(info["pages"])
    info["char_count"] = sum(len(p) for p in info["pages"])
    probe_path = os.path.join(out_dir, stem + ".extract.json")
    with open(probe_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(info, ensure_ascii=False, indent=2) + "\n")

    print("backend:      %s" % info["backend"])
    print("pages:        %d" % info["page_count"])
    print("chars:        %d" % info["char_count"])
    for w in info["warnings"]:
        print("WARN:         %s" % w)
    print("wrote:        %s" % txt_path)
    print("wrote:        %s" % probe_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())