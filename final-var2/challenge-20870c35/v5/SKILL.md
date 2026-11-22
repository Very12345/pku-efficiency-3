---
name: academic-talk-organizer
description: >
  组织学术汇报内容（学术 PPT 页面组织）：从论文/研究材料到可讲、可编辑、证据可追溯的演示文件。
  当输入包含科研论文材料、研究报告、组会/答辩/评审任务、听众与时长、页数与模板约束、讲稿或备注需求，
  关键词如 学术汇报、答辩PPT、组会汇报、slides、deck、页码规划、讲稿、备注、问答准备、听众适配、
  叙事顺序、汇报内容组织、evidence mapping、模板适配、plan contract、quality gates、
  多案例、泛化、题集、难度分层、可接受区间、失效边界、报告类型适配、结论先行、
  矛盾指标时使用本 Skill：
  读真实材料 → 抽取研究问题/方法/结果/局限 → 页级计划并经计划契约门 P1–P8 校验 →
  python-pptx 生成可编辑 .pptx（模板适配或内置主题）→ verify_deck 校验 → PIL 渲染预览 →
  evidence_audit 逐字审计 → finalize_result 写 result.json。严格以真实文件为准，不臆造数据。
  本版（v5）的落点是**多案例泛化与题集**：examples/cases/ 下两个不同题材的合成案例
  （实验物理·答辩 / 计算生物学·评审），逐案给出输入、期望产出结构、可接受区间、难度层与实测结果，
  并如实写明泛化到哪会失效，见 references/CASE-SET.md。
---

# 学术汇报内容组织 · v5 多案例泛化与题集版

面向「玻尔产品周赛 · 学术效率 · 第三期」challenge-20870c35（slides 组）。
把**已有**的论文/研究材料组织成：结构清楚、证据可追溯、可编辑、符合听众与模板约束的学术汇报产物。
本 Skill 不负责论文精读成文、写作成稿与科研绘图本身（相邻课题负责），只负责
**从已有内容材料到可讲页面的组织与交付**。

> **题面两条硬约束（Runtime contract 原文）**：
> ① `Skill resources: at most 50 UTF-8 text files, 500KB each and 2MB total, no symlinks.`
> ② `Runtime artifacts may be binary and are retained independently of final JSON validity.`
> ⇒ 提交资源**只有文本**（`.md/.py/.json/.txt/.csv/.yaml/.yml`），`.pptx/.png/.pdf` 等**一律由脚本运行时生成**；
> 包内不含任何本机绝对路径、无 `__pycache__`、无符号链接。逐类处置见 §8。

## 0. 本版的主张：单案例跑通 ≠ 这个交付物能用

一个 Skill 在**一个**案例上跑出漂亮结果，可能只是因为它恰好适配那个案例。
真正要回答的是：换成**别的学科**、**别的汇报类型**、**别的页数/时长量级**，它还是同一个交付物吗？
本版为此做三件事：

1. **换三个维度再造两个案例**（`examples/cases/`），且都与最小示例不同学科
   —— 不是"同样的东西再跑一遍"。
2. **把期望写成可判定的形式**（页数、块顺序、页数区间、问答条数、审计数值），
   这样"通过"不是主观判断，而是逐项比对。
3. **主动公开失效边界**：三个探针（未知汇报类型 / 页数越界 / 非中文材料）都**真跑过**，
   包括**两条未修的已知边界**。只展示成功案例的题集，复用价值远低于此。

## 1. 题集总览

| 案例 | 题材 | 汇报类型 | 听众 | 时长 | 冻结页数 | 难度层 | 主要考察点 |
|-|-|-|-|-|-|-|-|
| **L1** `examples/`（最小示例） | NLP 跨语言句子对齐 | `group_meeting` | familiar | 20 min | 12 | L1 易 | 接口演示；含 PDF 材料路径 |
| **L2** `case-a-muon-defense` | 凝聚态**实验物理**（μSR 内场分布反演） | `defense` 答辩 | expert | 25 min | 15 | L2 中 | 数值证据链；**三条局限必须靠前**；图引用存在但图片缺席 → 诚实占位 |
| **L3** `case-b-scrna-review` | 计算**生物学**（单细胞计数去噪） | `review` 评审 | expert | 12 min | 8 | L3 偏难 | **结论先行**；**两个互相矛盾的指标必须同页**；短时长下的取舍压缩 |

