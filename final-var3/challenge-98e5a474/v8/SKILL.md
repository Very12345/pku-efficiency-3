---
name: scientific-schematic-editor
description: >-
  Generate and edit editable scientific schematics, mechanism/relationship
  diagrams, flow diagrams and data charts from source materials — and prove the
  output contract holds for ANY declaration shape. This build (v8) leads with a
  runnable contract matrix (scripts/contract_matrix.py): 31 injections over the
  six container forms (string/array/object/number/boolean/nested) crossed with
  boundary values (empty string, empty array, 0, over-long, literal numbers,
  null, invalid types, missing/malformed output_contract) each run through the
  real pipeline plus the independent contract validator, recording the actual
  exit code, status, echoed value and type, G5 verdict, and whether the row
  PASSED SILENTLY (validated, but the declaration was never honoured). Extracts
  an entity-relation manifest traceable to sources, draws a layered editable SVG
  source plus PNG/PDF exports, runs CP1 plan-lint and export-compliance checks,
  and writes a result.json carrying every output_contract field. Use when a task
  asks to draw, regenerate or edit a scientific figure from papers, tables or
  notes: 科研示意图/机制图/信号通路图/流程图/实验装置图/图表的生成与编辑, or
  when a caller-supplied output contract must be honoured key by key.
  Order: read the contract → read the real files → extract ER → lint the plan
  (CP1) → draw → check (CP2) → edit and re-check (CP4) → contract gate (CP3) →
  contract matrix (CP6).
---

# scientific-schematic-editor —（v8 · 契约四形态 × 边界值矩阵版）

本版把"**平台给的 `output_contract` 我们一定回显对**"从一句承诺变成**可运行的
31 行注入矩阵 + 逐行实测 + 静默通过清单**：新增 `scripts/contract_matrix.py`，
把六种容器形态 × 边界值 × 非法类型 × 缺字段逐个注入 `case.json`，每行真跑一次
主流程与一次独立契约校验器，记录**实测**退出码 / `status` / 回显值（含类型）/
G5 判定 / 是否静默通过。逐行表与边界结论在 `references/CONTRACT-MATRIX.md`。

| 段 | 一句话 | 权威文件 |
|-|-|-|
| ① 输入与契约 | 平台给什么、四形态回显规则、契约管不到的三件事 | §1、`references/OUTPUT_CONTRACT.md` |
| ② 执行 | S0–S7 一步一条命令，五个检查点 | §2 |
| ③ **契约矩阵（本版主轴）** | 31 行注入 × 判据 K1–K6 + **16 行静默通过**逐条点名 | §3、`references/CONTRACT-MATRIX.md`、`scripts/contract_matrix.py` |
| ④ 失败与降级 | 四形态 25 条注入实测（0 条静默）+ 六条公开盲区 | §4、`references/FAULT-MATRIX.md`、`references/failure-modes.md` |
| ⑤ 契约与复核 | G1–G8 硬门 + 独立校验器（自说 success 不算数） | §5 |
| ⑥ 增益 / 机制 / 复用 | 真实读数在哪、哪些没测 | §6、`references/STRENGTH-AXES.md`、`references/CASE-SET.md` |

**本技能不做**：统计方法的数值计算与选择、海报/封面版式、艺术插画美化、论文正文写作。
数据表里的数值是**事实输入**：不改算、不补造、不换算单位。

---

## ① 输入与契约（本版的读法）

| 路径 | 内容 | 读法 |
|-|-|-|
| `/input/case.json` | `case_id` / `workorder` / `figure_type` / `sources` / 可选 `manifest`、`entities+relations`、`data`、`edits`、`edit_requests`、**`output_contract`** | **以文件实际内容为准**；`output_contract` 必须是**非空对象**，否则契约门整段跳过（见 §3 判据 K5） |
| `/input/task.md` | 任务书 | 与 case 冲突时以任务书 + 材料原文为准 |
| `/input/` 下的材料 | 可能是 PDF | 先过 `scripts/pdftext.py`（加密件会被明确拒绝，不出空文本） |

**四形态回显规则（唯一权威 = `references/OUTPUT_CONTRACT.md`）**

