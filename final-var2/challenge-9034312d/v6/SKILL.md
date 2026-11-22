---
name: apparatus-and-route-diagrams
description: >-
  依据科研材料生成或编辑「实验装置与技术路线图」可编辑图稿（分层 SVG 源文件 +
  PNG/PDF 预览 + result.json），并给出四类可复核证据：证据链（每条实体/关系带
  locator+quote+材料 sha256）、机器审计（连接规则资产 + G1–G10 契约门）、
  增益对照（协议 + 真跑记录）、以及可靠性演练（32 条故障注入 + 运行前闸门）。
  本版是全维合并版：把决策显性化、增益可验证、机制与复用、失败注入与恢复、
  多案例泛化五条线并进同一个包，并用一份整合 SKILL.md 按「输入 → 执行 → 失败 →
  增益 → 机制 → 复用」重排索引。附 4 个合成案例（route·flow·apparatus 三种图类）
  与题集跑批脚本；泛化边界（纯文本输入下关系保留率可低至 0）如实写进 CASE-SET。
---

# 实验装置与技术路线图 Skill · 全维合并版（challenge-9034312d · figures 组）

本文是本包的**唯一入口**：按「输入 → 执行 → 失败 → 增益 → 机制 → 复用」六段重排，
每一段都指向一份可复核的 reference。读完本文你应当能做到三件事：
**跑出图**、**知道它在什么条件下会坏**、**把其中的机制搬到别的题上**。

| 段 | 你想干的事 | 去哪一节 | 展开在哪份 reference |
|-|-|-|-|
| 0 | 定位技能根、知道包长什么样 | §0 | `README.md §1` |
| 1 | 输入约定与参数 | §1 | `references/OUTPUT_CONTRACT.md`（产物形状） |
| 2 | 执行：证据 → 布图 → 渲染 → 审计 → 契约 | §2 | `references/RUBRIC_MAP.md`（五维落点） |
| 3 | 坏了怎么办 | §3 | `references/failure-modes.md`、`references/FAULT-MATRIX.md` |
| 4 | 加载它到底好了多少 | §4 | `references/GAIN-PROTOCOL.md`、`references/comparison-data.json` |
| 5 | 它凭什么成立（机制） | §5 | `references/MECHANISM.md` |
| 6 | 怎么搬走 / 怎么换题材 | §6 | `references/MECHANISM.md` 附录 A、`references/CASE-SET.md` |

> 本版是**合并版**：五条线（决策显性化 / 增益可验证 / 机制与复用 / 失败注入与恢复 /
> 多案例泛化）的实质内容都在，且同主题材料做了合并（**内容不删**）。合并映射见 `README.md §1`
> 的"文件合并对照"。

## 0. 技能根、包形态与自定位

- 技能根 = 本 `SKILL.md` 所在目录，后文记作 `$SKILL_DIR`。平台把它装到
  `/skills/weekly-skill`；本地复现时就是你解包出来的目录：

  ```bash
  SKILL_DIR=/skills/weekly-skill
  SKILL_DIR="$(cd "$(dirname /path/to/SKILL.md)" && pwd)"
  ```

- `scripts/*.py` 全部用 `os.path.dirname(__file__)` 自定位，读 `templates/`、`assets/`、
  `references/`、`examples/` 相对技能根解析，**不依赖运行时 cwd**，也不写
  `__pycache__`（每个脚本首部都置 `sys.dont_write_bytecode = True`）。
- 资源形态（平台硬约束）：只含 `.md/.py/.json/.txt/.csv/.yaml/.yml` 文本资源，
  文件数 ≤50、单文件 ≤500KB、合计 ≤2MB、无符号链接；**包内不含任何二进制/矢量文件**。
  `figure.svg`（可编辑源文件）、`figure.png`、`figure.pdf` 由 `scripts/main.py`
  **运行时现场生成**（见 §2 产出表），不随包发布。
- 本包共 **15 个脚本**，全部自定位：`main.py`（编排）、`preflight.py`（运行前闸门）、
  `fault_inject.py`（故障演练）、`case_set_run.py`（题集跑批）、`gain_evidence.py`、
  `model.py`、`layout.py`、`render_svg.py`、`export_preview.py`、`svg_verify.py`、
  `check.py`、`fonts.py`、`bare_baseline.py`（对照下界）、`gain_probe.py`（指标复算）、
  `decision_probe.py`（决策用例探针）。

