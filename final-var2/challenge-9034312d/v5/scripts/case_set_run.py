#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""case_set_run.py — 题集跑批与泛化度测量（多案例泛化专项）。

`examples/cases/` 下的每个子目录是一个**案例**（`case.json` + `task.md`）。
本脚本把题集当成一个可执行整体来跑：

1. **逐案跑**：对每个案例跑 `main.py` → `check.py`，收集与判决有关的量
   （退出码、`status`、实体/关系数、`verify.ok`、`errors[]`、`warnings[]`、
   `spec_sha16`、PNG/PDF 字节、失败门号）；
2. **逐案对**：与 `references/case-set.json` 里该案的**期望结构**（允许区间）
   逐项比对，给出 PASS/FAIL 与偏差明细；
3. **泛化探针**：`--text-only` 时把每个案例"压扁"成只留 `text` 字段的版本再跑一遍，
   用两轮的差（实体/关系/风险告警丢失量）**测量结构化信息消失后本包还能保住什么**
   —— 这是本包对"泛化到哪会失效"的机器化回答，不是主观判断。

设计约束（与包内其它脚本一致）：
- 自定位（`os.path.dirname(__file__)`），任何 cwd 可运行；
- **只读包内文件**，所有产物写到 `--out`（默认系统临时目录）；子进程带
  `PYTHONDONTWRITEBYTECODE=1`，包内不会落 `.pyc`；
- 只通过正规 CLI（`subprocess`）调用 `main.py`/`check.py`，不 import 包内模块；
- 报告里的路径相对化（技能根记 `<SKILL_DIR>`、输出根记 `<OUT>`），可随包发布。

用法:
    python "$SKILL_DIR/scripts/case_set_run.py" [--cases-root examples/cases]
                                                [--out <目录>] [--json <report.json>]
                                                [--only <case_id>] [--text-only]
                                                [--timeout 300] [--list]

退出码: 0 = 全部案例 PASS（且 text-only 探针跑完）；1 = 有案例 FAIL；2 = 用法错误。
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(HERE)
MAIN_PY = "scripts/main.py"
CHECK_PY = "scripts/check.py"
EXPECT_PATH = os.path.join(SKILL_ROOT, "references", "case-set.json")


# ------------------------------------------------------------------ 工具

def _rel(base: str, p: str) -> str:
    return os.path.relpath(p, base).replace("\\", "/")


def _load_json(path: str):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _write_json(path: str, obj) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)