| 声明 | 回显 | 实测（31 行矩阵） |
|-|-|-|
| `"string"` / `"text"` / `"str"` | `""` | R01 |
| `"array"` / `"list"` / `"sequence"` | `[]` | R02、R10 |
| `"object"` / `"dict"` / `"map"` | `{}` | R03、R11 |
| `"number"` / `"int"` / `"float"` | `0` | R04、R12 |
| `"boolean"` / `"bool"` | `false` | R05 |
| 已在 `result.json` 里非空的键 | **不回显**（保留真实值） | R24–R26（类型冲突 ⇒ G5 INVALID） |
| 声明的值是 `null` | 回显 `null` ⇒ **G5 必须 INVALID** | R16 |

**契约管不到的三件事（本版逐条实测，写在这里免得踩）**

1. **未知类型词**被静默当字符串（`"whatever"`、`""`、`"null"`、超长串）⇒ 见 §3 的 S1；
2. **值形状**（数组元素类型、对象内部字段）没有任何门在查，结构化提示会被降级成空容器
   ⇒ 见 §3 的 S3；
3. **顶层 `output_contract` 形状非法**（缺失 / `null` / `[]` / 字符串 / `{}`）时契约门
   **整段跳过** ⇒ 见 §3 的 S4（这一条最危险：它让"没有契约"与"契约满足"不可区分）。

---

## ② 执行：S0–S7 与合同检查点

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
| **S0** | 读任务书与 case；**先确认 `output_contract` 是非空对象**；解析四形态；确认输出/工作目录 | **CP6 前置** | case 不可解析 ⇒ `exit 2`；契约形状非法 ⇒ 记 `uncertainty`（§3 S4） |
| **S1** | 逐份读真实材料；PDF 先过 `pdftext.py`；读不到的记 `uncertainty` | — | 加密件 `exit 2`；扫描件 `chars: 0`；缺库走 stdlib 回退 |
| **S2** | `extract.py` 产候选草稿（`_draft`）；人工复核后写 `entities.json` | — | 草稿进 CP1 会被判 INVALID |
| **S3** | `spec_lint.py --manifest …` | **CP1** | 结构错 ⇒ `exit 1` + `partial` + `spec.relation_kind` / `spec.containment_group` fail |
| **S4** | `main.py --case … --manifest … --work … --out …` | — | 依赖缺失 ⇒ `exit 1` + `failed` 的 result.json |
| **S5** | 溯源比例、图例双向、数据映射、导出预检（DPI/色彩/`<text>`/PDF/字体） | **CP2** | 字体缺失 ⇒ `font.cjk` warn + `uncertainty` |
| **S6** | `--edit-svg` 源文件级增量修改；改完重跑 CP2 + CP3 | **CP4** | 字段名错 ⇒ 请求条数 ≠ `change_records` 条数 |
| **S7** | `validate_result.py`（G1–G8）→ VALID；**再跑契约矩阵确认回显形态** | **CP3 / CP6** | 契约形状错 ⇒ 独立校验器 INVALID；静默通过 ⇒ 按 §3 清单显式处置 |

**退出码语义（与 `status` 同向）**：`0` = `success`（允许已被 `acknowledged_issues`
核可的 warn）；`1` = `partial`/`failed`（**一定写出** result.json）；`2` = 致命
（case 无法定位/解析、编辑目标无内嵌清单、输入层不可用，**不写出**）。

---

## ③ 契约矩阵（本版主轴）：31 行注入 + 静默通过清单

**一条命令**（`--out` 必须在包外）：

```bash
SKILL_DIR="$(cd "$(dirname "<本 SKILL.md 的实际路径>")" && pwd)"
RUN="<包外临时目录>"

python "$SKILL_DIR/scripts/contract_matrix.py" --list
python "$SKILL_DIR/scripts/contract_matrix.py" --skill-root "$SKILL_DIR" --out "$RUN/cm"
python "$SKILL_DIR/scripts/contract_matrix.py" --skill-root "$SKILL_DIR" --out "$RUN/cm" --json
python "$SKILL_DIR/scripts/contract_matrix.py" --skill-root "$SKILL_DIR" --out "$RUN/cm" --only R13,R17,R27
```