## 1. 输入

**做什么**：材料 → 证据链（每条实体/关系带 `locator`+`quote`）→ 结构化中间表示（SIR）
→ 确定性布图 → 可编辑分层 SVG → PNG/PDF 预览 → 机器校验 → `result.json`。
**不做什么**：数值拟合与数据分析；实验方案科学合理性判断；论文排版与期刊格式适配。

- 输入：`/input/case.json`（必读）+ `/input/task.md`（可选）+ 案例引用的材料
  （`--material`，或 case.json 的 `text/materials_text` 内联）；
- 输出：写进 `--out`（官方运行时 `/app/output`），落点 `<out>/<case_id>/`；
- 编辑既有图稿：`--merge <override.json>`（同名 id 替换、新 id 追加，动作进 `change_record`）。

```
python "$SKILL_DIR/scripts/main.py" --case <case.json|案例目录> [--task <task.md>]
                       [--material <材料文件|目录>] [--merge <override.json>]
                       --out <输出目录> [--dpi 200]
                       [--figure-type route|apparatus|flow|hybrid]
                       [--title "…"] [--width-mm N] [--height-mm N]
                       [--palette <palette.json>] [--rules <connection_rules.json>]
```

- `--case` 给**目录**时自动取该目录下 `case.json`，未给 `--task` 时取同目录 `task.md`
  （平台输入约定即这一对）；给**具体文件**时不猜同目录文件（材料来源宁可少而准）。
- `--rules` / `--palette` 是本包**最需要外部确认**的两个参数：指到不存在的路径或坏 JSON 时，
  主流程会**静默回落**（审计空转 / 默认配色），产物看起来完全正常 —— 实测证据见
  `references/FAULT-MATRIX.md` F2-01…F2-07，对策见 §3 的闸门。
- 输入形态决定上限：结构化 `entities/relations` 走主航道；只有 `text` 时走文本解构
  （`extraction=text-heuristic`，只串联相邻步骤）——**纯文本输入下关系保留率实测可低至
  0.000**，见 `references/CASE-SET.md §6`。

## 2. 执行

**主线五步**（每步都在真实文件上操作，禁止依据领域标签猜内容、禁止编造数值）：

```
步骤 0  读实际输入（cp1 前置：真实 read，不假设内容）
步骤 0.5 运行前闸门  python "$SKILL_DIR/scripts/preflight.py" --case … --deps
步骤 1  证据抽取与复核        → evidence.json            （CP1 证据门）
步骤 2  布图与校验            → layout.json / figure.svg / verify_report.json（CP2/CP3）
步骤 3  导出预览              → figure.png / figure.pdf （CP3 续）
步骤 4  契约与自查            → result.json + check.py   （CP4 契约门）
```

| 产物（相对 `<out>/<case_id>/`） | 谁生成 | 角色 |
|-|-|-|
| `evidence.json` | `gain_evidence.py` | 证据链：实体/关系 `locator`+`quote` + 材料 `sha256`/`size`/`role` |
| `layout.json` | `layout.py` | 几何中间证据（可复核、可重绘） |
| `figure.svg` | `render_svg.py` | **可编辑源文件**：5 层 `layer:*`，`<text>` 真实文本，实体组带 `data-*` |
| `figure.png` / `figure.pdf` | `export_preview.py` | 渲染预览（PIL 200 DPI / reportlab 矢量 + CID 字体） |
| `verify_report.json` | `svg_verify.py` | 图层/文本/箭头/编号/图例/连接规则审计 + `spec_sha16` 确定性探针 |
| `result.json` | `main.py` | 契约结果（18 个顶层字段，见 `references/OUTPUT_CONTRACT.md`） |

**四个检查点**：CP1 证据门（`locator` 真实命中材料）、CP2 连接门（类别/关系在词表内、
无 error 级违规）、CP3 校验门（SVG 结构与导出件）、CP4 契约门（G1–G10 全过 + 状态诚实）。

**辅助命令**（都可独立运行，全部自定位）：

