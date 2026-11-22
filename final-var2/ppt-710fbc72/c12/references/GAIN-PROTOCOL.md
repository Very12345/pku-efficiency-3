# GAIN-PROTOCOL — 与"不加载 Skill 的基础 Agent"的公平对照协议

本文件回答题面"使用增益 25 分"要的那件事：**在相同输入材料、相同模板、相同导出
环境下，加载本 Skill 相比基础 Agent，交付质量与效率到底改了什么，以及这个结论
怎么被第三方独立复跑推翻。**

组织方的正式白板与三案例对照由平台执行；本文给的是**可复跑的本地等效对照协议 +
作者真实跑过的记录**。两件事分开写清楚：§2–§5 是协议（任何人可照做），§6 是本次
实测数据。

---

## 1. 为什么需要协议

"我们的 Skill 更好"这句话本身不可评分 —— 因为它不可证伪。可评分的形态必须是：

1. **两个臂的定义可复述**（谁做了什么、没做什么）；
2. **公平性约束可核查**（同输入、同模板、同版本、同环境、同预算）；
3. **指标口径可计算**（给定两份产物，任何人算出同一个数）；
4. **原始数字与差异项都留在记录里**（包括对自方不利的差异）。

本协议的每条指标都写成"分子/分母 + 测量动作"，避免出现"质量明显提升"这类无法
复算的措辞。

## 2. 对照臂定义（A 臂 / B 臂）

### A 臂 —— 基础 Agent（不加载本 Skill）

忠实实现"一个普通 Agent 拿到论文 + 要求出 PPT 时最自然的几步"：

| 步骤 | A 臂的做法 |
|-|-|
| 1 | 打开**同一份** 16:9 模板 pptx（python-pptx 打开，沿用其母版/版式） |
| 2 | 读 `case.json`，把 `research_question/methods/results/discussion/limitations/conclusion` 各环节的 `text` **整段拼起来**，塞进"Title and Content"版式的正文占位符；超长就按字数上限分页 |
| 3 | `figures` 里的图用 `add_picture` **按原始尺寸**直接放（不做 contain-fit、不写图号/来源图注） |
| 4 | 不写页脚/页码、不写 speaker notes、不做版式规划、不记录来源定位 |
| 5 | **不产出 `result.json`**（没有契约概念），也不产出预览 |

A 臂不是"故意做坏"：它产出的是**能打开、能讲的 PPT**，只是没有可核验的中间判据。

### B 臂 —— 加载本 Skill

```bash
python "$SKILL_DIR/scripts/main.py" --case <case.json> --task <task.md> --out <out>
```

两阶段全流程：抽取（带 `文件:行`）→ 确定性页计划 → 阶段一适配方案（模板审计 +
页→版式分配 + 批量规则 + 图表计划）→ 阶段二按方案建册 → 预览 → 审计 →
`result.json` → CP3 契约门 G1–G8。

### 测量臂 —— 只看产物，不看自述

第三方测量脚本（**不随包分发**，属对照设施）只读产物，**不 import 本 Skill 的任何
模块**，也**不读 result.json 里的自述文字**来判断好坏：

| 被测对象 | 测量动作 |
|-|-|
| deck pptx | python-pptx 打开：页数、每页版式名、文本框字符数、形状里 `PICTURE` 的宽高比、原生 table 数、notes 文本、底部 12% 区域内的文本框数 |
| 来源定位 | 在所有文本里正则匹配 `文件:行` 形态（如 `material.md:15`），记页数与命中总数 |
| 页脚页码 | 底部区域存在非空文本框，或全册文本里匹配 `第 N 页` / `Page N` / `N/M` |
| PNG | 只读文件头：签名 + IHDR 宽高（不解析像素） |
| result.json | 顶层键数、`slide_evidence` 条数与证据行数、`template_audit.layout_used` 条数、`adopt_plan_applied`、`adopt_plan_deviations` 条数、审计检查条数与 fail/warn 数、`contract_gates` 通过数、**顶层 null 值个数** |

## 3. 公平性约束

