---
name: scientific-schematic-editor
description: >-
  Generate and edit editable scientific schematics, mechanism/relationship
  diagrams, flow diagrams and data charts from source materials. Extracts an
  entity-relation manifest (traceable to sources), draws a layered editable
  SVG source plus PNG/PDF (and TIFF/EPS) exports, runs CP1 plan-lint and
  legend/data-mapping and export-compliance checks, and writes a structured
  result.json with all output_contract fields. Use when a task asks to draw,
  regenerate or edit a scientific figure from papers, tables or notes:
  科研示意图/机制图/信号通路图/流程图/实验装置图/图表的生成与编辑.
  Execute in order: read actual files → extract ER (draft via scripts) →
  write/lint manifest (CP1) → main.py draw → checks (CP2) → edit & re-check
  (CP4) → contract gates (CP3) → self-check & determinism (CP5).
---

# scientific-schematic-editor — 科研示意图生成与编辑 · 整合版（增益层 + 机制层）

> 本包整合了基线 Skill 与 2 个强化层,各层对应不同的评分维度:使用增益 25 · 创新增益 15 + 生态贡献 10。
> 各层内容**不重复**:决策层给规则与失败分支;增益层给对照协议与指标口径;机制层给机制说明与可复用资产。
> 建议使用顺序:先用「决策层」跑通并处理异常,再用「增益层」证明并度量改善,最后用「机制层」复用与扩展。
> 各层的原始文件都完整保留在本包内,不是摘要 —— 下面每一层都是可以独立执行的完整规范。

## 本包文件索引

- `GITHUB_URL.txt`
- `README.md`
- `TEST.md`
- `assets/checklist.json`
- `assets/relation-dict.json`
- `examples/EXPECTED-OUTPUT.md`
- `examples/README.md`
- `examples/case.json`
- `examples/case_chart.json`
- `examples/case_edit.json`
- `examples/task.md`
- `references/CHECK-INDEX.md`
- `references/DRAWING_GRAMMAR.md`
- `references/EDIT-ACTION-SCHEMA.md`
- `references/ER_MANIFEST.md`
- `references/GAIN-PROTOCOL.md`
- `references/MECHANISM.md`
- `references/OUTPUT_CONTRACT.md`
- `references/REUSABLE-ASSETS.md`
- `references/RUBRIC_MAP.md`
- `references/failure-modes.md`
- `scripts/checks.py`
- `scripts/doccheck.py`
- `scripts/edit.py`
- `scripts/extract.py`
- `scripts/layout.py`
- `scripts/main.py`
- `scripts/manifest.py`
- `scripts/pdftext.py`
- `scripts/render.py`
- `scripts/report.py`
- `scripts/run_examples.py`
- `scripts/selftest.py`
- `scripts/spec_lint.py`
- `scripts/svgbuilder.py`
- `scripts/textfont.py`
- `scripts/validate_result.py`
- `examples/sources/data-table.csv`
- `examples/sources/figure03-note.md`

---

# 【增益层】公平对照协议与可测指标（目标维度:使用增益 25）

---
name: scientific-schematic-editor
description: >-
  Generate and edit editable scientific schematics, mechanism/relationship
  diagrams, flow diagrams and data charts from source materials, with a
  measurement protocol attached. Extracts an entity-relation manifest
  (traceable to sources), draws a layered editable SVG source plus PNG/PDF
  (and TIFF/EPS) exports, runs CP1 plan-lint and legend/data-mapping and
  export-compliance checks, and writes a structured result.json with all
  output_contract fields. Use when a task asks to draw, regenerate or edit a
  scientific figure from papers, tables or notes: 科研示意图/机制图/信号通路图/
  流程图/实验装置图/图表的生成与编辑. Every run emits the metrics needed to
  compare against a Skill-free baseline (references/GAIN-PROTOCOL.md):
  exit code, contract validity, gate counts, traceability ratio, rework
  cycles; the protocol also lists exactly which measurements are NOT yet
  made, so no unmeasured gain is claimed.
---
## scientific-schematic-editor — 科研示意图生成与编辑（增益可验证版）

本技能交付两样东西：**能出图的流水线**，以及**一套说清"它比不加技能强在哪"的
度量协议**。协议不是宣言，是 `references/GAIN-PROTOCOL.md`：里面定义了对照组、
指标、判据、公平性条款，以及**本机真实跑出来的数据**——包括哪些指标实测更好、
哪些没有差异、哪些**尚未测量**。

三条主张：

1. **图画对** — 实体、关系、方向、数值、单位逐条可回溯到材料；
2. **图可改** — 文字可选、图层可拆、SVG 内嵌 ER 清单，编辑只动被指明的元素；
3. **增益可测** — 每次运行的退出码、契约有效性、门控计数、溯源比例、返工轮次
   都是可记录的观测量；对照基线用同一夹具、同一命令集。

**本技能不做**：统计计算的数值方法选择、海报/封面版式、艺术插画美化、
论文正文写作。数据表里的数值是**事实输入**，不改算、不补造、不换算单位。

> 与基线包的结构差异：本包把**度量**提到正文主线。§3 给出指标定义与基线对照
> 矩阵（I1–I10），§4 给出"要产出一条可比较记录"的执行路线（M0–M6），
> 决策规则（§5）只在"影响可测性"时出现——因为一条静默降级会污染测量，
> 所以把会污染测量的分支专门点名。

### 1. 适用条件

- 任务是"科研示意图/机制图/通路图/流程图/实验装置图/数据图"的**绘制或编辑**，
  workorder 一般形如 `editable_relationship_schematic`；
- 有来源材料（论文图注/正文摘录/Markdown/CSV/PDF），或要求对已有图稿做
  **源文件级**修改；
- 交付要求包含可编辑源文件、导出件与结构化结果（`result.json`）；
- **需要给出增益证据**时（本题的"使用增益可验证性"评分点）——这时按 §3/§4 走，
  并把对照记录附在交付说明里。

### 2. 输入、输出与"可测产物"

**输入（平台提供）**：`/input/case.json`（`case_id`/`workorder`/`figure_type`/
`sources`/可选 `manifest`、`entities+relations`、`data`、`edits`、`output_contract`）、
`/input/task.md`、`/input/` 下的材料（可能是 PDF，先过 `scripts/pdftext.py`）。
**以实际文件内容为准，不凭字段标签猜内容。**

**输出（写入 `/app/output`，全部运行时现场生成）**

```
/app/output/
├── figure.svg      # 可编辑分层源文件
├── figure.png      # 渲染预览
├── figure.pdf      # 矢量导出件
├── result.json     # 结构化结果（OUTPUT_CONTRACT 全字段 + case_id）
└── work/           #（或 /app/work）entities.json / draft / layout / manifest.validated.json
```

