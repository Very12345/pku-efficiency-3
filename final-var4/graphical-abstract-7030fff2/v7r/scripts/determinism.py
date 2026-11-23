#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""determinism.py -- 字节级可复现性证明：同输入连跑 N 次，逐个产物比对 sha256。

Part of the "graphical-abstract" Skill (graphical-abstract-7030fff2, efficiency-3, axis v7).

**为什么需要这个脚本**：`references/OUTPUT_CONTRACT.md` 与 SKILL.md 都声称
"同输入重跑结构一致"，而 `audit.determinism_probe.spec_sha16` 只是**图面规格**的
一个 16 位指纹 —— 它证明不了产物是否逐字节相同，也证明不了"换个 cwd / 换个
PYTHONHASHSEED / 换个进程"之后还一样。本脚本把这件事做成**可执行判据**：

  * **跨进程**：每次运行都是独立 `python -B <sandbox>/scripts/main.py …` 子进程；
  * **跨 cwd**：每次运行使用不同的工作目录（技能沙箱 / 空临时目录 / 案例目录）；
  * **跨 PYTHONHASHSEED**：显式设置不同的哈希种子（dict/set 迭代顺序的经典不确定性来源）；
  * **全产物 sha256**：`result.json / spec.json / content.json / audit.json /
    render_log.json / *.svg / *.png / *.pdf`，一个不落；
  * **诚实分离"故意不稳定"的字段**：`generated_utc`、`change_records[].ts` 是**时间戳**，
    PDF 的 `/CreationDate` 也是 —— 这些必须被点名并给出稳定化办法，而不是假装全等。

三层可复现等级（本脚本实测并写进报告）：

  | 等级 | 判据 | 说明 |
  |-|-|-|
  | `L0 byte`        | 每个文件 sha256 全等 | 最强；时间戳类字段会破坏它 |
  | `L1 canonical`   | 掩掉**已声明**的易变字段后全等 | 默认判据（`--fail-on normalized`） |
  | `L2 structural`  | `result.json` 的语义字段（去掉时间戳/路径）逐项相等 | 与 L1 同步计算 |

用法（cwd 任意；`$SKILL_DIR` = 本包根）：

    # 默认：3 次，三种 cwd 形态，三种 PYTHONHASHSEED，落 determinism_report.json
    python "$SKILL_DIR/scripts/determinism.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/det

    # 更严/更松：--fail-on raw（要求逐字节相同） / none（只采数据，永远 exit 0）
    python "$SKILL_DIR/scripts/determinism.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/det --runs 5 --fail-on raw

退出码语义（本脚本自身）：
    0 = 达到 `--fail-on` 指定的等级
    1 = 未达到（报告里逐文件列出哪个文件、哪一层不一致）
    2 = 用法/环境错误（--out 落在包内、案例不可读、runs 越界等）

**只读本包**：脚本从不写包内任何文件——它把 `<skill>/scripts` 复制到 `<out>/_skill/`，
所有子进程都在沙箱副本里跑（`main.py` 内部还会写 `__pycache__`，那是沙箱的事）。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(SCRIPT_DIR)
PY = sys.executable or "python"

REPORT_SCHEMA = "determinism-report/1"

# cwd 形态：skill（技能沙箱）/ tmp（空目录）/ case（案例所在目录）
CWD_KINDS = ("skill", "tmp", "case")

# 已知的、**故意**不稳定的字段/字节区（实测确认后写进报告；不是猜测）
VOLATILE_RULES = [
    {"id": "V1", "where": "result.json: generated_utc",
     "kind": "timestamp", "why": "每次运行的真实 UTC 时间，契约要求它存在",
     "stabilized_by": "掩码 ISO-8601 → <TS>（L1/L2 比较时）"},
    {"id": "V2", "where": "result.json: change_records[*].ts",
     "kind": "timestamp", "why": "变更记录的时间戳，逐次不同是正确行为",
     "stabilized_by": "掩码 ISO-8601 → <TS>"},
    {"id": "V3", "where": "*.pdf: /CreationDate, /ModDate",
     "kind": "pdf-metadata", "why": "PDF 头里的生成时间由渲染库写入",
     "stabilized_by": "掩码 D:YYYYMMDDhhmmss → D:<TS>；要彻底消除可设 SOURCE_DATE_EPOCH"},
    {"id": "V4", "where": "任意文本产物: 运行目录绝对路径",
     "kind": "path", "why": "每次运行的 --out 目录不同（这正是被测变量）",
     "stabilized_by": "掩码 <run 目录> → <RUN>（路径本身不该出现在交付物里，见 G8-路径门）"},
]

