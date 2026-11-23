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
  starting deck must be re-edited on its own template. Ships with a
  runnable byte-reproducibility probe: scripts/determinism.py re-runs the
  real pipeline 16 times across separate OS processes, three working
  directories, four PYTHONHASHSEED values and relative-vs-absolute argument
  forms, hashes every produced file, and reports which JSON field paths
  differ and whether each one is a declared wall-clock stamp, a declared
  host anchor or an undeclared defect (references/DETERMINISM.md).
---

# Academic Slide Adapter（学术 PPT 模板与格式适配）Skill — slides 组

把论文/研究材料组织成**结构清楚、证据可追溯、可编辑、符合模板要求**的学术
汇报：从封面到结论逐页讲清主线，每页带着主张、图表引用与讲稿，并附「页 →
论文位置」证据映射附录。**对版式科学负责**：模板是否真实套用（母版/版式/
占位符继承可查）、页内内容与源论文与图表是否对得上、阶段一方案与阶段二
执行是否一致、整册能否被他人按记录复跑并逐页核对。

- Skill 版本：`2.0.0`（两阶段工作流 + 检查点 CP1–CP3 + 决策规则 D1–D12）
- **Skill 根 = 本文件所在目录**；下文所有 `$SKILL_DIR` 都指它，命令在**任意
  cwd** 下都能跑（脚本用 `os.path.dirname(__file__)` 自定位，不依赖 cwd）
- 核心入口：`$SKILL_DIR/scripts/main.py`（一条命令完成两阶段全流程）
- **资源形态**：本包**只含 UTF-8 文本文件**（`.md/.py/.json/.txt`），≤50 个、
  单文件 ≤500KB、合计 ≤2MB、无符号链接；模板/图片/预览等二进制一律**运行时
  生成**（§9）

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
| 模板 | `template` 指明的 `.pptx`（或 `--template` 显式指定）；缺省回退到**运行时生成**的内置 16:9 回退模板（§9，不随包分发二进制） |
| 起始 deck | `starting_deck` 指明的 `.pptx`（在其上改编：沿用母版/版式/主题，替换页面内容，记录 change_records） |
| `output_contract` | 案例自带的交付契约；每个字段原样进 `result.json` 顶层（四形态回显，禁止 null；已知语义的键取本次运行真实值，见 `references/OUTPUT_CONTRACT.md`） |

**不适用/明确边界**：本 Skill 不代写科学内容（材料中没有的数值绝不补造）、
不做动画/切换效果、不改写模板主题 XML（仅只读记录主题字体/色）；预览在无
LibreOffice/PPT 环境为 PIL 示意图（如实标注，不冒充像素级导出）。

## 2. 输入与输出

**输入路径约定（Runtime contract）**：官方案例运行时 `/input/case.json` 与
`task.md` 由平台挂载，材料按案例提供；在 `/app/work` 内解析相对路径。
本机/任意环境：`--case <case.json>` 显式指定，`--work <材料基目录>` 可选。
脚本均以自身文件目录（`os.path.dirname(__file__)`）自定位 Skill 根，**不依赖
cwd**；所有真实 I/O 路径都由命令行给出。

**输出**：全部写到 `--out` 指定目录（官方约定 `/app/output`）：

| 文件 | 内容 |
|-|-|
| `<case_id>_deck.pptx` | **可编辑源**：按两阶段方案套用版式/占位符，逐页主张/图表/讲稿备注，统一页脚页码 |
| `<case_id>_cover_preview.png` | 封面预览（PIL 示意图，命名与文件内标注 SCHEMATIC） |
| `<case_id>_slides_contact_schematic.png` | 全册联系表（PIL 示意图） |
| `result.json` | **结构化结果**（契约见 `references/OUTPUT_CONTRACT.md`） |
| `spec.json` / `content.json` | 页结构方案 / 规范化抽取（含来源定位） |
| **`adopt_plan.json`** | **适配方案**：模板结构审计 + 页→版式分配 + 批量规则 + 图表放置计划（阶段一产物） |
| `audit.json` / `render_log.json` / `summary.txt` | 自查报告 / 渲染日志 / 摘要 |
| `_runtime/builtin.pptx` | 案例未给模板/起始 deck 时**现场生成**的回退模板（已给模板时不使用、不产生） |

