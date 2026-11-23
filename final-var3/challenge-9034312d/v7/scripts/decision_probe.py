# -*- coding: utf-8 -*-
"""decision_probe.py — 20 个决策用例的批量探针（决策显性化版交付物之一）。

它把 `references/DECISION-CASES.md` 里那张表变成**可执行**的：现场合成 20 个输入形态
（材料异常 / 模板缺失 / 依赖缺失 / 契约四形态 / 状态不一致），逐个跑本包的流水线，
然后只抽取**与判决有关的可观测量**——退出码、`status`、`verify.ok`、
`verify.errors[].rule`、`verify.warnings[].rule`、`uncertainty[].scope`、失败门号。

设计约束（与包内其它脚本一致）：
- 脚本自定位（`os.path.dirname(__file__)`），**任何 cwd 都可运行**；
- 所有临时输入/输出都写在 `--out`（默认系统临时目录），**不在技能包内落任何文件**；
- 只读技能根的 `scripts/`，不修改 `assets/`、`templates/`、`examples/`。

用法:
    python "$SKILL_DIR/scripts/decision_probe.py" [--out <目录>] [--json <report.json>]

退出码: 0 = 探针跑完（不代表 20 个用例都该 exit 0，见 §期望列）；1 = 探针自身出错。
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

sys.dont_write_bytecode = True  # 包内不落 .pyc

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(HERE)
MAIN_PY = os.path.join(HERE, "main.py")


# ------------------------------------------------------------------ 用例定义
# 每个用例: (id, 名称, 期望退出码, 期望 status, 期望 verify.errors 规则集合, 输入构造)
def _cases():
    C = []

    C.append(("D01", "case 文件不存在", 2, None, [],
              {"kind": "missing_case"}))
    C.append(("D02", "case.json 不可解析", 1, "failed", [],
              {"kind": "raw", "name": "d02_bad.json", "text": '{"case_id":"d02","entities":[,,,]}'}))
    C.append(("D03", "结构化实体但无 relations", 0, "success", [],
              {"kind": "obj", "name": "d03.json", "obj": {
                  "case_id": "d03", "title": "结构化实体无关系", "figure_type": "flow",
                  "canvas": {"width_mm": 300, "height_mm": 180},
                  "entities": [{"id": f"S{i}", "name": f"步骤{i}", "kind": "step",
                                "stage": "A" if i < 3 else "B", "source": f"task.md §{i}"}
                               for i in range(1, 5)]}}))
    C.append(("D04", "纯文本（text-heuristic）", 0, "success", [],
              {"kind": "obj", "name": "d04.json", "obj": {
                  "case_id": "d04", "title": "仅自由文本", "figure_type": "flow",
                  "canvas": {"width_mm": 300, "height_mm": 180},
                  "text": "第一步 称量并溶解原料；第二步 升温反应两小时；第三步 冷却结晶；"
                          "第四步 过滤洗涤并干燥；第五步 取样送检。"}}))
    C.append(("D05", "单条断头关系", 0, "partial", [],
              {"kind": "obj", "name": "d05.json", "obj": {
                  "case_id": "d05", "title": "断头关系", "figure_type": "route",
                  "canvas": {"width_mm": 300, "height_mm": 180},
                  "entities": [{"id": "E1", "name": "构建载体", "kind": "step", "stage": "A", "source": "task.md §1"},
                               {"id": "E2", "name": "转化宿主", "kind": "step", "stage": "A", "source": "task.md §1"},
                               {"id": "E3", "name": "阳性克隆筛选", "kind": "step", "stage": "B", "source": "task.md §2"}],
                  "relations": [{"id": "R1", "from": "E1", "to": "E2", "kind": "flow"},
                                {"id": "R2", "from": "E2", "to": "E9", "kind": "flow"}]}}))
    C.append(("D06", "全部关系断头（安静退化）", 0, "success", [],
              {"kind": "obj", "name": "d06.json", "obj": {
                  "case_id": "d06", "title": "全部关系断头", "figure_type": "route",
                  "canvas": {"width_mm": 300, "height_mm": 180},
                  "entities": [{"id": "A1", "name": "步骤甲", "kind": "step", "stage": "S1", "source": "task.md §1"},
                               {"id": "A2", "name": "步骤乙", "kind": "step", "stage": "S2", "source": "task.md §2"}],
                  "relations": [{"id": "X1", "from": "A1", "to": "ZZ", "kind": "flow"},
                                {"id": "X2", "from": "YY", "to": "A2", "kind": "flow"}]}}))
    C.append(("D07", "实体缺 source", 3, "partial", [],
              {"kind": "obj", "name": "d07.json", "obj": {
                  "case_id": "d07", "title": "实体缺 source", "figure_type": "route",
                  "canvas": {"width_mm": 300, "height_mm": 180},
                  "entities": [{"id": "E1", "name": "步骤一", "kind": "step", "stage": "A", "source": "task.md §1"},
                               {"id": "E2", "name": "步骤二", "kind": "step", "stage": "A"},
                               {"id": "E3", "name": "步骤三", "kind": "step", "stage": "B"}],
                  "relations": [{"id": "R1", "from": "E1", "to": "E2", "kind": "flow"},
                                {"id": "R2", "from": "E2", "to": "E3", "kind": "flow"}]}}))
    C.append(("D08", "实体 id 重复", 0, "partial", [],
              {"kind": "obj", "name": "d08.json", "obj": {
                  "case_id": "d08", "title": "实体 id 重复", "figure_type": "route",
                  "canvas": {"width_mm": 300, "height_mm": 180},
                  "entities": [{"id": "E1", "name": "步骤甲", "kind": "step", "stage": "A", "source": "task.md §1"},
                               {"id": "E1", "name": "步骤乙", "kind": "step", "stage": "A", "source": "task.md §2"},
                               {"id": "E2", "name": "步骤丙", "kind": "step", "stage": "B", "source": "task.md §3"}],
                  "relations": [{"id": "R1", "from": "E1", "to": "E2", "kind": "flow"}]}}))
    C.append(("D09", "类别/关系词表外", 0, "success", [],
              {"kind": "obj", "name": "d09.json", "obj": {
                  "case_id": "d09", "title": "类别词表外", "figure_type": "route",
                  "canvas": {"width_mm": 300, "height_mm": 180},
                  "entities": [{"id": "E1", "name": "步骤甲", "kind": "步骤步骤", "stage": "A", "source": "task.md §1"},
                               {"id": "E2", "name": "步骤乙", "kind": "step", "stage": "A", "source": "task.md §2"}],
                  "relations": [{"id": "R1", "from": "E1", "to": "E2", "kind": "莫名其妙关系"}]}}))
    C.append(("D10", "画布过小 + 实体过多", 0, "success", [],
              {"kind": "obj", "name": "d10.json", "obj": {
                  "case_id": "d10", "title": "画布溢出", "figure_type": "route",
                  "canvas": {"width_mm": 60, "height_mm": 40},
                  "entities": [{"id": f"E{i}", "name": f"第{i}阶段工作内容较长的步骤名称{i}",
                                "kind": "step", "stage": f"阶段{i}", "source": f"task.md §{i}"}
                               for i in range(1, 13)],
                  "relations": [{"id": f"R{i}", "from": f"E{i}", "to": f"E{i+1}", "kind": "flow"}
                                for i in range(1, 12)]}}))
    C.append(("D11", "规则资产为空文件", 0, "success", [],
              {"kind": "obj", "name": "d11.json", "rules": "empty",
               "obj": {"case_id": "d11", "title": "空规则文件", "figure_type": "flow",
                       "canvas": {"width_mm": 300, "height_mm": 180},
                       "entities": [{"id": "S1", "name": "步骤一", "kind": "step", "stage": "A", "source": "task.md §1"},
                                    {"id": "S2", "name": "步骤二", "kind": "step", "stage": "B", "source": "task.md §2"}],
                       "relations": [{"id": "R1", "from": "S1", "to": "S2", "kind": "flow"}]}}))
    C.append(("D12", "规则资产路径不存在", 0, "success", [],
              {"kind": "obj", "name": "d12.json", "rules": "missing",
               "obj": {"case_id": "d12", "title": "规则文件缺失", "figure_type": "flow",
                       "canvas": {"width_mm": 300, "height_mm": 180},
                       "entities": [{"id": "S1", "name": "步骤一", "kind": "step", "stage": "A", "source": "task.md §1"},
                                    {"id": "S2", "name": "步骤二", "kind": "step", "stage": "B", "source": "task.md §2"}],
                       "relations": [{"id": "R1", "from": "S1", "to": "S2", "kind": "flow"}]}}))
    C.append(("D13", "装置图 flow 终点为 material", 3, "partial", ["apparatus-flow-into-material"],
              {"kind": "obj", "name": "d13.json", "obj": {
                  "case_id": "d13", "title": "物料作流向终点", "figure_type": "apparatus",
                  "canvas": {"width_mm": 300, "height_mm": 180},
                  "entities": [{"id": "D1", "name": "反应釜", "kind": "device", "source": "task.md §1"},
                               {"id": "M1", "name": "缓冲液", "kind": "material", "source": "task.md §2"}],
                  "relations": [{"id": "R1", "from": "D1", "to": "M1", "kind": "flow"}]}}))
    C.append(("D14", "装置图产物流出（warn）", 0, "success", [],
              {"kind": "obj", "name": "d14.json", "obj": {
                  "case_id": "d14", "title": "产物继续流出", "figure_type": "apparatus",
                  "canvas": {"width_mm": 300, "height_mm": 180},
                  "entities": [{"id": "D1", "name": "离心机", "kind": "device", "source": "task.md §1"},
                               {"id": "P1", "name": "上清液", "kind": "product", "source": "task.md §1"},
                               {"id": "D2", "name": "浓缩仪", "kind": "device", "source": "task.md §2"}],
                  "relations": [{"id": "R1", "from": "D1", "to": "P1", "kind": "flow"},
                                {"id": "R2", "from": "P1", "to": "D2", "kind": "flow"}]}}))
    C.append(("D15", "sequence 连 material", 3, "partial", ["sequence-step-only"],
              {"kind": "obj", "name": "d15.json", "obj": {
                  "case_id": "d15", "title": "sequence 连物料", "figure_type": "route",
                  "canvas": {"width_mm": 300, "height_mm": 180},
                  "entities": [{"id": "S1", "name": "步骤一", "kind": "step", "stage": "A", "source": "task.md §1"},
                               {"id": "M1", "name": "中间物料", "kind": "material", "stage": "A", "source": "task.md §1"}],
                  "relations": [{"id": "R1", "from": "S1", "to": "M1", "kind": "sequence"}]}}))
    C.append(("D16", "connect 两端非结构件", 3, "partial", ["connect-structural"],
              {"kind": "obj", "name": "d16.json", "obj": {
                  "case_id": "d16", "title": "connect 两端非结构件", "figure_type": "apparatus",
                  "canvas": {"width_mm": 300, "height_mm": 180},
                  "entities": [{"id": "S1", "name": "步骤一", "kind": "step", "source": "task.md §1"},
                               {"id": "S2", "name": "步骤二", "kind": "step", "source": "task.md §2"}],
                  "relations": [{"id": "R1", "from": "S1", "to": "S2", "kind": "connect"}]}}))
    C.append(("D17", "自环关系", 3, "partial", ["no-self-loop"],
              {"kind": "obj", "name": "d17.json", "obj": {
                  "case_id": "d17", "title": "自环关系", "figure_type": "flow",
                  "canvas": {"width_mm": 300, "height_mm": 180},
                  "entities": [{"id": "S1", "name": "循环步骤", "kind": "step", "stage": "A", "source": "task.md §1"},
                               {"id": "S2", "name": "后续步骤", "kind": "step", "stage": "B", "source": "task.md §2"}],
                  "relations": [{"id": "R1", "from": "S1", "to": "S1", "kind": "flow"},
                                {"id": "R2", "from": "S1", "to": "S2", "kind": "flow"}]}}))
    C.append(("D18", "recycle 回流（warn）", 0, "success", [],
              {"kind": "obj", "name": "d18.json", "obj": {
                  "case_id": "d18", "title": "回流关系", "figure_type": "flow",
                  "canvas": {"width_mm": 300, "height_mm": 180},
                  "entities": [{"id": "S1", "name": "反应", "kind": "step", "stage": "A", "source": "task.md §1"},
                               {"id": "S2", "name": "分离", "kind": "step", "stage": "B", "source": "task.md §2"}],
                  "relations": [{"id": "R1", "from": "S1", "to": "S2", "kind": "flow"},
                                {"id": "R2", "from": "S2", "to": "S1", "kind": "recycle",
                                 "label": "未反应物料回流"}]}}))
    C.append(("D19", "空壳 case（无实体无文本）", 3, "failed", [],
              {"kind": "obj", "name": "d19.json", "obj": {
                  "case_id": "d19", "title": "空壳输入", "figure_type": "route"}}))
    C.append(("D20", "非法 figure_type", 0, "success", [],
              {"kind": "obj", "name": "d20.json", "obj": {
                  "case_id": "d20", "title": "非法图类", "figure_type": "freeform",
                  "canvas": {"width_mm": 300, "height_mm": 180},
                  "entities": [{"id": "E1", "name": "步骤一", "kind": "step", "stage": "A", "source": "task.md §1"},
                               {"id": "E2", "name": "步骤二", "kind": "step", "stage": "B", "source": "task.md §2"}],
                  "relations": [{"id": "R1", "from": "E1", "to": "E2", "kind": "flow"}]}}))
    return C


# ------------------------------------------------------------------ 执行
def _materialise(spec, work_dir):
    """按用例定义把输入写到 work_dir，返回 (case_path, rules_path)。"""
    kind = spec["kind"]
    if kind == "missing_case":
        return os.path.join(work_dir, "does-not-exist.json"), None
    if kind == "raw":
        p = os.path.join(work_dir, spec["name"])
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(spec["text"])
        return p, None
    p = os.path.join(work_dir, spec["name"])
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(spec["obj"], fh, ensure_ascii=False, indent=2)
    rules = None
    if spec.get("rules") == "empty":
        rules = os.path.join(work_dir, "empty_rules.json")
        with open(rules, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("{}")
    elif spec.get("rules") == "missing":
        rules = os.path.join(work_dir, "no-such-rules.json")
    return p, rules


def _load_result(out_root):
    for root, _dirs, files in os.walk(out_root):
        if "result.json" in files:
            p = os.path.join(root, "result.json")
            try:
                with open(p, "r", encoding="utf-8") as fh:
                    return json.load(fh), os.path.relpath(p, out_root).replace("\\", "/")
            except Exception:  # noqa: BLE001
                return None, None
    return None, None


def _run_case(case_path, rules_path, run_out, cwd):
    """在**子进程**里跑一次单案例流水线。

    必须起子进程而不是 in-process 导入：每个用例都要拿到真实的**退出码**
    （0/1/2/3）与 stdout/stderr，这正是决策规则的可观测位点之一。
    路径全部先 `os.path.abspath` 再传参，并显式给 `cwd`，因此探针自身
    在任何 cwd 下都成立。
    """
    cmd = [sys.executable, os.path.abspath(MAIN_PY),
           "--case", os.path.abspath(case_path),
           "--out", os.path.abspath(run_out)]
    if rules_path:
        cmd += ["--rules", os.path.abspath(rules_path)]
    t0 = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=cwd)
    return p, round(time.time() - t0, 3)


def _gates_false(result_path):
    if not result_path or not os.path.isfile(result_path):
        return None
    check = os.path.join(HERE, "check.py")
    p = subprocess.run([sys.executable, os.path.abspath(check), os.path.abspath(result_path)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    try:
        data = json.loads((p.stdout or "").strip() or "{}")
    except Exception:  # noqa: BLE001
        return None
    gates = data.get("gates") or {}
    return sorted(k for k, v in gates.items() if not v)


def main(argv) -> int:
    ap = argparse.ArgumentParser(description="20 个决策用例的批量探针（只做观测，不改交付物）")
    ap.add_argument("--out", default=None, help="临时工作目录（默认系统临时目录下的新目录）")
    ap.add_argument("--json", default=None, help="把观测表写成 JSON（默认写到 <out>/decision-observations.json）")
    ap.add_argument("--keep", action="store_true", help="保留临时目录（默认跑完即删）")
    args = ap.parse_args(argv)

    out_root = os.path.abspath(args.out) if args.out else tempfile.mkdtemp(prefix="decide-")
    os.makedirs(out_root, exist_ok=True)
    rows = []
    try:
        for cid, name, exp_code, exp_status, exp_errs, spec in _cases():
            work = os.path.join(out_root, cid)
            os.makedirs(work, exist_ok=True)
            case_path, rules_path = _materialise(spec, work)
            run_out = os.path.join(work, "out")
            p, dt = _run_case(case_path, rules_path, run_out, cwd=work)
            res, rel = _load_result(run_out)
            verify = (res or {}).get("verify") or {}
            errs = sorted({e.get("rule") for e in (verify.get("errors") or [])})
            warns = sorted({w.get("rule") for w in (verify.get("warnings") or [])})
            unc = [u.get("scope") for u in (res or {}).get("uncertainty") or []]
            gates_false = _gates_false(os.path.join(run_out, rel) if rel else None)
            rows.append({
                "id": cid, "case": name,
                "expected_exit": exp_code, "exit": p.returncode,
                "expected_status": exp_status, "status": (res or {}).get("status"),
                "verify_ok": verify.get("ok"),
                "errors": errs, "expected_errors": exp_errs,
                "warnings": warns, "uncertainty": unc,
                "gates_false": gates_false,
                "result_json": rel, "sec": dt,
                "stderr_tail": (p.stderr or "").strip().splitlines()[-1][:160]
                               if (p.stderr or "").strip() else "",
                "verdict": "按表" if (p.returncode == exp_code and
                                     (exp_status is None or (res or {}).get("status") == exp_status) and
                                     errs == sorted(exp_errs)) else "偏离（查 DECISION-CASES.md §4）",
            })
            if p.returncode != exp_code and (p.stderr or "").strip():
                rows[-1]["stdout_head"] = (p.stdout or "").strip()[:200]
        table = {"generated_by": "scripts/decision_probe.py",
                 "skill_version": "2.1.0", "python": sys.version.split()[0],
                 "out_root": out_root, "rows": rows,
                 "summary": {"total": len(rows),
                             "on_table": sum(1 for r in rows if r["verdict"] == "按表"),
                             "deviations": [r["id"] for r in rows if r["verdict"] != "按表"]}}
        target = args.json or os.path.join(out_root, "decision-observations.json")
        with open(target, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(table, fh, ensure_ascii=False, indent=2)
        for r in rows:
            print(f"{r['id']} exit={r['exit']}(期望{r['expected_exit']}) "
                  f"status={r['status']} err={r['errors']} warn={r['warnings']} "
                  f"unc={r['uncertainty']} gates_false={r['gates_false']} [{r['verdict']}]")
        print(json.dumps(table["summary"], ensure_ascii=False))
        print(f"观测表: {target}")
    finally:
        if not args.keep and not args.out:
            shutil.rmtree(out_root, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