def _run(argv, cwd: str, env: dict, timeout: int):
    t0 = time.time()
    try:
        p = subprocess.run(argv, cwd=cwd, env=env, timeout=timeout,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        rc, out, err = p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        rc, out, err = None, b"", f"TIMEOUT {timeout}s".encode()
    dec = lambda b: b.decode("utf-8", errors="replace")  # noqa: E731
    return rc, dec(out), dec(err), round(time.time() - t0, 3)


def _discover(cases_root: str, only: str = None):
    """题集来源（按优先级）：

    1. `references/case-set.json` 里带 `case_path` 的登记项（**权威题集**，
       可以是案例目录，也可以是单个 case.json 文件）；
    2. 否则扫描 `cases_root` 下每个含 case.json 的子目录。

    两种情况都按 case_id 排序，保证多轮运行顺序一致、结果可比。

    **登记表与目录取并集**：登记表里的案子优先（可以用单文件或目录），
    `cases_root` 下**未登记**的案例目录也会被跑，只是标成 `without_expectation`
    （等于"跑了但没验收"）—— 这是为了防止"加了案例却忘了登记"被静默忽略
    （对应 SKILL.md 的 D13）。
    """
    entries = {}
    if os.path.isfile(EXPECT_PATH):
        try:
            entries = (_load_json(EXPECT_PATH) or {}).get("cases") or {}
        except Exception:  # noqa: BLE001
            entries = {}
    seen, out = set(), []
    for cid, e in entries.items():
        cp = (e or {}).get("case_path")
        if not cp:
            continue
        full = os.path.join(SKILL_ROOT, cp)
        if os.path.exists(full):
            out.append((cid, full, True))
            seen.add(cid)
    if os.path.isdir(cases_root):
        for d in sorted(os.listdir(cases_root)):
            full = os.path.join(cases_root, d)
            if d in seen:
                continue
            if os.path.isdir(full) and os.path.isfile(os.path.join(full, "case.json")):
                out.append((d, full, False))
    out.sort(key=lambda x: x[0])
    return [(c, p, reg) for c, p, reg in out if not only or c == only]


def _text_only_copy(src_dir: str, dst_dir: str) -> str:
    """把案例"压扁"成只留 text 的版本（模拟材料未结构化时的输入形态）。"""
    os.makedirs(dst_dir, exist_ok=True)
    src_case = src_dir if os.path.isfile(src_dir) else os.path.join(src_dir, "case.json")
    src_task = None if os.path.isfile(src_dir) else os.path.join(src_dir, "task.md")
    data = _load_json(src_case)
    flat = {
        "case_id": str(data.get("case_id") or "text-only"),
        "title": (str(data.get("title") or "") + "（文本解构探针）"),
        "figure_type": data.get("figure_type") or "flow",
        "canvas": data.get("canvas") or {"width_mm": 300, "height_mm": 190},
        "text": data.get("text") or "",
    }
    _write_json(os.path.join(dst_dir, "case.json"), flat)
    if src_task and os.path.isfile(src_task):
        shutil.copyfile(src_task, os.path.join(dst_dir, "task.md"))
    return os.path.join(dst_dir, "case.json")


# ------------------------------------------------------------------ 观测

def _observe(out_root: str, case_id: str, rc, stdout: str, stderr: str, elapsed: float) -> dict:
    obs = {"exit": rc, "elapsed_s": elapsed, "status": None, "entities": None,
           "relations": None, "verify_ok": None, "errors": [], "warnings": [],
           "uncertainty_scopes": [], "spec_sha16": None, "png_bytes": None,
           "pdf_bytes": None, "check_exit": None, "gates_false": [], "issues": 0,
           "stderr_tail": stderr.strip().splitlines()[-1][:200] if stderr.strip() else ""}
    d = os.path.join(out_root, case_id)
    rp = os.path.join(d, "result.json")
    if not os.path.isfile(rp):
        hits = glob.glob(os.path.join(out_root, "**", "result.json"), recursive=True)
        rp = hits[0] if hits else None
        d = os.path.dirname(rp) if rp else d
    if rp and os.path.isfile(rp):
        try:
            r = _load_json(rp)
            obs["status"] = r.get("status")
            obs["entities"] = len(r.get("entities") or [])
            obs["relations"] = len(r.get("relations") or [])
            v = r.get("verify") or {}
            obs["verify_ok"] = v.get("ok")
            obs["errors"] = sorted({str(e.get("rule")) for e in (v.get("errors") or [])
                                    if isinstance(e, dict)})
            obs["warnings"] = sorted({str(w.get("rule")) for w in (v.get("warnings") or [])
                                      if isinstance(w, dict)})
            obs["uncertainty_scopes"] = sorted({str(u.get("scope")) for u in
                                                (r.get("uncertainty") or []) if isinstance(u, dict)})
            obs["spec_sha16"] = ((v.get("determinism") or {}) or {}).get("spec_sha16")
        except Exception as exc:  # noqa: BLE001
            obs["status"] = f"<不可解析: {type(exc).__name__}>"
        for name, key in (("figure.png", "png_bytes"), ("figure.pdf", "pdf_bytes")):
            p = os.path.join(d, name)
            obs[key] = os.path.getsize(p) if os.path.isfile(p) else 0
    # check.py 结果（优先用 main.py stdout 里的摘要，其次单独跑 check.py）
    try:
        s = json.loads(stdout)
        if isinstance(s, dict) and "gates" in s:
            obs["gates_false"] = sorted(k for k, v in (s.get("gates") or {}).items() if not v)
            obs["issues"] = len(s.get("issues") or [])
            if s.get("check_ok") is not None:
                obs["check_exit"] = 0 if s["check_ok"] else 1
    except Exception:  # noqa: BLE001
        pass
    return obs


# ------------------------------------------------------------------ 判据

def _compare(case_id: str, obs: dict, expect: dict) -> list:
    """按期望结构比对；返回偏差列表（空 = PASS）。"""
    dev = []
    if expect.get("status") and obs["status"] != expect["status"]:
        dev.append(f"status 期望 {expect['status']} 实测 {obs['status']}")
    for key, label in (("entities", "实体数"), ("relations", "关系数")):
        exp = (expect.get(key) or {})
        lo, hi = exp.get("min"), exp.get("max")
        got = obs[key]
        if got is None:
            dev.append(f"{label} 未取到")
        elif lo is not None and got < lo:
            dev.append(f"{label} {got} < 允许下限 {lo}")
        elif hi is not None and got > hi:
            dev.append(f"{label} {got} > 允许上限 {hi}")
    if expect.get("verify_ok") is not None and obs["verify_ok"] is not expect["verify_ok"]:
        dev.append(f"verify.ok 期望 {expect['verify_ok']} 实测 {obs['verify_ok']}")
    allowed_warn = set(expect.get("allowed_warnings") or [])
    unexpected_warn = [w for w in obs["warnings"] if w not in allowed_warn]
    if unexpected_warn:
        dev.append(f"出现未预期的规则告警: {unexpected_warn}")
    forbidden_err = set(expect.get("forbidden_errors") or [])
    hit = [e for e in obs["errors"] if e in forbidden_err]
    if hit:
        dev.append(f"出现禁止的 error 级违规: {hit}")
    if expect.get("expect_no_errors", True) and obs["errors"]:
        dev.append(f"出现 error 级违规: {obs['errors']}")
    if expect.get("png_nonzero", True) and not obs["png_bytes"]:
        dev.append("figure.png 缺失或为 0 字节")
    if expect.get("pdf_nonzero", True) and not obs["pdf_bytes"]:
        dev.append("figure.pdf 缺失或为 0 字节")
    if expect.get("exit") is not None and obs["exit"] != expect["exit"]:
        dev.append(f"退出码期望 {expect['exit']} 实测 {obs['exit']}")
    return dev


# ------------------------------------------------------------------ 主流程

def run(args) -> dict:
    cases_root = os.path.abspath(args.cases_root)
    out_root = os.path.abspath(args.out or os.path.join(tempfile.gettempdir(), "case-set-run"))
    cases = _discover(cases_root, only=args.only)
    expects = {}
    if os.path.isfile(EXPECT_PATH):
        try:
            expects = (_load_json(EXPECT_PATH) or {}).get("cases") or {}
        except Exception:  # noqa: BLE001
            expects = {}

    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    rows = []
    for cid, cdir, registered in cases:
        case_json = cdir if os.path.isfile(cdir) else os.path.join(cdir, "case.json")
        o = os.path.join(out_root, "structured", cid)
        rc, so, se, dt = _run([sys.executable, os.path.join(SKILL_ROOT, MAIN_PY),
                               "--case", cdir, "--out", o], cwd=SKILL_ROOT, env=env,
                              timeout=args.timeout)
        obs = _observe(o, cid, rc, so, se, dt)
        dev = _compare(cid, obs, expects.get(cid) or {}) if (registered and expects.get(cid)) else []
        rows.append({
            "case_id": cid,
            "figure_type": (_load_json(case_json).get("figure_type")
                            if os.path.isfile(case_json) else None),
            "difficulty": (expects.get(cid) or {}).get("difficulty"),
            "has_expectation": bool(registered and expects.get(cid)),
            "verdict": ("PASS" if not dev else "FAIL") if (registered and expects.get(cid))
                       else "NO-EXPECTATION",
            "deviations": dev,
            "observed": obs,
        })

    text_rows = []
    if args.text_only:
        for cid, cdir, _reg in cases:
            flat_dir = os.path.join(out_root, "_flat", cid)
            _text_only_copy(cdir, flat_dir)
            o = os.path.join(out_root, "text-only", cid)
            rc, so, se, dt = _run([sys.executable, os.path.join(SKILL_ROOT, MAIN_PY),
                                   "--case", flat_dir, "--out", o], cwd=SKILL_ROOT,
                                  env=env, timeout=args.timeout)
            obs = _observe(o, cid, rc, so, se, dt)
            text_rows.append({"case_id": cid, "verdict": "—", "observed": obs})

    # 泛化损失：结构化 vs 文本解构
    degrad = []
    for r in rows:
        t = next((x for x in text_rows if x["case_id"] == r["case_id"]), None)
        if not t:
            continue
        a, b = r["observed"], t["observed"]
        degrad.append({
            "case_id": r["case_id"],
            "entities_structured": a["entities"], "entities_text_only": b["entities"],
            "relations_structured": a["relations"], "relations_text_only": b["relations"],
            "entity_retention": (round((b["entities"] or 0) / a["entities"], 3)
                                 if a["entities"] else None),
            "relation_retention": (round((b["relations"] or 0) / a["relations"], 3)
                                   if a["relations"] else None),
            "warnings_lost": sorted(set(a["warnings"]) - set(b["warnings"])),
            "status_structured": a["status"], "status_text_only": b["status"],
        })

    passed = sum(1 for r in rows if r["verdict"] == "PASS")
    no_exp = sum(1 for r in rows if r["verdict"] == "NO-EXPECTATION")
    return {
        "_doc": ("题集跑批报告：逐案实测 + 与 references/case-set.json 的期望结构比对 + "
                 "（可选）文本解构泛化损失。路径已相对化（技能根=<SKILL_DIR>、输出根=<OUT>），"
                 "可随包发布。数字全部由脚本现场产生。"),
        "skill_root": "<SKILL_DIR>",
        "cases_root": os.path.basename(cases_root),
        "python": sys.version.split()[0],
        "platform": sys.platform,
        "expectations_loaded": bool(expects),
        "summary": {
            "cases": len(rows),
            "passed": passed,
            "failed": len(rows) - passed,
            "without_expectation": no_exp,
            "text_only_probes": len(text_rows),
        },
        "rows": rows,
        "text_only": text_rows,
        "generalization_loss": degrad,
    }


def _print(rep: dict) -> None:
    s = rep["summary"]
    print("=" * 96)
    print(f"case_set_run · 案例 {s['cases']} 个 · PASS {s['passed']} / FAIL {s['failed']}"
          f" · 期望表{'已加载' if rep['expectations_loaded'] else '未找到'}"
          f" · python {rep['python']} ({rep['platform']})")
    print("=" * 96)
    print(f"{'case_id':26s} {'图类':9s} {'难度':8s} {'退出':4s} {'status':9s} "
          f"{'实体':4s} {'关系':4s} {'verify':6s} {'结论':14s}")
    print("-" * 96)
    for r in rep["rows"]:
        o = r["observed"]
        print(f"{r['case_id'][:24]:26s} {str(r['figure_type'])[:8]:9s} "
              f"{str(r['difficulty'] or '-')[:6]:8s} {str(o['exit']):4s} "
              f"{str(o['status'])[:9]:9s} {str(o['entities']):4s} {str(o['relations']):4s} "
              f"{str(o['verify_ok']):6s} {r['verdict']:14s}")
        for d in r["deviations"]:
            print(f"    ↳ {d}")
    if rep["generalization_loss"]:
        print("-" * 96)
        print("泛化损失（结构化 → 只留 text 字段）：")
        print(f"{'case_id':26s} {'实体保留':8s} {'关系保留':8s} {'丢失的告警':22s} {'status(文本)':12s}")
        for g in rep["generalization_loss"]:
            print(f"{g['case_id'][:24]:26s} {str(g['entity_retention']):8s} "
                  f"{str(g['relation_retention']):8s} "
                  f"{str(g['warnings_lost'])[:22]:22s} {str(g['status_text_only'])[:12]:12s}")


def main(argv) -> int:
    ap = argparse.ArgumentParser(description="题集跑批与泛化度测量")
    ap.add_argument("--cases-root", default=os.path.join(SKILL_ROOT, "examples", "cases"),
                    help="题集根目录（默认 examples/cases；若 references/case-set.json "
                         "已登记 case_path 则以登记表为准）")
    ap.add_argument("--out", default=None, help="产物落点（默认系统临时目录）")
    ap.add_argument("--json", default=None, help="机器可读报告路径")
    ap.add_argument("--only", default=None, help="只跑一个 case_id")
    ap.add_argument("--text-only", action="store_true",
                    help="同时跑'只留 text 字段'的压扁版，测泛化损失")
    ap.add_argument("--timeout", type=int, default=300, help="单案超时秒数（默认 300）")
    ap.add_argument("--list", action="store_true", help="只列案例与期望，不执行")
    args = ap.parse_args(argv)

    if not os.path.isdir(args.cases_root):
        print(f"FATAL: 题集目录不存在: {args.cases_root}", file=sys.stderr)
        return 2
    if args.list:
        expects = {}
        if os.path.isfile(EXPECT_PATH):
            expects = (_load_json(EXPECT_PATH) or {}).get("cases") or {}
        for cid, cdir, _reg in _discover(args.cases_root):
            e = expects.get(cid) or {}
            print(f"{cid}\n   目录: {_rel(SKILL_ROOT, cdir)}\n"
                  f"   图类: {e.get('figure_type')} · 难度: {e.get('difficulty')} · "
                  f"实体 {e.get('entities')} · 关系 {e.get('relations')}\n"
                  f"   素材: {e.get('concept')}")
        return 0

    rep = run(args)
    _print(rep)
    if args.json:
        _write_json(os.path.abspath(args.json), rep)
        print(f"\n机器可读报告已写入: {os.path.basename(args.json)}")
    # NO-EXPECTATION 不算 FAIL，但要提醒（D13：加了案例没登记 = 没验收）
    if rep["summary"]["without_expectation"]:
        print("\n有 %d 个案例未登记期望：跑了但没验收 —— "
              "请在 references/case-set.json 补登（见 SKILL.md D13）"
              % rep["summary"]["without_expectation"])
    return 0 if rep["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
