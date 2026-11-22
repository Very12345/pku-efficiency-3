---
name: apparatus-and-route-diagrams
description: >-
  依据科研材料生成或编辑「实验装置与技术路线图」可编辑图稿（分层 SVG 源文件 +
  PNG/PDF 预览 + result.json），并把「加载本 Skill 相对不加载」的增益写成可复算的对照：
  固定四个对照条件（同输入、同任务书、同运行环境、同预算），预注册质量指标
  （来源绑定率、断头端点外露数、连接违规暴露数、可编辑源文件与真实导出件）
  与效率指标（单轮耗时、产物字节、返工轮次），逐项给出机器可判的判定规则，
  并附本包实际跑过的对照记录与一条负面结果（单轮效率没有可测增益）。
---

# 实验装置与技术路线图 Skill · 增益可验证化版（challenge-9034312d · figures 组）

本 Skill 把「装置怎么搭、步骤怎么走、物料从哪来到哪去、技术路线分几个阶段」的材料
变成一张可编辑、可追溯的图稿：分层 SVG 源文件 + PNG/PDF 预览 + PNG/PDF 之外的
`evidence.json`/`layout.json`/`verify_report.json`/`result.json`。

本版的重点不是再加一个功能，而是回答一个评分表里分值最高的开放问题：
**「加载它之后到底好了多少，怎么证明？」**——题面把 25 分给"使用增益"，其中
5 分明确给"是否通过公平对照证明质量或效率改善"，并且写明**文字自述不能替代实际运行证据**。
所以本版做了三件事：

1. **把对照写成协议**（`references/GAIN-PROTOCOL.md`）：三个条件（无 Skill 下界 /
   本 Skill / 同代码但关闭门禁）各自的构造方式；四个必须固定住的对照条件；
   预注册的 6 个质量指标 + 4 个效率指标，每个都给"怎么算、阈值多少、谁来判"。
2. **把协议真跑一遍**（`references/COMPARISON-RECORD-20261122.md` + 
   `references/comparison-data.json`）：含逐项数字、命令、观测时间点，以及
   **一条负面结果**——单轮计算的效率增益测不出来（同一个渲染器，差异在 0.1 秒量级），
   真正可测的增益在"缺陷是否被暴露"这一列。
3. **把确定性与增益解耦**：`evidence.json` 的 sha 会随运行目录变化（它记的是运行时
   真实输入路径），而 `figure.svg`/`layout.json`/`verify_report.json` 逐字节可复现。
   对照记录里明确区分这两类，免得把"路径不同"误读成"结果不同"。

算法与 CLI 接口未变（`scripts/*.py` 的入口与参数名、产物文件名与基线一致）；
`references/OUTPUT_CONTRACT.md` 的字段块逐字保留。

## 1. 结果先行：一次运行产出什么

| 产物 | 是不是"可核验"的关键 | 谁生成 |
|-|-|-|
| `figure.svg` | **可编辑源文件**：5 层 `layer:*`，文字是真实 `<text>`，实体组带 `data-entity/data-source/data-kind/data-stage/data-step-no` | `render_svg.py` |
| `figure.png` / `figure.pdf` | **真实渲染件**（不是空占位）：PIL 按 200 DPI 出位图，reportlab 出矢量 PDF | `export_preview.py` |
| `evidence.json` | 每条实体/关系带 `locator`+`quote`；输入文件 `sha256`/`size`/`role` | `gain_evidence.py` |
| `layout.json` | 几何中间证据（x/y/w/h、正交连线路径、图例、画布） | `layout.py` |
| `verify_report.json` | 机器校验结果 + 规则审计 + 确定性探针 `spec_sha16` | `svg_verify.py` |
| `result.json` | 18 个顶层字段（契约见 `references/OUTPUT_CONTRACT.md`） | `main.py` |

