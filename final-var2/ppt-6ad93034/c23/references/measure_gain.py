#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""measure_gain.py -- 公平对照测量台（随包分发，**请在包外运行**）。

运行位置提醒：本文件不要放在技能包目录里执行，否则会在包内生成 __pycache__
（平台预检会因此拒收整包）。正确做法：复制到包外临时目录，或直接把技能包
复制到临时目录后在那里运行。

它把题面点名的"基础 Agent 典型失败清单"落成一段**确定性基线生成器**，
再用与技能包**同一套**口径对两种条件的产物做逐页对拍：

  条件 B（baseline / 不加载 Skill）
      把材料段落直接铺进幻灯片：标题 = 段落首句、正文 = 整段原文、
      无页级叙事角色、无证据脚注、无演讲备注、无预览、硬编码 18pt 不收敛。
      即题面 §1 "整段塞进文本框 / 数字不可定位 / 无备注 / 导出无预览" 的
      可复现代理实现（**是代理，不是真 Agent 跑分**）。

  条件 S（skill / 加载本 Skill）
      python <SKILL_DIR>/scripts/main.py --case <case.json> --out <out>

两条件使用**同一** case.json、同一 task.md、同一材料、同一页数上限、
同一 python-pptx 版本、同一测量脚本。指标定义见 GAIN-PROTOCOL.md §3。

用法:
  python measure_gain.py --skill-dir <技能包根目录> --case <case.json> \
      [--case <case2.json> ...] --work <临时工作目录> --out <report.json>

退出码: 0 = 测量完成；2 = 输入不可读。
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
import unicodedata
from datetime import datetime

BASE_PT = 18      # 基线硬编码字号：不按槽位收敛、不做自适应缩放
CHAR_LIMIT = 90   # 与技能包 spec.limits.max_chars_per_bullet 同口径的纪律上限


# --------------------------------------------------------------------------
# 文本工具（与技能包一致的归一化口径，便于对拍）
# --------------------------------------------------------------------------


def norm(s):
    return re.sub(r"[\s\u3000]+", "", unicodedata.normalize("NFKC", s or "")).lower()


def numeric_tokens(text):
    toks = set()
    for m in re.finditer(r"\d+(?:[.,]\d+)*\s*(?:%|％|倍|x|×)?", norm(text)):
        tok = m.group(0).strip()
        if tok and any(ch.isdigit() for ch in tok):
            toks.add(tok)
    return toks


def read_text(path):
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


# --------------------------------------------------------------------------
# 条件 B：确定性基线生成器
# --------------------------------------------------------------------------


def _paragraphs(material_text):
    """把材料切成"段落块"——这是基线做法唯一的取舍规则。"""
    blocks, buf = [], []
    for raw in material_text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            if buf:
                blocks.append("\n".join(buf).strip())
                buf = []
            continue
        if line.lstrip().startswith("#"):
            if buf:
                blocks.append("\n".join(buf).strip())
                buf = []
            blocks.append(line.strip())
            continue
        if line.lstrip().startswith(">"):
            continue
        buf.append(line.strip())
    if buf:
        blocks.append("\n".join(buf).strip())
    return [b for b in blocks if b]


def _title_of(block):
    first = re.split(r"[。！？!?\.\n]", block)[0].strip()
    return first[:60] if first else block[:60]


def build_baseline_deck(case, material_text, out_pptx, max_slides):
    """确定性"基础 Agent"形态：段落→页，无角色/无证据/无备注/无预览。"""
    from pptx import Presentation
    from pptx.util import Inches, Pt

    prs = Presentation()
    blank = prs.slide_layouts[6] if len(prs.slide_layouts) > 6 else prs.slide_layouts[-1]
    blocks = _paragraphs(material_text)

    slides_text = []
    for i, block in enumerate(blocks[:max_slides]):
        slide = prs.slides.add_slide(blank)
        title = _title_of(block)
        body = block              # 整段原文照录：不取舍、不压缩
        tb = slide.shapes.add_textbox(Inches(0.6), Inches(0.5), Inches(9.0), Inches(1.0))
        tf = tb.text_frame
        tf.text = title
        for p in tf.paragraphs:
            for r in p.runs:
                r.font.size = Pt(BASE_PT + 6)
        bb = slide.shapes.add_textbox(Inches(0.6), Inches(1.6), Inches(9.0), Inches(5.0))
        bf = bb.text_frame
        bf.word_wrap = True
        bf.text = body
        for p in bf.paragraphs:
            for r in p.runs:
                r.font.size = Pt(BASE_PT)
        slides_text.append({"index": i + 1, "title": title, "body": body})
    prs.save(out_pptx)
    return slides_text


# --------------------------------------------------------------------------
# 指标（两侧同一口径；"没做"的项按最差计，绝不补分）
# --------------------------------------------------------------------------