**判据 K1–K6**（`contract_matrix.py` 的退出码按 K1/K2 判；K3–K6 是逐行读数）

| 判据 | 内容 | 实测 |
|-|-|-|
| **K1** | 每一行都必须拿到可判定读数（VALID 或 INVALID 都算） | **31/31**，`unmeasurable = 0` ⇒ 退出码 0 |
| **K2** | 每行都必须写出 `result.json`（不许"崩了还没记录"） | 31/31 写出 |
| **K3** | 声明为 `null` 的键必须让契约门判 **INVALID** | R16 ⇒ INVALID（`G5 contract key x_none is null`） |
| **K4** | 契约键与既有字段**类型冲突**必须让契约门判 **INVALID** | R24/R25/R26 ⇒ INVALID（`expected str, got list` 等） |
| **K5** | 顶层 `output_contract` 形状非法 ⇒ **G5 整段跳过**（本版把它记成 S4 静默，并要求 S0 显式处置） | R27–R31 ⇒ VALID + S4 |
| **K6** | VALID 但声明未被兑现的每一行都必须逐条点名（S1/S2/S3/S4） | **16 行**（详见下表） |

**实测汇总（`contract-matrix.json.summary`）**

| 计数 | 值 |
|-|-|
| 行数 / 已测量 / 无法测量 | **31 / 31 / 0** |
| VALID / INVALID | **27 / 4** |
| **静默通过** | **16**（R06 R07 R09 R13 R14 R15 R17 R18 R21 R22 R23 R27 R28 R29 R30 R31） |
| `main_exit == 0` | **31/31** |
| `status` 分布 | `{"success": 31}` —— 契约形状问题**从不**降级 `status`（要靠契约门发现） |
| 形态 / 边界覆盖 | 12 种形态 · 24 种边界 |
| 矩阵墙钟 | 67 秒（31 行 × 主流程 + 校验器，每行独立 scratch 副本） |

**静默通过的四类（本版核心结论，逐条给出 Agent 侧缓解）**

| 静默 | 命中行 | 被静默接受的是什么 | 缓解 |
|-|-|-|-|
| **S4** | R27–R31 | 顶层契约形状非法 ⇒ G5 整段跳过 | S0 必须确认 `output_contract` 是非空对象；否则写 `uncertainty` 并逐键人工核对 |
| **S1** | R17 R18 R09 R15 | 未知类型词被当字符串（回显 `""`） | 只信五个识别的词（string/array/object/number/boolean）；清单到手后逐键核对，不在词表里的键在交付说明里点名 |
| **S3** | R06 R07 R21 R22 R23 | 结构化提示（嵌套对象/带元素数组）降级为空容器 | 值形状靠 `OUTPUT_CONTRACT.md` 字段表 + G4 类型检查兜，不靠 `output_contract` |
| **S2** | R13 R14 | 字面量被当"类型"：声明 `12` 回显 `0`、声明 `true` 回显 `false` | 见到字面量按"类型不确定"处理并记 `uncertainty` |

> **R08 的键数证据**：五形态同时声明 ⇒ `result.json` 顶层键 **26**（基线 21 + 5）；
> R27–R31 无契约 ⇒ **21**。这是"契约键真的进了顶层"的机器可核对读数。
> **R20 的体量证据**：`summary` 约 210KB ⇒ `result.json` **219,556 B**（仍低于 500KB 上限，
> 但足以说明"契约回显 + 大文本"会放大产物；超限行为**未测**）。

---

## ④ 失败与降级（四形态 25 条注入实测）

```bash
python "$SKILL_DIR/scripts/fault_inject.py" --skill-root "$SKILL_DIR" --out "$RUN/fi"
python "$SKILL_DIR/scripts/fault_inject.py" --skill-root "$SKILL_DIR" --out "$RUN/fi" --list
```

- **留痕律**：出了问题必须留下机器可读痕迹 —— 非零退出码、`status`、
  `verification.checks.fails/warns`、`uncertainty` 至少命中一个；四者全空 = 静默失败 = 本技能失效；
