---
name: graphical-abstract
description: >-
  Generate or edit a single-page Graphical Abstract (图形摘要) from research
  material: 方案先行（scaffold 出设计方案 → plan lint）→ extract scientific
  entities, relations and data with source provenance → lay out the question →
  method → results → conclusion story (四要素) → encode data into
  bars/colors/lengths with consistent legends → delivery: editable layered SVG
  (layer-naming 契约) plus rendered PNG/PDF previews and a verifiable
  result.json（四形态契约回显 + G1–G8 硬性门）。每个元素 data-src 可溯源、同输入
  同布局、失败分支 D1–D10 显式决策。Use when the task says "graphical abstract",
  "graphic abstract", "示意图 / 机制图 / 流程图 / 图稿", "make a figure for the
  paper / grant / report", "edit an existing figure", or asks to draw a
  mechanism, scheme or flow figure from experiment records.
---

# Graphical Abstract（图形摘要）Skill v2 — figures group

把「研究问题—方法—核心结果—结论」压缩到单页视觉摘要，并交付**可继续编辑的分层源文件**。
本 Skill 对图的科学内容负责：实体不张冠李戴、箭头方向与因果一致、图例/单位/比例尺与
数据一一对应、每个元素可溯源（`data-src`）、同输入可复现。**绝不编造数据**。
v2 在 v1 基础上按高分意图加强：**方案先行（plan-schema）**、**四要素知识文档**、
**SVG 分层命名规范（可机器校验）**、**双 lint 门**（绘制前方案 lint + 绘制后规格 lint）。

- Skill 版本：`2.0.0`（脚本版本见 `scripts/common.py` 的 `SKILL_VERSION`）
- Skill 根：本文件所在目录；下文用 `$SKILL_DIR` 指代（见 §0）
- 执行顺序：**读 OUTPUT_CONTRACT（交付什么）→ 按 plan-schema 出设计方案 →
  lint_plan（CP1）→ 绘制（extract→figurespec→spec_lint→svg→preview）→
  audit（含四要素/图层检查）→ check_contract → 按 RUBRIC_MAP 自评**
- 资源形态：**纯文本**（`.md/.py/.json/.txt/.csv/.yaml/.yml`），无二进制、无 `.svg` 预置件、
  无 `__pycache__`、无绝对路径；渲染件一律**运行时生成**

---

## 0. 自定位调用（cwd 任意，命令必须逐字可用）

本 Skill 的脚本用 `scripts/common.py` 的 `SCRIPT_DIR = dirname(abspath(__file__))`
**自定位技能根**，所以调用时只需给出 `$SKILL_DIR`，**不要求 cwd = 技能根**：

```bash
# 1) 设定技能根目录（任选其一）
SKILL_DIR=/skills/weekly-skill          # 官方评测容器（Skill 安装位置）
SKILL_DIR=/abs/path/to/graphical-abstract-7030fff2   # 本机/自建环境：本文件所在目录

# 若不确定根目录在哪，可用下面一行向上探测（从当前目录向上找 SKILL.md）：
SKILL_DIR="$(pwd)"; while [ ! -f "$SKILL_DIR/SKILL.md" ] && [ "$SKILL_DIR" != "/" ]; do SKILL_DIR="$(dirname "$SKILL_DIR")"; done

# 2) 冒烟（示例案例，合成数据；cwd 任意）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/ga-out

# 3) 官方案例形态（平台挂载输入、产物写 /app/output）
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md --out /app/output
```

> 若你只能写相对路径，请先 `cd "$SKILL_DIR"` 再执行 §3 中的命令——两种写法等价，
> 但**本文件所有示例均以 `$SKILL_DIR` 绝对化为准**，以免 cwd 不同导致找不到脚本。

## 1. 用途与适用条件

**适用**：给定研究描述、实验记录、论文草稿/图表数据，要求产出单页图形摘要
（问题/方法/结果/结论四要素）、机制图、流程图或科研图表，且要求可编辑源文件 +
渲染件 + 可复核来源。

**适用输入形态**（至少其一，全部读取真实文件，绝不凭文件名/标签猜内容）：

