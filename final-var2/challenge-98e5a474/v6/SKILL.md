---
name: scientific-schematic-editor
description: >-
  Generate and edit editable scientific schematics, mechanism/relationship
  diagrams, flow diagrams and data charts from source materials, and prove the
  pipeline holds up: a runnable four-form fault harness
  (scripts/fault_inject.py, 25 injections over input/template/dependency/
  contract) records the real exit code, status and uncertainty of every way it
  can break, and a runnable case-set runner (scripts/case_probe.py) re-runs five
  cases across two genres plus five deliberately out-of-range probes against
  each case's declared acceptable range. Extracts an entity-relation manifest
  (traceable to sources), draws a layered editable SVG source plus PNG/PDF
  exports, runs CP1 plan-lint and export-compliance checks, and writes a
  result.json carrying every output_contract field. Use when a task asks to
  draw, regenerate or edit a scientific figure from papers, tables or notes:
  科研示意图/机制图/信号通路图/流程图/实验装置图/图表的生成与编辑.
  Order: read the contract → read the real files → extract ER → lint the plan
  (CP1) → draw → check (CP2) → edit and re-check (CP4) → contract gate (CP3) →
  determinism (CP5) → fault drill → case-set.
---

# scientific-schematic-editor — 科研示意图生成与编辑（全维合并最强版）

本包把五条强化轴**合并**到同一套脚本与文档上，按
**输入 → 执行 → 失败 → 增益 → 机制 → 复用** 六段组织。
每一段都指到一份可跑的脚本或一份带实测数字的 reference，**没有一段靠形容词**。

| 段 | 一句话 | 权威文件 |
|-|-|-|
| **① 输入** | 平台给什么、以什么为准、什么算缺 | §1 |
| **② 执行** | S0–S7 + 检查点 CP1–CP5，一条命令跑通 | §2、`scripts/main.py` |
| **③ 失败** | 四形态 × 25 条真实注入；六条拦不住的盲区逐条公开 | §3、`references/FAULT-MATRIX.md`、`references/failure-modes.md` |
| **④ 增益** | 对照协议 F1–F8 + 指标 I1–I10 + 真实读数 + 明确写出的"未测量" | §4、`references/GAIN-PROTOCOL.md` |
| **⑤ 机制** | 五个具名机制 M1–M5，各带"没有它会怎样"与可证伪判据 | §5、`references/MECHANISM.md` |
| **⑥ 复用** | 12 项可复用资产 A1–A12 + 5 级采纳阶梯 + 题集（5 案 2 题材） | §6、`references/REUSABLE-ASSETS.md`、`references/CASE-SET.md` |

**本技能不做**：统计方法的数值计算与选择、海报/封面版式、艺术插画美化、
论文正文写作。数据表里的数值是**事实输入**：不改算、不补造、不换算单位。

---

## ① 输入：平台给什么、以什么为准

| 路径 | 内容 | 读法 |
|-|-|-|
| `/input/case.json` | `case_id` / `workorder` / `figure_type` / `sources` / 可选 `manifest`、`entities+relations`、`data`、`edits`、`edit_requests`、`output_contract` | **以文件实际内容为准，不凭字段名猜语义** |
| `/input/task.md` | 任务书 | 与 case 冲突时以任务书 + 材料原文为准 |
| `/input/` 下的材料 | 可能是 PDF | 先过 `scripts/pdftext.py`（加密件会被**明确拒绝**，不出空文本） |

**输出（`/app/output`，全部运行时现场生成）**

```
/app/output/
├── figure.svg      # 可编辑分层源文件：文字是 <text>、layer-* 分组、data-* 溯源、内嵌 ER 清单
├── figure.png      # 渲染预览（matplotlib 镜像同一 layout+manifest）
├── figure.pdf      # 矢量导出件
├── result.json     # 结构化结果（OUTPUT_CONTRACT 全字段 + case_id）
└── work/           #（或 /app/work）entities.json / layout.json / manifest.validated.json
```

