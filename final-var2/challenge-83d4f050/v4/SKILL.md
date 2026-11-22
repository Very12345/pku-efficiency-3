---
name: biological-mechanism-pathway-diagram
description: >-
  把机制/通路材料转成可逐条质疑的生物机制图与通路图（声明式机制规格 → 区室约束布局 →
  可编辑分层 SVG 源 + PNG/PDF 预览 → 拓扑与图例/数据编码审计 → 契约化 result.json），
  并把"出错时到底会怎样"做成可复算的台账：随包提供可运行的失败注入器
  `scripts/fault_inject.py`（把**输入/模板/依赖/契约**四形态逐个故意弄坏并跑真实主流程）
  与实测矩阵 `references/FAULT-MATRIX.md`（每个场景的退出码 / status / 留痕位点 / 是否静默失败）。
  Use when the task asks to draw, generate, edit, re-export or validate a biological
  mechanism map, pathway diagram, signaling cascade, regulatory network or flow
  diagram (figures group of the biology mechanism & pathway challenge), including
  tasks that require editable sources with per-element provenance, or when you need
  to know how such a pipeline behaves under broken inputs before trusting it.
---

# biological-mechanism-pathway-diagram（失败注入与恢复演练版）

机制图的科学性只看三条：**每个实体和每条边能否回溯到材料；图例、颜色映射与图面是否自洽；
别人能否打开源文件改一个标签并重新导出。** 本版在此之上回答第四个问题：

> **当输入坏了、资产丢了、依赖不在、契约对不上时，这条流水线会不会"假装成功"？**

答案不写在文档里，而是写在一份**可复算的实测台账**里：`references/FAULT-MATRIX.md`。
它由随包可运行脚本 `scripts/fault_inject.py` 当场生成 —— **四形态 × 24 场景 × 真实退出码**，
其中每个数字都能用一条命令复现。

## 0. 资源形态（先读这条）

本包**只有文本资源**：契约原文为
`at most 50 UTF-8 text files, 500KB each and 2MB total, no symlinks`。
允许扩展名仅 `.md .py .json .txt .csv .yaml .yml`；`diagram.svg` / `diagram.png` / `diagram.pdf`
一律由 `scripts/` 在 `--out` 目录**运行时生成**，包里看不到图是设计而不是缺失。

> **纪律（与失败注入直接相关）**：不要在包内运行任何脚本。
> 运行 `scripts/main.py` 会在 `scripts/__pycache__/` 留下字节码，把包变成不合规资源。
> `fault_inject.py` 自带防护（子进程 `PYTHONDONTWRITEBYTECODE=1`，且一切在**包外临时副本**里跑），
> 但复跑演练时仍建议照抄 `$SKILL_DIR → /tmp` 的复制步骤。

## 1. 用途与适用条件

- **适用**：机制图/通路图/信号级联/调控网络/流程图/图表编辑；也包括"先验证这条流水线在坏输入下的行为再决定要不要用"。
- **不适用**：数值统计与统计结论、实验方案设计、论文写作与版式美化（相邻课题负责）。
  本 Skill 只对图形中的科学内容表达、布局、可编辑性、导出质量，以及**故障行为**负责。
- **运行前提**：Python 3（标准库即可产出可编辑 SVG）；matplotlib/Pillow 可选，用于 PNG/PDF 预览，缺失时降级并留痕。

## 2. 输入与输出

**输入（平台运行时）**：`/input/case.json`（`case_id/title/task/materials/render/output_contract`）、
`/input/task.md`、材料文件（正文/表格/PDF，**必须实际读取**，不得按文件名猜内容）。

**输出（写入 `/app/output`，全部运行时生成）**：

| 文件 | 角色 |
|---|---|
| `result.json` | **唯一评分产物**：信封 19 键 + `output_contract` 全字段回显（四形态、**禁止 null**） |
| `diagram.svg` | **可编辑源**：7 个 `layer-*` 组，元素带 `data-id/data-type/data-source` |
| `diagram.png` / `diagram.pdf` | 预览与矢量导出（与 SVG 同一布局引擎） |
| `model.json` | 机制规格（实体/边/来源/图例），独立复核用 |
| `topology.json` / `legend_audit.json` | 拓扑审计与图例/数据编码审计产物 |

字段定义与硬性门 G1–G8 见 `references/OUTPUT_CONTRACT.md`（**唯一契约权威**）。

## 3. 主流程（CP1–CP5，与基线一致）

