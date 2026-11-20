# 示例材料：EGF/EGFR–MAPK/ERK 通路（教学简化版）

> **本文件是示例材料，非正式案例**。它只用于演示本 Skill 的读入 → 实体/关系抽取 → 布局 → 可编辑 SVG → PNG/PDF 预览 → 校验 → result.json 的完整数据流。正式评测案例由组织方提供。
> 本材料中的分子关系是教材级别的教学简化表述，数值（表1 表达量）为演示数据，均标注于表内，不冒充真实实验数据。

## 实体清单

- EGF | protein | extracellular | 表达量=0.95 | 分泌型生长因子配体；示例材料 表1
- EGFR | protein | membrane | 表达量=0.82 | 受体酪氨酸激酶（跨膜）；示例材料 表1
- GRB2 | protein | membrane | 表达量=0.60 | 衔接蛋白；示例材料 表1
- SOS | protein | membrane | 表达量=0.55 | 鸟苷酸交换因子(GEF)；示例材料 表1
- PIP3 | small_molecule | membrane | 表达量=0.50 | 磷脂酰肌醇三磷酸；示例材料 表1
- PTEN | protein | membrane | 表达量=0.30 | 脂磷酸酶；示例材料 表1
- RAS | protein | cytoplasm | 表达量=0.72 | 小 GTP 酶；示例材料 表1
- RAF | protein | cytoplasm | 表达量=0.68 | MAP3K 家族激酶；示例材料 表1
- MEK | protein | cytoplasm | 表达量=0.70 | MAP2K 激酶；示例材料 表1
- ERK | protein | cytoplasm | 表达量=0.66 | MAPK 激酶；示例材料 表1
- ELK1 | protein | nucleus | 表达量=0.50 | 转录因子；示例材料 表1
- MYC | protein | nucleus | 表达量=0.45 | 转录因子；示例材料 表1
- MYC（基因） | gene | nucleus | 表达量=0.40 | 转录靶标基因（书写区分基因/蛋白）；示例材料 表1

## 关系清单

- EGF | binding | EGFR | strong | 配体-受体结合；示例材料 表2
- EGFR | activation | GRB2 | moderate | 活化受体募集衔接蛋白；示例材料 表2
- GRB2 | binding | SOS | strong | 组成型结合；示例材料 表2
- SOS | activation | RAS | strong | GEF 催化 GDP→GTP 交换；示例材料 表2
- RAS | activation | RAF | strong | 转位至膜并被激活；示例材料 表2
- RAF | modification | MEK | moderate | 磷酸化激活；示例材料 表2
- MEK | modification | ERK | strong | 磷酸化激活；示例材料 表2
- ERK | transport | ELK1 | moderate | MAPK 核转位；示例材料 表2
- ERK | modification | ELK1 | strong | 磷酸化转录因子；示例材料 表2
- ELK1 | activation | MYC（基因） | weak | 转录激活（间接证据，虚线）；示例材料 表2
- ERK | inhibition | RAF | moderate | 负反馈环（右侧绕行绘制）；示例材料 表2
- PTEN | inhibition | PIP3 | strong | 去磷酸化负调控；示例材料 表2

数据映射：实体填充色=表达量（低 #FFF7E0 → 高 #1F4E79），数值来自示例材料 表1；边宽=证据强度（strong 2.8 / moderate 2.2 / weak 1.6，weak 或 uncertain 用虚线）。

## 表1 示例表达量（教学演示数据，非真实实验值）

| 实体 | 表达量 |
| --- | --- |
| EGF | 0.95 |
| EGFR | 0.82 |
| RAS | 0.72 |
| MEK | 0.70 |
| RAF | 0.68 |
| ERK | 0.66 |

## 表2 示例证据强度（教学演示标注）

| 关系 | 证据强度 | 依据 |
| --- | --- | --- |
| EGF→EGFR | strong | 经典配体-受体对（教材） |
| ERK→ELK1 | strong | 磷酸化位点已表征 |
| ELK1→MYC 基因 | weak | 间接/报道不一致，不明确 |