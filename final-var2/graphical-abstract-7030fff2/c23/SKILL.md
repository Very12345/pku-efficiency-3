# Graphical Abstract（图形摘要）Skill v2 — figures group · 整合版（增益层 + 机制层）

> 本包整合了基线 Skill 与 2 个强化层,各层对应不同的评分维度:使用增益 25 · 创新增益 15 + 生态贡献 10。
> 各层内容**不重复**:决策层给规则与失败分支;增益层给对照协议与指标口径;机制层给机制说明与可复用资产。
> 建议使用顺序:先用「决策层」跑通并处理异常,再用「增益层」证明并度量改善,最后用「机制层」复用与扩展。
> 各层的原始文件都完整保留在本包内,不是摘要 —— 下面每一层都是可以独立执行的完整规范。

## 本包文件索引

- `GITHUB_URL.txt`
- `README.md`
- `TEST.md`
- `assets/example_material.txt`
- `assets/result_example.json`
- `assets/spec_template.json`
- `examples/EXPECTED-OUTPUT.md`
- `examples/README.md`
- `examples/case.json`
- `examples/material.md`
- `examples/plan.example.json`
- `examples/task.md`
- `references/GAIN-PROTOCOL.md`
- `references/MECHANISM.md`
- `references/OUTPUT_CONTRACT.md`
- `references/REUSE-KIT.md`
- `references/RUBRIC_MAP.md`
- `references/TEMPLATE.md`
- `references/failure-modes.md`
- `references/ga-four-elements.md`
- `references/layer-naming.md`
- `references/plan-schema.md`
- `scripts/audit.py`
- `scripts/check_contract.py`
- `scripts/common.py`
- `scripts/extract.py`
- `scripts/figurespec.py`
- `scripts/gain_harness.py`
- `scripts/main.py`
- `scripts/preview.py`
- `scripts/scaffold.py`
- `scripts/spec_lint.py`
- `scripts/svgbuilder.py`
- `examples/output/_LABEL_example.txt`
- `examples/output/audit.json`
- `examples/output/content.json`
- `examples/output/render_log.json`
- `examples/output/result.json`
- `examples/output/spec.json`

---

# 【增益层】公平对照协议与可测指标（目标维度:使用增益 25）

---
name: graphical-abstract
description: >-
  单页 Graphical Abstract（图形摘要）Skill，以「增益可验证」为核心设计目标：同一条入口
  （--case/--out）跑完整链路 —— 材料抽取（逐元素 data-src 溯源）→ 方案先行与方案 lint →
  确定性版面与数据编码 → 可编辑分层 SVG + PNG/PDF → audit 与契约自查；并同时交付
  一套**可复算的对照协议**（references/GAIN-PROTOCOL.md）与只读测量器
  （scripts/gain_harness.py），把"加载 Skill 后到底改善了哪几项"折算成
  可被第三方重跑的指标（分层数、真文字节点、溯源覆盖率、四要素覆盖、数值可定位率、
  契约覆盖率、结构确定性、单次耗时）。Use when the task says "graphical abstract"、
  "图形摘要"、"机制图 / 示意图 / 流程图"、"为论文或基金画一张图"、"把结果画成一页"，
  或要求证明绘图流程相对基线做法的改进幅度。
---

## Graphical Abstract 图形摘要 Skill — 增益可验证版

产出物与同类 Skill 相同：一页讲完**研究问题 → 方法 → 核心结果 → 结论**，交付
**可编辑分层 SVG**（不是位图截图）、PNG/PDF 预览、以及字段完整的 `result.json`
（含来源、状态、不确定性、变更记录）。**数值不编造**：材料里定位不到的数值只进
`uncertainty` 并占位。

本版本把重点放在一个常被含糊处理的问题上：**"用了这个 Skill，到底好在哪、好多少"**。
为此包内提供三样东西：

1. **对照协议**（`references/GAIN-PROTOCOL.md`）：定义条件 A（加载本 Skill）与
   条件 B（不加载 Skill 的基础做法）的可比条件、指标口径、复算命令与局限；
2. **只读测量器**（`scripts/gain_harness.py`）：对任意输出目录算同一组指标，
   自身不产生任何图、不参与出图流水线；
3. **真实对照记录**：本地已按协议跑完 A / B / B+ 三种条件并留下原始指标
   （见 `references/GAIN-PROTOCOL.md` §4，含失败面与对 A 不利的数字）。

