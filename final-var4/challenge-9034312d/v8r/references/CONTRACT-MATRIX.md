# CONTRACT-MATRIX.md — 契约「容器形态 × 边界值」实测矩阵（本包 v8 的轴）

> 本文各表由 `scripts/contract_matrix.py` 现场跑出，按报告的 `rows[]` / `silent_pass[]` /
> `defects[]` / `counts` 逐行渲染，**没有一个手写数字**。
> 复核命令：`python "$SKILL_DIR/scripts/contract_matrix.py" --json /tmp/cm.json`
> 报告原文里 `rows[]` 是逐行实测原始记录（164 行），本文只做渲染与归类。

`references/OUTPUT_CONTRACT.md` 有一句硬话：

> 字段缺失或类型不符 ⇒ `scripts/check.py` 报 issue，**status 不能为 success**。

这一轴就是把这句话**逐字段、逐边界**打一遍，看它到底在哪里成立、在哪里只是"报了 issue 但门没关"。

---

## 0. 一句话结论（先说最难听的）

**契约声明了 18 个顶层字段，而 `check.py` 的 `required_fields` 只覆盖 9 个。**
另外 9 个（`workorder` `extraction` `entities` `relations` `evidence` `verify` `canvas`
`fonts` `execution`）**没有任何存在性检查**。其中 `entities` / `relations` 会被
`G5` / `G6` / `G7` 间接读到，所以"删掉它们"能在下游炸掉；而 `workorder` / `extraction` /
`canvas` / `fonts` / `execution` / `evidence` / `verify` 七段
**改成任意容器形态都能零退出通过**（`G9` 读的是 **`verify_report.json` 文件**，
不是 `result.json` 里的 `verify` 段 —— 这正是 §6 的 `nest-08/09/10` 三条缺陷的成因）。

这不是本包引入的缺陷（`check.py` 与基线逐字节相同），而是**这一轴第一次把它量出来**。
本包的处理是：**把差异写进本文 + 把矩阵做成可回归断言（`--expect-defects`）**，
而不是偷偷改门（改门会动 CLI 语义，规范禁止）。

## 1. 契约面自校验（先证明矩阵是在测"真的契约"）

| 契约字段 | 声明容器形态 | 进入 check.py 的 required_fields | 机器门实际检查什么 |
|---|---|---|---|
| `case_id` | str | 是 | 存在性（缺失 ⇒ issues） |
| `title` | str | 是 | 存在性（缺失 ⇒ issues） |
| `status` | enum | 是 | 存在性（缺失 ⇒ issues） |
| `workorder` | str | **否** | 无任何检查 |
| `figure_type` | enum | 是 | 存在性（缺失 ⇒ issues） |
| `extraction` | enum | **否** | 无任何检查 |
| `entities` | list | **否** | 无任何检查 |
| `relations` | list | **否** | 无任何检查 |
| `output_contract` | object | 是 | 存在性（缺失 ⇒ issues） |
| `evidence` | object | **否** | 无任何检查 |
| `verify` | object | **否** | 无任何检查 |
| `canvas` | object | **否** | 无任何检查 |
| `fonts` | list | **否** | 无任何检查 |
| `sources` | list | 是 | 存在性（缺失 ⇒ issues） |
| `uncertainty` | list | 是 | 存在性（缺失 ⇒ issues） |
| `change_record` | list | 是 | 存在性（缺失 ⇒ issues） |
| `execution` | object | **否** | 无任何检查 |
| `checksum` | str | 是 | 存在性（缺失 ⇒ issues） |

第一段做两条交叉核对：

1. `references/OUTPUT_CONTRACT.md` 的字段块 ⇄ `scripts/contract_matrix.py` 的内置清单
   → `contract_doc_matches`（本包 **true**，18 = 18）；
2. 同一份清单 ⇄ `scripts/check.py` 的 `required_fields` 源码解析
   → `contract_fields_not_checked`（本包 **9 个**）。

**这一步的意义**：如果文档与脚本清单不一致，后面的矩阵就是在测错的东西；
矩阵先自证测的是契约，再谈结论。

## 2. 第二段 · 输入侧注入（22 条，跑 `main.py` 全流程）

把 `case.json` 按非法容器 / 缺字段 / 空容器 / 超长逐个弄坏。信号分级：

- `failed` — 退出码非 0 或 `status=failed`（最响）；
- `partial` — 退出码 0 但 `status=partial`（诚实降级）；
- `success+recorded` — `status=success` 但 `uncertainty` 非空或 `extraction=text-heuristic`
  （**有记录**，能追溯）；
- `success-zero-signal` — `status=success` 且零记录（**沉默**）。

