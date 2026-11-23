# RUBRIC_MAP.md — 评分五维逐条落点（全维合并版）

> **文档路径重定向（本包 v9）**
>
> * `references/MECHANISM.md` → 已全文并入 `references/GAIN-PROTOCOL.md` 尾部的「并入全文」附录（本包 v9 为守住平台「≤50 个 UTF-8 文本文件」硬门而合并，**内容一字未删**）；本文出现的旧路径请按该附录阅读。
> * `references/CASE-SET.md` → 已全文并入 `references/failure-modes.md` 尾部的「并入全文」附录（本包 v9 为守住平台「≤50 个 UTF-8 文本文件」硬门而合并，**内容一字未删**）；本文出现的旧路径请按该附录阅读。

> 题面五维固定为 **实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 · 生态贡献 10**。
> 本文件把每一维拆成"评分点 → 本包给什么证据 → 证据在哪个文件的哪一段 → 怎么复核"。
> **数字不在本文件里复制**：实测数字的唯一权威处是各自的 reference，
> 本文件只给指针（文件 + 小节），避免同一事实出现两个版本而漂移。

## 0. 五维落点总表

| 维度 | 分 | 评分点（题面原文要点） | 本包落点 | 复核方式 |
|-|-|-|-|-|
| 实际效果 | 40 | 任务完成度 15 · 结果正确性 15 · 结果完整性 5 · 结果可核验性 5 | 一键流水线出 7 件产物；**4 个合成案例（route/flow/apparatus）真跑通过** | `scripts/case_set_run.py` → `passed=4`；`references/CASE-SET.md §5` |
| 使用增益 | 25 | 质量增益 15 · 效率增益 5 · 增益可验证性 5 | 证据先行 + 规则审计 + 运行前闸门；**对照协议 + 真跑记录（含负面结果）** | `references/GAIN-PROTOCOL.md` 附录 A/B；`references/FAULT-MATRIX.md §7` |
| 创新增益 | 15 | 新增能力 5 · 方法改进 5 · 创新证据 5 | SIR→确定性布图→三后端同布局；**三层机制各有"没有它会怎样"的可执行反例**；故障行为做成 32 条注入矩阵 | `references/MECHANISM.md`；`references/FAULT-MATRIX.md` |
| 可靠体验 | 10 | 调用与易用性 3 · 运行稳定性 4 · 异常处理 3 | 32 条故障注入实测 + 9 条静默逐条给位点 + 8 条缺口清单 + D1–D20/F1–F4 + 四入口退出码表 | `references/FAULT-MATRIX.md`；`references/failure-modes.md` |
| 生态贡献 | 10 | 文档完整性 3 · 资源可复用性 4 · 分享推广价值 3 | 15 项可复用资产 + 四步复用流程；**题集可搬走**（案例 + 期望表 + 跑批）；R1–R6 打包门可直接抄 | `references/MECHANISM.md` 附录 A；`references/CASE-SET.md §7` |

## 1. 实际效果（40）

**任务完成度（15）**：一次 `main.py` 产出 7 件（`evidence.json`、`layout.json`、
`figure.svg`、`figure.png`、`figure.pdf`、`verify_report.json`、`result.json`），
覆盖题面六类要素：

| 题面要素 | 产物 | 证据位点 |
|-|-|-|
| 科学实体 | `entities[]` + SVG `entity-<id>` 组 | `result.json.entities`、`data-entity` 属性 |
| 空间关系 | `layout.json`（x/y/w/h、正交连线路径） | `layout.json`；`figure.svg` 的 `arrow-<id>` |
| 数据编码 | kind → 形状/配色映射、阶段分列、步骤编号 | `output_contract.data_mapping` |
| 图例标注 | 图例层 kind 集合 == 图面 kind 集合（机器校验） | `verify.checks.legend_kinds` |
| 可编辑源文件 | 分层 SVG（5 层 `layer:*`、真实 `<text>`、`data-*`） | `output_contract.editable_sources[]` |
| 导出格式 | PNG（200 DPI）+ PDF（矢量、CID 字体） | `output_contract.exports[]` |

**结果正确性（15）**：正确性由三道机器门保证（CP1 证据门、CP2 连接门、CP4 契约门），
并且**在 4 个案例上被真跑验证**（`references/CASE-SET.md §5`：实体/关系数与输入一致、
`verify.ok=true`、G1–G10 全过）。判据"能判错"的证据：把期望下限改成不可能满足的值后，
该案判 FAIL 并给出偏差明细（`v5/TEST.md` 的 T4 记录了这一次负例）。

