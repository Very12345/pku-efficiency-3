# OUTPUT_CONTRACT.md — `result.json` 结构化结果契约（合规重打包版）

> 本文件是**唯一契约权威**：`result.json` 的顶层字段、`output_contract` 四形态回显、
> status 判定与硬性门 G1–G8 都以本文为准。相对 build 基础包的 `OUTPUT_CONTRACT.md`，
> 本版升级为：**四形态回显（禁止 null）+ 硬性门 G1–G8 + topology/legend_audit
> 审计嵌入 + 确定性探针**，并按技能包合规要求改用全大写文件名
> `references/OUTPUT_CONTRACT.md`（同目录还有 `RUBRIC_MAP.md`）。
> 官方运行时写在 `/app/output/result.json`；本机运行写在 `--out` 指定目录。
> **契约以本文件为准**；机器校验入口 `scripts/check_contract.py`。

## 1. 总原则

1. `result.json` 必须包含 `case_id` 与案例 `output_contract` 中的**全部字段**（§3）。
2. 所有字段诚实：`status` 不虚报；`uncertainty` 不隐瞒；`change_records` 记真实操作。
3. 数值（表达量、显著性、置信度）必须能在 `sources` 中定位；无法定位的数值不得进入
   画布颜色编码（核对 `legend_audit/E01`、`T03`）。
4. 产物（SVG/PNG/PDF/JSON）与 `result.json` 同目录；`deliverables[].path` 为相对路径。
5. 一次运行 = 一个结果文件；同输入重跑结构与图面一致（`self_check.determinism` 佐证：
   `model_sha16`/`svg_sha16` 为输入与布局纯函数产物，同输入双跑 SVG/model 逐字节一致）。

## 2. 顶层字段（信封）

| 字段 | 类型 | 必填 | 说明 |
|-|-|-|-|
| `case_id` | str | 是 | 取自 `case.json`，缺省用文件名 |
| `title` | str | 是 | 图标题 |
| `status` | str | 是 | `success \| partial \| failed`（判定规则 §4） |
| `contract_version` | str | 是 | 本契约版本 `"1.1"` |
| `skill` | object | 是 | `{name, version: "2.0.0", contract}` |
| `deliverables` | object | 是 | `editable_sources[] / previews[] / exports[] / audits[]`（§5） |
| `scientific_content` | object | 是 | entities/edges/legend/layout/counts（§6） |
| `evidence_sources` | list | 是 | 去重来源 `[{ref, kind, line}]` |
| `data_mapping` | object | 是 | 数据编码映射（字段、低/高色、标签） |
| `extraction` | object | 是 | `{method, verified_by_agent, note}` |
| `export_checks` | list | 是 | 每个导出件检查（sha256/尺寸/dpi/告警） |
| `topology` | object | 是 | 拓扑审计 `{checks[], failures[], warnings[]}`（v2 新增） |
| `legend_audit` | object | 是 | 图例/数据编码审计（v2 新增） |
| `self_check` | object | 是 | `{passed, checks, failures, warnings, determinism}` |
| `gates` | object | 是 | `g1..g8` 硬性门判定（§7，v2 新增） |
| `uncertainty` | list | 是 | `[{item, reason, mitigation}]` |
| `change_records` | list | 是 | `[{ts, what, why, by}]` |
| `files` | list | 是 | 输出目录产物文件名（相对） |
| `provenance` | object | 是 | skill/version/ts/command/material_refs/case_file/schema |
| `*` | 依 case.json | 是 | `output_contract` 声明的自定义字段，缺省按类型填空 |

## 3. output_contract 回显规则（四形态，v2 显式化）

案例 `output_contract` 中的字段直接出现在 result.json 顶层（同名同值）；未命中 pipeline
真实值（`null`/`""`/`[]`/`{}`）时按声明形态填空，**禁止 null**：

