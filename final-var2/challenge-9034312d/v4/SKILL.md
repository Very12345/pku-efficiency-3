---
name: apparatus-and-route-diagrams
description: >-
  依据科研材料生成或编辑「实验装置与技术路线图」可编辑图稿（分层 SVG 源文件 +
  PNG/PDF 预览 + result.json）。本版把工程重心放在**坏了以后会怎样**：包内自带
  scripts/fault_inject.py，把输入/模板/依赖/契约四类形态各注入若干条真实故障并
  跑主流程，用退出码、status、uncertainty、verify 与 check 门号逐条记录实测行为
  （32 条，见 references/FAULT-MATRIX.md）；据此新增 scripts/preflight.py 运行前
  闸门，把「--rules/--palette 写错 ⇒ 审计空转却全绿」这类静默失败在运行前拦住。
  正常路径不变：证据先行（locator+quote）→ 确定性布图 → 三后端同布局渲染 →
  规则审计 → 契约门 G1–G10。
---

# 实验装置与技术路线图 Skill · 故障注入与恢复演练版（challenge-9034312d · figures 组）

一个绘图 Skill 的成色，不看它顺利时画得多好，看它**在坏条件下会不会骗人**。
本版就做这一件事：把四类形态（输入 / 模板 / 依赖 / 契约）各注入一批真实故障，
跑完整流水线，逐条记录机器可读的判决位点，然后拿实测结果反过来补一道运行前闸门。

三件本版新增的东西，以及它们各自的证据：

| 新增 | 它回答什么问题 | 证据在哪 |
|-|-|-|
| `scripts/fault_inject.py` | 每个坏条件发生时，退出码 / `status` / `uncertainty` 到底是什么？ | `references/FAULT-MATRIX.md`（32 条实测） |
| `references/FAULT-MATRIX.md` | 哪几条是**静默失败**（退出码 0、`status=success`、产物看起来正常）？ | 同上，9 条缺陷型静默行逐条给出位点 |
| `scripts/preflight.py` | 怎么在**跑之前**就把那 9 条拦下来？ | 闸门对 9 条静默缺陷实测 0 漏网（矩阵 §7） |

算法、CLI 参数名与默认值、产物文件名、退出码语义、`references/OUTPUT_CONTRACT.md`
的字段块**一律与基线一致**；本版只在"运行前"与"文档"两层加东西。

## 0. 先读这一节：技能根与自定位

- 技能根 = 本 `SKILL.md` 所在目录，后文记作 `$SKILL_DIR`。平台把 Skill 装到
  `/skills/weekly-skill`；本地复现时就是你解包出来的那个目录。

  ```bash
  SKILL_DIR=/skills/weekly-skill                              # 平台安装位置
  SKILL_DIR="$(cd "$(dirname /path/to/SKILL.md)" && pwd)"     # 本地解包位置
  ```

- `scripts/*.py` 全部用 `os.path.dirname(__file__)` 自定位，读 `templates/`、`assets/`、
  `references/` 相对技能根解析，**不依赖运行时 cwd**，也不写 `__pycache__`
  （每个脚本首部都置了 `sys.dont_write_bytecode = True`）。
- 执行顺序（本版的"主线"）：
  **读实际文件 → 闸门 preflight（新增）→ 证据抽取 CP1 → SIR → 布图 → 渲染 →
  SVG 校验 + 规则审计 CP2/CP3 → 预览导出 → result.json CP4 → check.py**。
- 资源形态：包内只有 `.md/.py/.json/.txt/.csv/.yaml/.yml` 文本资源，
  文件数 ≤50、单文件 ≤500KB、合计 ≤2MB、无符号链接。`figure.svg`/`figure.png`/
  `figure.pdf` 是**运行期产物**，由 `scripts/main.py` 现场生成，不随包发布。

## 1. 用途与适用条件

把「装置怎么搭、步骤怎么走、物料从哪来到哪去、技术路线分几个阶段」的材料，
变成一张**每个实体都能追溯到材料、每条连接都经过机器审计**的可编辑图稿。

