#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Source-preserving edit of an existing figure.

A generated figure.svg embeds its ER manifest in
`<metadata id="er-manifest">`. A later editing task can therefore:

1. read the current source (existing figure.svg) instead of re-extracting
   everything from the materials,
2. apply a small, explicit `edits` list (from task.md / case.json),
3. keep every unchanged element byte-identical in spirit — only the
   affected nodes/edges/groups are re-laid-out or re-rendered,
4. produce a change record (before → after) that goes into result.json.

An edit list item is one of:

    {"action": "add_entity",      "entity": {id,name,type,source,evidence,...},
                                  "relation": {from,to,kind,source,evidence}?}
    {"action": "remove_entity",   "entity_id": "E3"}
    {"action": "remove_relation", "relation_id": "R2"}
    {"action": "rename",          "entity_id": "E1", "to": "IL-6R"}
    {"action": "relabel",         "relation_id": "R1", "to": "inhibits"}
    {"action": "flip_direction",  "relation_id": "R1"}   # swap from/to
    {"action": "change_kind",     "relation_id": "R1", "to": "inhibition"}
    {"action": "add_group",       "group": {id,label,members,source,evidence}}
    {"action": "update_value",    "entity_id"/"relation_id", "field", "value"}
    {"action": "note",            "text": "..."}          # record-only

