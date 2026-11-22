---
name: biological-mechanism-pathway-diagram
description: >-
  把生物机制/通路材料转成可逐条质疑的机制图与通路图：从真实材料抽取实体与相互作用
  （激活/抑制/结合/修饰/转运），按区室约束确定性布局（胞外—膜—胞质—核），输出可编辑分层
  SVG 源文件与 PNG/PDF 预览，跑拓扑与图例/数据编码双审计，并写契约化 result.json。
  全维合并版：同一包里同时给出**可测的增益协议**（与基础 Agent 的同输入对照 + 8 项指标独立
  度量器）、**失败注入实测台账**（输入/模板/依赖/契约四形态 × 24 场景的真实退出码与留痕）、
  **机制分解 M1–M6**（每条说明去掉它会退化成什么）、**可复用资产清单与复用三步**，
  以及 **3 个互补合成案例的题集**（含泛化失效边界）。
  Use when the task asks to draw, generate, edit, re-export or validate a biological
  mechanism map, pathway diagram, signaling cascade, regulatory network or flow
  diagram (figures group of the biology mechanism & pathway challenge), including
  tasks that require editable sources with per-element provenance — or when you must
  judge how such a pipeline behaves under broken inputs, how much it improves over a
  plain agent, and how far it generalises beyond one worked example.
---

# biological-mechanism-pathway-diagram（全维合并版 · 文本包 · 图件运行时生成）

机制图的科学性只看三条：**每个实体和每条边能否回溯到输入材料或权威命名；图例、颜色映射与
图形本身是否自洽；别人能否打开源文件改一个标签再重新导出。** 本包把这三条做成**可执行**的
流水线，并把四个通常只写在文档里的问题也做成了可复算的读数：

| 问题 | 本包的答案在哪 | 一句话结论（本机实测） |
|---|---|---|
| 出错时会怎样？ | `references/FAULT-MATRIX.md` + `scripts/fault_inject.py` | 四形态 24 场景全部按预期失败：`24/24` 符合期望、**0 静默失败**、恢复演练 `6/6` |
| 比基础 Agent 好在哪？ | `references/GAIN-PROTOCOL.md` + `scripts/gain_probe.py` | 同输入同尺子：结构/溯源/语义/图例/契约/导出 6 项指标条件 A=0 → 条件 B=1.0 |
| 为什么这样设计？ | `references/MECHANISM.md`（M1–M6 + 消融） | 每条机制都写了"去掉它会退化成什么"与可验证信号 |
| 换一个题材还灵吗？ | `references/CASE-SET.md` + `examples/cases/` | 3 个题材不重叠的案例全部 `exit 0 / success / gates 8/8`，并写明 10 条失效边界 |

下文按 **输入 → 执行 → 失败 → 增益 → 机制 → 复用** 组织；每一节末尾都指向对应的 reference。

---

## 0. 资源形态（先读这条，它决定包怎么用）

本包**只包含文本资源**，遵守运行时契约硬约束：
`at most 50 UTF-8 text files, 500KB each and 2MB total, no symlinks`。

- 允许扩展名只有七种：`.md .py .json .txt .csv .yaml .yml`；
- 包内**没有任何图片 / PDF / 演示文稿**——`diagram.svg`、`diagram.png`、`diagram.pdf`
  一律由 `scripts/` 在**运行时现场生成**（`pathway_svg.py` 写 SVG，`mpl_backend.py` 渲染预览；
  matplotlib 缺失时降级为仅 SVG 并如实记录）；
- `examples/output/` 只有示例案例上实跑得到的 **JSON 产物**与文字化的 `examples/EXPECTED-OUTPUT.md`；
- **不要在包内运行任何脚本**（会生成 `scripts/__pycache__/`，包立刻不合规）；
  一律 `cp -r "$SKILL_DIR" /tmp/...` 之后在包外跑。`fault_inject.py` 自己就是这么做的。

## 1. 输入（读什么、不能猜什么）

**平台运行时输入**：