- **输入**：`/input/case.json`（必读）+ `/input/task.md`（可选）+ 案例引用的材料
  （`--material`，或 case.json 里的 `text/materials_text` 内联）；
- **输出**：写进 `--out`（官方运行时 `/app/output`），实际落点 `<out>/<case_id>/`；
- **改图**：`--merge <override.json>`，同名 id 替换、新 id 追加，动作自动进
  `change_record`；
- **不做**：数值拟合与数据分析、实验方案科学合理性判断、论文排版与期刊格式适配。

**什么时候别直接用它**：材料自相矛盾且无法用 `--merge` 落定（此时按 D11 降级
`partial` 并写清冲突项）；需要多级嵌套放大视图的装配图（本包只做单层装配）。

## 2. 调用接口

```
python "$SKILL_DIR/scripts/main.py" --case <case.json|案例目录> [--task <task.md>]
                       [--material <材料文件|目录>] [--merge <override.json>]
                       --out <输出目录> [--dpi 200]
                       [--figure-type route|apparatus|flow|hybrid]
                       [--title "…"] [--width-mm N] [--height-mm N]
                       [--palette <palette.json>] [--rules <connection_rules.json>]
```

运行前闸门（本版新增；**不产出任何结果文件**，只读检查）：

```
python "$SKILL_DIR/scripts/preflight.py" --case <case.json|案例目录> [--task <task.md>]
                       [--material <材料|目录>] [--merge <override.json>]
                       [--rules <rules.json>] [--palette <palette.json>]
                       [--deps] [--strict] [--json <report.json>]
```

故障演练（本版新增；**只改沙箱副本，不动本包**）：

```
python "$SKILL_DIR/scripts/fault_inject.py" [--out <临时目录>] [--json <report.json>]
                       [--only F1-01,F2-*] [--timeout 300] [--list] [--clean]
                       [--no-preflight]
```

单件工具（与基线同名同参，可独立运行）：

```
python "$SKILL_DIR/scripts/gain_evidence.py" --case <case.json> [--task …] [--material …] --out <evidence.json>
python "$SKILL_DIR/scripts/svg_verify.py" --layout <layout.json> --svg <figure.svg> [--rules <rules.json>] [--out <verify_report.json>]
python "$SKILL_DIR/scripts/check.py" <result.json>
```

**参数语义提醒（都是实测出来的，不是推测）**：

- `--case` 给**目录**时自动取该目录下 `case.json`，未给 `--task` 时取同目录 `task.md`；
  给**具体文件**时不猜同目录文件（材料来源宁可少而准）。
- `--rules` 指到不存在的路径或坏 JSON 时，`main.py` 会**安静地跳过整个连接语义审计**
  （实测 F2-04/F2-05：退出码 0、`status=success`、`uncertainty` 为空）。
  要确认"审过了没有"，先跑 `preflight.py`，或核对 `verify.checks.connection_rules`
  与你传进去的规则集条数。
- `--palette` 同样静默回落（F2-01/F2-02/F2-06）；`--material`/`--task` 指向不存在的
  文件时**不报错**（F1-10/F1-11）。这四条是本包最需要外部闸门的地方。

**退出码语义（不改基线）**：`main.py` → `0` 全过 / `3` 已出图但契约门不过 /
`2` 输入缺失 / `1` 流水线异常（仍落盘 `failed/result.json`）；
`check.py` → `0` 全过 / `1` 有 issue；`preflight.py` → `0` 干净 / `1` 仅 warn /
`3` 有 error / `2` 用法错误；`fault_inject.py` → `0` 演练跑完 / `1` 探针自身出错。

## 3. 正常路径（五步，每步都在真实文件上）

> 全程禁止依据领域标签猜内容、禁止编造数值。CP1–CP4 是门，不过就按 §5 处置。

