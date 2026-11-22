# OUTPUT_CONTRACT.md — result.json 结构化契约（v4 · 失败注入与恢复演练版）

> **本版对契约正文的改动：无。** 下文 §1 的字段表、§2 的证据字段表、§3 的 `status` 语义、
> §3b 的退出码表、§4 的 `audit` 结构、§5 的 `self_check` 结构**逐字保留**（与上一版一致）。
> v4 只在文件**末尾追加** §7/§8 两节，说明"降级在哪些字段里可见"以及"契约在故障注入下的实测行为"。
> 追加内容不新增必填字段、不改任何既有字段名或容器类型。

> 本契约由 `scripts/check_contract.py`、`scripts/validate_result.py`、
> `scripts/selftest.py` 三方执行：「字段齐全（契约）」+「结构正确、文件在盘、
> 证据可追溯、数字可对源（校验）」+「全链路复核（自检）」。
> 正文中 `result.json` 的**相对路径均相对 result.json 所在目录**（即 `/app/output`）。

## 0. 路径可移植性（本版新增）

`result.json` / `talk_plan.json` / `evidence_map.json` / `deck_audit.json` /
`preview_manifest.json` / `self_check.json` 里的路径一律是**可移植形式**：

| 输入形态 | 写盘后的形态 |
|-|-|
| 本机绝对路径（作者机器）：Windows 盘符路径（盘符 + 反斜杠或正斜杠）、UNC 路径（双反斜杠 + `?` + 反斜杠开头） | **相对案例目录**的正斜杠路径：`materials/fig2.png`；不在案例目录下则退化为文件名 |
| 消息里内嵌的本机路径（错误文本、change note） | 就地改写为相对形式 |
| POSIX 运行期路径：`/input/case.json`、`/app/output/...` | **原样保留**（这是评测主机上的真实路径，必须可查） |
| 已经是相对路径 | 原样保留 |

实现见 `scripts/common.py` 的 `portable_path()` / `sanitize_output()`
（`main.py` 启动时用 `set_path_bases(<case_dir>)` 注册基准目录，`write_json()` 写盘时净化副本，
内存中的真实路径不受影响）。⇒ 提交资源与产物里不会残留作者机器的路径痕迹。

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
| `artifacts` | dict | `{editable_deck, talk_plan, evidence_map, evidence_audit, deck_audit, plan_gates, previews{cover,grid,manifest,slide_pngs}, template_used, deck_mode, preview_note, deck_limitation}`；`editable_deck` 在缺依赖时为 `null`，原因写 `deck_limitation` |
| `sources` | list | 每条 `{file, path, kind, parsed, note, char_count, sections[]}`；缺失材料 `kind=missing` |
| `uncertainty` | list | 每条 `{item, impact, mitigation}`（限制/降级必须有一条） |
| `change_records` | list | 每条 `{at, step, action}`，记录全部取舍/失败/降级动作 |
| `contract` | dict | `{declared_source, applied[]}`：本包实际执行的契约来源与字段清单 |
| `audit` | dict | `{plan_gates, evidence, deck, gates}`：三道审计 + G 门快照（见 §4） |
| `environment` | dict | 运行环境如实记录：`{python, platform, python_pptx, pillow, pypdf, cjk_font{found,file,family}}`（依赖缺失记 `null`） |
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
（derived 页按"概括语"如实记录），见 `references/evidence-audit.md`。

## 3. status 语义

| status | 条件 |
|-|-|
| `completed` | 材料全部解析（至少一个解析成功）、计划门 P1–P8 全过、`editable_deck.pptx` 写入且 verify_deck 通过、预览渲染、证据审计 + 自检通过 |
| `partial` | 任一材料未解析/缺失/**没有任何材料可解析**/计划门未全过/**缺 python-pptx 或 Pillow 导致 deck 或预览未生成**/证据审计发现问题/自检发现问题 —— 缺陷逐条写入 `uncertainty` 与 `change_records` |
| `failed` | `case.json` 不可读，或**已安装 python-pptx 但 deck 生成抛错**；此时仍写出 `result.json` 记录错误（`error` 字段） |

**不允许**：编造缺失软件状态、编造数据、把未覆盖证据描述为已覆盖、把降级静默处理成成功。
数字一致性由 `validate_result.py` 以**警告**级提示（页面数字不在任何源文本中）。

## 3b. 进程退出码（`scripts/main.py`）

| 退出码 | 含义 |
|-|-|
| `0` | 已产出通过 `validate_result` + `check_contract` 的 `result.json`。**其 `status` 字段说明是 `completed` 还是 `partial`** —— 诚实降级（如缺 python-pptx）不会被报成崩溃 |
| `1` | 没有可用的契约结果（`case.json` 不可读 → 最小失败信封；或自检未通过 / deck 意外抛错） |
| `2` | 参数用法错误（argparse） |

