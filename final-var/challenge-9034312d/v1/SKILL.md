---
name: apparatus-and-route-diagrams
description: >-
  依据科研材料生成或编辑「实验装置与技术路线图」可编辑图稿（分层 SVG 源文件 +
  PNG/PDF 预览 + result.json），保证实体可追溯、连接与顺序成立、可被打开修改并复跑。
  覆盖装置结构（装置清单/装配说明）、步骤顺序（工艺描述→编号流程图）、材料流向
  （分流/合流/回流/废料出口）与技术路线（阶段与里程碑）四类绘图任务；本版把
  「异常怎么判、判完怎么办」写成 20 条可执行决策规则 D1–D20 与 24 项失败分支表，
  每条规则绑定一个可观测证据位点（退出码 / status / uncertainty.scope / verify.errors /
  check 门号），让同一个异常在任何一次运行里都得到同一种处置，并把裁决权交给机器可判的门。
---

# 实验装置与技术路线图 Skill · 决策显性化版（challenge-9034312d · figures 组）

本 Skill 处理同一类问题：把「装置怎么搭、步骤怎么走、物料从哪来到哪去、技术路线分几个
阶段」的文本材料，变成一张可编辑、可追溯、可复核的科研图稿。它的价值不在画得漂亮，而在
**每一次运行都走同一套判决**：材料里出现歧义、缺口、冲突或非法结构时，处置动作不随
当时心情变化，而是由 **D1–D20 决策规则**指定、由 **CP1–CP4 四道门**验证、由
**可观测证据位点**（退出码、`status`、`uncertainty[].scope`、`verify.errors[]`、G 门号）
留下凭据。

本版（决策显性化）相对基线的实质改动：

- 决策规则由 12 条扩到 **20 条**，并**按失败域分组**（输入域 D1–D4 / 结构与连接域
  D5–D11 / 导出域 D12–D14 / 契约域 D15–D18 / 状态域 D19–D20），不再混在一张表里；
- 每条规则给全 **触发 / 动作 / 失败时的降级 / 证据位点** 四列 —— 缺了最后一列，规则就
  只是建议，不是规则；
- 新增 **失败分支表**（24 行，`references/failure-modes.md §2`），把五类异常
  （材料异常 / 模板缺失 / 依赖缺失 / 契约四形态 / 状态不一致）逐一映射到规则号与降级后果；
- 新增 **状态聚合优先级**（§4）与 **契约四形态的缺省填充约定**（§7）：同一份结果上多个
  缺陷同时出现时，`status` 只有一个取值，本版把谁压谁写死；
- 新增 `references/DECISION-CASES.md`：20 个**可复跑的决策用例**，每个给出输入形态、
  期望判决与**实测观测值**，供第三方直接验收本包的决策行为。

算法与 CLI 接口未变：`scripts/*.py` 的入口、参数名与产物名与基线一致。

## 0. 三分钟上手

1. **技能根**（后文记作 `$SKILL_DIR`）= 本 `SKILL.md` 所在目录。平台把本 Skill 安装到
   `/skills/weekly-skill`；本地复现时它是你解包出来的那个目录。
2. **一次生成**：

   ```bash
   python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md \
     --out /app/output
   ```

3. **看两个数字**：退出码（`0` 全过 / `3` 已出图但契约门不过 / `2` 输入缺失 /
   `1` 流水线异常）与 `result.json` 的 `status`（`success|partial|failed`）。
   两者由 §4 的聚合规则唯一决定，不由脚本临时判断。
4. **出事时查表**：按 §6 的规则号去 `references/failure-modes.md §2` 找失败分支，
   那里写明该异常会不会污染交付物、要不要重跑。

版本号 `2.1.0`（见 `scripts/main.py` 的 `execution.skill_version`）。

## 1. 用途与适用条件

**做什么**：材料 → 证据链（每个实体/关系带 `locator`+`quote`）→ 结构化中间表示（SIR）
→ 确定性布图 → 可编辑分层 SVG → PNG/PDF 预览 → 机器校验 → `result.json`。
**输入**：`/input/case.json` 必读；`/input/task.md` 与案例引用的材料文件可选
（`--material`，或 case.json 的 `text/materials_text` 内联）。
**输出**：写进 `--out`（官方运行时为 `/app/output`），实际落点 `<out>/<case_id>/`。
**编辑既有图稿**：`--merge <override.json>`，同名 id 替换、新 id 追加，动作自动进
`change_record`。

