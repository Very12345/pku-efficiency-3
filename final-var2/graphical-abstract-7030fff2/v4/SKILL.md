---
name: graphical-abstract
description: >-
  从研究材料产出单页 Graphical Abstract（图形摘要）的 Skill，本版以「失败注入与恢复演练」
  为轴心：材料 → 实体/关系/数据抽取（逐元素 data-src 溯源）→ 方案先行（scaffold 骨架 +
  方案 lint）→ 确定性版面与数据编码 → 可编辑分层 SVG（layer:* 七层契约）+ PNG/PDF 渲染件 →
  audit 与契约自查；并附一套**可执行的失败注入器**（scripts/fault_inject.py）与**实测矩阵**
  （references/FAULT-MATRIX.md）：把输入/模板/依赖/契约四形态缺陷逐个真的弄坏、跑真实主流程、
  记录退出码/status/uncertainty，逐行判定是否静默失败。Use when the task says
  "graphical abstract", "图形摘要", "示意图 / 机制图 / 流程图 / 图稿", "为论文或基金画一张图",
  "编辑已有的图稿"，或需要验证这条出图链路在各种材料/依赖/契约缺陷下的真实行为。
---

# Graphical Abstract 图形摘要 Skill — 失败注入与恢复演练版

把「研究问题 → 方法 → 核心结果 → 结论」压进**单页**，交付**可继续编辑的分层源文件**
（不是位图截图）、渲染预览与字段完整的 `result.json`。**数值不编造**：材料里定位不到的
数值只进 `uncertainty` 并占位。

本版与前几版的差别只有一件事：**不满足于"文档里写了会怎么失败"，而是把失败真的造出来跑一遍。**
`scripts/fault_inject.py` 对四形态注入 23 条用例，逐条抓真实进程行为；查出的缺陷在包内
按**纯增量**方式修好，修复前后的对照全部落在 `references/FAULT-MATRIX.md`。

| 项目 | 值 |
|-|-|
| Skill 名称 / 版本 | `graphical-abstract` / `2.0.0`（脚本内 `SKILL_VERSION`） |
| 技能根 | 本文件所在目录，下文记作 `$SKILL_DIR` |
| 资源形态 | 纯文本七种扩展名（`.md .py .json .txt .csv .yaml .yml`）；无二进制、无预置 `.svg/.png/.pdf`、无字体文件、无 `__pycache__`、无本机绝对路径 |
| 出图入口 | `python "$SKILL_DIR/scripts/main.py" --case <case.json> [--task …] [--material …] [--plan …] [--out <dir>] [--pdf|--no-pdf] [--raster-scale N]` |
| 本轴新增 | `scripts/fault_inject.py`（注入器）、`references/FAULT-MATRIX.md`（实测矩阵 + 修复点名） |
| 实测状态 | 注入 23/23 符合期望、0 静默失败；`fault_inject.py --fail-on strict` 退出码 0 |

---

## 0. 调用（cwd 任意；命令逐字可用）

脚本用 `scripts/common.py` 的 `SCRIPT_DIR = dirname(abspath(__file__))` 自定位技能根，
因此**不要求 cwd = 技能根**：

```bash
# 技能根（两种写法任选；不确定时用最后一行向上探测）
SKILL_DIR=/skills/weekly-skill                      # 官方评测容器的安装位置
SKILL_DIR=/abs/path/to/graphical-abstract-7030fff2  # 本机解压目录
SKILL_DIR="$(pwd)"; while [ ! -f "$SKILL_DIR/SKILL.md" ] && [ "$SKILL_DIR" != "/" ]; do SKILL_DIR="$(dirname "$SKILL_DIR")"; done

# 出图（示例案例；产物写包外目录）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/ga-out

# 契约自查（exit 0 = 顶层覆盖「信封 18 键 ∪ 案例契约」且无 null）
python "$SKILL_DIR/scripts/check_contract.py" --result /tmp/ga-out/result.json --case "$SKILL_DIR/examples/case.json"

# 失败注入演练（本轴核心；23 条用例，约 22 秒，全部写在包外）
python "$SKILL_DIR/scripts/fault_inject.py" --out /tmp/ga-fi --fail-on strict

# 官方案例形态（平台挂载输入，产物写 /app/output）
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md --out /app/output
```