| 文件 | 字段/内容 | 用途 |
|---|---|---|
| `/input/case.json` | `case_id`（必填）、`title`、`task`、`materials[]`、`render`、`output_contract` | 案例标识、材料清单、画布、**契约字段声明** |
| `/input/task.md` | 任务说明（图号、必需元素、导出格式） | 任务要求 |
| 材料文件 | 正文 / 表格 / PDF；**必须实际读取内容** | 事实来源（每个事实记"文件+行号"） |

**三条铁律**：
1. **不得按文件名猜内容**，不得用领域标签脑补数据；
2. `output_contract` 声明的字段必须出现在 `result.json` 顶层，且**顶层禁止 `null`**；
3. 材料缺失/不可解析时报 `failed` 并给补救路径，**不画空图凑数**。

字段契约、四形态回显规则与硬性门 G1–G8 见 **`references/OUTPUT_CONTRACT.md`**（唯一权威）。

## 2. 执行（CP1–CP5）

> 所有脚本用 `os.path.dirname(__file__)` 自定位，**与 cwd 无关**。先确定一次技能根：

```bash
export SKILL_DIR=/skills/weekly-skill        # 平台容器；本机指向含 SKILL.md 的那一层
python3 "$SKILL_DIR/scripts/main.py" --help  # 自检：能打印帮助即路径正确

# 主路径（已人工核验的机制规格 → 期望 exit 0 / status=success / gates 8/8）
python3 "$SKILL_DIR/scripts/main.py" --case /input/case.json \
    --model-file /app/work/model.json --out /app/output --verbose
# 自动草稿路径（结构化材料可用；未人工核验 ⇒ exit 2 / partial，符合设计）
python3 "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output
```

| 检查点 | 动作 | 产物 / 记录位点 |
|---|---|---|
| **CP1** 读真实文件 | 读 `case.json` / `task.md` / 每个材料文件；提取任务要求、事实（含出处）、约束 | `change_records` 首条；材料缺失 ⇒ `failed`(exit 3) |
| **CP2** 机制规格 + schema 门 | 结构化材料由 `extract.py` 出草稿；散文/PDF 走 **CP2b** 手写规格；规格**先过 `assets/mechanism-spec.schema.json`（对未归一化规格校验）** | `model.json`；schema 不过 ⇒ `failed`(exit 3) |
| **CP3** 人工核验（强制） | 逐条对照材料：实体类型（基因/蛋白/复合物/RNA/小分子）、边类型与方向、证据强度、区室归属；置 `extraction.verified_by_agent=true` | 核对清单（`templates/relation-checklist-template.md` 五表）+ `change_records` |
| **CP4** 布局 / 渲染 / 双审计 | 确定性区室布局 → 分层 SVG → PNG/PDF → `topology.py`(P01–P08) + `legend_audit.py`(L01–L08、E01–E02) + `validate_figure.py`（聚合 M/T/P/L/E/S/F/D + 确定性探针） | `diagram.svg`(7 层) / `diagram.png` / `diagram.pdf` / `topology.json` / `legend_audit.json` |
| **CP5** 契约与终态 | 写 `result.json`；核 `status` / 退出码 / `gates` 三者自洽 | `result.json`（信封 19 键 + 契约回显） |

**输出清单**（全部写在 `--out`）：`result.json`（**唯一评分产物**）、`diagram.svg`（可编辑源）+
`diagram.png` + `diagram.pdf`、`model.json`、`topology.json`、`legend_audit.json` —— 共 7 件。

**退出码即终态**：`0 = success`（门 8/8、提取已核验）、`2 = partial`（有降级但产物在）、
`3 = failed`（阻断），入口级错误（case 不存在/坏 JSON）实测 `1` 且不写 `result.json`。
两条独立复查命令都必须 exit 0 才允许写 success：

```bash
python3 "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json --case <case.json>
python3 "$SKILL_DIR/scripts/validate_figure.py" --out <out>
```

→ 详细规范：`references/mechanism-spec.md`（规格/命名/区室）、`references/failure-modes.md`（失败处置）。

## 3. 失败（四形态注入 · 静默失败为零）

**为什么要有这一节**：可靠体验不能靠"文档说会降级"来证明。本包随带一个**可运行的失败注入器**，
把四形态逐个弄坏、跑真实主流程、把退出码与留痕位点记成台账。

