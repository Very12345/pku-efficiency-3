---
name: scientific-schematic-editor
description: >-
  Generate and edit editable scientific schematics, mechanism/relationship
  diagrams, flow diagrams and data charts from source materials, and prove how
  the pipeline behaves when the inputs, the fixtures, the runtime or the
  contract are broken. Extracts an entity-relation manifest (traceable to
  sources), draws a layered editable SVG source plus PNG/PDF exports, runs CP1
  plan-lint and export-compliance checks, writes a result.json carrying every
  output_contract field, and ships scripts/fault_inject.py -- a runnable
  four-form fault harness (input / template / dependency / contract) whose
  measured matrix lives in references/FAULT-MATRIX.md. Use when a task asks to
  draw, regenerate or edit a scientific figure from papers, tables or notes:
  科研示意图/机制图/信号通路图/流程图/实验装置图/图表的生成与编辑.
  Execute in order: read the contract → read the real files → extract ER →
  lint the plan (CP1) → draw → check (CP2) → edit and re-check (CP4) →
  contract gate (CP3) → determinism (CP5) → fault drill.
---

# scientific-schematic-editor — 科研示意图生成与编辑（失败注入与恢复演练版）

本技能除了"把材料画成可编辑图稿"，还额外回答一个问题：
**当输入、夹具、运行环境或契约被弄坏时，它会怎么表现？**

答案不是一句"我们有异常处理"，而是 `scripts/fault_inject.py`：一个可运行的
四形态注入器。它把 25 种坏法逐个注入到**包外副本**上、真实跑一遍主流程，
并把"注入什么 → 期望行为 → 实测退出码/status/uncertainty → 是否静默失败"
逐行写成 `references/FAULT-MATRIX.md`。本轮 25 条**全部符合期望、0 条静默失败**，
并且**因此发现并修掉了两个真实缺陷**（见 §6）。

> 与决策系统版（v1）的关系：v1 把边界情况写成 D 规则；本版**不重述那些规则**，
> 而是给它们补上"**被真的弄坏过**"的实测证据，并且把 v1 承诺过、
> 却实测不成立的两处（字典损坏、依赖缺失）**修好**。规则表、降级档位、
> 检查名索引仍以 v1/references 为准。

## 1. 这套技能交付什么

| 交付面 | 内容 | 权威文件 |
|-|-|-|
| 能出图的链路 | 材料 → 实体关系清单 → CP1 生成前门 → 分层可编辑 SVG → PNG/PDF → `result.json` | `SKILL.md` §4、`scripts/main.py` |
| **会被弄坏的链路** | 25 条故障注入（输入/模板/依赖/契约四形态）与逐行实测结果 | `scripts/fault_inject.py`、`references/FAULT-MATRIX.md` |
| 契约 | `result.json` 字段、G1–G8 硬门、四形态回显 | `references/OUTPUT_CONTRACT.md`（字段块逐字不变） |
| 评审判据 | 五维（40/25/15/10/10）逐条 → 本包哪个文件/机制 | `references/RUBRIC_MAP.md` |
| 失败的权威描述 | 题面 12 类失败形态 → 检测 → 处置 | `references/failure-modes.md` |

**本技能不做**：统计方法的数值计算、海报/封面版式、艺术插画美化、论文正文
写作。数据表里的数值是**事实输入**：不改算、不补造、不换算单位。

## 2. 四形态故障模型（本版的组织主线）

任何一次运行都可能被四类东西弄坏。四类的**检测位置不同**，所以必须分开讲：

