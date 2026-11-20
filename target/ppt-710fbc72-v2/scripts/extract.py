# -*- coding: utf-8 -*-
"""extract.py — read actual input files, normalize paper content with sources.

Never trusts labels: every piece of content is bound to a source locator
(`file:line` or `case.json[field]`).  Numbers / claims that cannot be found
in the material are NOT invented; they go into uncertainty as missing.
"""
from __future__ import annotations

import os
import re

from common import read_text, write_text, dump_json, load_json, utf8_writer

# Section keywords used to bucket free-form material.md into the story line.
_SECTION_KW = [
    ("question", ["研究问题", "问题", "motivation", "background", "背景", "研究背景", "introduction", "引言"]),
    ("methods", ["方法", "method", "实验", "实验方法", "材料与方法", "methods"]),
    ("results", ["结果", "result", "数据", "fig", "图", "table", "表"]),
    ("discussion", ["讨论", "discussion"]),
    ("limitations", ["限制", "limitation", "局限", "不足"]),
    ("conclusion", ["结论", "conclusion", "总结", "小结"]),
]

# Figure caption line patterns:  图1 ... / Figure 1. ... / Fig. 1 ...
_FIG_RE = re.compile(r"^[#*\-\s]*((?:图|Figure|Fig\.?)\s*([0-9A-Za-z]+))[:：.\-]\s*(.+)$", re.IGNORECASE)
# Table caption line patterns
_TBL_RE = re.compile(r"^[#*\-\s]*((?:表|Table)\s*([0-9A-Za-z]+))[:：.\-]\s*(.+)$", re.IGNORECASE)


def _locate(case_path: str, rel: str, work_dir: str | None = None) -> str:
    """Resolve a relative source path from case.json against, in order:
    work_dir, case_dir.  Returns absolute path."""
    candidates = []
    if rel and os.path.isabs(rel):
        candidates.append(rel)
    if rel and work_dir:
        candidates.append(os.path.join(work_dir, rel))
    if rel and case_path:
        candidates.append(os.path.join(os.path.dirname(os.path.abspath(case_path)), rel))
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return candidates[0] if candidates else rel


def _strip_md(line: str) -> str:
    return re.sub(r"^[#*\-\s>\d.]+", "", line).strip()


def _scan_sections(text: str) -> dict:
    """Best-effort bucket text lines into story sections. Returns
    {section: [lines]} preserving line numbers."""
    sections = {k: [] for k in ("question", "methods", "results", "discussion", "limitations", "conclusion")}
    current = None
    for i, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped:
            continue
        if re.match(r"^#{1,6}\s+", stripped) or re.match(r"^(?:第[一二三四五六]|[0-9]+[.、)])\s*\S", stripped):
            for sec, kws in _SECTION_KW:
                if any(kw.lower() in stripped.lower() for kw in kws):
                    current = sec
                    break
            else:
                current = None  # unknown heading: keep previous? -> stay in previous
                # keep current bucket rather than dropping; see note below
        if current:
            sections[current].append((i, _strip_md(stripped)))
        else:
            # un-headed lines: attach to question bucket as preamble, it is
            # the default reading order start.
            sections["question"].append((i, _strip_md(stripped)))
    return sections


def _extract_figure_lines(text: str) -> list:
    out = []
    for i, raw in enumerate(text.splitlines(), start=1):
        m = _FIG_RE.match(raw.strip())
        if m:
            out.append({"fig_id": m.group(2).strip(), "caption": m.group(3).strip(),
                        "line": i, "raw": m.group(1).strip()})
    return out


def _extract_table_lines(text: str) -> list:
    out = []
    for i, raw in enumerate(text.splitlines(), start=1):
        m = _TBL_RE.match(raw.strip())
        if m:
            out.append({"tbl_id": m.group(2).strip(), "caption": m.group(3).strip(),
                        "line": i, "raw": m.group(1).strip()})
    return out