TEXT_MASKS = [
    (re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?"),
     "<TS>"),
]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_bytes(path: str) -> bytes:
    with open(path, "rb") as fh:
        return fh.read()


def _walk_files(root: str):
    """All regular files under root -> sorted relative posix paths."""
    out = []
    for base, dirs, names in os.walk(root):
        dirs.sort()
        for n in sorted(names):
            p = os.path.join(base, n)
            if os.path.isfile(p):
                out.append(os.path.relpath(p, root).replace(os.sep, "/"))
    return sorted(out)


def _mask_paths(text: str, roots) -> str:
    """Mask absolute run/skill/case roots, in raw and JSON-escaped spellings."""
    for placeholder, root in roots:
        if not root:
            continue
        for variant in {root, root.replace("\\", "/"), root.replace("/", "\\")}:
            text = text.replace(variant, placeholder)
            text = text.replace(variant.replace("\\", "\\\\"), placeholder)
    return text


def normalize_bytes(data: bytes, roots) -> tuple:
    """Return (masked_bytes, kind). kind ∈ {text, pdf, binary}."""
    if data[:5] == b"%PDF-":
        masked = re.sub(rb"/CreationDate\s*\(D:[^)]*\)", b"/CreationDate (D:<TS>)", data)
        masked = re.sub(rb"/ModDate\s*\(D:[^)]*\)", b"/ModDate (D:<TS>)", masked)
        masked = re.sub(rb"/ID\s*\[\s*<[0-9A-Fa-f]*>\s*<[0-9A-Fa-f]*>\s*\]",
                        b"/ID [<X> <X>]", masked)
        return masked, "pdf"
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return data, "binary"
    for rx, repl in TEXT_MASKS:
        text = rx.sub(repl, text)
    text = _mask_paths(text, roots)
    return text.encode("utf-8"), "text"


def json_leaves(obj, prefix=""):
    """Flatten a JSON tree into {json.path: leaf-value}."""
    out = {}
    if isinstance(obj, dict):
        for k in obj:
            out.update(json_leaves(obj[k], f"{prefix}.{k}" if prefix else str(k)))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.update(json_leaves(v, f"{prefix}[{i}]"))
    else:
        out[prefix] = obj
    return out


def _short(value, limit=90):
    text = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
    text = str(text).replace("\n", " ")
    return text if len(text) <= limit else text[:limit] + "…"


# ---------------------------------------------------------------------------
# one run
# ---------------------------------------------------------------------------
def run_once(i, case_abs, sandbox_skill, out_root, seeds, cwds, extra_argv):
    run_dir = os.path.join(out_root, "run%d" % i)
    if os.path.isdir(run_dir):          # never let a stale run pollute the comparison
        shutil.rmtree(run_dir, ignore_errors=True)
    os.makedirs(run_dir, exist_ok=True)
    cwd_kind = cwds[i % len(cwds)]
    if cwd_kind == "skill":
        cwd = os.path.dirname(sandbox_skill)          # sandbox skill root
    elif cwd_kind == "case":
        cwd = os.path.dirname(case_abs)               # next to the case file
    else:
        cwd = os.path.join(out_root, "cwd%d" % i)     # empty scratch dir
        os.makedirs(cwd, exist_ok=True)

    seed = seeds[i % len(seeds)]
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if seed == "-":
        env.pop("PYTHONHASHSEED", None)
    else:
        env["PYTHONHASHSEED"] = str(seed)

    argv = [PY, "-B", os.path.join(sandbox_skill, "main.py"),
            "--case", case_abs, "--out", run_dir] + list(extra_argv)
    t0 = time.time()
    proc = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=900)
    secs = round(time.time() - t0, 2)
    return {
        "i": i,
        "_run_dir": run_dir,
        "run_dir": "run%d" % i,                       # relative to --out (report stays path-free)
        "cwd_kind": cwd_kind,
        "cwd": {"skill": "<skill-root>", "case": "<case-dir>", "tmp": "cwd%d" % i}[cwd_kind],
        "pythonhashseed": seed,
        "argv": ["python", "-B", "<skill-sandbox>/scripts/main.py",
                 "--case", "<case>", "--out", "run%d" % i] +
                [a if os.path.isabs(a) is False else "<abs>" for a in extra_argv],
        "exit": proc.returncode,
        "seconds": secs,
        "stdout_head": (proc.stdout or "").strip().splitlines()[:3],
        "stderr_head": (proc.stderr or "").strip().splitlines()[:3],
    }


