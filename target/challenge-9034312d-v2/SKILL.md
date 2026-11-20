---
name: apparatus-and-route-diagrams
description: >-
  依据科研材料生成或编辑「实验装置与技术路线图」可编辑图稿（分层 SVG 源文件 +
  PNG/PDF 预览 + result.json），保证实体可追溯、连接与顺序成立、可被打开修改并复跑。
  覆盖装置结构（装置清单/装配说明）、步骤顺序（工艺描述→编号流程图）、材料流向
  （分流/合流/回流/废料出口）与技术路线（阶段与里程碑）四类绘图任务；每个图面实体
  带 source/locator/quote 溯源（证据先行），连接语义由 connection_rules 规则资产
  机器审计，交付含 output_contract 全字段、证据链与校验报告的 result.json，
  并诚实记录来源、不确定性与修改记录。
---

# 实验装置与技术路线图 Skill v2（challenge-9034312d · figures 组）

本 Skill 把「装置怎么搭、步骤怎么走、物料从哪来到哪去、技术路线分几个阶段」的文本
材料，变成一张可编辑的科研图稿。**核心不为「画得漂亮」，而是保证每个实体可追溯、
连接与顺序成立、交付物可被打开修改并复跑出同一张图**，且全部通过机器可执行的门。

v2 相对 v1 的加强（对齐高分意图 evidence→render→verify 三段式，见 COMPARE.md）：

- **证据先行**：新增 `scripts/gain_evidence.py`，从真实材料抽取实体/关系并带
  locator+quote，evidence.json 落盘（CP1 证据门）；
- **连接规则资产**：`assets/connection_rules.json` 把类别词表与连接语义做成可扩展
  规则字典，`svg_verify.py` 机器审计（CP2 连接门）；
- **校验闭环**：`svg_verify.py`（SVG 结构/图层/编号/图例/规则）+ `check.py`
  （G1–G10 契约门）（CP3/CP4）；
- **决策规则 D1–D12 与检查点 CP1–CP4**：失败分支与状态一致性显式化。

- Skill 版本：`2.0.0`（见 `scripts/main.py` execution.skill_version）
- Skill 根：本文件所在目录（下文中所有相对路径均相对 Skill 根）
- 执行顺序：**读 file(s) → gain_evidence（CP1）→ model(SIR) → layout →
  render_svg → svg_verify（CP2/CP3）→ export 预览 → result.json（CP4）→ check**
- 脚本自定位：全部脚本用 `os.path.dirname(__file__)` 定位技能根，**不依赖运行时 cwd**。

---

## 1. 用途

- 依据案例材料（装置清单/装配说明/方法段落/工艺描述）抽取**实体、关系、步骤、流向**，
  生成结构化中间表示（SIR）；
- 按图类（route / apparatus / flow / hybrid）确定性布图：阶段分列、步骤编号、
  正交连线、箭头方向、图例映射、数据映射；
- 交付四件套：**evidence.json**（证据链）、**可编辑分层 SVG 源文件**（`<text>` 真实
  文本，可被 Inkscape/文本编辑器直接改）、**PNG/PDF 预览**、**result.json**（含
  output_contract 全部字段 + case_id + verify 校验报告）；
- 对每个关键元素标注来源（source + locator + quote）、版本（源文件 sha256/材料 sha256）、
  导出检查结果（verify_report）。

不承担：数据分析与数值拟合、实验方案本身的科学合理性判断、论文排版与期刊投稿格式适配。

## 2. 适用条件

- 输入：`/input/case.json`（必读）+ `/input/task.md`（可选）+ 案例引用的材料文件
  （`--material` 或 case.json 的 `text/materials_text` 字段内联）；
- case.json 可为结构化（`entities`/`relations`/`figure_type`/`canvas`）或自由文本
  （`text`/`materials_text`）；两者均可处理，结构缺失时走文本解构并如实标注
  `extraction=text-heuristic`；
- 输出：写入 `--out`（官方运行时为 `/app/output`），实际以 `<case_id>` 为子目录；
- 编辑既有图稿：`--merge <override.json>`（同名 id 替换、新 id 追加，见 `SKILL.md §4`）。

## 3. 输入输出接口

```
python scripts/main.py --case /input/case.json [--task /input/task.md]
                       [--material <材料文件|目录>] [--merge /app/work/override.json]
                       --out /app/output [--dpi 200]
                       [--figure-type route|apparatus|flow|hybrid]
                       [--title "…"] [--width-mm N] [--height-mm N]
```

产出（相对输出根目录，实际以 `<case_id>` 为子目录）：

| 文件 | 说明 |
|-|-|
| `evidence.json` | **证据链**（实体/关系 locator+quote + 材料 sha256，v2 新增） |
| `layout.json` | 结构化布局模型（SIR → 几何的中间证据，可复核重绘） |
| `figure.svg` | **可编辑分层源文件**（5 层 layer:*；实体组带 data-entity/data-source/data-step-no；`<text>` 可编辑） |
| `figure.png` / `figure.pdf` | 渲染预览（PIL PNG + reportlab PDF，同一布局模型） |
| `verify_report.json` | **校验报告**（图层/文本/箭头/编号/图例/连接规则 + 确定性探针，v2 新增） |
| `result.json` | 结构化结果（contract 全字段 + case_id + evidence + verify，见 `references/OUTPUT_CONTRACT.md`） |

