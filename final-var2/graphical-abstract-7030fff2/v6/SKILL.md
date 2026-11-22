---
name: graphical-abstract
description: >-
  把研究材料做成单页 Graphical Abstract（图形摘要）的全维 Skill：输入侧做 source-bound 抽取
  （实体/关系/数据逐元素 data-src 溯源，禁编造数值），执行侧走「方案先行 → 双 lint 门 →
  确定性版面 → 可编辑分层 SVG（layer:* 七层契约）+ PNG/PDF 渲染件 → audit → 契约回显」，
  失败侧给 20 条决策规则、四形态注入演练与实测矩阵，增益侧给可复算的对照协议与只读测量器，
  机制侧写清三个独特机制的反事实与失效条件，复用侧给资产清单、三步移植与可复跑题集
  （三个不同题材的合成案例）。Use when the task says "graphical abstract"、"图形摘要"、
  "示意图 / 机制图 / 通路图 / 流程图 / 图稿"、"为论文、基金或汇报画一张可编辑的图"、
  "编辑已有的图稿"，或需要同时验证出图质量、失败行为与增益幅度。
---

# Graphical Abstract 图形摘要 Skill — 全维合并版（输入 → 执行 → 失败 → 增益 → 机制 → 复用）

一页讲完**研究问题 → 方法 → 核心结果 → 结论**，交付**可继续编辑的分层源文件**（不是位图截图）、
PNG/PDF 预览与字段完整的 `result.json`（含来源、状态、不确定性、变更记录）。
**数值不编造**：材料里定位不到的数值只进 `uncertainty` 并以「数值缺失」占位。

本包是同一 Skill 五条轴的**并集**，每一节都指向对应 reference；五条轴各自有实测记录，合并后不互相削弱：

| 轴 | 关注点 | 落到哪个 reference |
|-|-|-|
| A 决策显性化 | 20 条决策规则 + 五类失败分支，出问题可反查 | [`references/failure-modes.md`](references/failure-modes.md)（§3 互查表） |
| B 增益可验证 | 与"不加载 Skill 的基础做法"的公平对照 + 只读测量器 | [`references/GAIN-PROTOCOL.md`](references/GAIN-PROTOCOL.md)、`scripts/gain_harness.py` |
| C 机制与复用 | 三个独特机制的反事实与边界 + 资产清单/三步移植 | [`references/MECHANISM.md`](references/MECHANISM.md)、[`references/REUSE-KIT.md`](references/REUSE-KIT.md) |
| D 失败注入 | 四形态 23 条注入真跑 + 修复前后实测矩阵 | [`references/FAULT-MATRIX.md`](references/FAULT-MATRIX.md)、`scripts/fault_inject.py` |
| E 多案例泛化 | 三个跨题材案例 + 逐案可接受区间 + 失效边界 | [`references/CASE-SET.md`](references/CASE-SET.md) |

| 项目 | 值 |
|-|-|
| Skill 名称 / 版本 | `graphical-abstract` / `2.0.0`（脚本内 `SKILL_VERSION`） |
| 技能根 | 本文件所在目录，下文记作 `$SKILL_DIR` |
| 资源形态 | 纯文本七种扩展名（`.md .py .json .txt .csv .yaml .yml`）；无二进制、无预置 `.svg/.png/.pdf`、无字体文件、无 `__pycache__`、无本机绝对路径；49 个文件 / 约 412 KB（上限 50 / 2MB） |
| 交付物 | 分层 SVG + PNG/PDF + `result.json`（+ `spec/content/audit/render_log.json`） |
| 实测状态 | 出图 exit 0 / 26 键；契约 exit 0；注入 23/23 全绿、0 静默失败；三案例 exit 0（两例 success，一例 partial 且限制留痕） |

---

## 0. 调用（cwd 任意；命令逐字可用）

脚本用 `scripts/common.py` 的 `SCRIPT_DIR = dirname(abspath(__file__))` 自定位技能根，
**不要求 cwd = 技能根**：