## 3. 两阶段执行步骤（含检查点 CP1–CP3）

主入口（**命令与 `scripts/` 实际入口逐字一致**；`$SKILL_DIR` 为本包根目录，
任意 cwd 均可）：

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

**先跑通示例（可选，验证环境）**：示例图不在包内（资源只允许文本），先合成再跑：

```bash
SKILL_DIR=<本包根目录>; RUN=<任意可写目录>
cp -r "$SKILL_DIR/examples" "$RUN/examples"
python "$SKILL_DIR/scripts/make_synthetic_inputs.py" --dir "$RUN/examples"
python "$SKILL_DIR/scripts/main.py" --case "$RUN/examples/case.json" \
    --task "$RUN/examples/task.md" --out "$RUN/out"
```

分步命令与图示见 `references/two-phase-workflow.md`。作为 Agent，你**必须**在
调用脚本之外阅读真实文件并复核抽取/落版，偏差写进 `result.json` 的
`change_records` / `uncertainty`。**不得用预制答案替代实际运行。**

### 阶段一：适配方案（PLAN）

**步骤 1 —— 读实际文件（不要凭标签猜内容）**
1. 读取 `case.json`（UTF-8）与 `task.md`；失败即报错退出并说明，不留虚假产物；
2. 解析 `source_material` 相对路径，逐个读取材料原文，逐行编号
   （`extract.py`，`content.json` 每个条目带 `文件:行` 来源与材料 sha256）；
3. 定位模板/起始 deck：`case.json["template"]` → `case.json["starting_deck"]`
   → 运行时生成的内置回退模板（§9）；打不开就回退下一级并记录
   `template_errors`。

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
- 起始 deck 模式下：**旧页连关系一起移除**（不留旧页残件），页数与计划一致，
  替换过程写 `change_records`；
- **★ CP2**：构建后 pptx 可被 python-pptx 重开（`pptx.reopen`）、页数与
  spec.json 一致、逐页备注存在（audit 检查）。

**步骤 5 —— 导出渲染件（诚实标注）**
运行 `preview.py`：无 LibreOffice 时产出 **PIL 示意图**封面 + 全册联系表，
文件命名含 `schematic`、叠加免责声明、`render_log.json` 记录渲染后端与实际
解析到的字体；**PDF 导出能力缺失如实记录，不产伪 PDF**。

**步骤 6 —— 自查（audit）+ 写 result.json**
- 运行 `audit.py` 在**真实产物**上检查：pptx 重开、页数与计划一致、计划主张
  出现在页面上、图号交叉引用一致、逐页备注齐全、无溢出/字号落底、页脚页码
  一致、PNG 有效、证据定位覆盖率≥90%、**方案↔执行一致性
  （adopt_plan.consistency）**；
- 写 `result.json`：`output_contract` 全部字段镜像进顶层（四形态、禁止 null；
  已知语义的键取**本次运行真实值**并记在 `verification.contract_echo_derived`）
  + 信封字段（case_id/status/main_result/artifacts/slide_evidence/
  template_audit/adopt_plan/verification/sources/uncertainty/change_records/
  generated_at/…）；`status`：全绿=success；有 warn/fail=partial（必须写明
  限制）；管线未完成=failed。

**步骤 7 —— CP3 契约门 + 人工复核**
- **★ CP3（交付门）**：独立运行 `scripts/check_contract.py`（G1–G8，exit 0
  才算通过；main.py 内嵌执行并把结果写进 `verification.contract_gates`）：