参数表、依赖清单与退出码语义见 `README.md` 与 `references/failure-modes.md`；本文件不重复。

---

## 1. 什么时候该用它 / 什么时候不该用

**应当触发**：给研究描述、实验记录、论文草稿或图表数据，要一张**单页视觉摘要**；要画机制图、
通路图、流程图、方案示意图；要**编辑已有图稿**（改标签/换色/重排面板）；要求"交付可继续修改的
源文件"；或者要求**证明这条出图链路在缺陷下是否仍然可信**。

**不应触发**：论文正文写作、统计分析、实验设计、无 Q-M-R-C 叙事的纯数据可视化。本 Skill 只对
**图面科学内容的表达、版式、可编辑性、导出质量与失败行为**负责，不对材料本身的结论真伪负责。

---

## 2. 输入 → 输出

| 输入 | 说明 |
|-|-|
| `case.json` | 必读。`case_id / title / task / source_material / entities / relations / data / figure_constraints / output_contract`（键名有同义回退链） |
| `task.md` | 任务说明；`# 问题/方法/结果/结论` 小节直接映射为面板要点 |
| 材料文件 | `source_material` 指明的 `.md/.txt/.json/.csv/.tex/.rst` **或 PDF**（PDF 走文本层，见 §4） |
| `--plan plan.json` | 可选。设计方案（`scaffold.py` 出骨架 → Agent 定稿 → 方案 lint） |

输出（全部写进 `--out`）：

| 文件 | 内容 |
|-|-|
| `<case_id>_graphical_abstract.svg` | 可编辑分层 SVG 源：7 层 `layer:*`、真 `<text>`、元素带 `data-src`/`data-entity-id`/`data-role` |
| `<case_id>_graphical_abstract.png` / `.pdf` | 渲染预览（matplotlib → Pillow → 纯 Python PNG 回退链，后端如实记录） |
| `result.json` | 唯一评分产物：信封 18 键 + 案例 `output_contract` 全字段回显（禁 null） |
| `spec.json` / `content.json` | 图面规格与规范化抽取结果（与 SVG 同一几何） |
| `audit.json` / `render_log.json` | 自查报告（四要素/图层命名/覆盖率/确定性）与渲染后端日志 |

---

## 3. 四形态失败注入（本轴的操作面）

`scripts/fault_inject.py` 把缺陷**真的造出来**再跑主流程 —— 不 mock、不 in-process 调用，
每次都是 `python <沙箱>/scripts/main.py …` 子进程，抓真实退出码：

```bash
python "$SKILL_DIR/scripts/fault_inject.py" --out /tmp/ga-fi            # 全量 23 条
python "$SKILL_DIR/scripts/fault_inject.py" --out /tmp/ga-fi --only dependency
python "$SKILL_DIR/scripts/fault_inject.py" --out /tmp/ga-fi --only F15 --verbose
```

| 类 | 注入手段（真实动作） | 判据 | 用例 |
|-|-|-|-|
| **输入** | `--case` 指向不存在文件；case.json 截断；空 case；材料路径缺失；材料是 PDF 字节流；`entities` 类型错 | 该失败就 `exit 1`；该降级就 `partial` + `uncertainty` 点名 | F00–F06 |
| **模板** | `--plan` 缺失 / 非法 JSON / 未定稿骨架 / 画布超界 / 关系无 `src` / plan 覆盖 constraints | 方案门 `plan.lint.valid=false` ⇒ `status` 不得 `success`；非法 JSON 要干净 `exit 1` | F07–F12 |
| **依赖** | `PYTHONPATH` 前置假模块：屏蔽 `matplotlib` / `PIL` / `pypdf`；`--out` 指向普通文件 | 逐级回退且如实记录；不许静默成功 | F13–F17 |
| **契约** | 契约字段声明 `null`；键与信封保留键冲突；声明类型与实值不符；无契约；容器形态空值 | 禁 null（写 `""`/`[]`/`false`/`{}`）；冲突键进 `output_contract_echo` | F18–F22 |

