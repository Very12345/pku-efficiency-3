---
name: scientific-schematic-editor
description: >-
  Generate and edit editable scientific schematics, mechanism/relationship
  diagrams, flow diagrams and data charts from source materials. Extracts an
  entity-relation manifest (traceable to sources), produces a layered editable
  SVG source plus PNG/PDF (and TIFF/EPS) exports, runs legend/data-mapping and
  export-compliance checks, and writes a structured result.json. Use when a
  task asks to draw, regenerate or edit a scientific figure from papers,
  tables or notes: 科研示意图/机制图/信号通路图/流程图/图表的生成与编辑.
---

# scientific-schematic-editor — 科研示意图生成与编辑

把一个科研案例的**来源材料**变成**可编辑图稿 + 合规导出件 + 可核验记录**。
核心主张：图画对（实体、关系、方向、数据、单位可溯源），图可改
（文本可选中、图层可拆、源文件自描述），图能投（导出预检通过）。

本技能**不做**：统计计算的数值方法、海报/封面版式、艺术插画美化、
论文正文写作。数据表中的数值一律视为事实输入，不改算、不补造。

## 0. 适用条件

- 输入是"科研示意图/机制图/通路图/流程图/数据图的绘制或编辑"类任务，
  workorder 一般形如 `editable_relationship_schematic`；
- 提供来源材料（论文图注/正文摘录/Markdown/CSV 等），或要求对已有
  图稿做源文件级修改；
- 输出要求包含可编辑源文件、导出件与结果记录（result.json）。

## 1. 输入与输出

**输入（由平台提供）**

- `/input/case.json` — 案例主体：`case_id`、`workorder`、`figure_type`
  （schematic/chart）、`sources`（材料路径列表）、可选 `manifest` /
  `entities`+`relations` / `data` / `edits` / `output_contract`；
- `/input/task.md` — 具体任务书（以**实际文件内容**为准）；
- `/input/` 下的来源材料文件。

**输出（写入 /app/output）**

```
/app/output/
├── figure.svg        # 可编辑分层源文件（文字均为 <text>，带 id/图层/data-*）
├── figure.png        # 渲染预览（matplotlib 镜像同一 layout+manifest）
├── figure.pdf        # 矢量导出件（可提交审阅/期刊预检）
├── result.json       # 结构化结果（OUTPUT_CONTRACT 全字段 + case_id）
```
图表案例输出同名；编辑任务在源上做 before→after 增量修改并记录
`change_records`。可选 `--exports tiff,eps` 追加 TIFF/EPS。

## 2. 技能根目录定位（自定位，不依赖工作目录）

**技能根 = 本 SKILL.md 所在目录**（评测环境装在 `/skills/weekly-skill`，
本地即包目录）。脚本用自己的文件位置自定位，任何 cwd 下都可用：

```bash
SKILL_ROOT="$(dirname "$(readlink -f "$0" 2>/dev/null || echo "$BASH_SOURCE")")"
```
或直接在 Python 里：`os.path.dirname(os.path.abspath(__file__))`。
下文统一写 `<skill_root>`，执行时替换为实际绝对路径。

## 3. 执行步骤

### Step 1 — 读实际文件（禁止凭标签猜内容）
1. 读 `/input/case.json`（JSON 解析）与 `/input/task.md`；
2. 逐份读取 `case.sources` 指向的**真实文件**（路径相对 case.json 所在
   目录解析），摘录与图相关的句子/表格行；文件缺失要记录，不脑补内容；
3. 明确图型与要求：实体个数、关系方向、分组、图例、期刊/画布参数。

### Step 2 — 抽取实体—关系清单（图正确的关键）
把材料转成 ER 清单，写到工作区 `/app/work/entities.json`，规范见
`<skill_root>/references/ER_MANIFEST.md`。要点：
1. 每个实体 `{id, name, type, source, evidence}`，name **逐字**来自材料；
2. 每条关系 `{from, to, kind, source, evidence}`，**kind 用材料原文动词**，
   方向与材料一致（`激活`≠`抑制`，上下游不可颠倒，包含关系用 groups）；
3. 数值/单位只抄材料表格（图表用 `data` 块）；
4. 自查：图里每个词都能在材料中找到出处——出现材料之外的基因名、
   浓度、时间点或单位 = 本题最典型错误，必须避免；
5. 材料自身明示的"常见误读"（如"RIPK1 对 NF-κB 是激活不是抑制"）
   必须在清单里落实并可在 change_records/注释中说明。

### Step 3 — 生成可编辑源 + 导出渲染
```bash
python <skill_root>/scripts/main.py \
    --case /input/case.json \
    --manifest /app/work/entities.json \
    --work /app/work \
    --out /app/output
```
- 若 case.json 已含 `manifest`/`entities`+`relations`/`data`，可省略
  `--manifest`；
- **编辑任务**：`--edit-svg /app/work/<旧图>.svg`（edits 从 case.json
  读取），源文件内嵌清单支持增量修改；
- 输出 SVG（可编辑源）、PNG（预览）、PDF（导出）与 result.json。

### Step 4 — 核对检查结果（画图即核验）
`main.py` 会跑检查并把明细写进 result.json `verification.checks`：
- **溯源**：实体/关系带 `source+evidence` 的比例；
- **图例一致**：图面箭头类型 ↔ 图例条目双向比对（缺项/孤儿项）；
- **数据映射**：图表类别 ↔ 颜色 ↔ 图例来自同一数据表，单位上轴；
- **导出预检**：PNG 18 cm 宽有效 DPI（≥300 印刷/≥150 屏幕）、色彩
  模式、SVG 文字可编辑性、PDF 结构。

