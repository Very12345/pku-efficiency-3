# -*- coding: utf-8 -*-
"""main.py — end-to-end: material -> editable .pptx + previews + result.json.

Part of the "paper-to-academic-ppt" Skill (ppt-c7b80f0d, efficiency-3).

Usage
-----
    python main.py --case <case.json> [--task task.md] [--spec deck-spec.json] \\
                   [--materials <dir>] [--out <output dir>] [--demo] [--verbose]
    python main.py --case examples/case.json --spec examples/deck-spec.json \\
                   --out D:/BuildTemp/smoke-ppt-c7b80f0d

Behaviour
---------
1. Reads the *actual* case file (case_id + output_contract + material refs).
2. Locates the paper material (PDF/text/markdown; --materials or case refs).
   PDFs are parsed with scripts/pdf_extract.py (PyMuPDF -> pypdf -> pdfplumber);
   if no PDF library exists the agent's own PDF reader output is expected as
   .txt input. The script NEVER invents paper content.
3. Builds the deck from the agent-written deck-spec.json via deck_builder.py
   (organizer template adaptation, or the built-in academic layout).
4. Renders honest PIL-approximation previews (preview.py) — no PowerPoint /
   LibreOffice is assumed. Reconstructed charts (spec kind=reconstructed_chart)
   are emitted as PNG + editable SVG by matplotlib when available.
5. Writes result.json containing every output_contract field declared by the
   case (type-appropriate empty values when unknown), case_id, deck metadata,
   evidence mapping, sources, uncertainty, change_records and run_meta.
6. Runs a self-validation pass and prints a summary.

Honesty: status is completed/partial/failed and *never* upgraded silently;
material/software states are recorded, not assumed.
"""
from __future__ import annotations

import json
import os
import platform
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import deck_builder          # noqa: E402
import pdf_extract           # noqa: E402
import preview               # noqa: E402

VERSION = "1.0.0"
DEFAULT_OUT_NAME = "academic_deck"


def _container_default(v):
    """Type-appropriate empty value for an unknown declared contract field."""
    if isinstance(v, dict):
        return {}
    if isinstance(v, list):
        return []
    return ""


def apply_output_contract(result, case, spec=None):
    """Echo every field the case declares under output_contract (never null for
    declared containers). This mirrors how the evaluator expects contract fields
    at the top level of result.json. Known semantic fields (title / main_claim /
    slides / notes_separated) get real values from the run when available."""
    contract = case.get("output_contract")
    if isinstance(contract, dict):
        spec_slides = (spec or {}).get("slides", [])
        semantic = {
            "title": (spec or {}).get("deck_title", ""),
            "main_claim": (spec or {}).get("takeaway", ""),
            "slides": [{"page": s.get("page", i + 1), "title": s.get("title", ""),
                        "claim": s.get("claim", "")}
                       for i, s in enumerate(spec_slides)],
            "notes_separated": bool((result.get("deck") or {}).get("notes_separated")),
            "render_state": {
                "previews": len(result.get("previews", [])),
                "rendered_with": (result.get("run_meta") or {}).get("rendered_with"),
                "deck_file": (result.get("deck") or {}).get("file"),
                "evidence_mapping_file": (result.get("evidence_mapping") or {}).get("file"),
            },
        }
        for k, v in contract.items():
            if v is True:  # boolean declared flag
                result.setdefault(k, semantic.get(k, False))
            elif k in semantic and semantic.get(k):
                result.setdefault(k, semantic[k])
            else:
                result.setdefault(k, _container_default(v))
    elif isinstance(contract, list):
        for k in contract:
            if isinstance(k, str):
                result.setdefault(k, _container_default([k]))
    return result


# --------------------------------------------------------------------------- #
# Material discovery
# --------------------------------------------------------------------------- #
def _looks_like_paper_file(name):
    return name.lower().endswith((".pdf", ".txt", ".md", ".tex", ".rst"))


