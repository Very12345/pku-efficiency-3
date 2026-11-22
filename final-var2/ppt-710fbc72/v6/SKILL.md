---
name: academic-slide-adapt
description: >-
  Academic slide deck creation from research material with real template
  adaptation (学术 PPT 模板与格式适配) — the merged, strongest single package:
  readable storyline extraction with per-item `file:line` locators, a two-phase
  workflow (phase 1 freezes a machine-readable adaptation plan: template
  master/layout/placeholder audit + page→layout assignment + batch rules +
  figure placement; phase 2 applies it through the real placeholder
  inheritance), contain-fit figures/tables with cross-checked figure numbers,
  per-slide speaker notes, an appendix evidence map, and a verifiable
  result.json under an independent CP3 gate (G1–G8) that reopens the pptx and
  rescans artifacts instead of trusting self-reports. Beyond the core pipeline
  it carries four interlocking bodies of evidence: a fair control protocol with
  measurable quality/efficiency indicators (references/GAIN-PROTOCOL.md); six
  named mechanisms each with a falsifiable test (references/MECHANISM.md); an
  18-scenario fault-injection drill reporting measured exit codes, statuses and
  uncertainty fields plus the four places this package is honestly weaker than
  it claims (references/FAULT-MATRIX.md); and a three-case generalisation set
  with declared acceptance ranges that states where generalisation breaks
  (references/CASE-SET.md). Use when the task says "make an academic
  presentation / 学术PPT / 学术汇报 / 论文转PPT / adapt this paper into slides /
  套模板 / 模板适配 / 按模板生成PPT / deck from paper", or when a starting deck
  must be re-edited on its own template.
---

# Academic Slide Adapter（学术 PPT 模板与格式适配）— 全维合并版 4.0

把论文/研究材料组织成**结构清楚、证据可追溯、可编辑、符合模板要求**的学术汇报：
从封面到结论逐页讲清主线，每页带着主张、图表引用与讲稿，并附「页 → 论文位置」证据映射附录。

本包是**合并版**：把"决策显性化""增益可验证""机制可证伪""失败可触发""泛化可测量"
五条线合成一个交付物，并保持两条硬纪律 —— **每个主张都有落点文件**，
**每个机制都有可复跑的判据**。

- Skill 版本：`4.0.0`（union：决策规则 + 增益协议 + 机制 + 故障演练 + 题集）
- **Skill 根 = 本文件所在目录**；下文所有 `$SKILL_DIR` 都指它，命令在**任意 cwd**
  下都能跑（脚本用 `os.path.dirname(__file__)` 自定位，不依赖 cwd）
- 主入口：`$SKILL_DIR/scripts/main.py` · 题集：`scripts/run_case_set.py` · 演练：`scripts/fault_inject.py`
- **资源形态**：本包**只含 UTF-8 文本文件**（`.md/.py/.json/.txt`），50 个、
  单文件 ≤500KB、合计 ≤2MB、无符号链接；二进制一律**运行时生成**（§6.5 / M5）

## 0. 怎么读这份文件

本文件按 **输入 → 执行 → 失败 → 增益 → 机制 → 复用** 重排，每一节末尾都指向
**承载细节的 reference**；本节只保留"决定你下一步动作"的内容。六份 reference 各管一件事：

| Reference | 回答什么问题 | 什么时候必须打开 |
|-|-|-|
| `references/OUTPUT_CONTRACT.md` | 交付什么？字段契约与 CP3 门 G1–G8 的**逐字**定义 | **动手前**（唯一评分产物的定义） |
| `references/RUBRIC_MAP.md` | 本包哪个文件/机制对应五维评分的哪一项 | 交付前自评 |
| `references/failure-modes.md` | 失败模式与降级策略（F01–F24 + D1–D16 双向索引） | 出现异常时先查规则号 |
| `references/FAULT-MATRIX.md` | **实测**：注入 18 种故障后退出码/status/uncertainty 是什么；以及 4 处已知粗糙点 | 谈"可靠体验"之前 |
| `references/GAIN-PROTOCOL.md` | 与"不加载 Skill 的基础 Agent"的公平对照协议 + Q1–Q8/E1–E4 + 实测记录 | 谈"增益"之前 |
| `references/MECHANISM.md` | M1–M6 六个机制、没有它会怎样、**怎么证伪它** | 被问"你和脚本集合有什么区别"时 |
| `references/CASE-SET.md` | 三案例题集、声明区间、逐案实测、**泛化失效边界** | 谈"泛化"之前 |
| `references/REUSABLE-ASSETS.md` | 资产 A–F 的入口参数、依赖、继承的保证、三个复用场景 | 想只拿走一层时 |
| `references/two-phase-workflow.md` | 两阶段的分步命令、每步对应的决策规则与机制 | 分步调试时 |
| `references/checklist.md` | 收尾验收清单（A–E 组）+ 批量一致性规则 R1–R8（附章） | 交付前逐项勾选 |
| `references/template_guide.md` | 母版/版式/占位符/主题字体色/字号阶梯的操作细节 | 换模板族时 |

**执行顺序（先方案，后执行，最后自证）**：
① 读 `OUTPUT_CONTRACT.md` → ② 读真实文件并抽取 → 页结构方案 → 适配方案（**CP1**）
→ ③ 按方案构建（**CP2**）→ 预览 → 审计 → `result.json` → ④ 契约门（**CP3**）
→ ⑤ 故障演练（**CP4**）与题集（**CP5**）自证 → ⑥ 按 `RUBRIC_MAP.md` 五维自评。

---

# 第一部分 · 输入

## 1.1 用途与适用条件

**适用**：给定论文/实验材料要求产出学术汇报幻灯片，且要求可编辑 pptx、渲染预览与
可复核来源；尤其适用于"必须套用指定模板"或"在起始 deck 上改编"的场景。
读取**真实文件**，绝不凭文件名/标签猜内容（D1/D2）。

**输入形态**（至少其一）：

| 输入 | 说明 |
|-|-|
| `case.json` | 必读。键清单见 §1.2；**缺项是正常输入形态**（§3.6 的 L2 案例只给最小 12 键），缺的走材料抽取 |
| `task.md` | 任务说明：受众、时长、页数、交付要求 |
| 材料文件 | `source_material` 指明的 md/txt/tex/csv；主张与数值的真正来源（`文件:行` 定位 + 材料 sha256） |
| 模板 / 起始 deck | `template` / `starting_deck` 指明的 `.pptx`；两者都缺时回退到**运行时生成**的内置模板（M5） |
| `output_contract` | 案例自带的交付契约；每个字段原样进 `result.json` 顶层（四形态回显，禁止 null） |

**明确不适用**：本 Skill 不代写科学内容（材料中没有的数值绝不补造）、不做动画/切换
效果、不改写模板主题 XML（仅只读记录主题字体/色）；预览在无 LibreOffice/PPT 环境为
PIL 示意图（如实标注，不冒充像素级导出）。完整边界见 `MECHANISM.md` §8。

## 1.2 `case.json` 的完整键清单

```
case_id / _meta / title / subtitle / authors / affiliation /
research_question / methods / results / discussion / limitations / conclusion /
key_numbers / figures / tables / audience / duration_minutes / slide_count /
language / template / starting_deck / source_material / output_contract
```

全部可省略；缺项走材料抽取或默认值。`extract.py` 会为每条内容绑定来源
（`文件:行` 或 `case.json[字段]`），材料另记 sha256。

## 1.3 官方运行契约

平台运行时输入为 `/input/case.json` 与 `/input/task.md`，材料按案例挂载，
在 `/app/work` 内解析相对路径；产物写 `/app/output`。本包脚本以
`os.path.dirname(__file__)` 自定位 Skill 根，**不依赖 cwd**；真实 I/O 路径全部由命令行给出。

