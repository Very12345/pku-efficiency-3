# sample-output/ — 示例输出快照（示例，非正式案例）

本目录是 `examples/case.json` 一次真实运行的输出快照，**仅供演示接口与说明
输出形态**，不构成任何正式案例结果：

- `result.json` —— 结构化结果（case_id、deck、evidence、previews、sources、
  uncertainty、change_records 等，output_contract 字段已镜像）
- `evidence_map.md` —— 页级证据映射（人读版）
- `manifest.json` —— 全部输出文件 sha256 清单
- `deck.pptx` —— 可编辑演示文件（6 页，每页含演讲备注与证据脚注）
- `preview/slide_01.png`、`preview/slide_05.png` —— PIL 预览（非 PowerPoint 导出）
- `preview/preview.pdf` —— reportlab 逐页文本预览（非 PowerPoint 导出）

生成命令：

```bash
python scripts/main.py --case examples/case.json --out D:/BuildTemp/smoke-ppt-6ad93034
```

> 完整输出（work/plan.json、table_cache、logs、逐页 preview/*.png）位于
> 每次运行的实际输出目录，这里只保留最小可读子集以控制包体积。