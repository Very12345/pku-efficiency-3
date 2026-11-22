# GAIN-PROTOCOL.md — 公平对照协议 + 实跑记录 + 三层机制反例（合并版）

> 本文合并了三份同主题材料，**内容不删**：① 公平对照协议（原 GAIN-PROTOCOL.md）；② 本包实际跑过的对照记录（原 COMPARISON-RECORD-20261122.md）；③ 三层机制的反例摘要（原 COMPARISON-SUMMARY.md）。机器可读原始数据在 `references/comparison-data.json`。阅读顺序建议：先 §1–§3 定协议 → 再看附录 A 的真跑记录 → 附录 B 的机制归因。

> **这份文件回答的是题面里分值最高的一句追问**：
> *"评价是否通过公平对照证明质量或效率改善"*（使用增益 25 分中的"增益可验证性"5 分），
> 以及题面的硬性要求 *"质量与增益以平台固定案例、基础 Agent/Skill Agent 对照结果
> 和可核验记录为依据；文字自述不能替代实际运行证据"*。
>
> 在 v3 包里，这份协议还有一个额外用途：**给三层机制（M1/M2/M3）做归因**。
> 因为 C2 条件是"同一份代码、只把规则资产置空"，所以 C1−C2 的差**只能**归因于 M3；
> C0 与 C1 的差则同时包含 M1 与 M2 的贡献（两者在产物形态上可分：M1 看
> `evidence` 字段，M2 看 `layout.json` 与 PNG/PDF 是否真实）。
> 机制层的逐条对照见本文附录 B。
>
> 本文件只做三件事：**先把协议定死**（§1–§3）→ **给出每个指标的机器判定规则**（§3.3–§3.4）
> → **附上本包真跑过的记录**（§4，逐项数字与命令；原始数据在 `references/comparison-data.json`）。
> 协议里没有"大约""显著"这类词，凡是不能算的都不写。

## 1. 三个对照条件（怎么构造，为什么是这三个）

| 条件 | 构造方式 | 它代表什么 | 为什么必须放在协议里 |
|-|-|-|-|
| **C0 裸做法下界** | `scripts/bare_baseline.py`：读 `case.json` → 网格排版 → 写 `figure.svg` 与两个 **0 字节**占位 `figure.png`/`figure.pdf` | "不加载 Skill、也不额外努力"时的产物形态 | 没有它，"加载后更好"无从比较 |
| **C1 本 Skill** | `scripts/main.py` 完整流水线（证据抽取 → SIR → 布图 → 渲染 → 校验 → 契约） | 本包的交付路径 | 被检验的对象 |
| **C2 同代码关掉门禁** | `scripts/main.py --rules <空对象 json>`：**同一份代码**，只把规则资产置空 | 把"算法本身"与"门禁带来的增益"分开 | 只有 C2 存在，才能回答"增益是来自算法还是来自审计" |

**C2 为什么公平**：C2 与 C1 唯一的差别是一个 CLI 参数，两者产物内容
（`figure.svg`/`layout.json` 的 sha）完全相同——这一点在 §4 的记录里被实测确认。
因此 `Q3` 的差**只能**归因于规则审计，不能归因于别的。

**C0 的定位必须说清楚**：它是一个**可执行的下界**，不是"某个模型的真实行为录像"。
真实 agent 在无 Skill 时的表现可能更好也可能更差。C0 只回答一个问题：
*"当那些环节被拿掉、且不做任何额外努力时，产物会是什么样？"*
本协议**不对任何模型的真实分数作断言**，平台提供的白板才是相对比较的权威依据。

## 2. 必须固定住的四个条件（不固定就没有公平）

| # | 固定项 | 本协议怎么做 | 不固定的后果 |
|-|-|-|-|
| F1 | **同输入** | 三个条件读**同一份** `case.json`；记录其 `sha256` | 输入不同，指标差无法归因 |
| F2 | **同任务书** | 同一份 `task.md`；若某条件不支持读 task，视为该条件的固有劣势并在记录里标注 | 任务要求不同 = 不是同一道题 |
| F3 | **同运行环境** | 同机、同 Python、同依赖版本（Pillow/reportlab/字体） | 渲染差异会被误读成方法差异 |
| F4 | **同预算** | 每条件**只跑一轮、不重试**；耗时按单轮 wall-clock | 多次重试取最好成绩 = 选择性报告 |

