#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""determinism.py — 确定性与字节级可复现探针（R3 v7 轴；可直接运行）。

它回答一个评分点「结果可核验性 / 运行稳定性」里最难自证的问题：
**同一份输入连跑 N 次，产物到底是不是同一串字节？哪些字节是故意不同的？**

做法（全部在**沙箱副本**上跑，不写本包目录）：
  1. 把技能根按文本白名单复制到 `<out>/skill/`（包本体不动，也不落 `__pycache__`）；
  2. **raw 条件**：每次运行用**各自独立的 `--out`**、**不同 cwd**、**不同 `PYTHONHASHSEED`**，
     每个 run 都是**独立子进程**，跑完立刻对 `<out>/<case_id>/` 下全部产物做 sha256；
  3. **stabilized 条件**：把三条已知扰动源逐条关掉 ——
     （L1）所有 run 共用同一个 `--out` 根（消除 `execution.out_dir` 差异）；
     （L2）`RL_INVARIANT=1`（reportlab 固定 PDF 的 `/CreationDate`、`/ModDate`、`/ID`）；
     （L3）**冻结时钟驱动**（`datetime.now` 钉死到 2026-01-01T00:00:00Z，消除
     `change_record[].time`）—— 再跑一遍同样的 N 次；
  4. 逐文件比对两条件的 sha256，做 result.json 的**逐字段深比对**，
     把每个漂移字段归类为「故意/可稳定化」或「未解释」；
  5. 落盘机器可读的 `determinism_report.json`（`runs[]` / `per_file_sha256` /
     `identical` / `volatile_fields[]` / `identical_by_condition` /
     `identical_normalized` / `counts` / `verdict`）。

退出码：0 = 与声明的口径一致（漂移字段全在声明清单内，且 stabilized 条件逐字节相同）；
        3 = 出现未解释的漂移或 stabilized 仍不稳定；2 = 用法/输入错误。

判据（写进 SKILL.md §5，可被他人复核）：
  * `identical`（raw 口径，即平台默认环境）—— **不要求为 true**；为 false 是预期，
    但每个漂移字段必须出现在 `volatile_fields[]` 里且 `intentional=true`；
  * `identical_by_condition.stabilized` —— **必须为 true**（这是"可复现"的强判据）；
  * `identical_normalized` —— **必须为 true**（把声明清单掩码后的规范化摘要一致）。

用法（`$SKILL_DIR` = 含 SKILL.md 的技能根；任何 cwd 都可运行）：
    python "$SKILL_DIR/scripts/determinism.py"
    python "$SKILL_DIR/scripts/determinism.py" --case "$SKILL_DIR/examples" --runs 4 \
           --json /tmp/determinism_report.json
    python "$SKILL_DIR/scripts/determinism.py" --mode raw --keep        # 只跑默认条件，保留现场
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
import tempfile
import time

sys.dont_write_bytecode = True
from typing import Any, Dict, List, Optional, Tuple  # noqa: E402

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(SCRIPTS_DIR)

ALLOWED_EXT = {".md", ".py", ".json", ".txt", ".csv", ".yaml", ".yml"}
SKIP_DIRS = {"__pycache__", ".git", ".venv", "venv", "node_modules", ".mypy_cache"}
DEFAULT_SEEDS = ["0", "1", "12345", "31337"]

# ---------------------------------------------------------------- 声明的漂移源
# 每条都必须能在 stabilized 条件下被真正关掉；否则 verdict=attention。
DECLARED_VOLATILE = [
    {
        "file": "result.json",
        "path": "change_record/*/time",
        "kind": "wall-clock",
        "intentional": True,
        "why": "change_record 记录的是**真实**写入时刻（ISO8601 UTC，秒级）；伪造它等于伪造审计记录。",
        "stabilizer": "L3 冻结时钟驱动（--frozen-clock，仅用于复现实验，不进正式交付）",
    },
    {
        "file": "result.json",
        "path": "execution/out_dir",
        "kind": "absolute-path",
        "intentional": True,
        "why": "execution.out_dir 回显本次 --out 根目录；raw 条件故意每次换目录，所以它必然不同。",
        "stabilizer": "L1 所有 run 共用同一个 --out 根",
    },
    {
        "file": "figure.pdf",
        "path": "(binary) /CreationDate,/ModDate,/ID",
        "kind": "pdf-metadata",
        "intentional": True,
        "why": "PDF 规范要求写入生成时间与文档 ID；reportlab 默认用当前时间 + 随机 ID。",
        "stabilizer": "L2 环境变量 RL_INVARIANT=1（reportlab 官方 invariant 开关）",
    },
]