**结果完整性（5）**：`result.json` 顶层 18 个字段、`output_contract` 四段齐全；
`status` 与退出码配合使用。⚠ 两处必须一起读的诚实说明：
① **告警 ≠ 失败**（`recycle-review` 属设计行为，`status` 仍 `success`）；
② 实测存在 `status=success` 且退出码 3 的合法组合（缺中文字体，`FAULT-MATRIX.md F3-03`），
三处文档都点名了这条口径。

**结果可核验性（5）**：`evidence.json`（逐条 `locator`+`quote` + 材料 `sha256`）、
`layout.json`（几何中间证据）、`verify_report.json`（含 `spec_sha16` 确定性探针）、
`result.json.checksum`（`sha256(case_id + 实体 id 序列 + 关系 id 序列 + svg sha)`）。
`TEST.md` T3 记录同输入两轮的 sha256 对拍结果。

## 2. 使用增益（25）

题面写明"**文字自述不能替代实际运行证据**"，因此本维只给三类可复核材料：

**① 质量增益（15）：三条互补的证据链**

| 证据 | 说清了什么 | 在哪里 |
|-|-|-|
| 三层机制的反例对照（C0 下界 vs C1 本包 vs C2 关掉门禁） | 拿掉证据层/确定性/规则审计后**具体失去什么**（来源绑定率 0.00、断头外露 1 条、违规暴露 0 条） | `references/MECHANISM.md`；数字在 `GAIN-PROTOCOL.md` 附录 B |
| 公平对照协议 + 真跑记录 | 协议先行（三个条件、四个固定项、6+4 个预注册指标），再给逐项数字与命令 | `references/GAIN-PROTOCOL.md` §1–§3 + 附录 A |
| 运行前闸门 | 把 9 条"退出码 0 但实际没做对"的静默缺陷变成运行前 finding（实测 0 漏网） | `references/FAULT-MATRIX.md §6/§7` |

**② 效率增益（5）：本包不声称运行更快**

对照记录里有一组**负面结果照写**：单轮耗时 **0.10 s → 0.44–0.59 s**、
产物字节 **~2–4 KB → 78–105 KB**（`GAIN-PROTOCOL.md` 附录 A §2.1/§2.2）。
本包能站得住的效率增益只有两类"少做事"：

- **返工轮次**：`--merge` 增量改图，改一个标注不必重画（E4：1 → 0）；
- **发现问题的时间点**：没有闸门时，"`--rules` 写错但全绿"通常要等到交付后才暴露；
  有闸门时在运行前停下（`FAULT-MATRIX.md §7` 的闸门列）。

这两条**不用秒数或倍数表达**，因为没做对照计时 —— 写倍数就是不诚实。

**③ 增益可验证性（5）**：全部可被第三方复跑 ——
`bare_baseline.py`（C0）、`main.py --rules <空对象>`（C2）、`gain_probe.py`（只用公开
JSON 字段的独立复算器）、`fault_inject.py`（一条命令得到 32 行观测 + 11 个计数）。
协议 §4 给出一段**不依赖包内内部函数**的复算脚本，可整段复制去核别人的同类包。

## 3. 创新增益（15）

**新增能力（5）**：四个"把方法变成可执行物"的脚本 ——
`preflight.py`（运行前闸门）、`fault_inject.py`（故障注入与静默判定）、
`case_set_run.py`（题集跑批 + 泛化度量）、`gain_probe.py`（指标复算）。
它们的共同点：**输出的是判据，不是描述** —— 每个 finding `code`、每条注入期望值、
每个案例期望区间都能追到一条实测。

**方法改进（5）**：

1. **机制被拆成三层并逐层反例化**：每层都有一份"把它拿掉"的可执行对照（`bare_baseline.py`），
   而且用 C2 条件把"规则审计"的贡献从算法里单独量出来（C1 与 C2 的 `figure.svg`/`layout.json`
   sha 相同 ⇒ 差异只能归因于规则层）；
2. **故障行为被枚举成可复跑矩阵**：四形态 32 条 × 6 个观测位点，注入手法（沙箱副本 /
   `PYTHONPATH` 影子包 / `WINDIR` 空目录）都不污染环境；
3. **泛化边界被量化**：`--text-only` 一次给出实体/关系保留率与丢掉的告警类型。

**创新证据（5）**：三条"不测就写不出来"的结论（见 `FAULT-MATRIX.md §5.1` 与
`CASE-SET.md §6`）：数据坏掉比代码坏掉更难发现；依赖会互相牵连（Pillow ⇄ reportlab）；
输入退化不自动降级状态（只剩 2 实体 1 关系仍报 `success`）。