| 输入 | 说明 |
|-|-|
| `case.json` | 必读。可含 `case_id / title / task / source_material / entities / relations / data / figure_constraints / output_contract` |
| `task.md` | 任务说明；含 `# 问题/方法/结果/结论` 小节的直接映射为面板要点 |
| 材料文件 | `source_material` 指明的 md/txt/tex/csv 等；提供数值与机制的真正来源 |
| `figure_constraints` | 画布宽高、colorblind、flow_arrows、raster_scale、pdf 等（有默认值） |
| `output_contract` | 案例自带的交付契约；四形态回显进 `result.json` 顶层（见 `references/OUTPUT_CONTRACT.md`） |
| `--plan plan.json` | （可选）设计方案：`scripts/scaffold.py` 生成骨架，Agent 定稿（见 `references/plan-schema.md`） |

**不适用/明确边界**：正文写作、统计分析、实验设计不在本 Skill 范围；本 Skill 只对
图形的科学内容表达、版式、可编辑性与导出质量负责。

## 2. 输入与输出

**输入路径约定（Runtime contract）**：官方案例运行时，`/input/case.json` 与
`task.md` 由平台挂载，材料按案例提供；本机用 `--case <case.json>` 显式指定。

**输出**：全部写到 `--out`（官方 `/app/output`；本机默认 `<skill>/out`）：

| 文件 | 内容 |
|-|-|
| `<case_id>_graphical_abstract.svg` | **可编辑分层 SVG 源**（7 层 `layer:*`，文字真 `<text>`，元素带 `data-src`/`data-entity-id`/`data-role`；契约见 `references/layer-naming.md`）；**运行时生成** |
| `<case_id>_graphical_abstract.png` / `.pdf` | 渲染预览（matplotlib → Pillow → 纯 Python PNG 回退链，后端如实记录）；**运行时生成** |
| `result.json` | 结构化结果（契约见 `references/OUTPUT_CONTRACT.md`；含 plan/spec_lint/audit） |
| `spec.json` / `content.json` | 图面规格与规范化抽取结果（同一几何，再编辑/评审用） |
| `audit.json` / `render_log.json` | 自查报告（含四要素覆盖、图层命名、确定性探针）与渲染日志 |

## 3. 执行步骤（方案先行 + 绘制 + 双 lint 门）

第 0–9 步由脚本流水线执行（`python "$SKILL_DIR/scripts/main.py" --case <case.json>
[--task <task.md>] [--material <file|dir>] [--plan <plan.json>] --out <dir>`）；
作为 Agent，你**必须**在调用脚本之外阅读真实文件内容并复核抽取结果，偏差在
`change_records` / `uncertainty` 中如实记录。**不得用预制答案替代实际运行。**

### 步骤 0 —— 方案先行（design-first，CP1 门）
1. （推荐）先按 `references/plan-schema.md` 出设计方案：`python "$SKILL_DIR/scripts/scaffold.py"
   --case <case.json> --out plan.json` —— 骨架带真实抽取的实体/关系/数据与来源定位；
2. Agent 阅读材料后填充 `four_elements`（四句"一句话说明"，见
   `references/ga-four-elements.md`）+ 修剪上画布的元素 + 定稿 `figure_constraints`；
3. **CP1 方案 lint**：`python "$SKILL_DIR/scripts/spec_lint.py" --lint-plan --plan plan.json`
   （`main.py --plan` 内嵌执行同一函数）—— 四要素非空、实体/关系/数据带 src、画布尺寸合规；
   不过则按 D4 记录后修正，不得跳过。

### 步骤 1 —— 读实际文件（不要凭标签猜内容）
4. 读取 `case.json`（UTF-8）；失败即报错退出并说明，不留虚假产物。
5. 解析 `source_material` 相对路径（对 case 目录/`/app/work` 解析），逐个读取材料原文。
6. 读取 `task.md`（若存在），提取 `# 问题/方法/结果/结论` 小节要点与交付要求。

### 步骤 2 —— 抽取实体/关系/数据（source-bound）
7. 运行 `scripts/extract.py`（由 `main.py` 调用）：规范化 entities/relations/data，
   扫描材料中的 `A -> B (label)`、`键: 值 单位` 行作为补充事实。
   **规则：** 每个元素带 `src`（`文件:行` 或 `case.json[字段]`）；同 id 首见优先；
   材料中找不到源头的数值**不得上画布**，只进 `uncertainty` 并以「数值缺失」占位。
8. 复核面板要点进入正确面板（问题/方法/结果/结论）——四要素不变式见
   `references/ga-four-elements.md`。