**不做什么**：不做数值拟合与数据分析；不判断实验方案本身的科学合理性；不做论文排版
与期刊投稿格式适配。

**什么时候不适合直接用它**：材料本身自相矛盾且无法用 `--merge` 落实（此时按 D16 降级
`partial` 并写清冲突项）；需要局部放大视图的多级嵌套装配（本包只做单层装配，见 §10）。

## 2. 调用接口

```
python "$SKILL_DIR/scripts/main.py" --case <case.json|案例目录> [--task <task.md>]
                       [--material <材料文件|目录>] [--merge <override.json>]
                       --out <输出目录> [--dpi 200]
                       [--figure-type route|apparatus|flow|hybrid]
                       [--title "…"] [--width-mm N] [--height-mm N]
```

- `--case` 给**目录**时自动取该目录下 `case.json`，并在未给 `--task` 时取同目录
  `task.md`（平台输入约定就是这一对）；给**具体文件**时不猜同目录文件 —— 这条差异是
  故意的，材料来源宁可少而准（D4）。
- `--out` 默认 `./output`；`--dpi/--figure-type/--title/--width-mm/--height-mm/--palette/--rules`
  含义见 `--help`。

`scripts/*.py` 全部用 `os.path.dirname(__file__)` 自定位，读 `templates/`、`assets/`、
`references/` 一律相对技能根解析，**不依赖运行时 cwd**，也不写 `__pycache__`
（脚本首部已置 `sys.dont_write_bytecode = True`）。

产出（相对 `<out>/<case_id>/`，**全部在运行时生成**）：

| 文件 | 角色 | 判决相关 |
|-|-|-|
| `evidence.json` | 证据链：实体/关系 `locator`+`quote` + 材料 `sha256`/`size`/`role` | CP1 的证据位点 |
| `layout.json` | 布局模型：实体的 x/y/w/h、正交连线路径、图例、画布 | D8/D10 的位点 |
| `figure.svg` | 可编辑分层源文件：5 层 `layer:*`；`<text>` 真文本；实体组带 `data-*` | D13 的位点 |
| `figure.png` / `figure.pdf` | 渲染预览（PIL / reportlab，同一布局模型） | D12 的位点 |
| `verify_report.json` | 校验与规则审计：图层/文本/箭头/编号/图例/连接规则 + 确定性探针 | CP2/CP3 的位点 |
| `result.json` | 契约结果：18 个顶层字段（见 `references/OUTPUT_CONTRACT.md`） | CP4 的位点 |

> `figure.svg` / `figure.png` / `figure.pdf` 是**运行期产物**，不随 Skill 包发布
> （平台只接受 UTF-8 文本资源）。缺 Pillow 或 reportlab 时按 D12 降级为 `partial`，
> 原因写进 `uncertainty`；SVG 源文件不受影响。

## 3. 执行步骤（每步都在真实文件上操作）

> 全程禁止依据领域标签猜内容、禁止编造数值。下文的 CP 是门，不过就按 §6 的 D# 处理，
> **不许绕过**。

### 步骤 0 · 读取真实输入（D1/D2 在此生效）
1. `read /input/case.json`；2. 有 `task.md` 就读，有材料文件就读，全部登记为 `sources`；
3. 判结构：有结构化 `entities` → 走结构化路径；只有文本 → 预判将走文本解构（D2）。

### 步骤 1 · 证据抽取与复核（CP1 证据门）
1. 跑一次默认参数的 `main.py`；流水线内置 `gain_evidence.py`，为每条实体/关系生成
   `locator` + `quote`，并把输入文件的 `sha256` 记为版本证据，落盘 `evidence.json`；
2. **Agent 必须逐条复核证据链**（这是 CP1 的判定对象）：
   实体名与材料是否一致、同类部件是否已区分（D7）、`locator/quote` 是否真实命中材料
   （拿不到就标 `null` 并计入 `uncertainty`，D4）、关系方向是否与正文一致（D5/D6）、
   步骤编号能否与正文逐条对照；
3. 需要修正时写一份 `override.json`（运行时创建，不随包发布）：
   `{"entities":[{id,...}],"relations":[{id,...}],"change_notes":[…]}`，带 `--merge` 重跑。

