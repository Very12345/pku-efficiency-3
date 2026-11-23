# STRENGTH-AXES — 增益 / 机制 / 复用（三份强化文档的合并本，内容逐字保留）

> 本文件把三条强化轴各自独立的 reference 合并为**一个**文件，以便把包内文件数
> 稳定留在题面硬上限（50 个 UTF-8 文本文件）以内。**合并只为文件数，正文逐字保留**：
>
> | 节 | 内容 | 原文档 | 规则编号 |
> |-|-|-|-|
> | §A | 增益对照协议：对照臂定义、公平性约束、指标口径、实测读数、未测量清单 | `GAIN-PROTOCOL.md` | F1–F8 / I1–I10 / R1–R13 |
> | §B | 具名机制：每个机制的"没有它会怎样"与可证伪判据 | `MECHANISM.md` | M1–M5 |
> | §C | 可复用资产与 5 级采纳阶梯、复用坑 | `REUSABLE-ASSETS.md` | A1–A12 |
>
> 包内其它文档引用这三节时统一写作 `references/STRENGTH-AXES.md §A/§B/§C`。
> 三节里的实测数字是**包作者在本机真实跑出来的读数**，不含任何平台分数。

---

## §A 增益对照协议（原 GAIN-PROTOCOL.md；条款 F1–F8 / 指标 I1–I10 / 实测 R1–R13）

本文件是本题"使用增益（25 分）"的可核验载体。它分五部分：

1. **对照协议**（§1）：两臂怎么跑才叫公平；
2. **指标定义**（§2）：测什么、从哪取值；
3. **真实对照记录**（§3）：本机实际跑出来的数字，逐条给命令；
4. **能支撑与不能支撑的结论**（§4）：把"未测量"写在明面上；
5. **记账模板**（§5）：任何人复跑后可以直接填空产出同格式记录。

> **先说清楚本协议的边界**：题面写明"平台固定运行 3 个案例，比较不加载 Skill 与
> 加载参赛 Skill 时的实际结果"，并说明"白板是对照结果，不是参赛者答案"、
> "参赛者无须另交三个测试案例、白板或预先生成的正式答案"。
> 因此 **§3 记录的是"CLI 空间"的夹具级对照（本技能在固定示例上的可复现读数），
> 不是平台计分对照**。平台计分对照由组织方执行；本协议提供的是：让任何人
> **用同一套命令、同一套判据**复现本技能一侧的全部读数，并把基线一侧的口径钉死。

## 1. 对照协议（公平性条款 F1–F8）

| # | 条款 | 具体做法 | 违反后果 |
|-|-|-|-|
| **F1** | 同输入 | 两臂使用同一 `case.json`、同一材料文件、同一 `output_contract` | 输入不同 ⇒ 任何差异都无法归因 |
| **F2** | 同画布与导出参数 | 同一 `style.canvas`、同一 `--dpi`、同一 `--exports`；**把这些参数写进记账** | 改了画布/DPI，DPI 与排版类指标全部不可比 |
| **F3** | 同预算 | 同一模型、同一 64 请求 / 900 秒 / 16384 token 响应预算（题面运行契约） | 预算不同 ⇒ 效率类结论失效 |
| **F4** | 同模型与框架 | 对照臂**不加载**本 Skill，其余条件一致 | 增益必须归于 Skill，不能归于模型升级 |
| **F5** | 同判据 | 两臂用**同一个** `scripts/validate_result.py`（G1–G8）判定契约有效性 | 各写一套判据 = 自己给自己打分 |
| **F6** | 夹具固定 | `examples/` 三件套固定不改；对照运行不得为提高读数而调整夹具 | 改夹具 = 改题 |
| **F7** | 失败也记录 | 任一臂失败都记 exit code 与 fail 明细，不得丢弃重试直到好看 | 选择性报告 |
| **F8** | 不可测就标注 | 没有真正跑过的指标写"未测量"，不得用推断值顶替 | 不可核验的声明 |

### 1.1 关于 F5 的一处反向说明（有偏判据的处理）

用"被测方自带的判据"去评判被测方，**本身是有偏的**。本协议不假装没有这个偏差，
而是把它固定下来：

- 同一判据对两臂**同等生效**，因此偏差是**系统性的**，不偏向任一臂；
- 判据只管**结构与契约**（字段齐不齐、文字可不可选、图例与数据是否同源、
  导出参数是否达标），**不管科学结论对不对**；
- 科学正确性由题面明确的途径承担：*"scientific judgement remains native/LLM Judge,
  not a literal quote or export pass"*；
- 因此 §3 的一切数字都应读作"**结构与可核验性**的读数"，而不是"科学质量分数"。

### 1.2 两臂的最小可执行定义

| 臂 | 定义 | 最小命令 |
|-|-|-|
| **A（对照）** | 不加载本 Skill 的 Agent：只有 `/input/case.json`、`/input/task.md` 与材料；被要求"产出示意图"，**不告知**任何契约、门、字段要求 | 由平台/复跑者执行；本包不预置其答案 |
| **B（本技能）** | 加载本 Skill：按 `SKILL.md` 的 M0–M6 执行，产出三类产物 + `result.json` | 见 §3 的 R1–R13 |
| **判据** | 两臂产物都过同一个 `validate_result.py`，并用同一个指标字典（§2）打分 | `python "$SKILL_DIR/scripts/validate_result.py" --case … --result …` |

