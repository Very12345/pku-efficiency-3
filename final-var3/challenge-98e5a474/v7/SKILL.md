---
name: scientific-schematic-editor
description: >-
  Generate and edit editable scientific schematics, mechanism/relationship
  diagrams, flow diagrams and data charts from source materials — and prove
  the result is byte-reproducible. This build (v7) leads with determinism:
  a runnable matrix runner (scripts/determinism.py) executes the pipeline in
  six independent processes across different working directories and
  PYTHONHASHSEED values, hashes every produced file, and separates DELIBERATE
  instability (timestamps, absolute paths, PDF /CreationDate) from accidental
  instability; it exits non-zero when an unexplained byte difference survives
  normalisation. Extracts an entity-relation manifest traceable to sources,
  draws a layered editable SVG source plus PNG/PDF exports, runs CP1 plan-lint
  and export-compliance checks, and writes a result.json carrying every
  output_contract field. Use when a task asks to draw, regenerate or edit a
  scientific figure from papers, tables or notes: 科研示意图/机制图/信号通路图/
  流程图/实验装置图/图表的生成与编辑, or when two runs of a figure pipeline
  must be shown to agree. Order: read the contract → read the real files →
  extract ER → lint the plan (CP1) → draw → check (CP2) → edit and re-check
  (CP4) → contract gate (CP3) → determinism matrix (CP5).
---

# scientific-schematic-editor —（v7 · 确定性与字节级可复现版）

本版把"**同一份输入跑两遍必须一样**"从一句口号变成**可运行的矩阵 + 三档判据 + 实测读数**：
新增 `scripts/determinism.py`（6 个独立进程 × 不同 cwd × 不同 `PYTHONHASHSEED` × 可选
`SOURCE_DATE_EPOCH`），对**全部产物**逐字节比对，并把"故意不稳定"与"意外不稳定"分开。
逐字段表、稳定化命令与未覆盖声明在 `references/DETERMINISM.md`。

| 段 | 一句话 | 权威文件 |
|-|-|-|
| ① 输入 | 平台给什么、以什么为准、什么算缺 | §1 |
| ② 执行 | S0–S7 一步一条命令，五个检查点 | §2 |
| ③ **确定性（本版主轴）** | 6 个独立进程 × 三档判据 V1–V6 + 实测 sha256 表 | §3、`references/DETERMINISM.md`、`scripts/determinism.py` |
| ④ 失败与降级 | 四形态 25 条注入实测（0 条静默）+ 六条公开盲区 | §4、`references/FAULT-MATRIX.md`、`references/failure-modes.md` |
| ⑤ 契约与复核 | G1–G8 硬门 + 独立校验器（自说 success 不算数） | §5、`references/OUTPUT_CONTRACT.md` |
| ⑥ 增益 / 机制 / 复用 | 真实读数在哪、哪些没测 | §6、`references/STRENGTH-AXES.md`、`references/CASE-SET.md` |

**本技能不做**：统计方法的数值计算与选择、海报/封面版式、艺术插画美化、论文正文写作。
数据表里的数值是**事实输入**：不改算、不补造、不换算单位。

---

## ① 输入与输出

| 路径 | 内容 | 读法 |
|-|-|-|
| `/input/case.json` | `case_id` / `workorder` / `figure_type` / `sources` / 可选 `manifest`、`entities+relations`、`data`、`edits`、`edit_requests`、`output_contract` | **以文件实际内容为准，不凭字段名猜语义** |
| `/input/task.md` | 任务书 | 与 case 冲突时以任务书 + 材料原文为准 |
| `/input/` 下的材料 | 可能是 PDF | 先过 `scripts/pdftext.py`（加密件会被**明确拒绝**，不出空文本） |

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

**输入层三件事**（做错后面全错，结构门救不回来）：

1. 解析 `output_contract` 声明的键与类型 —— 四形态回显：string→`""`、
   array→`[]`、object→`{}`、number/boolean→`0`/`false`，**禁 `null`**；
2. 逐份读 `case.sources` 指向的**真实文件**，读不到的写进 `uncertainty`；
3. 核**画布预算**：`style.canvas` 一旦显式声明，布局不再自动扩展，超出部分会被
   `viewBox` 裁掉且不报 warn —— 按 `width ≥ 370 × 最大层号 + 节点宽 + 40` 算，或干脆不声明。

---

## ② 执行：S0–S7 与五个检查点

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