判级：`--fail-on silent`（默认）只有**静默失败**才判 1；`strict` 任何不符期望即判 1；
`none` 只出表。报告落在 `--out/fault_report.json`（含每条用例的 argv、退出码、status、
`uncertainty` 原文、stdout/stderr 摘要、耗时）。
**逐行实测结果（含注入前后的对照）见 [`references/FAULT-MATRIX.md`](references/FAULT-MATRIX.md)。**

---

## 4. 演练查出的缺陷与恢复措施（摘要）

第一轮演练（对着同源脚本）跑出 **8 条静默失败 + 5 条不干净失败**，v5 的两个合成案例又暴露
**5 处内容侧缺陷**。全部定位到代码行并按**纯增量**修复（只加行、不改不删；CLI 参数/默认值/
退出码语义不变）。总量：`extract.py +100`、`main.py +41`、`figurespec.py +6`、`preview.py +7`，
**删除行数全部为 0**。

| # | 位置 | 增/删 | 演练证据 | 恢复措施 |
|-|-|-|-|-|
| F1–F3 | `scripts/extract.py` | （见下行合计） | F04 F05 F16：材料路径缺失、非 UTF-8、二进制（PDF）全都**不记录**，仍报 `success` | 材料预检 + 新增 `uncertainty` 键；PDF 走 `pypdf` 文本层，取不到就跳过并写明"数值不上画布" |
| F4–F9 | `scripts/main.py` | **+41 / -0** | F08（traceback）、F07/F09/F11（方案门不过仍报 success）、F18（null 原样回显）、F13–F15（后端降级仍报 success）、F17（输出目录不可用抛栈）、F12（方案覆盖未留痕） | 六处干净化：探针解析、plan lint 降级、null 归一化、降级计入 status、`exit 2` + JSON、`change_notes` 落 `change_records` |
| P1 | `scripts/preview.py` | **+7 / -0** | F14 F15：**第三级纯 Python PNG 渲染器是死代码**（元组像素喂给 `hexc()` → `AttributeError`） | 序列化前归一化像素单元格；两级后端都缺时仍能出图 |
| G1 G3 | `scripts/extract.py` | （见下行合计） | v5 案例 A/B：`25.4 mA/cm2`、`3.1e11 cm-2` 被判「数值缺失」并排除出画布；材料行进不了事实流 | 数值解析与材料事实解析各加一次宽松二次解析（单位长度受限） |
| G2 | `scripts/extract.py` | **+100 / -0**（含 F1–F3、G1–G3、G5） | v5 案例 B：材料里 0.14 / 0.19 两处数值，第二个被静默丢弃 | 首见优先不变，但把冲突与两处 `src` 写进 `uncertainty` |
| G4 | `scripts/figurespec.py` | **+6 / -0** | v5 案例 A：说明文字渲染成 `310000000000.0`，而 audit 按 `:g` 找 `3.1e+11` ⇒ **G6 硬门报"数值未上画布"却仍报 success** | 说明文字改用与其它通道一致的 `:g` |
| G5 | `scripts/extract.py` | （含在上述 extract 合计内） | v5 案例 A/B：`RE_ARROW` 的分隔符写成可选 `⇒?`，几乎任何一行都被判成"关系"并 `continue`，材料数值因此永远进不了数据通道（案例 A 的 `relations` 被灌到 25） | 要求行内存在真实箭头记号 + 剥掉行首项目符号（案例 A 降到 9 条关系） |

> 顺带查出的一条**环境耦合**：matplotlib 自身 `import PIL`，屏蔽 Pillow 会连带 matplotlib 失效，
> 因此"第 2 级 Pillow"在装了 matplotlib 的环境里并非独立可达 —— 这类结论写进矩阵 §3，不当作缺陷。

---

## 5. 出问题时按这个顺序恢复（R1–R6）

1. **退出码**：`0` = 完成（`success`/`partial`）；`1` = 硬输入错误（case/plan 读不了）；
   `2` = 环境或内部错误（产物写不出、`status=failed`）。
2. **`result.json.status`**：`partial` 就去 `uncertainty` 找限制条目；`failed` 看 `audit.checks`。
3. **`audit.json` 六项红线**：`entity_coverage.missing` / `encoding_consistency.missing_from_canvas` /
   `bounds.outside_count` / `missing_values` / `four_element_coverage.missing` / `layer_naming.bad`。
