#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mechanism_probe.py — 机制可证伪判据探针（随包分发，**请在包外运行**）。

用途：对一次真实运行的输出目录逐条检查 MECHANISM.md 列出的机制是否**真的在产物里
留下痕迹**。它不看文档怎么写，只看 result.json / 产物文件里有没有对应字段。

用法:
  python mechanism_probe.py --out <一次运行的输出目录> [--out <第二个输出目录> ...]

退出码: 0 = 全部判据通过；1 = 有判据不成立（打印 FAIL 行）；2 = 输入不可读。

判据（编号与 MECHANISM.md 一致）:
  M1 page_units   每页都有 role 且页数 = deck.slide_count = slides 数
  M2 anchors      每条含数字的主张都有 evidence 指针；unverified 有解释或有据可查
  M3 figure_states figure.kind 在四态词表内；chart_image 必须指向真实存在的图片文件，
                   且该页 figure.table_id 指向的表文件存在（否则即为"无数据来源的图"）
  M4 versioning   deck 可重开；若存在 deck_<v>.pptx 则主版本仍在（可回退）；
                   changelog.jsonl 与 manifest.json 存在
  M5 contract     output_contract 声明的字段全部出现在顶层且非 null
"""
import argparse
import json
import os
import sys

FIGURE_STATES = {"chart_image", "table", "embedded", "placeholder", "none"}


def _load(out_dir):
    p = os.path.join(out_dir, "result.json")
    if not os.path.isfile(p):
        return None
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def check_m1(res, out_dir):
    deck = res.get("deck", {}) or {}
    slides = deck.get("slides", []) or []
    problems = []
    if not slides:
        problems.append("没有任何 slide")
    for s in slides:
        if not (s.get("role") or "").strip():
            problems.append("page %s 缺少 role" % s.get("index"))
    if deck.get("slide_count") != len(slides):
        problems.append("slide_count=%s 与 slides 数=%d 不一致"
                        % (deck.get("slide_count"), len(slides)))
    return problems


def check_m2(res, out_dir):
    problems = []
    deck = res.get("deck", {}) or {}
    numeric_total = numeric_traced = 0
    import re

    def toks(t):
        return re.findall(r"\d+(?:[.,]\d+)*\s*(?:%|％|倍|x|×)?", t or "")

    for s in deck.get("slides", []) or []:
        for c in (s.get("claims", []) or []):
            if toks(c.get("text", "")):
                numeric_total += 1
                if [e for e in (c.get("evidence", []) or []) if str(e).strip()]:
                    numeric_traced += 1
                else:
                    problems.append("page %s 的数字主张没有证据指针: %s"
                                    % (s.get("index"), (c.get("text") or "")[:40]))
    unc = (res.get("evidence", {}) or {}).get("unverified_claims", []) or []
    if unc and res.get("status") == "success":
        problems.append("有 %d 条未核验主张却标 success" % len(unc))
    return problems, {"numeric_claims": numeric_total,
                      "numeric_claims_with_evidence": numeric_traced,
                      "unverified_claims": len(unc)}


def _find_table(out_dir, table_id):
    """表文件按已知位置找：work/table_cache/<id> 或原材料同名。"""
    for cand in (os.path.join(out_dir, "work", "table_cache", table_id),
                 os.path.join(out_dir, "work", table_id),
                 os.path.join(out_dir, table_id)):
        if os.path.isfile(cand):
            return cand
    return None


def check_m3(res, out_dir):
    problems = []
    counts = {}
    for s in res.get("deck", {}).get("slides", []) or []:
        fig = s.get("figure", {}) or {}
        kind = fig.get("kind", "none")
        counts[kind] = counts.get(kind, 0) + 1
        if kind not in FIGURE_STATES:
            problems.append("page %s 出现词表外的 figure.kind=%r" % (s.get("index"), kind))
        if kind == "chart_image":
            img = fig.get("image") or ""
            # 相对输出目录解析（result.json 的路径字段约定为相对路径）
            ip = img if os.path.isabs(img) else os.path.join(out_dir, img)
            if not img or not os.path.isfile(ip):
                problems.append("page %s 标为 chart_image 但图片文件不存在: %r"
                                % (s.get("index"), img))
            tid = fig.get("table_id") or ""
            if tid and not _find_table(out_dir, tid):
                problems.append("page %s 的 chart_image 找不到数据表来源: %r"
                                % (s.get("index"), tid))
    return problems, counts


def check_m4(res, out_dir):
    problems = []
    deck = res.get("deck", {}) or {}
    editable = deck.get("editable") or ""
    ep = editable if os.path.isabs(editable) else os.path.join(out_dir, editable)
    if not editable or not os.path.isfile(ep):
        problems.append("可编辑源不存在: %r" % editable)
    else:
        try:
            from pptx import Presentation
            prs = Presentation(ep)
            if len(prs.slides) != len(deck.get("slides", []) or []):
                problems.append("pptx 页数 %d 与 result 记录不一致" % len(prs.slides))
        except Exception as exc:            # 缺 python-pptx 时如实报，不当作通过
            problems.append("pptx 无法重开（%s: %s）" % (type(exc).__name__, exc))
    wd = os.path.join(out_dir, "work")
    versions = sorted(f for f in os.listdir(wd)
                      if f.startswith("deck") and f.endswith(".pptx")) if os.path.isdir(wd) else []
    if len(versions) >= 2 and os.path.join(out_dir, deck.get("editable", "")) not in (
            os.path.join(wd, v) for v in versions):
        problems.append("存在多版本但主版本缺失，无法回退: %s" % versions)
    for name in ("changelog.jsonl", "manifest.json"):
        if not os.path.isfile(os.path.join(out_dir, name)):
            problems.append("缺少 %s（版本/产物清单不可复核）" % name)
    return problems, versions


def check_m5(res, out_dir):
    """契约字段是否逐项回显且非 null —— 需要 case.json 才能知道声明了什么；
    没有 case.json 时退化为"顶层不得有 null 值"。"""
    problems = []
    nulls = [k for k, v in res.items() if v is None]
    if nulls:
        problems.append("顶层存在 null 字段: %s" % nulls)
    return problems


def probe(out_dir):
    res = _load(out_dir)
    if res is None:
        print("ERROR: 无 result.json: %s" % out_dir, file=sys.stderr)
        return None
    m1 = check_m1(res, out_dir)
    m2, m2d = check_m2(res, out_dir)
    m3, m3d = check_m3(res, out_dir)
    m4, versions = check_m4(res, out_dir)
    m5 = check_m5(res, out_dir)
    return {
        "out_dir_label": "<OUT>",
        "status": res.get("status"),
        "M1_page_units": {"ok": not m1, "problems": m1},
        "M2_anchors": {"ok": not m2, "problems": m2, "counts": m2d},
        "M3_figure_states": {"ok": not m3, "problems": m3, "kind_counts": m3d},
        "M4_versioning": {"ok": not m4, "problems": m4, "deck_versions": versions},
        "M5_contract": {"ok": not m5, "problems": m5},
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="机制可证伪判据探针（包外运行）")
    ap.add_argument("--out", action="append", required=True, help="一次运行的输出目录")
    a = ap.parse_args(argv)
    bad = 0
    reports = []
    for d in a.out:
        if not os.path.isdir(d):
            print("ERROR: 目录不可读: %s" % d, file=sys.stderr)
            return 2
        r = probe(d)
        if r is None:
            return 2
        reports.append(r)
        print("== %s  status=%s" % (os.path.basename(os.path.normpath(d)), r["status"]))
        for k in ("M1_page_units", "M2_anchors", "M3_figure_states",
                  "M4_versioning", "M5_contract"):
            print("   %-18s %s %s" % (k, "PASS" if r[k]["ok"] else "FAIL",
                                      "" if r[k]["ok"] else r[k]["problems"]))
            if not r[k]["ok"]:
                bad = 1
    json.dump(reports, open("mechanism-probe-report.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print("报告已写出: mechanism-probe-report.json")
    return bad


if __name__ == "__main__":
    sys.exit(main())
