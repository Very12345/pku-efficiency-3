# RUBRIC_MAP.md — 评分五维逐条落点（故障注入与恢复演练版）

> 题面五维固定为 **实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 · 生态贡献 10**。
> 本文件把每一维拆成"评分点 → 本包给什么证据 → 证据在哪个文件的哪一段 → 怎么复核"，
> 并且**只写能复核的数字**。凡本包没测的，明确写"未测"，不拿形容词充数。
>
> 一条纪律：**同一个事实只在一处给数字**。`references/FAULT-MATRIX.md` 是实测数字的
> 唯一权威处；本文件只引用它的行号（F1-xx…F4-xx），不复制数字。

## 0. 五维落点总表

| 维度 | 分 | 评分点（题面） | 本包落点 | 复核方式 |
|-|-|-|-|-|
| 实际效果 | 40 | 任务完成度 15 · 结果正确性 15 · 结果完整性 5 · 结果可核验性 5 | `scripts/main.py` 出 7 件产物；`evidence/layout/verify_report/result` 四份 JSON 是可核验性载体 | 跑一次示例 → `exit 0`、`status=success`、`check.py ok:true`、`result.json` 18 个顶层键 |
| 使用增益 | 25 | 质量增益 15 · 效率增益 5 · 增益可验证性 5 | 闸门 `preflight.py`：把 9 条静默缺陷变成运行前 finding（**实测 0 漏网**）；`--merge` 免重画 | `fault_inject.py` 的 `preflight_caught` / `preflight_missed_silent_defects` 两个计数 |
| 创新增益 | 15 | 新增能力 5 · 方法改进 5 · 创新证据 5 | **把"故障行为"做成可复跑的注入矩阵**：32 条 × 6 个观测位点，脚本自带沙箱副本与依赖影子包 | `fault_inject.py --list` 看注入表；重跑得同一份 `summary` |
| 可靠体验 | 10 | 调用与易用性 3 · 运行稳定性 4 · 异常处理 3 | `FAULT-MATRIX.md`（四形态实测）+ `failure-modes.md`（现象→行号）+ 四脚本退出码语义表 | 读矩阵 §1–§4；每行都有退出码与门号 |
| 生态贡献 | 10 | 文档完整性 3 · 资源可复用性 4 · 分享推广价值 3 | 规则资产/配色/核对清单/闸门/注入语料全部可单独拿走；文档 6 份 references（契约/RUBRIC/故障矩阵/失败模式/术语/蓝图） | 见 §5 的"拿走即用"清单 |

## 1. 实际效果（40）

**任务完成度（15）**：一次 `main.py` 产出 7 件（`evidence.json`、`layout.json`、
`figure.svg`、`figure.png`、`figure.pdf`、`verify_report.json`、`result.json`），
覆盖题面要求的六类要素：

| 题面要素 | 产物 | 证据位点 |
|-|-|-|
| 科学实体 | `entities[]` + SVG `entity-<id>` 组 | `result.json.entities`、`data-entity` 属性 |
| 空间关系 | `layout.json`（x/y/w/h、正交连线路径） | `layout.json`；`figure.svg` 的 `arrow-<id>` |
| 数据编码 | kind → 形状/配色映射、阶段分列、步骤编号 | `output_contract.data_mapping` |
| 图例标注 | 图例层 kind 集合 == 图面 kind 集合（机器校验） | `verify.checks.legend_kinds` |
| 可编辑源文件 | 分层 SVG（5 层 `layer:*`、真实 `<text>`、`data-*`） | `output_contract.editable_sources[]` |
| 导出格式 | PNG（200 DPI）+ PDF（矢量、CID 字体） | `output_contract.exports[]` |

**结果正确性（15）**：正确性由三条机器门保证，不靠自述 —— 证据门（每条实体/关系带
`locator`+`quote`）、连接门（`connection_rules.json` 的 8 条规则逐条审计）、
契约门（G1–G10）。**这三道门在注入实验里的表现**正是 `FAULT-MATRIX` §1/§3/§4 的内容：
契约门 9/9 拦下、依赖域 3/3 诚实降级、输入域 5/5 干净失败。

