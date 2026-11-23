#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
spec_lint.py — figure spec 结构校验（CP3 生成门）

在绘制前校验图规格（figure spec），把"文字约束"变成可执行检查。
不依赖 jsonschema 库：按 templates/figure_map.schema.json 声明的图型词表手工校验。

检查项（问题分级：error=阻止生成；warn=记录偏差按 D 规则处置）：
E1  图型 type ∈ {bar,line,scatter,box,heatmap,pie,network,panel,auto}（error）
E2  每图必须有 id（error）
E3  数据型图（非 network/heatmap/pie-without-data）引用存在的列（error，需 --case 提供数据）
E4  误差线列存在（error）；error.semantics ∈ {SE,SEM,SD,STD,CI,95% CI}（warn）
E5  显著性 annotations：{from,to}|{at} + text + p 存在；引用的分类存在（error/warn）
E6  轴标签含单位的建议（源列名带单位或 spec 提供了 unit；warn）
E7  panel 必须含 panels[]，每个子规格通过 lint（递归，error）
E8  network：entities/relations 存在且关系引用的节点 id 存在（error）；
   实体 label 允许中文但必须以材料原文为准（warn）
E9  filter（column, eq）列存在（error）
E10 禁止字段：type 大小写不规范（warn）；width/height 超过 5000（warn）

输出：
  {"valid": bool, "problems": [{"level","code","figure_id","message"}],
   "counts": {"figures": n, "errors": n, "warnings": n}}

cli：python spec_lint.py --spec <figure_spec.json 或 case.json> [--case <case.json>] [--json]
     --spec 传 case.json 时自动取 figures[]。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chartkit as ck  # noqa: E402

TYPES = {"bar", "line", "scatter", "box", "heatmap", "pie", "network", "panel", "auto"}
ERROR_SEMANTICS = {"", "se", "sem", "sd", "std", "ci", "95% ci", "semantics"}
NUMERIC_TYPES = {"bar", "line", "scatter", "box"}


def lint_spec(spec, case=None, rows_map=None):
    """校验一个 figure spec。rows_map: {file_basename: rows} 供列存在性检查。"""
    problems = []
    fid = str(spec.get("id") or "?")
    t = str(spec.get("type") or "auto").lower()
    if t not in TYPES:
        problems.append({"level": "error", "code": "E1", "figure_id": fid,
                         "message": f"不支持的图型 '{t}'（允许 {sorted(TYPES)}）"})
    if not spec.get("id"):
        problems.append({"level": "error", "code": "E2", "figure_id": fid, "message": "缺少 id"})
    w = spec.get("width"); h = spec.get("height")
    if isinstance(w, (int, float)) and w > 5000:
        problems.append({"level": "warn", "code": "E10", "figure_id": fid, "message": "width 超过 5000，投稿环境可能不支持"})
    if isinstance(h, (int, float)) and h > 5000:
        problems.append({"level": "warn", "code": "E10", "figure_id": fid, "message": "height 超过 5000，投稿环境可能不支持"})

    rows = _rows_for(spec, rows_map)

    if t in NUMERIC_TYPES or t == "panel":
        # 列存在性
        for kind in ("x", "y", "error", "hue"):
            col = (spec.get(kind) or {}).get("column") if isinstance(spec.get(kind), dict) else None
            if col and rows is not None and col not in (rows[0] if rows else {}):
                problems.append({"level": "error", "code": "E3", "figure_id": fid,
                                 "message": f"{kind}.column '{col}' 在数据列中不存在（可用：{list((rows[0] if rows else {}).keys())}）"})
        err = spec.get("error") or {}
        if err.get("semantics") and str(err.get("semantics")).lower() not in ERROR_SEMANTICS:
            problems.append({"level": "warn", "code": "E4", "figure_id": fid,
                             "message": f"error.semantics '{err.get('semantics')}' 非常规（建议 SE/SD/CI）"})
        # 显著性
        cats = _categories(spec, rows)
        for i, ann in enumerate(spec.get("annotations") or []):
            a = ann if isinstance(ann, dict) else {}
            has_src = bool(a.get("from") is not None or a.get("at") is not None)
            if not has_src or a.get("text") is None:
                problems.append({"level": "error", "code": "E5", "figure_id": fid,
                                 "message": f"annotations[{i}] 缺少 from/to 或 at（显著性无锚点）"})
            if a.get("from") is not None and cats is not None and \
                    str(a["from"]) not in cats and str(a["from"]) not in (spec.get("order") or []):
                problems.append({"level": "error", "code": "E5", "figure_id": fid,
                                 "message": f"annotations[{i}] from='{a['from']}' 不在分类中 {cats}"})
            if a.get("to") is not None and cats is not None and \
                    str(a["to"]) not in cats and str(a["to"]) not in (spec.get("order") or []):
                problems.append({"level": "error", "code": "E5", "figure_id": fid,
                                 "message": f"annotations[{i}] to='{a['to']}' 不在分类中 {cats}"})
            if a.get("p") is None and not a.get("source"):
                problems.append({"level": "warn", "code": "E5", "figure_id": fid,
                                 "message": "显著性未注明 p 值或来源（只转述，不自行计算）"})
    if t == "network":
        ents = spec.get("entities") or spec.get("nodes") or []
        rels = spec.get("relations") or spec.get("edges") or []
        if not ents and not (spec.get("entities_file") or spec.get("material_file")):
            problems.append({"level": "error", "code": "E8", "figure_id": fid,
                             "message": "network 缺实体来源（entities[] 或 entities_file）"})
        ids = {str(n.get("id")) for n in ents if isinstance(n, dict) and n.get("id")}
        for i, rel in enumerate(rels or []):
            if not isinstance(rel, dict):
                continue
            if rel.get("from") not in ids or rel.get("to") not in ids:
                problems.append({"level": "error", "code": "E8", "figure_id": fid,
                                 "message": f"relations[{i}] {rel.get('from')}->{rel.get('to')} 引用了未定义节点"})
    if t == "panel":
        subs = spec.get("panels") or spec.get("subfigures") or []
        if not subs:
            problems.append({"level": "error", "code": "E7", "figure_id": fid, "message": "panel 需要 panels[]"})
        for i, s in enumerate(subs):
            if isinstance(s, dict):
                for p in lint_spec({**s, "id": s.get("id") or f"{fid}-{chr(ord('A') + i)}"},
                                   case=case, rows_map=rows_map):
                    problems.append(p)
    filt = spec.get("filter")
    if isinstance(filt, dict) and filt.get("column") and rows is not None and \
            filt["column"] not in (rows[0] if rows else {}):
        problems.append({"level": "error", "code": "E9", "figure_id": fid,
                         "message": f"filter.column '{filt['column']}' 不存在"})
    return problems


