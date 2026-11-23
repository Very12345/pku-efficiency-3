# EXPECTED-OUTPUT — 示例案例上本 Skill 应当产出什么（文字清单）

本文件替代"预置的示例产物"：包内不放任何 PDF/PNG/SVG（平台不支持的文件类型，
且预置产物会被误当正式答案）。这里用**文字**列出在三个合成示例上真实运行时
应当出现的文件、契约字段与检查结果，供复核者逐条对照。

> 所有产物都在运行时生成到包外目录（如 `/tmp/sse-examples/<name>/`）。
> 实测记录见 `TEST.md` §T3。

## 1. 公共产物（schematic / chart 各一套）

| 文件 | 说明 | 判定要点（对应检查名） |
|-|-|-|
| `figure.svg` | 可编辑分层源文件 | 文字是真实 `<text>`（`svg.editable_text`）、有语义图层（`svg.layers`）、内嵌 ER 清单（`svg.manifest_embedded`、`svg.manifest_matches`）、元素带溯源属性（`svg.data_entity_attrs`/`svg.data_relation_attrs`/`svg.data_source_attrs`）、有图题（`svg.title_exists`） |
| `figure.png` | 渲染预览 | 像素尺寸与画布一致（`bitmap.dimensions`）、18 cm 宽有效 DPI ≥300（`bitmap.dpi_print`）、色彩为 RGB 族（`bitmap.colourspace`） |
| `figure.pdf` | 矢量导出件 | 头部可读（`pdf.header`）、页数正常（`pdf.pages`）、字体嵌入尽力而为（`pdf.fonts_embedded`） |
| `result.json` | 结构化结果 | 覆盖 `references/OUTPUT_CONTRACT.md` §1 全部字段 + `case_id`；契约键四形态回显无 `null` |

## 2. `case.json`（schematic）期望的契约取值

| 键 | 期望 | 依据 |
|-|-|-|
| `status` | `success` | 全部检查 ok、CP1 `valid=true` |
| `figure_type` | `schematic` | 来自 case |
| `main_result.entity_count` | 6 | 清单里的 6 个实体 |
| `main_result.relation_count` | 5 | 清单里的 5 条关系 |
| `main_result.group_count` | 3 | 3 个模块分组 |
| `artifacts[*].role` | `figure` / `preview` / `pdf` | G7 要求三类齐全 |
| `legend_mapping` | 3 条（activation / recruitment / transcriptional） | 与图面箭头类型双向一致 |
| `change_records` | `[]`（无编辑） | 契约要求该键存在 |
| `evidence.entities[*]` | 每条都有 `source` + `evidence` | `traceability.entities` 应为 100% |
| `determinism.spec_sha16` | 非空 | CP5 双跑探针 |

`schematic` 的 `output_contract` 声明 5 个键（string/array/object/number/boolean 各一），
回显到顶层后应分别得到 `""` / `[]` / `{}` / `0` / `false`（**不得**是 `null`）。

## 3. `case_chart.json`（chart）期望

- `figure_type = chart`；数据只来自 `sources/data-table.csv`；
- `data_mapping.color_count` 的颜色数 ≥ 唯一类别数（`spec.color_category_count`）；
- G8：不得出现数据表之外的类别；
- `verification.checks` 里应能看到 `data_mapping.legend_consistency`、`data_mapping.rows`、
  `data_mapping.unit`、`traceability.data_table`。

## 4. `case_edit.json`（edit）期望

- 对**上一步真实生成的** `figure.svg` 做增量修改（不是重画）；
- `change_records` 条数应等于"请求条数按 `references/EDIT-ACTION-SCHEMA.md` §1
  推算出的期望值"（`remove_entity` 会级联出 `cascade_remove_relation`）；
- 每条记录含 `action` / `target` / `before` / `after` / `reason`；
- 编辑后**全部检查重跑**（CP2），且契约门（CP3）仍为 VALID；
- **注意**：走 `--edit-svg` 时编辑请求读的是 `edit_requests` 字段；
  若 `change_records` 为空而请求非空，按 D10 查明字段名（详见该文件 §3）。

## 5. 一键核验

```bash
python "$SKILL_DIR/scripts/run_examples.py" --out /tmp/sse-examples
# 期望：exit 0；schematic / chart / edit 三步各 exit 0；
#      三份 result.json 的 G1–G8 各 exit 0（VALID）
```

`run_examples.py` 会把每步的退出码与契约校验结果直接打印出来，
任一步不符即整体非零退出 —— 这张"期望清单"因此是可自动核验的，而不是承诺。