```bash
cp -r "$SKILL_DIR" /tmp/fault-skill
python3 /tmp/fault-skill/scripts/fault_inject.py --skill /tmp/fault-skill --out /tmp/fault-out
# 退出码：0 = 全部场景符合期望；1 = 有场景不符（必须看报告）；4 = 技能路径无效
# 产物：fault-report.json（机器可读）+ FAULT-MATRIX.generated.md（同表）
```

| 形态 | 注入示例 | 期望的"正确失败"（实测终态） |
|---|---|---|
| **输入** | case 不存在/坏 JSON；材料目录空；材料非 UTF-8；枚举外类型；边端点不存在 | `1`（入口拒绝，不写 result.json）/ `3 failed`（材料缺失、schema 门）/ `2 partial`（草稿未核验）/ `0 success + uncertainty`（丢边留痕） |
| **模板** | 删/损坏 `palettes.json`、`mechanism-spec.schema.json`；删核对清单与结果模板 | `0 success` + `uncertainty`（调色板回退、schema warn）；核对清单/结果模板属**文档资产**（主流程不读，如实标 N/A） |
| **依赖** | `matplotlib` 不可导入 / `pyplot` 抛错；`Pillow` 缺失；`--formats svg` | `2 partial` + `gates.g5_png=false` + `previews=[]` + 原因入 `export_checks`/`uncertainty`；**绝不伪造预览** |
| **契约** | 四形态声明 + 声明值为 `null`；往产物塞顶层 `null`；缺 `result.json` | 四形态按 `""`/`[]`/`false`/`0`·`{}` 回显且无 null；`check_contract.py` 实测 `exit 1`（抓 C04/C01） |

**"静默失败"的判据**（本包的定义）：`exit 0` **且** `status=success` **且**
`uncertainty` / `reason` / `self_check.warnings` / `self_check.failures` **四个留痕位点全空**。

> **演练真的抓到了 3 处静默失败**（`exit 0 / success / 零留痕`）：
> ① 端点不存在的边被 `normalize_edges()` 丢弃（少画一个科学论断）；
> ② `palettes.json` 缺失/损坏时静默回退内置色板（与文档承诺不符）；
> ③ CP1.2 判 `warn`（无 task 文本）在成功路径被丢弃。
> 三处都已用**纯增量**补丁修掉（`model.py` 381→437、`main.py` 482→512，删除行数 0，
> CLI 参数与退出码语义未改），复跑台账：**`24/24` 符合期望、`silent_failures=[]`、`recovery=6/6`**。
> 逐条前后对比见 `references/FAULT-MATRIX.md` §4；失败处置的五个视图见 `references/failure-modes.md`。

## 4. 增益（可测，不靠形容词）

**主张**：加载本 Skill 后，产物在**结构、溯源、语义、图例、契约、导出**六类可机读指标上
稳定优于"不加载 Skill 的基础形态"。**度量方式**：`scripts/gain_probe.py` 用**同一把尺子**
同时量两个条件，且**不 import 本包任何模块**（避免"用被测者的尺子量被测者"）。

```bash
# 条件 A：基础形态的结构复现器（把题面点名的基础 Agent 失败签名做成确定性反例）
python3 "$SKILL_DIR/scripts/baseline_emulator.py" --material <材料> --out /tmp/condA
# 条件 B：本 Skill 主路径
python3 "$SKILL_DIR/scripts/main.py" --case <case.json> --model-file <model.json> --out /tmp/condB
# 同尺子度量
python3 "$SKILL_DIR/scripts/gain_probe.py" --compare /tmp/condA /tmp/condB --material <材料> --json
```

8 项指标（定义见 `references/GAIN-PROTOCOL.md` §2）：`A1` 具名图层、`A2` 溯源属性覆盖、
`A3` 边语义标签覆盖、`A4` 图例声明覆盖、`A5` 契约信封覆盖、`A6` 审计产物、`A7` 导出件、
`A8` 材料实体名覆盖。本机实测（同一份材料，2026-11-22）：

