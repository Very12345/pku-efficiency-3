# -*- coding: utf-8 -*-
"""Page planning: turn the extracted Material into a page-level narrative plan.

Each page carries a narrative *role* (封面/主线/背景/问题/方法/结果/讨论/局限/收束),
claim bullets with evidence pointers, optional figure/table bindings and the
speaker-note skeleton. The plan is saved as JSON and is the *editable source*
the local edit commands mutate (see main.py --edit).

Rules kept deterministic on purpose:
  * page count is clamped by spec.max_slides (never silently over),
  * claims are built only from material text / tables,
  * numbers are not rounded or invented here; unverifiable claims are reported
    in `uncertainty` instead of being fabricated.
"""
import os
import re
from dataclasses import dataclass, field, asdict

from common import LOG, now_iso, atomic_write_json, check_claim_numbers
from material import Material

# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------
ROLE_LABELS = {
    "cover": "封面",
    "overview": "主线与贡献",
    "background": "背景与动机",
    "question": "研究问题",
    "method": "方法",
    "result": "结果",
    "discussion": "讨论",
    "limitation": "局限",
    "takeaway": "结论与展望",
}

AUDIENCE_TONES = {
    "组会": "面向实验室内部：突出方法与下一步计划，术语可深入，进度感要强。",
    "答辩": "面向评审：突出创新点、贡献界定与结论稳健性，主动交代局限与理由。",
    "评审": "面向项目/基金评审：对齐目标与指标，强调可行性、验证与影响。",
    "同行": "面向同行研究者：对比现有方法、数据与指标，给出可复现细节。",
    "基金": "面向基金评审：先讲意义与需求缺口，再讲方案与团队能完成的能力证据。",
    "默认": "条理清晰、证据可追溯、每页一个主张。",
}
DEFAULT_AUDIENCE = "默认"


@dataclass
class Claim:
    text: str
    evidence: list = field(default_factory=list)   # e.g. ["§方法", "表1"]
    level: int = 0
    verified: bool = True
    missing_numbers: list = field(default_factory=list)


@dataclass
class FigureSlot:
    ref: str = ""                 # 图N / 表N as mentioned in material
    kind: str = "none"            # chart_image | table | embedded | placeholder | none
    table_id: str = ""
    image: str = ""               # local asset path if embedded / chart_image
    note: str = ""


@dataclass
class Page:
    index: int
    role: str
    title: str
    claims: list = field(default_factory=list)
    figure: FigureSlot = field(default_factory=FigureSlot)
    notes: list = field(default_factory=list)
    agenda_item: str = ""


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def _sentence_split(text, max_items=5):
    parts = re.split(r"(?<=[。！？；.!?;])\s*", (text or "").strip())
    out = []
    for p in parts:
        p = p.strip()
        if len(p) >= 12:
            out.append(p)
        if len(out) >= max_items:
            break
    return out


def _first_sentence(text, max_chars=110):
    parts = re.split(r"(?<=[。！？.!?])\s*", (text or "").strip())
    s = (parts[0] if parts else (text or "")).strip()
    return s[:max_chars]


def _shorten(t, n=95):
    t = re.sub(r"\s+", " ", (t or "")).strip()
    return t if len(t) <= n else t[: n - 1].rstrip() + "…"


def _claim(body, evidence, material_text):
    text = _shorten(body)
    ok, missing = check_claim_numbers(text, material_text)
    return Claim(text=text, evidence=evidence or [],
                 verified=ok, missing_numbers=missing)


def _claim_unverified(body, evidence):
    return Claim(text=_shorten(body), evidence=evidence or [], verified=False)


# ---------------------------------------------------------------------------
# Allocation
# ---------------------------------------------------------------------------

def alloc_roles(m):
    """Page roles at *page count* granularity (deterministic, documented)."""
    m = max(3, min(int(m), 20))
    if m <= 4:
        extra = {3: ["result"], 4: ["method", "result"]}
        return (["cover", "overview"] + extra[m])[:m]
    base = ["cover", "overview", "question", "method", "result", "takeaway"]
    extras = ["background", "discussion", "limitation"]
    extra_n = max(0, m - len(base))
    roles = base[:2] + extras[:extra_n] + base[2:]
    # more slides -> more result pages before the takeaway
    extra2 = m - len(roles)
    if extra2 > 0:
        roles = roles[:-1] + ["result"] * extra2 + ["takeaway"]
    return roles[:m]


# ---------------------------------------------------------------------------
# Content builders per role
# ---------------------------------------------------------------------------

def _page_cover(mat, spec):
    return Page(index=1, role="cover",
                title=_shorten(mat.title or spec.get("title") or "研究汇报", 60) or "研究汇报",
                claims=[],
                notes=["开场白要点：一句话交代题目、动机和本次要讲清的问题。"])


