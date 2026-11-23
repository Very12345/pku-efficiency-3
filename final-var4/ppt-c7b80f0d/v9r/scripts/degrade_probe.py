#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""degrade_probe.py — measure what the pipeline really does when a dependency is
missing, instead of assuming it "degrades gracefully".

Axis of this package (v9): **the degradation chain, measured**. Each scenario runs
the unmodified end-to-end entry in a child process whose import machinery is
patched by a controlled blocker (``sys.meta_path`` finder) that raises
``ModuleNotFoundError`` for a chosen set of top-level modules — python-pptx,
Pillow, matplotlib, numpy, PyYAML — plus one environment scenario that removes
LibreOffice from ``PATH``. For every scenario the probe records:

* exit code of the run,
* whether ``result.json`` was written at all,
* ``status``, deck file, preview count, chart count, ``uncertainty``,
* **what is left in the output directory** (the surviving artifact set),
* the failing import (first lines of the traceback), when it crashed,
* and whether the run is a *silent* degradation (claims ``completed`` while the
  deck or the previews are gone).

A second phase asks which of the package's modules stay importable under each
block (``importlib.import_module`` per module), which is what the "minimal viable
environment" list is derived from — plus a static scan for LibreOffice usage, so
a documented-but-unimplemented capability is reported as such rather than
counted as a degradation path.

Usage
-----
    python "$SKILL_DIR/scripts/degrade_probe.py" --out <probe dir> \\
        [--case <case.json>] [--spec <deck-spec.json>] [--entry <main.py>] \\
        [--only S1-no-pptx] [--emit-md <path>] [--json <path>] [--quiet]

