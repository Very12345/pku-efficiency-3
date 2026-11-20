# examples/ — 最小调用示例

> ⚠ **这些文件是「示例，非正式案例」**，仅用于演示 Skill 接口与最小调用流程，
> **不参与正式评分**。正式测试案例、白板由平台提供。

## 内容

- `case.json` — 结构化案例：CRISPR 文库筛选技术路线（route 图，10 实体 9 关系，
  三阶段：文库构建→筛选→鉴定）；
- `task.md` — 示例任务说明与虚构材料（节选，标明为示例）。

## 调用

```bash
python scripts/main.py --case examples/case.json --task examples/task.md --out <输出目录>
```

示意输出（运行后生成）：`figure.svg`（可编辑源文件）、`figure.png`、`figure.pdf`、
`layout.json`、`result.json`。result.json 中的 `case_id` 为 `demo-biotech-route-01` 且
标题含「示例」，产出属示意输出，不冒充正式案例结果。

## 直接读取已生成的示意输出

如不想重新运行，可直接查看运行记录 `TEST.md`（含命令与产物清单），或
重新执行上述命令得到同一组文件（布局确定性，可复现）。