| # | 约束 | 本协议的落实 | 怎么核查 |
|-|-|-|-|
| C1 | **同输入** | 两臂用同一份 `case.json` / `task.md` / 同一批图（由 `make_synthetic_inputs.py` 现场合成一次，两臂共用） | 两臂命令里指向同一路径；图的 sha256 相同 |
| C2 | **同模板** | `case.json` 的 `template` 字段指向同一份 `template.pptx`（由 `make_template.py` 生成）；A 臂从同一字段解析模板，B 臂也从中解析 | B 臂 `template_audit.opened_from` 应为 `case_template` 且 `template_fallback_used=false`；两臂画布 EMU 与所用版式名集合应完全相同 |
| C3 | **同版本** | 记录 Skill 版本（`scripts/common.py` 的 `SKILL_VERSION`）与 A 臂脚本的 sha256 | 报告里附两个 sha256 |
| C4 | **同环境** | 同一台机器、同一次会话、同一 Python 与 python-pptx / Pillow 版本 | `result.json.tool_versions` |
| C5 | **同预算** | 两臂同一个子进程调用方式（`time.perf_counter()` 包住整个子进程），**不限制**任一臂的迭代次数（比较的是"各自完成一册"的代价） | 报告里给 3 次原始值 |
| C6 | **不预置答案** | 两臂都不使用任何"预制结果"；B 臂的示例产物标为示例 | `examples/README.md` 与 `examples/output/_LABEL_example.txt` |

> C2 是这份协议最容易被含糊过去的一条。很多"增益对照"其实是拿"我们用了指定模板"
> 对比"他们用了默认模板" —— 那不是流程增益，是输入差异。本协议强制两臂同模板，
> 并把版式名集合与画布尺寸作为**核查证据**写进记录。

## 4. 可测指标定义

### 4.1 质量指标 Q1–Q8

| # | 指标 | 计算式 | 目标 | 测量动作 |
|-|-|-|-|-|
| **Q1** | 页数达成度 | `实际页数 / case.slide_count` | 1.0 | 数 pptx 页数 |
| **Q2** | 逐页讲稿覆盖率 | `有非空 notes 的页数 / 总页数` | 1.0 | 读每页 `notes_slide.notes_text_frame.text` |
| **Q3** | 来源可追溯率 | `带 \`文件:行\` 定位串的页数 / 总页数`；另记定位串总数 | 越高越好 | 全文本正则匹配 |
| **Q4** | 页脚/页码一致性 | `底部带页脚或页码的页数 / 总页数`（口径：封面通常无页脚，故满分通常为 `(N-1)/N`） | ≥ (N-1)/N | 底部 12% 区域文本框 + 页码正则 |
| **Q5** | 图表放置完整率 | `实际嵌入图数 / case.figures 条数`；并核对**嵌入图宽高比 == 源图宽高比**（容差 1e-3） | 1.0 且比例相符 | python-pptx 读 `shape.width/height`；源图读 PNG IHDR |
| **Q6** | 模板继承可查性 | `result.json.template_audit.layout_used 条数 / 总页数` | 1.0 | 读 JSON |
| **Q7** | 方案↔执行一致性 | `adopt_plan_applied / 计划页数`，且 `adopt_plan_deviations` 逐条可读 | 1.0 且偏差可读 | 读 JSON |
| **Q8** | 契约完整率 | `check_contract.py 的 G1..G8 通过数 / 8`，且 `result.json` 顶层 null 值个数 = 0 | 8/8 且 0 | 跑 `check_contract.py` + 数 null |

### 4.2 效率指标 E1–E4

| # | 指标 | 定义 | 说明 |
|-|-|-|-|
| **E1** | 单册墙钟耗时 | `time.perf_counter()` 包住整个子进程，3 次取中位数 | **绝对值依赖机器**，跨机对比只看两臂**比值** |
| **E2** | 返工步数 | 输入变更后需要重跑的**阶段数** | 内容变 / 模板变分别记 |
| **E3** | 重跑字节一致性 | `同输入重跑后逐字节相同的产物数 / 总产物数`，并列出差异项及原因 | 同输出目录连跑两次 |
| **E4** | 人工核对工作量 | 需要人眼复查的记录条数 = 证据行数 + 审计检查行数 | 这条**对 B 臂不利**（B 臂要看的记录更多），如实计入 |

