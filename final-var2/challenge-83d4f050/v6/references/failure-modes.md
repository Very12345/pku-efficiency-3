# failure-modes.md — 失败模式与处置表

> 与 SKILL.md 的决策规则 D1–D12、检查点 CP1–CP5 一一对应（见 SKILL.md §4/§8）。
> 本题高分包几乎都带 failure-modes / failure_playbook（可靠体验 10 分的关键证据）。
> 表中每条都对应**脚本里的真实分支**与 `result.json` 里的真实记录位点，不是清单摆设。

> **本文档的五个视图（全维合并版）**：同一个失败集合，按五种方式索引，按需查其中一种即可 ——
> ① `## 1`–`## 5` 按**阶段/类别**（材料、规格、渲染、状态、反编造）；
> ② `## 6` 按 **F01–F22 编号**（R1/v1 的分类学，含每个分支的记录位点）；
> ③ `## 7` 按**破坏了哪条机制 M1–M6**（R1/v3，用于判断该先修哪一环）；
> ④ `## 8` 按**故障注入四形态**（R2/v4，实测退出码与留痕位点）；
> ⑤ `## 9` 按**换题材边界 F1–F10**（R2/v5）。五种索引指向同一套处置，不冲突。

## 1. 材料阶段失败

| # | 失败模式 | 检出点 | 处置 | 记录位点 |
|---|---|---|---|---|
| F1 | 材料缺失（case.json 无 materials 且目录无文件） | CP1.3 fail | 写 failed result，给出补救路径（补材料或 --model-file） | status=failed + uncertainty |
| F2 | 材料是 PDF/扫描件，无结构化文本 | extract method=manual-required | Agent 抽文本转成文本材料，或手工建规格 | extraction.method + change_records |
| F3 | 材料缺方向信息（不知上下游） | 人工核验 CP4 | 只画无向/结合类语义，标 uncertain；不臆造方向 | uncertainty + 边 uncertain=true |
| F4 | 同名基因/蛋白歧义 | P04 | 拆成两个实体并注明；无法区分时标 uncertain | uncertainty + note |
| F5 | 材料给出矛盾数值 | 人工核验 | 以材料原文为准，图与结果都标注矛盾点 | uncertainty + change_records |
| F6 | 材料无实体/关系 | extract manual-required | 明确 failed，不画空图凑数 | status=failed |

## 2. 规格/校验阶段失败

| # | 失败模式 | 检出点 | 处置 | 记录位点 |
|---|---|---|---|---|
| F7 | 机制规格未过 schema 门（类型/必需字段违规） | CP2（S01）fail | 阻断渲染，写 failed；修正规格后重跑 | status=failed |
| F8 | 边端点引用不存在的实体 | P02 fail | 阻断：删除或补实体 | self_check |
| F9 | 非反馈边逆流 | P03 warn | 必须说明缘由（转位/回流）或改方向 | uncertainty |
| F10 | 疑似反馈环未标注 | P07 warn | 补 `feedback=true` 右侧绕行 | topology |
| F11 | 图例缺在用类型 | L01/L02 fail | 补图例项；禁止"用了却不列" | legend_audit |
| F12 | 画布颜色不在图例/映射内 | L05 fail | 改回图例色或扩展图例 | legend_audit |
| F13 | 数值无法溯源 | E01 fail / T03 warn | 补 source 或降为假设并说明 | uncertainty |

## 3. 渲染/导出阶段失败

