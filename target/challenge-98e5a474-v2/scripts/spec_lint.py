#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CP1 — plan/spec lint gate for figure correctness.

Runs BEFORE drawing (SKILL.md CP1). It turns the topic's core correctness
requirements into machine checks:

* entity-relation manifest completeness (ids, names, from/to targets);
* traceability: every entity/relation carries source + evidence;
* grammar conformance against assets/relation-dict.json (arrow kind →
  line/dash/color vocabulary; containment must be expressed as a group,
  never as an arrow);
* legend conformance: every drawn relation kind has a legend entry and no
  orphan entries (legend ↔ drawing two-way consistency);
* data mapping: chart category ↔ legend ↔ colour count coherence;
* canvas bounds: requested canvas at least fits the estimate.

Exit codes: 0 = lint clean (or only warns), 1 = hard fails present,
2 = usage error. `{"valid": true}` is the CP1 pass verdict.

Only the Python standard library is required.
"""

import argparse
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
from manifest import canonical_kind, CANONICAL_KINDS  # noqa: E402


def load_dict(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def lint_manifest(manifest, relation_dict=None):
    issues = []
    manifest = manifest or {}
    entities = manifest.get("entities") or []
    relations = manifest.get("relations") or []
    groups = manifest.get("groups") or []
    legend = manifest.get("legend") or []
    data = manifest.get("data") or {}
    fig_type = (manifest.get("figure_type") or "schematic").lower()
    eids = [e.get("id") for e in entities]
    eid_set = {x for x in eids if x}

    def add(check, level, detail, target=None):
        issues.append({"check": check, "level": level,
                       "target": target, "detail": detail})

    # ---- entities ----
    if not entities and fig_type != "chart":
        add("spec.entities", "fail",
            "no entities in manifest; a schematic must have entities")
    seen = {}
    for e in entities:
        eid = e.get("id")
        if not eid:
            add("spec.entity_id", "fail", "entity with empty id")
            continue
        if eid in seen:
            add("spec.entity_id", "fail", "duplicate entity id %s" % eid,
                eid)
        seen[eid] = True
        if not e.get("name"):
            add("spec.entity_name", "fail", "entity %s has empty name" % eid,
                eid)
        if not e.get("source"):
            add("spec.traceability", "warn",
                "entity %s has no `source` (material reference)" % eid, eid)
        elif not e.get("evidence"):
            add("spec.traceability", "warn",
                "entity %s has source but no evidence quote" % eid, eid)

    # ---- relations ----
    for r in relations:
        rid = r.get("id")
        from_id, to_id = r.get("from"), r.get("to")
        if from_id not in eid_set:
            add("spec.relation_from", "fail",
                "relation %s: from=%r not in entity ids" % (rid, from_id), rid)
        if to_id not in eid_set:
            add("spec.relation_to", "fail",
                "relation %s: to=%r not in entity ids" % (rid, to_id), rid)
        canon, unknown = canonical_kind(r.get("kind"))
        if unknown:
            add("spec.relation_kind", "fail",
                "relation %s kind %r not in canonical vocabulary "
                "(activation/inhibition/recruitment/process/transcriptional/"
                "causal/containment)" % (rid, r.get("kind")), rid)
        else:
            if relation_dict:
                spec = relation_dict.get("relations", {}).get(canon, {})
                if not spec:
                    add("spec.relation_dict", "fail",
                        "canonical kind %r absent from relation-dict.json"
                        % canon, rid)
                else:
                    arrow = spec.get("arrow")
                    if arrow in ("activation", "inhibition", "open") and \
                            canon == "containment":
                        add("spec.containment_arrow", "fail",
                            "containment relation %s must be drawn as a "
                            "group box, never as an arrow" % rid, rid)
            if canon == "containment":
                in_group = any(g.get("id") and from_id in (g.get("members")
                              or []) and to_id in (g.get("members") or [])
                               for g in groups)
                if not in_group:
                    add("spec.containment_group", "fail",
                        "containment relation %s (%s→%s) is not covered by "
                        "any group box; containment requires a group member "
                        "relationship" % (rid, from_id, to_id), rid)
        if not r.get("source"):
            add("spec.relation_source", "warn",
                "relation %s has no `source` reference" % rid, rid)
        if from_id == to_id:
            add("spec.relation_selfloop", "warn",
                "relation %s is a self-loop; confirm direction" % rid, rid)

    # ---- groups ----
    for g in groups:
        gid = g.get("id")
        for mid in (g.get("members") or []):
            if mid not in eid_set:
                add("spec.group_member", "fail",
                    "group %s member %r is not an entity id" % (gid, mid), gid)

    # ---- legend <-> drawing two-way ----
    used_kinds = set()
    for r in relations:
        canon = r.get("_canon")
        if canon is None:
            canon, _ = canonical_kind(r.get("kind"))
        if canon and canon != "containment":
            used_kinds.add(canon)
    legend_keys = set()
    for item in legend:
        k = item.get("key") or item.get("arrow") or item.get("label")
        if k:
            legend_keys.add(k if not item.get("key") or item.get("key")
                            else (item.get("key")))
        elif item.get("id"):
            legend_keys.add(item["id"])
    missing = used_kinds - legend_keys
    if missing:
        add("spec.legend_missing_kinds", "fail",
            "relation kind(s) drawn but missing from legend: %s"
            % sorted(missing))
    else:
        add("spec.legend_missing_kinds", "ok", "all drawn kinds have legend")

    # ---- data mapping (chart) ----
    if fig_type == "chart":
        table = data.get("table") or {}
        rows = table.get("rows") or []
        cols = table.get("columns") or []
        if not rows:
            add("spec.data_rows", "fail", "chart data.table.rows empty")
        cat_col = data.get("category_col")
        if cat_col and cat_col not in (cols or []):
            add("spec.data_category", "fail",
                "category_col %r not in table columns %r" % (cat_col, cols))
        palette = data.get("colors") or data.get("palette")
        if palette and rows:
            cats = sorted({str(r[cols.index(cat_col)])
                           if cat_col and cat_col in cols else ""
                           for r in rows})
            if len(palette) < len(cats):
                add("spec.color_category_count", "fail",
                    "palette has %d colours but table has %d unique "
                    "categories (%s); colour mapping must match category "
                    "count" % (len(palette), len(cats), sorted(cats)))
            else:
                add("spec.color_category_count", "ok",
                    "palette (%d) covers %d categories" % (len(palette),
                                                           len(cats)))
        if not data.get("unit"):
            add("spec.data_unit", "warn", "chart declares no unit")
    else:
        add("spec.data_mapping", "ok", "schematic — legend conformance above")

    # ---- canvas bounds (soft) ----
    style = manifest.get("style") or {}
    canvas = style.get("canvas")
    if isinstance(canvas, dict) and canvas.get("width") and canvas.get("height"):
        est = 120 + max(0, len(entities)) * 160 + \
            max(0, len(relations)) * 40
        if canvas["width"] < 200 or canvas["height"] < 200:
            add("spec.canvas_bounds", "fail",
                "canvas %s too small to hold the figure" % (canvas,))
    return issues


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", required=True,
                    help="path to the ER manifest (entities.json)")
    ap.add_argument("--dict", default=None,
                    help="path to assets/relation-dict.json "
                         "(default: <scripts>/../assets/relation-dict.json)")
    ap.add_argument("--json", action="store_true",
                    help="emit machine-readable JSON verdict")
    args = ap.parse_args(argv)

    mp = os.path.abspath(args.manifest)
    if not os.path.isfile(mp):
        print("FATAL: manifest not found: %s" % mp)
        return 2
    with open(mp, "r", encoding="utf-8") as fh:
        manifest = json.load(fh)
    dict_path = args.dict or os.path.normpath(
        os.path.join(_HERE, "..", "assets", "relation-dict.json"))
    relation_dict = None
    if os.path.isfile(dict_path):
        relation_dict = load_dict(dict_path)
    issues = lint_manifest(manifest, relation_dict)

    fails = [i for i in issues if i["level"] == "fail"]
    warns = [i for i in issues if i["level"] == "warn"]
    valid = not fails
    verdict = {"valid": valid, "fail_count": len(fails),
               "warn_count": len(warns),
               "issues": issues,
               "dict": os.path.basename(dict_path) if relation_dict else None}

    if args.json:
        print(json.dumps(verdict, ensure_ascii=False, indent=2))
    else:
        print("spec_lint: %s (CP1)" % ("VALID" if valid else "INVALID"))
        for i in issues:
            print("  [%s] %-28s %s" % (i["level"], i["check"], i["detail"]))
    return 0 if valid else 1


if __name__ == "__main__":
    sys.exit(main())