| 形态 | 坏的是 | 典型注入 | 检测位置 | 期望的兜底形态 |
|-|-|-|-|-|
| **输入 damaged** | `case.json` / 材料文件本身 | case 不是对象、材料文件缺失或不可读、`--manifest` 路径不存在 | `main.py` 的 case 解析与 `resolve_sources` | 解析不了 ⇒ `exit 2` 且**不写半成品**；能解析但材料缺 ⇒ 继续出图 + `uncertainty` |
| **模板/夹具 damaged** | 清单、分组、图例、连接规则字典 | kind 不在词表、`to` 指向不存在的实体、evidence 被删、字典损坏 | `spec_lint.py`（生成前 CP1）+ `checks.py`（产物后 CP2） | 结构错 ⇒ `exit 1` + `partial` + `spec_lint.*` fail；降级项 ⇒ warn |
| **依赖 damaged** | 运行环境 | 无 PDF 库、无 matplotlib、无 Pillow、无 CJK 字体、材料是加密/扫描 PDF | 各模块的 import 守卫 + `pdftext.py` + `textfont.py` | 能用回退就用回退并**如实记 backend**；彻底不能用 ⇒ `exit 1` + `failed` 的 result.json |
| **契约 damaged** | `case.json.output_contract` 声明 | 声明缺失、声明类型与实际形状不符 | `main.py` 回显 + `validate_result.py`（G5） | 声明缺失不阻断；形状不符由**独立校验器**判 INVALID（`exit 1`） |

**两条不可让步的判据**（整个矩阵都按它们判"静默"）：

- **留痕律**：出了问题就必须留下机器可读痕迹 —— 非零退出码、`status`、
  `verification.checks.fails/warns`、`uncertainty` 至少命中一个。
  **四者全空 = 静默失败 = 本技能失效**；
- **出口一致律**：CLI 退出码与 `result.json.status` 必须同向。
  `0` = success；`1` = partial 或 failed（**result.json 一定写出**）；
  `2` = 致命（不写产物，重试无意义）。

**四形态与既有判定词表的对应**（完整规则表在
`references/failure-modes.md`：那里把题面 12 类失败形态逐条映射到
**检测机制 → 处置条目 → 档位（L0–L3）→ 恢复条件**四列）：

| 形态 | 主要落在哪些处置条目上 | 档位 | 本版新增的实测证据 |
|-|-|-|-|
| 输入 damaged | D1（case 不可定位）、D3（材料缺失/矛盾）、D12（PDF 不可抽取） | L3（不可解析/不可抽取）/ L1（缺一份材料） | D01–D06 |
| 模板 damaged | D2（无出处实体）、D4（kind 不可映射）、D5（containment 未分组）、D6（图例缺项/孤儿）、D7（调色板不足）、D8（表外类别） | L2（结构错）/ L1（孤儿项等降级） | D07–D14 |
| 依赖 damaged | D11（CJK 缺失）、D13（渲染异常）、D14（无 PDF 库）、D15（缺运行库） | L1（可回退）/ L3（不可运行） | D15–D21 |
| 契约 damaged | D9（契约键缺值/类型不符）、D16（自选跳过检查） | L2（不改产物）/ L1（读数缺失） | D22–D24 |

> **本版对 D6 与 D15 的实测修正**：`legend.orphan_items` 实测为 warn（不阻断出图，D12 行），
> 而 `D15` 原先只承诺"打印缺件提示"，实测修复前是**裸 traceback 且无产物** ⇒
> 已按 §6 补上依赖门（现在写 `failed` 的 result.json）。文档与实测不一致处以实测为准，
> 并已同步 `references/failure-modes.md` 的对应行。

## 3. 输入与输出

**输入（平台提供，路径固定）**

| 路径 | 内容 | 读法 |
|-|-|-|
| `/input/case.json` | `case_id` / `workorder` / `figure_type` / `sources` / 可选 `manifest`、`entities+relations`、`data`、`edits`、`edit_requests`、`output_contract` | **以文件实际内容为准，不凭字段名猜语义** |
| `/input/task.md` | 任务书 | 与 case 冲突时以任务书 + 材料原文为准 |
| `/input/` 下的材料 | 可能是 PDF | 先过 `scripts/pdftext.py`（加密件会被明确拒绝） |

**输出（写入 `/app/output`，全部运行时现场生成）**

```
/app/output/
├── figure.svg      # 可编辑分层源文件（文字是 <text>、layer-* 分组、data-* 溯源、内嵌 ER 清单）
├── figure.png      # 渲染预览（matplotlib 镜像同一 layout+manifest）
├── figure.pdf      # 矢量导出件
├── result.json     # 结构化结果（OUTPUT_CONTRACT 全字段 + case_id）
└── work/           #（或 /app/work）entities.json / layout.json / manifest.validated.json
```

