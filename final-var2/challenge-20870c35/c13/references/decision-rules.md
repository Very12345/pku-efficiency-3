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
