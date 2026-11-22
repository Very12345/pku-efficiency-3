# EXPECTED-OUTPUT.md — 示例案例的预期产物清单（文字契约，替代预置二进制产物）

> **这些产物不在包内。** 平台预检只接受 UTF-8 文本资源，`*.svg`/`*.png`/`*.pdf`
> 一律属于不支持的类型，所以本包**不预置任何图或预览**：
> 每次运行由 `scripts/main.py` 现场生成，产物落在 `--out` 指定的输出目录
> （平台运行期为 `/app/output`）。本文件用文字把「应该出现什么」写清楚，
> 供人工与脚本共同核对。
>
> `examples/output/` 下保留的 **5 个 `.json`** 是在**本包自带的合成示例案例**
> （`examples/case.json` + `data.csv` + `entities.json`，非平台正式案例）上
> **由本 Skill 实际运行产生**的真实产物，用于让评审看到真实的报告结构；
> 其中运行目录等本机字样已在归档时净化为相对占位（`"dir": "."`）。

## 1. 运行命令（示例案例，`$SKILL_DIR` = 本包绝对路径）

```bash
python $SKILL_DIR/scripts/main.py --case $SKILL_DIR/examples/case.json \
       --out <OUT> --style nature
```

预期：**exit 0**、`result.json.status = "completed"`、`gates.all_pass = true`、
`completed_figures = ["fig-01","fig-02"]`、`failed_figures` 不存在。

## 2. `<OUT>` 下应出现的文件（11 个）

| 文件 | 类型 | 内容（文字描述，替代原二进制预览） |
|-|-|-|
| `figure-fig-01.svg` | 文本矢量 | 可编辑分层 SVG：`<g id="layer-*">` 分层（背景/坐标轴/数据/文字/图例/标注）、`<metadata id='provenance'>` 溯源块；面板 A 为 24 h 剂量-响应柱状图（4 根柱，SE 误差线，`**` 显著性线段），面板 B 为 0 h/24 h 时间曲线（按剂量 4 系列）；每个柱/点带 `data-column`/`data-row-index`/`data-value`/`data-role`；文字是真实 `<text>`，**未转曲**。实测约 21 KB |
| `figure-fig-01.png` | 二进制预览 | 与 SVG 同一图元场景渲染（默认 300 dpi，`--style nature`）；归档前实测约 282 KB |
| `figure-fig-01.pdf` | 二进制预览 | PNG 光栅嵌入 PDF，供快速查看页；**可编辑源以 SVG 为准**；实测约 343 KB |
| `figure-fig-02.svg` | 文本矢量 | Wnt 信号转导机制/通路图：7 节点（配体/受体/胞质/降解复合物/核内）7 关系；激活用箭头、抑制用阻滞线，关系类型决定颜色与线型；节点带 `data-cite`（来源图表编号）；实测约 12 KB |
| `figure-fig-02.png` | 二进制预览 | 同场景 PNG；实测约 289 KB |
| `figure-fig-02.pdf` | 二进制预览 | 同场景 PDF；实测约 189 KB |
| `data_manifest.json` | 文本 JSON | 图元 ↔ 源数据映射：`figures.<fig_id>.elements[].source = {column,row_index,value,error_column,error_value,...}`，`svg_id` 与 SVG 元素 `id` 一一对应 |
| `validation.json` | 文本 JSON | 八类标注校验的逐项结果：`provenance`/`legend-mapping`/`axis-units`/`range-covers-data`/`cjk-font`/`significance`/`null-handling`/`occlusion`，以及 `adjustments`/`warnings` |
| `mapcheck_report.json` | 文本 JSON | 数据↔图元双向核对报告：实测 `fig-01` 79 元素 / `fig-02` 42 元素，汇总 `121 checked / 0 mismatched / 0 unmatched` |
| `figcheck_report.json` | 文本 JSON | 交付审计报告：`gates` G1–G8 全 `true`，`six_checkpoints` 六项 `covered=true` |
| `result.json` | 文本 JSON | **唯一评分产物**（契约见 `references/OUTPUT_CONTRACT.md`），字段见下节 |

中间产物（`--work`，缺省为 `<OUT 的父目录>/work`）：

| 文件 | 内容 |
|-|-|
| `work/extract.json` | CP2 抽取结果：表格列画像（列名/语义/单位/取值范围/空值位置）+ 实体-关系网络 |
| `work/spec_lint.json` | CP3 生成门结果：`{valid, errors[], warnings[], counts{figures,errors,warnings}}` |

## 3. `result.json` 必须覆盖的顶层字段

`references/OUTPUT_CONTRACT.md` §0 的机器可读清单（`scripts/check_contract.py` 逐条核对）：

```
case_id            status             outputs            editable_sources
renders            sources            figure_checks      uncertainty
change_records     environment        steps              spec_lint
checkpoints        gates              artifacts_sha256   figcheck_report
mapcheck_report    output_contract_applied
```

在示例案例上由 `case.json` 的 `output_contract` 额外声明并要求回显的字段
（四形态兼容，缺省按声明容器类型给值、**禁止 null**）：
`title`、`sources`、`outputs`、`editable_source`、`rendered_preview`、
`field_mapping`、`validation_report`、`uncertainty`、`change_records`、
`checkpoints`、`gates`。

外加恒等字段：`completed_figures`、`figure_meta`、`task_summary`、
`manual_confirmations`（来自 `case.json`，同时并入 `change_records`）、
`environment`（Python/Pillow 版本、实际发现的字体、dpi、`no_network`）。

> 官方运行契约要求 result.json 含 **original `output_contract` 全部字段 + `case_id`**，
> 并保留 `status` / `sources` / `uncertainty` / `change_records`：
> `main.py` 的 CP6 与 `check_contract.py` 就是为这条要求服务的。

## 4. 数值核验（示例 Figure 1 面板 A）

源数据 `data.csv` 中 `time_h=24` 的四行：剂量 0/1/5/20 mg/kg → `mean_um3` =
1180 / 902 / 610 / 485。SVG 中四根柱子的 `data-value` 依次为
`1180.0 / 902.0 / 610.0 / 485.0`，且每根柱同时写有 `data-row-index`
（指向 `data.csv` 的具体行号）；显著性线段位于 0 与 20 mg/kg 柱之间，
`data-p_value="0.004"`，来源在图注中转述（one-way ANOVA + Tukey HSD，本 Skill 不代算统计量）。
`mapcheck_report.example.json` 记录了逐元素的「文件→列→行→值」核对明细。

## 5. 归档的示例报告（`examples/output/`）

| 文件 | 说明 |
|-|-|
| `data_manifest.example.json` | 真实运行产物（未改动，除下述净化） |
| `validation.example.json` | 真实运行产物 |
| `mapcheck_report.example.json` | 真实运行产物；顶层 `"dir"` 归档时置为 `"."` |
| `figcheck_report.example.json` | 真实运行产物；顶层 `"dir"` 归档时置为 `"."` |
| `result.example.json` | 真实运行产物；`steps`/`change_records` 中的任务说明路径改写为相对路径 `examples/task.md` |

> 除上表两处路径净化外，这些 JSON 与«同一命令在同一示例输入上重跑»的输出逐字节一致
> （证据见 `TEST.md` T6）；它们**不是**平台正式案例的结果，也**不冒充**正式案例结果。
