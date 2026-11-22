# HUMAN-TEMPLATES.md — 叙事模板 + 上台前核对清单（v6 合并版）

> 由 `templates/narrative_template.md` 与 `templates/slide-checklist-template.md` 合并，两段内容逐字保留；合并只为守住「≤50 文件」硬门。

---

# 【合并段】叙事模板（原 `templates/narrative_template.md`）

# 叙事模板（narrative template）——学术汇报内容组织（v2）

> 本文件描述 Skill 使用的内容组织模板：报告目标 → 听众 → 叙事顺序 → 页级主张 → 问答准备。
> **机器可执行版本**在同目录 `talk_config.json`（scaffold_plan.py 实际读取它做页数分配；
> `validate_plan.py` 按 `assets/plan.schema.json` 对它 + 计划做门控 P1–P8，并沿
> `references/CONTRACT-GATES.md` 的 G1–G10 收口）；本文档供人（或 Agent 做人工精修时）
> 理解取舍逻辑，两者保持同一套"块"（block）定义。

## 0. 先定报告目标，再定页数与时长

| 汇报类型(`report_type`) | 报告目标（默认成功标准） | 页数建议 | 每页时长 |
|-|-|-|-|
| `group_meeting` 组会进度 | 讲清进度与风险、让合作者能对照图表 | 时长×60/85 秒 | ~85 s |
| `defense` 答辩 | 让评委认可创新点与边界、证据链完整 | 同上 | ~85 s |
| `review` 评审 | 让评审看到每条结论的证据强度与适用范围 | 同上 | ~85 s |

`case.json` 中的 `report_goal` 会覆写默认成功标准；`slide_count` 与 `duration_min`
存在时直接决定页数与节奏，缺失时按上表推导。**听众越不了解背景，背景/术语页占比越高**
（expert 10% / familiar 18% / lay 30%，见 `scaffold_plan.py::resolve_audience`）。
页数优先级：**任务冻结页数 > 时长推导页数 > 论文章节长度**（计划门 P3 校验
`len(pages) == slide_target`）。

## 1. 内容块（block）与叙事顺序

每个块 = 一组页，每页唯一主张（claim）+ 证据定位（evidence）。

| 块 id | 组会 | 答辩 | 评审 | 页内重点 |
|-|-|-|-|-|
| `title` | ✔ | ✔ | ✔ | 标题、报告目标、听众/时长说明 |
| `agenda` | – | ✔ | ✔ | 按叙事顺序给出目录，并说明"为什么是这个顺序" |
| `motivation` | ✔ | ✔ | – | 研究问题：为什么做、缺口在哪（证据=引言段） |
| `background` | ✔ | ✔ | – | 背景与术语铺垫（篇幅由听众熟悉度决定） |
| `method` | ✔ | ✔ | ✔ | 方法与材料：实验/模型/数据来源（证据=方法段） |
| `results` | ✔ | ✔ | ✔ | 结果：逐条主张 + 图/表引用 + 证据强度（证据=结果段） |
| `conclusion_risk` | ✔ | – | – | 结论 + 当前风险与下一步 |
| `innovation_limits` | – | ✔ | ✔ | 创新点与边界：主动划定适用范围 |
| `conclusion` | – | ✔ | ✔ | 结论与展望（评审时先行：结论前置） |
| `qa` | ✔ | ✔ | ✔ | 问答准备（备用页）：预判追问 + 回答要点 + 证据定位 |

**顺序不是论文目录**：组会按"问题—进度—方法—结果—风险"，答辩按"问题—方法—结果—
创新点/边界—结论"，评审"结论先行"。这是本 Skill 与"把论文每节搬成一页"的关键差异。

## 2. 页级主张（每页一句话）

- 一页一主张：`claim` 取源材料原句（逐字保留），证据锚点 = `源文件 · L行号 · §章节`。
- `one_liner`：把 claim 压成一句 ≤64 字可讲的"讲解一句话"。
- `strength` 证据强度：含数值/统计/图表引用 → `strong`；结论/结果动词 → `medium`；
  间接概括 → `weak`（页面会带"※ 间接概括"提示与 uncertainty 记录）。
- 材料中没有对应主张的块 → 用该块源章节首段概括成页并标注 `weak` + `derived=true`
  （诚实降级，不编造；证据审计对 derived 页按"概括语"而非"逐字引文"记录）。

## 3. 问答准备

- 每条局限/风险主张 → 一条预判追问 → 回答要点指向本页证据定位。
- 每条 strong 结果主张 → 一条"证据强度与统计基础"追问。
- `qa` 块是**备用页**：收拢所有追问与回答要点，讲解时不被问就不讲。

## 4. 模板与导出

- 案例自带模板/起始演示 → `python-pptx` 打开并**沿用其母版与版式**新增页面（模板约束不破坏）。
- 无模板 → 用包内置主题（16:9 母版 + 主题色 + 底栏）。
- 每个 Skill 创建的图形元素带确定性命名（`page-claim-NN` / `page-figure-NN` …），
  `verify_deck.py` 机器校验"每页仍表达其主张"，也方便在 PowerPoint 里定位编辑。
- 预览为 Pillow 模拟渲染（每张 PNG 带"PIL 模拟预览"水印），正式效果以 `.pptx` 打开为准。

---

# 【合并段】逐页上台前核对清单（原 `templates/slide-checklist-template.md`）

# 逐页核对清单模板（slide checklist template）——学术汇报内容组织

> 用于人对生成的 deck 做上台前逐页核对（与 `references/CONTRACT-GATES.md` 的机器门互补）。
> 复制本模板、按实际页号逐行打勾；每页一条。**示例，非正式案例结果。**

## 案例：`<case_id>` · `<title>` · 听众 `<audience>` · `<duration> 分钟 / <slide_count> 页`

| 页 | 唯一主张 有字数上限且可讲？ | 主张可溯源（源文件·L行·章）？ | 引文逐字未改写？ | 图/表引用与页内结论对应？ | 证据强度标注与证据匹配？ | 讲稿一句话 ≠ 页面重复？ | 备注含备答？ | 数字与源材料一致？ |
|-|-|-|-|-|-|-|-|-|
| 1 封面 | □ | – | – | – | – | □ | □ | – |
| 2 … | □ | □ | □ | □ | □ | □ | □ | □ |

## 收尾核对（全部勾选才算上台就绪）

- [ ] 页数 == 任务冻结页数；顺序 == 叙事模板（组会/答辩/评审对应顺序）
- [ ] 结论强度与证据匹配：strong 页都有数值/引用支撑；weak 页都标注了"间接概括"
- [ ] 缺失证据都有诚实说明（材料未提供/未解析/占位框）
- [ ] PowerPoint 打开无版式溢出（重点检查图表页与长引文页）
- [ ] 问答备用页预埋的追问能按页定位到证据
- [ ] `result.json` 的 status/sources/uncertainty/change_records 与 deck 实际一致

## 说明

- 逐页勾选的是**内容组织质量**（评分"实际效果/可核验性"的人核侧）；机器侧由
  `scripts/validate_plan.py`（P1–P8）、`scripts/evidence_audit.py`（逐字引文）、
  `scripts/verify_deck.py`（打开/页数/备注/命名）、`scripts/selftest.py`（G1–G10）覆盖。
- derived 页（源材料无直接主张、由章节概括而成）在"主张可溯源"一列按
  "概括自 §章节 首段（weak）"记录，不得勾"逐字引文"。