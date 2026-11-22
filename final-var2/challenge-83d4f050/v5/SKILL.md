---
name: biological-mechanism-pathway-diagram
description: >-
  把机制/通路材料转成可逐条质疑的生物机制图与通路图（声明式机制规格 → 区室约束布局 →
  可编辑分层 SVG 源 + PNG/PDF 预览 → 拓扑与图例/数据编码审计 → 契约化 result.json），
  并把"换一个题材还灵不灵"做成**可复跑的题集**：随包提供 3 个合成案例
  （受体激酶级联 / 免疫突触跨膜募集-无数值 / 植物激素基因-RNA-有数值），
  每个案例给出输入、期望产出结构、可接受区间、难度层与实测读数，
  并**如实写明泛化边界**（散文材料、PDF、枚举外类型、无数值 vs 有数值、逆流边、契约回显语义）。
  Use when the task asks to draw, generate, edit, re-export or validate a biological
  mechanism map, pathway diagram, signaling cascade, regulatory network or flow
  diagram (figures group of the biology mechanism & pathway challenge), including
  tasks that require editable sources with per-element provenance, or when you need
  to know how far this pipeline generalises beyond one worked example.
---

# biological-mechanism-pathway-diagram（多案例泛化与题集版）

一个只能画好"示例里那张图"的 Skill 没有价值。本版把**泛化能力本身**做成可检验的东西：
三个**题材互不重叠**的合成案例、每个案例的**期望结构 + 可接受区间 + 难度层**、
以及一份**诚实的失效边界表**（泛化到哪里会断、断了会怎样、怎么补救）。

> 判断这个 Skill 是否真的能用，不问"它能不能画通路图"，而问三个问题：
> **① 换一个题材（基因/RNA 而不是蛋白）还行不行？② 材料没有数值时会不会编造数据编码？
> ③ 材料是散文/PDF 时它是硬撑还是老实说不？**

## 0. 资源形态（先读）

本包**只有文本资源**，契约原文：
`at most 50 UTF-8 text files, 500KB each and 2MB total, no symlinks`。
允许扩展名仅 `.md .py .json .txt .csv .yaml .yml`；`diagram.svg` / `diagram.png` / `diagram.pdf`
一律在 `--out` 目录**运行时生成** —— 包里看不到图是设计，不是缺失。
**不要在包内运行任何脚本**（会生成 `scripts/__pycache__/`，使包不再合规）；复制到 `/tmp` 再跑。

## 1. 用途与适用条件

- **适用**：机制图 / 通路图 / 信号级联 / 调控网络 / 流程图 / 图表编辑；也适用于
  "拿到一份新材料，想知道这套流程能不能直接套"的前期判断（见 §5 的边界表）。
- **不适用**：数值统计与统计结论、实验方案设计、论文写作与版式美化（相邻课题负责）。
- **能力边界（先说清楚）**：本 Skill 泛化的是**"实体—关系—区室—图例"这套结构**，
  **不是**"从任意自然语言/PDF 自动读懂机制"。材料越结构化，自动化越高；越散文，越依赖人工核验。

## 2. 输入与输出

**输入**：`case.json`（`case_id`/`title`/`task`/`materials`/`render`/`output_contract`）、
`task.md`、材料文件（**必须实际读取内容**，不得按文件名猜）。
**输出**（全部运行时生成）：

| 文件 | 角色 |
|---|---|
| `result.json` | **唯一评分产物**：信封 19 键 + `output_contract` 全字段四形态回显（**禁止 null**） |
| `diagram.svg` | 可编辑源：7 个 `layer-*` 组 + 元素级 `data-id/data-type/data-source` |
| `diagram.png` / `diagram.pdf` | 预览与矢量导出（同一布局引擎，与 SVG 一致） |
| `model.json` | 机制规格（实体/边/来源/图例），独立复核用 |
| `topology.json` / `legend_audit.json` | 拓扑审计与图例/数据编码审计产物 |

字段定义、四形态规则与硬性门 G1–G8 见 `references/OUTPUT_CONTRACT.md`（**唯一契约权威**）。

## 3. ★ 题集：三个互补案例（本版核心）

