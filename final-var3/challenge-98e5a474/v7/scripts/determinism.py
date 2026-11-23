#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""determinism.py -- 确定性与字节级可复现实测器（可运行的确定性矩阵执行器）。

本脚本回答一个**可证伪**的问题：同一份输入、同一份技能包，在不同进程 /
不同工作目录 / 不同 PYTHONHASHSEED 下跑出来的产物，**哪些字节必须相同、
哪些字节允许不同、不同由谁负责**。

它做三件事：

1. 把技能包复制到包外 scratch，开 N 个**独立子进程**跑 `scripts/main.py`
   （每次换 cwd、换 PYTHONHASHSEED，最后两次额外设 `SOURCE_DATE_EPOCH`），
   对每个 run 的**全部产物**算 sha256 与字节数；
2. 逐文件比对，给出三档结论：raw 全等 / 自然组（未设 SOURCE_DATE_EPOCH）全等 /
   归一化后全等，并把**真正不同的字段**逐条抽出来（result.json 的 JSON 路径、
   PDF 的 /CreationDate 之类 token、以及归类不了的字节偏移）；
3. 把结论写成机器可读的 `determinism_report.json`，供第三方复跑核对。

设计原则（决定了它为什么能当证据用）：

* **只动包外副本**：绝不修改技能包本身；`--out` 指向包内时直接拒绝（exit 2）。
* **不改被测代码**：只通过 cwd / 环境变量 / 子进程隔离制造差异，不 patch 逻辑。
* **不伪造数据**：报告里的每个 sha256、每个字段值都来自子进程的真实产物；
  归类不了的差异如实记为 `unclassified`，绝不"解释掉"。
* **故意不稳定 vs 意外不稳定**：前者（时间戳、绝对路径）必须逐条点名并给出
  稳定化办法；后者（归一化后仍不同）一律判失败（exit 1）。

用法（建议在包外运行，产物写到包外）：

    python scripts/determinism.py --skill-root <技能根> --out <包外目录>
    python scripts/determinism.py --skill-root . --out /tmp/det --runs 6 --json
    python scripts/determinism.py --list
    python scripts/determinism.py --skill-root . --out /tmp/det --quiet