- **出口一致律**：CLI 退出码与 `result.json.status` 必须同向。

实测 **25/25 符合期望、0 条静默失败**。契约矩阵与故障矩阵互补：
前者问"**声明形状**变了会怎样"，后者问"坏输入有没有留痕"。

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
**注意**：本版实测证明 G5 **只在 `output_contract` 是非空对象时才运行**（§3 K5/S4），
所以"VALID"必须与"契约真的存在且被逐键核对"一起看。

---

## ⑥ 增益 / 机制 / 复用：真实读数在哪、哪些没测

- **增益读数**（F1–F8 / I1–I10 / R1–R13）在 `references/STRENGTH-AXES.md` §A；本包**没有**
  跑"不加载 Skill 的基线臂"，因此**不声称**"比基线得分更高"；
- **机制**（M1–M5）在 `references/STRENGTH-AXES.md` §B；本版新增的契约矩阵是
  **M1（方案先行）在输出侧的镜像**：输入形状没核对清楚，后面画得再对也可能交不上；
- **可复用资产** A1–A12 与采纳阶梯在 `references/STRENGTH-AXES.md` §C；本版新增资产：
  **契约矩阵执行器**（对任意同族技能包跑 `--skill-root <别的包> --base-case <别的 case>` 即可复用）；
- **跨题材题集**在 `references/CASE-SET.md`；
- **未测量**：平台真实 `output_contract` 字段清单、`oneOf`/联合类型、值形状（元素类型）、
  并发与中断、`result.json` 超 500KB 后的平台行为、chart/edit 基线的契约交互 —— 一律按"未测量"处理。

---

## ⑦ 资源清单（路径相对技能根，调用一律 `"$SKILL_DIR/..."`）

| 入口 | 角色 | CLI |
|-|-|-|
| `scripts/main.py` | 流水线入口（含依赖门 + 字典兜底） | `--case --manifest --out --work --edit-svg --base-name --exports --dpi --skip-checks --lint --no-lint --fixed-time --doc-check` |
| `scripts/contract_matrix.py` | **契约四形态 × 边界值矩阵（本版主轴）** | `--skill-root --out --base-case --only --list --json --quiet --keep --timeout` |
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
| `references/CONTRACT-MATRIX.md` | **本版主轴**：判据 S1–S5 · 逐行实测表（31 行）· 静默通过清单 · 未覆盖声明 |
| `references/OUTPUT_CONTRACT.md` | `result.json` 契约 + G1–G8 + 四形态回显（字段块逐字不变） |
| `references/FAULT-MATRIX.md` | 25 行实测注入矩阵 + 六条盲区 + 既有缺陷的修复前后对照 |
| `references/CASE-SET.md` | 题集（逐案输入/期望/区间/难度）+ 逐案实测 + 六条泛化边界 |
| `references/STRENGTH-AXES.md` | §A 对照协议 F1–F8 / I1–I10 + §B 机制 M1–M5 + §C 可复用资产 A1–A12 |
| `references/failure-modes.md` | 题面 12 类失败形态 → 检测 → 处置 → 档位 → 恢复条件 |
| `references/CHECK-INDEX.md` | 全部检查名清单（doccheck 事实源 / 机制判据来源 / 指标取值来源） |
| `references/EDIT-ACTION-SCHEMA.md` | 编辑动作 → 字段名 → 记录 的对照表、实测矩阵、反模式 |
| `references/ER_MANIFEST.md` / `references/DRAWING_GRAMMAR.md` | 清单规范 / 图形语法 |
| `references/RUBRIC_MAP.md` | 五维评分 → 本包文件/机制逐条映射（含本版契约轴的落点） |
| `assets/relation-dict.json` / `assets/checklist.json` | 连接规则字典 / CP1–CP5 自查清单（机器可读） |
| `examples/*` / `examples/cases/*` | 包内三示例 + 两个不同题材的合成案例 |

---

## ⑧ 自查清单（提交前逐行确认；机器版 `assets/checklist.json`）