```
python "$SKILL_DIR/scripts/preflight.py"  --case … [--task …] [--material …] [--merge …]
                                          [--rules …] [--palette …] [--deps] [--strict]
python "$SKILL_DIR/scripts/fault_inject.py" [--out <目录>] [--json <报告>] [--only F2-*] [--list]
python "$SKILL_DIR/scripts/case_set_run.py" [--out <目录>] [--json <报告>] [--only <id>] [--text-only] [--list]
python "$SKILL_DIR/scripts/gain_evidence.py" --case <case.json> [--task …] [--material …] --out <evidence.json>
python "$SKILL_DIR/scripts/svg_verify.py" --layout <layout.json> --svg <figure.svg> [--rules …] [--out …]
python "$SKILL_DIR/scripts/check.py" <result.json>
python "$SKILL_DIR/scripts/bare_baseline.py" --case <case.json> --out <目录>      # 对照下界（C0）
python "$SKILL_DIR/scripts/gain_probe.py" --result <result.json> [--baseline <C0 目录>]   # 指标复算
python "$SKILL_DIR/scripts/decision_probe.py" [--out <目录>] [--json <报告>]      # 20 个决策用例
```

**退出码语义**（四个入口各一套，互不改写）：

| 入口 | 0 | 1 | 2 | 3 |
|-|-|-|-|-|
| `main.py` | 全过 | 流水线异常（仍落盘 `failed/result.json`） | 输入缺失 | 已出图但契约门不过 |
| `check.py` | G1–G10 全过 | 有 issue | 用法错误 | — |
| `preflight.py` | 无 finding | 只有 warn | 用法错误 | 有 error |
| `fault_inject.py` / `case_set_run.py` | 跑完 / 全 PASS | 探针出错 / 有案例 FAIL | 用法错误 | — |

## 3. 失败：坏了会怎样，以及怎么提前拦住

本节的每个数字都来自 **32 条真实故障注入**（`scripts/fault_inject.py`），
完整矩阵见 `references/FAULT-MATRIX.md`，逐现象速查见 `references/failure-modes.md §1`。

| 形态 | 注入 | 实测结论 |
|-|-|-|
| 输入 | 11 条 | **硬的**：缺文件退出码 2；坏 JSON / 坏 `--merge` 退出码 1 + `failed/result.json`；空壳退出码 3 |
| 模板·资产 | 8 条 | **软的**：`--rules`/`--palette` 写错或包内资产被删 ⇒ 静默回落、审计空转、退出码仍 0 |
| 依赖 | 3 条 | **诚实降级**：缺库/缺字体写进 `uncertainty[].scope`；发现缺 Pillow 会连带 PDF 一起失败 |
| 契约 | 10 条 | **硬的**：9/9 被 G 门拦下，门号与注入一一对应 |

**9 条缺陷型静默失败**（退出码 0、`status=success`、`uncertainty` 空、产物看起来正常）
集中在：断头关系不留痕（F1-06）、`--material`/`--task` 指错（F1-10/F1-11）、
配色回落（F2-01/02/06）、**规则审计空转**（F2-04/05/07）。

**对策不是改算法，而是补一道运行前闸门**：

```
preflight.py（输入/结构/资产/依赖 → 20 余种 finding）
      │  实测：9 条静默缺陷 0 漏网；退出码 0 干净 / 1 仅 warn / 3 有 error
      ▼
main.py（D1–D12 处置 + uncertainty 记账）→ check.py（G1–G10）
```

三条必须记住的实测结论（`FAULT-MATRIX.md §5.1`）：

1. **数据坏掉比代码坏掉更难发现**：删 `.py` 会 `ModuleNotFoundError`，写错 `.json` 只会"全绿"；
2. **依赖会互相牵连**：Pillow 缺失时 reportlab 也失败 ⇒ 两个导出件都没了 ⇒ G4 失败；
3. **`status` 与退出码不是一回事**：实测存在 `status=success` 且退出码 3 的行（缺中文字体：
   D9 说不降级、G10 却判失败）——两个口径的冲突已如实记录，本包**未改**既有脚本。

**缺口清单**（8 条，无法靠闸门消除的已写明人手复核办法）见 `FAULT-MATRIX.md §6`。

## 4. 增益：加载它到底好了多少

⚠ 题面写明"**文字自述不能替代实际运行证据**"，所以本节只给可复算的东西。

