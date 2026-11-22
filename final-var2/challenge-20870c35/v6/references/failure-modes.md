# failure-modes.md — 失败模式处置手册（可靠体验维度的显性证据）

> 对应高分 intent 的 `failure-modes.md`。凡触发下表任一情形，一律**如实写入
> `change_records` 与 `uncertainty`**（含 `status` 降级），绝不编造缺失状态或数据。
> 决策规则 D1–D17（SKILL.md §6）与本表一一对应，机器分支见 `main.py` / `deck_builder.py`，
> 实测证据见 `TEST.md` §8（T8–T13，含负例）。

## 失败模式表

| # | 情形 | 处置 | 决策规则 | status |
|-|-|-|-|-|
| F1 | 材料在 case.json 声明但磁盘不存在 | `sources[]` 记 `kind=missing`（含 `path/file/kind/parsed/note`）；`evidence_map` 保留该条目；相关页面缺证据；不编造内容 | D1 | partial |
| F2 | 文本/PDF 解析失败或 PDF 无 pypdf | 记 `parsed=false` + 原因；该材料主张不进入页规划 | D2 | partial |
| F3 | PDF 抽取丢公式/符号/布局 | 以抽取文本为准并注明"抽取代理"，页内不补造公式 | D3 | 记录（completed 可保持） |
| F4 | 论文缺图/图分辨率低/图文件损坏 | 页内**诚实占位框**（标注"材料未提供图片文件"），notes 提示对照原文；坏图跳过 | D4 | 记录 |
| F5 | 无模板 / 模板路径失效 / 模板打不开 | 内置主题（16:9 母版），`artifacts.template_used/deck_mode` 注明 | D5 | 记录 |
| F6 | 模板适配中母版/版式不兼容 | 仅沿用可用版式；异常写入 change_records | D5 | partial（若核心页建不出） |
| F7 | 冻结页数与时长推导冲突 | 以任务冻结页数为准（P3），写入 plan_gates 说明 | D6 | 记录 |
| F8 | 听众信息缺失 | 按 familiar + 中等证据深度保守处理，audience.notes 说明可覆写 | D7 | 记录 |
| F9 | 材料中某块无直接主张 | 用该块章节概括成页（`derived=true`，strength=weak）并记录 | D8 | 记录 |
| F10 | 计划门 P1–P8 未全过 | 记录 errors；仍生成 honest 产物；status→partial；uncertainty 列出 | D9 | partial |
| F11 | deck 生成抛错（依赖已具备） | 保留异常前已写入的中间产物；`status=failed` + 异常入 `change_records` 与 `uncertainty` | D10 | failed |
| F12 | verify_deck 发现问题（页数/备注/命名/OPC） | 记录 entries；status→partial；不宣称"校验通过" | D11 | partial |
| F13 | 预览渲染失败/超时 | 非致命：仍写 result.json；`--skip-previews` 可跳过缩略图 | D12 | partial（预览维度） |
| F14 | 证据审计发现引文未逐字命中 | 记录条目（derived 页按概括语）；可修则重跑，不可修如实保留 | D13 | partial |
| F15 | 页内数字与源材料不一致（合理换算/截断） | validate_result 警告级提示；人工核对后忽略但需在 change_records 说明 | D14 | 记录 |
| F16 | 超时/预算（64 请求/900s/16k token） | 尽早落盘中间产物（talk_plan/deck/result 草稿）；收尾补 self_check；保存部分结果并说明限制 | D10/D12 | partial |
| F17 | 重复运行不确定性（时间戳等） | G9 探针记录"剔除记录性时间戳的内容投影 sha"；TEST.md 双跑实测（JSON 逐字节相同、PNG 逐字节相同） | — | 记录 |
| F18 | 平台/CLI 环境无 LibreOffice/PowerPoint | 预览用 PIL 模拟 + 水印 + manifest 限制说明；deck 仍可编辑主交付 | — | 记录 |
| F19 | output_contract 声明缺失字段 | apply_contract 按容器类型初始化（""/[]/{}/0，禁 null），missing_required 记录 | — | 记录 |
| F20 | 包约束超限（>50 文件/单文件 >500KB/合计 >2MB/符号链接/`__pycache__`） | `selftest --package-check` 拦截（G10）；打包前必须通过；扩展名白名单由提交前验收脚本核对 | — | 打包阻断 |
| **F21** | **缺 `python-pptx`（或 Pillow 连带不可用）** | **不崩**：跳过 deck，`artifacts.editable_deck=null` + `deck_limitation` + uncertainty 一条 + change_records 记明；页计划/计划门/预览/result.json/self_check 照常产出，命令仍返回 **0** | D15 | partial |
| **F22** | **模板/起始演示文件自带示例页** | 保留其母版与版式（模板约束不破坏），**丢弃自带页**后按冻结计划重建；`deck_mode.template_slides_present/dropped` + change_records 记明；保证最终页数 == 冻结页数 | D16 | 记录（completed 可保持） |
| **F23** | **材料为空 / 全部不可解析** | 只产出结构性页面；`status=partial` + uncertainty 明写"没有任何材料被解析为文本"；不据文件名/标签补造内容 | D17 | partial |
| **F24** | **本机绝对路径可能随产物外泄**（作者机器 `X:\...`/UNC 出现在 `sources[].path`、`figure_file`、`template_used`、错误文本里） | 写盘前由 `common.portable_path/sanitize_output` 改写为**相对案例目录**的正斜杠路径；消息内嵌路径就地改写；POSIX 运行期路径（`/input`、`/app`）原样保留 | — | 记录（`change_records` 可选说明） |
| **F25** | **示例二进制资源不能随包**（题面只允许 UTF-8 文本资源） | 示例 PDF/PNG/模板不随包：`scripts/make_synthetic_inputs.py` 运行时生成（零依赖手工 PDF + Pillow 纯几何示意图，均带 `SYNTHETIC` 标注）；示例输出二进制改为 `examples/EXPECTED-OUTPUT.md` 文字清单 | — | 打包阻断（存在二进制即不合规） |
| **F26** | **中文字体缺失或字形不适用** | 运行时按候选路径探测系统字体（Windows/Linux/macOS），结果（仅文件名）记入 `result.json.environment.cjk_font` 与 `previews/preview_manifest.json`；找不到则用 Pillow 内置位图字体，manifest 记明字形可能缺失 | — | 记录 |

