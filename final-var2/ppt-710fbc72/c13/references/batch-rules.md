# batch-rules.md — 批量一致性规则（整册统一应用）

学术汇报的"批量套模板"场景：对**整册多页**统一应用同一套格式规则，并在批量
处理后校验文件完整性与一致性。本 Skill 的批量规则由 `adopt_plan.py` 在
**阶段一**集中评估（`adopt_plan.json.batch`），由 `adapt_pptx.py` 在**阶段二**
统一执行，由 `audit.py` 在构建后逐页校验。规则冲突时**不静默**——偏差写入
`adopt_plan.batch.deviations` 与 `template_audit.adopt_plan_deviations`。

## 1. 规则清单（R1–R8）

| # | 规则 | 统一对象 | 例外/容忍 | 校验 |
|-|-|-|-|-|
| R1 | 页脚文字一致 | 封面外每页左下角：标题（≤45 字符），9pt 灰 | 封面无页脚 | `layout.footer_uniform` |
| R2 | 页码一致 | 每页右下角阿拉伯数字，从第 2 页起 | 封面无页码 | `layout.footer_uniform` |
| R3 | 标题位置一致 | 非封面页一律标题占位符/固定顶部区域；手工文本框仅占位符缺失时（记录） | 无 | `adopt_plan.consistency` |
| R4 | 字号层级一致 | 全部页面共用 32→12pt 阶梯；标题 ≤ 目标字号、正文按容量降级 | 溢出报告而非压缩 | `layout.overflow` / `layout.font_floor` |
| R5 | 图注格式一致 | `图N 标题 [来源: loc]`，10pt 灰 | — | `xref.figure_*` + 人工抽查 |
| R6 | 图表缩放一致 | 全部 contain-fit 等比，不拉伸 | — | `figure_adjust` / `figure_plan` |
| R7 | 主题继承一致 | 占位符内容不覆盖 run 字体（继承主题字体/色） | 手绘文本框显式设字体 | theme 记录 |
| R8 | 页序/页型一致 | 页序与 `spec.json` 计划一致；页型标题可讲 | 确定性裁剪（deckplan） | `pptx.slide_count` |

## 2. 批量评估在哪里发生

1. **阶段一（adopt_plan.py）**：逐页产出 `page_assignments`（版式/角色是否
   齐备），并汇总 `batch.rules`（规则说明）与 `batch.deviations`（已披露的
   偏差：如页数超目标、版式回退、主题读失败）——**动手前**就知道整册是否
   能一致；
2. **阶段二（adapt_pptx.py）**：统一写页脚/页码/图注/字号；逐页套方案；
3. **构建后（audit.py）**：`layout.footer_uniform`、`pptx.slide_count`、
   `adopt_plan.consistency` 等在真实产物上校验。

## 3. 批量处理边界（诚实声明）

- 一致性 = 规则统一 + 例外显式记录，**不是"每页模板变量都用上"**；多余变量
  不增加任何分（题面："不看生成了多少页、用了多少模板变量"）；
- 封面例外（无页脚/页码）按惯例保留并记录；
- 页数超目标时的确定性裁剪顺序（deckplan trim）：① 合并讨论+局限；
  ② 删议程；③ 合并最后两张结果页——裁剪**绝不静默丢弃证据页**，
  变更进 `change_records`；
- 主题字体/色来自模板继承；若不同版式主题不一致（少见），以
  `adopt_plan.json.template.theme` 的记录为准并披露。