> **包内不预置任何图稿或渲染件**：PDF/PNG/SVG/TIFF 一律运行时生成；
> 示例期望产物写在 `examples/EXPECTED-OUTPUT.md`，一键复现用 `scripts/run_examples.py`。

**输入层的三件事必须先做**（做错了后面全错，而且结构门救不回来）：

1. 解析 `output_contract` 声明的键与类型 —— 四形态回显：string→`""`、
   array→`[]`、object→`{}`、number/boolean→`0`/`false`，**禁 `null`**；
2. 逐份读 `case.sources` 指向的**真实文件**，读不到的**写进 `uncertainty`**
   （实测：材料内容不可读时 pipeline 自身没有痕迹，只有这一步能发现，见 §3 盲区 A1）；
3. 核**画布预算**：`style.canvas` 一旦显式声明，布局**不再自动扩展**，
   超出部分会被 `viewBox` 裁掉且不报 warn（实测 G2）。按
   `width ≥ 370 × 最大层号 + 节点宽 + 40` 算，或干脆不声明（代价是导出件很大）。

---

## ② 执行：S0–S7 与五个检查点

**读契约 → 读材料 → 抽取 → 写清单 → CP1 → 绘图 → CP2 →（编辑则 CP4）→
CP3 → CP5 → 故障演练 → 题集。**

| 步 | 动作 | 检查点 | 失败形态 |
|-|-|-|-|
| **S0** | 读 `/input/task.md` 与 `/input/case.json`；记 `case_id`；解析 `output_contract` 四形态；确认 `/app/output`、`/app/work` | — | case 不可解析 ⇒ `exit 2` + `FATAL`，**不写半成品** |
| **S1** | 逐份读真实材料；PDF 先过 `pdftext.py`；读不到的记 `uncertainty` | — | 加密件 `exit 2`；扫描件 `chars: 0`；缺库走 stdlib 回退 |
| **S2** | `extract.py` 产候选草稿（`_draft`）；Agent 复核后写 `entities.json`：`name` 逐字来自材料、`kind` 映射到 7 类规范词表、包含关系落到 `groups` | — | 草稿进 CP1 会被判 INVALID —— 这正是"草稿不是答案"的门 |
| **S3** | `spec_lint.py --manifest …` | **CP1** | 结构错 ⇒ `exit 1` + `partial` + `spec_lint.spec.*` fail |
| **S4** | `main.py --case … --manifest … --work … --out …`；绘图前再核一次画布预算 | — | 依赖缺失 ⇒ `exit 1` + `failed` 的 result.json |
| **S5** | 溯源比例、图例双向、数据映射、导出预检（DPI/色彩/`<text>`/PDF/字体） | **CP2** | 字体缺失 ⇒ `font.cjk` warn + `uncertainty` |
| **S6** | `--edit-svg` 源文件级增量修改；请求写在 `edit_requests`；改完重跑 CP2 + CP3 | **CP4** | 字段名错 ⇒ 日志 `[edit] fail`，条数对不上 |
| **S7** | `validate_result.py`（G1–G8）→ VALID；`--fixed-time` 双跑比对 | **CP3 / CP5** | 契约形状错 ⇒ 独立校验器 INVALID |

```bash
SKILL_DIR="$(cd "$(dirname "<本 SKILL.md 的实际路径>")" && pwd)"

python "$SKILL_DIR/scripts/extract.py" --inputs /app/work/pdftext/<stem>.txt \
    --out /app/work/draft-entities.json
python "$SKILL_DIR/scripts/spec_lint.py" --manifest /app/work/entities.json
python "$SKILL_DIR/scripts/main.py" --case /input/case.json \
    --manifest /app/work/entities.json --work /app/work --out /app/output
python "$SKILL_DIR/scripts/validate_result.py" \
    --case /input/case.json --result /app/output/result.json
```

**退出码语义（与 `status` 同向，不得含糊）**