> E4 故意反向计分说明：B 臂的"更多记录"是**用人工核对换可核验性**，不是纯收益。
> 把它写进协议是为了让对照不变成单方面吹捧。

## 5. 操作步骤（可被第三方逐步复跑）

`$SKILL_DIR` = 本包根目录（平台装到 `/skills/weekly-skill`）。
**测量脚本必须在 cwd ≠ `$SKILL_DIR` 的情况下运行** —— 在包内跑任何脚本都会生成
`scripts/__pycache__`，触发合规硬门失败（`.pyc` 属平台拒绝的资源类型）。

```bash
SKILL_DIR=<本包根目录>
RUN=<任意可写目录>; mkdir -p "$RUN"
cd "$RUN"

# ── 0. 准备：合成占位图 + 生成一份共享模板，并让案例指向它 ──────────────
cp -r "$SKILL_DIR/examples" "$RUN/input"
python "$SKILL_DIR/scripts/make_synthetic_inputs.py" --dir "$RUN/input"
mkdir -p "$RUN/input/tpl"
python "$SKILL_DIR/scripts/make_template.py" --out "$RUN/input/tpl/template.pptx"
# 把 case.json 的 template 指到 tpl/template.pptx（相对 case.json 所在目录）

# ── 1. A 臂：基础 Agent 做法（不加载 Skill） ─────────────────────────────
python <measure-dir>/plain_baseline_arm.py --case "$RUN/input/case.json" \
    --out "$RUN/armA/out/deck.pptx"

# ── 2. B 臂：加载本 Skill ───────────────────────────────────────────────
python "$SKILL_DIR/scripts/main.py" --case "$RUN/input/case.json" \
    --task "$RUN/input/task.md" --out "$RUN/armB/out"

# ── 3. 用同一套规则测量两臂 ─────────────────────────────────────────────
python <measure-dir>/measure_deck.py --out "$RUN/armA/out" \
    --assets "$RUN/input/figs" --label armA_plain_baseline --json "$RUN/mA.json"
python <measure-dir>/measure_deck.py --out "$RUN/armB/out" \
    --assets "$RUN/input/figs" --label armB_skill        --json "$RUN/mB.json"

# ── 4. 确定性（同输出目录连跑两次后逐文件 sha256 对拍） ───────────────────
python "$SKILL_DIR/scripts/main.py" --case "$RUN/input/case.json" \
    --task "$RUN/input/task.md" --out "$RUN/armB/out"
cp -r "$RUN/armB/out" "$RUN/armB/snap1"
python "$SKILL_DIR/scripts/main.py" --case "$RUN/input/case.json" \
    --task "$RUN/input/task.md" --out "$RUN/armB/out"
# diff -r 或逐文件 sha256 比较 snap1/ 与 armB/out/

# ── 5. 契约门（B 臂 Q8） ────────────────────────────────────────────────
python "$SKILL_DIR/scripts/check_contract.py" --result "$RUN/armB/out/result.json" \
    --out-dir "$RUN/armB/out" --case "$RUN/input/case.json"
```

测量脚本的输入约定：`--out <产物目录>`、`--assets <源图目录>`（用于比对宽高比）、
`--label <臂名>`、可选 `--json <报告路径>`。它**只读产物**，不 import Skill 代码。

## 6. 实测记录（本次真实跑过的对照数据）

环境：Windows 11 + Git Bash；Python 3.13.9；python-pptx 1.0.2；Pillow 12.3.0。
案例：本包自带的**合成**示例案例 `example-catalyst-201`（虚指数值，10 页目标，
2 张图 + 1 张表）。两臂同模板、同图、同一次会话。

### 表 1 —— 质量指标（同一模板、同一案例）

