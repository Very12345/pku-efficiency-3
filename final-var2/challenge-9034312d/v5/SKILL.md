---
name: apparatus-and-route-diagrams
description: >-
  依据科研材料生成或编辑「实验装置与技术路线图」可编辑图稿（分层 SVG 源文件 +
  PNG/PDF 预览 + result.json）。本版把能力放进**题集**里检验：包内自带 4 个合成案例
  （环境工程物质流向 / 分子生物四阶段路线 / 生物药筛路线 / 装置装配图），覆盖
  route·flow·apparatus 三种图类与三个难度层，并附 scripts/case_set_run.py 一键跑批
  ——逐案给出期望结构、可接受区间与实测值，再用 --text-only 探针测量「材料没有
  结构化实体时还剩多少」（实测实体保留率 0.20–0.67、关系保留率 0.00–0.36，
  装置图关系会全丢并降级 partial）。泛化边界写在 references/CASE-SET.md §6。
---

# 实验装置与技术路线图 Skill · 多案例泛化与题集版（challenge-9034312d · figures 组）

本版回答一个比"能不能画"更难的问题：**它在几个不同题材上都成立吗？换了题材会从哪里开始坏？**

为此本版做了三件事：

1. **把题集写进包里**：`examples/cases/` 两个**新题材**合成案例 + 基线自带两个示例，
   共 4 案，覆盖 `route` / `flow` / `apparatus` 三种图类与低/中/高三个难度层；
2. **把"跑题集"做成命令**：`scripts/case_set_run.py` 逐案跑 `main.py` + 收集判决位点，
   再与 `references/case-set.json` 的期望结构（区间 + 不变量 + 允许告警）比对，
   一次给出 PASS/FAIL 与偏差明细；
3. **把泛化损失量出来**：`--text-only` 把每案压扁成"只留一段文字"的版本再跑一遍，
   用两轮之差回答"结构化信息消失后还剩多少"——这是本版对「泛化到哪会失效」的
   **机器化回答**，不是主观评价。

算法、CLI 参数名与默认值、产物文件名、退出码语义、`references/OUTPUT_CONTRACT.md`
的字段块**一律与基线一致**；本版只在"案例集 + 跑批"这一层加东西。

## 0. 技能根与自定位（先读）

- 技能根 = 本 `SKILL.md` 所在目录，后文记作 `$SKILL_DIR`；平台安装位置是
  `/skills/weekly-skill`，本地复现时就是你解包出来的目录。

  ```bash
  SKILL_DIR=/skills/weekly-skill
  SKILL_DIR="$(cd "$(dirname /path/to/SKILL.md)" && pwd)"
  ```

- `scripts/*.py` 全部 `os.path.dirname(__file__)` 自定位，读 `templates/`、`assets/`、
  `references/` 相对技能根解析，**不依赖运行时 cwd**，也不写 `__pycache__`
  （每个脚本首部都置 `sys.dont_write_bytecode = True`）。
- 主线顺序：**读 file(s) → gain_evidence（CP1）→ model(SIR) → layout →
  render_svg → svg_verify（CP2/CP3）→ export 预览 → result.json（CP4）→ check**。
- 资源形态：只含文本资源（`.md/.py/.json/.txt/.csv/.yaml/.yml`），≤50 文件、
  单文件 ≤500KB、合计 ≤2MB、无符号链接；`figure.svg/png/pdf` 由 `main.py` 运行时生成。

## 1. 题集（本版核心，4 案 / 三种图类 / 三个难度层）

| # | case_id | 题材 | 图类 | 难度 | 实体/关系 | 考什么 |
|-|-|-|-|-|-|-|
| **C-1** | `mbr-wastewater-flow-01` | 环境工程 · 市政污水处理 | `flow` | 中 | 14 / 14 | 物质流向：分流、合流、回流、两条废料支路、出水两路 |
| **C-2** | `dtms-stage-route-01` | 分子生物学 · CRISPRi 全基因组筛选 | `route` | 高 | 18 / 18 | 阶段路线：4 阶段 + 2 里程碑 + 依赖方向 + 返工回流 + 编号逐条对照 |
| C-3 | `demo-biotech-route-01` | 分子生物学 · CRISPR 文库药筛 | `route` | 低 | 10 / 9 | 最简线性主链（基线示例，低难度锚点） |
| C-4 | `apparatus-spec-01` | 实验装置 · 冷冻干燥机 | `apparatus` | 低 | 6 / 5 | 单层装配 + 三桶布局 + 装置图特有限制（基线示例） |