```bash
python "$SKILL_DIR/scripts/validate_result.py" --case <case.json> --result <out>/result.json
python "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json \
    --out-dir <out> --case <case.json>
```

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
| D6 | 模板缺失/损坏/全链失败 | 回退链 case→starting deck→**运行时生成的内置模板**；全链失败 → **status=failed** 不静默冒充 | `template_audit` + result.json(status) |
| D7 | 方案↔执行不一致 / 主题读失败 | best-fit 替代并逐条记录偏差；主题仅记录 error | `adopt_plan_deviations` + `theme.error` |
| D8 | 文本框溢出 | 字号阶梯只降到 12pt，仍溢出则报告；绝不压到不可读 | `layout.overflow` / `font_floor` |
| D9 | 页数超限 | 确定性裁剪并记录；绝不静默丢弃证据页（优先合并非证据页） | `change_records` + `uncertainty` |
| D10 | 契约字段未知/无值 | 已知语义的键取本次运行真实值（如 `preview_png`/`evidence_per_slide`/`notes_per_slide`/`template_inheritance`）；未知键按四形态给 `""/[]/{}/0/false`，**禁止 null**；PDF 导出类键恒 false | result 顶层回显 + `verification.contract_echo_derived` |
| D11 | 字体缺失 / 无 LibreOffice | 按标准字体目录探测（失败再扫描 CJK 字体文件）→ PIL 内置位图字体；如实记录；不产伪 PDF，预览标注 SCHEMATIC | `render_log.json` + `preview_is_schematic` |
| D12 | 保存失败/流水线异常 | 先落盘已生成的部分产物，报错含已写路径；写 `status=failed` 的 result.json，工作不丢失 | stderr / result.json(status=failed) |

## 5. 异常处理（失败模式表）

完整对照表见 **`references/failure-modes.md`**；要点（每项含识别→处置→
记录→D#）：

| 情形 | 处置 | 记录位置 |
|-|-|-|
| `case.json` 缺失/不可解析 | 立即失败（D1） | stderr |
| 模板缺失/打不开 | 回退链 + 原因记录；全链失败写 failed result（D6） | `template_audit.template_errors` / `template_fallback_used` |
| 案例未给模板（用内置回退） | 运行时生成 16:9 回退模板并如实记录；版式继承照常审计 | `template_audit.opened_from=builtin` + `uncertainty` |
| 版式缺所需占位符 | 手绘文本框按计划几何落位，记录 fallback（D6） | `template_audit.layout_fallback_used` |
| 方案推荐版式不可用 | best-fit + 偏差记录（D7） | `template_audit.adopt_plan_deviations` |
| 材料/数值缺失 | 以现有材料继续；缺失项进 uncertainty，**绝不编造**（D2） | `uncertainty` + `audit` |
| 文本框溢出 | 字号阶梯只降到 12pt，仍溢出则报告（D8） | `audit.layout.overflow / font_floor` |
| 源图文件缺失/嵌入失败 | 灰底图位占位框（图号+标题+来源保留）（D5） | `uncertainty` + `figure_adjust` |
| 字体缺失（预览渲染） | 标准字体目录探测 → CJK 文件扫描 → PIL 内置位图字体，文件名如实记录（D11） | `render_log.json` + `uncertainty` |
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
      sources + uncertainty + change_records；无 null 占位（四形态），已知
      语义的键是真值而非类型默认
- [ ] `check_contract.py` G1–G8 全过、exit 0（CP3）
- [ ] pptx 可被 python-pptx 重开、页数=计划（CP2）；同输入重跑仅时间戳差异
- [ ] 预览 PNG 存在且非空白；渲染后端/字体探测在 `render_log.json` 如实记录
- [ ] 输出目录内没有本机绝对路径（记录一律是运行相对/环境路径）
- [ ] 未有「看起来热闹但无来源」的装饰性页面/数据

## 7. 目录结构

