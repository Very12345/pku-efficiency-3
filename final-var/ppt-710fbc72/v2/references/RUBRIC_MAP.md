# RUBRIC_MAP — 评分五维 → 本包的具体文件与机制

题面评分：**实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 · 生态贡献 10**
（GitHub 公开作品链接另加 5）。下表逐条把每个评分点落到**本包里可打开、可运行、
可复核的文件或机制**上——不是文字自述，`证据位置` 一列给出的都是包内路径，
括号内是该项在运行时会写进 `result.json` 的具体字段。

> 对照关系自检：五维合计 100 分，表中每个评分点都有一行；没有"仅靠叙述"的
> 评分点。交付前按本表逐行核对一遍（§6 的自查清单）。

## 1. 实际效果（40 = 任务完成度 15 + 结果正确性 15 + 结果完整性 5 + 可核验性 5）

| 评分点 | 覆盖设计（本包做了什么） | 证据位置（包内路径 + 运行时字段） |
|-|-|-|
| 任务完成度 15 | 一条命令走完真实链路：读真实 `case.json`/`task.md`/材料/模板 → 抽主张与图表（带 `文件:行`）→ 确定性页结构方案 → **阶段一适配方案**（模板母版/版式/占位符审计 + 页→版式分配）→ **阶段二按方案建册**（占位符继承、逐页讲稿备注、页脚页码）→ 预览 → 审计 → `result.json`；平台运行时直连 `/input`、`/app/work`、`/app/output` | `scripts/main.py`（`run()` 全流程）、`scripts/extract.py`、`scripts/deckplan.py`、`scripts/adopt_plan.py`、`scripts/adapt_pptx.py`；产物清单 `result.json.artifacts`（8 项，各带 sha256） |
| 结果正确性 15 | ① 页内文字只来自抽取结果（材料里没有的数值绝不补造，缺项进 `uncertainty`）；② 图号双向核验（正文引用 ⊂ 图清单，图清单 ⊆ 结果页放置）；③ 模板继承**真实发生且可查**（每页实际套用的版式名/master/来源写在 `template_audit.layout_used`，主题字体色读 `theme1.xml`）；④ pptx 用 python-pptx **重开验证**；⑤ 契约回显取**真实值**（`preview_png`/`evidence_per_slide`/`notes_per_slide`/`template_inheritance` 由产物推出，不再回落成 `false`），派生来源记在 `verification.contract_echo_derived` | `scripts/audit.py`（`content.claim_coverage`、`xref.figure_refs`、`xref.figure_placement`、`pptx.reopen`、`pptx.slide_count`、`layout.*`）、`scripts/main.py`（`_derive_contract_value()`）、`references/OUTPUT_CONTRACT.md` |
| 结果完整性 5 | 六类要素全覆盖：论文主线（cover→background→methods→results×N→discussion→limitations→conclusion）、页结构（含 agenda/evidence_map/thankyou 页型与超页裁剪）、图表引用（图/表容器 + 编号 + 标题 + 来源）、讲解逻辑（逐页 speaker notes 含建议时长）、模板约束（版式审计 + 方案套用一致性）、导出渲染（两张预览 + 渲染日志） | `scripts/deckplan.py` 页型表、`scripts/adapt_pptx.py`（图表/表格/页脚/备注）、`references/template_guide.md`、`references/batch-rules.md` |
| 可核验性 5 | 每条结论都有落盘记录：`content.json`（抽取 + 来源定位 + 材料 sha256）、`spec.json`（页计划）、`adopt_plan.json`（阶段一方案，含批量规则偏差）、`audit.json`（21 条真实产物检查）、`render_log.json`（渲染后端与字体）、`result.json`（契约 + 门）；同输入重跑**逐字节一致**（仅 `generated_at` 不同，`TEST.md` §2 实测） | `scripts/audit.py`、`scripts/adopt_plan.py`、`TEST.md` §2、`examples/EXPECTED-OUTPUT.md`（示例运行的逐文件实测清单） |

## 2. 使用增益（25 = 质量增益 15 + 效率增益 5 + 增益可验证性 5）

