# -*- coding: utf-8 -*-
"""Deterministic layered layout for pathway diagrams (v2).

Layout rules (see references/mechanism-spec.md §4 for the science behind them):
  * compartments are horizontal bands ordered by rank
      extracellular(0) -> membrane(1) -> cytoplasm(2) -> nucleus(3);
    nucleus is drawn as an inner box inside the cytoplasm band.
  * entities are placed in their band, evenly spaced, order kept stable.
  * every edge is routed as an orthogonal polyline:
      - downward edges (target rank > source rank):
          exit the source box, go down, elbow at the mid gap, enter the target;
          multiple edges leaving one node spread across its bottom edge;
      - same-compartment edges: horizontal connectors at slightly shifted lanes;
      - feedback / upward edges: routed on the right side of the drawing.
  * the same layout dict feeds BOTH the editable-SVG backend and the
    matplotlib PNG/PDF preview, so the two representations cannot drift.
  * the algorithm is a pure function of the model: same input, same output
    (determinism probe in result.self_check.determinism).
"""
from model import COMPARTMENT_DEFAULT, COMPARTMENT_ALIASES, clamp

BAND_MARGIN = 10
NODE_H = 52
MIN_W, MAX_W = 84, 220
LEGEND_W = 330
CANVAS_DEFAULT = {"width": 1200, "height": 900}


def _node_w(name):
    # CJK chars are wider; width scales with label length
    eff = sum(17 if ord(ch) > 0x2E7F else 9.5 for ch in name)
    return int(clamp(eff + 34, MIN_W, MAX_W))


def compute_layout(model, canvas=None):
    canvas = dict(CANVAS_DEFAULT if canvas is None else canvas)
    W, H = canvas["width"], canvas["height"]
    warnings = []
    x0, x1 = 36, W - LEGEND_W - 24          # drawing area
    bands_top, bands_bottom = 128, H - 116  # title above, footer below

    # ---------------- compartments ----------------
    comp_specs = dict(COMPARTMENT_DEFAULT)
    user_comps = (model.get("layout") or {}).get("compartments") or []
    for c in user_comps:
        if isinstance(c, dict) and c.get("id"):
            cid = COMPARTMENT_ALIASES.get(str(c["id"]).strip().lower(),
                                          str(c["id"]).strip().lower())
            merged = dict(comp_specs.get(cid, {}))
            for kk, vv in c.items():
                if vv is not None and kk != "id":
                    merged[kk] = vv
            comp_specs[cid] = merged

    used = []
    for e in model["entities"]:
        if e["compartment"] not in used:
            used.append(e["compartment"])
    for c in used:
        if c not in comp_specs:
            comp_specs[c] = {"zh": c, "en": c, "rank": 9,
                             "fill": "#FDFEFE", "stroke": "#B3B6B7", "height": 150}
            warnings.append("未识别区室 '%s'（按通用区室绘制，请核对拼写）" % c)
    bands = sorted(used, key=lambda c: float(comp_specs[c].get("rank", 9)))

    # nucleus inside cytoplasm: enlarge cytoplasm, keep nucleus as inner box
    nucleus_in = "cytoplasm" in bands and "nucleus" in bands
    if nucleus_in:
        comp_specs["cytoplasm"]["height"] += (
            comp_specs["nucleus"].get("height", 170) + 34)

    total_h = sum(float(comp_specs[c].get("height", 150)) for c in bands) or 1
    scale = (bands_bottom - bands_top) / total_h
    y = bands_top
    band_rects = {}
    for c in bands:
        h = max(64, float(comp_specs[c].get("height", 150)) * scale)
        band_rects[c] = {
            "id": c,
            "label_zh": comp_specs[c].get("zh", c),
            "label_en": comp_specs[c].get("en", c),
            "rect": (x0, y, x1 - x0, h),
            "fill": comp_specs[c].get("fill", "#FFFFFF"),
            "stroke": comp_specs[c].get("stroke", "#B3B6B7"),
        }
        y += h

    # ---------------- entities ----------------
    inner = None
    if nucleus_in:
        cx, cy, cw, chh = band_rects["cytoplasm"]["rect"]
        inner_h = band_rects["nucleus"]["rect"][3]
        inset = 26
        ix = cx + inset
        iy = cy + chh - inner_h - inset
        band_rects["nucleus"]["rect"] = (ix, iy, cw - 2 * inset, inner_h)
        band_rects["nucleus"]["inside"] = True
        inner = band_rects["nucleus"]

    ent_layout = {}
    for c in bands:
        ents = [e for e in model["entities"] if e["compartment"] == c]
        if not ents:
            continue
        bx, by, bw, bh = band_rects[c]["rect"]
        n = len(ents)
        gap = bw / (n + 1)
        maxw = clamp(bw / n - 18, MIN_W, MAX_W)
        inner_rect = inner["rect"] if (inner and c == "nucleus") else None
        for k, e in enumerate(ents):
            w = min(_node_w(e["name"]), maxw)
            hh = min(NODE_H, bh - 2 * BAND_MARGIN - 6)
            if inner_rect:
                ix, iy, iw, ih = inner_rect
                half_w = (iw - w) / 2.0
                if n == 1:
                    nx = ix + iw / 2.0 - w / 2.0
                else:
                    nx = ix + (iw - w) * (k + 1) / (n + 1)
                cy = iy + (ih - hh) / 2.0
                ent_layout[e["id"]] = {
                    "id": e["id"], "name": e["name"], "type": e["type"],
                    "compartment": c, "rect": (nx, cy, w, hh),
                    "style": _ent_style(e),
                    "data": e.get("data") or {}, "note": e.get("note", ""),
                    "source": e.get("source", []),
                }
                continue
            cx = bx + gap * (k + 1) - w / 2.0
            cy = by + bh / 2.0 - hh / 2.0
            if c == "membrane" and e["type"] != "small_molecule":
                cy = max(by + 4, by + (bh - hh) / 2.0)
            ent_layout[e["id"]] = {
                "id": e["id"], "name": e["name"], "type": e["type"],
                "compartment": c, "rect": (cx, cy, w, hh),
                "style": _ent_style(e),
                "data": e.get("data") or {}, "note": e.get("note", ""),
                "source": e.get("source", []),
            }

    # ---------------- edges ----------------
    exit_used = {}   # entity id -> count of downward edges leaving it
    lane_used = {}   # (src_comp, dst_comp) -> lane count (same-band / feedback)
    edge_layout = {}
    rank_of = {c: float(comp_specs[c].get("rank", 9)) for c in bands}

    for r in model["edges"]:
        s = ent_layout.get(r["from"])
        d = ent_layout.get(r["to"])
        if not s or not d:
            warnings.append("边 %s 端点缺失：%s -> %s（已跳过）" % (r["id"], r["from"], r["to"]))
            continue
        rank_s = rank_of.get(s["compartment"], 9)
        rank_d = rank_of.get(d["compartment"], 9)
        base = {"id": r["id"], "from": r["from"], "to": r["to"],
                "type": r["type"], "evidence": r.get("evidence", "moderate"),
                "subtype": r.get("subtype", ""),
                "style": _edge_style(r),
                "label": r.get("label", ""),
                "source": r.get("source", []), "note": r.get("note", ""),
                "side_route": False, "feedback": False}

        if r.get("feedback") or rank_d < rank_s:
            lane = lane_used.get("side", 0)
            lane_used["side"] = lane + 1
            pts, head = _route_side(s, d, x1, lane * 18)
            base.update({"points": pts, "head": head, "side_route": True,
                         "feedback": True})
        elif rank_d == rank_s:
            lane = lane_used.get(s["compartment"], 0)
            lane_used[s["compartment"]] = lane + 1
            pts, head = _route_horizontal(s, d, lane * 12)
            base.update({"points": pts, "head": head})
        else:
            idx = exit_used.get(r["from"], 0)
            exit_used[r["from"]] = idx + 1
            pts, head = _route_down(s, d, idx)
            base.update({"points": pts, "head": head})
        edge_layout[r["id"]] = base

    return {
        "canvas": canvas,
        "compartments": [band_rects[c] for c in bands],
        "entities": ent_layout,
        "edges": edge_layout,
        "rank_of": rank_of,
        "warnings": warnings,
    }


