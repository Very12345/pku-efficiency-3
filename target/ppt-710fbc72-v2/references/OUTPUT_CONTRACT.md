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
| `artifacts` | array | 是 | 产物清单（role/format/path/abspath/checks sha256；**不含 result.json 自身**，避免自引用哈希破坏确定性） |
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
| `template_source` | 实际打开的模板绝对路径（case 模板 / starting deck / 内置回退） |
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
- `render`：`render_log.json` 全文（渲染后端、字体探测、诚实说明）。
- `traceability`：`{evidence_loc_frac, contract_ok, hashes{spec, adopt_plan}}`。
- `contract_gates`：**v2 CP3 硬性门 G1–G8**（见下），每条 `{gate, ok, detail}`。

## CP3 硬性门（G1–G8，`scripts/check_contract.py` 独立复查）

| 门 | 含义 | 判定 |
|-|-|-|
| G1 | case_id 存在且与 case.json 一致 | 逐字相等（case 提供时） |
| G2 | status ∈ {success, partial, failed} | 诚实词汇 |
| G3 | output_contract 全部键回显顶层且无 null 占位 | 缺失/空占位即失败 |
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

> 渲染说明：运行环境无 LibreOffice/PPT 时**不产出伪 PDF**——预览为按同一
> 页计划绘制的 PIL 示意图并明确标注（`preview_is_schematic: true`、
> `_PREVIEW_ARE_SCHEMATIC.txt`、`render_log.json`）；真实像素级/PDF 导出需
> PowerPoint 或 LibreOffice，能力缺失如实记录，不静默成功。

## 校验方式

```bash
python <skill_root>/scripts/validate_result.py --case /input/case.json --result /app/output/result.json
# VALID 即契约通过；退出码 0

python <skill_root>/scripts/check_contract.py --result /app/output/result.json \
    --out-dir /app/output --case /input/case.json
# {"valid": true} 且退出码 0 即 G1–G8 全过（CP3 交付门）
```

## status 的诚实语义

- **success**：全部检查 ok（含 CP3 G1–G8）；
- **partial**：存在 warn/fail（如源图缺失占位、模板回退、adopt-plan 偏差、
  溢出未能完全消除、预览仅为示意图、契约门未全过），脚本仍写出全部产物与
  明细，绝不把失败伪装为成功；
- **failed**：case 无法解析、无可用模板或渲染异常；仍写出含 pipeline fail 的
  result.json（`uncertainty` 记录异常），工作不丢失。