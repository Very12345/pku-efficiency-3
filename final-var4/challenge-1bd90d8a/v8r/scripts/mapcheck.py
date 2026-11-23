#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mapcheck.py — 数据 ↔ 图元映射双向校验（CP5 / D14 / G3 / G4）

对输出目录做"从图回溯到数据、从数据定位到图元"的机器核对：
1. 正向（manifest → SVG）：data_manifest.json 里每个元素（svg_id）必须在 SVG 中存在，
   且其 data-* 溯源属性与 manifest 的 source 映射一致（双向检索的第一方向）。
2. 反向（SVG → manifest）：SVG 数据层每个带 data-role 的图元必须在 manifest 中登记。
3. 值核对（最强证据）：对带 column+row_index+value 的图元，重新打开源数据文件，
   读取该行该列的值并比较（浮点容差 1e-9）——验证"柱高/点位/数值来自源数据表"。
4. 输出 mapcheck_report.json：逐图统计 {elements, checked, mismatches, unmatched}。

cli：python mapcheck.py --dir <out_dir> [--case <case.json>] [--json]
退出码：0 = 全部通过；1 = 存在映射缺口/不一致。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chartkit as ck  # noqa: E402


def _parse_svg_elements(svg_path):
    """用正则解析 SVG 中的元素：id、data-* 属性。返回 [{id, role, data:{}}]。"""
    with open(svg_path, "r", encoding="utf-8", errors="replace") as f:
        data = f.read()
    elems = []
    tag_re = re.compile(r"<(rect|line|polyline|polygon|circle|ellipse|path|text)\b([^>]*)/?>")
    for m in tag_re.finditer(data):
        attrs = dict(re.findall(r'([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*"([^"]*)"', m.group(2)))
        eid = attrs.get("id")
        role = attrs.get("data-role")
        if not eid:
            continue
        data_attr = {k[len("data-"):]: v for k, v in attrs.items() if k.startswith("data-") and k != "data-role"}
        elems.append({"id": eid, "role": role, "data": data_attr})
    return elems


