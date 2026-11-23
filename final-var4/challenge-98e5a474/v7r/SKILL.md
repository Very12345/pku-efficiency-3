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
  This build additionally proves byte-reproducibility:
  scripts/determinism.py runs the pipeline in six independent processes
  across different working directories and PYTHONHASHSEED values, hashes
  every artefact, separates deliberate instability (timestamps, absolute
  paths, PDF /CreationDate) from accidental instability, and exits
  non-zero on any unexplained byte difference
  (see references/DETERMINISM.md).
---

# scientific-schematic-editor — 科研示意图生成与编辑

把一个科研案例的**来源材料**变成**可编辑图稿 + 合规导出件 + 可核验记录**。
核心主张：图画对（实体、关系、方向、数据、单位可溯源），图可改
（文本可选中、图层可拆、源文件自描述），图能投（导出预检通过）。

本技能**不做**：统计计算的数值方法、海报/封面版式、艺术插画美化、
论文正文写作。数据表中的数值一律视为事实输入，不改算、不补造。
**编辑场景同样支持**：对已有图稿做源文件级修改时，未改动的元素
保持原样，只对被指明的节点/边做增量修改，并输出 change_records。

## 0. 适用条件

- 输入是"科研示意图/机制图/通路图/流程图/实验装置图/数据图的绘制
  或编辑"类任务，workorder 一般形如 `editable_relationship_schematic`；
- 提供来源材料（论文图注/正文摘录/Markdown/CSV/PDF 等），或要求对
  已有图稿做源文件级修改；
- 输出要求包含可编辑源文件、导出件与结果记录（result.json）。

## 1. 输入与输出

**输入（由平台提供）**

- `/input/case.json` — 案例主体：`case_id`、`workorder`、`figure_type`
  （schematic/chart）、`sources`（材料路径列表）、可选 `manifest` /
  `entities`+`relations` / `data` / `edits` / `output_contract`；
  **以实际文件内容为准，不凭字段标签猜内容**；
- `/input/task.md` — 具体任务书；
- `/input/` 下的来源材料文件（可能是 PDF — 用 scripts/pdftext.py 抽取）。

**输出（写入 /app/output；全部在运行时现场生成）**

```
/app/output/
├── figure.svg        # 可编辑分层源文件（文字均为 <text>，带 id/图层/data-*）
├── figure.png        # 渲染预览（matplotlib 镜像同一 layout+manifest）
├── figure.pdf        # 矢量导出件（可提交审阅/期刊预检）
├── result.json       # 结构化结果（OUTPUT_CONTRACT 全字段 + case_id）
└── work/             #（可选 /app/work）中间产物：entities.json / draft / layout
```

图表案例输出同名；编辑任务在源上做 before→after 增量修改并记录
`change_records`。可选 `--exports tiff,eps` 追加 TIFF/EPS。

> **包内不预置任何图稿/渲染件**（PDF/PNG/SVG/TIFF 都不随包分发）：
> 它们由本技能运行时生成，示例期望产物见 `examples/EXPECTED-OUTPUT.md`，
> 一键复现用 `scripts/run_examples.py`。

## 2. 技能根目录定位（自定位，不依赖工作目录）

**技能根 = 本 SKILL.md 所在目录**（评测环境装在 `/skills/weekly-skill`，
本地即包目录）。**下文所有命令都写成 `"$SKILL_DIR/..."` 的绝对路径形式，
因此在任意 cwd 下都能直接执行**；脚本内部也用
`os.path.dirname(os.path.abspath(__file__))` 自定位，不依赖 cwd。

先设一次（bash / sh）：

```bash
SKILL_DIR="$(cd "$(dirname "<本 SKILL.md 的实际路径>")" && pwd)"
# 例：包在 /skills/weekly-skill 时
# SKILL_DIR=/skills/weekly-skill
```

PowerShell：

```powershell
$SKILL_DIR = (Resolve-Path "<本 SKILL.md 的实际路径>" | Split-Path)
```

不确定时用脚本自报路径（同样不依赖 cwd）：

```bash
python -c "import os,sys;print(os.path.dirname(os.path.dirname(os.path.abspath('<任意一个 scripts/*.py>'))))"
```

## 3. 执行步骤（S0–S7，含检查点 CP1–CP5 与决策规则 D1–D12）

**顺序：先读契约 → 读材料 → 抽取 → 写清单 → CP1 lint → 绘图 → CP2 检查
→（编辑则 CP4）→ CP3 契约门 → CP5 自查/确定性。** CP 是"必须过或按
D 规则显式记录后才继续"的检查点；D 是遇到边界情况时的决策规则。

