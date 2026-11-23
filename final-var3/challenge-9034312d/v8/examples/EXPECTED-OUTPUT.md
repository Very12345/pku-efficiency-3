# EXPECTED-OUTPUT.md — 示例案例的期望产物（文字版）

> 本文件用**文字**列出本 Skill 在示例案例上应产出的文件清单、契约字段与实测值，
> **替代随包的 `figure.svg`/`figure.png`/`figure.pdf` 等非文本产物**：
> 平台对 Skill 资源只接受 UTF-8 文本文件（≤50 个、单文件 ≤500KB、总计 ≤2MB、无符号链接），
> 因此这三个交付件改为**运行时现场生成**，其正确性由下面的清单 + `scripts/check.py` 保证。
> 全部数值为**本机实测**（Python 3.13.9 / Pillow 12.3.0 / reportlab 5.0.0），
> 示例案例为**合成**案例（示例，非正式案例），不代表平台正式评分。

## 1. 每次运行必产出的 7 个文件（`<out>/<case_id>/`）

| # | 文件 | 类型 | 内容要点 | 由谁生成 |
|-|-|-|-|-|
| 1 | `evidence.json` | 文本 | 证据链：每条实体/关系带 `locator`+`quote`；`sources[]` 带材料 `sha256`+`size`+`role` | `scripts/gain_evidence.py` |
| 2 | `layout.json` | 文本 | 布局模型：每实体 `x/y/w/h`、每条关系正交连线路径、图例、画布尺寸 | `scripts/layout.py` |
| 3 | `figure.svg` | **运行期** | 可编辑分层 SVG：5 层 `layer:*`；`<text>` 真实文本；实体组带 `data-entity/data-source/data-kind/data-stage` | `scripts/render_svg.py` |
| 4 | `figure.png` | **运行期** | PNG 预览（200 DPI，PIL + 本机中文字体） | `scripts/export_preview.py` |
| 5 | `figure.pdf` | **运行期** | PDF 预览（reportlab 矢量，CID 字体 `STSong-Light`） | `scripts/export_preview.py` |
| 6 | `verify_report.json` | 文本 | 校验报告：`layers/editable_text/arrows/no_dangling/numbering_continuous/legend_kinds/connection_rules` 全 true + `determinism.spec_sha16` | `scripts/svg_verify.py` |
| 7 | `result.json` | 文本 | 契约结果：18 个顶层字段（见 §3） | `scripts/main.py` |

**图层命名（固定）**：`layer-background`、`layer-title`、`layer-arrows`、`layer-entities`、
`layer-legend`。

## 2. 两个示例案例的期望值（本机实测）

| 项 | ① route（`case.json` + `task.md`） | ③ apparatus（`apparatus_spec.example.json`） |
|-|-|-|
| `case_id` | `demo-biotech-route-01` | `demo-apparatus-001` |
| `figure_type` / `extraction` | `route` / `structured` | `apparatus` / `structured` |
| `status` | `success` | `success` |
| 实体 / 关系 | **10 / 9** | **6 / 5** |
| `evidence.items` 条数 | **19** | **11** |
| `sources[]` | `case.json`、`task.md` | `apparatus_spec.example.json` |
| 步骤编号 | 1..7 连续（E1,E2,E4,E6,E7,E8,E10） | 无（apparatus 不编号） |
| 图例 kind 集合 == 图面 kind 集合 | `step/material/data/milestone` | `device/material/product/waste` |
| SVG 图层数 / `<text>` 数 / 实体组数 | 5 / 24 / 10 | 5 / 16 / 6 |
| 画布（实际 → 请求） | 311.11×166.0 mm ← 300×190 | 188.29×138.0 mm ← 300×180 |
| `figure.png` 尺寸 | 2362×1496 px @200 dpi | 1482×1086 px @200 dpi |
| `figure.pdf` 字体 | `STSong-Light`（CID） | 同左 |
| `verify_report.ok` + `spec_sha16` | true / `e04e9d47e8ca0099` | true / `4603787adcb287d7` |
| `figure.svg` sha256（前 16 位） | `f8b01ce26b622187` | `c6d422febfa1a1b9` |
| `result.json.checksum`（前 16 位） | `79991acc069898a4` | `17105908a53dfc15` |
| `uncertainty` / `change_record` 条数 | `[]` / 1 | `[]` / 1 |
| `check.py`（G1–G10） | `ok:true`，10/10，issues=[] | `ok:true`，10/10，issues=[] |
| `main.py` 退出码 | **0** | **0** |

