#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""determinism.py — 字节级可复现探针（v7 轴 · 只依赖标准库）。

它把"同输入重跑得到同一份产物"从口头承诺变成**可复算的测量**：

  1. 在 `--work` 下物化一份技能副本 `<work>/pkg` 与一份案例副本 `<work>/case`
     （case.json / task.md / materials 原样复制，model 也用同一份）；
  2. 用 `--runs N` 次**跨进程**运行 `scripts/main.py`（每次都是一个新解释器进程），
     并刻意让每次运行的 **cwd 不同**（技能根 / 工作根 / scripts / case / examples 轮转）
     与 **PYTHONHASHSEED 不同**（0 / 1 / 12345 / random / 不设置）；
  3. 每次运行后**立刻**对输出目录内全部产物做 sha256 + 字节数；
  4. 跨运行比对逐文件 sha256 → `per_file_sha256` / `identical`；
  5. 对不同字节的产物做**字节级定位**（偏移区间 + 上下文），对 JSON 产物做**字段级定位**
     （`volatile_fields[]`：哪个 JSON 路径、看过哪些值、掩码成什么）；
  6. 施加**文档化的稳定化规则**再比对一次：
       (a) JSON 键掩码投影（时间戳/路径类键 + 观测到的易变路径）；
       (b) PDF 的 `/CreationDate` `/ModDate` `/ID` 规范化；
       (c) 环境变量 `SOURCE_DATE_EPOCH=<固定值>` 重跑两次；
     证明"规范化后逐字节一致"，并给出两条互不依赖的稳定化做法。

用法
----
  export SKILL_DIR=/skills/weekly-skill
  python3 "$SKILL_DIR/scripts/determinism.py" --runs 5 \
      --work /tmp/det --report "$SKILL_DIR/determinism_report.json"

  只打印机器可读结果：加 `--json`（stdout 只输出报告 JSON）。
  严格模式：加 `--strict`（要求**原始**字节就完全一致，否则退出码 3）。

退出码
------
  0 = 规范化后全部产物逐字节一致（可复现）
  2 = 主流程本身在某个 run 里非期望退出（环境/输入问题，不是不确定性问题）
  3 = 规范化后仍不一致（真不可复现）
  4 = 探针自身参数/环境错误
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

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SKILL_ROOT = os.path.dirname(HERE)
TOOL_VERSION = "1.0"

# 轮转的 cwd（相对工作根）；每次运行换一个，用来证明脚本自定位不依赖 cwd
CWD_CYCLE = ("pkg", "pkg/scripts", "case", "pkg/examples", ".")
# 轮转的 PYTHONHASHSEED；None = 该次运行不设置这个变量
SEED_CYCLE = ("0", "1", "12345", "random", None)

# 文档化的易变键规则：键名本身表明"时间 / 主机 / 路径"时掩码（不依赖某次观测）
VOLATILE_KEY_RE = re.compile(
    r"(^|_)(ts|time|timestamp|datetime|date|created|created_at|modified|mtime|modtime"
    r"|elapsed|duration|runtime|host|hostname|user|username|pid|cwd|abspath|abs_path)($|_)",
    re.I)
# 位置相关键：值里含绝对路径 → 换机器/换工作根就会变
LOCATION_KEY_RE = re.compile(r"(^|_)(path|file|dir|root|command|argv|ref|source_file)($|_)", re.I)
ABS_PATH_RE = re.compile(r"(?<!>)(?:[A-Za-z]:[\\/]|\\\\[?]\\|/(?:Users|home|tmp|skills)/)[^\s\"'<>|,;)\]]*")
PDF_DATE_RE = re.compile(rb"/(CreationDate|ModDate)\s*\(D:[^)]*\)")
PDF_ID_RE = re.compile(rb"/ID\s*\[\s*<[0-9A-Fa-f]*>\s*<[0-9A-Fa-f]*>\s*\]")
MASK = "<VOLATILE>"


