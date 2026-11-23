# examples — 最小调用示例（示例，非正式案例）

> 本节全部为**合成演示**（case 输入、来源材料、期望产物说明），仅说明接口与
> 完整使用流程，**不冒充、不等同于平台正式案例结果**。正式案例由组织方提供，
> 平台以固定 3 案例运行本 Skill。
>
> **包内不预置任何产物**：PDF/PNG/SVG 属平台不支持的文件类型，且预置产物会被
> 误当"正式答案"。示例产物一律**运行时现场生成**，期望清单见
> `EXPECTED-OUTPUT.md`，一键复现见 `scripts/run_examples.py`。

## 三个示例（各自演示一组决策规则）

| 文件 | 演示能力 | 关联的决策规则 |
|-|-|-|
| `case.json`（schematic） | 机制/信号通路示意图：实体 6、关系 5（结合/招募/激活/转录上调）、分组 3、图例 3；产出 `figure.svg`（可编辑源）+ `figure.png`（预览）+ `figure.pdf`（导出）+ `result.json` | D2（实体须有出处）、D4（kind 必须可映射）、D5（包含用分组） |
| `case_chart.json`（chart） | 数据表驱动图表：图例/颜色直接从 `sources/data-table.csv` 的类别生成（图例 × 颜色 × 类别数三方一致）；改数据即整体重绘 | D6、D7、D8（表外类别 = G8 INVALID） |
| `case_edit.json`（edit） | 源文件级编辑：对**上一步真实生成**的 `figure.svg` 做增量修改，before→after 写入 `change_records`，未改动元素保持原样 | D10（字段名必须精确）、CP4（编辑后重跑全部检查） |

> `case.json` 里 `output_contract` 声明了 5 个契约键，用来演示**四形态回显**：
> string→`""`、array→`[]`、object→`{}`、number→`0`、boolean→`false`（禁 `null`）。
> 这正是 D9 的现场样例。

## 运行（全部自定位，任意 cwd 可跑；产物写在包外）

```bash
SKILL_DIR="$(cd "$(dirname "<本 SKILL.md 的实际路径>")" && pwd)"

# ① 一键复现：schematic → chart → edit，并对每份 result.json 跑 G1–G8 契约门
python "$SKILL_DIR/scripts/run_examples.py" --out /tmp/sse-examples

# ② 单跑 schematic（--case 可指目录，也可指 case.json 文件）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out /tmp/sse-sch

# ③ 单跑 chart
python "$SKILL_DIR/scripts/main.py" \
    --case "$SKILL_DIR/examples/case_chart.json" --out /tmp/sse-chart

# ④ 编辑：先出图，再在源文件上做增量修改
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out /tmp/sse-sch
python "$SKILL_DIR/scripts/main.py" \
    --case "$SKILL_DIR/examples/case_edit.json" \
    --edit-svg /tmp/sse-sch/figure.svg --out /tmp/sse-edit

# ⑤ 契约门 + 文档↔代码对拍
python "$SKILL_DIR/scripts/validate_result.py" \
    --case "$SKILL_DIR/examples/case.json" --result /tmp/sse-sch/result.json
PYTHONDONTWRITEBYTECODE=1 python -B "$SKILL_DIR/scripts/doccheck.py"
```

以上命令的**实测退出码**与产物清单见 `TEST.md` §T3–§T8。

## 示例材料的性质

`sources/figure03-note.md` 与 `sources/data-table.csv` 是**为演示写的合成材料**
（内容自洽、句式模仿真实论文图注），**不是任何真实论文的数据**。
用它们跑出来的图只能作为接口演示，**不得**当作正式案例答案提交。
