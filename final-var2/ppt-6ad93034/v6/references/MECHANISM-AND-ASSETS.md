# MECHANISM-AND-ASSETS.md — 五个机制 + 可复用资产清单（同一主题合并）

> 本文件由两份同主题文档合并而来（**内容一字未删**，只调整标题层级与相互引用）：
> ① 五个机制 M1–M5：每个机制写清「解决什么现实问题 → 由哪段代码实现 →
> 没有它会怎样（具体到产物形态）→ 可证伪判据」；
> ② 可复用资产清单：九项可直接被他人拿走的资产。
> 判据探针是 `references/mechanism_probe.py`；对照测量台是 `references/measure_gain.py`。

---

## 第一部分：五个机制（M1–M5）

> **这份文档解决什么问题**：题面「创新增益 15 分」要的是"**基础 Agent 或现有方案
> 不具备、或难以稳定实现**"的能力，并且要"证明创新点相对现有能力的边界和价值"。
> 本文不列功能清单，而是逐个说明**五个机制**：
> ① 它解决什么现实问题；② 它由代码里的哪一段实现；③ **没有它会怎样**（具体到
> 产物形态）；④ **可证伪判据**（一条能在产物里查的痕迹 + 一个探针 + 证伪条件）。
>
> 判据探针：`references/mechanism_probe.py`（随包分发，包外运行）。
> 它**不看本文档怎么写，只看产物里有没有痕迹**。

---

## 0. 为什么"机制"要比"功能"更能说明创新

功能清单（"支持页序规划、证据映射、图表绑定、版本回退…"）人人都能写；
**机制**要回答的是：**去掉这一段代码，产物会退化成什么样**。
退化成什么样是可观测的，所以机制主张可以被证伪——这就是本文件与
"功能介绍"的区别，也是复评者能独立核实的最低成本路径。

下表是五个机制的一览；后面逐条展开。

| # | 机制 | 一句话 | 缺失后的产物形态 | 探针判据 |
|-|-|-|-|-|
| **M1** | 页面单元化与角色确定性 | 页 = 一个叙事角色 + 一个主张集合，由确定性规则分配 | 材料段落 → 页（整段照录），页与页之间没有分工 | `M1_page_units` |
| **M2** | 主张—证据锚定 | 每条主张带材料定位，每个数字必须能在材料里找到 | 数字来源不可查；抄错也发现不了 | `M2_anchors` |
| **M3** | 图表四态绑定 | 只有拿到取数数据才画图，位图无数据只占位 | 出现"凭空生成的曲线"或死图 | `M3_figure_states` |
| **M4** | 版本与可复核链 | 每轮改动一条记录、多版本并存、全部产物 sha256 | "改一页改坏全稿"且无法回到上一版 | `M4_versioning` |
| **M5** | 契约四形态与自检验证 | 契约字段禁 null、四形态回显、独立脚本复核 | 下游按 `null` 崩；"自检通过"被当"内容正确" | `M5_contract` |

---

## M1 页面单元化与叙事角色确定性

**解决什么问题**：同一份研究材料，组会讲义、答辩、评审要的取舍完全不同；
"把段落铺进页面"会得到一个没有叙事角色的文本流。

**实现位置**：`scripts/slide_text.py::alloc_roles`（确定性角色分配：封面 → 主线 →
〔背景/讨论/局限按页数〕→ 问题 → 方法 → 结果×n → 结论与下一步）+
`scripts/evidence_check.py::plan_lint`（页面纪律，CP2 门）。

**没有它会怎样**：产物退化为一页一段的文本流 —— 页数由材料段落数决定而不是由
`spec.max_slides` 决定；没有"这页承担什么角色"的字段；结果页与讨论页无法区分；
`plan_lint` 无从校验，因为不存在"单元"这个概念。此时下游想问"结果在第几页"
只能靠读全文。

**可证伪判据**（探针 `M1_page_units`）：

| 项 | 内容 |
|-|-|
| 判据 | `deck.slides[]` 每页 `role` 非空；`deck.slide_count` = `slides` 数 |
| 复核命令 | `python references/mechanism_probe.py --out <一次运行的输出目录>` |
| 实测 | 示例案例 6/6 页有角色；8 页留出案例 8/8 页有角色（→ PASS） |
| **证伪条件** | 任一次运行里存在无 `role` 的页；或 `slide_count` 与 `slides` 数不一致；或把 `alloc_roles` 换成"按段落顺序铺页"后判据仍 PASS（说明角色是硬编码/伪造的，不是分配出来的） |

