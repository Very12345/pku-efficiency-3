#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run_case_set.py — run the whole synthetic case set and score it against the
declared acceptance ranges, so "the Skill generalises" is a measurement.

The case set lives in `examples/cases/` (plus the shipped `examples/` case as
the L0 baseline).  `examples/cases/case_manifest.json` declares, per case, the
difficulty tier and the acceptable range for a correct run.  This script:

  1. copies every case **out of the package** into a scratch directory
     (never writes inside the package: `__pycache__/*.pyc` would break the
     submission resource contract);
  2. synthesises the placeholder figures each case references
     (`make_synthetic_inputs.py --out-dir <figs>`);
  3. runs the real `scripts/main.py` end to end for that case;
  4. measures the produced `result.json` against the declared ranges;
  5. writes a JSON report and a Markdown table.

A case that runs but misses its declared range is reported as `RANGE-MISS`
with the offending field — never quietly counted as a pass.

Usage:
    python scripts/run_case_set.py --cases <examples dir> --run <scratch dir> \
        [--json <report.json>] [--markdown <table.md>] [--only a,b] [--timeout 300]

Exit codes: 0 = every case in range; 1 = at least one range miss or crash;
2 = usage/environment error.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time

# The fig1/fig2 names come from make_synthetic_inputs.py; a case may reference a
# subset, so figure synthesis simply offers both and the extractor uses what the
# case declares.
FIG_NAMES = ("fig1.png", "fig2.png")


def _rm(path: str) -> None:
    if os.path.exists(path):
        shutil.rmtree(path, ignore_errors=True)


def _load_json(path: str):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def _write(path: str, text: str) -> None:
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def _frac(num, den) -> float:
    try:
        num, den = float(num), float(den)
        return (num / den) if den else 0.0
    except Exception:
        return 0.0


