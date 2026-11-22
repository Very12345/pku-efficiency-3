---
name: academic-slide-adapt
description: >-
  Academic slide deck creation from research material with real template
  adaptation (学术 PPT 模板与格式适配), plus a runnable fault-injection and
  recovery drill: break the input, the template, a runtime dependency and the
  delivery contract on purpose, run the real pipeline as a child process, and
  read back what it actually did — exit code, result.json status, uncertainty
  entries, and whether the fault passed silently. Read the actual
  paper/material and the actual template, extract the research storyline
  (question → method → results → limitations) with per-item `file:line`
  locators, honour the frozen audience/duration/slide count, run a two-phase
  workflow (phase 1 writes a machine-readable adaptation plan: template
  master/layout/placeholder audit + page→layout assignment + batch rules +
  figure placement; phase 2 applies that plan through the template's real
  placeholder inheritance), embed figures/tables contain-fit with figure
  numbers cross-checked, add per-slide speaker notes plus an appendix evidence
  map, and deliver an editable .pptx, PNG previews and a verifiable
  result.json (CP3 gate: check_contract G1–G8). references/FAULT-MATRIX.md
  records, per injected fault, the measured exit code / status / uncertainty
  fields and whether the degradation was silent — including the four places
  where this package is honestly weaker than it claims. Use when the task says
  "make an academic presentation / 学术PPT / 学术汇报 / 论文转PPT / adapt this
  paper into slides / 套模板 / 模板适配 / 按模板生成PPT / deck from paper", or when
  a starting deck must be re-edited on its own template.
---

# Academic Slide Adapter（学术 PPT 模板与格式适配）— 失败注入与恢复演练版 3.5

把论文/研究材料组织成**结构清楚、证据可追溯、可编辑、符合模板要求**的学术汇报。
本版本在既有两阶段工作流之上回答一个更硬的问题：**这条流水线坏掉的时候，它到底怎么坏？**

"我们有失败处理"和"失败处理真的被触发过"是两件事。前者写在文档里，后者需要一个实验：
**故意把东西弄坏，跑真流程，读回真实结果**。本包自带这个实验 ——
`scripts/fault_inject.py` 覆盖 **18 个场景 / 4 个故障家族**，
`references/FAULT-MATRIX.md` 逐行记录**实测**（不是声明）的
退出码、`status`、`uncertainty` 字段，以及**是否静默失败**。

- Skill 版本：`3.5.0`（失败注入 / 恢复演练可复跑）
- **Skill 根 = 本文件所在目录**；下文所有 `$SKILL_DIR` 都指它，命令在**任意 cwd**
  下都能跑（脚本用 `os.path.dirname(__file__)` 自定位，不依赖 cwd）
- 主入口：`$SKILL_DIR/scripts/main.py`（两阶段全流程）
- 演练入口：`$SKILL_DIR/scripts/fault_inject.py`（18 个注入场景 + 静默失败判定）
- **资源形态**：本包**只含 UTF-8 文本文件**（`.md/.py/.json/.txt`），≤50 个、
  单文件 ≤500KB、合计 ≤2MB、无符号链接；二进制一律**运行时生成**（§8）

**读这份文件的顺序**：§2（演练：怎么跑、跑出什么）→ §3（退出码与状态语义）
→ §4（决策规则 D1–D16）→ §5（**已知粗糙点**，最该读）→ §6（检查点）→ §7（自查）。

---

## 1. 用途与适用条件

**适用**：给定论文/实验材料要求产出学术汇报幻灯片，且要求可编辑 pptx、渲染预览与
可复核来源；尤其适用于"必须套用指定模板"或"在起始 deck 上改编"的场景。
读取**真实文件**，绝不凭文件名/标签猜内容。

**适用输入形态**（至少其一）：