缺陷判据不是"注入得怪"，而是**产物本身违约**：18 字段形态不符、`status` 非法、
或 `status=success` 却带着未解决的 `uncertainty`（`OUTPUT_CONTRACT.md` 的状态表明确禁止后者）。

| id | 注入 | 违约 | 退出码 | status | 信号 | 期望 | 产物契约形态违规 | 缺陷 | 静默 |
|---|---|---|---|---|---|---|---|---|---|
| in-01 | entities=字符串 | True | 0 | success | success+recorded | none | — | True | True |
| in-02 | entities=空数组 | False | 0 | success | success+recorded | none | — | False | False |
| in-03 | entities=对象 | True | 0 | success | success+recorded | none | — | True | True |
| in-04 | entities=0 | True | 0 | success | success+recorded | none | — | True | True |
| in-05 | entities=null | True | 0 | success | success+recorded | none | — | True | True |
| in-06 | case_id=数值 | True | 0 | success | success-zero-signal | none | — | False | True |
| in-07 | case_id=空串 | True | 0 | success | success-zero-signal | none | — | False | True |
| in-08 | case_id 缺字段 | True | 0 | success | success-zero-signal | none | — | False | True |
| in-09 | canvas=数值 | True | 0 | success | success-zero-signal | none | — | False | True |
| in-10 | canvas.width_mm=负值 | True | 0 | success | success-zero-signal | none | — | False | True |
| in-11 | canvas.width_mm=字符串 | True | 1 | failed | failed | none | — | True | False |
| in-12 | figure_type=非法枚举 | True | 0 | success | success-zero-signal | none | — | False | True |
| in-13 | relations=字符串 | True | 0 | partial | partial | none | — | False | False |
| in-14 | relations=空数组 | False | 0 | partial | partial | none | — | False | False |
| in-15 | title=超长 12k 字 | False | 0 | success | success-zero-signal | none | — | False | False |
| in-16 | entities[0].id 空串 | True | 0 | partial | partial | none | — | False | False |
| in-17 | relations[0] 缺 from | True | 0 | partial | partial | none | — | False | False |
| in-18 | 顶层 JSON 数组 | True | 1 | failed | failed | none | — | True | False |
| in-19 | 空对象 {} | True | 0 | success | success+recorded | none | — | True | True |
| in-20 | 非 JSON 文本 | True | 1 | failed | failed | none | — | True | False |
| in-21 | entities=120 条 | False | 3 | partial | failed | none | — | False | False |
| in-22 | entities 元素=字符串 | True | 0 | success | success+recorded | none | — | True | True |

## 3. 第三段 · 输出侧注入（106 条，跑 `check.py` 的 G1–G10）

拿一次真实运行的 `result.json`，把**每个契约字段**按边界值（缺字段 / null / 空值 /
非法类型 / 超长）逐个替换。信号分级：

- `gate` — `ok=false`，退出码 1，**有 G 门被拦下**（门的本职）；
- `issues-only` — `ok=true`、退出码 **0**，只在 `issues[]` 里写了一条（契约承诺"报 issue"，
  但**门没关** —— 这是 `check.py` 的结构性事实：`ok = all(gates)`，`issues` 不计入 `ok`）；
- `crash` — `check.py` 抛异常（`AttributeError`），退出码 1 但**没有结构化报告**；
- `none` — 零信号。