| 退出码 | 含义 | result.json | 重试语义 |
|-|-|-|-|
| `0` | `status=success`；允许存在已被 `acknowledged_issues` 核可的 warn | 写出，`fail_count==0` | 无需重试 |
| `1` | `status=partial`（有 fail 明细）或 `status=failed`（流水线异常） | **一定写出** | 按 fail 明细定向修复后重跑 |
| `2` | 致命：case 无法定位/解析、编辑目标无内嵌清单、输入层不可用 | **不写出** | 先解决输入问题，重试无意义 |

---

## ③ 失败：四形态 25 条注入 + 六条已知盲区

**这一节的全部数字来自 `scripts/fault_inject.py` 的真实运行**（25 条，
2026-11-22 本机实测：**25/25 符合期望、0 条静默失败**）。逐行矩阵
（注入什么 → 期望 → 实测退出码/status/uncertainty → 是否静默）在
`references/FAULT-MATRIX.md` §3；题面 12 类失败形态 → 检测 → 处置 → 档位
（D 规则 / L0–L3）的权威描述在 `references/failure-modes.md`。

```bash
python "$SKILL_DIR/scripts/fault_inject.py" --skill-root "$SKILL_DIR" --out /tmp/sse-fault
python "$SKILL_DIR/scripts/fault_inject.py" --skill-root "$SKILL_DIR" --out /tmp/f --form dependency
python "$SKILL_DIR/scripts/fault_inject.py" --skill-root "$SKILL_DIR" --out /tmp/f --only D13,D18,D21
python "$SKILL_DIR/scripts/fault_inject.py" --list
```

**两条判据（整个矩阵按它们判"静默"）**

- **留痕律**：出了问题就必须留下机器可读痕迹 —— 非零退出码、`status`、
  `verification.checks.fails/warns`、`uncertainty` 至少命中一个。
  **四者全空 = 静默失败 = 本技能失效**；
- **出口一致律**：CLI 退出码与 `result.json.status` 必须同向；冲突时以
  `result.json` 为记录面、退出码为重试面，并把冲突本身写进 `uncertainty`。

**四形态与判定条目的对应**

| 形态 | 主要落在哪些判定条目上 | 档位 | 实测行 |
|-|-|-|-|
| 输入 damaged（case/材料本身） | 不可定位/不可解析、材料缺失或矛盾、PDF 不可抽取 | 停止（`exit 2`）/ 降级（继续 + `uncertainty`） | D01–D06 |
| 模板 damaged（清单/分组/图例/规则字典） | 无出处实体、kind 不可映射、containment 未分组、图例缺项/孤儿、调色板不足、表外类别 | 门降级（`partial`）/ 降级（warn） | D07–D14 |
| 依赖 damaged（运行环境） | CJK 缺失、渲染异常、无 PDF 库、缺运行库 | 降级（可回退）/ 停止（`failed` 记录） | D15–D21 |
| 契约 damaged（`output_contract`） | 键缺值、类型不符、自选跳过检查 | 降级（不改产物，由独立校验器判 INVALID） | D22–D24 |

**六条已知盲区（拦不住的，逐条公开）**

| # | 盲区 | 实测证据 | 缓解 |
|-|-|-|-|
| A1 | 材料**内容**不可读（存在但是二进制垃圾） | D02：`exit 0` / `success` / 0 fail / 0 warn | S1 的"逐份读实际文件"人工门；读不到必须写进 `uncertainty` |
| A2 | 关系**方向**对调（端点与 kind 都合法） | D09b：`exit 0` / `success`，`spec_lint` 全 ok | 逐条回材料核对 `from/to`；SVG 的 `data-relation`/`data-source` 可 grep；语义由 native/LLM Judge 承担 |
| A3 | 独立 `spec_lint.py` CLI 对**损坏的字典**仍会崩 | D13 的复核：`spec_lint exit=1`，`JSONDecodeError` | 该脚本逐字节未动（只在 `main.py` 侧兜）；属公开限制 |
| A4 | 缺 Pillow 与缺 matplotlib 不可分辨 | D18/D19 同为 `exit 1` / `failed` | `uncertainty` 写明缺失模块名 |
| A5 | `--skip-checks` / `--no-lint` 让"未检查"像"已通过" | 未注入（属自选降级） | §8 自查强制：交付前必须用默认参数完整重跑 |
| A6 | 加密 PDF 时主流程本身仍 `exit 0` | D15：主流程 `0/success`，`pdftext.py` `exit 2` | 硬性要求 PDF 必须先过 `pdftext.py` 并如实记录 |