> **难度分层依据**：L1→L2→L3 的难度**不来自材料更长**，而来自**约束互相冲突**。
> L3 只有 8 页、12 分钟，却同时要求"结论先行"与"两个矛盾指标都得上页" ——
> 页数预算与信息完整性直接对撞，这才是真正难的地方。

## 2. 逐案：输入 / 期望产出结构 / 可接受区间 / 实测

> 采集环境：Python 3.13.9 · python-pptx 1.0.2 · Pillow 12.3.0 · pypdf 6.14.2 · win32，
> **包外目录**运行（包内跑会生成 `__pycache__` 而使提交包不合规）。所有数值为合成数据。

```bash
SKILL_DIR="<本包根目录>"; OUT="<包外空目录>"
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/cases/case-a-muon-defense/case.json" --out "$OUT/a"
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/cases/case-b-scrna-review/case.json"   --out "$OUT/b"
```

### 2.1 L2 `case-a-muon-defense`（物理 · 答辩 · 25 min / 15 页）

**输入**：`case.json`（`report_type=defense`、`duration_min=25`、`slide_count=15`）+ `task.md`
（含 `output_contract` 声明块）+ `materials/paper_and_figures.md`（论文主体 + 图表清单，**不带图片文件**）。

| 项 | 期望 | 可接受区间 | 实测 |
|-|-|-|-|
| 页数 | == 冻结页数 15 | 恰好 15（P3 门） | **15** |
| 块顺序 | 答辩叙事，`motivation` 在 `method` 前、`innovation_limits` 在 `results` 后 | 与 `talk_config.json` 的 `defense` 一致 | `title, agenda, motivation, background, method, results, innovation_limits, conclusion, qa` |
| 结果页数 | 3–5 页 | 页 7–10 区间 | **4** |
| 局限/边界页 | ≥ 2 页 | — | **2** |
| `qa` 备用页 | ≥ 1 页 | — | **2** 页 |
| 问答条数 | ≥ 2（每条局限 + 每条 strong 结果） | — | **3** |
| 图表引用 | 与源材料一致，不许臆造 | — | `Fig. 1` → 页 7，页内**诚实占位** |
| `status` | `completed` | — | **`completed`** |
| `result.json` 顶层键 | 契约 16 字段齐全 | — | **20** |
| 证据审计 | `valid=true`、`errors=0` | — | **`11/11 ok`，`derived=3`** |

```
[plan] 15 pages, narrative=defense, audience=expert, P-gates valid=True
[deck] 15 slides, mode=built-in-theme, verify valid=True
[preview] wrote 14 preview files (PIL simulation)
[done] status=completed ... validate_valid=True contract_valid=True
EXIT=0
```
`main_line` 计数：`research_question=1, method=2, results=4, limitations=2, conclusion=1`；
逐页强度：`strong`×6 · `medium`×1 · `weak`(derived)×3 · 结构页×5；`uncertainty` **4** 条。

### 2.2 L3 `case-b-scrna-review`（生物 · 评审 · 12 min / 8 页）

| 项 | 期望 | 可接受区间 | 实测 |
|-|-|-|-|
| 页数 | == 冻结页数 8 | 恰好 8（P3 门） | **8** |
| 块顺序 | **结论先行**：`conclusion` 早于 `method`/`results` | 实测 `conclusion` 位于第 3 页 | `title, agenda, **conclusion**, method, results, innovation_limits, qa` |
| 两个矛盾指标 | **同时**上页（10.9% 与 0.4%） | 两者都能在 `pages[].claim` 或 `evidence[].quote` 找到 | 均在页内 |
| 结果页数 | 2–3 页 | — | **2** |
| `qa` 备用页 / 问答条数 | 1 页 / ≥ 2 条 | — | **1 页 / 2 条** |
| `status` | `completed` | — | **`completed`** |
| 证据审计 | `valid=true`、`errors=0` | — | **`5/5 ok`，`derived=1`** |

```
[plan] 8 pages, narrative=review, audience=expert, P-gates valid=True
[deck] 8 slides, mode=built-in-theme, verify valid=True
[preview] wrote 8 preview files (PIL simulation)
[done] status=completed ... validate_valid=True contract_valid=True
EXIT=0
```
图表引用：`Table 1` → 页 4、`Fig. 1` → 页 6（均为诚实占位）；`uncertainty` **4** 条。

> **该案暴露的结构性事实**：`main_line.research_question = 0`。原因是 `review` 叙事里
> **没有 `motivation` 块**（结论先行的代价），而 `main_line.research_question` 只由 `motivation` 填充。
> ⇒ 读 `main_line` 的下游消费者必须允许该键为空数组，不能假设四种汇报类型都有研究问题条。