- [ ] **`case.json` 的 `output_contract` 是非空对象**（判据 K5/S4：形状非法时契约门整段跳过）；
- [ ] 契约每个键都能在 `result.json` 顶层找到，且**类型形状**与声明一致（判据 K6）；
- [ ] 没有 `null` 回显（判据 K3）；没有与既有字段的类型冲突（判据 K4）；
- [ ] 契约矩阵跑过且 `unmeasurable == 0`；**16 行静默清单逐条对照过**，与本次真实契约无关的可以忽略，相关的写进交付说明；
- [ ] 实体名逐字出自材料；关系方向与材料一致；CP1 `{"valid": true}`；
- [ ] 数值/坐标/单位与数据表逐项一致，**绝不换算单位**；
- [ ] `figure.svg`：文字可选（`<text>`）、图层可拆、带 `id` 与 `data-*`、内嵌 ER 清单、良构 XML；
- [ ] 画布预算核过（`style.canvas` 显式声明时布局不再自动扩展）；
- [ ] 导出件：PDF 可打开；PNG 有效 DPI 达标；`artifact.<role>` 逐类核过；
- [ ] `validate_result.py`（G1–G8）输出 VALID，退出码 0；
- [ ] 编辑任务：请求条数 == `change_records` 条数；
- [ ] **故障演练过**：`fault_inject.py` 退出码 0（25/25）；**题集跑过**：`case_probe.py` 退出码 0（10/10）；
- [ ] 交付前最后一次运行**没有** `--skip-checks` / `--no-lint`；
- [ ] 形态：仅 7 种文本扩展名、无 `__pycache__`、≤50 文件、≤500KB/文件、≤2MB、包内无本机绝对路径。

---

## ⑨ 依赖与限制

- Python 3.9+（实测 3.13.9）；运行必需 **matplotlib / Pillow / numpy**，reportlab 可选；
  缺 matplotlib 或 Pillow 时**不会裸崩**，而是写 `failed` 的 `result.json` 并提示
  `pip install matplotlib pillow numpy`；
- `contract_matrix.py` **只用标准库**（含 `--timeout` 逐行超时保护），不引入新依赖；
- PDF 抽取按 fitz → pypdf → PyPDF2 → **stdlib 回退**逐级降级；无 cairosvg/svgwrite：
  PNG/PDF 是与 SVG 同源的 matplotlib 镜像（**语义一致、非逐像素**，写进 `uncertainty`）；
- **平台运行契约**：技能装在 `/skills/weekly-skill`；输入 `/input/case.json` + `/input/task.md`；
  中间产物 `/app/work`；最终产物 `/app/output`；预算 64 次模型请求 / 900 秒 / 16384 token
  per response（一次契约矩阵 ≈ 67 秒，评分轮不必跑；它用于**交付前自证**）；
- **资源形态（硬约束）**：包内只放 UTF-8 文本（`.md/.py/.json/.txt/.csv/.yaml/.yml`），
  ≤50 个文件、单文件 ≤500KB、合计 ≤2MB、无符号链接；图稿与渲染件一律运行时生成；
- **已知限制（如实标注）**：契约门的 G5 只覆盖**顶层容器类型**；值形状、联合类型、
  平台真实字段清单**未测量**；`extract.py` 只产草稿；走 `--edit-svg` 时 `edits` 与
  `edit_requests` 两个字段都生效（`edits` 优先），真正的坑是字段名写错。

## ⑩ 禁止事项

- 不提交预制答案/正式案例输出；示例与新案例只演示接口与流程，**产物不入包**；
- 不编造缺失的软件状态或科学数据（来源里没有的实体/数值一律不画）；
- **不把"没检查过"说成"检查通过"**：`--skip-checks` / `--no-lint` 的运行不得作为交付版本；
  契约缺失或形状非法时**必须**写进 `uncertainty`，不许当作"无契约 ⇒ 无需回显"；
- **不把"静默通过"说成"契约没问题"**：16 行静默清单是本版的核心结论，必须逐条对照；
- **不声称没测过的能力**：平台分数、平台真实契约字段清单、`oneOf` 联合类型、值形状、
  并发/中断、`result.json` 超 500KB 的行为、chart/edit 基线的契约交互均为"未测量"；
- 不为"好看"改关系颜色（改色 = 图例不一致）。
