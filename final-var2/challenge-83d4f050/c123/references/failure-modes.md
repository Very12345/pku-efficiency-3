# failure-modes.md — 失败模式（按"破坏了哪条机制"归类）

> 本版的组织方式与前两版不同：不问"失败发生在哪个阶段"，而问**"哪条机制被破坏了"**。
> 这样修复指令指向结构（补规格 / 修门 / 补溯源 / 恢复确定性 / 补齐契约），
> 而不是指向现象（"图不好看就调布局"）。
> 机制编号 M1–M6 见 `SKILL.md` §1 与 `references/MECHANISM.md`；修复捷径 K1–K10 见 `SKILL.md` §3。

## 1. 破坏 M1（规格先行）的失败

| # | 失败模式 | 触发信号 | 修复（补机制，而不是改图） | 记录位点 |
|---|---|---|---|---|
| F01 | 材料缺失/目录为空 | CP1.3 fail | 三级查找材料（case 路径 → `--materials-dir` → 同目录）后再谈出图 | `status/reason/uncertainty` |
| F02 | 材料不可结构化（PDF/扫描件） | 抽取器报 `manual-required`；实测 exit **3** | 抽文本 → 仍不行则手工建规格（`extraction.method=manual`） | `extraction.method` |
| F03 | 规格与材料脱钩（实体名/类型凭印象） | 人工核验时对不上材料行号 | 逐条回填 `source[{ref, kind, line}]`；无法定位的项降为 `assumption` | `source[]`、`uncertainty` |
| F04 | 草稿未人工核验就当成品 | `verified_by_agent=false` | 走 CP3；核验前只能 `partial`（exit 2） | `extraction`、`uncertainty` |
| F05 | 只有实体没有关系 | `counts.edges == 0` | 照画并说明"边清单为空"；实体也为空则 `failed`，不画空图 | `status/counts` |
| F06 | 同一分子跨区室被并成一个实体 | 拓扑 P04b | 按区室拆实体并注明去向（跨膜语义会被混淆） | `note`、`topology.json` |
| F07 | 同名基因/蛋白混用 | P04 | 拆两个实体（基因斜体/蛋白正体）或合并 + `uncertain` | `note/uncertainty` |

## 2. 破坏 M2（raw 规格 schema 门）的失败

| # | 失败模式 | 触发信号 | 修复 | 记录位点 |
|---|---|---|---|---|
| F08 | 规格含枚举外类型 | schema 门 fail | **改规格**（不是改图）；改正后重跑 | `reason`（实测：exit 3、只写 `result.json`） |
| F09 | 门被绕过（先归一化再校验） | 把类型改成 `banana` 仍 exit 0 | 把校验点移回**原始规格**；这是门失效的头号原因 | `change_records` |
| F10 | schema 文件缺失 | 检查 `S01` warn | 用内置默认 schema 继续（不阻断），但必须留 warn | `self_check.warnings` |
| F11 | 边端点引用不存在的实体 | 拓扑 P02 fail | 补实体或删边；端点悬空等于画出不存在的论断 | `self_check`、`topology.json` |

## 3. 破坏 M3（双审计）的失败

| # | 失败模式 | 触发信号 | 修复 | 记录位点 |
|---|---|---|---|---|
| F12 | 图面用了某类型但图例未列 | L01/L02 fail | 补图例项 → 重跑（**fail 级，不是 warn**） | `legend_audit.json` |
| F13 | 画布颜色不在图例 ∪ 映射内 | L05 fail | 改回图例色或扩图例 | `legend_audit.json` |
| F14 | 数值找不到来源 | E01 fail / T03 warn | 补 `source`，或降 `assumption` 并停止用它编码颜色 | `uncertainty` |
| F15 | 虚线被用来表达"类型"而非"证据弱/不确定" | L06 fail | 恢复：虚线只表示弱证据/不确定 | `legend_audit.json` |
| F16 | 非反馈边逆流 / 反馈环未标注 | P03 warn / P07 warn | 标 `feedback=true` 右侧绕行，或给出科学理由 | `topology.json`、`uncertainty` |
| F17 | 重复边 / 自环处理不当 | P05 / P06 | 重复边合并并保留全部来源；自环必须写机制依据，否则删除 | `topology.json` |

## 4. 破坏 M4（分层与溯源）的失败

| # | 失败模式 | 触发信号 | 修复 | 记录位点 |
|---|---|---|---|---|
| F18 | SVG 缺层或层名不符 | G4 fail（须 ≥7 个 `layer-*`） | 检查渲染后端；**不得**用扁平 SVG 交付（M4 会整体失效） | `deliverables.editable_sources` |
| F19 | 元素缺 `data-source` | A2 指标下降 / T 系列检查 | 从规格回填来源；规格里没有来源就先补规格（回到 M1） | `self_check` |
| F20 | 只能交位图（无可编辑源） | 请求的格式不含 SVG / SVG 生成失败 | 生成 SVG 是硬要求：失败即 `failed`（exit 3） | `status`、`deliverables` |

## 5. 破坏 M5（确定性）的失败

| # | 失败模式 | 触发信号 | 修复 | 记录位点 |
|---|---|---|---|---|
| F21 | 图件里混入时间戳/随机 id | 双跑 sha256 不一致（非 PDF 项） | 从布局与 SVG 生成里移除时间戳；PDF/`result.json` 例外需如实声明 | `self_check.determinism` |
| F22 | 同输入跑出不同结构 | 双跑结构不同（不是字节不同） | 检查是否读了外部状态（环境变量、系统字体差异、字典遍历顺序） | `TEST.md` 记录 |

## 6. 破坏 M6（契约化终态）的失败

| # | 失败模式 | 触发信号 | 修复 | 记录位点 |
|---|---|---|---|---|
| F23 | 契约字段无值 | 回显缺失 | 四形态填空：标量 `""`/列表 `[]`/布尔 `false`/数值·字典 `0`·`{}`；**顶层禁 null** | `result.json` |
| F24 | `failed` 终态信封不全 | 实测只有 **14 键**（信封 13/19，缺 `title/skill/data_mapping/extraction/export_checks/provenance`） | 若要交付，补写这 6 项空值后再自查；不得把 failed 报成 success | `result.json` |
| F25 | `status`/退出码/`gates` 不一致 | 三元组矛盾 | 以退出码为真，取保守档（success→partial→failed） | `uncertainty` |
| F26 | 审计产物未落盘 | G8 fail | 让 `topology.json` / `legend_audit.json` 写进 `--out` | `deliverables.audits` |

## 7. 破坏链上游优先（修复顺序）

```
M1 材料/规格 → M2 门 → M4 渲染与溯源 → M3 审计 → M6 契约
```

- 上游没修好，下游的修复都是白费力气：规格错了，图例补得再全也只是把错误画得更标准；
- 判断"我在上游还是下游"的办法：**看审计产物里报的是"缺内容"还是"不一致"**——
  缺内容（无来源、无实体）→ 上游；不一致（图例对不上、方向矛盾）→ 中游；信封缺项 → 下游。

## 8. 共同前提（不因机制分类而改变）

- 正式案例必须现场读材料；`examples/` 与 `assets/result.template.json` 都不得冒充正式输出；
- 不写、不预测平台评分；没有的软件状态如实说明；
- 追溯链必须闭合：材料行号 → `source[]` → SVG `data-source` → `evidence_sources` →
  `export_checks[].sha256` → `change_records`。