| role | format | 是什么 | 完成标准 |
|-|-|-|-|
| `figure` | svg | 可编辑分层源文件 | 文字是真实 `<text>`（未被 path 化）、语义图层可拆、带 `id`/`data-*`、内嵌 ER 清单 |
| `preview` | png | 渲染预览 | 18 cm 宽有效 DPI ≥300（印刷）/≥150（屏幕）、色彩为 RGB 族 |
| `pdf` | pdf | 矢量导出件 | 可打开、页数可读、字体嵌入为尽力而为并如实记录 |
| `tiff` / `eps` | 对应格式 | 可选导出件（`--exports tiff,eps`） | 按目标单位要求生成；未逐项实测，见未解决项 |

> **包内不预置任何图稿或渲染件**（PDF/PNG/SVG/TIFF 都不随包分发）：它们由本技能
> 运行时生成；示例期望产物见 `examples/EXPECTED-OUTPUT.md`，一键复现用
> `scripts/run_examples.py`。

### 3. 度量模型：I1–I10 指标与基线对照

#### 3.1 为什么先定义指标

"使用增益"包含**质量增益 / 效率增益 / 增益可验证性**三块。没有定义就没有增益：
先说清"测什么、怎么测、和谁比、什么算赢"，再谈结果。本技能选定的指标必须是
**同一条命令集下可重复观测**的，而不是主观观感。

#### 3.2 指标定义（每一项都给出取值来源）

| 指标 | 定义 | 取值来源（机器可读） | 基线做法（不加载 Skill） |
|-|-|-|-|
| **I1 契约有效性** | `validate_result.py` 是否 VALID（G1–G8） | 退出码 | 基线常见：无 `result.json`，或字段不全 ⇒ 无效 |
| **I2 结构完整性** | 三类产物（可编辑源 / 预览 / 导出）是否齐全 | `artifacts[].role`、G7 | 基线常见：只有位图 |
| **I3 可编辑性** | 文字是否为真实 `<text>`、是否有语义图层、是否带 `id`/`data-*` | `svg.editable_text`、`svg.layers`、`svg.data_entity_attrs` / `svg.data_relation_attrs` / `svg.data_source_attrs` | 基线常见：导出即栅格化或文字 path 化 |
| **I4 溯源比例** | 带 `source`（+`evidence`）的实体/关系占比 | `traceability.entities`、`traceability.relations` | 基线无此概念：图上元素没有出处字段 |
| **I5 关系语义正确性** | 方向/类型是否落到 7 类规范词表且可判 fail | `spec.relation_kind`、`spec.containment_group` | 基线靠自由文本箭头，无判据 |
| **I6 图例一致率** | 图面箭头类型 ↔ 图例条目双向一致 | `spec.legend_missing_kinds`、`legend.orphan_items` | 基线手工画图例，无双向校验 |
| **I7 数据映射一致** | 类别 ↔ 颜色 ↔ 图例同源、调色板覆盖类别数、单位上轴 | `spec.color_category_count`、`data_mapping.*` | 基线常见：颜色数与类别数不符 |
| **I8 导出合规** | 18 cm 宽有效 DPI、色彩族、PDF 结构、字体 | `bitmap.dpi_print`、`bitmap.colourspace`、`pdf.*`、`font.cjk` | 基线少见预检 |
| **I9 返工轮次** | 从材料到"门全过"需要几次重跑 | 同一 pipeline 的连续运行次数（人工记账） | 基线无门 ⇒ 无法定义"过" |
| **I10 端到端耗时** | 一条命令出齐产物并跑完门 | 命令的墙钟时间 | 同为一条命令，但缺门与校验 |

#### 3.3 公平性条款（对照成立的前提）

| # | 条款 | 理由 |
|-|-|-|
| F1 | **同输入**：同一 `case.json`、同一材料文件、同一 `output_contract` | 输入不同则不可比 |
| F2 | **同画布与导出参数**：同一 `style.canvas`、同一 `--dpi`、同一 `--exports` | 图面参数变了，DPI/排版类指标就不可比 |
| F3 | **同预算**：同一模型、同一 64 请求 / 900 秒 / 16384 token 响应预算 | 题面运行契约 |
| F4 | **同模型与同版本**：对照臂不加载本 Skill，其余条件一致 | "增益"必须归于 Skill 而非模型 |
| F5 | **同判据**：两个臂用**同一个** `validate_result.py`（本包自带的 G1–G8）判分 | 判据若各写一套，等于自己给自己打分 |
| F6 | **同夹具复用**：`examples/` 的三件套固定不改，对照运行不得调整夹具 | 改夹具 = 改题 |
| F7 | **失败也记录**：任一臂失败都记 exit code 与 fail 明细，不得丢弃重试直到好看 | 丢弃失败样本 = 选择性报告 |
| F8 | **不可测就标注**：没有实际跑过的指标写"未测量"，不得用推断值顶替 | 这是本协议最重要的一条 |

> F5 有点违反直觉但很关键：**用被测方自带的判据去评分被测方是有偏的**。
> 本协议的处理方式是把偏差**写明并固定**：同一判据同时作用于两个臂，
> 因此"判据偏严/偏松"对两臂同等生效；真正的科学正确性仍由题面所说的
> "scientific judgement remains native/LLM Judge"承担，不由本协议承担。

#### 3.4 实测对照记录（CLI 空间，本机真实运行）

**这部分是真实跑出来的，不是设计意图。** 完整命令见 `TEST.md` §M2–§M5，
复跑环境：Python 3.13.9 / matplotlib 3.10.6；夹具 = 本包 `examples/` 三件套。

| # | 场景 | 命令要点 | 实测 | 对应的指标 |
|-|-|-|-|-|
| R1 | 标准 schematic | `main.py --case examples --out <t>` | **exit 0**，墙钟 1.53 s；`status=success`；产物 3 类齐全；`result.json` 顶层 23 键 | I1、I2、I10 |
| R2 | 标准 schematic（外部 cwd） | 同上，cwd 在包外 | **exit 0**，1.53 s；`figure.svg` sha256 与 R1 **完全相同** | I10（自定位不引入差异） |
| R3 | 契约门 | `validate_result.py` | **exit 0 / VALID**（G1–G8 全过） | I1 |
| R4 | 三示例端到端 | `run_examples.py --out <t>` | **exit 0**，4.99 s；schematic/chart/edit 三步各 exit 0，三份契约各 VALID；顶层键 23 / 21 / 21 | I1、I2、I10 |
| R5 | 确定性双跑 | `--fixed-time` 两次 | 两次 `figure.svg` **逐字节一致**（sha256 相同）；两份 `result.json` 唯一差异是 `artifacts`（`abspath` 指向不同目录），去 `abspath` 后完全相同 | I9（可复现性是其前置） |
| R6 | 数据更新传播 | 把 chart 数据表的值翻倍后重跑 | 两次 `figure.svg` sha256 **不同** ⇒ 图随数据重绘（不是"改了数据图不动"） | I7 |
| R7 | 材料缺失 | `sources` 指向不存在文件 | **exit 0**、`status=success`，但 `sources=[]`、`uncertainty` 3 条 ⇒ 降级被记录 | I4（诚实性联动） |
| R8 | 未知关系类型 | manifest 里把 kind 改成 `gibberish` | **exit 1**、`status=partial`、`fails=[spec_lint.spec.relation_kind]` ⇒ 错误被拦而非静默通过 | I5 |
| R9 | 无依据即停 | 无 manifest 且 case 无 entities | **exit 1**；写 `status=failed`；`fails=[pipeline]` | I1（不造假） |
| R10 | 编辑增量 | `--edit-svg` + 5 个动作（字段名正确） | **exit 1**（夹具触发 `spec.group_member` fail）；`change_records` **7** 条；实体 6→5、关系 5→3；契约仍 VALID | I2、I9 |
| R11 | 编辑目标不存在 | `relabel` 指向不存在的 `R99` | 日志 `[edit] fail`；`change_records` **0** 条；**exit 0**、契约仍 VALID ⇒ **该分支不可从 result.json 察觉** | 见 §3.5 混合项 |
| R12 | 草稿抽取 | `extract.py` 跑示例材料 | **exit 0**，0.12 s；产出 17 实体 / 4 关系 / 5 组，全部带 `_draft` ⇒ 抽取只是加速，仍需复核 | I9 |
| R13 | `--exports tiff,eps` | 追加导出 | **exit 0**；TIFF ≈ 46 MB（未压缩 4500×2580@300dpi） | I8（体积相关） |

