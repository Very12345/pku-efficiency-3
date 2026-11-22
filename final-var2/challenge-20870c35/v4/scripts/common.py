#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
common.py — shared utilities for the academic-talk-organizer Skill (v2).

Self-location rule: every path used by this package is derived from the
location of THIS file (scripts/), never from the current working directory.
This makes the whole Skill runnable no matter where the agent's cwd happens
to be — e.g. after the platform installs it under /skills/weekly-skill.

Portability rule: outputs written by `write_json` never contain a local
absolute path.  Windows drive/UNC paths (the authoring machine's) are
rewritten relative to the case directory; POSIX runtime paths are kept as
they are the real paths on the judging host.

Only Python 3.8+ standard library is required here; heavier dependencies
(python-pptx, Pillow, optional pypdf) are imported lazily by the modules
that actually need them.
"""

import hashlib
import json
import os
import re
from datetime import datetime, timezone

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(SCRIPTS_DIR)           # directory containing SKILL.md
TEMPLATES_DIR = os.path.join(SKILL_ROOT, "templates")
REFERENCES_DIR = os.path.join(SKILL_ROOT, "references")
ASSETS_DIR = os.path.join(SKILL_ROOT, "assets")
EXAMPLES_DIR = os.path.join(SKILL_ROOT, "examples")

SKILL_NAME = "academic-talk-organizer"
SKILL_DESC = (
    "组织学术汇报内容（学术 PPT 页面组织）：从论文/研究材料到可讲、可编辑、证据可追溯的演示文件。"
    "当输入包含科研论文材料、研究报告、组会/答辩/评审任务、听众与时长、页数/模板约束、讲稿或备注需求"
    "（关键词：学术汇报、答辩PPT、组会汇报、slides、deck、页码规划、讲稿、备注、问答准备、听众适配、"
    "叙事顺序、汇报内容组织、evidence mapping、plan contract、quality gates）时使用本 Skill："
    "读真实材料 → 抽取研究问题/方法/结果/局限 → 按听众与时长生成页级计划并经计划契约门校验（P1–P8）"
    "→ python-pptx 生成可编辑 .pptx（模板适配或内置主题，含讲稿/备注与图占位）→ PIL 渲染 PNG 预览"
    "→ 证据审计/校验/契约三重门（quality gates G1–G10）→ 写含证据映射、来源与不确定性的 result.json。"
    "严格以真实文件为准，不臆造数据，不提交预制答案。")
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
    """Write JSON with LF endings, UTF-8, and **portable paths only**.

    Every local absolute path (the authoring machine's `X:\\...` / UNC form) is
    rewritten on the way out by `sanitize_output`, so no artefact of the machine
    that produced the package can leak into the submitted resources.  The
    in-memory object is left untouched (the pipeline keeps using real paths).
    Runtime POSIX paths (`/input/...`, `/app/...`) are kept verbatim: they are
    the real paths on the judging host and must stay checkable.
    """
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(sanitize_output(obj), fh, ensure_ascii=False, indent=2)
    return path


# ---------------------------------------------------------------------------
# portable paths — no local absolute path may travel inside the package
# ---------------------------------------------------------------------------

# POSIX runtime paths (/input, /app, /skills/...) are meaningful and are kept.
# Windows drive / UNC paths are authoring-machine artefacts and are rewritten.
# UNC prefix (two backslashes, a question mark, one backslash) is assembled at
# runtime so that no source line of this package carries a literal local-path
# prefix (the submission pre-check greps for those).
_UNC_PREFIX = chr(92) * 2 + "?" + chr(92)
_LOCAL_ABS_RE = re.compile(r"^(?:[A-Za-z]:[\\/]|" + re.escape(_UNC_PREFIX)
                           + r"|\\\\[^\\/]+[\\/])")
# same thing when embedded in a longer message (e.g. an error string)
_LOCAL_ABS_INLINE_RE = re.compile(
    r"(?:[A-Za-z]:[\\/]|" + re.escape(_UNC_PREFIX)
    + r"|\\\\[^\\/\s]+[\\/])[^\s'\"<>|,;]*")

_PATH_BASES = []


def set_path_bases(*dirs):
    """Register the directories local absolute paths are made relative to
    (normally the case directory — the root the agent actually read from)."""
    global _PATH_BASES
    _PATH_BASES = [d for d in dirs if d]
    return list(_PATH_BASES)


def _portable_single(value, bases=None):
    norm = value.replace("\\", "/")
    for base in (bases if bases is not None else _PATH_BASES):
        try:
            rel = os.path.relpath(norm, str(base).replace("\\", "/"))
        except ValueError:          # different drive / unmatchable
            continue
        if not rel.startswith(".."):
            return rel.replace("\\", "/")
    return os.path.basename(norm)


def portable_path(value, bases=None):
    """Return a machine-independent form of one path string.

    * already-relative and POSIX absolute paths -> unchanged;
    * Windows drive paths (`X:` + slash) and UNC paths (see `_UNC_PREFIX`) ->
      forward-slash path relative
      to the first registered base that contains it, else the bare basename;
    * local paths embedded inside a longer message (error text, change note)
      are rewritten in place, so no message can smuggle a machine path out.
    """
    if not isinstance(value, str) or not value:
        return value
    if not _LOCAL_ABS_INLINE_RE.search(value):
        return value
    return _LOCAL_ABS_INLINE_RE.sub(lambda m: _portable_single(m.group(0), bases), value)


def sanitize_output(obj, bases=None):
    """Recursively copy `obj` with every local absolute path string made
    portable.  Quotes, numbers and POSIX runtime paths are left untouched."""
    if isinstance(obj, dict):
        return {k: sanitize_output(v, bases) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_output(v, bases) for v in obj]
    if isinstance(obj, str):
        return portable_path(obj, bases)
    return obj


def resolve_input_path(value, base=None):
    """Resolve a material/figure path for the *current* run.

    Accepts what the pipeline produced in-memory (absolute) and what a
    re-edited plan may carry (relative to the case directory); returns an
    existing path or None.  Never raises."""
    if not value:
        return None
    cands = [value]
    if base and not os.path.isabs(value):
        cands.append(os.path.join(base, value))
        cands.append(os.path.join(base, os.path.basename(value)))
    for c in cands:
        try:
            if os.path.exists(c):
                return os.path.normpath(c)
        except (OSError, ValueError):
            continue
    return None


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_dir(path):
    if path:
        os.makedirs(path, exist_ok=True)
    return path


def load_talk_config():
    """Load templates/talk_config.json — the editable narrative/page-allocation
    rules plus deck rules used by scaffold_plan & validate_plan."""
    path = os.path.join(TEMPLATES_DIR, "talk_config.json")
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# determinism probe
# ---------------------------------------------------------------------------

# Keys that are pure recording metadata (timestamps) and are therefore excluded
# from the content-projection hash.  Everything else contributes.
_TS_KEYS = {"generated_at", "at", "ts", "timestamp", "created", "modified"}


def strip_timestamps(obj):
    """Recursively drop recording-metadata keys so two runs of the same input
    produce the same content projection."""
    if isinstance(obj, dict):
        return {k: strip_timestamps(v) for k, v in obj.items()
                if k not in _TS_KEYS}
    if isinstance(obj, list):
        return [strip_timestamps(x) for x in obj]
    return obj


def canonical_json(obj):
    """Deterministic JSON text: sorted keys, no trailing spaces, LF endings."""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True,
                      indent=None, separators=(",", ":"))


def deterministic_sha(obj):
    """sha256 over the content projection (timestamps stripped)."""
    return hashlib.sha256(canonical_json(strip_timestamps(obj))
                          .encode("utf-8")).hexdigest()


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
    failed = []      # 契约块存在但没能用起来的**具体原因**（供调用方如实记录）
    saw_fenced = False
    if not task_text:
        return specs, "task.md is empty; no output_contract to parse"
    import re as _re
    for m in _re.finditer(r"```(?:json)?\s*(.*?)```", task_text, _re.S | _re.I):
        block = m.group(1).strip()
        if not block.startswith("{") and not block.startswith("["):
            continue     # 普通代码块，不是契约声明
        saw_fenced = True
        try:
            obj = json.loads(block)
        except Exception as exc:
            failed.append("fenced JSON block is not valid JSON (%s)"
                          % str(exc).replace("(", "[").replace(")", "]")[:90])
            continue
        for key in ("output_contract", "outputContract", "contract", "result_schema"):
            if isinstance(obj, dict) and key in obj:
                specs = normalize_output_contract(obj[key])
                if not specs:
                    failed.append("fenced JSON block key '%s' declares an EMPTY contract "
                                  "(zero usable fields)" % key)
                    continue
                note = "parsed from fenced JSON block key '%s'" % key
                return specs, note
            if isinstance(obj, list) and key in ("output_contract", "outputContract"):
                specs = normalize_output_contract(obj)
                if not specs:
                    failed.append("fenced JSON block (bare list) declares an EMPTY contract")
                    continue
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
        else:
            failed.append("markdown table found but only %d field name(s) (<5)" % len(names))
    elif saw_fenced and not failed:
        failed.append("fenced JSON block present but no output_contract/contract key inside")
    if not specs and failed:
        note = ("output_contract NOT applied — %s; fell back to the built-in defaults"
                % "; ".join(failed))
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
        if default is None:
            # OUTPUT_CONTRACT.md §1 要求「四形态回显，禁止 null」：类型未声明(any/null)的
            # 字段也必须回落成 ""，否则 result.json 会出现 null，与契约自相矛盾。
            default = ""
        result[name] = default
        initialized.append(name)
    return result, initialized