## 4. audit 与 G 门快照（result.audit）

| 字段 | 来源 | 内容 |
|-|-|-|
| `audit.plan_gates` | `plan_gates.json` | 计划契约门 P1–P8 逐条（`assets/plan.schema.json` 定义） |
| `audit.evidence` | `evidence_audit.json` | 逐页逐字引文核验 + 定位/强度/图绑定 |
| `audit.deck` | `deck_audit.json` | 打开、页数、每页备注/claim 元素、OPC 完整性、规范化 sha |
| `audit.gates` | finalize_result 汇总 | G1–G10 质量门快照（见 `references/quality-gates.md`） |

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
# $SKILL_DIR = 本包根目录（含 SKILL.md）；脚本自定位，cwd 任意
python "$SKILL_DIR/scripts/validate_result.py" <out>/result.json     # 退出码 0 = 通过
python "$SKILL_DIR/scripts/check_contract.py"  <out>/result.json     # 退出码 0 = 契约齐全
python "$SKILL_DIR/scripts/evidence_audit.py"  <out>/result.json     # 退出码 0 = 证据可溯源
python "$SKILL_DIR/scripts/verify_deck.py" <out>/editable_deck.pptx \
       --expect-pages <N> --plan <out>/talk_plan.json                # 退出码 0 = deck 校验通过
python "$SKILL_DIR/scripts/selftest.py" <out> [--package-check "$SKILL_DIR"]  # 全链路复核
```

`selftest.py --package-check` 同时核对题面资源硬门：≤50 个 UTF-8 文本文件、单文件 ≤500KB、
合计 ≤2MB、无符号链接、无 `__pycache__`（G10）。

## 7. 降级在哪些字段里可见（v4：三处留痕，缺一即算静默）

`status` 只是一个**结论**；要能独立复核，原因必须在**三处**同时对得上。
`scripts/fault_inject.py` 的"非静默"判定就用这张表：

| 落点 | 字段 | 谁写 | 复核方式 |
|-|-|-|-|
| ① 状态 | `status`（`completed` / `partial` / `failed`） | `main.py` 按 D 规则升级 | 读 `result.json.status`；`failed` 时再看 `error` |
| ② 声明 | `uncertainty[]`（每条 `{item, impact, mitigation}`） | 各降级分支 | **≥1 条**才算这条降级被声明过；只读 `uncertainty` 的复核者也能发现 |
| ③ 过程 | `change_records[]`（每条 `{at, step, action}`） | 全流程 | 按 `step` 过滤（`material`/`deck`/`deck-source`/`preview`/`plan-gate`/`contract`/`audit`） |

补充落点（**不替代**上面三处，只是更细的机读位置）：

| 降级 | 细粒度字段 |
|-|-|
| 缺 `python-pptx` | `artifacts.editable_deck = null` + `artifacts.deck_limitation` |
| 模板未沿用（缺失/损坏） | `artifacts.template_used = null`；`artifacts.deck_mode.mode = "built-in-theme"`；损坏时另有 `deck_mode.template_load_error` |
| 模板自带页被丢弃 | `artifacts.deck_mode.{template_slides_present, template_slides_dropped}` |
| 材料未解析 / 缺失 | `sources[].parsed = false`；缺失材料 `kind = "missing"`；`sources[].note` 写原因 |
| 计划门未全过 | `audit.plan_gates.valid = false` + `errors[]` |
| 证据审计有问题 | `audit.evidence.valid = false` + `notes[]` |
| 契约未能解析 | `contract.declared_source`（回落来源）+ `change_records` 的 `contract` 步 |
| 契约字段回落 | `contract.applied[]` 列出实际回显的字段名 |

## 8. 契约在故障注入下的实测行为（v4）

| 注入 | 契约层实测结果 |
|-|-|
| `F12` 契约块非法 JSON | `contract.declared_source` 回落到 `case.json`；`change_records` 增 `contract` 步；`uncertainty` 增一条；`status=partial` |
| `F13` 空契约 `{}` + `case.json` 无声明 | 回落 `built-in default`，`contract.applied` **14** 个字段；`result.json` 顶层仍 **20** 键 —— 题面要求的核心字段一个不缺 ⇒ **契约只增不减**在空声明分支上同样成立 |
| `F14` 多声明 1 个产不出的字段 | 顶层 **21** 键；该字段值 `""`（**不是 `null`**）；`self_check.contract_check.valid = true`；退出码 `0` |

> **§1「四形态回显，禁止 null」的实测意义**：修前 `CONTRACT_TYPE_DEFAULTS["any"] = None`
> 会让"类型未声明"的契约字段落成 `null` —— 字段名在、值却是空的，`check_contract` 判缺失，
> 与本节表头那句话直接矛盾，且会把退出码顶成 `1`。v4 已修（`None → ""`），
> `F14` 是它的回归用例。
