# -*- coding: utf-8 -*-
"""Academic PPT builder — CLI orchestrator.

Pipeline (each step logs and can fail independently; partial results are
saved early and honestly reported in result.json `status`):

  1. read /input case.json + task.md and the *actual* material files,
  2. extract sections / tables / figure mentions and the research line,
  3. allocate page roles (页序 + 页级叙事角色) under spec.max_slides,
  4. bind figures: regenerate charts from data tables (matplotlib) or keep
     the native editable table / honest placeholder,
  5. build the editable deck.pptx (python-pptx, template slots, speaker
     notes, evidence footer per page),
  6. render PNG previews + PDF preview (PIL / reportlab, labeled as previews),
  7. write result.json (output_contract fields + case_id), evidence_map.md,
     changelog.jsonl and manifest.json,
  8. self-check (reopen pptx, contract keys, unverified claims).

Usage:
  python scripts/main.py --case <case.json> --out <outdir>
  python scripts/main.py --case <case.json> --out <outdir> --edit edits.json
  python scripts/main.py --case <case.json> --out <outdir> --max-slides 10 --template templates/default.json

Exit codes: 0 = success, 1 = partial, 2 = fatal input error.
"""
import argparse
import json
import os
import re
import sys
import shutil
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import (LOG, package_root, ensure_dir, now_iso, setup_logging,
                    atomic_write_json, sha256_file)
import material as material_mod
import planner as planner_mod
import result as result_mod

SKILL_VERSION = "1.0.0"


# ---------------------------------------------------------------------------
# Chart builder (injected into planner.bind_figures)
# ---------------------------------------------------------------------------

def make_chart_builder(no_chart=False):
    def builder(table, work_dir):
        if no_chart:
            raise RuntimeError("图表重绘被 --no-chart 关闭")
        from charting import build_chart
        png, note = build_chart(table, work_dir)
        return png, note
    return builder


def cache_tables(material, work_dir):
    """Copy source tables next to the deck for the native-table fallback."""
    cache_dir = ensure_dir(os.path.join(work_dir, "table_cache"))
    for t in material.tables:
        if t.source_file and os.path.isfile(t.source_file):
            dst = os.path.join(cache_dir, os.path.basename(t.source_file))
            if not os.path.exists(dst):
                shutil.copy2(t.source_file, dst)
    return cache_dir


# ---------------------------------------------------------------------------
# Self-check
# ---------------------------------------------------------------------------

def run_self_check(out_dir, case_id, pptx_path, expected_slides, contract_keys):
    """Lightweight checks that generate/verify artifacts exist & are openable."""
    checks = []
    ok = True
    try:
        from pptx import Presentation
        prs = Presentation(pptx_path)
        n = len(prs.slides._sldIdLst)
        checks.append({"name": "pptx_reopen", "ok": n == expected_slides,
                       "detail": "slides=%d expected=%d" % (n, expected_slides)})
        ok = ok and n == expected_slides
    except Exception as e:  # noqa: BLE001
        checks.append({"name": "pptx_reopen", "ok": False, "detail": str(e)})
        ok = False
    rj = os.path.join(out_dir, "result.json")
    have_result = os.path.isfile(rj)
    checks.append({"name": "result_json", "ok": have_result,
                   "detail": "exists" if have_result else "missing"})
    ok = ok and have_result
    if have_result:
        with open(rj, "r", encoding="utf-8") as f:
            data = json.load(f)
        missing = [k for k in contract_keys if k not in data]
        missing = [k for k in missing if not any(kk == k for kk in data)]
        checks.append({"name": "contract_keys", "ok": not missing,
                       "detail": ("missing=%s" % missing) if missing else "all present"})
        ok = ok and not missing
        unp = len(data.get("evidence", {}).get("unverified_claims", []))
        checks.append({"name": "unverified_claims", "ok": unp == 0,
                       "detail": "count=%d" % unp})
    ev = os.path.join(out_dir, "evidence_map.md")
    checks.append({"name": "evidence_map", "ok": os.path.isfile(ev), "detail": ""})
    ok = ok and os.path.isfile(ev)
    pv = os.path.join(out_dir, "preview")
    pngs = [f for f in os.listdir(pv) if f.endswith(".png")] if os.path.isdir(pv) else []
    checks.append({"name": "previews", "ok": len(pngs) > 0,
                   "detail": "png=%d pdf=%s" % (len(pngs), os.path.isfile(os.path.join(pv, "preview.pdf")))})
    ok = ok and len(pngs) > 0
    return {"all_pass": ok, "checks": checks}