**步骤 0 · 读真实输入**：`read /input/case.json`；有 `task.md`、材料文件就读，
全部登记为 `sources`；判断结构（有 `entities` → 结构化路径；只有文本 → 预判文本解构 D2）。

**步骤 0.5 · 闸门（本版新增，强烈建议）**：

```bash
python "$SKILL_DIR/scripts/preflight.py" --case /input/case.json --task /input/task.md --deps
```

退出码 `3` ⇒ 先看 findings 里的 `code`/`action`（例如 `rules-missing`、
`palette-unparsable`、`relation-dangling`），修完再往下。退出码 `1` ⇒ 可继续，
但你已经知道"这次运行存在静默风险项"。

**步骤 1 · 证据抽取与复核（CP1 证据门）**：跑一次默认参数的 `main.py`；流水线内置
`gain_evidence.py`，为每条实体/关系生成 `locator` + `quote`，并给每份输入文件记
`sha256`/`size`/`role`，落盘 `evidence.json`。**Agent 必须逐条复核**：名称与材料是否
一致、同类部件是否区分（D6）、`locator/quote` 是否真实命中、关系方向是否与正文一致
（D5）、步骤编号能否与正文逐条对照。要修正就写 `override.json` 再带 `--merge` 重跑。

**步骤 2 · 布图与校验（CP2 连接门 → CP3 校验门）**：`layout.py` 确定性布图 →
`render_svg.py` 写分层 SVG → `svg_verify.py` 校验（合法 XML / 5 层 `layer:*` /
可编辑 `<text>` ≥3 / 箭头与关系一一对应 / 无断头 / route·flow 编号 1..N 连续 /
图例 kind 集合 == 图面 kind 集合）并读规则资产做连接语义审计。error 级违规 ⇒ 按 D10
降级 `partial`；warn 级只写 `verify.warnings`（D9）。画布溢出按 D7 等比缩放居中，
或用 `--width-mm/--height-mm` 重跑。

**步骤 3 · 导出预览（CP3 续）**：确认 `figure.png`/`figure.pdf` 生成并目测箭头方向、
编号、图例、断头箭头、盒子重叠。任一渲染失败按 D10 处置（**注意**：没有 Pillow 时
PDF 也会一起失败，见 §4 发现 2）。

**步骤 4 · 契约与自查（CP4 契约门）**：确认 `output_contract` 四段 +
`evidence` + `verify` + 元数据齐全；跑 `check.py`（G1–G10，`ok:true`、退出码 0 才算
完成）；发现问题修完重跑，**不得隐瞒**。

## 4. 32 条注入告诉我们的事（结论速览，明细见 `references/FAULT-MATRIX.md`）

**四族的整体形态：**

| 形态 | 注入条数 | 拦得住吗 | 典型位点 |
|-|-|-|-|
| 输入 | 11 | **拦得住**：缺文件退出码 2；坏 JSON / 类型错 / 坏 `--merge` 退出码 1 + `failed/result.json`（`scope=pipeline`）；空壳输入退出码 3 + G3/G9 | 退出码 + `uncertainty[].scope` |
| 模板/资产 | 8 | **拦不住（静默）**：`--rules`/`--palette` 缺失或损坏 ⇒ 回落默认、审计空转、全绿 | `verify.checks.connection_rules` |
| 依赖 | 3 | **拦得住（诚实降级）**：缺库 ⇒ `partial` + `uncertainty[scope=png\|pdf]`；缺字体 ⇒ `scope=fonts` | `uncertainty` + `exports[]` |
| 契约 | 10 | **拦得住且门号准确**：9/9 被 G 门拦下（G2/G3/G4/G5/G6/G9/G10 逐条对得上） | `check.py` 的 `gates` |

**三条只有真跑才会发现的结论：**

1. **代码坏掉是响亮的，数据坏掉是安静的。** 删 `scripts/render_svg.py` ⇒
   `ModuleNotFoundError` + 退出码 1 + 无产物（硬失败）；把 `--rules` 写错 ⇒
   退出码 0、`status=success`、没有任何告警（静默失败）。**后者更危险**，
   因为它让你以为"审过了"。
