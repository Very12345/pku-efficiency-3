---
name: academic-slide-adapt
description: >-
  Academic slide deck creation from research material with real template
  adaptation (学术 PPT 模板与格式适配): read the actual paper/material and
  template files, extract the research storyline (question → method →
  results → limitations) with per-item source locators, plan a page structure
  that respects a fixed audience/duration/slide count, then follow a
  two-phase workflow — phase 1 builds a machine-readable adaptation plan
  (adopt_plan: template master/layout/placeholder audit + page→layout
  assignment + batch rules + figure placement), phase 2 applies the plan
  through the given PowerPoint template's real placeholder inheritance
  (falling back with full disclosure when placeholders are missing), embed
  figures/tables contain-fit with figure numbers cross-checked against the
  text, add per-slide speaker notes plus an appendix evidence map, and
  deliver an editable .pptx, PNG previews and a verifiable result.json
  (CP3 gate: check_contract G1–G8). Use when the task says "make an academic
  presentation / 学术PPT / 学术汇报 / 论文转PPT / adapt this paper into
  slides / 套模板 / 模板适配 / 按模板生成PPT / deck from paper", or when a
  starting deck must be re-edited on its own template.
---

# Academic Slide Adapter（学术 PPT 模板与格式适配）Skill — slides 组（v2）

把论文/研究材料组织成**结构清楚、证据可追溯、可编辑、符合模板要求**的学术
汇报：从封面到结论逐页讲清主线，每页带着主张、图表引用与讲稿，并附「页 →
论文位置」证据映射附录。**对版式科学负责**：模板是否真实套用（母版/版式/
占位符继承可查）、页内内容与源论文与图表是否对得上、阶段一方案与阶段二
执行是否一致、整册能否被他人按记录复跑并逐页核对。

- Skill 版本：`2.0.0`（v2：两阶段工作流 + 检查点 CP1–CP3 + 决策规则 D1–D12）
- Skill 根：本文件所在目录（下文所有相对路径均相对 Skill 根）
- 核心入口：`scripts/main.py`（一条命令完成两阶段全流程）

**执行顺序（先方案，后执行，最后自评）**：
**① 读 `references/OUTPUT_CONTRACT.md`**（交付什么、必须回显哪些字段、G1–G8 门）
→ **② 读真实文件 + 抽取（extract）→ 页结构方案（deckplan）→ 适配方案
（adopt_plan，CP1 门）** → **③ 按方案构建（adapt_pptx，CP2 门）→ 预览 → 审计
→ result.json** → **④ CP3 契约门（check_contract G1–G8）→ ⑤ 按
`references/RUBRIC_MAP.md` 五维自评**。

---

## 1. 用途与适用条件

**适用**：给定论文/实验材料要求产出学术汇报幻灯片，且要求可编辑 pptx、
渲染预览和可复核来源；尤其适用于"必须套用指定模板/在起始 deck 上改编"的
场景。读取**真实文件**，绝不凭文件名/标签猜内容。

**适用输入形态**（至少其一）：

| 输入 | 说明 |
|-|-|
| `case.json` | 必读。`case_id / title / subtitle / authors / affiliation / research_question / methods / results / discussion / limitations / conclusion / figures / tables / audience / duration_minutes / slide_count / language / template / starting_deck / source_material / output_contract`（均可省略，缺项走材料抽取或默认值） |
| `task.md` | 任务说明：受众、时长、页数、交付要求；`# 背景/方法/结果/结论` 小节会被抽取 |
| 材料文件 | `source_material` 指明的 md/txt/tex/csv 等；提供主张与数值的真正来源（`文件:行` 定位） |
| 模板 | `template` 指明的 `.pptx`（或 `--template` 显式指定）；缺省用 Skill 内置回退模板 `templates/builtin.pptx` |
| 起始 deck | `starting_deck` 指明的 `.pptx`（在其上改编：沿用母版/版式/主题，替换页面内容，记录 change_records） |
| `output_contract` | 案例自带的交付契约；每个字段原样进 `result.json` 顶层（四形态回显，禁止 null） |