```bash
# 技能根（二者取一；不确定时向上探测含 SKILL.md 的目录）
SKILL_DIR=/skills/weekly-skill
SKILL_DIR=/abs/path/to/graphical-abstract-7030fff2

# 出图（L1 最小示例）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/ga-out

# 契约自查（exit 0 = 顶层覆盖「信封 18 键 ∪ 案例契约」且无 null）
python "$SKILL_DIR/scripts/check_contract.py" --result /tmp/ga-out/result.json --case "$SKILL_DIR/examples/case.json"

# 失败注入演练（23 条，真跑子进程，约 30 秒；判级 strict）
python "$SKILL_DIR/scripts/fault_inject.py" --out /tmp/ga-fi --fail-on strict

# 增益测量（只读，不产生任何图）
python "$SKILL_DIR/scripts/gain_harness.py" --out /tmp/ga-out --case "$SKILL_DIR/examples/case.json" \
       --material "$SKILL_DIR/examples/material.md" --label A-skill

# 官方案例形态（平台挂载输入，产物写 /app/output）
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md --out /app/output
```

---

## 1. 输入

| 输入 | 说明 |
|-|-|
| `case.json` | 必读。`case_id / title / task / source_material / entities / relations / data / figure_constraints / output_contract`（键名有同义回退链） |
| `task.md` | 任务说明；`# 问题/方法/结果/结论` 小节直接映射为面板要点 |
| 材料文件 | `source_material` 指明的 `.md/.txt/.json/.csv/.tex/.rst` **或 PDF**（走文本层；取不到文本层则跳过并记录） |
| `--plan plan.json` | 可选。设计方案：`scaffold.py` 出骨架 → Agent 定稿 `four_elements` → 方案 lint（CP1 门） |

**输入侧三条硬规则**：① 只读真实文件，绝不凭文件名/标签猜内容；② 每个上画布的元素带 `src`
（`文件:行` 或 `case.json[字段]`）；③ 材料中找不到源头的数值**不得上画布** —— 只进 `uncertainty`
并以「数值缺失」占位。

接口与字段契约：[`references/OUTPUT_CONTRACT.md`](references/OUTPUT_CONTRACT.md)（唯一评分产物，
字段块逐字保留）、[`references/plan-schema.md`](references/plan-schema.md)（设计方案 schema）、
[`references/ga-four-elements.md`](references/ga-four-elements.md)（Q-M-R-C 不变式）。

---

## 2. 执行

```bash
# 0 方案先行（推荐）：骨架 → 定稿 → 方案门
python "$SKILL_DIR/scripts/scaffold.py" --case <case.json> --out plan.json
python "$SKILL_DIR/scripts/spec_lint.py" --lint-plan --plan plan.json      # exit 0 才继续

# 1 主链：抽取 → 版面 → 规格门 → 分层 SVG → 渲染 → audit → result.json
python "$SKILL_DIR/scripts/main.py" --case <case.json> --plan plan.json --out <out>

# 2 规格门独立复核（与 main 内嵌同一函数）
python "$SKILL_DIR/scripts/spec_lint.py" --spec <out>/spec.json --content <out>/content.json

# 3 契约门（判据 = 退出码）
python "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json --case <case.json>
```

| 步骤 | 出口判据 |
|-|-|
| 方案门（CP1） | `spec_lint.py --lint-plan --plan …` **exit 0**；不过则按 D14 修方案，`status` 不得 success |
| 抽取 | 每个元素有 `src`；数值能在材料里定位 |
| 版面与编码 | 四列面板按「问题→方法→结果→结论」；`bar_length`/`color_scale`/`area`/`value_label` 与图例一一对应 |
| 规格门（CP1b） | `spec_lint.py --spec … --content …` **exit 0** |
| 交付 | SVG 良构（7 层 `layer:*` + 真 `<text>` + `data-src`）、PNG 有效、`result.json` 26 键、契约 exit 0 |
| 复跑 | 同输入两次 `audit.determinism_probe.spec_sha16` **逐字符一致** |

