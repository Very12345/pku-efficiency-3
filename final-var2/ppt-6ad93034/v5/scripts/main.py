# -*- coding: utf-8 -*-
"""main.py — 编排层（build 轴）：学术 PPT 端到端流水线 + 检查点 CP1–CP4。

流程（每步独立 try/except，先存部分产物再增量改进，绝不假装成功）：
  CP1  CP1_extract  读 case/task/实际材料 → material_view.json（材料可读性）
  S1   规划          slide_text.build_plan（页序+页级叙事角色）+ CP2 plan_lint
  S2   构建          deck_tool：图表绑定 → 建 deck.pptx（模板槽位/备注/证据脚注）
  S3   渲染          render_qa：PIL PNG + reportlab PDF + 渲染 QA
  S4   汇总          result_tool：result.json（契约四形态回显）+ 证据映射双形态
                     + changelog + manifest
  CP4  CP4_verify    selftest 产物自检 + result_tool.validate（G1–G8 硬性门）
  --edit 模式        局部编辑（update_bullet 等）→ 版本归档 deck_<v>.pptx → 重跑

退出码：0 = success（各产物齐备、G 门通过）；1 = partial（有降级/未核验项，
已如实记录）；2 = 输入不可读（只写最小 failed result.json）。

平台形态：python main.py --case /input/case.json --out /app/output
本机形态：python scripts/main.py --case examples/case.json --out <outdir>
"""
import argparse
import json
import os
import re
import shutil
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from deck_common import (LOG, package_root, ensure_dir, now_iso, setup_logging,
                         atomic_write_json, sha256_file)
import deck_extract
import slide_text
import deck_tool
import render_qa
import result_tool
import selftest
import evidence_check

SKILL_VERSION = "2.0.0"

CONTRACT_KEYS = ["case_id", "status", "created_at", "deck", "evidence",
                 "previews", "sources", "uncertainty", "change_records"]


# ---------------------------------------------------------------------------
# Chart builder (injected into deck_tool.bind_figures)
# ---------------------------------------------------------------------------

def make_chart_builder(no_chart=False):
    def builder(table, work_dir):
        if no_chart:
            raise RuntimeError("图表重绘被 --no-chart 关闭")
        png, note = deck_tool.build_chart(table, work_dir)
        return png, note
    return builder


# ---------------------------------------------------------------------------
# CP2 plan lint wrapper (records problems into uncertainty per D4)
# ---------------------------------------------------------------------------

