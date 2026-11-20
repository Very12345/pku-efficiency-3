# OUTPUT_CONTRACT — result.json / validation.json / data_manifest.json / figure spec 契约

本文件定义本 Skill 全部结构化输出的字段、类型与语义。**脚本生成的一切字段在
`references/` 与 `scripts/` 中一一实现，Agent 复核时不得改动类型；只允许在
`uncertainty` / `change_records` / `manual_confirmations` 上追加诚实内容。**

## 1. result.json（/app/output/result.json，UTF-8，顶层对象）

| 字段 | 类型 | 必需 | 说明 |
|-|-|-|-|
| `case_id` | string | ✅ | 来自 case.json（`case_id`/`id`/`caseId`），无则 `"case"` |
| `status` | string | ✅ | `completed` / `partial` / `failed`（定义见 §1.1） |
| `title` | string | ｜ | case.json 的 title |
| `challenge_id` | string | ｜ | case.json 如有 |
| `dataset_version` | string | ｜ | 源数据版本标识 |
| `outputs` | array[obj] | ✅ | 每个产物 `{file, kind, figure_id}`；kind ∈ editable_svg/png_preview/pdf_preview |
| `editable_sources` | array[string] | ✅ | 全部 SVG 文件名（可编辑源） |
| `renders` | object | ✅ | `{png: [..], pdf: [..]}` |
| `sources` | array[obj] | ✅ | `{file, sha256, rows?, columns?, version?, role?}`；每个使用过的源文件 |
| `completed_figures` | array[string] | ｜ | 成功图 id |
| `failed_figures` | array[obj] | ｜ | `{figure_id, error}` |
| `figure_checks` | object | ✅ | `{<fig_id>: [ {id, level(ok/warn/fail), detail, pass} ]}`（= validation.json checks） |
| `figure_meta` | object | ｜ | 每图 `{y_range, x_range, adjustments[], warnings[], annotation_footnotes[]}` |
| `uncertainty` | array[string] | ✅ | 保留项：缺列、空值策略、字体缺字、无法核验项、失败图等。禁止空口编造 |
| `change_records` | array[obj] | ✅ | `{ts, action, detail}`：脚本流水 + 人工修改（--note / manual_confirmations） |
| `environment` | object | ✅ | `{python, pillow, fonts, no_network}`（字体=实际发现结果） |
| `steps` | array[obj] | ✅ | `{ts, action}` 执行流水（诚实过程记录） |
| `task_summary` | string | ｜ | task.md 前若干行（500 字符内） |
| `output_contract_applied` | boolean | ✅ | 是否应用了 output_contract |
| `manual_confirmations` | array | ｜ | case.json 带入，原样保留 |
| 契约字段 | 依声明 | ✅ | output_contract 声明的每个字段必须出现在顶层（见 §2） |

### 1.1 status 定义
- `completed`：全部 figure 生成成功且校验运行完成（允许 warn，不允许 fail）。
- `partial`：部分图失败，或材料缺失导致覆盖不全。
- `failed`：无任何图产出或运行异常（头部写 error 字段 + traceback 摘要）。

### 1.2 路径规范
result.json 内所有 `file` 都是 **相对 /app/output 的文件名**（不写绝对路径），
保证目录可整体移动复核。

## 2. output_contract 应用规则（脚本 `apply_output_contract`）

契约可表达为：`["field1", ...]` 或 `{"field1": "string|array|object|boolean", ...}` 或
`{"fields": [...]}`。

规则：
1. 已知别名映射到真实产物（缺省不再填空）：

   | 契约字段 | 映射到 |
   |-|-|
   | `editable_source` / `editable_sources` | `editable_sources`（SVG 文件名列表） |
   | `rendered_preview` / `renders` / `render_png` / `render_pdf` | `renders` 对应子集 |
   | `field_mapping` / `data_mapping` / `data_manifest` | `"data_manifest.json"` |
   | `validation_report` / `validation` | `"validation.json"` |
   | `sources` / `evidence` | sources 列表 |
   | `uncertainty` / `change_records` / `status` / `outputs` | 对应真实值 |

2. 其余声明字段缺失时按声明容器类型给默认值：`string→""`、`array→[]`、
   `object→{}`、`boolean→false`、`number→null`。**绝不把声明字段写成缺失。**
3. 保留字段一旦有真值不会被子默认覆盖。

## 3. validation.json（/app/output/validation.json）

```json
{
  "case_id": "...",
  "status": "completed",
  "checks": { "<fig_id>": [ {"id": "...", "level": "ok|warn|fail", "detail": "...", "pass": true} ] },
  "adjustments": ["x 轴刻度文字过长，自动旋转 30°", "图例自动移出绘图区"],
  "warnings": ["PDF 预览失败：..."]
}
```

检查项 id 清单（每图运行）：

