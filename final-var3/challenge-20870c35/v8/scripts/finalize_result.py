#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
finalize_result.py — assemble the final result.json envelope and self_check
from all pipeline stages.  (verification/收敛 role; corresponds to the
high-score finalize_result / result envelope pattern.)

Responsibilities:
  * build the top-level result dict (case metadata, main_line, pages,
    evidence_map, artifacts incl. audit files, sources, uncertainty,
    change_records, contract record)
  * embed the three audits as result.audit.{evidence,deck,plan_gates} so the
    whole audit chain travels with the result (G-verify visibility)
  * apply the output_contract (four-shape echo: missing fields initialized to
    "" / [] / {} / 0 — never null) and record applied fields
  * write result.json and self_check.json (validate + contract_check +
    contract_applied + determinism probe)
"""

import json
import os

from common import (utc_now, write_json,
                    apply_contract, deterministic_sha)
import validate_result as vr
import check_contract as cc


def _main_line_from_pages(plan):
    main_line = {"research_question": [], "method": [], "results": [],
                 "limitations": [], "conclusion": []}
    for p in plan["pages"]:
        e0 = (p.get("evidence") or [{}])[0]
        item = {"claim": p.get("claim", ""), "evidence": e0.get("locator", ""),
                "page_no": p["page_no"]}
        b = p.get("block")
        if b == "motivation":
            main_line["research_question"].append(item)
        elif b == "method":
            main_line["method"].append(item)
        elif b == "results":
            main_line["results"].append(item)
        elif b in ("limits", "conclusion_risk", "innovation_limits"):
            main_line["limitations"].append(item)
        elif b == "conclusion":
            main_line["conclusion"].append(item)
    return main_line


def _sources_from_records(material_records):
    sources = []
    for rec in material_records:
        sources.append({
            "file": rec.get("file"), "path": rec.get("path"), "kind": rec.get("kind"),
            "parsed": rec.get("parsed", False), "note": rec.get("note", ""),
            "char_count": rec.get("char_count", 0),
            "sections": [{"heading": s.get("heading"), "start_line": s.get("start_line"),
                          "end_line": s.get("end_line")} for s in rec.get("sections", [])],
        })
    return sources


def finalize_result(stage):
    """stage: dict of pipeline state built by main.py.  Writes result.json and
    self_check.json into stage["out_dir"]; returns (result, self_check,
    final_status)."""
    case = stage["case"]
    plan = stage["plan"]
    out_dir = stage["out_dir"]
    change_records = stage["change_records"]
    specs = stage["specs"]
    declared_note = stage["declared_note"]
    status = stage["status"]

    sources = _sources_from_records(stage["material_records"])

    previews_art = {"cover": None, "grid": None, "manifest": None, "slide_pngs": []}
    for r_ in stage["preview_records"]:
        tag = r_["file"].split("/")[-1]
        if tag.startswith("cover_"):
            previews_art["cover"] = r_["file"]
        elif tag.startswith("preview_grid"):
            previews_art["grid"] = r_["file"]
        elif tag == "preview_manifest.json":
            previews_art["manifest"] = r_["file"]
        elif tag.startswith("slide_"):
            previews_art["slide_pngs"].append(r_["file"])

    artifacts = {
        "editable_deck": "editable_deck.pptx" if stage["deck_ok"] else None,
        "talk_plan": "talk_plan.json",
        "evidence_map": "evidence_map.json",
        "evidence_audit": "evidence_audit.json" if stage["evidence_audit"] else None,
        "deck_audit": "deck_audit.json" if stage["deck_audit"] else None,
        "plan_gates": "plan_gates.json" if stage["plan_gates"] else None,
        "previews": previews_art,
        "template_used": (os.path.basename(stage["template_path"])
                          if stage.get("template_path") else None),
        "deck_mode": stage["deck_result"]["mode"] if stage["deck_ok"] else None,
        "preview_note": stage["preview_limitation"],
        "deck_limitation": stage.get("deck_failure"),
    }

    result = {
        "case_id": stage["case_id"],
        "status": status,
        "title": str(case.get("title") or ""),
        "report_goal": str(case.get("report_goal") or ""),
        "audience": plan["audience"],
        "duration_min": plan["timing"]["duration_min"],
        "slide_count": plan["timing"]["slide_target"],
        "summary": {
            "narrative_order": plan["narrative"]["order_blocks"],
            "plan_file": "talk_plan.json",
            "pages_total": len(plan["pages"]),
        },
        "main_line": _main_line_from_pages(plan),
        "pages": plan["pages"],
        "evidence_map": stage["evidence_map"],
        "artifacts": artifacts,
        "sources": sources,
        "uncertainty": stage["uncertainty"],
        "contract": {"declared_source": "", "applied": []},
        "change_records": change_records,
        "environment": stage.get("environment") or {},
        "generated_by": "main.py + finalize_result.py of academic-talk-organizer "
                        "(efficiency-3, challenge-20870c35, v2)",
        "generated_at": utc_now(),
    }

    # embed audits so the gate chain travels with the result
    result["audit"] = {
        "plan_gates": stage["plan_gates"],
        "evidence": stage["evidence_audit"],
        "deck": stage["deck_audit"],
    }

    # ---- output_contract (four-shape echo, never null) ----
    # v8 increment (D1): snapshot the names the pipeline really produced BEFORE the
    # contract echo runs.  check_contract() uses this to tell "the pipeline produced
    # this with a real value, the declaration disagrees about its container" (report,
    # never fail) apart from "a declared field is missing entirely" (still hard-fail).
    produced_names = sorted(k for k, v in result.items() if v is not None)
    result, initialized = apply_contract(result, specs)
    result["contract"] = {"declared_source": " + ".join(declared_note),
                          "applied": [s[0] for s in specs],
                          "pipeline_produced_fields": produced_names,
                          "echo_initialized_fields": sorted(initialized)}

    # ---- self check (validate + contract) ----
    validate_report = vr.validate(result, out_dir, strict=False)
    contract_report = cc.check(result, specs, result["contract"]["declared_source"],
                               produced_names=produced_names)
    determinism = None
    try:
        plan_path = os.path.join(out_dir, "talk_plan.json")
        emap_path = os.path.join(out_dir, "evidence_map.json")
        with open(plan_path, "r", encoding="utf-8") as fh:
            plan_obj = json.load(fh)
        with open(emap_path, "r", encoding="utf-8") as fh:
            emap_obj = json.load(fh)
        determinism = {
            "method": "content projection sha256 (recording timestamps stripped: "
                      "generated_at/at/ts/timestamp/created/modified)",
            "plan_sha16": deterministic_sha(plan_obj),
            "evidence_map_sha16": deterministic_sha(emap_obj),
            "deck_pptx_normalized_sha16": stage["deck_normalized_sha"],
        }
    except Exception as exc:  # noqa: BLE001
        determinism = {"method": "probe failed: %s" % exc}

    plan_g_valid = bool(stage["plan_gates"] and stage["plan_gates"].get("valid"))
    ev_g_valid = bool(stage["evidence_audit"] and stage["evidence_audit"].get("valid"))
    deck_g_valid = bool(stage["deck_audit"] and stage["deck_audit"].get("valid"))
    pages_ok = any(c.get("check") == "pages non-empty" and c.get("ok")
                   for c in validate_report.get("checks", []))
    result["audit"]["gates"] = {
        "G1": True,  # result.json written with case_id (verified below by validate)
        "G2": bool(contract_report and contract_report.get("valid")),
        "G3": bool(pages_ok),
        "G4": plan_g_valid,
        "G5": ev_g_valid,
        "G6": deck_g_valid,
        "G7": deck_g_valid,
        "G8": bool(stage["preview_ok"]),
        "G9": bool(determinism and determinism.get("plan_sha16")),
        "G10": None,  # package-constraint audit lives in selftest.py --package-check
    }

    result_path = os.path.join(out_dir, "result.json")
    write_json(result_path, result)
    change_records.append({"at": utc_now(), "step": "result",
                           "action": "wrote result.json (status=%s; contract from %s; initialized %s)" % (
                               status, result["contract"]["declared_source"], initialized)})

    self_check = {
        "validate": validate_report,
        "contract_check": contract_report,
        "contract_applied": [s[0] for s in specs],
        "plan_gates": stage["plan_gates"],
        "audit_gates": result["audit"]["gates"],
        "determinism": determinism,
        "generated_at": utc_now(),
    }
    self_check_path = os.path.join(out_dir, "self_check.json")
    write_json(self_check_path, self_check)

    if not validate_report["valid"] and result["status"] != "failed":
        old = result["status"]
        result["status"] = "partial"
        result["uncertainty"].append({
            "item": "自检发现结构问题（见 self_check.json）",
            "impact": "状态由 %s 降级为 partial" % old,
            "mitigation": "按 self_check.json 的 errors 修复后重跑"})
        write_json(result_path, result)
        validate_report2 = vr.validate(result, out_dir, strict=False)
        self_check["validate_after_downgrade"] = validate_report2
        write_json(self_check_path, self_check)
        final_status = "partial"
    else:
        final_status = result["status"]
    return result, self_check, final_status