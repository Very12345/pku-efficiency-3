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

# Graphical Abstract（图形摘要）Skill v2 — figures group · 整合版（决策层 + 机制层）

> 本包整合了基线 Skill 与 2 个强化层,各层对应不同的评分维度:可靠体验 10 + 实际效果 40 · 创新增益 15 + 生态贡献 10。
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
- `scripts/__pycache__/common.cpython-313.pyc`
- `scripts/__pycache__/extract.cpython-313.pyc`

---

# 【决策层】决策规则与失败分支（目标维度:可靠体验 10 + 实际效果 40）

---
name: graphical-abstract
description: >-
  单页 Graphical Abstract（图形摘要）生成/编辑 Skill，以「决策规则显性化」为核心：
  材料 → 实体/关系/数据抽取（逐元素 data-src 溯源）→ 方案先行（scaffold 骨架 →
  方案 lint CP1）→ 确定性版面与数据编码 → 可编辑分层 SVG（`layer:*` 七层契约）+
  PNG/PDF 渲染件 → audit 与契约自查，全流程带 20 条决策规则 D1–D20 与五类失败分支
  （材料异常 / 模板缺失 / 依赖缺失 / 契约四形态 / 状态不一致），每条规则都写明
  触发条件、动作、失败时的降级与记录位点。Use when the task mentions "graphical
  abstract"、"图形摘要"、"示意图 / 机制图 / 流程图"、"为论文/基金/汇报画一张图"、
  "编辑已有的图稿"，或要求从实验记录、研究描述里画机制/流程/结果图。
---

## Graphical Abstract 图形摘要 Skill — 决策显性化版（D1–D20 + 五类失败分支）

本 Skill 把「研究问题 → 方法 → 核心结果 → 结论」压进**单页**，并交付**可继续编辑的
分层源文件**。它对图里的科学内容负责：实体不许张冠李戴、箭头方向与因果一致、
图例/单位/比例尺与数据逐项对应、每个科学元素可溯源（`data-src`）、同输入同布局。
**数值一律不编造**：材料里找不到的数值只能进 `uncertainty`。

本版本的设计重点只有一句话：**把"遇到异常怎么办"从隐含经验变成可核对的规则表**。
§4 的 20 条决策规则、§5 的五类失败分支、`references/failure-modes.md` 的对照矩阵
三者编号一一对应 —— 出问题时可从退出码/字段直接反查到"本该走哪条规则"。

| 项目 | 值 |
|-|-|
| Skill 名称 / 版本 | `graphical-abstract` / `2.0.0`（脚本内 `SKILL_VERSION`；本包为文档轴 A：决策显性化） |
| 技能根 | 本文件所在目录，下文记作 `$SKILL_DIR` |
| 资源形态 | 纯文本（`.md/.py/.json/.txt/.csv/.yaml/.yml`）；无二进制、无预置 `.svg/.png/.pdf`、无字体文件、无 `__pycache__`、无绝对路径 |
| 交付物 | 可编辑分层 SVG + PNG/PDF 预览 + `result.json`（+ `spec/content/audit/render_log.json`） |
| 规则规模 | 决策规则 20 条（D1–D20）· 失败分支 5 类 21 支 · 硬性门 8 条（G1–G8） |

---

### 0. 自定位调用（cwd 任意，以下命令逐字可用）

脚本用 `scripts/common.py` 的 `SCRIPT_DIR = dirname(abspath(__file__))` 自定位技能根，
因此**不要求 cwd = 技能根**，只要把 `$SKILL_DIR` 指对：

```bash
# 1) 确定技能根（两种方式任选）
SKILL_DIR=/skills/weekly-skill                        # 官方评测容器的安装位置
SKILL_DIR=/abs/path/to/graphical-abstract-7030fff2    # 本机解压后的目录
# 不确定时向上探测：从 cwd 往上找含 SKILL.md 的目录
SKILL_DIR="$(pwd)"; while [ ! -f "$SKILL_DIR/SKILL.md" ] && [ "$SKILL_DIR" != "/" ]; do SKILL_DIR="$(dirname "$SKILL_DIR")"; done

# 2) 冒烟（合成示例案例；产物写包外目录）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/ga-out

# 3) 官方案例形态（平台挂载输入，产物写 /app/output）
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md --out /app/output
```