> 所有脚本用 `os.path.dirname(__file__)` 自定位，**与 cwd 无关**。先确定一次技能根：
>
> ```bash
> export SKILL_DIR=/skills/weekly-skill        # 平台容器；本机改成本包解压后的根目录
> python3 "$SKILL_DIR/scripts/main.py" --help  # 自检：能打印帮助即路径正确
> ```

| 阶段 | 做什么 | 落下的东西 |
|---|---|---|
| **CP1 读真实文件** | 读 `case.json`、`task.md`、逐个读材料；事实逐条记出处（文件+行号） | `change_records` 首条；材料缺失即 `failed` |
| **CP2 机制规格 + schema 门** | 结构化材料由 `extract.py` 出草稿；散文/PDF 由 Agent 手写规格；规格先过 `assets/mechanism-spec.schema.json`（**对未归一化规格校验**，防静默改写） | `model.json` |
| **CP3 人工核验（强制）** | 逐条对照材料；`extraction.verified_by_agent=true`；改动写 `change_records`；用 `templates/relation-checklist-template.md` 五张表当载体 | 核验证据 |
| **CP4 布局/渲染/双审计** | 确定性区室布局 → 分层 SVG → PNG/PDF → `topology.py`(P01–P08) + `legend_audit.py`(L01–L08、E01–E02) + `validate_figure.py` 聚合检查 | 三件产物 + 自检 |
| **CP5 契约与终态** | 写 `result.json`；`status`／退出码／`gates` 三者必须自洽 | 交付信封 |

```bash
# 已核验规格路径（推荐；示例案例上实测 exit 0 / status=success / gates 8/8）
python3 "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
    --model-file "$SKILL_DIR/examples/model.example.json" --out /app/output
# 草稿路径（未人工核验 ⇒ exit 2 / partial，这是设计而非缺陷）
python3 "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out /app/output
```

## 4. ★ 四形态失败注入（本版新增的核心机制）

**做法**：把技能复制到**包外**临时目录 → 只施加**一处**故障 → 跑**真实**入口 →
记录 `exit` / `status` / `gates` / `uncertainty` / 产物清单 → 判定它是**显式暴露**还是**被静默吞掉**；
对定义过修复动作的场景，再在干净副本上复跑一次，证明失败**可恢复**。

```bash
cp -r "$SKILL_DIR" /tmp/fault-skill                 # 绝不在包内跑
python3 /tmp/fault-skill/scripts/fault_inject.py \
    --skill /tmp/fault-skill --out /tmp/fault-out   # 全量 24 场景（约 1 分钟）
python3 /tmp/fault-skill/scripts/fault_inject.py \
    --skill /tmp/fault-skill --out /tmp/fault-out --family 契约        # 只跑一形态
python3 /tmp/fault-skill/scripts/fault_inject.py \
    --skill /tmp/fault-skill --out /tmp/fault-out --only dep-01-matplotlib-import
# 退出码即判据：0 = 全部场景符合期望；1 = 有场景不符（必须人看报告）
```

**四形态各注入什么**（完整 24 行实测见 `references/FAULT-MATRIX.md` §2）：

| 形态 | 注入示例 | 期望的"正确失败" |
|---|---|---|
| **输入** | `case.json` 不存在/坏 JSON；材料目录空；材料非 UTF-8；规格里出现枚举外类型；边指向不存在的实体 | 入口非零退出**或** `exit 3/failed`；schema 门阻断；丢边必须留痕 |
| **模板** | 删/损坏 `assets/palettes.json`、`assets/mechanism-spec.schema.json`；删人工核对清单与结果模板 | 能回退的静默回退**但要留痕**；不能回退的降级为 warn 并写 `uncertainty` |
| **依赖** | `matplotlib` 不可导入 / 能导入但 `pyplot` 抛错；`Pillow` 缺失；`--formats svg`（不要预览） | `exit 2/partial`、`gates.g5_png=false`、`previews=[]`，原因写 `export_checks` + `uncertainty`；**绝不伪造预览** |
| **契约** | `output_contract` 四种声明形态 + 声明值为 `null`；往产物塞顶层 `null`；指向不存在的 `result.json` | 四形态按 `""`/`[]`/`false`/`0`·`{}` 回显且**顶层无 null**；`check_contract.py` 必须 `exit 1` 并报 C04/C01 |

**判定"静默失败"的口径**（本包的定义，避免自欺）：
`exit 0` **且** `status=success` **且** `uncertainty` / `reason` / `self_check.warnings` / `self_check.failures`
**四个留痕位点全空** ⇒ 判为静默失败。演练**开跑前**实测到 3 处，修复后复跑为 0 处（见 §4.2）。

### 4.1 当前台账（复跑命令见上）

