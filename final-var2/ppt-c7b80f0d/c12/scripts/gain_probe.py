#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gain_probe.py — 「使用增益」的本地可执行对照（公平对照协议的执行件）。

三臂（`--arms` 逗号分隔；默认 `baseline,skill`）：

- ``baseline``  朴素单遍流水线：把材料按段落切块贴页，不写页级主张、不做证据映射、
  不跑 C1 lint、不做模板适配、不分离备注、不按契约产出 result.json。
  它是"**不加载本 Skill 的基础 Agent**"在可执行层面的代理——口径与边界见
  ``references/GAIN-PROTOCOL.md`` §2，**平台白板对照仍是权威口径**。
- ``skill``     调用本包 ``scripts/main.py``，用**同一个 case + 同一份 Agent 写的
  deck-spec**，走完整链路（C1 → 构建 → 预览 → C3 → 契约回显）。
- ``ablation``  调用 ``scripts/main.py --demo``：脚本还在，但**没有"方案先行 + C1 前置门"**
  （没有 Agent 写的页级方案与证据定位）。用于隔离机制 M2 的贡献，只在 v3 的
  机制消融记录里使用。

三臂由**同一套评审函数**（``_review``）逐项测量，指标定义见 GAIN-PROTOCOL.md §3；
因此"基线差在哪"是可以逐格复核的，而不是叙述。

约定：
- 只写 ``--out`` 指定的目录，**绝不写进技能包**；
- 所有子进程带 ``PYTHONDONTWRITEBYTECODE=1``，因此本脚本可在包内原地运行而不产生
  ``__pycache__``（技能资源只允许文本文件）；
- 退出码：0 = 报告已产出；2 = 后端不可用（缺 python-pptx）；3 = 输入不可读。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import zipfile

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROTOCOL_VERSION = "gain-probe/1.0"

# 与 references/OUTPUT_CONTRACT.md §1 同源的字段清单（优先从文档解析，失败用常量兜底）
CONTRACT_FALLBACK = [
    "case_id", "task", "status", "output_contract", "deck", "evidence_mapping",
    "evidence_map_json", "spec_lint", "previews", "charts", "sources", "uncertainty",
    "change_records", "run_meta", "title", "main_claim", "slides", "render_state",
    "notes_separated",
]
NULLABLE = {"deck", "evidence_map_json"}
NAME_PREFIXES = ("claim-title-", "claim-strip-", "body-bullets-", "figure-", "table-",
                 "footer-page-", "outline-", "evidence-map-", "closing-", "cover-")
MAX_BULLETS = 6
MAX_CHARS_BULLET = 110
# 占位主张的识别标记（骨架/待补），用于把"有 claim"与"claim 是真内容"分开量
PLACEHOLDER_MARKS = ("SKELETON", "骨架", "待补", "TODO", "占位")


def weighted_len(text) -> int:
    """字符预算：CJK 字形更宽，按双宽计（与 scripts/spec_lint.py 同一规则）。"""
    s = text[0] if isinstance(text, (list, tuple)) and text else ("" if text is None else str(text))
    return sum(2 if ord(ch) > 0x2E7F else 1 for ch in s)


def contract_fields() -> list:
    """从 references/OUTPUT_CONTRACT.md §1 的表格里解析顶层字段清单。"""
    path = os.path.join(SKILL_DIR, "references", "OUTPUT_CONTRACT.md")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
        body = text.split("## 1.")[-1].split("## 2.")[0]
        found = re.findall(r"^\|\s*`([a-z_]+)`\s*\|", body, flags=re.M)
        return found or list(CONTRACT_FALLBACK)
    except Exception:
        return list(CONTRACT_FALLBACK)


