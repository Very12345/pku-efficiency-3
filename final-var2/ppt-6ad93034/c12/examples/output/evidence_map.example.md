# 页级证据映射

> 案例: ppt-6ad93034-example-001 · 状态: partial · 由 result.json 的页级模型生成（双形态：本 md + evidence_map.json 机器可读）。
> “证据缺失”为显式标注（gap），不是作者无中生有。

| 页 | 角色 | 标题 | 证据定位 | 状态 |
|---|---|---|---|---|
| P01 | 封面 | 基于注意力机制改进的蛋白质二级结构预测（虚构示例材料） | EVIDENCE GAP（已显式标注） | gap |
| P02 | 主线与贡献 | 汇报主线 | 摘要/引言、摘要/结论 | mapped |
| P03 | 研究问题 | 研究问题 | 引言 | mapped |
| P04 | 方法 | 方法 | §方法 | mapped |
| P05 | 结果 | 结果 | 表(results)、列=Q3 (%) | mapped |
| P06 | 结论与展望 | 结论与下一步 | §结论 | mapped |

> 预览为 PIL/reportlab 近似渲染（非 PowerPoint 导出），见 previews/。