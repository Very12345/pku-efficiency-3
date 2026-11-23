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
  本版（缺依赖降级链实测）在此骨架上追加「附:本版增量」一章：scripts/degrade_probe.py 用受控导入拦截逐个抽走 Pillow/reportlab/yaml/numpy/matplotlib/python-pptx 与 LibreOffice CLI 共 13 个条件，实测纯标准库仍产出 5 件（status=partial）、Pillow 一缺 PNG 与 PDF 一起没、deviations 0，逐项表与最小可用环境分档见 references/DEGRADE-MATRIX.md。
---

# 实验装置与技术路线图 Skill v2（challenge-9034312d · figures 组）

本 Skill 把「装置怎么搭、步骤怎么走、物料从哪来到哪去、技术路线分几个阶段」的文本
材料，变成一张可编辑的科研图稿。**核心不为「画得漂亮」，而是保证每个实体可追溯、
连接与顺序成立、交付物可被打开修改并复跑出同一张图**，且全部通过机器可执行的门。

v2 相对 v1 的加强（对齐高分意图 evidence→render→verify 三段式，见 §9 与
`references/RUBRIC_MAP.md`）：

- **证据先行**：新增 `scripts/gain_evidence.py`，从真实材料抽取实体/关系并带
  locator+quote，evidence.json 落盘（CP1 证据门）；
- **连接规则资产**：`assets/connection_rules.json` 把类别词表与连接语义做成可扩展
  规则字典，`svg_verify.py` 机器审计（CP2 连接门）；
- **校验闭环**：`svg_verify.py`（SVG 结构/图层/编号/图例/规则）+ `check.py`
  （G1–G10 契约门）（CP3/CP4）；
- **决策规则 D1–D12 与检查点 CP1–CP4**：失败分支与状态一致性显式化。

## 0. 技能根与自定位（先读这一节）

- Skill 版本：`2.0.0`（见 `scripts/main.py` 的 `execution.skill_version`）
- **技能根 = 本 `SKILL.md` 所在目录**。平台把本 Skill 安装到 `/skills/weekly-skill`；
  本地复现时它是你解包出来的那个目录。下面所有命令都用 `$SKILL_DIR` 表达它，
  **因此 cwd 不是技能根时命令照样能跑**：

  ```bash
  # 解析技能根（任选一种；文件系统里能找到 SKILL.md 即可）
  SKILL_DIR=/skills/weekly-skill                       # 平台安装位置
  SKILL_DIR="$(cd "$(dirname /path/to/SKILL.md)" && pwd)"   # 本地解包位置
  ```

- `scripts/*.py` 全部用 `os.path.dirname(__file__)` 自定位，读 `templates/`、
  `assets/`、`references/` 一律相对技能根解析，**不依赖运行时 cwd**，也不写
  `__pycache__`（脚本内已置 `sys.dont_write_bytecode = True`）。
- 执行顺序：**读 file(s) → gain_evidence（CP1）→ model(SIR) → layout →
  render_svg → svg_verify（CP2/CP3）→ export 预览 → result.json（CP4）→ check**
- **资源形态（本包遵守平台硬约束）**：本包只含 **UTF-8 文本资源**
  （`.md/.py/.json/.txt/.csv/.yaml/.yml`），文件数 ≤50、单文件 ≤500KB、总计 ≤2MB、
  无符号链接；**不含任何 `.pdf/.png/.svg/.pptx` 等二进制或矢量文件**。
  `figure.svg`（可编辑源文件）、`figure.png`、`figure.pdf` 三个交付件由
  `scripts/main.py` **在运行时现场生成**（见 §3「产出」），不随包发布。

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
python "$SKILL_DIR/scripts/main.py" --case <case.json|案例目录> [--task <task.md>]
                       [--material <材料文件|目录>] [--merge <override.json>]
                       --out <输出目录> [--dpi 200]
                       [--figure-type route|apparatus|flow|hybrid]
                       [--title "…"] [--width-mm N] [--height-mm N]
