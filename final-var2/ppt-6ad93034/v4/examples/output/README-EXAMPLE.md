# examples/output — 示意输出（文本部分；**示例，非正式案例**）

> **来源声明**：本目录的 `.example.*` 文件是**在合成示例案例**
> （`examples/case.json` + `examples/task.md` + `examples/material.md` +
> `examples/results.csv`）上**由本 Skill 实际运行产生**的文本产物副本，
> 生成命令：
> `python "$SKILL_DIR/scripts/make_examples.py"`（内部调用
> `scripts/main.py --case examples/case.json --out <临时目录>`，随后把
> 机器本机绝对路径改写为包内相对路径）。
> **它们不是、也不代表平台正式 3 个固定案例的输出。**

## 为什么这里只有文本

本 Skill 包只允许 **UTF-8 文本资源**（`.md/.py/.json/.txt/.csv/.yaml/.yml`，
≤50 文件 / 单文件 ≤500KB / 合计 ≤2MB）。因此运行产物中的**二进制部分**
（`deck.pptx`、预览 `*.png`、预览 `*.pdf`）**不入包**，全部由运行时生成；
它们的完整文件清单、页级结构与契约字段写在
[`../EXPECTED-OUTPUT.md`](../EXPECTED-OUTPUT.md)（纯文字替代原二进制示意件）。

## 本目录文件

| 文件 | 对应运行产物 | 说明 |
|-|-|-|
| `result.example.json` | `result.json` | 唯一评分产物全文：契约字段回显（含 bool 形态 `is_example=false`）+ `deck`/`evidence`/`previews`/`sources`/`uncertainty`/`change_records`/`checks`/`environment`/`run_meta` |
| `plan.example.json` | `work/plan.json` | 页面模型（6 页 index/role/title/claims/evidence/figure/notes），可编辑源 |
| `material_view.example.json` | `work/material_view.json` | 材料抽取视图（章节/数据表/图表提及/任务头部） |
| `evidence_map.example.md` | `evidence_map.md` | 逐页证据映射（人读表格，6 行，mapped） |
| `evidence_map.example.json` | `evidence_map.json` | 逐页证据映射（机器可读，与 md 同源） |
| `manifest.example.json` | `manifest.json` | 全部产物 sha256 清单（25 项，路径相对该次运行的输出目录） |

**未随包的运行产物**（每次运行现场生成）：`work/deck.pptx`、
`work/chart_results.csv.png`、`work/preview/slide_*.png`、`work/preview/preview.pdf`、
`preview/slide_*.png`、`preview/preview.pdf`、`changelog.jsonl`、`logs/run_*.log`、
`work/table_cache/results.csv` —— 见 `../EXPECTED-OUTPUT.md` §1。

## 绝对路径处理

原先是本机绝对路径的三处（`sources[].path` ×3 与
`deck.slides[4].figure.image` / `plan.pages[4].figure.image`）已由
`scripts/make_examples.py` 统一改写为**包内相对路径**
（`examples/case.json`、`examples/material.md`、`examples/results.csv`、
`work/chart_results.csv.png`）。运行时仍会按实际机器写出真实路径，那是产物
而非包内容；跨机复跑时路径前缀随机器变化，内容不变。

## 复现

```bash
# 重新跑示例（产物写临时目录，不污染包）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out "$TMPDIR/out"
# 重新生成本目录的文本副本（含绝对路径净化）
python "$SKILL_DIR/scripts/make_examples.py"
```

正式运行时 Agent 必须依据案例实际提供的论文与模板重新生成全部内容；
本目录任何文件不得冒充正式案例结果，也不得被当作预制答案直接交付。
