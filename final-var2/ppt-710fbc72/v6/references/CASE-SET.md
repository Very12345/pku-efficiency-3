# CASE-SET — 合成题集、可接受区间与逐案实测（v5）

本文件给出本包自带题集的三件事：**每案的输入形态、期望产出结构、可接受区间与难度层**；
**每案在本机真跑出来的数字**；以及**这套泛化在哪里会失效**（§4，最该读的一节）。

题集是**合成示意案例**（`_meta` 与材料首行都写明"非真实研究结果"），用途是让"换个题材、
换个页预算、换成退化输入还能不能跑"变成可测量的东西。**它不冒充平台正式案例，也不是白板。**

> 复跑一条命令（在**包外**临时副本上跑；脚本会拒绝把工作目录设在包内）：
>
> ```bash
> RUN=<可写临时目录>; cp -r "$SKILL_DIR" "$RUN/pkg"
> python "$RUN/pkg/scripts/run_case_set.py" --skill "$RUN/pkg" \
>     --cases "$RUN/pkg/examples" --run "$RUN/caseset" \
>     --json "$RUN/caseset.json" --markdown "$RUN/caseset.md"
> # 实测：3 个案例，0 个超出声明区间，1 个已声明边界命中，退出码 0
> ```
>
> 声明与判定同源：区间写在 `examples/cases/case_manifest.json`，测量由
> `scripts/run_case_set.py` 完成；两者不一致时报告 `RANGE-MISS`，不会静默算作通过。

---

## 1. 题集总览

| # | 案例 | 难度层 | 题材 | 页预算 / 时长 | 图 | 表 | 结构化字段 | 这案在考什么 |
|-|-|-|-|-|-|-|-|-|
| A | `example-catalyst-201` | **L0** 基线接口 | 催化化学（Cu-ZnO/γ-Al₂O₃ 双金属催化剂，CO₂ 加氢制甲醇） | 10 页 / 12 min | 2 | 1 | 完整 | 接口没被改坏的回归基线 |
| B | `case-b-gnn-potential-301` | **L1** 结构完整 | 计算材料（图神经网络势函数 + 固态电解质 Li₆PS₅Cl 的锂离子输运 MD） | 12 页 / 15 min | 2 | 1 | 完整（39 条 `material.md:N` 定位） | 换题材、换页预算后页型序列与批量规则是否仍然成立 |
| C | `case-c-uhi-remote-302` | **L2** 退化输入 | 城市环境遥感（Landsat 9 + Sentinel-2 地表温度反演与城市热岛归因） | 9 页 / 10 min | 1 | 1（无 rows） | **只给最小 12 键**；六个故事线字段全部缺席 | 主线能否真的从 `material.md` 的 `#` 小节里抽出来 |

**为什么难度层这么分**：L0 是"接口对不对"，L1 是"换个题材还行不行"，L2 是"输入烂了还行不行"。
三层各自对应一组不同的代码路径 —— L2 走的正是 `extract.py` 的
`supplemented_from_material` 那条补位分支，L0 永远走不到它，所以 L0 通过**不能**推出 L2 通过。

### 各案的输入形态

| 案例 | `case.json` 给了什么 | `material.md` | 图件如何来 |
|-|-|-|-|
| A | 全部字段（research_question / methods / results / discussion / limitations / conclusion / key_numbers / figures / tables / output_contract） | 6 个 `##` 小节，38 行 | 包里没有二进制 ⇒ 运行前用 `make_synthetic_inputs.py` 现场合成 `figs/fig1.png`、`figs/fig2.png` |
| B | 同上，且 39 条 `source` 全部形如 `material.md:N` | 6 个 `##` 小节，52 行 | 同上（本案例恰好引用两张图） |
| C | **只有** `case_id / _meta / title / subtitle / audience / duration_minutes / slide_count / language / source_material / figures / tables / output_contract` | 6 个 `##` 小节，51 行 | 同上，本案例只引用 `figs/fig1.png` |

### 每案的期望产出结构与可接受区间

期望产出结构（三案相同，即 `references/OUTPUT_CONTRACT.md` 定义的形态）：
`<case_id>_deck.pptx`（可编辑、页数=计划） + 两张预览 PNG（示意图，如实标注）
+ `result.json`（契约字段全回显、无 `null`） + `spec.json` / `adopt_plan.json` / `content.json`
+ `audit.json` / `render_log.json` / `summary.txt`。

