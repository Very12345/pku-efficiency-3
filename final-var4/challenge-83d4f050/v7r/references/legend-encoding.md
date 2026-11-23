# legend-encoding.md — 符号语义与图例数据编码规范

> 由早期基础包的单篇绘图规范（`DIAGRAM_SPEC.md` 的符号与调色板章节，**不在本包内**，
> 仅作来历说明）独立成文，并配套可执行审计
> `scripts/legend_audit.py`（L01–L08 + E01–E02）。本题高分包共性：70+ 分包几乎都带
> "legend-encoding / glyph_semantics / check_encoding / mapcheck" 类文件——
> **符号系统的全局一致性是本类题区别于纯图表题的核心**。

## 1. 实体符号（glyph）语义

| type | 形状 | 语义 | 图例必须列出（当图面使用该类型时） |
|---|---|---|---|
| protein | 圆角矩形 | 蛋白质 | ✓ |
| gene | 直角矩形 + 斜体文字 | 基因（与蛋白严格区分） | ✓ |
| complex | 圆角矩形 + 内点线框 | 复合物/家族（非单体） | ✓ |
| rna | 圆角矩形 + 内点线框 | RNA | ✓ |
| small_molecule | 圆 | 小分子/配体/代谢物 | ✓ |
| other | 圆角矩形 | 其他/未归类 | ✓ |

同名基因与蛋白：拆为两个实体（P04）；同一蛋白多区室：拆为多个实体并注明（P04b）。

## 2. 相互作用箭头 = 科学论断（不可混用）

| type | 端点标记 | 颜色 | 语义 | 反例（错误画法） |
|---|---|---|---|---|
| activation | 实心三角 ▲ | #2E7D32 | 激活、促进、正向调控 | 用无箭头线 |
| inhibition | 横杠 ┴ (T-bar) | #C0392B | 抑制、阻断、负调控 | 用指向目标的正向三角 |
| binding | 无箭头实线 | #1F4E79 | 结合、互作、募集（不改状态） | 画成有向激活 |
| modification | 圆点 ●（带 P/Ub 标签） | #B9770E | 磷酸化、泛素化、甲基化、乙酰化、降解 | 用激活箭头 |
| transport | 菱形 ◆ | #6C3483 | 转运、转位、内化、出核/入核 | 无向横线 |

规则（L04/L06 机器强制）：
- marker 必须与图例/画布一致：SVG `marker-end` 的 marker id == 图例声明的 marker id；
- **边宽 = 证据强度**：strong=2.8 / moderate=2.2 / weak=1.6（`evidence_width`，L07）；
- **虚线出现条件**：仅当 `uncertain=true` 或 `evidence=weak`；语义="证据弱/间接/不确定"（L06）；
- 修饰亚型写进 `subtype`（如 磷酸化），需要时作为边中点标签（如 "P"）；
- 反馈环：`feedback=true`（右侧绕行回上游），方向仍按箭头表达（P07 提醒未标注的逆流回流边）。

## 3. 数据编码（data encoding）规则

- 默认映射：`data_mapping.field=表达量`；实体填充色在 `low #FFF7E0 ↔ high #1F4E79`
  之间按全局 min–max 线性插值（`data_color`）；**没有数值的实体用类型默认色**；
- 图例画出色带 + "低/高"标签；色带端点必须在图例中声明（E02）；
- **画布上的数值必须可溯源**（E01）：实体 `data` 有数值时，其 `source` 必须非空
  （材料行号）；仅假设/常识支撑的数值必须进 `uncertainty`（T03）；
- 除数据映射外，画面上不允许出现图例未声明的语义色（L05：装饰色如区室带/标题不受限）。

## 4. 调色板（palettes.json）

- 规范色板集中在 `assets/palettes.json`（node_types/edge_types/evidence_width/
  compartments/data_mapping），`scripts/model.py` 导入并合并到内置默认值——**改颜色/线宽
  只改一处，全图与图例同步**；
- 色板同时服务于 SVG 与 matplotlib 两个渲染后端（同源，零漂移）。

## 5. 图例≠画布的一致性审计（scripts/legend_audit.py）

| id | 检查 | 失败后果 |
|---|---|---|
| L01 | 图例覆盖在用实体类型 | fail |
| L02 | 图例覆盖在用边类型 | fail |
| L03 | 数据映射字段有数值支撑（无值则 warn） | warn |
| L04 | 画布 marker == 图例 marker（逐边对拍） | fail |
| L05 | 节点/边颜色 ⊆ 图例 ∪ 数据映射色带 | fail |
| L06 | 虚线仅用于 weak/uncertain | warn |
| L07 | 证据强度→线宽映射与规范一致 | warn |
| L08 | 7 个 `layer-*` 图层齐全 | fail |
| E01 | 带数据值的实体 source 非空 | fail |
| E02 | 色带端点 low/high 已声明 | fail |

> 审计结果写入 `out/legend_audit.json`，并嵌入 `result.json.legend_audit` 与 G6 门。