# ---------------------------------------------------------------------------
# comparison
# ---------------------------------------------------------------------------
def compare(runs, common_roots, keep=False):
    """Hash + compare every produced file across runs.

    Each run is masked with its *own* run directory first (-> <RUN>) so that
    artifacts which legitimately record their output location (render_log.json)
    do not look like real nondeterminism.
    """
    per_file = {}
    for r in runs:
        roots = [("<RUN>", r["_run_dir"])] + list(common_roots)
        r["files"] = {}
        for rel in _walk_files(r["_run_dir"]):
            data = _read_bytes(os.path.join(r["_run_dir"], rel))
            masked, kind = normalize_bytes(data, roots)
            r["files"][rel] = {
                "sha256": _sha256(data),
                "normalized_sha256": _sha256(masked),
                "kind": kind,
                "bytes": len(data),
            }
    all_rels = sorted({rel for r in runs for rel in r["files"]})
    for rel in all_rels:
        entries = [r["files"].get(rel) for r in runs]
        raw_hashes = [e["sha256"] if e else None for e in entries]
        norm_hashes = [e["normalized_sha256"] if e else None for e in entries]
        per_file[rel] = {
            "present_in_all_runs": all(e is not None for e in entries),
            "kind": next((e["kind"] for e in entries if e), None),
            "bytes": next((e["bytes"] for e in entries if e), None),
            "sha256_per_run": raw_hashes,
            "normalized_sha256_per_run": norm_hashes,
            "raw_identical": len(set(raw_hashes)) == 1 and None not in raw_hashes,
            "normalized_identical": len(set(norm_hashes)) == 1 and None not in norm_hashes,
        }
    for r in runs:                      # compact the per-run view for the report
        r["file_hashes"] = {rel: (r["files"].get(rel) or {}).get("sha256") for rel in all_rels}
        r.pop("files", None)
    return per_file


def volatile_fields(runs):
    """Diff the parsed result.json trees; classify every difference."""
    trees = []
    for r in runs:
        p = os.path.join(r["_run_dir"], "result.json")
        if not os.path.isfile(p):
            trees.append(None)
            continue
        with open(p, encoding="utf-8") as fh:
            trees.append(json_leaves(json.load(fh)))
    if any(t is None for t in trees):
        return [], ["result.json 未在所有运行中出现，无法做字段级比对"]

    all_paths = sorted({k for t in trees for k in t})
    diffs = []
    for path in all_paths:
        values = [t.get(path, "<absent>") for t in trees]
        if all(v == values[0] for v in values):
            continue
        rule = _classify(path)
        diffs.append({
            "json_path": "result.json:" + path,
            "values_per_run": [_short(v) for v in values],
            "class": rule["id"] if rule else "UNEXPLAINED",
            "why": rule["why"] if rule else "未在已声明的易变规则里：这是真实的不确定性，需修",
            "stabilized_by": rule["stabilized_by"] if rule else "—",
        })
    return diffs, []


