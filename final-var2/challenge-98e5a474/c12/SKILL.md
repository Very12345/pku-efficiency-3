---
name: scientific-schematic-editor
description: >-
  Generate and edit editable scientific schematics, mechanism/relationship
  diagrams, flow diagrams and data charts from source materials. Extracts an
  entity-relation manifest (traceable to sources), draws a layered editable
  SVG source plus PNG/PDF (and TIFF/EPS) exports, runs CP1 plan-lint and
  legend/data-mapping and export-compliance checks, and writes a structured
  result.json with all output_contract fields. Use when a task asks to draw,
  regenerate or edit a scientific figure from papers, tables or notes:
  科研示意图/机制图/信号通路图/流程图/实验装置图/图表的生成与编辑.
  Execute in order: read actual files → extract ER (draft via scripts) →
  write/lint manifest (CP1) → main.py draw → checks (CP2) → edit & re-check
  (CP4) → contract gates (CP3) → self-check & determinism (CP5).
---

# scientific-schematic-editor — 科研示意图生成与编辑 · 整合版（决策层 + 增益层）

> 本包整合了基线 Skill 与 2 个强化层,各层对应不同的评分维度:可靠体验 10 + 实际效果 40 · 使用增益 25。
> 各层内容**不重复**:决策层给规则与失败分支;增益层给对照协议与指标口径;机制层给机制说明与可复用资产。
> 建议使用顺序:先用「决策层」跑通并处理异常,再用「增益层」证明并度量改善,最后用「机制层」复用与扩展。
> 各层的原始文件都完整保留在本包内,不是摘要 —— 下面每一层都是可以独立执行的完整规范。

## 本包文件索引

- `GITHUB_URL.txt`
- `README.md`
- `TEST.md`
- `assets/checklist.json`
- `assets/relation-dict.json`
- `examples/EXPECTED-OUTPUT.md`
- `examples/README.md`
- `examples/case.json`
- `examples/case_chart.json`
- `examples/case_edit.json`
- `examples/task.md`
- `references/CHECK-INDEX.md`
- `references/DRAWING_GRAMMAR.md`
- `references/EDIT-ACTION-SCHEMA.md`
- `references/ER_MANIFEST.md`
- `references/GAIN-PROTOCOL.md`
- `references/OUTPUT_CONTRACT.md`
- `references/RUBRIC_MAP.md`
- `references/failure-modes.md`
- `scripts/checks.py`
- `scripts/doccheck.py`
- `scripts/edit.py`
- `scripts/extract.py`
- `scripts/layout.py`
- `scripts/main.py`
- `scripts/manifest.py`
- `scripts/pdftext.py`
- `scripts/render.py`
- `scripts/report.py`
- `scripts/run_examples.py`
- `scripts/selftest.py`
- `scripts/spec_lint.py`
- `scripts/svgbuilder.py`
- `scripts/textfont.py`
- `scripts/validate_result.py`
- `examples/sources/data-table.csv`
- `examples/sources/figure03-note.md`

---

# 【决策层】决策规则与失败分支（目标维度:可靠体验 10 + 实际效果 40）

---
name: scientific-schematic-editor
description: >-
  Generate and edit editable scientific schematics, mechanism/relationship
  diagrams, flow diagrams and data charts from source materials. Extracts an
  entity-relation manifest (traceable to sources), draws a layered editable
  SVG source plus PNG/PDF (and TIFF/EPS) exports, runs CP1 plan-lint and
  legend/data-mapping and export-compliance checks, and writes a structured
  result.json with all output_contract fields. Use when a task asks to draw,
  regenerate or edit a scientific figure from papers, tables or notes:
  科研示意图/机制图/信号通路图/流程图/实验装置图/图表的生成与编辑.
  Execute in order: read actual files → extract ER (draft via scripts) →
  write/lint manifest (CP1) → main.py draw → checks (CP2) → edit & re-check
  (CP4) → contract gates (CP3) → self-check & determinism (CP5).
  Every branch has a decision id (D) and a degradation level (L0-L3).
---
## scientific-schematic-editor — 科研示意图生成与编辑（决策系统版）

本技能把科研案例的**来源材料**变成**可编辑图稿 + 合规导出件 + 可核验记录**。
它写成一套**决策系统**：不假设输入干净、环境齐备、编辑请求一定合法，而是
**先把可能出岔子的地方枚举成规则（D），再给每条规则配上降级档位（L）**。

三条主张（与评分维度一一对应）：

1. **图画对** — 实体、关系、方向、数值、单位逐条可回溯到材料；
2. **图可改** — 文字可选、图层可拆、SVG 内嵌 ER 清单，编辑只动被指明的元素；
3. **图能投** — 导出前合规检查自动执行，失败分支有明确档位与记录。

**本技能不做**：统计计算的数值方法选择、海报/封面版式、艺术插画美化、
论文正文写作。数据表里的数值是**事实输入**，不改算、不补造、不换算单位。

> 与基线包的结构差异：本包把"决策"提到正文主线。执行步骤（§4）只保留
> **动作与检查点编号**，每条边界情况一律回指 §3 的 D 规则；边界情况不再
> 散落在"异常处理速查"里，而是与 D 规则、降级档位、脚本检查名**四点对齐**。

### 1. 适用条件

- 任务是"科研示意图/机制图/通路图/流程图/实验装置图/数据图"的**绘制或编辑**，
  workorder 一般形如 `editable_relationship_schematic`；
- 有来源材料（论文图注/正文摘录/Markdown/CSV/PDF），或要求对已有图稿做
  **源文件级**修改；
- 交付要求包含可编辑源文件、导出件与结构化结果（`result.json`）。

### 2. 输入、输出与责任边界

**输入（平台提供，路径固定）**

| 路径 | 内容 | 读法 |
|-|-|-|
| `/input/case.json` | `case_id` / `workorder` / `figure_type` / `sources` / 可选 `manifest`、`entities+relations`、`data`、`edits`、`output_contract` | **以文件实际内容为准，不凭字段名猜语义** |
| `/input/task.md` | 具体任务书 | 与 case.json 冲突时以任务书+材料原文为准（D3） |
| `/input/` 下的材料 | 可能是 PDF | 先过 `scripts/pdftext.py`（D11/D12） |

**输出（全部运行时现场生成，写入 `/app/output`）**

```
/app/output/
├── figure.svg      # 可编辑分层源文件（文字均为 <text>，带 id / layer / data-*）
├── figure.png      # 渲染预览（matplotlib 镜像同一 layout+manifest）
├── figure.pdf      # 矢量导出件
├── result.json     # 结构化结果（OUTPUT_CONTRACT 全字段 + case_id）
└── work/           #（或 /app/work）中间产物：entities.json / draft / layout
```

| role | format | 是什么 | 完成标准 |
|-|-|-|-|
| `figure` | svg | 可编辑分层源文件 | 文字是真实 `<text>`（未被 path 化）、语义图层可拆、带 `id`/`data-*`、内嵌 ER 清单 |
| `preview` | png | 渲染预览 | 18 cm 宽有效 DPI ≥300（印刷）/≥150（屏幕）、色彩为 RGB 族 |
| `pdf` | pdf | 矢量导出件 | 可打开、页数可读、字体嵌入为尽力而为并如实记录 |
| `tiff` / `eps` | 对应格式 | 可选导出件（`--exports tiff,eps`） | 按目标单位要求生成；未逐项实测，见未解决项 |

> **包内不预置任何图稿或渲染件**：PDF/PNG/SVG/TIFF 一律运行时生成；
> 示例期望产物以**文字清单**写在 `examples/EXPECTED-OUTPUT.md`，
> 一键复现用 `scripts/run_examples.py`。

**责任边界**：本技能负责"材料 → 图稿 → 导出"的可核验链路与决策记录；
不负责统计方法选择、版式美术、正文写作（题面明确排除）。技能一次处理
**一个** case（`/input/case.json`），跨 case 的一致性由调用方保证。

### 3. 决策模型与决策规则 D1–D16

#### 3.1 四个契约概念

| 概念 | 定义 | 为什么必须显式 |
|-|-|-|
| **D 规则** | 一条 `触发 → 动作 → 失败降级` 三元组，带唯一编号 | 让边界情况可被点名复核，而不是"看情况" |
| **降级档位 L0–L3** | 见 §3.2 | 让"降了多少"可比较、可复现 |
| **恢复条件** | 恢复到更高档需要的具体证据 | 避免一次降级永久生效 |
| **执行锚点** | 该规则在脚本里的落点（退出码 / 检查名 / CLI） | 让"文档说的"和"代码做的"能对拍 |

#### 3.2 降级档位 L0–L3

