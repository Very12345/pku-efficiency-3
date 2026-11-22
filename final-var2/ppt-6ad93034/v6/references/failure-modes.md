# failure-modes.md — 五族失败分支、降级去向、状态自洽规则与**实测对照**

> 本文件是 v6（union 包）的合并版：**v1 的全族展开（F1–F5）+ v2 的增益侵蚀表 +
> v3 的机制受损对照表 + v4 的 28 条注入实测 + v5 的跨题材失效边界**，同一主题一个文件。
> 阅读顺序：§0 判读约定 → §1–§8 设计口径 → §9–§12 实测与跨题材口径。

本文件是 [`SKILL.md`](../SKILL.md) §5 决策规则 **D1–D14** 与 §6 失败分支表
**F1–F5** 的**同一个体系的完整展开**：每一族都给出
**编号 → 识别信号 → 动作 → 失败时的降级去向 → 记录字段 → 用户可见后果**。

一条总原则（其余规则都是它的推论）：

> **宁可如实降级并留下可查的记录，也不要把"降级"包装成"成功"。**
> 判定"某条降级是否被正确执行"的唯一办法，就是去它声明的记录字段里找那条记录 ——
> **找不到记录 = 这条降级没有被执行**，无论调用方在报告里怎么写。

---

## 0. 退出码与判读约定

| 脚本 | 0 | 1 | 2 |
|-|-|-|-|
| `scripts/main.py` | `status=success`：产物齐备、G1–G8 通过、自检 `all_pass` | `status=partial`：有降级或未核验项，且**逐条**记入 `uncertainty` | 输入不可读（case 解析失败 / 材料读取失败），已写出最小 `status=failed` 的 result.json |
| `scripts/result_tool.py` | G1–G8 全过（`{"valid": true}`） | 有条目未过（`errors` 非空） | `result.json` 无法解析 |
| `scripts/selftest.py` | 全部自检项通过（`all_pass: true`） | 有未通过项（逐项列在 `checks[]`） | 输入不可读 |
| `scripts/evidence_check.py` | 主张里每个数字都能在材料中定位 | 有数字找不到（打印 `missing=[…]`） | — |

编排器判读：**只有 exit 0 才算这次运行"干净"**；exit 1 必须读
`result.json.uncertainty` 再决定是否补件重跑；exit 2 是输入侧问题，重跑无用。

---

## 1. F1 材料异常族（对应 D1 / D2 / D3 / D5）

| 编号 | 识别信号（可观测） | 动作 | 失败时的降级去向 | 记录字段 | 用户可见后果 |
|-|-|-|-|-|-|
| **F1.1** | `material_status=missing`：`inputs.material` 里一个文件都读不到 | 不构建 deck，只产出元信息 result（`deck.slide_count=0`） | case.json 也读不到 → 只写 `{"case_id","status":"failed","error","created_at"}` 并 exit 2 | `status`、`evidence.material_warnings` | 拿到一份说明"缺什么"的结果，而不是一份编造的稿子 |
| **F1.2** | `material_status=partial`：3 份只读到 2 份 | 用已读到的材料继续建稿；缺的那份显式标出 | 已读材料不足以支撑任一角色 → 降为 F1.3 | `evidence.material_warnings` | 页面不出现"只有缺失文件才有的数字" |
| **F1.3** | 材料可读但章节数为 0 且无数据表 | 产出最小可用稿 + 说明"材料无可用结构" | 无任何可用句 → 只出封面与说明页，状态 partial | `uncertainty` | 不会硬凑出无内容的页面 |
| **F1.4** | `check_claim_numbers` 返回 `missing` 非空 | 该主张 `verified=false` 入 `unverified_claims`，**原文照录不改写** | 整页主张都不可核 → 该页备注里明说"待核验"，不放行 | `evidence.unverified_claims` | 数字不会被"按印象取整"或静默改写 |
| **F1.5** | 扫描件 / 无文本层 PDF / 无任何抽取库 | 不 OCR 冒充：Agent 抽文本到 `<out>/work/materials/*.txt` 后重跑（D3） | 重跑仍读不出 → partial 并说明该材料未计入页级证据 | `uncertainty`、`sources[].tool` | 抽取方式被如实记录，事后可复核 |
| **F1.6** | 材料里的图是位图、无任何数值数据表 | 灰框**诚实占位**（`figure.kind=placeholder`）并标注"原图未提供取数数据"（D5） | 连位图文件也没有 → `figure.kind=none`，正文只保留图编号引用 | `deck.slides[].figure.note` | 永远不会出现"凭空生成的曲线" |
| **F1.7** | 数据表缺列 / 非数值列 | 图表绑定降级为 PPTX 原生可编辑表格（D9） | 表格文件也找不到 → `figure.kind=none` + 脚注保留引用 | `figure.note`、`uncertainty` | 图变成"可逐格改"的表格，而不是一张死图 |

> **三者语义不同，必须分开记录**：`material_warnings`（材料侧问题）、
> `uncertainty`（无法核验 / 已降级）、`status`（整体成败）。互相顶替即视为不自洽。

---

## 2. F2 模板缺失族（对应 D6 / D7）

| 编号 | 识别信号 | 动作 | 失败时的降级去向 | 记录字段 |
|-|-|-|-|-|
| **F2.1** | `spec.template_pptx` 打不开 / 损坏 | 备份原文件到 `<out>/work/original_inputs/`，改内置 `templates/default.json`，说明降级（D6） | 内置模板也读不到 → 用代码内 `DEFAULT_SPEC` 常量建稿，仍记降级 | `uncertainty`、`change_records` |
| **F2.2** | 母版版式 / 占位符不足，放不下 N 页 | 复用最接近的版式并新增文本框，**绝不改动母版** | 仍放不下 → **减少正文要点，而不是把字号缩到 <12pt** | `change_records` |
| **F2.3** | `spec.starting_deck` 起始稿需要适配 | 先备份到 `work/original_inputs/`，再按计划重排页面；每处改动记一条 | 起始稿损坏 → 按 F2.1 处理（视为无外部模板） | `change_records` |
| **F2.4** | `plan_lint` 报 `pages=N > max_slides`（D7） | 按 `max_slides` 确定性压缩角色分配（先并讨论/背景，再并结果页） | **不静默丢证据页**：被合并页的证据脚注并入保留页并在备注写明 | `run_meta.spec_lint`、`change_records` |
| **F2.5** | `spec.style` 缺键（要配色/页脚但没给值） | 取 `templates/default.json` 默认值；模板是数据不是代码，改 JSON 即可 | 默认值也不适用 → 记录偏差并以默认值交付 | `change_records` |