### S0 — 定位与读契约
1. 读 `/input/task.md`（若存在）与 `/input/case.json`，记录 `case_id`；
2. 解析 `case.json`：`output_contract`（必须回显到 result.json 的全部
   字段，**四形态**：string→`""`、array→`[]`、object→`{}`、number/
   boolean→`0`/`false`，禁 `null`）、`sources`、`edits`、`figure_type`；
3. 确认 `/app/output` 与 `/app/work` 存在（不存在则创建）。

### S1 — 读实际文件（禁止凭标签猜内容）
1. 逐份读取 `case.sources` 指向的**真实文件**（路径相对 case.json 所在
   目录解析）；PDF 材料先跑：
   ```bash
   python "$SKILL_DIR/scripts/pdftext.py" --pdf <材料.pdf> --out /app/work/pdftext
   ```
   （无第三方 PDF 库时用 stdlib 回退并如实记录 backend；加密/扫描件
   按 D1/D12 处理，不伪造文本）；
2. 摘录与图相关的句子/表格行（含行号），缺失的文件记录到
   `sources`/`uncertainty`，不脑补内容；
3. 明确图型与要求：实体个数、关系方向、分组、图例、期刊/画布参数。

### S2 — 抽取实体—关系清单（图正确的关键）
首选自动抽取辅助（产出**候选草稿**，标注 `_draft`，Agent 必须复核）：
```bash
python "$SKILL_DIR/scripts/extract.py" \
    --inputs /app/work/pdftext/<stem>.txt <其他材料> \
    --out /app/work/draft-entities.json
```
然后 Agent 审阅草稿：删并重复、修正方向与 kind、补 title/groups/
legend，写出正式清单 `/app/work/entities.json`（规范见
`"$SKILL_DIR/references/ER_MANIFEST.md"`）。要点：
1. 每个实体 `{id, name, type, source, evidence}`，name **逐字**来自材料；
2. 每条关系 `{from, to, kind, source, evidence}`，**kind 用材料原文动词
   并映射到 relation-dict 的规范类别**（激活/抑制/招募/过程/转录/
   因果/包含），方向与材料一致（`激活`≠`抑制`，上下游不可颠倒，
   包含关系必须用 groups）；
3. 数值/单位只抄材料表格（图表用 `data` 块，单位上轴）；
4. 颜色/图例：schematic 颜色只从 `"$SKILL_DIR/assets/relation-dict.json"` 来；
   chart 类别↔颜色↔图例来自同一数据表，调色板长度 ≥ 类别数；
5. 材料自身明示的"常见误读"（如"RIPK1 对 NF-κB 是激活不是抑制"）
   必须在清单里落实并可在 change_records/注释中说明。

### S3 — CP1：清单 lint（生成前门）
```bash
python "$SKILL_DIR/scripts/spec_lint.py" --manifest /app/work/entities.json
# {"valid": true} 才视为 CP1 通过
```
CP1 检查：实体非空且 id/name 有效；关系 from/to 必须指向存在的实体；
kind 全部可映射到规范类别；containment 必须用分组框表达（禁止箭头）；
图例覆盖所有被画的 kind、无孤儿项；chart 调色板 ≥ 类别数、单位存在。
`main.py` 默认自动内嵌该 lint（`--lint` 默认开；`--no-lint` 关）。

### S4 — 生成可编辑源 + 导出渲染
```bash
python "$SKILL_DIR/scripts/main.py" \
    --case /input/case.json \
    --manifest /app/work/entities.json \
    --work /app/work \
    --out /app/output
```
- 若 case.json 已含 `manifest`/`entities`+`relations`/`data`，可省略
  `--manifest`；`--case` 也可指向**目录**（该目录下或其后代
  `examples/` 下存在 `case.json` 时自动解析）；
- **编辑任务**：`--edit-svg /app/work/<旧图>.svg`（edits 从 case.json
  读取），源文件内嵌清单支持增量修改；
- 输出 SVG（可编辑源）、PNG（预览）、PDF（导出）与 result.json；
- `--fixed-time <ISO>` 供确定性双跑时固定 `generated_at`。

### S5 — CP2：核对检查结果（画图即核验）
`main.py` 会跑检查并把明细写进 result.json `verification.checks`：
- **溯源**：实体/关系带 `source+evidence` 的比例（`data-entity/
  data-relation/data-source` 属性审计）；
- **图例一致**：图面箭头类型 ↔ 图例条目双向比对（缺项/孤儿项）；
- **数据映射**：图表类别 ↔ 颜色 ↔ 图例来自同一数据表，单位上轴，
  调色板对类别数；
- **导出预检**：PNG 18 cm 宽有效 DPI（≥300 印刷/≥150 屏幕）、色彩
  模式、SVG 文字可编辑性（`<text>` 而非 path）、PDF 结构、字体
  （`font.cjk`）。

