#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_status_matrix.py — machine check that result.json's `status` agrees with
the machine-visible evidence inside the same file.  (verify role; the missing
counterpart of validate_result/check_contract for the *state consistency*
branch of the failure table.)

Why this script exists
----------------------
`status` is the only field the reviewer reads before deciding whether to trust
the rest of the envelope.  A run can therefore look honest in prose while the
file itself contradicts it: e.g. `status="completed"` together with
`artifacts.deck_limitation` set, a plan gate that failed, an unparsed text
material, or a page count that no longer equals the frozen `slide_count`.
Those contradictions are machine-detectable — this script detects them and
returns a non-zero exit code instead of leaving the check to a human reader.

The rule set below is the executable form of
`references/decision-rules.md` §4 (status decision matrix) and of the
"状态一致性规则" section of `references/failure-modes.md`: every rule prints the
contract field(s) it looked at, so a disagreement can be settled by opening
result.json rather than by re-reading the manual.

Usage
-----
    python check_status_matrix.py <out_dir | result.json> [--json <report.json>]
    python check_status_matrix.py <out_dir> --quiet

Exit codes
----------
    0 = every applicable rule holds (the file is self-consistent)
    1 = at least one rule is violated (the report lists rule id + evidence)
    2 = usage error / result.json unreadable