| 输入 | 说明 |
|-|-|
| `case.json` | 必读。`case_id / title / subtitle / authors / affiliation / research_question / methods / results / discussion / limitations / conclusion / key_numbers / figures / tables / audience / duration_minutes / slide_count / language / template / starting_deck / source_material / output_contract`（均可省略，缺项走材料抽取或默认值） |
| `task.md` | 任务说明：受众、时长、页数、交付要求 |
| 材料文件 | `source_material` 指明的 md/txt/tex/csv；提供主张与数值的真正来源（`文件:行` 定位） |
| 模板 / 起始 deck | `template` / `starting_deck` 指明的 `.pptx`；两者都缺时回退到**运行时生成**的内置模板（§8） |
| `output_contract` | 案例自带的交付契约；每个字段原样进 `result.json` 顶层（四形态回显，禁止 null） |

**不适用/明确边界**：本 Skill 不代写科学内容（材料中没有的数值绝不补造）、
不做动画/切换效果、不改写模板主题 XML（仅只读记录主题字体/色）；预览在无
LibreOffice/PPT 环境为 PIL 示意图（如实标注，不冒充像素级导出）。

## 2. 失败注入演练：18 个场景、4 个家族

### 2.1 怎么跑

```bash
RUN=<包外可写目录>; cp -r "$SKILL_DIR" "$RUN/pkg"     # 关键：不要在包内跑
python "$RUN/pkg/scripts/fault_inject.py" --skill "$RUN/pkg" --run "$RUN/faultrun" \
    --json "$RUN/fault-report.json" --markdown "$RUN/fault-table.md"
# 实测：18 个场景 / 0 个静默失败 / 退出码 0
```

其它入口：`--list` 列出全部场景；`--only i01-missing-case,k03-artifact-missing`
只跑指定场景；`--skip` 排除；`--timeout` 设单场景超时。

**退出码语义**：`0` = 全部场景与声明一致；`1` = **至少一个场景静默失败**
（把这一条单独做成非零退出码，是因为"静默失败"正是本演练要抓的东西）；
`2` = 用法/环境错误（例如把工作目录设在包内而被拒绝）。

### 2.2 四个故障家族

| 家族 | 注入手法 | 场景数 | 覆盖什么 |
|-|-|-|-|
| **control** | 无注入，原样跑通示例案例 | 1 | 参照组：确认其余 17 个场景的差异**是注入造成的**，不是环境波动 |
| **input** | `--case` 指向幽灵文件；`case.json` 写半截 JSON；`source_material` 指向幽灵文件；材料写成非 UTF-8 字节；删掉案例引用的两张图；`--task` 指向幽灵文件 | 6 | 材料这一层的全部退化形态（D1/D2/D3/D5/F03/F15） |
| **template** | `--template` 指向幽灵文件；模板存在但不是 zip；起始 deck 损坏 | 3 | "缺失"与"损坏"是两条不同代码路径：前者在候选枚举阶段就被跳过，后者真的抛异常并留错误记录 |
| **dependency** | `PYTHONPATH` 前置一个 `import` 即 `raise ImportError` 的假包（`pptx` / `PIL`）；`--out` 指向普通文件；`--out` 指向只读目录 | 4 | 依赖缺失与输出不可写（F21/F22/F23） |
| **contract** | 改 `case_id`；跑完**之后**删一个 `output_contract` 键再跑独立门；跑完**之后**删封面预览再跑独立门；`--work` 指向不存在的目录 | 4 | 契约与交付门（G1/G3/G7/G8），以及"自述不可信"这条主张本身 |

### 2.3 实测结果（摘要；逐行明细见 `references/FAULT-MATRIX.md` §2）

