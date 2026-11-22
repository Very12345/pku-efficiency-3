#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
selftest.py — independent re-verification of a produced output directory.
(verify role; corresponds to the high-score selftest.py pattern.)

Re-runs the whole gate chain without regenerating anything:
  * validate_result.validate  (structure/files/numbers)
  * check_contract.check      (contract from sibling self_check contract_applied)
  * evidence_audit.audit_evidence (verbatim quote check, best-effort from disk)
  * verify_deck.verify_deck   (opens the produced .pptx, per-slide invariants,
    OPC integrity, normalized sha)
  * determinism probe         (content-projection sha over talk_plan.json and
    evidence_map.json — recording timestamps excluded)

Optional --package-check <skill-root> audits the package constraints
(G10: <=50 UTF-8 text files, single file <=500KB, total <=2MB, no symlinks,
no __pycache__) — the same limits the platform enforces at submission.

CLI: python selftest.py <out_dir> [--package-check <skill-root>]
Exit code 0 when all re-checks pass.
"""

import json
import os
import sys

from common import (deterministic_sha, read_json)
import validate_result as vr
import check_contract as cc
import evidence_audit as ea
import verify_deck as vd


def _package_check(skill_root):
    """Audit the submission limits defined by the runtime contract."""
    report = {"ok": True, "checks": [], "errors": []}
    text_exts = {".md", ".txt", ".json", ".py", ".yml", ".yaml", ".html",
                 ".css", ".js", ".csv", ".rst", ".ini", ".cfg", ".toml"}
    n_text = 0
    total = 0
    max_file = 0
    symlinks = []
    pycache = []
    for root, dirs, files in os.walk(skill_root):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git")]
        for fn in files:
            full = os.path.join(root, fn)
            if os.path.islink(full):
                symlinks.append(full)
            if "__pycache__" in full:
                pycache.append(full)
            size = os.path.getsize(full)
            total += size
            max_file = max(max_file, size)
            if os.path.splitext(fn)[1].lower() in text_exts:
                n_text += 1
            if size > 500 * 1024:
                report["errors"].append("file >500KB: %s (%d)" % (full, size))
    report["checks"] = [
        {"check": "text_files_le_50", "ok": n_text <= 50, "detail": "n_text=%d" % n_text},
        {"check": "total_le_2MB", "ok": total <= 2 * 1024 * 1024, "detail": "total=%d" % total},
        {"check": "max_file_le_500KB", "ok": max_file <= 500 * 1024,
         "detail": "max_file=%d" % max_file},
        {"check": "no_symlinks", "ok": len(symlinks) == 0, "detail": "symlinks=%s" % symlinks},
        {"check": "no_pycache", "ok": len(pycache) == 0, "detail": "pycache=%s" % pycache[:5]},
    ]
    for c in report["checks"]:
        if not c["ok"]:
            report["errors"].append(c["check"])
    report["ok"] = len(report["errors"]) == 0
    report["summary"] = "text=%d total_bytes=%d max_file=%d" % (n_text, total, max_file)
    return report


def run_selftest(out_dir, package_root=None):
    result_path = os.path.join(out_dir, "result.json")
    checks = []
    errors = []

    def _chk(name, ok, detail=""):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})
        if not ok:
            errors.append(name + " " + str(detail)[:200])

    if not os.path.exists(result_path):
        _chk("result.json exists", False, "missing")
        return {"valid": False, "checks": checks, "errors": errors,
                "package_check": None}

    with open(result_path, "r", encoding="utf-8") as fh:
        result = json.load(fh)

    vrep = vr.validate(result, out_dir, strict=False)
    _chk("validate_result", vrep.get("valid"),
         "errors=%s" % vrep.get("errors", [])[:5])

    sr = os.path.join(out_dir, "self_check.json")
    specs = None
    note = "built-in default"
    if os.path.exists(sr):
        with open(sr, "r", encoding="utf-8") as fh:
            sc = json.load(fh)
        applied = sc.get("contract_applied")
        if applied:
            specs = cc.normalize_output_contract(applied)
            note = "self_check.json contract_applied"
    crep = cc.check(result, specs, note)
    _chk("check_contract", crep.get("valid"),
         "missing=%s wrong_type=%s" % (crep.get("missing_required"),
                                       crep.get("wrong_type")))

    erep = ea.audit_evidence(result.get("pages"), result=result, result_dir=out_dir)
    _chk("evidence_audit", erep.get("valid"),
         "errors=%d summary=%s" % (erep.get("summary", {}).get("errors"),
                                   erep.get("summary")))

    deck_path = None
    artifacts = result.get("artifacts") or {}
    if artifacts.get("editable_deck"):
        deck_path = os.path.join(out_dir, artifacts["editable_deck"])
    if deck_path and os.path.exists(deck_path):
        drep = vd.verify_deck(deck_path, expect_pages=len(result.get("pages") or []),
                              plan=result)
        _chk("verify_deck", drep.get("valid"), "errors=%s" % drep.get("errors", [])[:5])
    else:
        _chk("verify_deck", False, "deck missing (%s)" % deck_path)

    # determinism probe
    try:
        with open(os.path.join(out_dir, "talk_plan.json"), "r", encoding="utf-8") as fh:
            plan_obj = json.load(fh)
        with open(os.path.join(out_dir, "evidence_map.json"), "r", encoding="utf-8") as fh:
            emap_obj = json.load(fh)
        probe = {"plan_sha16": deterministic_sha(plan_obj),
                 "evidence_map_sha16": deterministic_sha(emap_obj)}
        _chk("determinism_probe", True, "plan=%s emap=%s" % (
            probe["plan_sha16"][:12], probe["evidence_map_sha16"][:12]))
    except Exception as exc:  # noqa: BLE001
        _chk("determinism_probe", False, str(exc))

    pkg = _package_check(package_root) if package_root else None
    if pkg is not None:
        _chk("package_constraints", pkg.get("ok"),
             "errors=%s" % pkg.get("errors"))

    return {"valid": len(errors) == 0, "checks": checks, "errors": errors,
            "package_check": pkg,
            "summary": "checks=%d errors=%d" % (len(checks), len(errors))}


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if len(args) < 2:
        print(json.dumps({"error": "usage: selftest.py <out_dir> "
                                   "[--package-check <skill-root>]"},
                         ensure_ascii=False))
        return 2
    out_dir = args[1]
    package_root = None
    if "--package-check" in argv:
        package_root = argv[argv.index("--package-check") + 1]
    report = run_selftest(out_dir, package_root=package_root)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))