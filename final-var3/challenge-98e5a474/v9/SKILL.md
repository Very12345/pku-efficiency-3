---
name: scientific-schematic-editor
description: >-
  Generate and edit editable scientific schematics, mechanism/relationship
  diagrams, flow diagrams and data charts from source materials — and state
  exactly what still works when a dependency is missing. This build (v9) leads
  with a runnable degradation matrix (scripts/degrade_probe.py): 16 probes use
  controlled import interception (sitecustomize + sys.meta_path) to remove
  matplotlib, Pillow, numpy, PyYAML, python-pptx, lxml, the PDF library family
  (fitz/pypdf/PyPDF2) and reportlab, sanitise PATH to remove the LibreOffice
  CLI, then run the real pipeline or a sub-tool and record what survives: exit
  code, status, whether result.json is written, which artefacts remain, the
  fail/warn counts, the uncertainty text, and whether the degradation was
  SILENT. Extracts an entity-relation manifest traceable to sources, draws a
  layered editable SVG source plus PNG/PDF exports, runs CP1 plan-lint and
  export-compliance checks, and writes a result.json carrying every
  output_contract field. Use when a task asks to draw, regenerate or edit a
  scientific figure from papers, tables or notes: 科研示意图/机制图/信号通路图/
  流程图/实验装置图/图表的生成与编辑, or when the target machine's dependency
  set is uncertain. Order: read the contract → read the real files → extract ER
  → lint the plan (CP1) → draw → check (CP2) → edit and re-check (CP4) →
  contract gate (CP3) → dependency audit (CP7).
---

# scientific-schematic-editor —（v9 · 缺依赖降级链实测版）

本版把"**缺个库还能不能用**"从一句"应该没问题"变成**可运行的 16 条探针 + 逐项实测 +
最小可用环境清单**：新增 `scripts/degrade_probe.py`，用**受控导入拦截**（等价于目标机
没装该库）与**净化 PATH**（等价于没有该命令）逐条制造缺失，真跑主流程 / 子工具，
记录退出码、`status`、是否写 `result.json`、产物还剩哪几件、fail/warn 计数、
`uncertainty` 原文、是否**静默降级**。逐项表与结论在 `references/DEGRADE-MATRIX.md`。

| 段 | 一句话 | 权威文件 |
|-|-|-|
| ① 输入与输出 | 平台给什么、以什么为准、什么算缺 | §1 |
| ② 执行 | S0–S7 一步一条命令，五个检查点 | §2 |
| ③ **依赖降级（本版主轴）** | 16 条探针 × 判据 P1–P6 + 最小可用环境清单 | §3、`references/DEGRADE-MATRIX.md`、`scripts/degrade_probe.py` |
| ④ 失败与降级 | 四形态 25 条注入实测（0 条静默）+ 六条公开盲区 | §4、`references/FAULT-MATRIX.md`、`references/failure-modes.md` |
| ⑤ 契约与复核 | G1–G8 硬门 + 独立校验器（自说 success 不算数） | §5 |
| ⑥ 增益 / 机制 / 复用 | 真实读数在哪、哪些没测 | §6、`references/STRENGTH-AXES.md`、`references/CASE-SET.md` |

**本技能不做**：统计方法的数值计算与选择、海报/封面版式、艺术插画美化、论文正文写作。
数据表里的数值是**事实输入**：不改算、不补造、不换算单位。

---

## ① 输入与输出

| 路径 | 内容 | 读法 |
|-|-|-|
| `/input/case.json` | `case_id` / `workorder` / `figure_type` / `sources` / 可选 `manifest`、`entities+relations`、`data`、`edits`、`edit_requests`、`output_contract` | **以文件实际内容为准**，不凭字段名猜语义 |
| `/input/task.md` | 任务书 | 与 case 冲突时以任务书 + 材料原文为准 |
| `/input/` 下的材料 | 可能是 PDF | 先过 `scripts/pdftext.py`（四段回退；加密件被明确拒绝） |

