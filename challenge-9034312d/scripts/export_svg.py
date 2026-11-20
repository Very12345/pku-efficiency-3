# -*- coding: utf-8 -*-
"""export_svg.py — 手写分层 SVG 导出（可编辑源文件本体）。

要点：
- 每个实体一个 <g> 组，含 data-entity / data-source / data-kind 属性；
- 文字用 <text> 真实文本（不是路径），可被 Inkscape / Illustrator / 浏览器直接编辑；
- 图层按 背景/箭头/实体/图例/标题 分组，id 命名规范；
- 写完用 xml.etree 解析校验一次，保证文件是合法 XML。
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from typing import Any, Dict, List

from layout import ARROW_LEN_MM

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
ET.register_namespace("", SVG_NS)

PT_TO_MM_SVG = 25.4 / 72.0


def _esc(s: Any) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _mm(v: float) -> str:
    return f"{v:.2f}mm"


def write_svg(layout: Dict[str, Any], path: str, checksum: str = "",
              tool: str = "challenge-9034312d/scripts") -> str:
    """把布局模型写成可编辑分层 SVG。返回 SVG 文本。"""
    canvas = layout["canvas"]
    W, H = canvas["width_mm"], canvas["height_mm"]
    font = layout["font"]
    family = font["family"]
    fs = font["size_pt"]
    title_pt = font["title_pt"]

    # canvas 缩放：若请求画布小于实际需要，等比压缩放置在画布内（不裁剪内容）
    req_w, req_h = layout["requested_canvas"]["width_mm"], layout["requested_canvas"]["height_mm"]
    scale = 1.0
    ox = oy = 0.0
    if req_w > 0 and req_h > 0 and (W > req_w or H > req_h):
        scale = min(req_w / W, req_h / H)
        ox = max(0.0, (req_w - W * scale) / 2 / scale if (req_w - W * scale) > 0 else 0.0)
        oy = max(0.0, (req_h - H * scale) / 2 / scale if (req_h - H * scale) > 0 else 0.0)
        W, H = req_w, req_h

    S = []

    def s(x: float, y: float) -> str:
        return f"{x*scale+ox:.2f},{y*scale+oy:.2f}"

    def box_path(x: float, y: float, w: float, h: float, shape: str) -> str:
        x0, y0 = x * scale + ox, y * scale + oy
        w0, h0 = w * scale, h * scale
        if shape == "rounded":
            r = min(3.0, h0 / 2.0)
            return (f"M {x0+r:.2f} {y0:.2f} H {x0+w0-r:.2f} "
                    f"A {r:.2f} {r:.2f} 0 0 1 {x0+w0:.2f} {y0+r:.2f} "
                    f"V {y0+h0-r:.2f} "
                    f"A {r:.2f} {r:.2f} 0 0 1 {x0+w0-r:.2f} {y0+h0:.2f} "
                    f"H {x0+r:.2f} "
                    f"A {r:.2f} {r:.2f} 0 0 1 {x0:.2f} {y0+h0-r:.2f} "
                    f"V {y0+r:.2f} "
                    f"A {r:.2f} {r:.2f} 0 0 1 {x0+r:.2f} {y0:.2f} Z")
        if shape == "diamond":
            xm, ym = x0 + w0 / 2, y0 + h0 / 2
            return (f"M {xm:.2f} {y0:.2f} L {x0+w0:.2f} {ym:.2f} "
                    f"L {xm:.2f} {y0+h0:.2f} L {x0:.2f} {ym:.2f} Z")
        return (f"M {x0:.2f} {y0:.2f} H {x0+w0:.2f} V {y0+h0:.2f} "
                f"H {x0:.2f} Z")

    head = f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!-- 可编辑科研图稿 SVG | {tool} -->
<!-- 结构: 实体→关系→布局模型→SVG；每个实体元素带 data-source 可回溯到输入材料 -->
<svg xmlns="{SVG_NS}" xmlns:xlink="{XLINK_NS}"
     width="{W:.1f}mm" height="{H:.1f}mm"
     viewBox="0 0 {W:.1f} {H:.1f}"
     font-family="{_esc(family)}" font-size="{fs}" xml:space="preserve">
  <metadata id="metadata">
    <dc:source xmlns:dc="http://purl.org/dc/elements/1.1/">case.json + task.md</dc:source>
    <dc:title xmlns:dc="http://purl.org/dc/elements/1.1/">{_esc(layout['title'])}</dc:title>
    <bd:case_id xmlns:bd="urn:challenge-9034312d">{_esc(layout['case_id'])}</bd:case_id>
    <bd:checksum xmlns:bd="urn:challenge-9034312d">{_esc(checksum)}</bd:checksum>
  </metadata>
  <rect id="layer-background" x="0" y="0" width="{W:.1f}" height="{H:.1f}" fill="#FFFFFF" stroke="none"/>
  <g id="layer-title" font-size="{title_pt}">
    <text x="{W/2:.1f}" y="{12.0*scale+oy:.2f}" text-anchor="middle" font-weight="bold"
          data-layer="title">{_esc(layout['title'])}</text>
  </g>"""

    # --- 箭头层（先画，实体覆盖连接点）---
    head += '\n  <g id="layer-arrows" fill="none" stroke="#555555" stroke-width="1.0">'
    for r in layout["relations"]:
        pts = r["points"]
        d = " ".join(f"M {s(*pts[0])}" if i == 0 else f"L {s(*p)}" for i, p in enumerate(pts))
        dash = ' stroke-dasharray="4,3"' if r["kind"] == "recycle" else ""
        head += f'\n    <path id="arrow-{_esc(r["id"])}" data-kind="{_esc(r["kind"])}" d="{d}"{dash}/>'
        ax, ay, bx, by, tipx, tipy = r["arrow"][:6]
        kind_col = "#C0392B" if r["kind"] in ("flow", "causation") else "#555555"
        head += (f'\n    <polygon id="arrowhead-{_esc(r["id"])}" data-kind="{_esc(r["kind"])}" '
                 f'fill="{kind_col}" stroke="none" '
                 f'points="{s(ax, ay)} {s(bx, by)} {s(tipx, tipy)}"/>')
        if r.get("label"):
            lx, ly = pts[len(pts) // 2]
            head += (f'\n    <text x="{s(lx, ly).split(",")[0]}" y="{s(lx, ly).split(",")[1]}" '
                     f'text-anchor="middle" fill="#C0392B" font-size="{fs-2}" '
                     f'transform="translate(0,-2)">{_esc(r["label"])}</text>')
    head += "\n  </g>"

    # --- 实体层 ---
    head += '\n  <g id="layer-entities">'
    for e in layout["entities"]:
        x, y, w, h = e["x"], e["y"], e["w"], e["h"]
        col = e["color"]
        fill, stroke, txt = col.get("fill", "#F4F4F4"), col.get("stroke", "#666"), col.get("text", "#333")
        shape = e.get("shape", "rect")
        lines: List[str] = e.get("lines") or [e["display_label"]]
        line_h = fs * PT_TO_MM_SVG + 3.0
        y0 = y + h / 2 - (len(lines) - 1) * line_h / 2
        gid = f"entity-{e['id']}"
        head += (
            f'\n    <g id="{gid}" data-entity="{_esc(e["id"])}" data-kind="{_esc(e["kind"])}"'
            f' data-source="{_esc(e.get("source") or "")}" data-stage="{_esc(e.get("stage") or "")}">'
            f'\n      <path id="{gid}-shape" d="{box_path(x, y, w, h, shape)}" fill="{fill}" stroke="{stroke}" stroke-width="1.2"/>'
        )
        for i, ln in enumerate(lines):
            ty = y0 + i * line_h + fs * PT_TO_MM_SVG * 0.35
            head += (
                f'\n      <text id="{gid}-text-{i}" x="{x*scale+ox + (w*scale)/2:.2f}" y="{ty*scale+oy:.2f}" '
                f'text-anchor="middle" fill="{txt}" font-weight="normal" data-line="{i}">{_esc(ln)}</text>'
            )
        head += "\n    </g>"
    head += "\n  </g>"

    # --- 图例层 ---
    head += '\n  <g id="layer-legend" font-size="9">'
    ly = H - 6.0
    lx = 10.0
    for item in layout["legend"]:
        head += (f'\n    <rect x="{lx*scale+ox:.2f}" y="{ly*scale+oy+(0.0):.2f}" width="4.0" height="4.0" '
                 f'fill="{item["fill"]}" stroke="{item["stroke"]}"/>')
        head += (f'\n    <text x="{(lx+5.5)*scale+ox:.2f}" y="{(ly+4.5)*scale+oy:.2f}" style="font-size:9px" '
                 f'fill="#333333">{_esc(item["label"])}: {_esc(item["kind"])}</text>')
        lx += 5.5 + 8 + 2.0 + len(item["label"]) * 2.4 + len(item["kind"]) * 2.0
    head += "\n  </g>"

    head += "\n</svg>\n"

    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(head)

    # 校验 XML 合法
    ET.parse(path)
    return head