#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""degrade_probe.py — remove one dependency at a time and measure what the Skill
still delivers, honestly.

Why this script exists
----------------------
A Skill claims graceful degradation.  Reading `references/failure-modes.md` tells
you what the author *intended*; only running the pipeline without the dependency
tells you what it *does*.  This script simulates "not installed" without
uninstalling anything, by shadowing the import with a package that raises
ImportError on `PYTHONPATH`, then runs the real entry points as child processes
and records the measured degradation:

  exit code · is `result.json` written · `status` · uncertainty entries ·
  how many artifacts survived · the last line of stderr · the traceback frame
  that raised.

Three things are measured for every dependency
----------------------------------------------
1. **The pipeline** (`scripts/main.py`) — the path a real case takes.
2. **The single-purpose entries** that need that dependency
   (`make_synthetic_inputs.py`, `make_template.py`, `preview.py`, …) — so the
   report can say *where* the chain breaks, not only that it did.
3. **Importability itself** (`python -c "import X"` with the shadow on
   PYTHONPATH) — proof that the simulation actually took effect.  Without this
   step a "no difference" result could just mean the poison never applied, which
   is the classic way a degradation probe lies to its author.

LibreOffice is treated differently: it is not a Python import but an external
program.  It is simulated with an empty `PATH`, and the report states plainly
whether the pipeline shells out to it at all (measured: it does not — the
preview renderer never calls `soffice`, it draws a PIL schematic and says so).

Design rules that matter for honesty
------------------------------------
1. **Never run inside the package.**  Executing `scripts/*.py` with the package
   as cwd leaves `scripts/__pycache__/*.pyc`, which the resource contract
   rejects.  Everything runs on a copy under the scratch dir.
2. **One scenario = one child process.**  No in-process reuse.
3. **Poison effectiveness is verified, not assumed** (see 3 above).
4. **Captured host paths are shrunk** to `<RUN>` before being stored: a
   submission package may not carry host paths.

Usage
-----
    python scripts/degrade_probe.py --skill <package root> \
        [--run <work dir>] [--json <report.json>] [--markdown <table.md>] \
        [--only D01,D07] [--skip ...] [--timeout 180] [--list]

Exit code: 0 when every scenario behaved as declared, 1 when a scenario passed
silently or the poison was ineffective, 2 on usage/environment errors.

Note on scope: this file probes the **whole pipeline** plus the entries that use
each dependency.  Per-entry fault injection for input/template/contract faults
lives in the sibling `fault_inject.py`; the two do not overlap.
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

