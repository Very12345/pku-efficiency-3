#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gain_ab.py — 公平对照装置（F 度量臂）+ 基础形态基线臂（A 臂模拟器）。

它回答一个问题：**加载本 Skill 之后，同一份输入上到底多出了什么、多花了什么。**
对照记录见 `references/GAIN-PROTOCOL.md`，机器可读结果见
`references/GAIN-PROTOCOL.md（附录）`（本脚本 --report 产出的同一结构）。

两个臂
------
A 臂（baseline，本脚本内置的**确定性基线模拟器**）：
    复现题面"常见表现"里描述的基础形态——把材料段落按固定块大小搬成页面、
    页数由材料长度（而不是时长）决定、不写讲稿备注、不记录来源定位、不预判追问、
    图只在页面文字里出现（有图片文件时按原尺寸放到末尾页）。
    它是**忠实实现的代理臂**，不是平台真实基础 Agent 的运行；这一点在协议里明写。
B 臂（skill）：以子进程调用本包唯一入口 `scripts/main.py`，不做任何参数变通。

度量口径（两个臂**同一把尺子**，指标定义写在 references/GAIN-PROTOCOL.md §4）
------------------------------------------------------------------
  D 组（只看 deck，条件无关）：页数、页数偏差、讲稿覆盖率、最大正文段落数、
                              正文字符数、逐字可溯源页占比、数字可对源率、嵌入图片数
  C 组（只看产物目录）：来源定位覆盖率、证据行数、问答条目数、计划门、契约、
                        不确定性条数、result.json 顶层键数、预览 PNG 有效数
  E 组（效率）：单臂墙钟秒；达到冻结页数所需轮数（A 臂实测：首轮页数不符时
                按最小返工重新分块再跑一轮，累加耗时）
  缺项一律记 0 或 null 并标 `available=false`，**不跳过**——"没产出"本身就是要测的差异。

用法
----
    python gain_ab.py --case examples/case.json --work <dir> [--skill-dir <pkg>]
                      [--report <path>] [--skip-arm-b] [--quiet]

退出码：0 = 度量完成（**不代表任何一臂合格**）；2 = 输入不合法。
本脚本不 import 本包任何模块（避免"用被测者自己的尺子量被测者"），
只读产物；唯一的外部调用是 B 臂的 `main.py` 子进程。
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

SENT_SPLIT = re.compile(r"[。．.!?！？\n]+")
NUM_RE = re.compile(r"\d+(?:\.\d+)?%?")
IMG_EXT = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff"}


# --------------------------------------------------------------------------- IO
def read_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def norm(text):
    return re.sub(r"\s+", " ", text or "").strip()


def read_source_text(path):
    """Return extracted text of one material, or None when it is not text."""
    ext = os.path.splitext(path)[1].lower()
    if ext in IMG_EXT:
        return None
    if ext in (".md", ".txt", ".csv", ".json", ".yaml", ".yml", ".tex", ".bib"):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                return fh.read()
        except OSError:
            return None
    if ext == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError:
            try:
                from PyPDF2 import PdfReader  # type: ignore
            except ImportError:
                return None
        try:
            reader = PdfReader(path)
            return "\n".join((p.extract_text() or "") for p in reader.pages)
        except Exception:  # noqa: BLE001
            return None
    return None


def resolve_materials(case, case_dir):
    """[(abs_path, role, text_or_None)] for everything the case declares."""
    entries = case.get("materials") or []
    out = []
    if isinstance(entries, dict):
        entries = [{"path": k, "role": v} for k, v in entries.items()]
    for ent in entries:
        rel = ent.get("path") if isinstance(ent, dict) else ent
        role = (ent.get("role") if isinstance(ent, dict) else "") or ""
        if not rel:
            continue
        cand = rel if os.path.isabs(rel) else os.path.join(case_dir, rel)
        if os.path.exists(cand):
            out.append((os.path.normpath(cand), role, read_source_text(cand)))
        else:
            out.append((os.path.normpath(rel), role, None))
    return out


