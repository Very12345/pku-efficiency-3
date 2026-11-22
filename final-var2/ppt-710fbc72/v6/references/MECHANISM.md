# MECHANISM — 本包的独特机制，以及"没有它会怎样"

## 0. 一句话定位

本包不是"论文转 PPT 的脚本集合"，而是**六个互相咬合的机制**组成的适配器：每个
机制负责堵住一个具体的退化通路，并且每个机制都有一个**能被第三方复跑推翻的
判据**。本文件逐条写清：机制是什么、落在哪个文件/字段、**没有它会出现什么（用
实测数字）**、以及怎么证伪它。

阅读方式：M1–M6 各占一节，每节四段固定结构（机制 / 落点 / 没有它会怎样 /
可证伪判据）。§7 讲六个机制一起失效时的连锁后果，§8 讲本包**不做**什么。

---

## 1. M1 方案先行（plan-before-build）

**机制**：把"模板结构审计 + 页→版式分配 + 批量规则 + 图表放置计划"在**动手建页
之前**固化成一份机器可读的 `adopt_plan.json`；阶段二只负责执行它。

**落点**：`scripts/adopt_plan.py`（产出方案）+ `adapt_pptx.py`（消费方案）；
运行时字段 `result.json.adopt_plan`（`source/pages_assigned/layout_gaps/
batch_deviations/figure_plan/gates`）与 `result.json.template_audit.layout_used`。
方案的独立文件是 `<out>/adopt_plan.json`。复用方式见
`references/REUSABLE-ASSETS.md` §3。

**没有它会怎样**：常规做法是"读一页、填一页"——版式合不合适只有在生成完之后才
看得见，出错就整册返工，而且**没有任何中间判据可以核对**。本包实测：方案阶段
枚举出模板的 **1 个母版 / 11 个版式 / 各版式占位符清单**，给 10 页各分配版式，
阶段二**逐页套用 10/10、偏差 0**。作为对照，不加载 Skill 的基础做法在同一案例上
产出 3 页，且没有任何版式分配记录（对照数据见 `GAIN-PROTOCOL.md` §6 表 1）。

**可证伪判据**：删掉 `adopt_plan.py` 的调用后重跑 `main.py`——`result.json` 里
`template_audit.adopt_plan_applied` 应变为缺失或 0，`adopt_plan.consistency` 检查
应 fail。若删掉后这些字段仍显示 10/10，说明"方案先行"是装饰而非真机制。

## 2. M2 契约先行（contract-before-render）+ CP3 硬门 G1–G8

**机制**：交付物的形状（`result.json` 的字段与门）**先于**渲染被固定下来；渲染
结束后由**一个不信任自述的独立校验器**从磁盘重扫并逐门判定。

**落点**：契约定义 `references/OUTPUT_CONTRACT.md`（顶层字段表 / `main_result` /
`template_audit` / `adopt_plan` / `verification` / **CP3 G1–G8**）；检查器
`scripts/check_contract.py`（独立重开 pptx、独立扫产物清单）；`scripts/
validate_result.py`（字段级校验）；运行时字段
`result.json.verification.contract_gates`。复用方式见
`references/REUSABLE-ASSETS.md` §5。

**没有它会怎样**：常规做法是"先做出文件，再补一份说明" —— 说明与产物之间没有
强制约束，于是常见两种退化：产物缺件（预览没生成、图没嵌进去）而说明里写"已完成"；
或契约要求的字段缺失、用 `null` 占位。本包把这两条都做成**硬门**：G7 逐文件扫
产物存在性（实测 `artifacts=8 missing=[]`）、G3 检查契约键回显且
`null_placeholders=[]`（实测**顶层 null 个数 = 0**），G4 真的把 pptx 重开一遍
（实测 `reopened; 10 slides`）。本次 8/8 门全过、`exit 0`。

**可证伪判据**：手工删掉 `<out>/` 里的一个产物（例如某张预览 PNG）再跑
`check_contract.py`——G7 应立刻 fail 并列出缺失文件名。若删了文件仍报
`valid: true`，说明 G7 没有真的从磁盘扫描。

## 3. M3 证据定位绑定（claim → `文件:行`）

**机制**：页面上每一条主张都携带"它从材料哪一行来"的定位串；没有定位的数值
**不允许上页面**。