层名与溯源属性规范：[`references/layer-naming.md`](references/layer-naming.md)；
版面模板与视觉通道：[`references/TEMPLATE.md`](references/TEMPLATE.md)。

---

## 3. 失败

**四形态注入演练**（本包最强的新证据）：`scripts/fault_inject.py` 把输入 / 模板 / 依赖 / 契约
四类缺陷**真的造出来**，每次用子进程跑真实主流程，抓 `退出码 / status / uncertainty / 相关字段`，
逐条判定是否**静默失败**（进程报 success 而缺陷既没修掉也没记录）：

```bash
python "$SKILL_DIR/scripts/fault_inject.py" --out /tmp/ga-fi --fail-on strict   # 23/23 ok, 0 silent
python "$SKILL_DIR/scripts/fault_inject.py" --out /tmp/x --only dependency --verbose
```

| 类 | 注入手段 | 判据 | 用例 |
|-|-|-|-|
| 输入 | `--case` 不存在；case.json 截断；空 case；材料缺失；PDF 字节流；`entities` 类型错 | 该失败就 exit 1，该降级就 `partial` + `uncertainty` 点名 | F00–F06 |
| 模板 | `--plan` 缺失 / 非法 / 未定稿骨架 / 画布超界 / 关系无 `src` / 覆盖 constraints | 方案门不过 ⇒ `status` 不得 success；非法 JSON 要干净 exit 1 | F07–F12 |
| 依赖 | 假模块屏蔽 `matplotlib`/`PIL`/`pypdf`；`--out` 指向普通文件 | 逐级回退且如实记录；不许静默成功 | F13–F17 |
| 契约 | 字段声明 `null`；键冲突；类型不符；无契约；容器空值 | 禁 null（`""`/`[]`/`false`/`{}`）；冲突键进 `output_contract_echo` | F18–F22 |

**实测结论**：修复前 `ok 10 / mismatch 5 / silent 8` → 修复后 **23/23 `ok`、0 静默失败**。
修复全部为纯增量（`extract.py +100`、`main.py +41`、`figurespec.py +6`、`preview.py +7`，
删除行数 0），逐条点名与行数在
[`references/FAULT-MATRIX.md`](references/FAULT-MATRIX.md) §2。

**决策规则**（20 条，完整表见 [`references/failure-modes.md`](references/failure-modes.md) §3）：

| 组 | 规则 | 记录位点 |
|-|-|-|
| 输入 | D1 case 不可读 → exit 1；D2 缺 `case_id` → 回退链；D3 `task.md` 缺失；D4 材料缺失/为空 | stdout / `result.case_id` / `warnings` / `uncertainty` |
| 材料 | D5 数值缺失占位；D6 实体歧义首见优先；D7 数值矛盾并列两处 `src`；D8 非 UTF-8；D9 二进制/PDF | `audit.missing_values` / `uncertainty` |
| 依赖 | D10 字体探测回退；D11 渲染后端三级回退；D12 PDF 不可用 → `present:false` + reason；D13 溢出/越界 | `render_log.json` / `deliverables` / `audit.layout_log` |
| 契约 | D14 lint 不过先修、修不动降 `partial`；D15 禁 null；D16 键冲突进 echo；D17 类型不符以真实值为准 | `plan.lint` / `spec_lint` / `check_contract` / `output_contract_echo` |
| 状态 | D18 lint 不过不得 success；D19 产物无效 → `status=failed` + exit 2；D20 结构漂移排查时间戳 | `audit.checks` / `determinism_probe` |

**退出码**：`0` 完成（success/partial）；`1` 硬输入错误；`2` 环境或内部错误（输出目录不可用、
`status=failed`）。

---

## 4. 增益（可复算的对照，不是自述）

