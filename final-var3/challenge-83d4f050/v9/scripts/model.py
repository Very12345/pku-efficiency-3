# -*- coding: utf-8 -*-
"""Shared mechanism-spec data model and glyph/palette tables (v2).

Pure standard library.  This module (together with extract.py, layout.py,
pathway_svg.py, mpl_backend.py, topology.py, legend_audit.py,
validate_figure.py, result_writer.py, check_contract.py) is the mandatory
core of the skill.  matplotlib is used only by mpl_backend.py for PNG/PDF
previews and is optional.

The whole pipeline speaks one JSON "mechanism spec" (model):

    {
      "case_id": str,
      "title": str,
      "example": bool,                 # True => diagram is marked 示例，非正式案例
      "entities": [ {"id","name","type","compartment","data"?,"note"?,
                     "source":[{"ref","kind","line"?}], "uncertain"?} ],
      "edges":    [ {"id","from","to","type","subtype"?,"evidence"?,"uncertain"?,
                     "label"?,"note"?,"feedback"?,"source":[...]} ],
      "legend":  {...},                # see default_legend()
      "layout":  {"compartments":[...], "constraints"?},
      "extraction": {"method": str, "verified_by_agent": bool}
    }

Style tables are the *canonical palette* and live in assets/palettes.json;
the literals below are the built-in fallback so the pipeline still runs when
the asset file is missing.  assets/palettes.json is generated from these
defaults (see TEST.md) and is the single place a human edits colors/widths.
"""
import json
import os

SKILL_NAME = "biological-mechanism-pathway-diagram"
CONTRACT_VERSION = "1.1"
SKILL_VERSION = "2.0.0"

CANVAS = {"width": 1200, "height": 900}

# ---------------------------------------------------------------------------
# default palette (fallback; canonical copy in assets/palettes.json) ---------
# ---------------------------------------------------------------------------
_NODE_TYPES_DEFAULT = {
    "protein":        {"shape": "roundrect", "fill": "#EAF2FB", "stroke": "#1F4E79",
                       "zh": "蛋白质", "en": "protein"},
    "gene":           {"shape": "rect", "fill": "#FFF3E0", "stroke": "#B9770E",
                       "italic": True, "zh": "基因", "en": "gene"},
    "complex":        {"shape": "roundrect", "fill": "#EDE7F6", "stroke": "#6C3483",
                       "double": True, "zh": "复合物", "en": "complex"},
    "rna":            {"shape": "roundrect", "fill": "#E8F8F5", "stroke": "#117A65",
                       "dash": True, "zh": "RNA", "en": "RNA"},
    "small_molecule": {"shape": "circle", "fill": "#FDEBD0", "stroke": "#CA6F1E",
                       "zh": "小分子/配体/代谢物", "en": "small molecule / ligand"},
    "other":          {"shape": "roundrect", "fill": "#F4F6F6", "stroke": "#7F8C8D",
                       "zh": "其他", "en": "other"},
}
_EDGE_TYPES_DEFAULT = {
    "activation":   {"marker": "arrow",   "color": "#2E7D32", "width": 2.4,
                     "zh": "激活 / 促进", "en": "activation / promotion"},
    "inhibition":   {"marker": "bar",     "color": "#C0392B", "width": 2.4,
                     "zh": "抑制 / 阻断", "en": "inhibition / block"},
    "binding":      {"marker": "none",    "color": "#1F4E79", "width": 2.0,
                     "zh": "结合 / 互作 / 募集", "en": "binding / interaction / recruitment"},
    "modification": {"marker": "circle",  "color": "#B9770E", "width": 2.0,
                     "zh": "修饰（磷酸化、泛素化等）", "en": "modification (phosphorylation, ubiquitination, ...)"},
    "transport":    {"marker": "diamond", "color": "#6C3483", "width": 2.2,
                     "zh": "转运 / 转位", "en": "transport / translocation"},
}
_EVIDENCE_WIDTH_DEFAULT = {"strong": 2.8, "moderate": 2.2, "weak": 1.6}
_COMPARTMENT_DEFAULT = {
    "extracellular": {"zh": "胞外", "en": "Extracellular", "rank": 0,
                      "fill": "#FBFCFC", "stroke": "#D5DBDB", "height": 150},
    "membrane":      {"zh": "细胞膜", "en": "Plasma membrane", "rank": 1,
                      "fill": "#EBF5FB", "stroke": "#5DADE2", "height": 90},
    "cytoplasm":     {"zh": "细胞质", "en": "Cytoplasm", "rank": 2,
                      "fill": "#FDFEFE", "stroke": "#D5DBDB", "height": 170},
    "nucleus":       {"zh": "细胞核", "en": "Nucleus", "rank": 3,
                      "fill": "#F4ECF7", "stroke": "#AF7AC5", "height": 170},
}
_DATA_MAPPING_DEFAULT = {
    "field": "表达量", "label_zh": "实体填充色 = 相对表达量（数据映射）",
    "label_en": "node fill = relative expression",
    "low": "#FFF7E0", "high": "#1F4E79",
    "note_zh": "材料未给出数值时使用类型默认色（见实体样式区）",
    "note_en": "type default color is used when no data value is available",
}


