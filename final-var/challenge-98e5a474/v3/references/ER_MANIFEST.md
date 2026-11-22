# ER Manifest 规范（实体—关系清单，绘图唯一数据源）

`scientific-schematic-editor` 的全部绘图与核验都从一份**实体—关系（ER）
清单**出发。ER 清单是图稿的"数据库"：图里每一个实体、每一条关系、
每一组分组、每一条图例，都必须能在这份清单里找到对应条目，且每条
都携带「来源 + 证据」两个字段，使图稿可独立复核。

正式案例运行时，Agent 的职责是从来源材料（/input 下的材料文件）
**现场抽取**这份清单并写到 `/app/work/entities.json`，然后交给
`scripts/main.py` 绘图。**不允许**凭空捏造清单条目；清单里出现材料中
不存在的基因名/浓度/时间点/单位，属于本题最典型的错误形态。

## 1. 顶层结构

```jsonc
{
  "schema_version": "1.0",
  "figure_type": "schematic | chart",     // 必填
  "title": "图题（与材料/任务书一致）",
  "subtitle": "可选",
  "entities": [ ... ],                    // schematic 必填
  "relations": [ ... ],                   // schematic 必填
  "groups": [ ... ],                      // 可选（包含/分区关系）
  "legend": [ ... ],                      // 可选（缺省由关系类型自动生成）
  "data": { ... },                        // chart 必填
  "style": { "font_size": 16,
             "canvas": {"width": 1500, "height": 860} } // 可选
  "acknowledged_issues": [ ... ]          // 可选：Agent 已处理并确认的检查项名单
}
```

## 2. entities（实体）

| 字段 | 必填 | 说明 |
|-|-|-|
| `id` | 是 | 唯一标识，建议 E1, E2, …（脚本可自动补全） |
| `name` | 是 | 图面上显示的名称，**必须逐字来自材料** |
| `type` | 是 | 决定节点配色：`protein/receptor/gene/small_molecule/process/cell/organ/pathway` 或其他 |
| `source` | 是 | 材料定位：文件 + 章节/行，如 `materials/fig3-note.md §3.1 L4` |
| `evidence` | 是 | 证据摘录或表格单元格引用（核验锚点） |
| `layer` | 否 | 层级序号（0 起始），override 自动分层 |
| `pos` | 否 | 手动坐标 `{"x": px, "y": px}`，指定后不参与自动布局 |

## 3. relations（关系）

| 字段 | 必填 | 说明 |
|-|-|-|
| `id` / `from` / `to` | 是 | from 与 to 必须是存在的 entity id |
| `kind` | 是 | **尽量用材料原文的动词**（如 binds / activates / 招募 / 抑制）。脚本按规范词表映射到 7 个箭头语义，映射不上的关系会被标红（fail） |
| `label` | 否 | 箭头上的文字；缺省用 kind |
| `source` / `evidence` | 是 | 同上，关系的方向必须有材料证据 |

### 箭头语义（7 类规范化 kind）

| 规范化 kind | 画法 | 常见同义词 |
|-|-|-|
| `activation` | 实线 + 实心三角箭头 | activates, stimulates, promotes, 激活, 促进, 正调控 |
| `inhibition` | 实线 + T 形线 | inhibits, blocks, suppresses, 抑制, 阻断, 负调控 |
| `recruitment` | 实线 + 开口箭头 | recruits, binds, interacts-with, 招募, 结合 |
| `process` | 实线 + 开口箭头 | produces, converts, catalyzes, 产生, 转化, 催化 |
| `transcriptional` | **虚线** + 开口箭头 | upregulates-gene, drives-transcription, 转录上调, 上调转录 |
| `causal` | 实线 + 开口箭头 | causes, leads-to, 导致, 引发 |
| `containment` | 不画箭头，画分组框 | contains, part-of, 包含, 属于, 组成 |

> **判定要点**：`激活` 与 `抑制` 画反、上下游颠倒、把包含关系画成并列
> 箭头，是审稿与判分最常见的硬伤。映射方向**以材料原文为准**，例如
> "RIPK1 激活 NF-κB" ⇒ `activation`；"X 抑制 Y" ⇒ `inhibition`。

## 4. groups（分组/包含关系）

含 `id / label / members(实体 id 列表) / source / evidence`。
成员必须是存在的实体；分组框会包住成员节点的外接矩形。

## 5. legend（图例）

每项：`id / key(=规范化 kind 或 arrow) / label / source`。
脚本会做**双向校验**：

- **缺项**：图上画了某种箭头但图例没有对应项 → fail；
- **孤儿项**：图例有但图上没有任何关系用它 → warn。

图例的 key 与颜色映射来自同一份数据，"图例与数据逐项一致"由构造保证，
并写入 result.json 的 `verification.checks` 供复核。

## 6. data（图表专用）

```jsonc
"data": {
  "chart_type": "bar | line | scatter | heatmap",
  "table": {"columns": ["compound", "response"],
            "rows": [["ctrl", 1.00], ["A", 2.40]]},   // 与来源表一致
  "category_col": "compound",      // 图例类别列
  "value_col": "response",         // 数值列
  "unit": "fold change",           // 单位，绘制到坐标轴标签
  "x_label": "...", "y_label": "..."
}
```

图表图例**直接从 table 的唯一类别生成**，颜色映射、类别数与图例项数
必然一致（写入 `data_mapping` 供查）。不支持表格里没有的分类。

## 7. 抽取后的必须动作

1. 逐字核对实体名与材料一致（含大小写/连字符/希腊字母写法）；
2. 每个关系核对方向（谁指向谁）；
3. 数值/单位只来自材料表格，不改写、不补算科学结论；
4. 保存到 `/app/work/entities.json`，运行：
   ```
   python <skill_root>/scripts/main.py --case /input/case.json \
       --manifest /app/work/entities.json --out /app/output
   ```
5. 复跑 check 汇总：任何 fail 都要回到材料或清单修正，而不是绕过。

## 8. 校验失败示例（都会导致 status=partial，绝不静默通过）

- 实体名在材料中无出处 → `traceability` warn；
- 关系 kind 无法映射 → `relation.kind` fail；
- 图例缺"抑制"项但图上有抑制箭头 → `legend.missing_kinds` fail；
- 图表类别与图例不一致 → `data_mapping.legend_consistency` fail；
- 来源材料文件缺失 → `unresolved source materials` 写入 uncertainty。