def discover_materials(case, materials_override, work_dir, case_dir=None):
    """Return a list of candidate paper material paths."""
    paths = []
    if materials_override:
        if os.path.isdir(materials_override):
            for n in sorted(os.listdir(materials_override)):
                p = os.path.join(materials_override, n)
                if os.path.isfile(p) and _looks_like_paper_file(n):
                    paths.append(p)
        elif os.path.isfile(materials_override):
            paths.append(materials_override)

    bases = [work_dir]
    if case_dir:
        bases.append(case_dir)

    def _resolve(candidate):
        if not candidate:
            return None
        if os.path.isabs(candidate):
            return candidate if os.path.exists(candidate) else None
        for base in bases:
            joined = os.path.join(base, candidate)
            if os.path.exists(joined):
                return joined
        return None

    for key in ("material", "materials", "paper", "document", "source_pdf", "pdf"):
        val = case.get(key)
        if isinstance(val, str):
            p = _resolve(val)
            if p and p not in paths:
                paths.append(p)
        elif isinstance(val, dict):
            for sub in ("path", "paths", "path_pdf", "file", "files"):
                v = val.get(sub)
                if isinstance(v, str):
                    p = _resolve(v)
                    if p and p not in paths:
                        paths.append(p)
                elif isinstance(v, list):
                    for x in v:
                        if isinstance(x, str):
                            p = _resolve(x)
                            if p and p not in paths:
                                paths.append(p)
        elif isinstance(val, list):
            for x in val:
                if isinstance(x, str):
                    p = _resolve(x)
                    if p and p not in paths:
                        paths.append(p)
    # order: pdf first, then text
    paths.sort(key=lambda p: (not p.lower().endswith(".pdf"), os.path.basename(p)))
    return paths