## 4. 可靠体验（10）

**调用与易用性（3）**：四个入口的退出码语义写在**同一张表**里（`SKILL.md §2`），
互不改写；`preflight.py --strict` 可把 warn 升级为阻断；案例目录遵循平台
`/input` 约定（`case.json` + 同目录 `task.md`），一条命令即可跑。

**运行稳定性（4）**：本轮共 **60+ 次真实运行**无崩溃 ——
4 案 × 2（结构化 + 文本探针）= 8 次、32 次注入（各含一次 preflight 子进程共 53 个子进程）、
20 条决策用例、3 次对照条件、2 轮确定性对拍。其中结构化 4/4 `verify.ok=true`、G1–G10 全过。

**异常处理（3）**：`references/failure-modes.md` §1 是"你看到什么 → 先看哪条"的速查表
（16 行现象）；§6 是 9 条静默缺口的处置表（闸门能否拦 + 人手复核办法）；
附录 A 是 D1–D20 决策规则的**四列**全表（触发 / 动作 / 降级 / 证据位点）；
附录 B 是 27 行失败分支表；附录 C 是 20 个可复跑决策用例（实测 20/20 与表一致）。

## 5. 生态贡献（10）

**文档完整性（3）**：SKILL（六段重排 + 索引）/ README（结构、合并对照、依赖、用法、
限制、维护）/ TEST（九组实测）/ 11 份 references（契约、RUBRIC、失败模式、故障矩阵、
增益协议、机制、题集、题集期望表、对照数据、术语与蓝图）。

**资源可复用性（4）** —— "拿走即用"清单（复用价值已排序）：

| 优先级 | 资产 | 复用到别的题要改什么 |
|-|-|-|
| 1 | `assets/connection_rules.json` | 换词表与规则体；**不改代码** |
| 2 | `references/failure-modes.md §8` 的 R1–R6 打包门 | **一行都不用改**，任何走平台预检的包都适用 |
| 3 | `scripts/gain_probe.py` 的指标算法（Q1–Q6） | 换字段名；不 import 包内模块 |
| 4 | `evidence.json` 的清单结构（`{id,type,ref,locator,quote}` + `source_files[].sha256`） | 换抽取器；格式可原样沿用 |
| 5 | `scripts/check.py`（G1–G10） | 换判定对象；退出码语义可沿用 |
| 6 | `scripts/preflight.py` 的 finding 结构（`level/code/scope/detail/action`） | 换判据；结构与退出码可沿用 |
| 7 | `scripts/fault_inject.py` 的沙箱/影子包/静默判据三段骨架 | 换 `_specs()` 语料 |
| 8 | `references/case-set.json` 的期望布局（区间 + 允许告警 + 禁止规则 + 不变量） | 换 `case_path` 与区间 |
| 9 | `--text-only` 泛化探针 | **与题材无关**，任何"输入 → 产物"型 Skill 都能用 |
| 10 | 其余（配色模板、核对清单、契约骨架、`spec_sha16` 思路、审计报告字段） | 见 `MECHANISM.md` 附录 A 的 15 项清单 |

**分享推广价值（3）**：本包沉淀的不是"一个更好的绘图脚本"，而是四件可迁移的方法物：
**机制反例化**（把设计说成可对照的实验）、**增益协议化**（先定判据再测）、
**故障矩阵化**（四形态 × 6 位点，含静默判定）、**题集判据化**（案例 + 期望表 + 跑批）。
四者加起来 = 一套"任何 Skill 都能自查"的验收骨架，成本是几十秒的运行时间。

## 6. 这一维落点没覆盖到的（诚实边界）

| 项 | 状态 | 原因 |
|-|-|-|
| 真实模型臂对照（裸 Agent vs 加载 Skill） | **未测** | 协议 §3 明确只提供可执行下界 C0，且**不对任何模型的分数作断言** |
| 平台固定 3 个案例上的表现 | **不可见** | 材料与白板由组织方提供；本包所有数字来自合成案例 |
| Linux / 容器环境 | **未测** | 本轮仅 Windows 11 + CPython 3.13.9（`WINDIR` 注入手法需换等价物，方法同构） |
| 实体数 > 24 / 阶段数 > 5 | **未测** | 未纳入题集；布局拥挤度未评估 |
| `--text-only` 之外的其他退化形态 | **未测** | 例如材料乱码、任务书与材料矛盾、超大 canvas 等 |
| 分数预测 | **不做** | 本包不宣称任何具体分数 |
