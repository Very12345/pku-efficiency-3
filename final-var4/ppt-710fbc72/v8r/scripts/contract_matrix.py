#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""contract_matrix.py — inject every container form and every boundary value into
`case.output_contract`, run the real pipeline, and record what actually happened.

Why this script exists
----------------------
`references/OUTPUT_CONTRACT.md` claims that every key of the case's
`output_contract` object is mirrored to the top level of `result.json` with its
declared container shape, never as a `null` placeholder, and that CP3 gate G3
fails when that does not hold.  A document is not evidence.  This script turns
each claim into a case: build a case whose contract holds exactly one shape or
one boundary value, run `scripts/main.py` as a child process, then run the
independent gate `scripts/check_contract.py` against the produced output, and
record exit code, `status`, the echoed key set, the container type actually
written, whether a `null` slipped through, and whether the failure was **silent**.

"Silent" has a precise meaning here
----------------------------------
A case that violates a declared invariant is only a *silent* pass when nothing
downstream noticed: the pipeline exited 0, `status` stayed `success` **and** the
independent gate `check_contract.py` still returned 0.  If the gate catches it,
the case is `caught` — that is the system working, not a defect.  Conflating the
two would turn a working verifier into a false alarm.

Case families
-------------
  A  container forms    string / list / object / number / boolean / nested
  B  boundary values    empty string / empty list / empty object / 0 / false /
                        null / very long / absent `output_contract` key /
                        empty contract / non-ASCII key / unknown-prefix key
  C  input integrity    missing case file / malformed JSON / contract declared
                        as a non-object (the shapes the type-default map cannot
                        honour)

Design rules that matter for honesty
------------------------------------
1. **Never run inside the package.**  Executing `scripts/*.py` with the package
   as cwd leaves `scripts/__pycache__/*.pyc`, which the resource contract
   rejects.  The script refuses that unless `--allow-in-package` is passed.
2. **One case = one child process.**  No in-process reuse, so an earlier case
   cannot contaminate a later measurement.
3. **The gate is run for every case**, not only for the ones expected to fail —
   otherwise "the gate would have caught it" stays a guess.
4. **Recorded numbers are measured, never assumed.**  The JSON report and the
   Markdown table come from the same measurement pass.

Usage
-----
    python scripts/contract_matrix.py --skill <package root> \
        [--run <work dir>] [--json <report.json>] [--markdown <table.md>] \
        [--only A01,B07] [--skip ...] [--timeout 180] [--list]

Exit code: 0 when no case failed its declared invariants (or every such case was
caught by the independent gate), 1 when at least one case was silent, 2 on
usage/environment errors.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time

