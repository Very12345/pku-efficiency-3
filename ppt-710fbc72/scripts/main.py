# -*- coding: utf-8 -*-
"""main.py — orchestration entry point for the Academic Slide Adapter Skill (v2).

Two-phase workflow:
  phase 1 (plan):  extract -> deckplan -> adopt_plan (template audit +
                   page->layout assignment + batch rules + figure plan) [CP1]
  phase 2 (build): adapt_pptx -> preview -> audit -> result.json -> CP3 gates

Pipeline:
  extract -> deckplan -> adopt_plan -> adapt_pptx -> preview -> audit
  -> result.json (output_contract echo, honest status) -> validate_result
  + check_contract (G1–G8) inline.

Usage:
  python scripts/main.py --case <case.json> [--task <task.md>]
      [--work <material base dir>] [--template <template.pptx>]
      [--starting-deck <deck.pptx>] --out <output dir>
"""
from __future__ import annotations

import os
import re
import sys
import json

import common
from common import (utf8_writer, SKILL_NAME, SKILL_VERSION, DISPLAY_NAME, WORKORDER,
                    dump_json, tool_versions, now_iso, load_json, sha256_file,
                    portable_path)
import make_template as make_template_mod

# NOTE: the pipeline modules (extract / deckplan / adopt_plan / adapt_pptx /
# preview / audit) are imported *inside* run(), not here.  adapt_pptx imports
# python-pptx and preview imports Pillow at module level, so a missing runtime
# dependency must surface inside the pipeline's try-block: that way main()
# still writes an honest status=failed result.json (see D12 / failure-modes
# F21-F22) instead of dying with a bare ImportError traceback.
SHIPPED_BUILTIN = os.path.join(common.skill_root(), "templates", "builtin.pptx")


def resolve_builtin(out_dir: str) -> tuple:
    """Return (path, note) of the builtin fallback template.

    The skill carries no .pptx binary (Skill resources are UTF-8 text only),
    so the fallback template is regenerated deterministically at run time into
    `<out>/_runtime/`.  When python-pptx is unavailable the chain simply has
    no builtin candidate and the failure is recorded honestly (D6).
    """
    return make_template_mod.ensure_builtin(
        shipped=SHIPPED_BUILTIN, cache_dir=os.path.join(out_dir, "_runtime"))



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


def _derive_contract_value(key, result):
    """Honest value for an output_contract key the run has no native field for.

    Each official case declares its own contract keys, so the mapping is
    name-based.  Without it the echo would fall back to the *type default*,
    which for a boolean contract is `false` — i.e. the result would deny
    deliverables that do exist (PDF export excepted: it genuinely is not
    produced without PowerPoint/LibreOffice).  Returns (handled, value).
    """
    k = re.sub(r"[^a-z0-9]", "", str(key).lower())
    ta = result.get("template_audit") or {}
    mr = result.get("main_result") or {}
    ev = result.get("slide_evidence") or []
    deck_ok = bool((mr.get("deck") or {}).get("path"))
    notes_full = bool(mr.get("notes_pages")) and mr.get("notes_pages") == result.get("slide_count")

    if not k:
        return False, None
    if "pdf" in k and "preview" not in k:                      # honest capability gap
        return True, False
    if "preview" in k or "schematic" in k or "png" in k or "thumbnail" in k:
        return True, bool(mr.get("previews"))
    if "note" in k or "speaker" in k:
        return True, notes_full
    if "evidence" in k or "citation" in k or "traceab" in k or "source" in k or "locator" in k:
        return True, bool(ev)
    if "template" in k or "inherit" in k or "master" in k or "layout" in k or "theme" in k:
        return True, bool(ta.get("layout_used")) and bool(ta.get("opened_from"))
    if "adopt" in k or "adapt" in k or "plan" in k:
        return True, bool(result.get("adopt_plan"))
    if "editable" in k or "deck" in k or "pptx" in k or "presentation" in k or "office" in k:
        return True, deck_ok
    if "slide" in k or "page" in k:
        if any(w in k for w in ("count", "number", "num", "total")):
            return True, result.get("slide_count")
        return True, bool(ev)
    if "figure" in k or "chart" in k or "table" in k or "image" in k:
        return True, bool(mr.get("figures_total")) or bool(mr.get("tables_pages"))
    return False, None


def _echo_output_contract(contract: dict, result: dict) -> dict:
    """Mirror every output_contract key into result top level; fill unseen
    keys with a genuine derived value when the run knows one, otherwise with
    the declared type default (never a None placeholder)."""
    derived = {}
    for key, val in (contract or {}).items():
        if key in result:
            continue
        handled, value = _derive_contract_value(key, result)
        result[key] = value if handled else _type_default(val)
        if handled:
            derived[key] = result[key]
    if derived:
        result.setdefault("verification", {})["contract_echo_derived"] = derived
    return result



