# -*- coding: utf-8 -*-
"""Material reading: load case.json, task.md and the actual source materials.

The skill must read *actual files* instead of assuming content from labels.
This module therefore resolves every input listed in case.json against the
case file's directory, reads it and extracts a structured Material view:
sections, tables, figure/table mentions and the full normalized text used for
claim cross-checking.
"""
import csv
import json
import os
import re
import html
from dataclasses import dataclass, field

from common import LOG, resolve_path, atomic_write_json, ensure_dir

TEXT_LIMIT_BYTES = 400_000  # per material file; larger files are truncated + noted

FIG_RE = re.compile(r"(?:图\s*[一二三四五六七八九十百\d]+(?:\s*[a-z])?|(?:Figure|Fig\.?)\s*\d+)", re.IGNORECASE)
TBL_RE = re.compile(r"(?:表\s*[一二三四五六七八九十百\d]+|(?:Table)\s*\d+)", re.IGNORECASE)


@dataclass
class Section:
    id: str
    heading: str
    text: str


@dataclass
class Table:
    id: str
    caption: str
    columns: list
    rows: list          # list of dict per row
    source_file: str = ""


@dataclass
class FigureMention:
    ref: str
    context: str


@dataclass
class Material:
    case_id: str = ""
    title: str = ""
    text: str = ""                      # normalized-ish full text (joined)
    sections: list = field(default_factory=list)
    tables: list = field(default_factory=list)
    figures: list = field(default_factory=list)
    source_files: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    numbers: set = field(default_factory=set)

    def find_sections(self, *keywords):
        """Sections whose heading or opening text matches any keyword
        (heading matches rank above body matches; document order breaks ties)."""
        kws = [norm(x) for x in keywords]
        best, best_score = [], 0
        for s in self.sections:
            head = norm(s.heading)
            body = norm(s.text[:400])
            score = (2 if any(k in head for k in kws) else 0) + \
                    (1 if any(k in body for k in kws) else 0)
            if score > best_score:
                best_score = score
                best = [s]
            elif score and score == best_score:
                best.append(s)
        return best

    def find_first_text(self, *keywords, fallback=""):
        """Return the full text of the best matching section (heading-match
        wins over body-only; earliest section wins ties)."""
        kws = [norm(x) for x in keywords]
        best, best_score = None, 0
        for s in self.sections:
            head = norm(s.heading)
            body = norm(s.text[:400])
            score = (2 if any(k in head for k in kws) else 0) + \
                    (1 if any(k in body for k in kws) else 0)
            if score > best_score:
                best_score, best = score, s
        if best is not None and best.text.strip():
            return best.text.strip()
        return fallback


def norm(s):
    import unicodedata
    import re as _re
    return _re.sub(r"[\s\u3000]+", "", unicodedata.normalize("NFKC", s or "")).lower()


def _strip_html(text):
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"<style.*?</style>", "", text, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return html.unescape(text)


def read_text_file(path):
    """Read a text-ish file returning (text, warning)."""
    _, ext = os.path.splitext(path)
    ext = ext.lower()
    raw = None
    with open(path, "rb") as f:
        head = f.read(2)
    enc = "utf-8-sig" if head == b"\xff\xfe" else "utf-8"
    with open(path, "r", encoding=enc, errors="replace") as f:
        raw = f.read(TEXT_LIMIT_BYTES)
    truncated = False
    if os.path.getsize(path) > TEXT_LIMIT_BYTES:
        truncated = True
    if ext == ".html" or ext == ".htm":
        raw = _strip_html(raw)
    warn = "file truncated at %d bytes" % TEXT_LIMIT_BYTES if truncated else ""
    return raw, warn