# ------------------------------------------------------------------ deck metrics
def measure_deck(deck_path, source_texts):
    """D-group metrics from a .pptx alone (works for both arms)."""
    res = {"available": False}
    try:
        from pptx import Presentation
    except ImportError:
        return res
    if not os.path.exists(deck_path):
        return res
    try:
        prs = Presentation(deck_path)
    except Exception as exc:  # noqa: BLE001
        res["error"] = str(exc)
        return res
    src = norm(" ".join(t for t in source_texts if t))
    slides, notes_ok, paragraphs, chars, grounded, nums_all, nums_hit, pics = [], 0, [], [], 0, 0, 0, 0
    nums_missing = []
    for slide in prs.slides:
        title = ""
        if slide.shapes.title is not None:
            title = norm(slide.shapes.title.text)
        body_paras, body_chars, slide_nums_hit, slide_nums_all = [], 0, 0, 0
        for shape in slide.shapes:
            if shape == slide.shapes.title:
                continue
            if shape.shape_type == 13 or getattr(shape, "image", None) is not None:
                pics += 1
            if not shape.has_text_frame:
                continue
            for para in shape.text_frame.paragraphs:
                txt = norm("".join(r.text for r in para.runs))
                if not txt:
                    continue
                body_paras.append(txt)
                body_chars += len(txt)
                for n in NUM_RE.findall(txt):
                    slide_nums_all += 1
                    if n in src:
                        slide_nums_hit += 1
                    elif len(nums_missing) < 20:
                        nums_missing.append(n)
        note = ""
        if slide.has_notes_slide:
            note = norm(slide.notes_slide.notes_text_frame.text)
        if note:
            notes_ok += 1
        # grounding is judged over every word the audience can see (title + body)
        body_text = title + " " + " ".join(body_paras)
        ok = any(len(s) >= 12 and norm(s) in src for s in SENT_SPLIT.split(body_text))
        grounded += 1 if ok else 0
        paragraphs.append(len(body_paras))
        chars.append(body_chars)
        nums_all += slide_nums_all
        nums_hit += slide_nums_hit
        slides.append({"index": len(slides) + 1, "title": title[:60],
                       "paras": len(body_paras), "chars": body_chars,
                       "notes": bool(note), "verbatim_grounded": bool(ok)})
    n = len(slides) or 1
    res.update({
        "available": True,
        "slides": len(slides),
        "notes_coverage": round(notes_ok / n, 4),
        "max_body_paragraphs": max(paragraphs) if paragraphs else 0,
        "mean_body_paragraphs": round(sum(paragraphs) / n, 3),
        "mean_body_chars": round(sum(chars) / n, 1),
        "mean_paragraph_chars": (round(sum(chars) / sum(paragraphs), 1)
                                 if sum(paragraphs) else None),
        "verbatim_grounded_ratio": round(grounded / n, 4),
        "numbers_in_source_ratio": (round(nums_hit / nums_all, 4) if nums_all else None),
        "numbers_total": nums_all,
        "numbers_not_in_source_sample": nums_missing,
        "embedded_pictures": pics,
        "slides_detail": slides,
    })
    return res


def measure_contract(out_dir, frozen_count):
    """C-group metrics from the produced directory (result.json based)."""
    res = {"available": False, "result_json": False}
    rpath = os.path.join(out_dir, "result.json")
    if not os.path.exists(rpath):
        return res
    try:
        r = read_json(rpath)
    except Exception as exc:  # noqa: BLE001
        res["error"] = str(exc)
        return res
    pages = r.get("pages") or []
    structural = {"title", "cover", "agenda", "toc", "qa", "backup", "thanks"}
    content = [p for p in pages if (p.get("block") or "") not in structural]
    with_loc = [p for p in content
                if ((p.get("evidence") or [{}])[0].get("locator") or "").strip()]
    ev_rows = sum(len(p.get("evidence") or []) for p in pages)
    qa_items = sum(len(p.get("qa") or []) for p in pages)
    audit = r.get("audit") or {}
    prev = ((r.get("artifacts") or {}).get("previews") or {})
    pngs = 0
    pdir = os.path.join(out_dir, "previews")
    if os.path.isdir(pdir):
        for name in os.listdir(pdir):
            if name.lower().endswith(".png"):
                with open(os.path.join(pdir, name), "rb") as fh:
                    if fh.read(8) == b"\x89PNG\r\n\x1a\n":
                        pngs += 1
    res.update({
        "available": True,
        "result_json": True,
        "status": r.get("status"),
        "top_level_keys": len(r.keys()),
        "pages": len(pages),
        "locator_coverage": (round(len(with_loc) / len(content), 4) if content else None),
        "content_pages": len(content),
        "evidence_rows": ev_rows,
        "qa_items": qa_items,
        "uncertainty_entries": len(r.get("uncertainty") or []),
        "change_records": len(r.get("change_records") or []),
        "plan_gates_valid": ((audit.get("plan_gates") or {}).get("valid")),
        "evidence_valid": ((audit.get("evidence") or {}).get("valid")),
        "deck_valid": ((audit.get("deck") or {}).get("valid")),
        "preview_pngs_valid": pngs,
        "slide_count_field": r.get("slide_count"),
        "page_count_delta_vs_frozen": (
            abs(len(pages) - frozen_count) if isinstance(frozen_count, int) else None),
    })
    return res