> 本包实测环境：Windows 11 (10.0.22621) · Python 3.13.9 · Pillow 12.3.0 ·
> reportlab 5.0.0 · cairo svg/svgwrite 不可用（本包不需要）。
> 换环境重跑，**数值会变、结论方向不应变**；若方向变了，把两条记录都保留。

## 3. 预注册指标（先定义，再测量）

### 3.1 为什么要"预注册"

如果先看图再挑指标，任何包都能找出"我更好"的那一列。所以本协议要求：
**指标、算式、阈值在看结果之前就写死**，测量只做"填数"。
下面每个指标都给出**算式**（可照抄）、**判定规则**（机器可判）、**测量对象**（哪个字段）。

### 3.2 质量指标（6 项）

| 指标 | 算式 | 判定规则 | 测量对象 |
|-|-|-|-|
| **Q1 来源绑定率** | 有 `locator` 的 `evidence.items` 条数 ÷ (输出实体数 + 输出关系数) | = 1.00 为达标；< 1.00 说明有图面元素无法追溯 | `result.json.evidence.items[].locator` |
| **Q2 断头端点外露数** | 输出关系里 `from`/`to` 不在输出实体集合内的条数 | = 0 为达标；> 0 说明画了不存在的连接 | `result.json.relations` × `entities` |
| **Q3 违规暴露数** | `len(verify.errors) + len(verify.warnings)` | 与输入缺陷量比较（见 Q3b） | `result.json.verify.errors/warnings` |
| **Q3b 缺陷召回** | Q3 ÷ 预先注入的缺陷数 | 越高越好；**C0 恒为 0**（无审计） | 需人工构造带缺陷的输入 |
| **Q4 可编辑源文件** | `verify.checks.editable_text` 且 `verify.checks.entity_groups` | 两者皆 true 为达标 | `result.json.verify.checks` |
| **Q5 真实导出件** | `figure.png`/`figure.pdf` 字节数 > 0，且 PNG 可解析、尺寸 == 画布×DPI | 两者都 > 0 为达标；0 字节 = 占位，**不算真实导出** | 输出目录文件字节 |
| **Q6 状态诚实性** | `verify.ok=false` 时 `status` 是否为 `partial`/`failed`；`verify.ok=true` 时是否为 `success` | 一致为达标 | `result.json.status` × `verify.ok` |

### 3.3 效率指标（4 项）

| 指标 | 算式 | 怎么读 |
|-|-|-|
| **E1 单轮耗时** | 一次完整运行的 wall-clock（秒） | 只用于**同条件跨版本**比较，不要跨机器比较绝对值 |
| **E2 产物字节** | 输出目录递归总字节 | 反映"产出了多少真东西"；**更大不等于更好**，要配合 Q5 读 |
| **E3 人工干预步骤** | 到"可交付"还需人工做几步（列清单） | 这是**"少做多少事"**，不是"跑多快"——真正的效率增益在这里 |
| **E4 返工轮次** | 修改一处标注要重做多少（重画 = 1 轮） | 本包用 `--merge` 把常见返工压到 0 轮 |

> **本协议明确区分"运行效率"与"人工效率"**。前者本包的实测结论是**没有增益**（§4.3），
> 后者有增益。把两者混在一起说"效率提升"是不诚实的，本协议不这么做。

## 4. 本包实际跑过的对照记录（2026-11-22）

> 复现命令就写在每小节里；机器可读原始数据在 `references/comparison-data.json`。
> 两个合成案例：`clean`（8 实体 / 7 关系，材料自洽）与
> `defective`（12 实体 / 13 关系，**预注入 5 类缺陷**：断头关系、非法类别、
> 缺 `source`、重复 id、非法关系种类）。

### 4.1 命令（逐字可复跑）

```bash
SKILL_DIR=<本包目录>
CASE=<case.json>; TMP=<临时目录>

python "$SKILL_DIR/scripts/bare_baseline.py" --case "$CASE" --out "$TMP/c0"        # C0
python "$SKILL_DIR/scripts/main.py" --case "$CASE" --out "$TMP/c1"                 # C1
printf '{}' > "$TMP/empty-rules.json"
python "$SKILL_DIR/scripts/main.py" --case "$CASE" --rules "$TMP/empty-rules.json" --out "$TMP/c2"  # C2

python "$SKILL_DIR/scripts/gain_probe.py" --result "$TMP/c1/<case_id>/result.json" --baseline "$TMP/c0"
python "$SKILL_DIR/scripts/check.py" "$TMP/c1/<case_id>/result.json"
```

### 4.2 质量指标实测（两个案例 × 三个条件）

