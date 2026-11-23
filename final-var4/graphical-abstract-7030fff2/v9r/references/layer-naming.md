# layer-naming.md — SVG 分层命名与溯源属性规范（v2）

> 题面"可编辑源文件与导出规范"评分点：输出分层、命名清楚、文字可编辑的源文件。
> 本文件是图面结构的**机器可校验规范**：`scripts/audit.py` 的 `layer_naming` 检查
> 逐条核对，图层名必须命中本表，`data-*` 溯源属性必须落在实体/关系/数据元素上。

## 1. 图层契约（SVG `<g id="layer:*">`，7 层固定）

| 层 | 内容 | 编辑语义 | 复用约定 |
|-|-|-|-|
| `background` | 画布底（含底色/边框） | 换底色只改这层 | 期刊模板背景在此层注入 |
| `panels` | 面板框、面板标题、面板要点文本 | 改文案/换色 | 阅读顺序的载体 |
| `entities` | 实体卡片、图标、实体标签 | 每个实体一个卡片组 | `data-entity-id` 检索 |
| `relations` | 面板内外箭头与关系标签 | 方向/正负修改 | `data-role="relation:<id>"`；负向自动红色 |
| `data` | 条形、色块、数值标签 | 数值只改 `<text>` 与高度 | `data-role="datum_bar:<id>"` |
| `legend` | 图例色块与标签 | 自动生成，**严禁手写** | 值↔颜色/长度一一对应 |
| `annotations` | 流程箭头、阅读顺序、比例尺 | 版式辅助 | 删除不影响科学内容 |

**命名不变式**：`audit.layer_naming.bad` 必须为空；`missing` 只能容忍
`annotations`（无流程箭头时可缺）；任何不在契约里的新图层必须先加进文档与
`EXPECTED_LAYERS`，再进入画布。

## 2. 溯源属性（data-*，每个科学元素必须有）

| 属性 | 含义 | 必需元素 |
|-|-|-|
| `data-src` | 来源定位 `文件:行` 或 `case.json[字段]` | 实体/关系/数据元素 |
| `data-entity-id` | 实体标识（`slug` 后的 id） | 实体卡片/图标/标签 |
| `data-role` | 角色：`entity:<id>` / `relation:<id>` / `datum:<id>` / `datum_bar:<id>` … | 全部 | 
| `data-panel` | 所在面板（question/method/results/conclusion） | 面板内元素 |
| `data-legend-key` | 图例键（与图例条目一一对应） | 被编码的数据元素 |

**audit 检查**：`elements_without_src`（entity:/relation:/datum:/icon 角色缺
src 的数量）必须为 0 —— 这是"每个元素可溯源"的机器判据。

## 3. 文字可编辑性

- 所有标题/要点/数值均为真 `<text>` 节点（可选中、可改字），不用 path 轮廓
  代替字形；
- 文字溢出自动缩字号（下限 8px），缩号与截断计入 `audit.layout_log`；
- 迁到 Inkscape/Illustrator 后 `data-*` 属性保留在 XML 中（不因编辑丢失）。

## 4. 文件名与版本

| 产物 | 命名 | 说明 |
|-|-|-|
| 可编辑源 | `<case_id>_graphical_abstract.svg` | 分层 SVG 源 |
| 版面规格 | `spec.json` | 与 SVG 同一几何（再编辑/评审用） |
| 预览 | `<case_id>_graphical_abstract.png` / `.pdf` | 渲染件（后端如实记录） |
| 内容 | `content.json` | 规范化抽取结果（实体/关系/数据/面板） |
| 自查 | `audit.json` / `render_log.json` | 检查与渲染日志 |

SVG `<metadata>` 内嵌 `build_id` 与 Skill 版本；图面布局不含时间戳
（仅 `result.json` 信封字段含时间）——保证同输入重跑的字节级稳定。

## 5. 新增层/元素的流程

1. 在本文件 §1 表登记新层（或在新元素登记 `data-role` 前缀）；
2. 在 `scripts/audit.py` 的 `EXPECTED_LAYERS` / src 检查角色前缀同步更新；
3. 跑 `audit`，确认 `layer_naming` 检查全绿；在 TEST.md 记录结构稳定。