```
/app/output/
├── figure.svg      # 可编辑分层源文件：文字是 <text>、layer-* 分组、data-* 溯源、内嵌 ER 清单
├── figure.png      # 渲染预览（matplotlib 镜像同一 layout+manifest）
├── figure.pdf      # 矢量导出件
├── result.json     # 结构化结果（OUTPUT_CONTRACT 全字段 + case_id）
└── work/           #（或 /app/work）entities.json / layout.json / manifest.validated.json
```

**输入层三件事**（做错后面全错）：① 解析 `output_contract` 四形态（string→`""`、
array→`[]`、object→`{}`、number/boolean→`0`/`false`，**禁 `null`**）；
② 逐份读 `case.sources` 指向的**真实文件**，读不到的写进 `uncertainty`；
③ 核**画布预算**（`style.canvas` 一旦显式声明，布局不再自动扩展，超出部分会被
`viewBox` 裁掉且不报 warn）。

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
| **S0** | 读任务书与 case；记 `case_id`；解析 `output_contract`；确认输出/工作目录 | **CP7 前置** | case 不可解析 ⇒ `exit 2` + `FATAL`，不写半成品 |
| **S1** | 逐份读真实材料；PDF 先过 `pdftext.py`；读不到的记 `uncertainty` | — | 加密件 `exit 2`；扫描件 `chars: 0`；**缺 PDF 库走 stdlib 回退**（实测 backend=stdlib、52 字） |
| **S2** | `extract.py` 产候选草稿（`_draft`）；人工复核后写 `entities.json` | — | 草稿进 CP1 会被判 INVALID |
| **S3** | `spec_lint.py --manifest …` | **CP1** | 结构错 ⇒ `exit 1` + `partial` + `spec.relation_kind` / `spec.containment_group` fail |
| **S4** | `main.py --case … --manifest … --work … --out …` | — | **缺 matplotlib/Pillow/numpy ⇒ `exit 1` + `failed` 的 result.json**（不是裸崩） |
| **S5** | 溯源比例、图例双向、数据映射、导出预检 | **CP2** | 字体缺失 ⇒ `font.cjk` warn + `uncertainty` |
| **S6** | `--edit-svg` 源文件级增量修改；改完重跑 CP2 + CP3 | **CP4** | 字段名错 ⇒ 请求条数 ≠ `change_records` 条数 |
| **S7** | `validate_result.py`（G1–G8）→ VALID；**再跑依赖审计确认目标机环境** | **CP3 / CP7** | 契约形状错 ⇒ 独立校验器 INVALID；关键依赖缺 ⇒ 见 §3 的"彻底不可用清单" |

**退出码语义（与 `status` 同向）**：`0` = `success`；`1` = `partial`/`failed`
（**一定写出** result.json）；`2` = 致命（case 无法定位/解析、编辑目标无内嵌清单、
输入层不可用，**不写出**）。

---

## ③ 依赖降级链（本版主轴）：16 条探针 + 最小可用环境

```bash
SKILL_DIR="$(cd "$(dirname "<本 SKILL.md 的实际路径>")" && pwd)"
RUN="<包外临时目录>"

python "$SKILL_DIR/scripts/degrade_probe.py" --list
python "$SKILL_DIR/scripts/degrade_probe.py" --skill-root "$SKILL_DIR" --out "$RUN/dg"
python "$SKILL_DIR/scripts/degrade_probe.py" --skill-root "$SKILL_DIR" --out "$RUN/dg" --json
python "$SKILL_DIR/scripts/degrade_probe.py" --skill-root "$SKILL_DIR" --out "$RUN/dg" --only G01,G03c,H01
```

**判据 P1–P6**

| 判据 | 内容 | 实测 |
|-|-|-|
| **P1** | 每条探针都必须留下可解释的形态（含"缺依赖 ⇒ 如实失败"） | 16/16；`silent = 0` ⇒ 退出码 0 |
| **P2** | 缺关键依赖时**必须**写出 `failed` 的 `result.json`，不许裸追栈 | G01/G02/G03/G03b/G03c：`exit 1` + `status=failed` + `uncertainty` 写明缺失模块 |
| **P3** | 出问题必须有痕迹：非零退出码 / `status` / fail / warn / `uncertainty` 至少命中一个 | 16/16（**0 条静默降级**） |
| **P4** | 可选依赖缺失必须**不减产物** | G04/G05/G06/G07/G08/G09/G10/H03：三件产物齐全、fail/warn 与基线相同 |
| **P5** | 降级链必须真的能降级（而不是直接失败） | H01：三个 PDF 库全缺 ⇒ `backend=stdlib`、仍抽到 52 字；H02：缺 lxml ⇒ `xml_backend=stdlib`、1/1 conforms |
| **P6** | "不在运行路径上"的依赖必须被实测证明（而不是靠文档声明） | `yaml`/`pptx`/`reportlab`/LibreOffice CLI 各自一条探针，全部 `full` |