完整规格（输入清单、期望产出结构、可接受区间、难度层、逐案实测读数、失效边界）见
**`references/CASE-SET.md`**。摘要：

| 槽位 | 案例 id | 题材 | 主实体 | 难度层 | 关键考点（用它检验什么） |
|---|---|---|---|---|---|
| 内置 | `example-egfr-mapk` | 受体酪氨酸激酶级联 | 蛋白/复合物 | L1 | 标准流程图：线性主链 + 负反馈 + 同名蛋白按区室拆分 |
| 新增 A | `synth-immune-synapse-tcr` | 免疫突触近膜信号（TCR→ZAP70→LAT→PLCγ1→钙→NFAT） | 复合物/激酶/第二信使 | **L2** | **材料没有数值 ⇒ 不许颜色编码**；跨膜募集产生"逆流边"；同一蛋白跨区室 |
| 新增 B | `synth-plant-hormone-mirna` | 植物激素 + 转录后调控（乙烯→EIN3→ERF1 / miR164→NAC1） | **基因 / RNA** | **L2** | **有数值 ⇒ 必须画色带**；gen 与转录本类型判定；并行分支不得串联 |

**为什么是这三个**：A 与 B 在"有没有数值"这条轴上**正好相反**，
在"主实体是蛋白还是基因/RNA"这条轴上也**正好相反**；任何"只会一种套路"的做法都会在其中一侧露馅。
三案在"已核验规格"路径上的实测读数（2026-11-22 本机）：

| 案例 | exit | status | gates | 实体/边/区室 | self_check failures/warnings | 告警 | `data_mapping.field` |
|---|---|---|---|---|---|---|---|
| `example-egfr-mapk` | `0` | `success` | `8/8` | 9/9/4 | 0 / 0 | 无 | `表达量` |
| `synth-immune-synapse-tcr` | `0` | `success` | `8/8` | 12/12/4 | 0 / **3** | P03, P07, L03（逐条可解释，见 CASE-SET.md §3.2） | `""`（无数值） |
| `synth-plant-hormone-mirna` | `0` | `success` | `8/8` | 8/8/2 | 0 / 0 | 无 | `表达量` |

> 数字来自包外副本上的真实运行，**复跑命令写在 `CASE-SET.md` §5**；文档数字与实跑同源。

## 4. 执行流程（CP1–CP5）

> 脚本用 `os.path.dirname(__file__)` 自定位，与 cwd 无关。先固定技能根：

```bash
export SKILL_DIR=/skills/weekly-skill        # 平台容器；本机改成本包根目录
python3 "$SKILL_DIR/scripts/main.py" --help  # 自检：能打印帮助即路径正确

# 已核验规格路径（推荐）：三案之一
python3 "$SKILL_DIR/scripts/main.py" \
    --case "$SKILL_DIR/examples/cases/plant-hormone/case.json" \
    --model-file "$SKILL_DIR/examples/cases/plant-hormone/model.json" --out /app/output
# 草稿路径（自动抽取、未人工核验 ⇒ exit 2 / partial，符合设计）
python3 "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out /app/output
```

| 阶段 | 做什么 | 落下的东西 |
|---|---|---|
| **CP1 读真实文件** | 读 `case.json` / `task.md` / 逐个读材料；事实逐条记出处（文件+行号） | `change_records` 首条 |
| **CP2 规格 + schema 门** | 结构化材料走 `extract.py` 出草稿；散文/PDF 走 CP2b 手写；规格先过 `assets/mechanism-spec.schema.json`（**校验未归一化规格**，防静默改写） | `model.json` |
| **CP3 人工核验（强制）** | 逐条对照材料：实体是否存在、类型对不对（基因/RNA/蛋白/复合物）、边类型与方向、证据强度、区室归属；`verified_by_agent=true`；改动写 `change_records` | 核验证据（`templates/relation-checklist-template.md` 五表） |
| **CP4 布局/渲染/双审计** | 确定性区室布局 → 分层 SVG → PNG/PDF → `topology.py`(P01–P08) + `legend_audit.py`(L01–L08/E01–E02) + `validate_figure.py` 聚合 | 三件产物 + 自检 |
| **CP5 契约与终态** | 写 `result.json`，`status`／退出码／`gates` 三者自洽 | 交付信封 |

