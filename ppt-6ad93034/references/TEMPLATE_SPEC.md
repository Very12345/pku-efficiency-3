# TEMPLATE_SPEC.md — 模板槽位与约束规范

讲解清楚模板从哪来、槽位如何填、哪些约束绝不能越界。模板是**数据**，不是
写死在代码里的样式。

## 1. 模板来源（三级优先）

| 优先级 | 来源 | 行为 |
|-|-|-|
| 1 | case.json `spec.template_pptx` | 打开组织方 PPTX，沿用其母版/版式的字体、配色、页脚；本 Skill **只填内容槽位**，不修改母版。 |
| 2 | case.json `spec.starting_deck` | 除第 1 级外还要"适配起始稿"：原稿备份到 `original_inputs/`，替换页面时沿用它的版式，改动记入 `change_records`。 |
| 3 | `templates/default.json` | 内置 16:9 学术模板，颜色/字体/页脚全部可参数化（case.json `spec.style` 可覆盖任意键）。 |

## 2. 槽位（templates/default.json `slots`）

| 槽位 | 坐标(英寸) | 用途 | 约束 |
|-|-|-|-|
| title | (0.55, 0.30) 12.2×0.95 | 页标题（主张式） | ≤60 字，28pt 粗体，主色 |
| subtitle | (0.55, 1.15) | 封面副题 | 可由 spec.subtitle 覆盖 |
| body | (0.60, 1.85) 12.1×4.9 | 正文要点 | ≤7 条；字号自动收敛（≥12pt）；单条 ≤90 字 |
| body_with_figure | (0.60, 1.85) 7.0×4.9 | 有图/表时正文 | 压缩列宽，字号 15pt 起 |
| figure | (7.95, 1.95) 4.85×4.4 | 图/表/占位 | 见 §3 |
| evidence | (0.60, 6.75) 9.5×0.3 | 页级证据脚注 | 9pt 灰字；每页必填 |
| footer | (0.40, 7.05) 12.5×0.3 | 模板页脚 | 9pt 灰字 + 页码 |

## 3. 图表槽位规则（诚实优先）

| figure.kind | 何时用 | 来源 |
|-|-|-|
| `chart_image` | 材料给出数值型数据表 | matplotlib 按表头/数值原样重绘，未修改数据 |
| `table` | 图表重绘不可用（无 matplotlib / 数据非数值列） | PPTX **原生可编辑表格**，数据逐格可改 |
| `embedded` | 材料直接提供图片文件 | 原样嵌入，不改动 |
| `placeholder` | 论文图是位图且无取数数据 | 灰框"诚实占位"，绝不凭空生成曲线 |

## 4. 字体与溢出

- 中文字体：优先 Microsoft YaHei（拉丁+东亚+复杂文种三处 typeface 均设置），
  缺失时回落并记入 `uncertainty`；PPTX 只记字体名，由打开端替换。
- 溢出防护：`_fit_size()` 按字符宽度估算行数，字号逐级下调至 ≥12pt；仍放不
  下的要点降级进演讲者备注并在备注里注明。
- 预览渲染（PIL/reportlab）若找不到 CJK 字体，只影响预览画质，不影响 PPTX
  本身；该事实写入 `previews.warnings`。

## 5. 模板约束自查（SKILL.md 自查清单第 4 条）

- [ ] 外部模板：母版/版式未被修改（仅新增内容对象）
- [ ] 全部正文处于槽位矩形内（预览核对）
- [ ] 字号 ≥ limits.min_body_pt；标题 ≤ title_max_chars
- [ ] 页脚/页码来源唯一（模板或 spec，不混用）
- [ ] 证据脚注每页存在，与会话 notes 一致