**落点**：`scripts/extract.py`（逐行编号抽取，材料另记 sha256）；
`scripts/audit.py`（`traceability.evidence_loc` 检查）；运行时字段
`result.json.slide_evidence[].evidence[].loc`、
`result.json.verification.traceability.evidence_loc_frac`；页型
`evidence_map` 把映射汇总成附录页。复用方式见
`references/REUSABLE-ASSETS.md` §4。

**没有它会怎样**：常规做法是把材料段落整体搬进 PPT —— 文字"看起来对"，但**无法
核对某一个数字是不是原文里的那个数**，也无法发现"图注写的数值与正文不一致"。
本包实测：**13/13 条证据行带定位（覆盖率 1.0）**，10 页 `slide_evidence` 各带
claim 与 locator；对照组（不加载 Skill）在同一案例上**定位串总数 = 0**。
两者的差别不是"更努力"，而是**结构上允不允许无来源内容上页**（决策规则 D4 直接
把"找不到定位的条目"挡在页面之外）。

**可证伪判据**：取任一页的 `slide_evidence[i].evidence[j].loc`（形如
`material.md:15`），到材料文件里翻到该行——应能在该行找到对应内容。抽样 3 条
对不上，即机制失效。

## 4. M4 方案↔执行一致性审计（planned vs applied）

**机制**：阶段一"计划了什么"与阶段二"实际做了什么"**逐页对照**，不一致必须逐条
留痕，不允许静默替换。

**落点**：`scripts/adapt_pptx.py` 写 `template_audit.adopt_plan_deviations` 与
`layout_fallback_used`；`scripts/audit.py` 的 `adopt_plan.consistency` 检查；
运行时字段 `template_audit.adopt_plan_applied` 与 `result.json.adopt_plan.gates`。
复用方式见 `references/REUSABLE-ASSETS.md` §5。

**没有它会怎样**：常规做法里"方案"和"产物"是两份互不校验的东西 —— 方案写得漂亮，
实际用了别的版式也没人知道。本包把这条变成**可计算的比率**：实测
`adopt_plan_applied = 10`（与计划页数相等）、`adopt_plan_deviations = 0`，
并且 `adopt_plan.consistency` 在 21 条审计检查里以 `ok` 出现。**关键在于"0 偏差"
是被测出来的，而不是被声明的**——偏差条数 > 0 时状态会被判定为 partial（§2.5 的
状态表），所以声称"0 偏差"有状态判定在背后兜着。

**可证伪判据**：故意把 `adopt_plan.json` 里某一页的 `recommended_layout_idx`
改成一个不存在占位符的版式，再跑阶段二——`adopt_plan_deviations` 应出现至少一条
记录，且 `adopt_plan.consistency` 应变为 warn/fail。若什么都没变，说明对照没生效。

## 5. M5 二进制资源运行时生成

**机制**：包里**只放 UTF-8 文本**；模板、示例图、预览等二进制全部在运行时现场
生成，生成物与正式案例的产物形态一致。

**落点**：`scripts/make_template.py`（`ensure_builtin()` 生成 16:9 回退模板，
真实母版/版式/占位符）、`scripts/make_synthetic_inputs.py`（纯几何占位图，带
SCHEMATIC 水印）；产物由 `scripts/main.py` 写入 `--out`。复用方式见
`references/REUSABLE-ASSETS.md` §6。

**没有它会怎样**：把 `.pptx` / `.png` 直接放进包里会踩题面硬约束
（*at most 50 UTF-8 text files, 500KB each and 2MB total, no symlinks*）——
实测同批提交里出现过因"资源类型不支持"与"文件数超限"被平台**整包拒收**的案例。
本包的处置是**根本不放二进制**：实测包内 `.pptx/.png` 数量为 **0**，但运行后仍能
产出 `_runtime/builtin.pptx`（27,522 B，**运行时生成**，来源记
`opened_from=builtin`）与两个有效预览（1280×720 / 2000×1580）。对照参考：
`GAIN-PROTOCOL.md` §6 表 1 里 A 臂 0 个预览、B 臂 2 个有效预览。

**可证伪判据**：`find <包目录> \( -name '*.pptx' -o -name '*.png' -o -name
'*.pyc' \)` 应 **0 命中**；同时运行 `main.py` 后 `<out>/` 里应出现
`_runtime/builtin.pptx` 与两个 PNG。前者证明包是纯文本，后者证明能力没有因为
"不放二进制"而丢失。两条必须同时成立。