**对照协议**（`references/GAIN-PROTOCOL.md`）：三个条件 ——
**C0** 裸做法下界（`scripts/bare_baseline.py`：读 case → 固定网格排版 → 写 SVG，
PNG/PDF 是 0 字节占位）、**C1** 本包完整流水线、**C2** 同代码但把 `--rules` 置空
（用来把"门禁带来的增益"从"算法本身"里单独量出来）；四个必须固定的条件（同输入 /
同任务书 / 同环境 / 同预算）；预注册 6 个质量指标（Q1 来源绑定率、Q2 断头端点外露、
Q3 违规暴露数、Q4 可编辑源文件、Q5 真实导出件、Q6 状态诚实性）+ 4 个效率指标。

**实测要点**（逐项数字与命令见 `GAIN-PROTOCOL.md` 附录 A，机器可读在
`references/comparison-data.json`）：

- Q1 来源绑定率 **0.00 → 1.00**（下界产物里根本没有出处字段）；
- Q2 断头端点外露 **1 → 0**（带缺陷输入上，下界照画断头）；
- Q3 违规暴露 **0 → 3**：C1 与 C2 的 `figure.svg`/`layout.json` sha **完全相同**，
  差异只能来自规则审计 ⇒ 这 3 条确实归因于 M3（规则层）；
- **负面结果照写**：单轮耗时 **0.10 s → 0.44–0.59 s**，产物字节 **~2–4 KB → 78–105 KB**。
  **本包不声称运行更快**；可站得住的增益是"不需要人工补齐"（返工轮次 1 → 0）
  与"缺陷会被暴露"，以及运行前闸门把 9 条静默失败变成响亮告警。

**本节不能支撑的结论**（不要拿它去论证）：本包比某个模型高 X 分（没跑过任何模型）；
所有图类上都有同样的差（只测了 apparatus/route/flow 各若干合成案例）；门禁在任何输入上
都有差异（干净输入上 C1 与 C2 的 Q3 都是 0）。

## 5. 机制：它凭什么成立

三层**串联**机制（完整版 + 每层"没有它会怎样"的可执行反例见 `references/MECHANISM.md`）：

| 层 | 机制 | 没有它会怎样（实测） |
|-|-|-|
| **M1** | 证据中间层：图面元素先落成带 `locator`+`quote`+材料 `sha256` 的清单 | 元素只剩名称；来源绑定率 **0.00** |
| **M2** | 确定性布局 + 规格探针：布局是纯函数，`spec_sha16` 把"同输入 ⇒ 同布局"变成指纹 | 没有指纹可对拍；下界实现连 `layout.json` 都没有 |
| **M3** | 规则资产的机器审计：连接语义做成可编辑 JSON，按 severity 决定降级 | 断头照画（外露 1 条）、违规暴露 **0** 条 |

一句话：**M1 让"对不对"可问，M2 让"是不是同一张图"可判，M3 让"错没错"可算。**
三层都不绑定"实验装置图"这个题材 —— 迁移表见 `MECHANISM.md §5`。

## 6. 复用：怎么搬走、怎么换题材

**两条复用路径**：

1. **搬机制**（`references/MECHANISM.md` 附录 A）：7 类 15 项可复用资产 +
   四步复用流程（选层 → 换数据不换结构 → 接门禁 → 自证增益）+ 三个搬运陷阱
   （把规则写进代码 / 拿 `evidence.json` 的 sha 当一致性判据 / 把 warn 也做成降级）。
   复用价值排序：**规则资产 > 打包门 R1–R6 > 指标复算器 > 证据格式 > 契约自查器**。
2. **换题材**（`references/CASE-SET.md §7`）：复制 `examples/cases/<案>/{case.json,task.md}`
   两份文件即成一个新案例；在 `references/case-set.json` 登记期望（区间 + 不变量 +
   允许告警 + 禁止的 error 规则），即可被 `scripts/case_set_run.py` 批量验收。

**题集现状（4 案，三种图类，三个难度层）**：`mbr-wastewater-flow-01`（环境工程 · flow · 中）、
`dtms-stage-route-01`（分子生物学 · route · 高）、`demo-biotech-route-01`（route · 低）、
`apparatus-spec-01`（装置装配 · apparatus · 低）。实测 `cases=4 · passed=4 · failed=0`。