```text
SUMMARY {"scenarios": 24, "expect_ok": 24, "mismatch": [],
         "silent_failures": [], "recovery": "6/6"}
```

### 4.2 演练发现并修掉的三处静默失败（本包最重要的实证）

| # | 故障 | 修复前实测 | 根因位置 | 修复（纯增量） | 修复后实测 |
|---|---|---|---|---|---|
| **G1** | 边指向不存在的实体 id | `exit 0 / success / gates 8/8 / uncertainty 0` —— **图面少一条边，毫无记录** | `model.py: normalize_edges()` 直接 `continue` | 新增 `dropped_edges(raw)` 探针 + `main.py` 写 `uncertainty`（+56/−0、+30/−0 行） | `uncertainty=1`，`reason` 精确到 `第 1 条边 e2→e999：端点 id 不在实体清单中` |
| **G2** | 删掉/弄坏 `assets/palettes.json` | `exit 0 / success / 零留痕` —— 文档承诺的"记 uncertainty"并未发生 | `model.py: _load_palettes()` 的 `except Exception: return {}` | 新增 `palette_load_status()` 探针 + `main.py` 写 `uncertainty` | `uncertainty=1`，区分 `FileNotFoundError`/`JSONDecodeError`；资产健康时**不产生噪音** |
| **G3** | `case.json` 无 `task` 且无 `task.md` | CP1.2 判 `warn`，但成功路径把 warn 丢掉 ⇒ 零留痕 | `main.py` CP1 段只检查 `fail` | 新增一段把 `cp1` 中所有 `warn` 写进 `uncertainty` | `uncertainty=1`：`CP1 前置检查降级：task 说明可用` |

> **修改性质**：上述三处只改 2 个文件，且**全部为纯增量**（`model.py 381→437`、`main.py 482→512`，
> 删除行数为 0）；**CLI 参数名/默认值/退出码语义一字未动**。
> 其余 9 个脚本与 `assets/`、`templates/` 逐字节未改。逐条点名见 `FAULT-MATRIX.md` §4.1。

## 5. 终态与退出码（三元组必须自洽）

| 终态 | `status` | `main.py` 退出码 | `check_contract.py` | `gates` | 触发条件 |
|---|---|---|---|---|---|
| 成功 | `success` | **0** | **0** | 8/8 | 阻断检查全过 **且** `extraction.verified_by_agent=true` |
| 降级 | `partial` | **2** | 0 或 1 | 允许 7/8 | 有 fail/warn、草稿未核验、或显式只要部分格式（如 `--formats svg`） |
| 阻断 | `failed` | **3** | 1 | `{}` | 材料不可解析、SVG 产不出、或 CP2 schema 门不过 |
| 入口拒绝 | —（不写 `result.json`） | **1** | 1 | — | `case.json` 路径不存在或不是合法 JSON（实测 `in-01`/`in-03`） |

**不自洽时以退出码为真**重算 `status`，取更保守档，并把理由写进 `uncertainty`。

## 6. 决策规则（R1–R10：出故障时先查这张表）

| # | 触发信号 | 动作 | 记录位点 |
|---|---|---|---|
| R1 | `case.json` 找不到 / 不是合法 JSON | 直接补齐输入再跑；**不要**用空模型绕过 CP1 | 入口 stderr（不入信封，属已知粗糙点） |
| R2 | 材料目录为空 / 材料不可读 | 用 `--materials-dir` 显式给目录；仍无材料则接受 `failed` 并给补救路径 | `status/reason/uncertainty` |
| R3 | 规格出现枚举外 `type`/`edge.type` | **改规格，不改图**；schema 门就是为此存在 | `status/reason`（exit 3） |
| R4 | 材料只有实体、没有关系 | 允许"只有实体"的图，但必须 `partial` + 说明边清单为空 | `uncertainty`、`counts.edges` |
| R5 | 规格里有点不到实体的边 | **核对端点 id**；丢弃会被记进 `uncertainty`（G1），不要装作没发生 | `uncertainty`（边被丢弃） |
| R6 | 资产缺失（调色板/schema/模板） | 调色板→内置默认色；schema→S01 warn；核对清单→本文档 §7 清单代替；**都要留痕** | `uncertainty`、`self_check` |
| R7 | `matplotlib`/`Pillow` 不可用或渲染抛错 | 只交付可编辑 SVG：`partial` + exit 2 + `g5_png=false` + `previews=[]`；**绝不伪造预览** | `export_checks` + `uncertainty` |
| R8 | 只请求了部分格式 | 未请求 ≠ 失败：`partial` + 空数组 + 说明；已请求的必须真产出 | `deliverables`、`uncertainty` |
| R9 | 契约字段无值 | 先判形态再填：标量 `""`／列表 `[]`／布尔 `false`／数值·字典 `0`·`{}`；**顶层禁 null** | `result.json` 顶层 |
| R10 | 三元组（status/退出码/gates）不一致 | 以退出码为真，取更保守档，写 `uncertainty`；**不得**谎报 success | `uncertainty` |

