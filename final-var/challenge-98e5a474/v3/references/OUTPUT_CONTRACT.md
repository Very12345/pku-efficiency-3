# OUTPUT_CONTRACT — result.json 契约（v2 字段，v3 机制版说明）

本文件定义 `scripts/main.py` 在 `/app/output/result.json` 产出的结构化
结果契约。**每个案例返回一份**；所有字段都由脚本诚实生成，Agent 只
补充需要科学判断的叙述性字段（如 task_summary、uncertainty），禁止
编造数据或评分。

若 `case.json` 自带 `output_contract` 对象，脚本会把其中的每个键
**同样回显到 result.json 顶层**（缺失值按其声明类型给 `""` / `[]` /
`{}` / `0` / `false`，禁 `null`），因此无论平台的字段清单如何，结果
都能完整对齐。**这是四形态回显**：string / array / object / number
（boolean）分别用对应类型的空值补齐。

> **本变体（v3 · 机制显性）在此补一层"机制归属"，不改任何字段名或结构**：
> 契约里每一个可判定的字段，都属于某个机制的可证伪判据的取值来源：
>
> | 字段 / 检查族 | 归属机制 | 用途 |
> |-|-|-|
> | `verification.spec_lint`（`valid` / `issues`） | **M1** | 生成前门是否通过；坏清单应使其为 false |
> | `artifacts[*]`、`svg.manifest_embedded` / `svg.manifest_matches` / `svg.data_entity_attrs` / `svg.data_relation_attrs` / `svg.data_source_attrs` | **M2** | 源文件是否自描述、是否可增量编辑 |
> | `sources`、`uncertainty`（PDF 相关条目） | **M3** | 材料是否被如实处理（含不可抽取的报告） |
> | `bitmap.*`、`pdf.*`、`svg.editable_text`、`artifact.<role>` | **M4** | 导出预检的读数 |
> | `verification.render`、`font.cjk`、`tool_versions` | **M5** | 字体事实源的结论 |
>
> **契约管不到的两处**（属机制盲区，见 `references/MECHANISM.md`）：
> ① `edit.*` 类编辑问题只进 stdout，不进本文件 ⇒ 靠"请求条数 vs `change_records` 条数"对拍；
> ② `--skip-checks` 会让 `verification.checks` 为空，而 G2 只看 `fail_count`
>  ⇒ "未检查"仍可能过门，因此该次运行不得当作交付版本。
>
> 全部检查名的完整清单（含级别与科学含义）见 `references/CHECK-INDEX.md`。

## 0. 硬性门（G1–G8，`scripts/validate_result.py` 执行）

| 门 | 内容 | 违例后果 |
|-|-|-|
| G1 | `case_id` 存在且与 case 一致 | INVALID |
| G2 | `status` ∈ {success,partial,failed}；success 时 `verification.checks.fail_count==0` 且 CP1 `spec_lint.valid` 非 false | INVALID |
| G3 | `artifacts` 中每个文件都存在 | INVALID |
| G4 | `evidence/sources/uncertainty/change_records/legend_mapping/data_mapping` 类型正确 | INVALID |
| G5 | `output_contract` 每个键回显到顶层，且非 null、类型形状正确 | INVALID |
| G6 | `verification` 含 `checks/spec_lint/traceability` | INVALID |
| G7 | 同时存在可编辑源（role=figure) + 预览 (role=preview) + 导出（pdf/eps/tiff）三类产物 | INVALID |
| G8 | chart 类别集合与 manifest 数据表一致（不出现数据表之外的新类别） | INVALID |

## 1. 顶层字段

| 字段 | 类型 | 必填 | 说明 |
|-|-|-|-|
| `case_id` | string | 是 | 输入 case_id（缺失时取 case 文件名的 stem） |
| `skill` | object | 是 | `{name, version, display}` |
| `status` | enum | 是 | `success` / `partial`（存在 fail 或 CP1 lint 不通过）/ `failed`（流水线未完成） |
| `workorder` | string | 是 | 任务类型（缺省 `editable_relationship_schematic`） |
| `task_summary` | string | 是 | 任务说明（可空） |
| `figure_type` | string | 是 | `schematic` / `chart` |
| `title` | string | 是 | 图题 |
| `main_result` | object | 是 | 主结果摘要（见下） |
| `artifacts` | array | 是 | 产物清单，每项 `{role, format, path(相对 out), abspath, checks, extra}` |
| `evidence` | object | 是 | `{sources, entities[], relations[]}` — 每个实体/关系带 `source`+`evidence` |
| `legend_mapping` | array | 是 | 图例条目（key/arrow/line/label/source） |
| `data_mapping` | object | 是 | 图表类别↔颜色映射 / 原始 data |
| `verification` | object | 是 | `{checks, render, traceability, spec_lint}` 检查记录 |
| `determinism` | object | 是 | `{spec_sha16, note}` — 同一输入双跑一致性探针 |
| `sources` | array | 是 | 实际读取的来源材料（相对路径） |
| `uncertainty` | array | 是 | `[{item, note}]` 不确定性/限制，诚实记录 |
| `change_records` | array | 是 | 编辑任务的 before→after 记录（无编辑时为空数组） |
| `status_notes` | string | 是 | 状态说明 |
| `generated_at` | string | 是 | ISO8601 时间（`--fixed-time` 可在确定性双跑时固定） |
| `generator` | string | 是 | `scientific-schematic-editor` |
| `tool_versions` | object | 是 | python/matplotlib/Pillow/numpy/reportlab 版本 |

