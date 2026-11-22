# -*- coding: utf-8 -*-
"""Entry point of the biological-mechanism-pathway-diagram skill (v2).

Pipeline mirrors SKILL.md checkpoints:
  CP1 preflight   : resolve & read case.json / task.md / materials (real files)
  CP2 spec gate   : build mechanism spec (draft extract or --model-file),
                    validate against assets/mechanism-spec.schema.json
  CP3 render+audit: deterministic layout -> editable SVG -> PNG/PDF preview
                    -> topology + legend/data-encoding audits -> gates G1..G8
  CP4 verdict     : honest status (success / partial / failed); auto-drafts
                    without agent verification can never be "success"

Usage (self-locating entry point; --case resolves against cwd first, then the
skill root; all outputs go under --out):
  export SKILL_DIR=/skills/weekly-skill          # 平台容器安装路径（本机改成包根目录）
  python3 "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output
  python3 "$SKILL_DIR/scripts/main.py" --case examples/case.json \
      --model-file "$SKILL_DIR/examples/model.example.json" --out /app/output
Exit code: 0 = success pipeline, 2 = partial, 3 = failed/hard error.
"""
import argparse
import hashlib
import json
import os
import sys
import time

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def portable_path(p, base=None):
    """Return a report/provenance-safe rendering of *p* (compliance fix).

    Shipped text resources must never contain a host absolute path, so paths
    recorded into result.json (provenance / change_records / check details)
    are rendered relative to the skill root when they live inside it,
    otherwise relative to the current working directory.  Container paths
    outside both roots (``/input/case.json``, ``/app/output`` on the
    platform) cannot be made relative and are reported unchanged.
    """
    if not p:
        return p
    ap = os.path.abspath(p)
    for root in (base or SKILL_ROOT, os.getcwd()):
        try:
            rel = os.path.relpath(ap, root)
        except ValueError:
            continue
        if rel != os.pardir and not rel.startswith(os.pardir + os.sep) \
                and not os.path.isabs(rel):
            return rel.replace(os.sep, "/")
    return ap

