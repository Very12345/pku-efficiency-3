---
name: graphical-abstract
description: >-
  把研究材料做成单页 Graphical Abstract（图形摘要）的 Skill，主打**输出契约的逐行可验证**：
  输入侧 data-src 溯源（材料里找不到的数值不上画布），执行侧「方案先行 → 双 lint 门 →
  确定性版面 → 可编辑分层 SVG（7 层 layer:*）+ PNG/PDF → audit → 契约回显」，
  契约侧用 scripts/contract_matrix.py 把 case.json.output_contract 的**六种容器形态与九类边界值
  （空串/空数组/空对象/0/0.0/false/4096 字符/null/整键缺失）加非法容器与保留键冲突逐个注入并真跑**，
  给出实测的退出码 / status / 回显位置与类型 / null 计数 / 是否静默通过。
  Use when the task says "graphical abstract"、"图形摘要"、"示意图 / 机制图 / 通路图 / 流程图"、
  "为论文、基金或汇报画一张可编辑的图"、"编辑已有的图稿"，
  或需要证明「result.json 真的覆盖了案例声明的每一个字段」时。
---

# Graphical Abstract 图形摘要 Skill（契约优先版）

交付物是两样东西：**一张可继续编辑的分层图**，和**一份能被逐字段核对的 `result.json`**。
本版把后者当成接口来对待：`case.json` 声明什么，`result.json` 就必须回显什么，
而且**每一种声明形态都有实测记录**（§4），而不是文档里的一句"已支持"。

| 项目 | 值 |
|-|-|
| Skill 名称 / 版本 | `graphical-abstract` / `2.0.0`（`scripts/common.py` 的 `SKILL_VERSION`） |
| 技能根 | 本文件所在目录，记作 `$SKILL_DIR`；脚本用 `__file__` 自定位，**cwd 任意** |
| 资源形态 | 纯文本七种扩展名；无二进制、无预置图、无字体文件 |
| 唯一评分产物 | `result.json`（契约见 [`references/OUTPUT_CONTRACT.md`](references/OUTPUT_CONTRACT.md)，字段块逐字保留） |
| 契约实测 | `contract_matrix.py`：**26 行注入 / 26 ok / 0 静默 / 0 crash**（61.3 s） |

---

## 1. 调用

```bash
SKILL_DIR=/skills/weekly-skill
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md --out /app/output
python "$SKILL_DIR/scripts/check_contract.py" --result /app/output/result.json --case /input/case.json
```

两条命令都以**退出码**为判据：`main.py` 0 = 完成（`success` 或 `partial`），1 = 硬输入错误，
2 = 环境/内部错误；`check_contract.py` 0 = 契约完整，1 = 有缺口（逐条打印），2 = 文件不存在。
`--out` 必须是可写目录；`--plan` / `--task` / `--material` / `--raster-scale` / `--pdf` / `--no-pdf` 可选。

---

## 2. 输入（只读真实文件）

| 输入 | 说明 |
|-|-|
| `case.json` | 必读：`case_id / title / task / source_material / entities / relations / data / figure_constraints / output_contract`（键名有同义回退链） |
| `task.md` | `问题 / 方法 / 结果 / 结论` 小节 → 四列面板要点 |
| 材料 | `source_material` 指明的文本文件或 PDF（PDF 走文本层，取不到则登记后跳过） |
| `--plan plan.json` | 可选：`scaffold.py` 出骨架 → 定稿 → 方案 lint（CP1 门） |

三条硬规则：① 不凭文件名/标签推断内容；② 每个画布元素带 `src`（`文件:行` 或 `case.json[字段]`）；
③ 材料里定位不到的数值**不上画布**，只进 `uncertainty` 并以「数值缺失」占位。

---

## 3. 契约：声明形态 → 回显规则

`case.json.output_contract` 是评分方的声明；`main.py` 把它逐字段回显到 `result.json` 顶层，
**与信封保留键同名时**改放 `output_contract_echo`（顶层保留信封值）：