### 步骤 3 —— 版面与数据编码（确定性布局）
9. `scripts/figurespec.py` 生成图面规格：四列面板按「问题→方法→结果→结论」阅读顺序、
   结果面板内条形/色块子图、跨面板流程箭头、页脚图例 + 比例尺 + 来源说明。
10. 数据编码：`bar_length`（长度∝数值）、`color_scale`（色阶，Okabe-Ito 色盲安全）、
    `area`/`value_label`。所有编码项进入 `data_encoding` + `legend`，
    **图例值与画面数值一一对应**（spec_lint 检查）。

### 步骤 4 —— 规格 lint（CP1b，绘制前）
11. `spec_lint.lint(spec, content)`（`main.py` 内嵌执行；也可独立跑
    `python "$SKILL_DIR/scripts/spec_lint.py" --spec <out>/spec.json --content <out>/content.json`）：
    面板/图层/编码/图例一致性；结果进 `result.spec_lint`；lint 有问题时 status 不得为 success。

### 步骤 5 —— 生成可编辑源文件
12. `scripts/svgbuilder.py` 按 `references/layer-naming.md` 契约输出分层 SVG：
    `<g id="layer:*">` 七层、`<text>` 文字节点、`data-src`/`data-entity-id`/`data-role` 属性、
    `<title>/<desc>/<metadata>` 记录 Skill 版本与 build id。生成后立即用
    ElementTree 回解析校验良构。

### 步骤 6 —— 导出渲染件
13. `scripts/preview.py` 用与 SVG 同一份几何元素渲染 PNG（默认 2× 分辨率）与可选 PDF。
    后端链 matplotlib → Pillow → 纯 Python PNG，逐级回退并在 `render_log.json` 记录
    后端与字体回退；**字体缺失/后端降级不是静默成功**，写进 warning/uncertainty。

### 步骤 7 —— 自查（audit，含 v2 新检查）
14. `scripts/audit.py` 在**真实生成文件**上检查：SVG 良构、PNG 签名/尺寸、实体覆盖率、
    编码一致性（数值字符串在 SVG 文本中）、画布边界、色板灰度/色盲可区分性、缺值检测、
    同输入同输出探针（spec hash）、**四要素覆盖（Q-M-R-C 必齐）**、**图层命名合规
    （layer:* 七层 + 实体/关系/数据元素必须带 src）**。

### 步骤 8 —— 写 result.json
15. 按 `references/OUTPUT_CONTRACT.md`：`output_contract` 四形态回显（保留键冲突进
    `output_contract_echo`）+ 信封字段（`case_id/status/summary/deliverables/provenance/
    sources/uncertainty/change_records/audit` + v2 新增 `plan`/`spec_lint`）。
    `status`：success/partial/failed（lint 不过不得 success，见契约 §4）。

### 步骤 9 —— 收尾与复核
16. `python "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json --case <case.json>`
    —— **exit 0** 才说明顶层覆盖「信封 18 键 ∪ 案例 output_contract 全部字段」且无 null；
17. `audit.json` 无红线问题（SVG 良构、PNG 有效、实体全覆盖、数值全覆盖、四要素齐全、
    图层命名合规）。
18. 打开 PNG 目视：阅读顺序、箭头方向、图例对应、无文字被裁切。
19. 打开 SVG（文本编辑器即可）：`<text>` 可编辑、`data-src` 可溯源。
20. 同输入重跑一次，确认结构一致（spec hash 不变）。
21. 按 `references/RUBRIC_MAP.md` 逐条自评五维覆盖；人工确认写进 `change_records`。

预算纪律：64 次模型请求 / 900 秒 / 16384 tokens（含推理）。先出方案与中间件，
再逐段增量交付；脚本运行本身 <10s。

## 4. 决策规则（D1–D10）

