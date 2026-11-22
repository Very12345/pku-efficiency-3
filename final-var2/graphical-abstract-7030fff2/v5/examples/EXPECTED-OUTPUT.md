# EXPECTED-OUTPUT.md — 示例案例的期望产物（纯文本契约，替代预置二进制产物）

> 本文件用**文字**列出：在 `examples/case.json`（`case_id = example-micelle-001`）上运行
> 本 Skill 后，`--out` 目录里**必须**出现哪些文件、每个文件的契约字段是什么。
> 这是「不携带任何预置二进制/矢量资源」的替代机制：渲染件由
> `scripts/svgbuilder.py` + `scripts/preview.py` **运行时生成**，包内不留 `.svg/.png/.pdf`。
>
> 下面的数值来自本包在 2026-11-22 的**真实运行**（Windows / Python 3.13.9 / matplotlib
> 后端）。**元素数、文件字节数、`spec_sha16` 会随脚本版本变化，属预期差异**；
> 而"文件清单、字段名、status 判定、硬性门"是契约，不应变化。

## 1. 产物文件清单（`--out` 目录）

命令：`python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <out>`

| # | 文件 | 形态 | 说明 |
|-|-|-|-|
| 1 | `<case_id>_graphical_abstract.svg` | **可编辑源**（运行时生成） | 7 层 `<g id="layer:*">`；`<text>` 真文字；实体/关系/数据元素带 `data-src`、`data-entity-id`、`data-role`；`<title>/<desc>/<metadata>` 记录 Skill 版本与 build id |
| 2 | `<case_id>_graphical_abstract.png` | 渲染预览（运行时生成） | 默认 2× 分辨率（本示例 2400×1600 px）；PDF 同源几何 |
| 3 | `<case_id>_graphical_abstract.pdf` | 矢量预览（运行时生成，可选） | `figure_constraints.pdf=true` 时产出，表头必须为 `%PDF-`；不可用时 `deliverables` 里 `present:false` + `reason` |
| 4 | `spec.json` | 图面规格 | 与 SVG **同一份几何元素**；`reading_order`、`legend`、`data_encoding`、`layers` |
| 5 | `content.json` | 规范化抽取 | `entities / relations / data / panels / constraints / source_files / notes` |
| 6 | `audit.json` | 自查报告 | 见 §3 |
| 7 | `render_log.json` | 渲染日志 | `backend`（`matplotlib`/`Pillow`/`pure-python-png`）、`font`、`warnings`、`pdf` |
| 8 | `result.json` | **唯一评分产物** | 契约见 `references/OUTPUT_CONTRACT.md`；顶层字段见 §2 |

> 本包 `examples/output/` 里随附了 4、5、6、7、8 五件**在本示例上实跑产生的文本副本**
> （路径已归一化为相对路径），1/2/3 三件渲染件**故意不随包**（见 `examples/README.md`）。

## 2. `result.json` 顶层字段（必须全部出现）

**信封字段（18 个，恒在）**：
`schema_version, skill, case_id, status, summary, task, deliverables, content_summary,
provenance, sources, uncertainty, warnings, change_records, audit, generated_utc,
output_contract_echo, plan, spec_lint`

**案例 `output_contract` 回显字段（8 个，本示例）**：
`target_format, resolution_dpi, colorblind_safe, require_legend, require_scale_bar,
layer_names, provenance_attr, deliverable`

⇒ 本示例的 `result.json` 顶层**应为 26 个键**（可用
`python "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json --case "$SKILL_DIR/examples/case.json"`
核验，exit 0 = 覆盖完整）。

关键字段的期望值（示例案例）：

