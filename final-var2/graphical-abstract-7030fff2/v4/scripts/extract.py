# -*- coding: utf-8 -*-
"""Source-bound content extraction for graphical abstracts.

Reads the *actual* input files (case.json, task.md, material files) and
produces a normalized ``content`` dict:

    {
      "case_id", "title", "task", "panels",
      "entities":  [ {id, name, type, panel, note, shape, src} ],
      "relations": [ {from, to, label, direction, kind, src} ],
      "data":      [ {id, label, value, unit, kind, group, note, src} ],
      "constraints":  {...merged figure_constraints...},
      "output_contract": {...},
      "source_files": [{path, sha256, role}],
      "notes": [...]
    }

Design principles
-----------------
* Never fabricate: every element carries ``src`` (file:line or JSON field).
  Values that cannot be located in the stated materials are *not* invented;
  they end up in ``uncertainty`` at the orchestrator level.
* Deterministic: same input files -> same content dict.
* Tolerant: understands several plausible case.json shapes (explicit
  entities/relations/data keys, arrow strings, "key: value unit" text lines,
  section headings 问题/方法/结果/结论).
"""
from __future__ import annotations

import json
import os
import re

from common import (list_dir_text, load_json, read_text, sha256_file, slug)

# ---------------------------------------------------------------------------
# JSON key synonyms
# ---------------------------------------------------------------------------
KEYS_ENTITIES = ("entities", "entity", "objects", "components", "nodes", "molecules", "items")
KEYS_RELATIONS = ("relations", "relation", "edges", "arrows", "links", "interactions", "flows", "edge_list")
KEYS_DATA = ("data", "datapoints", "metrics", "values", "numbers", "key_results", "stats", "measurements")
KEYS_CONSTRAINTS = ("figure_constraints", "constraints", "layout", "canvas", "drawing_constraints")
KEYS_CONTRACT = ("output_contract", "contract", "output_contract_fields", "deliverable_spec")
KEYS_MATERIAL = ("source_material", "material", "materials", "source_files", "attachments")

RE_ARROW = re.compile(
    r"^\s*(?P<f>[^>→>｜|]{1,48}?)\s*(?:->|→|==>|⇒?)\s*(?P<t>[^,;()（）]{1,48}?)\s*"
    r"(?:[\(（]\s*(?P<l>[^)）]*)\s*[\)）])?\s*$", re.UNICODE)
RE_DASH = re.compile(
    r"^\s*(?P<f>[^\-–—|]{1,48}?)\s*(?:-|–|—)\s*(?P<t>[^,;()（）]{1,48}?)\s*"
    r"(?:[\(（]\s*(?P<l>[^)）]*)\s*[\)）])?\s*$", re.UNICODE)
RE_NUM_UNIT = re.compile(r"^(?P<num>[-+]?[\d][\d.,]*(?:[eE][-+]?\d+)?)\s*(?P<unit>[A-Za-z%‰°/μµgmLnNκκл·^²³]+)?$")
RE_HEADING = re.compile(
    r"^\s*(?P<mark>#{1,6}\s*|[*+-]\s*)?\s*"
    r"(?P<kw>问题|研究问题|问题定义|question|research\s*question|背景|background|"
    r"方法|方法路线|实验方法|method|methods|approach|"
    r"结果|主要结果|核心结果|results?|result|findings|"
    r"结论|结论与意义|conclusion|conclusions?|summary|takeaway$|"
    r"机制|mechanism|通路|pathway|路线|pipeline|流程|workflow)\s*(?P<rest>.*)$",
    re.IGNORECASE)

PANEL_BY_KW = {
    "问题": "question", "question": "question", "研究问题": "question", "背景": "question",
    "方法": "method", "method": "method", "approach": "method", "机制": "method",
    "mechanism": "method", "通路": "method", "pathway": "method", "路线": "method",
    "pipeline": "method", "流程": "method", "workflow": "method",
    "结果": "results", "result": "results", "findings": "results",
    "结论": "conclusion", "conclusion": "conclusion", "summary": "conclusion",
}
VALID_PANELS = ("question", "method", "results", "conclusion")