```
<skill root>/                      # = $SKILL_DIR（平台装到 /skills/weekly-skill）
  SKILL.md                本文档（两阶段工作流 + CP1–CP3 + D1–D12 + 资源形态）
  README.md               使用说明 / 依赖 / 限制 / 失败处理 / 维护
  TEST.md                 本地实测记录（冒烟/确定性/鲁棒性/对照）
  GITHUB_URL.txt          GitHub 公开链接
  references/
    OUTPUT_CONTRACT.md    result.json 结构与字段契约 + CP3 G1–G8（必读）
    RUBRIC_MAP.md         评分五维 → 设计覆盖映射（交付前自评）
    template_guide.md     模板使用指南（母板/版式/占位符/主题字体色/字号阶梯）
    checklist.md          适配检查清单（收尾验收，逐项勾选）
    batch-rules.md        批量一致性规则（R1–R8）
    two-phase-workflow.md 两阶段工作流图示与分步命令
    failure-modes.md      失败模式表，与 D 规则配套
  scripts/
    main.py               编排入口（一条命令两阶段；CP1/CP3 门）
    extract.py            主张/图/表/数值抽取（来源定位 + 材料 sha256）
    deckplan.py           确定性页结构方案（页型/裁剪/证据映射）
    adopt_plan.py         ★阶段一：模板审计 + 页→版式分配 + 批量规则 + 图表计划
    adapt_pptx.py         ★阶段二：按方案模板适配 + pptx 生成
    preview.py            PIL 示意图预览（封面+联系表，诚实标注）
    audit.py              真实产物自查（重开/覆盖/图号/溢出/页脚/方案一致性）
    validate_result.py    result.json 契约校验（VALID, exit 0）
    check_contract.py     ★CP3 契约门（G1–G8 独立复查，exit 0）
    pptx_toolkit.py       共享 PPTX 工具（版式打分/占位符/contain-fit/主题/确定 zip）
    make_template.py      内置回退模板的运行时生成（ensure_builtin + make）
    make_synthetic_inputs.py  示例占位图的运行时合成（纯几何，带 SCHEMATIC 水印）
    common.py             公共工具（自定位/便携路径/字号阶梯/字体探测/颜色/哈希）
  examples/               最小示例（合成数据，非正式案例）
    README.md / EXPECTED-OUTPUT.md   示例说明 / 应产出的文件清单与契约字段
    case.json / task.md / material.md / minimal_example.md
    plan.sample.json / adopt_plan.sample.json     方案样例（真实运行，标注示例）
    output/               示例运行的**文本**产物（result/summary/render_log）
```

脚本不硬编码绝对路径：`scripts/common.py` 用 `os.path.dirname(__file__)`
自定位 Skill 根；所有真实输入输出路径由命令行显式给出（官方运行时为
`/input`、`/app/work`、`/app/output`）；**写进 JSON 的路径一律是便携形式**
（运行相对路径 / 正斜杠），不含本机盘符或用户目录。

## 8. 维护

- 版本：`scripts/common.py` 内 `SKILL_VERSION`；
- 分层约定：素材/抽取在 `extract.py`，页结构方案在 `deckplan.py`，阶段一
  方案在 `adopt_plan.py`，阶段二构建在 `adapt_pptx.py`，PPTX 底层细节在
  `pptx_toolkit.py`，验证在 `audit.py` + `validate_result.py` +
  `check_contract.py`，二进制资源生成在 `make_template.py` +
  `make_synthetic_inputs.py`；
- 改动后至少复跑 `TEST.md` §1 冒烟与 §2 确定性，确认全绿再交付；
- 交付前跑包外验收：`python validate_pkg.py <包目录>`（扩展名白名单、
  ≤50 文件、≤500KB/个、≤2MB、无 `__pycache__`、无绝对路径、`py_compile`）；
- 二进制资源**永不入包**：模板由 `make_template.py` 生成、示例图由
  `make_synthetic_inputs.py` 生成，产物（pptx/PNG）由运行时产生。

## 9. 资源形态与运行时生成（为什么包里没有 .pptx / .png）