```text
  c00-control               exit=0  status=success  unc=1   -> as-declared
  i01-missing-case          exit=1  status=failed   unc=1   -> as-declared
  i02-garbage-case          exit=1  status=failed   unc=1   -> as-declared
  i03-material-missing      exit=0  status=success  unc=3   -> as-declared
  i04-material-binary       exit=0  status=success  unc=2   -> as-declared
  i05-task-missing          exit=0  status=success  unc=1   -> as-declared
  i06-figures-missing       exit=0  status=success  unc=3   -> as-declared
  t01-template-missing      exit=0  status=success  unc=1   -> as-declared
  t02-template-corrupt      exit=0  status=success  unc=1   -> as-declared
  t03-startdeck-corrupt     exit=0  status=success  unc=1   -> as-declared
  d01-no-pptx               exit=1  status=failed   unc=1   -> as-declared
  d02-no-pil                exit=1  status=failed   unc=1   -> as-declared
  d03-out-unwritable        exit=2  status=(none)   unc=—   -> as-declared
  d04-out-readonly          exit=0  status=success  unc=1   -> HOST-DIFF
  k01-caseid-mismatch       exit=0  status=success  unc=1   -> as-declared
  k02-tamper-contract       exit=0  status=success  unc=1   -> as-declared
  k03-artifact-missing      exit=0  status=success  unc=1   -> as-declared
  k04-work-nonexistent      exit=0  status=success  unc=1   -> as-declared
```

**四条结论**（每条都有上表与 FAULT-MATRIX 的数字支撑）：

1. **"跑不下去"与"跑歪了"分开处置。** 前者（5 个场景）走 `exit≠0` 且**不冒充成功**；
   后者（13 个场景）走"继续跑 + 逐条记录 + 状态词汇诚实"。
   18 个场景里**没有一个是静默地假装一切正常**。
2. **独立校验器真的独立。** 两次篡改后 `result.json` 顶层仍写着 `status=success`，
   而 `check_contract.py` **从磁盘重扫**后判不合格：删契约键 → 失败门 `G3`；
   删预览 → 失败门 `G7`,`G8`。这就是"自述不算证据"的实测形态。
3. **有 4 处降级只落在 `uncertainty`、不改 `status`**（材料与图件类）。
   它们**不是静默失败**（记录在案、可检索），但确实不会把状态拉低到 `partial`。
   逐条列在 §5 与 FAULT-MATRIX §4。
4. **有 1 处是宿主平台差异，不是包的问题**：Windows 上 `chmod 0444` 拦不住写入，
   所以"只读目录"这条判据在本机无法验证。矩阵把它标成 `HOST-DIFF` 并保留原始实测，
   **而不是删掉这一行装作没测**。

## 3. 退出码与状态语义

`scripts/main.py` 的退出码是**三档**，且每一档都有实测：

| 退出码 | 含义 | 有没有 `result.json` | 实测场景 |
|-|-|-|-|
| **0** | 流水线跑完（`status` 可能是 `success` 或 `partial`） | 有 | `c00-control`、模板/材料/图件类降级场景 |
| **1** | 流水线中途失败 → 仍写出**诚实的 `status=failed`** result.json（原因进 `uncertainty`） | 有 | `i01-missing-case`、`i02-garbage-case`、`d01-no-pptx`、`d02-no-pil` |
| **2** | **连"诚实失败"的记录都没地方放**（`--out` 不可写） | **没有** | `d03-out-unwritable` |

`status` 的诚实语义：`success` = 全部审计检查 `ok` + CP3 G1–G8 全过；
`partial` = 出现任一 warn/fail 或命中任一降级分支（**必须写明限制**）；
`failed` = 流水线未完成。

> **注意这组语义的一个实测细节**：控制组 `c00-control` 的 `status=success` 但
> `uncertainty` **非空**（1 条：内置回退模板为运行时生成）。这条记录是**运行事实**，
> 不是降级。所以 G8 要求"非 success 必须有 uncertainty"，但**不要求**
> "有 uncertainty 必须非 success" —— 两者不是互为逆否。

## 4. 决策规则 D1–D16

规则号与 `references/failure-modes.md` 双向对应；下表末列给出**本演练中哪个场景
真的触发了它** —— 没有场景能触发的规则，说明它还没被验证过。

### 4.1 输入层（D1–D4）

