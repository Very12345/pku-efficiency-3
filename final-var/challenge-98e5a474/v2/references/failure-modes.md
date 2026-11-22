# failure-modes — 失败形态 → 检测 → 处置 → **对对照记录的影响**

本文件沿题面列举的失败形态逐条给出检测机制与处置，并**多一列**：这次失败
会不会污染 `references/GAIN-PROTOCOL.md` 的读数。多这一列的原因很直接：
一次不被记录的降级，会让"增益"看起来比真实更好。

## 1. 失败形态 → 检测 → 处置 → 对测量的影响

| # | 失败形态（题面列举） | 检测机制（真实检查名） | 处置 | 对对照记录的影响 |
|-|-|-|-|-|
| F1 | 把"机制图"当"配图"：只画得好看、无实体关系依据 | `spec.entities` fail；无清单时 `pipeline` fail | 停止出图（宁缺毋滥），写 `failed` 记录 | I2/I4 无读数；记账须注明"未出图" |
| F2 | 实体画错：材料中没有的基因名/浓度/时间点/单位 | `spec.traceability` warn（缺 source/evidence）+ 逐字对照；chart 表外类别由 G8 兜底 | 删条或补 `evidence`，**禁止上图** | I4 会因此掉数，**但这正是真实读数**，不得为好看而补假出处 |
| F3 | 方向颠倒/语义错（抑制画成激活、上下游颠倒） | `spec.relation_kind` fail；`spec.relation_selfloop` warn；relation-dict 给箭头语义 | 回材料用原文动词改写后重跑 | I5 读数 +1 返工轮次；语义错本身机器测不到（见协议 §1.1） |
| F4 | 包含关系画成并列（无分组框） | `spec.containment_arrow` fail + `spec.containment_group` fail + `spec.group_member` fail | 改成分组框表达 | I5 读数变化；返工轮次 +1 |
| F5 | 图例与数据表对不上（缺项/孤儿项） | `spec.legend_missing_kinds` fail / `legend.orphan_items` warn | 以数据表为基准修图例后重跑 | I6 直接读数；修完要重记 |
| F6 | 颜色映射与分类数目不一致 | `spec.color_category_count` fail / `data_mapping.color_count` | 补齐调色板或删冗余类别 | I7 直接读数 |
| F7 | 只有位图：文字不可选、图层不可拆 | `svg.editable_text` / `svg.layers` / `svg.data_entity_attrs` / `svg.data_relation_attrs` / `svg.data_source_attrs` | 手写分层 SVG + `svg.fonttype=none` | I3 直接读数（这是本技能最容易被看出优势的一项） |
| F8 | 导出件不满足期刊要求（DPI/字体/线宽/色彩） | `bitmap.dpi_print`、`bitmap.colourspace`、`pdf.header/pages/fonts_embedded` | 按目标参数重导出；嵌入审计如实标注 | I8 读数；字体嵌入是**尽力而为**，记账要写清 |
| F9 | 改数据后图不更新 | 数据只在清单里；改 `data.table.rows` 后重跑即重绘（实测 sha 变化） | 无需处置（构造上不可能不更新） | I7 的正面证据（R6） |
| F10 | 材料缺失/矛盾/未知 kind 时硬画 | `sources`/`uncertainty` 计数；`spec.relation_kind` fail；`pipeline` fail | 记录并降级；不补造 | **记账必须写"本次读数受降级影响"**，否则读数失真 |
| F11 | 中文字体缺失导致预览乱码 | `textfont.py` 探测 + `font.cjk` warn | SVG 文字仍在；PNG 缺字如实标注 | I8 读数降级；I3 不受影响（文字仍可选中） |
| F12 | PDF 是扫描件/加密件 | `pdftext.py` 报不可抽取（退出码 1/2）+ backend | 不伪造文本；改用可编辑版或 OCR | I4 的分母不可得；记账写"该材料不可用" |

## 2. 测量学上特别危险的分支（协议 G1–G8 的来源）

| 情形 | 为什么危险 | 处置 |
|-|-|-|
| 用 `--skip-checks` / `--no-lint` 跑出的结果 | `verification.checks` 为空 / `spec_lint` 为空对象 ⇒ **未检查被读成已通过** | 该次运行**不计入**对照记录（G1） |
| 降级未记入 `uncertainty` | 降级读数被当成正常读数（I3–I8 虚高） | 降级必须落 `uncertainty` 并在记账标注（G2） |
| 两次运行之间改了画布/`--dpi`/夹具 | 违反 F1/F2 ⇒ 差异无法归因 | 视为不同条件分开记账（G3） |
| 编辑请求没生效但没察觉 | `edit.*` 只进 stdout；`change_records` 为空也可能被当"本来没要求改" | 用"请求条数 vs 记录条数"对拍，不等即判失败（G4） |
| 失败样本被丢弃后重跑 | 选择性报告（F7） | 失败也入库（G5） |
| 没有基线臂就声明"更好" | 不可核验（F8） | 只能写"未测量"（G6） |
| 把 `acknowledged_issues` 核可的 warn 写成 ok | 混淆 ok 与 ack ⇒ I3–I8 虚高 | 记账分列 ok / warn / ack（G7） |

## 3. 常见"看似对实则错"的二义性

| 场景 | 正确做法 |
|-|-|
| "X 抑制 Y" 但材料又说 "Y 通路关闭" | 边方向是 X→Y（inhibition）；进展描述不是关系 |
| "IL-6 上调"到底谁上调谁 | 材料动词归属：NF-κB **上调** IL6 转录 |
| 浓度/时间点出现在文字叙述里 | 只有图表任务才上图；schematic 上的数字必须能溯源到表 |
| 单位不同（µM vs nM） | 以材料表格为准逐字抄写，**绝不换算改写** |
| 图上"看起来重叠" | 布局引擎自动扩展画布/换行；仍溢出则 warn + `uncertainty`，**不要手工挪图破坏可复现性** |

## 4. 处置原则

1. **宁可写"partial + 未测量"，绝不静默绕过**：所有降级落到退出码、`status`、
   `uncertainty` 或 `fails` 至少一个面上。
2. **失败也是数据**：对照记录里"这一臂失败"本身就是最有价值的结论之一。
3. **契约（G1–G8）与 CP1–CP5 是硬约束**，不得为让读数好看而改判据（F5 要求判据固定）。