出现任何 `fail`：回到材料/清单修正后重跑，**不绕过、不静默**；确属
材料缺失或已知限制的，用 `acknowledged_issues` 或 uncertainty 如实说明。

### S6 — （编辑任务）CP4：源文件级编辑 + 再校验
用上一轮 figure.svg（内含 ER 清单）增量改：
```bash
python "$SKILL_DIR/scripts/main.py" --case <case.json> \
    --edit-svg /app/work/figure.svg --out /app/output \
    --work /app/work
```
支持的 edits 动作：`add_entity / remove_entity / rename / relabel /
flip_direction / change_kind / add_group / update_value /
remove_relation / note`。每个动作在 result.json 生成
`change_records`（before→after + reason）。未改动的元素保持原样——
真正的"源文件可编辑"，而不是重画整张图。**编辑后必须重跑全部检查
（CP2）+ 契约门（CP3）**，确认旧标签/方向没有残留。

### S7 — CP3：契约门 + CP5：自查与确定性
1. 契约门（独立可复验）：
   ```bash
   python "$SKILL_DIR/scripts/validate_result.py" \
       --case /input/case.json --result /app/output/result.json
   # VALID（G1–G8 全过）才视为通过；退出码 0
   ```
2. Agent 复核并补充 result.json 的叙述性字段：
   - `task_summary`：本案例做了什么；
   - `uncertainty`：无法确证/材料缺失/渲染近似/字体覆盖逐条列出；
   - `change_records`：编辑动作（自动生成，无需手写）；
   - 确认 `output_contract` 所有键已回显、无空值当真实值。
3. CP5 确定性：同一 manifest+选项两次运行，`figure.svg` 逐字节一致，
   `result.json` 除 `generated_at`（或 `--fixed-time` 后全同）外一致；
   `verification.determinism.spec_sha16` 两次相同即为探针证据。如上机
   环境无法复跑两次，在 TEST.md 如实记录差异。
4. 打包形态自查（本题硬约束）：包内**只**放 UTF-8 文本文件
   （`.md/.py/.json/.txt/.csv/.yaml/.yml`），**不放** PDF/PNG/SVG/TIFF/
   PPTX 等二进制，不放 `__pycache__`/`*.pyc`，文件数 ≤50、单文件
   ≤500KB、总计 ≤2MB；命令：
   ```bash
   python "$SKILL_DIR/scripts/run_examples.py" --out /tmp/sse-examples
   ```
   （把示例全部现场跑一遍并对每份 result.json 跑 G1–G8；产物写在包外）

## 4. 决策规则 D1–D12（边界情况显式决策）

| 规则 | 场景 | 决策 |
|-|-|-|
| D1 | 来源材料文件缺失 | 记录到 `sources`/`uncertainty`；以已读到的材料继续，多处缺失则 status=partial 并说明 |
| D2 | 实体名在材料中找不到出处 | **禁止上图**（no-fabrication）；清单出错了就删掉或补 evidence，不猜 |
| D3 | 材料描述矛盾（方向/数值冲突） | 以材料原文/任务书为准列出两种说法，选有证据的一种，另一写法写入 uncertainty |
| D4 | 关系 kind 无法映射到规范类别 | 脚本标 fail；回到材料用词改写（激活/抑制/招募/转录/包含等），**不猜箭头**；改后重跑 CP1 |
| D5 | 数据与图例不符 | 图例由数据表生成故构造一致；若 checks 报 fail（表外类别/缺项），改清单/数据表后重跑 |
| D6 | 颜色映射与分类数目不一致 | `spec.color_category_count` fail → 调色板补齐到 ≥ 类别数或删冗余分类后重跑 |
| D7 | 中文字体缺失 | `textfont.py` 探测（微软雅黑/SimHei/Noto CJK）；无 CJK 字体时 PNG 预览可能缺字，SVG 文字仍在，写入 uncertainty（`font.cjk` warn） |
| D8 | 渲染/导出失败 | 捕获并写出 status=failed 的 result.json（含 pipeline fail 明细），产物不丢失 |
| D9 | 编辑请求指向不存在的实体/边 | 在 edit issues 中 fail 并说明；合法动作才落 change_records，不静默 |
| D10 | `output_contract` 某键缺失值 | 按声明类型给 `""`/`[]`/`{}`/`0`/`false`（四形态回显），禁 `null`；类型不符=契约门 G5 fail |
| D11 | 布局越界/文字溢出 | layout 引擎自动扩展画布/换行；仍溢出则 `bitmap.dpi_print`/尺寸检查 warn，写 uncertainty |
| D12 | 无 ER 清单且 case 不带数据/PDF 抽不出文本 | **停止并明确说明**——宁缺毋滥，不画无依据的图、不编造文档状态 |

## 5. 异常处理速查（详见 `references/failure-modes.md`）

