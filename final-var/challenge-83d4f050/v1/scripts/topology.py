# -*- coding: utf-8 -*-
"""Topology lint for pathway diagrams (v2, new in this package).

A mechanism figure is a *topological claim*: every arrow has a direction, every
receptor sits on the membrane, the nucleus is inside the cytoplasm band,
feedback loops go back upstream.  This module turns those rules into machine
checks (P-series) that run both inside main.py (CP3 gate) and standalone.

Check ids (aligned with references/mechanism-spec.md §6):
  P01 ids unique          P05 duplicate edges
  P02 edge endpoints      P06 self loop
  P03 direction rule      P07 unrecognized feedback (upward, not marked)
  P04 gene/protein clash  P08 unknown compartment
"""
import os

from model import COMPARTMENT_ALIASES, load_json

# compartments that may legitimately be drawn inside each other
NUCLEUS_IN_CYTOPLASM = True


def _check(id_, name, result, detail):
    return {"id": id_, "check": name, "result": result, "detail": detail}


def run_topology_checks(model, layout=None, out_path=None):
    """Return list of check dicts {id, check, result: pass|warn|fail, detail}.

    layout may be omitted; when provided it carries rank_of / compartments
    that were actually used by the renderer.
    """
    checks = []
    entities = model.get("entities", [])
    edges = model.get("edges", [])
    ent_ids = [e["id"] for e in entities]
    by_id = {e["id"]: e for e in entities}

    # P01 id uniqueness
    dup = [i for i in ent_ids if ent_ids.count(i) > 1]
    checks.append(_check("P01", "实体 id 唯一", "fail" if dup else "pass",
                         ("重复实体 id: %s" % sorted(set(dup))) if dup
                         else "%d 个实体 id 唯一" % len(entities)))

    # P02 edge endpoints exist
    bad = [r["id"] for r in edges if r["from"] not in by_id or r["to"] not in by_id]
    checks.append(_check("P02", "边端点存在", "fail" if bad else "pass",
                         ("端点缺失的边: %s" % ", ".join(bad)) if bad
                         else "%d 条边端点都存在" % len(edges)))

    # P03 direction rule: non-feedback edges should point downstream
    # (rank increase or same-compartment). Upward non-feedback edges are
    # allowed only with an explicit note (retrograde signalling, translocation
    # artefacts) — checked as warn so the agent must explain them.
    rank_of = {}
    if layout:
        rank_of = layout.get("rank_of") or {}
    else:
        comps = {}
        for e in entities:
            c = e.get("compartment") or "cytoplasm"
            if c not in comps:
                comps[c] = len(comps)
        rank_of = {c: comps[c] for c in comps}
    upward = []
    for r in edges:
        if r.get("feedback"):
            continue
        rs = rank_of.get(by_id.get(r["from"], {}).get("compartment", ""), 9)
        rd = rank_of.get(by_id.get(r["to"], {}).get("compartment", ""), 9)
        if rd < rs:
            upward.append("%s(%s→%s)" % (r["id"], r["from"], r["to"]))
    checks.append(_check("P03", "通路方向(非反馈边上游→下游)",
                         "warn" if upward else "pass",
                         ("非反馈边逆流: %s（须在 uncertainty 或边 note 中说明缘由）" % ", ".join(upward))
                         if upward else "全部非反馈边符合区室上→下流向"))

    # P04 gene vs protein same-name clash
    name_groups = {}
    for e in entities:
        name_groups.setdefault(e["name"], set()).add(e["type"])
    clash = [n for n, ts in name_groups.items() if len(ts) > 1 and "gene" in ts]
    checks.append(_check("P04", "同名基因/蛋白消歧",
                         "warn" if clash else "pass",
                         ("同名但类型不同的实体（须拆分为不同实体并在 note 说明依据）: %s" % ", ".join(clash))
                         if clash else "无同名基因/蛋白混用"))
    # entity name repeats across compartments with the same type (e.g. ERK in
    # cytoplasm and nucleus) must carry an explanatory note
    dup_names = [n for n, es in name_groups.items() if len(es) > 1]
    uncommented = []
    for n in dup_names:
        for e in [e for e in entities if e["name"] == n]:
            if not e.get("note") and not e.get("uncertain"):
                uncommented.append(e["id"])
    checks.append(_check("P04b", "同名实体须备注去向",
                         "warn" if uncommented else "pass",
                         ("同名实体缺说明 note: %s" % ", ".join(uncommented))
                         if uncommented else "同名实体均有 note 说明"))

    # P05 duplicate edges (same from/to/type)
    seen = {}
    for r in edges:
        key = (r["from"], r["to"], r["type"])
        seen.setdefault(key, []).append(r["id"])
    dup_edges = ["%s→%s[%s]: %s" % (k[0], k[1], k[2], ",".join(v))
                 for k, v in seen.items() if len(v) > 1]
    checks.append(_check("P05", "重复边检测", "warn" if dup_edges else "pass",
                         ("同一 from/to/type 出现多条: %s（建议合并或加 subtype 区分）" % "; ".join(dup_edges))
                         if dup_edges else "无重复边"))

    # P06 self loop
    self_loops = [r["id"] for r in edges if r["from"] == r["to"] and not r.get("feedback")]
    checks.append(_check("P06", "自环检测", "fail" if self_loops else "pass",
                         ("存在自环（非反馈）: %s" % ", ".join(self_loops)) if self_loops
                         else "无非反馈自环"))

    # P07 upward edges not marked as feedback (likely missing feedback flag)
    missing_fb = []
    for r in edges:
        if r.get("feedback"):
            continue
        rs = rank_of.get(by_id.get(r["from"], {}).get("compartment", ""), 9)
        rd = rank_of.get(by_id.get(r["to"], {}).get("compartment", ""), 9)
        if rd < rs and r.get("evidence") != "weak":
            missing_fb.append(r["id"])
    checks.append(_check("P07", "疑似反馈环未标注",
                         "warn" if missing_fb else "pass",
                         ("逆流边未标 feedback=true（如确为反馈/回流请补标）: %s" % ", ".join(missing_fb))
                         if missing_fb else "无未标注的逆流回流边"))

    # P08 compartment vocabulary
    unknown = []
    known = set(COMPARTMENT_ALIASES.values())
    for e in entities:
        c = e.get("compartment") or "cytoplasm"
        if c not in known:
            unknown.append("%s(%s)" % (e["id"], c))
    checks.append(_check("P08", "区室词表", "warn" if unknown else "pass",
                         ("未识别区室: %s（按通用区室绘制，请核对拼写）" % ", ".join(unknown))
                         if unknown else "区室均在词表内"))

    if out_path:
        dump = {"checks": checks,
                "counts": {"entities": len(entities), "edges": len(edges)},
                "failures": [c for c in checks if c["result"] == "fail"],
                "warnings": [c for c in checks if c["result"] == "warn"]}
        _dump_json(dump, out_path)
    return checks


def _dump_json(obj, path):
    import json
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)


def run_from_outdir(out_dir):
    """Standalone entry: audit the persisted model in an output directory."""
    import sys
    try:
        from layout import compute_layout
        from model import normalize_model
    except ImportError:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from layout import compute_layout
        from model import normalize_model
    model = normalize_model(load_json(os.path.join(out_dir, "model.json")))
    layout = compute_layout(model)
    return run_topology_checks(model, layout, os.path.join(out_dir, "topology.json"))


if __name__ == "__main__":
    import sys
    import json
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    if len(sys.argv) > 1:
        checks = run_from_outdir(sys.argv[1])
    else:
        checks = []
    print(json.dumps(checks, ensure_ascii=False, indent=2))