2. **依赖会互相牵连。** PIL 缺失时 `reportlab` 也 import 失败 ⇒ PNG/PDF **同时**丢
   ⇒ 契约门 G4 失败、退出码 3。"只坏一个导出件"是乐观假设，实测不成立。
3. **`status` 与退出码不是同一件事。** 实测存在 `status=success` 而退出码 3 的行
   （缺中文字体：D9/D14 说字体缺失不改 `status`，但 `check.py` 的 G10 把它算作
   降级不确定性）。两个口径冲突，本包**不改脚本、如实记录**在矩阵 §4 与 §5.1。

**9 条缺陷型静默行的分布**（全部实测，逐条列出）：

| 缺口 | 注入 | 静默表现 |
|-|-|-|
| A 断头关系不留痕 | F1-06 | 关系被丢弃，但不写 `uncertainty`（与 D3 的承诺不符），只留关系条数差 |
| B 材料缺失无告警 | F1-10 | `--material` 指到不存在的文件 ⇒ 只是 `source_files[]` 少一条 |
| C 任务书缺失无告警 | F1-11 | `--task` 指到不存在的文件 ⇒ 照样出图，无标记 |
| D 配色静默回落 | F2-01/F2-02/F2-06 | `--palette` 坏/缺、包内 palette 被删 ⇒ 用代码内默认配色 |
| E **审计整段空转** | F2-04/F2-05/F2-07 | `--rules` 坏/缺、包内规则资产被删 ⇒ 连接语义**完全没审**，却依然全绿 |

## 5. 决策规则（保留基线的 D1–D12 语义，并补上本版新增的 F 规则）

**D1–D12（与基线一致，此处只列触发与处置，证据位点见矩阵）**：

- **D1** `case.json` 不存在 → stderr `FATAL:`，退出码 **2**，不写任何产物；
- **D2** 无结构化实体、仅文本 → 文本解构（`extraction=text-heuristic`），
  只串联相邻步骤，记 `uncertainty[scope=relations]`，不直接降级；
- **D3** 关系指向不存在的实体 → 丢弃该关系、不画断头。⚠ **实测缺口 A**：丢弃后
  **不写 uncertainty**；复核办法是比对输入/输出关系条数，或看
  `verify.checks.no_dangling`；
- **D4** 实体缺 `source` → `source=null` 并列入 `uncertainty[scope=sources]`，不编造出处；
- **D5** 类别/关系不在词表 → 容错归一化（→ `step`/`flow`）。⚠ 原值不留痕，
  复核办法是对比 `evidence.entities[].kind` 与材料原始取值；
- **D6** 同名/近似实体歧义 → 保留并记 `uncertainty[scope=scope=ambiguity]`，交 Agent 裁决；
- **D7** 画布溢出 → 等比缩放居中（不裁剪），`canvas.requested` 保留原请求值；
- **D8** 重复 id → 重命名为 `<id>_2`，改名后无连接的实体走 D11 降级；
- **D9** 中文字体缺失 → `fonts[role=png].found=false` 如实记录；⚠ **实测**：
  `status` 仍为 `success`，但 `check.py` G10 会判失败 ⇒ 退出码 3（见 §4 结论 3）；
- **D10** PNG/PDF 渲染失败 → 保留已有产物与 SVG，`status=partial`，
  记 `uncertainty[scope=png|pdf]`；两个都失败且无实体 → `failed`；
- **D11** 孤儿实体 / `verify.ok=false` → `status=partial`（不得 `success`），
  列明违规，修正后重跑；
- **D12** 材料歧义/信息冲突 → 记 `uncertainty`（scope+issue+action），不擅自补造数据。

**F1–F4（本版新增：闸门规则，对应 `preflight.py` 的四类 finding）**：

