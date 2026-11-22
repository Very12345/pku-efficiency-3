# -*- coding: utf-8 -*-
"""scaffold.py — 方案先行（design-first）：从实际材料生成图形摘要设计方案骨架。

Part of the "graphical-abstract" Skill v2 (graphical-abstract-7030fff2,
efficiency-3).

流程位置（与 references/plan-schema.md 配套）：
    材料 → scaffold（本脚本）→ 设计方案 plan.json（Agent 补全/定稿）→
    spec_lint.lint_plan（CP1 方案门）→ main.py --plan plan.json → 绘制 → audit。

产出 plan.json（schema 见 references/plan-schema.md）：
    {
      "schema": "plan-schema/v2",
      "case_id": ...,
      "title": ...,
      "four_elements": { "question": "", "method": "", "results": "", "conclusion": "" },
      "entities":   [{name, type, panel, src, note?}, ...],   // 从材料抽取，带 src
      "relations":  [{from, to, label, kind?, src}, ...],
      "data":       [{label, value?, kind, src, note?}, ...],
      "figure_constraints": {width, height, dpi, colorblind, flow_arrows, ...},
      "plan_source": "scaffold",
      "skeleton": true
    }

骨架由 extract 流水线真实抽取（源定位），four_elements 需要 Agent 依据材料
一句话填充 —— 这是"先想清楚画什么，再动笔"的关键一步；不得跳过。
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import spec_lint  # noqa: E402
from common import SKILL_VERSION, write_json  # noqa: E402
from extract import run as extract_run  # noqa: E402


def build_plan(content: dict) -> dict:
    return {
        "schema": "plan-schema/v2",
        "case_id": content.get("case_id"),
        "title": content.get("title") or content.get("case_id", ""),
        "four_elements": {
            "question": "",
            "method": "",
            "results": "",
            "conclusion": "",
        },
        "entities": [
            {"name": e.get("name"), "type": e.get("type"),
             "panel": e.get("panel"), "src": e.get("src"),
             "note": e.get("note")} for e in content.get("entities", [])],
        "relations": [
            {"from": r.get("from"), "to": r.get("to"), "label": r.get("label"),
             "kind": r.get("kind"), "src": r.get("src")} for r in content.get("relations", [])],
        "data": [
            {"label": d.get("label"), "value": d.get("value"),
             "kind": d.get("kind"), "src": d.get("src"),
             "unit": d.get("unit"), "note": d.get("note")} for d in content.get("data", [])],
        "figure_constraints": content.get("constraints", {}),
        "panels_hint": {p: content.get("panels", {}).get(p, [])
                        for p in ("question", "method", "results", "conclusion")},
        "plan_source": "scaffold",
        "skill_version": SKILL_VERSION,
        "skeleton": True,
    }


def main(argv=None) -> int:
    import os as _os
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass
    ap = argparse.ArgumentParser(
        prog="scaffold",
        description="build a design-first plan.json skeleton from actual case material")
    ap.add_argument("--case", required=True, help="path to case.json")
    ap.add_argument("--task", default=None, help="path to task.md (auto: <case_dir>/task.md)")
    ap.add_argument("--material", default=None, help="material file or directory")
    ap.add_argument("--out", required=True, help="plan.json output path (or directory)")
    args = ap.parse_args(argv)

    case_path = os.path.abspath(args.case)
    if not os.path.isfile(case_path):
        print(json.dumps({"status": "failed", "error": f"case.json not found: {case_path}"},
                         ensure_ascii=False))
        return 1

    task_path = os.path.abspath(args.task) if args.task else None
    if task_path is None:
        cand = os.path.join(os.path.dirname(case_path), "task.md")
        if os.path.isfile(cand):
            task_path = cand
    material = os.path.abspath(args.material) if args.material else None

    try:
        content = extract_run(case_path, task_path, material)
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"status": "failed",
                          "error": f"extraction failed: {type(e).__name__}: {e}"},
                         ensure_ascii=False))
        return 1

    plan = build_plan(content)
    out = args.out
    if os.path.isdir(out) or out.endswith(os.sep) or out.endswith("/"):
        out = os.path.join(out, "plan.json")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    write_json(out, plan)

    lint_rep = spec_lint.lint_plan(plan)
    print(json.dumps({
        "status": "ok",
        "plan": out,
        "plan_hash": lint_rep.get("plan_hash"),
        "four_elements": list(plan["four_elements"].keys()),
        "lint": {"valid": lint_rep["valid"], "problems": lint_rep["problems"]},
        "next": "Agent: fill four_elements 一句话说明，按 references/plan-schema.md 定稿，"
                "随后运行 main.py --plan <plan.json>"
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())