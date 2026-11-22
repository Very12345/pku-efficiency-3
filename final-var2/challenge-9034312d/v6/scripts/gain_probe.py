# -*- coding: utf-8 -*-
"""gain_probe.py — 指标 Q1–Q6 的独立复算器（v3 机制与复用显性化包）。

本文件在 v3 里的角色是「机制价值的量尺」：Q1 量 M1（证据中间层）、
Q4/Q5 量 M2（确定性布局与真实导出件）、Q3 量 M3（规则审计），
Q2/Q6 量结构正确性与状态诚实性。机制原文见 references/MECHANISM.md。

它只读两类**公开输入**：
  ① 一次运行产出的 `result.json`（外加同目录的 `figure.svg`/`figure.png`/`figure.pdf`）；
  ② 可选的"下界目录"（对照条件 C0 的输出目录，含 `figure.svg`）。
**不 import 本包任何模块**，所以这份复算器可以直接拿去核别人的同类包——
只要对方的 `result.json` 也有 `entities`/`relations`/`evidence`/`verify` 这几个字段。

指标定义（与 references/GAIN-PROTOCOL.md §3.3 完全一致）:
  Q1 来源绑定率      = 有 locator 的 evidence 条数 ÷ (输出实体数 + 输出关系数)
  Q2 断头端点外露数  = 输出关系里 from/to 不在输出实体集合内的条数
  Q3 违规暴露数      = len(verify.errors) + len(verify.warnings)
  Q4 可编辑源文件    = verify.checks.editable_text 与 verify.checks.entity_groups
  Q5 真实导出件      = figure.png / figure.pdf 的字节数（0 = 占位，不算真实导出）
  Q6 状态诚实性      = verify.ok 为 false 时 status 是否为 partial/failed

用法:
    python "$SKILL_DIR/scripts/gain_probe.py" --result <result.json> [--baseline <C0 输出目录>] [--json <报告路径>]

退出码: 0 = 复算完成（不代表指标达标）；2 = 参数文件不存在。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

sys.dont_write_bytecode = True


def _sha16(path):
    if not path or not os.path.isfile(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def _size(path):
    return os.path.getsize(path) if path and os.path.isfile(path) else 0


def probe(result_path: str, baseline_dir: str = None) -> dict:
    with open(result_path, "r", encoding="utf-8") as fh:
        r = json.load(fh)
    d = os.path.dirname(os.path.abspath(result_path))

    ents = r.get("entities") or []
    rels = r.get("relations") or []
    ids = {e.get("id") for e in ents}
    items = (r.get("evidence") or {}).get("items") or []
    verify = r.get("verify") or {}
    checks = verify.get("checks") or {}
    errors = verify.get("errors") or []
    warnings = verify.get("warnings") or []

    png = os.path.join(d, "figure.png")
    pdf = os.path.join(d, "figure.pdf")
    svg = os.path.join(d, "figure.svg")

    out = {
        "result_json": os.path.abspath(result_path),
        "case_id": r.get("case_id"),
        "status": r.get("status"),
        "Q1_source_bound_rate": round(sum(1 for i in items if i.get("locator")) /
                                      max(1, len(ents) + len(rels)), 3),
        "Q1_evidence_items": len(items),
        "Q1_denominator": len(ents) + len(rels),
        "Q2_dangling_exposed": sum(1 for x in rels
                                   if x.get("from") not in ids or x.get("to") not in ids),
        "Q3_violations_exposed": len(errors) + len(warnings),
        "Q3_errors": [e.get("rule") for e in errors],
        "Q3_warnings": [w.get("rule") for w in warnings],
        "Q4_editable_text": checks.get("editable_text"),
        "Q4_entity_groups": checks.get("entity_groups"),
        "Q4_entity_source_coverage": checks.get("entity_source_coverage"),
        "Q5_png_bytes": _size(png),
        "Q5_pdf_bytes": _size(pdf),
        "Q5_png_sha16": _sha16(png),
        "Q6_status_honest": (r.get("status") in ("partial", "failed")) if not verify.get("ok")
                            else (r.get("status") == "success"),
        "svg_sha16": _sha16(svg),
        "layout_sha16": _sha16(os.path.join(d, "layout.json")),
        "verify_sha16": _sha16(os.path.join(d, "verify_report.json")),
        "uncertainty_scopes": [u.get("scope") for u in r.get("uncertainty") or []],
    }

    if baseline_dir:
        bsvg = os.path.join(baseline_dir, "figure.svg")
        out["baseline"] = {
            "dir": os.path.abspath(baseline_dir),
            "svg_bytes": _size(bsvg),
            "svg_text_elems": open(bsvg, encoding="utf-8", errors="replace").read().count("<text")
                              if os.path.isfile(bsvg) else 0,
            "has_layout_json": os.path.isfile(os.path.join(baseline_dir, "layout.json")),
            "has_result_json": os.path.isfile(os.path.join(baseline_dir, "result.json")),
            "png_bytes": _size(os.path.join(baseline_dir, "figure.png")),
            "pdf_bytes": _size(os.path.join(baseline_dir, "figure.pdf")),
        }
    return out


def main(argv) -> int:
    ap = argparse.ArgumentParser(description="Q1–Q6 增益指标独立复算器（只用公开字段）")
    ap.add_argument("--result", required=True, help="一次运行的 result.json")
    ap.add_argument("--baseline", default=None, help="可选的 C0 下界输出目录")
    ap.add_argument("--json", default=None, help="把复算结果写成 JSON")
    args = ap.parse_args(argv)

    if not os.path.isfile(args.result):
        print(f"FATAL: result.json 不存在: {args.result}", file=sys.stderr)
        return 2
    rep = probe(args.result, args.baseline)
    text = json.dumps(rep, ensure_ascii=False, indent=2)
    print(text)
    if args.json:
        with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