| id | 注入 | 违约 | check 退出码 | ok | 信号 | 期望 | 未过的门 | 缺陷 | 静默 |
|---|---|---|---|---|---|---|---|---|---|
| out-case_id-missing | case_id 缺字段 | True | 1 | False | gate | gate | G1, G10 | False | False |
| out-case_id-null | case_id=null | True | 1 | False | gate | gate | G1, G10 | False | False |
| out-case_id-empty | case_id=空值(str) | False | 1 | False | gate | gate | G1, G10 | False | False |
| out-case_id-wrongtype | case_id=number(≠str) | True | 1 | False | gate | gate | G1, G10 | False | False |
| out-case_id-huge | case_id=超长(str) | True | 0 | True | none | none | — | False | True |
| out-title-missing | title 缺字段 | True | 0 | True | issues-only | issue | — | False | True |
| out-title-null | title=null | True | 0 | True | none | none | — | False | True |
| out-title-empty | title=空值(str) | False | 0 | True | none | none | — | False | False |
| out-title-wrongtype | title=number(≠str) | True | 0 | True | none | none | — | False | True |
| out-title-huge | title=超长(str) | True | 0 | True | none | none | — | False | True |
| out-status-missing | status 缺字段 | True | 1 | False | gate | gate | G1 | False | False |
| out-status-null | status=null | True | 1 | False | gate | gate | G1 | False | False |
| out-status-empty | status=空值(enum) | False | 1 | False | gate | gate | G1 | False | False |
| out-status-wrongtype | status=number(≠enum) | True | 1 | False | gate | gate | G1 | False | False |
| out-status-huge | status=超长(enum) | True | 1 | False | gate | none | G1 | False | False |
| out-workorder-missing | workorder 缺字段 | True | 0 | True | none | none | — | False | True |
| out-workorder-null | workorder=null | True | 0 | True | none | none | — | False | True |
| out-workorder-empty | workorder=空值(str) | False | 0 | True | none | none | — | False | False |
| out-workorder-wrongtype | workorder=number(≠str) | True | 0 | True | none | none | — | False | True |
| out-workorder-huge | workorder=超长(str) | True | 0 | True | none | none | — | False | True |
| out-figure_type-missing | figure_type 缺字段 | True | 0 | True | issues-only | issue | — | False | True |
| out-figure_type-null | figure_type=null | True | 0 | True | none | none | — | False | True |
| out-figure_type-empty | figure_type=空值(enum) | False | 0 | True | none | none | — | False | False |
| out-figure_type-wrongtype | figure_type=number(≠enum) | True | 0 | True | none | none | — | False | True |
| out-figure_type-huge | figure_type=超长(enum) | True | 0 | True | none | none | — | False | True |
| out-extraction-missing | extraction 缺字段 | True | 0 | True | none | none | — | False | True |
| out-extraction-null | extraction=null | True | 0 | True | none | none | — | False | True |
| out-extraction-empty | extraction=空值(enum) | False | 0 | True | none | none | — | False | False |
| out-extraction-wrongtype | extraction=number(≠enum) | True | 0 | True | none | none | — | False | True |
| out-extraction-huge | extraction=超长(enum) | True | 0 | True | none | none | — | False | True |
| out-entities-missing | entities 缺字段 | True | 1 | False | gate | gate | G10, G5, G7 | False | False |
| out-entities-null | entities=null | True | 1 | False | gate | gate | G10, G5, G7 | False | False |
| out-entities-empty | entities=空值(list) | True | 1 | False | gate | gate | G10, G5, G7 | False | False |
| out-entities-wrongtype | entities=str(≠list) | True | 1 | — | crash | gate | — | False | False |
| out-entities-huge | entities=超长(list) | True | 1 | — | crash | none | — | False | False |
| out-relations-missing | relations 缺字段 | True | 0 | True | none | none | — | False | True |
| out-relations-null | relations=null | True | 0 | True | none | none | — | False | True |
| out-relations-empty | relations=空值(list) | True | 0 | True | none | none | — | False | True |
| out-relations-wrongtype | relations=str(≠list) | True | 1 | — | crash | none | — | False | False |
| out-relations-huge | relations=超长(list) | True | 1 | — | crash | none | — | False | False |
| out-output_contract-missing | output_contract 缺字段 | True | 1 | False | gate | gate | G10, G2, G3, G4, G5, G6 | False | False |
| out-output_contract-null | output_contract=null | True | 1 | False | gate | gate | G10, G2, G3, G4, G5, G6 | False | False |
| out-output_contract-empty | output_contract=空值(object) | False | 1 | False | gate | none | G10, G2, G3, G4, G5, G6 | False | False |
| out-output_contract-wrongtype | output_contract=str(≠object) | True | 1 | — | crash | none | — | False | False |
| out-output_contract-huge | output_contract=超长(object) | True | 1 | False | gate | none | G10, G2, G3, G4, G5, G6 | False | False |
| out-evidence-missing | evidence 缺字段 | True | 0 | True | none | none | — | False | True |
| out-evidence-null | evidence=null | True | 0 | True | none | none | — | False | True |
| out-evidence-empty | evidence=空值(object) | False | 0 | True | none | none | — | False | False |
| out-evidence-wrongtype | evidence=str(≠object) | True | 0 | True | none | none | — | False | True |
| out-evidence-huge | evidence=超长(object) | True | 0 | True | none | none | — | False | True |
| out-verify-missing | verify 缺字段 | True | 0 | True | none | none | — | False | True |
| out-verify-null | verify=null | True | 0 | True | none | none | — | False | True |
| out-verify-empty | verify=空值(object) | False | 0 | True | none | none | — | False | False |
| out-verify-wrongtype | verify=str(≠object) | True | 0 | True | none | none | — | False | True |
| out-verify-huge | verify=超长(object) | True | 0 | True | none | none | — | False | True |
| out-canvas-missing | canvas 缺字段 | True | 0 | True | none | none | — | False | True |
| out-canvas-null | canvas=null | True | 0 | True | none | none | — | False | True |
| out-canvas-empty | canvas=空值(object) | False | 0 | True | none | none | — | False | False |
| out-canvas-wrongtype | canvas=str(≠object) | True | 0 | True | none | none | — | False | True |
| out-canvas-huge | canvas=超长(object) | True | 0 | True | none | none | — | False | True |
| out-fonts-missing | fonts 缺字段 | True | 0 | True | none | none | — | False | True |
| out-fonts-null | fonts=null | True | 0 | True | none | none | — | False | True |
| out-fonts-empty | fonts=空值(list) | True | 0 | True | none | none | — | False | True |
| out-fonts-wrongtype | fonts=str(≠list) | True | 0 | True | none | none | — | False | True |
| out-fonts-huge | fonts=超长(list) | True | 0 | True | none | none | — | False | True |
| out-sources-missing | sources 缺字段 | True | 0 | True | issues-only | issue | — | False | True |
| out-sources-null | sources=null | True | 0 | True | none | none | — | False | True |
| out-sources-empty | sources=空值(list) | True | 0 | True | none | none | — | False | True |
| out-sources-wrongtype | sources=str(≠list) | True | 0 | True | none | none | — | False | True |
| out-sources-huge | sources=超长(list) | True | 0 | True | none | none | — | False | True |
| out-uncertainty-missing | uncertainty 缺字段 | True | 0 | True | issues-only | issue | — | False | True |
| out-uncertainty-null | uncertainty=null | True | 0 | True | none | none | — | False | True |
| out-uncertainty-empty | uncertainty=空值(list) | False | 0 | True | none | none | — | False | False |
| out-uncertainty-wrongtype | uncertainty=str(≠list) | True | 0 | True | none | none | — | False | True |
| out-uncertainty-huge | uncertainty=超长(list) | True | 0 | True | none | none | — | False | True |
| out-change_record-missing | change_record 缺字段 | True | 0 | True | issues-only | issue | — | False | True |
| out-change_record-null | change_record=null | True | 0 | True | none | none | — | False | True |
| out-change_record-empty | change_record=空值(list) | True | 0 | True | none | none | — | False | True |
| out-change_record-wrongtype | change_record=str(≠list) | True | 0 | True | none | none | — | False | True |
| out-change_record-huge | change_record=超长(list) | True | 0 | True | none | none | — | False | True |
| out-execution-missing | execution 缺字段 | True | 0 | True | none | none | — | False | True |
| out-execution-null | execution=null | True | 0 | True | none | none | — | False | True |
| out-execution-empty | execution=空值(object) | False | 0 | True | none | none | — | False | False |
| out-execution-wrongtype | execution=str(≠object) | True | 0 | True | none | none | — | False | True |
| out-execution-huge | execution=超长(object) | True | 0 | True | none | none | — | False | True |
| out-checksum-missing | checksum 缺字段 | True | 0 | True | issues-only | issue | — | False | True |
| out-checksum-null | checksum=null | True | 0 | True | none | none | — | False | True |
| out-checksum-empty | checksum=空值(str) | False | 0 | True | none | none | — | False | False |
| out-checksum-wrongtype | checksum=number(≠str) | True | 0 | True | none | none | — | False | True |
| out-checksum-huge | checksum=超长(str) | True | 0 | True | none | none | — | False | True |
| nest-01 | output_contract.editable_sources[0].path='' | True | 1 | False | gate | gate | G10, G3 | False | False |
| nest-02 | output_contract.exports=[] | True | 1 | False | gate | gate | G10, G4 | False | False |
| nest-03 | output_contract.data_mapping=[]（实体非空） | True | 1 | False | gate | gate | G10, G5 | False | False |
| nest-04 | output_contract.element_traceability=[] | True | 1 | False | gate | gate | G10, G6 | False | False |
| nest-05 | output_contract=字符串 | True | 1 | — | crash | gate | — | False | False |
| nest-06 | evidence.items=字符串 | True | 0 | True | none | none | — | False | True |
| nest-07 | evidence 缺 source_files | True | 0 | True | none | none | — | False | True |
| nest-08 | verify.ok='true'（字符串真值） | True | 0 | True | none | gate | — | True | True |
| nest-09 | verify.ok=1（数值真值） | True | 0 | True | none | gate | — | True | True |
| nest-10 | verify={}（ok 缺字段） | True | 0 | True | none | gate | — | True | True |
| nest-11 | entities=[] 且 data_mapping=[]（空对空 + status=success） | True | 0 | True | none | gate | — | True | True |
| nest-12 | uncertainty={}（应为列表） | True | 0 | True | none | none | — | False | True |
| nest-13 | change_record=字符串 | True | 0 | True | none | none | — | False | True |
| nest-14 | sources=[null] | True | 0 | True | none | none | — | False | True |
| nest-15 | checksum=''（空串） | True | 0 | True | none | none | — | False | True |
| nest-16 | 额外未知字段（应被容忍） | False | 0 | True | none | none | — | False | False |