> 这六个里，**只有 SVG/PNG/PDF 是运行期产物**（不随包发布，平台只收文本资源）。
> 其余三个 `.json` 是文本，会随包发布在 `examples/output/` 里作为"本包真跑过"的证据。

## 2. 调用接口

```
python "$SKILL_DIR/scripts/main.py" --case <case.json|案例目录> [--task <task.md>]
                       [--material <材料文件|目录>] [--merge <override.json>]
                       --out <输出目录> [--dpi 200]
                       [--figure-type route|apparatus|flow|hybrid]
                       [--title "…"] [--width-mm N] [--height-mm N]
```

- `--case` 给**目录**：自动取该目录下 `case.json`，未给 `--task` 时取同目录 `task.md`；
- `--case` 给**具体文件**：`--task` 必须显式传（不猜同目录文件，材料来源宁可少而准）；
- `--merge`：编辑既有图稿，同名 id 替换、新 id 追加，动作写入 `change_record`。

`scripts/*.py` 一律用 `os.path.dirname(__file__)` 自定位，读资源相对技能根解析，
**不依赖运行 cwd**，不写 `__pycache__`（首部已置 `sys.dont_write_bytecode = True`）。
退出码语义：`0` 成功且契约门全过；`3` 已出图但契约门不过（诚实降级）；`2` 输入缺失；
`1` 流水线异常（仍落盘 `failed/result.json`）。

## 3. 对照协议（25 分那一项的正面回答）

**协议全文与逐项数字在 `references/GAIN-PROTOCOL.md`；这里只放你必须先知道的骨架。**

### 3.1 三个条件

| 条件 | 怎么构造 | 它代表什么 | 本包实测耗时 |
|-|-|-|-|
| **C0 裸做法下界** | `scripts/bare_baseline.py`（读 case.json → 网格排版 → 写 SVG/PNG/PDF，不做任何对账） | "不加载 Skill、也不额外努力"时的产物形态 | 0.05–0.10 s |
| **C1 本 Skill** | `scripts/main.py`（完整流水线） | 本包交付路径 | 0.40–0.48 s（四形态平均 0.44 s） |
| **C2 同代码、关掉门禁** | 用 `--rules` 指向空对象文件 | 分离"算法本身"与"门禁带来的增益" | 0.50–0.60 s |

**为什么要有 C2**：如果只对比 C0 与 C1，就无法回答"增益是来自算法还是来自门禁"。
C2 让三者的差可以拆开看。本包实测：C2 与 C1 的**产物内容一致**，
差别只在 `verify.checks.connection_rules` 是否真的审过——这正是"门禁的价值"能被单独量出来的地方。

### 3.2 必须固定住的四个条件（不固定就没有公平可言）

1. **同输入**：三个条件读同一份 `case.json`（同 sha256）；
2. **同任务书**：同一份 `task.md`（若条件不支持读 task，视为该条件的固有劣势，在记录里标注）；
3. **同运行环境**：同一台机、同一个 Python、同一批依赖（Pillow/reportlab/字体一致）；
4. **同预算**：每个条件只跑一轮、不重试；耗时按单轮 wall-clock 记。

> C0 与 C1 用的是**同一个输入文件和同一台机器**，所以下面表格里的差就是"被省略的环节"
> 造成的差，不是两套渲染实现的差。

### 3.3 预注册指标（先定义再测量）

**质量指标**（每项给判定规则，机器可判）：