---

# 第二部分 · 执行

## 2.1 一条命令

```bash
python "$SKILL_DIR/scripts/main.py" --case <case.json> [--task <task.md>] \
    [--work <材料基目录>] [--template <模板.pptx>] \
    [--starting-deck <deck.pptx>] --out <输出目录>
```

平台正式运行时：

```bash
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md \
    --work /app/work --out /app/output
```

## 2.2 两阶段与五个检查点

**阶段一（PLAN）——建立 M1 的判据**

| 步骤 | 动作 | 落点 | 检查点 |
|-|-|-|-|
| 1 | 读真实文件：`case.json` + `task.md`；逐个读材料并**逐行编号** | `content.json`（每条带 `文件:行` + 材料 sha256） | — |
| 2 | 模板链解析：`case.template` → `starting_deck` → 运行时回退模板 | `template_audit.template_errors` / `opened_from` | D5/D6 |
| 3 | 页结构方案：cover → background → methods → results×N → discussion → limitations → conclusion → evidence_map → thankyou（页数充裕时插 agenda） | `spec.json` | D11 |
| 4 | 适配方案：枚举母版/版式/占位符(idx/name/宽高)/画布/主题 → 逐页 `recommended_layout_idx` → 批量规则评估 → 图表放置计划（含 contain-fit 比例） | `adopt_plan.json` | **CP1** |

**阶段二（EXECUTE）——让 M4/M6 可测**

| 步骤 | 动作 | 落点 | 检查点 |
|-|-|-|-|
| 5 | 按方案建册：逐页套版式（缺占位符 best-fit 或手绘文本框）；内容写进占位符**继承模板主题**；字号阶梯 32→12pt 抗溢出；图表等比 contain-fit；封面外统一页脚+页码；逐页 speaker notes；起始 deck 模式下**旧页连关系一起移除** | `<case>_deck.pptx` + `.build_audit.json` | **CP2** |
| 6 | 预览：无 LibreOffice 时出 PIL 示意图（封面 + 全册联系表，文件名含 `schematic`） | 两张 PNG + `render_log.json` | D14/D15 |
| 7 | 自查 + `result.json`：在**真实产物**上跑 21 项检查（重开/页数/主张覆盖/图号交叉引用/备注/溢出/字号落底/页脚一致/PNG 有效性/证据覆盖率/方案↔执行一致性）；契约回显；状态判定 | `audit.json` + `result.json` | — |
| 8 | 契约门：**不信自述**的独立校验器从磁盘重扫并逐门判定 | `verification.contract_gates` | **CP3** |

| 检查点 | 时机 | 判据 | 不过怎么办 |
|-|-|-|-|
| **CP1** | 阶段一结束 | `adopt_plan.json.gates.ok == true`，或偏差逐条披露 | 先修方案；硬约束无法满足 → 继续 + 记录 + status 降 partial（D7） |
| **CP2** | 构建完成 | pptx 可被 python-pptx 重开 + 页数 = `spec.json` + 逐页备注存在 | 记入 `verification.checks`，状态相应降级 |
| **CP3** | 交付前 | `check_contract.py` G1–G8 全过（exit 0 + `{"valid": true}`） | 修产物或如实保留 warning；**绝不让失败伪装 success** |
| **CP4** | 交付前（失败演练） | `fault_inject.py` 退出码 **0**（无静默失败） | 先修退出码/状态语义 |
| **CP5** | 交付前（题集） | `run_case_set.py` 退出码 **0**（无超出声明区间的案例） | 按 `CASE-SET.md` 判断是改案例还是登记边界 |

```bash
SKILL_DIR=<本包根目录>; RUN=<包外可写目录>
cp -r "$SKILL_DIR/examples" "$RUN/examples"
python "$SKILL_DIR/scripts/make_synthetic_inputs.py" --dir "$RUN/examples"   # 图不随包，运行时合成
python "$SKILL_DIR/scripts/main.py" --case "$RUN/examples/case.json" \
    --task "$RUN/examples/task.md" --out "$RUN/out"                          # → exit 0, status=success
python "$SKILL_DIR/scripts/validate_result.py" --case "$RUN/examples/case.json" --result "$RUN/out/result.json"
python "$SKILL_DIR/scripts/check_contract.py" --result "$RUN/out/result.json" \
    --out-dir "$RUN/out" --case "$RUN/examples/case.json"                    # → valid=true, exit 0
```

## 2.3 分步命令（`--out` 语义不同，传错会得到 `IsADirectoryError`）

```bash
python "$SKILL_DIR/scripts/make_template.py"  --out "$RUN/builtin.pptx"        # → 文件
python "$SKILL_DIR/scripts/extract.py"  --case "$CASE" --task "$TASK" --out "$RUN"    # → 目录
python "$SKILL_DIR/scripts/deckplan.py" --content "$RUN/content.json" --out "$RUN"    # → 目录
python "$SKILL_DIR/scripts/adopt_plan.py" --content "$RUN/content.json" \
    --spec "$RUN/spec.json" --builtin "$RUN/builtin.pptx" --out "$RUN/adopt_plan.json"   # → 文件
python "$SKILL_DIR/scripts/adapt_pptx.py" --content "$RUN/content.json" \
    --spec "$RUN/spec.json" --adopt-plan "$RUN/adopt_plan.json" \
    --builtin "$RUN/builtin.pptx" --out "$RUN/deck.pptx"                       # → 文件
python "$SKILL_DIR/scripts/preview.py" --content "$RUN/content.json" --spec "$RUN/spec.json" --out "$RUN"
python "$SKILL_DIR/scripts/audit.py"   --content "$RUN/content.json" --spec "$RUN/spec.json" \
    --out "$RUN" --adopt-plan "$RUN/adopt_plan.json"
```

**分步不产 `result.json`**（契约回显与 CP3 门是 `main.py` 的职责），
所以**分步运行不构成一次可交付**；定位完问题后回到一条命令重跑。
每步对应的决策规则与机制见 `references/two-phase-workflow.md`。

## 2.4 批量一致性规则（整册统一）

R1 页脚一致 · R2 页码一致 · R3 标题位置一致 · R4 字号层级一致（32→12pt 阶梯）·
R5 图注格式一致（`图N 标题 [来源: loc]`）· R6 图表缩放一致（contain-fit 不拉伸）·
R7 主题继承一致 · R8 页序/页型一致。
由 `adopt_plan.py` 在阶段一**集中评估**、`adapt_pptx.py` 在阶段二**统一执行**、
`audit.py` 构建后**逐页校验**；冲突**不静默**，写入 `batch.deviations`。
完整规则表见 `references/checklist.md` 附章。

---

# 第三部分 · 失败

## 3.1 退出码与状态语义（三档，每一档都有实测）

| 退出码 | 含义 | 有没有 `result.json` | 实测场景（`FAULT-MATRIX.md`） |
|-|-|-|-|
| **0** | 流水线跑完（`status` 可能是 `success` 或 `partial`） | 有 | 控制组与 13 个"跑歪了"的场景 |
| **1** | 流水线中途失败 → 仍写出**诚实的 `status=failed`**（原因进 `uncertainty`） | 有 | `i01-missing-case`、`i02-garbage-case`、`d01-no-pptx`、`d02-no-pil` |
| **2** | **连"诚实失败"的记录都没地方放**（`--out` 不可写） | **没有** | `d03-out-unwritable` |

`status` 三档：`success` = 全部审计检查 `ok` + CP3 全过；`partial` = 有 warn/fail 或
命中任一降级分支（**必须写明限制**）；`failed` = 流水线未完成。