题面硬约束：*Skill resources: at most 50 UTF-8 text files, 500KB each and
2MB total, no symlinks.* ⇒ 本包**只含文本资源**，所有二进制改为运行时生成，
生成物与正式案例的产物形态完全一致：

| 资源 | 处置 | 入口 |
|-|-|-|
| 内置回退模板 `.pptx` | 不随包；案例给模板/起始 deck 时用真实文件，两者都缺时**现场生成**（16:9，真实母版/版式/占位符），并记入 `uncertainty` | `scripts/make_template.py`（`ensure_builtin()` 由 `main.py` 调用；也可单跑 `--out <dir>/builtin.pptx`） |
| 示例输入图 `.png` | 不随包；示例运行前**现场合成**纯几何占位图（带 `SCHEMATIC / 示意` 水印，不含伪造数值） | `scripts/make_synthetic_inputs.py --dir <示例目录>` |
| 预览 `.png` / 产物 `.pptx` | 运行时由 `preview.py` / `adapt_pptx.py` 生成，写入 `--out` | `scripts/main.py` |
| 字体 `.ttf/.otf` | 不随包；运行时按标准字体目录探测（Windows 目录取自环境变量 `WINDIR`/`SystemRoot`，另有 `/usr/share/fonts`、`/System/Library/Fonts` 等候选），找不到则回退 PIL 内置位图字体并记录 | `scripts/common.py`（`font_dirs()` / `probe_font_candidates()`） |
| SVG 图元 | 不随包；本 Skill 不使用矢量模板，预览为 PIL 位图 | — |

**缺依赖时的降级**：无 python-pptx 时 `ensure_builtin()` 返回带原因的说明而非
抛异常，模板链退化为"案例模板 / 起始 deck"，失败按 D6/D12 写出诚实的
`status=failed` result.json；无 PIL 时预览阶段同理记录（不静默成功）。

## 附:本版增量 —— 确定性与字节级可复现（determinism）

上文 §1–§9 是基线正文、**逐字未改**（两阶段工作流、CP1–CP3 门、D1–D12 决策规则、
`$SKILL_DIR/scripts/...` 命令、`--flag` 表、§9 二进制运行时生成全部照旧）。本节只写
本版**新增的实质内容**：一条复现性实验入口、四层判据、四张声明表与实测数字。
本轴的完整论述另存 `references/SKILL-FULL-DETERMINISM.md`（讨论稿，非执行入口）；
**执行入口只有本文件与上文命令**。

### A1. 本轴要回答的两个问题

| 问题 | 谁回答 | 判据 |
|-|-|-|
| **同一输入重跑，产物是否一样？** | `scripts/determinism.py` | 二进制交付物 **L1**（原始字节）全条件一致；JSON 记录在 **L4** 后收敛为单一值 |
| **不一样的那些字段，是谁、为什么？** | `references/DETERMINISM.md` §3–§5 | 每个差异字段都落在四张声明表之一；**声明表外差异 = 0 条** |

两者缺一不可：只给"一致"会掩盖被删掉的字段；只给"字段清单"又没法判好坏。
所以本轴把两者做成一个可执行实验：**跑 → 测 → 归因 → 逐条列名**。

### A2. 运行命令（复现性实验；`--run` 必须在包外）

```bash
RUN=<包外可写目录>              # 必须包外：包内跑会留下 __pycache__/*.pyc，资源契约拒收
python "$SKILL_DIR/scripts/determinism.py" --skill "$SKILL_DIR" --run "$RUN" \
    --runs 3 --json "$RUN/determinism_report.json" --markdown "$RUN/determinism.md"
# exit 0 = 二进制交付物 L1 一致 + 全部 JSON 记录在 L4 后收敛 + 声明表外差异 0 条
python "$SKILL_DIR/scripts/determinism.py" --skill "$SKILL_DIR" --run "$RUN" --condition c1,c4
```

脚本自己会拒绝把 `--run` 放进包里（除非显式 `--allow-in-package`），因为
`__pycache__`/`.pyc` 是题面资源契约明确拒收的类型。