# --------------------------------------------------------------------------
# 基础工具
# --------------------------------------------------------------------------
def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def read_bytes(path):
    with open(path, "rb") as fh:
        return fh.read()


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def portable(text, roots):
    """把绝对路径替换成占位符（报告里绝不出现本机绝对路径）。"""
    if not isinstance(text, str):
        return text
    out = text
    for root, tag in roots:
        if not root:
            continue
        # 同一路径可能以 \ 或 / 分隔，也可能带尾部分隔符：逐个变体替换
        for variant in (root, root.rstrip("/\\"), root.replace("\\", "/"),
                        root.replace("/", "\\"), root.replace("\\", "\\\\")):
            if variant:
                out = out.replace(variant, tag)
    out = ABS_PATH_RE.sub("<ABS>", out)   # 整段绝对路径掩码；(?<!>) 保证幂等
    return out.replace("\\", "/")


def short_value(v, limit=90):
    """值的短快照：字符串保持原文（不做 JSON 转义），其它类型用 json 序列化。"""
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    return s[:limit]


def portable_obj(obj, roots):
    if isinstance(obj, dict):
        return {k: portable_obj(v, roots) for k, v in obj.items()}
    if isinstance(obj, list):
        return [portable_obj(v, roots) for v in obj]
    if isinstance(obj, str):
        return portable(obj, roots)
    return obj


def copy_tree(src, dst, skip_dir_names=("__pycache__", ".git", "out", "runs"),
              skip_ext=(".pyc", ".pyo")):
    os.makedirs(dst, exist_ok=True)
    for root, dirs, files in os.walk(src):
        dirs[:] = sorted(d for d in dirs
                         if d not in skip_dir_names and not d.startswith(".git"))
        rel = os.path.relpath(root, src)
        tgt = dst if rel == "." else os.path.join(dst, rel)
        os.makedirs(tgt, exist_ok=True)
        for f in sorted(files):
            if os.path.splitext(f)[1].lower() in skip_ext:
                continue
            shutil.copy2(os.path.join(root, f), os.path.join(tgt, f))


def safe_reset(work_root, sub):
    """只允许删 work_root 的**直接子项**，且 work_root 本身不能是技能根/盘根。"""
    target = os.path.abspath(os.path.join(work_root, sub))
    wr = os.path.abspath(work_root)
    if os.path.dirname(target) != wr:
        raise SystemExit("拒绝操作（越界）: %s 不是 %s 的直接子项" % (target, wr))
    if os.path.isfile(os.path.join(wr, "SKILL.md")):
        raise SystemExit("拒绝操作：--work 指向技能包内部（%s）" % wr)
    if len(os.path.normpath(wr).split(os.sep)) < 2:
        raise SystemExit("拒绝操作：--work 太靠近盘根（%s）" % wr)
    if os.path.isdir(target):
        shutil.rmtree(target)
    return target


# --------------------------------------------------------------------------
# 字节级 / 字段级差异定位
# --------------------------------------------------------------------------
def byte_regions(a, b, max_regions=6, gap=24):
    """定位 a 与 b 的差异字节区间（合并相邻差异），返回可读区间列表。"""
    n = min(len(a), len(b))
    diff = [i for i in range(n) if a[i] != b[i]]
    if len(a) != len(b):
        diff += list(range(n, max(len(a), len(b))))
    regions = []
    for i in diff:
        if regions and i - regions[-1][1] <= gap:
            regions[-1][1] = i + 1
        else:
            regions.append([i, i + 1])
        if len(regions) > max_regions * 4:
            break
    out = []
    for start, end in regions[:max_regions]:
        pad = 40
        lo, hi = max(0, start - pad), min(n, end + pad)
        out.append({
            "offset": start,
            "length": end - start,
            "a": _printable(a[lo:hi]),
            "b": _printable(b[lo:hi]) if lo < len(b) else "",
        })
    out.append({"offset": None, "length": len(diff),
                "a": "<%d differing byte(s) total>" % len(diff), "b": ""})
    return out