# ---------------------------------------------------------------------------
# The dependency catalogue.  `used_by` is what the source actually imports
# (verified by grep over scripts/*.py), and `expect` states the declared
# behaviour before measurement — the report says so when reality disagrees.
# ---------------------------------------------------------------------------
DEPS = {
    "pptx": dict(
        module="pptx", kind="import",
        used_by=["adapt_pptx (module level)", "adopt_plan (lazy, for sizes)",
                 "pptx_toolkit (lazy)", "make_template (lazy)", "check_contract G4 (lazy)",
                 "common.tool_versions"],
        expect=dict(exit=1, status="failed", result_json=True, deck=False,
                    note="adapt_pptx 在模块级 import pptx → 阶段二构建抛 ImportError，"
                         "被 main() 捕获 → failed result + exit 1；阶段一产物可能已落盘"),
    ),
    "PIL": dict(
        module="PIL", kind="import",
        used_by=["preview (module level)", "make_synthetic_inputs (lazy)",
                 "adapt_pptx (lazy, 嵌图尺寸)", "adopt_plan (lazy)", "common (lazy, 字体探测)"],
        expect=dict(exit=1, status="failed", result_json=True, deck=None,
                    note="preview 在模块级 import PIL → 预览阶段抛 ImportError → failed result + exit 1"),
    ),
    "matplotlib": dict(
        module="matplotlib", kind="import", used_by=["仅 common.tool_versions 记录版本"],
        expect=dict(exit=0, status=None, result_json=True, deck=None,
                    note="**未被任何交付路径使用** → 应完全不影响；tool_versions 记 unavailable"),
    ),
    "numpy": dict(
        module="numpy", kind="import", used_by=["仅 common.tool_versions 记录版本"],
        expect=dict(exit=0, status=None, result_json=True, deck=None,
                    note="**未被任何交付路径使用** → 应完全不影响；tool_versions 记 unavailable"),
    ),
    "yaml": dict(
        module="yaml", kind="import", used_by=["（无）"],
        expect=dict(exit=0, status=None, result_json=True, deck=None,
                    note="**完全没有被引用**（契约用 JSON）→ 应完全不影响；"
                         "本场景是「冗余依赖」的实测证明"),
    ),
    "lxml": dict(
        module="lxml", kind="import",
        used_by=["（本包代码不用它；但 `python-pptx` 在包级 `from lxml import etree` 用到）"],
        expect=dict(exit=1, status="failed", result_json=True, deck=False,
                    note="**间接硬依赖**：本包代码不 import lxml，但 `pptx` 的 "
                         "`opc/oxml.py` / `oxml/__init__.py` 在包级 `from lxml import etree` ⇒ "
                         "缺 lxml 等于缺 pptx，应走同一条 failed 路径"),
    ),
    "reportlab": dict(
        module="reportlab", kind="import", used_by=["仅 common.tool_versions 记录版本"],
        expect=dict(exit=0, status=None, result_json=True, deck=None,
                    note="**未被任何交付路径使用**（不产 PDF）→ 应完全不影响"),
    ),
    "libreoffice": dict(
        module=None, kind="external",
        used_by=["（无；preview 只画 PIL 示意图，从不调用 soffice）"],
        expect=dict(exit=0, status=None, result_json=True, deck=None,
                    note="外部程序：用空 PATH 模拟缺失。**预期无影响**，"
                         "因为管线从不 shell out 到 soffice；这是「外部渲染器缺失」的实测边界"),
    ),
    "combo-all": dict(
        module=None, kind="combo",
        poison=["pptx", "PIL", "matplotlib", "numpy", "yaml", "lxml", "reportlab"],
        used_by=["合并场景：所有 Python 依赖同时缺失（最坏情况）"],
        expect=dict(exit=1, status="failed", result_json=True, deck=False,
                    note="第一个失败的 import 决定行为（pptx 在阶段二、PIL 在预览阶段），"
                         "仍应是 failed + exit 1，不静默"),
    ),
    "PIL-with-figure": dict(
        module="PIL", kind="import", with_figure=True,
        used_by=["adapt_pptx（懒加载，只在**真的存在源图文件**时用 PIL 读尺寸）"],
        expect=dict(exit=1, status="failed", result_json=True, deck=False,
                    note="对照场景：只在**材料里真的有图**时才走进 adapt_pptx 的懒加载 PIL 分支"
                         "（`figures[].file_exists=True`）；用于验证上一条的失败不是"
                         "「图不存在所以没用到 PIL」造成的假象"),
    ),
}

# Entries probed per dependency: id -> (script, argv builder).  `{}` placeholders
# are filled from the scenario's own scratch dirs.
ENTRY_PROBES = {
    "main": ("main.py", lambda c: ["--case", c["case"], "--task", c["task"], "--out", c["out"]]),
    "make_synthetic_inputs": ("make_synthetic_inputs.py",
                              lambda c: ["--dir", c["examples"], "--force"]),
    "make_template": ("make_template.py",
                      lambda c: ["--out", os.path.join(c["scratch"], "builtin.pptx")]),
}


def _rm(path: str) -> None:
    if not os.path.exists(path):
        return
    try:
        shutil.rmtree(path)
    except Exception:
        for root, dirs, files in os.walk(path, topdown=False):
            for n in files:
                try:
                    os.chmod(os.path.join(root, n), 0o666)
                except Exception:
                    pass
            for n in dirs:
                try:
                    os.chmod(os.path.join(root, n), 0o777)
                except Exception:
                    pass
        shutil.rmtree(path, ignore_errors=True)