**五个受控条件（这是本轴的实验设计，不是顺手多跑几次）**：

| 条件 | 变了什么 | 专门抓什么缺陷 |
|-|-|-|
| `c1` | 同 cwd、同 env，3 个**独立进程** | 进程内状态、时钟、临时文件名 |
| `c2` | 停 1.2 s 后再跑 3 次 | 是否只对时序/jitter 敏感 |
| `c3` | cwd 换成 1 层嵌套 / 2 层嵌套 / 脚手架根 | 记录里混进了调用者自己的目录 |
| `c4` | `PYTHONHASHSEED` = 0 / 1 / 12345 / 未设置 | `set`/`dict` 迭代顺序泄进产物 |
| `c5` | 相对参数 vs 绝对参数（同一 cwd 显式启动） | 参数形态改变了记录内容 |

### A3. 判据：四层一致性（L1–L4）

| 层 | 做法 | 谁应该通过 |
|-|-|-|
| **L1 原始** | 直接比 sha256 | 不含时间戳、不含宿主路径的产物：`.pptx`、两张 `.png`、`summary.txt`、`_runtime/builtin.pptx` |
| **L2 去时间戳** | 去掉 `NONDETERMINISM` 表里的字段 | 还不够：路径记录仍在（见 L3） |
| **L3 归锚点** | 再把"调用者目录 / 输出目录 / 用例目录"替换成 `<CWD>/<OUT>/<CASEDIR>` 记号 | `spec.json`、`adopt_plan.json`、`content.json`、`render_log.json` |
| **L4 再去派生摘要** | 最后把**锚点文件的 sha256** 换成 `<DERIVED>` 记号 | 全部 JSON：`audit.json`、`result.json` 也在此层收敛为单一值 |

**为什么要 L4**：`result.json.artifacts[].checks.sha256` 是 `spec.json` 的摘要，而
`spec.json` 里带着锚点路径。摘要**不可能**在锚点变化时保持不变——它不是"不确定"，
是**级联**。把已知原因替换成记号后再比，问的才是真问题：**除了列出来的原因，还有
没有别的东西在变？** 答案是 0 条。

### A4. 实测数字（本机 python 3.13.9，16 次运行，全部 exit 0、status=success）

- 产物 12 个/次；**6 个文件 L1 逐字节一致（16/16 次）**：`deck.pptx`、
  `cover_preview.png`、`slides_contact_schematic.png`、`_runtime/builtin.pptx`、
  `summary.txt`、`_PREVIEW_ARE_SCHEMATIC.txt`
- `make_template.py` 单独在两处不同 cwd 各跑一次：**sha256 相同**
  （`f75fa66e4ebf88d1…`）
- 全部 6 个 JSON 记录在 **L4 后收敛为单一值**（各自唯一值数 = 1）
- **声明表外出现差异的字段：0 条**；逐字段归因共 41 条，分布：
  宿主锚定 34 · 锚点派生摘要 6 · 时间戳 1
- 单次流程耗时 **≈1.4–2.4 s**（16 次合计 **≈28 s**）

完整逐字段表见 **`references/DETERMINISM.md`**（由实测报告 `determinism_report.json`
渲染，非手抄；该 reference 末尾附有报告原文）。

**数字来源**：`references/DETERMINISM.md`（R3 实测报告渲染）。本包 2026-11-23 包外
按 A2 命令复核重跑（`--runs 3`，16 次）：`L1_bin=True / L4_stabilised=True /
undeclared=0`、稳定文件仍 **6** 个、`_runtime/builtin.pptx` sha256 仍为
`f75fa66e4ebf88d1…`、逐字段归因仍 **41** 条（宿主锚定 34 · 锚点派生摘要 6 ·
时间戳 1），与上表逐项一致；仅墙钟耗时高于原记录（两次复核 16 次合计 28.4 s /
28.0 s，原记录 24.4 s），以本次数字为准。