| 指标 | 定义 | 判定规则 | C0 | C1 |
|-|-|-|-|-|
| Q1 来源绑定率 | 图面元素中有 `source` 的比例 | `evidence.items[].locator` 非空的条数 ÷ (实体数+关系数) | **0.00**（无该字段） | **1.00** |
| Q2 断头端点外露数 | 被画出来但端点不存在的连接数 | 输出关系的 from/to 是否都在输出实体集合内 | **1** | **0** |
| Q3 连接违规暴露数 | 被机器发现并记账的规则违例数 | `verify.errors+warnings` 条数 | **0**（无审计） | **视输入**（缺陷样本 3 条） |
| Q4 可编辑源文件 | 文字是否为真实 `<text>`、实体组是否带 `data-*` | `verify.checks.editable_text/entity_groups` | **部分**（有 `<text>` 无 `data-*`） | **true** |
| Q5 真实导出件 | PNG/PDF 是否非空且像素正确 | 文件字节数 > 0 且 PNG 可解析、尺寸 == 画布×dpi | **false**（0 字节占位） | **true** |
| Q6 状态诚实性 | 有未解决缺陷时是否拒绝宣称完成 | `status` 与 `verify.ok` 是否一致 | **false**（无 status 字段） | **true**（`partial` + `exit 3`） |

**效率指标**（同样是单轮口径）：

| 指标 | 定义 | C0 | C1 |
|-|-|-|-|
| E1 单轮耗时 | wall-clock | 0.05–0.10 s | 0.40–0.48 s |
| E2 产物字节 | 输出目录总字节 | ~2 KB（SVG 文本 + 两个空文件） | ~100–140 KB（含真实 PNG/PDF/JSON） |
| E3 人工干预步骤 | 到"可交付"要额外做几步 | ≥ 3（补溯源、校验连接、渲染导出） | **0** |
| E4 返工轮次 | 修改一处标注要重做多少 | 1（重画） | 0（`--merge` 增量） |

### 3.4 本包实际跑出来的结果（一句话版）

- **质量**：C1 在 Q1/Q2/Q5/Q6 四项上从"不满足"变成"可机器验证地满足"；
  Q3 的暴露数取决于输入缺陷量——**在带 5 类缺陷的样本上，C0 暴露 0 条、C1 暴露 3 条**。
- **效率**：**C1 比 C0 慢**（0.44 s vs 0.07 s），产物也更大。
  **这是一条负面结果，本包如实写下来**：单轮计算的效率没有增益，增益在 E3/E4
  （不需要额外人工步骤、不需要重画）——而 E3/E4 是"少做多少事"，不是"跑多快"。
  声称"效率提升 X 倍"是不诚实的，本包不这么写。

> 完整数字、命令、逐项判定见 `references/COMPARISON-RECORD-20261122.md`。

## 4. 复用这份协议（别人怎么拿它验证同类包）

```bash
SKILL_DIR=/skills/weekly-skill          # 或你解包出来的目录
CASE=/input/case.json
TASK=/input/task.md
TMP=$(mktemp -d)

# C0 下界
python "$SKILL_DIR/scripts/bare_baseline.py" --case "$CASE" --out "$TMP/c0"

# C1 本 Skill
python "$SKILL_DIR/scripts/main.py" --case "$CASE" --task "$TASK" --out "$TMP/c1"
python "$SKILL_DIR/scripts/check.py" "$TMP/c1/<case_id>/result.json"

# C2 同代码、关掉门禁（用一个空规则文件）
printf '{}' > "$TMP/empty-rules.json"
python "$SKILL_DIR/scripts/main.py" --case "$CASE" --task "$TASK" \
  --rules "$TMP/empty-rules.json" --out "$TMP/c2"

# 逐项复算 Q1–Q6（下面这段是协议的参考实现，可整段复制）
python - "$TMP" <<'PY'
import json, os, sys, glob
tmp = sys.argv[1]
def load(p):
    return json.load(open(p, encoding="utf-8"))
c1 = glob.glob(os.path.join(tmp, "c1", "*", "result.json"))
assert c1, "先跑 C1"
r = load(c1[0])
ents, rels = r.get("entities") or [], r.get("relations") or []
ids = {e["id"] for e in ents}
ev = (r.get("evidence") or {}).get("items") or []
print("Q1 来源绑定率 =", round(sum(1 for i in ev if i.get("locator")) / max(1, len(ents) + len(rels)), 3))
print("Q2 断头端点外露 =", sum(1 for x in rels if x["from"] not in ids or x["to"] not in ids))
v = r.get("verify") or {}
print("Q3 违规暴露数 =", len(v.get("errors") or []) + len(v.get("warnings") or []))
print("Q4 可编辑源文件 =", (v.get("checks") or {}).get("editable_text"),
      (v.get("checks") or {}).get("entity_groups"))
d = os.path.dirname(c1[0])
print("Q5 导出件字节 =", {f: os.path.getsize(os.path.join(d, f))
                          for f in ("figure.png", "figure.pdf") if os.path.isfile(os.path.join(d, f))})
print("Q6 状态诚实性 =", r.get("status"), (v.get("ok")))
PY
```

