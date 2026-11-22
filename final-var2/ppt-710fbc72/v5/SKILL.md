---
name: academic-slide-adapt
description: >-
  Academic slide deck creation from research material with real template
  adaptation (学术 PPT 模板与格式适配), shipped with a measurable case set: three
  synthetic cases at three difficulty tiers — L0 a structure-complete baseline
  that guards the interface, L1 the same shape on a different subject and a
  different page budget, L2 a deliberately degraded input whose storyline
  fields are absent and must be recovered from the material markdown. Read the
  actual paper/material and the actual template, extract the research storyline
  (question → method → results → limitations) with per-item `file:line`
  locators, honour the frozen audience/duration/slide count, run a two-phase
  workflow (phase 1 writes a machine-readable adaptation plan: template
  master/layout/placeholder audit + page→layout assignment + batch rules +
  figure placement; phase 2 applies that plan through the template's real
  placeholder inheritance), embed figures/tables contain-fit with figure
  numbers cross-checked, add per-slide speaker notes plus an appendix evidence
  map, and deliver an editable .pptx, PNG previews and a verifiable
  result.json (CP3 gate: check_contract G1–G8). Every claim about generality is
  measured against declared acceptance ranges by scripts/run_case_set.py, and
  references/CASE-SET.md states — with numbers — where generalisation stops.
  Use when the task says "make an academic presentation / 学术PPT / 学术汇报 /
  论文转PPT / adapt this paper into slides / 套模板 / 模板适配 / 按模板生成PPT /
  deck from paper", or when a starting deck must be re-edited on its own template.
---

# Academic Slide Adapter（学术 PPT 模板与格式适配）— 题集与泛化可验证版 3.4

把论文/研究材料组织成**结构清楚、证据可追溯、可编辑、符合模板要求**的学术汇报：
从封面到结论逐页讲清主线，每页带着主张、图表引用与讲稿，并附「页 → 论文位置」证据映射附录。

本版本与前几版的组织方式不同：它以**一套可复跑的题集**为主线。理由很直接 ——
"这个 Skill 能用"这句话，只有在**换题材、换页预算、换输入完整度之后仍然成立**时才有意义；
而"仍然成立"必须能被测量。所以本包自带三个案例、三层难度、一组**事先声明**的可接受区间，
以及一个把它们真跑一遍并对拍的脚本。

- Skill 版本：`3.4.0`（题集驱动 / 泛化边界显性化）
- **Skill 根 = 本文件所在目录**；下文所有 `$SKILL_DIR` 都指它，命令在**任意 cwd**
  下都能跑（脚本用 `os.path.dirname(__file__)` 自定位，不依赖 cwd）
- 核心入口：`$SKILL_DIR/scripts/main.py`（一条命令完成两阶段全流程）
- 题集入口：`$SKILL_DIR/scripts/run_case_set.py`（跑满三案并与声明区间对拍）
- **资源形态**：本包**只含 UTF-8 文本文件**（`.md/.py/.json/.txt`），≤50 个、
  单文件 ≤500KB、合计 ≤2MB、无符号链接；模板/图片/预览等二进制一律**运行时生成**（§9）

**读这份文件的顺序**：§2（怎么跑）→ §3（题集与区间）→ **§4（泛化边界，最该读）**
→ §5（决策规则 D1–D16，按"哪一层会命中它"组织）→ §6（检查点）→ §8（按层自查）。

---

## 1. 用途与适用条件

**适用**：给定论文/实验材料要求产出学术汇报幻灯片，且要求可编辑 pptx、渲染预览与
可复核来源；尤其适用于"必须套用指定模板"或"在起始 deck 上改编"的场景。
读取**真实文件**，绝不凭文件名/标签猜内容。

**适用输入形态**（至少其一）：

| 输入 | 说明 |
|-|-|
| `case.json` | 必读。完整的键清单见 §3.3；**缺项是正常输入形态**（L2 就故意只给最小字段），缺的走材料抽取 |
| `task.md` | 任务说明：受众、时长、页数、交付要求 |
| 材料文件 | `source_material` 指明的 md/txt/tex/csv；提供主张与数值的真正来源（`文件:行` 定位） |
| 模板 / 起始 deck | `template` / `starting_deck` 指明的 `.pptx`；两者都缺时回退到**运行时生成**的内置模板（§9） |
| `output_contract` | 案例自带的交付契约；每个字段原样进 `result.json` 顶层（四形态回显，禁止 null） |