| 判据 | A | B | C | 为什么是这个区间 |
|-|-|-|-|-|
| `status` | ∈ {success, partial} | ∈ {success, partial} | ∈ {success, partial} | L2 的表格无 `rows` ⇒ 必然有 warn，`partial` 是**正确**结果而非缺陷 |
| `slide_count` | **= 10** | ∈ **[12, 13]**（见 §4.1） | **= 9** | 页计划是确定性纯函数，页预算由案例冻结，所以 A/C 要求精确；B 的区间与理由在 §4.1 |
| 讲稿覆盖率 `notes_pages / slide_count` | ≥ 1.0 | ≥ 1.0 | ≥ 1.0 | 逐页 speaker notes 是本包的基本承诺 |
| 证据定位覆盖率 `evidence_loc_frac` | ≥ 0.90 | ≥ 0.90 | ≥ 0.90 | 页级主张必须带 `文件:行` |
| 图表落位 `figures_embedded / figures_total` | ≥ 1.0 | ≥ 1.0 | ≥ 1.0 | 图上位率；不达标说明 contain-fit 或图位路径坏了 |
| CP3 契约门通过数 | = 8 | = 8 | = 8 | G1–G8 全过是交付门 |
| 顶层 `null` 键数 | = 0 | = 0 | = 0 | 契约禁止 `null` 占位 |
| 方案套用率 `adopt_plan_applied / total` | ≥ 1.0 | ≥ 1.0 | ≥ 1.0 | 方案↔执行一致性 |
| 材料补位桶数 | 不要求 | 不要求 | **必须 6/6** | L2 的核心考点：故事线只能来自材料 |

## 2. 逐案实测结果（本次真跑，非估计）

环境：Windows 11 + Git Bash；Python 3.13.9；python-pptx 1.0.2 / Pillow 12.3.0；
无 LibreOffice / PowerPoint（预览为 PIL 示意图，如实标注）。三案**各自独立子进程**，
输出目录在包外临时区。

| 判据 | A 实测 | B 实测 | C 实测 |
|-|-|-|-|
| `main.py` 退出码 | **0** | **0** | **0** |
| `status` | `success` | `partial` | `partial` |
| `slide_count`（声明） | **10**（=10） | **13**（∈[12,13]） | **9**（=9） |
| 讲稿覆盖 | 10/10 = **1.00** | 13/13 = **1.00** | 9/9 = **1.00** |
| 页级证据页数 / 证据行数 | 10 页 / 13 行 | 13 页 / 26 行 | 9 页 / 34 行 |
| 证据定位覆盖率 | **1.000** | **1.000** | **1.000** |
| 图表落位 | 2/2 | 2/2 | 1/1 |
| 模板来源 `opened_from` | `builtin` | `builtin` | `builtin` |
| 版式使用记录条数 | 10 | 13 | 9 |
| 方案套用 | 10/10，偏差 0 | 13/13，偏差 0 | 9/9，偏差 0 |
| CP3 门 | **8/8** | **8/8** | **8/8** |
| 顶层 `null` 键 | 0 | 0 | 0 |
| `artifacts` 条数 / 顶层键数 | 8 / 28 | 8 / 28 | 8 / 28 |
| `uncertainty` 条数 | 1 | 2 | 3 |
| `supplemented_from_material` | —（用不到） | —（用不到） | **6/6 全命中** |
| 审计中非 `ok` 的检查 | 无 | `content.claim_coverage` warn | `content.claim_coverage` warn |
| **判定** | **in-range** | **boundary-hit**（已声明） | **in-range** |

三案的**共同点**值得单独指出：`evidence_loc_frac` 全部为 **1.000**、CP3 门全部 **8/8**、
顶层 `null` 全部为 **0**、方案套用全部 **10/10、13/13、9/9 且偏差 0**。也就是说，
**换题材（催化→计算材料→遥感）、换页预算（10→12→9 页）、换输入完整度（完整→最小字段）
之后，契约层与证据层没有退化**。退化只出现在 §4 列出的两处，而且两处都被审计抓到了。

### L2 的关键证据：主线确实是从材料里抽出来的

案例 C 的 `case.json` 里**没有** `research_question / methods / results / discussion /
limitations / conclusion / key_numbers`，而运行后的 `content.json` 给出：

```text
supplemented_from_material = {question: true, methods: true, results: true,
                              discussion: true, limitations: true, conclusion: true}
sections 条数              = question 6 / methods 8 / results 7 / discussion 5 /
                              limitations 5 / conclusion 3
每条来源定位               = material.md:<行号>（例如 question→material.md:2、
                              results→material.md:26、limitations→material.md:42）
材料行数                    = 52（extract 报 lines=52）
```