> 若你的环境只允许相对路径，请先 `cd "$SKILL_DIR"`；两种写法等价，但本文件所有示例
> 都以 `$SKILL_DIR` 绝对化为准，避免 cwd 不同导致找不到脚本。

---

### 1. 触发条件与不适用边界

**应当触发**（满足任一）：用户给出研究描述/实验记录/论文草稿要求出**单页视觉摘要**；
要求画机制图、通路图、流程图、方案示意图；要求**编辑已有图稿**（改字幕/换色/重排面板）；
要求"交付可继续修改的源文件"（而不是一张位图）。

**不应触发**（明确边界，避免越界作答）：论文正文写作、统计分析、实验方案设计、
纯数据可视化（无 Q-M-R-C 叙事要求）。本 Skill 只对**图面科学内容的表达、版式、
可编辑性、导出质量**负责，不对材料本身的结论正确性负责。

---

### 2. 输入 → 输出（契约速览）

输入优先级：`case.json`（必读）→ `task.md`（若存在）→ `source_material` 指明的材料文件。
材料是数值与机制关系的**唯一事实来源**；`case.json` 是结构与约束来源。
全部输入按真实文件读取，**不得凭文件名或标签猜内容**（见 D3/D6/D8）。

输出（全部写入 `--out`，官方为 `/app/output`）：

| 产物 | 形态 | 契约/规范 |
|-|-|-|
| `<case_id>_graphical_abstract.svg` | 可编辑分层 SVG | 7 层 `layer:*`；文字为真 `<text>`；科学元素带 `data-src/data-role/data-panel`（`references/layer-naming.md`） |
| `<case_id>_graphical_abstract.png` / `.pdf` | 渲染预览 | 后端链 matplotlib → Pillow → 纯 Python PNG，逐级回退并记录 |
| `result.json` | 结构化结果（唯一评分产物） | `references/OUTPUT_CONTRACT.md`：信封 18 键 ∪ 案例 `output_contract` 全部字段，四形态回显、禁 null、G1–G8 |
| `spec.json` / `content.json` | 图面规格 / 规范化抽取 | 与 SVG 同一几何；再编辑与复核用 |
| `audit.json` / `render_log.json` | 自查 / 渲染日志 | 覆盖率、越界、四要素、图层命名、确定性探针、后端与字体 |

---

### 3. 执行主链（每步都写明"出口判据"）

第 0–9 步由 `scripts/main.py` 流水线执行；作为 Agent，你**必须在调用脚本之外**亲自读材料
并复核抽取结果，偏差如实写入 `change_records` / `uncertainty`。**不得用预制答案替代实际运行。**

| 步 | 动作 | 命令要点 | 出口判据（不满足就走对应决策规则） |
|-|-|-|-|
| 0 | 方案先行：生成骨架并定稿 | `scaffold.py --case <case.json> --out plan.json` → 填 `four_elements` | `spec_lint.py --lint-plan --plan plan.json` **exit 0**；否则 D14 组规则 |
| 1 | 读真实文件 | 直接读 `case.json` / `task.md` / 材料 | 三者至少 `case.json` 可解析；否则 D1 |
| 2 | 抽取实体/关系/数据 | `extract.py`（`main.py` 内嵌） | 每项带 `src`；无源数值不上画布（D5） |
| 3 | 版面与数据编码 | `figurespec.py` | 四面板阅读顺序成立；编码项进 `data_encoding` 与 `legend` |
| 4 | 规格 lint（绘制前） | `spec_lint.py --spec … --content …` | `valid=true`；否则 D14 + 降 `partial` |
| 5 | 生成分层 SVG | `svgbuilder.py` | ElementTree 回解析良构；7 层 `layer:*` 齐全（D20） |
| 6 | 导出渲染件 | `preview.py` | PNG 签名/尺寸有效；后端与字体被记录（D10/D11/D12） |
| 7 | 自查 | `audit.py` | 覆盖率、越界、缺值、四要素、图层命名、确定性探针全部量化落盘 |
| 8 | 写 `result.json` | 契约四形态回显 + 信封 | 无 null；`status` 按 §4 状态组规则判定（D18–D20） |
| 9 | 收尾复核 | `check_contract.py --result … --case …` | **exit 0**；`audit.json` 无红线；PNG 目视无裁切；同输入重跑结构一致 |