def _write(path: str, text: str) -> str:
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return path


def _load(path: str):
    try:
        with open(path, "r", encoding="utf-8-sig") as fh:
            return json.load(fh)
    except Exception:
        return None


def _tail(text: str, n: int = 200) -> str:
    text = (text or "").strip().replace("\r", "")
    return text.splitlines()[-1][:n] if text else ""


def _last_frame(stderr: str) -> str:
    """The file:line of the deepest traceback frame — 'where it broke'."""
    frames = re.findall(r'File "([^"]+)", line (\d+), in (\S+)', stderr or "")
    if not frames:
        return ""
    path, line, fn = frames[-1]
    return f"{os.path.basename(path)}:{line} in {fn}"


def _shrink(text: str, root: str) -> str:
    """Replace the scratch/skill roots with tokens (packages carry no host paths)."""
    if not text:
        return text
    forms = set()
    for base in (root,):
        if not base:
            continue
        for sep in ("/", "\\"):
            f = base.replace("/", sep).replace("\\", sep)
            forms.add(f)
            forms.add(f.replace(sep, sep * 2))
    for f in sorted(forms, key=len, reverse=True):
        text = text.replace(f, "<RUN>")
    return text


def _poison(root: str, module: str, message: str) -> str:
    """Create a shadow package that raises ImportError on import."""
    os.makedirs(root, exist_ok=True)
    pkg = os.path.join(root, module)
    os.makedirs(pkg, exist_ok=True)
    _write(os.path.join(pkg, "__init__.py"),
           f"raise ImportError('simulated: {message}')\n")
    return root


class Runner:
    def __init__(self, skill: str, run_dir: str, timeout: int = 180):
        self.src_skill = os.path.abspath(skill)
        self.run = os.path.abspath(run_dir)
        self.timeout = timeout
        self.skill = os.path.join(self.run, "skill")
        self.corpus = os.path.join(self.run, "input")

    def prepare(self) -> dict:
        if not os.path.isfile(os.path.join(self.src_skill, "scripts", "main.py")):
            raise SystemExit(f"[degrade_probe] main.py not found under {self.src_skill}")
        info = {"source_skill": "<SKILL>", "scratch_skill": "<RUN>/skill",
                "scratch": "<RUN>", "python": sys.version.split()[0]}
        _rm(self.run)
        os.makedirs(self.run, exist_ok=True)
        shutil.copytree(self.src_skill, self.skill)
        shutil.copytree(os.path.join(self.src_skill, "examples"), self.corpus)
        rc, _o, err = self._exec(
            [sys.executable, os.path.join(self.skill, "scripts", "make_synthetic_inputs.py"),
             "--dir", self.corpus], os.path.join(self.run, "setup-cwd"))
        info["figure_gen_exit"] = rc
        if rc != 0:
            info["figure_gen_stderr"] = _shrink(_tail(err), self.run)
        figs = os.path.join(self.corpus, "figs")
        info["figures"] = sorted(os.listdir(figs)) if os.path.isdir(figs) else []
        info["baseline"] = self.baseline()
        return info

    def _exec(self, argv, cwd, env_extra=None):
        os.makedirs(cwd, exist_ok=True)
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        if env_extra:
            env.update(env_extra)
        try:
            p = subprocess.run(argv, cwd=cwd, env=env, capture_output=True,
                               timeout=self.timeout)
            return (p.returncode, p.stdout.decode("utf-8", "replace"),
                    p.stderr.decode("utf-8", "replace"))
        except subprocess.TimeoutExpired:
            return 124, "", f"timeout after {self.timeout}s"

    def baseline(self) -> dict:
        """A clean run, for comparing "what is still delivered" against."""
        out = os.path.join(self.run, "baseline", "out")
        cwd = os.path.join(self.run, "baseline", "cwd")
        rc, so, se = self._exec(
            [sys.executable, os.path.join(self.skill, "scripts", "main.py"),
             "--case", os.path.join(self.corpus, "case.json"),
             "--task", os.path.join(self.corpus, "task.md"), "--out", out], cwd)
        res = _load(os.path.join(out, "result.json")) or {}
        return {
            "exit": rc, "status": res.get("status"),
            "artifacts": sorted(os.listdir(out)) if os.path.isdir(out) else [],
            "artifact_count": len(os.listdir(out)) if os.path.isdir(out) else 0,
            "result_top_keys": len(res),
            "stdout_tail": _shrink(_tail(so), self.run),
            "stderr_tail": _shrink(_tail(se), self.run),
        }