| 项目 | 值 |
|-|-|
| Skill 名称 / 版本 | `graphical-abstract` / `2.0.0`（`scripts/common.py` 的 `SKILL_VERSION`） |
| 技能根 | 本文件所在目录，下文记作 `$SKILL_DIR` |
| 资源形态 | 纯文本七种扩展名；无二进制/无预置渲染件/无字体文件/无 `__pycache__`/无绝对路径 |
| 新增于本轴 | `references/GAIN-PROTOCOL.md`、`scripts/gain_harness.py` |
| 出图入口 | `python "$SKILL_DIR/scripts/main.py" --case <case.json> [--plan plan.json] --out <dir>`（未改动） |

---

### 1. 快速调用（cwd 任意；命令逐字可用）

```bash
# 技能根（二者取一；不确定时用下面一行向上探测）
SKILL_DIR=/skills/weekly-skill
SKILL_DIR=/abs/path/to/graphical-abstract-7030fff2
SKILL_DIR="$(pwd)"; while [ ! -f "$SKILL_DIR/SKILL.md" ] && [ "$SKILL_DIR" != "/" ]; do SKILL_DIR="$(dirname "$SKILL_DIR")"; done

# 出图（示例案例；产物写包外目录）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/ga-out

# 契约自查（exit 0 = 顶层覆盖「信封 ∪ 案例契约」且无 null）
python "$SKILL_DIR/scripts/check_contract.py" --result /tmp/ga-out/result.json --case "$SKILL_DIR/examples/case.json"

# 官方案例形态
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md --out /app/output
```

参数表与依赖清单见 `README.md` §2/§3；本文件不重复。

---

### 2. 可比性设计（为什么"对照"能成立）

对照最容易失真在**条件不对等**。本包把可比条件写成硬约束，逐条可核对：

| 可比维度 | 本包做法 | 对照时如何保证 |
|-|-|-|
| 同一输入 | `case.json` + `task.md` + `source_material` 由调用方给定；抽取只读真实文件 | A/B 使用**同一个** case 目录，不替换材料、不预置答案 |
| 同一条入口 | 单命令 `main.py --case --out`；不要求 cwd = 技能根 | B 条件也必须是"一条命令出图"，不允许人工补画 |
| 同一约束 | 画布尺寸/DPI/色盲安全/图例/比例尺来自 `figure_constraints`；数值只来自材料 | 两侧使用同一份 constraints，代码里不硬编码尺寸 |
| 同一预算 | 官方 64 请求 / 900 秒 / 16384 tokens；本地对照按"单次运行墙钟 + 返工步数"计 | 见 §3 指标 E1/E2，两侧同一计法 |
| 同一判定 | 指标由 `scripts/gain_harness.py` 计算，**不采信自述** | 第三方可对任意目录复算，含对 A 不利的指标 |

**反过来说**：如果某项指标 A 并不占优（例如单次运行的墙钟时间），本包也照样记录 ——
见 `references/GAIN-PROTOCOL.md` §4 的"对 A 不利的观测"。

---

### 3. 可测指标（口径固定，全部由测量器复算）

| 编号 | 指标 | 口径（怎么算） | 属于哪一维 |
|-|-|-|-|
| G1 | 可编辑性 | SVG 中 `<g id="layer:*">` 层数；真 `<text>` 节点数；`<use>` 字形引用数（>0 说明文字被轮廓化） | 使用增益（质量）/实际效果 |
| G2 | 溯源覆盖率 | 带 `data-src` 的元素数 ÷ 带 `entity/relation/datum/icon` 角色的元素数 | 实际效果（可核验性） |
| G3 | 四要素覆盖 | 图面可检测到的面板语义数 ÷ 4（研究问题/方法/结果/结论） | 实际效果（完整性） |
| G4 | 数值可定位率 | 图面数值标签中能在材料原文里字符串级定位的个数 ÷ 图面数值标签数 | 实际效果（正确性） |
| G5 | 契约完整率 | `result.json` 顶层非空覆盖的案例契约字段数 ÷ 契约字段数；并看 `verdict` | 实际效果 / 可靠体验 |
| G6 | 结构确定性 | 同输入两次运行的**结构指纹**（层数/文字数/角色元素数/文本集合/顶层键/`spec_sha16`）是否逐项一致 | 使用增益（质量） |
| G7 | 证据完备性 | 是否产出 `audit.json` / `render_log.json` / `spec.json`（结构化自查与降级记录） | 可靠体验 |
| G8 | 效率 | E1 单次运行墙钟秒数；E2 达到"契约完整 + 溯源可核验"所需返工步数 | 使用增益（效率） |

