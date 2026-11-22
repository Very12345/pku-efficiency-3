---
name: apparatus-and-route-diagrams
description: >-
  依据科研材料生成或编辑「实验装置与技术路线图」可编辑图稿（分层 SVG 源文件 +
  PNG/PDF 预览 + result.json）。本包的独特之处是三层串联机制：先落一份带
  locator+quote+材料 sha256 的证据中间层，再由纯函数布局与 spec_sha16 规格探针把
  几何变成可对拍的指纹，最后由可编辑的规则资产做语义审计并按 severity 决定是否降级。
  三层各自都有「拿掉它会怎样」的可执行反例对照，机制说明与可复用资产清单分别见
  references/MECHANISM.md 与 references/REUSE-GUIDE.md。
---

# 实验装置与技术路线图 Skill · 机制与复用显性化版（challenge-9034312d · figures 组）

把一个领域任务做对，靠的通常不是"多写几个函数"，而是**少数几个撑住整条链路的机制**。
本包把这类机制挑出三层，逐层回答"**没有它会怎样**"，并把它们与题材解耦，
连同配套资产一起交出去，让别人能搬走。

- **M1 证据中间层**：图面元素先落成带 `locator`+`quote`+材料 `sha256` 的清单；
- **M2 确定性布局与规格探针**：布局是纯函数，`spec_sha16` 把"同输入 ⇒ 同布局"变成指纹；
- **M3 规则资产的机器审计**：连接语义做成可编辑 JSON 资产，按 severity 决定降级或仅提示。

三层是**串联**的：M1 让"对不对"可问，M2 让"是不是同一张图"可判，M3 让"错没错"可算。
机制原文与逐条反例对照见 `references/MECHANISM.md`；
可复用的 15 项资产与四步复用流程见 `references/REUSE-GUIDE.md`；
反例对照的原始数据见 `references/comparison-data.json`。

算法、CLI 接口、产物文件名与 `references/OUTPUT_CONTRACT.md` 的字段块均未改动。

## 1. 机制在哪一段生效（流水线视图）

```
read /input/case.json + task.md
      │
      ├─ M1 ─ evidence.json          每条实体/关系：locator + quote；每份材料：sha256/size/role
      │        └─ 回显 result.json.evidence；派生 data_mapping 与 element_traceability
      │
      ├── SIR（model.py）            实体/关系/步骤/流向的结构化中间表示
      │
      ├─ M2 ─ layout.py              纯函数布图（无随机、无时间/环境依赖）
      │        └─ figure.svg / PNG / PDF 三后端共享同一布局模型
      │        └─ verify_report.json.determinism.spec_sha16  ← 几何指纹
      │
      ├─ M3 ─ assets/connection_rules.json（数据） + svg_verify.py（执行）
      │        └─ error ⇒ status=partial + 退出码 3；warn ⇒ 只进 verify.warnings
      │
      └─ result.json（18 个顶层字段）+ check.py G1–G10
```

**为什么把机制画在流水线上而不是列成功能清单**：这张图说明三层各自"卡在哪一步"。
换成功能清单，读者无法判断 M2 是在渲染前还是渲染后生效——而这正是它能否保证
"三交付件同源"的关键。

## 2. 三层机制各自回答什么问题

| 层 | 它解决的问题 | 交付物里的落点 | 没有它会怎样（详见 `references/MECHANISM.md`） |
|-|-|-|-|
| M1 | 这个图面元素**出自材料哪一句**？用的是哪一版材料？ | `evidence.json`、`result.json.evidence`、`element_traceability[]` | 元素只剩名称；来源绑定率 0.00（对照实测） |
| M2 | 这两次运行**是不是同一张图**？三个交付件是否同源？ | `layout.json`、`spec_sha16`、PNG 尺寸 == 画布 × DPI | 无指纹可对拍；下界实现连 `layout.json` 都没有 |
| M3 | 这条连接**语义上成立吗**？谁来判、判错了会不会被放行？ | `verify_report.json`、`connection_rules.json`、`status` | 断头照画（外露 1 条）、违规暴露 0 条（对照实测） |