C-1 / C-2 是**本版新增**（`examples/cases/<case_id>/{case.json,task.md}`），
C-3 / C-4 是基线自带示例，登记进题集是为了覆盖"最简形态"与"装置图"两个锚点。
逐案的输入形态、期望产出结构、可接受区间、不变量与实测值见
**`references/CASE-SET.md`**；机器可读的期望表是 **`references/case-set.json`**。

## 2. 调用接口

主流程（与基线同名同参）：

```
python "$SKILL_DIR/scripts/main.py" --case <case.json|案例目录> [--task <task.md>]
                       [--material <材料文件|目录>] [--merge <override.json>]
                       --out <输出目录> [--dpi 200]
                       [--figure-type route|apparatus|flow|hybrid]
                       [--title "…"] [--width-mm N] [--height-mm N]
                       [--palette <palette.json>] [--rules <connection_rules.json>]
```

题集跑批（本版新增）：

```
python "$SKILL_DIR/scripts/case_set_run.py" [--cases-root examples/cases]
                       [--out <目录>] [--json <report.json>]
                       [--only <case_id>] [--text-only] [--timeout 300] [--list]
```

单件工具（与基线同名同参，可独立运行）：

```
python "$SKILL_DIR/scripts/gain_evidence.py" --case <case.json> [--task …] [--material …] --out <evidence.json>
python "$SKILL_DIR/scripts/svg_verify.py" --layout <layout.json> --svg <figure.svg> [--rules <rules.json>] [--out <verify_report.json>]
python "$SKILL_DIR/scripts/check.py" <result.json>
```

**参数语义**：

- `--case` 给**目录**时自动取该目录下 `case.json`，未给 `--task` 时取同目录 `task.md`；
  给**具体文件**时不猜同目录文件（材料来源宁可少而准）。题集的每个案例目录都按此约定布置，
  所以 `--case examples/cases/<case_id>` 一条命令即可跑通；
- `--merge` 用于编辑既有图稿（同名 id 替换、新 id 追加，动作写入 `change_record`）；
- `--width-mm/--height-mm` 覆盖画布（画布是布局输入的一部分，改它会改变 `spec_sha16`）；
- `--rules` 换一套连接规则（改 JSON 即改审计结论）。⚠ **实测**：指到不存在的路径或
  坏 JSON 时，审计会**静默整体跳过**（退出码仍 0、`verify.ok` 仍可能为 true）；
  正式交付前请确认规则文件存在且 `rules[]` 非空；
- `--palette` 换配色；缺失/损坏时同样静默回落代码内默认配色。

**退出码语义**：`main.py` → `0` 全过 / `3` 已出图但契约门不过 / `2` 输入缺失 /
`1` 流水线异常（仍落盘 `failed/result.json`）；`check.py` → `0` 全过 / `1` 有 issue；
`case_set_run.py` → `0` 全部案例 PASS / `1` 有案例 FAIL / `2` 用法错误。

## 3. 执行步骤（跑一个案例）

**步骤 0 · 读实际输入**：`read /input/case.json`；有 `task.md`、材料文件就读，全部
登记为 `sources`；判结构（有 `entities` → 结构化路径；只有文本 → 预判文本解构 D2）。

**步骤 1 · 证据抽取与复核（CP1 证据门）**：跑一次默认参数的 `main.py`；内置
`gain_evidence.py` 为每条实体/关系生成 `locator` + `quote`，并给每份输入文件记
`sha256`/`size`/`role`。**Agent 必须逐条复核**：名称与材料是否一致、同类部件是否区分
（D6）、`locator/quote` 是否真实命中、关系方向是否与正文一致（D5）、步骤编号能否与
正文逐条对照。要修正就写 `override.json` 再带 `--merge` 重跑。