| 指标 | 条件 A（基础形态） | 条件 B（加载本 Skill） |
|---|---|---|
| A1 / A2 / A3 / A4 / A5 / A6 / A7 | 0.0（无分层、无溯源、无语义标签、无 result.json、无导出流水线） | **1.0**（7 层 + `data-*` + 语义标签 + 图例声明 + 信封 19/19 + 两个审计 + PNG/PDF） |
| A8 材料实体名覆盖 | 1.0 | 1.0（**不是差异点**，如实列出） |

> **诚实边界**：条件 A 是"题面点名失败签名"的**结构复现器**，不是平台基础 Agent 的真实运行；
> 真实对照由平台执行（同输入、同预算、每条件 3 次）。本包只保证**判据可复算**。
> 完整协议、效率侧读数（`E1`–`E3`）、复现要点与反作弊说明见 **`references/GAIN-PROTOCOL.md`**。

## 5. 机制（每条都回答"去掉它会退化成什么"）

| # | 机制 | 没有它会怎样 | 可验证信号 |
|---|---|---|---|
| **M1** | **规格先行**：先落声明式机制规格，再由它渲染 | 图与来源脱钩：改一个标签要重画，实体/边清单无法独立复核，多导出件互相漂移 | `model.json` 存在且含 `entities[]/edges[]/source[]`；改规格一次即可重导出全部图件 |
| **M2** | **raw 规格的 schema 门**：对**未归一化**规格做类型枚举校验 | 未知类型被静默改写成 `other`：一个错误论断被"美化"成合规图形 | 把实体 `type` 改成枚举外值 ⇒ 实测 **exit 3 / failed**（不是"悄悄改成 other 后成功"） |
| **M3** | **双审计闭环**：拓扑（方向/区室/同名/重复边/自环/反馈）+ 图例与数据编码（覆盖/颜色/虚线/线宽/数值溯源） | 图例与图面不一致、上下游颠倒、数值无来源只能靠人眼发现 | `topology.json` + `legend_audit.json` 落盘；基础形态同两条命令实测 **exit 1** |
| **M4** | **可编辑分层源 + 逐元素溯源**：7 个 `layer-*` 组 + `data-id/data-type/data-source` | 只能交一张位图：改不了、追不回 | SVG 具名图层 7 个、`data-source` 计数 ≥ 边数；基础形态两项均为 0 |
| **M5** | **确定性探针**：布局与 SVG 不含时间戳，`self_check.determinism` 报 `model_sha16/svg_sha16` | 无法判断两次运行是否等价，"可复现"无从检验 | 同输入双跑：SVG/PNG/model/topology/legend_audit **逐字节一致**（PDF 内嵌时间戳例外） |
| **M6** | **契约化终态**：信封 + 四形态回显 + G1–G8 + 状态/退出码三元组 | 结果无法机器复核；成功与失败在产物上看不出区别 | 信封 19/19、顶层 null 0、门 8/8、exit 0 |

六条不是并列功能，而是**互相咬合的一根链**：M1 产生可审中间物 → M2 在源头挡住错误类型 →
M3 渲染前后各审一遍 → M4 让产物可改可追 → M5 让运行可复现 → M6 让结果可复核。
断掉任何一环，后面的环节都失去意义。→ 消融推理、依赖链与边界见 **`references/MECHANISM.md`**。

## 6. 复用（题集 · 资产 · 三步搬运）

**题集（3 个互补合成案例，`examples/cases/` + `references/CASE-SET.md`）**：

| 槽位 | 案例 | 题材 | 难度层 | 关键考点 |
|---|---|---|---|---|
| 内置 | `example-egfr-mapk` | 受体酪氨酸激酶级联 | L1 | 线性主链 + 负反馈 + 同名蛋白按区室拆分 |
| A | `synth-immune-synapse-tcr` | 免疫突触 TCR 近膜信号 | L2 | **材料无数值 ⇒ 不许颜色编码**；膜募集类逆流边；同一蛋白跨区室 |
| B | `synth-plant-hormone-mirna` | 植物激素 + 转录后调控 | L2 | **材料有数值 ⇒ 必须画色带**；主实体是**基因/RNA**；并行分支 |