## 3. 换题材、换类型真正改变了什么（实测对照，非推断）

| 维度 | L2（物理·答辩） | L3（生物·评审） | 变化来自 |
|-|-|-|-|
| 块顺序 | `motivation, background, method, results, innovation_limits, conclusion` | `conclusion, method, results, innovation_limits` | `report_type` 驱动的叙事配置 |
| 页数 | 15 | 8 | 案例冻结页数（P3 门） |
| `motivation` / `background` 页 | 有 | **无** | 评审类型的块集合 |
| 问答条数 | 3 | 2 | 强结果数 + 局限数 |
| 逐字证据页 | 8/11 内容页 | 4/5 | 材料句式与 claim 分类覆盖度 |

⇒ 同一套脚本在两个学科、两种汇报类型、两种量级上都产出契约完整、门全过、可复核的结果，
**没有**任何与题材绑定的硬编码分支（`templates/talk_config.json` 是配置而非代码）。

## 4. 泛化到哪里会失效（**如实写明**，每条都有实测支撑）

前两条**没有修**（属于设计取舍或已知边界），第三条**已修并附回归证据**，第四条是设计内的诚实降级。

### 4.1 未知 `report_type` 会被静默替换，且 `agenda` 页会消失 ❌ 未修

- **探针**：把 L2 的 `report_type` 改成 `workshop_retreat`（配置里没有的类型）。
- **实测**：`status=completed` · 15 页 · P-gates 8/8 全过；`talk_plan.json.narrative.report_type`
  被记成 **`group_meeting`**；块顺序变成 `title, motivation, background, method, results,
  conclusion_risk, qa` —— **`agenda` 页消失**；`uncertainty` **没有**任何相关条目（仍是 4 条通用项）。
- **失效率**：任何不在 `templates/talk_config.json` 三个类型内的汇报类型都会**静默**退回组会模板。
- **为什么不修**：退回默认模板是合理兜底（不该让未知类型直接失败），但"静默"是真实缺陷。
  **本包选择如实披露而不是悄悄改行为**。
- **给使用者的判据**：跑之前确认 `report_type` ∈ 三个已配置值；否则 `talk_plan.json.narrative.report_type`
  与 `case.json` 不一致，**以 `talk_plan.json` 的值为准**。要支持新类型请在 `templates/talk_config.json`
  加一条配置（纯 JSON，无需改代码）。

### 4.2 页数被硬钳制在 [6, 30]，极端冲突**不报不确定度** ❌ 未修

- **探针**：L2 改为 `duration_min=5, slide_count=40`（5 分钟讲 40 页，物理上不可行）。
- **实测**：产出 **30** 页（不是 40）；`result.json.slide_count=30`；
  `timing={"duration_min":5.0,"slide_target":30,"seconds_per_slide":10.0}`；
  `P3 detail="pages=30 target=30"` —— **P3 门通过了**，因为它比对的是"已钳制后的目标"；
  `uncertainty` 仍只有 4 条通用项，**没有**任何"页数被钳制"的说明。
- **根因（源码可查）**：`scripts/scaffold_plan.py` 里 `slide_target = max(6, min(30, int(slide_target)))`。
- **失效率**：`slide_count` 或时长推导结果落在 [6,30] 之外时，冻结页数被静默改写；
  5 分钟/30 页 ⇒ 10 秒每页，仍被报为 `completed`。
- **为什么不修**：钳制是防崩的合理设计，改它会影响所有已验收案例的页数。
- **给使用者的判据**：把 `slide_count` 当作"请求值"，**以 `result.json.slide_count` 为准**；
  两者不等说明被钳制了。

### 4.3 非中文材料：能抽到主张，但页面全部退化成概括页 ⚠️ **已修（Fix 7）**

- **探针**：把 L2 材料换成**纯英文**论文体（876 字符，含摘要/方法/结果/局限四小节）。
- **修前实测**：`status=completed` · P-gates 8/8 · **`derived_pages=11 / content_pages=11`**
  —— 11 个内容页**全部**是无逐字引文的概括页、`strength` 全为 `weak`，而 `status` 仍是 `completed`、
  `uncertainty` 里没有这一条。**典型的静默质量损失。**
- **根因（实测定位）**：`scripts/evidence.py` 能抽出英文 claim（实测 **6** 条，`strength=strong`），
  但 claim 分类器（`classify_claim`）是**中文研究动词驱动**的，英文句全部落成 `kind=general`，
  规划器无法把它们路由进 `method`/`results`/`limits` 块 ⇒ 只能生成 `derived` 概括页。
