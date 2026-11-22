# EXPECTED-OUTPUT.md — 示例案例上应产出的文件清单与契约字段（纯文字）

> 本文件用**文字**替代原先随包的二进制示意产物（`deck.example.pptx`、
> `preview/slide_*.example.png`、`preview.example.pdf`、`chart-results.example.png`）。
> 原因：本 Skill 包只允许 UTF-8 文本资源（`.md/.py/.json/.txt/.csv/.yaml/.yml`，
> ≤50 文件 / 单文件 ≤500KB / 合计 ≤2MB）。
> **二进制产物不是被删掉不做了，而是全部由运行时生成** —— 任何一次
> `main.py` 运行都会在输出目录重新产出下面清单里的全部文件。
>
> 场景：`examples/case.json` + `examples/task.md` + `examples/material.md`
> + `examples/results.csv`（**虚构示例，非平台正式案例**），
> `spec.max_slides = 6`，命令见 `examples/README.md`。
> 实测状态：`status=success`、`run_meta.checkpoints` 四门全 true、
> `result_tool.py` G1–G8 `{"valid": true}`、`selftest.py` `all_pass=true`。

## 1. 运行后在输出目录应出现的文件（25 个）

| 相对路径 | 类型 | 说明 | 是否随包提供 |
|-|-|-|-|
| `result.json` | 文本 JSON | 唯一评分产物；契约字段见 §2 | 文本 → 见 `examples/output/result.example.json` |
| `evidence_map.md` | 文本 MD | 页级证据映射（人读表格，6 行） | 文本 → `examples/output/evidence_map.example.md` |
| `evidence_map.json` | 文本 JSON | 同一来源的机器可读形态 | 文本 → `examples/output/evidence_map.example.json` |
| `changelog.jsonl` | 文本 JSONL | 版本记录（本次运行 start/图绑定/build/finish） | ✗ 扩展名不入包；运行时生成 |
| `manifest.json` | 文本 JSON | 全部产物的 sha256 清单（25 项） | 文本 → `examples/output/manifest.example.json` |
| `logs/run_<时间戳>.log` | 文本 LOG | 全流程日志（含 `STATUS=success …` 末行） | ✗ 运行时生成 |
| `work/deck.pptx` | **二进制** | 可编辑演示源；6 页，每页含主张式标题、要点、证据脚注、演讲者备注 | ✗ 运行时生成 |
| `work/plan.json` | 文本 JSON | 页面模型（页序/角色/主张/证据/图表），可编辑源 | 文本 → `examples/output/plan.example.json` |
| `work/material_view.json` | 文本 JSON | 材料抽取视图（章节 8 / 数据表 1 / 图表提及 / 任务头部） | 文本 → `examples/output/material_view.example.json` |
| `work/chart_results.csv.png` | **二进制** | 由 `results.csv` **原样重绘**的图表（数值未改动） | ✗ 运行时生成 |
| `work/table_cache/results.csv` | 文本 CSV | 抽表缓存（供可编辑复算） | ✗ 运行中间件 |
| `work/preview/slide_01.png` … `slide_06.png` | **二进制** | 逐页预览（PIL 画布，**非 PowerPoint 导出**） | ✗ 运行时生成 |
| `work/preview/preview.pdf` | **二进制** | 逐页文本版式预览（reportlab；缺库时跳过并记 warning） | ✗ 运行时生成 |
| `preview/slide_01.png` … `slide_06.png` | **二进制** | 输出根下的预览副本（便于直接取件） | ✗ 运行时生成 |
| `preview/preview.pdf` | **二进制** | 输出根下的 PDF 预览副本 | ✗ 运行时生成 |

> 二进制产物**一律不入包**（平台硬约束），它们由 `main.py` 在 `/app/output`
> 现场生成，并登记进 `manifest.json` 的 sha256 清单；`result.json` 的
> `deck.editable` 与 `previews.*` 指向它们。

## 2. `result.json` 顶层字段（每次运行都必须出现，禁 null）

`case_id` · `title` · `status` · `created_at` · `skill_version` · `deck` ·
`evidence` · `previews` · `sources` · `uncertainty` · `change_records` · `log` ·
`checks` · `evidence_map_json` · `manifest` · `environment` · `run_meta`
—— 外加 `case.json` 的 `output_contract` 逐项回显（示例案例声明
`case_id/deck/evidence/previews/is_example`，其中 `is_example` 是 **bool**，
按四形态回显为 `false`）。

字段语义、容器形态与 G1–G8 硬性门见 `../references/OUTPUT_CONTRACT.md`；
`examples/output/result.example.json` 是一次真实运行的全文（绝对路径已改写为
包内相对路径），可用于逐字段对拍。

## 3. 示例案例上的关键实测值

| 项 | 值 |
|-|-|
| `case_id` | `ppt-6ad93034-example-001` |
| `status` | `success`（材料齐全、无未核验主张、G1–G8 全过、自检 7/7） |
| `deck.slide_count` | 6 |
| 页级角色 | `cover → overview → question → method → result → takeaway` |
| 结果页 figure | `kind=chart_image`、`table_id=results.csv`、`image=work/chart_results.csv.png` |
| `evidence.unverified_claims` | `[]`（页面数字全部可在材料中定位） |
| `previews.method` | `PIL/reportlab 预览渲染，非 PowerPoint 导出` |
| `run_meta.checkpoints` | `cp1_extract/cp2_plan/cp3_build/cp4_verify = true` |
| `checks.all_pass` | `true`（7 项：pptx_reopen / result_json / contract_keys / unverified_claims / evidence_map_md / evidence_map_json / previews） |

## 4. 注意事项

1. **示例 ≠ 正式案例**：本示例材料是虚构的（蛋白质二级结构预测），只演示接口
   与完整流程；平台固定 3 个案例由组织方提供，Skill 在运行时依据实际输入重新
   生成全部产物，包内**没有任何预制答案**。
2. **预览不是 Office 导出**：运行环境无 PowerPoint/LibreOffice 时，预览由
   PIL/reportlab 按页面模型渲染，文件名与 `previews.method` 均如实标注。
3. 同一输入、无 `--edit` 时结构确定；不同机器/不同输出目录只会改变时间戳与
   路径前缀（`figure.image`、`sources[].path`），不改变内容。
4. 复现本清单：`python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <输出目录>`。
