#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py — 科研数据图生成与编辑 Skill 的命令行入口（v2，含检查点 CP1–CP6）

执行链（与 SKILL.md S0–S6 对齐）：
    CP1 材料盘点 → CP2 抽取(extract.json) → CP3 spec lint → CP4 导出(SVG/PNG/PDF)
    → CP5 校验(mapcheck+figcheck+确定性) → CP6 契约落地(result.json)

典型调用（路径用脚本自定位，不依赖当前工作目录）：
    python <skill_root>/scripts/main.py --case /input/case.json --out /app/output

输入
----
--case: 案例 JSON（必填）。支持顶层对象 / {"cases":[...]} / 数组（取第一项）。
--out:  输出目录（figure-*.svg/png/pdf、data_manifest.json、validation.json、
        mapcheck_report.json、figcheck_report.json、result.json）。
--work: 中间产物目录（extract.json / spec_lint.json），缺省 = <out 的父目录>/work。
--task/--data/--style/--dpi/--note/--no-pdf/--lang：同 v1，行为不变。

输出契约
--------
result.json 按 references/OUTPUT_CONTRACT.md 生成：output_contract 四形态字段
全部落顶层（禁止 null）；checkpoints/gates/artifacts_sha256 如实记录；
status 与校验结果自洽（任何 fail 不得 completed）。figcheck 在最终 result.json
上以两轮闭环复核（写临时 → 审 → 写最终 → 确认），保证 gates 自证一致（G8）。

退出码：0 = completed 且 G1–G8 全部通过；2 = partial（有图失败/材料缺失/校验缺口）；
1 = failed（无任何图产出或运行异常）。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import chartkit as fe  # noqa: E402
import extract as ext_mod  # noqa: E402
import figcheck as fig_mod  # noqa: E402
import mapcheck as map_mod  # noqa: E402
import spec_lint as lint_mod  # noqa: E402
import verify_rerun as rerun_mod  # noqa: E402

SKILL_ROOT = fe.skill_root()


# ---------------------------------------------------------------- case 装载

def load_case(case_path: str):
    with open(case_path, "r", encoding="utf-8-sig") as f:
        case = json.load(f)
    if isinstance(case, list):
        case = case[0]
    elif isinstance(case, dict) and isinstance(case.get("cases"), list) and case["cases"]:
        case = case["cases"][0]
    if not isinstance(case, dict):
        raise ValueError(f"case.json 不是对象：{type(case).__name__}")
    return case


def discover_task(case: dict, case_dir: str, explicit: str | None):
    if explicit:
        return explicit
    tf = case.get("task_file")
    if tf:
        p = tf if os.path.isabs(tf) else os.path.join(case_dir, tf)
        if os.path.exists(p):
            return p
    for name in ("task.md", "TASK.md", "Task.md"):
        p = os.path.join(case_dir, name)
        if os.path.exists(p):
            return p
    return None


def _re_split_paths(s):
    import re
    return [p for p in re.split(r"[;]", s) if p.strip()]


def discover_data_files(case: dict, case_dir: str, explicit: str | None):
    """返回数据文件绝对路径列表。优先显式字段，其次案例同目录下的表格文件。"""
    outs = []
    if explicit:
        for seg in _re_split_paths(explicit):
            if os.path.exists(seg):
                outs.append(seg)
    files = case.get("data_files") or case.get("sources") or []
    if isinstance(files, str):
        files = [files]
    for f in files:
        if isinstance(f, dict):
            f = f.get("file") or f.get("path")
        if not f:
            continue
        p = f if os.path.isabs(str(f)) else os.path.join(case_dir, str(f))
        if os.path.exists(p) and p not in outs:
            outs.append(p)
    if not outs and os.path.isdir(case_dir):
        exts = (".csv", ".tsv", ".tab", ".json")
        for fn in sorted(os.listdir(case_dir)):
            low = fn.lower()
            if low.startswith("case") or low.startswith("task"):
                continue
            if low.endswith(exts) and fn.lower() != "entities.json" \
                    and os.path.join(case_dir, fn) not in outs:
                outs.append(os.path.join(case_dir, fn))
    return outs


