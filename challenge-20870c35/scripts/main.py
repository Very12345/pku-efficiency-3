#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py — orchestrator of the academic-talk-organizer Skill.

True pipeline (all steps read/write real files, nothing is fabricated):

  case.json + task.md + materials
      -> load & parse materials (text/markdown; PDF via pypdf when present)
      -> extract claims with evidence anchors (line/section-level)
      -> page-level talk plan (audience/time-driven narrative order)
      -> editable .pptx (python-pptx; template adapt or built-in theme)
      -> PIL previews (cover / per-slide / grid) + manifest
      -> result.json (honest status/sources/uncertainty/change_records,
                      all output_contract fields applied)
      -> self_check.json (validate_result + check_contract reports)

Usage:
    python main.py --case <case.json> --out <output_dir> \
                   [--task task.md] [--materials dir] [--template deck.pptx] \
                   [--skip-previews] [--quiet]

The package never depends on the calling cwd: all internal paths derive from
this file's location, and all input/output paths are resolved from the
arguments (absolute or relative to the case file's directory).
"""

import argparse
import json
import os
import sys
import traceback

# Windows 控制台默认 GBK，UTF-8 输出易乱码；强制 UTF-8 输出不影响文件内容
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

from common import (SKILL_ROOT, TEMPLATES_DIR, utc_now, read_text, read_json,
                    write_json, ensure_dir, load_talk_config,
                    normalize_output_contract, parse_output_contract_from_task,
                    apply_contract, DEFAULT_CONTRACT_FIELDS)
import evidence as ev
import planner as pl
import deck_builder as db
import render as rnd
import validate_result as vr
import check_contract as cc

SUPPORTED_DOC_EXTS = {".md", ".markdown", ".txt", ".text", ".rst", ".rtf", ".pdf"}


def _setup_args():
    ap = argparse.ArgumentParser(description="academic-talk-organizer orchestrator")
    ap.add_argument("--case", required=True, help="path to case.json (or a directory containing case.json)")
    ap.add_argument("--out", required=True, help="output directory (final artifacts land here)")
    ap.add_argument("--task", default=None, help="path to task.md (default: <case_dir>/task.md)")
    ap.add_argument("--materials", default=None, help="materials directory (default: <case_dir>/materials)")
    ap.add_argument("--template", default=None, help="explicit template/start deck .pptx path")
    ap.add_argument("--skip-previews", action="store_true", help="skip per-slide PNG thumbnails (still renders cover+grid)")
    ap.add_argument("--quiet", action="store_true", help="less stdout")
    return ap.parse_args()


def _resolve_case_path(case_arg):
    if os.path.isdir(case_arg):
        cand = os.path.join(case_arg, "case.json")
        if os.path.exists(cand):
            return cand
        raise SystemExit("--case is a directory without case.json inside: %s" % case_arg)
    return case_arg


def _resolve_task_path(task_arg, case_dir):
    if task_arg:
        return task_arg if os.path.exists(task_arg) else None
    for cand in (os.path.join(case_dir, "task.md"),
                 os.path.join(os.path.sep, "input", "task.md")):
        if os.path.exists(cand):
            return cand
    return None


def _resolve_materials(case, case_dir, materials_arg):
    """Resolve the material file list into absolute paths.

    1) files explicitly listed in case.json (str or {path,role}),
    2) every supported document + image under --materials dir (auto-discovery),
    3) paths referenced but not found are reported honestly as missing.
    """
    listed = case.get("materials") or case.get("source_materials") \
        or case.get("material_files") or []
    if isinstance(listed, str):
        listed = [listed]
    resolved = []
    missing = []
    roles = {}
    base_dirs = [d for d in [materials_arg, case_dir] if d]
    for e in listed:
        if isinstance(e, dict):
            p = e.get("path") or e.get("file")
            role = str(e.get("role") or "")
        else:
            p, role = e, ""
        if not p:
            continue
        p = str(p)
        cands = []
        if os.path.isabs(p):
            cands.append(p)
        for bd in base_dirs:
            cands.append(os.path.join(bd, p))
            cands.append(os.path.join(bd, os.path.basename(p)))
        hit = None
        for c in cands:
            if os.path.exists(c):
                hit = os.path.normpath(c)
                break
        if hit:
            if hit not in [x[0] for x in resolved]:
                resolved.append((hit, role))
        else:
            missing.append((p, role))
    # auto-discover supported files in the materials directory
    if materials_arg and os.path.isdir(materials_arg):
        present = {os.path.normpath(x[0]) for x in resolved}
        for root, dirs, files in os.walk(materials_arg):
            dirs[:] = [d for d in dirs if not d.startswith((".", "_"))]
            for fn in sorted(files):
                full = os.path.normpath(os.path.join(root, fn))
                if full in present:
                    continue
                ext = os.path.splitext(fn)[1].lower()
                if ext in SUPPORTED_DOC_EXTS or ext in db.IMAGE_EXTS:
                    if full not in [x[0] for x in resolved]:
                        resolved.append((full, "auto-discovered"))
    return resolved, missing


def _resolve_template(case, case_dir, materials_arg, template_arg):
    """Determine the template/start deck .pptx (explicit arg > case.json field
    > materials dir scan).  Returns abs path or None."""
    explicit = template_arg
    if not explicit:
        explicit = case.get("template") or case.get("template_path") or case.get("start_deck")
    if explicit:
        cands = [explicit]
        if not os.path.isabs(explicit):
            for bd in (materials_arg, case_dir):
                if bd:
                    cands.append(os.path.join(bd, explicit))
                    cands.append(os.path.join(bd, os.path.basename(explicit)))
        for c in cands:
            if os.path.exists(c):
                return os.path.normpath(c)
        return None  # listed template missing -> built-in theme (recorded)
    if materials_arg and os.path.isdir(materials_arg):
        for root, dirs, files in os.walk(materials_arg):
            for fn in sorted(files):
                if fn.lower().endswith(".pptx"):
                    full = os.path.join(root, fn)
                    base = fn.lower()
                    if "template" in base or "master" in base or "start" in base or "deck" in base:
                        return os.path.normpath(full)
            # only top level to avoid picking up random files
            break
    return None


def main(argv=None):
    args = _setup_args()
    started = utc_now()
    change_records = [{"at": started, "step": "start",
                       "action": "academic-talk-organizer pipeline start (efficiency-3, challenge-20870c35)"}]

    # ---------- resolve paths ----------
    try:
        case_path = _resolve_case_path(args.case)
        case_dir = os.path.dirname(os.path.abspath(case_path))
        out_dir = os.path.abspath(args.out)
        materials_arg = args.materials
        if materials_arg and not os.path.isdir(materials_arg):
            auto = os.path.join(case_dir, materials_arg)
            if os.path.isdir(auto):
                materials_arg = auto
        ensure_dir(out_dir)
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        print("FATAL path setup:", exc)
        return 2

    # ---------- load case.json ----------
    try:
        case = read_json(case_path)
        change_records.append({"at": utc_now(), "step": "input",
                               "action": "loaded case.json: %s" % os.path.basename(case_path)})
    except Exception as exc:  # noqa: BLE001
        result = {"case_id": None, "status": "failed", "title": "",
                  "artifacts": {}, "sources": [], "uncertainty": [],
                  "error": "case.json unreadable: %s" % exc,
                  "change_records": change_records}
        write_json(os.path.join(out_dir, "result.json"), result)
        write_json(os.path.join(out_dir, "self_check.json"),
                   {"validate": {"valid": False, "errors": ["case.json unreadable"], "warnings": []},
                    "contract_check": {"valid": False, "error": str(exc)}})
        print("FATAL: case.json unreadable: %s" % exc)
        return 1

    case_id = case.get("case_id") or os.path.splitext(os.path.basename(case_path))[0]
    task_path = _resolve_task_path(args.task, case_dir)
    task_text = read_text(task_path) if task_path else ""
    if task_path:
        change_records.append({"at": utc_now(), "step": "input",
                               "action": "loaded task.md: %s" % task_path})

    # ---------- materials ----------
    materials_arg_final = args.materials
    if not materials_arg_final:
        fallback_md = os.path.join(case_dir, "materials")
        if os.path.isdir(fallback_md):
            materials_arg_final = fallback_md
    material_records = []
    resolved, missing = _resolve_materials(case, case_dir, materials_arg_final)
    # optional explicit figure map in case.json: {"Fig. 2": "figures/fig2.png", ...}
    fig_map = case.get("figure_files") or case.get("figures") or {}
    if isinstance(fig_map, dict):
        for _ref, rel in fig_map.items():
            cands = [rel]
            if not os.path.isabs(rel):
                for bd in (materials_arg_final, case_dir):
                    if bd:
                        cands.append(os.path.join(bd, rel))
            for c in cands:
                if c and os.path.exists(c):
                    if os.path.normpath(c) not in [x[0] for x in resolved]:
                        resolved.append((os.path.normpath(c), "figure-map"))
                    break
    for path, role in resolved:
        rec = ev.load_material(path)
        rec["role"] = role
        if rec["parsed"]:
            rec["claims"] = ev.extract_claims(rec)
        else:
            rec["claims"] = []
        material_records.append(rec)
        change_records.append({"at": utc_now(), "step": "material",
                               "action": "%s parsed=%s (%s)" % (rec["file"], rec["parsed"], rec["note"] or "ok")})
    for path, role in missing:
        material_records.append({"path": path, "file": os.path.basename(path), "kind": "missing",
                                 "parsed": False, "note": "listed in case.json but not found on disk (role=%s)" % role,
                                 "char_count": 0, "sections": [], "claims": [], "role": role})
        change_records.append({"at": utc_now(), "step": "material",
                               "action": "MISSING material %s not found on disk" % path})

    if not material_records:
        material_records.append({"path": "(none)", "file": "(none)", "kind": "none",
                                 "parsed": False, "note": "no materials found; deck carries structural pages only",
                                 "char_count": 0, "sections": [], "claims": [], "role": ""})
        change_records.append({"at": utc_now(), "step": "material",
                               "action": "no materials found on disk"})

    # ---------- plan ----------
    talk_config = load_talk_config()
    plan = pl.build_plan(case, material_records, talk_config, change_records)
    plan["title"] = str(case.get("title") or "(案例未提供标题)")
    talk_plan_path = os.path.join(out_dir, "talk_plan.json")
    write_json(talk_plan_path, plan)
    change_records.append({"at": utc_now(), "step": "plan", "action": "wrote talk_plan.json (%d pages)" % len(plan["pages"])})
    if not args.quiet:
        print("[plan] %d pages, narrative=%s, audience=%s" % (
            len(plan["pages"]), plan["narrative"]["report_type"],
            plan["audience"].get("expertise")))

    # ---------- evidence map ----------
    evidence_map = {}
    for p in plan["pages"]:
        for e in p.get("evidence") or []:
            src = e.get("source_file") or ""
            entry = evidence_map.setdefault(src, {"pages": [], "refs": []})
            if p["page_no"] not in entry["pages"]:
                entry["pages"].append(p["page_no"])
    for rec in material_records:
        entry = evidence_map.setdefault(rec["file"], {"pages": [], "refs": []})
        for r in rec["figure_refs"]:
            if r not in entry["refs"]:
                entry["refs"].append(r)
    evidence_map_path = os.path.join(out_dir, "evidence_map.json")
    write_json(evidence_map_path, evidence_map)

    # ---------- editable deck ----------
    template_path = _resolve_template(case, case_dir, materials_arg_final, args.template)
    deck_path = os.path.join(out_dir, "editable_deck.pptx")
    status = "completed"
    deck_ok = False
    deck_result = None
    try:
        deck_result, deck_changes = db.build_deck(plan, deck_path, template_path=template_path)
        change_records.extend(deck_changes)
        deck_ok = True
        if not args.quiet:
            print("[deck] %s slides, mode=%s" % (
                len(deck_result["manifest"]), deck_result["mode"]["mode"]))
    except Exception as exc:  # noqa: BLE001
        status = "failed"
        change_records.append({"at": utc_now(), "step": "deck",
                               "action": "deck build FAILED: %s" % exc})
        print("[deck] FAILED:", exc)
        traceback.print_exc()

    # ---------- previews (honest PIL simulation) ----------
    preview_ok = False
    preview_records, preview_limitation = [], ""
    try:
        preview_records, preview_limitation = rnd.render_all(
            plan, os.path.join(out_dir, "previews"),
            skip_slide_thumbs=args.skip_previews)
        preview_ok = True
        if not args.quiet:
            print("[preview] wrote %d preview files (PIL simulation)" % len(preview_records))
    except Exception as exc:  # noqa: BLE001
        change_records.append({"at": utc_now(), "step": "preview",
                               "action": "preview render FAILED (non-fatal): %s" % exc})
        print("[preview] FAILED (non-fatal):", exc)
    if args.skip_previews:
        change_records.append({"at": utc_now(), "step": "preview",
                               "action": "per-slide thumbnails skipped via --skip-previews"})

    # ---------- result.json ----------
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

    sources = []
    for rec in material_records:
        sources.append({
            "file": rec.get("file"), "path": rec.get("path"), "kind": rec.get("kind"),
            "parsed": rec.get("parsed", False), "note": rec.get("note", ""),
            "char_count": rec.get("char_count", 0),
            "sections": [{"heading": s.get("heading"), "start_line": s.get("start_line"),
                          "end_line": s.get("end_line")} for s in rec.get("sections", [])],
        })

    previews_art = {"cover": None, "grid": None, "manifest": None, "slide_pngs": []}
    for r_ in preview_records:
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
        "editable_deck": "editable_deck.pptx" if deck_ok else None,
        "talk_plan": "talk_plan.json",
        "evidence_map": "evidence_map.json",
        "previews": previews_art,
        "template_used": template_path,
        "deck_mode": deck_result["mode"] if deck_ok else None,
        "preview_note": preview_limitation,
    }

    uncertainty = []
    # binary figure attachments are intentionally unparsed; only document
    # materials (md/txt/pdf) that failed to parse downgrade the status
    image_kinds = {"png", "jpg", "jpeg", "gif", "bmp", "tif", "tiff", "webp"}
    unparsed = [r["file"] for r in material_records
                if not r["parsed"] and r["kind"] not in image_kinds and r["file"] != "(none)"]
    if unparsed:
        status = "partial"
        uncertainty.append({
            "item": "以下材料未能解析为文本：%s" % unparsed,
            "impact": "这些文件的主张未进入页级规划；相关结论若在其中有独立证据，本包未覆盖",
            "mitigation": "以已解析材料为事实依据；对覆盖不足明确标注而非补造"})
    if missing:
        uncertainty.append({
            "item": "case.json 声明但磁盘上不存在的材料：%s" % [m[0] for m in missing],
            "impact": "相关证据链路缺失",
            "mitigation": "在 sources 中如实标记 kind=missing"})
    framed = [c for c in change_records if c.get("step") == "framing"]
    if framed:
        uncertainty.append({
            "item": "若干页面由源材料章节间接概括而成（无逐句主张）",
            "impact": "这些页面证据强度为 weak，讲解时应回查原论文正文",
            "mitigation": "页面证据明确标注 strength=weak"})
    if not preview_ok:
        status = "partial"
        uncertainty.append({"item": "PNG 预览渲染失败或未执行", "impact": "无法图形化检查页布局",
                            "mitigation": "可打开 .pptx 人工检查"})
    if deck_result and not deck_ok:
        uncertainty.append({"item": "editable_deck.pptx 未生成", "impact": "核心交付缺失",
                            "mitigation": "见 change_records 中的异常记录"})
    uncertainty.append({
        "item": "证据定位为行级/章节级近似锚点（L<行号> · §<章节>）",
        "impact": "若源材料更新或行数变化，定位可能偏移",
        "mitigation": "同时给出引文原文与章节名，按引文复核"})
    uncertainty.append({
        "item": "PNG 预览为 Pillow 模拟渲染，非 Office 真实栅格化",
        "impact": "字体/间距与 PowerPoint 打开效果有差异",
        "mitigation": "以 editable_deck.pptx 在 PowerPoint/LibreOffice 打开为准"})
    if template_path is None:
        uncertainty.append({
            "item": "案例未提供模板或起始演示文件",
            "impact": "使用包内置主题母版，可能不完全符合组织方冻结模板（若题面另附模板，请经 --template 传入）",
            "mitigation": "本包支持模板适配模式，传入模板后自动改用它"})

    result = {
        "case_id": case_id,
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
        "main_line": main_line,
        "pages": plan["pages"],
        "evidence_map": evidence_map,
        "artifacts": artifacts,
        "sources": sources,
        "uncertainty": uncertainty,
        "contract": {"declared_source": "", "applied": []},
        "change_records": change_records,
        "generated_by": "main.py of academic-talk-organizer (efficiency-3)",
        "generated_at": utc_now(),
    }

    # ---------- output_contract ----------
    specs = []
    declared_note = []
    case_contract = case.get("output_contract")
    if case_contract is not None:
        cs = normalize_output_contract(case_contract)
        specs.extend(cs)
        declared_note.append("case.json")
    if task_text:
        ts, note = parse_output_contract_from_task(task_text)
        if ts:
            for s in ts:
                if s[0] not in [x[0] for x in specs]:
                    specs.append(s)
            declared_note.append("task.md")
    for name in DEFAULT_CONTRACT_FIELDS:
        if name not in [x[0] for x in specs]:
            specs.append((name, True, "any"))
    if not declared_note:
        declared_note.append("built-in default")
    result, initialized = apply_contract(result, specs)
    result["contract"] = {"declared_source": " + ".join(declared_note),
                          "applied": [s[0] for s in specs]}
    result_path = os.path.join(out_dir, "result.json")
    write_json(result_path, result)
    change_records.append({"at": utc_now(), "step": "result",
                           "action": "wrote result.json (status=%s; contract from %s; initialized %s)" % (
                               status, result["contract"]["declared_source"], initialized)})

    # ---------- self check ----------
    validate_report = vr.validate(result, out_dir, strict=False)
    contract_report = cc.check(result, specs, result["contract"]["declared_source"])
    self_check = {
        "validate": validate_report,
        "contract_check": contract_report,
        "contract_applied": [s[0] for s in specs],
        "generated_at": utc_now(),
    }
    write_json(os.path.join(out_dir, "self_check.json"), self_check)
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
        write_json(os.path.join(out_dir, "self_check.json"), self_check)

    if args.quiet:
        print("status=%s pages=%d deck=%s validate_valid=%s contract_valid=%s" % (
            result["status"], len(plan["pages"]), deck_ok,
            validate_report["valid"], contract_report["valid"]))
    else:
        print("[done] status=%s deck_ok=%s preview_ok=%s validate_valid=%s contract_valid=%s" % (
            result["status"], deck_ok, preview_ok,
            validate_report["valid"], contract_report["valid"]))
        print("[done] output: %s" % out_dir)
    return 0 if validate_report["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())