---

## 3. F3 依赖缺失族（对应 D8 / D9）

| 编号 | 缺失项 | 后果 | 动作与降级去向 | 记录字段 |
|-|-|-|-|-|
| **F3.1** | `python-pptx` | **致命**：无法建稿 | 走 partial/failed 分支，说清缺什么；**不用别的格式冒充 pptx** | `uncertainty`、`status` |
| **F3.2** | `matplotlib` | 图表无法重绘 | 结果页降级为 PPTX 原生可编辑表格（`figure.kind=table`） | `figure.note`、`uncertainty` |
| **F3.3** | `Pillow` | 预览 PNG 不产出 | G5 报错、自检 `previews` 不通过；状态降 partial | `previews.warnings` |
| **F3.4** | `reportlab` | 无 PDF 预览 | `previews.pdf=""`，PNG 不受影响（G5 仅 warning） | `previews.warnings` |
| **F3.5** | CJK 字体（预览绘制用） | 预览出方块，**PPTX 不受影响** | PPTX 只记字体名交由打开端替换；预览记 `cjk_font_available=false` | `previews.warnings` |
| **F3.6** | 字体探测候选全部落空 | 预览字体回落 | 回落 PIL 默认字体并预警；**不下载、不内嵌字体文件**（包内不允许二进制） | `uncertainty` |

> 依赖探测结果同时写入 `result.json.environment`（实测版本），
> 便于复核者区分"环境缺库"与"实现有缺陷"。

---

## 4. F4 契约四形态族（对应 D10 / D12）

`case.json` 的 `output_contract` 声明"必须镜像到 `result.json` 顶层"的字段。
**任何已声明字段都禁止 `null`**：

| 编号 | 声明类型 | 空值 | 有真实值时 |
|-|-|-|-|
| **F4.1** | `string` / `str` | `""` | 真实字符串 |
| **F4.2** | `list` / `array` | `[]` | 真实列表 |
| **F4.3** | `dict` / `object` | `{}` | 真实对象 |
| **F4.4** | `bool` / `boolean` | `false`（**注意不是 `0`**） | `true` / `false` |
| **F4.5** | `int` / `float` / `number` | `0` | 真实数值 |
| **F4.6** | 未声明类型（裸值） | 按运行时值的类型给同型空值 | — |
| **F4.7** | 复核者说"字段没回显" | **先查是否传了 `--case`**（D12），再查该字段是否真的在 `output_contract` 里 | 参数齐全且已声明仍不回显 → 报缺陷并附顶层键清单，**不手改 JSON 掩盖** |

实现：`scripts/result_tool.py::apply_output_contract`；
校验：G2（齐全 + 非 null）与 G8（`templates/result_envelope.json` 类型合规）。

---

## 5. F5 状态不一致族（对应 F5 内部规则）

| 编号 | 不一致形态 | 判定 | 处置 |
|-|-|-|-|
| **F5.1** | 有降级却标 `success` | `uncertainty` 非空但 `status=success` | 逐条把降级原因写清后降为 `partial` |
| **F5.2** | 有未核验主张却标 `success` | `unverified_claims` 非空但 `status=success` | 同上降为 `partial` |
| **F5.3** | 没有任何 deck 却标 `success` | `deck.slide_count=0` 且 `status=success` | 必为缺陷：降 `failed` 并说明 |
| **F5.4** | `partial` 但 `uncertainty` 为空 | 有降级无记录 | 不自洽：补齐每条降级原因的对应条目（一一对应，缺一即不自洽） |
| **F5.5** | 预览被当作 Office 导出件 | 文件名/`previews.method` 未标注"预览" | 立即更正措辞；预览不得冒充导出件 |

### 状态自洽速查表

| 状态 | 允许 | 禁止 |
|-|-|-|
| `success` | `uncertainty` 可为空；`checks.all_pass=true`；G 门通过；`unverified_claims` 为空 | 有未核验主张却标 success；有降级却没写原因 |
| `partial` | 核心产物（PPTX）可用但至少一项降级（图表降级 / PDF 缺失 / CP2 lint 偏差 / 编辑未应用 / 有未核验主张） | 每条降级原因**必须**在 `uncertainty` 里有对应条目 |
| `failed` | 只写最小 result.json 说明原因 | 不产出任何 deck 却标 success；把预览冒充 Office 导出件 |

> **三层核验不许互相顶替**：`selftest.py` 查"产物在不在、能不能开、页数对不对"；
> `result_tool.py` 查"契约合不合规"；**内容正确性**由 `evidence_check` 的数字核验与
> `plan_lint` 的页面纪律负责。三者都过，也不等于内容正确。

---

## 6. 编辑链路（`--edit`）分支（对应 D11）

| 编号 | 识别信号 | 动作 | 降级去向 | 记录字段 |
|-|-|-|-|-|
| **F6.1** | 未知 `op` | 跳过该条，其余 ops 照常应用 | 全部 op 都非法 → 不写新版本，只记 skipped | `uncertainty`、`changelog.jsonl` skipped |
| **F6.2** | 页码 / `bullet_index` 越界 | 同上，不改动目标页 | 越界涉及整页替换 → 整条拒绝 | 同上 |
| **F6.3** | `reorder_pages` 不是 `1..N` 的完整置换 | **整条拒绝**（避免"静默丢页"） | 拒绝后页序保持原样并记录 | 同上 |
| **F6.4** | 编辑引入的新数字材料里没有 | 该主张 `verified=false`；**不因"是用户让改的"就放行** | 编辑后的整页不可核 → 页级备注标注待核验 | `unverified_claims` |
| **F6.5** | 改坏要回退 | 复制上一版 `work/deck_<v>.pptx` 重跑，并补一条回退 change_record | 旧版本文件不存在 → 说明无法回退，不伪造"已回退" | `change_records` |

---

## 7. 资源形态族（本包特有，务必遵守）

