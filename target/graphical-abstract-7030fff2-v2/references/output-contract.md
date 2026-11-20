# output-contract.md — `result.json` 结构化结果契约（v2）

> 文件名与高分包（76.67/76.00 系）对齐：`references/output-contract.md`。
> 本文件定义本 Skill 每次运行必须产出的 `result.json`。官方运行时写在
> `/app/output/result.json`，本机运行写在 `--out` 指定目录。**契约以本文件为准**。

## 1. 总原则

1. `result.json` 必须包含 `case_id` 与案例 `output_contract` 中的**全部字段**（见 §3）。
2. 所有字段诚实：`status` 不虚报；`uncertainty` 不隐瞒；`change_records` 记真实操作。
3. 数值必须能在 `sources` 中定位；无法定位的数值不得进入画布，只能进 `uncertainty`。
4. 产物（SVG/PNG/PDF/JSON）与 `result.json` 同目录；`deliverables[].path` 为相对路径。
5. 一次运行 = 一个结果文件；同输入重跑结构一致（`audit.determinism_probe` 佐证）。
6. **方案先行**：若使用设计计划（`--plan`），计划 lint 结果与来源必须写入
   `result.plan`；最终 spec 的 lint 结果写入 `result.spec_lint`。

## 2. 顶层字段（信封）

| 字段 | 类型 | 必填 | 说明 |
|-|-|-|-|
| `schema_version` | str | 是 | 契约版本，当前 `"1.0"` |
| `skill` | object | 是 | `{name: "graphical-abstract", version: "2.0.0"}` |
| `case_id` | str | 是 | 取自 `case.json`，缺省用文件名 |
| `status` | str | 是 | `success \| partial \| failed`（判定规则见 §4） |
| `summary` | str | 是 | 1–3 句结果摘要 |
| `task` | str | 是 | 抽取到的任务一句话（可为空串，不得伪造） |
| `deliverables` | list | 是 | 各产物条目（见 §5） |
| `content_summary` | object | 是 | `entities/relations/data/panels/reading_order` 计数与顺序 |
| `provenance` | object | 是 | `source_files[]`（路径+sha256+role）、溯源说明 |
| `sources` | list | 是 | `[{ref, role}]` 来源定位清单 |
| `uncertainty` | list[str] | 是 | 全部不确定/受限项（缺值、歧义、回退、越界、lint 偏差等） |
| `warnings` | list[str] | 是 | 非阻断性警告（notes、layout_log、缺值等） |
| `change_records` | list | 是 | `[{ts, what}]` 版本/变更记录 |
| `audit` | object | 是 | 自查报告全文（含四要素覆盖 / 图层命名，见 §6） |
| `generated_utc` | str | 是 | UTC ISO 时间（仅信封含时间，图面布局不含时间） |
| `output_contract_echo` | object | 是 | 案例契约中被保留键冲突的字段（正常为空对象） |
| `plan` | object | 是 | `{source: "none"\|<plan.json 路径>, hash, lint}`（v2 新增） |
| `spec_lint` | object | 是 | `{valid, problems, spec_sha16, counts}`（v2 新增） |

## 3. output_contract 回显规则（四形态，v2 显式化）

- 案例 `output_contract` 中的字段**未与信封保留键冲突** → 直接出现在 result.json 顶层
  （同名同值）；与保留键冲突 → 顶层保留信封值，原值放 `output_contract_echo[k]`。
- 四种声明形态全覆盖、**禁止 null**：

| 形态 | case 声明示例 | result.json 处理 |
|-|-|-|
| ① 字段→类型提示 | `"resolution_dpi": 300` | 真实值；无则 `""` |
| ② 字段→容器（list） | `"target_format": ["svg","png","pdf"]` | 真实值；无则 `[]` |
| ③ 布尔开关 | `"colorblind_safe": true` | 真实布尔 |
| ④ 字段清单 | `"layer_names": [...]` | 回显实际使用的图层名 |

- 保留键集合：`schema_version, skill, case_id, status, summary, task, deliverables,
  content_summary, provenance, sources, uncertainty, warnings, change_records, audit,
  generated_utc, output_contract_echo, plan, spec_lint`。
- 判定方式：`result.json` 顶层能覆盖「信封字段 ∪ 案例 output_contract 全部字段」= 通过。

## 4. status 判定规则（v2）

