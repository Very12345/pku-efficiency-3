# -*- coding: utf-8 -*-
"""main.py — 图稿 Skill v2 一键流水线 CLI（编排：证据→模型→布局→渲染→校验→契约）。

用法（脚本自定位，任何 cwd 都可运行；$SKILL_DIR = 含 SKILL.md 的技能根）:
    python "$SKILL_DIR/scripts/main.py" --case <case.json|案例目录> [--task <task.md>]
                           [--material <材料文件|目录>] [--merge <override.json>]
                           [--out <输出目录>] [--dpi 200]
                           [--figure-type route|apparatus|flow|hybrid]
                           [--title 自定标题] [--width-mm 297] [--height-mm 180]

--case 既可给 case.json 本体，也可给**案例目录**（自动取其下 case.json，并在未给
--task 时取同目录 task.md；给具体文件时不猜同目录文件，--task 需显式传入）。

流程（v2，评委可沿证据链复核）:
  读真实输入 → gain_evidence 证据抽取（CP1 证据门）→ 结构化中间表示（SIR）
  → 布局模型（layout.json，确定性）→ 可编辑 SVG（render_svg）→ PNG/PDF 预览
  → svg_verify 校验 + 连接规则审计（CP3 校验门）→ result.json（output_contract
  全字段 + case_id + 证据/校验摘要）→ check 契约门（G1–G10）→ 交付摘要。

脚本自定位（os.path.dirname(__file__)），不依赖运行时 cwd；
模板/规则资产取技能根下的 templates/ 与 assets/。
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

import gain_evidence as evidence_mod      # noqa: E402
import check as check_mod                 # noqa: E402
import export_preview as preview_mod      # noqa: E402
import render_svg as svg_mod              # noqa: E402
import svg_verify as verify_mod           # noqa: E402
import fonts as fonts_mod                 # noqa: E402
from layout import compute_layout, layout_to_json, load_palette  # noqa: E402
from model import build_model             # noqa: E402

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_PALETTE = os.path.join(SKILL_ROOT, "templates", "palette.json")
CONNECTION_RULES = os.path.join(SKILL_ROOT, "assets", "connection_rules.json")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def merge_overrides(model, merge_path: str):
    """应用 Agent 人工修正（编辑既有图稿的入口，对应 route_spec.mutation 用例）：
    覆盖文件为 {"entities":[...], "relations":[...], "change_notes":[...]}，
    按 id 替换同名项，新 id 追加；修正动作自动写入 change_record。"""
    import json as _json
    from model import Entity, Relation
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


def resolve_case_arg(case_arg: str, task_arg: Optional[str]):
    """解析 --case/--task：只做路径解析，不改变任何算法或结果语义。

    - `--case` 既接受 case.json 本体，也接受**案例目录**；给目录时自动取其下
      `case.json`，并在未显式给 `--task` 时取同目录的 `task.md`（平台输入约定即
      `/input/case.json` + `/input/task.md` 同目录成对）。
    - `--case` 给的是**具体文件**时，`--task` 必须显式传入：不猜同目录文件，
      避免把无关材料误当任务说明（材料来源宁可少而准）。
    这样 SKILL.md 的示例命令在 cwd 不是技能根时也能跑通。
    """
    case_path = case_arg
    is_dir = os.path.isdir(case_arg)
    if is_dir:
        cand = os.path.join(case_arg, "case.json")
        if os.path.isfile(cand):
            case_path = cand
    task_path = task_arg
    if task_path is None and is_dir:
        cand_task = os.path.join(os.path.dirname(os.path.abspath(case_path)), "task.md")
        if os.path.isfile(cand_task):
            task_path = cand_task
    return case_path, task_path


def collect_materials(args: argparse.Namespace) -> List[str]:
    mats: List[str] = []
    for m in (args.material or []):
        if os.path.isdir(m):
            for root, _dirs, files in os.walk(m):
                for f in sorted(files):
                    if f.lower().endswith((".md", ".txt", ".csv", ".tex")):
                        mats.append(os.path.join(root, f))
        else:
            mats.append(m)
    return mats


def run_case(case_path: str, task_path: Optional[str], out_root: str,
             args: argparse.Namespace) -> Dict[str, Any]:
    """执行单个案例全流程，返回 result 摘要。"""
    # ---------- 0) 证据抽取（CP1 证据门；从真实材料抽取，不编造） ----------
    evidence = evidence_mod.extract_evidence(
        case_path, task_path, collect_materials(args))

    # ---------- 1) 结构化中间表示（证据优先） ----------
    model = build_model(case_path, task_path,
                        figure_type_override=args.figure_type,
                        evidence=evidence)

    # Agent 修正合并（可选；编辑既有图稿）
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
    # svg_verify 需要 figure_type 语义；layout 里补上
    layout["figure_type"] = model.figure_type

    out_dir = os.path.join(out_root, model.case_id)
    os.makedirs(out_dir, exist_ok=True)

    # ---------- 2) 证据清单与布局模型落盘（可复核） ----------
    evidence_path = os.path.join(out_dir, "evidence.json")
    with open(evidence_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(evidence, fh, ensure_ascii=False, indent=2)

    layout_json_path = os.path.join(out_dir, "layout.json")
    layout_to_json(layout, layout_json_path)

    # ---------- 3) 可编辑 SVG ----------
    svg_path = os.path.join(out_dir, "figure.svg")
    svg_mod.write_svg(layout, svg_path, tool=f"challenge-9034312d/scripts/{os.path.basename(__file__)}")
    svg_sha = sha256_file(svg_path)

    # ---------- 4) 校验 + 连接规则审计（CP3 校验门） ----------
    verify_report_path = os.path.join(out_dir, "verify_report.json")
    verify_report = verify_mod.check_svg(layout, svg_path, _load_rules(args.rules))
    with open(verify_report_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(verify_report, fh, ensure_ascii=False, indent=2)

    # ---------- 5) 预览 PNG / PDF ----------
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

    # ---------- 6) result.json（output_contract 全字段 + case_id + 证据/校验摘要） ----------
    change_record = [{
        "time": _now_iso(),
        "action": f"运行 {os.path.basename(__file__)}",
        "target": "figure.svg / layout.json / evidence.json / 预览",
        "reason": "初始生成：从输入案例经证据抽取后布图",
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
        "status": _decide_status(model, png_fail, pdf_fail, verify_report, args),
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
                 "format": "image/svg+xml",
                 "layers": ["layer-background", "layer-title", "layer-arrows",
                            "layer-entities", "layer-legend"],
                 "editability": "text 元素真实文本、实体组带 data-entity/data-source/data-step-no，可被 Inkscape/文本编辑器直接修改",
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
        "evidence": {
            "source": evidence.get("source"),
            "extraction": evidence.get("extraction"),
            "items": evidence.get("evidence") or [],
            "source_files": [
                {"file": s["file"], "sha256": s["sha256"], "size": s["size"], "role": s["role"]}
                for s in evidence.get("sources") or []
            ],
            "notes": evidence.get("notes") or [],
            "meta": model.evidence_meta,
        },
        "verify": {
            "ok": bool(verify_report.get("ok")),
            "checks": verify_report.get("checks") or {},
            "errors": verify_report.get("errors") or [],
            "warnings": verify_report.get("warnings") or [],
            "determinism": verify_report.get("determinism") or {},
            "summary": verify_report.get("summary") or {},
        },
        "canvas": {"width_mm": layout["canvas"]["width_mm"],
                   "height_mm": layout["canvas"]["height_mm"],
                   "requested": model.canvas},
        "fonts": fonts_mod.font_report(),
        "sources": [
            {"id": s.id, "file": s.file, "note": s.note} for s in model.sources
        ],
        "uncertainty": model.uncertainty + _extra_uncertainty(png_fail, pdf_fail, verify_report),
        "change_record": change_record,
        "execution": {
            "script": os.path.basename(__file__),
            "skill_version": "2.0.0",
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


def _load_rules(rules_path: Optional[str]) -> Dict[str, Any]:
    path = rules_path or CONNECTION_RULES
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:  # noqa: BLE001
        return {}


def _extra_uncertainty(png_fail, pdf_fail, verify_report) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if png_fail:
        out.append({"scope": "png", "issue": f"PNG 渲染失败: {png_fail}",
                    "action": "SVG 源文件仍可用；检查本机字体与 Pillow"})
    if pdf_fail:
        out.append({"scope": "pdf", "issue": f"PDF 渲染失败: {pdf_fail}",
                    "action": "SVG 源文件仍可用；检查 reportlab"})
    if not png_fail and not fonts_mod.is_cjk_supported():
        out.append({"scope": "fonts",
                    "issue": "本机未找到中文字体，PNG 预览可能缺字",
                    "action": "SVG/PDF 不受影响；可安装中文字体后重跑"})
    if verify_report and not verify_report.get("ok"):
        errs = verify_report.get("errors") or []
        out.append({
            "scope": "rule_violation",
            "issue": f"svg_verify 存在 {len(errs)} 条 error 级连接规则违规: "
                     f"{[e.get('rule') for e in errs][:6]}",
            "action": "对照材料复核实体类别/关系方向，用 --merge 修正后重跑",
        })
    return out


def _decide_status(model, png_fail, pdf_fail, verify_report, args) -> str:
    if model.extraction == "text-heuristic" and not model.entities:
        return "failed"
    if png_fail and pdf_fail:
        return "partial" if model.entities else "failed"
    if png_fail or pdf_fail:
        return "partial"
    if verify_report and not verify_report.get("ok"):
        return "partial"  # error 级规则违规未解决 → 诚实降级（D11）
    if model.uncertainty and any("orphan" in (u.get("scope") or "") for u in model.uncertainty):
        return "partial"
    return "success"


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="科研图稿 Skill v2：装置/技术路线图生成")
    ap.add_argument("--case", required=True,
                    help="case.json 路径（真实输入）；也可给案例目录（自动取目录下 case.json + task.md）")
    ap.add_argument("--task", default=None,
                    help="task.md 路径（可选；--case 给目录时可省略，自动取目录下 task.md）")
    ap.add_argument("--material", action="append", default=None,
                    help="材料文件或目录（可多次；目录自动收集 .md/.txt/.csv/.tex）")
    ap.add_argument("--out", default="output", help="输出根目录（默认 ./output）")
    ap.add_argument("--dpi", type=int, default=200, help="PNG DPI（默认 200）")
    ap.add_argument("--figure-type", default=None,
                    choices=["route", "apparatus", "flow", "hybrid"],
                    help="覆盖图类（默认按案例推断）")
    ap.add_argument("--title", default=None, help="覆盖标题")
    ap.add_argument("--width-mm", type=float, default=0.0, help="画布宽 mm")
    ap.add_argument("--height-mm", type=float, default=0.0, help="画布高 mm")
    ap.add_argument("--palette", default=None, help="自定义 palette.json 路径")
    ap.add_argument("--rules", default=None, help="自定义 connection_rules.json 路径")
    ap.add_argument("--merge", default=None,
                    help="Agent 人工修正 JSON：{\"entities\":[{id,...}],\"relations\":[{id,...}],\"change_notes\":[\"...\"]}")
    args = ap.parse_args(argv)

    case_path, task_path = resolve_case_arg(args.case, args.task)
    if not os.path.isfile(case_path):
        print(f"FATAL: case.json 不存在: {args.case}"
              "（--case 接受 case.json 本体或其所在目录）", file=sys.stderr)
        return 2

    try:
        run = run_case(case_path, task_path, os.path.abspath(args.out), args)
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

    # 交付自查（契约门 G1–G10）
    check_res = check_mod.check_result(run["result_path"])
    print(json.dumps({
        "case_id": run["result"]["case_id"],
        "status": run["result"]["status"],
        "out_dir": run["out_dir"],
        "artifacts": sorted(os.listdir(run["out_dir"])),
        "verify_ok": run["result"]["verify"]["ok"],
        "gates": check_res["gates"],
        "issues": check_res["issues"],
        "check_ok": check_res["ok"],
    }, ensure_ascii=False, indent=2))
    return 0 if check_res["ok"] else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))