---

## M2 主张—证据锚定与数字逐一核验

**解决什么问题**：学术汇报里最致命的错误不是排版，而是**数字对不上**。
"页面上的 82.4% 到底来自哪张表"必须能被回答，且**不能靠回忆**。

**实现位置**：`scripts/evidence_check.py::check_claim_numbers`（对每条入页主张在
材料原文里逐一匹配数字 token）+ `build_evidence_footer`（每页脚注）+
`result_tool.build_result` 输出 `evidence.map` 与 `unverified_claims`，
并写双形态 `evidence_map.md` / `evidence_map.json`。

**没有它会怎样**：数字与材料之间**失去可查的连线**。出现两类后果：
① 抄错/取整无法被发现（没有任何机制会比较页面与原文）；
② 复核者要核一个数字，必须逐页读材料 —— 而"复核"本身就是题面的评分点之一。
注意：整段照录的做法**看起来**没有抄错，但它同时也没有"定位"：
读者不知道这个数字来自表还是正文的哪一段，也无法判断是否有数字被漏掉。

**可证伪判据**（探针 `M2_anchors`）：

| 项 | 内容 |
|-|-|
| 判据 | 每条含数字 token 的主张 `evidence` 非空；`unverified_claims` 非空时状态不得为 `success` |
| 复核命令 | 同上探针；或 `python scripts/evidence_check.py --claim "<页面上的主张>" --material <材料文件>` |
| 实测 | 示例案例 6/6 条数字主张带证据指针、未核验 0 条；留出案例 8/8 条带指针、未核验 0 条（→ PASS） |
| **证伪条件** | 任一次运行里出现"有数字但无 `evidence`"的主张；或 `unverified_claims` 非空却标 `success`；或把 `check_claim_numbers` 替换成恒真函数后探针仍 PASS（说明核验是摆设） |

---

## M3 图表四态绑定（含"位图无数据只占位"的防编造）

**解决什么问题**：论文图常常是位图（截图），**没有取数数据**。
此时任何"重绘"都只能是编造；而放一张占位图又不说明来源，读者会以为它是真数据。

**实现位置**：`scripts/deck_tool.py::bind_figures` 的四态：

| 态 | 触发条件 | 产物 |
|-|-|-|
| `chart_image` | 材料提供**数值型数据表** | matplotlib 原样重绘（数值零改动，标注重绘来源） |
| `table` | 无 matplotlib / 数据非数值 / `--no-chart` | PPTX **原生可编辑表格**（仍可逐格改） |
| `embedded` | 材料直接给图片文件 | 原样嵌入，不加工 |
| `placeholder` | 论文图是位图且无取数数据 | 灰框**诚实占位** + 说明"原图未提供取数数据" |

**没有它会怎样**：只剩"有图/没图"两态，于是位图无数据的页要么空着（信息丢失），
要么被"重绘"成看似专业的曲线（编造）—— 后者正是题面 §1 点名的失败之一
（*"图表位置放一张占位图或凭空生成的曲线"*）。四态的价值不在多两个枚举值，
而在**把"不许编造"做成一个可判定的状态**：`placeholder` 是与 `chart_image`
并列的**合法交付态**，而不是失败。

**可证伪判据**（探针 `M3_figure_states`）：

| 项 | 内容 |
|-|-|
| 判据 | `figure.kind` 落在五态词表内；`chart_image` 必须指向**真实存在的图片文件**，且该页 `figure.table_id` 指向的**表文件存在**（否则即为"无数据来源的图"） |
| 复核命令 | 同上探针（它会解析相对输出目录的图片路径并检查文件与表文件） |
| 实测 | 示例案例 6 页：1×`chart_image`（图片与 `results.csv` 表均在）、5×`none`；留出案例 8 页：1×`chart_image`（图片与 `results_holdout.csv` 表均在）、7×`none`（→ PASS） |
| **证伪条件** | 出现词表外的 `kind`；或 `chart_image` 的图片/表文件找不到；或删掉 `placeholder` 分支后"位图无数据"的案例会产出 `chart_image`（即编造曲线） |

**负例验证（本探针确实会 FAIL）**：把一次真实运行的
`deck.slides[4].figure.image` 改成一个不存在的文件名，探针立刻报
`page 5 标为 chart_image 但图片文件不存在`（见 §5 负例控制）。

---

## M4 版本与可复核链（局部编辑 + 回退 + sha256 清单）

