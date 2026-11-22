#!/usr/bin/env python3
"""基准条件（不加载 Skill 的基础 Agent）的典型做法 —— 对照实验用。

诚实声明：本文件**不是**平台官方的基础 Agent，而是把"通用绘图库 + 直接写脚本"
这一常规做法固化成可复跑的一段程序，供本地 A/B 度量使用。它刻意采用最常见的
默认选择（plotly 风格自动配色换成 matplotlib、自动刻度、不做溯源、不做契约），
不刻意做差。

用法: python baseline_agent.py --case <case.json> --out <out_dir>
"""
import argparse, csv, json, os, sys

def load_csv(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    return rows

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)

    case = json.load(open(a.case, encoding="utf-8"))
    base = os.path.dirname(os.path.abspath(a.case))
    os.makedirs(a.out, exist_ok=True)

    figures = case.get("figures") or [case.get("figure") or {}]
    fig = figures[0]
    panel = (fig.get("panels") or [fig])[0]

    data_file = panel.get("data_file") or "data.csv"
    data_path = os.path.join(base, data_file)
    rows = load_csv(data_path)

    xcol = (panel.get("x") or {}).get("column")
    ycol = (panel.get("y") or {}).get("column")
    if not xcol:
        cols = list(rows[0].keys())
        xcol, ycol = cols[0], cols[1]

    xs = [r[xcol] for r in rows]
    ys = [float(r[ycol]) for r in rows]

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    outfile = os.path.join(a.out, "figure.png")
    figobj, ax = plt.subplots(figsize=(8, 4))
    ax.bar(xs, ys)
    ax.set_xlabel(xcol)      # 列名直接当标签
    ax.set_ylabel(ycol)
    ax.set_title(fig.get("title") or "")
    figobj.tight_layout()
    figobj.savefig(outfile, dpi=150)
    plt.close(figobj)

    summary = {
        "output": "figure.png",
        "rows_used": len(rows),
        "x": xcol,
        "y": ycol,
        "values": ys,
    }
    with open(os.path.join(a.out, "summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)

    print(f"[baseline] wrote {outfile} rows={len(rows)}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