> 三层的反例对照都做了实测：同一份输入，一侧是"三层全拿掉"的
> `scripts/bare_baseline.py`，一侧是本包。摘要在 `references/COMPARISON-SUMMARY.md`。

## 3. 调用接口

```
python "$SKILL_DIR/scripts/main.py" --case <case.json|案例目录> [--task <task.md>]
                       [--material <材料文件|目录>] [--merge <override.json>]
                       --out <输出目录> [--dpi 200]
                       [--figure-type route|apparatus|flow|hybrid]
                       [--title "…"] [--width-mm N] [--height-mm N]
                       [--palette <palette.json>] [--rules <connection_rules.json>]
```

两个参数值得单独说，因为它们**直接换机制的数据层**（这就是"机制与数据的分离"）：

- `--rules <path>`：换一套连接规则。**改 JSON 即改审计结论，不用改代码**；
  指到空对象文件等于关闭 M3（本包把这当成一个可观测条件用于对照，见
  `references/COMPARISON-SUMMARY.md §3`）。
- `--palette <path>`：换一套 kind→配色/形状映射。M2 的布局读取它，所以换配色
  会改变 `spec_sha16` —— 这是设计使然（配色是布局输入的一部分）。

其余参数含义见 `--help`；`scripts/*.py` 全部 `os.path.dirname(__file__)` 自定位，
**不依赖运行 cwd**，不写 `__pycache__`（首部已置 `sys.dont_write_bytecode = True`）。
退出码：**0** 成功且契约门全过；**3** 已出图但契约门不过；**2** 输入缺失；
**1** 流水线异常（仍落盘 `failed/result.json`）。

## 4. 产出清单（相对 `<out>/<case_id>/`）

| 文件 | 生成者 | 在哪一层 | 是否随包发布 |
|-|-|-|-|
| `evidence.json` | `gain_evidence.py` | M1 | 是（文本） |
| `layout.json` | `layout.py` | M2 | 是（文本） |
| `figure.svg` | `render_svg.py` | M2 | **否**（运行期生成） |
| `figure.png` / `figure.pdf` | `export_preview.py` | M2 | **否**（运行期生成） |
| `verify_report.json` | `svg_verify.py` | M3 | 是（文本） |
| `result.json` | `main.py` | 契约层 | 是（文本） |

> 平台对 Skill 资源只接受 UTF-8 文本文件（≤50 个、单文件 ≤500KB、合计 ≤2MB、无符号链接），
> 所以三个图稿文件改为**运行时现场生成**；它们的正确性由 `check.py`（G3/G4）与
> 对照记录保证，而不是靠随包附带。

## 5. 执行步骤

> 每步都在真实文件上操作。**不依据领域标签猜内容、不编造科研数据。**
> CP1–CP4 是门，不过就按 §7 的 D# 处置，不许绕过。

**步骤 0 · 读真实输入**：`read /input/case.json`；有 `task.md`、材料文件就读；
全部登记为 `sources`；判结构（结构化 → 直接用；只有文本 → 预判走文本解构）。

**步骤 1 · M1 落地并复核（CP1 证据门）**：跑一次默认参数的 `main.py`，
流水线内置 `gain_evidence.py`，产出 `evidence.json`。**Agent 必须逐条复核**：
名称与材料是否一致、同类部件是否区分、`locator/quote` 是否真实命中、
关系方向是否与正文一致、步骤编号能否逐条对照。需要修正就写一份 `override.json`（运行时创建，不随包发布） 用 `--merge` 重跑。

**步骤 2 · M2 布图与渲染（CP3 前段）**：`layout.py` 确定性布图 → `render_svg.py` 写分层 SVG
→ `export_preview.py` 出 PNG/PDF。三者共享同一布局模型；画布溢出时等比缩放居中
（`canvas.requested` 保留原请求值），或 `--width-mm/--height-mm` 重跑。