```bash
# 复算单条件（--material 用于 G4 的分母口径）
python "$SKILL_DIR/scripts/gain_harness.py" --out /tmp/ga-out \
       --case "$SKILL_DIR/examples/case.json" --material "$SKILL_DIR/examples/material.md" --label A
# 复算确定性（G6）：同输入跑两次后比较结构指纹
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/ga-r1 >/dev/null
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/ga-r2 >/dev/null
python "$SKILL_DIR/scripts/gain_harness.py" --compare /tmp/ga-r1 /tmp/ga-r2
```

---

### 4. 执行步骤（每步都留下可测量的证据）

第 0–9 步由 `scripts/main.py` 执行；Agent 的额外职责是读材料并复核抽取结果，偏差进
`change_records` / `uncertainty`。

| 步 | 动作 | 命令 | 该步留下的证据（可复算） |
|-|-|-|-|
| 0 | 方案先行：骨架 → 定稿 → CP1 门 | `scaffold.py --case … --out plan.json`；`spec_lint.py --lint-plan --plan plan.json` | `result.plan.{source,hash,lint}`；门是否放行（exit 0/1） |
| 1 | 读真实文件 | 直接读 `case.json` / `task.md` / 材料 | `provenance.source_files[].sha256` |
| 2 | 抽取实体/关系/数据 | `extract.py` | `content.json`；每项 `src` |
| 3 | 版面与数据编码 | `figurespec.py` | `spec.json`：`legend` / `data_encoding` / `reading_order` |
| 4 | 规格 lint（绘制前） | `spec_lint.py --spec … --content …` | `result.spec_lint.{valid,problems,spec_sha16}` |
| 5 | 分层 SVG | `svgbuilder.py` | G1 的层数与 `<text>` 数 |
| 6 | 渲染 PNG/PDF | `preview.py` | `render_log.json`：`backend` / `font` / `warnings` |
| 7 | 自查 | `audit.py` | `entity_coverage` / `encoding_consistency` / `bounds` / `layout_log` / `four_element_coverage` / `layer_naming` / `determinism_probe` |
| 8 | 写 `result.json` | 契约四形态回显 + 信封 | G5 的覆盖数与 `verdict` |
| 9 | 收尾 | `check_contract.py --result … --case …` | 契约自查 exit 0；G7 的三个证据文件存在 |

---

### 5. 决策速查表（R1–R14：情形 → 动作 → 记录位点）

> 本表是"边跑边查"的压缩版；同一批规则在 `references/failure-modes.md` §2 有
> 检测点与验证命令，两处编号一致（R 前缀）。

| # | 情形 | 动作 | 失败时 | 记录位点 |
|-|-|-|-|-|
| R1 | `case.json` 缺失/不可解析 | 立即失败，**exit 1** | 不猜测内容、不留半成品 | stdout JSON |
| R2 | `case_id` 缺失 | 回退到文件名并标注 | 不伪造 id | `result.case_id` / `uncertainty` |
| R3 | `task.md` 缺失 | 由材料小节标题映射面板要点 | 面板留空结构，不填填充句 | `warnings` |
| R4 | 材料缺失/为空 | 用可用材料继续 | 计数如实为 0 | `content_summary` / `uncertainty` |
| R5 | 关键数值缺失 | 「数值缺失」占位 | 该点移出编码子图 | `audit.missing_values` |
| R6 | 实体重名/歧义 | 首见优先，两项并列 | 歧义未解不画该关系箭头 | `uncertainty` |
| R7 | 材料数值矛盾 | 首见优先，双 `src` 并列 | **不平均、不择优** | `uncertainty` |
| R8 | 材料非 UTF-8 / 二进制 | 替换字符读取 / 跳过二进制 | 乱码段仅作背景 | `warnings` / `content.notes` |
| R9 | 字体缺失（CJK） | 候选路径探测 → 逐级降级 | SVG `<text>` 仍为真文字 | `render_log.font` |
| R10 | matplotlib/Pillow 缺失 | 后端链 matplotlib→Pillow→纯 Python PNG | 文字占位并注明 | `render_log.backend` |
| R11 | PDF 不可用 | PNG 照常；PDF 标 `present:false` + 原因 | 不允许空路径假装成功 | `deliverables[format=pdf]` |
| R12 | 文字溢出/元素越界 | 缩字号（下限 8px）+ 坐标夹紧 | 仍溢出进清单 | `audit.layout_log` / `bounds` |
| R13 | 方案或规格 lint 不过 | 先修；修不动则降 `partial` | **不得 success** | `result.plan.lint` / `result.spec_lint` |
| R14 | 契约字段无真实值 / 键冲突 | 按 `""`/`[]`/`false`/`{}` 回显；冲突值进 `output_contract_echo` | 禁止 null | `check_contract.py` exit 0 |