> **包内不预置任何图稿或渲染件**（PDF/PNG/SVG/TIFF 一律运行时生成）；
> 示例期望产物以文字清单写在 `examples/EXPECTED-OUTPUT.md`，
> 一键复现用 `scripts/run_examples.py`。

## 4. 执行顺序（含检查点与"哪一步会被哪种故障打断"）

**读契约 → 读材料 → 抽取 → 写清单 → CP1 → 绘图 → CP2 →（编辑则 CP4）→
CP3 → CP5 → 故障演练。**

| 步 | 动作 | 被哪种形态打断 | 打断后的样子 |
|-|-|-|-|
| **S0** | 读 `/input/task.md` 与 `/input/case.json`，记 `case_id`；解析 `output_contract` 的键与**四形态**（string→`""`、array→`[]`、object→`{}`、number/boolean→`0`/`false`，禁 `null`）；确认 `/app/output`、`/app/work` | 输入 | `exit 2` + `FATAL`，不写产物 |
| **S1** | 逐份读 `case.sources` 指向的**真实文件**；PDF 先过 `pdftext.py`；读不到的写进 `uncertainty` | 输入 / 依赖 | 材料缺失 ⇒ 继续（uncertainty）；PDF 加密 ⇒ `pdftext` `exit 2` 如实报告 |
| **S2** | `extract.py` 产候选草稿（带 `_draft`），Agent 复核后写 `/app/work/entities.json`：`name` 逐字来自材料、`kind` 映射到 7 类规范词表、包含关系落到 `groups` | 模板 | 草稿进 CP1 会被判 INVALID（缺图例等）——这正是"草稿不是答案"的门 |
| **S3** | **CP1 lint 门**：`spec_lint.py --manifest …`，只有 `{"valid": true}` 才继续 | 模板 | `exit 1` + `partial` + `spec_lint.spec.*` fail |
| **S4** | 绘图：`main.py --case … --manifest … --work … --out …`，产出 SVG/PNG/PDF + `result.json` | 依赖 / 契约 | 依赖缺失 ⇒ `exit 1` + `failed` 的 result.json |
| **S5** | **CP2 产物检查**：溯源比例、图例双向、数据映射、导出预检（DPI/色彩/`<text>`/PDF/字体） | 依赖（字体） | `font.cjk` warn + `uncertainty`，SVG 文字仍在 |
| **S6** | （编辑）`--edit-svg` 走源文件级增量修改；编辑请求写在 `edit_requests`；改完重跑 CP2 + CP3 | 模板（字段名） | 日志 `[edit] fail`；用"请求条数 vs `change_records` 条数"对拍 |
| **S7** | 契约门 `validate_result.py`（G1–G8）→ VALID；确定性双跑；**故障演练** `fault_inject.py` | 契约 | G5/G7 违例 ⇒ INVALID（`exit 1`） |

命令行（自定位，任意 cwd 可跑；`SKILL_DIR` = 本 SKILL.md 所在目录）：

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

## 5. 故障演练与恢复（本版的核心操作）

```bash
# 全矩阵：25 条四形态注入，约 40 s，产物全部落在包外
python "$SKILL_DIR/scripts/fault_inject.py" --skill-root "$SKILL_DIR" --out /tmp/sse-fault

# 按形态筛选 / 按 id 筛选 / 只看清单
python "$SKILL_DIR/scripts/fault_inject.py" --skill-root "$SKILL_DIR" --out /tmp/f --form dependency
python "$SKILL_DIR/scripts/fault_inject.py" --skill-root "$SKILL_DIR" --out /tmp/f --only D13,D18,D21
python "$SKILL_DIR/scripts/fault_inject.py" --list
```

**读到什么算什么**：每条记录都含 `exit_code`、`status`、`uncertainty`、
`fail_checks`、`warn_checks`、stdout 尾部，部分条目还带**独立复核器**结论
（`validate_result.py` / `spec_lint.py`）。退出码 `0` 表示 25 条全部符合期望。

**恢复动作对照表**（矩阵里每一条都能对到一句话）：