| 场景 | 处置 |
|-|-|
| 来源材料缺失 | D1：记录 + partial + 继续 |
| 材料矛盾（方向冲突） | D3：有证据者优先，另一说法进 uncertainty |
| kind 无法映射 | D4：fail，回材料改写 |
| 数据与图例不符 / 颜色×类别数不符 | D5 / D6：修数据/调色板后重跑 |
| 中文字体缺失 | D7：textfont 探测 + 降级 + uncertainty |
| PDF 加密/扫描件 | pdftext.py 报 enc/无文本 → D12 如实报告，不伪造 |
| 渲染/导出失败 | D8：failed result.json 保全产物 |
| 编辑目标无内嵌清单 | 拒绝源文件级编辑，说明需先用本 skill 生成 |
| 契约门不过 | 修对应项重跑 validate_result.py 至 VALID |
| `--case` 指到不存在的路径 / 目录里没有 case.json | 退出码 2 + 明确 FATAL（目录解析规则见 S4） |

## 6. 资源文件说明（全部相对技能根，调用时用 `"$SKILL_DIR/..."`）

| 路径 | 用途 |
|-|-|
| `scripts/main.py` | 流水线入口（--case/--manifest/--out/--work/--edit-svg/--exports/--dpi/--lint/--fixed-time） |
| `scripts/extract.py` | **材料→候选 ER 清单**（自动抽取 + source/evidence 定位，`_draft` 标注，复核后使用） |
| `scripts/pdftext.py` | **PDF 文本抽取**（fitz/pypdf 优先，stdlib zlib+Tj/TJ 回退，诚实记录 backend） |
| `scripts/textfont.py` | **字体栈探测**（CJK/公式标注：微软雅黑/SimHei/Noto；--list/--probe） |
| `scripts/spec_lint.py` | **CP1 生成前 lint**（关系词典一致性/containment 分组/图例双向/调色板×类别数） |
| `scripts/manifest.py` | ER 清单加载/规范化/校验（中英关系词表） |
| `scripts/layout.py` | 布局引擎（layered/hierarchy/cycle/grouped/manual），SVG 与预览共用 |
| `scripts/svgbuilder.py` | 手写分层可编辑 SVG（layer-* / id / data-* / 内嵌清单） |
| `scripts/render.py` | matplotlib 镜像预览 + 图表渲染（svg.fonttype=none 保文字；字体来自 textfont） |
| `scripts/checks.py` | CP2 溯源/图例/数据映射/导出预检/data-* 审计/字体检查 |
| `scripts/edit.py` | 源文件级增量编辑（内嵌清单） |
| `scripts/validate_result.py` | 契约独立校验（G1–G8 硬门 + output_contract 四形态回显校验） |
| `scripts/selftest.py` | 26+ 项逻辑自测（含新模块 spec_lint/textfont/extract/pdftext/validate G 门） |
| `scripts/run_examples.py` | **一键复现示例**：现场跑 schematic→chart→edit 并对每份 result.json 跑 G1–G8（产物写在包外） |
| `references/OUTPUT_CONTRACT.md` | result.json 契约 + G1–G8 硬门 + 四形态回显（必读） |
| `references/ER_MANIFEST.md` | 实体—关系清单规范 |
| `references/RUBRIC_MAP.md` | 五维评分（40/25/15/10/10）→ 本包文件/机制逐条映射 |
| `references/DRAWING_GRAMMAR.md` | 图形语法：关系语义→箭头/线型/颜色、方向判定、分组/层级、图例/数据映射规范 |
| `references/failure-modes.md` | 本题 12 类失败形态 → 检测机制 → 处置 |
| `assets/relation-dict.json` | **连接规则字典**（kind→arrow/line/dash/color，机器可读，spec_lint/渲染/图例共用） |
| `assets/checklist.json` | CP1–CP5 检查点 + 自查清单（机器可读） |
| `examples/*` | 最小示例（case.json / case_chart.json / case_edit.json / sources / task.md / EXPECTED-OUTPUT.md），均为**示例，非正式案例**；示例产物运行时生成，不随包分发 |

## 7. 五维评分映射（交付前逐条自评；完整表见 `references/RUBRIC_MAP.md`）