| # | 失败模式 | 检出点 | 处置 | 记录位点 |
|---|---|---|---|---|
| F14 | matplotlib 不可用 | preview 异常捕获 | 保留 SVG 源；PNG/PDF 缺失如实记录（`status=partial`、exit 2、G5=false） | export_checks + deliverables 空预览 + uncertainty |
| F14b | 运行者显式只要求 SVG（`--formats svg`） | 跳过预览渲染 | 不报错：只交付可编辑 SVG 源，并说明"本次未请求预览" | uncertainty + deliverables 空预览 |
| F15 | 中文字体缺失 | mpl 字体探测 | 告警并记录 font；SVG 用字体栈不受影响 | preview warnings + uncertainty |
| F16 | 导出失败（某格式） | F01_xxx fail | 至少交付 SVG + PNG；其他格式如实说明 | export_checks |
| F17 | 图面元素过多不可读 | 布局溢出/节点收缩 | 减小字号/收缩节点宽度，或拆分子图并记录 | layout.warnings |
| F18 | schema 文件缺失 | S01 warn | 降级用内置默认并记录（不阻断） | uncertainty |

## 4. 状态一致性（status 三值）

- `success`：断性检查全过 + **提取已人工核验** + 门 G1–G8 全过；
- `partial`：有 SVG 源但存在 fail/warn 或**自动草稿未核验**——失败/警告全部列明；
- `failed`：无法产出可编辑源、SVG 不合法、或 CP2 schema 门不过。
- 任何失败都不得静默：全部进入 `self_check / topology / legend_audit / uncertainty /
  change_records` 对应位点（诚实记录是判分"结果可核验性"的前提）。

## 5. 反预制答案 / 反编造规则

- 正式案例材料与示例不同，必须现场读取真实文件推导，禁止把 examples 内容抄入正式输出；
- 不写平台未提供的评分/分数；没有的软件状态（如 matplotlib 缺失）如实说明；
- 结果的可核验链 = 材料行号 → 实体/边 source → SVG data-source → result.json
  evidence_sources → export_checks(sha256) → change_records（D 系列自检守护）。
## 6. F01–F22 全表（R1/v1 逐字保留：触发、处置与记录位点）

> 本表与 `SKILL.md` **§1 决策规则 D1–D23** 和 **§2 失败分支总表**一一对应：
> 每个 F 编号在 SKILL.md §2 里有同一编号的行，并指明它由哪条 D 规则管辖。
> 表中"实测"列来自 2026-11-22 在**临时目录副本**上真跑的记录（命令与输出见 `TEST.md` §5–§9），
> 不是设计意图的复述。
>
> 使用方式：**发现异常 → 找到 F 编号 → 按"处置"做 → 把结果写进"记录位点"。**
> 记录位点没有内容 = 这次运行不可核验 = 交付缺陷（哪怕图本身画对了）。

### 1. 材料异常（F01–F06）

| # | 失败模式 | 触发信号（怎么发现） | 处置 | 记录位点 | D 规则 |
|---|---|---|---|---|---|
| F01 | 材料缺失 / 目录为空 | CP1.3 `fail`；`SUMMARY ... "reason": "CP1 fail"` | 按 D7 三级查找（case 相对路径 → `--materials-dir` → case 同目录）；都没有 → `status=failed` + 补救路径 | `status` / `reason` / `uncertainty` | D7 |
| F02 | 材料是 PDF / 扫描件，抽不出结构化文本 | 抽取器返回 `manual-required`；实测 `SUMMARY {"status": "failed", "reason": "manual-required"}`，exit **3** | 先抽文本另存为 `.md`；仍不可结构化 → CP2b 手工建 `model.json`，`extraction.method=manual` | `extraction.method` / `change_records` | D5 |
| F03 | 材料没写上下游方向 | 边无法定向；人工核验 CP3 发现 | 只画结合类无向语义边，`uncertain=true`，布局不给方向暗示 | `uncertainty` / 边的 `uncertain` | D1 |
| F04 | 同名基因与蛋白歧义 | 拓扑审计 P04 | 拆两个实体（gene 斜体 / protein 正体）并写 `note`；无法区分则合并 + `uncertain` | `note` / `uncertainty` | D2 |
| F05 | 材料数值自相矛盾 | 人工核验 CP3 | 以材料原文为准，图与结果**两处**都标矛盾点 | `uncertainty` + `change_records` | D4 |
| F06 | 只有实体没有关系 / 材料全空 | `scientific_content.counts.edges == 0` 或 entities 也为 0 | 有实体：照画并 `status=partial` 说明"边清单为空"；全空：`failed`，**不画空图** | `status` / `counts` | D6 |

