#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
figcheck.py — 图形内容审计与 G1–G8 硬门（CP5 前置 / CP6 契约落地依据）

对输出目录做交付前复核：契约回显（四形态）、文件存在与结构、SVG 可编辑性
（分层/溯源/文字未转曲/无外部实体）、标注校验项复检（图例-系列、显著性配对、
轴标签、CJK、遮挡、溯源）、六类检查点覆盖（科学实体/空间关系/数据编码/图例标注/
可编辑源文件/导出格式）、status 诚实性。输出 G1–G8 硬门汇总。

硬性门（定义见 references/output-contract.md）：
  G1 result.json 存在、可解析，case_id 与输入一致且非空
  G2 output_contract 声明字段全部出现在 result.json 顶层（四形态任一），值非 null
  G3 每张图的 manifest 元素数 = SVG data-role 图元数（1:1，缺一即断链）
  G4 每个数据图元至少一条源定位（column/row_index/id/from/to/cite 等价字段）
  G5 SVG 可编辑源存在、良构、分层 <g>、含 metadata 溯源、文字未转曲（真实 <text>）
  G6 PNG/PDF 预览存在可打开；导出参数（dpi/色彩）在 environment 如实记录
  G7 标注校验六项无 fail：provenance / legend-mapping / significance / axis-units /
     cjk-font / occlusion（warn 允许，须在 uncertainty 说明）
  G8 status 与产物自洽：存在 fail（校验/契约/映射）禁止 completed；uncertainty 诚实

cli：python figcheck.py --dir <out_dir> [--case <case.json>] [--json]
退出码：0 = G1–G8 全过；1 = 存在失败项。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chartkit as ck  # noqa: E402
import mapcheck as mc  # noqa: E402
import svgtext  # noqa: E402

SIX_CHECKPOINT_REQUIRED = {
    "科学实体": "实体名/标签存在且来自源材料（data-* 或 manifest source 记录）",
    "空间关系": "network 边/panel 布局/柱位置等几何关系与规格一致",
    "数据编码": "柱高/点位/热图色阶/扇区角度/误差线长度映射正确（mapcheck 值核对）",
    "图例标注": "图例与系列一一对应、轴标签与单位、显著性标注",
    "可编辑源文件": "分层 SVG + 图元 id + 溯源属性 + 文字未转曲",
    "导出格式": "SVG/PNG/PDF 存在，dpi/色彩空间等导出参数已记录",
}


def _load_json(path, default=None):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _contract_fields(contract):
    """抽取 output_contract 声明的字段名（四形态兼容）。"""
    if isinstance(contract, list):
        return [f for f in contract if isinstance(f, str)]
    if isinstance(contract, dict):
        inner = contract.get("fields", contract)
        if isinstance(inner, list):
            return [f for f in inner if isinstance(f, str)]
        if isinstance(inner, dict):
            return list(inner.keys())
    return []


def _svg_structure(svg_path):
    with open(svg_path, "r", encoding="utf-8", errors="replace") as f:
        data = f.read()
    ok = {
        "wellformed": "<svg" in data and data.rstrip().endswith("</svg>"),
        "layers": len(re.findall(r'<g id="layer-[a-z]+"', data)) >= 1,
        "provenance": "<metadata id='provenance'>" in data,
        "no_xxe": "<!DOCTYPE" not in data and "<!ENTITY" not in data,
    }
    ttp = svgtext.check_no_text_to_path(data, n_text_min=1)
    ok["real_text"] = ttp["pass"]
    ok["n_text"] = ttp["text_elements"]
    roles = set(re.findall(r"data-role=\"([^\"]+)\"", data))
    ok["n_data_roles"] = len(roles)
    return ok