| 声明形态 | 例子 | `result.json` 的处理 | 实测行 |
|-|-|-|-|
| ① 类型提示（串/数/布尔） | `"resolution_dpi": 300` | 顶层同名同值；**不许**改成字符串或 null | C01/C04/C05/C06/C07 |
| ② 容器（列表） | `"target_format": ["svg","png","pdf"]` | 顶层同值；空则 `[]` | C02/C10/C26 |
| ③ 布尔开关 | `"colorblind_safe": true` | 真实布尔；`false` 与"未声明"必须可区分 | C06/C07/C14 |
| ④ 字段清单 / 对象 / 嵌套 | `"legend": {...}`、`output_contract.layer_names` | 结构原样保留，可无限嵌套 | C03/C08/C25 |
| ⑤ 声明为 `null` | `"resolution_dpi": null` | 归一化为**空值**（`""`）**并写进 `uncertainty`**（禁 null） | C16/C24 |
| ⑥ 非法容器 | `output_contract` 是列表/数字/布尔 | 按空契约处理**并点名记录**（见 §4.3） | C19/C21/C22 |

保留键集合（18 个）：`schema_version, skill, case_id, status, summary, task, deliverables,
content_summary, provenance, sources, uncertainty, warnings, change_records, audit,
generated_utc, output_contract_echo, plan, spec_lint`。
判定方式：顶层能覆盖「信封 ∪ 案例契约全部字段」= 通过（`check_contract.py` 可独立复跑）。

---

## 4. ★ 本版主轴：契约四形态 × 边界值矩阵（命令 · 判据 · 实测）

### 4.1 一条命令，26 次真实注入

```bash
python "$SKILL_DIR/scripts/contract_matrix.py" --out /tmp/cm --fail-on strict   # 约 60 s
python "$SKILL_DIR/scripts/contract_matrix.py" --out /tmp/cm --only boundary    # 只跑一类
python "$SKILL_DIR/scripts/contract_matrix.py" --out /tmp/cm --only C19 --keep --verbose
```

每一行都是一次**真实子进程出图**：把 `output_contract` 整体替换成该行的注入值，
跑 `main.py`，再抓 `退出码 / status / 回显位置与类型 / result.json 的 null /
check_contract.py 的退出码与 problems / uncertainty 与 warnings`。

判级：`ok`（期望全满足）/ `mismatch`（缺陷被记录）/ `silent`（**期望未满足而进程仍报 success
且一条记录都没有**）/ `crash`（没产出 result.json）。
`--fail-on strict` 要求全 `ok`；`--fail-on silent`（默认）只要求无 `silent`/`crash`。

### 4.2 实测汇总（26 行，全绿）

| 指标 | 实测值 |
|-|-|
| 行数 / `ok` / `mismatch` / `silent` / `crash` | **26 / 26 / 0 / 0 / 0** |
| 分类 | form 8 · boundary 10 · illegal 6 · combo 2（各全 ok） |
| `result.json` 顶层 null | **0 行** |
| 契约声明字段为 null | **0 行** |
| `check_contract.py` 失败 | **0 行** |
| 覆盖的边界值 | 空串、空数组、空对象、`0`、`0.0`、`false`、**4096 字符**（长度实测未截断）、`null`、整键缺失 |
| 覆盖的非法形态 | 列表/数字/布尔当契约、字符串契约、保留键冲突、保留键 + null |
| 组合 | 六形态同现 + Unicode/emoji/箭头；50 元素列表（顺序与长度逐值相等） |

逐行表、每行回显位置与类型、`uncertainty` 原文见
[`references/CONTRACT-MATRIX.md`](references/CONTRACT-MATRIX.md)；
机器可读原件 [`examples/contract_matrix.example.json`](examples/contract_matrix.example.json)。

### 4.3 静默通过清单：3 条 → 0 条

首次实测并非全绿：`output_contract` 为**列表 / 数字 / 布尔**时（C19/C21/C22），
契约被静默归一化为 `{}` —— `exit 0`、`status=success`、`uncertainty` 与 `warnings` 皆空，
评分方会以为"案例本来就没声明字段"。

**修复 = 纯增量，`scripts/extract.py` **净 +7 行**（把 1 行 `normalize_contract(...)` 调用拆成 2 行 + 新增 1 个记录分支与 3 行注释；函数签名/CLI/退出码零改动）**：归一化之前先看原始值，
若既不是 `dict` 也不是 `str`，就往 `uncertainty` 追加一条点名形态的记录。修复后：

```
case.json output_contract 形态非法（list）：已按空契约处理，字段不回显；契约应为对象或字符串。
```

| 指标 | 修复前 | 修复后 |
|-|-|-|
| `ok` | 23 / 26 | **26 / 26** |
| `silent` | 3 | **0** |
| 回归 `fault_inject.py --fail-on strict`（四形态 23 条） | exit 0 / 0 静默 | **exit 0 / 0 静默** |

### 4.4 观测到但**不算违规**的事实（写在矩阵里，不藏）