对照协议（条件 A = 加载本 Skill；B = 不加载 Skill 的基础做法；B+ = B 的最有利设置）与指标口径见
[`references/GAIN-PROTOCOL.md`](references/GAIN-PROTOCOL.md)；`scripts/gain_harness.py` 是只读测量器，
对**任意**输出目录复算同一组指标：

```bash
python "$SKILL_DIR/scripts/gain_harness.py" --out <out> --case <case.json> --material <material.md>
python "$SKILL_DIR/scripts/gain_harness.py" --compare <outA> <outB>     # 结构指纹对比
```

| 指标 | A（加载 Skill） | B（基础做法） | B+（B 最有利设置） |
|-|-|-|-|
| 分层数 / 真文字节点 | **7 层 / 61 个 `<text>`** | 0 / 0（全为字形引用） | 0 / 38 |
| 溯源覆盖率 | **0.903（56/62）** | 0 | 0 |
| 四要素覆盖 | **4/4** | 0/4 | 1/4 |
| 数值可定位率 | **14/16** | 0/0 | 7/15 |
| 契约 | **8/8，顶层 26 键** | 0/8，4 键 | 0/8，4 键 |
| 结构确定性 | 两次逐项一致 | 两次逐项一致 | 未测 |
| 单次墙钟 | 2.441 / 2.156 s | **1.707 / 1.514 s** | — |
| 达标返工步数 | **0** | 未达标（无 audit/render_log/spec、无 `data-src`、无分层） | 未达标 |

**三条对 A 不利、但必须一起读的观测**（原文见 GAIN-PROTOCOL §4.3）：
① **A 单次更慢**（多出抽取、双门 lint、图层化、audit 与契约回填的时间）—— 增益体现在**免返工
与可核验性**，不是单次速度；② **确定性不是 A 的独占优势**（B 也两次一致），A 的贡献是把复现性
做成可检查字段（`audit.determinism_probe`）；③ **A 的溯源覆盖率是 0.903 而不是 1.000**，
残差是关系组容器（子元素带 `data-src`、容器不带），这里按更严格口径记录、不取好看的数字。

---

## 5. 机制

三个独特机制、它们的反事实与失效条件见 [`references/MECHANISM.md`](references/MECHANISM.md)：

| 机制 | 一句话 | 没有它会怎样（反事实） | 执行者 / 证据 |
|-|-|-|-|
| **M1 来源挂接** | 每个科学元素带 `data-src`；材料里没有的数值不上画布 | 图能看但不可查；缺值会被"看起来合理"的数字填掉 | `extract.py`、`svgbuilder.py`、`audit.py`；`audit.entity_coverage`/`encoding_consistency`、`result.sources[]`(sha256) |
| **M2 双 lint 门** | 绘制前拦方案、绘制后拦规格，两道门都以退出码为判据 | 错误在"画完"后才发现，只能整张重画；缺要素/图例错位的图会被当成品交出 | `scaffold.py`、`spec_lint.py`（`--lint-plan` / `--spec`）；`result.plan.lint`、`result.spec_lint` |
| **M3 契约与状态一致性** | 四形态回显（禁 null）+ `status` 不得虚报 | 评分产物字段缺失或为 null，复核方无法判断可信度 | `main.py`、`check_contract.py`；顶层 26 键、`check_contract` exit 0、`status` 与 `audit.checks` 一致 |

机制之间的耦合：去掉 M1 ⇒ 溯源与数值门失效（`encoding_consistency` 全空）；去掉 M2 ⇒ 错误延后到
成品；去掉 M3 ⇒ 产物不可判定。**失效条件**（何时这些机制不管用）写在 MECHANISM §2④/§3④/§4④。

---

## 6. 复用

资产清单（含"复用前必须改什么"）、题集/金标准协议、发布前校验清单与三步移植见
[`references/REUSE-KIT.md`](references/REUSE-KIT.md)。最小三步：