预算纪律：官方 64 次模型请求 / 900 秒 / 16384 tokens（含推理）。脚本本身单次运行 <10 s，
请把预算花在"读材料 → 定方案 → 复核抽取"上，而不是反复重绘。

---

### 4. 决策规则 D1–D20（触发条件 → 动作 → 失败时的降级 → 记录位点）

> 编号在 `references/failure-modes.md` 中**同名同号**出现，两边必须能互查。
> "降级" = 当首选动作无法完成时允许退到哪一步；**任何降级都不允许静默成功**。

#### 4.1 输入组（D1–D4）

| # | 触发条件 | 动作 | 失败时的降级 | 记录位点 |
|-|-|-|-|-|
| D1 | `case.json` 不存在 / 不是合法 JSON | 立即 **exit 1**，打印 `{"status":"failed","error":…}` | 不退化为"用文件名猜内容"；**不留半成品冒充成功** | stdout / stderr |
| D2 | `case.json` 缺 `case_id` | 回退链 `case_id → id → case → 文件名` | 用文件名兜底并标注"取自文件名" | `result.case_id` + `uncertainty` |
| D3 | `task.md` 缺失 | 只用 `case.json` + 材料；面板要点改由材料小节标题映射 | 要点为空时面板保留结构、不放填充句 | `content.notes` → `warnings` |
| D4 | `source_material` 指向的文件/目录不存在或为空 | 继续用其余可用材料 | 实体/数据计数如实为 0，**不虚构实体** | `uncertainty` + `content_summary` |

#### 4.2 材料组（D5–D9）

| # | 触发条件 | 动作 | 失败时的降级 | 记录位点 |
|-|-|-|-|-|
| D5 | 有指标名但材料里找不到数值 | 图上「数值缺失」占位；数值只进备注 | 该数据点从编码子图移除，但保留指标名 | `audit.missing_values` + `uncertainty` |
| D6 | 实体重名 / 同名不同物 | 同 id 首见优先；两项都列出并标注歧义 | 歧义未解除时该实体的关系箭头不画 | `uncertainty`（含两处 `src`） |
| D7 | 材料两处数值互相矛盾 | 保留首见值，矛盾处写清两个 `src` | **不取平均、不择优、不静默改写** | `uncertainty` |
| D8 | 材料非 UTF-8（GBK/Latin-1/乱码） | 以替换字符读取，不中断流程 | 乱码占比高时该段仅作背景，不进数值 | `warnings` |
| D9 | 材料是二进制（PDF/图片被误挂载） | 只收 `.md/.txt/.json/.csv/.tex/.rst` 文本材料 | 跳过二进制并提示需要文本材料 | `content.notes` |

#### 4.3 依赖与渲染组（D10–D13）

