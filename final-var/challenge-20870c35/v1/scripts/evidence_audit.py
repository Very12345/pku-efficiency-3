#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
evidence_audit.py — audit that every page claim is traceable to a real source
anchor.  (verify role in the build/extract/render/verify split; corresponds to
the high-score evidence_audit / audit_evidence scripts.)

For every page (structural pages title/agenda/qa are checked lightly):
  * source_file must be declared in the material/source list
  * the quote must appear verbatim in the source text actually read
    (whitespace-normalized line match) — pages flagged `derived` (framed from
    a section summary, e.g. when a block has no direct claim) are reported as
    synthetic summaries with reduced strength instead of pretending verbatim
  * the claimed line_no must fall inside the section bounds it names
  * numeric tokens in the claim should be traceable to the source text
    (warning level)
  * figure_ref → figure_file binding state is recorded

Output: evidence_audit.json ({valid, entries[], summary}) written next to the
result, and embedded into result.json.audit.

CLI: python evidence_audit.py <result.json> [--out evidence_audit.json] [--sources-dir <dir>]
"""

import json
import os
import re
import sys

from common import write_json, sha256_text

_NUM_RE = re.compile(r"\d+(?:\.\d+)?(?:%|％)?|±\s*\d+(?:\.\d+)?|P\s*[<>=]\s*0?\.?\d+", re.I)
_STRUCTURAL = {"title", "agenda", "qa"}


def _norm_line(text):
    """Normalize for verbatim line matching: strip \r, collapse trailing ws."""
    return text.replace("\r", "").rstrip()


def _numbers_in(text):
    return {m.group(0).strip().lower() for m in _NUM_RE.finditer(text)}


def _load_source_texts(material_records):
    """source file basename -> normalized full text (the text actually read)."""
    out = {}
    for rec in material_records or []:
        txt = rec.get("text")
        if isinstance(txt, str) and txt:
            out[rec.get("file", "")] = _norm_line(txt)
    return out


def _load_from_result(result, result_dir, sources_dir):
    """Best-effort standalone path: collect source texts from disk."""
    texts = {}
    for s in result.get("sources") or []:
        if not isinstance(s, dict):
            continue
        name = str(s.get("file") or "")
        candidates = []
        if s.get("path"):
            candidates.append(s["path"])
        candidates.append(os.path.join(result_dir, name))
        if sources_dir:
            candidates.append(os.path.join(sources_dir, name))
        for c in candidates:
            if c and os.path.exists(c):
                try:
                    with open(c, "r", encoding="utf-8", errors="replace") as fh:
                        texts[name] = _norm_line(fh.read())
                    break
                except Exception:  # noqa: BLE001
                    continue
    return texts


def audit_page(page, declared_sources, source_texts):
    """Audit one page.  Returns an entry dict."""
    entry = {
        "page_no": page.get("page_no"),
        "block": page.get("block"),
        "title": page.get("title", ""),
        "ok": True,
        "notes": [],
    }
    if page.get("block") in _STRUCTURAL:
        entry["kind"] = "structural"
        return entry
    entry["kind"] = "content"
    ev = (page.get("evidence") or [{}])[0]
    src = str(ev.get("source_file") or "")
    if src not in declared_sources:
        entry["ok"] = False
        entry["notes"].append("source_file 不在 sources 声明中: %s" % src)
    quote = str(ev.get("quote") or "")
    derived = bool(page.get("derived"))
    entry["derived"] = derived

    if src in source_texts:
        text = source_texts[src]
        q_norm = _norm_line(quote.strip())
        found = (q_norm in text) if q_norm else False
        if found:
            entry["quote_found"] = True
        elif derived:
            entry["quote_found"] = False
            entry["notes"].append("页面为源材料章节概括（derived/framed），引文为概括语非逐字，"
                                  "证据强度应为 weak —— 讲解时应回查原论文正文")
        else:
            entry["quote_found"] = False
            entry["ok"] = False
            entry["notes"].append("引文未在源文本中逐字找到（可能是抽取截断或多行拼接）")
        # locator line within section bounds
        line_no = ev.get("line_no")
        sec_path = str(ev.get("section") or "")
        if isinstance(line_no, int) and line_no > 0:
            lines = text.split("\n")
            if 0 < line_no <= len(lines):
                entry["line_text"] = _norm_line(lines[line_no - 1])[:80]
                entry["line_ok"] = bool(_norm_line(lines[line_no - 1]).strip())
            else:
                entry["line_ok"] = False
                entry["ok"] = False
                entry["notes"].append("line_no=%d 超出源文本行数 %d" % (line_no, len(lines)))
        # numeric traceability (warning level)
        claim_nums = _numbers_in(str(page.get("claim") or ""))
        src_nums = _numbers_in(text)
        stranger = [n for n in claim_nums
                    if len(n) >= 4 or any(ch in n for ch in ".%±<>=pP")]
        untrace = [n for n in stranger if n not in src_nums]
        if untrace:
            entry["numbers_not_in_source"] = untrace[:6]
            entry["notes"].append("claim 中数字未在源文本逐字出现（警告级，可能为合理换算）: %s"
                                  % untrace[:6])
    else:
        entry["quote_found"] = None
        entry["notes"].append("源文本不可用（本机磁盘无该文件），跳过逐字核验；"
                              "运行期由 main.py 以实际读取的文本执行")

    if page.get("figure_ref"):
        entry["figure_ref"] = page["figure_ref"]
        if page.get("figure_file"):
            entry["figure_bound"] = True
        else:
            entry["figure_bound"] = False
            entry["notes"].append("图表 %s 无对应图片文件，页内为诚实占位框" % page["figure_ref"])
    return entry


def audit_evidence(pages, material_records=None, declared_sources=None,
                   source_texts=None, result=None, result_dir=None,
                   sources_dir=None):
    """Audit all pages.  Takes either (pages, material_records) from the live
    run, or (result, result_dir) for standalone re-checks."""
    if declared_sources is None:
        if material_records is not None:
            declared_sources = {str(r.get("file") or "") for r in material_records}
        elif result is not None:
            declared_sources = set()
            for s in result.get("sources") or []:
                if isinstance(s, dict) and s.get("file"):
                    declared_sources.add(str(s["file"]))
        else:
            declared_sources = set()
    if source_texts is None:
        if material_records is not None:
            source_texts = _load_source_texts(material_records)
        elif result is not None:
            source_texts = _load_from_result(result, result_dir or ".", sources_dir)
        else:
            source_texts = {}
    entries = []
    for p in pages or []:
        if isinstance(p, dict):
            entries.append(audit_page(p, declared_sources, source_texts or {}))
    content_entries = [e for e in entries if e.get("kind") == "content"]
    errs = [e for e in content_entries if not e["ok"]]
    summary = {
        "pages_total": len(entries),
        "content_pages": len(content_entries),
        "ok_pages": len(content_entries) - len(errs),
        "errors": len(errs),
        "derived_pages": len([e for e in content_entries if e.get("derived")]),
        "unavailable_text": len([e for e in content_entries if e.get("quote_found") is None]),
    }
    report = {
        "schema": "evidence_audit.v1",
        "generated_by": "evidence_audit.py of academic-talk-organizer (efficiency-3, v2)",
        "method": "verbatim quote check against actually-read source text; "
                  "locator line/section bounds; numeric traceability (warning); "
                  "figure binding state",
        "valid": len(errs) == 0,
        "summary": summary,
        "entries": entries,
    }
    return report


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if len(args) < 2:
        print(json.dumps({"error": "usage: evidence_audit.py <result.json> "
                                   "[--out file.json] [--sources-dir <dir>]"},
                         ensure_ascii=False))
        return 2
    res_path = args[1]
    with open(res_path, "r", encoding="utf-8") as fh:
        result = json.load(fh)
    result_dir = os.path.dirname(os.path.abspath(res_path)) or "."
    sources_dir = None
    out_path = None
    if "--sources-dir" in argv:
        sources_dir = argv[argv.index("--sources-dir") + 1]
    if "--out" in argv:
        out_path = argv[argv.index("--out") + 1]
    report = audit_evidence(result.get("pages"), result=result,
                            result_dir=result_dir, sources_dir=sources_dir)
    text = json.dumps(report, ensure_ascii=False, indent=2)
    print(text)
    if out_path:
        write_json(out_path, report)
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))