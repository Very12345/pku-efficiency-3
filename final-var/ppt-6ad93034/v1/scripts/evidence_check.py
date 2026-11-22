# -*- coding: utf-8 -*-
"""evidence_check.py — verify layer: 页级证据与数字核验（对齐高分包 evidence_check）。

职责（verify 轴）：
* `check_claim_numbers`：页面上每个数字必须能在材料原文中找到；找不到 →
  该主张 verified=false 并进 `unverified_claims`，不当作正确数据（不编造红线）。
* `build_evidence_footer`：每页证据脚注（图/表/章节/数据的紧凑一行），
  deck_tool 建稿与 result_tool 汇总都从这一个函数取，保证同源。
* `evidence_rows`：生成"逐页证据映射"行（机器可读），result_tool 据此写
  evidence_map.md（人读）与 evidence_map.json（机器读）双形态。
* `plan_lint`：CP2 计划结构的结构化校验（每页 role/title/claims 上限/证据）
  —— 把"文字自述的页面纪律"变成可执行检查。

不含任何页面文案生成（那是 slide_text.py）与材料读取（那是 deck_extract.py）。
"""
import re

from deck_common import LOG, cjk_weight


# ---------------------------------------------------------------------------
# Number verification
# ---------------------------------------------------------------------------

def find_numeric_tokens(text: str):
    """Distinct numeric tokens (with optional trailing %/倍/x/×) found in text."""
    tokens = set()
    for m in re.finditer(r"\d+(?:[.,]\d+)*\s*(?:%|％|倍|x|×)?", _norm(text)):
        tok = m.group(0).strip()
        if tok and any(ch.isdigit() for ch in tok):
            tokens.add(tok)
    return tokens


def _norm(s: str):
    import unicodedata
    return re.sub(r"[\s\u3000]+", "", unicodedata.normalize("NFKC", s or "")).lower()


def check_claim_numbers(claim: str, material_text: str):
    """Verify every numeric token of *claim* appears in *material_text*.

    Returns (ok, missing_tokens). Missing tokens mean the slide may carry a
    number that the source does not support -> must be reported as uncertainty
    (D2 / G4), never silently kept.
    """
    material = _norm(material_text)
    missing = []
    for tok in sorted(find_numeric_tokens(claim)):
        if tok not in material:
            missing.append(tok)
    return not missing, missing


def unverified_summary(pages_meta):
    """Collect claims marked unverified across pages (result.evidence input)."""
    out = []
    for p in pages_meta or []:
        for c in p.get("claims", []):
            if not c.get("verified", True):
                out.append({"page": p.get("index"), "text": c.get("text", ""),
                            "missing_numbers": c.get("missing_numbers", [])})
    return out


# ---------------------------------------------------------------------------
# Evidence footer (single source used by build + verify)
# ---------------------------------------------------------------------------

def build_evidence_footer(page) -> str:
    """One-line evidence footer for a page: 证据: 图/表/章节 + 图表: 图N.

    Works on planner.Page objects (build layer) or plan dicts (verify layer).
    """
    claims = getattr(page, "claims", None)
    if claims is None:
        claims = page.get("claims", [])
    evs = []
    for c in claims:
        ev = getattr(c, "evidence", None) if not isinstance(c, dict) else c.get("evidence", [])
        for e in ev or []:
            if e and e not in evs:
                evs.append(e)
    fig = getattr(page, "figure", None)
    if not isinstance(fig, dict):
        fig = getattr(page, "figure", None)
        fig = {"kind": getattr(fig, "kind", "none"), "ref": getattr(fig, "ref", "")} if fig is not None else {}
    tag = ""
    if fig and fig.get("kind") not in (None, "none") and fig.get("ref"):
        tag = fig.get("ref")
    parts = []
    if evs:
        parts.append("证据: " + "、".join(evs[:6]))
    if tag:
        parts.append("图表: " + tag)
    if not parts:
        parts.append("证据: 依据材料整理")
    return " | ".join(parts)


def page_evidence_list(page_dict) -> list:
    """Distinct evidence refs of a plan page dict (for the evidence map)."""
    evs = []
    for c in page_dict.get("claims", []):
        for e in c.get("evidence", []):
            if e and e not in evs:
                evs.append(e)
    return evs