| 步 | 动作 | 检查点 | 失败形态 |
|-|-|-|-|
| **S0** | 读任务书与 case；记 `case_id`；解析 `output_contract` 四形态；确认输出/工作目录 | — | case 不可解析 ⇒ `exit 2` + `FATAL`，不写半成品 |
| **S1** | 逐份读真实材料；PDF 先过 `pdftext.py`；读不到的记 `uncertainty` | — | 加密件 `exit 2`；扫描件 `chars: 0`；缺库走 stdlib 回退 |
| **S2** | `extract.py` 产候选草稿（`_draft`）；**人工复核后**写 `entities.json` | — | 草稿进 CP1 会被判 INVALID —— 这正是"草稿不是答案"的门 |
| **S3** | `spec_lint.py --manifest …` | **CP1** | 结构错 ⇒ `exit 1` + `partial` + `spec.relation_kind` / `spec.containment_group` fail |
| **S4** | `main.py --case … --manifest … --work … --out …`；绘图前再核一次画布预算 | — | 依赖缺失 ⇒ `exit 1` + `failed` 的 result.json |
| **S5** | 溯源比例、图例双向、数据映射、导出预检（DPI/色彩/`<text>`/PDF/字体） | **CP2** | 字体缺失 ⇒ `font.cjk` warn + `uncertainty` |
| **S6** | `--edit-svg` 源文件级增量修改；请求写在 `edit_requests`；改完重跑 CP2 + CP3 | **CP4** | 字段名错 ⇒ 日志 `[edit] fail`，条数对不上 |
| **S7** | `validate_result.py`（G1–G8）→ VALID；**再跑一次确定性矩阵** | **CP3 / CP5** | 契约形状错 ⇒ 独立校验器 INVALID；字节漂移 ⇒ `determinism.py` `exit 1` |

**退出码语义（与 `status` 同向）**

| 退出码 | 含义 | result.json | 重试语义 |
|-|-|-|-|
| `0` | `status=success`；允许存在已被 `acknowledged_issues` 核可的 warn | 写出，`fail_count==0` | 无需重试 |
| `1` | `status=partial`（有 fail 明细）或 `status=failed`（流水线异常） | **一定写出** | 按 fail 明细定向修复后重跑 |
| `2` | 致命：case 无法定位/解析、编辑目标无内嵌清单、输入层不可用 | **不写出** | 先解决输入问题 |

---

## ③ 确定性验收（本版主轴）：6 进程矩阵 + 三档判据 + 实测读数

**一条命令**（`--out` 必须在包外，写进包内会被直接拒绝）：

```bash
SKILL_DIR="$(cd "$(dirname "<本 SKILL.md 的实际路径>")" && pwd)"
RUN="<包外临时目录>"

python "$SKILL_DIR/scripts/determinism.py" --list
python "$SKILL_DIR/scripts/determinism.py" --skill-root "$SKILL_DIR" --out "$RUN/det"
python "$SKILL_DIR/scripts/determinism.py" --skill-root "$SKILL_DIR" --out "$RUN/det" --json
python "$SKILL_DIR/scripts/determinism.py" --skill-root "$SKILL_DIR" --out "$RUN/det" --runs 6 --quiet
```

**三档判据 V1–V6**（`determinism.py` 的退出码就按它们判）

| 判据 | 内容 | 不满足时 |
|-|-|-|
| **V1** | 每个 run 都必须 `exit 0` 且写出 `result.json` | 记 `AT-LEAST-ONE-RUN-FAILED`，`exit 1` |
| **V2** | `figure.svg` / `figure.png` / `layout.json` / `manifest.validated.json` 在 6 个 run 间**逐字节全等** | `exit 1`（这是真缺陷） |
| **V3** | `result.json` 除 `generated_at` 与 `artifacts[].abspath` 外**逐字节全等** | `exit 1` |
| **V4** | `figure.pdf` 允许 `/CreationDate` 不同；**归一化后必须全等**，且设 `SOURCE_DATE_EPOCH` 后必须**raw 全等** | `exit 1` |
| **V5** | `volatile_fields[]` 里不允许出现 `kind="unclassified"`（"解释不掉"的差异一律判失败，绝不解释掉） | `exit 1` |
| **V6** | `result.json.determinism.spec_sha16`（输入+方案指纹）在 6 个 run 间相同 | 说明输入或 CP1 判定漂了 |

**实测读数（2026-11-23，Python 3.13.9 / matplotlib 3.10.6 / Pillow 12.3.0 / numpy 2.3.5，6 次运行）**