⇒ 六个故事线桶**全部由材料补位**，且每条都带 `material.md:行` 定位。这是"退化输入"
这条路径真实可用的直接证据，不是设计声明。

## 3. 题集的资源形态（为什么案例目录里没有 `figs/`）

题面硬约束 *at most 50 UTF-8 text files, 500KB each and 2MB total, no symlinks*
⇒ 包内**只能有文本**，所以三个案例目录里都**没有** `figs/*.png`。图件由
`scripts/make_synthetic_inputs.py` 在运行时合成（纯几何 + `SCHEMATIC / 示意` 水印，
不含任何伪造的测量数值，避免被误当成真实数据）。

`run_case_set.py` 的做法是：**先把案例复制到包外**，再对副本跑
`make_synthetic_inputs.py --out-dir <副本>/figs`，然后才跑主流程。
这样既满足硬门，又不会在包里留下 `.pyc` 或图片。

## 4. ★ 泛化到哪里会失效（如实写明）

这一节是本次题集最有价值的产出：**以下 3 条是实测暴露出来的边界，全部可复现，全部有数字。**

### 4.1 页预算会被"带媒体的结果条目数"顶破 —— 确定性裁剪最多只能回收 3 页

**现象**：案例 B 声明 12 页，实测 **13 页**（`planned_slides=13, target_slides=12`），
`status` 因此降为 `partial`。

**根因**（读 `scripts/deckplan.py` 的分支 + 实测复现）：

1. 案例 B 的 7 条 `results` 里，**7 条各自引用了图或表**（图 1、图 2、表 1 交叉出现）。
2. `deckplan.py` 的"每条结果一页"分支需要 `(target - fixed - 3) >= result_pages_needed`。
   `fixed = 5`、`target = 12` ⇒ 左边 = **4**，右边 = **7** ⇒ 条件不成立。
3. 于是走另一分支：**每条带媒体的结果各占一页** ⇒ 结果页 **7 张**。
4. 尾部裁剪策略是一次性的三步：**合并讨论+局限 → 删议程 → 合并末两页结果**，
   也就是**最多回收 3 页**。本案例需要回收的比 3 页更多（1 封面 + 1 背景 + 1 方法 +
   7 结果 + 讨论 + 局限 + 结论 = 13 页主体，目标主体 10 页）⇒ 裁完仍是 11 页主体，
   加上证据映射与致谢两页附录 = **13**。

**为什么会这样（不是 bug 的辩护，是机制说明）**：裁剪顺序是**刻意固定**的
（"证据页最后才动"，见 D9/D11），固定顺序换来的是可预测性与可复跑性；代价是
**回收能力有上限**。当案例的媒体条目数超过页预算能容纳的量时，本包选择
**如实地多出一页并记录**，而不是偷偷丢掉证据页或把两页硬挤成一页。

**判别与规避**：

- 判别：`result.json.main_result.planned_slides > target_slides`；
  `spec.json` 里 `results` 页数 = 带媒体的结果条目数。
- 规避（给案例作者）：让多条结果共用一个图表引用（把"图 2 的两条主张"写成一条），
  或者把页预算提高，或者接受这一页并让 status 停在 `partial`。
  **本包不会替调用方删证据。**

> 这条边界在案例 B 上是"声明 12、实测 13"，所以清单里把它写成区间 **[12, 13]** 并附这段
> 理由，由 `run_case_set.py` 判为 `boundary-hit`（**不是** `in-range`，也**不是**静默通过）。
> 上限 13 是实测值，不是设计目标。

### 4.2 "只有表格、没有图"的结果页会丢掉它自己的主张条目

**现象**：案例 B 第 8 页（`结果 5`，只放表 1）在幻灯片上**只有**标题、表题行
`1  不同温度下的 Li⁺ 电导率与迁移数统计  [来源: material.md:33]` 与页脚 ——
计划里的主张条目 `表1 汇总不同温度下的 Li⁺ 电导率与迁移数统计。` **没有出现在页面上**。
对照第 9 页（同时有图和表）主张条目**正常写出**。

**检出方式**：`audit.py` 的 `content.claim_coverage` 检查逐页抽取主张前 18 个字符、
在全册文本里做字面匹配，命中不到就 warn —— 实测报文原文：

```text
content.claim_coverage | warn | 1 claims not literally found;
    truncated: ['p8:表1 汇总不同温度下的 Li⁺ 电导']
```

于是 `status` 降为 `partial`，并且这条 warn 被写进 `uncertainty`。
**同理**：案例 C 第 5 页（只放表 1）也丢掉主张 `表1：热岛强度的归因分解结果。`，
warn 报文里报 2 条（另一条见 §4.3）。