| 指标 | A 臂（基础 Agent） | B 臂（加载本 Skill） | 差值 |
|-|-|-|-|
| 页数（Q1；目标 10） | 3 | 10 | +7 |
| out 目录文件数 | 1 | 12 | +11 |
| 逐页讲稿覆盖率（Q2） | 0.0 | 1.0 | +1.0 |
| 带 `文件:行` 来源定位的页数（Q3） | 0 | 3 | +3 |
| 来源定位串总数（Q3） | 0 | 16 | +16 |
| 底部页脚/页码覆盖页数（Q4） | 0 | 9 | +9 |
| 嵌入图片页数 / 图片总数（Q5） | 1 / 2 | 2 / 3 | +1 / +1 |
| 原生表格页数 | 0 | 1 | +1 |
| 嵌入图宽高比（Q5，源图 1.4286） | 1.4286 | 1.4286 | 0（两臂都未拉伸） |
| PNG 预览文件（签名有效） | 0 | 2（1280×720、2000×1580，均有效） | +2 |
| `result.json` 顶层键数 | 无 result.json | 28 | +28 |
| 页级证据条目 / 证据行总数 | 无 | 10 / 13 | +10 / +13 |
| 模板继承记录（`layout_used` 条数，Q6） | 无 | 10 | +10 |
| 方案套用页数 / 偏差条数（Q7） | 无（无方案阶段） | 10 / 0 | +10 / 0 |
| 自查检查条数（fail / warn） | 无 | 21（0 fail / 0 warn） | +21 |
| CP3 契约门通过数（Q8） | 无 | 8 / 8 | +8 |
| `result.json` 顶层 null 值个数（Q8） | 无 | 0 | — |
| deck 字节数 / sha256 前缀 | 53,039 B / `0ed822f04e873076` | 80,692 B / `c41cb2ce6db055ce` | — |
| **画的版式集合**（C2 核查） | Title Slide + Title and Content | Title Slide + Title and Content | **0（同模板）** |
| **画布 EMU**（C2 核查） | 12192000 × 6858000 | 12192000 × 6858000 | **0（同模板）** |

### 表 2 —— 效率与确定性

| 指标 | A 臂 | B 臂 | 说明 |
|-|-|-|-|
| **E1** 单册墙钟耗时（3 次原始值） | 0.392 / 0.375 / 0.470 s | 1.508 / 1.512 / 1.384 s | — |
| **E1** 中位数 | **0.392 s** | **1.508 s** | B 臂多跑 抽取→页计划→方案→构建→预览→审计→契约门，**用 +1.116 s（约 3.8×）换表 1 的全部 Q 指标** |
| **E2** 输入变更后的返工定位 | 整册重建（无中间判据） | 改内容 → `extract` + `deckplan` + `adopt_plan` + `adapt_pptx`；**只改模板** → `adopt_plan` + `adapt_pptx` | 阶段产物 `spec.json` / `adopt_plan.json` 可单独核对，改模板不必重抽内容 |
| **E3** 同输入重跑字节一致性 | 逐字节相同，但无任何记录可核 | **11 / 12** 个产物逐字节相同 | 差异项：`result.json` 的 `generated_at` 与 `uncertainty[0].note`（首次 `generated-at-runtime`，第二次复用已生成的回退模板写 `reused-generated` —— 运行事实的如实记录，不是随机性）；deck sha256 两次均 `c41cb2ce6db055ce` |
| **E4** 需人工复查的记录条数 | 0（也无可复查的判据） | 34（13 条证据行 + 21 条审计检查） | 这条对 B 臂不利，如实计入 |

### 关于这两张表的边界（必须一起读）

以上两表是包作者在**合成示例案例**（`example-catalyst-201`，虚指数值）上，用一份
**不加载 Skill 的对照脚本**、在同一台机器同一次会话中实测得到的；它证明的是
**机制差异与可测性**，不是平台分数。平台的三案例 × 三重复公平对照由组织方执行，
本包不预置白板、不冒充成绩。

两臂使用**同一份模板**（案例 `template` 字段指向同一 `template.pptx`）：B 臂的
`template_audit` 记录 `opened_from=case_template`、`template_fallback_used=false`、
枚举到 11 个版式；两臂画布与所用版式集合完全一致（见表 1 末两行）。**因此两臂的
差异来自流程，而不是模板来源。**