| 档 | 名称 | 语义 | 产物 | status | 记录位置 |
|-|-|-|-|-|-|
| **L0** | 完整 | 全部检查 ok/warn，且 warn 已核可 | 三类产物齐全 | `success` | `verification.checks` |
| **L1** | 分级降级 | 缺件/缺字体/缺库/材料缺一份：**继续跑完**，产物齐全但能力受限 | 三类产物齐全 | `success`（必要时 `partial`） | `uncertainty[]` + `render` 信息 |
| **L2** | 门降级 | 生成前或产物检查出 **fail**：产物仍落盘，但不得冒充通过 | 产物齐全 | `partial` | `verification.checks.fails[]`、`spec_lint.valid=false` |
| **L3** | 停止 | 连"依据"都不存在：无清单、case 不可解析、编辑目标不可增量改 | **不产出图**（能写则写 `failed` 记录） | `failed` | `verification.checks.fails=[pipeline]` 或退出码 2 |

**两条不变式**：

- **不变式 A（不静默）**：任何 L1/L2/L3 都必须留下机器可读痕迹——退出码、
  `status`、或 `uncertainty`/`fails` 至少命中一个。检测不到的降级按未发生处理，
  视为本技能失效。
- **不变式 B（出口一致）**：CLI 退出码与 `result.json.status` 必须同向。
  退出码是给自动化的，`result.json` 是给复核者的；**两者冲突时以 `result.json`
  为记录面、以退出码为重试面**，并把冲突本身写进 `uncertainty`。

| 退出码 | 含义 | result.json | 重试语义 |
|-|-|-|-|
| `0` | `status=success`；允许存在已被 `acknowledged_issues` 确认的 warn | 写出，`verification.checks.fail_count == 0` | 无需重试；可提高画质/补导出 |
| `1` | `status=partial`（有 fail 明细）或 `status=failed`（流水线异常） | **仍然写出**，fail 明细可逐条查 | 按 fail 明细定向修复后重跑；不要原样重跑 |
| `2` | 致命：case 无法定位/解析、编辑目标无内嵌清单、目录里没有 case.json | **不写出** | 先解决输入问题再跑，重试无意义 |

#### 3.3 D 规则总表（触发 → 动作 → 失败降级）

| 规则 | 触发条件（可观测） | 动作 | 降级 | 恢复条件 |
|-|-|-|-|-|
| **D1** | `case.json` 或其所在目录无法定位/解析（含 `--case` 指到空目录） | 打印 `FATAL`，**不写任何产物** | **L3** | 提供存在的 `case.json` 文件或含 case.json 的目录 |
| **D2** | 清单里出现**材料中找不到出处**的实体名/数值 | 删掉该条目或补上 `source`+`evidence` 后再画；**禁止上图** | **L2**（若已画则回到 S2 重做） | 每个实体/关系都有 source（+evidence） |
| **D3** | 材料与任务书、或材料内部**方向/数值冲突** | 取有证据的一种；另一种连同出处写入 `uncertainty` | **L1** | 拿到更高权威版本的材料后重跑 |
| **D4** | 关系 `kind` 映射不到规范词表（7 类：activation / inhibition / recruitment / process / transcriptional / causal / containment） | **回材料用原文动词改写**，改后重跑 CP1；不猜箭头 | **L2** | `spec.relation_kind` 不再 fail |
| **D5** | 包含关系被画成箭头，或 containment 关系未被任何分组框覆盖 | 改为分组框表达（containment 用 groups，不用箭头） | **L2** | `spec.containment_group` 不再 fail |
| **D6** | 图例与图面箭头类型**双向不一致**（图面有而图例无 = 缺项；图例有而图面无 = 孤儿项） | 以数据表/清单为基准修图例后重跑 | **L2**（缺项为 fail）/ **L1**（孤儿项为 warn） | `spec.legend_missing_kinds` = ok 且无孤儿项 |
| **D7** | 图表调色板颜色数 < 唯一类别数 | 补齐调色板到 ≥ 类别数，或删冗余类别 | **L2** | `spec.color_category_count` = ok |
| **D8** | 图表出现**数据表之外**的新类别 | 回数据表：类别只来自表本身 | **L2** | G8 通过（表外类别 = INVALID） |
| **D9** | `output_contract` 声明的键缺值/类型不符 | 按声明类型补空值（四形态，禁 `null`）：string→`""`、array→`[]`、object→`{}`、number→`0`、boolean→`false` | **L2**（不影响出图） | G5 通过且顶层键齐全 |
| **D10** | 编辑请求的 `action` 未知，或目标 ID 字段名写错（关系目标必须用 `relation_id`，实体目标必须用 `entity_id`） | **停止该动作**，在日志显式报 `[edit] fail …`；**并在 §9 自查里对比"请求条数 vs change_records 条数"** | **L2**（其余动作照常；`change_records` 少于请求数即为 L2 证据） | 用 §8 的编辑动作表核对字段名后重跑 |
| **D11** | CJK 字体缺失（`textfont.py` 探测不到可用族） | 仍出 SVG（文字在），PNG/PDF 可能缺字；记 `font.cjk` warn + `uncertainty` | **L1** | 目标机装上任一候选 CJK 族后重跑 |
| **D12** | PDF 是加密件/扫描件/抽不出文本 | `pdftext.py` 报告不可抽取并记 backend；**不伪造文本**；改用可编辑版或 OCR 后再抽取 | **L3**（该材料不可用） | 取得可抽取文本的版本 |
| **D13** | 渲染或导出抛出致命异常 | 捕获 → 写 `status=failed` 的 `result.json`（`fails=[pipeline]`），已落盘产物不删 | **L3** | 修掉异常后重跑；产物目录保留 |
| **D14** | 缺第三方 PDF 库 | `pdftext.py` 走 stdlib 回退（zlib + `Tj/TJ`），**如实记录 backend** | **L1** | 装上 fitz/pypdf 后重跑可得更完整文本 |
| **D15** | 缺 matplotlib/Pillow/numpy 等运行必需库 | 打印缺件并给出安装提示，不假装渲染成功 | **L3** | `pip install matplotlib pillow numpy` 后重跑 |
| **D16** | 用了 `--skip-checks`（跳过 CP2）或 `--no-lint`（跳过 CP1） | 允许用于快速迭代，但**不得**把"未检查"当"已通过"：`verification.checks` 会为空 / `spec_lint` 为空对象 | **L1** | 交付前**必须**用默认参数（带 CP1+CP2）重跑一次 |

#### 3.4 失败分支表（矩阵视图：同一份信息按"从哪来"排）

| 分支来源 | 具体情形 | D | 档 | 机器可读痕迹 | 复核方法 |
|-|-|-|-|-|-|
| 输入 | case 不存在 / 目录无 case.json | D1 | L3 | 退出码 2，无 result.json | 看退出码与 stderr |
| 输入 | 材料文件声明了但读不到 | D3 | L1 | `uncertainty` 条目 + `sources` 少一项 | 对比 case.json 的 `sources` 与 result 的 `sources` |
| 输入 | PDF 不可抽取 | D12 | L3 | `pdftext` 非零退出 + backend 记录 | 看抽取产物是否为空 |
| 依据 | 无清单 / 清单空 | D2 | L3 | 退出码 1，`fails=[pipeline]` | `result.json.verification.checks.fails` |
| 依据 | 实体名无出处 | D2 | L2 | CP1 warn（`spec.traceability`） | 逐条对照材料 |
| 依据 | 方向/数值矛盾 | D3 | L1 | `uncertainty` 两种说法并列 | 读 `uncertainty[]` |
| 依据 | kind 未知 | D4 | L2 | `spec.relation_kind` fail | `spec_lint --json` |
| 依据 | containment 画成箭头 / 未分组 | D5 | L2 | `spec.containment_arrow` / `spec.containment_group` fail | `spec_lint --json` |
| 图面 | 图例缺项 / 孤儿项 | D6 | L2 / L1 | `spec.legend_missing_kinds` fail、`legend.orphan_items` warn | `verification.checks` |
| 图面 | 调色板 < 类别数 | D7 | L2 | `spec.color_category_count` fail | `spec_lint --json` |
| 图面 | 表外类别 | D8 | L2 | G8 INVALID | `validate_result.py` |
| 图面 | 文字被 path 化 / 图层丢失 | D13 同族 | L2 | `svg.editable_text` / `svg.layers` fail | `verification.checks` |
| 契约 | 契约键缺值/类型错 | D9 | L2 | G5 INVALID | `validate_result.py` |
| 编辑 | 动作未知 / 目标 ID 字段名错 | D10 | L2 | 日志 `[edit] fail`；`change_records` 少于请求 | 数一数请求 vs 记录 |
| 编辑 | `--edit-svg` 指向无内嵌清单的 SVG | D10 | L3 | 退出码 2 + `FATAL` | 看退出码 |
| 环境 | 无 CJK 字体 | D11 | L1 | `font.cjk` warn + `uncertainty` | `textfont.py --probe` |
| 环境 | 无 PDF 库 | D14 | L1 | backend 字段 = stdlib | `pdftext` 输出 |
| 环境 | 无 matplotlib 等 | D15 | L3 | 缺件提示，无产物 | 看日志 |
| 环境 | 窄编码控制台 | — | L1 | 非 ASCII 输出被替换为 `?` | 设 `PYTHONIOENCODING=utf-8` |
| 参数 | 用 `--skip-checks` / `--no-lint` | D16 | L1 | `checks` 空 / `spec_lint` 空对象 | 看 result.json |
| 参数 | `--exports tiff,eps` | — | L1 | TIFF 为未压缩大图（约定 4500×2580 @300dpi 时约 46 MB） | 看产物体积，按需改 `--dpi` |