PANEL_LABELS = {
    "question": "研究问题",
    "method": "方法 / 机制",
    "results": "核心结果",
    "conclusion": "结论",
}
PANEL_LABELS_EN = {
    "question": "Question",
    "method": "Method / Mechanism",
    "results": "Key Results",
    "conclusion": "Conclusion",
}


def _find_key(obj, names):
    """Case-insensitive first match of any synonym; returns (key, value) or (None, None)."""
    low = {str(k).lower(): v for k, v in obj.items()}
    for n in names:
        if n.lower() in low:
            return n, low[n.lower()]
    return None, None


def _first(d, *names, default=None):
    for n in names:
        if isinstance(d, dict) and n in d:
            return d[n]
    return default


def _as_list(v):
    if v is None:
        return []
    if isinstance(v, list):
        return v
    return [v]


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
_ENTITY_SHAPES = {"molecule": "circle", "cell": "rounded", "tissue": "rounded",
                  "material": "diamond", "device": "rect", "sample": "circle",
                  "particle": "circle", "process": "rect", "state": "hex"}


def normalize_entities(value, src_ctx, existing_by_id):
    entities = []
    for raw in _as_list(value):
        if isinstance(raw, str) and raw.strip():
            name = raw.strip()
            rec = {"id": slug(name), "name": name, "type": "object",
                   "panel": None, "note": None, "shape": "circle", "src": src_ctx}
        elif isinstance(raw, dict):
            name = str(_first(raw, "name", "label", "id", "title") or "").strip()
            if not name:
                continue
            etype = str(_first(raw, "type", "category", "kind") or "object").strip()
            panel = _first(raw, "panel", "panel_id", "where")
            if isinstance(panel, str):
                p = panel.strip().lower()
                p = {"q": "question", "问题": "question", "m": "method", "方法": "method",
                     "r": "results", "结果": "results", "c": "conclusion", "结论": "conclusion"}.get(p, p)
                panel = p if p in VALID_PANELS else None
            else:
                panel = None
            note = _first(raw, "note", "description", "desc", "detail")
            rec = {"id": slug(name), "name": name, "type": etype,
                   "panel": panel, "note": str(note).strip() if note else None,
                   "shape": _ENTITY_SHAPES.get(etype, "circle"),
                   "src": raw.get("src") or src_ctx}
        else:
            continue
        if rec["id"] in existing_by_id:
            continue  # de-duplicate by id, first mention wins
        existing_by_id[rec["id"]] = rec
        entities.append(rec)
    return entities


# ---------------------------------------------------------------------------
# Relations
# ---------------------------------------------------------------------------
def _parse_relation_str(text, src):
    m = RE_ARROW.match(text) or RE_DASH.match(text)
    if not m:
        return None
    f, t = m.group("f").strip(), m.group("t").strip()
    label = (m.group("l") or "").strip() or None
    if not f or not t:
        return None
    kind = "positive"
    if label and re.search(r"inhibit|inhibit|block|reduce|suppress|down.?reg|decrease|prevent|抑制|减少|降低|阻断", label, re.I):
        kind = "negative"
    return {"id": slug(f + "_to_" + t), "from": f, "to": t, "label": label,
            "direction": "forward", "kind": kind, "src": src}


