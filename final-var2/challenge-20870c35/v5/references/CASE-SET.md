# CASE-SET.md — 多案例泛化题集（v5）

> **本文件里的每一个数字都来自真跑**，不是在别的案例上测完再推算的。
> 运行方式见 §0；两个合成案例的输入在 `examples/cases/`；边界探针（§4）的输入是临时改造的
> 副本，**不随包提交**（它们的作用是"如实定位泛化到哪里失效"，不是提供更多示例）。
> 所有数值均为**空构造的合成数据**，不代表任何真实研究，不得被引用为科学结论。

## 0. 复现命令

```bash
SKILL_DIR="<本包根目录>"
OUT="<包外空目录>"
for c in case-a-muon-defense case-b-scrna-review; do
  python "$SKILL_DIR/scripts/main.py" \
    --case "$SKILL_DIR/examples/cases/$c/case.json" \
    --task "$SKILL_DIR/examples/cases/$c/task.md" \
    --out "$OUT/$c"
done
```

采集环境：Python 3.13.9 · python-pptx 1.0.2 · Pillow 12.3.0 · pypdf 6.14.2 · win32
（**包外目录**运行；包内跑会生成 `__pycache__` 而使提交包不合规）。

## 1. 题集总览

| 案例 | 题材 | 汇报类型 | 听众 | 时长 | 冻结页数 | 难度层 | 主要考察点 |
|-|-|-|-|-|-|-|-|
| `case-a-muon-defense` | 凝聚态**实验物理**（μSR 内场分布反演） | `defense`（学位答辩） | 答辩委员会（expert） | 25 min | 15 | **L2 中** | 方法页/结果页的数值证据链；**三条局限必须靠前**；图表引用存在但图片文件缺席 → 诚实占位 |
| `case-b-scrna-review` | 计算**生物学**（单细胞计数去噪） | `review`（评审答辩） | 评审专家组（expert） | 12 min | 8 | **L3 偏难** | **结论先行**的块顺序；**两个互相矛盾的指标必须同时上页**；短时长下的取舍压缩 |

> **为什么是这两个题材**：它们与 `examples/` 里的最小示例（NLP 跨语言句子对齐）在
> **学科、汇报类型、时长量级、页数量级**四个维度上都不同 —— 这样才能检验"换题材还成不成立"，
> 而不是"同样的东西再跑一遍"。两个案例都**不提供图片文件**，用来走通"引用存在、文件缺席"的
> 诚实占位路径（`deck_mode` 与 `preview_manifest` 会记明）。

## 2. 逐案：输入 / 期望产出结构 / 可接受区间 / 实测结果

### 2.1 `case-a-muon-defense`

**输入**：`case.json`（`report_type=defense`、`audience` 为答辩委员会描述、`duration_min=25`、
`slide_count=15`、`materials` 两项）+ `task.md`（含 `output_contract` 声明块）+
`materials/muon_extract.md`（1165 字符，5 个章节）+ `materials/figures.md`（438 字符）。

**期望产出结构**（可判定的清单）：

| 项 | 期望 | 可接受区间 |
|-|-|-|
| 页数 | == 冻结页数 15 | 恰好 15（P3 门） |
| 块顺序 | 答辩叙事，含 `agenda` 与 `innovation_limits`（"局限/创新边界"后置块） | 顺序中 `motivation` 在 `method` 之前、`innovation_limits` 在 `results` 之后 |
| 结果页数 | 3–5 页 | 实测 4（页 7–10） |
| 局限/边界块页数 | ≥ 2 页 | 实测 2（页 11–12） |
| `qa` 备用页 | ≥ 1 页 | 实测 2 页（页 14–15） |
| 问答条数 | ≥ 2 条（每条局限 + 每条 strong 结果） | 实测 3 条 |
| 图表引用 | 与源材料一致，不许臆造 | 实测 `Fig. 1` 绑定到页 7，页内为**诚实占位**（无图片文件） |
| `status` | `completed` | 实测 `completed` |
| `result.json` 顶层键 | 契约 16 字段齐全 | 实测 20 键（契约字段 + `audit`/`environment`/`generated_*`） |
| 证据审计 | `valid=true`、`errors=0` | 实测 `11/11 ok`、`derived=3` |