## 2. main_result

```jsonc
{
  "figure_type": "schematic",
  "title": "…",
  "entity_count": 6, "relation_count": 5, "group_count": 3,
  "deliverables": {
    "figure": {"path": "figure.svg", "format": "svg"},     // 可编辑源
    "preview": {"path": "figure.png", "format": "png"},
    "pdf":     {"path": "figure.pdf", "format": "pdf"}      // 导出件
  }
}
```

## 3. artifacts 项的 role 约定

| role | format | 含义 |
|-|-|-|
| `figure` | svg | **可编辑分层源文件**（手写 XML 或 matplotlib fonttype=none，文字均为 `<text>`，带 data-* 溯源属性） |
| `preview` | png | 渲染预览（matplotlib 镜像同一 layout+manifest） |
| `pdf` / `tiff` / `eps` | 对应格式 | 目标导出件（矢量 PDF 编辑器/期刊可用） |

> 机制归属（本变体附加说明，不改变上表字段）：三类产物是**M2**（可编辑源自描述）
> 与**M4**（导出预检）的读数载体；`artifact.<role>` 逐 role 报缺。

## 4. verification

- `checks`：每条 `{check, level: ok|warn|fail|ack, detail}`，含：
  `svg.editable_text/svg.layers/svg.manifest_embedded/svg.manifest_matches/
  svg.data_entity_attrs/svg.data_relation_attrs/svg.data_source_attrs/
  svg.title_exists`、`bitmap.dimensions/bitmap.dpi_print/bitmap.colourspace`、
  `pdf.header/pdf.pages/pdf.fonts_embedded`、`legend.missing_kinds/
  legend.orphan_items`、`data_mapping.*`（含 `data_mapping.color_count`）、
  `traceability.*`、`font.cjk`、`artifact.<role>`；
- `spec_lint`：CP1 门（**机制 M1**）`{valid, fail_count, warn_count, issues}`
  （`--lint` 默认开启；`--no-lint` 时为空对象）；
- `traceability`：实体/关系带来源+证据的比例；
- `render`：渲染信息（font/cjk_ok/layout/mapping，**机制 M5** 的结论面）。

> 上面列的是**常用子集**。脚本还会产出 `svg.exists/readable`、
> `bitmap.exists/readable/pil`、`pdf.exists/readable`、`data_mapping.rows/unit/
> legend_consistency`、`traceability.data_table`、`pipeline`、以及 CP1 的
> `spec.*` 全族。**全表**见 `references/CHECK-INDEX.md`；
> `scripts/doccheck.py` 会自动对拍"文档提到的检查名"与"代码真实产出的检查名"。

## 5. status 的诚实语义

- **success**：全部检查 ok（warn 已由 Agent 在 `acknowledged_issues`
  中确认）且 CP1 lint 无 fail；
- **partial**：存在 fail 检查**或 CP1 lint 有 fail**；脚本仍然写出全部
  产物与检查明细，绝不把失败伪装成成功；
- **failed**：case 无法解析、清单缺失或渲染异常；仍写出含
  `pipeline` fail 的 result.json，工作不丢失。

对应关系（**机制可证伪判据的读数面**）：坏清单 → `partial` + `spec_lint.*` fail（M1）；
无依据 → `failed` + `pipeline`（不造假）。

## 6. 产物文件名（相对 /app/output）

| 场景 | 文件 |
|-|-|
| schematic | `figure.svg`（源）+ `figure.png`（预览）+ `figure.pdf`（导出） |
| chart | `figure.svg`（源，fonttype=none）+ `figure.png` + `figure.pdf` |
| 编辑任务 | 同名覆盖 + `change_records` 记录 before→after |
| 可选导出 | `--exports tiff,eps` 追加 `figure.tiff` / `figure.eps` |
| `--base-name <n>` | 文件名以 `<n>` 为前缀 |

## 7. 校验方式

```bash
python <skill_root>/scripts/validate_result.py \
    --case /input/case.json --result /app/output/result.json
# VALID（G1–G8 全过）即契约通过；退出码 0
```

配套（本变体新增，均为只读/复跑，不改产物）：

```bash
PYTHONDONTWRITEBYTECODE=1 python -B <skill_root>/scripts/doccheck.py   # 判据未漂移
python <skill_root>/scripts/run_examples.py --out /tmp/sse-examples    # 三示例端到端
```