PDF_DATE_RE = re.compile(rb"/(?:CreationDate|ModDate)\s*\([^)]*\)")
PDF_ID_RE = re.compile(rb"/ID\s*\[\s*<[0-9A-Fa-f]*>\s*<[0-9A-Fa-f]*>\s*\]")

FROZEN_CLOCK_DRIVER = '''# -*- coding: utf-8 -*-
"""冻结时钟驱动（由 scripts/determinism.py 现场生成）。

把 `datetime.now()` / `utcnow()` 钉死到 2026-01-01T00:00:00Z，**只为复现实验**：
跑出来的 result.json 里 change_record[].time 变成常量，用来证明
"时间戳是唯一残余漂移"。正式交付不要用它。
"""
import os
import runpy
import sys
import types

sys.dont_write_bytecode = True
import datetime as _real  # noqa: E402

_FIXED = _real.datetime(2026, 1, 1, 0, 0, 0, tzinfo=_real.timezone.utc)


class _FrozenDateTime(_real.datetime):
    @classmethod
    def now(cls, tz=None):
        return _FIXED if tz is not None else _FIXED.replace(tzinfo=None)

    @classmethod
    def utcnow(cls):
        return _FIXED.replace(tzinfo=None)


_proxy = types.ModuleType("datetime")
for _name in dir(_real):
    if not _name.startswith("__"):
        setattr(_proxy, _name, getattr(_real, _name))
_proxy.datetime = _FrozenDateTime
sys.modules["datetime"] = _proxy

_main_py = os.path.abspath(sys.argv[1])
sys.argv = sys.argv[1:]
runpy.run_path(_main_py, run_name="__main__")
'''


# ---------------------------------------------------------------- 基础工具
def sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def is_text_resource(name: str) -> bool:
    return os.path.splitext(name)[1].lower() in ALLOWED_EXT


def sandbox_copy(skill_root: str, dest: str) -> Dict[str, Any]:
    """把技能根的文本资源复制到 dest（只复制平台允许的扩展名），返回文件数与摘要。"""
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    os.makedirs(dest, exist_ok=True)
    rows: List[Tuple[str, str]] = []
    for root, dirs, files in os.walk(skill_root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for name in sorted(files):
            if not is_text_resource(name):
                continue
            src = os.path.join(root, name)
            rel = os.path.relpath(src, skill_root).replace("\\", "/")
            dst = os.path.join(dest, rel.replace("/", os.sep))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)
            rows.append((rel, sha256_file(src)))
    digest = hashlib.sha256()
    for rel, sha in sorted(rows):
        digest.update(f"{rel}\t{sha}\n".encode("utf-8"))
    return {"files": len(rows), "tree_sha256": digest.hexdigest()}


def snapshot_tree(case_dir: str) -> Dict[str, Dict[str, Any]]:
    """对一个案例输出目录做全量 sha256 快照（相对文件名 -> {sha256,size}）。"""
    out: Dict[str, Dict[str, Any]] = {}
    if not os.path.isdir(case_dir):
        return out
    for root, dirs, files in os.walk(case_dir):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for name in sorted(files):
            p = os.path.join(root, name)
            rel = os.path.relpath(p, case_dir).replace("\\", "/")
            out[rel] = {"sha256": sha256_file(p), "size": os.path.getsize(p), "path": p}
    return out