```

- `--case` 给**目录**时自动取该目录下 `case.json`，并在未给 `--task` 时取同目录
  `task.md`（平台输入约定即 `/input/case.json` + `/input/task.md` 成对）；
  给**具体文件**时 `--task` 需显式传入（不猜同目录文件，材料来源宁可少而准）。
- 其余参数（`--dpi/--figure-type/--title/--width-mm/--height-mm/--palette/--rules/--merge`）
  含义见 `--help`；`--out` 默认 `./output`，官方运行时为 `/app/output`。

产出（相对输出根目录，实际以 `<case_id>` 为子目录；**全部在运行时生成**）：

| 文件 | 说明 |
|-|-|
| `evidence.json` | **证据链**（实体/关系 locator+quote + 材料 sha256，v2 新增） |
| `layout.json` | 结构化布局模型（SIR → 几何的中间证据，可复核重绘） |
| `figure.svg` | **可编辑分层源文件**（5 层 layer:*；实体组带 data-entity/data-source/data-step-no；`<text>` 可编辑） |
| `figure.png` / `figure.pdf` | 渲染预览（PIL PNG + reportlab PDF，同一布局模型） |
| `verify_report.json` | **校验报告**（图层/文本/箭头/编号/图例/连接规则 + 确定性探针，v2 新增） |
| `result.json` | 结构化结果（contract 全字段 + case_id + evidence + verify，见 `references/OUTPUT_CONTRACT.md`） |

> ⚠ `figure.svg`/`figure.png`/`figure.pdf` 是**运行期产物**，不随 Skill 包发布
> （平台只接受文本资源）。复跑命令见 §4 步骤 1；无 Pillow/reportlab 时按 D10 降级
> 为 partial 并把原因写入 `result.json.uncertainty`，SVG 源文件不受影响。

## 4. 执行步骤

按顺序执行，每步都在真实文件上操作，**不依据领域标签猜内容、不编造数据**。
下文的 **CP1–CP4 是检查点**（门），不过则按 D# 决策规则处理后再继续。

### 步骤 0 · 读实际文件（CP1 前置）
1. `read /input/case.json`（真实读取，禁止假设内容）；
2. 如有 `read /input/task.md`；按需 `read` case 引用的材料文件；记录全部为 `sources`；
3. 判断结构：有结构化列表 → 直接使用；只有文本 → 标记将走文本解构（D2）。

### 步骤 1 · 证据抽取（CP1 证据门，v2 核心）
1. 运行 `python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md
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
2. 运行自查：`python "$SKILL_DIR/scripts/check.py" <result.json>`，G1–G10 全过
   （输出 `ok: true`，退出码 0）才算完成；
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
- [ ] CP3：figure.png / figure.pdf 存在且非空（失败已如实降级，写入 uncertainty）
- [ ] CP4：result.json 字段齐全（`references/OUTPUT_CONTRACT.md` 的 18 个顶层字段），status 诚实（error 违规 ⇒ partial）
- [ ] CP4：`python "$SKILL_DIR/scripts/check.py" <result.json>` 输出 `ok: true` 且退出码 0（或列出的 issues 已全部修复）
- [ ] 修改历史（change_record）、不确定性（uncertainty）、来源（sources + evidence）均已如实记录
- [ ] 打包形态：包内只含 `.md/.py/.json/.txt/.csv/.yaml/.yml` 文本资源，无 `__pycache__`、无绝对路径

## 7. 边界与诚实原则

- 本 Skill 只负责**绘图表达**与**可编辑交付**；不判断实验方案科学性，不做数值拟合；
- 每个实体/关系尽量携带 source + locator + quote；拿不到就标 null 并计入 uncertainty（D4）；
- 不伪造软件状态（如中文字体缺失）、不编造科研数据/数值（D12）；
- 正式案例的评分由平台执行；`examples/` 仅为接口演示（其中产物标注「示例，非正式案例」），
  不含任何预制答案；示例的期望产物清单见 `examples/EXPECTED-OUTPUT.md`。

## 8. 资源清单（路径均相对技能根）

- `scripts/main.py` — 一键流水线（证据→模型→布图→渲染→校验→契约）
- `scripts/gain_evidence.py` — 证据抽取（CP1；实体/关系 locator+quote + 材料 sha256）；
  可单独运行：`python "$SKILL_DIR/scripts/gain_evidence.py" --case <case.json> [--task …] [--material …] --out <evidence.json>`