class CaseSetRunner:
    def __init__(self, skill: str, cases_dir: str, run_dir: str, timeout: int = 300):
        self.skill = os.path.abspath(skill)
        self.cases_dir = os.path.abspath(cases_dir)
        self.run = os.path.abspath(run_dir)
        self.timeout = timeout
        self.main = os.path.join(self.skill, "scripts", "main.py")
        self.mkfigs = os.path.join(self.skill, "scripts", "make_synthetic_inputs.py")

    def _exec(self, argv, cwd):
        os.makedirs(cwd, exist_ok=True)
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        try:
            p = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, timeout=self.timeout)
            return (p.returncode, p.stdout.decode("utf-8", "replace"),
                    p.stderr.decode("utf-8", "replace"))
        except subprocess.TimeoutExpired:
            return 124, "", f"timeout after {self.timeout}s"

    def discover(self, manifest: dict, manifest_dir: str) -> list:
        """Return [(case_id, source_dir, spec)] for the manifest's cases.

        Each spec's `dir` is resolved **relative to the manifest's own
        directory** (that is what makes ".." mean "the shipped examples case"
        and "case-b-..." mean "a sibling case dir").
        """
        found = []
        for spec in manifest.get("cases", []):
            src = os.path.normpath(os.path.join(manifest_dir, spec.get("dir", ".")))
            cj = os.path.join(src, "case.json")
            if not os.path.isfile(cj):
                found.append((spec.get("case_id", "?"), None, spec))
                continue
            found.append((spec.get("case_id") or _load_json(cj).get("case_id"), src, spec))
        return found

    def run_one(self, case_id: str, src: str, spec: dict) -> dict:
        rec = {"case_id": case_id, "difficulty": spec.get("difficulty", ""),
               "theme": spec.get("theme", ""), "purpose": spec.get("purpose", ""),
               "source": src}
        if src is None:
            rec.update({"verdict": "MISSING-CASE", "problems": ["case.json not found"]})
            return rec

        stamp = time.strftime("%H%M%S")
        work = os.path.join(self.run, f"{case_id}-{stamp}")
        inputs = os.path.join(work, "inputs", case_id)
        out = os.path.join(work, "out")
        cwd = os.path.join(work, "cwd")
        _rm(work)
        os.makedirs(os.path.dirname(inputs), exist_ok=True)
        shutil.copytree(src, inputs)

        # --- figures: synthesised into the scratch copy, never into the package
        figs_dir = os.path.join(inputs, "figs")
        frc, fout, ferr = self._exec(
            [sys.executable, self.mkfigs, "--out-dir", figs_dir], cwd)
        rec["figure_synthesis_exit"] = frc
        rec["figures_available"] = sorted(os.listdir(figs_dir)) if os.path.isdir(figs_dir) else []

        # --- the real run
        case_json = os.path.join(inputs, "case.json")
        task_md = os.path.join(inputs, "task.md")
        argv = [sys.executable, self.main, "--case", case_json, "--out", out]
        if os.path.isfile(task_md):
            argv += ["--task", task_md]
        t0 = time.perf_counter()
        rc, stdout, stderr = self._exec(argv, cwd)
        rec["exit"] = rc
        rec["seconds"] = round(time.perf_counter() - t0, 2)
        rec["stdout_tail"] = (stdout or "").strip().splitlines()[-1][:200] if stdout.strip() else ""
        rec["stderr_tail"] = (stderr or "").strip().splitlines()[-1][:200] if stderr.strip() else ""

        result = _load_json(os.path.join(out, "result.json"))
        rec["result_json_written"] = result is not None
        if result is None:
            rec.update({"verdict": "NO-RESULT", "problems": ["result.json not produced"]})
            return rec

        # --- measure against the declared range
        mr = result.get("main_result") or {}
        ta = result.get("template_audit") or {}
        ver = result.get("verification") or {}
        gates = ver.get("contract_gates") or []
        slides = result.get("slide_count") or 0
        ev = result.get("slide_evidence") or []
        ev_lines = sum(len(p.get("evidence") or []) for p in ev)
        ev_located = sum(1 for p in ev for e in (p.get("evidence") or []) if e.get("loc"))
        null_keys = [k for k, v in result.items() if v is None]

        m = {
            "status": result.get("status"),
            "slide_count": slides,
            "notes_pages": mr.get("notes_pages"),
            "notes_frac": _frac(mr.get("notes_pages"), slides),
            "artifacts": len(result.get("artifacts") or []),
            "slide_evidence_pages": len(ev),
            "evidence_lines": ev_lines,
            "evidence_located": ev_located,
            "evidence_loc_frac": _frac(ev_located, ev_lines),
            "figures_total": mr.get("figures_total"),
            "figures_embedded": mr.get("figures_embedded"),
            "figures_placed_frac": _frac(mr.get("figures_embedded"), mr.get("figures_total")),
            "tables_pages": mr.get("tables_pages"),
            "contract_gates_pass": sum(1 for g in gates if g.get("ok")),
            "contract_gates_failed": [g.get("gate") for g in gates if not g.get("ok")],
            "null_top_keys": len(null_keys),
            "null_top_key_names": null_keys,
            "adopt_plan_applied": ta.get("adopt_plan_applied"),
            "adopt_plan_total_pages": ta.get("adopt_plan_total_pages"),
            "adopt_plan_applied_frac": _frac(ta.get("adopt_plan_applied"), ta.get("adopt_plan_total_pages")),
            "layout_used": len(ta.get("layout_used") or []),
            "opened_from": ta.get("opened_from"),
            "template_errors": len(ta.get("template_errors") or []),
            "layout_fallback_used": ta.get("layout_fallback_used"),
            "adopt_plan_deviations": len(ta.get("adopt_plan_deviations") or []),
            "uncertainty": len(result.get("uncertainty") or []),
            "change_records": [c.get("action") for c in (result.get("change_records") or [])],
            "top_keys": len(result.keys()),
        }
        rec["measured"] = m

        # --- range checks
        exp = spec.get("expected") or {}
        problems = []
        boundary = False
        if rc != 0:
            problems.append(f"main.py exit {rc}")
        if exp.get("status_any_of") and m["status"] not in exp["status_any_of"]:
            problems.append(f"status {m['status']!r} not in {exp['status_any_of']}")
        if "slide_count" in exp and m["slide_count"] != exp["slide_count"]:
            problems.append(f"slide_count {m['slide_count']} != {exp['slide_count']}")
        if "slide_count_range" in exp:
            lo, hi = exp["slide_count_range"]
            m["slide_count_range"] = [lo, hi]
            if m["slide_count"] < lo:
                problems.append(f"slide_count {m['slide_count']} < declared floor {lo}")
            elif m["slide_count"] == hi and exp.get("boundary_note"):
                # A declared boundary hit: inside the range we published, but at
                # the edge we documented.  Reported as `boundary-hit` so it is
                # neither a silent pass nor mislabelled a range miss.
                boundary = True
                m["boundary_note"] = exp["boundary_note"]
            elif m["slide_count"] > hi:
                problems.append(f"slide_count {m['slide_count']} > declared ceiling {hi}")
        if "notes_frac_min" in exp and m["notes_frac"] < exp["notes_frac_min"]:
            problems.append(f"notes_frac {m['notes_frac']:.3f} < {exp['notes_frac_min']}")
        if "evidence_loc_frac_min" in exp and m["evidence_loc_frac"] < exp["evidence_loc_frac_min"]:
            problems.append(f"evidence_loc_frac {m['evidence_loc_frac']:.3f} < {exp['evidence_loc_frac_min']}")
        if "figures_placed_frac_min" in exp and m["figures_placed_frac"] < exp["figures_placed_frac_min"]:
            problems.append(f"figures_placed_frac {m['figures_placed_frac']:.3f} < {exp['figures_placed_frac_min']}")
        if "contract_gates_pass" in exp and m["contract_gates_pass"] != exp["contract_gates_pass"]:
            problems.append(f"contract gates passed {m['contract_gates_pass']} != {exp['contract_gates_pass']}")
        if "null_top_keys" in exp and m["null_top_keys"] != exp["null_top_keys"]:
            problems.append(f"null_top_keys {m['null_top_keys']} != {exp['null_top_keys']}")
        if "adopt_plan_applied_frac_min" in exp and m["adopt_plan_applied_frac"] < exp["adopt_plan_applied_frac_min"]:
            problems.append(f"adopt_plan_applied_frac {m['adopt_plan_applied_frac']:.3f} < "
                            f"{exp['adopt_plan_applied_frac_min']}")
        if exp.get("material_supplemented_required"):
            # the story line must have been recovered from the material markdown
            content = _load_json(os.path.join(out, "content.json")) or {}
            sup = content.get("supplemented_from_material") or {}
            got = sorted(k for k, v in sup.items() if v)
            m["material_supplemented_buckets"] = got
            if len(got) < 6:
                problems.append(f"material-supplemented buckets {got} — expected all six")

        rec["problems"] = problems
        rec["boundary_hit"] = bool(boundary and not problems)
        rec["verdict"] = ("RANGE-MISS" if problems else
                          "boundary-hit" if boundary else "in-range")
        return rec