**本节由注入发现并修掉的三个真实缺陷**（两个纯增量 + 一处文档更正；CLI 参数名/默认值/退出码
语义均未改，其余 13 个脚本逐字节未动）

| # | 缺陷 | 修复前实测 | 增量 | 修复后实测 |
|-|-|-|-|-|
| 1 | `relation-dict.json` 损坏 ⇒ `json.load` 异常冒泡 | `exit 1` + 裸 traceback，**无 result.json** | `main.py` 读字典处包 `try/except` + `summarize()` 后补一条 `spec_lint.corpus` warn（+18/−2 行） | `exit 0` / `success` / `warns=[spec_lint.corpus]` |
| 2 | 缺 matplotlib/Pillow ⇒ import 期直接崩 | `exit 1` + 裸 traceback，**无 result.json** | `import render`/`import checks` 各包 `try/except` + 依赖门调用既有 `_write_failed_result`（+27/−5 行） | `exit 1` / `failed` / `fails=[pipeline]` |
| 3 | `--edit-svg` 分支把 `edit_from_svg()` 返回的编辑问题**整个丢掉** | 错误字段名夹具：`exit 0` / `success` / `change_records=0`，**stdout 连 `[edit] …` 都没有** | `main.py` 该分支收集 `ed_issues`、一致地打印并写进 `result.json.uncertainty`（+8/−1 行） | 同一夹具 → `uncertainty` 出现 `edit issue: edit.relabel`；正常夹具仍 `change_records=3` |

---

## ④ 增益：对照协议 + 指标 + 真实读数 + 未测量清单

完整协议在 `references/GAIN-PROTOCOL.md`（条款 **F1–F8**、指标 **I1–I10**、
实测记录 **R1–R13**、记账模板）。三句话摘要：

- **F1–F8** 规定对照成立的前提：同输入、同画布与导出参数、同预算、
  同模型与版本、**同判据**（两臂用同一个 `validate_result.py`）、同夹具、
  失败也记录、**不可测就标注**；
- **I1–I10** 覆盖契约有效性、结构完整性、可编辑性、溯源比例、关系语义、
  图例一致率、数据映射、导出合规、返工轮次、端到端耗时 ——
  每一项都给了"取值来源（机器可读字段）"与"基线做法"；
- **最重要的是那张"能支撑 / 不能支撑"表**：本包**没有**跑过"不加载 Skill 的
  基线臂"，因此**不声称**"比基线得分更高"；R1–R13 是 CLI 空间测量，
  不含"人工修改量"这类需要对照臂的量。

> 与本节配合的证据：`TEST.md` 的 T1–T10（每条都写命令 + 实测输出）、
> `references/FAULT-MATRIX.md`（可靠性读数）、`references/CASE-SET.md`
> （跨题材读数）。**三者都不含平台分数**。

---

## ⑤ 机制：五个具名机制，各带"没有它会怎样"与可证伪判据

完整版（含依赖图与已知盲区）在 `references/MECHANISM.md`；这里是索引。

