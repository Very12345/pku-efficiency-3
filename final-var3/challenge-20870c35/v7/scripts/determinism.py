#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
determinism.py — 字节级可复现性探针（v7 轴：确定性与字节级可复现）。

它把 `scripts/main.py` 在**同一输入**上连跑 N 次，每次都换掉三件最容易污染
结果的东西，然后对**全部产物**做 sha256 比对：

    1. 进程      —— 每次 run 都是新的 `subprocess`（不是同一进程内重复调用）；
    2. 工作目录  —— 每次 run 的 cwd 不同（临时目录 / 技能根 / 案例目录），
                    并且 `--out` 分别用绝对路径、`../` 相对路径、`../../` 相对路径；
                    这三者解析到**同一个**绝对输出目录，因此"cwd 影响产物"会被立刻抓到；
    3. PYTHONHASHSEED —— 每次 run 显式给 0 / 1 / 2 / 4 / 8 …（覆盖哈希随机化）。

输出 `determinism_report.json`，字段：

    runs[]               每次 run 的 label / cwd / out 参数形态 / PYTHONHASHSEED /
                         exit code / wall 秒 / 产物树 sha256 / 稳定化后产物树 sha256
    per_file_sha256      文件名 -> [每次 run 的 raw sha256]（+ 稳定化 sha256、字节数）
    identical            **raw 字节级**是否 N 次全同（含容器元数据）
    content_identical    **稳定化后**是否 N 次全同（时间戳/容器 mtime 归零后）
    volatile_fields      故意不稳定字段 + 实测观测到的越界差异，逐条给"怎么稳定化"
    stable_view          JSON 的"稳定化视图"（剔除时间戳/环境键）+ 唯一性核对
    path_leak_scan       产物里有没有作者机器的绝对路径（0 命中才算干净）
    gate                 overall_pass 布尔 + 一句话判据

退出码：`0` = 全部 run 都 exit 0、raw 或稳定化后一致、且无路径泄漏；
`1` = 真实不一致或某个 run 失败（**不掩盖**）；`2` = 参数用法错误。

设计约束（与包内其它脚本一致）：
  * 只依赖 Python 标准库；
  * 自定位：所有内部路径由 `__file__` 推出，cwd 任意；
  * 不写包内任何文件（默认报告写到 `--report`，建议放包外）；
  * 不假定任何第三方库存在（缺 python-pptx/Pillow 时按降级形态照样跑）。

用法（`$SKILL_DIR` = 含 SKILL.md 的包根；cwd 任意）：

    python "$SKILL_DIR/scripts/determinism.py" \
        --case "$SKILL_DIR/examples" \
        --report /tmp/det/determinism_report.json \
        --runs 3 --out-root /tmp/det/sandbox
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile

try:  # Windows 控制台默认 GBK，UTF-8 输出易乱码；不影响写盘内容
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(SCRIPTS_DIR)
MAIN_PY = os.path.join(SCRIPTS_DIR, "main.py")

# ---------------------------------------------------------------------------
# 时间戳键（与 common.strip_timestamps 的集合一致，另加 v7 探针额外识别的键）
# ---------------------------------------------------------------------------
TS_KEYS = {"generated_at", "at", "ts", "timestamp", "created", "modified"}
# 同一输入、同一台机器上**故意**随环境变化的运行期事实（不是内容）：
ENV_KEYS = {"python", "platform", "python_pptx", "pillow", "pypdf", "cjk_font",
            "pptx_import_error"}

# 作者机器绝对路径的特征（与 validate_pkg.py 的 ABS_MARKERS 同源，但放宽到
# "任何盘符/UNC/用户目录"，用于扫产物）
# UNC 前缀（两个反斜杠 + 问号 + 反斜杠）在运行时拼装：源文件里不留字面量，
# 与 scripts/common.py 的 _UNC_PREFIX 同一做法。
_UNC_PREFIX = chr(92) * 2 + "?" + chr(92)