# ---------------------------------------------------------------------------
# Edit operations (演示稿迭代：局部编辑、版本记录、可回退)
# ---------------------------------------------------------------------------

def apply_edits(plan_pages, edits, material_text, changelog, version):
    """Apply JSON edit ops to a plan; returns (pages, applied, skipped).
    Ops: update_bullet / add_bullet / remove_bullet / add_note / retitle /
           reorder_pages / set_figure
    """
    pages = planner_mod.plan_to_dict(plan_pages)  # work on plain dicts
    applied, skipped = [], []
    for op in edits.get("ops", []):
        kind = op.get("op")
        try:
            if kind == "retitle":
                p = _page(pages, op["page"])
                p["title"] = op["title"]
            elif kind == "update_bullet":
                p = _page(pages, op["page"])
                c = p["claims"][op["bullet_index"]]
                c["text"] = op["text"]
                if "evidence" in op:
                    c["evidence"] = op["evidence"]
                ok, missing = (True, [])
                from common import check_claim_numbers
                ok, missing = check_claim_numbers(op["text"], material_text)
                c["verified"] = ok
                c["missing_numbers"] = missing
            elif kind == "add_bullet":
                p = _page(pages, op["page"])
                c = {"text": op["text"], "evidence": op.get("evidence", []),
                     "level": op.get("level", 0), "verified": True,
                     "missing_numbers": []}
                from common import check_claim_numbers
                ok, missing = check_claim_numbers(op["text"], material_text)
                c["verified"] = ok
                c["missing_numbers"] = missing
                p["claims"].append(c)
            elif kind == "remove_bullet":
                p = _page(pages, op["page"])
                idx = op["bullet_index"]
                if 0 <= idx < len(p["claims"]):
                    del p["claims"][idx]
            elif kind == "add_note":
                p = _page(pages, op["page"])
                p["notes"].append(op["note"])
            elif kind == "reorder_pages":
                order = list(op["order"])
                if sorted(order) == list(range(1, len(pages) + 1)):
                    pages = [_page(pages, i) for i in order]
                    for i, p in enumerate(pages, start=1):
                        p["index"] = i
            elif kind == "set_figure":
                p = _page(pages, op["page"])
                p["figure"] = {"ref": op.get("ref", ""),
                               "kind": op.get("kind", "none"),
                               "table_id": op.get("table_id", ""),
                               "image": op.get("image", ""),
                               "note": op.get("note", "")}
            else:
                skipped.append({"op": kind, "reason": "未知操作"})
                continue
            applied.append(kind)
            changelog.append({"version": version, "op": kind, "page": op.get("page", ""),
                              "target": op.get("bullet_index", ""),
                              "reason": op.get("reason", "") or edits.get("reason", "")})
        except (KeyError, IndexError) as e:
            skipped.append({"op": kind, "reason": str(e)})
    return pages, applied, skipped


