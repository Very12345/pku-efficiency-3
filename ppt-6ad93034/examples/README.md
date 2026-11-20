# examples/ — 最小调用示例

本目录是一组**示例**输入（`case.json` + `task.md` + `material.md` +
`results.csv`），用于演示完整调用流程。**材料全为虚构**，任何输出都标注
"示例，非正式案例"，不得冒充平台正式案例结果。

## 运行

```bash
# 在技能根目录（含 SKILL.md 的目录）下运行：
python scripts/main.py --case examples/case.json --out D:/BuildTemp/smoke-ppt-6ad93034
python scripts/check_contract.py D:/BuildTemp/smoke-ppt-6ad93034/result.json examples/case.json
```

依赖（本机 python 3.13 / Anaconda 已验证）：`python-pptx>=0.6.21`、
`matplotlib>=3.5`、`Pillow>=9`、`numpy`；`reportlab` 可选（缺 PDF 预览自动跳过）。

## 演示局部编辑与版本记录（演示稿迭代）

```bash
python scripts/main.py --case examples/case.json \
    --out D:/BuildTemp/smoke-ppt-6ad93034-edit \
    --edit examples/edit_demo.json --version v2
```

`edit_demo.json` 演示：改一条主张、加一条备注、重排页面顺序；每次修改在
`changelog.jsonl` 与 `result.json.change_records` 各记一条，`deck_v2.pptx`
与 `deck.pptx` 并存以便对比回退。

## 输出结构（示例）

- `work/plan.json` —— 页面模型（页序 + 叙事角色 + 主张 + 证据），可编辑源
- `work/deck.pptx` / `deck_v2.pptx` —— 可编辑演示文件（python-pptx 生成）
- `work/preview/slide_*.png` + `preview.pdf` —— 预览渲染（PIL/reportlab，标注"非 PowerPoint 导出"）
- `work/table_cache/` —— 源数据表副本（原生表格回退用）
- `result.json`、`evidence_map.md`、`changelog.jsonl`、`manifest.json`、`logs/`

（`sample-output/` 内为一次真实运行的输出快照，标注为示例。）