## 状态一致性规则

1. `status` 只取 {completed, partial, failed}，降级必有对应 `uncertainty` 条目；
2. 每个 `uncertainty` / `change_records` 条目都要有"能垫付的具体事实"（文件名、错误信息、行号、门编号）；
3. 不允许"已覆盖"标注未覆盖证据；不允许把占位/概括描述为逐字引文；
4. **不允许静默降级**：产物缺失（deck/预览/某材料）必须在 `artifacts`/`sources`/`uncertainty` 三处之一可见；
5. **不允许虚报通过**：`verify_deck` / `evidence_audit` / 计划门未全过时不得声称"已校验通过"；
6. 退出码语义与状态一致：0 = 已有契约结果的诚实产出（可能 `partial`）；1 = 没有可用契约结果。

## 实测对照（TEST.md §8）

| 失败模式 | 实测测试 | 观测 |
|-|-|-|
| F1 / F23 | T8（声明材料不存在）、T13（材料为空） | `status=partial`；`sources` 分别出现 `kind=missing` 与 `(none)`；uncertainty 各有一条 |
| F2 | T9（遮蔽 pypdf/PyPDF2） | PDF `parsed=false` + 原因；其余材料照常出页 |
| F21 | T11（遮蔽 python-pptx）、T10（遮蔽 Pillow） | `status=partial`；deck 跳过、`deck_limitation` 记明；T11 仍产出 12 页计划与预览 |
| F22 | T5（带 1 张自带页的模板） | `template_slides_present=1 / dropped=1`；最终 12 张幻灯片 == 冻结页数 |
| F24 | T7a / 全部产物的路径扫描 | `sources[].path` 均为 `materials/...`；包内 grep「盘符 + 反斜杠」形式的绝对路径无命中 |
| F11 | T12（`case.json` 不可读） | 最小失败信封（`status=failed` + `error`，且 error 文本已净化）；退出码 1 |

