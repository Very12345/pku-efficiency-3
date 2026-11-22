# OUTPUT_CONTRACT — result.json 契约（slides 组：学术 PPT 模板与格式适配，v2）

本文档定义 `scripts/main.py` 在 `/app/output/result.json` 产出的结构化结果契约。
**每个案例返回一份**；所有字段由脚本对真实产物诚实生成，Agent 只补充需要
科学判断的叙述字段（如 uncertainty、status_notes），禁止编造数据、模板状态
或评分。

若 `case.json` 自带 `output_contract` 对象，脚本会把其中的**每一个键**同样
回显到 result.json 顶层（未覆盖的键按声明类型填 `""` / `[]` / `{}` / `0` /
`false`，**绝不填 `null` 占位**），因此无论平台的字段清单如何，结果都能完整对齐。

## 顶层字段

| 字段 | 类型 | 必填 | 说明 |
|-|-|-|-|
| `case_id` | string | 是 | 输入 case_id（缺失时取 case 文件名的 stem） |
| `skill` | object | 是 | `{name, version, display}` |
| `status` | enum | 是 | `success`（无 fail/warn 检查）/ `partial`（存在 warn/fail，已如实记录）/ `failed`（流水线未完成） |
| `workorder` | string | 是 | `academic_slide_deck` |
| `task_summary` | string | 是 | task.md 摘要（可空） |
| `title` / `subtitle` | string | 是 | 讲稿标题与副标题 |
| `audience` | string | 是 | 受众（来自 case/task） |
| `duration_minutes` | number | 是 | 汇报时长（来自 case，缺省 15） |
| `language` | string | 是 | `zh` / `en` |
| `slide_count` | number | 是 | 实际生成的页数 |
| `main_result` | object | 是 | 主结果摘要（见下） |
| `artifacts` | array | 是 | 产物清单（role/format/path/abspath/checks sha256；**不含 result.json 自身**，避免自引用哈希破坏确定性）。`abspath` 记**便携路径**：相对当前运行目录、正斜杠、不含本机盘符或用户目录，任何主机上都可读 |
| `slide_evidence` | array | 是 | **页级证据映射**：每页 `{page_no, page_type, title, claims, figure_refs, table_refs, evidence[{claim, loc}], notes_excerpt}` |
| `template_audit` | object | 是 | **模板套用审计**（见下，含 v2 新增 theme + adopt-plan 应用） |
| `adopt_plan` | object | 是 | **两阶段工作流·阶段一方案摘要**（v2 新增）：`{source, pages_assigned, layout_gaps, batch_deviations, figure_plan, gates}` |
| `verification` | object | 是 | `{checks, render, traceability, contract_gates}`（G1–G8 见下） |
| `sources` | array | 是 | 实际读取的来源材料（rel/exists/lines） |
| `uncertainty` | array | 是 | `[{item, note}]`：缺值、源图缺失、模板回退、字体/导出限制等 |
| `change_records` | array | 是 | 编辑任务（starting deck、adopt-plan 偏差等）before→after 记录；无编辑为空数组 |
| `status_notes` | string | 是 | 状态语义说明 |
| `generated_at` | string | 是 | ISO8601 UTC 时间 |
| `generator` | string | 是 | `academic-slide-adapt` |
| `tool_versions` | object | 是 | python/pptx/PIL/numpy/reportlab 版本 |

## main_result

```jsonc
{
  "deck": {"path": "<case_id>_deck.pptx", "format": "pptx", "editable": true},
  "planned_slides": 10, "target_slides": 10,
  "notes_pages": 10,
  "figures_embedded": 2, "figures_total": 2,
  "tables_pages": 1,
  "previews": {
    "cover": "<case_id>_cover_preview.png",
    "contact_schematic": "<case_id>_slides_contact_schematic.png"
  },
  "preview_is_schematic": true
}
```

## template_audit（模板 / 版式 / 占位符继承关系可查）