| 失败形态 | 处置 |
|-|-|
| 包内混入二进制（`.pptx/.png/.pdf/.svg/.jsonl`） | 平台预检直接拒绝整包（`unsupported Skill resource`）。本包**不携带任何二进制**：模板由 `templates/*.json` 参数化，图表/预览运行时生成 |
| 文件数 >50 | 保持 20–40 文件的精简形态；新增能力**并入既有文档**而不是新增文件 |
| 包内出现本机绝对路径 | 示例产物由 `scripts/make_examples.py` 生成并自动净化；**唯一允许的命中**是字体探测候选路径（跨平台回路），且不得写入示例 JSON |
| 运行前忘了 `--case` 就判"契约没回显" | 见 F4.7：先确认参数齐全再下结论 |
| 在包内跑脚本 | 会生成 `scripts/__pycache__/` → 验收器直接 FAIL。**一切实测都在包外临时副本上做** |

---

## 8. 排查顺序（复跑失败时按此走，不要跳步）

1. `result.json.environment`：依赖是否缺失（F3）；
2. `evidence.material_warnings`：材料路径 / 缺失（F1）；
3. `run_meta.checkpoints`：哪一道裁决点没过（`cp1_extract` / `cp2_plan` / `cp3_build` / `cp4_verify`）；
4. `run_meta.spec_lint.problems`：页面纪律偏差原文（F2）；
5. `run_meta.gate.errors` 与 `uncertainty`：契约门与降级原因（F4 / F5）；
6. `logs/run_*.log` 末行 `STATUS=…` 与其上方的 `figure:` / `edit applied:` 行。

**判读提示**：如果第 3 步四门全 `true` 但仍然 `status=partial`，那一定是
`uncertainty` 里有条目（F5.4 的反面情形）—— 这是**设计如此**，不是缺陷。

---

## 9. ★ 增益侵蚀表（来自 v2：降级 → 哪项指标受损）

| 降级种类 | 触发 | 对五项质量指标的影响 | 结论是否仍成立 |
|-|-|-|-|
| 图表降级为原生表格（D9） | 无 matplotlib / 非数值列 / `--no-chart` | **Q1–Q5 不受影响**；`figure.kind` 由 `chart_image` 变 `table` | 成立（该降级不在五项指标内，属"图形态"而非"结构"） |
| PDF 预览跳过（D8） | 无 reportlab / `--draft` | **Q6 由 7/7 降到 6/7**（`previews.pdf=""`） | 成立但需注明 Q6 下降原因 |
| 预览 PNG 不产出（D8） | 无 Pillow | **Q6 降到 5/7**；G5 报错、自检不过 | 对照应作废（产物不齐，条件不等价） |
| 材料部分缺失（D1） | 案例给了多份材料只读到一部分 | 页面数可能减少；**Q3 可能被影响**（缺失材料的数字无法核） | 成立但必须把缺失写进 `material_warnings`，并在报告里标注 |
| 材料全缺（D1） | 一个文件都读不到 | **全部五项坍塌**（无 deck、无 role、无备注） | 对照**不成立**：此时不产出 deck 是正确行为，不能拿去比 |
| 数字核验不过（D2） | 主张里的数字材料中找不到 | **Q3 下降**（该主张进 `unverified_claims`）；状态降 partial | 成立；报告须同时给出 `unverified_claims` 条数 |
| CP2 lint 偏差（D4） | 单条主张超长/页数超限 | **不影响五项指标**（Q1/Q3/Q4/Q5/Q6 都不看长度），但状态降 partial | 成立；这正是 Q2 不能进结论的原因（见 GAIN 协议 §3.3） |
| 编辑未应用（D11） | op 非法 | 五项指标按**未编辑**的那一版衡量 | 成立，但对照必须在同一轮（都编辑或都不编辑）后比较 |
| 备注缺失（D5/G6） | 备注槽写入失败 | **Q4 下降** | 需修后重测：Q4 是核心指标之一 |

> **用法**：做完一次对照后，若某项 Δ 不如预期，先查本表定位是**哪类降级**造成的，
> 而不是去改指标口径。改口径属于 `GAIN-PROTOCOL.md` §2 明令禁止的行为。

---

---

## 10. ★ 降级 → 机制受损对照表（来自 v3）

| 降级 | 触发 | 受损机制 | 探针会说什么 | 处置要求 |
|-|-|-|-|-|
| 图表降级为原生表格 | 无 matplotlib / 非数值列 / `--no-chart` | **M3**（态从 `chart_image` 变 `table`，机制未破） | `M3` 仍 PASS（`table` 是词表内合法态） | 在 `figure.note` 写清降级原因 |
| 位图无数据 → 占位 | 材料图无取数数据 | **M3**（走 `placeholder` 分支） | `M3` 仍 PASS | `figure.note` 必须写明"原图未提供取数数据" |
| 预览 PDF 跳过 | 无 reportlab / `--draft` | 无（不属任何机制） | `M5`/`M4` 不受影响 | 记入 `previews.warnings` |
| 预览 PNG 缺失 | 无 Pillow | **M5** 的产物齐全度（G5 报错） | `M4`/`M5` 可能仍 PASS（探针查的是契约与版本链，不查预览齐备） | 状态降 partial 并写明；**不要**用别的图冒充预览 |
| 材料部分缺失 | 多份材料只读到一部分 | **M2**（缺失材料的数字无法核） | `M2` 仍 PASS，但 `unverified_claims` 可能非空 | `material_warnings` 列出缺失项 |
| 材料全缺 | 一个文件都读不到 | **M1/M2/M3 全部**（无 deck） | `M1` 会 FAIL（无 slides） | 这是 D1 的**正确行为**；探针 FAIL 在此处是"如实反映"而不是缺陷 |
| 数字核验不过 | 主张数字材料中找不到 | **M2** | `M2` 仍 PASS（指标只要求"有证据指针"且状态自洽） | 该主张进 `unverified_claims`；状态降 partial |
| CP2 lint 偏差 | 单条超长 / 页数超限 | 无（不影响 M1–M5 判据） | 探针不受影响 | 记 `run_meta.spec_lint`，状态降 partial |
| 编辑未应用 | op 非法 | **M4** 的版本链完整性（若连版本都没写） | `M4` 在缺 changelog/多版本时 FAIL | 记 `uncertainty` + `changelog` skipped |
| 模板打不开 | `Presentation()` 抛错 | 无（属外观约束） | 探针不受影响 | 记 `uncertainty` + `change_records` |

> **用法**：跑完一次后先跑探针，再按本表解释每一条 FAIL 或降级。
> **探针 FAIL 不等于产物一定不合格**（例如材料全缺时 M1 FAIL 是正确行为），
> 但**必须能在 `uncertainty` / `material_warnings` 里找到对应解释**。

