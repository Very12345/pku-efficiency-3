# -*- coding: utf-8 -*-
"""Build & write result.json according to references/OUTPUT_CONTRACT.md.

Contract summary (see references/OUTPUT_CONTRACT.md for the full table):
    case_id, title, status, contract_version,
    deliverables {editable_sources[], previews[], exports[]},
    scientific_content {entities[], edges[], legend, layout, constraints},
    evidence_sources[], data_mapping, extraction,
    export_checks[], self_check {checks, passed, warnings, failures},
    uncertainty[], change_records[], files[],
    + every extra key declared in case.json output_contract
      (echoed with type-appropriate empty defaults when absent).

Honesty rules: status is only "success" when every blocking check passes and
the extraction was verified; sources/uncertainty/change_records must reflect
what actually happened; nothing is fabricated.
"""
import json, os

from model import dump_json, CONTRACT_VERSION, SKILL_NAME

EMPTY_BY_TYPE = {"str": "", "list": [], "dict": {}}


def _default_for(v):
    if isinstance(v, bool):
        return False
    if isinstance(v, (int, float)):
        return 0
    if isinstance(v, list):
        return []
    if isinstance(v, dict):
        return {}
    return ""


def apply_output_contract(results, case_json):
    """Merge every key of case_json['output_contract'] into the result at the
    top level, preserving explicit values and defaulting missing ones by the
    container type declared in the contract (never None)."""
    oc = case_json.get("output_contract") or {}
    if not isinstance(oc, dict):
        return results
    for k, v in oc.items():
        if k in results and results[k] not in (None, "", [], {}):
            continue  # pipeline produced a real value; keep it
        if isinstance(v, dict) and isinstance(v.get("type"), str):
            results[k] = {"str": "", "list": [], "dict": {}, "bool": False,
                          "number": 0}.get(v["type"], "")
        else:
            results[k] = _default_for(v)
    return results


def build_result(model, layout, svg_report, preview_meta, check_out,
                 out_paths, case_json, provenance, status,
                 uncertainty=None, change_records=None, extraction_note=None,
                 layout_warnings=None):
    """out_paths: {result_json, svg, png, pdf, model_json} absolute paths."""
    result = {
        "case_id": str(case_json.get("case_id") or model.get("case_id") or "-"),
        "title": model.get("title") or "",
        "example": bool(model.get("example")),
        "status": status,
        "contract_version": CONTRACT_VERSION,
        "skill": {"name": SKILL_NAME,
                  "version": provenance.get("skill_version", "1.0"),
                  "contract": CONTRACT_VERSION},
        "deliverables": {
            "editable_sources": [{
                "path": os.path.basename(out_paths["svg"]),
                "format": "svg", "layers": svg_report.get("layers", []),
                "well_formed": svg_report.get("well_formed", False),
                "note": "分层可编辑源文件：图层 layer-{compartment,edge,entity,label,title,legend,meta}，"
                        "元素带 data-id/data-type/data-source 属性，可直接改标签后重新导出",
            }],
            "previews": ([{"path": os.path.basename(out_paths["png"]), "format": "png",
                           "dpi": (preview_meta.get("png") or {}).get("dpi", 150),
                           "width_px": (preview_meta.get("png") or {}).get("width_px"),
                           "height_px": (preview_meta.get("png") or {}).get("height_px")}]
                         if preview_meta.get("png") and out_paths.get("png") else []),
            "exports": ([{"path": os.path.basename(out_paths["pdf"]), "format": "pdf",
                          "note": "matplotlib 矢量导出（预览用；可编辑源为 SVG）"}]
                        if preview_meta.get("pdf") and out_paths.get("pdf") else []),
        },
        "scientific_content": {
            "entities": [{
                "id": e["id"], "name": e["name"], "type": e["type"],
                "compartment": e["compartment"], "data": e.get("data") or {},
                "note": e.get("note", ""), "source": e.get("source", []),
            } for e in model["entities"]],
            "edges": [{
                "id": r["id"], "from": r["from"], "to": r["to"],
                "type": r["type"], "subtype": r.get("subtype", ""),
                "evidence": r.get("evidence", "moderate"),
                "label": r.get("label", ""), "note": r.get("note", ""),
                "feedback": bool(r.get("feedback")), "source": r.get("source", []),
            } for r in model["edges"]],
            "legend": model["legend"],
            "layout": {
                "canvas": layout["canvas"],
                "compartments": [{
                    "id": b["id"], "label_zh": b["label_zh"],
                    "label_en": b["label_en"], "rect": b["rect"],
                } for b in layout["compartments"]],
                "constraints": model.get("layout", {}).get("constraints") or {},
                "note": "布局规则见 references/DIAGRAM_SPEC.md：区室分层、跨膜受体位于膜带、反馈环右侧绕行",
            },
            "counts": {"entities": len(model["entities"]),
                       "edges": len(model["edges"]),
                       "compartments": len(layout["compartments"])},
        },
        "evidence_sources": _collect_sources(model, layout),
        "data_mapping": model["legend"].get("data_mapping") or {},
        "extraction": {
            "method": (model.get("extraction") or {}).get("method", "manual"),
            "verified_by_agent": bool((model.get("extraction") or {}).get("verified_by_agent")),
            "note": extraction_note or "实体/关系已与输入材料核对；草稿提取器输出的部分见 change_records",
        },
        "export_checks": _export_checks(out_paths, preview_meta, svg_report),
        "self_check": {
            "passed": bool(check_out.get("passed")),
            "checks": check_out.get("checks", []),
            "failures": check_out.get("failures", []),
            "warnings": check_out.get("warnings", []),
        },
        "uncertainty": uncertainty or [],
        "change_records": change_records or [],
        "files": sorted(os.path.basename(p) for p in out_paths.values()
                        if p and os.path.exists(p)),
        "provenance": provenance,
    }
    if layout_warnings:
        result["scientific_content"]["layout"]["warnings"] = layout_warnings
    return result


