#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gain_harness.py — 「加载本 Skill」与「不加载 Skill 的基础做法」之间的只读对照测量器。

定位（重要）：
  * 本脚本 **不生成任何图**，**不参与 `scripts/main.py` 出图流水线**，只读取一个输出目录，
    把它折算成同一组结构化指标。它存在的唯一理由是让「使用增益」可被第三方复算。
  * 只依赖 Python 标准库（`json/re/os/sys/glob/xml.etree`），不需要 matplotlib/Pillow。

两种用法：

  1) 单条件测量
     python gain_harness.py --out <输出目录> [--case <case.json>] [--material <材料文件>]
                            [--label A] [--json <报告.json>]

  2) 确定性/一致性对比（同输入跑两次后比较结构指纹）
     python gain_harness.py --compare <目录1> <目录2>

指标口径（全部可由本脚本复算，不接受自述）：
  editable.layers            SVG 中 `<g id="layer:*">` 分层组数（0 = 无分层，无从定位再编辑）
  editable.text_nodes        真 `<text>` 文字节点数（可直接改字）
  editable.glyph_use_nodes   `<use>` 字形引用数（>0 说明文字被轮廓化，改字必须回原工具）
  provenance.src_attrs       带 `data-src` 的元素数（机器可读的来源挂接）
  provenance.science_elems   科学元素数（`data-role` 以 entity:/relation:/datum:/icon 开头）
  provenance.coverage        src_attrs / science_elems（无科学元素时记 0）
  four_elements.on_canvas    图面可检测到的面板语义数 / 4（研究问题/方法/结果/结论）
  numbers.on_canvas          图面数值标签数（从 SVG `<text>` 抽取）
  numbers.found_in_material  其中能在材料原文里定位到的个数（字符串级）
  contract.expected/covered  案例 `output_contract` 字段数 / result.json 顶层非空覆盖数
  contract.missing_or_null   未覆盖或为 null 的字段清单
  contract.verdict           "complete" | "partial" | "absent"
  evidence.result_json       result.json 是否存在（无 → 复核者只能目视位图）
  evidence.audit_json        audit.json 是否存在（结构化自查证据）
  evidence.render_log        render_log.json 是否存在（后端/字体降级是否如实记录）

退出码：0 = 测量完成（无论条件好坏）；1 = 参数错误；2 = 输出目录不存在。
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

TEXT_EXT = (".md", ".txt", ".json", ".csv", ".tex", ".rst")
NUM_RE = re.compile(r"\d+(?:[.,]\d+)?")
PANEL_MARKERS = {
    "question": ("研究问题", "问题", "question", "背景"),
    "method": ("方法", "机制", "method", "路线"),
    "results": ("结果", "results", "数据"),
    "conclusion": ("结论", "conclusion", "总结"),
}