## 4. 第四段 · 六形态 × 代表字段 + 嵌套结构（36 条）

「字符串 / 列表 / 对象 / 数值 / 布尔 / 嵌套」六种容器形态逐个塞进六个代表字段
（`output_contract` / `entities` / `evidence` / `verify` / `checksum` / `status`），
再打契约四段的内部结构（`editable_sources[].path`、`exports`、`data_mapping`、
`element_traceability`、`evidence.items`、`verify.ok`、`uncertainty`…）。

| id | 注入 | 违约 | check 退出码 | ok | 信号 | 期望 | 未过的门 | 缺陷 | 静默 |
|---|---|---|---|---|---|---|---|---|---|
| form-00-str | output_contract=str | True | 1 | — | crash | none | — | False | False |
| form-00-list | output_contract=list | True | 1 | False | gate | none | G10, G2, G3, G4, G5, G6 | False | False |
| form-00-object | output_contract=object | False | 1 | False | gate | none | G10, G2, G3, G4, G5, G6 | False | False |
| form-00-number | output_contract=number | True | 1 | False | gate | none | G10, G2, G3, G4, G5, G6 | False | False |
| form-00-bool | output_contract=bool | True | 1 | False | gate | none | G10, G2, G3, G4, G5, G6 | False | False |
| form-00-nested | output_contract=nested | True | 1 | False | gate | none | G10, G2, G3, G4, G5, G6 | False | False |
| form-01-str | entities=str | True | 1 | — | crash | gate | — | False | False |
| form-01-list | entities=list | False | 1 | False | gate | none | G10, G5, G7 | False | False |
| form-01-object | entities=object | True | 1 | False | gate | none | G10, G5, G7 | False | False |
| form-01-number | entities=number | True | 1 | False | gate | gate | G10, G5, G7 | False | False |
| form-01-bool | entities=bool | True | 1 | False | gate | gate | G10, G5, G7 | False | False |
| form-01-nested | entities=nested | True | 1 | — | crash | none | — | False | False |
| form-02-str | evidence=str | True | 0 | True | none | none | — | False | True |
| form-02-list | evidence=list | True | 0 | True | none | none | — | False | True |
| form-02-object | evidence=object | False | 0 | True | none | none | — | False | False |
| form-02-number | evidence=number | True | 0 | True | none | none | — | False | True |
| form-02-bool | evidence=bool | True | 0 | True | none | none | — | False | True |
| form-02-nested | evidence=nested | True | 0 | True | none | none | — | False | True |
| form-03-str | verify=str | True | 0 | True | none | none | — | False | True |
| form-03-list | verify=list | True | 0 | True | none | none | — | False | True |
| form-03-object | verify=object | False | 0 | True | none | none | — | False | False |
| form-03-number | verify=number | True | 0 | True | none | none | — | False | True |
| form-03-bool | verify=bool | True | 0 | True | none | none | — | False | True |
| form-03-nested | verify=nested | True | 0 | True | none | none | — | False | True |
| form-04-str | checksum=str | False | 0 | True | none | none | — | False | False |
| form-04-list | checksum=list | True | 0 | True | none | none | — | False | True |
| form-04-object | checksum=object | True | 0 | True | none | none | — | False | True |
| form-04-number | checksum=number | True | 0 | True | none | none | — | False | True |
| form-04-bool | checksum=bool | True | 0 | True | none | none | — | False | True |
| form-04-nested | checksum=nested | True | 0 | True | none | none | — | False | True |
| form-05-str | status=str | True | 1 | False | gate | gate | G1 | False | False |
| form-05-list | status=list | True | 1 | False | gate | none | G1 | False | False |
| form-05-object | status=object | True | 1 | False | gate | none | G1 | False | False |
| form-05-number | status=number | True | 1 | False | gate | gate | G1 | False | False |
| form-05-bool | status=bool | True | 1 | False | gate | gate | G1 | False | False |
| form-05-nested | status=nested | True | 1 | False | gate | none | G1 | False | False |

