---
name: scientific-schematic-editor
description: >-
  Generate and edit editable scientific schematics, mechanism/relationship
  diagrams, flow diagrams and data charts from source materials, and check how
  far that ability generalises: a bundled case-set spans two genres
  (cell-biology mechanism schematic, transcriptomics heatmap chart) and
  scripts/case_probe.py re-runs every case plus a set of deliberately
  out-of-range probes, comparing the measured output against each case's
  declared acceptable range and recording where generalisation actually
  breaks. Extracts an entity-relation manifest (traceable to sources), draws a
  layered editable SVG source plus PNG/PDF exports, runs CP1 plan-lint and
  export-compliance checks, and writes a result.json carrying every
  output_contract field. Use when a task asks to draw, regenerate or edit a
  scientific figure from papers, tables or notes: 科研示意图/机制图/信号通路图/
  流程图/实验装置图/图表的生成与编辑.
  Execute in order: read the contract → read the real files → extract ER →
  lint the plan (CP1) → draw → check (CP2) → edit and re-check (CP4) →
  contract gate (CP3) → determinism (CP5) → run the case-set.
---

# scientific-schematic-editor — 科研示意图生成与编辑（多案例泛化与题集版）

本技能除了"把材料画成可编辑图稿"，还回答第二个问题：
**这套能力换一个题材、换一种图型、把规模放大之后，还成立吗？**

答案不是形容词，而是 `scripts/case_probe.py`：一个可运行的题集执行器。
它对每个案例真跑一次，把产物量化成数字，再逐条对照该案例**声明的可接受
区间**（实体/关系/分组计数、fail/warn 上限、必备产物角色、溯源覆盖率、
SVG 是否良构 XML、画布是否溢出…）；另外跑一组**故意越界**的探针，
看它究竟在哪一步、以什么退出码失效。逐案实测结果与**失效边界**写在
`references/CASE-SET.md`。

> 与决策系统版（v1）的关系：v1 把边界情况写成 D 规则、把"画布溢出"写成
> 一句话；本版**把那句话量出来**——实测发现"显式声明 `style.canvas` 时布局
> 不再自动扩展，超出部分会被 viewBox 裁掉且不报 warn"，并据此给出
> **画布预算公式**（§5），同时把包内示例与新案例的声明画布修到能容下自己的
> 内容。规则表、降级档位、检查名索引仍以 v1/`references` 为准。

## 1. 这套技能交付什么

| 交付面 | 内容 | 权威文件 |
|-|-|-|
| 能出图的链路 | 材料 → 实体关系清单 → CP1 生成前门 → 分层可编辑 SVG → PNG/PDF → `result.json` | §6、`scripts/main.py` |
| **题集（5 案 2 题材）** | 3 个包内示例 + 2 个新合成案例（细胞生物学机制图 / 转录组热图），每案带输入、期望产出结构、可接受区间、难度层 | `examples/cases/`、`references/CASE-SET.md` |
| **泛化边界（实测）** | 5 条故意越界探针 + 量出来的数字（哪一步失效、以什么退出码） | `scripts/case_probe.py`、`references/CASE-SET.md` §4 |
| 契约 | `result.json` 字段、G1–G8 硬门、四形态回显 | `references/OUTPUT_CONTRACT.md`（字段块逐字不变） |
| 评审判据 | 五维（40/25/15/10/10）逐条 → 本包哪个文件/机制 | `references/RUBRIC_MAP.md` |
| 失败的权威描述 | 题面 12 类失败形态 → 检测 → 处置 | `references/failure-modes.md` |

**本技能不做**：统计方法的数值计算、海报/封面版式、艺术插画美化、论文正文
写作。数据表里的数值是**事实输入**：不改算、不补造、不换算单位。

## 2. 题集：两题材五案例

| 案例 id | 题材 / 图型 | 难度层 | 输入 | 期望产出结构 |
|-|-|-|-|-|
| `example-schematic-001` | 信号通路机制图（schematic） | 入门 | `examples/case.json` + `sources/figure03-note.md` | 6 实体 / 5 关系 / 3 分组 / 3 图例项；SVG+PNG+PDF+`result.json` |
| `example-chart-002` | 数据表驱动柱状图（chart） | 入门 | `examples/case_chart.json` + `sources/data-table.csv` | 4 类别；图例与颜色由同一张表生成；单位上轴 |
| `example-edit-003` | 源文件级增量编辑（edit） | 入门 | `examples/case_edit.json` + 上一步的 `figure.svg` | 3 条 `change_records`；未改动元素保持原样 |
| `synth-mitophagy-101` | **细胞生物学：线粒体自噬清除通路**（schematic） | 中 | `examples/cases/case_mitophagy.json` + `cases/sources/mitophagy-note.md` | 6 实体 / 5 关系 / 3 模块；含材料自带的反误读（PINK1 是激酶不是底物） |
| `synth-expression-heatmap-102` | **转录组：三条件 × 三重复表达矩阵**（chart/heatmap） | 中高 | `examples/cases/case_expr_heatmap.json` + `cases/sources/expression-table.csv` | 3 类别 × 3 重复矩阵 + 行/列标签 + 色标单位；与柱状图完全不同的渲染路径 |