| 字段 | 说明 |
|-|-|
| `template_source` | 实际打开的模板（case 模板 / starting deck / 运行时生成的内置回退），记为**便携路径**（运行相对、正斜杠） |
| `opened_from` | `case_template` ／ `starting_deck` ／ `builtin` |
| `template_fallback_used` | 是否为内置回退模板 |
| `slide_size_emu` | 模板画布尺寸（EMU） |
| `layouts` | 模板全部版式的占位符清单（idx/name/宽高） |
| `layout_used` | 每页实际套用的版式名 + master 名 + 来源（`adopt_plan`/`best_fit`） |
| `layout_fallback_used` | 是否存在"需求占位符缺失 → 手绘文本框替代" |
| `dropped_original_slides` | starting deck 被替换的原始页数（>0 表示发生了编辑） |
| `template_errors` | 打开模板时的错误记录（空数组=无） |
| `figure_adjust` | 图表等比缩放日志（src/scale/aspect_preserved） |
| `theme` | **v2**：主题字体（latin/ea）+ 主题色（读 theme1.xml，尽力而为） |
| `adopt_plan_applied / adopt_plan_total_pages` | **v2**：阶段一方案在阶段二实际套用的页数（方案↔执行一致性） |
| `adopt_plan_deviations` | **v2**：方案未能套用的逐条偏差（绝不静默改变） |

## adopt_plan（阶段一方案摘要）

```jsonc
{
  "source": "builtin",            // 方案分析的模板来源
  "pages_assigned": 10,           // 页→版式分配页数
  "layout_gaps": [],              // 无法提供所需角色的版式缺口
  "batch_deviations": [],         // 批量规则偏差（已披露）
  "figure_plan": 3,               // 图表放置计划条目数
  "gates": {"G1_template_open": true, "G2_layouts_enumerated": true,
            "G3_every_page_has_layout": true, "G4_batch_rules_ok_or_disclosed": true,
            "ok": true}
}
```

完整方案见 `<out>/adopt_plan.json`（模板结构审计 / page→layout 分配 / 批量规则 /
figure 放置计划，均由 `scripts/adopt_plan.py` 生成，确定性纯函数）。

## verification

- `checks`：审计清单，每条 `{check, level: ok|warn|fail, detail}`：
  `artifact.*.exists`（pptx/两预览/spec/adopt_plan）、`pptx.reopen`、`pptx.slide_count`、
  `content.claim_coverage`、`xref.figure_refs / figure_placement`、`notes.present`、
  `layout.overflow / font_floor`、`layout.footer_uniform`、`preview.*`（PNG 签名）、
  `traceability.evidence_loc`、`adopt_plan.consistency / adopt_plan.gates`（v2）、
  `result.contract`、`result.contract_gates`。
- `render`：`render_log.json` 全文（渲染后端、字体探测、诚实说明）。字体项按
  **文件名**记录（`file` / `index` / `fallback_default` / `candidates_probed`），
  字体目录在运行时按平台标准位置解析，因此日志里不含本机路径。
- `traceability`：`{evidence_loc_frac, contract_ok, hashes{spec, adopt_plan}}`；
  `evidence_loc_frac` 是**真实覆盖率**（带 `文件:行` 定位的证据行 / 全部证据行，
  0.0–1.0），与 `checks` 里的 `traceability.evidence_loc` 同源。
- `contract_echo_derived`：只列**由本次运行真实推出**的契约键（例如
  `preview_png` / `evidence_per_slide` / `notes_per_slide` /
  `template_inheritance`）及其取值，供核对"这个 true 从哪来"。
- `contract_gates`：**v2 CP3 硬性门 G1–G8**（见下），每条 `{gate, ok, detail}`。

## CP3 硬性门（G1–G8，`scripts/check_contract.py` 独立复查）