| 形态 | case 声明示例 | result.json 处理 |
|-|-|-|
| ① 字段→标量 | `"custom_demo_field": "示例文本"` | 真实值；无则 `""` |
| ② 字段→容器(list) | `"custom_list_field": ["a"]` | 真实值；无则 `[]` |
| ③ 布尔开关 | `"colorblind_safe": true` | 真实布尔；无则 `false` |
| ④ 数值/字典 | `"resolution_dpi": 150` | 真实值；无则 `0` / `{}` |

判定方式：`script/check_contract.py --result result.json --case case.json` 检查
「信封字段 ∪ 案例 output_contract 全部字段」是否齐全且无顶层 null。

## 4. status 判定规则（v2）

| status | 条件 |
|-|-|
| `success` | SVG 良构 + PNG 有效 + 无失败项 + **提取已人工核验**（`extraction.verified_by_agent=true`）+ 硬性门 G1–G8 全过 |
| `partial` | 产物完整但有：任何 fail（缺预览、审计失败、契约缺项）、或**自动草稿未核验**、或 warn 需说明（必须列明） |
| `failed` | 无法产出可编辑源（材料不可解析且无 --model-file）、SVG 不合法、或 **CP2 机制规格未过 schema 门** |

## 5. deliverables 条目

| 组 | 条目 | 必需字段 | 说明 |
|-|-|-|-|
| editable_sources | `diagram.svg` | `path, format:"svg", layers[], well_formed, note` | 分层可编辑源，7 个 `layer-*` 组 + `data-id/data-type/data-source` |
| previews | `diagram.png` | `path, format:"png", dpi, width_px, height_px` | 预览；可空数组 |
| exports | `diagram.pdf` | `path, format:"pdf", note` | 预览用矢量导出；可空数组 |
| audits | `topology.json` `legend_audit.json` | 文件名列表 | 审计产物（v2） |

## 6. scientific_content 子结构

```
entities: [ {id, name, type, compartment, data{字段:值}, note, uncertain,
             source[{ref, kind, line}]} ]
edges:    [ {id, from, to, type, subtype, evidence, label, note, feedback,
             source[{ref, kind, line}]} ]
legend:   { title, entities{类型→样式}, edges{类型→样式},
            evidence_width{strong/moderate/weak}, dash_note,
            data_mapping{field,label_zh,low,high}, direction_note, version_note }
layout:   { canvas{width,height}, compartments[{id,label_zh,label_en,rect}],
            constraints{}, warnings[]? }
counts:   { entities, edges, compartments }
```

- 实体 type 枚举：`protein / gene / complex / rna / small_molecule / other`。
- 边 type 枚举：`activation / inhibition / binding / modification / transport`；
  evidence 枚举：`strong / moderate / weak`。
- `source.kind` 枚举：`material`（材料原文）、`data_table`（材料数据表）、
  `common_knowledge`（公认常识）、`assumption`（推断/假设——必须在 uncertainty 说明）。
- 图例实体/边样式中的颜色、线宽与图面实际使用**逐值一致**（legend_audit L01/L02/L04/L05）。

## 7. 硬性门（G1–G8，交付检查）

| 门 | 判定 | 后果 |
|-|-|-|
| G1 | `case_id` 非空 | error |
| G2 | `output_contract` 全部字段回显、无 null | error |
| G3 | `status` ∈ {success, partial, failed} | error |
| G4 | SVG 存在、良构、含 ≥7 层 `layer-*` 组 | error |
| G5 | PNG 存在且可打开 | error |
| G6 | 图例覆盖全部在用实体/边类型（L01/L02 无 fail） | error |
| G7 | 实体/边全部带 source（T01/T02 无 fail） | error |
| G8 | `topology.json` 与 `legend_audit.json` 已产出 | error |

任一门 error → 该条目 `gates.gN.pass=false`；status 不得为 success（见 §4）。

## 8. 最小示例

见 `assets/result.template.json`（结构模板，示例非正式案例）与
`examples/output/result.json`（本机实跑产物，`example: true` 标注）。

## 9. 验收命令

```bash
python3 scripts/check_contract.py --result <out>/result.json --case <case.json>   # exit 0 = 契约通过
python3 scripts/validate_figure.py --out <out>                                     # exit 0 = 全检查通过
```