def _ent_style(e):
    return {"type": e["type"], "italic": bool(e["type"] == "gene"),
            "double": bool(e["type"] == "complex"),
            "dash": bool(e["type"] == "rna")}


def _edge_style(r):
    from model import edge_style
    return edge_style(r, None)


def _route_down(s, d, from_idx):
    """Orthogonal top-down route; multiple edges from one source spread across
    its bottom edge."""
    sx, sy, sw, sh = s["rect"]
    dx, dy, dw, dh = d["rect"]
    scx = sx + sw / 2.0
    n_exit = max(1, int(dw / 60))
    span = max(12, sw - 24)
    ex = clamp(sx + 12 + span * (from_idx + 0.5) / (from_idx + 2),
               sx + 4, sx + sw - 4)
    tx = clamp(dx + dw / 2.0, dx + 8, dx + dw - 8)
    ty = dy
    mid = (sy + sh + ty) / 2.0
    pts = [(ex, sy + sh), (ex, mid), (tx, mid), (tx, ty)]
    return pts, (tx, ty)


def _route_horizontal(s, d, lane):
    """Same-compartment connector with lane jitter to reduce overlap."""
    sx, sy, sw, sh = s["rect"]
    dx, dy, dw, dh = d["rect"]
    sy2 = sy + sh / 2.0
    dy2 = dy + dh / 2.0
    ymid = (sy2 + dy2) / 2.0 + (lane * 6 if lane % 2 == 0 else -lane * 6)
    if sx + sw <= dx:          # s left of d: arrow pointing right
        pts = [(sx + sw, sy2), (sx + sw, ymid), (dx, ymid), (dx, dy2)]
        head = (dx, dy2)
    else:                      # d left of s: arrow pointing left
        pts = [(sx, sy2), (sx, ymid), (dx + dw, ymid), (dx + dw, dy2)]
        head = (dx + dw, dy2)
    return pts, head


def _route_side(s, d, x1, off):
    """Feedback / upward edge routed around the right side of the drawing."""
    sx, sy, sw, sh = s["rect"]
    dx, dy, dw, dh = d["rect"]
    scy = sy + sh / 2.0
    dcy = dy + dh / 2.0
    xside = x1 + 16 + off
    pts = [(sx + sw, scy), (xside, scy), (xside, dcy), (dx + dw, dcy)]
    return pts, (dx + dw, dcy)   # head points left-wards into target right edge