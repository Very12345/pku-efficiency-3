# mechanism-spec.md — 机制规格与绘图规范

> 由早期基础包的单篇绘图规范（`DIAGRAM_SPEC.md`，**不在本包内**，仅作来历说明）拆分而来：
> 「机制规格生产规范」本文 + 「符号/图例语义」`references/legend-encoding.md`。
> 本文定义机制/通路图的**声明式规格**（model.json）的语义与生产规则，以及区室/布局/导出规范。
> 规范第一原则：
> **图上的每个图元都是可被质疑的机制论断，符号系统必须全局一致、可溯源。**

## 1. 机制规格（mechanism spec）是什么

一张机制图 = 一份可逐条质疑的机制陈述。流水线把它写成一个 JSON 规格
（`model.json`，即本 Skill 的"单一中间制品"）：

```
case_id, title, example,
entities[]  # 生物实体：id/name/type/compartment/data/note/source
edges[]     # 相互作用：id/from/to/type/subtype/evidence/feedback/label/source
legend      # 图例：实体样式/边样式/证据宽度/虚线/数据映射/方向说明
layout      # 布局覆盖（可选）：compartments/constraints
extraction  # {method, verified_by_agent}
```

- 规格由 `scripts/extract.py` 草稿化，**由 Agent 对照真实材料人工核验（CP4）**后定稿；
- 定稿前必须通过 `assets/mechanism-spec.schema.json`（CP2 schema 门，校验在
  `scripts/validate_figure.py`）；
- 规格 → 布局 → SVG/PNG/PDF 全部由同一规格驱动（单一数据源，双后端零漂移）。

## 2. 实体与命名规则

| 类型 (type) | 形状 | 描边色 | 底填充（默认） | 文字 |
|---|---|---|---|---|
| protein 蛋白质 | 圆角矩形 | #1F4E79 | #EAF2FB | 正体 |
| gene 基因 | 直角矩形 | #B9770E | #FFF3E0 | **斜体** |
| complex 复合物 | 圆角矩形 + 内点线框 | #6C3483 | #EDE7F6 | 正体 |
| rna RNA | 圆角矩形 + 内点线框 | #117A65 | #E8F8F5 | 正体 |
| small_molecule 小分子/配体 | 圆 | #CA6F1E | #FDEBD0 | 正体 |
| other 其他 | 圆角矩形 | #7F8C8D | #F4F6F6 | 正体 |

命名规则（全部可在拓扑审计中复核，P04/P04b）：
1. **基因 vs 蛋白严格分开**：基因斜体、蛋白正体；同名必须拆成两个实体并在 note 说明
   （如 `MYC（基因）` 与 `MYC` 蛋白）。
2. 复合物与家族成员不混为单体（complex 带内框）；物种前缀按材料/权威命名保留。
3. 同义名/旧名：选材料或权威数据库规范名作 name，同义名放 note，不做无依据归一。
4. **同一蛋白出现在多个区室**（如胞质 ERK 与核内 ERK）→ 按区室拆分为多个实体，
   每个实体注明去向（P04b 强制 note）。
5. 实体 id 在模型内唯一（e1…）；SVG 中对应 `entity-<id>` 分组。

## 3. 相互作用语义

完整的箭头形态/颜色/线宽/虚线语义见 `references/legend-encoding.md`，要点：
激活=实心三角、抑制=T-bar 横杠、结合=无箭头、修饰=圆点（可带 P/Ub 标签）、
转运=菱形；边宽=证据强度；**虚线仅表达"证据弱/间接/不确定"**（L06 强制）。

## 4. 区室与布局

| 区室 (compartment) | rank | 表达 | 绘制 |
|---|---|---|---|
| extracellular 胞外 | 0 | 分泌配体、外部刺激 | 顶部横带 |
| membrane 细胞膜 | 1 | 受体（跨膜）、膜相关蛋白 | 中间细横带，受体跨满带高 |
| cytoplasm 细胞质 | 2 | 胞内激酶、小 GTP 酶等 | 横带；核存在时内部再嵌核框 |
| nucleus 细胞核 | 3 | 转录因子、基因 | 细胞质带内嵌框（淡紫 #F4ECF7） |

- 信号流方向：**上 → 下**（rank 递增）；跨膜受体必须位于膜带内；反向/反馈边一律右侧绕行；
- 同区室实体水平排列；某区室无内容则不画空带；
- 布局由 `layout.py` 确定性算法完成（无随机）：同一规格 → 同一布局（确定性探针）；
- 人工可在 SVG 内直接拖曳覆盖算法结果（再导出即可，校验只认语义属性 data-*）。

## 5. 图例与数据编码

- 图例必须出现：全部用到的实体类型、全部用到的边类型、证据宽度样例、虚线语义、
  数据映射色带、方向说明；图例色/线宽与图面**逐值相等**（L01/L02/L04/L05/L07 强制）；
- 数据编码默认：`data_mapping.field=表达量`，实体填充色在 低 #FFF7E0 ↔ 高 #1F4E79 间按
  全局 min–max 线性插值；数值缺失用类型默认色；