---

### 6. 增益记录（摘要；原始记录与复算命令见 GAIN-PROTOCOL）

本地同机同输入（合成示例案例 6 实体 / 5 关系 / 7 数据点 / 1200×800 @300dpi）实测：

| 指标 | A：加载本 Skill | B：不加载 Skill 的基础做法 | B+：给 B 最有利的可编辑性设置 |
|-|-|-|-|
| G1 分层 / 真文字 / 字形轮廓 | 7 层 / 61 / 0 | 0 层 / 0 / 435 | 0 层 / 38 / 12 |
| G2 溯源覆盖率 | 0.903（56/62） | 0（0/0） | 0（0/0） |
| G3 四要素覆盖 | 4/4 | 0/4 | 1/4 |
| G4 数值可定位率 | 14/16 | 0/0（位图为主） | 7/15 |
| G5 契约完整率 | 8/8（complete，顶层 26 键） | 0/8（absent，顶层 4 键） | 0/8（absent） |
| G6 结构确定性 | 两次一致 | 两次一致 | 未测两次 |
| G7 证据文件 | audit + render_log + spec 齐 | 全缺 | 全缺 |
| G8 E1 单次墙钟 | 2.44 s / 2.16 s | 1.71 s / 1.51 s | — |

**必须同时读的三条边界**（详见 GAIN-PROTOCOL §4/§5）：
① E1 上 A 比 B **慢**约 0.5–0.9 秒/次，A 的收益在 E2（免返工）而不是单次速度；
② G6 上 B 也做到了两次一致 —— 确定性**不是**本包的独占优势；
③ 上述 B 条件是本地最小复现（单次脚本出图），**不等于**平台官方对照里那个
   "不加载 Skill 的基础 Agent"；正式对照由平台生成，本包只提供可复算的代理证据。

---

### 7. 交付前自查清单

- [ ] 读的是真实文件（case/task/材料），没有凭标签猜内容
- [ ] `result.plan` 记录了方案来源与 lint 结果；方案 lint 不过时不绘制
- [ ] 抽查 ≥3 个元素：`data-src` 能在材料中定位
- [ ] `check_contract.py` **exit 0**；`result.json` 顶层无 null
- [ ] `audit.four_element_coverage.missing` 为空；`layer_naming.bad` 为空
- [ ] `audit.encoding_consistency.missing_from_canvas` 为空
- [ ] `render_log.json` 的 `backend` / `font` 与实际情况一致（降级已记录）
- [ ] 同输入重跑：`determinism_probe.spec_sha16` 一致（可用 `gain_harness.py --compare` 复核）
- [ ] 若要报告增益：用 `gain_harness.py` 在同一输入上跑 A 与自己的基线，**如实记录不利项**
- [ ] 五维覆盖按 `references/RUBRIC_MAP.md` 自评；文字自述不作为运行证据

---

### 8. 五维落点（速查）

| 维度 | 分 | 本包落点 |
|-|-|-|
| 实际效果 40 | | 四要素单页流水线 + 可编辑分层 SVG/PNG/PDF；逐元素溯源；`audit` 量化核验 |
| 使用增益 25 | | **本轴主强化**：`references/GAIN-PROTOCOL.md`（可比条件 + 指标口径 + 真实对照记录）+ `scripts/gain_harness.py`（第三方可复算）；免重绘/免搬运的机制 |
| 创新增益 15 | | 方案先行 + 双 lint 门 + 图层命名契约 + 契约四形态回显；**把"增益"本身做成可复算协议** |
| 可靠体验 10 | | R1–R14 速查 + `references/failure-modes.md`（退出码/降级/证据）+ `audit` 红线 + 两个 exit-code 自查器 |
| 生态贡献 10 | | 文档齐备 + 资产三件套 + 最小示例 + 测量器可被任何项目直接拿去做对照 |

---

### 9. 目录结构

```
<skill root>/
  SKILL.md                     自定位 + 可比性设计 + 指标 G1–G8 + 决策速查 R1–R14
  README.md                    使用说明 / 参数 / 依赖 / 限制 / 如何复算增益 / 维护
  TEST.md                      本地实测（出图链 + 对照链，含真实数字）
  GITHUB_URL.txt               公开作品链接
  references/
    OUTPUT_CONTRACT.md         result.json 契约（唯一评分产物；字段名不改）
    RUBRIC_MAP.md              五维 → 机制 → 复算命令
    GAIN-PROTOCOL.md           ★ 对照协议 + 指标口径 + 真实对照记录 + 局限
    failure-modes.md           R1–R14 的检测点/处置/验证命令
    plan-schema.md             设计方案 schema（方案先行）
    ga-four-elements.md        四要素内容知识
    layer-naming.md            SVG 分层与溯源属性规范
    TEMPLATE.md                面板模板与视觉通道映射
  assets/                      纯文本资产三件套
  scripts/                     10 个流水线脚本（未改动）+ gain_harness.py（只读测量器）
  examples/                    最小示例（合成案例）与其实跑产物
```

