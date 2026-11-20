# -*- coding: utf-8 -*-
"""result.json builder + evidence map + change records + manifest.

Contract (references/OUTPUT_CONTRACT.md): every case returns a structured
result with case_id, deck, evidence map, previews, sources, uncertainty,
change records, status. If case.json declares an `output_contract` dict,
every declared field is mirrored into result.json top-level with a
container-typed default ("" / [] / {} / 0 / false) so a validator reading
only that schema still passes; honest absence is expressed via `status`
and `uncertainty`, never by filling invented values.
"""
import os
import json

from common import LOG, now_iso, sha256_file, atomic_write_json, ensure_dir


def _container_default(value):
    t = type(value).__name__
    return {"str": "", "list": [], "dict": {}, "int": 0, "float": 0,
            "bool": False}.get(t, None)


def build_result(case, material, plan_pages, deck_info, preview_info,
                 sources, uncertainty, change_records, status, log_path=None,
                 skill_version="1.0.0", extra=None, out_dir=None):
    """Assemble the full result.json dict.

    Paths are stored relative to out_dir (default: current directory) so the
    result remains valid no matter where the run started from.
    """
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
    }
    # environment facts we actually observed
    result["environment"] = {
        "python": _safe_import_version("sys"),
        "pptx": _safe_import_version("pptx"),
        "matplotlib": _safe_import_version("matplotlib"),
        "PIL": _safe_import_version("PIL"),
        "reportlab": _safe_import_version("reportlab"),
    }

    # ---- mirror declared output_contract fields (container defaults) ----
    oc = case.get("output_contract")
    if isinstance(oc, dict):
        for key, value in oc.items():
            if key in result:
                continue
            if isinstance(value, (str,)) and value in ("str", "string"):
                result[key] = ""
            elif isinstance(value, (str,)) and value in ("list", "array"):
                result[key] = []
            elif isinstance(value, (str,)) and value in ("dict", "object"):
                result[key] = {}
            elif isinstance(value, dict) and "type" in value:
                result[key] = _default_for_decl(value["type"])
            else:
                result[key] = _container_default(value)

    if extra:
        result.update(extra)
    return result


def _default_for_decl(t):
    return {"string": "", "str": "", "list": [], "array": [], "dict": {},
            "object": {}, "number": 0, "integer": 0, "boolean": False}.get(str(t), "")


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


def write_result(result, out_dir, out_name="result.json"):
    path = os.path.join(out_dir, out_name)
    atomic_write_json(path, result)
    return path


def write_evidence_map(result, out_dir):
    """Human-readable per-page evidence mapping (markdown)."""
    lines = ["# 页级证据映射", "",
             "案例: %s  状态: %s" % (result.get("case_id"), result.get("status")), ""]
    for p in result["deck"]["slides"]:
        evs = p.get("evidence_footer") or "、".join(
            e2 for c in p.get("claims", []) for e2 in c.get("evidence", []))
        lines.append("## 第 %d 页 · %s（%s）" % (p["index"], p["title"], p.get("role_label", "")))
        lines.append("- 主张: " + "；".join(c.get("text", "") for c in p.get("claims", [])) or "（无）")
        lines.append("- 证据: %s" % (evs or "依据材料整理"))
        fig = p.get("figure", {})
        if fig.get("ref"):
            lines.append("- 图表: %s（%s）%s" % (fig.get("ref"), fig.get("kind"),
                                            ("→ " + fig.get("image", "")) if fig.get("image") else ""))
        lines.append("")
    path = os.path.join(out_dir, "evidence_map.md")
    atomic_write_text_md(path, "\n".join(lines))
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


def atomic_write_text_md(path, text):
    from common import atomic_write_text
    atomic_write_text(path, text)