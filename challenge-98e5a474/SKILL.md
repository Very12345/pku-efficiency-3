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