**实测（真跑一次）**：

```
[plan] 15 pages, narrative=defense, audience=expert, P-gates valid=True
[deck] 15 slides, mode=built-in-theme, verify valid=True
[preview] wrote 14 preview files (PIL simulation)
[done] status=completed deck_ok=True preview_ok=True plan_gates=True evidence_audit=True
       validate_valid=True contract_valid=True
EXIT=0
```

- 叙事顺序（实测）：`title, agenda, motivation, background, method, results, innovation_limits, conclusion, qa`
- `main_line` 计数（实测）：`research_question=1, method=2, results=4, limitations=2, conclusion=1`
- 逐页强度（实测）：`strong` ×6 · `medium` ×1 · `weak`(derived) ×3 · 结构页 ×5
- `plan_gates`（实测）：`gates=8 ok=8`，`P3 detail = "pages=15 target=15"`
- `evidence_audit`（实测）：`content_pages=11, ok_pages=11, errors=0, derived_pages=3`
- 产物（实测）：`editable_deck.pptx`（15 页，verify 通过）· `previews/` 14 个文件 · `uncertainty` 4 条

### 2.2 `case-b-scrna-review`

**输入**：`case.json`（`report_type=review`、`duration_min=12`、`slide_count=8`）+
`task.md` + `materials/scrna_extract.md`（1077 字符）+ `materials/figures.md`（408 字符）。

**期望产出结构**：

| 项 | 期望 | 可接受区间 |
|-|-|-|
| 页数 | == 冻结页数 8 | 恰好 8（P3 门） |
| 块顺序 | **结论先行**：`conclusion` 出现在 `method`/`results` **之前** | 实测顺序中 `conclusion` 位于第 3 页 |
| 两个矛盾指标 | 同时出现在页面上（10.9% 与 0.4%） | 两者都必须能在 `pages[].claim` 或 `evidence[].quote` 里找到 |
| 结果页数 | 2–3 页 | 实测 2（页 5–6） |
| `qa` 备用页 | 1 页 | 实测 1 页（页 8） |
| 问答条数 | ≥ 2 条 | 实测 2 条 |
| `status` | `completed` | 实测 `completed` |
| 证据审计 | `valid=true`、`errors=0` | 实测 `5/5 ok`、`derived=1` |

**实测（真跑一次）**：

```
[plan] 8 pages, narrative=review, audience=expert, P-gates valid=True
[deck] 8 slides, mode=built-in-theme, verify valid=True
[preview] wrote 8 preview files (PIL simulation)
[done] status=completed ... validate_valid=True contract_valid=True
EXIT=0
```

- 叙事顺序（实测）：`title, agenda, conclusion, method, results, innovation_limits, qa`
  ⇒ **结论先行成立**：`conclusion` 在 `method`/`results` 之前，与 `templates/talk_config.json`
  里 `review` 的块顺序一致。
- `main_line` 计数（实测）：`research_question=0, method=1, results=2, limitations=1, conclusion=1`
- 图表引用（实测）：`Table 1` 绑定页 4、`Fig. 1` 绑定页 6，均为诚实占位
- `plan_gates`（实测）：`gates=8 ok=8`，`P3 detail = "pages=8 target=8"`
- `evidence_audit`（实测）：`content_pages=5, ok_pages=5, errors=0, derived_pages=1`
- 产物（实测）：`editable_deck.pptx`（8 页）· `previews/` 8 个文件 · `uncertainty` 4 条

> **该案暴露的结构性事实**：`main_line.research_question = 0`。原因是 `review` 叙事里
> **没有 `motivation` 块**（结论先行的代价），而 `main_line.research_question` 只由
> `motivation` 块填充。⇒ 读 `main_line` 的下游消费者必须允许该键为空数组，
> 不能假设四种汇报类型都有研究问题条。

## 3. 两案对比：换题材/换类型真正改变了什么（实测，非推断）