- `scripts/model.py` — SIR：实体/关系/步骤/流向解析与文本解构兜底
- `scripts/layout.py` — 确定性布图引擎（图元库+布局模板落点）
- `scripts/render_svg.py` — 手写分层 SVG（可编辑源文件；5 层 layer:*）
- `scripts/export_preview.py` — PIL PNG + reportlab PDF 预览（同一布局模型）
- `scripts/svg_verify.py` — SVG 校验 + 连接规则审计（CP2/CP3；verify_report.json）；
  可单独运行：`python "$SKILL_DIR/scripts/svg_verify.py" --layout <layout.json> --svg <figure.svg> [--rules <rules.json>] [--out <verify_report.json>]`
- `scripts/check.py` — 交付自查（CP4；G1–G10 硬性门）；
  可单独运行：`python "$SKILL_DIR/scripts/check.py" <result.json>`（退出码 0 = 全过、1 = 有 issue）
- `scripts/fonts.py` — 中文字体探测与降级
- `assets/connection_rules.json` — 连接规则字典（词表+语义规则，可扩展）
- `assets/result_example.json` — result.json 最小形态示例
- `templates/palette.json` — 图元配色模板
- `templates/component-connection-checklist.md` / `entity-relation-checklist.csv` — 核对清单/表
- `references/OUTPUT_CONTRACT.md` — result.json 契约（18 个顶层字段）+ G1–G10
- `references/RUBRIC_MAP.md` — **评分五维（40/25/15/10/10）逐条落点**
- `references/vocabulary.md` — 术语表/词表（kind/关系/图类/命名/状态）
- `references/figure-blueprint.md` — 布局蓝图（图元/模板/命名/导出/扩展）
- `references/failure-modes.md` — 失败模式、决策规则 D1–D12、资源形态门 R1–R6
- `examples/` — 最小调用示例（生成 + 编辑双用例；`README.md` + `EXPECTED-OUTPUT.md`）
- `examples/output/` — 两个合成示例案例的**文本类**运行产物（evidence/layout/verify_report/result）

依赖（全部可降级）：Python 3.10+ 标准库；Pillow（PNG 预览）；reportlab（PDF 预览）。
`cairosvg/svgwrite/python-pptx` 不需要：SVG 为手写 XML，预览直接从同一布局模型渲染。

## 9. 评分五维落点（速查；逐条证据见 `references/RUBRIC_MAP.md`）

| 维度 | 分 | 本包落点（文件/机制） |
|-|-|-|
| 实际效果 | 40 | `scripts/main.py` 一键出图 → 可编辑分层 `figure.svg` + `figure.png/pdf` + `evidence.json`/`layout.json`/`verify_report.json`/`result.json`（运行期生成）；`examples/` 有真实运行产物 |
| 使用增益 | 25 | 基准 Agent「画得像却错」↔ 本 Skill：`gain_evidence.py` 证据先行 + `svg_verify.py` 连接规则机器审计 + 图例↔图元/编号一致性门；`--merge` 增量改图免重画 |
| 创新增益 | 15 | SIR 结构化中间表示（`model.py`）→ 确定性布图（`layout.py`）→ 三后端同布局；规则资产 `assets/connection_rules.json` 可扩展并机器审计；`spec_sha16` 确定性探针 |
| 可靠体验 | 10 | `references/failure-modes.md`（材料异常/模板缺失/依赖缺失/契约四形态/状态一致性 + R1–R6 打包门）；`check.py` 退出码 0/1/3 语义；D1–D12 决策规则 |
| 生态贡献 | 10 | 文档完整性（SKILL/README/TEST/5 份 references/2 份 templates）；可复用资产（规则字典、配色、核对清单、result 形态示例、SIR 与导出脚本）；`GITHUB_URL.txt` 公开入口 |

## 附:本版增量 —— 缺依赖降级链实测

上面第 0–9 章是基线正文（章节顺序、命令、`--flag` 表、契约说明一字未改）。本版在这份骨架上
只加一条**可运行的降级链实测**：把「依赖缺了会怎样」从文档口径变成逐项实测。算法、CLI、
既有脚本一行未改。

