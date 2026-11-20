# DIAGRAM_SPEC.md —— 生物机制图与通路图绘图规范

本文件是 `scripts/model.py` 与 `scripts/svg_backend.py` 的行为基准，也是人工编辑
model.json 与 SVG 时的速查表。规范第一原则：**图上的每个图元都是可被质疑的机制论断，
符号系统必须全局一致、可溯源。**

## 1. 实体图形与命名

| 类型 (type) | 形状 | 描边色 | 底填充（默认） | 文字 |
|---|---|---|---|---|
| protein 蛋白质 | 圆角矩形 | #1F4E79 | #EAF2FB | 正体 |
| gene 基因 | 直角矩形 | #B9770E | #FFF3E0 | **斜体** |
| complex 复合物 | 圆角矩形 + 内点线框 | #6C3483 | #EDE7F6 | 正体 |
| rna RNA | 圆角矩形 + 内点线框 | #117A65 | #E8F8F5 | 正体 |
| small_molecule 小分子/配体 | 圆 | #CA6F1E | #FDEBD0 | 正体 |
| other 其他 | 圆角矩形 | #7F8C8D | #F4F6F6 | 正体 |

命名规则：
1. **基因 vs 蛋白严格分开**：基因斜体、蛋白正体；同名必须拆成两个实体并在 note 说明
   （如 `MYC（基因）` 与 `MYC` 蛋白）。
2. 复合物与家族成员不混为单体；物种前缀按材料/权威命名保留（如人源 EGFR）。
3. 同义名/旧名：选材料或权威数据库的规范名作为 name，同义名放 note，不做无依据归一。
4. 实体 id 在模型内唯一（e1…）；SVG 中对应 `entity-<id>` 分组。

## 2. 相互作用箭头语义（不可混用）

| type | 端点标记 | 颜色 | 说明 |
|---|---|---|---|
| activation | 实心三角 ▲ | #2E7D32 | 激活、促进、正向调控、GEF 催化 |
| inhibition | 横杠 ┴ (T-bar) | #C0392B | 抑制、阻断、负调控 |
| binding | 无箭头 | #1F4E79 | 结合、互作、募集（不改状态） |
| modification | 圆点 ●（可带 P/Ub 标签） | #B9770E | 磷酸化、泛素化、甲基化、乙酰化、降解 |
| transport | 菱形 ◆ | #6C3483 | 转运、转位、内化、出核/入核 |

- 边宽 = 证据强度：strong=2.8 / moderate=2.2 / weak=1.6（`evidence_width`）。
- **虚线出现条件**：仅当 `uncertain=true` 或 `evidence=weak`；语义为“证据弱/间接/不确定”。
- 反馈环：`feedback=true`（在右侧绕行回上游），方向仍按箭头表达。
- 修饰亚型写进 `subtype`（如 磷酸化），需要时作为边中点标签（如 “P”）。

## 3. 区室与布局

| 区室 (compartment) | rank | 表达 | 绘制 |
|---|---|---|---|
| extracellular 胞外 | 0 | 分泌配体、外部刺激 | 顶部横带 |
| membrane 细胞膜 | 1 | 受体（跨膜）、膜相关蛋白、脂质信号 | 中间细横带，受体跨满带高 |
| cytoplasm 细胞质 | 2 | 胞内激酶、小 GTP 酶等 | 横带；核存在时内部再嵌核框 |
| nucleus 细胞核 | 3 | 转录因子、基因 | 细胞质带内嵌框（淡紫 #F4ECF7） |

- 信号流方向：**上 → 下**（rank 递增）；跨膜受体必须位于膜带内；反向/反馈边一律右侧绕行。
- 同区室实体水平排列；某区室无内容则不画空带。
- 布局由 `layout.py` 确定性算法完成（无随机），重复运行结构一致；人工可在 SVG 内直接拖曳
  覆盖算法结果（再导出即可，校验只认语义属性）。

## 4. 图例与数据编码

- 图例必须出现：全部用到的实体类型、全部用到的边类型、证据宽度样例、虚线语义、
  数据映射色带、方向说明。图例色/线宽与图面**逐值相等**（validate L01/L02/L05 强制）。
- 数据编码默认：`data_mapping.field=表达量`，实体填充色在 低 #FFF7E0 ↔ 高 #1F4E79 之间
  按全局 min–max 线性插值；数值缺失用类型默认色。
- 除上述映射外，不允许画面上出现图例未声明的**语义色**（装饰色如区室带、标题不限）。

## 5. 导出与质量参数

- 画布：1200 × 900（可经 case.json `render` 覆盖，必须同时更新 viewBox/canvas 字段）。
- 可编辑 SVG：图层 id 固定为 `layer-compartment / layer-edge / layer-entity /
  layer-label / layer-title / layer-legend / layer-meta`；每个实体/边元素带
  `data-id / data-type / data-source`。
- 预览：PNG @150dpi（1200×900 px）、PDF（矢量）。字体栈
  `Arial, PingFang SC, Microsoft YaHei, Noto Sans CJK SC, sans-serif`；
  PNG 渲染优先 SimHei/Microsoft YaHei（缺中文字体时告警并记录，SVG 不受影响）。
- 每个产物记录 sha256 与字节数（result.json `export_checks`）。

## 6. 校验规则一览（scripts/validate.py）

| id | 规则 | 失败后果 |
|---|---|---|
| M01 | 实体 id 唯一 | fail |
| M02 | 边端点必须存在 | fail |
| M03 | 实体必须有名称 | fail |
| T01/T02 | 每个实体/边必须有 source | fail |
| T03 | 假设型来源必须在 uncertainty 说明 | warn |
| L01/L02 | 图例覆盖在用实体/边类型 | fail |
| L03 | 数据映射有数值支撑（无则 warn） | warn |
| L04 | 箭头 marker = 图例声明 | fail |
| L05 | 节点与边颜色 ⊆ 图例∪数据映射 | fail |
| D01 | 非反馈边符合上→下流向 | warn |
| S00/F0x/F02/F03 | SVG well-formed、产物存在、PNG 可开、契约字段齐全 | fail |

## 7. 修改工作流（“改一标签再导出”的保证）

1. 编辑 `/app/work/model.json`（或直接编辑 SVG 图层文本）。
2. 重跑 `python3 scripts/main.py --model-file model.json --case case.json --out <out>`
   或直接改 SVG 后自行转 PNG（本包建议走脚本以保持两版一致）。
3. `validate.py` 复检；记录 `change_records` 与 sha256 变化。