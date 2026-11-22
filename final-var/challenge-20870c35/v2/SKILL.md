---
name: academic-talk-organizer
description: >
  把已有科研材料组织成可讲、可编辑、证据可追溯的学术汇报（学术 PPT 页面组织）。
  输入：论文/研究报告/组会材料 + 听众、时长、页数、模板约束、讲稿或备注需求；
  关键词：学术汇报、答辩PPT、组会汇报、slides、deck、页码规划、讲稿、备注、问答准备、
  听众适配、叙事顺序、证据定位、evidence mapping、模板适配、增益对照、A/B 对照、
  gain protocol、可核验记录、契约回显。本包以"证据链"运行：每一步都产出可被第三方
  复算的记录（计划门 P1–P8 / 逐字证据审计 / deck 机器校验 / 契约四形态回显 /
  确定性探针），并提供 scripts/gain_ab.py 在同一输入上对照"不加载 Skill 的基础形态"，
  指标定义与实测记录见 references/GAIN-PROTOCOL.md（含不利于本包的结果）。
---

# 学术汇报内容组织 · v2 增益可验证版（academic-talk-organizer）

面向「玻尔产品周赛 · 学术效率 · 第三期」challenge-20870c35（slides 组）。

本版的重点不是"多做什么"，而是**让"多做了什么"能被别人复算**：
每个动作都留下结构化证据，效率与质量都被翻译成同一把尺子上的指标，
并且把**不利于本包的对照结果**一起放进包里。

**边界**：只做"从已有内容材料到可讲页面"的组织与交付；不做论文精读成稿、学术写作成稿、
科研绘图素材生产。页面内容取自源材料逐字引文，不改写事实、不补造数据。

## 1. 交付物：一份结果 + 一条可复算的证据链

```bash
SKILL_DIR="<本包根目录>"        # 平台安装后即 /skills/weekly-skill
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md --out /app/output
```

一次运行产出（`result.json` 是唯一评分产物，其余是它的证据）：

| 产物 | 它证明什么 |
|-|-|
| `result.json` | 契约字段齐全 + 主结果 + 三道审计内嵌（`audit{plan_gates,evidence,deck,gates}`） |
| `talk_plan.json` | 页级取舍**在生成之前**就已固定（可编辑、可 diff） |
| `plan_gates.json` | 计划守约（P1–P8 逐条，`assets/plan.schema.json` 驱动） |
| `evidence_audit.json` | 每页论断**能落回源材料**（逐字引文 + 行号区间 + 数字对源） |
| `deck_audit.json` | 交付的 `.pptx` 真的可打开、页数守约、每页有备注与 `page-claim-NN` |
| `previews/` + `preview_manifest.json` | 渲染可检查，并如实说明"PIL 模拟"的边界与字体探测结果 |
| `self_check.json` | 结构 + 契约 + 门快照 + **确定性探针**（内容投影 sha） |

退出码：**0** = 已产出通过 `validate_result` + `check_contract` 的 `result.json`
（`status` 说明是 `completed` 还是 `partial`——诚实降级不算崩溃）；**1** = 没有可用的契约结果；
**2** = 参数用法错误。

## 2. 证据链的七个环节（E1–E7）：每环都留下可复算的东西

| 环节 | 动作 | 产出证据 | 第三方复算方式 |
|-|-|-|-|
| **E1 材料实读** | 按真实路径读取每个材料并逐文件解析（md/txt/PDF），缺失照实标记 | `sources[].{file,path,kind,parsed,char_count,sections[]}`、`environment.pypdf` | 打开 `sources[]` 对拍磁盘；`kind=missing` 必须真的不存在 |
| **E2 计划先行** | 听众 → 背景比例；时长 → 页预算并**校准到冻结页数**；每页一个主张 + 一句话讲稿 + 证据强度 | `talk_plan.json`（含 `audience`、`narrative.order_blocks`、`timing`）、`summary.pages_total` | 改 `report_type` 重跑，页序与比例随之变化（可 diff） |
| **E3 计划门** | schema 驱动的 P1–P8 机器校验（含冻结页数、证据定位存在性、强度词法） | `plan_gates.json`、`result.audit.plan_gates` | `validate_plan.py <out>/talk_plan.json --materials-dir <材料>` |
| **E4 生成可编辑 deck** | 模板适配（沿用母版/版式、丢弃自带示例页）或内置主题；图绑定或诚实占位；确定性元素命名 | `editable_deck.pptx`、`artifacts.deck_mode/template_used` | `verify_deck.py <out>/editable_deck.pptx --expect-pages <N> --plan <out>/talk_plan.json` |
| **E5 渲染可检查** | PIL 模拟预览（封面/逐页/网格）+ manifest 说明限制 | `previews/*.png`（12 张）、`preview_manifest.json` | 看 PNG 魔数与 manifest；**不得**把它当成 Office 栅格化 |
| **E6 逐字证据审计** | 每页 `quote` 与实际读取文本逐字比对；行号落在章节区间；数字不在源文本逐字出现 → 警告 | `evidence_audit.json`、`evidence_map.json`（反向映射） | `evidence_audit.py <out>/result.json`（可加 `--sources-dir` 复读） |
| **E7 契约与自检** | 契约四形态回显（`""/[]/{}/0`，禁 `null`）+ 结构校验 + 确定性探针 | `result.json.contract`、`self_check.json` | `check_contract.py`、`validate_result.py`、`selftest.py` |