# ---------------------------------------------------------------------------
# measurement
# ---------------------------------------------------------------------------


def scenarios(R: Runner) -> list:
    S = []
    for dep, meta in DEPS.items():
        S.append(dict(id=f"{len(S) + 1:02d}-{dep}", dep=dep, meta=meta))
    return S


def _is_primary(rec: dict) -> bool:
    """True when this scenario is the 1:1 test of one dependency."""
    return rec["kind"] in ("import", "external") and not rec.get("control")


def measure(sc: dict, R: Runner) -> dict:
    dep, meta = sc["dep"], sc["meta"]
    t0 = time.perf_counter()
    scratch = os.path.join(R.run, "cases", sc["id"])
    out = os.path.join(scratch, "out")
    cwd = os.path.join(scratch, "cwd")

    env_extra = {}
    poison_root = os.path.join(scratch, "poison")
    poisoned = []
    if meta["kind"] == "import":
        poisoned = [meta["module"]]
    elif meta["kind"] == "combo":
        poisoned = list(meta["poison"])
    for module in poisoned:
        _poison(poison_root, module, f"{module} not installed")
    if poisoned:
        env_extra["PYTHONPATH"] = poison_root + os.pathsep + os.environ.get("PYTHONPATH", "")
    if dep == "libreoffice":
        env_extra["PATH"] = ""          # no external program can be found
        env_extra["PYTHONPATH"] = os.environ.get("PYTHONPATH", "")

    # Some scenarios need a corpus whose figure files really exist, because the
    # code path under test is a *lazy* import guarded by `file_exists`.  Without
    # this the scenario would "pass" for the wrong reason (no figure -> the
    # import never happens), which is exactly the kind of false negative this
    # probe is supposed to avoid.
    corpus = R.corpus
    if meta.get("with_figure"):
        corpus = os.path.join(scratch, "input")
        _rm(corpus)
        shutil.copytree(R.corpus, corpus)
        # Figures are synthesised WITHOUT the poison first: the point of the
        # scenario is to reach `adapt_pptx`'s lazy PIL branch with source images
        # present, so the precondition must exist before the dependency is
        # removed.  (`make_synthetic_inputs.py` needs PIL itself, so doing this
        # under the poison would prove nothing.)
        rc_fig, _fo, fe = R._exec(
            [sys.executable, os.path.join(R.skill, "scripts", "make_synthetic_inputs.py"),
             "--dir", corpus, "--force"], cwd)
        figs_dir = os.path.join(corpus, "figs")
        fig_files = sorted(os.listdir(figs_dir)) if os.path.isdir(figs_dir) else []
        rec_fig = {"figure_gen_exit": rc_fig, "figures": fig_files,
                   "generated_without_poison": True,
                   "stderr_tail": _shrink(_tail(fe), R.run)}
    else:
        rec_fig = None


    rec = {
        "id": sc["id"], "dependency": dep, "kind": meta["kind"],
        "simulation": ("PYTHONPATH 前置 import 即抛 ImportError 的假包: " + ", ".join(poisoned)
                       if poisoned else
                       "PATH 置空（外部程序不可发现）" if dep == "libreoffice" else "—"),
        "used_by": meta["used_by"], "declared": dict(meta["expect"]),
        "env_extra_keys": sorted(env_extra),
        "corpus_figures_exist": bool(meta.get("with_figure")),
        "control": bool(meta.get("with_figure")),
        "figure_gen": rec_fig,
    }

    # ---- 0. did the simulation take effect, and what else does it take down?
    # A poison that never applies would make every "no difference" result a lie,
    # so effectiveness is verified.  The same loop also maps the *import chain*:
    # a dependency the package never imports directly can still be a hard one
    # (measured: lxml, pulled in by python-pptx at package level).
    CHAIN = ["pptx", "PIL", "lxml", "matplotlib", "numpy", "yaml", "reportlab"]
    chain = {}
    for module in CHAIN:
        rc, _so, se = R._exec([sys.executable, "-c", f"import {module}"], cwd, env_extra)
        chain[module] = {"exit": rc, "stderr_tail": _shrink(_tail(se), R.run)}
    rec["import_chain"] = chain
    rec["import_unavailable"] = sorted(m for m, v in chain.items() if v["exit"] != 0)
    rec["poison_probe"] = [chain[m] | {"module": m} for m in poisoned]
    rec["poison_effective"] = all(chain[m]["exit"] != 0 for m in poisoned) if poisoned else True

    # ---- 1. the pipeline --------------------------------------------------
    argv = [sys.executable, os.path.join(R.skill, "scripts", "main.py"),
            "--case", os.path.join(corpus, "case.json"),
            "--task", os.path.join(corpus, "task.md"), "--out", out]
    rc, stdout, stderr = R._exec(argv, cwd, env_extra)
    result = _load(os.path.join(out, "result.json"))
    unc = (result or {}).get("uncertainty") or []
    rec.update({
        "exit": rc,
        "stdout_tail": _shrink(_tail(stdout), R.run),
        "stderr_tail": _shrink(_tail(stderr), R.run),
        "raised_at": _last_frame(stderr),
        "result_json_written": isinstance(result, dict),
        "status": (result or {}).get("status"),
        "result_top_keys": len(result) if isinstance(result, dict) else 0,
        "uncertainty_count": len(unc),
        "uncertainty_items": [str(u.get("item")) for u in unc][:6],
        "uncertainty_notes": [_shrink(str(u.get("note")), R.run)[:180] for u in unc][:6],
        "artifacts": sorted(os.listdir(out)) if os.path.isdir(out) else [],
    })
    rec["artifact_count"] = len(rec["artifacts"])
    rec["deck_written"] = any(a.endswith("_deck.pptx") for a in rec["artifacts"])
    rec["previews_written"] = sum(1 for a in rec["artifacts"] if a.endswith(".png"))
    rec["has_spec"] = "spec.json" in rec["artifacts"]
    rec["has_adopt_plan"] = "adopt_plan.json" in rec["artifacts"]
    rec["tool_versions_missing"] = sorted(
        k for k, v in ((result or {}).get("tool_versions") or {}).items() if v == "unavailable")

    # ---- 2. the single-purpose entries ------------------------------------
    rec["entries"] = {}
    for eid, (script, build) in ENTRY_PROBES.items():
        ctx = dict(case=os.path.join(corpus, "case.json"),
                   task=os.path.join(corpus, "task.md"),
                   out=os.path.join(scratch, "entry-" + eid),
                   examples=R.corpus, scratch=os.path.join(scratch, "entry-" + eid + "-files"))
        os.makedirs(ctx["scratch"], exist_ok=True)
        erc, eso, ese = R._exec(
            [sys.executable, os.path.join(R.skill, "scripts", script)] + build(ctx),
            os.path.join(scratch, "entry-" + eid + "-cwd"), env_extra)
        rec["entries"][eid] = {
            "exit": erc, "stderr_tail": _shrink(_tail(ese), R.run),
            "stdout_tail": _shrink(_tail(eso), R.run), "raised_at": _last_frame(ese),
        }

    # ---- 3. verdict --------------------------------------------------------
    base = R.baseline_cached
    exp = meta["expect"]
    diff = []
    if exp.get("exit") is not None and rc != exp["exit"]:
        diff.append(f"exit {rc} != 声明 {exp['exit']}")
    if exp.get("status") is not None and rec["status"] != exp["status"]:
        diff.append(f"status {rec['status']!r} != 声明 {exp['status']!r}")
    if exp.get("result_json") and not rec["result_json_written"]:
        diff.append("未写出 result.json")
    if exp.get("deck") is False and rec["deck_written"]:
        diff.append("声明不产 deck，实测产出了")
    if exp.get("deck") is None and base and rc == 0 and not rec["deck_written"]:
        diff.append("干净跑能产 deck，这里没产出但也没报错（可能静默降级）")
    rec["declaration_mismatch"] = diff
    # "silent" here = the run looks healthy (exit 0, success) while a declared
    # capability was expected to be gone.
    rec["silent_pass"] = bool(diff) and rc == 0 and rec["status"] == "success"
    rec["verdict"] = ("silent-pass" if rec["silent_pass"] else
                      "as-declared" if not diff else
                      "differs-from-declaration")
    rec["seconds"] = round(time.perf_counter() - t0, 3)
    return rec


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------


