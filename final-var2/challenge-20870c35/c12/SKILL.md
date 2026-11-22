---
name: academic-talk-organizer
description: >
  组织学术汇报内容（学术 PPT 页面组织）：从论文/研究材料到可讲、可编辑、证据可追溯的演示文件。
  当输入包含科研论文材料、研究报告、组会/答辩/评审任务、听众与时长、页数与模板约束、讲稿或备注需求，
  关键词如 学术汇报、答辩PPT、组会汇报、slides、deck、页码规划、讲稿、备注、问答准备、听众适配、
  叙事顺序、汇报内容组织、evidence mapping、模板适配、plan contract、quality gates 时使用本 Skill：
  读真实材料 → 抽取研究问题/方法/结果/局限 → 生成页级计划（scaffold_plan）并经计划契约门
  P1–P8（validate_plan + assets/plan.schema.json）校验 → python-pptx 生成可编辑 .pptx
  （模板适配或内置主题；确定性元素命名 + 讲稿/备注 + 图占位）→ verify_deck 校验
  → PIL 渲染 PNG 预览 → evidence_audit 逐字审计 → finalize_result 写含证据映射、来源、
  不确定性、审计链路的 result.json。严格以真实文件为准，不臆造数据，不提交预制答案；
  二进制示例输入（PDF/PNG）由 make_synthetic_inputs.py 在运行时生成，包内只含 UTF-8 文本资源。
---

# 学术汇报内容组织（academic-talk-organizer）v2 · 合规重打包版 · 整合版（决策层 + 增益层）

> 本包整合了基线 Skill 与 2 个强化层,各层对应不同的评分维度:可靠体验 10 + 实际效果 40 · 使用增益 25。
> 各层内容**不重复**:决策层给规则与失败分支;增益层给对照协议与指标口径;机制层给机制说明与可复用资产。
> 建议使用顺序:先用「决策层」跑通并处理异常,再用「增益层」证明并度量改善,最后用「机制层」复用与扩展。
> 各层的原始文件都完整保留在本包内,不是摘要 —— 下面每一层都是可以独立执行的完整规范。

## 本包文件索引

- `COMPARE.md`
- `GITHUB_URL.txt`
- `README.md`
- `TEST.md`
- `assets/plan.schema.json`
- `assets/result.template.json`
- `examples/EXPECTED-OUTPUT.md`
- `examples/README.md`
- `examples/case.json`
- `examples/task.md`
- `references/GAIN-PROTOCOL.md`
- `references/OUTPUT_CONTRACT.md`
- `references/RUBRIC_MAP.md`
- `references/decision-rules.md`
- `references/deck-rules.md`
- `references/evidence-audit.md`
- `references/failure-modes.md`
- `references/gain-run-record.json`
- `references/plan-contract.md`
- `references/quality-gates.md`
- `scripts/check_contract.py`
- `scripts/check_status_matrix.py`
- `scripts/common.py`
- `scripts/deck_builder.py`
- `scripts/evidence.py`
- `scripts/evidence_audit.py`
- `scripts/finalize_result.py`
- `scripts/gain_ab.py`
- `scripts/main.py`
- `scripts/make_synthetic_inputs.py`
- `scripts/render.py`
- `scripts/scaffold_plan.py`
- `scripts/selftest.py`
- `scripts/validate_plan.py`
- `scripts/validate_result.py`
- `scripts/verify_deck.py`
- `templates/narrative_template.md`
- `templates/slide-checklist-template.md`
- `templates/talk_config.json`
- `examples/materials/figures.md`
- `examples/materials/paper_extract.md`
- `examples/output/result.example.json`
- `examples/output/self_check.example.json`

---

# 【决策层】决策规则与失败分支（目标维度:可靠体验 10 + 实际效果 40）

---
name: academic-talk-organizer
description: >
  把已有科研材料组织成可讲、可编辑、证据可追溯的学术汇报（学术 PPT 页面组织）。
  适用输入：论文/研究报告/组会材料 + 听众、时长、页数、模板约束、讲稿或备注需求；
  关键词：学术汇报、答辩PPT、组会汇报、slides、deck、页码规划、讲稿、备注、问答准备、
  听众适配、叙事顺序、证据定位、evidence mapping、模板适配、plan contract、降级处置。
  本 Skill 以**决策规则**运行：每条规则写明触发条件 → 动作 → 失败时的降级与落点字段，
  执行顺序 CP1–CP5 的每个检查点都有进入/出口条件与失败分支编号（B-M/B-T/B-D/B-C/B-S），
  状态判定按 §6 状态矩阵执行（completed / partial / failed 与退出码 0/1/2 一一对应），
  并提供 scripts/check_status_matrix.py 把"状态与文件内容是否自相矛盾"变成机器判定。
---

## 学术汇报内容组织 · v1 决策显性化版（academic-talk-organizer）

面向「玻尔产品周赛 · 学术效率 · 第三期」challenge-20870c35（slides 组）。

本版只做一件事：把"遇到什么情况该怎么办"从散文变成**可执行、可对照、可机器复核的规则**。
算法、脚本入口与 CLI 参数与本包其它版本一致，新增的是**决策层**：规则表、分支表、状态矩阵、
以及一个把状态一致性变成退出码的检查器。

**边界**：本 Skill 只做"从已有内容材料到可讲页面"的组织与交付；不做论文精读成稿、学术写作成稿、
科研绘图素材生产（相邻课题负责）。页面内容一律取自源材料逐字引文，不改写事实、不补造数据。

### 0. 三十秒速览