退出码：0 = 每个 run 都成功（exit 0 + 有 result.json），且**归一化后逐字节全等**
（差异只剩被点名的故意不稳定字段）；1 = 有 run 失败，或归一化后仍存在未解释的
字节差异（真缺陷）；2 = 参数/环境错误。
"""

import argparse
import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

try:  # 窄编码控制台（GBK）不得让 --help / 日志崩溃
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ROOT = os.path.dirname(HERE)
PY = sys.executable or "python"

# 默认的"稳定化时间"：2026-01-01T00:00:00Z。
# matplotlib 的 PDF backend 会用 SOURCE_DATE_EPOCH 覆写 /CreationDate，
# 因此把它固定下来可以让 PDF 逐字节可复现（本包实测：见 references/DETERMINISM.md）。
DEFAULT_FIXED_TIME = "2026-01-01T00:00:00+0000"
DEFAULT_SDE = "1767225600"          # = 2026-01-01T00:00:00Z

# 运行矩阵：profile 只影响 cwd 与两组环境变量
RUN_PLAN = [
    {"profile": "natural",    "cwd": "cwd-a",           "seed": "0"},
    {"profile": "natural",    "cwd": "cwd-b",           "seed": "0"},
    {"profile": "natural",    "cwd": "cwd-c/deep/nest", "seed": "1"},
    {"profile": "natural",    "cwd": "cwd-d",           "seed": None},
    {"profile": "stabilized", "cwd": "cwd-e",           "seed": None},
    {"profile": "stabilized", "cwd": "cwd-f",           "seed": "7"},
]

# 归一化规则：文件 → 要抹掉的东西（用于 identical_after_normalization）
NORMALIZATION_RULES = [
    {"file": "result.json", "target": "generated_at",
     "how": "JSON 路径 generated_at 归一化为 <FIXED_TIME>（--fixed-time 已固定；"
            "未传时它记录真实生成时间，属故意不稳定）"},
    {"file": "result.json", "target": "artifacts[].abspath",
     "how": "JSON 里任何落在本次 scratch/out 之下的绝对路径归一化为 <RUN>/<rel>"
            "（它记录的是「这次跑在哪」，不是内容）"},
    {"file": "*.json", "target": "scratch/out 绝对路径",
     "how": "递归替换所有等于 scratch 前缀的字符串（正反斜杠都替换）"},
    {"file": "figure.pdf", "target": "/CreationDate",
     "how": "字节级替换 /CreationDate (...) 为 /CreationDate (<N>)；"
            "设 SOURCE_DATE_EPOCH 后本字段本来就不再变化（stabilized 组实测 raw 全等）"},
    {"file": "*.pdf", "target": "/ModDate, /ID",
     "how": "同样的字节级替换（本包实测这两个 token 不出现，规则保留以便复用）"},
    {"file": "*.pdf", "target": "xref 偏移 / startxref 数值",
     "how": "PDF 把每个对象的字节偏移写进 xref 表；时间戳字符串长度一变，"
            "xref 的 10 位偏移与 startxref 数值就整体位移。因此跨 profile 比对时"
            "把 [0-9]{10} [0-9]{5} [nf] 与 startxref 数字替换为占位符 —— "
            "这是「结构归一化」，不是「忽略差异」：替换后仍逐字节全等才算通过"},
]

PDF_TOKEN_PATTERNS = [
    (re.compile(rb"/CreationDate\s*\(([^)]*)\)"), "/CreationDate"),
    (re.compile(rb"/ModDate\s*\(([^)]*)\)"), "/ModDate"),
    (re.compile(rb"/ID\s*\[([^\]]*)\]"), "/ID"),
]

TEXT_EXT = (".json", ".svg", ".txt", ".md", ".csv")


# --------------------------------------------------------------------------
# 小工具
# --------------------------------------------------------------------------
def log(msg, *args):
    print("[det] " + (msg % args if args else msg), flush=True)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(blob):
    return hashlib.sha256(blob).hexdigest()


def read_bytes(path):
    with open(path, "rb") as fh:
        return fh.read()


def dump_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def tail(text, n=6, width=180):
    lines = [l for l in (text or "").splitlines() if l.strip()]
    return [l[:width] for l in lines[-n:]]


def in_root(path, root):
    """path 是否落在 root 之内（用于拒绝把产物写进技能包）。"""
    a = os.path.abspath(path).rstrip("\\/").lower()
    b = os.path.abspath(root).rstrip("\\/").lower()
    return a == b or a.startswith(b + os.sep) or a.startswith(b + "/")


def walk_files(root):
    out = []
    for r, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for n in sorted(names):
            if n.endswith(".pyc"):
                continue
            p = os.path.join(r, n)
            out.append((os.path.relpath(p, root).replace("\\", "/"), p))
    return sorted(out)


def normalise_bytes(rel, blob, prefixes, fixed_time):
    """按 NORMALIZATION_RULES 把一次运行的产物归一化成可比字节。"""
    for pre in prefixes:
        for form in (pre, pre.replace("\\", "/"), pre.replace("/", "\\")):
            blob = blob.replace(form.encode("utf-8", "replace"),
                                b"<RUN>")
            blob = blob.replace(form.encode("utf-8", "replace").replace(b"\\", b"\\\\"),
                                b"<RUN>")
    if rel.lower().endswith(".pdf"):
        for pat, _name in PDF_TOKEN_PATTERNS:
            blob = pat.sub(lambda m: pat.pattern.split(rb"\s")[0] + b" (<N>)",
                           blob)
        # PDF 是"带字节偏移的结构"：时间戳字符串长度一变，xref 偏移与
        # startxref 数值就跟着变。要跨 profile 比较，必须把这两类数字也归一化
        # （否则会把"偏移变了"误判成"内容不稳定"）。
        blob = re.sub(rb"startxref\s*\d+", b"startxref <N>", blob)
        blob = re.sub(rb"\d{10} \d{5} [nf]", b"<OFF> <GEN> X", blob)
        return blob
    if rel.lower().endswith(".json"):
        try:
            obj = json.loads(blob.decode("utf-8"))
        except Exception:
            return blob
        obj = _norm_json(obj, prefixes, fixed_time)
        return json.dumps(obj, ensure_ascii=False, sort_keys=True,
                          indent=2).encode("utf-8")
    return blob


def _norm_json(node, prefixes, fixed_time):
    if isinstance(node, dict):
        return {k: ("<FIXED_TIME>" if k == "generated_at" else
                    _norm_json(v, prefixes, fixed_time))
                for k, v in node.items()}
    if isinstance(node, list):
        return [_norm_json(v, prefixes, fixed_time) for v in node]
    if isinstance(node, str):
        s = node
        for pre in prefixes:
            for form in (pre, pre.replace("\\", "/"), pre.replace("/", "\\")):
                if s.startswith(form):
                    s = "<RUN>" + s[len(form):]
        if re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", s):
            s = "<FIXED_TIME>"
        return s
    return node


def json_paths_diff(a, b, path="", out=None):
    """结构化 diff：返回两棵 JSON 树里所有不同的路径与两侧取值。"""
    if out is None:
        out = []
    if type(a) is not type(b):
        out.append({"path": path or "/", "left": repr(a)[:200],
                    "right": repr(b)[:200], "kind": "type"})
        return out
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append({"path": (path + "/" + k),
                            "left": repr(a.get(k))[:200],
                            "right": repr(b.get(k))[:200], "kind": "key"})
                continue
            json_paths_diff(a[k], b[k], path + "/" + k, out)
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append({"path": path, "left": "len=%d" % len(a),
                        "right": "len=%d" % len(b), "kind": "length"})
            return out
        for i, (x, y) in enumerate(zip(a, b)):
            json_paths_diff(x, y, "%s/%d" % (path, i), out)
    elif a != b:
        out.append({"path": path or "/", "left": repr(a)[:200],
                    "right": repr(b)[:200], "kind": "value"})
    return out


def token_diff(blob_a, blob_b):
    """从两份字节里抽出会变动的 token（PDF 时间戳等），返回命中的字段名。"""
    hits = []
    for pat, name in PDF_TOKEN_PATTERNS:
        ma, mb = pat.search(blob_a), pat.search(blob_b)
        if ma and mb and ma.group(1) != mb.group(1):
            hits.append({"field": name, "values": [
                ma.group(1).decode("latin-1", "replace"),
                mb.group(1).decode("latin-1", "replace")]})
    return hits


def first_diff_excerpt(blob_a, blob_b, width=48):
    n = min(len(blob_a), len(blob_b))
    for i in range(n):
        if blob_a[i] != blob_b[i]:
            lo = max(0, i - 12)
            return {"offset": i,
                    "left": blob_a[lo:i + width].decode("latin-1", "replace"),
                    "right": blob_b[lo:i + width].decode("latin-1", "replace")}
    if len(blob_a) != len(blob_b):
        return {"offset": n, "left": "len=%d" % len(blob_a),
                "right": "len=%d" % len(blob_b)}
    return None


# --------------------------------------------------------------------------
# 一个 run
# --------------------------------------------------------------------------
def run_one(index, plan, scratch, skill_root, case_rel, args):
    cwd = os.path.join(scratch, "run%d" % index, plan["cwd"])
    os.makedirs(cwd, exist_ok=True)
    pkg = os.path.join(scratch, "pkg-run%d" % index)
    shutil.copytree(skill_root, pkg,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    out = os.path.join(scratch, "run%d" % index, "out")
    os.makedirs(out, exist_ok=True)

    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.pop("SOURCE_DATE_EPOCH", None)
    if plan["seed"] is None:
        env.pop("PYTHONHASHSEED", None)
    else:
        env["PYTHONHASHSEED"] = plan["seed"]
    if plan["profile"] == "stabilized":
        env["SOURCE_DATE_EPOCH"] = args.source_date_epoch

    cmd = [PY, "-B", os.path.join(pkg, "scripts", "main.py"),
           "--case", os.path.join(pkg, case_rel),
           "--out", out, "--fixed-time", args.fixed_time]
    t0 = time.time()
    proc = subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    dt = time.time() - t0
    rec = {
        "index": index, "profile": plan["profile"],
        "cwd": "<scratch>/run%d/%s" % (index, plan["cwd"]),
        "pythonhashseed": plan["seed"] if plan["seed"] is not None else "(unset)",
        "source_date_epoch": env.get("SOURCE_DATE_EPOCH", "(unset)"),
        "command": "python -B <pkg>/scripts/main.py --case <pkg>/%s "
                   "--out <out> --fixed-time %s" % (case_rel, args.fixed_time),
        "exit": proc.returncode,
        "seconds": round(dt, 2),
        "stdout_tail": tail(proc.stdout.decode("utf-8", "replace")),
        "files": {},
    }
    for rel, p in walk_files(out):
        rec["files"][rel] = {"sha256": sha256_file(p),
                             "bytes": os.path.getsize(p)}
        if rel.lower().endswith(".pdf"):
            blob = read_bytes(p)
            for pat, name in PDF_TOKEN_PATTERNS:
                m = pat.search(blob)
                if m:
                    rec.setdefault("pdf_tokens", {})[rel + name] = \
                        m.group(1).decode("latin-1", "replace")
    rp = os.path.join(out, "result.json")
    rec["result_json"] = os.path.isfile(rp)
    if rec["result_json"]:
        try:
            res = load_json(rp)
            rec["status"] = res.get("status")
            rec["spec_sha16"] = (res.get("determinism") or {}).get("spec_sha16")
            rec["generated_at"] = res.get("generated_at")
        except Exception as exc:                     # pragma: no cover
            rec["status"] = "<unreadable: %r>" % (exc,)
    else:
        rec["status"] = None
    return rec, out, pkg


# --------------------------------------------------------------------------
# 主流程
# --------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(
        description="确定性与字节级可复现实测器（多个独立进程 × 不同 cwd × "
                    "不同 PYTHONHASHSEED × 可选 SOURCE_DATE_EPOCH）")
    ap.add_argument("--skill-root", default=DEFAULT_ROOT,
                    help="技能根目录（默认：本脚本上一级）")
    ap.add_argument("--case", default=None,
                    help="case.json 相对技能根的路径（默认 examples/case.json）")
    ap.add_argument("--out", default=None,
                    help="输出目录（**必须在技能包之外**）；报告写到 <out>/determinism_report.json")
    ap.add_argument("--runs", type=int, default=6,
                    help="跑几次（默认 6：前 4 次 natural，后 2 次 stabilized）")
    ap.add_argument("--fixed-time", default=DEFAULT_FIXED_TIME,
                    help="传给 main.py 的 --fixed-time（默认固定值）")
    ap.add_argument("--source-date-epoch", default=DEFAULT_SDE,
                    help="stabilized 组使用的 SOURCE_DATE_EPOCH（默认 1767225600 = 2026-01-01Z）")
    ap.add_argument("--json", action="store_true", help="stdout 也打印 JSON 报告")
    ap.add_argument("--quiet", action="store_true", help="只打印结论行")
    ap.add_argument("--keep", action="store_true", help="保留 scratch（排查用）")
    ap.add_argument("--list", action="store_true", help="只列运行矩阵，不执行")
    args = ap.parse_args(argv)

    skill_root = os.path.abspath(args.skill_root)
    if not os.path.isdir(os.path.join(skill_root, "scripts")):
        log("FATAL: %s 不像技能根（缺 scripts/）", skill_root)
        return 2
    case_rel = args.case or os.path.join("examples", "case.json")
    if os.path.isabs(case_rel):
        case_rel = os.path.relpath(case_rel, skill_root)
    case_rel = case_rel.replace("\\", "/")
    if not os.path.isfile(os.path.join(skill_root, case_rel)):
        log("FATAL: case 不存在：%s", os.path.join(skill_root, case_rel))
        return 2

    plan = RUN_PLAN[:max(1, min(args.runs, len(RUN_PLAN)))]
    if args.list:
        print("运行矩阵（%d 次）：" % len(plan))
        for i, p in enumerate(plan, 1):
            print("  run%d  profile=%-10s cwd=<scratch>/run%d/%s  PYTHONHASHSEED=%s"
                  "  SOURCE_DATE_EPOCH=%s"
                  % (i, p["profile"], i, p["cwd"],
                     p["seed"] if p["seed"] is not None else "(unset)",
                     args.source_date_epoch if p["profile"] == "stabilized"
                     else "(unset)"))
        print("说明：前 %d 次 natural（只变 cwd/seed），后 %d 次 stabilized（额外设 "
              "SOURCE_DATE_EPOCH）" % (sum(1 for p in plan if p["profile"] == "natural"),
                                     sum(1 for p in plan if p["profile"] == "stabilized")))
        return 0

    if not args.out:
        log("FATAL: --out 必填（报告与 scratch 都要写在包外）")
        return 2
    out_dir = os.path.abspath(args.out)
    if in_root(out_dir, skill_root):
        log("FATAL: --out 不能指向技能包内部（%s）；本脚本只动包外副本", out_dir)
        return 2
    os.makedirs(out_dir, exist_ok=True)

    scratch = tempfile.mkdtemp(prefix="sse-determinism-")
    try:
        runs, outs = [], []
        for i, p in enumerate(plan, 1):
            if not args.quiet:
                log("run%d/%d profile=%s cwd=%s seed=%s", i, len(plan),
                    p["profile"], p["cwd"],
                    p["seed"] if p["seed"] is not None else "(unset)")
            rec, o, _pkg = run_one(i, p, scratch, skill_root, case_rel, args)
            rec["_out"] = o
            runs.append(rec)
            outs.append(o)
            if not args.quiet:
                log("   exit=%s status=%s files=%d result_json=%s",
                    rec["exit"], rec["status"], len(rec["files"]),
                    rec["result_json"])

        # ---- 逐文件比对（raw + 归一化两份读数） ----
        all_rels = sorted({r for rec in runs for r in rec["files"]})
        norm = {}
        for rec in runs:
            for rel, _p in walk_files(rec["_out"]):
                blob = read_bytes(os.path.join(rec["_out"], rel))
                nb = normalise_bytes(rel, blob, [rec["_out"], scratch],
                                     args.fixed_time)
                norm.setdefault(rel, []).append(sha256_bytes(nb))

        nat_idx = [i for i, r in enumerate(runs) if r["profile"] == "natural"]
        sta_idx = [i for i, r in enumerate(runs) if r["profile"] == "stabilized"]

        def _subset(hs):
            return [hs[i] for i in nat_idx]

        def _subset_sta(hs):
            return [hs[i] for i in sta_idx]

        def _same(hs, need_multi=False):
            if need_multi and len(hs) < 2:
                return None
            return len(set(hs)) == 1 and None not in hs

        per_file = {}
        for rel in all_rels:
            hashes = [rec["files"].get(rel, {}).get("sha256") for rec in runs]
            sizes = [rec["files"].get(rel, {}).get("bytes") for rec in runs]
            nh = norm.get(rel, [None] * len(runs))
            if len(nh) < len(runs):
                nh = list(nh) + [None] * (len(runs) - len(nh))
            per_file[rel] = {
                "sha256": hashes,
                "bytes": sizes,
                "sha256_normalised": nh,
                "identical": _same(hashes),
                "identical_natural": _same(_subset(hashes)),
                "identical_natural_normalised": _same(_subset(nh)),
                "identical_stabilized": _same(_subset_sta(hashes), True),
                "identical_stabilized_normalised": _same(_subset_sta(nh), True),
                "identical_after_normalization": _same(nh),
            }

        # ---- volatile_fields：谁在变、为什么 ----
        volatile = []
        for rel in all_rels:
            if per_file[rel]["identical"]:
                continue
            base = runs[0]
            others = [r for r in runs[1:] if r["files"].get(rel)]
            if not others:
                continue
            other = others[0]
            pa = os.path.join(base["_out"], rel)
            pb = os.path.join(other["_out"], rel)
            ba, bb = read_bytes(pa), read_bytes(pb)
            classified = False
            if rel.lower().endswith(".json"):
                try:
                    da, db = json.loads(ba.decode("utf-8")), json.loads(bb.decode("utf-8"))
                    for d in json_paths_diff(da, db)[:12]:
                        volatile.append({
                            "file": rel, "field": d["path"], "kind": "json-" + d["kind"],
                            "values": [d["left"], d["right"]],
                            "reason": _reason_for(rel, d["path"]),
                            "stabilised_by": _stabiliser_for(d["path"]),
                        })
                    classified = True
                except Exception:
                    classified = False
            for hit in token_diff(ba, bb):
                volatile.append({
                    "file": rel, "field": hit["field"], "kind": "byte-token",
                    "values": hit["values"],
                    "reason": _reason_for(rel, hit["field"]),
                    "stabilised_by": _stabiliser_for(hit["field"]),
                })
                classified = True
            # 路径类差异（scratch/out 前缀不同）
            if ba.replace(base["_out"].encode(), b"<RUN>") == \
                    bb.replace(other["_out"].encode(), b"<RUN>"):
                volatile.append({
                    "file": rel, "field": "(output-dir absolute path)",
                    "kind": "path",
                    "values": ["<out of run1>", "<out of run2>"],
                    "reason": "产物字节里嵌了本次运行的输出目录绝对路径"
                              "（result.json 的 artifacts[].abspath）",
                    "stabilised_by": "归一化规则：把落在本次 out/scratch 下的绝对路径替换为 <RUN>",
                })
                classified = True
            if not classified:
                exc = first_diff_excerpt(ba, bb)
                volatile.append({
                    "file": rel, "field": "(unclassified)",
                    "kind": "unclassified",
                    "values": [exc["left"] if exc else "", exc["right"] if exc else ""],
                    "reason": "差异未能归类到已知的故意不稳定字段（时间戳/绝对路径）"
                              "—— 需要人工判断，脚本不替它解释",
                    "stabilised_by": "",
                    "offset": exc.get("offset") if exc else None,
                })

        identical = all(v["identical"] for v in per_file.values())
        identical_natural = all(v["identical_natural"]
                                for v in per_file.values()) if nat_idx else None
        natural_norm = all(v["identical_natural_normalised"]
                           for v in per_file.values()) if nat_idx else None
        stab_ok = (all(v["identical_stabilized_normalised"] is True
                       for v in per_file.values())
                   if len(sta_idx) > 1 else None)
        stab_raw = (all(v["identical_stabilized"] is True
                        for v in per_file.values())
                    if len(sta_idx) > 1 else None)
        identical_norm = all(v["identical_after_normalization"]
                             for v in per_file.values())
        unclassified = [v for v in volatile if v["kind"] == "unclassified"]
        runs_ok = all(r["exit"] == 0 and r["result_json"] for r in runs)

        report = {
            "schema": "sse-determinism/1",
            "skill_root": os.path.basename(skill_root),
            "case": case_rel,
            "fixed_time": args.fixed_time,
            "source_date_epoch": args.source_date_epoch,
            "python": sys.version.split()[0],
            "run_plan": [{"index": i + 1, "profile": p["profile"],
                          "cwd": p["cwd"],
                          "pythonhashseed": p["seed"] if p["seed"] is not None
                          else "(unset)",
                          "source_date_epoch": args.source_date_epoch
                          if p["profile"] == "stabilized" else "(unset)"}
                         for i, p in enumerate(plan)],
            "runs": [{k: v for k, v in rec.items() if not k.startswith("_")}
                     for rec in runs],
            "per_file_sha256": per_file,
            "identical": identical,
            "identical_natural": identical_natural,
            "identical_natural_normalised": natural_norm,
            "identical_stabilized_raw": stab_raw,
            "identical_stabilized": stab_ok,
            "identical_after_normalization": identical_norm,
            "volatile_fields": volatile,
            "unclassified_differences": len(unclassified),
            "stable_files": sorted(r for r, v in per_file.items() if v["identical"]),
            "unstable_files": sorted(r for r, v in per_file.items() if not v["identical"]),
            "normalization_rules": NORMALIZATION_RULES,
            "verdict": _verdict(runs_ok, identical, identical_norm, unclassified),
        }
        rp = os.path.join(out_dir, "determinism_report.json")
        dump_json(rp, report)

        if not args.quiet:
            print("")
            print("  %-28s %-6s %-8s %-9s %s"
                  % ("file", "raw", "nat-raw", "nat-norm", "all-norm"))
            for rel in all_rels:
                v = per_file[rel]
                print("  %-28s %-6s %-8s %-9s %s  (%s)"
                      % (rel, "same" if v["identical"] else "DIFF",
                         "same" if v["identical_natural"] else "DIFF",
                         "same" if v["identical_natural_normalised"] else "DIFF",
                         "same" if v["identical_after_normalization"] else "DIFF",
                         (v["sha256"][0] or "")[:12]))
        log("identical(raw)=%s natural(raw)=%s natural(norm)=%s "
            "stabilized-pair(norm)=%s all(norm)=%s volatile=%d unclassified=%d",
            identical, identical_natural, natural_norm, stab_ok, identical_norm,
            len(volatile), len(unclassified))
        log("verdict: %s", report["verdict"])
        log("wrote %s", rp)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=1))
        return 0 if (runs_ok and identical_norm and not unclassified) else 1
    finally:
        if args.keep:
            log("scratch kept: %s", scratch)
        else:
            shutil.rmtree(scratch, ignore_errors=True)


def _reason_for(rel, field):
    low = field.lower()
    if "abspath" in low or "path" in low:
        return ("记录的是「这次跑在哪里」（输出目录的绝对路径），不是图稿内容 —— "
                "故意不稳定；同一目录重跑则相同")
    if "generated_at" in low:
        return "生成时间戳；--fixed-time 可固定（本脚本默认已固定）"
    if "creationdate" in low:
        return ("PDF 渲染器写入的当日时间戳（matplotlib PDF backend）；"
                "设 SOURCE_DATE_EPOCH 后由该环境变量决定 —— 故意不稳定，可稳定化")
    if "moddate" in low or field == "/ID":
        return "PDF 渲染器写入的文档标识；同源归一化处理"
    if field == "(unclassified)":
        return "未归类差异"
    return "逐次运行的自然差异（见 references/DETERMINISM.md 的逐字段表）"


def _stabiliser_for(field):
    low = field.lower()
    if "generated_at" in low:
        return "--fixed-time <ISO>"
    if "abspath" in low or "path" in low:
        return "归一化：把本次 out/scratch 前缀替换为 <RUN>（scripts/determinism.py 内置规则）"
    if "creationdate" in low or "moddate" in low or field == "/ID":
        return "SOURCE_DATE_EPOCH=<epoch>（本脚本 stabilized 组默认 1767225600）"
    return ""


def _verdict(runs_ok, identical, identical_norm, unclassified):
    if not runs_ok:
        return "AT-LEAST-ONE-RUN-FAILED：有 run 未成功（见 runs[].exit / result_json）"
    if unclassified:
        return ("UNEXPLAINED-DIFFERENCE：归一化后仍有未归类差异，判为意外不稳定"
                "（真缺陷），见 volatile_fields 里 kind=unclassified 的条目")
    if identical:
        return "BYTE-IDENTICAL：全部产物在全部 run 之间逐字节相同（最强结论）"
    if identical_norm:
        return ("BYTE-IDENTICAL-AFTER-DOCUMENTED-NORMALISATION：差异只剩"
                "被逐条点名的故意不稳定字段（时间戳/绝对路径），其余字节全等")
    return "UNSTABLE：存在归一化也解释不了的差异"


if __name__ == "__main__":
    sys.exit(main())