| 机制 | 一句话 | 落点 | 可证伪判据 |
|-|-|-|-|
| **M1 方案先行** | 画之前先过 CP1 lint：kind 必须可映射、containment 必须分组、图例双向、调色板覆盖类别数 | `scripts/spec_lint.py` | 坏清单必须 `spec_lint.valid=false` 且 `main.py` 降为 `partial`（实测 D08/D09/D11） |
| **M2 源文件自描述** | ER 清单**内嵌**进 SVG，源文件自带语义 | `scripts/svgbuilder.py`、`scripts/edit.py` | `svg.manifest_embedded`/`svg.manifest_matches` 为 ok；无内嵌清单的 `--edit-svg` 必须 `exit 2` |
| **M3 抽取四段回退** | PDF 文本按 fitz → pypdf → PyPDF2 → stdlib 逐级降级，backend 如实记录 | `scripts/pdftext.py` | 无第三方库仍能抽（实测 15 字）+ backend 记 stdlib；加密件必须 `exit 2`（实测 D15） |
| **M4 导出预检** | 导出前后查有效 DPI、色彩族、文字可选中、PDF 结构、字体 | `scripts/checks.py` | `bitmap.*`/`pdf.*`/`svg.editable_text`/`artifact.<role>` 都有读数 |
| **M5 单一字体事实源** | render / checks / result.json 三方共用同一个字体探针 | `scripts/textfont.py` | `textfont --probe` 与 `verification.render`、`font.cjk` 同源一致（实测 D20：无 CJK ⇒ `font.cjk` warn + uncertainty） |

---

## ⑥ 复用：12 项资产 + 采纳阶梯 + 题集

**可复用资产 A1–A12 与 5 级采纳阶梯**见 `references/REUSABLE-ASSETS.md`：
它把"能拿走的东西"（连接规则字典、CP 自查清单、ER 清单规范、图形语法、
契约校验器、文档对拍器、注入器、题集执行器…）逐项写清"拿走它能省什么、
最小采纳怎么验"，并列出复用时最容易踩的坑。

**题集（5 案 2 题材 + 5 条越界探针）**见 `references/CASE-SET.md`：

```bash
python "$SKILL_DIR/scripts/case_probe.py" --skill-root "$SKILL_DIR" --out /tmp/sse-cases
python "$SKILL_DIR/scripts/case_probe.py" --skill-root "$SKILL_DIR" --out /tmp/c --group new
python "$SKILL_DIR/scripts/case_probe.py" --list
```

| 案例 | 题材 / 图型 | 难度层 | 可接受区间（摘要） |
|-|-|-|-|
| `example-schematic-001` | 信号通路机制图 | 入门 | 6 实体 / 5 关系 / 3 分组；`exit 0`/`success`/fail 0/warn 0 |
| `example-chart-002` | 数据表驱动柱状图 | 入门 | 4 类别、单位非空、图例同源 |
| `example-edit-003` | 源文件级增量编辑 | 入门 | `change_records` 恰 3 条，未改动元素保持原样 |
| `synth-mitophagy-101` | **细胞生物学：线粒体自噬通路** | 中 | 6/5/3；含材料自带反误读 |
| `synth-expression-heatmap-102` | **转录组：表达矩阵热图** | 中高 | 3 类别 × 3 重复，单位进色标 |

实测 **10/10 项落在声明区间内**。**泛化边界**（§4 同表，详见 CASE-SET）：
图型白名单外会被拦下（G1）；长链 + 显式小画布会被**静默裁掉**（G2，
可用预算公式规避）；不声明画布则自动扩展但导出件巨大（G3）；特殊字符转义
正确（G4）；containment 未分组会被拦（G5）；**关系方向对调拦不住**（G6）。

---

## ⑦ 资源清单（路径相对技能根，调用一律 `"$SKILL_DIR/..."`）