---

---

## 9. 实测对照（2026-11-23 · 28 条注入）

本文件以上各节是**设计口径**；`references/FAULT-MATRIX.md` 是**逐行实测口径**。
两者不一致的地方已在矩阵里标 ⚠️，共 4 条：

| 本节的设计口径 | 实测结果 | 差在哪 |
|-|-|-|
| §1 材料异常：图/表解析不出时"降级并记录" | `F-IN-07`：`exit=0`/`success`，**无 note、无 uncertainty** | 设计只覆盖"重绘失败"，没覆盖"表解析不出"（静默丢图，S1） |
| §2 模板异常：`template_pptx` 打不开 → D6 记录 | `F-TPL-04`（损坏）✅ 留 `uncertainty`；**`F-TPL-05`（不存在）静默** | "打不开"与"不存在"走了两条不同分支（S3） |
| §2/§5：降级 → `partial` + uncertainty | `F-TPL-06`：降级只进 `change_records`，`status` 仍 `success` | change_records 与 uncertainty 未联动（F5.1 的实际样本） |
| §0 退出码：exit 1 = partial 且留 uncertainty | `F-TPL-03`/`F-DEP-03`/`F-DEP-04`/`F-DEP-05`：**exit 1 且无 result.json** | 崩溃发生在 `try/except` 之外（S4–S7） |

**结论**：本节的退出码语义与状态一致性规则在"能走到 `main.py` 保护范围里"的路径上
**全部成立**（实测 19/28 条 `product` 级留痕）；在保护范围之外的 7 条上不成立，
因此新增了 `scripts/fault_inject.py --guard` 这一层（见 §10），**并且把缺陷如实记录在此**。

---

## 10. 守卫（CP0 / CP5）：把静默失败变成可判读报告

```bash

---

## 9. 跨题材的失效边界（2026-11-23 · 两案例 + 四探针实测）

本文件前面各节是**通用失败模式**；本节记录的是"**换了题材/材料结构**以后才暴露"
的失败，全部来自 `scripts/case_check.py` 的实测（证据见 `references/CASE-SET.md` §3）。

| 编号 | 边界 | 实测现象 | 是否留痕 | 规避做法 |
|-|-|-|-|-|
| GAP-A1 | 材料缺"标准小节"（无"背景"） | `background` 页写占位主张 → `unverified_claims=1` → `status=partial` | ✅ 留痕（未核验清单） | 补一节背景，或接受 partial |
| GAP-A2 | markdown 表与 CSV 同时存在 | 数据源取 CSV，markdown 表（含 PCE 24.8%）**不进页面** | ❌ 不留痕 | 把要用的表导出成 CSV 并放 `material[]` 第一位 |
| GAP-B1 | 正文用"编号小标题"（`## 1. …`） | 产生只含 `1.` 的退化要点 | ❌ 不留痕（长度合规，`plan_lint` 不报） | 材料侧避免标题带序号；或 `--edit` 修掉 |
| GAP-B2 | 章节名不是标准论文骨架 | 年份等关键信息**整体不进页面** | ❌ 不留痕 | 交付前人工核对"最重要的 3 个信息是否都上页" |
| GAP-B3 | 同上 | 结果页取到摘要、方法页取到局限（内容错位） | ❌ 不留痕 | 人工看页面，不能只看 `status` |
| GAP-P1 | 材料给多张数值表 | 只绑定第一张，其余静默忽略 | ❌ 不留痕 | 只把要用的表放进 `material[]` |
| GAP-P3 | `max_slides` 过紧 | 角色被裁掉（`cover→overview→result`），`change_records` 只有 `start` | ❌ 不留痕 | 放宽上限；或人工在交付说明写明合并了哪些页 |

**判读提醒**：这 7 条里有 **6 条不留痕**——它们**不会**出现在 `uncertainty` /
`unverified_claims` / `change_records` 里，G1–G8 与 `selftest` 也抓不到。
因此"契约门全过 + 自检全过"**不能**推断"内容对齐"；
跨题材时必须再走一层：`case_check.py` 的案例级判据 + 人工看页面。

---

## 10. 状态规则在跨题材下的实际含义

| 状态 | 在跨题材场景下的含义 | 实测例子 |
|-|-|-|
| `success` | 材料齐全、无未核验主张、G 门与自检全过、`plan_lint` 通过 | 示例案例；探针 P3（压缩到 3 页且无缺口） |
| `partial` | **有据可查的降级**：缺小节写占位主张、`plan_lint` 偏差、预览降级 | 案例 A/B、探针 P1/P2/P4 |
| `failed` | 输入不可读，只写最小 result | 材料全缺（`TEST.md` §T7a 是 partial，`case.json` 不可读才是 failed） |

**关键口径**：跨题材时 `partial` **不是缺陷**，而是"材料本身有缺口"的诚实反映。
把它当成失败去追 `success`，只会诱导实现把缺口藏起来——那才是真正的失败。

---

# 附录 A：v2 的失败模式文档（增益视角）—— 原文逐字保留

> 为什么保留：v2 把每一族失败额外写成"**这条降级会侵蚀哪项增益指标**"，
> 是 §9 增益侵蚀表的展开版，与 §1–§8 的通用口径互补。
> 阅读顺序仍以正文 §0–§12 为准；本附录用于对照与溯源。

本文件回答两个问题：
① **出错时怎么办**（识别 → 处置 → 记录 → 退出码）；
② **出问题时"使用增益"还成不成立** —— 因为对照协议里的五项质量指标
（[`GAIN-PROTOCOL.md`](GAIN-PROTOCOL.md) §3）在降级路径上会被侵蚀，
必须能指出来是哪一类降级吃掉了哪一项指标。

总原则：**宁可如实降级并留下可查记录，也不把"降级"包装成"成功"。**

---

## 0. 退出码与判读

| 脚本 | 0 | 1 | 2 |
|-|-|-|-|
| `scripts/main.py` | `status=success`（产物齐备、G1–G8 过、自检 `all_pass`） | `status=partial`（有降级/未核验项，逐条记入 `uncertainty`） | 输入不可读，已写最小 `status=failed` result |
| `scripts/result_tool.py` | G1–G8 全过（`{"valid": true}`） | 有条目未过 | `result.json` 无法解析 |
| `scripts/selftest.py` | 全部自检项通过 | 有未通过项（列在 `checks[]`） | 输入不可读 |
| `scripts/evidence_check.py` | 主张里每个数字都能定位 | 有数字找不到（`missing=[…]`） | — |
| `references/measure_gain.py` | 测量完成（成败写在报告的 `gate` / `selftest` / 退出码字段里） | — | 输入不可读 |