def _page(pages, index):
    for p in pages:
        if int(p["index"]) == int(index):
            return p
    raise KeyError("page %s not found" % index)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args(argv=None):
    ap = argparse.ArgumentParser(description="academic-ppt-builder skill")
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

    change_records = []
    uncertainty = []
    status = "failed"

    try:
        case, task_text, case_warn, case_abs, case_dir = material_mod.load_case(
            args.case, args.input_dir)
        # if the case file lives under /input (platform), materials resolve
        # against the case's own directory by default
        LOG.info("case_id=%s title=%s", case.get("case_id"), case.get("title"))
    except Exception as e:  # noqa: BLE001
        LOG.error("case load failed: %s", e)
        atomic_write_json(os.path.join(out_dir, "result.json"),
                          {"case_id": "unknown", "status": "failed",
                           "error": str(e), "created_at": now_iso()})
        return 2

    case_id = case.get("case_id") or "unknown"
    spec = dict(case.get("spec") or {})

    # ---- template spec -----------------------------------------------------
    try:
        if args.template:
            tpl_path = os.path.abspath(args.template)
        else:
            tpl_path = os.path.join(package_root(), "templates", "default.json")
        with open(tpl_path, "r", encoding="utf-8") as f:
            template_spec = json.load(f)
    except Exception as e:  # noqa: BLE001
        from deck_builder import DEFAULT_SPEC
        template_spec = DEFAULT_SPEC
        uncertainty.append("模板 spec 读取失败，使用内置默认: %s" % e)

    from deck_builder import merge_spec
    spec = merge_spec(template_spec, spec)
    if args.max_slides:
        spec["max_slides"] = args.max_slides
    spec.setdefault("max_slides", 8)
    spec["deck_title"] = case.get("title") or case_id
    if not spec.get("subtitle"):
        spec["subtitle"] = "受众=%s · 时长=%s 分钟 · ≤%s 页" % (
            spec.get("audience", "默认"),
            spec.get("duration_minutes", 15), spec.get("max_slides", 8))

    # ---- read actual material ----------------------------------------------
    try:
        inputs = case.get("inputs") or {}
        mat = material_mod.read_material(case_dir, inputs)
        mat.warnings.extend(case_warn)
    except Exception as e:  # noqa: BLE001
        LOG.error("material read failed: %s", e)
        uncertainty.append("材料读取失败: %s" % e)
        atomic_write_json(os.path.join(out_dir, "result.json"),
                          {"case_id": case_id, "status": "failed",
                           "error": str(e), "created_at": now_iso()})
        return 2

    work_dir = ensure_dir(os.path.join(out_dir, "work"))

    # resolve optional template_pptx / starting_deck relative to case dir
    for key in ("template_pptx", "starting_deck"):
        v = spec.get(key)
        if v and not os.path.isabs(v):
            cand = os.path.join(case_dir, v)
            spec[key] = cand if os.path.isfile(cand) else v

    # ---- plan ---------------------------------------------------------------
    try:
        pages = planner_mod.build_plan(mat, spec)
        chart_builder = make_chart_builder(no_chart=args.no_chart)
        cache_dir = cache_tables(mat, work_dir)
        pages, chart_log = planner_mod.bind_figures(
            pages, mat, work_dir, chart_builder=chart_builder)
        plan_file = planner_mod.dump_plan(pages, os.path.join(work_dir, "plan.json"))
        for entry in chart_log:
            LOG.info("figure: %s", entry)
    except Exception as e:  # noqa: BLE001
        LOG.error("plan failed: %s", e)
        uncertainty.append("页面规划失败: %s" % e)
        status = "failed"
        _write_partial(case, out_dir, status, uncertainty, change_records)
        return 1

    # ---- edits (incremental iteration) --------------------------------------
    if args.edit and os.path.isfile(args.edit):
        try:
            with open(args.edit, "r", encoding="utf-8") as f:
                edits = json.load(f)
            version = args.version or "v1"
            pages, applied, skipped = apply_edits(pages, edits, mat.text,
                                                  change_records, version)
            for a in applied:
                LOG.info("edit applied: %s", a)
            for s in skipped:
                uncertainty.append("编辑未应用: %s" % json.dumps(s, ensure_ascii=False))
            pages = [_dict_to_page_obj(p) for p in pages]
            planner_mod.dump_plan(pages, os.path.join(work_dir, "plan.json"))
        except Exception as e:  # noqa: BLE001
            uncertainty.append("编辑文件解析失败: %s" % e)

    # ---- build deck ----------------------------------------------------------
    chart_map = {}
    for p in pages:
        if p.figure.table_id:
            chart_map[p.figure.table_id] = p.figure.image or ""
    try:
        from deck_builder import build_deck, _evidence_text
        pptx_path, notes, receipt = build_deck(
            pages, None, spec, work_dir, table_cache_dir=cache_dir,
            template_pptx=spec.get("template_pptx"),
            starting_deck=spec.get("starting_deck"))
        change_records.extend([{"version": "deck-build", "note": n} for n in notes])
        LOG.info("deck built: %s (%d pages)", pptx_path, len(pages))
        # version archive: keep deck_<version>.pptx alongside the final deck.pptx
        if args.edit and os.path.isfile(args.edit):
            vname = re_sub_safe(args.version or "v2")
            vpath = os.path.join(work_dir, "deck_%s.pptx" % vname)
            shutil.copy2(pptx_path, vpath)
            LOG.info("version archive: %s", vpath)
    except Exception as e:  # noqa: BLE001
        LOG.error("deck build failed: %s", e)
        uncertainty.append("PPTX 生成失败: %s" % e)
        status = "partial"
        _write_partial(case, out_dir, status, uncertainty, change_records)
        return 1

    # ---- preview render ------------------------------------------------------
    pages_meta = planner_mod.plan_to_dict(pages)
    for pm in pages_meta:
        pm["evidence_footer"] = _evidence_text(_dict_to_page_obj(pm))
    preview_info = {"pngs": [], "pdf": None, "warnings": []}
    try:
        import render as render_mod
        pngs, pdf, warns = render_mod.render_all(pages_meta, work_dir,
                                                 chart_map=chart_map)
        preview_info = {"pngs": pngs, "pdf": pdf, "warnings": warns}
        uncertainty.extend("预览: %s" % w for w in warns)
    except Exception as e:  # noqa: BLE001
        LOG.error("preview failed: %s", e)
        uncertainty.append("预览渲染失败（不影响 pptx）: %s" % e)
        if args.draft:
            status = "partial"

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

    # ---- sources --------------------------------------------------------------
    sources = [{"role": "case", "path": case_abs,
                "sha256": sha256_file(case_abs)}]
    for sf in mat.source_files:
        sources.append({"role": sf["role"], "path": sf["path"],
                        "sha256": sha256_file(sf["path"])})

    # ---- self check ------------------------------------------------------------
    contract_keys = ["case_id", "status", "deck", "evidence", "previews",
                     "sources", "uncertainty", "change_records"]
    deck_info = {"editable": os.path.relpath(pptx_path, out_dir),
                 "slide_count": len(pages), "notes": True, "receipt": receipt}
    result = result_mod.build_result(
        case, mat, pages_meta, deck_info, preview_info, sources,
        uncertainty, change_records, "pending", log_path=os.path.relpath(log_path, out_dir),
        skill_version=SKILL_VERSION, out_dir=out_dir)
    result_mod.write_result(result, out_dir)
    result_mod.write_evidence_map(result, out_dir)
    result_mod.write_changelog(out_dir, change_records)

    checks = run_self_check(out_dir, case_id, pptx_path, len(pages), contract_keys)
    if not checks["all_pass"]:
        for c in checks["checks"]:
            if not c["ok"] and c["name"] not in ("unverified_claims",):
                uncertainty.append("自检未通过: %s (%s)" % (c["name"], c.get("detail", "")))

    status = "partial" if not checks["all_pass"] else "success"
    deck_info["checks"] = checks
    result = result_mod.build_result(
        case, mat, pages_meta, deck_info, preview_info, sources,
        uncertainty, change_records, status, log_path=os.path.relpath(log_path, out_dir),
        skill_version=SKILL_VERSION, out_dir=out_dir)
    result_mod.write_result(result, out_dir)
    result_mod.write_manifest(out_dir)

    LOG.info("STATUS=%s ok_checks=%d/%d checks_all_pass=%s",
             status,
             sum(1 for c in checks["checks"] if c["ok"]), len(checks["checks"]),
             checks["all_pass"])
    print("STATUS=%s case_id=%s deck=%s slides=%d" % (
        status, case_id, os.path.relpath(pptx_path, out_dir), len(pages)))
    return 0 if status == "success" else 1


def re_sub_safe(name):
    return re.sub(r"[^\w.-]+", "_", str(name))[:60]


def _dict_to_page_obj(p):
    """Rebuild a planner.Page from a plan dict (used after --edit)."""
    from planner import Claim, FigureSlot
    return type("P", (), dict(
        index=p["index"], role=p["role"], title=p["title"],
        claims=[Claim(text=c["text"], evidence=c["evidence"], level=c["level"],
                      verified=c["verified"],
                      missing_numbers=c["missing_numbers"]) for c in p["claims"]],
        figure=FigureSlot(ref=p["figure"]["ref"], kind=p["figure"]["kind"],
                          table_id=p["figure"]["table_id"],
                          image=p["figure"]["image"], note=p["figure"]["note"]),
        notes=p["notes"], agenda_item=p.get("agenda_item", "")))()


def _write_partial(case, out_dir, status, uncertainty, change_records):
    result_mod.atomic_write_json(os.path.join(out_dir, "result.json"), {
        "case_id": case.get("case_id", "unknown"), "status": status,
        "uncertainty": list(uncertainty), "change_records": list(change_records),
        "created_at": now_iso(),
    })


if __name__ == "__main__":
    sys.exit(main())