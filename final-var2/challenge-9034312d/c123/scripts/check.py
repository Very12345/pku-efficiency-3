# -*- coding: utf-8 -*-
"""check.py — 交付自查（对应「结果可核验性」评分点；G1–G10 硬性门）。

与 references/OUTPUT_CONTRACT.md 的「G1–G10 硬性门」一一对应。检查
result.json 是否符合契约、产物文件是否真实存在、SVG 是否可解析且文字可编辑、
图例与图元是否一致、编号是否连续、箭头是否无断头、verify_report 是否全绿。
失败项进 issues，不以 0 退出隐瞒问题——由 main.py 汇总为 honest status
（G8：verify/rule 错误未解决时 status 不得为 success，见 D11）。
"""

from __future__ import annotations

import json
import os
import sys
sys.dont_write_bytecode = True
import xml.etree.ElementTree as ET
from typing import Any, Dict, List


# ---------------------------------------------------------------- 检查项

def check_result(result_path: str) -> Dict[str, Any]:
    """检查 result.json 及其引用的产物文件。返回 {ok, gates, issues, summary}。"""
    issues: List[str] = []
    gates: Dict[str, bool] = {}
    checks: Dict[str, Any] = {}

    # G1 result.json 存在、可解析、含 case_id 与合法 status
    if not os.path.isfile(result_path):
        return {"ok": False, "gates": {"G1": False}, "checks": {},
                "issues": [f"result.json 不存在: {result_path}"]}
    try:
        with open(result_path, "r", encoding="utf-8") as fh:
            result = json.load(fh)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "gates": {"G1": False}, "checks": {},
                "issues": [f"result.json 不可解析: {exc}"]}
    g1 = bool(result.get("case_id")) and result.get("status") in ("success", "partial", "failed")
    gates["G1"] = g1
    if not g1:
        issues.append("G1: case_id 缺失或 status 非法")

    required_fields = [
        "case_id", "status", "title", "figure_type", "output_contract",
        "sources", "uncertainty", "change_record", "checksum",
    ]
    for rf in required_fields:
        checks[f"field:{rf}"] = rf in result
        if rf not in result:
            issues.append(f"result.json 缺少必需字段: {rf}")

    oc = result.get("output_contract") or {}
    out_dir = os.path.dirname(os.path.abspath(result_path))
    # G2 output_contract 四段齐全且不为 null
    g2 = all(f in oc and oc[f] is not None for f in
             ["editable_sources", "exports", "data_mapping", "element_traceability"])
    gates["G2"] = g2
    if not g2:
        issues.append("G2: output_contract 四段不齐或为 null")

    # G3 可编辑源文件真实存在、SVG 可解析、<text> 可编辑
    g3 = bool(oc.get("editable_sources"))
    for src in oc.get("editable_sources") or []:
        p = src.get("path") or ""
        full = p if os.path.isabs(p) else os.path.join(out_dir, p)
        exists = os.path.isfile(full)
        checks[f"file:{os.path.basename(p)}"] = exists
        if not exists:
            g3 = False
            issues.append(f"G3: 可编辑源文件不存在: {p}")
        elif p.endswith(".svg"):
            svg_issues = _svg_editability(full)
            checks[f"svg:{os.path.basename(p)}"] = not svg_issues
            if svg_issues:
                g3 = False
                issues.extend(svg_issues)
    gates["G3"] = g3
    if not g3:
        issues.append("G3: 可编辑源文件缺失或 SVG 不可编辑")

    # G4 导出件真实存在且非空
    for ex in oc.get("exports") or []:
        p = ex.get("path") or ""
        full = p if os.path.isabs(p) else os.path.join(out_dir, p)
        exists = os.path.isfile(full)
        checks[f"export:{os.path.basename(p)}"] = exists
        if not exists:
            g4 = False
            issues.append(f"G4: 导出文件不存在: {p}")
        else:
            st = os.stat(full)
            checks[f"export_size:{os.path.basename(p)}"] = st.st_size > 0
            if st.st_size == 0:
                g4 = False
                issues.append(f"G4: 导出文件为空: {p}")
    g4 = bool(oc.get("exports")) and all(
        checks.get(f"export:{os.path.basename(e.get('path') or '')}", False)
        for e in oc.get("exports") or [])
    gates["G4"] = g4
    if not g4:
        issues.append("G4: 导出件缺失或为空")

    # G5 data_mapping 与实体一一对应
    entities = result.get("entities") or []
    rels = result.get("relations") or []
    dm = oc.get("data_mapping") or []
    eids = {e.get("id") for e in entities}
    dm_ids = [d.get("entity_id") for d in dm]
    g5 = len(dm) == len(entities) and len(set(dm_ids)) == len(dm_ids) and set(dm_ids) == eids
    gates["G5"] = g5
    if not g5:
        issues.append(f"G5: data_mapping 行数/唯一性/实体对齐不符 (dm={len(dm)}, entities={len(entities)})")

    # G6 element_traceability 覆盖全部实体与关系
    et = oc.get("element_traceability") or []
    et_entities = {x.get("element") for x in et if str(x.get("element", "")).startswith("entity-")}
    et_arrows = {x.get("element") for x in et if x.get("element", "").startswith("arrow-")}
    g6 = set(f"entity-{i}" for i in eids) <= et_entities and \
         set(f"arrow-{r.get('id')}" for r in rels) <= et_arrows
    gates["G6"] = g6
    if not g6:
        issues.append("G6: element_traceability 未覆盖全部实体/箭头")

    # G7 无断头箭头
    g7 = all(r.get("from") in eids and r.get("to") in eids for r in rels)
    gates["G7"] = g7
    if not g7:
        issues.append("G7: 存在指向不存在实体的关系（断头箭头）")

    # G8 步骤编号连续（route/flow）
    nos = [int(e["step_no"]) for e in entities
           if e.get("step_no") and str(e["step_no"]).isdigit()]
    if result.get("figure_type") in ("route", "flow") and nos:
        g8 = sorted(nos) == list(range(1, len(nos) + 1))
    else:
        g8 = True
    gates["G8"] = g8
    if not g8:
        issues.append(f"G8: 步骤编号不连续: {sorted(nos)}")

    # G9 verify_report.json 存在且全绿（深层规则/图层审计，与 svg_verify 对齐）
    g9 = False
    vp = os.path.join(out_dir, "verify_report.json")
    if os.path.isfile(vp):
        try:
            with open(vp, "r", encoding="utf-8") as fh:
                vr = json.load(fh)
            g9 = bool(vr.get("ok"))
            checks["verify_report"] = g9
            if not g9:
                issues.append(f"G9: verify_report 未全绿: {vr.get('summary', {})}")
        except Exception as exc:  # noqa: BLE001
            issues.append(f"G9: verify_report 不可解析: {exc}")
    else:
        issues.append("G9: verify_report.json 缺失（应已运行 svg_verify）")
    gates["G9"] = g9

    # G10 status 诚实：success 需要全部硬门通过且无可降级不确定性
    un = result.get("uncertainty") or []
    error_unc = [u for u in un if "scope" in u and str(u.get("scope")) in
                 ("rule_violation", "svg_verify", "orphan_entities", "png", "pdf", "fonts")]
    if result.get("status") == "success":
        g10 = all([g1, g2, g3, g4, g5, g6, g7, g8, g9]) and not error_unc
    else:
        g10 = True  # partial/failed 允许（诚实降级不判失败）
    gates["G10"] = g10
    if not g10:
        issues.append("G10: status=success 但硬门未全过或有未解决降级不确定性")

    checks["status_honest"] = result.get("status") in ("success", "partial", "failed")
    checks["uncertainty_recorded"] = isinstance(un, list)

    ok = all(gates.values())
    return {"ok": ok, "gates": gates, "checks": checks, "issues": issues, "summary": {
        "status": result.get("status"),
        "entities": len(entities),
        "relations": len(rels),
        "gates_pass": sum(1 for v in gates.values() if v),
        "gates_total": len(gates),
        "issues": len(issues),
    }}


def _svg_editability(svg_path: str) -> List[str]:
    """SVG 可解析、有可编辑文本、有分层 <g> 结构。"""
    issues: List[str] = []
    try:
        tree = ET.parse(svg_path)
    except Exception as exc:  # noqa: BLE001
        return [f"SVG XML 解析失败: {exc}"]
    root = tree.getroot()
    ns = root.tag.split("}")[0] + "}" if root.tag.startswith("{") else ""

    def elems(tag: str):
        return list(root.iter(f"{ns}{tag}")) if ns else list(root.iter(tag))
    texts = elems("text")
    if len(texts) < 3:
        issues.append(f"SVG 可编辑 <text> 元素过少: {len(texts)}")
    groups = elems("g")
    if len(groups) < 3:
        issues.append("SVG 缺少分层 <g> 结构（图层）")
    return issues


def main(argv: List[str]) -> int:
    if len(argv) < 1:
        print("usage: python scripts/check.py <result.json>")
        return 2
    res = check_result(argv[0])
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))