| 门 | 含义 | 判定 |
|-|-|-|
| G1 | case_id 存在且与 case.json 一致 | 逐字相等（case 提供时） |
| G2 | status ∈ {success, partial, failed} | 诚实词汇 |
| G3 | output_contract 全部键回显顶层且无 null 占位 | 缺失/空占位即失败；已知语义的键取本次运行真实值（见 D10） |
| G4 | main_result.deck 存在且可被 python-pptx 重开 | 重开成功 |
| G5 | slide_evidence 为每页一条、字段齐全 | 逐条 page_no/page_type |
| G6 | template_audit 含 opened_from/template_source/layouts/layout_used | 继承关系可查 |
| G7 | 产物清单中每个文件真实存在 | 逐文件扫描 out-dir |
| G8 | 契约要求 preview 时预览存在；非 success 状态必须带 uncertainty | 诚实披露 |

`check_contract.py` 从磁盘独立重扫，不信任 result.json 自述：
`exit 0 + {"valid": true}` 才视为门通过。

## 产物文件名（相对 /app/output）

| 角色 | 文件 |
|-|-|
| 可编辑源 | `<case_id>_deck.pptx` |
| 封面预览 | `<case_id>_cover_preview.png`（PIL 示意图） |
| 全册预览 | `<case_id>_slides_contact_schematic.png`（PIL 示意图联系表） |
| 结构化结果 | `result.json` |
| 页结构方案 | `spec.json`（deckplan，可复跑核对） |
| **适配方案（v2）** | `adopt_plan.json`（模板审计 + 版式分配 + 批量规则 + 图表计划） |
| 抽取结果 | `content.json`（实体/主张/图/表 + 来源定位） |
| 自查报告 | `audit.json` / `render_log.json` / `summary.txt` |
| 回退模板（条件产物） | `_runtime/builtin.pptx`（案例未给模板/起始 deck 时**运行时生成**） |

> 渲染说明：运行环境无 LibreOffice/PPT 时**不产出伪 PDF**——预览为按同一
> 页计划绘制的 PIL 示意图并明确标注（`preview_is_schematic: true`、
> `_PREVIEW_ARE_SCHEMATIC.txt`、`render_log.json`）；真实像素级/PDF 导出需
> PowerPoint 或 LibreOffice，能力缺失如实记录，不静默成功。

## 校验方式

```bash
SKILL_DIR=<本包根目录>          # 平台装到 /skills/weekly-skill；任意 cwd 均可
python "$SKILL_DIR"/scripts/validate_result.py --case /input/case.json --result /app/output/result.json
# VALID 即契约通过；退出码 0

python "$SKILL_DIR"/scripts/check_contract.py --result /app/output/result.json \
    --out-dir /app/output --case /input/case.json
# {"valid": true} 且退出码 0 即 G1–G8 全过（CP3 交付门）
```

## 资源形态与产物（为什么包里没有 .pptx / .png）

题面硬约束：*Skill resources: at most 50 UTF-8 text files, 500KB each and
2MB total, no symlinks* ⇒ 本 Skill 包**只含文本资源**；`deck.pptx`、预览 PNG、
回退模板等二进制都是**运行时产物**（写进 `--out`），与正式案例的产物形态一致。
`result.json` 是**唯一评分产物**：产物清单（含 sha256）、页级证据映射、模板审计、
适配方案摘要、审计检查与 CP3 门都收在这一份里；产物本身损坏或缺失由
`check_contract.py` 的 G4/G7 当场判失败。

## status 的诚实语义

- **success**：全部检查 ok（含 CP3 G1–G8）；
- **partial**：存在 warn/fail（如源图缺失占位、模板回退、adopt-plan 偏差、
  溢出未能完全消除、预览仅为示意图、契约门未全过），脚本仍写出全部产物与
  明细，绝不把失败伪装为成功；
- **failed**：case 无法解析、无可用模板或渲染异常；仍写出含 pipeline fail 的
  result.json（`uncertainty` 记录异常），工作不丢失。
---

## 附：字段由哪个机制保障、在哪一层可证伪（v3 机制显性化版补充）

> 本节只**补充说明**字段与机制的关系，**不改变上文任何字段名、类型或结构**。
> 机制定义与"没有它会怎样"见 `references/MECHANISM.md`；复用方式见
> `references/REUSABLE-ASSETS.md`。

### 字段 → 机制 → 可证伪判据