### 步骤 2 · 布图与校验（CP2 连接门 → CP3 校验门）
1. `layout.py` 确定性布图 → `layout.json`；
2. `render_svg.py` 写分层 SVG；随后 `svg_verify.py` 执行：SVG 合法 XML、5 层齐全、
   可编辑 `<text>` ≥3、实体组带 `data-entity/data-source`、箭头与关系一一对应、
   无断头箭头、route/flow 编号 1..N 连续、图例 kind 集合 == 图面 kind 集合，以及
   **连接规则审计**（类别/关系词表、`sequence` 只连步骤、`connect` 至少一端为结构件、
   装置图物料不作流向终点、回流需复核）。error 级违规 ⇒ 按 D18 降级 `partial`，
   warn 级只提示复核（D10）；
3. 画布溢出或文字折行异常 → 按 D8 调整；
4. 复杂图可在 Inkscape 微调，但改动必须补进 `change_record`（D20，诚实优先）。

### 步骤 3 · 导出（CP3 续）
确认 `figure.png`/`figure.pdf` 生成并打开目测：箭头方向、编号、图例、断头箭头、盒子重叠。
任一渲染失败按 D12 处置。

### 步骤 4 · 写 `result.json` 并自查（CP4 契约门）
1. 确认 `output_contract` 四段（`editable_sources`/`exports`/`data_mapping`/
   `element_traceability`）+ `evidence` + `verify` + 元数据字段齐全；
2. `python "$SKILL_DIR/scripts/check.py" <result.json>` → G1–G10 全过、`ok: true`、
   退出码 0 才算完成；
3. 自查发现的问题按 §6 的 D# 修复后重跑；**不得隐瞒**（D18/D19）。

## 4. 状态聚合优先级（同一份结果上多个缺陷同时出现时）

`status` 是**单一取值**，所以必须先定谁压谁。本 Skill 按下列顺序遍历，命中即停：

| 序 | 条件 | 结果 |
|-|-|-|
| 1 | 输入缺失 / 不可解析 / 空壳（无实体且无文本） | `failed` |
| 2 | PNG 与 PDF 双双失败，且实体集合为空 | `failed` |
| 3 | PNG 或 PDF 任一失败（D12） | `partial` |
| 4 | `verify.ok = false`（存在 error 级规则违规，D18） | `partial` |
| 5 | `uncertainty` 中存在 `scope=orphan_entities`（D6） | `partial` |
| 6 | 以上都不命中 | `success` |

**注意两处容易误判的地方**：
① `scope=sources`（实体缺出处）与 `scope=relations`（文本解构兜底）**不单独触发降级** ——
它们记录事实、供 Agent 复核，但不代表交付物不可用；如果它们在本案例里同时伴随孤儿实体，
则由第 5 条承接。
② `warn` 级规则违规（`recycle-review`、`product-terminal`）**永不**改变 `status`，
只在 `verify.warnings` 里留痕。

## 5. 溯源与版本：图面元素 ↔ 输入材料的双向回溯

- `result.json.evidence.items[]`：每条 `{id, type, ref, locator, quote}`，`ref` 指向
  `E*`/`R*`，即图面上的实体或箭头；条数应为实体数 + 关系数；
- `result.json.evidence.source_files[]`：每个输入文件的 `sha256`/`size`/`role` ——
  这一项让「用的是哪一版材料」可被第三方核对，而不是靠自述；
- `result.json.output_contract.data_mapping[]` 与 `element_traceability[]`：把
  `entity-<id>` / `arrow-<id>` 逐个映射到 `source` 与所在 `stage`；
- `result.json.checksum`：`sha256(case_id + 实体 id 序列 + 关系 id 序列 + svg sha)`，
  实体/关系集合一变它就变 —— 这是「编辑确实生效」的机器证据（`--merge` 前后对比）。

## 6. 决策规则 D1–D20（触发 → 动作 → 失败时的降级 → 证据位点）

### 6.1 输入域

