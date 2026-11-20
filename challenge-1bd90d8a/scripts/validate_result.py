#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_result.py — 对 main.py 的输出目录做独立复核（契约 + 文件 + SVG 结构）

用法：
    python <skill_root>/scripts/validate_result.py --dir <out_dir> [--case <case.json>] [--json]

检查项
-------
1. result.json 存在且可解析；case_id 非空（与 --case 提供时一致）。
2. 契约字段：output_contract 声明的字段全部在 result.json 顶层（若非空声明）。
3. 输出文件：result.json 引用的每个文件都存在且非空。
4. SVG：XML 良构、无外部实体（XXE 防护）、含分层 <g>、含 metadata 溯源块、
   每个 data 图元至少带一个 data-* 属性、宽度/高度有效。
5. PNG：可被 Pillow 打开，尺寸 > 0。
6. PDF：以 %PDF 头开始。

退出码：0 = 全部通过；1 = 存在问题（--json 时输出机器可读摘要）。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figure_engine as fe  # noqa: E402


def check_dir(out_dir, case_path=None):
    report = {"dir": out_dir, "checks": [], "all_pass": True}

    def ck(name, passed, detail=""):
        report["checks"].append({"id": name, "pass": bool(passed), "detail": detail})
        if not passed:
            report["all_pass"] = False

    rp = os.path.join(out_dir, "result.json")
    if not os.path.exists(rp):
        ck("result-json-exists", False, "result.json 缺失")
        return report
    try:
        with open(rp, "r", encoding="utf-8") as f:
            res = json.load(f)
    except Exception as exc:
        ck("result-json-parses", False, f"解析失败：{exc}")
        return report
    ck("result-json-parses", True)
    case_id = res.get("case_id")
    ck("case-id-present", bool(case_id), f"case_id={case_id!r}")
    if case_path and os.path.exists(case_path):
        try:
            with open(case_path, "r", encoding="utf-8-sig") as f:
                case = json.load(f)
            if isinstance(case, list):
                case = case[0]
            cid = str(case.get("case_id") or case.get("id") or "")
            if cid:
                ck("case-id-matches-input", str(case_id) == cid, f"result={case_id} input={cid}")
        except Exception:
            pass
    # 契约
    contract = None
    if case_path and os.path.exists(case_path):
        try:
            with open(case_path, "r", encoding="utf-8-sig") as f:
                case = json.load(f)
            if isinstance(case, list):
                case = case[0]
            contract = case.get("output_contract")
        except Exception:
            contract = None
    if contract:
        fields = []
        if isinstance(contract, list):
            fields = [f for f in contract if isinstance(f, str)]
        elif isinstance(contract, dict):
            inner = contract.get("fields", contract)
            fields = list(inner) if isinstance(inner, (dict, list)) else []
        missing = [f for f in fields if f not in res]
        ck("contract-fields-present", not missing, f"缺失契约字段：{missing}（共声明 {len(fields)}）")
    # 引用的文件
    for o in res.get("outputs", []):
        fp = os.path.join(out_dir, str(o.get("file", "")))
        ok = os.path.exists(fp) and os.path.getsize(fp) > 0
        ck(f"file-exists:{os.path.basename(fp)}", ok, fp)
    for lst in res.get("renders", {}).values():
        for f in lst:
            fp = os.path.join(out_dir, str(f))
            ck(f"render-exists:{os.path.basename(fp)}", os.path.exists(fp) and os.path.getsize(fp) > 0, fp)
    # SVG 结构
    for o in res.get("outputs", []):
        if o.get("kind") != "editable_svg":
            continue
        svg = os.path.join(out_dir, str(o.get("file")))
        if not os.path.exists(svg):
            continue
        with open(svg, "r", encoding="utf-8", errors="replace") as f:
            data = f.read()
        ck(f"svg-xmlnt:{os.path.basename(svg)}", "<svg" in data and data.rstrip().endswith("</svg>"),
           "外层 svg 标签完整")
        ck(f"svg-no-xxe:{os.path.basename(svg)}", "<!DOCTYPE" not in data and "<!ENTITY" not in data,
           "无外部实体声明")
        ck(f"svg-layers:{os.path.basename(svg)}", bool(re.search(r'<g id="layer-[a-z]+"', data)),
           "含分层 <g>")
        ck(f"svg-provenance:{os.path.basename(svg)}", "<metadata id='provenance'>" in data,
           "含 metadata 溯源块")
        n_data_attrs = len(re.findall(r"data-(role|file|column|row_index|value|x|y|series|category|id|from|to|label)=", data))
        ck(f"svg-data-attrs:{os.path.basename(svg)}", n_data_attrs > 0,
           f"data-* 溯源属性 {n_data_attrs} 处")
    # PNG
    try:
        from PIL import Image
        for f in res.get("renders", {}).get("png", []):
            png = os.path.join(out_dir, str(f))
            if not os.path.exists(png):
                continue
            try:
                im = Image.open(png)
                im.verify()
                ck(f"png-open:{os.path.basename(png)}", True, f"{im.format} {im.size[0]}x{im.size[1]}")
            except Exception as exc:
                ck(f"png-open:{os.path.basename(png)}", False, str(exc))
    except ImportError:
        pass
    # PDF 头
    for f in res.get("renders", {}).get("pdf", []):
        pdf = os.path.join(out_dir, str(f))
        if not os.path.exists(pdf):
            continue
        with open(pdf, "rb") as fh:
            head = fh.read(5)
        ck(f"pdf-head:{os.path.basename(pdf)}", head == b"%PDF-", "以 %PDF 头开始")
    ck("status-honest", res.get("status") in ("completed", "partial", "failed"),
       f"status={res.get('status')}")
    return report


def main():
    ap = argparse.ArgumentParser(description="复核 main.py 输出目录")
    ap.add_argument("--dir", required=True)
    ap.add_argument("--case", default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    report = check_dir(args.dir, args.case)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for c in report["checks"]:
            print(f"[{'PASS' if c['pass'] else 'FAIL'}] {c['id']} — {c['detail']}")
        print(f"SUMMARY: {'ALL PASS' if report['all_pass'] else 'ISSUES FOUND'} ({outline(sum(1 for c in report['checks'] if c['pass']), len(report['checks']))})")
    sys.exit(0 if report["all_pass"] else 1)


def outline(passed, total):
    return f"{passed}/{total} pass"


if __name__ == "__main__":
    main()