> **链条的意义**：任一环节失败都不会"消失"——它在该环节的证据文件里留下条目，
> 并让 `status` 降级（见 §6）。评审可以只读证据文件就判断"这份结果能不能信"。

## 3. 使用增益怎么被证明（本版核心）

题面写明：*"平台固定运行 3 个案例，比较不加载 Skill 与加载参赛 Skill 时的实际结果"*，
并禁止用文字自述替代运行证据。因此本包把"增益"写成**可复跑的对照协议**：

- 协议与指标定义：`references/GAIN-PROTOCOL.md`（两个臂的定义、公平性约束、
  D/C/E 三组指标的精确口径、复跑命令）；
- 对照装置：`scripts/gain_ab.py` —— 一条命令跑完**A 臂（基础形态模拟器）**与
  **B 臂（本包 main.py）**，用**同一把尺子**度量并写出 `gain_report.json`；
  它**不 import 本包任何模块**，只读产物，避免"用被测者自己的尺子量被测者"；
- 原始实测记录：`references/gain-run-record.json`（未手工编辑，可核对到每个字段）。

```bash
# 两个臂 + 度量（RUN 必须是包外临时目录）
python "$SKILL_DIR/scripts/gain_ab.py" --case "$SKILL_DIR/examples/case.json" \
       --work "$RUN/gain" --skill-dir "$SKILL_DIR"
```

## 4. 实测摘要（2026-11-22 本机真实运行；完整表见 GAIN-PROTOCOL.md §6）

同输入（包内合成示例案例：20 分钟 / 冻结 12 页 / 组会），A 臂 vs B 臂：

| 指标 | A 臂 | B 臂 | 方向 |
|-|-|-|-|
| 讲稿覆盖率 | 0.0 | **1.0** | B 优 |
| 来源定位覆盖率（内容页） | 无该字段 | **1.0（10/10）** | B 优 |
| 问答条目 / 证据行 | 0 / 0 | **4 / 11** | B 优 |
| `result.json` 顶层键 | 无文件 | **20** | B 优 |
| 有效 PNG 预览 | 0 | **12** | B 优 |
| 达到冻结页数的运行轮数 | **2**（首轮 3 页） | **1**（首轮 12 页） | B 优 |
| 单臂墙钟秒 | **0.26** | 1.67 | A 优（B 更慢） |
| 可见文本逐字可溯源率 | **0.75** | 0.3333 | **A 优（不利于 B）** |
| 数字可对源率 | **1.0** | 0.8679 | **A 优（不利于 B）** |

**为什么后两项 A 更好、以及它说明了什么**：A 臂整段照搬材料，可见文本自然与源文本重合；
B 臂页面上是压缩后的主张与短行（长句渲染时被截断），所以"可见文本逐字命中"这项天然吃亏；
B 臂的可溯源性是**结构化**的（每页有定位与引文，且由 `evidence_audit` 独立校验）。
B 臂未命中的数字样本是页脚页码（`01…12`）与时长换算值（`20.0/100.0`），不是科学数据。

⇒ **本包不声称"质量提升 X%"**：对照是单案例、单机的机制与可测性证据，不是平台白板结果。

## 5. 降级时证据链如何保持完整

| 情形 | 仍然产出 | 证据链上的记录 |
|-|-|-|
| 缺 `python-pptx` | 页计划、计划门、预览、`result.json`、`self_check.json`；**命令仍返回 0** | `artifacts.editable_deck=null` + `deck_limitation` + `uncertainty` 一条 + `change_records` 记明 |
| 缺 `Pillow` | 除预览与 deck 外全部 | `preview_note` + `status=partial` |
| 缺 `pypdf`/`PyPDF2` | 其余材料照常 | `sources[].parsed=false` + `note` |
| 材料缺失 / 材料为空 | 结构性页面 + 诚实标注 | `sources[].kind=missing/none` + `uncertainty` |
| 无模板 / 模板打不开 | 内置主题 deck | `artifacts.deck_mode.mode` + `template_used` |
| 模板自带示例页 | 沿用母版/版式、丢弃自带页 | `template_slides_present/dropped`；最终页数 == 冻结页数 |
| 计划门/证据审计/deck 校验未过 | 照常落盘全部产物 | 对应审计文件 + `status=partial`；**不宣称"校验通过"** |
| `case.json` 不可读 | 最小失败信封 | `status=failed` + `error`；退出码 1 |

**统一纪律**：降级必须**同时**满足三条 —— ① `status` 跟着降；② `uncertainty` 有
`{item, impact, mitigation}`；③ `change_records` 有 `{at, step, action}`。
三者缺一即为"静默降级"，本包视为缺陷。

## 6. 收尾核对清单（每条都能机器验证）