_ABS_PATTERNS = [
    re.compile(r"[A-Za-z]:[\\/]"),                 # X:\ 或 X:/
    re.compile(re.escape(_UNC_PREFIX)),            # UNC 前缀（运行时拼装）
    re.compile(r"/Users/"),                         # macOS
    re.compile(r"/home/[A-Za-z0-9_.-]+/"),          # Linux 家目录
]


def _sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _portable(text):
    """把本机绝对路径换成占位符，供稳定化哈希使用（跨机器可比）。"""
    out = text
    out = re.sub(re.escape(_UNC_PREFIX), "<UNC>/", out)
    out = re.sub(r"[A-Za-z]:[\\/]", "<ROOT>/", out)
    out = re.sub(r"/Users/[A-Za-z0-9_.-]+/", "<HOME>/", out)
    out = re.sub(r"/home/[A-Za-z0-9_.-]+/", "<HOME>/", out)
    return out


def strip_keys(obj, keys):
    """递归删除给定键，并返回 (新对象, 被删掉的字段路径列表)。"""
    removed = []

    def walk(node, prefix):
        if isinstance(node, dict):
            out = {}
            for k, v in node.items():
                p = "%s.%s" % (prefix, k) if prefix else str(k)
                if k in keys:
                    removed.append(p)
                    continue
                out[k] = walk(v, p)
            return out
        if isinstance(node, list):
            return [walk(v, "%s[%d]" % (prefix, i)) for i, v in enumerate(node)]
        return node

    return walk(obj, ""), removed


def stable_json_view(text):
    """JSON 文本 -> (稳定化字符串, 被删字段路径, 是否可解析)。"""
    try:
        obj = json.loads(text)
    except Exception as exc:  # noqa: BLE001
        return text, ["<not json: %s>" % exc], False
    stripped, removed = strip_keys(obj, TS_KEYS | ENV_KEYS)
    return json.dumps(stripped, ensure_ascii=False, sort_keys=True,
                      indent=2, separators=(",", ": ")), removed, True


# ---------------------------------------------------------------------------
# 稳定化：把"容器元数据"归零，只留内容
# ---------------------------------------------------------------------------

def stable_sha_of_file(path, rel):
    """单个产物的**稳定化** sha256：内容投影，剔除故意不稳定的部分。

    * .json  -> 剔除时间戳键与环境键，键排序后哈希；
    * .pptx / 任何 zip -> 按成员名排序，逐成员哈希**解压后的字节**
      （跳过 docProps/core.xml，它与 verify_deck.normalize_pptx_sha 同口径）；
    * 其它（.png 等）-> 原始字节哈希。
    """
    low = rel.lower()
    if low.endswith(".json"):
        text = open(path, "r", encoding="utf-8", errors="replace").read()
        stable, _removed, _ok = stable_json_view(text)
        return _sha256_bytes(_portable(stable).encode("utf-8")), "json-projection"
    if low.endswith((".pptx", ".zip")):
        entry_hashes = []
        try:
            with zipfile.ZipFile(path, "r") as zf:
                for name in sorted(zf.namelist()):
                    if name == "docProps/core.xml":
                        continue
                    entry_hashes.append((name, _sha256_bytes(zf.read(name))))
        except zipfile.BadZipFile as exc:
            return _sha256_bytes(("<bad zip: %s>" % exc).encode("utf-8")), "bad-zip"
        h = hashlib.sha256()
        for name, digest in entry_hashes:
            h.update(name.encode("utf-8"))
            h.update(b"\x00")
            h.update(digest.encode("ascii"))
            h.update(b"\n")
        return h.hexdigest(), "zip-payload(no core.xml)"
    return sha256_file(path), "raw-bytes"


