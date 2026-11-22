#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py — orchestrator of the academic-talk-organizer Skill (v2).

True pipeline (all steps read/write real files, nothing is fabricated):

  case.json + task.md + materials
      [CP1] load & parse materials + collect output_contract
      [CP2] scaffold plan (scaffold_plan.build_plan) -> write talk_plan.json
            -> validate against assets/plan.schema.json (gates P1–P8)
            -> write plan_gates.json
      [CP3] editable .pptx (deck_builder.build_deck; template adapt or
            built-in theme) -> verify_deck opens/count/notes/naming
            -> write deck_audit.json
      [CP4] PIL previews (render.render_all: cover / per-slide / grid)
            -> previews/preview_manifest.json
      [CP5] evidence audit (verbatim quote vs actually-read text)
            -> evidence_audit.json
            -> finalize_result: result.json (all output_contract fields,
               audits embedded, honest status/sources/uncertainty/
               change_records) + self_check.json (validate + contract +
               determinism probe)

Usage:
    python main.py --case <case.json> --out <output_dir> \
                   [--task task.md] [--materials dir] [--template deck.pptx] \
                   [--skip-previews] [--quiet]

Exit code 0 = a contract-valid result.json was produced and passes the built-in
validate + contract checks (its `status` field says `completed` or `partial` —
the honest status travels *inside* result.json, so an honest partial run is not
reported as a crash); 1 = no contract-valid result could be produced (case.json
unreadable, self-check errors, unexpected deck crash).  Exit code 2 is argparse
usage error.

Degradation rules (never a silent failure):
  * python-pptx missing  -> deck skipped, status=partial, reason recorded in
    uncertainty/change_records; talk_plan/plan_gates/previews/result.json are
    still produced;
  * Pillow missing       -> previews skipped (non-fatal, status=partial);
  * pypdf missing        -> PDF materials recorded as unparsed.

The package never depends on the calling cwd: all internal paths derive from
this file's location, and all input/output paths are resolved from the
arguments (absolute or relative to the case file's directory).  Nothing
written by this orchestrator carries this machine's absolute paths — see
common.write_json / common.sanitize_output.
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
                    write_json, ensure_dir, load_talk_config, set_path_bases,
                    resolve_input_path, portable_path,
                    normalize_output_contract, parse_output_contract_from_task,
                    apply_contract, DEFAULT_CONTRACT_FIELDS)
import evidence as ev
import scaffold_plan as sp
import validate_plan as vp
import evidence_audit as ea
import deck_builder as db
import verify_deck as vdeck
import render as rnd
import finalize_result as fr

SUPPORTED_DOC_EXTS = {".md", ".markdown", ".txt", ".text", ".rst", ".rtf", ".pdf"}


def _setup_args():
    ap = argparse.ArgumentParser(description="academic-talk-organizer orchestrator (v2)")
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
            break
    return None