**不适用/明确边界**：本 Skill 不代写科学内容（材料中没有的数值绝不补造）、
不做动画/切换效果、不改写模板主题 XML（仅只读记录主题字体/色）；预览在无
LibreOffice/PPT 环境为 PIL 示意图（如实标注，不冒充像素级导出）。

## 2. 执行：一条命令，或分步

主入口（**命令与 `scripts/` 实际入口逐字一致**；`$SKILL_DIR` 为本包根，任意 cwd 均可）：

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

**跑整套题集**（推荐先用它确认环境，再上正式案例）：

```bash
RUN=<包外可写目录>; cp -r "$SKILL_DIR" "$RUN/pkg"      # 关键：不要在包内跑
python "$RUN/pkg/scripts/run_case_set.py" --skill "$RUN/pkg" \
    --cases "$RUN/pkg/examples" --run "$RUN/caseset" \
    --json "$RUN/caseset.json" --markdown "$RUN/caseset.md"
# 期望：3 个案例，0 个超出声明区间，1 个已声明边界命中（见 §4.1），退出码 0
```

**只跑自带示例**（示例图不随包，需现场合成）：

```bash
SKILL_DIR=<本包根目录>; RUN=<任意可写目录>
cp -r "$SKILL_DIR/examples" "$RUN/examples"
python "$SKILL_DIR/scripts/make_synthetic_inputs.py" --dir "$RUN/examples"
python "$SKILL_DIR/scripts/main.py" --case "$RUN/examples/case.json" \
    --task "$RUN/examples/task.md" --out "$RUN/out"
```

**分步命令**（每一步的 `--out` 语义不同，传错会得到 `IsADirectoryError` 一类错误）：

```bash
python "$SKILL_DIR/scripts/make_template.py"  --out "$RUN/builtin.pptx"      # → 文件
python "$SKILL_DIR/scripts/extract.py"  --case "$CASE" --task "$TASK" --out "$RUN"   # → 目录
python "$SKILL_DIR/scripts/deckplan.py" --content "$RUN/content.json" --out "$RUN"   # → 目录
python "$SKILL_DIR/scripts/adopt_plan.py" --content "$RUN/content.json" \
    --spec "$RUN/spec.json" --builtin "$RUN/builtin.pptx" --out "$RUN/adopt_plan.json"  # → 文件
python "$SKILL_DIR/scripts/adapt_pptx.py" --content "$RUN/content.json" \
    --spec "$RUN/spec.json" --adopt-plan "$RUN/adopt_plan.json" \
    --builtin "$RUN/builtin.pptx" --out "$RUN/deck.pptx"                     # → 文件
python "$SKILL_DIR/scripts/preview.py" --content "$RUN/content.json" --spec "$RUN/spec.json" --out "$RUN"
python "$SKILL_DIR/scripts/audit.py"   --content "$RUN/content.json" --spec "$RUN/spec.json" \
    --out "$RUN" --adopt-plan "$RUN/adopt_plan.json"
```

> **分步不产 `result.json`** —— 契约回显与 CP3 门是 `main.py` 的职责，
> 所以分步运行**不构成一次可交付**；定位完问题后回到一条命令重跑。
> 作为 Agent，你**必须**在调用脚本之外阅读真实文件并复核抽取/落版，
> 偏差写进 `result.json` 的 `change_records` / `uncertainty`。**不得用预制答案替代实际运行。**

工作流的两阶段语义与检查点：

1. **阶段一（PLAN）**：抽取（带 `文件:行` + 材料 sha256）→ 确定性页计划 →
   适配方案（模板审计 + 页→版式分配 + 批量规则 + 图表放置计划）→ **CP1**；
2. **阶段二（EXECUTE）**：按方案建册 → **CP2** → 预览 → 审计 → `result.json` → **CP3**。

## 3. 题集：三个案例、三层难度、一组区间

完整内容（每案输入形态、期望产出结构、可接受区间、逐案实测数字、以及**失效边界**）
见 **`references/CASE-SET.md`**（本版本新增）。这里给速查。

