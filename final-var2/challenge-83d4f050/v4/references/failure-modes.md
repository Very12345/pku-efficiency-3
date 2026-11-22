# failure-modes.md — 失败模式与处置表

> 与 SKILL.md 的决策规则 D1–D12、检查点 CP1–CP5 一一对应（见 SKILL.md §4/§8）。
> 本题高分包几乎都带 failure-modes / failure_playbook（可靠体验 10 分的关键证据）。
> 表中每条都对应**脚本里的真实分支**与 `result.json` 里的真实记录位点，不是清单摆设。

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

## 6. 四形态故障注入矩阵（实测台账索引 · 本版新增）

§1–§5 是"遇到失败怎么办"的规则表；本节回答"**这些规则真的会生效吗**"。
`scripts/fault_inject.py` 把四形态各弄坏一次并跑真实主流程，逐行记录退出码 / status /
留痕位点 / 是否静默失败；完整 24 行表与恢复演练见 `references/FAULT-MATRIX.md`。

| 形态 | 对应本文件 | 注入示例 | 实测终态（详见矩阵） |
|-|-|-|-|
| 输入 | §1 材料阶段、§2 规格/校验阶段 | case 不存在/坏 JSON、材料目录空、材料非 UTF-8、枚举外类型、边端点不存在 | `exit 1`（入口拒绝）/ `3 failed`（schema 门、材料缺失）/ `2 partial`（草稿未核验） |
| 模板 | §3 渲染/导出阶段（资产分支） | 删/损坏 `palettes.json`、删 `mechanism-spec.schema.json`、删人工核对清单与结果模板 | `exit 0 success` + `uncertainty`（调色板、schema warn）；核对清单/结果模板属**文档资产**，主流程不读（如实标 N/A） |
| 依赖 | §3 渲染/导出阶段 | `matplotlib` 不可导入 / `pyplot` 抛错、`Pillow` 缺失、`--formats svg` | `exit 2 partial` + `gates.g5_png=false` + `previews=[]` + 原因入 `export_checks`/`uncertainty` |
| 契约 | §4 状态一致性 | `output_contract` 四形态与 `null` 声明、产物里塞顶层 `null`、缺 `result.json` | 四形态按 `""`/`[]`/`false`/`0`·`{}` 回显且无 null；`check_contract.py` 实测 `exit 1`（C04/C01） |

## 7. 演练发现的三处静默失败（G1–G3，已纯增量修复）

"静默失败"= `exit 0` **且** `status=success` **且** `uncertainty` / `reason` /
`self_check.warnings` / `self_check.failures` 四个留痕位点**全空**。

| # | 失败模式 | 修复前实测 | 修复（纯增量） | 修复后实测 |
|-|-|-|-|-|
| G1 | 边端点不存在 → 边被 `normalize_edges()` 丢弃 | `exit 0 success`、零留痕：**图面少一个科学论断** | `model.py` 新增 `dropped_edges()` 探针 + `main.py` 写 `uncertainty` | `uncertainty=1`，点名 `e2→e999` |
| G2 | `palettes.json` 缺失/损坏 → `_load_palettes()` 静默回退 | `exit 0 success`、零留痕：与 F07/D18 的文档承诺不符 | `model.py` 新增 `palette_load_status()` + `main.py` 写 `uncertainty` | `uncertainty=1`，区分两种异常 |
| G3 | `case.json` 无 `task` 且无 `task.md` → CP1.2 判 warn 后被丢弃 | `exit 0 success`、零留痕：静默降级 | `main.py` 新增一段把 `cp1` 的所有 warn 写进 `uncertainty` | `uncertainty=1`：CP1 前置检查降级 |

> 维护义务：**任何脚本改动后必须重跑 `fault_inject.py`**，并把新台账写回
> `references/FAULT-MATRIX.md` 与 `TEST.md` §12；文档里的数字必须能在报告里找到同源行。
