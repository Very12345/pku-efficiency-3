# TEST（v5）—— 多案例泛化与题集实测记录

> 本文件是 **v5（多案例泛化与题集包）** 的实测记录。数字来自本轮
> `scripts/run_case_set.py` 的一次真实运行（3 条案例记录）与
> `references/CASE-SET.md` 已登记的实测明细；凡有出处的都注明出处，
> 找不到出处的项宁可留白。命令占位符：`$SKILL_DIR` = 本包根目录
> （平台装到 `/skills/weekly-skill`）；`$RUN` = 包外**可写**临时目录。

---

## 0. 环境

| 项 | 值 |
|-|-|
| 系统 | Windows 11 + Git Bash（MSYS2） |
| Python | 3.13.9（报告自身的 `python` 字段也是 `3.13.9`） |
| 运行时依赖 | python-pptx 1.0.2 / Pillow 12.3.0 |
| 预览 | **无 LibreOffice / PowerPoint** ⇒ 预览为 PIL 示意图（如实标注，不产伪 PDF） |
| 案例形态 | 三案均为**合成示意案例**（非真实研究结果，`language` 均为 `zh`） |
| 图件来源 | 包内无二进制 ⇒ 运行前由 `make_synthetic_inputs.py` 现场合成（三案 `figure_synthesis_exit` 均为 **0**，产物 `fig1.png` / `fig2.png`） |
| 报告生成时间 | 2026-11-22 19:57:24 +0800（Asia/Shanghai） |

三案**各自独立子进程**，输出目录都在**包外**临时区；单案耗时 1.47 / 1.55 / 1.48 秒。

---

## 1. 题集总结果

**3 个案例 / 0 个超出声明区间 / 1 个已声明边界命中 / 退出码 0。**

报告的顶层字段直接给出前三个：`case_count = 3`、`out_of_range = 0`、
`boundary_hits = 1`；三案的 `exit` 全为 **0**、`problems` 全为空列表。
那个唯一的「边界命中」是案例 B，**它是清单里事先声明过的区间**（见 §2 与 §6），
不是漏判。

### 1.1 三案的判定分布

| 判定 | 案例数 | 案例 |
|-|-|-|
| `in-range` | **2** | `example-catalyst-201`（L0）、`case-c-uhi-remote-302`（L2） |
| `boundary-hit` | **1** | `case-b-gnn-potential-301`（L1） |
| `RANGE-MISS` / 崩溃 | **0** | —— |

### 1.2 为什么 `status` 有两个 `partial`

`status` 分布是：`success` **1** 个（A）、`partial` **2** 个（B、C）。
这两个 `partial` **都不是崩溃，也不都是缺陷**：

- **C 的 `partial` 是正确结果**：它的表格没有 `rows`，按契约必然产生 warn，
  所以清单里把三案的 `status` 区间都写成 `∈ {success, partial}`；
- **B 的 `partial` 是真实退化**：页预算被顶破（13 > 12）+ 一条主张条目没落到页面上（见 §4）。

**契约门与它们是两回事**：三案的 `contract_gates_failed` 都是空列表、
`contract_gates_pass` 都是 **8**，即 CP3 的 G1–G8 全过。
`status` 说的是「这一册有没有降级」，契约门说的是「交付形态合不合规」。

### 1.3 三案的共同项（契约层与证据层没有退化）

| 项 | A | B | C |
|-|-|-|-|
| `contract_gates_pass` | 8 | 8 | 8 |
| `contract_gates_failed` | `[]` | `[]` | `[]` |
| 顶层 `null` 键 `null_top_keys` | 0 | 0 | 0 |
| 顶层键数 `top_keys` | 28 | 28 | 28 |
| `evidence_loc_frac` | 1.0 | 1.0 | 1.0 |
| 方案套用 `adopt_plan_applied` | 10/10 | 13/13 | 9/9 |
| 方案偏差 `adopt_plan_deviations` | 0 | 0 | 0 |
| 模板来源 `opened_from` | `builtin` | `builtin` | `builtin` |
| 版式使用记录 `layout_used` | 10 | 13 | 9 |
| 产物条数 `artifacts` | 8 | 8 | 8 |

