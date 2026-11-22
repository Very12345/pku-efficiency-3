#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""preflight.py — 运行前闸门（把「静默失败」提前变成「响亮的告警」）。

`scripts/fault_inject.py` 的演练证明了一件事：本流水线的**算法**很稳，
不稳定的地方在**入口的宽容**——`--rules` 写错路径、`--material` 指到不存在的文件、
`templates/palette.json` 被删，`main.py` 都会安静地"用默认值继续跑"，
产物看起来完全正常（退出码 0、`status=success`、`uncertainty` 空）。
这对一次演示是优点，对**评测**是风险：你不知道自己交上去的图是用哪套规则审的。

本脚本是那道缺失的闸门：**在跑 main.py 之前**，把同一批输入按四类形态
（输入 / 结构 / 资产 / 依赖）检一遍，把每个问题变成一条带 `code`/`scope`/`action`
的 finding，并按严重级给出退出码。它**不修改任何输入、不写产物、不调用算法**，
因此可以安全地在正式运行前无脑跑一次。

与包内既有脚本的关系：
- `main.py` —— 真正干活；本脚本**不替代**它，也不改变它的退出码语义；
- `check.py` —— 交付后验（G1–G10）；本脚本是**交付前验**，两者互补：
  preflight 管"进去的东西对不对"，check 管"出来的东西全不全"。

用法:
    python "$SKILL_DIR/scripts/preflight.py" --case /input/case.json [--task /input/task.md]
                                            [--material <材料|目录>] [--merge <override.json>]
                                            [--rules <rules.json>] [--palette <palette.json>]
                                            [--deps] [--json <report.json>] [--strict]

退出码:
    0 = 无 finding（可继续）
    1 = 只有 warn 级 finding（可继续，但已告警；--strict 时升级为 3）
    2 = 命令行用法错误（缺 --case 等）
    3 = 有 error 级 finding（建议先修再跑，别把缺陷带进产物）

设计约束：只用标准库；自定位；不写任何文件（除非显式 `--json`）；不 import 包内算法模块
（只读 `assets/`、`templates/` 的数据文件），因此 preflight 自身不会被算法 bug 影响。
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.dont_write_bytecode = True  # 包内不落 .pyc

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(HERE)
BUILTIN_RULES = os.path.join(SKILL_ROOT, "assets", "connection_rules.json")
BUILTIN_PALETTE = os.path.join(SKILL_ROOT, "templates", "palette.json")

# 与 references/vocabulary.md 一致（只做"是否在词表内"这一件事，不复制算法）
KINDS = {"step", "phase", "device", "material", "product",
         "data", "decision", "milestone", "waste", "container"}
REL_KINDS = {"flow", "connect", "depend", "recycle", "sequence", "causation"}
MATERIAL_EXT = (".md", ".txt", ".csv", ".tex")


# ------------------------------------------------------------------ finding 构造

def _f(level: str, code: str, scope: str, detail: str, action: str) -> dict:
    return {"level": level, "code": code, "scope": scope, "detail": detail, "action": action}


def _load_json(path: str):
    """返回 (对象, 错误字符串)。错误字符串非空即失败；不抛异常。"""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh), ""
    except FileNotFoundError:
        return None, "文件不存在"
    except UnicodeDecodeError as exc:
        return None, f"不是 UTF-8：{exc}"
    except json.JSONDecodeError as exc:
        return None, f"JSON 语法错误：第 {exc.lineno} 行第 {exc.colno} 列（{exc.msg}）"
    except OSError as exc:
        return None, f"读取失败：{exc}"


# ------------------------------------------------------------------ 四类检查