| 评分点 | 覆盖设计 | 证据位置 |
|-|-|-|
| 质量增益 15 | 相对"基础 Agent 直接往默认版式里塞正文"，本包提供的是**可查的结构化增益**：① 先方案后执行——版式分配在动手前定稿，阶段二逐页套用并记录偏差（`adopt_plan_applied` / `adopt_plan_deviations`）；② 每页 claim/evidence/notes 都有字段，不存在"内容对不上资料"；③ 整册一致性（页脚/页码/标题位置/字号阶梯/图表缩放）由批量规则统一并审计；④ 起始 deck 改编时**旧页连关系一起移除**，不会出现"只改前几页、后面还是旧模板" | `scripts/adopt_plan.py`、`scripts/adapt_pptx.py`（`template_audit.*`）、`scripts/pptx_toolkit.py`（`drop_slides()`）、`references/batch-rules.md`、`result.json.slide_evidence`（每页 claim/图表引用/证据） |
| 效率增益 5 | 一条命令完成 抽取→页计划→适配方案→建册→脚注页码字号→预览→审计→契约门；批量规则**单点评估**而非逐页手改；分步命令（`references/two-phase-workflow.md`）用于返工定位，不必整册重跑；重建二进制资源只需两条脚本命令（模板/示例图） | `scripts/main.py`（单命令）、`references/two-phase-workflow.md`、`scripts/make_template.py`、`scripts/make_synthetic_inputs.py` |
| 增益可验证性 5 | 增益不是自述而是可复跑记录：同一示例案例的**朴素基线 vs 本 Skill**对照表在 `TEST.md` §5；阶段一→阶段二的逐页吻合由 `audit` 的 `adopt_plan.consistency` 检查（示例运行 10/10、0 偏差）；同输入重跑确定性在 `TEST.md` §2；三条鲁棒性分支（模板损坏 / 显式模板 / 起始 deck 编辑）在 `TEST.md` §4 各有真实运行结果 | `TEST.md` §2/§4/§5、`scripts/audit.py`（`adopt_plan.consistency`）、`references/checklist.md` |

## 3. 创新增益（15 = 新增能力 5 + 方法改进 5 + 创新证据 5）

| 评分点 | 覆盖设计 | 证据位置 |
|-|-|-|
| 新增能力 5 | **两阶段工作流（方案先行）**：`adopt_plan.py` 把"模板结构审计 + 页→版式分配 + 批量规则 + 图表放置计划"在动手前固化成机器可读方案，`adapt_pptx.py` 按方案执行并逐条记录偏差；基础 Agent 或现成模板工具通常是"读一页填一页"，没有可核对的中间判据 | `scripts/adopt_plan.py`、`references/two-phase-workflow.md`、`result.json.adopt_plan`（阶段一方案摘要 + gates） |
| 方法改进 5 | ① 内容↔版式映射：claim 容量 → 字号阶梯（32→12pt，换行按占位符真实几何估算，地板 12pt，溢出上报不静默压字）；② 图表等比 contain-fit（按容器实算比例，绝不拉伸）；③ 页脚/页码/标题位置整册统一；④ 主题字体/主题色只读继承可查；⑤ 超页时确定性裁剪顺序；⑥ **二进制资源运行时生成**（模板/示例图/预览），使包体只含文本资源仍能产出完整形态 | `scripts/common.py`（`FONT_LADDER`/`fit_font_size`）、`scripts/adapt_pptx.py`（contain-fit/页脚/备注）、`scripts/adopt_plan.py`（批量规则/图表计划）、`scripts/make_template.py` |
| 创新证据 5 | 五种退化场景各有**确定性处置 + 记录位置 + 决策编号**：模板无目标版式（best-fit + `adopt_plan_deviations`）、占位符缺失（手绘框 + `layout_fallback_used`）、文本框溢出（字号地板 + `layout.overflow`）、源图缺失（图位占位框 + `uncertainty`）、无 LibreOffice（不产伪 PDF + `preview_is_schematic`）；全部收敛成 D1–D12 决策规则 + CP1–CP3 检查点，边界与价值可复验 | `references/failure-modes.md`、`SKILL.md` §4/§5、`references/checklist.md`、`TEST.md` §4（三条分支实测） |

## 4. 可靠体验（10 = 调用与易用性 3 + 运行稳定性 4 + 异常处理 3）