**换题材、换页预算、换输入完整度之后，上表没有一列发生退化。**

---

## 2. 逐案实测明细

| id | 难度层 | exit | status | `slide_count` | 讲稿覆盖 | `evidence_loc_frac` | 图表落位 | 契约门 | `null` 数 | 判定 |
|-|-|-|-|-|-|-|-|-|-|-|
| `example-catalyst-201` | L0 基线接口 | 0 | `success` | 10/10 | 10/10 = 1.0 | 13/13 = 1.0 | 2/2 = 1.0 | 8/8 | 0 | `in-range` |
| `case-b-gnn-potential-301` | L1 结构完整 | 0 | `partial` | **13**（区间 [12,13]） | 13/13 = 1.0 | 26/26 = 1.0 | 2/2 = 1.0 | 8/8 | 0 | **`boundary-hit`** |
| `case-c-uhi-remote-302` | L2 退化输入 | 0 | `partial` | 9/9 | 9/9 = 1.0 | 34/34 = 1.0 | 1/1 = 1.0 | 8/8 | 0 | `in-range` |

补充字段（同一次测量）：

| 项 | A | B | C |
|-|-|-|-|
| 页级证据页数 / 证据行数 | 10 页 / 13 行 | 13 页 / 26 行 | 9 页 / 34 行 |
| 含表页数 `tables_pages` | 2 | 2 | 1 |
| `uncertainty` 条数 | 1 | 2 | 3 |
| `change_records` | `[]` | `[]` | `[]` |
| `layout_fallback_used` / `template_errors` | `false` / 0 | `false` / 0 | `false` / 0 |
| `result_json_written` | `true` | `true` | `true` |
| 耗时（秒） | 1.47 | 1.55 | 1.48 |

> 读表注意两点：① **讲稿覆盖与证据定位覆盖三案都是满分**，退化不在这两处；
> ② B 的 `slide_count=13` 是**声明区间内的实测值**，清单为它附了根因说明
> （`boundary_note`），脚本因此判 `boundary-hit` 而不是 `RANGE-MISS`。
---

## 3. L2 的关键证据：主线确实是从材料里抽出来的

案例 C 的 `case.json` **没有** `research_question / methods / results / discussion /
limitations / conclusion / key_numbers` —— 清单里写明它「只给最小 12 键；
六个故事线字段全部缺席」。那么这一册的故事线从哪来？答案是 `material.md`。

**题集报告 JSON 里能直接读到的**：

```text
measured.material_supplemented_buckets =
  ["conclusion", "discussion", "limitations", "methods", "question", "results"]
```

即 **6 个桶全部出现在补位结果里**（这正是清单里 `material_supplemented_required: true`
要求的那一项）。

**以下三行是本轮 `content.json` 的实测内容，登记在 `references/CASE-SET.md` §2**
（题集报告 JSON 只记录「哪些桶被补位」，**不记录逐桶条数与材料行数**，
所以这三行按文档出处引用）：

```text
supplemented_from_material = {question: true, methods: true, results: true,
                              discussion: true, limitations: true, conclusion: true}
六个桶条数                  = question 6 / methods 8 / results 7 /
                              discussion 5 / limitations 5 / conclusion 3
材料行数                    = 52（extract 的 sources[].lines 口径）
```

> 关于「52」这个数：`extract.py` 的 `sources[].lines` 用 `文本中换行符个数 + 1` 计算，
> 所以一个 51 行（51 个换行结尾）的材料会报 **52**。这是口径差异，不是笔误。

⇒ 结论：**六个故事线桶全部由材料补位，且每条都带 `material.md:行` 定位。**
这是「退化输入」这条路径真实可用的直接证据，而不是设计声明。
它的意义在于：L2 走的补位分支 **L0 永远走不到**，所以这一节不是 §2 那张表的重复，
而是补上了「最小字段输入」这一条独立代码路径的证据。

