#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
evidence.py — load source materials and extract claims with evidence anchors.
(extract role in the build/extract/render/verify split.)

Honesty rule: nothing here invents content.  Claims are taken verbatim (or
lightly re-worded) from material lines, and every claim carries a locator
(source file, section, line number, quote).  PDFs are parsed with pypdf when
available; when it is not, the material is recorded as unparsed and the
affected slides are marked with reduced evidence strength instead of guessing.
"""

import os
import re

TEXT_EXTS = {".md", ".markdown", ".txt", ".text", ".rtf", ".rst"}

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
NUMBERED_HEADING_RE = re.compile(r"^(\d+(?:\.\d+)*)[\.\)、]\s*(.*)$")
PUB_HEADING_RE = re.compile(r"^(摘要|引言|方法|结果|结论|讨论|局限|数据|附录|Abstract|Introduction|Methods|Results|Discussion|Conclusion|Limitations)\b", re.I)

FIG_REF_RE = re.compile(
    r"(?:Fig(?:ure|s|\.)?|S(?:upp\.?|upplementary)?\s*Fig(?:ure|s|\.)?|"
    r"图|Table|表|Scheme|S(?:upp\.?)?\s*Table)\s*"
    r"([A-Za-z]?[0-9]+(?:[-–—][0-9A-Za-z]+)?|[一二三四五六七八九十]+)",
    re.I)

NUM_RE = re.compile(r"\d+(?:\.\d+)?(?:%|％|e-?\d+)?|±\s*\d+(?:\.\d+)?|P\s*[<>=]\s*0?\.?\d+", re.I)

# ordered classification rules: first match wins
# Order matters: 研究问题/动机 must win over 结果类动词；方法类词要优先于泛结果词。
CLASS_RULES = [
    (re.compile(r"(局限性|不足|限制|风险|未来|展望|尚未(验证|覆盖|评估)|未(验证|覆盖|评估)|开放问题|缺口|bias|limitation|局限)", re.I), "limits"),
    (re.compile(r"(会被问|备答|问答|提问|质疑|答辩问题|评委可能)", re.I), "qa"),
    (re.compile(r"(综上|结论|总结|总体而言|我们认为|说明(了)?|意味着|因此建议)", re.I), "conclusion"),
    (re.compile(r"(研究问题|研究目标|研究动机|动机|为什么|痛点|问题|缺乏|现有(方法|工作|基线)的(不足|局限)|gap|学术空白)", re.I), "introduction"),
    (re.compile(r"(方法|采用|提出|使用|基于|流程|框架|体系|数据(集|来源)|检索|召回(阶段)?|候选|编码器|模型|算法|指标|评估|实验(设计|设置|条件)|阶段|消融)", re.I), "method"),
    (re.compile(r"(结果表明|结果显示|研究发现|观察到|相比|对比|高于|低于|提升|下降|降到|降至|增加|减少|增强|抑制|显著|实现|达到|显示|准确率|精度|误差|性能|效果|基线|Acc@|F1|auc|p\s*[<=>]|±|improve|increase|decrease|enhance|achieve|significant)", re.I), "results"),
]

FINDING_HINT_RE = re.compile(
    r"(结果表明|结果显示|我们发现|我们提出|实验(证明|表明|验证)|显著|相比|达到|提升|实现|"
    r"准确率|精度|误差|达到|P<|p=|性能|效果|X{[0-9]|方法(采用|基于)|流程|分为|阶段|"
    r"局限性|不足之处|下一步|未来工作|参数|超参|epoch|loss|"
    r"术语|缩写|前置步骤|覆盖(不足|有限)|受限|失真|口径|差距)", re.I)


def classify_claim(text):
    for rule, kind in CLASS_RULES:
        if rule.search(text):
            return kind
    return "general"


def number_tokens(text):
    """Numeric tokens found in a text, normalized (lowercase)."""
    out = set()
    for m in NUM_RE.finditer(text):
        out.add(m.group(0).strip().lower())
    return out


def extract_figure_refs(text):
    """Return list of figure/table/scheme references in source order."""
    out = []
    seen = set()
    for m in FIG_REF_RE.finditer(text):
        label = m.group(0).strip()
        key = label.lower().replace(".", "")
        if key not in seen:
            seen.add(key)
            out.append(label)
    return out


def split_sections(text):
    """Split material text into sections with line-level anchors.

    Returns list of {heading, path, start_line, end_line, lines:[{no, text}]}.
    """
    sections = []
    lines = text.splitlines()
    cur_heading = "__preamble__"
    cur_path = []
    cur = {"heading": cur_heading, "path": ["(前言/标题区)"], "start_line": 1,
           "end_line": 0, "lines": []}
    for idx, raw in enumerate(lines, start=1):
        line = raw.rstrip()
        stripped = line.strip()
        heading = None
        m = HEADING_RE.match(stripped)
        if m:
            heading = m.group(2).strip()
        else:
            m = NUMBERED_HEADING_RE.match(stripped)
            if m and len(stripped) <= 70:
                heading = stripped
            elif PUB_HEADING_RE.match(stripped) and len(stripped) <= 50:
                heading = stripped
        if heading:
            if cur["lines"] or cur["heading"] != "__preamble__":
                cur["end_line"] = idx - 1
                sections.append(cur)
            if m and m.group(0).startswith("#"):
                level = len(HEADING_RE.match(stripped).group(1))
                if level == 1:
                    cur_path = [heading]
                else:
                    cur_path = (cur_path[: level - 1] if cur_path else []) + [heading]
            else:
                number_m = NUMBERED_HEADING_RE.match(stripped) or re.match(r"^(\d+)", stripped)
                if number_m and not stripped.startswith("#"):
                    cur_path = cur_path[:1] + [stripped] if cur_path else [stripped]
                else:
                    cur_path = [stripped] if not cur_path else cur_path
            cur = {"heading": heading, "path": list(cur_path) or [heading],
                   "start_line": idx, "end_line": 0, "lines": []}
            continue
        if stripped:
            cur["lines"].append({"no": idx, "text": raw})
    cur["end_line"] = len(lines)
    if cur["lines"] or sections:
        sections.append(cur)
    return [s for s in sections if s["lines"]]


def section_of_line(line_no, sections):
    for s in sections:
        if s["start_line"] <= line_no <= max(s["end_line"], s["start_line"]):
            return " / ".join(s["path"])
    return "(无章节定位)"


def load_material(path):
    """Load one source material into a parse record."""
    base = os.path.basename(path)
    ext = os.path.splitext(base)[1].lower()
    record = {"path": path, "file": base, "kind": ext.lstrip(".") or "unknown",
              "parsed": False, "note": "", "char_count": 0, "sections": [],
              "figure_refs": [], "text": ""}
    if not os.path.exists(path):
        record["note"] = "file missing"
        return record
    if ext in TEXT_EXTS:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                raw = fh.read()
            record["parsed"] = True
            record["text"] = raw
            record["char_count"] = len(raw)
            record["sections"] = split_sections(raw)
            record["figure_refs"] = extract_figure_refs(raw)
        except Exception as exc:  # noqa: BLE001
            record["note"] = "text read failed: %s" % exc
            return record
    elif ext == ".pdf":
        try:
            from pypdf import PdfReader  # optional dependency
        except Exception:
            try:
                from PyPDF2 import PdfReader  # legacy name
            except Exception:
                record["note"] = ("PDF parsing unavailable (pypdf/PyPDF2 not installed); "
                                  "recorded as unparsed, claims from this file are not "
                                  "extracted and evidence strength is degraded")
                return record
        try:
            reader = PdfReader(path)
            parts = []
            for i, page in enumerate(reader.pages):
                try:
                    txt = page.extract_text() or ""
                except Exception:  # noqa: BLE001
                    txt = ""
                parts.append("--- page %d ---\n%s" % (i + 1, txt))
            raw = "\n".join(parts)
            record["parsed"] = True
            record["text"] = raw
            record["char_count"] = len(raw)
            record["sections"] = split_sections(raw)
            record["figure_refs"] = extract_figure_refs(raw)
            record["note"] = "text extracted via pypdf (plain text proxy; layout/figures not recovered)"
        except Exception as exc:  # noqa: BLE001
            record["note"] = "pdf extraction failed: %s" % exc
            return record
    else:
        record["note"] = ("binary/image type '%s' — kept as attachment reference; "
                          "cannot be quoted as text evidence" % ext)
    return record


def extract_claims(record, min_len=14, max_len=420):
    """Extract claim candidates from one parsed material record.

    Each candidate is a single line that looks like a finding/statement and
    carries: text (verbatim), line_no, section, kind (introduction/method/
    results/limits/conclusion/qa/general), strength and figure refs on the
    same line.  Strength: strong if numeric/statistical tokens or a figure
    reference is present; medium for clear finding verbs; weak otherwise.
    """
    claims = []
    if not record["parsed"]:
        return claims
    seen = set()
    for sec in record["sections"]:
        for ln in sec["lines"]:
            t = ln["text"].strip()
            if len(t) < min_len or len(t) > max_len:
                continue
            if t in seen:
                continue
            refs = [r for r in extract_figure_refs(t)]
            nums = number_tokens(t)
            strong = bool(refs) or len(nums) > 0 or bool(re.search(r"\bP\b|p\s*[<=>]|±", t, re.I))
            finding = bool(FINDING_HINT_RE.search(t))
            # skip pure captions ("Table 2. Summary of ..."), but keep caption-led
            # finding sentences ("Table 1 显示：... 提升了 ...") as claims
            caption_start = t.startswith(("Fig.", "Figure", "图", "Table", "表", "Scheme"))
            if caption_start and not (strong or finding):
                continue
            if not (strong or finding or len(nums) > 1):
                continue
            kind = classify_claim(t)
            strength = "strong" if strong else ("medium" if finding else "weak")
            seen.add(t)
            claims.append({
                "text": t,
                "line_no": ln["no"],
                "section": " / ".join(sec["path"]),
                "kind": kind,
                "strength": strength,
                "refs": refs,
                "numbers": sorted(nums)[:12],
            })
    return claims


def collect_terms(record):
    """Collect candidate terminology: parenthesized abbreviations + domain pairs
    like 'XXX（XXX）' occurring in the text.  Best-effort glossary seed."""
    terms = []
    if not record["parsed"]:
        return terms
    pat = re.compile(r"([\u4e00-\u9fffA-Za-z][^\n（）()]{1,40}?)[（(]([A-Za-z0-9_\-\s]{2,40})[)）]", re.I)
    for sec in record["sections"]:
        for ln in sec["lines"]:
            for m in pat.finditer(ln["text"]):
                term = m.group(1).strip()
                abbr = m.group(2).strip()
                if len(term) >= 2 and len(abbr) >= 2 and not abbr.lower().startswith(("fig", "table", "supp")):
                    pair = (term, abbr)
                    if pair not in terms:
                        terms.append(pair)
    return terms