**不适用/明确边界**：本 Skill 不代写科学内容（材料中没有的数值绝不补造）、
不做动画/切换效果、不改写模板主题 XML（仅只读记录主题字体/色）；预览在无
LibreOffice/PPT 环境为 PIL 示意图（如实标注，不冒充像素级导出）。

## 2. 输入与输出

**输入路径约定（Runtime contract）**：官方案例运行时 `/input/case.json` 与
`task.md` 由平台挂载，材料按案例提供；在 `/app/work` 内解析相对路径。
本机/任意环境：`--case <case.json>` 显式指定。脚本均以自身文件目录
（`os.path.dirname(__file__)`）自定位 Skill 根，不依赖 cwd。

**输出**：全部写到 `--out` 指定目录（官方约定 `/app/output`）：

| 文件 | 内容 |
|-|-|
| `<case_id>_deck.pptx` | **可编辑源**：按两阶段方案套用版式/占位符，逐页主张/图表/讲稿备注，统一页脚页码 |
| `<case_id>_cover_preview.png` | 封面预览（PIL 示意图，命名与文件内标注 SCHEMATIC） |
| `<case_id>_slides_contact_schematic.png` | 全册联系表（PIL 示意图） |
| `result.json` | **结构化结果**（契约见 `references/OUTPUT_CONTRACT.md`） |
| `spec.json` / `content.json` | 页结构方案 / 规范化抽取（含来源定位） |
| **`adopt_plan.json`** | **适配方案（v2）**：模板结构审计 + 页→版式分配 + 批量规则 + 图表放置计划（阶段一产物） |
| `audit.json` / `render_log.json` / `summary.txt` | 自查报告 / 渲染日志 / 摘要 |

## 3. 两阶段执行步骤（含检查点 CP1–CP3）

主入口：`python scripts/main.py --case <case.json> [--task <task.md>]
[--work <材料基目录>] [--template <模板.pptx>] [--starting-deck <deck.pptx>]
--out <输出目录>`；分步命令与图示见 `references/two-phase-workflow.md`。
作为 Agent，你**必须**在调用脚本之外阅读真实文件并复核抽取/落版，偏差写进
`result.json` 的 `change_records` / `uncertainty`。**不得用预制答案替代实际
运行。**

### 阶段一：适配方案（PLAN）

**步骤 1 —— 读实际文件（不要凭标签猜内容）**
1. 读取 `case.json`（UTF-8）与 `task.md`；失败即报错退出并说明，不留虚假产物；
2. 解析 `source_material` 相对路径，逐个读取材料原文，逐行编号
   （`extract.py`，`content.json` 每个条目带 `文件:行` 来源）；
3. 定位模板/起始 deck：`case.json["template"]` → `case.json["starting_deck"]`
   → 内置 `templates/builtin.pptx`；打不开就回退下一级并记录 `template_errors`。

**步骤 2 —— 页结构方案（确定性、受页数约束）**
运行 `deckplan.py`：cover→background→methods→results×N（每图/表一页）→
discussion→limitations→conclusion→evidence_map 附录→thankyou（agenda 可选，
页数充裕时插入）；超页时按确定性裁剪：合并讨论+局限 → 删议程 → 合并最后两张
结果页。每页给出**页级主张 claims、图表引用 figure_refs/table_refs、讲稿
notes（含建议时长）、证据 evidence[{claim, loc}]**。

**步骤 3 —— 适配方案（模板审计 + 页→版式分配）+ 检查点 CP1**
运行 `adopt_plan.py`：
- 打开真实模板，枚举**母版 / 版式 / 占位符（idx/name/宽高）/ 画布尺寸 /
  主题字体与主题色**（读 `ppt/theme/theme1.xml`，尽力而为）；
- 逐页按页型（cover/thankyou 需 title+subtitle，其余需 title+content body，
  `text` 类侧栏不算 body）打版式分、给出 `recommended_layout_idx`；
- 评估**批量规则**（页脚/页码/标题位置/字号阶梯/图表缩放，见
  `references/batch-rules.md`），偏差全部进 `batch.deviations`（不隐藏）；