**这些数字能支撑什么、不能支撑什么（关键的自制）**：

| 结论 | 是否被 R1–R13 支撑 |
|-|-|
| 本技能能稳定产出"可编辑源 + 预览 + 导出 + 契约有效"的一整套 | ✅ 被 R1–R4 支撑（同一夹具，多次运行） |
| 同一输入下产出是确定性的（除时间戳/输出目录） | ✅ 被 R5 支撑 |
| 图随数据重绘而非冻结 | ✅ 被 R6 支撑 |
| 错误输入会被拦下并显式降级，而不是静默出图 | ✅ 被 R7–R9 支撑 |
| 编辑是增量而非重画，且改动有 before→after 记录 | ✅ 被 R10 支撑 |
| **本包比"不加载 Skill 的基线 Agent"得分更高** | ❌ **未测量**。基线臂要由平台按同一案例运行；本机没有跑过基线臂，因此不作此声明 |
| **返工轮次比人工/基线更少** | ❌ **未测量**。R1–R13 是 CLI 空间测量，不含"人工修改量"这类需要对照臂的量 |
| **耗时比基线更短** | ❌ **未测量**。只有本包自身的墙钟时间（约 1.5 s/例，毫秒级差异不足以支撑结论） |

#### 3.5 "可测性混合项"清单（哪些改进无法被机器判据完全覆盖）

诚实标注比夸大更有价值。以下三处是**部分可测**的，协议要求用"半自动判据"补：

| 混合项 | 机器能测的部分 | 需要人/LLM 判的部分 | 本文档的态度 |
|-|-|-|-|
| 科学正确性（方向、机制） | kind 是否可映射、containment 是否用分组、self-loop 告警 | "抑制画成激活"这类**语义**错 | 机器只兜结构错误；语义由题面所说的 native/LLM 判断承担 |
| 编辑生效性 | `change_records` 条数与内容（before→after） | "这是不是用户真想要的那次编辑" | **请求条数 vs 记录条数**是本协议指定的对拍判据（因为 `edit.*` 问题只进 stdout） |
| 图面美观/可读性 | 溢出、重叠、字号下限的部分检测 | 审美 | 不声称；只给 warn 与 `uncertainty` |

### 4. 执行路线 M0–M6（每一步都产出"可记录的观测"）

**顺序：读契约 → 读材料 → 抽取 → 写清单 → CP1 → 绘图 → CP2 →（编辑则 CP4）
→ CP3 → CP5 → 记账。**

#### M0 定位并读契约
1. 读 `/input/task.md` 与 `/input/case.json`，记 `case_id`；
2. 解析 `output_contract` 声明的键与类型（四形态：string→`""`、array→`[]`、
   object→`{}`、number/boolean→`0`/`false`，禁 `null`）；
3. 记下本次运行的**参数快照**（`--dpi`、`--exports`、画布尺寸）——F2 要求对照时
   参数一致，参数不记 = 对照无效；
4. 确认 `/app/output`、`/app/work` 存在。

#### M1 读实际文件（记录材料清单）
1. 逐份读 `case.sources` 指向的**真实文件**；PDF 先过 `pdftext.py`；
2. 记下"读到几份 / 缺几份"——这是 I4 与诚实性的输入；
3. 记下"材料里有几条与图相关的陈述"作为溯源分母。

#### M2 抽取候选清单（加速项，不是答案）
```bash
python "$SKILL_DIR/scripts/extract.py" \
    --inputs /app/work/pdftext/<stem>.txt <其他材料> \
    --out /app/work/draft-entities.json
```
草稿带 `_draft` 标注。**记录"草稿条数 vs 最终清单条数"**：这个差值是 I9 的
可观测代理（人工复核量），也是"抽取只是加速器"的证据。

#### M3 CP1：生成前 lint（I5/I6/I7 的第一道闸）
```bash
python "$SKILL_DIR/scripts/spec_lint.py" --manifest /app/work/entities.json
# {"valid": true} 才算通过；否则按 fail 的检查名定位问题后重跑
```
**记录本次 CP1 的结果与轮次**：第 1 次就 valid，还是第 k 次才 valid —— 这就是
I9 的读数（返工轮次）。

#### M4 生成 + CP2（I2/I3/I8 的读数来源）
```bash
python "$SKILL_DIR/scripts/main.py" --case /input/case.json \
    --manifest /app/work/entities.json --work /app/work --out /app/output
```
- 记录**墙钟时间**（I10）与**exit code**；
- `result.json.verification.checks` 里逐条读：`svg.*`（I3）、`bitmap.*`+`pdf.*`+`font.cjk`（I8）、
  `legend.*`（I6）、`data_mapping.*`（I7）、`traceability.*`（I4）；
- **记录 fail/warn 计数**，不要只看 `status`。

#### M5 编辑（如适用）→ 记录改动量
```bash
python "$SKILL_DIR/scripts/main.py" --case <case.json> \
    --edit-svg /app/work/figure.svg --out /app/output --work /app/work
```
- 走 `--edit-svg` 时编辑请求写在 case 的 **`edit_requests`** 字段（写 `edits` 会被忽略）；
- **必须对拍**："请求条数（按 `references/EDIT-ACTION-SCHEMA.md` §1 推算，含
  `remove_entity` 的级联）" vs "`change_records` 条数"。不等即为一次**未被机器捕获的失败**，
  按 §3.5 的半自动判据处理；
- 记录"未改动元素是否保持原样"（同一 SVG 的其余部分不应变化）。