def normalize_relations(value, entities, src_ctx):
    by_name = {e["name"].lower(): e["id"] for e in entities}
    relations = []
    for raw in _as_list(value):
        rec = None
        if isinstance(raw, str) and raw.strip():
            rec = _parse_relation_str(raw, src_ctx)
        elif isinstance(raw, dict):
            f = str(_first(raw, "from", "source", "start", "subject", "src_node") or "").strip()
            t = str(_first(raw, "to", "target", "end", "object", "tgt_node") or "").strip()
            label = _first(raw, "label", "relation", "edge", "verb", "name")
            if f and t:
                label = str(label).strip() if label else None
                kind = "negative" if (label and re.search(
                    r"inhibit|block|reduce|suppress|down.?reg|decrease|prevent|抑制|减少|降低|阻断", label, re.I)) else "positive"
                rec = {"id": slug(f + "_to_" + t), "from": f, "to": t, "label": label,
                       "direction": "forward", "kind": kind,
                       "src": raw.get("src") or src_ctx}
        if rec:
            rec["from_id"] = by_name.get(rec["from"].lower(), None)
            rec["to_id"] = by_name.get(rec["to"].lower(), None)
            relations.append(rec)
    return relations


# ---------------------------------------------------------------------------
# Data points
# ---------------------------------------------------------------------------
def _parse_value(val):
    """Return (number, unit) for strings like '95 nm', '18 %', 72, '72%'; else (None, None)."""
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        return float(val), None
    if not isinstance(val, str):
        return None, None
    # second chance FIRST: units with digits / '-' / '/' (mA/cm2, cm-2, h^-1,
    # m2/g) fail the strict class below, which used to report an existing value
    # as "数值缺失" and keep it off the canvas (purely additive).
    m2 = re.match(r"^(?P<num>[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)(?![.\d])\s*(?P<unit>\D\S*)$",
                  val.strip())
    if m2:
        try:
            return (float(m2.group("num").replace(",", "")),
                    (m2.group("unit") or "").strip())
        except ValueError:
            pass
    m = RE_NUM_UNIT.match(val.strip())
    if not m:
        return None, None
    num = m.group("num").replace(",", "")
    try:
        return float(num), (m.group("unit") or None)
    except ValueError:
        return None, None


def normalize_data(value, src_ctx):
    data = []
    seen = set()
    for raw in _as_list(value):
        if isinstance(raw, dict):
            label = str(_first(raw, "label", "name", "metric", "key", "title") or "").strip()
            if not label:
                continue
            vraw = _first(raw, "value", "val", "number", "result")
            num, unit = _parse_value(vraw)
            kind = str(_first(raw, "kind", "encode", "encoding", "channel") or "bar_length").strip()
            if kind not in ("bar_length", "color_scale", "area", "value_label"):
                kind = "bar_length"
            note = _first(raw, "note", "description", "unit_note")
            rec = {"id": slug(label), "label": label, "value": num, "unit": unit,
                   "kind": kind,
                   "group": str(_first(raw, "group", "category", "series") or "").strip() or None,
                   "note": str(note).strip() if note else None,
                   "src": raw.get("src") or src_ctx}
        elif isinstance(raw, (str, int, float)) and str(raw).strip():
            label = str(raw).strip()
            rec = {"id": slug(label), "label": label, "value": None, "unit": None,
                   "kind": "bar_length", "group": None, "note": None, "src": src_ctx}
        else:
            continue
        if rec["id"] in seen:
            continue
        seen.add(rec["id"])
        data.append(rec)
    return data


# ---------------------------------------------------------------------------
# Panel / point mapping from task or material text
# ---------------------------------------------------------------------------
def parse_panel_text(text, file_tag):
    """Extract {panel -> [bullet points]} from headings 问题/方法/结果/结论.

    Also returns a list of (line_no, line) pairs that look like facts
    ("key: value unit" or arrow lines) for later use when no JSON data block
    exists.
    """
    panels = {p: [] for p in VALID_PANELS}
    current = None
    bullets = []
    for i, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        m = RE_HEADING.match(stripped)
        if m:
            kw = m.group("kw").strip().lower()
            panel = PANEL_BY_KW.get(kw)
            if panel:
                if current and bullets:
                    panels[current].extend(bullets)
                current = panel
                bullets = []
                # trailing text on the heading line counts as the first point
                rest = m.group("rest").strip()
                if rest:
                    bullets.append(rest)
                continue
        if current:
            if stripped.startswith(("-", "*", "+", "•", "1.", "2.", "3.")):
                bullets.append(re.sub(r"^[\s\-*+•\d.]+", "", stripped))
        else:
            # facts outside any panel also matter (usually method/results context)
            pass
    if current and bullets:
        panels[current].extend(bullets)
    return panels