#### 3.5 D 规则 → 执行锚点（"文档说的" vs "代码做的" 对拍表）

| 规则 | 执行锚点（脚本 / CLI） | 检查名 / 退出码 | 对拍命令 |
|-|-|-|-|
| D1 | `main.py` case 解析 | 退出码 2 | `main.py --case <不存在的路径>` |
| D2 | `spec_lint.py` + `main.py` 无清单分支 | `spec.traceability` warn / `fails=[pipeline]` | `spec_lint.py --manifest <m.json> --json` |
| D3 | Agent 判断写入 `uncertainty` | `uncertainty[]` | 读 `result.json` |
| D4 | `spec_lint.py` | `spec.relation_kind` | 同上 |
| D5 | `spec_lint.py` | `spec.containment_arrow` / `spec.containment_group` | 同上 |
| D6 | `spec_lint.py` + `checks.py` | `spec.legend_missing_kinds` / `legend.orphan_items` | 同上 |
| D7 | `spec_lint.py` | `spec.color_category_count` | 同上 |
| D8 | `checks.py` + `validate_result.py` | G8 | `validate_result.py --case … --result …` |
| D9 | `main.py` 契约回显 + `validate_result.py` | G5 | 同上 |
| D10 | `edit.py` 的 action 分派 | 日志 `[edit] fail` | `main.py --case … --edit-svg …` |
| D11 | `textfont.py` + `checks.py` | `font.cjk` | `textfont.py --probe` |
| D12 | `pdftext.py` | 退出码 1/2 + backend | `pdftext.py --pdf <f> --out <dir>` |
| D13 | `main.py` 渲染 try/except | `fails=[pipeline]` + 退出码 1 | 看 result.json |
| D14 | `pdftext.py` 后端选择 | `backend` 字段 | 同上 |
| D15 | 各脚本 import 守卫 | 缺件提示 | 直接运行 |
| D16 | `main.py --skip-checks` / `--no-lint` | `checks` 空 / `spec_lint` `{}` | 看 result.json |

> 这张表是**可对拍**的：左列是文档承诺，中列是脚本真实产出，右列是一条能跑的命令。
> 若某行的中列与本机实测不符，以实测为准并同步修本文档（或按 §9 上报）。

### 4. 执行骨架 S0–S7（动作 + 检查点，边界一律回指 D 规则）

**顺序固化**：读契约 → 读材料 → 抽取 → 写清单 → **CP1** → 绘图 → **CP2**
→（编辑则 **CP4**）→ **CP3** → **CP5**。

#### S0 定位与读契约
1. 读 `/input/task.md` 与 `/input/case.json`，记下 `case_id`；
2. 解析 `output_contract` 声明的键与类型（→ D9 四形态）、`sources`、`edits`、`figure_type`；
3. 确认 `/app/output`、`/app/work` 存在（不存在就建）。

#### S1 读实际文件
1. 逐份读 `case.sources` 指向的**真实文件**（相对 case.json 所在目录解析）；
   PDF 先过 `pdftext.py`（→ D12/D14）；
2. 摘录与图相关的句子/表格行并记行号；读不到的文件按 D3 记 `uncertainty`；
3. 明确图型与硬参数：实体数、关系方向、分组、图例、画布/期刊参数。

#### S2 抽取实体—关系清单
```bash
python "$SKILL_DIR/scripts/extract.py" \
    --inputs /app/work/pdftext/<stem>.txt <其他材料> \
    --out /app/work/draft-entities.json
```
草稿带 `_draft` 标注，**只是候选**。Agent 复核后写 `/app/work/entities.json`
（规范见 `references/ER_MANIFEST.md`；**字段级细则与反模式见
`references/EDIT-ACTION-SCHEMA.md` §2**）：
1. 实体 `{id, name, type, source, evidence}`，`name` **逐字**来自材料（→ D2）；
2. 关系 `{from, to, kind, source, evidence}`，`kind` 用材料原文动词并映射到
   7 类规范类别（→ D4）；方向与材料一致；包含关系落到 `groups`（→ D5）；
3. 数值/单位只抄材料表格，**不换算**（µM 与 nM 不互相改写）；
4. 颜色：schematic 只从 `assets/relation-dict.json` 取；chart 的
   类别↔颜色↔图例来自**同一张数据表**，调色板长度 ≥ 类别数（→ D7/D8）；
5. 材料自己点明的"常见误读"必须在清单里落实，并在 `change_records`/注释中说明。

#### S3 CP1：生成前 lint（门）
```bash
python "$SKILL_DIR/scripts/spec_lint.py" --manifest /app/work/entities.json
# 只有 {"valid": true} 才算 CP1 通过；否则按该 fail 对应的 D 规则修（见 §3.5）
```
CP1 覆盖：实体非空且 id/name 有效；关系 from/to 指向存在的实体；kind 全部可映射；
containment 必须用分组框；图例双向一致；chart 调色板 ≥ 类别数、单位存在。
`main.py` 默认内嵌该 lint（`--lint` 默认开，`--no-lint` 关 → D16）。

#### S4 生成可编辑源 + 导出
```bash
python "$SKILL_DIR/scripts/main.py" \
    --case /input/case.json \
    --manifest /app/work/entities.json \
    --work /app/work \
    --out /app/output
```
- case.json 自带 `manifest`/`entities+relations`/`data` 时可省 `--manifest`；
  `--case` 也可指向**目录**（该目录或其 `examples/` 下有 `case.json` 时自动解析）；
- **编辑任务**：见 S6；
- `--fixed-time <ISO>` 固定 `generated_at`，用于确定性双跑（CP5）；
- 常用参数：`--exports png,pdf,svg`（`tiff,eps` 按需，见 §3.4 末行）、
  `--dpi 300`、`--base-name figure`。

#### S5 CP2：核对检查结果
`main.py` 把逐项明细写进 `result.json.verification.checks`：

- **溯源**：实体/关系带 `source`+`evidence` 的比例（`data-entity`/`data-relation`/`data-source` 审计）；
- **图例一致**：图面箭头类型 ↔ 图例条目**双向**比对（→ D6）；
- **数据映射**：类别 ↔ 颜色 ↔ 图例同源于一张表，单位上轴（→ D7/D8）；
- **导出预检**：PNG 在 18 cm 宽下的有效 DPI（≥300 印刷/≥150 屏幕）、色彩模式、
  SVG 文字可编辑性（`<text>` 而非 path）、PDF 结构、字体（→ D11）。

出现任何 `fail`：按 §3.5 找到对应 D 规则修正后**重跑**，不绕过、不静默。
确属材料缺失或已知限制的，按 L1 写进 `uncertainty` / `acknowledged_issues`。

#### S6 CP4：源文件级编辑 + 再校验（编辑任务）
```bash
python "$SKILL_DIR/scripts/main.py" --case <case.json> \
    --edit-svg /app/work/figure.svg --out /app/output --work /app/work
```
- **字段名必须精确**（→ D10）：关系目标用 `relation_id`，实体目标用 `entity_id`，
  新值用 `to`，沿用 `reason`；完整表见 §8；
- **走 `--edit-svg` 时，编辑请求要写在 case.json 的 `edit_requests` 字段**；
  只写 `edits` 时该字段会被忽略——这是本包点名的一处**易错点**：
  交付前用"请求条数 vs `change_records` 条数"对拍（→ D10）；
- 未改动元素保持原样——这才是"源文件可编辑"，不是重画整张图；
- **编辑后必须重跑全部 CP2 检查与 CP3 契约门**，确认没有残留的旧标签/旧方向。

#### S7 CP3 契约门 + CP5 自查与确定性
1. 契约门：
   ```bash
   python "$SKILL_DIR/scripts/validate_result.py" \
       --case /input/case.json --result /app/output/result.json
   # VALID（G1–G8 全过）才算通过；退出码 0
   ```