def check_inputs(args) -> list:
    """输入形态：case/task/material/merge 是否存在、是否可解析。"""
    out = []

    case_path, is_dir = args.case, os.path.isdir(args.case)
    if is_dir:
        cand = os.path.join(args.case, "case.json")
        if os.path.isfile(cand):
            case_path = cand
        else:
            out.append(_f("error", "case-json-missing", "input",
                          f"--case 给的是目录，但目录下没有 case.json：{os.path.basename(args.case)}",
                          "把 case.json 放进该目录，或 --case 直接给文件"))
            return out

    if not os.path.isfile(case_path):
        out.append(_f("error", "case-missing", "input",
                      f"case 文件不存在：{os.path.basename(case_path)}",
                      "核对 --case 路径（main.py 此处会以退出码 2 失败）"))
        return out

    data, err = _load_json(case_path)
    if err:
        out.append(_f("error", "case-unparsable", "input",
                      f"case 文件不可解析（{err}）",
                      "修好 JSON；main.py 此处会兜底写 status=failed 并以退出码 1 结束"))
        return out
    if not isinstance(data, dict):
        out.append(_f("error", "case-not-object", "input",
                      f"case 顶层是 {type(data).__name__}，不是对象",
                      "顶层必须是 JSON 对象；数组/字符串无法取 case_id"))
        return out

    ents = data.get("entities") or data.get("entity_list") or data.get("nodes") \
        or data.get("步骤") or data.get("stages")
    txt = data.get("text") or data.get("materials_text") or data.get("材料") or ""
    if not ents and not txt:
        out.append(_f("error", "case-empty-shell", "input",
                      "case 里既无 entities 也无 text/material 文本（空壳输入）",
                      "补结构化实体或材料文本；否则产物只有空画布"))
    if not data.get("case_id") and not data.get("id"):
        out.append(_f("warn", "case-id-derived", "input",
                      "case 未给 case_id，将回落到文件名（产物子目录名会随文件名变化）",
                      "显式给 case_id，便于跨平台对拍输出目录"))
    if not data.get("canvas"):
        out.append(_f("warn", "canvas-defaulted", "input",
                      "case 未给 canvas，将用默认 297×180 mm",
                      "需要特定画布尺寸时显式给 canvas.width_mm/height_mm"))
    if data.get("figure_type") and str(data["figure_type"]) not in ("route", "apparatus",
                                                                   "flow", "hybrid"):
        out.append(_f("error", "figure-type-invalid", "input",
                      f"figure_type={data['figure_type']!r} 不在 route|apparatus|flow|hybrid 内",
                      "改成合法图类，或用 --figure-type 覆盖"))

    # task.md：显式给了却读不到 = 静默缺口
    if args.task:
        if not os.path.isfile(args.task):
            out.append(_f("warn", "task-missing", "input",
                          "显式给的 --task 不存在（main.py 会安静地不读任务书，产物无任何标记）",
                          "核对路径；或用 --case 给目录让 it 自动取同目录 task.md"))
        else:
            try:
                open(args.task, "r", encoding="utf-8").read(4096)
            except Exception as exc:  # noqa: BLE001
                out.append(_f("warn", "task-unreadable", "input",
                              f"--task 存在但读不出来：{type(exc).__name__}",
                              "确认编码为 UTF-8"))

    # material：被引用却读不到 = 证据条数会悄悄变少
    for m in (args.material or []):
        if os.path.isdir(m):
            hits = []
            for root, _d, files in os.walk(m):
                hits += [f for f in files if f.lower().endswith(MATERIAL_EXT)]
            if not hits:
                out.append(_f("warn", "material-dir-empty", "input",
                              f"--material 目录里没有可读材料（{'/'.join(MATERIAL_EXT)}）："
                              f"{os.path.basename(m)}",
                              "确认材料确实放在该目录；空目录会让证据条数变少而不报错"))
        elif not os.path.isfile(m):
            out.append(_f("warn", "material-missing", "input",
                          f"--material 指向的文件不存在：{os.path.basename(m)}",
                          "核对路径（main.py 会静默跳过并少记一条 source）"))

    # merge：人工修正入口给错 = 修正根本没生效
    if args.merge:
        if not os.path.isfile(args.merge):
            out.append(_f("error", "merge-missing", "input",
                          "显式给的 --merge 不存在（修正输入缺失，main.py 会以退出码 1 失败）",
                          "核对路径；若要「只跑不合并」就别传 --merge"))
        else:
            mv, merr = _load_json(args.merge)
            if merr:
                out.append(_f("error", "merge-unparsable", "input",
                              f"--merge 不可解析（{merr}）", "修好 JSON 再跑"))
            elif not isinstance(mv, dict):
                out.append(_f("error", "merge-not-object", "input",
                              "--merge 顶层不是对象", "应为 {\"entities\":[…],\"relations\":[…]}"))
            else:
                for r in (mv.get("relations") or []):
                    if not isinstance(r, dict) or "from" not in r or "to" not in r:
                        out.append(_f("error", "merge-relation-fields", "input",
                                      "--merge 里有关系缺少 from/to",
                                      "补齐端点；缺端点的关系会被丢弃并可能造出孤儿实体"))
    return out