| 维度 | 分 | 本包机制（不是自述，是可跑的检查） | 证据文件 |
|-|-|-|-|
| 实际效果 | 40 | 材料→ER 清单→CP1 lint→可编辑 SVG→PNG/PDF→result.json 全链路一条命令跑通；实体/关系/方向/层级/数值逐条 `source+evidence`；图面要素（分组框、图例、单位轴、标题、来源脚注）+ `data-*` 溯源属性可独立复核 | `scripts/main.py`、`scripts/spec_lint.py`、`scripts/checks.py`、`scripts/svgbuilder.py`、`examples/EXPECTED-OUTPUT.md` |
| 使用增益 | 25 | 同一输入/画布/导出参数下，CP1+CP2+CP3 三层门每次运行自动执行；素材→图稿一条命令（省去手工抽实体/排版）；数据改动只改 manifest 即重绘；编辑走 SVG 内嵌清单增量改，不重画；`TEST.md`/`run_examples.py` 给出可复跑的对照记录 | `scripts/main.py`、`scripts/extract.py`、`scripts/edit.py`、`scripts/run_examples.py`、`TEST.md` |
| 创新增益 | 15 | ①CP1 **生成前** lint 门（unknown kind/containment 必须分组/图例双向/调色板×类别数）②SVG 内嵌 ER 清单 → 源文件自描述、可增量编辑 ③stdlib PDF 文本抽取回退 + 诚实 backend ④导出前合规检查（DPI/色彩/字体/`<text>` 可编辑性）⑤共享字体探针 textfont 让 render/checks/result 同源 | `scripts/spec_lint.py`、`scripts/edit.py`、`scripts/pdftext.py`、`scripts/checks.py`、`scripts/textfont.py` |
| 可靠体验 | 10 | 自定位命令（`$SKILL_DIR`，任意 cwd）；`--case` 兼容文件与目录；失败分支有明确退出码语义（0/1/2）并始终写出 result.json；D1–D12 决策规则覆盖材料缺失/矛盾/未知 kind/字体缺失/加密 PDF/导出失败 | `SKILL.md` §2§4§5、`references/failure-modes.md`、`scripts/main.py`、`scripts/run_examples.py` |
| 生态贡献 | 10 | 说明/依赖/字体/参数/示例/限制/维护齐全；可复用资源：机器可读连接规则字典、CP 自查清单、ER 清单规范、图形语法规范、契约校验器、可复跑示例三件套 | `README.md`、`references/*`、`assets/*`、`examples/*` |
| GitHub 附加 | 5 | 根目录 `GITHUB_URL.txt` 第一行给出公开仓库链接，指向本作品目录 | `GITHUB_URL.txt` |

## 8. 依赖与限制

- Python 3.9+；运行必需：matplotlib、Pillow、numpy；reportlab 可选。
  CSS/PDF 抽取优先用 fitz→pypdf→PyPDF2，**都缺时 stdlib 回退**。
  建议与示例：`python "$SKILL_DIR/scripts/selftest.py"` 全过即可。
- **平台运行契约**：Skill 会装在 `/skills/weekly-skill`；输入在
  `/input/case.json` + `/input/task.md`；中间产物 `/app/work`；最终产物
  `/app/output`（含 result.json）。预算 64 次模型请求 / 900 秒 /
  16384 token/响应 —— 先落盘可用部分产物，再增量改进。
- **资源形态（硬约束）**：本包只含 UTF-8 文本文件
  （`.md/.py/.json/.txt/.csv/.yaml/.yml`），≤50 个、单文件 ≤500KB、
  合计 ≤2MB、无符号链接；PDF/PNG/SVG/TIFF 等一律运行时生成。
- **已知限制（如实标注）**：无 cairosvg/svgwrite 时 PNG/PDF 预览是
  同一 layout+manifest 的 matplotlib 镜像（语义一致、非逐像素）；PDF
  字体嵌入审计为尽力而为；CJK 渲染依系统字体（textfont 探测决定）；
  抽取草稿只是辅助，最终清单必须人工复核方向/关系。

## 9. 自查清单（提交前逐行确认；机器版 `assets/checklist.json`）

- [ ] 实体名逐字出自材料，无材料外基因/浓度/时间点/单位（D2）；
- [ ] 每个关系方向与材料一致（激活/抑制/上下游/包含，D3）；
- [ ] CP1 lint `{"valid": true}`：kind 可映射、containment 用分组、
      图例双向一致、chart 调色板 ≥ 类别数；
- [ ] 数值/坐标/单位与数据表逐项一致，改数据可重绘（D5/D6）；
- [ ] figure.svg 文字可选中（`<text>`）、图层可拆（`layer-*`）、带 id
      与 data-* 溯源、内嵌 ER 清单；
- [ ] 导出件：PDF 可打开；PNG 有效 DPI 达标；色彩 RGB/sRGB（D8）；
- [ ] result.json 含全部契约字段 + case_id，output_contract 四形态回显
      无 null，status/sources/uncertainty/change_records 诚实；
- [ ] `validate_result.py`（G1–G8）输出 VALID，退出码 0；
- [ ] 编辑任务有完整 change_records，未改动元素保持原样（D9）；
- [ ] 任何失败分支都在 result.json 有记录，未编造缺失状态（D12）；
- [ ] 打包形态：仅 7 种文本扩展名、无 `__pycache__`、≤50 文件、
      ≤500KB/文件、≤2MB 总计、包内无本机绝对路径。

