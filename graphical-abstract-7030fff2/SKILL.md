---
name: graphical-abstract
description: >-
  Generate or edit a single-page Graphical Abstract (图形摘要) from research
  material: extract scientific entities, relations and data with source
  provenance, lay out the question → method → results → conclusion story,
  encode data into bars/colors/lengths with consistent legends, and deliver an
  editable layered SVG plus rendered PNG/PDF previews and a verifiable
  result.json. Use when the task says "graphical abstract", "graphic
  abstract", "示意图 / 机制图 / 流程图 / 图稿", "make a figure for the paper /
  grant / report", "edit an existing figure", or asks to draw a mechanism,
  scheme or flow figure from experiment records.
---

# Graphical Abstract（图形摘要）Skill — figures group

把「研究问题—方法—核心结果—结论」压缩到单页视觉摘要，并交付**可继续编辑的源文件**。
本 Skill 对图的科学内容负责：实体不张冠李戴、箭头方向与因果一致、图例/单位/比例尺与数据一一对应、
每个元素可溯源、同输入可复现。**绝不编造数据**：图中数值必须能在来源材料里找到对应记录。

- Skill 版本：`1.0.0`（脚本版本见 `scripts/common.py` 的 `SKILL_VERSION`）
- Skill 根：本文件所在目录（下文中所有相对路径均相对 Skill 根）

---

## 1. 用途与适用条件

**适用**：给定研究描述、实验记录、论文草稿/图表数据，要求产出单页图形摘要（问题/方法/结果/结论四要素）、
机制图、流程图或科研图表，且要求可编辑源文件 + 渲染件 + 可复核来源。

**适用输入形态**（至少其一，全部读取真实文件，绝不凭文件名/标签猜内容）：

| 输入 | 说明 |
|-|-|
| `case.json` | 必读。可含 `case_id / title / task / source_material / entities / relations / data / figure_constraints / output_contract`（字段名兼容常见同义词，见 `scripts/extract.py` 顶部） |
| `task.md` | 任务说明；含 `# 问题/方法/结果/结论` 小节的直接映射为面板要点 |
| 材料文件 | `source_material` 指明的 md/txt/tex/csv 等；提供数值与机制的真正来源 |
| `figure_constraints` | 画布宽高、colorblind、flow_arrows、raster_scale、pdf 等（有默认值） |
| `output_contract` | 案例自带的交付契约；其中每个字段都会原样进 `result.json` 顶层（见 `references/OUTPUT_CONTRACT.md`） |

**不适用/明确边界**：正文写作、统计分析、实验设计不在本 Skill 范围；本 Skill 只对图形内容的
科学表达、版式、可编辑性与导出质量负责。

## 2. 输入与输出

**输入路径约定（Runtime contract）**：官方案例运行时，`/input/case.json` 与 `task.md` 由平台挂载，
材料按案例提供；在工作目录 `/app/work` 内解析相对路径。本机/任意环境：`--case <case.json>` 显式指定。

**输出**：全部写到 `--out` 指定目录（官方约定为 `/app/output`；本机默认 `<skill>/out`）：

| 文件 | 内容 |
|-|-|
| `<case_id>_graphical_abstract.svg` | **可编辑分层 SVG 源**（7 层：background/panels/entities/relations/data/legend/annotations；文字为真 `<text>`；元素带 `data-src`/`data-entity-id`/`data-role` 溯源属性） |
| `<case_id>_graphical_abstract.png` | 渲染预览（matplotlib → Pillow → 纯 Python PNG 回退链，渲染器与后端如实记录在 `render_log.json`） |
| `<case_id>_graphical_abstract.pdf` | 矢量 PDF 预览（matplotlib 可用时；`pdf=false` 或不可用则跳过并如实说明） |
| `result.json` | **结构化结果**（契约见 `references/OUTPUT_CONTRACT.md`） |
| `spec.json` | 机器可读图面规格（与 SVG 同一几何，便于再编辑/评审） |
| `content.json` | 规范化抽取结果（实体/关系/数据/面板要点 + 来源定位） |
| `audit.json` / `render_log.json` | 自查报告与渲染日志 |