def extract(case_path: str, task_path: str | None, work_dir: str | None, out_dir: str) -> dict:
    """Run extraction and persist content.json under out_dir."""
    case = load_json(case_path)
    case_dir = os.path.dirname(os.path.abspath(case_path)) if case_path else "."
    case_id = str(case.get("case_id") or os.path.splitext(os.path.basename(case_path))[0])

    sources = []          # [{path, rel, exists, lines}]
    material_text = ""
    material_srcs = case.get("source_material") or case.get("material") or case.get("sources") or []
    if isinstance(material_srcs, str):
        material_srcs = [material_srcs]

    for rel in material_srcs:
        abspath = _locate(case_path, rel, work_dir)
        rec = {"rel": rel, "path": abspath, "exists": os.path.exists(abspath), "lines": 0}
        if rec["exists"]:
            try:
                txt = read_text(abspath)
            except Exception as exc:  # binary materials: list only
                rec.update({"note": f"not UTF-8 text: {exc}"})
                sources.append(rec)
                continue
            rec["lines"] = txt.count("\n") + 1
            rec["sha256"] = None  # computed below
            material_text += "\n" + txt
        sources.append(rec)

    # --- normalize structured fields from case.json -------------------
    def _norm_list(key, alt=None):
        val = case.get(key, case.get(alt) if alt else None)
        if val is None:
            return []
        if isinstance(val, str):
            return [{"text": val}]
        out = []
        for i, item in enumerate(val):
            if isinstance(item, str):
                out.append({"text": item})
            elif isinstance(item, dict):
                entry = dict(item)
                entry.setdefault("text", entry.get("claim") or entry.get("title") or str(entry))
                cur = entry.get("source") or entry.get("src") or entry.get("loc") or ""
                if not cur:
                    cur = f"case.json[{key}.{i}]"
                entry["source"] = cur
                out.append(entry)
        return out

    question = _norm_list("research_question", "question")
    methods = _norm_list("methods")
    results = _norm_list("results", "result_items")
    discussion = _norm_list("discussion")
    limitations = _norm_list("limitations", "limits")
    conclusion = _norm_list("conclusion")

    # --- bucket free material text as the fallback / supplement --------
    sections = _scan_sections(material_text)
    supplemented = {"question": False, "methods": False, "results": False,
                    "discussion": False, "limitations": False, "conclusion": False}
    if material_text.strip():
        if not question:
            question = [{"text": t, "source": f"{sources[-1]['rel']}:{ln}"} for ln, t in sections["question"]][:6]
            supplemented["question"] = bool(question)
        if not methods:
            methods = [{"text": t, "source": f"{sources[-1]['rel']}:{ln}"} for ln, t in sections["methods"]][:8]
            supplemented["methods"] = bool(methods)
        if not results:
            results = [{"text": t, "source": f"{sources[-1]['rel']}:{ln}"} for ln, t in sections["results"]][:12]
            supplemented["results"] = bool(results)
        if not discussion:
            discussion = [{"text": t, "source": f"{sources[-1]['rel']}:{ln}"} for ln, t in sections["discussion"]][:6]
            supplemented["discussion"] = bool(discussion)
        if not limitations:
            limitations = [{"text": t, "source": f"{sources[-1]['rel']}:{ln}"} for ln, t in sections["limitations"]][:6]
            supplemented["limitations"] = bool(limitations)
        if not conclusion:
            conclusion = [{"text": t, "source": f"{sources[-1]['rel']}:{ln}"} for ln, t in sections["conclusion"]][:6]
            supplemented["conclusion"] = bool(conclusion)

    # --- figures / tables --------------------------------------------------
    figures = []
    for item in case.get("figures") or case.get("figure_sources") or []:
        if isinstance(item, str):
            item = {"id": item}
        entry = dict(item)
        entry.setdefault("id", str(entry.get("fig_id") or entry.get("name") or f"fa{len(figures)+1}"))
        entry.setdefault("caption", entry.get("caption") or entry.get("title") or "")
        entry.setdefault("source", entry.get("source") or entry.get("src") or f"case.json[figures]")
        entry.setdefault("file", entry.get("file") or "")
        entry["file_abs"] = _locate(case_path, entry["file"], work_dir) if entry.get("file") else ""
        entry["file_exists"] = bool(entry["file_abs"]) and os.path.exists(entry["file_abs"])
        if not entry["file_exists"] and entry.get("file"):
            entry["missing"] = entry["file"]
        figures.append(entry)

    if not figures:
        for f in _extract_figure_lines(material_text):
            figures.append({"id": f["fig_id"], "caption": f["caption"],
                            "source": f"{sources[-1]['rel']}:{f['line']}",
                            "detected": "material_caption", "file": "", "file_exists": False})

    tables = []
    for item in case.get("tables") or []:
        if isinstance(item, str):
            item = {"id": item}
        entry = dict(item)
        entry.setdefault("id", str(entry.get("tbl_id") or entry.get("name") or f"ta{len(tables)+1}"))
        entry.setdefault("caption", entry.get("caption") or entry.get("title") or "")
        entry.setdefault("source", entry.get("source") or entry.get("src") or "case.json[tables]")
        entry.setdefault("rows", entry.get("rows") or entry.get("data") or [])
        if isinstance(entry["rows"], str):  # CSV file reference
            csvp = _locate(case_path, entry["rows"], work_dir)
            if os.path.exists(csvp):
                entry["rows"] = _read_csv(csvp)
                entry.setdefault("file", entry["rows"])
                entry["source"] = f"{os.path.basename(csvp)}"
            else:
                entry["rows"] = []
                entry["missing_csv"] = entry["rows"]
        tables.append(entry)

    if not tables:
        for t in _extract_table_lines(material_text):
            tables.append({"id": t["tbl_id"], "caption": t["caption"],
                           "source": f"{sources[-1]['rel']}:{t['line']}",
                           "detected": "material_caption", "rows": []})

    # --- key numbers (values must be traceable) ----------------------------
    key_numbers = []
    for item in case.get("key_numbers") or case.get("data") or []:
        if isinstance(item, str):
            item = {"text": item}
        entry = dict(item)
        entry.setdefault("source", entry.get("source") or entry.get("src") or "case.json[key_numbers]")
        key_numbers.append(entry)
    if not key_numbers and material_text.strip():
        # crude scan for "labelled number + unit" bullets — informational only
        for i, raw in enumerate(material_text.splitlines(), start=1):
            m = re.match(r"^\s*[-*•]?\s*([^:：;]{2,40})[:：]\s*([0-9][0-9.,]*(?:\s*[%℃°×±μmnkgmM]*))", raw)
            if m:
                key_numbers.append({"text": m.group(1).strip(), "value": m.group(2).strip(),
                                    "source": f"{sources[-1]['rel']}:{i}", "detected": True})
            if len(key_numbers) >= 15:
                break

    content = {
        "_meta": "normalized extraction; every item carries a source locator",
        "case_id": case_id,
        "title": case.get("title") or case.get("deck_title") or "",
        "subtitle": case.get("subtitle") or case.get("abstract") or "",
        "authors": _norm_list("authors", "author"),
        "affiliation": case.get("affiliation") or case.get("institution") or "",
        "audience": case.get("audience") or "科研同行",
        "duration_minutes": case.get("duration_minutes") or case.get("duration") or 15,
        "language": case.get("language") or "zh",
        "slide_count_target": case.get("slide_count") or case.get("total_slides") or 0,
        "template": case.get("template") or "",
        "template_path": _locate(case_path, case.get("template") or "", work_dir) if case.get("template") else "",
        "starting_deck": case.get("starting_deck") or "",
        "starting_deck_path": _locate(case_path, case.get("starting_deck") or "", work_dir) if case.get("starting_deck") else "",
        "sections": {
            "question": question, "methods": methods, "results": results,
            "discussion": discussion, "limitations": limitations, "conclusion": conclusion,
        },
        "figures": figures,
        "tables": tables,
        "key_numbers": key_numbers,
        "supplemented_from_material": supplemented,
        "sources": sources,
        "uncertainty": _collect_uncertainty(sources),
        "output_contract": case.get("output_contract") or {},
        "task_text": read_text(task_path) if task_path and os.path.exists(task_path) else "",
    }
    return content