**逐案实测的完整算术**（含草稿路径计数、两份独立 CLI 的复查、用时）见 `CASE-SET.md` §3。

## 5. ★ 泛化边界（先看这张表，再决定要不要换题材）

| # | 边界 | 表现 | 缓解 |
|---|---|---|---|
| F1 | **散文材料**（无实体表、无 `A 动词 B（证据）` 行） | 抽取器报 `manual-required`，草稿路径 **exit 3 / failed** | 走 CP2b 手写 `model.json`（本包三个案例都给了可对照的规格格式） |
| F2 | **PDF / 扫描件** | 抽取器直接跳过 `.pdf` | 外部工具抽文本，或手工建规格（`extraction.method=manual`） |
| F3 | **枚举外类型**（`type="banana"`） | schema 门 **exit 3 / failed**，**不会**被静默改写成 `other` | 改规格不改图 |
| F4 | **契约字段只保证形态、不保证语义** | 声明字段一定回显且非 null，但管道无真实值时按四形态填空（字符串→`""`、列表→`[]`） | 真值请从 `scientific_content` 读（`counts` / `data_mapping.field`） |
| F5 | **逆流边**（如膜募集事件） | 记 `P03`/`P07` **warn** 而不是 fail（案例 A 实测 2 条） | warn 不阻断 success，但必须在 `uncertainty` 逐条说明 |
| F6 | **数值缺失/退化** | 案例 A 实测 `data_mapping.field=""` + `L03 warn`；有声明无数值时退回类型默认色 | 不要在无数值案例上强行插值 |
| F7 | **区室词表** | 非常规区室名会归一失败并给 warn | 用规范词表（`references/mechanism-spec.md` §4） |
| F8 | **图面规模** | 元素过多时布局拥挤，靠 `layout.warnings` 提示；**本包不自动分图** | 拆子图/缩小字号并记录 |
| F9 | **字体/渲染环境** | 无 matplotlib ⇒ 仅 SVG（`partial`）；缺中文字体 ⇒ PNG 告警入 `export_checks` | 见 `references/failure-modes.md` |
| F10 | **契约自定义字段类型** | 只覆盖 `str/list/bool/number/dict`；复杂结构按 `[]` 降级 | 复杂结构放 `scientific_content` |

> 完整版（含每条边界的代码依据与复验方式）见 **`CASE-SET.md` §4**。

## 6. 新题材决策规则（N1–N10：换一个案例时先查这张表）

| # | 触发信号 | 动作 | 记录位点 |
|---|---|---|---|
| N1 | 材料是散文/PDF | 走 CP2b 手工建规格；不要指望抽取器 | `extraction.method=manual` |
| N2 | 主实体是基因/RNA/小分子（不是蛋白） | 用对类型与书写（基因正方框、RNA 虚线圆角框、小分子圆形）；**不要**统一画成圆角矩形 | `scientific_content.entities[].type` |
| N3 | 材料没有数值列 | **关闭**颜色数据映射：`data_mapping.field=""`，图例注明"本案例无数值编码" | `legend_audit` L03 会是 warn（正常） |
| N4 | 材料有数值列 | 必须画色带 + 标"低/高"，且每个数值可定位到材料行 | `data_mapping`、E01/T03 |
| N5 | 出现"募集/转位/入核"类事件 | 方向按材料原意；逆着区室流会被记 P03/P07 warn，要在 `uncertainty` 说明理由 | `uncertainty` |
| N6 | 同一分子出现在多个区室 | 按区室拆实体并互相注明；不要用一条跨区室边代替 | `entities[].note` |
| N7 | 两条并行分支（如 ERF1 / miR164） | 并置布局，**禁止**串成一条链（会改变机制含义） | `layout.constraints.parallel_branches` |
| N8 | 反馈环 | `feedback=true` 右侧绕行；弱证据用虚线 | `edges[].feedback` |
| N9 | 材料给了新的区室名 | 先查规范词表；确实需要的自定义区室要在图例与 `layout.compartments` 同步声明 | `layout.warnings` |
| N10 | 想把新案例加进题集 | 按 `CASE-SET.md` §6 三步走；**必须写明它的失效边界**，否则不算完成 | `CASE-SET.md` §1/§2/§3 |