**注意**：A 臂的"最小命令"故意留空。写下一条命令不难，但那会是**我们替基线写的答案**，
恰好是题面禁止的"预置白板"。因此 A 臂读数只能来自真实对照运行。

## 2. 指标定义（I1–I10）

| 指标 | 定义 | 档位/取值 | 机器可读来源 | A 臂的常见形态（预期，非实测） |
|-|-|-|-|-|
| **I1 契约有效性** | `validate_result.py` 是否 VALID | 0/1 | 命令退出码 | 无 `result.json` 或字段不全 ⇒ 0 |
| **I2 结构完整性** | 可编辑源 + 预览 + 导出三类产物是否齐全 | 0–3 | `artifacts[].role`、G7 | 常见只有位图 ⇒ 1 |
| **I3 可编辑性** | `<text>` 是否存在、图层是否可拆、是否带 `id`/`data-*` | 三个布尔 | `svg.editable_text`、`svg.layers`、`svg.data_entity_attrs` / `svg.data_relation_attrs` / `svg.data_source_attrs` | 常见栅格化/path 化 ⇒ false |
| **I4 溯源比例** | 带 `source`（+`evidence`）的实体/关系占比 | 0–100% | `traceability.entities`、`traceability.relations` | 无"出处字段"概念 ⇒ 分母为 0 或不可比 |
| **I5 关系语义** | kind 可映射 + containment 用分组 + 无自环告警 | fail/warn 计数 | `spec.relation_kind`、`spec.containment_group`、`spec.relation_selfloop` | 无判据 ⇒ 无法取值 |
| **I6 图例一致** | 图面箭头类型 ↔ 图例条目双向一致 | 缺项/孤儿项计数 | `spec.legend_missing_kinds`、`legend.orphan_items` | 手工图例，无双向校验 |
| **I7 数据映射** | 类别↔颜色↔图例同源、调色板覆盖类别数、单位上轴 | fail/warn 计数 | `spec.color_category_count`、`data_mapping.*` | 颜色数与类别数常见不符 |
| **I8 导出合规** | 18 cm 宽有效 DPI、色彩族、PDF 结构、字体 | 达标布尔 + 数值 | `bitmap.dpi_print`、`bitmap.colourspace`、`pdf.*`、`font.cjk` | 少见导出前预检 |
| **I9 返工轮次** | 从材料到"门全过"的连续运行次数 | 整数 | **人工记账**（CP1 第 k 次 valid） | 无门 ⇒ "过"无定义 |
| **I10 端到端耗时** | 一条命令出齐产物并跑完门 | 秒 | 命令墙钟时间 | 可比，但需 F1–F3 一致 |

**为什么把 I9 列为"人工记账"也是可核验的**：它不依赖主观判断，只依赖
"第几次运行 CP1 才 valid"这一可复现事实。记录方式见 §5。

## 3. 真实对照记录（CLI 空间，本机实测）

- 环境：Python **3.13.9 (Anaconda)**、matplotlib 3.10.6；已装 Pillow / numpy /
  reportlab / PyMuPDF(fitz)；无 cairosvg/svgwrite（与平台同类：预览走 matplotlib 镜像）。
- 夹具：本包 `examples/` 三件套（`case.json` schematic / `case_chart.json` chart /
  `case_edit.json` edit），**固定不改**（F6）。
- 臂：**B（本技能）**。**A 臂未运行**——见 §4。
- 全部命令用 `$SKILL_DIR` 指向技能根，产物写在包外。

| # | 场景 | 命令要点 | 实测读数 | 指标 |
|-|-|-|-|-|
| R1 | 标准 schematic | `main.py --case examples --out <t>` | **exit 0**；墙钟 **1.53 s**；`status=success`；三类产物齐全（svg 15241 B / png 124129 B / pdf 37929 B）；`result.json` 顶层 **23** 键 | I1、I2、I10 |
| R2 | 同 R1，cwd 在包外 | 同上 | **exit 0**；1.53 s；`figure.svg` sha256 `163e20f7…` 与 R1 **完全相同** | I10、自定位 |
| R3 | 契约门 | `validate_result.py --case examples/case.json --result <t>/result.json` | **exit 0 / VALID**（G1–G8 全过） | I1 |
| R4 | 三示例端到端 | `run_examples.py --out <t>` | **exit 0**；墙钟 **4.99 s**；三步各 exit 0；三份契约各 VALID；顶层键 23 / 21 / 21 | I1、I2、I10 |
| R5 | 确定性双跑 | `main.py … --fixed-time 2026-01-01T00:00:00+0800` ×2 | 两次 `figure.svg` **逐字节一致**（sha256 `163e20f7…`）；两份 `result.json` **唯一差异键是 `artifacts`**（`abspath`），去 `abspath` 后完全相同 | I9 前置 |
| R6 | 数据更新传播 | chart 数据表数值翻倍后重跑 | `figure.svg` sha `fd54b008…` → `29c52b98…` ⇒ **图随数据重绘** | I7 |
| R7 | 材料缺失 | `sources` 指向不存在文件 | **exit 0**、`status=success`，`sources=[]`、`uncertainty` **3** 条 | I4 诚实性 |
| R8 | 未知关系类型 | kind 改 `gibberish` | **exit 1**、`status=partial`、`fails=[spec_lint.spec.relation_kind]`、`spec_lint.valid=false` | I5 |
| R9 | 无依据即停 | 无 manifest 且 case 无 entities | **exit 1**；写 `status=failed`；`fails=[pipeline]` | I1 不造假 |
| R10 | 编辑增量 | `--edit-svg` + 5 个动作（字段名正确） | **exit 1**（夹具触发 `spec.group_member`）；`change_records` **7** 条（含 2 条 `cascade_remove_relation`）；实体 6→5、关系 5→3；契约仍 VALID | I2、I9 |
| R11 | 编辑目标不存在 | `relabel` 指向 `R99` | 日志 `[edit] fail unknown relation R99`；`change_records` **0** 条；**exit 0**、契约仍 VALID | §1.2 半自动判据 |
| R12 | 草稿抽取 | `extract.py --inputs examples/sources/figure03-note.md` | **exit 0**；墙钟 **0.12 s**；17 实体 / 4 关系 / 5 组，**全部带 `_draft`** | I9 代理量 |
| R13 | 追加导出 | `--exports tiff,eps` | **exit 0**；TIFF ≈ **46 MB**（未压缩 4500×2580@300dpi） | I8 |