def _classify(json_path: str):
    if json_path == "generated_utc":
        return VOLATILE_RULES[0]
    if json_path.startswith("change_records[") and json_path.endswith(".ts"):
        return VOLATILE_RULES[1]
    return None


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def _parse_args(argv=None):
    ap = argparse.ArgumentParser(
        prog="determinism",
        description="prove byte-level reproducibility of the pipeline across processes, "
                    "cwd and PYTHONHASHSEED (writes determinism_report.json)")
    ap.add_argument("--case", required=True, help="path to case.json (the fixed input)")
    ap.add_argument("--out", required=True,
                    help="workspace for the N runs + report (must be outside this package)")
    ap.add_argument("--runs", type=int, default=3, help="number of independent runs (2..8)")
    ap.add_argument("--hashseeds", default="0,1,12345",
                    help='comma list of PYTHONHASHSEED values; "-" means leave unset')
    ap.add_argument("--cwds", default="skill,tmp,case",
                    help="comma list of cwd variations (skill|tmp|case)")
    ap.add_argument("--plan", default=None, help="optional design plan -> main.py --plan")
    ap.add_argument("--task", default=None, help="optional task.md -> main.py --task")
    ap.add_argument("--material", default=None, help="optional material -> main.py --material")
    ap.add_argument("--report", default=None,
                    help="report path (default: <out>/determinism_report.json)")
    ap.add_argument("--fail-on", default="normalized", choices=["normalized", "raw", "none"],
                    help="normalized = fail when a file differs after masking declared "
                         "volatile fields; raw = demand byte identity; none = collect only")
    ap.add_argument("--keep", action="store_true", help="keep the per-run directories")
    ap.add_argument("--verbose", action="store_true", help="print per-run stdout heads")
    ap.add_argument("--json", action="store_true", help="print the whole report to stdout")
    return ap.parse_args(argv)


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass
    args = _parse_args(argv)

    case_abs = os.path.abspath(args.case)
    out_root = os.path.abspath(args.out)
    if not os.path.isfile(case_abs):
        print(json.dumps({"status": "error", "error": "case.json not found: %s" % case_abs},
                         ensure_ascii=False, indent=2))
        return 2
    if out_root == SKILL_ROOT or out_root.startswith(SKILL_ROOT + os.sep):
        print(json.dumps({"status": "error",
                          "error": "--out must be outside the skill package (it would add "
                                   "run artifacts to the deliverable): %s" % out_root},
                         ensure_ascii=False, indent=2))
        return 2
    if not (2 <= args.runs <= 8):
        print(json.dumps({"status": "error", "error": "--runs must be 2..8"},
                         ensure_ascii=False, indent=2))
        return 2

    seeds = [s.strip() for s in args.hashseeds.split(",") if s.strip()] or ["-"]
    cwds = [c.strip() for c in args.cwds.split(",") if c.strip() in CWD_KINDS] or list(CWD_KINDS)

    os.makedirs(out_root, exist_ok=True)
    sandbox_root = os.path.join(out_root, "_skill")
    if os.path.isdir(sandbox_root):
        shutil.rmtree(sandbox_root, ignore_errors=True)
    shutil.copytree(SCRIPT_DIR, os.path.join(sandbox_root, "scripts"))
    sandbox_skill = os.path.join(sandbox_root, "scripts")

    extra_argv = []
    for flag, val in (("--plan", args.plan), ("--task", args.task), ("--material", args.material)):
        if val:
            extra_argv += [flag, os.path.abspath(val)]

    roots = [("<OUT>", out_root), ("<SKILL>", SKILL_ROOT),
             ("<CASE>", os.path.dirname(case_abs))]
    if args.plan:
        roots.append(("<PLAN>", os.path.dirname(os.path.abspath(args.plan))))

    runs = []
    t0 = time.time()
    for i in range(args.runs):
        r = run_once(i, case_abs, sandbox_skill, out_root, seeds, cwds, extra_argv)
        runs.append(r)
        if args.verbose:
            print("[run%d] cwd=%s seed=%s exit=%s %.2fs"
                  % (i, r["cwd_kind"], r["pythonhashseed"], r["exit"], r["seconds"]))
            for line in r["stdout_head"]:
                print("    out| " + line[:150])

    per_file = compare(runs, roots, keep=args.keep)
    diffs, diff_notes = volatile_fields(runs)

    files_present_mismatch = [f for f, v in per_file.items() if not v["present_in_all_runs"]]
    raw_diff = sorted(f for f, v in per_file.items() if not v["raw_identical"])
    norm_diff = sorted(f for f, v in per_file.items() if not v["normalized_identical"])
    unexplained = [d for d in diffs if d["class"] == "UNEXPLAINED"]

    if not norm_diff and not files_present_mismatch and not unexplained:
        verdict = "canonical-stable" if raw_diff else "byte-stable"
    else:
        verdict = "unstable"

    spec_probe = []
    for r in runs:
        p = os.path.join(r["_run_dir"], "result.json")
        try:
            with open(p, encoding="utf-8") as fh:
                rep = json.load(fh)
            spec_probe.append(((rep.get("audit") or {}).get("determinism_probe") or {})
                              .get("spec_sha16"))
        except Exception:  # noqa: BLE001
            spec_probe.append(None)

    for r in runs:                      # never publish machine-specific paths in the report
        r.pop("_run_dir", None)

    ok = (args.fail_on == "none"
          or (args.fail_on == "raw" and not raw_diff and not files_present_mismatch
              and not unexplained)
          or (args.fail_on == "normalized" and not norm_diff
              and not files_present_mismatch and not unexplained))

    report = {
        "schema": REPORT_SCHEMA,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "skill": "graphical-abstract",
        "python": sys.version.split()[0],
        "platform": sys.platform,
        "case": {"file": os.path.basename(case_abs),
                 "case_id": _case_id(case_abs),
                 "sha256": _sha256(_read_bytes(case_abs))},
        "invocation": {
            "runs": args.runs,
            "hashseeds": seeds,
            "cwds": cwds,
            "isolated_processes": True,
            "argv": "python -B <sandbox>/scripts/main.py --case <case> --out <run-dir> " +
                    " ".join(extra_argv),
        },
        "runs": runs,
        "per_file_sha256": {f: v["sha256_per_run"] for f, v in per_file.items()},
        "per_file": per_file,
        "identical": {
            "raw": not raw_diff and not files_present_mismatch,
            "normalized": not norm_diff and not files_present_mismatch,
            "per_file_raw": {f: v["raw_identical"] for f, v in per_file.items()},
            "per_file_normalized": {f: v["normalized_identical"] for f, v in per_file.items()},
            "files_only_in_some_runs": files_present_mismatch,
        },
        "volatile_fields": diffs,
        "volatile_rules": VOLATILE_RULES,
        "unexplained_differences": unexplained,
        "structure_probe": {"spec_sha16_per_run": spec_probe,
                            "all_equal": len(set(spec_probe)) == 1 and None not in spec_probe},
        "normalization": {
            "rules": ["ISO-8601 时间戳 → <TS>",
                      "运行目录 / 技能目录 / 案例目录（含 JSON 转义写法）→ <RUN>/<SKILL>/<CASE>",
                      "PDF /CreationDate|/ModDate → D:<TS>，/ID → [<X> <X>]"],
            "applied_to": "all produced files (text masking) + PDF byte masking",
        },
        "verdict": verdict,
        "fail_on": args.fail_on,
        "checks": {
            "files_compared": len(per_file),
            "raw_identical_files": len(per_file) - len(raw_diff),
            "normalized_identical_files": len(per_file) - len(norm_diff),
            "raw_diff_files": raw_diff,
            "normalized_diff_files": norm_diff,
            "declared_volatile_fields": len(diffs),
            "unexplained_differences": len(unexplained),
            "seconds_total": round(time.time() - t0, 2),
        },
        "notes": diff_notes + [
            "本报告只声明实测到的东西：raw 层不一致的文件一定是时间戳/路径类字段造成的，"
            "逐条列在 volatile_fields 里；normalized 层若不一致即为真实不确定性（verdict=unstable）。",
            "运行目录在比对时被掩码，但交付物本身**不应**含任何本机绝对路径 —— 这一条由 "
            "validate_pkg.py 与 SKILL.md 的自查清单独立把关。",
        ],
    }

    report_path = os.path.abspath(args.report) if args.report \
        else os.path.join(out_root, "determinism_report.json")
    with open(report_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    if not args.keep:
        for _i in range(args.runs):
            shutil.rmtree(os.path.join(out_root, "run%d" % _i), ignore_errors=True)
        shutil.rmtree(os.path.join(out_root, "_skill"), ignore_errors=True)

    print("verdict=%s  runs=%d  files=%d  raw-identical=%d  normalized-identical=%d  "
          "declared-volatile-fields=%d  unexplained=%d"
          % (verdict, args.runs, len(per_file), len(per_file) - len(raw_diff),
             len(per_file) - len(norm_diff), len(diffs), len(unexplained)))
    print("report: %s" % report_path)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if ok else 1


def _case_id(case_path: str) -> str:
    try:
        with open(case_path, encoding="utf-8") as fh:
            obj = json.load(fh)
        return str(obj.get("case_id") or os.path.basename(case_path))
    except Exception:  # noqa: BLE001
        return os.path.basename(case_path)


if __name__ == "__main__":
    sys.exit(main())
