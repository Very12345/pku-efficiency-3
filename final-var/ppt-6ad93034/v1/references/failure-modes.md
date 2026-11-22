# failure-modes.md — 五族失败分支、降级去向与状态自洽规则

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