def _page_overview(mat, spec):
    rq = mat.find_first_text("研究问题", "研究目标", "问题", "objective",
                             "research question", "本文提出",
                             fallback=mat.find_first_text("摘要", "abstract", fallback=""))
    tone = AUDIENCE_TONES.get(spec.get("audience", DEFAULT_AUDIENCE), AUDIENCE_TONES[DEFAULT_AUDIENCE])
    claims = []
    if rq:
        claims.append(_claim(_first_sentence(rq), ["摘要/引言"], mat.text))
    main_line = mat.find_first_text("摘要", "abstract", "结论", "conclusion", fallback="")
    if main_line:
        claims.append(_claim(_first_sentence(main_line), ["摘要/结论"], mat.text))
    return Page(index=2, role="overview", title="汇报主线", claims=claims,
                agenda_item="背景 · 问题 · 方法 · 结果 · 局限与展望",
                notes=[tone,
                       "受众=%s，时长=%s 分钟，共 %s 页（按 spec.max_slides 压缩）"
                       % (spec.get("audience", DEFAULT_AUDIENCE),
                          spec.get("duration_minutes", 15), spec.get("max_slides", 8))])


def _page_background(mat):
    s = mat.find_first_text("背景", "引言", "introduction", "motivation",
                            "相关工作", "related work", fallback="")
    claims = []
    head = "§背景" if s else "§引言"
    for sent in _sentence_split(s)[:3]:
        claims.append(_claim(sent, [head], mat.text))
    if not claims:
        claims.append(_claim_unverified("材料未提供明确的背景段落；请在讲稿中基于材料事实补充，不臆造引用。", ["材料缺失"]))
    return Page(index=3, role="background", title="背景与动机", claims=claims,
                notes=["说明为什么这个问题重要；不要复述论文摘要原文，用一两句人话。"])


def _page_question(mat):
    rq = mat.find_first_text("引言", "introduction", "研究问题", "研究目标",
                             "研究内容", fallback="")
    claims = []
    if rq:
        for sent in _sentence_split(rq)[:2]:
            claims.append(_claim(sent, ["引言"], mat.text))
    if not claims:
        claims.append(_claim_unverified("材料未明确写出研究问题；请根据标题与摘要归纳，并标注为推断。", ["材料缺失（推断）"]))
    return Page(index=4, role="question", title="研究问题", claims=claims,
                notes=["一页只放一个核心问题；回答“为什么值得做”。"])


def _page_method(mat):
    s = mat.find_first_text("方法", "模型", "方案", "method", "approach",
                            "实验设置", "设置", fallback="")
    claims = []
    for sent in _sentence_split(s, max_items=5)[:4]:
        claims.append(_claim(sent, ["§方法"], mat.text))
    if not claims:
        claims.append(_claim_unverified("材料未提供方法细节；请按论文结构补讲稿并标注来源。", ["材料缺失"]))
    return Page(index=5, role="method", title="方法", claims=claims,
                notes=["方法压到 4 条以内：核心思路 > 关键步骤 > 与基线的差异。"])


def _table_index(t):
    """Evidence label for a table: prefer numeric ref, else file basename."""
    if t.id.isdigit():
        return "表" + t.id
    base = os.path.splitext(os.path.basename(t.id))[0]
    return "表(" + base + ")"


def _result_pages(mat, n):
    """Build n result pages; prefer table-driven claims when tables exist."""
    pages = []
    table_rank = sorted(mat.tables, key=lambda t: t.id)  # deterministic order
    for i in range(n):
        t = table_rank[i] if i < len(table_rank) else None
        ev = _table_index(t) if t else "§结果"
        if t and t.rows:
            claims = []
            shown = 0
            for row in t.rows[:4]:
                for col in t.columns[1:]:
                    val = (row.get(col) or "").strip()
                    if re.fullmatch(r"-?\d+(?:[.,]\d+)?\s*[%％]?", val):
                        claims.append(_claim("%s 为 %s（%s）" % (_shorten(t.caption, 40), val, col),
                                             [ev, "列=%s" % col], mat.text))
                        shown += 1
                        break
                if shown >= 2:
                    break
            if not claims:
                claims.append(_claim("数据表 %s 共 %d 行，见讲稿逐行说明。" % (ev, len(t.rows)),
                                     [ev], mat.text))
            claims.append(Claim(text="表中数值直接取自源数据，未取整、未编造。",
                                evidence=[ev], verified=True))
            pages.append(Page(index=0, role="result",
                              title="结果%s" % ("：" + _shorten(t.caption, 20) if t.caption and t.caption != t.id else ""),
                              claims=claims,
                              figure=FigureSlot(ref=ev, kind="table", table_id=t.id, note="绑定数据表" + ev),
                              notes=["讲出“这个数字说明什么”，而不是念表。"]))
        else:
            s = mat.find_first_text("结果", "实验", "分析", "result", "evaluation",
                                    "performance", "effect", fallback="")
            claims = []
            for sent in _sentence_split(s, max_items=6)[:4]:
                claims.append(_claim(sent, ["§结果"], mat.text))
            if not claims:
                claims.append(_claim_unverified("材料未提供量化结果；如需要数字请在讲稿中明确说明依据。", ["材料缺失"]))
            pages.append(Page(index=0, role="result", title="实验结果", claims=claims,
                              notes=["结果页承载最多信息量，一页 3–5 条，量化主张必须写证据脚注。"]))
    return pages