**可接受区间不是"越像越好"**，而是每案显式声明的六类判据（`case_probe.py`
逐条比对并在报告里写出"期望值 / 实测值 / 是否满足"）：

1. `exit` 与 `status`（成功案例必须 `0` / `success`）；
2. `fail_count` / `warn_count` 上限（成功案例为 0 / 0）；
3. 结构计数：`entity_count` / `relation_count` / `group_count` / `category_count`；
4. 必备产物角色集合（`figure` + `preview` + `pdf`，缺一即违约）；
5. `traceability_entities ≥ 100%`（每条实体都能回到材料出处）；
6. 形态类：SVG 是否良构 XML、原始标记是否泄漏、画布是否溢出、
   单位是否声明。

逐案实测（2026-11-22，本机 Python 3.13.9）见 `references/CASE-SET.md` §3；
**结论是 10/10 条落在声明区间内**（5 案 + 5 探针）。

## 3. 怎么跑题集

```bash
SKILL_DIR="$(cd "$(dirname "<本 SKILL.md 的实际路径>")" && pwd)"

# 全部 10 项（5 案 + 5 边界探针），产物落在包外，退出码 0 = 全部落在区间内
python "$SKILL_DIR/scripts/case_probe.py" --skill-root "$SKILL_DIR" --out /tmp/sse-cases

# 只跑某一组：bundled（包内三示例）/ new（两个新合成案例）/ probe（边界探针）
python "$SKILL_DIR/scripts/case_probe.py" --skill-root "$SKILL_DIR" --out /tmp/c --group new

# 只跑某几项 / 只看题集清单
python "$SKILL_DIR/scripts/case_probe.py" --skill-root "$SKILL_DIR" --out /tmp/c \
    --only synth-mitophagy-101,synth-expression-heatmap-102
python "$SKILL_DIR/scripts/case_probe.py" --list
```

退出码：`0` = 每案都落在声明区间内、每个探针都复现了它声明的失效形态；
`1` = 至少一条偏离（报告里给出期望/实测差值）；`2` = 参数错误。
产物：`<out>/case-report.json`（逐案全字段：命令、退出码、耗时、
`observed`、`expectations[]`、`conforms`、`deviations[]`）。

**只读技能包**：案例输入从包里读，夹具与产物一律写 `--out`；
`--out` 指向包内会被直接拒绝。

## 4. 泛化到哪会失效（实测，不是免责声明）

| # | 边界 | 实测结果 | 结论 |
|-|-|-|-|
| **G1** | 声明了不支持的 `chart_type`（`histogram`） | `exit 1` / `status=failed` / `fails=[pipeline]` / **无产物** | 图型白名单是 `bar/line/scatter/heatmap`；**不会**悄悄退化成别的图型（好事），但也没有产物可用 |
| **G2** | 长链（18 节点单链）+ **显式** `style.canvas: 1500×900` | `exit 0` / `success` / **0 fail 0 warn**，而内容宽 **6530 px**、viewBox 仍是 1500 ⇒ **被裁掉** | 显式画布**不会**自动扩展，且**没有任何 warn 提示溢出** ⇒ 必须按 §5 的预算公式自己算 |
| **G3** | 同样 18 节点单链，**不声明** canvas | `exit 0` / 自动画布 **6609×500**、无溢出；PNG 变成 **19827×1500 px** | 不声明画布 = 安全但代价大（文件尺寸/渲染时间） |
| **G4** | 实体名含 `& < > " µ × ²` | `exit 0` / `success`，SVG **良构 XML**（lxml 校验通过），原始标记不泄漏 | 文本转义正确；CJK/符号依赖系统字体（`font.cjk` 报事实） |
| **G5** | `containment` 关系没落到任何分组框 | `exit 1` / `status=partial` / `fails=[spec_lint.spec.containment_group]` | 结构错误在**生成前**就被拦下，且产物仍落盘可复查 |
| **G6** | 结构合法但**语义**错误（关系方向对调） | **无法用结构门发现** | 见 v4 的注入矩阵 D09b；必须靠"逐条回材料核对 from/to"的人工门 |

