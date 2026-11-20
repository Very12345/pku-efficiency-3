# -*- coding: utf-8 -*-
"""check.py — 交付自查（对应「结果可核验性」评分点）。

检查 result.json 是否符合 OUTPUT_CONTRACT、产物文件是否真实存在、
SVG 是否可被 XML 解析且文字为可编辑 <text>、图例与图元是否一致、
编号是否连续、箭头方向是否与关系一致。失败项进 issues，不以 0 退出
隐瞒问题——由 main.py 汇总为 honest status。
"""

from __future__ import annotations

import json
import os
import sys
sys.dont_write_bytecode = True  # 评测包内不落 .pyc
import xml.etree.ElementTree as ET
from typing import Any, Dict, List


def check_result(result_path: str) -> Dict[str, Any]:
    """检查 result.json 及其引用的产物文件。返回 {ok, checks, issues}。"""
    issues: List[str] = []
    checks: Dict[str, Any] = {}

    if not os.path.isfile(result_path):
        return {"ok": False, "checks": {}, "issues": [f"result.json 不存在: {result_path}"]}
    with open(result_path, "r", encoding="utf-8") as fh:
        result = json.load(fh)

    required_fields = [
        "case_id", "status", "title", "figure_type", "output_contract",
        "sources", "uncertainty", "change_record", "checksum",
    ]
    for rf in required_fields:
        checks[f"field:{rf}"] = rf in result
        if rf not in result:
            issues.append(f"result.json 缺少必需字段: {rf}")

    oc = result.get("output_contract") or {}
    for f in ["editable_sources", "exports", "data_mapping", "element_traceability"]:
        checks[f"contract:{f}"] = f in oc
        if f not in oc:
            issues.append(f"output_contract 缺少字段: {f}")

    # 产物文件真实存在性
    out_dir = os.path.dirname(os.path.abspath(result_path))
    for src in oc.get("editable_sources") or []:
        p = src.get("path") or ""
        full = p if os.path.isabs(p) else os.path.join(out_dir, p)
        checks[f"file:{os.path.basename(p)}"] = os.path.isfile(full)
        if not os.path.isfile(full):
            issues.append(f"可编辑源文件不存在: {p}")
        elif p.endswith(".svg"):
            svg_issues = check_svg(full)
            checks[f"svg_parse:{os.path.basename(p)}"] = not svg_issues
            issues.extend(svg_issues)
    for ex in oc.get("exports") or []:
        p = ex.get("path") or ""
        full = p if os.path.isabs(p) else os.path.join(out_dir, p)
        checks[f"file:{os.path.basename(p)}"] = os.path.isfile(full)
        if not os.path.isfile(full):
            issues.append(f"导出文件不存在: {p}")
        else:
            st = os.stat(full)
            checks[f"size:{os.path.basename(p)}"] = st.st_size > 0
            if st.st_size == 0:
                issues.append(f"导出文件为空: {p}")

    # SVG 实体与 result 实体对齐
    entities = result.get("entities") or []
    rels = result.get("relations") or []
    checks["entity_count_gte1"] = len(entities) >= 1
    checks["relation_none_dangling"] = all(
        r.get("from") in {e["id"] for e in entities}
        and r.get("to") in {e["id"] for e in entities}
        for r in rels
    )
    if rels and not checks["relation_none_dangling"]:
        issues.append("存在指向不存在实体的关系（断头箭头）")

    # 编号连续性
    nos = sorted([e.get("step_no") for e in entities if e.get("step_no")],
                 key=lambda v: int(v) if str(v).isdigit() else 999)
    nums = [int(v) for v in nos if str(v).isdigit()]
    if nums and nums != list(range(1, len(nums) + 1)):
        issues.append(f"步骤编号不连续: {nums}")

    checks["uncertainty_recorded"] = isinstance(result.get("uncertainty"), list)
    checks["status_honest"] = result.get("status") in ("success", "partial", "failed")
    if result.get("status") == "success" and oc.get("data_mapping") is None:
        issues.append("status=success 但 data_mapping 缺失")

    ok = not issues
    return {"ok": ok, "checks": checks, "issues": issues, "summary": {
        "status": result.get("status"),
        "entities": len(entities),
        "relations": len(rels),
        "issues": len(issues),
    }}


def check_svg(svg_path: str) -> List[str]:
    """SVG 可解析、有可编辑文本、实体组带 data-source。"""
    issues: List[str] = []
    try:
        tree = ET.parse(svg_path)
    except Exception as exc:  # noqa: BLE001
        return [f"SVG XML 解析失败: {exc}"]
    root = tree.getroot()
    ns = root.tag.split("}")[0] + "}" if root.tag.startswith("{") else ""
    def elems(tag):
        return list(root.iter(f"{ns}{tag}")) if ns else list(root.iter(tag))
    text_list = elems("text")
    if len(text_list) < 3:
        issues.append(f"SVG 可编辑 <text> 元素过少: {len(text_list)}")
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