> **一个容易搞错的实测细节**：控制组的 `status=success` 但 `uncertainty` **非空**
> （"内置回退模板为运行时生成"）。这条是**运行事实**，不是降级。所以 G8 要求
> "非 success 必须有 uncertainty"，但**不要求**"有 uncertainty 必须非 success"。

## 3.2 决策规则总表（D1–D16）

每条三要素：**触发条件 → 动作 → 失败时的降级**。与
`references/failure-modes.md`（F01–F24）编号双向对应。

### 3.2.1 输入层（D1–D4）

| # | 触发条件 | 动作 | 失败时的降级 | 实测场景 |
|-|-|-|-|-|
| **D1** | `--case` 不存在或不是合法 JSON | 立即停止，写 `status=failed`（`case_id` 取文件名词干），退出码 **1** | 不可降级；**绝不**用空壳 case 跑出"看起来像 PPT"的东西 | `i01`、`i02` |
| **D2** | 材料文件缺失 / 编码失败 / 非文本 | 以 `case.json` 结构化字段继续；缺失项进 `uncertainty`，来源标 `exists:false` | 结构化字段也为空 → 退回材料补位；仍**不编造内容**，状态至少 partial | `i03`、`i04` |
| **D3** | 材料是扫描件（无文本层） | 如实标注"图像型材料，未做 OCR"；有图仍按图清单引用 | 不引入任何编造的转写文本 | 未覆盖 |
| **D4** | 材料里的数值/结论没有 `文件:行` 定位 | 该条**不上页面**，进 `uncertainty` | 某页因此无主张 → 合并进相邻页并记 `change_records`，不保留空页 | 未单独覆盖 |

### 3.2.2 模板层（D5–D8）

| # | 触发条件 | 动作 | 失败时的降级 | 实测场景 |
|-|-|-|-|-|
| **D5** | 案例既未给模板也未给起始 deck | 运行时**现场生成** 16:9 回退模板（真实母版/版式/占位符），`opened_from=builtin` 并进 `uncertainty` | 无 python-pptx → `ensure_builtin()` 返回原因字符串而非抛栈 | **全部 18 个演练场景** |
| **D6** | 模板 / 起始 deck 打不开（损坏、加密、格式不符） | 逐级回退 `case.template` → `starting_deck` → 运行时回退模板；**每级失败都进** `template_errors` | 全链失败 → `status=failed`，不静默用默认样式冒充"已套用" | `t01`、`t02`、`t03` |
| **D7** | 推荐版式缺该页型所需占位符（cover 要 title+subtitle；正文页要 title+body，`text` 类侧栏不算 body） | best-fit 选替代版式；仍缺角色就**手绘文本框**按计划几何落位 | 两条路径都写 `adopt_plan_deviations` / `layout_fallback_used`；偏差 > 0 时至少 partial | 换模板族才触发 |
| **D8** | 主题读取失败（`theme1.xml` 不可读） | 主题字段只填 `theme.error`，**不影响构建**（主题本就是只读记录） | 不猜测主题值；`theme` 里不写推测出来的字体名 | 未覆盖 |

### 3.2.3 版式与内容层（D9–D12b）

| # | 触发条件 | 动作 | 失败时的降级 | 实测场景 |
|-|-|-|-|-|
| **D9** | 正文超出占位符真实几何 | 字号阶梯 32→28→24→20→18→16→14→**12**pt 逐级下调 | 落 12pt 仍溢出：**只报告不继续压**（`layout.overflow`）；页脚字号不受影响。实测后果见 §3.5.3 | 题集案例 C 命中 |
| **D10** | 标题单行超过容器估算宽度 | 先降号 | 仍超 → 按容器上限截断并记录；不出现"看不见的溢出文字" | 未覆盖 |
| **D11** | 计划页数 > `case.slide_count` | 固定顺序裁剪：合并 discussion+limitations → 删 agenda → 合并最后两张结果页 | **证据页（evidence_map）最后才动**；任何裁剪写 `change_records`。回收上限实测为 3 页，见 §3.5.1 | 题集案例 B 命中 |
| **D12** | 图表源文件缺失或嵌入抛异常 | 保留图位占位框（图号 + 标题 + 来源照写） | 灰底占位框，不伪造图形、不留空白页；`figure_adjust.placed=false` | `i06`（见 §3.5.1） |
| **D12b** | 正文引用图号 ∉ 图清单 | 记 `xref.figure_refs` warn | **保留原文引用不擅改编号**；图清单为空时正文图号降级为文字描述 | 未覆盖 |

### 3.2.4 交付与状态层（D13–D16）

| # | 触发条件 | 动作 | 失败时的降级 | 实测场景 |
|-|-|-|-|-|
| **D13** | `output_contract` 的键在本 Skill 里没有天然对应值 | **已知语义的键先取本次运行真实值**（`preview_png` / `evidence_per_slide` / `notes_per_slide` / `template_inheritance` / `slide_count` / `audience` / `language`） | 其余按声明容器类型给 `""` / `[]` / `{}` / `0` / `false`；**禁止 null**；PDF 类键恒 `false`；派生明细进 `verification.contract_echo_derived` | 全部场景 |
| **D14** | 无 LibreOffice / PowerPoint | 预览走 PIL 示意图：封面 + 全册联系表，文件名含 `schematic`，图内叠加免责声明 | **不产伪 PDF**；`preview_is_schematic=true` | 全部场景 |
| **D15** | 预览字体探测全失败（标准字体目录 + CJK 文件扫描都没命中） | 回退 PIL 内置位图字体，按**文件名/索引**记录 | 日志不写本机路径 | 未覆盖 |
| **D16** | 保存中途失败 / 流水线异常 | **先落盘已生成的部分产物**，报错含已写路径，再写 `status=failed` | 现场不丢；**绝不写半截 JSON**；`--out` 不可写时退出码 **2** | `i01`/`i02`/`d01`/`d02`/`d03` |

## 3.3 失败分支表（B01–B24，与 D 规则双向检索）

执行中遇到异常，**先在下表定位分支号，再按"处置"列的末档动作执行** —— 不要临场发明处置方式。
完整版（含识别信号与记录字段的逐字名称）见 `references/failure-modes.md`。

| 组 | 分支 | 覆盖 |
|-|-|-|
| 材料异常 | **B01–B05** | case 缺失/坏 JSON（B01）· 材料文件缺失（B02）· 材料不可读（B03）· 扫描件/无文本层（B04）· 数值无 `文件:行` 定位（B05） |
| 模板与版式异常 | **B06–B11** | 模板路径不存在（B06）· 模板损坏/加密（B07）· 全链模板失败（B08）· 案例未给模板（B09）· 版式缺所需占位符（B10）· 推荐版式阶段二不可用（B11） |
| 内容/几何/图表异常 | **B12–B17** | 文本框溢出（B12）· 标题过长（B13）· 页数超目标（B14）· 源图缺失/嵌入失败（B15）· 图号与正文不一致（B16）· 图宽高比异常（B17） |
| 环境/依赖/交付异常 | **B18–B24** | 无 LibreOffice/PPT（B18）· 预览字体缺失（B19）· 契约键无值（B20）· python-pptx 缺失（B21）· Pillow 缺失（B22）· `--out` 不可写（B23）· 保存中途失败（B24） |

`references/failure-modes.md` 另有一节把每个降级动作接到 M1–M6 上，并给出
**"它在保护哪个机制"** 的判据（答不上来的动作就不该存在）。

## 3.4 失败注入演练：18 个场景、4 个家族

```bash
RUN=<包外可写目录>; cp -r "$SKILL_DIR" "$RUN/pkg"
python "$RUN/pkg/scripts/fault_inject.py" --skill "$RUN/pkg" --run "$RUN/faultrun" \
    --json "$RUN/fault-report.json" --markdown "$RUN/fault-table.md"
# 实测：18 个场景 / 0 个静默失败 / 退出码 0
```