**只有 exit 0 才算这次运行"干净"**；exit 1 必须读 `result.json.uncertainty`；
exit 2 是输入侧问题，重跑无用。

---

## 1. ★ 增益侵蚀表（本版特有：降级 → 哪项指标受损）

| 降级种类 | 触发 | 对五项质量指标的影响 | 结论是否仍成立 |
|-|-|-|-|
| 图表降级为原生表格（D9） | 无 matplotlib / 非数值列 / `--no-chart` | **Q1–Q5 不受影响**；`figure.kind` 由 `chart_image` 变 `table` | 成立（该降级不在五项指标内，属"图形态"而非"结构"） |
| PDF 预览跳过（D8） | 无 reportlab / `--draft` | **Q6 由 7/7 降到 6/7**（`previews.pdf=""`） | 成立但需注明 Q6 下降原因 |
| 预览 PNG 不产出（D8） | 无 Pillow | **Q6 降到 5/7**；G5 报错、自检不过 | 对照应作废（产物不齐，条件不等价） |
| 材料部分缺失（D1） | 案例给了多份材料只读到一部分 | 页面数可能减少；**Q3 可能被影响**（缺失材料的数字无法核） | 成立但必须把缺失写进 `material_warnings`，并在报告里标注 |
| 材料全缺（D1） | 一个文件都读不到 | **全部五项坍塌**（无 deck、无 role、无备注） | 对照**不成立**：此时不产出 deck 是正确行为，不能拿去比 |
| 数字核验不过（D2） | 主张里的数字材料中找不到 | **Q3 下降**（该主张进 `unverified_claims`）；状态降 partial | 成立；报告须同时给出 `unverified_claims` 条数 |
| CP2 lint 偏差（D4） | 单条主张超长/页数超限 | **不影响五项指标**（Q1/Q3/Q4/Q5/Q6 都不看长度），但状态降 partial | 成立；这正是 Q2 不能进结论的原因（见 GAIN 协议 §3.3） |
| 编辑未应用（D11） | op 非法 | 五项指标按**未编辑**的那一版衡量 | 成立，但对照必须在同一轮（都编辑或都不编辑）后比较 |
| 备注缺失（D5/G6） | 备注槽写入失败 | **Q4 下降** | 需修后重测：Q4 是核心指标之一 |

> **用法**：做完一次对照后，若某项 Δ 不如预期，先查本表定位是**哪类降级**造成的，
> 而不是去改指标口径。改口径属于 `GAIN-PROTOCOL.md` §2 明令禁止的行为。

---

## 2. 材料类异常

| 失败模式 | 识别信号 | 处置 | 记录 | 用户可见后果 |
|-|-|-|-|-|
| 材料文件不存在 / 为空 | `material_status=missing` | **不补造、不编 deck**：只产出元信息 result（`deck.slide_count=0`），状态 partial（D1） | `evidence.material_warnings` + `uncertainty` | 拿到"缺什么"的说明，而非编造的稿子 |
| 部分材料缺失 | `material_status=partial` | 用已读到的继续，缺的显式标出；页面上不得出现只有缺失文件才有的数字 | `evidence.material_warnings` | 数字来源边界清晰 |
| 扫描件 / 无文本层 PDF | 抽取为空或近空 | 不 OCR 冒充；Agent 抽文本到 `<out>/work/materials/*.txt` 后重跑（D3） | `uncertainty` + `sources[].tool` | 抽取方式可事后复核 |
| 无 PDF 抽取库 | 抽取阶段抛错 | 同上走 D3；**不静默把 PDF 当空文件** | `uncertainty` | 不会被"悄悄跳过" |
| 数字与页面主张不一致 | `check_claim_numbers` 返回 `missing` 非空 | 该主张 `verified=false`，**不回填、不取整、不按印象改**（D2） | `evidence.unverified_claims` | 页面不会出现材料外的数字 |
| 数据表缺列 / 非数值列 | 图表绑定阶段判定 | 降级 PPTX 原生可编辑表格（D9） | `figure.note` + `uncertainty` | 图变表格，仍可逐格改 |

> `material_warnings`（材料问题）、`uncertainty`（无法核验/降级）、`status`（整体成败）
> 三者语义不同，**必须分开记录**。

---

## 3. 模板类异常

| 失败模式 | 识别信号 | 处置 | 记录 |
|-|-|-|-|
| `template_pptx` 打不开 / 损坏 | `Presentation()` 抛错 | 备份原文件 → 回退内置 `templates/default.json`（D6） | `uncertainty` + `change_records` |
| 版式/占位符不足 | 母版版式枚举不足 | 复用最接近版式 + 新增文本框，**绝不改母版**；仍不够则减要点而非把字号压到 <12pt | `change_records` |
| `starting_deck` 需适配 | 起始稿存在 | 先备份到 `work/original_inputs/` 再重排；每处改动记一条 | `change_records` |
| 页数超限 | `plan_lint` 报超限（D7） | 确定性压缩角色；**不静默丢证据页**，合并说明写进备注 | `run_meta.spec_lint` + `change_records` |
| 无模板但要求特定配色/页脚 | `spec.style` 缺键 | 用模板默认值；模板是数据不是代码 | `change_records` |

---

## 4. 依赖缺失类异常

| 依赖 | 缺失时的行为 | 记录 |
|-|-|-|
| `python-pptx` | **致命**：无法建稿 → partial/failed，如实说明缺什么 | `uncertainty` + `status` |
| `matplotlib` | 结果页降级原生可编辑表格（`figure.kind=table`） | `figure.note` + `uncertainty` |
| `Pillow` | 预览 PNG 不产出 → G5 报错、自检 `previews` 不过 | `previews.warnings` + `uncertainty` |
| `reportlab` | 跳过 PDF（`previews.pdf=""`），PNG 不受影响（G5 仅 warning） | `previews.warnings` |
| CJK 字体（预览用） | 预览出方块但 **PPTX 不受影响**；PPTX 只记字体名 | `previews.warnings`（`render_qa` 的 `cjk_font_available`） |
| 字体探测全落空 | 回落 PIL 默认字体并预警；**不下载、不内嵌字体文件** | `uncertainty` |

