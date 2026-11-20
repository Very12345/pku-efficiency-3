# RUBRIC_MAP — 评分五维 → 本 Skill 设计覆盖（v2）

题面评分：实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 · 生态贡献 10
（GitHub 公开链接另加 5）。下表逐项说明本包如何覆盖；证据都指向 Skill 内
**可实际运行的脚本与真实产物**，不靠文字自述。v2 相对 v1 的新落点以 `(v2)` 标注。

## 1. 实际效果（40 = 完成度15 + 正确性15 + 完整性5 + 可核验性5）

| 评分点 | 覆盖设计 | 证据位置 |
|-|-|-|
| 任务完成度 15 | 读真实文件→抽主张/图/表（带 `file:line`）→ 确定性页计划 → **(v2) 适配方案**（模板结构审计+页→版式分配）→ 按方案建 `deck.pptx`（占位符继承）→ 逐页讲稿备注 → 预览 + result.json 全流程可跑 | `scripts/main.py`（两阶段管线）、`extract.py`、`deckplan.py`、`adopt_plan.py`、`adapt_pptx.py` |
| 结果正确性 15 | 页内文字/数字/图号与源材料一致：主张来自抽取（绝不编造）；图号交叉引用审计；证据映射 100% 带 loc；母版/版式/占位符继承写入 `template_audit`（**(v2) 主题字体/主题色读 theme1.xml**），`pptx.reopen` 重开核验 | `scripts/audit.py` 检查 3/4/16；`references/OUTPUT_CONTRACT.md` |
| 结果完整性 5 | 六类要素全覆盖：论文主线（question→method→results→conclusion 页序）、页结构（10+2 页型）、图表引用（图/表容器+编号+标题+来源）、讲解逻辑（逐页 notes）、模板约束（layout 审计+方案套用一致性）、导出渲染（2 张预览+render_log） | `deckplan.py` 页型表；`references/template_guide.md` |
| 可核验性 5 | 源材料、模板、适配方案、导出件、逐页偏差记录齐备：`content.json`（来源定位）、`spec.json`（页计划）、**(v2) `adopt_plan.json`（方案，含批量规则偏差）**、`audit.json`、`render_log.json`；同输入重跑结构一致（TEST.md §2） | `scripts/audit.py`、`scripts/adopt_plan.py`、`TEST.md` |

## 2. 使用增益（25 = 质量增益15 + 效率增益5 + 增益可验证性5）

| 评分点 | 覆盖设计 | 证据位置 |
|-|-|-|
| 质量增益 15 | 相对基础 Agent，模板套用/版式继承 + 来源绑定 + 整册一致性 + 逐页讲稿 + **(v2) 先方案后执行**（版式分配在动手前定稿，方案↔执行一致性可查）是有据可查的结构化增益；每页 claim/evidence/notes 均有字段，不存在"内容对不上资料" | `slide_evidence`、`template_audit.adopt_plan_*`；对照记录 `TEST.md` §4 |
| 效率增益 5 | 一条命令完成 抽取→页计划→适配方案→建册→脚注/页码/字号→预览→审计→契约门；**(v2) 批量规则单点评估**（页脚/页码/标题位置/字号阶梯整册统一），减少逐页手改与返工 | `scripts/main.py`、`references/batch-rules.md` |
| 增益可验证性 5 | 同输入同模板对照（直接产出 vs Skill 产出）记录在 `TEST.md` §4；v2 另以 `adopt_plan.consistency` 审计「方案→执行」逐页吻合 | `TEST.md` §4、`scripts/audit.py` |

## 3. 创新增益（15 = 新增能力5 + 方法改进5 + 创新证据5）