#### M6 CP3 契约门 + CP5 确定性 + 记账
1. 契约门：`validate_result.py --case … --result …` → **VALID** 是 I1 的唯一读数；
2. CP5 确定性：`--fixed-time` 双跑，比对 `figure.svg` 字节与 `result.json`
   （除 `generated_at` / `artifacts[].abspath` 外应一致）；
3. **把本次运行的记账写成一段可粘贴的记录**（模板见
   `references/GAIN-PROTOCOL.md` §5），字段：case_id、参数快照、exit code、
   门控计数、各指标读数、返工轮次、未测量项。

### 5. 决策规则（只列"会影响可测性"的分支）

这里不重复完整决策体系，只列**会污染测量**或**会让读数失真**的分支——
这类分支一旦静默，整份对照记录就不可信。

| 规则 | 触发 | 动作 | 对测量的影响 |
|-|-|-|-|
| **G1** | 运行中使用了 `--skip-checks` 或 `--no-lint` | 该次运行**不得**计入对照记录：`verification.checks` 会为空、`spec_lint` 会是空对象，I3–I8 全部无读数 | 让"未检查"看起来像"已通过" |
| **G2** | 发生任何降级（材料缺失、字体缺失、无 PDF 库、镜像渲染） | 写入 `uncertainty`，并在记账里标注"本次读数受 X 影响" | 不标注就会把降级读数当成正常读数 |
| **G3** | 两次运行之间改了夹具、画布或 `--dpi` | 视为**不同条件**，分开记账，不得互相比较 | 违反 F1/F2 ⇒ 对照无效 |
| **G4** | 编辑请求条数 ≠ `change_records` 条数 | 本次编辑**判为失败**并查明字段名（`relation_id`/`entity_id`）；不得计入"编辑成功" | 该分支只进 stdout，不查就查不出 |
| **G5** | 任一臂失败 | 记录 exit code 与 fail 明细，**不得**丢弃重试直到好看 | 违反 F7 ⇒ 选择性报告 |
| **G6** | 想声明"比基线更好" | 必须已有**基线臂的实测读数**；没有就只能写"未测量" | 违反 F8 ⇒ 不可核验的声明 |
| **G7** | 写入 `acknowledged_issues` 把一个 warn 标记为已核可 | 可以在记账里写"warn 已核可"，但**不得**把它写成 ok | 混淆 ok 与 ack 会让 I3–I8 虚高 |
| **G8** | 材料本身不可抽取（加密/扫描 PDF） | 停在该材料，不伪造文本；记账写"该材料不可用" | 造假文本会让 I4 变成假读数 |

> 与基线包的关系：完整决策体系（材料缺失/矛盾、未知 kind、containment、
> 图例、调色板、字体、导出失败、编辑目标缺失…）在本包中按**同一套脚本行为**
> 生效，其权威描述见 `references/failure-modes.md`；本表只补"测量学上特别
> 危险"的那几条。

### 6. 异常处置速查（含"记账怎么写"）

| 情形 | 处置 | 记账字段 |
|-|-|-|
| 材料缺失 | 继续跑，写 `uncertainty` | 已读/缺失份数，`uncertainty` 条数 |
| 方向/数值矛盾 | 取有证据者，另一说法入 `uncertainty` | 冲突条数与取舍理由 |
| kind 未知 | CP1 fail → 回材料用原文动词改写 → 重跑 | 返工轮次 +1，记录检查名 |
| containment 画成箭头 | 改成分组框 | 同上 |
| 图例缺项 / 孤儿项 | 以数据表为基准修图例 | 检查名 + 修了几项 |
| 调色板 < 类别数 | 补齐或删冗余类别 | 类别数、颜色数 |
| 字体缺失 | `font.cjk` warn + `uncertainty` | 是否影响 PNG 预览 |
| PDF 不可抽取 | 报不可抽取，不伪造文本 | backend 字段 |
| 渲染/导出致命错 | 写 `status=failed` 的 result.json | exit 1、`fails=[pipeline]` |
| 编辑目标不存在 | 判为编辑失败并查字段名 | 请求条数 vs 记录条数 |
| 契约门不过 | 修对应项重跑到 VALID | G 门编号 |
| 用了 `--skip-checks`/`--no-lint` | **不计入对照记录**（G1） | 标注"仅迭代用" |

### 7. 资源文件说明（路径相对技能根，调用一律 `"$SKILL_DIR/..."`）

| 入口 | 角色 | CLI |
|-|-|-|
| `scripts/main.py` | 流水线入口 | `--case --manifest --out --work --edit-svg --base-name --exports --dpi --skip-checks --lint --no-lint --fixed-time --doc-check` |
| `scripts/extract.py` | 材料→候选 ER 清单草稿 | `--inputs --out --base-dir` |
| `scripts/pdftext.py` | PDF 文本抽取（含 stdlib 回退） | `--pdf --out` |
| `scripts/textfont.py` | 字体栈探测 | `--list --probe` |
| `scripts/spec_lint.py` | CP1 生成前 lint | `--manifest --dict --json` |
| `scripts/manifest.py` | ER 清单加载/规范化（位置参数） | `<manifest.json>` |
| `scripts/layout.py` | 布局引擎（库模块） | `—` |
| `scripts/svgbuilder.py` | 分层可编辑 SVG 构建（库模块） | `—` |
| `scripts/render.py` | matplotlib 镜像渲染（库模块） | `—` |
| `scripts/checks.py` | CP2 产物检查（库模块） | `—` |
| `scripts/edit.py` | 源文件级增量编辑 | `<figure.svg> <edits.json>` |
| `scripts/validate_result.py` | 契约独立校验 G1–G8 | `--case --result --out --json` |
| `scripts/selftest.py` | 模块级自测 | `—` |
| `scripts/run_examples.py` | 一键复现三示例 | `--out --keep` |
| `scripts/report.py` | 结果渲染辅助（库模块） | `—` |

| 其它文件 | 用途 |
|-|-|
| `references/GAIN-PROTOCOL.md` | **本包新增**：对照协议（F1–F8）、指标定义（I1–I10）、实测记录、记账模板、未测量清单 |
| `references/OUTPUT_CONTRACT.md` | `result.json` 契约 + G1–G8 硬门 + 四形态回显（**必读**） |
| `references/EDIT-ACTION-SCHEMA.md` | 编辑动作 → 字段名 → 记录 的对照表与反模式（G4 的依据） |
| `references/CHECK-INDEX.md` | 全部检查名的清单（级别 + 科学含义），指标取值的字典 |
| `references/failure-modes.md` | 题面 12 类失败形态 → 检测机制 → 处置（含对测量的影响） |
| `references/ER_MANIFEST.md` | 实体—关系清单规范（绘图唯一数据源） |
| `references/DRAWING_GRAMMAR.md` | 图形语法：关系语义→箭头/线型/颜色、方向判定、分组/层级、图例/数据映射 |
| `references/RUBRIC_MAP.md` | 五维评分（40/25/15/10/10）→ 本包文件/机制逐条映射 |
| `assets/relation-dict.json` | 连接规则字典（kind→arrow/line/dash/color，机器可读） |
| `assets/checklist.json` | CP1–CP5 检查点 + 自查清单（机器可读） |
| `examples/*` | 最小示例（schematic / chart / edit + 合成材料 + `EXPECTED-OUTPUT.md`），**示例非正式案例** |