# --------------------------------------------------------------------------- #
# 材料读取（基线与 skill 臂读同一份输入）
# --------------------------------------------------------------------------- #
def read_material(case: dict, case_path: str):
    """按 case.json 的 material 定位材料并抽成纯文本，返回 (text, tool, note)。"""
    rel = case.get("material") or case.get("material_path") or ""
    if not rel:
        return "", None, "case.json declares no material"
    cand = rel if os.path.isabs(rel) else os.path.join(os.path.dirname(case_path), rel)
    if not os.path.isfile(cand):
        return "", None, "material not found: %s" % rel
    ext = os.path.splitext(cand)[1].lower()
    if ext in (".txt", ".md", ".tex"):
        with open(cand, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read(), "direct-read", ""
    if ext == ".pdf":
        try:
            import fitz  # type: ignore
            doc = fitz.open(cand)
            pages = [p.get_text() for p in doc]
            return "\n\n".join(pages), "pymupdf", ""
        except Exception:
            pass
        try:
            from pypdf import PdfReader  # type: ignore
            reader = PdfReader(cand)
            return "\n\n".join((p.extract_text() or "") for p in reader.pages), "pypdf", ""
        except Exception:
            pass
        return "", None, "no readable PDF backend for: %s" % rel
    return "", None, "unsupported material type: %s" % ext


# --------------------------------------------------------------------------- #
# 臂 A：朴素单遍流水线（基础 Agent 的可执行代理）
# --------------------------------------------------------------------------- #
def run_baseline_arm(case: dict, case_path: str, out_dir: str) -> dict:
    from pptx import Presentation  # noqa: F401  (backend probe)

    os.makedirs(out_dir, exist_ok=True)
    text, tool, note = read_material(case, case_path)
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

    prs = Presentation()
    deck_title = case.get("title") or "Presentation"
    cover = prs.slides.add_slide(prs.slide_layouts[0])
    cover.shapes.title.text = deck_title[:80]
    try:
        cover.placeholders[1].text = ""
    except Exception:
        pass

    chunk = 6
    for i in range(0, len(paragraphs), chunk):
        block = paragraphs[i:i + chunk]
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        slide.shapes.title.text = block[0][:60]
        body = slide.placeholders[1].text_frame
        body.text = block[0]
        for line in block[1:]:
            para = body.add_paragraph()
            para.text = line
    deck_name = "baseline_deck.pptx"
    prs.save(os.path.join(out_dir, deck_name))

    # 基础 Agent 会读 case.json 的 output_contract 键名，但按容器给空值即可（它没有真值）
    declared = case.get("output_contract")
    echo = {}
    if isinstance(declared, dict):
        for k, v in declared.items():
            if isinstance(v, bool):
                echo[k] = False
            elif isinstance(v, list):
                echo[k] = []
            elif isinstance(v, dict):
                echo[k] = {}
            else:
                echo[k] = ""
    elif isinstance(declared, list):
        echo = {str(k): "" for k in declared}

    result = {
        "case_id": case.get("case_id", ""),
        "status": "completed",
        "output_contract": echo,
        "title": deck_title,
        "deck": {"file": deck_name, "slide_count": len(prs.slides.__iter__.__self__._sldIdLst)
                 if False else len(prs.slides._sldIdLst)},
        "slides": [{"page": i + 1, "title": s.shapes.title.text if s.shapes.title else ""}
                   for i, s in enumerate(prs.slides)],
        "sources": [{"type": "paper_material", "tool": tool, "note": note}],
    }
    with open(os.path.join(out_dir, "result.json"), "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    return {"arm": "baseline", "note": note, "material_tool": tool,
            "paragraphs": len(paragraphs)}


# --------------------------------------------------------------------------- #
# 臂 B/C：调用本包 main.py（skill 全链路 / --demo 消融）
# --------------------------------------------------------------------------- #
def run_cli_arm(case_path: str, spec_path, out_dir: str, demo: bool) -> dict:
    args = [sys.executable, os.path.join(SKILL_DIR, "scripts", "main.py"),
            "--case", case_path, "--out", out_dir]
    if demo:
        args.append("--demo")
    else:
        args += ["--spec", spec_path]
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    t0 = time.time()
    proc = subprocess.run(args, capture_output=True, env=env)
    return {"exit": proc.returncode, "wall": time.time() - t0,
            "stdout_tail": proc.stdout.decode("utf-8", "replace").strip().splitlines()[-1:]}


# --------------------------------------------------------------------------- #
# 统一评审（三臂同一套检查，逐格可复核）
# --------------------------------------------------------------------------- #
def _safe_json(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def _pptx_stats(pptx_path):
    """从 .pptx 直接量出：页数、备注页数、命名形状数、超限正文框数、部件哈希。"""
    from pptx import Presentation
    stats = {"slides": 0, "notes_pages": 0, "named_shapes": 0,
             "over_limit_frames": 0, "parts": {}}
    prs = Presentation(pptx_path)
    stats["slides"] = len(prs.slides._sldIdLst)
    for slide in prs.slides:
        if slide.has_notes_slide:
            txt = (slide.notes_slide.notes_text_frame.text or "").strip()
            if txt:
                stats["notes_pages"] += 1
        for shape in slide.shapes:
            name = getattr(shape, "name", "") or ""
            if name.startswith(NAME_PREFIXES):
                stats["named_shapes"] += 1
            if shape.has_text_frame:
                paras = shape.text_frame.paragraphs
                longest = max((weighted_len(p.text) for p in paras), default=0)
                if len(paras) > MAX_BULLETS or longest > MAX_CHARS_BULLET * 2:
                    stats["over_limit_frames"] += 1
    with zipfile.ZipFile(pptx_path) as z:
        for n in sorted(z.namelist()):
            stats["parts"][n] = hashlib.sha256(z.read(n)).hexdigest()
    return stats


def _review(out_dir: str, fields: list) -> dict:
    """对任一臂的产物做同一套检查，返回指标 + 复核点（rework points）。"""
    m = {"rework": [], "claim_coverage": 0.0, "substantive_claim_coverage": 0.0,
         "placeholder_claims": 0, "evidence_locations": 0,
         "contract_fields_present": 0, "slides": 0, "notes_pages": 0,
         "named_shapes": 0, "over_limit_frames": 0, "artifacts": 0,
         "template_adapted": False, "evidence_rows": 0, "parts": {},
         "deck_reopenable": False, "slide_count_matches": False}
    if not os.path.isdir(out_dir):
        m["rework"].append("arm produced no output directory")
        return m
    m["artifacts"] = sum(len(f) for _, _, f in os.walk(out_dir))

    res = _safe_json(os.path.join(out_dir, "result.json"))
    if res is None:
        m["rework"].append("no parseable result.json")
        return m

    m["contract_fields_present"] = sum(1 for f in fields if f in res)
    missing = [f for f in fields if f not in res]
    if missing:
        m["rework"].append("contract top-level fields missing: %s" % ",".join(missing[:6]))
    nulls = [f for f in fields if f in res and res[f] is None and f not in NULLABLE]
    if nulls:
        m["rework"].append("declared contract fields are null: %s" % ",".join(nulls))

    if res.get("status") not in ("completed", "partial", "failed"):
        m["rework"].append("status not in the honest vocabulary")

    slides = res.get("slides") if isinstance(res.get("slides"), list) else []
    claimed = [s for s in slides if isinstance(s, dict) and str(s.get("claim") or "").strip()]
    m["claim_coverage"] = round(len(claimed) / len(slides), 3) if slides else 0.0
    substantive = [s for s in claimed
                   if not any(mark in str(s.get("claim")) for mark in PLACEHOLDER_MARKS)]
    m["placeholder_claims"] = len(claimed) - len(substantive)
    m["substantive_claim_coverage"] = (round(len(substantive) / len(slides), 3)
                                       if slides else 0.0)
    if slides and not claimed:
        m["rework"].append("no slide carries a page-level claim")
    if m["placeholder_claims"]:
        m["rework"].append("%d slide(s) carry placeholder claims instead of real ones"
                           % m["placeholder_claims"])

    # 证据映射（双形态）
    em = res.get("evidence_mapping")
    em_file = em.get("file") if isinstance(em, dict) else None
    declared_entries = em.get("entries") if isinstance(em, dict) else None
    rows = 0
    if em_file and os.path.isfile(os.path.join(out_dir, em_file)):
        with open(os.path.join(out_dir, em_file), "r", encoding="utf-8", errors="replace") as fh:
            rows = len([ln for ln in fh if ln.strip().startswith("|")]) - 2  # 去掉表头与分隔行
    else:
        m["rework"].append("no evidence mapping file on disk")
    m["evidence_rows"] = max(rows, 0)
    if isinstance(declared_entries, int) and m["evidence_rows"] != declared_entries:
        m["rework"].append("evidence table rows != declared entries")
    emj = res.get("evidence_map_json")
    if emj and os.path.isfile(os.path.join(out_dir, emj)):
        data = _safe_json(os.path.join(out_dir, emj)) or {}
        rows_json = data.get("rows")
        if not isinstance(rows_json, list):
            rows_json = data.get("entries") if isinstance(data.get("entries"), list) else []
        m["evidence_locations"] = sum(
            1 for e in rows_json
            if isinstance(e, dict) and (e.get("location") or e.get("evidence"))
            and e.get("status") != "gap"
        )
    elif res.get("status") == "completed" and "evidence_map_json" not in res:
        m["rework"].append("no machine-readable evidence map")

    # 预览：声明即必须落盘
    for p in (res.get("previews") or []):
        if isinstance(p, dict) and not os.path.isfile(os.path.join(out_dir, p.get("file") or "")):
            m["rework"].append("declared preview missing: %s" % p.get("file"))
            break

    # deck：可重开 + 页数一致 + 备注 + 命名 + 溢出
    deck = res.get("deck") if isinstance(res.get("deck"), dict) else {}
    deck_file = deck.get("file")
    if deck_file and os.path.isfile(os.path.join(out_dir, deck_file)):
        try:
            stats = _pptx_stats(os.path.join(out_dir, deck_file))
            m["deck_reopenable"] = True
            m["slides"] = stats["slides"]
            m["notes_pages"] = stats["notes_pages"]
            m["named_shapes"] = stats["named_shapes"]
            m["over_limit_frames"] = stats["over_limit_frames"]
            m["parts"] = stats["parts"]
            m["slide_count_matches"] = (deck.get("slide_count") == stats["slides"])
            if not m["slide_count_matches"]:
                m["rework"].append("deck slide_count != result.slide_count")
            if stats["notes_pages"] != stats["slides"]:
                m["rework"].append("notes not present on every slide (%d/%d)"
                                   % (stats["notes_pages"], stats["slides"]))
            if stats["over_limit_frames"]:
                m["rework"].append("%d text frame(s) exceed the overflow guard"
                                   % stats["over_limit_frames"])
        except Exception as exc:  # noqa: BLE001
            m["rework"].append("deck cannot be reopened: %s" % type(exc).__name__)
    else:
        m["rework"].append("no deck file on disk")

    m["template_adapted"] = bool(isinstance(deck.get("template"), dict)
                                 and deck["template"].get("kind") == "file")
    return m


# --------------------------------------------------------------------------- #
def main(argv=None):
    ap = argparse.ArgumentParser(description="使用增益的本地可执行对照（见 references/GAIN-PROTOCOL.md）")
    ap.add_argument("--case", default=os.path.join(SKILL_DIR, "examples", "case.json"))
    ap.add_argument("--spec", default=os.path.join(SKILL_DIR, "examples", "deck-spec.json"))
    ap.add_argument("--out", required=True, help="对照产物目录（脚本只写这里）")
    ap.add_argument("--arms", default="baseline,skill",
                    help="逗号分隔：baseline | skill | ablation")
    ap.add_argument("--repeat", type=int, default=1, help="每臂重复次数（用于确定性测量）")
    ap.add_argument("--json", default=None, help="报告输出路径（默认 <out>/gain-report.json）")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    try:
        import pptx  # noqa: F401
    except Exception:
        print(json.dumps({"status": "backend_unavailable", "need": "python-pptx"}, ensure_ascii=False))
        return 2

    if not os.path.isfile(args.case):
        print(json.dumps({"status": "input_unreadable", "case": args.case}, ensure_ascii=False))
        return 3
    case = _safe_json(args.case)
    if case is None:
        print(json.dumps({"status": "input_unreadable", "case": args.case}, ensure_ascii=False))
        return 3

    fields = contract_fields()
    arms = [a.strip() for a in args.arms.split(",") if a.strip()]
    report = {
        "protocol_version": PROTOCOL_VERSION,
        "skill_version_dir": os.path.basename(SKILL_DIR),
        "case_id": case.get("case_id", ""),
        "case_file": os.path.basename(args.case),
        "arms_requested": arms,
        "contract_fields_checked": len(fields),
        "repeat": max(1, args.repeat),
        "arms": {},
        "notes": [
            "baseline 是『不加载本 Skill 的基础 Agent』在可执行层面的代理（朴素单遍流水线），"
            "不是对某个具体 LLM 的测量；平台白板对照仍是权威口径。",
            "所有臂由同一套 _review 检查逐格测量，差异可直接复核。",
            "本机 wall_seconds 依赖机器与案例规模，只作效率参考，不作绝对承诺。",
        ],
    }
    os.makedirs(args.out, exist_ok=True)

    for arm in arms:
        entry = {"runs": [], "metrics": None}
        for rep in range(max(1, args.repeat)):
            sub = os.path.join(args.out, arm if rep == 0 else "%s-run%d" % (arm, rep + 1))
            if os.path.isdir(sub):
                for root, _dirs, files in os.walk(sub, topdown=False):
                    for f in files:
                        os.remove(os.path.join(root, f))
                    os.rmdir(root)
            t0 = time.time()
            if arm == "baseline":
                info = run_baseline_arm(case, args.case, sub)
                wall = time.time() - t0
            elif arm == "skill":
                info = run_cli_arm(args.case, args.spec, sub, demo=False)
                wall = info.get("wall", time.time() - t0)
            elif arm == "ablation":
                info = run_cli_arm(args.case, args.spec, sub, demo=True)
                wall = info.get("wall", time.time() - t0)
            else:
                raise SystemExit("unknown arm: %s" % arm)
            metrics = _review(sub, fields)
            metrics["wall_seconds"] = round(wall, 3)
            metrics["rework_points"] = len(metrics["rework"])
            entry["runs"].append({"dir": os.path.basename(sub), "info": info,
                                  "metrics": metrics})
        first = entry["runs"][0]["metrics"]
        second = entry["runs"][1]["metrics"] if len(entry["runs"]) > 1 else None
        entry["metrics"] = {k: v for k, v in first.items() if k != "parts"}
        entry["metrics"]["rework_points"] = first["rework_points"]
        if second is not None:
            a, b = first["parts"], second["parts"]
            entry["metrics"]["differing_opc_parts"] = (
                len([k for k in set(a) | set(b) if a.get(k) != b.get(k)]))
            entry["metrics"]["opc_parts"] = len(a)
        entry["runs"] = [{"dir": r["dir"], "info": r["info"],
                          "metrics": {k: v for k, v in r["metrics"].items() if k != "parts"}}
                         for r in entry["runs"]]
        report["arms"][arm] = entry

    out_json = args.json or os.path.join(args.out, "gain-report.json")
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    if not args.quiet:
        summary = {a: {"rework_points": e["metrics"]["rework_points"],
                       "claim_coverage": e["metrics"]["claim_coverage"],
                       "substantive_claim_coverage": e["metrics"]["substantive_claim_coverage"],
                       "evidence_rows": e["metrics"]["evidence_rows"],
                       "evidence_locations": e["metrics"]["evidence_locations"],
                       "notes_pages": e["metrics"]["notes_pages"],
                       "named_shapes": e["metrics"]["named_shapes"],
                       "wall_seconds": e["metrics"]["wall_seconds"]}
                   for a, e in report["arms"].items()}
        print(json.dumps({"status": "ok", "report": os.path.basename(out_json),
                          "summary": summary}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
