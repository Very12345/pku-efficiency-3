# failure-modes.md — 失败模式、降级策略与状态一致性

本文件是 `SKILL.md` §5 决策规则 D1–D12 的**按失败类展开版**：每一类都给出
**识别信号 → 处置动作 → 记录位置 → 用户可见后果**，以及脚本的**退出码语义**。
原则只有一条：**宁可如实降级并留痕，也不假装成功**。

## 0. 退出码语义（脚本可被编排器直接判读）

| 脚本 | 0 | 1 | 2 |
|-|-|-|-|
| `scripts/main.py` | `status=success`（产物齐备、G1–G8 通过、自检 all_pass） | `status=partial`（有降级/未核验项，已逐条记入 `uncertainty`） | 输入不可读（case 解析失败 / 材料读取失败），已写最小 `status=failed` result.json |
| `scripts/result_tool.py` | G1–G8 全过（`{"valid": true}`） | 有条目未过（`errors` 非空） | `result.json` 无法解析 |
| `scripts/selftest.py` | 全部自检项通过（`all_pass: true`） | 有未通过项（逐项列在 `checks[]`） | 输入不可读 |
| `scripts/evidence_check.py` | 主张里**每个数字**都能在材料中定位 | 有数字找不到（打印 `missing=[…]`） | — |

编排器判读约定：**只有 exit 0 才算这次运行"干净"**；exit 1 必须读
`result.json.uncertainty` 再决定是否补件重跑；exit 2 表示输入侧问题，重跑无用。

## 1. 材料类异常

| 失败模式 | 识别信号 | 处置 | 记录 |
|-|-|-|-|
| 材料文件不存在 / 为空 | `material_status=missing`；`material_warnings` 非空 | **不补造、不编 deck**：只产出元信息 result（`deck.slide_count=0`），状态降 `partial`（D1） | `evidence.material_warnings` + `uncertainty` |
| 部分材料缺失（案例给了 3 份只读到 2 份） | `material_status=partial` | 用已读到的材料继续，但把缺的那份显式标出，页面上不得出现只有它才有的数字 | `evidence.material_warnings` |
| 材料是扫描件 / 无文本层 PDF | 抽取文本为空或近空 | 不 OCR 冒充；由 Agent 用自身读图/读文能力抽成 `<work>/materials/*.txt` 后重跑，仍不行则 `partial`（D3） | `uncertainty` + `sources[].tool` |
| 环境无 PDF 抽取库（fitz/pypdf/pdfplumber 全缺） | 抽取阶段抛错 | 同上走 D3；不要静默把 PDF 当空文件 | `uncertainty` |
| 材料正文里的数字与页面主张不一致 | `check_claim_numbers` 返回 `missing` 非空 | 该主张 `verified=false` 进 `unverified_claims`，**不回填、不取整、不按印象改**（D2） | `evidence.unverified_claims` |
| 数据表缺列 / 非数值列 | 图表绑定阶段判定 | 降级为 PPTX 原生可编辑表格（仍可逐格改），保留引用（D9） | `deck.slides[].figure.note` + `uncertainty` |

**判读提醒**：`material_warnings`（材料问题）、`uncertainty`（无法核验/降级）、
`status`（整体成败）三者语义不同，**必须分开记录**，不得互相顶替。

## 2. 模板类异常

| 失败模式 | 识别信号 | 处置 | 记录 |
|-|-|-|-|
| `spec.template_pptx` 打不开 / 损坏 | `Presentation()` 抛错 | 备份原文件 → 回退内置 `templates/default.json`，说明降级（D6） | `uncertainty` + `change_records` |
| 模板版式/占位符不足（放不下 N 页） | 母版版式枚举不足 | 复用最接近的版式并新增文本框，**绝不改动母版**；仍不够则减少正文要点而不是缩字号到 <12pt | `change_records` |
| `spec.starting_deck` 起始稿需要适配 | 起始稿存在 | 先备份到 `<out>/work/original_inputs/`，再按计划重排页面；每处改动记一条 | `change_records` |
| 页数超限（`max_slides` 小于必需页数） | `plan_lint` 报 `pages=N > max_slides`（D7） | 按 `max_slides` 确定性压缩角色分配；**不静默丢证据页**，把降级说明写进备注 | `run_meta.spec_lint` + `change_records` |
| 无模板但要求特定配色/页脚 | `spec.style` 缺失键 | 用 `templates/default.json` 的默认值，模板是数据不是代码（改 JSON 即可，不逐页手改） | `change_records` |

## 3. 依赖缺失类异常

| 依赖 | 缺失时的行为 | 记录 |
|-|-|-|
| `python-pptx` | **致命**：无法建稿 → `main.py` 走 partial/failed 分支，如实说明缺什么 | `uncertainty` + `status` |
| `matplotlib` | 结果页降级为 PPTX 原生可编辑表格（`figure.kind=table`） | `figure.note` + `uncertainty` |
| `Pillow` | 预览 PNG 不产出 → G5 报错、自检 `previews` 不通过 | `previews.warnings` + `uncertainty` |
| `reportlab` | 跳过 PDF 预览（`previews.pdf=""`），PNG 不受影响（G5 仅 warning） | `previews.warnings` |
| CJK 字体（预览用） | 预览出现方块但 **PPTX 不受影响**；PPTX 只记字体名由打开端替换 | `previews.warnings`（`render_qa` 的 `cjk_font_available` 检查） |
| 字体探测不到的兜底 | 回落 PIL 默认字体并预警；**不下载、不内嵌字体文件**（包内不允许二进制资源） | `uncertainty` |