2. Agent 复核并补叙述字段：`task_summary`、`uncertainty`（逐条写 L1/L2 降级）、
   `change_records`（自动生成，勿手写）、确认 `output_contract` 键都已回显且无 `null`；
3. CP5 确定性：同一 manifest + 选项**两次运行**，`figure.svg` 逐字节一致，
   `result.json` 除 `generated_at`（用 `--fixed-time` 后应全同）外一致；
   `verification.determinism.spec_sha16` 两次相同即为探针证据。
   若上机环境无法复跑两次，在 `TEST.md` 如实记差异；
4. 形态自查（本题硬约束）：包内**只**放 UTF-8 文本
   （`.md/.py/.json/.txt/.csv/.yaml/.yml`），不放 PDF/PNG/SVG/TIFF/PPTX、
   不放 `__pycache__`/`*.pyc`，文件数 ≤50、单文件 ≤500KB、总计 ≤2MB：
   ```bash
   python "$SKILL_DIR/scripts/run_examples.py" --out /tmp/sse-examples
   ```

### 5. 异常处置速查（按"谁先发现"排）

| 谁先发现 | 情形 | 处置 |
|-|-|-|
| 脚本（生成前） | kind 未知 / containment 未分组 / 图例缺项 / 调色板不足 | CP1 fail → 依 D4/D5/D6/D7 修清单后重跑 |
| 脚本（产物后） | 文字被 path 化、图层丢失、DPI 不足、色彩不符 | CP2 fail → 修渲染参数/选项后重跑 |
| 脚本（产物后） | PDF 结构或字体嵌入可疑 | 按 D11/D13 处理并写 `uncertainty`（字体嵌入审计为尽力而为） |
| 脚本（致命） | case 不可解析 / 编辑目标不可增量改 / 缺必需库 | D1/D10/D15 → 退出码 2 或 3 的 `failed` 记录 |
| Agent（材料层） | 材料缺失、矛盾、PDF 不可抽取 | D3/D12 → 记录 + 降级，**不补造** |
| Agent（图面层） | 实体名找不到出处、方向吃不准 | D2/D3 → 删条或补 evidence；宁缺毋滥 |
| Agent（交付前） | 用了 `--skip-checks`/`--no-lint`、或改过清单没重跑 | D16 → 用默认参数完整重跑一次 |

### 6. 资源文件说明（路径相对技能根，调用一律 `"$SKILL_DIR/..."`）

| 入口 | 角色 | CLI |
|-|-|-|
| `scripts/main.py` | 流水线入口 | `--case --manifest --out --work --edit-svg --base-name --exports --dpi --skip-checks --lint --no-lint --fixed-time --doc-check` |
| `scripts/extract.py` | 材料→候选 ER 清单草稿 | `--inputs --out --base-dir` |
| `scripts/pdftext.py` | PDF 文本抽取（含 stdlib 回退） | `--pdf --out` |
| `scripts/textfont.py` | 字体栈探测 | `--list --probe` |
| `scripts/spec_lint.py` | CP1 生成前 lint | `--manifest --dict --json` |
| `scripts/manifest.py` | ER 清单加载/规范化（位置参数） | `<manifest.json>` |
| `scripts/layout.py` | 布局引擎（库模块） | `—` |
| `scripts/svgbuilder.py` | 分层可编辑 SVG 构建（库模块） | `—` |
| `scripts/render.py` | matplotlib 镜像渲染（库模块） | `—` |
| `scripts/checks.py` | CP2 产物检查（库模块） | `—` |
| `scripts/edit.py` | 源文件级增量编辑 | `<figure.svg> <edits.json>` |
| `scripts/validate_result.py` | 契约独立校验 G1–G8 | `--case --result --out --json` |
| `scripts/selftest.py` | 模块级自测 | `—` |
| `scripts/run_examples.py` | 一键复现三示例 | `--out --keep` |
| `scripts/report.py` | 结果渲染辅助（库模块） | `—` |

| 其它文件 | 用途 |
|-|-|
| `scripts/doccheck.py` | **本变体新增**：文档承诺（D 规则编号 / 检查名 / CLI 参数）与 `scripts/` 事实的只读对拍；退出码 0 = 一致，1 = 有 FAIL |
| `references/CHECK-INDEX.md` | **本变体新增**：全部检查名的清单（级别 + 科学含义），是 doccheck 的事实来源 |
| `references/OUTPUT_CONTRACT.md` | `result.json` 契约 + G1–G8 硬门 + 四形态回显（**必读**） |
| `references/EDIT-ACTION-SCHEMA.md` | **本包新增**：编辑动作→字段名→记录的对照表、`main.py` 编辑路径矩阵、反模式与字段级自查 |
| `references/failure-modes.md` | 题面 12 类失败形态 → 检测机制 → **D 规则 → L 档位**（与 §3 四点对齐） |
| `references/ER_MANIFEST.md` | 实体—关系清单规范（绘图唯一数据源） |
| `references/DRAWING_GRAMMAR.md` | 图形语法：关系语义→箭头/线型/颜色、方向判定、分组/层级、图例/数据映射 |
| `references/RUBRIC_MAP.md` | 五维评分（40/25/15/10/10）→ 本包文件/机制逐条映射 |
| `assets/relation-dict.json` | 连接规则字典（kind→arrow/line/dash/color，机器可读；spec_lint/渲染/图例共用） |
| `assets/checklist.json` | CP1–CP5 检查点 + 自查清单（机器可读） |
| `examples/*` | 最小示例（schematic / chart / edit + 合成材料 + `EXPECTED-OUTPUT.md`），**示例非正式案例**；示例产物运行时生成，不入包 |

### 7. 五维评分映射（交付前逐条自评；完整表见 `references/RUBRIC_MAP.md`）

| 维度 | 分 | 本包机制（可跑的检查，不是自述） | 证据文件 |
|-|-|-|-|
| 实际效果 | 40 | 材料→ER 清单→CP1→可编辑 SVG→PNG/PDF→result.json 一条命令跑通；实体/关系/方向/层级/数值逐条 `source+evidence`；图面要素（分组框、图例、单位轴、标题、来源脚注）齐备 | `scripts/main.py`、`scripts/spec_lint.py`、`scripts/checks.py`、`scripts/svgbuilder.py` |
| 使用增益 | 25 | CP1+CP2+CP3 三层门每次运行自动执行；素材→图稿一条命令；改数据只改清单即重绘；编辑走内嵌清单增量改；**D 规则把返工点前置**（错了在生成前就被拦下，而不是画完才发现） | `scripts/main.py`、`scripts/extract.py`、`scripts/edit.py`、§3、`TEST.md` |
| 创新增益 | 15 | ①CP1 **生成前** lint 门 ②SVG 内嵌 ER 清单 → 源文件自描述、可增量编辑 ③stdlib PDF 抽取回退 + 诚实 backend ④导出前合规检查 ⑤共享字体探针 ⑥**本包新增：D 规则 + L 档位 + 执行锚点三点对拍表**（把边界决策变成可对拍的契约） | `scripts/spec_lint.py`、`scripts/edit.py`、`scripts/pdftext.py`、`scripts/checks.py`、§3.5、`references/EDIT-ACTION-SCHEMA.md` |
| 可靠体验 | 10 | 自定位（`$SKILL_DIR`，任意 cwd 可跑）；`--case` 兼容文件与目录；退出码 0/1/2 语义与 `status` 同向（不变式 B）；**D1–D16 覆盖输入/依据/图面/契约/编辑/环境/参数七类分支，每条带降级档位与恢复条件** | §3、§5、`references/failure-modes.md`、`scripts/run_examples.py` |
| 生态贡献 | 10 | 说明/依赖/字体/参数/示例/限制/维护齐全；可复用资产：机器可读连接规则字典、CP 自查清单、ER 清单规范、图形语法规范、契约校验器、**D 规则—检查名对拍表**、可复跑示例三件套 | `README.md`、`references/*`、`assets/*`、`examples/*` |

### 8. 编辑动作对照表（D10 的字段级依据）

| action | 目标 ID 字段 | 新值字段 | 记录到的 action |
|-|-|-|-|
| `add_entity` | —（`entity.id` 可省，自动补） | `entity{...}` / 可选 `relation{...}` | `add_entity`（+`add_relation`） |
| `remove_entity` | `entity_id` | — | `remove_entity` + 每条被波及关系的 `cascade_remove_relation` |
| `rename` | `entity_id` | `to` | `rename` |
| `relabel` | `relation_id` | `to` | `relabel` |
| `flip_direction` | `relation_id` | — | `flip_direction`（before/after 记 `from→to`） |
| `change_kind` | `relation_id` | `to` | `change_kind` |
| `remove_relation` | `relation_id` | — | `remove_relation` |
| `add_group` | —（`group.id` 可省，自动补） | `group{...}` | `add_group` |
| `update_value` | `entity_id` 或 `relation_id` + `field` | `value` | `update_value` |
| `note` | — | `text` | `note` |