`scripts/gain_harness.py` **不出图、不参与 `main.py` 流水线**：它只读一个输出目录并打印
指标 JSON。把它删掉不影响出图，只是无法复算增益。

---

### 10. 限制（如实声明）

- 本地对照的条件 B 是**最小复现脚本**而非真实无 Skill 的 LLM Agent；它衡量的是
  "机制层面的差距"，平台官方的白板对照才是正式依据；
- 指标是**结构与文本级**判据（层数、属性数、字符串可定位性），不判断图的美观与
  领域结论正确性；
- 渲染后端可能降级；降级后 PNG 文字可能为占位框，但 SVG 的 `<text>` 仍可编辑；
- `examples/` 为合成示例，与平台正式案例无关；平台正式案例由组织方挂载运行。

---

# 【机制层】机制说明与可复用资产（目标维度:创新增益 15 + 生态贡献 10）

---
name: graphical-abstract
description: >-
  单页 Graphical Abstract（图形摘要）Skill：把研究问题、方法、核心结果、结论压进一页，
  并交付可编辑分层 SVG + PNG/PDF 预览 + 可复核 result.json。本包围绕三个**独特机制**组织：
  M1 逐元素来源挂接（每个科学元素带 data-src，越界的数值不上画布）、
  M2 方案先行 + 双 lint 门（绘制前后各一道可执行判据）、
  M3 契约四形态回显 + 状态一致性（status 不得虚报，禁 null）。
  每个机制都写明"没有它会怎样"、由哪个脚本执行、留下什么可核验证据，并配套
  可复用资产清单与三步移植流程（references/MECHANISM.md、references/REUSE-KIT.md）。
  Use when the task says "graphical abstract"、"图形摘要"、"机制图 / 通路图 / 流程图"、
  "为论文、基金或汇报画一张能继续编辑的图"，或要求把实验记录/研究描述做成单页图稿。
---

## Graphical Abstract 图形摘要 Skill — 机制与复用版

同类工具大多在回答"怎么画"。本包回答的是另外两个问题：**"画出来的东西凭什么可信"**
与 **"这套做法能不能被别人拿走用在别的图上"**。为此本包把能力收敛成三个机制，
每个机制都配了反事实说明（没有它会怎样）、执行脚本、以及可核验证据：

| 机制 | 一句话 | 没有它会怎样 | 执行者 | 证据 |
|-|-|-|-|-|
| **M1 来源挂接** | 每个科学元素带 `data-src`，数值只在材料里存在时才上画布 | 图能看但不可查：审稿人问"这个 85% 从哪来"时无从回答；缺值被"看起来合理"的数字填掉 | `scripts/extract.py`、`scripts/svgbuilder.py`、`scripts/audit.py` | `data-src` 属性（实测 56 个）、`audit.entity_coverage` / `encoding_consistency`、`result.sources[]`（含 sha256） |
| **M2 双 lint 门** | 绘制前拦方案、绘制后拦规格，两道门都是 exit code 判据 | 错误在"画完"之后才被发现，只能整张重画；面板缺要素、图例与数据错位的图会被当成成品交出去 | `scripts/scaffold.py`、`scripts/spec_lint.py`（`--lint-plan` / `--spec`） | 方案门 exit 0/1、`result.plan.lint`、`result.spec_lint` |
| **M3 契约与状态一致性** | 契约四形态回显（`""`/`[]`/`false`/`{}`，禁 null）+ `status` 不得虚报 | 评分产物字段缺失或为 null，复核方无法判断结果是否可信；"图没出来但报成功"这类虚报会毁掉整包可信度 | `scripts/main.py`、`scripts/check_contract.py` | 顶层 26 键（信封 18 ∪ 契约 8）、`check_contract.py` exit 0、`result.status` 与 `audit.checks` 一致 |

机制的完整反事实推理、边界与实测证据见 [`references/MECHANISM.md`](references/MECHANISM.md)；
可复用资产清单与三步移植见 [`references/REUSE-KIT.md`](references/REUSE-KIT.md) 与本文 §6。