## 4. 契约四形态（`output_contract` 回显）

`case.json` 的 `output_contract` 声明"必须镜像到 `result.json` 顶层"的字段。
**任何已声明字段都禁止 `null`**，按声明类型给空值：

| 声明类型 | 空值 | 有真实值时 |
|-|-|-|
| `string` / `str` | `""` | 真实字符串 |
| `list` / `array` | `[]` | 真实列表 |
| `dict` / `object` | `{}` | 真实对象 |
| `bool` / `boolean` | `false` | `true` / `false` |
| `int` / `float` / `number` | `0` | 真实数值 |
| 未声明类型（裸值） | 按运行时值的类型给同型空值 | — |

实现：`scripts/result_tool.py::apply_output_contract`；校验：G2
（字段齐全 + 非 null）与 G8（`templates/result_envelope.json` 类型合规）。
`--case` 必须传给 `result_tool.py`，否则无法做契约回显核对 —— **漏传
`--case` 会让"契约全回显"看起来失败**，这是最容易误判的一处。

## 5. 状态一致性（success / partial / failed 的自洽规则）

| 状态 | 允许出现 | 禁止出现 |
|-|-|-|
| `success` | `uncertainty` 可为空；`checks.all_pass=true`；G 门通过；`unverified_claims` 为空 | 有未核验主张却标 success；有降级却没写原因 |
| `partial` | 核心产物（PPTX）可用但至少一项降级（图表降级/PDF 缺失/CP2 lint 偏差/编辑未应用/有未核验主张） | **每条降级原因都必须在 `uncertainty` 里有对应条目**（一一对应，缺一即不自洽） |
| `failed` | 只写最小 result.json 说明原因 | 不产出任何 deck 却标 success；把预览冒充 Office 导出件 |

自检与门的关系：`selftest.py` 查"产物在不在、能不能开、页数对不对"，
`result_tool.py` 查"契约合不合规"；**两者都过也不等于内容正确**——内容正确性
由 `evidence_check` 的数字核验与 `plan_lint` 的页面纪律负责，三层不能互相顶替。

## 6. 编辑链路（`--edit`）异常

| 失败模式 | 识别信号 | 处置 | 记录 |
|-|-|-|-|
| 未知 `op` | `apply_edits` 不认识 | 跳过该条，其余 ops 照常应用（D11） | `uncertainty` + `changelog` skipped |
| 页码不存在 / 下标越界 | 页码或 `bullet_index` 越界 | 同上，不改动目标页 | 同上 |
| `reorder_pages` 不是完整置换 | 页序数组不是 1..N 的置换 | 拒绝该条（避免"静默丢页"） | 同上 |
| 编辑引入的新数字材料中没有 | 编辑后重跑 `check_claim_numbers` 未命中 | 该主张 `verified=false`，**不因"是用户让改的"就放行** | `unverified_claims` |
| 改坏要回退 | — | 复制上一版 `work/deck_<v>.pptx` 重跑，并写一条回退 change_record | `change_records` |

## 7. 资源形态类异常（本包特有，务必遵守）

| 失败模式 | 处置 |
|-|-|
| 包内混入二进制资源（`.pptx/.png/.pdf/.svg/.jsonl` 等） | 平台预检会直接拒绝整包（`unsupported Skill resource`）。**本包不携带任何二进制**；模板由 `templates/*.json` 参数化，图表/预览由运行时生成 |
| 文件数超上限（>50） | 保持 20–40 个文件的精简形态；新增能力优先并入既有文档，而不是新增文件 |
| 包内出现本机绝对路径 | 示例产物由 `scripts/make_examples.py` 生成并自动净化；字体探测候选路径（跨平台回路）除外，且不得写入示例 JSON |
| 运行前忘了 `--case` 就判"契约没回显" | 见 §4 末段：先确认参数齐全再下结论 |

## 8. 排查顺序（复跑失败时按此走）

1. 读 `result.json.environment`（实测库版本）→ 依赖是否缺失（§3）；
2. 读 `evidence.material_warnings`（材料路径/缺失，§1）；
3. 读 `run_meta.checkpoints`（哪一门没过：cp1_extract / cp2_plan / cp3_build / cp4_verify）；
4. 读 `run_meta.spec_lint.problems`（页面纪律偏差，§2）；
5. 读 `run_meta.gate.errors` 与 `uncertainty`（契约门与降级原因，§4/§5）；
6. 读 `logs/run_*.log` 末行 `STATUS=…` 与上面的 `figure:` / `edit applied:` 行。

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

## 10. 状态规则在跨题材下的实际含义

| 状态 | 在跨题材场景下的含义 | 实测例子 |
|-|-|-|
| `success` | 材料齐全、无未核验主张、G 门与自检全过、`plan_lint` 通过 | 示例案例；探针 P3（压缩到 3 页且无缺口） |
| `partial` | **有据可查的降级**：缺小节写占位主张、`plan_lint` 偏差、预览降级 | 案例 A/B、探针 P1/P2/P4 |
| `failed` | 输入不可读，只写最小 result | 材料全缺（`TEST.md` §T7a 是 partial，`case.json` 不可读才是 failed） |

**关键口径**：跨题材时 `partial` **不是缺陷**，而是"材料本身有缺口"的诚实反映。
把它当成失败去追 `success`，只会诱导实现把缺口藏起来——那才是真正的失败。