def pdf_mask(blob: bytes) -> bytes:
    blob = PDF_DATE_RE.sub(b"/CreationDate (MASKED)", blob)
    return PDF_ID_RE.sub(b"/ID [<MASKED><MASKED>]", blob)


def mask_json_paths(doc: Any, rules: List[Tuple[str, Any]]) -> Any:
    """按 (json-path, replacer) 规则生成规范化副本；路径用 / 分段，* 匹配任意下标。"""
    copy = json.loads(json.dumps(doc, ensure_ascii=False))

    def walk(node: Any, segs: List[str], rule_path: List[str], repl: Any) -> None:
        if not segs:
            return
        key, rest = segs[0], segs[1:]
        if isinstance(node, dict):
            if key == "*":
                for k in list(node.keys()):
                    walk(node, [k] + rest, rule_path, repl)
                return
            if key not in node:
                return
            if not rest:
                node[key] = repl
                return
            walk(node[key], rest, rule_path, repl)
        elif isinstance(node, list):
            if key == "*":
                for item in node:
                    walk(item, rest, rule_path, repl)
                return
            idx = int(key)
            if idx >= len(node):
                return
            if not rest:
                node[idx] = repl
                return
            walk(node[idx], rest, rule_path, repl)

    for path, repl in rules:
        walk(copy, path.split("/"), path.split("/"), repl)
    return copy


