# examples — 最小调用示例（示例，非正式案例）

> 本节所有内容均为**合成演示**（case 输入、来源材料、产物），仅用于
> 说明接口与完整使用流程，**不冒充、不等同于平台正式案例结果**。
> 正式案例由组织方提供，平台以固定 3 案例运行本 Skill。

## 三个示例

| 文件 | 演示能力 |
|-|-|
| `case.json` (schematic) | 机制/信号通路示意图：实体 6、关系 5（结合/招募/激活/转录上调）、分组 3、图例 3；输出 `output/`（figure.svg 可编辑源 + figure.png 预览 + figure.pdf 导出 + result.json） |
| `case_chart.json` (chart) | 数据表驱动图表：图例/颜色直接从 `sources/data-table.csv` 类别生成（图例×颜色×类别数三方一致）；输出 `output/chart/` |
| `case_edit.json` (edit) | 源文件级编辑：对已生成的 `figure.svg` 做 rename/relabel/note 三种动作，before→after 写入 result.json `change_records` |

## 运行（全部自定位，任意 cwd 可跑）

```bash
python scripts/main.py --case examples/case.json --out /tmp/sse-out            # schematic
python scripts/main.py --case examples/case_chart.json --out /tmp/sse-out-ch   # chart
python scripts/main.py --case examples/case_edit.json \
    --edit-svg examples/output/figure.svg --out /tmp/sse-out-edit              # edit
python scripts/validate_result.py --case examples/case.json \
    --result /tmp/sse-out/result.json                                          # 契约校验 G1–G8
```

## v2 新增角色的演示

```bash
# ① 材料 → 候选 ER 清单（自动抽取 + 定位，_draft 标注，需人工复核）
python scripts/extract.py --inputs examples/sources/figure03-note.md \
    --out /tmp/sse-draft.json
# ② 字体栈探测（中文/公式渲染前必查）
python scripts/textfont.py --list
# ③ PDF 文本抽取（stdlib 回退；真实 PDF 用例见 TEST.md）
python scripts/pdftext.py --pdf <your.pdf> --out /tmp/pdftext-out
# ④ CP1 生成前 lint 门（main.py 默认自动运行）
python scripts/spec_lint.py --manifest /tmp/sse-draft.json
```

## 产物说明（`examples/output/`，本机 v2 流水线真实生成）

- `figure.svg`：可编辑分层 SVG —— 文字均为 `<text>`；元素带 `id` 与
  `data-entity/data-relation/data-source`；语义图层 `layer-*`；
  ER 清单内嵌于 `<metadata id="er-manifest">`（源文件自描述，供编辑）；
- `figure.png`：渲染预览（同一 layout+manifest 的 matplotlib 镜像，
  分辨率按 18cm 打印宽有效 DPI ≥300 输出）；
- `figure.pdf`：矢量导出件；
- `result.json`：契约 G1–G8 全过（含 `spec_lint` CP1 门与
  `determinism.spec_sha16` 探针）+ `_example` 状态说明标注"示例"；
- `chart/`、`edit/`：数据图与编辑任务的对应产物；
- `work/`：中间产物（layout.json、manifest.validated.json、
  draft-entities.json），作为可复核的过程证据。

本示例输出全部用 v2 流水线在本机生成并在任意新目录可复现（上面的
运行命令即生成方法），请勿将其作为正式案例答案提交。