## 5. 静默通过清单（原始观测，逐条）

`silent_pass` = **注入值违反契约声明，但门仍放行**（输出侧 `ok=true`，输入侧
`exit 0` 且 `status=success`）。本包实测 **96 条**，按性质分三类：

| 段 | 实测信号 | 归类 | 行数 |
|---|---|---|---|
| output | none | 未覆盖 | 59 |
| form | none | 未覆盖 | 15 |
| input | success+recorded | 缺陷 | 6 |
| input | success-zero-signal | 未覆盖 | 6 |
| output | issues-only | 未覆盖 | 6 |
| output | none | 缺陷 | 4 |

**① 门面内缺陷（10 条）** —— 期望被拦、实际没拦，逐条列在 §6。
**② 仅报 issue（6 条）** —— `title`/`figure_type`/`sources`/`uncertainty`/`change_record`/`checksum`
缺字段时，`check.py` 往 `issues[]` 写一条但 `ok` 不变。契约的原文是"报 issue"，所以这算**履约**；
但它的退出码是 **0**，自动化流水线若只看退出码就会漏掉 —— 这是**用法陷阱**，写进本节。
**③ 未覆盖（86 条）** —— 落在 G1–G10 检查面之外的字段与形态（见 §0 的 9 个字段）。
它们是**设计边界**不是缺陷，但**必须点名**，否则"矩阵全绿"就是假象。