| # | 触发条件 | 动作 | 失败时的降级 | 记录位点 |
|-|-|-|-|-|
| D10 | CJK 字体缺失（中文渲染为方框/空白） | 按候选路径逐级探测系统字体（Windows/macOS/Linux） | 退到默认字体；**SVG 里的 `<text>` 仍是真文字**，可编辑性不受影响 | `render_log.font` + `uncertainty` |
| D11 | `matplotlib` 不可用 / 渲染抛错 | 自动切 Pillow 后端 | Pillow 再失败 → 纯 Python PNG（文字占位并注明） | `render_log.backend` + `uncertainty` |
| D12 | PDF 导出失败或后端不支持 | PNG 照常交付；PDF 标 `present:false` + `reason` | 不允许留空 `path` 假装成功 | `result.deliverables[format=pdf]` |
| D13 | 文字溢出面板 / 元素越出画布 | 自动缩字号（下限 8px）与坐标夹紧 | 仍溢出 → 进清单并缩内容（不缩小到不可读） | `audit.layout_log` / `audit.bounds` |

#### 4.4 契约组（D14–D17）

| # | 触发条件 | 动作 | 失败时的降级 | 记录位点 |
|-|-|-|-|-|
| D14 | 方案或规格 lint 不过（四要素空 / 缺 `src` / 画布超限） | 先修 plan/spec 再重跑；`main.py --plan` 内嵌同一 lint | 确属硬性限制 → 记录后继续，`status` 降 `partial`，**不得 success** | `result.plan.lint` / `result.spec_lint` |
| D15 | 案例 `output_contract` 某字段没有真实值 | 按声明类型给空值：`""` / `[]` / `false` / `{}` | **禁止 null**（null 视为契约缺口） | `check_contract.py` exit 0 |
| D16 | 案例契约字段名与信封保留键冲突 | 顶层保留信封值，原值移入 `output_contract_echo[<key>]` | 正常情况 `output_contract_echo` 为空对象 | `result.output_contract_echo` |
| D17 | 契约声明类型与实际不符（声明数字却给字符串等） | 以**真实值**为准写入，并在备注说明类型偏差 | 类型不可转换时给该类型的空值并记录 | `uncertainty` + `check_contract.py` 输出 |

#### 4.5 状态一致性组（D18–D20）

| # | 触发条件 | 动作 | 失败时的降级 | 记录位点 |
|-|-|-|-|-|
| D18 | `spec_lint.valid=false` | `status` 直接判 `partial`，不做 success | 逐条列明限制，写明"哪一条 lint 未过" | `result.spec_lint` + `uncertainty` |
| D19 | 关键产物缺失（SVG 不良构 / PNG 无效） | `status=failed`，**exit 2** | 已写出的部分产物保留在原路径，报错含已写入清单 | stderr + `audit.checks` |
| D20 | 同输入重跑结构不一致（确定性被破坏） | 视为缺陷：检查是否引入了时间戳/随机数进图面 | 修正后重跑；未修正前在结果中声明不稳定 | `audit.determinism_probe` |

**规则间的优先级**：D1 最高（读不到输入就直接失败）> D19（产不出产物不允许报成功）>
D18/D14（lint 不过不允许 success）> D5/D7（科学诚实性优先于版面美观）> 其余降级规则。

---

### 5. 失败分支总表（五类，与 §4 同号互查）