**实测汇总（`degrade-matrix.json.summary`）**

| 计数 | 值 |
|-|-|
| 探针数 / 静默 | **16 / 0** |
| 档位分布 | `full 9 · unavailable 5 · degraded-usable 2` |
| 在运行路径上的模块 | `matplotlib`、`PIL`、`numpy` |
| 不在运行路径上的模块 | `yaml`、`pptx`、`lxml`、`reportlab`、`fitz`、`pypdf`、`PyPDF2`、LibreOffice CLI |
| 探针总墙钟 | 18.3 秒 |

**最小可用环境（表格读数直接来自 `degrade-matrix.json.minimal_env`）**

| 模块 | 是否必需 | 缺了会怎样 | 证据 |
|-|-|-|-|
| `matplotlib` | **必需** | 流水线不可用（`exit 1` / `failed` / 无产物） | G01 |
| `Pillow` | **必需** | 同上（失败原因写作 `render.matplotlib`，须读 `uncertainty` 分辨） | G02 |
| `numpy` | **必需（传递依赖）** | 同上 —— **不是"只有热图才要"**（matplotlib 硬依赖 numpy） | G03/G03b/G03c |
| `fitz`/`pypdf`/`PyPDF2` | 可选 | 仍能抽字面量，但**不重建版面** | H01 |
| `lxml` | 可选 | XML 校验回退标准库（功能等价） | H02 |
| `reportlab` / `PyYAML` / `python-pptx` / LibreOffice CLI | **不需要** | 实测无影响（不在运行路径上） | G04/G05/G08/G09 |

> **一个被实测推翻的直觉**：原以为"`numpy` 只在 chart 的 heatmap+matrix 分支被 import，
> 所以 schematic 不受影响"。三条探针（G03/G03b/G03c）**一致推翻了它**：numpy 是
> matplotlib 的硬依赖，缺它连 schematic 都起不来。这正是"可运行的探针"比"读代码猜"
> 值钱的地方 —— 预测写在 `degrade_probe.py` 的 `why` 里，实测结果写进
> `references/DEGRADE-MATRIX.md` §7 第 8 条。

---

## ④ 失败与降级（四形态 25 条注入实测）

```bash
python "$SKILL_DIR/scripts/fault_inject.py" --skill-root "$SKILL_DIR" --out "$RUN/fi"
python "$SKILL_DIR/scripts/fault_inject.py" --skill-root "$SKILL_DIR" --out "$RUN/fi" --list
```

- **留痕律**：出了问题必须留下机器可读痕迹；四者全空 = 静默失败 = 本技能失效；
- **出口一致律**：CLI 退出码与 `result.json.status` 必须同向。

实测 **25/25 符合期望、0 条静默失败**。依赖矩阵与故障矩阵互补：前者问
"**环境缺东西**会怎样"，后者问"**输入坏掉**有没有留痕"。

---

## ⑤ 契约与独立复核（自说 success 不算数）

```bash
python "$SKILL_DIR/scripts/validate_result.py" \
    --case /input/case.json --result /app/output/result.json
python "$SKILL_DIR/scripts/run_examples.py" --out "$RUN/examples"
python "$SKILL_DIR/scripts/doccheck.py"
```

G1–G8 是独立可复跑的硬门 ⇒ 脚本说 `success` 不算数，契约门说 VALID 才算数。
实测：三示例全部 `exit 0` + VALID；`selftest.py` 35/35；`doccheck.py` 0 fails。

---

## ⑥ 增益 / 机制 / 复用：真实读数在哪、哪些没测