**案例 clean**（`case.json` sha256 前 16 位 `c7af792527dda9d6`）

| 指标 | C0 裸做法 | C1 本 Skill | C2 关掉门禁 | 读法 |
|-|-|-|-|-|
| Q1 来源绑定率 | **0.00**（无该字段） | **1.00** | 1.00 | 差值 1.00 来自证据层，与门禁无关 |
| Q2 断头端点外露 | **0** | **0** | 0 | 该案例无断头输入，三者无差 |
| Q3 违规暴露数 | **0**（无审计） | **0** | **0** | 干净输入上 C1 与 C2 **等价**——如实记录 |
| Q4 可编辑源文件 | `<text>` 0 个、无 `data-*` 组 | true / true | true / true | C0 的 SVG 只有 `<rect>`，没有文字 |
| Q5 真实导出件 | PNG **0 B**、PDF **0 B** | PNG **39 136 B**、PDF **4 028 B** | 同 C1 | C0 是占位文件，不是导出件 |
| Q6 状态诚实性 | **无 `status` 字段** | true（`success`） | true | C0 无从表达"我完成了没有" |
| 退出码 | 0 | 0 | 0 | — |
| 产物字节 E2 | 2 491 B | **78 509 B**（≈31.5×） | 78 371 B | 大是因为产出了真 PNG/PDF/JSON |
| 单轮耗时 E1 | 0.112 s | **0.5925 s** | 0.4847 s | C1 更慢——见 §4.3 |

**案例 defective**（`case.json` sha256 前 16 位 `5afbea68e9c8ee84`，预注入 5 类缺陷）

| 指标 | C0 裸做法 | C1 本 Skill | C2 关掉门禁 | 读法 |
|-|-|-|-|-|
| Q1 来源绑定率 | **0.00** | **1.00** | 1.00 | 同 clean |
| Q2 断头端点外露 | **1** | **0** | 0 | **C0 把不存在的端点也画了出来**；C1 丢弃该关系 |
| Q3 违规暴露数 | **0** | **3**（2 error + 1 warn） | **0** | **C1−C2 = 3**：这 3 条完全是门禁抓到的 |
| Q3 明细 | — | error：`no-self-loop`、`sequence-step-only`；warn：`recycle-review` | — | 与预注入缺陷对得上 |
| Q4 可编辑源文件 | `<text>` 0 个、无 `data-*` 组 | true / true | true / true | — |
| Q5 真实导出件 | PNG 0 B、PDF 0 B | PNG **47 080 B**、PDF **4 522 B** | 同 C1 | — |
| Q6 状态诚实性 | 无 `status` 字段 | true（`partial` + **退出码 3**） | true（`partial` + 退出码 3） | C1 拒绝把带缺陷的结果称作完成 |
| 契约门 | 未跑 | `check.py` **退出码 1**，`gates_false=['G9']` | 同 C1 | G9 报的失败是"审计未全绿" |
| `uncertainty` 域 | 无该字段 | `orphan_entities` / `sources` / `rule_violation` | 同 C1（`rule_violation` 来自 `verify.ok=false` 的统一记账） | — |
| 产物字节 E2 | 3 814 B | **105 444 B**（≈27.6×） | 103 283 B | — |
| 单轮耗时 E1 | 0.1002 s | **0.4970 s** | 0.4886 s | — |

**确定性**（两个案例各跑两轮 C1）：`figure.svg`、`layout.json`、`evidence.json`、
`verify_report.json` **全部逐字节一致**（4/4 × 2 案例）。
同时 C1 与 C2 的 `figure.svg`/`layout.json` **sha 完全相同**（defective：`46dcf42a...` /
`e661e8c3...`），只有 `verify_report.json` 不同（`6ab17444...` vs `1c04d7a5...`）——
这正是 C2 条件的构造意图：**算法输出不变，审计结果改变**。

### 4.3 效率结论：一条负面结果

| 指标 | C0 | C1 | 结论 |
|-|-|-|-|
| E1 单轮耗时 | 0.100–0.112 s | **0.497–0.593 s** | **C1 慢约 4.4–5.3 倍** |
| E2 产物字节 | 2.5–3.8 KB | 78–105 KB | C1 大 27.6–31.5 倍（因为产出了真的 PNG/PDF） |

**所以本包不声称"运行效率提升"。** 慢与大的原因很直接：C0 只做排版与写文件，
C1 还做了证据抽取、确定性布图、SVG 渲染、PIL/reportlab 导出、规则审计与契约自查。