- **已修（Fix 7，纯增量）**：`scripts/main.py` 增加判据 ——「主张总数 ≥ 3」且「内容页 > 0」且
  「`derived_pages >= content_pages`」⇒ 写 `change_records`(step=`audit`) + `uncertainty`，
  `status → partial`。判据刻意收紧，**设计内的 D8 概括页（claims 本来就少）不会误伤**。
- **修后实测（同一探针）**：`status=partial`（退出码仍 `0`），`uncertainty` 由 4 条增至 **5** 条，
  新增条目原文：`材料中共抽出 6 条候选主张，但它们一条都没有被逐字引用到页面上
  （11 个内容页全部是概括页 derived=true）`；`change_records` 尾部出现第二个 `audit` 步。
- **回归确认（修复后重跑两案）**：L2 与 L3 仍为 `status=completed`（`derived_pages` 分别 3/11 与 1/5，
  均未触发该判据）⇒ 修复**没有**影响正常中文案例。
- **仍然失效的部分**：Fix 7 只把"静默"变成"可见"，**没有**让英文材料产出逐字证据页 ——
  分类词表仍是中文的。要用英文材料跑出完整证据链需扩展 `classify_claim` 词表（本版不做：
  那属于算法改动，超出"纯增量"边界）。

### 4.4 听众信息缺失 ✅ 设计内诚实降级

- **探针**：`case.json` 去掉 `audience`。
- **实测**：`expertise=familiar`、`background_ratio=0.18`、`audience.notes` 写明
  "听众信息缺失…可覆写"；`status` 不降级（符合 D7 的设计）。

### 4.5 未验证方向（明确声明**没有**实测数据）

以下**没有**跑过，因此不作任何断言（不是"应该没问题"，是"不知道"）：

1. **材料数 > 2、材料间数值互相矛盾** —— 只测了 2 个材料；跨材料矛盾数字由 `validate_result.py`
   给警告，但矛盾的取舍规则未测。
2. **超长材料**（如 5 万字符以上的整篇论文）—— 未测截断行为与耗时。
3. **非中非英材料**（日/俄等）—— 未测。
4. **真实有文本层 PDF** —— 两个合成案例**都不含 PDF**（PDF 路径由本包 `TEST.md` 的示例案例
   与 D2/D3 覆盖，但**本节不重复声称**）。
5. **同一案例重复三次**（平台是 3 案例 × 3 复跑）—— 本节只记录**单次**运行；
   双跑一致性由 `TEST.md` 的确定性探针另行覆盖，**不是**同一件事。
6. **模板适配模式下的两个新案例** —— 两案都走 `built-in-theme`（案例未提供模板）。

## 5. 执行（CP1–CP6）与异常处理

> **自定位**：`$SKILL_DIR` = 本包根目录（含 `SKILL.md`；平台安装后即 `/skills/weekly-skill`）。
> 所有脚本用 `os.path.dirname(__file__)` 自定位，**命令与当前 cwd 无关**。

| 检查点 | 做什么 | 出口条件 |
|-|-|-|
| **CP1 输入契约** | 读 `case.json`/`task.md`；解析材料与模板；环境预检。**另按 §6 核对三处输入开关** | 缺失项按 D 规则记录；`environment`/`change_records` 已写入 |
| **CP2 计划门** | 主流程一条命令；产出 `talk_plan.json` 并跑 P1–P8 写 `plan_gates.json` | 未全过 → D9 降级但**不中断** |
| **CP3 生成与校验门** | 模板适配（沿用母版/版式、丢弃自带页）或内置主题；确定性命名；图绑定或诚实占位；`verify_deck` | deck 页数 == 计划页数 |
| **CP4 渲染门** | PIL 模拟渲染封面/逐页/网格 + `preview_manifest.json` | 失败非致命（D12） |
| **CP5 审计与收口门** | `evidence_audit` 逐页逐字核验（**含 D21 证据路由停滞判定**）；`finalize_result` 组装 result.json + `self_check.json` | `contract_check.valid == true` |
| **CP6 多案例泛化复跑** | 两个合成案例各跑一遍，与 §2 的期望结构表逐项核；确认 §4 边界表现与描述一致 | 两案 `exit 0` 且期望结构全部对上 |

```bash
# CP2：主流程
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md --out /app/output

# CP6：两案泛化复跑
OUT="<包外空目录>"
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/cases/case-a-muon-defense/case.json" --out "$OUT/a"
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/cases/case-b-scrna-review/case.json"   --out "$OUT/b"
```