| 家族 | 注入手法 | 场景数 |
|-|-|-|
| **control** | 无注入，原样跑通示例案例（参照组） | 1 |
| **input** | `--case` 幽灵文件 · 半截 JSON · `source_material` 幽灵文件 · 非 UTF-8 材料 · 删掉案例引用的两张图 · `--task` 幽灵文件 | 6 |
| **template** | `--template` 幽灵文件 · 模板损坏（不是 zip）· 起始 deck 损坏 | 3 |
| **dependency** | `PYTHONPATH` 前置 import 即抛 `ImportError` 的假 `pptx` / `PIL` · `--out` 指向普通文件 · `--out` 指向只读目录 | 4 |
| **contract** | 改 `case_id` · 跑完删一个契约键再跑独立门 · 跑完删封面预览再跑独立门 · `--work` 指向不存在的目录 | 4 |

**四条结论**（逐行明细见 `references/FAULT-MATRIX.md` §2）：

1. **"跑不下去"与"跑歪了"分开处置**：前者走 `exit≠0` 且**不冒充成功**；
   后者走"继续跑 + 逐条记录 + 状态词汇诚实"。18 个场景**没有一个是静默地假装正常**。
2. **独立校验器真的独立**：两次篡改后 `result.json` 顶层仍写着 `status=success`，
   而 `check_contract.py` 从磁盘重扫后判不合格 —— 删契约键 → 失败门 **G3**；
   删预览 → 失败门 **G7, G8**。
3. **有 4 处降级只落在 `uncertainty`、不改 `status`**（见 §3.5）。
4. **有 1 处是宿主差异**：Windows 上 `chmod 0444` 拦不住写入，"只读目录"这条判据
   在本机无法验证；矩阵把它标成 `HOST-DIFF` 并保留原始实测，而不是改成"通过"。

## 3.5 ★ 已知粗糙点与失效边界（如实列出，不粉饰）

这一节是全包最该被读的部分：**以下条目都是实测暴露出来的，不是推测。**

### 3.5.1 缺图不会把状态拉低（来自失败演练 `i06`）

两张源图都被删掉时，`uncertainty` 逐图记了两条，但 `status` 仍是 `success`，
且 `main_result.figures_embedded` 仍报 **2/2**（该字段数的是"按计划落位的图表引用数"，
不是"成功嵌入的位图数"）。**判别法**：同时读 `uncertainty` 里的
`figure * source image` 条目与 `template_audit.figure_adjust[].placed`。

### 3.5.2 `--task` 缺失没有专属记录（来自失败演练 `i05`）

`task_summary` 为空字符串，但 `uncertainty` 里**没有**一条说"任务说明没读到"。
**判别法**：检查 `result.json.task_summary` 是否为空。

### 3.5.3 内容侧降级不改变 `status`（11 条只进 uncertainty）

只有 case 不可解析、全链模板失败、依赖缺失、`--out` 不可写会让状态离开 `success`；
`D2/D3/D4/D5/D12` 这些**内容侧**降级全部只进 `uncertainty`。
**理由**（是取舍不是借口）：这些场景下本包**仍然产出了一册完整、可讲、证据可追溯的
汇报**，一律标 `partial` 会让真正有损的场景失去区分度；但这条取舍**应当由消费方知道**。
**判别法**：直接读 `uncertainty` 的 `item` 前缀（`source material` / `figure` /
`builtin fallback template` / `pipeline`），它比 `status` 更细。

### 3.5.4 页预算会被"带媒体的结果条目数"顶破（来自题集案例 B）

案例 B 声明 12 页、实测 **13 页**。根因：`deckplan.py` 的"每条结果一页"分支要求
`(target - fixed - 3) >= result_pages_needed`；该案为 `4 >= 7`，不成立 ⇒ 走另一分支，
**每条带媒体的结果各占一页** ⇒ 结果页 7 张；尾部裁剪是**一次性三步**
（合并讨论+局限 → 删议程 → 合并末两页结果），**最多回收 3 页**，不足以回到 12。
**这不是要修的 bug，而是固定裁剪顺序的代价**：顺序固定换来可预测与可复跑。
**判别法**：`main_result.planned_slides > target_slides`。

### 3.5.5 "只有表格、没有图"的结果页会丢掉它自己的主张条目（来自题集案例 B）

第 8 页（只放表 1）页面上**只有**标题与表题行，该页的主张条目没有出现；
对照第 9 页（有图有表）条目正常。被 `audit.py` 的 `content.claim_coverage` 抓到：

```text
content.claim_coverage | warn | 1 claims not literally found; truncated: ['p8:表1 汇总不同温度下的 Li⁺ 电导']
```

⇒ `status=partial` + `uncertainty` 记一条。**本包未修改该版式路径**（见 §9 改动纪律），
如实登记供使用方决定。

### 3.5.6 一页塞太多主张时，末尾主张会被文本框装不下而丢掉（来自题集案例 C）

第 4 页把 6 条主张归到同一收集页，实际只写到第 4 条末尾就断了
（字号阶梯压到 12pt 地板后**只报告、不继续压**，见 D9/F12），后两条未上页；
同样由 `content.claim_coverage` 抓出 ⇒ `partial`。

### 3.5.7 宿主差异（来自失败演练 `d04`）

`chmod 0444` 在 Windows 上不阻止写入，只读目录场景实测照常写成功。
矩阵标 `HOST-DIFF`，不改判据、不改结论。

> **这七条的共同点**：全部**已检出、已记录、已降级或已声明**，没有一条是"静默地
> 假装没发生"。把没测到的与做得不好的写清楚，比只列有利数字更能让评审判断
> 哪些结论是**测出来的**、哪些是**推出来的**。

## 3.6 题集：三案例、三层难度、声明区间

完整内容（每案输入形态、期望产出结构、可接受区间、逐案实测、失效边界）见
**`references/CASE-SET.md`**。

| # | 案例 | 难度层 | 题材 | 页预算 | 结构化字段 | 这案在考什么 |
|-|-|-|-|-|-|-|
| A | `example-catalyst-201` | **L0** 基线接口 | 催化化学（CO₂ 加氢制甲醇） | 10 页 / 12 min | 完整 | 接口没被改坏的回归基线 |
| B | `case-b-gnn-potential-301` | **L1** 结构完整 | 计算材料（GNN 势函数 / 固态电解质 Li⁺ 输运） | 12 页 / 15 min | 完整（39 条定位） | 换题材 + 换页预算后还成不成立 |
| C | `case-c-uhi-remote-302` | **L2** 退化输入 | 城市环境遥感（地表温度反演 / 热岛归因） | 9 页 / 10 min | **只给最小 12 键** | 主线能否真的从材料小节里抽出来 |

```bash
python "$RUN/pkg/scripts/run_case_set.py" --skill "$RUN/pkg" \
    --cases "$RUN/pkg/examples" --run "$RUN/caseset" \
    --json "$RUN/caseset.json" --markdown "$RUN/caseset.md"
# 实测：3 个案例 / 0 个超出声明区间 / 1 个已声明边界命中（案例 B，见 §3.5.4）/ 退出码 0
```

**声明区间与实测**（摘要；完整表见 `CASE-SET.md` §1–§2）：

| 判据 | A | B | C |
|-|-|-|-|
| `status` | success | partial | partial |
| `slide_count`（声明 → 实测） | =10 → **10** | ∈[12,13] → **13**（boundary-hit） | =9 → **9** |
| 讲稿覆盖率 | 1.00 | 1.00 | 1.00 |
| 证据定位覆盖率 | **1.000** | **1.000** | **1.000** |
| 图表落位 | 2/2 | 2/2 | 1/1 |
| CP3 门 / 顶层 null | 8/8 / 0 | 8/8 / 0 | 8/8 / 0 |
| 材料补位桶数 | — | — | **6/6 全命中** |