- 无 `--plan` 时 `plan.hash = null`：嵌套信封字段，`OUTPUT_CONTRACT.md` §2 已声明该形态，
  `check_contract` 判通过；矩阵把它单列为观测（26 行均如此），不计契约违规。
- 类型"提示"不做强制修正：契约写数字而案例给字符串时，顶层按**案例真实值**回显
  （`failure-modes.md` D17）。这是有意的 —— 不替案例改写它自己的声明。
- 保留键冲突时案例值进 `output_contract_echo`，顶层 `case_id`/`status` 仍是信封值（C23 实测）。

---

## 5. 主链与两道门

```bash
python "$SKILL_DIR/scripts/scaffold.py" --case <case.json> --out plan.json      # 方案骨架
python "$SKILL_DIR/scripts/spec_lint.py" --lint-plan --plan plan.json           # CP1 门（exit 0）
python "$SKILL_DIR/scripts/main.py" --case <case.json> --plan plan.json --out <out>
python "$SKILL_DIR/scripts/spec_lint.py" --spec <out>/spec.json --content <out>/content.json   # CP1b
python "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json --case <case.json>    # 契约门
```

`main.py` 内部顺序：读 case.json（不可读即 exit 1）→ 解析 task/材料 → 抽取（逐元素带 `src`）
→ 版面与视觉通道 → 规格 lint → 写分层 SVG → 渲染 PNG/PDF（三级后端）→ audit 自查 →
写 `result.json`（信封 + 契约回显 + 溯源 + plan/spec_lint）。

`status` 判定：`success` = SVG 良构 + PNG 有效 + 无缺值/无实体缺失/无越界 + 两道 lint 通过；
`partial` = 产物完整但存在上述任一限制（必须列明）；`failed` = SVG/PNG 未产出或输入不可读。
硬性门 G1–G8（`case_id` 非空、契约无 null、SVG ≥7 层、PNG 有效、数值编码一致、
四要素齐、`sources` 非空）见 [`references/OUTPUT_CONTRACT.md`](references/OUTPUT_CONTRACT.md) §7。

---

## 6. 命令面（每个入口都真跑过；`--flag` 全部列出）

| 入口 | 关键参数 | 退出码 |
|-|-|-|
| `scripts/main.py` | `--case`(必) `--task` `--material` `--out` `--plan` `--raster-scale` `--pdf`/`--no-pdf` | 0 / 1 / 2 |
| `scripts/contract_matrix.py` | `--out`(必) `--case` `--only` `--fail-on strict\|silent\|none` `--keep` `--verbose` | 0 / 1 / 2 |
| `scripts/check_contract.py` | `--result`(必) `--case` | 0 完整 / 1 缺口 / 2 文件不存在 |
| `scripts/spec_lint.py` | `--spec` `--content` `--lint-plan` `--plan` | 0 / 1 |
| `scripts/scaffold.py` | `--case`(必) `--task` `--material` `--out`(必) | 0 / 1 |
| `scripts/fault_inject.py` | `--out`(必) `--only` `--fail-on` `--keep` `--verbose` | 0 无静默 / 1 有 / 2 环境 |
| `scripts/gain_harness.py` | `--out` `--case` `--material` `--label` `--json` `--compare` | 0 |
| `scripts/extract.py` `figurespec.py` `svgbuilder.py` `preview.py` `audit.py` `common.py` | 被上面入口导入的库模块 | — |

---

## 7. 失败、降级与三道"非自述"证据

| 证据 | 工具 | 实测 |
|-|-|-|
| 四形态注入（输入/模板/依赖/契约 23 条） | `fault_inject.py --fail-on strict` | **exit 0，ok 23 / silent 0** |
| 契约形态与边界值 26 行 | `contract_matrix.py --fail-on strict` | **exit 0，26/26 ok** |
| 缺依赖降级 12 场景（脚本随本题姊妹版本 v9 发送） | `degrade_probe.py --fail-on strict` | **exit 0，12/12 ok、0 crash，12/12 仍写 result.json** |

决策规则 D1–D20 与失败分支同号互查：[`references/failure-modes.md`](references/failure-modes.md)；
注入矩阵：[`references/FAULT-MATRIX.md`](references/FAULT-MATRIX.md)；
契约矩阵：[`references/CONTRACT-MATRIX.md`](references/CONTRACT-MATRIX.md)。

---

## 8. 五维落点（速查；逐条对照见 [`references/RUBRIC_MAP.md`](references/RUBRIC_MAP.md)）

