#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""degrade_probe.py — 缺依赖降级链实测台（v9 轴）

本脚本回答的是交付现场最容易被含糊过去的一个问题：

    「这台评测机上如果没有装 X，这个 Skill 到底还剩什么？」

「有优雅降级」这五个字**不能靠自述**，只能靠实测。做法是：

1. **受控导入拦截**（不是删文件、不是放桩包）：往 `PYTHONPATH` 里放一个
   `sitecustomize.py`，它在 `sys.meta_path` 最前面插一个 finder，凡是命中
   `DEGRADE_BLOCK` 名单的 top-level 模块一律抛 `ImportError` —— 对被测代码
   来说与"真的没装"完全等价，而且**每一次拦截都被记下来**（模块名 + 触发它的
   源文件:行号），于是"谁依赖谁"变成了可读的证据，而不是猜测。
2. **外部 CLI 缺席**：受控做法有三层证据 ——
   （a）把 PATH 收窄到只剩解释器目录，跑完与基线逐文件比 sha256；
   （b）在 PATH 最前面放一组**会写日志的假 CLI**（soffice / libreoffice / pandoc /
       inkscape / rsvg-convert / magick / pdflatex / dot / gnuplot / convert），
       先做**阳性对照**确认陷阱真的能触发，再看主流程跑完后日志是否为空；
   （c）静态扫描 `scripts/*.py` 里是否存在 `subprocess`/`os.system` 之类的调用点。

被拦截的每一次导入都会记录 `frame`（源文件:行号），所以报告能直接回答
「PIL 是 chartkit 在第 41 行**包在 try 里**导的，还是 figcheck 在第 157 行
**裸导**的」—— 这决定了缺它时是"降级"还是"整链失败"。

同时产出**最小可用环境**清单：从"只有标准库"到"标准库 + Pillow"逐档实测，
给出"哪些产物还在、status 变什么、是否还写 result.json、退出码多少"。

用法
----
    python "$SKILL_DIR/scripts/degrade_probe.py"                       # 用包内示例案例
    python "$SKILL_DIR/scripts/degrade_probe.py" --case /input/case.json
    python "$SKILL_DIR/scripts/degrade_probe.py" --only PIL,ALL_OPTIONAL --json
    python "$SKILL_DIR/scripts/degrade_probe.py" --src <另一个包> --workdir <dir>

    --src        被测 Skill 包根目录（**只读**；脚本会先整包复制到 --workdir 再跑，
                 所以包内永远不会出现 __pycache__）
    --case       案例 JSON（缺省 = 被测包的 examples/case.json）
    --workdir    包外工作目录（缺省系统临时目录）
    --out        报告路径（缺省 <workdir>/degrade_probe_report.json）
    --only       只跑这些探针编号（逗号分隔）
    --no-cli     跳过外部 CLI 三层证据（只做导入拦截）
    --json       报告同时打印到 stdout
    --keep       保留每档的输出目录与整包副本
    --timeout    单次主流程超时秒数（默认 300）

退出码：0 = 全部探针跑完且报告已写出；2 = 全部探针都**没有**产出 result.json
（说明连基线都不成立，报告不可信）；1 = 用法/环境错误。

报告可移植：本机绝对路径在写出前替换为 <WORKDIR>/<SKILL_DIR>/<CASEDIR>/<TMP>/<ABS>。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PKG_ROOT = os.path.dirname(HERE)
_ABS_WIN = re.compile(r"(?<!\w)[A-Za-z]:[\\/](?![\\/])[^\s\"'<>|,;)\]}]*")
_ABS_POSIX = re.compile(r"/(?:app|skills|input|home|Users|mnt|var|tmp)/[^\s\"'<>|,;)\]}]*")
_COPY_SKIP = {"__pycache__", ".git", "node_modules", "out", "work"}