def _load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def _read_text(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except Exception:
        return ""


def _find_svg(out_dir):
    hits = sorted(glob.glob(os.path.join(out_dir, "*.svg")))
    return hits[0] if hits else None


def _svg_metrics(svg_path):
    m = {"layers": 0, "layer_names": [], "text_nodes": 0, "glyph_use_nodes": 0,
         "src_attrs": 0, "science_elems": 0, "texts": []}
    if not svg_path:
        return m
    raw = _read_text(svg_path)
    m["layers"] = len(re.findall(r'<g[^>]*\bid="layer:[^"]+"', raw))
    m["layer_names"] = sorted(set(re.findall(r'<g[^>]*\bid="(layer:[^"]+)"', raw)))
    m["text_nodes"] = len(re.findall(r"<text[\s>]", raw))
    m["glyph_use_nodes"] = len(re.findall(r"<use[\s>]", raw))
    m["src_attrs"] = len(re.findall(r'data-src="', raw))
    m["science_elems"] = len(re.findall(r'data-role="(?:entity|relation|datum|icon)[^"]*"', raw))
    try:
        root = ET.fromstring(raw)
    except Exception:
        return m
    for node in root.iter():
        tag = node.tag.split("}")[-1]
        if tag == "text":
            txt = "".join(node.itertext()).strip()
            if txt:
                m["texts"].append(txt)
    return m


def _material_text(material):
    """材料可为单文件或目录；目录时合并其中全部文本文件。"""
    if not material:
        return ""
    if os.path.isdir(material):
        chunks = []
        for root, _dirs, names in os.walk(material):
            for name in sorted(names):
                if name.lower().endswith(TEXT_EXT):
                    chunks.append(_read_text(os.path.join(root, name)))
        return "\n".join(chunks)
    return _read_text(material)


def _number_metrics(texts, material_text):
    on_canvas, located = [], []
    seen = set()
    for txt in texts:
        for token in NUM_RE.findall(txt):
            if token in seen:
                continue
            seen.add(token)
            on_canvas.append(token)
            if token in material_text:
                located.append(token)
    return {"on_canvas": len(on_canvas), "found_in_material": len(located),
            "unlocated": [t for t in on_canvas if t not in located][:12]}


def _four_element_metrics(blob):
    found = []
    for panel, markers in PANEL_MARKERS.items():
        if any(mk in blob for mk in markers):
            found.append(panel)
    return {"on_canvas": len(found), "panels": sorted(found), "expected": 4}


def _contract_metrics(out_dir, case):
    result = _load_json(os.path.join(out_dir, "result.json"))
    expected = {}
    if isinstance(case, dict):
        oc = case.get("output_contract")
        if isinstance(oc, dict):
            expected = oc
        elif isinstance(oc, str):
            expected = {"output_contract_note": oc}
    covered, missing = [], []
    for key in expected:
        if isinstance(result, dict) and key in result and result[key] is not None:
            covered.append(key)
        else:
            missing.append(key)
    if result is None:
        verdict = "absent"
    elif expected and not missing:
        verdict = "complete"
    elif covered:
        verdict = "partial"
    else:
        verdict = "absent"
    return {"expected": len(expected), "covered": len(covered),
            "missing_or_null": missing, "verdict": verdict,
            "result_toplevel_keys": len(result) if isinstance(result, dict) else 0}


def measure(out_dir, case_path=None, material_path=None, label=None):
    out_dir = os.path.abspath(out_dir)
    case = _load_json(case_path) if case_path else None
    svg_path = _find_svg(out_dir)
    svg = _svg_metrics(svg_path)
    material_text = _material_text(material_path)
    blob = "\n".join(svg["texts"]) + "\n" + _read_text(os.path.join(out_dir, "result.json"))
    report = {
        "label": label or os.path.basename(out_dir.rstrip("/\\")),
        "out_dir_basename": os.path.basename(out_dir.rstrip("/\\")),
        "files": sorted(os.path.basename(p) for p in glob.glob(os.path.join(out_dir, "*"))),
        "editable": {"layers": svg["layers"], "layer_names": svg["layer_names"],
                     "text_nodes": svg["text_nodes"],
                     "glyph_use_nodes": svg["glyph_use_nodes"]},
        "provenance": {"src_attrs": svg["src_attrs"], "science_elems": svg["science_elems"],
                       "coverage": round(svg["src_attrs"] / svg["science_elems"], 3)
                       if svg["science_elems"] else 0.0},
        "four_elements": _four_element_metrics(blob),
        "numbers": _number_metrics(svg["texts"], material_text),
        "contract": _contract_metrics(out_dir, case),
        "evidence": {
            "result_json": os.path.isfile(os.path.join(out_dir, "result.json")),
            "audit_json": os.path.isfile(os.path.join(out_dir, "audit.json")),
            "render_log": os.path.isfile(os.path.join(out_dir, "render_log.json")),
            "spec_json": os.path.isfile(os.path.join(out_dir, "spec.json")),
        },
    }
    return report


def _fingerprint(out_dir):
    """结构指纹：不看时间戳/文件字节，只看图面结构与契约字段。"""
    svg_path = _find_svg(out_dir)
    svg = _svg_metrics(svg_path)
    result = _load_json(os.path.join(out_dir, "result.json")) or {}
    spec_sha = None
    audit = _load_json(os.path.join(out_dir, "audit.json")) or {}
    try:
        spec_sha = audit["determinism_probe"]["spec_sha16"]
    except Exception:
        spec_sha = None
    return {
        "layers": svg["layers"],
        "text_nodes": svg["text_nodes"],
        "src_attrs": svg["src_attrs"],
        "science_elems": svg["science_elems"],
        "texts_sorted": sorted(svg["texts"]),
        "result_toplevel_keys": sorted(result.keys()),
        "spec_sha16": spec_sha,
    }


def compare(dir_a, dir_b):
    fa, fb = _fingerprint(dir_a), _fingerprint(dir_b)
    diffs = {k: {"a": fa[k], "b": fb[k]} for k in fa if fa[k] != fb[k]}
    return {"dir_a": os.path.basename(os.path.abspath(dir_a)),
            "dir_b": os.path.basename(os.path.abspath(dir_b)),
            "structure_identical": not diffs,
            "diff_keys": sorted(diffs.keys()),
            "detail": diffs if diffs else "结构指纹逐项一致（同输入同布局）"}


def main(argv=None):
    ap = argparse.ArgumentParser(description="GAIN 对照测量器（只读，不出图）")
    ap.add_argument("--out", default=None, help="待测量的输出目录")
    ap.add_argument("--case", default=None, help="case.json（取 output_contract 期望字段）")
    ap.add_argument("--material", default=None, help="材料文件或材料目录（数值可定位性）")
    ap.add_argument("--label", default=None, help="条件名（A=加载 Skill / B=基础做法）")
    ap.add_argument("--json", dest="json_out", default=None, help="把报告写入该路径")
    ap.add_argument("--compare", nargs=2, metavar=("DIR_A", "DIR_B"),
                    help="比较两个输出目录的结构指纹（确定性）")
    args = ap.parse_args(argv)

    if args.compare:
        a, b = args.compare
        for d in (a, b):
            if not os.path.isdir(d):
                print(json.dumps({"error": "not a directory: " + d}, ensure_ascii=False))
                return 2
        report = compare(a, b)
    else:
        if not args.out:
            ap.print_help()
            return 1
        if not os.path.isdir(args.out):
            print(json.dumps({"error": "not a directory: " + args.out}, ensure_ascii=False))
            return 2
        report = measure(args.out, args.case, args.material, args.label)

    text = json.dumps(report, ensure_ascii=False, indent=2)
    print(text)
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text + "\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
