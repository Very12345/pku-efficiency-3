# -*- coding: utf-8 -*-
"""result_tool.py — verify layer: 结果信封 result.json + 证据映射双形态 + 契约校验
（对齐高分包 result_tool + check_contract：结果信封收口）。

职责（verify 轴）：
* `build_result`：组装 result.json（output_contract 四形态回显、禁止 null、
  case_id、deck/evidence/previews/sources/uncertainty/change_records/
  environment/run_meta 等）；
* 双形态证据映射：evidence_map.md（人读）+ evidence_map.json（机器读，同源）
  —— 保证"页级证据映射"既给人查也支持自动校验；
* `write_changelog` / `write_manifest`：版本记录与产物 sha256 清单；
* `validate`（G1–G8 硬性门 + 结果信封 templates/result_envelope.json 合规）：
  独立 CLI `python scripts/result_tool.py --result ... --out-dir ... [--case ...]`，
  exit 0 = 通过。G 门定义见 references/OUTPUT_CONTRACT.md §8。
"""
import json
import os
import sys

from deck_common import LOG, now_iso, sha256_file, atomic_write_json, atomic_write_text, ensure_dir


# ---------------------------------------------------------------------------
# Container-typed defaults (four-shape echo; never null)
# ---------------------------------------------------------------------------

def _container_default(value):
    t = type(value).__name__
    return {"str": "", "list": [], "dict": {}, "int": 0, "float": 0,
            "bool": False}.get(t, None)


def _default_for_decl(t):
    return {"string": "", "str": "", "list": [], "array": [], "dict": {},
            "object": {}, "number": 0, "integer": 0, "boolean": False}.get(str(t), "")


def apply_output_contract(result, case):
    """Mirror every declared output_contract field to result.json top level.

    Declared containers get type-appropriate empty values (never null):
    string -> "", list/array -> [], dict/object -> {}, bool/boolean -> false,
    int/float/number -> 0 (D10 四形态回显); fields that already carry real
    values keep them.
    """
    oc = case.get("output_contract")
    if isinstance(oc, dict):
        for key, value in oc.items():
            if key in result:
                continue
            if isinstance(value, str) and value in ("str", "string"):
                result[key] = ""
            elif isinstance(value, str) and value in ("list", "array"):
                result[key] = []
            elif isinstance(value, str) and value in ("dict", "object"):
                result[key] = {}
            elif isinstance(value, str) and value in ("bool", "boolean"):
                result[key] = False
            elif isinstance(value, str) and value in ("int", "integer", "float", "number"):
                result[key] = 0
            elif isinstance(value, dict) and "type" in value:
                result[key] = _default_for_decl(value["type"])
            else:
                result[key] = _container_default(value)
    elif isinstance(oc, list):
        for key in oc:
            if isinstance(key, str):
                result.setdefault(key, _container_default([key]))
    return result


# ---------------------------------------------------------------------------
# Envelope loading (templates/result_envelope.json)
# ---------------------------------------------------------------------------

_ENVELOPE_CACHE = {}


