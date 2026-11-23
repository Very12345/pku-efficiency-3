#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run every bundled example end-to-end and verify the contract gates.

This is the reproducibility entry point promised by examples/EXPECTED-OUTPUT.md
and TEST.md: it regenerates the demo artifacts that are deliberately NOT
shipped inside the package (PDF/PNG/SVG are unsupported Skill resource types,
and pre-generated figures must not be mistaken for official answers).

Steps (all with the skill root resolved from __file__, so any cwd works):

  1. schematic : main.py --case <root>/examples/case.json      -> out/schematic
  2. chart     : main.py --case <root>/examples/case_chart.json-> out/chart
  3. edit      : main.py --case <root>/examples/case_edit.json
                 --edit-svg out/schematic/figure.svg            -> out/edit
  4. contract  : validate_result.py (G1-G8) on each result.json

Exit codes: 0 = every step passed, 1 = at least one step failed,
2 = the requested output directory could not be prepared.

Nothing is written inside the skill directory unless the caller explicitly
passes --out pointing there.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

try:  # narrow Windows consoles (GBK) must not crash --help or log output
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")
except Exception:
    pass

_HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(_HERE)
EXAMPLES = os.path.join(SKILL_ROOT, "examples")

FAILED = []


def run(step, cmd, expect=0, cwd=None):
    """Run one step; return (ok, stdout_tail)."""
    print("\n=== [%s] %s" % (step, " ".join('"%s"' % c if " " in c else c
                                            for c in cmd)), flush=True)
    proc = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    out = proc.stdout.decode("utf-8", "replace")
    tail = "\n".join(out.strip().splitlines()[-12:])
    if tail:
        print(tail)
    ok = proc.returncode == expect
    print("--- [%s] exit=%d (expected %d) -> %s"
          % (step, proc.returncode, expect, "PASS" if ok else "FAIL"))
    if not ok:
        FAILED.append("%s (exit %d != %d)" % (step, proc.returncode, expect))
    return ok, out


def gate_result(result_path, required_keys):
    """Check deliverables exist and result.json carries the contract keys."""
    ok = True
    if not os.path.isfile(result_path):
        FAILED.append("missing result.json: %s" % result_path)
        return False
    with open(result_path, "r", encoding="utf-8") as fh:
        res = json.load(fh)
    missing = [k for k in required_keys if k not in res]
    if missing:
        FAILED.append("result.json missing contract keys: %s" % missing)
        ok = False
    print("      status=%r  top-level keys=%d  missing=%s"
          % (res.get("status"), len(res), missing or "none"))
    for art in res.get("artifacts") or []:
        p = os.path.join(os.path.dirname(result_path), art.get("path") or "")
        if not os.path.isfile(p):
            FAILED.append("declared artifact missing: %s" % art.get("path"))
            ok = False
    return ok


CONTRACT_KEYS = ["case_id", "skill", "status", "workorder", "task_summary",
                 "figure_type", "title", "main_result", "artifacts",
                 "evidence", "legend_mapping", "data_mapping", "verification",
                 "determinism", "sources", "uncertainty", "change_records",
                 "status_notes", "generated_at", "generator", "tool_versions"]


def required_keys_for(case_json):
    """Base contract keys + whatever case.json declares in output_contract
    (those are echoed to the result top level, four-shape defaults)."""
    keys = list(CONTRACT_KEYS)
    try:
        with open(case_json, "r", encoding="utf-8") as fh:
            oc = (json.load(fh) or {}).get("output_contract") or {}
        keys += [k for k in oc if k not in keys]
    except Exception as exc:
        FAILED.append("cannot read case for output_contract: %s (%r)"
                      % (case_json, exc))
    return keys


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=None,
                    help="output root for the demo runs (default: a fresh "
                         "temp dir; nothing is written into the skill dir)")
    ap.add_argument("--keep", action="store_true",
                    help="keep an auto-created temp dir (prints the path)")
    args = ap.parse_args(argv)

    out_root = os.path.abspath(args.out) if args.out else tempfile.mkdtemp(
        prefix="sse-examples-")
    try:
        os.makedirs(out_root, exist_ok=True)
    except OSError as exc:
        print("FATAL: cannot prepare --out %s: %r" % (out_root, exc))
        return 2
    main_py = os.path.join(_HERE, "main.py")
    val_py = os.path.join(_HERE, "validate_result.py")
    py = sys.executable or "python"
    print("skill root: %s\noutput root: %s" % (SKILL_ROOT, out_root))

    cases = [
        ("schematic", os.path.join(EXAMPLES, "case.json"), None),
        ("chart", os.path.join(EXAMPLES, "case_chart.json"), None),
        ("edit", os.path.join(EXAMPLES, "case_edit.json"),
         os.path.join(out_root, "schematic", "figure.svg")),
    ]
    for step, case_json, edit_svg in cases:
        if not os.path.isfile(case_json):
            FAILED.append("example input missing: %s" % case_json)
            continue
        out_dir = os.path.join(out_root, step)
        cmd = [py, main_py, "--case", case_json, "--out", out_dir]
        if edit_svg:
            if not os.path.isfile(edit_svg):
                FAILED.append("edit example needs the schematic SVG, which "
                              "was not produced: %s" % edit_svg)
                continue
            cmd += ["--edit-svg", edit_svg]
        ok, _ = run(step, cmd, expect=0)
        if ok:
            gate_result(os.path.join(out_dir, "result.json"),
                        required_keys_for(case_json))

    for step, case_json, _e in cases:
        out_dir = os.path.join(out_root, step)
        rp = os.path.join(out_dir, "result.json")
        if os.path.isfile(rp):
            run("%s:contract" % step,
                [py, val_py, "--case", case_json, "--result", rp], expect=0)

    print("\n" + "=" * 64)
    if FAILED:
        print("EXAMPLES: %d problem(s)" % len(FAILED))
        for f in FAILED:
            print("  FAIL %s" % f)
        return 1
    print("EXAMPLES: all steps passed; artifacts under %s" % out_root)
    if not args.out and not args.keep:
        shutil.rmtree(out_root, ignore_errors=True)
        print("(temp output removed; pass --out or --keep to inspect it)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
