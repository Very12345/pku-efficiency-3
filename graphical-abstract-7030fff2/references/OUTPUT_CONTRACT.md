# OUTPUT_CONTRACT —— `result.json` 结构化结果契约

本文件定义本 Skill 每次运行必须产出的 `result.json`。官方运行时写在 `/app/output/result.json`，
本机运行时写在 `--out` 指定目录。**契约以本文件为准**；脚本实现见 `scripts/main.py`。

## 1. 总原则

1. `result.json` 必须包含 `case_id` 与案例 `output_contract` 中的**全部字段**（见 §3 冲突规则）。
2. 所有字段诚实：`status` 不虚报；`uncertainty` 不隐瞒；`change_records` 记真实操作。
3. 数值必须能在 `sources` 中定位；无法定位的数值不得进入画布，只能进 `uncertainty`。
4. 产物（SVG/PNG/PDF/JSON）与 `result.json` 同目录；`deliverables[].path` 为**相对该目录**的路径。
5. 一次运行 = 一个结果文件；同输入重跑结构一致（`audit.determinism_probe` 佐证）。

## 2. 顶层字段（信封）

| 字段 | 类型 | 必填 | 说明 |
|-|-|-|-|
| `schema_version` | str | 是 | 契约版本，当前 `"1.0"` |
| `skill` | object | 是 | `{name: "graphical-abstract", version: "1.0.0"}` |
| `case_id` | str | 是 | 取自 `case.json` 的 `case_id`/`id`/`case`，缺省用文件名 |
| `status` | str | 是 | `success` \| `partial` \| `failed`（判定规则见 §4） |
| `summary` | str | 是 | 1–3 句结果摘要 |
| `task` | str | 是 | 抽取到的任务一句话（可为空串，不得伪造） |
| `deliverables` | list | 是 | 各产物条目（见 §5） |
| `content_summary` | object | 是 | `entities/relations/data/panels/reading_order` 计数与顺序 |
| `provenance` | object | 是 | `source_files[]`（路径+sha256+role）、溯源说明 |
| `sources` | list | 是 | `[{ref, role}]` 来源定位清单 |
| `uncertainty` | list[str] | 是 | 全部不确定/受限项（缺值、歧义、回退、越界等） |
| `warnings` | list[str] | 是 | 非阻断性警告（notes、layout_log、缺值等） |
| `change_records` | list | 是 | `[{ts, what}]` 版本/变更记录（Skill 版本、读取源文件哈希、人工修改） |
| `audit` | object | 是 | 自查报告全文（见 §6） |
| `generated_utc` | str | 是 | UTC ISO 时间（仅信封字段含时间，图面布局不含时间，保证结构稳定） |
| `output_contract_echo` | object | 是 | 案例契约中被保留键冲突的字段（正常情况下为空对象） |

## 3. output_contract 字段镜像规则

- 案例 `output_contract` 中**未与信封保留键冲突**的字段：**直接出现在 result.json 顶层**（同名同值）。
- 与保留键冲突的字段（如案例契约里也有 `status`）：顶层保留信封值，原值放入 `output_contract_echo[status]`。
- 保留键集合（信封字段 + 下述）：`schema_version, skill, case_id, status, summary, task, deliverables,
  content_summary, provenance, sources, uncertainty, warnings, change_records, audit, generated_utc,
  output_contract_echo`。
- 判定方式：`result.json` 顶层能覆盖「信封字段 ∪ 案例 output_contract 全部字段」即为通过；
  平台侧可据此校验「所有 original output_contract fields 均存在」。

## 4. status 判定规则

| status | 条件 |
|-|-|
| `success` | SVG 良构 + PNG 有效 + 无缺值/无实体缺失/无越界/无输入 notes |
| `partial` | 产物完整但有：缺数值、实体缺失、越界、字体/渲染回退、输入 notes 之一（**必须列明限制**） |
| `failed` | SVG 或 PNG 未产出/无效；或 `case.json` 不可读（此时不写 result.json，stderr 报错；已落盘的半成品与 `failed` status 一起说明） |

## 5. deliverables 条目

| kind | format | 必需字段 | 说明 |
|-|-|-|-|
| `editable_source` | `svg` | `path, layers[], element_count, checks` | 可编辑分层源文件；`checks` 来自 `audit.checks.svg_well_formed` |
| `layout_spec` | `json` | `path, note` | `spec.json`：与 SVG 同一几何的机器可读规格 |
| `preview` | `png` | `path, backend, checks` | 渲染预览；`backend` 如实记录 matplotlib/Pillow/pure-python-png |
| `preview` | `pdf` | `path \| null, present, reason?` | 矢量预览；未生成时 `present:false` + `reason` |

`path` 一律相对输出目录；PNG/PDF 的 `checks` 来自 `audit.checks.png / audit.checks.pdf`
（`{ok, size_bytes, px/pts 尺寸}`、`{present, header_ok}`）。

## 6. audit 子结构

从 `audit.json` 原样嵌入：

| 键 | 内容 |
|-|-|
| `checks.svg_well_formed` | `{ok, size_bytes, layers}` 或 `{ok:false, error}` |
| `checks.png` | `{ok, size_bytes, px:[w,h]}`（含 PNG 签名校验） |
| `checks.pdf` | `{present, size_bytes, header_ok}` 或 `{present:false, reason}` |
| `entity_coverage` | `{total, on_canvas, missing[]}`（data-entity-id 覆盖） |
| `encoding_consistency` | `{total, missing_from_canvas[]}`（每个数值字符串出现在 SVG 文本） |
| `bounds` | `{outside_count, outside[]}`（画布越界元素） |
| `grayscale_check` | `{default_colorblind_palette, min_pairwise_luminance_gap, weak_pairs[]}` |
| `missing_values` | 缺数值的数据点 label 列表 |
| `layout_log` | 版面告警（缩字号、截断、溢出） |
| `determinism_probe` | `{spec_sha16, note}`（同输入同布局的哈希探针） |

## 7. 最小示例（见 `examples/output/result.json`）

```json
{
  "schema_version": "1.0",
  "case_id": "example-micelle-001",
  "status": "success",
  "deliverables": [ {"kind": "editable_source", "format": "svg", ...},
                    {"kind": "preview", "format": "png", "backend": "matplotlib", ...} ],
  "content_summary": {"entities": 6, "relations": 5, "data": 7, "panels": {...}},
  "provenance": {"source_files": [{"path": ".../material.md", "sha256": "...", "role": "material"}]},
  "sources": [{"ref": "...material.md", "role": "material"}],
  "uncertainty": [],
  "warnings": [],
  "change_records": [{"ts": "...", "what": "skill run (graphical-abstract v1.0.0)"}],
  "audit": {...},
  "target_format": ["svg","png","pdf"]
}
```

> `examples/output/result.json` 为**合成示例**（标注「示例，非正式案例」），供接口演示；正式案例结果由平台案例实跑产出。