# -*- coding: utf-8 -*-
"""Figure specification + deterministic layout engine.

Turns the extracted ``content`` dict into a geometry-level ``figure_spec``:

    {
      "case_id", "title", "width", "height",
      "palette": [...hex...],
      "font_family": "....",
      "layers": [ordered layer names],
      "elements": [ {kind, layer, x, y, w, h, r, fill, stroke, stroke_width,
                     text, font_size, bold, align, entity_id, src, role, ...} ],
      "legend": [{label, value, unit, color|symbol, match_keys}],
      "scale_bar": {...} | None,
      "reading_order": [panel ids in visual order],
      "panels": [{id, label, label_en, x, y, w, h, points: [], entities: []}],
      "layout_log": [...warnings...],
      "data_encoding": [{data_id, channel, geometry, legend_key}],
      "constraints_used": {...}
    }

Element kinds shared by the SVG builder and preview renderer:
    rect, roundrect, circle, diamond, line, arrow, text,
    label_row (text + optional swatch), bar (length encoding)

Layout is fully deterministic: same content -> same spec.
"""
from __future__ import annotations

import extract as ext
from common import (DEFAULT_PALETTE, estimate_text_width, interpolate,
                     lighten, slug)

FONT_CHAIN = ("Inter", "'Helvetica Neue'", "Helvetica", "Arial",
              "'Microsoft YaHei'", "'PingFang SC'", "'Noto Sans CJK SC'", "sans-serif")
FONT_FAMILY = ", ".join(FONT_CHAIN)

MIN_FONT = 8.0
IDX = {"_n": 0}


def _next_id(kind):
    IDX["_n"] += 1
    return f"{kind}_{IDX['_n']}"


def _panel_label(p):
    lang = "zh"
    return ext.PANEL_LABELS.get(p, p), ext.PANEL_LABELS_EN.get(p, p)