4. **`render_log.json`**：`backend` 与 `font` 是否与预期一致，降级是否已记录。
5. **`check_contract.py --result … --case …`**：`exit 0` 才说明契约无缺口、无 null。
6. **`fault_inject.py --only <类>`**：怀疑环境/依赖/契约行为时，直接跑注入看判级；
   报告里 `verdict != ok` 的那一条就是根因方向。

---

## 6. 执行主链（每步都有出口判据）

```bash
# 0 方案先行（可选但推荐）：骨架 → 人工/Agent 定稿 four_elements → 方案 lint
python "$SKILL_DIR/scripts/scaffold.py" --case <case.json> --out plan.json
python "$SKILL_DIR/scripts/spec_lint.py" --lint-plan --plan plan.json     # exit 0 才继续

# 1 出图：抽取 → 版面 → 规格 lint → 分层 SVG → 渲染 → audit → result.json
python "$SKILL_DIR/scripts/main.py" --case <case.json> --plan plan.json --out <out>

# 2 规格 lint 独立复核（与 main 内嵌同一函数）
python "$SKILL_DIR/scripts/spec_lint.py" --spec <out>/spec.json --content <out>/content.json

# 3 契约自查（判据 = 退出码）
python "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json --case <case.json>

# 4 缺陷演练（判据 = 退出码 + fault_report.json 的逐行 verdict）
python "$SKILL_DIR/scripts/fault_inject.py" --out /tmp/ga-fi --fail-on strict
```

作为 Agent，除调用脚本外**必须阅读真实文件内容并复核抽取结果**：材料里没有的数值不得上画布，
偏差写进 `change_records` / `uncertainty`。**不得用预制答案替代实际运行。**

---

## 7. 决策规则索引（完整表在 `references/failure-modes.md`）

| 规则 | 触发 | 记录位点 |
|-|-|-|
| D1 / D2 | `case.json` 缺失/不可解析 / 缺 `case_id` | stdout JSON（exit 1）/ `result.case_id` |
| D3 / D4 | `task.md` 缺失 / 材料路径缺失 | `warnings` / `uncertainty`（**F1 修复后才有**） |
| D5 / D6 / D7 | 数值缺失 / 实体歧义 / 材料数值矛盾 | `audit.missing_values` / `uncertainty` |
| D8 / D9 | 材料非 UTF-8 / 二进制（含 PDF） | `uncertainty`（**F1/F2 修复后才有**） |
| D10 / D11 / D12 | 字体缺失 / 渲染后端缺失 / PDF 不可用 | `render_log.json` + `uncertainty` / `deliverables` |
| D13 | 文字溢出 / 元素越界 | `audit.layout_log` / `audit.bounds` |
| D14 | 方案或规格 lint 不过 | `result.plan.lint` / `result.spec_lint` + `status` 降级（**F5 修复**） |
| D15 / D16 / D17 | 契约无真实值 / 键冲突 / 类型不符 | `check_contract.py` exit 0 / `output_contract_echo` / `uncertainty` |
| D18 / D19 / D20 | lint 不过仍想报成功 / 产物无效 / 重跑结构漂移 | 禁止；`status=failed`（exit 2）；`determinism_probe` |

---

## 8. 交付前自查清单

- [ ] 跑的是**真实文件**（case.json / task.md / 材料），没有凭标签假设内容
- [ ] `python "$SKILL_DIR/scripts/main.py" --case … --out …` → exit 0 且产出 `result.json`
- [ ] 顶层覆盖「信封 18 键 ∪ 案例 `output_contract` 全部字段」且**无 null**
- [ ] `check_contract.py` **exit 0**；`spec_lint.py` 无 problems
- [ ] SVG 良构、`<text>` 可编辑、7 层 `layer:*` 全绿；PNG 非空；PDF 头 `%PDF-`（或 `present:false` + reason）
- [ ] 四要素 Q-M-R-C 全部上画布；实体覆盖率与数值编码一致性 100%
- [ ] 同输入重跑：`audit.determinism_probe.spec_sha16` 一致
- [ ] **`fault_inject.py --fail-on strict` exit 0**，且 `fault_report.json` 里 `verdict` 全为 `ok`
- [ ] 本次运行触发的每条决策规则都有对应记录位点（无记录 = 未按规则执行）

