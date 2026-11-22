# vocabulary.md — 术语表 / 词表（challenge-9034312d · v2）

> 与高分包 78615（references/vocabulary.md）形态对齐：把领域知识做成独立词表
> 而非埋在 SKILL 长文或代码里。本文件是**人读词表**；机器执行端使用
> `assets/connection_rules.json`（类别/关系词表 + 规则），代码中的别名映射
> （scripts/model.py 顶部）与本表保持一致。**新增类别/关系时三处同步**：
> model.py 的 KINDS/RELATION_KINDS → connection_rules.json → 本表。

## 1. 图元类别（kind）

| kind | 图例标签 | 形状 | 用途 | 常见别名（输入容错） |
|-|-|-|-|-|
| `step` | 步骤 | rect | 流程步骤（route/flow 图自动编号） | 步骤/step/operation |
| `phase` | 阶段 | rect | 阶段容器/子步骤 | 阶段/stage |
| `device` | 装置/仪器 | rect | 部件、仪器、装配单元 | 装置/仪器/部件/equipment/part/machine |
| `container` | 容器/接口 | rect | 容器、接口（装置图与 device 同色系） | 容器/接口 |
| `material` | 物料/样本 | rounded | 输入物料、样本 | 物料/样本/样品/input/sample |
| `product` | 产物/输出 | rounded | 输出产物 | 产物/输出/outcome |
| `data` | 数据/文件 | diamond | 数据、文件、结果 | 数据/文件/result |
| `decision` | 判断/条件 | diamond | 分支/判断节点 | 判断/条件 |
| `milestone` | 里程碑 | rect | 阶段出口/结论 | 里程碑 |
| `waste` | 废料/终点 | rounded | 废料、终点 | 废料/终点 |

## 2. 关系类别（relation kind）

| kind | 图例 | 线型/箭头 | 用途 | 常见别名（输入容错） |
|-|-|-|-|-|
| `flow` | 流向 | 实线三角箭头（红） | 物料/能量/信息流向 | 流向/arrow/material_flow |
| `connect` | 连接 | 实线无箭头 | 结构连接（部件↔接口） | 连接/link/connection |
| `depend` | 依赖 | 实线三角 | 阶段依赖 | 依赖/depends_on |
| `recycle` | 回流 | 虚线三角 | 回流/循环（避免与正向流混淆） | 回流/reuse/循环 |
| `sequence` | 顺序 | 实线三角 | 步骤先后（仅 step/phase/milestone） | 顺序/next |
| `causation` | 导致 | 实线三角 | 因果（机制图） | 导致/result_in |

## 3. 图类（figure_type）与布局模板

| figure_type | 布局模板 | 判定 |
|-|-|-|
| `route` | 阶段分列 + 步骤编号 + 正交肘型连线 | 默认；无 stage 时单列 |
| `apparatus` | 三桶布局：物料列→装置列→产物列 | 实体含 device/container/material 时自动切换 |
| `flow` | 与 route 相同（强调材料流向） | 显式指定 |
| `hybrid` | route 底座 + 装置实体混排 | 显式指定 |

## 4. SVG 命名词表（可编辑性契约）

| 元素 | 命名规范 |
|-|-|
| 图层 | `layer-background` / `layer-title` / `layer-arrows` / `layer-entities` / `layer-legend` |
| 实体组 | `entity-<id>`，属性 data-entity/data-kind/data-source/data-stage/data-step-no |
| 实体文本 | `<text id="entity-<id>-text-<i>" data-line="<i>">`（真实文本，可编辑） |
| 箭头 | `arrow-<id>`（path）+ `arrowhead-<id>`（polygon）；回流带 stroke-dasharray |
| 元数据 | dc:title / dc:source / bd:case_id / bd:workorder / bd:checksum |

## 5. 状态词表

| 词 | 取值 |
|-|-|
| status | `success` / `partial` / `failed`（error 级规则违规未解决 ⇒ 不得 success） |
| extraction | `structured`（结构化输入）/ `text-heuristic`（文本解构兜底） |
| 规则严重级 | `error`（阻断 success）/ `warn`（提示人工复核） |