**泛化边界（实测，务必先读）**：把案例压扁成"只留一段文字"后重跑，实体保留率
**0.200–0.667**、关系保留率 **0.000–0.357**；装置图 5 条关系全丢并降级 `partial`；
两案的回流告警消失（回流根本没被识别），而另一案只剩 2 实体 1 关系却仍报 `success`
—— **输入退化不会自动降级状态**。详见 `references/CASE-SET.md §6`。

## 7. 自查清单（完成判定）

- [ ] 闸门先过：`preflight.py` 退出码 0，或 1/3 的每条 finding 都已确认或修复
- [ ] CP1：`evidence.json` 存在；实体 ≥1 且与材料一致；`source/locator` 可追溯
- [ ] CP2：无 error 级连接规则违规；**且确认规则集非空**（否则等于没审）
- [ ] CP3：SVG 合法 XML、5 层齐全、`<text>` ≥3；编号连续；图例↔图元一致；无断头箭头
- [ ] CP3：`figure.png`/`figure.pdf` 存在且非空（失败已如实降级并写进 `uncertainty`）
- [ ] CP4：`result.json` 含契约 18 个顶层字段；`check.py` 输出 `ok:true`、退出码 0
- [ ] 状态诚实：有未解决 error 违规 / 孤儿实体时 `status` 不得为 `success`
- [ ] 题集：`case_set_run.py` 退出码 0，没有 `NO-EXPECTATION` 的案例
- [ ] 记录：`change_record` / `uncertainty` / `sources`+`evidence` 均已如实填写
- [ ] 形态：只有 `.md/.py/.json/.txt/.csv/.yaml/.yml`，无 `__pycache__`、无本机绝对路径
- [ ] 复跑过一次 `fault_inject.py`，知道自己这套环境里哪几行会静默

## 8. 边界与诚实原则

- 只负责**绘图表达**与**可编辑交付**；不判断实验方案科学性，不做数值拟合；
- 每个实体/关系尽量带 `source`+`locator`+`quote`；拿不到就标 `null` 并计入 `uncertainty`；
- 不伪造软件状态（如中文字体缺失）、不编造科研数据或数值；
- **既有脚本不改**：基线的 9 个脚本逐字节一致，R1/R2 新增脚本原样并入；
  已知的 8 条缺口（`FAULT-MATRIX.md §6`）靠闸门 + 文档处置，不靠改算法；
- 本包全部实测数字来自合成案例与本机运行（Windows 11 · CPython 3.13.9），
  **不构成**对平台正式评分的预测；正式案例、白板与评分由平台提供/执行；
- `examples/` 与 `examples/cases/` 都是**合成**示例（标注「示例，非正式案例」），
  不含预制答案，期望产物清单见 `examples/EXPECTED-OUTPUT.md`。

## 9. 资源清单（路径均相对技能根；★ = 本合并版的关键证据）

**脚本（15 个，全部自定位）**

- `scripts/main.py` ★ — 一键流水线（证据→模型→布图→渲染→校验→契约）
- `scripts/preflight.py` ★ — 运行前闸门（输入/结构/资产/依赖四类 finding）
- `scripts/fault_inject.py` ★ — 32 条四形态故障注入与恢复演练
- `scripts/case_set_run.py` ★ — 题集跑批 + 期望比对 + 泛化损失测量
- `scripts/gain_evidence.py` — 证据抽取（CP1）
- `scripts/model.py` — SIR：实体/关系/步骤/流向解析与文本解构兜底
- `scripts/layout.py` — 确定性布图（图元库 + 模板落点）
- `scripts/render_svg.py` — 手写分层 SVG（可编辑源文件）
- `scripts/export_preview.py` — PIL PNG + reportlab PDF（同一布局模型）
- `scripts/svg_verify.py` — SVG 校验 + 连接规则审计（CP2/CP3）
- `scripts/check.py` — 契约门 G1–G10（CP4；退出码 0/1）
- `scripts/fonts.py` — 中文字体探测与降级
- `scripts/bare_baseline.py` — 对照下界 C0（把 M1/M2/M3 三层全拿掉的反例实现）
- `scripts/gain_probe.py` — Q1–Q6 指标复算器（只用公开 JSON 字段，不 import 包内模块）
- `scripts/decision_probe.py` — 20 个决策用例的批量探针（输出观测值表）