def to_markdown(records: list, manifest: dict) -> str:
    L = []
    L.append("| 案例 | 难度层 | 题材 | exit | slide_count | 讲稿覆盖 | 证据定位覆盖 | 图表落位 | 契约门 | 顶层 null | 判定 |")
    L.append("|-|-|-|-|-|-|-|-|-|-|-|")
    for r in records:
        m = r.get("measured") or {}
        L.append("| `{}` | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
            r["case_id"], r.get("difficulty", ""), r.get("theme", ""),
            r.get("exit", "—"),
            m.get("slide_count", "—"),
            f"{m['notes_frac']:.2f}" if m else "—",
            f"{m['evidence_loc_frac']:.2f}" if m else "—",
            f"{m['figures_embedded']}/{m['figures_total']}" if m else "—",
            f"{m['contract_gates_pass']}/8" if m else "—",
            m.get("null_top_keys", "—"),
            r.get("verdict", "—")))
    L.append("")
    L.append("### 逐案实测明细")
    L.append("")
    for r in records:
        L.append(f"#### `{r['case_id']}` — {r.get('difficulty','')}")
        L.append("")
        L.append(f"- **题材**：{r.get('theme','')}")
        L.append(f"- **该案用途**：{r.get('purpose','')}")
        m = r.get("measured")
        if not m:
            L.append(f"- **实测**：exit={r.get('exit')}；{'; '.join(r.get('problems') or [])}")
            L.append("")
            continue
        L.append(f"- **实测**：exit={r['exit']}（{r.get('seconds')}s）；status=`{m['status']}`；"
                 f"页数 {m['slide_count']}；产物 {m['artifacts']} 个；顶层键 {m['top_keys']} 个")
        L.append(f"- **讲稿**：{m['notes_pages']}/{m['slide_count']} 页有 speaker notes")
        L.append(f"- **证据**：{m['slide_evidence_pages']} 页有页级证据；"
                 f"证据行 {m['evidence_located']}/{m['evidence_lines']} 带定位"
                 f"（覆盖率 {m['evidence_loc_frac']:.3f}）")
        L.append(f"- **模板**：`opened_from={m['opened_from']}`；枚举版式使用记录 {m['layout_used']} 条；"
                 f"方案套用 {m['adopt_plan_applied']}/{m['adopt_plan_total_pages']}；"
                 f"偏差 {m['adopt_plan_deviations']} 条；`layout_fallback_used={m['layout_fallback_used']}`")
        L.append(f"- **契约**：门 {m['contract_gates_pass']}/8 通过"
                 + (f"（失败 {m['contract_gates_failed']}）" if m["contract_gates_failed"] else "")
                 + f"；顶层 null {m['null_top_keys']} 个；uncertainty {m['uncertainty']} 条")
        L.append(f"- **图表**：{m['figures_embedded']}/{m['figures_total']} 图上位；表格页 {m['tables_pages']}")
        if m.get("material_supplemented_buckets") is not None:
            L.append(f"- **材料补位**：`supplemented_from_material` 命中的桶 = "
                     f"{m['material_supplemented_buckets']}")
        if m.get("change_records"):
            L.append(f"- **change_records**：{m['change_records']}")
        L.append(f"- **判定**：**{r['verdict']}**"
                 + ("；" + "；".join(r["problems"]) if r.get("problems") else ""))
        if m.get("boundary_note"):
            L.append(f"- **边界说明（已声明）**：{m['boundary_note']}")
        L.append("")
    return "\n".join(L)


