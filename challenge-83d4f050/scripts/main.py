# -*- coding: utf-8 -*-
"""Entry point of the biological-mechanism-pathway-diagram skill.

Pipeline (mirrors SKILL.md execution steps):
  1. resolve case.json (--case, else /input/case.json, else examples/case.json)
  2. resolve task.md and material files (read the REAL files, not labels)
  3. build the model:
       - --model-file <json>  -> use the agent-verified model as-is
       - otherwise run extract.py's bootstrap draft extractor on the material
       - apply legend defaults / data mapping
  4. compute the layered layout (scripts/layout.py)
  5. render the editable SVG (scripts/svg_backend.py) and the PNG/PDF
     previews via matplotlib (scripts/mpl_backend.py) if available
  6. verify (scripts/validate.py): ids, endpoints, sources, legend & color
     consistency, arrow semantics, direction rule, exports
  7. write result.json (scripts/result_writer.py) per references/OUTPUT_CONTRACT.md

Every produced file is listed with size + sha256 on stdout so the caller can
re-verify.  Status is honest: success / partial / failed.

Usage examples (paths are resolved relative to cwd first, skill root second):
  python scripts/main.py --case examples/case.json --out /app/output
  python scripts/main.py --model-file my_model.json --out /app/output
"""
import argparse
import hashlib
import json
import os
import sys
import time

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from model import normalize_model, load_json, dump_json, default_legend
from layout import compute_layout
from svg_backend import render_svg
import validate as validate_mod
import result_writer as rw

SKILL_VERSION = "1.0.0"
FORMATS = ("svg", "png", "pdf")


def _sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_paths(case_arg, out_arg, materials_arg, task_arg):
    root = SKILL_ROOT
    case_path = None
    if case_arg:
        p = os.path.abspath(case_arg)
        if not os.path.isfile(p) and os.path.isfile(os.path.join(root, case_arg)):
            p = os.path.join(root, case_arg)
        case_path = p if os.path.isfile(p) else case_arg
    elif os.path.isfile("/input/case.json"):
        case_path = "/input/case.json"
    elif os.path.isfile(os.path.join(root, "examples", "case.json")):
        case_path = os.path.join(root, "examples", "case.json")
    if not case_path or not os.path.isfile(case_path):
        raise SystemExit("未找到 case.json：请用 --case 指定，或提供 /input/case.json，"
                         "或使用技能内置示例 examples/case.json")

    out_dir = None
    if out_arg:
        out_dir = os.path.abspath(out_arg)
    elif os.getenv("TASK_OUTPUT"):
        out_dir = os.path.abspath(os.environ["TASK_OUTPUT"])
    else:
        out_dir = os.path.join(os.path.dirname(case_path), "output")
    os.makedirs(out_dir, exist_ok=True)

    materials = []
    if materials_arg:
        for d in (materials_arg.split(os.pathsep) if os.pathsep in materials_arg
                  else [materials_arg]):
            materials.append(os.path.abspath(d))

    task_path = None
    if task_arg:
        task_path = os.path.abspath(task_arg)
    elif os.path.isfile("/input/task.md"):
        task_path = "/input/task.md"
    return case_path, out_dir, materials, task_path


