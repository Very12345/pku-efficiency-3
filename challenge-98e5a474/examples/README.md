# examples — 最小调用示例（示例，非正式案例）

> 本节所有内容均为**合成演示**（case 输入、来源材料、产物），仅用于
> 说明接口与完整使用流程，**不冒充、不等同于平台正式案例结果**。
> 正式案例由组织方提供，平台以固定 3 案例运行本 Skill。

## 三个示例

| 文件 | 演示能力 |
|-|-|
| `case.json` (schematic) | 机制/信号通路示意图：实体 6、关系 5（结合/招募/激活/转录上调）、分组 3、图例 3；输出 `output/`（figure.svg 可编辑源 + figure.png 预览 + figure.pdf 导出 + result.json） |
| `case_chart.json` (chart) | 数据表驱动图表：图例/颜色直接从 `sources/data-table.csv` 类别生成；输出 `output/chart/` |
| `case_edit.json` (edit) | 源文件级编辑：对 `output/figure.svg` 做 rename/relabel/note 三种动作，before→after 写入 result.json `change_records` |

## 运行

```bash
# 从包根目录
python scripts/main.py --case examples/case.json --out /tmp/sse-out            # schematic
python scripts/main.py --case examples/case_chart.json --out /tmp/sse-out-ch   # chart
python scripts/main.py --case examples/case_edit.json \
    --edit-svg examples/output/figure.svg --out /tmp/sse-out-edit              # edit
python scripts/validate_result.py --case examples/case.json \
    --result /tmp/sse-out/result.json                                          # 契约校验
```

## 产物说明（`examples/output/`）

- `figure.svg`：可编辑分层 SVG —— 文字均为 `<text>`；元素带 `id` 与
  `data-entity/data-relation/data-source`；语义图层 `layer-*` 分组；
  ER 清单内嵌于 `<metadata id="er-manifest">`（源文件自描述，供编辑）；
- `figure.png`：渲染预览（同一 layout+manifest 的 matplotlib 镜像）；
- `figure.pdf`：矢量导出件；
- `result.json`：契约全字段 + `_example: true` + 状态说明标注"示例"；
- `work/`：中间产物（layout.json、manifest.validated.json），作为可
  复核的过程证据。

本示例输出已包含"示例，非正式案例"标注，并可在任意新目录重新生成
（上面的运行命令即生成方法），请勿将其作为正式案例答案提交。