| 入口 | 角色 | CLI |
|-|-|-|
| `scripts/main.py` | 流水线入口（含依赖门 + 字典兜底） | `--case --manifest --out --work --edit-svg --base-name --exports --dpi --skip-checks --lint --no-lint --fixed-time --doc-check` |
| `scripts/fault_inject.py` | 四形态故障注入与恢复演练（只动包外副本） | `--skill-root --out --form --only --json --quiet --keep --list` |
| `scripts/case_probe.py` | 题集执行器（逐案真跑 + 对区间 + 边界探针） | `--skill-root --out --group --only --list --json --quiet --keep` |
| `scripts/extract.py` | 材料 → 候选 ER 清单草稿 | `--inputs --out --base-dir` |
| `scripts/pdftext.py` | PDF 文本抽取（四段回退，backend 如实记录） | `--pdf --out` |
| `scripts/textfont.py` | 字体栈探测（CJK 可用性事实源） | `--list --probe` |
| `scripts/spec_lint.py` | CP1 生成前 lint | `--manifest --dict --json` |
| `scripts/manifest.py` | ER 清单加载/规范化 | `<manifest.json>` |
| `scripts/layout.py` | 布局引擎（画布公式在此） | — |
| `scripts/svgbuilder.py` / `scripts/render.py` / `scripts/checks.py` | 分层 SVG / 镜像渲染 / 产物检查 | — |
| `scripts/edit.py` | 源文件级增量编辑 | `<figure.svg> <edits.json>` |
| `scripts/validate_result.py` | 契约独立校验 G1–G8 | `--case --result --out --json` |
| `scripts/selftest.py` | 模块级自测（35 项） | — |
| `scripts/run_examples.py` | 一键复现包内三示例 | `--out --keep` |
| `scripts/report.py` | 结果装配（库模块） | — |
| `scripts/doccheck.py` | 文档承诺 ↔ 脚本事实 的只读对拍 | `--root --files --json` |

| 文档 / 资源 | 用途 |
|-|-|
| `references/OUTPUT_CONTRACT.md` | `result.json` 契约 + G1–G8 + 四形态回显 + **四个读数面**（字段块逐字不变） |
| `references/FAULT-MATRIX.md` | 25 行实测注入矩阵 + 六条盲区 + 三个缺陷的修复前后对照 |
| `references/CASE-SET.md` | 题集（逐案输入/期望/区间/难度）+ 逐案实测 + 六条泛化边界 + 画布预算公式 |
| `references/GAIN-PROTOCOL.md` | 对照协议 F1–F8 + 指标 I1–I10 + 实测 R1–R13 + 记账模板 + 未测量清单 |
| `references/MECHANISM.md` | M1–M5 完整机制说明（没有它会怎样 / 可证伪判据 / 已知盲区） |
| `references/REUSABLE-ASSETS.md` | 12 项可复用资产 + 5 级采纳阶梯 + 复用坑 |
| `references/failure-modes.md` | 题面 12 类失败形态 → 检测 → 处置 → 档位 → 恢复条件 |
| `references/CHECK-INDEX.md` | 全部检查名清单（三重身份：doccheck 事实源 / 机制判据来源 / 指标取值来源） |
| `references/EDIT-ACTION-SCHEMA.md` | 编辑动作 → 字段名 → 记录 的对照表、实测矩阵、反模式 |
| `references/ER_MANIFEST.md` | 实体—关系清单规范（绘图唯一数据源） |
| `references/DRAWING_GRAMMAR.md` | 图形语法：关系语义 → 箭头/线型/颜色、方向判定、分组/层级 |
| `references/RUBRIC_MAP.md` | 五维评分 → 本包文件/机制逐条映射（并标出由哪条轴的实测支撑） |
| `assets/relation-dict.json` / `assets/checklist.json` | 连接规则字典 / CP1–CP5 自查清单（机器可读） |
| `examples/*` | 包内三示例（schematic / chart / edit + 合成材料 + `EXPECTED-OUTPUT.md`） |
| `examples/cases/*` | 两个不同题材的合成案例（细胞生物学机制图 / 转录组热图）+ 各自来源材料 |

---

## ⑧ 自查清单（提交前逐行确认；机器版 `assets/checklist.json`）

