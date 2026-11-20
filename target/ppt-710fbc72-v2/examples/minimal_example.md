# 最小示例（示例，非正式案例）

本目录演示 Skill 的最小调用接口；**所有内容均为合成示意数据，不是任何真实
论文结果，平台正式案例由组织方提供**。

## 输入

| 文件 | 作用 |
|-|-|
| `case.json` | 最小案例：Cu-ZnO/γ-Al₂O₃ 催化剂 CO₂ 加氢制甲醇（合成数据），10 页 / 12 分钟 / zh，带 `output_contract`（7 个契约键） |
| `task.md` | 任务说明（示例） |
| `material.md` | 材料原文（含 `# 方法/结果/…` 小节与图注，供 `file:line` 定位） |
| `figs/fig1.png` `figs/fig2.png` | 两张示意位图（合成） |

## 调用方式

```bash
# 一键全流程（两阶段：方案 → 执行 → 验证）
python scripts/main.py --case examples/case.json --task examples/task.md --out <out>
```

## 示意输出（真实运行产物，见 examples/output/）

| 文件 | 说明 |
|-|-|
| `_LABEL_example.txt` | 本目录"示例"标注 |
| `<case>_deck.pptx` | 可编辑源（10 页、逐页备注、页脚页码、图表 contain-fit） |
| `<case>_cover_preview.png` | 封面预览（PIL 示意图，见文件内 SCHEMATIC 标注） |
| `<case>_slides_contact_schematic.png` | 全册联系表示意图 |
| `result.json` | 结构化结果（output_contract 7 键全部回显顶层 + case_id/status/sources/uncertainty/change_records；status=success） |
| `spec.json` | 页结构方案（与 pptx 同一计划，复跑可核对） |
| `adopt_plan.json` | **适配方案**（模板审计 + 页→版式分配 + 批量规则 + 图表计划） |
| `content.json` / `audit.json` / `render_log.json` / `summary.txt` | 抽取 / 自查 / 渲染日志 / 摘要 |

方案样例（`plan.sample.json` / `adopt_plan.sample.json`）即由上述真实运行生成
并加注"示例"标识，不是预制答案。

## 验证命令

```bash
python scripts/validate_result.py --case examples/case.json --result examples/output/result.json   # VALID
python scripts/check_contract.py  --result examples/output/result.json --out-dir examples/output --case examples/case.json  # {"valid": true}
```