class FigureSpecBuilder:
    def __init__(self, content: dict):
        self.c = content
        self.con = content["constraints"]
        self.W = float(self.con["width"])
        self.H = float(self.con["height"])
        self.palette = list(content.get("constraints", {}).get("palette") or DEFAULT_PALETTE)
        self.elements = []
        self.layout_log = []
        self.legend = []
        self.scale_bar = None
        self.data_encoding = []
        self.reading_order = []
        self.panels_meta = []
        self.layers = ["background", "panels", "entities", "relations",
                       "data", "legend", "annotations"]

    # ------------------------------------------------------------------
    def add(self, layer, **kw):
        el = {"id": _next_id("el"), "layer": layer}
        el.update({k: v for k, v in kw.items() if v is not None})
        self.elements.append(el)
        return el

    # ------------------------------------------------------------------
    def build(self) -> dict:
        self._background()
        rects = self._panel_rects()
        if self.c["title"]:
            self._header()
        self._panels(rects)
        self._footer(rects)
        return self._spec()

    # ------------------------------------------------------------------
    def _background(self):
        self.add("background", kind="rect",
                 x=0, y=0, w=self.W, h=self.H,
                 fill="#FFFFFF", stroke="none", role="canvas")

    def _header(self):
        title = self.c["title"] or "Graphical Abstract"
        y = 22
        self.add("panels", kind="text", x=24, y=y, w=self.W - 48, h=34,
                 text=title, font_size=26, bold=True, fill="#1A1A1A",
                 role="title", align="left")
        tag = f"case: {self.c['case_id']}"
        self.add("panels", kind="text", x=24, y=y + 34, w=self.W - 48, h=16,
                 text=tag, font_size=11, bold=False, fill="#666666",
                 role="case_tag", align="left")
        self.add("panels", kind="line", x1=24, y1=y + 56, x2=self.W - 24, y2=y + 56,
                 stroke="#BBBBBB", stroke_width=1, role="header_rule")

    # ------------------------------------------------------------------
    def _panel_rects(self) -> dict:
        m = float(self.con["margin"])
        W, H = self.W, self.H
        header_bottom = 24 + 56 + 14 if self.c["title"] else m
        footer_top = H - 92
        top, bottom = header_bottom + 8, footer_top - 8
        gap = 16.0
        cols_w = [250.0, 250.0, 390.0, 270.0]
        total = sum(cols_w) + gap * 3
        scale = (W - 2 * m) / total
        cols_w = [w * scale for w in cols_w]
        xs = []
        x = m
        for w in cols_w:
            xs.append(x)
            x += w + gap
        panels = {
            "question":  {"x": xs[0], "w": cols_w[0]},
            "method":    {"x": xs[1], "w": cols_w[1]},
            "results":   {"x": xs[2], "w": cols_w[2]},
            "conclusion": {"x": xs[3], "w": cols_w[3]},
        }
        for pid in ext.VALID_PANELS:
            panels[pid]["y"] = top
            panels[pid]["h"] = bottom - top
        self._panel_h = bottom - top
        return panels

    # ------------------------------------------------------------------
    def _panels(self, rects: dict):
        order = ext.VALID_PANELS  # question -> method -> results -> conclusion
        self.reading_order = list(order)
        for i, pid in enumerate(order, start=1):
            r = rects[pid]
            self._panel_frame(pid, i, r)

        # entities per panel (already inferred by extract)
        by_panel = {pid: [] for pid in order}
        for e in self.c["entities"]:
            by_panel.get(e["panel"] or "question", []).append(e)

        for pid in order:
            ents = by_panel[pid]
            pts = self.c["panels"].get(pid, [])
            self._panel_content(pid, rects[pid], pts, ents, order.index(pid) + 1)

        self._flow_arrows(rects, order)

    # ------------------------------------------------------------------
    def _panel_frame(self, pid, number, r):
        fill = lighten(self.palette[(number - 1) % len(self.palette)], 0.82)
        border = self.palette[(number - 1) % len(self.palette)]
        self.add("panels", kind="roundrect", x=r["x"], y=r["y"], w=r["w"], h=r["h"],
                 r=10, fill=fill, stroke=border, stroke_width=1.5,
                 entity_id=None, role=f"panel:{pid}", panel=pid)
        self.add("panels", kind="roundrect", x=r["x"], y=r["y"], w=7, h=r["h"],
                 r=3, fill=border, stroke="none", role=f"panel_rail:{pid}", panel=pid)
        zh, en = _panel_label(pid)
        self.add("annotations", kind="text", x=r["x"] + 16, y=r["y"] + 22, w=r["w"] - 40, h=20,
                 text=f"{number}. {zh}  ({en})", font_size=14, bold=True,
                 fill=border, role=f"panel_title:{pid}", panel=pid)
        self.add("panels", kind="text", x=r["x"] + 16, y=r["y"] + r["h"] - 20, w=r["w"] - 32, h=14,
                 text=f"panel {pid}", font_size=9, fill="#999999",
                 role=f"panel_tag:{pid}", panel=pid)

    # ------------------------------------------------------------------
    def _panel_content(self, pid, r, points, entities, number):
        inner_x = r["x"] + 18
        inner_w = r["w"] - 36
        cursor = r["y"] + 46

        # entity cards
        for e in entities[:4]:
            card_h = 58.0
            if cursor + card_h > r["y"] + r["h"] - 46:
                self.layout_log.append(
                    f"panel {pid}: 实体卡片溢出（{e['name']}），已截断显示，请精简面板要点。")
                break
            self.add("entities", kind="roundrect", x=inner_x, y=cursor,
                     w=inner_w, h=card_h, r=8, fill="#FFFFFF",
                     stroke=self.palette[number % len(self.palette)], stroke_width=1.2,
                     entity_id=e["id"], src=e.get("src"), role=f"entity:{e['id']}", panel=pid)
            cx = inner_x + 22
            cy = cursor + card_h / 2
            self._entity_icon(cx, cy, e, number)
            name = e["name"]
            fs = 13.0
            while estimate_text_width(name, fs) > inner_w - 60 and fs > MIN_FONT:
                fs -= 0.5
            self.add("entities", kind="text", x=inner_x + 44, y=cursor + 12,
                     w=inner_w - 52, h=fs + 4, text=name, font_size=fs, bold=True,
                     fill="#222222", entity_id=e["id"], src=e.get("src"),
                     role=f"entity_label:{e['id']}", panel=pid)
            sub = e.get("type") or "object"
            note = (e.get("note") or "").strip()
            if note:
                sub = note if len(note) <= 40 else note[:37] + "..."
            self.add("entities", kind="text", x=inner_x + 44, y=cursor + 12 + fs + 3,
                     w=inner_w - 52, h=16, text=sub, font_size=10,
                     fill="#777777", entity_id=e["id"], src=e.get("src"),
                     role=f"entity_note:{e['id']}", panel=pid)
            cursor += card_h + 10

        # relations inside the panel (compact arrow rows)
        # relations genuinely associated with this panel: endpoints in panel
        panel_entity_ids = {e["id"] for e in entities}
        rels = [rl for rl in self.c["relations"]
                if (rl.get("from_id") in panel_entity_ids or rl.get("to_id") in panel_entity_ids)]
        for rl in rels[:3]:
            if cursor + 26 > r["y"] + r["h"] - 46:
                break
            label = rl.get("label") or rl.get("kind") or "→"
            color = "#B23A3A" if rl.get("kind") == "negative" else self.palette[number % len(self.palette)]
            mid_y = cursor + 12
            self.add("relations", kind="arrow", x1=inner_x, y1=mid_y,
                     x2=inner_x + inner_w, y2=mid_y, stroke=color, stroke_width=2.0,
                     src=rl.get("src"), role=f"relation:{rl['id']}", panel=pid)
            self.add("relations", kind="text", x=inner_x + 6, y=mid_y - 13,
                     w=inner_w - 12, h=12, text=f"{rl['from']} → {rl['to']}"
                     + (f" ({label})" if rl.get("label") else ""),
                     font_size=9, fill="#444444", src=rl.get("src"),
                     role=f"relation_label:{rl['id']}", panel=pid)
            cursor += 26

        # panel bullet points
        for pt in points[:6]:
            text = pt if len(pt) <= 60 else pt[:57] + "..."
            fs = 10.5
            while estimate_text_width(text, fs) > inner_w and fs > MIN_FONT:
                fs -= 0.5
            self.add("panels", kind="text", x=inner_x, y=cursor, w=inner_w, h=fs + 6,
                     text="• " + text, font_size=fs, fill="#333333",
                     role=f"point:{pid}", panel=pid)
            cursor += fs + 8

        if pid == "results":
            self._data_tiles(pid, r, entities)

    # ------------------------------------------------------------------
    def _entity_icon(self, cx, cy, e, number):
        color = "#FFFFFF"
        stroke = self.palette[number % len(self.palette)]
        shape = e.get("shape", "circle")
        ent_id = e["id"]
        r = 10.0
        if shape == "circle":
            self.add("entities", kind="circle", cx=cx, cy=cy, r=r, fill=stroke,
                     stroke="none", entity_id=ent_id, src=e.get("src"), role="icon")
        elif shape in ("rounded", "rect"):
            k = "roundrect" if shape == "rounded" else "rect"
            self.add("entities", kind=k, x=cx - r, y=cy - r * 0.75, w=r * 2, h=r * 1.5,
                     r=4 if k == "roundrect" else None, fill=stroke, stroke="none",
                     entity_id=ent_id, src=e.get("src"), role="icon")
        elif shape == "diamond":
            pts = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
            self.add("entities", kind="polygon", points=pts, fill=stroke, stroke="none",
                     entity_id=ent_id, src=e.get("src"), role="icon")
        else:  # hex
            import math
            pts = [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
                   for a in (90, 150, 210, 270, 330, 30)]
            self.add("entities", kind="polygon", points=pts, fill=stroke, stroke="none",
                     entity_id=ent_id, src=e.get("src"), role="icon")

    # ------------------------------------------------------------------
    def _data_tiles(self, pid, r, entities):
        data = self.c["data"]
        if not data:
            return
        order = [d for d in data if d.get("kind") == "bar_length"]
        color_ok = [d for d in data if d.get("kind") == "color_scale"]
        done = [d["id"] for d in data if d.get("kind") not in ("bar_length", "color_scale")]

        # tile grid for bar_length encodings inside the results panel
        tiles = self._grid_tiles(r, len(order))
        for tile, d in zip(tiles, order):
            self._bar_tile(tile, d, pid)

        # color_scale swatch strip (whole panel width)
        if color_ok:
            self._color_strip(r, color_ok, pid)

        for kind in ("area", "value_label"):
            for d in data:
                if d.get("kind") == kind:
                    self._simple_datum(r, d, pid)

    def _grid_tiles(self, r, n):
        if n <= 0:
            return []
        cols = 1 if n <= 2 else (2 if n <= 6 else 3)
        rows = (n + cols - 1) // cols
        tw = (r["w"] - 36 - 14 * (cols - 1)) / cols
        th = 120.0
        tiles = []
        for i in range(n):
            c = i % cols
            row = i // cols
            tiles.append({
                "x": r["x"] + 18 + c * (tw + 14),
                "y": r["y"] + r["h"] - th - 24 - row * (th + 10),
                "w": tw, "h": th,
            })
        return tiles

    def _bar_tile(self, tile, d, pid):
        x, y, w, h = tile["x"], tile["y"], tile["w"], tile["h"]
        color = self.palette[3 % len(self.palette)]
        self.add("data", kind="roundrect", x=x, y=y, w=w, h=h, r=8,
                 fill="#FFFFFF", stroke="#CCCCCC", stroke_width=1,
                 src=d.get("src"), role=f"datum:{d['id']}", panel=pid)
        label = d["label"]
        fs = 12.0
        while estimate_text_width(label, fs) > w - 16 and fs > MIN_FONT:
            fs -= 0.5
        self.add("data", kind="text", x=x + 8, y=y + 6, w=w - 16, h=fs + 4,
                 text=label, font_size=fs, bold=True, fill="#222222",
                 src=d.get("src"), role=f"datum_label:{d['id']}", panel=pid)
        if d.get("value") is None:
            self.add("data", kind="text", x=x + 8, y=y + h - 34, w=w - 16, h=16,
                     text="（数值缺失，见 uncertainty）", font_size=10, fill="#B23A3A",
                     src=d.get("src"), role=f"datum_missing:{d['id']}", panel=pid)
            self.add("data", kind="roundrect", x=x + 8, y=y + h - 56, w=w - 16, h=18,
                     r=3, fill="#EEEEEE", stroke="#999999", stroke_width=1,
                     src=d.get("src"), role=f"datum_bar_missing:{d['id']}", panel=pid)
            return
        bmax = 0.0
        for dd in self.c["data"]:
            if dd.get("kind") == "bar_length" and dd.get("value") is not None:
                bmax = max(bmax, float(dd["value"]))
        if bmax <= 0:
            bmax = 1.0
        val = float(d["value"])
        bar_h = 34.0
        bar_y = y + h - 58
        bar_w_max = w - 16
        frac = max(0.02, min(1.0, val / bmax))
        self.add("data", kind="rect", x=x + 8, y=bar_y + bar_h * (1 - frac),
                 w=bar_w_max, h=bar_h * frac, fill=color, stroke=color,
                 src=d.get("src"), role=f"datum_bar:{d['id']}", panel=pid)
        unit_txt = f" {d['unit']}" if d.get("unit") else ""
        self.add("data", kind="text", x=x + 8, y=bar_y + bar_h + 4, w=w - 16, h=16,
                 text=f"{val:g}{unit_txt}", font_size=11, bold=True, fill="#111111",
                 src=d.get("src"), role=f"datum_value:{d['id']}", panel=pid)
        self.data_encoding.append({
            "data_id": d["id"], "label": d["label"], "channel": "bar_length",
            "geometry": f"bar {val:g}{unit_txt} (length ∝ value, max={bmax:g})",
            "legend_key": d["label"],
        })
        self._legend_entry(d["label"], f"{val:g}{unit_txt}", color, "bar")

    # ------------------------------------------------------------------
    def _color_strip(self, r, color_ok, pid):
        data = color_ok
        values = [float(d["value"]) for d in data if d.get("value") is not None]
        if not values:
            return
        vmin, vmax = min(values), max(values)
        x0, y0 = r["x"] + 18, r["y"] + 16
        sw = (r["w"] - 36) / len(data)
        for d in data:
            if d.get("value") is None:
                continue
            t = (float(d["value"]) - vmin) / (vmax - vmin) if vmax > vmin else 0.5
            color = interpolate("#FFF3E0", "#C4520A", t)
            self.add("data", kind="rect", x=x0, y=y0, w=sw - 4, h=18, fill=color,
                     stroke="#999999", stroke_width=0.5,
                     src=d.get("src"), role=f"datum_swatch:{d['id']}", panel=pid)
            unit = f" {d['unit']}" if d.get("unit") else ""
            self.add("data", kind="text", x=x0, y=y0 - 12, w=sw, h=12,
                     text=f"{d['label']}: {float(d['value']):g}{unit}", font_size=8,
                     fill="#444444", src=d.get("src"),
                     role=f"datum_swatch_label:{d['id']}", panel=pid)
            self.data_encoding.append({
                "data_id": d["id"], "label": d["label"], "channel": "color_scale",
                "geometry": f"swatch {(vmin):g}..{vmax:g}, t={t:.2f}",
                "legend_key": "color scale",
            })
            x0 += sw
        self._legend_entry("color scale", f"{vmin:g}…{vmax:g}", "#C4520A", "gradient")

    def _simple_datum(self, r, d, pid):
        x, y = r["x"] + 18, r["y"] + 46
        unit = f" {d['unit']}" if d.get("unit") else ""
        txt = f"{d['label']}: {d['value'] if d.get('value') is not None else '?'}{unit}"
        self.add("data", kind="text", x=x, y=y, w=r["w"] - 36, h=16,
                 text=txt, font_size=12, bold=False, fill="#222222",
                 src=d.get("src"), role=f"datum_note:{d['id']}", panel=pid)

    # ------------------------------------------------------------------
    def _flow_arrows(self, rects, order):
        if not self.con.get("flow_arrows", True):
            return
        xs = [rects[p]["x"] for p in order[:3]]
        widths = [rects[p]["w"] for p in order[:3]]
        gap = 16.0
        y = self._panel_h / 2 + rects["question"]["y"]
        for i, p in enumerate(order[:3]):
            x1 = xs[i] + widths[i] + 2
            x2 = x1 + gap - 2
            self.add("annotations", kind="arrow", x1=x1, y1=y, x2=x2, y2=y,
                     stroke="#888888", stroke_width=2.0,
                     role=f"flow:{p}->{order[i+1]}")

    # ------------------------------------------------------------------
    def _footer(self, rects):
        y = self.H - 76
        self.add("legend", kind="line", x1=24, y1=y - 8, x2=self.W - 24, y2=y - 8,
                 stroke="#DDDDDD", stroke_width=1, role="footer_rule")
        lx = 24
        self.add("legend", kind="text", x=lx, y=y - 2, w=110, h=16,
                 text="图例 / Legend", font_size=11, bold=True, fill="#333333",
                 role="legend_title")
        lx += 116
        for entry in self.legend[:6]:
            txt = f"{entry['label']}  {entry['value_text']}"
            fs = 10.0
            while estimate_text_width(txt, fs) > 460 and fs > MIN_FONT:
                fs -= 0.5
            self.add("legend", kind="rect", x=lx, y=y + 2, w=14, h=10,
                     fill=entry["color"], stroke="#666666", stroke_width=0.5,
                     role=f"legend_swatch:{slug(entry['label'])}", legend_key=entry["label"])
            self.add("legend", kind="text", x=lx + 18, y=y, w=self.W - lx - 320, h=14,
                     text=txt, font_size=fs, fill="#444444",
                     role=f"legend_label:{slug(entry['label'])}")
            lx += 24 + estimate_text_width(txt, fs) + 16
            if lx > self.W - 320:
                break
        # scale bar + units
        self.add("annotations", kind="rect", x=self.W - 190, y=y + 2, w=120, h=10,
                 fill="#FFFFFF", stroke="#000000", stroke_width=1.2,
                 role="scale_bar")
        self.add("annotations", kind="text", x=self.W - 190, y=y + 14, w=150, h=12,
                 text="scale bar (rel. units)", font_size=9, fill="#666666",
                 role="scale_bar_label")
        self.scale_bar = {"x": self.W - 190, "y": y + 2, "w": 120, "h": 10,
                          "label": "scale bar (rel. units)",
                          "matches": "relative length encoding"}

    def _legend_entry(self, label, value_text, color, symbol):
        self.legend.append({"label": label, "value_text": value_text,
                            "color": color, "symbol": symbol})

    # ------------------------------------------------------------------
    def _spec(self) -> dict:
        return {
            "case_id": self.c["case_id"],
            "title": self.c["title"],
            "width": self.W,
            "height": self.H,
            "palette": self.palette,
            "font_family": FONT_FAMILY,
            "layers": self.layers,
            "elements": self.elements,
            "legend": self.legend,
            "scale_bar": self.scale_bar,
            "reading_order": self.reading_order,
            "data_encoding": self.data_encoding,
            "layout_log": self.layout_log,
            "constraints_used": {
                k: self.con.get(k) for k in ("width", "height", "dpi", "colorblind",
                                             "flow_arrows", "language", "raster_scale", "pdf")
            },
        }


def build(content: dict) -> dict:
    return FigureSpecBuilder(content).build()