```bash
SKILL_DIR="<本包根目录>"        # 平台安装后即 /skills/weekly-skill
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md --out /app/output
python "$SKILL_DIR/scripts/check_status_matrix.py" /app/output     # 状态与内容自洽？（退出码 0）
```

| 你会得到 | 你要看哪里 |
|-|-|
| 一份可编辑演示文件 + 逐页讲稿备注 | `editable_deck.pptx`（运行期产物） |
| 唯一评分产物 | `result.json`（契约字段 + 三道审计内嵌） |
| 计划是否守约 | `plan_gates.json` / `result.audit.plan_gates`（P1–P8） |
| 每页话能不能落回原文 | `evidence_audit.json` / `result.audit.evidence` |
| deck 是否真的可打开、页数是否守约 | `deck_audit.json` / `result.audit.deck` |
| **状态是否自相矛盾** | `check_status_matrix.py` 的退出码与逐条规则表 |

退出码：**0** = 已产出通过 validate + contract 的 `result.json`（`status` 字段说明是 `completed`
还是 `partial`——诚实降级不会被当成崩溃）；**1** = 没有可用的契约结果；**2** = 参数用法错误。

### 1. 触发判据（什么时候用、什么时候不要用）

| 判据 | 用本 Skill | 不要用 |
|-|-|-|
| 输入是**已有**材料（论文/报告/图表清单/数据卡片） | ✅ | 输入只有一句主题、没有任何源材料 → 先要材料 |
| 需要**页级组织**（哪页讲什么、按什么顺序、每页留哪句话） | ✅ | 只要"把论文全文翻译/润色/摘要" → 相邻课题 |
| 有听众/时长/页数/模板任一约束 | ✅ | 无任何约束且只要一个粗略大纲 → 直接对话更快 |
| 需要**证据可追溯**（每页能对回原文位置） | ✅ | 允许自由发挥、不需要溯源 → 本 Skill 的强约束会显得啰嗦 |
| 需要可编辑交付 + 讲稿/问答准备 | ✅ | 只要图片/海报/科研绘图 → 相邻课题 |

判定口径：上述"✅ 列"命中任意两条即触发；命中"不要用"任意一条则不触发。触发后一律走 §3 的顺序。

### 2. 输入、输出与它保证什么

**输入**：`/input/case.json`（`case_id`/`title`/`report_goal`/`audience`/`duration_min`/`slide_count`/
`report_type`/`materials`/`template`·`start_deck`/`figure_files`/`output_contract`）+ `/input/task.md`
+ 材料目录（`.md/.txt/.pdf` 与图片）。**必须实际读取文件内容**；不得按文件名或标签假设内容。

**输出**（`--out`，平台运行期即 `/app/output`）：

```
result.json          # 唯一评分产物：契约字段 + 主结果 + 证据定位 + status/sources/uncertainty/
                     #   change_records/environment + audit{plan_gates,evidence,deck,gates}
talk_plan.json       # 页级计划（可编辑中间产物；改它再重跑可复核取舍）
plan_gates.json      # 计划契约门 P1–P8（assets/plan.schema.json 驱动）
evidence_map.json    # 源文件 → {用到它的页, 图表引用} 反向映射
evidence_audit.json  # 逐页逐字引文核验（derived/占位/数字对源说明）
deck_audit.json      # deck 机器校验（打开/页数/备注/claim 元素/OPC/规范化 sha）
editable_deck.pptx   # 可编辑演示文件（运行期产物，二进制不进提交资源）
previews/            # 封面/逐页/网格 PNG + preview_manifest.json（PIL 模拟，如实标注）
self_check.json      # validate + contract + 门快照 + 确定性探针 + 状态矩阵快照
```

三条不变量：① `result.json` 里的路径**可移植**（本机绝对路径写盘前改写为相对案例目录的形式，
POSIX 运行期路径原样保留）；② 契约字段**只增不减**、回调值为 `""/[]/{}/0` 而**不是 `null`**；
③ `status` 必须与文件内容自洽（由 §6 矩阵 + `check_status_matrix.py` 判定）。

### 3. 执行顺序（CP1–CP5：每步都有进入条件、出口条件、失败分支）

> **自定位**：`$SKILL_DIR` = 含 `SKILL.md` 的目录。所有脚本用 `os.path.dirname(__file__)` 自定位，
> **命令与当前 cwd 无关**；Linux 容器里 `SKILL_DIR=/skills/weekly-skill`。

| 检查点 | 进入条件 | 动作 | 出口条件（不满足 → 分支） |
|-|-|-|-|
| **CP1 输入契约** | `case.json` 可读 | 读 case/task；解析材料清单（显式 + 自动发现）；解析模板；环境预检（`python-pptx`/`Pillow`/`pypdf`/中文字体） | 材料清单与实际文件对齐（缺 → **B-M1**）；模板可用或明确标记（缺 → **B-T1**）；依赖状态写进 `environment`（缺 → **B-D1**） |
| **CP2 计划门** | CP1 完成 | `scaffold_plan.build_plan` 生成页计划 → `validate_plan` 执行 P1–P8 → 写 `talk_plan.json`/`plan_gates.json` | `plan_gates.valid == true`（否则 → **B-S1**，继续产出诚实产物而非中断） |
| **CP3 生成门** | CP2 完成 | `deck_builder` 生成/适配 `.pptx`（模板适配沿用母版版式；图绑定或诚实占位）→ `verify_deck` | `deck_audit.valid == true`（否则 → **B-S1**）；缺依赖 → **B-D1** |
| **CP4 渲染门** | CP3 完成或已降级 | PIL 预览（封面/逐页/网格 + manifest） | 预览落盘（失败 → **B-D2**，非致命） |
| **CP5 审计收口** | CP4 完成 | `evidence_audit` 逐字审计 → `finalize_result` 组装 `result.json` + `self_check.json` → `check_status_matrix` 自洽复核 | 契约齐全 + 结构有效 + 状态自洽（不满足 → **B-C1/B-S2**） |