**反模式（会导致"请求了但没记下来"）**：

| 写法 | 结果 | 正确写法 |
|-|-|-|
| `{"action":"relabel","target":"R5","value":"…"}` | 目标解析不到 → 日志 `[edit] fail unknown relation`，**不落 change_records，退出码仍为 0** | `{"action":"relabel","relation_id":"R5","to":"…"}` |
| `{"action":"remove_entity","target":"E3"}` | 同上 | `{"action":"remove_entity","entity_id":"E3"}` |
| 把编辑写在 case 的 `edits` 但用 `--edit-svg` 调用 | `edits` 在该路径下被忽略 | 改用 `edit_requests`（或不用 `--edit-svg`） |

### 9. 自查清单（提交前逐行确认；机器版 `assets/checklist.json`）

- [ ] 实体名逐字出自材料，无材料外基因/浓度/时间点/单位（**D2**）；
- [ ] 每条关系方向与材料一致，激活≠抑制、上下游不颠倒（**D3/D4**）；
- [ ] CP1 `{"valid": true}`：kind 可映射、containment 用分组、图例双向、调色板 ≥ 类别数（**D4/D5/D6/D7**）；
- [ ] 数值/坐标/单位与数据表逐项一致，改数据能重绘（**D7/D8**）；
- [ ] `figure.svg`：文字可选（`<text>`）、图层可拆（`layer-*`）、带 `id` 与 `data-*`、内嵌 ER 清单；
- [ ] 导出件：PDF 可打开；PNG 有效 DPI 达标；色彩 RGB 族（**D13**）；
- [ ] `result.json` 含全部契约键 + `case_id`，契约四形态回显无 `null`（**D9**）；
- [ ] `validate_result.py`（G1–G8）输出 VALID，退出码 0（**CP3**）；
- [ ] 编辑任务：**请求条数 == `change_records` 条数**，未改动元素保持原样（**D10**）；
- [ ] `uncertainty` 覆盖每一条 L1/L2 降级；未编造缺失状态（**D2/D3/D12/D15**）；
- [ ] 交付前最后一次运行**没有**用 `--skip-checks` / `--no-lint`（**D16**）；
- [ ] 形态：仅 7 种文本扩展名、无 `__pycache__`、≤50 文件、≤500KB/文件、≤2MB、包内无本机绝对路径。

### 10. 依赖与限制

- Python 3.9+（实测 3.13）；运行必需 **matplotlib / Pillow / numpy**，reportlab 可选；
  PDF 抽取按 fitz → pypdf → PyPDF2 → **stdlib 回退**逐级降级（→ D14）。
  建议先跑 `python "$SKILL_DIR/scripts/selftest.py"` 确认环境；
- **平台运行契约**：技能装在 `/skills/weekly-skill`；输入 `/input/case.json` + `/input/task.md`；
  中间产物 `/app/work`；最终产物 `/app/output`（含 `result.json`）。
  预算 64 次模型请求 / 900 秒 / 16384 token/响应 —— **先落盘可用部分产物，再增量改进**；
- **资源形态（硬约束）**：仅 UTF-8 文本文件
  （`.md/.py/.json/.txt/.csv/.yaml/.yml`），≤50 个、单文件 ≤500KB、合计 ≤2MB、
  无符号链接；PDF/PNG/SVG/TIFF 一律运行时生成；
- **已知限制（如实标注）**：无 cairosvg/svgwrite 时 PNG/PDF 预览是与 SVG 同源的
  matplotlib 镜像（语义一致、**非逐像素**）；PDF 字体嵌入审计为尽力而为；
  CJK 渲染依系统字体；`extract.py` 只产候选草稿，方向必须人工复核；
  走 `--edit-svg` 时 `edits` 字段不生效（用 `edit_requests`）；TIFF/EPS 路径未逐项实测。

### 11. 禁止事项

- 不提交预制答案/正式案例输出；示例只用于演示接口与流程，**示例产物不入包**；
- 不编造缺失的软件状态或科学数据（来源里没有的实体/数值一律不画，**D2**）；
- 不宣称未经评分的成绩或基准；不为"好看"改关系颜色（改色 = 图例不一致）；
- 不把 `--skip-checks` / `--no-lint` 的结果当交付版本（**D16**）。

---

# 【增益层】公平对照协议与可测指标（目标维度:使用增益 25）

---
name: scientific-schematic-editor
description: >-
  Generate and edit editable scientific schematics, mechanism/relationship
  diagrams, flow diagrams and data charts from source materials, with a
  measurement protocol attached. Extracts an entity-relation manifest
  (traceable to sources), draws a layered editable SVG source plus PNG/PDF
  (and TIFF/EPS) exports, runs CP1 plan-lint and legend/data-mapping and
  export-compliance checks, and writes a structured result.json with all
  output_contract fields. Use when a task asks to draw, regenerate or edit a
  scientific figure from papers, tables or notes: 科研示意图/机制图/信号通路图/
  流程图/实验装置图/图表的生成与编辑. Every run emits the metrics needed to
  compare against a Skill-free baseline (references/GAIN-PROTOCOL.md):
  exit code, contract validity, gate counts, traceability ratio, rework
  cycles; the protocol also lists exactly which measurements are NOT yet
  made, so no unmeasured gain is claimed.
---
## scientific-schematic-editor — 科研示意图生成与编辑（增益可验证版）

本技能交付两样东西：**能出图的流水线**，以及**一套说清"它比不加技能强在哪"的
度量协议**。协议不是宣言，是 `references/GAIN-PROTOCOL.md`：里面定义了对照组、
指标、判据、公平性条款，以及**本机真实跑出来的数据**——包括哪些指标实测更好、
哪些没有差异、哪些**尚未测量**。

三条主张：

1. **图画对** — 实体、关系、方向、数值、单位逐条可回溯到材料；
2. **图可改** — 文字可选、图层可拆、SVG 内嵌 ER 清单，编辑只动被指明的元素；
3. **增益可测** — 每次运行的退出码、契约有效性、门控计数、溯源比例、返工轮次
   都是可记录的观测量；对照基线用同一夹具、同一命令集。

**本技能不做**：统计计算的数值方法选择、海报/封面版式、艺术插画美化、
论文正文写作。数据表里的数值是**事实输入**，不改算、不补造、不换算单位。

> 与基线包的结构差异：本包把**度量**提到正文主线。§3 给出指标定义与基线对照
> 矩阵（I1–I10），§4 给出"要产出一条可比较记录"的执行路线（M0–M6），
> 决策规则（§5）只在"影响可测性"时出现——因为一条静默降级会污染测量，
> 所以把会污染测量的分支专门点名。

### 1. 适用条件

- 任务是"科研示意图/机制图/通路图/流程图/实验装置图/数据图"的**绘制或编辑**，
  workorder 一般形如 `editable_relationship_schematic`；
- 有来源材料（论文图注/正文摘录/Markdown/CSV/PDF），或要求对已有图稿做
  **源文件级**修改；
- 交付要求包含可编辑源文件、导出件与结构化结果（`result.json`）；
- **需要给出增益证据**时（本题的"使用增益可验证性"评分点）——这时按 §3/§4 走，
  并把对照记录附在交付说明里。

### 2. 输入、输出与"可测产物"

**输入（平台提供）**：`/input/case.json`（`case_id`/`workorder`/`figure_type`/
`sources`/可选 `manifest`、`entities+relations`、`data`、`edits`、`output_contract`）、
`/input/task.md`、`/input/` 下的材料（可能是 PDF，先过 `scripts/pdftext.py`）。
**以实际文件内容为准，不凭字段标签猜内容。**

**输出（写入 `/app/output`，全部运行时现场生成）**

```
/app/output/
├── figure.svg      # 可编辑分层源文件
├── figure.png      # 渲染预览
├── figure.pdf      # 矢量导出件
├── result.json     # 结构化结果（OUTPUT_CONTRACT 全字段 + case_id）
└── work/           #（或 /app/work）entities.json / draft / layout / manifest.validated.json
```

| role | format | 是什么 | 完成标准 |
|-|-|-|-|
| `figure` | svg | 可编辑分层源文件 | 文字是真实 `<text>`（未被 path 化）、语义图层可拆、带 `id`/`data-*`、内嵌 ER 清单 |
| `preview` | png | 渲染预览 | 18 cm 宽有效 DPI ≥300（印刷）/≥150（屏幕）、色彩为 RGB 族 |
| `pdf` | pdf | 矢量导出件 | 可打开、页数可读、字体嵌入为尽力而为并如实记录 |
| `tiff` / `eps` | 对应格式 | 可选导出件（`--exports tiff,eps`） | 按目标单位要求生成；未逐项实测，见未解决项 |

