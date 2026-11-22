# 任务说明 · 案例 B（Mg-Zn 合金体外降解，合成数据）

> 本案例是 Skill 自带的**合成案例**（非平台正式案例）。数据与机制描述均为演示用文本。

## 任务

依据 `data.csv`（4 种合金）与 `material.md`（机制/通路来源）产出**两张图**：

1. **Figure B1（scatter）**：Zn 含量（wt%）vs 降解速率（mm/year），带 **SD** 误差线，
   轴标签带单位；每个点标注合金 `alloy_id`。
2. **Figure B2（network）**：按 `material.md` 的 `ENTITY:` / `REL:` 行绘制产物膜机制图，
   节点按 group 分层（Bulk / Microstructure / Surface film / Aqueous / Cell），
   每个节点带 `cite` 来源标注；抑制类关系用阻滞线、促进类用箭头。

## 数据与图面约束

- 误差线语义**必须**按源表/材料标明：Figure B1 为 SD（列 `sd_rate`），
  成骨细胞活力若上图则为 SE（列 `se_viability`）——**不得混用**。
- 实体名与关系名照抄 `material.md` 原文（含 `Cl-`、`Mg(OH)2`、`MgZn2`、`MC3T3-E1`）。
- 未被任何图引用的列（`ph_day7`、`viability_percent`）仍须在 `sources[].columns` 里如实记录。
- 机制图的节点/关系只在**显式行**中取；自然语言段落里的候选须标记为待确认。
- 交付：可编辑分层 SVG + PNG + PDF 预览 + `result.json`（含 output_contract 全部字段）。