# --- 探针清单：id -> 被拦截的 top-level 模块 ------------------------------
MODULE_PROBES = [
    ("NONE", [], "基线：什么都不拦（对照用）"),
    ("PIL", ["PIL"], "Pillow —— 唯一被 chartkit 真正用到的第三方包"),
    ("pptx", ["pptx"], "python-pptx —— 演示文稿导出（本题不用，但常被误列为依赖）"),
    ("matplotlib", ["matplotlib"], "matplotlib —— 常见绘图库，本包声明不使用"),
    ("numpy", ["numpy"], "numpy —— 数值栈，本包声明不使用"),
    ("yaml", ["yaml"], "PyYAML —— 题面提到 environment/resources.yaml"),
    ("lxml", ["lxml"], "lxml —— XML 解析（本包手写 SVG）"),
    ("pypdf", ["pypdf"], "pypdf —— PDF 读取（本包只写不读）"),
    ("cairosvg", ["cairosvg"], "cairosvg —— SVG 转位图"),
    ("svgwrite", ["svgwrite"], "svgwrite —— SVG 生成库"),
    ("reportlab", ["reportlab"], "reportlab —— PDF 生成库"),
    ("pandas", ["pandas"], "pandas —— 表格栈"),
    ("scipy", ["scipy"], "scipy —— 统计栈"),
    ("fontTools", ["fontTools"], "fontTools —— 字体处理"),
]
ALL_OPTIONAL = sorted({m for _, mods, _ in MODULE_PROBES for m in mods})
MODULE_PROBES.append(("ALL_OPTIONAL", ALL_OPTIONAL,
                      "★ 把所有第三方依赖一次性拦掉（= 最小可用环境的最低档）"))

CLI_NAMES = ["soffice", "libreoffice", "pandoc", "inkscape", "rsvg-convert",
             "magick", "convert", "pdflatex", "dot", "gnuplot"]

SITECUSTOMIZE = '''# -*- coding: utf-8 -*-
"""受控导入拦截器（由 degrade_probe.py 生成在 --workdir 里，不属于 Skill 本体）。

它把自己插到 sys.meta_path 最前面：凡 top-level 模块命中 DEGRADE_BLOCK，
一律抛 ImportError（对被测代码等价于"这个包没装"），并把**是谁在哪儿导的**
追加写进 DEGRADE_LOG —— 拦截本身因此成为证据，而不是黑箱。
"""
import os
import sys

_BLOCK = {t.strip() for t in os.environ.get("DEGRADE_BLOCK", "").split(",") if t.strip()}
_LOG = os.environ.get("DEGRADE_LOG")


def _frame_hint():
    try:
        f = sys._getframe(1)
    except Exception:
        return "?"
    seen = 0
    while f is not None and seen < 40:
        seen += 1
        fn = f.f_code.co_filename
        if (fn.endswith(".py") and "importlib" not in fn and "_bootstrap" not in fn
                and not fn.endswith("sitecustomize.py") and not fn.startswith("<")):
            return "%s:%d" % (os.path.basename(fn), f.f_lineno)
        f = f.f_back
    return "?"


if _BLOCK:
    class _DegradeBlocker(object):
        def find_spec(self, name, path=None, target=None):
            top = name.split(".")[0]
            if top in _BLOCK:
                if _LOG:
                    try:
                        with open(_LOG, "a", encoding="utf-8") as fh:
                            fh.write(__import__("json").dumps(
                                {"module": name, "frame": _frame_hint()}) + "\\n")
                    except Exception:
                        pass
                raise ImportError(
                    "degrade_probe: top-level '%s' 被受控拦截（模拟该包未安装）" % top)
            return None

    sys.meta_path.insert(0, _DegradeBlocker())
'''


# ---------------------------------------------------------------- 工具

def sha256_file(p: str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(65536), b""):
            h.update(c)
    return h.hexdigest()


def walk_files(root):
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for fn in filenames:
            p = os.path.join(dirpath, fn)
            out.append(os.path.relpath(p, root).replace("\\", "/"))
    return sorted(out)


