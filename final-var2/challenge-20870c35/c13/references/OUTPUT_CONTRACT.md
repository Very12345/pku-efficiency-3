# OUTPUT_CONTRACT.md — result.json 结构化契约（v3 · 机制与复用版）

> 本契约由 `scripts/check_contract.py`、`scripts/validate_result.py`、
> `scripts/selftest.py` 三方执行：「字段齐全（契约）」+「结构正确、文件在盘、
> 证据可追溯、数字可对源（校验）」+「全链路复核（自检）」。
> 正文中 `result.json` 的**相对路径均相对 result.json 所在目录**（即 `/app/output`）。
>
> **本版边界**：§1–§6 的**字段块**（字段名、类型、结构、状态语义、退出码、审计分组、
> 复核命令）**逐字保持原样**；v3 只重写了本页开头这段说明，并新增文末
> **§7「机制 ↔ 契约字段对照」**——说明 `references/MECHANISM.md` 里的每个机制
> 各自把事实写进哪些字段，使"机制是否真的在工作"可以被机器判定。

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

## 7. 机制 ↔ 契约字段对照（v3 新增）

机制定义见 `references/MECHANISM.md`；本表说明**每个机制把事实写进哪些字段**，
使"机制是否真的在工作"可以被机器判定（而不是只写在文档里）。

| 机制 | 主要字段 | 机器判定 |
|-|-|-|
| M1 计划契约门先行 | `plan_gates.valid/errors/gates[P1..P8]`、`audit.plan_gates`、`summary.pages_total`、`slide_count` | `gates[P3].pages == target`；`validate_plan.py` 退出码 0 |
| M2 逐字证据审计 | `pages[].evidence{source_file,section,line_no,locator,quote,strength}`、`audit.evidence.summary`、`evidence_map` 字段（同名产物文件） | `audit.evidence.valid=true` 且 `errors==0`；`evidence_audit.py` 退出码 0 |
| M3 叙事配置化 | `audience{expertise,background_ratio,evidence_depth}`、`summary.narrative_order` | 改 `report_type` 后 `order_blocks` 与 `background_ratio` 必须变化 |
| M4 问答预演 | `pages[].qa[]{question,answer_points}`、`pages[].notes`、`audit.deck.slides[].notes_nonempty` | `Σ len(pages[].qa) > 0` 且备注逐页非空 |
| M5 模板适配与自带页丢弃 | `artifacts.deck_mode{mode,template_slides_present,template_slides_dropped}`、`artifacts.template_used`、`audit.deck.{valid,slide_count}` | `slide_count == len(pages)`；差值 = 丢弃页数 |
| M6 契约四形态与状态可见性 | `contract.{declared_source,applied}`、`status`、`uncertainty[]`、`change_records[]`、`artifacts.deck_limitation` | 顶层无 `null`；`check_contract.py` 的 `missing_required==[]`；降级时三处留痕 |
| M7 运行时文本化资源 | `environment{python_pptx,pillow,pypdf,cjk_font}`、`artifacts.previews`、`preview_note` | `selftest.py --package-check` 的 `errors==[]`；包内零二进制 |
| M8 确定性探针 | `self_check.determinism{plan_sha16,evidence_map_sha16,deck_pptx_normalized_sha16}` | 双跑三个 sha 逐位相同；`selftest.py` 的 `determinism_probe` ok |

> 复用这些机制时（见 `references/REUSE-KIT.md`），字段名就是接口：
> 只要保留上表的字段，第三方脚本（如 `evidence_audit.py`、`gain_ab.py`）就能直接读你的产物。
