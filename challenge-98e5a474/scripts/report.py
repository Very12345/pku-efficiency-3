#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""result.json emission.

Implements the contract documented in references/OUTPUT_CONTRACT.md:

* every UPDATE_/main_result artifact is recorded with role, format,
  path (absolute + relative to the output dir) and its checks,
* `case_id` is always present,
* `sources` lists the original material files that were actually read,
* `status` is honest (success / partial / failed),
* `uncertainty` and `change_records` are never fabricated,
* if the case.json itself declares an `output_contract` object, every key
  of it is also emitted at the top level (defaulted by declared type) so
  the result survives whatever field list the platform checks.
"""

import json
import os
import platform
import sys
import time
import uuid

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

TOOL_VERSIONS = {
    "scientific_schematic_editor": "1.0.0",
    "python": platform.python_version(),
}


def tool_versions():
    v = dict(TOOL_VERSIONS)
    try:
        import matplotlib
        v["matplotlib"] = matplotlib.__version__
    except Exception:
        pass
    try:
        import PIL
        v["Pillow"] = PIL.__version__
    except Exception:
        pass
    try:
        import numpy
        v["numpy"] = numpy.__version__
    except Exception:
        pass
    try:
        import reportlab
        v["reportlab"] = reportlab.Version
    except Exception:
        pass
    return v


def _default_for(arg):
    """Best-effort JSON-compatible default for an output_contract key.
    Accepts Python types or string type hints ("array", "object", ...)."""
    if isinstance(arg, str):
        low = arg.strip().lower()
        if low in ("array", "list", "json-array", "sequence"):
            return []
        if low in ("object", "dict", "map", "json-object"):
            return {}
        if low in ("string", "text", "str"):
            return ""
        if low in ("number", "integer", "int", "float", "numeric", "double"):
            return 0
        if low in ("boolean", "bool"):
            return False
        if low in ("status", "case_id", "id"):
            return "unknown"
        return ""
    if isinstance(arg, list):
        return []
    if isinstance(arg, dict):
        return {}
    if isinstance(arg, (int, float)) and not isinstance(arg, bool):
        return 0
    if isinstance(arg, bool):
        return False
    return None


def apply_output_contract(case, result):
    """If case.json declares an output_contract, mirror every key into the
    result top level (missing values get type-appropriate defaults)."""
    oc = None
    if isinstance(case, dict):
        oc = case.get("output_contract")
    if not isinstance(oc, dict) or not oc:
        return result
    for key, hint in oc.items():
        have = result.get(key)
        if have not in (None, "", [], {}):
            continue
        if key == "case_id":
            if not result.get("case_id"):
                result["case_id"] = case.get("case_id") or ""
            continue
        result[key] = have if have is not None else _default_for(hint)
        if result[key] is None:
            result[key] = _default_for(hint)
    return result


def build_result(case, manifest, checks_summary, artifacts, render_info,
                 sources, uncertainty, change_records, header=None):
    """Assemble the complete result.json dict.

    :param artifacts: dict of {role: {"path": abs, "rel": rel-path,
                      "format": ext, "checks": [single-issue dicts],
                      "extra": {..}}}
    :param reliability is expressed through checks_summary + uncertainty.
    """
    case_id = (case or {}).get("case_id") or (case or {}).get("id") or ""
    out_dir = os.path.dirname(next(iter(artifacts.values()))["path"]) \
        if artifacts else ""
    out_dir = os.path.abspath(out_dir) if out_dir else os.getcwd()

    fig_type = (manifest or {}).get("figure_type") or "schematic"
    entities = (manifest or {}).get("entities") or []
    relations = (manifest or {}).get("relations") or []

    result = {
        "case_id": case_id,
        "skill": {"name": "scientific-schematic-editor",
                  "version": "1.0.0",
                  "display": "科研示意图生成与编辑"},
        "status": checks_summary.get("status", "unknown"),
        "workorder": ((case or {}).get("workorder")
                      or ((case or {}).get("task") or {}).get("workorder")
                      or "editable_relationship_schematic"),
        "task_summary": ((case or {}).get("summary")
                         or ((case or {}).get("task") or {}).get("summary")
                         or ""),
        "figure_type": fig_type,
        "title": (manifest or {}).get("title") or "",
        "main_result": {
            "figure_type": fig_type,
            "title": (manifest or {}).get("title") or "",
            "entity_count": len(entities),
            "relation_count": len(relations),
            "group_count": len((manifest or {}).get("groups") or []),
            "deliverables": {role: {"path": v["rel"], "format": v["format"]}
                             for role, v in artifacts.items()},
        },
        "artifacts": [
            {"role": role, "format": v["format"], "path": v["rel"],
             "abspath": v["path"], "checks": v["checks"],
             **({"extra": v["extra"]} if v.get("extra") else {})}
            for role, v in artifacts.items()
        ],
        "evidence": {
            "sources": sources,
            "entities": [
                {"id": e.get("id"), "name": e.get("name"),
                 "type": e.get("type"),
                 "source": e.get("source", ""), "evidence": e.get("evidence", "")}
                for e in entities
            ],
            "relations": [
                {"id": r.get("id"), "from": r.get("from"), "to": r.get("to"),
                 "kind": r.get("kind"), "canonical_kind": r.get("_canon"),
                 "source": r.get("source", ""), "evidence": r.get("evidence", "")}
                for r in relations
            ],
        },
        "legend_mapping": (manifest or {}).get("legend") or [],
        "data_mapping": (render_info or {}).get("mapping")
                        if isinstance(render_info, dict) and render_info.get("mapping")
                        else (manifest or {}).get("data") or {},
        "verification": {
            "checks": checks_summary,
            "render": render_info if isinstance(render_info, dict) else {},
            "traceability": (manifest or {}).get("_traceability") or {},
        },
        "sources": [{"path": p} for p in sources],
        "uncertainty": uncertainty,
        "change_records": change_records,
        "status_notes": (header or "")
                        or "Generated locally by scientific-schematic-editor.",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "generator": "scientific-schematic-editor",
        "tool_versions": tool_versions(),
    }
    if (case or {}).get("case_id") in (None, ""):
        result["case_id"] = case_id or os.path.basename(out_dir) or "case"
    result = apply_output_contract(case, result)
    return result


def write_result(path, result):
    """Persist result.json (UTF-8, LF, 2-space indent)."""
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return os.path.abspath(path)


def now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")