| 项目 | 值 |
|-|-|
| Skill 名称 / 版本 | `graphical-abstract` / `2.0.0`（`scripts/common.py` 的 `SKILL_VERSION`） |
| 技能根 | 本文件所在目录（下文 `$SKILL_DIR`） |
| 资源形态 | 纯文本；无二进制、无预置渲染件、无字体文件、无 `__pycache__`、无本机绝对路径 |
| 本轴新增 | `references/MECHANISM.md`、`references/REUSE-KIT.md`、`references/GAIN-PROTOCOL.md`、`scripts/gain_harness.py` |

---

### 0. 调用（cwd 任意；命令逐字可用）

```bash
SKILL_DIR=/skills/weekly-skill                        # 官方评测容器
SKILL_DIR=/abs/path/to/graphical-abstract-7030fff2    # 本机解压目录
SKILL_DIR="$(pwd)"; while [ ! -f "$SKILL_DIR/SKILL.md" ] && [ "$SKILL_DIR" != "/" ]; do SKILL_DIR="$(dirname "$SKILL_DIR")"; done

# 冒烟（示例案例，产物写包外）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/ga-out
# 官方案例形态
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md --out /app/output
```

### 1. 适用与边界

**适用**：从研究描述、实验记录、论文草稿/图表数据出发，产出单页图形摘要（机制图/通路图/
流程图/结果图），且要求**可继续编辑的源文件**与**可追溯的元素来源**。

**不适用**：论文正文写作、统计分析、实验设计。本 Skill 对图面科学内容的表达、版式、
可编辑性与导出质量负责；材料本身的结论正确性由材料负责。

### 2. 机制 → 脚本 → 证据链

| 步骤 | 谁执行 | 产出 | 机制归属 | 可核验点 |
|-|-|-|-|-|
| ① 读真实输入 | Agent + `main.py` | 材料原文与结构 | M1 | `provenance.source_files[].sha256` |
| ② 出方案骨架 → 定稿 | `scaffold.py` + Agent | `plan.json`（含 `four_elements`） | M2 | 骨架里的 `src` 定位 |
| ③ 方案 lint（绘制前门） | `spec_lint.py --lint-plan` | 通过/不通过 + problems | M2 | **exit 0/1**；`result.plan.lint` |
| ④ 抽取实体/关系/数据 | `extract.py` | `content.json` | M1 | 每项 `src`；首见优先 |
| ⑤ 版面与数据编码 | `figurespec.py` | `spec.json`（legend/encoding/reading_order） | M1+M2 | 图例↔数据一一对应 |
| ⑥ 规格 lint（绘制后门） | `spec_lint.py --spec` | `result.spec_lint` | M2 | `valid` 与 `problems` |
| ⑦ 分层 SVG | `svgbuilder.py` | `<case_id>_graphical_abstract.svg` | M1 | 7 层 `layer:*`；真 `<text>`；`data-src` |
| ⑧ 渲染预览 | `preview.py` | PNG / PDF + `render_log.json` | M3 | `backend` / `font` / 降级告警 |
| ⑨ 自查 | `audit.py` | `audit.json` | M1+M3 | 覆盖率、越界、缺值、四要素、图层命名、确定性探针 |
| ⑩ 契约与状态 | `main.py` + `check_contract.py` | `result.json` | M3 | 顶层 26 键；exit 0；`status` 与 checks 一致 |
| ⑪ 复核（可选但推荐） | `gain_harness.py` | 指标 JSON | 复用 | G1–G8（见 `references/GAIN-PROTOCOL.md`） |

### 3. 决策规则 K1–K16（按机制分组）

> 与前作不同，这里按**机制**分组：M1 组管"科学诚实"，M2 组管"拦在绘制前"，M3 组管
> "交付态一致"，最后一组管"跨平台与复用"。每行给：触发 → 动作 → 失败时的降级 → 记录位点。

#### 3.1 M1 组：来源挂接与科学诚实（K1–K6）

| # | 触发 | 动作 | 失败时的降级 | 记录位点 |
|-|-|-|-|-|
| K1 | 材料里找不到某数值 | 图上「数值缺失」占位，**不上编造数字** | 该数据点移出编码子图，保留指标名 | `audit.missing_values` |
| K2 | 实体重名 / 同名不同物 | 同 id 首见优先，两项并列标注 | 歧义未解则该实体的关系箭头不画 | `uncertainty`（含两处 `src`） |
| K3 | 材料两处数值矛盾 | 首见优先，两个 `src` 并列 | **不取平均、不择优、不静默改写** | `uncertainty` |
| K4 | 材料为空 / 缺实体 / 缺数据 | 用可用材料继续；计数如实为 0 | 面板保留结构，不填填充句 | `content_summary` / `uncertainty` |
| K5 | 材料非 UTF-8 或为二进制 | 替换字符读取 / 跳过二进制 | 乱码段仅作背景，不进数值 | `warnings` / `content.notes` |
| K6 | 元素无 `src` 却想上画布 | **拒绝上画布**（spec_lint 硬检查） | 改放进图注或备注 | `result.spec_lint.problems` |