def read_material_text(path, work_dir):
    """Read a text-like material with page markers from a PDF if possible."""
    low = path.lower()
    if low.endswith(".pdf"):
        extract_dir = os.path.join(work_dir, "extract")
        rep = pdf_extract.extract_pdf(path, extract_dir)
        if rep.get("status") == "ok" and rep.get("text_chars", 0) > 0:
            txt = rep.get("text_file")
            full = os.path.join(extract_dir, txt)
            with open(full, encoding="utf-8", errors="replace") as fh:
                return fh.read(), rep
        return "", rep
    with open(path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    rep = {"pdf": path, "status": "ok_text", "tool": "direct-read",
           "text_chars": len(text), "pages_parsed": 0, "images_extracted": 0,
           "errors": [], "text_file": os.path.relpath(path, work_dir)}
    return text, rep


# --------------------------------------------------------------------------- #
# Evidence mapping markdown
# --------------------------------------------------------------------------- #
def write_evidence_mapping(spec, out_dir, deck_meta):
    """Write the page-level evidence mapping (markdown) for review."""
    lines = ["# 页级证据映射（复核用）", "",
             "> 由 deck-spec.json 生成；引用项对应论文的图/表/章节/页码。",
             "> “证据缺失”是显式标注，不是作者无中生有。", "",
             "| 页 | 标题 | 主张（一句话） | 证据定位 | 状态 |",
             "|---|---|---|---|---|"]
    for s in spec.get("slides", []):
        ev = s.get("evidence") or []
        gap = bool(s.get("evidence_gap"))
        if gap or not ev:
            loc = "EVIDENCE GAP（已显式标注）"
            st = "gap"
        else:
            loc = "; ".join(
                "%s (%s)" % (e.get("ref", "?"), e.get("page") or e.get("location") or "?")
                for e in ev)
            st = "mapped"
        lines.append("| P%02d | %s | %s | %s | %s |" % (
            s.get("page", 0),
            (s.get("title") or "").replace("|", "\\|"),
            (s.get("claim") or "").replace("|", "\\|")[:60],
            loc.replace("|", "\\|"), st))
    lines.append("")
    lines.append("附件：源文件 %s；导出预览见 previews/（PIL 近似渲染）。"
                 % (deck_meta.get("file") and os.path.basename(deck_meta["file"])))
    path = os.path.join(out_dir, "evidence_mapping.md")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines))
    return path


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def run(case_path, task_path, spec_path, materials_override, out_dir, demo, verbose):
    started = time.time()
    os.makedirs(out_dir, exist_ok=True)
    sources = []
    uncertainty = []
    change_records = [{
        "time": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "what": "start run",
        "why": "case %s" % os.path.basename(case_path),
    }]

    # -- case -----------------------------------------------------------------
    try:
        with open(case_path, encoding="utf-8") as fh:
            case = json.load(fh)
    except Exception as exc:
        result = {"case_id": "unknown", "status": "failed",
                  "error": "case_unreadable: %s" % exc,
                  "output_contract": {}, "sources": sources,
                  "uncertainty": uncertainty, "change_records": change_records,
                  "run_meta": _run_meta()}
        _dump_result(out_dir, result)
        return 3

    case_id = case.get("case_id") or case.get("id") or "unknown"
    work_dir = out_dir
    run_meta = _run_meta()
    run_meta["case_file"] = os.path.abspath(case_path)
    paper_text = ""
    material_ok = False
    extract_rep = None
    template_path = None

    # -- material -------------------------------------------------------------
    candidates = discover_materials(case, materials_override, work_dir,
                                    case_dir=os.path.dirname(os.path.abspath(case_path)))
    if candidates:
        chosen = candidates[0]
        try:
            paper_text, extract_rep = read_material_text(chosen, work_dir)
            material_ok = bool(paper_text.strip())
        except Exception as exc:
            extract_rep = {"status": "error", "errors": [str(exc)]}
    if material_ok:
        sources.append({"type": "paper_material", "path": os.path.abspath(chosen),
                        **({k: v for k, v in (extract_rep or {}).items()
                            if k in ("pages_parsed", "text_chars", "images_extracted", "tool")})})
    else:
        sources.append({"type": "paper_material", "path": None,
                        "reason": "no readable paper material found",
                        "extract_status": (extract_rep or {}).get("status", "not_attempted")})

    # -- spec -----------------------------------------------------------------
    spec = None
    spec_source = "none"
    if spec_path and os.path.isfile(spec_path):
        with open(spec_path, encoding="utf-8") as fh:
            spec = json.load(fh)
        spec_source = os.path.abspath(spec_path)
    elif demo or not material_ok:
        spec = deck_builder.spec_from_case_meta(case, paper_text)
        spec_source = "auto-skeleton (demo / missing material)"
        uncertainty.append("deck-spec was auto-generated SKELETON — agent narration "
                           "required for a real deliverable." if not demo else
                           "this run is a DEMO skeleton; not a formal case result")
    if spec:
        spec.setdefault("case_id", case_id)
        spec.setdefault("deck_title", spec.get("deck_title") or (case.get("title") or "Academic Talk"))

    # -- build deck -----------------------------------------------------------
    deal_meta = {
        "file": None, "basename": None, "slide_count": 0,
        "template": {"kind": "none"}, "layouts_used": {},
        "figures": [], "tables": [], "notes_included": False,
        "notes_separated": False, "error": None,
    }
    if not material_ok and not demo:
        uncertainty.append("paper material could not be read — no deck built, nothing invented.")
        deal_meta["error"] = "no_material"
    elif spec:
        template_path = (spec.get("constraints") or {}).get("template_path")
        if not template_path:
            template_path = (case.get("template") or {}).get("path") if isinstance(case.get("template"), dict) else case.get("template")
        template_path = _resolve_template_path(
            template_path,
            os.path.dirname(os.path.abspath(spec_path)) if spec_path and os.path.isfile(spec_path) else None,
            os.path.dirname(os.path.abspath(case_path)),
            work_dir)
        try:
            deal_meta = deck_builder.build_deck(spec, template_path, work_dir, out_dir)
        except Exception as exc:
            deal_meta["error"] = "deck_build_failed: %s" % exc
            import traceback
            if verbose:
                traceback.print_exc()
        if deal_meta.get("page_budget") and deal_meta.get("page_budget_met") is False:
            uncertainty.append(
                "page budget %s exceeded (%s slides) — trim/merge per SKILL S7"
                % (deal_meta["page_budget"], deal_meta.get("slide_count")))

    # -- reconstructed charts -------------------------------------------------
    chart_records = []
    if deal_meta.get("file") and deal_meta.get("error") is None:
        for s in spec.get("slides", []):
            fig = s.get("figure") or {}
            if fig.get("kind") == "reconstructed_chart":
                rec = preview.make_chart(fig, out_dir)
                chart_records.append({"slide": s.get("page", 0),
                                      "ref": fig.get("ref"),
                                      "chart": rec})
                if rec and rec.get("png"):
                    rel = os.path.relpath(rec["file"], out_dir)
                    # re-embed the freshly generated chart into the slide figure
                    s["figure"]["image"] = rel
                if rec and rec.get("reason"):
                    uncertainty.append("reconstructed chart skipped: %s" % rec["reason"])

    # rebuild the deck so the generated chart image is embedded (second pass)
    if deal_meta.get("file") and deal_meta.get("error") is None and any(
            (s.get("figure") or {}).get("kind") == "reconstructed_chart" for s in spec.get("slides", [])):
        try:
            deal_meta = deck_builder.build_deck(spec, template_path, work_dir, out_dir)
        except Exception as exc:
            deal_meta["error"] = "deck_rebuild_failed: %s" % exc

    # -- previews -------------------------------------------------------------
    preview_records = []
    if deal_meta.get("file") and deal_meta.get("error") is None:
        try:
            preview_records = preview.render_all(spec, deal_meta, out_dir)
            rendered_with = "pil-approximation (no PowerPoint/LibreOffice attached)"
        except Exception as exc:
            uncertainty.append("preview render failed: %s" % exc)
            rendered_with = "failed"
    else:
        rendered_with = "not-built"

    # -- evidence mapping -----------------------------------------------------
    ev_path = None
    if deal_meta.get("file") and deal_meta.get("error") is None:
        ev_path = write_evidence_mapping(spec, out_dir, deal_meta)

    # -- result.json ----------------------------------------------------------
    gaps = []
    for s in (spec or {}).get("slides", []):
        if s.get("evidence_gap") or not s.get("evidence"):
            gaps.append(s.get("title") or s.get("page", 0))
    if not material_ok:
        status = "failed" if not deal_meta.get("file") else "partial"
    elif deal_meta.get("error"):
        status = "partial"
    elif gaps:
        status = "partial"
        uncertainty.append("some slides carry explicit evidence gaps: %s" % "; ".join(map(str, gaps[:6])))
    else:
        status = "completed"

    deck_out = None
    if deal_meta.get("file"):
        deck_out = {
            "file": os.path.basename(deal_meta["file"]),
            "path": os.path.relpath(deal_meta["file"], out_dir),
            "slide_count": deal_meta["slide_count"],
            "template": deal_meta["template"],
            "layouts_used": deal_meta["layouts_used"],
            "notes_included": deal_meta["notes_included"],
            "notes_separated": deal_meta["notes_separated"],
            "editable": True,
            "overflow_guard": deal_meta["overflow_guard"],
            "auto_slides": deal_meta.get("auto_slides"),
        }
        if deal_meta.get("page_budget") is not None:
            deck_out["page_budget"] = deal_meta["page_budget"]
            deck_out["page_budget_met"] = bool(deal_meta.get("page_budget_met"))

    run_merged = dict(run_meta)
    run_merged.update({
        "rendered_with": rendered_with,
        "spec_source": spec_source,
        "duration_seconds": round(time.time() - started, 2),
        "skill_version": VERSION,
    })
    result = {
        "case_id": case_id,
        "status": status,
        "task": "academic-presentation-from-paper",
        "deck": deck_out,
        "evidence_mapping": {"file": os.path.basename(ev_path), "entries": len((spec or {}).get("slides", [])),
                             "gaps": gaps} if ev_path else {},
        "previews": preview_records,
        "charts": chart_records,
        "sources": sources,
        "uncertainty": uncertainty,
        "change_records": change_records + [{
            "time": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "what": "run finished",
            "why": "status=%s, deck=%s" % (status, bool(deal_meta.get("file"))),
        }],
        "run_meta": run_merged,
    }
    if not material_ok:
        result["material_status"] = "unreadable"
    if deal_meta.get("error"):
        result["deck_error"] = deal_meta["error"]

    apply_output_contract(result, case, spec)

    # -- self-check -----------------------------------------------------------
    problems = self_check(result, out_dir)
    result["run_meta"]["self_check"] = {"ok": not problems, "problems": problems}
    _dump_result(out_dir, result)
    _print_summary(result, problems, verbose, out_dir)
    return 0 if not problems else 1


