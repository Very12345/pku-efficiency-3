# -*- coding: utf-8 -*-
"""baseline_emulator.py — 对照实验"条件 A（基础）"的结构复现器（反例生成器）。

定位（务必先读）
----------------
`references/GAIN-PROTOCOL.md` 的本地对照实验需要一份**条件 A（不加载本 Skill）**的产物。
真实条件 A 由平台用自己的基础 Agent 运行（同输入、同预算、每条件 3 次重复），
**本脚本不是 LLM，也不冒充平台结果**。它做的事只有一件：把题面 §1 已经点名的基础 Agent
典型失败签名，做成一个**确定性、可复现**的结构复现器，好让"增益是否可判定"这件事
在离线环境里也能被第三方复算：

  · 把材料里的名词**平铺成一圈节点**，节点之间**随意连线**；
  · 所有连线用**同一种灰色箭头**，不区分激活/抑制/结合/修饰/转运；
  · **没有图例**，颜色/线宽不编码任何数据；
  · **没有来源标注**（元素不带 data-source，notes.md 只有自然语言）；
  · **没有结构化契约产物**（不写 result.json）；
  · **没有可编辑分层**（只有一个扁平 <g>），只相当于"一张图"。

它是**反例生成器，不是绘图方案**：产物禁止作为正式案例输出、禁止冒充平台对照结果、
禁止把它的实体名/连线抄进正式交付。度量侧用 `scripts/gain_probe.py`（同一把尺子量两边）。

用法
----
  python3 scripts/baseline_emulator.py --material <材料 md> --out <dir> [--title 标题]
输出
----
  <out>/figure.svg   单层扁平 SVG（无 data-*、无图例、统一灰箭头）
  <out>/notes.md     自然语言说明（无行号、无契约、无审计）
退出码
------
  0 = 已产出；2 = 材料不可读或无实体表；3 = 参数错误。
"""
from __future__ import annotations

import argparse
import math
import os
import sys

FONT = "Helvetica, Arial, sans-serif"
CANVAS_W, CANVAS_H = 1200, 900
NAIVE_EDGE_COLOR = "#7F8C8D"          # 单一灰色：不区分语义
NAIVE_NODE_FILL = "#D5DBDB"           # 单一填充：不编码数据


def read_text(path):
    with open(path, "rb") as fh:
        return fh.read().decode("utf-8", "replace")


def parse_entities(material_text):
    """只做基础 Agent 会做的那一步：把材料实体表第一列抄出来。"""
    names = []
    for raw in material_text.splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        head = cells[0]
        if not head or head.startswith("---") or head in ("名称", "name", "Name"):
            continue
        if head not in names:
            names.append(head)
    return names


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


def render_flat_svg(names, title):
    """环状平铺 + 统一灰箭头：刻意保留基础 Agent 的失败签名。"""
    n = max(len(names), 1)
    cx, cy = CANVAS_W / 2.0, CANVAS_H / 2.0 + 40
    rx, ry = CANVAS_W * 0.34, CANVAS_H * 0.30
    pts = []
    for i in range(n):
        ang = -math.pi / 2.0 + 2.0 * math.pi * i / n
        pts.append((cx + rx * math.cos(ang), cy + ry * math.sin(ang)))

    p = []
    p.append('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
             'viewBox="0 0 %d %d">' % (CANVAS_W, CANVAS_H, CANVAS_W, CANVAS_H))
    p.append('<rect width="100%%" height="100%%" fill="#FFFFFF"/>')
    p.append('<defs><marker id="a" markerWidth="8" markerHeight="8" refX="8" refY="4" '
             'orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="%s"/></marker></defs>'
             % NAIVE_EDGE_COLOR)
    p.append('<g>')                                    # 单一扁平层，无 layer-*
    p.append('<text x="40" y="48" font-family="%s" font-size="20" fill="#212F3D">%s</text>'
             % (FONT, esc(title)))
    # 随意连线：环上相邻 + 一条长弦，全部同一种样式
    links = [(i, (i + 1) % n) for i in range(n)] + [(0, n // 2)] if n > 2 else [(0, 1)]
    for a, b in links:
        if a == b:
            continue
        p.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" '
                 'stroke-width="1.6" marker-end="url(#a)"/>'
                 % (pts[a][0], pts[a][1], pts[b][0], pts[b][1], NAIVE_EDGE_COLOR))
    for i, name in enumerate(names):
        x, y = pts[i]
        p.append('<ellipse cx="%.1f" cy="%.1f" rx="86" ry="34" fill="%s" '
                 'stroke="#566573" stroke-width="1.4"/>' % (x, y, NAIVE_NODE_FILL))
        p.append('<text x="%.1f" y="%.1f" font-family="%s" font-size="13" fill="#1B2631" '
                 'text-anchor="middle">%s</text>' % (x, y + 4, FONT, esc(name)))
    p.append('</g>')
    p.append('</svg>')
    return "\n".join(p) + "\n"


NOTES = """# 图说明（基础条件产物 · 反例生成器输出）

图为 `figure.svg`：把材料里出现的名词按环状排布，相关名词之间连线，
箭头方向表示"指向下游"。本次共 %d 个节点、%d 条连线。

说明：

- 连线样式统一，未区分促进/抑制/结合等关系类型；
- 未绘制图例，未用颜色或线宽编码数据；
- 未标注每个元素的来源行号；
- 未提供可编辑分层源文件说明与导出检查记录；
- 未生成结构化结果文件（result.json），因此无法被契约命令复核。

> 本文件由 `scripts/baseline_emulator.py` 生成，用于对照实验的条件 A（结构复现），
> **不是**平台基础 Agent 的真实运行结果，**也不是**可交付的正式图稿。
"""


def main(argv=None):
    ap = argparse.ArgumentParser(description="条件 A（基础）结构复现器（反例生成器）")
    ap.add_argument("--material", required=True, help="与条件 B 完全相同的材料文件")
    ap.add_argument("--out", required=True, help="输出目录")
    ap.add_argument("--title", default="机制图（基础条件）")
    args = ap.parse_args(argv)

    if not os.path.isfile(args.material):
        print("baseline_emulator|error|material not found: %s" % args.material)
        return 2
    names = parse_entities(read_text(args.material))
    if not names:
        print("baseline_emulator|error|no entity table rows found in %s" % args.material)
        return 2

    os.makedirs(args.out, exist_ok=True)
    svg = render_flat_svg(names, args.title)
    with open(os.path.join(args.out, "figure.svg"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(svg)
    n_links = len(names) + (1 if len(names) > 2 else 0)
    with open(os.path.join(args.out, "notes.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(NOTES % (len(names), n_links))
    print("baseline_emulator|ok|entities=%d|links=%d|out=%s" % (len(names), n_links, args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