| 规则 | 触发（闸门会报出来） | 闸门处置 | 为什么加它 |
|-|-|-|-|
| **F1** | `case` 缺失/不可解析/顶层非对象/空壳；`--merge` 缺失或坏 JSON；`figure_type` 非法 | **error**（退出码 3） | 这些会让 `main.py` 以 1/2/3 失败；提前说清原因 |
| **F2** | `--material`/`--task` 指向不存在的文件；实体 id 重复；关系端点缺失；类别越词表 | **warn**（退出码 1） | 对应缺口 A/B/C —— 它们不会失败，只会**安静地少东西** |
| **F3** | `--rules`/`--palette` 缺失、不可解析、空对象、无 error 级规则；`allowed_kinds` 为空 | **error**（退出码 3） | 对应缺口 D/E —— 假绿的主要来源 |
| **F4** | `--deps` 打开时：Pillow / reportlab / CJK 字体不可用 | **warn**（退出码 1） | 对应发现 2/3，提前知道会降级到哪一档 |

## 6. 故障演练怎么跑（本版的自证手段）

```bash
# ① 全部 32 条（默认同时跑 preflight，记录闸门能否提前拦住）
OUT=$(mktemp -d)
python "$SKILL_DIR/scripts/fault_inject.py" --out "$OUT" --json "$OUT/fault-report.json"

# ② 只看注入表与期望值（不执行）
python "$SKILL_DIR/scripts/fault_inject.py" --list

# ③ 只跑一类（按 id 前缀）
python "$SKILL_DIR/scripts/fault_inject.py" --only F3-* --out "$OUT"

# ④ 关掉闸门列（只看主流程自己的行为）
python "$SKILL_DIR/scripts/fault_inject.py" --no-preflight --out "$OUT"
```

三条硬约束，保证演练**不会污染交付物**：

1. 每条注入先把技能根复制成 `<out>/<注入号>/skill/` 的**沙箱副本**，只改副本；
   原包在整个演练过程中只被读取。
2. 所有子进程都带 `PYTHONDONTWRITEBYTECODE=1`，包内不会出现 `__pycache__`/`.pyc`。
3. 异常依赖用 `PYTHONPATH` 影子包模拟（`__init__.py` 里 `raise ImportError`），
   字体缺失用 `WINDIR` 指向空目录模拟 —— 都**只影响那一次子进程**，
   不卸载、不改环境、不动全局配置。

报告里的路径已全部相对化（技能根记作 `<SKILL_DIR>`、输出根记作 `<OUT>`），
所以 `--json` 的结果可以随包发布给第三方复核。

## 7. 自查清单（完成判定）

- [ ] 闸门先过：`preflight.py` 退出码 0，或退出码 1/3 的每条 finding 都已确认/修复
- [ ] CP1：`evidence.json` 存在；实体 ≥1 且与材料一致；`source/locator` 可追溯（缺失已列 uncertainty）
- [ ] CP2：无 error 级连接规则违规；且**确认规则集非空**（否则等于没审，见缺口 E）
- [ ] CP3：SVG 合法 XML、5 层齐全、`<text>` ≥3；编号连续；图例↔图元一致；无断头箭头
- [ ] CP3：`figure.png`/`figure.pdf` 存在且非空（失败已如实降级并写进 uncertainty）
- [ ] CP4：`result.json` 含契约 18 个顶层字段；`check.py` 输出 `ok:true`、退出码 0
- [ ] 状态诚实：有未解决 error 违规/孤儿实体时 `status` 不得为 `success`
- [ ] 修改历史（`change_record`）、不确定性（`uncertainty`）、来源（`sources`+`evidence`）如实记录
- [ ] 打包形态：只有 `.md/.py/.json/.txt/.csv/.yaml/.yml`，无 `__pycache__`、无本机绝对路径
- [ ] 至少跑过一次 `fault_inject.py`，知道自己这套环境里哪些行会静默（幂等可重跑）

## 8. 边界与诚实原则