**结论**：这是**已检出、已降级、未修复**的行为。按本轮约束（既有脚本尽量逐字节不变，
只允许纯增量修真实缺陷）本包**没有**改 `adapt_pptx.py` 的版式路径；本文件把它如实登记，
供使用方决定：要么给"只有表"的结果条目补一条图引用，要么接受 `partial` + 这条 warn。

### 4.3 一条结果页塞太多主张时，末尾的主张会被文本框装不下而丢掉

**现象**：案例 C 第 4 页把 **6 条**主张分到同一页（因为它们都不带媒体引用，
被 `deckplan.py` 归到同一个收集页）。幻灯片上实际只写到第 4 条末尾就断了
（正文在"研究区夏季平均热岛强度为"处截断），**第 5、6 条没有出现**。

**检出方式**：同样是 `content.claim_coverage` warn，报文原文：

```text
content.claim_coverage | warn | 2 claims not literally found;
    truncated: ['p4:热岛强度在夜间为 2.1 K，低于白', 'p5:表1：热岛强度的归因分解结果。']
```

**为什么没被字号阶梯救回来**：字号阶梯只负责把字号往下压到 12pt 为止；
**压到地板仍装不下时，本包的策略是"只报告、不继续压"**（D9 / F12），
因为把字压到不可读比少写一条主张更糟。这条取舍是有意的，代价就是这里看到的丢条。

**规避**：给这类页面的主张数量设上限（案例作者控制），或者接受 warn + `partial`。

### 4.4 题集**没有**覆盖的东西（别把这三案当成泛化的全部证据）

- **没有跨模板族**：三案的模板链全部落到运行时生成的内置回退模板
  （`opened_from=builtin`）。**多母版、多主题、商业模板族、SmartArt 全部没测。**
- **没有真 PDF/像素级导出一致性**：本机无 LibreOffice/PowerPoint，预览是 PIL 示意图，
  因此"导出件与 pptx 渲染一致"这一项只测到"有/无有效预览"，**测不到像素级差异**。
- **没有中文以外的语言**：三案 `language` 都是 `zh`，`en` 分支（`deckplan.py` 的 `T()`）
  未跑。
- **没有**起始 deck 编辑场景：三案都没给 `starting_deck`，所以
  `change_records[].action=edit_starting_deck` 与"旧页连关系一起移除"这条路径
  在本题集里**未被覆盖**（它在 `TEST.md` §4c 有单独用例，但不在题集里）。
- **没有超长材料**：三案材料都在 51–52 行量级，**没有**测过上百行的长材料与
  由此带来的抽取/分页压力。
- **没有多图并排**：每页最多 2 张图（案例 B 第 9 页），没有测过 3 张以上并排。

### 4.5 题集**不能**用来做什么

- 不能当作平台正式案例或白板：组织方的 3 个固定案例与对照由平台提供/生成，
  **本包不预置白板、不冒充成绩**。
- 不能当作分数预测：这里的 `in-range` / `boundary-hit` 是本包自己声明的区间，
  与平台评分无关。
- 不能当作"质量更好"的证明：题集只回答"**能不能跑、跑出来是什么形状**"，
  不回答"讲得好不好"。质量对照的口径在 `references/GAIN-PROTOCOL.md`。

## 5. 维护约定

新增案例时同步做四件事：

1. 在 `examples/cases/<case-dir>/` 放 `case.json` / `task.md` / `material.md`；
2. 在 `examples/cases/case_manifest.json` 加一条，写清 **难度层**、**期望产出结构**、
   **可接受区间**与**这案在考什么**；
3. **真跑一次** `run_case_set.py`，把实测数字补进 §2；
4. 若发现新的失效方式，追加进 §4 并写明根因 —— **不要把区间改宽来掩盖实测**；
   要改区间，必须像 §4.1 那样附上可复现的理由与实测上限。

新增案例的**格式红线**（踩了会静默抽不到东西）：

- 图/表标题行必须写成 `图1：…` / `表1：…`（**图号后紧跟中文全角冒号**）；
  `图1 催化剂…`（用空格分隔）**匹配不上** `extract.py` 的标题正则；
- 材料小节标题必须含 `extract.py` 的分桶关键词（背景/问题/引言、方法/实验、结果/数据/图/表、
  讨论、限制/局限/不足、结论/总结）；
- 小节内的编号不要写成 `2.1 xxx` 形式（会被误判成小节标题并清空分桶），
  用 `（1）` 这类中文括号编号。