def parse_fact_lines(text, file_tag):
    """Conservative 'key: value unit' / 'label = value unit' / arrow scans."""
    facts = []
    for i, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        # drop a leading bullet marker so "- key = value" keeps a clean label
        stripped = re.sub(r"^[-*·•]\s+", "", stripped)
        if not stripped or stripped.startswith("#"):
            continue
        src = f"{file_tag}:{i}"
        # arrow relations
        rel = _parse_relation_str(stripped, src)
        # a real arrow token must be present: the pattern alone also matches
        # plain text (optional delimiter) and would swallow every data line
        if rel and not re.search(r"->|→|==>|⇒", stripped):
            rel = None
        if rel:
            facts.append({"kind": "relation", "src": src, "rec": rel})
            continue
        # key : value unit   or   label = value unit
        m = re.match(r"^[\[(]?\s*(?P<key>[^:=]{1,60}?)\s*[:=]\s*(?P<val>[-+]?[\d][\d.,]*(?:[eE][-+]?\d+)?)\s*"
                     r"(?P<unit>[A-Za-z%‰°/μµgmLnNκл·^²³]+)?\s*([\];)]+)?\s*$", stripped)
        if m:
            key = m.group("key").strip(" *#*").strip()
            num = float(m.group("val").replace(",", "")) if re.match(r"^\d", m.group("val")) else None
            unit = m.group("unit")
            facts.append({"kind": "data", "src": src, "rec": {
                "id": slug(key), "label": key, "value": num, "unit": unit,
                "kind": "bar_length", "group": None, "note": None, "src": src}})
            continue
        _m2 = re.match(r"^[\[(]?\s*(?P<key>[^:=]{1,60}?)\s*[:=]\s*"
                       r"(?P<val>[-+]?\d[\d.,]*(?:[eE][-+]?\d+)?)\s*"
                       r"(?P<unit>[A-Za-z%‰°/μµgmLnNκл·^²³0-9/\-]{1,14})?\s*([\];)]+)?\s*$",
                       stripped)
        if _m2:
            key = _m2.group("key").strip(" *#*").strip()
            num = float(_m2.group("val").replace(",", ""))
            facts.append({"kind": "data", "src": src, "rec": {
                "id": slug(key), "label": key, "value": num,
                "unit": _m2.group("unit"), "kind": "bar_length",
                "group": None, "note": None, "src": src}})
            continue
        # plain numeric bullet: "95 nm" with a preceding label line is too
        # ambiguous -> do not guess; keep the line as a candidate chain only.
    return facts


# ---------------------------------------------------------------------------
# Constraints + contract
# ---------------------------------------------------------------------------
DEFAULT_CONSTRAINTS = {
    "width": 1200, "height": 800, "margin": 24, "dpi": 300,
    "colorblind": True, "flow_arrows": True, "language": "auto",
    "font_family": None, "palette": None, "reading_order": True,
    "raster_scale": 2, "pdf": True,
}


def normalize_constraints(value):
    c = dict(DEFAULT_CONSTRAINTS)
    if isinstance(value, dict):
        for k, v in value.items():
            if k in c and v is not None:
                c[k] = v
    w = int(c["width"]); h = int(c["height"])
    c["width"] = max(600, min(4000, w))
    c["height"] = max(400, min(4000, h))
    return c