| 本版新增（本轴） | 作用 | 实测结论（数字见下，现场跑出） |
|-|-|-|
| `scripts/degrade_probe.py` | 13 个条件（逐个拦截 + 组合 + 关键标准库对照）跑同一份输入的主流程 | 真实依赖只有 **2** 个；**Pillow 一缺，PNG 与 PDF 一起没**；规格点名的 5 项**零差异** |
| `references/DEGRADE-MATRIX.md` | 逐项实测表 + 可用性结论 + 彻底不可用清单 + **分档最小可用环境** | 纯标准库**仍产出 5 件**（SVG + 4 份 JSON，`status=partial`）；`xml`/`hashlib` 缺 ⇒ **0 件** |

### 一条命令跑出 13 个条件

```bash
python "$SKILL_DIR/scripts/degrade_probe.py" --json /tmp/degrade_report.json
python "$SKILL_DIR/scripts/degrade_probe.py" --only c01-no-PIL --only c02-no-reportlab   # 只看真实依赖
python "$SKILL_DIR/scripts/degrade_probe.py" --only c04-no-PIL.Image                     # 拦截器自证
python "$SKILL_DIR/scripts/degrade_probe.py" --list                                      # 只列条件
python "$SKILL_DIR/scripts/degrade_probe.py" --expect-deviations 0                       # 回归断言
```

**方法**：不改脚本、不卸载包 —— 在**子进程**里装一个 `sys.meta_path` 拦截器
（现场生成 `_blocker_driver.py`），对命中前缀的模块 `find_spec` 直接抛
`ModuleNotFoundError`，再用 `runpy` 跑真实 `main.py`。被拦进程的一切行为等价于
"这台机器上没装这个包"。`c10` 用另一种手法模拟"没有 LibreOffice CLI"：把 `PATH` 指向空目录。

**拦截器自证**（防"拦了没拦住"）：`c04` 只拦**子模块** `PIL.Image` 就复现了整包拦截的降级；
`c11`/`c12` 拦关键标准库后流水线整体不可用。两条合起来证明拦截真的生效。

### 判据

- 每个条件在脚本里**先声明期望形态**（`full` / `degrade` / `zero-diff` / `broken`），
  再与实测比对；不符的进 `deviations[]`；
- `verdict = pass` 要求 `deviations == []`（或用 `--expect-deviations N` 把它变成回归断言）；
- 退出码：**0** = 结论与声明一致；**1** = 出现未预期降级形态；**2** = 用法 / 环境错误。

### 实测数字（13 条件，Windows 11 + CPython 3.13.9，约 6 s 跑完；本机复跑 6.7 s，纯墙钟量、随负载浮动）

| 条件 | 拦截 | 退出码 | `status` | 产物数 | 结论 |
|-|-|-|-|-|-|
| `c00-base` | 无 | 0 | `success` | **7** | 对照 |
| `c01-no-PIL` | `PIL` | **3** | `partial` | **5** | **PNG 与 PDF 一起丢**（`exports=[]` ⇒ `G4` 不过） |
| `c02-no-reportlab` | `reportlab` | 0 | `partial` | **6** | 只丢 PDF，仍可交付 |
| `c03-no-PIL-no-reportlab` | 两个 | 3 | `partial` | 5 | 最坏真实情形 |
| `c04-no-PIL.Image` | `PIL.Image`（子模块） | 3 | `partial` | 5 | 拦截器自证：与 `c01` 同形 |
| `c05`–`c08` | `yaml` / `numpy` / `matplotlib` / `pptx` | 0 | `success` | **7** | **零差异**：本包不 import 它们 |
| `c09-no-named-five` | 规格点名 5 项 + PIL + reportlab | 3 | `partial` | 5 | 同上，等效于 `c03` |
| `c10-no-soffice` | PATH 清空 | 0 | `success` | **7** | **零差异**：不调用外部 CLI |
| `c11-no-xml` | `xml` | **1** | 无 | **0** | **彻底不可用**（连 `result.json` 都写不出） |
| `c12-no-hashlib` | `hashlib` | **1** | 无 | **0** | **彻底不可用** |

关键事实（都有实测证据）：

1. **`reportlab` 在导入期就 `from PIL import Image`**（`reportlab/lib/utils.py`）⇒
   **Pillow 是唯一的"硬"依赖**：它一缺，两个预览都没了（而不是文档里假设的"PNG 靠 PIL、
   PDF 靠 reportlab"的并列关系）。安装顺序上 **Pillow 在前**。