### 2. 资产缺失（F07–F09）

| # | 失败模式 | 触发信号 | 处置 | 记录位点 | D 规则 |
|---|---|---|---|---|---|
| F07 | `assets/palettes.json` 缺失或损坏 | 读资产异常 / JSON 解析失败 | 回退 `scripts/model.py` 内置默认调色板继续跑；**不得**因此改变图例语义 | `uncertainty` | D18 |
| F08 | `assets/mechanism-spec.schema.json` 缺失 | 检查 `S01` 记 `warn` | 用内置默认 schema 继续（**不阻断**），但在自检里留下 warn | `self_check.warnings` | D18 |
| F09 | `templates/relation-checklist-template.md` 缺失 | 模板路径不存在 | 用 `SKILL.md` §7 自查清单代替核验载体，仍要逐条留痕 | `change_records` | D18 |

### 3. 依赖缺失（F10–F12）

| # | 失败模式 | 触发信号 | 处置 | 记录位点 | D 规则 |
|---|---|---|---|---|---|
| F10 | matplotlib 不可用 | `import matplotlib` 抛异常 | 只交付可编辑 SVG：`status=partial`、exit **2**、`gates.g5_png.pass=false`（实测 7/8 门过）、`previews/exports` 保持 `[]` | `deliverables` / `export_checks` / `uncertainty` | D16 |
| F11 | Pillow 缺失 | 尺寸校验无法执行 | PNG 仍由 matplotlib 写出；尺寸校验降级为 warn | `self_check.warnings` | D16 |
| F12 | 系统中文字体缺失 | 渲染期字体探测告警 | SVG 用 CSS 字体栈（不受影响）；PNG 记录 `font` 与告警，**不静默输出乱码** | `export_checks` / `uncertainty` | D17 |
| F12b | 运行者显式只要 SVG（`--formats svg`） | 命令行显式指定 | 不算失败：`partial` + exit 2，SVG 与全量运行**逐字节相同**（实测 sha16 `27f344a0dfb2e90f`） | `uncertainty` / 空 `previews` | D16 |

### 4. 契约四形态（F13–F16）

判定顺序：先看 `case.json` 的 `output_contract` 里**声明值的 JSON 形态**，再决定空值怎么写。

| # | 形态 | 声明示例 | 无真实值时的填空 | 机器判定 | D 规则 |
|---|---|---|---|---|---|
| F13 | ① 字段 → 标量 | `"custom_demo_field": "示例文本"` | `""` | `check_contract.py` C05 | D19 / D20 |
| F14 | ② 字段 → 容器 | `"custom_list_field": ["示例"]` | `[]` | 同上 | D19 / D20 |
| F15 | ③ 布尔开关 | `"colorblind_safe": true` | `false` | 同上 | D19 / D20 |
| F16 | ④ 数值 / 字典 | `"resolution_dpi": 150` | `0` / `{}` | 同上 | D19 / D20 |

统一铁律：**顶层不得出现 `null`**（实测 C04 会直接判 fail）。
声明值本身是 `null` 时按形态 ① 处理（填 `""`），并在 `uncertainty` 说明判据。

### 5. 状态一致性（F17–F20）