依赖实测版本写入 `result.json.environment`，便于区分"环境缺库"与"实现有缺陷"。

---

## 5. 契约四形态（`output_contract` 回显）

**任何已声明字段都禁止 `null`**：

| 声明类型 | 空值 | 有真实值时 |
|-|-|-|
| `string` / `str` | `""` | 真实字符串 |
| `list` / `array` | `[]` | 真实列表 |
| `dict` / `object` | `{}` | 真实对象 |
| `bool` / `boolean` | `false` | `true` / `false` |
| `int` / `float` / `number` | `0` | 真实数值 |
| 未声明类型（裸值） | 按运行时值类型给同型空值 | — |

实现：`scripts/result_tool.py::apply_output_contract`；校验：G2（齐全 + 非 null）
与 G8（`templates/result_envelope.json` 类型合规）。

> ⚠ **`--case` 必须传给 `result_tool.py`**，否则无法做契约回显核对 ——
> 漏传会让"契约全回显"看起来失败。这是本 Skill 最容易误判的一处。

---

## 6. 状态一致性

| 状态 | 允许 | 禁止 |
|-|-|-|
| `success` | `uncertainty` 可为空；`checks.all_pass=true`；G 门通过；`unverified_claims` 为空 | 有未核验主张却标 success；有降级却没写原因 |
| `partial` | 核心产物（PPTX）可用但至少一项降级（图表降级/PDF 缺失/CP2 lint 偏差/编辑未应用/有未核验主张） | **每条降级原因都必须在 `uncertainty` 里有对应条目**（缺一即不自洽） |
| `failed` | 只写最小 result.json 说明原因 | 不产出任何 deck 却标 success；把预览冒充 Office 导出件 |

**三层核验不许互相顶替**：`selftest.py` 查"产物在不在、能不能开、页数对不对"；
`result_tool.py` 查"契约合不合规"；内容正确性由 `evidence_check` 的数字核验与
`plan_lint` 的页面纪律负责。三者都过，**也不等于内容正确**。

> 与对照协议的联接：若某次运行是 `partial`，则它**仍可用于对照**（前提是两侧
> 条件对齐、且 §1 侵蚀表能指出是哪类降级），但报告里必须同时给出
> `unverified_claims` / `previews` / `material_warnings` 的实际取值。

---

## 7. 编辑链路（`--edit`）异常

| 失败模式 | 识别信号 | 处置 | 记录 |
|-|-|-|-|
| 未知 `op` | `apply_edits` 不认识 | 跳过该条，其余照常（D11） | `uncertainty` + `changelog` skipped |
| 页码 / `bullet_index` 越界 | 越界 | 同上，不改动目标页 | 同上 |
| `reorder_pages` 不是完整置换 | 不是 `1..N` 的置换 | 拒绝该条（避免"静默丢页"） | 同上 |
| 编辑引入的新数字材料中没有 | 重跑核验未命中 | 该主张 `verified=false`，**不因"是用户让改的"就放行** | `unverified_claims` |
| 改坏要回退 | — | 复制上一版 `work/deck_<v>.pptx` 重跑，并补一条回退 change_record | `change_records` |

---

## 8. 资源形态与测量台的自我约束

| 失败模式 | 处置 |
|-|-|
| 包内混入二进制（`.pptx/.png/.pdf/.svg/.jsonl`） | 平台预检直接拒收整包。本包只携带 UTF-8 文本；模板参数化、图表/预览运行时生成 |
| 文件数 >50 | 保持 20–40 文件形态；新增能力并入既有文档而不是新增文件 |
| 包内出现本机绝对路径 | 示例由 `scripts/make_examples.py` 自动净化；**唯一允许的命中**是字体探测候选路径，且不得写入示例 JSON |
| **在包内运行任何脚本** | 生成 `scripts/__pycache__/` → 验收器直接 FAIL。**对照测量尤其注意**：先把 `references/measure_gain.py` 复制到包外，或整体复制技能包到临时目录 |
| 测量脚本报告里的路径 | 报告记录的是**运行时机器路径**（属产物不属包内容）；跨机复跑前缀自然不同，数字不受影响 |
| 为了让 Δ 好看而改口径 | **明令禁止**（`GAIN-PROTOCOL.md` §2）。口径变更必须走版本化修订并在协议里留修订记录 |

---

## 9. 排查顺序

1. 读 `result.json.environment`（实测库版本）→ 依赖是否缺失（§4）；
2. 读 `evidence.material_warnings`（材料路径/缺失，§2）；
3. 读 `run_meta.checkpoints`（哪一门没过：cp1_extract / cp2_plan / cp3_build / cp4_verify）；
4. 读 `run_meta.spec_lint.problems`（页面纪律偏差，§3）；
5. 读 `run_meta.gate.errors` 与 `uncertainty`（契约门与降级原因，§5/§6）；
6. 读 `logs/run_*.log` 末行 `STATUS=…` 与其上方的 `figure:` / `edit applied:` 行；
7. **做对照时再看 §1 增益侵蚀表**：把降级映射到受影响的那项指标，再解释 Δ。

---

# 附录 B：v3 的失败模式文档（机制视角）—— 原文逐字保留

> 为什么保留：v3 把每一族失败额外写成"**这条降级伤了哪个机制、探针能不能查出来**"，
> 是 §10 机制受损对照表的展开版。判据探针见 `references/mechanism_probe.py`。

本文件把失败分成**五族**（材料异常 / 模板缺失 / 依赖缺失 / 契约四形态 / 状态不一致）逐条展开，
并额外回答一个本版特有的问题：**这次降级打坏了哪个机制**（M1–M5，见
[`MECHANISM.md`](MECHANISM.md)）—— 因为机制受损是可以被探针查出来的。

一条总原则：**宁可如实降级并留下可查的记录，也不把"降级"包装成"成功"。**
判定"某条降级是否被正确执行"的**唯一办法**是去它声明的记录字段里找那条记录：
**找不到记录 = 这条降级没有执行**。

---

## 0. 退出码与判读

