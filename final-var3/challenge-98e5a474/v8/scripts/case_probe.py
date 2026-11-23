#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""case_probe.py -- 多案例泛化与题集执行器（可运行的题集 + 边界探针）。

它对"题集"里的每个案例做三件事：

1. **真跑**：把案例输入交给 `scripts/main.py`（或编辑任务走 `--edit-svg`），
   在**包外**临时目录里产出真实图稿与 `result.json`；
2. **对期望**：逐条比对**该案例声明的可接受区间**（实体/关系/分组计数、
   fail/warn 上限、必备产物角色、溯源覆盖率、单位是否声明、SVG 是否
   良构 XML 等），把"期望值 / 实测值 / 是否满足"三项写进报告；
3. **探边界**：跑一组**故意越界**的探针（不支持的图型、超长链、特殊字符、
   containment 未分组…），记录它到底在哪一步、以什么退出码失效 ——
   这就是"泛化到哪里会失效"的**实测**来源，而不是拍脑袋写的免责声明。

**画布预算规则**（本脚本会替你量，规则来自实测的布局公式）：
`style.canvas` 一旦显式声明，布局**不会**再自动扩展（见 `layout.py` 的
canvas 分支），而 SVG 的 `viewBox` 与 PNG/PDF 都将按声明尺寸裁剪。层状布局
（layered，左→右）的节点 x = `层号 × (240 + 130)`，所以

    canvas.width  >= 370 × (最大层号) + 单个节点最大宽度 + 余量（建议 ≥ 40）
    canvas.height >= 行数 × (90 + 70) + 图例/脚注所需高度

不声明 `style.canvas` 时布局自动扩到内容尺寸（实测 18 节点单链 →
6609×500），代价是 PNG 会变得很大（实测 19827×1500）。

用法（建议在包外运行，产物写到包外）：

    python scripts/case_probe.py --skill-root <技能根> --out <包外目录>
    python scripts/case_probe.py --group new      --skill-root . --out /tmp/cp
    python scripts/case_probe.py --group probe    --skill-root . --out /tmp/cp
    python scripts/case_probe.py --only synth-mitophagy-101 --list
    python scripts/case_probe.py --list

退出码：0 = 每个案例都落在声明的可接受区间内、每个边界探针都复现了它
声明的失效形态；1 = 至少一条偏离（报告里给出期望/实测差值）；2 = 参数错误。

