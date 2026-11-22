#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fault_inject.py — deliberately break the four fault families and watch what
the pipeline actually does.

Why this script exists
----------------------
`references/failure-modes.md` states, for every degradation path, what *should*
happen.  A statement in a document is not evidence.  This script turns each of
those statements into an experiment: it injects one concrete fault, runs the
real `scripts/main.py` end to end as a child process, and records what actually
came back — exit code, `result.json` status, the `uncertainty` entries, whether
any artifact was still produced, and whether the fault passed *silently*.

The four fault families (the ones a reviewer actually hits)
----------------------------------------------------------
  input        case.json / task.md / material.md / figure files
  template     missing, corrupt, or empty template & starting deck
  dependency   python-pptx or Pillow not importable; --out not writable
  contract     result.json / its artifact list / the CP3 gate G1-G8

Design rules that matter for honesty
------------------------------------
1. **Never run inside the package.**  Executing `scripts/*.py` with the package
   as cwd leaves `scripts/__pycache__/*.pyc` behind, and `.pyc` is a resource
   type the submission contract rejects.  This script therefore refuses to use
   the package directory as a working directory unless `--allow-in-package` is
   passed explicitly.
2. **One scenario = one fresh subprocess.**  No in-process reuse, so an earlier
   fault cannot contaminate a later measurement.
3. **Silent failure is a verdict, not a footnote.**  Every scenario declares
   `expect.status`; if a scenario that must fail comes back `success` (or exit
   0), the report marks it `silent_failure: true` instead of quietly counting
   it as a pass.
4. **Recorded numbers are measured, never assumed.**  The JSON report and the
   Markdown table are both generated from the same measurement pass.

Usage
-----
    python scripts/fault_inject.py --skill <package root> \
        [--run <work dir>] [--json <report.json>] [--markdown <table.md>] \
        [--skip <id,id>] [--only <id,id>] [--timeout 180]

Exit code: 0 when every scenario behaved as declared (no silent failures),
1 when at least one scenario failed silently, 2 on usage/environment errors.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time

ALLOWED_EXT = {".md", ".py", ".json", ".txt", ".csv", ".yaml", ".yml"}

# ----------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------


def _rm(path: str) -> None:
    """Remove a directory tree, tolerating read-only files (Windows)."""
    if not os.path.exists(path):
        return
    try:
        shutil.rmtree(path)
    except Exception:
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                try:
                    os.chmod(os.path.join(root, name), 0o666)
                except Exception:
                    pass
            for name in dirs:
                try:
                    os.chmod(os.path.join(root, name), 0o777)
                except Exception:
                    pass
        shutil.rmtree(path, ignore_errors=True)


def _write(path: str, text: str, mode: str = "w") -> str:
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, mode, encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return path


def _poison(path: str, module: str, message: str) -> str:
    """Create a fake importable module that raises on import.

    Used to simulate 'dependency not installed' without uninstalling anything:
    the directory goes on PYTHONPATH and shadows the real package.
    """
    os.makedirs(path, exist_ok=True)
    if "." in module:
        head, tail = module.split(".", 1)
        os.makedirs(os.path.join(path, head), exist_ok=True)
        _write(os.path.join(path, head, "__init__.py"), "")
        _write(os.path.join(path, head, tail, "__init__.py"),
               f"raise ImportError('simulated: {message}')\n")
    else:
        _write(os.path.join(path, module, "__init__.py"),
               f"raise ImportError('simulated: {message}')\n")
    return path


def _load_json(path: str):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def _file_list(root: str) -> list:
    out = []
    for dirpath, dirnames, names in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for n in names:
            out.append(os.path.relpath(os.path.join(dirpath, n), root).replace("\\", "/"))
    return sorted(out)


def _tail(text: str, n: int = 240) -> str:
    text = (text or "").strip().replace("\r", "")
    if not text:
        return ""
    line = text.splitlines()[-1]
    return line[:n]