| status | 条件 |
|-|-|
| `success` | SVG 良构 + PNG 有效 + 无缺值/无实体缺失/无越界/无输入 notes + **spec_lint 通过**（四要素齐全、图层命名合规、数据可溯源、图例一致） |
| `partial` | 产物完整但有：缺数值、实体缺失、越界、字体/渲染回退、输入 notes、**spec_lint 或 plan lint 任一有问题**（必须列明限制） |
| `failed` | SVG 或 PNG 未产出/无效；或 `case.json` 不可读 |

## 5. deliverables 条目

| kind | format | 必需字段 | 说明 |
|-|-|-|-|
| `editable_source` | `svg` | `path, layers[], element_count, checks` | 可编辑分层源文件；`checks` 来自 `audit.checks.svg_well_formed` |
| `layout_spec` | `json` | `path, note` | `spec.json`：与 SVG 同一几何的机器可读规格 |
| `preview` | `png` | `path, backend, checks` | 渲染预览；`backend` 如实记录 |
| `preview` | `pdf` | `path \| null, present, reason?` | 矢量预览；未生成时 `present:false` + `reason` |

`path` 一律相对输出目录；PNG/PDF 的 `checks` 来自 `audit.checks.png / checks.pdf`。

## 6. audit 子结构（v2 扩展）

从 `audit.json` 原样嵌入：

| 键 | 内容 |
|-|-|
| `checks.svg_well_formed` | `{ok, size_bytes, layers}`（分层计数） |
| `checks.png` / `checks.pdf` | 签名/尺寸/表头 |
| `entity_coverage` | `{total, on_canvas, missing[]}`（data-entity-id 覆盖） |
| `encoding_consistency` | `{total, missing_from_canvas[]}`（数值字符串上画布） |
| `bounds` | `{outside_count, outside[]}` |
| `grayscale_check` | 色盲/灰度可区分性 |
| `missing_values` | 缺数值数据点 |
| `layout_log` | 版面告警 |
| `determinism_probe` | `{spec_sha16, note}`（同输入同布局探针） |
| `four_element_coverage` | `{expected, on_canvas, missing, content_panels}`（四要素覆盖，v2 新增） |
| `layer_naming` | `{expected, found, bad, missing, elements_without_src, missing_src_roles}`（图层命名合规，v2 新增） |

## 7. 硬性门（G1–G8，交付检查）

| 门 | 判定 | 后果 |
|-|-|-|
| G1 | `case_id` 非空 | error |
| G2 | `output_contract` 全部字段回显、无 null | error |
| G3 | `status` ∈ {success, partial, failed} | error |
| G4 | SVG 存在、良构、含 ≥7 层 `layer:*` 组 | error |
| G5 | PNG 存在、签名正确、非空白 | error |
| G6 | `audit.encoding_consistency.missing_from_canvas` 为空 | error |
| G7 | 四要素覆盖无缺失（question/method/results/conclusion 都上画布） | error |
| G8 | 非空 `sources`（至少一个来源文件，带 sha256） | error |

## 8. 最小示例（`examples/output/result.json`）

```json
{
  "schema_version": "1.0",
  "case_id": "example-micelle-001",
  "status": "success",
  "plan": {"source": "none", "hash": null, "lint": {"valid": true, "problems": []}},
  "spec_lint": {"valid": true, "problems": [], "spec_sha16": "...", "counts": {...}},
  "deliverables": [ {"kind": "editable_source", "format": "svg", ...},
                    {"kind": "preview", "format": "png", "backend": "matplotlib", ...},
                    {"kind": "layout_spec", "format": "json", "path": "spec.json"} ],
  "content_summary": {"entities": 6, "relations": 5, "data": 7,
                      "panels": {"question": 2, "method": 2, "results": 2, "conclusion": 2}},
  "provenance": {"source_files": [{"path": ".../material.md", "sha256": "...", "role": "material"}]},
  "sources": [{"ref": "...material.md", "role": "material"}],
  "uncertainty": [],
  "warnings": [],
  "change_records": [{"ts": "...", "what": "skill run (graphical-abstract v2.0.0)"}],
  "audit": {...},
  "target_format": ["svg","png","pdf"],
  "resolution_dpi": 300
}
```

> `examples/output/result.json` 为**合成示例**（标注「示例，非正式案例」）；正式案例结果由平台案例实跑产出。