def _load_palettes():
    """Read assets/palettes.json next to the skill root; {} when missing."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, "assets", "palettes.json")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


_PAL = _load_palettes()


def _merge(base, overlay):
    out = dict(base)
    if isinstance(overlay, dict):
        for k, v in overlay.items():
            if isinstance(v, dict) and isinstance(out.get(k), dict):
                out[k] = _merge(out[k], v)
            elif v is not None:
                out[k] = v
    return out


NODE_TYPES = _merge(_NODE_TYPES_DEFAULT, _PAL.get("node_types") or {})
EDGE_TYPES = _merge(_EDGE_TYPES_DEFAULT, _PAL.get("edge_types") or {})
EVIDENCE_WIDTH = _merge(_EVIDENCE_WIDTH_DEFAULT, _PAL.get("evidence_width") or {})
COMPARTMENT_DEFAULT = _merge(_COMPARTMENT_DEFAULT, _PAL.get("compartments") or {})
DATA_MAPPING_DEFAULT = _merge(_DATA_MAPPING_DEFAULT, _PAL.get("data_mapping") or {})

NODE_TYPE_ALIASES = {
    "protein": "protein", "蛋白质": "protein", "蛋白": "protein", "proteins": "protein",
    "gene": "gene", "基因": "gene", "genes": "gene",
    "complex": "complex", "复合物": "complex", "复合体": "complex", "protein complex": "complex",
    "rna": "rna", "rnas": "rna",
    "small_molecule": "small_molecule", "小分子": "small_molecule", "配体": "small_molecule",
    "代谢物": "small_molecule", "metabolite": "small_molecule", "ligand": "small_molecule",
    "other": "other", "其他": "other",
}
EDGE_TYPES_ALIASES = {
    "activation": "activation", "激活": "activation", "促进": "activation",
    "inhibition": "inhibition", "抑制": "inhibition", "阻断": "inhibition",
    "binding": "binding", "结合": "binding", "互作": "binding", "募集": "binding",
    "modification": "modification", "修饰": "modification",
    "transport": "transport", "转运": "transport", "转位": "transport",
}
COMPARTMENT_ALIASES = {
    "extracellular": "extracellular", "胞外": "extracellular", "细胞外": "extracellular",
    "外": "extracellular", "membrane": "membrane", "细胞膜": "membrane",
    "膜": "membrane", "质膜": "membrane", "cytoplasm": "cytoplasm",
    "细胞质": "cytoplasm", "胞质": "cytoplasm", "浆膜": "cytoplasm",
    "nucleus": "nucleus", "细胞核": "nucleus", "核": "nucleus", "核内": "nucleus",
}
EDGE_VERB_MAP = {
    # (keyword, type, subtype)
    "激活": ("activation", ""), "促进": ("activation", ""), "正向调控": ("activation", ""),
    "磷酸化": ("modification", "磷酸化"), "去磷酸化": ("modification", "去磷酸化"),
    "泛素化": ("modification", "泛素化"), "甲基化": ("modification", "甲基化"),
    "乙酰化": ("modification", "乙酰化"), "糖基化": ("modification", "糖基化"),
    "修饰": ("modification", ""), "降解": ("modification", "降解"),
    "抑制": ("inhibition", ""), "阻断": ("inhibition", ""), "负向调控": ("inhibition", ""),
    "结合": ("binding", ""), "互作": ("binding", ""), "募集": ("binding", ""),
    "转位": ("transport", ""), "转运": ("transport", ""), "内化": ("transport", "内化"),
    "activate": ("activation", ""), "activates": ("activation", ""), "promotes": ("activation", ""),
    "inhibit": ("inhibition", ""), "inhibits": ("inhibition", ""), "repress": ("inhibition", ""),
    "block": ("inhibition", ""), "bind": ("binding", ""), "binds": ("binding", ""),
    "recruit": ("binding", ""), "interact": ("binding", ""),
    "phosphorylate": ("modification", "phosphorylation"),
    "phosphorylates": ("modification", "phosphorylation"),
    "ubiquitinate": ("modification", "ubiquitination"),
    "methylate": ("modification", "methylation"),
    "translocate": ("transport", ""), "translocates": ("transport", ""),
    "transport": ("transport", ""),
}

# ---------------------------------------------------------------------------
# helpers --------------------------------------------------------------------
# ---------------------------------------------------------------------------
def clamp(v, lo, hi):
    return lo if v < lo else (hi if v > hi else v)


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return "#%02X%02X%02X" % tuple(int(round(v)) for v in rgb)


def lerp_hex(c1, c2, t):
    """Linear interpolation between two hex colors, t in [0,1]."""
    t = clamp(float(t), 0.0, 1.0)
    a, b = hex_to_rgb(c1), hex_to_rgb(c2)
    return rgb_to_hex(tuple(x + (y - x) * t for x, y in zip(a, b)))


def default_legend():
    dm = dict(DATA_MAPPING_DEFAULT)
    return {
        "title": "图例 Legend",
        "entities": {t: dict(v) for t, v in NODE_TYPES.items()},
        "edges": {t: dict(v) for t, v in EDGE_TYPES.items()},
        "evidence_width": dict(EVIDENCE_WIDTH),
        "dash_note": {"zh": "虚线 = 证据弱/间接，或不明确的联系（uncertain）",
                      "en": "dashed = weak / indirect / uncertain evidence"},
        "data_mapping": dm,
        "direction_note": {"zh": "信号流向：自上方区室向下（受体位于膜区）；反馈环在右侧绕行",
                           "en": "flow from upper to lower compartments; feedback loops routed on the right"},
        "version_note": "conventions: see references/legend-encoding.md",
    }


def data_color(entity, legend, vmin=0.0, vmax=1.0):
    """Resolve entity fill from the data mapping, falling back to the type color."""
    dm = legend.get("data_mapping") or {}
    field = dm.get("field")
    val = None
    if field and isinstance(entity.get("data"), dict):
        val = entity["data"].get(field)
    if val is None:
        t = NODE_TYPES.get(entity.get("type", "other"), NODE_TYPES["other"])
        return {"fill": t["fill"], "mapped": False, "value": None}
    try:
        v = float(val)
    except (TypeError, ValueError):
        return {"fill": NODE_TYPES.get(entity.get("type", "other"), NODE_TYPES["other"])["fill"],
                "mapped": False, "value": None}
    t = (v - vmin) / (vmax - vmin) if vmax > vmin else 0.5
    return {"fill": lerp_hex(dm.get("low", "#FFF7E0"), dm.get("high", "#1F4E79"), t),
            "mapped": True, "value": v}


def data_scale(model):
    """Global min/max of the data-mapping field over all entities, or None."""
    dm = (model.get("legend") or {}).get("data_mapping") or {}
    field = dm.get("field")
    if not field:
        return None
    vals = []
    for e in model.get("entities", []):
        v = (e.get("data") or {}).get(field)
        if v is not None:
            try:
                vals.append(float(v))
            except (TypeError, ValueError):
                pass
    if not vals:
        return None
    return min(vals), max(vals)


def entity_has_data(e):
    d = e.get("data") if isinstance(e.get("data"), dict) else {}
    return bool(d)


def edge_style(edge, legend):
    """Resolve stroke color/width/dash/marker for an edge."""
    etype = edge.get("type", "binding")
    spec = (legend or {}).get("edges", {}).get(etype) or EDGE_TYPES.get(etype, EDGE_TYPES["binding"])
    color = spec["color"]
    ev = edge.get("evidence", "moderate")
    width = (legend or {}).get("evidence_width", EVIDENCE_WIDTH).get(
        ev, EVIDENCE_WIDTH.get(ev, 2.2))
    uncertain = bool(edge.get("uncertain")) or ev == "weak"
    dash = [6, 4] if uncertain else None
    return {"color": color, "width": width, "dash": dash, "marker": spec["marker"],
            "uncertain": uncertain}


# ---------------------------------------------------------------------------
# normalization --------------------------------------------------------------
# ---------------------------------------------------------------------------
def normalize_entities(raw_entities):
    out, used = [], set()
    for i, e in enumerate(raw_entities or []):
        if not isinstance(e, dict) or not e.get("name"):
            continue
        eid = str(e.get("id") or ("e%d" % (i + 1)))
        if eid in used:
            eid = eid + "_%d" % i
        used.add(eid)
        etype = NODE_TYPE_ALIASES.get(str(e.get("type", "other")).strip().lower(), "other")
        comp = COMPARTMENT_ALIASES.get(str(e.get("compartment", "")).strip().lower(), None)
        if comp is None:
            comp = str(e.get("compartment", "cytoplasm") or "cytoplasm")
        out.append({
            "id": eid, "name": str(e["name"]).strip(),
            "type": etype, "compartment": comp,
            "data": e.get("data") if isinstance(e.get("data"), dict) else {},
            "note": str(e.get("note", "")).strip(),
            "uncertain": bool(e.get("uncertain")),
            "source": _norm_sources(e.get("source")),
        })
    return out


def normalize_edges(raw_edges, entity_ids):
    out, used = [], set()
    for i, r in enumerate(raw_edges or []):
        if not isinstance(r, dict):
            continue
        fid, tid = str(r.get("from", "")), str(r.get("to", ""))
        if not fid or not tid:
            continue
        if fid not in entity_ids or tid not in entity_ids:
            continue
        rid = str(r.get("id") or ("r%d" % (i + 1)))
        if rid in used:
            rid = rid + "_%d" % i
        used.add(rid)
        etype = (None, None)
        if isinstance(r.get("type"), str):
            key = r["type"].strip().lower()
            etype = EDGE_VERB_MAP.get(key, (None, None))
            if etype[0] is None and key in EDGE_TYPES:
                etype = (key, str(r.get("subtype", "")) or "")
        t, sub = etype if etype[0] else ("binding", "")
        out.append({
            "id": rid, "from": fid, "to": tid,
            "type": t, "subtype": str(r.get("subtype", "") or sub),
            "evidence": str(r.get("evidence", "moderate") or "moderate"),
            "uncertain": bool(r.get("uncertain")),
            "label": str(r.get("label", "")).strip(),
            "note": str(r.get("note", "")).strip(),
            "feedback": bool(r.get("feedback")),
            "source": _norm_sources(r.get("source")),
        })
    return out


def _norm_sources(src):
    out = []
    if isinstance(src, str):
        out = [{"ref": src, "kind": "material"}]
    elif isinstance(src, list):
        for s in src:
            if isinstance(s, str):
                out.append({"ref": s, "kind": "material"})
            elif isinstance(s, dict) and s.get("ref"):
                out.append({"ref": str(s["ref"]), "kind": str(s.get("kind", "material")),
                            "line": s.get("line")})
    return out


def normalize_model(raw):
    """Coerce a raw dict (from extract.py, agent edit or JSON file) into a valid model."""
    raw = raw or {}
    entities = normalize_entities(raw.get("entities"))
    ids = {e["id"] for e in entities}
    edges = normalize_edges(raw.get("edges"), ids)
    legend = raw.get("legend")
    if not isinstance(legend, dict) or not legend:
        legend = default_legend()
    else:
        base = default_legend()
        for k, v in legend.items():
            if isinstance(v, dict) and isinstance(base.get(k), dict):
                base[k].update({kk: vv for kk, vv in v.items() if vv is not None})
            else:
                base[k] = v
        legend = base
    return {
        "case_id": str(raw.get("case_id", "") or ""),
        "title": str(raw.get("title", "") or ""),
        "example": bool(raw.get("example")),
        "entities": entities,
        "edges": edges,
        "legend": legend,
        "layout": raw.get("layout") if isinstance(raw.get("layout"), dict) else {},
        "extraction": raw.get("extraction") if isinstance(raw.get("extraction"), dict) else {},
    }


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def dump_json(obj, path, indent=2):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=indent)


def rel(p, base):
    p = os.path.abspath(p)
    base = os.path.abspath(base)
    try:
        return os.path.relpath(p, base).replace("\\", "/")
    except ValueError:
        return p