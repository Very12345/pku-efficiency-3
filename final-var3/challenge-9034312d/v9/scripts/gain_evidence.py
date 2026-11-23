# -*- coding: utf-8 -*-
"""gain_evidence.py — 证据抽取（对应高分包 88686 的 evidence-first 职责）。

职责：从**真实材料文件**（case.json + task.md + 案例引用的材料文件）中抽取
「实体—关系—步骤—流向」的证据清单：每条实体/关系尽量带上
`locator`（材料定位，如 "task.md §2.1" / "case.json[entities][3]"）与
`quote`（原文引用片段），并计算每个输入文件的 sha256 作为「版本」证据。

产出 evidence.json（结构化）供 main.py 的 --evidence 使用；Agent 必须复核
evidence 后再进入布图（CP1 证据门）。

设计约束：
- 只用标准库；自定位（os.path.dirname(__file__)），不依赖运行时 cwd；
- 不编造：拿不到出处的条目 source=null 并在 notes 里列出，由 Agent 补齐；
- 文本兜底复用 model.text_entities/text_relations，locator 用 "text:line@N"。
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
sys.dont_write_bytecode = True  # 评测包内不落 .pyc

_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import model as model_mod  # noqa: E402


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _pick(d: dict, *keys):
    for k in keys:
        if k in d and d[k] is not None and d[k] != "":
            return d[k]
    return None


def _quote_for(name: str, text: str, maxlen: int = 120) -> str:
    """在文本中找第一个包含实体名的句子/行作为原文引用。找不到返回空串。"""
    if not text:
        return ""
    for seg, _ in model_mod._split_segments(text):
        if name and name in seg:
            return seg.strip()[:maxlen]
    for line in text.splitlines():
        if name and name in line:
            return line.strip()[:maxlen]
    return ""


def extract_evidence(case_path: str,
                     task_path: Optional[str] = None,
                     material_paths: Optional[list] = None) -> dict:
    """抽取证据清单。返回结构见 references/OUTPUT_CONTRACT.md 的 evidence 段。

    返回:
    {
      "source": "gain_evidence",
      "extraction": "structured" | "text-heuristic",
      "entities": [{id,name,kind,stage,source,label,locator,quote}],
      "relations": [{id,from,to,kind,label,source,locator,quote}],
      "evidence":   [{"id","type","ref","locator","quote"}],
      "sources":   [{"id","file","path","sha256","size","role"}],
      "notes":     [字符串说明（含缺失 source 清单、兜底说明）],
    }
    """
    data, task_text = model_mod.load_inputs(case_path, task_path)
    raw_text = data.get("text") or data.get("materials_text") or data.get("材料") or ""

    # ---------- 材料文件来源（版本证据） ----------
    sources = []
    sources.append({
        "id": "input-case", "file": os.path.basename(case_path),
        "path": os.path.abspath(case_path), "sha256": sha256_file(case_path),
        "size": os.path.getsize(case_path), "role": "case",
    })
    if task_path and os.path.isfile(task_path):
        sources.append({
            "id": "input-task", "file": os.path.basename(task_path),
            "path": os.path.abspath(task_path), "sha256": sha256_file(task_path),
            "size": os.path.getsize(task_path), "role": "task",
        })
    material_text = ""
    for i, mp in enumerate(material_paths or []):
        if os.path.isfile(mp):
            sources.append({
                "id": f"material-{i+1}", "file": os.path.basename(mp),
                "path": os.path.abspath(mp), "sha256": sha256_file(mp),
                "size": os.path.getsize(mp), "role": "material",
            })
            with open(mp, "r", encoding="utf-8") as fh:
                material_text += "\n" + fh.read()

    all_text = "\n".join(t for t in (task_text, raw_text, material_text) if t)
    notes: list = []

    # ---------- 结构化实体/关系（优先） ----------
    entities_raw = data.get("entities") or data.get("entity_list") or \
                   data.get("nodes") or data.get("步骤") or data.get("stages")
    relations_raw = data.get("relations") or data.get("links") or \
                    data.get("edges") or data.get("连接") or data.get("flows")

    extraction = "structured"
    entities, relations = [], []
    if entities_raw:
        entities = model_mod._parse_entities(entities_raw)
    if relations_raw:
        relations = model_mod._parse_relations(relations_raw, {e.id for e in entities})

    if not entities:
        entities = model_mod.text_entities(task_text, all_text)
        relations = model_mod.text_relations(entities, task_text, all_text)
        extraction = "text-heuristic"
        notes.append(
            "未提供结构化 entities/relations，采用文本朴素解构（仅串联相邻步骤）；"
            "设备/部件不自动连线，需 Agent 按材料补齐连接关系。")

    # ---------- 每个实体/关系补 locator + quote ----------
    ent_out, rel_out, evidence = [], [], []
    evi_no = 0
    for e in entities:
        locator = None
        quote = ""
        if e.source and e.source.startswith("text:"):
            locator = e.source
        elif e.source:
            locator = e.source
        elif extraction == "structured":
            locator = "case.json[entities]"
        if e.name and extraction == "text-heuristic":
            quote = _quote_for(e.name, all_text)
        evi_no += 1
        evidence.append({"id": f"EV{evi_no}", "type": "entity", "ref": e.id,
                         "locator": locator, "quote": quote})
        ent_out.append({
            "id": e.id, "name": e.name, "kind": e.kind, "stage": e.stage,
            "source": e.source, "label": e.label,
            "locator": locator, "quote": quote,
        })

    for r in relations:
        locator = r.source or ("case.json[relations]" if extraction == "structured" else "text:order")
        quote = ""
        if extraction == "text-heuristic":
            fr = next((e for e in entities if e.id == r.from_id), None)
            to = next((e for e in entities if e.id == r.to_id), None)
            if fr and to:
                quote = _quote_for(fr.name, all_text) if fr.name else ""
                if not quote and to.name:
                    quote = _quote_for(to.name, all_text)
        evi_no += 1
        evidence.append({"id": f"EV{evi_no}", "type": "relation", "ref": r.id,
                         "locator": locator, "quote": quote})
        rel_out.append({
            "id": r.id, "from": r.from_id, "to": r.to_id, "kind": r.kind,
            "label": r.label, "source": r.source,
            "locator": locator, "quote": quote,
        })

    # ---------- 缺失 source 清单（诚实） ----------
    missing = [e.id for e in entities if not e.source]
    if missing and extraction == "structured":
        notes.append(f"{len(missing)} 个实体无 source 出处: {missing[:10]} —— 需按材料补齐")

    return {
        "source": "gain_evidence",
        "extraction": extraction,
        "entities": ent_out,
        "relations": rel_out,
        "evidence": evidence,
        "sources": sources,
        "notes": notes,
    }


def main(argv) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="证据抽取：从真实材料抽取实体/关系证据清单")
    ap.add_argument("--case", required=True, help="case.json 路径（真实输入）")
    ap.add_argument("--task", default=None, help="task.md 路径（可选）")
    ap.add_argument("--material", action="append", default=None,
                    help="材料文件/目录（可多次）；目录只读其中 .md/.txt/.csv/.tex")
    ap.add_argument("--out", default="evidence.json", help="输出 evidence.json 路径")
    args = ap.parse_args(argv)

    mats = []
    if args.material:
        for m in args.material:
            if os.path.isdir(m):
                for root, _dirs, files in os.walk(m):
                    for f in sorted(files):
                        if f.lower().endswith((".md", ".txt", ".csv", ".tex")):
                            mats.append(os.path.join(root, f))
            else:
                mats.append(m)

    ev = extract_evidence(args.case, args.task, mats)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(ev, fh, ensure_ascii=False, indent=2)
    print(json.dumps({
        "extraction": ev["extraction"],
        "entities": len(ev["entities"]),
        "relations": len(ev["relations"]),
        "evidence_items": len(ev["evidence"]),
        "source_files": [s["file"] for s in ev["sources"]],
        "notes": ev["notes"],
        "out": args.out,
    }, ensure_ascii=False, indent=2))
    return 0 if ev["entities"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))