**解决什么问题**：多轮修改之后"说不清哪一版是交付版"是学术场景的高频事故
（题面 §1 原文：*"多轮迭代之后无法回到上一版，也说不清哪一版是交付版"*）。

**实现位置**：`scripts/deck_tool.py::apply_edits`（7 类局部 op）+
`main.py --edit … --version v2` 写出 `work/deck_v2.pptx` 且**保留** `work/deck.pptx`
+ `result_tool.write_changelog`（每轮一条 `{version, op, page, target, reason}`）
+ `write_manifest`（全部产物 sha256）+ `sources[].sha256`（输入侧对拍）。

**没有它会怎样**：改一页只能整稿重跑 → 旧版被覆盖、改动无记录、输入侧无法对拍。
具体退化形态：`work/` 下只有一个 `deck.pptx`（没有 `deck_<v>.pptx`），
`changelog.jsonl` 缺失，`manifest.json` 缺失 —— 复核者无法回答"这一版和上一版差在哪"，
也无法确认"交付的字节就是跑出来的字节"。

**可证伪判据**（探针 `M4_versioning`）：

| 项 | 内容 |
|-|-|
| 判据 | ① 可编辑源存在且能被 python-pptx **重开**、页数与 `result` 记录一致；② 存在多版本时**主版本仍在**（可回退）；③ `changelog.jsonl` 与 `manifest.json` 存在 |
| 复核命令 | 同上探针；`--edit` 场景另跑 `python scripts/main.py --case <case> --out <out> --edit <edits.json> --version v2` |
| 实测 | 示例案例：`deck.pptx` 可重开、6 页一致；`--edit` 运行时 `deck_v2.pptx` 与 `deck.pptx` **并存**、`changelog.jsonl` 3 条 op（→ PASS） |
| **证伪条件** | 删除旧版本或删除 changelog 后仍被判定"可回退"；或 pptx 页数与 `result` 记录不一致；或 `manifest.json` 缺失而探针仍 PASS |

---

## M5 契约四形态与"三层不互相顶替"的验证

**解决什么问题**：交付物要被**别的程序**读（平台、评审脚本、下游报表）。
字段缺省给 `null` 会让下游在类型判断上出错；而"自检通过"经常被误当成"内容正确"。

**实现位置**：`scripts/result_tool.py::apply_output_contract`（按声明类型给
`""/[]/{}/false/0`，**禁 null**）+ `validate`（G1–G8 门）+
`references/failure-modes.md` 第 5/6 节的"状态一致性"表；`selftest.py` 独立复核产物。

**没有它会怎样**：① 契约字段为 `null` 或缺失 → 下游按字符串处理时报错/静默丢字段；
② 只有一层自检 → "产物在不在"被当成"内容对不对"，于是 `unverified_claims`
里堆着数字也照样标 `success`。本包把核验切成三层并显式声明**互不顶替**：
`selftest`（产物可复核性）/ `result_tool`（契约合规）/ `evidence_check`（内容核验）。

**可证伪判据**（探针 `M5_contract`）：

| 项 | 内容 |
|-|-|
| 判据 | `result.json` 顶层不存在 `null` 值字段；`output_contract` 声明的字段逐项回显（G2）；类型合规（G8） |
| 复核命令 | 同上探针；`python scripts/result_tool.py --result <out>/result.json --out-dir <out> --case <case.json> --envelope templates/result_envelope.json`（**`--case` 必须传**） |
| 实测 | 示例案例：`{"valid": true}`、G1–G8 全 true、顶层 null 字段 0；留出案例同样 `{"valid": true}`（状态 `partial`，说明"门通过"与"状态降级"是两回事） |
| **证伪条件** | 顶层出现 `null`；或漏传 `--case` 时被误判为"契约没回显"（这正是 D12 要拦的误判）；或把 G2/G8 关掉仍报 `valid: true` |

---

## 5. 判据实测与负例控制（证明探针不是"恒真"）

**真实运行上的判据结果**（探针包外运行）：

| 输出 | 状态 | M1 | M2 | M3 | M4 | M5 | 探针退出码 |
|-|-|-|-|-|-|-|-|
| 示例案例（6 页） | `success` | PASS | PASS | PASS | PASS | PASS | 0 |
| 留出案例（8 页） | `partial` | PASS | PASS | PASS | PASS | PASS | 0 |
| **负例控制**（人为破坏） | `success` | **FAIL** | PASS | **FAIL** | PASS | **FAIL** | 1 |

