---
name: graphical-abstract
description: >-
  从研究材料产出单页 Graphical Abstract（图形摘要）的 Skill，本版以「多案例泛化与题集」
  为轴心：材料 → 实体/关系/数据抽取（逐元素 data-src 溯源）→ 方案先行（scaffold 骨架 +
  方案 lint）→ 确定性版面与数据编码 → 可编辑分层 SVG（layer:* 七层契约）+ PNG/PDF 渲染件 →
  audit 与契约自查；并附一套**三个不同题材的可复跑题集**（examples/ 最小示例 +
  examples/cases/ 两个合成案例）与 references/CASE-SET.md（逐案输入、期望产出结构、
  可接受区间、难度层、实测结果、**泛化失效边界**）。Use when the task says
  "graphical abstract"、"图形摘要"、"示意图 / 机制图 / 流程图 / 图稿"、"为论文或基金画一张图"、
  "编辑已有的图稿"，或需要在不止一种题材与材料形态上验证同一条出图链路。
---

# Graphical Abstract 图形摘要 Skill — 多案例泛化与题集版

把「研究问题 → 方法 → 核心结果 → 结论」压进**单页**，交付**可继续编辑的分层源文件**、
渲染预览与字段完整的 `result.json`。**数值不编造**：材料里定位不到的数值只进 `uncertainty`
并在图上以「数值缺失」占位。

本版的差别是**不止一个案例**：包内自带三个不同题材的可跑案例，逐案给出"输入 → 期望结构 →
可接受区间 → 实测结果"，并把**这条链路在哪里会退化**写成可复现的边界，而不是笼统说"支持广泛场景"。

| 项目 | 值 |
|-|-|
| Skill 名称 / 版本 | `graphical-abstract` / `2.0.0`（脚本内 `SKILL_VERSION`） |
| 技能根 | 本文件所在目录，下文记作 `$SKILL_DIR` |
| 资源形态 | 纯文本七种扩展名（`.md .py .json .txt .csv .yaml .yml`）；无二进制、无预置 `.svg/.png/.pdf`、无字体文件、无 `__pycache__`、无本机绝对路径 |
| 出图入口 | `python "$SKILL_DIR/scripts/main.py" --case <case.json> [--task …] [--material …] [--plan …] [--out <dir>] [--pdf\|--no-pdf] [--raster-scale N]` |
| 本轴新增 | `examples/cases/{calab-perovskite-001,urban-heat-001}/`、`references/CASE-SET.md` |
| 题集实测 | 三案全部 exit 0；两案 `success`、一案 `partial`（缺值 + 材料数值矛盾，均已在 `uncertainty` 说明）；确定性复跑逐字符一致 |

---

## 0. 调用（cwd 任意；命令逐字可用）

脚本用 `scripts/common.py` 的 `SCRIPT_DIR = dirname(abspath(__file__))` 自定位技能根，
**不要求 cwd = 技能根**：

```bash
# 技能根（二者取一；不确定时向上探测含 SKILL.md 的目录）
SKILL_DIR=/skills/weekly-skill
SKILL_DIR=/abs/path/to/graphical-abstract-7030fff2

# 三个案例（题集）：最小示例 + 材料/能源 + 地球/环境
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/ga-c0
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/cases/calab-perovskite-001/case.json" --out /tmp/ga-c1
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/cases/urban-heat-001/case.json" --out /tmp/ga-c2

# 契约自查（exit 0 = 顶层覆盖「信封 18 键 ∪ 案例契约」且无 null）
python "$SKILL_DIR/scripts/check_contract.py" --result /tmp/ga-c1/result.json \
       --case "$SKILL_DIR/examples/cases/calab-perovskite-001/case.json"

# 官方案例形态（平台挂载输入，产物写 /app/output）
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md --out /app/output
```

参数表、依赖与退出码语义见 `README.md`；**逐案期望结构与实测结果见
[`references/CASE-SET.md`](references/CASE-SET.md)**。

---

## 1. 适用与边界

**适用**：研究描述 / 实验记录 / 论文草稿 / 图表数据 → 单页视觉摘要、机制图、通路图、流程图；
编辑已有图稿；要求"可继续修改的源文件"；要求在**多个题材**上验证同一条链路。

**不适用**：论文正文写作、统计分析、实验设计、无 Q-M-R-C 叙事的纯数据可视化。
本 Skill 对图面科学内容的表达、版式、可编辑性与导出质量负责；**材料本身结论的真伪由人负责**。

---

## 2. 题集一览（包内自带；详见 CASE-SET.md）

| # | 案例 id | 题材 | 难度层 | 输入 | 实测 `status` |
|-|-|-|-|-|-|
| 0 | `example-micelle-001` | 纳米医学（pH 响应胶束递送） | L1 基线 | case.json + material.md + task.md | `success` |
| 1 | `calab-perovskite-001` | 材料 / 能源器件（钙钛矿界面钝化） | L2 标准 | 同上（7 实体 / 5 关系 / 7 数据点） | `success` |
| 2 | `urban-heat-001` | 地球 / 环境科学（城市热岛能量平衡） | L3 挑战 | 同上（**故意含缺值 + 数值矛盾**） | `partial`（限制均已记录） |