- [ ] `result.json` 存在；`case_id` 与输入一致；`status ∈ {completed, partial, failed}`
- [ ] 契约字段齐全且**无 `null`**（`self_check.contract_check.missing_required == []`）
- [ ] 计划门 P1–P8 全过（或 `uncertainty` 里有对应条目）
- [ ] 每页（除封面/目录/问答备用页）有 `locator` + 逐字 `quote`
- [ ] `evidence.source_file` 全部能在 `sources[]` 找到（无孤儿引用）
- [ ] `editable_deck.pptx` 可打开、页数 == 冻结页数、每页有备注（`verify_deck.py` 退出码 0）
- [ ] 预览 PNG 有效且带水印；manifest 说明限制与字体探测结果
- [ ] 双跑确定性：内容投影 sha 相同（记录性时间戳已由探针剔除）
- [ ] 若跑过对照：`gain_ab.py` 的 `gain_report.json` 与 `GAIN-PROTOCOL.md` §6 数字一致
- [ ] 包内只有 `.md/.py/.json/.txt/.csv/.yaml/.yml`；≤50 文件；单文件 ≤500KB；合计 ≤2MB；
      无符号链接、无 `__pycache__`、无本机绝对路径

## 7. 输入与依赖（事实层）

**输入**：`/input/case.json`（`case_id`/`title`/`report_goal`/`audience`/`duration_min`/`slide_count`/
`report_type`/`materials`/`template`·`start_deck`/`figure_files`/`output_contract`）+ `/input/task.md`
+ 材料目录。**必须实际读取文件内容**，不按标签预设。

**依赖**：Python ≥ 3.8（本机 3.13.9）；必需 `python-pptx` + `Pillow`；
可选 `pypdf`/`PyPDF2`（PDF 文本）；无网络、无 cwd 依赖；不调用 LibreOffice/PowerPoint。
字体：运行时按候选路径探测系统字体（`/usr/share/fonts`、`/System/Library/Fonts`、`C:/Windows/Fonts`），
探测结果（仅文件名）写入 `environment.cjk_font` 与 `preview_manifest.json`；找不到则用内置位图字体并记明。

## 8. 资源形态与平台约束

题面运行契约原文：*at most 50 UTF-8 text files, 500KB each and 2MB total, no symlinks* /
*runtime artifacts may be binary and are retained independently of final JSON validity*。

| 常见二进制 | 本包做法 |
|-|-|
| 模板 `.pptx` | 不随包：`deck_builder` 现场构建 16:9 母版；案例模板直接读取 |
| 示例图/PDF | 不随包：`scripts/make_synthetic_inputs.py` 运行时生成（纯几何示意图 + 手工最小 PDF） |
| 示例输出 `.pptx/.png` | 不随包：`examples/EXPECTED-OUTPUT.md` 用文字列清单与实测数量 |
| 字体 | 不随包：运行时探测（见 §7） |
| `__pycache__`/`.pyc` | 不随包：提交前删除（`selftest.py --package-check` 的 G10 拦截） |

平台在 `/skills/weekly-skill` 安装本包，固定 3 案例 × 3 复跑；中间产物放 `/app/work`、
最终产物放 `/app/output`；执行预算 64 请求 / 900 秒 / 每响应 16384 token ——
**尽早落盘**：预算耗尽时已落盘的部分仍可复核（这正是收口先于"再优化一轮"的原因）。

## 9. 文件地图

| 文件 | 作用 |
|-|-|
| `scripts/main.py` | 唯一入口（CP1–CP5 编排） |
| **`scripts/gain_ab.py`** | **本版新增**：A/B 对照装置（基线模拟器 + 度量器，不 import 本包模块） |
| `scripts/scaffold_plan.py` / `validate_plan.py` | 页级规划 / 计划门 P1–P8 |
| `scripts/deck_builder.py` / `verify_deck.py` | 生成可编辑 deck / deck 机器校验 |
| `scripts/evidence.py` / `evidence_audit.py` / `render.py` | 材料与主张抽取 / 逐字审计 / 预览渲染 |
| `scripts/validate_result.py` / `check_contract.py` / `finalize_result.py` / `selftest.py` | 结构 / 契约 / 收口 / 全链路自检 |
| `scripts/make_synthetic_inputs.py` / `common.py` | 运行时生成示例输入 / 共享工具与路径净化 |
| **`references/GAIN-PROTOCOL.md`** | **本版新增**：对照协议、指标定义、实测记录、不利结果、待改进项 |
| **`references/gain-run-record.json`** | **本版新增**：`gain_ab.py` 的原始输出（未手工编辑） |
| `references/OUTPUT_CONTRACT.md` | 字段契约（含 §7 指标 ↔ 字段对照） |
| `references/RUBRIC_MAP.md` | 五维评分 → 文件与机制逐条对照 |
| `references/failure-modes.md` / `plan-contract.md` / `quality-gates.md` / `deck-rules.md` / `evidence-audit.md` | 失败模式 / 计划条款 / G1–G10 / 版式命名 / 审计规范 |
| `templates/` · `assets/` · `examples/` | 叙事规则与模板 / 计划模式与结果信封 / 合成示例 |