### 3.1 可复跑性说明

- 这些数字来自**同一夹具的多次真实运行**；命令列在 `TEST.md` §M2–§M5，
  逐条可复跑；
- 时间类读数（R1/R2/R4/R12）受机器负载影响，**只能作量级参考**，
  不得用于声称"比基线快"；
- sha256 类读数（R2/R5/R6）不随机器变化，可作为**回归判据**使用。

## 4. 能支撑 / 不能支撑（本协议最重要的一节）

| 结论 | 支撑状态 | 依据 |
|-|-|-|
| 本技能能在固定夹具上稳定产出「可编辑源 + 预览 + 导出 + 契约有效」| ✅ **已支撑** | R1–R4 |
| 同一输入下产出确定（除时间戳与输出目录） | ✅ **已支撑** | R5 |
| 改数据后图确实随之重绘 | ✅ **已支撑** | R6 |
| 错误输入被拦下并显式降级，而非静默出图 | ✅ **已支撑** | R7–R9 |
| 编辑是增量修改且有 before→after 记录 | ✅ **已支撑** | R10 |
| **本包在平台打分上高于"不加载 Skill 的基线 Agent"** | ❌ **未测量** | A 臂未运行；平台对照由组织方执行 |
| **返工轮次/人工修改量低于基线** | ❌ **未测量** | I9 需要 A 臂同夹具读数才能比较 |
| **端到端耗时低于基线** | ❌ **未测量** | 只有 B 臂绝对量（约 1.5 s/例），无 A 臂对照 |
| **科学结论（机制、方向）正确性优于基线** | ❌ **未测量** | 属 native/LLM Judge 范围，本协议的机器判据不覆盖 |

**这张表的用法**：任何人在交付说明或答辩里引用本包时，只能引用"已支撑"那一半；
引用"未测量"那一半必须补上真实对照运行。写这张表的目的就是让"不夸口"变成
一条可检查的工程约束，而不是一句态度。

## 5. 记账模板（复跑时直接填空）

```text
case_id            :
参数快照           : canvas=?  --dpi=?  --exports=?  模型/预算=?
臂                 : A（无 Skill）/ B（本技能）
I1 契约            : validate_result exit=?  VALID/INVALID
I2 产物            : figure=? preview=? export=?  （role 清单）
I3 可编辑性        : svg.editable_text=?  svg.layers=?  svg.data_entity_attrs / svg.data_relation_attrs / svg.data_source_attrs=?
I4 溯源            : traceability.entities=?  traceability.relations=?
I5 关系语义        : spec.relation_kind=?  spec.containment_group=?  selfloop 告警=?
I6 图例一致        : spec.legend_missing_kinds=?  legend.orphan_items=?
I7 数据映射        : spec.color_category_count=?  data_mapping.color_count=?
I8 导出合规        : bitmap.dpi_print=?  bitmap.colourspace=?  pdf.*=?  font.cjk=?
I9 返工轮次        : CP1 第 ? 次 valid；编辑请求 ? 条 / change_records ? 条
I10 耗时           : 墙钟 ? s（注明机器负载）
降级与不确定性     : uncertainty 条数=?  逐条摘要
未测量项           : <显式列出>
判据版本           : validate_result.py sha256:?
夹具版本           : examples/ sha256:?
```

模板里**必须有"未测量项"一行**：留空等于声称"没有未测量项"，那是 F8 的违规。

## 6. 复跑命令（一屏内）