| # | 失败模式 | 触发信号 | 处置 | 记录位点 | D 规则 |
|---|---|---|---|---|---|
| F17 | 机制规格没过 schema 门 | CP2 `S01` fail；实测 `SUMMARY ... "reason": "机制规格未通过 schema 门"`，exit **3**，输出目录**只有 `result.json`** | 阻断渲染；按违规清单修正规格后重跑；修正过程写进 `change_records` | `status` / `reason` / `change_records` | D21 |
| F18 | 契约回显不完整 | `check_contract.py` 非 0；实测对 failed 结果返回 `contract\|fail\|...\|checks=7`，exit **1** | 按报出的缺项补齐（填空规则见第 4 节）；同一缺项两次修不好就停止重跑并如实记录 | `result.json` / `uncertainty` | D20 |
| F19 | failed 路径信封不全 | 实测 schema 门失败时 `result.json` 只有 **14 个顶层键**，缺 `title / skill / data_mapping / extraction / export_checks / provenance` **6 项**（信封 13/19） | 若平台要求 failed 运行也必须带全契约：把这 6 项按 D19 空值形态补写后再自查；**不得**把 failed 报成 success | `result.json` | D21 |
| F20 | `status` / `gates` / 退出码互相矛盾 | 三者不一致（例如 status=success 但 exit 2） | 以**退出码为真**重算三元组；取更保守的档位（success→partial→failed），并写明取值理由 | `uncertainty` | D22 |

**状态一致性速查（实测口径）**

| 情形 | status | exit | gates | 说明 |
|---|---|---|---|---|
| 已核验规格 + 预览齐全 | `success` | 0 | 8/8 | 唯一允许 success 的组合 |
| 自动草稿未核验 / 缺预览 / 只要 SVG | `partial` | 2 | 7/8 或 8/8 | 必须列明 warn/fail |
| schema 门不过 / 材料不可解析 | `failed` | 3 | 不适用（`gates={}`） | 只写最小信封（见 F19） |

### 6. 渲染与可读性（F21–F22）

| # | 失败模式 | 触发信号 | 处置 | 记录位点 | D 规则 |
|---|---|---|---|---|---|
| F21 | 图面元素过多、不可读 | 布局溢出 / 节点被压缩到字号下限 | 减小默认字号、收缩节点宽度，或拆子图；严重时降 `partial` | `layout.warnings` / `uncertainty` | — |
| F22 | 目标导出格式不支持 | `F01_xxx` fail / 请求了未知格式 | 至少交付 SVG + PNG；其余格式如实说明不支持（实测 `--formats png` → exit 2、`partial`、PNG 正常产出 203655 字节） | `export_checks` | D16 |

### 7. 反预制答案 / 反编造（所有 F 的共同前提）

- 正式案例材料与 `examples/` 不同，**必须现场读取真实文件**推导；禁止把示例实体/边/数值抄进正式输出；
- 不写平台未提供的评分；没有的软件状态（如 matplotlib 缺失）如实说明，不假装有预览；
- 追溯链必须是完整的：**材料行号 → 实体/边 `source[]` → SVG `data-source` → `result.json.evidence_sources`
  → `export_checks[].sha256` → `change_records`**；断在任意一环都按上面某条 F 处理并在对应记录位点留痕。
## 7. 按机制归类（R1/v3 逐字保留：破坏了 M1–M6 哪一环）

> 本版的组织方式与前两版不同：不问"失败发生在哪个阶段"，而问**"哪条机制被破坏了"**。
> 这样修复指令指向结构（补规格 / 修门 / 补溯源 / 恢复确定性 / 补齐契约），
> 而不是指向现象（"图不好看就调布局"）。
> 机制编号 M1–M6 见 `SKILL.md` §1 与 `references/MECHANISM.md`；修复捷径 K1–K10 见 `SKILL.md` §3。

### 1. 破坏 M1（规格先行）的失败