- **增益读数**（F1–F8 / I1–I10 / R1–R13）在 `references/STRENGTH-AXES.md` §A；本包**没有**
  跑"不加载 Skill 的基线臂"，因此**不声称**"比基线得分更高"；
- **机制**（M1–M5）在 `references/STRENGTH-AXES.md` §B；本版新增的依赖矩阵是
  **M3（抽取四段回退）与 M5（单一字体事实源）在"环境侧"的验收器**：回退链必须能
  被真实触发并留下 backend 记录（P5）；
- **可复用资产** A1–A12 与采纳阶梯在 `references/STRENGTH-AXES.md` §C；本版新增资产：
  **依赖降级探针**（对任意同族技能包跑 `--skill-root <别的包>` 即可得到它自己的
  最小可用环境清单）；
- **跨题材题集**在 `references/CASE-SET.md`；
- **未测量**：半损坏的库、跨 OS/跨 Python 版本、缺 CJK 字体、matplotlib 后端/FreeType
  缺失、只读输出目录与磁盘满、`--skip-checks` 叠加缺依赖 —— 一律按"未测量"处理。

---

## ⑦ 资源清单（路径相对技能根，调用一律 `"$SKILL_DIR/..."`）

| 入口 | 角色 | CLI |
|-|-|-|
| `scripts/main.py` | 流水线入口（含依赖门 + 字典兜底） | `--case --manifest --out --work --edit-svg --base-name --exports --dpi --skip-checks --lint --no-lint --fixed-time --doc-check` |
| `scripts/degrade_probe.py` | **缺依赖降级链实测（本版主轴）** | `--skill-root --out --only --list --json --quiet --keep --timeout` |
| `scripts/fault_inject.py` | 四形态故障注入与恢复演练（只动包外副本） | `--skill-root --out --form --only --json --quiet --keep --list` |
| `scripts/case_probe.py` | 题集执行器（逐案真跑 + 对区间 + 边界探针） | `--skill-root --out --group --only --list --json --quiet --keep` |
| `scripts/extract.py` | 材料 → 候选 ER 清单草稿 | `--inputs --out --base-dir` |
| `scripts/pdftext.py` | PDF 文本抽取（fitz → pypdf → PyPDF2 → stdlib 四段回退） | `--pdf --out` |
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
| `references/DEGRADE-MATRIX.md` | **本版主轴**：注射方法 · 16 行逐项实测 · 可用性结论 · 彻底不可用清单 · 最小可用环境 · 未覆盖声明 |
| `references/OUTPUT_CONTRACT.md` | `result.json` 契约 + G1–G8 + 四形态回显（字段块逐字不变） |
| `references/FAULT-MATRIX.md` | 25 行实测注入矩阵 + 六条盲区 + 既有缺陷的修复前后对照 |
| `references/CASE-SET.md` | 题集（逐案输入/期望/区间/难度）+ 逐案实测 + 六条泛化边界 |
| `references/STRENGTH-AXES.md` | §A 对照协议 F1–F8 / I1–I10 + §B 机制 M1–M5 + §C 可复用资产 A1–A12 |
| `references/failure-modes.md` | 题面 12 类失败形态 → 检测 → 处置 → 档位 → 恢复条件 |
| `references/CHECK-INDEX.md` | 全部检查名清单（doccheck 事实源 / 机制判据来源 / 指标取值来源） |
| `references/EDIT-ACTION-SCHEMA.md` | 编辑动作 → 字段名 → 记录 的对照表、实测矩阵、反模式 |
| `references/ER_MANIFEST.md` / `references/DRAWING_GRAMMAR.md` | 清单规范 / 图形语法 |
| `references/RUBRIC_MAP.md` | 五维评分 → 本包文件/机制逐条映射（含本版环境轴的落点） |
| `assets/relation-dict.json` / `assets/checklist.json` | 连接规则字典 / CP1–CP5 自查清单（机器可读） |
| `examples/*` / `examples/cases/*` | 包内三示例 + 两个不同题材的合成案例 |

---

## ⑧ 自查清单（提交前逐行确认；机器版 `assets/checklist.json`）