```bash
SKILL_DIR="$(cd "$(dirname "<本 SKILL.md 的实际路径>")" && pwd)"

# B 臂：三示例端到端 + 契约门
python "$SKILL_DIR/scripts/run_examples.py" --out /tmp/gp-examples

# B 臂：单例 + 确定性双跑
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out /tmp/gp-a --fixed-time 2026-01-01T00:00:00+0800
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out /tmp/gp-b --fixed-time 2026-01-01T00:00:00+0800
python -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" /tmp/gp-a/figure.svg
python -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" /tmp/gp-b/figure.svg

# 判据（两臂都用这一条）
python "$SKILL_DIR/scripts/validate_result.py" --case "$SKILL_DIR/examples/case.json" --result /tmp/gp-a/result.json

# 文档与代码是否仍然一致（防止判据漂移）
PYTHONDONTWRITEBYTECODE=1 python -B "$SKILL_DIR/scripts/doccheck.py"
```

## 7. 修订记录

| 时间 | 变更 |
|-|-|
| 本包首次交付 | 建立 F1–F8 条款、I1–I10 指标、R1–R13 实测记录、§4 可支撑/不可支撑表、§5 记账模板 |

**维护要求**：任何脚本行为改变（新增检查、改字段名、改退出码）后必须重跑 §6 的
命令并更新 §3 与 §4；否则本协议会退化成过时文档。

---

## §B 具名机制（原 MECHANISM.md；M1–M5）

本文件是 `SKILL.md` §3 机制索引的完整版。每个机制写四段：

1. **是什么** — 机制的定义与落点；
2. **没有它会怎样** — 具体会退化成哪一种失败（不是"差一点"，而是可指名的失败形态）；
3. **可证伪判据** — 什么观测会**推翻**"这个机制在起作用"；
4. **已知盲区** — 这个机制**测不到**什么（写出来，免得它变成万能借口）。

> 写作约定：判据必须是**可跑的命令或可读的字段**，不能是"感觉更可靠"。
> 检查名与级别的完整清单见 `references/CHECK-INDEX.md`；
> 每个判据在本机是否实测过，见 `TEST.md` §V2。

---

## M1 方案先行（plan-before-draw）

### M1.1 是什么
在**画之前**跑一道 lint 门：`scripts/spec_lint.py --manifest <entities.json>`。
门覆盖：实体非空且 id/name 有效；关系 `from`/`to` 指向存在实体；
`kind` 能映射到 7 类规范词表（activation / inhibition / recruitment / process /
transcriptional / causal / containment）；containment **必须**用 `groups` 表达；
图例与图面箭头类型**双向**一致；chart 调色板长度 ≥ 唯一类别数、单位已声明。
`main.py` 默认内嵌这道门（`--lint` 默认开）。

### M1.2 没有它会怎样
退化为"先画出来再说"。具体后果按严重度排：

| 后果 | 为什么 | 对应检查名 |
|-|-|-|
| 未知关系类型被悄悄画成某种箭头 | 画图阶段没有词表可依，凭感觉选箭头 | `spec.relation_kind` 本应 fail |
| 包含关系被画成箭头（层级被读成因果） | containers 与 relations 在画布上都表现为"线"，不拦就会混 | `spec.containment_arrow` / `spec.containment_group` |
| 图例缺项或孤儿项 | 图例往往在画完后"补"，补的时候已经和画面对不上 | `spec.legend_missing_kinds` |
| 调色板不够分 | 颜色数 < 类别数时会出现"两类同色" | `spec.color_category_count` |
| 发现错误的时机最晚 | 错误在成品里才暴露，返工要重排整张图 | — |

### M1.3 可证伪判据
- **正向**：`spec_lint.py --manifest <m.json>` 对**好清单**输出 `VALID (CP1)` 且退出码 0；
  对**坏清单**（未知 kind）输出 `INVALID (CP1)` 且退出码 1 —— 本机已实测（`TEST.md` §V2）；
- **反向（推翻条件）**：如果一份含未知 `kind` 或未分组 containment 的清单**也能**
  让 `spec_lint.py` 输出 `valid: true`，或让 `main.py` 的
  `verification.spec_lint.valid` 不为 false，则 M1 不成立；
- **端到端**：坏清单走 `main.py` 时，`status` 必须降为 `partial` 且
  `fails` 出现 `spec_lint.<检查名>` —— 本机已实测（`TEST.md` §V2）。

### M1.4 已知盲区
- M1 只做**结构**判断：它不知道"抑制"在生物学上是否真的成立，
  只检查这个关系有没有被声明为可映射的类型；
- 它不检查实体名是否**真的**出现在材料里（那需要逐条对照 `evidence`，
  属 Agent 判断 + `spec.traceability` warn）；
- `--no-lint` 会把 M1 整个关掉，而 `result.json` 里只会留下一个空对象
  （`verification.spec_lint = {}`）⇒ 交付前必须用默认参数重跑。

---

## M2 源文件自描述（self-describing source）

### M2.1 是什么
把 ER 清单**内嵌**进生成的 SVG：`<metadata id="er-manifest">` 里保存
entities / relations / groups / legend / style 的完整 JSON；每个图元带
`id` 与 `data-entity` / `data-relation` / `data-canon` / `data-source` 属性。
结果是：**SVG 自己就是数据源**，不需要回头找清单文件。
`scripts/edit.py` 正是靠读这份内嵌清单做增量编辑。

### M2.2 没有它会怎样
退化为"图与数据分离"：