> **包内不预置任何图稿或渲染件**（PDF/PNG/SVG/TIFF 都不随包分发）：它们由本技能
> 运行时生成；示例期望产物见 `examples/EXPECTED-OUTPUT.md`，一键复现用
> `scripts/run_examples.py`。

### 3. 度量模型：I1–I10 指标与基线对照

#### 3.1 为什么先定义指标

"使用增益"包含**质量增益 / 效率增益 / 增益可验证性**三块。没有定义就没有增益：
先说清"测什么、怎么测、和谁比、什么算赢"，再谈结果。本技能选定的指标必须是
**同一条命令集下可重复观测**的，而不是主观观感。

#### 3.2 指标定义（每一项都给出取值来源）

| 指标 | 定义 | 取值来源（机器可读） | 基线做法（不加载 Skill） |
|-|-|-|-|
| **I1 契约有效性** | `validate_result.py` 是否 VALID（G1–G8） | 退出码 | 基线常见：无 `result.json`，或字段不全 ⇒ 无效 |
| **I2 结构完整性** | 三类产物（可编辑源 / 预览 / 导出）是否齐全 | `artifacts[].role`、G7 | 基线常见：只有位图 |
| **I3 可编辑性** | 文字是否为真实 `<text>`、是否有语义图层、是否带 `id`/`data-*` | `svg.editable_text`、`svg.layers`、`svg.data_entity_attrs` / `svg.data_relation_attrs` / `svg.data_source_attrs` | 基线常见：导出即栅格化或文字 path 化 |
| **I4 溯源比例** | 带 `source`（+`evidence`）的实体/关系占比 | `traceability.entities`、`traceability.relations` | 基线无此概念：图上元素没有出处字段 |
| **I5 关系语义正确性** | 方向/类型是否落到 7 类规范词表且可判 fail | `spec.relation_kind`、`spec.containment_group` | 基线靠自由文本箭头，无判据 |
| **I6 图例一致率** | 图面箭头类型 ↔ 图例条目双向一致 | `spec.legend_missing_kinds`、`legend.orphan_items` | 基线手工画图例，无双向校验 |
| **I7 数据映射一致** | 类别 ↔ 颜色 ↔ 图例同源、调色板覆盖类别数、单位上轴 | `spec.color_category_count`、`data_mapping.*` | 基线常见：颜色数与类别数不符 |
| **I8 导出合规** | 18 cm 宽有效 DPI、色彩族、PDF 结构、字体 | `bitmap.dpi_print`、`bitmap.colourspace`、`pdf.*`、`font.cjk` | 基线少见预检 |
| **I9 返工轮次** | 从材料到"门全过"需要几次重跑 | 同一 pipeline 的连续运行次数（人工记账） | 基线无门 ⇒ 无法定义"过" |
| **I10 端到端耗时** | 一条命令出齐产物并跑完门 | 命令的墙钟时间 | 同为一条命令，但缺门与校验 |

#### 3.3 公平性条款（对照成立的前提）

| # | 条款 | 理由 |
|-|-|-|
| F1 | **同输入**：同一 `case.json`、同一材料文件、同一 `output_contract` | 输入不同则不可比 |
| F2 | **同画布与导出参数**：同一 `style.canvas`、同一 `--dpi`、同一 `--exports` | 图面参数变了，DPI/排版类指标就不可比 |
| F3 | **同预算**：同一模型、同一 64 请求 / 900 秒 / 16384 token 响应预算 | 题面运行契约 |
| F4 | **同模型与同版本**：对照臂不加载本 Skill，其余条件一致 | "增益"必须归于 Skill 而非模型 |
| F5 | **同判据**：两个臂用**同一个** `validate_result.py`（本包自带的 G1–G8）判分 | 判据若各写一套，等于自己给自己打分 |
| F6 | **同夹具复用**：`examples/` 的三件套固定不改，对照运行不得调整夹具 | 改夹具 = 改题 |
| F7 | **失败也记录**：任一臂失败都记 exit code 与 fail 明细，不得丢弃重试直到好看 | 丢弃失败样本 = 选择性报告 |
| F8 | **不可测就标注**：没有实际跑过的指标写"未测量"，不得用推断值顶替 | 这是本协议最重要的一条 |

> F5 有点违反直觉但很关键：**用被测方自带的判据去评分被测方是有偏的**。
> 本协议的处理方式是把偏差**写明并固定**：同一判据同时作用于两个臂，
> 因此"判据偏严/偏松"对两臂同等生效；真正的科学正确性仍由题面所说的
> "scientific judgement remains native/LLM Judge"承担，不由本协议承担。

#### 3.4 实测对照记录（CLI 空间，本机真实运行）

**这部分是真实跑出来的，不是设计意图。** 完整命令见 `TEST.md` §M2–§M5，
复跑环境：Python 3.13.9 / matplotlib 3.10.6；夹具 = 本包 `examples/` 三件套。

| # | 场景 | 命令要点 | 实测 | 对应的指标 |
|-|-|-|-|-|
| R1 | 标准 schematic | `main.py --case examples --out <t>` | **exit 0**，墙钟 1.53 s；`status=success`；产物 3 类齐全；`result.json` 顶层 23 键 | I1、I2、I10 |
| R2 | 标准 schematic（外部 cwd） | 同上，cwd 在包外 | **exit 0**，1.53 s；`figure.svg` sha256 与 R1 **完全相同** | I10（自定位不引入差异） |
| R3 | 契约门 | `validate_result.py` | **exit 0 / VALID**（G1–G8 全过） | I1 |
| R4 | 三示例端到端 | `run_examples.py --out <t>` | **exit 0**，4.99 s；schematic/chart/edit 三步各 exit 0，三份契约各 VALID；顶层键 23 / 21 / 21 | I1、I2、I10 |
| R5 | 确定性双跑 | `--fixed-time` 两次 | 两次 `figure.svg` **逐字节一致**（sha256 相同）；两份 `result.json` 唯一差异是 `artifacts`（`abspath` 指向不同目录），去 `abspath` 后完全相同 | I9（可复现性是其前置） |
| R6 | 数据更新传播 | 把 chart 数据表的值翻倍后重跑 | 两次 `figure.svg` sha256 **不同** ⇒ 图随数据重绘（不是"改了数据图不动"） | I7 |
| R7 | 材料缺失 | `sources` 指向不存在文件 | **exit 0**、`status=success`，但 `sources=[]`、`uncertainty` 3 条 ⇒ 降级被记录 | I4（诚实性联动） |
| R8 | 未知关系类型 | manifest 里把 kind 改成 `gibberish` | **exit 1**、`status=partial`、`fails=[spec_lint.spec.relation_kind]` ⇒ 错误被拦而非静默通过 | I5 |
| R9 | 无依据即停 | 无 manifest 且 case 无 entities | **exit 1**；写 `status=failed`；`fails=[pipeline]` | I1（不造假） |
| R10 | 编辑增量 | `--edit-svg` + 5 个动作（字段名正确） | **exit 1**（夹具触发 `spec.group_member` fail）；`change_records` **7** 条；实体 6→5、关系 5→3；契约仍 VALID | I2、I9 |
| R11 | 编辑目标不存在 | `relabel` 指向不存在的 `R99` | 日志 `[edit] fail`；`change_records` **0** 条；**exit 0**、契约仍 VALID ⇒ **该分支不可从 result.json 察觉** | 见 §3.5 混合项 |
| R12 | 草稿抽取 | `extract.py` 跑示例材料 | **exit 0**，0.12 s；产出 17 实体 / 4 关系 / 5 组，全部带 `_draft` ⇒ 抽取只是加速，仍需复核 | I9 |
| R13 | `--exports tiff,eps` | 追加导出 | **exit 0**；TIFF ≈ 46 MB（未压缩 4500×2580@300dpi） | I8（体积相关） |

**这些数字能支撑什么、不能支撑什么（关键的自制）**：

| 结论 | 是否被 R1–R13 支撑 |
|-|-|
| 本技能能稳定产出"可编辑源 + 预览 + 导出 + 契约有效"的一整套 | ✅ 被 R1–R4 支撑（同一夹具，多次运行） |
| 同一输入下产出是确定性的（除时间戳/输出目录） | ✅ 被 R5 支撑 |
| 图随数据重绘而非冻结 | ✅ 被 R6 支撑 |
| 错误输入会被拦下并显式降级，而不是静默出图 | ✅ 被 R7–R9 支撑 |
| 编辑是增量而非重画，且改动有 before→after 记录 | ✅ 被 R10 支撑 |
| **本包比"不加载 Skill 的基线 Agent"得分更高** | ❌ **未测量**。基线臂要由平台按同一案例运行；本机没有跑过基线臂，因此不作此声明 |
| **返工轮次比人工/基线更少** | ❌ **未测量**。R1–R13 是 CLI 空间测量，不含"人工修改量"这类需要对照臂的量 |
| **耗时比基线更短** | ❌ **未测量**。只有本包自身的墙钟时间（约 1.5 s/例，毫秒级差异不足以支撑结论） |