## 4. 执行步骤

按顺序执行，每步都在真实文件上操作，**不依据领域标签猜内容、不编造数据**。
下文的 **CP1–CP4 是检查点**（门），不过则按 D# 决策规则处理后再继续。

### 步骤 0 · 读实际文件（CP1 前置）
1. `read /input/case.json`（真实读取，禁止假设内容）；
2. 如有 `read /input/task.md`；按需 `read` case 引用的材料文件；记录全部为 `sources`；
3. 判断结构：有结构化列表 → 直接使用；只有文本 → 标记将走文本解构（D2）。

### 步骤 1 · 证据抽取（CP1 证据门，v2 核心）
1. 运行 `python scripts/main.py --case /input/case.json --task /input/task.md
   [--material …] --out /app/output`（默认参数先跑一遍），流水线内置
   `gain_evidence.py`：每条实体/关系带上 `locator`（材料定位）与 `quote`（原文引用），
   evidence.json 落盘；
2. **Agent 必须复核证据链**（CP1）：
   - 实体名称与材料是否一致、同类部件是否区分（D7）；
   - 每实体的 locator/quote 是否真实命中材料（拿不到就标 null 并计入 uncertainty，D4）；
   - 关系/箭头方向是否与正文一致（严禁反向或凭空补齐连接，D6）；
   - 步骤编号是否与正文顺序逐条对应；
3. 需要修正时，写 `/app/work/override.json`（`{"entities":[{id,...}],
   "relations":[{id,...}],"change_notes":[...]}`），再带 `--merge` 重跑：同名 id 替换、
   新 id 追加，修正动作自动写入 change_record（by="agent"）。

### 步骤 2 · 布图与校验（CP2 连接门 → CP3 校验门）
1. `layout.py` 确定性布图（路线分列/装置三桶/编号/正交连线）→ `layout.json`；
2. `render_svg.py` 写分层 SVG 源文件；随后 **cp3 内置 svg_verify.py**：
   - SVG 合法 XML、5 层 `layer:*` 齐全；
   - 可编辑 `<text>` ≥3、实体组带 data-entity/data-source（缺 source 记为 issue，D4）；
   - 箭头与关系一一对应、无断头箭头（D3）；
   - route/flow 步骤编号 1..N 连续（G8）；
   - 图例 kind 集合 == 图面 kind 集合（图例↔图元一致）；
   - **连接规则审计**（CP2）：类别/关系词表、sequence 只连步骤、connect 至少一端为
     结构件、装置图物料不作流向终点、回流需人工复核（D5/D6）——error 级违规 ⇒
     status=partial（D11），warn 仅提示复核；
3. 如画布溢出/文字折行异常，用 `--width-mm/--height-mm` 调整画布或精简标签重跑（D8）；
4. 复杂图（多阶段回流、跨列长箭头）可在 Inkscape 微调后在 change_record 增补
   `action: manual-edit` 记录修改内容（保持诚实）。

### 步骤 3 · 导出渲染（CP3 续）
1. 确认 `figure.png` 与 `figure.pdf` 生成（单个渲染失败会如实写入 uncertainty 与
   status=partial，D10）；
2. 检查字体：PNG 依赖本机 TTF（fonts.py 候选表），缺失时 result.json.fonts 记录
   found=false（D9）；
3. 预览打开目测：箭头方向、编号、图例、无断头箭头、无重叠盒子。

### 步骤 4 · 写 result.json + 交付自查（CP4 契约门）
1. 确认输出目录含 `result.json`（`output_contract.editable_sources/exports/data_mapping/
   element_traceability` + `evidence` + `verify` + `case_id/status/sources/uncertainty/
   change_record/checksum`）；
2. 运行自查：`python scripts/check.py <result.json>`，G1–G10 全过（`ok: true`）才算完成；
3. 自查发现的问题（缺文件、SVG 不可解析、编号断号、断头箭头、verify 违规）必须修复
   后重跑，不得隐瞒（D11）。

## 5. 决策规则 D1–D12 与检查点 CP1–CP4

**检查点**（门，必须先过后再进入下一步）：

| 门 | 时点 | 判定 |
|-|-|-|
| CP1 证据门 | 步骤 1 后 | evidence.json 已生成；实体/关系 locator 真实命中材料；无 source 的条目已计入 uncertainty |
| CP2 连接门 | 步骤 2 绘制前/中 | 类别词表合法；sequence/connect/流向语义符合 connection_rules（无 error 违规） |
| CP3 校验门 | 步骤 2–3 | svg_verify 全绿：图层/文本/箭头/编号/图例一致；PNG/PDF 存在或已诚实降级 |
| CP4 契约门 | 步骤 4 | check.py G1–G10 全过；status 诚实（error 违规未解决 ⇒ 不得 success） |