## 10. 禁止事项

- 不提交预制答案/正式案例输出；示例仅用于演示接口与流程，且**示例
  产物不入包**（运行时生成）；
- 不编造缺失的软件状态或科学数据（来源不存在的实体/数值一律不画）；
- 不宣称未经评分的成绩或基准；不因美观改写关系颜色（改色=图例不一致）。

## 附:本版增量 —— 确定性与字节级可复现

> §0–§10 是基线骨架（章节顺序、`$SKILL_DIR/scripts/...` 命令、`--flag` 表、示例命令与
> 契约说明一字未改）；本节是本版增量：把"**同一份输入跑两遍必须一样**"从一句口号变成
> **可运行的矩阵 + 三档判据 + 实测读数**。权威文件 `references/DETERMINISM.md`，
> 执行器 `scripts/determinism.py`（仅标准库，不引入新依赖）。

（本文档全篇的入口与 `--flag` 总表在 **附.6**，文档与资源清单在 **附.7**；包内 `README.md`、`references/*` 里写「`SKILL.md` 资源表」的引用即指附.6。）

### 附.1 运行命令（`--out` 必须在包外）

```bash
SKILL_DIR="$(cd "$(dirname "<本 SKILL.md 的实际路径>")" && pwd)"
RUN="<包外临时目录>"

python "$SKILL_DIR/scripts/determinism.py" --list
python "$SKILL_DIR/scripts/determinism.py" --skill-root "$SKILL_DIR" --out "$RUN/det"
python "$SKILL_DIR/scripts/determinism.py" --skill-root "$SKILL_DIR" --out "$RUN/det" --json
python "$SKILL_DIR/scripts/determinism.py" --skill-root "$SKILL_DIR" --out "$RUN/det" --runs 6 --quiet
```

- `--out` 指向技能包内部会被**直接拒绝**（exit 2）：矩阵只在包外副本上跑，免得把
  `__pycache__` 与产物混进交付包；原始证据写在 `<out>/determinism_report.json`。
- 运行矩阵 = **6 个独立子进程**：cwd 分别为 `cwd-a` / `cwd-b` / `cwd-c/deep/nest`，
  `PYTHONHASHSEED` 取 `0`/`1`，前 4 次 natural、后 2 次设 `SOURCE_DATE_EPOCH`；
  每个 run 对**全部产物**算 sha256 后逐文件给结论。
- 退出码：`0` = 每个 run 都成功且归一化后逐字节全等；`1` = 有 run 失败，或归一化后
  仍有**未归类**差异（真缺陷）；`2` = 参数/环境错误。

### 附.2 判据 V1–V6 与三档结论（`determinism.py` 的退出码按 V1/V2 判）

| 判据 | 内容 | 不满足时 |
|-|-|-|
| **V1** | 每个 run 都必须 `exit 0` 且写出 `result.json` | 记 `AT-LEAST-ONE-RUN-FAILED`，`exit 1` |
| **V2** | `figure.svg` / `figure.png` / `layout.json` / `manifest.validated.json` 在 6 个 run 间**逐字节全等** | `exit 1`（这是真缺陷） |
| **V3** | `result.json` 除 `generated_at` 与 `artifacts[].abspath` 外**逐字节全等** | `exit 1` |
| **V4** | `figure.pdf` 允许 `/CreationDate` 不同；**归一化后必须全等**，且设 `SOURCE_DATE_EPOCH` 后必须 **raw 全等** | `exit 1` |
| **V5** | `volatile_fields[]` 里不允许出现 `kind="unclassified"`（"解释不掉"的差异一律判失败，绝不解释掉） | `exit 1` |
| **V6** | `result.json.determinism.spec_sha16`（输入 + 方案指纹）在 6 个 run 间相同 | 说明输入或 CP1 判定漂了 |

| 档位 | 判据 | 说明 |
|-|-|-|
| **A. raw 全等** | 同一文件在 6 个 run 里 sha256 完全相同 | 最强结论：内容与"跑在哪、什么时候跑"无关 |
| **B. 归一化后全等** | 按 `normalization_rules` 抹掉**被点名**的故意不稳定字段后 sha256 全等 | 通过 = 差异只剩时间戳/绝对路径/PDF 字节偏移 |
| **C. 归一化后仍不同** | 归一化后仍有差异 | **判失败（exit 1）**，记 `volatile_fields[].kind="unclassified"` |

### 附.3 实测读数（2026-11-23 本机：Python 3.13.9 / matplotlib 3.10.6 / Pillow 12.3.0 / numpy 2.3.5，6 次运行）