def _page_discussion(mat):
    s = mat.find_first_text("讨论", "discussion", "启示", "意义", "分析", fallback="")
    claims = []
    for sent in _sentence_split(s)[:3]:
        claims.append(_claim(sent, ["§讨论"], mat.text))
    if not claims:
        claims.append(_claim_unverified("材料未提供讨论章节；可在讲稿中按事实对比基线并说明差异。", ["材料缺失"]))
    return Page(index=0, role="discussion", title="讨论", claims=claims,
                notes=["讨论 = 解释结果为什么是这样，而不是重复结果。"])


def _page_limitation(mat):
    s = mat.find_first_text("局限", "不足", "限制", "limitation", "future work", "展望", fallback="")
    claims = []
    for sent in _sentence_split(s)[:3]:
        claims.append(_claim(sent, ["§局限/展望"], mat.text))
    if not claims:
        claims.append(_claim_unverified("材料未明确列出局限；请按材料事实在讲稿中说明，未验证的不写。", ["材料缺失"]))
    return Page(index=0, role="limitation", title="局限与展望", claims=claims,
                notes=["诚实交代局限是加分项：适用的边界、未验证的场景、后续方向。"])


def _page_takeaway(mat):
    s = mat.find_first_text("结论", "总结", "conclusion", "总结与展望", fallback="")
    claims = []
    if s:
        for sent in _sentence_split(s)[:3]:
            claims.append(_claim(sent, ["§结论"], mat.text))
    if not claims:
        claims.append(Claim(text="研究主线：问题 → 方法 → 结果 → 局限。", evidence=["结构约定"], verified=True))
    return Page(index=0, role="takeaway", title="结论与下一步", claims=claims,
                notes=["最后一页给听众一个“带走”的句子。",
                       "下一步/开放问题请主讲人根据材料补充，并在备注中标注来源（本行是讲稿约定，不是材料结论）。"])


# ---------------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------------

def build_plan(mat: Material, spec: dict):
    m = max(3, min(int(spec.get("max_slides", 8) or 8), 20))
    roles = alloc_roles(m)
    pages = []
    results_done = False
    for role in roles:
        if role == "result":
            if not results_done:
                pages.extend(_result_pages(mat, roles.count("result")))
                results_done = True
            continue
        if role == "cover":
            p = _page_cover(mat, spec)
        elif role == "overview":
            p = _page_overview(mat, spec)
        elif role == "background":
            p = _page_background(mat)
        elif role == "question":
            p = _page_question(mat)
        elif role == "method":
            p = _page_method(mat)
        elif role == "discussion":
            p = _page_discussion(mat)
        elif role == "limitation":
            p = _page_limitation(mat)
        else:
            p = _page_takeaway(mat)
        pages.append(p)
    for i, p in enumerate(pages, start=1):
        p.index = i
    return pages


def bind_figures(pages, mat, work_dir, chart_builder=None):
    """Resolve figure slots: regenerate charts from bound tables when possible.

    chart_builder(table, work_dir) -> (kind, image_path_or_None, note).
    Returns (pages, chart_log) where chart_log records what was done per page.
    """
    log = []
    for p in pages:
        f = p.figure
        if p.role != "result" or f.kind != "table" or not f.table_id:
            continue
        t = next((x for x in mat.tables if x.id == f.table_id), None)
        if t is None or not t.rows:
            f.kind = "placeholder"
            f.note = "绑定数据表缺失/为空，未重绘（诚实占位）"
            log.append({"page": p.index, "kind": "placeholder", "reason": "数据表缺失"})
            continue
        if chart_builder is not None:
            try:
                img, note = chart_builder(t, work_dir)
                f.kind = "chart_image"
                f.image = img
                f.note = note or "由源数据表用 matplotlib 重绘（可编辑数据在 assets/%s 图表脚本可复现）" % t.id
                log.append({"page": p.index, "kind": "chart_image", "source": t.id})
            except Exception as e:  # noqa: BLE001
                LOG.warning("chart failed for %s: %s", t.id, e)
                f.kind = "table"  # fall back to a native editable pptx table
                f.note = "图表重绘失败，已降级为原生可编辑表格：" + str(e)
                f.image = ""
                log.append({"page": p.index, "kind": "table", "reason": str(e)})
        else:
            f.kind = "table"
            log.append({"page": p.index, "kind": "table", "reason": "未启用图表重绘"})
    return pages, log


def plan_to_dict(pages):
    return [{"index": p.index, "role": p.role,
             "role_label": ROLE_LABELS.get(p.role, p.role), "title": p.title,
             "claims": [{"text": c.text, "evidence": c.evidence, "level": c.level,
                         "verified": c.verified,
                         "missing_numbers": c.missing_numbers} for c in p.claims],
             "figure": asdict(p.figure), "notes": p.notes,
             "agenda_item": p.agenda_item} for p in pages]


def dump_plan(pages, plan_path):
    atomic_write_json(plan_path, {"generated_at": now_iso(),
                                  "pages": plan_to_dict(pages)})
    return plan_path