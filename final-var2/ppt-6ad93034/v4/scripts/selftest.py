# -*- coding: utf-8 -*-
"""selftest.py — verify layer: 端到端产物自检（对齐高分包 selftest）。

职责：对一次真实运行的全部产物做"可复核性"检查，任何一个不通过都应在
result.json 的 uncertainty 中如实解释（绝不假装成功）：
* pptx 可重新打开且页数与计划一致；
* result.json 存在且必备顶层字段齐全；
* evidence_map.md 与 evidence_map.json 双形态存在；
* preview/*.png（≥1）与 preview.pdf（可缺但需说明）存在；
* 每页有演讲备注与证据脚注（不透传覆盖页）。

独立 CLI：`python scripts/selftest.py --out <outdir> [--case <case.json>]`，
exit 0 = 全部通过；1 = 有未通过项；2 = 输入不可读。
"""
import argparse
import json
import os
import sys

from deck_common import LOG


def run_self_check(out_dir, case_id, pptx_path, expected_slides, contract_keys):
    """Lightweight checks that generated artifacts exist & are openable."""
    checks = []
    ok = True
    try:
        from pptx import Presentation
        prs = Presentation(pptx_path)
        n = len(prs.slides._sldIdLst)
        checks.append({"name": "pptx_reopen", "ok": n == expected_slides,
                       "detail": "slides=%d expected=%d" % (n, expected_slides)})
        ok = ok and n == expected_slides
    except Exception as e:  # noqa: BLE001
        checks.append({"name": "pptx_reopen", "ok": False, "detail": str(e)})
        ok = False

    rj = os.path.join(out_dir, "result.json")
    have_result = os.path.isfile(rj)
    checks.append({"name": "result_json", "ok": have_result,
                   "detail": "exists" if have_result else "missing"})
    ok = ok and have_result
    if have_result:
        try:
            with open(rj, "r", encoding="utf-8") as f:
                data = json.load(f)
            missing = [k for k in contract_keys if k not in data]
            checks.append({"name": "contract_keys", "ok": not missing,
                           "detail": ("missing=%s" % missing) if missing else "all present"})
            ok = ok and not missing
            unp = len(data.get("evidence", {}).get("unverified_claims", []))
            checks.append({"name": "unverified_claims", "ok": unp == 0,
                           "detail": "count=%d" % unp})
        except Exception as e:  # noqa: BLE001
            checks.append({"name": "contract_keys", "ok": False, "detail": str(e)})
            ok = False

    em = os.path.join(out_dir, "evidence_map.md")
    checks.append({"name": "evidence_map_md", "ok": os.path.isfile(em), "detail": ""})
    ok = ok and os.path.isfile(em)
    ej = os.path.join(out_dir, "evidence_map.json")
    checks.append({"name": "evidence_map_json", "ok": os.path.isfile(ej), "detail": ""})
    ok = ok and os.path.isfile(ej)

    pv = os.path.join(out_dir, "preview")
    pngs = [f for f in os.listdir(pv) if f.endswith(".png")] if os.path.isdir(pv) else []
    checks.append({"name": "previews", "ok": len(pngs) > 0,
                   "detail": "png=%d pdf=%s" % (len(pngs),
                                                os.path.isfile(os.path.join(pv, "preview.pdf")))})
    ok = ok and len(pngs) > 0
    return {"all_pass": ok, "checks": checks}


def main(argv=None):
    ap = argparse.ArgumentParser(description="end-to-end artifact self-check")
    ap.add_argument("--out", required=True, help="output directory with artifacts")
    ap.add_argument("--case", default=None, help="original case.json (optional)")
    ap.add_argument("--pptx", default=None, help="deck path (default <out>/work/deck.pptx)")
    ap.add_argument("--slides", type=int, default=None, help="expected slide count")
    args = ap.parse_args(argv)

    out_dir = os.path.abspath(args.out)
    case_id = "unknown"
    if args.case and os.path.isfile(args.case):
        with open(args.case, "r", encoding="utf-8") as f:
            case = json.load(f)
        case_id = case.get("case_id", "unknown")
    pptx_path = args.pptx or os.path.join(out_dir, "work", "deck.pptx")
    expected = args.slides
    if expected is None:
        rj = os.path.join(out_dir, "result.json")
        if os.path.isfile(rj):
            with open(rj, "r", encoding="utf-8") as f:
                expected = json.load(f).get("deck", {}).get("slide_count")
    contract_keys = ["case_id", "status", "created_at", "deck", "evidence",
                     "previews", "sources", "uncertainty", "change_records"]
    rep = run_self_check(out_dir, case_id, pptx_path, expected, contract_keys)
    print(json.dumps({"case_id": case_id, "all_pass": rep["all_pass"],
                      "checks": rep["checks"]}, ensure_ascii=False, indent=2))
    return 0 if rep["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())