真正的效率增益在 E3/E4 两列，它们是"**人工要补多少**"：

| 指标 | C0 | C1 | 依据 |
|-|-|-|-|
| E3 人工干预步骤 | ≥ 3 步：①补每个元素的出处 ②检查连接方向是否成立 ③真正渲染导出（C0 的 PNG/PDF 是 0 字节） | **0 步** | C0 的产物里没有 `evidence`/`verify` 字段，也没有可用的 PNG/PDF |
| E4 返工轮次 | 1 轮（改一处标注要重画） | **0 轮**（`--merge` 同名替换 + 新 id 追加，动 `change_record`） | 见 `examples/EXPECTED-OUTPUT.md §5` |

> **诚实的总结**：本包的增益是**质量与可靠性**（Q1/Q2/Q5/Q6 从"不满足"变"可机器验证地满足"，
> Q3 在缺陷输入上多抓 3 条），而不是**运行速度**。任何"效率提升 N 倍"的说法都与本包实测不符。

## 5. 第三方怎么用这份协议

1. **核本包**：按 §4.1 的三条命令跑一遍，用 `gain_probe.py` 复算 Q1–Q6，
   与 §4.2 的表对拍。数字对不上 → 先查环境（F3）与输入 sha（F1），再查结论。
2. **核别人的同类包**：`gain_probe.py` **不 import 本包任何模块**，
   只读 `result.json` 的公开字段；只要对方的 `result.json` 也有
   `entities`/`relations`/`evidence`/`verify`，就能算出同一套 Q1–Q6。
3. **搬到别的题**：把 Q1（来源绑定）/Q2（断头）/Q3（违规暴露）/Q5（真实导出）/
   Q6（状态诚实）换成那道题的对应概念，协议结构（条件 × 固定项 × 预注册指标 × 记录）不变。
4. **只报能算的**：协议里没有"提升明显"这种话；每个数字都能被 §4.1 的命令重算出来。
   如果某个指标在你的环境里算不出来，**写"未测"而不是写估计值**。

## 6. 协议自身的已知局限（诚实声明）

- **样本量小**：2 个合成案例 × 3 条件 × 1 轮。C0 是"可执行下界"而不是真实 agent 录像，
  所以本协议证明的是"这些环节的价值"，**不是**"本包一定比某个 agent 好 X 分"。
- **C0 的 SVG 含 `<text>` 计数为 0 是设计使然**：它只画 `<rect>` + 无文字标签，
  这不是"所有裸做法都会这样"，而是"下界实现长这样"。
- **E3/E4 是清单式指标**，不是秒表式指标；它们的裁决需要人读产物（清单在 §4.3 给出）。
  之所以仍然放进协议，是因为"少做几步"正是本题效率增益的实义。
- **Q3 依赖缺陷输入**：干净输入上 C1 与 C2 的 Q3 都是 0（§4.2），
  所以门禁的价值**只能**在带缺陷的输入上被量出来。这条限制让 Q3 必须配合 Q3b 一起读。
- 本协议不覆盖多案例统计显著性（无重复实验设计）；它覆盖的是"指标定义 + 单轮可比 + 可复算"。

---

## 附录 A · 本包实际跑过的对照记录（原 COMPARISON-RECORD-20261122.md）

> 协议是"打算怎么比"，本附录是"实际比了什么"：每条给出时间、命令、原始观测，以及"这条能不能被第三方重跑"。

> 这是 `references/GAIN-PROTOCOL.md` 的**执行记录**（协议是"打算怎么比"，本文件是"实际比了什么"）。
> 每条都给出：时间、命令、原始观测、以及"这条能不能被第三方重跑"。
> 机器可读版本：`references/comparison-data.json`。
>
> **记录原则**：只写跑出来的数字，不写估计值；跑不了的项写"未测"并说明原因；
> 出现与自己预期相反的结果（本文件有两条）照写。

## 0. 记录元信息