**手工精修路径**：改 `talk_plan.json`（页级取舍）或 `templates/talk_config.json`（页权重/顺序/问答模板）
后重跑同一条命令即可；重跑会重新 scaffold，若要锁定请改配置文件而不是只改中间产物。

### 4. 决策规则表 D1–D20

> 每条固定三段：**触发条件 → 动作 → 失败时的降级**。第三段末的 `〔落点〕` 是必须出现该事实的字段，
> 供机器复核；触发即必须记录，**不允许静默处理**。

| # | 触发条件 | 动作 | 失败时的降级 〔落点〕 |
|-|-|-|-|
| D1 | `case.json` 声明了材料，文件不在盘 | 仍保留在 `sources[]`，标 `kind=missing`；相关页不进入规划 | `status→partial`；不据文件名编造内容 〔`sources[].kind/note`〕 |
| D2 | PDF 无 `pypdf`/`PyPDF2` 或解析抛错 | 记录 `parsed=false` + 原因；其余材料照常出页 | 该材料主张不进入页规划 〔`sources[].parsed/note` + `uncertainty`〕 |
| D3 | PDF 抽取丢公式/符号/版式 | 以**实际抽取文本**为准，注明抽取代理方式 | 页内不补造公式；相关主张强度降级 〔`evidence_audit.entries[].notes`〕 |
| D4 | 材料缺图 / 图分辨率低 / 图文件损坏 | 有图则绑定嵌入；无图则页内**诚实占位框**并注明 | 跳过坏图，不声称已引用 〔`pages[].figure_file` + `evidence_audit.figure_bound`〕 |
| D5 | 无模板 / 模板路径失效 / 模板打不开 | 改用包内置主题母版（16:9） | 记录实际模式，不谎称套用了模板 〔`artifacts.deck_mode/template_used`〕 |
| D6 | 时长推导页数与任务冻结页数冲突 | **以任务冻结页数为准**，按时长重排块权重 | 记录冲突与取舍理由 〔`plan_gates.gates[P3]` + `summary.pages_total`〕 |
| D7 | 听众信息缺失 | 按 `familiar` + 中等证据深度保守处理 | 注明可覆写，不猜听众身份 〔`audience.expertise/notes`〕 |
| D8 | 某叙事块在材料中无直接主张 | 用该块章节文本概括成页 | `derived=true` + `strength=weak`，不冒充逐字引文 〔`pages[].derived/strength`〕 |
| D9 | 计划门 P1–P8 未全过 | 记录全部 errors，**继续**产出诚实产物 | `status→partial`；不得声称"计划已通过" 〔`plan_gates.errors` + `uncertainty`〕 |
| D10 | deck 生成抛错（依赖已具备） | 保留异常前已落盘的中间产物 | `status→failed` + 异常入记录 〔`change_records[step=deck]` + `uncertainty`〕 |
| D11 | `verify_deck` 发现问题（页数/备注/命名/OPC） | 记录 entries | `status→partial`；不宣称"校验通过" 〔`deck_audit.errors`〕 |
| D12 | 预览渲染失败/超时 | 仍写 `result.json`；`--skip-previews` 可只留封面+网格 | `status→partial`（预览维度） 〔`artifacts.preview_note`〕 |
| D13 | 证据审计发现引文未逐字命中 | 能修则修（改 `talk_plan.json` 重跑），不能修如实保留 | 逐条列出，不把概括说成逐字 〔`evidence_audit.entries[]` + `uncertainty`〕 |
| D14 | 页内数字不在任何源文本中逐字出现 | 提示为**警告级**（合理换算/截断可接受） | 人工核对后忽略也必须在记录里说明 〔`validate_result` warnings〕 |
| D15 | 缺 `python-pptx`（或 Pillow 连带不可用） | **不崩**：跳过 deck，其余产物照常；命令仍返回 0 | `status→partial` + `artifacts.editable_deck=null` + `deck_limitation` 〔`uncertainty` 首条〕 |
| D16 | 模板/起始演示自带示例页 | 沿用其母版与版式，**丢弃自带页**后按冻结计划重建 | 记录丢弃数量，保证最终页数 == 冻结页数 〔`deck_mode.template_slides_present/dropped`〕 |
| D17 | 材料为空 / 全部不可解析 | 只产出结构性页面 | `status→partial`；明写"没有任何材料被解析为文本" 〔`sources[].kind=none` + `uncertainty`〕 |
| D18 | 案例/task.md 未声明 `output_contract` | 回落到内置默认契约，并把来源写清楚 | 契约**只增不减**；缺失字段按容器类型初始化 〔`contract.declared_source/applied`〕 |
| D19 | 同输入两次运行产物不完全一致 | 用"剔除记录性时间戳的内容投影 sha"比较 | 记录性时间戳差异如实登记，不冒充逐字节一致 〔`self_check.determinism`〕 |
| D20 | **多条规则同时命中** | 按 §5 优先级裁决；**全部**命中项都要记录 | 高优先级规则的降级结论覆盖低优先级，但低优先级的记录不得删除 〔`change_records` 全量〕 |

### 5. 决策冲突的优先级（D20 的裁决表）

同时命中多条时，按下列顺序裁决，**前者覆盖后者**；被覆盖的规则不消失，仍进 `change_records`：

