#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scientific-schematic-editor v2 -- CLI orchestrator.

Reads a case (case.json + task.md + source materials), runs the CP1
plan-lint gate (scripts/spec_lint.py) against assets/relation-dict.json,
draws an editable SVG from the ER manifest, renders PNG/PDF (and optional
TIFF/EPS) previews/exports, runs honest export & correctness checks, and
writes a structured result.json per references/OUTPUT_CONTRACT.md (with a
determinism sha probe so identical inputs produce identical output).

Typical invocation (paths absolute -- the script does NOT depend on the
working directory):

    python <skill_root>/scripts/main.py \\
        --case <case.json> \\
        --manifest <entities.json> \\      # optional: ER manifest
        --out <output-dir>

`--case` also accepts a *directory* (`--case examples` resolves to
`examples/case.json`), so the documented one-liner works without knowing
the file name. `--out` is always given explicitly in the docs; when it is
omitted it defaults to ./output relative to cwd.

`--manifest` is optional: if the case.json already carries `entities` /
`relations` / `manifest` / `data`, they are used directly. In the
platform runtime the agent first extracts the ER manifest from the source
materials into /app/work/entities.json and then passes it here. `--out`
defaults to ./output relative to cwd (the platform sets /app/output).

Exit codes: 0 success (with or without warnings), 1 pipeline produced a
partial result (hard check failures -- result.json is still written so the
work is never lost), 2 fatal error (case unreadable, no manifest at all,
or internal error).
"""

import argparse
import json
import os
import shutil
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import hashlib

from manifest import (normalize_manifest, load_manifest, case_to_manifest,
                      validate_manifest, traceability_score, persist_manifest)
from layout import compute_layout
from svgbuilder import build_schematic_svg, write_svg
import render as render_mod
import checks as checks_mod
import edit as edit_mod
import spec_lint as spec_lint_mod
from report import build_result, write_result

try:  # narrow Windows consoles (GBK) must not crash --help or log output
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")
except Exception:
    pass


def log(msg, *args):
    print("[sse] " + (msg % args if args else msg), flush=True)


def now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def resolve_sources(case, case_dir):
    """Normalize source-material references into absolute paths actually
    checked for existence. Returns (list_of_paths, missing_notes)."""
    raw = []
    for key in ("sources", "materials", "input_files", "source_files"):
        v = case.get(key)
        if isinstance(v, list) and v:
            raw.extend(v)
            break
    if isinstance(case.get("materials"), dict):
        raw.extend(case["materials"].values())
    paths, missing = [], []
    for item in raw:
        if isinstance(item, dict):
            p = item.get("path") or item.get("file") or item.get("name")
        else:
            p = item
        if not p:
            continue
        p = str(p)
        ap = p if os.path.isabs(p) else os.path.join(case_dir, p)
        ap = os.path.normpath(ap)
        if os.path.isfile(ap):
            paths.append(ap)
        else:
            missing.append(p)
    return paths, missing


def fetch_manifest(args, case, work_dir):
    """Precedence: --manifest file > case.manifest > case.entities/relations
    > entities.json in the work area. Returns (manifest, provenance_note)."""
    if args.manifest:
        if not os.path.isfile(args.manifest):
            raise FileNotFoundError("--manifest file not found: %s"
                                    % args.manifest)
        return load_manifest(args.manifest), "manifest file: %s" % args.manifest
    ad_hoc = case.get("manifest")
    if isinstance(ad_hoc, dict) and (ad_hoc.get("entities")
                                     or ad_hoc.get("data")):
        return normalize_manifest(ad_hoc), "case.json[manifest]"
    if case.get("entities") or case.get("relations"):
        return case_to_manifest(case), "case.json[entities/relations]"
    work_cand = os.path.join(work_dir, "entities.json")
    if os.path.isfile(work_cand):
        return (load_manifest(work_cand),
                "entities.json in work area (agent-extracted)")
    raise ValueError(
        "no entity-relation manifest available. Extract the ER manifest "
        "from the source materials first (references/ER_MANIFEST.md) and "
        "pass it via --manifest, or let case.json carry "
        "entities/relations/manifest/data. Nothing is drawn without a "
        "manifest: inventing entities would violate the no-fabrication "
        "rule.")


def resolve_case_path(raw):
    """Resolve --case to an actual case.json file.

    Accepts, in order:
      1. a file path (used as-is);
      2. a directory containing `case.json`
         (e.g. `--case <skill_root>/examples`);
      3. a directory containing `examples/case.json`
         (e.g. `--case <skill_root>`);
      4. a directory whose only JSON file looks like a case
         (has case_id / figure_type / workorder).

    Returns (case_path, None) on success or (None, error_message).
    Directories are supported so the documented smoke command
    `main.py --case examples --out <dir>` works without guessing a
    filename; nothing else about case handling changes.
    """
    p = os.path.abspath(raw)
    if os.path.isfile(p):
        return p, None
    if not os.path.isdir(p):
        return None, ("case not found: %s (pass a case.json file or a "
                      "directory containing case.json)" % p)
    for cand in (os.path.join(p, "case.json"),
                 os.path.join(p, "examples", "case.json")):
        if os.path.isfile(cand):
            return cand, None
    import glob
    for cand in sorted(glob.glob(os.path.join(p, "*.json"))):
        try:
            with open(cand, "r", encoding="utf-8") as fh:
                probe = json.load(fh)
        except Exception:
            continue
        if isinstance(probe, dict) and (probe.get("case_id")
                                        or probe.get("figure_type")
                                        or probe.get("workorder")):
            return cand, None
    return None, ("no case.json found under directory: %s (expected "
                  "case.json, examples/case.json or a single case-like "
                  "*.json)" % p)



def _run_doc_check():
    """Pure addition: run the read-only documentation consistency checker.

    Delegates to scripts/doccheck.py next to this file. Never raises: a
    missing helper or a non-zero report must not change this pipeline's own
    exit code or its artefacts.
    """
    helper = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "doccheck.py")
    if not os.path.isfile(helper):
        log("DOC-CHECK: skipped (%s not found)" % helper)
        return
    try:
        import subprocess
        proc = subprocess.run([sys.executable, helper],
                              capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
    except Exception as exc:            # pragma: no cover - defensive
        log("DOC-CHECK: skipped (%r)" % (exc,))
        return
    for line in (proc.stdout or "").strip().splitlines():
        log("DOC-CHECK %s", line)
    if proc.returncode:
        log("DOC-CHECK: report exit=%d (informational; the delivery exit "
            "code is unchanged)" % proc.returncode)

def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="scientific-schematic-editor",
        description="Generate/edit editable scientific schematics and "
                    "charts from source materials, with traceability and "
                    "export checks.")
    ap.add_argument("--case", required=True,
                    help="path to case.json, or a directory containing "
                         "case.json (platform: /input/case.json; smoke: "
                         "--case <skill_root>/examples)")
    ap.add_argument("--manifest",
                    help="optional path to the ER manifest (entities.json)")
    ap.add_argument("--out", default=None,
                    help="output directory (platform: /app/output)")
    ap.add_argument("--work", default=None,
                    help="work directory for intermediate files "
                         "(platform: /app/work; default: --out)")
    ap.add_argument("--edit-svg", default=None,
                    help="existing figure.svg to edit (source-preserving; "
                         "edits read from case.json)")
    ap.add_argument("--base-name", default=None,
                    help="output base name (default: figure)")
    ap.add_argument("--exports", default="png,pdf,svg",
                    help="comma list: png,pdf,svg,tiff,eps "
                         "(default png,pdf,svg)")
    ap.add_argument("--dpi", type=int, default=300,
                    help="raster resolution for PNG/TIFF (default 300)")
    ap.add_argument("--skip-checks", action="store_true",
                    help="write artifacts without running checks")
    ap.add_argument("--lint", dest="lint", action="store_true",
                    default=True,
                    help="run CP1 spec_lint before drawing (default on)")
    ap.add_argument("--no-lint", dest="lint", action="store_false",
                    help="skip the CP1 spec_lint gate")
    ap.add_argument("--fixed-time", default=None,
                    help="override generated_at with this ISO time (used by "
                         "TEST.md for byte-identical determinism double-runs)")
    ap.add_argument("--doc-check", action="store_true",
                    help="run scripts/doccheck.py after the pipeline and "
                         "print the documentation-vs-code consistency report "
                         "(read-only; never changes the produced artefacts)")
    args = ap.parse_args(argv)

    # ---- locate case (file or directory; see resolve_case_path) ----
    case_path, case_err = resolve_case_path(args.case)
    if case_err:
        log("FATAL: %s", case_err)
        return 2
    if os.path.abspath(case_path) != os.path.abspath(args.case):
        log("case resolved: %s", case_path)
    case_dir = os.path.dirname(case_path)
    try:
        with open(case_path, "r", encoding="utf-8") as fh:
            case = json.load(fh)
    except Exception as exc:
        log("FATAL: cannot parse case.json: %r", exc)
        return 2
    if not isinstance(case, dict):
        log("FATAL: case.json must be a JSON object")
        return 2

    # ---- dirs ----
    out_dir = os.path.abspath(args.out or os.path.join(os.getcwd(), "output"))
    work_dir = os.path.abspath(args.work or out_dir)
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(work_dir, exist_ok=True)

    exports = [x.strip().lower() for x in
               (args.exports or "png,pdf,svg").split(",") if x.strip()]
    base_name = args.base_name or "figure"

    # ---- sources ----
    src_paths, missing_src = resolve_sources(case, case_dir)
    source_records = [os.path.relpath(p, case_dir) for p in src_paths]
    for ms in missing_src:
        log("WARN: source material referenced but not found: %s", ms)

    # ---- manifest ----
    if args.edit_svg:
        if not os.path.isfile(args.edit_svg):
            log("FATAL: --edit-svg file not found: %s", args.edit_svg)
            return 2
        try:
            manifest, recs, ed_issues = edit_mod.edit_from_svg(
                args.edit_svg, case.get("edits") or
                case.get("edit_requests") or [], origin="case.json")
            change_records = list(recs)
        except (ValueError, OSError) as exc:
            log("FATAL: %s", exc)
            return 2
        provenance = "source-preserving edit of %s" % args.edit_svg
    else:
        try:
            manifest, provenance = fetch_manifest(args, case, work_dir)
        except (ValueError, FileNotFoundError) as exc:
            log("FATAL: %s", exc)
            _write_failed_result(case, out_dir, source_records, exc)
            return 1
        change_records = []
        if case.get("edits") or case.get("edit_requests"):
            manifest, recs, ed_issues = edit_mod.apply_edits(
                manifest, case.get("edits") or case.get("edit_requests"),
                origin="case.json")
            change_records = list(recs)
            for i in ed_issues:
                log("   [edit] %s %s", i["level"], i["detail"])

    manifest["_provenance"] = provenance
    manifest["_traceability"] = traceability_score(manifest)

    # ---- validate manifest ----
    m_issues = validate_manifest(manifest)
    hard_manifest = [i for i in m_issues if i["level"] == "fail"]
    if hard_manifest:
        log("WARN: manifest validation: %d hard issue(s); result.json will "
            "be status=partial:", len(hard_manifest))
        for i in hard_manifest[:8]:
            log("   - [%s] %s %s", i["level"], i.get("target", ""),
                i["detail"])
    persist_manifest(manifest,
                     os.path.join(work_dir, "manifest.validated.json"))
    if args.manifest:
        shutil.copyfile(args.manifest, os.path.join(work_dir, "entities.json"))

    # ---- CP1 gate: plan/spec lint (SKILL.md CP1) ----
    spec_lint_verdict = None
    if args.lint:
        dict_path = os.path.normpath(os.path.join(_HERE, "..", "assets",
                                                  "relation-dict.json"))
        rel_dict = None
        if os.path.isfile(dict_path):
            with open(dict_path, "r", encoding="utf-8") as fh:
                rel_dict = json.load(fh)
        spec_lint_issues = spec_lint_mod.lint_manifest(manifest, rel_dict)
        spec_fails = [i for i in spec_lint_issues if i["level"] == "fail"]
        spec_lint_verdict = {
            "valid": not spec_fails,
            "fail_count": len(spec_fails),
            "warn_count": sum(1 for i in spec_lint_issues
                              if i["level"] == "warn"),
            "issues": spec_lint_issues,
        }
        for i in spec_lint_issues:
            log("   [spec_lint] %-28s %-4s %s", i["check"], i["level"],
                i["detail"][:110])
        log("SPEC_LINT (CP1): %s (%d fails, %d warns)",
            "VALID" if spec_lint_verdict["valid"] else "INVALID",
            spec_fails and len(spec_fails) or 0,
            spec_lint_verdict["warn_count"])

    # ---- determinism probe (CP5): sha of normalised manifest + lint ----
    determinism = {}
    try:
        m_flat = json.dumps(manifest, sort_keys=True, ensure_ascii=False)
        l_flat = json.dumps(spec_lint_verdict or {}, sort_keys=True)
        determinism = {
            "spec_sha16": hashlib.sha256(
                (m_flat + "|" + l_flat).encode("utf-8")).hexdigest()[:16],
            "note": "same manifest+lint -> same sha; SVG is byte-identical "
                    "across runs (result.json differs only in generated_at "
                    "unless --fixed-time is set)"}
    except Exception:
        determinism = {"spec_sha16": "", "note": "probe failed"}

    # ---- draw ----
    layout = None
    artifacts = {}
    render_info = None
    fig_type = (manifest.get("figure_type") or "schematic").lower()
    try:
        if fig_type == "chart":
            render_info = render_mod.build_chart_artifacts(
                manifest, os.path.join(out_dir, base_name),
                exports=exports, dpi=args.dpi)
            for k in ("png", "pdf", "svg", "tiff", "eps"):
                if k in render_info and render_info[k] and \
                        not isinstance(render_info[k], (dict, list)):
                    p = render_info[k]
                    artifacts[k] = {"path": p,
                                    "rel": os.path.relpath(p, out_dir),
                                    "format": k, "checks": [], "extra": {}}
            if "svg" in artifacts:
                # the SVG is the editable source: promoted to role "figure"
                artifacts["figure"] = artifacts.pop("svg")
                artifacts["figure"]["extra"] = {
                    "role_hint": "editable source (matplotlib SVG, text "
                                 "kept as <text>)"}
            if "png" in artifacts:
                # PNG is the raster preview, same role for charts as for
                # schematics (G7 wants figure + preview + export)
                artifacts["preview"] = artifacts.pop("png")
                artifacts["preview"]["extra"] = {
                    "role_hint": "raster preview of the editable source"}
        else:
            layout = compute_layout(manifest)
            svg_xml = build_schematic_svg(manifest, layout)
            svg_path = write_svg(os.path.join(out_dir, base_name + ".svg"),
                                 svg_xml)
            artifacts["figure"] = {"path": svg_path,
                                   "rel": os.path.relpath(svg_path, out_dir),
                                   "format": "svg", "checks": [],
                                   "extra": {"role_hint":
                                             "editable layered SVG source"}}
            r_info = render_mod.render_schematic(
                manifest, layout, os.path.join(out_dir, base_name + ".png"),
                exports=exports, dpi=args.dpi)
            if r_info.get("png"):
                artifacts["preview"] = {
                    "path": r_info["png"],
                    "rel": os.path.relpath(r_info["png"], out_dir),
                    "format": "png", "checks": [],
                    "extra": {"font": r_info.get("font"),
                              "cjk_ok": r_info.get("cjk_ok")}}
            for k in ("pdf", "tiff", "eps"):
                if r_info.get(k):
                    artifacts[k] = {"path": r_info[k],
                                    "rel": os.path.relpath(r_info[k], out_dir),
                                    "format": k, "checks": [],
                                    "extra": {"role_hint":
                                              "export for submission"}}
            render_info = {"kind": "schematic",
                           "font": r_info.get("font"),
                           "cjk_ok": r_info.get("cjk_ok"),
                           "layout": {"canvas": layout["canvas"],
                                      "node_count": len(layout["nodes"]),
                                      "edge_count": len(layout["edges"])}}
            layout_path = os.path.join(work_dir, "layout.json")
            persist_manifest({"canvas": layout["canvas"],
                              "nodes": layout["nodes"],
                              "edges": layout["edges"]}, layout_path)
            artifacts["figure"]["extra"]["layout"] = os.path.relpath(
                layout_path, out_dir)
    except Exception as exc:
        log("FATAL(render): %r", exc)
        _write_failed_result(case, out_dir, source_records, exc, manifest)
        return 1

    # ---- checks ----
    all_issues = []
    overall = {"status": "success", "fail_count": 0, "warn_count": 0,
               "ack_count": 0, "fails": [], "warns": [], "acks": []}
    if not args.skip_checks and artifacts:
        role_paths = {role: art["path"] for role, art in artifacts.items()}
        all_issues = checks_mod.check_all(
            manifest, role_paths,
            layout=layout if fig_type != "chart" else None,
            render_info=render_info if fig_type == "chart" else render_info)
        ack = (manifest.get("acknowledged_issues")
               or case.get("acknowledged_issues") or [])
        overall = checks_mod.summarize(all_issues, ack)
        if spec_lint_verdict and not spec_lint_verdict.get("valid"):
            # CP1 gate: hard lint fails downgrade the run honestly (never
            # silently pretend a non-compliant plan produced full success)
            spec_fails = [i for i in (spec_lint_verdict.get("issues") or [])
                          if i["level"] == "fail"]
            overall["status"] = "partial"
            overall["fail_count"] += len(spec_fails)
            overall["fails"] = list(overall.get("fails") or []) + [
                {"check": "spec_lint." + i.get("check", "gate"),
                 "level": "fail",
                 "detail": "CP1: " + i["detail"]} for i in spec_fails]
        for i in all_issues:
            log("   [check] %-26s %-4s %s", i["check"], i["level"],
                i["detail"][:110])
        log("CHECK SUMMARY: %s (%d fails, %d warns, %d acks)",
            overall["status"], overall["fail_count"], overall["warn_count"],
            overall["ack_count"])

    # attach per-artifact checks
    prefix = {"svg": "svg.", "png": "bitmap.", "tiff": "bitmap.",
              "tif": "bitmap.", "pdf": "pdf."}
    for role, art in artifacts.items():
        pfx = prefix.get(art["format"], "artifact.%s." % role)
        art["checks"] = [i for i in all_issues
                         if i["check"].startswith(pfx)]
        art["extra"] = art.get("extra") or {}

    # ---- uncertainty ----
    uncertainty = []
    u1 = case.get("uncertainty")
    if isinstance(u1, list):
        uncertainty.extend(u1)
    elif isinstance(u1, str) and u1:
        uncertainty.append({"item": "agent-stated", "note": u1})
    if missing_src:
        uncertainty.append({"item": "unresolved source materials",
                            "note": "referenced but not found: %s"
                                    % ", ".join(missing_src)})
    if fig_type == "schematic":
        uncertainty.append({
            "item": "layout",
            "note": "auto-layout; verify grouping/ordering against the "
                    "source when the figure has strong layout requirements "
                    "(entity['pos'] overrides are honoured)."})
    if isinstance(render_info, dict) and render_info.get("cjk_ok") is False:
        uncertainty.append({"item": "fonts",
                            "note": "no CJK font for matplotlib -- Chinese "
                                    "labels may show as boxes in PNG "
                                    "previews (SVG keeps the text)."})
    uncertainty.append(
        {"item": "preview fidelity",
         "note": "PNG/PDF previews are a matplotlib mirror of the same "
                 "layout+manifest (cairosvg unavailable at runtime); they "
                 "match the editable SVG semantically, not pixel-for-pixel."})

    # ---- result.json ----
    result = build_result(case, manifest, overall, artifacts, render_info,
                          source_records, uncertainty, change_records,
                          spec_lint=spec_lint_verdict, determinism=determinism)
    if args.fixed_time:
        result["generated_at"] = args.fixed_time
    rp = write_result(os.path.join(out_dir, "result.json"), result)
    log("wrote %s", rp)

    log("deliverables in %s:", out_dir)
    for role, art in sorted(artifacts.items()):
        log("   %-8s %-6s %s (%d bytes)", role, art["format"], art["rel"],
            os.path.getsize(art["path"])
            if os.path.isfile(art["path"]) else 0)

    if getattr(args, "doc_check", False):
        _run_doc_check()

    return 0 if overall["status"] == "success" else 1


def _write_failed_result(case, out_dir, source_records, exc, manifest=None):
    """Write an honest result.json when the pipeline cannot complete."""
    try:
        result = build_result(
            case, normalize_manifest(manifest or {}),
            {"status": "failed", "fail_count": 1, "warn_count": 0,
             "ack_count": 0,
             "fails": [{"check": "pipeline", "level": "fail",
                        "detail": str(exc)}],
             "warns": [], "acks": []},
            artifacts={},
            render_info={},
            sources=[p for p in source_records],
            uncertainty=[{"item": "pipeline error", "note": str(exc)}],
            change_records=[],
            header="Pipeline failed; no figure produced. %s" % exc)
        write_result(os.path.join(out_dir, "result.json"), result)
        log("wrote failed-status result.json: %s",
            os.path.join(out_dir, "result.json"))
    except Exception as e2:
        log("WARN: could not write failed result.json: %r", e2)


if __name__ == "__main__":
    sys.exit(main())