#### 3.2 M2 组：两道 lint 门（K7–K10）

| # | 触发 | 动作 | 失败时的降级 | 记录位点 |
|-|-|-|-|-|
| K7 | 方案 `four_elements` 有空项 | 补一句话说明后重跑方案 lint | 补不出来 → 该面板只放结构不放编造结论 | `result.plan.lint` |
| K8 | 方案/规格 lint 报 problems | 先修 plan/spec；`main.py --plan` 内嵌同一 lint | 属硬性限制则记录后继续，`status` 降 `partial` | `result.spec_lint` |
| K9 | 图例值与画面数值不一致 | 由 `spec_lint` 拦下，重算编码 | 无法一致则该编码项撤下画布 | `result.spec_lint` |
| K10 | 画布尺寸超限（<600 或 >4000） | 由 lint 夹紧到区间并记录 | 夹紧仍溢出则该面板缩减内容 | `spec_lint.problems` |

#### 3.3 M3 组：交付态一致性（K11–K14）

| # | 触发 | 动作 | 失败时的降级 | 记录位点 |
|-|-|-|-|-|
| K11 | 契约字段缺真实值 | 按 `""`/`[]`/`false`/`{}` 回显 | **禁止 null**（null 视为契约缺口） | `check_contract.py` exit 0 |
| K12 | 契约键与信封保留键冲突 | 顶层留信封值，原值进 `output_contract_echo` | 正常为 `{}` | `result.output_contract_echo` |
| K13 | 产物缺失/无效（SVG 不良构、PNG 无效） | `status=failed` + **exit 2**；已写产物保留 | 不允许"图没出来却报 success" | `audit.checks` / stderr |
| K14 | 同输入重跑结构漂移 | 排查时间戳/随机数进图面 | 未修正前在结果中声明不稳定 | `audit.determinism_probe` |

#### 3.4 复用与环境组（K15–K16）

| # | 触发 | 动作 | 失败时的降级 | 记录位点 |
|-|-|-|-|-|
| K15 | 字体缺失 / 后端缺失 / PDF 不可用 | 字体候选探测 → 后端链 matplotlib→Pillow→纯 Python PNG；PDF 标 `present:false` + `reason` | SVG `<text>` 始终为真文字，可编辑性不受影响 | `render_log.json` |
| K16 | 想改图层/加元素类型/加指标 | 先登记规范（`layer-naming.md` / `GAIN-PROTOCOL.md` §3），再改脚本，最后在 `TEST.md` 留一条真实数字 | 只改一处视为未完成 | 三处一致 |

规则完整矩阵（检测点、验证命令、受害指标）见 [`references/failure-modes.md`](references/failure-modes.md)。

### 4. 交付物与契约

| 产物 | 说明 |
|-|-|
| `<case_id>_graphical_abstract.svg` | 可编辑分层源：7 层 `layer:*`、真 `<text>`、`data-src`/`data-role`/`data-panel` |
| `<case_id>_graphical_abstract.png` / `.pdf` | 预览（后端与字体如实记录；PDF 不可用则标原因） |
| `result.json` | **唯一评分产物**：信封 18 键 ∪ 案例 `output_contract` 全字段，四形态回显、禁 null |
| `spec.json` / `content.json` | 图面规格 / 规范化抽取（同一几何，供再编辑与评审） |
| `audit.json` / `render_log.json` | 结构化自查与渲染日志 |

字段级契约见 [`references/OUTPUT_CONTRACT.md`](references/OUTPUT_CONTRACT.md)（**字段名不得改动**）。

### 5. 交付前自查（按机制分组）

**M1**
- [ ] 抽查 ≥3 个元素：`data-src` 能在材料中定位
- [ ] `audit.entity_coverage.missing` 与 `audit.encoding_consistency.missing_from_canvas` 均为空
- [ ] `audit.missing_values` 为空，或非空但已在 `uncertainty` 说明

**M2**
- [ ] 方案 lint 通过（exit 0）；`result.plan.lint.valid=true`
- [ ] 规格 lint 通过；`result.spec_lint.valid=true`（否则 `status` 不得为 success）