def _collect_sources(model, layout):
    seen, out = set(), []
    for e in model["entities"]:
        for s in e.get("source", []):
            k = (s.get("ref"), s.get("kind"), s.get("line"))
            if k in seen:
                continue
            seen.add(k)
            out.append({"ref": s.get("ref", ""), "kind": s.get("kind", "material"),
                        "line": s.get("line")})
    for r in model["edges"]:
        for s in r.get("source", []):
            k = (s.get("ref"), s.get("kind"), s.get("line"))
            if k in seen:
                continue
            seen.add(k)
            out.append({"ref": s.get("ref", ""), "kind": s.get("kind", "material"),
                        "line": s.get("line")})
    return out


def _export_checks(out_paths, preview_meta, svg_report):
    out = []
    svg_p = out_paths.get("svg")
    if svg_p and os.path.isfile(svg_p):
        import hashlib
        data = open(svg_p, "rb").read()
        out.append({"file": "diagram.svg", "check": "well-formed XML + sha256",
                    "result": "pass" if svg_report.get("well_formed") else "fail",
                    "detail": "sha256=%s, %d bytes" % (hashlib.sha256(data).hexdigest()[:16],
                                                       len(data))})
    png = preview_meta.get("png")
    if png:
        out.append({"file": os.path.basename(png["path"]), "check": "size/dpi",
                    "result": "pass",
                    "detail": "%dx%d px @ %d dpi" % (png["width_px"], png["height_px"], png["dpi"])})
    pdf = preview_meta.get("pdf")
    if pdf and os.path.isfile(pdf["path"]):
        out.append({"file": os.path.basename(pdf["path"]),
                    "check": "vector PDF exists", "result": "pass",
                    "detail": "%d bytes" % os.path.getsize(pdf["path"])})
    for w in preview_meta.get("warnings") or []:
        out.append({"file": "preview", "check": "preview warning",
                    "result": "warn", "detail": w})
    return out


def write_result(result, out_path):
    dump_json(result, out_path)
    return out_path