# TEMPLATE —— 面板模板、图层约定与复用指南

本文档描述本 Skill 的图面模板与复用规约，供他人直接套用或扩展。

## 1. 图面模板（单页 4 面板布局）

默认画布 1200×800（`figure_constraints.width/height` 可调，600–4000 范围内自动夹紧）。
四列按阅读顺序排布，列宽比例 250:250:390:270（结果列更宽以容纳数据子图）：

```
┌─────────────────────────────────────────────────────────────────┐
│ 标题（case title）                        case: <case_id>        │  header
├──────────┬──────────┬──────────────┬──────────────┬─────────────┤
│ 1.研究问题│→ 2.方法/机制 │→ 3.核心结果  │  4.结论       │  ← 流程箭头   │
│ ▶实体卡片 │  ▶实体卡片  │  ▶条形成长子图 │  ▶要点        │             │
│ ▶要点    │  ▶面板内关系 │  ▶色阶色块    │  ▶实体        │             │
│          │  ▶要点      │  ▶要点       │              │             │
├──────────┴──────────┴──────────────┴──────────────┴─────────────┤
│ 图例 / Legend（自动生成，值↔颜色/长度一一对应）    比例尺 │ units │   footer
└─────────────────────────────────────────────────────────────────┘
```

面板内元素顺序固定：**实体卡片（≤4）→ 面板内关系箭头行（≤3）→ 要点要点（≤6）**。
结果面板额外承载数据编码：`bar_length` 数据按 1–3 列子图网格（≤2 个=1 列、≤6 个=2 列、否则 3 列），
`color_scale` 数据渲染为整宽色阶条，`area/value_label` 数据渲染为要点行。

## 2. 图层约定（SVG `<g id="layer:*">`）

| 层 | 内容 | 复用约定 |
|-|-|-|
| `background` | 画布底 | 换底色/加期刊模板背景只需改此层 |
| `panels` | 面板框、面板标题、要点文本 | 改日志/换色直接编辑 |
| `entities` | 实体卡片、图标、实体标签 | 每个实体一个卡片组，`data-entity-id` 检索 |
| `relations` | 面板内外箭头与关系标签 | `data-role="relation:<id>"` 检索；负向关系（抑制/阻断）自动红色 |
| `data` | 条形、色块、数值标签 | `data-role="datum_bar:<id>"` 检索；数值改动只改 `<text>` 与条形高度 |
| `legend` | 图例色块与标签 | 自动由 `spec.legend` 生成，严禁手工写字（会失联） |
| `annotations` | 流程箭头、阅读顺序、比例尺 | 版式辅助层 |

元素溯源属性：`data-src`（来源 `文件:行`）、`data-entity-id`、`data-role`、`data-panel`、`data-legend-key`。
迁到 Inkscape/Illustrator 后这些属性仍保留在 XML 中。

## 3. 视觉通道映射表（数据编码规约）

| 通道 | 适用 | 图例呈现 | 注意事项 |
|-|-|-|-|
| `bar_length` | 单值比较（粒径、百分比、倍数） | 色块+数值文本 | 长度∝数值，`audit` 校验数值字符串在图上出现 |
| `color_scale` | 连续/梯度值 | 色阶条 + min…max | 默认 Okabe-Ito 派生色阶；`grayscale_check` 报告弱区分对 |
| `area` | 面积编码值 | 缩放圆 | 图例必须给参考面积对应数值 |
| `value_label` | 少量关键数 | 数值行 | 与单位同行 |

## 4. 风格令牌

- 色板：Okabe-Ito（色盲安全、灰度可打印）`["#0072B2","#009E73","#D55E00","#CC79A7","#F0E442","#56B4E9","#E69F00","#000000","#7F7F7F"]`；`constraints.palette` 可覆盖。
- 字体链：Inter → Helvetica Neue → Arial → Microsoft YaHei → PingFang SC → Noto Sans CJK SC → sans-serif（中西文混排可迁移）。
- 字号层级：标题 26 / 面板标题 14 / 实体名 13 / 要点 10.5 / 数据标签 12 / 页脚 9–11；溢出自动缩号（下限 8）。
- 负向关系（抑制/阻止/下调）用红色 `#B23A3A`，正向用面板主色；方向语义一律实体→指向（箭头指向受作用方）。

## 5. 复用步骤（他人套用到新论文/基金图）

1. 复制 `examples/case.json`，替换 `entities/relations/data/figure_constraints`（数值必须同时在材料文件中出现）。
2. 运行 `python scripts/main.py --case yours/case.json --out yours/out`。
3. 检查 `audit.json`：关注 `missing_values / entity_coverage / bounds`。
4. 打开 SVG 微调：改 `<text>` 文案、移动面板层元素、换 `background` 底色；保存后重新 `python scripts/main.py`（spec.json 为新基线）。
5. 导出：PNG/PDF 已随运行产出；如需期刊专用分辨率 `--raster-scale 3`。

## 6. 扩展点（新增面板类型）

- 在 `figurespec.py` 的 `_panel_content` 增加面板内容类型（如时间轴、通路子图）→ 元素字典进入 `elements` → SVG 与预览同步生效（两者共用同一几何，不会漂移）。
- 在 `extract.py` 增加抽取规则（如 CSV 数字列）→ 保持「带 `src`、首见优先、无源不画」三条不变式。