**步骤 2 · 布图与校验（CP2 连接门 → CP3 校验门）**：`layout.py` 确定性布图 →
`render_svg.py` 写分层 SVG → `svg_verify.py` 校验（合法 XML / 5 层 `layer:*` /
可编辑 `<text>` ≥3 / 箭头与关系一一对应 / 无断头 / route·flow 编号 1..N 连续 /
图例 kind == 图面 kind）并读规则资产做连接语义审计。error 级违规 ⇒ 按 D10 降级
`partial`；warn 级只写 `verify.warnings`（D9）。画布溢出按 D7 等比缩放居中，
或用 `--width-mm/--height-mm` 重跑。

**步骤 3 · 导出预览（CP3 续）**：确认 `figure.png`/`figure.pdf` 生成并目测箭头方向、
编号、图例、断头箭头、盒子重叠。任一渲染失败按 D10 处置（缺 Pillow / reportlab /
中文字体都会走到这一档，并写入 `uncertainty[].scope`）。

**步骤 4 · 契约与自查（CP4 契约门）**：`check.py` 的 G1–G10 全过（`ok:true`、退出码 0）
才算完成；发现问题修完重跑，**不得隐瞒**。

**步骤 5 · 题集跑批（本版新增，改完包或换题材后必跑）**：

```bash
python "$SKILL_DIR/scripts/case_set_run.py" --out <临时目录> --text-only
# 退出码 0 = 4 案全 PASS；每案的偏差会逐条打印出来
```

## 4. 逐案实测结果（4 案真跑，一次运行的数据）

| case_id | 图类 | 难度 | 退出码 | `status` | 实体 | 关系 | `verify.ok` | 告警 | `spec_sha16` | 结论 |
|-|-|-|-|-|-|-|-|-|-|-|-|
| `apparatus-spec-01` | apparatus | 低 | 0 | `success` | 6 | 5 | true | — | `4603787adcb287d7` | **PASS** |
| `demo-biotech-route-01` | route | 低 | 0 | `success` | 10 | 9 | true | — | `e04e9d47e8ca0099` | **PASS** |
| `dtms-stage-route-01` | route | 高 | 0 | `success` | 18 | 18 | true | `recycle-review` | `cb33950dedb47795` | **PASS** |
| `mbr-wastewater-flow-01` | flow | 中 | 0 | `success` | 14 | 14 | true | `recycle-review` | `5b65c6612f7714e0` | **PASS** |

汇总：`cases=4 · passed=4 · failed=0`；四次运行契约门 G1–G10 **全部通过**
（`gates_false` 全为空），PNG 28.9–82.6 KB、PDF 3.9–5.4 KB，单案耗时 0.58–0.71 s。

**告警 ≠ 失败**：C-1/C-2 各带 1 条 `recycle-review`（回流需人工复核），这是规则的
设计行为 —— `status` 仍为 `success`，契约门仍全过。把"有告警"当成"不合格"是误读。

## 5. ★ 泛化到哪里会失效（实测量化）

`--text-only` 把每个案例压扁成只留 `text` 字段的版本重跑：

| case_id | 实体保留率 | 关系保留率 | 丢失的规则告警 | 文本版 `status` |
|-|-|-|-|-|
| `apparatus-spec-01` | 0.667（6→4） | **0.000（5→0）** | — | **`partial`** |
| `demo-biotech-route-01` | 0.200（10→2） | 0.111（9→1） | — | `success` |
| `dtms-stage-route-01` | 0.389（18→7） | 0.333（18→6） | **`recycle-review`** | `success` |
| `mbr-wastewater-flow-01` | 0.429（14→6） | 0.357（14→5） | **`recycle-review`** | `success` |

三条结论（逐条对应上表某一行）：

1. **结构化输入是主航道**：文本解构只串联相邻步骤，分流/合流/回流/依赖/里程碑整体丢失。
   C-1、C-2 的核心考点（污泥回流、返工回流）在文本形态下**完全消失**——
   `recycle-review` 告警不再出现，说明回流关系根本没被识别。
2. **装置图在文本形态下最危险**：C-4 的 5 条关系**全部丢失**，4 个孤实体触发
   `orphan_entities`，`status` 由 `success` 掉到 **`partial`**。
   ⇒ 给装置图时不要只喂一段文字，至少给"部件清单 + 接口/连接清单"。