| 实测到的产物 | 含义 | 恢复动作 |
|-|-|-|
| `exit 2`，无 `result.json` | 输入层根本性失败 | 修 case/材料路径，再跑；重试无意义 |
| `exit 1` + `status=failed` + `fails=[pipeline]` | 清单缺失 / 依赖缺失 / 渲染异常；**产物目录保留** | 按 `uncertainty[0]` 的原文定向修复后重跑 |
| `exit 1` + `status=partial` + `spec_lint.spec.*` | 生成前门拦下的结构错误 | 回材料改清单（kind/端点/分组），重跑 CP1 |
| `exit 0` + `warns=[…]` | 可继续但已降级 | 读 warn 原文；能补则补，不能补就写进 `uncertainty` 交付 |
| `exit 0` + 无任何 fail/warn | **必须核对 §7 盲区表**：可能是真的没问题，也可能落在已知盲区 | 走人工门（逐份读材料 / 逐条核对 from-to） |

## 6. 本轮注入发现的三个真实缺陷（两个纯增量 + 一处文档更正）

| # | 缺陷 | 修复前实测 | 增量 | 修复后实测 |
|-|-|-|-|-|
| 1 | `relation-dict.json` 损坏 ⇒ `json.load` 异常冒泡 | `exit 1` + 裸 `JSONDecodeError`，**连 `result.json` 都不写** | `main.py` 读字典处包 `try/except`；`summarize()` 后补一条 `spec_lint.corpus` warn（+18/−2 行） | `exit 0` / `success` / `warns=[spec_lint.corpus]`，图稿照常交付 |
| 2 | 缺 matplotlib / Pillow ⇒ import 期直接崩 | `exit 1` + 裸 `ModuleNotFoundError`，**无 `result.json`** | `import render` / `import checks` 各包 `try/except` + 解析 case 后加一道依赖门调用既有 `_write_failed_result`（+27/−5 行） | `exit 1` / `failed` / `fails=[pipeline]` / `uncertainty` 写明缺失模块与安装提示 |
| 3 | `--edit-svg` 分支把 `edit_from_svg()` 返回的编辑问题**整个丢掉** | 错误字段名夹具：`exit 0` / `success` / `change_records=0`，**stdout 连 `[edit] …` 都没有**（旧文档却写着"会打印"） | `main.py`：该分支收集 `ed_issues` 并打印，同时写进 `result.json.uncertainty`（+8/−1 行） | 同一夹具 → `uncertainty` 出现 `edit issue: edit.relabel`；正常夹具仍 `change_records=3` |

两条都**没有改动** `main.py` 的 CLI 参数名、默认值或退出码语义；改动逐条
记录在 `references/FAULT-MATRIX.md` §5。其余 13 个脚本**逐字节未动**。

## 7. 已知盲区（本包拦不住的故障，公开在此）

| # | 盲区 | 实测证据 | 缓解手段 |
|-|-|-|-|
| A1 | 材料**内容**不可读（存在但是二进制垃圾） | D02：`exit 0` / `success` / 0 fail / 0 warn | S1 的"逐份读实际文件"人工门；读不到必须手写进 `uncertainty` |
| A2 | 关系**方向**对调（端点与 kind 都合法） | D09b：`exit 0` / `success`，`spec_lint` 全 ok | 逐条回材料核对 `from/to`；SVG 的 `data-relation`/`data-source` 可 grep 复核；语义正确性最终由题面所说的 native/LLM Judge 承担 |
| A3 | 独立 `spec_lint.py` CLI 对损坏字典仍会崩 | D13 的复核：`spec_lint exit=1`，`JSONDecodeError` | 该脚本逐字节未动（只在 `main.py` 侧兜）；`--only D13` 可复现，属公开限制 |
| A4 | 缺 Pillow 与缺 matplotlib 不可分辨 | D18/D19 同为 `exit 1` / `failed` | `uncertainty` 里写明缺失模块名 |
| A5 | `--skip-checks` / `--no-lint` 让"未检查"像"已通过" | 未注入（属自选降级） | §9 自查强制：交付前必须用默认参数完整重跑一次 |
| A6 | 加密 PDF 时主流程本身仍 `exit 0` | D15：主流程 `0/success`，`pdftext.py` `exit 2` | 硬性要求 PDF 必须先过 `pdftext.py` 并如实记录 |

> 完整 25 行矩阵（含每条的命令、退出码、`status`、`uncertainty`、
> fail/warn 检查名、是否静默）见 `references/FAULT-MATRIX.md`。