def _run_meta():
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "ppt_version": _pkg_version("pptx"),
        "pillow_version": _pkg_version("PIL"),
        "matplotlib_available": _pkg_version("matplotlib") is not None,
        "pdf_tools": pdf_extract._tool_snapshot(),
        "rendered_with": None,  # filled below
        "preview_fidelity": "approximate — PIL re-composition, not PowerPoint rendering",
        "preview_font": preview.find_fonts().get("font_path"),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }


def _pkg_version(name):
    try:
        mod = __import__(name)
        return getattr(mod, "__version__", "unknown")
    except Exception:
        return None


def _resolve_template_path(template_path, spec_dir, case_dir, work_dir):
    """Resolve a relative template path against spec dir -> case dir -> work dir.
    Absolute paths (recommended in real runs, e.g. /input/template.pptx) pass
    through unchanged."""
    if not template_path:
        return template_path
    if os.path.isabs(template_path):
        return template_path
    for base in (spec_dir, case_dir, work_dir):
        cand = os.path.join(base, template_path)
        if os.path.exists(cand):
            return cand
    return template_path


def _dump_result(out_dir, result):
    path = os.path.join(out_dir, "result.json")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2, default=str)
    return path


def self_check(result, out_dir):
    problems = []
    for k in ("case_id", "status", "sources", "uncertainty", "change_records", "run_meta"):
        if k not in result:
            problems.append("missing result field: %s" % k)
    if result.get("status") not in ("completed", "partial", "failed"):
        problems.append("bad status value: %s" % result.get("status"))
    if "output_contract" in result and not isinstance(result.get("output_contract"), (dict, list)):
        problems.append("output_contract must be a dict/list of declared fields")
    deck = result.get("deck") or {}
    if deck.get("file"):
        if not os.path.isfile(os.path.join(out_dir, deck["path"] or deck["file"])):
            problems.append("deck file missing on disk: %s" % deck.get("file"))
        else:
            from pptx import Presentation as _P
            try:
                _P(os.path.join(out_dir, deck["path"] or deck["file"]))
            except Exception as exc:
                problems.append("deck not reopenable with python-pptx: %s" % exc)
    for p in result.get("previews", []):
        f = os.path.join(out_dir, p.get("file", ""))
        if not os.path.isfile(f):
            problems.append("preview missing: %s" % f)
    ev = result.get("evidence_mapping") or {}
    if ev.get("file"):
        if not os.path.isfile(os.path.join(out_dir, ev["file"])):
            problems.append("evidence mapping missing on disk")
    return problems


