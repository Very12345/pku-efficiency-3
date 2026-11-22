# EXPECTED-OUTPUT — 示例上的期望产物与**期望判据读数**

本文件替代"预置的示例产物"。这里用**文字**列出三个合成示例上真实运行时应出现的
文件与读数，并**按机制分组**——因为本变体的主张是"五个机制各自可被检验"，
期望值就应该落在机制上。

> 实测记录见 `TEST.md` §V1–§V6；本文件是"期望"，`TEST.md` 是"实测"。

## 1. 公共产物与归属机制

| 文件 | 说明 | 主要检查名 | 归属机制 |
|-|-|-|-|
| `figure.svg` | 可编辑分层源文件 | `svg.editable_text`、`svg.layers`、`svg.manifest_embedded`、`svg.manifest_matches`、`svg.data_entity_attrs` / `svg.data_relation_attrs` / `svg.data_source_attrs` | M2（+M4 的可编辑性判定） |
| `figure.png` | 渲染预览 | `bitmap.dimensions`、`bitmap.dpi_print`、`bitmap.colourspace` | M4 |
| `figure.pdf` | 矢量导出件 | `pdf.header`、`pdf.pages`、`pdf.fonts_embedded` | M4 |
| `result.json` | 结构化结果 | 契约 §1 全部字段 + `case_id` | 全部（读数面） |

## 2. M1 的期望读数（`case.json`）

| 项目 | 期望 |
|-|-|
| `verification.spec_lint.valid` | `true`（示例清单合法） |
| `spec.legend_missing_kinds` | ok（3 类箭头都有图例条目） |
| `spec.containment_group` | 不出现 fail（示例无 containment 关系；若加了必须落到 `groups`） |
| 推翻实验 | 把任一 `kind` 改成 `gibberish` → `spec_lint.py` **exit 1 / INVALID**；走 `main.py` → `status=partial`、`fails=[spec_lint.spec.relation_kind]` |

## 3. M2 的期望读数

| 项目 | 期望 |
|-|-|
| `svg.manifest_embedded` / `svg.manifest_matches` | 均 ok |
| `svg.data_entity_attrs` / `svg.data_relation_attrs` / `svg.data_source_attrs` | 6/6、5/5、5/5 |
| 编辑后 | `change_records` 条数 == 按 `scripts/edit.py` 推算的期望条数（含 `cascade_remove_relation`） |
| 推翻实验 | 用一个**没有内嵌清单**的 SVG 做 `--edit-svg` → **exit 2** + `FATAL: no embedded ER manifest…` |
| **盲区取证** | 目标 id 不存在时：日志 `[edit] fail …`、`change_records` 为 **0**、退出码仍 **0** ⇒ 必须靠条数对拍 |

## 4. M4 / M5 的期望读数

| 项目 | 期望（本机实测值） |
|-|-|
| `bitmap.dimensions` | 4500×2580 |
| `bitmap.dpi_print` | 18 cm 宽有效 ≈635 DPI（≥300） |
| `bitmap.colourspace` | RGBA（RGB 族） |
| `svg.editable_text` | ok（真实 `<text>`） |
| `font.cjk` | True（`textfont.py --probe` 的结论） |
| 推翻实验（M4） | 把 `--dpi` 降到阈值以下时 `bitmap.dpi_print` 应随之变化；若不变则判据失效 |
| 推翻实验（M5） | 比对 `verification.render` 记录的族名与渲染日志：同机同次必须一致 |

## 5. `case_chart.json`（chart）与 `case_edit.json`（edit）的期望

**chart**：`figure_type = chart`；数据只来自 `sources/data-table.csv`；
`data_mapping.color_count` ≥ 唯一类别数；G8 不得出现表外类别；
把数据表数值翻倍后重跑，`figure.svg` 的 sha256 应**改变**（M1+M2 联动）。

**edit**：`change_records` 每条含 `action`/`target`/`before`/`after`/`reason`；
编辑后全部 CP2 检查重跑且契约门仍 VALID；未改动元素保持原样（M2 的增量性）。

## 6. 一键核验（含两个推翻实验）

```bash
python "$SKILL_DIR/scripts/run_examples.py" --out /tmp/sse-examples
# 期望：exit 0；三步各 exit 0；三份契约各 VALID
python "$SKILL_DIR/scripts/spec_lint.py" --manifest <坏清单>
# 期望：exit 1（M1 的推翻实验只在机制失效时才返回 0）
```
