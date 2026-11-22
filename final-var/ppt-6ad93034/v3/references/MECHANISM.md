# MECHANISM.md — 本包的五个机制、各自"缺了会怎样"与可证伪判据

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