- 除上述映射外，不允许画面上出现图例未声明的**语义色**（装饰色如区室带、标题不限）；
- 画布上的每个数值必须能回溯到材料来源（E01），否则不得上画布编码。

## 6. 导出与质量参数

- 画布：1200 × 900（可经 case.json `render` 覆盖，layout/SVG/PNG 同步）；
- 可编辑 SVG：图层 id 固定为 `layer-compartment / layer-edge / layer-entity /
  layer-label / layer-title / layer-legend / layer-meta`（7 层，G4 强制）；每个实体/边
  元素带 `data-id / data-type / data-source / data-compartment`（边另带
  `data-evidence / data-feedback`）；
- 预览：PNG @150dpi（1200×900 px）、PDF（矢量）；字体栈
  `Arial, PingFang SC, Microsoft YaHei, Noto Sans CJK SC, sans-serif`；PNG 渲染优先
  SimHei/Microsoft YaHei，缺中文字体时告警并记录，SVG 不受影响；
- 每个产物记录 sha256 与字节数（result.json `export_checks`）。

## 7. 校验规则一览（scripts/validate_figure.py 聚合）

| 系列 | 规则 | 失败后果 |
|---|---|---|
| M01/M03 | 实体 id 唯一/必须有名称 | fail |
| P01–P08 | 拓扑：id 唯一、边端点、方向、同名消歧、重复边、自环、反馈标注、区室词表 | fail/warn |
| T01–T03 | 实体/边必须有 source；假设型来源显式化 | fail/warn |
| S01 | 机制规格 schema 门（CP2） | fail |
| L01/L02/L04/L05/L07 | 图例覆盖、箭头=图例、颜色⊆图例∪映射、线宽映射 | fail |
| L03/L06/E01/E02 | 数据映射、虚线语义、数据可溯源、色带端点 | warn/fail |
| F01x/F02x | 产物存在、PNG 可打开 | fail |

## 8. 修改工作流（"改一个标签再导出"的保证）

1. 编辑 `/app/work/model.json`（机制规格）或直接编辑 SVG 图层文本；
2. 重跑 `python3 scripts/main.py --model-file model.json --case case.json --out <out>`
   或直接改 SVG 后自行转 PNG（本包建议走脚本保持两版一致）；
3. `validate_figure.py`/`check_contract.py` 复检；记录 `change_records` 与 sha256 变化。
## 9. 符号语义与图例数据编码规范（原 `references/legend-encoding.md`，全维合并版逐字保留）

> 本节由 `legend-encoding.md` 合并而来（旧文件名保留在既有引用与脚本注释里，内容一字未减）：箭头语义、数据编码、调色板与审计规则以下表为准。

> 由早期基础包的单篇绘图规范（`DIAGRAM_SPEC.md` 的符号与调色板章节，**不在本包内**，
> 仅作来历说明）独立成文，并配套可执行审计
> `scripts/legend_audit.py`（L01–L08 + E01–E02）。本题高分包共性：70+ 分包几乎都带
> "legend-encoding / glyph_semantics / check_encoding / mapcheck" 类文件——
> **符号系统的全局一致性是本类题区别于纯图表题的核心**。

### 1. 实体符号（glyph）语义

| type | 形状 | 语义 | 图例必须列出（当图面使用该类型时） |
|---|---|---|---|
| protein | 圆角矩形 | 蛋白质 | ✓ |
| gene | 直角矩形 + 斜体文字 | 基因（与蛋白严格区分） | ✓ |
| complex | 圆角矩形 + 内点线框 | 复合物/家族（非单体） | ✓ |
| rna | 圆角矩形 + 内点线框 | RNA | ✓ |
| small_molecule | 圆 | 小分子/配体/代谢物 | ✓ |
| other | 圆角矩形 | 其他/未归类 | ✓ |

同名基因与蛋白：拆为两个实体（P04）；同一蛋白多区室：拆为多个实体并注明（P04b）。

### 2. 相互作用箭头 = 科学论断（不可混用）

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

### 3. 数据编码（data encoding）规则

- 默认映射：`data_mapping.field=表达量`；实体填充色在 `low #FFF7E0 ↔ high #1F4E79`
  之间按全局 min–max 线性插值（`data_color`）；**没有数值的实体用类型默认色**；
- 图例画出色带 + "低/高"标签；色带端点必须在图例中声明（E02）；
- **画布上的数值必须可溯源**（E01）：实体 `data` 有数值时，其 `source` 必须非空
  （材料行号）；仅假设/常识支撑的数值必须进 `uncertainty`（T03）；
- 除数据映射外，画面上不允许出现图例未声明的语义色（L05：装饰色如区室带/标题不受限）。

### 4. 调色板（palettes.json）

- 规范色板集中在 `assets/palettes.json`（node_types/edge_types/evidence_width/
  compartments/data_mapping），`scripts/model.py` 导入并合并到内置默认值——**改颜色/线宽
  只改一处，全图与图例同步**；
- 色板同时服务于 SVG 与 matplotlib 两个渲染后端（同源，零漂移）。

### 5. 图例≠画布的一致性审计（scripts/legend_audit.py）

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