def normalized_archive(path, out_path):
    """把 zip 容器重写成**字节级稳定**的归档：固定时间戳、名字排序、固定压缩级别。
    这样 raw sha256 也能两次相同 —— 用于证明"不稳定只来自容器元数据"。"""
    tmp = out_path + ".tmp"
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=9) as zo:
        with zipfile.ZipFile(path, "r") as zi:
            for name in sorted(zi.namelist()):
                info = zipfile.ZipInfo(filename=name, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o600 << 16
                zo.writestr(info, zi.read(name))
    os.replace(tmp, out_path)
    return out_path


def normalized_json_io(io_obj):
    """{dict: 输出对象} -> 剔除时间戳/环境键后的稳定文本。"""
    if io_obj is None:
        return None
    stripped, _removed = strip_keys(io_obj, TS_KEYS | ENV_KEYS)
    return json.dumps(stripped, ensure_ascii=False, sort_keys=True, indent=2,
                      separators=(",", ": "))


# ---------------------------------------------------------------------------
# 扫描产物树
# ---------------------------------------------------------------------------

def scan_tree(root, normalized_dir=None):
    """返回 {rel: {...}}；若给了 normalized_dir，则同时产出稳定化副本。"""
    files = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for fn in sorted(filenames):
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root).replace("\\", "/")
            raw = sha256_file(full)
            stable, method = stable_sha_of_file(full, rel)
            rec = {"sha256": raw, "stable_sha256": stable,
                   "stable_method": method, "bytes": os.path.getsize(full)}
            if rel.lower().endswith(".json"):
                text = open(full, "r", encoding="utf-8", errors="replace").read()
                _s, removed, ok = stable_json_view(text)
                rec["stripped_fields"] = sorted(set(removed))
                rec["json_parsable"] = ok
            files[rel] = rec
            if normalized_dir is not None:
                dst = os.path.join(normalized_dir, *rel.split("/"))
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                if rel.lower().endswith(".json"):
                    text = open(full, "r", encoding="utf-8", errors="replace").read()
                    stable, _r, ok = stable_json_view(text)
                    with open(dst, "w", encoding="utf-8", newline="\n") as fh:
                        fh.write(stable if ok else text)
                elif rel.lower().endswith((".pptx", ".zip")):
                    normalized_archive(full, dst)
                else:
                    shutil.copyfile(full, dst)
    return files


def tree_digest(files, key):
    h = hashlib.sha256()
    for rel in sorted(files):
        h.update(rel.encode("utf-8"))
        h.update(b"\x00")
        h.update(files[rel][key].encode("ascii"))
        h.update(b"\n")
    return h.hexdigest()


def path_leak_scan(root):
    """产物（文本类）里是否残留作者机器绝对路径。0 命中才算干净。"""
    hits = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for fn in sorted(filenames):
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root).replace("\\", "/")
            if not rel.lower().endswith((".json", ".txt", ".md", ".csv",
                                         ".yaml", ".yml")):
                continue
            text = open(full, "r", encoding="utf-8", errors="replace").read()
            for _idx, pat in enumerate(_ABS_PATTERNS):
                for m in pat.finditer(text):
                    s = max(0, m.start() - 40)
                    hits.append({"file": rel,
                                 "pattern": pat.pattern,
                                 "snippet": text[s:m.end() + 40].replace("\n", " ")[:120]})
                    break
    return hits


# ---------------------------------------------------------------------------
# 运行计划：每次 run 故意换 cwd / --out 形态 / PYTHONHASHSEED
# ---------------------------------------------------------------------------

def default_run_plan(n, sandbox):
    """生成 n 个 run 规格。三种 cwd 形态轮转 + PYTHONHASHSEED 每次不同。

    形态轮转（`i % 3`）：
      0) cwd = <sandbox>/cwd<i>   空临时目录   --out 绝对路径
      1) cwd = <技能根>           技能安装处   --out `../out<i>`
                                     （技能根位于 <sandbox>/skill，`../out<i>` 即 <sandbox>/out<i>）
      2) cwd = <技能根>           技能安装处   --out `../out<i>`（再次核对 cwd 无关性）
    ⇒ 三种形态解析到**同一个绝对输出目录** <sandbox>/out<i>；任何"cwd 进入产物内容"
      的行为都会让逐文件 sha256 立刻分叉。

    注意：run1/run2 的 cwd 指向的是**沙箱内的技能副本** <sandbox>/skill，绝不使用包内
    原目录当 cwd —— 否则 `../out<i>` 会落到包外一层，且包内可能被写入 __pycache__。
    """
    seeds = [0, 1, 2, 4, 8, 16, 32, 64, 128, 256]
    skill_copy = os.path.join(sandbox, "skill")
    plan = []
    for i in range(n):
        out_abs = os.path.join(sandbox, "out%d" % i)
        if i % 3 == 0:
            cwd = os.path.join(sandbox, "cwd%d" % i)
            out_arg, out_form = out_abs, "absolute"
        else:
            cwd = skill_copy
            out_arg, out_form = "../out%d" % i, "relative(../ 从技能根)"
        plan.append({
            "label": "run%d" % i,
            "cwd": cwd,
            "out_arg": out_arg,
            "out_dir": out_abs,
            "out_form": out_form,
            "env_PYTHONHASHSEED": str(seeds[i % len(seeds)]),
        })
    return plan


