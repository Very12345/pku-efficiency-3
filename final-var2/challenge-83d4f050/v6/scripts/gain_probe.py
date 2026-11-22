# -*- coding: utf-8 -*-
"""gain_probe.py — 与绘图实现无关的独立度量器（对照实验的"同一把尺子"）。

为什么独立
----------
对照实验（`references/GAIN-PROTOCOL.md`）要对**两个条件**给出同一组可测指标：
条件 A（`scripts/baseline_emulator.py` 复现的基础形态）与条件 B（本 Skill 的产物）。
若度量直接调用本包自己的审计器（`topology.py` / `legend_audit.py`），
就变成"用被测者自己的尺子量被测者"。因此本脚本：

  1. **不 import 本包任何模块**（纯标准库，只读产物目录）；
  2. 指标定义写死在 `references/GAIN-PROTOCOL.md` §2，两侧**逐项同法计算**；
  3. 输出一份可直接对比的 JSON，缺项计 0（不是跳过），避免"没产物反而好看"。

它度量的是**结构性与可核验性**（分层、溯源、语义标签、图例声明、契约信封、审计产物），
不评判图面美观度——美观度由人/模型评判，本脚本不承诺。

用法
----
  python3 scripts/gain_probe.py --dir <cond_out> [--material <材料 md>] [--case <case.json>]
  python3 scripts/gain_probe.py --compare <dirA> <dirB> --material <材料 md> \
      [--label-a 基础条件 --label-b 加载Skill]

退出码：0 = 度量完成（**不代表产物合格**）；2 = 输入不合法。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

# 契约信封必备字段（独立抄自 references/OUTPUT_CONTRACT.md §2，不 import 本包模块）
ENVELOPE_KEYS = ["case_id", "title", "status", "contract_version", "skill", "deliverables",
                 "scientific_content", "evidence_sources", "data_mapping", "extraction",
                 "export_checks", "topology", "legend_audit", "self_check", "gates",
                 "uncertainty", "change_records", "files", "provenance"]
TAG_RE = re.compile(r"<(path|line|rect|circle|ellipse|polygon|text)\b([^>]*)>")
ATTR_RE = re.compile(r'([A-Za-z_:][-A-Za-z0-9_:.]*)\s*=\s*"([^"]*)"')
LAYER_RE = re.compile(r'<g id="layer-([A-Za-z0-9_-]+)">')


def read_text(path):
    with open(path, "rb") as fh:
        return fh.read().decode("utf-8", "replace")


def walk_files(root):
    out = []
    for dirpath, dirnames, names in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for n in names:
            out.append(os.path.join(dirpath, n))
    return sorted(out)


def svg_sections(text):
    """按顺序切出 layer-* 组的内容（顶层顺序切片，嵌套 </g> 不影响）。"""
    hits = [(m.start(), m.group(1)) for m in LAYER_RE.finditer(text)]
    sec = {}
    for i, (pos, name) in enumerate(hits):
        end = hits[i + 1][0] if i + 1 < len(hits) else len(text)
        sec[name] = sec.get(name, "") + text[pos:end]
    return sec


def tags(section):
    for m in TAG_RE.finditer(section or ""):
        yield m.group(1), dict(ATTR_RE.findall(m.group(2)))


def edgestyle(a):
    """边的可视样式指纹：箭头 + 虚线 + 描边色（两侧同法计算）。"""
    marker = a.get("marker-end") or a.get("marker") or ""
    return (bool(marker), "dash" if a.get("stroke-dasharray") else "solid",
            (a.get("stroke") or "").upper())


def parse_material_entities(path):
    names = []
    for raw in read_text(path).splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        head = cells[0]
        if not head or head.startswith("---") or head in ("名称", "name", "Name"):
            continue
        if head not in names:
            names.append(head)
    return names


def probe(dirpath, material=None, case=None, label="cond"):
    if not os.path.isdir(dirpath):
        return {"error": "not a directory: %s" % dirpath}
    res = {"label": label, "dir": dirpath}
    files = walk_files(dirpath)
    rel = [os.path.relpath(p, dirpath).replace("\\", "/") for p in files]
    ext = {}
    for r in rel:
        e = os.path.splitext(r)[1].lower()
        ext[e] = ext.get(e, 0) + 1
    res["files"] = {"count": len(rel), "by_ext": ext, "names": rel[:40]}

    svg_paths = [p for p in files if p.lower().endswith(".svg")]
    svg_text = read_text(svg_paths[0]) if svg_paths else ""
    # <defs> 里的箭头 marker 也是 <path>，必须剔除，否则会被误计成一条边
    svg_text = re.sub(r"<defs>.*?</defs>", "", svg_text, flags=re.S)
    sec = svg_sections(svg_text)
    canvas_edges_sec = sec.get("edge", svg_text if not sec else "")
    canvas_ent_sec = sec.get("entity", svg_text if not sec else "")

    edge_tags = list(tags(canvas_edges_sec))
    edges = [(t, a) for t, a in edge_tags if t in ("path", "line", "polygon")]
    sem = [a.get("data-type") for _, a in edges if a.get("data-type")]
    styles = set(edgestyle(a) for _, a in edges)
    legend_sec = sec.get("legend", "")
    legend_arrow_styles = set()
    legend_swatches = 0
    for t, a in tags(legend_sec):
        # 图例里的"声明线"：不论有无箭头端点都算一条声明（binding 类本就无箭头）
        if t in ("line", "path") and a.get("stroke"):
            legend_arrow_styles.add((bool(a.get("marker-end") or a.get("marker")),
                                     (a.get("stroke") or "").upper()))
        if t in ("rect", "circle", "ellipse") and a.get("fill"):
            legend_swatches += 1
    declared = 0
    for _, a in edges:
        if (bool(a.get("marker-end") or a.get("marker")),
                (a.get("stroke") or "").upper()) in legend_arrow_styles:
            declared += 1

    res["editable_source"] = {
        "svg_files": len(svg_paths),
        "named_groups": len(re.findall(r'<g\s+id="', svg_text)),
        "layer_groups": len(sec),
        "layer_names": sorted(sec.keys()),
    }
    res["provenance"] = {
        "data_id": svg_text.count("data-id="),
        "data_type": svg_text.count("data-type="),
        "data_source": svg_text.count("data-source="),
        "data_from_to": svg_text.count("data-from=") + svg_text.count("data-to="),
        "entities_with_provenance": sum(1 for t, a in tags(canvas_ent_sec) if a.get("data-source")),
    }
    res["semantics"] = {
        "canvas_edges": len(edges),
        "edges_with_semantic_tag": len(sem),
        "distinct_semantic_tags": len(set(sem)),
        "distinct_visual_styles": len(styles),
        "edges_declared_in_legend": declared,
        "edges_undeclared_in_legend": len(edges) - declared,
    }
    res["legend"] = {
        "legend_group": bool(legend_sec),
        "legend_arrow_styles": len(legend_arrow_styles),
        "legend_swatches": legend_swatches,
        "has_data_ramp": ("ramp" in legend_sec) if legend_sec else False,
    }
    res["exports"] = {"png": any(p.lower().endswith(".png") for p in files),
                      "pdf": any(p.lower().endswith(".pdf") for p in files),
                      "json": sorted(os.path.basename(p) for p in files
                                     if p.lower().endswith(".json"))}

    if material and os.path.isfile(material):
        names = parse_material_entities(material)
        blob = "\n".join(read_text(p) for p in files
                         if os.path.splitext(p)[1].lower() in (".svg", ".json", ".md", ".txt"))
        hit = [n for n in names if n in blob]
        res["coverage"] = {"material_entities": len(names), "present_in_artifacts": len(hit),
                           "ratio": round(len(hit) / len(names), 4) if names else 0.0,
                           "missing": [n for n in names if n not in hit]}

    rp = os.path.join(dirpath, "result.json")
    env = {"result_json": os.path.isfile(rp)}
    if env["result_json"]:
        try:
            data = json.loads(read_text(rp))
        except ValueError as exc:
            data = None
            env["parse_error"] = str(exc)[:120]
        if isinstance(data, dict):
            present = [k for k in ENVELOPE_KEYS if k in data]
            nulls = [k for k, v in data.items() if v is None]
            gates = data.get("gates") or {}
            gp = sum(1 for v in gates.values() if isinstance(v, dict) and v.get("pass"))
            env.update({"envelope_keys_present": len(present),
                        "envelope_keys_total": len(ENVELOPE_KEYS),
                        "missing_envelope_keys": [k for k in ENVELOPE_KEYS if k not in data],
                        "top_level_nulls": len(nulls), "null_keys": nulls,
                        "status": data.get("status"),
                        "gates_pass": gp, "gates_total": len(gates) or 8,
                        "entities": ((data.get("scientific_content") or {}).get("counts") or {}).get("entities"),
                        "edges": ((data.get("scientific_content") or {}).get("counts") or {}).get("edges")})
            if case and os.path.isfile(case):
                oc = (json.loads(read_text(case)).get("output_contract") or {})
                env["output_contract_fields"] = len(oc)
                env["output_contract_echoed"] = sum(1 for k in oc if k in data)
        else:
            env.setdefault("parse_error", "not a JSON object")
    res["contract"] = env
    base = [os.path.basename(p) for p in files]
    res["audits"] = {"topology.json": "topology.json" in base,
                     "legend_audit.json": "legend_audit.json" in base}
    return res


def score_row(r):
    """把指标压成 0–1 的可比标量（定义见 GAIN-PROTOCOL §2.4；缺项计 0）。"""
    s, e = r.get("semantics", {}), r.get("editable_source", {})
    p, L = r.get("provenance", {}), r.get("legend", {})
    c = r.get("contract", {})
    ce = s.get("canvas_edges") or 0
    return {
        "A1_layer_score": round(min(e.get("layer_groups", 0) / 7.0, 1.0), 4),
        "A2_provenance_ratio": round(min(p.get("data_source", 0) / float(ce or 1), 1.0), 4),
        "A3_semantic_tag_ratio": round((s.get("edges_with_semantic_tag", 0) / float(ce)) if ce else 0.0, 4),
        "A4_legend_declared_ratio": round((s.get("edges_declared_in_legend", 0) / float(ce)) if ce else 0.0, 4),
        "A5_contract_ratio": round(c.get("envelope_keys_present", 0) / float(c.get("envelope_keys_total", 19)), 4),
        "A6_audit_artifacts": round((int(r.get("audits", {}).get("topology.json", False))
                                     + int(r.get("audits", {}).get("legend_audit.json", False))) / 2.0, 4),
        "A7_export_ratio": round((int(r.get("exports", {}).get("png", False))
                                  + int(r.get("exports", {}).get("pdf", False))) / 2.0, 4),
        "A8_coverage_ratio": r.get("coverage", {}).get("ratio", 0.0),
        "legend_group": bool(L.get("legend_group")),
    }


def print_row(r, score):
    print("== %s ==" % r.get("label"))
    print("   files=%d  svg=%d  layers=%d  edges=%d  semantic_tags=%d  legend_declared=%d/%d"
          % (r["files"]["count"], r["editable_source"]["svg_files"],
             r["editable_source"]["layer_groups"], r["semantics"]["canvas_edges"],
             r["semantics"]["distinct_semantic_tags"],
             r["semantics"]["edges_declared_in_legend"], r["semantics"]["canvas_edges"]))
    print("   data_source=%d  contract_keys=%s/%s  status=%s  gates=%s/%s  png=%s pdf=%s  coverage=%s"
          % (r["provenance"]["data_source"],
             r["contract"].get("envelope_keys_present", 0), r["contract"].get("envelope_keys_total", 19),
             r["contract"].get("status"), r["contract"].get("gates_pass", 0),
             r["contract"].get("gates_total", 8), r["exports"]["png"], r["exports"]["pdf"],
             r.get("coverage", {}).get("ratio")))
    print("   score: " + "  ".join("%s=%.4f" % (k, v) for k, v in score.items() if k != "legend_group"))


def main(argv=None):
    ap = argparse.ArgumentParser(description="对照实验独立度量器（不依赖本包模块）")
    ap.add_argument("--dir", help="单个条件产物目录")
    ap.add_argument("--compare", nargs=2, metavar=("DIR_A", "DIR_B"), help="同时度量两个条件")
    ap.add_argument("--material", help="两侧共用的材料文件（用于实体名覆盖度量）")
    ap.add_argument("--case", help="case.json（用于 output_contract 回显度量）")
    ap.add_argument("--label", default="cond")
    ap.add_argument("--label-a", default="A-baseline")
    ap.add_argument("--label-b", default="B-skill")
    ap.add_argument("--json", action="store_true", help="额外打印机器可读 JSON")
    args = ap.parse_args(argv)

    if args.compare:
        a = probe(args.compare[0], args.material, args.case, args.label_a)
        b = probe(args.compare[1], args.material, args.case, args.label_b)
        for r in (a, b):
            if "error" in r:
                print("gain_probe|error|%s" % r["error"])
                return 2
        sa, sb = score_row(a), score_row(b)
        print_row(a, sa)
        print_row(b, sb)
        print("-- 差值 (B - A) --")
        for k in sa:
            if k == "legend_group":
                continue
            print("   %-24s %+.4f" % (k, sb[k] - sa[k]))
        out = {"a": a, "b": b, "score_a": sa, "score_b": sb}
    else:
        if not args.dir:
            print("gain_probe|error|--dir or --compare is required")
            return 2
        r = probe(args.dir, args.material, args.case, args.label)
        if "error" in r:
            print("gain_probe|error|%s" % r["error"])
            return 2
        s = score_row(r)
        print_row(r, s)
        out = {"cond": r, "score": s}
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