**M3**
- [ ] `python "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json --case <case.json>` **exit 0**
- [ ] `result.json` 无 null；`deliverables[].path` 均为相对路径且文件真实存在
- [ ] `status` 与 `audit.checks` 一致（PNG 无效即不得 success）
- [ ] 同输入重跑 `determinism_probe.spec_sha16` 一致

**复用**
- [ ] 若改过图层/指标：规范、脚本、`TEST.md` 三处已同步（K16）

### 6. 复用（三步拿走）

```bash
# ① 换成你自己的案例：复制 examples/case.json，改 entities/relations/data/figure_constraints，
#    数值必须同时出现在你的材料文件里（M1 的前置条件）
# ② 跑一遍：方案骨架 → 方案 lint → 出图 → 契约自查
python "$SKILL_DIR/scripts/scaffold.py" --case /path/to/your/case.json --out /tmp/plan.json
python "$SKILL_DIR/scripts/spec_lint.py" --lint-plan --plan /tmp/plan.json
python "$SKILL_DIR/scripts/main.py"     --case /path/to/your/case.json --plan /tmp/plan.json --out /tmp/your-out
python "$SKILL_DIR/scripts/check_contract.py" --result /tmp/your-out/result.json --case /path/to/your/case.json
# ③ 复核：用同一把尺子量你的产物（可与自己未用本 Skill 的做法对照）
python "$SKILL_DIR/scripts/gain_harness.py" --out /tmp/your-out --case /path/to/your/case.json \
       --material /path/to/your/material.md --label mine
```

资产清单（图层规约、面板模板、色板与字号、契约与硬性门、校验清单、题集与金标准协议）
见 [`references/REUSE-KIT.md`](references/REUSE-KIT.md)。

### 7. 五维落点（速查）

| 维度 | 分 | 落点 |
|-|-|-|
| 实际效果 40 | | 四要素单页流水线 + 可编辑分层 SVG/PNG/PDF；M1 使每个元素可回查，M3 使产物可复核 |
| 使用增益 25 | | M2 把错误拦在绘制前（省整张重画）；`scaffold.py` 一步出方案；对照协议与测量器（`references/GAIN-PROTOCOL.md`） |
| 创新增益 15 | | 三个机制 + 反事实说明 + 机器判据（`references/MECHANISM.md`）；契约四形态回显；图层命名可校验 |
| 可靠体验 10 | | K1–K16 + `references/failure-modes.md` 完整矩阵（含退出码语义与受害指标） |
| 生态贡献 10 | | `references/REUSE-KIT.md` 资产清单 + 三步移植 + 题集/金标准协议；纯文本包便于 fork |

### 8. 目录结构

```
<skill root>/
  SKILL.md                      三个机制 + 机制→脚本→证据链 + K1–K16 + 复用三步
  README.md                     使用说明 / 参数 / 依赖 / **可复用资产清单与复用步骤** / 维护
  TEST.md                       本地实测（含机制验证与对照链真实数字）
  GITHUB_URL.txt                公开作品链接
  references/
    OUTPUT_CONTRACT.md          result.json 契约（唯一评分产物；字段名不改）
    RUBRIC_MAP.md               五维 → 机制 → 复算命令
    MECHANISM.md                ★ 三个机制的反事实推理、边界与实测证据
    REUSE-KIT.md                ★ 可复用资产清单 / 题集与金标准协议 / 校验清单
    GAIN-PROTOCOL.md            对照协议 + 指标口径 + 真实对照记录 + 局限
    failure-modes.md            K1–K16 的检测点、处置、受害指标、验证命令
    plan-schema.md              设计方案 schema（方案先行）
    ga-four-elements.md         四要素内容知识
    layer-naming.md             SVG 分层与溯源属性规范
    TEMPLATE.md                 面板模板与视觉通道映射
  assets/                       纯文本资产三件套
  scripts/                      10 个流水线脚本（未改动）+ gain_harness.py（只读测量器）
  examples/                     最小示例（合成案例）与其实跑产物
```

### 9. 限制（如实声明）

- 三个机制解决的是**可核验性**，不保证图"好看"，也不代替领域科学判断；
- 抽取依赖材料文本结构，复杂表格/多图材料需 Agent 复核；
- 渲染后端可能降级；降级后 PNG 文字可能为占位框（SVG 的 `<text>` 不受影响）；
- 对照记录是单案例、单机的可复现观测，不构成统计显著性结论；
- `examples/` 为合成示例，与平台正式案例无关；正式案例由平台挂载运行。
