# failure-modes — 失败形态 → 检测 → **决策规则 D → 降级档位 L**

> **本版（v4）追加**：上表每一行都配了**真实注入**。把四形态故障逐个弄坏
> 再跑主流程的 25 行实测矩阵（注入什么 → 期望 → 实测退出码/status/
> uncertainty → 是否静默失败）在 `references/FAULT-MATRIX.md`；本轮
> 25/25 符合期望、0 条静默失败，并因此修掉两个真实缺陷（同文件 §5）。
> 其中 **D15（缺运行库）** 一行的行为已按实测收紧：修复前是裸 traceback
> 且不留 `result.json`，现由 `main.py` 的依赖门写成 `status=failed` 记录。

**（v6 追加第二处指针）** 每条失败形态在**题集**里的可复现版本（哪一类案例
会触发它、以什么退出码）见 `references/CASE-SET.md` §4 的 G1–G6 边界表；
两处合起来才完整：本文件说"怎么接住"，CASE-SET 说"在哪类案例上实测到它"。

题面把现有 Agent 的失败形态列得很具体。本文件把**每一类失败**映射成四列：
**检测机制（脚本产出的检查名）→ 处置（D 规则）→ 降级档位（L0–L3）→ 恢复条件**。
四列齐全才算"这条失败被真正接住了"：只有检测没有处置 = 会看到 fail 但不知道干什么；
只有处置没有档位 = 不知道降了多少；没有恢复条件 = 一次降级永久生效。

> 全部检查名的完整清单（含级别与科学含义）在 `references/CHECK-INDEX.md`；
> 检查名与 D 规则、脚本锚点的三点对拍表在 `SKILL.md` §3.5。

## 1. 失败形态 → 检测 → 处置 → 档位

| # | 失败形态（题面列举） | 检测机制（真实检查名） | 处置（D） | 档位 | 恢复条件 |
|-|-|-|-|-|-|
| F1 | 把"机制图"当"配图"：只画得好看、无实体关系依据 | `spec.entities` fail（schematic 无实体清单）；无清单时 `pipeline` fail | **D2** | **L3**（无依据不画） | 抽出至少一条带 source 的实体—关系 |
| F2 | 实体画错：材料中没有的基因名/浓度/时间点/单位上图 | `spec.traceability` warn（缺 source/evidence）+ Agent 逐字对照；chart 表外类别由 G8 兜底 | **D2** | **L2** | 每个实体/关系都有 `source`（+`evidence`） |
| F3 | 方向颠倒/语义错：抑制画成激活、上下游颠倒 | `spec.relation_kind` fail（不可映射）；`spec.relation_selfloop` warn；`assets/relation-dict.json` 给箭头语义 | **D3 / D4** | **L2**（kind）/ **L1**（材料矛盾并列两种说法） | 方向与材料原文动词一致 |
| F4 | 包含关系画成并列（无分组框） | `spec.containment_arrow` fail + `spec.containment_group` fail + `spec.group_member` fail | **D5** | **L2** | containment 落到 `groups` 且成员都是真实实体 |
| F5 | 图例与所依据的数据表对不上（缺项/孤儿项） | `spec.legend_missing_kinds` fail（缺项）/ `legend.orphan_items` warn（孤儿项）/ `data_mapping.legend_consistency` | **D6** | **L2**（缺项）/ **L1**（孤儿项） | 图面箭头类型 ↔ 图例条目双向一致 |
| F6 | 颜色映射与分类数目不一致 | `spec.color_category_count` fail / `data_mapping.color_count` / `data_mapping.rows` | **D7** | **L2** | 调色板颜色数 ≥ 唯一类别数 |
| F7 | 输出只有位图，文字不可选、图层不可拆 | `svg.editable_text` fail（文字被 path 化）/ `svg.layers` fail / `svg.data_entity_attrs` / `svg.data_relation_attrs` / `svg.data_source_attrs` warn | **D13 同族**（渲染参数） | **L2** | 手写分层 SVG + `svg.fonttype=none` |
| F8 | 导出件分辨率/字体嵌入/线宽/色彩不满足期刊 | `bitmap.dpi_print` warn / `bitmap.colourspace` warn / `pdf.header`、`pdf.pages`、`pdf.fonts_embedded` warn / `pdf.readable`、`pdf.exists` fail | **D11 / D13** | **L1**（DPI/色彩/嵌入为 warn 档） | 按目标参数重导出；嵌入审计为尽力而为 |
| F9 | 改动数据后图不更新（不可重绘） | 数据只在清单里：改 `data.table.rows` 后重跑即整体重绘（实测 SVG sha 随之变化） | **D7/D8 的前置** | **L0**（构造上不可能不更新） | — |
| F10 | 材料缺失/描述矛盾/未知 kind 时硬画 | `sources` 与 `uncertainty` 计数；`spec.relation_kind` fail；`pipeline` fail | **D2 / D3 / D4** | **L1**（缺材料）/ **L2**（未知 kind）/ **L3**（无依据） | 补齐材料或用材料原文动词重写 kind |
| F11 | 中文字体缺失导致预览乱码 | `textfont.py` 探测 + `font.cjk` warn（`render.cjk_ok=false`） | **D11** | **L1** | 目标机装上任一候选 CJK 族 |
| F12 | PDF 是扫描件/加密件 | `pdftext.py` 报不可抽取（退出码 1/2）+ backend 记录 | **D12** | **L3**（该材料不可用） | 取得可抽取文本的版本或先 OCR |

