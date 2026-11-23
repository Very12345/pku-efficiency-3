#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""determinism.py — 字节级可复现性实测台（v7 轴）

本脚本回答一个**只能用数字回答**的问题：

    「同一份 case.json、同一套参数，把 main.py 连跑 N 次，
      产出的每一个文件是不是逐字节一样？不一样的那些，差在哪个字段？」

做法（三个变量一起动，缺一不可）
--------------------------------
每一次重复都是一次**独立进程**（subprocess，不是同进程内复用），并且：

* **cwd 轮转**：run 目录 / 系统临时目录 / 案例目录 —— 证明脚本自定位不依赖 cwd；
* **PYTHONHASHSEED 轮转**（`--seeds`）：证明产物不依赖 dict/set 的哈希顺序；
* **输出目录**：`--mode isolated` 每次换一个绝对路径（连"路径泄漏进产物"一起测）；
  `--mode inplace` 每次写同一个绝对路径（把路径变量排除，只看剩余不确定性）。

然后对**输出目录里的全部文件**（不是只对 result.json 里登记的那几个）做
sha256 比对，并做两级判定：

1. `identical` —— 原始字节是否全同；
2. `normalized_identical` —— 施加**归一化规则 N1–N4** 之后是否全同。

归一化规则（每条都在 references/DETERMINISM.md 有实测依据）
----------------------------------------------------------
* **N1** JSON 中键名为 `ts` 的值 → `"<TS>"`（`chartkit.now_ts()` 写入的本地时间戳）
* **N2** JSON / SVG / TXT 字符串里出现的**本次运行根路径** → `"<RUNROOT>"`
  （`figcheck_report.json` 与 `mapcheck_report.json` 的 `dir` 字段写的是输出目录绝对路径）
* **N3** JSON 中 `artifacts_sha256.<file>` 的值 → 该文件**归一化之后**的 sha256
  （自引用哈希：它记的是别的产物在第 5 步的字节，PDF 日期一变它就跟着变）
* **N4** PDF 里的 `/CreationDate (...)` 与 `/ModDate (...)` → `(D:0)`
  （Pillow 写 PDF 时嵌的当前时间；实测这是 PDF 唯一的差异来源）

确定性阶梯（退出码，与包内既有脚本口径一致：1 = 用法/运行错误，2/3 = 有差异）
--------------------------------------------------------------------------
    0   全部运行都产出可解析 result.json，且**全部产物逐字节相同**
    2   字节级不同，但归一化后全部相同 => 不确定性 100% 被 N1–N4 解释
    3   归一化后仍有差异 ⇒ 存在**未解释**的不确定性（报告给首个差异文件与字节偏移）
    1   用法错误，或至少一次运行没能产出可解析的 result.json（无法判定）

附加证据（同样是实测，不是声明）
------------------------------
* `abs_path_leaks`：产物文本里出现的绝对路径清单 —— 它**不影响同机重跑**，
  但会让"换一台机器/换一个目录"的字节一致性失效，属于必须点名的可移植性缺口。

用法
----
    python "$SKILL_DIR/scripts/determinism.py" --case /input/case.json
    python "$SKILL_DIR/scripts/determinism.py" --case /input/case.json --runs 3 --mode inplace
    python "$SKILL_DIR/scripts/determinism.py" --case /input/case.json --out /tmp/det.json --json

    --case      案例 JSON（必填）
    --runs      重复次数（默认 3，最少 2）
    --seeds     PYTHONHASHSEED 轮转表（默认 "0,1,12345"）
    --mode      isolated（默认，各自独立输出目录）| inplace（同一输出目录）
    --workroot  包外工作目录（默认系统临时目录）
    --out       报告路径（默认 <workroot>/determinism_report.json）
    --main      main.py 路径（默认本脚本同目录的 main.py；可指向另一个包做对照）
    --json      报告同时打印到 stdout
    --keep      保留各次运行的输出目录（默认只保留报告与归一化副本的哈希）
    --timeout   单次运行超时秒数（默认 300）

报告是**可移植**的：所有本机绝对路径在写入前被替换为
`<WORKSPACE>` / `<CASEDIR>` / `<SKILL_DIR>` / `<TMP>` 占位符（`--abs-policy keep` 可关闭）。
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

HERE = os.path.dirname(os.path.abspath(__file__))
PKG_ROOT = os.path.dirname(HERE)
DEFAULT_MAIN = os.path.join(HERE, "main.py")