| # | 触发条件 | 动作 | 失败时的降级 | 触发场景 |
|-|-|-|-|-|
| **D1** | `--case` 不存在或不是合法 JSON | 立即停止，写 `status=failed`（`case_id` 取文件名词干），退出码 **1** | 不可降级；**绝不**用空壳 case 跑出"看起来像 PPT"的东西 | `i01`、`i02` |
| **D2** | 材料文件缺失 / 编码失败 / 非文本 | 以 `case.json` 结构化字段继续；缺失项进 `uncertainty`，来源标 `exists:false` | 结构化字段也为空时退化为章节标题页，仍**不编造内容**，状态至少 partial | `i03`、`i04` |
| **D3** | 材料是扫描件（无文本层） | 如实标注"图像型材料，未做 OCR" | 不引入任何编造的转写文本 | 未覆盖（需真实扫描件） |
| **D4** | 材料里的数值/结论没有 `文件:行` 定位 | 该条**不上页面**，进 `uncertainty` | 某页因此无主张 → 合并进相邻页并记 `change_records` | 未单独覆盖 |

### 4.2 模板层（D5–D8）

| # | 触发条件 | 动作 | 失败时的降级 | 触发场景 |
|-|-|-|-|-|
| **D5** | 案例既未给模板也未给起始 deck | 运行时现场生成 16:9 回退模板（真实母版/版式/占位符），`opened_from=builtin` 并进 `uncertainty` | 无 python-pptx → `ensure_builtin()` 返回原因字符串而非抛栈 | **全部 18 个场景**（示例案例未给模板） |
| **D6** | 模板 / 起始 deck 打不开 | 逐级回退 `case.template` → `starting_deck` → 运行时回退模板；**每级失败都进** `template_errors` | 全链失败 → `status=failed`，不静默用默认样式冒充"已套用" | `t01`、`t02`、`t03` |
| **D7** | 推荐版式缺该页型所需占位符 | best-fit 选替代版式；仍缺角色就**手绘文本框**按计划几何落位 | 两条路径都写 `adopt_plan_deviations` / `layout_fallback_used` | 需模板族变化才能触发 |
| **D8** | 主题读取失败（`theme1.xml` 不可读） | 主题字段只填 `theme.error`，**不影响构建** | 不猜测主题值 | 未覆盖 |

### 4.3 版式与内容层（D9–D12b）

| # | 触发条件 | 动作 | 失败时的降级 | 触发场景 |
|-|-|-|-|-|
| **D9** | 正文超出占位符真实几何 | 字号阶梯 32→**12**pt 逐级下调 | 落 12pt 仍溢出：**只报告不继续压** | 未单独覆盖（长正文案例可触发） |
| **D10** | 标题单行超过容器估算宽度 | 先降号 | 仍超 → 按容器上限截断并记录 | 未覆盖 |
| **D11** | 计划页数 > `case.slide_count` | 固定顺序裁剪：合并讨论+局限 → 删议程 → 合并末两页结果 | **证据页最后才动**；裁剪写 `change_records` | 未覆盖（示例案例页数刚好） |
| **D12** | 图表源文件缺失或嵌入抛异常 | 保留图位占位框（图号+标题+来源照写） | 灰底占位框，不伪造图形；`figure_adjust.placed=false` | `i06`（**实测只见 uncertainty，见 §5.1**） |
| **D12b** | 正文引用图号 ∉ 图清单 | 记 `xref.figure_refs` warn | **保留原文引用不擅改编号** | 未覆盖 |

### 4.4 交付与状态层（D13–D16）

| # | 触发条件 | 动作 | 失败时的降级 | 触发场景 |
|-|-|-|-|-|
| **D13** | `output_contract` 的键没有天然对应值 | **已知语义的键先取本次运行真实值** | 其余按声明类型给 `""`/`[]`/`{}`/`0`/`false`；**禁止 null**；PDF 类键恒 `false` | 全部 18 个场景 |
| **D14** | 无 LibreOffice / PowerPoint | 预览走 PIL 示意图：文件名含 `schematic`，图内叠加免责声明 | **不产伪 PDF**；`preview_is_schematic=true` | 全部 18 个场景 |
| **D15** | 预览字体探测全失败 | 回退 PIL 内置位图字体，按**文件名/索引**记录 | 日志不写本机路径 | 未覆盖 |
| **D16** | 保存中途失败 / 流水线异常 | 先落盘已生成的部分产物，报错含已写路径，再写 `status=failed` | **绝不写半截 JSON**；`--out` 不可写时退出码 **2** | `i01`/`i02`/`d01`/`d02`/`d03` |