### 8. 五维评分映射（交付前逐条自评；完整表见 `references/RUBRIC_MAP.md`）

| 维度 | 分 | 本包机制（可跑的检查，不是自述） | 证据文件 |
|-|-|-|-|
| 实际效果 | 40 | 材料→ER 清单→CP1→可编辑 SVG→PNG/PDF→result.json 一条命令跑通；每例的真实 exit code / 耗时 / 门控计数都留档 | `scripts/main.py`、`scripts/spec_lint.py`、`scripts/checks.py`、§3.4 |
| 使用增益 | 25 | 评价点"增益可验证性"由 `references/GAIN-PROTOCOL.md` 直接承担：对照条款 F1–F8、指标 I1–I10、**真实实测 R1–R13**、以及**明确写出的未测量项**；每次运行可按 §4 的 M0–M6 产出一条可比较记录 | `references/GAIN-PROTOCOL.md`、`TEST.md` |
| 创新增益 | 15 | ①CP1 **生成前** lint 门 ②SVG 内嵌 ER 清单 → 可增量编辑 ③stdlib PDF 抽取回退 + 诚实 backend ④导出前合规检查 ⑤共享字体探针 ⑥**把"归因于 Skill 的改进"与"未测量的改进"分开记录**（可核验性创新） | `scripts/spec_lint.py`、`scripts/edit.py`、`scripts/pdftext.py`、`scripts/checks.py`、§3.3/§3.5 |
| 可靠体验 | 10 | 自定位（任意 cwd 可跑，R2 给出同 sha 证据）；`--case` 兼容文件与目录；退出码 0/1/2 与 `status` 同向；G1–G8 决策规则专治"污染测量"的分支；失败分支仍写 result.json | §5、§6、`references/failure-modes.md` |
| 生态贡献 | 10 | 说明/依赖/字体/参数/示例/限制/维护齐全；可复用资产：对照协议与记账模板、指标字典、检查名索引、连接规则字典、CP 清单、契约校验器、三示例题集 | `README.md`、`references/*`、`assets/*`、`examples/*` |

### 9. 自查清单（提交前逐行确认；机器版 `assets/checklist.json`）

- [ ] 实体名逐字出自材料，无材料外基因/浓度/时间点/单位；
- [ ] 每个关系方向与材料一致（激活≠抑制、上下游不颠倒、包含用分组）；
- [ ] CP1 `{"valid": true}`：kind 可映射、containment 用分组、图例双向、调色板 ≥ 类别数；
- [ ] 数值/坐标/单位与数据表逐项一致，**改数据后图确实重绘**（R6 式验证）；
- [ ] `figure.svg`：文字可选、图层可拆、带 `id` 与 `data-*`、内嵌 ER 清单；
- [ ] 导出件：PDF 可打开；PNG 有效 DPI 达标；色彩 RGB 族；
- [ ] `result.json` 含全部契约键 + `case_id`，契约四形态回显无 `null`；
- [ ] `validate_result.py`（G1–G8）输出 VALID，退出码 0；
- [ ] 编辑任务：**请求条数 == `change_records` 条数**（G4），未改动元素保持原样；
- [ ] **对照记录里"未测量"写得出来**：凡未跑过基线臂的增益声明，一律标未测量（G6）；
- [ ] 最后一次交付运行**没有**用 `--skip-checks` / `--no-lint`（G1）；
- [ ] 形态：仅 7 种文本扩展名、无 `__pycache__`、≤50 文件、≤500KB/文件、≤2MB、包内无本机绝对路径。

### 10. 依赖与限制

- Python 3.9+（实测 3.13）；运行必需 **matplotlib / Pillow / numpy**，reportlab 可选；
  PDF 抽取按 fitz → pypdf → PyPDF2 → **stdlib 回退**逐级降级。
  建议先跑 `python "$SKILL_DIR/scripts/selftest.py"`；
- **平台运行契约**：技能装在 `/skills/weekly-skill`；输入 `/input/case.json` + `/input/task.md`；
  中间产物 `/app/work`；最终产物 `/app/output`。预算 64 请求 / 900 秒 / 16384 token/响应
  —— 先落盘可用部分产物，再增量改进；**F3 要求对照时预算一致**；
- **资源形态（硬约束）**：仅 UTF-8 文本（`.md/.py/.json/.txt/.csv/.yaml/.yml`），
  ≤50 个、单文件 ≤500KB、合计 ≤2MB、无符号链接；图稿与渲染件一律运行时生成；
- **已知限制（如实标注）**：预览是与 SVG 同源的 matplotlib 镜像（语义一致、非逐像素）；
  PDF 字体嵌入审计为尽力而为；CJK 渲染依系统字体；`extract.py` 只产候选草稿；
  走 `--edit-svg` 时 `edits` 字段不生效（用 `edit_requests`）；
  **`edit.*` 问题只进 stdout**，不进 result.json、不改退出码；
  **最重要的一条**：本包**没有**跑过"不加载 Skill 的基线臂"，因此不声称
  在平台打分上一定更高——只声称交付了可复跑的对照协议与自身实测读数。

### 11. 禁止事项

- 不提交预制答案/正式案例输出；示例只用于演示接口与流程，**示例产物不入包**；
- 不编造缺失的软件状态或科学数据（来源里没有的实体/数值一律不画）；
- 不宣称未经测量的增益：**没有基线臂读数就只能写"未测量"**（G6/F8）；
- 不丢弃失败样本后重新跑直到好看（G5/F7）；
- 不为"好看"改关系颜色（改色 = 图例不一致，且会污染 I6/I7 读数）。

---

# 【机制层】机制说明与可复用资产（目标维度:创新增益 15 + 生态贡献 10）

---
name: scientific-schematic-editor
description: >-
  Generate and edit editable scientific schematics, mechanism/relationship
  diagrams, flow diagrams and data charts from source materials. Five named
  mechanisms carry the design: M1 plan-before-draw (CP1 lint gate), M2
  self-describing source (ER manifest embedded in the SVG), M3 four-stage
  PDF extraction fallback with an honest backend record, M4 export
  pre-flight (DPI/colour/editable-text/PDF/font), M5 one shared font probe
  for render+checks+result. Each mechanism states what breaks without it and
  how it can be falsified (references/MECHANISM.md). Also ships a reusable
  asset inventory with an adoption ladder (references/REUSABLE-ASSETS.md).
  Use when a task asks to draw, regenerate or edit a scientific figure from
  papers, tables or notes: 科研示意图/机制图/信号通路图/流程图/实验装置图/
  图表的生成与编辑.
---
## scientific-schematic-editor — 科研示意图生成与编辑（机制显性版）

