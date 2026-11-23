# OUTPUT_CONTRACT.md — 结果契约（result.json / validation.json / data_manifest.json / figure spec）

本文件定义本 Skill 每次运行后必须产出的全部结构化输出的字段、类型与语义，
以及交付前硬性门 G1–G8。**脚本生成的一切字段在 `scripts/` 中一一实现；
Agent 复核时不得改动类型，只允许在 `uncertainty` / `change_records` /
`manual_confirmations` 上追加诚实内容。**

本文件同时是**机器可读契约**：`scripts/check_contract.py` 直接解析下面的
`REQUIRED-FIELDS` 块，对每次运行的 `result.json` 做字段覆盖自查
（命令见 §7）。文档与脚本保持一致，改契约 = 同时改这两处。

`figcheck.py` 按本契约做交付前检查（exit 0 = 通过）。

## 0. 必需顶层字段（机器可读）

<!-- REQUIRED-FIELDS:BEGIN -->
case_id
status
outputs
editable_sources
renders
sources
figure_checks
uncertainty
change_records
environment
steps
spec_lint
checkpoints
gates
artifacts_sha256
figcheck_report
mapcheck_report
output_contract_applied
<!-- REQUIRED-FIELDS:END -->

> `status=failed`（运行异常，如 case.json 不存在/不可解析）时按**最小诚实信封**判定：
> `case_id`、`status`、`uncertainty`、`sources`、`change_records`（另含 `error`
> 与 traceback 摘要）。此时其余字段降级为 warn，**不要求把没算出来的字段编出来**。

## 1. result.json（/app/output/result.json，UTF-8，顶层对象）

| 字段 | 类型 | 必需 | 说明 |
|-|-|-|-|
| `case_id` | string | ✅ | 来自 case.json（`case_id`/`id`/`caseId`），无则 `"case"` |
| `status` | string | ✅ | `completed` / `partial` / `failed`（定义见 §1.1） |
| `title` / `challenge_id` / `dataset_version` | string | ｜ | 来自 case.json |
| `outputs` | array[obj] | ✅ | `{file, kind, figure_id}`；kind ∈ editable_svg/png_preview/pdf_preview |
| `editable_sources` | array[string] | ✅ | 全部 SVG 文件名（可编辑源） |
| `renders` | object | ✅ | `{png: [..], pdf: [..]}` |
| `sources` | array[obj] | ✅ | `{file, sha256, rows?, columns?, version?, role?}` |
| `completed_figures` / `failed_figures` | array | ｜ | 成功/失败图 id |
| `figure_checks` | object | ✅ | `{<fig_id>: [{id, level(ok/warn/fail), detail, pass}]}` |
| `figure_meta` | object | ｜ | 每图 `{y_range, x_range, adjustments[], warnings[], annotation_footnotes[]}` |
| `uncertainty` | array[string] | ✅ | 缺列/空值策略/字体缺字/无法核验项/失败图；禁止空口编造 |
| `change_records` | array[obj] | ✅ | `{ts, action, detail}`：人工确认（`manual_confirmations`）→ 脚本流水 |
| `manual_confirmations` | array | ｜ | case.json 带入，原样保留（同时并入 change_records 作为 `manual_confirmation` 条目） |
| `environment` | object | ✅ | `{python, pillow, fonts, dpi, no_network, cwd, style}`（字体=实际发现结果） |
| `steps` | array[obj] | ✅ | `{ts, action}` 执行流水 |
| `task_summary` | string | ｜ | task.md 前若干行（500 字符内） |
| `spec_lint` | object | ✅ | `{valid, errors[], warnings[], counts{figures, errors, warnings}}`（CP3） |
| `checkpoints` | object | ✅ | `cp1_material_survey / cp2_extract / cp3_spec_lint / cp4_export / cp5_mapcheck / cp5_figcheck / cp6_contract` |
| `gates` | object | ✅ | `{G1..G8: bool, all_pass: bool}`（见 §3） |
| `artifacts_sha256` | object | ✅ | 每产物文件 sha256（确定性证据，D18） |
| `figcheck_report` / `mapcheck_report` | string | ✅ | 本次校验报告文件名 |
| `output_contract_applied` | boolean | ✅ | 是否应用 output_contract |
| 契约字段 | 依声明 | ✅ | output_contract 声明的每个字段必须出现在顶层（见 §2） |