## 6. M6 确定性字节（同输入可重跑）

**机制**：几何与方案是**纯函数**；写出的 pptx 通过 `deterministic_zip()` 固定
zip 条目时间戳并折叠同名条目，使同一输入产出同一字节。

**落点**：`scripts/pptx_toolkit.py` 的 `deterministic_zip()`；`scripts/
deckplan.py` 与 `adopt_plan.py` 的无时间戳纯函数设计；验证方式见 `TEST.md` §2。
复用方式见 `references/REUSABLE-ASSETS.md` §2/§3。

**没有它会怎样**：pptx 本质是 zip，zip 默认带创建时间，于是"同输入两次运行得到
不同 sha256"——**这让"这份产物是不是跑出来的"变得无法核对**，也让任何基于哈希的
回归测试失效。本包实测：同输出目录连跑两次，**11/12 个产物逐字节相同，deck
sha256 两次均为 `c41cb2ce6db055ce`**。唯一差异是 `result.json` 的
`generated_at` 与 `uncertainty[0].note`（首次写 `generated-at-runtime`、第二次写
`reused-generated`）——**这是运行事实的如实记录，不是随机性**；把它抹平反而会让
"模板是否现场生成"不可查，所以本包选择保留并在 `TEST.md` §2 写明。

**可证伪判据**：同输出目录连跑两次，对 `<case>_deck.pptx` 与两张 PNG 分别算
sha256——三者的哈希应**完全相同**。若 deck 哈希每次都变，说明 zip 时间戳没有
真正固定。

## 7. 机制组合效应：单独失效时的连锁后果

六个机制不是并列的功能点，而是**互相依赖的链条**。下表给出"抽掉某一个"的可预测
后果——这也是审阅者检验本包是否真有机制的最快路径：

| 抽掉 | 直接后果 | 连锁后果 | 会掉哪条指标 |
|-|-|-|-|
| M1 方案先行 | 没有 `adopt_plan.json` | M4 失去对照基准（无从测偏差）→ Q6/Q7 无法计算 | Q6 / Q7 / E2 |
| M2 契约先行 | 没有 G1–G8 与独立校验 | 产物缺件只能在人眼看时才发现 → Q8 失去判定 | Q8 |
| M3 证据定位 | 页面允许无来源内容 | `slide_evidence` 变成复述，Q3 归零；证据映射附录失去意义 | Q3 |
| M4 一致性审计 | 方案与执行脱钩 | M1 的"方案"退化为装饰文档 | Q7 / Q6 |
| M5 运行时生成 | 必须往包里塞 `.pptx`/`.png` | 触题面硬约束（资源类型 / 文件数），**整包可能被拒收** | 全部（包都收不了） |
| M6 确定性字节 | 每次跑出不同哈希 | 无法做回归比对；"产物是不是跑出来的"不可核 | E3 |

**读法**：M5 位于最外层（包能不能被接收），M2 决定"交付物是否完整"，M1/M3/M4 决定
"内容是否可信"，M6 决定"过程是否可复验"。这也解释了为什么本包把 M1 与 M2 放在
最前面：它们是其余机制能够被测量的前提。

## 8. 与常规做法的边界（本包不做什么）

- **不代写科学内容**：材料里没有的数值、结论、图件绝不补造；找不到 `文件:行`
  定位的条目不上页面（D4）。
- **不做像素级导出**：无 LibreOffice/PowerPoint 时不产伪 PDF，预览是 PIL 示意图
  并在文件名与图内双重标注（D14）；对应的契约键保持 `false` 而不是谎报 `true`。
- **不改写模板主题**：主题字体与主题色只做**只读记录**（读 `theme1.xml`），
  不换色板、不改主题 XML（D8）。
- **不覆盖动画/切换/SmartArt/艺术字**：超出"学术汇报模板适配"的范围。
- **不预置答案、不冒充成绩**：`examples/` 一律标注"示例，非正式案例"；
  `GAIN-PROTOCOL.md` 里的数字是作者在合成示例上的实测，明写"不是平台分数"。
- **不给"看起来热闹"的装饰页**：没有来源的图表、没有主张的页面不进交付物。