### 3.1 三案与难度层

| # | 案例 | 难度层 | 题材 | 页预算 | 结构化字段 | 这案在考什么 |
|-|-|-|-|-|-|-|
| A | `example-catalyst-201` | **L0** 基线接口 | 催化化学（CO₂ 加氢制甲醇） | 10 页 / 12 min | 完整 | 接口没被改坏的回归基线 |
| B | `case-b-gnn-potential-301` | **L1** 结构完整 | 计算材料（GNN 势函数 / 固态电解质 Li⁺ 输运） | 12 页 / 15 min | 完整（39 条定位） | 换题材 + 换页预算后还成不成立 |
| C | `case-c-uhi-remote-302` | **L2** 退化输入 | 城市环境遥感（地表温度反演 / 热岛归因） | 9 页 / 10 min | **只给最小 12 键** | 主线能否真的从材料小节里抽出来 |

**为什么必须是三层而不是三个同类案例**：三层各自触发不同的代码路径。
L2 走的是 `extract.py` 的 `supplemented_from_material` 补位分支，
L0 **永远走不到它** —— 所以"L0 通过"推不出"L2 通过"。这正是题集存在的理由。

### 3.2 声明的可接受区间（摘要；完整表见 `references/CASE-SET.md` §1）

| 判据 | A | B | C |
|-|-|-|-|
| `status` | ∈ {success, partial} | ∈ {success, partial} | ∈ {success, partial}（表格无 rows ⇒ 必然 partial） |
| `slide_count` | **= 10** | **∈ [12, 13]**（理由见 §4.1） | **= 9** |
| 讲稿覆盖率 | ≥ 1.0 | ≥ 1.0 | ≥ 1.0 |
| 证据定位覆盖率 | ≥ 0.90 | ≥ 0.90 | ≥ 0.90 |
| 图表落位率 | ≥ 1.0 | ≥ 1.0 | ≥ 1.0 |
| CP3 门 / 顶层 null | = 8 / = 0 | = 8 / = 0 | = 8 / = 0 |
| 材料补位桶数 | — | — | **必须 6/6** |

区间写在 `examples/cases/case_manifest.json` 里，**由测量脚本对拍**：
超出区间报 `RANGE-MISS`；落在已声明上限且附了理由的报 `boundary-hit`
（两者都不算静默通过）。

### 3.3 `case.json` 的完整键清单（缺项是正常输入形态）

```
case_id / _meta / title / subtitle / authors / affiliation /
research_question / methods / results / discussion / limitations / conclusion /
key_numbers / figures / tables / audience / duration_minutes / slide_count /
language / template / starting_deck / source_material / output_contract
```

**L2 案例只给了 12 个键**（`case_id / _meta / title / subtitle / audience /
duration_minutes / slide_count / language / source_material / figures / tables /
output_contract`）—— 实测六个故事线桶仍全部非空，来源是 `material.md` 的小节标题。

## 4. ★ 泛化边界（实测，必读）

§3.2 的区间不是设计意图，是**真跑出来的**。三案共同点：`evidence_loc_frac` 全部 **1.000**、
CP3 门全部 **8/8**、顶层 `null` 全部 **0**、方案套用全部 **10/10、13/13、9/9 且偏差 0**。
退化只出现在下面两处，两处都**被审计抓到并降级**了。

### 4.1 页预算会被"带媒体的结果条目数"顶破（案例 B：声明 12，实测 13）

`deckplan.py` 的"每条结果一页"分支要求 `(target - fixed - 3) >= result_pages_needed`；
案例 B 该式为 `4 >= 7`，不成立 ⇒ 走另一分支，**每条带媒体的结果各占一页** ⇒ 结果页 7 张。
尾部裁剪是**一次性三步**（合并讨论+局限 → 删议程 → 合并末两页结果），**最多回收 3 页**，
不足以回到 12 ⇒ 实测 **13 页**，`status=partial`。

**这不是要修的 bug，是固定裁剪顺序的代价**：顺序固定换来可预测与可复跑，
代价是回收能力有上限。本包选择**如实多出一页并记录**，而不是偷偷丢证据页。
判别法：`main_result.planned_slides > target_slides`。规避法见 `references/CASE-SET.md` §4.1。