from model import normalize_model, load_json, dump_json, default_legend, SKILL_VERSION, CONTRACT_VERSION
import model as model_observability   # R2 纯增量：可观测性挂钩（判据见 references/FAULT-MATRIX.md §4）
from layout import compute_layout
from pathway_svg import render_svg
import topology as topology_mod
import legend_audit as legend_mod
import validate_figure as vf
import result_writer as rw

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
        # argparse 的 action="append" 传入 list；环境变量/直接调用可能传 str。
        # 两种形态都必须接受：collect_material_paths() 本来就按 list 迭代，
        # 而此处旧实现只按 str 处理，于是 --materials-dir 会以
        # TypeError: path should be string... not list 崩溃（本地实测 exit 1）。
        raw_items = materials_arg if isinstance(materials_arg, (list, tuple)) else [materials_arg]
        for item in raw_items:
            parts = (item.split(os.pathsep)
                     if isinstance(item, str) and os.pathsep in item else [item])
            for d in parts:
                if d:
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
                                                     "diagram.svg", "diagram.png",
                                                     "diagram.pdf", "topology.json",
                                                     "legend_audit.json"):
                    paths.append(ap)
                    refs.append(fp)
        elif os.path.isfile(base):
            paths.append(base)
            refs.append(os.path.basename(base))
    if not paths:
        for fp in sorted(os.listdir(case_dir)):
            if fp in ("case.json", "task.md", "result.json", "model.json",
                      "diagram.svg", "diagram.png", "diagram.pdf",
                      "topology.json", "legend_audit.json"):
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
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(
        description="biological-mechanism-pathway-diagram v2: editable pathway "
                    "figure from mechanism material (Skill entry)")
    ap.add_argument("--case", help="path to case.json (default: /input/case.json, "
                                   "then skill examples/case.json)")
    ap.add_argument("--task", help="path to task.md (default: /input/task.md)")
    ap.add_argument("--out", help="output directory (default: TASK_OUTPUT env, "
                                  "or <case_dir>/output)")
    ap.add_argument("--materials-dir", action="append", default=[],
                    help="directory of material files (repeatable)")
    ap.add_argument("--model-file", help="pre-built/agent-verified mechanism "
                                         "spec model.json (skips the bootstrap extractor)")
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

    schema_path = os.path.join(SKILL_ROOT, "assets", "mechanism-spec.schema.json")

    # ============ CP1: preflight ============
    change_records = [{"ts": _now(), "what": "CP1 读取输入",
                       "why": "case=%s, materials=%s, task文字长度=%d" %
                              (portable_path(case_path), ",".join(mat_refs) or "-", len(task_text)),
                       "by": "main.py"}]
    uncertainty = []
    cp1 = []
    cp1.append(vf._check("CP1.1", "case.json 已读取", "pass", portable_path(case_path)))
    cp1.append(vf._check("CP1.2", "task 说明可用",
                         "pass" if task_text or case_json.get("task") else "warn",
                         "%d chars" % len(task_text) if task_text else "无 task 文本（使用 case.task 或 case.json 其他字段）"))
    cp1.append(vf._check("CP1.3", "材料文件存在",
                         "pass" if mat_paths else "fail",
                         ("%d 个文件: %s" % (len(mat_paths), ", ".join(mat_refs))) if mat_paths
                         else "case.json 未给出 materials 且目录内无材料文件"))
    cp1.append(vf._check("CP1.4", "输出目录可写", "pass", portable_path(out_dir)))
    if any(c["result"] == "fail" for c in cp1):
        write_failed_result(case_json, out_dir, case_id,
                            "CP1 前置检查失败：材料缺失或输入不可读", cp1)
        print("SUMMARY %s" % json.dumps({"status": "failed", "case_id": case_id,
                                         "reason": "CP1 fail"}, ensure_ascii=False))
        return 3

    # --- R2 纯增量：CP1 的 warn 级降级必须留痕 -------------------------------
    # 原先成功路径只把 cp1 列表用于"是否 failed"判定，warn（如 task 文本缺失）
    # 会被丢掉，结果是"降级发生了但结果里看不出来"（失败注入演练 in-07 实测）。
    for _c in cp1:
        if _c.get("result") == "warn":
            uncertainty.append({
                "item": "CP1 前置检查降级：%s" % _c.get("check", _c.get("id", "")),
                "reason": _c.get("detail", ""),
                "mitigation": "补齐该输入后重跑；不补齐时本次结果按 warn 对待，"
                              "下游判定不得按 pass 处理"})

    # ============ CP2: mechanism spec (build) ============
    extraction_method = "manual"
    verified = True
    raw = None
    if args.model_file:
        raw = load_json(os.path.abspath(args.model_file))
        model = normalize_model(raw)
        extraction_method = (model.get("extraction") or {}).get("method", "manual")
        verified = bool((model.get("extraction") or {}).get("verified_by_agent"))
        change_records.append({"ts": _now(), "what": "CP2 使用 --model-file 机制规格",
                               "why": portable_path(args.model_file),
                               "by": "main.py"})
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
        raw = {
            "case_id": case_id,
            "title": title,
            "example": example,
            "entities": draft["entities"],
            "edges": draft["edges"],
            "legend": default_legend(),
            "extraction": {"method": draft.get("method", "manual-required"),
                           "verified_by_agent": False},
        }
        model_raw = raw
        for w in draft.get("warnings") or []:
            uncertainty.append({"item": "草稿提取提示", "reason": w,
                                "mitigation": "逐条核对材料并修正模型"})
        if draft.get("legend_overrides"):
            for k, v in draft["legend_overrides"].items():
                if v:
                    raw["legend"]["data_mapping"][k] = v
        model = normalize_model(raw)
        extraction_method = draft.get("method", "manual-required")
        verified = False
        change_records.append({"ts": _now(), "what": "CP2 草稿提取器生成初稿",
                               "why": "entities=%d, edges=%d, method=%s" %
                                      (len(model["entities"]), len(model["edges"]),
                                       extraction_method), "by": "extract.py"})
        if extraction_method == "manual-required" and not model["entities"]:
            write_failed_result(case_json, out_dir, case_id,
                                "材料中未找到可结构化解析的实体/关系，需要 Agent 手工建模型（--model-file）",
                                cp1)
            print("SUMMARY %s" % json.dumps({"status": "failed", "case_id": case_id,
                                             "reason": "manual-required"},
                                            ensure_ascii=False))
            return 3

    if not model["case_id"]:
        model["case_id"] = case_id
    if not model["title"]:
        model["title"] = title
    if example:
        model["example"] = True

    # --- R2 纯增量：把两处"静默"显式化（丢弃的边 / 调色板回退）---------------
    # normalize_edges() 仍照原样丢弃端点不存在的边，_load_palettes() 仍照原样回退
    # 内置默认色 —— 这里只是把**已经发生**的事写进 uncertainty（失败注入演练
    # in-08 / tpl-01 / tpl-05 实测：修复前 exit 0 + status=success + 零留痕）。
    for _d in model_observability.dropped_edges(raw):
        uncertainty.append({
            "item": "机制规格中有边被丢弃（未进入图面）",
            "reason": "第 %s 条边 %s→%s：%s" % (_d.get("index"), _d.get("from") or "?",
                                                _d.get("to") or "?", _d.get("reason")),
            "mitigation": "核对该边端点 id 与材料原文；修正规格后重跑，"
                          "不要让一条关系从图上静默消失"})
    _pal = model_observability.palette_load_status()
    if not _pal.get("loaded"):
        uncertainty.append({
            "item": "调色板资产未加载，已回退内置默认",
            "reason": _pal.get("detail", ""),
            "mitigation": "恢复 assets/palettes.json 后重跑；图面与图例语义不变（F07）"})

    # schema gate (CP2) — validated on the RAW spec before normalization so
    # unknown entity/edge types cannot be silently coerced away
    schema_check = vf.check_schema(raw, schema_path)
    if schema_check["result"] == "fail":
        write_failed_result(case_json, out_dir, case_id, "机制规格未通过 schema 门",
                            [schema_check])
        print("SUMMARY %s" % json.dumps({"status": "failed", "case_id": case_id,
                                         "reason": "schema gate fail"},
                                        ensure_ascii=False))
        return 3
    if schema_check["result"] == "warn":
        uncertainty.append({"item": "schema 门降级为 warn",
                            "reason": schema_check["detail"],
                            "mitigation": "确保 assets/mechanism-spec.schema.json 随包存在"})
    change_records.append({"ts": _now(), "what": "CP2 schema 门", "why": schema_check["detail"],
                           "by": "main.py"})

    # ============ CP3: layout, render, audits ============
    provenance = {"skill": "biological-mechanism-pathway-diagram",
                  "skill_version": SKILL_VERSION,
                  "contract": CONTRACT_VERSION,
                  "ts": _now(),
                  "command": " ".join([portable_path(sys.argv[0])] + list(sys.argv[1:])),
                  "material_refs": mat_refs,
                  "case_file": portable_path(case_path),
                  "schema": portable_path(schema_path) if os.path.isfile(schema_path) else None}
    layout = compute_layout(model)
    for w in layout["warnings"]:
        uncertainty.append({"item": "布局提示", "reason": w,
                            "mitigation": "核对区室拼写/实体归属"})

    fmt = {f.strip() for f in args.formats.split(",") if f.strip()}
    svg_p = os.path.join(out_dir, "diagram.svg")
    svg_text, svg_report = render_svg(model, layout, provenance, out_path=svg_p)

    preview_meta = {"png": None, "pdf": None, "warnings": []}
    if {"png", "pdf"} & fmt:
        try:
            from mpl_backend import render_preview
            got = render_preview(
                model, layout,
                png_path=os.path.join(out_dir, "diagram.png") if "png" in fmt else None,
                pdf_path=os.path.join(out_dir, "diagram.pdf") if "pdf" in fmt else None,
                dpi=args.dpi)
            preview_meta["png"] = got.get("png")
            preview_meta["pdf"] = got.get("pdf")
            preview_meta["warnings"] = list(got.get("warnings") or [])
        except Exception as ex:
            preview_meta["warnings"].append(
                "预览渲染失败（SVG 可编辑源仍有效）: %s: %s" % (type(ex).__name__, ex))
    else:
        preview_meta["warnings"].append(
            "本次未请求 PNG/PDF 预览（--formats %s）：只交付可编辑 SVG 源；"
            "需要预览时加 --formats svg,png,pdf 重跑" % ",".join(sorted(fmt)))
    for w in preview_meta["warnings"]:
        uncertainty.append({"item": "PNG/PDF 预览未生成或未请求",
                            "reason": w,
                            "mitigation": "已保留可编辑 SVG 源文件；安装 matplotlib 后以 "
                                          "--formats svg,png,pdf 重跑即可补齐预览"})

    model_p = os.path.join(out_dir, "model.json")
    dump_json(model, model_p)
    top_p = os.path.join(out_dir, "topology.json")
    leg_p = os.path.join(out_dir, "legend_audit.json")
    topology_checks = topology_mod.run_topology_checks(model, layout, out_path=top_p)
    legend_checks = legend_mod.run_legend_audit(model, layout, svg_path=svg_p,
                                                out_path=leg_p)
    out_files = {"svg": svg_p,
                 "png": preview_meta["png"]["path"] if preview_meta["png"] else None,
                 "pdf": preview_meta["pdf"]["path"] if preview_meta["pdf"] else None,
                 "result_json": os.path.join(out_dir, "result.json"),
                 "model_json": model_p,
                 "topology": top_p,
                 "legend_audit": leg_p}

    check_out = vf.run_checks(model, layout, out_files, schema_path=schema_path,
                              svg_path=svg_p)

    status = "success"
    if check_out["failures"]:
        status = "partial" if svg_report.get("well_formed") else "failed"
    if not verified:
        status = "partial" if status == "success" else status
        uncertainty.insert(0, {
            "item": "实体/关系由草稿提取器自动生成，尚未由 Agent 逐条复核（CP4 未过）",
            "reason": "auto-draft 未核验快照；正式运行必须人工核验后置 verified_by_agent=true",
            "mitigation": "对照材料逐条核对 entity/edge 后重跑，或在 result.json uncertainty 中说明"})

    # gates
    result = rw.build_result(model, layout, svg_report, preview_meta, check_out,
                             out_files, case_json, provenance, status,
                             uncertainty=uncertainty,
                             change_records=change_records,
                             layout_warnings=layout["warnings"],
                             topology_checks=topology_checks,
                             legend_checks=legend_checks,
                             gates={})
    if case_json.get("output_contract"):
        result = rw.apply_output_contract(result, case_json)
    # detect echo misses for gate g2
    oc = case_json.get("output_contract") or {}
    result["_echo_missing"] = [k for k in oc if k not in result] if isinstance(oc, dict) else []
    result["case_id"] = case_id
    result["gates"] = rw.evaluate_gates(result, out_files, check_out, svg_report)
    del result["_echo_missing"]
    rw.write_result(result, out_files["result_json"])

    # ============ CP3b: post-write result checks ============
    post = vf.run_result_checks(out_files["result_json"])
    check_out["checks"] = check_out["checks"] + post["checks"]
    check_out["failures"] = check_out["failures"] + post["failures"]
    check_out["warnings"] = check_out["warnings"] + post["warnings"]
    check_out["passed"] = not check_out["failures"]
    if status in ("success", "partial") and not check_out["passed"] and svg_report.get("well_formed"):
        status = "partial"
    result["status"] = status
    result["self_check"] = {
        "passed": bool(check_out["passed"]),
        "checks": check_out["checks"],
        "failures": check_out["failures"],
        "warnings": check_out["warnings"],
        "determinism": {"model_sha16": vf.sha16(model_p),
                        "svg_sha16": vf.sha16(svg_p),
                        "note": "同输入同布局：SVG/model 为输入+布局纯函数产物；result.json 含时间戳"},
    }
    rw.write_result(result, out_files["result_json"])

    # ============ CP4: verdict & summary ============
    produced = [p for p in (svg_p, out_files["png"], out_files["pdf"],
                            out_files["result_json"], model_p, top_p, leg_p)
                if p and os.path.isfile(p)]
    lines = []
    for p in produced:
        lines.append("%s  sha256=%s  %d bytes" %
                     (os.path.relpath(p, out_dir), _sha256(p)[:16], os.path.getsize(p)))
    print("[main] case_id=%s status=%s entities=%d edges=%d bands=%d verified=%s" %
          (case_id, status, len(model["entities"]), len(model["edges"]),
           len(layout["compartments"]), verified))
    for ln in lines:
        print("  produced  " + ln)
    gates_passed = sum(1 for g in (result.get("gates") or {}).values() if g.get("pass"))
    gates_total = len(result.get("gates") or {})
    print("SUMMARY " + json.dumps({
        "status": status, "case_id": case_id, "out_dir": out_dir,
        "files": [os.path.basename(p) for p in produced],
        "self_check_passed": check_out["passed"],
        "failures": len(check_out["failures"]),
        "warnings": len(check_out["warnings"]),
        "gates": "%d/%d" % (gates_passed, gates_total),
        "extraction": {"method": extraction_method, "verified_by_agent": verified},
    }, ensure_ascii=False))
    return 0 if status == "success" else (2 if status == "partial" else 3)


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def write_failed_result(case_json, out_dir, case_id, reason, pre_checks):
    result = {
        "case_id": case_id,
        "status": "failed",
        "contract_version": CONTRACT_VERSION,
        "reason": reason,
        "deliverables": {},
        "scientific_content": {"entities": [], "edges": [], "legend": {},
                               "layout": {}, "counts": {"entities": 0, "edges": 0,
                                                        "compartments": 0}},
        "evidence_sources": [],
        "uncertainty": [{
            "item": "无法启动绘图流程",
            "reason": "case=%s；%s" % (case_id, reason),
            "mitigation": "补齐材料后重跑，或由 Agent 阅读材料后以 --model-file 提供机制规格"}],
        "change_records": [], "self_check": {"passed": False, "checks": pre_checks or []},
        "topology": {"checks": []}, "legend_audit": {"checks": []}, "gates": {},
        "files": ["result.json"],
    }
    rw.write_result(result, os.path.join(out_dir, "result.json"))


if __name__ == "__main__":
    sys.exit(main())