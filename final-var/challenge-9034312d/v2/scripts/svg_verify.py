# -*- coding: utf-8 -*-
"""svg_verify.py — SVG 校验 + 连接规则审计（对应高分包 88686 的 svg_verify / 86267 的
check_svg 职责，并按 78615 的 connection_rules.json 思路升级为「规则资产驱动」）。

消费：
- layout.json（结构化布局模型，main.py 产出）
- figure.svg（可编辑源文件）
- assets/connection_rules.json（连接/类别规则资产，可被他人直接扩展）

检查项（CP3 校验门）：
1. svg_parse        — SVG 是合法 XML
2. layers           — 五层 id 齐全（background/title/arrows/entities/legend）
3. editable_text    — 可编辑 <text> ≥3、实体组 <g> 结构与布局模型一一对应
4. arrows           — 每条关系有 arrow-<id> 路径 + arrowhead-<id> 多边形
5. numbering        — route/flow 图步骤编号 1..N 连续（figure_type 从 layout 读）
6. legend_kinds     — 图例 kind 集合 == 实际使用 kind 集合（图例↔图元一致）
7. connection_rules — 按 assets/connection_rules.json 审计类别词表与连接语义
8. determinism      — 布局确定性探针 spec_sha16（同输入同布局的机器证据）

退出码：无 error 级违规 → 0；有 error 级违规或不可解析 → 1。
输出 verify_report.json（{ok, checks, rule_violations, issues, summary}）。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
sys.dont_write_bytecode = True
import xml.etree.ElementTree as ET
from typing import Any, Dict, List

_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(_SCRIPTS_DIR)

# 与 layout.py 的 figure_type 判定保持一致
STEP_KINDS = {"step", "phase", "milestone"}


def _load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _default_rules_path() -> str:
    return os.path.join(SKILL_ROOT, "assets", "connection_rules.json")


def _spec_sha16(layout: Dict[str, Any]) -> str:
    """确定性探针：对图面内容的规范化子集做 sha256 前 16 位。"""
    probe = {
        "case_id": layout.get("case_id"),
        "canvas": layout.get("canvas"),
        "entities": [
            {"id": e["id"], "kind": e["kind"], "x": e["x"], "y": e["y"],
             "w": e["w"], "h": e["h"], "step_no": e.get("step_no")}
            for e in layout.get("entities") or []
        ],
        "relations": [
            {"id": r["id"], "kind": r["kind"], "from": r["from"], "to": r["to"],
             "points": r.get("points")}
            for r in layout.get("relations") or []
        ],
    }
    canon = json.dumps(probe, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(canon).hexdigest()[:16]


def check_svg(layout: Dict[str, Any], svg_path: str, rules: Dict[str, Any]) -> Dict[str, Any]:
    """校验 SVG 与布局模型的一致性 + 连接规则审计。返回报告的 dict。"""
    issues: List[str] = []
    errors: List[Dict[str, str]] = []     # error 级规则违规
    warnings: List[Dict[str, str]] = []   # warn 级规则违规
    checks: Dict[str, Any] = {}

    # ---------- 1) SVG XML 解析 ----------
    try:
        tree = ET.parse(svg_path)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "checks": {"svg_parse": False},
                "issues": [f"SVG XML 解析失败: {exc}"],
                "rule_violations": [], "errors": [], "warnings": [],
                "determinism": {"spec_sha16": _spec_sha16(layout)},
                "summary": {"status": "invalid-svg"}}
    root = tree.getroot()
    ns = root.tag.split("}")[0] + "}" if root.tag.startswith("{") else ""

    def elems(tag: str):
        return list(root.iter(f"{ns}{tag}")) if ns else list(root.iter(tag))

    # ---------- 2) 图层 ----------
    exp_layers = ["layer-background", "layer-title", "layer-arrows", "layer-entities", "layer-legend"]
    ids = {e.get("id") for e in root.iter() if e.get("id")}
    missing_layers = [ln for ln in exp_layers if ln not in ids]
    checks["layers"] = not missing_layers
    if missing_layers:
        issues.append(f"SVG 缺少图层: {missing_layers}")

    # ---------- 3) 可编辑文本 + 实体组一一对应 ----------
    texts = elems("text")
    checks["editable_text"] = len(texts) >= 3
    if len(texts) < 3:
        issues.append(f"SVG 可编辑 <text> 元素过少: {len(texts)}")

    entity_ids_in_svg = {
        g.get("data-entity") for g in elems("g") if g.get("data-entity")
    }
    layout_entity_ids = {e["id"] for e in layout.get("entities") or []}
    missing_entities = sorted(layout_entity_ids - entity_ids_in_svg)
    checks["entity_groups"] = not missing_entities
    if missing_entities:
        issues.append(f"SVG 缺少实体组: {missing_entities}")

    # data-source 覆盖率（可核验性）
    no_src = [e["id"] for e in layout.get("entities") or []
              if not (e.get("source") or "").strip()]
    checks["entity_source_coverage"] = len(no_src) == 0
    if no_src:
        issues.append(f"{len(no_src)} 个实体缺 source: {no_src[:6]}")

    # ---------- 4) 箭头 ----------
    rel_ids = {r["id"] for r in layout.get("relations") or []}
    svg_arrow_ids = {e.get("id", "")[len("arrow-"):] for e in elems("path")
                     if (e.get("id") or "").startswith("arrow-")}
    missing_arrows = sorted(rel_ids - svg_arrow_ids)
    svg_arrowhead_ids = {e.get("id", "")[len("arrowhead-"):] for e in elems("polygon")
                         if (e.get("id") or "").startswith("arrowhead-")}
    missing_heads = sorted(rel_ids - svg_arrowhead_ids)
    checks["arrows"] = not missing_arrows and not missing_heads
    if missing_arrows:
        issues.append(f"SVG 缺箭头路径: {missing_arrows}")
    if missing_heads:
        issues.append(f"SVG 缺箭头多边形: {missing_heads}")

    # 断头箭头检测（关系两端实体都必须存在）
    dangling = [r["id"] for r in layout.get("relations") or []
                if r["from"] not in layout_entity_ids or r["to"] not in layout_entity_ids]
    checks["no_dangling"] = not dangling
    if dangling:
        issues.append(f"存在断头箭头（关系端点实体缺失）: {dangling}")

    # ---------- 5) 编号连续性（route/flow） ----------
    ftype = str(layout.get("figure_type") or "")
    nums = sorted(
        (int(e["step_no"]) for e in layout.get("entities") or []
         if e.get("step_no") and str(e["step_no"]).isdigit()))
    if ftype in ("route", "flow") and nums:
        checks["numbering_continuous"] = nums == list(range(1, len(nums) + 1))
        if not checks["numbering_continuous"]:
            issues.append(f"步骤编号不连续: {nums}")
    else:
        checks["numbering_continuous"] = True  # 非 route/flow 或无数值，跳过

    # ---------- 6) 图例 ↔ 图元 kind 一致 ----------
    used_kinds = {e["kind"] for e in layout.get("entities") or []}
    legend_kinds = {it["kind"] for it in layout.get("legend") or []}
    checks["legend_kinds"] = used_kinds == legend_kinds
    if used_kinds != legend_kinds:
        issues.append(f"图例与图元 kind 不一致: 缺 {sorted(used_kinds - legend_kinds)} / "
                      f"多 {sorted(legend_kinds - used_kinds)}")

    # ---------- 7) 连接规则审计（assets/connection_rules.json） ----------
    allowed_kinds = set(rules.get("allowed_kinds") or [])
    allowed_rel_kinds = set(rules.get("allowed_relation_kinds") or [])
    if allowed_kinds:
        bad_kinds = sorted(used_kinds - allowed_kinds)
        if bad_kinds:
            errors.append({"rule": "kind-vocabulary",
                           "severity": "error",
                           "detail": f"图元类别不在词表内: {bad_kinds}"})
        checks["kind_vocabulary"] = not bad_kinds
    if allowed_rel_kinds:
        bad_rel = sorted({r["kind"] for r in layout.get("relations") or []} - allowed_rel_kinds)
        if bad_rel:
            errors.append({"rule": "relation-kind-vocabulary",
                           "severity": "error",
                           "detail": f"关系类别不在词表内: {bad_rel}"})
        checks["relation_kind_vocabulary"] = not bad_rel

    entity_kind = {e["id"]: e["kind"] for e in layout.get("entities") or []}
    for rule in (rules.get("rules") or []):
        rid = rule.get("id", "?")
        sev = rule.get("severity", "warn")
        when_figs = rule.get("when_figure_types") or []
        if when_figs and ftype not in when_figs:
            continue
        rkind = rule.get("when_rel_kind")
        chk = rule.get("check")
        hits: List[str] = []
        for r in layout.get("relations") or []:
            if rkind and r["kind"] != rkind:
                continue
            fk = entity_kind.get(r["from"])
            tk = entity_kind.get(r["to"])
            if chk == "sequence_step_only" and r["kind"] == "sequence":
                if fk not in STEP_KINDS or tk not in STEP_KINDS:
                    hits.append(f"{r['id']}({r['from']}:{fk or '?'}→{r['to']}:{tk or '?'})")
            elif chk == "no_flow_into_material" and r["kind"] != "recycle":
                if tk == "material" and fk in ("device", "step", "phase", "product"):
                    hits.append(f"{r['id']}({r['from']}→{r['to']})")
            elif chk == "product_is_terminal" and r["kind"] != "recycle":
                if fk in ("product", "data", "waste", "milestone"):
                    hits.append(f"{r['id']}({r['from']}:{fk}→{r['to']})")
            elif chk == "connect_structural":
                if r["kind"] == "connect" and not ({fk, tk} & {"device", "container"}):
                    hits.append(f"{r['id']}({r['from']}:{fk or '?'}↔{r['to']}:{tk or '?'})")
            elif chk == "recycle_review":
                hits.append(f"{r['id']}({r['from']}→{r['to']})")  # 回流需 Agent 复核
            elif chk == "no_self_loop":
                if r["from"] == r["to"]:
                    hits.append(f"{r['id']}({r['from']}→{r['to']})")
        if hits:
            entry = {"rule": rid, "severity": sev, "detail": f"{rule.get('reason', rid)}: {hits[:8]}"}
            if sev == "error":
                errors.append(entry)
            else:
                warnings.append(entry)

    checks["connection_rules"] = not errors
    checks["all"] = (not issues) and (not errors)

    summary = {
        "status": "pass" if checks["all"] else "attention",
        "figure_type": ftype,
        "entities": len(layout_entity_ids),
        "relations": len(rel_ids),
        "errors": len(errors),
        "warnings": len(warnings),
        "issues": len(issues),
        "spec_sha16": _spec_sha16(layout),
    }
    return {"ok": checks["all"], "checks": checks, "issues": issues,
            "rule_violations": errors + warnings, "errors": errors, "warnings": warnings,
            "determinism": {"spec_sha16": _spec_sha16(layout)}, "summary": summary}


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="SVG 校验 + 连接规则审计")
    ap.add_argument("--layout", required=True, help="layout.json 路径")
    ap.add_argument("--svg", required=True, help="figure.svg 路径")
    ap.add_argument("--rules", default=None, help="connection_rules.json 路径（默认取技能根 assets/）")
    ap.add_argument("--out", default=None, help="verify_report.json 输出路径（默认打印到 stdout）")
    args = ap.parse_args(argv)

    layout = _load_json(args.layout)
    rules_path = args.rules or _default_rules_path()
    rules = _load_json(rules_path) if os.path.isfile(rules_path) else {}
    report = check_svg(layout, args.svg, rules)

    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))