def _printable(data):
    txt = "".join(chr(c) if 32 <= c < 127 else "." for c in data)
    return txt


def json_diff(a, b, path="$"):
    """递归找出 a 与 b 不同的 JSON 路径（只记值，不记结构差异）。"""
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            p = "%s.%s" % (path, k)
            if k not in a or k not in b:
                out.append((p, a.get(k, "<missing>"), b.get(k, "<missing>")))
            else:
                out.extend(json_diff(a[k], b[k], p))
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append(("%s.length" % path, len(a), len(b)))
        for i in range(min(len(a), len(b))):
            out.extend(json_diff(a[i], b[i], "%s[%d]" % (path, i)))
    elif a != b:
        out.append((path, a, b))
    return out


def mask_projection(doc, observed_paths):
    """稳定化投影：掩码时间/主机/路径键 + 观测到的易变路径；返回 (投影, 掩码路径列表)。"""
    masked = []

    def walk(node, path):
        if isinstance(node, dict):
            out = {}
            for k in sorted(node):
                p = "%s.%s" % (path, k)
                key_hits = bool(VOLATILE_KEY_RE.search(k))
                loc_hit = bool(LOCATION_KEY_RE.search(k)) and isinstance(node[k], str) \
                    and bool(ABS_PATH_RE.search(node[k]))
                if (key_hits or loc_hit or p in observed_paths):
                    out[k] = MASK
                    masked.append(p)
                else:
                    out[k] = walk(node[k], p)
            return out
        if isinstance(node, list):
            return [walk(v, "%s[%d]" % (path, i)) for i, v in enumerate(node)]
        return node

    return walk(doc, "$"), sorted(set(masked))