- [ ] **依赖审计跑过**：`degrade_probe.py` 退出码 0、`silent == 0`，且目标机的
      `matplotlib` / `Pillow` / `numpy` 三者可用（判据 P2/P3）；
- [ ] 若目标机缺 PDF 库：`pdftext.py` 走 stdlib 回退并在 `uncertainty` 里写明"不重建版面"（P5）；
- [ ] 实体名逐字出自材料；关系方向与材料一致；CP1 `{"valid": true}`；
- [ ] 数值/坐标/单位与数据表逐项一致，**绝不换算单位**；
- [ ] `figure.svg`：文字可选（`<text>`）、图层可拆、带 `id` 与 `data-*`、内嵌 ER 清单、良构 XML；
- [ ] 画布预算核过；导出件：PDF 可打开、PNG 有效 DPI 达标、`artifact.<role>` 逐类核过；
- [ ] `result.json` 含全部契约键 + `case_id`，四形态回显无 `null`；
- [ ] `validate_result.py`（G1–G8）输出 VALID，退出码 0；
- [ ] 编辑任务：请求条数 == `change_records` 条数；
- [ ] **故障演练过**：`fault_inject.py` 退出码 0（25/25）；**题集跑过**：`case_probe.py` 退出码 0（10/10）；
- [ ] 交付前最后一次运行**没有** `--skip-checks` / `--no-lint`；
- [ ] 形态：仅 7 种文本扩展名、无 `__pycache__`、≤50 文件、≤500KB/文件、≤2MB、包内无本机绝对路径。

---

## ⑨ 依赖与限制

- **最小可用环境**：`matplotlib` + `Pillow` + `numpy`（三个都必需，见 §3）；
  可选：`pymupdf`/`pypdf`（升级 PDF 抽取到版面级）、`lxml`（XML 校验后端）、`reportlab`；
  `PyYAML`/`python-pptx`/LibreOffice CLI **不在运行路径上**（实测无影响）；
- 缺关键依赖时**不会裸崩**：写 `failed` 的 `result.json` 并提示
  `pip install matplotlib pillow numpy`；
- PDF 抽取四段回退（fitz → pypdf → PyPDF2 → **stdlib**）：stdlib 档**只抓字面量、
  不重建版面**，`backend` 如实写进结果；
- 无 cairosvg/svgwrite：PNG/PDF 是与 SVG 同源的 matplotlib 镜像（**语义一致、非逐像素**，
  写进 `uncertainty`）；
- **平台运行契约**：技能装在 `/skills/weekly-skill`；输入 `/input/case.json` + `/input/task.md`；
  中间产物 `/app/work`；最终产物 `/app/output`；预算 64 次模型请求 / 900 秒 /
  16384 token per response（一次依赖矩阵 ≈ 18 秒，用于交付前自证）；
- **资源形态（硬约束）**：包内只放 UTF-8 文本（`.md/.py/.json/.txt/.csv/.yaml/.yml`），
  ≤50 个文件、单文件 ≤500KB、合计 ≤2MB、无符号链接；图稿与渲染件一律运行时生成；
- **已知限制（如实标注）**：只测"完全缺失"，不测半损坏的库；只测本机 Windows +
  Python 3.13.9；缺 CJK 字体属另一条链路（`font.cjk`），未纳入本矩阵；`G03c` 的
  heatmap 夹具是**合成值**；`extract.py` 只产草稿。

## ⑩ 禁止事项

- 不提交预制答案/正式案例输出；示例与新案例只演示接口与流程，**产物不入包**；
- 不编造缺失的软件状态或科学数据（来源里没有的实体/数值一律不画）；
- **不把"没检查过"说成"检查通过"**：`--skip-checks` / `--no-lint` 的运行不得作为交付版本；
- **不把"没测过的环境"说成"能跑"**：半损坏的库、跨 OS/版本、缺字体、只读输出目录
  一律按"未测量"处理；交付前必须按 §3 的清单确认三个必需依赖可用；
- **不声称没测过的能力**：平台分数、`line`/`scatter` 分支、真实论文 PDF、>60 节点拓扑、
  EPS/TIFF 导出与期刊字体嵌入审计均为"未测量"；
- 不为"好看"改关系颜色（改色 = 图例不一致）。