**结果完整性（5）**：`status` 只有 `success|partial|failed` 三档且与退出码配合使用；
**实测存在 `status=success` + 退出码 3 的合法组合**（F3-03），本包在
`SKILL.md §4`、`README.md §2`、`failure-modes.md §0` 三处都点名了这条口径，
避免使用者把"status 好看"当成"门全过"。

**结果可核验性（5）**：`result.json` 的 `checksum` = `sha256(case_id + 实体 id 序列 +
关系 id 序列 + svg sha)`；`evidence.source_files[].sha256` 给出"用的是哪一版材料"；
布局确定性由 `verify.determinism.spec_sha16` 提供指纹。`TEST.md` T3 记录了同输入
两轮的 sha256 对拍结果。

## 2. 使用增益（25）

题面写明"**文字自述不能替代实际运行证据**"，所以这一维本包只给三类可复核的东西：

**① 质量增益（15）：把"静默失败"变成"运行前就响"**

| | 不加载本包的好做法 | 加载本包 | 怎么验证 |
|-|-|-|-|
| `--rules` 写错路径 | 照常出图，`verify.ok` 可能仍为 `true`（审计空转） | `preflight.py` 报 `rules-missing` **error**，退出码 3 | 矩阵 F2-04；`fault_inject.py` 的 `preflight` 列 |
| `--material` 指错 | 证据条数悄悄变少 | `preflight.py` 报 `material-missing` **warn** | 矩阵 F1-10 |
| 关系端点不存在 | 被丢弃且不留痕（缺口 A） | `preflight.py` 报 `relation-dangling` **warn** | 矩阵 F1-06 |
| 缺 Pillow | 以为只有 PNG 会坏；实际 PNG+PDF 一起坏 | `preflight.py --deps` 报 `dep-pillow-missing` | 矩阵 F3-01 |

**可复核的数字**：`fault_inject.py` 的输出里有两个计数直接对应这件事 ——
`summary.preflight_caught`（闸门提前拦住的注入条数）与
`summary.preflight_missed_silent_defects`（**闸门漏掉的静默缺陷条数，实测 0**）。
两个数都由脚本算，不接受手工填。

**② 效率增益（5）：本包**不**声称运行更快**

单轮耗时、产物字节这些在故障演练里只会变大（每条注入都要复制一次沙箱副本）。
本包能站得住的效率增益只有一条，而且是"少做事"而不是"跑得快"：

- **返工轮次**：没有闸门时，"`--rules` 写错但结果全绿"这种情况通常要等到**交付后**
  或第三方复核时才发现（那时图已经画完、可能已经提交）；有闸门时在**运行前**就停下，
  返工成本从"重画＋重交"降到"改一个路径"。这条增益**无法用秒数衡量**，
  本包只用"发现问题的时间点"来陈述，不用倍数。

**③ 增益可验证性（5）**：全部通过 `scripts/fault_inject.py` 现场复算 ——
不带任何参数跑一遍就得到 32 行观测 + 11 个计数，任何人可在自己机器上重跑并得到
同一张表（实测两次运行的 `summary` 完全一致，见 `TEST.md` T4）。

## 3. 创新增益（15）

**新增能力（5）**：`scripts/preflight.py` —— 一个**不跑算法**的运行前闸门。
它只读输入与资产，把四类风险变成 20 余种带 `code` 的 finding。
之所以算"新增能力"而不是"多写个脚本"：它输出的 `code`（如 `rules-missing`、
`relation-dangling`、`dep-pillow-missing`）与 `FAULT-MATRIX.md` 的行号一一对应，
**每一个 code 都能追到一条实测注入**。

**方法改进（5）**：`scripts/fault_inject.py` 用三条手法保证注入实验**可重复且不污染**：

1. 每条注入把技能根复制成沙箱副本再改（原包只读）；
2. 依赖缺失用 `PYTHONPATH` 影子包模拟（`__init__.py` 里 `raise ImportError`），
   而不是卸载真包 —— 只影响那一次子进程；