**退出码（`main.py`）**：`0` = 已产出通过 validate+contract 的 `result.json`
（其 `status` 说明 `completed` 还是 `partial`）；`1` = 没有可用的契约结果；`2` = 参数用法错误。

### 5.1 决策规则（D1–D23；全表含优先级裁决见 `references/failure-modes.md`）

| 规则 | 情形 | 处置（全部如实记录到 `uncertainty` / `change_records`） |
|-|-|-|
| D1 | 材料缺失 | `sources` 中 `kind=missing`；status 视影响降 `partial`；不编造内容 |
| D2 | 材料是 PDF 且无 pypdf / 解析失败 | 记 `parsed=false` + 原因；其余材料照常 |
| D3 | PDF 丢公式/符号；**或抽取到 0 个非空文本行** | 前者 quote 以抽取文本为准并注明代理方式；后者记未解析（不再冒充成功解析） |
| D4 | 论文缺图/图分辨率低/图损坏 | 页内**诚实占位框**；坏图跳过 |
| D5 | 无模板 / 模板路径失效 | 内置主题；`template_used`/`deck_mode` 注明 + `uncertainty` 记明 |
| D6 | 页数与时长推导冲突 | 以任务冻结页数为准（P3），`plan_gates` 记录说明 |
| D7 | 听众信息缺失 | `familiar` + 中等证据深度；`audience.notes` 注明可覆写（§4.4 实测） |
| D8 | 材料中某块无直接主张 | 用该块章节概括成页（`derived=true`、`weak`），framing 记 `change_records` |
| D9 | 计划门 P1–P8 未全过 | 记 errors；仍生成 honest 产物；`status→partial`；uncertainty 列出 |
| D10 | 导出/生成抛错、超时 | 非致命：仍写 `result.json`；中间产物尽早落盘；异常写 `change_records` |
| D11 | `verify_deck` 发现问题 | 记 entries；`status→partial`；不宣称"校验通过" |
| D12 | 预览失败/超时 | 非致命：仍写 `result.json`；`--skip-previews` 可跳过 |
| D13 | 证据审计引文未逐字命中 | 记录条目（derived 页按概括语）；可修则修，不能修如实保留 |
| D14 | 页面数字与源不一致 | `validate_result` 给警告；人工核对；合理换算需说明 |
| D15 | 缺 `python-pptx`（或连带 Pillow） | **不崩**：跳过 deck，`status→partial`，`editable_deck=null` + `deck_limitation`；命令仍返回 **0** |
| D16 | 模板自带示例页 | 保留母版/版式，**丢弃自带页**后按冻结计划重建；最终页数 == 冻结页数 |
| D17 | 材料为空 / 全部不可解析 | 只产出结构性页面；`status→partial` + uncertainty 明写；不据标签补造内容 |
| D18 | 模板存在但不是合法 OOXML | `try` 打开失败 → 记 `template_load_error` → **回落内置主题**；异常进 `change_records` + `uncertainty`；**不得**把整轮记成 `failed` |
| D19 | `task.md` 声明了 output_contract 却用不起来 | 解析器带回**具体原因**；写 `change_records`(step=`contract`) + `uncertainty`，`status→partial` |
| D20 | 契约声明了本包产不出的字段 | 按声明容器类型回落 `""`/`[]`/`{}`/`0`，**禁止 `null`**；`contract.applied` 记录已回显字段 |
| **D21** | **抽出主张却一条都没逐字上页** | 判据：主张 ≥3 且 内容页 >0 且 `derived_pages >= content_pages` ⇒ `change_records`(step=`audit`) + `uncertainty`，`status→partial`。**不**把概括页伪装成引文页（§4.3 实测） |
| **D22** | **未知 `report_type`** | 静默退回 `group_meeting`（`agenda` 消失）。**已知边界，未修**：以 `talk_plan.json.narrative.report_type` 为准（§4.1） |
| **D23** | **`slide_count` 落在 [6,30] 之外** | 硬钳制且不报不确定度。**已知边界，未修**：以 `result.json.slide_count` 为准（§4.2） |

### 5.2 三处留痕：降级必须"看得见"

`status` 只是结论；要能独立复核，原因必须在**三处**同时对得上：