## 3. 执行步骤

第 1–8 步由脚本流水线执行（`python scripts/main.py --case <case.json> [--task <task.md>] [--material <file|dir>] --out <dir>`）；
作为 Agent，你**必须**在调用脚本之外阅读真实文件内容并复核抽取结果，偏差在 `result.json` 的
`change_records` / `uncertainty` 中如实记录。**不得用预制答案替代实际运行。**

### 步骤 1 —— 读实际文件（不要凭标签猜内容）
1. 读取 `case.json`（UTF-8）；失败即报错退出并说明，不留虚假产物。
2. 解析 `source_material` 相对路径（对 `case.json` 所在目录/`/app/work` 解析），逐个读取材料文件原文。
3. 读取 `task.md`（若存在），提取 `# 问题/方法/结果/结论` 小节要点与交付要求。

### 步骤 2 —— 抽取实体/关系/数据（source-bound）
运行 `scripts/extract.py`（由 `main.py` 调用）：规范化 entities/relations/data，
并扫描材料文本中的 `A -> B (label)`、`键: 值 单位` 行作为补充事实。
**规则：** 每个元素带 `src`（`文件:行` 或 `case.json[字段]`）；同 id 首见优先；
材料中找不到源头的数值**不得上画布**，只进 `uncertainty` 并以「数值缺失」占位。
复核面板要点是否进入正确面板（问题/方法/结果/结论）。

### 步骤 3 —— 版面与数据编码（确定性布局）
`scripts/figurespec.py` 生成图面规格：四列面板按「问题→方法→结果→结论」阅读顺序、
结果面板内条形/色块子图、跨面板流程箭头、页脚图例 + 比例尺 + 来源说明。
数据编码：`bar_length`（长度∝数值）、`color_scale`（色阶，Okabe-Ito 色盲安全色板）、`area`/`value_label`。
所有编码项进入 `data_encoding` + `legend`，**图例值与画面数值一一对应**。

### 步骤 4 —— 生成可编辑源文件
`scripts/svgbuilder.py` 手写 XML 输出分层 SVG：
`<g id="layer:*">` 分组、`<text>` 文字节点（可选中可编辑）、`data-src` 溯源属性、
`<title>/<desc>/<metadata>` 记录 Skill 版本与 build id。生成后立即用 ElementTree 回解析校验良构。

### 步骤 5 —— 导出渲染件
`scripts/preview.py` 用与 SVG 同一份几何元素渲染 PNG（默认 2× 分辨率）与可选 PDF。
后端链 matplotlib → Pillow → 纯 Python PNG，逐级回退并在 `render_log.json` 记录后端与字体回退；
**字体缺失/后端降级不是静默成功**，要写进 warning/uncertainty。

### 步骤 6 —— 自查（audit）
`scripts/audit.py` 在**真实生成文件**上检查：SVG 良构、PNG 签名/尺寸、实体覆盖率（每个实体上画布）、
编码一致性（每个数值字符串出现在 SVG 文本中）、画布边界（溢出即调整或记录）、
色板灰度/色盲可区分性、缺值检测、同输入同输出探针（spec hash）。

### 步骤 7 —— 写 result.json
按 `references/OUTPUT_CONTRACT.md`：`output_contract` 全部字段镜像进顶层（保留键冲突时放入
`output_contract_echo`）+ 信封字段（`case_id/status/summary/deliverables/provenance/sources/uncertainty/change_records/audit/...`）。
`status`：成功=success；有缺值/溢出/字体回退等=partial（必须写明限制）；未产出=失败。