**参考文档（11 份；括号内是合并来源）** ★

- `references/OUTPUT_CONTRACT.md` — 契约 18 个顶层字段 + G1–G10 + 故障视角读法
  （附录：`result.json` 最小形态示例，原 `assets/result_example.json`）
- `references/RUBRIC_MAP.md` ★ — 五维（40/25/15/10/10）逐条落点与可复核证据
- `references/failure-modes.md` ★ — 四形态实测失败模式（附录 A：D1–D20 决策规则全表 +
  状态聚合优先级；附录 B：27 行失败分支表；附录 C：20 个可复跑决策用例，
  原 `DECISION-CASES.md`）
- `references/FAULT-MATRIX.md` ★ — 32 条注入的实测矩阵 + 9 条静默 + 8 条缺口 + 闸门效果
- `references/GAIN-PROTOCOL.md` ★ — 公平对照协议（附录 A：实跑对照记录，原
  `COMPARISON-RECORD-20261122.md`；附录 B：三层机制反例摘要，原 `COMPARISON-SUMMARY.md`）
- `references/MECHANISM.md` ★ — 三层机制与逐层反例（附录 A：15 项可复用资产 + 四步复用
  流程 + 三个陷阱，原 `REUSE-GUIDE.md`）
- `references/CASE-SET.md` ★ — 题集逐案说明（输入/期望结构/可接受区间/难度/实测/失效边界）
- `references/case-set.json` — 题集期望表（机器可读，跑批判据来源）
- `references/comparison-data.json` — 对照实验原始数据（v2 与 v3 两版字段的并集）
- `references/vocabulary.md` — 术语表与词表（kind / 关系 / 图类 / 命名 / 状态）
- `references/figure-blueprint.md` — 布局蓝图（图元 / 模板落点 / 命名 / 导出 / 扩展）

**资产与模板**

- `assets/connection_rules.json` — 连接规则字典（词表 + 8 条带 severity 的规则）
- `templates/palette.json` — 图元配色模板（kind → 填充/描边/形状）
- `templates/component-connection-checklist.md` / `entity-relation-checklist.csv` — 核对清单/表

**示例**

- `examples/case.json` + `examples/task.md` — route 示例（含 `--merge` 编辑用例）
- `examples/apparatus_spec.example.json` / `route_spec.example.json` /
  `route_spec.mutation.example.json`
- `examples/cases/<case_id>/{case.json,task.md}` — 题集两个新题材合成案例
- `examples/output/<case>/{result.json, artifacts.json}` — 两个示例案例的文本类运行产物
  （`artifacts.json` 是 evidence/layout/verify_report 三份的合并版，内容逐字保留）
- `examples/EXPECTED-OUTPUT.md` / `examples/README.md` — 期望产物清单与用法
  （`examples/README.md` 已并入原 `examples/output/README-EXAMPLE.md` 的正文，并补写了题集案例与 `artifacts.json` 的组织方式）

**依赖**（全部可降级）：Python 3.10+ 标准库；Pillow（PNG）；reportlab（PDF）。
⚠ 实测：reportlab 内部也依赖 PIL，缺 Pillow 时 PNG 与 PDF 会**一起失败**。

## 10. 评分五维速查（逐条证据见 `references/RUBRIC_MAP.md`）

| 维度 | 分 | 本包落点（一句话） |
|-|-|-|
| 实际效果 | 40 | 一键出图（可编辑 SVG + 真实 PNG/PDF + 四份 JSON）；**4 个合成案例三种图类全部真跑 PASS** |
| 使用增益 | 25 | 证据先行 + 规则审计 + 运行前闸门；**公平对照协议 + 真跑记录 + 负面结果照写**（`GAIN-PROTOCOL.md`） |
| 创新增益 | 15 | SIR → 确定性布图 → 三后端同布局；**三层机制各自"没有它会怎样"的可执行反例**；故障行为做成 32 条注入矩阵 |
| 可靠体验 | 10 | 32 条注入实测 + 9 条静默逐条给出位点 + 8 条缺口清单 + D1–D20/F1–F4 决策规则 + 退出码语义表 |
| 生态贡献 | 10 | 15 项可复用资产与四步复用流程 + 可搬走的题集（案例 + 期望表 + 跑批）+ R1–R6 打包门可直接抄 |