3. **输入退化不会自动降级状态**：C-3 在文本形态下只剩 2 实体 1 关系，却仍报
   `success`；只有出现孤儿实体时（C-4）才降级。复核办法：同时看 `extraction`
   （应为 `text-heuristic`）与实体数是否与材料规模相称。

**其他已知边界**（未实测，如实标注）：实体数 > 24 或阶段数 > 5 未测；多级嵌套装配与
局部放大视图**不支持**；图内数值注记不强制渲染；非 UTF-8 / 超长材料 / 并发运行未测；
平台固定 3 个案例不可见，本包**不预测**其表现。

## 6. 决策规则（与基线一致；本版只补"案例集相关"两条）

- **D1** `case.json` 不存在 → stderr `FATAL:`，退出码 **2**，不写任何产物；
- **D2** 无结构化实体、仅文本 → 文本解构（`extraction=text-heuristic`），
  记 `uncertainty[scope=relations]`；**后果见 §5**：关系大量丢失，不自动降级；
- **D3** 关系指向不存在的实体 → 丢弃该关系、不画断头（⚠ 实测不留 uncertainty）；
- **D4** 实体缺 `source` → `source=null` 并列入 `uncertainty[scope=sources]`，
  且会让 `verify.checks.entity_source_coverage=false` ⇒ 可能连带拖垮 `verify.ok`；
- **D5** 类别/关系不在词表 → 容错归一化（→ `step`/`flow`），原值不留痕；
- **D6** 同名/近似实体歧义 → 保留并记 `uncertainty[scope=ambiguity]`，交 Agent 裁决；
- **D7** 画布溢出 → 等比缩放居中（不裁剪），`canvas.requested` 保留原请求值；
- **D8** 重复 id → 重命名为 `<id>_2`，改名后无连接的实体走 D11 降级；
- **D9** 中文字体缺失 → `fonts[role=png].found=false` + `uncertainty[scope=fonts]`；
- **D10** PNG/PDF 渲染失败 → 保留已有产物与 SVG，`status=partial`，
  记 `uncertainty[scope=png|pdf]`；两个都失败且无实体 → `failed`；
- **D11** 孤儿实体 / `verify.ok=false` → `status=partial`（不得 `success`）；
- **D12** 材料歧义/信息冲突 → 记 `uncertainty`（scope+issue+action），不擅自补造数据。

**本版新增两条（案例集维护纪律）**：

| 规则 | 触发 | 处置 |
|-|-|-|
| **D13** | 新增/修改了案例，但 `references/case-set.json` 没有对应条目 | 跑批时该案会被标 `without_expectation`（不判 FAIL，但**等于没验收**）；必须补登记：`case_path` + 期望区间 + `allowed_warnings`/`forbidden_errors` |
| **D14** | 某案的实测**结构性丢失**（少回流、少终点、方向反）但区间比对仍 PASS | 说明区间写得太松：把该结构写成 `forbidden_errors` 里的一条规则名（或收紧实体/关系下限），不要靠人眼守 |

## 7. 自查清单（完成判定）

- [ ] CP1：`evidence.json` 存在；实体 ≥1 且与材料一致；`source/locator` 可追溯
- [ ] CP2：无 error 级连接规则违规；且**确认规则集非空**（否则等于没审）
- [ ] CP3：SVG 合法 XML、5 层齐全、`<text>` ≥3；编号连续；图例↔图元一致；无断头箭头
- [ ] CP3：`figure.png`/`figure.pdf` 存在且非空（失败已如实降级并写进 uncertainty）
- [ ] CP4：`result.json` 含契约 18 个顶层字段；`check.py` 输出 `ok:true`、退出码 0
- [ ] 题集：`case_set_run.py` 退出码 0（4 案全 PASS），没有 `without_expectation` 的案子
- [ ] 泛化：若目标题材只能提供文本，先跑 `--text-only` 看保留率，再决定是否需要
      Agent 先补结构化实体（否则回流/分流/依赖会丢）