### 4.2 "只有表格、没有图"的结果页会丢掉它自己的主张条目

案例 B 第 8 页（只放表 1）页面上**没有**该页的主张条目，只有标题与表题行；
对照第 9 页（有图有表）条目正常。被 `audit.py` 的 `content.claim_coverage` 抓到：

```text
content.claim_coverage | warn | 1 claims not literally found; truncated: ['p8:表1 汇总不同温度下的 Li⁺ 电导']
```

⇒ `status=partial` + `uncertainty` 记一条。**本包未修改该版式路径**（见 §10 的改动纪律），
如实登记供使用方决定。

### 4.3 一页塞太多主张时，末尾主张会被文本框装不下而丢掉

案例 C 第 4 页把 6 条主张归到同一收集页，实际只写到第 4 条末尾就断了
（字号阶梯压到 12pt 地板后**只报告、不继续压**，见 D9/F12），后两条未上页。
同样由 `content.claim_coverage` 抓出（warn 报文里报 2 条）⇒ `partial`。

### 4.4 题集**没有**覆盖的（别把它当成泛化的全部证据）

跨模板族（三案全部 `opened_from=builtin`，未测多母版/商业模板族）· 真 PDF/像素级导出
（无 LibreOffice，只测到"有/无有效预览"）· 英文分支（三案均 `zh`）· 起始 deck 编辑
（三案都没给 `starting_deck`）· 上百行长材料 · 单页 3 张以上并排图。
完整清单与"题集不能用来做什么"见 `references/CASE-SET.md` §4.4–§4.5。

## 5. 决策规则 D1–D16（按"哪一层会命中它"组织）

规则号与 `references/failure-modes.md` 双向对应。下表右列标出**哪一层难度会命中它** ——
这也是"跑通 L0 不代表跑通 L2"的具体原因。

### 5.1 输入层（D1–D4）

| # | 触发条件 | 动作 | 失败时的降级 | 命中层 |
|-|-|-|-|-|
| **D1** | `--case` 不存在或不是合法 JSON | 立即停止，写 `status=failed` 的 result.json（`case_id` 取文件名词干），退出码 **1** | 不可降级；**绝不**用空壳 case 跑出"看起来像 PPT"的东西 | 任何层 |
| **D2** | 材料文件缺失 / 编码失败 / 非文本 | 以 `case.json` 结构化字段继续；缺失项进 `uncertainty`，来源标 `exists:false` | 结构化字段也为空时改走材料补位；仍**不编造内容**，状态 partial | **L2 的主路径** |
| **D3** | 材料是扫描件（无文本层） | 如实标注"图像型材料，未做 OCR"；有图仍按图清单引用 | 不引入任何编造的转写文本 | L2 |
| **D4** | 材料里的数值/结论没有 `文件:行` 定位 | 该条**不上页面**，进 `uncertainty` | 某页因此无主张 → 合并进相邻页并记 `change_records`，不保留空页 | 任何层 |

### 5.2 模板层（D5–D8）

| # | 触发条件 | 动作 | 失败时的降级 | 命中层 |
|-|-|-|-|-|
| **D5** | 案例既未给模板也未给起始 deck | 运行时现场生成 16:9 回退模板（真实母版/版式/占位符），`opened_from=builtin` 并进 `uncertainty` | 无 python-pptx → `ensure_builtin()` 返回原因字符串而非抛栈 | **三案都命中**（题集全部走回退模板） |
| **D6** | 模板 / 起始 deck 打不开（损坏、加密、格式不符） | 逐级回退 `case.template` → `starting_deck` → 运行时回退模板；**每级失败都进** `template_errors` | 全链失败 → `status=failed`，不静默用默认样式冒充"已套用" | 需模板的案例 |
| **D7** | 推荐版式缺该页型所需占位符（cover 要 title+subtitle；正文页要 title+body） | best-fit 选替代版式；仍缺角色就**手绘文本框**按计划几何落位 | 两条路径都写 `adopt_plan_deviations` / `layout_fallback_used`；偏差 > 0 时至少 partial | 模板族变化时 |
| **D8** | 主题读取失败（`theme1.xml` 不可读） | 主题字段只填 `theme.error`，**不影响构建** | 不猜测主题值 | 异常模板 |

