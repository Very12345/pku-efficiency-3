# CONTRACT-MATRIX.md — 契约四形态 × 边界值：逐行实测矩阵

> 判据不是"文档承诺了什么"，而是"注入之后进程到底做了什么"。本文件全部数字来自
> `scripts/contract_matrix.py` 在**包外临时副本**上的真实运行
> （Windows / Python 3.13.9，2026-11-23，26 行 × 每行一次真实子进程出图，合计 61.3 s）；
> 机器可读原件见 [`../examples/contract_matrix.example.json`](../examples/contract_matrix.example.json)。
> 契约的权威文本是 [`OUTPUT_CONTRACT.md`](OUTPUT_CONTRACT.md) §3（四形态）与 §7（G1–G8 硬性门）。

---

## 1. 为什么需要这张矩阵

`case.json.output_contract` 是**评分方与 Skill 之间的接口**：评分方声明它要哪些字段，
Skill 必须把它们出现在 `result.json` 里。文档里写的"四种形态全覆盖、禁止 null"是一句承诺，
而**承诺与实现是两件事** —— 一个形态可能在代码里被静默丢掉（不报错、不记录、状态还是 success），
评分方拿到 `result.json` 才发现少了一个字段，且没有任何线索说明为什么。

矩阵把每个形态/边界值**真的写进 case.json 再跑一遍**，于是"覆盖"从形容词变成一张逐行可查的表。

---

## 2. 判级口径（先说清，再贴表）

| 判定 | 含义 |
|-|-|
| `ok` | 预先写下的期望全部满足（退出码、status、回显位置/类型/值、无 null、`check_contract` 退出码、必要记录） |
| `mismatch` | 期望未满足，但**缺陷被记录**（`uncertainty`/`warnings` 有说明）或状态如实降级 —— 复核方能看见 |
| `silent` | 期望未满足，而进程仍报 `success` 且 `uncertainty` 与 `warnings` **都为空** = **静默通过** |
| `crash` | 没跑出 `result.json`（未捕获异常 / 退出码非预期） |

`silent` 的定义**故意严格**："记录了但状态没降级"只算 `mismatch`，不算静默。
两个 null 作用域也分开算：`result.json` **顶层键**与**契约声明字段**；
嵌套信封字段（无 `--plan` 时的 `plan.hash = null`）单列为观测
（`rows_with_nested_null_only = 26`），不计契约违规 —— 它是 `OUTPUT_CONTRACT.md` §2 声明过的形态。

---

## 3. 逐行实测（26 行）

命令：`python "$SKILL_DIR/scripts/contract_matrix.py" --out /tmp/cm --fail-on strict`
（基础案例 `examples/case.json`；每行把 `output_contract` 整体替换后重跑一次主链）

