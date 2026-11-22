# COMPARISON-RECORD-20261122.md — 本包实际跑过的对照记录

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