def run_plan_lint(pages_meta, spec):
    """CP2: structural lint of the plan; returns {valid, report}. Problems are
    recorded (D4) but do not by themselves stop the build."""
    report = evidence_check.plan_lint(pages_meta, spec)
    return report.get("valid", False), report


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args(argv=None):
    ap = argparse.ArgumentParser(description="academic-ppt-builder v2 skill")
    ap.add_argument("--case", required=True, help="case.json 路径（或相对路径）")
    ap.add_argument("--out", required=True, help="输出目录（/app/output 或本地目录）")
    ap.add_argument("--input-dir", default=None,
                    help="case.json 相对路径的基准目录（默认取 cwd）")
    ap.add_argument("--template", default=None,
                    help="模板 spec JSON 路径（默认 templates/default.json）")
    ap.add_argument("--max-slides", type=int, default=None,
                    help="覆盖 spec.max_slides")
    ap.add_argument("--edit", default=None, help="编辑操作 JSON 文件（局部编辑与版本记录）")
    ap.add_argument("--no-chart", action="store_true",
                    help="关闭 matplotlib 图表重绘（降级为原生可编辑表格）")
    ap.add_argument("--version", default="v1", help="版本标签（change records）")
    ap.add_argument("--draft", action="store_true", help="快速草稿模式（跳过 PDF 预览）")
    ap.add_argument("--verbose", action="store_true")
    return ap.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    out_dir = ensure_dir(os.path.abspath(args.out))
    log_path = os.path.join(out_dir, "logs", "run_%s.log" % now_iso().replace(":", "-"))
    setup_logging(log_path, verbose=args.verbose)
    LOG.info("case=%s out=%s", args.case, out_dir)

    change_records = [{"version": "run", "op": "start", "page": "",
                       "target": "", "reason": "v2 pipeline start"}]
    uncertainty = []
    status = "failed"
    checkpoints = {"cp1_extract": False, "cp2_plan": False,
                   "cp3_build": False, "cp4_verify": False}

    # ---- CP1: load case + task ---------------------------------------------
    try:
        case, task_text, case_warn, case_abs, case_dir = deck_extract.load_case(
            args.case, args.input_dir)
        LOG.info("case_id=%s title=%s", case.get("case_id"), case.get("title"))
    except Exception as e:  # noqa: BLE001
        LOG.error("case load failed: %s", e)
        atomic_write_json(os.path.join(out_dir, "result.json"),
                          {"case_id": "unknown", "status": "failed",
                           "error": str(e), "created_at": now_iso()})
        return 2

    case_id = case.get("case_id") or "unknown"
    spec = dict(case.get("spec") or {})

    # ---- template spec ------------------------------------------------------
    try:
        if args.template:
            tpl_path = os.path.abspath(args.template)
        else:
            tpl_path = os.path.join(package_root(), "templates", "default.json")
        with open(tpl_path, "r", encoding="utf-8") as f:
            template_spec = json.load(f)
    except Exception as e:  # noqa: BLE001
        template_spec = deck_tool.DEFAULT_SPEC
        uncertainty.append("模板 spec 读取失败，使用内置默认: %s" % e)

    spec = deck_tool.merge_spec(template_spec, spec)
    if args.max_slides:
        spec["max_slides"] = args.max_slides
    spec.setdefault("max_slides", 8)
    spec["deck_title"] = case.get("title") or case_id
    if not spec.get("subtitle"):
        spec["subtitle"] = "受众=%s · 时长=%s 分钟 · ≤%s 页" % (
            spec.get("audience", "默认"),
            spec.get("duration_minutes", 15), spec.get("max_slides", 8))

    # ---- read actual material (CP1) ----------------------------------------
    try:
        inputs = case.get("inputs") or {}
        mat = deck_extract.read_material(case_dir, inputs)
        mat.warnings.extend(case_warn)
        mat_status = deck_extract.material_status(mat)
        checkpoints["cp1_extract"] = mat_status in ("ok", "partial")
        if mat_status == "missing":
            uncertainty.append("材料不可读/为空，仅产出元信息 result（D1）")
        work_dir = ensure_dir(os.path.join(out_dir, "work"))
        view = deck_extract.dump_work(work_dir, case, task_text, mat)
        LOG.info("material_status=%s sections=%d tables=%d",
                 mat_status, len(mat.sections), len(mat.tables))
    except Exception as e:  # noqa: BLE001
        LOG.error("material read failed: %s", e)
        uncertainty.append("材料读取失败: %s" % e)
        atomic_write_json(os.path.join(out_dir, "result.json"),
                          {"case_id": case_id, "status": "failed",
                           "error": str(e), "created_at": now_iso()})
        return 2

    # resolve optional template_pptx / starting_deck relative to case dir
    for key in ("template_pptx", "starting_deck"):
        v = spec.get(key)
        if v and not os.path.isabs(v):
            cand = os.path.join(case_dir, v)
            spec[key] = cand if os.path.isfile(cand) else v

    plan_gate = {"valid": False, "problems": ["plan not built"]}
    pages = []
    if mat_status != "missing":
        # ---- S1: plan + CP2 lint ---------------------------------------------
        try:
            pages = slide_text.build_plan(mat, spec)
            cache_dir = deck_tool.cache_tables(mat, work_dir)
            chart_builder = make_chart_builder(no_chart=args.no_chart)
            pages, chart_log = deck_tool.bind_figures(
                pages, mat, work_dir, chart_builder=chart_builder)
            pages_meta = deck_tool.plan_to_dict(pages)
            plan_gate = evidence_check.plan_lint(pages_meta, spec)
            checkpoints["cp2_plan"] = True
            if not plan_gate["valid"]:
                uncertainty.append("CP2 plan lint 偏差已记录（D4）: %s"
                                   % "; ".join(plan_gate["problems"][:6]))
            deck_tool.dump_plan(pages, os.path.join(work_dir, "plan.json"))
            for entry in chart_log:
                LOG.info("figure: %s", entry)
        except Exception as e:  # noqa: BLE001
            LOG.error("plan failed: %s", e)
            uncertainty.append("页面规划失败: %s" % e)
            status = "failed"
            _write_partial(case, out_dir, status, uncertainty, change_records)
            return 1

        # ---- S1b: edits (incremental iteration, optional) ---------------------
        if args.edit and os.path.isfile(args.edit):
            try:
                with open(args.edit, "r", encoding="utf-8") as f:
                    edits = json.load(f)
                version = args.version or "v1"
                pages_dicts, applied, skipped = deck_tool.apply_edits(
                    pages, edits, mat.text, change_records, version)
                for a in applied:
                    LOG.info("edit applied: %s", a)
                for s in skipped:
                    uncertainty.append("编辑未应用: %s" % json.dumps(s, ensure_ascii=False))
                pages = deck_tool.pages_from_dict(pages_dicts)
                deck_tool.dump_plan(pages, os.path.join(work_dir, "plan.json"))
            except Exception as e:  # noqa: BLE001
                uncertainty.append("编辑文件解析失败: %s" % e)

        # ---- S2: build deck (CP3) ---------------------------------------------
        chart_map = {}
        for p in pages:
            if p.figure.table_id:
                chart_map[p.figure.table_id] = p.figure.image or ""
        try:
            pptx_path, notes, receipt = deck_tool.build_deck(
                pages, spec, work_dir, table_cache_dir=cache_dir,
                template_pptx=spec.get("template_pptx"),
                starting_deck=spec.get("starting_deck"))
            change_records.extend([{"version": "deck-build", "op": "build",
                                    "page": "", "target": "", "reason": n}
                                   for n in notes])
            LOG.info("deck built: %s (%d pages)", pptx_path, len(pages))
            if args.edit and os.path.isfile(args.edit):
                vname = _re_safe(args.version or "v2")
                vpath = os.path.join(work_dir, "deck_%s.pptx" % vname)
                shutil.copy2(pptx_path, vpath)
                LOG.info("version archive: %s", vpath)
            checkpoints["cp3_build"] = True
        except Exception as e:  # noqa: BLE001
            LOG.error("deck build failed: %s", e)
            uncertainty.append("PPTX 生成失败: %s" % e)
            _write_partial(case, out_dir, "partial", uncertainty, change_records)
            return 1

        # ---- S3: preview render ---------------------------------------------
        pages_meta = deck_tool.plan_to_dict(pages)
        for pm in pages_meta:
            pm["evidence_footer"] = evidence_check.build_evidence_footer(pm)
        preview_info = {"pngs": [], "pdf": None, "warnings": []}
        try:
            pngs, pdf, warns = render_qa.render_all(
                pages_meta, work_dir, chart_map=chart_map)
            preview_info = {"pngs": pngs, "pdf": pdf, "warnings": warns}
            uncertainty.extend("预览: %s" % w for w in warns)
        except Exception as e:  # noqa: BLE001
            LOG.error("preview failed: %s", e)
            uncertainty.append("预览渲染失败（不影响 pptx）: %s" % e)

        # copy previews next to outputs for convenient inspection
        if os.path.isdir(os.path.join(work_dir, "preview")):
            dst = ensure_dir(os.path.join(out_dir, "preview"))
            for name in os.listdir(os.path.join(work_dir, "preview")):
                shutil.copy2(os.path.join(work_dir, "preview", name),
                             os.path.join(dst, name))
            preview_info["pngs"] = [os.path.join(dst, n) for n in
                                    sorted(x for x in os.listdir(dst) if x.endswith(".png"))]
            pdf2 = os.path.join(dst, "preview.pdf")
            preview_info["pdf"] = pdf2 if os.path.isfile(pdf2) else None

        # ---- render QA --------------------------------------------------------
        qa = render_qa.qa_report(pages_meta, os.path.join(out_dir, "preview"))
        qa_warnings = [detail for c in qa["checks"] if not c["ok"]
                       for detail in [c["detail"]] if "missing" in detail or "no CJK" in detail]
        uncertainty.extend(qa.get("warnings", []))

        # ---- S4: sources ------------------------------------------------------
        sources = [{"role": "case", "path": case_abs,
                    "sha256": sha256_file(case_abs)}]
        for sf in mat.source_files:
            sources.append({"role": sf["role"], "path": sf["path"],
                            "sha256": sha256_file(sf["path"])})

        # ---- result.json + records -------------------------------------------
        deck_info = {"editable": os.path.relpath(pptx_path, out_dir),
                     "slide_count": len(pages), "notes": True, "receipt": receipt,
                     "evidence_map_json": "evidence_map.json", "manifest": "manifest.json"}
        # provisional result: status uses a VALID vocabulary value while CP4 runs;
        # the final result is rebuilt below with the true status + checks + gate.
        provisional = result_tool.build_result(
            case, mat, pages_meta, deck_info, preview_info, sources,
            uncertainty, change_records, "partial", log_path=os.path.relpath(log_path, out_dir),
            skill_version=SKILL_VERSION, out_dir=out_dir)
        provisional["run_meta"] = _run_meta(args, {
            "checkpoints": checkpoints,
            "spec_lint": plan_gate,
            "render_qa": {"checks": len(qa["checks"]), "warnings": len(qa["warnings"]),
                          "method": "PIL/reportlab 预览渲染，非 PowerPoint 导出"},
            "edit_mode": bool(args.edit and os.path.isfile(args.edit)),
            "status_line": "verify-in-progress",
        })
        result_tool.write_result(provisional, out_dir)   # CP4 selftest checks it on disk
        result_tool.write_evidence_map(provisional, out_dir)
        result_tool.write_evidence_map_json(provisional, out_dir)
        result_tool.write_changelog(out_dir, change_records)
        result_tool.write_manifest(out_dir)   # G7 needs manifest on disk before CP4

        # ---- CP4: verify (selftest + G1–G8) -----------------------------------
        checks = selftest.run_self_check(out_dir, case_id, pptx_path, len(pages), CONTRACT_KEYS)
        if not checks["all_pass"]:
            for c in checks["checks"]:
                if not c["ok"] and c["name"] not in ("unverified_claims",):
                    uncertainty.append("自检未通过: %s (%s)" % (c["name"], c.get("detail", "")))
        envelope_path = os.path.join(package_root(), "templates", "result_envelope.json")
        gate = result_tool.validate(provisional, out_dir, case, envelope_path)
        for w in gate["warnings"]:
            LOG.info("G-gate warning: %s", w)
        if not gate["valid"]:
            uncertainty.append("G 门未全过: %s" % "; ".join(gate["errors"][:6]))
        has_unverified = len(provisional.get("evidence", {}).get("unverified_claims", [])) > 0
        checkpoints["cp4_verify"] = (gate["valid"] and checks["all_pass"] and not has_unverified)

        status = ("partial" if (not checks["all_pass"] or not gate["valid"]
                                or has_unverified or not plan_gate["valid"])
                  else "success")
        deck_info["checks"] = checks
        result = result_tool.build_result(
            case, mat, pages_meta, deck_info, preview_info, sources,
            uncertainty, change_records, status, log_path=os.path.relpath(log_path, out_dir),
            skill_version=SKILL_VERSION, out_dir=out_dir)
        result["run_meta"] = _run_meta(args, {
            "checkpoints": checkpoints,
            "spec_lint": plan_gate,
            "render_qa": {"checks": len(qa["checks"]), "warnings": len(qa["warnings"]),
                          "method": "PIL/reportlab 预览渲染，非 PowerPoint 导出"},
            "edit_mode": bool(args.edit and os.path.isfile(args.edit)),
            "status_line": status,
            "gate": {"valid": gate["valid"], "errors": gate["errors"][:6],
                     "warnings": gate["warnings"][:6]},
        })
        result_tool.write_result(result, out_dir)
        result_tool.write_changelog(out_dir, [{
            "version": args.version or "run", "op": "finish", "page": "",
            "target": "", "reason": "status=%s cp4=%s" % (status, checkpoints["cp4_verify"])}])
        result_tool.write_manifest(out_dir)
    else:
        # D1: material missing — honest minimal result, no deck invented
        status = "partial"
        deck_info = {"editable": "", "slide_count": 0, "notes": False, "receipt": []}
        sources = [{"role": "case", "path": case_abs, "sha256": sha256_file(case_abs)}]
        preview_info = {"pngs": [], "pdf": None, "warnings": []}
        result = result_tool.build_result(
            case, mat, [], deck_info, preview_info, sources,
            uncertainty, change_records, status,
            log_path=os.path.relpath(log_path, out_dir), skill_version=SKILL_VERSION,
            out_dir=out_dir)
        result["material_status"] = "unreadable"
        result["run_meta"] = _run_meta(args, {"checkpoints": checkpoints,
                                              "note": "D1: 材料缺失，未编造 deck"})
        result_tool.write_result(result, out_dir)
        result_tool.write_changelog(out_dir, change_records)
        result_tool.write_manifest(out_dir)

    ok_checks = sum(1 for c in checks["checks"] if c["ok"]) if "checks" in locals() else 0
    n_checks = len(checks["checks"]) if "checks" in locals() else 0
    LOG.info("STATUS=%s ok_checks=%d/%d cp=%s", status, ok_checks, n_checks, checkpoints)
    print("STATUS=%s case_id=%s deck=%s slides=%d" % (
        status, case_id,
        result.get("deck", {}).get("editable", ""), len(result.get("deck", {}).get("slides", []))))
    return 0 if status == "success" else (1 if status == "partial" else 2)


def _re_safe(name):
    return re.sub(r"[^\w.-]+", "_", str(name))[:60]


def _run_meta(args, extra=None):
    import platform
    meta = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "skill_version": SKILL_VERSION,
        "timestamp": now_iso(),
        "cli_args": {"case": os.path.basename(args.case), "edit": bool(args.edit),
                     "no_chart": bool(args.no_chart), "max_slides": args.max_slides},
    }
    if extra:
        meta.update(extra)
    return meta


def _write_partial(case, out_dir, status, uncertainty, change_records):
    result_tool.atomic_write_json(os.path.join(out_dir, "result.json"), {
        "case_id": case.get("case_id", "unknown"), "status": status,
        "uncertainty": list(uncertainty), "change_records": list(change_records),
        "created_at": now_iso(),
    })


if __name__ == "__main__":
    sys.exit(main())