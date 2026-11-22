# 生物源材料示例（material.md，非正式案例）

> 示意一份"供 figure03 类网络/机制图提取"的源材料写法：显式 `ENTITY:` / `REL:`
> 行会被 extract.py 结构化抽取；自然语言段落仅按词表扫描给出候选（标 uncertain，
> 需 Agent 对照原文确认）。正式案例的材料以平台提供为准。

## 通路描述

Wnt 信号通路的激活由 Wnt3a 配体结合 Frizzled 受体（FZD）与 LRP5/6 共受体起始，
随后 Dishevelled（DVL）被磷酸化激活，破坏复合物（APC/Axin/GSK3β）装配受抑，
β-catenin 免于磷酸化降解并转入核内，激活 TCF/LEF 转录程序。

## 图谱行（结构化）

ENTITY: L | Wnt3a (配体) | Ligand | Fig. 2A
ENTITY: Fz | Frizzled (FZD) | Receptor | Fig. 2A
ENTITY: LRP | LRP5/6 共受体 | Receptor | Fig. 2B
ENTITY: Dvl | Dishevelled (DVL) | Cytosolic | Fig. 2C
ENTITY: APC | APC/Axin/GSK3β 复合物 | Destruction complex | Fig. 2C
ENTITY: beta | β-catenin | Cytosolic | Fig. 2D
ENTITY: nucl | TCF/LEF 转录激活 | Nuclear | Fig. 2E

REL: L -> Fz | 结合 | activation
REL: L -> LRP | 结合 | activation
REL: Fz -> Dvl | 磷酸化激活 | phosphorylation
REL: LRP -> APC | 抑制复合物装配 | inhibition
REL: Dvl -> APC | 抑制 | inhibition
REL: APC -> beta | 磷酸化降解 | inhibition
REL: beta -> nucl | 入核 | activation