| id | 段 | 实测信号 | 期望信号 | 归类 |
|---|---|---|---|---|
| in-01 | input | success+recorded | none | 缺陷 |
| in-03 | input | success+recorded | none | 缺陷 |
| in-04 | input | success+recorded | none | 缺陷 |
| in-05 | input | success+recorded | none | 缺陷 |
| in-06 | input | success-zero-signal | none | 未覆盖（设计边界） |
| in-07 | input | success-zero-signal | none | 未覆盖（设计边界） |
| in-08 | input | success-zero-signal | none | 未覆盖（设计边界） |
| in-09 | input | success-zero-signal | none | 未覆盖（设计边界） |
| in-10 | input | success-zero-signal | none | 未覆盖（设计边界） |
| in-12 | input | success-zero-signal | none | 未覆盖（设计边界） |
| in-19 | input | success+recorded | none | 缺陷 |
| in-22 | input | success+recorded | none | 缺陷 |
| out-case_id-huge | output | none | none | 未覆盖（设计边界） |
| out-title-missing | output | issues-only | issue | 仅报 issue |
| out-title-null | output | none | none | 未覆盖（设计边界） |
| out-title-wrongtype | output | none | none | 未覆盖（设计边界） |
| out-title-huge | output | none | none | 未覆盖（设计边界） |
| out-workorder-missing | output | none | none | 未覆盖（设计边界） |
| out-workorder-null | output | none | none | 未覆盖（设计边界） |
| out-workorder-wrongtype | output | none | none | 未覆盖（设计边界） |
| out-workorder-huge | output | none | none | 未覆盖（设计边界） |
| out-figure_type-missing | output | issues-only | issue | 仅报 issue |
| out-figure_type-null | output | none | none | 未覆盖（设计边界） |
| out-figure_type-wrongtype | output | none | none | 未覆盖（设计边界） |
| out-figure_type-huge | output | none | none | 未覆盖（设计边界） |
| out-extraction-missing | output | none | none | 未覆盖（设计边界） |
| out-extraction-null | output | none | none | 未覆盖（设计边界） |
| out-extraction-wrongtype | output | none | none | 未覆盖（设计边界） |
| out-extraction-huge | output | none | none | 未覆盖（设计边界） |
| out-relations-missing | output | none | none | 未覆盖（设计边界） |
| out-relations-null | output | none | none | 未覆盖（设计边界） |
| out-relations-empty | output | none | none | 未覆盖（设计边界） |
| out-evidence-missing | output | none | none | 未覆盖（设计边界） |
| out-evidence-null | output | none | none | 未覆盖（设计边界） |
| out-evidence-wrongtype | output | none | none | 未覆盖（设计边界） |
| out-evidence-huge | output | none | none | 未覆盖（设计边界） |
| out-verify-missing | output | none | none | 未覆盖（设计边界） |
| out-verify-null | output | none | none | 未覆盖（设计边界） |
| out-verify-wrongtype | output | none | none | 未覆盖（设计边界） |
| out-verify-huge | output | none | none | 未覆盖（设计边界） |
| out-canvas-missing | output | none | none | 未覆盖（设计边界） |
| out-canvas-null | output | none | none | 未覆盖（设计边界） |
| out-canvas-wrongtype | output | none | none | 未覆盖（设计边界） |
| out-canvas-huge | output | none | none | 未覆盖（设计边界） |
| out-fonts-missing | output | none | none | 未覆盖（设计边界） |
| out-fonts-null | output | none | none | 未覆盖（设计边界） |
| out-fonts-empty | output | none | none | 未覆盖（设计边界） |
| out-fonts-wrongtype | output | none | none | 未覆盖（设计边界） |
| out-fonts-huge | output | none | none | 未覆盖（设计边界） |
| out-sources-missing | output | issues-only | issue | 仅报 issue |
| out-sources-null | output | none | none | 未覆盖（设计边界） |
| out-sources-empty | output | none | none | 未覆盖（设计边界） |
| out-sources-wrongtype | output | none | none | 未覆盖（设计边界） |
| out-sources-huge | output | none | none | 未覆盖（设计边界） |
| out-uncertainty-missing | output | issues-only | issue | 仅报 issue |
| out-uncertainty-null | output | none | none | 未覆盖（设计边界） |
| out-uncertainty-wrongtype | output | none | none | 未覆盖（设计边界） |
| out-uncertainty-huge | output | none | none | 未覆盖（设计边界） |
| out-change_record-missing | output | issues-only | issue | 仅报 issue |
| out-change_record-null | output | none | none | 未覆盖（设计边界） |
| out-change_record-empty | output | none | none | 未覆盖（设计边界） |
| out-change_record-wrongtype | output | none | none | 未覆盖（设计边界） |
| out-change_record-huge | output | none | none | 未覆盖（设计边界） |
| out-execution-missing | output | none | none | 未覆盖（设计边界） |
| out-execution-null | output | none | none | 未覆盖（设计边界） |
| out-execution-wrongtype | output | none | none | 未覆盖（设计边界） |
| out-execution-huge | output | none | none | 未覆盖（设计边界） |
| out-checksum-missing | output | issues-only | issue | 仅报 issue |
| out-checksum-null | output | none | none | 未覆盖（设计边界） |
| out-checksum-wrongtype | output | none | none | 未覆盖（设计边界） |
| out-checksum-huge | output | none | none | 未覆盖（设计边界） |
| form-02-str | form | none | none | 未覆盖（设计边界） |
| form-02-list | form | none | none | 未覆盖（设计边界） |
| form-02-number | form | none | none | 未覆盖（设计边界） |
| form-02-bool | form | none | none | 未覆盖（设计边界） |
| form-02-nested | form | none | none | 未覆盖（设计边界） |
| form-03-str | form | none | none | 未覆盖（设计边界） |
| form-03-list | form | none | none | 未覆盖（设计边界） |
| form-03-number | form | none | none | 未覆盖（设计边界） |
| form-03-bool | form | none | none | 未覆盖（设计边界） |
| form-03-nested | form | none | none | 未覆盖（设计边界） |
| form-04-list | form | none | none | 未覆盖（设计边界） |
| form-04-object | form | none | none | 未覆盖（设计边界） |
| form-04-number | form | none | none | 未覆盖（设计边界） |
| form-04-bool | form | none | none | 未覆盖（设计边界） |
| form-04-nested | form | none | none | 未覆盖（设计边界） |
| nest-06 | output | none | none | 未覆盖（设计边界） |
| nest-07 | output | none | none | 未覆盖（设计边界） |
| nest-08 | output | none | gate | 缺陷 |
| nest-09 | output | none | gate | 缺陷 |
| nest-10 | output | none | gate | 缺陷 |
| nest-11 | output | none | gate | 缺陷 |
| nest-12 | output | none | none | 未覆盖（设计边界） |
| nest-13 | output | none | none | 未覆盖（设计边界） |
| nest-14 | output | none | none | 未覆盖（设计边界） |
| nest-15 | output | none | none | 未覆盖（设计边界） |