def collect_material_paths(case_json, case_path, materials_arg):
    """Materials = explicit list in case.json + --materials-dir + material
    files beside case.json (excluding output/).  Returns abs paths + refs."""
    case_dir = os.path.dirname(case_path)
    paths, refs = [], []
    for item in case_json.get("materials") or []:
        p = item if isinstance(item, str) else item.get("path", "")
        if not p:
            continue
        ap = os.path.abspath(p) if os.path.isabs(p) else os.path.join(case_dir, p)
        if os.path.isfile(ap):
            paths.append(ap)
            refs.append(p)
    for base in materials_arg:
        if os.path.isdir(base):
            for fp in sorted(os.listdir(base)):
                ap = os.path.join(base, fp)
                if os.path.isfile(ap) and fp not in ("result.json", "model.json",
                                                     "diagram.svg", "diagram.png", "diagram.pdf"):
                    paths.append(ap)
                    refs.append(fp)
        elif os.path.isfile(base):
            paths.append(base)
            refs.append(os.path.basename(base))
    # auto: text material beside case.json (not outputs)
    if not paths:
        for fp in sorted(os.listdir(case_dir)):
            if fp in ("case.json", "task.md", "result.json", "model.json",
                      "diagram.svg", "diagram.png", "diagram.pdf"):
                continue
            ap = os.path.join(case_dir, fp)
            if os.path.isfile(ap) and not fp.endswith((".png", ".jpg", ".jpeg",
                                                       ".gif", ".zip", ".xlsx",
                                                       ".ppt", ".pdf", ".svg")):
                paths.append(ap)
                refs.append(fp)
    return paths, refs