def _build_artifacts(out_dir: str, case_id: str) -> list:
    files = [
        ("deck", "pptx", f"{case_id}_deck.pptx", []),
        ("cover_preview", "png", f"{case_id}_cover_preview.png", []),
        ("contact_preview", "png", f"{case_id}_slides_contact_schematic.png", []),
        ("plan spec", "json", "spec.json", []),
        ("adaptation plan", "json", "adopt_plan.json", []),
        ("content", "json", "content.json", []),
        ("audit", "json", "audit.json", []),
        ("render log", "json", "render_log.json", []),
    ]
    # NOTE: result.json itself is deliberately NOT listed (its sha256 would be
    # self-referential and the artifact list would shift run-to-run); the
    # contract validation + CP3 gates check result.json separately.
    arts = []
    for role, fmt, name, extra in files:
        p = os.path.join(out_dir, name)
        if os.path.exists(p):
            arts.append({
                "role": role, "format": fmt, "path": name,
                "abspath": portable_path(p),
                "checks": {"exists": True, "sha256": sha256_file(p)},
                "extra": extra,
            })
    return arts


def _slide_evidence(plan: dict) -> list:
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
    if any(l in ("fail", "warn") for l in levels):
        return "partial"
    return "success"


def run(case_path: str, task_path: str | None, work_dir: str | None,
        out_dir: str, template: str = "", starting_deck: str = "") -> dict:
    import extract as extract_mod
    import deckplan as deckplan_mod
    import adopt_plan as adopt_plan_mod
    import adapt_pptx as adapt_pptx_mod
    import preview as preview_mod
    import audit as audit_mod

    os.makedirs(out_dir, exist_ok=True)

    # 1 extract
    content = extract_mod.extract(case_path, task_path, work_dir, out_dir)
    dump_json(os.path.join(out_dir, "content.json"), content)
    case_id = content["case_id"]

    # 2 page plan (deterministic)
    plan = deckplan_mod.plan(content)
    dump_json(os.path.join(out_dir, "spec.json"), plan)

    # 3 phase 1: adaptation plan (template audit + assignments + batch rules)
    tpl = template or content.get("template_path") or ""
    sdeck = starting_deck or content.get("starting_deck_path") or ""
    builtin, builtin_note = resolve_builtin(out_dir)
    adopt = adopt_plan_mod.build_plan(content, plan, tpl, sdeck, builtin)
    dump_json(os.path.join(out_dir, "adopt_plan.json"), adopt)
    adopt_gates_ok = bool((adopt.get("gates") or {}).get("ok"))

    # 4 phase 2: build editable pptx applying the plan
    pptx_out = os.path.join(out_dir, f"{case_id}_deck.pptx")
    build_audit = adapt_pptx_mod.build(content, plan, pptx_out, tpl, sdeck,
                                       builtin, adopt)


    # 5 preview (schematic PIL, honestly labelled)
    render_log = preview_mod.render_all(content, plan, out_dir, case_id)

    # 6 audit over real artifacts
    audit_obj = audit_mod.audit(content, plan, out_dir, case_id, build_audit, adopt)

    # 7 result.json envelope
    sources = [{"rel": s.get("rel"), "exists": s.get("exists", False),
                "lines": s.get("lines", 0)} for s in content.get("sources", [])]
    figs = content.get("figures") or []
    tables = content.get("tables") or []
    placed_figs = [f["id"] for f in figs
                   if any(f["id"] in (p.get("figure_refs") or [])
                          for p in plan.get("pages", []) if p["page_type"] == "results")]
    uncertainty = list(content.get("uncertainty", []))
    for c in audit_obj.get("checks", []):
        if c["level"] in ("warn", "fail"):
            uncertainty.append({"item": f"check:{c['check']}", "note": c["detail"]})
    for f in figs:
        if not f.get("file_exists"):
            uncertainty.append({"item": f"figure {f['id']} source image",
                                "note": "source image missing/unavailable -> placeholder box with caption; original caption kept"})
    for t in tables:
        if not t.get("rows"):
            uncertainty.append({"item": f"table {t['id']}",
                                "note": "no row data available -> caption-only mention"})
    if not adopt_gates_ok:
        uncertainty.append({"item": "adopt_plan.gates",
                            "note": "phase-1 adaptation plan gates not all ok; see adopt_plan.json gates"})
    if build_audit.get("opened_from") == "builtin":
        uncertainty.append({
            "item": "builtin fallback template",
            "note": ("no usable case template/starting deck: the 16:9 fallback template was "
                     f"regenerated at run time ({builtin_note}) because Skill resources are "
                     "text-only; placeholder inheritance was audited normally."),
        })
    elif not builtin and builtin_note:
        uncertainty.append({"item": "builtin fallback template", "note": builtin_note})


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

    template_audit = {
        "template_source": build_audit.get("template_source"),
        "opened_from": build_audit.get("opened_from"),
        "template_fallback_used": build_audit.get("opened_from") == "builtin",
        "slide_size_emu": build_audit.get("slide_size_emu"),
        "layout_scores_concept": "masters/layouts/placeholders enumerated by python-pptx; see adopt_plan.json layouts",
        "layouts": build_audit.get("layouts", []),
        "layout_used": build_audit.get("layout_used", []),
        "layout_fallback_used": any(u.get("fallback") for u in build_audit.get("layout_used", [])),
        "dropped_original_slides": build_audit.get("dropped_original_slides", 0),
        "template_errors": build_audit.get("template_errors", []),
        "figure_adjust": build_audit.get("figure_adjust", []),
        "theme": (adopt.get("template") or {}).get("theme", {}),
        "adopt_plan_applied": build_audit.get("adopt_plan_applied"),
        "adopt_plan_total_pages": build_audit.get("adopt_plan_total_pages"),
        "adopt_plan_deviations": build_audit.get("adopt_plan_deviations", []),
    }

    adopt_summary = {
        "source": (adopt.get("template") or {}).get("opened_from"),
        "pages_assigned": len(adopt.get("page_assignments", [])),
        "layout_gaps": adopt.get("layout_gaps", []),
        "batch_deviations": adopt.get("batch", {}).get("deviations", []),
        "figure_plan": len(adopt.get("figure_plan", [])),
        "gates": adopt.get("gates", {}),
    }

    verification = {
        "checks": audit_obj.get("checks", []),
        "render": render_log,
        "traceability": {
            "evidence_loc_frac": (audit_obj.get("traceability") or {}).get("evidence_loc", 0.0),
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
        "slide_evidence": _slide_evidence(plan),
        "template_audit": template_audit,
        "adopt_plan": adopt_summary,
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
    if build_audit.get("adopt_plan_deviations"):
        change_records.append({
            "action": "adopt_plan_deviations",
            "before": {"deviations": 0},
            "after": {"deviations": len(build_audit["adopt_plan_deviations"])},
            "note": "phase-1 recommended layouts not fully applicable during phase-2; "
                    "best-fit used and listed in template_audit.adopt_plan_deviations.",
        })
    result["change_records"] = change_records

    # 8 verify: contract validation + CP3 gates (independent re-check)
    import validate_result as validate_mod
    import check_contract as check_mod
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

    # ---- write result.json then run CP3 gates against the real files -------
    dump_json(os.path.join(out_dir, "result.json"), result)
    gates = check_mod.run_gates(result, out_dir, load_json(case_path) if os.path.exists(case_path) else {})
    all_gates = all(g["ok"] for g in gates)
    gates_check = {
        "check": "result.contract_gates",
        "level": "ok" if all_gates else "warn",
        "detail": "check_contract G1-G8 all pass" if all_gates
                  else "check_contract failed gates: " + ", ".join(
                      f"{g['gate']}({g['detail']})" for g in gates if not g["ok"]),
    }
    audit_obj["checks"] = [c for c in audit_obj["checks"] if c["check"] != "result.contract_gates"]
    audit_obj["checks"].append(gates_check)
    dump_json(os.path.join(out_dir, "audit.json"), audit_obj)
    result["verification"]["checks"] = list(audit_obj["checks"])
    result["verification"]["contract_gates"] = gates
    result["status"] = _classify(audit_obj["checks"])
    result["generated_at"] = now_iso()  # single authoritative timestamp in final file
    dump_json(os.path.join(out_dir, "result.json"), result)

    summary_lines = [
        f"case_id      : {case_id}",
        f"status       : {result['status']}",
        f"slides       : {result['slide_count']} (planned {main_result['target_slides']})",
        f"adopt_plan   : applied {template_audit['adopt_plan_applied']}/{template_audit['adopt_plan_total_pages']}"
        + (f", deviations={len(template_audit['adopt_plan_deviations'])}" if template_audit['adopt_plan_deviations'] else ""),
        f"deck         : {main_result['deck']['path']}",
        f"previews     : cover/schematic contact sheet (PIL schematic, see render_log.json)",
        f"figures      : {main_result['figures_embedded']}/{main_result['figures_total']} placed",
        f"checks       : {len(verification['checks'])} total, contract_gates {'ok' if all_gates else 'FAILED'}",
    ]
    with open(os.path.join(out_dir, "summary.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(summary_lines) + "\n")

    print(f"main ok: case={case_id} status={result['status']} slides={result['slide_count']} "
          f"contract_gates={'ok' if all_gates else 'FAILED'} out={portable_path(out_dir)}")
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
        try:
            os.makedirs(a.out, exist_ok=True)
        except Exception as out_exc:            # unwritable --out: say so, do not stack-trace
            print(f"main FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
            print(f"main FAILED: cannot write to --out {portable_path(a.out)!r}: "
                  f"{type(out_exc).__name__}: {out_exc}", file=sys.stderr)
            return 2
        failed = {
            "case_id": os.path.splitext(os.path.basename(a.case))[0],
            "skill": {"name": SKILL_NAME, "version": SKILL_VERSION, "display": DISPLAY_NAME},
            "status": "failed",
            "workorder": WORKORDER,
            "main_result": {},
            "artifacts": [],
            "sources": [],
            "adopt_plan": {},
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