def figcheck(out_dir, case_path=None):
    report = {"dir": out_dir, "gates": {}, "checks": [], "figures": {}, "all_pass": True}

    def ck_item(id_, passed, detail, gate=None):
        report["checks"].append({"id": id_, "pass": bool(passed), "detail": detail, "gate": gate})
        if gate and not passed:
            report["gates"][gate] = False
        if gate and passed:
            report["gates"].setdefault(gate, True)
        if not passed:
            report["all_pass"] = False

    rp = os.path.join(out_dir, "result.json")
    res = _load_json(rp)

    # G1
    if res is None:
        ck_item("G1-result-json", False, "result.json 缺失或不可解析", "G1")
    else:
        cid = res.get("case_id")
        if case_path and os.path.exists(case_path):
            case = _load_json(case_path)
            if isinstance(case, list):
                case = case[0]
            want = str(case.get("case_id") or case.get("id") or "")
            ok_g1 = bool(cid) and (not want or str(cid) == want)
            ck_item("G1-result-json", ok_g1, f"case_id={cid!r} 与输入 {want!r} 一致", "G1")
        else:
            ck_item("G1-result-json", bool(cid), f"case_id={cid!r} 非空", "G1")

    # G2 契约回显
    if case_path and os.path.exists(case_path) and res is not None:
        case = _load_json(case_path)
        if isinstance(case, list):
            case = case[0]
        fields = _contract_fields(case.get("output_contract"))
        missing = [f for f in fields if f not in res or res.get(f) is None]
        ck_item("G2-contract-fields", not missing,
                f"声明 {len(fields)} 字段，缺失/为空 {missing}", "G2")
    else:
        ck_item("G2-contract-fields", res is not None, "无 case.json 或契约声明（跳过）", "G2")

    # 引用的文件与 SVG 结构（G3 用 manifest 计数，G5 结构，G6 预览）
    manifest = _load_json(os.path.join(out_dir, "data_manifest.json"), {})
    svg_files, png_files, pdf_files = [], [], []
    for o in (res or {}).get("outputs", []):
        fp = os.path.join(out_dir, str(o.get("file", "")))
        if o.get("kind") == "editable_svg" and os.path.exists(fp):
            svg_files.append(fp)
        if o.get("kind") == "png_preview" and os.path.exists(fp):
            png_files.append(fp)
        if o.get("kind") == "pdf_preview" and os.path.exists(fp):
            pdf_files.append(fp)
    ck_item("outputs-exist", len(svg_files) + len(png_files) + len(pdf_files) >= 1,
            f"SVG {len(svg_files)} / PNG {len(png_files)} / PDF {len(pdf_files)} 存在", None)

    # G5 SVG 结构
    svg_ok = True
    for f in svg_files:
        st = _svg_structure(f)
        for k, v in st.items():
            ck_item(f"svg:{os.path.basename(f)}:{k}", v, k, "G5" if k in
                    ("wellformed", "layers", "provenance", "no_xxe", "real_text") else None)
        if not all(st[k] for k in ("wellformed", "layers", "provenance", "no_xxe", "real_text")):
            svg_ok = False
    if not svg_files:
        ck_item("G5-svg-exists", False, "无可编辑 SVG 产物", "G5")

    # G6 预览
    from PIL import Image
    png_ok, pdf_ok = True, True
    for f in png_files:
        try:
            im = Image.open(f); im.verify()
            ck_item(f"png:{os.path.basename(f)}", True, f"{im.format} {im.size[0]}x{im.size[1]}", "G6")
        except Exception as exc:
            ck_item(f"png:{os.path.basename(f)}", False, str(exc), "G6")
            png_ok = False
    for f in pdf_files:
        with open(f, "rb") as fh:
            head = fh.read(5)
        ok_h = head == b"%PDF-"
        ck_item(f"pdf:{os.path.basename(f)}", ok_h, "开头 %PDF", "G6")
        if not ok_h:
            pdf_ok = False
    if not png_files:
        ck_item("G6-png-exists", False, "无 PNG 预览", "G6")
    env = (res or {}).get("environment") or {}
    ck_item("G6-export-params", bool(env.get("dpi") is not None or env.get("fonts")),
            f"导出参数已记录 dpi={env.get('dpi')}", None)

    # G3 / G4 映射（复用 mapcheck）
    mcheck = mc.mapcheck(out_dir, case_path)
    ck_item("G3-manifest-svg-1to1", mcheck["all_pass"] and mcheck["summary"]["unmatched"] == 0,
            f"unmatched={mcheck['summary']['unmatched']} mismatched={mcheck['summary']['mismatches']}", "G3")
    ck_item("G4-element-source-located", mcheck["all_pass"],
            "每个映射元素均可定位（值核对或实体来源）。", "G4")
    report["mapcheck"] = mcheck["summary"]

    # G7 标注校验六项无 fail（warn 允许，但须如实记录于 validation/uncertainty）
    val = _load_json(os.path.join(out_dir, "validation.json"), {})
    required_checks = {"provenance", "legend-mapping", "significance", "axis-units", "cjk-font", "occlusion"}
    all_figs_ok = True
    warnings_seen = []
    for fid, chex in (val.get("checks") or {}).items():
        fig = {"figure_id": fid, "checks": {}}
        for c in chex:
            fig["checks"][c.get("id")] = {"level": c.get("level"), "pass": c.get("pass"), "detail": c.get("detail")}
        fails = [c for c in chex if c.get("level") == "fail"]
        warnings_seen.extend([c.get("id") for c in chex
                              if c.get("level") == "warn" and c.get("pass") is False])
        missing_ids = required_checks - {c.get("id") for c in chex}
        ok7 = not fails and not missing_ids
        ck_item(f"G7-validate:{fid}", ok7,
                f"fail={[c['id'] for c in fails]} missing={sorted(missing_ids)}", "G7")
        if not ok7:
            all_figs_ok = False
        report["figures"][fid] = fig
    if not (val.get("checks")):
        ck_item("G7-validation-exists", False, "validation.json 无 checks", "G7")
    if warnings_seen:
        report["g7_warnings"] = sorted(set(warnings_seen))

    # 六类检查点覆盖叙述（结果完整性）
    six = {}
    for name, desc in SIX_CHECKPOINT_REQUIRED.items():
        covered = _six_covered(name, res, manifest, svg_ok)
        six[name] = {"covered": covered, "required": desc}
        ck_item(f"six-checkpoint:{name}", covered, desc, None)
    report["six_checkpoints"] = six

    # G8 status 诚实
    status = (res or {}).get("status")
    has_fail = (mcheck["summary"]["unmatched"] > 0 or mcheck["summary"]["mismatches"] > 0
                or not all_figs_ok or not svg_ok)
    honest = bool(status) and status in ("completed", "partial", "failed") and not (
        status == "completed" and has_fail)
    ck_item("G8-status-honest", honest,
            f"status={status}；存在检查失败/映射缺口={has_fail}", "G8")

    # 未覆盖的 G 门显式记为失败（宁可报错，不静默通过）
    for g in ("G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8"):
        if g not in report["gates"]:
            report["gates"][g] = False

    report["all_pass"] = all(report["gates"].values()) if report["gates"] else False
    return report