def _json_block(text: str):
    """Parse the first complete JSON object out of a child process's stdout.

    check_contract.py pretty-prints its verdict, so "take the last line" would
    only ever yield the closing brace.  Scanning for the outermost balanced
    object is robust to leading/trailing log lines.
    """
    text = text or ""
    start = text.find("{")
    while start != -1:
        depth = 0
        in_str = False
        esc = False
        for i in range(start, len(text)):
            ch = text[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except Exception:
                        break
        start = text.find("{", start + 1)
    return None


# ----------------------------------------------------------------------------
# runner
# ----------------------------------------------------------------------------


class Runner:
    def __init__(self, skill_dir: str, run_dir: str, timeout: int = 180):
        self.skill = os.path.abspath(skill_dir)
        self.run = os.path.abspath(run_dir)
        self.timeout = timeout
        self.main = os.path.join(self.skill, "scripts", "main.py")
        self.examples_src = os.path.join(self.skill, "examples")
        self.base = os.path.join(self.run, "base")   # pristine input copy

    # -- setup ---------------------------------------------------------------
    def prepare(self) -> dict:
        info = {"skill": self.skill, "run": self.run}
        if not os.path.isfile(self.main):
            raise SystemExit(f"[fault_inject] main.py not found under {self.skill}")
        _rm(self.base)
        os.makedirs(self.run, exist_ok=True)
        shutil.copytree(self.examples_src, self.base)
        # figures are not shipped (resource contract: text only) -> synthesise
        rc, out, err = self._exec(
            [sys.executable, os.path.join(self.skill, "scripts", "make_synthetic_inputs.py"),
             "--dir", self.base], os.path.join(self.run, "cwd"))
        figs = os.path.join(self.base, "figs")
        info["figures_synthesised"] = sorted(os.listdir(figs)) if os.path.isdir(figs) else []
        info["figure_gen_exit"] = rc
        if rc != 0:
            info["figure_gen_stderr"] = _tail(err)
        return info

    # -- one child process ---------------------------------------------------
    def _exec(self, argv: list, cwd: str, env_extra: dict | None = None):
        os.makedirs(cwd, exist_ok=True)
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        if env_extra:
            for k, v in env_extra.items():
                env[k] = v
        try:
            p = subprocess.run(argv, cwd=cwd, env=env, capture_output=True,
                               timeout=self.timeout)
            return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")
        except subprocess.TimeoutExpired:
            return 124, "", f"timeout after {self.timeout}s"

    def run_case(self, case: str, out: str, cwd: str,
                 env_extra: dict | None = None, extra_argv: list | None = None):
        task = os.path.join(self.base, "task.md")
        argv = [sys.executable, self.main, "--case", case, "--task", task, "--out", out]
        if extra_argv:
            argv += extra_argv
        return self._exec(argv, cwd, env_extra)


# ----------------------------------------------------------------------------
# the scenario catalogue
# ----------------------------------------------------------------------------


def scenarios(R: Runner) -> list:
    """Each entry: id, family, what is injected, expectation, and the launcher.

    `run()` returns the invocation plan for one child process:
        case, out, cwd, [env_extra], [extra_argv]
    A scenario may additionally declare:
        tamper     — mutate the clean output before the gate re-check
        post_gate  — run scripts/check_contract.py against that output
        must_not_succeed / host_sensitive / known_gap
    """
    ex = R.base
    case_ok = os.path.join(ex, "case.json")
    task_ok = os.path.join(ex, "task.md")
    material_ok = os.path.join(ex, "material.md")

    def _case_copy(scenario_id: str) -> str:
        """Copy the example directory, then return the writable case.json path."""
        d = os.path.join(R.run, scenario_id, "input")
        _rm(d)
        shutil.copytree(ex, d)
        return os.path.join(d, "case.json")

    def _mutate(case_path: str, **kw) -> str:
        obj = _load_json(case_path) or {}
        obj.update(kw)
        _write(case_path, json.dumps(obj, ensure_ascii=False, indent=2))
        return case_path

    S = []

    # ---- 1. healthy control ------------------------------------------------
    def s_control():
        c = _case_copy("c00-control")
        return dict(case=c, out=os.path.join(R.run, "c00-control", "out"),
                    cwd=os.path.join(R.run, "c00-control", "cwd"))

    S.append(dict(
        id="c00-control", family="control",
        inject="无注入：原样跑通示例案例（基线对照，用于判断其余场景的差异是不是注入造成的）",
        expect=dict(exit=0, status="success",
                    note="status=success；全部产物齐全；G1–G8 全过"),
        must_not_succeed=False, run=s_control,
    ))

    # ---- input family ------------------------------------------------------
    def s_input_missing():
        d = os.path.join(R.run, "i01-missing-case", "input")
        return dict(case=os.path.join(d, "absent_case.json"),
                    out=os.path.join(R.run, "i01-missing-case", "out"),
                    cwd=os.path.join(R.run, "i01-missing-case", "cwd"))

    S.append(dict(
        id="i01-missing-case", family="input",
        inject="--case 指向不存在的 case.json",
        expect=dict(exit=1, status="failed",
                    note="立即失败；写 failed result.json；case_id 取文件名词干；不产 pptx"),
        must_not_succeed=True, run=s_input_missing,
    ))

    def s_input_garbage():
        d = os.path.join(R.run, "i02-garbage-case", "input")
        _rm(d)
        os.makedirs(d, exist_ok=True)
        _write(os.path.join(d, "case_broken.json"), '{"case_id": "broken", "title": ')
        return dict(case=os.path.join(d, "case_broken.json"),
                    out=os.path.join(R.run, "i02-garbage-case", "out"),
                    cwd=os.path.join(R.run, "i02-garbage-case", "cwd"))

    S.append(dict(
        id="i02-garbage-case", family="input",
        inject="case.json 内容被截断（非法 JSON）",
        expect=dict(exit=1, status="failed",
                    note="JSONDecodeError 被 main() 捕获 → failed result + exit 1，不抛裸栈到 stdout"),
        must_not_succeed=True, run=s_input_garbage,
    ))

    def s_input_material_gone():
        c = _case_copy("i03-material-missing")
        # keep case.json structured fields, point source_material at a ghost file
        _mutate(c, source_material=["material_v2_final.md"])
        return dict(case=c, out=os.path.join(R.run, "i03-material-missing", "out"),
                    cwd=os.path.join(R.run, "i03-material-missing", "cwd"))

    S.append(dict(
        id="i03-material-missing", family="input",
        inject="case.json 的 source_material 指向不存在的文件（结构化字段仍在）",
        expect=dict(exit=0, status="success",
                    note="按 D2 降级继续：sources[].exists=false + uncertainty 记一条，页面由结构化字段支撑"),
        must_not_succeed=False, run=s_input_material_gone,
    ))

    def s_input_material_binary():
        c = _case_copy("i04-material-binary")
        p = os.path.join(os.path.dirname(c), "material_bin.md")
        with open(p, "wb") as fh:
            fh.write(b"\xff\xfe\x00\x01PK\x03\x04 not utf-8 \x81\x82")
        _mutate(c, source_material=["material_bin.md"])
        return dict(case=c, out=os.path.join(R.run, "i04-material-binary", "out"),
                    cwd=os.path.join(R.run, "i04-material-binary", "cwd"))

    S.append(dict(
        id="i04-material-binary", family="input",
        inject="材料文件存在但不是 UTF-8（二进制字节）",
        expect=dict(exit=0, status="success",
                    note="按 F03 降级：只登记来源 + note，不假装读过内容；状态不冒充失败也不编造"),
        must_not_succeed=False, run=s_input_material_binary,
    ))

    def s_input_task_missing():
        c = _case_copy("i05-task-missing")
        return dict(case=c, out=os.path.join(R.run, "i05-task-missing", "out"),
                    cwd=os.path.join(R.run, "i05-task-missing", "cwd"),
                    extra_argv=["--task", os.path.join(R.run, "i05-task-missing", "no_task.md")])

    S.append(dict(
        id="i05-task-missing", family="input",
        inject="--task 指向不存在的 task.md",
        expect=dict(exit=0, status="success",
                    note="main.py 只传路径、extract 只在存在时读：task_summary 为空但流程继续（不崩）"),
        must_not_succeed=False, run=s_input_task_missing,
    ))

    def s_input_figs_missing():
        c = _case_copy("i06-figures-missing")
        for n in ("fig1.png", "fig2.png"):     # PICTURE_TYPE_BMP / PNG decoys
            p = os.path.join(os.path.dirname(c), "figs", n)
            if os.path.exists(p):
                os.remove(p)
        return dict(case=c, out=os.path.join(R.run, "i06-figures-missing", "out"),
                    cwd=os.path.join(R.run, "i06-figures-missing", "cwd"))

    S.append(dict(
        id="i06-figures-missing", family="input",
        inject="case.figures 指定的 fig1.png / fig2.png 被删除",
        expect=dict(exit=0, status="success",
                    note="按 D5/F15 降级：保留图号+标题+来源的占位框，"
                         "uncertainty 逐图记一条，figures_embedded 归 0 — "
                         "但 **status 仍是 success**（审计项只记 ok，不转 warn）。"
                         "这条降级目前只落在 uncertainty 上，是本包已承认的粗糙点，"
                         "见 references/FAULT-MATRIX.md §4"),
        must_not_succeed=False, run=s_input_figs_missing,
        known_gap="missing-figure degradation is recorded in uncertainty "
                  "but never raises the audit level, so status stays success",
    ))

    # ---- template family ---------------------------------------------------
    def s_tpl_missing():
        c = _case_copy("t01-template-missing")
        return dict(case=c, out=os.path.join(R.run, "t01-template-missing", "out"),
                    cwd=os.path.join(R.run, "t01-template-missing", "cwd"),
                    extra_argv=["--template", os.path.join(R.run, "t01-template-missing", "ghost.pptx")])

    S.append(dict(
        id="t01-template-missing", family="template",
        inject="--template 指向不存在的文件（案例本身也没给模板）",
        expect=dict(exit=0, status="success",
                    note="按 D6 走回退链到运行时内置模板：opened_from=builtin，不中止构建"),
        must_not_succeed=False, run=s_tpl_missing,
    ))

    def s_tpl_broken():
        c = _case_copy("t02-template-corrupt")
        d = os.path.dirname(c)
        p = os.path.join(d, "broken_template.pptx")
        _write(p, "NOT A ZIP FILE — deliberately corrupt template\n")
        return dict(case=c, out=os.path.join(R.run, "t02-template-corrupt", "out"),
                    cwd=os.path.join(R.run, "t02-template-corrupt", "cwd"),
                    extra_argv=["--template", p])

    S.append(dict(
        id="t02-template-corrupt", family="template",
        inject="模板文件存在但不是 zip（损坏的 pptx）",
        expect=dict(exit=0, status="success",
                    note="按 D6/F07 记录 template_errors 一条后回退到内置模板并继续"),
        must_not_succeed=False, run=s_tpl_broken,
    ))

    def s_tpl_startdeck_corrupt():
        c = _case_copy("t03-startdeck-corrupt")
        d = os.path.dirname(c)
        p = os.path.join(d, "broken_startdeck.pptx")
        _write(p, "ALSO NOT A ZIP\n")
        return dict(case=c, out=os.path.join(R.run, "t03-startdeck-corrupt", "out"),
                    cwd=os.path.join(R.run, "t03-startdeck-corrupt", "cwd"),
                    extra_argv=["--starting-deck", p])

    S.append(dict(
        id="t03-startdeck-corrupt", family="template",
        inject="起始 deck 损坏（编辑模式入口不可用）",
        expect=dict(exit=0, status="success",
                    note="同样走回退链；change_records 里不出现 edit_starting_deck（因为没编辑成）"),
        must_not_succeed=False, run=s_tpl_startdeck_corrupt,
    ))

    # ---- dependency family -------------------------------------------------
    def s_dep_pptx():
        c = _case_copy("d01-no-pptx")
        poison = _poison(os.path.join(R.run, "d01-no-pptx", "poison-pptx"), "pptx",
                         "python-pptx not installed")
        return dict(case=c, out=os.path.join(R.run, "d01-no-pptx", "out"),
                    cwd=os.path.join(R.run, "d01-no-pptx", "cwd"),
                    env_extra={"PYTHONPATH": poison + os.pathsep + os.environ.get("PYTHONPATH", "")})

    S.append(dict(
        id="d01-no-pptx", family="dependency",
        inject="在 PYTHONPATH 前置一个 import 即抛 ImportError 的假 pptx 包",
        expect=dict(exit=1, status="failed",
                    note="ImportError 被捕获 → failed result.json，uncertainty 含原始异常文本；绝不报 success"),
        must_not_succeed=True, run=s_dep_pptx,
    ))

    def s_dep_pil():
        c = _case_copy("d02-no-pil")
        poison = _poison(os.path.join(R.run, "d02-no-pil", "poison-pil"), "PIL",
                         "Pillow not installed")
        return dict(case=c, out=os.path.join(R.run, "d02-no-pil", "out"),
                    cwd=os.path.join(R.run, "d02-no-pil", "cwd"),
                    env_extra={"PYTHONPATH": poison + os.pathsep + os.environ.get("PYTHONPATH", "")})

    S.append(dict(
        id="d02-no-pil", family="dependency",
        inject="同法伪造 PIL（Pillow）导入失败",
        expect=dict(exit=1, status="failed",
                    note="preview 阶段 ImportError → failed result；不产空 PNG 冒充成功"),
        must_not_succeed=True, run=s_dep_pil,
    ))

    def s_dep_out_unwritable():
        c = _case_copy("d03-out-unwritable")
        blocker = os.path.join(R.run, "d03-out-unwritable", "out_is_a_file")
        _write(blocker, "this path is a regular file, so it cannot be used as --out\n")
        return dict(case=c, out=blocker, cwd=os.path.join(R.run, "d03-out-unwritable", "cwd"))

    S.append(dict(
        id="d03-out-unwritable", family="dependency",
        inject="--out 指向一个普通文件（目录创建必然失败）",
        expect=dict(exit=2, status=None,
                    note="按 F23 立即报错 exit 2；**不写半截 JSON**（上限档：明确拒绝而不是静默降级）"),
        must_not_succeed=True, run=s_dep_out_unwritable,
    ))

    def s_dep_out_ro():
        c = _case_copy("d04-out-readonly")
        ro = os.path.join(R.run, "d04-out-readonly", "out_ro")
        os.makedirs(ro, exist_ok=True)
        os.chmod(ro, 0o444)
        return dict(case=c, out=ro, cwd=os.path.join(R.run, "d04-out-readonly", "cwd"))

    S.append(dict(
        id="d04-out-readonly", family="dependency",
        inject="--out 是一个只读目录（chmod 0444）",
        expect=dict(exit=1, status="failed",
                    note="POSIX 下不可写 → 应报错；**Windows 上 chmod 不能阻止写入**，若真写成功必须写明宿主差异"),
        must_not_succeed=False, run=s_dep_out_ro, host_sensitive=True,
    ))

    # ---- contract family ---------------------------------------------------
    def s_ctr_case_id():
        c = _case_copy("k01-caseid-mismatch")
        _mutate(c, case_id="renamed-by-hand-999")
        return dict(case=c, out=os.path.join(R.run, "k01-caseid-mismatch", "out"),
                    cwd=os.path.join(R.run, "k01-caseid-mismatch", "cwd"))

    S.append(dict(
        id="k01-caseid-mismatch", family="contract",
        inject="把 case.json 的 case_id 改成别的值（模拟交付人手工改名）",
        expect=dict(exit=0, status="success",
                    note="G1 要求 result.case_id == case.json.case_id：两边一起改，门应仍全过（改对了的情形）"),
        must_not_succeed=False, run=s_ctr_case_id,
    ))

    def s_ctr_tamper_result():
        """Run clean, then tamper the *result* and re-run the independent gates."""
        d = os.path.join(R.run, "k02-tamper-contract")
        return dict(case=_case_copy("k02-tamper-contract"),
                    out=os.path.join(d, "out"), cwd=os.path.join(d, "cwd"))

    S.append(dict(
        id="k02-tamper-contract", family="contract",
        inject="跑完后删掉 result.json 顶层的一个 output_contract 键（伪造『全部字段都已回显』），"
               "再跑 check_contract.py",
        expect=dict(exit=1, status="success",
                    note="独立校验器应判不合格：G3 报 missing=[...]；这是『自述不算证据』的实测证据"),
        must_not_succeed=True, run=s_ctr_tamper_result, tamper="drop_contract_key", post_gate=True,
    ))

    def s_ctr_artifact_missing():
        d = os.path.join(R.run, "k03-artifact-missing")
        return dict(case=_case_copy("k03-artifact-missing"),
                    out=os.path.join(d, "out"), cwd=os.path.join(d, "cwd"))

    S.append(dict(
        id="k03-artifact-missing", family="contract",
        inject="跑完后删掉封面预览 PNG，再跑 check_contract.py（G7 逐文件扫产物）",
        expect=dict(exit=1, status="success",
                    note="G7 应立刻 fail 并列出缺失文件名——证明产物清单不是自述"),
        must_not_succeed=True, run=s_ctr_artifact_missing, tamper="delete_preview", post_gate=True,
    ))
    def s_ctr_gate_offline():
        d = os.path.join(R.run, "k04-gate-offline")
        case = _case_copy("k04-gate-offline")
        return dict(case=case, out=os.path.join(d, "out"), cwd=os.path.join(d, "cwd"),
                    extra_argv=["--work", os.path.join(d, "no_such_workdir")])

    S.append(dict(
        id="k04-work-nonexistent", family="contract",
        inject="--work 指向不存在的材料基目录（路径解析必须回落到 case 目录）",
        expect=dict(exit=0, status="success",
                    note="材料仍能被 case.json 所在目录解析到：sources[].exists=true，不因 --work 缺失而失联"),
        must_not_succeed=False, run=s_ctr_gate_offline,
    ))

    return S


# ----------------------------------------------------------------------------
# measurement
# ----------------------------------------------------------------------------


def measure(sc: dict, R: Runner) -> dict:
    t0 = time.perf_counter()
    kind = sc["run"]()
    out = kind["out"]
    # NOTE: the output directory is NOT wiped here.  Every scenario gets its own
    # directory name, and wiping it would destroy the clean run that the
    # tamper-then-gate scenarios (k02/k03) have to measure.  Reproducibility
    # across repeats is handled by deleting the whole --run tree beforehand.

    rec = {
        "id": sc["id"], "family": sc["family"], "inject": sc["inject"],
        "expected_exit": sc["expect"]["exit"],
        "expected_status": sc["expect"]["status"],
        "expected_note": sc["expect"]["note"],
        "must_not_succeed": bool(sc.get("must_not_succeed")),
        "host_sensitive": bool(sc.get("host_sensitive")),
    }

    # ---- pass 1: the pipeline itself --------------------------------------
    rc, stdout, stderr = R.run_case(kind["case"], out, kind["cwd"],
                                    kind.get("env_extra"), kind.get("extra_argv"))
    rec["exit"] = rc
    rec["stdout_tail"] = _tail(stdout)
    rec["stderr_tail"] = _tail(stderr)

    result = _load_json(os.path.join(out, "result.json")) if os.path.isdir(out) else None
    rec["result_json_written"] = result is not None
    rec["status"] = (result or {}).get("status")
    unc = (result or {}).get("uncertainty")
    rec["uncertainty_count"] = len(unc) if isinstance(unc, list) else None
    rec["uncertainty_items"] = [str(u.get("item")) for u in unc] if isinstance(unc, list) else []
    rec["uncertainty_notes"] = [str(u.get("note"))[:160] for u in unc] if isinstance(unc, list) else []
    rec["result_top_keys"] = sorted(result.keys()) if isinstance(result, dict) else []
    rec["artifact_files"] = _file_list(out) if os.path.isdir(out) else []

    ta = (result or {}).get("template_audit") or {}
    rec["opened_from"] = ta.get("opened_from")
    rec["template_errors"] = len(ta.get("template_errors") or [])
    rec["layout_fallback_used"] = ta.get("layout_fallback_used")
    mr = (result or {}).get("main_result") or {}
    rec["figures_embedded"] = mr.get("figures_embedded")
    rec["figures_total"] = mr.get("figures_total")
    rec["change_records"] = [c.get("action") for c in ((result or {}).get("change_records") or [])]

    # ---- pass 2: contract tamper (optional) -------------------------------
    if sc.get("tamper"):
        rp = os.path.join(out, "result.json")
        obj = _load_json(rp) or {}
        if sc["tamper"] == "drop_contract_key":
            case_obj = _load_json(kind["case"]) or {}
            keys = list((case_obj.get("output_contract") or {}).keys())
            victim = keys[0] if keys else "case_id"
            if victim == "case_id":
                obj.pop("case_id", None)
            else:
                obj.pop(victim, None)
            _write(rp, json.dumps(obj, ensure_ascii=False, indent=2))
            rec["tamper"] = f"removed top-level contract key {victim!r} from result.json"
        elif sc["tamper"] == "delete_preview":
            victim = None
            for n in os.listdir(out):
                if n.endswith("_cover_preview.png"):
                    victim = os.path.join(out, n)
            if victim:
                os.remove(victim)
                rec["tamper"] = f"deleted {os.path.basename(victim)}"
            else:
                rec["tamper"] = "no cover preview found to delete"

    # ---- pass 3: the independent gate -------------------------------------
    if sc.get("post_gate") or sc.get("id") in ("c00-control",):
        rp = os.path.join(out, "result.json")
        if os.path.isfile(rp):
            argv = [sys.executable, os.path.join(R.skill, "scripts", "check_contract.py"),
                    "--result", rp, "--out-dir", out, "--case", kind["case"]]
            grc, gout, gerr = R._exec(argv, kind["cwd"])
            rec["gate_exit"] = grc
            rec["gate_stdout_tail"] = _tail(gout, 400)
            rec["gate_stderr_tail"] = _tail(gerr)
            payload = _json_block(gout)
            rec["gate_valid"] = payload.get("valid") if isinstance(payload, dict) else None
            if isinstance(payload, dict) and isinstance(payload.get("gates"), list):
                rec["gate_failed"] = [g.get("gate") for g in payload["gates"] if not g.get("ok")]

    # ---- verdicts ----------------------------------------------------------
    # Two kinds of scenario, judged by two different yardsticks:
    #
    #   * plain scenarios  — main.py's exit code and status must match the
    #     declaration.  A must-fail scenario must NOT come back success.
    #   * post_gate ones   — the pipeline is expected to complete honestly
    #     (k02/k03 tamper *after* a clean run), so main.py's exit code is
    #     irrelevant.  What matters is that the independent gate refuses the
    #     tampered output: gate_valid must be False.  Judging these by
    #     main.py's exit code would mislabel a working verifier as a silent
    #     failure — the exact class of measurement bug this file exists to
    #     avoid.
    silent = []
    gate_ok = rec.get("gate_valid") is False
    if sc["expect"]["exit"] is not None and rc != sc["expect"]["exit"]:
        if not sc.get("host_sensitive") and not gate_ok:
            silent.append(f"exit {rc} != declared {sc['expect']['exit']}")
    if sc["expect"]["status"] is not None and rec["status"] != sc["expect"]["status"]:
        if not sc.get("host_sensitive"):
            if sc.get("must_not_succeed"):
                if rec["status"] in ("success",) or rc == 0:
                    if not gate_ok:
                        silent.append(f"must-fail scenario came back status={rec['status']!r} "
                                      f"exit={rc} — SILENT")
            else:
                silent.append(f"status {rec['status']!r} != declared {sc['expect']['status']!r}")
    if sc.get("must_not_succeed") and rc == 0 and rec["status"] == "success" and not gate_ok:
        silent.append("must-fail scenario succeeded — SILENT")
    if sc.get("post_gate") and rec.get("gate_valid") is True:
        silent.append("tampered result still passed the independent gate — SILENT")
    if sc.get("post_gate") and rec.get("gate_exit") == 0:
        silent.append("independent gate exited 0 on a tampered result — SILENT")
    if sc.get("post_gate") and rec.get("gate_exit") is None:
        silent.append("independent gate did not run — SILENT")

    rec["silent_failure"] = bool(silent)
    rec["verdict"] = ("SILENT-FAIL" if silent else
                      "HOST-DIFF" if sc.get("host_sensitive") and
                      (rc != sc["expect"]["exit"] or rec["status"] != sc["expect"]["status"]) else
                      "as-declared")
    rec["mismatch"] = silent
    rec["seconds"] = round(time.perf_counter() - t0, 2)
    return rec


# ----------------------------------------------------------------------------
# report
# ----------------------------------------------------------------------------


MD_COLS = ["id", "family", "exit", "gate", "status", "uncertainty", "silent", "verdict"]


def to_markdown(records: list, info: dict) -> str:
    lines = []
    lines.append("| 场景 ID | 家族 | 注入的故障 | 期望（声明） | 实测 exit | 独立门 exit | 实测 status | uncertainty 条数 | 静默失败 | 判定 |")
    lines.append("|-|-|-|-|-|-|-|-|-|-|")
    for r in records:
        exp = f"exit {r['expected_exit']}" + (f" / status `{r['expected_status']}`"
                                              if r["expected_status"] else " / 无 result.json")
        act_st = f"`{r['status']}`" if r["status"] is not None else "（无 result.json）"
        unc = "—" if r["uncertainty_count"] is None else str(r["uncertainty_count"])
        sil = "**是**" if r["silent_failure"] else "否"
        gate = "—" if r.get("gate_exit") is None else str(r["gate_exit"])
        lines.append("| `{}` | {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
            r["id"], r["family"], r["inject"], exp, r["exit"], gate, act_st, unc, sil, r["verdict"]))
    lines.append("")
    lines.append(f"环境：skill=`{info['skill']}`；工作区=`{info['run']}`；"
                 f"合成图件={len(info.get('figures_synthesised') or [])} 个。")
    lines.append("")
    lines.append("> `独立门 exit` = `check_contract.py` 对该场景产物目录的判定（G1–G8）；"
                 "只有控制组与控制类场景会跑它，其余显示「—」。")
    lines.append("")
    lines.append("### 逐场景实测明细")
    lines.append("")
    for r in records:
        lines.append(f"#### `{r['id']}` ({r['family']})")
        lines.append("")
        lines.append(f"- **注入**：{r['inject']}")
        lines.append(f"- **期望**：{r['expected_note']}")
        lines.append(f"- **实测**：exit={r['exit']}；"
                     f"result.json {'已写出' if r['result_json_written'] else '未写出'}；"
                     f"status={r['status']!r}；uncertainty={r['uncertainty_count']} 条；"
                     f"产物 {len(r['artifact_files'])} 个；耗时 {r['seconds']}s")
        if r.get("opened_from") or r.get("template_errors") is not None:
            lines.append(f"- **模板链**：`opened_from={r.get('opened_from')}`；"
                         f"`template_errors={r.get('template_errors')}`；"
                         f"`layout_fallback_used={r.get('layout_fallback_used')}`")
        if r.get("figures_total") is not None:
            lines.append(f"- **图表**：embedded={r.get('figures_embedded')}/{r.get('figures_total')}；"
                         f"change_records={r.get('change_records')}")
        if r.get("tamper"):
            lines.append(f"- **篡改**：{r['tamper']}")
        if r.get("gate_exit") is not None:
            lines.append(f"- **独立门 `check_contract.py`**：exit={r['gate_exit']}；"
                         f"valid={r.get('gate_valid')}；失败门={r.get('gate_failed')}")
        if r["uncertainty_notes"]:
            lines.append("- **uncertainty 前 3 条**：" +
                         "；".join(f"`{n}`" for n in r["uncertainty_notes"][:3]))
        if r["stderr_tail"]:
            lines.append(f"- **stderr 末行**：`{r['stderr_tail']}`")
        lines.append(f"- **判定**：{'**静默失败**' if r['silent_failure'] else r['verdict']}"
                     + ("；" + "；".join(r["mismatch"]) if r["mismatch"] else ""))
        lines.append("")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--skill", default=os.path.dirname(here),
                    help="package root (default: parent of this script's dir)")
    ap.add_argument("--run", default="",
                    help="scratch directory (default: <cwd>/fault-inject-run)")
    ap.add_argument("--json", default="", help="write the full report here")
    ap.add_argument("--markdown", default="", help="write the Markdown table here")
    ap.add_argument("--only", default="", help="comma separated scenario ids")
    ap.add_argument("--skip", default="", help="comma separated scenario ids to skip")
    ap.add_argument("--timeout", type=int, default=180, help="per-run timeout (s)")
    ap.add_argument("--allow-in-package", action="store_true",
                    help="permit a working directory inside the package (NOT recommended: "
                         "creates scripts/__pycache__/.pyc, which the resource contract rejects)")
    ap.add_argument("--list", action="store_true", help="list scenario ids and exit")
    a = ap.parse_args(argv)

    skill = os.path.abspath(a.skill)
    run = os.path.abspath(a.run or os.path.join(os.getcwd(), "fault-inject-run"))

    def inside(p: str, root: str) -> bool:
        p, root = os.path.abspath(p), os.path.abspath(root)
        return p == root or p.startswith(root + os.sep)

    if inside(run, skill) and not a.allow_in_package:
        print(f"[fault_inject] refusing to run with a working dir inside the package:\n"
              f"  run={run}\n  skill={skill}\n"
              f"Running the scripts there leaves scripts/__pycache__/*.pyc behind, and .pyc "
              f"is a resource type the submission contract rejects.  Pass a --run directory "
              f"outside the package (that is what this script does by default), or "
              f"--allow-in-package if you really mean it.", file=sys.stderr)
        return 2

    R = Runner(skill, run, timeout=a.timeout)
    S = scenarios(R)
    if a.list:
        for s in S:
            print(f"{s['id']:24s} {s['family']:11s} {s['inject']}")
        return 0
    only = {x.strip() for x in a.only.split(",") if x.strip()}
    skip = {x.strip() for x in a.skip.split(",") if x.strip()}
    if only:
        S = [s for s in S if s["id"] in only]
    if skip:
        S = [s for s in S if s["id"] not in skip]

    print(f"[fault_inject] skill={skill}")
    print(f"[fault_inject] run  ={run}")
    info = R.prepare()
    print(f"[fault_inject] synthesised figures: {info.get('figures_synthesised')} "
          f"(exit {info.get('figure_gen_exit')})")

    records = []
    for s in S:
        rec = measure(s, R)
        records.append(rec)
        flag = "SILENT-FAIL" if rec["silent_failure"] else rec["verdict"]
        print(f"  {rec['id']:26s} exit={rec['exit']:<3} status={str(rec['status']):<8} "
              f"unc={str(rec['uncertainty_count']):<4} -> {flag}")

    silent = [r for r in records if r["silent_failure"]]
    report = {
        "_meta": "fault-injection and recovery drill; every number below is measured, not asserted",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "python": sys.version.split()[0],
        "environment": info,
        "scenario_count": len(records),
        "silent_failures": len(silent),
        "scenarios": records,
    }

    if a.json:
        _write(a.json, json.dumps(report, ensure_ascii=False, indent=2))
        print(f"[fault_inject] json  -> {a.json}")
    if a.markdown:
        _write(a.markdown, to_markdown(records, info))
        print(f"[fault_inject] table -> {a.markdown}")

    print(f"[fault_inject] {len(records)} scenarios, {len(silent)} silent failure(s)")
    for r in silent:
        print(f"  ! {r['id']}: {'; '.join(r['mismatch'])}")
    return 1 if silent else 0


if __name__ == "__main__":
    raise SystemExit(main())