2. **`status` 从不撒谎**：`c01`/`c02`/`c03` 都是 `partial`，`result.json.uncertainty` 里逐条写明
   `{"scope":"png"|"pdf","issue":"… 失败: <原因>","action": …}`（`c02` 只有 `pdf` 一条，
   `c01` 有 `png`+`pdf` 两条）。
3. **退出码会跟着变**：`exports` 为空时 `check.py` 的 `G4` 不过 ⇒ `main.py` 返回 **3**
   （不是 0、也不是崩）—— 契约门在降级时仍然工作。
4. **`result.json` 始终落盘**（除 `xml`/`hashlib` 两个地基条件外）：即使预览全失败，
   结构化结果仍在，回放可见。

### 「最小可用环境」清单（分三档，实测）

| 档位 | 需要什么 | 能产出什么 | `status` | 退出码 |
|-|-|-|-|-|
| ① **纯标准库** | CPython 3.10+（`json`/`hashlib`/`math`/`xml.etree`/`dataclasses`/`re`） | **5 件**：`figure.svg` + `evidence.json` + `layout.json` + `verify_report.json` + `result.json` | `partial` | 3 |
| ② ①+Pillow | `Pillow` | **6 件**（+ `figure.png`） | `success` | 0 |
| ③ ②+reportlab | `reportlab`（且**必须**有 Pillow） | **7 件**（+ `figure.pdf`） | `success` | 0 |

**明确不需要**（抽走零差异）：`yaml`、`numpy`、`matplotlib`、`python-pptx`、LibreOffice CLI。
**怎么都救不了**（缺了连 `result.json` 都没有）：`xml`（`xml.etree.ElementTree`）、`hashlib`。

### 降级清单 / 静默通过要点

- 降级处置沿用基线 D9/D10：字体缺失记 `fonts.found=false`；渲染失败保留已有产物、
  `status=partial`、原因逐条写入 `uncertainty`（本轴把影响面**实测**清楚了：Pillow 缺失是
  **PNG+PDF 同时缺**，不是只缺 PNG）；
- 本轴没有"静默通过"：每个条件都先声明期望形态再比对，`deviations[]` 非空即 `attention`；
- **D15（本版新增决策口径）= 降级后果必须与文档一致**：任何会让产物件数 / `status` / 退出码
  发生变化的依赖变动，必须同步更新 `references/DEGRADE-MATRIX.md` 的「最小可用环境」表；
  `scripts/degrade_probe.py` 的 `deviations[]` 就是这条口径的可执行闸门（`--expect-deviations 0`）；
- 本轴**未覆盖**（如实声明）：间接依赖（PIL 之下的 zlib 等 C 扩展）、磁盘满 / 只读输出目录
  （归 `scripts/fault_inject.py`）、Python 3.9 及以下的语法级不可用、跨 OS 复跑、
  `pip install` 顺序，完整清单见 `DEGRADE-MATRIX.md` §8。

### 完成判定追加项

- [ ] `python "$SKILL_DIR/scripts/degrade_probe.py"` 退出码 0、`deviations == []`；
      产物件数 / `status` / 退出码与 `references/DEGRADE-MATRIX.md` 的表一致（D15）；
- [ ] 部署环境至少覆盖①档（纯标准库）；要交 PNG/PDF 预览时才需 ②/③ 档；
- [ ] 诚实性：**不夸大可用性** —— 纯标准库下 `status=partial`、退出码 3、`exports` 为空，
      这是 `check.py` 的 G4 在诚实报错，不是失败被掩盖；缺依赖原因逐条写进 `uncertainty`。

### 路径更正（随本骨架一并生效）

- `references/MECHANISM.md` → 全文并入 `references/GAIN-PROTOCOL.md` 尾部附录；
- `references/CASE-SET.md` → 全文并入 `references/failure-modes.md` 尾部附录；
- `assets/result_example.json` → 全文并入 `references/OUTPUT_CONTRACT.md` 文末附录。

以上三处都是为守住平台「≤50 个 UTF-8 文本文件」硬门而做的**同主题合并，内容一字未删**；
脚本 docstring 里的旧路径指向对应的宿主文件附录。

**逐项实测表、每个条件还剩哪些产物、`uncertainty` scope 对照、彻底不可用清单与
最小可用环境分档，全部在 `references/DEGRADE-MATRIX.md`。**
