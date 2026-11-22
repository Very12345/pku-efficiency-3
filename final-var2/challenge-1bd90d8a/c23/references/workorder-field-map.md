# workorder-field-map.md — 输入→字段→输出 映射链（字段映射）

把「案例输入材料 → 图表字段 → 输出图元」的链路显式化，保证每个图面元素都能
回答"来自哪份材料、哪一列、哪一行"。分五段映射，与执行步骤 S1–S5 一一对应。

## 1. 材料层（CP1 盘点，extract.py）

| 材料类型 | 识别 | 处理的脚本 | 记录的元数据 |
|-|-|-|-|
| 数据表 CSV/TSV/JSON | `.csv/.tsv/.tab/.json`，case `data_files` 或案例同目录 | extract → profile_table | file、sha256、rows、columns、每列画像 |
| 任务说明 | task.md / task_file 字段 | main discover_task | task_summary（前 500 字符） |
| 生物源材料（figure03 类） | entities_file(JSON) / material_file(文本) | extract → scan_material_text | 实体/关系/不确定候选 |
| 案例元信息 | case_id / dataset_version / output_contract | main | 原样进 result.json |

## 2. 字段语义层（CP2 抽取，extract.json）

对每个数据列给出语义标签（role），供图规格（figure spec）引用：

| role | 判定（按列名/值分布） | 图元语义 |
|-|-|-|
| `error` | 列名 ∈ {se,sem,sd,std,stddev,ci,err,error} 或 sd/se 前缀 | 误差线长度（语义随源：SE/SD/CI，D8） |
| `n` | 列名 ∈ {n,n_samples,sample_size,count_n} | 样本量（入 manifest，不画图元） |
| `time` | 列名命中 time/dose/conc/temp 等且数值占比 ≥60% | x 轴（折线） |
| `numeric` | 数值占比 ≥60% 且非 time/error/n | y / 点位 / 热图值 |
| `category` | 低基数非数值 | x 分类 / hue 分组 |

列名中括号内的单位被提取（`"time (h)"` → unit=`h`）写入 spec 的 x/y.unit（D2）。
extract.json 里每个网络材料给出 entities/relations 清单；词表扫描命中项标记
`uncertain: true`，未经确认不得上图（D4/D14）。

## 3. 规格层（CP3，figure spec / figure_map.schema.json）

| spec 字段 | 来自 | 校验（spec_lint） |
|-|-|-|
| `id` | 任务要求/自拟 | E2 必有 |
| `type` | 数据形状或任务指定 | E1 词表内 |
| `x/y/hue/error.column` | extract 列画像 | E3 列存在 |
| `error.semantics` | 源元数据 | E4 常规语义 |
| `annotations[]` | 材料 p 值（转述） | E5 锚点+来源 |
| `filter` | 子面板取子集 | E9 列存在 |
| network `entities/relations` | entities_file / 材料 | E8 边两端存在 + 词表确认 |

## 4. 图元层（CP4 生成，SVG data-* 属性）

| SVG 属性 | 内容 | 反向定位 |
|-|-|-|
| `data-role` | bar/point/series/errorbar/cell/node/relation/… | manifest role |
| `data-column` | 源数据列名 | manifest source.column |
| `data-row-index` | 源数据行号（出现顺序） | manifest source.row_index |
| `data-value` | 该行该列数值 | mapcheck 与源表逐行核对 |
| `data-category`/`data-series` | 分类/系列标签 | manifest source |
| `data-cite`/`data-source` | 网络节点来源图表编号/文件 | manifest source |
| `id` | 唯一图元 id（确定性命名的 svg_id） | manifest svg_id ↔ SVG id |

## 5. 校验闭合层（CP5，mapcheck 三向）

1. manifest → SVG：每个 manifest 元素必须存在于 SVG（正向）。
2. SVG → manifest：SVG 数据层每个 data-role 图元必须登记在 manifest（反向）。
3. 图元 ↔ 源值：column+row_index+value 三元组重读源表核对（容差 1e-9）。

任何一环断裂 → mapcheck mismatch/unmatched → G3/G4 失败 → status 不得 completed。

## 示例（examples/data.csv → fig-01 面板 A）

```
data.csv 行5: dose_mg_kg=20, time_h=24, mean_um3=485, se_um3=58
spec fig-01a: filter{time_h=24}, y.column=mean_um3, error.column=se_um3
SVG bar-4: data-column=mean_um3 data-row-index=5 data-value=485.0 data-category=20
manifest fig-01a.elements[4]: svg_id=bar-4, role=bar,
   source={column:mean_um3, row_index:5, category:20, series:…, value:485.0,
           error_column:se_um3, error_value:58.0}
mapcheck: 读 data.csv 行5 列 mean_um3 = 485.0 → 与图元一致 ✔
```

> 字段映射必须以实际文件为准：extract 对每个文件先算 sha256 并记录版本；
> 材料缺失/列缺失在 extract.json 与 result.uncertainty 如实说明，不补造。