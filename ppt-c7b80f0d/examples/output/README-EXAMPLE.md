# examples/output — 示意输出（示例，非正式案例）

本目录是 `examples/case.json` + `examples/deck-spec.json` 跑通后的**示意产物副本**，
文件名统一带 `.example.` 标记。**它们不是、也不代表平台正式 3 个固定案例的输出**；
正式案例由平台提供，Skill 在运行时依据实际输入重新生成全部产物。

| 文件 | 说明 |
|-|-|
| `academic_deck.example.pptx` | 可编辑演示源（8 页：标题 + 6 内容 + 致谢；演示用示例组织方模板 template-example.pptx 的版式） |
| `result.example.json` | 结构化的 result.json（含 output_contract 全部字段回显 + case_id），运行时输出格式示例 |
| `evidence_mapping.example.md` | 页级证据映射（每页 → 论文 p.1–p.4 的图/表/章节定位） |
| `preview-approx-cover.example.png` | 封面预览（PIL 近似渲染，非 PowerPoint 渲染；正式产物为每页 preview-approx-*.png） |
| `chart-Fig_1.example.png/.svg` | 从 Table 1 数字重建的示例图（PNG 嵌入 deck，SVG 为可编辑源，标注 reconstructed_from_table） |

复跑命令（需要在仓库根/本目录所在 Skill 根）：

```bash
python scripts/main.py --case examples/case.json --spec examples/deck-spec.json \
  --out <某个空输出目录>
python scripts/validate.py --result <输出目录>/result.json --out-dir <输出目录> \
  --case examples/case.json
```

注意：`examples/materials/paper-mini.txt` 为**合成示例论文**（人物/机构/数据均虚构），
仅用于演示接口；`examples/template-example.pptx` 为**示例模板**（含 1 个起始页，
运行以 template_mode=replace 移除，仅留版式）。正式运行时 Agent 必须依据案例
实际提供的论文与模板重新生成全部内容。