- 产出**图表放置计划**（每图所在页、容器尺寸、contain-fit 比例预览）；
- **★ CP1（方案门）**：`adopt_plan.json.gates`（G1 模板可开 / G2 版式已枚举 /
  G3 每页有版式 / G4 批量偏差已披露）。不平衡时**先修方案；确属案例硬约束
  无法满足 → 按 D4 继续但显式记录，status 降 partial**。

### 阶段二：执行与验证（EXECUTE）

**步骤 4 —— 按方案生成可编辑 pptx（模板适配层）+ 检查点 CP2**
运行 `adapt_pptx.py`（消费 `adopt_plan.json`）：
- 每页优先套用方案推荐的版式（`plan_source=adopt_plan`）；推荐版式缺所需
  占位符时 best-fit 替代并记入 `adopt_plan_deviations`（绝不静默改变）；
- 内容写进占位符→**继承模板主题字体/颜色**；缺占位符→手绘文本框回退并记录；
- 字号阶梯（32→12pt）按占位符真实几何估算换行，溢出只降字号、最低 12pt，
  再溢出就报告，绝不压到不可读；
- 图表等比 contain-fit（不拉伸），图注 `图N 标题 [来源: …]`；表格原生 table；
- 封面外统一页脚+页码；逐页写 speaker notes（主张/证据/建议时长）；
- **★ CP2**：构建后 pptx 可被 python-pptx 重开（`pptx.reopen`）、页数与
  spec.json 一致、逐页备注存在（audit 检查）。

**步骤 5 —— 导出渲染件（诚实标注）**
运行 `preview.py`：无 LibreOffice 时产出 **PIL 示意图**封面 + 全册联系表，
文件命名含 `schematic`、叠加免责声明、`render_log.json` 记录渲染后端与字体
探测；**PDF 导出能力缺失如实记录，不产伪 PDF**。

**步骤 6 —— 自查（audit）+ 写 result.json**
- 运行 `audit.py` 在**真实产物**上检查：pptx 重开、页数与计划一致、计划主张
  出现在页面上、图号交叉引用一致、逐页备注齐全、无溢出/字号落底、页脚页码
  一致、PNG 有效、证据定位覆盖率≥90%、**方案↔执行一致性
  （adopt_plan.consistency）**；
- 写 `result.json`：`output_contract` 全部字段镜像进顶层（四形态、禁止 null）
  + 信封字段（case_id/status/main_result/artifacts/slide_evidence/
  template_audit/adopt_plan/verification/sources/uncertainty/change_records/
  generated_at/…）；`status`：全绿=success；有 warn/fail=partial（必须写明
  限制）；管线未完成=failed。

**步骤 7 —— CP3 契约门 + 人工复核**
- **★ CP3（交付门）**：独立运行 `scripts/check_contract.py`（G1–G8，exit 0
  才算通过；main.py 内嵌执行并把结果写进 `verification.contract_gates`）；
- 打开 PNG 目视：封面主标题/副标题/作者单位、联系表每页标题与主张无乱码；
  打开 pptx：版式继承、图表不拉伸、页脚页码一致、备注可读；
- 同输入重跑一次：`spec.json`/`adopt_plan.json`/pptx/PNG 逐字节一致，
  `result.json` 仅 `generated_at` 差异（`TEST.md` §2 实测记录）；
- 复核证据映射：抽查 ≥3 条 `claim → 文件:行` 能在材料里找到；
- 人工确认与修改写进 `change_records`，再按 `references/RUBRIC_MAP.md`
  五维逐条自评。

## 4. 决策规则（D1–D12；覆盖材料异常 / 模板异常 / 状态一致性）