### A5. 四张声明表（"故意不稳定"的白名单）

`scripts/determinism.py` 顶部把"允许不一样的字段"写成四张**精确**表，表外出现差异
就是失败：

| 表 | 含义 | 本包实测条数 |
|-|-|-|
| `NONDETERMINISM` | 墙钟戳、解释器/依赖版本 | 1 |
| `HOST_ANCHOR` | 值 = 运行发生**在哪里**的函数（调用者 cwd、输出目录、用例目录、宿主字体集） | 34 |
| `INVOCATION_FORM` | 同一次运行内稳定，但"给了相对路径"与"给了绝对路径"两种调用形态之间不同 | 4 类 |
| `DERIVED_FROM_ANCHORED` | **锚点记录的摘要**（sha256）或引用运行期模板路径的说明文字 | 6 |

**为什么这些字段不能直接删掉**：`references/OUTPUT_CONTRACT.md` 规定
`artifacts[].abspath` 记"相对当前运行目录的便携路径"，`unexpected` 之外的每一处路径
都是评审用来**找到那个文件**的定位符。把它们改成与 cwd 无关的常量，就等于把契约里
的定位能力拿掉。本包的取舍是：**保留定位符，把不稳定性显式列名并给出稳定化办法**。

### A6. 怎么把"不稳定"变成"稳定"（按字段类别给做法）

| 字段类别 | 现状 | 想让它逐字节一致，需要动什么 |
|-|-|-|
| `generated_at` / `render_log.generated_at` | 墙钟戳 | 不建议改：冻死时间戳是**说谎**。要在 CI 里比对，请用 L2/L4 层 |
| `artifacts[].abspath`、`*.detail`、`cover.path`、`contact_sheet.path`、`template.source` | 运行期算出的路径 | 若要把"跨 cwd 也逐字节一致"变成硬指标，需把记录锚点从"当前工作目录"改成"输出目录"并同步修改 `references/OUTPUT_CONTRACT.md` 的措辞——**本包不动契约文本**，因此这一条作为已知取舍如实列出 |
| `spec.json.pages[].figures_on_page[].file`、`content.json.figures[].file_abs`、`sources[].path` | 原样记录 `--case` 给出的路径 | `--case` 用**相对路径**给出时记录即为相对路径；两种调用形态的差异已列入 `INVOCATION_FORM` |
| `*.checks.sha256`、`verification.traceability.hashes.*`、`audit.json.hashes.*` | 锚点记录的摘要 | 随上游稳定而自动稳定：**先把上游锚点稳定化，摘要自然一致** |
| 字体探测字段 | 宿主字体目录的函数 | 同一镜像内稳定；本包按**文件名**记录，不含本机路径 |
| `tool_versions.*` | 宿主解释器/依赖版本 | 固定镜像即固定 |

### A7. 本轴新增的交付前动作（不属于 D1–D12）

- **R1** 跑 `determinism.py`，要求 exit 0；
- **R2** 若 exit 1，逐条读 `unexpected_volatile`，每条要么修掉、要么在四张声明表里
  写明理由——**不许"大概是因为时间戳"**。

维护口径：改了管线任何一步 → **必须重跑 `determinism.py`**，并把新报告重新渲染进
`references/DETERMINISM.md`；声明表只能"新增并写明理由"，不能为了让脚本通过而放宽
匹配（表里每个键都能被 `_matches` 精确解释）。

### A8. 本轴自查（在上文 §6 清单之外）

- [ ] `determinism.py` 跑通，exit 0；**L1 二进制一致 / L4 全 JSON 收敛 /
      未声明差异 0 条** 三项都为真
- [ ] `references/DETERMINISM.md` 里的字段表与实际报告一致（重新生成而非手改）
- [ ] 输出目录内没有本机绝对路径**泄漏进包里**（运行时产物在 `--out`，不进提交包）

本轴的机制说明、逐字段归因与未覆盖声明：**`references/DETERMINISM.md`**。