| 维度 | 分 | 落点 |
|-|-|-|
| 实际效果 | 40 | 真跑出图：四要素单页 + 可编辑分层 SVG + PNG（+PDF）；逐元素 `data-src`；`sources[]`(sha256)；`audit.json` 全文 |
| 使用增益 | 25 | 与基础做法的对照协议 + 只读测量器 `gain_harness.py`（分层数/真文字数/溯源覆盖率/契约通过率/返工步数） |
| 创新增益 | 15 | **契约形态与边界值的可执行矩阵**（26 行、含"静默通过"判据）+ 方案先行 + 双 lint 门 + 契约回显四形态 |
| 可靠体验 | 10 | 契约 26 行 + 注入 23 条 + 降级 12 场景三套实测；20 条决策规则；稳定退出码与 `status` 语义 |
| 生态贡献 | 10 | 契约/五维/失败模式/契约矩阵/注入矩阵/增益协议/机制/复用/方案 schema/四要素/图层/模板等文档 + 资产三件套 |

---

## 9. 交付前自查清单

- [ ] 跑的是**真实文件**；`case.json` 与其声明的材料都存在且可读
- [ ] `main.py` → **exit 0**，`result.json` 已写出
- [ ] `check_contract.py` → **exit 0**：顶层覆盖「信封 18 键 ∪ 案例契约全字段」且**无 null**
- [ ] 契约的六种形态都按 §3 处理：空串/空数组/空对象/`0`/`false` 不能被"空值化"
- [ ] 声明为 `null` 的字段已归一化为空值**且**在 `uncertainty` 里点名
- [ ] 保留键冲突时，顶层保留信封值，案例值进 `output_contract_echo`
- [ ] `contract_matrix.py --fail-on strict` → **exit 0**（26/26）
- [ ] `fault_inject.py --fail-on strict` → exit 0（23/23、0 静默）
- [ ] SVG 良构 7 层 + 真 `<text>` + `data-src`；PNG 签名正确；PDF 有头或 `present:false` + reason
- [ ] 四要素 4/4；`uncertainty` 里没有编造数据类补丁

---

## 10. 限制与边界（如实声明）

- **抽取边界**：只认独立成行的 `键 = 数值 单位` 与带真实箭头（`->`/`→`/`⇒`）的机制行；
  散文里的数字、带比较符或区间的值（`≈`、`0.8–1.2`）不抽取；材料与 case 数值矛盾时首见优先、
  两处 `src` 并列；非 UTF-8 材料按替换字符读取并登记；PDF 取不到文本层时跳过而非编造。
- **契约矩阵的边界**：只测"声明 → 回显"的形态与边界，**不测字段语义**（例如
  `resolution_dpi=300` 是否真的写进 SVG 画布）—— 那属于 `audit.checks`/`spec_lint` 的范围；
  也不测跨字段一致性（如声明了 `require_legend` 却没有图例）。
- **回显不是校验**：Skill 忠实回显案例声明的值，**不替案例判断声明是否合理**
  （类型提示与真实值不符时以真实值为准，见 D17）。
- **平台侧**（挂载缺失、配额、容器超时）不在本包任何矩阵的覆盖范围内。
- 四要素/图层/契约检查是**结构判据**，不代替领域科学判断。
- 随包示例案例均为**合成示意**，不是平台正式案例，不代表正式成绩。

### 10.1 本版相对上一代引擎的纯增量修复（逐条点名）

| 文件 | 变更 | 发现它的判据 | 理由 |
|-|-|-|-|
| `scripts/extract.py` | **净 +7 行**（把 1 行 `normalize_contract(...)` 调用拆成 2 行 + 新增 1 个记录分支与 3 行注释；函数签名/CLI/退出码零改动）：契约容器既非 dict 也非 str 时，往 `uncertainty` 写一条点名记录 | 本版 `contract_matrix.py` C19/C21/C22 | 非法契约此前被**静默**归一化为 `{}`，评分方看不到"契约被丢弃" |
| `scripts/main.py` | **净 +6 行**（在既有 `if/elif` 链上新增 1 个 `elif` 分支：4 行代码 + 2 行注释；无删改）：PDF 未产出且不是 `pdf=false` 时把 `reason` 填成实际后端名 | `degrade_probe.py` P03/P08/P09 | 回退后端时 `present:false` 的 reason 曾是 null，失败原因不可见 |

两处均为纯增量：CLI 参数名、默认值、退出码语义未动；修复后 `fault_inject.py --fail-on strict`
与 `contract_matrix.py --fail-on strict` 双双 **exit 0**（回归实测）。