| 序 | 优先级族 | 为什么在前 | 典型组合 |
|-|-|-|-|
| 1 | **材料事实**（D1–D4、D17） | 事实层不可协商：材料没有的东西不能上页 | D4（缺图） × D8（无直接主张）→ 先按 D4 出占位框，再按 D8 标 `derived` |
| 2 | **依赖可用性**（D15、D2） | 决定了本次**能产出什么**，早于任何生成动作 | D15（缺 python-pptx） × D11（deck 校验）→ deck 未生成，不进入 D11 |
| 3 | **任务冻结约束**（D6、D16） | 页数是评审可数的硬约束 | D6（页数冲突） × D7（听众缺失）→ 先满足冻结页数，再按 familiar 排背景比例 |
| 4 | **模板与渲染**（D5、D12） | 影响交付形态，不影响内容正确性 | D5（无模板） × D12（预览失败）→ 两条都记，状态同降 `partial` |
| 5 | **契约与记录**（D18、D19、D14） | 收口层：保证别人能复核上面所有取舍 | D18 × D19 → 契约字段先补齐，再登记时间戳差异 |

裁决必须留下**可读的理由**：`change_records` 里同时出现命中规则编号与最终采用的动作。

### 6. 状态判定矩阵（status 一致性）

`status` 只有三种取值；下表是**唯一**判定口径（实现见 `scripts/main.py`，可复核见
`scripts/check_status_matrix.py`）：

| 机器可见信号 | `completed` | `partial` | `failed` |
|-|-|-|-|
| 材料：≥1 个文本材料解析成功，且文本材料全部解析 | 必须 | 允许（有未解析文本材料） | 允许 |
| 计划门 P1–P8 | 必须全过 | 允许未全过 | 允许 |
| `deck_audit.valid` | 必须 true 且 deck 存在 | 允许 false / deck 缺失 | 允许 |
| 证据审计 | 必须 valid | 允许不 valid | 允许 |
| 预览 cover + manifest | 必须存在 | 允许缺失 | 允许 |
| `artifacts.deck_limitation` | 必须为空 | 允许有值 | 允许 |
| 退出码（`main.py`） | 0 | 0 | 1 |

反向约束（防止"把失败写成成功"和"把成功写成降级"）：

1. `completed` 而 `deck_limitation` 有值、或计划门未过、或有未解析文本材料 → **自相矛盾**，检查器报错；
2. `partial` 而**没有任何**机器可见缺陷信号 → 也是自相矛盾（状态没跟着降级走）；
3. `failed` 必须能指出 `error` 字段或 `change_records` 里的 deck 失败记录；
4. 每个降级理由都要在 `uncertainty` 有一条 `{item, impact, mitigation}`，三者皆非空。

```bash
python "$SKILL_DIR/scripts/check_status_matrix.py" /app/output            # 退出码 0 = 自洽
python "$SKILL_DIR/scripts/check_status_matrix.py" /app/output --json <path>  # 落盘报告供复核
```

### 7. 失败分支表（五族，与 references/failure-modes.md 一一对应）

#### B-M 材料异常

| 编号 | 情形 | 决策规则 | 处置要点 | 必写字段 |
|-|-|-|-|-|
| B-M1 | 声明材料不存在 | D1 | 保留条目 + `kind=missing`；相关页不规划 | `sources[]`、`uncertainty` |
| B-M2 | PDF 无解析器 / 解析失败 | D2 | `parsed=false` + 原因；其余材料照常 | `sources[].note` |
| B-M3 | 抽取丢公式/符号 | D3 | 以抽取文本为准；不补造 | `evidence_audit.entries[].notes` |
| B-M4 | 缺图 / 图损坏 | D4 | 诚实占位框；坏图跳过 | `pages[].figure_file`、`figure_bound` |
| B-M5 | 材料为空 / 全不可解析 | D17 | 只出结构性页面 | `sources[].kind=none` |
| B-M6 | 材料目录给了但为空目录 | D17 | 同 B-M5，并在记录里区分"空目录"与"无材料字段" | `change_records[step=material]` |

#### B-T 模板缺失 / 冲突

| 编号 | 情形 | 决策规则 | 处置要点 | 必写字段 |
|-|-|-|-|-|
| B-T1 | 无模板字段，或路径失效、打不开 | D5 | 内置主题；如实记录模式 | `artifacts.deck_mode.mode` |
| B-T2 | 模板自带示例页 | D16 | 保留母版/版式，丢弃自带页重建 | `template_slides_present/dropped` |
| B-T3 | 模板版式不兼容个别页 | D5 | 仅沿用可用版式，异常入记录 | `change_records[step=deck]` |
| B-T4 | 模板与冻结页数冲突 | D6/D16 | 冻结页数优先 | `plan_gates.gates[P3]` |

#### B-D 依赖缺失 / 渲染不可用

| 编号 | 情形 | 决策规则 | 处置要点 | 必写字段 |
|-|-|-|-|-|
| B-D1 | 缺 `python-pptx` | D15 | 跳过 deck，其余照常，命令仍返回 0 | `artifacts.deck_limitation` |
| B-D2 | 预览渲染失败/超时 | D12 | 非致命；可 `--skip-previews` | `artifacts.preview_note` |
| B-D3 | 缺 `pypdf` | D2 | PDF 记未解析 | `sources[].parsed` |
| B-D4 | 中文字体缺失 | — | 用 Pillow 内置位图字体并在 manifest 记明字形可能缺失 | `environment.cjk_font` |
| B-D5 | 环境无 LibreOffice/PowerPoint | — | 预览为 PIL 模拟 + 水印；以 `.pptx` 打开为准 | `preview_manifest.json` |