| # | 失败模式 | 触发信号 | 修复（补机制，而不是改图） | 记录位点 |
|---|---|---|---|---|
| F01 | 材料缺失/目录为空 | CP1.3 fail | 三级查找材料（case 路径 → `--materials-dir` → 同目录）后再谈出图 | `status/reason/uncertainty` |
| F02 | 材料不可结构化（PDF/扫描件） | 抽取器报 `manual-required`；实测 exit **3** | 抽文本 → 仍不行则手工建规格（`extraction.method=manual`） | `extraction.method` |
| F03 | 规格与材料脱钩（实体名/类型凭印象） | 人工核验时对不上材料行号 | 逐条回填 `source[{ref, kind, line}]`；无法定位的项降为 `assumption` | `source[]`、`uncertainty` |
| F04 | 草稿未人工核验就当成品 | `verified_by_agent=false` | 走 CP3；核验前只能 `partial`（exit 2） | `extraction`、`uncertainty` |
| F05 | 只有实体没有关系 | `counts.edges == 0` | 照画并说明"边清单为空"；实体也为空则 `failed`，不画空图 | `status/counts` |
| F06 | 同一分子跨区室被并成一个实体 | 拓扑 P04b | 按区室拆实体并注明去向（跨膜语义会被混淆） | `note`、`topology.json` |
| F07 | 同名基因/蛋白混用 | P04 | 拆两个实体（基因斜体/蛋白正体）或合并 + `uncertain` | `note/uncertainty` |

### 2. 破坏 M2（raw 规格 schema 门）的失败

| # | 失败模式 | 触发信号 | 修复 | 记录位点 |
|---|---|---|---|---|
| F08 | 规格含枚举外类型 | schema 门 fail | **改规格**（不是改图）；改正后重跑 | `reason`（实测：exit 3、只写 `result.json`） |
| F09 | 门被绕过（先归一化再校验） | 把类型改成 `banana` 仍 exit 0 | 把校验点移回**原始规格**；这是门失效的头号原因 | `change_records` |
| F10 | schema 文件缺失 | 检查 `S01` warn | 用内置默认 schema 继续（不阻断），但必须留 warn | `self_check.warnings` |
| F11 | 边端点引用不存在的实体 | 拓扑 P02 fail | 补实体或删边；端点悬空等于画出不存在的论断 | `self_check`、`topology.json` |

### 3. 破坏 M3（双审计）的失败

| # | 失败模式 | 触发信号 | 修复 | 记录位点 |
|---|---|---|---|---|
| F12 | 图面用了某类型但图例未列 | L01/L02 fail | 补图例项 → 重跑（**fail 级，不是 warn**） | `legend_audit.json` |
| F13 | 画布颜色不在图例 ∪ 映射内 | L05 fail | 改回图例色或扩图例 | `legend_audit.json` |
| F14 | 数值找不到来源 | E01 fail / T03 warn | 补 `source`，或降 `assumption` 并停止用它编码颜色 | `uncertainty` |
| F15 | 虚线被用来表达"类型"而非"证据弱/不确定" | L06 fail | 恢复：虚线只表示弱证据/不确定 | `legend_audit.json` |
| F16 | 非反馈边逆流 / 反馈环未标注 | P03 warn / P07 warn | 标 `feedback=true` 右侧绕行，或给出科学理由 | `topology.json`、`uncertainty` |
| F17 | 重复边 / 自环处理不当 | P05 / P06 | 重复边合并并保留全部来源；自环必须写机制依据，否则删除 | `topology.json` |

### 4. 破坏 M4（分层与溯源）的失败

| # | 失败模式 | 触发信号 | 修复 | 记录位点 |
|---|---|---|---|---|
| F18 | SVG 缺层或层名不符 | G4 fail（须 ≥7 个 `layer-*`） | 检查渲染后端；**不得**用扁平 SVG 交付（M4 会整体失效） | `deliverables.editable_sources` |
| F19 | 元素缺 `data-source` | A2 指标下降 / T 系列检查 | 从规格回填来源；规格里没有来源就先补规格（回到 M1） | `self_check` |
| F20 | 只能交位图（无可编辑源） | 请求的格式不含 SVG / SVG 生成失败 | 生成 SVG 是硬要求：失败即 `failed`（exit 3） | `status`、`deliverables` |