| 落点 | 字段 | 复核方式 |
|-|-|-|
| ① 状态 | `status`（`completed`/`partial`/`failed`） | 读 `result.json.status`；`failed` 时再看 `error` |
| ② 声明 | `uncertainty[]`（每条 `{item, impact, mitigation}`） | **≥1 条**才算这条降级被声明过 |
| ③ 过程 | `change_records[]`（每条 `{at, step, action}`） | 按 `step` 过滤：`material`/`deck`/`deck-source`/`preview`/`plan-gate`/`contract`/`audit` |

> **统计口径提醒（本版实测后补）**：`status=completed` 只表示"契约五条件满足"，
> **不**表示"页面都有逐字引文"或"冻结页数被完全遵守"。后两者要分别看
> `evidence_audit.derived_pages` 与 `result.json.slide_count`（与案例输入比对）。

## 6. 输入：三处"输入决定行为"的开关（**先看这里，能省一轮返工**）

| 输入字段 | 决定什么 | 实测边界（本版重点，详见 §4） |
|-|-|-|
| `report_type` | 叙事块顺序与块集合（`templates/talk_config.json` 配置驱动）。`defense` 含 `agenda`+`innovation_limits`；`review` **结论先行**；`group_meeting` 无 `agenda` | ⚠️ 不在配置里的类型被**静默替换成 `group_meeting`**（§4.1） |
| `slide_count` / `duration_min` | 冻结页数（P3 门）与每页秒数 | ⚠️ 页数被**硬钳制在 [6, 30]** 且不报不确定度；以 `result.json.slide_count` 为准（§4.2） |
| `materials` 的语言/句式 | 能否产出**逐字引文页** | ⚠️ claim 分类词表**以中文研究动词为主**；纯英文材料会让内容页全部退化为概括页（§4.3） |
| `audience` | 背景铺垫比例与术语收录 | 缺失时 `familiar`/0.18 并写明可覆写（§4.4） |

### 6.1 输入（平台运行期）

| 路径 | 内容 |
|-|-|
| `/input/case.json` | `case_id`、`title`、`report_goal`、`audience`、`duration_min`、`slide_count`、`report_type`、`materials`（可为 `{path,role}`）、`template`/`start_deck`（可选）、`figure_files`（可选映射）、`output_contract`（可选字段声明） |
| `/input/task.md` | 任务说明；可能含 output_contract 声明（fenced JSON 或字段表） |
| 材料目录 | `case.json` 中列出的文本/PDF（缺省取 `<case 目录>/materials`）：`.md/.txt/.pdf` 与图片附件 |

**必须实际读取文件内容**，不得根据标签/文件名预设内容。`main.py` 自动发现材料目录中的 md/txt/pdf/图片。

### 6.2 输出（`--out`，平台运行期即 `/app/output`）

```
result.json            # 唯一评分产物：契约字段 + 主结果 + 证据定位 + status/sources/
                       #   uncertainty/change_records/environment + audit{plan_gates,evidence,deck,gates}
talk_plan.json         # 页级计划（可编辑中间产物）
plan_gates.json        # 计划契约门 P1–P8 结果（assets/plan.schema.json 驱动）
evidence_map.json      # 源文件 → {用到它的页, 图表引用} 反向映射
evidence_audit.json    # 逐页逐字引文审计
deck_audit.json        # deck 机器校验（打开/页数/备注/claim 元素/OPC/规范化 sha）
editable_deck.pptx     # 可编辑演示文件 ← 运行期产物（二进制），不进提交资源
previews/              # cover_preview.png · slide_0NN.png · preview_grid.png · preview_manifest.json
self_check.json        # validate_result + check_contract + 门 + 确定性探针
```

`result.json` 里的路径一律是**可移植形式**：本机绝对路径写盘前改写成相对案例目录的路径，
POSIX 运行期路径（`/input/...`、`/app/output/...`）原样保留。字段契约全文见
[`references/OUTPUT_CONTRACT.md`](references/OUTPUT_CONTRACT.md)（该文件的字段块在本版中**逐字未改**）。

## 7. 脚本与资源清单

