# -*- coding: utf-8 -*-
"""Bootstrap entity/relation extractor for mechanism/pathway materials (v2).

Design intent (unchanged from v1, keep accurate over automatic):
Real materials arrive in many shapes.  This extractor is NOT an omniscient NLP
parser: it reads *structured* statements (Markdown tables, `A | verb | B` rows,
bulleted `- A 激活 B（证据）` lines, data-mapping declarations) and turns them
into a *draft* mechanism spec whose every element carries a source (file+line).

The Skill instructs the calling agent to ALWAYS (CP4, SKILL.md):
  1. read the real material files first (CP1),
  2. run this extractor to get a draft,
  3. verify every entity/edge against the actual text (fix, split, merge,
     disambiguate gene vs protein, decide evidence strength, mark feedback),
  4. record every manual correction in change_records / uncertainty.

If the material is pure prose without structured statements the extractor
reports method="manual-required" so the agent builds the spec by hand
(scripts/main.py --model-file model.json).
"""
import os
import re
import json

from model import (EDGE_VERB_MAP, EDGE_TYPES, NODE_TYPE_ALIASES,
                   COMPARTMENT_ALIASES, EVIDENCE_WIDTH)

SKIP_ENTITY_HEADERS = {"名称", "名字", "实体", "name", "names", "entity", "entities"}
VERB_KEYS = set(EDGE_VERB_MAP) | set(EDGE_TYPES)
VERB_RE = re.compile(
    r"(激活|促进|正向调控|磷酸化|去磷酸化|泛素化|甲基化|乙酰化|糖基化|修饰|降解|"
    r"抑制|阻断|负向调控|结合|互作|募集|转位|转运|内化|"
    r"activate|activates|promote|promotes|inhibit|inhibits|repress|block|blocks|"
    r"bind|binds|recruit|recruits|interact|phosphorylate|phosphorylates|"
    r"ubiquitinate|methylate|translocate|translocates)",
    re.IGNORECASE,
)
DATA_MAP_RE = re.compile(r"数据映射\s*[:：]\s*(?P<phrase>[^\n]{4,120})", re.I)
HEX_RE = re.compile(r"#([0-9A-Fa-f]{6})")


def read_text_files(paths):
    """Return [(abs_path, filename, [lines])] for text-like files; skips binaries."""
    out = []
    for p in paths:
        if not os.path.isfile(p):
            continue
        name = os.path.basename(p)
        if name.endswith((".png", ".jpg", ".jpeg", ".pdf", ".svg", ".gif", ".zip",
                          ".fcs", ".tif", ".tiff", ".xlsx", ".pptx", ".docx")):
            continue
        try:
            with open(p, "r", encoding="utf-8", errors="replace") as fh:
                lines = [ln.rstrip("\r\n") for ln in fh]
            out.append((p, name, lines))
        except Exception:
            continue
    return out


def _strip_table_row(line):
    s = line.strip()
    if s.startswith(("|", "-", "*", "•", "·")):
        s = s.lstrip("|-*•· \t")
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip().strip("`") for c in s.split("|")]


def _parse_data_cell(cell):
    d = {}
    for kv in cell.split(";"):
        kv = kv.strip()
        if not kv or "=" not in kv:
            continue
        k, _, v = kv.partition("=")
        d[k.strip()] = v.strip()
    return d


def _norm_verb(v):
    key = v.lower()
    if key in EDGE_TYPES:
        return key, ""
    hit = EDGE_VERB_MAP.get(v) or EDGE_VERB_MAP.get(key)
    if hit is None:
        for k2, tup in EDGE_VERB_MAP.items():
            if k2 in v.lower() or v.lower() in k2:
                hit = tup
                break
    return (hit if hit else ("binding", ""))