三个案例的差异是有意设计的：题材、实体类型、单位形态（`mA/cm2`、`cm-2`、`mm/day`、`%`、`K`）
与材料异常程度都不同 —— 用来逼出"只在一个案例上能跑"的假泛化。

---

## 3. 执行主链（每步都有出口判据）

```bash
# 0 方案先行（可选但推荐）：骨架 → 定稿 four_elements → 方案 lint（exit 0 才继续）
python "$SKILL_DIR/scripts/scaffold.py" --case <case.json> --out plan.json
python "$SKILL_DIR/scripts/spec_lint.py" --lint-plan --plan plan.json

# 1 出图：抽取 → 版面 → 规格 lint → 分层 SVG → 渲染 → audit → result.json
python "$SKILL_DIR/scripts/main.py" --case <case.json> --plan plan.json --out <out>

# 2 规格门独立复核
python "$SKILL_DIR/scripts/spec_lint.py" --spec <out>/spec.json --content <out>/content.json

# 3 契约门（判据 = 退出码）
python "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json --case <case.json>

# 4 确定性：同输入再跑一次，比较 audit.determinism_probe.spec_sha16
python "$SKILL_DIR/scripts/main.py" --case <case.json> --out <out>-2
```

作为 Agent，除调用脚本外**必须阅读真实文件内容并复核抽取结果**：材料里没有的数值不得上画布；
偏差写进 `change_records` / `uncertainty`。**不得用预制答案替代实际运行。**

---

## 4. 新增一个案例时要做的四件事

1. **写输入三件套**：`case.json`（`case_id / title / source_material / entities / relations /
   data / figure_constraints / output_contract`）+ `material.md`（数值与机制的唯一来源）
   + `task.md`（问题 / 方法 / 结果 / 结论四小节）。
2. **数值必须双向可定位**：case.json 里每个上画布的数值都要能在 `material.md` 中逐字找到
   （题集的自查就是这么做的；材料里找不到的数值只能进 `uncertainty`）。
3. **契约四形态齐备**：类型提示 / 容器 / 布尔 / 字段清单各至少一个字段，避免把契约写成单一形态。
4. **跑一遍并记录**：`exit code`、`status`、顶层键数、`uncertainty` 原文、六项 audit 判据、
   `check_contract.py` 退出码、二次运行的 `spec_sha16`。**不要只写"应该能跑"。**

---

## 5. 三个案例的实测摘要（原始数字见 CASE-SET.md）

| 判据 | `calab-perovskite-001` | `urban-heat-001` |
|-|-|-|
| exit code | **0** | **0** |
| `result.json.status` | **success** | **partial** |
| 顶层键数 | 26 | 26 |
| `uncertainty` 条目 | 0 | **2**（缺值占位 + 材料数值矛盾，均带 `src`） |
| `audit.missing_values` | `[]` | `['夜间地表温度差']` |
| 实体覆盖 / 数值编码一致性 | 7/7 · 7/7 | 7/7 · 6/6 |
| 四要素覆盖 | 4/4 | 4/4 |
| 图层命名违规 / 无 `src` 元素 / 越界 | 0 / 0 / 0 | 0 / 0 / 0 |
| `check_contract.py` | exit 0 | exit 0 |
| 两次运行 `determinism_probe.spec_sha16` | `8b1b2a88fc72eff3`（一致） | `d12251c822cf4141`（一致） |
| PNG 后端 | matplotlib | matplotlib |

---

## 6. 失败分支索引（完整表见 `references/failure-modes.md`）

| 规则 | 触发 | 记录位点 |
|-|-|-|
| D1 / D2 | `case.json` 缺失/不可解析 / 缺 `case_id` | stdout JSON（exit 1）/ `result.case_id` |
| D3 / D4 | `task.md` 缺失 / 材料路径缺失 | `warnings` / `uncertainty` |
| D5 / D6 / D7 | 数值缺失 / 实体歧义 / 材料数值矛盾 | `audit.missing_values` / `uncertainty`（**D7 实测：案例 B 的 0.14 与 0.19 并列**） |
| D8 / D9 | 材料非 UTF-8 / 二进制（含 PDF） | `uncertainty` |
| D10 / D11 / D12 | 字体缺失 / 渲染后端缺失 / PDF 不可用 | `render_log.json` / `deliverables` |
| D13 | 文字溢出 / 元素越界 | `audit.layout_log` / `audit.bounds` |
| D14 | 方案或规格 lint 不过 | `result.plan.lint` / `result.spec_lint` + `status` 降级 |
| D15 / D16 / D17 | 契约无真实值 / 键冲突 / 类型不符 | `check_contract.py` exit 0 / `output_contract_echo` / `uncertainty` |
| D18 / D19 / D20 | lint 不过仍想报成功（禁止）/ 产物无效（exit 2）/ 重跑结构漂移 | 三处一致 |

