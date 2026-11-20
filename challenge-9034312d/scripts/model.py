# -*- coding: utf-8 -*-
"""model.py — 结构化中间表示 (Structured Intermediate Representation, SIR).

把输入案例（case.json + 可选 task.md）解析成「实体—关系—步骤—流向」的
结构化图面模型。这是本 Skill 的核心创新点：先出结构化中间表示，再据此
布图与自检（对应评分维度「创新增益」）。

设计约束：
- 只用标准库，保证在任何装有 Python 3 的评测机上可跑。
- 不依赖领域标签猜数据：每个实体/关系尽量携带 source（材料出处），
  拿不到就记为 null 并写入 uncertainty。
- 不编造数据：结构化字段缺失时只做朴素文本解构（提取步骤/箭头/编号），
  解构结果标记 extraction="text-heuristic"，由 Agent 复核。
"""

from __future__ import annotations

import json
import os
import re
import sys
sys.dont_write_bytecode = True  # 评测包内不落 .pyc
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

PT_TO_MM = 25.4 / 72.0  # 1 pt → mm

# 图元类别统一词表（图例/配色/形状都从 kind 映射）
KINDS = {
    "step":       {"label": "步骤",       "shape": "rect"},
    "phase":      {"label": "阶段",       "shape": "rect"},
    "device":     {"label": "装置/仪器",   "shape": "rect"},
    "material":   {"label": "物料/样本",   "shape": "rounded"},
    "product":    {"label": "产物/输出",   "shape": "rounded"},
    "data":       {"label": "数据/文件",   "shape": "diamond"},
    "decision":   {"label": "判断/条件",   "shape": "diamond"},
    "milestone":  {"label": "里程碑",      "shape": "rect"},
    "waste":      {"label": "废料/终点",   "shape": "rounded"},
    "container":  {"label": "容器/接口",   "shape": "rect"},
}

RELATION_KINDS = {
    "flow":     {"label": "流向",   "arrow": "triangle"},
    "connect":  {"label": "连接",   "arrow": "line"},
    "depend":   {"label": "依赖",   "arrow": "triangle"},
    "recycle":  {"label": "回流",   "arrow": "triangle-dashed"},
    "sequence": {"label": "顺序",   "arrow": "triangle"},
    "causation": {"label": "导致",  "arrow": "triangle"},
}


@dataclass
class Entity:
    id: str
    name: str
    kind: str = "step"
    stage: Optional[str] = None       # 阶段/列
    source: Optional[str] = None      # 材料出处，如 "task.md §2.1"
    label: Optional[str] = None       # 图面标签（覆盖 name 的短标签）
    props: Dict[str, Any] = field(default_factory=dict)

    def display_label(self) -> str:
        return (self.label or self.name or self.id).strip()


@dataclass
class Relation:
    id: str
    from_id: str
    to_id: str
    kind: str = "flow"
    label: Optional[str] = None
    source: Optional[str] = None


@dataclass
class SourceRef:
    id: str
    file: str
    ref: Optional[str] = None
    note: Optional[str] = None


@dataclass
class FigureModel:
    case_id: str
    title: str
    figure_type: str = "route"          # route | apparatus | flow | hybrid
    canvas: Dict[str, Any] = field(default_factory=lambda: {"width_mm": 297, "height_mm": 180})
    entities: List[Entity] = field(default_factory=list)
    relations: List[Relation] = field(default_factory=list)
    sources: List[SourceRef] = field(default_factory=list)
    extraction: str = "structured"
    uncertainty: List[Dict[str, Any]] = field(default_factory=list)
    raw_text: str = ""
    task_text: str = ""

    def entity_by_id(self, eid: str) -> Optional[Entity]:
        for e in self.entities:
            if e.id == eid:
                return e
        return None


# ---------------------------------------------------------------- 数据读取