### 1.1 status 定义
- `completed`：全部 figure 生成成功、spec lint 无 error、校验六项无 fail、
  G1–G8 全部通过（允许 warn 但须在 uncertainty 说明）。
- `partial`：部分图失败，或材料缺失，或校验/映射有缺口（G8 强制降级）。
- `failed`：无任何图产出或运行异常（写 error 字段 + traceback 摘要）。

### 1.2 路径规范
result.json 内所有 `file` 都是**相对 /app/output 的文件名**（不写绝对路径），
保证目录可整体移动复核。

## 2. output_contract 应用规则（四形态，禁止 null）

契约可表达为四种形态，脚本 `apply_output_contract` 全部兼容：

| 形态 | 示例 | 行为 |
|-|-|-|
| ① 字段名列表 | `["case_id","status","outputs"]` | 顶层补齐列表字段 |
| ② 名称→类型 | `{"outputs":"array","uncertainty":"array"}` | 缺失时按类型给 `[]`/`{}`/`""`/`false`/`0` |
| ③ 嵌套 fields 列表 | `{"fields":["case_id","sources"]}` | 同 ① |
| ④ 嵌套 fields 映射 | `{"fields":{"title":"string"}}` | 同 ② |

规则：
1. 已知别名映射到真实产物（不打空）：

   | 契约字段 | 映射到 |
   |-|-|
   | `editable_source` / `editable_sources` | `editable_sources`（SVG 文件名列表） |
   | `rendered_preview` / `renders` / `render_png` / `render_pdf` | `renders` 对应子集 |
   | `field_mapping` / `data_mapping` / `data_manifest` | `"data_manifest.json"` |
   | `validation_report` / `validation` | `"validation.json"` |
   | `figcheck_report` / `mapcheck_report` | 对应报告文件名 |
   | `sources` / `evidence` | sources 列表 |
   | `uncertainty` / `change_records` / `status` / `outputs` / `gates` / `checkpoints` | 对应真实值 |

2. 其余声明字段缺失时按声明容器类型给 `""`/`[]`/`{}`/`false`/`0`。
   **绝不把声明字段写成缺失或 null。**
3. 保留字段一旦有真值不会被子默认覆盖。

## 3. 硬性门 G1–G8（figcheck.py 逐项判定）

| 门 | 判定 | 失败含义 |
|-|-|-|
| G1 | result.json 存在、可解析，case_id 与输入一致且非空 | 结果信封损坏 |
| G2 | output_contract 声明字段全部在顶层（四形态任一），值非 null | 契约回显不齐 |
| G3 | 每图 manifest 元素数 = SVG data-role 图元数（1:1） | 映射断链 |
| G4 | 每个数据图元至少一条源定位（column/row_index/id/from/to/cite） | 无源图元 |
| G5 | SVG 良构、分层 `<g>`、含 metadata 溯源、无外部实体、文字未转曲（真实 `<text>`） | 不可编辑 |
| G6 | PNG 可打开、PDF 以 %PDF 开头；导出参数（dpi/字体/色域）在 environment 记录 | 预览缺失 |
| G7 | provenance/legend-mapping/significance/axis-units/cjk-font/occlusion 六项无 fail | 标注错误 |
| G8 | status 与产物自洽：存在 fail/缺口 → 不得 completed；uncertainty 诚实 | 虚报完成 |

## 4. validation.json（/app/output/validation.json）

```json
{
  "case_id": "...",
  "status": "completed",
  "checks": { "<fig_id>": [ {"id": "...", "level": "ok|warn|fail", "detail": "...", "pass": true} ] },
  "adjustments": ["x 轴刻度文字过长，自动旋转 30°"],
  "warnings": ["PDF 预览失败：..."]
}
```

每图检查项 id 清单：

| id | 检查内容 | 失败/警告含义 |
|-|-|-|
| `provenance` | 数据图元 100% 带 role 溯源 | fail：存在无溯源图元 |
| `legend-mapping` | 系列 ↔ 图例一一对应 | fail：缺/多图例项（network 按组） |
| `axis-units` | 轴标签存在（panel 递归；network/pie 无轴跳过） | warn：缺标签 |
| `range-covers-data` | 数据点落在轴范围内 | warn：裁剪风险 |
| `cjk-font` | CJK 文本存在时找到 CJK 字体 | warn：PNG 可能缺字 |
| `significance` | 显著性线段数 = 文字数 | fail：星号缺配对 |
| `null-handling` | 空值处理计数 | ok：记录计数 |
| `occlusion` | 文本包围盒重叠（真实字体测量） | warn：N 处重叠 |