Companion checks: `validate_result.py` (structure, files on disk, numbers),
`check_contract.py` (declared fields present and typed) — this script answers
the third question: "does `status` match what the file itself shows?"
"""

import json
import os
import sys

# Windows consoles default to GBK; force UTF-8 output (written files unaffected)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001  (stdout may be a wrapper without reconfigure)
    pass

IMAGE_KINDS = {"png", "jpg", "jpeg", "gif", "bmp", "tif", "tiff", "webp",
               "image", "figure"}
# structural pages that legitimately carry no source locator; "title" is the
# cover block id emitted by scaffold_plan.py, "qa" is the backup question page
NON_EVIDENCE_BLOCKS = {"title", "cover", "agenda", "toc", "qa", "backup", "thanks"}
# limitations that cannot coexist with status=completed
CONTRADICTS_COMPLETED = ("未生成", "没有生成", "降级", "无法生成", "status=partial",
                         "status=failed", "缺失", "not generated", "degraded")


def _load(args):
    """Return (result_dict, out_dir_or_None)."""
    target = args[0]
    if os.path.isdir(target):
        path = os.path.join(target, "result.json")
        out_dir = target
    else:
        path = target
        out_dir = os.path.dirname(os.path.abspath(target))
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh), out_dir


def _texts(entries, key):
    out = []
    for e in entries or []:
        v = e.get(key)
        if isinstance(v, str) and v.strip():
            out.append(v)
    return out


def check(result):
    """Return the list of rule rows: {rule, scope, ok, detail}."""
    rows = []

    def add(rule, scope, ok, detail):
        rows.append({"rule": rule, "scope": scope, "ok": bool(ok),
                     "detail": detail})

    status = result.get("status")
    pages = result.get("pages") or []
    audit = result.get("audit") or {}
    plan_gates = audit.get("plan_gates") or {}
    ev_audit = audit.get("evidence") or {}
    deck_audit = audit.get("deck") or {}
    artifacts = result.get("artifacts") or {}
    sources = result.get("sources") or []
    uncertainty = result.get("uncertainty") or []
    frozen = result.get("slide_count")
    deck_limitation = artifacts.get("deck_limitation")

    text_sources = [s for s in sources
                    if (s.get("kind") or "").lower() not in IMAGE_KINDS
                    and s.get("file") not in (None, "(none)")]
    unparsed_text = [s.get("file") for s in text_sources if not s.get("parsed")]
    parsed_any = [s for s in text_sources if s.get("parsed")]
    previews = artifacts.get("previews") or {}

    # ---------- rules that must hold for every status ----------
    add("C1", "case_id 非空",
        isinstance(result.get("case_id"), str) and result["case_id"].strip() != "",
        "case_id=%r" % (result.get("case_id"),))

    if status == "failed":
        add("C2", "pages 允许为空（failed）", True, "status=failed：只要求失败信封")
    else:
        add("C2", "pages 非空", len(pages) > 0, "len(pages)=%d" % len(pages))

    same = (not isinstance(frozen, int)) or len(pages) == frozen
    add("C3", "len(pages) == slide_count（冻结页数一致）", same,
        "len(pages)=%s slide_count=%s" % (len(pages), frozen))

    missing_ev = []
    for p in pages:
        if (p.get("block") or "") in NON_EVIDENCE_BLOCKS:
            continue
        ev = (p.get("evidence") or [{}])[0]
        if not (ev.get("locator") or "").strip() or not (ev.get("quote") or "").strip():
            missing_ev.append(p.get("page_no"))
    add("C4", "内容页有 locator + quote", not missing_ev,
        "缺定位的页=%s" % (missing_ev or "无"))

    known = {s.get("file") for s in sources}
    orphan = sorted({e.get("source_file") for p in pages
                     for e in (p.get("evidence") or [])
                     if e.get("source_file") and e["source_file"] not in known})
    add("C5", "evidence.source_file 均在 sources[] 中", not orphan,
        "孤儿引用=%s" % (orphan or "无"))

    bad_unc = [i for i, u in enumerate(uncertainty)
               if not all((u.get(k) or "").strip() for k in ("item", "impact", "mitigation"))]
    add("C6", "uncertainty 每条含 item/impact/mitigation", not bad_unc,
        "不合格条目下标=%s" % (bad_unc or "无"))

    # ---------- status-specific rules ----------
    if status == "completed":
        deck_slides = deck_audit.get("slide_count")
        if deck_slides is None and isinstance(deck_audit.get("slides"), list):
            deck_slides = len(deck_audit["slides"])
        deck_ok = (bool(artifacts.get("editable_deck"))
                   and deck_audit.get("valid") is True
                   and deck_slides in (None, len(pages)))
        add("S1", "completed ⇒ deck 存在且 deck_audit.valid", deck_ok,
            "editable_deck=%r deck_audit.valid=%r deck_slides=%r pages=%d"
            % (artifacts.get("editable_deck"), deck_audit.get("valid"),
               deck_slides, len(pages)))
        add("S2", "completed ⇒ plan_gates.valid", plan_gates.get("valid") is True,
            "plan_gates.valid=%r errors=%s"
            % (plan_gates.get("valid"), plan_gates.get("errors")))
        add("S3", "completed ⇒ evidence_audit.valid", ev_audit.get("valid") is True,
            "evidence.valid=%r summary=%s"
            % (ev_audit.get("valid"), ev_audit.get("summary")))
        add("S4", "completed ⇒ 全部文本材料已解析", not unparsed_text,
            "未解析文本材料=%s" % (unparsed_text or "无"))
        add("S5", "completed ⇒ 预览 cover+manifest 存在",
            bool(previews.get("cover")) and bool(previews.get("manifest")),
            "previews.cover=%r manifest=%r"
            % (previews.get("cover"), previews.get("manifest")))
        add("S6", "completed ⇒ 无 deck_limitation", not deck_limitation,
            "deck_limitation=%r" % (deck_limitation,))
        hits = [(i, u.get("item", "")) for i, u in enumerate(uncertainty)
                if any(m in (u.get("item") or "") for m in CONTRADICTS_COMPLETED)]
        add("S7", "completed ⇒ uncertainty 无降级条目", not hits,
            "矛盾条目=%s" % (hits or "无"))

    elif status == "partial":
        defect = []
        if deck_limitation:
            defect.append("deck_limitation")
        if plan_gates.get("valid") is False:
            defect.append("plan_gates.invalid")
        if ev_audit.get("valid") is False:
            defect.append("evidence_audit.invalid")
        if deck_audit and deck_audit.get("valid") is False:
            defect.append("deck_audit.invalid")
        if not artifacts.get("editable_deck"):
            defect.append("editable_deck=null")
        if unparsed_text:
            defect.append("unparsed_text_material")
        if not (previews.get("cover") and previews.get("manifest")):
            defect.append("previews_missing")
        if not parsed_any:
            defect.append("no_parsed_material")
        add("P1", "partial ⇒ 至少一处机器可见缺陷", bool(defect),
            "缺陷信号=%s" % (defect or "无（可能是把成功写成 partial，或状态未随降级更新）"))
        add("P2", "partial ⇒ uncertainty 记录了缺陷", len(uncertainty) > 0,
            "uncertainty 条数=%d" % len(uncertainty))

    elif status == "failed":
        err = result.get("error")
        deck_failed = any((c.get("step") == "deck" and "FAILED" in (c.get("action") or ""))
                          for c in result.get("change_records") or [])
        add("F1", "failed ⇒ 有 error 字段或 deck 失败记录", bool(err) or deck_failed,
            "error=%r deck_failed_record=%s" % (err, deck_failed))

    else:
        add("X1", "status ∈ {completed, partial, failed}", False,
            "status=%r 不在枚举内" % (status,))

    return rows


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    quiet = "--quiet" in argv
    json_out = None
    if "--json" in argv:
        i = argv.index("--json")
        if i + 1 >= len(argv):
            print("--json needs a path")
            return 2
        json_out = argv[i + 1]
        args = [a for a in args if a != json_out]
    if len(args) != 1:
        print(__doc__)
        return 2
    try:
        result, out_dir = _load(args)
    except Exception as exc:  # noqa: BLE001
        print("FATAL: cannot read result.json: %s" % exc)
        return 2

    rows = check(result)
    bad = [r for r in rows if not r["ok"]]
    report = {"valid": not bad, "status": result.get("status"),
              "checked": len(rows), "violations": len(bad), "rows": rows,
              "source": os.path.abspath(args[0])}
    if json_out:
        with open(json_out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2)
    if not quiet:
        print("status-matrix check of %s (status=%s)" % (args[0], result.get("status")))
        for r in rows:
            print("  [%s] %-8s %-38s %s" % ("ok" if r["ok"] else "XX", r["rule"],
                                            r["scope"], r["detail"]))
        print("=> %s (%d rules checked, %d violations)"
              % ("CONSISTENT" if not bad else "INCONSISTENT", len(rows), len(bad)))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
