#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Layout engine for relationship schematics.

Computes positions/sizes for entity nodes and group boxes from the ER
manifest. The SAME layout object is consumed by both the hand-authored
editable SVG (svgbuilder.py) and the matplotlib preview/PDF renderer
(render.py), which is what keeps the preview mirror faithful to the
editable source.

Layout families
---------------
* layered  — left → right tiers (cascades, pathways, pipelines)
* hierarchy— top → bottom tree (taxonomies, inclusion trees)
* cycle    — entities on a circle (feedback loops, cycles)
* grouped  — group boxes drawn from manifest.groups; members laid out
             inside their group
* manual   — entity["pos"] = {"x": .., "y": ..} is honored verbatim;
             everything else is auto-laid-out around the fixed nodes

Only the Python standard library is used.
"""

import math
import os
import sys

# Self-location: helpers live next to this file; make them importable
# regardless of the caller's working directory.
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
from manifest import CANONICAL_KINDS as CANON

# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def est_text_w(text, font_px=16, min_w=96, pad=28):
    """Rough width estimate for a node box that must fit `text`."""
    n = max(len(str(text or "")), 1)
    return max(min_w, int(n * font_px * 0.62) + pad)


def clip_segment_to_rect(cx, cy, px, py, half_w, half_h):
    """Clip the ray from box centre (cx,cy) to point (px,py) at the box
    edge. Returns the point on the box boundary in direction of (px,py).
    Standard slab method; handles the degenerate cases."""
    dx = px - cx
    dy = py - cy
    if abs(dx) < 1e-9 and abs(dy) < 1e-9:
        return (px, py)
    tmin = -1e18
    tmax = 1e18
    if abs(dx) > 1e-12:
        t1 = (-half_w) / dx
        t2 = (+half_w) / dx
        if t1 > t2:
            t1, t2 = t2, t1
        tmin = max(tmin, t1)
        tmax = min(tmax, t2)
    else:
        # direction is vertical within the slab
        if px < cx - half_w or px > cx + half_w:
            # outside the horizontal slab: fall back to nearest corner ray
            px = cx + (half_w if px > cx else -half_w)
    if abs(dy) > 1e-12:
        t1 = (-half_h) / dy
        t2 = (+half_h) / dy
        if t1 > t2:
            t1, t2 = t2, t1
        tmin = max(tmin, t1)
        tmax = min(tmax, t2)
    if tmin > tmax:
        # no slab overlap (should not happen for a ray through the box)
        return (px, py)
    t = tmin if tmin > 0 else (tmax if tmax > 0 else 1.0)
    if t < 0:
        return (px, py)
    return (cx + dx * t, cy + dy * t)


def edge_endpoints(sx, sy, sw, sh, tx, ty, tw, th, x1, y1, x2, y2):
    """Given source rect (sx,sy,sw,sh) and target rect (tx,ty,tw,th) and
    the raw segment (x1,y1)-(x2,y2) between centres, return the trimmed
    endpoints that touch the rect borders (arrows start/end visibly)."""
    scx, scy = sx + sw / 2.0, sy + sh / 2.0
    tcx, tcy = tx + tw / 2.0, ty + th / 2.0
    p1 = clip_segment_to_rect(scx, scy, x2, y2, sw / 2.0, sh / 2.0)
    p2 = clip_segment_to_rect(tcx, tcy, x1, y1, tw / 2.0, th / 2.0)
    # keep a small gap so the marker is clearly visible
    def _step(a, b, d=6.0):
        ax, ay = a
        bx, by = b
        n = math.hypot(bx - ax, by - ay) or 1.0
        return (ax + (bx - ax) / n * d, ay + (by - ay) / n * d)
    p1 = _step(p1, p2)
    p2 = _step(p2, p1)
    return p1, p2


# ---------------------------------------------------------------------------
# Layout computation
# ---------------------------------------------------------------------------

def _dependencies(relations):
    """Pred/succ maps excluding containment edges."""
    pred = {}
    succ = {}
    for r in relations:
        if r.get("_canon") == "containment":
            continue
        pred.setdefault(r["to"], []).append(r["from"])
        succ.setdefault(r["from"], []).append(r["to"])
    return pred, succ


def _assign_layers(entities, relations):
    """Assign an integer layer (0 = leftmost/topmost) to every entity."""
    pred, _ = _dependencies(relations)
    layers = {}
    by_id = {e["id"]: e for e in entities}

    def depth(nid, seen=None):
        seen = set(seen or ())
        if nid in seen:
            return 0                      # cycle guard: break the loop
        if nid in layers:
            return layers[nid]
        ps = [p for p in pred.get(nid, []) if p in by_id]
        if not ps:
            return 0
        d = 1 + max(depth(p, seen | {nid}) for p in ps)
        return d

    for e in entities:
        layers[e["id"]] = depth(e["id"])
    # honour explicit layer hints
    for e in entities:
        hint = e.get("layer")
        if isinstance(hint, (int, float)) and not isinstance(hint, bool):
            layers[e["id"]] = int(hint)
    return layers


def compute_layout(manifest, canvas=None):
    """Return a dict with:
        nodes: {id: {x,y,w,h, layer, col, text, type, source, evidence}}
        groups: {id: {x,y,w,h, label, members}}
        canvas: {"width","height"}
        edges: list of raw segments (id, from, to, kind, canon, label)
    Coordinates are in px; both the SVG builder and matplotlib renderer
    consume them unchanged.
    """
    m = manifest or {}
    entities = m.get("entities") or []
    relations = m.get("relations") or []
    groups = m.get("groups") or []
    style = m.get("style") or {}
    fig_type = m.get("figure_type", "schematic")

    eids = [e["id"] for e in entities]
    by_id = {e["id"]: e for e in entities}

    fonts = style.get("font_size", 16)
    node_w = {}
    node_h = 58

    # ---- manual positions ----
    manual = {}
    for e in entities:
        pos = e.get("pos")
        if isinstance(pos, dict) and pos.get("x") is not None and pos.get("y") is not None:
            manual[e["id"]] = pos

    nodes = {}
    # build auto positions
    if fig_type == "cycle":
        n = max(len(entities), 1)
        cx, cy = 800.0, 450.0
        R = 300.0
        for i, e in enumerate(entities):
            ang = 2 * math.pi * i / n - math.pi / 2
            x = cx + R * math.cos(ang)
            y = cy + R * math.sin(ang)
            w = est_text_w(e.get("name"), fonts, min_w=110)
            nodes[e["id"]] = {"x": x - w / 2, "y": y - node_h / 2, "w": w,
                              "h": node_h, "layer": 0, "col": i,
                              "text": e.get("name"), "type": e.get("type"),
                              "source": e.get("source"), "evidence": e.get("evidence")}
    else:
        layers = _assign_layers(entities, relations)
        if fig_type == "hierarchy":
            # column = layer index (top→down), rows spread vertically
            ncols = max(layers.values()) + 1 if layers else 1
            cols = {}
            for e in entities:
                cols.setdefault(layers[e["id"]], []).append(e["id"])
            max_rows = max((len(v) for v in cols.values()), default=1)
            w0, h0, gapx, gapy = 240.0, 90.0, 120.0, 80.0
            grid_w = max(max_rows, 1) * (w0 + gapx)
            grid_h = ncols * (h0 + gapy)
            for e in entities:
                lyr = layers[e["id"]]
                idx = cols[lyr].index(e["id"])
                x = ((grid_w / 2) - (len(cols[lyr]) * (w0 + gapx)) / 2
                     + idx * (w0 + gapx))
                y = lyr * (h0 + gapy)
                w = est_text_w(e.get("name"), fonts, min_w=w0)
                nodes[e["id"]] = {"x": x, "y": y, "w": w, "h": h0,
                                  "layer": lyr, "col": idx, "text": e.get("name"),
                                  "type": e.get("type"), "source": e.get("source"),
                                  "evidence": e.get("evidence")}
        else:  # layered (left → right)
            ncols = max(layers.values()) + 1 if layers else 1
            cols = {}
            for e in entities:
                cols.setdefault(layers[e["id"]], []).append(e["id"])
            max_rows = max((len(v) for v in cols.values()), default=1)
            w0, h0, gapx, gapy = 240.0, 90.0, 130.0, 70.0
            for e in entities:
                lyr = layers[e["id"]]
                idx = cols[lyr].index(e["id"])
                x = lyr * (w0 + gapx)
                y = ((max_rows * (h0 + gapy)) / 2
                     - (len(cols[lyr]) * (h0 + gapy)) / 2 + idx * (h0 + gapy))
                w = est_text_w(e.get("name"), fonts, min_w=w0)
                nodes[e["id"]] = {"x": x, "y": y, "w": w, "h": h0,
                                  "layer": lyr, "col": idx, "text": e.get("name"),
                                  "type": e.get("type"), "source": e.get("source"),
                                  "evidence": e.get("evidence")}

    # apply manual positions (auto-laid out nodes keep their computed sizes)
    for eid, pos in manual.items():
        if eid in nodes:
            nodes[eid]["x"] = float(pos["x"])
            nodes[eid]["y"] = float(pos["y"])

    # ---- group boxes around their members ----
    group_boxes = {}
    for g in groups:
        members = [mid for mid in g.get("members", []) if mid in nodes]
        if not members:
            continue
        xs = [nodes[mid]["x"] for mid in members]
        ys = [nodes[mid]["y"] for mid in members]
        xe = [nodes[mid]["x"] + nodes[mid]["w"] for mid in members]
        ye = [nodes[mid]["y"] + nodes[mid]["h"] for mid in members]
        pad = 34
        group_boxes[g["id"]] = {
            "x": min(xs) - pad, "y": min(ys) - pad,
            "w": max(xe) - min(xs) + pad * 2,
            "h": max(ye) - min(ys) + pad * 2,
            "label": g.get("label", ""),
            "members": members,
            "source": g.get("source", ""),
            "evidence": g.get("evidence", ""),
            "unknown_members": g.get("_unknown_members", []),
        }

    # ---- canvas ----
    if canvas is None:
        canvas = style.get("canvas")
    if not (isinstance(canvas, dict) and canvas.get("width") and canvas.get("height")):
        margin = 90
        max_x = max((n["x"] + n["w"] for n in nodes.values()), default=0)
        max_y = max((n["y"] + n["h"] for n in nodes.values()), default=0)
        gx = max((gb["x"] + gb["w"] for gb in group_boxes.values()), default=0)
        gy = max((gb["y"] + gb["h"] for gb in group_boxes.values()), default=0)
        width = max(900, int(max_x + margin / 2), int(gx + margin / 2))
        height = max(500, int(max_y + margin / 2), int(gy + margin / 2))
        canvas = {"width": width, "height": height}

    # ---- edges ----
    edges = []
    for r in relations:
        if r["from"] not in nodes or r["to"] not in nodes:
            continue
        if r.get("_canon") == "containment":
            continue  # drawn as group boxes, not arrows
        edges.append({
            "id": r["id"], "from": r["from"], "to": r["to"],
            "kind": r.get("kind"), "canon": r.get("_canon"),
            "arrow": (CANON.get(r.get("_canon")) or {}).get("arrow", "open")
                     if r.get("_canon") else "open",
            "line": (CANON.get(r.get("_canon")) or {}).get("line", "solid")
                    if r.get("_canon") else "solid",
            "label": r.get("label") or r.get("kind") or "",
            "source": r.get("source", ""), "evidence": r.get("evidence", ""),
        })

    return {"nodes": nodes, "groups": group_boxes, "canvas": canvas,
            "edges": edges, "text_px": fonts, "node_h": node_h}