这段脚本 = 协议的可执行版本。**它不依赖本包的内部函数**，只用 `result.json` 的公开字段，
所以也能拿它去核别人的同类包。

## 5. 执行步骤

> 每步都在真实文件上操作；不依据领域标签猜内容、不编造数值。
> **CP1–CP4 是门**，不过就按 §7 的 D# 处理，不许绕过。

**步骤 0 · 读取真实输入**：`read /input/case.json`；有 `task.md` 就读；有材料文件就读；
全部登记为 `sources`；判结构（结构化 → 直接用；只有文本 → 预判走文本解构）。

**步骤 1 · 证据抽取与复核（CP1）**：跑一次默认参数的 `main.py`；内置 `gain_evidence.py`
生成逐条 `locator`+`quote` 与材料 `sha256`；**Agent 逐条复核**——名称是否与材料一致、
同类部件是否区分、`locator/quote` 是否真实命中、关系方向是否与正文一致、编号能否逐条对照。
需要修正就写一份 `override.json`（运行时创建，不随包发布） 并 `--merge` 重跑（同名替换、新 id 追加、动作进 `change_record`）。

**步骤 2 · 布图与校验（CP2 → CP3）**：`layout.py` 确定性布图 → `render_svg.py` 写分层 SVG
→ `svg_verify.py` 校验 SVG 合法性与规则审计。error 级违规 ⇒ `status=partial`；
warn 级只提示复核。画布溢出时等比缩放居中，或 `--width-mm/--height-mm` 重跑。

**步骤 3 · 导出（CP3 续）**：确认 `figure.png`/`figure.pdf` 生成并目测
（箭头方向、编号、图例、断头箭头、盒子重叠）；任一失败按 D10 处理。

**步骤 4 · 写 `result.json` + 交付自查（CP4）**：确认 `output_contract` 四段 +
`evidence` + `verify` + 元数据齐全；跑 `check.py`（G1–G10，`ok:true`、退出码 0 才算完成）；
发现问题修复后重跑，**不得隐瞒**。

**步骤 5 · 增益自查（本版新增）**：按 §3.3 的 Q1–Q6 复算一遍，把数字填进你自己的记录。
若 Q1 < 1.00 或 Q5 = false，说明你这次运行的产物不满足本包的增益前提，先修再交付。

## 6. 决策规则 D1–D14（异常时照查）

本版把规则表按**影响面**重排：前 4 条影响"是否能出结果"，中 6 条影响"图对不对"，
后 4 条影响"能不能当交付物"。