#### B-C 契约四形态（output_contract）

| 编号 | 情形 | 决策规则 | 处置要点 | 必写字段 |
|-|-|-|-|-|
| B-C1 | 案例声明了契约字段但流水线未产出 | D18 | 按声明容器类型初始化：`str→""`、`list→[]`、`dict→{}`、`number→0`、`bool→False`；**禁止 `null`** | `result.json` 顶层、`self_check.contract_check` |
| B-C2 | case.json 与 task.md 都声明了契约 | D18 | 合并去重，`declared_source` 同时记两者 | `contract.declared_source` |
| B-C3 | 两处都未声明 | D18 | 回落内置默认契约并注明来源 | `contract.declared_source="built-in default"` |
| B-C4 | 声明了额外字段（题面/平台要求） | D18 | 契约只增不减，照常注入 | `contract.applied` |
| B-C5 | 字段类型声明模糊 | D18 | 按 `any` 处理；不臆造结构 | `check_contract.py` 报告 |

#### B-S 状态不一致 / 门未过

| 编号 | 情形 | 决策规则 | 处置要点 | 必写字段 |
|-|-|-|-|-|
| B-S1 | 计划门或 deck 校验未过 | D9/D11 | 继续产出诚实产物 + 状态降级 | `plan_gates.errors` / `deck_audit.errors` |
| B-S2 | 自检发现结构问题 | D9 | 状态自动降 `partial` 并重写 `result.json` | `self_check.validate_after_downgrade` |
| B-S3 | 状态与内容矛盾（如 completed + deck 缺失） | §6 矩阵 | 机器判定为不一致，退出码 1 | `check_status_matrix.py` 报告 |
| B-S4 | 证据引用指向不存在的源文件 | D13 | 逐条列出；`evidence.source_file` 必须落在 `sources[]` | `evidence_audit` |
| B-S5 | 数字与源材料不一致 | D14 | 警告级提示 + 人工核对说明 | `validate_result` warnings |
| B-S6 | 多规则同时命中 | D20 | 按 §5 优先级裁决，全部命中项留痕 | `change_records` |

### 8. 收尾核对清单（逐项机器可查）

- [ ] `result.json` 存在；`case_id` 与输入一致；`status ∈ {completed, partial, failed}`
- [ ] `output_contract` 声明字段全部在顶层且类型正确（`self_check.contract_check.valid == true`）
- [ ] **状态自洽**：`check_status_matrix.py <out>` 退出码 0（§6 的 12 条规则全过）
- [ ] 每页（除封面/目录/问答备用页）有 `evidence[0].locator` 与逐字 `quote`
- [ ] `evidence_audit.json` 逐页核对过；所有 `evidence.source_file` 都在 `sources[]` 中
- [ ] `editable_deck.pptx` 可打开、每页有备注、页数 == 冻结页数（`verify_deck.py` 退出码 0）
- [ ] 预览 PNG 存在且带水印；`preview_manifest.json` 说明渲染限制与字体探测结果
- [ ] 命中任一决策规则时，`change_records` / `uncertainty` 均有对应条目（**无静默降级**）
- [ ] 包内只有 `.md/.py/.json/.txt/.csv/.yaml/.yml`；≤50 文件；单文件 ≤500KB；合计 ≤2MB；
      无符号链接、无 `__pycache__`、无本机绝对路径

### 9. 资源形态（为什么包内没有二进制）

题面运行契约原文：*at most 50 UTF-8 text files, 500KB each and 2MB total, no symlinks* /
*runtime artifacts may be binary and are retained independently of final JSON validity*。
因此本包**只提交文本资源**，所有二进制一律运行时生成：

| 常见二进制资源 | 本包做法 |
|-|-|
| 内置模板 `.pptx` | 不随包：`deck_builder._new_deck()` 现场构建 16:9 母版；案例自带模板则直接用平台的 |
| 示例图 `.png` / 示例 PDF | 不随包：`scripts/make_synthetic_inputs.py` 用 Pillow 画纯几何示意图、手工构造最小 PDF |
| 示例输出 `.pptx/.png` | 不随包：改为 `examples/EXPECTED-OUTPUT.md` 的文字清单与实测数量 |
| 字体 `.ttf/.otf` | 不随包：运行时按候选路径探测（`/usr/share/fonts`、`/System/Library/Fonts`、`C:/Windows/Fonts`） |
| `__pycache__` / `*.pyc` | 不随包：提交前删除（`selftest.py --package-check` 的 G10 会拦） |

### 10. 平台运行约束

- 平台把本 Skill 装到 `/skills/weekly-skill`，在固定 3 案例 × 3 次复跑上执行；
- 输入 `/input/case.json` + `/input/task.md`；中间产物放 `/app/work`；最终产物与 `result.json` 放 `/app/output`；
- `result.json` 必须含 output_contract 全部字段与 `case_id`；诚实记录 `status/sources/uncertainty/change_records`；
- 执行预算：64 个模型请求 / 900 秒 / 每响应 16384 token（含推理）。**尽早落盘**中间产物，
  预算耗尽时已落盘的部分仍然可复核（这正是 CP5 收口早于"再优化一轮"的原因）。

### 11. 文件地图