def check_structure(case_path: str) -> list:
    """结构形态：端点、重复 id、词表外类别（这三类会让门禁误判或静默归一化）。"""
    out = []
    if not case_path or not os.path.isfile(case_path):
        return out
    data, err = _load_json(case_path)
    if err or not isinstance(data, dict):
        return out

    ents = data.get("entities") or data.get("entity_list") or data.get("nodes") \
        or data.get("步骤") or data.get("stages") or []
    rels = data.get("relations") or data.get("links") or data.get("edges") \
        or data.get("连接") or data.get("flows") or []
    if not isinstance(ents, list):
        ents = []
    if not isinstance(rels, list):
        rels = []

    ids = []
    for e in ents:
        if isinstance(e, dict) and e.get("id") is not None:
            ids.append(str(e.get("id")))
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        out.append(_f("warn", "entity-id-duplicate", "structure",
                      f"实体 id 重复：{dup[:6]}（会被重命名，且改名后的实体常常变成孤儿）",
                      "改成唯一 id；重复通常意味着材料里同类部件没区分开"))

    id_set = set(ids)
    dangling = []
    for r in rels:
        if not isinstance(r, dict):
            continue
        fr, to = str(r.get("from")), str(r.get("to"))
        if fr not in id_set or to not in id_set:
            dangling.append(f"{r.get('id')}({fr}->{to})")
        if fr == to and fr:
            out.append(_f("error", "relation-self-loop", "structure",
                          f"关系 {r.get('id')} 两端是同一实体（{fr}）",
                          "自环通常来自解析错误；audit 会判 error 级违规并降级"))
    if dangling:
        out.append(_f("warn", "relation-dangling", "structure",
                      f"{len(dangling)} 条关系端点不存在：{dangling[:4]}（会被静默丢弃，"
                      f"只在 verify.checks.no_dangling 留痕）",
                      "修端点，或确认材料本身就没有这个连接"))

    bad_kind = sorted({str(e.get("kind")) for e in ents
                       if isinstance(e, dict) and e.get("kind") and str(e.get("kind")) not in KINDS})
    if bad_kind:
        out.append(_f("warn", "kind-out-of-vocabulary", "structure",
                      f"实体类别不在词表内：{bad_kind[:6]}（会被容错归一化为 step，原始值不留痕）",
                      "对照 references/vocabulary.md 换成合法类别，否则图例映射会失真"))
    bad_rel = sorted({str(r.get("kind")) for r in rels
                      if isinstance(r, dict) and r.get("kind")
                      and str(r.get("kind")) not in REL_KINDS})
    if bad_rel:
        out.append(_f("warn", "relation-kind-out-of-vocabulary", "structure",
                      f"关系类别不在词表内：{bad_rel[:6]}（会被归一化为 flow，原始值不留痕）",
                      "对照 vocabulary.md 换成合法关系类别"))
    return out