| # | 情形 | 决策（做什么 | 记录在哪） |
|-|-|-|-|
| D1 | `case.json` 缺失/不可解析 | 立即失败（exit 1）并说明原因，不产半成品冒充成功 | stderr |
| D2 | 材料缺失/不可读 | 以 case.json 结构化字段继续；缺失项进 uncertainty，**绝不编造** | `uncertainty` + `sources` |
| D3 | 材料无文本层（扫描件） | 不 OCR 冒充；如实标注"图像型材料" | `uncertainty` + `sources` |
| D4 | **CP1 方案门有偏差**（版式缺口/批量偏差） | 先修方案；确属案例硬约束无法满足 → 继续但**显式记录偏差**，status 降 partial | `adopt_plan.gates` + `uncertainty` |
| D5 | 图/表抽不出 | 页面保留**显式占位框**（标注"需补齐，非原图"），不伪造 | `figure_adjust`(placed=false) + `uncertainty` |
| D6 | 模板缺失/损坏/全链失败 | 回退链 case→starting deck→内置；全链失败 → **status=failed** 不静默冒充 | `template_audit` + result.json(status) |
| D7 | 方案↔执行不一致 / 主题读失败 | best-fit 替代并逐条记录偏差；主题仅记录 error | `adopt_plan_deviations` + `theme.error` |
| D8 | 文本框溢出 | 字号阶梯只降到 12pt，仍溢出则报告；绝不压到不可读 | `layout.overflow` / `font_floor` |
| D9 | 页数超限 | 确定性裁剪并记录；绝不静默丢弃证据页（优先合并非证据页） | `change_records` + `uncertainty` |
| D10 | 契约字段未知/无值 | 按四形态给类型对应空值 `""/[]/{}/0/false`，**禁止 null**；语义字段取本次运行真实值 | result 顶层回显 |
| D11 | 字体缺失 / 无 LibreOffice | PIL 字体回退链 + 如实记录；不产伪 PDF，预览标注 SCHEMATIC | `render_log.json` + `preview_is_schematic` |
| D12 | 保存失败/流水线异常 | 先落盘已生成的部分产物，报错含已写路径；写 `status=failed` 的 result.json，工作不丢失 | stderr / result.json |

## 5. 异常处理（失败模式表）

完整 20 项对照表见 **`references/failure-modes.md`**；要点（每项含识别→处置→
记录→D#）：

| 情形 | 处置 | 记录位置 |
|-|-|-|
| `case.json` 缺失/不可解析 | 立即失败（D1） | stderr |
| 模板缺失/打不开 | 回退链 + 原因记录；全链失败写 failed result（D6） | `template_audit.template_errors` / `template_fallback_used` |
| 版式缺所需占位符 | 手绘文本框按计划几何落位，记录 fallback（D6） | `template_audit.layout_fallback_used` |
| 方案推荐版式不可用 | best-fit + 偏差记录（D7） | `template_audit.adopt_plan_deviations` |
| 材料/数值缺失 | 以现有材料继续；缺失项进 uncertainty，**绝不编造**（D2） | `uncertainty` + `audit` |
| 文本框溢出 | 字号阶梯只降到 12pt，仍溢出则报告（D8） | `audit.layout.overflow / font_floor` |
| 源图文件缺失/嵌入失败 | 灰底图位占位框（图号+标题+来源保留）（D5） | `uncertainty` + `figure_adjust` |
| 字体缺失（预览渲染） | PIL 字体回退链（msyh→simhei→默认），字体名如实记录（D11） | `render_log.json` + `uncertainty` |
| 导出失败/无 LibreOffice | 不产伪 PDF；预览标注 SCHEMATIC，能力缺失如实说明（D11） | `render_log.json` + `preview_is_schematic` |
| 保存中途失败 | 先落盘部分产物，报错含已写路径；写 failed result.json（D12） | stderr / `result.json(status=failed)` |

## 6. 自查清单（每次运行后逐项确认）

- [ ] 读取的是真实文件（case.json/task.md/材料/模板），不是凭标签假设内容
- [ ] 阶段一方案存在且门通过或偏差已记录：`adopt_plan.json.gates.ok` 或
      `uncertainty` 写明（CP1）
- [ ] 模板被真实套用：`template_audit.layouts/layout_used/adopt_plan_applied`
      记录了母版/版式/占位符继承关系，可查（抽查页型对应的版式名）