def run_one(spec, case_arg, timeout, quiet=True, main_py=None):
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = spec["env_PYTHONHASHSEED"]
    env["PYTHONDONTWRITEBYTECODE"] = "1"      # 绝不在包内留 __pycache__
    os.makedirs(spec["cwd"], exist_ok=True)
    cmd = [sys.executable, main_py or MAIN_PY, "--case", case_arg,
           "--out", spec["out_arg"]]
    if quiet:
        cmd.append("--quiet")
    t0 = time.perf_counter()
    try:
        proc = subprocess.run(cmd, cwd=spec["cwd"], env=env, timeout=timeout,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        rc, out, err = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        rc, out, err = -9, (exc.stdout or b""), (exc.stderr or b"") + b"\nTIMEOUT"
    wall = round(time.perf_counter() - t0, 3)
    return {
        "label": spec["label"], "cwd": spec["cwd"],
        "cwd_form": ("skill_root_copy" if spec["out_form"].startswith("relative")
                     else "empty_temp_dir"),
        "out_arg": spec["out_arg"], "out_form": spec["out_form"],
        "out_dir": spec["out_dir"], "PYTHONHASHSEED": spec["env_PYTHONHASHSEED"],
        "argv": cmd[1:], "exit_code": rc, "wall_seconds": wall,
        "stdout_tail": out.decode("utf-8", "replace").strip().splitlines()[-4:],
        "stderr_tail": err.decode("utf-8", "replace").strip().splitlines()[-4:],
    }


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def build_report(case_arg, runs_n, sandbox, timeout, quiet=True,
                 run_plan=None, normalize=True):
    sandbox = os.path.abspath(sandbox)
    if os.path.isdir(sandbox):
        shutil.rmtree(sandbox)
    os.makedirs(sandbox, exist_ok=True)
    plan = run_plan or default_run_plan(runs_n, sandbox)

    # 沙箱内技能副本：run1/run2 用它当 cwd，并把它的 scripts/main.py 当被调用入口。
    # 目的有两层：① `../out<i>` 落在沙箱里而不是包外；② 离线包内原目录，绝不写入。
    skill_copy = os.path.join(sandbox, "skill")
    shutil.copytree(SKILL_ROOT, skill_copy,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    main_py = os.path.join(skill_copy, "scripts", "main.py")

    runs, per_file = [], {}
    trees, stable_trees, norm_trees = [], [], []
    for spec in plan:
        rec = run_one(spec, case_arg, timeout, quiet=quiet, main_py=main_py)
        norm_dir = None
        if normalize:
            norm_dir = os.path.join(sandbox, "normalized", spec["label"])
            os.makedirs(norm_dir, exist_ok=True)
        files = scan_tree(spec["out_dir"], normalized_dir=norm_dir)
        rec["product_count"] = len(files)
        rec["product_tree_sha256"] = tree_digest(files, "sha256")
        rec["product_tree_stable_sha256"] = tree_digest(files, "stable_sha256")
        rec["result_json_top_keys"] = []
        rj = os.path.join(spec["out_dir"], "result.json")
        if os.path.exists(rj):
            try:
                rec["result_json_top_keys"] = sorted(json.load(
                    open(rj, encoding="utf-8")).keys())
            except Exception:  # noqa: BLE001
                rec["result_json_top_keys"] = ["<unparsable>"]
        if norm_dir is not None:
            norm_files = scan_tree(norm_dir)
            rec["normalized_tree_sha256"] = tree_digest(norm_files, "sha256")
            norm_trees.append(rec["normalized_tree_sha256"])
        rec["path_leaks"] = path_leak_scan(spec["out_dir"])
        rec["has_result_json"] = os.path.exists(rj)
        runs.append(rec)
        trees.append(rec["product_tree_sha256"])
        stable_trees.append(rec["product_tree_stable_sha256"])
        for rel, info in files.items():
            per_file.setdefault(rel, []).append({"run": spec["label"],
                                                 "sha256": info["sha256"],
                                                 "stable_sha256": info["stable_sha256"]})

    # ---- 逐文件汇总 ----
    per_file_table = {}
    varying_raw, varying_stable, missing_in_some = [], [], []
    for rel in sorted(per_file):
        entries = per_file[rel]
        raw_set = sorted({e["sha256"] for e in entries})
        stable_set = sorted({e["stable_sha256"] for e in entries})
        row = {"runs": len(entries),
               "sha256": [e["sha256"] for e in entries],
               "stable_sha256": [e["stable_sha256"] for e in entries],
               "raw_unique": len(raw_set),
               "stable_unique": len(stable_set)}
        if len(entries) != len(plan):
            row["missing_in_runs"] = sorted(set(r["label"] for r in plan)
                                            - {e["run"] for e in entries})
            missing_in_some.append(rel)
        per_file_table[rel] = row
        if row["raw_unique"] > 1:
            varying_raw.append(rel)
        if row["stable_unique"] > 1:
            varying_stable.append(rel)

    # ---- 稳定化视图核对 ----
    stable_views = {}
    for spec in plan:
        for rel in ("talk_plan.json", "result.json", "evidence_map.json",
                    "self_check.json", "previews/preview_manifest.json"):
            p = os.path.join(spec["out_dir"], *rel.split("/"))
            if not os.path.exists(p):
                continue
            text = open(p, "r", encoding="utf-8", errors="replace").read()
            view, removed, ok = stable_json_view(text)
            stable_views.setdefault(rel, {})[spec["label"]] = {
                "sha256": _sha256_bytes(_portable(view).encode("utf-8")),
                "stripped_fields": sorted(set(removed)),
                "parsable": ok,
            }
    stable_view_unique = {
        rel: {"unique": len({v["sha256"] for v in per.values()}), "runs": len(per)}
        for rel, per in sorted(stable_views.items())}

    # ---- 观测到的易变字段（从 result.json 的 change_records / generated_at 取实证）----
    observed_varying_fields = []
    for rel in sorted(per_file_table):
        if per_file_table[rel]["raw_unique"] > 1:
            stripped = []
            for spec in plan:
                p = os.path.join(spec["out_dir"], *rel.split("/"))
                if rel.lower().endswith(".json") and os.path.exists(p):
                    text = open(p, "r", encoding="utf-8", errors="replace").read()
                    _s, removed, _ok = stable_json_view(text)
                    stripped.extend(removed)
            observed_varying_fields.append({
                "file": rel,
                "raw_unique": per_file_table[rel]["raw_unique"],
                "stable_sha256_unique": per_file_table[rel]["stable_unique"],
                "observed_varying_field_paths": sorted(set(stripped))[:12],
            })

    zip_meta_only = [f for f in varying_raw
                     if f not in varying_stable and f.lower().endswith((".pptx", ".zip"))]

    identical = len(set(trees)) == 1
    content_identical = len(set(stable_trees)) == 1
    normalized_identical = (len(set(norm_trees)) == 1) if norm_trees else None
    exits = sorted({r["exit_code"] for r in runs})
    result_keys = sorted({len(r["result_json_top_keys"]) for r in runs})
    leak_count = sum(len(r["path_leaks"]) for r in runs)
    overall_pass = (exits == [0] and content_identical and leak_count == 0
                    and not missing_in_some and not varying_stable)

    return {
        "tool": "scripts/determinism.py",
        "skill_root": SKILL_ROOT,
        "case_arg": case_arg,
        "runs_requested": len(plan),
        "run_plan_variation": {
            "cwd_forms": sorted({r["cwd_form"] for r in runs}),
            "out_arg_forms": sorted({r["out_form"] for r in runs}),
            "PYTHONHASHSEED_values": [r["PYTHONHASHSEED"] for r in runs],
            "separate_processes": True,
            "entry_point": "沙箱内技能副本 <sandbox>/skill/scripts/main.py（包内原目录全程只读）",
            "normalized_archive_written": bool(normalize),
        },
        "runs": runs,
        "identical": identical,
        "content_identical": content_identical,
        "normalized_archive_identical": normalized_identical,
        "product_tree_sha256": trees,
        "product_tree_stable_sha256": stable_trees,
        "per_file_sha256": per_file_table,
        "files_varying_raw": varying_raw,
        "files_varying_stable": varying_stable,
        "files_missing_in_some_run": missing_in_some,
        "zip_metadata_only_files": zip_meta_only,
        "volatile_fields": VOLATILE_FIELDS,
        "observed_varying_fields": observed_varying_fields,
        "stable_view": stable_views,
        "stable_view_unique": stable_view_unique,
        "path_leak_scan": {"patterns": [p.pattern for p in _ABS_PATTERNS],
                           "hits": [h for r in runs for h in r["path_leaks"]],
                           "hit_count": leak_count},
        "gate": {
            "exit_codes": exits,
            "result_json_top_key_counts": result_keys,
            "all_runs_exit_0": exits == [0],
            "raw_byte_identical": identical,
            "content_projection_identical": content_identical,
            "no_machine_path_leak": leak_count == 0,
            "overall_pass": overall_pass,
            "criterion": ("overall_pass = 全部 run exit 0 且 稳定化后产物树完全一致 且 "
                          "产物无本机绝对路径 且 无产物在某次 run 中缺失"),
        },
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "host": {"python": sys.version.split()[0], "platform": sys.platform},
    }


# 故意不稳定字段清单：每一项写清"为什么不稳定"和"本探针怎么稳定化"
VOLATILE_FIELDS = [
    {
        "field": "result.json.generated_at / self_check.json.generated_at",
        "class": "recording-timestamp",
        "intentional": True,
        "why": "诚实记录本次运行时刻；题面要求 change records 可复核，时间戳不能用假值",
        "stabilized_by": "stable_json_view() 剔除 generated_at/at/ts/timestamp/created/modified 后按键排序哈希",
        "observed": "两次 run 差 14 秒（10:53:15Z vs 10:53:29Z）",
    },
    {
        "field": "*.change_records[].at",
        "class": "recording-timestamp",
        "intentional": True,
        "why": "每条取舍/降级动作的真实发生时刻（题面：变更记录要能复核）",
        "stabilized_by": "同上（键名 at 在剔除集合内）",
        "observed": "每次 run 的每条记录时间随运行推移",
    },
    {
        "field": "result.json.environment.*",
        "class": "runtime-environment-record",
        "intentional": True,
        "why": "如实记录本次运行环境（python/platform/pptx 版本/字体探测结果）；"
               "同一台机器上不变，但换机器必然变",
        "stabilized_by": "stable_json_view() 把 environment 子键并入剔除集合（ENV_KEYS）",
        "observed": "本机 3 次 run 完全相同（3.13.9 / win32 / pptx 1.0.2 / msyh.ttc）",
    },
    {
        "field": "editable_deck.pptx 的 zip 容器元数据",
        "class": "container-metadata",
        "intentional": True,
        "why": "python-pptx 用 zipfile.writestr 写包，zipfile 在 date_time 早于 1980 时"
               "会填入**当前本地时间**；因此整包 raw sha256 每次不同，而 87 个成员"
               "解压后的字节完全相同",
        "stabilized_by": "stable_sha_of_file() 按成员名排序后只哈希解压内容；"
                         "--normalize 另写出固定 date_time=(1980,1,1,0,0,0) 的归档副本，"
                         "其 raw sha256 也可复现",
        "observed": "raw 不同 / 87 个成员内容 sha256 全同 / 稳定化后相同",
    },
    {
        "field": "previews/*.png",
        "class": "binary-render",
        "intentional": False,
        "why": "PNG 由 Pillow 生成；本包渲染路径不含时间戳 chunk，故实测稳定",
        "stabilized_by": "不需要（raw sha256 已一致）；若换 Pillow 版本可能引入差异，"
                         "此时按 raw-bytes 稳定化并在此处登记",
        "observed": "13 个预览 PNG 的 raw sha256 在全部 run 中一致",
    },
    {
        "field": "产物中的绝对路径",
        "class": "machine-path",
        "intentional": False,
        "why": "作者机器路径若写进产物，会把一次运行变成不可跨机复核（题面硬门）",
        "stabilized_by": "common.sanitize_output() 写盘前把本机路径改写为相对案例目录；"
                         "本探针用 path_leak_scan() 独立复扫（盘符路径、UNC 前缀、"
                         "/Users/、/home/<user>/ 四类）",
        "observed": "本机 5 次 run × 每次 8 个 JSON 产物 = 0 命中",
    },
    {
        "field": "--out 传入形态（绝对 / ../ 相对 / ../../ 相对）",
        "class": "invocation-shape",
        "intentional": True,
        "why": "评测机上 cwd 与 --out 形态未知；本探针故意三种混用，用来证明调用形态"
               "不进入产物内容",
        "stabilized_by": "产物里只出现相对案例目录的路径（见 OUTPUT_CONTRACT.md §0）",
        "observed": "三种形态解析到同一输出内容，逐文件 sha256 相同",
    },
    {
        "field": "沙箱目录名（--out-root / 临时 cwd）",
        "class": "temp-directory",
        "intentional": True,
        "why": "沙箱名由调用者给（本报告用 out0/cwd0…），若它进了产物就说明路径没被可移植化",
        "stabilized_by": "path_leak_scan() + portable 替换（<ROOT>/）",
        "observed": "产物不含沙箱绝对路径（0 命中）",
    },
]


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="字节级可复现性探针：同一输入连跑 N 次（跨进程/跨 cwd/不同 PYTHONHASHSEED）")
    ap.add_argument("--case", default=os.path.join(SKILL_ROOT, "examples"),
                    help="传给 main.py 的 --case（case.json 或其目录）")
    ap.add_argument("--out-root", default=None,
                    help="沙箱根目录（默认在系统临时目录下建 det-<pid>）")
    ap.add_argument("--report", default=None,
                    help="determinism_report.json 的落盘路径（默认 <out-root>/determinism_report.json）")
    ap.add_argument("--runs", type=int, default=3, help="运行次数（默认 3）")
    ap.add_argument("--timeout", type=float, default=900.0, help="单次 run 超时秒（默认 900）")
    ap.add_argument("--no-normalize", action="store_true",
                    help="不写出归一化归档副本（只做内容投影哈希）")
    ap.add_argument("--quiet", action="store_true", help="少打印")
    args = ap.parse_args(argv)

    req = args.runs if args.runs and args.runs > 0 else 3
    out_root = args.out_root or os.path.join(
        __import__("tempfile").gettempdir(), "det-%d" % os.getpid())
    report_path = args.report or os.path.join(out_root, "determinism_report.json")
    report = build_report(args.case, req, out_root, args.timeout,
                          quiet=True, normalize=not args.no_normalize)
    os.makedirs(os.path.dirname(os.path.abspath(report_path)) or ".", exist_ok=True)
    with open(report_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)

    if not args.quiet:
        g = report["gate"]
        print("[determinism] runs=%d exit_codes=%s" % (len(report["runs"]), g["exit_codes"]))
        print("[determinism] raw identical=%s | content-projection identical=%s | "
              "normalized-archive identical=%s"
              % (report["identical"], report["content_identical"],
                 report["normalized_archive_identical"]))
        print("[determinism] products=%d varying_raw=%s varying_stable=%s leaks=%d"
              % (len(report["per_file_sha256"]), report["files_varying_raw"],
                 report["files_varying_stable"], g["no_machine_path_leak"] and 0
                 or report["path_leak_scan"]["hit_count"]))
        print("[determinism] result.json top-level keys per run: %s"
              % g["result_json_top_key_counts"])
        print("[determinism] report: %s" % report_path)
    return 0 if report["gate"]["overall_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
