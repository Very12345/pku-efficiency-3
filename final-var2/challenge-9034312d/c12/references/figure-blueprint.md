# figure-blueprint.md — 布局蓝图：图元规范 + 布局模板 + 命名契约 + 导出规范（v2)

> 本文件是「布局经验 + 图元规范」的可分享落点（生态贡献 + 创新方法），替代并升级
> build 版的 LAYOUT_SPEC.md。任何人可据此独立再现本 Skill 的图稿风格与可编辑结构；
> 机器侧一致性由 `scripts/svg_verify.py` 校验（CP3）。

## 1. 图元规范

- 图元类别（kind）→ 形状/配色/图例标签 的映射见 `references/vocabulary.md` §1，
  配色值见 `templates/palette.json`（色板兼顾打印灰度与色觉友好）。
- 关系类别（relation kind）→ 线型/箭头 映射见 `references/vocabulary.md` §2。

## 2. 布局模板（按 figure_type）

### Route / Flow（默认）
- **阶段分列**：每个 `stage` 一列，列从左到右 = 时间/逻辑顺序；
- **步骤编号**：对 step/phase/milestone 按「列序-行序」编 1..N，与正文顺序一一对应（G8）；
- **连线**：同列上下直连；跨列正交肘型线（先水平后垂直）；`recycle` 走盒下方回绕虚线；
  反向流走盒上方回绕；
- **图例**：自动按实际使用的 kind 生成（legend_kinds 与图面一致，CP3 校验）。

### Apparatus（装置图）
- **三桶布局**：物料列(左，material/container) → 装置列(中，device/step/phase) →
  产物列(右，product/data/waste)；
- 连接线区分 connect（结构连接，无箭头）与 flow（流向，三角箭头）；
- 规则：物料不可作为流向终点（除 recycle）；connect 至少一端为 device/container
  （assets/connection_rules.json）。

### Hybrid / 兜底
- 有结构走 route 列布局；实体类别偏装置时自动切 apparatus。

## 3. 几何与文本规范

- 单位：全部 mm；PNG 按 DPI 换算像素，PDF 按 pt；
- 盒子宽度 = max(26mm, 标签估算宽度 + 8mm)；CJK 全角按 1.0 字宽、ASCII 按 0.55 字宽估算；
- 长标签 ≥110mm 自动拆行（逐字贪婪拆行）；
- 列间距 34mm、行间距 12mm、外边距 14mm；默认字号 11pt、标题 16pt；
- 字体链声明：`'Noto Sans CJK SC','Microsoft YaHei','PingFang SC','SimHei','DejaVu Sans',sans-serif`；
- 画布溢出：等比缩小并居中放入请求画布，**不裁剪内容**（requested canvas 记录在 layout.json）。

## 4. 命名与可编辑性契约（SVG）

- 图层 id：`layer-background / layer-title / layer-arrows / layer-entities / layer-legend`
  （svg_verify 逐层核对）；
- 实体组：`entity-<id>`，属性 `data-entity / data-kind / data-source / data-stage / data-step-no`；
- 文字：`<text id="entity-<id>-text-<i>" data-line="<i>">` 真实文本（可编辑）；
- 箭头：`arrow-<id>` 路径 + `arrowhead-<id>` 多边形；回流带 `stroke-dasharray`；
- metadata：dc:title / dc:source / bd:case_id / bd:workorder / bd:checksum。

## 5. 导出参数（导出规范）

| 项 | 默认 | 说明 |
|-|-|-|
| PNG DPI | 200（--dpi 可调） | 汇报/截图常见分辨率；灰度打印友好 |
| PDF | reportlab 矢量 CID(STSong-Light) | 投稿/打印矢量；无需外部字体文件 |
| SVG | 手写 XML（分层可编辑） | 源文件；Inkscape/浏览器可直接修改 |
| 画布 | 默认 297×180mm；case.json canvas 可覆盖 | 溢出自动等比缩放不裁剪 |

## 6. 扩展指引

- 新图元：`scripts/model.py` 的 KINDS/RELATION_KINDS + `templates/palette.json` +
  `assets/connection_rules.json` + `references/vocabulary.md` 四处同步增项即可，
  形状/配色/图例/规则自动生效；
- 新布局：在 `scripts/layout.py` 的 `compute_layout` 增列桶规则（如 apparatus 三桶）；
- 新规则：在 `assets/connection_rules.json` 的 rules[] 增 {id, severity, check, when_*}
  条目，`svg_verify.py` 的规则引擎自动执行（check 取值见脚本内说明）；
- 新导出后端：复用 `layout.json` 几何（如新增 PPTX 导出只需读 layout 逐盒写图形）。

## 7. 确定性说明

- `layout.py` 是纯函数式确定性布局：同一输入（case+evidence+palette）必得同一布局；
- `verify_report.json.determinism.spec_sha16` 是布局内容的规范化哈希探针：
  同输入两次运行该值逐位一致（TEST.md T4 有实测）。