def _print_summary(result, problems, verbose, out_dir=None):
    print("=" * 64)
    print("case_id      : %s" % result["case_id"])
    print("status       : %s" % result["status"])
    deck = result.get("deck") or {}
    print("deck         : %s (%d slides)" % (deck.get("file"), deck.get("slide_count", 0)))
    print("previews     : %d files" % len(result.get("previews", [])))
    print("evidence_map : %s (entries=%s, gaps=%s)"
          % ((result.get("evidence_mapping") or {}).get("file"),
             (result.get("evidence_mapping") or {}).get("entries"),
             len((result.get("evidence_mapping") or {}).get("gaps", []))))
    print("sources      : %d  uncertainty: %d  changes: %d"
          % (len(result.get("sources", [])), len(result.get("uncertainty", [])),
             len(result.get("change_records", []))))
    print("self_check   : %s" % ("OK" if not problems else problems))
    print("artifacts    : %s" % out_dir)
    print("=" * 64)


def main(argv=None):
    import argparse

    ap = argparse.ArgumentParser(description="paper -> academic PPT (editable) + previews + result.json")
    ap.add_argument("--case", required=True, help="case.json path (or a directory containing case.json)")
    ap.add_argument("--task", default=None, help="task.md path (optional; advisory)")
    ap.add_argument("--spec", default=None, help="deck-spec.json path (agent-written page plan)")
    ap.add_argument("--materials", default=None, help="optional dir/file override for paper material")
    ap.add_argument("--out", required=True, help="output directory (final artifacts live here)")
    ap.add_argument("--demo", action="store_true", help="allow auto skeleton spec (demo/missing-material)")
    ap.add_argument("--verbose", action="store_true", help="print tracebacks")
    args = ap.parse_args(argv)

    case_path = args.case
    if os.path.isdir(case_path):
        case_path = os.path.join(case_path, "case.json")
    if not os.path.isfile(case_path):
        print("case file not found: %s" % case_path, file=sys.stderr)
        return 3
    return run(case_path, args.task, args.spec, args.materials, args.out, args.demo, args.verbose)


if __name__ == "__main__":
    sys.exit(main())