| # | 类 | 形态 | 注入 | 退出 | status | 回显位置/类型 | unc | `check_contract` | 判定 |
|-|-|-|-|-|-|-|-|-|-|-|
| C01 | form | string | `{"figure_note": "GA · 合成示例 · 2026"}` | 0 | success | top / str | 0 | exit 0 | ok |
| C02 | form | list | `{"target_format": ["svg","png","pdf"]}` | 0 | success | top / list | 0 | exit 0 | ok |
| C03 | form | object | `{"legend": {"position":"bottom","font_pt":9}}` | 0 | success | top / dict | 0 | exit 0 | ok |
| C04 | form | int | `{"resolution_dpi": 300}` | 0 | success | top / int | 0 | exit 0 | ok |
| C05 | form | float | `{"bar_width_pt": 1.5}` | 0 | success | top / float | 0 | exit 0 | ok |
| C06 | form | bool | `{"colorblind_safe": true}` | 0 | success | top / bool | 0 | exit 0 | ok |
| C07 | form | bool | `{"grayscale_print": false}` | 0 | success | top / bool | 0 | exit 0 | ok |
| C08 | form | nested | 三层：对象→列表→对象 | 0 | success | top / dict（结构逐值相等） | 0 | exit 0 | ok |
| C09 | boundary | string | `""` 空串 | 0 | success | top / str（`""`，未变 null） | 0 | exit 0 | ok |
| C10 | boundary | list | `[]` 空数组 | 0 | success | top / list | 0 | exit 0 | ok |
| C11 | boundary | int | `0` | 0 | success | top / int（真值 0 未被吞） | 0 | exit 0 | ok |
| C12 | boundary | float | `0.0` | 0 | success | top / float（与 int 0 可区分） | 0 | exit 0 | ok |
| C13 | boundary | object | `{}` 空对象 | 0 | success | top / dict | 0 | exit 0 | ok |
| C14 | boundary | bool | `false`（显式关闭） | 0 | success | top / bool | 0 | exit 0 | ok |
| C15 | boundary | string | **4096 字符**超长串 | 0 | success | top / str，长度 **4096**（未截断） | 0 | exit 0 | ok |
| C16 | boundary | null | `{"resolution_dpi": null}` | 0 | success | top / **str `""`** | **1** | exit 0 | ok |
| C17 | boundary | missing | 整个 `output_contract` 键删除 | 0 | success | ——（信封 18 键齐全） | 0 | exit 0 | ok |
| C18 | boundary | object | `{}`（声明了但没字段） | 0 | success | ——（顶层 18 键） | 0 | exit 0 | ok |
| C19 | illegal | list | `["svg","png"]` 当契约 | 0 | success | ——（按空契约处理） | **1** | exit 0 | ok（修复后） |
| C20 | illegal | string | `"svg+png"` 当契约 | 0 | success | top / str（`{"note": …}` 归一化） | 0 | exit 0 | ok |
| C21 | illegal | number | `300` 当契约 | 0 | success | —— | **1** | exit 0 | ok（修复后） |
| C22 | illegal | bool | `true` 当契约 | 0 | success | —— | **1** | exit 0 | ok（修复后） |
| C23 | illegal | object | 保留键冲突 `status` / `case_id` | 0 | success | **echo** / str（案例值）；顶层仍是信封值；非冲突键 `target_format` → top / list | 0 | exit 0 | ok |
| C24 | illegal | null | 保留键 + `null`（`summary` / `warnings`） | 0 | success | **echo** / str `""`；顶层信封值未被覆盖 | **1** | exit 0 | ok |
| C25 | combo | mixed | 六形态同现 + Unicode 键/emoji/箭头 | 0 | success | 7 个字段全部 top，类型逐一对上；顶层 **25 键** | 0 | exit 0 | ok |
| C26 | combo | list | 50 个对象的列表（顺序敏感） | 0 | success | top / list，长度 **50** 且逐值相等 | 0 | exit 0 | ok |

**汇总（实测）**：`rows 26 / ok 26 / mismatch 0 / silent 0 / crash 0`；
`nulls_top 0`、`nulls_contract 0`、`check_contract_failures 0`；
`by_class = {form 8, boundary 10, illegal 6, combo 2}`（全 ok）。

C16 / C19 / C21 / C22 / C24 的 `uncertainty` 原文（这就是"缺陷可见"的样子）：

```
案例 output_contract 声明为 null 的字段已归一化为空值：resolution_dpi
案例 output_contract 声明为 null 的字段已归一化为空值：summary, warnings
case.json output_contract 形态非法（list）：已按空契约处理，字段不回显；契约应为对象或字符串。
case.json output_contract 形态非法（int）：已按空契约处理，字段不回显；契约应为对象或字符串。
case.json output_contract 形态非法（bool）：已按空契约处理，字段不回显；契约应为对象或字符串。
```

---

## 4. 静默通过清单：从 3 条到 0 条

首次运行（修复前）的实测结果不是全绿：

| 行 | 注入 | 修复前实测 | 为什么算静默 |
|-|-|-|-|
| C19 | `output_contract = ["svg","png"]` | exit 0、`status=success`、`uncertainty=[]`、`warnings=[]` | 契约被 `normalize_contract()` 归一化为 `{}`，**一个字都没记**；评分方会以为"案例本来就没声明字段" |
| C21 | `output_contract = 300` | 同上 | 同上 |
| C22 | `output_contract = true` | 同上 | 同上 |