**步骤 3 · M3 审计（CP2 连接门 → CP3 校验门）**：`svg_verify.py` 校验 SVG 结构
（合法 XML / 5 层 / 可编辑 `<text>` ≥3 / 箭头与关系一一对应 / 无断头 / 编号 1..N 连续 /
图例 kind == 图面 kind）并读取 `--rules` 指定的规则资产逐条审计。
**error ⇒ `status=partial` 且退出码 3；warn ⇒ 只写 `verify.warnings`。**

**步骤 4 · 契约与自查（CP4 契约门）**：确认 `output_contract` 四段 +
`evidence` + `verify` + 元数据齐全；跑 `check.py`（G1–G10，`ok:true`、退出码 0 才算完成）；
发现问题修复后重跑，**不得隐瞒**。

**步骤 5 · 机制自检（本版新增，可选但推荐）**：
```bash
python "$SKILL_DIR/scripts/bare_baseline.py" --case "<同输入>" --out <TMP>/c0
python "$SKILL_DIR/scripts/main.py"          --case "<同输入>" --out <TMP>/c1
```
比对 `c0`/`c1` 的产物形态（有无 `evidence`/`layout`/`verify`、PNG/PDF 是否 0 字节）。
若你的运行结果与 `references/COMPARISON-SUMMARY.md` 的形态差不同，先查环境再改结论。

## 6. 决策规则 D1–D16

本版按**决策发生在哪一层**分组（机制层 / 结构层 / 交付层），这样每条规则的归属一目了然。

**机制层（M1/M2/M3 自身的边界）**

| D# | 触发 | 处置 | 降级 | 证据位点 |
|-|-|-|-|-|
| D1 | 材料被引用却读不到（M1） | 只登记实际读到的文件，不伪造内容 | 不降级；证据条数变少 | `evidence.source_files[]` / `.notes[]` |
| D2 | 实体缺 `source`（M1） | 置 `null` 并列入不确定性 | 不单独降级 | `uncertainty[scope=sources]` |
| D3 | 画布装不下（M2） | 等比缩放居中（不裁剪） | 不降级 | `canvas.requested` vs 实际值 |
| D4 | PNG 或 PDF 渲染失败（M2） | 保留已有产物与 SVG，如实记录 | `status=partial` | `uncertainty[scope=png\|pdf]` |
| D5 | 无中文字体（M2） | `fonts.found=false` 如实记录 | 不改 `status` | `fonts[]`；`uncertainty[scope=fonts]` |
| D6 | 规则资产不可读或为空（M3） | 审计按"无规则"通过（**本包把它当可观测条件，不是隐藏行为**） | 不降级 | `verify.checks.connection_rules=true` 但规则数为 0 |
| D7 | error 级规则违规（M3） | 列明违规；不得宣称成功 | `status=partial`，退出码 3 | `verify.errors[]` |
| D8 | warn 级规则命中（M3） | 只提示复核 | **永不**改 `status` | `verify.warnings[]` |

**结构层（输入与图面之间）**

| D# | 触发 | 处置 | 降级 | 证据位点 |
|-|-|-|-|-|
| D9 | `case.json` 不存在 | 打印 `FATAL:` 后退出，不写产物 | 退出码 2 | stderr |
| D10 | JSON 不可解析 | 兜底写失败结果 | `status=failed`，退出码 1 | `failed/result.json.error` |
| D11 | 无结构化实体、仅文本 | 文本解构（只串联相邻步骤） | 不降级；记 `uncertainty[scope=relations]` | `extraction=text-heuristic` |
| D12 | 关系端点不存在 | 丢弃该关系（不画断头） | 若致孤儿则转 D13 | `verify.checks.no_dangling=true` |
| D13 | 实体无任何连接（孤儿） | 保留 + 记录，交 Agent 核对 | `status=partial` | `uncertainty[scope=orphan_entities]` |
| D14 | 实体 id 重复 | 重命名为 `<id>_2` 等 | 不降级；改名后可能触发 D13 | `entities[].id` |
| D15 | 类别/关系种类不在词表 | 容错归一化 | 不降级（**原值不留痕，见 §9**） | `verify.checks.*_vocabulary=true` |

**交付层（状态与契约）**