3. 所有子进程带 `PYTHONDONTWRITEBYTECODE=1`，包内不落 `.pyc`。

**创新证据（5）**：创新点不是"我做了故障注入"，而是**注入结果反过来改变了包的形态**：
32 条注入 → 发现 9 条静默缺陷 → 新增一道闸门 → 复跑验证 0 漏网 → 把 8 条无法消除的
缺口写进矩阵 §6。这条链在 `FAULT-MATRIX.md §7` 有一张 ASCII 流程图和三行实测计数。

## 4. 可靠体验（10）

**调用与易用性（3）**：四个脚本的退出码语义各不相同但**写在同一个表里**
（`README.md §3` 的"退出码速查"）。`preflight.py` 的 `--strict` 可把 warn 升级为阻断，
适配"我只想跑干净输入"的用法。

**运行稳定性（4）**：矩阵 §1（输入 11 条）与 §4（契约 10 条）合计 21 条，
**退出码与期望不符 0 条**。另有两类"看起来像故障但不是"的行被单独标注：
F2-03（空 palette 是合法写法）、F4-00（不注入的对照行）。

**异常处理（3）**：`failure-modes.md §1` 是一张"你看到什么 → 先看哪条"的速查表，
16 行现象全部指向矩阵行号；§6 的 9 条缺口逐条给"闸门能不能拦 + 人手怎么复核"。
两处都不写"应该会……"，只写"实测是……"。

## 5. 生态贡献（10）

**文档完整性（3）**：SKILL（主线 + 决策规则）、README（依赖/调用/限制/维护/退出码表）、
TEST（验收记录）、6 份 references（契约 / RUBRIC / 故障矩阵 / 失败模式 / 术语表 / 布局蓝图）。

**资源可复用性（4）** —— "拿走即用"清单（谁都能单独复制走）：

| 资产 | 复用到别的题要改什么 |
|-|-|
| `assets/connection_rules.json` | 换词表与规则体；**不用改代码** |
| `templates/palette.json` | 换配色即可 |
| `scripts/check.py`（G1–G10） | 换 G 门判定对象；退出码语义（0/1）可沿用 |
| `scripts/preflight.py` | 换四组 checks 的判据；**finding 结构（level/code/scope/detail/action）可直接沿用** |
| `scripts/fault_inject.py` | 换 `_specs()` 里的注入语料；沙箱/影子包/静默判据三段骨架不动 |
| `references/FAULT-MATRIX.md §5`（静默判据） | "退出码 0 + status 正常 + uncertainty 空 + verify 绿 + 门号空"这套判据任何包都适用 |
| `references/failure-modes.md §8`（R1–R6 打包门） | **一行都不用改**，任何走平台预检的包都适用 |

**分享推广价值（3）**：本版沉淀的不是"一个更好的绘图脚本"，而是一份**可复用的
可靠性检验方法**：四形态 × 6 观测位点 × 静默判据 × 闸门闭环。任何"输入→处理→交付"
形态的 Skill 都能照这个骨架自查，且成本只有几十秒（实测 32 条注入 0.13–0.71 s/条）。

## 6. 这一维落点没覆盖到的（诚实边界）

| 项 | 状态 | 原因 |
|-|-|-|
| 与"不加载 Skill 的裸 Agent"的质量对照 | **未测** | 本版聚焦故障行为；对照协议与实测在另一份包（增益可验证化版）里，本版不重复也不冒称 |
| 平台固定 3 个案例上的表现 | **未测** | 案例与白板由平台提供，参赛者不可见；本包所有数字都来自合成案例 |
| GNU/Linux / 容器环境的注入结果 | **未测** | 本轮在 Windows 11 + CPython 3.13.9 上跑；`WINDIR` 依赖注入在 Linux 下需换成字体目录改写（方法同构，但**未实测**） |
| 并发/重入、磁盘写满、超长材料 | **未测** | 未纳入本轮 32 条语料（矩阵 §8 已列出） |
| 分数预测 | **不做** | 本包不宣称任何具体分数 |
