# -*- coding: utf-8 -*-
"""Legend & data-encoding audit (v2, new in this package).

A pathway figure is only correct if the legend, the data mapping and the
canvas are internally consistent, and if every encoded value on the canvas is
traceable to a source.  This module machine-checks those rules (L/E series)
both inside main.py (CP3 gate) and standalone.

Check ids (aligned with references/legend-encoding.md §3):
  L01 legend covers used entity types   L05 canvas colors ⊆ legend ∪ ramp
  L02 legend covers used edge types     L06 dash only for weak/uncertain
  L03 data mapping field vs values      L07 evidence widths match canonical
  L04 arrow marker == legend marker     E01 canvas data values traceable
  L05b semantic colors unknown          E02 ramp endpoints present
"""
import os
import json

from model import (EDGE_TYPES, EVIDENCE_WIDTH, data_scale, data_color,
                   load_json)

LAYER_IDS = ["layer-compartment", "layer-edge", "layer-entity", "layer-label",
             "layer-title", "layer-legend", "layer-meta"]


def _check(id_, name, result, detail):
    return {"id": id_, "check": name, "result": result, "detail": detail}


def _svg_tree(svg_path):
    import xml.etree.ElementTree as ET
    tree = ET.parse(svg_path)
    return tree


def run_legend_audit(model, layout=None, svg_path=None, out_path=None):
    """Return list of check dicts.  svg_path optional: color/marker checks
    are skipped when the SVG is not available yet (called before render)."""
    checks = []
    legend = model.get("legend") or {}
    entities = model.get("entities", [])
    edges = model.get("edges", [])
    used_etypes = {e["type"] for e in entities}
    used_rtypes = {r["type"] for r in edges}

    # L01 / L02 legend coverage
    missing_e = used_etypes - set((legend.get("entities") or {}))
    checks.append(_check("L01", "图例覆盖(实体类型)", "fail" if missing_e else "pass",
                         ("图例缺少实体类型: %s" % sorted(missing_e)) if missing_e
                         else "图例覆盖全部在用实体类型"))
    missing_r = used_rtypes - set((legend.get("edges") or {}))
    checks.append(_check("L02", "图例覆盖(边类型)", "fail" if missing_r else "pass",
                         ("图例缺少边类型: %s" % sorted(missing_r)) if missing_r
                         else "图例覆盖全部在用边类型"))

    # L03 data mapping field vs values
    dm = legend.get("data_mapping") or {}
    if dm.get("field"):
        scale = data_scale(model)
        checks.append(_check("L03", "数据映射有数值支撑",
                             "warn" if not scale else "pass",
                             ("映射字段 %s 在实体数据中未找到数值（图将用默认色）" % dm["field"])
                             if not scale
                             else "映射字段 %s: 数值范围 [%s, %s]" % (dm["field"], scale[0], scale[1])))
    else:
        checks.append(_check("L03", "数据映射字段声明", "warn",
                             "未声明 data_mapping.field（图例不含数据映射区）"))

    # E02 ramp endpoints
    if dm.get("field"):
        checks.append(_check("E02", "色带端点声明",
                             "fail" if not (dm.get("low") and dm.get("high")) else "pass",
                             ("data_mapping.low/high 缺失：%s/%s" % (dm.get("low"), dm.get("high")))
                             if not (dm.get("low") and dm.get("high"))
                             else "色带低→高: %s → %s" % (dm.get("low"), dm.get("high"))))

    # L07 evidence width canonical
    ew = legend.get("evidence_width") or {}
    drift = [k for k in EVIDENCE_WIDTH if ew.get(k) not in (None, EVIDENCE_WIDTH[k])]
    checks.append(_check("L07", "证据强度→线宽映射",
                         "warn" if drift else "pass",
                         ("图例线宽与规范不一致: %s" % ", ".join(drift)) if drift
                         else "证据宽度 strong/moderate/weak = 2.8/2.2/1.6 与规范一致"))

    # E01 data values traceable to sources
    untraceable = []
    for e in entities:
        d = e.get("data") if isinstance(e.get("data"), dict) else {}
        if not d:
            continue
        src = e.get("source") or []
        if not src:
            untraceable.append("%s(%s) 无任何 source" % (e["id"], e["name"]))
        else:
            kinds = {s.get("kind") for s in src}
            if kinds and kinds <= {"assumption"}:
                pass  # assumption flows through uncertainty; recorded by T03
    checks.append(_check("E01", "画布数据可溯源",
                         "fail" if any("无任何 source" in u for u in untraceable) else
                         ("warn" if untraceable else "pass"),
                         ("携带数据值但无来源: %s" % "; ".join(untraceable)) if untraceable
                         else "所有数据值均挂接 source（材料行号）"))

    # ---------- SVG dependent checks ----------
    if svg_path and os.path.isfile(svg_path):
        try:
            tree = _svg_tree(svg_path)
        except Exception as ex:
            checks.append(_check("S00", "SVG 可解析", "fail",
                                 "svg 解析失败: %s" % ex))
            tree = None
        if tree is not None:
            ns = "{http://www.w3.org/2000/svg}"
            paths = [p for p in tree.iter(ns + "path")]

            # L04 marker semantics: canvas marker-end must equal the legend
            # marker for the same edge type
            bad_markers = []
            for p in paths:
                mid = p.get("marker-end")
                if not mid:
                    continue
                mid = mid.replace("url(#", "").rstrip(")")
                rtype = p.get("data-type")
                rid = p.get("data-id")
                spec = (legend.get("edges") or {}).get(rtype)
                if not spec:
                    bad_markers.append("%s: type %s 不在图例" % (rid, rtype))
                    continue
                want = "mk-%s-%s" % (spec["marker"], spec["color"].lstrip("#").lower())
                if mid != want:
                    bad_markers.append("%s: marker %s，图例应为 %s" % (rid, mid, want))
            checks.append(_check("L04", "箭头语义=图例声明",
                                 "fail" if bad_markers else "pass",
                                 ("; ".join(bad_markers)) if bad_markers
                                 else "全部边 marker 与图例声明一致"))

            # L05 / L05b canvas colors ⊆ legend ∪ data ramp (semantic elements)
            legend_colors = set()
            for t, sp in (legend.get("entities") or {}).items():
                legend_colors.add(sp.get("fill"))
                legend_colors.add(sp.get("stroke"))
            for t, sp in (legend.get("edges") or {}).items():
                legend_colors.add(sp.get("color"))
            if dm.get("low"):
                legend_colors.add(dm["low"])
            if dm.get("high"):
                legend_colors.add(dm["high"])
            scale = data_scale(model)
            vmin, vmax = (scale[0], scale[1]) if scale else (0.0, 1.0)
            resolved = {data_color({"type": e["type"], "data": e.get("data")},
                                   legend, vmin, vmax)["fill"] for e in entities}
            allowed = legend_colors | resolved
            off = []
            for g in tree.iter(ns + "g"):
                gid = g.get("id") or ""
                if gid.startswith("entity-"):
                    for el in g.iter():
                        if el.tag in (ns + "rect", ns + "circle"):
                            for c in (el.get("fill"), el.get("stroke")):
                                if c and c.startswith("#") and c not in allowed and c not in off:
                                    off.append(c)
            for p in paths:
                if p.get("data-type") is not None:
                    c = p.get("stroke") or ""
                    if c and c.startswith("#") and c not in allowed and c not in off:
                        off.append(c)
            checks.append(_check("L05", "图面颜色⊆图例∪数据映射(节点与边)",
                                 "fail" if off else "pass",
                                 ("节点/边出现未声明颜色: %s" % ", ".join(off)) if off
                                 else "节点与边颜色全部可回溯到图例或数据映射"))

            # L06 dash only for weak/uncertain
            dash_ok = []
            for p in paths:
                rid = p.get("data-id")
                if p.get("data-type") is None:
                    continue
                dashed = bool(p.get("stroke-dasharray"))
                r = next((r for r in edges if r["id"] == rid), None)
                if r is None:
                    continue
                weak_or_uncertain = (r.get("evidence") == "weak" or r.get("uncertain"))
                if dashed and not weak_or_uncertain:
                    dash_ok.append("%s 虚线但 evidence 非 weak/uncertain" % rid)
                if not dashed and weak_or_uncertain and r.get("evidence") == "weak" and not r.get("uncertain"):
                    pass  # weak ⇒ dashed per convention; missing dash is a warn
                    dash_ok.append("%s weak 但未用虚线" % rid)
            checks.append(_check("L06", "虚线语义(仅 weak/uncertain)",
                                 "warn" if dash_ok else "pass",
                                 ("; ".join(dash_ok)) if dash_ok
                                 else "虚线仅用于 weak/间接/uncertain"))

            # layer ids present (feeds G4)
            found_layers = {g.get("id") for g in tree.iter(ns + "g")
                            if (g.get("id") or "").startswith("layer-")}
            missing_layers = [lk for lk in LAYER_IDS if lk not in found_layers]
            checks.append(_check("L08", "图层命名(layer-*)",
                                 "fail" if missing_layers else "pass",
                                 ("缺少图层: %s" % ", ".join(missing_layers)) if missing_layers
                                 else "%d 个规范图层齐全" % len(LAYER_IDS)))
    else:
        checks.append(_check("S01", "SVG 存在(供图例审计)", "fail" if svg_path else "warn",
                             "未找到 SVG，跳过画布侧一致性检查" if svg_path
                             else "渲染前调用，跳过画布侧检查"))

    if out_path:
        dump = {"checks": checks,
                "counts": {"entities": len(entities), "edges": len(edges)},
                "failures": [c for c in checks if c["result"] == "fail"],
                "warnings": [c for c in checks if c["result"] == "warn"]}
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(dump, fh, ensure_ascii=False, indent=2)
    return checks


if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from layout import compute_layout
    from model import normalize_model
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    model = normalize_model(load_json(os.path.join(out, "model.json")))
    layout = compute_layout(model)
    checks = run_legend_audit(
        model, layout,
        svg_path=os.path.join(out, "diagram.svg") if os.path.isfile(os.path.join(out, "diagram.svg")) else None,
        out_path=os.path.join(out, "legend_audit.json"))
    print(json.dumps(checks, ensure_ascii=False, indent=2))