#### 3.5 "可测性混合项"清单（哪些改进无法被机器判据完全覆盖）

诚实标注比夸大更有价值。以下三处是**部分可测**的，协议要求用"半自动判据"补：

| 混合项 | 机器能测的部分 | 需要人/LLM 判的部分 | 本文档的态度 |
|-|-|-|-|
| 科学正确性（方向、机制） | kind 是否可映射、containment 是否用分组、self-loop 告警 | "抑制画成激活"这类**语义**错 | 机器只兜结构错误；语义由题面所说的 native/LLM 判断承担 |
| 编辑生效性 | `change_records` 条数与内容（before→after） | "这是不是用户真想要的那次编辑" | **请求条数 vs 记录条数**是本协议指定的对拍判据（因为 `edit.*` 问题只进 stdout） |
| 图面美观/可读性 | 溢出、重叠、字号下限的部分检测 | 审美 | 不声称；只给 warn 与 `uncertainty` |

### 4. 执行路线 M0–M6（每一步都产出"可记录的观测"）

**顺序：读契约 → 读材料 → 抽取 → 写清单 → CP1 → 绘图 → CP2 →（编辑则 CP4）
→ CP3 → CP5 → 记账。**

#### M0 定位并读契约
1. 读 `/input/task.md` 与 `/input/case.json`，记 `case_id`；
2. 解析 `output_contract` 声明的键与类型（四形态：string→`""`、array→`[]`、
   object→`{}`、number/boolean→`0`/`false`，禁 `null`）；
3. 记下本次运行的**参数快照**（`--dpi`、`--exports`、画布尺寸）——F2 要求对照时
   参数一致，参数不记 = 对照无效；
4. 确认 `/app/output`、`/app/work` 存在。

#### M1 读实际文件（记录材料清单）
1. 逐份读 `case.sources` 指向的**真实文件**；PDF 先过 `pdftext.py`；
2. 记下"读到几份 / 缺几份"——这是 I4 与诚实性的输入；
3. 记下"材料里有几条与图相关的陈述"作为溯源分母。

#### M2 抽取候选清单（加速项，不是答案）
```bash
python "$SKILL_DIR/scripts/extract.py" \
    --inputs /app/work/pdftext/<stem>.txt <其他材料> \
    --out /app/work/draft-entities.json
```
草稿带 `_draft` 标注。**记录"草稿条数 vs 最终清单条数"**：这个差值是 I9 的
可观测代理（人工复核量），也是"抽取只是加速器"的证据。

#### M3 CP1：生成前 lint（I5/I6/I7 的第一道闸）
```bash
python "$SKILL_DIR/scripts/spec_lint.py" --manifest /app/work/entities.json
# {"valid": true} 才算通过；否则按 fail 的检查名定位问题后重跑
```
**记录本次 CP1 的结果与轮次**：第 1 次就 valid，还是第 k 次才 valid —— 这就是
I9 的读数（返工轮次）。

#### M4 生成 + CP2（I2/I3/I8 的读数来源）
```bash
python "$SKILL_DIR/scripts/main.py" --case /input/case.json \
    --manifest /app/work/entities.json --work /app/work --out /app/output
```
- 记录**墙钟时间**（I10）与**exit code**；
- `result.json.verification.checks` 里逐条读：`svg.*`（I3）、`bitmap.*`+`pdf.*`+`font.cjk`（I8）、
  `legend.*`（I6）、`data_mapping.*`（I7）、`traceability.*`（I4）；
- **记录 fail/warn 计数**，不要只看 `status`。

#### M5 编辑（如适用）→ 记录改动量
```bash
python "$SKILL_DIR/scripts/main.py" --case <case.json> \
    --edit-svg /app/work/figure.svg --out /app/output --work /app/work
```
- 走 `--edit-svg` 时编辑请求写在 case 的 **`edit_requests`** 字段（写 `edits` 会被忽略）；
- **必须对拍**："请求条数（按 `references/EDIT-ACTION-SCHEMA.md` §1 推算，含
  `remove_entity` 的级联）" vs "`change_records` 条数"。不等即为一次**未被机器捕获的失败**，
  按 §3.5 的半自动判据处理；
- 记录"未改动元素是否保持原样"（同一 SVG 的其余部分不应变化）。

#### M6 CP3 契约门 + CP5 确定性 + 记账
1. 契约门：`validate_result.py --case … --result …` → **VALID** 是 I1 的唯一读数；
2. CP5 确定性：`--fixed-time` 双跑，比对 `figure.svg` 字节与 `result.json`
   （除 `generated_at` / `artifacts[].abspath` 外应一致）；
3. **把本次运行的记账写成一段可粘贴的记录**（模板见
   `references/GAIN-PROTOCOL.md` §5），字段：case_id、参数快照、exit code、
   门控计数、各指标读数、返工轮次、未测量项。

### 5. 决策规则（只列"会影响可测性"的分支）

这里不重复完整决策体系，只列**会污染测量**或**会让读数失真**的分支——
这类分支一旦静默，整份对照记录就不可信。

| 规则 | 触发 | 动作 | 对测量的影响 |
|-|-|-|-|
| **G1** | 运行中使用了 `--skip-checks` 或 `--no-lint` | 该次运行**不得**计入对照记录：`verification.checks` 会为空、`spec_lint` 会是空对象，I3–I8 全部无读数 | 让"未检查"看起来像"已通过" |
| **G2** | 发生任何降级（材料缺失、字体缺失、无 PDF 库、镜像渲染） | 写入 `uncertainty`，并在记账里标注"本次读数受 X 影响" | 不标注就会把降级读数当成正常读数 |
| **G3** | 两次运行之间改了夹具、画布或 `--dpi` | 视为**不同条件**，分开记账，不得互相比较 | 违反 F1/F2 ⇒ 对照无效 |
| **G4** | 编辑请求条数 ≠ `change_records` 条数 | 本次编辑**判为失败**并查明字段名（`relation_id`/`entity_id`）；不得计入"编辑成功" | 该分支只进 stdout，不查就查不出 |
| **G5** | 任一臂失败 | 记录 exit code 与 fail 明细，**不得**丢弃重试直到好看 | 违反 F7 ⇒ 选择性报告 |
| **G6** | 想声明"比基线更好" | 必须已有**基线臂的实测读数**；没有就只能写"未测量" | 违反 F8 ⇒ 不可核验的声明 |
| **G7** | 写入 `acknowledged_issues` 把一个 warn 标记为已核可 | 可以在记账里写"warn 已核可"，但**不得**把它写成 ok | 混淆 ok 与 ack 会让 I3–I8 虚高 |
| **G8** | 材料本身不可抽取（加密/扫描 PDF） | 停在该材料，不伪造文本；记账写"该材料不可用" | 造假文本会让 I4 变成假读数 |

> 与基线包的关系：完整决策体系（材料缺失/矛盾、未知 kind、containment、
> 图例、调色板、字体、导出失败、编辑目标缺失…）在本包中按**同一套脚本行为**
> 生效，其权威描述见 `references/failure-modes.md`；本表只补"测量学上特别
> 危险"的那几条。

### 6. 异常处置速查（含"记账怎么写"）

| 情形 | 处置 | 记账字段 |
|-|-|-|
| 材料缺失 | 继续跑，写 `uncertainty` | 已读/缺失份数，`uncertainty` 条数 |
| 方向/数值矛盾 | 取有证据者，另一说法入 `uncertainty` | 冲突条数与取舍理由 |
| kind 未知 | CP1 fail → 回材料用原文动词改写 → 重跑 | 返工轮次 +1，记录检查名 |
| containment 画成箭头 | 改成分组框 | 同上 |
| 图例缺项 / 孤儿项 | 以数据表为基准修图例 | 检查名 + 修了几项 |
| 调色板 < 类别数 | 补齐或删冗余类别 | 类别数、颜色数 |
| 字体缺失 | `font.cjk` warn + `uncertainty` | 是否影响 PNG 预览 |
| PDF 不可抽取 | 报不可抽取，不伪造文本 | backend 字段 |
| 渲染/导出致命错 | 写 `status=failed` 的 result.json | exit 1、`fails=[pipeline]` |
| 编辑目标不存在 | 判为编辑失败并查字段名 | 请求条数 vs 记录条数 |
| 契约门不过 | 修对应项重跑到 VALID | G 门编号 |
| 用了 `--skip-checks`/`--no-lint` | **不计入对照记录**（G1） | 标注"仅迭代用" |

