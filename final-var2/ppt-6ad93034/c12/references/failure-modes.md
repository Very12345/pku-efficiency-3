# failure-modes.md — 失败模式、降级策略、状态一致性与"增益被侵蚀"的判定

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