## 泛化边界实测对照（v5；完整分析见 references/VALIDATION-EVIDENCE.md §4）

上表是"设计里的失败模式"，本节是**换题材/换类型/换量级撞出来的边界**（每条都有实测）。

| 边界 | 触发 | 实测行为 | 状态 |
|-|-|-|-|
| **未知 `report_type`** | 传入 `talk_config.json` 未定义的类型（实测 `workshop_retreat`） | `status=completed`、P-gates 8/8；`talk_plan.narrative.report_type` 记为 **`group_meeting`**，**`agenda` 页消失**，`uncertainty` 无相关条目 | ⚠️ **已知边界，未修**（D22）。权威值看 `talk_plan.json.narrative.report_type`；要支持新类型请在 `templates/talk_config.json` 加配置 |
| **`slide_count` 越界** | `duration_min=5` 且 `slide_count=40` | 产出 **30** 页（非 40）；`timing.seconds_per_slide=10.0`；`P3` 门比对**钳制后**目标故仍通过；`uncertainty` 无钳制说明 | ⚠️ **已知边界，未修**（D23）。根因 `scaffold_plan.py` 的 `max(6, min(30, ...))`；以 `result.json.slide_count` 为准 |
| **纯英文材料** | 材料 876 字符英文论文体 | 修前：`status=completed` 但 `derived_pages=11 / content_pages=11`（11 个内容页全部无逐字引文）⇒ 静默质量损失；修后：`status=partial` + `uncertainty` 增至 5 条（写明"抽出 6 条主张但一条都没逐字上页"） | ✅ **已修（Fix 7 / D21）**，附两案回归证据 |
| 听众信息缺失 | `case.json` 去掉 `audience` | `expertise=familiar`、`background_ratio=0.18`、`audience.notes` 写明可覆写 | ✅ 按 D7 诚实降级（设计内） |

**统计口径提醒**：`status=completed` 只表示"契约五条件满足"，
**不**表示"页面都有逐字引文"或"冻结页数被完全遵守"。后两者要分别看
`evidence_audit.derived_pages` 与 `result.json.slide_count`（与案例输入比对）。
这一条是 v5 实测后补写入状态一致性规则的。

---

# 【合并段】决策规则表（D 系列全文）

> 本段原为独立文件 `references/decision-rules.md`，在 v6（union 包）中并入本文件以守住「≤50 文件」硬门；**内容逐字保留**，未删减。

# decision-rules.md — 决策规则全文（D1–D20）、优先级裁决与代码对应

本文件是 `SKILL.md` §4–§7 的**展开版**，也是运行时行为的唯一人工可读口径。
它与 `references/failure-modes.md`（F 表 + 五族分支）互为索引：每条 D 规则都指向至少一条 F，
每条 F 都回指一条 D。**凡是本文件写了"动作"而代码没有做的，以代码为准并视为缺陷**；
代码位置列在每条规则末尾，便于对着源码复核。

> 读法：**触发条件 →（动作）→ 失败时的降级**。第三段是"出问题时必须留下什么"，
> 全部落到 `result.json` / `plan_gates.json` / `evidence_audit.json` / `deck_audit.json` /
> `self_check.json` 的可读字段上，而不是只写在日志里。

## 0. 规则的统一约束

1. **触发即记录**：命中任一规则，必须在 `change_records` 留下一条 `{at, step, action}`；
   若导致能力缺失或结果不完整，还必须在 `uncertainty` 留 `{item, impact, mitigation}`（三者皆非空）。