def collect_figure_specs(case: dict):
    """收集图规格（规范形态见 references/OUTPUT_CONTRACT.md §6）。

    增量修正（P1，见 references/EVIDENCE.md 第一部分 · 故障矩阵「代码增量」）：
      ① 原写法 `isinstance(case.get("figures"), list) and case["figures"]` 在**显式给了
         空 figures 列表**时会静默落到末尾兜底分支，把"没有任何图"的案例当成"要画一张
         图"。改为"只要 figures 是列表就以它为准"，空列表即空列表。
      ② 末尾兜底分支原先无条件造 `{"type": "auto", "id": "fig", "title": <案例标题>}`；
         若案例连图规格都没有，失败记录只会报"不支持的图型：auto"，看不出真正原因。
         现在兜底规格仅用于"案例本身就是一张图的规格"这一种历史场景（案例里确实带
         图字段时），否则给出**指名道姓**的 error，让失败记录说明是"缺图规格"。
    两条都只改返回值内容，不改 CLI、不改退出码/status 语义。
    """
    if isinstance(case.get("figures"), list):
        return list(case["figures"])
    if case.get("figure") is not None:
        return [case["figure"]]
    if case.get("figure_spec") is not None:
        return [case["figure_spec"]]
    if case.get("figures") is not None and isinstance(case["figures"], dict):
        return [case["figures"]]
    fig_keys = ("type", "x", "y", "entities", "relations", "nodes", "matrix",
                "panels", "subfigures", "labels", "values", "presets", "id")
    if any(k in case for k in fig_keys):
        fb = {"id": case.get("case_id") or "fig"}
        fb.update({k: case[k] for k in fig_keys if k in case})
        if case.get("title"):
            fb["title"] = case["title"]
        return [fb]
    # 增量修正（P8）：案例**完全没有任何图规格**时返回**空列表**，不再造一张
    # "type=auto 的占位图"。原因：`type: "auto"` 在修正 P7 之后会真的走自动推断，
    # 于是这个占位图可能**凭空画出一张案例从未要求的图并报 completed** ——
    # 那是编造产物，比失败更糟。返回空列表后由 main() 记录 uncertainty 并给出
    # status=failed / exit 1（"没有任何图产出"正是 failed 的定义，退出码语义不变）。
    return []


def attach_source(case: dict, case_dir: str, data_files, spec: dict, index: int):
    if spec.get("data") is not None and isinstance(spec.get("data"), list):
        return spec
    ds = spec.get("data_files") or spec.get("data_file")
    if ds:
        if isinstance(ds, str):
            ds = [ds]
        files = []
        for d in ds:
            p = d if os.path.isabs(str(d)) else os.path.join(case_dir, str(d))
            files.append(p)
        spec = {**spec, "_data_files": [p for p in files if os.path.exists(p)]}
        if spec["_data_files"]:
            return spec
    if data_files:
        f = data_files[index % len(data_files)]
        spec = {**spec, "_data_files": [f]}
    return spec


def inject_panel_rows(spec: dict, case_dir: str, fallback_rows):
    t = str(spec.get("type") or "").lower()
    if t != "panel":
        return spec
    panels = spec.get("panels") or spec.get("subfigures") or []
    for s in panels:
        if not isinstance(s, dict):
            continue
        df = s.get("data_file") or s.get("data_files")
        if isinstance(df, str):
            p = df if os.path.isabs(df) else os.path.join(case_dir, df)
            if os.path.exists(p):
                _h, rws, _e = fe.load_table(p)
                s["_rows"] = rws
        elif df is None:
            s.setdefault("_rows", fallback_rows)
    return spec


# ---------------------------------------------------------------- 契约

_CONTRACT_ALIASES = {
    "editable_source": lambda res: list(res.get("editable_sources") or []),
    "editable_sources": lambda res: list(res.get("editable_sources") or []),
    "rendered_preview": lambda res: dict(res.get("renders") or {}),
    "renders": lambda res: dict(res.get("renders") or {}),
    "render_png": lambda res: (res.get("renders") or {}).get("png", []),
    "render_pdf": lambda res: (res.get("renders") or {}).get("pdf", []),
    "field_mapping": lambda res: "data_manifest.json",
    "data_mapping": lambda res: "data_manifest.json",
    "source_mapping": lambda res: "data_manifest.json",
    "data_manifest": lambda res: "data_manifest.json",
    "validation_report": lambda res: "validation.json",
    "validation": lambda res: "validation.json",
    "figcheck_report": lambda res: "figcheck_report.json",
    "mapcheck_report": lambda res: "mapcheck_report.json",
    "sources": lambda res: list(res.get("sources") or []),
    "evidence": lambda res: list(res.get("sources") or []),
    "uncertainty": lambda res: list(res.get("uncertainty") or []),
    "change_records": lambda res: list(res.get("change_records") or []),
    "status": lambda res: str(res.get("status") or ""),
    "outputs": lambda res: list(res.get("outputs") or []),
    "checkpoints": lambda res: dict(res.get("checkpoints") or {}),
    "gates": lambda res: dict(res.get("gates") or {}),
}


