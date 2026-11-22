# DECK_SPEC.md — 页面蓝图与模板槽位规范

> 说明模板从哪来、槽位如何填、页面模型（plan.json）长什么样、哪些约束
> 绝不能越界。模板是**数据**，不是写死在代码里的样式；页面蓝图是
> deck_tool/slide_text 的确定性映射规则。

## 1. 页面蓝图（论文结构 → 页面结构）

页级叙事角色（`slide_text.ROLE_LABELS`）与收纳规则：

| 角色 | 收纳内容 | 页码常态 | 证据要求 |
|-|-|-|-|
| cover | 标题 + 副题（受众/时长/页数） | 1 | 无（封面页） |
| overview | 主线：研究问题一句 + 摘要/结论首句 | 2 | 摘要/引言/结论 |
| background | 背景/动机 ≤3 条 | 富余页 | §背景/§引言 |
| question | 研究问题 ≤2 条（一页一个问题） | 3–4 | 引言 |
| method | 方法 ≤4 条：核心思路>步骤>差异 | 4–5 | §方法 |
| result | 表驱动量化主张（每表页 2 条）+ 图/表槽 | N | 表/图/§结果 |
| discussion | 解释性结论 ≤3 条 | 富余页 | §讨论 |
| limitation | 局限与边界 ≤3 条 | 富余页 | §局限/展望 |
| takeaway | 带走的一句话 + 下一步 | 末页 | §结论 |

页数分配（`alloc_roles`，确定性）：3–20 页自动展开；5 页起主干
cover→overview→question→method→result→takeaway，富余页先插
background/discussion/limitation，再在收束前增加 result 页。

## 2. 模板来源（三级优先）

| 优先级 | 来源 | 行为 |
|-|-|-|
| 1 | case.json `spec.template_pptx` | 打开组织方 PPTX，沿用其母版/版式字体配色页脚；**只填内容槽位，不修改母版** |
| 2 | case.json `spec.starting_deck` | 同 1 外还要"适配起始稿"：原稿备份到 `work/original_inputs/`，用其版式重排页面，改动记入 change_records |
| 3 | `templates/default.json` | 内置 16:9 学术模板，颜色/字体/页脚/槽位全部参数化（case `spec.style` 可覆盖任意键） |

## 3. 槽位（templates/default.json `slots`）

| 槽位 | 坐标(英寸) | 用途 | 约束 |
|-|-|-|-|
| title | (0.55, 0.30) 12.2×0.95 | 页标题（主张式） | ≤60 字，28pt 粗体，主色 |
| subtitle | (0.55, 1.15) | 封面副题 | 可由 spec.subtitle 覆盖 |
| body | (0.60, 1.85) 12.1×4.9 | 正文要点 | ≤7 条；字号自动收敛 ≥12pt；单条 ≤90 字 |
| body_with_figure | (0.60, 1.85) 7.0×4.9 | 有图/表时正文 | 压缩列宽，字号 15pt 起 |
| figure | (7.95, 1.95) 4.85×4.4 | 图/表/占位 | 见 §4 |
| evidence | (0.60, 6.75) 9.5×0.3 | 页级证据脚注 | 9pt 灰字；每页必填（G6 配套） |
| footer | (0.40, 7.05) 12.5×0.3 | 模板页脚 | 9pt 灰字 + 页码 |

页面蓝图落盘为 `work/plan.json`（**可编辑源**）：`{generated_at, schema,
pages:[{index, role, role_label, title, claims[], figure{}, notes[],
agenda_item}]}`；`--edit` 修改的就是它，再据此重建 deck。

## 4. 图表槽位规则（诚实优先四态）

| figure.kind | 何时用 | 来源 |
|-|-|-|
| `chart_image` | 材料给出数值型数据表 | matplotlib 按表头/数值**原样重绘**，未修改数据 |
| `table` | 图表重绘不可用（无 matplotlib / 数据非数值列 / --no-chart） | PPTX **原生可编辑表格**，数据逐格可改 |
| `embedded` | 材料直接提供图片文件 | 原样嵌入，不改动 |
| `placeholder` | 论文图是位图且无取数数据 | 灰框"诚实占位"，绝不凭空生成曲线 |

## 5. 字体与溢出

- 中文字体：首选 Microsoft YaHei（拉丁+东亚+复杂文种三处 typeface 均设置），
  缺失时回落并记入 `uncertainty`；PPTX 只记字体名，由打开端替换（换机防御）。
- 溢出防护：`_fit_size()` 按字符宽度估算行数，字号逐级下调至 ≥12pt；仍放
  不下的要点降级进演讲者备注并注明。
- 预览渲染（PIL/reportlab）找不到 CJK 字体时只影响预览画质，不影响 PPTX；
  该事实写入 `previews.warnings`（render_qa.qa_report 的 cjk_font_available 检查）。

## 6. 模板约束自查（SKILL.md §7 自查清单第 7 条）

- [ ] 外部模板：母版/版式未被修改（仅新增内容对象）
- [ ] 全部正文处于槽位矩形内（预览核对）
- [ ] 字号 ≥ limits.min_body_pt；标题 ≤ title_max_chars
- [ ] 页脚/页码来源唯一（模板或 spec，不混用）
- [ ] 证据脚注每页存在，与演讲备注一致