| 文件 | 作用 |
|-|-|
| `scripts/main.py` | 唯一入口，编排 CP1–CP5 |
| `scripts/check_status_matrix.py` | **本版新增**：状态一致性机器判定（§6 矩阵的可执行形式） |
| `scripts/scaffold_plan.py` / `validate_plan.py` | 页级规划 / 计划门 P1–P8 |
| `scripts/deck_builder.py` / `verify_deck.py` | 生成可编辑 deck / deck 机器校验 |
| `scripts/render.py` / `evidence.py` / `evidence_audit.py` | 预览渲染 / 材料与主张抽取 / 逐字证据审计 |
| `scripts/validate_result.py` / `check_contract.py` / `finalize_result.py` / `selftest.py` | 结构校验 / 契约校验 / 结果收口 / 全链路自检 |
| `scripts/make_synthetic_inputs.py` / `common.py` | 运行时生成示例二进制输入 / 共享工具与路径净化 |
| `references/decision-rules.md` | **本版新增**：D1–D20 全文、优先级裁决、分支族定义、与代码的对应 |
| `references/failure-modes.md` | F1–F26 失败模式表 + 五族分支 + 状态一致性规则（与 §4/§7 同源） |
| `references/OUTPUT_CONTRACT.md` | `result.json` 字段契约（含 §7 决策规则 ↔ 字段对照） |
| `references/RUBRIC_MAP.md` | 五维评分（40/25/15/10/10）→ 本包文件与机制 |
| `references/plan-contract.md` / `quality-gates.md` / `deck-rules.md` / `evidence-audit.md` | 计划条款 / G1–G10 / 版式命名 / 审计规范 |
| `templates/talk_config.json` etc. | 叙事规则、叙事模板、上台前清单 |
| `assets/plan.schema.json` | 计划契约模式（P1–P8 的单点真相） |
| `examples/` | 合成示例案例、预期输出清单、示例产物 |

---

# 【增益层】公平对照协议与可测指标（目标维度:使用增益 25）

---
name: academic-talk-organizer
description: >
  把已有科研材料组织成可讲、可编辑、证据可追溯的学术汇报（学术 PPT 页面组织）。
  输入：论文/研究报告/组会材料 + 听众、时长、页数、模板约束、讲稿或备注需求；
  关键词：学术汇报、答辩PPT、组会汇报、slides、deck、页码规划、讲稿、备注、问答准备、
  听众适配、叙事顺序、证据定位、evidence mapping、模板适配、增益对照、A/B 对照、
  gain protocol、可核验记录、契约回显。本包以"证据链"运行：每一步都产出可被第三方
  复算的记录（计划门 P1–P8 / 逐字证据审计 / deck 机器校验 / 契约四形态回显 /
  确定性探针），并提供 scripts/gain_ab.py 在同一输入上对照"不加载 Skill 的基础形态"，
  指标定义与实测记录见 references/GAIN-PROTOCOL.md（含不利于本包的结果）。
---

## 学术汇报内容组织 · v2 增益可验证版（academic-talk-organizer）

面向「玻尔产品周赛 · 学术效率 · 第三期」challenge-20870c35（slides 组）。

本版的重点不是"多做什么"，而是**让"多做了什么"能被别人复算**：
每个动作都留下结构化证据，效率与质量都被翻译成同一把尺子上的指标，
并且把**不利于本包的对照结果**一起放进包里。

**边界**：只做"从已有内容材料到可讲页面"的组织与交付；不做论文精读成稿、学术写作成稿、
科研绘图素材生产。页面内容取自源材料逐字引文，不改写事实、不补造数据。

### 1. 交付物：一份结果 + 一条可复算的证据链

```bash
SKILL_DIR="<本包根目录>"        # 平台安装后即 /skills/weekly-skill
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md --out /app/output
```

一次运行产出（`result.json` 是唯一评分产物，其余是它的证据）：

| 产物 | 它证明什么 |
|-|-|
| `result.json` | 契约字段齐全 + 主结果 + 三道审计内嵌（`audit{plan_gates,evidence,deck,gates}`） |
| `talk_plan.json` | 页级取舍**在生成之前**就已固定（可编辑、可 diff） |
| `plan_gates.json` | 计划守约（P1–P8 逐条，`assets/plan.schema.json` 驱动） |
| `evidence_audit.json` | 每页论断**能落回源材料**（逐字引文 + 行号区间 + 数字对源） |
| `deck_audit.json` | 交付的 `.pptx` 真的可打开、页数守约、每页有备注与 `page-claim-NN` |
| `previews/` + `preview_manifest.json` | 渲染可检查，并如实说明"PIL 模拟"的边界与字体探测结果 |
| `self_check.json` | 结构 + 契约 + 门快照 + **确定性探针**（内容投影 sha） |

退出码：**0** = 已产出通过 `validate_result` + `check_contract` 的 `result.json`
（`status` 说明是 `completed` 还是 `partial`——诚实降级不算崩溃）；**1** = 没有可用的契约结果；
**2** = 参数用法错误。

### 2. 证据链的七个环节（E1–E7）：每环都留下可复算的东西

