#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""degrade_probe.py -- 缺依赖降级链实测：受控导入拦截，逐个模拟缺库/缺外部 CLI，记录真实降级形态。

Part of the "graphical-abstract" Skill (graphical-abstract-7030fff2, efficiency-3, axis v9).

**为什么需要这个脚本**：README 里写着"依赖：Python 3.9+，可选 matplotlib / Pillow / pypdf"。
"可选"这三个字必须能被复核 —— 缺了它**具体会变成什么样**：产物还剩什么？`status` 变什么？
还写不写 `result.json`？退出码是多少？还剩下哪个后端？这些问题在文档里怎么猜都不算数，
只有把库真的"弄没"再跑一遍才知道。

拦截方式（**受控、可复核、不动本机环境**）：

  * 在 `<out>/_shim/modules/` 下生成一组**只做一件事**的假包：写入一行命中日志，
    然后 `raise ImportError`。把该目录前置到子进程 `PYTHONPATH`，
    等价于"该库在这台机器上不存在"，而本机真实 site-packages 分毫未动；
  * LibreOffice 用 `PATH` 前置一组 `soffice` / `libreoffice` 假命令（落日志 + `exit 127`），
    用来实测"主流程到底会不会去调它"；
  * 每个场景都是独立子进程（`python -B <sandbox>/scripts/main.py …`），抓真实退出码。

实测记录（每条）：`退出码 / status / 产物还剩哪些（svg/png/pdf）/ PNG 后端 / 字体 /
result.json 是否写出与顶层键数 / uncertainty 条目 / warnings 条目 / 命中日志`。

用法（cwd 任意；`$SKILL_DIR` = 本包根）：

    # 全部场景，人读表 + 落 degrade_matrix.json
    python "$SKILL_DIR/scripts/degrade_probe.py" --out /tmp/dg

    # 只跑某个场景 / 某类；只看汇总
    python "$SKILL_DIR/scripts/degrade_probe.py" --out /tmp/dg --only P09 --verbose

退出码语义（本脚本自身）：
    0 = 达到 `--fail-on` 等级（silent: 无"能力丢了却没有任何记录"的场景；strict: 全部符合期望）
    1 = 未达到（逐行打印）
    2 = 用法/环境错误

