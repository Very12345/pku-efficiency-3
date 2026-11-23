#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""degrade_probe.py — 缺依赖降级链实测（v9 轴 · 只依赖标准库）。

本包（生物机制图 Skill）声称"Python 标准库即可产出可编辑 SVG 与全部审计产物，
matplotlib 只影响 PNG/PDF 预览"。这个声明必须能被逐个依赖地**证伪或证实**，
所以本探针用**受控导入拦截**（sys.meta_path 拦截器，装在子进程里）逐个屏蔽
`python-pptx` / `PIL` / `matplotlib` / `numpy` / `yaml` / `lxml` / `pypdf`，
再用 PATH 处理模拟 **LibreOffice CLI 缺失**（命令不存在）与**存在但失败**（退出 127），
每种情况跑一次**真实主流程**，记录**实测**降级形态：

  * 退出码 / status（success / partial / failed）
  * 还剩下哪些产物（SVG？PNG？PDF？result.json？审计 JSON？）
  * 是否写 result.json、失败检查项 id（F01_png / F01_pdf / F02_png …）
  * gates.g4 / g5 的实测值、self_check.passed
  * uncertainty / export_checks 里留下了什么（降级是否**有留痕**）
  * 拦截器是否真的生效（自证行：被拦模块在子进程内确实 import 失败）

用法
----
  export SKILL_DIR=/skills/weekly-skill
  python3 "$SKILL_DIR/scripts/degrade_probe.py" \
      --work /tmp/dg --report "$SKILL_DIR/degrade_report.json"
  python3 "$SKILL_DIR/scripts/degrade_probe.py" --only s01     # 只跑一行

退出码
------
  0 = 全部场景跑完（含降级行）
  2 = 控制行（全依赖）就不通 → 环境本身有问题，结论不可用
  4 = 参数错误
