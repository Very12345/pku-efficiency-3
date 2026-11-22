# EXPECTED-OUTPUT — 示例上的期望产物与**期望读数**

本文件替代"预置的示例产物"：包内不放任何 PDF/PNG/SVG。这里用**文字**列出
三个合成示例上真实运行时应出现的文件、契约取值与**指标读数**——后者是
`references/GAIN-PROTOCOL.md` §5 记账模板的期望值，可用来判断一次复跑
是否正常。

> 实测记录见 `TEST.md` §M3–§M7；本文件是"期望"，`TEST.md` 是"实测"。

## 1. 公共产物

| 文件 | 说明 | 对应检查名 |
|-|-|-|
| `figure.svg` | 可编辑分层源文件 | `svg.editable_text`、`svg.layers`、`svg.manifest_embedded`、`svg.manifest_matches`、`svg.data_entity_attrs` / `svg.data_relation_attrs` / `svg.data_source_attrs`、`svg.title_exists` |
| `figure.png` | 渲染预览 | `bitmap.dimensions`、`bitmap.dpi_print`、`bitmap.colourspace` |
| `figure.pdf` | 矢量导出件 | `pdf.header`、`pdf.pages`、`pdf.fonts_embedded` |
| `result.json` | 结构化结果 | 契约 §1 全部字段 + `case_id` |

## 2. `case.json`（schematic）期望取值与读数

| 项目 | 期望 | 对应指标 |
|-|-|-|
| `status` | `success` | I1 的辅助信息（I1 的真读数是外部命令退出码） |
| `main_result.entity_count / relation_count / group_count` | 6 / 5 / 3 | I2 |
| `artifacts[*].role` | `figure` / `preview` / `pdf` | I2（G7 要求三类齐全） |
| `svg.editable_text` | ok（真实 `<text>`） | I3 |
| `svg.layers` | ok（语义图层） | I3 |
| `legend_mapping` | 3 条，且与图面箭头类型双向一致 | I6 |
| `traceability.entities / relations` | 6/6 与 5/5（100%） | I4 |
| `bitmap.dpi_print` | 18 cm 宽有效 DPI ≥300（实测 ≈635） | I8 |
| `font.cjk` | True（本机有 CJK 族） | I8 |
| `change_records` | `[]` | — |
| `determinism.spec_sha16` | 非空 | I9 前置 |
| 契约回显 | 声明 5 个键 → `""` / `[]` / `{}` / `0` / `false`（不得 `null`） | I1（G5） |

## 3. `case_chart.json`（chart）期望

- `figure_type = chart`；数据只来自 `sources/data-table.csv`；
- `data_mapping.color_count` 的颜色数 ≥ 唯一类别数；**G8：不得出现表外类别**；
- 应能看到 `data_mapping.legend_consistency`、`data_mapping.rows`、`data_mapping.unit`、
  `traceability.data_table`；
- **R6 式验证**：把数据表数值翻倍后重跑，`figure.svg` 的 sha256 应**改变**
  （否则 I7 不成立）。

## 4. `case_edit.json`（edit）期望

- `change_records` 条数 == 按 `references/EDIT-ACTION-SCHEMA.md` §1 推算的
  **期望条数**（`remove_entity` 会级联出 `cascade_remove_relation`）；
- 每条记录含 `action` / `target` / `before` / `after` / `reason`；
- 编辑后全部 CP2 检查重跑，且契约门仍 VALID；
- **R11 对照**：若把目标改成不存在的 id，`change_records` 会变成 0 条
  而退出码仍是 0 ⇒ 必须按协议 G4 用条数对拍发现。

## 5. 一次"正常复跑"的期望读数（协议 §5 模板的填空示范）

```text
I1 契约            : exit 0 / VALID
I2 产物            : figure + preview + pdf（3/3）
I3 可编辑性        : ok / ok / 属性计数 6/6、5/5、5/5
I4 溯源            : 100% / 100%
I9 返工轮次        : CP1 第 1 次 valid；编辑请求 5 条 / change_records 7 条
I10 耗时           : ≈1.5 s（单例）、≈5.0 s（三示例）
未测量项           : 基线臂读数（本机未跑）
```

> 最后一行**不是可选项**：协议 F8 要求任何记账都必须写明未测量项。