| D# | 触发条件 | 动作 | 失败时的降级 | 证据位点 |
|-|-|-|-|-|
| D1 | `case.json` 不存在 | 打印 `FATAL:` 到 stderr 后退出，不写任何产物 | 退出码 **2**，无 `result.json` | stderr + 退出码 2 |
| D2 | `case.json` 存在但不可解析（JSON 坏） | 兜底写一份诚实的失败结果后退出 | `status=failed`；退出码 **1**；写 `<out>/failed/result.json` | `failed/result.json.error` |
| D3 | 结构化 `entities` 为空但文本非空 | 走文本解构（`extraction=text-heuristic`），只串联相邻步骤 | 不直接降级；随后按 D6 判孤儿实体 | `extraction`；`uncertainty[scope=relations]` |
| D4 | 材料文件被引用却读不到 | **不伪造材料内容**，只登记实际读到的文件；引用缺失项写入 `notes` | 不降级；证据条数变少即为痕迹 | `evidence.source_files[]`；`evidence.notes[]` |

### 6.2 结构与连接域

| D# | 触发条件 | 动作 | 失败时的降级 | 证据位点 |
|-|-|-|-|-|
| D5 | 关系的 `from`/`to` 指向不存在的实体 | **丢弃该关系、不画**（断头箭头不进图面） | 若被丢弃的关系导致实体失去全部连接，转 D6 降级 | `verify.checks.no_dangling=true` + 实体数/关系数差 |
| D6 | 存在没有任何连接的实体（孤儿） | 保留实体并记录，交 Agent 核对是否漏画流向 | `status=partial` | `uncertainty[scope=orphan_entities]` |
| D7 | 实体 id 重复 | 重命名为 `<id>_2`、`<id>_3`… 保证唯一 | 不降级；改名本身会造成一个孤儿实体，由 D6 承接 | `result.json.entities[].id` |
| D8 | 画布装不下实体（溢出） | 等比缩放居中放入，**不裁剪**；或 `--width-mm/--height-mm` 重跑 | 不降级 | `canvas.requested` vs `canvas.width_mm/height_mm` |
| D9 | 类别或关系种类不在统一词表内 | 归一化到最近的合法值（类别 → `step`，关系 → `flow`） | 不降级（归一化后的值合法）；**原始非法值不留痕，属已知缺口，见 §10** | `verify.checks.kind_vocabulary=true` |
| D10 | `warn` 级规则命中（`recycle-review` / `product-terminal`） | 只提示人工复核，不阻断 | **不降级**：`status` 不受影响 | `verify.warnings[]` |
| D11 | 实体缺少 `source` 出处 | 置 `source=null`，列入不确定性，**不编造出处** | 不单独降级 | `uncertainty[scope=sources]`；`verify.checks.entity_source_coverage=false` |

### 6.3 导出域

| D# | 触发条件 | 动作 | 失败时的降级 | 证据位点 |
|-|-|-|-|-|
| D12 | PNG 或 PDF 渲染失败（缺 Pillow/reportlab 或渲染异常） | 保留已有产物与 SVG 源文件，如实记录异常 | `status=partial`；两个都失败且无实体 → `failed` | `uncertainty[scope=png|pdf]`；`exports[]` 缺项 |
| D13 | SVG 非法 XML 或图层/文本不达标 | 校验器捕获 → 修复后重跑；**禁止交付坏文件** | 修不好则 `status=partial` | `verify.checks.layers/editable_text` |
| D14 | 本机无中文字体 | `fonts[role=png].found=false` 如实记录；SVG 用 `font-family` 声明、PDF 用 CID 字体，均不受影响 | 不改变 `status`（D9 语义只记录；若同时有其它缺陷，由 §4 顺序决定） | `fonts[]`；`uncertainty[scope=fonts]` |

### 6.4 契约域

| D# | 触发条件 | 动作 | 失败时的降级 | 证据位点 |
|-|-|-|-|-|
| D15 | `result.json` 缺字段或字段类型不符 | `check.py` 报 issue；补齐后重跑 | 退出码 **3**；`status` 不得为 `success` | `check.py` 的 `issues[]` |
| D16 | 材料内部自相矛盾（同一实体两种类别/方向相反） | 不擅自选边：记入不确定性并写明冲突双方 | 不单独降级；由 Agent 用 `--merge` 决定后再定 | `uncertainty[scope=ambiguity]` |
| D17 | 契约某段为空 | 按容器类型补缺省值（列表 `[]`、字符串 `""`、对象 `{}`），**禁止 `null`** | 不降级；`null` 才降级 | `check.py` G2/G5/G6 |
| D18 | `svg_verify` 命中 error 级规则违规且未解决 | 列明违规项；`status` 不得为 `success` | `status=partial`；退出码 **3** | `verify.errors[]` + `uncertainty[scope=rule_violation]` |