| # | 情形 | 决策（做什么 | 记录在哪） |
|-|-|-|-|
| D1 | case.json 缺失/不可解析 | 立即失败（exit 1），不留半成品冒充成功 | stderr |
| D2 | 材料文件缺失 | 以已有材料继续；实体/数据为空如实说明 | uncertainty + content.notes |
| D3 | 关键数值缺失 | 图中「数值缺失」占位，值进 uncertainty，绝不编造 | audit.missing_values |
| D4 | **方案/规格 lint 不过** | 先修正 plan/spec；确属硬性限制 → 记录后继续，status 降 partial | result.plan.lint / result.spec_lint + uncertainty |
| D5 | 实体重名/歧义 | 取首次定义；两项都列出，说明歧义 | uncertainty |
| D6 | 文字溢出面板 | 自动缩字号（下限 8px）+ 截断提示，仍溢出则记录 | audit.layout_log |
| D7 | 元素越界画布 | 自动收缩；无法收缩进越界清单 | audit.bounds |
| D8 | 字体缺失（CJK/西文） | 渲染回退链逐级降级，字体名如实记录 | render_log + uncertainty |
| D9 | 导出失败（PNG/PDF） | 换后端重试（matplotlib→Pillow→纯 Python）；PDF 不可用如实标注 | render_log |
| D10 | 四要素缺面板 / 图层命名违规 | 绘制前即被 plan/spec lint 拦截；补救 = 补面板内容/归入契约层 | spec_lint + audit.four_element_coverage / layer_naming |

**完整失败模式与降级策略见 `references/failure-modes.md`**（含退出码语义、依赖缺失、
模板缺失、契约四形态、状态一致性、跨平台坑）。

## 5. 异常处理表（与 D 规则配套）

| 情形 | 处理 | 记录位置 |
|-|-|-|
| `case.json` 缺失/不可解析 | D1 | stderr |
| 材料文件缺失 | D2 | `uncertainty` + `content.notes` |
| 关键数值缺失 | D3 | `audit.missing_values` |
| 实体重名/歧义 | D5 | `uncertainty` |
| 文字溢出面板 | D6 | `audit.layout_log` |
| 元素越界画布 | D7 | `audit.bounds` |
| 字体缺失（CJK/西文） | D8 | `render_log.json` + `uncertainty` |
| 导出失败（PNG/PDF） | D9 | `render_log.json` |
| 布局后端不可用 | 自动走 Pillow；再不可走纯 Python PNG（文字占位并注明） | `render_log.json` |
| 保存中途失败 | 先落盘部分产物，报错含已写入路径 | stderr |
| 方案 lint 缺四要素说明 | D4：补 `four_elements` 后重跑 | `result.plan.lint` |
| 案例契约字段缺失 | 按四形态给 `""`/`[]`/`false`/`{}`，**禁止 null** | `check_contract.py` exit 0 |

## 6. 自查清单（每次运行后逐项确认）

- [ ] 读取的是真实文件（case.json/task.md/材料），不是凭标签假设内容
- [ ] 方案先行：`result.plan` 记录了 plan 来源与 lint 结果（无 plan 时 source=none）
- [ ] 图中每个实体/关系/数据带 `data-src` 且能在材料中定位（抽查 ≥3 项）
- [ ] `result.json` 包含 `output_contract` 四形态字段 + `case_id` + status/sources/
      uncertainty/change_records + plan/spec_lint
- [ ] `python "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json --case <case.json>` **exit 0**
- [ ] SVG 良构、`<text>` 可编辑、七层 `layer:*` 命名契约全绿（audit.layer_naming）
- [ ] 四要素 Q-M-R-C 覆盖无缺失（audit.four_element_coverage）
- [ ] PNG 预览存在且非空白；PDF（若启用）头 `%PDF-`
- [ ] 实体覆盖率 100%、数值编码一致性 100%（audit）
- [ ] 同输入重跑：spec hash 一致（结构稳定）
- [ ] 无「看起来热闹但无来源」的装饰性数据；已按 `references/RUBRIC_MAP.md` 五维自评

## 7. 评分维度落点（五维自查表）

题面满分 100（+5 公开链接）。**完整映射见 `references/RUBRIC_MAP.md`**，此处为速查：