| 项 | 值 |
|-|-|
| 记录日期 | 2026-11-22（+08:00） |
| 被测包 | 本包（v2 增益可验证化版），`scripts/` 未做任何对照专用改造 |
| 运行环境 | Windows 11（10.0.22621）· Python 3.13.9 · Pillow 12.3.0 · reportlab 5.0.0 |
| 协议版本 | `GAIN-PROTOCOL.md` v1 |
| 对照条件 | C0（`bare_baseline.py`）/ C1（`main.py`）/ C2（`main.py --rules <空>`） |
| 案例 | `clean`（8 实体 / 7 关系，sha256 前 16 位 `c7af792527dda9d6`）与 `defective`（12 实体 / 13 关系，预注入 5 类缺陷，sha256 前 16 位 `5afbea68e9c8ee84`） |
| 轮次 | 每条件每案例 **1 轮**，不重试（协议 F4）；另跑一轮 C1 做确定性对拍 |
| 总耗时 | 约 20 秒（含 2 案例 × 3 条件 + 2 轮确定性对拍 + 2 次契约门） |

> 两个案例都是**合成**案例（标注：对照用合成案例，非正式案例），与平台固定案例无关。

## 1. 实际执行的命令序列

```bash
# 每个案例 c ∈ {clean, defective}
python "$SKILL/scripts/bare_baseline.py" --case <c>/case.json --out <c>/c0
python "$SKILL/scripts/main.py"          --case <c>/case.json --out <c>/c1
python "$SKILL/scripts/main.py"          --case <c>/case.json --out <c>/c2 --rules <c>/empty-rules.json
python "$SKILL/scripts/main.py"          --case <c>/case.json --out <c>/c1b   # 确定性对拍
python "$SKILL/scripts/check.py"         <c>/c1/<case_id>/result.json
python "$SKILL/scripts/check.py"         <c>/c2/<case_id>/result.json

# 指标复算（独立于包内模块）
python "$SKILL/scripts/gain_probe.py" --result <c>/c1/<case_id>/result.json --baseline <c>/c0
```

`empty-rules.json` 是**临时构造**的文件（内容为 `{}`，一个空对象，不随包发布）——这就是 C2 条件的全部构造。

## 2. 逐项观察（原始值）

### 2.1 案例 clean

| 观测量 | C0 | C1 | C2 |
|-|-|-|-|
| 退出码 | 0 | 0 | 0 |
| `status` | （无该字段） | `success` | `success` |
| 实体 / 关系（输出） | 8 / 7 | 8 / 7 | 8 / 7 |
| `evidence.items` 条数 | （无该字段） | 15 | 15 |
| Q1 来源绑定率 | 0.00 | **1.00** | 1.00 |
| Q2 断头端点外露 | 0 | 0 | 0 |
| Q3 违规暴露 | 0（无审计） | 0 | **0** |
| Q4 `editable_text` / `entity_groups` | `<text>` 元素 0 个 / 无 | true / true | true / true |
| Q5 `figure.png` / `figure.pdf` | 0 B / 0 B | **39 136 B / 4 028 B** | 39 136 B / 4 028 B |
| Q6 状态诚实性 | 无 `status` | true | true |
| 输出总字节 | 2 491 B | 78 509 B | 78 371 B |
| 单轮耗时 | 0.1120 s | 0.5925 s | 0.4847 s |
| `figure.svg` sha16 | 见 §2.3 | `04b3d6723f5929bb` | `04b3d6723f5929bb` |
| `layout.json` sha16 | — | `53217a37a044b2f9` | `53217a37a044b2f9` |
| `verify_report.json` sha16 | — | `bb49fe0e22fc201f` | `cd64bc5cb114802f` |

**这一组里最重要的一行是 Q3**：干净输入上 C1 与 C2 都是 0。
说明**门禁在无缺陷输入上不产生可测差异**——这是必须记下来的负面观察，
它意味着 Q3 只能在带缺陷的输入上体现价值（见 §2.2），协议也因此把 Q3b 单列。

### 2.2 案例 defective

| 观测量 | C0 | C1 | C2 |
|-|-|-|-|
| 退出码 | 0 | **3** | **3** |
| `status` | （无该字段） | **`partial`** | **`partial`** |
| 实体 / 关系（输出） | 12 / 13 | 12 / **12** | 12 / **12** |
| 被丢弃的关系 | 0（原样画） | **1** | 1 |
| Q1 来源绑定率 | 0.00 | **1.00** | 1.00 |
| Q2 断头端点外露 | **1** | **0** | 0 |
| Q3 违规暴露 | 0（无审计） | **3** | **0** |
| Q3 明细 | — | error `no-self-loop`、error `sequence-step-only`、warn `recycle-review` | — |
| Q4 `editable_text` / `entity_groups` | `<text>` 0 个 / 无 | true / true | true / true |
| Q5 `figure.png` / `figure.pdf` | 0 B / 0 B | **47 080 B / 4 522 B** | 47 080 B / 4 522 B |
| Q6 状态诚实性 | 无 `status` | true | true |
| `check.py` | 未跑 | 退出码 **1**，`gates_false=['G9']` | 退出码 1，`gates_false=['G9']` |
| `uncertainty` 域 | 无该字段 | `orphan_entities` / `sources` / `rule_violation` | 同 C1 |
| 输出总字节 | 3 814 B | 105 444 B | 103 283 B |
| 单轮耗时 | 0.1002 s | 0.4970 s | 0.4886 s |
| `figure.svg` sha16 | 见 §2.3 | `46dcf42a9749a89c` | `46dcf42a9749a89c` |
| `layout.json` sha16 | — | `e661e8c3b770ecae` | `e661e8c3b770ecae` |
| `verify_report.json` sha16 | — | `6ab174447ee34a4a` | `1c04d7a51ba92920` |