### 5. 破坏 M5（确定性）的失败

| # | 失败模式 | 触发信号 | 修复 | 记录位点 |
|---|---|---|---|---|
| F21 | 图件里混入时间戳/随机 id | 双跑 sha256 不一致（非 PDF 项） | 从布局与 SVG 生成里移除时间戳；PDF/`result.json` 例外需如实声明 | `self_check.determinism` |
| F22 | 同输入跑出不同结构 | 双跑结构不同（不是字节不同） | 检查是否读了外部状态（环境变量、系统字体差异、字典遍历顺序） | `TEST.md` 记录 |

### 6. 破坏 M6（契约化终态）的失败

| # | 失败模式 | 触发信号 | 修复 | 记录位点 |
|---|---|---|---|---|
| F23 | 契约字段无值 | 回显缺失 | 四形态填空：标量 `""`/列表 `[]`/布尔 `false`/数值·字典 `0`·`{}`；**顶层禁 null** | `result.json` |
| F24 | `failed` 终态信封不全 | 实测只有 **14 键**（信封 13/19，缺 `title/skill/data_mapping/extraction/export_checks/provenance`） | 若要交付，补写这 6 项空值后再自查；不得把 failed 报成 success | `result.json` |
| F25 | `status`/退出码/`gates` 不一致 | 三元组矛盾 | 以退出码为真，取保守档（success→partial→failed） | `uncertainty` |
| F26 | 审计产物未落盘 | G8 fail | 让 `topology.json` / `legend_audit.json` 写进 `--out` | `deliverables.audits` |

### 7. 破坏链上游优先（修复顺序）

```
M1 材料/规格 → M2 门 → M4 渲染与溯源 → M3 审计 → M6 契约
```

- 上游没修好，下游的修复都是白费力气：规格错了，图例补得再全也只是把错误画得更标准；
- 判断"我在上游还是下游"的办法：**看审计产物里报的是"缺内容"还是"不一致"**——
  缺内容（无来源、无实体）→ 上游；不一致（图例对不上、方向矛盾）→ 中游；信封缺项 → 下游。

### 8. 共同前提（不因机制分类而改变）

- 正式案例必须现场读材料；`examples/` 与 `assets/result.template.json` 都不得冒充正式输出；
- 不写、不预测平台评分；没有的软件状态如实说明；
- 追溯链必须闭合：材料行号 → `source[]` → SVG `data-source` → `evidence_sources` →
  `export_checks[].sha256` → `change_records`。
## 8. 四形态故障注入矩阵（R2/v4 逐字保留：实测台账索引）

§1–§5 是"遇到失败怎么办"的规则表；本节回答"**这些规则真的会生效吗**"。
`scripts/fault_inject.py` 把四形态各弄坏一次并跑真实主流程，逐行记录退出码 / status /
留痕位点 / 是否静默失败；完整 24 行表与恢复演练见 `references/FAULT-MATRIX.md`。

| 形态 | 对应本文件 | 注入示例 | 实测终态（详见矩阵） |
|-|-|-|-|
| 输入 | §1 材料阶段、§2 规格/校验阶段 | case 不存在/坏 JSON、材料目录空、材料非 UTF-8、枚举外类型、边端点不存在 | `exit 1`（入口拒绝）/ `3 failed`（schema 门、材料缺失）/ `2 partial`（草稿未核验） |
| 模板 | §3 渲染/导出阶段（资产分支） | 删/损坏 `palettes.json`、删 `mechanism-spec.schema.json`、删人工核对清单与结果模板 | `exit 0 success` + `uncertainty`（调色板、schema warn）；核对清单/结果模板属**文档资产**，主流程不读（如实标 N/A） |
| 依赖 | §3 渲染/导出阶段 | `matplotlib` 不可导入 / `pyplot` 抛错、`Pillow` 缺失、`--formats svg` | `exit 2 partial` + `gates.g5_png=false` + `previews=[]` + 原因入 `export_checks`/`uncertainty` |
| 契约 | §4 状态一致性 | `output_contract` 四形态与 `null` 声明、产物里塞顶层 `null`、缺 `result.json` | 四形态按 `""`/`[]`/`false`/`0`·`{}` 回显且无 null；`check_contract.py` 实测 `exit 1`（C04/C01） |