| 环节 | 动作 | 产出证据 | 第三方复算方式 |
|-|-|-|-|
| **E1 材料实读** | 按真实路径读取每个材料并逐文件解析（md/txt/PDF），缺失照实标记 | `sources[].{file,path,kind,parsed,char_count,sections[]}`、`environment.pypdf` | 打开 `sources[]` 对拍磁盘；`kind=missing` 必须真的不存在 |
| **E2 计划先行** | 听众 → 背景比例；时长 → 页预算并**校准到冻结页数**；每页一个主张 + 一句话讲稿 + 证据强度 | `talk_plan.json`（含 `audience`、`narrative.order_blocks`、`timing`）、`summary.pages_total` | 改 `report_type` 重跑，页序与比例随之变化（可 diff） |
| **E3 计划门** | schema 驱动的 P1–P8 机器校验（含冻结页数、证据定位存在性、强度词法） | `plan_gates.json`、`result.audit.plan_gates` | `validate_plan.py <out>/talk_plan.json --materials-dir <材料>` |
| **E4 生成可编辑 deck** | 模板适配（沿用母版/版式、丢弃自带示例页）或内置主题；图绑定或诚实占位；确定性元素命名 | `editable_deck.pptx`、`artifacts.deck_mode/template_used` | `verify_deck.py <out>/editable_deck.pptx --expect-pages <N> --plan <out>/talk_plan.json` |
| **E5 渲染可检查** | PIL 模拟预览（封面/逐页/网格）+ manifest 说明限制 | `previews/*.png`（12 张）、`preview_manifest.json` | 看 PNG 魔数与 manifest；**不得**把它当成 Office 栅格化 |
| **E6 逐字证据审计** | 每页 `quote` 与实际读取文本逐字比对；行号落在章节区间；数字不在源文本逐字出现 → 警告 | `evidence_audit.json`、`evidence_map.json`（反向映射） | `evidence_audit.py <out>/result.json`（可加 `--sources-dir` 复读） |
| **E7 契约与自检** | 契约四形态回显（`""/[]/{}/0`，禁 `null`）+ 结构校验 + 确定性探针 | `result.json.contract`、`self_check.json` | `check_contract.py`、`validate_result.py`、`selftest.py` |

> **链条的意义**：任一环节失败都不会"消失"——它在该环节的证据文件里留下条目，
> 并让 `status` 降级（见 §6）。评审可以只读证据文件就判断"这份结果能不能信"。

### 3. 使用增益怎么被证明（本版核心）

题面写明：*"平台固定运行 3 个案例，比较不加载 Skill 与加载参赛 Skill 时的实际结果"*，
并禁止用文字自述替代运行证据。因此本包把"增益"写成**可复跑的对照协议**：

- 协议与指标定义：`references/GAIN-PROTOCOL.md`（两个臂的定义、公平性约束、
  D/C/E 三组指标的精确口径、复跑命令）；
- 对照装置：`scripts/gain_ab.py` —— 一条命令跑完**A 臂（基础形态模拟器）**与
  **B 臂（本包 main.py）**，用**同一把尺子**度量并写出 `gain_report.json`；
  它**不 import 本包任何模块**，只读产物，避免"用被测者自己的尺子量被测者"；
- 原始实测记录：`references/gain-run-record.json`（未手工编辑，可核对到每个字段）。

```bash
# 两个臂 + 度量（RUN 必须是包外临时目录）
python "$SKILL_DIR/scripts/gain_ab.py" --case "$SKILL_DIR/examples/case.json" \
       --work "$RUN/gain" --skill-dir "$SKILL_DIR"
```

### 4. 实测摘要（2026-11-22 本机真实运行；完整表见 GAIN-PROTOCOL.md §6）

同输入（包内合成示例案例：20 分钟 / 冻结 12 页 / 组会），A 臂 vs B 臂：

| 指标 | A 臂 | B 臂 | 方向 |
|-|-|-|-|
| 讲稿覆盖率 | 0.0 | **1.0** | B 优 |
| 来源定位覆盖率（内容页） | 无该字段 | **1.0（10/10）** | B 优 |
| 问答条目 / 证据行 | 0 / 0 | **4 / 11** | B 优 |
| `result.json` 顶层键 | 无文件 | **20** | B 优 |
| 有效 PNG 预览 | 0 | **12** | B 优 |
| 达到冻结页数的运行轮数 | **2**（首轮 3 页） | **1**（首轮 12 页） | B 优 |
| 单臂墙钟秒 | **0.26** | 1.67 | A 优（B 更慢） |
| 可见文本逐字可溯源率 | **0.75** | 0.3333 | **A 优（不利于 B）** |
| 数字可对源率 | **1.0** | 0.8679 | **A 优（不利于 B）** |

**为什么后两项 A 更好、以及它说明了什么**：A 臂整段照搬材料，可见文本自然与源文本重合；
B 臂页面上是压缩后的主张与短行（长句渲染时被截断），所以"可见文本逐字命中"这项天然吃亏；
B 臂的可溯源性是**结构化**的（每页有定位与引文，且由 `evidence_audit` 独立校验）。
B 臂未命中的数字样本是页脚页码（`01…12`）与时长换算值（`20.0/100.0`），不是科学数据。

⇒ **本包不声称"质量提升 X%"**：对照是单案例、单机的机制与可测性证据，不是平台白板结果。

### 5. 降级时证据链如何保持完整

| 情形 | 仍然产出 | 证据链上的记录 |
|-|-|-|
| 缺 `python-pptx` | 页计划、计划门、预览、`result.json`、`self_check.json`；**命令仍返回 0** | `artifacts.editable_deck=null` + `deck_limitation` + `uncertainty` 一条 + `change_records` 记明 |
| 缺 `Pillow` | 除预览与 deck 外全部 | `preview_note` + `status=partial` |
| 缺 `pypdf`/`PyPDF2` | 其余材料照常 | `sources[].parsed=false` + `note` |
| 材料缺失 / 材料为空 | 结构性页面 + 诚实标注 | `sources[].kind=missing/none` + `uncertainty` |
| 无模板 / 模板打不开 | 内置主题 deck | `artifacts.deck_mode.mode` + `template_used` |
| 模板自带示例页 | 沿用母版/版式、丢弃自带页 | `template_slides_present/dropped`；最终页数 == 冻结页数 |
| 计划门/证据审计/deck 校验未过 | 照常落盘全部产物 | 对应审计文件 + `status=partial`；**不宣称"校验通过"** |
| `case.json` 不可读 | 最小失败信封 | `status=failed` + `error`；退出码 1 |