> **表末列的价值**：它同时是一份**覆盖率报告**。18 个场景验证了 D1/D2/D5/D6/D12/D13/
> D14/D16，**没有**验证 D3/D4/D7/D8/D9/D10/D11/D12b/D15 —— 后者需要真实扫描件、
> 长正文、商业模板族、缺字体环境等本机造不出来的条件。别把"文档写了"当成"验证过了"。

## 5. ★ 已知粗糙点（如实列出，不粉饰）

这一节是本次演练最有价值的产出：**以下 4 条是真实暴露出来的弱点**，
全部可复现，全部在 `references/FAULT-MATRIX.md` §4 有逐条说明。

### 5.1 缺图不会把状态拉低

`i06` 里两张源图都被删掉，`uncertainty` 逐图记了两条
（`figure 1 source image` / `figure 2 source image`），但 `status` 仍是 `success`，
且 `main_result.figures_embedded` 仍报 **2/2**（该字段数的是"按计划落位的图表引用数"，
不是"成功嵌入的位图数"）。**后果**：只看 `status` 的消费方会以为图都进去了。
**判别法**：同时读 `uncertainty` 里的 `figure * source image` 条目与
`template_audit.figure_adjust[].placed`。

### 5.2 `--task` 缺失没有专属记录

`i05` 里 `task_summary` 为空字符串，但 `uncertainty` 里**没有**一条说"任务说明没读到"。
**后果**：`--task` 拼错路径时，运行记录不会提醒。
**判别法**：检查 `result.json.task_summary` 是否为空。

### 5.3 内容侧降级不改变 `status`

只有 `case.json` 不可解析、全链模板失败、依赖缺失、`--out` 不可写这几条会让状态
离开 `success`。`D2/D3/D4/D5/D12` 这些**内容侧**降级全部只进 `uncertainty`。
**理由**（是取舍，不是借口）：这些场景下本包**仍然产出了一册完整、可讲、证据可追溯的
汇报**，把它们一律标成 `partial` 会让真正有损的场景失去区分度。
**但这条取舍应当由消费方知道** —— 如果你的流程对状态敏感，请直接读 `uncertainty` 的
`item` 前缀（`source material` / `figure` / `builtin fallback template` / `pipeline`），
它比 `status` 更细。

### 5.4 宿主差异会打乱"只读目录"这条判据

`d04` 在 Windows 上无法用 `chmod 0444` 模拟只读；实测**照常写成功**（exit 0、12 个产物）。
矩阵把这一行标成 `HOST-DIFF`，保留原始实测，**而不是改成"通过"**。

## 6. 检查点与验收入口

| 检查点 | 时机 | 判据 | 不过怎么办 |
|-|-|-|-|
| **CP1** | 阶段一结束 | `adopt_plan.json.gates.ok == true`，或偏差逐条披露 | 先修方案；硬约束无法满足 → 继续 + 记录 + partial（D7） |
| **CP2** | 构建完成 | pptx 可重开 + 页数一致 + 每页有备注 | 记入 `verification.checks`，状态相应降级 |
| **CP3** | 交付前 | `check_contract.py` G1–G8 全过（exit 0） | 修产物或如实保留 warning；**绝不让失败伪装 success** |
| **CP4** | 交付前（本版本新增） | `fault_inject.py` 退出码 **0**（无静默失败） | 有静默失败 → 先修退出码/状态语义，再谈交付 |

```bash
python "$SKILL_DIR/scripts/validate_result.py" --case <case.json> --result <out>/result.json
python "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json \
    --out-dir <out> --case <case.json>
python "$SKILL_DIR/scripts/fault_inject.py" --skill "$SKILL_DIR" --run "$RUN/faultrun"
```