| 后果 | 为什么 | 对应检查名 |
|-|-|-|
| 改一个标签要重画整张图 | 没有清单可改，只能改画布 | — |
| 无法做**源文件级**增量编辑 | 编辑需要"知道每个图元对应哪个实体" | `svg.manifest_embedded` |
| 图元与清单可能不一致 | 两份数据各自演化，没有校验点 | `svg.manifest_matches` |
| 溯源属性无法审计 | `data-*` 属性是溯源的载体 | `svg.data_entity_attrs` / `svg.data_relation_attrs` / `svg.data_source_attrs` |

### M2.3 可证伪判据
- **正向**：`figure.svg` 里能按 XML 解析出 `<metadata id="er-manifest">`，
  且 `svg.manifest_embedded` 与 `svg.manifest_matches` 为 ok；编辑后
  `change_records` 含 `before`/`after` —— 本机已实测（`TEST.md` §V2/§V3）；
- **反向（推翻条件）**：如果 `--edit-svg` 指向一个**没有**内嵌清单的 SVG
  也能成功编辑，或编辑后的 `figure.svg` 里查不到 `data-*` 属性，则 M2 不成立。
  实测后者会走 `exit 2` + `FATAL: no embedded ER manifest in …`；
- **增量性**：编辑后未改动元素应与编辑前一致（同一 `<text>` 内容、
  同一 `id`）；若整张图被重写，增量性不成立。

### M2.4 已知盲区（**必须写出来**）
编辑动作的错误（`edit.*`）**只出现在 stdout 日志**里：不进 `result.json`、
不改退出码。因此：

- 一个"目标不存在"的编辑请求会让 `change_records` 为空，
  而命令仍可能 `exit 0`、契约门仍然 `VALID`；
- 唯一可靠的判据是**条数对拍**："请求条数（按
  `references/EDIT-ACTION-SCHEMA.md` §1 推算期望值）" vs "`change_records` 条数"；
- 这不是"以后会修"的托词，而是**当前必须由 Agent 执行的检查步骤**，
  已写进 `SKILL.md` 的自查清单。

---

## M3 抽取四段回退（four-stage extraction fallback）

### M3.1 是什么
`scripts/pdftext.py` 按 **fitz → pypdf → PyPDF2 → stdlib（zlib + `Tj`/`TJ` 解析）**
逐级尝试抽取 PDF 文本，并把实际使用的 backend **如实写进结果**。
任何一个后端不可用都不导致整体失败。

### M3.2 没有它会怎样
退化为两种坏结果之一：

| 退化 | 后果 | 证据面 |
|-|-|-|
| 直接失败 | 环境里没有 PyMuPDF 就完全读不了 PDF，案例无法开始 | — |
| 静默空转 | 抽不出文本却继续往下走，图上出现"看起来像真的"的内容 | 这正是题面点名的失败形态 F12 |

没有 M3 时，"PDF 是扫描件/加密件"这类材料会被当成"有文本"处理，
而**编造文本**是本题最严重的错误之一。

### M3.3 可证伪判据
- **正向**：在**没有** fitz/pypdf 的环境里，`pdftext.py` 仍能对一个
  可抽取的 PDF 产出文本，且 backend 字段显示 stdlib 回退（`selftest.py`
  对回退路径有断言，见 `TEST.md` §V1）；
- **反向（推翻条件）**：如果 `pdftext.py` 对**不存在的文件**返回 0，
  或对伪造的 `%PDF` 头文件崩溃而非返回非零，则 M3 的边界处理不成立。
  实测：不存在 → `exit 2` + `FATAL: pdf not found`；伪造头 → `exit 1`（不崩）；
- **诚实性**：若 backend 字段恒为同一个值（无论实际用了哪个库），
  则"如实记录"这一点不成立。

### M3.4 已知盲区
- stdlib 回退的抽取**质量**取决于 PDF 的文本编码方式（压缩流、子集字体、
  自定义编码都可能抽不全）；回退成功 ≠ 抽全；
- 加密/扫描件**本来就不该**被抽出来，M3 的职责是"如实报告不可抽取"，
  不是"想办法抽出来"（OCR 属其它工具）。

---

## M4 导出预检（export pre-flight）

### M4.1 是什么
在写出产物后立刻检查，并把逐项明细写进 `result.json.verification.checks`：
`svg.editable_text`（文字是真实 `<text>`，未被 path 化）、`svg.layers`（语义图层）、
`bitmap.dimensions` / `bitmap.dpi_print`（18 cm 宽下的有效 DPI，印刷 ≥300 / 屏幕 ≥150）、
`bitmap.colourspace`（RGB 族）、`pdf.header` / `pdf.pages` / `pdf.fonts_embedded`、
`font.cjk`，以及每类产物的 `artifact.<role>` 存在性。

### M4.2 没有它会怎样
退化为"导出来再说"，失败在**投稿节点**才暴露：

| 后果 | 为什么 | 对应检查名 |
|-|-|-|
| 图能用但投不出去 | 分辨率/色彩/字体不合要求，改要重导 | `bitmap.dpi_print`、`bitmap.colourspace` |
| 文字不可选、图层不可拆 | 预览是栅格图被当成"源文件" | `svg.editable_text`、`svg.layers` |
| 缺文件却报成功 | 没有产物存在性检查 | `artifact.figure` / `artifact.preview` / `artifact.pdf` |
| 中文标注乱码未被发现 | 没有字体可用性检查 | `font.cjk` |