负例控制的构造方式（可复现）：把一次真实运行的输出复制一份，然后
① 清空第 1 页的 `role`；② 把第 5 页的 `figure.image` 指向不存在的文件；
③ 在顶层加一个值为 `null` 的字段。探针随即报出三条：

```
M1_page_units      FAIL ['page 1 缺少 role']
M3_figure_states   FAIL ["page 5 标为 chart_image 但图片文件不存在: 'work/does-not-exist.png'"]
M5_contract        FAIL ['顶层存在 null 字段: [...]']
```

⇒ **探针具备区分能力**：机制痕迹被破坏时它会 FAIL。
（M2/M4 未被破坏，因此仍 PASS —— 这也是它"只报真实缺陷"的证明。）

---

## 6. 复核者最短路径（三条命令）

```bash
# 0) 在包外复制一份技能包并跑一次（不要污染包目录）
SKILL_DIR=<复制的技能包路径>; OUT=<临时输出目录>
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out "$OUT"

# 1) 机制痕迹探针（M1–M5 一次全查）
python "$SKILL_DIR/references/mechanism_probe.py" --out "$OUT"      # 期望 5/5 PASS

# 2) 契约门与自检（独立于探针的两条链）
python "$SKILL_DIR/scripts/result_tool.py" --result "$OUT/result.json" --out-dir "$OUT" \
    --case "$SKILL_DIR/examples/case.json" --envelope "$SKILL_DIR/templates/result_envelope.json"
python "$SKILL_DIR/scripts/selftest.py" --out "$OUT" --case "$SKILL_DIR/examples/case.json"
```

---

## 7. 机制边界（不主张什么）

1. **不主张"独家发明"**：页面角色、证据映射、四态图表、版本记录各自都不神秘；
   本包主张的是**把它们做成可判定的状态并留下可查痕迹**（探针能查、负例能让它 FAIL）。
2. **不主张"内容一定对"**：M2 只能保证"页面上的数字在材料里找得到"，
   不保证材料本身的科学结论正确。
3. **不主张"覆盖全部演示场景"**：SmartArt 等智慧型占位符不重排；
   动画/切换效果不在范围内。
4. **判据是必要条件而非充分条件**：探针 PASS 只说明"机制痕迹在"，
   不说明"这一版讲得好"。机制与内容质量是两件事，本文件只管前者。

---

## 第二部分：可复用资产清单

> **这份文档解决什么问题**：题面「生态贡献 10 分」考的是"作品本体、模板、页面骨架、
> 图表重绘脚本、题集与页级金标准能否被他人**直接复用**"，以及是否有"分享推广价值"。
> 本文把本包里**可以脱离本 Skill 单独拿走的东西**列成清单：每一项给
> **是什么 / 拿走它 / 怎么用 / 依赖 / 适用范围与不适用**。
>
> 一个前提取自题面：**本包不含任何正式案例的答案**；下面所有"题集/金标准"都是
> **虚构示例 + 一次真实运行的文本副本**，用途是接口冒烟与契约对拍，不是评分答案。

---

## 1. 资产总览（按"拿走之后能干什么"排序）

| # | 资产 | 位置 | 依赖 | 拿走它能干什么 |
|-|-|-|-|-|
| A1 | **结果信封 + 契约文档** | `templates/result_envelope.json`、`references/OUTPUT_CONTRACT.md` | 无（纯 JSON + 文档） | 给**任何**产出 `result.json` 的工具当校验依据（G8 就是读它） |
| A2 | **机制判据探针** | `references/mechanism_probe.py` | 标准库（M4 的 pptx 重开需 python-pptx） | 对任意一次运行的产物做 M1–M5 痕迹检查，**不依赖本包其余代码** |
| A3 | **增益测量台** | `references/measure_gain.py`（同目录另有对照协议文档） | python-pptx（仅条件 B 建基线稿用） | 对**任何"材料 → 结构化工件"的 Skill** 做同一口径的对照测量 |
| A4 | **页面骨架与角色词表** | `scripts/slide_text.py`（`ROLE_LABELS`、`AUDIENCE_TONES`、`alloc_roles`） | 标准库 | 把"论文结构 → 页面角色"的取舍规则搬到别的演示生成器 |
| A5 | **编辑操作目录** | `references/EDIT_OPS.md` + `scripts/deck_tool.py::apply_edits` | python-pptx | 给"局部改稿 + 版本归档"提供一套现成的 op 词表与决策树 |
| A6 | **模板参数文件** | `templates/default.json` | 无 | 换配色/字体/页脚**不改代码**；可作为别家模板的 schema 参考 |
| A7 | **数字核验器** | `scripts/evidence_check.py::check_claim_numbers` | 标准库 | 任何"页面/报告 vs 原文"的数字一致性检查（CLI 可直接用） |
| A8 | **示例即冒烟题集** | `examples/`（case/task/material/csv/edit_demo + `EXPECTED-OUTPUT.md`） | 无 | 新实现的接口冒烟与产物清单对拍 |
| A9 | **契约形态与状态一致性规则** | `references/failure-modes.md` §4/§5/§6 | 无 | 给别人写"降级要留痕"的规范时可直接引用（四形态表、状态自洽表） |