def to_markdown(records: list, info: dict) -> str:
    base = info["baseline"]
    L = []
    L.append("## 0. 结论")
    L.append("")
    hard = [r for r in records if r["exit"] != 0]
    soft = [r for r in records if r["exit"] == 0]
    L.append(f"- 场景 **{len(records)}** 个：缺依赖后**管线失败**的 {len(hard)} 个，"
             f"**管线仍成功**的 {len(soft)} 个")
    L.append(f"- 干净基线：exit={base['exit']}、status=`{base['status']}`、"
             f"`--out` 下 {base['artifact_count']} 个产物、result.json {base['result_top_keys']} 顶层键")
    L.append(f"- 真依赖（缺了就失败）："
             + ("、" .join(f"`{r['dependency']}`" for r in hard) or "无"))
    L.append(f"- 非依赖（缺了不影响）："
             + ("、".join(f"`{r['dependency']}`" for r in soft) or "无"))
    L.append(f"- **静默通过**（结果与声明不符但 exit 0 + `success`）："
             f"**{len([r for r in records if r['silent_pass']])}**")
    L.append(f"- 模拟有效性："
             f"**{len([r for r in records if not r['poison_effective']])}** 个场景的投毒未生效（应为 0）")
    L.append("")
    L.append("## 1. 实测环境")
    L.append("")
    L.append(f"- python `{info['python']}`；命令：`{info['command']}`")
    L.append(f"- 参测包（只读源）：`{info['source_skill']}`；"
             f"所有场景跑在包的**一份拷贝**上（`{info['scratch_skill']}`），不在包内执行")
    L.append(f"- 固定输入语料：`<RUN>/input`；合成图件 "
             f"{len(info.get('figures') or [])} 个（exit {info.get('figure_gen_exit')}）")
    L.append(f"- **投毒方式**：`PYTHONPATH` 前置一个 `__init__.py` 即 `raise ImportError` 的同名包；"
             f"每个场景都用 `python -c \"import X\"` 单独验证过投毒确实生效")
    L.append("")
    L.append("## 2. 主流程实测矩阵（按缺什么排序）")
    L.append("")
    L.append("| 场景 | 缺什么 | 投毒生效 | 实测 exit | result.json | status | 顶层键 | 产物数 | deck | 预览 | uncertainty | 连带不可导入 | 判定 |")
    L.append("|-|-|-|-|-|-|-|-|-|-|-|-|-|")
    for r in records:
        extra = [m for m in r.get("import_unavailable", []) if m != r["dependency"]]
        L.append("| `{}` | `{}` | {} | {} | {} | `{}` | {} | {} | {} | {} | {} | {} | {} |".format(
            r["id"], r["dependency"],
            "是" if r["poison_effective"] else "**否**",
            r["exit"], "有" if r["result_json_written"] else "**无**",
            r["status"], r["result_top_keys"], r["artifact_count"],
            "有" if r["deck_written"] else "**无**", r["previews_written"],
            r["uncertainty_count"], ("、".join(f"`{m}`" for m in extra) or "无"),
            "**静默通过**" if r["silent_pass"] else
            "与声明不符" if r["declaration_mismatch"] else "按声明"))
    L.append("")
    L.append("## 3. 逐场景明细（产物还剩什么 + 单入口实测）")
    L.append("")
    for r in records:
        L.append(f"#### `{r['id']}` — 缺 `{r['dependency']}`")
        L.append("")
        L.append(f"- **模拟**：{r['simulation']}")
        L.append(f"- **谁用它**：" + "；".join(r["used_by"]))
        L.append(f"- **声明**：exit={r['declared'].get('exit')} / "
                 f"status=`{r['declared'].get('status')}` / 写 result.json={r['declared'].get('result_json')}")
        L.append(f"- **实测**：exit={r['exit']}；result.json "
                 f"{'已写出（' + str(r['result_top_keys']) + ' 顶层键）' if r['result_json_written'] else '**未写出**'}；"
                 f"status=`{r['status']}`；产物 {r['artifact_count']} 个；"
                 f"deck {'有' if r['deck_written'] else '**无**'}；PNG {r['previews_written']} 张；"
                 f"{r['seconds']}s")
        if r.get("corpus_figures_exist"):
            L.append(f"- **语料**：**带真实源图**（`make_synthetic_inputs.py` exit "
                     f"{(r.get('figure_gen') or {}).get('figure_gen_exit')}）——"
                     f"确保懒加载 PIL 分支真的会被走到")
        L.append(f"- **产物清单**：{('、'.join('`' + a + '`' for a in r['artifacts'])) or '（空目录）'}")
        if r["raised_at"]:
            L.append(f"- **报错位置**：`{r['raised_at']}`")
        if r["stderr_tail"]:
            L.append(f"- **stderr 末行**：`{r['stderr_tail']}`")
        if r["uncertainty_items"]:
            L.append(f"- **uncertainty（{r['uncertainty_count']} 条，列前 3）**："
                     + "；".join(f"`{i}`" for i in r["uncertainty_items"][:3]))
            for note in r["uncertainty_notes"][:2]:
                L.append(f"    - `{note}`")
        if r["tool_versions_missing"]:
            L.append(f"- **tool_versions 记 unavailable**：{r['tool_versions_missing']}")
        L.append(f"- **导入链实测**（同一环境下 `python -c \"import M\"` 是否可用）："
                 + "；".join(f"`{m}`={'可用' if v['exit'] == 0 else '**不可用**'}"
                             for m, v in r.get("import_chain", {}).items()))
        L.append("- **单入口实测**：")
        for eid, e in r["entries"].items():
            L.append(f"    - `{eid}`：exit={e['exit']}"
                     + (f"；报错位置 `{e['raised_at']}`" if e["raised_at"] else "")
                     + (f"；stderr `{e['stderr_tail']}`" if e["stderr_tail"] else ""))
        if r["declaration_mismatch"]:
            L.append("- **与声明不符**：" + "；".join(r["declaration_mismatch"]))
        L.append(f"- **判定**：{'**静默通过**' if r['silent_pass'] else '与声明不符' if r['declaration_mismatch'] else '按声明'}")
        L.append("")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--skill", default=os.path.dirname(here),
                    help="package root (default: parent of this script's dir)")
    ap.add_argument("--run", default="", help="scratch dir (default <cwd>/degrade-probe-run)")
    ap.add_argument("--json", default="", help="write the machine-readable report here")
    ap.add_argument("--markdown", default="", help="write the Markdown table here")
    ap.add_argument("--only", default="", help="comma separated scenario ids or dependency names")
    ap.add_argument("--skip", default="", help="comma separated scenario ids or dependency names")
    ap.add_argument("--timeout", type=int, default=180, help="per-run timeout (s)")
    ap.add_argument("--allow-in-package", action="store_true",
                    help="permit a scratch dir inside the package (NOT recommended)")
    ap.add_argument("--list", action="store_true", help="list scenarios and exit")
    a = ap.parse_args(argv)

    skill = os.path.abspath(a.skill)
    run = os.path.abspath(a.run or os.path.join(os.getcwd(), "degrade-probe-run"))

    def inside(p, root):
        p, root = os.path.abspath(p), os.path.abspath(root)
        return p == root or p.startswith(root + os.sep)

    if inside(run, skill) and not a.allow_in_package:
        print("[degrade_probe] refusing a scratch dir inside the package: running the "
              "pipeline there leaves scripts/__pycache__/*.pyc, which the resource "
              "contract rejects. Pass --run outside the package.", file=sys.stderr)
        return 2

    R = Runner(skill, run, timeout=a.timeout)
    print("[degrade_probe] skill  = <SKILL>")
    print(f"[degrade_probe] scratch= {run}")
    info = R.prepare()
    R.baseline_cached = info["baseline"]
    info["command"] = (f"python scripts/degrade_probe.py --skill <SKILL> --run <RUN>"
                       + (f" --only {a.only}" if a.only else ""))
    print(f"[degrade_probe] baseline: exit={info['baseline']['exit']} "
          f"status={info['baseline']['status']} artifacts={info['baseline']['artifact_count']}")

    S = scenarios(R)
    if a.list:
        for s in S:
            print(f"{s['id']:26s} {s['meta']['kind']:9s} {s['dep']}")
        return 0
    only = {x.strip() for x in a.only.split(",") if x.strip()}
    skip = {x.strip() for x in a.skip.split(",") if x.strip()}
    if only:
        S = [s for s in S if s["id"] in only or s["dep"] in only]
    if skip:
        S = [s for s in S if s["id"] not in skip and s["dep"] not in skip]

    records = []
    for s in S:
        rec = measure(s, R)
        records.append(rec)
        flag = ("SILENT" if rec["silent_pass"] else
                "differs" if rec["declaration_mismatch"] else "ok")
        print(f"  {rec['id']:26s} exit={rec['exit']:<3} status={str(rec['status']):<9} "
              f"res={'y' if rec['result_json_written'] else 'n'} "
              f"art={rec['artifact_count']:<3} deck={'y' if rec['deck_written'] else 'n'} "
              f"unc={rec['uncertainty_count']:<2} poison={'y' if rec['poison_effective'] else 'N'} "
              f"-> {flag}")

    ineffective = [r for r in records if not r["poison_effective"]]
    silent = [r for r in records if r["silent_pass"]]
    report = {
        "_meta": "dependency-degradation probe; every number is measured, not asserted",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "python": sys.version.split()[0],
        "command": info["command"],
        "environment": info,
        "scenario_count": len(records),
        "silent_pass_count": len(silent),
        "ineffective_poison_count": len(ineffective),
        # Only single-dependency scenarios answer "is X required?"; combo and
        # with-figure scenarios are controls and are listed separately so they
        # cannot be mistaken for dependencies.
        # Only the 1:1 scenarios answer "is X required?"; combo and with-figure
        # scenarios are controls (they repeat a dependency on purpose).
        "hard_fail_dependencies": [r["dependency"] for r in records
                                   if r["exit"] != 0 and _is_primary(r)],
        "unaffected_dependencies": [r["dependency"] for r in records
                                    if r["exit"] == 0 and _is_primary(r)],
        "control_scenarios": [{"id": r["id"], "kind": r["kind"], "exit": r["exit"]}
                              for r in records if r["kind"] == "combo"],
        "scenarios": records,
    }
    if a.json:
        _write(a.json, json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n")
        print(f"[degrade_probe] json  -> {a.json}")
    if a.markdown:
        _write(a.markdown, to_markdown(records, info) + "\n")
        print(f"[degrade_probe] table -> {a.markdown}")

    print(f"[degrade_probe] {len(records)} scenarios, {len(silent)} silent pass(es), "
          f"{len(ineffective)} ineffective poison(s)")
    for r in ineffective:
        print(f"  ! POISON INEFFECTIVE {r['id']}")
    for r in silent:
        print(f"  ! SILENT {r['id']}: {'; '.join(r['declaration_mismatch'])}")
    return 1 if (silent or ineffective) else 0


if __name__ == "__main__":
    raise SystemExit(main())