**只读本包**：把 `<skill>/scripts` 复制到 `<out>/_skill/` 再跑；包内不落任何文件。
"""
from __future__ import annotations

import argparse
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

PROBE_SCHEMA = "degrade-matrix/1"

# 本 Skill 的**真实**第三方依赖面（静态实测，见 report.import_sites）：
#   matplotlib -> 抗锯齿 PNG + 矢量 PDF；PIL -> 位图文字；pypdf -> PDF 材料文本层；
#   numpy 是 matplotlib 的传递依赖；python-pptx / yaml / LibreOffice CLI 在本 Skill 里
#   **没有任何导入点或调用点**（本矩阵用运行时拦截来证明"拦了也没变化"）。
MODULES = ("matplotlib", "PIL", "numpy", "pypdf", "yaml", "pptx")

SCENARIOS = [
    dict(id="P00", title="阳性对照：不拦截任何库", block=[], loco=False, pdf_material=False,
         expect=dict(exit=(0,), status_in=("success",), control=True),
         rationale="对照组：完整环境下必须是 success；后续场景的能力增量都相对它计算"),
    dict(id="P01", title="拦截 python-pptx（pptx）", block=["pptx"], loco=False,
         pdf_material=False, expect=dict(exit=(0,), no_edge=True),
         rationale="本 Skill 不生成 pptx：命中日志必须为空，行为与对照一致"),
    dict(id="P02", title="拦截 Pillow（PIL）", block=["PIL"], loco=False, pdf_material=False,
         expect=dict(exit=(0,), record_if_degraded=True),
         rationale="matplotlib 自身 import PIL：实测它会不会连带失效；降级必须留痕"),
    dict(id="P03", title="拦截 matplotlib", block=["matplotlib"], loco=False,
         pdf_material=False,
         expect=dict(exit=(0,), pdf_present=False, pdf_reason_required=True,
                     uncertainty_contains="matplotlib", record_if_degraded=True),
         rationale="D11：渲染后端回退；PDF 条目必须 present:false + reason，并留 uncertainty"),
    dict(id="P04", title="拦截 numpy", block=["numpy"], loco=False, pdf_material=False,
         expect=dict(exit=(0,), record_if_degraded=True),
         rationale="numpy 是 matplotlib 的传递依赖：实测回退到哪一级，降级必须留痕"),
    dict(id="P05", title="拦截 PyYAML（yaml）", block=["yaml"], loco=False, pdf_material=False,
         expect=dict(exit=(0,), no_edge=True),
         rationale="主链只读写 JSON：命中日志必须为空，行为与对照一致"),
    dict(id="P06", title="拦截 pypdf（材料是 .md，不触发该路径）", block=["pypdf"], loco=False,
         pdf_material=False, expect=dict(exit=(0,), no_edge=True),
         rationale="非 PDF 材料根本不会 import pypdf：命中日志为空即为证据"),
    dict(id="P07", title="拦截 pypdf + 材料改成真实 PDF", block=["pypdf"], loco=False,
         pdf_material=True,
         expect=dict(exit=(0,), record_if_degraded=True),
         rationale="D9：PDF 文本层取不到时必须如实记录，不得把字节流当 UTF-8 解出乱码实体"),
    dict(id="P08", title="拦截 Pillow + matplotlib（两级绘图后端都不可用）",
         block=["PIL", "matplotlib"], loco=False, pdf_material=False,
         expect=dict(exit=(0,), png_backend="pure-python-png", pdf_present=False,
                     pdf_reason_required=True, record_if_degraded=True),
         rationale="第三级纯 Python PNG 保底：文字变占位框，但几何、SVG 与 PNG 仍在"),
    dict(id="P09", title="只留标准库：matplotlib + PIL + numpy + pypdf 全拦",
         block=["matplotlib", "PIL", "numpy", "pypdf"], loco=False, pdf_material=False,
         expect=dict(exit=(0,), png_backend="pure-python-png", pdf_present=False,
                     pdf_reason_required=True, record_if_degraded=True,
                     svg_present=True, png_present=True, result_keys_min=20),
         rationale="最小可用环境：stdlib-only 仍须产出可编辑 SVG + PNG + result.json"),
    dict(id="P10", title="LibreOffice CLI 不存在（假 soffice 落日志 + exit 127）",
         block=[], loco=True, pdf_material=False, expect=dict(exit=(0,), no_edge=True),
         rationale="本 Skill 不调用外部办公套件：命中日志必须为空（本机也确实没装）"),
    dict(id="P11", title="拦截 python-pptx + yaml + LibreOffice（三重无关依赖）",
         block=["pptx", "yaml"], loco=True, pdf_material=False,
         expect=dict(exit=(0,), no_edge=True),
         rationale="三个别人会依赖、本 Skill 不依赖的东西一起拦，验证零影响"),
]


MINIMAL_PDF = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 200]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj
4 0 obj<</Length 68>>stream
BT /F1 14 Tf 20 150 Td (GA degrade probe PDF material) Tj ET
endstream
endobj
5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj
trailer<</Root 1 0 R>>
"""

SHIM_TEMPLATE = '''import os
_log = os.environ.get("GA_DEGRADE_LOG")
if _log:
    with open(_log, "a", encoding="utf-8") as fh:
        fh.write("import-attempt: %(mod)s\\n")
raise ImportError("degrade-probe: %(mod)s is blocked on purpose")
'''

LOCO_SH = """#!/bin/sh
log="$GA_DEGRADE_LOG"
[ -n "$log" ] && echo "exec-attempt: %(name)s" >> "$log"
exit 127
"""