### 7. 资源文件说明（路径相对技能根，调用一律 `"$SKILL_DIR/..."`）

| 入口 | 角色 | CLI |
|-|-|-|
| `scripts/main.py` | 流水线入口 | `--case --manifest --out --work --edit-svg --base-name --exports --dpi --skip-checks --lint --no-lint --fixed-time --doc-check` |
| `scripts/extract.py` | 材料→候选 ER 清单草稿 | `--inputs --out --base-dir` |
| `scripts/pdftext.py` | PDF 文本抽取（含 stdlib 回退） | `--pdf --out` |
| `scripts/textfont.py` | 字体栈探测 | `--list --probe` |
| `scripts/spec_lint.py` | CP1 生成前 lint | `--manifest --dict --json` |
| `scripts/manifest.py` | ER 清单加载/规范化（位置参数） | `<manifest.json>` |
| `scripts/layout.py` | 布局引擎（库模块） | `—` |
| `scripts/svgbuilder.py` | 分层可编辑 SVG 构建（库模块） | `—` |
| `scripts/render.py` | matplotlib 镜像渲染（库模块） | `—` |
| `scripts/checks.py` | CP2 产物检查（库模块） | `—` |
| `scripts/edit.py` | 源文件级增量编辑 | `<figure.svg> <edits.json>` |
| `scripts/validate_result.py` | 契约独立校验 G1–G8 | `--case --result --out --json` |
| `scripts/selftest.py` | 模块级自测 | `—` |
| `scripts/run_examples.py` | 一键复现三示例 | `--out --keep` |
| `scripts/report.py` | 结果渲染辅助（库模块） | `—` |

| 其它文件 | 用途 |
|-|-|
| `references/GAIN-PROTOCOL.md` | **本包新增**：对照协议（F1–F8）、指标定义（I1–I10）、实测记录、记账模板、未测量清单 |
| `references/OUTPUT_CONTRACT.md` | `result.json` 契约 + G1–G8 硬门 + 四形态回显（**必读**） |
| `references/EDIT-ACTION-SCHEMA.md` | 编辑动作 → 字段名 → 记录 的对照表与反模式（G4 的依据） |
| `references/CHECK-INDEX.md` | 全部检查名的清单（级别 + 科学含义），指标取值的字典 |
| `references/failure-modes.md` | 题面 12 类失败形态 → 检测机制 → 处置（含对测量的影响） |
| `references/ER_MANIFEST.md` | 实体—关系清单规范（绘图唯一数据源） |
| `references/DRAWING_GRAMMAR.md` | 图形语法：关系语义→箭头/线型/颜色、方向判定、分组/层级、图例/数据映射 |
| `references/RUBRIC_MAP.md` | 五维评分（40/25/15/10/10）→ 本包文件/机制逐条映射 |
| `assets/relation-dict.json` | 连接规则字典（kind→arrow/line/dash/color，机器可读） |
| `assets/checklist.json` | CP1–CP5 检查点 + 自查清单（机器可读） |
| `examples/*` | 最小示例（schematic / chart / edit + 合成材料 + `EXPECTED-OUTPUT.md`），**示例非正式案例** |

### 8. 五维评分映射（交付前逐条自评；完整表见 `references/RUBRIC_MAP.md`）

| 维度 | 分 | 本包机制（可跑的检查，不是自述） | 证据文件 |
|-|-|-|-|
| 实际效果 | 40 | 材料→ER 清单→CP1→可编辑 SVG→PNG/PDF→result.json 一条命令跑通；每例的真实 exit code / 耗时 / 门控计数都留档 | `scripts/main.py`、`scripts/spec_lint.py`、`scripts/checks.py`、§3.4 |
| 使用增益 | 25 | 评价点"增益可验证性"由 `references/GAIN-PROTOCOL.md` 直接承担：对照条款 F1–F8、指标 I1–I10、**真实实测 R1–R13**、以及**明确写出的未测量项**；每次运行可按 §4 的 M0–M6 产出一条可比较记录 | `references/GAIN-PROTOCOL.md`、`TEST.md` |
| 创新增益 | 15 | ①CP1 **生成前** lint 门 ②SVG 内嵌 ER 清单 → 可增量编辑 ③stdlib PDF 抽取回退 + 诚实 backend ④导出前合规检查 ⑤共享字体探针 ⑥**把"归因于 Skill 的改进"与"未测量的改进"分开记录**（可核验性创新） | `scripts/spec_lint.py`、`scripts/edit.py`、`scripts/pdftext.py`、`scripts/checks.py`、§3.3/§3.5 |
| 可靠体验 | 10 | 自定位（任意 cwd 可跑，R2 给出同 sha 证据）；`--case` 兼容文件与目录；退出码 0/1/2 与 `status` 同向；G1–G8 决策规则专治"污染测量"的分支；失败分支仍写 result.json | §5、§6、`references/failure-modes.md` |
| 生态贡献 | 10 | 说明/依赖/字体/参数/示例/限制/维护齐全；可复用资产：对照协议与记账模板、指标字典、检查名索引、连接规则字典、CP 清单、契约校验器、三示例题集 | `README.md`、`references/*`、`assets/*`、`examples/*` |

### 9. 自查清单（提交前逐行确认；机器版 `assets/checklist.json`）

- [ ] 实体名逐字出自材料，无材料外基因/浓度/时间点/单位；
- [ ] 每个关系方向与材料一致（激活≠抑制、上下游不颠倒、包含用分组）；
- [ ] CP1 `{"valid": true}`：kind 可映射、containment 用分组、图例双向、调色板 ≥ 类别数；
- [ ] 数值/坐标/单位与数据表逐项一致，**改数据后图确实重绘**（R6 式验证）；
- [ ] `figure.svg`：文字可选、图层可拆、带 `id` 与 `data-*`、内嵌 ER 清单；
- [ ] 导出件：PDF 可打开；PNG 有效 DPI 达标；色彩 RGB 族；
- [ ] `result.json` 含全部契约键 + `case_id`，契约四形态回显无 `null`；
- [ ] `validate_result.py`（G1–G8）输出 VALID，退出码 0；
- [ ] 编辑任务：**请求条数 == `change_records` 条数**（G4），未改动元素保持原样；
- [ ] **对照记录里"未测量"写得出来**：凡未跑过基线臂的增益声明，一律标未测量（G6）；
- [ ] 最后一次交付运行**没有**用 `--skip-checks` / `--no-lint`（G1）；
- [ ] 形态：仅 7 种文本扩展名、无 `__pycache__`、≤50 文件、≤500KB/文件、≤2MB、包内无本机绝对路径。

### 10. 依赖与限制

- Python 3.9+（实测 3.13）；运行必需 **matplotlib / Pillow / numpy**，reportlab 可选；
  PDF 抽取按 fitz → pypdf → PyPDF2 → **stdlib 回退**逐级降级。
  建议先跑 `python "$SKILL_DIR/scripts/selftest.py"`；
- **平台运行契约**：技能装在 `/skills/weekly-skill`；输入 `/input/case.json` + `/input/task.md`；
  中间产物 `/app/work`；最终产物 `/app/output`。预算 64 请求 / 900 秒 / 16384 token/响应
  —— 先落盘可用部分产物，再增量改进；**F3 要求对照时预算一致**；
- **资源形态（硬约束）**：仅 UTF-8 文本（`.md/.py/.json/.txt/.csv/.yaml/.yml`），
  ≤50 个、单文件 ≤500KB、合计 ≤2MB、无符号链接；图稿与渲染件一律运行时生成；
- **已知限制（如实标注）**：预览是与 SVG 同源的 matplotlib 镜像（语义一致、非逐像素）；
  PDF 字体嵌入审计为尽力而为；CJK 渲染依系统字体；`extract.py` 只产候选草稿；
  走 `--edit-svg` 时 `edits` 字段不生效（用 `edit_requests`）；
  **`edit.*` 问题只进 stdout**，不进 result.json、不改退出码；
  **最重要的一条**：本包**没有**跑过"不加载 Skill 的基线臂"，因此不声称
  在平台打分上一定更高——只声称交付了可复跑的对照协议与自身实测读数。

### 11. 禁止事项

- 不提交预制答案/正式案例输出；示例只用于演示接口与流程，**示例产物不入包**；
- 不编造缺失的软件状态或科学数据（来源里没有的实体/数值一律不画）；
- 不宣称未经测量的增益：**没有基线臂读数就只能写"未测量"**（G6/F8）；
- 不丢弃失败样本后重新跑直到好看（G5/F7）；
- 不为"好看"改关系颜色（改色 = 图例不一致，且会污染 I6/I7 读数）。