| 维度 | 分值 | 本包落点（文件/机制） |
|-|-|-|
| 实际效果 | 40 | `scripts/{extract,figurespec,svgbuilder,preview}.py` 单页四要素流水线；可编辑分层 SVG + PNG/PDF 渲染件；`data-src` 逐元素溯源 + `provenance/sources`(sha256) |
| 使用增益 | 25 | 与"不加载 Skill 的基础 Agent"对照：数值可追源（spec_lint 硬门）、布局确定性（spec hash 两次一致）、文字可编辑、`scaffold.py` 一步出方案骨架、免重绘/重排版 |
| 创新增益 | 15 | 方案先行（plan-schema + lint_plan CP1 门）、四要素不变式（ga-four-elements.md）、SVG 分层命名可机器校验（layer-naming.md）、双 lint 门、契约四形态回显 |
| 可靠体验 | 10 | `references/failure-modes.md`（退出码语义 / 依赖降级链 / 模板缺失 / 契约四形态 / 状态一致性）；`audit.py` 六项红线；`check_contract.py` 独立自查 |
| 生态贡献 | 10 | 文档齐备（SKILL/README/TEST/OUTPUT_CONTRACT/RUBRIC_MAP/failure-modes/plan-schema/ga-four-elements/layer-naming/TEMPLATE）+ `assets/` 三件套 + `examples/` 最小示例 + `GITHUB_URL.txt` 公开入口 |

## 8. 目录结构

```
<skill root>/
  SKILL.md                本文档（自定位 + 五维落点 + 执行流程 + D1–D10）
  README.md               使用说明 / 依赖 / 参数 / 限制 / 失败处理 / 维护
  TEST.md                 本地实测记录（命令、产物、结果、复现判据）
  GITHUB_URL.txt          公开作品链接（第一行 URL；第二行为作品在仓库中的相对路径）
  references/
    OUTPUT_CONTRACT.md    result.json 契约 + 四形态回显 + G1–G8（唯一评分产物）
    RUBRIC_MAP.md         评分五维（40/25/15/10/10）→ 本包文件/机制逐条映射
    failure-modes.md      失败模式、降级策略、退出码、状态一致性
    plan-schema.md        设计方案 schema（方案先行）
    ga-four-elements.md   图形摘要四要素知识文档（Q-M-R-C 不变式）
    layer-naming.md       SVG 分层命名与溯源属性规范（机器可校验）
    TEMPLATE.md           面板模板 / 视觉通道映射 / 复用指南
  assets/                 可复用资产三件套（纯文本）
    spec_template.json    设计方案骨架模板
    result_example.json   结果信封示例（合成）
    example_material.txt  材料写法样例（"数值必须在材料中找到"）
  scripts/
    main.py               编排入口（--case/--task/--material/--plan/--out/--pdf…）
    extract.py            实体/关系/数据抽取（源定位）
    figurespec.py         确定性版面与数据编码
    svgbuilder.py         可编辑分层 SVG 输出（运行时生成）
    preview.py            PNG/PDF 预览（后端与字体回退链，运行时生成）
    audit.py              自查（四要素覆盖 / 图层命名 / 覆盖率 / 确定性）
    spec_lint.py          规格 + 方案 lint（--lint-plan / --spec；退出码即判据）
    scaffold.py           方案骨架生成（方案先行）
    check_contract.py     result.json 契约自查（信封 ∪ 案例契约，退出码即判据）
    common.py             公共工具（路径自定位、颜色、哈希、字体探测）
  examples/
    README.md             示例说明（合成案例、非正式案例、路径归一化说明）
    case.json / task.md / material.md   最小示例输入（合成数据）
    plan.example.json     已定稿设计方案（--plan 示例）
    EXPECTED-OUTPUT.md    期望产物清单与契约字段（文字版，替代预置渲染件）
    output/               本示例实跑产生的文本产物（result/spec/content/audit/render_log）
```

脚本不硬编码绝对路径：`scripts/common.py` 用 `os.path.dirname(os.path.abspath(__file__))`
自定位 Skill 根；所有输入输出路径由命令行显式给出（官方运行时为 `/input`、`/app/work`、
`/app/output`）。**包内无二进制资源、无 `.svg/.pdf/.png` 预置件、无字体文件** ——
渲染件与 SVG 一律运行时生成；字体按候选路径运行时探测（Windows/macOS/Linux）。
唯一保留的 `C:/Windows/Fonts` 等字符串是**跨平台字体探测候选路径**，不是本机运行残留。

## 9. 限制（如实声明）

- 渲染预览后端链可能降级（matplotlib → Pillow → 纯 Python PNG），后端如实记录；
- 实体抽取依赖材料文本结构；复杂表格/多图材料需 Agent 人工复核抽取结果；
- 四要素/图层检查是结构判据，不代替领域科学判断（图内容正确性以材料为准）；
- 示例数据为合成示意，与平台正式案例无关；正式案例结果由平台实跑产生。