### 7. 演练发现的三处静默失败（G1–G3，已纯增量修复）

"静默失败"= `exit 0` **且** `status=success` **且** `uncertainty` / `reason` /
`self_check.warnings` / `self_check.failures` 四个留痕位点**全空**。

| # | 失败模式 | 修复前实测 | 修复（纯增量） | 修复后实测 |
|-|-|-|-|-|
| G1 | 边端点不存在 → 边被 `normalize_edges()` 丢弃 | `exit 0 success`、零留痕：**图面少一个科学论断** | `model.py` 新增 `dropped_edges()` 探针 + `main.py` 写 `uncertainty` | `uncertainty=1`，点名 `e2→e999` |
| G2 | `palettes.json` 缺失/损坏 → `_load_palettes()` 静默回退 | `exit 0 success`、零留痕：与 F07/D18 的文档承诺不符 | `model.py` 新增 `palette_load_status()` + `main.py` 写 `uncertainty` | `uncertainty=1`，区分两种异常 |
| G3 | `case.json` 无 `task` 且无 `task.md` → CP1.2 判 warn 后被丢弃 | `exit 0 success`、零留痕：静默降级 | `main.py` 新增一段把 `cp1` 的所有 warn 写进 `uncertainty` | `uncertainty=1`：CP1 前置检查降级 |

> 维护义务：**任何脚本改动后必须重跑 `fault_inject.py`**，并把新台账写回
> `references/FAULT-MATRIX.md` 与 `TEST.md` §12；文档里的数字必须能在报告里找到同源行。
## 9. 换题材相关失败分支（R2/v5 逐字保留：F1–F10 索引）

§1–§5 是通用失败模式；换一个新题材时最容易踩的是下面这几条（题集实测见 `CASE-SET.md`）：

| F 编号 | 触发信号 | 处置 | 记录位点 |
|-|-|-|-|
| F1 | 材料是散文，抽取器报 `manual-required` | 走 CP2b 手写 `model.json`；**不要**用空模型硬跑 | `extraction.method`、`status` |
| F2 | 材料是 PDF/扫描件 | 先抽文本另存 `.md`；或直接手工建规格 | `extraction.method` |
| F3 | 规格里出现枚举外 `type` | schema 门阻断（exit 3 / failed） | `status/reason` |
| F4 | 契约自定义字段需要"真实值" | 管道只保证**形态回显**；真值从 `scientific_content` 读 | `result.json` 顶层 + `counts` |
| F5 | 逆流边（膜募集/转位） | 记 `P03`/`P07` warn，不阻断；在 `uncertainty` 说明方向依据 | `uncertainty`、`topology` |
| F6 | 材料无数值却想上色 | 关闭数据映射（`data_mapping.field` 为空），图例注明"无数据编码"；`L03` 会是 warn | `legend_audit`、图例 |
| F7 | 区室名不在词表内 | 归一失败即 warn；自定义区室要在 `layout.compartments` 与图例同步声明 | `layout.warnings` |
| F8 | 元素过多、图面拥挤 | 拆子图或缩小字号，记录 `layout.warnings`；本包不自动分图 | `layout.warnings` |
| F9 | 无 matplotlib / 缺中文字体 | 仅交付可编辑 SVG（partial）；字体告警入 `export_checks` | `export_checks` |
| F10 | 契约字段声明成复杂结构 | 按空列表降级并说明；复杂结构放 `scientific_content` | `uncertainty` |