### M4.3 可证伪判据
- **正向**：一次正常运行的 `verification.checks` 里能读到上述项的实测值
  （本机实测：DPI ≈635 ≥300、色彩 RGBA、`svg.editable_text` ok、
  `font.cjk` True —— `TEST.md` §V3）；
- **反向（推翻条件）**：
  - 把 `--dpi` 降到远低于阈值后 `bitmap.dpi_print` **仍然 ok** ⇒ 判据失效；
  - 删掉某一个产物（或让它写失败）后**没有**出现 `artifact.<role>` fail ⇒ 存在性检查失效；
  - 把文字改成 path（或换成 fonttype 非 none）后 `svg.editable_text` **仍 ok** ⇒ 可编辑性检查失效；
- 以上三条都是可构造的"推翻实验"，任何人都能做——这正是 M4 可被检验的原因。

### M4.4 已知盲区
- `pdf.fonts_embedded` 是**尽力而为**的审计（解析 PDF 字体表），
  不等于目标期刊的硬性要求；
- `bitmap.dpi_print` 假设"18 cm 宽"这一常见印刷宽度，其它版面宽度需自行换算；
- 预检**不知道审美**：重叠、配色观感、字号是否合适，只做阈值与结构判断；
- `--skip-checks` 会跳过整个 M4（`verification.checks` 为空），
  而此时 `status` 仍可能是 `success` ⇒ 该次运行不得当作交付版本。

---

## M5 单一字体事实源（single source of font truth）

### M5.1 是什么
`scripts/textfont.py` 探测系统可用字体（候选族：微软雅黑 / SimHei / Noto CJK 等），
`render.py`、`checks.py`、`result.json` 三方**共用同一个探测结果**，
不再各自 fallback。`--list` 打印逐候选族的命中情况，`--probe` 输出机器可读结论。

### M5.2 没有它会怎样
退化为"三处各猜一个字体"：

| 后果 | 为什么 |
|-|-|
| 预览用的字体与检查报告的字体不一致 | 渲染与检查各自探测，环境差异时结论互相矛盾 |
| `result.json` 里的字体信息不可信 | 第三处又猜一次 |
| 中文缺字问题被误报或漏报 | 探测口径不同 ⇒ `font.cjk` 的布尔值没有统一定义 |
| 无法定位"为什么这台机器上字变了" | 没有单一的 `--list` 入口 |

### M5.3 可证伪判据
- **正向**：`textfont.py --probe` 输出包含解析到的族名与 `cjk_ok` 布尔，
  且同一输入下**两次运行结果相同**（确定性）—— `selftest.py` 对确定性有断言
  （`TEST.md` §V1）；
- **反向（推翻条件）**：如果 `render.py` 用的字体族与 `result.json` 里记录的
  字体族在**同一台机器同一次运行**里不一致，则"单一事实源"不成立；
  这个检查可以直接比对 `verification.render` 与渲染日志；
- **可定位性**：`--list` 应逐候选族打印 `[x]/[ ]` 与最终解析结果；
  若 `--list` 不给出逐候选信息，则"可定位"这一点不成立。

### M5.4 已知盲区
- 探测**只回答"能不能用"**，不回答"字形对不对"（数学符号覆盖、
  连字、上标下标可能仍缺）；
- 没有 CJK 字体时，PNG 会缺字而 SVG 文字仍在 —— M5 只能报告，
  不能凭空补出字体；
- 字体探测依赖运行环境的字体目录，**跨机器结果会不同**，
  因此 `font.cjk` 的取值必须与机器信息一起记录才有意义。

---

## 机制之间的关系与联合判据

| 联合场景 | 需要哪几个机制同时成立 | 联合判据（可跑） |
|-|-|-|
| "错误在生成前被拦下" | M1 | 坏清单 → `spec_lint` INVALID（exit 1）；走 `main.py` → `status=partial` 且 `fails=[spec_lint.*]` |
| "图可以被继续维护" | M2 | 编辑后 `change_records` 含 before/after；未改动元素保持；`svg.manifest_matches` ok |
| "看得懂的材料都能读" | M3 | 有无第三方 PDF 库都能跑；backend 字段随实际路径变化 |
| "交出去能被期刊接住" | M4 + M5 | `bitmap.dpi_print` 达标、`svg.editable_text` ok、`font.cjk` 有记录 |
| "换了人/换了机器还能复现" | M1+M2+M5 | 确定性双跑同 sha；`font.cjk` 与机器信息一起记录 |

**联合判据的意义**：单个机制的判据可能被"恰好通过"蒙混，但联合判据要求
多个不相关的事实同时成立，蒙混成本高得多。

## 机制的修改纪律

改动任何一个机制（改检查名、改字段名、改回退顺序、改字体候选）时：

1. 先在本文件更新对应的**可证伪判据**（判据变了，机制的定义就变了）；
2. 同步**受影响的下游**：本文件的依赖图给出了影响范围
   （例：改 M5 的候选族会影响 M4 的 `font.cjk` 与预览保真）；
3. 重跑 `python "$SKILL_DIR/scripts/selftest.py"` 与
   `PYTHONDONTWRITEBYTECODE=1 python -B "$SKILL_DIR/scripts/doccheck.py"`
   （后者会检查"文档提到的检查名"是否还真实存在）；