| 评分点 | 覆盖设计 | 证据位置 |
|-|-|-|
| 调用与易用性 3 | `SKILL.md` 前置 YAML frontmatter 给出 name/description 与中英文触发词；"论文+模板→pptx+预览"一条命令；**命令自定位**：文档里一律写 `"$SKILL_DIR/scripts/..."`，脚本用 `os.path.dirname(__file__)` 定位 Skill 根，**cwd 不是技能根目录时照样能跑**（`TEST.md` §3 实测）；`README.md` 给依赖、最小示例与分步命令 | `SKILL.md`（§3 命令块）、`README.md`、`scripts/common.py`（`skill_root()`）、`TEST.md` §3 |
| 运行稳定性 4 | 同输入重跑确定性（`spec.json`/`adopt_plan.json`/pptx/两张 PNG 逐字节一致，`result.json` 仅时间戳差异；pptx 的 zip 时间戳被固定化并去重同名条目）；构建后 python-pptx 重开验证；多模板/多页数/缺字体/重复运行均可产出；CP3 把"产物 + 契约"变成硬门，失败显式而非静默 | `scripts/pptx_toolkit.py`（`deterministic_zip()`）、`scripts/audit.py`、`TEST.md` §2、`result.json.verification.contract_gates` |
| 异常处理 3 | `references/failure-modes.md` 失败模式表（识别→处置→记录→决策编号）+ `SKILL.md` D1–D12 + CP1–CP3：case 不可解析→立即失败不产半成品；模板缺失/损坏→回退链（含**运行时生成**的内置回退，生成失败也只记录原因不抛栈）；版式缺占位符→手绘框并记录；溢出→字号地板 + 上报；源图缺失→占位框保留图号来源；无预览后端→如实标注；流水线异常→先落盘部分产物再写 `status=failed` 的 `result.json` | `references/failure-modes.md`、`SKILL.md` §4/§5、`scripts/main.py`（异常分支写 failed result）、`scripts/make_template.py`（`ensure_builtin()` 返回原因而非抛异常） |

## 5. 生态贡献（10 = 文档完整性 3 + 资源可复用性 4 + 分享推广价值 3）

| 评分点 | 覆盖设计 | 证据位置 |
|-|-|-|
| 文档完整性 3 | `SKILL.md`（用途/适用条件/输入输出/两阶段步骤/决策规则/失败处理/自查清单/目录/资源形态）、`README.md`（运行/依赖/输入字段/输出/增益/限制/维护）、`references/OUTPUT_CONTRACT.md`（字段契约 + CP3 门 + 资源形态）、`template_guide.md`（母版/版式/占位符/主题/字号阶梯）、`checklist.md`（收尾验收清单）、`batch-rules.md`（批量规则）、`two-phase-workflow.md`（两阶段图示与逐条命令）、`failure-modes.md`、`TEST.md`（实测记录）、`examples/README.md` + `examples/EXPECTED-OUTPUT.md`（示例怎么跑、应产出什么）——均随包 | `SKILL.md`、`README.md`、`TEST.md`、`references/`（7 篇）、`examples/*.md` |
| 资源可复用性 4 | 可被他人直接复用的部分：模板适配层（`pptx_toolkit.py` + `adapt_pptx.py` 能对**任意** pptx 做母版/版式/占位符审计与套用）、阶段一方案器（`adopt_plan.py` 单点分析任意模板）、确定性页计划器（`deckplan.py`）、审计与契约工具（`audit.py` / `validate_result.py` / `check_contract.py`，均带独立 CLI 与退出码语义）、回退模板生成器（`make_template.py`）、示例输入生成器（`make_synthetic_inputs.py`）、最小案例与方案样例（`examples/`）、页级金标准字段（每页 claim/evidence 可核对） | `scripts/`（13 个脚本）、`examples/`（case/task/material + plan/adopt_plan 样例 + 文本产物）、`examples/EXPECTED-OUTPUT.md` |
| 分享推广价值 3 | 沉淀的是可迁移的**方法**而非一次性产物：两阶段工作流、字号/间距阶梯与容差规则、图表缩放策略、批量一致性校验、失败模式与决策规则表、契约四形态回显与 CP 门；`GITHUB_URL.txt` 指向公开仓库，`examples/` 可直接作为他人上手题集 | `references/`、`GITHUB_URL.txt`、`examples/`、`TEST.md` §5 |

## 6. 明确边界（不夸大，交付前逐条确认）

- 预览是 **PIL 示意图**而非像素级导出；无 PowerPoint/LibreOffice 时**不产伪 PDF**，
  能力缺失记在 `render_log.json` 与 `uncertainty`（`preview_is_schematic=true`）；
- 主题色/主题字体是**只读记录**（读 `theme1.xml`），不改写主题 XML、不换色板；
- 复杂 SmartArt / 艺术字 / 动画 / 切换不在范围；
- **不代写科学内容**：材料里没有的数值、结论、图件绝不补造，缺项一律进
  `uncertainty`；
