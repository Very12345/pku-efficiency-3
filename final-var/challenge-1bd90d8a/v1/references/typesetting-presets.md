# typesetting-presets.md — 排版预设（期刊样式约束）

目标期刊/模板的排版约束以 `templates/journal_styles.json` 的命名预设承载，
渲染引擎（chartkit）按预设应用字号/线宽/配色/边距/DPI；本文件说明每个预设的
约束内容、适用场景与覆盖方式。**样式是可复用配置，不是一次性手工调整。**

## 1. 预设一览（templates/journal_styles.json）

| 预设 | 适用场景 | 关键参数 |
|-|-|-|
| `default` | 通用/快速浏览 | 标题 34；轴标签 26；刻度 20；dpi 150；sRGB |
| `nature` | Nature 系投稿 | 标题 28；tick 17；线宽 2.4；**300 dpi**；经典配色 |
| `cell` | Cell 系投稿 | 标题 30；tick 18；线宽 2.6；**300 dpi** |
| `prism` | GraphPad Prism 风格汇报 | 标题 32；dpi 200；高对比配色 |
| `minimal` | 无网格极简 | grid 0.6；低饱和灰蓝配色 |
| `ppt` | 汇报/幻灯片 | 标题 40；线宽 4；大字号；演示配色 |

每个预设含：字号组（title/subtitle/axis_label/tick/legend/annotation/panel_label）、
线宽组（grid/axis/line/errorbar）、`bar_width_ratio`、`pad`（轴留白比例）、
`dpi`、`color_space`（sRGB）、`transparent_bg`、`palette`（八色顺序调色板）。

## 2. 覆盖方式（三层）

1. **命名预设**：`--style nature` 或 spec `"style":"nature"` —— 最常用。
2. **spec 内联覆盖**：spec 顶层同名字段（如 `"title_size": 30`）> 预设值
   （chartkit.load_style 以 spec 显式为最高优先级注入 context 前合并）。
3. **新增预设**：直接向 `templates/journal_styles.json` 添加键（如
   `"acs": {...}`），无需改代码。

## 3. 投稿导出约束（结果完整性/导出格式检查点）

| 检查点 | 要求 | 判定 |
|-|-|-|
| 分辨率 | 位图 dpi ≥ 期刊要求（nature/cell 预设 300） | environment.dpi 记录 |
| 色彩空间 | PNG 渲染为 sRGB（RGBA→RGB 白底） | color_space 记录 |
| 字号 | 标题/轴标签/图例/标注 全部 ≥ 期刊最小字号（预设已保证） | 无自动判据，视觉终检 |
| 字体 | CJK 回退链 + PNG 缺字警告 | cjk-font 校验 |
| 矢量源 | 分层 SVG 未转曲（G5） | figcheck real_text |
| 面板对齐 | panel 网格 + 面板字母 A/B/C | spec.grid + 视觉终检 |
| 背景 | 透明背景按需（预设 transparent_bg） | 记录 |

## 4. 说明

- 本包只负责**样式参数**；统计方法/显著性计算不属于本 Skill（转述源数据）。
- 不同期刊对线宽/字体有细则差异，交付前按目标期刊核对 vein（figcheck 无自动判据
  的项进入人工视觉终检，见 SKILL S5 与 audit-rules 第 4 节）。