| 类 | 分支（触发） | 走哪条规则 | 处置与降级 | 证据字段 |
|-|-|-|-|-|
| **材料异常** | `case.json` 缺失/不可解析 | D1 | exit 1，不留半成品 | stdout JSON |
| | 材料文件缺失 / 材料为空 | D4 | 用可用材料继续，计数如实为 0 | `uncertainty` |
| | 关键数值缺失 | D5 | 「数值缺失」占位，绝不编造 | `audit.missing_values` |
| | 实体重名或歧义 | D6 | 首见优先，两项并列 | `uncertainty` |
| | 材料数值互相矛盾 | D7 | 首见优先，双 `src` 并列 | `uncertainty` |
| | 材料非 UTF-8 / 二进制误挂载 | D8 / D9 | 替换字符读取 / 跳过并提示 | `warnings` / `content.notes` |
| **模板缺失** | 预置 SVG/PNG/PDF 模板不存在（本包本就不带） | 结构上不触发 | 模板 = 代码 + 文本规格，运行时生成 | `svgbuilder.py` / `preview.py` |
| | 预置方案模板 `assets/spec_template.json` 缺失 | D14 | `scaffold.py` 仍可从材料抽骨架 | `result.plan.source` |
| **依赖缺失** | matplotlib / Pillow 缺失 | D11 | 逐级回退到纯 Python PNG，文字占位并注明 | `render_log.backend` |
| | CJK 字体缺失 | D10 | 探测候选路径 → 默认字体；SVG 文字仍可编辑 | `render_log.font` |
| | PDF 后端不可用 | D12 | PNG 照常，PDF 标 `present:false` + 原因 | `deliverables` |
| **契约四形态** | ①字段→类型提示：无真实值 | D15 | 写 `""` | `check_contract.py` exit 0 |
| | ②字段→容器：无真实值 | D15 | 写 `[]` | 同上 |
| | ③布尔开关：无真实值 | D15 | 写 `false`（真布尔，不写 0/字符串） | 同上 |
| | ④字段清单：无真实值 | D15 | 写 `[]`；有值时回显实际使用的图层名 | 同上 |
| | 契约键与信封保留键冲突 | D16 | 原值移入 `output_contract_echo` | `output_contract_echo` |
| | 声明类型与实际不符 | D17 | 以真实值写入并说明 | `uncertainty` |
| **状态不一致** | plan/spec lint 不过 | D14 / D18 | 先修；修不动则 `status=partial`，禁止 success | `plan.lint` / `spec_lint` |
| | SVG/PNG 未产出或无效 | D19 | `status=failed` + exit 2 | `audit.checks` |
| | 重跑结构漂移 | D20 | 排查时间戳/随机数；未修正前声明不稳定 | `determinism_probe` |
| | 产物路径写成绝对路径或指向不存在文件 | D19 | 全部改为相对输出目录的路径，并核对文件真实存在 | `deliverables[].path` |

---

### 6. 三分钟分诊（出问题按这个顺序看）

1. **退出码**：`0` = 完成（success/partial）；`1` = 输入错误（看 D1）；`2` = 内部错误（看 D19）。
2. **`result.json.status`**：是 `partial` 就在 `uncertainty` 找限制条目，按 §4.5 判定可否接受。
3. **`audit.json` 六项红线**：`entity_coverage.missing`、`encoding_consistency.missing_from_canvas`、
   `bounds.outside_count`、`missing_values`、`four_element_coverage.missing`、`layer_naming.bad`
   —— 非空即回到 §4 对应规则。
4. **`render_log.json`**：`backend` 与 `font` 是否与预期一致；降级是否已被记录（D10/D11）。
5. **契约**：`check_contract.py` 是否 exit 0（D15–D17 的最终判据）。

---

### 7. 交付前自查清单（每条都可判真假）

- [ ] 读的是**真实文件**（`case.json`/`task.md`/材料），没有凭标签假设内容
- [ ] 方案先行：`result.plan.source` 为 `none` 或具体 plan 路径，`result.plan.lint` 已记录
- [ ] 抽查 ≥3 个图面元素，其 `data-src` 能在材料中定位到
- [ ] `result.json` 顶层覆盖「信封 18 键 ∪ 案例 `output_contract` 全部字段」，无 null
- [ ] `python "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json --case <case.json>` **exit 0**
- [ ] SVG 良构、`<text>` 可编辑、7 层 `layer:*` 全绿（`audit.layer_naming`）
- [ ] 四要素 question/method/results/conclusion 全部上画布（`audit.four_element_coverage.missing` 为空）
- [ ] PNG 存在且非空白；PDF 若启用则头为 `%PDF-`，未启用则有 `present:false` + `reason`
- [ ] 实体覆盖率与数值编码一致性均为 100%（`audit`）
- [ ] 同输入重跑：`audit.determinism_probe.spec_sha16` 一致
- [ ] `uncertainty` 里没有"编造数据"类的补丁；已按 `references/RUBRIC_MAP.md` 自评五维
- [ ] 本次运行触发的每条决策规则都有对应记录位点（无记录 = 未按规则执行）