- 平台对照与白板由组织方运行；本包**不提交预制答案**，`examples/` 一律标注
  "示例，非正式案例"，`GITHUB_URL.txt` 只指向作品本身；
- 包内**无二进制资源**（只含 `.md/.py/.json/.txt`）：需要 pptx/PNG 时由
  `scripts/make_template.py`、`scripts/make_synthetic_inputs.py` 或运行时产物生成。

---

## 7. v2 的落地方式：五维 → 可测量证据（增益可验证）

前六节写的是"这个包有哪些设计"。本节回答：
**每个评分点背后有没有一个第三方能算出来的数？** v2 的做法是把评分点接到
`references/GAIN-PROTOCOL.md` 定义的指标（Q1–Q8 / E1–E4）上。

### 7.1 "使用增益 25"是本节的主战场

题面把使用增益拆成**质量增益 15 · 效率增益 5 · 增益可验证性 5**。这三项的关键差别
在于：前两项是"结论"，第三项是"结论的可复核性"。v2 的处置：

| 评分点 | 结论 | 支撑它的测量 | 落在哪条指标 |
|-|-|-|-|
| 质量增益 15 | 同模板条件下，本 Skill 补齐一册学术汇报应有的可核验要件 | 页数 3→10、讲稿覆盖 0.0→1.0、定位串 0→16、页脚页数 0→9、`result.json` 键数 无→28、CP3 门 无→8/8 | Q1–Q8 |
| 效率增益 5 | 返工定位成本下降（阶段产物解耦）；单册总代价上升约 3.8× 换取全部 Q 指标 | E1 中位数 0.392 s → 1.508 s；E2 改模板只需重跑两个阶段 | E1 / E2 |
| 增益可验证性 5 | 协议 + 指标 + 操作步骤 + 实测记录写在同一处；**对自方不利的差异也列出** | `GAIN-PROTOCOL.md` §2–§6；E3 只有 11/12 字节一致、E4 需人工复查 34 条（对 B 臂不利） | E3 / E4 |

### 7.2 五维各自的可测量落点

| 维度 | 分值 | 可测量的落点 | 指标 |
|-|-|-|-|
| 实际效果 | 40 | 页数达成度、证据定位覆盖率、图表放置完整率、模板继承记录条数、契约门通过数 | Q1/Q3/Q5/Q6/Q8 |
| 使用增益 | 25 | 上表 §7.1 的三行 | Q1–Q8 / E1–E4 |
| 创新增益 | 15 | 方案先行（`adopt_plan` 存在且被消费）、二进制运行时生成（包内 0 二进制） | Q7 / 见 `TEST.md` §4f |
| 可靠体验 | 10 | 四条分支实测 + 确定性（11/12）+ CP2 重开校验 + 退出码语义（0/1/2） | E3 |
| 生态贡献 | 10 | 文档完整（契约 + 协议 + 指标定义）；13 个脚本独立 CLI；`examples/` 可直接当题集 | — |

### 7.3 对照实验的"公平性"本身就是评分材料

评审若要判断"增益可验证性 5"，最直接的动作是按 `GAIN-PROTOCOL.md` §8 的清单
逐条核对。其中**最容易失败的一条**是 C2（同模板）：

- B 臂 `template_audit.opened_from` 必须是 `case_template`；
- 若为 `builtin`，说明两臂模板来源不同，**整个对照作废**。

把这条写成"可失败的检查项"而不是"我们保证了公平"，是 v2 在增益可验证性上的具体
做法：**一个不能被推翻的公平声明不算证据**。

### 7.4 明确不宣称的部分（对应题面"文字自述不能替代实际运行证据"）

- 本包给出的对照是**合成示例上的本地代理臂**，不是平台白板，也不是平台真实基础
  Agent 的运行记录（`GAIN-PROTOCOL.md` §7.2）；
- 未测项：人工排版耗时、跨模板族泛化、PDF 导出保真；
- 因此**不使用"平台分数""排名"一类措辞**，只报可复算的指标值。

### 7.5 交付前按本节自检

- [ ] 五维里每一维都能指到 §7.2 表中的至少一条指标
- [ ] `GAIN-PROTOCOL.md` §6 的数字与 `TEST.md` §7 的数字一致
- [ ] 协议 §7.2 的"未测项"清单已按本次实际范围更新
- [ ] 没有任何评分点只用形容词支撑（若发现，补一条指标或明确列入未测）
