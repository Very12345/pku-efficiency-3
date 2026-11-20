# LAYOUT_SPEC.md — 布局与图元规范（图元库 + 布局模板）

本文件说明 Skill 的图元规范、布局模板与失败清单，是「生态贡献」与「创新方法」
的落点文档。任何他人可据此复用量产同一风格图稿。

## 1. 图元（KIND）词表

图元类别决定形状、配色与图例标签，请勿在图内混用：

| kind | 图例标签 | 形状 | 用途 |
|-|-|-|-|
| `step` | 步骤 | rect | 流程步骤（route/flow 图自动编号） |
| `phase` | 阶段 | rect | 阶段容器/子步骤 |
| `device` | 装置/仪器 | rect | 部件、仪器、装配单元 |
| `container` | 容器/接口 | rect | 容器、接口（装置图与 device 同色系） |
| `material` | 物料/样本 | rounded | 输入物料、样本 |
| `product` | 产物/输出 | rounded | 输出产物 |
| `data` | 数据/文件 | diamond | 数据、文件、结果 |
| `decision` | 判断/条件 | diamond | 分支/判断节点 |
| `milestone` | 里程碑 | rect | 阶段出口/结论 |
| `waste` | 废料/终点 | rounded | 废料、终点 |

关系（arrow）类型：

| kind | 图例 | 线型 | 用途 |
|-|-|-|-|
| `flow` | 流向 | 实线三角箭头（红） | 物料/能量/信息流向 |
| `connect` | 连接 | 实线无箭头 | 结构连接 |
| `depend` | 依赖 | 实线三角 | 阶段依赖 |
| `recycle` | 回流 | 虚线三角 | 回流/循环（避免与正向流混淆） |
| `sequence` | 顺序 | 实线三角 | 步骤先后 |

## 2. 布局模板

### Route / Flow（默认）
- **阶段分列**：每个 `stage` 一列，列从左到右 = 时间/逻辑顺序；
- **步骤编号**：route/flow 图对 step/phase/milestone 按「列序-行序」编 1..N，
  与正文顺序一一对应；
- **连线**：同列上下直连；跨列用正交肘型线（先水平后垂直）；
  `recycle` 走盒下方回绕虚线；反向流走盒上方回绕；
- **图例**：自动按使用的 kind 生成，置于画布底部。

### Apparatus（装置图）
- **三桶布局**：物料列(左，material/container) → 装置列(中，device/step/phase) →
  产物列(右，product/data/waste)；
- 连接线强调部件与接口的对应（connect/flow 区分）。

### Hybrid / 兜底
- 有结构用 route 列布局；实体类别偏装置时自动切 apparatus。

## 3. 几何与文本规范

- 单位：全部 mm；PNG 按 DPI 换算像素，PDF 按 pt。
- 盒子宽度 = max(26mm, 标签估算宽度 + 8mm)；标签 CJK 全角按 1.0 字宽、ASCII 按 0.55 字宽估算；
- 长标签 ≥ 等于 110mm 时自动拆行（逐字贪婪拆行）；
- 列间距 34mm（容纳箭头与标签），行间距 12mm，外边距 14mm；
- 默认字号 11pt，标题 16pt（SVG 声明 font-family 链：Noto Sans CJK SC → Microsoft YaHei →
  PingFang SC → SimHei → sans-serif）。
- 画布溢出：等比缩小并居中放入请求画布，**不裁剪内容**（requested canvas 记录在 layout.json）。

## 4. 命名与可编辑性规范（SVG）

- 图层 id：`layer-background / layer-title / layer-arrows / layer-entities / layer-legend`；
- 实体组：`entity-<id>`，属性 `data-entity / data-kind / data-source / data-stage`；
- 文字：`<text id="entity-<id>-text-<i>" data-line="<i>">` 真实文本（可编辑）；
- 箭头：`arrow-<id>` 路径 + `arrowhead-<id>` 多边形；回流带 `stroke-dasharray`；
- metadata：dc:title / dc:source / bd:case_id / bd:checksum。

## 5. 失败清单（已识别问题与处置）

| 失败情形 | 现象 | 处置 |
|-|-|-|
| 断头箭头 | 关系指向不存在实体 | model.py 自动过滤并在 uncertainty 记录，Agent 复核补连 |
| 编号错位 | 步骤编号与正文不符 | 步骤编号由列序自动生成；Agent 对照正文用 `--merge` 修正 |
| 中文缺字 | PNG 中文字体缺失 | fonts.py 降级名单；result.json.fonts.found=false 如实记录 |
| 画布溢出 | 盒子超出画布 | 自动等比缩小；或 --width-mm/--height-mm 重跑 |
| 长标签重叠 | 文本超盒 | 自动拆行；Agent 可精简 label |
| 自由文本无结构化 | extraction=text-heuristic | 只做朴素解构（步骤串联），设备不自动连线；status=partial，Agent 复核 |

## 6. 扩展指引

- 新图元：在 `model.KINDS`/`RELATION_KINDS` 与 `templates/palette.json` 增项即可，
  形状/配色/图例自动生效；
- 新布局：在 `scripts/layout.py` 的 `compute_layout` 增列桶规则（如 apparatus 三桶）；
- 新导出后端：复用 `layout.json` 几何（如新增 PPTX 导出只需读 layout 逐盒写图形）。