# ------------------------------------------------------------- baseline arm (A)
def build_baseline_deck(case, materials, out_dir, target_pages=None):
    """Deterministic stand-in for the plain baseline shape described by the task
    statement ("把摘要和 Results 逐段搬成页面 … 页数与讲述时长脱节 … 讲稿备注缺失").
    Page count is material-driven (5 paragraphs / slide) unless target_pages is
    given (that is the *rework* pass used to measure E2)."""
    from pptx import Presentation
    from pptx.util import Inches, Pt

    paras = []
    for _path, _role, text in materials:
        if not text:
            continue
        for block in re.split(r"\n\s*\n", text):
            b = norm(block)
            if len(b) >= 20:
                paras.append(b)
    if not paras:
        paras = ["(no textual material could be read)"]
    per_slide = 5
    n_pages = target_pages or max(3, -(-len(paras) // per_slide))
    os.makedirs(out_dir, exist_ok=True)
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    blank = prs.slide_layouts[6]
    chunk = max(1, -(-len(paras) // n_pages))
    for i in range(n_pages):
        group = paras[i * chunk:(i + 1) * chunk] or paras[:1]
        slide = prs.slides.add_slide(blank)
        tb = slide.shapes.add_textbox(Inches(0.6), Inches(0.4), Inches(12), Inches(1.0))
        tb.text_frame.text = norm(group[0])[:60]
        tb.text_frame.paragraphs[0].runs[0].font.size = Pt(24)
        body = slide.shapes.add_textbox(Inches(0.6), Inches(1.6), Inches(12), Inches(5.2))
        tf = body.text_frame
        tf.word_wrap = True
        for j, para in enumerate(group):
            p = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
            run = p.add_run()
            run.text = para[:260]
            run.font.size = Pt(12)
    # the obvious thing a plain agent also does: drop the figure files in
    figs = [p for p, _r, t in materials if t is None
            and os.path.splitext(p)[1].lower() in IMG_EXT and os.path.exists(p)]
    for idx, fig in enumerate(figs):
        slide = prs.slides[min(idx, len(prs.slides) - 1)]
        try:
            slide.shapes.add_picture(fig, Inches(0.6), Inches(2.2))
        except Exception:  # noqa: BLE001
            pass
    deck_path = os.path.join(out_dir, "baseline_deck.pptx")
    prs.save(deck_path)
    envelope = {
        "case_id": case.get("case_id"),
        "title": case.get("title"),
        "status": "baseline_emulator_output",
        "pages": [{"page_no": i + 1, "title": None, "text": ""} for i in range(n_pages)],
        "sources": [{"file": os.path.basename(p), "parsed": t is not None}
                    for p, _r, t in materials],
        "notes_prepared": False, "evidence_locators": 0, "qa_items": 0,
        "disclaimer": "deterministic baseline emulator (see references/GAIN-PROTOCOL.md §2); "
                      "not the platform's real base Agent",
    }
    with open(os.path.join(out_dir, "baseline_result.json"), "w", encoding="utf-8") as fh:
        json.dump(envelope, fh, ensure_ascii=False, indent=2)
    return {"deck": deck_path, "pages": n_pages, "paragraphs_available": len(paras),
            "figures_embedded": len(figs)}


# --------------------------------------------------------------------- skill arm
def run_skill(skill_dir, case_path, out_dir):
    main = os.path.join(skill_dir, "scripts", "main.py")
    if not os.path.exists(main):
        return {"exit_code": None, "seconds": None, "error": "main.py not found"}
    t0 = time.time()
    proc = subprocess.run([sys.executable, main, "--case", case_path,
                           "--out", out_dir, "--quiet"],
                          capture_output=True, text=True)
    return {"exit_code": proc.returncode, "seconds": round(time.time() - t0, 2),
            "stdout_tail": (proc.stdout or "").strip().splitlines()[-1:] or []}


# -------------------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description="fair A/B harness for the talk-organizer Skill")
    ap.add_argument("--case", required=True, help="path to case.json")
    ap.add_argument("--work", required=True, help="scratch directory for both arms")
    ap.add_argument("--skill-dir", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    help="package root (default: this script's parent)")
    ap.add_argument("--report", default=None, help="where to write the JSON report")
    ap.add_argument("--skip-arm-b", action="store_true", help="measure arm A only")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    case_path = os.path.abspath(args.case)
    if not os.path.exists(case_path):
        print("FATAL: case.json not found: %s" % args.case)
        return 2
    case = read_json(case_path)
    case_dir = os.path.dirname(case_path)
    work = os.path.abspath(args.work)
    os.makedirs(work, exist_ok=True)
    materials = resolve_materials(case, case_dir)
    sources = [t for _p, _r, t in materials]
    frozen = case.get("slide_count")

    report = {
        "harness": "gain_ab.py",
        "case": {"path": os.path.basename(case_path), "case_id": case.get("case_id"),
                 "slide_count": frozen, "duration_min": case.get("duration_min"),
                 "materials": [{"file": os.path.basename(p), "role": r, "text_read": t is not None}
                               for p, r, t in materials]},
        "arms": {},
        "notes": ["A 臂 = 本脚本内置的确定性基线模拟器（代理臂），不是平台真实基础 Agent。",
                  "缺项记 0/null 并标 available=false，不跳过。",
                  "指标定义见 references/GAIN-PROTOCOL.md §4。"],
    }

    # ---- arm A: baseline (two rounds when the first pass violates the frozen count)
    arm_a = os.path.join(work, "arm-A")
    os.makedirs(arm_a, exist_ok=True)
    t0 = time.time()
    a1 = build_baseline_deck(case, materials, arm_a)
    seconds_a = time.time() - t0
    rounds_a = 1
    pages_before_rework = a1["pages"]
    if isinstance(frozen, int) and a1["pages"] != frozen:
        t1 = time.time()
        a2 = build_baseline_deck(case, materials, arm_a, target_pages=frozen)
        seconds_a += time.time() - t1
        rounds_a = 2
        a1 = a2
    deck_a = measure_deck(os.path.join(arm_a, "baseline_deck.pptx"), sources)
    report["arms"]["A"] = {
        "kind": "baseline_emulator", "out_dir": "arm-A",
        "wall_seconds": round(seconds_a, 2), "wall_seconds_first_pass_only": None,
        "rerun_rounds_to_frozen": rounds_a,
        "pages_before_rework": pages_before_rework,
        "pages_final": a1["pages"],
        "deck": deck_a,
        "contract": {"available": False, "result_json": False},
    }

    # ---- arm B: this package
    if not args.skip_arm_b:
        arm_b = os.path.join(work, "arm-B")
        os.makedirs(arm_b, exist_ok=True)
        run = run_skill(args.skill_dir, case_path, arm_b)
        deck_b = measure_deck(os.path.join(arm_b, "editable_deck.pptx"), sources)
        contract_b = measure_contract(arm_b, frozen)
        rounds_b = 1
        if (deck_b.get("slides") is not None and isinstance(frozen, int)
                and deck_b.get("slides") != frozen):
            rounds_b = None  # would need rework; reported honestly as None
        report["arms"]["B"] = {
            "kind": "skill", "out_dir": "arm-B", "run": run,
            "wall_seconds": run.get("seconds"), "rerun_rounds_to_frozen": rounds_b,
            "deck": deck_b, "contract": contract_b,
        }

    # ---- delta table (only the pairs that exist on both sides)
    deltas = {}
    a, b = report["arms"].get("A", {}).get("deck", {}), report["arms"].get("B", {}).get("deck", {})
    for key in ("slides", "notes_coverage", "max_body_paragraphs", "mean_body_chars",
                "verbatim_grounded_ratio", "numbers_in_source_ratio", "embedded_pictures"):
        if isinstance(a.get(key), (int, float)) and isinstance(b.get(key), (int, float)):
            deltas[key] = round(b[key] - a[key], 4)
    if "B" in report["arms"]:
        deltas["result_json_top_level_keys"] = report["arms"]["B"]["contract"].get("top_level_keys", 0)
        deltas["evidence_rows"] = report["arms"]["B"]["contract"].get("evidence_rows", 0)
        deltas["qa_items"] = report["arms"]["B"]["contract"].get("qa_items", 0)
    report["deltas_B_minus_A"] = deltas
    report["generated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")

    out = args.report or os.path.join(work, "gain_report.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    if not args.quiet:
        print("arm A (baseline emulator): slides=%s notes=%.2f max_paras=%s pics=%s rounds=%s %.2fs"
              % (a.get("slides"), a.get("notes_coverage", 0), a.get("max_body_paragraphs"),
                 a.get("embedded_pictures"), report["arms"]["A"]["rerun_rounds_to_frozen"],
                 report["arms"]["A"]["wall_seconds"]))
        if "B" in report["arms"]:
            c = report["arms"]["B"]["contract"]
            print("arm B (this Skill):        slides=%s notes=%.2f locators=%s qa=%s "
                  "result_keys=%s exit=%s %.2fs"
                  % (b.get("slides"), b.get("notes_coverage", 0), c.get("locator_coverage"),
                     c.get("qa_items"), c.get("top_level_keys"),
                     report["arms"]["B"]["run"].get("exit_code"),
                     report["arms"]["B"]["wall_seconds"] or 0))
        print("report: %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