本技能不是一个"能跑的命令集合"，而是**五个有名字的机制**加上一条可核验的
链路。每个机制都要回答三个问题：**它是什么、没有它会怎样、怎么证明它真的在起作用**。
逐一写在 `references/MECHANISM.md`；可被别的技能复用的资产与采纳路径写在
`references/REUSABLE-ASSETS.md`。

**三条主张**（前两条是能力，第三条是这次变体的重点）：

1. **图画对** — 实体、关系、方向、数值、单位逐条可回溯到材料；
2. **图可改** — 文字可选、图层可拆、SVG 自描述，编辑只动被指明的元素；
3. **机制可被拆开检验** — 五个机制各自有"缺席实验"（拿掉它会出现什么）
   与"可证伪判据"（什么观测会推翻"它在起作用"），因此贡献不是笼统的
   "更好"，而是可指名的。

**本技能不做**：统计计算的数值方法选择、海报/封面版式、艺术插画美化、
论文正文写作。数据表里的数值是**事实输入**，不改算、不补造、不换算单位。

> 与基线包的结构差异：本包的正文主线是**机制索引**（§3），执行步骤（§4）
> 只作为"机制在流程中的位置"出现；边界情况的权威描述在
> `references/failure-modes.md`，而"为什么这条分支必须存在"回到 §3 的机制。
> 新增的两份文档分别承担"机制可检验"与"资产可复用"。

### 1. 适用条件

- 任务是"科研示意图/机制图/通路图/流程图/实验装置图/数据图"的**绘制或编辑**，
  workorder 一般形如 `editable_relationship_schematic`；
- 有来源材料（论文图注/正文摘录/Markdown/CSV/PDF），或要求对已有图稿做
  **源文件级**修改；
- 交付要求包含可编辑源文件、导出件与结构化结果（`result.json`）；
- 可能需要在**别的技能/别的题**里复用本包的某一部分（→
  `references/REUSABLE-ASSETS.md` 的采纳阶梯）。

### 2. 输入与输出

**输入（平台提供）**：`/input/case.json`（`case_id`/`workorder`/`figure_type`/
`sources`/可选 `manifest`、`entities+relations`、`data`、`edits`、`output_contract`）、
`/input/task.md`、`/input/` 下的材料（可能是 PDF）。
**以实际文件内容为准，不凭字段标签猜内容。**

**输出（写入 `/app/output`，全部运行时现场生成）**

```
/app/output/
├── figure.svg      # 可编辑分层源文件（自描述：内嵌 ER 清单 —— 机制 M2）
├── figure.png      # 渲染预览
├── figure.pdf      # 矢量导出件
├── result.json     # 结构化结果（OUTPUT_CONTRACT 全字段 + case_id）
└── work/           #（或 /app/work）entities.json / draft / layout / manifest.validated.json
```

| role | format | 是什么 | 完成标准 |
|-|-|-|-|
| `figure` | svg | 可编辑分层源文件 | 文字是真实 `<text>`（未被 path 化）、语义图层可拆、带 `id`/`data-*`、内嵌 ER 清单 |
| `preview` | png | 渲染预览 | 18 cm 宽有效 DPI ≥300（印刷）/≥150（屏幕）、色彩为 RGB 族 |
| `pdf` | pdf | 矢量导出件 | 可打开、页数可读、字体嵌入为尽力而为并如实记录 |
| `tiff` / `eps` | 对应格式 | 可选导出件（`--exports tiff,eps`） | 按目标单位要求生成；未逐项实测，见未解决项 |

> **包内不预置任何图稿或渲染件**（PDF/PNG/SVG/TIFF 都不随包分发）：
> 它们由本技能运行时生成；示例期望产物见 `examples/EXPECTED-OUTPUT.md`。

### 3. 机制索引（M1–M5）——本包的设计核心

每条机制的完整版（含"没有它会怎样"与"可证伪判据"）在
`references/MECHANISM.md`；这里是索引与落点。

| 机制 | 一句话 | 稀缺性（常规做法是怎么做的） | 落点 |
|-|-|-|-|
| **M1 方案先行** | 画之前先过 CP1 lint：kind 必须可映射、containment 必须分组、图例双向、调色板覆盖类别数 | 常规做法是"先画出来再说"，错误在成品里才被发现 | `scripts/spec_lint.py`（`spec.*` 一族检查名） |
| **M2 源文件自描述** | ER 清单**内嵌**进 SVG（`<metadata id="er-manifest">`），源文件自带语义 | 常规做法是图与数据分离，改标签要回头找数据源 | `scripts/svgbuilder.py`、`scripts/edit.py`、`svg.manifest_embedded` / `svg.manifest_matches` |
| **M3 抽取四段回退** | PDF 文本按 fitz → pypdf → PyPDF2 → **stdlib（zlib + Tj/TJ）** 逐级降级，backend 如实记录 | 常规做法是直接失败或静默空转 | `scripts/pdftext.py` |
| **M4 导出预检** | 导出前后自动查：有效 DPI、色彩族、文字是否可选中、PDF 结构、字体可用性 | 常规做法是"导出来再说"，投稿时才发现不达标 | `scripts/checks.py`（`bitmap.*` / `pdf.*` / `svg.editable_text` / `font.cjk`） |
| **M5 单一字体事实源** | render / checks / result.json 三方共用同一个字体探针，避免"各猜一个字体" | 常规做法是三处各自 fallback，结果互相矛盾 | `scripts/textfont.py` |

**机制清单（编号即本包声明的机制词汇表）**：

| 机制 | 名称 | 判据（可跑命令 / 可读字段） |
|-|-|-|
| M1 | 方案先行 | `spec_lint.py` 对坏清单 exit 1；`main.py` 对坏清单 `status=partial` + `fails=[spec_lint.*]` |
| M2 | 源文件自描述 | `svg.manifest_embedded` / `svg.manifest_matches` ok；无内嵌清单的 `--edit-svg` 必须 exit 2 |
| M3 | 抽取四段回退 | 无第三方 PDF 库时仍能抽；backend 字段随实际后端变化；缺文件 exit 2 |
| M4 | 导出预检 | `bitmap.dpi_print` / `bitmap.colourspace` / `svg.editable_text` / `artifact.<role>` 有读数 |
| M5 | 单一字体事实源 | `textfont.py --probe` 的结论与 `verification.render`、`font.cjk` 同源一致 |

**机制之间的依赖**（改动其中一个必须考虑另两个）：

```
M5 (字体事实源) ──► M4 (导出预检里的 font.cjk 与预览保真)
M3 (抽取回退)  ──► 材料可读性 ──► M1 (清单能不能建起来)
M2 (内嵌清单)  ──► 编辑能力；同时也是 M1 的持久化载体
M1 (生成前门)  ──► 决定 M2 里写进去的是什么（错清单会被拦住）
```

### 4. 执行流程（机制在流程中的位置）