三案在"已核验规格"路径上实测 `exit 0 / success / gates 8/8`（实体边 9/9、12/12、8/8）；
草稿路径实测 `exit 2 / partial`（未核验），**但实体与边数已与人工版一致** ——
结构化材料可自动抽取，类型/方向/证据强度仍须 CP3 核验。
**泛化失效边界 F1–F10**（散文材料、PDF、枚举外类型、契约"形态≠语义"、逆流边只给 warn、
数值缺失/退化、区室词表、图面规模、字体与渲染、契约复杂类型）逐条写在 `CASE-SET.md` §4。

**可复用资产**（完整清单、复用场景、迁移检查表与常见坑见 `references/MECHANISM.md` §7）：
机制规格 schema、调色板与 glyph 语义、关系核对清单、四个带退出码的校验 CLI、契约与门、
最小可运行示例与实跑产物、失败分支表、独立度量器 `gain_probe.py`、反例生成器 `baseline_emulator.py`、
失败注入器 `fault_inject.py`、题集。

**复用三步**：① 搬骨架（`scripts/` + `assets/` + `references/OUTPUT_CONTRACT.md`）；
② 换语义（`assets/mechanism-spec.schema.json` + `assets/palettes.json` + `references/mechanism-spec.md` §9
三处同步，保持"箭头=科学论断"原则）；③ 验一遍（示例主路径 `0` → 两条审计 `0` → 故意失败用例 `3`
→ 写进新任务的 TEST.md，并复跑 `fault_inject.py`）。

## 7. 决策规则总表（遇情况先查表，不要临场发挥）

本包共有四套互相引用的规则，全部是"触发信号 → 动作 → 失败时降级（记录位点）"的形状：

| 规则集 | 主题 | 在哪 |
|---|---|---|
| **D1–D23** | 边界情况处置（方向缺失、同名基因/蛋白、多区室、PDF、契约四形态、状态一致性、自定位） | `references/failure-modes.md` §6（F 编号对照）；R1/v1 的规则表全文亦在该 §6 的表格中 |
| **R1–R10** | **出故障时**先修哪里（入口拒绝、材料缺失、枚举外类型、丢边、资产缺失、依赖缺失、格式请求、契约填空、三元组不一致） | 本文档 §3 + `references/FAULT-MATRIX.md` |
| **N1–N10** | **换题材时**（散文材料、基因/RNA、无数值、有数值、募集/转位、多区室、并行分支、反馈、新区室、加案例） | `references/CASE-SET.md` §2/§6 + 本文档 §6 |
| **M1–M6 / K1–K10** | 机制被破坏时先修哪一环 | `references/MECHANISM.md` |

共同底线：**任何降级都必须落在记录位点**（`uncertainty` / `reason` / `export_checks` /
`self_check` / `change_records` / `layout.warnings`）——"降级了但看不出来"就是缺陷（本包已修掉三处）。

## 8. 交付前自查清单（逐条打勾，任一条打不上就不报 success）

- [ ] 实际读取了 `case.json` / `task.md` / 全部材料，没有按文件名猜内容；
- [ ] 实体类型判对（基因/蛋白/复合物/RNA/小分子不混用），区室归属与材料一致；
- [ ] 每条边有 `source`（文件:行）；边类型与方向来自材料原意；逆流边在 `uncertainty` 说明；
- [ ] 图例覆盖在用类型与箭头；颜色/线宽与图面逐值一致；虚线语义 = 弱证据/不确定；
- [ ] **有数值** ⇒ 色带 + 低/高标签 + 数值可溯源；**无数值** ⇒ 关闭映射并在图例注明；
- [ ] SVG 7 层良构 + `data-*`；PNG/PDF 或明确记录缺失原因；
- [ ] `result.json` 契约字段齐全（四形态、顶层无 null）；两条复查 CLI 均 exit 0；
- [ ] `status` / 退出码 / `gates` 三元组自洽；`failed` 路径未冒充完整交付；
- [ ] `uncertainty` / `change_records` 诚实；改了脚本就**重跑 `fault_inject.py`** 并更新台账；
- [ ] 若新增案例：`CASE-SET.md` 的表已更新且写明失效边界。