## 8. 资源文件说明（路径相对技能根，调用一律 `"$SKILL_DIR/..."`）

| 入口 | 角色 | CLI |
|-|-|-|
| `scripts/main.py` | 流水线入口（含依赖门与字典兜底） | `--case --manifest --out --work --edit-svg --base-name --exports --dpi --skip-checks --lint --no-lint --fixed-time --doc-check` |
| `scripts/fault_inject.py` | **本版新增**：四形态故障注入与恢复演练（只动包外副本） | `--skill-root --out --form --only --json --quiet --keep --list` |
| `scripts/extract.py` | 材料 → 候选 ER 清单草稿 | `--inputs --out --base-dir` |
| `scripts/pdftext.py` | PDF 文本抽取（fitz→pypdf→PyPDF2→stdlib 四段回退，backend 如实记录） | `--pdf --out` |
| `scripts/textfont.py` | 字体栈探测（CJK 可用性事实源） | `--list --probe` |
| `scripts/spec_lint.py` | CP1 生成前 lint | `--manifest --dict --json` |
| `scripts/manifest.py` | ER 清单加载/规范化 | `<manifest.json>` |
| `scripts/layout.py` / `scripts/svgbuilder.py` / `scripts/render.py` / `scripts/checks.py` | 布局 / 分层 SVG / 镜像渲染 / 产物检查（库模块） | — |
| `scripts/edit.py` | 源文件级增量编辑 | `<figure.svg> <edits.json>` |
| `scripts/validate_result.py` | 契约独立校验 G1–G8 | `--case --result --out --json` |
| `scripts/selftest.py` | 模块级自测（35 项） | — |
| `scripts/run_examples.py` | 一键复现三示例（schematic/chart/edit + 各跑 G1–G8） | `--out --keep` |
| `scripts/report.py` | 结果装配（库模块） | — |
| `scripts/doccheck.py` | 文档承诺 ↔ 脚本事实 的只读对拍 | `--root --files --json` |
| `references/FAULT-MATRIX.md` | **本版新增**：25 行实测矩阵 + 6 条盲区 + 2 条缺陷修复记录 | — |
| `references/OUTPUT_CONTRACT.md` | `result.json` 契约 + G1–G8 + 四形态回显（**字段块逐字不变**） | — |
| `references/failure-modes.md` | 题面 12 类失败形态 → 检测机制 → 处置 | — |
| `references/CHECK-INDEX.md` | 全部检查名清单（级别 + 科学含义） | — |
| `references/EDIT-ACTION-SCHEMA.md` | 编辑动作 → 字段名 → 记录 的对照表与反模式 | — |
| `references/ER_MANIFEST.md` | 实体—关系清单规范（绘图唯一数据源） | — |
| `references/DRAWING_GRAMMAR.md` | 图形语法：关系语义 → 箭头/线型/颜色、方向判定、分组/层级 | — |
| `references/RUBRIC_MAP.md` | 五维评分 → 本包文件/机制逐条映射 | — |
| `assets/relation-dict.json` | 连接规则字典（kind→arrow/line/dash/color，机器可读） | — |
| `assets/checklist.json` | CP1–CP5 检查点 + 自查清单（机器可读） | — |
| `examples/*` | 最小示例（schematic / chart / edit + 合成材料 + `EXPECTED-OUTPUT.md`），**示例非正式案例** | — |

## 9. 五维评分映射（完整表见 `references/RUBRIC_MAP.md`）