### 步骤 8 —— 收尾与复核
- `audit.json` 无红线问题（SVG 良构、PNG 有效、实体全覆盖、数值全覆盖）。
- 打开 PNG 目视：阅读顺序、箭头方向、图例对应、无文字被裁切。
- 打开 SVG（文本编辑器即可）：`<text>` 可编辑、`data-src` 可溯源。
- 同输入重跑一次，确认结构一致（spec hash 不变）。
- 把人工确认与修改写进 `change_records`。

## 4. 异常处理（失败模式表）

| 情形 | 处理 | 记录位置 |
|-|-|-|
| `case.json` 缺失/不可解析 | 立即失败（exit 1），不产出半成品冒充成功 | stderr |
| 材料文件缺失 | 以已有材料继续；实体/数据为空时如实说明 | `uncertainty` + `content.notes` |
| 关键数值缺失 | 图中「数值缺失」占位，值进 `uncertainty`，绝不编造 | `audit.missing_values` |
| 实体重名/歧义 | 取首次定义；两项都列出，说明歧义 | `uncertainty` |
| 文字溢出面板 | 自动缩字号（下限 8px）+ 截断提示，仍溢出则记录 | `audit.layout_log` |
| 元素越界画布 | 自动收缩布局；无法收缩的列进越界清单 | `audit.bounds` |
| 字体缺失（CJK/西文） | 渲染回退链逐级降级，字体名如实记录 | `render_log.json` + `uncertainty` |
| 导出失败（PNG/PDF） | 换后端重试（matplotlib→Pillow→纯 Python）；PDF 不可用则如实标注 | `render_log.json` |
| MATLAB/matplotlib 不可用 | 自动走 Pillow；再不可用走纯 Python PNG（文字以占位框呈现并注明） | `render_log.json` |
| 保存中途失败 | 先落盘部分产物，报错信息含已写入路径 | stderr |

## 5. 自查清单（每次运行后逐项确认）

- [ ] 读取的是真实文件（case.json/task.md/材料），不是凭标签假设内容
- [ ] 图中每个实体与数值都带 `data-src` 且能在材料中定位（抽查 ≥3 项）
- [ ] `result.json` 包含 `output_contract` 全部字段 + `case_id` + status/sources/uncertainty/change_records
- [ ] SVG 良构（可被 ElementTree / 浏览器打开）、`<text>` 可编辑、分层命名清晰
- [ ] PNG 预览存在且非空白；PDF（若启用）头 `%PDF-`
- [ ] 实体覆盖率 100%、数值编码一致性 100%（`audit.json`）
- [ ] 同输入重跑：spec hash 一致（结构稳定）
- [ ] 无「看起来热闹但无来源」的装饰性数据

## 6. 目录结构

```
<skill root>/
  SKILL.md                本文档
  README.md               使用说明 / 依赖 / 限制 / 失败处理
  TEST.md                 本地实测记录
  GITHUB_URL.txt          GitHub 公开链接占位（发布代理覆写）
  references/
    OUTPUT_CONTRACT.md    result.json 结构与字段契约
    RUBRIC_MAP.md         评分五维 → 设计覆盖映射
    TEMPLATE.md           面板模板 / 图层约定 / 复用指南
  scripts/
    main.py               编排入口（命令行）
    extract.py            实体/关系/数据抽取（源定位）
    figurespec.py         确定性版面与数据编码
    svgbuilder.py         可编辑分层 SVG 输出
    preview.py            PNG/PDF 预览渲染（后端回退链）
    audit.py              自查（良构/覆盖/边界/灰度/确定性）
    common.py             公共工具（路径自定位、颜色、哈希、字体）
  examples/
    case.json / task.md / material.md   最小示例输入（合成数据，非正式案例）
    output/*                             示例输出（标注「示例，非正式案例」）
```

脚本不硬编码绝对路径：`scripts/common.py` 用 `os.path.dirname(__file__)` 自定位 Skill 根；
所有输入输出路径由命令行显式给出（官方运行时为 `/input`、`/app/work`、`/app/output`）。