| 脚本 | 0 | 1 | 2 |
|-|-|-|-|
| `scripts/main.py` | `status=success`（产物齐备、G1–G8 过、自检 `all_pass`） | `status=partial`（有降级/未核验项，逐条记入 `uncertainty`） | 输入不可读，已写最小 `status=failed` result |
| `scripts/result_tool.py` | G1–G8 全过（`{"valid": true}`） | 有条目未过（`errors` 非空） | `result.json` 无法解析 |
| `scripts/selftest.py` | 全部自检项通过 | 有未通过项（列在 `checks[]`） | 输入不可读 |
| `scripts/evidence_check.py` | 主张里每个数字都能定位 | 有数字找不到（`missing=[…]`） | — |
| `references/mechanism_probe.py` | M1–M5 全 PASS | 有判据 FAIL（打印具体缺陷） | 输出目录无 `result.json` |

**只有 exit 0 才算这次运行"干净"**；exit 1 必须读 `result.json.uncertainty` 再决定
是否补件重跑；exit 2 是输入侧问题，重跑无用。

---

## 1. ★ 降级 → 机制受损对照表（本版特有）

| 降级 | 触发 | 受损机制 | 探针会说什么 | 处置要求 |
|-|-|-|-|-|
| 图表降级为原生表格 | 无 matplotlib / 非数值列 / `--no-chart` | **M3**（态从 `chart_image` 变 `table`，机制未破） | `M3` 仍 PASS（`table` 是词表内合法态） | 在 `figure.note` 写清降级原因 |
| 位图无数据 → 占位 | 材料图无取数数据 | **M3**（走 `placeholder` 分支） | `M3` 仍 PASS | `figure.note` 必须写明"原图未提供取数数据" |
| 预览 PDF 跳过 | 无 reportlab / `--draft` | 无（不属任何机制） | `M5`/`M4` 不受影响 | 记入 `previews.warnings` |
| 预览 PNG 缺失 | 无 Pillow | **M5** 的产物齐全度（G5 报错） | `M4`/`M5` 可能仍 PASS（探针查的是契约与版本链，不查预览齐备） | 状态降 partial 并写明；**不要**用别的图冒充预览 |
| 材料部分缺失 | 多份材料只读到一部分 | **M2**（缺失材料的数字无法核） | `M2` 仍 PASS，但 `unverified_claims` 可能非空 | `material_warnings` 列出缺失项 |
| 材料全缺 | 一个文件都读不到 | **M1/M2/M3 全部**（无 deck） | `M1` 会 FAIL（无 slides） | 这是 D1 的**正确行为**；探针 FAIL 在此处是"如实反映"而不是缺陷 |
| 数字核验不过 | 主张数字材料中找不到 | **M2** | `M2` 仍 PASS（指标只要求"有证据指针"且状态自洽） | 该主张进 `unverified_claims`；状态降 partial |
| CP2 lint 偏差 | 单条超长 / 页数超限 | 无（不影响 M1–M5 判据） | 探针不受影响 | 记 `run_meta.spec_lint`，状态降 partial |
| 编辑未应用 | op 非法 | **M4** 的版本链完整性（若连版本都没写） | `M4` 在缺 changelog/多版本时 FAIL | 记 `uncertainty` + `changelog` skipped |
| 模板打不开 | `Presentation()` 抛错 | 无（属外观约束） | 探针不受影响 | 记 `uncertainty` + `change_records` |

> **用法**：跑完一次后先跑探针，再按本表解释每一条 FAIL 或降级。
> **探针 FAIL 不等于产物一定不合格**（例如材料全缺时 M1 FAIL 是正确行为），
> 但**必须能在 `uncertainty` / `material_warnings` 里找到对应解释**。

---

## 2. 材料异常族

| 失败模式 | 识别信号 | 处置 | 记录 | 受损机制 |
|-|-|-|-|-|
| 材料文件不存在 / 为空 | `material_status=missing` | **不补造、不编 deck**：只出元信息 result（`deck.slide_count=0`），状态 partial | `material_warnings` + `uncertainty` | M1/M2/M3（全无产物） |
| 部分材料缺失 | `material_status=partial` | 用已读到的继续；缺的显式标出，页面上不得出现只有它才有的数字 | `material_warnings` | M2 |
| 扫描件 / 无文本层 PDF | 抽取为空或近空 | 不 OCR 冒充；Agent 抽文本到 `<out>/work/materials/*.txt` 后重跑 | `uncertainty` + `sources[].tool` | M2 |
| 无 PDF 抽取库 | 抽取阶段抛错 | 同上；**不静默把 PDF 当空文件** | `uncertainty` | M2 |
| 数字与主张不一致 | `check_claim_numbers` 返回 `missing` 非空 | 该主张 `verified=false`，**不回填、不取整、不按印象改** | `unverified_claims` | M2 |
| 数据表缺列 / 非数值列 | 图表绑定阶段判定 | 降级 PPTX 原生可编辑表格（仍是 M3 的合法态） | `figure.note` + `uncertainty` | M3（降级不破） |

> `material_warnings`（材料问题）、`uncertainty`（无法核验/降级）、`status`（整体成败）
> 语义不同，**必须分开记录**。

---

## 3. 模板缺失族

| 失败模式 | 识别信号 | 处置 | 记录 |
|-|-|-|-|
| `template_pptx` 打不开 / 损坏 | `Presentation()` 抛错 | 备份原文件 → 回退内置 `templates/default.json` | `uncertainty` + `change_records` |
| 版式/占位符不足 | 母版版式枚举不足 | 复用最接近版式 + 新增文本框，**绝不改母版**；仍不够则减要点而非压字号 <12pt | `change_records` |
| `starting_deck` 需适配 | 起始稿存在 | 先备份到 `work/original_inputs/` 再重排；每处改动记一条 | `change_records` |
| 页数超限 | `plan_lint` 报超限 | 确定性压缩角色；**不静默丢证据页**，合并说明写进备注 | `run_meta.spec_lint` + `change_records` |
| 无模板但要特定配色/页脚 | `spec.style` 缺键 | 用模板默认值；模板是数据不是代码 | `change_records` |

---

## 4. 依赖缺失族（依赖与机制的直接耦合）