- [ ] 每页主张带 `claim→文件名:行` 定位；抽查 ≥3 条能在材料中找到
- [ ] 图号与正文引用一致（xref 通过）；图表等比放入（figure_adjust 无拉伸）
- [ ] 逐页 speaker notes 存在；页脚/页码全册一致（batch-rules R1/R2）
- [ ] `result.json` 含 `output_contract` 全部字段 + case_id + status +
      sources + uncertainty + change_records；无 null 占位（四形态）
- [ ] `check_contract.py` G1–G8 全过、exit 0（CP3）
- [ ] pptx 可被 python-pptx 重开、页数=计划（CP2）；同输入重跑仅时间戳差异
- [ ] 预览 PNG 存在且非空白；渲染后端/字体回退在 `render_log.json` 如实记录
- [ ] 未有「看起来热闹但无来源」的装饰性页面/数据

## 7. 目录结构

```
<skill root>/
  SKILL.md                本文档（两阶段工作流 + CP1–CP3 + D1–D12）
  README.md               使用说明 / 依赖 / 限制 / 失败处理
  TEST.md                 本地实测记录（确定性/鲁棒性/对照）
  COMPARE.md              三方对照（build vs 高分 vs v2）+ 增强点
  GITHUB_URL.txt          GitHub 公开链接占位（发布代理覆写）
  references/
    OUTPUT_CONTRACT.md    result.json 结构与字段契约 + CP3 G1–G8（必读）
    RUBRIC_MAP.md         评分五维 → 设计覆盖映射（交付前自评）
    template_guide.md     模板使用指南（母板/版式/占位符/主题字体色/字号阶梯）
    checklist.md          适配检查清单（收尾验收，逐项勾选）
    batch-rules.md        批量一致性规则（R1–R8）
    two-phase-workflow.md 两阶段工作流图示与分步命令
    failure-modes.md      失败模式表（20 项，与 D 规则配套）
  scripts/
    main.py               编排入口（一条命令两阶段；CP1/CP3 门）
    extract.py            主张/图/表/数值抽取（来源定位）
    deckplan.py           确定性页结构方案（页型/裁剪/证据映射）
    adopt_plan.py         ★阶段一：模板审计 + 页→版式分配 + 批量规则 + 图表计划
    adapt_pptx.py         ★阶段二：按方案模板适配 + pptx 生成
    preview.py            PIL 示意图预览（封面+联系表，诚实标注）
    audit.py              真实产物自查（重开/覆盖/图号/溢出/页脚/方案一致性）
    validate_result.py    result.json 契约校验（VALID, exit 0）
    check_contract.py     ★CP3 契约门（G1–G8 独立复查，exit 0）
    pptx_toolkit.py       共享 PPTX 工具（版式打分/占位符/contain-fit/主题/确定zip）
    make_template.py      内置回退模板再生成
    common.py             公共工具（路径自定位/字号阶梯/字体/颜色/哈希）
  templates/
    builtin.pptx          内置回退模板（16:9，真实母版/版式/占位符）
  examples/
    case.json / task.md / material.md / figs/     最小示例输入（合成数据，非正式案例）
    plan.sample.json / adopt_plan.sample.json     适配方案样例（由真实运行生成，标注示例）
    minimal_example.md    最小示例说明
    output/*              示例输出（标注「示例，非正式案例」）
```

脚本不硬编码绝对路径：`scripts/common.py` 用 `os.path.dirname(__file__)`
自定位 Skill 根；所有输入输出路径由命令行显式给出（官方运行时为
`/input`、`/app/work`、`/app/output`）。

## 8. 维护

- 版本：`scripts/common.py` 内 `SKILL_VERSION`（v2 = 2.0.0）；
- 分层约定：素材/抽取在 `extract.py`，页结构方案在 `deckplan.py`，阶段一
  方案在 `adopt_plan.py`，阶段二构建在 `adapt_pptx.py`，PPTX 底层细节在
  `pptx_toolkit.py`，验证在 `audit.py` + `validate_result.py` +
  `check_contract.py`；
- 改动后至少复跑 `TEST.md` §1 冒烟与 §2 确定性，确认全绿再交付；
- 内置模板为 Skill 资源（二进制，不计入文本文件限额），可从
  `scripts/make_template.py` 再生成。