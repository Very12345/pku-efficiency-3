# plan-contract.md — 计划契约（plan contract，P1–P8）

> 对应高分 intent 的 `plan_contract.md` + `plan-schema.md` 组合：**先定方案契约，再按契约生成**。
> 机器形式：`assets/plan.schema.json`（单点真相）；执行者：`scripts/scaffold_plan.py`（产出）
> + `scripts/validate_plan.py`（门控）；产物：`<out>/talk_plan.json` + `<out>/plan_gates.json`，
> 并随 `result.json` 的 `audit.plan_gates` / `self_check.plan_gates` 归档。

## 0. 为什么先有计划契约

汇报内容组织的质量不在"生成了多少页、套了多少模板"，而在**取舍是否可复核**：
页数为何是这些、每页唯一主张是什么、证据在哪、顺序为何服务于听众与时长。
计划契约把上述取舍**固化成可机器校验的字段与门**，生成阶段只做执行；
"先计划后生成"的流水线是高分管线的共同思路（intel 该题：plan_contract + plan-schema +
scaffold/validate 脚本对）。

## 1. 计划(json) 的顶层必填字段

`scaffold_plan.build_plan(case, material_records, talk_config, change_records)` 产出：

| 字段 | 说明 |
|-|-|
| `case_id` | 输入标识 |
| `report_goal` | 报告目标（默认按汇报类型给成功标准） |
| `audience` | `{description, expertise ∈ {expert,familiar,lay}, background_ratio, evidence_depth, notes}` |
| `timing` | `{duration_min, slide_target, seconds_per_slide}` |
| `narrative` | `{report_type, order_blocks[], template}`（顺序来自 talk_config，非论文目录） |
| `success_criteria` | 目标可检查化（列表） |
| `pages` | 页级计划（见 §2） |
| `question_bank` | 问答预演（追问卷） |
| `terminology` | `{assumed[], explain_on_page[], glossary[]}`（听众适配的术语层） |

## 2. 页级契约（schema 的 `page` 段）

每页字段：`page_no / block / block_label / title / claim / one_liner / evidence[] /
figure_ref / figure_file / notes / strength / qa[] / derived`。

- `block ∈` 词表：title, agenda, motivation, background, method, results,
  conclusion_risk, innovation_limits, conclusion, qa。
- `strength ∈` {strong, medium, weak, null(结构性页)}。
- 内容块（非 title/agenda/qa）必须带 `evidence[0]`（locator/quote/source_file/strength）。
- `derived=true` 表示该页是"材料无直接主张 → 用章节首段概括"（证据强度 weak）。
- 长度约束：title ≤ 40、claim 6–500、one_liner ≤ 64（见 `templates/talk_config.json` 的
  `deck_rules`；validate_plan 强制 claim 范围）。

## 3. 计划门 P1–P8（validate_plan 执行）

| 门 | 内容 | 违例处理 |
|-|-|-|
| P1 | 顶层必填字段齐全且类型正确 | 记录 errors；继续生成但 status→partial |
| P2 | 页编号 1..N 连续无重复 | 同上 |
| P3 | `len(pages) == timing.slide_target`（冻结页数） | 同上（页数以任务为准，不跟随论文章节） |
| P4 | 每页 `block` ∈ 词表 | 同上 |
| P5 | 内容页 `evidence[0]` 含 locator/quote/source_file/strength | 同上 |
| P6 | 证据 `source_file` ∈ 本次材料清单 | 同上 |
| P7 | 每页 title/claim/one_liner 非空；claim 长度与 strength 词法正确 | 同上 |
| P8 | notes 含【讲解】行；derived 页 strength=weak | 同上 |

验证器由 schema 驱动（`gates` 段 + `page` 段 + `properties` 段），改 schema 即改行为。

## 4. 与 result 的衔接

`finalize_result.py` 把 `plan_gates` 嵌入 `result.audit.plan_gates` 与
`self_check.plan_gates`。计划未过门 → `uncertainty` 明确列出
（"计划门 P1–P8 未全过，已如实降级为 partial"），不静默吞掉。

## 5. 独立复核

```bash
# $SKILL_DIR = 本包根目录（含 SKILL.md）
python "$SKILL_DIR/scripts/validate_plan.py" <out>/talk_plan.json --materials-dir <case材料目录>
# 退出码 0 = P1–P8 全过；输出 plan_gates 报告
```