| 评分点 | 覆盖设计 | 证据位置 |
|-|-|-|
| 新增能力 5 | **两阶段工作流（(v2) 先方案后执行）**：`adopt_plan.py` 把模板结构审计、页→版式分配、批量规则、图表放置计划在动手前固化为机器可读方案，`adapt_pptx.py` 按方案套用并记录偏差 —— 基础 Agent/现成工具通常直接逐页硬填 | `scripts/adopt_plan.py`、`references/two-phase-workflow.md` |
| 方法改进 5 | 内容↔版式映射：claim 容量→字号阶梯（FONT_LADDER + 换行估算，12pt 下限）、图表容器等比 contain-fit（不拉伸）、页脚/页码整册统一、(v2) 主题字体/色继承可查、页数超目标确定性裁剪 | `scripts/common.py`、`adapt_pptx.py`、`adopt_plan.py` |
| 创新证据 5 | 五种退化场景的确定性处置与记录：模板无目标版式/占位符缺失/超页/缺源图/无 LibreOffice——(v2) 全部升级为**失败模式文档 + D 决策规则 + 检查点门**，边界与价值可复验 | `references/failure-modes.md`、`references/checklist.md`、`TEST.md` §5 |

## 4. 可靠体验（10 = 调用与易用性3 + 运行稳定性4 + 异常处理3）

| 评分点 | 覆盖设计 | 证据位置 |
|-|-|-|
| 调用与易用性 3 | SKILL.md 前 8 行给出 name/description（含中英文触发词）；"论文+模板→pptx+预览"一条命令完整流程；README 含依赖清单与最小示例；脚本全部 `os.path.dirname(__file__)` 自定位，不依赖 cwd | `SKILL.md`、`README.md`、`scripts/common.py` |
| 运行稳定性 4 | 确定性（同输入→同方案/同 spec/结构，TEST.md §2 实测逐字节）；python-pptx 重开验证；多模板/多页数/缺字体/重复运行均可产出；(v2) 契约门 CP3 把"产物+契约"变成硬门，失败显式而非静默 | `scripts/common.py`、`TEST.md` §2/§3 |
| 异常处理 3 | (v2) `references/failure-modes.md` 18 项失败模式表 + SKILL.md D1–D12 决策规则 + 检查点 CP1–CP3：模板缺失→内置回退、版式缺占位符→手绘框并记录、溢出→字号阶梯+下限、源图缺失→图位占位框、模板打不开→回退链、预览后端缺失→如实标注；流水线异常仍写 failed result.json | `SKILL.md` §4/§5、`references/failure-modes.md`、`scripts/main.py` 异常分支 |

## 5. 生态贡献（10 = 文档完整性3 + 资源可复用性4 + 分享推广价值3）

| 评分点 | 覆盖设计 | 证据位置 |
|-|-|-|
| 文档完整性 3 | SKILL.md（用途/适用条件/输入输出/两阶段步骤/异常/自查+检查点）、README（运行/依赖/限制）、OUTPUT_CONTRACT（契约+硬性门）、template_guide（模板规范/版式/字号阶梯）、checklist（适配检查清单）、batch-rules（批量规则）、two-phase-workflow（两阶段）、failure-modes（失败模式）、TEST（实测记录） | 全部文档位于包内 |
| 资源可复用性 4 | 可直接复用：模板适配层（`adapt_pptx.py`+`pptx_toolkit.py` 可对任意 pptx 审计+套用）、**(v2) 适配方案器（`adopt_plan.py` 单点分析任意模板生成方案）**、确定性页计划器（`deckplan.py`）、审计器（`audit.py`/`validate_result.py`/**`check_contract.py`**）、内置回退模板（`templates/builtin.pptx` + 再生成脚本）、最小案例（`examples/`） | `scripts/`、`templates/`、`examples/` |
| 分享推广价值 3 | 沉淀可分享能力：页级金标准（每页 claim/evidence 可核对）、字号/间距阶梯规则、图表缩放策略、批量一致性校验、失败模式知识；`GITHUB_URL.txt` 指向公开仓库 | `references/`、`GITHUB_URL.txt` |

## 明确边界（不夸大）

- 预览为 PIL 示意图而非像素级导出（无 LibreOffice/PPT 时如实标注）；
- 主题色/主题字体通过占位符继承 + theme1.xml 只读记录保持，不做主题 XML 改写；
- 复杂 SmartArt/动画/切换不在范围；
- 本 Skill 不代写科学内容：材料里没有的数值绝不补造；
- 平台对照与白板由组织方运行，本包不提交预制答案；示例一律标注"示例，非正式案例"。