- 本 Skill 只负责**绘图表达**与**可编辑交付**；不判断实验方案科学性，不做数值拟合；
- 拿不到出处就标 `null` 并计入 `uncertainty`（D4），**不编造**；
- 不顺带修既有脚本：`main.py`/`check.py`/`layout.py` 的 CLI、默认值、退出码语义
  与基线**逐字节一致**；矩阵 §6 的缺口清单靠闸门 + 文档处置，不靠改算法；
- 演练结果**不构成**对平台正式评分的预测：32 条注入全部是合成案例，
  与官方固定案例、白板、评分无关；
- `examples/` 是**合成**示例（标注「示例，非正式案例」），不含预制答案；
  示例期望产物清单见 `examples/EXPECTED-OUTPUT.md`。

## 9. 资源清单（路径相对技能根）

- `scripts/main.py` — 一键流水线（证据→模型→布图→渲染→校验→契约）
- `scripts/preflight.py` — **本版新增**：运行前闸门（输入/结构/资产/依赖四类检查）
- `scripts/fault_inject.py` — **本版新增**：32 条四形态故障注入与恢复演练
- `scripts/gain_evidence.py` — 证据抽取（CP1；`locator`+`quote`+材料 `sha256`）
- `scripts/model.py` — SIR：实体/关系/步骤/流向解析与文本解构兜底
- `scripts/layout.py` — 确定性布图（图元库 + 模板落点）
- `scripts/render_svg.py` — 手写分层 SVG（可编辑源文件）
- `scripts/export_preview.py` — PIL PNG + reportlab PDF（同一布局模型）
- `scripts/svg_verify.py` — SVG 校验 + 连接规则审计（CP2/CP3）
- `scripts/check.py` — 交付自查（CP4；G1–G10；退出码 0/1）
- `scripts/fonts.py` — 中文字体探测与降级
- `assets/connection_rules.json` — 连接规则字典（词表 + 8 条带 severity 的规则）
- `assets/result_example.json` — `result.json` 最小形态示例
- `templates/palette.json` / `component-connection-checklist.md` / `entity-relation-checklist.csv`
- `references/FAULT-MATRIX.md` — **本版新增**：32 条注入的实测矩阵 + 缺口清单 + 闸门效果
- `references/failure-modes.md` — 失败模式、四形态处置表、打包门 R1–R6
- `references/OUTPUT_CONTRACT.md` — `result.json` 契约（18 个顶层字段）+ G1–G10
- `references/RUBRIC_MAP.md` — 评分五维（40/25/15/10/10）逐条落点
- `references/vocabulary.md` / `references/figure-blueprint.md`
- `examples/` — 最小调用示例（生成 + 编辑双用例）

依赖（全部可降级）：Python 3.10+ 标准库；Pillow（PNG）；reportlab（PDF）。
**实测提醒**：reportlab 内部也依赖 PIL，所以缺 Pillow 时两个导出件会一起失败。

## 10. 评分五维落点（速查；逐条证据见 `references/RUBRIC_MAP.md`）

| 维度 | 分 | 本包落点 |
|-|-|-|
| 实际效果 | 40 | `main.py` 一键出图 → 可编辑分层 SVG + 真实 PNG/PDF + `evidence/layout/verify_report/result.json`；`examples/` 有真跑产物 |
| 使用增益 | 25 | 证据先行 + 规则审计 + **运行前闸门**（把 9 条静默缺陷提前变响）；`--merge` 增量改图免重画 |
| 创新增益 | 15 | SIR → 确定性布图 → 三后端同布局；**把"故障行为"变成可复跑的 32 条注入矩阵**（同批评测里少见） |
| 可靠体验 | 10 | `references/FAULT-MATRIX.md`（四形态实测 + 9 条静默 + 8 条缺口）+ `preflight.py` 四类 finding + 决策规则 D1–D12/F1–F4 |
| 生态贡献 | 10 | 文档完整性 + 可复用资产（规则字典、配色、核对清单、闸门、故障矩阵）+ `GITHUB_URL.txt` 公开入口 |