| id | 检查内容 | 失败/警告含义 |
|-|-|-|
| `provenance` | 数据图元 100% 带 role 溯源 | fail：存在无溯源图元 |
| `legend-mapping` | 系列 ↔ 图例一一对应 | fail：缺/多图例项（network 按组） |
| `axis-units` | 轴标签存在（panel 递归子面板；network/pie 无轴跳过） | warn：缺标签 |
| `range-covers-data` | 数据点落在轴范围内（非全部图型） | warn：裁剪风险 |
| `cjk-font` | CJK 文本存在时找到 CJK 字体 | warn：PNG 可能缺字 |
| `significance` | 显著性线段数 = 文字数 | fail：星号缺配对 |
| `null-handling` | 空值处理记录 | ok：记录计数 |
| `occlusion` | 文本包围盒重叠检测（真实字体测量，排除旋转/标题） | warn：N 处重叠 |

## 4. data_manifest.json（/app/output/data_manifest.json）

```json
{
  "case_id": "...",
  "sources": [ {"file":"data.csv","sha256":"...","rows":8,"columns":["dose_mg_kg", ...]} ],
  "figures": {
    "<fig_id>": {
      "type": "bar",
      "title": "...",
      "elements": [
        { "svg_id": "bar-1", "role": "bar",
          "source": {"column": "mean_um3", "row_index": 5, "category": "20", "series": "...", "value": 485.0,
                     "error_column": "se_um3", "error_value": 58.0} },
        { "svg_id": "node-3", "role": "node",
          "source": {"id": "APC", "label": "...", "group": "...", "cite": "Fig. 2C"} }
      ]
    }
  },
  "version": 1,
  "note": "图元→源数据映射；SVG 内同名 data-* 属性可反向定位"
}
```

`svg_id` 与 SVG 内元素 `id` 一一对应 → 实现「从图回溯到数据、从数据定位到图元」双向检索。

## 5. figure spec 契约（写入 case.json 或被 Agent 在 /app/work/figure_spec.json 生成）

通用字段：`id, type, title, subtitle, width, height, style, filter, layout{margin_*}`
（width/height 缺省 1200×800；style 缺省 default）。

| type | 特有字段 | 说明 |
|-|-|-|
| bar | `x{column,label,unit,order?}`, `y{column,label,unit}`, `hue{column,labels?}`, `error{column,semantics}`, `annotations[]`, `series[]`, `colors{}` | annotations: `{from,to,text,p,source}` 或 `{at,text,p,source}` |
| line | `x{column,label,unit}`, `y{column,label,unit}`, `hue{column,labels?}`, `error{column,semantics}`, `series[]` | series: `{column,label,error?}` |
| scatter | `x/y{column,label}`, `hue{column,labels?}`, `size{column}?` | 颜色/大小可选 |
| box | `x{column}`, `y{column}` 或 `presets[{label,min,q1,median,q3,max,n,outliers?}]` | presets 直供统计值（不代算） |
| heatmap | `matrix`（二维数组或 `{rows,columns}`）, `row_labels/col_labels`（list 或 `{column}`）, `vmin/vmax`, `colormap`（bwr/viridis/blues/magma）, `show_values`, `value_label` | |
| pie | `labels{column}`, `values{column}`, `percent`, `legend` | |
| network | `entities[]{id,label,group,shape,cite,x?,y?}`, `relations[]{from,to,label,type}`, `layout`（auto/layer）, `entities_file` | type∈activation/inhibition/phosphorylation/transcription → 颜色与箭头语义 |
| panel | `panels[]`（子 spec，可各带 `data_file` 与 `filter`）, `grid=[rows,cols]` | 子面板共用画布，字母 A/B/C 标注 |

### 5.1 自动推断（type=auto 或字段缺省）
- 实体/关系存在 → network；有 matrix → heatmap；有 panels → panel。
- 有时间列（time/day/week/hour/dose/conc…）且 ≥2 数值列 → line。
- ≥2 数值列 + 分类列 → bar；仅数值 → scatter。
- 误差列按名（se/sem/sd/std/ci/err...）识别；空值 → 跳过并计数（D9）。

### 5.2 filter
`{"column": "time_h", "eq": "24"}` —— 构建前按列过滤行（数值/字符串均可），
用于子面板取子集（如固定时间点作柱状图）。无匹配行 → SpecError 明示。

## 6. 契约的验证

`scripts/validate_result.py --dir <out> [--case <case.json>]` 独立复核：
result.json 可解析且 case_id 与输入一致 → 契约字段齐全 → 引用的 SVG/PNG/PDF 存在 →
SVG 良构（无外部实体）、分层、含 metadata 溯源、含 data-* 属性 → PNG 可打开 → PDF 以 %PDF 开头。
全部通过退出码 0。