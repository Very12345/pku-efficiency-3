# examples — 最小调用示例（示例，非正式案例）

> 本节所有内容均为**合成演示**（case 输入、来源材料、期望产物说明），仅用于
> 说明接口与完整使用流程，**不冒充、不等同于平台正式案例结果**。
> 正式案例由组织方提供，平台以固定 3 案例运行本 Skill。
>
> **包内不预置任何产物**：PDF/PNG/SVG 属平台不支持的文件类型，且预置产物
> 会被误当"正式答案"。示例产物一律**运行时现场生成**，期望清单见
> `EXPECTED-OUTPUT.md`，一键复现见下文 `run_examples.py`。

## 三个示例

| 文件 | 演示能力 |
|-|-|
| `case.json` (schematic) | 机制/信号通路示意图：实体 6、关系 5（结合/招募/激活/转录上调）、分组 3、图例 3；产出 `figure.svg`（可编辑源）+ `figure.png`（预览）+ `figure.pdf`（导出）+ `result.json` |
| `case_chart.json` (chart) | 数据表驱动图表：图例/颜色直接从 `sources/data-table.csv` 类别生成（图例×颜色×类别数三方一致） |
| `case_edit.json` (edit) | 源文件级编辑：对**上一步真实生成**的 `figure.svg` 做 rename/relabel/note 三种动作，before→after 写入 result.json `change_records`，未改动元素保持原样 |

## 运行（全部自定位，任意 cwd 可跑；产物写在包外）

```bash
SKILL_DIR="$(cd "$(dirname "<本 SKILL.md 的实际路径>")" && pwd)"

# ① 一键复现：schematic → chart → edit，并对每份 result.json 跑 G1–G8 契约门
python "$SKILL_DIR/scripts/run_examples.py" --out /tmp/sse-examples

# ② 或逐步执行
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out /tmp/sse-examples/schematic
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case_chart.json" --out /tmp/sse-examples/chart
#    编辑示例以上一步真实生成的 SVG 为输入（包内不预置 SVG）：
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case_edit.json" \
    --edit-svg /tmp/sse-examples/schematic/figure.svg --out /tmp/sse-examples/edit
python "$SKILL_DIR/scripts/validate_result.py" --case "$SKILL_DIR/examples/case.json" \
    --result /tmp/sse-examples/schematic/result.json
```

`--case` 既接受 `case.json` 文件，也接受**目录**（目录下或其后代
`examples/` 下存在 `case.json` 时自动解析）。

## 其余可用角色的演示

```bash
# ① 材料 → 候选 ER 清单（自动抽取 + 定位，_draft 标注，需人工复核）
python "$SKILL_DIR/scripts/extract.py" \
    --inputs "$SKILL_DIR/examples/sources/figure03-note.md" --out /tmp/sse-draft.json
# ② 字体栈探测（中文/公式渲染前必查）
python "$SKILL_DIR/scripts/textfont.py" --list
# ③ PDF 文本抽取（stdlib 回退；写法与输出见 TEST.md）
python "$SKILL_DIR/scripts/pdftext.py" --pdf <your.pdf> --out /tmp/pdftext-out
# ④ CP1 生成前 lint 门（main.py 默认自动运行）
python "$SKILL_DIR/scripts/spec_lint.py" --manifest /tmp/sse-draft.json
```

## 期望产物（`EXPECTED-OUTPUT.md` 为权威文字清单）

每次运行产出的 `figure.svg` 都是**可编辑分层源文件**：文字均为 `<text>`；
元素带 `id` 与 `data-entity`/`data-relation`/`data-source`；语义图层
`layer-*`；ER 清单内嵌于 `<metadata id="er-manifest">`（源文件自描述，
供 `--edit-svg` 增量编辑）。`result.json` 为唯一评分产物，字段契约见
`references/OUTPUT_CONTRACT.md`，硬门 G1–G8 由 `scripts/validate_result.py`
独立复跑。

示例输入与产出均可由上面的命令在任意新目录复现；**请勿**把示例产物
当作正式案例答案提交。