# ---- 归一化规则用到的模式 ------------------------------------------------

_TS_KEY = "ts"
_SELFREF_KEY = "artifacts_sha256"
_PDF_DATE_PATTERNS = (
    (re.compile(rb"/CreationDate \([^)]*\)"), b"/CreationDate (D:0)"),
    (re.compile(rb"/ModDate \([^)]*\)"), b"/ModDate (D:0)"),
)
_ABS_WIN = re.compile(r"(?<!\w)[A-Za-z]:[\\/](?![\\/])[^\s\"'<>|,;)\]}]*")
_ABS_POSIX = re.compile(r"/(?:app|skills|input|home|Users|mnt|var|tmp)/[^\s\"'<>|,;)\]}]*")
_TEXT_EXT = (".json", ".svg", ".txt", ".csv", ".md", ".yaml", ".yml")

CWD_ROLES = ("run-dir", "system-temp", "case-dir", "skill-root")


# ---------------------------------------------------------------- 基础工具

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def walk_files(root: str):
    """输出目录内的全部文件（相对路径，/ 分隔），排序后返回。"""
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for fn in filenames:
            p = os.path.join(dirpath, fn)
            out.append(os.path.relpath(p, root).replace("\\", "/"))
    return sorted(out)


def _runs_of(o):
    """去掉 list 下标，便于把上千个 ts 收敛成一条路径模式。"""
    return o


def path_diff(a, b, path=""):
    """结构化 diff：产出 (路径模式, 左值, 右值) 三元组；list 下标折叠为 [*]。"""
    if type(a) is not type(b):
        yield (path or ".<root>"), a, b
        return
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            sub = f"{path}.{k}" if path else f".{k}"
            if k not in a:
                yield sub, "<absent>", b[k]
            elif k not in b:
                yield sub, a[k], "<absent>"
            else:
                yield from path_diff(a[k], b[k], sub)
        return
    if isinstance(a, list):
        if len(a) != len(b):
            yield f"{path}[*]", f"len={len(a)}", f"len={len(b)}"
        for i in range(min(len(a), len(b))):
            yield from path_diff(a[i], b[i], f"{path}[{i}]")
        return
    if a != b:
        yield (path or ".<root>"), a, b


def collapse_pattern(path: str) -> str:
    """`.steps[0].ts` → `.steps[*].ts`（同一字段出现 N 次收敛成一行）。"""
    return re.sub(r"\[\d+\]", "[*]", path)


def _short(v, n=48):
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    return s if len(s) <= n else s[: n - 1] + "…"


def portable(v, pairs):
    """把差异样例里的本机根路径就地换成占位符（在**截断之前**做，样例才有信息量）。"""
    if not isinstance(v, str):
        return v
    for root, ph in sorted(pairs, key=lambda x: -len(x[0] or "")):
        if not root:
            continue
        for variant in (root, root.replace("\\", "/"), root.replace("/", "\\")):
            if variant and variant in v:
                v = v.replace(variant, ph)
    return v


# ---------------------------------------------------------------- 归一化

class NormCtx:
    def __init__(self, roots, norm_sha=None):
        self.roots = [r for r in roots if r]
        self.norm_sha = dict(norm_sha or {})
        self.rules = set()

    def replace_roots(self, s: str) -> str:
        for r in self.roots:
            for variant in (r, r.replace("\\", "/"), r.replace("/", "\\")):
                if variant and variant in s:
                    s = s.replace(variant, "<RUNROOT>")
                    self.rules.add("N2")
        return s


def _norm_obj(o, ctx: NormCtx):
    if isinstance(o, dict):
        out = {}
        for k, v in o.items():
            if k == _SELFREF_KEY and isinstance(v, dict):
                ctx.rules.add("N3")
                out[k] = {kk: ctx.norm_sha.get(kk, "<UNRESOLVED>") for kk in v}
            elif k == _TS_KEY and isinstance(v, str):
                ctx.rules.add("N1")
                out[k] = "<TS>"
            else:
                out[k] = _norm_obj(v, ctx)
        return out
    if isinstance(o, list):
        return [_norm_obj(x, ctx) for x in o]
    if isinstance(o, str):
        return ctx.replace_roots(o)
    return o