def check_assets(args) -> list:
    """资产形态：规则资产与配色模板——这两样缺失时审计会**空转**，最容易假绿。"""
    out = []

    rules_path = args.rules or BUILTIN_RULES
    src = "自定义 --rules" if args.rules else "内置 assets/connection_rules.json"
    if not os.path.isfile(rules_path):
        out.append(_f("error" if args.rules else "warn", "rules-missing", "asset",
                      f"{src} 不存在 ⇒ 连接语义审计会整体空转（退出码仍 0、verify 仍可能全绿）",
                      "核对路径；不要在不清楚规则集的情况下交付"))
    else:
        rules, rerr = _load_json(rules_path)
        if rerr:
            out.append(_f("error", "rules-unparsable", "asset",
                          f"{src} 不可解析（{rerr}）⇒ 审计按「无规则」通过",
                          "修好 JSON；这是最容易「看起来全绿却没审」的一种"))
        elif not isinstance(rules, dict) or not rules:
            out.append(_f("warn", "rules-empty", "asset",
                          f"{src} 是空对象 ⇒ 审计无规则可依（C2 对照条件的构造方式）",
                          "正式交付必须用非空规则集"))
        else:
            rl = rules.get("rules") or []
            if not rl:
                out.append(_f("warn", "rules-no-rule-body", "asset",
                              f"{src} 没有 rules[] 规则体",
                              "补规则体，否则只有词表检查"))
            if not (rules.get("allowed_kinds") or []):
                out.append(_f("warn", "rules-no-kinds", "asset",
                              f"{src} 的 allowed_kinds 为空", "补类别词表"))
            if not (rules.get("allowed_relation_kinds") or []):
                out.append(_f("warn", "rules-no-rel-kinds", "asset",
                              f"{src} 的 allowed_relation_kinds 为空", "补关系词表"))
            sev = [r.get("severity") for r in rl if isinstance(r, dict)]
            if sev and not any(s == "error" for s in sev):
                out.append(_f("warn", "rules-no-error-severity", "asset",
                              f"{src} 里没有任何 error 级规则 ⇒ 违规永远不会降级",
                              "至少保留一条 error 级规则，否则 status 失去区分度"))

    palette_path = args.palette or BUILTIN_PALETTE
    psrc = "自定义 --palette" if args.palette else "内置 templates/palette.json"
    if not os.path.isfile(palette_path):
        out.append(_f("error" if args.palette else "warn", "palette-missing", "asset",
                      f"{psrc} 不存在 ⇒ 静默回落到代码内默认配色（产物无任何标记）",
                      "核对路径；配色会参与布局输入，换配色会改变 spec_sha16"))
    else:
        pal, perr = _load_json(palette_path)
        if perr:
            out.append(_f("error", "palette-unparsable", "asset",
                          f"{psrc} 不可解析（{perr}）⇒ 静默回落默认配色",
                          "修好 JSON"))
        elif not isinstance(pal, dict):
            out.append(_f("warn", "palette-not-object", "asset",
                          f"{psrc} 顶层不是对象", "应为 {kind: {fill, stroke, shape}} 映射"))
    return out


def check_deps() -> list:
    """依赖形态：PNG 要 Pillow，PDF 要 reportlab，PNG 中文要 TTF 字体。"""
    out = []
    try:
        import PIL  # noqa: F401
    except Exception as exc:  # noqa: BLE001
        out.append(_f("warn", "dep-pillow-missing", "dependency",
                      f"Pillow 不可用（{type(exc).__name__}）⇒ 无 figure.png，status 会降为 partial",
                      "pip install pillow；或接受降级（SVG/PDF 不受影响）"))
    try:
        import reportlab  # noqa: F401
    except Exception as exc:  # noqa: BLE001
        out.append(_f("warn", "dep-reportlab-missing", "dependency",
                      f"reportlab 不可用（{type(exc).__name__}）⇒ 无 figure.pdf，status 会降为 partial",
                      "pip install reportlab；或接受降级"))
    # 字体探测：与 scripts/fonts.py 的候选表同源，但这里只做"有没有"的只读判断
    win = (os.environ.get("WINDIR") or "C:/Windows").replace("\\", "/").rstrip("/")
    cands = [f"{win}/Fonts/msyh.ttc", f"{win}/Fonts/msyh.ttf", f"{win}/Fonts/simhei.ttf",
             f"{win}/Fonts/simsun.ttc", "/System/Library/Fonts/PingFang.ttc",
             "/System/Library/Fonts/STHeiti Light.ttc",
             "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
             "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
             "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc"]
    if not any(os.path.isfile(p) for p in cands):
        out.append(_f("warn", "dep-cjk-font-missing", "dependency",
                      "未找到中文字体 ⇒ PNG 预览可能把中文画成空框（SVG/PDF 不受影响）",
                      "安装任一候选 CJK 字体；或接受 uncertainty[scope=fonts] 的记录"))
    return out