def read_task_text(task_path, case_json, case_dir):
    if task_path and os.path.isfile(task_path):
        with open(task_path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    if case_json.get("task"):
        return str(case_json["task"])
    tf = case_json.get("task_file")
    if tf and os.path.isfile(os.path.join(case_dir, tf)):
        with open(os.path.join(case_dir, tf), "r", encoding="utf-8") as fh:
            return fh.read()
    return ""


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="biological-mechanism-pathway-diagram: editable pathway "
                    "figure from mechanism material (Skill entry)")
    ap.add_argument("--case", help="path to case.json (default: /input/case.json, "
                                   "then skill examples/case.json)")
    ap.add_argument("--task", help="path to task.md (default: /input/task.md)")
    ap.add_argument("--out", help="output directory (default: TASK_OUTPUT env, "
                                  "or <case_dir>/output)")
    ap.add_argument("--materials-dir", action="append", default=[],
                    help="directory of material files (repeatable)")
    ap.add_argument("--model-file", help="pre-built/agent-verified model.json "
                                         "(skips the bootstrap extractor)")
    ap.add_argument("--formats", default=",".join(FORMATS),
                    help="output formats (comma list, default svg,png,pdf)")
    ap.add_argument("--dpi", type=int, default=150)
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args(argv)

    case_path, out_dir, materials_arg, task_path = resolve_paths(
        args.case, args.out, args.materials_dir, args.task)
    case_json = load_json(case_path)
    case_id = str(case_json.get("case_id") or
                  os.path.splitext(os.path.basename(case_path))[0])
    title = str(case_json.get("title") or case_json.get("task", "")[:80] or
                "生物机制图 / Pathway diagram")
    example = bool(case_json.get("example") or case_json.get("is_demo"))

    task_text = read_task_text(task_path, case_json, os.path.dirname(case_path))
    mat_paths, mat_refs = collect_material_paths(case_json, case_path, materials_arg)
    if args.verbose:
        print("[main] case=%s materials=%s task=%d chars" %
              (case_path, mat_refs, len(task_text)))

    # -------- model --------
    change_records = [{"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                       "what": "读取输入",
                       "why": "case=%s, materials=%s, task文字长度=%d" %
                              (case_path, ",".join(mat_refs) or "-", len(task_text)),
                       "by": "main.py"}]
    uncertainty = []
    extraction_method = "manual"
    verified = True
    if args.model_file:
        model = normalize_model(load_json(os.path.abspath(args.model_file)))
        extraction_method = (model.get("extraction") or {}).get("method", "manual")
        verified = bool((model.get("extraction") or {}).get("verified_by_agent"))
        change_records.append({"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                               "what": "使用 --model-file 模型",
                               "why": os.path.abspath(args.model_file), "by": "main.py"})
        if not verified:
            uncertainty.append({"item": "模型未经人工核验",
                                "reason": "model-file 未标记 verified_by_agent=true",
                                "mitigation": "对每个实体/边逐条对照材料后重跑校验"})
    else:
        from extract import draft_model as bootstrap_draft
        draft = bootstrap_draft(mat_paths) if mat_paths else {"entities": [],
                                                              "edges": [],
                                                              "warnings": [],
                                                              "method": "manual-required"}
        model_raw = {
            "case_id": case_id,
            "title": title,
            "example": example,
            "entities": draft["entities"],
            "edges": draft["edges"],
            "legend": default_legend(),
            "extraction": {"method": draft.get("method", "manual-required"),
                           "verified_by_agent": False},
        }
        for w in draft.get("warnings") or []:
            uncertainty.append({"item": "草稿提取提示", "reason": w,
                                "mitigation": "逐条核对材料并修正模型"})
        if draft.get("legend_overrides"):
            for k, v in draft["legend_overrides"].items():
                if v:
                    model_raw["legend"]["data_mapping"][k] = v
        model = normalize_model(model_raw)
        extraction_method = draft.get("method", "manual-required")
        verified = False
        change_records.append({"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                               "what": "草稿提取器生成初稿",
                               "why": "entities=%d, edges=%d, method=%s" %
                                      (len(model["entities"]), len(model["edges"]),
                                       extraction_method), "by": "extract.py"})
        if extraction_method == "manual-required" and not model["entities"]:
            # nothing to draw; report honestly
            write_failed_result(case_json, model, out_dir, case_id,
                                task_available=bool(task_text), mat_available=bool(mat_paths))
            print(SUMMARY % {"status": "failed", "case": case_id,
                             "files": "result.json", "why":
                             "材料中未找到可结构化解析的实体/关系，需要 Agent 手工建模型"})
            return 1

    if not model["case_id"]:
        model["case_id"] = case_id
    if not model["title"]:
        model["title"] = title
    if example:
        model["example"] = True

    # -------- layout & render --------
    provenance = {"skill": "biological-mechanism-pathway-diagram",
                  "skill_version": SKILL_VERSION,
                  "contract": "1.0",
                  "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                  "command": " ".join(sys.argv),
                  "material_refs": mat_refs,
                  "case_file": case_path}
    layout = compute_layout(model)
    for w in layout["warnings"]:
        uncertainty.append({"item": "布局提示", "reason": w,
                            "mitigation": "核对区室拼写/实体归属"})

    fmt = {f.strip() for f in args.formats.split(",") if f.strip()}
    svg_p = os.path.join(out_dir, "diagram.svg")
    svg_text, svg_report = render_svg(model, layout, provenance, out_path=svg_p)

    preview_meta = {"png": None, "pdf": None, "warnings": []}
    try:
        from mpl_backend import render_preview
        preview_meta = render_preview(
            model, layout,
            png_path=os.path.join(out_dir, "diagram.png") if "png" in fmt else None,
            pdf_path=os.path.join(out_dir, "diagram.pdf") if "pdf" in fmt else None,
            dpi=args.dpi)
    except Exception as ex:
        preview_meta["warnings"].append(
            "预览渲染失败（SVG 可编辑源仍有效）: %s: %s" % (type(ex).__name__, ex))
        uncertainty.append({"item": "PNG/PDF 预览未生成",
                            "reason": "matplotlib 不可用或渲染异常: %s" % ex,
                            "mitigation": "已保留可编辑 SVG 源文件；安装 matplotlib 后重跑 --formats png,pdf"})

    # model.json snapshot for independent verification of entity/edge lists
    model_p = os.path.join(out_dir, "model.json")
    dump_json(model, model_p)

    out_files = {"svg": svg_p, "png": preview_meta["png"]["path"] if preview_meta["png"] else None,
                 "pdf": preview_meta["pdf"]["path"] if preview_meta["pdf"] else None,
                 "result_json": os.path.join(out_dir, "result.json"),
                 "model_json": model_p}

    # -------- verify --------
    check_out = validate_mod.run_checks(model, layout, out_files)
    # -------- result.json (first write) --------
    status = "success"
    if check_out["failures"]:
        status = "partial" if svg_report.get("well_formed") else "failed"
    if not verified and extraction_method == "auto-draft":
        uncertainty.insert(0, {
            "item": "实体/关系由草稿提取器自动生成，尚未由 Agent 逐条复核",
            "reason": "auto-draft 模式快照（本机演示/冒烟运行）；正式运行必须人工核验后置 verified_by_agent=true",
            "mitigation": "对照材料逐条核对 entity/edge 后重跑，或将产物标记为 partial"})

    result = rw.build_result(model, layout, svg_report, preview_meta, check_out,
                             out_files, case_json, provenance, status,
                             uncertainty=uncertainty,
                             change_records=change_records,
                             layout_warnings=layout["warnings"])
    if case_json.get("output_contract"):
        result = rw.apply_output_contract(result, case_json)
    result["case_id"] = case_id
    rw.write_result(result, out_files["result_json"])

    # -------- post-write checks (result.json itself) & final write --------
    post = validate_mod.run_result_checks(out_files["result_json"])
    check_out["checks"] = check_out["checks"] + post["checks"]
    check_out["failures"] = check_out["failures"] + post["failures"]
    check_out["warnings"] = check_out["warnings"] + post["warnings"]
    check_out["passed"] = not check_out["failures"]
    if status == "success" and not check_out["passed"]:
        status = "partial"
    result["status"] = status
    result["self_check"] = {
        "passed": bool(check_out["passed"]),
        "checks": check_out["checks"],
        "failures": check_out["failures"],
        "warnings": check_out["warnings"],
    }
    rw.write_result(result, out_files["result_json"])

    # -------- summary --------
    produced = [p for p in (svg_p, out_files["png"], out_files["pdf"],
                            out_files["result_json"], model_p) if p and os.path.isfile(p)]
    lines = []
    for p in produced:
        lines.append("%s  sha256=%s  %d bytes" %
                     (os.path.relpath(p, out_dir), _sha256(p)[:16], os.path.getsize(p)))
    print("[main] case_id=%s status=%s entities=%d edges=%d bands=%d" %
          (case_id, status, len(model["entities"]), len(model["edges"]),
           len(layout["compartments"])))
    for ln in lines:
        print("  produced  " + ln)
    print("SUMMARY " + json.dumps({
        "status": status, "case_id": case_id, "out_dir": out_dir,
        "files": [os.path.basename(p) for p in produced],
        "self_check_passed": check_out["passed"],
        "failures": len(check_out["failures"]),
        "warnings": len(check_out["warnings"]),
        "extraction": {"method": extraction_method, "verified_by_agent": verified},
    }, ensure_ascii=False))
    return 0 if status == "success" else (2 if status == "partial" else 3)


SUMMARY = "%(status)s|%(case)s|%(files)s|%(why)s"


def write_failed_result(case_json, model, out_dir, case_id, task_available, mat_available):
    result = {
        "case_id": case_id,
        "status": "failed",
        "contract_version": "1.0",
        "reason": "材料中未找到可解析的实体/关系",
        "deliverables": {},
        "scientific_content": {"entities": [], "edges": [], "legend": {},
                               "layout": {}},
        "evidence_sources": [],
        "uncertainty": [{
            "item": "无法启动绘图流程",
            "reason": "case=%s task_available=%s material_available=%s；"
                      "材料必须是可读文本或提供 --model-file" %
                      (case_id, task_available, mat_available),
            "mitigation": "把材料整理成文本再重跑，或由 Agent 阅读材料后以 --model-file 提供模型"}],
        "change_records": [], "self_check": {"passed": False, "checks": []},
        "files": ["result.json"],
    }
    rw.write_result(result, os.path.join(out_dir, "result.json"))


if __name__ == "__main__":
    sys.exit(main())