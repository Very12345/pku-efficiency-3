# DRAWING_GRAMMAR — 示意图图形语法（v2）

本文件把"结构关系与层级表达"变成可执行的绘图规则（题面方向 2、3、
4）。`assets/relation-dict.json` 是机器可读的连接规则字典，本文件是
人读规范；两者由 `scripts/spec_lint.py`（CP1）和 `scripts/checks.py`
共同执行/校验。

## 1. 关系语义 → 箭头语法（照 relation-dict.json）

| 语义类别 kind | 箭头 | 线型 | 颜色 | 画法约束 |
|-|-|-|-|-|
| activation（激活/促进/诱导/正调控） | 实心三角头 | 实线 | 蓝 `#1F77B4` | 方向 = 材料动词方向；激活≠抑制，二者不可互换 |
| inhibition（抑制/阻断/阻遏/负调控） | T 型短横（⊥） | 实线 | 红 `#D62728` | 与激活方向相反语义，最常被画错的点 |
| recruitment（招募/结合/互作） | 开箭头（chevron） | 实线 | 绿 `#2CA02C` | 方向 = "谁招募谁"，不可颠倒上下游 |
| process（产生/转化/催化/裂解/转录） | 开箭头 | 实线 | 紫 `#9467BD` | 材料明确"X 产生 Y"才可画 |
| transcriptional（转录水平上调） | 开箭头 | **虚线** | 品红 `#E377C2` | 虚线只用于基因/转录层面事件（审稿常见硬伤：把转录上调画成普通实线） |
| causal（因果/导致/引发） | 开箭头 | 实线 | 棕 `#8C564B` | 因果是弱于激活的表述，材料用"导致"时用 causal |
| containment（包含/属于/组成/定位于） | **无箭头** | **无连线** | — | **必须用分组框（groups）表达**，永远不画箭头；见 §3 |

> 规则来自 `assets/relation-dict.json` 的 `group_grammar`：
> containment_must_be_group=true；arrow_must_not_cross_group_boundary=
> true；dash_line_only_for_gene_level_transcriptional=true。CP1
> （spec_lint）对违反项给 `fail`。

## 2. 方向判定（题面要求：上下游不可颠倒）

1. 以材料原文动词为准：`激活`、`抑制`、`上调`、`招募`、`结合`、
   `产生`、`导致` 等词决定了 from→to；
2. 材料如明示"常见误读"（例：RIPK1 对 NF-κB 是激活不是抑制），
   必须在清单落实并在 evidence/change_records 里注明；
3. 一条关系只能有一个方向；双向/反馈回路用两条边分别标注或使用
   cycle 布局（layout family `cycle`）；
4. 不确定方向时：`spec_lint` 给关系缺失 source 的 warn，但方向
   语义本身由 Agent 判断——宁可在 uncertainty 说明，不猜箭头。

## 3. 包含与并列（层级表达）

- **包含（containment）**：`groups[].members` 表达，"A 属于 B"=
  A 是 B 组的成员；组框即包含关系，**不画成员之间的箭头**；
  组框可嵌套（成员实体再被更外层的组包含时，合并为一个大组）；
- **并列**：同一 layer 内多个实体（layout 引擎按依赖分层，同层
  并列）；并列实体之间无方向关系时**不画边**；
- **上下游**：layered 布局天然表达（左→右 / 上→下），layer 由
  依赖深度自动分配，`entity.layer` 可显式覆盖（层顺序对装置/
  流程类图尤其重要）；
- CP1 检查：containment 关系若没有对应分组（成员都在同一组），
  `spec.containment_group` fail。

## 4. 图例规范

- 图例条目 == 图面实际使用的箭头类型集合，双向一致：
  每个被画出的 kind 必须有图例项（`legend.missing_kinds` fail），
  每个图例项必须被至少一条关系使用（`legend.orphan_items` warn）；
- 图例每项必须带 `source`（来自材料哪节）；
- 图例不含数据（chart 的图例由数据表类别自动生成，数据图例与其
  颜色一一对应，见 §5）。

## 5. 颜色与数据映射（图例与数据一致）

- schematic：关系颜色只从 relation-dict 的 kind→color 来，**不得
  因美观改写**（改了颜色 = 图例与图面不一致）；
- chart：类别 ↔ 颜色 ↔ 图例三者来自同一数据表；
  `data.colors/palette` 若提供，其长度必须 ≥ 表内唯一类别数
  （`spec.color_category_count` fail）；
  未提供调色板则自动分配色盲安全调色板（Okabe-Ito 系）；
- 单位必须上轴（`data_mapping.unit`）；图上的数字只来自数据表
  （G8：result 里出现表外类别即 INVALID）。

## 6. 布局与图面规范（题面方向 3）

- 画布：`style.canvas` 若提供，尺寸不得过小挤爆节点（CP1 软检查）；
  缺省自动扩展至内容 + 边距；
- 文字：所有标签为 `<text>`（可选中可搜索）；节点按字号自动换行
  防溢出；字号层级：图题 ≥ 组标题 ≥ 节点名 ≥ 图例 ≥ 来源页脚；
- 引导线：SVG 边用二次/三次贝塞尔绕行减少交叉，交叉不可避免时
  逐条标注；
- 导出：PNG/TIFF 按打印宽度 18cm 的**有效 DPI 预检**（≥300 印刷 /
  ≥150 屏幕 → `bitmap.dpi_print`）；色彩 RGB/sRGB；PDF 结构健全
  （字体嵌入为尽力而为审计）。

## 7. 子图编号（figure 内部模块/面板）

- 多模块示意图用 `groups[].label` 标注模块（"Module A / 模块 A"），
  组标题即子图标题；不另设子图编号字段，避免与论文正式 Fig. 编号
  冲突；若任务书明确要求面板编号（a/b/c），写入 group label 前缀。