- [ ] 实体名逐字出自材料，无材料外基因/浓度/时间点/单位（盲区 A1 的人工门已走）；
- [ ] 每条关系方向与材料一致（激活≠抑制、上下游不颠倒、包含用分组；盲区 A2 的逐条核对已做）；
- [ ] CP1 `{"valid": true}`：kind 可映射、containment 用分组、图例双向、调色板 ≥ 类别数；
- [ ] 数值/坐标/单位与数据表逐项一致，**绝不换算单位**，改数据后图确实重绘；
- [ ] `figure.svg`：文字可选（`<text>`）、图层可拆、带 `id` 与 `data-*`、内嵌 ER 清单、良构 XML；
- [ ] **画布预算核过**（§1 第 3 条）：内容没有被 `viewBox` 裁掉；
- [ ] 导出件：PDF 可打开；PNG 有效 DPI 达标；色彩 RGB 族；
- [ ] `result.json` 含全部契约键 + `case_id`，四形态回显无 `null`；
- [ ] `validate_result.py`（G1–G8）输出 VALID，退出码 0；
- [ ] 编辑任务：请求条数 == `change_records` 条数，未改动元素保持原样；
- [ ] **故障演练过**：`fault_inject.py` 退出码 0（25/25 符合期望）；
- [ ] **题集跑过**：`case_probe.py` 退出码 0（10/10 落在声明区间）；
- [ ] 交付前最后一次运行**没有** `--skip-checks` / `--no-lint`（盲区 A5）；
- [ ] 形态：仅 7 种文本扩展名、无 `__pycache__`、≤50 文件、≤500KB/文件、≤2MB、包内无本机绝对路径。

## ⑨ 依赖与限制

- Python 3.9+（实测 3.13.9）；运行必需 **matplotlib / Pillow / numpy**，
  reportlab 可选；缺 matplotlib 或 Pillow 时**不会裸崩**，而是写 `failed` 的
  `result.json` 并提示 `pip install matplotlib pillow numpy`；
- PDF 抽取按 fitz → pypdf → PyPDF2 → **stdlib 回退**逐级降级（backend 记 stdlib，
  并注明**不重建版面**）；无 cairosvg/svgwrite：PNG/PDF 是与 SVG 同源的
  matplotlib 镜像（**语义一致、非逐像素**，写进 `uncertainty`）；
- `case_probe.py` 的 XML 良构校验优先用 lxml，**缺 lxml 自动用标准库**兜底；
- **平台运行契约**：技能装在 `/skills/weekly-skill`；输入 `/input/case.json`
  + `/input/task.md`；中间产物 `/app/work`；最终产物 `/app/output`；
  预算 64 次模型请求 / 900 秒 / 16384 token per response —— 先落盘可用部分
  产物，再增量改进；
- **资源形态（硬约束）**：包内只放 UTF-8 文本
  （`.md/.py/.json/.txt/.csv/.yaml/.yml`），≤50 个文件、单文件 ≤500KB、
  合计 ≤2MB、无符号链接；图稿与渲染件一律运行时生成；
- **已知限制（如实标注）**：预览为同源镜像非逐像素；PDF 字体嵌入审计为
  尽力而为；CJK 依系统字体；`extract.py` 只产草稿；走 `--edit-svg` 时
  **`edits` 与 `edit_requests` 两个字段都生效**（`edits` 优先；本轮实测更正了旧文档的反向说法），
  真正的坑是**字段名写错**（`target`/`value`）会让请求被拒 ⇒ 必须对拍
  「请求条数 vs `change_records` 条数」（`main.py` 已把编辑问题写进 `uncertainty`）；
  四形态注入只覆盖**注册过的 25 条**、
  题集只覆盖**5 个案例 + 5 条探针** —— 没测过的情形一律按"未测量"处理，
  **不给它们背书**。

## ⑩ 禁止事项

- 不提交预制答案/正式案例输出；示例与新案例只演示接口与流程，**产物不入包**；
- 不编造缺失的软件状态或科学数据（来源里没有的实体/数值一律不画）；
- **不把"没检查过"说成"检查通过"**：`--skip-checks` / `--no-lint` 的运行
  不得作为交付版本；字典加载失败必须留下 `spec_lint.corpus` warn；
- **不声称没测过的能力**：平台分数、`line`/`scatter` 分支、真实论文 PDF、
  >60 节点拓扑、EPS/TIFF 导出与期刊字体嵌入审计均为"未测量"；
- 不为"好看"改关系颜色（改色 = 图例不一致）。
