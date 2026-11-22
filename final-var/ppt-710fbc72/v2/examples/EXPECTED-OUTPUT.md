# EXPECTED-OUTPUT — 示例案例上应产出的文件与契约字段（文字版）

> 本文件**替代**原先随包分发的二进制示例产物（`examples/output/*.pptx`、
> `*.png`）。原因：题面硬约束是 *"Skill resources: at most 50 UTF-8 text files,
> 500KB each and 2MB total"* —— 二进制资源不进包；它们由脚本**运行时生成**，
> 与正式案例的产物形态完全一致。运行记录见 `TEST.md`。

## 一次运行（`scripts/main.py`）应在 `--out` 目录留下

| 文件 | 形态 | 示例案例上的实测内容 |
|-|-|-|
| `example-catalyst-201_deck.pptx` | 可编辑 PPTX（二进制，运行时生成） | 10 页 = 目标页数；逐页套用模板版式（占位符继承）；2 张图等比 contain-fit（`figure_adjust` 记录缩放比、`aspect_preserved=true`）；原生表格；逐页 speaker notes；页脚+页码自第 2 页起统一 |
| `example-catalyst-201_cover_preview.png` | PNG 预览（二进制，运行时生成） | 1280×720，封面版式，含 `SCHEMATIC PREVIEW (PIL)` 免责标注 |
| `example-catalyst-201_slides_contact_schematic.png` | PNG 预览（二进制，运行时生成） | 全册联系表，每页一格（标题 + 主张 + 图表引用） |
| `spec.json` | JSON（文本） | 确定性页结构方案：10 页，页型 cover→background→methods→results×3→conclusion→discussion→evidence_map→thankyou；每页 claims / figure_refs / table_refs / notes / evidence(claim,loc) |
| `adopt_plan.json` | JSON（文本） | **阶段一适配方案**：模板结构审计（1 母版 / 11 版式 / 占位符 idx·name·宽高 / 画布 EMU / 主题字体与 12 个主题色）、10 页版式分配、批量规则 0 偏差、3 条图表放置计划、`gates` 全 ok |
| `content.json` | JSON（文本） | 规范化抽取：主张/图/表/关键数值均带 `文件:行` 定位；`sources[]` 含行数与 sha256 |
| `audit.json` | JSON（文本） | **在真实产物上**的 21 条自查全 `ok`（重开/页数/主张覆盖/图号交叉引用/备注/溢出/页脚/预览签名/证据覆盖率/方案↔执行一致性/契约与契约门） |
| `render_log.json` | JSON（文本） | 渲染后端 `PIL`（无 LibreOffice/PPT → 不产伪 PDF）、实际解析到的字体文件名与候选数、诚实说明 |
| `result.json` | JSON（文本） | **唯一评分产物**，字段见 `references/OUTPUT_CONTRACT.md`；示例运行 `status=success`、`verification.contract_gates` 8/8 ok |
| `summary.txt` | 文本 | 一屏摘要（case_id / status / 页数 / 方案套用 / 产物名 / 图数 / 检查数） |
| `_PREVIEW_ARE_SCHEMATIC.txt` | 文本 | 预览为示意图的说明（与 PNG 同目录，防误读） |
| `_runtime/builtin.pptx` | PPTX（二进制，运行时生成） | 案例未给模板/起始 deck 时**现场生成**的回退模板（16:9，真实母版/版式/占位符）；已给模板时不使用 |

## `result.json` 顶层字段（示例案例上实测）

信封字段（见 `OUTPUT_CONTRACT.md` 全表）：
`case_id` `skill` `status` `workorder` `task_summary` `title` `subtitle` `audience`
`duration_minutes` `language` `slide_count` `main_result` `artifacts` `slide_evidence`
`template_audit` `adopt_plan` `verification` `sources` `uncertainty` `change_records`
`status_notes` `generated_at` `generator` `tool_versions`

案例自带 `output_contract` 的回显（示例案例声明了 7 个键，全部镜像到顶层且非空）：

| 契约键 | 示例运行的值 | 取值方式 |
|-|-|-|
| `template_inheritance` | `true` | 由 `template_audit.opened_from` + `layout_used` 实际推出 |
| `slide_count` | `10` | 原生字段（实际生成页数） |
| `audience` | `"催化方向课题组组会"` | 原生字段（来自 case/task） |
| `language` | `"zh"` | 原生字段 |
| `evidence_per_slide` | `true` | 由 `slide_evidence`（10 页逐条）推出 |
| `notes_per_slide` | `true` | 由 `main_result.notes_pages`（10/10）推出 |
| `preview_png` | `true` | 由 `main_result.previews` + 实际 PNG 推出 |

> 派生结果同时记在 `verification.contract_echo_derived`，便于核对"这个 `true`
> 是从哪里来的"。**PDF 类字段恒为 `false`**：无 PowerPoint/LibreOffice 时不产
> 伪 PDF —— 这是唯一允许为 `false` 的能力项，且在 `uncertainty` 中说明。

## 与随包文本产物的对应关系

`examples/output/` 内保留的是**文本**产物（`result.json` / `summary.txt` /
`render_log.json` + 两个说明文件），它们就是上面这张表在本示例案例上的真实
运行结果（同一 `scripts/` 代码、同一 `examples/case.json`、同一提交版本）。
页结构方案与适配方案的样例另存为 `examples/plan.sample.json` 与
`examples/adopt_plan.sample.json`（内容与运行时 `spec.json` / `adopt_plan.json`
同构，仅 `_meta` 标为示例）。

二进制产物（pptx、两张 PNG、`_runtime/builtin.pptx`）不随包分发，一条命令即可重建：

```bash
SKILL_DIR=<本包根目录>; RUN=<任意可写目录>
cp -r "$SKILL_DIR/examples" "$RUN/examples"
python "$SKILL_DIR/scripts/make_synthetic_inputs.py" --dir "$RUN/examples"
python "$SKILL_DIR/scripts/main.py" --case "$RUN/examples/case.json" \
    --task "$RUN/examples/task.md" --out "$RUN/out"
```

`$RUN/out/` 应出现上表全部文件；`result.json` 的 `status` 为 `success`、
`verification.contract_gates` 的 G1–G8 全 `ok`（否则按
`references/failure-modes.md` 的对应行处置，并把偏差写进 `uncertainty`）。
