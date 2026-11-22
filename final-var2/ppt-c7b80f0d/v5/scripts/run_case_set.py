#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run_case_set.py — 多案例题集执行件：把示例 + 合成案例逐个跑真、逐个对验收区间。

它回答的是"**这套 Skill 换一个题材还成立吗**"这个问题——而且是用**命令**回答，
不是用形容词。对每个案例目录（默认 `examples/cases/*/`，可用 `--include-example`
把 `examples/` 那个最小示例也算进来）：

1. 读 `case.json`（材料的真实来源）与 `expected.json`（验收区间）；
2. 用案例自带的 `deck-spec.json` 跑 `scripts/main.py` → 真产物落在 `--out/<case>/`；
3. 逐条对**可机检的验收区间**：`status` 词表、页数区间、证据映射行数下限、
   `must_keep_verbatim` 里的每个数字是否**逐字**出现在产物文字里、
   `must_not_claim` 里的每个越界表述是否**不**出现；
4. 再跑两道交付门（`export_check` G1–G8、`check_contract` 字段覆盖）；
5. 渲染成一张表 + 一份 JSON，退出码给出总体结论。

退出码：0 = 全部案例都在验收区间内且两道门通过；1 = 有案例越界（报告里点名）；
2 = 环境不可用（连一个案例都跑不出产物）；3 = 参数/输入错误。