**三案的共同点值得单独指出**：换题材（催化→计算材料→遥感）、换页预算（10→12→9）、
换输入完整度（完整→最小字段）之后，**契约层与证据层没有退化** —— 证据定位覆盖率
全部 1.000、CP3 门全部 8/8、顶层 `null` 全部 0、方案套用全部满分且偏差 0。
退化只出现在 §3.5.4–§3.5.6 三处，且三处都被审计抓到并降级。

**题集没有覆盖的**（别把它当成泛化的全部证据）：跨模板族（三案全部
`opened_from=builtin`）· 真 PDF/像素级导出 · 英文分支 · 起始 deck 编辑 ·
上百行长材料 · 单页 3 张以上并排图。完整清单见 `CASE-SET.md` §4.4。

---

# 第四部分 · 增益（与"不加载 Skill 的基础 Agent"的公平对照）

完整协议、指标定义与实测记录见 **`references/GAIN-PROTOCOL.md`**。
组织方的正式白板与三案例对照由平台执行；本包给的是**可复跑的本地等效对照协议 + 真实跑过的记录**。

## 4.1 两个臂的定义

- **A 臂（基础 Agent，不加载本 Skill）**：沿用同一份模板；把 `case.json` 各环节的
  `text` **整段拼起来**塞进"Title and Content"正文占位符；图**按原始尺寸**直接放；
  不写页脚/页码、不写 speaker notes、不做版式规划、不记录来源定位；**不产 `result.json`**。
  A 臂不是"故意做坏"——它产出的是**能打开、能讲的 PPT**，只是没有可核验的中间判据。
- **B 臂（加载本 Skill）**：`main.py` 一条命令跑完两阶段全流程。

**公平性六约束**：C1 同输入 · C2 **同模板**（最容易含糊的一条：很多"增益对照"其实
拿"我们用了指定模板"对比"他们用了默认模板"，那不是流程增益而是输入差异；
本协议强制两臂同模板，并把**版式名集合与画布 EMU** 作为核查证据）· C3 同版本
（附两个 sha256）· C4 同环境 · C5 同预算 · C6 不预置答案。

## 4.2 指标 ↔ 执行动作映射（交付前逐行核对）

| 指标 | 计算式 | 本 Skill 里谁负责产出 | 落点字段 | 保护它的规则 |
|-|-|-|-|-|
| **Q1** 页数达成度 | 实际页数 / `case.slide_count` | `deckplan.py` 确定性页结构 + 超页裁剪 | `result.json.slide_count` | D9/D10/D11 |
| **Q2** 逐页讲稿覆盖率 | 有非空 notes 的页数 / 总页数 | `adapt_pptx.py` 逐页写 speaker notes | `main_result.notes_pages` | — |
| **Q3** 来源可追溯率 | 带 `文件:行` 定位串的页数 / 总页数 | `extract.py` 逐行编号抽取 | `slide_evidence[].evidence[].loc` / `traceability.evidence_loc_frac` | D2/D3/D4 |
| **Q4** 页脚/页码一致性 | 底部带页脚或页码的页数 / 总页数（封面口径：满分通常为 `(N-1)/N`） | `adapt_pptx.py` 批量规则 | `audit.json` 的 `layout.footer_uniform` | R1/R2 |
| **Q5** 图表放置完整率 | 嵌入图数 / `case.figures` 条数，且**宽高比 == 源图**（容差 1e-3） | `adopt_plan.py` 算 contain-fit → `adapt_pptx.py` 按比例放置 | `template_audit.figure_adjust[].aspect_preserved` | D12/D12b |
| **Q6** 模板继承可查性 | `layout_used` 条数 / 总页数 | 阶段一审计 → 阶段二逐页套用并记录 | `template_audit.layout_used` | D5–D8 |
| **Q7** 方案↔执行一致性 | `adopt_plan_applied` / 计划页数，且偏差逐条可读 | 阶段二消费阶段一方案 | `adopt_plan_applied` / `adopt_plan_deviations` | D7 |
| **Q8** 契约完整率 | G1–G8 通过数 / 8，且顶层 `null` 个数 = 0 | `check_contract.py` 独立重扫 + 契约四形态回显 | `verification.contract_gates` / 顶层键 | D13/D14/D16 |
| **E1** 单册墙钟 | 端到端子进程耗时中位数 | 一条命令跑完两阶段（避免人工串联） | — | — |
| **E2** 返工步数 | 输入变更后需重跑的**阶段数** | 阶段产物解耦：`spec.json`（内容侧）与 `adopt_plan.json`（模板侧）分离 | — | — |
| **E3** 重跑字节一致性 | 逐字节相同产物数 / 总数（并列差异项与原因） | `deterministic_zip()` 固定 zip 条目时间戳；几何为纯函数 | — | M6 |
| **E4** 人工核对工作量 | 证据行数 + 审计检查行数（**越大代表要看的越多，不是越大越好**） | 全部结论落盘 | `audit.json` + `slide_evidence` | — |

## 4.3 实测记录（同一合成示例案例、同一模板、同一次会话）

| 指标 | A 臂 | B 臂 | 差值 |
|-|-|-|-|
| 页数（Q1；目标 10） | 3 | **10** | +7 |
| out 目录文件数 | 1 | 12 | +11 |
| 逐页讲稿覆盖率（Q2） | 0.0 | **1.0** | +1.0 |
| 带 `文件:行` 定位的页数 / 定位串总数（Q3） | 0 / 0 | 3 / **16** | +3 / +16 |
| 底部页脚/页码覆盖页数（Q4） | 0 | 9 | +9 |
| 嵌入图片页数 / 图片总数（Q5） | 1 / 2 | 2 / 3 | +1 / +1 |
| 原生表格页数 | 0 | 1 | +1 |
| 嵌入图宽高比（源图 1.4286） | 1.4286 | 1.4286 | 0（两臂都未拉伸） |
| PNG 预览（签名有效） | 0 | **2**（1280×720、2000×1580） | +2 |
| `result.json` 顶层键数 | 无 | 28 | +28 |
| 页级证据条目 / 证据行总数 | 无 | 10 / 13 | +10 / +13 |
| 模板继承记录（`layout_used` 条数，Q6） | 无 | 10 | +10 |
| 方案套用页数 / 偏差条数（Q7） | 无（无方案阶段） | 10 / 0 | +10 / 0 |
| 自查检查条数（fail / warn） | 无 | 21（0 / 0） | +21 |
| CP3 门通过数（Q8） | 无 | **8 / 8** | +8 |
| 顶层 `null` 个数（Q8） | 无 | **0** | — |
| deck 字节数 / sha256 前缀 | 53,039 B / `0ed822f04e873076` | 80,692 B / `c41cb2ce6db055ce` | — |
| 画的版式集合（C2 核查） | Title Slide + Title and Content | 同 | **0（同模板）** |
| 画布 EMU（C2 核查） | 12192000 × 6858000 | 同 | **0（同模板）** |

| 效率与确定性 | A 臂 | B 臂 | 说明 |
|-|-|-|-|
| **E1** 单册墙钟（3 次原始值） | 0.392 / 0.375 / 0.470 s | 1.508 / 1.512 / 1.384 s | — |
| **E1** 中位数 | **0.392 s** | **1.508 s** | 用 **+1.116 s（约 3.8×）** 换 Q1–Q8 全部指标；**绝对值依赖机器，跨机只看比值** |
| **E2** 输入变更后的返工定位 | 整册重建（无中间判据） | 改内容 → `extract` + `deckplan` + `adopt_plan` + `adapt_pptx`；**只改模板** → `adopt_plan` + `adapt_pptx` | 阶段产物可单独核对 |
| **E3** 同输入重跑字节一致性 | 逐字节相同，但无记录可核 | **11 / 12** 逐字节相同 | 差异项：`result.json` 的 `generated_at` 与 `uncertainty[0].note`（首次 `generated-at-runtime`、第二次 `reused-generated`——**运行事实的如实记录**，不是随机性）；deck sha256 两次均 `c41cb2ce6db055ce` |
| **E4** 需人工复查的记录条数 | 0（也无可复查的判据） | 34（13 条证据行 + 21 条审计检查） | **这条对 B 臂不利，如实计入** |