def normalize_contract(value):
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        return {"note": value}
    return {}


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------
def _binary_material_text(path: str, max_pages: int = 20, max_chars: int = 200000):
    """Best-effort text layer for a binary material (PDF). Optional: pypdf.

    Returns None when no text layer is available, so the caller can record an
    honest "material not readable as text" limitation instead of decoding raw
    bytes as UTF-8 (which silently produces mojibake entities/values).
    """
    if not path.lower().endswith(".pdf"):
        return None
    try:
        from pypdf import PdfReader  # optional dependency
    except Exception:  # noqa: BLE001
        return None
    try:
        reader = PdfReader(path)
        chunks = [(page.extract_text() or "") for page in reader.pages[:max_pages]]
        text = "\n".join(chunks).strip()
    except Exception:  # noqa: BLE001
        return None
    return text[:max_chars] if text else None


def run(case_path: str, task_path=None, material=None) -> dict:
    """Load real files and produce the normalized content dict.

    `material` may be a file or a directory with text-like files.
    """
    case = load_json(case_path)
    case_dir = os.path.dirname(os.path.abspath(case_path))

    sources = []

    def tag_file(path, role):
        sources.append({"path": path, "sha256": sha256_file(path), "role": role})
        return path

    case_id = str(_first(case, "case_id", "id", "case") or os.path.splitext(os.path.basename(case_path))[0] or "case")
    title = str(_first(case, "title", "topic", "figure_title") or "").strip()
    task_text = ""
    if task_path and os.path.isfile(task_path):
        tag_file(task_path, "task")
        task_text = read_text(task_path)

    # ---- material files ---------------------------------------------------
    mat_cfg = _find_key(case, KEYS_MATERIAL)[1] if _find_key(case, KEYS_MATERIAL)[1] is not None else None
    mat_paths = []
    if material:
        mat_paths = [material]
    elif mat_cfg:
        mat_paths = _as_list(mat_cfg)
    if not mat_paths:
        # sensible default: task.md / material.md next to case.json
        for cand in ("material.md", "materials.md", "source.md", "task.md"):
            p = os.path.join(case_dir, cand)
            if os.path.isfile(p):
                mat_paths.append(p)
                break
    mat_texts = []
    missing_materials = []
    non_utf8_materials = []
    binary_materials = []
    pdf_text_materials = []
    for p in mat_paths:
        ap = p if os.path.isabs(p) else os.path.join(case_dir, p)
        if not os.path.exists(ap):
            missing_materials.append(p)
            continue
        for f in list_dir_text(ap):
            try:
                with open(f, "rb") as _probe:
                    _head = _probe.read(4096)
                _head.decode("utf-8")
            except UnicodeDecodeError:
                non_utf8_materials.append(os.path.basename(f))
            if bytes([0]) in _head or _head.lstrip()[:5] == b"%PDF-":
                binary_materials.append(os.path.basename(f))
                _pdf_text = _binary_material_text(f)
                if _pdf_text:
                    pdf_text_materials.append(os.path.basename(f))
                    tag_file(f, "material(pdf-text)")
                    mat_texts.append(_pdf_text)
                continue
            tag_file(f, "material")
            mat_texts.append(read_text(f))
    all_text = "\n".join(mat_texts)

    uncertainty = []
    value_conflicts = []
    if missing_materials:
        uncertainty.append("case.json 声明的材料路径不存在：" + ", ".join(missing_materials)
                           + "（已用其余可用材料继续，未虚构内容）")
    if non_utf8_materials:
        uncertainty.append("以下材料文件不是合法 UTF-8，已按替换字符读取（内容可能失真）："
                           + ", ".join(non_utf8_materials))
    if binary_materials:
        uncertainty.append("以下材料是二进制文件（未按文本解析）：" + ", ".join(binary_materials)
                           + ("；已改用 PDF 文本层：" + ", ".join(pdf_text_materials)
                              if pdf_text_materials else
                              "；未取得可用文本层，相关数值一律不上画布"))
    # ---- extraction -------------------------------------------------------
    existing = {}
    entities = []

    ev = _find_key(case, KEYS_ENTITIES)
    if ev[1] is not None:
        entities = normalize_entities(ev[1], f"case.json[{ev[0]}]", existing)

    # relations from JSON
    rv = _find_key(case, KEYS_RELATIONS)
    relations = normalize_relations(rv[1] if rv[1] is not None else [], entities, f"case.json[{rv[0]}]") if rv[0] else []

    # data from JSON
    dv = _find_key(case, KEYS_DATA)
    data = normalize_data(dv[1] if dv[1] is not None else [], f"case.json[{dv[0]}]") if dv[0] else []

    # text-derived facts (appended only; first mention wins by id)
    by_name_lower = {e["name"].lower(): e["id"] for e in entities}
    if all_text:
        for fact in parse_fact_lines(all_text, "material"):
            if fact["kind"] == "relation":
                rec = fact["rec"]
                rec["from_id"] = by_name_lower.get(rec["from"].lower(), None)
                rec["to_id"] = by_name_lower.get(rec["to"].lower(), None)
                existing_ids = {r["id"] for r in relations}
                if rec["id"] not in existing_ids:
                    relations.append(rec)
            else:
                rec = fact["rec"]
                if rec["id"] not in {d["id"] for d in data}:
                    data.append(rec)
                else:
                    _prev = next((d for d in data if d["id"] == rec["id"]), None)
                    if (_prev and _prev.get("value") is not None
                            and rec.get("value") is not None
                            and abs(float(rec["value"]) - float(_prev["value"])) > 1e-12):
                        value_conflicts.append(
                            "%s：case.json 取 %s，材料另给 %s（两处 src=%s / %s）"
                            % (_prev.get("label"), _prev.get("value"), rec.get("value"),
                               _prev.get("src"), rec.get("src")))

    # panel points from task + material headings
    panels = {p: [] for p in VALID_PANELS}
    for txt, tag in ((task_text, "task.md"), (all_text, "material")):
        for p, pts in parse_panel_text(txt, tag).items():
            panels[p].extend(pts)

    # task summary (first non-empty paragraph)
    task_summary = ""
    if task_text:
        for line in task_text.splitlines():
            s = line.strip()
            if s and not s.startswith("#"):
                task_summary = s
                break

    constraints = normalize_constraints(_find_key(case, KEYS_CONSTRAINTS)[1])
    contract = normalize_contract(_find_key(case, KEYS_CONTRACT)[1])

    # panel inference for entities that have no explicit panel: an entity is
    # placed in the first panel whose points mention it (results > conclusion >
    # method > question), falling back to "question".
    def infer_panel(name):
        low = name.lower()
        for p in ("results", "conclusion", "method", "question"):
            for pt in panels[p]:
                if low in (pt or "").lower():
                    return p
        return "question"

    for e in entities:
        if e["panel"] is None:
            e["panel"] = infer_panel(e["name"])

    notes = []
    if not mat_texts:
        notes.append("未读到任何材料文本（材料为空、路径不可用或仅含非文本文件）；"
                     "实体/关系/数据仅来自 case.json 字段。")
    if not entities:
        notes.append("未在 case.json 或材料中发现可识别的实体列表（entities 字段缺失）；"
                     "如需实体元素请补充材料或 'entities' 字段。")
    if not data:
        notes.append("未在输入中发现可量化的数据点（data 字段缺失）；结果面板将只显示要点文本。")

    # conflicts must be appended AFTER the fact loop has filled the list
    if value_conflicts:
        uncertainty.extend("材料与 case.json 数值不一致（首见优先，未取平均）：" + c
                           for c in value_conflicts)
    return {
        "schema_version": "1.0",
        "case_id": case_id,
        "title": title,
        "task": task_summary,
        "panels": panels,
        "entities": entities,
        "relations": relations,
        "data": data,
        "constraints": constraints,
        "output_contract": contract,
        "source_files": sources,
        "notes": notes,
        "uncertainty": uncertainty,
    }