# -*- coding: utf-8 -*-
"""deckplan.py — deterministic slide plan from extracted content.

Maps content → page structure: cover, agenda, background/question,
methods, one page per result figure/table (or grouped when slide budget is
tight), discussion, limitations, conclusion, closing evidence-map page.
Every page carries: page_type, title, claims, bullets, figure/table refs,
speaker-note draft, and evidence locators with their source.
Same input ⇒ same plan (pure function of content + constraints).
"""
from __future__ import annotations

import os
import re
from common import dump_json, utf8_writer

PAGE_TYPES = ("cover", "agenda", "background", "methods", "results", "discussion",
              "limitations", "conclusion", "evidence_map", "thankyou")


def _num(s) -> int:
    """Parse 图3 / Figure 3.2 / fig4 into int-ish sortable tuple."""
    digits = "".join(ch for ch in str(s) if ch.isdigit() or ch == ".")
    try:
        return tuple(int(p) for p in digits.split("."))
    except Exception:
        return (0,)


def plan(content: dict, constraints: dict | None = None) -> dict:
    constraints = constraints or {}
    lang = content.get("language") or "zh"

    def T(zh, en):
        return zh if lang == "zh" else en

    sec = content["sections"]
    figs = sorted(content.get("figures") or [], key=lambda f: _num(f.get("id")))
    tb = sorted(content.get("tables") or [], key=lambda t: _num(t.get("id")))

    results = sec.get("results") or []
    question = sec.get("question") or []
    methods = sec.get("methods") or []
    discussion = sec.get("discussion") or []
    limits = sec.get("limitations") or []
    conclusion = sec.get("conclusion") or []

    # figure/table refs mentioned by result texts (and structured refs)
    def _norm_ref(rid) -> str:
        s = str(rid)
        for pre in ("图", "figure", "fig.", "fig", "表", "table", "tbl"):
            if s.lower().startswith(pre):
                s = s[len(pre):]
                break
        return s.strip()

    def claim_refs(item) -> dict:
        text = item.get("text", "") if isinstance(item, dict) else str(item)
        frefs = sorted(set(re.findall(r"(?:图|Figure|Fig\.?)\s*([0-9A-Za-z.]+)", text, re.I)))
        trefs = sorted(set(re.findall(r"(?:表|Table)\s*([0-9A-Za-z.]+)", text, re.I)))
        if isinstance(item, dict):
            frefs += [ _norm_ref(x) for x in (item.get("figure_refs") or []) ]
            trefs += [ _norm_ref(x) for x in (item.get("table_refs") or []) ]
        return {"figure_refs": sorted(set(frefs)), "table_refs": sorted(set(trefs))}

    target = int(constraints.get("slide_count") or content.get("slide_count_target") or 0)
    target = min(max(target, 6), 18) if target else 12

    # budget allocation: fixed pages cost 5 (cover/agenda/background/methods/
    # closing evidence) + optional discussion/limitations/conclusion = +2..3
    fixed = 5
    flexible = max(target - fixed - 3, 1)  # after reserving disc/limit/conc
    result_pages_needed = 0
    for r in results:
        frefs = claim_refs(r).get("figure_refs")
        trefs = claim_refs(r).get("table_refs")
        has_fig = any(f["id"] == fr for f in figs for fr in frefs)
        has_tbl = any(t["id"] == tr for t in tb for tr in trefs)
        if has_fig or has_tbl:
            result_pages_needed += 1

    # group results that carry no figure/table onto the last result page,
    # or into "results overview" if none carries media.
    media_results = []
    text_results = []
    for r in results:
        frefs = claim_refs(r).get("figure_refs")
        trefs = claim_refs(r).get("table_refs")
        if any(f["id"] == fr for f in figs for fr in frefs) or \
           any(t["id"] == tr for t in tb for tr in trefs):
            media_results.append(r)
        else:
            text_results.append(r)

    pages = []

    # 0 cover
    pages.append({
        "page_type": "cover", "page_no": len(pages) + 1,
        "title": content.get("title") or T("（标题）", "(title)"),
        "claims": [],
        "bullets": [],
        "figure_refs": [], "table_refs": [],
        "notes": (
            T(f"开场（建议 {_est_min(content)} 分钟总时长）。一句话介绍题目与核心论点："
              f"「{content.get('title') or ''}」。",
              f"Opening (total ~{_est_min(content)} min). One sentence stating the topic and core claim: "
              f"\"{content.get('title') or ''}\".")),
        "evidence": [],
    })

    # 1 agenda
    agenda_items = [
        T("背景与问题", "Background & question"),
        T("方法", "Methods"),
        T("结果", "Results"),
        T("讨论与结论", "Discussion & conclusion"),
    ]
    pages.append({
        "page_type": "agenda", "page_no": len(pages) + 1,
        "title": T("议程", "Agenda"), "claims": [], "bullets": agenda_items,
        "figure_refs": [], "table_refs": [],
        "notes": T("概述汇报结构，提示听众各环节的讲解顺序。",
                   "Outline; point at the narration order used in this deck."),
        "evidence": [],
    })

    # 2 background / question
    q_bullets = [q.get("text") for q in question][:6]
    pages.append({
        "page_type": "background", "page_no": len(pages) + 1,
        "title": T("研究背景与研究问题", "Background & Research Question"),
        "claims": q_bullets[:2] if q_bullets else [],
        "bullets": q_bullets,
        "figure_refs": [], "table_refs": [],
        "notes": (T("按证据顺序讲背景：先重要性，后空白，落到本工作的研究问题。",
                    "Narrate background from importance to gap to the research question.")),
        "evidence": [{"claim": b, "loc": q.get("source", "")} for b, q in zip(q_bullets, question)],
    })

    # 3 methods
    m_bullets = [m.get("text") for m in methods][:8]
    pages.append({
        "page_type": "methods", "page_no": len(pages) + 1,
        "title": T("方法", "Methods"),
        "claims": m_bullets[:2] if m_bullets else [],
        "bullets": m_bullets,
        "figure_refs": [], "table_refs": [],
        "notes": (T("讲清材料与实验流程；避免进入结果细节。", "Methods only; defer results.")),
        "evidence": [{"claim": b, "loc": m.get("source", "")} for b, m in zip(m_bullets, methods)],
    })

    # result pages
    consumed = 0
    pool = [r for r in media_results] + [r for r in text_results]
    grouped = []
    if result_pages_needed and (target - fixed - 3) >= result_pages_needed:
        for r in pool:
            grouped.append([r])
    else:
        # group non-media claims into the first/collector result page
        for r in pool:
            frefs = claim_refs(r).get("figure_refs")
            trefs = claim_refs(r).get("table_refs")
            is_media = bool(frefs or trefs)
            if not is_media:
                if grouped:
                    grouped[0].append(r)
                else:
                    grouped.append([r])
            else:
                grouped.append([r])
    result_claim_n = 0
    for grp in grouped:
        result_claim_n += 1
        claims = [r.get("text", "") if isinstance(r, dict) else str(r) for r in grp]
        frefs = sorted({f for r in grp for f in claim_refs(r).get("figure_refs", [])})
        trefs = sorted({t for r in grp for t in claim_refs(r).get("table_refs", [])})
        figs_on = [f for f in figs if f["id"] in frefs]
        tb_on = [t for t in tb if t["id"] in trefs]
        title = T(f"结果 {result_claim_n}", f"Results {result_claim_n}")
        if len(grp) == 1 and figs_on:
            title = f"结果：{figs_on[0]['id']} {figs_on[0].get('caption', '')}"[:60] or title
        pages.append({
            "page_type": "results", "page_no": len(pages) + 1,
            "title": title,
            "claims": claims,
            "bullets": [],
            "figure_refs": frefs, "table_refs": trefs,
            "figures_on_page": [{"id": f["id"], "caption": f.get("caption", ""),
                                 "source": f.get("source", ""), "file": f.get("file_abs", ""),
                                 "exists": f.get("file_exists", False)} for f in figs_on],
            "tables_on_page": [{"id": t["id"], "caption": t.get("caption", ""),
                                "source": t.get("source", ""), "rows": t.get("rows", [])} for t in tb_on],
            "notes": (T(f"讲结果主张，然后指向 {'/'.join(frefs + trefs) or '数据'}：证据在哪、结论是什么、30 秒内讲完。",
                        f"State the claim, then point at {'/'.join(frefs + trefs) or 'data'}: where the evidence is and what it shows.")),
            "evidence": [{"claim": c, "loc": r.get("source", "")} for c, r in zip(claims, grp)],
        })
        consumed += 1

    if not grouped and results:
        pages.append({
            "page_type": "results", "page_no": len(pages) + 1,
            "title": T("结果概览", "Results overview"),
            "claims": [r.get("text", "") if isinstance(r, dict) else str(r) for r in results[:6]],
            "bullets": [], "figure_refs": [], "table_refs": [],
            "notes": T("概览式讲述结果要点。", "Summarize result highlights."),
            "evidence": [{"claim": (r.get("text", "") if isinstance(r, dict) else str(r)),
                          "loc": r.get("source", "") if isinstance(r, dict) else ""} for r in results[:6]],
        })

    # discussion / limitations / conclusion
    if discussion:
        d_bullets = [d.get("text") for d in discussion][:5]
        pages.append({
            "page_type": "discussion", "page_no": len(pages) + 1,
            "title": T("讨论", "Discussion"), "claims": d_bullets[:1], "bullets": d_bullets,
            "figure_refs": [], "table_refs": [],
            "notes": T("把结果放回文献/场景，讲含义与可取之处。", "Interpret results in context."),
            "evidence": [{"claim": b, "loc": d.get("source", "")} for b, d in zip(d_bullets, discussion)],
        })
    if limits:
        l_bullets = [l.get("text") for l in limits][:5]
        pages.append({
            "page_type": "limitations", "page_no": len(pages) + 1,
            "title": T("局限与不确定性", "Limitations & uncertainty"),
            "claims": l_bullets[:1], "bullets": l_bullets,
            "figure_refs": [], "table_refs": [],
            "notes": T("诚实列出局限，防止提问环节被动。", "State limitations openly."),
            "evidence": [{"claim": b, "loc": l.get("source", "")} for b, l in zip(l_bullets, limits)],
        })
    if conclusion:
        c_bullets = [c.get("text") for c in conclusion][:4]
        pages.append({
            "page_type": "conclusion", "page_no": len(pages) + 1,
            "title": T("结论", "Conclusion"), "claims": c_bullets[:1], "bullets": c_bullets,
            "figure_refs": [], "table_refs": [],
            "notes": T("回到研究问题给出回答，附一句展望。", "Answer the research question."),
            "evidence": [{"claim": b, "loc": c.get("source", "")} for b, c in zip(c_bullets, conclusion)],
        })

    # ---- trim policy: respect the slide-count target deterministically -----
    # Appendix (evidence-map + thank-you) is part of the delivered deck and
    # counts toward the target, so the story body budget is target - 2.
    body_target = max(target - 2, 4)
    if len(pages) > body_target:
        disc = next((p for p in pages if p["page_type"] == "discussion"), None)
        lim = next((p for p in pages if p["page_type"] == "limitations"), None)
        if disc and lim:
            merged = {
                "page_type": "discussion",
                "title": T("讨论与局限", "Discussion & limitations"),
                "claims": (disc.get("claims") or [])[:1] + (lim.get("claims") or [])[:1],
                "bullets": (disc.get("bullets") or []) + (lim.get("bullets") or []),
                "figure_refs": [], "table_refs": [],
                "notes": T("先讲结果含义，再诚实列出局限。", "Interpret results, then state limitations openly."),
                "evidence": (disc.get("evidence") or []) + (lim.get("evidence") or []),
            }
            pages[:] = [p for p in pages if p["page_type"] not in ("discussion", "limitations")]
            pages.insert(len(pages), merged)  # keep position before conclusion
        if len(pages) > body_target:
            agenda = next((p for p in pages if p["page_type"] == "agenda"), None)
            if agenda:
                pages.remove(agenda)
        if len(pages) > body_target:
            res = [p for p in pages if p["page_type"] == "results"]
            if len(res) >= 2:
                a, b = res[-2], res[-1]
                a["claims"] = (a.get("claims") or []) + (b.get("claims") or [])
                a["figure_refs"] = sorted(set((a.get("figure_refs") or []) + (b.get("figure_refs") or [])))
                a["table_refs"] = sorted(set((a.get("table_refs") or []) + (b.get("table_refs") or [])))
                a["figures_on_page"] = (a.get("figures_on_page") or []) + (b.get("figures_on_page") or [])
                a["tables_on_page"] = (a.get("tables_on_page") or []) + (b.get("tables_on_page") or [])
                a["evidence"] = (a.get("evidence") or []) + (b.get("evidence") or [])
                a["notes"] = T("合并页：依次讲清每张图/表的主张与证据。",
                               "Merged page: walk through each figure/table claim in order.")
                pages.remove(b)

    for i, p in enumerate(pages, start=1):
        p["page_no"] = i

    # evidence-map appendix (每页内容对应论文位置)
    ev_rows = []
    for p in pages[1:]:
        for e in p.get("evidence", []):
            if e.get("loc"):
                ev_rows.append({"page": p["page_no"], "page_type": p["page_type"],
                                "claim": e["claim"], "loc": e["loc"]})
    pages.append({
        "page_type": "evidence_map", "page_no": len(pages) + 1,
        "title": T("证据映射（页 → 论文位置）", "Evidence map (slide → source)"),
        "claims": [], "bullets": [],
        "figure_refs": [], "table_refs": [],
        "notes": T("本附录证明每页主张可追溯到原文位置，供评审/复跑核对。",
                   "Appendix proving every claim maps to a source location."),
        "evidence": [],
        "evidence_rows": ev_rows,
    })
    pages.append({
        "page_type": "thankyou", "page_no": len(pages) + 1,
        "title": T("谢谢 / 欢迎提问", "Thank you / Q&A"),
        "claims": [], "bullets": [],
        "figure_refs": [], "table_refs": [],
        "notes": T("重述核心结论与主要证据位置。", "Restate the key takeaway and evidence locations."),
        "evidence": [],
        "thank_meta": {"title": content.get("title", ""),
                       "affiliation": content.get("affiliation", "")},
    })
    # renumber after any trim
    for i, p in enumerate(pages, start=1):
        p["page_no"] = i

    # per-slide speaking-time estimate
    total_min = _est_min(content)
    per = max(1, round(total_min / max(len(pages), 1), 1))
    for p in pages:
        p["notes"] = f"[建议时长 {per} 分钟] " + p["notes"]

    plan_obj = {
        "case_id": content["case_id"],
        "language": lang,
        "target_slides": target,
        "planned_slides": len(pages),
        "duration_minutes": total_min,
        "pages": pages,
        "trim_applied": len(pages) < target or (target > 0 and len(pages) <= target),
        "note": (f"trimmed to target {target}" if len(pages) == target
                 else f"planned {len(pages)} (target {target})"),
    }
    return plan_obj


def _est_min(content) -> int:
    dur = content.get("duration_minutes") or 15
    try:
        return int(dur)
    except Exception:
        return 15


def main(argv=None):
    utf8_writer()
    import argparse
    ap = argparse.ArgumentParser(description="deckplan.py — build deterministic slide plan")
    ap.add_argument("--content", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    import json
    content = json.load(open(a.content, "r", encoding="utf-8-sig"))
    plan_obj = plan(content)
    os.makedirs(a.out, exist_ok=True)
    dump_json(os.path.join(a.out, "spec.json"), plan_obj)
    print(f"deckplan ok: planned_slides={plan_obj['planned_slides']} target={plan_obj['target_slides']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())