**顺序：读契约 → 读材料 → 抽取 → 写清单 → M1 → 绘图 → M2/M4 →（编辑）
→ 契约门 → 自查。**

| 步 | 动作 | 激活的机制 |
|-|-|-|
| S0 | 读 `/input/task.md` 与 `/input/case.json`，记 `case_id`；解析 `output_contract` 的键与四形态（string→`""`、array→`[]`、object→`{}`、number/boolean→`0`/`false`，禁 `null`）；确认 `/app/output`、`/app/work` | — |
| S1 | 逐份读 `case.sources` 指向的**真实文件**；PDF 先过 `pdftext.py`；读不到的记入 `uncertainty` | **M3** |
| S2 | `extract.py` 产候选草稿（`_draft`），Agent 复核后写 `/app/work/entities.json`；`name` 逐字来自材料、`kind` 映射到 7 类规范词表、包含关系落到 `groups` | 为 **M1** 备料 |
| S3 | **CP1 lint 门**：`spec_lint.py --manifest …` → 只有 `{"valid": true}` 才继续 | **M1** |
| S4 | 绘图：`main.py --case … --manifest … --out /app/output`；产出 SVG/PNG/PDF + `result.json` | **M2**（生成内嵌清单）、**M5**（字体） |
| S5 | **CP2 产物检查**：溯源比例、图例双向、数据映射、导出预检 | **M4**、**M5** |
| S6 | （编辑）`--edit-svg` 走源文件级增量修改；编辑请求写在 `edit_requests`；改完重跑 CP2 | **M2** |
| S7 | 契约门 `validate_result.py`（G1–G8）→ VALID；确定性双跑；打包形态自查 | M1–M5 的综合 |

命令行（自定位，任意 cwd 可跑）：

```bash
SKILL_DIR="$(cd "$(dirname "<本 SKILL.md 的实际路径>")" && pwd)"

python "$SKILL_DIR/scripts/extract.py" --inputs /app/work/pdftext/<stem>.txt --out /app/work/draft-entities.json
python "$SKILL_DIR/scripts/spec_lint.py" --manifest /app/work/entities.json      # M1
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --manifest /app/work/entities.json     --work /app/work --out /app/output                                           # M2/M4/M5
python "$SKILL_DIR/scripts/validate_result.py" --case /input/case.json --result /app/output/result.json
```

### 5. 退出码与降级语义（每条降级都要指到某个机制）

| 退出码 | 含义 | result.json | 重试语义 |
|-|-|-|-|
| `0` | `status=success`；允许存在已被 `acknowledged_issues` 确认的 warn | 写出，`verification.checks.fail_count == 0` | 无需重试；可提高画质/补导出 |
| `1` | `status=partial`（有 fail 明细）或 `status=failed`（流水线异常） | **仍然写出**，fail 明细可逐条查 | 按 fail 明细定向修复后重跑；不要原样重跑 |
| `2` | 致命：case 无法定位/解析、编辑目标无内嵌清单、目录里没有 case.json | **不写出** | 先解决输入问题再跑，重试无意义 |

| 降级 | 说明 | 与机制的关系 |
|-|-|-|
| 镜像渲染（无 cairosvg/svgwrite） | PNG/PDF 是与 SVG 同源的 matplotlib 镜像，**语义一致、非逐像素**，写 `uncertainty` | 影响 M4 的判据强度（预检仍做，但"预览保真"降级） |
| PDF stdlib 回退 | backend 记为 stdlib，抽取质量可能下降 | M3 的第四段回退，**不隐藏** |
| CJK 字体缺失 | SVG 文字仍在（M2 保证文字是 `<text>`），PNG 可能缺字 | M5 报告事实，M4 记 warn |
| `--skip-checks` / `--no-lint` | 跳过 M1 或 M4 ⇒ 该次运行不得当作交付版本 | 直接关掉机制，必须显式标注 |
| 编辑目标不存在 | 日志 `[edit] fail`；`change_records` 条数对不上 | 该分支**不进 result.json**（M2 的已知盲区，见 MECHANISM §M2.4） |

### 6. 异常处置速查（权威描述见 `references/failure-modes.md`）

| 情形 | 处置 | 相关机制 |
|-|-|-|
| 来源材料缺失 | 记录 `sources`/`uncertainty`，以已读材料继续；多处缺失则 `status=partial` | M3 |
| 材料描述矛盾（方向/数值冲突） | 取有证据的一种，另一种连同出处写入 `uncertainty` | — |
| 实体名找不到出处 | **禁止上图**（no-fabrication）；删条或补 `evidence` | M1 |
| kind 无法映射 | CP1 fail → 回材料用原文动词改写后重跑 | M1 |
| 包含关系画成箭头 | 改成 `groups` 分组框 | M1 |
| 图例缺项 / 孤儿项 | 以数据表为基准修图例后重跑 | M1、M4 |
| 调色板 < 类别数 | 补齐或删冗余类别 | M1 |
| CJK 字体缺失 | 仍出 SVG；`font.cjk` warn + `uncertainty` | M5、M4 |
| PDF 加密/扫描件 | `pdftext.py` 报不可抽取，**不伪造文本** | M3 |
| 渲染/导出致命错 | 捕获 → 写 `status=failed` 的 `result.json`（`fails=[pipeline]`） | — |
| 编辑请求条数 ≠ `change_records` 条数 | 判为编辑失败，按 `references/EDIT-ACTION-SCHEMA.md` 查字段名 | M2 |
| 用了 `--skip-checks`/`--no-lint` | 交付前必须用默认参数完整重跑 | M1/M4 |

### 7. 资源文件说明（路径相对技能根，调用一律 `"$SKILL_DIR/..."`）

| 入口 | 角色 | CLI |
|-|-|-|
| `scripts/main.py` | 流水线入口 | `--case --manifest --out --work --edit-svg --base-name --exports --dpi --skip-checks --lint --no-lint --fixed-time --doc-check` |
| `scripts/extract.py` | 材料→候选 ER 清单草稿 | `--inputs --out --base-dir` |
| `scripts/pdftext.py` | PDF 文本抽取（**机制 M3**） | `--pdf --out` |
| `scripts/textfont.py` | 字体栈探测（**机制 M5**） | `--list --probe` |
| `scripts/spec_lint.py` | CP1 生成前 lint（**机制 M1**） | `--manifest --dict --json` |
| `scripts/manifest.py` | ER 清单加载/规范化 | `<manifest.json>` |
| `scripts/layout.py` | 布局引擎（库模块） | — |
| `scripts/svgbuilder.py` | 分层可编辑 SVG 构建（**机制 M2**） | — |
| `scripts/render.py` | matplotlib 镜像渲染（库模块） | — |
| `scripts/checks.py` | CP2 产物检查（**机制 M4**） | — |
| `scripts/edit.py` | 源文件级增量编辑（**机制 M2**） | `<figure.svg> <edits.json>` |
| `scripts/validate_result.py` | 契约独立校验 G1–G8 | `--case --result --out --json` |
| `scripts/selftest.py` | 模块级自测 | — |
| `scripts/run_examples.py` | 一键复现三示例 | `--out --keep` |
| `scripts/report.py` | 结果渲染辅助（库模块） | — |
| `scripts/doccheck.py` | **本包新增**：文档↔代码一致性对拍（只读） | `--root --files --json` |