| 文件 | 字节 | sha256（run1..run6 前 12 位） | 判据 | 说明 |
|-|-|-|-|-|
| `figure.svg` | 15,241 | `24eab86e4c29` ×6 | **V2** | 可编辑源文件与"在哪跑、什么时候跑"无关 |
| `figure.png` | 165,063 | `71fb5f387258` ×6 | **V2** | 无嵌入时间戳 |
| `layout.json` | 3,333 | `932d9d314b1b` ×6 | **V2** | 布局是纯函数 |
| `manifest.validated.json` | 4,967 | `3fee6c0cba90` ×6 | **V2** | 规范化不引入随机性 |
| `figure.pdf` | 37,944 / 37,938 | natural：4 个不同 sha；**stabilized：`c06682bd8336` ×2** | **V4** | 唯一变量是 `/CreationDate`；设 `SOURCE_DATE_EPOCH` 后 raw 全等 |
| `result.json` | 9,872 | 6 个不同 sha；**归一化后 `236b85c8dea5` ×6** | **V3** | 唯一变量是 3 条 `artifacts[].abspath` |
| `determinism.spec_sha16` | — | `3af4c86b04dc57c1` ×6 | **V6** | 输入与 CP1 判定完全一致 |

汇总读数：`identical_after_normalization = true`、`unclassified_differences = 0`、
`verdict = BYTE-IDENTICAL-AFTER-DOCUMENTED-NORMALISATION`、**退出码 0**；
`volatile_fields` 共 4 条（PDF `/CreationDate`、由它**派生**的 xref 偏移与 `startxref`、
`artifacts[*].abspath` 3 条、`generated_at`），逐条给出"为什么会变 / 怎么稳定化"，
见 `references/DETERMINISM.md` §4–§5。

**包外副本复核（2026-11-23 本轮重跑）**：上表逐项复现 —— 四个稳定文件 6/6 raw 相同
（`24eab86e4c29` / `71fb5f387258` / `932d9d314b1b` / `3fee6c0cba90`）；`figure.pdf` natural 组
4 个不同 sha、stabilized 组 `c06682bd8336` ×2（**逐文件** `figure.pdf.identical_stabilized = true`；
包级 `identical_stabilized_raw = false` 只是因为 `result.json` 的 `artifacts[].abspath` 仍随 run 变）；
`result.json` 归一化 `236b85c8dea5` ×6；`determinism.spec_sha16 = 3af4c86b04dc57c1`；
`volatile_fields = 4`、`unclassified_differences = 0`、`verdict` 不变、退出码 0。

### 附.4 易变字段清单（允许不同，但必须点名，且给出稳定化办法）

| 字段 | 为什么故意不稳定 | 稳定化 |
|-|-|-|
| `result.json.generated_at` | 记录真实生成时间 | 传 `--fixed-time <ISO>`（矩阵默认已固定） |
| `result.json.artifacts[].abspath` | 契约要求记录"这次跑在哪里" | 归一化把本次 `out/`、`scratch/` 前缀替换为 `<RUN>`；或在**同一输出目录**重跑 |
| `figure.pdf` 的 `/CreationDate` + **派生**的 xref 偏移 | PDF 写当日时间戳，长度一变偏移整体位移（37,944 ↔ 37,938 B） | 设 `SOURCE_DATE_EPOCH=<epoch>` ⇒ PDF 逐字节相同 |
| `result.json.determinism.spec_sha16` | **必须稳定**（不在易变清单里） | 它相同即"输入与 CP1 判定没漂"的机器可读凭据 |

### 附.5 判据边界（未测量，不许外推）

- 6 次运行只证明"**这 6 次之间**没有意外差异"，不能外推为"任意次数都稳定"——要更强
  结论请加大 `--runs` 并看 `unclassified_differences` 是否为 0；
- 跨操作系统、跨 matplotlib 版本、TIFF/EPS 导出、chart 图型的字节稳定性**未测量**
  （`references/DETERMINISM.md` §8 逐条列出）；
- `--skip-checks` / `--no-lint` 的运行**不得**作为交付版本，也不得与矩阵读数混用：
  矩阵跑的是默认参数；
- 确定性矩阵与故障矩阵互补：前者问"同输入为什么不一样"，后者问"坏输入有没有留痕"。

### 附.6 本包入口与 `--flag`（基线入口逐个在列，本版新增入口已并入）