| 文件 | 字节 | sha256（run1..run6 前 12 位） | 判据 | 说明 |
|-|-|-|-|-|
| `figure.svg` | 15,241 | `24eab86e4c29` ×6 | **V2** | 可编辑源文件与"在哪跑、什么时候跑"无关 |
| `figure.png` | 165,063 | `71fb5f387258` ×6 | **V2** | 无嵌入时间戳 |
| `layout.json` | 3,333 | `932d9d314b1b` ×6 | **V2** | 布局是纯函数 |
| `manifest.validated.json` | 4,967 | `3fee6c0cba90` ×6 | **V2** | 规范化不引入随机性 |
| `figure.pdf` | 37,944 / 37,938 | natural：4 个不同 sha；**stabilized：`c06682bd8336` ×2** | **V4** | 唯一变量是 `/CreationDate`；设 `SOURCE_DATE_EPOCH` 后 raw 全等 |
| `result.json` | 9,872 | 6 个不同 sha；**归一化后 `236b85c8dea5` ×6** | **V3** | 唯一变量是 3 条 `artifacts[].abspath` |
| `determinism.spec_sha16` | — | `3af4c86b04dc57c1` ×6 | **V6** | 输入与 CP1 判定完全一致 |

汇总：`identical_after_normalization = true`、`unclassified_differences = 0`、
`verdict = BYTE-IDENTICAL-AFTER-DOCUMENTED-NORMALISATION`、**退出码 0**；
`volatile_fields` 恰 4 条（PDF `/CreationDate` + 3 条 `abspath`），逐条给了
"为什么会变 / 怎么稳定化"，见 `references/DETERMINISM.md` §5。

**"故意不稳定"清单（允许不同，但必须点名，且给出稳定化办法）**

| 字段 | 为什么故意不稳定 | 稳定化 |
|-|-|-|
| `result.json.generated_at` | 记录真实生成时间 | 传 `--fixed-time <ISO>`（矩阵默认已固定） |
| `result.json.artifacts[].abspath` | 契约要求记录"这次跑在哪里" | 归一化把本次 `out/`、`scratch/` 前缀替换为 `<RUN>`；或在**同一输出目录**重跑 |
| `figure.pdf` 的 `/CreationDate` + 派生 xref 偏移 | PDF 写当日时间戳，长度一变偏移整体位移 | 设 `SOURCE_DATE_EPOCH=<epoch>` ⇒ PDF 逐字节相同 |

> **判据的边界**：6 次运行只能证明"这 6 次之间没有意外差异"，不能外推为
> "任意次数都稳定"；跨操作系统、跨 matplotlib 版本、TIFF/EPS 导出、
> chart 图型的字节稳定性**未测量**（`references/DETERMINISM.md` §8 逐条列出）。

---

## ④ 失败与降级（四形态 25 条注入实测）

```bash
python "$SKILL_DIR/scripts/fault_inject.py" --skill-root "$SKILL_DIR" --out "$RUN/fi"
python "$SKILL_DIR/scripts/fault_inject.py" --skill-root "$SKILL_DIR" --out "$RUN/fi" --list
python "$SKILL_DIR/scripts/fault_inject.py" --skill-root "$SKILL_DIR" --out "$RUN/fi" --only D13,D18,D21
```

**判据（两条，整个矩阵按它们判"静默"）**

- **留痕律**：出了问题必须留下机器可读痕迹 —— 非零退出码、`status`、
  `verification.checks.fails/warns`、`uncertainty` 至少命中一个；**四者全空 = 静默失败 = 本技能失效**；
- **出口一致律**：CLI 退出码与 `result.json.status` 必须同向；冲突时以 `result.json`
  为记录面、退出码为重试面，并把冲突本身写进 `uncertainty`。

实测：**25/25 符合期望、0 条静默失败**（逐行矩阵在 `references/FAULT-MATRIX.md` §3，
题面 12 类失败形态 → 检测 → 处置 → 档位在 `references/failure-modes.md`）。
确定性矩阵与故障矩阵互补：前者问"同输入为什么不一样"，后者问"坏输入有没有留痕"。

---

## ⑤ 契约与独立复核（自说 success 不算数）

```bash
python "$SKILL_DIR/scripts/validate_result.py" \
    --case /input/case.json --result /app/output/result.json
# VALID（G1–G8 全过）即契约通过；退出码 0
python "$SKILL_DIR/scripts/run_examples.py" --out "$RUN/examples"   # 三个包内示例端到端
python "$SKILL_DIR/scripts/doccheck.py"                             # 文档承诺 vs 代码事实（只读）
```

- G1–G8 是**独立可复跑**的硬门，与 `main.py` 自己的汇总相互独立 ⇒ 脚本说 `success`
  不算数，契约门说 VALID 才算数；`--skip-checks` / `--no-lint` 的运行**不得**作为交付版本；