| 维度 | 分 | 本包机制（可跑的检查，不是自述） | 证据文件 |
|-|-|-|-|
| 实际效果 | 40 | 材料 → ER 清单 → CP1 → 可编辑 SVG → PNG/PDF → `result.json` 一条命令跑通；`fault_inject.py` 的 25 条注入证明这条链路在坏输入下**仍然留下可核验产物** | `scripts/main.py`、`scripts/spec_lint.py`、`scripts/checks.py`、`references/FAULT-MATRIX.md` |
| 使用增益 | 25 | 故障矩阵把"返工点"提前：25 类坏法各自的退出码/status/痕迹固定，接手者不必猜；`--only` 可只跑相关几条；恢复动作对照表把"看到什么 → 做什么"写死 | `scripts/fault_inject.py`、§5、`TEST.md` |
| 创新增益 | 15 | ①**可运行的失败注入器**（四形态 × 25 条，只动包外副本）②**静默失败判据**（exit 0 + success + 无痕迹 ⇒ 判为失效）③**独立复核器交叉验证**（主流程说 ok ≠ 契约门说 ok：D23 就是这么被抓出来的）④注入**发现并修掉**两个真实缺陷 | `scripts/fault_inject.py`、`references/FAULT-MATRIX.md` §4/§5/§6 |
| 可靠体验 | 10 | 25/25 符合期望、0 静默；§7 六条盲区公开；退出码 0/1/2 与 `status` 同向；依赖门让"缺库"也留下 `failed` 记录 | `references/FAULT-MATRIX.md`、`scripts/main.py`、`references/failure-modes.md` |
| 生态贡献 | 10 | 矩阵可被任何同族技能复跑（`--skill-root` 指向任意包根）；`fault-matrix.json` 是机器可读的对照基线；检查名索引 + 连接规则字典 + 三示例题集 + 契约校验器可直接复用 | `references/*`、`assets/*`、`scripts/doccheck.py` |

## 10. 依赖与限制

- Python 3.9+（实测 3.13.9）；运行必需 **matplotlib / Pillow / numpy**，
  reportlab 可选；缺 matplotlib 或 Pillow 时**不会裸崩**，而是写 `failed`
  的 `result.json` 并提示 `pip install matplotlib pillow numpy`；
- PDF 抽取按 fitz → pypdf → PyPDF2 → **stdlib 回退**逐级降级，无第三方库
  也能抽（backend 记 `stdlib`，并注明**不重建版面**）；
- 无 cairosvg/svgwrite：PNG/PDF 是与 SVG 同源的 matplotlib 镜像
  （**语义一致、非逐像素**），该降级写进 `uncertainty`；
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
  `fault_inject.py` 只覆盖
  **注册过的 25 条**注入，不代表穷尽所有故障（§7 盲区已公示）。

## 11. 自查清单（提交前逐行确认；机器版 `assets/checklist.json`）

- [ ] 实体名逐字出自材料，无材料外基因/浓度/时间点/单位；
- [ ] 每个关系方向与材料一致（激活≠抑制、上下游不颠倒、包含用分组）；
- [ ] CP1 `{"valid": true}`：kind 可映射、containment 用分组、图例双向、
      调色板 ≥ 类别数；
- [ ] 数值/坐标/单位与数据表逐项一致，改数据后图确实重绘；
- [ ] `figure.svg`：文字可选（`<text>`）、图层可拆（`layer-*`）、带 `id`
      与 `data-*`、内嵌 ER 清单；
- [ ] 导出件：PDF 可打开；PNG 有效 DPI 达标；色彩 RGB 族；
- [ ] `result.json` 含全部契约键 + `case_id`，四形态回显无 `null`；
- [ ] `validate_result.py`（G1–G8）输出 VALID，退出码 0；
- [ ] 编辑任务：请求条数 == `change_records` 条数，未改动元素保持原样；
- [ ] **故障演练过**：`fault_inject.py` 退出码 0（25/25 符合期望），
      且本次交付的运行**没有** `--skip-checks` / `--no-lint`；
- [ ] §7 盲区表里与本次案例相关的行（尤其 A2 方向核对）已人工走过一遍，
      结论写进 `uncertainty`；
- [ ] 形态：仅 7 种文本扩展名、无 `__pycache__`、≤50 文件、≤500KB/文件、
      ≤2MB、包内无本机绝对路径。

## 12. 禁止事项

- 不提交预制答案/正式案例输出；示例只用于演示接口与流程，**示例产物不入包**；
- 不编造缺失的软件状态或科学数据（来源里没有的实体/数值一律不画）；
- **不把"没检查过"说成"检查通过"**：`--skip-checks` / `--no-lint` 的运行
  不得作为交付版本；字典加载失败必须留下 `spec_lint.corpus` warn；
- 不宣称未经实测的恢复能力：`references/FAULT-MATRIX.md` 里没有的行，
  不许在别处声称"已验证"；
- 不为"好看"改关系颜色（改色 = 图例不一致）。
