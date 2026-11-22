# failure-modes — 失败形态 → 检测 → 处置 → **由哪个机制负责**

题面把现有 Agent 的失败形态列得很具体。本文件逐条映射到**检测机制（真实检查名）**、
**处置**，并多一列：**这条失败由哪个机制负责**。多这一列的目的是让"机制"这个说法
落在具体失败上——如果一个失败形态没有任何机制对它负责，那机制清单就是装饰。

> 机制的定义、**没有它会怎样**、**可证伪判据**与**已知盲区**见
> `references/MECHANISM.md`；检查名的完整清单见 `references/CHECK-INDEX.md`。

## 1. 失败形态 → 检测 → 处置 → 负责机制

| # | 失败形态（题面列举） | 检测机制 | 处置 | 负责机制 |
|-|-|-|-|-|
| F1 | 把"机制图"当"配图"：只画得好看、无实体关系依据 | `spec.entities` fail；无清单时 `pipeline` fail | 停止出图，写 `failed` 记录 | **M1** |
| F2 | 实体画错：材料中没有的基因名/浓度/时间点/单位 | `spec.traceability` warn + 逐字对照；chart 表外类别 G8 兜底 | 删条或补 `evidence`，禁止上图 | **M1** |
| F3 | 方向颠倒/语义错（抑制画成激活、上下游颠倒） | `spec.relation_kind` fail；`spec.relation_selfloop` warn；relation-dict 给箭头语义 | 回材料用原文动词改写后重跑 | **M1**（语义本身属 M1 盲区） |
| F4 | 包含关系画成并列（无分组框） | `spec.containment_arrow` + `spec.containment_group` + `spec.group_member` | 改成分组框 | **M1** |
| F5 | 图例与数据表对不上（缺项/孤儿项） | `spec.legend_missing_kinds` fail / `legend.orphan_items` warn | 以数据表为基准修图例 | **M1** + **M4** |
| F6 | 颜色映射与分类数目不一致 | `spec.color_category_count` fail / `data_mapping.color_count` | 补齐调色板或删冗余类别 | **M1** |
| F7 | 只有位图：文字不可选、图层不可拆 | `svg.editable_text` / `svg.layers` / `svg.data_entity_attrs` / `svg.data_relation_attrs` / `svg.data_source_attrs` | 手写分层 SVG + `svg.fonttype=none` | **M2** + **M4** |
| F8 | 导出件不满足期刊要求（DPI/字体/线宽/色彩） | `bitmap.dpi_print` / `bitmap.colourspace` / `pdf.*` | 按目标参数重导出；嵌入审计如实标注 | **M4** + **M5** |
| F9 | 改数据后图不更新 | 数据只在清单里；改 `data.table.rows` 后重跑即重绘（实测 sha 变化） | 无需处置（构造上不可能不更新） | **M1** + **M2** |
| F10 | 材料缺失/矛盾/未知 kind 时硬画 | `sources`/`uncertainty` 计数；`spec.relation_kind` fail；`pipeline` fail | 记录并降级；不补造 | **M1** + **M3** |
| F11 | 中文字体缺失导致预览乱码 | `textfont.py` 探测 + `font.cjk` warn | SVG 文字仍在；PNG 缺字如实标注 | **M5** + **M4** |
| F12 | PDF 是扫描件/加密件 | `pdftext.py` 报不可抽取（exit 1/2）+ backend | 不伪造文本；改用可编辑版或 OCR | **M3** |

## 2. 机制盲区对应的失败（**没有机制负责**的那几类，必须写出来）

| 情形 | 为什么机制接不住 | 当前的替代判据 |
|-|-|-|
| 编辑请求未生效（目标 id 不存在 / 字段名写错） | `edit.*` 问题只进 stdout，不进 `result.json`、不改退出码（**M2 盲区**） | "请求条数 vs `change_records` 条数"对拍 |
| "抑制画成激活"这类**语义**错误 | M1 只判结构（kind 是否可映射），判不了生物学对错 | 材料原文动词逐条对照 + 人工/LLM 复核 |
| 图面审美（重叠观感、配色是否好看） | M4 只做阈值与结构判断 | 人工复核；不声称 |
| 扫描件内容缺失 | M3 的职责是"如实报告不可抽取"，不是"抽出来" | 报告 + 索要可编辑版 + 外部 OCR |
| 用了 `--skip-checks` / `--no-lint` 的结果 | 机制被显式关闭（M1/M4 都不运行） | 交付前用默认参数完整重跑一次 |

## 3. 常见"看似对实则错"的二义性

| 场景 | 正确做法 | 相关机制 |
|-|-|-|
| "X 抑制 Y" 但材料又说 "Y 通路关闭" | 边方向是 X→Y（inhibition）；进展描述不是关系 | M1 |
| "IL-6 上调"到底谁上调谁 | 材料动词归属：NF-κB **上调** IL6 转录 | M1 |
| 浓度/时间点出现在文字叙述里 | 只有图表任务才上图；schematic 上的数字必须能溯源到表 | M1 |
| 单位不同（µM vs nM） | 以材料表格为准逐字抄写，**绝不换算改写** | M1 |
| 图上"看起来重叠" | 布局引擎自动扩展画布/换行；仍溢出则 warn + `uncertainty` | M4 |

## 4. 处置原则

1. **宁可 partial 说明，绝不静默绕过**：所有降级落到退出码、`status`、
   `uncertainty` 或 `fails` 至少一个面上；
2. **每条降级都要指到一个机制**（§1 的第 5 列）；若指不到，说明要么该机制
   覆盖不全（应补判据），要么这条失败本来就不该由机制负责（应在 §2 里写明）；
3. **契约（G1–G8）与 CP1–CP5 是硬约束**，不得为让结果好看而删改判据。