**三处可直接引用的结论**：

1. **Q2：C0 把一条端点不存在的关系也画了出来（1 条），C1 丢弃它并留痕（0 条外露 + 输入 13 → 输出 12）。**
   这就是"断头箭头不会被画出来"的可观测证据。
2. **Q3：C1−C2 = 3。** 因为 C1/C2 的 `figure.svg` 与 `layout.json` sha 完全相同，
   这 3 条违规**只能**来自规则审计，不能来自任何其它环节。
3. **Q6：C1 在带缺陷输入上给出 `partial` + 退出码 3，而不是"看起来成功"。**
   C0 连 `status` 字段都没有——它没有表达"我完成了没有"的能力。

### 2.3 C0 的原始观测（`bare_baseline.py` 的 stdout）

```jsonc
// clean
{"case_id":"cmp-apparatus-001","entities_drawn":8,"relations_drawn":7,
 "dangling_endpoints_kept":0,"source_binding":"none","gates_run":[],
 "status_field":null,"png_bytes":0,"pdf_bytes":0}

// defective
{"case_id":"cmp-defective-001","entities_drawn":12,"relations_drawn":13,
 "dangling_endpoints_kept":1,"source_binding":"none","gates_run":[],
 "status_field":null,"png_bytes":0,"pdf_bytes":0}
```

注意 `png_bytes: 0` / `pdf_bytes: 0`：C0 写出的是**0 字节占位文件**。
这不是"渲染失败"，而是"没有渲染这一步"——Q5 的判定规则正是为此设的：
**0 字节不算真实导出件**。

### 2.4 确定性与"条件纯净度"

两个案例各跑两轮 C1，四个文件的 sha 全部逐字节一致（4/4 × 2）：

| 文件 | clean | defective |
|-|-|-|
| `figure.svg` | 一致 | 一致 |
| `layout.json` | 一致 | 一致 |
| `evidence.json` | 一致 | 一致 |
| `verify_report.json` | 一致 | 一致 |

> 说明：这一轮的 `evidence.json` 与 `figure.svg` 同目录同输入，所以能一致。
> 若把包复制到**另一个目录**再跑，`evidence.json` 的 sha 会变——
> 因为它的 `sources[].path` 记的是**运行时真实输入路径**（取证需要）。
> 对比"内容是否一致"时请比对 `figure.svg`/`layout.json`/`verify_report.json`，
> 或忽略 `evidence.json` 里的 `path` 字段。这一点在 SKILL.md §8 也点了名。

另外 §2.1/§2.2 已显示：**C1 与 C2 的 `figure.svg`、`layout.json` sha 全同**，
只有 `verify_report.json` 不同。这是 C2 条件成立的直接证据。

## 3. 未测项（如实列出，不填估计值）

| 未测项 | 为什么未测 | 本记录里写的是什么 |
|-|-|-|
| **真实 agent 在无 Skill 时的表现** | 本轮对照工具环境的并发子代理额度已满（上限 8），一粒"裸 agent 臂"起不来；且本包不含网络与外部模型调用，无法从包内发起 | 协议 §1 已声明 C0 是**可执行下界**，不是模型录像；本文件不对任何模型的分数作断言 |
| **多轮统计显著性** | 协议 F4 规定单轮不重试（避免选择性报告） | 记录里每个数字都是单轮值，并注明"只用于同条件跨版本比较" |
| **平台固定案例上的白板对照** | 白板由组织方提供，参赛者不提供也不可见 | 本包只提供**可复算的本地协议**；正式相对比较以平台白板为准 |
| **C0 在其它图类（route/flow/hybrid）上的表现** | 本轮只跑了 apparatus 图类的两个案例 | 未测；协议 §5 说明如何把同一张表搬到别的图类 |
| **缺 Pillow / reportlab / 中文字体时的对照** | 需要改造依赖环境 | 这三条走决策规则 D10/D13（`uncertainty[scope=png\|pdf\|fonts]`），不属增益协议的测量范围 |