---

## 7. 交付前自查清单

- [ ] 三个案例分别跑通：`exit 0` 且各产出 `result.json`
- [ ] 每个案例的 `check_contract.py` **exit 0**（顶层覆盖信封 ∪ 案例契约、无 null）
- [ ] `audit.entity_coverage.missing` 与 `audit.encoding_consistency.missing_from_canvas` 均为空
- [ ] 四要素 4/4 上画布；图层命名无违规、无缺 `src` 元素
- [ ] `status=partial` 的案例：限制逐条写在 `uncertainty`，且**能追到具体材料行**
- [ ] 每案两次运行 `determinism_probe.spec_sha16` 一致
- [ ] 新增案例时，`case.json` 的每个数值都能在 `material.md` 中逐字定位（反之亦然）
- [ ] 按 `references/RUBRIC_MAP.md` 五维自评，并把本次运行的偏差写进 `change_records`

---

## 8. 五维落点（速查；完整对照见 `references/RUBRIC_MAP.md`）

| 维度 | 分 | 本包落点 |
|-|-|-|
| 实际效果 | 40 | 三案例跨题材实跑；单页四要素 + 可编辑分层 SVG + PNG/PDF；逐元素 `data-src` 与 `sources[]`(sha256) |
| 使用增益 | 25 | 换题材时只需换"输入三件套"，流水线、契约、自查全部复用；方案先行免重绘；确定性布局免重排 |
| 创新增益 | 15 | **自带可复跑题集 + 逐案可接受区间 + 泛化失效边界**（同类包通常只给一个示例）；方案先行双 lint 门；契约四形态回显 |
| 可靠体验 | 10 | 案例 B 专门构造缺值与数值矛盾两条降级路径并给出实测记录；退出码语义稳定（0/1/2）；六项 audit 红线 |
| 生态贡献 | 10 | 题集本身可被他人直接复用（输入 + 期望结构 + 区间 + 难度层 + 复现命令）；文档齐备 + `assets/` 三件套 + `GITHUB_URL.txt` |

---

## 9. 目录结构

```
<skill root>/
  SKILL.md                    本文档（题集导览 + 主链判据 + 加案例的四件事）
  README.md                   安装 / 依赖 / 参数 / 失败处理 / 维护
  TEST.md                     本机实测记录（三案例 + 确定性 + 契约）
  GITHUB_URL.txt              公开作品链接
  references/
    OUTPUT_CONTRACT.md        result.json 契约（字段块逐字保留）
    RUBRIC_MAP.md             五维 → 文件/机制逐条映射
    failure-modes.md          失败模式、降级策略、退出码、状态一致性
    CASE-SET.md               ★本轴新增★ 题集：逐案输入 / 期望结构 / 可接受区间 / 实测 / 失效边界
    plan-schema.md            设计方案 schema（方案先行）
    ga-four-elements.md       四要素知识文档（Q-M-R-C 不变式）
    layer-naming.md           SVG 分层命名与溯源属性规范
    TEMPLATE.md               面板模板 / 视觉通道映射 / 复用指南
  assets/                     可复用资产三件套（纯文本）
  scripts/
    main.py                   编排入口（--case/--task/--material/--plan/--out/--pdf/--no-pdf/--raster-scale）
    extract.py / figurespec.py / svgbuilder.py / preview.py
    audit.py / spec_lint.py / scaffold.py / check_contract.py / common.py
  examples/
    case.json / material.md / task.md / plan.example.json / EXPECTED-OUTPUT.md   L1 基线案例
    cases/calab-perovskite-001/{case.json,material.md,task.md}                   L2 材料/能源
    cases/urban-heat-001/{case.json,material.md,task.md}                         L3 地球/环境（含异常边界）
    output/                                                                    L1 案例的实跑文本产物
```

脚本不硬编码绝对路径；唯一出现的 `C:/Windows/Fonts` 等字符串是**跨平台字体探测候选路径**。

---

## 10. 限制（如实声明）

- 抽取依赖材料文本结构：**只有形如 `键 = 数值 单位` 的独立行**与**带真实箭头（`->`/`→`）的机制行**
  会被解析；散落在散文里的数字不会自动进数据通道（判据见 `references/CASE-SET.md` §4）。
- 材料内部数值矛盾目前只做到"首见优先 + 冲突留痕"（`uncertainty` 列出两处 `src`），
  **不做自动裁决** —— 哪个口径正确必须由人判断。
- 渲染后端链会逐级降级（matplotlib → Pillow → 纯 Python PNG），字体按候选路径探测；
  后端与字体名一律如实记录，降级时 `status` 降为 `partial`。
- 四要素/图层/契约检查是结构判据，不代替领域科学判断。
- 三个案例均为**合成示意**，不是平台正式案例，不代表正式成绩。