4. 在 `TEST.md` 里补一条新的实测读数 —— **没有实测读数的机制判据视为未验证**。

---

## §C 可复用资产与采纳阶梯（原 REUSABLE-ASSETS.md；A1–A12）

本文件回答一个具体问题：**如果别人（或别的技能题）想用本包的成果，
可以拿走哪一块、怎么拿、拿完怎么知道拿对了。**

清单分四类：**题集与金标准**、**规范与字典**、**校验与对拍工具**、
**预设与模板**。每项给出：资产位置、复用方式、依赖、以及**采纳验证**
（拿对没拿对，怎么一眼看出）。

## 1. 资产总表（A1–A12）

| # | 资产 | 位置 | 类型 | 复用方式 | 采纳验证 |
|-|-|-|-|-|-|
| **A1** | 合成示例题集（schematic / chart / edit 三件套 + 合成材料） | `examples/case.json`、`examples/case_chart.json`、`examples/case_edit.json`、`examples/sources/*` | 题集 | 直接当新技能的回归夹具；或改造成新案例（保持字段结构） | `run_examples.py --out <tmp>` **exit 0** 且三份契约各 VALID |
| **A2** | 期望产物清单（文字版金标准） | `examples/EXPECTED-OUTPUT.md` | 金标准 | 作为"应该产出什么"的对照表；新案例照抄结构填新值 | 逐条对照真实产物：文件齐全、字段取值一致 |
| **A3** | ER 清单规范 | `references/ER_MANIFEST.md` | 规范 | 任何"材料→结构图"任务都可直接采用（实体/关系/分组/图例/data/style 六块） | 用 `scripts/manifest.py <m.json>` 规范化不报错；`spec_lint.py` 能判 valid/invalid |
| **A4** | 图形语法规范（关系语义→箭头/线型/颜色、方向判定、分组/层级） | `references/DRAWING_GRAMMAR.md` | 规范 | 迁移到任何"关系图"类技能；给 LLM 当判定依据 | 构造一对"激活 vs 抑制"关系，判定结果必须不同 |
| **A5** | 连接规则字典（机器可读） | `assets/relation-dict.json` | 字典 | 直接加载：`kind → {arrow, line, dash, color}`；spec_lint / 渲染 / 图例三方共用 | 7 类规范 kind 全部能在字典里找到；缺一类则 `spec.relation_dict` 报 fail |
| **A6** | CP1–CP5 检查点清单（机器可读） | `assets/checklist.json` | 清单 | 当作"验收脚本的条目来源"；或用于生成人工复核表 | 文件里 CP1..CP5 五个 id 齐全（`selftest.py` 有断言） |
| **A7** | 契约校验器（G1–G8 硬门） | `scripts/validate_result.py` | 工具 | 任何"必须产出结构化 result.json"的技能都能改用它的门模型 | 对**缺产物**与**假成功**两种坏输入必须非 VALID（`selftest.py` 有断言） |
| **A8** | 检查名索引（含级别与科学含义） | `references/CHECK-INDEX.md` | 字典 | 把"检查名 → 含义"当术语表；新技能照此给自己定名 | 索引里的每个检查名都能在 `scripts/` 里找到；`doccheck.py` 自动对拍 |
| **A9** | 文档↔代码一致性对拍器（只读） | `scripts/doccheck.py` | 工具 | **与本题无关的纯工具**：任何有"文档承诺 + 代码产出"的项目都能用 | `--json` 输出结构稳定；对本包自身 exit 0；对故意加一个假检查名的副本 exit 1 |
| **A10** | 源文件自描述模式（内嵌清单 + `data-*` 属性） | `scripts/svgbuilder.py`、`scripts/edit.py` | 模式 | 任何"可编辑图稿"任务都可照此把语义写进产物本身 | `--edit-svg` 指向**无内嵌清单**的 SVG 必须被拒（exit 2） |
| **A11** | 字体探针（候选族 + 确定性结论） | `scripts/textfont.py` | 工具 | 任何要渲染 CJK 的技能都可复用（--list/--probe 两个入口） | 同机两次 `--probe` 结论一致；`--list` 逐候选打印命中情况 |
| **A12** | 导出预检清单（DPI/色彩/文字可编辑/PDF/字体） | `scripts/checks.py`、`references/OUTPUT_CONTRACT.md` §4 | 清单 | 当作"导出前必查项"的模板；阈值可按目标期刊改 | 把 `--dpi` 降到阈值下必须触发 `bitmap.dpi_print` 非 ok（**M4 的推翻实验**） |

## 2. 采纳阶梯（L0–L4）：按改造成本从低到高

