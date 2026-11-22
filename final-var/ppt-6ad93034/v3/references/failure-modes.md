# failure-modes.md — 失败模式、降级策略、状态一致性（按"机制受损"组织）

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