Every edit records {action, target, before, after, reason, time}.
"""

import json
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from manifest import (normalize_manifest, load_manifest,
                      extract_manifest_from_svg)


def apply_edits(manifest, edits, origin="case.json"):
    """Return (new_manifest, change_records, issues)."""
    m = normalize_manifest(dict(manifest))
    records = []
    issues = []
    by_eid = {e["id"]: e for e in m["entities"]}
    by_rid = {r["id"]: r for r in m["relations"]}
    groups = m.get("groups") or []

    for num, ed in enumerate(edits or []):
        if not isinstance(ed, dict):
            issues.append({"check": "edit.form", "level": "fail",
                           "detail": "edit #%d is not an object" % num})
            continue
        action = ed.get("action") or ""
        ts = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        reason = ed.get("reason") or ed.get("note") or "from %s" % origin

        if action == "add_entity":
            ent = dict(ed.get("entity") or {})
            if not ent.get("id"):
                ent["id"] = "E%d" % (len(m["entities"]) + 1)
            ent.setdefault("name", ent.get("id"))
            ent.setdefault("type", "entity")
            ent.setdefault("source", "")
            ent.setdefault("evidence", "")
            if ent["id"] in by_eid:
                issues.append({"check": "edit.add_entity", "level": "fail",
                               "detail": "entity %s already exists" % ent["id"]})
                continue
            m["entities"].append(ent)
            by_eid[ent["id"]] = ent
            records.append({"action": "add_entity", "target": ent["id"],
                            "before": None,
                            "after": {"name": ent.get("name"),
                                      "type": ent.get("type")},
                            "reason": reason, "time": ts})
            rel = ed.get("relation")
            if isinstance(rel, dict) and rel.get("from") and rel.get("to"):
                rid = rel.get("id") or "R%d" % (len(m["relations"]) + 1)
                rel = dict(rel)
                rel.setdefault("id", rid)
                rel.setdefault("label", "")
                rel.setdefault("source", "")
                rel.setdefault("evidence", "")
                m["relations"].append(rel)
                by_rid[rel["id"]] = rel
                records.append({"action": "add_relation", "target": rel["id"],
                                "before": None,
                                "after": {"from": rel["from"], "to": rel["to"],
                                          "kind": rel.get("kind")},
                                "reason": reason, "time": ts})

        elif action == "remove_entity":
            eid = ed.get("entity_id")
            if eid not in by_eid:
                issues.append({"check": "edit.remove_entity", "level": "fail",
                               "detail": "unknown entity %s" % eid})
                continue
            removed = m["entities"][:]
            m["entities"] = [e for e in m["entities"] if e["id"] != eid]
            # drop relations touching the entity
            kept = []
            for r in m["relations"]:
                if r["from"] == eid or r["to"] == eid:
                    records.append({"action": "cascade_remove_relation",
                                    "target": r["id"],
                                    "before": {"from": r["from"],
                                               "to": r["to"]},
                                    "after": None, "reason": reason,
                                    "time": ts})
                else:
                    kept.append(r)
            m["relations"] = kept
            m["groups"] = [g for g in groups
                           if eid not in (g.get("members") or [])]
            records.append({"action": "remove_entity", "target": eid,
                            "before": {"name": removed[0]["name"]
                                       if removed else None}, "after": None,
                            "reason": reason, "time": ts})

        elif action == "remove_relation":
            rid = ed.get("relation_id")
            if rid not in by_rid:
                issues.append({"check": "edit.remove_relation", "level": "fail",
                               "detail": "unknown relation %s" % rid})
                continue
            r = by_rid[rid]
            m["relations"] = [x for x in m["relations"] if x["id"] != rid]
            records.append({"action": "remove_relation", "target": rid,
                            "before": {"from": r["from"], "to": r["to"],
                                       "kind": r["kind"]}, "after": None,
                            "reason": reason, "time": ts})

        elif action == "rename":
            eid = ed.get("entity_id")
            if eid not in by_eid:
                issues.append({"check": "edit.rename", "level": "fail",
                               "detail": "unknown entity %s" % eid})
                continue
            old = by_eid[eid]["name"]
            by_eid[eid]["name"] = ed.get("to") or old
            records.append({"action": "rename", "target": eid,
                            "before": old, "after": by_eid[eid]["name"],
                            "reason": reason, "time": ts})

        elif action == "relabel":
            rid = ed.get("relation_id")
            if rid not in by_rid:
                issues.append({"check": "edit.relabel", "level": "fail",
                               "detail": "unknown relation %s" % rid})
                continue
            old = by_rid[rid]["label"]
            by_rid[rid]["label"] = ed.get("to") or old
            records.append({"action": "relabel", "target": rid,
                            "before": old, "after": by_rid[rid]["label"],
                            "reason": reason, "time": ts})

        elif action == "flip_direction":
            rid = ed.get("relation_id")
            if rid not in by_rid:
                issues.append({"check": "edit.flip", "level": "fail",
                               "detail": "unknown relation %s" % rid})
                continue
            r = by_rid[rid]
            old_from, old_to = r["from"], r["to"]
            r["from"], r["to"] = r["to"], r["from"]
            records.append({"action": "flip_direction", "target": rid,
                            "before": "%s→%s" % (old_from, old_to),
                            "after": "%s→%s" % (r["from"], r["to"]),
                            "reason": reason, "time": ts})

        elif action == "change_kind":
            rid = ed.get("relation_id")
            if rid not in by_rid:
                issues.append({"check": "edit.change_kind", "level": "fail",
                               "detail": "unknown relation %s" % rid})
                continue
            r = by_rid[rid]
            old = r.get("kind")
            r["kind"] = ed.get("to") or old
            records.append({"action": "change_kind", "target": rid,
                            "before": old, "after": r["kind"],
                            "reason": reason, "time": ts})

        elif action == "add_group":
            g = dict(ed.get("group") or {})
            if not g.get("id"):
                g["id"] = "G%d" % (len(groups) + 1)
            g.setdefault("members", [])
            g.setdefault("label", "")
            g.setdefault("source", "")
            g.setdefault("evidence", "")
            groups = [x for x in groups if x.get("id") != g["id"]]
            groups.append(g)
            records.append({"action": "add_group", "target": g["id"],
                            "before": None,
                            "after": {"label": g.get("label"),
                                      "members": g.get("members")},
                            "reason": reason, "time": ts})

        elif action == "update_value":
            eid = ed.get("entity_id")
            rid = ed.get("relation_id")
            field = ed.get("field")
            val = ed.get("value")
            if eid and eid in by_eid and field:
                old = by_eid[eid].get(field)
                by_eid[eid][field] = val
                records.append({"action": "update_value", "target": eid,
                                "field": field, "before": old, "after": val,
                                "reason": reason, "time": ts})
            elif rid and rid in by_rid and field:
                old = by_rid[rid].get(field)
                by_rid[rid][field] = val
                records.append({"action": "update_value", "target": rid,
                                "field": field, "before": old, "after": val,
                                "reason": reason, "time": ts})
            else:
                issues.append({"check": "edit.update_value", "level": "fail",
                               "detail": "update_value needs existing "
                                         "entity_id/relation_id + field"})

        elif action == "note":
            records.append({"action": "note", "target": None,
                            "before": None, "after": ed.get("text", ""),
                            "reason": reason, "time": ts})

        else:
            issues.append({"check": "edit.unknown_action", "level": "fail",
                           "detail": "unknown edit action %r" % action})

    m["groups"] = groups
    return normalize_manifest(m), records, issues


def edit_from_svg(svg_path, edits, origin="svg"):
    """Extract the embedded manifest from an existing figure.svg, apply the
    edit list, and return (new_manifest, change_records, issues)."""
    if not os.path.isfile(svg_path):
        raise FileNotFoundError("edit source svg not found: %s" % svg_path)
    m = extract_manifest_from_svg(svg_path)
    if m is None:
        raise ValueError("no embedded ER manifest in %s — cannot do a "
                         "source-preserving edit (regenerate the figure with "
                         "this skill first)" % svg_path)
    return apply_edits(m, edits, origin)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: python edit.py <figure.svg> <edits.json>")
        sys.exit(2)
    with open(sys.argv[2], "r", encoding="utf-8") as fh:
        edits = json.load(fh)
    m, recs, issues = edit_from_svg(sys.argv[1], edits)
    print(json.dumps({"entities": len(m["entities"]),
                      "relations": len(m["relations"]),
                      "change_records": recs, "issues": issues},
                     ensure_ascii=False, indent=2))