| 文件 | 角色 | 作用 |
|-|-|-|
| `scripts/main.py` | build 编排 | 唯一入口：CP1–CP5 门控（环境预检→材料解析→计划→校验→deck→预览→审计→result→自检） |
| `scripts/evidence.py` | extract | 材料加载（md/txt/PDF-pypdf）与主张/证据锚点抽取（**claim 分类词表以中文为主**，见 §4.3） |
| `scripts/scaffold_plan.py` | build | 页级规划：听众→背景比例、叙事顺序、一页一主张、问答预演、图绑定（**含 §4.2 的页数钳制**） |
| `scripts/validate_plan.py` | verify | 计划契约门 P1–P8（schema 驱动）；独立 CLI |
| `scripts/evidence_audit.py` | verify | 逐页逐字引文审计 + 定位/数字/图绑定；独立 CLI |
| `scripts/deck_builder.py` | render | python-pptx 生成/模板适配可编辑 `.pptx`（母版复用、自带页丢弃、确定性命名、讲稿备注、图占位） |
| `scripts/verify_deck.py` | verify | deck 打开/页数/备注/命名/OPC/规范化 sha 校验；独立 CLI |
| `scripts/render.py` | render | PIL 模拟预览（封面/逐页/网格 + manifest + 字体探测） |
| `scripts/validate_result.py` | verify | result.json 结构+文件+数字可对源校验；独立 CLI |
| `scripts/check_contract.py` | verify | output_contract 字段齐全性校验；独立 CLI |
| `scripts/finalize_result.py` | verify/build | result 信封组装：契约回显 + 审计嵌入 + environment + self_check + 确定性探针 |
| `scripts/selftest.py` | verify | 全链路复核（G1–G10）+ 包约束审计；独立 CLI |
| `scripts/common.py` | shared | 自定位、JSON IO、契约工具、确定性投影 hash、路径净化、输入解析 |
| `scripts/make_synthetic_inputs.py` | assets | **运行时生成示例二进制输入**：`dataset_card.pdf`、`fig2.png`、`--template` 时的 `synthetic_template.pptx` |
| `references/CASE-SET.md` | docs | **多案例泛化题集**（本版新增）：题集总览 / 逐案期望结构与实测 / 实测对照 / **4 条失效边界** / 6 条未验证方向 / 复用方式与难度分层 |
| `references/OUTPUT_CONTRACT.md` | docs | result.json 契约（字段块逐字保留） |
| `references/RUBRIC_MAP.md` | docs | 五维评分（40/25/15/10/10）→ 本包文件与机制逐条对照（含"泛化与适用范围"落点） |
| `references/failure-modes.md` | docs | 失败模式处置表（F1–F26 + 决策规则 D1–D23 + 状态一致性 + **泛化边界实测对照**） |
| `references/plan-contract.md` · `references/quality-gates.md` · `references/deck-rules.md` · `references/evidence-audit.md` | docs | 计划契约 / 质量门 / 页面规则 / 证据审计规范 |
| `templates/talk_config.json` | assets | 可编辑叙事规则：每类型页权重/顺序/问答模板 + deck_rules（**换题材不改代码的关键**） |
| `templates/narrative_template.md` · `templates/slide-checklist-template.md` | assets | 叙事模板人类可读版 + 上台前逐页核对清单 |
| `assets/plan.schema.json` · `assets/result.template.json` | assets | 计划契约模式（P1–P8 驱动源）+ result 信封示例 |
| `examples/cases/case-a-muon-defense/` | demo | 合成案例 L2（实验物理 · 答辩 · 25 min/15 页 · 不带图片文件） |
| `examples/cases/case-b-scrna-review/` | demo | 合成案例 L3（计算生物学 · 评审 · 12 min/8 页 · 结论先行 + 矛盾指标同页） |
| `COMPARE.md` · `examples/README.md` · `examples/EXPECTED-OUTPUT.md` · `examples/output/*.example.json` | docs/demo | 对照方案 / 示例说明 / 应产出清单 / 示例运行产物 |

### 7.1 题集能被别人怎么复用

- **可整块拿走**：`examples/cases/` 下每个案例是自包含的（`case.json` + `task.md` + `materials/`），
  换掉 `materials/` 与 `case.json` 的描述字段就是一个新案例，**不需要改任何代码**。
- **可作对照基线**：§2 的期望结构表刻意写成**可判定项**（页数、块顺序、页数区间、问答条数、审计数值），
  可直接当验收脚本的判据。
- **可作反例使用**：§4 的三个探针是**故意造出来的失败输入**，用来验证"降级是否可见"，
  比正例更有判别力；它们不随包提交，但重建步骤已写清（改 `case.json` 的一个字段）。

## 8. 自查清单（收尾前逐项确认）

- [ ] `result.json` 存在；`case_id` 与输入一致；`status` ∈ {completed, partial, failed}
- [ ] `output_contract` 声明字段全部出现在顶层（`self_check.json → contract_check.valid == true`；四形态回显、无 null）
- [ ] **§6 三处开关已核**：`talk_plan.json.narrative.report_type` 与案例一致；
      `result.json.slide_count` 与案例冻结页数一致；材料语言是否在 claim 分类覆盖内
      （看 `evidence_audit.derived_pages` 是否等于 `content_pages`）