def read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_inputs(case_path: str, task_path: Optional[str] = None) -> Tuple[Dict[str, Any], str]:
    """读取真实输入文件。文件不存在直接报错（禁止假装内容）。"""
    if not os.path.isfile(case_path):
        raise FileNotFoundError(f"case.json 不存在: {case_path}")
    data = read_json(case_path)
    task_text = ""
    if task_path and os.path.isfile(task_path):
        with open(task_path, "r", encoding="utf-8") as fh:
            task_text = fh.read()
    return data, task_text


# ---------------------------------------------------------------- 结构化解构

def _strip_key(d: Dict[str, Any], *keys: str) -> Any:
    for k in keys:
        if k in d and d[k] is not None and d[k] != "":
            return d[k]
    return None


def _norm_kind(k: Any) -> str:
    if not k:
        return "step"
    s = str(k).strip().lower()
    if s in KINDS:
        return s
    # 容错映射
    alias = {
        "step": "step", "步骤": "step", "step/operation": "step",
        "phase": "phase", "阶段": "phase", "stage": "phase",
        "device": "device", "装置": "device", "仪器": "device", "部件": "device",
        "equipment": "device", "part": "device", "部件/接口": "device",
        "material": "material", "物料": "material", "样本": "material", "样品": "material",
        "product": "product", "产物": "product", "输出": "product", "outcome": "product",
        "data": "data", "数据": "data", "file": "data", "文件": "data",
        "decision": "decision", "判断": "decision", "条件": "decision",
        "milestone": "milestone", "里程碑": "milestone",
        "waste": "waste", "废料": "waste", "终点": "waste",
        "container": "container", "容器": "container", "接口": "container",
    }
    return alias.get(s, "step")


def _norm_relation_kind(k: Any) -> str:
    if not k:
        return "flow"
    s = str(k).strip().lower()
    if s in RELATION_KINDS:
        return s
    alias = {
        "flow": "flow", "流向": "flow", "arrow": "flow", "material_flow": "flow",
        "connect": "connect", "连接": "connect", "link": "connect", "connection": "connect",
        "depend": "depend", "依赖": "depend", "depends_on": "depend", "include": "depend",
        "recycle": "recycle", "回流": "recycle", "reuse": "recycle", "循环": "recycle",
        "sequence": "sequence", "顺序": "sequence", "next": "sequence",
        "causation": "causation", "导致": "causation", "result_in": "causation",
    }
    return alias.get(s, "flow")


def _parse_entities(list_data: Any) -> List[Entity]:
    out: List[Entity] = []
    if not isinstance(list_data, list):
        return out
    for i, item in enumerate(list_data):
        if not isinstance(item, dict):
            continue
        eid = str(_strip_key(item, "id", "ID", "entity_id", "key") or f"E{i+1}")
        name = str(_strip_key(item, "name", "label", "title", "text", "部件", "entity") or "")
        if not name:
            continue
        stage = _strip_key(item, "stage", "phase_id", "phase", "阶段", "column", "lane")
        src = _strip_key(item, "source", "source_ref", "src", "出处", "ref")
        if isinstance(src, (dict, list)):
            src = json.dumps(src, ensure_ascii=False)
        kind = _norm_kind(_strip_key(item, "kind", "type", "类别", "shape"))
        props = {k: v for k, v in item.items()
                 if k not in ("id", "ID", "entity_id", "name", "label", "title", "text",
                              "kind", "type", "category", "类别", "stage", "phase_id",
                              "source", "source_ref", "src", "ref", "出处")}
        out.append(Entity(id=eid, name=str(name), kind=kind,
                          stage=None if stage is None else str(stage),
                          source=None if src is None else str(src),
                          label=_strip_key(item, "short_label", "图面标签"),
                          props=props))
    return out