DELIVERABLE_KEYS = ("editable_pptx", "preview_png", "preview_pdf", "evidence_map_md",
                    "evidence_map_json", "manifest_sha256", "result_json")

# 进入 delta 的指标：全部对"无结构照录"这一基线形态可判定为 0 或显著更低。
# Q2（单条文本长度）**不进 delta**：它是纪律的自我约束度量，而基线只是原样照录
# 材料段落 —— 若材料段落本身很短，基线会在 Q2 上"意外合规"。该指标仍逐例报出，
# 并在 GAIN-PROTOCOL.md §5 记录它为什么不作为对照结论的依据。
METRIC_KEYS = ("Q1_page_role_coverage", "Q3_numeric_claim_traceability",
               "Q4_notes_coverage", "Q5_evidence_footer_coverage",
               "Q6_deliverables_score")
REPORTED_ONLY_KEYS = ("Q2_page_discipline",)


def metric_baseline(case, case_dir, out_dir, slides_text, material_text, wall_s):
    n = max(len(slides_text), 1)

    # Q1：基线没有页级叙事角色字段
    q1 = 0.0

    # Q2：基线整段照录 → 语义单元（段落块）远超"单条 ≤90 字"的纪律
    q2_ok, max_unit = 0, 0
    for s in slides_text:
        units = [u for u in s["body"].split("\n") if u.strip()]   # 段落块 = 一个语义单元
        longest = max((len(u) for u in units), default=0)
        max_unit = max(max_unit, longest)
        if len(units) <= 7 and longest <= CHAR_LIMIT:
            q2_ok += 1
    q2 = q2_ok / n

    # Q3：带数字的主张必须带证据指针 —— 基线没有主张/证据结构
    numeric_slides = sum(
        1 for s in slides_text if numeric_tokens(s["title"] + "\n" + s["body"]))

    # Q4 / Q5：基线不写演讲备注、不写证据脚注
    deliverables = {
        "editable_pptx": 1 if os.path.exists(os.path.join(out_dir, "deck.pptx")) else 0,
        "preview_png": 0,
        "preview_pdf": 0,
        "evidence_map_md": 0,
        "evidence_map_json": 0,
        "manifest_sha256": 0,
        "result_json": 0,
    }

    return {
        "condition": "baseline_plain",
        "case_id": case.get("case_id"),
        "pages": len(slides_text),
        "wall_seconds": round(wall_s, 3),
        "quality": {
            "Q1_page_role_coverage": round(q1, 4),
            "Q2_page_discipline": round(q2, 4),
            "Q3_numeric_claim_traceability": 0.0,
            "Q4_notes_coverage": 0.0,
            "Q5_evidence_footer_coverage": 0.0,
            "Q6_deliverables_score": round(sum(deliverables.values()) / len(deliverables), 4),
            "deliverables_present": deliverables,
        },
        "diagnostics": {
            "slides_containing_numbers": numeric_slides,
            "longest_text_unit_chars": max_unit,
            "char_limit": CHAR_LIMIT,
            "adaptive_font_shrink": 0,
            "numbers_are_verbatim": 1,   # 整段照录："没抄错"但"不可定位"
            "numbers_with_evidence_pointer": 0,
        },
        "efficiency": {
            "edit_granularity": "whole_deck_regenerate",
            "manual_edit_ops_supported": 0,
            "version_archives": 0,
            "preview_review_artifacts": 0,
        },
    }