> 画布会自动等比缩放以容纳全部实体（`canvas.requested` 记录原始请求值，`width_mm/height_mm`
> 记录实际值）；这是 D8 的既定行为，不是数据丢失。

## 3. `result.json` 的 18 个顶层字段（与 `references/OUTPUT_CONTRACT.md` 一致）

```
case_id  title  status  workorder(=apparatus_and_technical_route)  figure_type  extraction
entities  relations
output_contract{editable_sources[], exports[], data_mapping[], element_traceability[]}
evidence{source, extraction, items[], source_files[], notes[], meta}
verify{ok, checks, errors[], warnings[], determinism, summary}
canvas  fonts[]  sources[]  uncertainty[]  change_record[]  execution  checksum
```

- `output_contract.editable_sources[]`：`kind=svg`、`path=figure.svg`、`format`、`layers[]`(5 层)、
  `editability` 说明、`checksum_sha256`（SVG 文件 sha256）；
- `output_contract.exports[]`：`png`（`width_px/height_px/dpi/font_ttf`）+ `pdf`（`vector:true/font`）；
- `output_contract.data_mapping[]`：行数与实体数相同、`entity_id` 唯一、与实体集合一致；
- `output_contract.element_traceability[]`：覆盖全部 `entity-<id>` 与 `arrow-<id>`。

## 4. 复跑与自查（期望退出码）

```bash
SKILL_DIR=/skills/weekly-skill
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out /tmp/out     # → exit 0
python "$SKILL_DIR/scripts/check.py" /tmp/out/demo-biotech-route-01/result.json     # → exit 0，ok:true
```

- 复跑后 `layout.json`、`verify_report.json`、`evidence.json`、`figure.svg` 与上表 sha256
  **应逐字节一致**（确定性；本机 `TEST.md` T3 有记录）；
  `result.json` 仅 `change_record` 时间戳与 `execution.out_dir` 不同；
- 只有对**新跑出来的** `result.json` 跑 `check.py` 才是有效自查（包内冻结的
  `examples/output/**/result.json` 因不含 `figure.svg/png/pdf` 会如实报 G3/G4，见
  `examples/README.md` §3）。

## 5. 编辑用例（`--merge route_spec.mutation.example.json`）的期望差异

| 项 | 生成（无 `--merge`） | 编辑（带 `--merge`） |
|-|-|-|
| 实体 / 关系 | 10 / 9 | **11 / 11** |
| 变更 | — | E5 图面标签 → `药物（激酶抑制剂）`（同名替换）；新增 E11 `DMSO 对照`（material）、R10 `E6→E4 recycle 复筛回流`（虚线，命中 `recycle-review` warn）、R11 `E11→E4 flow 对照孔` |
| `change_record` 条数 | 1（初始生成） | **5**（初始生成 + 4 条 `by=agent` 修正记录） |
| `uncertainty` | `[]` | `agent_manual_edits`（记录修正项与 `change_notes`） |
| `result.json.checksum` | `79991acc…` | **`0ee47cf9…`**（随实体/关系集合变化 ⇒ 编辑生效的机器证据） |
| `verify.ok` | true | true（recycle 仅 warn，不阻断 success；如设计） |
| 退出码 | 0 | **0** |

编辑结果可在 `layout.json`（E5/E11 的 `label`、R10/R11）与 `figure.svg` 文本中直接看到，
例如 `激酶抑制剂`、`DMSO 对照`、`复筛回流` 三个字符串都应出现在 SVG 里。

## 6. 第三方依赖缺失时的期望降级

| 缺失项 | 期望表现 |
|-|-|
| Pillow | 无 `figure.png`；`status=partial`；`uncertainty[scope=png]`；SVG/PDF 照常 |
| reportlab | 无 `figure.pdf`；`status=partial`；`uncertainty[scope=pdf]`；SVG/PNG 照常 |
| 中文字体 | `fonts[role=png].found=false` 且 `uncertainty[scope=fonts]`；`status=partial`（D9），不伪造 |
| `assets/connection_rules.json` 不可读 | 规则审计跳过（`connection_rules` 项不报 error），其余检查照常 |
| case.json 不存在/不可解析 | `exit 2`（文件不存在）或 `exit 1` + `failed/result.json`（解析失败），不猜内容 |