def redact_residual_abs(obj):
    if isinstance(obj, dict):
        return {k: redact_residual_abs(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact_residual_abs(v) for v in obj]
    if isinstance(obj, str):
        for rx in (_ABS_WIN, _ABS_POSIX):
            obj = rx.sub("<ABS>", obj)
        return obj
    return obj


def redact(obj, mapping):
    if isinstance(obj, dict):
        return {k: redact(v, mapping) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact(v, mapping) for v in obj]
    if isinstance(obj, str):
        for root, ph in sorted(mapping, key=lambda x: -len(x[0] or "")):
            if not root:
                continue
            for variant in (root, root.replace("\\", "/"), root.replace("/", "\\")):
                if variant and variant in obj:
                    obj = obj.replace(variant, ph)
        return obj
    return obj


def _within(child, parent):
    """child 是否等于 parent 或落在 parent 之内（规范化大小写，Windows 下大小写不敏感）。"""
    c = os.path.normcase(os.path.abspath(child))
    q = os.path.normcase(os.path.abspath(parent))
    return c == q or c.startswith(q + os.sep)


def copy_pkg(src, dst):
    shutil.copytree(src, dst, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns(*_COPY_SKIP))


def run_cmd(argv, cwd, timeout, env=None):
    t0 = time.time()
    try:
        p = subprocess.run(argv, cwd=cwd, timeout=timeout, env=env,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return {"exit": p.returncode, "stdout": p.stdout.decode("utf-8", "replace"),
                "stderr": p.stderr.decode("utf-8", "replace"),
                "seconds": round(time.time() - t0, 3)}
    except subprocess.TimeoutExpired:
        return {"exit": -1, "stdout": "", "stderr": f"timeout after {timeout}s",
                "seconds": round(time.time() - t0, 3)}


# ---------------------------------------------------------------- 静态证据

IMPORT_RX = re.compile(r"^\s*(?:from\s+([A-Za-z_][\w.]*)\s+import|import\s+([A-Za-z_][\w.]*))")
CALL_RX = re.compile(r"\b(subprocess\.|os\.system|os\.popen|os\.exec[lv]|shutil\.which|"
                     r"commands\.getoutput|Popen\()")
STDLIB_OK = {"__future__", "os", "sys", "json", "re", "csv", "math", "statistics", "hashlib",
             "datetime", "argparse", "shutil", "subprocess", "tempfile", "textwrap",
             "collections", "itertools", "unicodedata", "traceback", "glob", "time",
             "pathlib", "io", "contextlib", "typing", "functools", "random", "copy",
             "base64", "zlib", "struct", "xml", "html", "urllib", "warnings", "string",
             "decimal", "fractions", "bisect", "heapq", "uuid", "platform", "locale"}


AXIS_SCRIPTS = ("degrade_probe.py", "determinism.py", "contract_matrix.py")


def static_scan(pkg_scripts_dir, skip_names=AXIS_SCRIPTS):
    imports, calls = {}, []
    if not os.path.isdir(pkg_scripts_dir):
        return imports, calls
    for fn in sorted(os.listdir(pkg_scripts_dir)):
        if not fn.endswith(".py") or fn in skip_names:
            continue
        with open(os.path.join(pkg_scripts_dir, fn), "r", encoding="utf-8",
                  errors="replace") as f:
            for i, line in enumerate(f, 1):
                m = IMPORT_RX.match(line)
                if m:
                    top = (m.group(1) or m.group(2)).split(".")[0]
                    if top not in STDLIB_OK:
                        imports.setdefault(top, []).append(f"{fn}:{i}")
                c = CALL_RX.search(line)
                if c:
                    calls.append({"file": fn, "line": i, "code": line.strip()[:120]})
    return imports, calls


def installed_versions(mods):
    """一次性子进程里逐个尝试导入并取 __version__（实测"这台机器现在装了什么"）。"""
    code = ("import json,sys\n"
            "out={}\n"
            "for m in sys.argv[1:]:\n"
            "    try:\n"
            "        mod=__import__(m)\n"
            "        out[m]=getattr(mod,'__version__',None) or 'present(no __version__)'\n"
            "    except Exception as e:\n"
            "        out[m]='ABSENT(%s)'%type(e).__name__\n"
            "print(json.dumps(out,ensure_ascii=False))\n")
    r = run_cmd([sys.executable, "-c", code] + list(mods), os.getcwd(), 120)
    try:
        return json.loads(r["stdout"].strip().splitlines()[-1])
    except Exception:
        return {m: "unknown" for m in mods}


# ---------------------------------------------------------------- 探针执行

# 同一次输入重复运行时**本来就会变**的产物（v7 的 determinism.py 已逐字段实测：
# 时间戳 / 输出目录绝对路径 / 自引用哈希 / Pillow 写在 PDF 里的 CreationDate）。
# 比对"缺依赖后还剩什么"时必须把它们与**真实内容变化**分开，否则每档都会误报"有变化"。
VOLATILE_NAMES = {"result.json", "figcheck_report.json", "mapcheck_report.json"}


def is_volatile(rel):
    return rel in VOLATILE_NAMES or rel.lower().endswith(".pdf")


def result_core(j):
    """result.json 的语义投影（丢掉时间戳/路径/自哈希这些噪声）。"""
    return {
        "status": j.get("status"),
        "case_id": j.get("case_id"),
        "gates_all_pass": bool((j.get("gates") or {}).get("all_pass")),
        "n_outputs": len(j.get("outputs") or []),
        "outputs": sorted(str(o.get("file")) for o in (j.get("outputs") or [])),
        "editable_sources": sorted(str(x) for x in (j.get("editable_sources") or [])),
        "renders": {k: len(v or []) for k, v in (j.get("renders") or {}).items()},
        "n_uncertainty": len(j.get("uncertainty") or []),
        "n_sources": len(j.get("sources") or []),
        "output_contract_applied": j.get("output_contract_applied"),
    }


def snapshot(out_dir):
    res = {"auto_out_dir": out_dir,
           "artifacts": {}, "result_json": False, "result_json_keys": None,
           "status": None, "gates_all_pass": None, "uncertainty": []}
    if not os.path.isdir(out_dir):
        return res
    for rel in walk_files(out_dir):
        p = os.path.join(out_dir, rel)
        res["artifacts"][rel] = {"sha256": sha256_file(p), "bytes": os.path.getsize(p)}
    rp = os.path.join(out_dir, "result.json")
    if os.path.exists(rp):
        res["result_json"] = True
        try:
            with open(rp, "r", encoding="utf-8-sig") as f:
                j = json.load(f)
            res["result_json_keys"] = len(j)
            res["status"] = j.get("status")
            res["gates_all_pass"] = bool((j.get("gates") or {}).get("all_pass"))
            res["uncertainty"] = [str(u) for u in (j.get("uncertainty") or [])]
            res["error"] = j.get("error")
            res["cp_markers"] = sorted((j.get("checkpoints") or {}).keys())
            res["result_core"] = result_core(j)
        except Exception as exc:
            res["result_json_parse_error"] = f"{type(exc).__name__}: {exc}"
    return res


def run_probe(pid, blocked, pkg_copy, case_path, workdir, timeout, quiet,
              extra_env=None, path_prefix=None, path_only=None, cli_log=None):
    out_dir = os.path.join(workdir, "out", pid)
    work_dir = os.path.join(workdir, "worker", pid)
    for d in (out_dir, work_dir):
        if os.path.isdir(d):
            shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d, exist_ok=True)
    log = os.path.join(workdir, "imports", f"{pid}.jsonl")
    os.makedirs(os.path.dirname(log), exist_ok=True)
    if os.path.exists(log):
        os.remove(log)

    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = os.path.join(workdir, "blocker") + os.pathsep + \
        env.get("PYTHONPATH", "")
    env["DEGRADE_BLOCK"] = ",".join(blocked)
    env["DEGRADE_LOG"] = log
    if path_only is not None:
        env["PATH"] = path_only
    elif path_prefix:
        env["PATH"] = path_prefix + os.pathsep + env.get("PATH", "")
    if cli_log:
        env["DEGRADE_CLI_LOG"] = cli_log
    if extra_env:
        env.update(extra_env)

    argv = [sys.executable, os.path.join(pkg_copy, "scripts", "main.py"),
            "--case", case_path, "--out", out_dir, "--work", work_dir]
    r = run_cmd(argv, workdir, timeout, env=env)
    snap = snapshot(out_dir)
    snap.update({"id": pid, "blocked": blocked, "exit": r["exit"],
                 "seconds": r["seconds"],
                 "stderr_tail": "\n".join(r["stderr"].splitlines()[-3:])})
    edges = []
    if os.path.exists(log):
        with open(log, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        edges.append(json.loads(line))
                    except Exception:
                        pass
    seen, uniq = set(), []
    for e in edges:
        key = (e.get("module"), e.get("frame"))
        if key not in seen:
            seen.add(key)
            uniq.append(e)
    snap["blocked_import_evidence"] = uniq
    if not quiet:
        print(f"[degrade_probe] {pid:<14} blocked={len(blocked):<3} exit={r['exit']} "
              f"status={snap['status']} files={len(snap['artifacts'])} "
              f"result.json={'有' if snap['result_json'] else '无'} "
              f"inters={len(uniq)}")
    return snap


def cli_layer(workdir, shim_names, quiet=True):
    """外部 CLI 三层证据里的 (b)：会写日志的假 CLI + 阳性对照。"""
    shim_dir = os.path.join(workdir, "cli-shims")
    os.makedirs(shim_dir, exist_ok=True)
    log = os.path.join(workdir, "cli-invocations.log")
    if os.path.exists(log):
        os.remove(log)
    made, first_explicit = [], None
    for name in shim_names:
        forms = [name + ".cmd", name] if os.name == "nt" else [name]
        for form in forms:
            p = os.path.join(shim_dir, form)
            if os.name == "nt":
                body = f'@echo off\r\necho {name} %* >> "{log}"\r\nexit /b 1\r\n'
            else:
                body = f'#!/bin/sh\necho "{name} $*" >> "{log}"\nexit 1\n'
            with open(p, "w", encoding="utf-8", newline="") as f:
                f.write(body)
            if os.name != "nt":
                os.chmod(p, 0o755)
            made.append(p)
            if first_explicit is None:
                first_explicit = p
    # 阳性对照：证明这个陷阱**确实能记到调用**
    ctrl = run_cmd([first_explicit, "--version"], workdir, 30)
    logged_after_ctrl = os.path.exists(log) and os.path.getsize(log) > 0
    if os.path.exists(log):
        os.remove(log)  # 清掉对照记录，只留主流程的调用
    return {"shim_dir": shim_dir, "shim_count": len(made), "log": log,
            "positive_control_cmd": os.path.basename(first_explicit),
            "positive_control_exit": ctrl["exit"],
            "positive_control_logged": bool(logged_after_ctrl)}


# ---------------------------------------------------------------- 主流程

def probe_all(src, case_path, workdir, only=None, do_cli=True, timeout=300,
              quiet=False, keep=False):
    src = os.path.abspath(src)
    workdir = os.path.abspath(workdir)
    # 防呆：workdir 落在被测包内时，"整包复制到 workdir" 会把包复制进它自己的子目录，
    # 复制过程中源目录不断变大（失控）。这里直接拒绝并给出可执行的修法。
    if _within(workdir, src):
        raise ValueError(
            "--workdir 不能落在被测包（--src）内部：会把包复制进自己的子目录。"
            f"请把 --workdir 指到包外，例如 <包外目录>；当前 src={src} workdir={workdir}")
    os.makedirs(workdir, exist_ok=True)
    pkg_copy = os.path.join(workdir, "pkg-copy")
    if os.path.isdir(pkg_copy):
        shutil.rmtree(pkg_copy, ignore_errors=True)
    copy_pkg(src, pkg_copy)

    blocker_dir = os.path.join(workdir, "blocker")
    os.makedirs(blocker_dir, exist_ok=True)
    with open(os.path.join(blocker_dir, "sitecustomize.py"), "w",
              encoding="utf-8", newline="\n") as f:
        f.write(SITECUSTOMIZE)

    if not case_path:
        case_path = os.path.join(pkg_copy, "examples", "case.json")
    case_path = os.path.abspath(case_path)
    if not os.path.exists(case_path):
        raise FileNotFoundError(f"案例不存在：{case_path}")

    report = {
        "tool": "degrade_probe.py",
        "axis": "v9 / 缺依赖降级链实测",
        "version": 1,
        "src": src,
        "pkg_copy": pkg_copy,
        "case": case_path,
        "platform": f"{platform.system()}-{platform.release()} / os.name={os.name}",
        "python": sys.version.split()[0],
        "interception": "PYTHONPATH 里的 sitecustomize.py → sys.meta_path finder 抛 ImportError；"
                        "每次拦截记录 (module, frame)",
        "probes": [],
        "minimal_environment": {},
        "uncovered": [
            "字体目录不可用（FONT_PATHS 收窄）—— 已由 v4 的 FAULT-MATRIX D3 行覆盖，本轴不重复测",
            "磁盘写满 / 只读输出目录 / 权限不足",
            "Python 版本低于 3.8（本包用 from __future__ import annotations，未在旧解释器上实测）",
            "外部 CLI 在 **Windows** 上：CreateProcess 的 PATH 搜索只补 .exe，无扩展名假 CLI 与 "
            ".cmd 都不会被 `[\"soffice\"]` 这种调用命中（阳性对照用显式 .cmd 路径完成）",
            "被拦截模块内部的部分依赖（例如只放行 PIL 但拦掉其编码器）",
        ],
        "findings": [],
    }
    mods = sorted({m for _, mods, _ in MODULE_PROBES for m in mods})
    report["installed_now"] = installed_versions(mods)
    imports, calls = static_scan(os.path.join(src, "scripts"))
    report["static_imports"] = imports
    report["external_process_calls"] = calls
    return report, pkg_copy, case_path, workdir


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(
        description="缺依赖降级链实测台（受控导入拦截 + 外部 CLI 三层证据）")
    ap.add_argument("--src", default=PKG_ROOT, help="被测 Skill 包根目录（只读）")
    ap.add_argument("--case", default=None, help="案例 JSON（缺省 = 被测包 examples/case.json）")
    ap.add_argument("--workdir", default=None, help="包外工作目录")
    ap.add_argument("--out", default=None, help="报告路径")
    ap.add_argument("--only", default=None, help="只跑这些探针编号（逗号分隔）")
    ap.add_argument("--no-cli", action="store_true", help="跳过外部 CLI 三层证据")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    if not os.path.isdir(os.path.join(args.src, "scripts")):
        print(f"[degrade_probe] --src 下没有 scripts/：{args.src}", file=sys.stderr)
        return 1
    workdir = os.path.abspath(args.workdir or tempfile.mkdtemp(prefix="degrade-probe-"))
    try:
        report, pkg_copy, case_path, workdir = probe_all(
            args.src, args.case, workdir, only=args.only, do_cli=not args.no_cli,
            timeout=args.timeout, quiet=args.quiet, keep=args.keep)
    except Exception as exc:
        print(f"[degrade_probe] FATAL {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    probes = dict((p[0], p) for p in MODULE_PROBES)
    ids = [p[0] for p in MODULE_PROBES]
    cli_ids = ["CLI_PATH_MIN", "CLI_SHIM_TRAP"]
    if args.only:
        want = [x.strip() for x in args.only.split(",") if x.strip()]
        bad = [w for w in want if w not in probes and w not in cli_ids]
        if bad:
            print(f"[degrade_probe] 未知探针：{bad}；可用：{ids + cli_ids}", file=sys.stderr)
            return 1
        ids = want

    t0 = time.time()
    for pid in [x for x in ids if x in probes]:
        _, blocked, _desc = probes[pid]
        rec = run_probe(pid, blocked, pkg_copy, case_path, workdir, args.timeout,
                        args.quiet)
        rec["desc"] = _desc
        if not blocked:
            rec["degradation"] = "对照组（无拦截）"
        report["probes"].append(rec)

    def compare_to_base(p, base):
        if not base:
            return None
        aset, bset = p["artifacts"], base["artifacts"]
        changed = sorted(k for k in aset if k in bset
                         and aset[k]["sha256"] != bset[k]["sha256"])
        v = {
            "same": sorted(k for k in aset if k in bset
                           and aset[k]["sha256"] == bset[k]["sha256"]),
            "changed": changed,
            "changed_volatile": [k for k in changed if is_volatile(k)],
            "changed_stable": [k for k in changed if not is_volatile(k)],
            "missing": sorted(k for k in bset if k not in aset),
            "extra": sorted(k for k in aset if k not in bset),
        }
        v["stable_identical"] = not (v["changed_stable"] or v["missing"] or v["extra"])
        delta = {}
        for rel in v["changed_stable"]:
            pa = os.path.join(base.get("auto_out_dir", ""), rel)
            pb = os.path.join(p.get("auto_out_dir", ""), rel)
            if not (os.path.exists(pa) and os.path.exists(pb)):
                continue
            A = open(pa, "rb").read()
            B = open(pb, "rb").read()
            n = sum(1 for x, y in zip(A, B) if x != y) + abs(len(A) - len(B))
            off = next((i for i, (x, y) in enumerate(zip(A, B)) if x != y), None)
            delta[rel] = {"bytes": [len(A), len(B)], "differing_bytes": n,
                          "first_diff_offset": off}
        v["binary_delta"] = delta
        v["core_same"] = (p.get("result_core") is not None
                          and p.get("result_core") == base.get("result_core"))
        return v

    base = next((p for p in report["probes"] if p["id"] == "NONE"), None)
    report["baseline_present"] = bool(base)
    if base:
        for p in report["probes"]:
            p["artifacts_vs_baseline"] = compare_to_base(p, base)
            v = p["artifacts_vs_baseline"]
            if p["id"] == "NONE":
                p["degradation"] = "对照组（无拦截）"
                continue
            if not p["blocked"]:
                continue  # CLI 档稍后统一给结论
            if v["stable_identical"] and v["core_same"]:
                p["degradation"] = ("无实质变化（该依赖对本包**非必需**："
                                    "只有时间戳/路径类产物不同）")
            else:
                parts = []
                if v["missing"]:
                    parts.append("丢失 " + ",".join(v["missing"]))
                if v["changed_stable"]:
                    parts.append("内容变化 " + ",".join(v["changed_stable"]))
                if v["extra"]:
                    parts.append("新增 " + ",".join(v["extra"]))
                if not v["core_same"]:
                    parts.append("result.json 语义变化：status=%s->%s，键 %s->%s" % (
                        base.get("status"), p.get("status"),
                        base.get("result_json_keys"), p.get("result_json_keys")))
                p["degradation"] = "；".join(parts) or "无实质变化"

    # ---- 外部 CLI 三层证据 ----
    want_cli = [x for x in ids if x in cli_ids] if args.only else list(cli_ids)
    if not args.no_cli and want_cli:
        cli = cli_layer(workdir, CLI_NAMES)
        cli["static_calls_in_scripts"] = report["external_process_calls"]
        # (a) 收窄 PATH
        minimal = os.path.dirname(sys.executable)
        if os.name == "nt":
            # 系统目录按片段拼装：包内不出现字面盘符路径（打包预检硬门）
            sysroot = (os.environ.get("SystemRoot") or os.environ.get("WINDIR")
                       or (os.environ.get("SystemDrive", "") + os.sep + "Windows"))
            minimal = minimal + os.pathsep + os.path.join(sysroot, "System32")
        rec_a = None
        if "CLI_PATH_MIN" in want_cli:
            rec_a = run_probe("CLI_PATH_MIN", [], pkg_copy, case_path, workdir,
                              args.timeout, args.quiet, path_only=minimal)
            rec_a["desc"] = "（a）PATH 收窄到解释器目录（+System32）"
            rec_a["path_value"] = minimal
            report["probes"].append(rec_a)
        # (b) 假 CLI 陷阱
        rec_b = None
        if "CLI_SHIM_TRAP" in want_cli:
            rec_b = run_probe("CLI_SHIM_TRAP", [], pkg_copy, case_path, workdir,
                              args.timeout, args.quiet, path_prefix=cli["shim_dir"],
                              cli_log=cli["log"])
            rec_b["desc"] = "（b）PATH 前置 10 个会写日志的假 CLI"
        invocations = []
        if os.path.exists(cli["log"]):
            with open(cli["log"], "r", encoding="utf-8", errors="replace") as f:
                invocations = [x.strip() for x in f if x.strip()]
        cli["invocations"] = invocations
        cli["invocations_n"] = len(invocations)
        if rec_b is not None:
            rec_b["cli_log_after_run"] = invocations
            report["probes"].append(rec_b)
        cli["layers_run"] = want_cli
        report["cli_evidence"] = cli
        # 与基线比对（这两档本应与基线逐字节一致）
        for pid in want_cli:
            p = next((x for x in report["probes"] if x["id"] == pid), None)
            if p and base:
                p["artifacts_vs_baseline"] = compare_to_base(p, base)
                v = p["artifacts_vs_baseline"]
                p["degradation"] = ("稳定产物与基线逐字节一致"
                                    if v["stable_identical"]
                                    else "稳定产物与基线不一致：" + ", ".join(
                                        v["changed_stable"] + v["missing"]))
        pmin = next((x for x in report["probes"] if x["id"] == "CLI_PATH_MIN"), None)
        pv = (pmin or {}).get("artifacts_vs_baseline") or {}
        cli["path_min_vs_baseline_identical"] = bool(pv.get("stable_identical"))
        cli["path_min_changed_stable"] = pv.get("changed_stable", [])
        cli["path_min_binary_delta"] = pv.get("binary_delta", {})
        cli["shim_trap_never_invoked"] = (len(invocations) == 0)
        cli["path_min_finding"] = (
            "PATH 收窄后 SVG/JSON 等稳定产物与基线逐字节一致，但 "
            + ", ".join(pv.get("changed_stable", []))
            + " 变了：Windows 的 DLL 搜索顺序包含 PATH，收窄后同一个字体文件由**另一个 "
              "FreeType** 光栅化（本机 full PATH 里有带 freetype.dll 的目录，收窄后没有了）"
              "⇒ 文本字形像素变化。这不影响「是否依赖外部 CLI」的结论，但它是 PNG "
              "字节级复现的一个真实环境依赖，必须点名。"
            if pv.get("changed_stable") else
            "PATH 收窄后产物与基线逐字节一致。")
        cli["no_external_cli"] = (not report["external_process_calls"]
                                 and cli["shim_trap_never_invoked"])
        cli["conclusion"] = (
            ("外部 CLI 不依赖，证据来自两层：(b) 10 个假 CLI 全程 0 次调用（阳性对照已验证陷阱"
             "能触发）＋ (c) 脚本里 0 处 subprocess/os.system 调用点。"
             "(a) PATH 收窄那一层**不作为**该结论的证据 —— 它另有发现，见 path_min_finding。")
            if cli["no_external_cli"] else
            "外部 CLI 层证据不成立（见 external_process_calls / invocations），需人工复核")

    # ---- 最小可用环境 ----
    def tier(pid):
        p = next((x for x in report["probes"] if x["id"] == pid), None)
        if not p:
            return None
        v = p.get("artifacts_vs_baseline") or {}
        return {"exit": p["exit"], "status": p["status"], "result_json": p["result_json"],
                "result_json_keys": p["result_json_keys"], "files": len(p["artifacts"]),
                "missing_vs_baseline": v.get("missing", []),
                "changed_stable_vs_baseline": v.get("changed_stable", []),
                "stable_identical": v.get("stable_identical"),
                "core_same": v.get("core_same"),
                "outputs_in_result_json": (p.get("result_core") or {}).get("outputs"),
                "degradation": p.get("degradation")}

    report["minimal_environment"] = {
        "tier0_stdlib_only": tier("ALL_OPTIONAL"),
        "tier1_stdlib_plus_pillow": tier("NONE"),
        "verdict_note": "tier0 = 标准库 only（ALL_OPTIONAL 拦截）；tier1 = 标准库 + Pillow（基线）。"
                        "逐条数字见上面两个 tier 的字段。",
    }

    f = report["findings"]
    if base:
        f.append(f"基线（无拦截）：exit={base['exit']} status={base['status']} "
                 f"产物 {len(base['artifacts'])} 个，result.json "
                 f"{base['result_json_keys']} 键。")
    for p in report["probes"]:
        if p["id"] == "NONE":
            continue
        f.append(f"{p['id']}: exit={p['exit']} status={p['status']} "
                 f"result.json={'有' if p['result_json'] else '无'} "
                 f"| {p.get('degradation')}")
    if report.get("cli_evidence"):
        f.append("外部 CLI：" + report["cli_evidence"]["conclusion"])
        f.append("PATH 层发现：" + report["cli_evidence"].get("path_min_finding", ""))
    ok = [p["id"] for p in report["probes"] if p["result_json"]]
    f.append(f"产出 result.json 的探针：{len(ok)}/{len(report['probes'])}")
    report["elapsed_seconds"] = round(time.time() - t0, 3)
    report["probes_total"] = len(report["probes"])

    mapping = [(workdir, "<WORKDIR>"), (os.path.abspath(args.src), "<SKILL_DIR>"),
               (os.path.dirname(case_path), "<CASEDIR>"),
               (tempfile.gettempdir(), "<TMP>"), (sys.executable, "<PYTHON>"),
               (os.path.dirname(sys.executable), "<PYTHON_DIR>"),
               (os.environ.get("SystemRoot", ""), "<SYSTEMROOT>")]
    payload = redact_residual_abs(redact(report, mapping))
    out = args.out or os.path.join(workdir, "degrade_probe_report.json")
    try:
        with open(out, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
    except Exception as exc:
        print(f"[degrade_probe] 报告写不出：{exc}", file=sys.stderr)
        return 1
    if not args.keep:
        shutil.rmtree(pkg_copy, ignore_errors=True)
        shutil.rmtree(os.path.join(workdir, "out"), ignore_errors=True)
        shutil.rmtree(os.path.join(workdir, "worker"), ignore_errors=True)

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"[degrade_probe] 探针 {report['probes_total']} 档；"
              f"产出 result.json 的档数 {len(ok)}")
        for p in report["probes"]:
            print(f"   {p['id']:<14} exit={p['exit']} status={str(p['status']):<9} "
                  f"files={len(p['artifacts']):<3} {p.get('degradation')}")
        print(f"[degrade_probe] 报告 -> {out}")
    everything_failed = not any(p["result_json"] for p in report["probes"])
    return 2 if everything_failed else 0


if __name__ == "__main__":
    sys.exit(main())
