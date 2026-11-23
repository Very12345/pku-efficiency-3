# checklist.md — 适配检查清单（收尾验收，逐项勾选）

与 `scripts/audit.py` 的检查一致：**每完成一次适配/构建后逐项核对**。每项给出
`检查名（对应 audit check id）→ 通过判据 → 不通过时怎么处理（D 规则）`。
正式案例运行后，本清单的核对结果落在 `audit.json.checks` 与
`verification.contract_gates`（机器可复核，不是口头自述）。

## A. 输入真实性（先决条件）

- [ ] A1 读取的是真实文件：`case.json` / `task.md` / 材料 / 模板，不是凭标签
      假设内容（`extract.py`、`sources`）
- [ ] A2 每个主张/数值带来源定位 `file:line` 或 `case.json[字段]`；材料中
      找不到源头的数值**不上页面**，进 `uncertainty`（`traceability.evidence_loc`）

## B. 模板套用（母版 / 版式 / 占位符继承可查）

- [ ] B1 模板来源与回退原因有记录：`template_audit.opened_from` /
      `template_errors`（模板损坏回退内置，如实记录）——audit `artifact.*.exists`
- [ ] B2 母版/版式/占位符枚举完整：`adopt_plan.json.template.layouts` 含
      每个版式的 idx/name/占位符——audit `adopt_plan.gates`（G2）
- [ ] B3 每页按方案套用版式：`template_audit.adopt_plan_applied` =
      `adopt_plan_total_pages`，偏差为 0 或已逐条记录——audit
      `adopt_plan.consistency`
- [ ] B4 缺占位符时手绘文本框替代并记录（`layout_fallback_used`），
      不静默降级——audit `layout.overflow` / D6

## C. 内容与来源一致性

- [ ] C1 页内文字/数字/图号与源材料一致（抽查 ≥3 处）——audit
      `content.claim_coverage`
- [ ] C2 图号与正文引用一致：正文引用 ⊂ 图清单（`xref.figure_refs`），
      图清单 ⊆ 结果页放置（`xref.figure_placement`）
- [ ] C3 图表等比 contain-fit，不拉伸（`figure_adjust.aspect_preserved`、
      `adopt_plan.figure_plan`）
- [ ] C4 逐页 speaker notes 存在（audit `notes.present`），含封面/收尾页

## D. 版式与整册一致性（批量规则）

- [ ] D1 页脚/页码全册一致（audit `layout.footer_uniform`）；标题位置/留白/
      字号层级按 batch-rules.md 统一（`adopt_plan.batch.deviations`）
- [ ] D2 无静默字号压缩：溢出报告 `layout.overflow`，落底记录
      `layout.font_floor`（12pt 下限）

## E. 导出与契约

- [ ] E1 pptx 可被 python-pptx 重开（`pptx.reopen`）、页数 = `spec.json`
      （`pptx.slide_count`）
- [ ] E2 预览 PNG 存在且非空白（`preview.*`）；渲染后端/字体回退在
      `render_log.json` 如实记录（`preview_is_schematic`）
- [ ] E3 `result.json` 含 output_contract 全部字段 + case_id + status +
      sources + uncertainty + change_records（`result.contract`）
- [ ] E4 CP3 契约门 G1–G8 全过（`result.contract_gates` 全部 ok）——
      `scripts/check_contract.py` exit 0
- [ ] E5 status/uncertainty/change_records 诚实，无编造软件状态或科学数据

## 核对入口

```bash
SKILL_DIR=<本包根目录>          # 平台装到 /skills/weekly-skill；任意 cwd 均可

# 1) 审计（真实产物自动检查；--out 是目录）
python "$SKILL_DIR/scripts/audit.py" --content <out>/content.json --spec <out>/spec.json \
    --out <out> --build-audit <out>/<case>_deck.build_audit.json

# 2) 契约校验 + CP3 硬性门（两项都必须 exit 0）
python "$SKILL_DIR/scripts/validate_result.py" --case <case> --result <out>/result.json
python "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json \
    --out-dir <out> --case <case>
```

> 首次运行前的资源准备（包里没有二进制）：案例未给模板时先
> `python "$SKILL_DIR/scripts/make_template.py" --out <run>/builtin.pptx`；
> 跑自带示例时先 `python "$SKILL_DIR/scripts/make_synthetic_inputs.py" --dir <示例目录>`。

> 全部项打勾 ≠ 得满分；它只证明本 Skill 的自查与该做的一致。评审对"内容是否
> 与源论文对得上、模板是否真实套用"另有独立核对路径（`adopt_plan.json` +
> `slide_evidence` + `template_audit` 逐页可查）。