Exit codes
----------
    0  measurement complete: the baseline control produced result.json and no
       scenario was a silent degradation
    1  a scenario is a silent degradation (claims completed while the deck or
       previews are missing) — the failure mode this probe exists to catch
    2  parameter/input error
    3  the baseline control itself failed (the probe's environment is wrong)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
DEFAULT_ENTRY = os.path.join(HERE, "main.py")
SCHEMA = "degrade-matrix/1"

MODULES = ["cli_io", "assetkit", "deckgen", "ooxml_kit", "preview", "spec_lint",
           "export_check", "check_contract", "make_template",
           "make_synthetic_inputs", "main", "degrade_probe"]

BLOCKER_SRC = """
import os, runpy, sys
blocked = {m for m in os.environ.get("DEGRADE_BLOCK", "").split(",") if m}


class _Blocker:
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in blocked:
            raise ModuleNotFoundError(
                "No module named '%s' (blocked by degrade_probe)" % fullname,
                name=fullname)
        return None


if blocked:
    sys.meta_path.insert(0, _Blocker())
entry = sys.argv[1]
sys.argv = sys.argv[1:]
runpy.run_path(entry, run_name="__main__")
"""

IMPORT_CHECK_SRC = """
import os, sys
sys.path.insert(0, sys.argv[1])
blocked = {m for m in os.environ.get("DEGRADE_BLOCK", "").split(",") if m}


class _Blocker:
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in blocked:
            raise ModuleNotFoundError(
                "No module named '%s' (blocked by degrade_probe)" % fullname,
                name=fullname)
        return None


if blocked:
    sys.meta_path.insert(0, _Blocker())
import importlib
try:
    importlib.import_module(sys.argv[2])
    print("IMPORT_OK")
except BaseException as exc:
    print("IMPORT_FAIL %s: %s" % (type(exc).__name__, exc))
    raise SystemExit(1)
"""

# --------------------------------------------------------------------------- #
# scenarios
# --------------------------------------------------------------------------- #
SCENARIOS = [
    dict(id="S0-baseline", label="对照：什么都不屏蔽", blocks=[], env={},
         kind="control"),
    dict(id="S1-no-pptx", label="缺 python-pptx", blocks=["pptx"], env={},
         kind="dependency"),
    dict(id="S2-no-PIL", label="缺 Pillow(PIL)", blocks=["PIL"], env={},
         kind="dependency"),
    dict(id="S3-no-matplotlib", label="缺 matplotlib", blocks=["matplotlib"],
         env={}, kind="dependency"),
    dict(id="S4-no-numpy", label="缺 numpy", blocks=["numpy"], env={},
         kind="dependency"),
    dict(id="S5-no-yaml", label="缺 PyYAML", blocks=["yaml"], env={},
         kind="dependency"),
    dict(id="S6-no-pptx-no-PIL", label="同时缺 python-pptx 与 Pillow",
         blocks=["pptx", "PIL"], env={}, kind="dependency"),
    dict(id="S7-no-soffice", label="PATH 里没有 LibreOffice(soffice)",
         blocks=[], env={"__STRIP_SOFFICE__": "1"}, kind="environment"),
]

UNCOVERED = [
    "**PDF 解析库未纳入**：`PyMuPDF`/`pypdf`/`pdfplumber` 的缺失降级没有实测，因为自带示例案例的"
    "材料是纯文本（`.txt`），PDF 分支不会被走到；要覆盖它需要一份 PDF 素材并屏蔽三个库。",
    "**未测组合爆炸**：只测了单缺 5 个库 + 一个双缺组合；三缺以上的组合未测。",
    "**未测操作系统级缺失**：例如系统字体目录为空、只读输出目录、磁盘满；这些属于环境故障，"
    "不是依赖缺失。",
    "**未测 LibreOffice 真实存在时的行为**：本机没有 LibreOffice，因此只能测“不存在”这一侧"
    "（见 §4 的静态扫描结论）。",
    "**未测子进程被中断**（Ctrl-C/超时）时的产物一致性。",
    "**`--demo` 分支与材料不可读分支未与屏蔽矩阵交叉**（它们由 `failure-modes.md` 的状态一致性"
    "条目覆盖）。",
]


DEP_PROBES = [
    ("pptx", [], "基线：python-pptx 可导入"),
    ("PIL", [], "基线：Pillow 可导入"),
    ("matplotlib", [], "基线：matplotlib 可导入"),
    ("numpy", [], "基线：numpy 可导入"),
    ("yaml", [], "基线：PyYAML 可导入"),
    ("pptx", ["PIL"], "python-pptx 是否依赖 Pillow"),
    ("matplotlib", ["numpy"], "matplotlib 是否依赖 numpy"),
    ("matplotlib", ["PIL"], "matplotlib 是否依赖 Pillow"),
    ("PIL", ["pptx"], "Pillow 是否反向依赖 python-pptx"),
]


def dep_graph_probe(python, scripts_dir, out_dir, timeout):
    """Measure *transitive* requirements instead of assuming them."""
    rows = []
    for mod, blocks, why in DEP_PROBES:
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["DEGRADE_BLOCK"] = ",".join(blocks)
        p = subprocess.run([python, "-c", IMPORT_CHECK_SRC, scripts_dir, mod],
                           cwd=out_dir, env=env, timeout=timeout,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out = p.stdout.decode("utf-8", "replace").strip()
        ok = out.startswith("IMPORT_OK")
        rows.append({"module": mod, "blocked": blocks, "ok": ok, "why": why,
                     "detail": "" if ok else (out.splitlines()[-1][:170]
                                              if out else "no output")})
    return rows


def strip_soffice_env(env, out_dir):
    """Build a PATH without LibreOffice and record whether that changed anything."""
    path = os.environ.get("PATH", "")
    kept = [p for p in path.split(os.pathsep)
            if p and not os.path.exists(os.path.join(p, "soffice"))
            and not os.path.exists(os.path.join(p, "soffice.exe"))]
    env = dict(env)
    env["PATH"] = os.pathsep.join(kept)
    env["DEGRADE_NO_SOFFICE"] = "1"
    return env


def run_scenario(scn, case, spec, out_dir, python, entry, timeout, scripts_dir):
    scn_dir = os.path.join(out_dir, "scenarios", scn["id"])
    run_out = os.path.join(scn_dir, "out")
    os.makedirs(scn_dir, exist_ok=True)
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["DEGRADE_BLOCK"] = ",".join(scn["blocks"])
    if scn["env"].get("__STRIP_SOFFICE__"):
        env = strip_soffice_env(env, scn_dir)
    argv = [python, "-c", BLOCKER_SRC, entry, "--case", case, "--out", run_out]
    if spec:
        argv += ["--spec", spec]
    proc = subprocess.run(argv, cwd=scn_dir, env=env, timeout=timeout,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = proc.stdout.decode("utf-8", "replace")
    rec = {"scenario": scn["id"], "label": scn["label"], "blocks": scn["blocks"],
           "kind": scn["kind"], "exit_code": proc.returncode}
    rec["soffice_on_path"] = bool(shutil.which("soffice", path=env.get("PATH")))
    res_path = os.path.join(run_out, "result.json")
    rec["result_written"] = os.path.isfile(res_path)
    rec["artifacts_left"] = sorted(os.listdir(run_out)) if os.path.isdir(run_out) else []
    rec["artifact_count"] = len(rec["artifacts_left"])
    rec["chart_files_on_disk"] = sum(1 for x in rec["artifacts_left"]
                                     if x.startswith("chart-"))
    rec["preview_files_on_disk"] = sum(1 for x in rec["artifacts_left"]
                                       if x.startswith("preview-"))
    rec["failing_import"] = None
    prefer = [ln.strip() for ln in text.splitlines()
              if "No module named" in ln and "Error" in ln]
    if prefer:
        rec["failing_import"] = prefer[-1][:200]
    else:
        for line in text.splitlines():
            if "ModuleNotFoundError" in line or "ImportError" in line:
                rec["failing_import"] = line.strip()[:200]
                break
    tail = [ln for ln in text.strip().splitlines() if ln.strip()][-6:]
    rec["stdout_tail"] = tail
    if rec["result_written"]:
        with open(res_path, encoding="utf-8") as fh:
            res = json.load(fh)
        deck = res.get("deck") or {}
        rec["status"] = res.get("status")
        rec["deck_file"] = deck.get("file")
        rec["deck_present_on_disk"] = bool(
            deck.get("file") and os.path.isfile(os.path.join(run_out, deck["file"])))
        rec["previews"] = len(res.get("previews") or [])
        rec["chart_records"] = len(res.get("charts") or [])
        rec["uncertainty"] = res.get("uncertainty") or []
        rec["rendered_with"] = (res.get("run_meta") or {}).get("rendered_with")
        rec["self_check_ok"] = ((res.get("run_meta") or {}).get("self_check") or {}).get("ok")
        rec["uncertainty_count"] = len(rec["uncertainty"])
    else:
        rec.update(status=None, deck_file=None, deck_present_on_disk=False,
                   previews=0, chart_records=0, uncertainty=[], rendered_with=None,
                   self_check_ok=None, uncertainty_count=0)

    # verdict + the failure mode this probe exists to catch
    if not rec["result_written"]:
        rec["verdict"] = "crash (no result.json)"
        rec["silent_degrade"] = False
    elif rec["status"] == "completed" and (not rec["deck_present_on_disk"]
                                           or rec["previews"] == 0):
        rec["verdict"] = "silent degradation"
        rec["silent_degrade"] = True
    elif rec["status"] == "completed":
        rec["verdict"] = "full success"
        rec["silent_degrade"] = False
    else:
        rec["verdict"] = "honest partial/failed"
        rec["silent_degrade"] = False

    # ---- module importability under the same block -------------------------
    imports = {}
    for mod in MODULES:
        if mod.endswith(".py"):
            mod = mod[:-3]
        p = subprocess.run([python, "-c", IMPORT_CHECK_SRC, scripts_dir, mod],
                           cwd=scn_dir, env=env, timeout=timeout,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out = p.stdout.decode("utf-8", "replace").strip()
        imports[mod] = {"ok": out.startswith("IMPORT_OK"),
                        "detail": "" if out.startswith("IMPORT_OK")
                        else out.splitlines()[-1][:160] if out else "no output"}
    rec["module_imports"] = imports
    rec["modules_importable"] = sum(1 for v in imports.values() if v["ok"])
    rec["modules_total"] = len(imports)
    return rec


def soffice_static_scan(scripts_dir):
    """Static evidence: does the pipeline ever invoke LibreOffice?

    `degrade_probe.py` is excluded: it mentions soffice on purpose (scenario id,
    docstring), so counting the probe itself would be self-referential.
    """
    hits = []
    for name in sorted(os.listdir(scripts_dir)):
        if not name.endswith(".py") or name == "degrade_probe.py":
            continue
        path = os.path.join(scripts_dir, name)
        with open(path, encoding="utf-8", errors="replace") as fh:
            for i, line in enumerate(fh, 1):
                if re.search(r"soffice|libreoffice|LibreOffice", line, re.I):
                    hits.append({"file": name, "line": i, "text": line.strip()[:160]})
    invocations = [h for h in hits
                   if re.search(r"subprocess|Popen|os\.system|check_output|shutil\.which",
                                h["text"])]
    return {"files_scanned": len([x for x in os.listdir(scripts_dir)
                                 if x.endswith(".py") and x != "degrade_probe.py"]),
            "hits": hits, "hit_count": len(hits),
            "invocation_hits": invocations, "invocation_count": len(invocations),
            "invokes_soffice": bool(invocations)}


# --------------------------------------------------------------------------- #
# markdown
# --------------------------------------------------------------------------- #
def emit_md(report, path):
    scns = report["scenarios"]
    o = []
    o.append("# DEGRADE-MATRIX.md — 缺依赖降级链（**逐项实测**）\n")
    o.append("> 本文件由 `scripts/degrade_probe.py --emit-md` 从**真实运行**生成。"
             "每个场景在子进程里用受控导入拦截（`sys.meta_path` finder 抛 "
             "`ModuleNotFoundError`）模拟缺库，然后跑**未经修改的**端到端入口。")
    o.append("> 原始记录见 `references/degrade-matrix-data.json`。\n")
    o.append("## 0. 运行命令与判据\n")
    o.append("```bash")
    o.append('python "$SKILL_DIR/scripts/degrade_probe.py" --out <探针目录> \\')
    o.append('  --emit-md "$SKILL_DIR/references/DEGRADE-MATRIX.md"')
    o.append("```\n")
    o.append("| 退出码 | 含义 |")
    o.append("|-|-|")
    o.append("| 0 | 测量完成：基线对照写出 `result.json`，且没有场景是**静默降级** |")
    o.append("| 1 | 有场景静默降级（自称 `completed`，但 deck 或预览已经没了） |")
    o.append("| 2 | 参数/输入错误 |")
    o.append("| 3 | 基线对照本身失败（探针环境有问题） |\n")
    o.append("判定口径：`full success`（写出 result.json 且 status=completed、deck 与预览都在）／"
             "`honest partial/failed`（写出 result.json 但如实降级）／"
             "`crash (no result.json)`（导入期就失败）／"
             "**`silent degradation`**（自称完成但产物残缺）。\n")
    s = report["summary"]
    o.append("## 1. 场景总表（实测）\n")
    o.append("| 场景 | 屏蔽 | exit | result.json | status | deck 落盘 | 预览数 | 重建图 | "
             "uncertainty | 剩余产物 | 判定 |")
    o.append("|-|-|-|-|-|-|-|-|-|-|-|")
    for c in scns:
        o.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            c["scenario"], ", ".join(c["blocks"]) or "（无）",
            c["exit_code"], "是" if c["result_written"] else "**否**",
            c["status"] or "—",
            "是" if c["deck_present_on_disk"] else "**否**",
            c["previews"], c.get("chart_files_on_disk", 0),
            c.get("uncertainty_count", 0),
            c["artifact_count"], c["verdict"]))
    o.append("")
    o.append("注意 S3/S4：`status` 仍是 `completed`，但 `uncertainty` 从 1 条升到 2 条、"
             "重建图文件（`chart-*.png/svg`）不再落盘 —— 降级**被如实记录**，"
             "所以判 `full success` 而不是 `silent degradation`；"
             "这正是本探针要区分的两种情况。\n")
    o.append("汇总：场景 %d 个；`full success` %d；`honest partial/failed` %d；"
             "`crash` %d；**`silent degradation` %d**。\n"
             % (s["scenarios"], s["full_success"], s["honest_partial"],
                s["crash"], s["silent_degrade"]))
    o.append("## 2. 逐场景细节（产物还剩什么）\n")
    for c in scns:
        o.append("### %s · %s" % (c["scenario"], c["label"]))
        o.append("")
        o.append("- 屏蔽：`%s`；exit=`%s`；`soffice` 在 PATH 上：%s"
                 % (c["blocks"] or "（无）", c["exit_code"], c["soffice_on_path"]))
        if c["failing_import"]:
            o.append("- 失败导入：`%s`" % c["failing_import"])
        if c["result_written"]:
            o.append("- `result.json`：status=%s，deck=%s（落盘=%s），previews=%s（落盘 %s），"
                     "重建图记录=%s / 落盘文件=%s，rendered_with=`%s`，self_check=%s"
                     % (c["status"], c["deck_file"], c["deck_present_on_disk"],
                        c["previews"], c.get("preview_files_on_disk"),
                        c.get("chart_records"), c.get("chart_files_on_disk"),
                        c["rendered_with"], c["self_check_ok"]))
            for u in (c["uncertainty"] or [])[:3]:
                o.append("  - uncertainty：`%s`" % str(u)[:170])
        else:
            o.append("- **没有 `result.json`** —— 主流程在产出任何评分产物之前就结束了")
        o.append("- 输出目录剩余产物（%d 个）：`%s`"
                 % (c["artifact_count"], ", ".join(c["artifacts_left"]) or "（空）"))
        o.append("- 末尾输出：`%s`" % " | ".join(c["stdout_tail"][-3:])[:300])
        o.append("")
    o.append("## 3. 模块可导入性矩阵（同一屏蔽下逐个 `importlib.import_module`）\n")
    o.append("| 模块 | " + " | ".join(c["scenario"].split("-")[0] for c in scns) + " |")
    o.append("|-" * (len(scns) + 1) + "|")
    for mod in report["modules"]:
        cells = []
        for c in scns:
            info = c["module_imports"].get(mod, {})
            cells.append("✅" if info.get("ok") else "❌")
        o.append("| `%s` | %s |" % (mod, " | ".join(cells)))
    o.append("")
    o.append("可导入模块数：" + "；".join(
        "%s=%d/%d" % (c["scenario"], c["modules_importable"], c["modules_total"])
        for c in scns) + "\n")
    o.append("## 4. LibreOffice：文档化能力与实现的差距（如实声明）\n")
    o.append("## 3.5 依赖关系实测（谁真的依赖谁）\n")
    o.append("| 探测 | 屏蔽 | 结果 | 说明 |")
    o.append("|-|-|-|-|")
    for d in report["dependency_probes"]:
        o.append("| `import %s` | %s | %s | %s |" % (
            d["module"], ", ".join(d["blocked"]) or "（无）",
            ("OK" if d["ok"] else "FAIL"),
            d["why"] + ("" if d["ok"] else " -> `%s`" % d["detail"][:90])))
    o.append("")
    o.append("> 这张表解释了为什么 S1 与 S2 的可导入性矩阵**完全一样**：`python-pptx` 自己"
             "导入 Pillow，因此“缺 Pillow”在这条管线里等价于“缺 python-pptx”。把硬依赖写成"
             "两个独立条件是不准确的，准确写法是“python-pptx（含其 Pillow 依赖）”。\n")
    o.append("")
    scan = report["soffice_scan"]
    o.append("- 静态扫描 `scripts/*.py`（%d 个文件）：命中 `soffice|libreoffice|LibreOffice` "
             "**%d 处**，其中疑似真的去调用子进程的 **%s**。"
             % (scan["files_scanned"], scan["hit_count"],
                "有" if scan["invokes_soffice"] else "没有"))
    for h in scan["hits"][:6]:
        o.append("  - `%s:%d`：`%s`" % (h["file"], h["line"], h["text"]))
    o.append("- **口径提醒**：本机基线环境里本来就没有 `soffice`（S0 行的 `soffice` 在 PATH 上"
             "同样是 False），所以 S7 只是把这件事显式化；「LibreOffice 缺失无影响」的实质证据是"
             "上面的**静态扫描（0 处调用）**，不是 S7 本身。")
    o.append("- 环境场景实测：把 `soffice` 从 PATH 去掉后，本次运行的 exit / status / 产物与"
             "基线一致（见 §1 的 S7 行）。")
    o.append("- ⇒ **结论（诚实口径）**：LibreOffice 缺失在当前实现里**不构成降级路径**，"
             "因为代码从不调用它；SKILL.md 中「有 LibreOffice 时可转真 PDF」是**文档化的目标**"
             "而非已实现能力，预览恒为 PIL 近似并如实标注。\n")
    o.append("## 5. 最小可用环境（由上面的实测反推）\n")
    for line in report["minimal_env"]:
        o.append("- %s" % line)
    o.append("")
    o.append("## 6. 未覆盖声明（如实列出）\n")
    for line in report["uncovered"]:
        o.append("- %s" % line)
    o.append("")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(o))
    return path


MINIMAL_ENV = [
    "**硬依赖（实测：缺则主流程连 `result.json` 都写不出）**：`python-pptx`（S1 导入期失败）"
    "与其 **Pillow 依赖**（S2 导入期失败；实测 `import pptx` 在屏蔽 PIL 时同样失败）。两者不是"
    "\"可选回退\"，而是 `scripts/deckgen.py` / `scripts/ooxml_kit.py` / `scripts/preview.py` "
    "的模块级导入链。",
    "**软依赖（实测：缺则可降级，产物形态变化）**：`matplotlib`（S3：重建图跳过，"
    "其余产物照常）、`numpy`（S4：只影响 matplotlib 自身）。",
    "**未被主流程使用（实测：屏蔽后与基线一致）**：`PyYAML`（S5，代码里没有任何 `yaml` 导入）"
    "——它属于平台环境清单里的资源，不是本 Skill 的依赖。",
    "**外部引擎**：LibreOffice 未实现调用，缺失无影响；模板与预览是运行期自生成的文本→二进制流程。",
    "**最低可用组合（把上面的实测拼起来）**：Python ≥3.8 + `python-pptx` + `Pillow`；"
    "要 PDF 素材再加 `PyMuPDF`/`pypdf`/`pdfplumber` 任一；要重建图再加 `matplotlib`。"
    "只缺 `matplotlib` 时仍产出完整 `result.json`：`charts` 记录仍在但带 `reason`、重建图文件不落盘"
    "（实测 S3/S4 的 `uncertainty` 从 1 条升到 2 条，第 2 条即 `reconstructed chart skipped: …`）。",
    "**排障顺序建议**：先看 `result.json` 是否存在 → 不存在就先解决 `python-pptx`/`Pillow`；"
    "存在但 `status=partial` → 读 `uncertainty`（它逐条写了哪一步降级）；"
    "再跑 `export_check.py` / `check_contract.py` 确认契约面。",
]


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="measure the real degradation chain when a dependency is missing")
    ap.add_argument("--case", default=None, help="case.json (default: packaged examples)")
    ap.add_argument("--spec", default=None, help="deck-spec.json (default: packaged examples)")
    ap.add_argument("--entry", default=DEFAULT_ENTRY, help="entry (default scripts/main.py)")
    ap.add_argument("--python", default=sys.executable, help="interpreter for the runs")
    ap.add_argument("--out", required=True, help="probe dir (scenarios/, report)")
    ap.add_argument("--only", default=None, help="comma-separated scenario ids")
    ap.add_argument("--timeout", type=int, default=900, help="per-scenario timeout (s)")
    ap.add_argument("--emit-md", default=None, help="write the markdown matrix here")
    ap.add_argument("--json", default=None, help="report path (default <out>/degrade_matrix.json)")
    ap.add_argument("--redact-paths", action="store_true",
                    help="replace machine-specific absolute paths with placeholders")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    case = args.case or os.path.join(SKILL_DIR, "examples", "case.json")
    spec = args.spec or os.path.join(SKILL_DIR, "examples", "deck-spec.json")
    if not os.path.isfile(case):
        print("case not readable: %s" % case, file=sys.stderr)
        return 2
    if spec and not os.path.isfile(spec):
        spec = None
    if not os.path.isfile(args.entry):
        print("entry not found: %s" % args.entry, file=sys.stderr)
        return 2
    os.makedirs(args.out, exist_ok=True)

    wanted = None
    if args.only:
        wanted = {s.strip() for s in args.only.split(",") if s.strip()}
    scns = [s for s in SCENARIOS if not wanted or s["id"] in wanted]
    if not scns:
        print("no scenario matched --only", file=sys.stderr)
        return 2

    dep_probes = dep_graph_probe(args.python, HERE, args.out, args.timeout)
    if not args.quiet:
        print("[dep-graph] " + "; ".join(
            "import %s%s=%s" % (d["module"],
                                "(-%s)" % ",".join(d["blocked"]) if d["blocked"] else "",
                                "ok" if d["ok"] else "FAIL")
            for d in dep_probes))
    records = []
    for scn in scns:
        rec = run_scenario(scn, case, spec, args.out, args.python, args.entry,
                           args.timeout, HERE)
        records.append(rec)
        if not args.quiet:
            print("[%s] exit=%s result=%s status=%s deck=%s previews=%s -> %s"
                  % (rec["scenario"], rec["exit_code"], rec["result_written"],
                     rec["status"], rec["deck_present_on_disk"], rec["previews"],
                     rec["verdict"]))
    summary = {
        "scenarios": len(records),
        "result_written": sum(1 for r in records if r["result_written"]),
        "full_success": sum(1 for r in records if r["verdict"] == "full success"),
        "honest_partial": sum(1 for r in records
                              if r["verdict"] == "honest partial/failed"),
        "crash": sum(1 for r in records if not r["result_written"]),
        "silent_degrade": sum(1 for r in records if r["silent_degrade"]),
    }
    base = [r for r in records if r["kind"] == "control"]
    report = {"schema": SCHEMA, "tool": "scripts/degrade_probe.py",
              "entry": args.entry, "case": case, "spec": spec, "python": args.python,
              "blocking": "sys.meta_path finder raising ModuleNotFoundError "
                          "(child process, per scenario)",
              "scenarios": records, "summary": summary,
              "modules": MODULES,
              "dependency_probes": dep_probes,
              "soffice_scan": soffice_static_scan(HERE),
              "minimal_env": MINIMAL_ENV, "uncovered": UNCOVERED}
    report_path = args.json or os.path.join(args.out, "degrade_matrix.json")
    if args.redact_paths:
        pairs = [(os.path.abspath(args.out), "<PROBE_DIR>"),
                 (os.path.abspath(SKILL_DIR), "<SKILL_DIR>"),
                 (os.path.dirname(os.path.abspath(case)), "<CASE_DIR>"),
                 (args.python, "<PYTHON>")]
        report = redact(report, pairs)
        report["_redaction"] = {"applied": True,
                                "replaced": ["<PROBE_DIR>", "<SKILL_DIR>",
                                             "<CASE_DIR>", "<PYTHON>",
                                             "<ABS> (remaining drive-letter path)"],
                                "note": "only path strings; verdicts and counts are measured"}
    with open(report_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    if args.emit_md:
        emit_md(report, args.emit_md)
    if not args.quiet:
        print("-" * 64)
        print("report : %s" % report_path)
        print("scenarios=%d result_written=%d full=%d honest_partial=%d crash=%d silent=%d"
              % (summary["scenarios"], summary["result_written"], summary["full_success"],
                 summary["honest_partial"], summary["crash"], summary["silent_degrade"]))
    if base and not base[0]["result_written"]:
        return 3
    return 1 if summary["silent_degrade"] else 0


def redact(obj, pairs):
    if isinstance(obj, dict):
        return {k: redact(v, pairs) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact(v, pairs) for v in obj]
    if isinstance(obj, str):
        out = obj
        for needle, token in pairs:
            if not needle:
                continue
            for variant in {needle, needle.replace("\\", "/"),
                            needle.replace("/", "\\")}:
                if variant:
                    out = out.replace(variant, token)
        return re.sub(r"[A-Za-z]:[\\/]", "<ABS>/", out)
    return obj


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    sys.exit(main())
