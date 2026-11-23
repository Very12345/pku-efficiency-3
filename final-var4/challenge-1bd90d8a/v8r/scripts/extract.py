#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract.py — 源材料抽取（CP2 字段映射 / 实体-关系抽取）

职责（对应工作流字段映射链 workorder-field-map.md）：
1. 表格文件（CSV/TSV/JSON）：逐列画像 —— {列名, 语义提示(time/error/n/分类/数值),
   单位推断（从列名括号提取，如 "time (h)" → h）, 数值范围, 空值占比, 样例值}。
2. 网络/机制图材料：
   a. 结构化 JSON（nodes/relations 数组或 {nodes, relations}）→ 直接解析，
      逐个实体/关系标注来源文件；
   b. 边表（含 from/to 列的数据文件）→ 从行构建节点与关系；
   c. 纯本文材料（material file）：支持两种显式行语法（文档化的约定）：
      - `ENTITY: <id> | <label> | <group> | <cite>`  → 实体
      - `REL: <from> -> <to> | <label> | <type>`      → 关系
      其余自然语言段落**不猜测实体**（诚实原则）：只按 templates/entity_glossary.json
      的 entity_glossary 词表做候选扫描并标记 uncertain=true，由 Agent 复核后
      才可上图（D4/D14）。
3. 输出 <work>/extract.json：
   {tool, generated_at?, tables:[{file, sha256, headers, n_rows, columns:[...]}],
    networks:[{figure_id, entities:[...], relations:[...], uncertain:[]}],
    notes: [...]}。本文件 timestamps 允许存在（中间产物，非最终图稿字节）。

命令行：
    python extract.py --case <case.json> [--data <f;[f]>] --out <work_dir> [--json]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chartkit as ck  # noqa: E402

_UNIT_RE = re.compile(r"\(([^()]*)\)|（([^（）]*)）")


def _guess_unit(header: str):
    m = _UNIT_RE.search(str(header))
    if m:
        u = (m.group(1) or m.group(2) or "").strip()
        if u:
            return u
    return None


def _classify(header: str, values):
    low = header.lower()
    err = ck.detect_error_col([header])
    if err == header:
        return "error"
    if low in ("n", "n_samples", "sample_size", "count_n"):
        return "n"
    if any(h in low for h in ("time", "day", "week", "month", "hour", "duration", "dose", "conc", "temp")):
        num = sum(1 for v in values if ck.safe_float(v) is not None)
        return "time" if num > 0 else "category"
    num = sum(1 for v in values if ck.safe_float(v) is not None)
    if len(values) > 0 and num >= 0.6 * len(values):
        return "numeric"
    return "category"


def _profile_column(header, rows):
    values = [r.get(header) for r in rows]
    nums = [ck.safe_float(v) for v in values]
    nums = [v for v in nums if v is not None]
    nulls = sum(1 for v in values if v is None or str(v).strip() == "")
    col = {
        "column": header,
        "role": _classify(header, values),
        "unit": _guess_unit(header),
        "n_rows": len(values),
        "n_null": nulls,
        "null_ratio": round(nulls / len(values), 4) if values else 1.0,
        "sample_values": [str(v) for v in values[:3]],
    }
    if nums:
        col["min"] = min(nums)
        col["max"] = max(nums)
        col["is_numeric"] = True
    else:
        col["is_numeric"] = False
        uniq = sorted({str(v) for v in values if v not in (None, "")})
        col["unique_values"] = uniq[:12]
        col["n_unique"] = len(uniq)
    return col


def profile_table(path):
    headers, rows, ext = ck.load_table(path)
    return {
        "file": os.path.basename(path),
        "sha256": ck.sha256_file(path),
        "format": ext.lstrip("."),
        "headers": headers,
        "n_rows": len(rows),
        "columns": [_profile_column(h, rows) for h in headers],
        "detected": {
            "error_column": ck.detect_error_col(headers),
            "n_column": ck.detect_n_col(headers),
            "time_column": ck.detect_time_col(headers, rows),
            "category_candidates": ck.detect_cat_cols(headers, rows),
            "numeric_candidates": ck.detect_num_cols(headers, rows),
        },
    }