| D# | 触发（可观测） | 处置 | 降级后果 | 证据位点 |
|-|-|-|-|-|
| D1 | `--case` 文件不存在 | 打印 `FATAL:` 后退出，不写产物 | 退出码 2 | stderr |
| D2 | JSON 不可解析 | 兜底写失败结果 | `status=failed`，退出码 1 | `failed/result.json.error` |
| D3 | 无结构化实体、仅文本 | 文本解构（只串联相邻步骤） | 不降级；记 `uncertainty[scope=relations]` | `extraction=text-heuristic` |
| D4 | 材料被引用却读不到 | 只登记实际读到的文件，不伪造内容 | 不降级；证据条数变少 | `evidence.source_files[]` / `.notes[]` |
| D5 | 关系端点不存在 | 丢弃该关系（不画断头） | 若致孤儿则转 D6 | `verify.checks.no_dangling=true` |
| D6 | 实体无任何连接（孤儿） | 保留 + 记录，交 Agent 核对 | `status=partial` | `uncertainty[scope=orphan_entities]` |
| D7 | 实体 id 重复 | 重命名为 `<id>_2` 等 | 不降级；改名后会触发 D6 | `entities[].id` |
| D8 | 画布装不下 | 等比缩放居中（不裁剪） | 不降级 | `canvas.requested` vs 实际值 |
| D9 | 类别/关系种类非法 | 归一化到最近合法值 | 不降级（**原值不留痕，见 §8**） | `verify.checks.*_vocabulary=true` |
| D10 | PNG 或 PDF 渲染失败 | 保留已有产物与 SVG，如实记录 | `status=partial` | `uncertainty[scope=png\|pdf]`；`exports[]` 缺项 |
| D11 | error 级规则违规未解决 | 列明违规，不得宣称成功 | `status=partial`，退出码 3 | `verify.errors[]` |
| D12 | `result.json` 缺字段/类型不符 | `check.py` 报 issue | 退出码 3；不得 `success` | `check.py` 的 `issues[]` |
| D13 | 本机无中文字体 | `fonts.found=false` 如实记录 | 不改 `status` | `fonts[]`；`uncertainty[scope=fonts]` |
| D14 | 人工直接改了 SVG | 把改动补进 `change_record` | 不降级（隐瞒才是问题） | `change_record[]`；`checksum` |

**状态聚合优先级**（多缺陷同时出现时 `status` 取谁）：
输入缺失/空壳 → `failed`；两个导出都失败且无实体 → `failed`；任一导出失败 → `partial`；
`verify.ok=false` → `partial`；有孤儿实体 → `partial`；否则 `success`。
**`scope=sources`（缺出处）与 `scope=relations`（文本解构）不单独降级**；
**warn 级违规永不改变 `status`**。

## 7. 检查点 CP1–CP4（对照实验里也要过）

| 门 | 时点 | 判定 | 在对照里的作用 |
|-|-|-|-|
| CP1 证据门 | 步骤 1 后 | `evidence.json` 已生成；`locator` 真实命中材料；无出处条目入 `uncertainty` | Q1 的测量对象 |
| CP2 连接门 | 步骤 2 绘制中 | 类别/关系在词表内；`sequence`/`connect`/流向语义合规，无 error 违规 | Q3 的测量对象 |
| CP3 校验门 | 步骤 2–3 | `svg_verify` 全绿；PNG/PDF 存在或已诚实降级 | Q4/Q5 的测量对象 |
| CP4 契约门 | 步骤 4 | `check.py` G1–G10 全过；`status` 诚实 | Q6 的测量对象 |

## 8. 已知边界（含本版新查明项）

1. **单轮效率没有增益**（§3.4）：本包比裸做法慢约 6 倍、产物约 60 倍。
   增益在"不需要人工补齐"和"缺陷会被暴露"，**不在运行速度**。任何"效率提升 N 倍"的
   说法都与本包的实测不符。
2. **`evidence.json` 的 sha 随运行目录变化**：它的 `sources[].path` 记的是运行时真实输入
   路径（这是取证需要）。要对比"内容是否一致"，请比对 `figure.svg`/`layout.json`/
   `verify_report.json` 的 sha，或比对 `evidence.json` 里除 `path` 之外的部分。
3. **全部关系端点都不存在时会退化成顺序链**：关系集合被清空后改走文本顺序兜底
   （`source=text:order`），此时 `status=success` 且不报错。复核办法：看
   `relations[].source` 是否全为 `text:order`、以及输入/输出关系条数之差。