### 6.5 状态域

| D# | 触发条件 | 动作 | 失败时的降级 | 证据位点 |
|-|-|-|-|-|
| D19 | 主流程抛出未预期异常 | 兜底写 `failed/result.json`（含异常文本）+ traceback 到 stderr；**不自称成功** | 退出码 **1**；`status=failed` | `failed/result.json`；stderr traceback |
| D20 | Agent 或人工在 Inkscape 里直接改了图稿 | 把改动补进 `change_record`（`action=manual-edit`、`by=agent`），并同步 `--merge` 的 `change_notes` | 不降级；隐瞒改动才是问题 | `change_record[]`；`checksum` 变化 |

### 6.6 检查点（门）

| 门 | 时点 | 判定对象 |
|-|-|-|
| CP1 证据门 | 步骤 1 后 | `evidence.json` 已生成；`locator` 真实命中材料；无出处条目已入 `uncertainty` |
| CP2 连接门 | 步骤 2 绘制中 | 类别/关系在词表内；`sequence`/`connect`/流向语义符合规则资产，无 error 违规 |
| CP3 校验门 | 步骤 2–3 | `svg_verify` 全绿：图层/文本/箭头/编号/图例一致；PNG/PDF 存在或已按 D12 诚实降级 |
| CP4 契约门 | 步骤 4 | `check.py` G1–G10 全过；`status` 与 `verify`/`uncertainty` 一致（D18/D19） |

## 7. 失败分支表（24 行；完整矩阵见 `references/failure-modes.md §2`）

按失败域读这张表：左两列是「你看到什么」，右三列是「谁负责、后果是什么、去哪里核对」。

| # | 失败域 | 现象（可观测） | 规则 | 是否污染交付物 | 核对位点 |
|-|-|-|-|-|-|
| 1 | 材料异常 | `--case` 指到的文件不存在 | D1 | 无产物（干净失败） | stderr；退出码 2 |
| 2 | 材料异常 | JSON 语法坏 | D2 | 仅有 `failed/result.json`，无图稿 | `failed/result.json.error` |
| 3 | 材料异常 | 只有自由文本、无结构化实体 | D3 | 低置信解构，需 Agent 复核 | `extraction=text-heuristic` |
| 4 | 材料异常 | 材料被引用但读不到 | D4 | 证据条数变少 | `evidence.source_files[]` |
| 5 | 材料异常 | 同一实体两种类别/相反方向 | D16 | 不污染，但要 Agent 裁决 | `uncertainty[scope=ambiguity]` |
| 6 | 材料异常 | 实体名重复或高度近似 | D7（并转 D6） | 产生一个孤儿实体 | `entities[].id` + `orphan_entities` |
| 7 | 连接正确性 | 关系端点不存在（断头） | D5 | **不污染**：该关系被丢弃 | `no_dangling=true` |
| 8 | 连接正确性 | 关系全部断头 | D5 → 顺序兜底 | **可能掩盖缺陷**：退化成顺序链而不报错，见 §10 | `relations[].source=text:order` |
| 9 | 连接正确性 | 有实体没有任何连接 | D6 | 触发降级 | `uncertainty[scope=orphan_entities]` |
| 10 | 连接正确性 | `sequence` 连到非步骤实体 | D18 | 触发降级，退出码 3 | `verify.errors[].rule=sequence-step-only` |
| 11 | 连接正确性 | `connect` 两端都不是结构件 | D18 | 触发降级，退出码 3 | `verify.errors[].rule=connect-structural` |
| 12 | 连接正确性 | 装置图里物料成为流向终点 | D18 | 触发降级，退出码 3 | `verify.errors[].rule=apparatus-flow-into-material` |
| 13 | 连接正确性 | 装置图产物继续流出 | D10 | **不污染**：仅提示复核 | `verify.warnings[].rule=product-terminal` |
| 14 | 连接正确性 | 自环关系 | D18 | 触发降级，退出码 3 | `verify.errors[].rule=no-self-loop` |
| 15 | 连接正确性 | `recycle` 回流 | D10 | **不污染**：仅提示复核 | `verify.warnings[].rule=recycle-review` |
| 16 | 材料异常 | 类别或关系种类非法 | D9 | **静默归一化**，合法值顶替原值，见 §10 | `kind_vocabulary=true`（原值不留痕） |
| 17 | 模板缺失 | 自定义 `--rules` 文件为空对象 | D9/D10 | 审计退化为"无规则"，其余检查照常 | `verify.checks.connection_rules=true` |
| 18 | 模板缺失 | 自定义 `--rules` 路径不存在 | D9/D10 | 同上：静默跳过审计，不报错 | 退出码仍为 0 |
| 19 | 依赖缺失 | 无 Pillow | D12 | 无 `figure.png`，降级 | `uncertainty[scope=png]` |
| 20 | 依赖缺失 | 无 reportlab | D12 | 无 `figure.pdf`，降级 | `uncertainty[scope=pdf]` |
| 21 | 依赖缺失 | 无中文字体 | D14 | 不污染 SVG/PDF；PNG 缺字属实记录 | `fonts[].found=false` |
| 22 | 契约四形态 | 某段为 `null` 或缺键 | D17 | 触发降级 | `check.py` G2/G5/G6 |
| 23 | 契约四形态 | 四段是列表但内容为空 | D17 | **不污染**：空列表合法 | `check.py` issues=[] |
| 24 | 状态不一致 | `verify.ok=false` 却报 `success` | D18 | 被 G10 拦截，退出码 3 | `check.py` G10 |
| 25 | 状态不一致 | `--merge` 引入非法端点 | D5/D15 | 断头关系由 `layout` 保持可画路径 → 触发 G6/G7/G9 拦截，退出码 3 | `check.py` G6/G7/G9 |
| 26 | 状态不一致 | 人工改了 SVG 未记录 | D20 | 不降级，但 `checksum` 与 `change_record` 对不上 | `change_record[]` |
| 27 | 运行期 | 未预期异常 | D19 | 干净失败 + 兜底结果 | `failed/result.json` |