EXPECTED_CONTAINER = {
    "str": str, "list": list, "dict": dict,
    "int": (int, float), "float": (int, float), "bool": bool,
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


def _shrink(text: str, root: str) -> str:
    """Replace the scratch root with `<RUN>` in captured child output.

    Error messages quote the path the child was given, and that path is a host
    path.  A submission package may not carry host paths, so the captured text
    is rewritten before it is stored or rendered.  Nothing else about the
    message is touched.
    """
    if not text:
        return text
    forms = set()
    for sep_in, sep_out in (("\\", "/"), ("/", "\\")):
        base = (root or "").replace("\\", "/").replace("/", sep_out)
        if not base:
            continue
        forms.add(base)
        forms.add(base.replace(sep_out, sep_out * 2))   # repr()-escaped, as in a message
    for form in sorted(forms, key=len, reverse=True):
        text = text.replace(form, "<RUN>")
    return text


def _tail(text: str, n: int = 220) -> str:
    text = (text or "").strip().replace("\r", "")
    return text.splitlines()[-1][:n] if text else ""


def _json_block(text: str):
    """Parse the first complete JSON object out of a child's stdout.

    `check_contract.py` pretty-prints its verdict, so "take the last line" would
    only ever yield the closing brace.
    """
    text = text or ""
    start = text.find("{")
    while start != -1:
        depth, in_str, esc = 0, False, False
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


# ---------------------------------------------------------------------------
# the case catalogue
# ---------------------------------------------------------------------------
# Every entry declares:
#   id       stable label used in the report and by --only/--skip
#   family   A containers / B boundaries / C input integrity
#   inject   what exactly is put into case.output_contract
#   expect   declared invariants: exit, status, all keys echoed, no null
#   build    callable(run_dir, base_case) -> (case_path, out_dir)
# ---------------------------------------------------------------------------


def cases(R) -> list:
    ex = R.base
    base_case = os.path.join(ex, "case.json")

    def make(cid: str, contract, *, drop_key: bool = False, raw: str | None = None):
        """Materialise one case directory; returns (case_path, out_dir, input_dir)."""
        d = os.path.join(R.run, "cases", cid)
        inp = os.path.join(d, "input")
        _rm(d)
        os.makedirs(inp, exist_ok=True)
        for name in os.listdir(ex):
            src = os.path.join(ex, name)
            dst = os.path.join(inp, name)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            elif os.path.exists(src):
                shutil.copy2(src, dst)
        cp = os.path.join(inp, "case.json")
        if raw is not None:
            _write(cp, raw)
        else:
            obj = _load(base_case) or {}
            if drop_key:
                obj.pop("output_contract", None)
            else:
                obj["output_contract"] = contract
            _write(cp, json.dumps(obj, ensure_ascii=False, indent=2))
        return cp, os.path.join(d, "out"), inp

    S = []

    def add(cid, family, inject, expect, builder):
        S.append(dict(id=cid, family=family, inject=inject, expect=expect, build=builder))

    # ---- A. container forms -------------------------------------------------
    add("A01-string", "A-container",
        "output_contract = {k_str: \"hello\"}（字符串形态）",
        dict(exit=0, status="success", echo=True, no_null=True,
             note="按声明类型填 \"\"（无已知语义 → 类型默认值）"),
        lambda: make("A01-string", {"k_str": "hello"}))
    add("A02-list", "A-container",
        "output_contract = {k_list: [\"a\",\"b\"]}（列表形态）",
        dict(exit=0, status="success", echo=True, no_null=True,
             note="按声明类型填 []"),
        lambda: make("A02-list", {"k_list": ["a", "b"]}))
    add("A03-object", "A-container",
        "output_contract = {k_obj: {\"x\": 1}}（对象形态）",
        dict(exit=0, status="success", echo=True, no_null=True,
             note="按声明类型填 {}"),
        lambda: make("A03-object", {"k_obj": {"x": 1}}))
    add("A04-number", "A-container",
        "output_contract = {k_num: 7}（数值形态）",
        dict(exit=0, status="success", echo=True, no_null=True,
             note="按声明类型填 0"),
        lambda: make("A04-number", {"k_num": 7}))
    add("A05-boolean", "A-container",
        "output_contract = {k_bool: true}（布尔形态）",
        dict(exit=0, status="success", echo=True, no_null=True,
             note="按声明类型填 false（PDF 导出类键恒 false 是诚实能力缺口，见 D10）"),
        lambda: make("A05-boolean", {"k_bool": True}))
    add("A06-nested", "A-container",
        "output_contract = {k_nest: {\"a\": [{\"b\": 1}]}}（嵌套对象）",
        dict(exit=0, status="success", echo=True, no_null=True,
             note="嵌套形态按顶层声明类型填 {}（不做深拷贝就是诚实做法：运行期并没有产出这个结构）"),
        lambda: make("A06-nested", {"k_nest": {"a": [{"b": 1}]}}))

    # ---- B. boundary values ------------------------------------------------
    add("B01-empty-string", "B-boundary",
        "边界：值为空串 \"\"",
        dict(exit=0, status="success", echo=True, no_null=True, note="空串应原样回显为空串"),
        lambda: make("B01-empty-string", {"k_es": ""}))
    add("B02-empty-list", "B-boundary",
        "边界：值为空数组 []",
        dict(exit=0, status="success", echo=True, no_null=True, note="空数组应回显为空数组"),
        lambda: make("B02-empty-list", {"k_el": []}))
    add("B03-empty-object", "B-boundary",
        "边界：值为空对象 {}",
        dict(exit=0, status="success", echo=True, no_null=True, note="空对象应回显为空对象"),
        lambda: make("B03-empty-object", {"k_eo": {}}))
    add("B04-zero", "B-boundary",
        "边界：数值 0（falsy，容易被 `if value:` 吞掉）",
        dict(exit=0, status="success", echo=True, no_null=True,
             note="0 必须仍然出现（0 与『缺失』不是一回事）"),
        lambda: make("B04-zero", {"k_z": 0}))
    add("B05-false", "B-boundary",
        "边界：布尔 false（falsy）",
        dict(exit=0, status="success", echo=True, no_null=True,
             note="false 必须仍然出现"),
        lambda: make("B05-false", {"k_f": False}))
    add("B06-null", "B-boundary",
        "边界：值为 null（契约自己声明了 null —— 容易把 null 传递到顶层）",
        dict(exit=0, status="success", echo=True, no_null=True,
             note="**禁止 null 占位**：应替换为该声明类型的默认值；声明是 null 时取字符串 \"\""),
        lambda: make("B06-null", {"k_n": None}))
    add("B07-very-long", "B-boundary",
        "边界：超长值（单键 3000 字符）",
        dict(exit=0, status="success", echo=True, no_null=True,
             note="不应截断/不应抛错；无已知语义 → \"\"（不把长文本塞进结果）"),
        lambda: make("B07-very-long", {"k_long": "L" * 3000}))
    add("B08-very-long-key", "B-boundary",
        "边界：超长键名（256 字符）",
        dict(exit=0, status="success", echo=True, no_null=True,
             note="键名长度不设限，应原样出现在顶层"),
        lambda: make("B08-very-long-key", {"k_" + "x" * 254: True}))
    add("B09-nonascii", "B-boundary",
        "边界：非 ASCII 键名（中文键）",
        dict(exit=0, status="success", echo=True, no_null=True,
             note="`ensure_ascii=False` 应保留中文键名与值"),
        lambda: make("B09-nonascii", {"契约字段": "值"}))
    add("B10-missing-key", "B-boundary",
        "边界：case.json **完全没有** output_contract 键",
        dict(exit=0, status="success", echo=True, no_null=True,
             note="没有契约就不回显任何键；G3 的 missing 应为空集（不因缺契约而失败）"),
        lambda: make("B10-missing-key", None, drop_key=True))
    add("B11-empty-contract", "B-boundary",
        "边界：output_contract = {}（空对象）",
        dict(exit=0, status="success", echo=True, no_null=True,
             note="空契约 → 回显 0 个键；G3 仍应全过"),
        lambda: make("B11-empty-contract", {}))
    add("B12-unknown-prefix", "B-boundary",
        "边界：语义未覆盖的键名（`zzz_unknown_field`）",
        dict(exit=0, status="success", echo=True, no_null=True,
             note="不落任何已知前缀 → 类型默认值，且**不得**出现在 contract_echo_derived"),
        lambda: make("B12-unknown-prefix", {"zzz_unknown_field": True}))
    add("B13-derived-known", "B-boundary",
        "对照：语义已知的键（`preview_png` / `notes_per_slide`）",
        dict(exit=0, status="success", echo=True, no_null=True,
             note="应取本次运行真实值 true（不是类型默认 false），并记入 contract_echo_derived"),
        lambda: make("B13-derived-known", {"preview_png": True, "notes_per_slide": True}))
    add("B14-preview-false", "B-boundary",
        "边界：`preview_png: false`（G8 的预览要求随之关闭）",
        dict(exit=0, status="success", echo=True, no_null=True,
             note="G8 只在声明 preview_png 为真时要求封面存在；false 时不应因此失败"),
        lambda: make("B14-preview-false", {"preview_png": False}))

    # ---- C. input integrity ------------------------------------------------
    add("C01-case-missing", "C-input",
        "输入缺陷：--case 指向不存在的文件",
        dict(exit=1, status="failed", echo=False, no_null=True,
             note="立即失败（D1）；写 status=failed 的 result.json；不产 pptx"),
        lambda: (os.path.join(R.run, "cases", "C01-case-missing", "input", "absent.json"),
                 os.path.join(R.run, "cases", "C01-case-missing", "out"),
                 os.path.join(R.run, "cases", "C01-case-missing", "input")))
    add("C02-case-broken", "C-input",
        "输入缺陷：case.json 被截断（非法 JSON）",
        dict(exit=1, status="failed", echo=False, no_null=True,
             note="JSONDecodeError 被 main() 捕获 → failed result + exit 1，不抛裸栈"),
        lambda: make("C02-case-broken", None,
                     raw='{"case_id": "broken", "title": '))
    add("C03-contract-not-object", "C-input",
        "输入缺陷：output_contract 是**非对象**（字符串 \"oops\"）",
        dict(exit=1, status="failed", echo=False, no_null=True,
             note="_echo_output_contract() 直接对契约调用 .items() ⇒ AttributeError 被 main() "
                  "捕获 → failed result + exit 1；产物大部分已落盘但 result.json 只剩失败信封"),
        lambda: make("C03-contract-not-object", "oops"))
    add("C04-contract-list", "C-input",
        "输入缺陷：output_contract 是**数组** [\"a\",\"b\"]",
        dict(exit=1, status="failed", echo=False, no_null=True,
             note="数组同样没有 .items() ⇒ 与 C03 同一条失败路径"),
        lambda: make("C04-contract-list", ["a", "b"]))
    add("C05-empty-case-object", "C-input",
        "输入缺陷：case.json = {}（完全空对象）",
        dict(exit=0, status="partial", echo=True, no_null=True,
             note="case_id 取文件名 stem（`case`）；无材料、无结构化字段 ⇒ 诚实降级为 partial，"
                  "uncertainty 记 3 条"),
        lambda: make("C05-empty-case-object", None, raw="{}"))
    add("C06-case-is-directory", "C-input",
        "输入缺陷：--case 指向一个**目录**",
        dict(exit=1, status="failed", echo=False, no_null=True,
             note="IsADirectoryError 应被捕获成 failed result + exit 1"),
        lambda: (os.path.join(R.run, "cases", "C06-case-is-directory", "input"),
                 os.path.join(R.run, "cases", "C06-case-is-directory", "out"),
                 os.path.join(R.run, "cases", "C06-case-is-directory", "input")))
    return S


# ---------------------------------------------------------------------------
# measurement
# ---------------------------------------------------------------------------


class Runner:
    def __init__(self, skill: str, run_dir: str, timeout: int = 180):
        self.skill = os.path.abspath(skill)
        self.src_skill = self.skill
        self.run = os.path.abspath(run_dir)
        self.timeout = timeout
        self.base = os.path.join(self.run, "base")
        self.main = os.path.join(self.skill, "scripts", "main.py")
        self.gate = os.path.join(self.skill, "scripts", "check_contract.py")
        # run on a copy, so the submission package can never gain __pycache__
        self.work_skill = os.path.join(self.run, "skill")

    def prepare(self) -> dict:
        if not os.path.isfile(self.main):
            raise SystemExit(f"[contract_matrix] main.py not found under {self.skill}")
        _rm(self.run)
        os.makedirs(self.run, exist_ok=True)
        shutil.copytree(self.src_skill, self.work_skill)
        self.main = os.path.join(self.work_skill, "scripts", "main.py")
        self.gate = os.path.join(self.work_skill, "scripts", "check_contract.py")
        shutil.copytree(os.path.join(self.src_skill, "examples"), self.base)
        rc, _o, err = self._exec(
            [sys.executable, os.path.join(self.work_skill, "scripts", "make_synthetic_inputs.py"),
             "--dir", self.base], os.path.join(self.run, "setup-cwd"))
        figs = os.path.join(self.base, "figs")
        info = {"source_skill": "<SKILL>", "scratch_skill": "<RUN>/skill",
                "scratch": "<RUN>", "figure_gen_exit": rc,
                "figures": sorted(os.listdir(figs)) if os.path.isdir(figs) else []}
        if rc != 0:
            info["figure_gen_stderr"] = _tail(err)
        return info

    def _exec(self, argv, cwd):
        os.makedirs(cwd, exist_ok=True)
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        try:
            p = subprocess.run(argv, cwd=cwd, env=env, capture_output=True,
                               timeout=self.timeout)
            return (p.returncode, p.stdout.decode("utf-8", "replace"),
                    p.stderr.decode("utf-8", "replace"))
        except subprocess.TimeoutExpired:
            return 124, "", f"timeout after {self.timeout}s"


def measure(sc: dict, R: Runner) -> dict:
    t0 = time.perf_counter()
    case, out, inp = sc["build"]()
    cwd = os.path.join(R.run, "cases", sc["id"], "cwd")
    task = os.path.join(inp, "task.md")

    argv = [sys.executable, R.main, "--case", case, "--out", out]
    if os.path.exists(task):
        argv[2:2] = ["--task", task]
    rc, stdout, stderr = R._exec(argv, cwd)

    result = _load(os.path.join(out, "result.json")) if os.path.isdir(out) else None
    contract = None
    if isinstance(result, dict) or True:
        case_obj = _load(case) if os.path.isfile(case) else None
        if isinstance(case_obj, dict):
            c = case_obj.get("output_contract")
            contract = c if isinstance(c, dict) else c

    rec = {
        "id": sc["id"], "family": sc["family"], "inject": sc["inject"],
        "expected": dict(sc["expect"]),
        "case_path": _shrink(case, R.run), "out_dir": _shrink(out, R.run), "exit": rc,
        "stdout_tail": _shrink(_tail(stdout), R.run),
        "stderr_tail": _shrink(_tail(stderr), R.run),
        "result_json_written": isinstance(result, dict),
        "status": (result or {}).get("status"),
        "seconds": round(time.perf_counter() - t0, 3),
    }

    echo, types, nulls, missing = {}, {}, [], []
    if isinstance(contract, dict):
        for key in contract:
            if key not in (result or {}):
                missing.append(key)
                continue
            val = result[key]
            echo[key] = val
            types[key] = type(val).__name__
            if val is None:
                nulls.append(key)
    rec.update({
        "contract_is_object": isinstance(contract, dict),
        "contract_key_count": len(contract) if isinstance(contract, dict) else None,
        "echoed": echo, "echoed_types": types,
        "null_placeholders": nulls, "missing_keys": missing,
        "all_keys_echoed": not missing,
        "has_null": bool(nulls),
        "echo_n": len(echo),
    })

    # derived-value bookkeeping: which echoes were declared *derived* by the run
    derived = ((result or {}).get("verification") or {}).get("contract_echo_derived") or {}
    rec["contract_echo_derived"] = derived
    rec["result_top_key_count"] = len(result) if isinstance(result, dict) else 0
    marker = os.path.join(out, f"{(result or {}).get('case_id') or 'case'}_deck.pptx")
    rec["deck_written"] = os.path.isfile(marker)
    rec["artifacts_written"] = (len([n for n in os.listdir(out)
                                     if os.path.isfile(os.path.join(out, n))])
                                if os.path.isdir(out) else 0)
    # A clean run writes the full envelope (28 keys measured in TEST.md §1).
    # A short envelope after a crash is *degraded*, and that is worth naming:
    # it means the failure record itself is thin while the intermediates live on.
    rec["envelope_degraded"] = (isinstance(result, dict)
                                and rec["result_top_key_count"] < 20)

    # the independent gate, for EVERY case (not only the failing ones)
    rp = os.path.join(out, "result.json")
    rec["gate_ran"] = os.path.isfile(rp)
    if rec["gate_ran"]:
        gargv = [sys.executable, R.gate, "--result", rp, "--out-dir", out]
        if os.path.isfile(case):
            gargv += ["--case", case]
        grc, gout, gerr = R._exec(gargv, cwd)
        payload = _json_block(gout)
        rec["gate_exit"] = grc
        rec["gate_valid"] = payload.get("valid") if isinstance(payload, dict) else None
        rec["gate_failed"] = ([g.get("gate") for g in payload.get("gates", []) if not g.get("ok")]
                              if isinstance(payload, dict) else None)
        rec["gate_stdout_tail"] = _shrink(_tail(gout, 400), R.run)
        rec["gate_stderr_tail"] = _shrink(_tail(gerr), R.run)
        g3 = None
        if isinstance(payload, dict):
            for g in payload.get("gates", []):
                if g.get("gate") == "G3":
                    g3 = g
        rec["G3"] = g3

    # ---- verdicts ----------------------------------------------------------
    exp = sc["expect"]
    violations = []
    if exp.get("exit") is not None and rc != exp["exit"]:
        violations.append(f"exit={rc} 与声明 {exp['exit']} 不符")
    if exp.get("status") is not None and rec["status"] != exp["status"]:
        violations.append(f"status={rec['status']!r} 与声明 {exp['status']!r} 不符")
    if exp.get("echo") and isinstance(contract, dict) and missing:
        violations.append(f"契约键未回显: {missing}")
    if exp.get("no_null") and nulls:
        violations.append(f"顶层出现 null 占位: {nulls}")
    if isinstance(contract, dict):
        for key, val in contract.items():
            if key not in types:
                continue
            want = EXPECTED_CONTAINER.get(type(val).__name__)
            got = result[key]
            if want is not None and not isinstance(got, want):
                violations.append(f"键 {key!r} 容器类型变了: 声明 {type(val).__name__} → 实测 {type(got).__name__}")

    # A case is *silent* only when nothing downstream noticed: the pipeline was
    # happy AND the independent gate was happy.  Caught-by-the-gate is a pass.
    gate_noticed = rec.get("gate_valid") is False
    rec["violations"] = violations
    rec["visual_violation"] = bool(violations)
    rec["caught_by_gate"] = bool(violations) and gate_noticed
    rec["silent_pass"] = bool(violations) and not gate_noticed
    rec["verdict"] = ("silent-pass" if rec["silent_pass"] else
                      "caught-by-gate" if rec["caught_by_gate"] else
                      "degraded-envelope" if rec.get("envelope_degraded") else
                      "as-declared")
    return rec


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------


def to_markdown(records: list, info: dict, cases_meta: list) -> str:
    L = []
    L.append("## 0. 结论")
    L.append("")
    silent = [r for r in records if r["silent_pass"]]
    caught = [r for r in records if r["caught_by_gate"]]
    L.append(f"- 用例总数 **{len(records)}**（A 容器形态 / B 边界值 / C 输入完整性）")
    L.append(f"- 按声明通过的：**{len(records) - len(silent) - len(caught)}**")
    L.append(f"- **静默通过**（违规但 exit 0 + `success` + 独立门也 0）：**{len(silent)}**"
             + ("：" + "、".join(f"`{r['id']}`" for r in silent) if silent else ""))
    L.append(f"- 被独立门拦下的：**{len(caught)}**"
             + ("：" + "、".join(f"`{r['id']}`" for r in caught) if caught else ""))
    L.append("")
    L.append("`静默通过` 的定义：**管线 exit 0 且 `status=success`，并且独立门 "
             "`check_contract.py` 也返回 0**。若门拦下了它，那叫\"被拦下\"，是验证器在"
             "正常工作，不是缺陷。")
    L.append("")
    L.append("## 1. 实测环境")
    L.append("")
    L.append(f"- python `{info.get('python')}`；命令：`{info.get('command')}`")
    L.append(f"- 参测包（只读源）：`<SKILL>`（本报告不写入宿主路径）")
    L.append(f"- 管线跑在包的**一份拷贝**上：`<RUN>/skill`（不在包内执行，避免 `__pycache__`）")
    L.append(f"- 合成图件 {len(info.get('figures') or [])} 个（exit {info.get('figure_gen_exit')}）")
    L.append("")
    L.append("## 2. 逐用例实测（全部为真实运行）")
    L.append("")
    L.append("| 用例 | 家族 | 实测 exit | 独立门 exit | 门 valid | 实测 status | 契约键 | 回显 | null | result 顶层键 | 判定 |")
    L.append("|-|-|-|-|-|-|-|-|-|-|-|")
    for r in records:
        ge = r.get("gate_exit", "—")
        gv = r.get("gate_valid", "—")
        L.append("| `{}` | {} | {} | {} | {} | `{}` | {} | {} | {} | {} | {} |".format(
            r["id"], r["family"].split("-")[0], r["exit"], ge, gv,
            r["status"], r["contract_key_count"], r["echo_n"],
            ("**" + ",".join(r["null_placeholders"]) + "**") if r["has_null"] else "0",
            r.get("result_top_key_count", "—"),
            "**静默通过**" if r["silent_pass"] else
            "被门拦下" if r["caught_by_gate"] else
            "信封降级" if r.get("envelope_degraded") else "按声明"))
    L.append("")
    L.append("## 3. 契约回显逐键实测（容器形态有没有被改）")
    L.append("")
    L.append("| 用例 | 键 | 契约声明类型 | 实测类型 | 实测值 | contract_echo_derived |")
    L.append("|-|-|-|-|-|-|")
    for r in records:
        if not r["echoed"]:
            continue
        cobj = r.get("_contract_types") or {}
        for k, v in r["echoed"].items():
            L.append("| `{}` | `{}` | {} | {} | `{}` | {} |".format(
                r["id"], k, cobj.get(k, "?"), r["echoed_types"].get(k, "?"),
                json.dumps(v, ensure_ascii=False)[:60],
                "是" if k in (r.get("contract_echo_derived") or {}) else "否"))
    L.append("")
    L.append("## 4. 逐用例明细")
    L.append("")
    for r in records:
        L.append(f"#### `{r['id']}`（{r['family']}）")
        L.append("")
        L.append(f"- **注入**：{r['inject']}")
        L.append(f"- **声明**：exit={r['expected'].get('exit')} / status=`{r['expected'].get('status')}`"
                 f" / 全键回显={r['expected'].get('echo')} / 无 null={r['expected'].get('no_null')}")
        L.append(f"- **实测**：exit={r['exit']}；result.json "
                 f"{'已写出' if r['result_json_written'] else '未写出'}；status=`{r['status']}`；"
                 f"契约键 {r['contract_key_count']}；回显 {r['echo_n']}；"
                 f"缺键 {r['missing_keys'] or '无'}；null 占位 {r['null_placeholders'] or '无'}；"
                 f"{r['seconds']}s")
        if r.get("G3"):
            L.append(f"- **G3 原文**：`{r['G3'].get('ok')}` — {r['G3'].get('detail')}")
        if r.get("contract_echo_derived"):
            L.append(f"- **运行期派生回显**：`{json.dumps(r['contract_echo_derived'], ensure_ascii=False)}`")
        if r["violations"]:
            L.append("- **违规**：" + "；".join(r["violations"]))
            L.append(f"- **谁发现了**：{'独立门 ' + str(r.get('gate_failed')) if r['caught_by_gate'] else '**没有任何人 —— 静默通过**'}")
        if r["stderr_tail"]:
            L.append(f"- **stderr 末行**：`{r['stderr_tail']}`")
        L.append(f"- **产物**：deck {'已落盘' if r.get('deck_written') else '未落盘'}；"
                 f"`--out` 下文件 {r.get('artifacts_written')} 个；"
                 f"result.json 顶层键 **{r.get('result_top_key_count')}**（完整信封 28 键）")
        L.append(f"- **判定**：{'**静默通过**' if r['silent_pass'] else '被独立门拦下' if r['caught_by_gate'] else '信封降级（诚实失败）' if r.get('envelope_degraded') else '按声明'}")
        L.append("")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--skill", default=os.path.dirname(here),
                    help="package root (default: parent of this script's dir)")
    ap.add_argument("--run", default="", help="scratch dir (default <cwd>/contract-matrix-run)")
    ap.add_argument("--json", default="", help="write the machine-readable report here")
    ap.add_argument("--markdown", default="", help="write the Markdown table here")
    ap.add_argument("--only", default="", help="comma separated case ids")
    ap.add_argument("--skip", default="", help="comma separated case ids to skip")
    ap.add_argument("--timeout", type=int, default=180, help="per-run timeout (s)")
    ap.add_argument("--allow-in-package", action="store_true",
                    help="permit a scratch dir inside the package (NOT recommended)")
    ap.add_argument("--list", action="store_true", help="list case ids and exit")
    a = ap.parse_args(argv)

    skill = os.path.abspath(a.skill)
    run = os.path.abspath(a.run or os.path.join(os.getcwd(), "contract-matrix-run"))

    def inside(p, root):
        p, root = os.path.abspath(p), os.path.abspath(root)
        return p == root or p.startswith(root + os.sep)

    if inside(run, skill) and not a.allow_in_package:
        print("[contract_matrix] refusing a scratch dir inside the package: running the "
              "pipeline there leaves scripts/__pycache__/*.pyc, which the resource "
              "contract rejects. Pass --run outside the package.", file=sys.stderr)
        return 2

    R = Runner(skill, run, timeout=a.timeout)
    print(f"[contract_matrix] skill  = <SKILL>")
    print(f"[contract_matrix] scratch= {run}")
    info = R.prepare()
    info["python"] = sys.version.split()[0]
    info["command"] = (f"python scripts/contract_matrix.py --skill <SKILL> --run <RUN>"
                       + (f" --only {a.only}" if a.only else ""))

    S = cases(R)
    if a.list:
        for s in S:
            print(f"{s['id']:22s} {s['family']:12s} {s['inject']}")
        return 0
    only = {x.strip() for x in a.only.split(",") if x.strip()}
    skip = {x.strip() for x in a.skip.split(",") if x.strip()}
    if only:
        S = [s for s in S if s["id"] in only]
    if skip:
        S = [s for s in S if s["id"] not in skip]

    records = []
    for s in S:
        rec = measure(s, R)
        # keep the declared container types for the report (not part of the run)
        case_obj = _load(rec["case_path"]) if os.path.isfile(rec["case_path"]) else None
        c = (case_obj or {}).get("output_contract")
        rec["_contract_types"] = ({k: type(v).__name__ for k, v in c.items()}
                                  if isinstance(c, dict) else {})
        records.append(rec)
        flag = "SILENT" if rec["silent_pass"] else ("caught" if rec["caught_by_gate"] else "ok")
        print(f"  {rec['id']:22s} exit={rec['exit']:<3} status={str(rec['status']):<9} "
              f"gate={str(rec.get('gate_exit')):<3} echo={rec['echo_n']:<2} "
              f"null={len(rec['null_placeholders'])} -> {flag}")

    silent = [r for r in records if r["silent_pass"]]
    report = {
        "_meta": "output-contract container/boundary matrix; every number is measured",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "python": sys.version.split()[0],
        "command": info["command"],
        "environment": info,
        "case_count": len(records),
        "silent_pass_count": len(silent),
        "caught_by_gate_count": len([r for r in records if r["caught_by_gate"]]),
        "silent_pass_ids": [r["id"] for r in silent],
        "cases": records,
    }
    if a.json:
        _write(a.json, json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n")
        print(f"[contract_matrix] json  -> {a.json}")
    if a.markdown:
        _write(a.markdown, to_markdown(records, info, S) + "\n")
        print(f"[contract_matrix] table -> {a.markdown}")

    print(f"[contract_matrix] {len(records)} cases, {len(silent)} silent pass(es), "
          f"{report['caught_by_gate_count']} caught by the gate")
    for r in silent:
        print(f"  ! SILENT {r['id']}: {'; '.join(r['violations'])}")
    return 1 if silent else 0


if __name__ == "__main__":
    raise SystemExit(main())