| 维度 | case A（物理 · 答辩） | case B（生物 · 评审） | 变化来自 |
|-|-|-|-|
| 块顺序 | `...motivation, background, method, results, innovation_limits, conclusion...` | `...conclusion, method, results, innovation_limits...` | `report_type` 驱动的叙事配置 |
| 页数 | 15 | 8 | 案例冻结页数（P3 门） |
| `agenda` 页 | 有（页 2） | 有（页 2） | 配置 |
| `motivation` 页 | 有（页 3） | **无** | 评审类型的块集合 |
| `background` 页 | 有（页 4，derived/weak） | **无** | 同上 |
| 问答条数 | 3 | 2 | 强结果数 + 局限数 |
| 逐字证据页 | 8/11 内容页有逐字引文 | 4/5 | 材料句式与 claim 分类覆盖度 |

⇒ 同一套脚本在**两个学科、两种汇报类型、两种量级**上都产出了契约完整、门全过、可复核的结果，
**没有**依赖任何与题材绑定的硬编码分支（`templates/talk_config.json` 是配置而非代码）。

## 4. 泛化到哪里会失效（**如实写明**，每条都有实测支撑）

下面四条都是**真跑出来的**，不是推测。前三条**没有修**（属于设计取舍或已知边界），
第四条**已修并给出回归证据**。

### 4.1 未知 `report_type` 会被静默替换，且 `agenda` 页会消失 ❌ 未修（已知边界）

- **探针**：把 case A 的 `report_type` 改成 `workshop_retreat`（本包配置里没有的类型）。
- **实测**：`status=completed` · 15 页 · P-gates 8/8 全过；`talk_plan.json.narrative.report_type`
  被记成 **`group_meeting`**（不是输入的 `workshop_retreat`），块顺序变成
  `title, motivation, background, method, results, conclusion_risk, qa` ——
  **`agenda` 页消失**（组会模板不含目录页），且 `uncertainty` **没有**任何相关条目（仍是 4 条通用项）。
- **失效率**：任何不在 `templates/talk_config.json` 三个类型（`group_meeting`/`defense`/`review`）
  内的汇报类型，都会**静默**退回组会模板。
- **为什么没修**：退回默认模板本身是合理的兜底（不该让未知类型直接失败），
  但"静默"这一点是真实缺陷。**本包选择如实披露而不是悄悄改行为**：如果要用未知类型，
  请先在 `templates/talk_config.json` 里加一条配置（配置是纯 JSON，不需要改代码）。
- **给使用者的判据**：跑之前确认 `report_type` ∈ 三个已配置值；否则 `talk_plan.json.narrative.report_type`
  会与 `case.json` 不一致，**以 `talk_plan.json` 的值为准**。

### 4.2 页数被硬钳制在 [6, 30]，极端冲突**不报不确定度** ❌ 未修（已知边界）

- **探针**：case A 改为 `duration_min=5, slide_count=40`（5 分钟讲 40 页，物理上不可行）。
- **实测**：产出 **30** 页（不是 40）；`result.json.slide_count=30`；`timing={"duration_min":5.0,
  "slide_target":30,"seconds_per_slide":10.0}`；`P3 detail="pages=30 target=30"` —— 
  **P3 门通过了**，因为它比对的是"已钳制后的目标"，而不是输入里的 40；
  `uncertainty` 仍只有 4 条通用项，**没有**任何"页数被钳制"的说明。
- **根因（源码可查）**：`scripts/scaffold_plan.py` 里 `slide_target = max(6, min(30, int(slide_target)))`。
- **失效率**：`slide_count` 或时长推导结果落在 [6,30] 之外时，冻结页数被静默改写；
  5 分钟/30 页 ⇒ 10 秒每页，仍被报为 `completed`。
- **为什么没修**：钳制是防崩的合理设计，改它会影响所有已验收案例的页数。
  **本条的正确用法**：把 `slide_count` 当作"请求值"，**以下游 `result.json.slide_count` 为准**；
  若两者不等，说明被钳制了（可自行对比）。

### 4.3 非中文材料：能抽到主张，但页面全部退化成概括页 ⚠️ **已修（Fix 7）**，并给出回归证据

- **探针**：把 case A 的材料换成**纯英文**论文体（876 字符，含摘要/方法/结果/局限四个小节）。
- **修前实测**：`status=completed` · P-gates 8/8 全过 · **`derived_pages=11 / content_pages=11`**
  —— 11 个内容页**全部**是无逐字引文的概括页，`strength` 全部 `weak`，
  而 `status` 仍是 `completed`、`uncertainty` 里没有这一条。**典型的静默质量损失。**