```bash
# ① 换成你自己的案例：复制 examples/case.json，改 entities/relations/data/figure_constraints；
#    每个数值必须同时出现在你的材料文件里（M1 的前置条件）
# ② 跑一遍：方案骨架 → 方案门 → 出图 → 契约门
python "$SKILL_DIR/scripts/scaffold.py" --case my_case.json --out plan.json
python "$SKILL_DIR/scripts/main.py" --case my_case.json --plan plan.json --out /tmp/my-out
python "$SKILL_DIR/scripts/check_contract.py" --result /tmp/my-out/result.json --case my_case.json
# ③ 用同一把尺子量你的产物（可与自己未用本 Skill 的做法对照）
python "$SKILL_DIR/scripts/gain_harness.py" --out /tmp/my-out --case my_case.json --material my_material.md
```

**可复用资产**：SVG 图层命名契约、四要素知识文档、方案 schema、结果契约 + G1–G8 硬性门、
面板模板/色板/字号、资产三件套、最小可跑案例、只读测量器、对照协议、机制说明、决策规则与失败矩阵、
两个 exit-code 自查器、**失败注入器（可搬到任何以 `main.py --case/--out` 为入口的出图 Skill）**、
**三案例题集**。

---

## 7. 题集（三个跨题材案例 + 失效边界）

逐案输入、期望产出结构、可接受区间、难度层、实测结果见
[`references/CASE-SET.md`](references/CASE-SET.md)。

| # | 案例 | 题材 | 难度层 | 实测 `status` | `uncertainty` |
|-|-|-|-|-|-|
| 0 | `example-micelle-001` | 纳米医学（pH 响应胶束递送） | L1 基线 | `success` | 0 条 |
| 1 | `calab-perovskite-001` | 材料/能源器件（钙钛矿界面钝化） | L2 标准 | `success` | 0 条 |
| 2 | `urban-heat-001` | 地球/环境科学（城市热岛能量平衡） | L3 挑战 | **`partial`** | **2 条**（缺值占位 + 数值矛盾，均带 `src`） |

三案共同判据全部通过：exit `0`、顶层 26 键、`check_contract` exit 0、四要素 4/4、
实体覆盖与数值编码一致性为空、图层命名无违规、两次运行 `spec_sha16` 一致。

**泛化失效边界（摘要，完整 8 条见 CASE-SET §4）**：散文里的数字不抽取；机制关系必须带真实箭头；
材料与 case 数值矛盾**不自动裁决**（首见优先 + 冲突留痕）；扫描件无文本层时跳过而非编造；
带比较符/区间的值（`≈`、`0.8–1.2`）不解析；`task.md` 缺四小节会削弱面板内容；契约字段一律禁 null；
确定性只承诺"同输入同结构"，不承诺记住手工改动。

---

## 8. 交付前自查清单

- [ ] 跑的是**真实文件**（case.json / task.md / 材料），没有凭标签假设内容
- [ ] 主链 `python "$SKILL_DIR/scripts/main.py" --case … --out …` → **exit 0**、产出 `result.json`（26 键）
- [ ] 顶层覆盖「信封 18 键 ∪ 案例契约全部字段」且**无 null**；`check_contract.py` **exit 0**
- [ ] 方案门与规格门均无 problems
- [ ] SVG 良构、7 层 `layer:*`、`<text>` 可编辑、`data-src` 可溯源；PNG 非空；PDF 有头或 `present:false`+reason
- [ ] 四要素 4/4；实体覆盖率与数值编码一致性 100%
- [ ] 同输入重跑 `determinism_probe.spec_sha16` 一致
- [ ] `fault_inject.py --fail-on strict` **exit 0**（23/23 `ok`、0 静默失败）
- [ ] 至少跑两个不同题材的案例，确认不退化（题集三案）
- [ ] `uncertainty` 里没有"编造数据"类补丁；已按 `references/RUBRIC_MAP.md` 五维自评

---

## 9. 五维落点（速查；完整对照见 `references/RUBRIC_MAP.md`）