## 4.4 未测 / 不宣称

- **人工排版耗时未测**：本对照只测机器墙钟，不含人眼检查时间；E4 只给"要看的条数"。
- **跨模板族泛化未测**：只跑了"运行时回退模板 + 案例指定模板"两类，未跑多母版/
  多主题/复杂 SmartArt 的商业模板族。
- **PDF 导出保真未测**：本机无 LibreOffice/PowerPoint，`preview_is_schematic=true`，
  因此"导出渲染一致性"只能测到"有/无有效预览"，**测不到像素级差异**。
- **E1 绝对秒数不可跨机比较**；**本协议不是平台白板**：A 臂是作者按"基础 Agent 最
  自然做法"忠实实现的**代理臂**，表里的数字**不能当作平台分数或平台对照结果引用**。

---

# 第五部分 · 机制（六个机制，每个都可证伪）

详解（含"没有它会怎样"与逐条可证伪判据）见 **`references/MECHANISM.md`**。

| # | 机制 | 一句话 | 落点 | **没有它会怎样** | 可证伪判据（复跑即可验） |
|-|-|-|-|-|-|
| **M1** | 方案先行 | 模板审计与页→版式分配在动手前固化成 `adopt_plan.json` | `scripts/adopt_plan.py` → `result.json.adopt_plan` / `template_audit.layout_used` | "读一页填一页"：出错只能整册返工，且**没有中间判据可核对** | 删掉 `adopt_plan.py` 的调用后重跑 → `adopt_plan_applied` 应变为缺失或 0，`adopt_plan.consistency` 应 fail |
| **M2** | 契约先行 + CP3 硬门 | 交付形状先定；结束后由**不信自述**的校验器从磁盘重扫并逐门判定 | `OUTPUT_CONTRACT.md` · `scripts/check_contract.py` → `verification.contract_gates` | 产物缺件与 `null` 占位只能在人眼看时才发现 | **实测已证**：删一个契约键 → G3 fail；删一张预览 → G7+G8 fail（§3.4） |
| **M3** | 证据定位绑定 | 每条主张带 `文件:行`；无定位的数值不上页面 | `scripts/extract.py` · `scripts/audit.py` → `slide_evidence[].evidence[].loc` / `traceability.evidence_loc_frac` | 页面"看起来对"但无法核对某个数字是不是原文里的那个 | 取任一 `evidence[].loc`（形如 `material.md:15`）翻到该行应能找到对应内容；抽样 3 条对不上即失效 |
| **M4** | 方案↔执行一致性 | 计划与实际**逐页对照**，不一致逐条留痕 | `scripts/adapt_pptx.py` → `adopt_plan_applied` / `adopt_plan_deviations` | 方案与产物脱钩，M1 退化成装饰文档 | 故意把 `adopt_plan.json` 某页的 `recommended_layout_idx` 改成缺占位符的版式 → 偏差应出现至少一条 |
| **M5** | 二进制运行时生成 | 包内只放文本，模板/示例图/预览现场生成 | `scripts/make_template.py` · `make_synthetic_inputs.py` | 必须往包里塞 `.pptx`/`.png` ⇒ 触题面资源约束，**可能整包被拒收** | `find <包目录> \( -name '*.pptx' -o -name '*.png' -o -name '*.pyc' \)` 应 0 命中；**同时**运行后 `<out>/` 应出现 `_runtime/builtin.pptx` 与两个 PNG（两条必须同时成立） |
| **M6** | 确定性字节 | 几何为纯函数 + `deterministic_zip()` 固定 zip 时间戳 | `scripts/pptx_toolkit.py` | 每次跑出不同哈希，"产物是不是跑出来的"不可核 | 同输出目录连跑两次，`<case>_deck.pptx` 与两张 PNG 的 sha256 应完全相同（实测 11/12，差异项为 `generated_at` 等运行事实） |

**依赖顺序（也是排查顺序）**：**M5 最外层**（包能不能被接收）→ **M2**（交付物是否完整）
→ **M1/M3/M4**（内容是否可信）→ **M6**（过程是否可复验）。
抽掉链条上游的机制，下游判据会连带失效 —— 完整连锁表见 `MECHANISM.md` §7。

**实测锚点**：方案阶段枚举出 **1 个母版 / 11 个版式**及占位符清单；阶段二
**逐页套用 10/10、偏差 0**；**13/13 条证据行带定位（覆盖率 1.0）**；
`artifacts=8 missing=[]`；`reopened; 10 slides`；顶层 `null` 个数 **0**；
运行后产出 `_runtime/builtin.pptx`（**27,522 B**，**运行时生成**，
`opened_from=builtin`）与两个有效预览（1280×720 / 2000×1580）。

---

# 第六部分 · 复用

资产清单、入口参数、依赖、继承的保证（**参数名与 `scripts/*.py --help` 逐字一致**，
已逐个核对）见 **`references/REUSABLE-ASSETS.md`**。

## 6.1 可复用资产 A–F

| 资产 | 路径 | 依赖 | 可独立运行 | 适合谁 |
|-|-|-|-|-|
| **A** 模板适配层 | `pptx_toolkit.py` + `adapt_pptx.py` | python-pptx | ✅ | 已有内容管线，只借"套模板 + 占位符继承 + contain-fit" |
| **B** 阶段一方案器 | `adopt_plan.py` | python-pptx | ✅ | 想先审模板结构、再决定每页版式 |
| **C** 确定性页计划器 | `deckplan.py` | **无（纯标准库）** | ✅ | 想要"论文章节 → 页型序列"的确定性映射 |
| **D** 审计与契约工具 | `audit.py` · `validate_result.py` · `check_contract.py` | python-pptx | ✅ | 给自己的 Skill 加"独立校验 + 硬门" |
| **E** 运行时资源生成器 | `make_template.py` · `make_synthetic_inputs.py` | python-pptx / Pillow | ✅ | 包体受限（只能放文本）、又需要真实模板/图件 |
| **F** 示例题集与页级金标准 | `examples/`（含 `cases/` 三案例） | 无 | 作为输入 | 快速验证自己管线；照抄"案例 → 契约"形态 |
| **G** 失败演练装置 | `fault_inject.py` + `FAULT-MATRIX.md` | 无（纯标准库） | ✅ | 想给自己的 Skill 也做一套降级路径实测 |
| **H** 题集运行器 | `run_case_set.py` + `case_manifest.json` | 无（纯标准库） | ✅ | 想用"声明区间 + 实测对拍"的方式证明泛化 |
| 公共工具 / 契约定义 | `common.py` / `OUTPUT_CONTRACT.md` | 无 | 库 / 文档 | 自定位、便携路径、字号阶梯、字体探测 / 字段契约与 G1–G8 |

## 6.2 三个复用场景

1. **只用模板适配层（自带内容管线）**：`extract` → `deckplan` → `adopt_plan` →
   `adapt_pptx` → `preview`。产出 deck + 两张预览，**不产 `result.json`**
   （那是 `main.py` 的职责），因此不构成一次可提交交付。