LOCO_CMD = """@echo off
if defined GA_DEGRADE_LOG echo exec-attempt: %(name)s>>"%%GA_DEGRADE_LOG%%"
exit /b 127
"""


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _write(path, text, binary=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    mode = "wb" if binary else "w"
    kwargs = {} if binary else {"encoding": "utf-8", "newline": "\n"}
    with open(path, mode, **kwargs) as fh:
        fh.write(text)


def _load_json(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:  # noqa: BLE001
        return None


TOOL_FILES = {"degrade_probe.py", "contract_matrix.py", "fault_inject.py",
              "determinism.py", "gain_harness.py"}


def _import_sites(scripts_dir):
    """Static measurement: dependency edges of the **pipeline**, and of the tooling separately.

    The verification tools ship with the package and legitimately import matplotlib
    (fixtures) or mention soffice; counting them would blur the claim "the pipeline itself
    does not depend on X". Both scopes are therefore reported side by side.
    """
    pats = {
        "matplotlib": r"^\s*(?:import|from)\s+matplotlib\b",
        "PIL": r"^\s*(?:import|from)\s+PIL\b",
        "numpy": r"^\s*(?:import|from)\s+numpy\b",
        "pypdf": r"^\s*(?:import|from)\s+pypdf\b",
        "yaml": r"^\s*(?:import|from)\s+yaml\b",
        "pptx": r"^\s*(?:import|from)\s+pptx\b",
        "LibreOffice": r"\b(?:soffice|libreoffice)\b",
    }
    counts, tool_counts, where = {}, {}, {}
    for name, pat in pats.items():
        rx = re.compile(pat, re.M)
        hits, tool_hits = [], []
        for fn in sorted(os.listdir(scripts_dir)):
            if not fn.endswith(".py"):
                continue
            with open(os.path.join(scripts_dir, fn), encoding="utf-8") as fh:
                for i, line in enumerate(fh, 1):
                    if rx.search(line):
                        (tool_hits if fn in TOOL_FILES else hits).append("%s:%d" % (fn, i))
        counts[name] = len(hits)
        tool_counts[name] = len(tool_hits)
        where[name] = hits[:6]
    return counts, where, tool_counts


def _build_bin_shims(out_root):
    """PATH shims for the external office-suite CLIs (soffice / libreoffice)."""
    bin_dir = os.path.join(out_root, "_shim", "bin")
    for name in ("soffice", "libreoffice"):
        _write(os.path.join(bin_dir, name), LOCO_SH % {"name": name})
        os.chmod(os.path.join(bin_dir, name), 0o755)
        _write(os.path.join(bin_dir, name + ".cmd"), LOCO_CMD % {"name": name})
    return bin_dir


def _scenario_shim(out_root, sc):
    """One shim directory **per scenario**, containing ONLY that scenario's blocked modules.

    (A single shared directory would block every module for every scenario — that bug was
    caught by the very first measurement: P01 blocked only pptx yet matplotlib/PIL never
    imported, and the shim log said so.)
    """
    if not sc["block"]:
        return None
    mod_dir = os.path.join(out_root, "_shim", "scn_" + sc["id"])
    if os.path.isdir(mod_dir):
        shutil.rmtree(mod_dir, ignore_errors=True)
    for name in sc["block"]:
        _write(os.path.join(mod_dir, name, "__init__.py"), SHIM_TEMPLATE % {"mod": name})
    return mod_dir


def _pdf_fixture(work):
    """A real one-page PDF (matplotlib if available, else the hand-written minimal one)."""
    path = os.path.join(work, "material.pdf")
    try:
        import matplotlib
        matplotlib.use("Agg")
        from matplotlib.backends.backend_pdf import PdfPages
        import matplotlib.pyplot as plt
        with PdfPages(path) as pdf:
            fig = plt.figure(figsize=(3, 2))
            ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off")
            ax.text(0.05, 0.75, "GA degrade probe", fontsize=13)
            ax.text(0.05, 0.5, "release rate pH 5.5 = 85 %", fontsize=11)
            ax.text(0.05, 0.25, "particle size = 95 nm", fontsize=11)
            pdf.savefig(fig); plt.close(fig)
        return path, "matplotlib"
    except Exception:  # noqa: BLE001
        _write(path, MINIMAL_PDF, binary=True)
        return path, "handwritten-minimal"


def _run(argv, cwd, env_extra=None, timeout=300):
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.update(env_extra or {})
    t0 = time.time()
    proc = subprocess.run([PY, "-B"] + argv, cwd=cwd, env=env, capture_output=True,
                          text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return proc.returncode, proc.stdout or "", proc.stderr or "", round(time.time() - t0, 2)


# ---------------------------------------------------------------------------
# one scenario
# ---------------------------------------------------------------------------
def run_one(sc, base_case, base_dir, sandbox_skill, out_root, bin_dir, keep=False):
    sid = sc["id"]
    box = os.path.join(out_root, "_box", sid)
    if os.path.isdir(box):
        shutil.rmtree(box, ignore_errors=True)
    work, out = os.path.join(box, "work"), os.path.join(box, "out")
    os.makedirs(work, exist_ok=True)
    log_path = os.path.join(box, "shim_hits.log")
    _write(log_path, "")

    case_obj = json.loads(json.dumps(base_case, ensure_ascii=False))
    case_obj["case_id"] = "dg-" + sid.lower()
    for name in ("material.md", "task.md"):
        src = os.path.join(base_dir, name)
        if os.path.isfile(src):
            shutil.copyfile(src, os.path.join(work, name))
    pdf_note = None
    if sc["pdf_material"]:
        _p, generator = _pdf_fixture(work)
        case_obj["source_material"] = "material.pdf"
        pdf_note = "PDF 指纹件由 %s 生成" % generator
    _write(os.path.join(work, "case.json"),
           json.dumps(case_obj, ensure_ascii=False, indent=2) + "\n")

    mod_dir = _scenario_shim(out_root, sc)
    env_extra = {"GA_DEGRADE_LOG": log_path}
    if mod_dir:
        env_extra["PYTHONPATH"] = mod_dir
    if sc["loco"]:
        env_extra["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")

    rc, stdout, stderr, secs = _run([os.path.join(sandbox_skill, "main.py"),
                                     "--case", os.path.join(work, "case.json"),
                                     "--out", out], cwd=work, env_extra=env_extra)
    result = _load_json(os.path.join(out, "result.json"))
    render_log = _load_json(os.path.join(out, "render_log.json"))
    hits = []
    try:
        with open(log_path, encoding="utf-8") as fh:
            hits = [ln.strip() for ln in fh if ln.strip()]
    except OSError:
        pass

    row = _evaluate(sc, rc, result, render_log, hits, out, stdout, stderr, pdf_note)
    row["seconds"] = secs
    if not keep:
        shutil.rmtree(box, ignore_errors=True)
    return row


def _deliverable_map(result):
    out = {}
    for d in (result or {}).get("deliverables") or []:
        out[d.get("format")] = d
    return out


def _evaluate(sc, rc, result, render_log, hits, out_dir, stdout, stderr, pdf_note):
    exp = sc["expect"]
    problems, observations = [], []
    result = result or {}
    deliv = _deliverable_map(result)
    backend = (render_log or {}).get("backend") or (deliv.get("png") or {}).get("backend")
    font = (render_log or {}).get("font")
    pdf_entry = deliv.get("pdf") or {}
    pdf_rel = pdf_entry.get("path")
    pdf_present = bool(pdf_rel) and pdf_entry.get("present") is not False and         os.path.isfile(os.path.join(out_dir, str(pdf_rel)))
    svg_rel = (deliv.get("svg") or {}).get("path")
    png_rel = (deliv.get("png") or {}).get("path")
    svg_present = bool(svg_rel) and os.path.isfile(os.path.join(out_dir, str(svg_rel)))
    png_present = bool(png_rel) and os.path.isfile(os.path.join(out_dir, str(png_rel)))
    uncertainty = result.get("uncertainty") or []
    warnings = result.get("warnings") or []
    recorded = bool(uncertainty or warnings)
    status = result.get("status")

    # measured capability losses -------------------------------------------------
    capability_lost = []
    if backend and backend != "matplotlib":
        capability_lost.append("PNG 后端降级为 %s" % backend)
    if not pdf_present:
        capability_lost.append("PDF 预览未产出")
    if "pypdf" in sc["block"] and sc["pdf_material"]:
        capability_lost.append("PDF 材料的文本层不可读")
    degraded = bool(capability_lost)

    # expectations ---------------------------------------------------------------
    if rc not in exp.get("exit", (0,)):
        problems.append("exit %s 不在期望 %s 内" % (rc, list(exp.get("exit", (0,)))))
    if not result:
        problems.append("未写出 result.json（stderr: %s）" % (stderr or "").strip()[:120])
    if result and exp.get("status_in") and status not in exp["status_in"]:
        problems.append("status=%r 不在期望 %s 内" % (status, list(exp["status_in"])))
    if exp.get("png_backend") and backend != exp["png_backend"]:
        problems.append("PNG 后端=%r，期望 %r" % (backend, exp["png_backend"]))
    if exp.get("pdf_present") is not None and pdf_present != exp["pdf_present"]:
        problems.append("PDF present=%s，期望 %s" % (pdf_present, exp["pdf_present"]))
    if exp.get("svg_present") is not None and svg_present != exp["svg_present"]:
        problems.append("SVG 存在=%s，期望 %s" % (svg_present, exp["svg_present"]))
    if exp.get("png_present") is not None and png_present != exp["png_present"]:
        problems.append("PNG 存在=%s，期望 %s" % (png_present, exp["png_present"]))
    if exp.get("result_keys_min") and len(result) < exp["result_keys_min"]:
        problems.append("result.json 顶层键数 %d < %d" % (len(result), exp["result_keys_min"]))
    if exp.get("uncertainty_contains"):
        blob = " || ".join(str(x) for x in uncertainty + warnings)
        if exp["uncertainty_contains"].lower() not in blob.lower():
            problems.append("uncertainty/warnings 里找不到 %r" % exp["uncertainty_contains"])
    if exp.get("no_edge") and hits:
        problems.append("声明为无关依赖，却有命中日志：%s" % ", ".join(hits[:3]))
    if exp.get("pdf_reason_required") and not pdf_present and not pdf_entry.get("reason"):
        problems.append("PDF 未产出但 deliverables[pdf].reason 为空（不可见原因）")
    if exp.get("record_if_degraded") and degraded and not recorded:
        problems.append("能力降级（%s）但 uncertainty/warnings 均为空" % "；".join(capability_lost))

    # verdict --------------------------------------------------------------------
    silent = bool(problems) and degraded and not recorded and status == "success"
    if problems and not result:
        verdict = "crash"
    elif not problems:
        verdict = "ok"
    elif silent:
        verdict = "silent"
    else:
        verdict = "mismatch"

    if exp.get("no_edge") and not hits and not problems:
        observations.append("零影响：行为与对照组一致，且没有任何导入/调用尝试")
    if sc["block"] and not hits:
        observations.append("拦截目录已前置到 PYTHONPATH，但本次运行没有触发该导入")
    if hits:
        observations.append("命中日志：" + ", ".join(hits[:4]))
    if not pdf_present and pdf_entry.get("reason"):
        observations.append("PDF 缺席原因：" + str(pdf_entry["reason"])[:100])
    if font:
        observations.append("字体：%s" % font)

    return {
        "id": sc["id"],
        "title": sc["title"],
        "blocked_modules": sc["block"],
        "libreoffice_shimmed": sc["loco"],
        "pdf_material": sc["pdf_material"],
        "pdf_fixture": pdf_note,
        "expected": sc["expect"].get("rationale") or sc["rationale"],
        "measured_exit": rc,
        "measured_status": status,
        "result_json": bool(result),
        "result_top_keys": len(result),
        "deliverables": {"svg": svg_present, "png": png_present, "pdf": pdf_present,
                         "pdf_reason": pdf_entry.get("reason")},
        "png_backend": backend,
        "font": font,
        "render_warnings": (render_log or {}).get("warnings"),
        "uncertainty_n": len(uncertainty),
        "uncertainty_sample": [str(x)[:150] for x in uncertainty[:3]],
        "warnings_n": len(warnings),
        "warnings_sample": [str(x)[:150] for x in warnings[:2]],
        "shim_hits": hits,
        "capability_lost": capability_lost,
        "degradation_form": ("；".join(capability_lost) if capability_lost else "无（与完整环境一致）"),
        "verdict": verdict,
        "problems": problems,
        "observations": observations,
        "stdout_head": (stdout or "").strip().splitlines()[:2],
        "stderr_head": (stderr or "").strip().splitlines()[:2],
    }


def _print_table(rows):
    print("%-5s %-9s %-18s %-8s %-8s %-4s %-5s %s"
          % ("id", "verdict", "png_backend", "exit", "status", "unc", "pdf", "title"))
    print("-" * 132)
    for r in rows:
        print("%-5s %-9s %-18s %-8s %-8s %-4s %-5s %s"
              % (r["id"], r["verdict"], str(r["png_backend"]), r["measured_exit"],
                 str(r["measured_status"]), r["uncertainty_n"], r["deliverables"]["pdf"],
                 r["title"][:38]))
        for p in r["problems"]:
            print("        ! %s" % p)
        for o in r["observations"]:
            print("        ~ %s" % o)


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass
    ap = argparse.ArgumentParser(
        prog="degrade_probe",
        description="simulate missing python-pptx / PIL / matplotlib / numpy / yaml / "
                    "LibreOffice and record the real degradation of the pipeline")
    ap.add_argument("--out", required=True, help="directory for degrade_matrix.json (outside this package)")
    ap.add_argument("--case", default=os.path.join(SKILL_ROOT, "examples", "case.json"),
                    help="base case.json used as the fixture for every scenario")
    ap.add_argument("--only", default=None, help="run one scenario id (P09)")
    ap.add_argument("--fail-on", default="silent", choices=["silent", "strict", "none"],
                    help="silent = only invisible capability loss fails; strict = any mismatch")
    ap.add_argument("--keep", action="store_true", help="keep per-scenario sandboxes")
    ap.add_argument("--verbose", action="store_true", help="print per-scenario stdout/stderr heads")
    args = ap.parse_args(argv)

    base_path = os.path.abspath(args.case)
    base_case = _load_json(base_path)
    if not isinstance(base_case, dict):
        print(json.dumps({"status": "error", "error": "base case.json not found/invalid: %s"
                          % base_path}, ensure_ascii=False, indent=2))
        return 2
    scenarios = SCENARIOS
    if args.only:
        sel = args.only.lower()
        scenarios = [s for s in SCENARIOS if s["id"].lower() == sel]
        if not scenarios:
            print(json.dumps({"error": "no scenario matches --only %r" % args.only,
                              "ids": [s["id"] for s in SCENARIOS]}, ensure_ascii=False, indent=2))
            return 2

    out_root = os.path.abspath(args.out)
    if out_root == SKILL_ROOT or out_root.startswith(SKILL_ROOT + os.sep):
        print(json.dumps({"status": "error",
                          "error": "--out must be outside the skill package: %s" % out_root},
                         ensure_ascii=False, indent=2))
        return 2
    os.makedirs(out_root, exist_ok=True)
    sandbox_root = os.path.join(out_root, "_skill")
    if os.path.isdir(sandbox_root):
        shutil.rmtree(sandbox_root, ignore_errors=True)
    shutil.copytree(SCRIPT_DIR, os.path.join(sandbox_root, "scripts"))
    sandbox_skill = os.path.join(sandbox_root, "scripts")
    bin_dir = _build_bin_shims(out_root)
    counts, where, tool_counts = _import_sites(SCRIPT_DIR)

    rows, t0 = [], time.time()
    for sc in scenarios:
        row = run_one(sc, base_case, os.path.dirname(base_path), sandbox_skill, out_root,
                      bin_dir, keep=args.keep)
        rows.append(row)
        if args.verbose:
            print("[%s] exit=%s status=%s backend=%s verdict=%s"
                  % (row["id"], row["measured_exit"], row["measured_status"],
                     row["png_backend"], row["verdict"]))
            for line in row["stdout_head"]:
                print("    out| " + line[:150])
            for line in row["stderr_head"]:
                print("    err| " + line[:150])

    if not args.keep:
        shutil.rmtree(os.path.join(out_root, "_box"), ignore_errors=True)
        shutil.rmtree(sandbox_root, ignore_errors=True)

    by_id = {r["id"]: r for r in rows}
    control = by_id.get("P00")
    stdlib_only = by_id.get("P09")
    pil_only = by_id.get("P03")

    summary = {
        "scenarios_run": len(rows),
        "ok": sum(1 for r in rows if r["verdict"] == "ok"),
        "mismatch": sum(1 for r in rows if r["verdict"] == "mismatch"),
        "silent_capability_loss": sum(1 for r in rows if r["verdict"] == "silent"),
        "crash": sum(1 for r in rows if r["verdict"] == "crash"),
        "result_json_written": sum(1 for r in rows if r["result_json"]),
        "exit_zero": sum(1 for r in rows if r["measured_exit"] == 0),
        "seconds_total": round(time.time() - t0, 2),
        "zero_impact_scenarios": [r["id"] for r in rows
                                  if r["verdict"] == "ok" and not r["capability_lost"]],
    }
    silent_rows = [r["id"] for r in rows if r["verdict"] == "silent"]

    minimal = {
        "claim": "最小可用环境 = 纯标准库（Python 3.9+，无任何第三方包）",
        "evidence_scenario": "P09",
        "measured": ({} if not stdlib_only else {
            "exit": stdlib_only["measured_exit"],
            "status": stdlib_only["measured_status"],
            "svg": stdlib_only["deliverables"]["svg"],
            "png": stdlib_only["deliverables"]["png"],
            "png_backend": stdlib_only["png_backend"],
            "pdf": stdlib_only["deliverables"]["pdf"],
            "result_json": stdlib_only["result_json"],
            "result_top_keys": stdlib_only["result_top_keys"],
        }),
        "third_party_adds": {
            "matplotlib": ("抗锯齿位图 + 矢量 PDF 预览；缺它时 PNG 回退（见 P03/P04）"
                           if control else "未测"),
            "PIL": "位图文字（有系统字体时）；缺它且无 matplotlib 时文字退化为占位框（P08/P09）",
            "numpy": "matplotlib 的传递依赖，单独缺失的影响见 P04",
            "pypdf": "PDF 材料的文本层；缺它时 PDF 材料只记录『不可读』（P07）",
        },
        "not_used_by_this_skill": [m for m in ("pptx", "yaml", "LibreOffice")
                                   if counts.get(m if m != "LibreOffice" else "LibreOffice") == 0],
        "static_import_sites": counts,
    }

    report = {
        "schema": PROBE_SCHEMA,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "skill": "graphical-abstract",
        "python": sys.version.split()[0],
        "platform": sys.platform,
        "base_case": {"file": os.path.basename(base_path), "case_id": base_case.get("case_id")},
        "method": {
            "import_interception": "PYTHONPATH 前置 <out>/_shim/modules/<mod>/__init__.py："
                                   "写一行命中日志后 raise ImportError",
            "libreoffice_interception": "PATH 前置 <out>/_shim/bin/{soffice,libreoffice}[.cmd]："
                                        "写一行命中日志后 exit 127",
            "isolation": "每个场景一个独立子进程 + 独立工作目录；本机 site-packages 未被修改",
        },
        "import_sites": {"pipeline": counts, "tools": tool_counts, "where": where,
                         "excluded_tool_files": sorted(TOOL_FILES)},
        "summary": summary,
        "silent_loss_list": silent_rows,
        "minimal_environment": minimal,
        "reference_run": ("P00" if control else None),
        "scenarios": rows,
        "uncovered": [
            "字体文件缺失：本机系统字体真实存在，无法用导入拦截模拟；相关行为只在"
            "P08/P09（无绘图库 ⇒ 文字占位框）与 render_log.font 里间接体现",
            "平台侧依赖缺失（容器里没有 python 解释器、磁盘满、挂载只读）不在本矩阵范围",
            "第三方包**版本不兼容**（装了但导入即抛别的异常）不在本矩阵范围；"
            "拦截只模拟 ImportError",
            "本机没有 LibreOffice，因此 P10 的『不存在』就是本机真实状态（实测而非模拟）",
        ],
        "notes": [
            "判级口径：silent = 实测到能力丢失（后端降级 / PDF 不可用 / PDF 材料不可读），"
            "而 status 仍为 success 且 uncertainty 与 warnings 都为空。",
            "静态导入点统计（import_sites）与运行时命中日志（shim_hits）是两个独立证据："
            "前者说明代码里有没有依赖边，后者说明这条边在这次运行里有没有被走到。",
        ],
    }
    report_path = os.path.join(out_root, "degrade_matrix.json")
    with open(report_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    _print_table(rows)
    print("")
    print("summary: scenarios=%d ok=%d mismatch=%d silent=%d crash=%d result_json=%d/=%d "
          "exit0=%d  %.1fs"
          % (summary["scenarios_run"], summary["ok"], summary["mismatch"],
             summary["silent_capability_loss"], summary["crash"], summary["result_json_written"],
             summary["scenarios_run"], summary["exit_zero"], summary["seconds_total"]))
    print("report: %s" % report_path)

    if args.fail_on == "none":
        return 0
    if args.fail_on == "strict":
        return 0 if summary["ok"] == summary["scenarios_run"] else 1
    return 0 if not silent_rows and not summary["crash"] else 1


if __name__ == "__main__":
    sys.exit(main())