def evidence_rows(pages_meta):
    """Per-page evidence rows shared by md + json dual form.

    Each row: {page, role, role_label, title, evidence[], figure_ref,
               figure_kind, status: mapped|gap}. A page with no evidence at all
    is an explicit "gap" row — 显式标注，不许假装有证据。
    """
    rows = []
    for p in pages_meta or []:
        evs = page_evidence_list(p)
        fig = p.get("figure", {})
        if evs:
            status = "mapped"
        else:
            status = "gap"
        rows.append({
            "page": p.get("index"),
            "role": p.get("role"),
            "role_label": p.get("role_label", p.get("role")),
            "title": p.get("title", ""),
            "evidence": evs,
            "figure_ref": fig.get("ref", ""),
            "figure_kind": fig.get("kind", "none"),
            "status": status,
        })
    return rows


# ---------------------------------------------------------------------------
# CP2 plan lint (structural rules of the page plan)
# ---------------------------------------------------------------------------

def plan_lint(pages_meta, spec):
    """Structured checks on the plan; returns {"valid", "problems", "counts"}.

    Rules (advisory for the agent, hard for the deck): every page has
    role/title; claims <= limits.max_bullets_per_page; bullet/title length is
    bounded both in plain chars (deck truncates at max_chars_per_bullet via
    _char_safe) and in CJK-weighted chars (weighted > 2× limit means extreme
    CJK density the auto font-shrink cannot rescue); page count within
    spec.max_slides (3-20); unknown roles rejected.
    A plan that fails lint must not be built silently — build may continue
    only when problems are recorded (D4 / CP2 gate note).
    """
    from slide_text import ROLE_LABELS
    problems = []
    limits = (spec or {}).get("limits", {})
    max_bullets = int(limits.get("max_bullets_per_page", 7) or 7)
    max_bullet_chars = int(limits.get("max_chars_per_bullet", 90) or 90)
    title_max = int(limits.get("title_max_chars", 60) or 60)
    max_slides = int((spec or {}).get("max_slides", 8) or 8)

    pages = pages_meta or []
    counts = {"pages": len(pages), "gaps": 0, "unverified": 0}
    if not pages:
        problems.append("plan has no pages")
        return {"valid": False, "problems": problems, "counts": counts}

    if not (3 <= max_slides <= 20):
        problems.append("spec.max_slides=%s outside 3..20" % max_slides)
    if len(pages) > max_slides:
        problems.append("plan pages=%d exceed spec.max_slides=%d" % (len(pages), max_slides))

    for p in pages:
        idx = p.get("index")
        if not p.get("role"):
            problems.append("page %s missing role" % idx)
        elif p.get("role") not in ROLE_LABELS:
            problems.append("page %s unknown role %r" % (idx, p.get("role")))
        title = p.get("title", "") or ""
        if not title.strip():
            problems.append("page %s empty title" % idx)
        elif len(title) > title_max or cjk_weight(title) > title_max * 2:
            problems.append("page %s title too long (chars=%d, CJK-weighted=%d vs limit=%d)"
                            % (idx, len(title), cjk_weight(title), title_max))
        claims = p.get("claims", [])
        if len(claims) > max_bullets:
            problems.append("page %s claims=%d > %d" % (idx, len(claims), max_bullets))
        for c in claims:
            ctext = c.get("text", "") or ""
            if len(ctext) > max_bullet_chars or cjk_weight(ctext) > max_bullet_chars * 2:
                problems.append("page %s bullet too long (chars=%d, CJK-weighted=%d vs limit=%d)"
                                % (idx, len(ctext), cjk_weight(ctext), max_bullet_chars))
                break
            if not c.get("verified", True):
                counts["unverified"] += 1
        if not page_evidence_list(p):
            counts["gaps"] += 1
    return {"valid": not problems, "problems": problems, "counts": counts}


def main(argv=None):
    """Standalone: verify a claim against a material text file.

    python scripts/evidence_check.py --claim "82.4%" --material material.md
    exit 0 = all claim numbers found; 1 = missing.
    """
    import argparse
    import sys
    ap = argparse.ArgumentParser(description="evidence number check")
    ap.add_argument("--claim", required=True, help="claim text to verify")
    ap.add_argument("--material", required=True, help="material text file")
    args = ap.parse_args(argv)
    with open(args.material, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    ok, missing = check_claim_numbers(args.claim, text)
    print("ok=%s missing=%s" % (ok, missing))
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())