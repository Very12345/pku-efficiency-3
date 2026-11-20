# -*- coding: utf-8 -*-
"""Independent verification for the produced figure & result.

Every check returns {"id", "check", "result": pass|warn|fail, "detail"}.
The pipeline treats any 'fail' as a blocking condition (status downgraded to
partial/failed) and requires every 'warn' to be echoed in result.json
uncertainty / self_check so nothing is silently papered over.
"""
import json, os
import xml.etree.ElementTree as ET

from model import NODE_TYPES, EDGE_TYPES, EVIDENCE_WIDTH, data_color, data_scale

SVG_NS = "{http://www.w3.org/2000/svg}"


def run_result_checks(result_path):
    """Post-write checks on result.json (file exists, parses, contract keys)."""
    checks = []

    def add(cid, name, result, detail):
        checks.append({"id": cid, "check": name, "result": result, "detail": detail})

    if not (isinstance(result_path, str) and os.path.isfile(result_path)):
        add("F01_result_json", "result.json 存在且非空", "fail", "缺失: %s" % result_path)
        return {"passed": False, "checks": checks, "failures": [c for c in checks if c["result"] == "fail"],
                "warnings": [c for c in checks if c["result"] == "warn"]}
    sz = os.path.getsize(result_path)
    add("F01_result_json", "result.json 存在且非空", "pass", "%s (%d bytes)" % (result_path, sz))
    try:
        with open(result_path, encoding="utf-8") as fh:
            rj = json.load(fh)
    except Exception as ex:
        add("F03_contract", "result.json 可解析", "fail", str(ex))
        return {"passed": False, "checks": checks, "failures": [c for c in checks if c["result"] == "fail"],
                "warnings": [c for c in checks if c["result"] == "warn"]}
    need = ["case_id", "status", "deliverables", "scientific_content",
            "evidence_sources", "uncertainty", "change_records", "export_checks",
            "self_check"]
    miss = [k for k in need if k not in rj]
    add("F03_contract", "result.json 契约字段完整", "fail" if miss else "pass",
        ("缺字段: %s" % miss) if miss else "契约字段齐全 (contract %s)" % rj.get("contract_version"))
    failed = [c for c in checks if c["result"] == "fail"]
    return {"passed": not failed, "checks": checks, "failures": failed,
            "warnings": [c for c in checks if c["result"] == "warn"]}


def _svg_elems(tree, tag):
    return [e for e in tree.iter() if e.tag == SVG_NS + tag]