- 实测：三个包内示例全部 `exit 0` 且 `VALID`；`selftest.py` 35/35 通过；
  `doccheck.py` 0 fails（检查名、规则编号、CLI 参数三方对拍）。

---

## ⑥ 增益 / 机制 / 复用：真实读数在哪、哪些没测

- **增益读数**（对照协议 F1–F8、指标 I1–I10、实测 R1–R13）在 `references/STRENGTH-AXES.md` §A：
  它明确写出**本包没有跑过"不加载 Skill 的基线臂"**，因此**不声称**"比基线得分更高"；
- **机制**（M1 方案先行 / M2 源文件自描述 / M3 抽取四段回退 / M4 导出预检 / M5 单一字体
  事实源）在 `references/STRENGTH-AXES.md` §B，每条带"没有它会怎样"与可证伪判据；
  本版新增的确定性矩阵是这些机制的**验收器**：M1/M2 的产物必须跨进程逐字节一致（V2/V3）；
- **可复用资产** A1–A12 与采纳阶梯在 `references/STRENGTH-AXES.md` §C；
  本版新增资产：**确定性矩阵执行器**（对任意同族技能包跑 `--skill-root <别的包>` 即可复用）；
- **跨题材题集**（5 案 2 题材 + 5 条越界探针）与逐案实测在 `references/CASE-SET.md`；
- **未测量**：平台分数、`line`/`scatter` 分支、真实论文 PDF、>60 节点拓扑、EPS/TIFF 导出、
  期刊字体嵌入审计、**跨 OS/跨版本字节稳定性** —— 一律按"未测量"处理，不给它们背书。

---

## ⑦ 资源清单（路径相对技能根，调用一律 `"$SKILL_DIR/..."`）

| 入口 | 角色 | CLI |
|-|-|-|
| `scripts/main.py` | 流水线入口（含依赖门 + 字典兜底） | `--case --manifest --out --work --edit-svg --base-name --exports --dpi --skip-checks --lint --no-lint --fixed-time --doc-check` |
| `scripts/determinism.py` | **确定性矩阵执行器（本版主轴）** | `--skill-root --case --out --runs --fixed-time --source-date-epoch --json --quiet --keep --list` |
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
| `references/DETERMINISM.md` | **本版主轴**：三档判据 + 逐文件实测表 + `volatile_fields` 逐字段 + 稳定化命令 + 未覆盖声明 |
| `references/OUTPUT_CONTRACT.md` | `result.json` 契约 + G1–G8 + 四形态回显（字段块逐字不变） |
| `references/FAULT-MATRIX.md` | 25 行实测注入矩阵 + 六条盲区 + 既有缺陷的修复前后对照 |
| `references/CASE-SET.md` | 题集（逐案输入/期望/区间/难度）+ 逐案实测 + 六条泛化边界 |
| `references/STRENGTH-AXES.md` | §A 对照协议 F1–F8 / I1–I10 + §B 机制 M1–M5 + §C 可复用资产 A1–A12 |
| `references/failure-modes.md` | 题面 12 类失败形态 → 检测 → 处置 → 档位 → 恢复条件 |
| `references/CHECK-INDEX.md` | 全部检查名清单（doccheck 事实源 / 机制判据来源 / 指标取值来源） |
| `references/EDIT-ACTION-SCHEMA.md` | 编辑动作 → 字段名 → 记录 的对照表、实测矩阵、反模式 |
| `references/ER_MANIFEST.md` | 实体—关系清单规范（绘图唯一数据源） |
| `references/DRAWING_GRAMMAR.md` | 图形语法：关系语义 → 箭头/线型/颜色、方向判定、分组/层级 |
| `references/RUBRIC_MAP.md` | 五维评分 → 本包文件/机制逐条映射（含本版确定性轴的落点） |
| `assets/relation-dict.json` / `assets/checklist.json` | 连接规则字典 / CP1–CP5 自查清单（机器可读） |
| `examples/*` | 包内三示例（schematic / chart / edit + 合成材料 + `EXPECTED-OUTPUT.md`） |
| `examples/cases/*` | 两个不同题材的合成案例（细胞生物学机制图 / 转录组热图）+ 各自来源材料 |

---

## ⑧ 自查清单（提交前逐行确认；机器版 `assets/checklist.json`）

