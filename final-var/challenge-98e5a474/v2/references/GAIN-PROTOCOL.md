# GAIN-PROTOCOL — 与"不加载 Skill 的基础 Agent"的公平对照协议

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