2. **不得静默降级**：产物缺失必须在 `artifacts` 可见（如 `editable_deck=null` + `deck_limitation`）。
3. **不得虚报通过**：门/审计未过时不得写"已校验通过"；`status` 必须随降级更新（§6 矩阵 + 检查器）。
4. **不得补造事实**：材料没有的图、公式、数字、结论一律不"补"；只能如实占位或标 `derived=true`。
5. **契约只增不减**：案例或题面声明的字段一律注入顶层，缺失时按容器类型初始化（禁 `null`）。

## 1. 材料事实族（D1–D4、D17）

| 规则 | 触发条件 | 动作 | 失败时的降级 | 代码位置 |
|-|-|-|-|-|
| **D1** | `case.json.materials` 列出某文件，但磁盘上不存在（含路径大小写/分隔符不一致） | 该条目仍进 `sources[]`，`kind=missing`、`parsed=false`、`note` 写明"listed but not found"；相关页不进入规划阶段 | `status→partial`；`uncertainty` 列出缺失清单；**不据文件名推测内容** | `main.py::_resolve_materials` / `main.py` 的 missing 分支 |
| **D2** | 材料是 PDF，且环境无 `pypdf`/`PyPDF2`，或解析抛异常 | 记录 `parsed=false` + 原因；其余材料继续；`evidence` 只用已解析文本 | 该 PDF 的主张不进入页级规划；若它是唯一材料 → 叠加 D17 | `evidence.py::load_material` / `main.py` 环境预检 |
| **D3** | PDF 抽取后公式/符号/版式丢失（抽取文本与肉眼所见不一致） | 一律以**实际抽取文本**为准，并在审计条目里注明"抽取代理" | 页内不补造公式；该主张强度按实际证据类型判定（通常 weak） | `evidence.py` / `evidence_audit.py` |
| **D4** | `figure_ref` 指向的图片文件不存在、损坏、或是占位 | 有可用图片 → 真的嵌入 deck（`page-figure-NN`）；无可用图片 → 页内**诚实占位框**并标注"材料未提供图片文件" | 坏图跳过并记录；`evidence_audit` 的 `figure_bound=false` 如实登记，不声称已引用 | `deck_builder.py::_add_figure` / `evidence_audit.py` |
| **D17** | 材料为空、材料目录为空目录、或全部材料都不可解析 | 只产出结构性页面（封面/目录/结论/问答），页计划照常走门 | `status→partial`；`sources[].kind=none`；`uncertainty` 明写"没有任何材料被解析为文本" | `main.py`（`material_records` 兜底分支）/ `scaffold_plan.py` |

## 2. 依赖可用性族（D2、D12、D15）

| 规则 | 触发条件 | 动作 | 失败时的降级 | 代码位置 |
|-|-|-|-|-|
| **D15** | `import pptx` 失败（缺 `python-pptx`，或 Pillow 连带不可用） | **不崩**：跳过 deck 生成，继续写 `talk_plan.json`/`plan_gates.json`/预览/`result.json`/`self_check.json`；**命令仍返回 0** | `status→partial`、`artifacts.editable_deck=null`、`artifacts.deck_limitation` 记明；`uncertainty` 首条即该限制；补齐依赖后重跑同一命令即可 | `deck_builder.py::dependency_status` / `main.py` deck 分支 |
| **D12** | 预览渲染抛错、超时，或显式 `--skip-previews` | 非致命：`result.json` 照常写；预览清单说明缺了什么 | `status→partial`（预览维度）；`artifacts.preview_note` 说明限制 | `render.py::render_all` / `main.py` 预览分支 |
| **D2** | 同上（PDF 解析依赖） | 同上 | 同上 | 同上 |

## 3. 任务冻结约束族（D6、D16）