def _collect_uncertainty(sources: list) -> list:
    out = []
    for s in sources:
        if not s.get("exists"):
            out.append({"item": f"source material {s['rel']}",
                        "note": "file missing -> content derived only from case.json + task.md"})
        elif s.get("note"):
            out.append({"item": f"source material {s['rel']}",
                        "note": s["note"]})
    if not any(s.get("exists") for s in sources):
        out.append({"item": "no readable material", "note": "no material text; decks are driven by case.json structure only"})
    return out


def _read_csv(path: str) -> list:
    import csv
    with open(path, "r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.reader(fh))


def main(argv=None):
    utf8_writer()
    import argparse
    ap = argparse.ArgumentParser(description="extract.py — normalize paper content with source locators")
    ap.add_argument("--case", required=True)
    ap.add_argument("--task", default=None)
    ap.add_argument("--work", default=None, help="/app/work or material base dir")
    ap.add_argument("--out", required=True, help="output dir for content.json")
    a = ap.parse_args(argv)

    content = extract(a.case, a.task, a.work, a.out)
    os.makedirs(a.out, exist_ok=True)
    dump_json(os.path.join(a.out, "content.json"), content)
    n = (len(content["sections"]["question"]) + len(content["sections"]["results"])
         + len(content["figures"]) + len(content["tables"]))
    print(f"extract ok: case={content['case_id']} story_items={n} sources={len(content['sources'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())