产物：`<out>/case-report.json`（机器可读，逐案全字段）+ 终端表格。
本脚本**只读**技能包：案例输入从包里读，产物与临时夹具一律写在 `--out`。
"""

import argparse
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


# --------------------------------------------------------------------------
# 题集登记表：每个案例的输入、产出结构期望、可接受区间、难度层
# --------------------------------------------------------------------------
def case_registry():
    return [
        {
            "id": "example-schematic-001",
            "kind": "case",
            "group": "bundled",
            "genre": "schematic（信号通路机制图）",
            "difficulty": "入门（6 实体 / 5 关系 / 3 分组 / 3 图例项）",
            "input": "examples/case.json",
            "sources": "examples/sources/figure03-note.md",
            "expect": {
                "exit": 0, "status": "success",
                "max_fail": 0, "max_warn": 0,
                "entity_count": 6, "relation_count": 5, "group_count": 3,
                "roles": ["figure", "preview", "pdf"],
                "xml_wellformed": True,
                "canvas_overflow": False,
                "traceability_entities_min": 1.0,
            },
        },
        {
            "id": "example-chart-002",
            "kind": "case",
            "group": "bundled",
            "genre": "chart（数据表驱动的柱状图）",
            "difficulty": "入门（4 类别 / 单位上轴 / 图例由表生成）",
            "input": "examples/case_chart.json",
            "sources": "examples/sources/data-table.csv",
            "expect": {
                "exit": 0, "status": "success",
                "max_fail": 0, "max_warn": 0,
                "category_count": 4, "unit_nonempty": True,
                "roles": ["figure", "preview", "pdf"],
                "xml_wellformed": True,
            },
        },
        {
            "id": "example-edit-003",
            "kind": "case",
            "group": "bundled",
            "genre": "edit（对已生成 SVG 做源文件级增量编辑）",
            "difficulty": "入门（3 个动作：rename / relabel / note）",
            "input": "examples/case_edit.json",
            "sources": "examples/sources/figure03-note.md",
            "edit_svg_from": "example-schematic-001",
            "expect": {
                "exit": 0, "status": "success",
                "max_fail": 1, "max_warn": 0,
                "change_records": 3,
                "roles": ["figure", "preview", "pdf"],
            },
        },
        {
            "id": "synth-mitophagy-101",
            "kind": "case",
            "group": "new",
            "genre": "schematic（细胞生物学：线粒体自噬清除通路）",
            "difficulty": "中（6 实体 / 5 关系 / 3 模块；含一处材料自带的反误读）",
            "input": "examples/cases/case_mitophagy.json",
            "sources": "examples/cases/sources/mitophagy-note.md",
            "expect": {
                "exit": 0, "status": "success",
                "max_fail": 0, "max_warn": 0,
                "entity_count": 6, "relation_count": 5, "group_count": 3,
                "roles": ["figure", "preview", "pdf"],
                "xml_wellformed": True,
                "traceability_entities_min": 1.0,
            },
        },
        {
            "id": "synth-expression-heatmap-102",
            "kind": "case",
            "group": "new",
            "genre": "chart（转录组：三条件 × 三重复的表达矩阵热图）",
            "difficulty": "中高（矩阵 + 行/列标签 + 色标单位；与柱状图完全不同的渲染路径）",
            "input": "examples/cases/case_expr_heatmap.json",
            "sources": "examples/cases/sources/expression-table.csv",
            "expect": {
                "exit": 0, "status": "success",
                "max_fail": 0, "max_warn": 0,
                "category_count": 3, "unit_nonempty": True,
                "roles": ["figure", "preview", "pdf"],
                "xml_wellformed": True,
            },
        },
        {
            "id": "B1-unsupported-chart-type",
            "kind": "probe",
            "group": "probe",
            "genre": "边界：声明了不支持的 chart_type（histogram）",
            "difficulty": "探针",
            "expect": {
                "exit": 1, "status": "failed",
                "fail_contains": "pipeline",
                "roles": [],
            },
        },
        {
            "id": "B2-dense-chain-declared-canvas",
            "kind": "probe",
            "group": "probe",
            "genre": "边界：18 节点单链 + 显式 style.canvas 1500x900",
            "difficulty": "探针",
            "expect": {
                "exit": 0, "status": "success",
                "max_fail": 0, "max_warn": 0,
                "canvas_overflow": True,      # 实测：内容溢出而检查不报
                "roles": ["figure", "preview", "pdf"],
            },
        },
        {
            "id": "B3-dense-chain-auto-canvas",
            "kind": "probe",
            "group": "probe",
            "genre": "边界：同样的 18 节点单链，但不声明 canvas",
            "difficulty": "探针",
            "expect": {
                "exit": 0, "status": "success",
                "max_fail": 0, "max_warn": 0,
                "canvas_overflow": False,     # 实测：自动扩画布后不再溢出
                "roles": ["figure", "preview", "pdf"],
            },
        },
        {
            "id": "B4-special-characters",
            "kind": "probe",
            "group": "probe",
            "genre": "边界：实体名含 & < > \" 与 µ/×/² 等符号",
            "difficulty": "探针",
            "expect": {
                "exit": 0, "status": "success",
                "max_fail": 0, "max_warn": 0,
                "xml_wellformed": True,
                "raw_markup_absent": True,
                "roles": ["figure", "preview", "pdf"],
            },
        },
        {
            "id": "B5-containment-without-group",
            "kind": "probe",
            "group": "probe",
            "genre": "边界：containment 关系未落到任何分组框",
            "difficulty": "探针",
            "expect": {
                "exit": 1, "status": "partial",
                "fail_contains": "spec_lint.spec.containment_group",
                "roles": ["figure", "preview", "pdf"],
            },
        },
    ]


# --------------------------------------------------------------------------
# 探针夹具生成（全部写在 --out 下，不动技能包）
# --------------------------------------------------------------------------
def _load(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _dump(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)


def _base_manifest(root):
    """探针共用的基座清单：取包内 schematic 示例的 manifest 深拷贝。"""
    return json.loads(json.dumps(
        _load(os.path.join(root, "examples", "case.json"))["manifest"]))


def write_probe_fixtures(root, fx):
    """生成 5 个探针夹具；返回 {probe_id: case_path}。"""
    base_case = _load(os.path.join(root, "examples", "case.json"))
    out = {}

    # B1 不支持的图型
    c = json.loads(json.dumps(base_case))
    c["case_id"] = "probe-b1"
    c.pop("manifest", None)
    c["figure_type"] = "chart"
    c["manifest"] = {
        "schema_version": "1.0", "figure_type": "chart",
        "title": "probe: unsupported chart type",
        "data": {"chart_type": "histogram",
                 "table": {"columns": ["c", "v"], "rows": [["a", 1.0], ["b", 2.0]]},
                 "category_col": "c", "value_col": "v", "unit": "au"},
    }
    p = os.path.join(fx, "b1.json")
    _dump(p, c)
    out["B1-unsupported-chart-type"] = p

    # B2/B3 18 节点单链（B3 只是去掉 style.canvas）
    N = 18
    for name, canvas in (("b2", {"width": 1500, "height": 900}), ("b3", None)):
        c = json.loads(json.dumps(base_case))
        c["case_id"] = "probe-%s" % name
        c["sources"] = []
        m = _base_manifest(root)
        m["title"] = "probe: %d-node chain (%s canvas)" % (
            N, "declared" if canvas else "auto")
        m["entities"] = [
            {"id": "E%d" % i, "name": "node-%02d" % i, "type": "protein",
             "source": "synthetic dense probe",
             "evidence": "chain node %d" % i} for i in range(1, N + 1)]
        m["relations"] = [
            {"id": "R%d" % i, "from": "E%d" % i, "to": "E%d" % (i + 1),
             "kind": "activates", "source": "synthetic dense probe",
             "evidence": "chain edge %d" % i} for i in range(1, N)]
        m["groups"] = [{"id": "G1", "label": "all nodes",
                        "members": ["E%d" % i for i in range(1, N + 1)],
                        "source": "probe", "evidence": "one group"}]
        m["legend"] = [{"id": "L1", "key": "activation",
                        "label": "activation", "arrow": "activation",
                        "line": "solid", "source": "probe"}]
        if canvas:
            m["style"] = {"font_size": 16, "canvas": canvas}
        else:
            m.pop("style", None)
        c["manifest"] = m
        p = os.path.join(fx, "%s.json" % name)
        _dump(p, c)
        out["B2-dense-chain-declared-canvas" if name == "b2"
            else "B3-dense-chain-auto-canvas"] = p

    # B4 特殊字符
    c = json.loads(json.dumps(base_case))
    c["case_id"] = "probe-b4"
    c["sources"] = []
    m = _base_manifest(root)
    m["title"] = "probe: escaping & entities"
    m["entities"][0]["name"] = 'IL-6 & NF-\u03baB <up> "quoted"'
    m["entities"][1]["name"] = "PINK1 > Parkin? \u00b5M \u00d7 10\u00b2"
    m["entities"][2]["name"] = "ATF4 / CHOP (stress)"
    c["manifest"] = m
    p = os.path.join(fx, "b4.json")
    _dump(p, c)
    out["B4-special-characters"] = p

    # B5 containment 未分组
    c = json.loads(json.dumps(base_case))
    c["case_id"] = "probe-b5"
    c["sources"] = []
    m = _base_manifest(root)
    m["title"] = "probe: containment without group"
    m["relations"].append({"id": "R6", "from": "E1", "to": "E5",
                           "kind": "contains", "source": "probe",
                           "evidence": "containment drawn as an arrow"})
    c["manifest"] = m
    p = os.path.join(fx, "b5.json")
    _dump(p, c)
    out["B5-containment-without-group"] = p
    return out


# --------------------------------------------------------------------------
# 观测：从产物里量出可比较的数字
# --------------------------------------------------------------------------
def _xml_wellformed(svg_path):
    """优先用 lxml（本机已装）；没有就用标准库 xml.etree 兜底。"""
    try:
        with open(svg_path, "rb") as fh:
            blob = fh.read()
    except OSError:
        return None, "cannot read svg"
    try:
        from lxml import etree
        etree.fromstring(blob)
        return True, "lxml"
    except ImportError:
        pass
    except Exception as exc:                          # noqa: BLE001
        return False, "lxml: %r" % (exc,)
    try:
        import xml.etree.ElementTree as ET
        ET.fromstring(blob)
        return True, "stdlib"
    except Exception as exc:                          # noqa: BLE001
        return False, "stdlib: %r" % (exc,)


def observe(out_dir, result, expect):
    """把一次运行的产物量化成可对期望的观测值。"""
    obs = {}
    checks = (result.get("verification") or {}).get("checks") or {}
    fails = [c.get("check") for c in (checks.get("fails") or [])
             if isinstance(c, dict)]
    warns = [c.get("check") for c in (checks.get("warns") or [])
             if isinstance(c, dict)]
    obs["status"] = result.get("status")
    obs["top_level_keys"] = len(result)
    obs["fail_count"] = len(fails)
    obs["warn_count"] = len(warns)
    obs["fail_checks"] = sorted(fails)
    obs["warn_checks"] = sorted(warns)
    mr = result.get("main_result") or {}
    obs["entity_count"] = mr.get("entity_count")
    obs["relation_count"] = mr.get("relation_count")
    obs["group_count"] = mr.get("group_count")
    obs["roles"] = sorted(a.get("role") for a in (result.get("artifacts") or []))
    obs["change_records"] = len(result.get("change_records") or [])
    dm = result.get("data_mapping") or {}
    obs["category_count"] = len(dm.get("unique_categories") or []) or None
    obs["unit_nonempty"] = bool(dm.get("unit"))
    tr = (result.get("verification") or {}).get("traceability") or {}
    pct = tr.get("entities_traceable_pct")
    obs["traceability_entities"] = (round(float(pct) / 100.0, 4)
                                    if isinstance(pct, (int, float)) else None)
    obs["spec_lint_valid"] = ((result.get("verification") or {})
                              .get("spec_lint") or {}).get("valid")

    svg = os.path.join(out_dir, "figure.svg")
    if os.path.isfile(svg):
        ok, backend = _xml_wellformed(svg)
        obs["xml_wellformed"] = ok
        obs["xml_backend"] = backend
        with open(svg, "r", encoding="utf-8") as fh:
            text = fh.read()
        obs["raw_markup_absent"] = ("<up>" not in text)
        obs["svg_bytes"] = os.path.getsize(svg)
        vb = re.search(r'viewBox="([\d.\s-]+)"', text)
        if vb:
            parts = [float(x) for x in vb.group(1).split()]
            obs["viewbox"] = parts[2:4]
    else:
        obs["xml_wellformed"] = None
        obs["raw_markup_absent"] = None
        obs["svg_bytes"] = 0

    lay = os.path.join(out_dir, "layout.json")
    if os.path.isfile(lay):
        L = _load(lay)
        nodes = L.get("nodes") or {}
        cv = L.get("canvas") or {}
        if nodes and cv.get("width"):
            mx = max(n.get("x", 0) + n.get("w", 0) for n in nodes.values())
            my = max(n.get("y", 0) + n.get("h", 0) for n in nodes.values())
            obs["canvas"] = [cv.get("width"), cv.get("height")]
            obs["content_wh"] = [round(mx), round(my)]
            obs["canvas_overflow"] = bool(mx > cv["width"]
                                          or my > cv.get("height", 0))
    png = os.path.join(out_dir, "figure.png")
    if os.path.isfile(png):
        try:
            from PIL import Image
            with Image.open(png) as im:
                obs["png_size"] = list(im.size)
        except Exception:                             # noqa: BLE001
            obs["png_size"] = None
    return obs


def evaluate(expect, obs):
    """逐条比对期望；返回 [{name, expected, observed, ok}]。"""
    rows = []

    def add(name, exp, got):
        ok = True
        if exp is not None:
            if name.startswith("max_"):
                ok = got is not None and got <= exp
            elif name == "roles":
                ok = sorted(got or []) == sorted(exp)
            elif name == "fail_contains":
                ok = exp in (got or [])
            elif name == "traceability_entities_min":
                ok = got is not None and got >= exp
            else:
                ok = got == exp
        rows.append({"name": name, "expected": exp, "observed": got, "ok": ok})

    add("exit", expect.get("exit"), obs.get("_exit"))
    add("status", expect.get("status"), obs.get("status"))
    if "max_fail" in expect:
        add("max_fail", expect["max_fail"], obs.get("fail_count"))
    if "max_warn" in expect:
        add("max_warn", expect["max_warn"], obs.get("warn_count"))
    if "fail_contains" in expect:
        add("fail_contains", expect["fail_contains"], obs.get("fail_checks"))
    for key in ("entity_count", "relation_count", "group_count",
                "category_count", "change_records", "xml_wellformed",
                "raw_markup_absent", "canvas_overflow", "unit_nonempty"):
        if key in expect:
            add(key, expect[key], obs.get(key))
    if "roles" in expect:
        add("roles", expect["roles"], obs.get("roles"))
    if "traceability_entities_min" in expect:
        add("traceability_entities_min", expect["traceability_entities_min"],
            obs.get("traceability_entities"))
    return rows


# --------------------------------------------------------------------------
# 主流程
# --------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="case_probe",
        description="多案例题集执行器：逐案真跑 + 对期望 + 边界探针")
    ap.add_argument("--skill-root", default=DEFAULT_ROOT,
                    help="技能根目录（默认：本脚本的上一级）")
    ap.add_argument("--out", default=None,
                    help="产物目录（默认：系统临时目录下的新目录）")
    ap.add_argument("--group", default="all",
                    choices=["all", "bundled", "new", "probe"],
                    help="只跑某一组（bundled 包内三示例 / new 新合成案例 / probe 边界探针）")
    ap.add_argument("--only", default=None, help="逗号分隔的案例 id")
    ap.add_argument("--list", action="store_true", help="只列题集，不运行")
    ap.add_argument("--json", action="store_true", help="同时打印 JSON 摘要")
    ap.add_argument("--quiet", action="store_true", help="不打逐条明细")
    ap.add_argument("--keep", action="store_true", help="保留临时夹具目录")
    args = ap.parse_args(argv)

    root = os.path.abspath(args.skill_root)
    if not os.path.isfile(os.path.join(root, "scripts", "main.py")):
        print("FATAL: %s is not a skill root (scripts/main.py missing)" % root)
        return 2

    items = case_registry()
    if args.list:
        for it in items:
            print("%-34s %-8s %-8s %s" % (it["id"], it["kind"], it["group"],
                                          it["genre"]))
        return 0
    if args.group != "all":
        items = [i for i in items if i["group"] == args.group]
    if args.only:
        want = {x.strip() for x in args.only.split(",") if x.strip()}
        items = [i for i in items if i["id"] in want]
    if not items:
        print("FATAL: no case selected")
        return 2

    out_dir = os.path.abspath(args.out) if args.out else tempfile.mkdtemp(
        prefix="sse-case-probe-")
    if out_dir == root or out_dir.startswith(root + os.sep):
        print("FATAL: --out must not be inside the skill package (%s)" % root)
        return 2
    os.makedirs(out_dir, exist_ok=True)
    fx = os.path.join(out_dir, "_fixtures")
    probes = write_probe_fixtures(root, fx)

    print("case-probe: skill-root=%s" % root)
    print("case-probe: out=%s" % out_dir)
    print("case-probe: %d item(s)\n" % len(items))

    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    records = []
    run_out = {}

    for it in items:
        cid = it["id"]
        case_path = probes.get(cid) or os.path.join(root, it["input"])
        item_out = os.path.join(out_dir, cid)
        cmd = [PY, os.path.join(root, "scripts", "main.py"),
               "--case", case_path, "--out", item_out]
        if it.get("edit_svg_from"):
            src = run_out.get(it["edit_svg_from"])
            if not src:
                records.append({"id": cid, "kind": it["kind"],
                                "skipped": "needs %s first"
                                           % it["edit_svg_from"]})
                print("=== [%s] SKIPPED (needs %s)" % (cid, it["edit_svg_from"]))
                continue
            cmd += ["--edit-svg", src]
        t0 = time.time()
        proc = subprocess.run(cmd, cwd=out_dir, env=env,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        dt = round(time.time() - t0, 2)
        out = proc.stdout.decode("utf-8", "replace")
        rp = os.path.join(item_out, "result.json")
        rec = {"id": cid, "kind": it["kind"], "group": it["group"],
               "genre": it["genre"], "difficulty": it["difficulty"],
               "input": os.path.relpath(case_path, root)
               if case_path.startswith(root) else "<generated probe fixture>",
               "command": "python scripts/main.py --case <in> --out <out>"
                          + (" --edit-svg <generated>" if it.get("edit_svg_from")
                             else ""),
               "exit_code": proc.returncode, "seconds": dt,
               "stdout_tail": [l[:180] for l in out.strip().splitlines()[-4:]]}
        if os.path.isfile(rp):
            res = _load(rp)
            obs = observe(item_out, res, it.get("expect") or {})
            rec["result_json"] = True
            rec["observed"] = obs
            rows = evaluate(it.get("expect") or {}, dict(obs, _exit=proc.returncode))
            rec["expectations"] = rows
            rec["conforms"] = all(r["ok"] for r in rows)
            rec["deviations"] = ["%s expected %r got %r"
                                 % (r["name"], r["expected"], r["observed"])
                                 for r in rows if not r["ok"]]
            if cid == "example-schematic-001":
                run_out[cid] = os.path.join(item_out, "figure.svg")
        else:
            rec["result_json"] = False
            rows = evaluate(it.get("expect") or {}, {"_exit": proc.returncode})
            rec["expectations"] = rows
            rec["conforms"] = all(r["ok"] for r in rows)
            rec["deviations"] = ["%s expected %r got %r"
                                 % (r["name"], r["expected"], r["observed"])
                                 for r in rows if not r["ok"]]
        records.append(rec)

        if not args.quiet:
            print("=== [%s] %s ===" % (cid, it["genre"]))
            print("    difficulty: %s" % it["difficulty"])
            print("    input     : %s" % rec["input"])
            print("    actual    : exit=%s status=%s result.json=%s "
                  "(%ss)" % (rec["exit_code"], (rec.get("observed") or {})
                             .get("status"), rec["result_json"], dt))
            if rec["result_json"]:
                o = rec["observed"]
                print("    observed  : entities=%s relations=%s groups=%s "
                      "categories=%s roles=%s" % (
                          o.get("entity_count"), o.get("relation_count"),
                          o.get("group_count"), o.get("category_count"),
                          ",".join(o.get("roles") or []) or "-"))
                if o.get("canvas"):
                    print("    canvas    : %sx%s content=%sx%s overflow=%s"
                          % (o["canvas"][0], o["canvas"][1],
                             (o.get("content_wh") or ["?", "?"])[0],
                             (o.get("content_wh") or ["?", "?"])[1],
                             o.get("canvas_overflow")))
                print("    checks    : fails=%s warns=%s"
                      % (o.get("fail_checks") or "-", o.get("warn_checks") or "-"))
            for r in rec["expectations"]:
                print("      %s %-26s expected=%-22r observed=%r"
                      % ("[ok]  " if r["ok"] else "[FAIL]",
                         r["name"], r["expected"], r["observed"]))
            print("    verdict   : %s"
                  % ("CONFORMS" if rec["conforms"] else
                     "DEVIATES -> " + "; ".join(rec["deviations"])))
            print("")

    conforming = [r for r in records if r.get("conforms")]
    bad = [r for r in records if r.get("conforms") is False]
    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "skill_root": root,
        "python": sys.version.split()[0],
        "total": len(records),
        "conforming": len(conforming),
        "deviating": [r["id"] for r in bad],
        "items": records,
    }
    jp = os.path.join(out_dir, "case-report.json")
    _dump(jp, report)
    print("=" * 72)
    print("case-probe: %d/%d item(s) conform to their declared expectations"
          % (len(conforming), len(records)))
    if bad:
        for r in bad:
            print("  DEVIATION %s: %s" % (r["id"], "; ".join(r["deviations"])))
    print("case-probe: report written to %s" % jp)
    if not args.keep:
        shutil.rmtree(fx, ignore_errors=True)
    if args.json:
        print(json.dumps({"total": report["total"],
                          "conforming": report["conforming"],
                          "deviating": report["deviating"]},
                         ensure_ascii=False))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