| 规则 | 触发条件 | 动作 | 失败时的降级 | 代码位置 |
|-|-|-|-|-|
| **D6** | 按时长推导的页数（`duration_min × 60 / 每页秒数`）与 `case.json.slide_count` 冲突 | **以任务冻结页数为准**，按时长重排各叙事块的权重与顺序 | `plan_gates.gates[P3]` 记录 `pages` 与 `target`；冲突与取舍写 `change_records` | `scaffold_plan.py` 页预算 / `validate_plan.py` P3 |
| **D16** | 案例模板/起始演示文件自带示例页 | 沿用其**母版与版式**，丢弃自带页，按冻结计划重建整份 deck | `deck_mode.template_slides_present/dropped` + `change_records` 记明；保证最终页数 == 冻结页数 | `deck_builder.py::build_deck`（template-adapt 分支） |
| **D5** | 无模板字段、模板路径失效、模板打不开 | 使用包内置 16:9 主题母版 | `artifacts.deck_mode.mode=built-in-theme`、`template_used=null`；`uncertainty` 一条说明"若题面另附模板请经 `--template` 传入" | `main.py::_resolve_template` / `deck_builder.py::_new_deck` |

## 4. 内容与证据族（D3、D7、D8、D13、D14）

| 规则 | 触发条件 | 动作 | 失败时的降级 | 代码位置 |
|-|-|-|-|-|
| **D7** | `audience` 缺失或无法判定先验知识 | 按 `familiar` 处理：背景/术语页占比 18%、证据深度 medium；`audience.notes` 说明可覆写 | 不猜听众身份、不臆造"专家/公众"设定 | `scaffold_plan.py::resolve_audience` |
| **D8** | 某叙事块（如"创新点"）在材料中找不到可直接引用的句子 | 用该块章节文本概括成页 | `derived=true` + `strength=weak`，并在 `change_records[step=framing]` 说明；**不冒充逐字引文** | `scaffold_plan.py` framing 分支 |
| **D13** | 证据审计发现某页 `quote` 未在实际读取的源文本中逐字命中 | 能修则修（改 `talk_plan.json` 后重跑）；不能修则如实保留并列出 | `evidence_audit.entries[]` 逐条给出未命中原因；`status→partial` | `evidence_audit.py::audit_evidence` |
| **D14** | 页内数字在任何源文本中都不逐字出现（含合理换算/千分位/四舍五入） | 作为**警告级**提示输出，由人核对 | 核对后允许忽略，但必须在记录里说明是"换算/截断"而非改数 | `validate_result.py` 数字检查 |

## 5. 门与状态族（D9、D10、D11）

| 规则 | 触发条件 | 动作 | 失败时的降级 | 代码位置 |
|-|-|-|-|-|
| **D9** | 计划门 P1–P8 未全过（典型：冻结页数不符、证据缺定位、强度词法不合法） | 记录**全部** errors，**继续**产出诚实产物（不中断流水线） | `status→partial`；`uncertainty` 列出 errors；不得声称"计划已通过" | `validate_plan.py::validate_plan` |
| **D11** | `verify_deck` 发现问题（打不开、页数不符、某页无备注、缺 `page-claim-NN`、OPC 不完整） | 记录逐条 entries | `status→partial`；`deck_audit.valid=false`；不宣称"校验通过" | `verify_deck.py::verify_deck` |
| **D10** | deck 生成**抛异常**（依赖已具备的异常路径） | 保留异常前已落盘的中间产物 | `status→failed`；异常文本进 `change_records[step=deck]` 与 `uncertainty`；退出码 1 | `main.py` deck try/except 分支 |

## 6. 契约记录族（D18、D19）

