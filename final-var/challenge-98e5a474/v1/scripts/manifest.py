#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Entity-Relation (ER) manifest handling for scientific-schematic-editor.

The ER manifest is the single source of truth a figure is drawn from.
Every entity and every relation MUST carry a `source` (which material
file/section) and `evidence` (short quote, table row, or figure label) so
that the finished figure stays traceable back to the originals.

This module loads, normalizes, validates, persists and re-extracts
manifests — including the copy embedded inside a generated figure.svg
(which is what makes "source-preserving edit" possible).

Only the Python standard library is used.
"""

import json
import os
import re
import sys

# ---------------------------------------------------------------------------
# Canonical relation vocabulary.
# Mapping a free-text relation (`kind`) onto these canonical kinds is the
# single most important correctness step: activation vs inhibition vs
# containment decides how the arrow is drawn.
# ---------------------------------------------------------------------------
CANONICAL_KINDS = {
    "activation": {
        "synonyms": (
            "activates", "stimulates", "promotes", "enhances", "induces",
            "positively-regulates", "phosphorylates", "activates transcription of",
            "激活", "促进", "增强", "诱导", "正调控",
        ),
        "arrow": "activation",   # solid arrow head
        "line": "solid",
    },
    "inhibition": {
        "synonyms": (
            "inhibits", "represses", "blocks", "suppresses", "negates",
            "negatively-regulates", "downregulates", "down-regulates",
            "antagonizes", "negative regulation", "prevents",
            "抑制", "阻断", "阻遏", "下调", "负调控", "拮抗", "阻止",
        ),
        "arrow": "inhibition",   # perpendicular T-bar
        "line": "solid",
    },
    "recruitment": {
        "synonyms": (
            "recruits", "binds", "interacts-with", "associates", "binds to",
            "interacts with", "recruited by", "dock", "docking",
            "招募", "结合", "相互作用", "互作",
        ),
        "arrow": "open",         # chevron (direction = "recruits …")
        "line": "solid",
    },
    "process": {
        "synonyms": (
            "produces", "converts", "leads-to", "generates", "cleaves",
            "transcribes", "translates", "synthesizes", "release", "catalyzes",
            "产生", "生成", "转化", "催化", "裂解", "翻译", "分泌",
        ),
        "arrow": "open",
        "line": "solid",
    },
    "transcriptional": {
        "synonyms": (
            "upregulates-gene", "drives-transcription", "promotes-expression",
            "induces-expression", "activation of transcription",
            "转录上调", "上调转录", "上调基因表达", "促进转录", "驱动转录",
        ),
        "arrow": "open",
        "line": "dashed",        # dashed line = gene/transcription level event
    },
    "causal": {
        "synonyms": (
            "causes", "triggers", "leads to", "results in", "promotes outcome",
            "导致", "引发", "引起", "促使",
        ),
        "arrow": "open",
        "line": "solid",
    },
    "containment": {
        "synonyms": (
            "contains", "is-part-of", "composed-of", "includes", "is member of",
            "part of", "localized to",
            "包含", "属于", "组成", "构成", "定位于",
        ),
        "arrow": "none",         # drawn as group boxes, never as an arrow
        "line": "none",
    },
}


def canonical_kind(kind, _cache=None):
    """Map a free-text relation kind onto the canonical arrow style.

    Returns (canonical_name or None, is_unknown).
    """
    if not kind:
        return None, True
    k = str(kind).strip().lower().replace("_", "-")
    if k in CANONICAL_KINDS:
        return k, False
    for canon, spec in CANONICAL_KINDS.items():
        sn = tuple(s.replace(" ", "-").lower() for s in spec["synonyms"])
        if k in sn:
            return canon, False
    # loose word-level match ("IL-6 activates NF-kB" style phrases)
    for canon, spec in CANONICAL_KINDS.items():
        for s in spec["synonyms"]:
            words = s.replace(" ", "-").lower().split("-")
            if len(words) >= 2 and all(w in k.split("-") or w in k for w in words):
                return canon, False
    return None, True


def normalize_manifest(manifest):
    """Fill defaults, canonicalize relation kinds, re-index entities."""
    m = dict(manifest or {})
    m.setdefault("schema_version", "1.0")
    m.setdefault("figure_type", "schematic")
    m.setdefault("title", "")
    m.setdefault("subtitle", "")
    entities = list(m.get("entities") or [])
    relations = list(m.get("relations") or [])
    groups = list(m.get("groups") or [])
    legend = list(m.get("legend") or [])

    # entity index for lookup
    for idx, e in enumerate(entities):
        e.setdefault("id", "E%d" % (idx + 1))
        e.setdefault("name", str(e.get("id", "?")))
        e.setdefault("type", "entity")
        e.setdefault("source", "")
        e.setdefault("evidence", "")
        e.setdefault("note", "")

    id_set = {e["id"] for e in entities}

    for idx, r in enumerate(relations):
        r.setdefault("id", "R%d" % (idx + 1))
        r.setdefault("from", "")
        r.setdefault("to", "")
        r.setdefault("kind", "")
        r.setdefault("label", "")
        r.setdefault("source", "")
        r.setdefault("evidence", "")
        r.setdefault("note", "")
        canon, unknown = canonical_kind(r.get("kind"))
        r["_canon"] = canon
        r["_unknown_kind"] = unknown
        if not r.get("label"):
            r["label"] = str(r.get("kind") or "")

    for idx, g in enumerate(groups):
        g.setdefault("id", "G%d" % (idx + 1))
        g.setdefault("label", "")
        g.setdefault("members", [])
        g.setdefault("source", "")
        g.setdefault("evidence", "")
        # members may not be present in the entity list; keep them but note it
        unknown_members = [mid for mid in g["members"] if mid not in id_set]
        g["_unknown_members"] = unknown_members

    # legend normalization
    used_arrows = sorted({r["_canon"] for r in relations if r["_canon"]})
    default_legend = []
    for i, kind in enumerate(used_arrows):
        if kind == "containment":
            continue
        default_legend.append({
            "id": "L-%s" % kind,
            "key": kind,
            "label": "%s (%s)" % (kind, CANONICAL_KINDS[kind]["arrow"]),
            "arrow": CANONICAL_KINDS[kind]["arrow"],
            "line": CANONICAL_KINDS[kind]["line"],
            "source": "auto-derived from relation kinds in manifest",
        })
    if not legend and default_legend:
        legend = default_legend

    m["entities"] = entities
    m["relations"] = relations
    m["groups"] = groups
    m["legend"] = legend
    m.setdefault("style", {})
    m["style"].setdefault("font", "")
    m["style"].setdefault("canvas", None)     # {"width":..,"height":..}
    return m


def load_manifest(path_or_dict):
    """Load a manifest from a JSON file or accept an already-parsed dict."""
    if isinstance(path_or_dict, dict):
        return normalize_manifest(path_or_dict)
    with open(path_or_dict, "r", encoding="utf-8") as fh:
        return normalize_manifest(json.load(fh))


def extract_manifest_from_svg(svg_path):
    """Read the ER manifest embedded in a figure.svg (<metadata> element)."""
    with open(svg_path, "r", encoding="utf-8") as fh:
        text = fh.read()
    mobj = re.search(r"<metadata[^>]*id=[\"']er-manifest[\"'][^>]*>(.*?)</metadata>",
                     text, flags=re.S)
    if not mobj:
        return None
    raw = mobj.group(1)
    raw = raw.replace("&lt;", "<").replace("&gt;", ">").replace(
        "&quot;", '"').replace("&#34;", '"').replace("&amp;", "&")
    return json.loads(raw)


def persist_manifest(manifest, path):
    """Write a manifest as compact UTF-8 JSON (LF line endings)."""
    body = json.dumps(manifest, ensure_ascii=False, indent=2)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body + "\n")
    return os.path.abspath(path)


def validate_manifest(manifest):
    """Return a list of issue dicts. Hard issues are `level: fail`,
    soft ones `level: warn`. This is the contract check between the
    extraction step (agent) and the drawing step (scripts)."""
    issues = []
    entities = manifest.get("entities") or []
    relations = manifest.get("relations") or []
    groups = manifest.get("groups") or []
    eids = {e["id"] for e in entities}
    fig_type = (manifest.get("figure_type") or "schematic").lower()

    if not entities:
        if fig_type == "chart" and (manifest.get("data") or {}).get(
                "table", {}).get("rows"):
            issues.append({"level": "ok", "check": "entities",
                           "detail": "chart manifest: data table is the "
                                     "source of truth (entities/relations "
                                     "not required)"})
        else:
            issues.append({"level": "fail", "check": "entities", "detail":
                           "manifest contains no entities"})

    for e in entities:
        if not e.get("name"):
            issues.append({"level": "fail", "check": "entity.name",
                           "target": e.get("id"), "detail": "entity has empty name"})
        if not e.get("source"):
            issues.append({"level": "warn", "check": "traceability",
                           "target": e.get("id"), "detail":
                           "entity has no `source` (material reference). Add it "
                           "so the figure element is independently verifiable."})
        elif not e.get("evidence"):
            issues.append({"level": "warn", "check": "traceability",
                           "target": e.get("id"), "detail":
                           "entity has `source` but no `evidence` quote"})

    for r in relations:
        if r.get("from") not in eids:
            issues.append({"level": "fail", "check": "relation.from",
                           "target": r.get("id"),
                           "detail": "relation from=%r not in entity ids" % r.get("from")})
        if r.get("to") not in eids:
            issues.append({"level": "fail", "check": "relation.to",
                           "target": r.get("id"),
                           "detail": "relation to=%r not in entity ids" % r.get("to")})
        if r.get("_unknown_kind"):
            issues.append({"level": "fail", "check": "relation.kind",
                           "target": r.get("id"),
                           "detail": "unknown relation kind %r — map it onto the "
                                     "canonical vocabulary (activation / "
                                     "inhibition / recruitment / process / "
                                     "transcriptional / causal / containment)"
                           % r.get("kind")})
        if r.get("from") == r.get("to"):
            issues.append({"level": "warn", "check": "relation.selfloop",
                           "target": r.get("id"),
                           "detail": "self-loop relation %s — confirm direction "
                                     "is intended" % r.get("id")})
        if not r.get("source"):
            issues.append({"level": "warn", "check": "traceability",
                           "target": r.get("id"),
                           "detail": "relation has no `source` reference"})

    for g in groups:
        for mid in g.get("_unknown_members") or []:
            issues.append({"level": "fail", "check": "group.member",
                           "target": g.get("id"),
                           "detail": "group member %r is not an entity id" % mid})
    return issues


def traceability_score(manifest):
    """Summarize how much of the manifest is source-bound (for result.json)."""
    entities = manifest.get("entities") or []
    relations = manifest.get("relations") or []
    ent_w = sum(1 for e in entities if e.get("source") and e.get("evidence"))
    rel_w = sum(1 for r in relations if r.get("source"))
    return {
        "entities_total": len(entities),
        "entities_with_source_and_evidence": ent_w,
        "relations_total": len(relations),
        "relations_with_source": rel_w,
        "entities_traceable_pct": round(100 * ent_w / len(entities), 1) if entities else 0.0,
        "relations_traceable_pct": round(100 * rel_w / len(relations), 1) if relations else 0.0,
    }


def _first(*vals):
    for v in vals:
        if v not in (None, "", [], {}):
            return v
    return None


def case_to_manifest(case):
    """Best-effort build a manifest from whatever the case.json carries.
    Precedence: case["manifest"] (full object) → case["entities"]/+case
    ["relations"] → empty skeleton."""
    c = case or {}
    inline = c.get("manifest")
    if isinstance(inline, dict) and inline.get("entities"):
        return normalize_manifest(inline)
    entities = c.get("entities") or []
    relations = c.get("relations") or []
    if entities or relations:
        return normalize_manifest({
            "figure_type": c.get("figure_type")
            or (c.get("main_figure") or {}).get("type")
            or ("chart" if c.get("data") else "schematic"),
            "title": _first(c.get("title"), (c.get("task") or {}).get("title"), ""),
            "entities": entities,
            "relations": relations,
            "groups": c.get("groups") or [],
            "legend": c.get("legend") or [],
            "data": c.get("data") or {},
            "style": _first(c.get("style"), {}),
        })
    return normalize_manifest({"figure_type": "schematic",
                               "title": _first(c.get("title"), ""),
                               "entities": [], "relations": []})


# ---------------------------------------------------------------------------
# Small CLI so the manifest helpers can be driven from the shell too.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    m = load_manifest(sys.argv[1])
    issues = validate_manifest(m)
    print(json.dumps({
        "entities": len(m["entities"]),
        "relations": len(m["relations"]),
        "groups": len(m["groups"]),
        "issues": issues,
        "traceability": traceability_score(m),
    }, ensure_ascii=False, indent=2))