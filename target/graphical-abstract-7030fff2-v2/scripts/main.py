# -*- coding: utf-8 -*-
"""Graphical Abstract skill -- orchestrator (figures group, pku-efficiency-3) v2.

Usage:
    python scripts/main.py --case examples/case.json --out <outdir> \
        [--task examples/task.md] [--material examples/] [--raster-scale 2] \
        [--pdf|--no-pdf] [--plan plan.json]

Pipeline (all steps operate on *actual* input files; nothing is assumed):
    0. plan-first (design-first): optional --plan plan.json (scaffolded by
       scripts/scaffold.py, finalized by the agent); linted with spec_lint.
    1. read case.json  (hard fail if unreadable)
    2. resolve task.md + material files (CLI override > case.json > defaults)
    3. extract entities / relations / data / panel points (source-bound)
    4. build deterministic figure spec + layout
    5. lint the produced spec (spec_lint) — problems recorded in result.json
    6. write editable layered SVG (real source file)
    7. render PNG (+ optional PDF) preview  (backend chain w/ honest log)
    8. audit self-checks on the produced files (incl. four-element coverage,
       layer naming, determinism)
    9. write result.json (output_contract echo + envelope + provenance + plan)

Exit codes: 0 = success (may include warnings -> status "partial"),
            1 = hard input error, 2 = internal error (stderr explains).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import (SCHEMA_VERSION, SKILL_ROOT, SKILL_VERSION, sha256_file,  # noqa: E402
                    write_json)
from extract import run as extract_run  # noqa: E402
from figurespec import build as spec_build  # noqa: E402
from svgbuilder import write as svg_write  # noqa: E402
from preview import render as preview_render  # noqa: E402
from audit import audit  # noqa: E402
import spec_lint  # noqa: E402

RESERVED_ENVELOPE = {
    "schema_version", "case_id", "status", "summary", "deliverables",
    "content_summary", "provenance", "sources", "uncertainty",
    "change_records", "warnings", "output_contract_echo", "generated_utc",
    "skill", "audit", "task",
}


def main() -> int:
    # Windows console: ensure UTF-8/stdout survives CJK output
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

    args = _parse_args()
    out_dir = os.path.abspath(args.out)
    os.makedirs(out_dir, exist_ok=True)

    # ---- 0. design-first plan (optional) ------------------------------------
    plan = None
    plan_source = "none"
    plan_lint = {"valid": True, "problems": []}
    if args.plan:
        if os.path.isfile(args.plan):
            with open(args.plan, encoding="utf-8") as fh:
                plan = json.load(fh)
            plan_source = os.path.abspath(args.plan)
            plan_lint = spec_lint.lint_plan(plan)
        else:
            plan_lint = {"valid": False,
                         "problems": [f"plan file not found: {args.plan}"]}
    # plan may carry figure_constraints the case does not (design first)
    plan_overrides = {}
    if plan:
        pc = plan.get("figure_constraints") or plan.get("constraints") or {}
        for k in ("width", "height", "dpi", "colorblind", "flow_arrows",
                  "raster_scale", "pdf", "language"):
            if k in pc and pc[k] is not None:
                plan_overrides[k] = pc[k]

    # ---- 1. read the actual case -----------------------------------------
    case_path = os.path.abspath(args.case)
    if not os.path.isfile(case_path):
        print(json.dumps({"status": "failed", "error": f"case.json not found: {case_path}"},
                         ensure_ascii=False))
        return 1

    task_path = os.path.abspath(args.task) if args.task else None
    material = os.path.abspath(args.material) if args.material else None
    # default task.md lives next to case.json (help text promises this)
    if task_path is None:
        cand = os.path.join(os.path.dirname(case_path), "task.md")
        if os.path.isfile(cand):
            task_path = os.path.abspath(cand)
    change_notes = []

    try:
        content = extract_run(case_path, task_path, material)
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"status": "failed", "error": f"extraction failed: {type(e).__name__}: {e}"},
                         ensure_ascii=False))
        return 1

    case_id = content["case_id"]
    if not content["title"]:
        content["title"] = f"Graphical Abstract — {case_id}"

    # 0b. design-first plan overrides applied to constraints (plan wins on
    #     design decisions; source content still comes from the material).
    for k, v in plan_overrides.items():
        content.setdefault("constraints", {})[k] = v
    if plan_source != "none" and plan_overrides:
        change_notes.append(f"plan {os.path.basename(plan_source)} overrode constraints: "
                            + ", ".join(sorted(plan_overrides)))

    # ---- 2. figure spec (deterministic layout) ----------------------------
    try:
        spec = spec_build(content)
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"status": "failed", "error": f"layout failed: {type(e).__name__}: {e}"},
                         ensure_ascii=False))
        return 2

    # ---- 2b. lint the produced spec before drawing (CP1b) --------------------
    spec_lint_rep = spec_lint.lint(spec, content)
    for p in spec_lint_rep["problems"]:
        change_notes.append("spec_lint: " + p)

    # ---- 3. editable SVG source -------------------------------------------
    stem = f"{case_id}_graphical_abstract"
    svg_path = os.path.join(out_dir, stem + ".svg")
    try:
        svg_write(spec, svg_path)
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"status": "failed", "error": f"svg write failed: {type(e).__name__}: {e}"},
                         ensure_ascii=False))
        return 2

    # ---- 4. rendered previews ----------------------------------------------
    scale = content["constraints"].get("raster_scale", 2)
    pdf_path = os.path.join(out_dir, stem + ".pdf") if content["constraints"].get("pdf", True) else None
    try:
        render_report = preview_render(spec, os.path.join(out_dir, stem + ".png"),
                                       scale=scale, out_pdf=pdf_path)
    except Exception as e:  # noqa: BLE001
        render_report = {"backend": "none", "error": f"{type(e).__name__}: {e}"}
        pdf_path = None

    # ---- 5. audit self-checks ----------------------------------------------
    try:
        audit_report = audit(spec, content, svg_path,
                             os.path.join(out_dir, stem + ".png"), pdf_path)
    except Exception as e:  # noqa: BLE001
        audit_report = {"checks": {"error": f"{type(e).__name__}: {e}"}}

    # ---- 6. transparency artifacts ------------------------------------------
    write_json(os.path.join(out_dir, "content.json"), content)
    write_json(os.path.join(out_dir, "spec.json"), spec)
    write_json(os.path.join(out_dir, "audit.json"), audit_report)

    # ---- 7. result.json ------------------------------------------------------
    warnings = []
    warnings += content.get("notes", [])
    warnings += spec.get("layout_log", [])
    warnings += render_report.get("warnings", [])
    warnings += [m for m in audit_report.get("missing_values", [])]

    uncertainty = []
    if audit_report.get("missing_values"):
        uncertainty.append("以下数据点缺少可核验数值："
                           + ", ".join(audit_report["missing_values"])
                           + "（已在图上以“数值缺失”占位标记，未编造数值）")
    if audit_report.get("entity_coverage", {}).get("missing"):
        uncertainty.append("以下实体未能上画布："
                           + ", ".join(audit_report["entity_coverage"]["missing"]))
    if audit_report.get("bounds", {}).get("outside_count", 0):
        uncertainty.append(f"{audit_report['bounds']['outside_count']} 个元素超出画布边界，请检查。")
    if render_report.get("matplotlib_failed"):
        uncertainty.append("matplotlib 渲染不可用，已回退到备用渲染器："
                           + str(render_report["matplotlib_failed"]))
    uncertainty += [u for u in content.get("uncertainty", [])]
    for p in spec_lint_rep["problems"]:
        uncertainty.append("spec_lint: " + p)

    if plan_lint.get("problems"):
        uncertainty.append("plan lint problems: " + "; ".join(plan_lint["problems"][:6]))

    change_records = [
        {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "what": "skill run (graphical-abstract v" + SKILL_VERSION + ")"},
        {"ts": "-", "what": "deliverables generated by scripts/main.py; layout deterministic"},
    ]
    for f in content.get("source_files", []):
        change_records.append({"ts": "-", "what": f"read source: {f['path']} (sha256 {f['sha256'][:12]})"})
    if isinstance(content.get("output_contract"), dict) and content["output_contract"].get("change_notes"):
        change_records.append({"ts": "-", "what": "case-provided change notes: "
                               + str(content["output_contract"]["change_notes"])})

    deliverables = [
        {"kind": "editable_source", "format": "svg",
         "path": stem + ".svg",
         "layers": spec["layers"],
         "element_count": len(spec["elements"]),
         "checks": audit_report.get("checks", {}).get("svg_well_formed", {})},
        {"kind": "layout_spec", "format": "json", "path": "spec.json",
         "note": "machine-readable figure spec (same geometry as SVG)"},
        {"kind": "preview", "format": "png",
         "path": stem + ".png",
         "backend": render_report.get("backend"),
         "checks": audit_report.get("checks", {}).get("png", {})},
    ]
    if render_report.get("pdf") and render_report["pdf"].get("present"):
        deliverables.append({"kind": "preview", "format": "pdf",
                             "path": stem + ".pdf",
                             "checks": audit_report.get("checks", {}).get("pdf", {})})
    else:
        pdf_reason = None
        if render_report.get("pdf") is not None:
            pdf_reason = render_report["pdf"].get("reason")
        elif pdf_path is None:
            pdf_reason = "disabled by constraints (pdf=false)"
        deliverables.append({"kind": "preview", "format": "pdf",
                             "path": None, "present": False, "reason": pdf_reason})

    main_status = _status(audit_report, render_report, content)
    if main_status == "success" and not spec_lint_rep["valid"]:
        main_status = "partial"   # lint problems must never be hidden behind success

    result = {
        "schema_version": SCHEMA_VERSION,
        "skill": {"name": "graphical-abstract", "version": SKILL_VERSION},
        "case_id": case_id,
        "status": main_status,
        "plan": {"source": plan_source,
                 "hash": plan_lint.get("plan_hash"),
                 "lint": plan_lint},
        "spec_lint": spec_lint_rep,
        "summary": (f"已生成 {len(spec['elements'])} 个图形元素（实体 {len(content['entities'])}、"
                    f"关系 {len(content['relations'])}、数据 {len(content['data'])}）的图形摘要；"
                    f"SVG 可编辑源 + PNG{'+PDF' if any(d.get('format')=='pdf' and d.get('present') for d in deliverables) else ''} 预览已导出。"),
        "task": content.get("task", ""),
        "deliverables": deliverables,
        "content_summary": {
            "entities": len(content["entities"]),
            "relations": len(content["relations"]),
            "data": len(content["data"]),
            "panels": {p: len(content.get("panels", {}).get(p, [])) for p in
                       ("question", "method", "results", "conclusion")},
            "reading_order": spec.get("reading_order", []),
        },
        "provenance": {
            "source_files": [{"path": s["path"], "sha256": s["sha256"], "role": s["role"]}
                             for s in content.get("source_files", [])],
            "note": ("每个画布元素带 data-src 属性指向来源；"
                     "layout 由纯函数生成，同输入必同输出。"),
        },
        "sources": [{"ref": f['path'], "role": f['role']} for f in content.get("source_files", [])],
        "uncertainty": uncertainty,
        "warnings": warnings,
        "change_records": change_records,
        "audit": audit_report,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    # echo every case-provided output_contract field (contract requirement)
    contract = content.get("output_contract") or {}
    contract_echo = {}
    for k, v in contract.items():
        if k in RESERVED_ENVELOPE:
            contract_echo[k] = v
        else:
            result[k] = v  # top-level mirror when no collision
    result["output_contract_echo"] = contract_echo

    write_json(os.path.join(out_dir, "result.json"), result)

    print(json.dumps({"status": result["status"], "case_id": case_id,
                      "deliverables": [d.get("path") for d in deliverables],
                      "audit": {k: v for k, v in audit_report.items()
                                if k != "checks"},
                      "out": out_dir}, ensure_ascii=False, indent=2))
    return 0 if result["status"] != "failed" else 2


def _status(audit_report, render_report, content) -> str:
    wf = audit_report.get("checks", {}).get("svg_well_formed", {})
    if not wf.get("ok"):
        return "failed"
    png = audit_report.get("checks", {}).get("png", {})
    if not png.get("ok"):
        return "failed"
    problems = (len(audit_report.get("missing_values", []))
                + len(audit_report.get("entity_coverage", {}).get("missing", []))
                + audit_report.get("bounds", {}).get("outside_count", 0)
                + len(content.get("notes", [])))
    return "success" if problems == 0 else "partial"


def _parse_args():
    ap = argparse.ArgumentParser(
        prog="graphical-abstract",
        description="Graphical Abstract skill runner (figures group)")
    ap.add_argument("--case", required=True, help="path to case.json")
    ap.add_argument("--task", default=None, help="path to task.md (auto: <case_dir>/task.md)")
    ap.add_argument("--material", default=None,
                    help="material file or directory (auto: case.json source_material)")
    ap.add_argument("--out", default=os.path.join(SKILL_ROOT, "out"),
                    help="output directory (default: <skill>/out)")
    ap.add_argument("--raster-scale", type=int, default=None,
                    help="PNG scale vs canvas (default: constraints.raster_scale)")
    ap.add_argument("--plan", default=None,
                    help="design plan json from scripts/scaffold.py (design-first; optional)")
    ap.add_argument("--pdf", dest="pdf", action="store_true", default=None,
                    help="produce PDF preview (default: constraints.pdf)")
    ap.add_argument("--no-pdf", dest="pdf", action="store_false", default=None)
    return ap.parse_args()


if __name__ == "__main__":
    sys.exit(main())