- **根因（实测定位）**：`scripts/evidence.py` 能抽出英文 claim（实测 **6** 条，`strength=strong`），
  但 claim 分类器（`classify_claim`）是**中文研究动词驱动**的，英文句全部落成 `kind=general`，
  规划器无法把它们路由进 `method`/`results`/`limits` 块 ⇒ 只能生成 `derived` 概括页。
- **已修（Fix 7，纯增量）**：`scripts/main.py` 增加判据 ——
  「抽到的主张 ≥ 3 条」且「内容页 > 0」且「`derived_pages >= content_pages`」⇒
  写 `change_records`(step=`audit`) + `uncertainty`，`status → partial`。
  判据刻意收紧，**设计内的 D8 概括页（claims 本来就少）不会误伤**。
- **修后实测（同一探针）**：`status=partial`（退出码仍 `0`），`uncertainty` 由 4 条增至 **5** 条，
  新增条目原文：`材料中共抽出 6 条候选主张，但它们一条都没有被逐字引用到页面上
  （11 个内容页全部是概括页 derived=true）`；`change_records` 尾部出现第二个 `audit` 步。
- **回归确认（同一次修复后重跑两案）**：case A 与 case B 仍为 `status=completed`
  （`derived_pages` 分别为 3/11 与 1/5，均未触发该判据）⇒ 修复**没有**影响正常中文案例。
- **仍然失效的部分**：Fix 7 只把"静默"变成"可见"，**没有**让英文材料产出逐字证据页 ——
  claim 分类词表仍是中文的。要用英文材料跑出完整证据链，需要扩展 `classify_claim` 的词表
  （本版不做：那属于算法改动，超出"纯增量"边界）。

### 4.4 未验证的方向（明确声明**没有**实测数据）

以下方向本版**没有**跑过，因此不作任何断言（不是"应该没问题"，是"不知道"）：

1. **超过两个材料文件、材料间数值互相矛盾** —— 只测了 2 个材料；跨材料的矛盾数字由
   `validate_result.py` 给警告，但矛盾的取舍规则未测。
2. **超长材料**（比如 5 万字符以上的整篇论文）—— 未测截断行为与耗时。
3. **非中非英材料**（日/俄等）—— 未测。
4. **真实 PDF**（有文本层）—— 两个合成案例**都不含 PDF**；PDF 路径由 v4 的
   由**同一作者的另一份包（v4 失败注入版）的失败注入矩阵**覆盖（含"无文本层 PDF"的注入实测），
   但那**不是本包的内容**，本文件不重复声称、也不引用其路径。
5. **同一案例重复三次**（平台是 3 案例 × 3 复跑）—— 本文件只记录**单次**运行；
   双跑一致性由 `TEST.md` 的确定性探针另行覆盖，**不是**同一件事。
6. **模板适配模式下的两个新案例** —— 两案都是 `mode=built-in-theme`（案例未提供模板）；
   模板路径由 case A/B 之外的既有 `TEST.md` T5 与 v4 的 `F06`/`F07`/`F08` 覆盖。

## 5. 这套题集能被别人怎么复用

- **可整块拿走**：`examples/cases/` 下每个案例是自包含的（`case.json` + `task.md` + `materials/`），
  换掉 `materials/` 与 `case.json` 的描述字段就是一个新案例，**不需要改任何代码**。
- **可作对照基线**：§2 的"期望产出结构"表刻意写成**可判定项**（页数、块顺序、页数区间、
  问答条数、审计数值），可以直接当验收脚本的判据。
- **可作反例使用**：§4.1–4.3 三个探针是**故意造出来的失败输入**，用来验证"降级是否可见"，
  比正例更有判别力；它们不随包提交，但重建步骤已在文中写清（改 `case.json` 的一个字段）。
- **难度分层**：L1 = `examples/`（NLP，20 min/12 页，有 PDF）→ L2 = case A（物理，25 min/15 页，
  无图片）→ L3 = case B（生物，12 min/8 页，结论先行 + 矛盾指标）。L3 不是"更长的材料"，
  而是"约束彼此冲突"，因此更难。