# ------------------------------------------------------------------ 主流程

def run(args) -> dict:
    case_path = args.case
    if os.path.isdir(case_path):
        cand = os.path.join(case_path, "case.json")
        if os.path.isfile(cand):
            case_path = cand

    findings = []
    findings += check_inputs(args)
    findings += check_structure(case_path)
    findings += check_assets(args)
    if args.deps:
        findings += check_deps()

    errors = [f for f in findings if f["level"] == "error"]
    warns = [f for f in findings if f["level"] == "warn"]
    if errors:
        rc = 3
    elif warns:
        rc = 1 if not args.strict else 3
    else:
        rc = 0
    return {
        "_doc": ("运行前闸门报告：四类形态（输入/结构/资产/依赖）逐项检查结果。"
                 "本脚本不运行算法、不写产物；退出码 0=干净 / 1=仅 warn / 3=有 error / 2=用法错误。"),
        "skill_root": "<SKILL_DIR>",
        "case": os.path.basename(case_path) if case_path else None,
        "deps_checked": bool(args.deps),
        "ok": not errors and not warns,
        "exit": rc,
        "counts": {"error": len(errors), "warn": len(warns), "total": len(findings)},
        "checks": {
            "input": [f for f in findings if f["scope"] == "input"],
            "structure": [f for f in findings if f["scope"] == "structure"],
            "asset": [f for f in findings if f["scope"] == "asset"],
            "dependency": [f for f in findings if f["scope"] == "dependency"],
        },
        "findings": findings,
    }


def _print_human(rep: dict) -> None:
    print(f"preflight · case={rep['case']} · 依赖检查={'开' if rep['deps_checked'] else '关'}")
    if not rep["findings"]:
        print("  ✅ 无 finding：输入/结构/资产/依赖四类检查全过，可以跑 main.py")
        return
    for f in rep["findings"]:
        tag = "❌ error" if f["level"] == "error" else "⚠ warn "
        print(f"  {tag}  [{f['scope']}/{f['code']}] {f['detail']}")
        print(f"           → {f['action']}")
    print(f"  合计 {rep['counts']['error']} error / {rep['counts']['warn']} warn · "
          f"退出码 {rep['exit']}"
          f"{'（仅 warn：可继续，但已知有静默风险项）' if rep['exit'] == 1 else ''}")


def main(argv) -> int:
    ap = argparse.ArgumentParser(description="运行前闸门：输入/结构/资产/依赖四类检查")
    ap.add_argument("--case", default=None,
                    help="case.json 或案例目录（与 main.py 同一套解析规则）")
    ap.add_argument("--task", default=None, help="task.md 路径（可选）")
    ap.add_argument("--material", action="append", default=None,
                    help="材料文件/目录（可多次，与 main.py 同名同义）")
    ap.add_argument("--merge", default=None, help="--merge 覆盖文件（可选）")
    ap.add_argument("--rules", default=None, help="自定义 connection_rules.json（可选）")
    ap.add_argument("--palette", default=None, help="自定义 palette.json（可选）")
    ap.add_argument("--deps", action="store_true", help="同时检查 Pillow/reportlab/中文字体")
    ap.add_argument("--strict", action="store_true", help="把 warn 也当作阻断（退出码 3）")
    ap.add_argument("--json", default=None, help="把报告写到该路径（默认只打印）")
    args = ap.parse_args(argv)
    if not args.case:
        print("usage: python scripts/preflight.py --case <case.json|目录> [--task …] "
              "[--material …] [--merge …] [--rules …] [--palette …] [--deps] [--strict]",
              file=sys.stderr)
        return 2

    rep = run(args)
    _print_human(rep)
    if args.json:
        with open(os.path.abspath(args.json), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(rep, fh, ensure_ascii=False, indent=2)
        print(f"  报告已写入: {os.path.basename(args.json)}")
    return rep["exit"]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