def run_checks(model, layout, out_files, case_info=None):
    """out_files: dict with keys like result_json, svg, png, pdf, model_json
    (relative names) and abs paths."""
    checks = []

    def add(cid, name, result, detail):
        checks.append({"id": cid, "check": name, "result": result, "detail": detail})

    # --- model integrity ----------------------------------------------------
    ids = [e["id"] for e in model["entities"]]
    if len(ids) != len(set(ids)):
        add("M01", "实体 id 唯一", "fail", "存在重复实体 id")
    else:
        add("M01", "实体 id 唯一", "pass", "%d 个实体" % len(ids))
    ent_ids = set(ids)
    bad = [r["id"] for r in model["edges"] if r["from"] not in ent_ids or r["to"] not in ent_ids]
    add("M02", "边端点存在性", "fail" if bad else "pass",
        ("端点为空的边: %s" % ", ".join(bad)) if bad else "%d 条边端点都存在" % len(model["edges"]))
    no_name = [e["id"] for e in model["entities"] if not e["name"]]
    add("M03", "实体命名", "fail" if no_name else "pass",
        ("缺名称: %s" % no_name) if no_name else "全部实体有名称")

    # --- source traceability -------------------------------------------------
    no_src_e = [e["id"] for e in model["entities"] if not e.get("source")]
    add("T01", "实体来源标注", "fail" if no_src_e else "pass",
        ("无来源实体: %s" % ", ".join(no_src_e)) if no_src_e
        else "全部实体携带 source（材料行号/出处）")
    no_src_r = [r["id"] for r in model["edges"] if not r.get("source")]
    add("T02", "边来源标注", "fail" if no_src_r else "pass",
        ("无来源边: %s" % ", ".join(no_src_r)) if no_src_r else "全部边携带 source")
    assumed = [e["id"] for e in model["entities"] if any(
        s.get("kind") in ("assumption", "common_knowledge") for s in e.get("source", []))]
    if assumed:
        add("T03", "假设型来源显式化", "warn",
            "实体基于假设/常识: %s（须在 uncertainty 中说明）" % ", ".join(assumed))
    else:
        add("T03", "假设型来源显式化", "pass", "无假设型来源实体")

    # --- legend / data-encoding consistency -----------------------------------
    used_etypes = {e["type"] for e in model["entities"]}
    used_rtypes = {r["type"] for r in model["edges"]}
    missing_e = used_etypes - set((model["legend"].get("entities") or {}))
    missing_r = used_rtypes - set((model["legend"].get("edges") or {}))
    add("L01", "图例覆盖(实体类型)", "fail" if missing_e else "pass",
        ("图例缺少类型: %s" % sorted(missing_e)) if missing_e else "图例覆盖全部在用实体类型")
    add("L02", "图例覆盖(边类型)", "fail" if missing_r else "pass",
        ("图例缺少边类型: %s" % sorted(missing_r)) if missing_r else "图例覆盖全部在用边类型")
    dm = model["legend"].get("data_mapping") or {}
    if dm.get("field"):
        scale = data_scale(model)
        add("L03", "数据映射有数值支撑", "warn" if not scale else "pass",
            "映射字段 %s 在实体数据中未找到数值（图默认色）" % dm["field"] if not scale
            else "映射字段 %s: 数值范围 [%s, %s]" % (dm["field"], scale[0], scale[1]))
    else:
        add("L03", "数据映射字段声明", "warn", "未声明 data_mapping.field（图例将不含数据映射区）")

    # --- arrow semantics (marker matches legend) ------------------------------
    svg_path = out_files.get("svg")
    marker_of = {}
    if svg_path and os.path.isfile(svg_path):
        try:
            tree = ET.parse(svg_path)
        except Exception as ex:
            add("S00", "SVG 可解析", "fail", "svg 解析失败: %s" % ex)
            tree = None
        if tree is not None:
            add("S00", "SVG 可解析(XML well-formed)", "pass", "ElementTree 可解析")
            for m in _svg_elems(tree, "marker"):
                marker_of[m.get("id")] = m
            for p in _svg_elems(tree, "path"):
                mid = p.get("marker-end")
                if not mid:
                    continue
                mid = mid.replace("url(#", "").rstrip(")")
                rtype = p.get("data-type")
                rid = p.get("data-id")
                spec = (model["legend"].get("edges") or {}).get(rtype)
                if not spec:
                    add("L04", "边类型->图例映射", "fail",
                        "边 %s 类型 %s 不在图例中" % (rid, rtype))
                    continue
                want = "mk-%s-%s" % (spec["marker"], spec["color"].lstrip("#").lower())
                if mid != want:
                    add("L04", "箭头语义=图例声明", "fail",
                        "边 %s 使用 marker %s，图例声明为 %s" % (rid, mid, want))
            # color audit: every *semantic* element color (entity nodes &
            # typed edges) must appear in the legend or the data mapping ramp.
            # Compartment bands, titles, texts and legend chrome are layout
            # decoration, not data encoding, so they are out of scope here.
            legend_colors = set()
            for t, sp in (model["legend"].get("entities") or {}).items():
                legend_colors.add(sp.get("fill")); legend_colors.add(sp.get("stroke"))
            for t, sp in (model["legend"].get("edges") or {}).items():
                legend_colors.add(sp.get("color"))
            if dm.get("low"): legend_colors.add(dm["low"])
            if dm.get("high"): legend_colors.add(dm["high"])
            scale = data_scale(model)
            vmin, vmax = (scale[0], scale[1]) if scale else (0, 1)
            resolved_fills = {data_color({"type": e["type"], "data": e.get("data")},
                                         model["legend"], vmin, vmax)["fill"]
                              for e in model["entities"]}
            allowed = legend_colors | resolved_fills
            off_colors = []
            for g in tree.iter(SVG_NS + "g"):
                gid = g.get("id") or ""
                if gid.startswith("entity-"):
                    for el in g.iter():
                        if el.tag in (SVG_NS + "rect", SVG_NS + "circle"):
                            for c in (el.get("fill"), el.get("stroke")):
                                if c and c.startswith("#") and c not in allowed and c not in off_colors:
                                    off_colors.append(c)
            for p in _svg_elems(tree, "path"):
                if p.get("data-type") is not None:
                    c = p.get("stroke") or (p.get("style") or "").split("stroke:")[-1].split(";")[0]
                    if c and c.startswith("#") and c not in allowed and c not in off_colors:
                        off_colors.append(c)
            add("L05", "图面颜色⊆图例/数据映射(节点与边)", "fail" if off_colors else "pass",
                ("节点/边出现图例未声明的颜色: %s" % ", ".join(off_colors)) if off_colors
                else "节点与边的全部颜色都可回溯到图例或数据映射")
    else:
        add("S00", "SVG 存在", "fail", "未找到 SVG 输出")

    # --- layout direction rule -------------------------------------------------
    rank_of = layout.get("rank_of") or {}
    up_edges = []
    for rid, r in layout["edges"].items():
        if r.get("feedback"):
            continue
        rs = rank_of.get(r["from"], 9)
        rd = rank_of.get(r["to"], 9)
        if rd < rs:
            up_edges.append("%s(%s→%s)" % (rid, r["from"], r["to"]))
    add("D01", "通路方向(上游→下游)", "warn" if up_edges else "pass",
        ("非反馈边逆流: %s（需在 uncertainty 中说明）" % ", ".join(up_edges)) if up_edges
        else "全部非反馈边符合区室上→下流向")

    # --- files ---------------------------------------------------------------
    for key, fname in (("svg", "SVG"), ("png", "PNG预览"), ("pdf", "PDF预览")):
        p = out_files.get(key)
        if isinstance(p, str) and os.path.isfile(p):
            sz = os.path.getsize(p)
            add("F01_%s" % key, "%s 存在且非空" % fname, "pass", "%s (%d bytes)" % (p, sz))
        else:
            add("F01_%s" % key, "%s 存在且非空" % fname, "fail", "缺失: %s" % (p or "N/A"))
    png = out_files.get("png")
    if png and os.path.isfile(png):
        try:
            from PIL import Image
            im = Image.open(png)
            w, h = im.size
            add("F02_png", "PNG 尺寸/可打开", "pass", "%dx%d px" % (w, h))
        except Exception as ex:
            add("F02_png", "PNG 尺寸/可打开", "fail", str(ex))

    failed = [c for c in checks if c["result"] == "fail"]
    warned = [c for c in checks if c["result"] == "warn"]
    return {"passed": len(failed) == 0, "checks": checks,
            "failures": failed, "warnings": warned}