### 5.3 版式与内容层（D9–D12b）

| # | 触发条件 | 动作 | 失败时的降级 | 命中层 |
|-|-|-|-|-|
| **D9** | 正文超出占位符真实几何 | 字号阶梯 32→28→24→20→18→16→14→**12**pt 逐级下调 | 落 12pt 仍溢出：**只报告不继续压**（`layout.overflow`）—— §4.3 就是这条的实测后果 | **L2** |
| **D10** | 标题单行超过容器估算宽度 | 先降号 | 仍超 → 按容器上限截断并记录 | 长标题案例 |
| **D11** | 计划页数 > `case.slide_count` | 固定顺序裁剪：合并 discussion+limitations → 删 agenda → 合并最后两张结果页 | **证据页（evidence_map）最后才动**；裁剪写 `change_records` —— §4.1 是它的数量上限 | **L1** |
| **D12** | 图表源文件缺失或嵌入抛异常 | 保留图位占位框（图号 + 标题 + 来源照写） | 灰底占位框，不伪造图形；`figure_adjust.placed=false` | 图件缺失时 |
| **D12b** | 正文引用图号 ∉ 图清单 | 记 `xref.figure_refs` warn | **保留原文引用不擅改编号** | 图号不一致时 |

### 5.4 交付与状态层（D13–D16）

| # | 触发条件 | 动作 | 失败时的降级 | 命中层 |
|-|-|-|-|-|
| **D13** | `output_contract` 的键在本 Skill 里没有天然对应值 | **已知语义的键先取本次运行真实值**（`preview_png` / `evidence_per_slide` / `notes_per_slide` / `template_inheritance` / `slide_count` / `audience` / `language`） | 其余按声明类型给 `""` / `[]` / `{}` / `0` / `false`；**禁止 null**；PDF 类键恒 `false` | 三案都命中 |
| **D14** | 无 LibreOffice / PowerPoint | 预览走 PIL 示意图：封面 + 全册联系表，文件名含 `schematic`，图内叠加免责声明 | **不产伪 PDF**；`preview_is_schematic=true` | **三案都命中** |
| **D15** | 预览字体探测全失败 | 回退 PIL 内置位图字体，按**文件名/索引**记录 | 日志不写本机路径 | 字体异常环境 |
| **D16** | 保存中途失败 / 流水线异常 | 先落盘已生成的部分产物，报错含已写路径，再写 `status=failed` | **绝不写半截 JSON**；`--out` 不可写时退出码 **2** | — |

### 5.5 状态判定（三档）

| 状态 | 判定条件 | 题集里的实例 |
|-|-|-|
| `success` | 全部审计检查 `ok` + CP3 G1–G8 全过 + 无任何降级条目 | A（`uncertainty` 非空但那是运行事实：内置模板现场生成） |
| `partial` | 出现任一 warn/fail，或命中任一降级分支 | **B 与 C**，两案的非 `ok` 检查都是 `content.claim_coverage`（见 §4.2/§4.3） |
| `failed` | 流水线未完成：D1 / D5(无 pptx) / D6(全链失败) / D16 | 题集未出现 |

## 6. 检查点与验收入口

| 检查点 | 时机 | 判据 | 不过怎么办 |
|-|-|-|-|
| **CP1** | 阶段一结束 | `adopt_plan.json.gates.ok == true`，或偏差逐条披露 | 先修方案；硬约束无法满足 → 继续 + 记录 + partial（D7） |
| **CP2** | 构建完成 | pptx 可重开 + 页数一致 + 每页有备注 | 记入 `verification.checks`，状态相应降级 |
| **CP3** | 交付前 | `check_contract.py` G1–G8 全过（exit 0） | 修产物或如实保留 warning；**绝不让失败伪装 success** |

```bash
python "$SKILL_DIR/scripts/validate_result.py" --case <case.json> --result <out>/result.json
python "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json \
    --out-dir <out> --case <case.json>
```

`check_contract.py` **从磁盘独立重扫**（自己重开 pptx、自己逐文件扫产物清单），
不信任 `result.json` 的自述；`exit 0` + `{"valid": true}` 才算 CP3 通过。

## 7. 产物清单与契约