**统一纪律**：降级必须**同时**满足三条 —— ① `status` 跟着降；② `uncertainty` 有
`{item, impact, mitigation}`；③ `change_records` 有 `{at, step, action}`。
三者缺一即为"静默降级"，本包视为缺陷。

### 6. 收尾核对清单（每条都能机器验证）

- [ ] `result.json` 存在；`case_id` 与输入一致；`status ∈ {completed, partial, failed}`
- [ ] 契约字段齐全且**无 `null`**（`self_check.contract_check.missing_required == []`）
- [ ] 计划门 P1–P8 全过（或 `uncertainty` 里有对应条目）
- [ ] 每页（除封面/目录/问答备用页）有 `locator` + 逐字 `quote`
- [ ] `evidence.source_file` 全部能在 `sources[]` 找到（无孤儿引用）
- [ ] `editable_deck.pptx` 可打开、页数 == 冻结页数、每页有备注（`verify_deck.py` 退出码 0）
- [ ] 预览 PNG 有效且带水印；manifest 说明限制与字体探测结果
- [ ] 双跑确定性：内容投影 sha 相同（记录性时间戳已由探针剔除）
- [ ] 若跑过对照：`gain_ab.py` 的 `gain_report.json` 与 `GAIN-PROTOCOL.md` §6 数字一致
- [ ] 包内只有 `.md/.py/.json/.txt/.csv/.yaml/.yml`；≤50 文件；单文件 ≤500KB；合计 ≤2MB；
      无符号链接、无 `__pycache__`、无本机绝对路径

### 7. 输入与依赖（事实层）

**输入**：`/input/case.json`（`case_id`/`title`/`report_goal`/`audience`/`duration_min`/`slide_count`/
`report_type`/`materials`/`template`·`start_deck`/`figure_files`/`output_contract`）+ `/input/task.md`
+ 材料目录。**必须实际读取文件内容**，不按标签预设。

**依赖**：Python ≥ 3.8（本机 3.13.9）；必需 `python-pptx` + `Pillow`；
可选 `pypdf`/`PyPDF2`（PDF 文本）；无网络、无 cwd 依赖；不调用 LibreOffice/PowerPoint。
字体：运行时按候选路径探测系统字体（`/usr/share/fonts`、`/System/Library/Fonts`、`C:/Windows/Fonts`），
探测结果（仅文件名）写入 `environment.cjk_font` 与 `preview_manifest.json`；找不到则用内置位图字体并记明。

### 8. 资源形态与平台约束

题面运行契约原文：*at most 50 UTF-8 text files, 500KB each and 2MB total, no symlinks* /
*runtime artifacts may be binary and are retained independently of final JSON validity*。

| 常见二进制 | 本包做法 |
|-|-|
| 模板 `.pptx` | 不随包：`deck_builder` 现场构建 16:9 母版；案例模板直接读取 |
| 示例图/PDF | 不随包：`scripts/make_synthetic_inputs.py` 运行时生成（纯几何示意图 + 手工最小 PDF） |
| 示例输出 `.pptx/.png` | 不随包：`examples/EXPECTED-OUTPUT.md` 用文字列清单与实测数量 |
| 字体 | 不随包：运行时探测（见 §7） |
| `__pycache__`/`.pyc` | 不随包：提交前删除（`selftest.py --package-check` 的 G10 拦截） |

平台在 `/skills/weekly-skill` 安装本包，固定 3 案例 × 3 复跑；中间产物放 `/app/work`、
最终产物放 `/app/output`；执行预算 64 请求 / 900 秒 / 每响应 16384 token ——
**尽早落盘**：预算耗尽时已落盘的部分仍可复核（这正是收口先于"再优化一轮"的原因）。

### 9. 文件地图

| 文件 | 作用 |
|-|-|
| `scripts/main.py` | 唯一入口（CP1–CP5 编排） |
| **`scripts/gain_ab.py`** | **本版新增**：A/B 对照装置（基线模拟器 + 度量器，不 import 本包模块） |
| `scripts/scaffold_plan.py` / `validate_plan.py` | 页级规划 / 计划门 P1–P8 |
| `scripts/deck_builder.py` / `verify_deck.py` | 生成可编辑 deck / deck 机器校验 |
| `scripts/evidence.py` / `evidence_audit.py` / `render.py` | 材料与主张抽取 / 逐字审计 / 预览渲染 |
| `scripts/validate_result.py` / `check_contract.py` / `finalize_result.py` / `selftest.py` | 结构 / 契约 / 收口 / 全链路自检 |
| `scripts/make_synthetic_inputs.py` / `common.py` | 运行时生成示例输入 / 共享工具与路径净化 |
| **`references/GAIN-PROTOCOL.md`** | **本版新增**：对照协议、指标定义、实测记录、不利结果、待改进项 |
| **`references/gain-run-record.json`** | **本版新增**：`gain_ab.py` 的原始输出（未手工编辑） |
| `references/OUTPUT_CONTRACT.md` | 字段契约（含 §7 指标 ↔ 字段对照） |
| `references/RUBRIC_MAP.md` | 五维评分 → 文件与机制逐条对照 |
| `references/failure-modes.md` / `plan-contract.md` / `quality-gates.md` / `deck-rules.md` / `evidence-audit.md` | 失败模式 / 计划条款 / G1–G10 / 版式命名 / 审计规范 |
| `templates/` · `assets/` · `examples/` | 叙事规则与模板 / 计划模式与结果信封 / 合成示例 |