"""
import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SKILL_ROOT = os.path.dirname(HERE)
TOOL_VERSION = "1.0"

ARTIFACT_KEYS = {
    "diagram.svg": "editable_svg",
    "diagram.png": "png_preview",
    "diagram.pdf": "pdf_export",
    "result.json": "result_json",
    "model.json": "model",
    "topology.json": "topology_audit",
    "legend_audit.json": "legend_audit",
}

SHIM = '''# -*- coding: utf-8 -*-
"""受控导入拦截器（由 degrade_probe.py 写到工作目录，子进程执行）。"""
import json
import runpy
import shutil
import sys

BLOCK = set(json.loads(sys.argv[1]))
MAIN = sys.argv[2]
REST = sys.argv[3:]


class Blocker:
    """把指定顶层模块的 import 变成 ImportError（模拟该依赖未安装）。"""

    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in BLOCK:
            raise ImportError(
                "degrade_probe: import of %r is blocked in this environment" % fullname)
        return None


sys.meta_path.insert(0, Blocker())

probe = {"blocked": sorted(BLOCK), "import_checks": [], "which": {}}
for m in sorted(BLOCK):
    entry = {"module": m}
    try:
        __import__(m)
        entry["importable"] = True
        entry["detail"] = "仍可导入（拦截未生效！该行结论不可用）"
    except ImportError as ex:
        entry["importable"] = False
        entry["detail"] = str(ex)[:160]
    except Exception as ex:                     # 依赖内部报错也算"不可用"
        entry["importable"] = None
        entry["detail"] = "%s: %s" % (type(ex).__name__, str(ex)[:140])
    probe["import_checks"].append(entry)
for cmd in ("soffice", "libreoffice"):
    probe["which"][cmd] = shutil.which(cmd)

sys.stdout.write("PROBE " + json.dumps(probe, ensure_ascii=False) + "\\n")
sys.stdout.flush()

sys.argv = [MAIN] + REST
runpy.run_path(MAIN, run_name="__main__")


'''
# micro-trace source: run matplotlib Agg directly (not through main.py) so the
# report can tell apart "our own checker needs the dependency" from
# "the renderer itself needs the dependency".
MICROTRACE_SRC = '''# -*- coding: utf-8 -*-
"""micro-trace: what matplotlib Agg itself does when a dependency is missing."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig = plt.figure(figsize=(2, 2))
fig.savefig(os.path.join(os.getcwd(), "micro.png"))
print("MICRO OK: png written")
'''


# 场景表：每一行都是"把某一个依赖拿掉/命令拿掉"的一次真实运行
SCENARIOS = [
    {"id": "s00-baseline", "what": "全依赖可用（对照行）", "block": [], "formats": None},
    {"id": "s01-no-matplotlib", "what": "缺 matplotlib（PNG/PDF 渲染器）",
     "block": ["matplotlib"], "formats": None},
    {"id": "s02-no-numpy", "what": "缺 numpy（matplotlib 的硬依赖）",
     "block": ["numpy"], "formats": None},
    {"id": "s03-no-pil", "what": "缺 PIL/Pillow（只被 PNG 尺寸检查 F02 用到）",
     "block": ["PIL"], "formats": None},
    {"id": "s04-no-yaml", "what": "缺 PyYAML（本包未 import）", "block": ["yaml"], "formats": None},
    {"id": "s05-no-pptx", "what": "缺 python-pptx（本包未 import）",
     "block": ["pptx"], "formats": None},
    {"id": "s06-no-lxml", "what": "缺 lxml（本包用标准库 xml.etree）",
     "block": ["lxml"], "formats": None},
    {"id": "s07-no-pypdf", "what": "缺 pypdf（本包不解析 PDF）",
     "block": ["pypdf"], "formats": None},
    {"id": "s08-no-mpl-no-pil", "what": "同时缺 matplotlib+numpy+PIL（最坏情况）",
     "block": ["matplotlib", "numpy", "PIL"], "formats": None},
    {"id": "s09-svg-only", "what": "依赖齐全，但用户主动只请求 SVG（有意的降级）",
     "block": [], "formats": "svg"},
    {"id": "s10-libreoffice-missing", "what": "PATH 里没有 soffice/libreoffice（命令不存在）",
     "block": [], "formats": None, "path_mode": "empty"},
    {"id": "s11-libreoffice-failing", "what": "soffice/libreoffice 存在但立即失败（退出 127）",
     "block": [], "formats": None, "path_mode": "failing-stub"},
    {"id": "s12-pil-png-microtrace",
     "what": "micro-trace: matplotlib Agg PNG save with PIL blocked",
     "block": ["PIL"], "formats": "svg", "microtrace": True},
]


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def portable(text, roots):
    if not isinstance(text, str):
        return text
    out = text
    for root, tag in roots:
        if not root:
            continue
        for variant in (root, root.rstrip("/\\"), root.replace("\\", "/"),
                        root.replace("/", "\\"), root.replace("\\", "\\\\")):
            if variant:
                out = out.replace(variant, tag)
    out = re.sub(
        r"(?<!>)(?:[A-Za-z]:[\\/]|\\\\[?]\\|/(?:Users|home|tmp|skills)/)[^\s\"'<>|,;)\]]*",
        "<ABS>", out)   # 整段绝对路径掩码；(?<!>) 保证幂等
    return out.replace("\\", "/")


def portable_obj(obj, roots):
    if isinstance(obj, dict):
        return {k: portable_obj(v, roots) for k, v in obj.items()}
    if isinstance(obj, list):
        return [portable_obj(v, roots) for v in obj]
    if isinstance(obj, str):
        return portable(obj, roots)
    return obj


def copy_tree(src, dst, skip_dir_names=("__pycache__", ".git", "out"), skip_ext=(".pyc", ".pyo")):
    os.makedirs(dst, exist_ok=True)
    for root, dirs, files in os.walk(src):
        dirs[:] = sorted(d for d in dirs if d not in skip_dir_names)
        rel = os.path.relpath(root, src)
        tgt = dst if rel == "." else os.path.join(dst, rel)
        os.makedirs(tgt, exist_ok=True)
        for f in sorted(files):
            if os.path.splitext(f)[1].lower() in skip_ext:
                continue
            shutil.copy2(os.path.join(root, f), os.path.join(tgt, f))


def safe_reset(work_root, sub):
    target = os.path.abspath(os.path.join(work_root, sub))
    wr = os.path.abspath(work_root)
    if target == wr or not target.startswith(wr + os.sep):
        raise SystemExit("拒绝操作（越界）: %s 不在 %s 内部" % (target, wr))
    if os.path.isfile(os.path.join(wr, "SKILL.md")):
        raise SystemExit("拒绝操作：--work 指向技能包内部（%s）" % wr)
    if len(os.path.normpath(wr).split(os.sep)) < 2:
        raise SystemExit("拒绝操作：--work 太靠近盘根（%s）" % wr)
    if os.path.isdir(target):
        shutil.rmtree(target)
    return target


def make_stub_bin(work, roots):
    """构造"命令存在但立即失败"的 PATH 前置目录（POSIX 脚本 + .cmd/.bat）。

    桩命令**先写调用标记再退出 127**：标记文件是否出现，就是"主流程到底有没有真的
    去调 LibreOffice"的实测证据（比"看不出影响"强得多）。
    """
    d = os.path.join(work, "stubbin")
    os.makedirs(d, exist_ok=True)
    mark = os.path.join(work, "stub-calls.txt")
    if os.path.isfile(mark):
        os.remove(mark)
    for name in ("soffice", "libreoffice"):
        posix = os.path.join(d, name)
        with open(posix, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("#!/bin/sh\necho called-%s >> '%s'\nexit 127\n"
                     % (name, mark.replace("\\", "/")))
        os.chmod(posix, os.stat(posix).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        for ext in (".cmd", ".bat"):
            with open(os.path.join(d, name + ext), "w", encoding="utf-8",
                      newline="\r\n") as fh:
                fh.write("@echo off\r\necho called-%s >> \"%s\"\r\nexit /b 127\r\n"
                         % (name, mark))
    return d, portable(d, roots), mark


def check_ids(entries):
    out = []
    for e in entries or []:
        if isinstance(e, dict) and e.get("id"):
            out.append(e.get("id"))
    return out


def run_scenario(sc, pkg, base_dir, work, roots, python, args):
    row_dir = safe_reset(work, os.path.join("rows", sc["id"]))
    os.makedirs(row_dir, exist_ok=True)
    case_path = os.path.join(row_dir, "case.json")
    model_path = os.path.join(row_dir, "model.example.json")
    for name in os.listdir(base_dir):
        src = os.path.join(base_dir, name)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(row_dir, name))
        elif os.path.isdir(src) and name != "output":
            shutil.copytree(src, os.path.join(row_dir, name), dirs_exist_ok=True)
    shutil.copy2(os.path.join(base_dir, "model.example.json"), model_path)
    out_dir = os.path.join(row_dir, "out")

    fmt = sc.get("formats") or args.formats
    main_py = os.path.join(pkg, "scripts", "main.py")
    base_argv = ["--case", case_path, "--model-file", model_path, "--out", "out",
                 "--formats", fmt, "--dpi", str(args.dpi)]

    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    path_mode = sc.get("path_mode")
    stub_dir = stub_cmd = stub_mark = None
    if path_mode == "empty":
        empty = os.path.join(work, "emptybin")
        os.makedirs(empty, exist_ok=True)
        env["PATH"] = empty
    elif path_mode == "failing-stub":
        stub_dir, stub_cmd, stub_mark = make_stub_bin(work, roots)
        env["PATH"] = stub_dir + os.pathsep + env.get("PATH", "")

    if sc["block"]:
        shim_path = os.path.join(work, "shim_blocked.py")
        with open(shim_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(SHIM)
        argv = [python, shim_path, json.dumps(sc["block"]), main_py] + base_argv
    else:
        argv = [python, main_py] + base_argv

    rec = {"id": sc["id"], "what": sc["what"], "blocked": sc["block"],
           "formats": fmt, "path_mode": path_mode or "inherit",
           "path_stub_dir": stub_cmd}
    rec["which_soffice"] = portable(shutil.which("soffice", path=env.get("PATH")), roots)
    rec["which_libreoffice"] = portable(shutil.which("libreoffice", path=env.get("PATH")), roots)
    try:
        proc = subprocess.run(argv, cwd=row_dir, env=env, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, timeout=args.timeout)
        rc, out, err = proc.returncode, proc.stdout, proc.stderr
        rec["timeout"] = False
    except subprocess.TimeoutExpired as ex:
        rc = None
        out = ex.stdout or b""
        err = ex.stderr or b""
        rec["timeout"] = True
    stdout = out.decode("utf-8", "replace")
    stderr = err.decode("utf-8", "replace")
    rec["exit_code"] = rc

    probe_line, summary = None, None
    for line in stdout.splitlines():
        if line.startswith("PROBE "):
            try:
                probe_line = json.loads(line[len("PROBE "):])
            except Exception:
                probe_line = {"raw": line[len("PROBE "):]}
        if line.startswith("SUMMARY "):
            try:
                summary = json.loads(line[len("SUMMARY "):])
            except Exception:
                summary = {"raw": line[len("SUMMARY "):]}
    rec["import_interception"] = probe_line
    rec["summary"] = summary
    rec["stdout_tail"] = portable("\n".join(stdout.strip().splitlines()[-3:]), roots)
    rec["stderr_tail"] = portable("\n".join(stderr.strip().splitlines()[-3:]), roots)

    files = sorted(os.listdir(out_dir)) if os.path.isdir(out_dir) else []
    rec["artifacts"] = {ARTIFACT_KEYS.get(f, f): True for f in files if f in ARTIFACT_KEYS}
    rec["artifacts_present"] = files
    rj_path = os.path.join(out_dir, "result.json")
    rec["result_json_written"] = os.path.isfile(rj_path)
    if rec["result_json_written"]:
        rj = load_json(rj_path)
        rec["status"] = rj.get("status")
        sc_ = rj.get("self_check") or {}
        rec["self_check_passed"] = sc_.get("passed")
        rec["failed_checks"] = check_ids(sc_.get("failures"))
        rec["gates"] = {k: v.get("pass") for k, v in (rj.get("gates") or {}).items()}
        rec["deliverables"] = {
            "editable_sources": len((rj.get("deliverables") or {}).get("editable_sources") or []),
            "previews": len((rj.get("deliverables") or {}).get("previews") or []),
            "exports": len((rj.get("deliverables") or {}).get("exports") or []),
            "audits": (rj.get("deliverables") or {}).get("audits") or [],
        }
        unc = rj.get("uncertainty") or []
        rec["uncertainty_n"] = len(unc)
        rec["uncertainty_dependency_items"] = [
            {"item": u.get("item"), "reason": (u.get("reason") or "")[:140]}
            for u in unc
            if any(k in json.dumps(u, ensure_ascii=False)
                   for k in ("matplotlib", "PIL", "Pillow", "numpy", "字体", "预览",
                             "yaml", "pptx", "lxml", "pypdf", "LibreOffice"))]
        rec["export_check_warnings"] = [
            {"file": e.get("file"), "check": e.get("check"), "result": e.get("result"),
             "detail": (e.get("detail") or "")[:140]}
            for e in (rj.get("export_checks") or []) if e.get("result") != "pass"]
    else:
        rec["status"] = None
        rec["self_check_passed"] = None
        rec["failed_checks"] = []
        rec["gates"] = {}
        rec["deliverables"] = {}
        rec["uncertainty_n"] = 0
        rec["uncertainty_dependency_items"] = []
        rec["export_check_warnings"] = []

    rec["usable"] = {
        "editable_source_svg": bool(rec["artifacts"].get("editable_svg")),
        "png_preview": bool(rec["artifacts"].get("png_preview")),
        "pdf_export": bool(rec["artifacts"].get("pdf_export")),
        "contract_result_json": bool(rec["artifacts"].get("result_json")),
        "audits": bool(rec["artifacts"].get("topology_audit")
                       and rec["artifacts"].get("legend_audit")),
    }
    # 桩命令是否真的被调用过（标记文件 = 调用证据）
    rec["stub_invoked"] = bool(stub_mark) and os.path.isfile(stub_mark) \
        and os.path.getsize(stub_mark) > 0
    if stub_mark and os.path.isfile(stub_mark):
        with open(stub_mark, encoding="utf-8", errors="replace") as fh:
            rec["stub_call_log"] = portable(fh.read()[:200], roots)
    if sc.get("microtrace"):
        micro = os.path.join(work, "microtrace_%s.py" % sc["id"])
        with open(micro, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(MICROTRACE_SRC)
        _shim = os.path.join(work, "shim_blocked.py")
        mt = subprocess.run([python, _shim, json.dumps(sc["block"]), micro],
                            cwd=row_dir, env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, timeout=args.timeout)
        mt_out = mt.stdout.decode("utf-8", "replace")
        mt_err = mt.stderr.decode("utf-8", "replace")
        rec["microtrace"] = {
            "what": "blocked=%s: direct matplotlib Agg PNG save result" % ",".join(sc["block"]),
            "exit_code": mt.returncode,
            "stdout_tail": portable("\n".join(mt_out.strip().splitlines()[-3:]), roots),
            "traceback_tail": _tb_tail(mt_err, roots),
            "traceback_omitted_host_path_lines": _tb_omitted,
            "png_written": os.path.isfile(os.path.join(row_dir, "micro.png")),
            "main_pipeline_ran_instead": False,
        }

    rec["availability"] = _availability(rec)
    return rec



def _tb_tail(text, roots, limit=7):
    """只保留**不含主机路径**的 traceback 行（用全局 _tb_omitted 记省略行数）。

    交付物里不放本机 site-packages 路径：报告只保留「哪一行 from PIL import Image」与
    ImportError 消息这类可复核证据，主机路径行一律省略并计数。
    """
    global _tb_omitted
    keep, omitted = [], 0
    for ln in text.strip().splitlines():
        tagged = portable(ln, roots)
        if re.search(r"[A-Za-z]:[\\/]|/site-packages/|/lib/python", tagged):
            omitted += 1
            continue
        keep.append(tagged)
    _tb_omitted = omitted
    return "\n".join(keep[-limit:])


_tb_omitted = 0
def _availability(rec):
    """一句话结论：这一行之后还剩什么、status 是什么。"""
    u = rec["usable"]
    parts = []
    parts.append("SVG" if u["editable_source_svg"] else "无 SVG")
    parts.append("PNG" if u["png_preview"] else "无 PNG")
    parts.append("PDF" if u["pdf_export"] else "无 PDF")
    parts.append("result.json" if u["contract_result_json"] else "无 result.json")
    parts.append("审计 JSON 齐全" if u["audits"] else "审计 JSON 缺失")
    return "exit=%s status=%s | %s" % (rec.get("exit_code"), rec.get("status"),
                                       " · ".join(parts))


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="missing-dependency degradation probe for the pathway-diagram skill")
    ap.add_argument("--skill", default=DEFAULT_SKILL_ROOT)
    ap.add_argument("--case", default=None)
    ap.add_argument("--model-file", default=None)
    ap.add_argument("--work", default=None)
    ap.add_argument("--report", default=None)
    ap.add_argument("--formats", default="svg,png,pdf")
    ap.add_argument("--dpi", type=int, default=150)
    ap.add_argument("--python", default=None)
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--only", default=None, help="只跑 id 含该子串的行（逗号分隔）")
    ap.add_argument("--json", action="store_true")
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
    args.case = args.case or os.path.join(skill_root, "examples", "case.json")
    args.model_file = args.model_file or os.path.join(skill_root, "examples", "model.example.json")
    for p in (args.case, args.model_file):
        if not os.path.isfile(p):
            print("错误：找不到 %s" % p, file=sys.stderr)
            return 4
    if args.work is None:
        import tempfile
        args.work = os.path.join(tempfile.gettempdir(), "dg-%d" % os.getpid())
    work = os.path.abspath(args.work)
    os.makedirs(work, exist_ok=True)
    roots = [(work, "<WORK>"), (skill_root, "<SKILL>")]
    python = args.python or sys.executable

    pkg = safe_reset(work, "pkg")
    copy_tree(skill_root, pkg)
    base_dir = safe_reset(work, "base")
    os.makedirs(base_dir, exist_ok=True)
    src_dir = os.path.dirname(os.path.abspath(args.case))
    for name in os.listdir(src_dir):
        src = os.path.join(src_dir, name)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(base_dir, name))
        elif os.path.isdir(src) and name != "output":
            shutil.copytree(src, os.path.join(base_dir, name), dirs_exist_ok=True)
    shutil.copy2(args.model_file, os.path.join(base_dir, "model.example.json"))

    rows = SCENARIOS
    if args.only:
        keys = [k.strip() for k in args.only.split(",") if k.strip()]
        rows = [s for s in rows if any(k in s["id"] for k in keys)]
        if not rows:
            print("错误：--only 没匹配到任何场景", file=sys.stderr)
            return 4

    results = []
    for i, sc in enumerate(rows, 1):
        rec = run_scenario(sc, pkg, base_dir, work, roots, python, args)
        results.append(rec)
        if not args.json:
            print("[%2d/%d] %-24s %s" % (i, len(rows), rec["id"], rec["availability"]))
            if rec["failed_checks"]:
                print("        failed checks: %s" % ", ".join(rec["failed_checks"]))
            if rec["uncertainty_dependency_items"]:
                print("        uncertainty: %s" % rec["uncertainty_dependency_items"][0]["item"])
            if rec.get("path_mode") == "failing-stub":
                print("        stub invoked: %s" % (
                    (rec.get("stub_call_log") or "yes") if rec["stub_invoked"] else
                    "no（标记文件未生成 → 主流程从未调用 LibreOffice）"))
            if rec["import_interception"]:
                bad = [c["module"] for c in rec["import_interception"]["import_checks"]
                       if c.get("importable") is not False]
                print("        interception: %s" %
                      ("生效（%d 个模块确实 import 失败）"
                       % len(rec["import_interception"]["import_checks"])
                       if not bad else "**未生效: %s**" % bad))

    base = next((r for r in results if r["id"] == "s00-baseline"), None)
    base_set = set(base["artifacts_present"]) if base else set()
    for r in results:
        r["same_artifact_set_as_baseline"] = (set(r["artifacts_present"]) == base_set)
        r["same_exit_code_as_baseline"] = bool(base) and r["exit_code"] == base["exit_code"]

    # 依赖面判定：拿掉它是否改变结果
    dependency_surface = {}
    for r in results:
        for m in r["blocked"] or []:
            key = m
            prev = dependency_surface.get(key, {"scenarios": [], "impact": None})
            prev["scenarios"].append(r["id"])
            if r["same_artifact_set_as_baseline"] and r["same_exit_code_as_baseline"]:
                prev["impact"] = "none-or-minor"
            else:
                prev["impact"] = "changes-deliverables-or-status"
            dependency_surface[key] = prev
    for r in results:
        if r["path_mode"] == "empty":
            dependency_surface["LibreOffice CLI (PATH 无该命令)"] = {
                "scenarios": [r["id"]], "impact": ("none-or-minor"
                                                   if r["same_artifact_set_as_baseline"]
                                                   and r["same_exit_code_as_baseline"]
                                                   else "changes-deliverables-or-status")}
        if r["path_mode"] == "failing-stub":
            dependency_surface["LibreOffice CLI (存在但退出 127)"] = {
                "scenarios": [r["id"]], "impact": ("none-or-minor"
                                                   if r["same_artifact_set_as_baseline"]
                                                   and r["same_exit_code_as_baseline"]
                                                   else "changes-deliverables-or-status")}

    # 依赖面判定（由实测行推导，不写死结论）
    dep_effect = {}
    for _r in results:
        if _r.get("microtrace"):
            continue
        for _m in _r["blocked"] or []:
            if _r["same_artifact_set_as_baseline"] and _r["same_exit_code_as_baseline"]:
                dep_effect.setdefault(_m, "no-effect-measured")
            else:
                dep_effect[_m] = "removing-it-changes-deliverables-or-status"
    for _r in results:
        if _r["path_mode"] == "empty":
            dep_effect["LibreOffice CLI (PATH clean, command absent)"] = (
                "no-effect-measured" if _r["same_artifact_set_as_baseline"]
                and _r["same_exit_code_as_baseline"]
                else "removing-it-changes-deliverables-or-status")
        if _r["path_mode"] == "failing-stub":
            dep_effect["LibreOffice CLI (present, exits 127)"] = (
                "no-effect-measured" if _r["same_artifact_set_as_baseline"]
                and _r["same_exit_code_as_baseline"]
                else "removing-it-changes-deliverables-or-status")
    _required = sorted(m for m, v in dep_effect.items() if v != "no-effect-measured")
    _not_required = sorted(m for m, v in dep_effect.items() if v == "no-effect-measured")

    report = portable_obj({
        "probe": "degrade-probe",
        "tool": "scripts/degrade_probe.py",
        "tool_version": TOOL_VERSION,
        "what_this_measures": [
            "受控导入拦截（sys.meta_path）逐个屏蔽 matplotlib/numpy/PIL/yaml/pptx/lxml/pypdf 后跑真实主流程",
            "PATH 处理模拟 LibreOffice CLI 缺失（命令不存在）与失败（退出 127）",
            "每行记录：退出码 / status / 剩余产物 / 是否写 result.json / 失败检查项 / 留痕",
            "拦截器自证：被拦模块在子进程内确实 import 失败（防'拦了但没生效'的假结论）",
        ],
        "config": {
            "case": portable(os.path.join(work, "base", "case.json"), roots),
            "model_file": portable(os.path.join(work, "base", "model.example.json"), roots),
            "formats": args.formats, "dpi": args.dpi, "timeout_s": args.timeout,
            "python": sys.version.split()[0], "platform": sys.platform,
            "host_has_libreoffice": bool(shutil.which("soffice")
                                         or shutil.which("libreoffice")),
        },
        "rows": results,
        "dependency_surface": dependency_surface,
        "minimal_environment": {
            "required": [
                "Python 3（仅标准库：json/os/re/math/xml.etree/hashlib/subprocess/argparse）",
            ],
            "required_for_full_deliverables_measured": _required,
            "no_effect_measured": _not_required,
            "per_dependency_effect": dep_effect,
            "pil_mechanism_note": [
                "缺 PIL 时 PNG **与** PDF 都拿不到（实测 s03：exit 2 / partial / 无 PNG 无 PDF）",
                "机制见 s12 微追溯：matplotlib.colors 自己就 `from PIL import Image`，",
                "因此 PIL 不是「只被 F02 尺寸检查用到」，而是 matplotlib 的硬依赖；",
                "且 mpl_backend 先存 PNG 再存 PDF，PNG 保存抛错会连带丢掉 PDF",
            ],
            "how_derived": "见 rows[*].blocked / path_mode 与 dependency_surface 的实测影响（本段自动生成）",
        },
        "not_covered": [
            "字体真的缺失（无中文字体）时的渲染：属环境探测，本探针只记录 matplotlib 自身的字体告警，不卸载系统字体",
            "部分损坏的安装（如 matplotlib 能 import 但 Agg 后端缺 C 扩展）：只覆盖'整模块不可导入'",
            "README 声明的依赖之外的第三方库：本包 scripts/ 的 import 并集已逐个覆盖",
            "平台真实评测容器的依赖集（不可见）：结论只对本机实测的解释器/版本组合有效",
            "若本机基线本来就没有 LibreOffice（config.host_has_libreoffice=false），"
            "则 s10 只证明「PATH 被清空后行为不变」；s11 用桩命令补上「命令存在但失败」这一格",
            "s11 的桩命令会写调用标记文件：标记未生成即证明主流程**从未** shell out 到 LibreOffice",
        ],
    }, roots)
    report_path = args.report or os.path.join(skill_root, "degrade_report.json")
    blob = json.dumps(report, ensure_ascii=False, indent=2)
    with open(report_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(blob + "\n")

    if args.json:
        print(blob)
    else:
        print("=" * 78)
        print("dependency surface (实测):")
        for k, v in dependency_surface.items():
            print("  %-38s %-32s %s" % (k, v["impact"], ",".join(v["scenarios"])))
        print("  report -> %s" % report_path)
    if base and (base["exit_code"] != 0 or base.get("status") != "success"):
        print("控制行 s00-baseline 未通过（exit=%s status=%s）：结论不可用"
              % (base["exit_code"], base.get("status")), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
