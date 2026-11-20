#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
planner.py — turn raw materials + case constraints into a page-level talk plan.

The plan is the *editorial* artifact of the Skill: it decides the narrative
order (not the paper's table of contents), the unique claim of every page,
its evidence anchor, figure binding, one-line script and Q&A preparation.
Everything here is driven by (a) real material content and (b) the editable
rules in templates/talk_config.json — nothing is hard-coded per case.
"""

import os
import re

from common import utc_now

DEFAULT_AUDIENCE = {
    "description": "(未在案例中给出听众描述)",
    "expertise": "familiar",
    "background_ratio": 0.18,
    "evidence_depth": "medium",
    "notes": "听众信息缺失，按领域熟悉度『familiar』与中等证据深度保守处理；如知悉真实听众请覆写。",
}

EXPERTISE_RULES = [
    (re.compile(r"(专家|评审|评委|同行|审稿|reviewer|expert|defense|答辩|professor|doctor)", re.I), "expert", 0.10),
    (re.compile(r"(组会|研究生|学生|合作者|同事|lab|实验室|intern|familiar|组内|导师)", re.I), "familiar", 0.18),
    (re.compile(r"(公众|非专业|跨学科|本科生|lay|general audience|科普|外行|科普)", re.I), "lay", 0.30),
]

REPORT_GOAL_MAP = {
    "group_meeting": [
        "讲清当前进度与主要风险",
        "让合作者能听懂方法要点并对照图纸/图表",
        "为下一步方向获取反馈与对齐",
    ],
    "defense": [
        "让评委认可研究问题、创新点与边界",
        "证明方法与结果的证据链完整、可复现",
        "对追问能按页快速定位证据",
    ],
    "review": [
        "让评审看到每条结论的证据强度与来源定位",
        "澄清方法、数据与指标口径",
        "明确结论的适用范围与不确定性",
    ],
}

BLOCK_LABELS = {
    "title": "封面",
    "agenda": "目录",
    "motivation": "研究问题与动机",
    "background": "背景与术语铺垫",
    "method": "方法与材料",
    "results": "结果与证据",
    "conclusion_risk": "结论与风险",
    "innovation_limits": "创新点与边界",
    "conclusion": "结论与展望",
    "qa": "问答准备（备用页）",
}

WEAK_BLOCK_TEMPLATES = {
    "motivation": "研究问题与动机：{section} 段陈述的研究动因（源材料概括，证据强度弱）",
    "background": "背景铺垫：{section} 段给出的领域背景（源材料概括，证据强度弱）",
    "method": "方法与材料：{section} 段描述的方法要点（源材料概括，证据强度弱）",
    "results": "结果：{section} 段报告的结果要点（源材料概括，证据强度弱）",
    "conclusion": "结论：{section} 段的收束表述（源材料概括，证据强度弱）",
    "innovation_limits": "创新点与边界：{section} 段的边界表述（源材料概括，证据强度弱）",
    "conclusion_risk": "结论与风险：{section} 段的风险/收束表述（源材料概括，证据强度弱）",
}


def resolve_audience(case):
    raw = str(case.get("audience") or "")
    for rule, expertise, ratio in EXPERTISE_RULES:
        if rule.search(raw):
            return {
                "description": raw.strip() or DEFAULT_AUDIENCE["description"],
                "expertise": expertise,
                "background_ratio": ratio,
                "evidence_depth": "high" if expertise == "expert" else ("medium" if expertise == "familiar" else "shallow"),
                "notes": "",
            }
    return dict(DEFAULT_AUDIENCE, description=raw.strip() or DEFAULT_AUDIENCE["description"])


def resolve_success_criteria(case, report_type):
    explicit = case.get("success_criteria")
    if isinstance(explicit, list) and explicit:
        return [str(x) for x in explicit]
    return REPORT_GOAL_MAP.get(report_type, REPORT_GOAL_MAP["group_meeting"])


def _alloc_pages(report_type, slide_target, audience, config):
    """Return block id -> page count honoring the frozen slide target."""
    blocks = config["blocks"]
    if report_type not in blocks:
        report_type = "group_meeting"
    weights = dict(blocks[report_type].get("weights", {}))
    order = list(blocks[report_type].get("order", []))
    fixed = set(blocks[report_type].get("fixed", []))  # blocks with stable count
    # background block scales with audience background_ratio
    bkg = "background"
    if bkg in weights and bkg not in fixed:
        base_bkg = weights.get(bkg, 0)
        scale = audience.get("background_ratio", 0.18) / 0.18
        weights[bkg] = base_bkg * scale

    counts = {}
    used = 0
    temp = {}
    for bid in order:
        if bid in fixed:
            n = 1
            used += n
            counts[bid] = n
        else:
            temp[bid] = weights.get(bid, 0.1)
    total_w = sum(temp.values()) or 1.0
    remaining = max(slide_target - used, 3)
    for bid in order:
        if bid in temp:
            counts[bid] = max(1, round(remaining * temp[bid] / total_w))
        elif bid not in counts:
            counts[bid] = 1
    # correct drift to hit target exactly
    cur = sum(counts.values())
    diff = slide_target - cur
    if diff > 0:
        counts["results"] = counts.get("results", 1) + diff
    elif diff < 0:
        biggest = None
        for bid in order:
            if counts.get(bid, 0) > 1:
                biggest = bid
                break
        if biggest:
            counts[biggest] = counts[biggest] + diff
    return counts, order


def _intro_section(claim):
    """True when the claim sits in a 引言/背景-like section (not the abstract:
    abstract headlines are results/claims summaries, not background context)."""
    path = (claim.get("section") or "").lower()
    return any(k in path for k in ("引言", "背景", "introduction", "related work"))


def _section_matches(claim, block):
    """A section whose path matches the block's topic outranks keyword-only
    classification — the claim then anchors to the paper's own structure."""
    path = (claim.get("section") or "").lower()
    if block in ("motivation", "background"):
        return any(k in path for k in ("引言", "摘要", "问题", "动机", "背景", "abstract", "introduction"))
    if block == "method":
        return any(k in path for k in ("方法", "评估", "数据", "实验", "methods"))
    if block == "results":
        return any(k in path for k in ("结果", "评估", "results"))
    if block in ("limits", "innovation_limits", "conclusion_risk"):
        return any(k in path for k in ("局限", "讨论", "结论", "limitation", "discussion"))
    if block == "conclusion":
        return any(k in path for k in ("结论", "总结", "摘要", "conclusion", "abstract"))
    return False


def pick_claims(claim_buckets, kind, want, used_keys, block=None):
    """Pick up to `want` claims: section-match first, strong-first, source
    order; never reuse a claim.  For introduction blocks (motivation/
    background) claims of other kinds that sit in 引言/摘要 sections are also
    eligible, so background pages get real context lines instead of framed
    placeholders."""
    pool = [c for c in claim_buckets if c["kind"] == kind and c["key"] not in used_keys]
    if block in ("motivation", "background"):
        extra = [c for c in claim_buckets
                 if c["key"] not in used_keys and c["kind"] != kind
                 and _intro_section(c)]
        for c in extra:
            if c not in pool:
                pool.append(c)
    _rank = {"strong": 0, "medium": 1, "weak": 2}
    pool.sort(key=lambda c: (0 if _section_matches(c, block) else 1,
                             _rank.get(c.get("strength"), 3), c.get("line_no", 0)))
    chosen = pool[:want]
    for c in chosen:
        used_keys.add(c["key"])
    return chosen


def _first_content_section(rec):
    if rec and rec.get("parsed") and rec.get("sections"):
        for s in rec["sections"]:
            if s.get("heading") == "__preamble__":
                continue
            # single top-level heading at the very top of the file = document
            # title, not content
            if len(s.get("path", [])) == 1 and s.get("start_line", 0) <= 3:
                continue
            if s.get("lines"):
                return s
        return rec["sections"][0]
    return None


def _page_title(claim_text):
    """Short page title: prefer the part before the first '：' when it is
    short, otherwise a truncated first sentence."""
    head = claim_text.split("：", 1)[0].strip()
    if 3 <= len(head) <= 30:
        return head
    return _one_liner(claim_text, 24)


def _short_section(section):
    parts = section.split(" / ")
    if len(parts) >= 2:
        return parts[-1]
    return section


def _page_from_claim(claim, block, page_no, material_files, change_records, config):
    title = _page_title(claim["text"])
    evidence = [{
        "source_file": claim["source_file"],
        "section": claim["section"],
        "line_no": claim["line_no"],
        "locator": "L%d · §%s" % (claim["line_no"], _short_section(claim["section"])),
        "quote": claim["text"],
        "strength": claim["strength"],
    }]
    figure_ref = claim["refs"][0] if claim["refs"] else None
    figure_file, bind_note = _bind_figure(figure_ref, claim["source_file"], material_files)
    if bind_note:
        change_records.append({"at": utc_now(), "step": "figure-binding",
                               "action": bind_note})
    page = {
        "page_no": page_no,
        "block": block,
        "block_label": BLOCK_LABELS.get(block, block),
        "title": title,
        "claim": claim["text"],
        "one_liner": _one_liner(claim["text"]),
        "evidence": evidence,
        "figure_ref": figure_ref,
        "figure_file": figure_file,
        "notes": "",
        "strength": claim["strength"],
        "qa": [],
        "derived": False,
    }
    page["notes"] = _notes_for(page)
    return page


def _bind_figure(figure_ref, source_file, material_files):
    """Try to locate a real figure image file that matches the reference.

    `material_files` is a list of {path, basename, in_material_dir}.  Matching
    is by token overlap, e.g. 'Fig. 2' vs 'fig2.png' / 'figure_2.png'.
    """
    if not figure_ref:
        return None, None
    tokens = re.sub(r"[^0-9A-Za-z]+", " ", figure_ref).lower().split()
    key = "".join(tokens[-2:]) if len(tokens) >= 2 else "".join(tokens)
    for mf in material_files:
        stem = os.path.splitext(mf["basename"])[0].lower()
        norm = re.sub(r"[^0-9a-z]+", "", stem)
        if key and key[-2:] and (key in norm or key[-2:] in norm):
            return mf["path"], "figure %s bound to image file %s" % (figure_ref, mf["basename"])
    return None, ("figure %s has no matching image file in materials; deck uses a "
                  "placeholder box (honest placeholder, not invented artwork)" % figure_ref if figure_ref else None)


def _mask_sentence_text(text):
    """Length-preserving masking so sentence splitting in _one_liner does not
    break on decimal points (92.3%) or caption abbreviations (Fig. 2)."""
    s = re.sub(r"(?<=\d)\.(?=\d)", "\x01", text)
    s = re.sub(r"(?i)(\bfigs?\.|\btabs?\.|\bschemes?\.|\bfigures?\.)",
               lambda m: m.group(1).replace(".", "\x02"), s)
    return s


def _one_liner(text, limit=64):
    masked = _mask_sentence_text(text)
    cut = None
    for idx, ch in enumerate(masked):
        if ch in "。；;?!":
            cut = idx
            break
    t = text[:cut].strip() if cut is not None else text.strip()
    if len(t) <= limit:
        return t or text[:limit]
    seg = t[:limit]
    for sep in "，、：: ":
        i = seg.rfind(sep)
        if i > max(0, limit // 3):
            seg = seg[: i + 1]
            break
    else:
        # CJK has no word spaces: hard cut, but never cut a number in half
        k = limit
        while k < len(t) and (t[k].isdigit() or t[k] in ".%‰"):
            k += 1
            if k > limit + 16:
                break
        seg = t[:k]
    return seg.strip() + "…"


def _notes_for(page):
    ev = page["evidence"][0] if page["evidence"] else None
    lines = []
    lines.append("【本页主张】%s" % page["claim"])
    if ev:
        lines.append("【证据】%s（%s，证据强度：%s）" % (ev["quote"][:120], ev["locator"], ev["strength"]))
    if page["figure_ref"]:
        lines.append("【图表】本页指向 %s；%s" % (
            page["figure_ref"],
            "使用材料附图" if page["figure_file"] else "材料未提供对应图片文件，页内为占位框，讲解时以原论文图现场展示"))
    lines.append("【讲解】%s" % page["one_liner"])
    if page["qa"]:
        for q in page["qa"]:
            lines.append("【备答】%s → %s" % (q["question"], "；".join(q["answer_points"])))
    return "\n".join(lines)


def build_question_bank(plan, case, config):
    """Pre-build 问答准备: one question per limits claim + per strong result claim."""
    bank = []
    limits = [p for p in plan["pages"] if p["block"] in ("limits", "conclusion_risk")]
    strong_results = [p for p in plan["pages"] if p["block"] == "results" and p["strength"] == "strong"]
    seen_q = set()
    for p in limits[:3]:
        q = "局限『%s』是否影响本工作结论的适用范围？" % p["claim"][:40]
        if q in seen_q:
            continue
        seen_q.add(q)
        bank.append({
            "question": q,
            "answer_points": ["指向本页证据 %s" % p["evidence"][0]["locator"],
                              "在结论页强调结论只适用于源材料声明范围"],
            "to_pages": [p["page_no"]],
            "source_claim": p["claim"],
        })
    for p in strong_results[:3]:
        q = "『%s』这条结论的证据强度和统计基础是什么？" % p["claim"][:40]
        if q in seen_q:
            continue
        seen_q.add(q)
        bank.append({
            "question": q,
            "answer_points": ["证据定位：%s，强度%s" % (p["evidence"][0]["locator"], p["strength"]),
                              "如需更细口径，引导到材料原文对应章节"],
            "to_pages": [p["page_no"]],
            "source_claim": p["claim"],
        })
    # templates from config for the report type
    tpl = config["questions"].get(case.get("report_type", "group_meeting"), [])
    for t in tpl[:2]:
        q = t.get("question", "")
        if not q or q in seen_q:
            continue
        seen_q.add(q)
        bank.append({"question": q, "answer_points": t.get("answers", []),
                     "to_pages": t.get("to_pages", []), "source_claim": ""})
    return bank


def build_plan(case, material_records, talk_config, change_records):
    """Main planning entry point.  Returns the plan dict."""
    report_type = str(case.get("report_type") or "group_meeting")
    if report_type not in talk_config["blocks"]:
        report_type = "group_meeting"
    audience = resolve_audience(case)
    duration = case.get("duration_min")
    try:
        duration = float(duration) if duration is not None else 20.0
    except (TypeError, ValueError):
        duration = 20.0
    slide_target = case.get("slide_count")
    if slide_target is None:
        slide_target = int(round(duration * 60.0 / 85.0)) if duration else 12
    slide_target = max(6, min(30, int(slide_target)))

    # ---- bucket all claim candidates from parsed materials ----
    claim_buckets = []
    material_files = []
    for rec in material_records:
        material_files.append({"path": rec["path"], "basename": rec["file"]})
        for c in rec.get("claims", []):
            c["key"] = "%s::%d::%s" % (rec["file"], c["line_no"], c["text"][:40])
            c["source_file"] = rec["file"]
            claim_buckets.append(c)

    counts, order = _alloc_pages(report_type, slide_target, audience, talk_config)
    used_keys = set()

    pages = []
    page_no = 0

    def new_page(block):
        nonlocal page_no
        page_no += 1
        return page_no

    for bid in order:
        want = counts.get(bid, 1)
        for i in range(want):
            pn = new_page(bid)
            if bid == "title":
                pages.append({
                    "page_no": pn, "block": bid, "block_label": BLOCK_LABELS[bid],
                    "title": str(case.get("title") or "学术汇报"),
                    "claim": "封面：标题 + 汇报人/时间 + 案例来源",
                    "one_liner": "开场致谢并交代汇报目标。",
                    "evidence": [], "figure_ref": None, "figure_file": None,
                    "notes": "【本页主张】封面\n【报告目标】%s\n【讲解】%s\n【备答】确认时长与重点，提醒可随时打断提问。"
                             % (str(case.get("report_goal") or ""), "开场致谢并交代汇报目标。"),
                    "strength": None, "qa": [], "derived": False,
                })
                continue
            if bid == "agenda":
                seq = " / ".join(BLOCK_LABELS.get(b, b) for b in order if b not in ("title", "agenda", "qa"))
                pages.append({
                    "page_no": pn, "block": bid, "block_label": BLOCK_LABELS[bid],
                    "title": "目录", "claim": "按叙事主线列出段落：%s" % seq,
                    "one_liner": "告诉听众我们将按什么顺序讲、为什么是这个顺序。",
                    "evidence": [], "figure_ref": None, "figure_file": None,
                    "notes": "【本页主张】目录\n【讲解】按『问题—方法—结果—结论—问答』的叙事顺序预告，并说明顺序依听众与时长设定。",
                    "strength": None, "qa": [], "derived": False,
                })
                continue
            if bid == "qa":
                pages.append({
                    "page_no": pn, "block": bid, "block_label": BLOCK_LABELS[bid],
                    "title": "问答准备（备用页）",
                    "claim": "预判追问：局限与证据强度问题可在备用页定位证据",
                    "one_liner": "预留页，用于回答关于局限与证据强度的追问。",
                    "evidence": [{"source_file": rec["file"], "section": "(问答准备)",
                                  "line_no": 0, "locator": "(问答准备)", "quote": "",
                                  "strength": "weak"} for rec in material_records[:1]],
                    "figure_ref": None, "figure_file": None,
                    "notes": "【本页主张】问答准备\n【讲解】本页为备用页：将所有预判追问、回答要点与对应证据定位收拢于此。",
                    "strength": None, "qa": [], "derived": False,
                })
                continue
            # ---- content blocks ----
            kind_map = {"motivation": "introduction", "background": "introduction",
                        "method": "method", "results": "results",
                        "conclusion_risk": ["limits", "conclusion"],
                        "innovation_limits": "limits", "conclusion": "conclusion"}
            kinds = kind_map.get(bid, "general")
            if not isinstance(kinds, list):
                kinds = [kinds]
            claim = None
            for k in kinds:
                picked = pick_claims(claim_buckets, k, 1, used_keys, block=bid)
                if picked:
                    claim = picked[0]
                    break
            if claim is None:
                # no direct claim -> framed page from section text (weak, honest)
                rec = material_records[0] if material_records else None
                section = "(无源材料)"
                line_no = 1
                if rec and rec["parsed"] and rec["sections"]:
                    first = _first_content_section(rec)
                    if first:
                        section = " / ".join(first["path"])
                        line_no = first.get("start_line", 1)
                claim = {
                    "text": WEAK_BLOCK_TEMPLATES.get(bid, "内容页").format(section=section),
                    "line_no": line_no,
                    "section": section,
                    "kind": "general",
                    "strength": "weak",
                    "refs": [],
                    "numbers": [],
                    "source_file": rec["file"] if rec else "(无源材料)",
                    "key": "framed-%s-%s" % (bid, rec["file"] if rec else "none"),
                }
                change_records.append({"at": utc_now(), "step": "framing",
                                       "action": "block '%s' 在材料中无直接主张，页面由源材料章节概括而成（证据强度 weak）" % bid})
            page = _page_from_claim(claim, bid, pn, material_files, change_records, talk_config)
            if bid == "results" and i > 0 and claim.get("refs") is None:
                pass
            pages.append(page)

    # ---- Q&A: attach bank + wire to pages ----
    plan = {
        "case_id": case.get("case_id"),
        "report_goal": str(case.get("report_goal") or ""),
        "audience": audience,
        "timing": {"duration_min": duration,
                   "slide_target": slide_target,
                   "seconds_per_slide": round(duration * 60.0 / slide_target, 1) if slide_target else None},
        "narrative": {"report_type": report_type,
                      "order_blocks": order,
                      "template": talk_config["narrative"][report_type] if report_type in talk_config["narrative"] else talk_config["narrative"]["group_meeting"]},
        "success_criteria": resolve_success_criteria(case, report_type),
        "pages": pages,
        "question_bank": [],
        "terminology": {"assumed": [], "explain_on_page": [], "glossary": []},
        "generated_by": "planner.py of academic-talk-organizer (efficiency-3)",
        "generated_at": utc_now(),
    }
    from evidence import collect_terms
    for rec in material_records:
        for term, abbr in collect_terms(rec)[:20]:
            pair = {"term": term, "abbr": abbr, "source_file": rec["file"]}
            if pair not in plan["terminology"]["glossary"]:
                plan["terminology"]["glossary"].append(pair)
    if plan["terminology"]["glossary"]:
        go = [g["abbr"] for g in plan["terminology"]["glossary"][:6]]
        plan["terminology"]["explain_on_page"] = go
        plan["terminology"]["assumed"] = (
            [] if audience["expertise"] == "expert" else go)

    bank = build_question_bank(plan, case, talk_config)
    plan["question_bank"] = bank
    by_page = {}
    for q in bank:
        for pn in q["to_pages"]:
            by_page.setdefault(pn, []).append(q)
    for p in pages:
        p["qa"] = by_page.get(p["page_no"], [])
        p["notes"] = _notes_for(p)
    return plan