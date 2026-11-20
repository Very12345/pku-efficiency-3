#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
common.py — shared utilities for the academic-talk-organizer Skill.

Self-location rule: every path used by this package is derived from the
location of THIS file (scripts/), never from the current working directory.
This makes the whole Skill runnable no matter where the agent's cwd happens
to be — e.g. after the platform installs it under /skills/weekly-skill.

Only Python 3.8+ standard library is required here; heavier dependencies
(python-pptx, Pillow, optional pypdf) are imported lazily by the modules
that actually need them.
"""

import json
import os
from datetime import datetime, timezone

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(SCRIPTS_DIR)           # directory containing SKILL.md
TEMPLATES_DIR = os.path.join(SKILL_ROOT, "templates")
REFERENCES_DIR = os.path.join(SKILL_ROOT, "references")
EXAMPLES_DIR = os.path.join(SKILL_ROOT, "examples")

SKILL_NAME = "academic-talk-organizer"
SKILL_DESC = (
    "组织学术汇报内容（学术 PPT 页面组织）：从论文/研究材料到可讲、可编辑、证据可追溯的演示文件。"
    "当输入包含科研论文材料、研究报告、组会/答辩/评审任务、听众与时长、页数/模板约束、讲稿或备注需求"
    "（关键词：学术汇报、答辩PPT、组会汇报、slides、deck、页码规划、讲稿、备注、问答准备、听众适配、"
    "叙事顺序、汇报内容组织、evidence mapping）时使用本 Skill：读真实材料 → 抽取研究问题/方法/结果/局限"
    "→ 按听众与时长规划页级主张、图表引用与讲解顺序 → python-pptx 生成可编辑 .pptx（模板适配或内置主题）"
    "→ PIL 渲染 PNG 预览 → 写含证据映射、来源与不确定性的 result.json。严格以真实文件为准，不臆造数据，"
    "不提交预制答案。")
FRONTMATTER = {"name": SKILL_NAME, "description": SKILL_DESC}


def utc_now():
    """IS08601 UTC timestamp used for change_records."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_text(path):
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def write_text(path, text):
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return path


def read_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path, obj):
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)
    return path


def ensure_dir(path):
    if path:
        os.makedirs(path, exist_ok=True)
    return path


def load_talk_config():
    """Load templates/talk_config.json — the editable narrative/page-allocation rules."""
    path = os.path.join(TEMPLATES_DIR, "talk_config.json")
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# output_contract handling
# ---------------------------------------------------------------------------

CONTRACT_TYPE_DEFAULTS = {
    "str": "",
    "string": "",
    "text": "",
    "list": [],
    "array": [],
    "dict": {},
    "object": {},
    "int": 0,
    "integer": 0,
    "number": 0,
    "float": 0.0,
    "bool": False,
    "boolean": False,
    "any": None,
    "null": None,
}


def _field_spec(field):
    """Normalize one contract field entry to (name, required, container_type).

    Accepts: str name; {"name": str, "type|container|kind"?: str, "required"?: bool}
    """
    if isinstance(field, str):
        return field, True, "any"
    if isinstance(field, dict):
        name = field.get("name") or field.get("field") or field.get("key")
        if not name:
            return None, False, "any"
        ctype = field.get("type") or field.get("container") or field.get("kind") or "any"
        required = bool(field.get("required", True))
        return name, required, str(ctype).lower()
    return None, False, "any"


def normalize_output_contract(payload):
    """Extract a list of (name, required, ctype) from any common shape of an
    output_contract declaration found in case.json / task.md:

    - list of field names            ["case_id","status",...]
    - list of dicts                  [{"name":"pages","type":"list"}, ...]
    - dict of type strings           {"case_id":"str","pages":"list"}
    - JSON-schema-like dict          {"required":[...], "properties":{...}}
    - None / missing                 -> []
    """
    specs = []
    if isinstance(payload, list):
        for item in payload:
            spec = _field_spec(item)
            if spec[0]:
                specs.append(spec)
    elif isinstance(payload, dict):
        if "properties" in payload or "required" in payload:
            required = payload.get("required") or []
            req_set = set(required) if isinstance(required, list) else set()
            props = payload.get("properties") or {}
            for name, p in props.items():
                if not isinstance(p, dict):
                    p = {}
                ctype = (p.get("type") or "any").lower()
                if p.get("container") or p.get("format") in ("list", "array"):
                    ctype = p.get("container") or "list"
                specs.append((name, name in req_set, ctype))
            for name in required:
                if name not in props:
                    specs.append((name, True, "any"))
        else:
            for name, ctype in payload.items():
                specs.append((name, True, str(ctype).lower()))
    return specs


def parse_output_contract_from_task(task_text):
    """Scan task.md for an output_contract declaration.

    Recognized shapes:
    - fenced JSON block containing keys 'output_contract' / 'outputContract' / 'contract'
    - a markdown table whose first column header is 'output_contract'-ish
    Returns (specs, source_note).
    """
    specs = []
    note = "no output_contract found in task.md"
    if not task_text:
        return specs, note
    import re as _re
    for m in _re.finditer(r"```(?:json)?\s*(.*?)```", task_text, _re.S | _re.I):
        block = m.group(1).strip()
        try:
            obj = json.loads(block)
        except Exception:
            continue
        for key in ("output_contract", "outputContract", "contract", "result_schema"):
            if isinstance(obj, dict) and key in obj:
                specs = normalize_output_contract(obj[key])
                note = "parsed from fenced JSON block key '%s'" % key
                return specs, note
            if isinstance(obj, list) and key in ("output_contract", "outputContract"):
                specs = normalize_output_contract(obj)
                note = "parsed from fenced JSON block (bare list)"
                return specs, note
    # markdown table fallback
    table_re = _re.compile(r"^\s*\|?\s*(field|字段|name|名称|output_contract)[^\n]*\|", _re.I | _re.M)
    if table_re.search(task_text):
        names = []
        for row in task_text.splitlines():
            cells = [c.strip() for c in row.strip().lstrip("|").split("|")]
            if len(cells) >= 2 and cells[0] and cells[0] not in ("---", "-"):
                if _re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", cells[0]):
                    names.append(cells[0])
        if len(names) >= 5:
            specs = normalize_output_contract(names)
            note = "parsed from markdown table of field names"
    return specs, note


DEFAULT_CONTRACT_FIELDS = [
    "case_id", "status", "title", "report_goal", "audience", "duration_min",
    "slide_count", "main_line", "pages", "evidence_map", "artifacts",
    "sources", "uncertainty", "change_records",
]


def apply_contract(result, specs):
    """Guarantee every declared field exists at the top level of `result`,
    initialized with a type-appropriate default when the pipeline did not
    produce it.  Returns (result, newly_initialized_names)."""
    initialized = []
    declared_names = []
    for name, required, ctype in specs:
        if name in declared_names:
            continue
        declared_names.append(name)
        if name in result and result[name] is not None:
            continue
        if not required and name not in result:
            # optional + missing -> skip (do not pollute)
            continue
        default = CONTRACT_TYPE_DEFAULTS.get(ctype, CONTRACT_TYPE_DEFAULTS["any"])
        result[name] = default
        initialized.append(name)
    return result, initialized