def _load_glossary():
    p = os.path.join(ck.skill_root(), "templates", "entity_glossary.json")
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                obj = json.load(f)
            g = obj.get("entity_glossary") if isinstance(obj, dict) else None
            if isinstance(g, dict):
                return g
        except Exception:
            pass
    return {}


ENTITY_LINE = re.compile(r"^\s*ENTITY:\s*(.+)$", re.IGNORECASE)
REL_LINE = re.compile(r"^\s*REL:\s*(.+)$", re.IGNORECASE)


def _parse_entity_line(body: str):
    parts = [p.strip() for p in body.split("|")]
    eid = parts[0] if len(parts) > 0 else None
    label = parts[1] if len(parts) > 1 else eid
    group = parts[2] if len(parts) > 2 else "default"
    cite = parts[3] if len(parts) > 3 else None
    return {"id": eid, "label": label, "group": group, "cite": cite}


def _parse_rel_line(body: str):
    left, sep, right = body.partition("->")
    if not sep:
        return None
    parts = [p.strip() for p in right.split("|")] if right else []
    from_id = left.strip()
    to_id = parts[0] if parts else None
    label = parts[1] if len(parts) > 1 else None
    rtype = parts[2] if len(parts) > 2 else None
    return {"from": from_id, "to": to_id, "label": label, "type": rtype}


def scan_material_text(path, glossary):
    """扫描材料文本：
    1. ENTITY:/REL: 显式行 → 结构化抽取（无不确定）；
    2. 其余段落 → 用词表做候选扫描，标记 uncertain=true。
    返回 (entities, relations, uncertain)。"""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    entities, relations, uncertain = [], [], []
    seen_e = set()
    for line in text.splitlines():
        m = ENTITY_LINE.match(line)
        if m:
            ent = _parse_entity_line(m.group(1))
            if ent.get("id") and ent["id"] not in seen_e:
                seen_e.add(ent["id"])
                ent["source"] = os.path.basename(path)
                entities.append(ent)
            continue
        m = REL_LINE.match(line)
        if m:
            rel = _parse_rel_line(m.group(1))
            if rel and rel.get("from") and rel.get("to"):
                rel["source"] = os.path.basename(path)
                relations.append(rel)
    # 词表候选扫描（不猜测，仅提示）
    for key, meta in glossary.items():
        if not isinstance(meta, dict):
            continue
        pattern = meta.get("pattern")
        if not pattern:
            continue
        try:
            hits = len(re.findall(pattern, text, re.IGNORECASE))
        except re.error:
            hits = 0
        if hits and not any(e.get("id") == key for e in entities):
            uncertain.append({
                "candidate_id": key, "label": meta.get("label", key),
                "hits": hits, "uncertain": True,
                "note": "词表扫描命中，未经 Agent 确认不得上图（D4/D14）。",
                "source": os.path.basename(path),
            })
    return entities, relations, uncertain


def extract(case_path, data_paths=None, work_dir=None, out_path=None):
    case_dir = os.path.dirname(os.path.abspath(case_path))
    case = _load_case(case_path)
    report = {"tool": "extract.py (efficiency-3 / challenge-1bd90d8a v2)",
              "case_id": str(case.get("case_id") or case.get("id") or case.get("caseId") or "case"),
              "tables": [], "networks": [], "notes": []}
    # 数据文件路径解析
    files = list(data_paths or [])
    files += _case_data_files(case, case_dir)
    files = _dedup_paths(files)
    for f in files:
        if os.path.exists(f) and f.lower().endswith((".csv", ".tsv", ".tab", ".json")):
            try:
                report["tables"].append(profile_table(f))
            except Exception as exc:
                report["notes"].append(f"表格画像失败 {os.path.basename(f)}：{exc}")
    # 网络材料
    specs = _case_figures(case)
    glossary = _load_glossary()
    for spec in specs:
        if str(spec.get("type") or "").lower() not in ("network", "auto"):
            continue
        fid = str(spec.get("id") or "fig")
        net = {"figure_id": fid, "entities": [], "relations": [], "uncertain": []}
        ef = spec.get("entities_file") or spec.get("entities_path")
        material = spec.get("material_file")
        if ef:
            p = ef if os.path.isabs(str(ef)) else os.path.join(case_dir, str(ef))
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8-sig") as fh:
                    obj = json.load(fh)
                nodes = obj.get("nodes") if isinstance(obj, dict) else obj
                rels = (obj.get("relations") if isinstance(obj, dict) else None) or spec.get("relations") or []
                if isinstance(nodes, list):
                    for n in nodes:
                        n = {**n, "source": os.path.basename(p)}
                        net["entities"].append(n)
                if isinstance(rels, list):
                    for r in rels:
                        r = {**r, "source": os.path.basename(p)}
                        net["relations"].append(r)
            else:
                net["uncertain"].append(f"entities_file 不存在：{p}")
        elif material:
            p = material if os.path.isabs(str(material)) else os.path.join(case_dir, str(material))
            if os.path.exists(p):
                ents, rels, unc = scan_material_text(p, glossary)
                net["entities"].extend(ents)
                net["relations"].extend(rels)
                net["uncertain"].extend(unc)
        elif spec.get("entities") or spec.get("relations"):
            net["entities"] = list(spec.get("entities") or [])
            net["relations"] = list(spec.get("relations") or [])
        report["networks"].append(net)
    if work_dir:
        os.makedirs(work_dir, exist_ok=True)
        p = out_path or os.path.join(work_dir, "extract.json")
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        report["_written_to"] = os.path.basename(p)
    return report