| 依赖 | 缺失时的行为 | 受损机制 | 记录 |
|-|-|-|-|
| `python-pptx` | **致命**：无法建稿 → partial/failed，如实说明缺什么 | M1/M3/M4（无 deck 可查） | `uncertainty` + `status` |
| `matplotlib` | 结果页降级原生可编辑表格 | M3（`chart_image` → `table`） | `figure.note` + `uncertainty` |
| `Pillow` | 预览 PNG 不产出 → G5 报错、自检不过 | M5（产物齐全度） | `previews.warnings` |
| `reportlab` | 跳过 PDF（`previews.pdf=""`），PNG 不受影响 | 无 | `previews.warnings` |
| CJK 字体（预览用） | 预览出方块但 **PPTX 不受影响** | 无（仅预览外观） | `previews.warnings` |
| 字体探测全落空 | 回落 PIL 默认字体并预警；**不下载、不内嵌字体文件** | 无 | `uncertainty` |

依赖实测版本写入 `result.json.environment`，便于区分"环境缺库"与"实现有缺陷"。
**探针本身只依赖标准库**（pptx 重开检查在缺库时如实报 FAIL，不假装通过）。

---

## 5. 契约四形态（M5 的判定面）

**任何已声明字段都禁止 `null`**：

| 声明类型 | 空值 | 有真实值时 |
|-|-|-|
| `string` / `str` | `""` | 真实字符串 |
| `list` / `array` | `[]` | 真实列表 |
| `dict` / `object` | `{}` | 真实对象 |
| `bool` / `boolean` | `false` | `true` / `false` |
| `int` / `float` / `number` | `0` | 真实数值 |
| 未声明类型（裸值） | 按运行时值类型给同型空值 | — |

实现：`scripts/result_tool.py::apply_output_contract`；校验：G2（齐全 + 非 null）
与 G8（`templates/result_envelope.json` 类型合规）；探针侧由 `M5_contract` 复查顶层无 `null`。

> ⚠ **`--case` 必须传给 `result_tool.py`**，否则无法做契约回显核对 ——
> 漏传会让"契约全回显"看起来失败。这是本 Skill 最容易误判的一处。

---

## 6. 状态一致性（M5 的"三层不互相顶替"）

| 状态 | 允许 | 禁止 |
|-|-|-|
| `success` | `uncertainty` 可为空；`checks.all_pass=true`；G 门通过；`unverified_claims` 为空 | 有未核验主张却标 success；有降级却没写原因 |
| `partial` | 核心产物（PPTX）可用但至少一项降级（图表降级/PDF 缺失/CP2 lint 偏差/编辑未应用/有未核验主张） | **每条降级原因都必须在 `uncertainty` 里有对应条目**（缺一即不自洽） |
| `failed` | 只写最小 result.json 说明原因 | 不产出任何 deck 却标 success；把预览冒充 Office 导出件 |

**三层核验不许互相顶替**：

| 层 | 查什么 | 不查什么 |
|-|-|-|
| `selftest.py` | 产物在不在、能不能开、页数对不对 | 内容是否正确 |
| `result_tool.py` | 契约合不合规（G1–G8） | 内容是否正确 |
| `evidence_check.py` | 数字能否指回材料、页面纪律 | 契约是否合规 |
| `mechanism_probe.py` | 机制痕迹在不在（M1–M5） | 讲得好不好 |

**四者都过，也不等于内容正确** —— 这一点是本包反复强调的边界。

---

## 7. 编辑链路（`--edit`）异常（M4 的判定面）

| 失败模式 | 识别信号 | 处置 | 记录 |
|-|-|-|-|
| 未知 `op` | `apply_edits` 不认识 | 跳过该条，其余照常 | `uncertainty` + `changelog` skipped |
| 页码 / `bullet_index` 越界 | 越界 | 同上，不改动目标页 | 同上 |
| `reorder_pages` 不是完整置换 | 不是 `1..N` 的置换 | 拒绝该条（避免"静默丢页"） | 同上 |
| 编辑引入的新数字材料中没有 | 重跑核验未命中 | 该主张 `verified=false`，**不因"是用户让改的"就放行** | `unverified_claims` |
| 改坏要回退 | — | 复制上一版 `work/deck_<v>.pptx` 重跑，并补一条回退 change_record | `change_records` |
| 多版本并存但主版本丢失 | `work/` 下只有 `deck_v2.pptx` | **不允许**：主版本必须保留（否则回退语义破裂） | 探针 `M4_versioning` 会 FAIL |

---

## 8. 资源形态与随包脚本的自我约束

| 失败模式 | 处置 |
|-|-|
| 包内混入二进制（`.pptx/.png/.pdf/.svg/.jsonl`） | 平台预检直接拒收整包。本包只携带 UTF-8 文本；模板参数化、图表/预览运行时生成 |
| 文件数 >50 | 保持 20–40 文件形态；新增能力并入既有文档而不是无限新增文件 |
| 包内出现本机绝对路径 | 示例由 `scripts/make_examples.py` 自动净化；**唯一允许的命中**是字体探测候选路径，且不得写入示例 JSON |
| **在包内运行任何脚本** | 生成 `scripts/__pycache__/` → 验收器直接 FAIL。**随包的两个脚本尤其注意**：`references/mechanism_probe.py` 与 `references/measure_gain.py` 都必须在**包外**运行（复制到临时目录，或整体复制技能包） |
| 探针报告的落点 | 探针把 `mechanism-probe-report.json` 写在**当前工作目录**，所以务必在包外跑 |
| 探针 FAIL 被当成"包坏了" | 先查 §1 对照表：材料全缺等场景下探针 FAIL 是**如实反映**，需在 `uncertainty` 找到解释 |

---

## 9. 排查顺序（复跑失败时按此走）

1. 跑探针：`python references/mechanism_probe.py --out <out>` —— 先看 M1–M5 哪一条 FAIL；
2. 读 `result.json.environment`（实测库版本）→ 依赖是否缺失（§4）；
3. 读 `evidence.material_warnings`（材料路径/缺失，§2）；
4. 读 `run_meta.checkpoints`（哪一门没过：cp1_extract / cp2_plan / cp3_build / cp4_verify）；
5. 读 `run_meta.spec_lint.problems`（页面纪律偏差，§3）；
6. 读 `run_meta.gate.errors` 与 `uncertainty`（契约门与降级原因，§5/§6）；
7. 读 `logs/run_*.log` 末行 `STATUS=…` 与其上方的 `figure:` / `edit applied:` 行；
8. 若仍不明：按 §1 把降级映射到受损机制，再决定是修实现还是改文档。

**判读提示**：四门全 `true` 但 `status=partial` 是**设计如此**（`uncertainty` 里有条目），
不是缺陷。反过来，`status=success` 但 `uncertainty` 非空才是真正的不自洽。