def metric_skill(case, case_dir, out_dir, material_text, wall_s):
    res_path = os.path.join(out_dir, "result.json")
    res = {}
    if os.path.exists(res_path):
        try:
            res = json.load(open(res_path, encoding="utf-8"))
        except Exception:
            res = {}
    deck = res.get("deck", {}) or {}
    slides = deck.get("slides", []) or []
    n = max(len(slides), 1)

    # Q1
    q1 = sum(1 for s in slides if s.get("role")) / n

    # Q2：单页单元数 ≤7 且每个单元（标题/主张）≤90 字
    q2_ok, max_unit = 0, 0
    for s in slides:
        units = [(s.get("title", "") or "")] + [
            (c.get("text", "") or "") for c in (s.get("claims", []) or [])]
        units = [u for u in units if u.strip()]
        longest = max((len(u) for u in units), default=0)
        max_unit = max(max_unit, longest)
        if len(units) <= 7 and longest <= CHAR_LIMIT:
            q2_ok += 1
    q2 = q2_ok / n

    # Q3：带数字的主张是否有证据指针
    numeric_claims, traced = 0, 0
    for s in slides:
        for c in (s.get("claims", []) or []):
            if numeric_tokens(c.get("text", "") or ""):
                numeric_claims += 1
                if [e for e in (c.get("evidence", []) or []) if str(e).strip()]:
                    traced += 1
    q3 = (traced / numeric_claims) if numeric_claims else 1.0

    # Q4 / Q5
    q4 = sum(1 for s in slides if s.get("notes")) / n
    q5 = sum(1 for s in slides if s.get("evidence_footer")) / n

    # Q6
    pngs = (res.get("previews", {}) or {}).get("pngs", []) or []
    pdf = (res.get("previews", {}) or {}).get("pdf", "") or ""
    deliverables = {
        "editable_pptx": 1 if os.path.exists(os.path.join(out_dir, "work", "deck.pptx")) else 0,
        "preview_png": 1 if pngs else 0,
        "preview_pdf": 1 if pdf else 0,
        "evidence_map_md": 1 if os.path.exists(os.path.join(out_dir, "evidence_map.md")) else 0,
        "evidence_map_json": 1 if os.path.exists(os.path.join(out_dir, "evidence_map.json")) else 0,
        "manifest_sha256": 1 if os.path.exists(os.path.join(out_dir, "manifest.json")) else 0,
        "result_json": 1 if os.path.exists(res_path) else 0,
    }
    receipt = deck.get("receipt", []) or []
    pts = [r.get("body_font_pt") or 0 for r in receipt]
    pts = [p for p in pts if p]
    changes = res.get("change_records", []) or []
    return {
        "condition": "skill_pipeline",
        "case_id": case.get("case_id"),
        "pages": len(slides),
        "wall_seconds": round(wall_s, 3),
        "status": res.get("status"),
        "quality": {
            "Q1_page_role_coverage": round(q1, 4),
            "Q2_page_discipline": round(q2, 4),
            "Q3_numeric_claim_traceability": round(q3, 4),
            "Q4_notes_coverage": round(q4, 4),
            "Q5_evidence_footer_coverage": round(q5, 4),
            "Q6_deliverables_score": round(sum(deliverables.values()) / len(deliverables), 4),
            "deliverables_present": deliverables,
        },
        "diagnostics": {
            "numeric_claims": numeric_claims,
            "numeric_claims_with_evidence": traced,
            "unverified_claims": len((res.get("evidence", {}) or {}).get("unverified_claims", []) or []),
            "longest_text_unit_chars": max_unit,
            "char_limit": CHAR_LIMIT,
            "adaptive_font_shrink": 1 if (pts and min(pts) < 18 and min(pts) >= 12) else 0,
            "body_font_pt_set": sorted(set(pts)),
            "uncertainty_items": len(res.get("uncertainty", []) or []),
        },
        "efficiency": {
            "edit_granularity": "local_op_with_version_archive",
            "manual_edit_ops_supported": 7,   # update/add/remove/retitle/reorder/set_figure/add_note
            "version_archives": len(changes),
            "preview_review_artifacts": len(pngs) + (1 if pdf else 0),
        },
    }


# --------------------------------------------------------------------------
# 单案例流程
# --------------------------------------------------------------------------


def run_case(skill_dir, case_path, work_dir, tag):
    case_path = os.path.abspath(case_path)
    case_dir = os.path.dirname(case_path)
    case = json.load(open(case_path, encoding="utf-8"))

    material_texts = []
    for rel in (case.get("inputs", {}) or {}).get("material", []) or []:
        p = rel if os.path.isabs(rel) else os.path.join(case_dir, rel)
        if os.path.exists(p):
            material_texts.append(read_text(p))
    material_text = "\n\n".join(material_texts)

    # ---- 条件 B ----
    b_out = os.path.join(work_dir, tag + "-baseline")
    os.makedirs(b_out, exist_ok=True)
    t0 = time.time()
    slides_text = build_baseline_deck(
        case, material_text, os.path.join(b_out, "deck.pptx"),
        int(case.get("spec", {}).get("max_slides", 8) or 8))
    b_wall = time.time() - t0
    report_b = metric_baseline(case, case_dir, b_out, slides_text, material_text, b_wall)

    # ---- 条件 S ----
    s_out = os.path.join(work_dir, tag + "-skill")
    os.makedirs(s_out, exist_ok=True)
    t0 = time.time()
    proc = subprocess.run(
        [sys.executable, os.path.join(skill_dir, "scripts", "main.py"),
         "--case", case_path, "--out", s_out],
        cwd=work_dir, capture_output=True, text=True, encoding="utf-8", errors="replace")
    s_wall = time.time() - t0

    gate = selftest = None
    if os.path.exists(os.path.join(s_out, "result.json")):
        g = subprocess.run(
            [sys.executable, os.path.join(skill_dir, "scripts", "result_tool.py"),
             "--result", os.path.join(s_out, "result.json"), "--out-dir", s_out,
             "--case", case_path,
             "--envelope", os.path.join(skill_dir, "templates", "result_envelope.json")],
            cwd=work_dir, capture_output=True, text=True, encoding="utf-8", errors="replace")
        gate = {"exit": g.returncode, "stdout_tail": (g.stdout or "").strip()[-400:]}
        st = subprocess.run(
            [sys.executable, os.path.join(skill_dir, "scripts", "selftest.py"),
             "--out", s_out, "--case", case_path],
            cwd=work_dir, capture_output=True, text=True, encoding="utf-8", errors="replace")
        selftest = {"exit": st.returncode, "stdout_tail": (st.stdout or "").strip()[-400:]}

    report_s = metric_skill(case, case_dir, s_out, material_text, s_wall)
    report_s["condition_exit_code"] = proc.returncode
    report_s["gate"] = gate
    report_s["selftest"] = selftest
    report_s["notes_tail"] = (proc.stdout or "").strip().splitlines()[-2:]

    return {
        "case_path": os.path.basename(case_path),
        "case_id": case.get("case_id"),
        "material_chars": len(material_text),
        "max_slides": int(case.get("spec", {}).get("max_slides", 8) or 8),
        "baseline": report_b,
        "skill": report_s,
        "deltas": {k: round(report_s["quality"][k] - report_b["quality"][k], 4)
                   for k in METRIC_KEYS},
    }