## 4. 这份记录能支撑什么、不能支撑什么

**能支撑**（每一条都指向 §2 的某个具体数字）：

- 本包产出的 SVG **是**可编辑的（`<text>` 存在 + 实体组带 `data-*`；C0 的 SVG 里 `<text>` 为 0 个）；
- 本包产出的 PNG/PDF **是**真实导出件（39–47 KB / 4.0–4.5 KB；C0 为 0 B 占位）；
- 图面元素**全部**可追溯到材料（Q1 = 1.00；C0 无此能力）；
- 端点不存在的关系**不会**被画出来（Q2 = 0 vs C0 = 1）；
- 规则审计在带缺陷输入上**确实**抓到了 3 条违规（C1−C2 = 3），且这 3 条不可能来自其它环节
  （C1/C2 的 SVG 与 layout sha 相同）；
- 带缺陷时本包**拒绝**宣称完成（`partial` + 退出码 3；C0 无 `status` 字段）；
- 同输入同目录下四个证据文件**逐字节可复现**。

**不能支撑**（不要拿这份记录去论证）：

- ❌ "本包比某个模型高 X 分"——本记录没有跑过任何模型；
- ❌ "运行速度更快"——实测更慢（§2.1/§2.2：0.10 s → 0.50–0.59 s）；
- ❌ "在所有图类上都有同样的差"——只测了 apparatus 图类；
- ❌ "门禁在任何输入上都带来差异"——干净输入上 C1 与 C2 的 Q3 都是 0（§2.1）。

**这一节是本文件存在的主要理由**：把"能证明的"和"不能证明的"分开写，
比给出一堆好看但无法复算的数字更有用。

---

## 附录 B · 三层机制的反例摘要（原 `COMPARISON-SUMMARY.md`）

> `references/MECHANISM.md` 里每一句"没有它会怎样"都对应本附录的一张表。

> `references/MECHANISM.md` 里每一句"没有它会怎样"都对应本文件的一张表。
> 对照的一侧是 `scripts/bare_baseline.py`（**把 M1/M2/M3 三层全部拿掉**：
> 不抽取证据、改用固定网格排版、不做任何规则审计），另一侧是本包完整流水线。
> 两侧读**同一份** `case.json`、同一台机、同一个 Python、各跑一轮。
>
> 完整逐项数据（含 sha16、耗时、字节数）见随包的 `references/comparison-data.json`。

## 0. 怎么复跑（三条命令）

```bash
SKILL_DIR=<本包目录>; CASE=<case.json>; TMP=<临时目录>

python "$SKILL_DIR/scripts/bare_baseline.py" --case "$CASE" --out "$TMP/c0"    # 无三层机制
python "$SKILL_DIR/scripts/main.py"          --case "$CASE" --out "$TMP/c1"    # 有全部机制
python "$SKILL_DIR/scripts/check.py" "$TMP/c1/<case_id>/result.json"           # 契约门 G1–G10
```

两个合成案例：
- `clean`：8 实体 / 7 关系，材料自洽（`case.json` sha256 前 16 位 `c7af792527dda9d6`）；
- `defective`：12 实体 / 13 关系，**预注入 5 类缺陷**（断头关系、非法类别、缺 `source`、
  重复 id、非法关系种类；sha256 前 16 位 `5afbea68e9c8ee84`）。

## 1. M1（证据中间层）的对照

| 观测量 | 无 M1 | 有 M1 | 缺陷案例（同上） |
|-|-|-|-|
| 有 `locator` 的元素 / 元素总数 | **0.00** | **1.00** | **1.00**（24 条证据 / 12 实体 + 12 关系） |
| 材料版本可查 | 无 | `evidence.source_files[].sha256` | 同左 |
| 元素↔材料双向回溯 | 无 | `element_traceability[]` + `evidence.items[].ref` | 同左 |

> 读法：M1 的差是**从"没有这个字段"到"每个元素都有出处"**，不是精度差异。

## 2. M2（确定性布局 + 规格探针）的对照

