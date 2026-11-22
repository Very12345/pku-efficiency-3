# COMPARE.md — 对照方法论：怎么才算"公平地证明了增益"

本文件回答方法论问题（**为什么这样对照才算数**）；**具体指标定义、复跑命令与实测数字**
在 [references/GAIN-PROTOCOL.md](references/GAIN-PROTOCOL.md)，原始记录在
[references/gain-run-record.json](references/gain-run-record.json)。

## 1. 三层证据，缺一层就只是"文字自述"

| 层 | 内容 | 本包落点 | 谁能验 |
|-|-|-|-|
| ① 机制层 | 加载前后"做法"的差异（计划先行 / 逐页证据 / 讲稿与问答 / 模板与渲染 / 失败处置） | `SKILL.md` §2、`references/plan-contract.md`、`references/quality-gates.md` | 读文档 + 看产物字段 |
| ② 口径层 | 指标的精确定义、公平性约束、缺项如何计分 | `references/GAIN-PROTOCOL.md` §3–§4 | 按定义复算 |
| ③ 实测层 | 同一输入上两个臂的实测数字（**含不利于本包的两项**） | `references/gain-run-record.json` + `GAIN-PROTOCOL.md` §6 | 复跑 `scripts/gain_ab.py` |

题面禁止"文字自述替代实际运行证据"，所以本包的做法是：**把①的说法都落到②的指标上，
再用③的真实数字回答**——不能落到指标上的说法一律删掉。

## 2. 两个臂的对照关系（同输入 / 同工具栈 / 同尺子）

| 环节 | A 臂（基础形态模拟器） | B 臂（加载本包） | 可判定字段 |
|-|-|-|-|
| 材料盘点 | 读 case 声明的材料文本 | 实读 + 解析 + 记 `parsed/char_count/sections` | `sources[]` |
| 页数来源 | 材料长度（每页 5 段） | 时长推导并校准到冻结页数 | `plan_gates.gates[P3]` |
| 逐页内容 | 整段照搬（长段） | 一页一主张 + 一句话讲稿 + 证据强度 | `pages[].claim/one_liner/strength` |
| 讲稿备注 | 无 | 每页【主张/证据/讲解/备答】 | `deck_audit.slides[].notes_nonempty` |
| 来源定位 | 无 | 每页 `locator` + 逐字 `quote` | `evidence_audit`、`evidence_map.json` |
| 问答准备 | 无 | 局限/风险 + strong 结果各一条追问 | `pages[].qa` |
| 图与表 | 只贴显式声明的图片文件 | 图引用绑定图片（无图则诚实占位框） | `pages[].figure_file`、`evidence_audit.figure_bound` |
| 渲染检查 | 无 | PIL 预览 + manifest 限制说明 | `artifacts.previews`、PNG 魔数 |
| 结果形态 | 一个 `.pptx` | `result.json`（契约 + 三道审计内嵌）+ 9 类产物 | `result.json` 顶层键 |
| 失败处置 | 无分支概念 | 降级仍产出 + 三处记录（status/uncertainty/change_records） | 同左 |
| 可复跑 | 依赖会话 | 同输入双跑内容投影 sha 相同 | `self_check.determinism` |

## 3. 度量必须满足的四条硬要求

1. **同一把尺子**：度量代码只读产物（`.pptx` / `result.json` / PNG 文件头），
   **不 import 被测包的任何模块**；两个臂逐项同法计算（`scripts/gain_ab.py` 满足）；
2. **缺项不跳过**：没有该字段就记 `0`/`null` 并标 `available=false`——"没产出"本身是被测差异；
3. **不利结果一并公布**：本包实测中 A 臂在"可见文本逐字可溯源率"（0.75 vs 0.3333）与
   "数字可对源率"（1.0 vs 0.8679）上更好，原因与解释写在 `GAIN-PROTOCOL.md` §7.1，
   **不隐藏、不换指标**；
4. **不越界宣称**：本对照是单案例、单机的机制与可测性证据，**不是平台白板**，
   **不是**"质量提升 X%"，**不是**平台分数。

## 4. 不能靠本包自证、必须由平台来做的部分

- 组织方 3 个固定案例上的 A/B 与白板对照（题面明文：白板由组织方提供/生成）；
- 真实基础 Agent 的行为（本包只能用**代理臂**忠实复现题面描述的常见表现）；
- 人把讲稿改到"能上台"所需的人工工时（本包只测机器可判定的结构指标与墙钟时间）。

⇒ 因此本包提交的是**可复跑的对照装置 + 指标定义 + 原始记录**，
让评审能在自己的条件下复用同一把尺子；而不是替平台下分数结论。

## 5. 本包已知的不利事实（汇总，供评审直接引用）

| # | 事实 | 出处 |
|-|-|-|
| 1 | B 臂墙钟时间更长（1.67 s vs A 臂 0.26 s）——多做计划/审计/预览的必然成本 | `GAIN-PROTOCOL.md` §6、§8 |
| 2 | D6 可见文本逐字可溯源率 A 更好（页面长句被截断所致） | §7.1 |
| 3 | D7 数字可对源率 A 更好（未命中项含页脚页码与换算值） | §7.1 |
| 4 | A 臂只贴显式声明的图片，B 臂会扫描材料目录 → D8 的差被放大 | §8 第 3 条 |
| 5 | 预览是 PIL 示意，不是 Office 栅格化，"导出渲染"只能证明可检查 | §7.3 |