> 第 8/16/17/18 行是**本版诚实标注的三类"安静"缺陷**：它们不报错、不降级，靠人读位点
> 才能发现。把它们写进表里，比假装不存在更有用；处置方法见 §10。

## 8. 交付自查（复制到你的检查脚本里直接用）

```bash
SKILL_DIR=/skills/weekly-skill
OUT=/tmp/out

# ① 生成 + 契约门（退出码 0 = 全过；3 = 已出图但门不过，需按 §6 处置）
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md --out "$OUT"
python "$SKILL_DIR/scripts/check.py" "$OUT/<case_id>/result.json"

# ② 确定性（同输入应逐字节一致 → 结论可被第三方复现）
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md --out /tmp/out-B
# 比对 figure.svg / layout.json / evidence.json / verify_report.json 的 sha256

# ③ 决策规则是否按表执行（20 个内置用例，逐条给期望判决与实测观测值）
python "$SKILL_DIR/scripts/decision_probe.py" --out /tmp/decisions
```

`references/DECISION-CASES.md` 给出 ③ 的期望值与实测值对照；若你的运行结果与表不符，
说明你的环境触发了 §7 的某一行（先查那一行的核对位点，再查 D# 规则）。

## 9. 资源清单（路径均相对技能根）

- `scripts/main.py` — 一键流水线（编排：证据→模型→布图→渲染→校验→契约）
- `scripts/gain_evidence.py` — 证据抽取（CP1；`locator`+`quote`+材料 `sha256`）
- `scripts/model.py` — SIR：实体/关系/步骤/流向解析与文本解构兜底
- `scripts/layout.py` — 确定性布图（图元库 + 模板落点）
- `scripts/render_svg.py` — 手写分层 SVG（可编辑源文件）
- `scripts/export_preview.py` — PIL PNG + reportlab PDF（同一布局模型）
- `scripts/svg_verify.py` — SVG 校验 + 连接规则审计（CP2/CP3；`verify_report.json`）
- `scripts/check.py` — 契约门 G1–G10（CP4；退出码 0/1/3）
- `scripts/fonts.py` — 中文字体探测与降级
- `scripts/decision_probe.py` — **本版新增**：20 个决策用例的批量探针（输出观测值表）
- `scripts/bare_baseline.py` — **本版新增**：不加载 Skill 的可执行下界（对照实验用，不是交付路径）
- `assets/connection_rules.json` — 连接规则字典（词表 + 语义规则，可扩展）
- `assets/result_example.json` — `result.json` 最小形态示例
- `templates/palette.json` — 图元配色模板
- `templates/component-connection-checklist.md` / `entity-relation-checklist.csv` — 核对清单/表
- `references/OUTPUT_CONTRACT.md` — `result.json` 契约（18 个顶层字段）+ G1–G10
- `references/RUBRIC_MAP.md` — 评分五维（40/25/15/10/10）逐条落点
- `references/failure-modes.md` — **本版重写**：失败分支表 + 决策规则矩阵 + 打包门 R1–R6
- `references/DECISION-CASES.md` — **本版新增**：20 个决策用例（期望判决 + 实测观测值）
- `references/vocabulary.md` — 术语表/词表（kind/关系/图类/命名/状态）
- `references/figure-blueprint.md` — 布局蓝图（图元/模板/命名/导出/扩展）
- `examples/` — 最小调用示例（生成 + 编辑双用例）

