# -*- coding: utf-8 -*-
"""bare_baseline.py — 对照条件 C0：「不加载 Skill」路径的可执行下界。

本文件属于 v2「增益可验证化」包：它是 references/GAIN-PROTOCOL.md 里 C0 条件的
可执行实现，配套的实跑记录在 references/COMPARISON-RECORD-20261122.md，
指标复算器在 scripts/gain_probe.py。

**它不是交付路径，也不是任何模型的真实行为记录。** 它把"裸做法"里最容易出错的几个
结构性动作写成代码，用来给对照实验提供一条**可复跑的下界**：

  case.json 原样读入 → 网格排版 → 写 SVG/PNG/PDF，
  不做材料对账、不做 id 去重、不做类别归一、不丢弃断头关系、不跑任何门禁、
  不写 status / sources / uncertainty / change_record。

这样 C0 与 C1 跑的是**同一份输入**，差别只来自那些被省略的环节，而不是来自两套
不同的渲染实现。真实 agent 在无 Skill 时的行为可能更好也可能更差；本脚本只回答
"少了这些环节、且不做任何额外努力时，产物会是什么样"。

**C0 的实测对照结果（摘要）**：来源绑定率 0.00（无该字段）· 断头端点外露 1 条（原样画出）
· 规则违规暴露 0 条（无审计）· PNG/PDF 为 0 字节占位 · 无 status 字段。

用法:
    python "$SKILL_DIR/scripts/bare_baseline.py" --case <case.json> --out <输出目录>

退出码: 0 = 已写出下界产物；2 = 输入缺失。
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.dont_write_bytecode = True  # 包内不落 .pyc

W, H, COLS, BW, BH = 1200, 800, 4, 240, 70
COLORS = ["#cfe3f7", "#f7e2cf", "#d9f2d9", "#f2d9ea", "#e6e6e6"]


def render(case_path: str, out_dir: str) -> dict:
    with open(case_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    ents = data.get("entities") or []
    rels = data.get("relations") or []

    os.makedirs(out_dir, exist_ok=True)
    pos = {}
    for i, e in enumerate(ents):
        c, r = i % COLS, i // COLS
        pos[e["id"]] = (60 + c * (BW + 40), 120 + r * (BH + 60))

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        '<defs><marker id="a" markerWidth="10" markerHeight="10" refX="8" refY="3" '
        'orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#666"/></marker></defs>',
        f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
        f'<text x="60" y="60" font-size="24" font-family="sans-serif">'
        f'{data.get("title", "图稿")}</text>',
    ]
    # 关系原样画：端点缺失时给一个占位坐标，让箭头"仍然画得出来"（这正是要对照的动作）
    dangling = 0
    for r in rels:
        frm, to = r.get("from"), r.get("to")
        if frm not in pos or to not in pos:
            dangling += 1
        a = pos.get(frm, (60.0, H - 30.0))
        b = pos.get(to, (W - 60.0, H - 30.0))
        x1, y1 = a[0] + BW / 2, a[1] + BH / 2
        x2, y2 = b[0] + BW / 2, b[1] + BH / 2
        parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#666" '
                     f'stroke-width="2" marker-end="url(#a)"/>')
    for i, e in enumerate(ents):
        x, y = pos[e["id"]]
        parts.append(f'<rect x="{x}" y="{y}" width="{BW}" height="{BH}" rx="8" '
                     f'fill="{COLORS[i % len(COLORS)]}" stroke="#333"/>')
        parts.append(f'<text x="{x + 12}" y="{y + BH / 2 + 6}" font-size="16" '
                     f'font-family="sans-serif">{e.get("name", e["id"])}</text>')
    parts.append("</svg>")

    with open(os.path.join(out_dir, "figure.svg"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(parts))
    for name in ("figure.png", "figure.pdf"):
        with open(os.path.join(out_dir, name), "wb") as fh:
            fh.write(b"")  # 占位空文件：没有真正的渲染步骤

    return {
        "case_id": data.get("case_id"),
        "entities_drawn": len(ents),
        "relations_drawn": len(rels),
        "dangling_endpoints_kept": dangling,
        "source_binding": "none",
        "gates_run": [],
        "status_field": None,
        "png_bytes": 0, "pdf_bytes": 0,
        "out_dir": out_dir,
    }


def main(argv) -> int:
    ap = argparse.ArgumentParser(description="不加载 Skill 的可执行下界（对照实验用）")
    ap.add_argument("--case", required=True, help="case.json 路径")
    ap.add_argument("--out", default="bare-out", help="输出目录（默认 ./bare-out）")
    args = ap.parse_args(argv)
    if not os.path.isfile(args.case):
        print(f"FATAL: case 不存在: {args.case}", file=sys.stderr)
        return 2
    info = render(args.case, os.path.abspath(args.out))
    print(json.dumps(info, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