def canonical_json_bytes(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def normalize_bytes(name: str, raw: bytes, ctx: NormCtx) -> bytes:
    """按扩展名走 N1–N4，返回归一化后的字节。"""
    low = name.lower()
    if low.endswith(".json"):
        try:
            obj = json.loads(raw.decode("utf-8-sig"))
        except Exception:
            return ctx.replace_roots(raw.decode("utf-8", "replace")).encode("utf-8")
        return canonical_json_bytes(_norm_obj(obj, ctx))
    if low.endswith(".pdf"):
        out = raw
        for pat, rep in _PDF_DATE_PATTERNS:
            if pat.search(out):
                ctx.rules.add("N4")
                out = pat.sub(rep, out)
        return out
    if low.endswith(_TEXT_EXT):
        return ctx.replace_roots(raw.decode("utf-8", "replace")).encode("utf-8")
    return raw + b"\x00" + name.encode("utf-8")  # 二进制：不改内容，仅绑定文件名


# ---------------------------------------------------------------- 绝对路径扫描

def scan_abs_paths(obj, path="", found=None):
    """在 JSON 对象里找绝对路径字符串（实测可移植性缺口）。"""
    found = [] if found is None else found
    if isinstance(obj, dict):
        for k, v in obj.items():
            scan_abs_paths(v, f"{path}.{k}" if path else f".{k}", found)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            scan_abs_paths(v, f"{path}[*]", found)
    elif isinstance(obj, str):
        for rx in (_ABS_WIN, _ABS_POSIX):
            for m in rx.finditer(obj):
                found.append({"path": path or ".", "sample": m.group(0)})
    return found


# ---------------------------------------------------------------- 报告脱敏

def redact_residual_abs(obj):
    """兜底：把任何残留的绝对路径形态（含被截断的前缀）替换为 <ABS>。

    为什么需要它：`volatile_fields.example_left` 是**截断过**的值，其前缀可能与
    完整根路径不再逐字相等，映射式替换会漏掉。报告要进包，而包内不许出现本机
    绝对路径，所以这里再兜一道（幂等）。
    """
    if isinstance(obj, dict):
        return {k: redact_residual_abs(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact_residual_abs(v) for v in obj]
    if isinstance(obj, str):
        if obj.startswith("<"):
            return obj
        for rx in (_ABS_WIN, _ABS_POSIX):
            obj = rx.sub("<ABS>", obj)
        return obj
    return obj


def redact(obj, mapping):
    """把报告里的本机绝对路径换成占位符（报告要进包，包里不许有本机路径）。"""
    if isinstance(obj, dict):
        return {k: redact(v, mapping) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact(v, mapping) for v in obj]
    if isinstance(obj, str):
        for root, ph in sorted(mapping, key=lambda x: -len(x[0])):
            if not root:
                continue
            for variant in (root, root.replace("\\", "/"), root.replace("/", "\\")):
                obj = obj.replace(variant, ph)
        return obj
    return obj


# ---------------------------------------------------------------- 单次运行

def _cwd_for(i: int, run_dir: str, case_dir: str) -> tuple:
    role = CWD_ROLES[i % len(CWD_ROLES)]
    if role == "run-dir":
        return run_dir, role
    if role == "system-temp":
        return tempfile.gettempdir(), role
    if role == "case-dir":
        return case_dir, role
    return PKG_ROOT, role


def _arg_display(a) -> str:
    """报告里只留可移植写法：解释器与技能根一律用占位符。"""
    s = str(a)
    if s == sys.executable:
        return "<PYTHON>"
    for root, ph in ((PKG_ROOT, "<SKILL_DIR>"), (tempfile.gettempdir(), "<TMP>")):
        for variant in (root, root.replace("\\", "/"), root.replace("/", "\\")):
            if variant and variant in s:
                s = s.replace(variant, ph)
    if s.startswith("<"):
        return s.replace("\\", "/")
    # 其余绝对路径（如 --out 落在 --workroot 下）交给报告脱敏阶段套 <WORKSPACE>/<CASEDIR>
    return s.replace("\\", "/")


def run_once(i: int, main_py: str, case_path: str, out_dir: str, work_dir: str,
             run_dir: str, case_dir: str, seed, timeout: int, quiet: bool):
    cwd, role = _cwd_for(i, run_dir, case_dir)
    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir, ignore_errors=True)
    if os.path.isdir(work_dir):
        shutil.rmtree(work_dir, ignore_errors=True)
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(work_dir, exist_ok=True)

    argv = [sys.executable, main_py, "--case", os.path.abspath(case_path),
            "--out", os.path.abspath(out_dir), "--work", os.path.abspath(work_dir)]
    env = dict(os.environ)
    if seed is not None:
        env["PYTHONHASHSEED"] = str(seed)
    env.pop("MAIN_DEBUG", None)

    rec = {"i": i, "cwd_role": role, "cwd": _arg_display(cwd), "pythonhashseed": seed,
           "argv": [_arg_display(a) for a in argv], "exit": None, "seconds": None,
           "stdout_sha256": None,
           "stdout_tail": "", "stderr_tail": "", "errors": []}
    t0 = time.time()
    try:
        proc = subprocess.run(argv, cwd=cwd, env=env, timeout=timeout,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        rec["exit"] = proc.returncode
        out, err = proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        rec["exit"] = -1
        rec["errors"].append(f"timeout after {timeout}s")
        out = err = b""
    rec["seconds"] = round(time.time() - t0, 3)
    rec["stdout_sha256"] = sha256_bytes(out)
    rec["stdout_tail"] = "\n".join(out.decode("utf-8", "replace").splitlines()[-4:])
    rec["stderr_tail"] = "\n".join(err.decode("utf-8", "replace").splitlines()[-4:])

    rp = os.path.join(out_dir, "result.json")
    rec["result_json_present"] = os.path.exists(rp)
    rec["status"] = None
    rec["result_json_keys"] = 0
    if rec["result_json_present"]:
        try:
            with open(rp, "r", encoding="utf-8-sig") as f:
                _res = json.load(f)
            rec["status"] = _res.get("status")
            rec["result_json_keys"] = len(_res) if isinstance(_res, dict) else -1
            rec["gates_all_pass"] = (_res.get("gates") or {}).get("all_pass")
        except Exception as exc:
            rec["errors"].append(f"result.json 不可解析：{type(exc).__name__}: {exc}")
    else:
        rec["errors"].append("未产出 result.json")

    rec["artifacts"] = {}
    for rel in walk_files(out_dir):
        p = os.path.join(out_dir, rel)
        rec["artifacts"][rel] = {"sha256": sha256_file(p), "bytes": os.path.getsize(p)}
    rec["n_artifacts"] = len(rec["artifacts"])
    if not quiet:
        print(f"[determinism] run-{i} seed={seed} cwd={role} exit={rec['exit']} "
              f"status={rec['status']} files={rec['n_artifacts']} {rec['seconds']}s")
    return rec


# ---------------------------------------------------------------- 主流程

def determinism(case_path, runs=3, seeds=None, mode="isolated", workroot=None,
                main_py=None, keep=False, timeout=300, quiet=False,
                abs_policy="redact"):
    case_path = os.path.abspath(case_path)
    case_dir = os.path.dirname(case_path)
    main_py = os.path.abspath(main_py or DEFAULT_MAIN)
    if not os.path.exists(case_path):
        raise FileNotFoundError(f"case.json 不存在：{case_path}")
    if not os.path.exists(main_py):
        raise FileNotFoundError(f"main.py 不存在：{main_py}")

    workroot = os.path.abspath(workroot or tempfile.mkdtemp(prefix="determinism-"))
    os.makedirs(workroot, exist_ok=True)
    seeds = list(seeds or [None])

    report = {
        "tool": "determinism.py",
        "axis": "v7 / 确定性与字节级可复现",
        "version": 1,
        "case": case_path,
        "case_dir": case_dir,
        "main": main_py,
        "mode": mode,
        "runs_requested": runs,
        "seeds": [str(s) for s in seeds],
        "cwd_roles": list(CWD_ROLES),
        "workroot": workroot,
        "normalization_rules": {
            "N1": "JSON 键 `ts` 的值 → \"<TS>\"（chartkit.now_ts() 本地时间戳）",
            "N2": "JSON/SVG/TXT 里的本次运行根路径 → \"<RUNROOT>\"",
            "N3": "JSON `artifacts_sha256.<file>` → 该文件归一化后的 sha256（自引用哈希闭合）",
            "N4": "PDF `/CreationDate|/ModDate (...)` → `(D:0)`（Pillow 内嵌当前时间）",
        },
        "runs": [],
        "per_file_sha256": {},
        "identical": None,
        "normalized_identical": None,
        "volatile_fields": [],
        "volatile_classes": {},
        "binary_notes": {},
        "file_set_identical": None,
        "abs_path_leaks": [],
        "verified_by_command": (
            f'{os.path.basename(sys.executable)} scripts/determinism.py '
            f'--case <case> --runs {runs} --mode {mode}'
        ),
        "findings": [],
        "ladder": None,
    }

    t_start = time.time()
    for i in range(runs):
        run_dir = os.path.join(workroot, f"run-{i}")
        out_dir = (os.path.join(workroot, "shared-out") if mode == "inplace"
                   else os.path.join(run_dir, "out"))
        work_dir = (os.path.join(workroot, "shared-work") if mode == "inplace"
                    else os.path.join(run_dir, "work"))
        os.makedirs(run_dir, exist_ok=True)
        rec = run_once(i, main_py, case_path, out_dir, work_dir, run_dir, case_dir,
                       seeds[i % len(seeds)], timeout, quiet)
        rec["out_dir"] = out_dir
        rec["run_root"] = workroot if mode == "inplace" else run_dir
        # inplace 模式下所有运行共用同一个输出目录 ⇒ 必须**当场快照**，
        # 否则下一轮会把它覆盖掉，事后再读就只能读到最后一轮的内容。
        if mode == "inplace":
            snap = os.path.join(workroot, "snapshots", f"run-{i}")
            if os.path.isdir(snap):
                shutil.rmtree(snap, ignore_errors=True)
            shutil.copytree(out_dir, snap)
            rec["compare_dir"] = snap
        else:
            rec["compare_dir"] = out_dir
        # 归一化副本（写入 out_dir 之外，避免污染被测产物）
        norm_dir = os.path.join(workroot, "normalized", f"run-{i}")
        os.makedirs(norm_dir, exist_ok=True)
        rec["_norm_dir"] = norm_dir
        report["runs"].append(rec)

    ok_runs = [r for r in report["runs"] if r["result_json_present"]
               and not any("不可解析" in e for e in r["errors"])]
    report["runs_with_result_json"] = len(ok_runs)

    # ---- 文件集与逐文件比对 ----
    file_sets = [set(r["artifacts"]) for r in report["runs"]]
    all_names = sorted(set().union(*file_sets)) if file_sets else []
    report["file_set_identical"] = all(fs == file_sets[0] for fs in file_sets)
    report["files"] = all_names

    # pass 1：先算各文件归一化 sha（不含 artifacts_sha256 的互引）
    ctx1 = NormCtx([], {})
    for r in report["runs"]:
        for rel in r["artifacts"]:
            p = os.path.join(r["compare_dir"], rel)
            with open(p, "rb") as f:
                raw = f.read()
            with open(os.path.join(r["_norm_dir"], rel.replace("/", "__")), "wb") as f:
                f.write(normalize_bytes(rel, raw, ctx1))

    def _norm_sha_map_of(run_rec, sha_key):
        m = {}
        for rel in run_rec["artifacts"]:
            src = (os.path.join(run_rec["_norm_dir"], rel.replace("/", "__"))
                   if sha_key == "norm" else os.path.join(run_rec["compare_dir"], rel))
            m[rel] = sha256_file(src)
        return m

    per_file = {}
    for rel in all_names:
        entry = {"present_in_runs": 0, "byte_identical": None, "normalized_identical": None}
        for r in report["runs"]:
            tag = f"run-{r['i']}"
            if rel in r["artifacts"]:
                entry[tag] = r["artifacts"][rel]["sha256"]
                entry[tag + "_bytes"] = r["artifacts"][rel]["bytes"]
                entry["present_in_runs"] += 1
            else:
                entry[tag] = None
        raw_vals = [entry.get(f"run-{r['i']}") for r in report["runs"]]
        entry["byte_identical"] = (None not in raw_vals and len(set(raw_vals)) == 1)
        per_file[rel] = entry

    # pass 2：用 pass-1 的归一化 sha 做 N3 自引用替换，得到最终归一化 sha
    ref_sha = {}
    for r in report["runs"]:
        ref_sha[r["i"]] = _norm_sha_map_of(r, "norm")
    ctx2 = NormCtx([], {})
    norm_sha_by_run = {}
    for r in report["runs"]:
        ctx = NormCtx([r["run_root"], workroot, case_dir], ref_sha[r["i"]])
        m = {}
        for rel in r["artifacts"]:
            p = os.path.join(r["compare_dir"], rel)
            with open(p, "rb") as f:
                raw = f.read()
            nb = normalize_bytes(rel, raw, ctx)
            m[rel] = sha256_bytes(nb)
            with open(os.path.join(r["_norm_dir"], rel.replace("/", "__")), "wb") as f:
                f.write(nb)
            ctx2.rules |= ctx.rules
        norm_sha_by_run[r["i"]] = m
    report["normalization_rules_applied"] = sorted(ctx2.rules)

    for rel in all_names:
        vals = [norm_sha_by_run[r["i"]].get(rel) for r in report["runs"]]
        per_file[rel]["normalized_identical"] = (None not in vals and len(set(vals)) == 1)
        if vals and vals[0] is not None:
            per_file[rel]["normalized_sha256"] = vals[0]
    report["per_file_sha256"] = per_file

    raw_identical = all(e["byte_identical"] for e in per_file.values()) and \
        report["file_set_identical"] and bool(per_file)
    norm_identical = all(e["normalized_identical"] for e in per_file.values()) and \
        report["file_set_identical"] and bool(per_file)
    report["identical"] = bool(raw_identical)
    report["normalized_identical"] = bool(norm_identical)
    report["identical_files"] = [k for k, v in per_file.items() if v["byte_identical"]]
    report["differing_files"] = [k for k, v in per_file.items() if not v["byte_identical"]]

    # ---- volatile_fields：逐字段定位差异 ----
    base_i = report["runs"][0]["i"]
    agg = {}
    for r in report["runs"][1:]:
        for rel in all_names:
            if per_file[rel]["byte_identical"]:
                continue
            if not rel.lower().endswith(".json"):
                continue
            pa, pb = os.path.join(report["runs"][0]["compare_dir"], rel), os.path.join(r["compare_dir"], rel)
            if not (os.path.exists(pa) and os.path.exists(pb)):
                continue
            try:
                with open(pa, "r", encoding="utf-8-sig") as f:
                    A = json.load(f)
                with open(pb, "r", encoding="utf-8-sig") as f:
                    B = json.load(f)
            except Exception:
                continue
            for path, va, vb in path_diff(A, B):
                key = (rel, collapse_pattern(path))
                disp = [(report["runs"][0]["run_root"], "<RUNROOT>"),
                        (r["run_root"], "<RUNROOT>"),
                        (workroot, "<WORKSPACE>"),
                        (case_dir, "<CASEDIR>"),
                        (PKG_ROOT, "<SKILL_DIR>")]
                slot = agg.setdefault(key, {"file": rel, "path": collapse_pattern(path),
                                            "n": 0,
                                            "example_left": _short(portable(va, disp), 64),
                                            "example_right": _short(portable(vb, disp), 64),
                                            "class": None})
                slot["n"] += 1
                slot["class"] = classify(slot["class"], key[1], va, vb, report, r)
    report["volatile_fields"] = sorted(agg.values(), key=lambda d: (d["file"], d["path"]))
    classes = {}
    for v in report["volatile_fields"]:
        classes[v["class"]] = classes.get(v["class"], 0) + 1
    report["volatile_classes"] = classes

    # ---- 二进制差异说明（PDF 日期 / 首个差异偏移）----
    for rel in report["differing_files"]:
        if rel.lower().endswith((".json",)):
            continue
        note = {"file": rel}
        pa = os.path.join(report["runs"][0]["compare_dir"], rel)
        pb = os.path.join(report["runs"][-1]["compare_dir"], rel)
        if os.path.exists(pa) and os.path.exists(pb):
            with open(pa, "rb") as f:
                A = f.read()
            with open(pb, "rb") as f:
                B = f.read()
            note["bytes"] = [len(A), len(B)]
            off = next((i for i, (x, y) in enumerate(zip(A, B)) if x != y), None)
            note["first_diff_offset"] = off
            if rel.lower().endswith(".pdf"):
                ctxd = NormCtx([], {})
                date_only = normalize_bytes(rel, A, ctxd) == normalize_bytes(rel, B, ctxd)
                note["date_only_diff"] = bool(date_only)
                note["embedded_dates"] = [
                    m.group(0).decode("latin-1")
                    for pat, _ in _PDF_DATE_PATTERNS for m in pat.finditer(A)
                ][:4]
        report["binary_notes"][rel] = note

    # ---- 绝对路径泄漏扫描（跑一次 run-0 的产物文本）----
    leaks = []
    for rel in all_names:
        if not rel.lower().endswith(_TEXT_EXT):
            continue
        p = os.path.join(report["runs"][0]["compare_dir"], rel)
        try:
            txt = open(p, "r", encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        if rel.lower().endswith(".json"):
            try:
                for hit in scan_abs_paths(json.loads(txt)):
                    leaks.append({"file": rel, **hit})
                continue
            except Exception:
                pass
        for rx in (_ABS_WIN, _ABS_POSIX):
            for m in rx.finditer(txt):
                leaks.append({"file": rel, "path": "<text>", "sample": m.group(0)})
    seen, uniq = set(), []
    for h in leaks:
        key = (h["file"], h["path"], h["sample"])
        if key not in seen:
            seen.add(key)
            uniq.append(h)
    report["abs_path_leaks"] = uniq[:40]

    # ---- 结论与阶梯 ----
    f = report["findings"]
    f.append(f"重复 {runs} 次（独立进程 + cwd 轮转 + PYTHONHASHSEED 轮转，mode={mode}），"
             f"每次产出 {report['runs'][0]['n_artifacts']} 个产物文件。")
    f.append(f"字节级全同：{report['identical']}；归一化后全同：{report['normalized_identical']}。")
    if report["differing_files"]:
        f.append("字节不同的文件：" + ", ".join(report["differing_files"]))
    if report["volatile_fields"]:
        f.append("不稳定字段：" + "; ".join(
            f"{v['file']}{v['path']}×{v['n']}[{v['class']}]" for v in report["volatile_fields"][:12]))
    if report["abs_path_leaks"]:
        f.append(f"产物文本中另有 {len(report['abs_path_leaks'])} 处绝对路径（同机重跑不影响，"
                 f"换目录/换机器会破坏字节一致性）："
                 + "; ".join(sorted({h["file"] + h["path"] for h in report["abs_path_leaks"]})[:6]))
    unknown = [v for v in report["volatile_fields"] if v["class"] == "unknown"]
    if unknown:
        f.append("★ 未被 N1–N4 解释的字段（必须处理）："
                 + "; ".join(f"{v['file']}{v['path']}" for v in unknown[:8]))

    if len(ok_runs) < runs:
        report["ladder"] = 1
    elif report["identical"]:
        report["ladder"] = 0
    elif report["normalized_identical"]:
        report["ladder"] = 2
    else:
        report["ladder"] = 3
    report["exit_meaning"] = {
        0: "全部产物逐字节相同（最强）",
        2: "字节级不同但归一化后相同 => 差异已被 N1–N4 完全解释",
        3: "归一化后仍有差异 => 存在未解释的不确定性",
        1: "运行未能产出可解析 result.json，无法判定",
    }[report["ladder"]]
    report["ladder_note"] = (
        "阶梯 0 需要运行环境在整轮内时钟不前进：本包**故意**保留 change_records/steps 的 "
        "ts（审计线索）与 Pillow 写入 PDF 的 /CreationDate（预览件元数据），所以在本机实测"
        "落在阶梯 2 —— 差异被 N1–N4 逐字段解释完，并非随机。要拿到 0，需在启动前冻结时钟"
        "（如 libfaketime）或改写这两处写入点；本包选择「诚实留痕 + 归一化可判定」，"
        "而不是删掉时间戳来伪造字节稳定。"
    )
    if keep:
        for r in report["runs"]:
            r["normalized_dir"] = r.get("_norm_dir")
            r["compare_dir_note"] = ("同一输出目录的快照" if r.get("compare_dir") != r.get("out_dir")
                                     else "各次运行自己的输出目录")

    report["elapsed_seconds"] = round(time.time() - t_start, 3)

    if not keep:
        for r in report["runs"]:
            shutil.rmtree(r["_norm_dir"], ignore_errors=True)
            if r.get("compare_dir") != r.get("out_dir"):
                shutil.rmtree(r["compare_dir"], ignore_errors=True)
    for r in report["runs"]:
        r.pop("_norm_dir", None)

    if abs_policy == "redact":
        mapping = [
            (workroot, "<WORKSPACE>"),
            (case_dir, "<CASEDIR>"),
            (PKG_ROOT, "<SKILL_DIR>"),
            (tempfile.gettempdir(), "<TMP>"),
            (sys.executable, "<PYTHON>"),
            (os.path.dirname(sys.executable), "<PYTHON_DIR>"),
        ]
        report = redact_residual_abs(redact(report, mapping))
    return report


def classify(current, path, va, vb, report, run_rec):
    """把一个差异字段归类；归不了类的老实标 unknown（不许猜）。"""
    leaf = re.sub(r"\[\*\]", "", path.split(".")[-1])
    if leaf == "ts":
        return "timestamp"
    if current == "unknown":
        return "unknown"
    if path.startswith("." + _SELFREF_KEY):
        return "self_reference_hash"
    for v in (va, vb):
        if isinstance(v, str) and ("<RUNROOT>" in v or run_rec["run_root"] in v):
            return "run_root_path"
        if isinstance(v, str) and report["workroot"] and report["workroot"] in v:
            return "run_root_path"
    if current:
        return current
    return "unknown"


# ---------------------------------------------------------------- CLI

def main(argv=None):
    # 控制台编码兜底（Windows 默认 GBK；只影响打印，不影响产物与报告）
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(
        description="字节级可复现性实测台（同输入连跑 N 次 × 跨进程/跨 cwd/跨 PYTHONHASHSEED）")
    ap.add_argument("--case", required=True, help="case.json 路径")
    ap.add_argument("--runs", type=int, default=3, help="重复次数（默认 3，最少 2）")
    ap.add_argument("--seeds", default="0,1,12345",
                    help="PYTHONHASHSEED 轮转表，逗号分隔；空串表示不改动环境")
    ap.add_argument("--mode", default="isolated", choices=["isolated", "inplace"],
                    help="isolated=每次换输出目录；inplace=每次写同一绝对输出目录")
    ap.add_argument("--workroot", default=None, help="包外工作目录（默认系统临时目录）")
    ap.add_argument("--out", default=None, help="报告路径（默认 <workroot>/determinism_report.json）")
    ap.add_argument("--main", default=None, help="main.py 路径（默认本脚本同目录）")
    ap.add_argument("--json", action="store_true", help="报告同时打印到 stdout")
    ap.add_argument("--keep", action="store_true", help="保留各次运行的输出目录")
    ap.add_argument("--timeout", type=int, default=300, help="单次运行超时（秒）")
    ap.add_argument("--abs-policy", default="redact", choices=["redact", "keep"],
                    help="报告里的本机绝对路径是否替换为占位符（默认 redact）")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    if args.runs < 2:
        print("[determinism] --runs 至少为 2（1 次无法判定确定性）", file=sys.stderr)
        return 1
    seeds = [s for s in (args.seeds or "").split(",") if s.strip()] or [None]
    seeds = [int(s) if s.strip().lstrip("-").isdigit() else s for s in seeds]

    workroot = args.workroot
    try:
        if not workroot:
            workroot = tempfile.mkdtemp(prefix="determinism-")
        report = determinism(args.case, runs=args.runs, seeds=seeds, mode=args.mode,
                             workroot=workroot, main_py=args.main, keep=args.keep,
                             timeout=args.timeout, quiet=args.quiet,
                             abs_policy=args.abs_policy)
        out = args.out or os.path.join(workroot, "determinism_report.json")
        os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
        _scratch_write(out, report, args.abs_policy, workroot, report.get("case_dir"))
    except Exception as exc:
        print(f"[determinism] FATAL {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"[determinism] case={report['case']} mode={report['mode']} runs={len(report['runs'])}")
        for rel, e in sorted(report["per_file_sha256"].items()):
            tag = "SAME" if e["byte_identical"] else ("NORM-SAME" if e["normalized_identical"] else "DIFF")
            print(f"   [{tag:>9s}] {rel}")
        for v in report["volatile_fields"]:
            print(f"   [volatile] {v['file']}{v['path']} ×{v['n']}  class={v['class']}  "
                  f"{v['example_left']} -> {v['example_right']}")
        print(f"[determinism] identical={report['identical']} "
              f"normalized_identical={report['normalized_identical']} "
              f"=> exit {report['ladder']} ({report['exit_meaning']})")
    return report["ladder"]


def _scratch_write(path, report, abs_policy, workroot, case_dir):
    """写报告：报告本身也要过"包内无本机绝对路径"的硬门。"""
    payload = report
    if abs_policy == "redact":
        payload = redact(report, [(workroot or "", "<WORKSPACE>"),
                                  (case_dir or "", "<CASEDIR>"),
                                  (PKG_ROOT, "<SKILL_DIR>"),
                                  (tempfile.gettempdir(), "<TMP>"),
                                  (sys.executable, "<PYTHON>"),
                                  (os.path.dirname(sys.executable), "<PYTHON_DIR>")])
    payload = redact_residual_abs(payload)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path


if __name__ == "__main__":
    sys.exit(main())