---

## 4. 两处非 `ok` 检查的原文

先说清楚**出处**：题集报告 JSON 里的 `measured.contract_gates_failed` 三案**都是空列表**
（CP3 契约门 8/8 全过）；**审计层的 `warn` 不在题集报告 JSON 的字段里**。
因此下面两处原文按 `references/CASE-SET.md` **§4.2 / §4.3** 引用，
它们对应 `audit.py` 的 `content.claim_coverage` 检查（逐页抽取主张前 18 个字符，
在全册文本里做字面匹配，命中不到就 `warn`）。

### 4.1 案例 B —— 报 1 条

```text
content.claim_coverage | warn | 1 claims not literally found;
    truncated: ['p8:表1 汇总不同温度下的 Li⁺ 电导']
```

对应现象：第 8 页（`结果 5`，**只放表 1**）在幻灯片上只有标题、表题行与页脚，
计划里的主张条目没有出现在页面上；对照第 9 页（同时有图和表）主张正常写出。

### 4.2 案例 C —— 报 2 条

```text
content.claim_coverage | warn | 2 claims not literally found;
    truncated: ['p4:热岛强度在夜间为 2.1 K，低于白', 'p5:表1：热岛强度的归因分解结果。']
```

两处成因不同：

- `p4`：一页塞了 **6 条**主张（都不带媒体引用，被归到同一个收集页），
  页面上写到第 4 条末尾就断了，**第 5、6 条没有出现**；
- `p5`：与案例 B 同因 —— **只放表格**的结果页丢掉了自己的主张条目。

### 4.3 这两处 warn 的后果与口径

| 项 | 说明 |
|-|-|
| 对 `status` 的影响 | 两案都因此降为 `partial`（B 还同时被页预算顶破影响，见 §2） |
| 是否影响契约门 | **不影响**：CP3 的 G1–G8 三案全过（`contract_gates_failed` 均为空） |
| 是否已修复 | **未修复**，属如实登记：按本轮约束不改既有版式路径 |
| 消费方怎么办 | 给「只有表」的结果条目补一条图引用，或接受 `partial` + 这条 warn |

> 换句话说：**契约门是「形态合规」，审计 warn 是「内容有损」，两者必须分开看。**
> 只看契约门会漏掉内容侧退化，只看 `status` 又分不清是哪一种。
---

## 5. 继承自基线的实测（三案逐项复核）

基线在示例案例上的冒烟承诺，在本轮三案上**逐项重新测量**，全部成立。
下表每一行都取自本轮 `measured` 字段（不是把基线的数字搬过来）：

| 基线承诺 | A（L0） | B（L1） | C（L2） | 字段 |
|-|-|-|-|-|
| 页级主张带 `文件:行`（基线：13/13 = 100%） | **13/13 = 1.0** | **26/26 = 1.0** | **34/34 = 1.0** | `evidence_loc_frac` |
| CP3 契约门全过（基线：G1–G8 全过） | **8/8** | **8/8** | **8/8** | `contract_gates_pass` / `contract_gates_failed=[]` |
| 契约禁止 `null` 占位 | **0** | **0** | **0** | `null_top_keys` |
| 方案↔执行一致（基线：10/10、0 偏差） | **10/10，偏差 0** | **13/13，偏差 0** | **9/9，偏差 0** | `adopt_plan_applied` / `adopt_plan_deviations` |
| 逐页 speaker notes | **10/10 = 1.0** | **13/13 = 1.0** | **9/9 = 1.0** | `notes_frac` |
| 图表按计划落位 | **2/2 = 1.0** | **2/2 = 1.0** | **1/1 = 1.0** | `figures_placed_frac` |

**这六行才是「泛化」的硬证据**：题材从催化化学换到计算材料、再换到城市遥感，
页预算从 10 换到 12 再换到 9，输入完整度从「全字段」换到「最小 12 键」，
而**契约层、证据层、方案层一行都没有退化**。