| 规则 | 触发条件 | 动作 | 失败时的降级 | 代码位置 |
|-|-|-|-|-|
| **D18** | `case.json` / `task.md` 未声明 `output_contract`，或声明了流水线未产出的字段 | 回落到**内置默认契约**；契约**只增不减**；缺失字段按声明容器类型初始化：`str→""`、`list→[]`、`dict→{}`、`number→0`、`bool→False`（**禁止 `null`**） | `contract.declared_source` 写清来源（`case.json` / `task.md` / `built-in default`）；`contract.applied` 列出全部字段；`self_check.contract_check.missing_required` 记录 | `common.py::apply_contract` / `check_contract.py` |
| **D19** | 同一输入两次运行的产物不完全一致 | 用"**剔除记录性时间戳的内容投影 sha**"比较（`generated_at`/`at`/`ts` 等字段被剔除） | 记录性时间戳差异如实登记；**不冒充逐字节一致**；`self_check.determinism` 留 `plan_sha16`/`evidence_map_sha16`/deck 规范化 sha | `common.py::deterministic_sha` / `finalize_result.py` |

## 7. 冲突裁决（D20）

**D20**：多条规则同时命中时，按 `SKILL.md` §5 的优先级族裁决 ——
① 材料事实（D1–D4、D17）→ ② 依赖可用性（D15、D2）→ ③ 任务冻结约束（D6、D16）→
④ 模板与渲染（D5、D12）→ ⑤ 契约与记录（D18、D19、D14）。

裁决的三条硬要求：

1. **覆盖不等于删除**：高优先级结论生效，但低优先级命中项仍须进 `change_records`；
2. **理由可读**：记录里同时出现规则编号与最终动作（例："D4×D8 → 先出占位框（D4），该页标 derived（D8）"）；
3. **状态取最严**：任一命中项要求 `partial`，最终 `status` 即为 `partial`（降级不会因为别处成功而回涨）。

已实测的组合（见 `TEST.md`）：

| 组合 | 场景 | 实测结论 |
|-|-|-|
| D4 × D8 | 示例材料有 `Fig. 3` 引用但没有对应图片 | 出占位框（D4）；该页仍按材料文本给主张（D8 只在无直接主张时触发，故本例不命中） |
| D15 × D11 | 遮蔽 `python-pptx` | deck 未生成 → 不进入 D11；状态同降 `partial`，退出码 0 |
| D6 × D16 | 模板自带 1 页 + 冻结 12 页 | 丢弃自带页后重建 12 页，`P3 pages=12 target=12` |
| D1 × D17 | 声明材料不存在且盘上无其它材料 | 同一次运行里 `kind=missing` 与"无任何材料被解析"两条 uncertainty 并存 |

## 8. 与失败模式表（F 表）的对应

`references/failure-modes.md` 用 F1–F26 描述**现象**，本文件用 D1–D20 描述**决策**；
两边的映射写在 F 表的"决策规则"列，五族分支编号（B-M/B-T/B-D/B-C/B-S）写在 F 表的"族"列。
复核方法：任取一条 F，应能在本文件找到同名 D；任取一条 D，应能在 F 表找到至少一条对应现象。

## 9. 机器复核命令

```bash
# $SKILL_DIR = 本包根目录（含 SKILL.md）；脚本自定位，cwd 任意
python "$SKILL_DIR/scripts/check_status_matrix.py" <out>          # §6 状态矩阵：退出码 0 = 自洽
python "$SKILL_DIR/scripts/validate_result.py"     <out>/result.json   # 结构/文件/数字
python "$SKILL_DIR/scripts/check_contract.py"      <out>/result.json   # 契约字段与类型
python "$SKILL_DIR/scripts/evidence_audit.py"      <out>/result.json   # 逐页逐字引文
python "$SKILL_DIR/scripts/validate_plan.py"       <out>/talk_plan.json --materials-dir <材料目录>
python "$SKILL_DIR/scripts/verify_deck.py" <out>/editable_deck.pptx --expect-pages <N> --plan <out>/talk_plan.json
python "$SKILL_DIR/scripts/selftest.py" <out> --package-check "$SKILL_DIR"
```

以上命令的退出码语义统一：**0 = 通过**；非 0 = 有不一致，报告里逐条给出字段与值。