## 6. 门面内缺陷（10 条，逐条实测）

| id | 段 | 注入 | 期望信号 | 实测信号 | 门/提示（若有） |
|---|---|---|---|---|---|
| in-01 | input | entities=字符串 | none | success+recorded | — |
| in-03 | input | entities=对象 | none | success+recorded | — |
| in-04 | input | entities=0 | none | success+recorded | — |
| in-05 | input | entities=null | none | success+recorded | — |
| in-19 | input | 空对象 {} | none | success+recorded | — |
| in-22 | input | entities 元素=字符串 | none | success+recorded | — |
| nest-08 | output | verify.ok='true'（字符串真值） | gate | none | — |
| nest-09 | output | verify.ok=1（数值真值） | gate | none | — |
| nest-10 | output | verify={}（ok 缺字段） | gate | none | — |
| nest-11 | output | entities=[] 且 data_mapping=[]（空对空 + status=success） | gate | none | — |

**逐条定性**：

| 簇 | 行 | 现象 | 定性 |
|-|-|-|-|
| 输入侧结构段形态 | `in-01` `in-03` `in-04` `in-05` `in-22` | `entities` 给字符串/对象/0/null/元素为字符串 | `model.py` 的文本解构兜底把它当"没有结构化实体"处理，**在 `uncertainty` 里记了一条**（所以不是零信号），但 `status` 仍是 `success`。契约的状态表把"文本解构"列为 `partial` 条件 ⇒ **状态判定与契约不一致** |
| 输入侧空对象 | `in-19` | `case.json` 是 `{}` | 同上：走文本解构，`uncertainty` 有一条，`status=success` |
| `verify.ok` 真值 | `nest-08` `nest-09` | `verify.ok="true"` / `=1` | `check.py` 的 `G9` 读的是 **`verify_report.json`** 而不是 `result.json` 里的 `verify.ok`，所以改 `result.json` 的 `verify.ok` 无人检查（**两份记录可以互相矛盾而门不响**） |
| `verify` 段被清空 | `nest-10` | `verify={}` | 同上 |
| 空对空 | `nest-11` | `entities=[]` 且 `data_mapping=[]` 且 `status=success` | `G5` 的判据是"行数 == 实体数"，两个 0 也相等 ⇒ 通过。**"零实体"从未被任何门禁止**，而 `OUTPUT_CONTRACT.md` 的 status 表写着 `success` 需要"实体≥1" ⇒ **这一条是文档承诺与代码实现之间最硬的一处冲突** |