`check_contract.py` **从磁盘独立重扫**（自己重开 pptx、自己逐文件扫产物清单），
不信任 `result.json` 的自述；`exit 0` + `{"valid": true}` 才算 CP3 通过。
`fault_inject.py` 的退出码 **0** 才算 CP4 通过 —— 它的非零退出码专门用来表示
"有场景静默失败了"。

## 7. 自查清单

**跑前**

- [ ] 演练与验收都跑在**包外副本**上（包内跑会留 `scripts/__pycache__/*.pyc`，
      那是平台拒绝的资源类型；两个脚本都会主动拒绝包内工作目录）
- [ ] 一个场景一个全新子进程（`fault_inject.py` 已如此设计：同进程复用会让上一个
      故障的残留状态污染下一个测量）

**跑后**

- [ ] `fault_inject.py` 退出码 **0**，且报告里 `silent_failures` 为 **0**
- [ ] 每个 `must_not_succeed` 场景的退出码 ≠ 0，或独立门 `valid=false`
- [ ] `result.json` 覆盖契约全部字段，**顶层 null 个数为 0**（三档退出码下均如此）
- [ ] `check_contract.py` exit 0 + `{"valid": true}`（CP3）
- [ ] 每条页级主张带 `claim → 文件名:行`；抽查 ≥3 条能在材料中找到
- [ ] 逐页 speaker notes 非空；页脚/页码自封面之后全册一致
- [ ] 输出目录内**没有本机绝对路径**
- [ ] 状态词汇诚实：有降级就不是 `success`
- [ ] **§5 的四条粗糙点在本轮是否仍然成立**；若已修，同步更新 FAULT-MATRIX §4 与本节

## 8. 目录结构与资源形态

```
<skill root>/                      # = $SKILL_DIR（平台装到 /skills/weekly-skill）
  SKILL.md                本文档（故障注入演练 + 退出码语义 + D1–D16 + CP1–CP4）
  README.md               使用说明 / 依赖 / 演练入口 / 限制 / 维护
  TEST.md                 本地实测记录（含 18 场景逐条实测）
  GITHUB_URL.txt          GitHub 公开链接
  references/
    OUTPUT_CONTRACT.md    result.json 结构与字段契约 + CP3 G1–G8（必读）
    RUBRIC_MAP.md         评分五维 → 设计覆盖映射
    FAULT-MATRIX.md       ★ 18 场景实测矩阵 + 四条已知粗糙点（本版重点）
    failure-modes.md      失败模式与降级策略（F01–F24 / D1–D16）
    template_guide.md     模板使用指南（母板/版式/占位符/主题/字号阶梯）
    checklist.md          收尾验收清单
    batch-rules.md        批量一致性规则 R1–R8
    two-phase-workflow.md 两阶段工作流图示与分步命令
  scripts/
    main.py               编排入口（一条命令跑完两阶段；CP1/CP3 门）
    fault_inject.py       ★ 故障注入演练（18 场景 / 4 家族 / 静默失败判定）
    extract.py            主张/图/表/数值抽取（来源定位 + 材料 sha256）
    deckplan.py           确定性页结构方案（页型/裁剪/证据映射）
    adopt_plan.py         阶段一：模板审计 + 页→版式分配 + 批量规则 + 图表计划
    adapt_pptx.py         阶段二：按方案模板适配 + pptx 生成
    preview.py            PIL 示意图预览（封面+联系表，诚实标注）
    audit.py              真实产物自查（重开/覆盖/图号/溢出/页脚/方案一致性）
    validate_result.py    result.json 契约校验（VALID, exit 0）
    check_contract.py     CP3 契约门（G1–G8 独立复查，exit 0）
    pptx_toolkit.py       共享 PPTX 工具（版式打分/占位符/contain-fit/主题/确定 zip）
    make_template.py      内置回退模板的运行时生成（ensure_builtin + make）
    make_synthetic_inputs.py  示例占位图的运行时合成（纯几何，带 SCHEMATIC 水印）
    common.py             公共工具（自定位/便携路径/字号阶梯/字体探测/颜色/哈希）
  examples/               最小示例（合成数据，非正式案例）
    case.json / task.md / material.md / minimal_example.md
    plan.sample.json / adopt_plan.sample.json     方案样例（真实运行，标注示例）
    EXPECTED-OUTPUT.md                            应产出的文件清单与契约字段
    output/               示例运行的**文本**产物（result/summary/render_log）
```