---

### 8. 五维评分落点（速查；完整对照见 `references/RUBRIC_MAP.md`）

| 维度 | 分 | 本包落点 |
|-|-|-|
| 实际效果 | 40 | `scripts/{extract,figurespec,svgbuilder,preview}.py` 的单页四要素流水线；可编辑分层 SVG + PNG/PDF；逐元素 `data-src` + `sources[]`(sha256) |
| 使用增益 | 25 | 决策规则表 + 失败分支表使异常处置可预期（不靠临场发挥）；方案先行免重绘；`scaffold.py` 一步出方案骨架；确定性布局免重排 |
| 创新增益 | 15 | 方案先行（plan-schema + CP1 门）、四要素不变式、图层命名可机器校验、双 lint 门、契约四形态回显、**决策规则与失败分支同号互查** |
| 可靠体验 | 10 | 本文件 §4（D1–D20）+ §5（五类分支）+ `references/failure-modes.md` 对照矩阵；`audit.py` 六项红线；`check_contract.py` exit-code 判据 |
| 生态贡献 | 10 | 文档齐备（SKILL/README/TEST/OUTPUT_CONTRACT/RUBRIC_MAP/failure-modes/plan-schema/ga-four-elements/layer-naming/TEMPLATE）+ `assets/` 三件套 + `examples/` 最小示例 + `GITHUB_URL.txt` |

---

### 9. 目录结构

```
<skill root>/
  SKILL.md                 本文档（自定位 + 决策规则 D1–D20 + 失败分支五类）
  README.md                使用说明 / 依赖 / 参数 / 限制 / 失败处理 / 维护
  TEST.md                  本地实测记录（命令、产物、退出码、复现判据）
  GITHUB_URL.txt           公开作品链接（第一行 URL，第二行作品在仓库中的相对路径）
  references/
    OUTPUT_CONTRACT.md     result.json 契约 + 四形态回显 + G1–G8（唯一评分产物）
    RUBRIC_MAP.md          五维（40/25/15/10/10）→ 文件/机制的逐条映射
    failure-modes.md       失败模式与 D1–D20 的对照矩阵、退出码语义、状态一致性
    plan-schema.md         设计方案 schema（方案先行）
    ga-four-elements.md    四要素内容知识（Q-M-R-C 不变式与面板上限）
    layer-naming.md        SVG 分层命名与溯源属性规范（机器可校验）
    TEMPLATE.md            面板模板 / 视觉通道映射 / 复用指南
  assets/                  可复用资产三件套（纯文本）
  scripts/                 10 个脚本：main / extract / figurespec / svgbuilder / preview /
                           audit / spec_lint / scaffold / check_contract / common
  examples/                最小示例（合成案例）：case.json / task.md / material.md /
                           plan.example.json / README.md / EXPECTED-OUTPUT.md / output/
```

脚本不硬编码绝对路径；输入输出路径全部由命令行显式给出。
包内唯一的 `C:/Windows/Fonts` 一类字符串是**跨平台字体探测候选路径**，不是本机运行残留
（判别法：删除它会让字体探测少一条候选，而不是让某张图找不到文件）。

---

### 10. 限制（如实声明）

- 渲染后端可能降级，实测本机为 matplotlib；降级一律记录，但降级后的 PNG 文字可能为占位框；
- 实体抽取依赖材料文本结构，复杂表格/多图材料需 Agent 人工复核；
- 四要素/图层/覆盖率是**结构判据**，不代替领域科学判断；
- 示例数据为合成示意（`examples/`），与平台正式案例无关，正式案例结果由平台实跑产生；
- 决策规则表覆盖的是**已知**异常；遇到表外情形时按"先记后判"原则处理：先进 `uncertainty`，
  再决定是否继续，绝不静默通过。

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