---

## 2. 逐项复用命令（复制即用）

### A1 结果信封 + 契约文档

```bash
# 把信封拷到你自己的验证器旁边
cp "<SKILL_DIR>/templates/result_envelope.json" ./schema/result_envelope.json
# 用它校验任何 result.json（本包的 result_tool 已内置这条逻辑，G8）
python "<SKILL_DIR>/scripts/result_tool.py" --result <你的>/result.json --out-dir <你的> \
    --case <你的>/case.json --envelope ./schema/result_envelope.json
```

**复用点**：`required_fields` 与字段类型声明是**数据**，不是代码；
你可以只拿走这个 JSON，用自己语言的验证器实现同一份检查。

### A2 机制判据探针（**最独立的一个资产**）

```bash
python "<SKILL_DIR>/references/mechanism_probe.py" --out <任意一次运行的输出目录>
# 期望：M1–M5 全 PASS，退出码 0；有 FAIL 时退出码 1
```

- 它只读 `result.json` + 产物文件；
- **可配合你自己的 Skill**：只要你的产物里有 `deck.slides[].role`、
  `claims[].evidence`、`figure.kind`、`deck_editable`、`changelog/manifest`，
  同一探针就能用；
- 它写出的报告文件名固定为 `mechanism-probe-report.json`（写在**当前工作目录**，
  所以在包外跑）。

### A3 增益测量台

```bash
cp "<SKILL_DIR>/references/measure_gain.py" <tmp>/     # 必须在包外跑，避免 __pycache__
python <tmp>/measure_gain.py --skill-dir "<你的技能包>" \
    --case <case1.json> --case <case2.json> --work <tmp>/work --out <tmp>/gain-report.json
```

- 条件 B 的基线生成器（`build_baseline_deck`）是**确定性**的，可被替换成
  你自己的基线实现（例如"只抽摘要"）；
- 五项质量指标（Q1/Q3/Q4/Q5/Q6）只依赖 `result.json` 与产物目录，
  **换成别的领域的结构化工件也能用**（把字段名映射改到 `metric_skill` 里即可）。

### A4 页面骨架与角色词表

```python
import sys; sys.path.insert(0, "<SKILL_DIR>/scripts")
from slide_text import ROLE_LABELS, AUDIENCE_TONES, alloc_roles   # 不触发任何 I/O
```

- `ROLE_LABELS` 是九种叙事角色（cover/overview/background/question/method/
  result/discussion/limitation/takeaway）与中文标签；
- `alloc_roles` 是**纯函数式**的确定性分配：输入材料视图 + spec，输出页级角色序列；
- **移植提示**：把"角色 → 页面模板"的映射换成你自己模板的版式名即可，
  规则本身（富余页先插背景/讨论/局限，再增加结果页）与领域无关。

### A5 编辑操作目录

```bash
# 操作词表（7 类）与决策树：直接当规范用
sed -n '1,80p' "<SKILL_DIR>/references/EDIT_OPS.md"
# 参考实现
python "<SKILL_DIR>/scripts/main.py" --case <case.json> --out <out> \
    --edit "<SKILL_DIR>/examples/edit_demo.json" --version v2
```

7 类 op：`update_bullet / add_bullet / remove_bullet / add_note / retitle /
reorder_pages / set_figure`；每次改动写一条
`{version, op, page, target, reason}`，旧版本以 `deck_<version>.pptx` 归档。

### A6 模板参数文件

```bash
cp "<SKILL_DIR>/templates/default.json" ./my-template.json   # 改颜色/字体/页脚即可
python "<SKILL_DIR>/scripts/main.py" --case <case> --out <out> --template ./my-template.json
```

**复用点**：颜色、字体族、页脚文案、槽位尺寸全部是数据；
"换模板不改代码"这条承诺由 `--template` 兑现（`merge_spec` 负责合并与覆盖）。