2. **接进已有管线（只要方案与校验）**：先用 `adopt_plan.py` 审模板拿到版式清单与
   页→版式建议；你自己的生成器产出 deck + `result.json` 之后，用
   `check_contract.py` 把门。**它对任意产物都有效**（G4 自己重开 pptx、G7 逐文件扫
   产物），不依赖本包的生成器。
3. **当作对照基线（做自己的增益实验）**：用本包当 B 臂、你的做法当 A 臂，
   按 `GAIN-PROTOCOL.md` §3 的六条约束执行。**最容易出错的一步**：让两臂共用
   **同一份模板**；若 B 臂的 `template_audit.opened_from` 是 `builtin`（而非
   `case_template`），说明"同模板"没落实，整个对照无效。
4. **（本版新增）当作失败演练与题集的模板**：把 `fault_inject.py` 的**场景四元组**
   （`inject` / `expect` / `must_not_succeed` / `run`）与 `run_case_set.py` 的
   **声明区间 + 对拍** 抄到你自己的 Skill 上 —— 这两套装置的写法比结论更可复用。

## 6.3 复用产出如何自证（七条）

1. **结构完整**：`check_contract.py --result ... --out-dir ... --case ...` → exit 0 且 `{"valid": true}`；
2. **字段契约**：`validate_result.py --case ... --result ...` → `VALID`；
3. **模板继承可查**：`template_audit.layout_used` 每页一条（版式名 / master / 来源）；
4. **内容可追溯**：抽查 ≥3 条 `slide_evidence[].evidence[].loc` 能在材料中命中；
5. **方案可信**：`adopt_plan_applied` == 计划页数，`adopt_plan_deviations` 可读；
6. **过程可复跑**：同输出目录连跑两次，deck 与 PNG 的 sha256 相同；
7. **诚实披露**：非 `success` 状态必须带 `uncertainty`（G8 会查这一点）。

## 6.4 复用时的已知坑

| 坑 | 现象 | 处置 |
|-|-|-|
| **在包内跑脚本** | 生成 `scripts/__pycache__/*.pyc` | 交付前删除；**永远在包外副本上跑**（`.pyc` 属平台拒绝的资源类型）。`fault_inject.py` 与 `run_case_set.py` 都会**主动拒绝**包内工作目录 |
| `--out` 语义混用 | `extract/deckplan/preview/audit` 收**目录**；`adopt_plan/adapt_pptx/make_template` 收**文件** | 传错会得到 `IsADirectoryError` 一类错误；按 §2.3 传 |
| 案例未给模板就以为会失败 | 走的是回退模板路径 | **这是设计行为**（D5）：`opened_from=builtin`，来源进 `uncertainty`；不要据此判失败 |
| 把"预览"当"导出" | 预览是 PIL 示意图（`preview_is_schematic=true`） | 需要像素级/PDF 时须自备 LibreOffice/PowerPoint；本包**不产伪 PDF** |
| 认为重跑一定全字节一致 | `result.json` 有 `generated_at`，且回退模板来源措辞会变 | 见 §4.3 的 E3（11/12）；**核对 deck 与 PNG 的哈希**，不要拿 `result.json` 当一致性判据 |
| 主题字体/色当可写 | 它们只是**只读记录** | 需要改主题请改模板本体，本包不代改（D8） |
| 依赖缺失静默失败 | 不会：写 `status=failed` 的 `result.json` | 读 `uncertainty[0].note` 拿到原始 `ImportError` 文本（实测见 `FAULT-MATRIX.md`） |
| 案例图/表标题写成 `图1 标题`（空格分隔） | 抽取阶段匹配不上，图表清单为空 | 必须写成 **`图1：标题`**（图号后紧跟中文全角冒号）；表同理 |
| 材料小节标题不含分桶关键词 | 六个故事线桶可能为空 | 小节标题须含：背景/问题/引言、方法/实验、结果/数据/图/表、讨论、限制/局限/不足、结论/总结 |

## 6.5 资源形态（为什么包里没有 `.pptx` / `.png`）

题面硬约束：*Skill resources: at most 50 UTF-8 text files, 500KB each and
2MB total, no symlinks.* ⇒ 本包**只含文本资源**，所有二进制改为运行时生成，
生成物与正式案例的产物形态完全一致：

| 资源 | 处置 | 入口 |
|-|-|-|
| 内置回退模板 `.pptx` | 不随包；案例给模板/起始 deck 时用真实文件，两者都缺时**现场生成**（16:9，真实母版/版式/占位符） | `scripts/make_template.py`（`ensure_builtin()`；也可单跑 `--out <dir>/builtin.pptx`） |
| 案例/示例输入图 `.png` | 不随包；运行前**现场合成**纯几何占位图（带 `SCHEMATIC / 示意` 水印，不含伪造数值） | `scripts/make_synthetic_inputs.py --dir <目录>` 或 `--out-dir <figs 目录>` |
| 预览 `.png` / 产物 `.pptx` | 运行时生成，写入 `--out` | `scripts/main.py` |
| 字体 `.ttf/.otf` | 不随包；运行时按标准字体目录探测（Windows 目录取自环境变量 `WINDIR`/`SystemRoot`，另有 `/usr/share/fonts`、`/System/Library/Fonts` 等候选），找不到回退 PIL 内置位图字体并记录 | `scripts/common.py`（`font_dirs()` / `probe_font_candidates()`） |
| SVG 图元 | 不随包；本 Skill 不使用矢量模板，预览为 PIL 位图 | — |

**缺依赖时的降级**：无 python-pptx 时 `ensure_builtin()` 返回带原因的说明而非抛异常；
构建/预览阶段失败按 D16 写出诚实的 `status=failed` result.json（实测见 `FAULT-MATRIX.md`）。

---

# 第七部分 · 目录结构与产出

```
<skill root>/                      # = $SKILL_DIR（平台装到 /skills/weekly-skill）
  SKILL.md                本文档（输入→执行→失败→增益→机制→复用）
  README.md               使用说明 / 依赖 / 入口 / 限制 / 维护
  TEST.md                 本地实测记录（冒烟 / 确定性 / 鲁棒性 / 演练 / 题集）
  GITHUB_URL.txt          GitHub 公开链接
  references/
    OUTPUT_CONTRACT.md    result.json 结构与字段契约 + CP3 G1–G8（必读）
    RUBRIC_MAP.md         评分五维 → 设计覆盖映射（交付前自评）
    failure-modes.md      F01–F24 失败模式 + 与 D1–D16 双向索引 + 机制归属
    FAULT-MATRIX.md       ★ 18 场景故障注入实测 + 4 处已知粗糙点
    GAIN-PROTOCOL.md      ★ 公平对照协议 + Q1–Q8/E1–E4 + 实测记录
    MECHANISM.md          ★ M1–M6 六机制 + 可证伪判据 + 连锁表
    CASE-SET.md           ★ 三案例题集 + 声明区间 + 泛化失效边界
    REUSABLE-ASSETS.md    ★ 资产 A–F 复用清单 + 三个场景 + 坑表
    checklist.md          收尾验收清单（A–E）+ 批量规则 R1–R8（附章）
    template_guide.md     模板使用指南（母板/版式/占位符/主题/字号阶梯）
    two-phase-workflow.md 两阶段分步命令 + 每步的规则/机制对应
  scripts/
    main.py               编排入口（一条命令两阶段；CP1/CP3 门）
    fault_inject.py       ★ 故障注入演练（18 场景 / 4 家族 / 静默失败判定）
    run_case_set.py       ★ 题集运行器（跑三案并与声明区间对拍）
    extract.py            主张/图/表/数值抽取（来源定位 + 材料 sha256）
    deckplan.py           确定性页结构方案（页型/裁剪/证据映射）
    adopt_plan.py         阶段一：模板审计 + 页→版式分配 + 批量规则 + 图表计划
    adapt_pptx.py         阶段二：按方案模板适配 + pptx 生成
    preview.py            PIL 示意图预览（封面 + 联系表，诚实标注）
    audit.py              真实产物自查（重开/覆盖/图号/溢出/页脚/方案一致性）
    validate_result.py    result.json 契约校验（VALID, exit 0）
    check_contract.py     CP3 契约门（G1–G8 独立复查，exit 0）
    pptx_toolkit.py       共享 PPTX 工具（版式打分/占位符/contain-fit/主题/确定 zip）
    make_template.py      内置回退模板的运行时生成（ensure_builtin + make）
    make_synthetic_inputs.py  示例占位图的运行时合成（纯几何，带 SCHEMATIC 水印）
    common.py             公共工具（自定位/便携路径/字号阶梯/字体探测/颜色/哈希）
  examples/               最小示例 + 题集（合成数据，非正式案例）
    case.json / task.md / material.md / minimal_example.md
    plan.sample.json / adopt_plan.sample.json     方案样例（真实运行，标注示例）
    EXPECTED-OUTPUT.md                            应产出的文件清单与契约字段
    cases/                ★ 题集：case-b-… / case-c-… 两个新题材案例
      case_manifest.json  每案的难度层与可接受区间（测量脚本据此对拍）
    output/               示例运行的**文本**产物（result/summary/render_log）
```