| D# | 触发 | 处置 | 降级 | 证据位点 |
|-|-|-|-|-|
| D16 | `result.json` 缺字段/类型不符 | `check.py` 报 issue | 退出码 3；不得 `success` | `check.py` 的 `issues[]` |

**状态聚合优先级**：输入缺失/空壳 → `failed`；两个导出都失败且无实体 → `failed`；
任一导出失败 → `partial`；`verify.ok=false` → `partial`；有孤儿实体 → `partial`；否则 `success`。
**`scope=sources` 与 `scope=relations` 不单独降级；warn 永不降级。**

## 7. 检查点 CP1–CP4 与三层的对应

| 门 | 时点 | 判定 | 属哪一层 |
|-|-|-|-|
| CP1 证据门 | 步骤 1 后 | `evidence.json` 已生成；`locator` 真实命中材料；无出处条目入 `uncertainty` | M1 |
| CP2 连接门 | 步骤 3 中 | 类别/关系在词表内；`sequence`/`connect`/流向语义合规，无 error 违规 | M3 |
| CP3 校验门 | 步骤 2–3 | `svg_verify` 全绿；PNG/PDF 存在或已按 D4 降级 | M2 + M3 |
| CP4 契约门 | 步骤 4 | `check.py` G1–G10 全过；`status` 诚实 | 交付层 |

> 这张表也是"机制的验收面"：改动 M1 只会让 CP1 变动，改动 M3 只会让 CP2/CP3 的
> 审计部分变动。**如果改一层导致另一层的门也变了，说明两层耦合了，需要重构。**

## 8. 可复用资产与复用步骤（生态贡献那一项的正面回答）

**资产清单按"拿走后省下多少工作量"排序，共 7 类 15 项**：规则资产
（`connection_rules.json` / `vocabulary.md` / `palette.json`）→ 打包门（R1–R6）→
指标复算器（`gain_probe.py` 思路）→ 证据清单格式 → 契约自查器（`check.py`）→
审计报告格式 → 其余。**完整清单（含"拿走要改什么"）与四步复用流程见
`references/REUSE-GUIDE.md`。**

四步流程的骨架（细节见该文件 §2）：

1. **选层**：按 `references/MECHANISM.md §5` 的迁移表决定搬 M1、M2 还是 M3 ——
   **一次只搬一层**，因为三层是串联的；
2. **换数据不换结构**：改 `connection_rules.json` / `vocabulary.md` / `palette.json`，
   审计结论会自动跟着变；
3. **接门禁**：对着新契约改 `check.py` 的 G 门，抄走 R1–R6 打包门（**一行都不用改**）；
4. **自证增益**：写自己领域的下界实现 → 跑 C0/C1/C2 → 复算指标 →
   **把负面结果也写进记录**。

搬运的三个陷阱（本包踩过）见 `REUSE-GUIDE.md §3`：规则写进代码、拿
`evidence.json` 的 sha 当一致性判据、把 warn 也做成降级。

## 9. 已知边界（含与机制相关的三条）

1. **`evidence.json` 的 sha 不保证跨目录一致**：它的 `sources[].path` 记的是运行时
   真实输入路径（M1 的取证需要）。要判断"内容是否一致"，请比对
   `figure.svg`/`layout.json`/`verify_report.json`，或忽略 `path` 字段。
2. **M3 会安静地跳过审计**：`--rules` 指向空对象或不存在路径时，规则集为空、
   审计自然全过。这是刻意的可观测行为（本包用它构造对照条件），
   但在正式交付里属缺陷——复核办法：核对 `verify.checks.connection_rules` 的同时
   看一眼你传的 `--rules` 是否存在、内容是否非空。
3. **M3 只审结构语义，不判科学正确性**：`sequence` 该不该连某类实体能判，
   "这个装置该不该接真空泵"不能判（题面也把科学判断留给原生/LLM 评审）。
4. **类别/关系非法值被静默归一化**：归一化后词表审计自然通过，原值不留痕。
   复核办法：对比 `evidence.entities[].kind` 与材料原始取值。