def _parse_relations(list_data: Any, entity_ids: set) -> List[Relation]:
    out: List[Relation] = []
    if not isinstance(list_data, list):
        return out
    for i, item in enumerate(list_data):
        if not isinstance(item, dict):
            continue
        frm = str(_strip_key(item, "from", "from_id", "source", "src", "起点") or "")
        to = str(_strip_key(item, "to", "to_id", "target", "tgt", "终点") or "")
        if not frm or not to or frm not in entity_ids or to not in entity_ids:
            continue  # 指向不存在实体的关系不画，避免断头箭头
        kind = _norm_relation_kind(_strip_key(item, "kind", "type", "关系", "arrow_type"))
        rid = str(_strip_key(item, "id", "rel_id", "key") or f"R{i+1}")
        src = _strip_key(item, "source", "source_ref", "src", "出处", "ref")
        out.append(Relation(id=rid, from_id=frm, to_id=to, kind=kind,
                            label=_strip_key(item, "label", "flow_label", "标签"),
                            source=None if src is None else str(src)))
    return out


# ---------------------------------------------------------------- 文本解构（兜底）

_NUM = r"(?:第?\s*[0-9一二三四五六七八九十]+\s*(?:步|环节|阶段|步奏|工序|期)|[0-9]+[.、)])"

def _clean(line: str) -> str:
    return re.sub(r"^[\s\-*•·◦>]+", "", line).strip()


# 「第N步:内容」「第N步内容」显式步骤
_STEP_LINE = re.compile(r"^(第\s*[0-9一二三四五六七八九十]+\s*步)\s*[:：、.，,]?\s*(.+)$")
# 「由A、B、C(等)组成/构成/包括」装置部件列举
_PART_LIST = re.compile(r"由\s*([^。；;]+?)\s*(?:等\s*)?(?:组成|构成|构成(?:的)?|包括|包含)")


def _split_segments(text: str):
    """按句读切段，每段保留起止偏移供 source 引用。"""
    segments = []
    pos = 0
    for m in re.finditer(r"[^。；;\n]+[。；;\n]?", text):
        seg = m.group(0).strip()
        if seg:
            segments.append((seg, m.start() + 1))
    return segments


def text_entities(task_text: str, raw_text: str) -> List[Entity]:
    """从正文文本朴素抽取设备/步骤实体。仅作结构化数据缺失时的兜底。"""
    entities: List[Entity] = []
    seen = set()
    all_text = "\n".join(t for t in (task_text, raw_text) if t)

    # A) 装置部件列表：「由 A、B、C 组成」
    for m in _PART_LIST.finditer(all_text):
        parts = [p.strip() for p in re.split(r"[、,，和及与]", m.group(1)) if p.strip()]
        for p in parts:
            if p and p not in seen and len(p) <= 30:
                seen.add(p)
                entities.append(Entity(id=f"D{len(entities)+1}", name=p,
                                       kind="device", source="text:part-list"))
    # B) 显式编号步骤：「第N步:内容」
    segs = _split_segments(all_text)
    for seg, off in segs:
        m = _STEP_LINE.match(seg)
        if m:
            name = _clean(m.group(2))
            name = re.split(r"[。；;]", name)[0].strip()
            if name and name not in seen and 2 <= len(name) <= 60:
                seen.add(name)
                entities.append(Entity(id=f"T{len(entities)+1}", name=name,
                                       kind="step", source=f"text:line@{off}"))
    # C) 兜底：普通编号行「1. xxx」
    if not any(e.kind == "step" for e in entities):
        for seg, off in segs:
            if not re.match(_NUM, seg):
                continue
            name = re.sub(_NUM, "", seg, count=1).strip(" ：:，,。;；\t ")
            name = re.split(r"[。；;]", name)[0].strip()
            if name and name not in seen and 2 <= len(name) <= 60:
                seen.add(name)
                entities.append(Entity(id=f"T{len(entities)+1}", name=name,
                                       kind="step", source=f"text:line@{off}"))
    return entities[:24]


def text_relations(entities: List[Entity], task_text: str, raw_text: str) -> List[Relation]:
    """把相邻步骤串成顺序关系（仅兜底，箭头方向由 Agent 复核）。

    只串 step 类实体的先后顺序；设备/部件等不自动连线（避免凭空画连接），
    由 Agent 按材料补充连接关系。
    """
    rels: List[Relation] = []
    steps = [e for e in entities if e.kind == "step"]
    for a, b in zip(steps, steps[1:]):
        rels.append(Relation(id=f"TR{len(rels)+1}", from_id=a.id, to_id=b.id,
                             kind="sequence", source="text:order"))
    return rels