题面硬约束 *at most 50 UTF-8 text files, 500KB each and 2MB total, no symlinks*
⇒ 本包**只含文本资源**，全部二进制改为运行时生成：

| 资源 | 处置 | 入口 |
|-|-|-|
| 回退模板 `.pptx` | 不随包；案例给模板时用真实文件，都缺时**现场生成**（16:9，真实母版/版式/占位符） | `scripts/make_template.py`（`ensure_builtin()`；也可单跑 `--out <dir>/builtin.pptx`） |
| 示例输入图 `.png` | 不随包；示例运行前**现场合成**纯几何占位图（带 `SCHEMATIC / 示意` 水印，不含伪造数值） | `scripts/make_synthetic_inputs.py --dir <示例目录>` |
| 预览 `.png` / 产物 `.pptx` | 运行时生成，写入 `--out` | `scripts/main.py` |
| 字体 `.ttf/.otf` | 不随包；运行时按标准字体目录探测（Windows 目录取自环境变量 `WINDIR`/`SystemRoot`，另有 `/usr/share/fonts`、`/System/Library/Fonts` 等候选），找不到回退 PIL 内置位图字体 | `scripts/common.py`（`font_dirs()` / `probe_font_candidates()`） |
| SVG 图元 | 不随包；本 Skill 不使用矢量模板，预览为 PIL 位图 | — |

脚本不硬编码绝对路径：`scripts/common.py` 用 `os.path.dirname(__file__)` 自定位；
所有真实 I/O 路径由命令行显式给出（官方运行时为 `/input`、`/app/work`、`/app/output`）；
**写进 JSON 的路径一律是便携形式**（运行相对路径 / 正斜杠）。

## 9. 维护

- 版本常量：`scripts/common.py` 的 `SKILL_VERSION`
- 分层约定：素材/抽取 `extract.py`，页结构方案 `deckplan.py`，阶段一方案 `adopt_plan.py`，
  阶段二构建 `adapt_pptx.py`，PPTX 底层 `pptx_toolkit.py`，验证 `audit.py` +
  `validate_result.py` + `check_contract.py`，二进制资源生成 `make_template.py` +
  `make_synthetic_inputs.py`，演练 `fault_inject.py`
- **新增失败模式时同步做四件事**：① 在 `fault_inject.py` 的 `scenarios()` 加一条
  （含 `expect` 与 `must_not_succeed`）；② **真跑一次**并把实测列补进
  `references/FAULT-MATRIX.md` §2/§3；③ 若发现新粗糙点，追加进该文件 §4 与本文 §5；
  ④ 若改变了退出码或状态语义，同步 `references/failure-modes.md` 与本文 §3。
  **没有实测的场景不算覆盖。**
- **改动纪律（本包沿用）**：既有 `scripts/*.py` 尽量逐字节不变；确需修真实缺陷只允许
  **纯增量**并逐条点名（文件、增删行数、理由），**CLI 参数名/默认值/退出码语义不得改**。
  本轮据此**没有**改动 `main.py` / `adapt_pptx.py` 的任何既有行为 —— §5 的四条粗糙点
  因此是"已实测、已登记、未修复"，而不是被悄悄绕过。
- 改动后至少复跑 `fault_inject.py`（CP4）与 `TEST.md` §1 冒烟、§2 确定性。
- 交付前跑包外验收：`python validate_pkg.py <包目录>`（扩展名白名单、≤50 文件、
  ≤500KB/个、≤2MB、无 `__pycache__`、无绝对路径、`py_compile`）。