> 这张表的意义：**G1/G5 是"拦得住"，G2 是"拦不住但可计算"，G6 是"根本拦不住"**。
> 三类分开写，才知道该在哪里加人工门。

## 5. 画布预算规则（由 G2/G3 实测反推，按公式算就不会被裁）

层状布局（layered，左→右）实测的坐标公式（见 `scripts/layout.py`）：
节点 `x = 层号 × (240 + 130)`，节点高 90、行距 70。所以：

```
canvas.width  ≥ 370 × (最大层号) + 单个节点最大宽度 + 余量(建议 ≥ 40)
canvas.height ≥ 行数 × (90 + 70) + 图例/脚注高度(建议 ≥ 200)
```

- **一条 N 节点的链会把每个节点放进独立层**（因为分层按拓扑深度），
  所以 N 节点链需要的宽度约 `370×(N−1) + 240 + 余量`：6 节点 ≈ 2090、18 节点 ≈ 6530；
- 本包的 `examples/case.json` 与新案例 `synth-mitophagy-101` 原先都声明
  `width: 1500`（内容 2090）⇒ **被裁**。本轮已按公式改成 `2300`，
  并在 `case_probe.py` 里加了 `canvas_overflow: False` 这条**常驻判据**，
  以后改夹具若再把画布算小，题集会直接报偏离；
- 不想算就把 `style.canvas` 整个省掉：布局自动扩到内容尺寸（G3），
  代价是导出件尺寸不可控。

## 6. 执行顺序（S0–S7，含检查点）

**读契约 → 读材料 → 抽取 → 写清单 → CP1 → 绘图 → CP2 →（编辑则 CP4）→
CP3 → CP5 → 跑题集。**

| 步 | 动作 | 检查点 / 产物 |
|-|-|-|
| **S0** | 读 `/input/task.md` 与 `/input/case.json`，记 `case_id`；解析 `output_contract` 的键与**四形态**（string→`""`、array→`[]`、object→`{}`、number/boolean→`0`/`false`，禁 `null`）；确认 `/app/output`、`/app/work` | 契约快照 |
| **S1** | 逐份读 `case.sources` 指向的**真实文件**（相对 case.json 所在目录解析）；PDF 先过 `pdftext.py`；读不到的写进 `uncertainty` | 材料清单 + 缺失清单 |
| **S2** | `extract.py` 产候选草稿（带 `_draft`），Agent 复核后写 `/app/work/entities.json`：`name` 逐字来自材料、`kind` 映射到 7 类规范词表、包含关系落到 `groups` | 清单 |
| **S3** | **CP1 lint 门**：`spec_lint.py --manifest …`，只有 `{"valid": true}` 才继续 | CP1 通过/失败明细 |
| **S4** | 绘图：`main.py --case … --manifest … --work … --out …`；**绘图前先按 §5 核一次画布预算** | SVG/PNG/PDF + `result.json` |
| **S5** | **CP2 产物检查**：溯源比例、图例双向、数据映射、导出预检（DPI/色彩/`<text>`/PDF/字体） | `verification.checks` |
| **S6** | （编辑）`--edit-svg` 源文件级增量修改；编辑请求写在 `edit_requests`；改完重跑 CP2 + CP3 | `change_records` |
| **S7** | 契约门 `validate_result.py`（G1–G8）→ VALID；确定性双跑；**跑题集** `case_probe.py` | 契约判定 + 题集报告 |

命令行（自定位，任意 cwd 可跑）：

```bash
python "$SKILL_DIR/scripts/extract.py" --inputs /app/work/pdftext/<stem>.txt \
    --out /app/work/draft-entities.json
python "$SKILL_DIR/scripts/spec_lint.py" --manifest /app/work/entities.json
python "$SKILL_DIR/scripts/main.py" --case /input/case.json \
    --manifest /app/work/entities.json --work /app/work --out /app/output
python "$SKILL_DIR/scripts/validate_result.py" \
    --case /input/case.json --result /app/output/result.json
```

## 7. 资源文件说明（路径相对技能根，调用一律 `"$SKILL_DIR/..."`）