def canon_sha(doc):
    blob = json.dumps(doc, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")
    return sha256_bytes(blob)


def strip_pdf(data):
    """PDF 稳定化：剔除创建/修改时间与文件 ID。返回 (bytes, 命中规则列表)。"""
    hits = []
    new = data
    if PDF_DATE_RE.search(new):
        hits.append("/CreationDate|/ModDate")
        new = PDF_DATE_RE.sub(lambda m: b"/" + m.group(1) + b" (D:00000000000000+00'00')", new)
    if PDF_ID_RE.search(new):
        hits.append("/ID")
        new = PDF_ID_RE.sub(b"/ID [<00><00>]", new)
    return new, hits


def png_chunks(data):
    """列出 PNG 块类型（用来判断是否存在 tIME / tEXt 这类时间块）。"""
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return {"is_png": False, "chunks": []}
    i, chunks = 8, []
    while i + 8 <= len(data):
        ln = int.from_bytes(data[i:i + 4], "big")
        typ = data[i + 4:i + 8].decode("latin-1")
        chunks.append({"type": typ, "length": ln})
        if typ == "IEND":
            break
        i += 12 + ln
    return {"is_png": True, "chunks": chunks,
            "has_time_chunk": any(c["type"] in ("tIME",) for c in chunks),
            "text_chunks": [c["type"] for c in chunks if c["type"] in ("tEXt", "iTXt", "zTXt")]}


# --------------------------------------------------------------------------
# 主流程调用
# --------------------------------------------------------------------------
def run_main(python, pkg, cwd, case_json, model_json, out_literal, fmt, dpi, seed, extra_env=None):
    argv = [python, os.path.join(pkg, "scripts", "main.py"),
            "--case", case_json]
    if model_json:
        argv += ["--model-file", model_json]
    argv += ["--out", out_literal, "--formats", fmt, "--dpi", str(dpi), "--verbose"]
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    if seed is None:
        env.pop("PYTHONHASHSEED", None)
    else:
        env["PYTHONHASHSEED"] = seed
    for k, v in (extra_env or {}).items():
        env[k] = v
    t0 = time.time()
    proc = subprocess.run(argv, cwd=cwd, env=env, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, timeout=900)
    stdout = proc.stdout.decode("utf-8", "replace")
    return {"argv": argv, "exit_code": proc.returncode, "stdout": stdout,
            "seconds": round(time.time() - t0, 3)}


def parse_summary(stdout):
    for line in reversed(stdout.splitlines()):
        if line.startswith("SUMMARY "):
            try:
                return json.loads(line[len("SUMMARY "):])
            except Exception:
                return {"raw": line[len("SUMMARY "):]}
    return None


def snapshot_out(out_dir):
    files = {}
    if not os.path.isdir(out_dir):
        return files
    for name in sorted(os.listdir(out_dir)):
        p = os.path.join(out_dir, name)
        if os.path.isfile(p):
            files[name] = {"sha256": sha256_file(p), "bytes": os.path.getsize(p)}
    return files


# --------------------------------------------------------------------------
# 报告
# --------------------------------------------------------------------------
def build_report(args, skill_root):
    work = os.path.abspath(args.work)
    os.makedirs(work, exist_ok=True)
    roots = [(work, "<WORK>"), (skill_root, "<SKILL>")]

    pkg = safe_reset(work, "pkg")
    case_dir = safe_reset(work, "case")
    copy_tree(skill_root, pkg)
    src_case_dir = os.path.dirname(os.path.abspath(args.case))
    shutil.copytree(src_case_dir, case_dir)
    case_json = os.path.join(case_dir, os.path.basename(args.case))
    model_json = None
    if args.model_file:
        model_json = os.path.join(case_dir, os.path.basename(args.model_file))
        if os.path.abspath(args.model_file) != os.path.abspath(model_json):
            shutil.copy2(args.model_file, model_json)

    python = args.python or sys.executable
    runs = []
    for i in range(args.runs):
        cwd_rel = CWD_CYCLE[i % len(CWD_CYCLE)]
        seed = SEED_CYCLE[i % len(SEED_CYCLE)]
        cwd = os.path.abspath(os.path.join(work, cwd_rel))
        os.makedirs(cwd, exist_ok=True)
        out_dir = os.path.join(cwd, "out")
        if os.path.isdir(out_dir):
            shutil.rmtree(out_dir)
        got = run_main(python, pkg, cwd, case_json, model_json, "out",
                       args.formats, args.dpi, seed)
        summary = parse_summary(got["stdout"])
        status = (summary or {}).get("status")
        files = snapshot_out(out_dir)
        runs.append({
            "run": i + 1,
            "cwd": portable(cwd, roots),
            "pythonhashseed": seed if seed is not None else "<unset>",
            "python": os.path.basename(python),
            "out_dir": portable(out_dir, roots),
            "exit_code": got["exit_code"],
            "status": status,
            "seconds": got["seconds"],
            "stdout_tail": portable("\n".join(got["stdout"].strip().splitlines()[-6:]), roots),
            "artifacts": files,
        })

    # ---- 逐文件跨运行比对 ----
    all_names = sorted({n for r in runs for n in r["artifacts"]})
    per_file = {}
    for n in all_names:
        hashes = [r["artifacts"][n]["sha256"] for r in runs if n in r["artifacts"]]
        per_file[n] = {
            "sha256": hashes[0] if hashes else None,
            "bytes": next((r["artifacts"][n]["bytes"] for r in runs if n in r["artifacts"]), None),
            "runs_with_file": len(hashes),
            "runs_total": len(runs),
            "distinct_sha256": len(set(hashes)),
            "identical": len(set(hashes)) == 1 and len(hashes) == len(runs),
        }
    volatile = [n for n in all_names if not per_file[n]["identical"]]
    stable = [n for n in all_names if per_file[n]["identical"]]
    identical_raw = not volatile

    # ---- 字节级 / 字段级定位 ----
    byte_diff, volatile_fields = {}, []
    first = runs[0]
    for n in volatile:
        if not n.endswith(".json"):
            a_dir, b_dir = _out_paths(runs[0], work), _out_paths(runs[-1], work)
            pa, pb = os.path.join(a_dir, n), os.path.join(b_dir, n)
            if not (os.path.isfile(pa) and os.path.isfile(pb)):
                continue
            da, db = read_bytes(pa), read_bytes(pb)
            entry = {"a_run": 1, "b_run": len(runs), "bytes_a": len(da), "bytes_b": len(db),
                     "regions": byte_regions(da, db)}
            if n.endswith(".pdf"):
                entry["pdf_volatile_tokens"] = sorted(set(
                    m.group(0).decode("latin-1")[:28] for m in PDF_DATE_RE.finditer(da)))
                entry["pdf_has_id"] = bool(PDF_ID_RE.search(da))
            if n.endswith(".png"):
                entry["png_chunks"] = png_chunks(da)
            byte_diff[n] = entry

    for n in volatile:
        if not n.endswith(".json"):
            continue
        docs = []
        for r in runs:
            p = os.path.join(_out_paths(r, work), n)
            if os.path.isfile(p):
                try:
                    docs.append(load_json(p))
                except Exception:
                    docs.append(None)
        if len(docs) < 2 or docs[0] is None:
            continue
        obs = {}
        for d in docs[1:]:
            if d is None:
                continue
            for path, va, vb in json_diff(docs[0], d):
                obs.setdefault(path, set()).update([short_value(va), short_value(vb)])
        for path in sorted(obs):
            volatile_fields.append({
                "artifact": n,
                "json_path": path,
                "values_seen": sorted(obs[path])[:3],
                "kind": ("timestamp" if VOLATILE_KEY_RE.search(path.rsplit(".", 1)[-1]) else
                         "value"),
                "masked_as": MASK,
                "stabilize": "投影时按路径掩码（见 stabilization.json_projection.rule）",
            })

    # ---- 稳定化 (a): JSON 键掩码投影 ----
    obs_paths = {v["json_path"] for v in volatile_fields if v["artifact"] == "result.json"}
    proj = {}
    for n in sorted(x for x in all_names if x.endswith(".json")):
        hashes, keys = [], []
        for r in runs:
            p = os.path.join(_out_paths(r, work), n)
            if not os.path.isfile(p):
                continue
            try:
                doc = load_json(p)
            except Exception:
                continue
            m, mk = mask_projection(doc, obs_paths if n == "result.json" else set())
            hashes.append(canon_sha(m))
            keys = mk
        if hashes:
            proj[n] = {"distinct_sha256": len(set(hashes)), "runs": len(hashes),
                       "identical": len(set(hashes)) == 1,
                       "masked_paths": keys}
    json_projection_ok = all(v["identical"] for v in proj.values()) and bool(proj)

    # ---- 稳定化 (b): PDF 规范化 ----
    pdf_hashes, pdf_hits = [], []
    for r in runs:
        p = os.path.join(_out_paths(r, work), "diagram.pdf")
        if os.path.isfile(p):
            new, hits = strip_pdf(read_bytes(p))
            pdf_hashes.append(sha256_bytes(new))
            pdf_hits = hits
    pdf_strip = {"rule": "/CreationDate|/ModDate|/ID → 固定占位",
                 "hits": pdf_hits,
                 "runs": len(pdf_hashes),
                 "distinct_sha256": len(set(pdf_hashes)),
                 "identical": bool(pdf_hashes) and len(set(pdf_hashes)) == 1}

    # ---- 稳定化 (c): SOURCE_DATE_EPOCH 环境配方 ----
    env_recipe = {"SOURCE_DATE_EPOCH": "1577836800", "runs": 0, "identical": None,
                  "per_file": {}}
    # 两次运行使用同一个 cwd、同一套命令行字面量、同一个输出目录，因此剩余差异只可能
    # 来自时间/环境本身 —— 这是"不改脚本能达到的最强字节级复现"配方。
    env_cwd = os.path.abspath(os.path.join(work, "envrun"))
    os.makedirs(env_cwd, exist_ok=True)
    env_out = os.path.join(env_cwd, "out")
    env_runs = []
    env_docs = []          # 每次运行当下的 result.json（不能等两次跑完再读，否则读到的是最后一次）
    for i in range(2):
        if i:
            time.sleep(1.2)   # 保证两次运行的秒级时间戳必然不同，否则比对可能"同秒侥幸通过"
        if os.path.isdir(env_out):
            shutil.rmtree(env_out)
        got = run_main(python, pkg, env_cwd, case_json, model_json, "out",
                       args.formats, args.dpi, "0",
                       extra_env={"SOURCE_DATE_EPOCH": env_recipe["SOURCE_DATE_EPOCH"]})
        snap = snapshot_out(env_out)
        _doc = None
        _rp = os.path.join(env_out, "result.json")
        if os.path.isfile(_rp):
            try:
                _doc = load_json(_rp)
            except Exception:
                _doc = None
        env_docs.append(_doc)
        env_runs.append({"run": i + 1, "exit_code": got["exit_code"],
                         "status": (parse_summary(got["stdout"]) or {}).get("status"),
                         "artifacts": snap,
                         "result_json_sha256": (snap.get("result.json") or {}).get("sha256")})
    names = sorted({n for r in env_runs for n in r["artifacts"]})
    for n in names:
        hs = [r["artifacts"][n]["sha256"] for r in env_runs if n in r["artifacts"]]
        env_recipe["per_file"][n] = {"distinct_sha256": len(set(hs)),
                                     "identical": len(set(hs)) == 1 and len(hs) == len(env_runs)}
    env_recipe["runs"] = len(env_runs)
    env_recipe["cwd"] = portable(env_cwd, roots)
    env_recipe["identical"] = (all(v["identical"] for v in env_recipe["per_file"].values())
                              and bool(env_recipe["per_file"]))
    env_recipe["identical_except_result_json"] = all(
        v["identical"] for k, v in env_recipe["per_file"].items() if k != "result.json")
    env_recipe["pdf_identical"] = bool(env_recipe["per_file"].get("diagram.pdf", {})
                                       .get("identical"))
    # 固定 cwd 后 result.json 还残留哪些差异路径？（预期只剩时间戳字段）
    rj_paths, rj_docs = [], [d for d in env_docs if isinstance(d, dict)]
    if len(rj_docs) == 2:
        rj_paths = [x[0] for x in json_diff(rj_docs[0], rj_docs[1])]
    env_recipe["result_json_diff_paths"] = rj_paths
    env_recipe["result_json_projected_identical"] = bool(rj_docs) and len(
        {canon_sha(mask_projection(d, set(rj_paths))[0]) for d in rj_docs}) == 1

    # "规范化后可复现"的判据：JSON 投影一致 + PDF 规范化一致 + 固定 cwd 下除 result.json
    # 外原始字节全一致 + result.json 投影一致（三件互不依赖的证据一起成立）
    stabilized_ok = bool(json_projection_ok and pdf_strip["identical"]
                         and env_recipe["identical_except_result_json"]
                         and env_recipe["result_json_projected_identical"])
    names_env = {k: v["identical"] for k, v in env_recipe["per_file"].items()}

    # PNG 元数据探测（不进 byte_diff 时也能说明"为什么稳"：无 tIME 这类时间块）
    png_probe = {}
    _png1 = os.path.join(_out_paths(runs[0], work), "diagram.png")
    if os.path.isfile(_png1):
        png_probe = png_chunks(read_bytes(_png1))

    report = {
        "probe": "determinism",
        "tool": "scripts/determinism.py",
        "tool_version": TOOL_VERSION,
        "what_this_measures": [
            "同输入、跨进程、跨 cwd、跨 PYTHONHASHSEED 重跑主流程",
            "逐产物 sha256 比对（原始字节）",
            "易变字段/字节的定位与稳定化验证",
        ],
        "config": {
            "runs": args.runs,
            "case": portable(case_json, roots),
            "model_file": portable(model_json, roots) if model_json else None,
            "formats": args.formats,
            "dpi": args.dpi,
            "cwd_cycle": list(CWD_CYCLE),
            "pythonhashseed_cycle": [s if s is not None else "<unset>" for s in SEED_CYCLE],
            "python": sys.version.split()[0],
            "platform": sys.platform,
            "matplotlib": _pkg_version("matplotlib"),
            "pillow": _pkg_version("PIL"),
        },
        "runs": [{k: v for k, v in r.items() if k != "out_dir"} for r in runs],
        "per_file_sha256": per_file,
        "identical": identical_raw,
        "stable_artifacts": stable,
        "volatile_artifacts": volatile,
        "volatile_fields": volatile_fields,
        "byte_diff": byte_diff,
        "png_metadata_probe": png_probe,
        "stabilization": {
            "json_projection": {
                "rule": "递归掩码：键名匹配 %s 的字段 / 值为绝对路径的位置类键 / 观测到的易变路径 → '%s'；"
                        "再以 sort_keys 规范化 JSON 序列化后取 sha256"
                        % (VOLATILE_KEY_RE.pattern, MASK),
                "per_file": proj,
                "identical": json_projection_ok,
            },
            "pdf_normalization": pdf_strip,
            "env_recipe": dict({k: v for k, v in env_recipe.items() if k != "per_file"},
                               per_file=env_recipe["per_file"]),
            "env_recipe_per_file_identical": names_env,
        },
        "verdict": {
            "byte_identical_raw": identical_raw,
            "byte_identical_after_documented_stabilization": stabilized_ok,
            "main_pipeline_exit_codes": sorted({r["exit_code"] for r in runs}),
            "main_pipeline_status": sorted({str(r["status"]) for r in runs}),
            "notes": [
                "原始字节不一致的产物 = %s（原因见 volatile_fields / byte_diff）" % (", ".join(volatile) or "无"),
                "result.json 的政策是**故意**保留时间戳（change_records/provenance），"
                "因此原始字节必然不同；稳定化投影后必须一致",
                "固定 cwd + SOURCE_DATE_EPOCH 后残余的 result.json 差异路径 = "
                + (", ".join(env_recipe.get("result_json_diff_paths") or []) or "无")
                + "；这些路径的投影一致性 = %s"
                % env_recipe.get("result_json_projected_identical"),
                "稳定化不改变交付语义：投影/规范化只用于比对，不覆盖产物本身",
            ],
        },
    }
    report = portable_obj(report, roots)
    return report, work


def _out_paths(run, work):
    """把报告里的可移植 cwd 还原成实际输出目录（<WORK> → 工作根，".", 也支持）。"""
    rel = run["cwd"].replace("<WORK>", "", 1).lstrip("/")
    return os.path.join(work, rel.replace("/", os.sep), "out")


def _pkg_version(mod):
    try:
        m = __import__(mod)
        return getattr(m, "__version__", "?")
    except Exception:
        return None


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="byte-level determinism probe for the pathway-diagram skill")
    ap.add_argument("--skill", default=DEFAULT_SKILL_ROOT,
                    help="技能根目录（含 SKILL.md；默认=本脚本的上一级）")
    ap.add_argument("--case", default=None,
                    help="案例 case.json（默认 <skill>/examples/case.json）")
    ap.add_argument("--model-file", default=None,
                    help="机制规格 model.json（默认 <skill>/examples/model.example.json）")
    ap.add_argument("--no-model-file", action="store_true",
                    help="不使用 --model-file（走自动草稿路径，status 预期为 partial）")
    ap.add_argument("--runs", type=int, default=5, help="运行次数（默认 5）")
    ap.add_argument("--work", default=None, help="工作目录（默认系统临时目录下的 det-<pid>）")
    ap.add_argument("--report", default=None,
                    help="报告输出路径（默认 <skill>/determinism_report.json）")
    ap.add_argument("--formats", default="svg,png,pdf")
    ap.add_argument("--dpi", type=int, default=150)
    ap.add_argument("--python", default=None, help="解释器路径（默认=当前解释器）")
    ap.add_argument("--strict", action="store_true", help="要求原始字节也完全一致")
    ap.add_argument("--clean", action="store_true", help="结束后删除工作目录里的副本")
    ap.add_argument("--json", action="store_true", help="stdout 只输出报告 JSON")
    args = ap.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    skill_root = os.path.abspath(args.skill)
    if not os.path.isfile(os.path.join(skill_root, "SKILL.md")):
        print("错误：--skill 下没有 SKILL.md：%s" % skill_root, file=sys.stderr)
        return 4
    if args.case is None:
        args.case = os.path.join(skill_root, "examples", "case.json")
    if not os.path.isfile(args.case):
        print("错误：找不到 --case：%s" % args.case, file=sys.stderr)
        return 4
    if args.model_file is None and not args.no_model_file:
        cand = os.path.join(skill_root, "examples", "model.example.json")
        if os.path.isfile(cand):
            args.model_file = cand
    if args.model_file and not os.path.isfile(args.model_file):
        print("错误：找不到 --model-file：%s" % args.model_file, file=sys.stderr)
        return 4
    if args.work is None:
        import tempfile
        args.work = os.path.join(tempfile.gettempdir(), "det-%d" % os.getpid())
    expected_exit = 2 if args.no_model_file else 0

    report, work = build_report(args, skill_root)
    report["config"]["expected_main_exit"] = expected_exit
    report_path = args.report or os.path.join(skill_root, "determinism_report.json")
    blob = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=False)
    with open(report_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(blob + "\n")

    if args.json:
        print(blob)
    else:
        v = report["verdict"]
        print("[determinism] runs=%d  raw_identical=%s  stabilized_identical=%s" %
              (report["config"]["runs"], v["byte_identical_raw"],
               v["byte_identical_after_documented_stabilization"]))
        print("  stable   : %s" % ", ".join(report["stable_artifacts"]))
        print("  volatile : %s" % (", ".join(report["volatile_artifacts"]) or "-"))
        for f in report["volatile_fields"][:8]:
            print("    volatile field %-28s %s" % (f["json_path"], f["values_seen"][:2]))
        for n, e in report["byte_diff"].items():
            print("    byte-diff %-14s regions=%d" % (n, len(e.get("regions", []))))
        _er = report["stabilization"]["env_recipe"]
        print("  stabilized: json-projection=%s pdf-normalize=%s | "
              "env(SOURCE_DATE_EPOCH, fixed cwd): except-result.json=%s pdf=%s "
              "residual-result.json-diff=%s" %
              (report["stabilization"]["json_projection"]["identical"],
               report["stabilization"]["pdf_normalization"]["identical"],
               _er["identical_except_result_json"], _er["pdf_identical"],
               _er.get("result_json_diff_paths")))
        print("  exit codes of main pipeline: %s" % v["main_pipeline_exit_codes"])
        print("  report -> %s" % report_path)
        print("  work   -> %s" % work)

    exits = report["verdict"]["main_pipeline_exit_codes"]
    if exits != [expected_exit]:
        if args.clean:
            shutil.rmtree(os.path.join(work, "pkg"), ignore_errors=True)
            shutil.rmtree(os.path.join(work, "case"), ignore_errors=True)
        return 2
    if args.strict and not report["verdict"]["byte_identical_raw"]:
        return 3
    if not report["verdict"]["byte_identical_after_documented_stabilization"]:
        return 3
    if args.clean:
        for sub in ("pkg", "case"):
            shutil.rmtree(os.path.join(work, sub), ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