**为什么不在本包修**：规范要求既有脚本「尽量逐字节不变；确需修真实缺陷只允许**纯增量**并逐条点名；
CLI 参数/退出码语义不得改」。上面五簇若要修，改的是 `check.py` 的**判据**（不是纯增量），
会改变 G9/G10 的语义与退出码分布。本包的选择是：**量出来、写清楚、做成回归断言**
（`--expect-defects 10`：缺陷数一变就 `verdict=attention`）。§8 给出精确的修法与影响面，
交给维护者决定。

## 7. 计数

| 总行数 | 输入侧 | 输出侧 | 六形态 | 违约行 | 静默通过 | 门面内缺陷 | 未覆盖静默 |
|---|---|---|---|---|---|---|---|
| 164 | 22 | 106 | 36 | 141 | 96 | 10 | 86 |

读法：

- **164 行**注入里 141 行是违约注入（另 15 行是"应被容忍"的对照，如额外未知字段）；
- **96 条静默**里只有 **10 条**是门面内缺陷（6%）；
- **86 条未覆盖**全部可归因到 §0 的 9 个无检查字段 + 六形态越界，逐条在 §5 表里点名。

## 8. 如果要修，修法与影响面（本包**未改**，只给方案）

| 缺陷簇 | 最小修法（纯增量） | 影响面 |
|-|-|-|
| `entities` 非列表 ⇒ status 不应 success | `main.py` 的 `_decide_status` 增加一条：`extraction=="text-heuristic"` 且实体来自非结构化输入 ⇒ `partial` | 只改状态判定，不改 CLI；会让 6 条输入行从 `success` 变 `partial` |
| `verify.ok` 与 `verify_report.json` 不一致 | `check.py` 的 `G9` 增加"`result.json.verify.ok == verify_report.ok`"这一条 AND | 新增一条 gate 内断言；不影响 CLI |
| 零实体 | `check.py` 增加 `G0`：`entities` 非空 | **会影响合法空案例**，需先与题面确认"空案例是否允许" |
| 9 个未检查字段 | `check.py` 的 `required_fields` 补齐 18 项 | 纯增量，但会让一批历史 `result.json` 变成 `ok=false` |

## 9. 未覆盖声明（这一轴**没有**测到什么）

- 画布真实溢出（需要极大实体规模才触发 D8；本矩阵规模上限 120 实体）；
- 并发重入 / 多进程写同一 `--out`（本探针串行）；
- SVG 内部结构违约（手改 `figure.svg` 的 layer/id）—— 归 `scripts/svg_verify.py` 的 CP2/CP3，
  不在 G1–G10；
- PDF/PNG 二进制层面的契约（本矩阵只看 `result.json` 与 `check.py` 的 G1–G10）；
- 行覆盖率（本矩阵测的是**契约面**，不是代码覆盖率）；
- Linux/macOS 上的同一矩阵（本轮只在 Windows 11 + CPython 3.13.9 实测）。

## 10. 怎么把它当回归用

```bash
# 基线：本包实测 10 条门面内缺陷；数量一变就 attention
python "$SKILL_DIR/scripts/contract_matrix.py" --expect-defects 10

# 只跑某一簇（改了 check.py 之后重点看这几行）
python "$SKILL_DIR/scripts/contract_matrix.py" --section output --only nest-08 --only nest-09
python "$SKILL_DIR/scripts/contract_matrix.py" --section input  --only in-01 --only in-19

# 只要"契约面是否对齐"，不跑注入（快）
python "$SKILL_DIR/scripts/contract_matrix.py" --section form --only form-00-str
```
