#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_plan.py — schema-driven validation of the talk plan (plan gates
P1–P8).  (build-check role in the build/extract/render/verify split.)

The plan contract lives in assets/plan.schema.json (single source of truth);
this module interprets it (top-level required fields + property types + the
page-level contract) and runs the named gates:

  P1 required top-level fields present & typed
  P2 page_no forms a continuous 1..N sequence with no duplicates
  P3 len(pages) == timing.slide_target  (frozen slide count honored)
  P4 every page block ∈ vocabulary (templates/talk_config.json blocks ∪ schema)
  P5 every content page has evidence[0] with locator/quote/source_file/strength
  P6 every evidence source_file is declared in the material file list
  P7 every page has non-empty title/claim/one_liner; 6 <= len(claim) <= 500
  P8 notes contain an 【讲解】 line; derived pages are strength=weak

CLI: python validate_plan.py <plan.json> [--materials-dir <dir>] [--schema <file>]
Exit code 0 when gates pass (report printed as JSON).
"""

import json
import os
import sys

from common import ASSETS_DIR, read_json, write_json

_DEFAULT_SCHEMA = os.path.join(ASSETS_DIR, "plan.schema.json")

_BLOCK_LABELS = {
    "title", "agenda", "motivation", "background", "method", "results",
    "conclusion_risk", "innovation_limits", "conclusion", "qa",
}
_STRENGTHS = {"strong", "medium", "weak"}
_STRUCTURAL_BLOCKS = {"title", "agenda", "qa"}
_TYPE_MAP = {
    "str": str, "string": str, "text": str,
    "int": (int, float), "integer": (int, float), "number": (int, float),
    "float": (int, float),
    "list": list, "array": list,
    "dict": dict, "object": dict,
    "bool": bool, "boolean": bool,
    "any": object, "null": None,
}


def _check_type(value, ctype):
    wanted = _TYPE_MAP.get(str(ctype).lower(), object)
    if wanted is None:
        return value is None
    return isinstance(value, wanted)


def _load_schema(path=None):
    path = path or _DEFAULT_SCHEMA
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _gather_material_names(materials_dir):
    """Collect material file basenames from a directory (best effort)."""
    names = set()
    if materials_dir and os.path.isdir(materials_dir):
        for fn in os.listdir(materials_dir):
            if os.path.isfile(os.path.join(materials_dir, fn)):
                names.add(fn)
    return names


def validate_plan(plan, schema=None, material_names=None):
    """Validate a plan dict against the schema + gates.  `material_names` is
    the set/list of material file basenames visible to this run."""
    schema = schema or _load_schema()
    errors = []
    warnings = []
    gates = []

    def _gate(gid, desc, ok, detail=""):
        gates.append({"id": gid, "desc": desc, "ok": bool(ok), "detail": detail})
        if not ok:
            errors.append("%s %s" % (gid, detail))

    if not isinstance(plan, dict):
        _gate("P1", "plan 顶层字段齐全", False, "plan is not an object")
        return {"valid": False, "gates": gates, "errors": errors,
                "warnings": warnings, "schema_id": schema.get("$id")}

    # ---- P1 required fields + types ----
    required = schema.get("required", [])
    props = schema.get("properties", {})
    p1_ok = True
    p1_detail = []
    for name in required:
        if name not in plan or plan[name] is None:
            p1_ok = False
            p1_detail.append("missing:%s" % name)
            continue
        spec = props.get(name, {})
        ctype = spec.get("type") if isinstance(spec, dict) else "any"
        if ctype and str(ctype).lower() != "any":
            sub_ok = True
            val = plan[name]
            if isinstance(val, list) and str(ctype).lower() in ("list", "array"):
                sub_ok = True
            elif isinstance(val, dict) and str(ctype).lower() in ("dict", "object"):
                sub_ok = True
            elif isinstance(val, str) and str(ctype).lower() in ("str", "string", "text"):
                sub_ok = True
            elif isinstance(val, (int, float)) and not isinstance(val, bool) \
                    and str(ctype).lower() in ("int", "integer", "number", "float"):
                sub_ok = True
            elif isinstance(val, bool) and str(ctype).lower() == "bool":
                sub_ok = True
            elif str(ctype).lower() == "any":
                sub_ok = True
            else:
                sub_ok = False
            if not sub_ok:
                p1_ok = False
                p1_detail.append("type:%s!=%s" % (name, ctype))
    _gate("P1", "plan 顶层必填字段齐全且类型正确", p1_ok, "; ".join(p1_detail))

    # ---- pages ----
    pages = plan.get("pages") if isinstance(plan, dict) else None
    if not isinstance(pages, list):
        _gate("P2", "页编号连续", False, "pages missing")
        _gate("P5", "内容页证据齐全", False, "pages missing")
        return {"valid": len(errors) == 0, "gates": gates, "errors": errors,
                "warnings": warnings, "schema_id": schema.get("$id")}

    page_contract = schema.get("page", {})
    block_vocab = set(page_contract.get("blocks", [])) | _BLOCK_LABELS
    ev_required_blocks = set(page_contract.get("evidence_required_blocks", []))
    strengths = set(page_contract.get("strengths", ["strong", "medium", "weak"]))
    strengths.add(None)

    # ---- P2 sequence ----
    nums = [p.get("page_no") for p in pages if isinstance(p, dict)]
    seq_ok = (nums == list(range(1, len(pages) + 1)))
    _gate("P2", "页编号 1..N 连续且无重复", seq_ok,
          "got=%s" % ([n for n in nums if not isinstance(n, int)][:5] or nums[:12]))

    # ---- P3 page count == slide_target ----
    target = None
    timing = plan.get("timing") if isinstance(plan, dict) else None
    if isinstance(timing, dict):
        target = timing.get("slide_target")
    count_ok = (isinstance(target, int) and len(pages) == target)
    _gate("P3", "页总数 == slide_target（冻结页数）", count_ok,
          "pages=%d target=%s" % (len(pages), target))

    # ---- P4 block enum ----
    bad_blocks = [p.get("page_no") for p in pages
                  if p.get("block") not in block_vocab]
    _gate("P4", "每页 block ∈ 词表", len(bad_blocks) == 0,
          "bad_page_blocks=%s" % bad_blocks)

    # ---- P5 evidence present on content pages ----
    ev_missing = []
    for p in pages:
        if p.get("block") in ev_required_blocks:
            ev = p.get("evidence")
            ev0 = ev[0] if isinstance(ev, list) and ev else None
            if not ev0 or not (ev0.get("locator") and ev0.get("quote")
                               and ev0.get("source_file") and ev0.get("strength")):
                ev_missing.append(p.get("page_no"))
    _gate("P5", "内容页 evidence 齐全（locator/quote/source_file/strength）",
          len(ev_missing) == 0, "pages=%s" % ev_missing)

    # ---- P6 source declared ----
    src_missing = []
    if material_names is not None:
        declared = {str(n) for n in material_names}
        for p in pages:
            for ev in p.get("evidence") or []:
                if ev.get("source_file") and ev["source_file"] not in declared \
                        and ev["source_file"] != "(无源材料)":
                    if (p.get("page_no"), ev["source_file"]) not in src_missing:
                        src_missing.append((p.get("page_no"), ev["source_file"]))
    _gate("P6", "证据 source_file 均在材料清单中", len(src_missing) == 0,
          "undeclared=%s" % src_missing)

    # ---- P7 text fields ----
    text_issues = []
    for p in pages:
        for f in ("title", "claim", "one_liner"):
            txt = p.get(f)
            if not isinstance(txt, str) or not txt.strip():
                text_issues.append((p.get("page_no"), f, "empty"))
        cl = p.get("claim") or ""
        if not (6 <= len(cl) <= 500):
            text_issues.append((p.get("page_no"), "claim", "len=%d" % len(cl)))
        st = p.get("strength")
        if st not in strengths:
            text_issues.append((p.get("page_no"), "strength", repr(st)))
    _gate("P7", "每页 title/claim/one_liner 非空、claim 长度与强度词法正确",
          len(text_issues) == 0, "issues=%s" % text_issues[:12])

    # ---- P8 notes / derived ----
    notes_issues = []
    for p in pages:
        notes = p.get("notes") or ""
        if "【讲解】" not in notes:
            notes_issues.append((p.get("page_no"), "no-讲解-note"))
        if p.get("derived") and p.get("strength") != "weak":
            notes_issues.append((p.get("page_no"), "derived-not-weak"))
    _gate("P8", "每页 notes 含【讲解】行；derived 页 strength=weak",
          len(notes_issues) == 0, "issues=%s" % notes_issues)

    return {"valid": len(errors) == 0, "gates": gates, "errors": errors,
            "warnings": warnings, "schema_id": schema.get("$id"),
            "summary": "gates=%d ok=%d" % (len(gates), len(gates) - len(errors))}


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if len(args) < 2:
        print(json.dumps({"error": "usage: validate_plan.py <plan.json> "
                                   "[--materials-dir <dir>] [--schema <file>]"},
                         ensure_ascii=False))
        return 2
    plan_path = args[1]
    plan = read_json(plan_path)
    materials_dir = None
    schema_path = None
    if "--materials-dir" in argv:
        materials_dir = argv[argv.index("--materials-dir") + 1]
    if "--schema" in argv:
        schema_path = argv[argv.index("--schema") + 1]
    material_names = _gather_material_names(materials_dir) if materials_dir else None
    report = validate_plan(plan, schema=_load_schema(schema_path),
                           material_names=material_names)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))