# RUBRIC_MAP — 评分五维 → 本 Skill 设计覆盖

题面评分：实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 · 生态贡献 10
（GitHub 公开链接另加 5）。下表逐项说明本包如何覆盖，证据都指向 Skill 内
可实际运行的脚本与产物，不靠文字自述。

## 1. 实际效果（40 = 完成度15 + 正确性15 + 完整性5 + 可核验性5）

| 评分点 | 覆盖设计 | 证据位置 |
|-|-|-|
| 任务完成度 15 | 读真实文件→抽主张/图/表（带 `file:line` 来源定位）→ 按页计划建 `deck.pptx`（模板/版式的占位符继承）→ 逐页讲稿备注 → 预览 + result.json 全流程可跑 | `scripts/main.py`（管线）、`scripts/extract.py`、`scripts/deckplan.py`、`scripts/pptxbuild.py` |
| 结果正确性 15 | 页内文字/数字/图号与源材料一致：主张来自抽取（绝不编造数值）；图号交叉引用审计（`xref.figure_refs`）；证据映射 100% 带 loc；母版/版式/占位符继承写入 `template_audit`，`pptx.reopen` 重新打开核验 | `scripts/audit.py` 检查 3/4/16；`references/OUTPUT_CONTRACT.md` |
| 结果完整性 5 | 六类要素全覆盖：论文主线（question→method→results→conclusion 页序）、页结构（10+2 页型）、图表引用（结果页图/表容器+编号+标题+来源）、讲解逻辑（逐页 notes）、模板约束（layout 审计）、导出渲染（2 张预览+render_log） | `scripts/deckplan.py` 页型表；`references/TEMPLATE.md` |
| 可核验性 5 | 源材料、模板、导出件、逐页偏差记录齐备：`content.json`（来源定位）、`spec.json`（页计划）、`audit.json`（真实产物检查+哈希）、`render_log.json`；同输入重跑结构一致（TEST.md §2） | `scripts/audit.py`、`TEST.md` |

## 2. 使用增益（25 = 质量增益15 + 效率增益5 + 增益可验证性5）

| 评分点 | 覆盖设计 | 证据位置 |
|-|-|-|
| 质量增益 15 | 对比基础 Agent 的直接产出，「套用模板/版式继承 + 来源绑定 + 整册一致性 + 逐页讲稿」是可查的结构化增益：每页 claim/evidence/notes 都有字段，**不存在"内容对不上资料"** | 同上 + `slide_evidence` 字段、`template_audit`；对照运行记录见 `TEST.md` §4 |
| 效率增益 5 | 一次命令完成 抽取→计划→建册→脚注/页码/字号→预览→审计→result.json；减少排版耗时与批量返工（整册统一处理而非逐页手改） | `scripts/main.py` 单命令管线 |
| 增益可验证性 5 | 公平对照路径：同一 case 输入，`AUTO=0`？（不用自定义变量）—— 明确记录「基础 Agent 常见失败 vs 本 Skill 检查点」，并以 TEST.md §4 的对照运行（同输入同模板，直接产出 vs Skill 产出）为证据 | `README.md`「预期增益」、`TEST.md` §4 |

## 3. 创新增益（15 = 新增能力5 + 方法改进5 + 创新证据5）

| 评分点 | 覆盖设计 | 证据位置 |
|-|-|-|
| 新增能力 5 | 基础 Agent 难以稳定做到的：**母版/版式/占位符继承关系可查的表驱动适配**（按页型自动选版式+缺占位符回退+主题字体继承）+ 图号↔正文交叉引用自动核验 | `scripts/pptxbuild.py` `_best_layout`、`scripts/audit.py` xref 检查 |
| 方法改进 5 | 内容↔版式映射：claim 容量→字号阶梯（FONT_LADDER + 逐段换行估算，12pt 下限）、图表容器等比 contain-fit（不拉伸）、页脚/页码整册统一、页数超目标时的确定性裁剪策略（合并讨论/局限→去议程→合并结果页） | `scripts/common.py` `fit_font_size`、`scripts/deckplan.py` trim、`scripts/pptxbuild.py` `_contain_fit` |
| 创新证据 5 | 边界与价值：对"模板无目标版式/占位符缺失/超页/缺源图/无 LibreOffice"五种退化场景提供确定性处置并记录（audit/uncertainty），非现成工具行为 | `references/TEMPLATE.md` 异常表、`TEST.md` §3 |

## 4. 可靠体验（10 = 调用与易用性3 + 运行稳定性4 + 异常处理3）

| 评分点 | 覆盖设计 | 证据位置 |
|-|-|-|
| 调用与易用性 3 | SKILL.md 前 8 行给出 name/description（含中英文触发词）；"论文+模板→pptx+预览"一条命令完整流程；README 含依赖清单与最小示例 | `SKILL.md`、`README.md` |
| 运行稳定性 4 | 确定性布局（同输入→同 spec/结构，TEST.md §2）；python-pptx 重开验证；多模板/多页数/缺字体/重复运行均可产出；全脚本仅标准库+python-pptx+PIL（matplotlib/reportlab 仅示例图生成与信息性版本记录） | `scripts/common.py`、`TEST.md` §2/§3 |
| 异常处理 3 | 失败模式表：模板缺失→内置回退、版式缺占位符→手工文本框并记录、溢出→字号阶梯+下限、源图缺失→图位占位框+uncertainty、模板打不开→回退链、预览后端缺失→如实标注；流水线异常仍写 failed result.json | `SKILL.md` §4、`references/TEMPLATE.md`、`scripts/main.py` 异常分支 |

## 5. 生态贡献（10 = 文档完整性3 + 资源可复用性4 + 分享推广价值3）

| 评分点 | 覆盖设计 | 证据位置 |
|-|-|-|
| 文档完整性 3 | SKILL.md（用途/适用条件/输入输出/步骤/异常/自查）、README（运行/依赖/限制/失败处理）、OUTPUT_CONTRACT（契约）、TEMPLATE.md（版式与字号阶梯规则、内置模板说明）、TEST.md（实测记录） | 全部文档位于包内 |
| 资源可复用性 4 | 可直接复用：模板适配层（`pptxbuild.py` 可对任意 pptx 模板做版式审计+套用）、确定性页计划器（`deckplan.py`）、审计器（`audit.py`/`validate_result.py`）、内置回退模板（`templates/builtin.pptx` + 再生成脚本 `make_template.py`）、最小案例（`examples/`） | `scripts/`、`templates/`、`examples/` |
| 分享推广价值 3 | 沉淀可分享能力：页级金标准（每页 claim/evidence 可核对）、字号/间距阶梯规则、图表缩放策略、批量一致性校验、示例案例；`GITHUB_URL.txt` 指向公开仓库 | `references/TEMPLATE.md`、`GITHUB_URL.txt` |

## 明确边界（不夸大）

- 预览为 PIL 示意图而非像素级导出（无 LibreOffice/PPT 时如实标注）；
- 主题色/主题字体通过"占位符继承 + 不覆盖 run 字体"保持，未做主题 XML 深度解析；
- 本 Skill 不代写科学内容：材料里没有的数值绝不补造；
- 平台对照与白板由组织方运行，本包不提交预制答案。