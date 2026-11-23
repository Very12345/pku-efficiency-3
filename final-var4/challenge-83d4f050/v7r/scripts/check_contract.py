# -*- coding: utf-8 -*-
"""Standalone result.json contract check (aligned with the full-score sample's
`scripts/check_contract.py`: 83-point package carried check_contract.py).

Verifies a produced result.json against references/OUTPUT_CONTRACT.md:
  * file exists & parses
  * envelope keys present (case_id/status/deliverables/scientific_content/
    evidence_sources/uncertainty/change_records/export_checks/self_check)
  * status ∈ {success, partial, failed}
  * no top-level null values (four-form echo rule: 缺省按类型填空，禁止 null)
  * when --case is given: every output_contract field appears at top level
  * deliverables paths exist relative to the result.json directory (warn)
  * gates g1..g8 present when produced by v2 pipeline

Exit code: 0 = contract pass, 1 = contract fail.
"""
import argparse
import json
import os
import sys

REQUIRED_ENVELOPE = ["case_id", "status", "deliverables", "scientific_content",
                     "evidence_sources", "uncertainty", "change_records",
                     "export_checks", "self_check"]
STATUS_VALUES = ("success", "partial", "failed")


def _load(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def check_result(result_path, case_path=None):
    """Return {ok, checks, summary}.  checks: [{id, name, result, detail}]."""
    checks = []
    ok = True

    def add(cid, name, good, detail):
        nonlocal ok
        if not good:
            ok = False
        result = "pass" if good else "fail"
        checks.append({"id": cid, "check": name, "result": result, "detail": detail})

    if not (os.path.isfile(result_path)):
        return {"ok": False, "checks": [{"id": "C01", "check": "result.json 存在",
                                         "result": "fail", "detail": result_path}],
                "summary": "missing result.json"}
    try:
        rj = _load(result_path)
    except Exception as ex:
        return {"ok": False, "checks": [{"id": "C02", "check": "result.json 可解析",
                                         "result": "fail", "detail": str(ex)}],
                "summary": "unparseable result.json"}

    add("C01", "case_id 非空", bool(rj.get("case_id")), "case_id=%r" % rj.get("case_id"))
    add("C02", "status 三值枚举", rj.get("status") in STATUS_VALUES,
        "status=%r" % rj.get("status"))
    miss_env = [k for k in REQUIRED_ENVELOPE if k not in rj]
    add("C03", "信封字段齐全", not miss_env,
        ("缺: %s" % ", ".join(miss_env)) if miss_env else "信封字段齐全")

    # no top-level null
    nulls = [k for k, v in rj.items() if v is None]
    add("C04", "顶层禁止 null", not nulls,
        ("null 字段: %s" % ", ".join(nulls)) if nulls else "顶层无 null（四形态填空）")

    # output_contract echo
    if case_path and os.path.isfile(case_path):
        case = _load(case_path)
        oc = case.get("output_contract")
        if isinstance(oc, dict) and oc:
            miss_fields = [k for k in oc if k not in rj]
            add("C05", "output_contract 全部回显", not miss_fields,
                ("缺回显: %s" % ", ".join(miss_fields)) if miss_fields
                else "%d 个契约字段全部回显" % len(oc))
        else:
            add("C05", "output_contract 全部回显", True, "case.json 无 output_contract")
    else:
        add("C05", "output_contract 全部回显", True, "未提供 --case，跳过回显核对")

    # deliverables paths exist (warn only)
    base = os.path.dirname(os.path.abspath(result_path))
    missing = []
    for group in ("editable_sources", "previews", "exports"):
        for item in rj.get("deliverables", {}).get(group, []) or []:
            p = item.get("path")
            if p and not os.path.isfile(os.path.join(base, p)):
                missing.append("%s/%s" % (group, p))
    if missing:
        checks.append({"id": "C06", "check": "deliverables 路径存在",
                       "result": "warn", "detail": "缺失: %s" % ", ".join(missing)})
    else:
        checks.append({"id": "C06", "check": "deliverables 路径存在",
                       "result": "pass", "detail": "全部产物路径存在"})

    gates = rj.get("gates")
    if isinstance(gates, dict) and gates:
        g_fail = [k for k, v in gates.items() if not v.get("pass")]
        add("C07", "硬性门 G1–G8 全过", not g_fail,
            ("未过: %s" % ", ".join(g_fail)) if g_fail else "%d/%d 门全过" % (len(gates), len(gates)))
    else:
        add("C07", "硬性门 G1–G8 全过", True, "该 result.json 无 gates（非 v2 流水线产物）")

    summary = "ok" if ok else "fail"
    return {"ok": ok, "checks": checks,
            "summary": "contract|%s|case=%s|status=%s|checks=%d" % (
                summary, rj.get("case_id"), rj.get("status"), len(checks))}


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="check result.json against OUTPUT_CONTRACT.md")
    ap.add_argument("--result", required=True, help="path to result.json")
    ap.add_argument("--case", help="path to case.json whose output_contract must echo")
    args = ap.parse_args(argv)
    r = check_result(args.result, args.case)
    for c in r["checks"]:
        print("%-6s %-30s %s" % (c["result"], c["id"], c["check"]))
        if c["result"] != "pass":
            print("        detail: %s" % c["detail"])
    print(r["summary"])
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())