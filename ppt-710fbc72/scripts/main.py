# -*- coding: utf-8 -*-
"""main.py — orchestration entry point for the Academic Slide Adapter Skill.

Pipeline: extract (read real files) -> deckplan (deterministic slide plan)
-> pptxbuild (template-aware editable pptx + speaker notes) -> preview
(schematic PIL PNGs, honestly labelled) -> audit (checks on real artifacts)
-> result.json (output_contract echo + envelope fields).

Usage:
  python scripts/main.py --case <case.json> [--task <task.md>]
      [--work <material base dir>] [--template <template.pptx>]
      [--starting-deck <deck.pptx>] --out <output dir>
"""
from __future__ import annotations

import os
import sys
import json
import datetime

import common
from common import (utf8_writer, SKILL_NAME, SKILL_VERSION, DISPLAY_NAME, WORKORDER,
                    dump_json, tool_versions, now_iso, load_json, sha256_file)
import extract as extract_mod
import deckplan as deckplan_mod
import pptxbuild as pptxbuild_mod
import preview as preview_mod
import audit as audit_mod

DEFAULT_BUILTIN = os.path.join(common.skill_root(), "templates", "builtin.pptx")


def _type_default(value):
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return 0 if isinstance(value, int) else 0.0
    if isinstance(value, list):
        return []
    if isinstance(value, dict):
        return {}
    return ""


def _echo_output_contract(contract: dict, result: dict) -> dict:
    """Mirror every output_contract key into result top level; fill unseen
    keys with their declared type default (never None placeholder)."""
    for key, val in (contract or {}).items():
        if key not in result:
            result[key] = _type_default(val)
    return result


def _build_artifacts(out_dir: str, case_id: str) -> list:
    files = [
        ("deck", "pptx", f"{case_id}_deck.pptx", []),
        ("cover_preview", "png", f"{case_id}_cover_preview.png", []),
        ("contact_preview", "png", f"{case_id}_slides_contact_schematic.png", []),
        ("examined result", "json", "result.json", []),
        ("plan spec", "json", "spec.json", []),
        ("content", "json", "content.json", []),
        ("audit", "json", "audit.json", []),
        ("render log", "json", "render_log.json", []),
    ]
    arts = []
    for role, fmt, name, extra in files:
        p = os.path.join(out_dir, name)
        if os.path.exists(p):
            arts.append({
                "role": role, "format": fmt, "path": name,
                "abspath": os.path.abspath(p),
                "checks": {"exists": True, "sha256": sha256_file(p)},
                "extra": extra,
            })
    return arts


def _slide_evidence(plan: dict, content: dict) -> list:
    out = []
    for p in plan.get("pages", []):
        out.append({
            "page_no": p["page_no"], "page_type": p["page_type"],
            "title": p.get("title", ""),
            "claims": p.get("claims", []),
            "figure_refs": p.get("figure_refs", []),
            "table_refs": p.get("table_refs", []),
            "evidence": p.get("evidence", []),
            "notes_excerpt": (p.get("notes") or "")[:200],
        })
    return out


def _classify(checks: list) -> str:
    levels = [c.get("level") for c in checks]
    if any(l == "fail" for l in levels) or any(l == "warn" for l in levels):
        return "partial"
    return "success"