def extract(lines, src_ref=""):
    """Extract a draft mechanism spec from text lines.

    Returns {"entities", "edges", "legend_overrides", "method", "warnings",
             "sources"}.
    """
    entities, edges = [], []
    warnings, sources = [], []
    by_name = {}
    data_map_override = None
    in_entity_sec = in_rel_sec = False
    t_label = ""

    def add_entity(name, etype, comp, data, note, lineno, force_id=None):
        if name in by_name:
            return by_name[name]
        eid = force_id or "e%d" % (len(entities) + 1)
        by_name[name] = eid
        entities.append({
            "id": eid, "name": name, "type": etype, "compartment": comp,
            "data": data, "note": note,
            "source": [{"ref": src_ref, "kind": "material", "line": lineno}],
        })
        sources.append({"ref": src_ref, "line": lineno, "text": t_label[:180]})
        return eid

    for i, ln in enumerate(lines):
        t = ln.strip()
        t_label = t
        if not t or t.startswith(("```", ">")):
            continue
        if re.match(r"^\s*#{1,6}\s+", ln):
            if re.search(r"实体", t) or re.match(r"^\s*#{1,6}\s+entities?\s*$", t, re.I):
                in_entity_sec, in_rel_sec = True, False
            elif (re.search(r"关系|作用|interaction|regulation", t, re.I) or
                  re.match(r"^\s*#{1,6}\s+relations?\s*$", t, re.I)):
                in_entity_sec, in_rel_sec = False, True
            else:
                in_entity_sec = in_rel_sec = False
            continue

        # ---------- data mapping declaration ----------
        if "数据映射" in t or "data mapping" in t.lower():
            mm = DATA_MAP_RE.search(t)
            if mm:
                phrase = mm.group("phrase").strip()
                over = {}
                mf = re.search(r"([\u4e00-\u9fffA-Za-z0-9_]+)\s*=\s*([\u4e00-\u9fffA-Za-z0-9_]+)", phrase)
                if mf:
                    over["field"] = mf.group(2).strip()
                    over["label_zh"] = phrase
                colors = HEX_RE.findall(phrase)
                if len(colors) >= 2:
                    over["low"], over["high"] = "#" + colors[0], "#" + colors[1]
                elif len(colors) == 1:
                    over["high"] = "#" + colors[0]
                if over:
                    data_map_override = over
            continue

        # ---------- table / bullet-csv rows ----------
        if ("|" in t) or t.startswith("-"):
            cells = _strip_table_row(t)
            loose = not in_entity_sec and not in_rel_sec
            if len(cells) >= 3 and cells[0] and not re.match(r"^[-|:\s]+$", cells[0]) \
                    and cells[0].strip() not in SKIP_ENTITY_HEADERS:
                c0 = cells[0].strip()
                c1 = cells[1].strip()
                cn = len(cells)
                verb_like = c1.lower() in VERB_KEYS or _norm_verb(c1) != ("binding", "")
                ent_like = (c1.lower() in NODE_TYPE_ALIASES or
                            cells[2].strip().lower() in COMPARTMENT_ALIASES)
                if (in_rel_sec or loose) and verb_like:
                    etype, subtype = _norm_verb(c1)
                    if c1.lower() in EDGE_TYPES:
                        etype = c1.lower()
                        subtype = ""
                    ev = "moderate"
                    note = ""
                    if cn >= 4 and cells[3].strip().lower() in EVIDENCE_WIDTH:
                        ev = cells[3].strip().lower()
                        note = cells[4].strip() if cn >= 5 else ""
                    else:
                        note = "；".join(c.strip() for c in cells[3:] if c.strip())
                    edges.append({
                        "id": "r%d" % (len(edges) + 1),
                        "from": c0, "to": cells[2].strip(),
                        "type": etype, "subtype": subtype,
                        "evidence": ev, "note": note,
                        "source": [{"ref": src_ref, "kind": "material", "line": i + 1}],
                    })
                    sources.append({"ref": src_ref, "line": i + 1, "text": t[:200]})
                    continue
                if (in_entity_sec or loose) and ent_like:
                    etype_name = NODE_TYPE_ALIASES.get(c1.lower(), "other")
                    comp = COMPARTMENT_ALIASES.get(cells[2].strip().lower(), cells[2].strip())
                    data = _parse_data_cell(cells[3]) if cn >= 4 else {}
                    note = cells[4].strip() if cn >= 5 else ""
                    add_entity(c0, etype_name, comp, data, note, i + 1)
                continue

        # ---------- sentence rows "- A 动词 B（证据）" ----------
        m = re.match(r"^\s*[-*•·]\s*(.+)$", t)
        if m and "|" not in t:
            body = m.group(1).strip()
            vm = VERB_RE.search(body)
            if vm:
                verb = vm.group(0)
                left = body[:vm.start()].strip(" \t（）()[]（）()")
                right = body[vm.end():].strip()
                right_no_par = re.split(r"[（(]", right)[0].strip().rstrip("，。;；")
                if left and right_no_par:
                    etype, subtype = _norm_verb(str(verb))
                    ev = "moderate"
                    m_ev = re.search(r"(强|中|弱|strong|moderate|weak)", body[vm.end():])
                    if m_ev:
                        ev = {"强": "strong", "中": "moderate", "弱": "weak",
                              "strong": "strong", "moderate": "moderate",
                              "weak": "weak"}[m_ev.group(1).lower()]
                    edges.append({
                        "id": "r%d" % (len(edges) + 1),
                        "from": left, "to": right_no_par,
                        "type": etype, "subtype": subtype,
                        "evidence": ev, "note": body[len(right_no_par):] if right not in (right_no_par,) else "",
                        "source": [{"ref": src_ref, "kind": "material", "line": i + 1}],
                    })
                    sources.append({"ref": src_ref, "line": i + 1, "text": t[:200]})
                    continue

    # ---------- second pass: "- 区室（name）：名称（类型）" style ----------
    for i, ln in enumerate(lines):
        t = ln.strip()
        m = re.match(r"^\s*[-*•·]\s*([^-:：|]{1,40})[：:]\s*(.+)$", t)
        if not m or "|" in t:
            continue
        left, right = m.group(1).strip(), m.group(2).strip()
        comp = None
        mc = re.search(r"[（(]([^）)]+)[）)]", left)
        if mc:
            comp = COMPARTMENT_ALIASES.get(mc.group(1).strip().lower())
        if comp is None:
            comp = re.sub(r"[（(][^）)]+[）)]", "", left).strip() or None
        if comp is None:
            comp = "cytoplasm"
        mm = re.match(r"^(.+?)[（(]([^）)]+)[）)]\s*$", right)
        name, etype = (mm.group(1).strip(), NODE_TYPE_ALIASES.get(mm.group(2).strip().lower(), "protein")) if mm \
            else (right, "protein")
        # require at least one structural anchor: a compartment in the left
        # label, or a typed name on the right; otherwise it is prose, not an
        # entity declaration (e.g. "信号流向：…" constraint lines are skipped)
        if mc is None and mm is None:
            continue
        if name and name not in by_name and len(name) <= 40:
            eid = "e%d" % (len(entities) + 1)
            by_name[name] = eid
            entities.append({
                "id": eid, "name": name, "type": etype, "compartment": comp,
                "data": {}, "note": t[:160],
                "source": [{"ref": src_ref, "kind": "material", "line": i + 1}],
            })
            sources.append({"ref": src_ref, "line": i + 1, "text": t[:200]})

    # ---------- result ----------
    overrides = {"data_mapping": data_map_override} if data_map_override else {}
    for e in edges:
        if e["evidence"] not in EVIDENCE_WIDTH:
            e["evidence"] = "moderate"
    return {"entities": entities, "edges": edges,
            "legend_overrides": overrides,
            "method": "auto-draft" if (entities or edges) else "manual-required",
            "warnings": warnings, "sources": sources}