## 2. 属于"环境/参数"而非"科学内容"的失败（基线未单列）

| 情形 | 检测机制 | 处置（D） | 档位 | 恢复条件 |
|-|-|-|-|-|
| 缺第三方 PDF 库 | `pdftext.py` 记录 backend = stdlib 回退 | **D14** | **L1** | 装上 fitz/pypdf |
| 缺 matplotlib / Pillow / numpy | **依赖门**（`main.py` 在解析完 case、建好输出目录后检查 import 结果）+ `uncertainty` 写明缺失模块 | **D15** | **L3** | 安装运行必需库（提示原文含 `pip install matplotlib pillow numpy`） |
| 用了 `--skip-checks` / `--no-lint` | `verification.checks` 为空 / `spec_lint` 为空对象 | **D16** | **L1** | 交付前用默认参数完整重跑 |
| 窄编码控制台（GBK） | 非 ASCII 输出被替换为 `?`；脚本导入区已 `reconfigure(errors="replace")` 兜底 | — | **L1** | 设 `PYTHONIOENCODING=utf-8` |
| `--exports tiff,eps` 体积失控 | TIFF 为未压缩大图（实测约 46 MB） | — | **L1** | 降 `--dpi` 或只交付 PDF |
| 编辑目标 ID 写错 / 用了 `target` 字段 | 日志 `[edit] fail unknown relation …`；`change_records` 为空；**退出码不变** | **D10** | **L2** | 用 `relation_id`/`entity_id` 重写后重跑，并对拍条数 |

> **D10 特别说明（不掩盖）**：`edit.*` 问题目前**只出现在 stdout**，不写进
> `result.json`、不影响退出码。因此"编辑请求被拒"必须由 Agent 用
> "请求条数 vs `change_records` 条数"对拍发现。这条限制写在
> `references/CHECK-INDEX.md` §3 与 `references/EDIT-ACTION-SCHEMA.md` §3，
> 并在 `SKILL.md` 的自查清单里成为一条硬性勾选项。

## 3. 常见"看似对实则错"的二义性

| 场景 | 正确做法 | 依据 |
|-|-|-|
| "X 抑制 Y" 但材料又说 "Y 通路关闭" | 边方向是 X→Y（inhibition），不是 Y→X；进展描述不是关系 | `spec.relation_kind` + relation-dict |
| "IL-6 上调" 到底谁上调谁 | 材料动词归属：NF-κB **上调** IL6 转录（NF-κB→IL6, transcriptional） | 同上 |
| 浓度/时间点出现在文字叙述里 | 只有图表任务才上图；schematic 上出现数字必须能溯源到表 | `spec.traceability` |
| 单位不同（µM vs nM） | 以材料表格为准逐字抄写，**绝不换算改写**（数字是事实输入） | `data_mapping.unit` |
| 画布小、字多 | 布局引擎自动扩展画布/换行；仍溢出则记 warn 与 `uncertainty` | `spec.canvas_bounds` |

## 4. 处置原则（与 SKILL.md §3.2 的两条不变式对应）

1. **宁可 L2 说明，绝不静默绕过**：任何降级都必须落到退出码、`status`、
   `uncertainty` 或 `fails` 至少一个面上（不变式 A）；检测不到的降级按未发生处理。
2. **出口必须一致**：CLI 退出码与 `result.json.status` 必须同向（不变式 B）；
   两者冲突时以 `result.json` 为记录面、退出码为重试面，并把冲突写进 `uncertainty`。
3. **契约（G1–G8）与 CP1–CP5 是硬约束**，不得为"看起来好看"而删改；
   所有降级都要能被第三方按 §1 的检查名逐条复跑。