**修复（纯增量，`scripts/extract.py` **净 +7 行**（把 1 行 `normalize_contract(...)` 调用拆成 2 行 + 新增 1 个记录分支与 3 行注释；函数签名/CLI/退出码零改动））**：在归一化之前先取原始值，若既不是
`dict` 也不是 `str`，就往 `uncertainty` 追加一条点名形态的记录；CLI 参数、退出码、其余语义未动。

| 指标 | 修复前 | 修复后 |
|-|-|-|
| `ok` | 23 / 26 | **26 / 26** |
| `silent` | **3**（C19/C21/C22） | **0** |
| `crash` | 0 | 0 |
| `check_contract_failures` | 0 | 0 |
| 回归：`fault_inject.py --fail-on strict`（23 条四形态注入） | exit 0 / 0 静默 | **exit 0 / 0 静默**（未退化） |

> 静默通过清单现在是**空的** —— 这就是本轴的产出：不是"我们支持四形态"，
> 而是"26 行注入逐行有实测，静默条目为 0，且为此改的那几行被逐条点名"。

---

## 5. 观察到的、**不构成违规**但值得记一笔的事实

| 观察 | 说明 |
|-|-|
| 无 `--plan` 时 `plan.hash = null` | 嵌套信封字段，`OUTPUT_CONTRACT.md` §2 已声明 `source=none` 的形态，`check_contract` 判定通过；本矩阵单列为观测（26 行全部如此） |
| 类型"声明提示"不会被强制 | 例如契约写 `resolution_dpi` 是数字、而案例给字符串时，顶层按**案例真实值**回显（`failure-modes.md` D17：类型不符以真实值为准）。这是有意的：Skill 不替案例"修正"声明 |
| 保留键冲突时案例值进 `output_contract_echo` | C23 实测 `echo = {"status":"ready","case_id":"brand-x"}`，顶层 `status`/`case_id` 仍是信封值；`case_id` 不会被案例值冒名顶替 |
| C17/C18/C21/C22/C24 顶层 18 键、其余 19–25 键 | 键数差异完全由"案例声明了几个字段"决定，信封 18 键始终齐全 |

---

## 6. 未覆盖声明（这张矩阵**不**保证什么）

1. **字段语义正确性**：`resolution_dpi=300` 是否真的写进了 SVG 的 `width/height`、
   `target_format=["pdf"]` 是否真的产出了 PDF —— 属于"声明到实现的映射"，由
   `audit.checks` + `spec_lint` + [FAULT-MATRIX.md](FAULT-MATRIX.md) 覆盖，不在本矩阵。
2. **契约字段的相互约束**：例如"声明了 `require_legend: true` 却没有图例"这种跨字段一致性，
   本矩阵只测单字段/单容器的注入与回显。
3. **超大契约**：最大只测到 50 元素列表与 4096 字符字符串；没有测"契约本身几百 KB"
   （平台的文件上限是 500 KB/文件、2 MB/包，与本矩阵无关）。
4. **并发**：每行是串行子进程；两个进程同时写同一 `--out` 的行为未测。
5. **平台侧**：挂载缺失、配额、容器超时不在本矩阵范围。
6. **非 JSON 契约载体**：本 Skill 只读 `case.json`；如果平台把契约放进别的文件
   （如 `task.md` 里的表格），不在覆盖范围。

---

## 7. 怎么复跑

```bash
# 全量（约 60 s，26 次真实出图）
python "$SKILL_DIR/scripts/contract_matrix.py" --out /tmp/cm --fail-on strict

# 只看某一类 / 某一行
python "$SKILL_DIR/scripts/contract_matrix.py" --out /tmp/cm --only boundary
python "$SKILL_DIR/scripts/contract_matrix.py" --out /tmp/cm --only C19 --keep --verbose

# 只采数据（永远 exit 0），用于对照别的版本
python "$SKILL_DIR/scripts/contract_matrix.py" --out /tmp/cm --fail-on none
```

退出码：`0` = 达到 `--fail-on` 等级（`strict` 要求全 `ok`；`silent` 只要求无 `silent`/`crash`）；
`1` = 未达到；`2` = 用法/环境错误。`--out` 必须在包外；脚本先把 `scripts/` 复制到
`<out>/_skill/`，**包内不会被写入任何文件**（含 `__pycache__`）。