def draft_model(material_files, src_ref=None):
    """Run extraction over text files and merge into one draft spec."""
    agg = {"entities": [], "edges": [], "warnings": [], "sources": [],
           "method": "auto-draft"}
    for path, name, lines in read_text_files(material_files):
        ref = src_ref or name
        r = extract(lines, src_ref=ref)
        agg["entities"].extend(r["entities"])
        agg["edges"].extend(r["edges"])
        agg["warnings"].extend("[%s] %s" % (name, w) for w in r["warnings"])
        agg["sources"].extend(r["sources"])
        if r["method"] == "manual-required":
            agg["method"] = "manual-required"
        if r.get("legend_overrides", {}).get("data_mapping"):
            agg.setdefault("legend_overrides", {})["data_mapping"] = \
                r["legend_overrides"]["data_mapping"]
    by_name = {}
    for e in agg["entities"]:
        if e["name"] not in by_name:
            by_name[e["name"]] = "e%d" % (len(by_name) + 1)
        e["id"] = by_name[e["name"]]
    name_to_id = {e["name"]: e["id"] for e in agg["entities"]}
    kept = []
    for r in agg["edges"]:
        fid, tid = name_to_id.get(r["from"]), name_to_id.get(r["to"])
        if fid and tid:
            r["from"], r["to"] = fid, tid
            kept.append(r)
        else:
            agg["warnings"].append("边 %s → %s 无法解析端点（实体名不存在），已跳过"
                                   % (r["from"], r["to"]))
    agg["edges"] = kept
    return agg


if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    for f in sys.argv[1:] or ["../examples/materials/example_material.md"]:
        print(json.dumps(draft_model([os.path.abspath(f)]), ensure_ascii=False, indent=2))