5. **全部关系端点都不存在时会退化成顺序链**（`source=text:order`），此时不报错。
   复核办法：看 `relations[].source` 是否全为 `text:order`。
6. 局部放大视图未内置；装置图为单层装配（三桶布局）；图内数值注记不强制渲染。
7. `examples/` 是**合成**示例（标注「示例，非正式案例」），不含预制答案；
   正式案例、白板与评分由平台提供/执行，本包不宣称任何具体分数。

## 10. 资源清单（按机制的归属分组）

**机制 M1**
- `scripts/gain_evidence.py` — 证据抽取（可单独运行：`--case … --out evidence.json`）
- `references/REUSE-GUIDE.md` 的 B2 条 — 证据清单格式说明

**机制 M2**
- `scripts/layout.py` — 确定性布图（纯函数）
- `scripts/render_svg.py` — 手写分层 SVG（可编辑源文件）
- `scripts/export_preview.py` — PIL PNG + reportlab PDF（同一布局模型）
- `scripts/bare_baseline.py` — **本版新增**：把 M1/M2/M3 三层全拿掉的反例实现

**机制 M3**
- `assets/connection_rules.json` — 规则资产（词表 + 8 条带 severity 的规则）
- `scripts/svg_verify.py` — SVG 校验 + 规则审计（可单独运行）
- `scripts/check.py` — 契约门 G1–G10（退出码 0/1/3）

**机制文档与数据**
- `references/MECHANISM.md` — **本版新增**：三层机制 + "没有它会怎样" + 迁移表
- `references/COMPARISON-SUMMARY.md` — **本版新增**：三层反例对照的实测摘要
- `references/REUSE-GUIDE.md` — **本版新增**：15 项可复用资产 + 四步复用流程 + 三个陷阱
- `references/comparison-data.json` — **本版新增**：对照的机器可读原始数据
- `references/GAIN-PROTOCOL.md` — 对照协议（条件/固定项/指标定义）
- `scripts/gain_probe.py` — 指标复算器（不 import 包内模块）

**其它**
- `scripts/model.py` — SIR：实体/关系/步骤/流向解析与文本解构兜底
- `scripts/main.py` — 一键流水线（编排）
- `scripts/fonts.py` — 中文字体探测与降级
- `assets/result_example.json`、`templates/palette.json`、
  `templates/component-connection-checklist.md`、`templates/entity-relation-checklist.csv`
- `references/OUTPUT_CONTRACT.md`（契约唯一权威处）、`references/RUBRIC_MAP.md`、
  `references/failure-modes.md`、`references/figure-blueprint.md`、`references/vocabulary.md`
- `examples/` — 最小调用示例（生成 + 编辑双用例）

依赖：Python 3.10+ 标准库；Pillow（PNG）；reportlab（PDF）。缺任一按 D4 降级。

## 11. 评分五维落点（速查；逐条见 `references/RUBRIC_MAP.md`）

| 维度 | 分 | 本包落点 |
|-|-|-|
| 实际效果 | 40 | `main.py` 一键出图 → 可编辑分层 SVG + 真实 PNG/PDF + 四份 JSON；四形态实测 `exit 0`、契约 18/18 |
| 使用增益 | 25 | M1/M2/M3 三层带来的可核验性差异；`GAIN-PROTOCOL.md`（协议）+ `gain_probe.py`（复算器）+ 对照记录 |
| **创新增益** | **15** | **`references/MECHANISM.md`（三层机制 + 每层"没有它会怎样"的可执行反例）+ `COMPARISON-SUMMARY.md`（实测摘要）+ C2 条件（同代码关掉审计）把 M3 的贡献单独量出来** |
| 可靠体验 | 10 | D1–D16（按层分组）+ 状态聚合优先级 + 退出码语义 + `failure-modes.md`（含 R1–R6） |
| **生态贡献** | **10** | **`references/REUSE-GUIDE.md`（7 类 15 项资产 + 四步复用流程 + 三个陷阱）+ 规则资产/配色/核对清单/契约骨架/指标复算器 + `GITHUB_URL.txt`** |