| 入口 | 角色 | CLI |
|-|-|-|
| `scripts/main.py` | 流水线入口 | `--case --manifest --out --work --edit-svg --base-name --exports --dpi --skip-checks --lint --no-lint --fixed-time --doc-check` |
| `scripts/case_probe.py` | **本版新增**：题集执行器（逐案真跑 + 对期望 + 边界探针） | `--skill-root --out --group --only --list --json --quiet --keep` |
| `scripts/extract.py` | 材料 → 候选 ER 清单草稿 | `--inputs --out --base-dir` |
| `scripts/pdftext.py` | PDF 文本抽取（四段回退，backend 如实记录） | `--pdf --out` |
| `scripts/textfont.py` | 字体栈探测（CJK 可用性事实源） | `--list --probe` |
| `scripts/spec_lint.py` | CP1 生成前 lint | `--manifest --dict --json` |
| `scripts/manifest.py` | ER 清单加载/规范化 | `<manifest.json>` |
| `scripts/layout.py` | 布局引擎（**§5 的画布公式就在这里**） | — |
| `scripts/svgbuilder.py` / `scripts/render.py` / `scripts/checks.py` | 分层 SVG / 镜像渲染 / 产物检查 | — |
| `scripts/edit.py` | 源文件级增量编辑 | `<figure.svg> <edits.json>` |
| `scripts/validate_result.py` | 契约独立校验 G1–G8 | `--case --result --out --json` |
| `scripts/selftest.py` | 模块级自测（35 项） | — |
| `scripts/run_examples.py` | 一键复现包内三示例 | `--out --keep` |
| `scripts/report.py` | 结果装配（库模块） | — |
| `scripts/doccheck.py` | 文档承诺 ↔ 脚本事实 的只读对拍 | `--root --files --json` |
| `references/CASE-SET.md` | **本版新增**：题集（逐案输入/期望结构/可接受区间/难度层）+ 逐案实测 + **失效边界** + 画布预算规则 | — |
| `references/OUTPUT_CONTRACT.md` | `result.json` 契约 + G1–G8 + 四形态回显（**字段块逐字不变**） | — |
| `references/failure-modes.md` | 题面 12 类失败形态 → 检测机制 → 处置 | — |
| `references/CHECK-INDEX.md` | 全部检查名清单（级别 + 科学含义） | — |
| `references/EDIT-ACTION-SCHEMA.md` | 编辑动作 → 字段名 → 记录 的对照表与反模式 | — |
| `references/ER_MANIFEST.md` | 实体—关系清单规范（绘图唯一数据源） | — |
| `references/DRAWING_GRAMMAR.md` | 图形语法：关系语义 → 箭头/线型/颜色、方向判定、分组/层级 | — |
| `references/RUBRIC_MAP.md` | 五维评分 → 本包文件/机制逐条映射 | — |
| `assets/relation-dict.json` / `assets/checklist.json` | 连接规则字典 / CP1–CP5 自查清单（机器可读） | — |
| `examples/cases/*` | **本版新增**：两个不同题材的合成案例（含各自来源材料） | — |

## 8. 五维评分映射（完整表见 `references/RUBRIC_MAP.md`）

| 维度 | 分 | 本包机制（可跑的检查，不是自述） | 证据文件 |
|-|-|-|-|
| 实际效果 | 40 | 材料 → ER 清单 → CP1 → 可编辑 SVG → PNG/PDF → `result.json` 一条命令跑通；**两个新题材案例**（细胞生物学机制图 / 转录组热图）各留下真实产物与数字；10/10 项落在声明区间 | `scripts/main.py`、`scripts/case_probe.py`、`references/CASE-SET.md` |
| 使用增益 | 25 | 题集把"换题材要重学一遍"变成"改夹具 + 重跑 `case_probe.py`"：每案的可接受区间是**显式声明**的，偏离会被逐条打印；画布预算公式把最容易返工的一类错误（图被裁）前置到绘图之前 | `scripts/case_probe.py`、§5、`TEST.md` |
| 创新增益 | 15 | ①**可运行的题集执行器**（真跑 + 对区间 + 探边界三合一）②把"泛化边界"分成**拦得住 / 拦不住但可计算 / 根本拦不住**三类并各给实测数字 ③`observed` 里包含画布溢出这个**上游检查不产出**的量 ④由 G2 反推出可用的画布预算公式并回头修好自家夹具 | `scripts/case_probe.py`、`references/CASE-SET.md` §4/§5 |
| 可靠体验 | 10 | 案例输入只读、产物写包外、`--out` 越界拒绝；每案逐条比对并在报告里写出期望/实测差值；失效边界（含"结构门拦不住语义错"）公开 | `scripts/case_probe.py`、`references/CASE-SET.md`、`references/failure-modes.md` |
| 生态贡献 | 10 | 题集本身可复用：新案例只需在 registry 里加一条（输入 + 期望区间）；`case-report.json` 是机器可读的对照基线；连接规则字典、检查名索引、三示例与契约校验器可直接拿走 | `references/CASE-SET.md`、`assets/*`、`scripts/doccheck.py` |

