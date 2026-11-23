# 组件-连接核对清单（component-connection-checklist）

> 与 `entity-relation-checklist.csv`、`scripts/svg_verify.py` 的检查项一一对应。
> 用途：Agent 在复核图稿时逐项勾选；机器侧由 svg_verify.py 自动核对（G 门见
> `references/OUTPUT_CONTRACT.md`）。任何一项不过 → 用 `--merge` 修正后重跑。

## A. 类别与词表（CP2 连接门）

- [ ] A1 每个实体 kind ∈ {step, phase, device, material, product, data, decision, milestone, waste, container}（违反=error）
- [ ] A2 每条关系 kind ∈ {flow, connect, depend, recycle, sequence, causation}（违反=error）
- [ ] A3 关系两端不是同一实体（无自环，违反=error）

## B. 连接语义（CP2 连接门）

- [ ] B1 sequence(顺序) 关系两端都是 step/phase/milestone 步骤实体（违反=error）
- [ ] B2 connect(连接) 关系至少一端是 device/container 结构件（违反=error）
- [ ] B3 装置图：物料不作为流向终点（除 recycle，违反=error）
- [ ] B4 产物/数据/里程碑作为终点的约定已复核（出边=warn，需人工确认分叉）
- [ ] B5 回流(recycle) 环路与正文一致、方向正确（warn，需人工确认）

## C. 图面一致性（CP3 校验门）

- [ ] C1 箭头两端实体都存在（无断头箭头）
- [ ] C2 route/flow 图步骤编号 1..N 连续且与正文顺序一致
- [ ] C3 图例 kind 集合 == 图面实际使用的 kind 集合（图例↔图元一致）
- [ ] C4 每个实体可追溯到材料出处（source），缺失者已计入 uncertainty

## D. 可编辑与导出（CP3 校验门）

- [ ] D1 SVG 是合法 XML；五个图层 id 齐全（background/title/arrows/entities/legend）
- [ ] D2 实体是真实 <text> 文本（≥3 个），实体组带 data-entity/data-source/data-step-no
- [ ] D3 figure.png / figure.pdf 存在且非空；字体缺失已如实记录（fonts.found）
- [ ] D4 result.json 通过 check.py G1–G10（python scripts/check.py <result.json> → ok:true）

## E. 状态与记录

- [ ] E1 status 诚实：error 级违规未解决 ⇒ partial（不得 success）
- [ ] E2 change_record / uncertainty / sources 均已如实记录