# `examples/cases/` — 两个不同题材的合成案例（示例，非正式案例）

> 这两案是**合成演示**：材料由本包自造，用于证明"换个题材/图型还能走通同样的
> 链路"，并作为题集（`scripts/case_probe.py`）的输入。**不是真实论文数据，
> 也不得当作正式案例答案。**

## 两案一览

| 文件 | 题材 / 图型 | 难度层 | 与包内 `examples/case*.json` 的差异 |
|-|-|-|-|
| `case_mitophagy.json` | **细胞生物学：PINK1/Parkin 线粒体自噬清除通路** / schematic | 中 | ①实体类型换成 organelle / kinase / e3_ligase / modification ②关系词表覆盖 recruitment + process ③材料中英混排，压 `textfont` 的 CJK 路径 ④材料**自带一处反误读**（PINK1 是被稳定化的激酶，不是被降解的底物） |
| `case_expr_heatmap.json` | **转录组：三条件 × 三重复的标记基因表达矩阵** / chart/heatmap | 中高 | ①走 `data.matrix` + `row_labels`/`col_labels` 的**热图分支**（与柱状图完全不同的渲染路径）②单位进色标而非 y 轴 ③要求"类别 ↔ 图例 ↔ 颜色数"三方一致 |

## 怎么跑

```bash
SKILL_DIR="$(cd "$(dirname "<本 SKILL.md 的实际路径>")" && pwd)"

# 单案
python "$SKILL_DIR/scripts/main.py" \
    --case "$SKILL_DIR/examples/cases/case_mitophagy.json" --out /tmp/sse-mito
python "$SKILL_DIR/scripts/validate_result.py" \
    --case "$SKILL_DIR/examples/cases/case_mitophagy.json" --result /tmp/sse-mito/result.json

# 两案（连同 5 条边界探针）一起对"可接受区间"
python "$SKILL_DIR/scripts/case_probe.py" --skill-root "$SKILL_DIR" --out /tmp/c --group new
```

## 来源材料（合成）

| 文件 | 内容 |
|-|-|
| `sources/mitophagy-note.md` | 自噬通路的机制链条（§2，带行号）、模块划分（§3）、图例约定（§4）；**含"PINK1 是激酶、不是底物"这条反误读提示** |
| `sources/expression-table.csv` | 三条件 × 三重复的表达值（`log2 fold change`），与 `case_expr_heatmap.json` 的 `data.matrix` 逐值一致 |

> 材料与案例里出现的基因名/条件名/数值均为**合成演示数据**，不来自任何
> 真实论文。真实案例由平台提供，本包不预置任何正式答案。

## 期望产物（产物运行时生成，包内不预置任何图稿）

| 案例 | 期望产物 | 关键判据 |
|-|-|-|
| `case_mitophagy.json` | `figure.svg` + `figure.png` + `figure.pdf` + `result.json` | 6 实体 / 5 关系 / 3 分组 / 2 图例项；溯源 100%；画布不溢出；`exit 0` / `success` |
| `case_expr_heatmap.json` | 同上 | 3 类别、单位非空、类别↔图例↔颜色数一致；`exit 0` / `success` |

实测数字（本机 Python 3.13.9）见 `references/CASE-SET.md` §3。