## 7. 交付前自查清单（逐条打勾，任一条打不上就不报 success）

- [ ] 我实际读了 `case.json` / `task.md` / 全部材料，没有按文件名猜内容；
- [ ] 实体/边/图例项与材料一一对应，每条都有 `source`（文件:行）；没有点不到实体的边（或已在 `uncertainty` 里交代）；
- [ ] 基因/蛋白/复合物/RNA/小分子没有混用；区室归属与材料一致；
- [ ] 每个箭头语义 = 图例声明；虚线只出现在弱证据/不确定处；
- [ ] 数据映射（颜色/线宽/大小）与图例、图面三方一致，数值可溯源；
- [ ] SVG 7 层齐全且良构；PNG/PDF 或**明确记录**缺失原因（R7）；
- [ ] `result.json` 契约字段齐全（含 `output_contract` 四形态回显），**顶层无 null**；`check_contract.py` exit 0；
- [ ] `topology.json` / `legend_audit.json` 已产出；`uncertainty` / `change_records` 诚实；
- [ ] `status` 与退出码、`gates` 三元组自洽（R10）；`failed` 路径没有冒充完整交付；
- [ ] **故障面**：本包相关场景在 `references/FAULT-MATRIX.md` 中的行为与本次运行一致（改了脚本就重跑演练）。

## 8. 反预制答案规则

`examples/` 里的一切都是**演示示例（非正式案例）**，图内与 `result.json` 均带示例标记；
正式运行**禁止**把示例的实体/边/数值抄进正式输出。
`assets/result.template.json` 只是结构模板，不得冒充运行产物；**不给自己编造任何评分数字**。

## 9. 限制与维护

- 图件不在包内：每次运行由脚本在 `--out` 现场生成；SVG/PNG/model/topology/legend_audit 为确定性产物，
  `result.json` 与 PDF 含时间戳，**不作确定性承诺**。
- 自动抽取只处理结构化语句；散文/PDF 走 CP2b 人工抽取（"准确率优先于全自动"的刻意设计）。
- **改动流程**：改色 → `assets/palettes.json`；改契约/门 → `references/OUTPUT_CONTRACT.md` +
  `check_contract.py` + `result_writer.py` 三处同步；改校验规则 → `topology.py`/`legend_audit.py`/`validate_figure.py`。
  **任何脚本改动后必须重跑 `fault_inject.py`**，并把新台账写回 `references/FAULT-MATRIX.md` 与 `TEST.md`。
- **明令禁止**：向包内添加二进制资源、`__pycache__`、或预置图件。

## 10. 文件索引（相对 `$SKILL_DIR`）

| 文件 | 作用 |
|---|---|
| `references/FAULT-MATRIX.md` | **本版核心新增**：24 场景四形态实测矩阵 + 恢复演练 + 三处静默失败的修复前后对比 + 边界 |
| `scripts/fault_inject.py` | **本版核心新增**：失败注入器（`--skill/--out/--family/--only/--json/--md/--keep`，退出码 0/1/4） |
| `references/OUTPUT_CONTRACT.md` | 字段契约 + 四形态回显 + G1–G8 硬性门 + §10 状态一致性 × 故障实测 |
| `references/failure-modes.md` | F01–F26 失败模式表（与本文档 §6 规则、`FAULT-MATRIX.md` 场景交叉索引） |
| `references/RUBRIC_MAP.md` | 五维评分（40/25/15/10/10）逐条落点（可靠体验按故障矩阵逐格落点） |
| `references/mechanism-spec.md` / `legend-encoding.md` | 规格结构、命名与区室规范；箭头语义与数据编码 |
| `assets/` `templates/` `examples/` | schema/调色板/结果模板；人工核对清单；最小可运行示例（含实跑 JSON 产物） |
| `scripts/{extract,model,layout,pathway_svg,mpl_backend,topology,legend_audit,validate_figure,check_contract,result_writer}.py` | 抽取/规格/布局/渲染/审计/契约/写盘 |
| `README.md` / `TEST.md` / `worklog.md` / `COMPARE.md` | 依赖与用法 / 自测与实测（含 T11 故障演练记录）/ 构建日志 / 与基础 Agent 的对照方案 |