## 7. 交付前自查清单（逐条打勾，任一条打不上就不报 success）

- [ ] 实际读了 `case.json` / `task.md` / 全部材料，没有按文件名猜内容；
- [ ] 实体类型判对（基因/RNA/蛋白/复合物/小分子没有混用），区室归属与材料一致；
- [ ] 边类型与方向来自材料原意；逆流边已在 `uncertainty` 说明（N5）；
- [ ] 图例覆盖在用类型与箭头，颜色/线宽与图面逐值一致；
- [ ] **有数值** ⇒ 色带 + 低/高标签 + 数值可溯源；**无值** ⇒ 关闭映射并注明（N3/N4）；
- [ ] 并行分支并置、反馈环右绕（N7/N8）；
- [ ] SVG 7 层良构；PNG/PDF 或明确记录缺失原因；
- [ ] `result.json` 契约字段齐全（四形态、顶层无 null）；`check_contract.py` exit 0；
- [ ] `status` / 退出码 / `gates` 自洽；`uncertainty` 与 `change_records` 诚实；
- [ ] 若新增/修改案例：`CASE-SET.md` 的表已更新，且写明失效边界（N10）。

## 8. 反预制答案规则

`examples/`（含 `examples/cases/`）里的三个案例都是**合成演示**，与平台固定 3 个正式案例无关；
正式运行**禁止**把它们的实体/边/数值抄进正式输出。`assets/result.template.json` 只是结构模板。
**不给自己编造任何评分数字**；本包只报"实跑读数"（退出码/状态/计数/告警），不报分数。

## 9. 限制与维护

- 图件不在包内；SVG/PNG/model/topology/legend_audit 为确定性产物，`result.json` 与 PDF 含时间戳。
- 自动抽取只处理结构化语句；散文/PDF 走人工（"准确率优先于全自动"）。
- **改动流程**：改色 → `assets/palettes.json`；改契约/门 → `references/OUTPUT_CONTRACT.md` +
  `check_contract.py` + `result_writer.py` 三处同步；改校验规则 → `topology.py` / `legend_audit.py` /
  `validate_figure.py`；**加案例 → 按 §6/N10 更新 `CASE-SET.md`**。改完跑 `TEST.md` 全套并追加 `worklog.md`。
- **明令禁止**：向包内添加二进制资源、`__pycache__`、预置图件。

## 10. 文件索引（相对 `$SKILL_DIR`）

| 文件 | 作用 |
|---|---|
| `references/CASE-SET.md` | **本版核心新增**：题集（3 案 × 输入/期望结构/可接受区间/难度层）+ 逐案实测 + 失效边界 F1–F10 + 加案例步骤 |
| `examples/cases/immune-synapse/**` | **本版新增案例 A**：跨膜募集 + 无数值（12 实体 / 12 边 / 4 区室） |
| `examples/cases/plant-hormone/**` | **本版新增案例 B**：基因/RNA + 有数值（8 实体 / 8 边 / 2 区室） |
| `references/OUTPUT_CONTRACT.md` | 字段契约 + 四形态回显 + G1–G8 + §10 多案例的契约回显实测 |
| `references/failure-modes.md` | F01–F24 失败模式（含"换题材"相关分支与记录位点） |
| `references/RUBRIC_MAP.md` | 五维评分落点（实际效果/生态贡献按案例与题集逐条落点） |
| `references/mechanism-spec.md` / `legend-encoding.md` | 规格结构、命名与区室规范；箭头语义与数据编码 |
| `assets/` `templates/` `examples/` | schema/调色板/结果模板；人工核对清单；内置示例与两个新增案例 |
| `scripts/{extract,model,layout,pathway_svg,mpl_backend,topology,legend_audit,validate_figure,check_contract,result_writer}.py` | 抽取/规格/布局/渲染/审计/契约/写盘 |
| `README.md` / `TEST.md` / `COMPARE.md` / `worklog.md` | 依赖与用法 / 自测（含 T11 三案例实测）/ 对照方案 / 构建日志 |