## 5. data_manifest.json（/app/output/data_manifest.json）

```json
{
  "case_id": "...",
  "sources": [{"file":"data.csv","sha256":"...","rows":8,"columns":["dose_mg_kg", ...]}],
  "figures": {
    "<fig_id>": {
      "type": "bar", "title": "...", "width": 2200, "height": 900, "style": "nature",
      "elements": [
        {"svg_id": "bar-1", "role": "bar",
         "source": {"column": "mean_um3", "row_index": 5, "category": "20", "series": "...",
                    "value": 485.0, "error_column": "se_um3", "error_value": 58.0}},
        {"svg_id": "node-3", "role": "node",
         "source": {"id": "APC", "label": "...", "group": "...", "cite": "Fig. 2C"}}
      ]
    }
  },
  "version": 2,
  "note": "图元→源数据映射；SVG 内同名 data-* 属性可反向定位；value 由 mapcheck 与源表逐行核对。"
}
```

`svg_id` 与 SVG 元素 `id` 一一对应 → 「从图回溯到数据、从数据定位到图元」双向检索
（mapcheck.py 机器执行，G3/G4）。

## 6. figure spec 契约（case.json figures[] 或 /app/work/figure_spec.json）

结构见 `templates/figure_map.schema.json`。要点：

- 通用：`id, type, title, subtitle, width, height, style, filter, layout{margin_*}`。
- `filter`：`{"column":"time_h","eq":"24"}` —— 构建前按列过滤行（子面板取子集）。

| type | 特有字段 |
|-|-|
| bar | `x{column,label,unit,order?}`, `y{column,label,unit}`, `hue{column,labels?}`, `error{column,semantics}`, `annotations[]`, `series[]`, `colors{}` |
| line | `x{column,label,unit}`, `y{column,label,unit}`, `hue{column,labels?}`, `error{column,semantics}`, `series[]` |
| scatter | `x/y{column,label}`, `hue{column,labels?}`, `size{column}?` |
| box | `x{column}`, `y{column}` 或 `presets[{label,min,q1,median,q3,max,n,outliers?}]` |
| heatmap | `matrix`（二维数组或 `{rows,columns}`）, `row_labels/col_labels`, `vmin/vmax`, `colormap` |
| pie | `labels{column}`, `values{column}`, `percent`, `legend` |
| network | `entities[]{id,label,group,shape,cite,x?,y?}`, `relations[]{from,to,label,type}`, `entities_file`, `material_file`, `layout` |
| panel | `panels[]`（子 spec，可各带 `data_file`/`filter`）, `grid=[rows,cols]` |

自动推断（type=auto）：实体/关系 → network；matrix → heatmap；panels → panel；
有时间列且 ≥2 数值列 → line；≥2 数值列+分类列 → bar；仅数值 → scatter。
误差列按名识别（se/sem/sd/std/ci/err）；空值 → 跳过并计数（D9）。

## 7. 契约的验证

`$SKILL_DIR` = 本 Skill 安装根目录（平台为 `/skills/weekly-skill`）；脚本用
`os.path.dirname(__file__)` 自定位资源，**任意 cwd 均可运行**：

```bash
python $SKILL_DIR/scripts/main.py --case <case.json> --out <out>       # 生成（CP1–CP6）
python $SKILL_DIR/scripts/check_contract.py --result <out>/result.json --case <case.json>
                                                                       # 字段覆盖（本契约 §0）
python $SKILL_DIR/scripts/figcheck.py --dir <out> --case <case.json>   # G1–G8（exit 0=通过）
python $SKILL_DIR/scripts/mapcheck.py --dir <out> --case <case.json>   # 映射双向核对
python $SKILL_DIR/scripts/verify_rerun.py --case <case.json> --out <out>  # 确定性再跑
```

全部通过退出码 0；`check_contract.py` 覆盖不全时退出码 1，契约文档本身不可读时 2。