## 9. 依赖与限制

- Python 3.9+（实测 3.13.9）；运行必需 **matplotlib / Pillow / numpy**；
  `case_probe.py` 的 XML 良构校验优先用 lxml，**缺 lxml 时自动用标准库
  `xml.etree` 兜底**（报告里记 `xml_backend`），因此没有额外硬依赖；
- PDF 抽取按 fitz → pypdf → PyPDF2 → **stdlib 回退**逐级降级；
- 无 cairosvg/svgwrite：PNG/PDF 是与 SVG 同源的 matplotlib 镜像
  （**语义一致、非逐像素**），该降级写进 `uncertainty`；
- **平台运行契约**：技能装在 `/skills/weekly-skill`；输入 `/input/case.json`
  + `/input/task.md`；中间产物 `/app/work`；最终产物 `/app/output`；
  预算 64 次模型请求 / 900 秒 / 16384 token per response；
- **资源形态（硬约束）**：包内只放 UTF-8 文本
  （`.md/.py/.json/.txt/.csv/.yaml/.yml`），≤50 个文件、单文件 ≤500KB、
  合计 ≤2MB、无符号链接；图稿与渲染件一律运行时生成；
- **已知限制（如实标注）**：
  - 题集只覆盖**两个**新题材；`references/CASE-SET.md` §4 的 G1–G6 就是
    当前测到的失效边界，**没有被测过的题材不声称支持**；
  - 图型白名单固定为 `bar/line/scatter/heatmap`（G1）；长链+显式小画布会被
    静默裁掉（G2，可用 §5 公式规避）；关系方向这类**语义**错误结构门
    拦不住（G6）；
  - 预览为同源镜像非逐像素；PDF 字体嵌入审计为尽力而为；CJK 依系统字体；
  - `extract.py` 只产草稿；**`edits` 与 `edit_requests` 两个字段都生效**
    （`edits` 优先；本轮实测更正了旧文档的反向说法），真正的坑是字段名写错
    （`target`/`value`）⇒ 必须对拍「请求条数 vs `change_records` 条数」。

## 10. 自查清单（提交前逐行确认；机器版 `assets/checklist.json`）

- [ ] 实体名逐字出自材料，无材料外基因/浓度/时间点/单位；
- [ ] 每个关系方向与材料一致（激活≠抑制、上下游不颠倒、包含用分组）；
- [ ] CP1 `{"valid": true}`：kind 可映射、containment 用分组、图例双向、
      调色板 ≥ 类别数；
- [ ] 数值/坐标/单位与数据表逐项一致，**绝不换算单位**，改数据后图确实重绘；
- [ ] `figure.svg`：文字可选（`<text>`）、图层可拆、带 `id` 与 `data-*`、
      内嵌 ER 清单、**良构 XML**；
- [ ] 导出件：PDF 可打开；PNG 有效 DPI 达标；色彩 RGB 族；
- [ ] **画布预算核过**（§5）：`canvas_overflow` 为 False，图没有被 viewBox 裁掉；
- [ ] `result.json` 含全部契约键 + `case_id`，四形态回显无 `null`；
- [ ] `validate_result.py`（G1–G8）输出 VALID，退出码 0；
- [ ] 编辑任务：请求条数 == `change_records` 条数，未改动元素保持原样；
- [ ] **题集跑过**：`case_probe.py` 退出码 0（10/10 落在声明区间）；
- [ ] §4 的失效边界里与本次案例相关的行（尤其 G2 画布、G6 方向）已人工核过；
- [ ] 形态：仅 7 种文本扩展名、无 `__pycache__`、≤50 文件、≤500KB/文件、
      ≤2MB、包内无本机绝对路径。

## 11. 禁止事项

- 不提交预制答案/正式案例输出；示例与新案例都只用于演示接口与流程，
  **产物不入包**，也不得当作正式案例答案；
- 不编造缺失的软件状态或科学数据（来源里没有的实体/数值一律不画）；
- **不声称没测过的泛化能力**：题集外的题材/图型必须按"未测量"处理；
  声明的可接受区间一旦被实测突破，先修夹具或改区间，**不许悄悄放宽**；
- 不为"好看"改关系颜色（改色 = 图例不一致）。