| 其它文件 | 用途 |
|-|-|
| `references/MECHANISM.md` | **本包新增**：M1–M5 的完整机制说明（含"没有它会怎样"与可证伪判据） |
| `references/REUSABLE-ASSETS.md` | **本包新增**：可复用资产清单（A1–A12）与采纳阶梯（L0–L4） |
| `references/OUTPUT_CONTRACT.md` | `result.json` 契约 + G1–G8 硬门 + 四形态回显（**必读**） |
| `references/CHECK-INDEX.md` | 全部检查名清单（级别 + 科学含义）——机制可证伪判据的取值来源 |
| `references/EDIT-ACTION-SCHEMA.md` | 编辑动作 → 字段名 → 记录 的对照表与反模式 |
| `references/failure-modes.md` | 题面 12 类失败形态 → 检测 → 处置 → 相关机制 |
| `references/ER_MANIFEST.md` | 实体—关系清单规范（绘图唯一数据源） |
| `references/DRAWING_GRAMMAR.md` | 图形语法：关系语义→箭头/线型/颜色、方向判定、分组/层级、图例/数据映射 |
| `references/RUBRIC_MAP.md` | 五维评分（40/25/15/10/10）→ 本包文件/机制逐条映射 |
| `assets/relation-dict.json` | 连接规则字典（kind→arrow/line/dash/color，机器可读） |
| `assets/checklist.json` | CP1–CP5 检查点 + 自查清单（机器可读） |
| `examples/*` | 最小示例（schematic / chart / edit + 合成材料 + `EXPECTED-OUTPUT.md`），**示例非正式案例** |

### 8. 五维评分映射（交付前逐条自评；完整表见 `references/RUBRIC_MAP.md`）

| 维度 | 分 | 本包机制（可跑的检查，不是自述） | 证据文件 |
|-|-|-|-|
| 实际效果 | 40 | 材料→ER 清单→M1 门→可编辑 SVG（M2 自描述）→PNG/PDF（M4 预检）→result.json 一条命令跑通 | `scripts/main.py`、`scripts/spec_lint.py`、`scripts/checks.py`、`scripts/svgbuilder.py` |
| 使用增益 | 25 | 三层门每次运行自动执行；素材→图稿一条命令；改数据只改清单即重绘；编辑走内嵌清单增量改 | `scripts/main.py`、`scripts/edit.py`、`TEST.md` |
| 创新增益 | 15 | **M1–M5 五个具名机制**，每个都给出"没有它会怎样"与**可证伪判据**；机制之间有显式依赖图；`references/MECHANISM.md` 还列出各机制的**已知盲区**（不让创新点逃避检验） | `references/MECHANISM.md`、`scripts/spec_lint.py`、`scripts/edit.py`、`scripts/pdftext.py`、`scripts/checks.py`、`scripts/textfont.py` |
| 可靠体验 | 10 | 自定位（任意 cwd 可跑）；`--case` 兼容文件与目录；退出码 0/1/2 与 `status` 同向；降级逐条指到受影响机制；失败分支仍写 result.json | §5、§6、`references/failure-modes.md` |
| 生态贡献 | 10 | **`references/REUSABLE-ASSETS.md`：12 项可复用资产 + 5 级采纳阶梯（含最小采纳与验证方式）**；README/README 的复用步骤；机器可读字典与清单；契约校验器；文档↔代码对拍器；三示例题集 | `references/REUSABLE-ASSETS.md`、`assets/*`、`scripts/*`、`examples/*` |

### 9. 自查清单（提交前逐行确认；机器版 `assets/checklist.json`）

- [ ] 实体名逐字出自材料，无材料外基因/浓度/时间点/单位；
- [ ] 每个关系方向与材料一致（激活≠抑制、上下游不颠倒、包含用分组）；
- [ ] **M1 生效**：CP1 `{"valid": true}`（kind 可映射、containment 用分组、图例双向、调色板 ≥ 类别数）；
- [ ] **M2 生效**：`figure.svg` 文字可选中、图层可拆、内嵌 ER 清单、`svg.manifest_matches` 为 ok；
- [ ] **M4 生效**：PNG 有效 DPI 达标、色彩 RGB 族、PDF 可打开；
- [ ] **M5 生效**：`font.cjk` 有明确记录（True 或 warn + `uncertainty`）；
- [ ] 数值/单位与数据表逐项一致，改数据后图确实重绘；
- [ ] `result.json` 含全部契约键 + `case_id`，四形态回显无 `null`；
- [ ] `validate_result.py`（G1–G8）输出 VALID，退出码 0；
- [ ] 编辑任务：**请求条数 == `change_records` 条数**，未改动元素保持原样；
- [ ] 交付前最后一次运行**没有**用 `--skip-checks` / `--no-lint`；
- [ ] 形态：仅 7 种文本扩展名、无 `__pycache__`、≤50 文件、≤500KB/文件、≤2MB、包内无本机绝对路径。

### 10. 依赖与限制

- Python 3.9+（实测 3.13）；运行必需 **matplotlib / Pillow / numpy**，reportlab 可选；
  PDF 抽取按 M3 的四段回退逐级降级。建议先跑 `python "$SKILL_DIR/scripts/selftest.py"`；
- **平台运行契约**：技能装在 `/skills/weekly-skill`；输入 `/input/case.json` + `/input/task.md`；
  中间产物 `/app/work`；最终产物 `/app/output`。预算 64 请求 / 900 秒 / 16384 token/响应；
- **资源形态（硬约束）**：仅 UTF-8 文本（`.md/.py/.json/.txt/.csv/.yaml/.yml`），
  ≤50 个、单文件 ≤500KB、合计 ≤2MB、无符号链接；图稿与渲染件一律运行时生成；
- **已知限制（如实标注，并指到受影响机制）**：预览为同源镜像非逐像素（M4 判据强度）；
  PDF 字体嵌入审计为尽力而为（M4）；CJK 依系统字体（M5）；`extract.py` 只产草稿；
  走 `--edit-svg` 时 `edits` 字段不生效（用 `edit_requests`）；
  **`edit.*` 问题只进 stdout**，不进 result.json、不改退出码（M2 的已知盲区）；
  TIFF/EPS 的期刊级合规未逐项实测。

### 11. 禁止事项

- 不提交预制答案/正式案例输出；示例只用于演示接口与流程，**示例产物不入包**；
- 不编造缺失的软件状态或科学数据（来源里没有的实体/数值一律不画）；
- 不宣称未经测量的增益或未验证的机制；**每个机制的"可证伪判据"必须能被真实观测检验**；
- 不为"好看"改关系颜色（改色 = 图例不一致）。