def run(case_path: str, task_path: str | None, work_dir: str | None,
        out_dir: str, template: str = "", starting_deck: str = "") -> dict:
    os.makedirs(out_dir, exist_ok=True)

    # 1 extract
    content = extract_mod.extract(case_path, task_path, work_dir, out_dir)
    dump_json(os.path.join(out_dir, "content.json"), content)
    case_id = content["case_id"]

    # 2 plan
    plan = deckplan_mod.plan(content)
    dump_json(os.path.join(out_dir, "spec.json"), plan)

    # 3 build
    tpl = template or content.get("template_path") or ""
    sdeck = starting_deck or content.get("starting_deck_path") or ""
    pptx_out = os.path.join(out_dir, f"{case_id}_deck.pptx")
    build_audit = pptxbuild_mod.build(content, plan, pptx_out, tpl, sdeck,
                                      DEFAULT_BUILTIN)

    # 4 preview
    render_log = preview_mod.render_all(content, plan, out_dir, case_id)

    # 5 audit (over real artifacts; result.json written next)
    audit_obj = audit_mod.audit(content, plan, out_dir, case_id, build_audit)

    # 6 result.json
    sources = [{"rel": s.get("rel"), "exists": s.get("exists", False),
                "lines": s.get("lines", 0)} for s in content.get("sources", [])]
    figs = content.get("figures") or []
    tables = content.get("tables") or []
    placed_figs = [f["id"] for f in figs
                   if any(f["id"] in (p.get("figure_refs") or [])
                          for p in plan.get("pages", []) if p["page_type"] == "results")]
    uncertainty = list(content.get("uncertainty", []))
    # auto-collect honest issues from pipeline
    for c in audit_obj.get("checks", []):
        if c["level"] in ("warn", "fail"):
            uncertainty.append({"item": f"check:{c['check']}", "note": c["detail"]})
    for f in figs:
        if not f.get("file_exists"):
            uncertainty.append({"item": f"figure {f['id']} source image",
                                "note": f"source image missing/unavailable -> placeholder box with caption; original caption kept"})
    for t in tables:
        if not t.get("rows"):
            uncertainty.append({"item": f"table {t['id']}",
                                "note": "no row data available -> caption-only mention"})

    main_result = {
        "deck": {"path": f"{case_id}_deck.pptx", "format": "pptx", "editable": True},
        "planned_slides": plan.get("planned_slides"),
        "target_slides": plan.get("target_slides"),
        "notes_pages": sum(1 for s in audit_obj.get("slide_summary", []) if s.get("notes_len", 0) > 0),
        "figures_embedded": len(placed_figs),
        "figures_total": len(figs),
        "tables_pages": sum(1 for p in plan.get("pages", [])
                            if p["page_type"] == "results" and p.get("tables_on_page")),
        "previews": {
            "cover": f"{case_id}_cover_preview.png",
            "contact_schematic": f"{case_id}_slides_contact_schematic.png",
        },
        "preview_is_schematic": True,
    }

    verification = {
        "checks": audit_obj.get("checks", []),
        "render": render_log,
        "traceability": {
            "evidence_loc_frac": audit_obj.get("traceability", {}).get("evidence_loc") or None,
            "hashes": audit_obj.get("hashes", {}),
        },
    }

    result = {
        "case_id": case_id,
        "skill": {"name": SKILL_NAME, "version": SKILL_VERSION, "display": DISPLAY_NAME},
        "status": _classify(audit_obj.get("checks", [])),
        "workorder": WORKORDER,
        "task_summary": content.get("task_text", "")[:400],
        "title": content.get("title", ""),
        "subtitle": content.get("subtitle", ""),
        "audience": content.get("audience", ""),
        "duration_minutes": content.get("duration_minutes"),
        "language": content.get("language", "zh"),
        "slide_count": plan.get("planned_slides"),
        "main_result": main_result,
        "artifacts": _build_artifacts(out_dir, case_id),
        "slide_evidence": _slide_evidence(plan, content),
        "template_audit": {
            "template_source": build_audit.get("template_source"),
            "opened_from": build_audit.get("opened_from"),
            "template_fallback_used": build_audit.get("opened_from") == "builtin",
            "slide_size_emu": build_audit.get("slide_size_emu"),
            "layouts": build_audit.get("layouts", []),
            "layout_used": build_audit.get("layout_used", []),
            "layout_fallback_used": any(u.get("fallback") for u in build_audit.get("layout_used", [])),
            "dropped_original_slides": build_audit.get("dropped_original_slides", 0),
            "template_errors": build_audit.get("template_errors", []),
            "figure_adjust": build_audit.get("figure_adjust", []),
        },
        "verification": verification,
        "sources": sources,
        "uncertainty": uncertainty,
        "change_records": [],
        "status_notes": "status semantics: success=all checks ok; partial=some checks warn/fail "
                        "(recorded); failed=pipeline did not complete.",
        "generated_at": now_iso(),
        "generator": SKILL_NAME,
        "tool_versions": tool_versions(),
    }
    _echo_output_contract(content.get("output_contract") or {}, result)

    # change records: starting deck / template edits are real changes
    change_records = []
    dropped = build_audit.get("dropped_original_slides", 0)
    if dropped:
        change_records.append({
            "action": "edit_starting_deck",
            "before": {"slides": dropped},
            "after": {"slides": plan.get("planned_slides")},
            "note": "starting deck was edited in place: original slides replaced by planned pages "
                    "(template/layout placeholders reused where available).",
        })
    result["change_records"] = change_records

    # contract self-check: validate in memory, then append the check to both
    # audit.json and result.json so the record is consistent.
    import validate_result as validate_mod
    ok, problems = validate_mod.validate(case_path, result=result, verbose=False)
    contract_check = {
        "check": "result.contract",
        "level": "ok" if ok else "warn",
        "detail": "result.json conforms to OUTPUT_CONTRACT" if ok else "; ".join(problems),
    }
    audit_obj["checks"].append(contract_check)
    dump_json(os.path.join(out_dir, "audit.json"), audit_obj)
    result["verification"]["checks"] = list(audit_obj["checks"])
    result["verification"]["traceability"]["contract_ok"] = ok
    result["status"] = _classify(audit_obj["checks"])
    dump_json(os.path.join(out_dir, "result.json"), result)

    # leave a human-readable summary too
    summary_lines = [
        f"case_id      : {case_id}",
        f"status       : {result['status']}",
        f"slides       : {result['slide_count']} (planned {main_result['target_slides']})",
        f"deck         : {main_result['deck']['path']}",
        f"previews     : cover/schematic contact sheet (PIL schematic, see render_log.json)",
        f"figures      : {main_result['figures_embedded']}/{main_result['figures_total']} placed",
        f"checks       : {len(verification['checks'])} total",
    ]
    with open(os.path.join(out_dir, "summary.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(summary_lines) + "\n")

    print(f"main ok: case={case_id} status={result['status']} slides={result['slide_count']} "
          f"out={os.path.abspath(out_dir)}")
    return result


def main(argv=None):
    utf8_writer()
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case", required=True, help="path to case.json")
    ap.add_argument("--task", default=None, help="path to task.md")
    ap.add_argument("--work", default=None, help="material base dir (/app/work)")
    ap.add_argument("--template", default="", help="explicit template pptx (overrides case.template)")
    ap.add_argument("--starting-deck", default="", help="explicit starting deck (edits it)")
    ap.add_argument("--out", required=True, help="output dir (/app/output)")
    a = ap.parse_args(argv)

    try:
        run(a.case, a.task, a.work, a.out, a.template, a.starting_deck)
        return 0
    except Exception as exc:
        # honest partial/failed record even on pipeline failure
        os.makedirs(a.out, exist_ok=True)
        failed = {
            "case_id": os.path.splitext(os.path.basename(a.case))[0],
            "skill": {"name": SKILL_NAME, "version": SKILL_VERSION, "display": DISPLAY_NAME},
            "status": "failed",
            "workorder": WORKORDER,
            "main_result": {},
            "artifacts": [],
            "sources": [],
            "uncertainty": [{"item": "pipeline", "note": f"{type(exc).__name__}: {exc}"}],
            "change_records": [],
            "status_notes": "pipeline failed before completing; partial artifacts (if any) are listed above.",
            "generated_at": now_iso(),
            "generator": SKILL_NAME,
            "tool_versions": tool_versions(),
        }
        dump_json(os.path.join(a.out, "result.json"), failed)
        print(f"main FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())