| 字段 | 守护它的机制 | 被抽掉后字段会怎样 | 可证伪判据（复跑即可） |
|-|-|-|-|
| `adopt_plan`（`source` / `pages_assigned` / `layout_gaps` / `batch_deviations` / `figure_plan` / `gates`） | **M1** | 整块缺失（阶段二不消费方案时**不会**出现"假装 0 偏差"的字段） | 不传 `--adopt-plan` 跑阶段二 → `.build_audit.json` 里无 `adopt_plan_*` 字段 |
| `verification.contract_gates[]` | **M2** | 无门可判，交付完整性只能靠人眼 | 删掉一个产物 → G7 `missing=[...]`、`exit 1` |
| `slide_evidence[].evidence[].loc` | **M3** | 页面允许无来源内容，覆盖率归零 | 抽 3 条 `loc` 到材料对应行核对 |
| `template_audit.adopt_plan_applied` / `adopt_plan_deviations[]` | **M4** | 方案与执行脱钩，无从测偏差 | 篡改某页 `recommended_layout_idx` → `applied` 下降、`deviations` 出现 |
| `artifacts[]`（含 `_runtime/builtin.pptx` 等运行时产物） | **M5** | 必须往包里塞二进制 ⇒ 可能整包被拒收 | 包内 `find` 0 命中 ⌆ 运行后产物齐全（两条同时成立） |
| `<case_id>_deck.pptx` 与两张 PNG 的 sha256（`artifacts[].checks`） | **M6** | 哈希每次变化，回归比对失效 | 同输出目录连跑两次 → deck 与 PNG 哈希相同 |
| `template_audit.layout_used[]` / `theme` | **M1 + M4** | 继承关系不可查，"模板是否真被套用"无法回答 | 抽查页型对应的版式名是否与 `adopt_plan` 推荐一致 |
| `uncertainty[]` | **M2**（G8 强制） | 降级被静默，`partial` 与 `success` 无法区分 | 非 `success` 且 `uncertainty` 为空 → G8 fail |
| 契约回显的其余键（禁 `null`） | **M2**（G3 强制） | 出现 `null` 占位 → 字段语义丢失 | `null_placeholders=[]` 且顶层 null 个数 = 0 |

### 字段的两类读者

1. **交付读者**（评审 / 复跑者）：关心字段能否回答"模板是否被真实套用、内容与来源
   是否对得上、整册能否被复跑"—— 即上文 §顶层字段到 §CP3 的那几张表。
2. **复用读者**（拿走一层机制的人）：关心字段的**产生条件**与**退化症状**，也就是
   本节的表。例如只想用"证据定位"这一层的人，需要知道 `evidence[].loc` 由
   `scripts/extract.py` 产出、由 `scripts/audit.py` 的
   `traceability.evidence_loc` 检查兜底（见 `references/REUSABLE-ASSETS.md` §4）。

### 字段与复用资产的对应

| 字段所在层 | 复用资产 |
|-|-|
| `template_audit.*` / `figure_adjust` | 资产 A 模板适配层（`pptx_toolkit.py` + `adapt_pptx.py`） |
| `adopt_plan` / `gates` | 资产 B 阶段一方案器（`adopt_plan.py`） |
| `slide_evidence` 的页型与顺序 | 资产 C 确定性页计划器（`deckplan.py`） |
| `verification.checks` / `contract_gates` | 资产 D 审计与契约工具（`audit.py` / `validate_result.py` / `check_contract.py`） |
| `_runtime/builtin.pptx` 的存在与否 | 资产 E 运行时资源生成器（`make_template.py` / `make_synthetic_inputs.py`） |
| `output_contract` 回显的形状 | 资产 F 示例题集与页级金标准（`examples/case.json`） |

> **维护提醒**：新增或改动字段时，除更新上文表格，还要同步检查
> `references/MECHANISM.md`（该字段由哪个机制保障）与
> `references/REUSABLE-ASSETS.md`（该字段属于哪件可复用资产）。三份文档对同一字段
> 的描述若不一致，以本文件（契约）为准，并当场修正另两份。