def apply_output_contract(contract, result: dict) -> dict:
    """把输出契约声明的字段全部落到 result.json 顶层（四形态；缺失按声明容器类型给默认值）。

    契约可为：
      * list[str]
      * dict[name -> 'string'|'array'|'object'|'number'|'boolean'|例值]
      * {"fields": [...] }  /  {"fields": {name: type}}
    已知别名映射到真实产物；其余缺失字段按声明容器类型给 ""/[]/{}/false/0 —— 绝不写 null。
    """
    fields = []
    types = {}
    if isinstance(contract, list):
        fields = [f for f in contract if isinstance(f, str)]
    elif isinstance(contract, dict):
        inner = contract.get("fields", contract)
        if isinstance(inner, list):
            fields = [f for f in inner if isinstance(f, str)]
        elif isinstance(inner, dict):
            fields = list(inner.keys())
            types = inner
    defaults = {
        "string": "", "text": "", "str": "",
        "array": [], "list": [],
        "object": {}, "dict": {},
        "number": 0, "float": 0, "int": 0,
        "boolean": False, "bool": False,
    }
    # 增量修正：先把"声明字段表"归一化为只含非空字符串，再交给下面的循环。
    # 缺陷：旧逻辑只在循环里 `continue` 跳过非法项，于是 `""`（空字符串）仍留在
    # fields 里进入循环；而 figcheck._contract_fields 是"只保留字符串"，`""` 算字符串
    # 因此**被 G2 当作一个必须存在的字段** → G2 必然报「缺失/为空 ['']」，把一份
    # 本来完整的契约判成失败（实测见 scripts/fault_inject.py 用例 K1）。
    # 两处对"契约字段表"的定义由此统一为同一条：非空字符串才算字段。
    fields = [f for f in fields if isinstance(f, str) and f]
    for f in fields:
        if not f or not isinstance(f, str):
            continue
        if f in _CONTRACT_ALIASES:
            try:
                result[f] = _CONTRACT_ALIASES[f](result)
            except Exception:
                pass
        if f not in result or result[f] is None:
            typ = types.get(f, "")
            if not isinstance(typ, str):
                typ = ""
            result[f] = defaults.get(typ, defaults.get(str(typ).lower(), ""))
    return result


# ---------------------------------------------------------------- 运行

def build_provenance(case: dict, task_path, data_files, case_dir):
    prov = {
        "generator": "scientific-figure-craft (efficiency-3 / challenge-1bd90d8a v2)",
        "engine": os.path.basename(__file__),
        "source_files": [],
        # 不写时间戳 —— 保证同输入同参数重复运行时 SVG 字节级稳定（D18）
        "method": "chartkit 手写 XML 分层 SVG + Pillow 同场景渲染 PNG/PDF；"
                  "每个图元携带 data-* 溯源属性；mapcheck/figcheck 双校验；"
                  "未使用网络、未调用统计推断。",
    }
    for f in data_files:
        try:
            prov["source_files"].append({"file": os.path.basename(f), "sha256": fe.sha256_file(f)})
        except Exception as exc:
            prov["source_files"].append({"file": os.path.basename(f), "sha256": f"unavailable ({exc})"})
    if task_path:
        prov["task_file"] = os.path.basename(task_path)
    if case.get("dataset_version") or case.get("data_version"):
        prov["data_version"] = case.get("dataset_version") or case.get("data_version")
    return prov


def _pil_version():
    try:
        from PIL import __version__
        return __version__
    except Exception:
        return "unknown"