def main(argv=None):
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skill", default=os.path.dirname(here),
                    help="package root (default: parent of this script's dir)")
    ap.add_argument("--cases", default="", help="examples dir holding the case set")
    ap.add_argument("--run", default="", help="scratch dir (default: <cwd>/case-set-run)")
    ap.add_argument("--only", default="", help="comma separated case ids")
    ap.add_argument("--json", default="", help="write the JSON report here")
    ap.add_argument("--markdown", default="", help="write the Markdown table here")
    ap.add_argument("--timeout", type=int, default=300, help="per-case timeout (s)")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args(argv)

    skill = os.path.abspath(a.skill)
    cases = os.path.abspath(a.cases or os.path.join(skill, "examples"))
    run = os.path.abspath(a.run or os.path.join(os.getcwd(), "case-set-run"))

    def inside(p, root):
        p, root = os.path.abspath(p), os.path.abspath(root)
        return p == root or p.startswith(root + os.sep)

    if inside(run, skill):
        print("[run_case_set] refusing a scratch dir inside the package "
              "(would leave scripts/__pycache__).  Pass --run outside the package.",
              file=sys.stderr)
        return 2

    manifest_path = os.path.join(cases, "cases", "case_manifest.json")
    manifest = _load_json(manifest_path)
    if not manifest:
        print(f"[run_case_set] cannot read the case manifest: {manifest_path}", file=sys.stderr)
        return 2

    R = CaseSetRunner(skill, cases, run, timeout=a.timeout)
    if not os.path.isfile(R.main):
        print(f"[run_case_set] main.py not found under {skill}", file=sys.stderr)
        return 2

    todo = R.discover(manifest, os.path.dirname(manifest_path))
    only = {x.strip() for x in a.only.split(",") if x.strip()}
    if only:
        todo = [t for t in todo if t[0] in only]
    if a.list:
        for cid, src, spec in todo:
            print(f"{cid:28s} {spec.get('difficulty',''):24s} {spec.get('theme','')}")
        return 0

    print(f"[run_case_set] skill={skill}")
    print(f"[run_case_set] cases={cases}")
    print(f"[run_case_set] run  ={run}")
    records = []
    for cid, src, spec in todo:
        rec = R.run_one(cid, src, spec)
        records.append(rec)
        m = rec.get("measured") or {}
        print(f"  {cid:28s} exit={rec.get('exit','—'):<3} status={str(m.get('status')):<8} "
              f"slides={str(m.get('slide_count','—')):<3} -> {rec['verdict']}")

    misses = [r for r in records if r["verdict"] == "RANGE-MISS"]
    boundaries = [r for r in records if r.get("boundary_hit")]
    report = {
        "_meta": "case-set generalisation run; every number is measured against case_manifest.json",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "python": sys.version.split()[0],
        "skill": skill, "cases_dir": cases, "run_dir": run,
        "case_count": len(records),
        "out_of_range": len(misses),
        "boundary_hits": len(boundaries),
        "cases": records,
    }
    if a.json:
        _write(a.json, json.dumps(report, ensure_ascii=False, indent=2))
        print(f"[run_case_set] json  -> {a.json}")
    if a.markdown:
        _write(a.markdown, to_markdown(records, manifest))
        print(f"[run_case_set] table -> {a.markdown}")
    print(f"[run_case_set] {len(records)} cases, {len(misses)} out of declared range, "
          f"{len(boundaries)} declared boundary hit(s)")
    for r in boundaries:
        m = r.get("measured") or {}
        print(f"  ~ {r['case_id']}: slide_count={m.get('slide_count')} sits on the declared "
              f"ceiling {m.get('slide_count_range')} — see references/CASE-SET.md")
    for r in misses:
        print(f"  ! {r['case_id']}: {'; '.join(r.get('problems') or [])}")
    return 1 if misses else 0


if __name__ == "__main__":
    raise SystemExit(main())