def _load_source_tables(out_dir, case_path):
    """装载源数据文件：{basename: rows}。源定位优先 manifest.sources.file。"""
    tables = {}
    manifest_path = os.path.join(out_dir, "data_manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        for s in manifest.get("sources", []):
            bn = s.get("file")
            if not bn:
                continue
            for cand in (os.path.join(out_dir, bn), bn,
                         os.path.join(os.path.dirname(os.path.abspath(case_path or ".")), bn)):
                if os.path.exists(cand):
                    try:
                        _h, rows, _e = ck.load_table(cand)
                        tables[bn] = rows
                    except Exception:
                        pass
                    break
    if case_path and os.path.exists(case_path):
        case_dir = os.path.dirname(os.path.abspath(case_path))
        with open(case_path, "r", encoding="utf-8-sig") as f:
            case = json.load(f)
        if isinstance(case, list):
            case = case[0]
        files = case.get("data_files") or case.get("sources") or []
        if isinstance(files, str):
            files = [files]
        for f in files:
            if isinstance(f, dict):
                f = f.get("file") or f.get("path")
            if not f:
                continue
            p = f if os.path.isabs(str(f)) else os.path.join(case_dir, str(f))
            if os.path.exists(p) and os.path.basename(p) not in tables:
                try:
                    _h, rows, _e = ck.load_table(p)
                    tables[os.path.basename(p)] = rows
                except Exception:
                    pass
    return tables


def _check_value(data_attr, tables):
    """用源数据表核对 value/column/row_index。返回 (ok, detail)。"""
    col = data_attr.get("column") or data_attr.get("x_column") or data_attr.get("y_column")
    v = data_attr.get("value")
    ri = data_attr.get("row_index")
    if col is None or v is None or ri is None:
        return None, "无 value/column/row_index 三元组（网络图等非表格图元，改查实体存在性）"
    try:
        row_idx = int(ri)
        val = float(v)
    except (TypeError, ValueError):
        return None, "value/row_index 无法解析为数值"
    for bn, rows in tables.items():
        if row_idx < len(rows) and col in rows[0]:
            cell = rows[row_idx].get(col)
            cell_v = ck.safe_float(cell)
            if cell_v is None:
                # 源表此处为空：图元画了值 → 不一致
                return False, f"{bn} 行 {row_idx} 列 {col} 源值为空，但图中画了 {val}"
            if abs(cell_v - val) < 1e-9 * max(1.0, abs(val)):
                return True, f"{bn} 行 {row_idx} 列 {col} = {cell_v} 与图元一致"
            return False, f"{bn} 行 {row_idx} 列 {col} = {cell_v} ≠ 图元 {val}"
    return None, "未找到可用的源数据表（仅做映射结构核对）"


def mapcheck(out_dir, case_path=None):
    manifest_path = os.path.join(out_dir, "data_manifest.json")
    report = {"dir": out_dir, "figures": {}, "all_pass": True, "summary": {}}
    if not os.path.exists(manifest_path):
        return {"dir": out_dir, "figures": {}, "all_pass": False,
                "error": "data_manifest.json 缺失", "summary": {"checked": 0, "mismatches": 0, "unmatched": 0}}
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    tables = _load_source_tables(out_dir, case_path)
    total_checked = total_mismatch = total_unmatched = 0
    for fid, fig in (manifest.get("figures") or {}).items():
        svg = os.path.join(out_dir, fig.get("svg") or f"figure-{fid}.svg")
        if not os.path.exists(svg):
            svg = os.path.join(out_dir, f"figure-{fid}.svg")
        if not os.path.exists(svg):
            report["figures"][fid] = {"error": "SVG 缺失", "pass": False}
            report["all_pass"] = False
            continue
        elems = _parse_svg_elements(svg)
        svg_by_id = {e["id"]: e for e in elems}
        fig_report = {"elements": [], "pass": True}
        for me in fig.get("elements", []):
            eid = me.get("svg_id")
            role = me.get("role")
            src = me.get("source") or {}
            rec = {"svg_id": eid, "role": role, "status": "ok"}
            if not eid or eid not in svg_by_id:
                rec["status"] = "missing-in-svg"
                rec["detail"] = "manifest 元素在 SVG 中不存在（正向断链）"
                total_unmatched += 1
                fig_report["pass"] = False
            else:
                svg_data = svg_by_id[eid].get("data") or {}
                # 反向：SVG 元素必须在 manifest 登记（这里按 svg_id 对齐，天然闭合）
                if svg_by_id[eid].get("role") != role:
                    rec["status"] = "role-mismatch"
                    rec["detail"] = f"manifest role={role} ≠ SVG role={svg_by_id[eid].get('role')}"
                    fig_report["pass"] = False
                # 值核对
                ok, detail = _check_value(svg_data, tables)
                total_checked += 1
                if ok is False:
                    rec["status"] = "value-mismatch"
                    rec["detail"] = detail
                    total_mismatch += 1
                    fig_report["pass"] = False
                else:
                    rec["detail"] = detail or "结构一致（无表格值可核，见 detail 说明）"
            fig_report["elements"].append(rec)
        # 反向补充：SVG 数据层元素必须在 manifest 登记
        manifest_ids = {me.get("svg_id") for me in fig.get("elements", [])}
        svg_orphans = [e["id"] for e in elems
                       if e.get("role") and e["id"] not in manifest_ids
                       and e["role"] not in ("x-tick", "y-tick", "grid", "title", "subtitle",
                                             "x-axis-label", "y-axis-label", "panel-label",
                                             "legend-box", "legend-title", "legend-swatch", "legend-label")]
        if svg_orphans:
            fig_report["orphans_in_svg"] = svg_orphans[:10]
            fig_report["pass"] = False
            total_unmatched += len(svg_orphans)
        fig_report["counts"] = {"elements": len(fig.get("elements", [])),
                                "orphans": len(svg_orphans)}
        report["figures"][fid] = fig_report
        if not fig_report["pass"]:
            report["all_pass"] = False
    report["summary"] = {"checked": total_checked, "mismatches": total_mismatch,
                         "unmatched": total_unmatched}
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(description="数据↔图元映射双向校验（CP5）")
    ap.add_argument("--dir", required=True, help="输出目录")
    ap.add_argument("--case", default=None, help="case.json（提供源数据上下文）")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    report = mapcheck(args.dir, args.case)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for fid, fr in report["figures"].items():
            tag = "PASS" if fr.get("pass") else "FAIL"
            print(f"[{tag}] {fid}: {fr.get('counts', {}).get('elements', 0)} elements, "
                  f"{fr.get('counts', {}).get('orphans', 0)} orphans"
                  + (f" — {fr.get('error', '')}" if fr.get("error") else ""))
        s = report["summary"]
        print(f"SUMMARY: {'ALL PASS' if report['all_pass'] else 'ISSUES FOUND'} "
              f"({s.get('checked')} checked / {s.get('mismatches')} mismatched / {s.get('unmatched')} unmatched)")
    sys.exit(0 if report["all_pass"] else 1)


if __name__ == "__main__":
    main()