## 7. 结论与边界

### 7.1 成立的增益（每条都有表 1/表 2 的数字支撑）

| 维度 | 结论 | 证据 |
|-|-|-|
| 质量增益 15 | 在**同模板**条件下，本 Skill 把"一册能讲的学术汇报"应该有的可核验要件补齐：页数达标、逐页讲稿、来源定位、页脚页码、图表放置与比例、模板继承记录、页级证据映射、方案↔执行一致性、契约门 | 表 1 各行（`+7` 页、`1.0` 讲稿覆盖、`+16` 定位串、`+9` 页脚、`10` 条继承记录、`8/8` 契约门） |
| 效率增益 5 | 单位产出的返工定位成本显著下降：阶段产物把"内容"与"模板"解耦，**只换模板时不必重抽内容**；阶段一方案可在动手前被核对，避免整册做完才发现版式不对 | 表 2 的 E2；`adopt_plan.json` / `spec.json` 独立存在 |
| 增益可验证性 5 | 本文件本身即证据：臂定义、公平约束、指标口径、操作步骤都在同一处；两臂数据用同一套规则测量；**对自方不利的差异也列出**（E1 慢 3.8×、E3 并非全字节一致、E4 记录更多） | §2–§5 + 表 2 |

### 7.2 未测 / 不宣称的部分

- **人工排版耗时**未测：本对照只测机器墙钟，不含人眼检查时间。E4 只给"要看的
  条数"，不给"要花多少分钟"——后者依赖人和经验，本包无从测量。
- **跨模板族泛化**未测：只跑了"运行时回退模板 + 案例指定模板"两类，没有跑
  多母版 / 多主题 / 复杂 SmartArt 的商业模板族。
- **PDF 导出保真**未测：本机无 LibreOffice / PowerPoint，`preview_is_schematic=true`，
  因此"导出渲染一致性"这一项**只能测到"有/无有效预览"**（B 臂 2 个有效 PNG、
  A 臂 0 个），**测不到像素级差异**。不宣称 PDF 一致性。
- **E1 的绝对秒数不可跨机比较**：不同机器上应看两臂**比值**（本次约 3.8×）。
- 本协议**不是平台白板**：不含组织方三案例，也不含组织方的评分口径；A 臂是作者
  按"基础 Agent 最自然做法"忠实实现的**代理臂**，不是平台真实基础 Agent 的运行
  记录。因此表 1/表 2 的数字**不能当作平台分数或平台对照结果引用**。

### 7.3 这些边界的意义

把"没测的部分"写清楚不是示弱：如果一份增益材料只列对自方有利的数字，审阅者无法
判断哪些结论是**测出来的**、哪些是**推出来的**。本协议要求每条结论都指到具体
指标行；指不到的，就写进 §7.2。

## 8. 复跑核对清单

- [ ] 两臂命令行里指向的是**同一份** `case.json` / `task.md`
- [ ] `case.json.template` 指向的模板对两臂**都存在且同一份**（不要只在 B 臂用模板）
- [ ] B 臂 `result.json.template_audit.opened_from == "case_template"` 且
      `template_fallback_used == false`（若为 `builtin`，说明 C2 没落实，要重跑）
- [ ] 两臂画布 EMU 与所用版式名集合相同（C2 核查）
- [ ] 测量脚本的 cwd **不在** `$SKILL_DIR` 内（否则生成 `__pycache__` 破坏合规）
- [ ] Q3 的定位串口径写明是 `文件:行` 形态（`material.md:15`），不是任意冒号
- [ ] Q4 写明封面口径（本次 B 臂 9/10，封面无页脚）
- [ ] Q5 同时给出"图数"与"宽高比是否与源图相符"两项，缺一不可
- [ ] Q8 同时给出"门通过数"与"顶层 null 个数"
- [ ] E3 明确列出**差异文件与原因**，不只给一个比率
- [ ] E4 如实计入 B 臂更多的记录条数（不要只报对自己有利的指标）
- [ ] §7.2 里"未测项"清单随本次实际范围更新（测了就移出，没测就留着）