写盘纪律：只写 `--out` 与 `--emit-md`/`--json` 指定的路径；所有子进程带
`PYTHONDONTWRITEBYTECODE=1`，因此也可以在包外副本上安全复跑。
"""

from __future__ import annotations

import argparse
import io
import json
import os
import platform
import re
import subprocess
import sys
import time

PROTOCOL_VERSION = "case-set/1.0"
HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)


def _run(argv, cwd=None, timeout=600):
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env.pop("PYTHONPATH", None)
    proc = subprocess.run(argv, capture_output=True, timeout=timeout,
                          env=env, cwd=cwd)
    return {"argv": argv, "exit_code": proc.returncode,
            "stdout": proc.stdout.decode("utf-8", "replace")[-2000:],
            "stderr": proc.stderr.decode("utf-8", "replace")[-2000:]}


def _read_json(path):
    with io.open(path, encoding="utf-8") as fh:
        return json.load(fh)


def discover(cases_dir, include_example):
    """Return [(case_id, case_dir)] sorted; each dir must hold case.json."""
    found = []
    if include_example:
        ex = os.path.join(SKILL_DIR, "examples")
        if os.path.isfile(os.path.join(ex, "case.json")):
            found.append((_read_json(os.path.join(ex, "case.json")).get("case_id",
                                                                        "example"), ex))
    if os.path.isdir(cases_dir):
        for name in sorted(os.listdir(cases_dir)):
            d = os.path.join(cases_dir, name)
            if os.path.isfile(os.path.join(d, "case.json")):
                found.append((_read_json(os.path.join(d, "case.json")).get("case_id", name), d))
    return found


def deck_text(out_dir, deck_file):
    """Every string inside the produced .pptx — the page text is what a reader sees,
    and it lives in the deck, not in result.json (which only carries claims)."""
    if not deck_file:
        return ""
    path = os.path.join(out_dir, deck_file)
    if not os.path.isfile(path):
        return ""
    try:
        from pptx import Presentation
        prs = Presentation(path)
    except Exception:
        return ""
    parts = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    parts.append("".join(r.text for r in para.runs))
        if slide.has_notes_slide:
            for para in slide.notes_slide.notes_text_frame.paragraphs:
                parts.append("".join(r.text for r in para.runs))
    return chr(10).join(parts)


def result_text(result):
    """All human-visible text of a run, for verbatim / forbidden-phrase checks."""
    parts = []

    def walk(x):
        if isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
        elif isinstance(x, str):
            parts.append(x)
    for key in ("title", "main_claim", "slides", "deck", "evidence_mapping",
                "uncertainty"):
        walk(result.get(key))
    return "\n".join(parts)


def check_case(cid, case_dir, out_root):
    case = _read_json(os.path.join(case_dir, "case.json"))
    spec = os.path.join(case_dir, "deck-spec.json")
    out = os.path.join(out_root, cid)
    os.makedirs(out, exist_ok=True)
    argv = [sys.executable, "-B", os.path.join(SKILL_DIR, "scripts", "main.py"),
            "--case", os.path.join(case_dir, "case.json"), "--out", out]
    if os.path.isfile(spec):
        argv += ["--spec", spec]
    task = os.path.join(case_dir, "task.md")
    if os.path.isfile(task):
        argv += ["--task", task]
    run = _run(argv, cwd=os.path.dirname(out_root))
    row = {"case_id": cid, "case_dir": os.path.relpath(case_dir, SKILL_DIR),
           "run_exit": run["exit_code"], "argv": argv}
    rpath = os.path.join(out, "result.json")
    if not os.path.isfile(rpath):
        row.update({"result_present": False, "checks": [], "in_band": False,
                    "stderr": run["stderr"][-600:]})
        return row
    result = _read_json(rpath)
    row["result_present"] = True
    row["status"] = result.get("status")
    row["top_level_keys"] = len(result)
    deck = result.get("deck") or {}
    row["deck_file"] = deck.get("file")
    row["slides"] = deck.get("slide_count")
    row["previews"] = len(result.get("previews") or [])
    row["evidence_entries"] = (result.get("evidence_mapping") or {}).get("entries")
    row["evidence_gaps"] = len((result.get("evidence_mapping") or {}).get("gaps") or [])
    row["uncertainty"] = len(result.get("uncertainty") or [])
    row["charts"] = len(result.get("charts") or [])
    row["spec_lint_valid"] = bool((result.get("spec_lint") or {}).get("valid"))
    row["self_check_ok"] = bool(((result.get("run_meta") or {}).get("self_check") or {}).get("ok"))

    exp_path = os.path.join(case_dir, "expected.json")
    exp = _read_json(exp_path) if os.path.isfile(exp_path) else {}
    band = exp.get("acceptance_band") or {}
    # the numbers must be verbatim in what a *reader* sees: result.json carries the
    # claims, the deck carries the page text + notes, the evidence table carries quotes
    ev_md = os.path.join(out, "evidence_mapping.md")
    ev_txt = ""
    if os.path.isfile(ev_md):
        with io.open(ev_md, encoding="utf-8", errors="replace") as fh:
            ev_txt = fh.read()
    text = chr(10).join([result_text(result), deck_text(out, deck.get("file")), ev_txt])
    checks = []

    def add(name, ok, detail=""):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    if band.get("status"):
        add("status in band", result.get("status") in band["status"],
            "status=%s, band=%s" % (result.get("status"), band["status"]))
    if band.get("evidence_entries_min") is not None:
        n = row["evidence_entries"] or 0
        add("evidence entries >= min", n >= band["evidence_entries_min"],
            "entries=%s, min=%s" % (n, band["evidence_entries_min"]))
    if band.get("slides"):
        lo, hi = 1, 99
        rng = str(band["slides"])
        m = re.match(r"\s*(\d+)\s*[-–]\s*(\d+)", rng)   # "8-11（说明…）"
        if m:
            lo, hi = int(m.group(1)), int(m.group(2))
        add("slide count in band", lo <= (row["slides"] or 0) <= hi,
            "slides=%s, band=%s" % (row["slides"], rng))
    if band.get("uncertainty_max_if_completed") is not None:
        ok = (result.get("status") != "completed"
              or row["uncertainty"] <= band["uncertainty_max_if_completed"])
        add("uncertainty within budget when completed", ok,
            "uncertainty=%s" % row["uncertainty"])
    missing = [v for v in (band.get("must_keep_verbatim") or []) if v not in text]
    add("verbatim numbers preserved", not missing, "missing=%s" % missing)
    leaked = [v for v in (band.get("must_not_claim") or []) if v in text]
    add("forbidden claims absent", not leaked, "leaked=%s" % leaked)

    gates = {}
    gates["export_check"] = _run(
        [sys.executable, "-B", os.path.join(SKILL_DIR, "scripts", "export_check.py"),
         "--result", rpath, "--out-dir", out,
         "--case", os.path.join(case_dir, "case.json")], cwd=os.path.dirname(out_root))
    gates["check_contract"] = _run(
        [sys.executable, "-B", os.path.join(SKILL_DIR, "scripts", "check_contract.py"),
         "--result", rpath,
         "--contract", os.path.join(SKILL_DIR, "references", "OUTPUT_CONTRACT.md"),
         "--case", os.path.join(case_dir, "case.json")], cwd=os.path.dirname(out_root))
    add("export_check exit 0", gates["export_check"]["exit_code"] == 0,
        "exit=%s" % gates["export_check"]["exit_code"])
    add("check_contract exit 0", gates["check_contract"]["exit_code"] == 0,
        "exit=%s" % gates["check_contract"]["exit_code"])
    add("self_check ok", row["self_check_ok"])

    row["checks"] = checks
    row["in_band"] = all(c["ok"] for c in checks)
    row["difficulty_tier"] = exp.get("difficulty_tier")
    row["failure_boundary"] = exp.get("failure_boundary")
    row["gate_exits"] = {k: v["exit_code"] for k, v in gates.items()}
    return row


def render_md(rows, meta):
    L = []
    L.append("<!-- 本表由 scripts/run_case_set.py --emit-md 从真实运行数据渲染；"
             "不要手改数字，重跑即可。 -->")
    L.append("")
    L.append("| 案例 | 题材难度层 | 实测 exit | status | 页数 | 预览 | 证据行 | 缺口 | uncertainty | self_check | 两道门 | 逐条验收 |")
    L.append("|-|-|-|-|-|-|-|-|-|-|-|-|")
    for r in rows:
        if not r.get("result_present"):
            L.append("| `%s` | %s | %s | — | — | — | — | — | — | — | — | **未产出 result.json** |"
                     % (r["case_id"], r.get("difficulty_tier") or "—", r.get("run_exit")))
            continue
        gates = r.get("gate_exits") or {}
        gt = "export %s / contract %s" % (gates.get("export_check"), gates.get("check_contract"))
        bad = [c["check"] for c in r["checks"] if not c["ok"]]
        L.append("| `%s` | %s | %s | `%s` | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            r["case_id"], (r.get("difficulty_tier") or "—").split(" —")[0],
            r["run_exit"], r.get("status"), r.get("slides"), r.get("previews"),
            r.get("evidence_entries"), r.get("evidence_gaps"), r.get("uncertainty"),
            "OK" if r.get("self_check_ok") else "**FAIL**", gt,
            "全部通过" if r.get("in_band") else "**未通过：%s**" % "; ".join(bad)))
    L.append("")
    ok = sum(1 for r in rows if r.get("in_band"))
    L.append("**统计（本次实测）**：案例 %d 个 · 在验收区间内 %d 个 · 未通过 %d 个。"
             % (len(rows), ok, len(rows) - ok))
    L.append("")
    L.append("> 生成命令：`python \"$SKILL_DIR/scripts/run_case_set.py\" --out <报告目录> "
             "--include-example --emit-md <本表>`；协议 `%s`；Python %s；%s。"
             % (meta["protocol"], meta["python"], meta["platform"]))
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description="run every case in the case set for real")
    ap.add_argument("--out", required=True, help="report/artifact directory (outside the package)")
    ap.add_argument("--cases", default=None,
                    help="case-set directory (default: <skill>/examples/cases)")
    ap.add_argument("--include-example", action="store_true",
                    help="also run the minimal example in examples/")
    ap.add_argument("--only", default=None, help="comma separated case ids")
    ap.add_argument("--emit-md", default=None, help="write the measured table here")
    ap.add_argument("--json", default=None, help="write the full JSON report here")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    global SKILL_DIR
    out = os.path.abspath(args.out)
    if out == os.path.abspath(SKILL_DIR) or out.startswith(os.path.abspath(SKILL_DIR) + os.sep):
        print("refusing to write inside the skill package: %s" % out, file=sys.stderr)
        return 3
    cases_dir = os.path.abspath(args.cases or os.path.join(SKILL_DIR, "examples", "cases"))
    cases = discover(cases_dir, args.include_example)
    if args.only:
        want = {x.strip() for x in args.only.split(",") if x.strip()}
        cases = [c for c in cases if c[0] in want]
    if not cases:
        print("no cases found under %s" % cases_dir, file=sys.stderr)
        return 3
    os.makedirs(out, exist_ok=True)

    started = time.time()
    rows = []
    for cid, cdir in cases:
        if not args.quiet:
            print("[case] %s (%s)" % (cid, os.path.relpath(cdir, SKILL_DIR)))
        rows.append(check_case(cid, cdir, out))

    meta = {"protocol": PROTOCOL_VERSION,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "python": platform.python_version(), "platform": platform.platform(),
            "skill_dir": SKILL_DIR, "seconds": round(time.time() - started, 2)}
    payload = {"protocol": PROTOCOL_VERSION, "generated_at": meta["generated_at"],
               "meta": meta, "rows": rows,
               "summary": {"cases": len(rows),
                           "in_band": sum(1 for r in rows if r.get("in_band")),
                           "missing_result": sum(1 for r in rows if not r.get("result_present")),
                           "seconds": meta["seconds"]}}
    json_path = os.path.abspath(args.json or os.path.join(out, "case-set-report.json"))
    with io.open(json_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    if args.emit_md:
        with io.open(os.path.abspath(args.emit_md), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(render_md(rows, meta))

    if not args.quiet:
        print("=" * 74)
        for r in rows:
            print("%-24s exit=%-3s status=%-10s slides=%-4s evidence=%-4s in_band=%s"
                  % (r["case_id"], r.get("run_exit"), r.get("status"), r.get("slides"),
                     r.get("evidence_entries"), r.get("in_band")))
        print("-" * 74)
        print("summary: %s" % json.dumps(payload["summary"], ensure_ascii=False))
        print("report : %s" % json_path)
        if args.emit_md:
            print("table  : %s" % os.path.abspath(args.emit_md))
        print("=" * 74)

    if payload["summary"]["missing_result"] == len(rows):
        return 2
    return 0 if payload["summary"]["in_band"] == len(rows) else 1


if __name__ == "__main__":
    sys.exit(main())