### A7 数字核验器（CLI 与函数两种用法）

```bash
python "<SKILL_DIR>/scripts/evidence_check.py" --claim "Q3 达到 82.4%" --material <材料文件>
# ok=True missing=[]  → exit 0；有缺失 → exit 1（可直接作为 CI 判据）
```

```python
import sys; sys.path.insert(0, "<SKILL_DIR>/scripts")
from evidence_check import check_claim_numbers, find_numeric_tokens
ok, missing = check_claim_numbers("Q3 达到 82.4%", open("material.md", encoding="utf-8").read())
```

### A8 示例即冒烟题集

```bash
# 只跑不回抄（验证接口，不改动包内文件）
python "<SKILL_DIR>/scripts/make_examples.py" --dry-run
# 真跑并重建 examples/output 的文本副本（会净化机器绝对路径）
python "<SKILL_DIR>/scripts/make_examples.py"
```

对拍清单在 `examples/EXPECTED-OUTPUT.md`（纯文字列出应产出的全部文件与契约字段）。
**注意**：示例是虚构材料，已标注"示例，非正式案例"，**不得冒充正式案例结果**。

### A9 契约形态与状态一致性规则

直接引用 `references/failure-modes.md` 的两张表：
§4「契约四形态」（`string→""`、`list→[]`、`dict→{}`、`bool→false`、`number→0`、禁 null）
与 §6「状态一致性」（`success`/`partial`/`failed` 各允许与禁止什么）。
这两张表**与实现解耦**，写给任何团队的"降级规范"都能用。

---

## 3. 移植到别的演示生成器（最小步骤）

1. **先立契约**：确定你的 `result.json` 顶层字段，写完 `OUTPUT_CONTRACT.md`，
   放一份 `templates/result_envelope.json`；
2. **带探针开发**：把 `references/mechanism_probe.py` 的 M1–M5 判据接到你的产物上
   （字段名不同就改探针里的取值路径，判据本身不用改）；
3. **接数字核验**：把你"页面文字 → 原文定位"的那一步换成 `check_claim_numbers`；
4. **补降级表**：照着 `failure-modes.md` 的编号方式写你自己的 D/F 规则，
   每条都指定记录字段（**没有记录 = 没执行降级**）；
5. **最后接测量台**：用 `measure_gain.py` 跑一遍，得到你自己的 Q1–Q6 基线
   —— **不要引用本包的 Δ 数字**，那是在本包案例上测的。

---

## 4. 复用边界（不适用的情况）

| 资产 | 不适用 / 需要改造 |
|-|-|
| A2 探针 | 产物里没有 `deck.slides[]` 这类结构化页级字段时需先做字段映射；M4 的 pptx 重开检查需要 python-pptx |
| A3 测量台 | 条件 B 的基线生成器是**演示场景专用**；换领域要重写 `build_baseline_deck`，否则基线不代表该领域的常见失败形态 |
| A4 角色词表 | 面向"研究材料 → 汇报"的场景；教学课件/商业提案的叙事角色不同，需替换词表 |
| A5 编辑 op | 只覆盖页面文本/备注/页序/图表引用；**不覆盖**动画、切换、SmartArt 重排 |
| A6 模板 JSON | 是"参数化模板"而非 OOXML 母版；需要真实母版时用 `spec.template_pptx`（本包只填槽位、不动母版） |
| A8 示例 | **虚构材料**，只能用于接口冒烟；任何对外材料中必须保留"示例，非正式案例"的标注 |

---

## 5. 版本与兼容

- 资产之间**没有隐式耦合**：A1/A2/A3/A9 只依赖 `result.json` 与产物目录；
  A4/A7 只依赖标准库；A5/A6 依赖 python-pptx 与 JSON。
- 探针与测量台都是**单文件脚本**，无第三方依赖（除上文写明的一处），
  可整文件拷走；如需改造，改文件内的判据/指标函数即可，不必动本包其他部分。
- 版本对齐：本包 `result.json` 的路径字段一律**相对输出目录**，
  因此探针/测量台在跨机复跑时不需要改路径逻辑（前缀不同不影响判据）。

---

## 6. 一句话总结

**本包可被拿走的不是"一个 PPT 生成器"，而是四件可独立使用的东西**：
一份**契约 + 信封**（A1/A9）、一个**判据探针**（A2）、一个**对照测量台**（A3）、
一套**页面骨架与编辑词表**（A4/A5/A6/A7/A8）。
它们共同的性质是：**判据可见、可在产物里查、可被别人的实现照做**。
