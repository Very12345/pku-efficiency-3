# 关系核对清单模板（relation checklist template）

> 用法：对每个案例，把**从材料中实际读到的**实体/关系/数据逐行填入下表并给出材料出处
> （文件 + 行号）。这张表是「人工核验（SKILL.md CP4）」的执行载体，也是 outcome 的
> 追溯证据：**材料没写的东西不许画上去**，材料写了但图上没有的必须说明原因。
> 类型与箭头语义词表见 `references/legend-encoding.md`；区室/命名规则见
> `references/mechanism-spec.md`。本模板为通用清单，非正式案例答案。

## 1. 实体核对

| # | 实体名称（图面写法） | 类型（gene/protein/complex/rna/small_molecule/other） | 区室 | 数据值（字段=值） | 材料出处（文件:行） | 备注/消歧说明 |
|---|---|---|---|---|---|---|
| 1 | 例：EGFR | protein | membrane | 表达量=0.82 | 材料.md:9 | 跨膜受体 |

## 2. 相互作用核对（箭头语义 = 科学论断）

| # | 从（实体#） | 到（实体#） | 类型（activation/inhibition/binding/modification/transport） | 证据强度（strong/moderate/weak） | 反馈环？ | 材料出处（文件:行） | 备注（如亚型：磷酸化） |
|---|---|---|---|---|---|---|---|
| 1 | 1 | 2 | binding | strong | 否 | 材料.md:19 | — |

## 3. 图例与数据编码核对

| 检查项 | 图面实际值 | 图例声明值 | 一致？ | 备注 |
|---|---|---|---|---|
| 实体类型 → 形状/颜色 | | | | |
| 边类型 → 箭头端点 | | | | |
| 边宽 = 证据强度 | | | | |
| 虚线条件（仅 weak/uncertain） | | | | |
| 数据映射字段 / 低色 / 高色 | | | | |

## 4. 通路方向与拓扑核对

| 检查项 | 结论 | 备注 |
|---|---|---|
| 信号流向符合 胞外→膜→胞质→核（rank 升序） | | 例外须在 uncertainty 说明 |
| 跨膜受体位于膜带内 | | |
| 核内因子位于核框内（核嵌入胞质） | | |
| 反馈环/回流边已标 `feedback=true` 且右侧绕行 | | |
| 同名基因/蛋白已拆分并注明 | | |

## 5. 导出核对

| 检查项 | 结果 |
|---|---|
| diagram.svg 良构（7 个 layer-* 图层齐全） | |
| diagram.png / diagram.pdf 生成（或记录缺失原因） | |
| model.json / topology.json / legend_audit.json 生成 | |
| result.json 契约字段齐全（含 case.json output_contract 全部字段） | |
| 每个产物 sha256 与字节数已记录 | |