**决策规则**（异常时按 D# 处置，完整表见 `references/failure-modes.md`）：

| D# | 触发 | 处置 |
|-|-|-|
| D1 | case.json 不存在/不可解析 | 立即终止，写 status=failed 的 result.json，说明原因；不猜内容 |
| D2 | 无结构化实体，仅文本 | 文本解构；extraction=text-heuristic；uncertainty 说明；status 按孤儿实体降级 |
| D3 | 关系指向不存在实体 | 丢弃该关系并在 uncertainty 记录「断头箭头已过滤」，Agent 复核 |
| D4 | 实体无 source | source=null + 列入 uncertainty.sources；不编造出处 |
| D5 | 类别/关系不在词表 | 容错归一化；svg_verify 报 error → 对照材料修正 |
| D6 | 方向/连接与材料冲突 | 连接规则审计报 error；--merge 修正方向/类别 |
| D7 | 同名/近似实体歧义 | 保留并列入 uncertainty.scope=ambiguity，Agent 决定 |
| D8 | 画布溢出 | 自动等比缩放居中；或 --width-mm/--height-mm 重跑 |
| D9 | 本机无中文字体 | fonts.found=false 记入 result.json；SVG/PDF 仍可用，如实说明 |
| D10 | PNG/PDF 渲染失败 | 保留已有产物，status=partial，uncertainty 记录；SVG 源文件仍在 |
| D11 | svg_verify error 违规/check 门不过 | 不得 status=success；列明违规，修正后重跑 |
| D12 | 材料歧义/信息冲突 | 记入 uncertainty（scope+issue+action），不擅自补造数据 |

## 6. 自查清单（完成判定）

- [ ] CP1：evidence.json 存在；实体≥1 且与材料一致，source/locator 可追溯（缺失已列 uncertainty）
- [ ] CP2：无 error 级连接规则违规（sequence/connect/流向语义、类别词表）
- [ ] CP3：SVG 合法 XML、5 层齐全、`<text>` 可编辑 ≥3；编号连续（route/flow）；图例↔图元一致；无断头箭头
- [ ] CP3：figure.png / figure.pdf 存在且非空（失败已如实降级）
- [ ] CP4：result.json 字段齐全（OUTPUT_CONTRACT.md），status 诚实（error 违规 ⇒ partial）
- [ ] CP4：`python scripts/check.py <result.json>` 输出 ok:true（或列出的 issues 已全部修复）
- [ ] 修改历史（change_record）、不确定性（uncertainty）、来源（sources + evidence）均已如实记录

## 7. 边界与诚实原则

- 本 Skill 只负责**绘图表达**与**可编辑交付**；不判断实验方案科学性，不做数值拟合；
- 每个实体/关系尽量携带 source + locator + quote；拿不到就标 null 并计入 uncertainty（D4）；
- 不伪造软件状态（如中文字体缺失）、不编造科研数据/数值（D12）；
- 正式案例的评分由平台执行；`examples/` 仅为接口演示（其中产物标注「示例，非正式案例」）。

## 8. 资源清单（相对技能根）

- `scripts/main.py` — 一键流水线（证据→模型→布图→渲染→校验→契约）
- `scripts/gain_evidence.py` — 证据抽取（CP1；实体/关系 locator+quote + 材料 sha256）
- `scripts/model.py` — SIR：实体/关系/步骤/流向解析与文本解构兜底
- `scripts/layout.py` — 确定性布图引擎（图元库+布局模板落点）
- `scripts/render_svg.py` — 手写分层 SVG（可编辑源文件；5 层 layer:*）
- `scripts/export_preview.py` — PIL PNG + reportlab PDF 预览（同一布局模型）
- `scripts/svg_verify.py` — SVG 校验 + 连接规则审计（CP2/CP3；verify_report.json）
- `scripts/check.py` — 交付自查（CP4；G1–G10 硬性门）
- `scripts/fonts.py` — 中文字体探测与降级
- `assets/connection_rules.json` — 连接规则字典（词表+语义规则，可扩展）
- `assets/result_example.json` — result.json 最小形态示例
- `templates/palette.json` — 图元配色模板
- `templates/component-connection-checklist.md` / `entity-relation-checklist.csv` — 核对清单/表
- `references/OUTPUT_CONTRACT.md` — result.json 契约 + G1–G10
- `references/RUBRIC_MAP.md` — 评分维度→设计覆盖映射
- `references/vocabulary.md` — 术语表/词表（kind/关系/图类/命名/状态）
- `references/figure-blueprint.md` — 布局蓝图（图元/模板/命名/导出/扩展）
- `references/failure-modes.md` — 失败模式与决策规则 D1–D12
- `examples/` — 最小调用示例（含生成+编辑双用例；非正式案例）

依赖（运行环境已具备，全部可降级）：Python 3.10+ 标准库；Pillow（PNG 预览）；
reportlab（PDF 预览）。`cairosvg/svgwrite/python-pptx` 不需要：SVG 为手写 XML，
预览直接从同一布局模型渲染。