| 维度 | 分 | 本包落点 |
|-|-|-|
| 实际效果 | 40 | 三案例跨题材实跑；四要素单页 + 可编辑分层 SVG + PNG/PDF；逐元素 `data-src` 与 `sources[]`(sha256) |
| 使用增益 | 25 | 对照协议 + 只读测量器给出可复算的增益数字（分层 7、真文字 61、溯源 0.903、四要素 4/4、契约 8/8、返工 0 步），并如实记录 A 单次更慢 |
| 创新增益 | 15 | 三个机制各自带反事实与失效条件；**可执行失败注入器 + 实测矩阵**；**跨题材题集 + 失效边界** |
| 可靠体验 | 10 | 四形态 23 条注入逐行实测（修复前 8 条静默 → 修复后 0）；20 条决策规则与失败分支同号互查；退出码语义稳定 |
| 生态贡献 | 10 | 全文档齐备（契约/五维/失败模式/注入矩阵/增益协议/机制/复用/题集/方案 schema/四要素/图层/模板）+ 资产三件套 + 三案例 + `GITHUB_URL.txt` |

---

## 10. 目录结构（49 个文件，上限 50）

```
<skill root>/
  SKILL.md  README.md  TEST.md  GITHUB_URL.txt
  references/
    OUTPUT_CONTRACT.md    result.json 契约（字段块逐字保留）
    RUBRIC_MAP.md         五维 → 文件/机制逐条映射
    failure-modes.md      失败模式 ↔ D1–D20 ↔ 注入用例 三者互查
    FAULT-MATRIX.md       ★D 轴★ 四形态注入实测矩阵 + 修复点名
    CASE-SET.md           ★E 轴★ 题集：逐案输入/期望结构/可接受区间/实测/失效边界
    GAIN-PROTOCOL.md      ★B 轴★ 对照协议 + 实测记录（含对 A 不利的观测）
    MECHANISM.md          ★C 轴★ 三个机制的反事实与失效条件
    REUSE-KIT.md          ★C 轴★ 资产清单 / 题集与金标准协议 / 三步移植
    plan-schema.md  ga-four-elements.md  layer-naming.md  TEMPLATE.md
  scripts/
    main.py               编排入口（--case/--task/--material/--plan/--out/--pdf/--no-pdf/--raster-scale）
    fault_inject.py       ★D 轴★ 四形态注入器（23 条用例，真跑子进程）
    gain_harness.py       ★B 轴★ 只读测量器（--out/--case/--material/--label/--json/--compare）
    extract.py figurespec.py svgbuilder.py preview.py audit.py
    spec_lint.py scaffold.py check_contract.py common.py
  assets/                 spec_template.json  result_example.json  example_material.txt
  examples/
    case.json material.md task.md plan.example.json EXPECTED-OUTPUT.md README.md output/…
    cases/calab-perovskite-001/{case.json,material.md,task.md}
    cases/urban-heat-001/{case.json,material.md,task.md}
```

---

## 11. 限制（如实声明）

- 渲染链真实可达的两级是「matplotlib → 纯 Python PNG」：matplotlib 自身 `import PIL`，
  屏蔽 Pillow 会连带 matplotlib 失效（FAULT-MATRIX §3 记录）；三级都不可用时 `status=failed`。
- 抽取依赖材料文本结构：只认**独立成行的 `键 = 数值 单位`**与**带真实箭头的机制行**；
  散文里的数字不会被抽取（CASE-SET §4 边界 1/2）。
- 材料与 case 数值矛盾**不自动裁决**（首见优先 + 冲突留痕）；扫描件无文本层时跳过并记录。
- 注入演练覆盖本包可控的输入/模板/依赖/契约四类；**平台侧故障（挂载缺失、配额、超时）不在其内**。
- 四要素/图层/契约检查是结构判据，不代替领域科学判断。
- 三个示例案例均为**合成示意**，不是平台正式案例，不代表正式成绩。
