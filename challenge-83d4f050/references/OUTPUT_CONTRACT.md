# OUTPUT_CONTRACT.md —— result.json 字段契约

本文件定义 `result.json` 的机器可校验契约。`scripts/result_writer.py` 按本契约生成，
`scripts/validate.py`（检查 F03）按本契约验收。**凡是 case.json `output_contract`
中声明的字段，都必须出现在 result.json 顶层；未声明时按类型给 "" / [] / {}，不出现 null。**

## 1. 顶层字段

| 字段 | 类型 | 必需 | 说明 |
|---|---|---|---|
| `case_id` | str | ✅ | 案例标识，取自 case.json（缺省用文件名） |
| `title` | str | ✅ | 图标题 |
| `status` | str | ✅ | `success` / `partial` / `failed`（定义见 §3） |
| `contract_version` | str | ✅ | 本契约版本（当前 "1.0"） |
| `skill` | dict | ✅ | {name, version, contract} |
| `deliverables` | dict | ✅ | 产物清单（见 §2） |
| `scientific_content` | dict | ✅ | 科学内容（实体/边/图例/布局/计数） |
| `evidence_sources` | list | ✅ | 去重后的来源明细 [{ref, kind, line}] |
| `data_mapping` | dict | ✅ | 数据编码映射（字段、低/高色、标签） |
| `extraction` | dict | ✅ | {method: auto-draft/manual, verified_by_agent, note} |
| `export_checks` | list | ✅ | 每个导出件的检查结果 |
| `self_check` | dict | ✅ | {passed, checks[], failures[], warnings[]} |
| `uncertainty` | list | ✅ | [{item, reason, mitigation}]，空数组即可 |
| `change_records` | list | ✅ | [{ts, what, why, by}]，每次实质修改一条 |
| `files` | list | ✅ | 输出目录下产物文件名（相对） |
| `provenance` | dict | ✅ | {skill, skill_version, contract, ts, command, material_refs, case_file} |
| `*` | 依 case.json | ✅ | `output_contract` 声明的自定义字段，缺省按类型填空 |

## 2. deliverables 与 scientific_content

```
deliverables:
  editable_sources: [ {path, format: "svg", layers: [...], well_formed, note} ]
  previews:         [ {path, format: "png", dpi, width_px, height_px} ]   # 可空
  exports:          [ {path, format: "pdf", note} ]                       # 可空

scientific_content:
  entities: [ {id, name, type, compartment, data{字段:值}, note, source[{ref,kind,line}]} ]
  edges:    [ {id, from, to, type, subtype, evidence, label, note,
               feedback: bool, source[{ref,kind,line}]} ]
  legend:   { title, entities{类型→样式}, edges{类型→样式},
              evidence_width{strong/moderate/weak}, dash_note,
              data_mapping{field,label_zh,low,high,...}, direction_note }
  layout:   { canvas{width,height}, compartments[{id,label_zh,label_en,rect}],
              constraints{}, warning列表(可选) }
  counts:   { entities, edges, compartments }
```

- 实体 type 枚举：`protein / gene / complex / rna / small_molecule / other`。
- 边 type 枚举：`activation / inhibition / binding / modification / transport`，
  evidence 枚举：`strong / moderate / weak`。
- `source.kind` 枚举：`material`（材料原文）、`data_table`（材料数据表）、
  `common_knowledge`（公认常识）、`assumption`（推断/假设——必须在 uncertainty 说明）。
- 图例实体/边样式中的颜色、线宽与图面实际使用**逐值一致**（validate L01/L02/L05）。

## 3. status 语义（诚实记录）

| status | 条件 |
|---|---|
| `success` | 全部阻断性检查通过（self_check.passed=true），且有 SVG 源文件 |
| `partial` | 有 SVG 源但存在失败项或预览缺失/未经人工核验的自动草稿等（失败/警告全部列明） |
| `failed` | 无法产出可编辑源文件（材料不可解析且无 --model-file），或 SVG 不合法 |

- 自动抽取草稿未由 Agent 复核时，`extraction.verified_by_agent=false`，并必须在
  `uncertainty` 首条记录；复核后可改 model.json 置 true 重跑。
- 缺失软件状态（如 matplotlib 不可用导致无 PNG/PDF）记录在 `export_checks` 与
  `deliverables`（预览数组为空），不假装生成。

## 4. 反编造规则

- 数值（表达量、显著性、置信度）必须能在材料中定位到出处，否则标注假设并在 uncertainty 说明。
- 不写平台未提供的评分/分数；不编造材料里不存在的实体或相互作用。
- `change_records` 保留从“读取输入”到“最终导出”的完整链，人工修正必须逐条登记。

## 5. 最小示例（示意）

```json
{
  "case_id": "example-egfr-mapk",
  "status": "success",
  "contract_version": "1.0",
  "deliverables": {"editable_sources": [{"path": "diagram.svg", "format": "svg"}],
                   "previews": [{"path": "diagram.png", "format": "png"}],
                   "exports": [{"path": "diagram.pdf", "format": "pdf"}]},
  "scientific_content": {
    "entities": [{"id": "e1", "name": "EGFR", "type": "protein",
                  "compartment": "membrane", "data": {"表达量": "0.82"},
                  "source": [{"ref": "materials/x.md", "kind": "material", "line": 9}]}],
    "edges": [{"id": "r2", "from": "e1", "to": "e3", "type": "activation",
               "evidence": "moderate",
               "source": [{"ref": "materials/x.md", "kind": "material", "line": 20}]}],
    "legend": {}, "layout": {}, "counts": {"entities": 1, "edges": 1, "compartments": 1}
  },
  "evidence_sources": [{"ref": "materials/x.md", "kind": "material", "line": 9}],
  "uncertainty": [], "change_records": [],
  "export_checks": [], "self_check": {"passed": true, "checks": []},
  "files": ["diagram.svg", "diagram.png", "diagram.pdf", "model.json", "result.json"]
}
```

## 6. 验收命令

```bash
python3 scripts/validate.py  # 或 main.py 运行末的自检（F01/F03 检查）
```
`result.json` 应包含本契约 §1 全部字段，且 `self_check.failures == []`。