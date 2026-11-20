# -*- coding: utf-8 -*-
"""main.py — 图稿 Skill 一键流水线 CLI。

用法（相对技能根目录）:
    python scripts/main.py --case <case.json> [--task <task.md>]
                           [--out <输出目录>] [--dpi 200]
                           [--figure-type route|apparatus|flow|hybrid]
                           [--title 自定标题] [--width-mm 297] [--height-mm 180]

流程: 读真实输入 → 结构化中间表示 → 布局模型 → 可编辑 SVG → PNG/PDF 预览
      → result.json（含 output_contract 全字段 + case_id）→ 交付自查。

本脚本自定位（os.path.dirname(__file__)），不依赖运行时的 cwd。
输出目录默认取 <out>/<case_id>；全部产物写入其中。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
sys.dont_write_bytecode = True  # 评测包内不落 .pyc
import traceback
from typing import Any, Dict, List, Optional

_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

# 控制台 UTF-8（Windows GBK 终端下避免打印乱码）
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

import check as check_mod            # noqa: E402
import export_preview as preview_mod  # noqa: E402
import export_svg as svg_mod          # noqa: E402
import fonts as fonts_mod             # noqa: E402
from layout import compute_layout, layout_to_json, load_palette  # noqa: E402
from model import build_model         # noqa: E402

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_PALETTE = os.path.join(SKILL_ROOT, "templates", "palette.json")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def merge_overrides(model, merge_path: str):
    """应用 Agent 人工修正：覆盖文件为 {"entities":[...], "relations":[...],
    "change_notes":[...]}，按 id 替换同名项，新 id 追加；修正记录进模型级 checklist。"""
    import json as _json
    from model import Entity, Relation  # noqa: F811
    with open(merge_path, "r", encoding="utf-8") as fh:
        data = _json.load(fh)
    applied: List[str] = []

    ent_overrides = {str(e.get("id")): e for e in (data.get("entities") or [])}
    for i, e in enumerate(model.entities):
        if e.id in ent_overrides:
            ov = ent_overrides.pop(e.id)
            model.entities[i] = Entity(
                id=e.id,
                name=str(ov.get("name", e.name)),
                kind=ov.get("kind", e.kind) if ov.get("kind") else e.kind,
                stage=ov.get("stage", e.stage) if ov.get("stage") is not None else e.stage,
                source=ov.get("source", e.source) if ov.get("source") else e.source,
                label=ov.get("label", e.label),
                props=e.props,
            )
            applied.append(f"entity:{e.id}")
    for eid in sorted(ent_overrides):
        ov = ent_overrides[eid]
        model.entities.append(Entity(id=eid, name=str(ov.get("name") or eid),
                                     kind=ov.get("kind") or "step",
                                     stage=ov.get("stage"),
                                     source=ov.get("source"),
                                     label=ov.get("label")))
        applied.append(f"entity:+{eid}")

    rel_overrides = {str(r.get("id")): r for r in (data.get("relations") or [])}
    for i, r in enumerate(model.relations):
        if r.id in rel_overrides:
            ov = rel_overrides.pop(r.id)
            model.relations[i] = Relation(
                id=r.id, from_id=str(ov.get("from", r.from_id)),
                to_id=str(ov.get("to", r.to_id)),
                kind=ov.get("kind", r.kind) if ov.get("kind") else r.kind,
                label=ov.get("label", r.label),
                source=ov.get("source", r.source) if ov.get("source") else r.source,
            )
            applied.append(f"relation:{r.id}")
    for rid in sorted(rel_overrides):
        ov = rel_overrides[rid]
        model.relations.append(Relation(id=rid, from_id=str(ov["from"]),
                                        to_id=str(ov["to"]),
                                        kind=ov.get("kind") or "flow",
                                        label=ov.get("label"), source=ov.get("source")))
        applied.append(f"relation:+{rid}")

    notes = list(data.get("change_notes") or [])
    model.uncertainty.append({
        "scope": "agent_manual_edits",
        "issue": f"Agent 人工修正 {len(applied)} 项: {applied[:8]}{'…' if len(applied)>8 else ''}",
        "action": "; ".join(notes) if notes else "人工修正内容已写入 change_record",
    })
    model.agent_edits = applied  # type: ignore[attr-defined]
    return model


def _rel(out_dir: str, p: str) -> str:
    return os.path.relpath(p, out_dir).replace("\\", "/")


def run_case(case_path: str, task_path: Optional[str], out_root: str, args: argparse.Namespace) -> Dict[str, Any]:
    """执行单个案例全流程，返回 result 摘要。

    --merge 支持：Agent 人工修正的实体/关系覆盖文件（id 相同替换、新 id 追加），
    修正动作会如实写入 change_record（by="agent"）。
    """
    model = build_model(case_path, task_path, figure_type_override=args.figure_type)

    # Agent 修正合并（可选）
    if args.merge:
        model = merge_overrides(model, args.merge)

    # 图面约束：宽度/高度可由 CLI 覆盖（默认取 case.json canvas）
    if args.width_mm:
        model.canvas["width_mm"] = float(args.width_mm)
    if args.height_mm:
        model.canvas["height_mm"] = float(args.height_mm)
    if args.title:
        model.title = args.title

    palette = load_palette(args.palette or TEMPLATE_PALETTE)
    layout = compute_layout(model, palette, font_family=fonts_mod.SVG_FONT_FAMILY)

    out_dir = os.path.join(out_root, model.case_id)
    os.makedirs(out_dir, exist_ok=True)

    # ---------- 1) 结构化中间表示落盘（可复核） ----------
    layout_json_path = os.path.join(out_dir, "layout.json")
    layout_to_json(layout, layout_json_path)

    # ---------- 2) 可编辑 SVG ----------
    svg_path = os.path.join(out_dir, "figure.svg")
    svg_mod.write_svg(layout, svg_path, tool=f"challenge-9034312d/scripts/{os.path.basename(__file__)}")
    svg_sha = sha256_file(svg_path)

    # ---------- 3) 预览 PNG / PDF ----------
    png_info: Dict[str, Any] = {}
    pdf_info: Dict[str, Any] = {}
    png_fail = pdf_fail = None
    try:
        png_info = preview_mod.render_png(layout, os.path.join(out_dir, "figure.png"),
                                          dpi=args.dpi,
                                          ttf_font=fonts_mod.find_ttf_font())
    except Exception as exc:  # noqa: BLE001
        png_fail = str(exc)
    try:
        pdf_info = preview_mod.render_pdf(layout, os.path.join(out_dir, "figure.pdf"))
    except Exception as exc:  # noqa: BLE001
        pdf_fail = str(exc)

    # ---------- 4) result.json（output_contract 全字段 + case_id） ----------
    change_record = [{
        "time": _now_iso(),
        "action": f"运行 {os.path.basename(__file__)}",
        "target": "figure.svg / layout.json / 预览",
        "reason": "初始生成：从输入案例抽取实体与关系后布图",
        "by": "scripts/main.py (自动)",
    }]
    for note in (getattr(model, "agent_edits", None) or []):
        change_record.append({
            "time": _now_iso(),
            "action": "merge 人工修正",
            "target": note,
            "reason": "Agent 依据材料复核/修正实体或关系",
            "by": "agent (--merge)",
        })

    exports = []
    if png_info:
        exports.append({"kind": "png", "path": _rel(out_dir, png_info["file"]),
                        "format": "image/png", "width_px": png_info["width_px"],
                        "height_px": png_info["height_px"], "dpi": png_info["dpi"],
                        "font_ttf": png_info.get("font_ttf")})
    if pdf_info:
        exports.append({"kind": "pdf", "path": _rel(out_dir, pdf_info["file"]),
                        "format": "application/pdf", "vector": True,
                        "font": pdf_info.get("font")})

    result = {
        "case_id": model.case_id,
        "title": model.title,
        "status": _decide_status(model, png_fail, pdf_fail, args),
        "workorder": "apparatus_and_technical_route",
        "figure_type": model.figure_type,
        "extraction": model.extraction,
        "entities": [
            {"id": e.id, "name": e.name, "kind": e.kind, "stage": e.stage,
             "step_no": next((x.get("step_no") for x in layout["entities"] if x["id"] == e.id), None),
             "source": e.source}
            for e in model.entities
        ],
        "relations": [
            {"id": r.id, "from": r.from_id, "to": r.to_id, "kind": r.kind,
             "label": r.label, "source": r.source}
            for r in model.relations
        ],
        "output_contract": {
            "editable_sources": [
                {"kind": "svg", "path": _rel(out_dir, svg_path),
                 "format": "image/svg+xml", "layers": ["title", "arrows", "entities", "legend"],
                 "editability": "text 元素真实文本、实体组带 data-entity/data-source，可被 Inkscape/文本编辑器直接修改",
                 "checksum_sha256": svg_sha}
            ],
            "exports": exports,
            "data_mapping": [
                {"entity_id": e["id"], "kind": e["kind"], "source": e["source"],
                 "svg_group": f"entity-{e['id']}"}
                for e in layout["entities"]
            ],
            "element_traceability": [
                {"element": f"entity-{e['id']}", "source": e.get("source"),
                 "kind": e.get("kind"), "stage": e.get("stage")}
                for e in layout["entities"]
            ] + [
                {"element": f"arrow-{r['id']}", "from": r["from"], "to": r["to"],
                 "source": r.get("source")}
                for r in layout["relations"]
            ],
        },
        "canvas": {"width_mm": layout["canvas"]["width_mm"],
                   "height_mm": layout["canvas"]["height_mm"],
                   "requested": model.canvas},
        "fonts": fonts_mod.font_report(),
        "sources": [
            {"id": s.id, "file": s.file, "note": s.note} for s in model.sources
        ],
        "uncertainty": model.uncertainty + [
            u for u in ([
                {"scope": "png", "issue": f"PNG 渲染失败: {png_fail}"} if png_fail else None,
                {"scope": "pdf", "issue": f"PDF 渲染失败: {pdf_fail}"} if pdf_fail else None,
                {"scope": "fonts", "issue": "本机未找到中文字体，PNG 预览可能缺字"} if not fonts_mod.is_cjk_supported() and not png_fail else None,
            ] if (png_fail or pdf_fail or not fonts_mod.is_cjk_supported()) else [])
        ],
        "change_record": change_record,
        "execution": {
            "script": os.path.basename(__file__),
            "python": sys.version.split()[0],
            "out_dir": out_root,
        },
        "checksum": hashlib.sha256(json.dumps({
            "case_id": model.case_id, "entities": [e.id for e in model.entities],
            "relations": [r.id for r in model.relations],
            "svg_sha": svg_sha,
        }, sort_keys=True).encode("utf-8")).hexdigest(),
    }

    result_path = os.path.join(out_dir, "result.json")
    with open(result_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)

    return {"result_path": result_path, "out_dir": out_dir, "result": result}


def _decide_status(model, png_fail, pdf_fail, args) -> str:
    if model.extraction == "text-heuristic" and not model.entities:
        return "failed"
    if png_fail and pdf_fail:
        return "partial" if model.entities else "failed"
    if png_fail or pdf_fail:
        return "partial"
    if model.uncertainty and any("orphan" in (u.get("scope") or "") for u in model.uncertainty):
        return "partial"  # 有遗漏风险，诚实降级
    return "success"


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="科研图稿 Skill：装置/技术路线图生成")
    ap.add_argument("--case", required=True, help="case.json 路径（真实输入）")
    ap.add_argument("--task", default=None, help="task.md 路径（可选）")
    ap.add_argument("--out", default="output", help="输出根目录（默认 ./output）")
    ap.add_argument("--dpi", type=int, default=200, help="PNG DPI（默认 200）")
    ap.add_argument("--figure-type", default=None,
                    choices=["route", "apparatus", "flow", "hybrid"],
                    help="覆盖图类（默认按案例推断）")
    ap.add_argument("--title", default=None, help="覆盖标题")
    ap.add_argument("--width-mm", type=float, default=0.0, help="画布宽 mm")
    ap.add_argument("--height-mm", type=float, default=0.0, help="画布高 mm")
    ap.add_argument("--palette", default=None, help="自定义 palette.json 路径")
    ap.add_argument("--merge", default=None,
                    help="Agent 人工修正 JSON：{\"entities\":[{id,...}],\"relations\":[{id,...}],\"change_notes\":[\"...\"]}")
    args = ap.parse_args(argv)

    if not os.path.isfile(args.case):
        print(f"FATAL: case.json 不存在: {args.case}", file=sys.stderr)
        return 2

    try:
        run = run_case(args.case, args.task, os.path.abspath(args.out), args)
    except Exception as exc:  # noqa: BLE001
        print("FATAL: 流水线异常", file=sys.stderr)
        traceback.print_exc()
        # 仍然落盘一个诚实的失败 result.json
        try:
            os.makedirs(os.path.join(os.path.abspath(args.out), "failed"), exist_ok=True)
            with open(os.path.join(os.path.abspath(args.out), "failed", "result.json"),
                      "w", encoding="utf-8", newline="\n") as fh:
                json.dump({
                    "case_id": os.path.basename(args.case),
                    "status": "failed",
                    "error": str(exc),
                    "output_contract": {
                        "editable_sources": [], "exports": [],
                        "data_mapping": [], "element_traceability": [],
                    },
                    "sources": [], "uncertainty": [{"scope": "pipeline", "issue": str(exc)}],
                    "change_record": [], "checksum": "",
                }, fh, ensure_ascii=False, indent=2)
        except Exception:  # noqa: BLE001
            pass
        return 1

    # 交付自查
    check_res = check_mod.check_result(run["result_path"])
    print(json.dumps({
        "case_id": run["result"]["case_id"],
        "status": run["result"]["status"],
        "out_dir": run["out_dir"],
        "artifacts": sorted(os.listdir(run["out_dir"])),
        "issues": check_res["issues"],
        "check_ok": check_res["ok"],
    }, ensure_ascii=False, indent=2))
    return 0 if check_res["ok"] else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))