- [ ] `plan_gates.json` 与 `result.audit.plan_gates` 存在；P1–P8 未全过时 uncertainty 有对应条目
- [ ] 每一页（除封面/目录/问答备用页）都有 `evidence[0].locator` + `quote` 原句
- [ ] `evidence_audit.json` 逐页核对过；所有 `evidence.source_file` 都能在 `sources[]` 中找到
- [ ] `editable_deck.pptx` 存在且能被打开；每页有讲稿备注；页数 == 计划
- [ ] 预览 PNG 存在且每张带「PIL 模拟预览」水印；`preview_manifest.json` 已说明限制与字体探测结果
- [ ] 数字可信：页面上的数字在源材料中可定位（warnings 已审查）
- [ ] 没有预置正式答案：`examples/` 仅为合成的接口示例（`case_id` 形如 `example-*`/`synth-*`）
- [ ] 依赖缺失/材料异常时**如实降级**：`status=partial` + `uncertainty` + `change_records`
- [ ] **两个合成案例都跑过**，且与 §2 的期望结构表逐项对得上（页数/块顺序/页数区间/问答条数/审计数值）
- [ ] **已知边界未被误当成功**：`narrative.report_type` 与 `case.json` 一致；
      `result.json.slide_count` 与案例冻结页数一致；§4.1/§4.2 的两条未修边界已如实记入交付说明
- [ ] **资源形态硬门**：只含七种扩展名；≤50 个 UTF-8 文本文件；单文件 ≤500KB；合计 ≤2MB；
      无符号链接；无 `__pycache__`/`.pyc`；**无本机绝对路径残留**
- [ ] 包内**不存在任何**该七种扩展名之外的文件；二进制示例输入由 `make_synthetic_inputs.py` 运行时生成

## 9. 资源形态：为什么包内没有二进制，以及逐类处置

题面只允许 UTF-8 文本资源作为 Skill 资源（runtime artifacts 不在此列），因此本包**只用文本**表达规则、
脚本与示例；所有二进制一律改由脚本现场生成：

| 原本常见的二进制资源 | 本包的做法 |
|-|-|
| 内置模板 `*.pptx` | **不随包**：`deck_builder._new_deck()` 用 python-pptx 现场构建 16:9 母版/主题；案例自带模板时直接读取平台提供的模板 |
| 示例图 `*.png` | **不随包**：`make_synthetic_inputs.py` 用 Pillow 画纯几何示意图（带 `SYNTHETIC` 标注，不含测量值） |
| 示例 PDF | **不随包**：同一脚本手工构造最小 PDF（零第三方依赖、字节确定、pypdf 可解析） |
| 示例输出 `*.pptx/*.png/*.svg` | **不随包**：改为 `examples/EXPECTED-OUTPUT.md` 用**文字**列出应产出文件清单与实测数量 |
| 示例输出 `*.json` | **随包但净化**：只保留 `result.example.json` / `self_check.example.json`，路径全部为相对形式 |
| 字体 `*.ttf/*.otf` | **不随包**：运行时按候选路径探测系统字体（`/usr/share/fonts`、`/System/Library/Fonts`、`C:/Windows/Fonts`），结果记入 `result.json.environment.cjk_font` 与 `preview_manifest.json`；找不到则用 Pillow 内置位图字体并在 manifest 记明 |
| `scripts/__pycache__`、`*.pyc` | **不随包**：提交前删除（`selftest.py --package-check` 的 G10 会检查） |

## 10. 平台约束（Runtime contract 要点）

- 平台把本 Skill 安装到 `/skills/weekly-skill` 后在**固定 3 个案例 × 3 次复跑**上运行；
- 输入 `/input/case.json` + `task.md`；在 `/app/work` 干中间活；最终产物 `result.json` +
  可编辑源 + 渲染预览放 `/app/output`；`result.json` 必须含 output_contract 全部字段与 `case_id`；
- **提交资源**：≤50 个 UTF-8 文本文件、单文件 ≤500KB、合计 ≤2MB、无符号链接（§9 逐条处置）；
- **运行期产物可以是二进制**，且不因 `result.json` 的最终有效性而被丢弃；
- 诚实记录 `status/sources/uncertainty/change_records`；不编造缺失软件状态与科学数据；
- 执行预算：64 个模型请求 / 900 秒 / 每响应 16384 token（含推理）；尽早保存部分成果，渐进改进。