def main(argv=None):
    args = _setup_args()
    started = utc_now()
    change_records = [{"at": started, "step": "start",
                       "action": "academic-talk-organizer v2 pipeline start (efficiency-3, challenge-20870c35)"}]

    # ============ CP1 · 输入契约：路径、case.json、task.md、材料、模板 ============
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
        # every local absolute path written from now on becomes relative to the
        # case directory (no machine-specific path may travel inside the pack)
        set_path_bases(case_dir)
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        print("FATAL path setup:", exc)
        return 2

    # ============ 环境预检（决定本次运行能生成哪些产物，如实记录） ============
    deps = db.dependency_status()
    font_info = rnd.font_status()
    env_info = {
        "python": sys.version.split()[0],
        "platform": sys.platform,
        "python_pptx": deps.get("python_pptx"),
        "pillow": deps.get("pillow"),
        "pypdf": deps.get("pypdf"),
        "cjk_font": font_info,
    }
    change_records.append({
        "at": utc_now(), "step": "environment",
        "action": "deps python-pptx=%s pillow=%s pypdf=%s; cjk_font=%s" % (
            deps.get("python_pptx") or "MISSING", deps.get("pillow") or "MISSING",
            deps.get("pypdf") or "MISSING",
            font_info.get("file") or "built-in bitmap fallback")})
    if not deps.get("python_pptx"):
        change_records.append({
            "at": utc_now(), "step": "environment",
            "action": "python-pptx 不可用(%s)：本次运行将跳过可编辑 .pptx，"
                      "其余产物照常产出并降级为 partial" % (deps.get("pptx_import_error") or "")})
    if not deps.get("pillow"):
        change_records.append({"at": utc_now(), "step": "environment",
                               "action": "Pillow 不可用：PNG 预览将跳过（非致命）"})
    if not deps.get("pypdf"):
        change_records.append({"at": utc_now(), "step": "environment",
                               "action": "pypdf/PyPDF2 不可用：PDF 材料将按未解析如实记录"})

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
                               "action": "loaded task.md: %s" % os.path.basename(task_path)})

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
                                 "char_count": 0, "sections": [], "claims": [],
                                 "figure_refs": [], "text": "", "role": role})
        change_records.append({"at": utc_now(), "step": "material",
                               "action": "MISSING material %s not found on disk" % path})

    if not material_records:
        material_records.append({"path": "(none)", "file": "(none)", "kind": "none",
                                 "parsed": False, "note": "no materials found; deck carries structural pages only",
                                 "char_count": 0, "sections": [], "claims": [],
                                 "figure_refs": [], "text": "", "role": ""})
        change_records.append({"at": utc_now(), "step": "material",
                               "action": "no materials found on disk"})

    # ============ CP2 · 计划门：scaffold -> validate (P1–P8) ============
    talk_config = load_talk_config()
    plan = sp.build_plan(case, material_records, talk_config, change_records)
    plan["title"] = str(case.get("title") or "(案例未提供标题)")
    talk_plan_path = os.path.join(out_dir, "talk_plan.json")
    write_json(talk_plan_path, plan)
    change_records.append({"at": utc_now(), "step": "plan", "action": "wrote talk_plan.json (%d pages)" % len(plan["pages"])})

    material_names = [r.get("file") for r in material_records]
    plan_gates = vp.validate_plan(plan, material_names=material_names)
    write_json(os.path.join(out_dir, "plan_gates.json"), plan_gates)
    change_records.append({"at": utc_now(), "step": "plan",
                           "action": "plan gates: valid=%s errors=%d" % (
                               plan_gates["valid"], len(plan_gates.get("errors", [])))})
    if not plan_gates["valid"]:
        for err in plan_gates.get("errors", [])[:8]:
            change_records.append({"at": utc_now(), "step": "plan-gate",
                                   "action": "P-gate violation: %s" % err})
    if not args.quiet:
        print("[plan] %d pages, narrative=%s, audience=%s, P-gates valid=%s" % (
            len(plan["pages"]), plan["narrative"]["report_type"],
            plan["audience"].get("expertise"), plan_gates["valid"]))

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

    # ============ CP3 · 生成门：deck -> verify_deck ============
    template_path = _resolve_template(case, case_dir, materials_arg_final, args.template)
    deck_path = os.path.join(out_dir, "editable_deck.pptx")
    status = "completed"
    deck_ok = False
    deck_result = None
    deck_audit = None
    deck_normalized_sha = None
    deck_failure = None
    if not deps.get("python_pptx"):
        # dependency missing -> honest degradation, everything else still runs
        status = "partial"
        deck_failure = ("python-pptx 不可用（%s）" % (deps.get("pptx_import_error") or "import failed"))
        change_records.append({"at": utc_now(), "step": "deck",
                               "action": "deck SKIPPED: %s" % deck_failure})
        print("[deck] SKIPPED (dependency missing):", deck_failure)
    else:
        try:
            deck_result, deck_changes = db.build_deck(plan, deck_path,
                                                      template_path=template_path,
                                                      figure_base=case_dir)
            change_records.extend(deck_changes)
            deck_ok = True
            deck_audit = vdeck.verify_deck(deck_path, expect_pages=len(plan["pages"]), plan=plan)
            write_json(os.path.join(out_dir, "deck_audit.json"), deck_audit)
            deck_normalized_sha = deck_audit.get("normalized_sha256")
            change_records.append({"at": utc_now(), "step": "deck",
                                   "action": "deck built (%s), verify valid=%s, normalized_sha=%s" % (
                                       deck_result["mode"]["mode"], deck_audit["valid"],
                                       (deck_normalized_sha or "")[:16])})
            if not deck_audit["valid"]:
                status = "partial"
                change_records.append({"at": utc_now(), "step": "deck-gate",
                                       "action": "verify_deck 发现 %d 处问题: %s" % (
                                           len(deck_audit.get("errors", [])),
                                           deck_audit.get("errors", [])[:3])})
            if not args.quiet:
                print("[deck] %s slides, mode=%s, verify valid=%s" % (
                    len(deck_result["manifest"]), deck_result["mode"]["mode"], deck_audit["valid"]))
        except Exception as exc:  # noqa: BLE001
            status = "failed"
            deck_failure = str(exc)
            change_records.append({"at": utc_now(), "step": "deck",
                                   "action": "deck build FAILED: %s" % exc})
            print("[deck] FAILED:", exc)
            traceback.print_exc()

    # ============ CP4 · 渲染门：PIL 预览 ============
    preview_ok = False
    preview_records, preview_limitation = [], ""
    try:
        preview_records, preview_limitation = rnd.render_all(
            plan, os.path.join(out_dir, "previews"),
            skip_slide_thumbs=args.skip_previews, figure_base=case_dir)
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

    # ============ CP5 · 证据审计 + 收口 ============
    uncertainty = []
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
            "mitigation": "页面证据明确标注 strength=weak 且 derived=true"})
    if not any(r.get("parsed") for r in material_records):
        status = "partial"
        uncertainty.append({
            "item": "没有任何材料被解析为文本（材料为空，或全部不可解析/不存在）",
            "impact": "交付的 deck 只包含结构性页面，没有可溯源的证据页",
            "mitigation": "核对 case.json 的 materials 字段与实际材料目录；"
                          "本包不据标签补造材料内容，因此如实降级为 partial"})
    if not preview_ok:
        status = "partial"
        uncertainty.append({"item": "PNG 预览渲染失败或未执行", "impact": "无法图形化检查页布局",
                            "mitigation": "可打开 .pptx 人工检查"})
    if deck_result and not deck_ok:
        uncertainty.append({"item": "editable_deck.pptx 未生成", "impact": "核心交付缺失",
                            "mitigation": "见 change_records 中的异常记录"})
    if deck_failure and not deck_ok:
        if not deps.get("python_pptx"):
            uncertainty.append({
                "item": "运行环境缺少 python-pptx（%s）：本次未生成可编辑 .pptx" % deck_failure,
                "impact": "核心可编辑交付缺失；页计划、计划门、预览与 result.json 仍然完整产出",
                "mitigation": "在目标环境执行 pip install python-pptx 后重跑同一条命令即可补齐；"
                              "本包不预置任何 .pptx 二进制（题面只允许 UTF-8 文本资源）"})
        else:
            uncertainty.append({
                "item": "可编辑演示文件生成抛错：%s" % deck_failure,
                "impact": "deck 缺失，其余产物已落盘",
                "mitigation": "见 change_records 的 deck 记录；修因后重跑（status=failed 为如实降级）"})
    if plan_gates and not plan_gates["valid"]:
        status = "partial"
        uncertainty.append({
            "item": "计划门 P1–P8 未全过（见 plan_gates.json / result.audit.plan_gates）",
            "impact": "页计划存在结构性偏差，已如实降级为 partial",
            "mitigation": "按 plan_gates.json 的 errors 修复（多为冻结页数/材料声明问题）后重跑"})
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

    # evidence audit against the text actually read
    evidence_audit = ea.audit_evidence(plan["pages"], material_records=material_records)
    write_json(os.path.join(out_dir, "evidence_audit.json"), evidence_audit)
    change_records.append({"at": utc_now(), "step": "audit",
                           "action": "evidence audit: valid=%s errors=%d derived=%d" % (
                               evidence_audit["valid"],
                               evidence_audit["summary"].get("errors"),
                               evidence_audit["summary"].get("derived_pages"))})
    if not evidence_audit["valid"]:
        status = "partial"
        uncertainty.append({
            "item": "证据审计发现引文/定位问题（见 evidence_audit.json / result.audit.evidence）",
            "impact": "存在页面论断未能在源材料逐字定位",
            "mitigation": "按 evidence_audit.json 的 notes 逐条核对；derived 页以概括语标注"})

    # output_contract collection
    specs = []
    declared_note = []
    case_contract = case.get("output_contract")
    if case_contract is not None:
        cs = normalize_output_contract(case_contract)
        specs.extend(cs)
        declared_note.append("case.json")
    if task_text:
        ts, _note = parse_output_contract_from_task(task_text)
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

    stage = {
        "case": case, "case_id": case_id, "out_dir": out_dir,
        "plan": plan,
        "material_records": material_records,
        "evidence_map": evidence_map,
        "deck_result": deck_result, "deck_ok": deck_ok,
        "deck_audit": deck_audit, "deck_normalized_sha": deck_normalized_sha,
        "deck_failure": deck_failure,
        "environment": env_info,
        "preview_records": preview_records, "preview_ok": preview_ok,
        "preview_limitation": preview_limitation,
        "template_path": template_path,
        "evidence_audit": evidence_audit,
        "plan_gates": plan_gates,
        "uncertainty": uncertainty, "status": status,
        "change_records": change_records,
        "specs": specs, "declared_note": declared_note,
    }
    result, self_check, final_status = fr.finalize_result(stage)

    if args.quiet:
        print("status=%s pages=%d deck=%s validate_valid=%s contract_valid=%s" % (
            final_status, len(plan["pages"]), deck_ok,
            self_check["validate"]["valid"], self_check["contract_check"]["valid"]))
    else:
        print("[done] status=%s deck_ok=%s preview_ok=%s plan_gates=%s "
              "evidence_audit=%s validate_valid=%s contract_valid=%s" % (
                  final_status, deck_ok, preview_ok,
                  bool(plan_gates and plan_gates["valid"]),
                  bool(evidence_audit and evidence_audit["valid"]),
                  self_check["validate"]["valid"],
                  self_check["contract_check"]["valid"]))
        print("[done] output: %s" % out_dir)

    ok = (final_status != "failed" and self_check["validate"]["valid"]
          and self_check["contract_check"]["valid"])
    if ok and not deck_ok and not args.quiet:
        print("[done] NOTE: 可编辑 .pptx 未生成 —— 见 result.json.artifacts.deck_limitation "
              "与 uncertainty；status 已按 partial 如实标注，其余产物均已落盘")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())