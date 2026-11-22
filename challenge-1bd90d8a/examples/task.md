# 任务说明（示例，非正式案例）

> 本文件是 Skill 自带的**最小示例**，用于演示调用方式、CP1–CP6 全链路与
> 契约四形态回显；正式评分使用平台固定的 3 个案例，二者无关。
> 所有示意输出均标注为示例。

## 任务

依据 `data.csv` 和 `entities.json`（另附 `material.md` 生物源材料样例）生成两张
可投稿的科研图稿，并交付可编辑源文件与预览：

1. **Figure 1（panel）**
   - 面板 A：24 h 时间点下不同剂量（0/1/5/20 mg/kg）肿瘤体积的柱状图，带 SE 误差线，
     并标注 0 与 20 mg/kg 组的显著性（**，p=0.004，来源见源材料）。
   - 面板 B：时间曲线（0 h 与 24 h），按剂量分组成系列。
2. **Figure 2（network）**：按 `entities.json` 的实体与关系画出 Wnt 信号通路简化机制图，
   激活用箭头、抑制用阻滞线，每个节点标注其来源图表编号（cite）。

## 数据与图面约束

- 每个图元必须能回到源数据的列与行（data-* 溯源 / data_manifest.json / mapcheck）。
- 轴标签必须带单位；误差线须注明含义（本示例为 SE，n=6）。
- 显著性只转述材料已给的 p 值并注明来源（本 Skill 不代算统计量）。
- 实体名以材料原文为准（如 β-catenin、LRP5/6），不"修正"拼写。
- 交付：可编辑分层 SVG + PNG 预览 + PDF 预览；中文字体缺失时须在结果中如实记录。
- 输出：result.json（含 output_contract 全部字段 + case_id），
  status/sources/uncertainty/change_records/checkpoints/gates 如实填写。