# ---- case 兼容装载（与 main.py 同一语义，避免重复实现）----

def _load_case(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        case = json.load(f)
    if isinstance(case, list):
        case = case[0]
    elif isinstance(case, dict) and isinstance(case.get("cases"), list) and case["cases"]:
        case = case["cases"][0]
    if not isinstance(case, dict):
        raise ValueError(f"case.json 不是对象：{type(case).__name__}")
    return case


def _case_data_files(case, case_dir):
    outs = []
    files = case.get("data_files") or case.get("sources") or []
    if isinstance(files, str):
        files = [files]
    for f in files:
        if isinstance(f, dict):
            f = f.get("file") or f.get("path")
        if not f:
            continue
        p = f if os.path.isabs(str(f)) else os.path.join(case_dir, str(f))
        if os.path.exists(p):
            outs.append(p)
    if not outs and os.path.isdir(case_dir):
        for fn in sorted(os.listdir(case_dir)):
            low = fn.lower()
            if low.startswith("case") or low.startswith("task"):
                continue
            if low.endswith((".csv", ".tsv", ".tab", ".json")) and fn.lower() != "entities.json":
                p = os.path.join(case_dir, fn)
                if os.path.exists(p):
                    outs.append(p)
    return outs


def _case_figures(case):
    if isinstance(case.get("figures"), list) and case["figures"]:
        return list(case["figures"])
    if case.get("figure") is not None:
        return [case["figure"]]
    if case.get("figure_spec") is not None:
        return [case["figure_spec"]]
    return []


def _dedup_paths(paths):
    seen, out = set(), []
    for p in paths:
        ap = os.path.abspath(p)
        if ap not in seen:
            seen.add(ap)
            out.append(ap)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="源材料抽取：表格画像 + 实体/关系（CP2）")
    ap.add_argument("--case", required=True, help="case.json 路径")
    ap.add_argument("--data", default=None, help="显式数据文件（; 分隔多个）")
    ap.add_argument("--out", default=None, help="工作目录（写 extract.json，缺省仅打印）")
    ap.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    args = ap.parse_args(argv)
    data_paths = [p for p in re.split(r"[;]", args.data) if p.strip()] if args.data else None
    report = extract(args.case, data_paths=data_paths, work_dir=args.out)
    if args.json or args.out:
        print(json.dumps({k: v for k, v in report.items() if not k.startswith("_")},
                         ensure_ascii=False, indent=2))
    else:
        print(f"[extract] case_id={report['case_id']} tables={len(report['tables'])} "
              f"networks={len(report['networks'])} notes={len(report['notes'])}")
        for t in report["tables"]:
            print(f"  table {t['file']}: {t['n_rows']} rows, {len(t['headers'])} cols "
                  f"(err={t['detected']['error_column']}, n={t['detected']['n_column']}, "
                  f"time={t['detected']['time_column']})")
        for net in report["networks"]:
            print(f"  network {net['figure_id']}: {len(net['entities'])} entities, "
                  f"{len(net['relations'])} relations, {len(net['uncertain'])} uncertain")
    sys.exit(0)


if __name__ == "__main__":
    main()