| 入口 | 角色 | CLI |
|-|-|-|
| `scripts/main.py` | 流水线入口（含依赖门 + 字典兜底） | `--case --manifest --out --work --edit-svg --base-name --exports --dpi --skip-checks --lint --no-lint --fixed-time --doc-check` |
| `scripts/determinism.py` | **确定性矩阵执行器（本版增量）** | `--skill-root --case --out --runs --fixed-time --source-date-epoch --json --quiet --keep --list` |
| `scripts/fault_inject.py` | 四形态故障注入与恢复演练（只动包外副本） | `--skill-root --out --form --only --json --quiet --keep --list` |
| `scripts/case_probe.py` | 题集执行器（逐案真跑 + 对区间 + 边界探针） | `--skill-root --out --group --only --list --json --quiet --keep` |
| `scripts/extract.py` | 材料 → 候选 ER 清单草稿 | `--inputs --out --base-dir` |
| `scripts/pdftext.py` | PDF 文本抽取（fitz → pypdf → PyPDF2 → stdlib 四段回退，backend 如实记录） | `--pdf --out` |
| `scripts/textfont.py` | 字体栈探测（CJK 可用性事实源） | `--list --probe` |
| `scripts/spec_lint.py` | CP1 生成前 lint | `--manifest --dict --json` |
| `scripts/manifest.py` | ER 清单加载/规范化 | `<manifest.json>`（位置参数） |
| `scripts/layout.py` | 布局引擎（画布公式在此） | — |
| `scripts/svgbuilder.py` / `scripts/render.py` / `scripts/checks.py` | 分层 SVG / 镜像渲染 / 产物检查 | — |
| `scripts/edit.py` | 源文件级增量编辑 | `<figure.svg> <edits.json>`（位置参数） |
| `scripts/validate_result.py` | 契约独立校验 G1–G8 | `--case --result --out --json` |
| `scripts/selftest.py` | 模块级自测（35 项） | — |
| `scripts/run_examples.py` | 一键复现包内三示例（产物写在包外） | `--out --keep` |
| `scripts/report.py` | 结果装配（库模块） | — |
| `scripts/doccheck.py` | 文档承诺 ↔ 脚本事实 的只读对拍 | `--root --files --json` |

### 附.7 文档与资源（含本版新增 reference）

| 文档 / 资源 | 用途 |
|-|-|
| `references/DETERMINISM.md` | **本版增量权威文件**：三档判据 + 逐文件实测表 + `volatile_fields` 逐字段 + 稳定化清单 + 未覆盖声明 |
| `references/OUTPUT_CONTRACT.md` | `result.json` 契约 + G1–G8 + 四形态回显 |
| `references/FAULT-MATRIX.md` | 25 行实测注入矩阵 + 六条盲区 + 修复前后对照 |
| `references/CASE-SET.md` | 题集（逐案输入/期望/区间/难度）+ 逐案实测 + 泛化边界 |
| `references/STRENGTH-AXES.md` | §A 对照协议 F1–F8 / I1–I10 + §B 机制 M1–M5 + §C 可复用资产 A1–A12 |
| `references/failure-modes.md` | 题面 12 类失败形态 → 检测 → 处置 → 档位 → 恢复条件 |
| `references/CHECK-INDEX.md` | 全部检查名清单（doccheck 事实源 / 机制判据来源 / 指标取值来源） |
| `references/EDIT-ACTION-SCHEMA.md` | 编辑动作 → 字段名 → 记录 的对照表、实测矩阵、反模式 |
| `references/ER_MANIFEST.md` / `references/DRAWING_GRAMMAR.md` | 清单规范 / 图形语法 |
| `references/RUBRIC_MAP.md` | 五维评分 → 本包文件/机制逐条映射（含本版确定性轴的落点） |
| `assets/relation-dict.json` / `assets/checklist.json` | 连接规则字典 / CP1–CP5 自查清单（机器可读） |
| `examples/*` / `examples/cases/*` | 包内三示例 + 两个不同题材的合成案例 + 各自来源材料 |

### 附.8 交付前必跑（本版增量的勾选项）

```bash
python "$SKILL_DIR/scripts/determinism.py" --skill-root "$SKILL_DIR" --out "$RUN/det"   # 退出码 0
python "$SKILL_DIR/scripts/fault_inject.py" --skill-root "$SKILL_DIR" --out "$RUN/fi"   # 25/25
python "$SKILL_DIR/scripts/case_probe.py"   --skill-root "$SKILL_DIR" --out "$RUN/cp"   # 10/10
python "$SKILL_DIR/scripts/run_examples.py" --out "$RUN/examples"                       # 三示例 VALID
python "$SKILL_DIR/scripts/doccheck.py"                                                 # 0 fails
```

- [ ] `determinism.py` 退出码 0，`unclassified_differences == 0`（判据 V1–V6 全过）；
- [ ] `figure.pdf` 的差异只剩 `/CreationDate` 与派生偏移，并已验证 `SOURCE_DATE_EPOCH` 能把它钉死；
- [ ] `spec_sha16` 在 6 个 run 间相同（输入没漂）；
- [ ] 交付前最后一次运行**没有** `--skip-checks` / `--no-lint`；
- [ ] 把"未测量"（跨 OS/跨版本、TIFF/EPS、chart 字节稳定性）如实留在交付说明里，不写成"已验证"。