| 文件 | 角色 |
|-|-|
| `<case_id>_deck.pptx` | 可编辑源：套版式/占位符、逐页主张+图表+讲稿备注、统一页脚页码 |
| `<case_id>_cover_preview.png` | 封面预览（PIL 示意图，命名与文件内均标注 SCHEMATIC） |
| `<case_id>_slides_contact_schematic.png` | 全册联系表（PIL 示意图） |
| `result.json` | **唯一评分产物**（契约见 `references/OUTPUT_CONTRACT.md`） |
| `adopt_plan.json` | 阶段一方案：模板审计 + 页→版式分配 + 批量规则 + 图表计划 |
| `spec.json` / `content.json` | 页结构方案 / 规范化抽取（含来源定位） |
| `audit.json` / `render_log.json` / `summary.txt` | 自查报告 / 渲染日志 / 摘要 |
| `_runtime/builtin.pptx` | 案例未给模板/起始 deck 时**运行时生成**的回退模板 |

字段契约**逐字**以 `references/OUTPUT_CONTRACT.md` 为准（顶层字段表 / `main_result` /
`template_audit` / `adopt_plan` / `verification` / CP3 G1–G8）。三案实测的顶层键数均为 **28**，
`artifacts` 均为 **8** 条，顶层 `null` 均为 **0**。

## 8. 按难度层自查

**通用（每层都查）**

- [ ] 读的是真实文件（case/task/材料/模板），不是凭标签假设内容
- [ ] 每条页级主张带 `claim → 文件名:行`；抽查 ≥3 条能在材料中找到
- [ ] `result.json` 覆盖契约全部字段，**顶层 null 个数为 0**
- [ ] `check_contract.py` exit 0 + `{"valid": true}`（CP3）；pptx 可重开且页数 = 计划（CP2）
- [ ] 逐页 speaker notes 非空；页脚/页码自封面之后全册一致
- [ ] 图号交叉引用通过；图表等比（`figure_adjust` 无拉伸记录）
- [ ] 输出目录内**没有本机绝对路径**（记录一律是运行相对路径或环境路径）
- [ ] 状态词汇诚实：有降级就不是 `success`

**L0 额外**：`slide_count` 精确等于案例声明 —— 它是回归基线，**不允许**有页数漂移。

**L1 额外**：若 `main_result.planned_slides > target_slides`，必须能在
`references/CASE-SET.md` §4.1 找到原因；页数落在声明区间内并在回报里点明是 `boundary-hit`。

**L2 额外**：确认 `content.json.supplemented_from_material` 的六个桶**全部为真**
（题集要求 6/6）；若某桶为空，先检查材料的小节标题是否含分桶关键词，**不要**去改区间。

## 9. 目录结构与资源形态

```
<skill root>/                      # = $SKILL_DIR（平台装到 /skills/weekly-skill）
  SKILL.md                本文档（题集驱动 + 泛化边界 + D1–D16 + CP1–CP3）
  README.md               使用说明 / 依赖 / 题集入口 / 限制 / 维护
  TEST.md                 本地实测记录（冒烟 / 确定性 / 鲁棒性 / 题集）
  GITHUB_URL.txt          GitHub 公开链接
  references/
    OUTPUT_CONTRACT.md    result.json 结构与字段契约 + CP3 G1–G8（必读）
    RUBRIC_MAP.md         评分五维 → 设计覆盖映射
    CASE-SET.md           ★ 题集：三案输入/区间/逐案实测 + 泛化失效边界（本版重点）
    failure-modes.md      失败模式与降级策略
    template_guide.md     模板使用指南（母板/版式/占位符/主题/字号阶梯）
    checklist.md          收尾验收清单
    batch-rules.md        批量一致性规则 R1–R8
    two-phase-workflow.md 两阶段工作流图示与分步命令
  scripts/
    main.py               编排入口（一条命令跑完两阶段；CP1/CP3 门）
    run_case_set.py       ★ 题集运行器：跑满三案并与声明区间对拍
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
  examples/               最小示例 + 题集（合成数据，非正式案例）
    case.json / task.md / material.md / minimal_example.md
    plan.sample.json / adopt_plan.sample.json     方案样例（真实运行，标注示例）
    EXPECTED-OUTPUT.md                            应产出的文件清单与契约字段
    cases/                ★ 题集：case-b-… / case-c-… 两个新题材案例
      case_manifest.json  每案的难度层与可接受区间（测量脚本据此对拍）
    output/               示例运行的**文本**产物（result/summary/render_log）
```