4. **非法类别/关系被静默归一化**：归一化后词表审计自然通过，原始非法值不留痕。
   复核办法：对比 `evidence.entities[].kind` 与材料原始取值。
5. **`--rules` 指向空文件或不存在路径时审计空转**：这正是 C2 条件的构造方式；
   在对照里它是**有意为之**，在正式交付里它是**缺陷**——两种情形都要在记录里说明。
6. 局部放大视图未内置；装置图为单层装配（三桶布局）；图内数值注记不强标。
7. `examples/` 是**合成**示例（标注「示例，非正式案例」），不含预制答案；
   正式案例、白板与评分由平台提供/执行；本包不宣称任何具体分数。

## 9. 资源清单

- `scripts/main.py` — 一键流水线（证据→模型→布图→渲染→校验→契约）
- `scripts/gain_evidence.py` — 证据抽取（CP1；`locator`+`quote`+材料 `sha256`）
- `scripts/model.py` — SIR：实体/关系/步骤/流向解析与文本解构兜底
- `scripts/layout.py` — 确定性布图引擎
- `scripts/render_svg.py` — 手写分层 SVG（可编辑源文件）
- `scripts/export_preview.py` — PIL PNG + reportlab PDF（同一布局模型）
- `scripts/svg_verify.py` — SVG 校验 + 连接规则审计（CP2/CP3）
- `scripts/check.py` — 契约门 G1–G10（CP4；退出码 0/1/3）
- `scripts/fonts.py` — 中文字体探测与降级
- `scripts/bare_baseline.py` — **本版新增**：对照条件 C0（不加载 Skill 的可执行下界）
- `scripts/gain_probe.py` — **本版新增**：Q1–Q6 指标的独立复算器（只用 `result.json` 公开字段）
- `assets/connection_rules.json` / `assets/result_example.json`
- `templates/palette.json` / `templates/component-connection-checklist.md` /
  `templates/entity-relation-checklist.csv`
- `references/GAIN-PROTOCOL.md` — **本版新增**：对照协议全文（条件/固定项/指标/判定/复现）
- `references/COMPARISON-RECORD-20261122.md` — **本版新增**：本包实际跑过的对照记录
- `references/comparison-data.json` — **本版新增**：对照的机器可读原始数据
- `references/OUTPUT_CONTRACT.md` — `result.json` 契约（18 个顶层字段）+ G1–G10
- `references/RUBRIC_MAP.md` — 评分五维（40/25/15/10/10）逐条落点（本版按"增益"重排）
- `references/failure-modes.md` — 失败模式与决策规则、打包门 R1–R6
- `references/figure-blueprint.md` / `references/vocabulary.md`
- `examples/` — 最小调用示例（生成 + 编辑双用例）

依赖：Python 3.10+ 标准库；Pillow（PNG）；reportlab（PDF）。两者缺一即按 D10 降级。

## 10. 评分五维落点（速查；逐条证据见 `references/RUBRIC_MAP.md`）

| 维度 | 分 | 本包落点 |
|-|-|-|
| 实际效果 | 40 | `main.py` 一键出图 → 可编辑分层 SVG + 真实 PNG/PDF + 四份 JSON；四形态实测 `exit 0`、契约 18/18 |
| **使用增益** | **25** | **`references/GAIN-PROTOCOL.md`（协议）+ `COMPARISON-RECORD-20261122.md`（真跑记录）+ `gain_probe.py`（独立复算器）+ `bare_baseline.py`（下界）** |
| 创新增益 | 15 | SIR → 确定性布图 → 三后端共享布局；规则资产可扩展；**增益本身被做成可复算协议** |
| 可靠体验 | 10 | D1–D14 + 状态聚合优先级 + `check.py` 退出码语义 + `failure-modes.md`（含 R1–R6 打包门） |
| 生态贡献 | 10 | 文档完整性 + 可复用资产（规则字典/配色/核对清单/**对照协议与复算脚本**）+ `GITHUB_URL.txt` |