def _write_json(path, obj):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def main(argv=None):
    ap = argparse.ArgumentParser(description="科研数据图生成与编辑 Skill 入口（v2）")
    ap.add_argument("--case", required=True, help="case.json 路径")
    ap.add_argument("--out", default="out", help="输出目录（默认 ./out）")
    ap.add_argument("--work", default=None, help="中间产物目录（提取/lint）")
    ap.add_argument("--task", default=None, help="显式 task.md 路径")
    ap.add_argument("--data", default=None, help="显式数据文件（; 分隔多个）")
    ap.add_argument("--style", default="default")
    ap.add_argument("--dpi", type=int, default=None, help="PNG 渲染分辨率（覆盖样式预设）")
    ap.add_argument("--note", default=None, help="追加一条人工变更记录")
    ap.add_argument("--lang", default="zh", choices=["zh", "en"])
    ap.add_argument("--no-pdf", action="store_true")
    args = ap.parse_args(argv)

    result = {}
    steps = []

    def step(msg):
        steps.append({"ts": fe.now_ts(), "action": msg})
        result.setdefault("steps", []).append({"ts": fe.now_ts(), "action": msg})

    try:
        case_path = os.path.abspath(args.case)
        case_dir = os.path.dirname(case_path)
        out_dir = os.path.abspath(args.out)
        work_dir = os.path.abspath(args.work) if args.work \
            else os.path.join(os.path.dirname(out_dir), "work")
        os.makedirs(out_dir, exist_ok=True)
        os.makedirs(work_dir, exist_ok=True)

        # ---------------- CP1 材料盘点 ----------------
        step("CP1 读取案例与盘点材料")
        case = load_case(case_path)
        case_id = str(case.get("case_id") or case.get("id") or case.get("caseId") or "case")
        result["case_id"] = case_id
        for k in ("title", "challenge_id", "dataset_version"):
            if case.get(k) is not None:
                result[k] = case.get(k)

        task_path = discover_task(case, case_dir, args.task)
        if task_path:
            step(f"发现任务说明 {task_path}")
            with open(task_path, "r", encoding="utf-8", errors="replace") as f:
                result["task_summary"] = "\n".join(f.read().splitlines()[:8])[:500]
        else:
            result.setdefault("uncertainty", []).append(
                "未找到 task.md（自动发现：task_file 字段 / 案例同目录）。请确认材料配套。")

        # case.json 的 manual_confirmations 原样带入（契约见 references/OUTPUT_CONTRACT.md），
        # 并作为人工确认条目并入 change_records（确定性：不做时间戳改写）。
        manual_conf = case.get("manual_confirmations")
        result["manual_confirmations"] = list(manual_conf) if isinstance(manual_conf, list) else []
        for _m in result["manual_confirmations"]:
            if isinstance(_m, dict):
                result.setdefault("change_records", []).append({
                    "ts": str(_m.get("ts") or ""),
                    "action": "manual_confirmation",
                    "detail": str(_m.get("what") or _m.get("detail") or ""),
                })

        data_files = discover_data_files(case, case_dir, args.data)
        declared_missing = []
        _decl = case.get("data_files") or case.get("sources") or []
        if isinstance(_decl, str):
            _decl = [_decl]
        for _f in _decl:
            if isinstance(_f, dict):
                _f = _f.get("file") or _f.get("path")
            if not _f:
                continue
            _p = _f if os.path.isabs(str(_f)) else os.path.join(case_dir, str(_f))
            if not os.path.exists(_p):
                declared_missing.append(str(_f))
        sources = []
        seen_sf = set()
        for f in data_files:
            try:
                sources.append({"file": os.path.basename(f), "sha256": fe.sha256_file(f),
                                "rows": None, "version": case.get("dataset_version")})
            except Exception as exc:
                sources.append({"file": os.path.basename(f), "sha256": None, "error": str(exc)})
        result.setdefault("sources", []).extend(sources)
        cp1 = {"ok": bool(task_path is not None) and bool(data_files),
               "task_found": bool(task_path),
               "data_files": [os.path.basename(f) for f in data_files],
               "declared_missing": declared_missing}
        if not data_files:
            msg = ("未发现任何可用源数据文件（data_files/显式 --data/案例同目录表格均缺失）。"
                   "无法生成数据图。")
            if declared_missing:
                msg += f" case.json 声明的文件不存在：{declared_missing}"
            result.setdefault("uncertainty", []).append(msg)
        result.setdefault("checkpoints", {})["cp1_material_survey"] = cp1

        # ---------------- CP2 抽取 ----------------
        step("CP2 源材料抽取（列画像 / 实体-关系）")
        try:
            extract_report = ext_mod.extract(case_path, data_paths=args.data,
                                             work_dir=work_dir,
                                             out_path=os.path.join(work_dir, "extract.json"))
            cext = {"ok": True, "tables": len(extract_report.get("tables", [])),
                    "networks": len(extract_report.get("networks", [])),
                    "uncertain": sum(len(n.get("uncertain", []))
                                     for n in extract_report.get("networks", [])),
                    "file": "extract.json"}
        except Exception as exc:
            cext = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
            result.setdefault("uncertainty", []).append("extract 阶段异常：" + str(exc))
        result.setdefault("checkpoints", {})["cp2_extract"] = cext

        # ---------------- CP3 spec lint ----------------
        step("CP3 figure spec lint（生成门）")
        specs = collect_figure_specs(case)
        # 增量修正（P3）：样式回退过去是**完全静默**的 —— templates/journal_styles.json
        # 缺失或 JSON 损坏时 load_style 直接给内置默认，未知的 --style 预设名同样静默
        # 退回 default，result.json 里一个字都不提（实测见 scripts/fault_inject.py 用例
        # T1/T2 与 T5）。参考 references/failure-modes.md 的 FM-X1，回退本身是对的，
        # 但**必须留痕**。这里只补 uncertainty（不影响样式值、菜单、退出码）。
        _presets = fe.load_journal_styles()
        if not os.path.exists(os.path.join(fe.skill_root(), "templates",
                                           "journal_styles.json")):
            result.setdefault("uncertainty", []).append(
                "templates/journal_styles.json 缺失：样式预设回退内置默认（FM-X1）。"
                "自定义期刊预设不可用，已按 default 出图。")
        elif not isinstance(_presets, dict) or set(_presets.keys()) <= {"default"}:
            result.setdefault("uncertainty", []).append(
                "templates/journal_styles.json 无法解析或只有 default 键：样式预设回退"
                "内置默认（FM-X1）。当前样式设置可能不是投稿目标期刊的真实预设。")
        if args.style and args.style != "default" and \
                not (isinstance(_presets, dict) and args.style in _presets):
            result.setdefault("uncertainty", []).append(
                f"--style {args.style!r} 不是已知预设（可用："
                f"{sorted(k for k in (_presets or {}) if not str(k).startswith('_'))}）："
                f"已回退 default。如需该期刊样式，请在 templates/journal_styles.json 增加同名键。")
        style = fe.load_style(args.style)
        if args.dpi:
            style["dpi"] = args.dpi
        style["dpi"] = int(style.get("dpi", 150))
        fonts = fe.new_fontmap()
        prov = build_provenance(case, task_path, data_files, case_dir)
        rows_map = {}
        try:
            rows_map = lint_mod.build_rows_map(case_path, case)
        except Exception:
            rows_map = {}
        lint_problems = []
        for spec in specs:
            if isinstance(spec, dict):
                lint_problems.extend(lint_mod.lint_spec(spec, case=case, rows_map=rows_map))
        lint_errs = [p for p in lint_problems if p["level"] == "error"]
        lint_warns = [p for p in lint_problems if p["level"] == "warn"]
        for w in lint_warns:
            result.setdefault("warnings_collected", []).append(
                f"spec_lint {w['code']} {w['figure_id']}: {w['message']}")
        result["spec_lint"] = {"valid": not lint_errs,
                               "errors": [p["message"] for p in lint_errs],
                               "warnings": [p["message"] for p in lint_warns],
                               "counts": {"figures": len(specs), "errors": len(lint_errs),
                                          "warnings": len(lint_warns)}}
        _write_json(os.path.join(work_dir, "spec_lint.json"), result["spec_lint"])
        result.setdefault("checkpoints", {})["cp3_spec_lint"] = {
            "ok": not lint_errs, "figures": len(specs),
            "errors": len(lint_errs), "warnings": len(lint_warns)}

        font_report = fonts.report()
        result.setdefault("environment", {}).update({
            "python": sys.version.split()[0],
            "pillow": _pil_version() if fe.HAS_PIL else None,
            "fonts": font_report,
            "dpi": style.get("dpi"),
            "no_network": True,
            "cwd": None,
            "style": args.style,
        })

        # ---------------- CP4 导出 ----------------
        # 增量修正（P8 配套）：图规格为空时**如实说明**，不静默（实测见
        # scripts/fault_inject.py 用例 I6）。
        if not specs:
            result.setdefault("uncertainty", []).append(
                "案例未提供任何图规格（figures / figure / figure_spec 均缺）："
                "没有可执行的图规格，按 failed 处理，不臆造图稿。")
            step("未发现任何图规格：跳过 CP4 生成。")
        ctx = {"style": style, "fonts": fonts, "with_preview": not args.no_pdf,
               "width": None, "height": None}
        completed, failed, outputs = [], [], []
        manifest_figures = {}
        figure_checks = {}
        figure_meta = {}
        for fi, spec in enumerate(specs):
            fig_id = str(spec.get("id") or f"fig-{fi + 1:02d}")
            # 增量修正（P2）：把图规格自带的 error 说明带进失败记录。缺图规格时
            # 规格里已经写明原因，但失败记录只抄了渲染层那句"不支持的图型：auto"，
            # 真正原因被丢掉（实测见 scripts/fault_inject.py 用例 I6）。
            spec_detail = spec.get("error") if isinstance(spec, dict) else None
            try:
                step(f"CP4 构建图 {fig_id}（type={spec.get('type') or 'auto'}）")
                if str(spec.get("type") or "").lower() == "network" and spec.get("entities_file"):
                    ef = spec["entities_file"]
                    p = ef if os.path.isabs(str(ef)) else os.path.join(case_dir, str(ef))
                    if os.path.exists(p):
                        with open(p, "r", encoding="utf-8-sig") as f:
                            obj = json.load(f)
                        if isinstance(obj, dict) and "nodes" in obj:
                            spec = {**spec, "entities": list(obj.get("nodes", [])),
                                    "relations": list(obj.get("relations", []))}
                        else:
                            spec = {**spec, "entities": obj}
                        sources.append({"file": os.path.basename(p),
                                        "sha256": fe.sha256_file(p), "role": "entities_file"})
                    else:
                        raise fe.SpecError(f"network entities_file 不存在：{p}")
                elif str(spec.get("type") or "").lower() == "network" and spec.get("material_file"):
                    # 增量修正（P5，由案例集探针暴露）：SKILL.md S2 写明材料文本支持
                    # `ENTITY: <id> | <label> | <group> | <cite>` 与
                    # `REL: <from> -> <to> | <label> | <type>` 两种显式行，extract.py 也已
                    # 实现（scan_material_text），但**生成路径过去只认 entities_file(JSON)**，
                    # 于是"只给 material_file 的机制图"一律以
                    # "通路图需要 entities（节点）列表。" 失败。
                    # 这里把 extract.py 的既有解析器接到生成路径上：纯增量（新增分支，
                    # 原 entities_file / spec.entities 两个分支行为一字未改）。
                    mf = spec["material_file"]
                    p = mf if os.path.isabs(str(mf)) else os.path.join(case_dir, str(mf))
                    if os.path.exists(p):
                        _ents, _rels, _unc = ext_mod.scan_material_text(
                            p, ext_mod._load_glossary())
                        spec = {**spec, "entities": list(_ents), "relations": list(_rels)}
                        sources.append({"file": os.path.basename(p),
                                        "sha256": fe.sha256_file(p), "role": "material_file"})
                        if _unc:
                            result.setdefault("uncertainty", []).append(
                                f"{os.path.basename(p)}：词表扫描命中 {len(_unc)} 个候选实体"
                                f"（{', '.join(str(u.get('candidate_id')) for u in _unc[:6])}"
                                f"{'…' if len(_unc) > 6 else ''}），未经对照原文确认，未上图（D4）。")
                        if not _ents:
                            result.setdefault("uncertainty", []).append(
                                f"{os.path.basename(p)} 中未找到显式 ENTITY: 行；机制图可能为空。")
                    else:
                        raise fe.SpecError(f"network material_file 不存在：{p}")
                spec = attach_source(case, case_dir, data_files, spec, fi)
                spec = inject_panel_rows(spec, case_dir, None)
                is_net = str(spec.get("type") or "").lower() == "network"
                data_files_eff = ([] if (is_net and (spec.get("entities") or spec.get("relations")))
                                  else (spec.get("_data_files") or data_files))
                rows = []
                for df in data_files_eff:
                    headers, rws, _e = fe.load_table(df)
                    rows.extend(rws)
                    for s in sources:
                        if s["file"] == os.path.basename(df):
                            s["rows"] = len(rws)
                            s["columns"] = headers
                if not rows and not is_net:
                    raise fe.SpecError(f"图 {fig_id}：源数据为空。")
                if str(spec.get("type") or "").lower() == "panel":
                    for s in (spec.get("panels") or spec.get("subfigures") or []):
                        if isinstance(s, dict) and "_rows" not in s:
                            s["_rows"] = rows
                prefix = os.path.join(out_dir, f"figure-{fig_id}")
                fprov = {**prov, "figure_id": fig_id,
                         "data_files": [os.path.basename(f) for f in data_files_eff]}
                fig_result = fe.export_figure(spec, rows, ctx, prefix, provenance=fprov)
                completed.append(fig_result["figure_id"])
                outputs.append({"kind": "editable_svg", "file": fig_result["files"]["editable_svg"],
                                "figure_id": fig_id})
                if fig_result["files"]["png_preview"]:
                    outputs.append({"kind": "png_preview", "file": fig_result["files"]["png_preview"],
                                    "figure_id": fig_id})
                if fig_result["files"]["pdf_preview"]:
                    outputs.append({"kind": "pdf_preview", "file": fig_result["files"]["pdf_preview"],
                                    "figure_id": fig_id})
                figure_checks[fig_id] = fig_result["checks"]
                figure_meta[fig_id] = fig_result["meta"]
                manifest_figures[fig_id] = {
                    "type": fig_result["type"], "title": fig_result["title"],
                    "width": spec.get("width"), "height": spec.get("height"),
                    "style": args.style,
                    "elements": fig_result["elements"]}
                result.setdefault("warnings_collected", []).extend(
                    fig_result["meta"].get("warnings", []))
                result.setdefault("adjustments_collected", []).extend(
                    fig_result["meta"].get("adjustments", []))
            except fe.SpecError as exc:
                detail = str(exc) + (f"（{spec_detail}）" if spec_detail else "")
                failed.append({"figure_id": fig_id, "error": detail})
                step(f"图 {fig_id} 失败（SpecError）：{detail}")
            except Exception as exc:
                detail = f"{type(exc).__name__}: {exc}" + (f"（{spec_detail}）" if spec_detail else "")
                failed.append({"figure_id": fig_id, "error": detail})
                step(f"图 {fig_id} 失败：{detail}")
                if os.environ.get("MAIN_DEBUG"):
                    traceback.print_exc()

        seen_src = set()
        unique_sources = []
        for s in sources:
            key = (s.get("file"), s.get("sha256"))
            if key not in seen_src:
                seen_src.add(key)
                unique_sources.append(s)
        sources = unique_sources
        result["sources"] = sources
        result["completed_figures"] = completed
        if failed:
            result["failed_figures"] = failed
            result.setdefault("uncertainty", []).append(
                f"以下图未能生成：{json.dumps(failed, ensure_ascii=False)}")
        result["outputs"] = outputs
        result["editable_sources"] = [o["file"] for o in outputs if o["kind"] == "editable_svg"]
        result["renders"] = {"png": [o["file"] for o in outputs if o["kind"] == "png_preview"],
                             "pdf": [o["file"] for o in outputs if o["kind"] == "pdf_preview"]}
        result["figure_checks"] = figure_checks
        result["figure_meta"] = figure_meta

        # ---------------- 状态初判 ----------------
        figure_fail = any(c.get("level") == "fail"
                          for cs in figure_checks.values() for c in cs)
        lint_blocked = bool(lint_errs)
        if completed and not failed and not figure_fail and not lint_blocked:
            result["status"] = "completed"
        elif completed:
            result["status"] = "partial"
        elif failed:
            # 材料/数据问题（缺文件、缺列、filter 无匹配等）→ partial：可复验（D10）
            result["status"] = "partial"
        elif not data_files:
            result["status"] = "partial"
        else:
            result["status"] = "failed"
        result["checkpoints"]["cp4_export"] = {"completed": completed, "failed": failed}
        result["checkpoints"]["cp6_contract"] = {}
        result.setdefault("uncertainty", []).extend(
            [w for w in result.get("warnings_collected", [])
             if w not in result["uncertainty"]])
        if args.note:
            result.setdefault("change_records", []).append(
                {"ts": fe.now_ts(), "action": "manual", "detail": args.note})
        result["change_records"] = result.get("change_records", []) + steps

        # ---------------- 写基础产物（manifest / validation） ----------------
        _write_json(os.path.join(out_dir, "data_manifest.json"), {
            "case_id": case_id,
            "sources": sources,
            "figures": manifest_figures,
            "version": 2,
            "note": "图元→源数据映射（文件/列/行/值）；SVG 内同名 data-* 属性可反向定位；"
                    "value 由 mapcheck 与源表逐行核对。",
        })
        _write_json(os.path.join(out_dir, "validation.json"), {
            "case_id": case_id,
            "status": result["status"],
            "checks": figure_checks,
            "adjustments": result.get("adjustments_collected", []),
            "warnings": result.get("warnings_collected", []),
        })

        # ---------------- CP5 双校验 + CP6 契约 ----------------
        step("CP5 校验（mapcheck + figcheck + 确定性）")
        mapcheck_report = map_mod.mapcheck(out_dir, case_path)
        _write_json(os.path.join(out_dir, "mapcheck_report.json"), mapcheck_report)
        result["checkpoints"]["cp5_mapcheck"] = {
            "ok": mapcheck_report["all_pass"], **mapcheck_report["summary"]}

        try:
            result["artifacts_sha256"] = rerun_mod.record_shas(out_dir)
        except Exception as exc:
            result["artifacts_sha256"] = {"error": str(exc)}

        contract = case.get("output_contract")
        # 增量修正（P4）：旧写法只看 `if contract:` 就置 output_contract_applied=True。
        # 若契约是四形态之外的形态（例如一个裸字符串），apply_output_contract 什么都不做，
        # 却仍然对外报"契约已应用" —— 这是**谎报**（实测见 scripts/fault_inject.py 用例 K6）。
        # 现在只有 dict / list 两种可解释形态才算"应用"；其余如实置 false 并记 uncertainty。
        if isinstance(contract, (dict, list)) and contract:
            apply_output_contract(contract, result)
            result["output_contract_applied"] = True
        elif contract:
            result["output_contract_applied"] = False
            result.setdefault("uncertainty", []).append(
                f"output_contract 形态无法解释（{type(contract).__name__}），未回显任何契约"
                f"字段；已如实置 output_contract_applied=false（OUTPUT_CONTRACT.md §2 的"
                f"四形态：列表 / 名称→类型 / 嵌套 fields 列表 / 嵌套 fields 映射）。")
        else:
            result.setdefault("output_contract_applied", False)

        result["mapcheck_report"] = "mapcheck_report.json"
        result["figcheck_report"] = "figcheck_report.json"

        # 两轮 figcheck：先写临时 result.json 审计出 gates，写入最终 result.json 后
        # 再复核一次，保证最终字节上的 gates 自洽（G8 闭合）。
        gates = {}
        for _round in (1, 2):
            _write_json(os.path.join(out_dir, "result.json"), result)
            fig_report = fig_mod.figcheck(out_dir, case_path)
            _write_json(os.path.join(out_dir, "figcheck_report.json"), fig_report)
            gates = dict(fig_report.get("gates") or {})
            gates["all_pass"] = all(v for k, v in gates.items() if k != "all_pass")
            result["gates"] = dict(gates)
            result["checkpoints"]["cp5_figcheck"] = {
                "gates": gates["all_pass"],
                "six_checkpoints": {k: v["covered"] for k, v in
                                    (fig_report.get("six_checkpoints") or {}).items()}}
            result["checkpoints"]["cp6_contract"] = {
                "applied": result["output_contract_applied"],
                "gates_all_pass": gates["all_pass"]}
            # G8 自洽性：completed 但 gates 未全过 → 降级 partial + 如实说明
            if result["status"] == "completed" and not gates["all_pass"]:
                result["status"] = "partial"
                result.setdefault("uncertainty", []).append(
                    "figcheck G 门未全过，status 降级为 partial 以保持诚实（G8）。")
            # 清理瞬态收集字段后写出最终 result.json
            for _k in ("manifest_figures", "warnings_collected", "adjustments_collected", "_pipeline"):
                result.pop(_k, None)
            _write_json(os.path.join(out_dir, "result.json"), result)

        print(f"[main] case_id={case_id} status={result['status']} figures={completed} "
              f"failed={[x['figure_id'] for x in failed]}")
        print(f"[main] outputs -> {out_dir}")
        for o in outputs:
            print(f"  - {o['file']} ({o['kind']})")
        gg = " ".join(f"{k}={'OK' if v else 'X'}" for k, v in sorted(gates.items()))
        print(f"[main] gates: {gg}")
        print(f"[main] 中间产物 -> {work_dir}")
        sys.exit(0 if (result["status"] == "completed" and gates.get("all_pass", True))
                else (0 if result["status"] == "completed" else
                      (2 if result["status"] == "partial" else 1)))
    except Exception as exc:
        msg = f"{type(exc).__name__}: {exc}"
        try:
            _write_json(os.path.join(os.path.abspath(args.out), "result.json"), {
                "case_id": result.get("case_id", "unknown"),
                "status": "failed", "error": msg,
                "uncertainty": ["运行异常，产物不完整。",
                                "traceback: " + traceback.format_exc(limit=4)],
                "sources": [], "change_records": []})
        except Exception:
            pass
        print(f"[main] FATAL {msg}", file=sys.stderr)
        if os.environ.get("MAIN_DEBUG"):
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()