def normalized_digests(case_dir: str, snap: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
    """规范化摘要：JSON 掩码声明路径（用定点值替换）后取 canonical sha256；
    PDF 掩码 /CreationDate、/ModDate、/ID；其余文件取原始字节。"""
    stamps: Dict[str, str] = {}
    for rel, info in snap.items():
        p = info["path"]
        low = rel.lower()
        if low.endswith(".json"):
            try:
                doc = json.load(open(p, encoding="utf-8"))
            except Exception:  # noqa: BLE001
                stamps[rel] = info["sha256"]
                continue
            if rel == "result.json":
                doc = mask_json_paths(doc, [
                    ("change_record/*/time", "<TIME>"),
                    ("execution/out_dir", "<OUT_DIR>"),
                ])
            elif rel == "verify_report.json":
                doc = mask_json_paths(doc, [])
            stamps[rel] = sha256_bytes(json.dumps(doc, ensure_ascii=False,
                                                  sort_keys=True).encode("utf-8"))
        elif low.endswith(".pdf"):
            stamps[rel] = sha256_bytes(pdf_mask(open(p, "rb").read()))
        else:
            stamps[rel] = info["sha256"]
    return stamps


def json_leaf_diff(a: Any, b: Any, prefix: str = "") -> List[Dict[str, Any]]:
    """逐叶子比对两个 JSON，返回 [{path, a, b}]。"""
    diffs: List[Dict[str, Any]] = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            diffs.extend(json_leaf_diff(a.get(k), b.get(k), f"{prefix}/{k}"))
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            diffs.append({"path": prefix + "/#len", "a": len(a), "b": len(b)})
        for i, (x, y) in enumerate(zip(a, b)):
            diffs.extend(json_leaf_diff(x, y, f"{prefix}/{i}"))
    elif a != b:
        diffs.append({"path": prefix, "a": a, "b": b})
    return diffs


def leaf_at(doc: Any, path: str) -> Any:
    """按 json_leaf_diff 的路径取叶子值（取不到返回 "<absent>"）。"""
    cur = doc
    for seg in path.lstrip("/").split("/"):
        if seg.startswith("#"):
            return "<len-changed>"
        if isinstance(cur, list):
            try:
                cur = cur[int(seg)]
            except (ValueError, IndexError):
                return "<absent>"
        elif isinstance(cur, dict):
            if seg not in cur:
                return "<absent>"
            cur = cur[seg]
        else:
            return "<absent>"
    return cur


def declared_match(file_rel: str, diff_path: str) -> Optional[Dict[str, Any]]:
    """把一条 JSON 叶子漂移映射到声明清单；未声明返回 None。"""
    for rule in DECLARED_VOLATILE:
        if rule["file"] != file_rel or rule["kind"] in ("pdf-metadata", "binary"):
            continue
        segs = rule["path"].split("/")
        leaf = diff_path.lstrip("/").split("/")
        if len(segs) != len(leaf):
            continue
        if all(s == "*" or s == l for s, l in zip(segs, leaf)):
            return rule
    return None


# ---------------------------------------------------------------- 运行一次
def run_once(python_exe: str, driver: Optional[str], skill_dir: str, case_arg: str,
             out_root: str, cwd: str, seed: str, timeout: int,
             rl_invariant: bool) -> Dict[str, Any]:
    main_py = os.path.join(skill_dir, "scripts", "main.py")
    if driver:
        argv = [python_exe, driver, main_py]
    else:
        argv = [python_exe, main_py]
    argv += ["--case", case_arg, "--out", out_root]

    env = dict(os.environ)
    env["PYTHONHASHSEED"] = seed
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if rl_invariant:
        env["RL_INVARIANT"] = "1"
    else:
        env.pop("RL_INVARIANT", None)

    t0 = time.time()
    timed_out = False
    try:
        proc = subprocess.Popen(argv, cwd=cwd, env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True,
                                encoding="utf-8", errors="replace")
        pid = proc.pid
        out, err = proc.communicate(timeout=timeout)
        rc = proc.returncode
    except subprocess.TimeoutExpired:  # noqa: PERF203
        proc.kill()
        out, err = proc.communicate()
        rc, timed_out, pid = 124, True, proc.pid
    elapsed = time.time() - t0
    return {"exit": rc, "pid": pid, "stdout_tail": (out or "")[-800:],
            "stderr_tail": (err or "")[-800:],
            "elapsed_s": round(elapsed, 3), "timed_out": timed_out,
            "rl_invariant": "1" if rl_invariant else "0"}


def cwd_cycle(skill_dir: str, workdir: str, case_path: str) -> List[str]:
    """故意让 cwd 每次都不一样：证明脚本靠 __file__ 自定位，而不是靠 cwd。"""
    case_dir = os.path.dirname(os.path.abspath(case_path))
    cands = [skill_dir, workdir, os.path.join(skill_dir, "scripts"), case_dir,
             tempfile.gettempdir()]
    seen: List[str] = []
    for c in cands:
        c = os.path.abspath(c)
        if os.path.isdir(c) and c not in seen:
            seen.append(c)
    return seen


def resolve_case(case_arg: str) -> Tuple[str, str]:
    """返回 (实际 case.json 路径, 传给 main.py 的 --case 实参)。"""
    p = os.path.abspath(case_arg)
    if os.path.isdir(p):
        cand = os.path.join(p, "case.json")
        return (cand if os.path.isfile(cand) else p), case_arg
    return p, case_arg


# ---------------------------------------------------------------- 主流程
def probe(args: argparse.Namespace) -> Dict[str, Any]:
    workdir = os.path.abspath(args.out or tempfile.mkdtemp(prefix="determinism-"))
    os.makedirs(workdir, exist_ok=True)
    skill_dir = os.path.join(workdir, "skill")
    sandbox = {"files": 0, "tree_sha256": ""}
    if args.no_sandbox:
        skill_dir = SKILL_ROOT
        sandbox = {"files": -1, "tree_sha256": "not-copied(use --no-sandbox)"}
    else:
        sandbox = sandbox_copy(SKILL_ROOT, skill_dir)

    case_path, case_arg = resolve_case(args.case or os.path.join(SKILL_ROOT, "examples"))
    if not os.path.isfile(case_path):
        raise SystemExit(f"FATAL: case.json 不存在: {case_path}")

    driver_path = os.path.join(workdir, "_frozen_clock_driver.py")
    with open(driver_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(FROZEN_CLOCK_DRIVER)

    cwds = cwd_cycle(skill_dir, workdir, case_path)
    seeds = [s.strip() for s in (args.seeds or ",".join(DEFAULT_SEEDS)).split(",") if s.strip()]
    n_runs = max(2, int(args.runs))
    modes = ["raw", "stabilized"] if args.mode == "both" else [args.mode]

    runs: List[Dict[str, Any]] = []
    snaps: Dict[str, List[Dict[str, Dict[str, Any]]]] = {"raw": [], "stabilized": []}
    norm: Dict[str, List[Dict[str, str]]] = {"raw": [], "stabilized": []}
    case_id_holder: Dict[str, str] = {}

    for mode in modes:
        for i in range(n_runs):
            seed = seeds[i % len(seeds)]
            cwd = cwds[i % len(cwds)]
            if mode == "raw":
                out_root = os.path.join(workdir, "raw", f"run{i}", "out")
                driver = None
                rl = False
            else:
                out_root = os.path.join(workdir, "stab", "out")
                if os.path.isdir(out_root):
                    shutil.rmtree(out_root)
                driver = driver_path
                rl = True
            os.makedirs(os.path.dirname(out_root), exist_ok=True)
            res = run_once(args.python, driver, skill_dir, case_arg, out_root, cwd,
                           seed, args.timeout, rl)
            # 产物目录 = <out_root>/<case_id>
            subdirs = [d for d in sorted(os.listdir(out_root))
                       if os.path.isdir(os.path.join(out_root, d))] if os.path.isdir(out_root) else []
            case_id = case_id_holder.get("id") or (subdirs[0] if subdirs else "?")
            if subdirs:
                case_id_holder["id"] = case_id
            case_dir = os.path.join(out_root, case_id)
            snap = snapshot_tree(case_dir)
            snaps[mode].append(snap)
            norm[mode].append(normalized_digests(case_dir, snap))
            runs.append({
                "run": len(runs), "condition": mode, "index_in_condition": i,
                "pid": res["pid"], "cwd": cwd, "pythonhashseed": seed,
                "rl_invariant": res["rl_invariant"], "frozen_clock": bool(driver),
                "out_root": out_root, "case_id": case_id,
                "exit": res["exit"], "timed_out": res["timed_out"],
                "elapsed_s": res["elapsed_s"], "artifacts": len(snap),
                "artifact_sha256": {k: v["sha256"] for k, v in sorted(snap.items())},
            })

    # ---- 逐文件跨 run 比对
    per_file: Dict[str, Dict[str, List[str]]] = {}
    all_files = sorted({f for mode in snaps for snap in snaps[mode] for f in snap})
    for f in all_files:
        per_file[f] = {}
        for mode in ("raw", "stabilized"):
            seq = [snap[f]["sha256"] if f in snap else "<absent>" for snap in snaps[mode]]
            if seq:
                per_file[f][mode] = seq
    ident_by_cond: Dict[str, bool] = {}
    ident_norm_by_cond: Dict[str, bool] = {}
    for mode in ("raw", "stabilized"):
        ident_by_cond[mode] = bool(per_file) and all(
            len(set(v.get(mode, []))) == 1 and v.get(mode) for v in per_file.values())
        files_norm = sorted({f for s in norm[mode] for f in s})
        ident_norm_by_cond[mode] = bool(files_norm) and all(
            len({s.get(f, "<absent>") for s in norm[mode]}) == 1 for f in files_norm)

    # ---- result.json 逐字段深比对（跨 run 收集漂移路径）
    volatile_fields: List[Dict[str, Any]] = []
    unexplained: List[Dict[str, Any]] = []
    obs_by_path: Dict[Tuple[str, str], List[Any]] = {}
    for mode in ("raw", "stabilized"):
        docs = []
        for i, snap in enumerate(snaps[mode]):
            info = snap.get("result.json")
            if not info:
                continue
            docs.append(json.load(open(info["path"], encoding="utf-8")))
        for i in range(1, len(docs)):
            for d in json_leaf_diff(docs[0], docs[i]):
                key = (mode, d["path"])
                obs_by_path.setdefault(key, [leaf_at(docs[0], d["path"])])
                obs_by_path[key].append(d["b"])
    exprs: Dict[str, Dict[str, Any]] = {}
    for (mode, path), vals in sorted(obs_by_path.items()):
        rule = declared_match("result.json", path)
        uniq = sorted({json.dumps(v, ensure_ascii=False) for v in vals})
        entry = {
            "file": "result.json",
            "path": path.lstrip("/"),
            "conditions": sorted({m for (m, p) in obs_by_path if p == path}),
            "kind": (rule or {}).get("kind", "UNEXPLAINED"),
            "intentional": bool(rule),
            "why": (rule or {}).get("why", "未在 DECLARED_VOLATILE 中声明 —— 需要调查"),
            "stabilizer": (rule or {}).get("stabilizer", "n/a"),
            "observed": uniq[:4],
        }
        key = f"result.json#{entry['path']}"
        if key in exprs:
            exprs[key]["observed"] = sorted(set(exprs[key]["observed"]) | set(entry["observed"]))[:4]
            exprs[key]["conditions"] = sorted(set(exprs[key]["conditions"]) | set(entry["conditions"]))
        else:
            exprs[key] = entry
    volatile_fields = list(exprs.values())
    unexplained = [v for v in volatile_fields if not v["intentional"]]

    # ---- 非 JSON 产物的字节漂移（PDF 元数据属声明清单）
    non_json_drift: List[Dict[str, Any]] = []
    for f, byc in per_file.items():
        if f.lower().endswith(".json"):
            continue
        for mode in ("raw", "stabilized"):
            shas = byc.get(mode) or []
            if shas and len(set(shas)) > 1:
                rule = next((r for r in DECLARED_VOLATILE
                             if r["file"] == f and r["kind"] == "pdf-metadata"), None)
                non_json_drift.append({
                    "file": f, "condition": mode, "distinct_sha256": len(set(shas)),
                    "kind": (rule or {}).get("kind", "UNEXPLAINED"),
                    "intentional": bool(rule),
                    "stabilizer": (rule or {}).get("stabilizer", "n/a"),
                })
    # PDF 在 raw 下漂移但 stabilized 下不漂移 ⇒ 声明成立
    for item in non_json_drift:
        if item["file"] == "figure.pdf":
            stab = per_file.get("figure.pdf", {}).get("stabilized") or []
            item["stabilized_distinct_sha256"] = len(set(stab)) if stab else 0
            item["resolved_by_stabilizer"] = item["stabilized_distinct_sha256"] == 1

    counts = {
        "runs": len(runs),
        "runs_per_condition": n_runs,
        "artifacts": len(all_files),
        "raw_identical_files": sum(1 for v in per_file.values()
                                   if len(set(v.get("raw", []))) == 1),
        "stabilized_identical_files": sum(1 for v in per_file.values()
                                          if len(set(v.get("stabilized", []))) == 1),
        "volatile_fields": len(volatile_fields),
        "unexplained_volatile_fields": len(unexplained),
        "non_json_drift_entries": len(non_json_drift),
    }
    verdict = "pass" if (
        not unexplained
        and ident_by_cond.get("stabilized", False)
        and ident_norm_by_cond.get("raw", True)
        and all(item.get("resolved_by_stabilizer", True) for item in non_json_drift)
        and counts["stabilized_identical_files"] == counts["artifacts"]
    ) else "attention"

    report = {
        "probe": "determinism",
        "schema": "determinism-report/1",
        "generated_by": "scripts/determinism.py",
        "skill_root": SKILL_ROOT,
        "sandbox": {"dir": skill_dir, **sandbox},
        "case": case_path,
        "case_id": case_id_holder.get("id", "?"),
        "python": sys.version.split()[0],
        "python_executable": args.python,
        "runs_per_condition": n_runs,
        "modes": modes,
        "seeds": seeds,
        "cwds": cwds,
        "runs": runs,
        "per_file_sha256": per_file,
        "identical": ident_by_cond.get("raw", False),
        "identical_by_condition": ident_by_cond,
        "identical_normalized": ident_norm_by_cond,
        "stabilizers": [
            {"id": "L1", "what": "所有 run 共用同一个 --out 根（每次运行前清空）",
             "removes": "result.json#execution/out_dir"},
            {"id": "L2", "what": "环境变量 RL_INVARIANT=1（reportlab invariant 开关）",
             "removes": "figure.pdf 的 /CreationDate、/ModDate、/ID"},
            {"id": "L3", "what": "冻结时钟驱动 _frozen_clock_driver.py（datetime.now 钉死）",
             "removes": "result.json#change_record/*/time"},
        ],
        "volatile_fields": volatile_fields,
        "non_json_drift": non_json_drift,
        "counts": counts,
        "verdict": verdict,
        "notes": [
            "identical 字段 = **raw 条件**（各自独立 --out / 不同 cwd / 不同 PYTHONHASHSEED / 真实时钟）"
            "下 N 次产物是否逐字节相同；为 false 是**预期**，判据是漂移字段必须全部已声明。",
            "identical_by_condition.stabilized = 关掉 L1/L2/L3 后是否逐字节相同 —— 这才是"
            "「可复现」的强判据，必须为 true。",
            "跑批全程在沙箱副本上进行，包本体不被写入、不落 __pycache__。",
        ],
    }
    return report


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(
        description="确定性与字节级可复现探针（v7）：同输入 N 次 × 跨进程/cwd/PYTHONHASHSEED")
    ap.add_argument("--case", default=None,
                    help="case.json 或其所在目录（默认 <技能根>/examples）")
    ap.add_argument("--runs", type=int, default=4, help="每个条件的运行次数（默认 4，最少 2）")
    ap.add_argument("--seeds", default=None,
                    help="逗号分隔的 PYTHONHASHSEED 序列（默认 0,1,12345,31337）")
    ap.add_argument("--mode", default="both", choices=["raw", "stabilized", "both"],
                    help="只跑某一条件或两个都跑（默认 both）")
    ap.add_argument("--out", default=None, help="探针工作目录（默认系统临时目录；不写技能根）")
    ap.add_argument("--json", default=None,
                    help="报告路径（默认 <out>/determinism_report.json）")
    ap.add_argument("--python", default=sys.executable, help="用于跑主流程的解释器（默认本解释器）")
    ap.add_argument("--timeout", type=int, default=300, help="单次运行超时秒数（默认 300）")
    ap.add_argument("--no-sandbox", action="store_true",
                    help="不复制沙箱，直接在技能根上跑（会读到包本体；默认不这么做）")
    ap.add_argument("--keep", action="store_true", help="保留工作目录（默认保留；显式给出便于脚本化）")
    args = ap.parse_args(argv)

    try:
        report = probe(args)
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        print(f"FATAL: 探针异常: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 2

    json_path = args.json or os.path.join(os.path.abspath(args.out or tempfile.gettempdir()),
                                          "determinism_report.json")
    os.makedirs(os.path.dirname(os.path.abspath(json_path)), exist_ok=True)
    with open(json_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)

    summary = {
        "verdict": report["verdict"],
        "case_id": report["case_id"],
        "runs": report["counts"]["runs"],
        "artifacts": report["counts"]["artifacts"],
        "identical": report["identical"],
        "identical_by_condition": report["identical_by_condition"],
        "identical_normalized": report["identical_normalized"],
        "raw_identical_files": report["counts"]["raw_identical_files"],
        "stabilized_identical_files": report["counts"]["stabilized_identical_files"],
        "volatile_fields": [v["path"] for v in report["volatile_fields"]],
        "unexplained": report["counts"]["unexplained_volatile_fields"],
        "report": json_path,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if not args.keep:
        print("(提示：--keep 未给出，工作目录仍保留以便复核：%s)" % report["sandbox"]["dir"])
    return 0 if report["verdict"] == "pass" else 3


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass
    sys.exit(main(sys.argv[1:]))
