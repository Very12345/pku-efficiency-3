# RUBRIC_MAP.md — 五维评分落点（本版以**使用增益 25**为主轴）

> 交付前自评的唯一对照表。官方题面维度：
> **实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 · 生态贡献 10**（+ GitHub 附加 5）。
> 本版的强化选择是"把更强写成可测断言"，因此 **§1 把使用增益的 15+5+5 拆到可跑的命令上**，
> §2 给出其余四维的落点，§3 是"对照不是什么"的口径边界。
> 纪律：**表中每条复核命令都必须能当场跑出同一结果；引用数字必须来自本机真实运行。**

## 1. 使用增益 25 分逐条落点（本版主攻）

| 评分点 | 分 | 本版证据（文件 / 机制 / 实测数字） | 复核命令 |
|-|-|-|-|
| **质量增益** | 15 | 与朴素单遍流水线的结构性差异，逐格可查（条件 T，`--repeat 2`）：`substantive_claim_coverage` 0.0 → **1.0**；`evidence_rows` 0 → **6**；`evidence_locations` 0 → **6**；`contract_fields_present` 7/19 → **19/19**；`notes_pages` 0 → **8/8**；`over_limit_frames` 2 → **0**；`rework_points` **6 → 0**。机制侧：`spec_lint` BL-1/BL-3 强制"一页一主张 + 证据或显式 gap"，`overflow_guard`（≤6 条 / CJK 加权 ≤110）在生成期再截断，备注与页面文字分离 | `python "$SKILL_DIR/scripts/gain_probe.py" --out <scratch> --arms baseline,skill,ablation --repeat 2` → 读 `<scratch>/gain-report.json` |
| **效率增益** | 5 | 一条命令端到端（`main.py --case --spec --out`），脚本自身秒级：示例案例 `wall_seconds` **2.155 / 2.508**（两次），基线 0.028（对照的是脚本开销，不含人工修改页数——见 §3 边界）；返工点 **6 → 0** 即"交付前人工要修的地方"减少；`--demo` 可先出骨架验证管道再补内容 | 同上（`metrics.wall_seconds` / `metrics.rework_points`） |
| **增益可验证性** | 5 | ① 协议文档 `references/GAIN-PROTOCOL.md`（四同条件 + 三臂定义 + 指标定义 + 实测记录 + 复跑步骤）；② 执行件 `scripts/gain_probe.py`（同一 `_review()` 测三臂，`rework` 原文逐条保留）；③ 确定性：同臂两次运行 **72 个 OPC 部件逐部件一致**（`differing_opc_parts=0`）；④ 边界声明明确写出"这不是平台白板分数" | 同上；再跑一次确认 `differing_opc_parts` 仍为 0 |

**消融证据（机制可归因，不是整体感觉）**：`ablation` 臂（`main.py --demo`，去掉 Agent
写的页级方案与 Q1 前置门）在条件 T 下得到 `substantive_claim_coverage` **0.0**、
`placeholder_claims` **1**、`evidence_rows` **1**、`evidence_locations` **0**、
`notes_pages` **3/6**、`rework_points` **2** —— 相对 `skill` 臂的全面退步说明
"方案先行 + 页级证据"是**可测量、可归因**的贡献项。

## 2. 其余四维落点

| 维度 | 分 | 本版落点 | 复核命令 |
|-|-|-|-|
| **实际效果** | 40 | `SKILL.md` §4 执行链 Step 0–6（Q1/Q2/Q3 三道闸门）；`main.py` 串起抽取→构建→预览→检查→契约；正确性由 `spec_lint` BL-1…BL-4 + `export_check` G1–G8 反查；完整性靠必需页自动补齐 + H08 合并规则；可核验性靠双形态证据映射（md 人读 + json 机读，同源）+ `run_meta.checkpoints` | `python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --task "$SKILL_DIR/examples/task.md" --spec "$SKILL_DIR/examples/deck-spec.json" --out <tmp>/out` → exit 0；`export_check.py` / `check_contract.py` 均 exit 0 |
| **创新增益** | 15 | ① 契约先行且**文档-代码同源**（`check_contract.py` 直接读 `.md` 字段表，解析不出即 exit 2，绝不假通过）；② 方案先行 + Q1 前置门（消融已证明其可测贡献）；③ **增益可执行化**：把"更强"写成 `gain_probe.py` 的三臂对照（本版新增）；④ 双形态证据映射 + 行数守恒门 G7；⑤ OOXML 分层命名（对象名 = 可编辑性的机器可查证据）；⑥ 运行时资源自生成以通过"仅文本资源"硬门 | `python "$SKILL_DIR/scripts/gain_probe.py" --arms ablation --out <scratch>`；`references/GAIN-PROTOCOL.md` §4.1 的消融行 |
| **可靠体验** | 10 | 触发词（中英）+ §2 输入输出 + §4 三步调用；脚本 `__file__` 自定位（cwd 无关，两种调用风格均 exit 0）；六级回退（PDF/图片/模板/字体/渲染/契约）见 `failure-modes.md`；H01–H14 每条给出触发/首选/降级/记录；统一退出码语义（0/1/2/3） | TEST.md T-B2 / T-B8 / T-B11；`main.py --case /nonexistent.json --out <tmp>/x` → exit 3 |
| **生态贡献** | 10 | 每个脚本有独立 CLI（含新增的 `gain_probe.py`）；`deck-spec` schema 可当页级大纲模板；蓝图映射与证据表格式可平移；`make_synthetic_inputs.py` 的合成夹具可作任何 PDF 管道的回归样本；`GAIN-PROTOCOL.md` 的指标定义可迁移到其它"文档→演示"题做对照 | `python "$SKILL_DIR/scripts/make_synthetic_inputs.py" --out <tmp>/synth`；`find "$SKILL_DIR" -type f` |

## 3. 对照的口径边界（写进自评，避免夸大）

1. `gain_probe.py` 的 `baseline` 是"基础 Agent 行为"的**可执行代理**，不是对某个具体 LLM
   的测量；权威口径仍是平台白板对照。
2. `wall_seconds` 只反映脚本开销（秒级），**不等于**"端到端总耗时更短"——题面要求考察的
   "人工修改页数下降"必须在平台口径下测量，本包只提供"返工点 6 → 0"作为代理量。
3. 实测记录建立在**合成示例案例**上（`examples/`，明确标注非正式案例）；
   正式 3 个案例由平台提供，本包不预置任何答案。
4. 条件 T（模板在场）与条件 N（无模板）的数字**分开记录**，不混用；混用会把条件差异
   误报成能力差异。

## 4. 维护

- 版本：`scripts/main.py` 的 `VERSION`（当前 `2.1.0`）；本表随能力变更同步更新；
- **数字同步铁律**：改动影响 GAIN-PROTOCOL §4 任一行 → 重跑协议 → 更新该处与
  `TEST.md`、本表 §1 的数字；禁止沿用旧数字；
- 新增能力必须给出：落点文件、复核命令、失败时的记录字段（写进 `failure-modes.md`）；
- 题面评分维度若更新，先改本表再改实现，避免"文档承诺 > 代码事实"。
