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

# Graphical Abstract 图形摘要 Skill — 增益可验证版

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

## 1. 快速调用（cwd 任意；命令逐字可用）

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

## 2. 可比性设计（为什么"对照"能成立）

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

## 3. 可测指标（口径固定，全部由测量器复算）

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

## 4. 执行步骤（每步都留下可测量的证据）

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

## 5. 决策速查表（R1–R14：情形 → 动作 → 记录位点）

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

## 6. 增益记录（摘要；原始记录与复算命令见 GAIN-PROTOCOL）

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

## 7. 交付前自查清单

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

## 8. 五维落点（速查）

| 维度 | 分 | 本包落点 |
|-|-|-|
| 实际效果 40 | | 四要素单页流水线 + 可编辑分层 SVG/PNG/PDF；逐元素溯源；`audit` 量化核验 |
| 使用增益 25 | | **本轴主强化**：`references/GAIN-PROTOCOL.md`（可比条件 + 指标口径 + 真实对照记录）+ `scripts/gain_harness.py`（第三方可复算）；免重绘/免搬运的机制 |
| 创新增益 15 | | 方案先行 + 双 lint 门 + 图层命名契约 + 契约四形态回显；**把"增益"本身做成可复算协议** |
| 可靠体验 10 | | R1–R14 速查 + `references/failure-modes.md`（退出码/降级/证据）+ `audit` 红线 + 两个 exit-code 自查器 |
| 生态贡献 10 | | 文档齐备 + 资产三件套 + 最小示例 + 测量器可被任何项目直接拿去做对照 |

---

## 9. 目录结构

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

## 10. 限制（如实声明）

- 本地对照的条件 B 是**最小复现脚本**而非真实无 Skill 的 LLM Agent；它衡量的是
  "机制层面的差距"，平台官方的白板对照才是正式依据；
- 指标是**结构与文本级**判据（层数、属性数、字符串可定位性），不判断图的美观与
  领域结论正确性；
- 渲染后端可能降级；降级后 PNG 文字可能为占位框，但 SVG 的 `<text>` 仍可编辑；
- `examples/` 为合成示例，与平台正式案例无关；平台正式案例由组织方挂载运行。
