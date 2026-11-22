# failure-modes — 本题失败形态与处置

题面明确列出了现有 Agent 的失败形态。本文件把每一类失败映射到
**检测机制（脚本）** 与 **处置（决策规则 D / 检查点 CP）**，确保
正式运行时不重蹈覆辙。逐条自查时对照本表与 `assets/checklist.json`。

## 1. 失败形态 → 检测 → 处置

| # | 失败形态（题面列举） | 检测机制 | 处置（规则） | 不踩的后果 |
|-|-|-|-|-|
| F1 | 把"机制图"当"配图"：只画得好看、无实体关系依据 | CP1 spec_lint：无 entities（schematic）即 fail；每个 entity 需 source+evidence | D2：材料外实体禁止上图；无清单停止（宁缺毋滥） | 图一出生就无依据，无法复核 |
| F2 | 实体画错：材料中没有的基因名/浓度/时间点/单位上图 | `spec_lint`（结构）+ Agent 自查（材料逐字对照） | D2：清单里出现材料外词 → 删掉或加 evidence；G8 对 chart 表外类别 INVALID | 审稿人对照材料必查出为假 |
| F3 | 方向颠倒/语义错：抑制画成激活、上下游颠倒 | DP：关系 kind 走 relation-dict（activation≠inhibition）；方向以材料动词为准 | D3：方向冲突取有证据的一种，另一种写 uncertainty；材料明示误区必须落实 | 机制图方向错 = 科学结论错，最致命 |
| F4 | 包含关系画成并列（无分组框） | `spec.containment_group`/`spec.containment_arrow` fail；containment 必须 groups | D4：containment 一律用分组框，不画箭头 | 层级结构表达错误 |
| F5 | 图例与所依据数据表对不上（缺项/孤儿项） | `spec.legend_missing_kinds` fail / `legend.orphan_items` warn；双向比对 | D5：以数据表为基准修正图例后重跑 | 图例-图面不一致是审稿最常见硬伤 |
| F6 | 颜色映射与分类数目不一致 | `spec.color_category_count`（palette≥类别数）/ `data_mapping.color_count` | D6：调色板补齐或按类别数自动分配，重跑 | 颜色对不上类别 = 读者无法读图 |
| F7 | 输出只有位图，文字不可选、图层不可拆 | `svg.editable_text`（<text> 存在、无 path 化）+ `svg.layers` + `svg.data_*_attrs` | 手写分层 SVG + `svg.fonttype=none`；缺图层即 fail | 改一个标签要整张重画 → 失去可编辑性 |
| F8 | 导出件分辨率/字体嵌入/线宽/色彩不满足期刊 | `bitmap.dpi_print`（18cm 有效 DPI ≥300/≥150）、`bitmap.colourspace`、`pdf.*` | D8：按导出参数重导出；PDF 字体嵌入审计如实标注（尽力而为） | 投出去被要求重做 → 返工 |
| F9 | 改动数据后图不更新（不可重绘） | 数据驱动：manifest.data 即唯一数据源，重跑即更新 | 修改 manifest 数据 → main.py 重跑 → checks 全过 | 数据-图无法同步 = 维护死胡同 |
| F10 | 材料缺失/描述矛盾/未知 kind 时硬画 | 读取真实文件并记录 missing；kind 未知即 fail | D1：缺材料记录+partial；矛盾取有证据者；未知 kind 回材料用词重写，不猜箭头 | 编造缺失状态 = 失信 |
| F11 | 中文字体缺失导致预览乱码 | `textfont.py` 探测 + `font.cjk` check + uncertainty 记录 | D7：SVG 文字仍在；PNG/PDF 缺字如实标注 | 中文标注乱码被误读 |
| F12 | PDF 是扫描件/加密件 | `pdftext.py` 检测加密/无文本 → 明确失败信息 | D1/D12：报告不可抽取，不伪造文本；用 OCR 或索要可编辑版 | 把空白页当文本 = 造假 |

## 2. 常见"看似对实则错"的二义性

| 场景 | 正确做法 |
|-|-|
| "X 抑制 Y" 但材料又说 "Y 通路关闭" | 边方向是 X→Y（inhibition），不是 Y→X；进展描述不许当关系 |
| "IL-6 上调" 到底是谁上调谁 | 材料动词归属：NF-κB **上调** IL6 转录（NF-κB→IL6, transcriptional） |
| 浓度/时间点出现在文字叙述中 | 图表任务才上图；schematic 上出现数字必须能溯源到表 |
| 单位不同（µM vs nM） | 以材料表格为准逐字抄写，绝不换算改写（数字是事实输入） |

## 3. 运行时异常 → 处置（与 SKILL.md §5 异常表对应）

| 异常 | 处置 |
|-|-|
| 来源材料文件缺失 | 记录 sources/uncertainty；以已读材料继续；多处缺失 → status=partial 并说明 |
| case.json 无 manifest 且无 entities/relations | 停止（D12）——不画无依据的图；写 failed result.json |
| render 抛异常 | 捕获 → 写 status=failed 的 result.json（pipeline fail 明细），产物不丢失 |
| 编辑目标 SVG 无内嵌清单 | 拒绝源文件级编辑，说明需先用本 skill 生成 |
| 字体缺失 | textfont 探测 → 用可用族渲染 + `font.cjk` warn + uncertainty |
| PDF 无第三方库 | pdftext stdlib 回退（zlib+Tj/TJ），warnings 记录；抽不出文本 → 如实报告 |

> 处置原则：**宁可 partial 说明，绝不静默绕过**（对应 SKILL.md 第 10 节
> 禁止事项）。契约（OUTPUT_CONTRACT 的 G1–G8）与 CP1–CP5 检查门是硬约束，
> 不得为"看起来好看"而删改；所有降级都必须落到 `uncertainty` 或
> `acknowledged_issues` 里，供复核者逐条对照。