def load_envelope(envelope_path=None):
    """Load the result envelope declaration (field types / required lists).

    Falls back to built-in defaults when the file is missing so the validator
    still runs; a missing envelope file itself is reported as a warning.
    """
    if _ENVELOPE_CACHE:
        return _ENVELOPE_CACHE["data"], _ENVELOPE_CACHE.get("path")
    data = {
        "envelope_version": "2.0",
        "required_fields": [
            {"field": "case_id", "type": "string"},
            {"field": "title", "type": "string"},
            {"field": "status", "type": "string"},
            {"field": "created_at", "type": "string"},
            {"field": "skill_version", "type": "string"},
            {"field": "deck", "type": "object"},
            {"field": "evidence", "type": "object"},
            {"field": "previews", "type": "object"},
            {"field": "sources", "type": "array"},
            {"field": "uncertainty", "type": "array"},
            {"field": "change_records", "type": "array"},
            {"field": "evidence_map_json", "type": "string"},
            {"field": "manifest", "type": "string"},
            {"field": "log", "type": "string"},
            {"field": "checks", "type": "object"},
            {"field": "environment", "type": "object"},
            {"field": "run_meta", "type": "object"},
        ],
        "deck_required": ["editable", "format", "template", "slide_count", "slides", "notes", "receipt"],
        "evidence_required": ["map", "unverified_claims", "material_warnings"],
        "previews_required": ["pngs", "pdf", "method", "warnings"],
        "status_vocabulary": ["success", "partial", "failed"],
    }
    path = None
    if envelope_path and os.path.isfile(envelope_path):
        try:
            with open(envelope_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            path = os.path.abspath(envelope_path)
        except Exception as e:  # noqa: BLE001
            LOG.warning("envelope unreadable, using built-in: %s", e)
    _ENVELOPE_CACHE["data"] = data
    _ENVELOPE_CACHE["path"] = path
    return data, path


# ---------------------------------------------------------------------------
# result.json builder
# ---------------------------------------------------------------------------

def _portable(path):
    """Forward slashes on every platform (JSON consumers may be Linux)."""
    return (path or "").replace("\\", "/")


def _page_evidence(p):
    evs = []
    for c in p.get("claims", []):
        for e in c.get("evidence", []):
            if e and e not in evs:
                evs.append(e)
    return evs


def build_result(case, material, plan_pages, deck_info, preview_info,
                 sources, uncertainty, change_records, status, log_path=None,
                 skill_version="2.0.0", out_dir=None):
    """Assemble the full result.json dict (paths relative to out_dir)."""
    base = out_dir or "."
    case_id = case.get("case_id") or "unknown"
    spec = case.get("spec") or {}

    pages_meta = []
    for p in plan_pages:
        fig = p.get("figure", {})
        pages_meta.append({
            "index": p.get("index"),
            "role": p.get("role"),
            "role_label": p.get("role_label", p.get("role")),
            "title": p.get("title"),
            "claims": [{"text": c.get("text", ""),
                        "evidence": c.get("evidence", []),
                        "verified": c.get("verified", True),
                        "missing_numbers": c.get("missing_numbers", [])}
                       for c in p.get("claims", [])],
            "figure": {"ref": fig.get("ref", ""), "kind": fig.get("kind", "none"),
                       "table_id": fig.get("table_id", ""),
                       "image": fig.get("image", ""), "note": fig.get("note", "")},
            "notes": p.get("notes", []),
            "evidence_footer": p.get("evidence_footer", ""),
        })

    deck = {
        "editable": _portable(deck_info.get("editable", "")),
        "format": "pptx",
        "template": spec.get("template", "default"),
        "template_pptx": spec.get("template_pptx", ""),
        "starting_deck": spec.get("starting_deck", ""),
        "slide_count": deck_info.get("slide_count", len(pages_meta)),
        "slides": pages_meta,
        "notes": deck_info.get("notes", True),
        "receipt": deck_info.get("receipt", []),
    }

    evidence = {
        "map": [{"page": p.get("index"), "role": p.get("role"),
                 "title": p.get("title"),
                 "evidence": _page_evidence(p),
                 "figure_ref": p.get("figure", {}).get("ref", ""),
                 "figure_kind": p.get("figure", {}).get("kind", "none")}
                for p in pages_meta],
        "unverified_claims": [
            {"page": p.get("index"), "text": c.get("text"),
             "missing_numbers": c.get("missing_numbers", [])}
            for p in pages_meta for c in p.get("claims", [])
            if not c.get("verified", True)],
        "material_warnings": list(material.warnings or []),
    }

    result = {
        "case_id": case_id,
        "title": material.title or case.get("title") or case_id,
        "status": status,                      # success | partial | failed
        "created_at": now_iso(),
        "skill_version": skill_version,
        "deck": deck,
        "evidence": evidence,
        "previews": {
            "pngs": [_portable(os.path.relpath(p, base)) for p in (preview_info.get("pngs") or [])],
            "pdf": _portable(os.path.relpath(preview_info["pdf"], base)) if preview_info.get("pdf") else "",
            "method": "PIL/reportlab 预览渲染，非 PowerPoint 导出",
            "warnings": preview_info.get("warnings", []),
        },
        "sources": sources,
        "uncertainty": list(uncertainty),
        "change_records": list(change_records),
        "log": _portable(log_path) if log_path else "",
        "checks": deck_info.get("checks", {}),
        "evidence_map_json": deck_info.get("evidence_map_json", ""),
        "manifest": deck_info.get("manifest", ""),
    }
    result["environment"] = {
        "python": _safe_import_version("sys"),
        "pptx": _safe_import_version("pptx"),
        "matplotlib": _safe_import_version("matplotlib"),
        "PIL": _safe_import_version("PIL"),
        "reportlab": _safe_import_version("reportlab"),
    }
    return apply_output_contract(result, case)


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------

def write_result(result, out_dir, out_name="result.json"):
    path = os.path.join(out_dir, out_name)
    atomic_write_json(path, result)
    return path


def write_evidence_map(result, out_dir):
    """Human-readable per-page evidence mapping (markdown table)."""
    from evidence_check import evidence_rows
    rows = evidence_rows(result.get("deck", {}).get("slides", []))
    lines = ["# 页级证据映射", "",
             "> 案例: %s · 状态: %s · 由 result.json 的页级模型生成（双形态："
             "本 md + evidence_map.json 机器可读）。" % (result.get("case_id"), result.get("status")),
             "> “证据缺失”为显式标注（gap），不是作者无中生有。", "",
             "| 页 | 角色 | 标题 | 证据定位 | 状态 |",
             "|---|---|---|---|---|"]
    for r in rows:
        loc = "、".join(r["evidence"]) if r["evidence"] else "EVIDENCE GAP（已显式标注）"
        lines.append("| P%02d | %s | %s | %s | %s |" % (
            r["page"], r["role_label"], (r["title"] or "").replace("|", "\\|"),
            loc.replace("|", "\\|"), r["status"]))
    lines += ["", "> 预览为 PIL/reportlab 近似渲染（非 PowerPoint 导出），见 previews/。"]
    path = os.path.join(out_dir, "evidence_map.md")
    atomic_write_text(path, "\n".join(lines))
    return path


def write_evidence_map_json(result, out_dir):
    """Machine-readable per-page evidence mapping (same source as the md)."""
    from evidence_check import evidence_rows
    rows = evidence_rows(result.get("deck", {}).get("slides", []))
    payload = {
        "source": "result.json deck.slides (same source as evidence_map.md)",
        "case_id": result.get("case_id"),
        "status": result.get("status"),
        "rows": rows,
        "unverified_claims": result.get("evidence", {}).get("unverified_claims", []),
    }
    path = os.path.join(out_dir, "evidence_map.json")
    atomic_write_json(path, payload)
    return path


def write_changelog(out_dir, records):
    """Append change records as JSONL; returns path."""
    ensure_dir(out_dir)
    path = os.path.join(out_dir, "changelog.jsonl")
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return path


def write_manifest(out_dir):
    """sha256 manifest of all output files (verifiability)."""
    manifest = {"generated_at": now_iso(), "files": []}
    root = os.path.abspath(out_dir)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for name in sorted(filenames):
            fp = os.path.join(dirpath, name)
            try:
                manifest["files"].append({"path": os.path.relpath(fp, root),
                                          "sha256": sha256_file(fp),
                                          "size": os.path.getsize(fp)})
            except Exception as e:  # noqa: BLE001
                manifest["files"].append({"path": os.path.relpath(fp, root),
                                          "sha256": "", "size": -1, "error": str(e)})
    path = os.path.join(out_dir, "manifest.json")
    atomic_write_json(path, manifest)
    return path


def _safe_import_version(module_name):
    try:
        if module_name == "sys":
            import sys
            return sys.version.split()[0]
        import importlib
        mod = importlib.import_module(module_name)
        return str(getattr(mod, "__version__", "?"))
    except Exception:  # noqa: BLE001
        return "unavailable"


# ---------------------------------------------------------------------------
# G1–G8 contract validation (CP3 gate)
# ---------------------------------------------------------------------------

REQUIRED_TOP = ["case_id", "status", "created_at", "deck", "evidence",
                "previews", "sources", "uncertainty", "change_records"]
DECK_KEYS = ["editable", "format", "slide_count", "slides"]
EVIDENCE_KEYS = ["map", "unverified_claims"]
PREVIEW_KEYS = ["pngs", "pdf", "method"]
STATUS_VALUES = {"success", "partial", "failed"}


def _count_md_table_rows(path):
    try:
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    except Exception:  # noqa: BLE001
        return None
    rows, in_table, header = 0, False, False
    import re as _re
    for ln in lines:
        if ln.strip().startswith("|"):
            if not in_table:
                in_table, header = True, True
            parts = [c.strip() for c in ln.strip().strip("|").split("|")]
            if header:
                header = False
                continue
            if all(_re.fullmatch(r":?-{3,}:?", p) for p in parts):
                continue
            if any(p for p in parts):
                rows += 1
        elif ln.strip():
            in_table = False
    return rows


def validate(result, out_dir=None, case=None, envelope_path=None):
    """CP3 gate: G1–G8 + envelope conformance. Returns report dict.

    G1 result 可解析且必备顶层字段齐、status 在词汇表；G2 case_id/契约回显；
    G3 deck 存在且可重开、页数一致；G4 证据 map 行数=页数与未核验留痕；
    G5 预览文件存在且如实标注；G6 每页演讲备注非空；G7 sources sha + manifest；
    G8 结果信封字段类型合规。
    """
    errors, warnings = [], []
    base = out_dir or "."
    envelope, env_path = load_envelope(envelope_path)
    if env_path is None and envelope_path:
        warnings.append("result envelope file missing: %s (used built-in)" % envelope_path)

    # -- G1 ------------------------------------------------------------------
    for k in REQUIRED_TOP:
        if k not in result:
            errors.append("G1 missing top-level field: %s" % k)
        elif result[k] is None:
            errors.append("G1 top-level field is null: %s" % k)
    for k in DECK_KEYS:
        if k not in result.get("deck", {}):
            errors.append("G1 deck missing field: %s" % k)
    for k in EVIDENCE_KEYS:
        if k not in result.get("evidence", {}):
            errors.append("G1 evidence missing field: %s" % k)
    for k in ("sources", "uncertainty", "change_records"):
        if not isinstance(result.get(k), list):
            errors.append("G1 %s should be a list" % k)

    # -- G2 ------------------------------------------------------------------
    cid = result.get("case_id")
    if not cid:
        errors.append("G2 case_id empty/missing")
    if case is not None and cid != case.get("case_id"):
        warnings.append("G2 case_id %r != case.json case_id %r" % (cid, case.get("case_id")))
    oc = (case or {}).get("output_contract")
    if isinstance(oc, dict):
        for key in oc:
            if key not in result:
                errors.append("G2 declared output_contract field missing: %s" % key)
            elif result[key] is None:
                errors.append("G2 output_contract field is null: %s (must be ''/[]/{})" % key)

    # -- G3 ------------------------------------------------------------------
    status = result.get("status")
    if status not in STATUS_VALUES:
        errors.append("G1 invalid status: %r" % status)
    editable = result.get("deck", {}).get("editable", "")
    slide_count = result.get("deck", {}).get("slide_count")
    if editable:
        ep = editable if os.path.isabs(editable) else os.path.join(base, editable)
        if not os.path.isfile(ep):
            errors.append("G3 editable deck file missing: %s" % editable)
        else:
            try:
                from pptx import Presentation
                prs = Presentation(ep)
                n = len(prs.slides._sldIdLst)
                if n != slide_count:
                    errors.append("G3 deck reopen slide_count=%d != result slide_count=%s" % (n, slide_count))
                if n != len(result.get("deck", {}).get("slides", [])):
                    errors.append("G3 deck reopen pages=%d != deck.slides=%d" % (n, len(result.get("deck", {}).get("slides", []))))
            except Exception as e:  # noqa: BLE001
                errors.append("G3 deck not reopenable with python-pptx: %s" % e)

    # -- G4 ------------------------------------------------------------------
    slides = result.get("deck", {}).get("slides", [])
    ev_rows = result.get("evidence", {}).get("map", [])
    if ev_rows and len(ev_rows) != len(slides):
        errors.append("G4 evidence.map rows=%d != deck.slides=%d" % (len(ev_rows), len(slides)))
    for p in slides:
        if not p.get("role") or not p.get("title"):
            errors.append("G4 slide %s missing role/title" % p.get("index"))
        claims = p.get("claims", [])
        evs = _page_evidence(p)
        if claims and not evs and p.get("figure", {}).get("kind") == "none":
            # content slide with claims must be traceable; cover/blank pages
            # legitimately carry no claims, hence no evidence requirement
            errors.append("G4 slide %s has claims (%d) but no evidence and no figure "
                          "(must be an explicit gap)" % (p.get("index"), len(claims)))
    unp = len(result.get("evidence", {}).get("unverified_claims", []))
    if unp and status == "success":
        warnings.append("G4 status=success but %d unverified claims recorded (must be explained)" % unp)

    # -- G5 ------------------------------------------------------------------
    pdf = result.get("previews", {}).get("pdf", "")
    if pdf and not os.path.isfile(pdf if os.path.isabs(pdf) else os.path.join(base, pdf)):
        warnings.append("G5 preview pdf missing: %s" % pdf)
    pngs = result.get("previews", {}).get("pngs", [])
    if not pngs and status == "success":
        errors.append("G5 no preview pngs produced")
    for p in pngs[:1]:
        if not os.path.isfile(p if os.path.isabs(p) else os.path.join(base, p)):
            errors.append("G5 preview png missing: %s" % p)
    method = result.get("previews", {}).get("method", "")
    if "预览" not in method and "preview" not in str(method).lower():
        warnings.append("G5 preview method not honestly labeled: %r" % method)

    # -- G6 ------------------------------------------------------------------
    missing_notes = [p.get("index") for p in slides if not (p.get("notes") or [])]
    if missing_notes:
        errors.append("G6 slides without speaker notes: %s" % missing_notes)

    # -- G7 ------------------------------------------------------------------
    for s in result.get("sources", []):
        if not s.get("sha256"):
            warnings.append("G7 source without sha256: %s" % s.get("path"))
    if not os.path.isfile(os.path.join(base, "manifest.json")):
        warnings.append("G7 manifest.json missing (verifiability artifact)")

    # -- G8 (envelope conformance) --------------------------------------------
    for decl in envelope.get("required_fields", []):
        key = decl.get("field")
        want = decl.get("type")
        if key not in result:
            errors.append("G8 envelope field missing: %s" % key)
            continue
        got = type(result[key]).__name__
        type_map = {"string": "str", "object": "dict", "array": "list"}
        if type_map.get(want, want) != got:
            warnings.append("G8 envelope field %s type %s != declared %s" % (key, got, want))

    ok = not errors
    report = {"valid": ok, "errors": errors, "warnings": warnings,
              "case_id": result.get("case_id"), "status": status,
              "gates": {"G1": _gate(errors, "G1"), "G2": _gate(errors, "G2"),
                        "G3": _gate(errors, "G3"), "G4": _gate(errors, "G4"),
                        "G5": _gate(errors, "G5"), "G6": _gate(errors, "G6"),
                        "G7": _gate(errors, "G7"), "G8": _gate(errors, "G8")}}
    return report


def _gate(errors, tag):
    return not any(e.startswith(tag) for e in errors)


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="result envelope contract check (G1–G8)")
    ap.add_argument("--result", required=True, help="result.json path")
    ap.add_argument("--out-dir", default=".", help="directory where artifacts live")
    ap.add_argument("--case", default=None, help="original case.json (contract echo check)")
    ap.add_argument("--envelope", default=None, help="result_envelope.json (optional)")
    args = ap.parse_args(argv)

    try:
        with open(args.result, "r", encoding="utf-8") as f:
            result = json.load(f)
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"valid": False, "errors": ["result unreadable: %s" % e],
                          "warnings": []}))
        return 2
    case = None
    if args.case and os.path.isfile(args.case):
        with open(args.case, "r", encoding="utf-8") as f:
            case = json.load(f)
    report = validate(result, args.out_dir, case, args.envelope)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())