- [ ] 修改历史（`change_record`）、不确定性（`uncertainty`）、来源（`sources`+`evidence`）如实记录
- [ ] 打包形态：只有 `.md/.py/.json/.txt/.csv/.yaml/.yml`，无 `__pycache__`、无本机绝对路径

## 8. 边界与诚实原则

- 只负责**绘图表达**与**可编辑交付**；不判断实验方案科学性，不做数值拟合；
- 拿不到出处就标 `null` 并计入 `uncertainty`（D4），**不编造**；
- 本版新增的全部数字都来自 `scripts/case_set_run.py` 的一次现场运行，可逐条复跑；
- 题集是**合成案例**（`examples/` 与 `examples/cases/` 均标注「示例，非正式案例」），
  不含预制答案；正式案例、白板与评分由平台提供/执行；
- 本包**不宣称任何具体分数**，也不预测平台固定案例上的表现。

## 9. 资源清单（路径相对技能根）

- `scripts/main.py` — 一键流水线（证据→模型→布图→渲染→校验→契约）
- `scripts/case_set_run.py` — **本版新增**：题集跑批 + 期望结构比对 + 泛化损失测量
- `scripts/gain_evidence.py` — 证据抽取（CP1；`locator`+`quote`+材料 `sha256`）
- `scripts/model.py` — SIR：实体/关系/步骤/流向解析与文本解构兜底
- `scripts/layout.py` — 确定性布图（图元库 + 模板落点）
- `scripts/render_svg.py` — 手写分层 SVG（可编辑源文件）
- `scripts/export_preview.py` — PIL PNG + reportlab PDF（同一布局模型）
- `scripts/svg_verify.py` — SVG 校验 + 连接规则审计（CP2/CP3）
- `scripts/check.py` — 交付自查（CP4；G1–G10；退出码 0/1）
- `scripts/fonts.py` — 中文字体探测与降级
- `assets/connection_rules.json`（词表 + 8 条带 severity 的规则）/ `assets/result_example.json`
- `templates/palette.json` / `component-connection-checklist.md` / `entity-relation-checklist.csv`
- `references/CASE-SET.md` — **本版新增**：题集逐案说明（输入/期望结构/可接受区间/难度/实测）
- `references/case-set.json` — **本版新增**：题集期望表（机器可读；跑批的判据来源）
- `references/OUTPUT_CONTRACT.md` — `result.json` 契约（18 个顶层字段）+ G1–G10
- `references/RUBRIC_MAP.md` — 评分五维（40/25/15/10/10）逐条落点
- `references/failure-modes.md` — 失败模式、决策规则、打包门 R1–R6
- `references/vocabulary.md` / `references/figure-blueprint.md`
- `examples/cases/<case_id>/{case.json,task.md}` — **本版新增**两个不同题材的合成案例
- `examples/` — 基线自带示例与文本类运行产物

依赖：Python 3.10+ 标准库；Pillow（PNG）；reportlab（PDF）。
⚠ 实测：reportlab 内部也依赖 PIL，缺 Pillow 时 PNG 与 PDF 会**一起失败**。

## 10. 评分五维落点（速查；逐条证据见 `references/RUBRIC_MAP.md`）

| 维度 | 分 | 本包落点 |
|-|-|-|
| **实际效果** | **40** | **4 个案例（三种图类 / 三个难度层）全部真跑 PASS**；`case_set_run.py` 逐案给出实体/关系/门/ `spec_sha16`；期望写成"区间 + 不变量"而非定值 |
| 使用增益 | 25 | 证据先行 + 规则审计 + `--merge` 增量改图；**新增**：跑批一次发现"某题材是否需要结构化输入"（`--text-only` 保留率） |
| 创新增益 | 15 | SIR → 确定性布图 → 三后端同布局；**新增**：题集 = 可执行判据（`case-set.json`）+ 泛化损失的机器化测量 |
| 可靠体验 | 10 | 决策规则 D1–D12 + 新增 D13/D14（案例集维护纪律）；`references/failure-modes.md`（含 R1–R6） |
| **生态贡献** | **10** | **题集可搬走**：复制两个文件即成一个新案例、登记一行即被批量验收；`CASE-SET.md §7` 给出换题材/加判据/测泛化三步 |