| 观测量 | 无 M2 | 有 M2 |
|-|-|-|
| 排版 | 固定 4 列网格 | 按图类选模板（route 分列 / apparatus 三桶 / flow 链路） |
| 同输入两轮 | 网格稳定（简陋所以稳定） | `figure.svg`/`layout.json`/`evidence.json`/`verify_report.json` **4/4 逐字节一致**（两个案例各验一次） |
| "是不是同一张图"的判据 | 只能肉眼 | `verify_report.json.determinism.spec_sha16` 一个指纹 |
| 三交付件同源 | 只有一个真 SVG | SVG/PNG/PDF 共享同一布局模型（PNG 39 136–47 080 B @200 DPI） |

> 注意：**"稳定"本身不是 M2 的卖点**（固定网格也稳定）。M2 的卖点是**稳定可证**
> ——上表第二行给了两侧；下界实现没有任何指纹可以让人对拍。

## 3. M3（规则资产机器审计）的对照

这一层的对照最关键，因为它需要排除"违规是别处顺带产生的"。
所以除了"无 M3"（下界实现），还跑了一个 **"同代码但审计关闭"** 条件：
`main.py --rules <空对象 json>`。

| 观测量 | 无 M3（下界实现） | 审计关闭（同代码 `--rules {}`） | 有 M3（正常） |
|-|-|-|-|
| 端点不存在的关系 | **照画**（外露 **1** 条） | 丢弃（外露 0） | 丢弃（外露 0） |
| 违规暴露条数 | **0** | **0** | **3**（error `no-self-loop`、error `sequence-step-only`、warn `recycle-review`） |
| `status` | 无该字段 | `partial` | `partial` |
| 退出码 | 0 | 3 | **3** |
| `figure.svg` sha16（缺陷案例） | `b5e603db8f30cdd8` | `46dcf42a9749a89c` | `46dcf42a9749a89c` |
| `layout.json` sha16（缺陷案例） | （无该文件） | `e661e8c3b770ecae` | `e661e8c3b770ecae` |
| `verify_report.json` sha16 | （无该文件） | `1c04d7a51ba92920` | `6ab174447ee34a4a` |

**这张表要点**：中间列与右列的 `figure.svg`/`layout.json` **sha 完全相同**，
唯一的差在 `verify_report.json` 与违规条数（0 → 3）。
⇒ 这 3 条违规**只能**来自规则审计这一层，不可能来自布图或渲染。

对照的另一个方向：**干净案例上两侧的违规都是 0**（无 M3 是 0，有 M3 也是 0）。
这说明 M3 不会凭空造出违规——它只在输入真的有结构性缺陷时说话。
这条负面观察同样收录在 `references/comparison-data.json` 里。

## 4. 三层一起看：产物形态的整体差

| 产物 | 无三层机制 | 有全部三层机制 |
|-|-|-|
| 可编辑源文件 | `figure.svg`（有 `<text>`？**0 个**，只有色块 `<rect>`） | 5 层 `layer:*`、真实 `<text>`、实体组带 `data-entity/data-source/...` |
| PNG 预览 | **0 字节占位** | 39 136–47 080 B（200 DPI，与画布 × DPI 一致） |
| PDF 预览 | **0 字节占位** | 4 028–4 522 B（reportlab 矢量，CID 字体 `STSong-Light`） |
| 证据链 | 无 | `evidence.json` + 回显进 `result.json.evidence` |
| 布局模型 | 无（几何只存在于一次性写出的 SVG 里） | `layout.json`（可复核、可重绘） |
| 校验报告 | 无 | `verify_report.json`（含 `spec_sha16`） |
| 状态与不确定性 | **无 `status` 字段**，无法表达"完成到哪一步" | `status`（`success`/`partial`）+ `uncertainty[].scope` + `change_record[]` |
| 输出总字节 | 2 491–3 814 B | 78 509–105 444 B |

> 字节数变大是**结果不是卖点**：多出来的是真 PNG/PDF 与四份结构化证据。
> 单轮耗时也同样变大（0.100–0.112 s → 0.497–0.593 s），本包**不**声称运行更快。

## 5. 这份摘要的边界

- 下界实现 `bare_baseline.py` 是**一个**反例实现，不代表所有既有方案；
- 只跑了 apparatus 图类的两个合成案例（route/flow/hybrid 未测）；
- 每条件一轮（避免"多跑几次取最好"的选择性报告），不做统计显著性结论；
- 这些数字**不构成**对平台正式评分的预测——正式案例与白板由平台提供；
- 想要机器可读的完整数据（含每次运行的 sha16 与耗时）请读
  `references/comparison-data.json`。