题面硬约束 *at most 50 UTF-8 text files, 500KB each and 2MB total, no symlinks*
⇒ 本包**只含文本资源**，全部二进制改为运行时生成：

| 资源 | 处置 | 入口 |
|-|-|-|
| 回退模板 `.pptx` | 不随包；案例给模板时用真实文件，都缺时**现场生成**（16:9，真实母版/版式/占位符） | `scripts/make_template.py`（`ensure_builtin()`；也可单跑 `--out <dir>/builtin.pptx`） |
| 案例/示例输入图 `.png` | 不随包；运行前**现场合成**纯几何占位图（带 `SCHEMATIC / 示意` 水印，不含伪造数值） | `scripts/make_synthetic_inputs.py --dir <案例目录>` 或 `--out-dir <figs 目录>` |
| 预览 `.png` / 产物 `.pptx` | 运行时生成，写入 `--out` | `scripts/main.py` |
| 字体 `.ttf/.otf` | 不随包；运行时按标准字体目录探测（Windows 目录取自环境变量 `WINDIR`/`SystemRoot`，另有 `/usr/share/fonts`、`/System/Library/Fonts` 等候选），找不到回退 PIL 内置位图字体 | `scripts/common.py`（`font_dirs()` / `probe_font_candidates()`） |
| SVG 图元 | 不随包；本 Skill 不使用矢量模板，预览为 PIL 位图 | — |

脚本不硬编码绝对路径：`scripts/common.py` 用 `os.path.dirname(__file__)` 自定位；
所有真实 I/O 路径由命令行显式给出（官方运行时为 `/input`、`/app/work`、`/app/output`）；
**写进 JSON 的路径一律是便携形式**（运行相对路径 / 正斜杠）。

> **两条跑脚本的纪律**：① **永远不要在包内跑**（会在 `scripts/__pycache__` 留下
> `.pyc`，那是平台拒绝的资源类型）；`run_case_set.py` 会**主动拒绝**把工作目录设在包内。
> ② 题集运行会**先复制再跑**，所以它不会污染案例目录。

## 10. 维护

- 版本常量：`scripts/common.py` 的 `SKILL_VERSION`
- 分层约定：素材/抽取 `extract.py`，页结构方案 `deckplan.py`，阶段一方案 `adopt_plan.py`，
  阶段二构建 `adapt_pptx.py`，PPTX 底层 `pptx_toolkit.py`，验证 `audit.py` +
  `validate_result.py` + `check_contract.py`，二进制资源生成 `make_template.py` +
  `make_synthetic_inputs.py`，题集运行 `run_case_set.py`
- **新增案例时同步做三件事**：① 放好 `case.json` / `task.md` / `material.md`；
  ② 在 `examples/cases/case_manifest.json` 加一条（难度层 + 期望产出结构 + 可接受区间 +
  这案在考什么）；③ 真跑 `run_case_set.py` 并把实测数字补进 `references/CASE-SET.md` §2。
  **没有实测数字的案例不算题集成员。**
- **改动纪律（本包沿用）**：既有 `scripts/*.py` 尽量逐字节不变；确需修真实缺陷只允许
  **纯增量**并逐条点名（文件、增删行数、理由），**CLI 参数名/默认值/退出码语义不得改**。
  本轮据此**没有**修改 `adapt_pptx.py` 的版式路径 —— §4.2/§4.3 的行为因此是
  "已检出、已降级、未修复"，如实登记在 `references/CASE-SET.md` 里。
- 改动后至少复跑题集（`run_case_set.py`）与 `TEST.md` §1 冒烟、§2 确定性；
  **若区间需要变动，必须像 §4.1 那样附上可复现的理由与实测上限，不得靠改宽区间掩盖实测。**
- 交付前跑包外验收：`python validate_pkg.py <包目录>`（扩展名白名单、≤50 文件、
  ≤500KB/个、≤2MB、无 `__pycache__`、无绝对路径、`py_compile`）。