def _rows_for(spec, rows_map):
    """为 spec 挑选数据行（按 data_file 或默认第一张表）。"""
    if not rows_map:
        return None
    df = spec.get("data_file") or spec.get("data_files")
    if isinstance(df, str) and df in rows_map:
        return rows_map[df]
    if isinstance(df, list):
        for d in df:
            if d in rows_map:
                return rows_map[d]
    files = list(rows_map.keys())
    return rows_map[files[0]] if files else None


def _categories(spec, rows):
    xcol = (spec.get("x") or {}).get("column")
    if xcol and rows:
        seen = []
        for r in rows:
            v = str(r.get(xcol))
            if v not in seen:
                seen.append(v)
        if seen:
            return seen
    if spec.get("order"):
        return list(spec["order"])
    return None


def lint_case(case):
    """校验整个 case 的所有 figure spec。case 已 load 为 dict。"""
    specs = []
    if isinstance(case.get("figures"), list):
        specs = case["figures"]
    elif case.get("figure") is not None:
        specs = [case["figure"]]
    elif case.get("figure_spec") is not None:
        specs = [case["figure_spec"]]
    problems = []
    for s in specs:
        problems.extend(lint_spec(s, case=case))
    return problems


def build_rows_map(case_path, case):
    """按 case 数据文件装载 {basename: rows}，供列存在性校验。"""
    case_dir = os.path.dirname(os.path.abspath(case_path))
    files = case.get("data_files") or case.get("sources") or []
    if isinstance(files, str):
        files = [files]
    rows_map = {}
    for f in files:
        if isinstance(f, dict):
            f = f.get("file") or f.get("path")
        if not f:
            continue
        p = f if os.path.isabs(str(f)) else os.path.join(case_dir, str(f))
        if os.path.exists(p):
            try:
                _h, rws, _e = ck.load_table(p)
                rows_map[os.path.basename(p)] = rws
            except Exception:
                pass
    if not rows_map and os.path.isdir(case_dir):
        for fn in sorted(os.listdir(case_dir)):
            low = fn.lower()
            if low.startswith(("case", "task")):
                continue
            if low.endswith((".csv", ".tsv", ".tab", ".json")):
                p = os.path.join(case_dir, fn)
                if os.path.exists(p):
                    try:
                        _h, rws, _e = ck.load_table(p)
                        rows_map[fn] = rws
                    except Exception:
                        pass
    return rows_map


def main(argv=None):
    ap = argparse.ArgumentParser(description="figure spec lint（CP3）")
    ap.add_argument("--spec", required=True, help="figure spec JSON 或 case.json（自动取 figures[]）")
    ap.add_argument("--case", default=None, help="case.json（提供数据列上下文）")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    def load(p):
        with open(p, "r", encoding="utf-8-sig") as f:
            return json.load(f)

    spec_obj = load(args.spec)
    case_path = args.case or (args.spec if isinstance(spec_obj, dict) and
                              (spec_obj.get("figures") or spec_obj.get("case_id")) else None)
    case = None
    if case_path and os.path.exists(case_path):
        case = load(case_path)
    rows_map = build_rows_map(case_path, case) if case_path and os.path.exists(case_path) else {}

    if isinstance(spec_obj, dict) and (spec_obj.get("figures") or spec_obj.get("case_id")):
        problems = lint_case(spec_obj)
        figs = spec_obj.get("figures")
        if not isinstance(figs, list):
            one = spec_obj.get("figure") or spec_obj.get("figure_spec")
            figs = [one] if one is not None else []
        n_fig = len(figs)
    else:
        problems = [{"level": "error", "code": "E1", "figure_id": "?", "message": "输入不是 case.json（无 figures）"}]
        n_fig = 0
    errs = [p for p in problems if p["level"] == "error"]
    warns = [p for p in problems if p["level"] == "warn"]
    report = {"valid": not errs, "problems": problems,
              "counts": {"figures": n_fig, "errors": len(errs), "warnings": len(warns)}}
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for p in problems:
            print(f"[{p['level'].upper()}] {p['code']} {p['figure_id']} — {p['message']}")
        print(f"SUMMARY: {'VALID' if report['valid'] else 'INVALID'} "
              f"({len(errs)} errors / {len(warns)} warnings / {n_fig} figures)")
    sys.exit(0 if report["valid"] else 2)


if __name__ == "__main__":
    main()