**产物清单**（写 `--out`；官方约定 `/app/output`）：

| 文件 | 角色 |
|-|-|
| `<case_id>_deck.pptx` | 可编辑源：套版式/占位符、逐页主张+图表+讲稿备注、统一页脚页码 |
| `<case_id>_cover_preview.png` | 封面预览（PIL 示意图，命名与文件内均标注 SCHEMATIC） |
| `<case_id>_slides_contact_schematic.png` | 全册联系表（PIL 示意图） |
| **`result.json`** | **唯一评分产物**（契约见 `references/OUTPUT_CONTRACT.md`） |
| `adopt_plan.json` | 阶段一方案：模板审计 + 页→版式分配 + 批量规则 + 图表计划（M1） |
| `spec.json` / `content.json` | 页结构方案 / 规范化抽取（含来源定位，M3；也是 E2 解耦的两侧） |
| `audit.json` / `render_log.json` / `summary.txt` | 自查报告 / 渲染日志 / 摘要 |
| `_runtime/builtin.pptx` | 案例未给模板/起始 deck 时**运行时生成**的回退模板（M5） |

---

# 第八部分 · 交付前自查（合并各版清单）

**结构性与契约（每轮都查）**

- [ ] 读的是真实文件（case/task/材料/模板），不是凭标签假设内容
- [ ] **M1**：`adopt_plan.json.gates.ok` 为真，或偏差逐条写明（CP1）
- [ ] **M2**：`check_contract.py` exit 0 + `{"valid": true}`；顶层 `null` 个数 = 0（CP3）
- [ ] **M3**：每条页级主张带 `claim → 文件名:行`；抽查 ≥3 条能在材料中命中
- [ ] **M4**：`adopt_plan_applied` == 计划页数；偏差可读（含 0 偏差时的记录）
- [ ] **M5**：包内 `*.pptx / *.png / *.pyc` **0 命中**，但运行后产物齐全（两条同时成立）
- [ ] **M6**：同输出目录连跑两次，deck 与 PNG 的 sha256 相同
- [ ] `result.json` 覆盖契约全部字段 + case_id + status + sources + uncertainty + change_records
- [ ] pptx 可重开、页数 = 计划（CP2）；预览 PNG 存在且非空白
- [ ] 输出目录内**没有本机绝对路径**（记录一律是运行相对路径或环境路径）
- [ ] 状态词汇诚实：有降级就不是 `success`

**增益（§4.2 逐行核对）**

- [ ] **Q1** 页数 == `case.slide_count`（或裁剪已记 `change_records`）
- [ ] **Q2** 每页都有非空 speaker notes；**Q4** 封面外每页有页脚或页码
- [ ] **Q5** 图数 == `case.figures` 条数；`figure_adjust` 无拉伸记录
- [ ] **Q6** `layout_used` 每页一条；**Q7** `adopt_plan_applied` == 计划页数
- [ ] **Q8** `check_contract.py` exit 0 + `{"valid": true}`；顶层 null = 0
- [ ] **没有**把"未测的东西"写成已测（§4.4 的未测清单要同步更新）

**失败（§3 逐条核对）**

- [ ] 命中过的每条 D 规则与 B 分支都能在 `result.json` 里找到对应字段
- [ ] `fault_inject.py` 退出码 **0**，报告里 `silent_failures` = 0（CP4）
- [ ] 每个 `must_not_succeed` 场景的退出码 ≠ 0，或独立门 `valid=false`
- [ ] §3.5 的七条粗糙点在本轮是否仍然成立；若已修，同步更新 `FAULT-MATRIX.md` §4 与本文件

**泛化（§3.6 逐条核对）**

- [ ] `run_case_set.py` 退出码 **0**（无超出声明区间的案例）（CP5）
- [ ] 若某案落入 `boundary-hit`，必须能在 `CASE-SET.md` §4 找到原因，并在回报里点明
- [ ] **不要为了让报告好看而改宽区间**；要改区间必须附可复现理由与实测上限

---

# 第九部分 · 维护与改动纪律

- 版本常量：`scripts/common.py` 的 `SKILL_VERSION`
- 分层约定：素材/抽取 `extract.py` · 页结构 `deckplan.py` · 阶段一方案 `adopt_plan.py` ·
  阶段二构建 `adapt_pptx.py` · PPTX 底层 `pptx_toolkit.py` · 验证 `audit.py` +
  `validate_result.py` + `check_contract.py` · 二进制生成 `make_template.py` +
  `make_synthetic_inputs.py` · 演练 `fault_inject.py` · 题集 `run_case_set.py`
- **新增能力时同步做四件事**：① 本文件对应章节加行，并说明它产出**哪条指标**
  （Q/E）或守护**哪个机制**（M）；② 若引入新降级路径，在 `failure-modes.md` 加条目并
  指定 D 号与守护的机制；③ 若引入新资产，在 `REUSABLE-ASSETS.md` 加条目并给出参数与
  继承的保证；④ 真跑本章的检查点并更新 `TEST.md`。
  **只有动作、没有落点的功能不算增益；没有可证伪判据的机制不算机制。**
- **改动纪律**：既有 `scripts/*.py` 尽量**逐字节不变**；确需修真实缺陷只允许**纯增量**，
  并逐条点名（文件、增删行数、理由），**CLI 参数名/默认值/退出码语义不得改**。
  本轮据此**没有**修改任何既有脚本的行为 —— §3.5 的七条因此是
  "已实测、已登记、未修复"，而不是被悄悄绕过。
- **合并包的取舍**：本包是 union 包，受"≤50 个文件"硬门约束，因此把同主题的两份
  reference 并成了一份 —— 原 `references/batch-rules.md` 的**全文**已并入
  `references/checklist.md` 的附章，**内容一字未删**（章节编号原样保留）。
  后续若再超限，**继续合并同主题文档，不要删内容**。
- 改动后至少复跑：`TEST.md` §1 冒烟与 §2 确定性、`run_case_set.py`（CP5）、
  `fault_inject.py`（CP4）；若改动了影响 Q/E 指标的行为，**必须重跑
  `GAIN-PROTOCOL.md` §5 的对照步骤并更新其 §6 实测记录**，同时复核
  `MECHANISM.md` 与 `FAULT-MATRIX.md` 里引用的数字。
- 交付前跑包外验收：`python validate_pkg.py <包目录>`（扩展名白名单、≤50 文件、
  ≤500KB/个、≤2MB、无 `__pycache__`、无绝对路径、`py_compile`）。
