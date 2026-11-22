# EXPECTED-OUTPUT.md — 示例案例应产出的文件清单与契约字段（文字形式）

> 本文件**取代**原先随包的 `examples/output/diagram.svg|png|pdf` 等二进制示例：
> 技能资源只允许 UTF-8 文本文件，图件一律由 `scripts/` 在运行时生成。
> 这里用文字写清"跑一次应该得到什么"，使接口、产物与契约在没有预置图件的情况下仍可核对。
>
> 案例：`examples/case.json`（`case_id = example-egfr-mapk`，`example: true`，
> 教学简化版 EGF/EGFR→RAS→RAF→MEK→ERK→MYC 通路）。
> 材料：`examples/materials/example_material.md`（9 实体 / 9 关系 / 数据映射 / 图面约束）。
> 规格：`examples/model.example.json`（已人工核验，`verified_by_agent=true`）。

## 1. 复跑命令与期望退出码

```bash
export SKILL_DIR=/path/to/challenge-83d4f050
python3 "$SKILL_DIR/scripts/main.py" \
    --case "$SKILL_DIR/examples/case.json" \
    --model-file "$SKILL_DIR/examples/model.example.json" \
    --out /tmp/example-out
echo "exit=$?"        # 期望 0（status=success）
```

| 路径 | 期望 | 退出码 |
|-|-|-|
| `--model-file`（已核验规格）+ matplotlib 可用 | `status=success`，`gates 8/8` | **0** |
| `--model-file` + 无 matplotlib | `status=partial`（仅缺 PNG/PDF 预览，SVG 仍产出） | **2** |
| 无 `--model-file`（自动草稿、未核验） | `status=partial`，`uncertainty` 提示逐条复核 | **2** |
| 材料缺失 / 规格不过 schema 门 / SVG 无法产出 | `status=failed`，`reason` 写明 | **3** |

## 2. 应产出的文件清单（7 件，全部写进 `--out` 目录）

| 文件 | 类型 | 内容要点 | 合同字段落点 |
|-|-|-|-|
| `diagram.svg` | **可编辑源**（运行时生成） | 7 个图层组 `layer-compartment / layer-edge / layer-entity / layer-label / layer-title / layer-legend / layer-meta`；实体/边/标注带 `data-id`、`data-type`、`data-source`；字体用 CSS 字体栈（无需随包字体）；无时间戳（确定性） | `deliverables.editable_sources[0]`（`path/format/layers/well_formed`） |
| `diagram.png` | 预览（运行时生成） | 1200×900 px @150 dpi，与 SVG 同一布局 | `deliverables.previews[0]`（`path/format/dpi/width_px/height_px`） |
| `diagram.pdf` | 矢量导出（运行时生成） | matplotlib 导出，供投稿/打印预览；可编辑源仍是 SVG | `deliverables.exports[0]`（`path/format/note`） |
| `model.json` | 机制规格 | 规范化后的实体/边/图例/布局规格（独立复核实体清单与边清单） | `scientific_content` 与其同源；`files[]` |
| `topology.json` | 审计产物 | P 系列：id 唯一、端点存在、方向、同名消歧、重复边、自环、反馈标注、区室词表 | `topology`、`deliverables.audits[]` |
| `legend_audit.json` | 审计产物 | L/E 系列：图例覆盖在用类型、箭头=图例、颜色⊆图例∪映射、虚线语义、线宽映射、图层命名、数值溯源 | `legend_audit`、`deliverables.audits[]` |
| `result.json` | **唯一评分产物** | 契约字段全集（见 §3） | 本体 |

## 3. `result.json` 顶层字段（应与 `references/OUTPUT_CONTRACT.md` §2 完全一致）

```
case_id, title, status, contract_version, skill,
deliverables{editable_sources[], previews[], exports[], audits[]},
scientific_content{entities[], edges[], legend{}, layout{compartments[]}, counts{}},
evidence_sources[], data_mapping{}, extraction{}, export_checks[],
topology{}, legend_audit{}, self_check{passed, checks[], failures[], warnings[], determinism{}},
gates{g1..g8}, uncertainty[], change_records[], files[], provenance{},
+ case.json output_contract 声明的全部自定义字段（本示例：custom_demo_field、custom_list_field）
```

**无 null**：未命中的契约字段按声明形态回填 `""` / `[]` / `false` / `0`（四形态，见契约 §3）。

## 4. 示例案例上应看到的科学内容（用于核对"画对了没有"）

| 项目 | 期望值 |
|-|-|
| 实体数 | 9（含按区室拆分的 `ERK`（细胞质）与 `核内 ERK`（细胞核），同一种蛋白两个实体） |
| 实体类型在用 | `protein`、`gene`、`complex`、`small_molecule`（`rna`/`other` 在图例中保留但未在用） |
| 区室 | 4 带：`extracellular`（胞外）→ `membrane`（细胞膜）→ `cytoplasm`（细胞质，核内嵌）→ `nucleus`（细胞核） |
| 边数 | 9，且 5 类箭头全部在用：`activation`（实心三角）、`inhibition`（T 形端点）、`binding`（无箭头实线）、`modification`（圆点端点）、`transport`（菱形端点） |
| 证据强度 | `strong` / `moderate` / `weak` 三档线宽（2.8 / 2.2 / 1.6）；弱证据边用虚线 |
| 反馈环 | 1 条（`核内 ERK → RAF` 抑制，`feedback=true`，右侧绕行） |
| 数据编码 | 实体填充色按 `表达量` 从 `#FFF7E0`（低）插值到 `#1F4E79`（高），图例含色带与"低/高"标签 |
| 来源追溯 | 每条实体/边都有 `source[{ref, kind, line}]`，`ref` 为相对材料路径，`line` 为材料行号 |

## 5. 已实跑产物的 sha256（本包 `examples/output/` 内，可用于对照）

| 文件 | sha256（全量） | 说明 |
|-|-|-|
| `examples/output/model.json` | `f93a20a283492f7312b0e3ff597be92783b69cd1403d4eed3b37845bc9099935` | 确定性：同输入双跑逐字节一致 |
| `examples/output/topology.json` | `eb826fc5557fccfcb32e173bbe09212bfe9bc662c00e2e03b890b34c345eacad` | 确定性 |
| `examples/output/legend_audit.json` | `efdb1805c839d64858ad84aaae4e0f5aab4209085226eef274fc7862e22c899a` | 确定性 |
| `examples/output/result.json` | 含 `provenance.ts` / `change_records[].ts`，每次运行不同（去掉时间戳后与本次一致） | 非确定性字段已声明 |
| `diagram.svg` | 本次运行前缀 `27f344a0dfb2e90f`（17771 bytes） | 确定性（无时间戳） |
| `diagram.png` | 本次运行前缀 `9137715961238f3f`（203655 bytes） | 同环境重现一致；跨 matplotlib 版本可能变化 |
| `diagram.pdf` | 每次不同（matplotlib 内嵌 CreationDate 时间戳） | 非确定性，已在 TEST.md 声明 |

> 图件（SVG/PNG/PDF）不在包内，因此上面的 sha256 是在本机 plt 环境下跑出的参考值；
> 你的环境若 matplotlib 版本不同，PNG/PDF 字节可能不同，**结构和检查结果应保持一致**。

## 6. 与正式案例的区别（防混淆）

- 本示例的实体/边/数值是**教学简化的合成内容**，不是任何真实论文数据；
- 正式案例由平台提供，材料在 `/input/**`，必须**实际读取文件内容**后再建规格；
- 正式运行**不得**复用本示例的实体名、边的类型判定或数值；示例仅用于演示接口与契约形态。