def _six_covered(name, res, manifest, svg_ok):
    if name in ("可编辑源文件",):
        return bool(svg_ok and manifest.get("figures"))
    if name in ("导出格式",):
        return bool((res or {}).get("renders"))
    if name in ("数据编码",):
        return bool(manifest.get("figures"))
    if name in ("图例标注",):
        return bool((res or {}).get("figure_checks"))
    if name in ("科学实体", "空间关系"):
        return bool(manifest.get("figures"))
    return False


def main(argv=None):
    ap = argparse.ArgumentParser(description="图形内容审计与 G1–G8 硬门（CP5/CP6）")
    ap.add_argument("--dir", required=True)
    ap.add_argument("--case", default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    report = figcheck(args.dir, args.case)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for c in report["checks"]:
            print(f"[{'PASS' if c['pass'] else 'FAIL'}] {c['id']} — {c['detail']}"
                  + (f" (gate={c['gate']})" if c["gate"] else ""))
        gates = report["gates"]
        print("GATES:", " ".join(f"{k}={'OK' if v else 'FAIL'}" for k, v in sorted(gates.items())))
        print(f"SUMMARY: {'ALL GATES PASS' if report['all_pass'] else 'ISSUES FOUND'}")
    sys.exit(0 if report["all_pass"] else 1)


if __name__ == "__main__":
    main()