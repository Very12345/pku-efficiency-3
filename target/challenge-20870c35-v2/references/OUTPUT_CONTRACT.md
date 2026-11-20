# OUTPUT_CONTRACT.md — result.json 结构化契约（v2）

> 本契约由 `scripts/check_contract.py`、`scripts/validate_result.py`、
> `scripts/selftest.py` 三方执行：「字段齐全（契约）」+「结构正确、文件在盘、
> 证据可追溯、数字可对源（校验）」+「全链路复核（自检）」。
> 正文中 `result.json` 的**相对路径均相对 result.json 所在目录**（即 `/app/output`）。

## 1. 必填字段（顶层）

`main.py` 会把 `case.json` / `task.md` 中声明的 output_contract（或其字段表）**逐项注入
result.json 顶层**；未在案例中声明时回落到下表内置契约。缺失字段按声明容器类型以
`""` / `[]` / `{}` / `0` 初始化（**四形态回显，禁止 null**），并在
`self_check.json → contract_check.missing_required` 记录。

| 字段 | 类型 | 说明 |
|-|-|-|
| `case_id` | str | 输入标识，取 `case.json["case_id"]`，缺失时取文件名 |
| `status` | str | `completed` / `partial` / `failed`（见 §3） |
| `title` | str | 汇报标题 |
| `report_goal` | str | 报告目标（来自案例，缺省空） |
| `audience` | dict | 听众画像：`{description, expertise, background_ratio, evidence_depth, notes}` |
| `duration_min` | number | 时长（分钟） |
| `slide_count` | number | 目标页数 |
| `summary` | dict | `{narrative_order, plan_file, pages_total}` |
| `main_line` | dict | `{research_question[], method[], results[], limitations[], conclusion[]}`，每项 `{claim, evidence, page_no}` |
| `pages` | list | 页级结构，每条含 `page_no/block/title/claim/one_liner/evidence/figure_ref/figure_file/notes/strength/qa/derived` |
| `evidence_map` | dict | `source_file → {pages[], refs[]}` 的全局映射 |
| `artifacts` | dict | `{editable_deck, talk_plan, evidence_map, evidence_audit, deck_audit, plan_gates, previews{cover,grid,manifest,slide_pngs}, template_used, deck_mode, preview_note}` |
| `sources` | list | 每条 `{file, path, kind, parsed, note, char_count, sections[]}` |
| `uncertainty` | list | 每条 `{item, impact, mitigation}` |
| `change_records` | list | 每条 `{at, step, action}`，记录全部取舍/失败/降级动作 |
| `contract` | dict | `{declared_source, applied[]}`：本包实际执行的契约来源与字段清单 |
| `audit` | dict | `{plan_gates, evidence, deck, gates}`：三道审计 + G 门快照（见 §4） |
| `generated_by` / `generated_at` | str | 生成器标识与时间 |

> 平台/task.md 若声明**额外字段**，`apply_contract` 会保证其存在并按声明容器类型填默认值
> —— 契约只增不减。`assets/result.template.json` 给出信封示例。

## 2. 证据与页级结构（可核验性）

每页 `evidence` 至少一条（封面/目录/问答备用页除外），字段：

| 字段 | 说明 |
|-|-|
| `source_file` | 源材料文件名（须存在于 `sources[].file`，否则自检报错） |
| `section` | 章节路径（`§`） |
| `line_no` | 行号（`L`），PDF 时为抽取文本中的行序号 |
| `locator` | 组合定位 `L<行号> · §<章节>` |
| `quote` | 原句引文（逐字取自源材料，**未改写事实**） |
| `strength` | `strong` / `medium` / `weak`，依数值/统计/图表引用存在与否自动判定 |

`evidence_map.json` 给出反向映射（源文件 → 用到它的页 + 该文件出现的图表引用），供独立复核。
`evidence_audit.json` 进一步对**每一页**逐字核验 quote 是否出现在实际读取的源文本中
（derived 页按"概括语"如实记录），见 `references/EVIDENCE_AUDIT.md`。

## 3. status 语义

| status | 条件 |
|-|-|
| `completed` | 材料全部解析、计划门 P1–P8 全过、`editable_deck.pptx` 写入且 verify_deck 通过、预览渲染、证据审计 + 自检通过 |
| `partial` | 任一材料未解析/缺失/计划门未全过/预览未渲染/证据审计发现问题/自检发现问题 —— 缺陷逐条写入 `uncertainty` 与 `change_records` |
| `failed` | case.json 不可读或可编辑演示文件生成抛错；仍写出 result.json 记录错误 |

**不允许**：编造缺失软件状态、编造数据、把未覆盖证据描述为已覆盖。
数字一致性由 `validate_result.py` 以**警告**级提示（页面数字不在任何源文本中）。

## 4. audit 与 G 门快照（result.audit）

| 字段 | 来源 | 内容 |
|-|-|-|
| `audit.plan_gates` | `plan_gates.json` | 计划契约门 P1–P8 逐条（`assets/plan.schema.json` 定义） |
| `audit.evidence` | `evidence_audit.json` | 逐页逐字引文核验 + 定位/强度/图绑定 |
| `audit.deck` | `deck_audit.json` | 打开、页数、每页备注/claim 元素、OPC 完整性、规范化 sha |
| `audit.gates` | finalize_result 汇总 | G1–G10 质量门快照（见 `references/QUALITY_GATES.md`） |

## 5. 自检文件（self_check.json）

与 result.json 同目录，含：
- `validate`：`validate_result.py` 输出（`errors/warnings/checks`）
- `contract_check`：`check_contract.py` 输出（`declared/missing_required/wrong_type`）
- `contract_applied`：实际注入的字段清单
- `plan_gates` / `audit_gates`：P 门与 G 门结果
- `determinism`：内容投影 sha（talk_plan.json / evidence_map.json，剔除记录性时间戳）
  + deck 规范化 sha —— 供双跑一致性核验

## 6. 独立复核命令

```bash
python scripts/validate_result.py <out>/result.json          # 退出码 0 = 通过
python scripts/check_contract.py <out>/result.json           # 退出码 0 = 契约齐全
python scripts/evidence_audit.py <out>/result.json           # 退出码 0 = 证据可溯源
python scripts/verify_deck.py <out>/editable_deck.pptx \
       --expect-pages <N> --plan <out>/talk_plan.json        # 退出码 0 = deck 校验通过
python scripts/selftest.py <out> [--package-check <skill-root>]  # 全链路复核
```