- [ ] 实体名逐字出自材料，无材料外基因/浓度/时间点/单位；
- [ ] 每条关系方向与材料一致（激活≠抑制、上下游不颠倒、包含用分组）；
- [ ] CP1 `{"valid": true}`：kind 可映射、containment 用分组、图例双向、调色板 ≥ 类别数；
- [ ] 数值/坐标/单位与数据表逐项一致，**绝不换算单位**，改数据后图确实重绘；
- [ ] `figure.svg`：文字可选（`<text>`）、图层可拆、带 `id` 与 `data-*`、内嵌 ER 清单、良构 XML；
- [ ] **画布预算核过**（§1 第 3 条）：内容没有被 `viewBox` 裁掉；
- [ ] 导出件：PDF 可打开；PNG 有效 DPI 达标；色彩 RGB 族；`artifact.<role>` 逐类核过；
- [ ] `result.json` 含全部契约键 + `case_id`，四形态回显无 `null`；
- [ ] `validate_result.py`（G1–G8）输出 VALID，退出码 0；
- [ ] 编辑任务：请求条数 == `change_records` 条数，未改动元素保持原样；
- [ ] **确定性矩阵跑过**：`determinism.py` 退出码 0，`unclassified_differences == 0`（判据 V1–V6 全过）；
- [ ] **故障演练过**：`fault_inject.py` 退出码 0（25/25 符合期望）；
- [ ] **题集跑过**：`case_probe.py` 退出码 0（10/10 落在声明区间）；
- [ ] 交付前最后一次运行**没有** `--skip-checks` / `--no-lint`；
- [ ] 形态：仅 7 种文本扩展名、无 `__pycache__`、≤50 文件、≤500KB/文件、≤2MB、包内无本机绝对路径。

---

## ⑨ 依赖与限制

- Python 3.9+（实测 3.13.9）；运行必需 **matplotlib / Pillow / numpy**，reportlab 可选；
  缺 matplotlib 或 Pillow 时**不会裸崩**，而是写 `failed` 的 `result.json` 并提示
  `pip install matplotlib pillow numpy`；
- **确定性相关**：`determinism.py` 只用标准库；PDF 的 `/CreationDate` 由
  `SOURCE_DATE_EPOCH` 决定（matplotlib 的 PDF backend 行为，实测生效）；
  PNG 与 SVG 未嵌入任何时间戳（实测 raw 全等）；
- PDF 抽取按 fitz → pypdf → PyPDF2 → **stdlib 回退**逐级降级（backend 记 stdlib，
  并注明不重建版面）；无 cairosvg/svgwrite：PNG/PDF 是与 SVG 同源的 matplotlib 镜像
  （**语义一致、非逐像素**，写进 `uncertainty`）；
- `case_probe.py` 的 XML 良构校验优先用 lxml，缺 lxml 自动用标准库兜底；
- **平台运行契约**：技能装在 `/skills/weekly-skill`；输入 `/input/case.json` + `/input/task.md`；
  中间产物 `/app/work`；最终产物 `/app/output`；预算 64 次模型请求 / 900 秒 /
  16384 token per response —— 先落盘可用部分产物，再增量改进（一次确定性矩阵 ≈ 8 秒，
  与预算相比可忽略）；
- **资源形态（硬约束）**：包内只放 UTF-8 文本（`.md/.py/.json/.txt/.csv/.yaml/.yml`），
  ≤50 个文件、单文件 ≤500KB、合计 ≤2MB、无符号链接；图稿与渲染件一律运行时生成；
- **已知限制（如实标注）**：预览为同源镜像非逐像素；PDF 字体嵌入审计为尽力而为；
  CJK 依系统字体；`extract.py` 只产草稿；走 `--edit-svg` 时 `edits` 与 `edit_requests`
  两个字段都生效（`edits` 优先），真正的坑是**字段名写错**会让请求被拒 ⇒ 必须对拍
  「请求条数 vs `change_records` 条数」；确定性矩阵只覆盖 **6 次运行的矩阵**与
  包内 schematic 示例，chart 图型、TIFF/EPS、跨 OS/跨版本**未测量**。

## ⑩ 禁止事项

- 不提交预制答案/正式案例输出；示例与新案例只演示接口与流程，**产物不入包**；
- 不编造缺失的软件状态或科学数据（来源里没有的实体/数值一律不画）；
- **不把"没检查过"说成"检查通过"**：`--skip-checks` / `--no-lint` 的运行不得作为交付版本；
- **不把"解释不掉"说成"可接受"**：`determinism.py` 出现 `kind="unclassified"` 必须当缺陷处理；
- **不声称没测过的能力**：平台分数、跨 OS/跨版本确定性、`line`/`scatter` 分支、真实论文 PDF、
  >60 节点拓扑、EPS/TIFF 导出与期刊字体嵌入审计均为"未测量"；
- 不为"好看"改关系颜色（改色 = 图例不一致）。