出现任何 `fail`：回到材料/清单修正后重跑，**不绕过、不静默**；确属
材料缺失或已知限制的，用 `acknowledged_issues` 或 uncertainty 如实说明。

### Step 5 — 源文件级编辑（任务要求改图时）
用上一轮的 figure.svg（内含 ER 清单）增量改：
```bash
python <skill_root>/scripts/main.py --case <case.json> \
    --edit-svg <旧 figure.svg 绝对路径> --out /app/output \
    --work /app/work
```
支持的 edits 动作：`add_entity / remove_entity / rename / relabel /
flip_direction / change_kind / add_group / update_value / remove_relation /
note`。每个动作在 result.json 生成 `change_records`（before→after）。
未改动的元素保持原样——真正的"源文件可编辑"，而不是重画整张图。

### Step 6 — 写 result.json（诚实记录）
脚本已生成 result.json 初稿；Agent 复核并补充：
- `task_summary`：本案例做了什么；
- `uncertainty`：无法确证/材料缺失/渲染近似（镜像预览、字体覆盖）
  逐条列出；
- `change_records`：编辑动作（自动生成，无需手写）；
- 若 case.json 带 `output_contract`，脚本已把所有键回显到顶层；
  确认没有空值被当成真实值。

### Step 7 — 自查清单（提交前逐行确认）
- [ ] 实体名逐字出自材料，无材料外基因/浓度/时间点/单位；
- [ ] 每个关系方向与材料一致（激活/抑制/上下游/包含）；
- [ ] 图例项 == 图面实际箭头类型（无缺项无孤儿项）；
- [ ] 数值/坐标/单位与数据表逐项一致，改数据可重绘；
- [ ] figure.svg 文字可选中（`<text>`）、图层可拆（`layer-*` 分组）、
      带 id 与 data-* 溯源属性、内嵌 ER 清单；
- [ ] 导出件：PDF 可打开；PNG 有效 DPI 达标；色彩 RGB/sRGB；
- [ ] result.json 含全部契约字段 + case_id，status/sources/uncertainty/
      change_records 诚实；
- [ ] `python <skill_root>/scripts/validate_result.py --case /input/case.json --result /app/output/result.json` 输出 VALID；
- [ ] 任何失败分支都在 result.json 有记录，未编造缺失状态。

## 4. 异常处理

| 场景 | 处置 |
|-|-|
| 来源材料文件缺失 | 记录到 result.json `sources`/`uncertainty`；以已读到的材料继续，多处缺失则明确 partial |
| 材料描述矛盾（如方向冲突） | 以材料原文/任务书为准列出两种说法，选有证据的一种，另一写法写入 uncertainty |
| 关系 kind 无法映射 | 脚本标 fail；回到材料用词改写（激活/抑制/招募/转录/包含等），不猜箭头 |
| 数据与图例不符 | 图例由数据表生成故构造一致；若 checks 报 fail，改清单/数据表后重跑 |
| 中文字体缺失 | resolve_font_stack 自动探测（微软雅黑/SimHei/Noto CJK）；无 CJK 字体时 PNG 预览可能缺字，SVG 文字仍在，写入 uncertainty |
| 渲染/导出失败 | 捕获并写出 status=failed 的 result.json（含 pipeline fail 明细），产物不丢失 |
| 无 ER 清单且 case 不带数据 | 停止并明确说明——宁缺毋滥，不画无依据的图 |

## 5. 资源文件说明（全部相对技能根）

| 路径 | 用途 |
|-|-|
| `scripts/main.py` | 流水线入口（--case/--manifest/--out/--edit-svg/--exports/--dpi） |
| `scripts/manifest.py` | ER 清单加载/规范化/校验（中英关系词表） |
| `scripts/layout.py` | 布局引擎（layered/hierarchy/cycle/manual），SVG 与预览共用 |
| `scripts/svgbuilder.py` | 手写分层可编辑 SVG |
| `scripts/render.py` | matplotlib 镜像预览 + 图表渲染（svg.fonttype=none 保文字） |
| `scripts/checks.py` | 溯源/图例/数据映射/导出预检 |
| `scripts/edit.py` | 源文件级增量编辑（内嵌清单） |
| `scripts/validate_result.py` | result.json 契约独立校验 |
| `scripts/selftest.py` | 23 项逻辑自测 |
| `references/ER_MANIFEST.md` | 实体—关系清单规范 |
| `references/OUTPUT_CONTRACT.md` | result.json 契约 |
| `references/RUBRIC_MAP.md` | 五维评分 → 设计覆盖 |
| `examples/*` | 最小示例（case.json / case_chart.json / case_edit.json / sources / output），均为**示例，非正式案例** |

## 6. 依赖与限制

- Python 3.9+，依赖：matplotlib（渲染/预览）、Pillow（位图检查）、
  numpy（heatmap）；SVG 与清单逻辑仅标准库。
- **已知限制（如实标注）**：运行时无 cairosvg/svgwrite，PNG/PDF 预览是
  同一 layout+manifest 的 matplotlib 镜像（语义一致、非逐像素）；PDF 字体
  嵌入审计为尽力而为；CJK 渲染依系统字体。
- 运行时体积约束由包结构保证：≤50 个 UTF-8 文本文件、单文件 ≤500KB、
  总计 ≤2MB、无符号链接。

## 7. 禁止事项

- 不提交预制答案/正式案例输出；示例仅用于演示接口与流程；
- 不编造缺失的软件状态或科学数据（来源不存在的实体/数值一律不画）；
- 不宣称未经评分的成绩或基准。