| 字段 | 期望值 | 说明 |
|-|-|-|
| `status` | `success` | 示例案例四要素齐全、无缺值、无越界、lint 通过 |
| `case_id` | `example-micelle-001` | 与 `case.json` 一致 |
| `skill` | `{"name":"graphical-abstract","version":"2.0.0"}` | 与 `scripts/common.py::SKILL_VERSION` 一致 |
| `plan.source` | `none`（不带 `--plan`）或 plan 文件路径（带 `--plan`） | 带 plan 时 `plan.lint.valid=true` |
| `spec_lint.valid` | `true` | 元素数本示例 113、图例 7 项、编码 7 项 |
| `content_summary` | `entities=6, relations=14, data=7`；`panels={q:2,m:3,r:4,c:3}` | 关系数含材料 `A -> B` 行补充 |
| `deliverables` | 4 条：`editable_source/svg`、`layout_spec/json`、`preview/png`、`preview/pdf` | 路径**均为相对输出目录** |
| `uncertainty` / `warnings` | `[]`（本示例） | 有降级时必须非空 |
| `output_contract_echo` | `{}`（本示例无保留键冲突） | 冲突时才非空 |
| `generated_utc` | UTC ISO 时间 | 仅信封含时间，图面布局不含时间 |

## 3. `audit.json` 必须全绿的结构判据

| 键 | 本示例实测 | 判据 |
|-|-|-|
| `checks.svg_well_formed` | `{ok:true, size_bytes:32455, layers:7}` | `ok=true`、`layers≥7` |
| `checks.png` | `{ok:true, size_bytes:397555, px:[2400,1600]}` | 签名正确、非空白 |
| `checks.pdf` | `{present:true, header_ok:true}` | 表头 `%PDF-` |
| `entity_coverage` | `{total:6, on_canvas:6, missing:[]}` | `missing` 必须为空 |
| `encoding_consistency` | `{total:7, missing_from_canvas:[]}` | 数值字符串全部上画布 |
| `bounds` | `{outside_count:0}` | 无元素越界 |
| `missing_values` | `[]` | 无缺值（有缺值 → `status=partial` 且图上占位） |
| `layout_log` | `[]` | 无溢出/收缩告警 |
| `four_element_coverage` | `{missing:[], on_canvas:[question,method,results,conclusion]}` | **Q-M-R-C 必齐**（硬性门 G7） |
| `layer_naming` | `{bad:[], missing:[], elements_without_src:0}` | 7 层命名合规、科学元素全带 `data-src` |
| `determinism_probe` | `{spec_sha16:"<16 hex>"}` | 同输入重跑必须同值 |
| `grayscale_check` | N 组弱对比对（Okabe-Ito 调色板） | 仅作提示，不阻断 |

## 4. `deliverables` 条目的最小字段

| `kind` | `format` | 必需字段 |
|-|-|-|
| `editable_source` | `svg` | `path, layers[], element_count, checks` |
| `layout_spec` | `json` | `path, note` |
| `preview` | `png` | `path, backend, checks` |
| `preview` | `pdf` | `path, checks`（未产出时 `path:null, present:false, reason`） |

## 5. 退出码与幂等性

- 成功（含 `status=partial`）：**exit 0**；输入不可读：**exit 1**；内部错误/SVG 未产出：**exit 2**；
- 同输入重跑两次：`audit.determinism_probe.spec_sha16` **必须一致**
  （示例实测 `b863154605758e84`，见 `examples/output/audit.json`）；
  SVG 与 `spec.json` 逐字节一致；PNG/PDF 允许字节差异（嵌入元数据/后端版本），
  但尺寸与几何必须一致。

## 6. 与正式案例的差异（如实声明）

- 正式案例的 `case.json`、`task.md`、材料由平台挂载（`/input/`），产物写 `/app/output/`；
- 正式案例的实体数、数据点数、面板要点数与本示例**不同**，`content_summary`、`element_count`、
  `spec_sha16` 都会不同 —— 这些**不是**验收判据；
- 验收判据恒为：**文件清单齐全 + `result.json` 覆盖契约全部字段 + `audit` 六项红线全空 +
  `status` 不虚报**。
