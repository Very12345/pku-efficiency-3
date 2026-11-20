# QUALITY_GATES.md — 质量门 G1–G10（全链路收口）

> 对应高分 intent 的 `quality-gates.md`（76594 系 08-quality-gates 形态）。G1–G10 把
> "评委看到的每一页论断可溯源、可编辑、可复核"落实为**可执行检查**；每个门都有
> 对应脚本/文件与独立复核命令（`TEST.md` 记实测）。

## 门清单

| 门 | 检查内容 | 执行者 | 违例的影响 |
|-|-|-|-|
| G1 | `result.json` 存在且 `case_id` 与输入一致 | validate_result | status→partial + uncertainty |
| G2 | output_contract 声明字段全部在场且类型正确（四形态，禁 null） | check_contract | 同上 |
| G3 | pages 非空；页编号 1..N；页数 == slide_target | validate_result + validate_plan(P2/P3) | 同上 |
| G4 | 计划门 P1–P8 全过 | validate_plan → plan_gates.json | 同上 |
| G5 | 每页 claim 能溯源：source_file 已声明 + 引文逐字在源文本中（derived 页按概括语如实记录） | evidence_audit → evidence_audit.json | 同上 |
| G6 | deck 可打开、页数 == 计划、每页有备注与 claim 元素、OPC 完整 | verify_deck → deck_audit.json | 同上 |
| G7 | 图绑定状态记录（真实图片 vs 诚实占位框） | verify_deck + evidence_audit | 记录并展示，不误报为真实图 |
| G8 | 预览 PNG 存在且每张带"PIL 模拟预览"水印；preview_manifest 说明限制 | render → previews/ | 预览失败 → partial（deck 仍是主交付） |
| G9 | 确定性：talk_plan/evidence_map 内容投影 sha（剔除记录性时间戳）+ deck 规范化 sha；双跑一致或如实记录 | finalize_result + selftest | 不能声称"字节级确定性"之处如实说明 |
| G10 | 包约束：≤50 UTF-8 文本文件、单文件 ≤500KB、总 ≤2MB、无符号链接、无 __pycache__ | selftest --package-check | 打包前必须通过（平台硬约束） |

## 执行链（一次 main.py 运行）

```
case.json/task.md/材料 ─▶ [CP1] ─▶ scaffold_plan ─▶ validate_plan (P1–P8=G4)
   ─▶ deck_builder ─▶ verify_deck (G6=G7) ─▶ render (G8)
   ─▶ evidence_audit (G5) ─▶ finalize_result (G1–G3, G9) ─▶ self_check.json
   ─▶ selftest 复核 (G1–G10)
```

G 门快照写入 `result.audit.gates` 与 `self_check.audit_gates`，随结果归档。

## 独立复核（全部退出码 0 = 通过）

```bash
python scripts/validate_result.py <out>/result.json
python scripts/check_contract.py  <out>/result.json
python scripts/evidence_audit.py  <out>/result.json
python scripts/verify_deck.py <out>/editable_deck.pptx --expect-pages <N> --plan <out>/talk_plan.json
python scripts/selftest.py <out> --package-check <skill-root>
```