依赖（全部可降级）：Python 3.10+ 标准库；Pillow（PNG）；reportlab（PDF）。
`cairosvg/svgwrite/python-pptx` 不需要。

## 10. 已知边界（诚实声明，含本版新查明的三类"安静"缺陷）

1. **关系全断头时会退化成顺序链**：`relations` 全部被丢弃后，模型会改走文本顺序兜底
   （`source=text:order`），结果 `status=success` 且不报错。**后果**：非法输入可能被
   静默"修好"。**处置**：看到 `relations[].source` 全为 `text:order` 就视为可疑，回查
   `verify.checks.no_dangling` 与原始 `relations` 条数差。
2. **词表外类别被静默归一化**：模型容错把非法 `kind` 归一为 `step`、非法关系归一为
   `flow`，随后词表审计自然通过。**后果**：材料里的类别错误不再可见。**处置**：对比
   `evidence.entities[].kind` 与输入材料的原始取值。
3. **规则资产缺失/为空时审计静默跳过**：`--rules` 指向空文件或不存在的路径时，
   `connection_rules` 检查按"无规则"通过。**后果**：看起来"全绿"，实际没审。
   **处置**：核对 `verify.checks.connection_rules` 的同时看一眼你给的 `--rules` 是否存在。
4. **局部放大视图未内置**：多级嵌套装配需 Agent 拆画布或增补 `stage` 列。
5. **数值注记不强制**：材料给出可标注原值时可放入实体 `props`，当前渲染端不强标数值。
6. **`examples/` 是合成示例**（标注「示例，非正式案例」），不含预制答案；正式案例、
   白板与评分由平台提供/执行。本包不宣称任何具体分数。

## 11. 评分五维落点（速查；逐条证据见 `references/RUBRIC_MAP.md`）

| 维度 | 分 | 本包落点（文件/机制） |
|-|-|-|
| 实际效果 | 40 | `scripts/main.py` 一键出图 → 可编辑分层 `figure.svg` + PNG/PDF + `evidence/layout/verify_report/result.json`；示例产物在 `examples/output/` |
| 使用增益 | 25 | 证据先行（CP1）+ 连接规则机器审计（CP2）+ 编号/图例一致性门（CP3）+ `--merge` 增量改图；对照协议见 `references/RUBRIC_MAP.md §2` |
| 创新增益 | 15 | SIR 结构化中间表示 → 确定性布图 → 三后端共享布局；规则资产可扩展并机器审计；**D1–D20 与 24 行失败分支表把"异常处置"做成可执行规范** |
| 可靠体验 | 10 | 本文件 §6/§7 + `references/failure-modes.md`（材料异常/模板缺失/依赖缺失/契约四形态/状态一致性）+ `check.py` 退出码 0/1/2/3 语义 + 状态聚合优先级 §4 |
| 生态贡献 | 10 | 文档完整性（SKILL/README/TEST/6 份 references/2 份 templates）；可复用资产（规则字典、配色、核对清单、决策用例集、探针脚本）；`GITHUB_URL.txt` 公开入口 |