---

## 9. 五维落点（速查；完整对照见 `references/RUBRIC_MAP.md`）

| 维度 | 分 | 本包落点 |
|-|-|-|
| 实际效果 | 40 | 单页四要素流水线 + 可编辑分层 SVG + PNG/PDF；逐元素 `data-src` 与 `sources[]`(sha256)；示例案例真跑产物 |
| 使用增益 | 25 | 出问题不必猜：退出码/status/uncertainty/audit 六红线/契约自查/注入演练六层判据；方案先行免重绘；确定性布局免重排 |
| 创新增益 | 15 | **可执行的失败注入器 + 实测矩阵**（同类包普遍只写"我们会处理异常"）；方案先行双 lint 门；契约四形态回显 |
| 可靠体验 | 10 | 四形态 23 条注入逐行实测；8 条静默失败被查出并按纯增量修复；退出码语义稳定；`references/failure-modes.md` 与矩阵互查 |
| 生态贡献 | 10 | 文档齐备（SKILL/README/TEST/OUTPUT_CONTRACT/RUBRIC_MAP/failure-modes/plan-schema/ga-four-elements/layer-naming/TEMPLATE/FAULT-MATRIX）+ `assets/` 三件套 + `examples/` + `GITHUB_URL.txt` |

---

## 10. 目录结构

```
<skill root>/
  SKILL.md                    本文档（四形态注入 + 恢复顺序 + 主链判据）
  README.md                   安装 / 依赖 / 参数 / 失败处理 / 维护
  TEST.md                     本机实测记录（冒烟 + 注入演练原始结论）
  GITHUB_URL.txt              公开作品链接
  references/
    OUTPUT_CONTRACT.md        result.json 契约（字段块逐字保留）
    RUBRIC_MAP.md             五维 → 文件/机制逐条映射
    failure-modes.md          失败模式 ↔ 决策规则 ↔ 注入用例 三者互查
    FAULT-MATRIX.md           ★本轴新增★ 四形态注入的实测矩阵 + 缺陷修复点名
    plan-schema.md            设计方案 schema（方案先行）
    ga-four-elements.md       四要素知识文档（Q-M-R-C 不变式）
    layer-naming.md           SVG 分层命名与溯源属性规范
    TEMPLATE.md               面板模板 / 视觉通道映射 / 复用指南
  assets/                     可复用资产三件套（纯文本）
  scripts/
    main.py                   编排入口（--case/--task/--material/--plan/--out/--pdf/--no-pdf/--raster-scale）
    fault_inject.py           ★本轴新增★ 四形态失败注入器（23 条用例，真跑子进程）
    extract.py / figurespec.py / svgbuilder.py / preview.py
    audit.py / spec_lint.py / scaffold.py / check_contract.py / common.py
  examples/                   最小示例输入 + EXPECTED-OUTPUT.md + 实跑文本产物
```

脚本不硬编码绝对路径；唯一出现的 `C:/Windows/Fonts` 等字符串是**跨平台字体探测候选路径**，
不是本机运行残留（判据：它不指向任何一次运行的产物）。

---

## 11. 限制（如实声明）

- 渲染预览后端链会逐级降级，后端与字体名如实记录；**Pillow 与 matplotlib 不是独立的两级**
  （matplotlib 依赖 PIL，见矩阵 §3），因此真实可达的降级顺序是「matplotlib → 纯 Python PNG」。
- 材料抽取依赖文本结构与 PDF 文本层；扫描件（无文本层）会被跳过并在 `uncertainty` 写明，
  相关数值一律不上画布。
- 注入演练覆盖本包可控的输入/模板/依赖/契约四类；**平台侧故障（挂载缺失、配额、超时）不在其内**。
- 四要素/图层/契约检查是结构判据，不代替领域科学判断。
- 示例数据为合成示意，与平台正式案例无关；正式案例结果由平台实跑产生。