| 级 | 名称 | 拿什么 | 改什么 | 验证 | 适合谁 |
|-|-|-|-|-|-|
| **L0** | 只读参考 | 规范类：A3 / A4 / A8 / A12 | 不改，只当文档读 | 无（阅读即可） | 想理解"关系图该怎么建模"的人 |
| **L1** | 直接复用工具 | A7（契约校验器）、A9（对拍器）、A11（字体探针） | 只改调用路径（命令里的 `$SKILL_DIR`） | 各工具自己的最小自测：A7 对坏输入非 VALID、A9 对自身 exit 0、A11 两次结论一致 | 已有自己的流水线，只缺校验/对拍/字体探测 |
| **L2** | 复用夹具与字典 | A1（题集）、A2（金标准）、A5（关系字典）、A6（检查点清单） | 换案例内容，保留字段结构与文件形态 | `run_examples.py --out <tmp>` 在**改造后**仍 exit 0；或新写一个等价的复现脚本 | 要给自己的技能做回归测试的人 |
| **L3** | 复用模式 | A10（源文件自描述） | 需要改渲染层：把语义写进产物、实现"读产物做增量编辑" | 两条不变式：无内嵌清单必须被拒；编辑后未改动元素保持一致 | 做"可编辑图稿/可编辑文档"类技能的人 |
| **L4** | 整套方法 | 全部 + `SKILL.md` 的机制/决策结构 | 换成自己领域的机制与判据（M1–M5 换成自己的 M'） | 每个新机制都要有"没有它会怎样"与"可证伪判据"，且判据要有实测读数 | 要从零做一道同类技能题的人 |

> **不建议的采纳方式**：把本包的机制名原样抄进别的领域（例如把
> "containment 必须分组"套到没有包含关系的任务上）。机制的价值在于
> "判据可被观测"，不在于名字。

## 3. 复用步骤（照着做）

### 3.1 只想用校验器（L1，约 5 分钟）
```bash
# 1) 复制工具（单文件、纯标准库）
cp "$SKILL_DIR/scripts/validate_result.py" <你的项目>/tools/
# 2) 用你自己的 result.json 与 case.json 跑一遍
python <你的项目>/tools/validate_result.py --case <你的 case.json> --result <你的 result.json>
# 3) 确认它对自己的坏输入也会拒绝（这一步不能省）
#    构造一个 artifacts 为空的结果 → 必须出现 G7 的 INVALID
```

### 3.2 想给自己的文档做一致性对拍（L1，约 10 分钟）
```bash
cp "$SKILL_DIR/scripts/doccheck.py" <你的项目>/tools/
python <你的项目>/tools/doccheck.py --root <你的项目根> --json
# 输出：check ids 文档/代码 对照、规则编号缺号、缺失的 --flag
```
`doccheck.py` 的设计前提只有两条：① 代码里用带点小写标识符报检查名；
② 文档是 markdown。不满足这两条时它会报环境错误（exit 2）而不是瞎猜。

### 3.3 想复用题集做回归（L2，约 30 分钟）
```bash
cp -r "$SKILL_DIR/examples" <你的项目>/tests/fixtures/sse/
# 改 fixtures 里的 case.json / 材料，保持字段结构
python <你的项目>/scripts/run_examples.py --out /tmp/your-regression
```
**验收**：三步（schematic / chart / edit）各 exit 0，且三份 `result.json`
过你自己版本的契约门。若你把契约也换了，**必须同时换判据**（别用旧门判新字段）。

### 3.4 想复用"源文件自描述"模式（L3，约半天）
两个必须一起做的事：
1. **写进去**：渲染时把语义清单嵌进产物（本包用 `<metadata id="er-manifest">` + `data-*`）；
2. **读出来**：编辑入口先尝试从产物里读清单，读不到就**明确拒绝**而不是猜。
```bash
# 拒绝路径必须真实存在（否则"自描述"只是个说法）
python <你的项目>/edit.py <无内嵌清单的产物>   # 期望：非零退出 + 明确说明
```

## 4. 复用时最容易踩的三个坑

| 坑 | 现象 | 正确做法 |
|-|-|-|
| 只抄文件不抄判据 | 工具能跑，但不知道"什么算通过" | 连同 `references/CHECK-INDEX.md` 的级别语义一起抄；明确 fail/warn 的分界 |
| 改判据后不更新文档 | 文档说 A，代码做 B | 复用时把 `doccheck.py` 一并引入，让它替你发现漂移 |
| 把"示例"当"正式答案" | 复用了示例夹具，却把它当比赛答案交出去 | 示例明确标注"示例，非正式案例"；正式案例由平台提供 |

## 5. 与其它变体的关系（供评审理解本包定位）

- 本包（v3）包含"机制显性化"与"复用显性化"两条轴；
  决策规则与失败分支的**权威描述**仍在 `references/failure-modes.md`
  与 `SKILL.md` §5/§6（本包不重复展开，只把每条分支指到受影响机制）；
- 因此复用时若要完整理解"出错时会怎样"，应同时读
  `references/failure-modes.md`（现象→处置）与 `references/STRENGTH-AXES.md §B`
  （机制→判据→盲区）——**前者回答"怎么办"，后者回答"凭什么相信它是有效的"**。

## 6. 资产的许可与来源（如实说明）

- 全部资产均为本作品原创（脚本、规范、字典、示例夹具），随包提供；
- 示例材料（`examples/sources/*`）是**合成内容**，不来自任何真实论文，
  也不含任何第三方数据；
- 包内不含字体文件、不含二进制资源；字体探测只**读取**系统字体目录的
  可用性，不分发字体；
- 复用本包资产时请保留 `references/CHECK-INDEX.md` 与
  `references/OUTPUT_CONTRACT.md`（它们是判据的一部分，不是可选文档）。