退化只出现在两处，且两处都被审计抓到（不是没发现）：

| 退化 | 案例 | 后果 | 出处 |
|-|-|-|-|
| 页预算被顶破（声明 12、实测 13） | B | `status=partial`、判 `boundary-hit` | `references/CASE-SET.md` §4.1 |
| 主张条目未落到页面（warn 1 条 / 2 条） | B、C | `status=partial` | `references/CASE-SET.md` §4.2 / §4.3 |

---

## 6. 未覆盖项（照 `references/CASE-SET.md` **§4.4**，注明出处）

**别把这三案当成泛化的全部证据** —— 以下六项本轮**没有**覆盖：

1. **没有跨模板族**：三案的模板链全部落到运行时生成的内置回退模板
   （`opened_from=builtin`，三案皆然）。**多母版、多主题、商业模板族、SmartArt 全部没测。**
2. **没有真 PDF / 像素级导出一致性**：本机无 LibreOffice / PowerPoint，预览是 PIL 示意图，
   因此「导出件与 pptx 渲染一致」只测到「有/无有效预览」，**测不到像素级差异**。
3. **没有中文以外的语言**：三案 `language` 都是 `zh`，`en` 分支未跑。
4. **没有起始 deck 编辑场景**：三案都没给 `starting_deck`，所以
   `change_records[].action=edit_starting_deck` 与「旧页连关系一起移除」这条路径
   在本题集里**未被覆盖**。
5. **没有超长材料**：三案材料都在 51–52 行量级，**没有**测过上百行的长材料与
   由此带来的抽取/分页压力。
6. **没有多图并排**：每页最多 2 张图（案例 B 第 9 页），没有测过 3 张以上并排。

另有一条**报告口径**上的限制：题集报告 JSON 记录的是**契约与结构层**的测量
（页数、覆盖、契约门、`null`、方案偏差），**不携带审计层的逐项检查**，
所以 §4 那两处 warn 必须回到 `references/CASE-SET.md` §4.2/§4.3 引用。

---

## 7. 复跑方法

```bash
SKILL_DIR=<本包根目录>            # 平台装到 /skills/weekly-skill
RUN=<包外可写临时目录>

cp -r "$SKILL_DIR" "$RUN/pkg"
python "$RUN/pkg/scripts/run_case_set.py" --skill "$RUN/pkg" \
    --cases "$RUN/pkg/examples" --run "$RUN/caseset" \
    --json "$RUN/caseset.json" --markdown "$RUN/caseset.md"
# 期望输出行：3 个案例 / 0 个超出声明区间 / 1 个已声明边界命中 / 退出码 0
```

期望的机器可读复核点（都在 `$RUN/caseset.json` 里）：

- 顶层 `case_count = 3`、`out_of_range = 0`、`boundary_hits = 1`；
- 三案 `exit` 全 **0**、`problems` 全为 `[]`；
- `case-b-gnn-potential-301` 的 `verdict = "boundary-hit"`、`boundary_hit = true`、
  `measured.slide_count = 13` 且落在 `measured.slide_count_range = [12, 13]` 内；
- `case-c-uhi-remote-302` 的 `measured.material_supplemented_buckets` 有 **6** 个桶名；
- 三案 `contract_gates_failed = []`、`null_top_keys = 0`、`adopt_plan_deviations = 0`。

只复核 L2 那一案（不必跑满三案）：

```bash
python "$RUN/pkg/scripts/run_case_set.py" --list --cases "$RUN/pkg/examples"
python "$RUN/pkg/scripts/run_case_set.py" --skill "$RUN/pkg" \
    --cases "$RUN/pkg/examples" --run "$RUN/only-c" --only case-c-uhi-remote-302
```

> 复跑前请确认 `$RUN/pkg` 是**包外副本**：案例会先被复制到包外、再现场合成占位图，
> 这样包内不会留下 `.pyc` 或图片。
