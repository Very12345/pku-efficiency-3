# 源材料（合成）：Mg-Zn 合金体外降解与产物膜机制

> 合成材料，仅用于演示 `ENTITY:` / `REL:` 行语法与词表候选扫描；不代表任何真实文献结论。
> 下列实体的名称与来源标注须**照抄原文**，不得翻译或"修正"拼写。

## 一、显式实体行（推荐写法）

ENTITY: mgmatrix | Mg 基体 | Bulk | Fig. 1A
ENTITY: znrich | Zn 富集区 | Microstructure | Fig. 1B
ENTITY: mgh2 | Mg(OH)2 产物膜 | Surface film | Fig. 2A
ENTITY: clattack | Cl- 侵蚀 | Aqueous | Fig. 2B
ENTITY: caphase | Ca-P 沉积层 | Surface film | Fig. 3A
ENTITY: mg2zn3 | MgZn2 第二相 | Microstructure | Fig. 1C
ENTITY: osteo | MC3T3-E1 成骨细胞 | Cell | Fig. 3C

## 二、显式关系行

REL: znrich -> mgmatrix | 细化晶粒 | microstructure
REL: mg2zn3 -> mgmatrix | 电偶腐蚀 | electrochemical
REL: mgmatrix -> mgh2 | 腐蚀产物沉积 | passivation
REL: mgh2 -> mgmatrix | 屏障保护 | protection
REL: clattack -> mgh2 | 破坏产物膜 | inhibition
REL: caphase -> mgh2 | 协同沉积 | passivation
REL: mgh2 -> osteo | 影响细胞黏附 | biointerface

## 三、自然语言段落（仅作词表候选，须对照上文原文确认后才可上图）

Mg 基体中添加 Zn 可细化晶粒并形成 MgZn2 第二相，第二相与基体构成微电偶，
在模拟体液（SBF）中加速初期腐蚀。腐蚀产物以 Mg(OH)2 为主，在含 Cl- 的介质中
会被逐步破坏；同时 Ca-P 沉积层可与之协同，共同影响 MC3T3-E1 成骨细胞的黏附行为。