## 9. 反预制答案规则（重要）

- `examples/`（含 `examples/cases/`）里的一切都是**合成演示，非正式案例**，图内与 `result.json`
  均带示例标记；正式运行**禁止**把示例/题集的实体、边或数值抄进正式输出；
- `assets/result.template.json` 只是结构模板；`scripts/baseline_emulator.py` 产出的是**刻意的坏例子**，
  不得作为正式输出、更不得冒充平台对照结果；
- 不写、不预测、不引用任何平台评分数字；本包只报**实跑读数**（退出码/状态/计数/门/告警）。

## 10. 限制与维护

- 图件不在包内；确定性承诺 = SVG / PNG / model / topology / legend_audit；
  `result.json` 与 PDF 含时间戳（不作确定性承诺）。
- 自动抽取只处理结构化语句；散文/PDF 走人工规格（"准确率优先于全自动"的刻意设计）。
- **改动流程**：改色 → `assets/palettes.json`；改契约/门 → `references/OUTPUT_CONTRACT.md` +
  `scripts/check_contract.py` + `scripts/result_writer.py` 三处同步；改校验规则 →
  `topology.py` / `legend_audit.py` / `validate_figure.py`；改语义枚举 →
  `assets/mechanism-spec.schema.json` + `references/mechanism-spec.md` §9；
  **改完必须重跑 `TEST.md` 全套 + `fault_inject.py`**，并更新 `worklog.md`。
- **明令禁止**：向包内添加二进制资源、`__pycache__`、预置图件。

## 11. 文件索引（相对 `$SKILL_DIR`）

| 文件 | 作用 |
|---|---|
| `references/OUTPUT_CONTRACT.md` | 契约权威：字段契约 + 四形态回显 + G1–G8 + §10 状态一致性矩阵 + §11 可测判定 + §12 机制→字段映射 |
| `references/RUBRIC_MAP.md` | 五维评分（40/25/15/10/10）逐条落点 + §8–§12 四套新维度的落点 |
| `references/failure-modes.md` | 失败处置**五个视图**（按阶段 / F01–F22 / 按机制 M1–M6 / 四形态注入 / 换题材 F1–F10） |
| `references/FAULT-MATRIX.md` | **失败注入实测台账**：24 场景 × 四形态 + 6 条恢复演练 + 三处静默失败修复前后 + 边界 |
| `references/GAIN-PROTOCOL.md` | **增益公平对照协议**：8 项指标定义、复算命令、实测记录、效率读数、局限 + 附录 A/B（同输入对照方案全文） |
| `references/MECHANISM.md` | **机制分解 M1–M6** + 消融推理 + 依赖链 + 边界 + §7 可复用资产清单与复用三步 |
| `references/CASE-SET.md` | **题集**：3 案规格（输入/期望结构/可接受区间/难度层）+ 逐案实测 + 失效边界 F1–F10 + 加案例流程 |
| `references/mechanism-spec.md` | 机制规格结构、命名与区室规范、导出与校验一览 + §9 符号语义与数据编码（原 `legend-encoding.md` 全文） |
| `scripts/main.py` | 单一入口（CP1–CP5；退出码 0/2/3） |
| `scripts/fault_inject.py` | **失败注入与恢复演练器**（四形态 24 场景；退出码 0/1/4） |
| `scripts/gain_probe.py` | **独立度量器**（`--dir` / `--compare`；不依赖本包模块） |
| `scripts/baseline_emulator.py` | **条件 A 反例生成器**（题面点名的基础 Agent 失败签名，仅供对照） |
| `scripts/{extract,model,layout,pathway_svg,mpl_backend,topology,legend_audit,validate_figure,check_contract,result_writer}.py` | 抽取 / 规格 / 布局 / 渲染 / 审计 / 契约 / 写盘 |
| `assets/` `templates/` `examples/` | schema / 调色板 / 结果模板；人工核对清单；内置示例 + 两个新增案例 + 实跑 JSON 产物 |
| `README.md` / `TEST.md` / `worklog.md` | 依赖与用法 / 自测与实测记录（含四条新轴的复跑记录）/ 构建与合并日志 |