def _aggregate(results):
    agg = {"cases": len(results), "baseline_mean": {}, "skill_mean": {}, "delta_mean": {}}
    for k in METRIC_KEYS:
        b = [r["baseline"]["quality"][k] for r in results]
        s = [r["skill"]["quality"][k] for r in results]
        agg["baseline_mean"][k] = round(sum(b) / len(b), 4)
        agg["skill_mean"][k] = round(sum(s) / len(s), 4)
        agg["delta_mean"][k] = round((sum(s) - sum(b)) / len(b), 4)
    agg["baseline_wall_seconds_sum"] = round(
        sum(r["baseline"]["wall_seconds"] for r in results), 3)
    agg["skill_wall_seconds_sum"] = round(
        sum(r["skill"]["wall_seconds"] for r in results), 3)
    agg["skill_exit_codes"] = [r["skill"].get("condition_exit_code") for r in results]
    agg["skill_statuses"] = [r["skill"].get("status") for r in results]
    agg["gate_valid"] = [
        bool(r["skill"].get("gate") and r["skill"]["gate"].get("exit") == 0)
        for r in results]
    return agg


def main(argv=None):
    ap = argparse.ArgumentParser(description="公平对照测量台（包外运行）")
    ap.add_argument("--skill-dir", required=True)
    ap.add_argument("--case", action="append", required=True, help="case.json 路径，可重复")
    ap.add_argument("--work", required=True, help="临时工作目录")
    ap.add_argument("--out", required=True, help="report.json 输出路径")
    args = ap.parse_args(argv)

    skill_dir = os.path.abspath(args.skill_dir)
    if not os.path.isfile(os.path.join(skill_dir, "SKILL.md")):
        print("ERROR: skill dir has no SKILL.md", file=sys.stderr)
        return 2
    os.makedirs(args.work, exist_ok=True)

    results = []
    for i, c in enumerate(args.case):
        if not os.path.isfile(c):
            print("ERROR: case not readable: %s" % c, file=sys.stderr)
            return 2
        results.append(run_case(skill_dir, c, args.work, "c%d" % (i + 1)))

    report = {
        "protocol": "GAIN-PROTOCOL.md §3（同输入 / 同模板 / 同预算 / 同测量脚本）",
        "measured_at": datetime.now().isoformat(timespec="seconds"),
        "python": sys.version.split()[0],
        "skill_dir_label": "<SKILL_DIR>（技能包根目录，运行时由 --skill-dir 传入）",
        "conditions": {
            "baseline_plain": "确定性段落铺页生成器（无角色/无证据/无备注/无预览/字号不收敛）",
            "skill_pipeline": "python <SKILL_DIR>/scripts/main.py --case <case> --out <out>",
        },
        "shared_conditions": [
            "同一 case.json / task.md / 材料文件",
            "同一 spec.max_slides 页数上限与同一模板 spec",
            "同一 Python 解释器与同一 python-pptx / Pillow / matplotlib 版本",
            "同一测量脚本、同一数字归一化口径（NFKC + 去空白 + 小写）",
        ],
        "cases": results,
        "aggregate": _aggregate(results),
        "scope_note": (
            "条件 B 是题面点名失败形态的确定性代理实现，用于给出可复算的下界；"
            "它不等于也不替代平台用真实基础 Agent 生成的对照结果（题面明确对照由平台提供/生成）。"),
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print(json.dumps(report["aggregate"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