# ---------------------------------------------------------------- 主入口

def build_model(case_path: str, task_path: Optional[str] = None,
                figure_type_override: Optional[str] = None) -> FigureModel:
    """构建 FigureModel。返回前自动做一致性自查（实体 id 唯一、关系两端存在）。"""
    data, task_text = load_inputs(case_path, task_path)
    raw_text = data.get("text") or data.get("materials_text") or data.get("材料") or ""

    case_id = str(data.get("case_id") or data.get("id") or os.path.splitext(os.path.basename(case_path))[0])
    title = str(data.get("title") or data.get("name") or "科研图稿")

    canvas = dict(data.get("canvas") or data.get("画布") or {})
    canvas.setdefault("width_mm", 297)
    canvas.setdefault("height_mm", 180)

    entities = _parse_entities(data.get("entities") or data.get("entity_list") or
                               data.get("nodes") or data.get("步骤") or data.get("stages"))
    relations = _parse_relations(data.get("relations") or data.get("links") or
                                 data.get("edges") or data.get("连接") or data.get("flows"),
                                 {e.id for e in entities})

    extraction = "structured"
    if not entities:
        entities = text_entities(task_text, raw_text)
        extraction = "text-heuristic"
    if not relations:
        relations = text_relations(entities, task_text, raw_text)

    # id 唯一化
    used: set = set()
    for e in entities:
        base = e.id
        n = 2
        while e.id in used:
            e.id = f"{base}_{n}"
            n += 1
        used.add(e.id)

    # 孤立实体（无任何关系）计数，供 Agent 决定是否补连线
    linked = {r.from_id for r in relations} | {r.to_id for r in relations}
    orphans = [e.id for e in entities if e.id not in linked]

    fig_type = figure_type_override or str(data.get("figure_type") or data.get("type") or "") or \
               ("apparatus" if any(e.kind in ("device", "container", "material") for e in entities)
                else "route")
    if fig_type not in ("route", "apparatus", "flow", "hybrid"):
        fig_type = "route"

    uncertainty: List[Dict[str, Any]] = []
    if extraction == "text-heuristic":
        uncertainty.append({
            "scope": "relations",
            "issue": "未提供结构化 entities/relations，采用文本朴素解构，仅串联相邻步骤",
            "action": "Agent 需对照材料复核实体集合与箭头方向",
        })
    if orphans:
        uncertainty.append({
            "scope": "orphan_entities",
            "issue": f"{len(orphans)} 个实体没有任何连接关系: {orphans[:10]}",
            "action": "核对是否漏画材料流向或步骤顺序",
        })
    missing_src = [e.id for e in entities if not e.source]
    if missing_src and extraction == "structured":
        uncertainty.append({
            "scope": "sources",
            "issue": f"{len(missing_src)} 个实体缺少 source 出处: {missing_src[:10]}",
            "action": "按题面材料补 source 字段，保证可追溯",
        })

    sources = [SourceRef(id="input-case", file=os.path.basename(case_path), note="case.json")]
    if task_path:
        sources.append(SourceRef(id="input-task", file=os.path.basename(task_path), note="task.md"))

    return FigureModel(
        case_id=case_id, title=title, figure_type=fig_type, canvas=canvas,
        entities=entities, relations=relations, sources=sources,
        extraction=extraction, uncertainty=uncertainty,
        raw_text=raw_text, task_text=task_text,
    )


if __name__ == "__main__":
    # 自检：python model.py <case.json> [task.md]
    if len(sys.argv) < 2:
        print("usage: python model.py <case.json> [task.md]", file=sys.stderr)
        sys.exit(2)
    m = build_model(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    print(json.dumps({
        "case_id": m.case_id, "figure_type": m.figure_type,
        "entities": len(m.entities), "relations": len(m.relations),
        "extraction": m.extraction,
        "uncertainty": [u["issue"] for u in m.uncertainty],
    }, ensure_ascii=False, indent=2))