def read_csv_table(path):
    """Read a CSV into a Table (first row = header)."""
    with open(path, "r", encoding="utf-8-sig", errors="replace", newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        return None, "csv is empty"
    header = [c.strip() for c in rows[0]]
    data = []
    for r in rows[1:]:
        if r and any(c.strip() for c in r):
            data.append(dict(zip(header, [c.strip() for c in r])))
    return Table(id=os.path.basename(path), caption=os.path.basename(path),
                 columns=header, rows=data, source_file=path), ""


def try_read_pdf_text(path):
    """Best-effort PDF text extraction. Returns (text, warning)."""
    for mod in ("fitz", "pypdf", "PyPDF2", "pdfplumber"):
        try:
            if mod == "fitz":
                import fitz
                doc = fitz.open(path)
                parts = [p.get_text() for p in doc]
                return "\n".join(parts), ""
            if mod == "pypdf":
                from pypdf import PdfReader
                return "\n".join((p.extract_text() or "") for p in PdfReader(path).pages), ""
            if mod == "PyPDF2":
                from PyPDF2 import PdfReader
                return "\n".join((p.extract_text() or "") for p in PdfReader(path).pages), ""
            if mod == "pdfplumber":
                import pdfplumber
                with pdfplumber.open(path) as pdf:
                    return "\n".join((p.extract_text() or "") for p in pdf.pages), ""
        except Exception as e:  # noqa: BLE001
            LOG.warning("pdf module %s failed: %s", mod, e)
    return "", "PDF 文本抽取不可用（无 fitz/pypdf/pdfplumber）；请用 Agent 读取 PDF 并把原文抽到 /app/work/materials/*.txt"


def extract_sections(text):
    """Split plain/markdown text into sections by markdown or Chinese numbering.
    Lines starting with '===' are file banners inserted by read_material and are
    skipped entirely (they are not content)."""
    lines = text.splitlines()
    sections = []
    cur_heading, cur_buf = "前言", []
    heading_re = re.compile(r"^(#{1,6})\s*(.*)$|^([一二三四五六七八九十]+)[、.．]\s*(.*)$")

    def flush():
        body = "\n".join(cur_buf).strip()
        if body or cur_heading:
            sections.append(Section(id="s%02d" % len(sections), heading=cur_heading.strip(), text=body))

    for ln in lines:
        stripped = ln.strip()
        if stripped.startswith("==="):
            continue
        m = heading_re.match(stripped)
        if m and len(stripped) <= 60:
            flush()
            cur_heading = (m.group(2) or m.group(4) or "").strip()
            cur_buf = []
        else:
            cur_buf.append(ln)
    flush()

    # First meaningful line as title (usually a '# Title' or the very first line)
    title = sections[0].heading if sections else ""
    if not title or title == "前言":
        for ln in lines[:10]:
            s = ln.strip().strip("#").strip()
            if s and not s.startswith("===") and len(s) < 120 and "===" not in s:
                title = s
                break
    return title, sections


def collect_mentions(text):
    figs = [m.group(0) for m in FIG_RE.finditer(text)]
    tbls = [m.group(0) for m in TBL_RE.finditer(text)]
    seen_f, seen_t = [], []
    for x in figs:
        if x not in seen_f:
            seen_f.append(x)
        if len(seen_f) >= 24:
            break
    for x in tbls:
        if x not in seen_t:
            seen_t.append(x)
        if len(seen_t) >= 24:
            break
    return seen_f, seen_t


def load_material_text(path):
    """Dispatch on file extension -> raw text."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return try_read_pdf_text(path)
    if ext in (".csv",):
        return "", "csv handled separately"
    return read_text_file(path)


def read_material(case_dir, input_spec):
    """Read all listed materials into one Material object.

    input_spec: {"task_md": "...", "material": ["a.md", "b.csv"]} where paths
    are relative to case_dir (or absolute). Preserves order.
    """
    warnings = []
    text_parts = []
    tables = []
    source_files = []

    def add_file(path, role):
        abs_path = resolve_path(path, case_dir)
        if not os.path.isfile(abs_path):
            warnings.append("输入缺失：%s（role=%s）" % (path, role))
            return
        source_files.append({"path": abs_path, "role": role})
        ext = os.path.splitext(abs_path)[1].lower()
        if ext == ".csv":
            t, w = read_csv_table(abs_path)
            if t:
                tables.append(t)
            if w:
                warnings.append("csv %s: %s" % (path, w))
            return
        txt, w = load_material_text(abs_path)
        if w:
            warnings.append("%s: %s" % (path, w))
        if txt.strip():
            text_parts.append("=== %s (%s) ===\n%s" % (os.path.basename(path), role, txt))

    mat_list = input_spec.get("material") or []
    if isinstance(mat_list, dict):           # some cases map figure->file
        for role, p in mat_list.items():
            add_file(p, str(role))
    else:
        for i, p in enumerate(mat_list):
            add_file(p, "material-%d" % (i + 1))

    full_text = "\n\n".join(text_parts)
    title, sections = extract_sections(full_text)
    figs, _ = collect_mentions(full_text)

    mat = Material(
        title=title,
        text=full_text,
        sections=sections,
        tables=tables,
        figures=[FigureMention(ref=f, context="") for f in figs],
        source_files=source_files,
        warnings=warnings,
        numbers={n for t in (find_numbers(full_text),) for n in t},
    )
    return mat


def find_numbers(text):
    out = set()
    for m in re.finditer(r"\d+(?:[.,]\d+)*\s*(?:%|％|倍|x|×)?", text):
        out.add(m.group(0).strip())
    return out


def load_case(case_path, input_dir=None):
    """Load case.json and task.md; validate minimal fields.

    Returns (case, task_text, warnings).
    """
    case_abs = resolve_path(case_path, input_dir or os.getcwd())
    if not os.path.isfile(case_abs):
        raise FileNotFoundError("找不到 case 文件: %s" % case_abs)
    with open(case_abs, "r", encoding="utf-8-sig") as f:
        case = json.load(f)
    case_dir = os.path.dirname(case_abs)
    case.setdefault("case_id", os.path.splitext(os.path.basename(case_abs))[0])
    case.setdefault("title", case.get("case_id", "未命名案例"))
    inputs = case.get("inputs") or {}
    case.setdefault("spec", {})
    warnings = []

    task_text = ""
    task_path = inputs.get("task_md") or case.get("task_md")
    if task_path:
        abs_tp = resolve_path(str(task_path), case_dir)
        if os.path.isfile(abs_tp):
            with open(abs_tp, "r", encoding="utf-8-sig", errors="replace") as f:
                task_text = f.read()
        else:
            warnings.append("task.md 缺失: %s" % task_path)

    return case, task_text, warnings, case_abs, case_dir


def dump_work(work_dir, case, task_text, material):
    """Persist the working view (plan inputs) for traceability."""
    ensure_dir(work_dir)
    payload = {
        "case_id": case.get("case_id"),
        "title": material.title or case.get("title"),
        "sections": [{"id": s.id, "heading": s.heading, "text": s.text[:2000]}
                     for s in material.sections],
        "tables": [{"id": t.id, "caption": t.caption, "columns": t.columns,
                    "rows": t.rows[:50]} for t in material.tables],
        "figures": [f.ref for f in material.figures],
        "warnings": material.warnings,
        "task_text_head": task_text[:4000],
    }
    atomic_write_json(os.path.join(work_dir, "material_view.json"), payload)
    return payload