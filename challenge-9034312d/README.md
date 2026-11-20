# challenge-9034312d 实验装置与技术路线图 Skill

玻尔产品周赛·北大专区·学术效率·第三期（efficiency-3）· figures 组。
依据科研材料生成**可编辑**的装置图/技术路线图（SVG 分层源文件 + PNG/PDF 预览 + result.json）。

## 运行方法

```bash
# 结构化案例（推荐）
python scripts/main.py --case /input/case.json --task /input/task.md --out /app/output

# 最小示例（本包自带，见 examples/）
python scripts/main.py --case examples/case.json --task examples/task.md --out D:/BuildTemp/smoke-9034312d

# Agent 复核后人工修正（可选项）：--merge <override.json>
python scripts/main.py --case examples/case.json --merge D:/BuildTemp/merge-demo.json --out D:/BuildTemp/smoke-9034312d-merge

# 交付自查
python scripts/check.py <output>/<case_id>/result.json
```

输出（`<out>/<case_id>/`）：`figure.svg`（可编辑源文件）、`figure.png`、`figure.pdf`、
`layout.json`（结构化中间表示）、`result.json`（contract 全字段 + case_id）。

## 依赖

| 依赖 | 用途 | 缺失时 |
|-|-|-|
| Python 3.10+（标准库） | 解析/布局/写 SVG | —（必需） |
| Pillow（PIL） | PNG 预览 | 仅 PNG 缺失，status=partial |
| reportlab | PDF 预览 | 仅 PDF 缺失，status=partial |
| 本机中文字体（msyh/simhei 等） | PNG 中文渲染 | fonts.found=false 如实记录 |

`cairosvg/svgwrite/python-pptx` 不需要：SVG 为手写 XML，预览直接从同一布局模型渲染。

## 限制

- 只负责绘图表达与可编辑交付；**不**做数值拟合、方案科学性判断、投稿格式适配；
- 文本无结构化时走朴素解构（仅串联步骤），设备连接需 Agent 复核；
- 复杂装配图的局部放大视图未内置，可在 Inkscape 微调源文件；
- 正式案例评分由平台执行，`examples/` 仅为接口演示（示例，非正式案例）。

## 失败处理

管线异常/输入缺失 → `scripts/main.py` 兜底写出 `status=failed` 的 result.json 并打印原因；
PNG/PDF 单个渲染失败 → 保留已有产物并 `status=partial`；所有不确定性写入
`result.json.uncertainty`（scope + issue + action），修改记录写入 `change_record`。

## 维护

- 图元/配色：`templates/palette.json`；词表：`scripts/model.py` 顶部 KINDS/RELATION_KINDS；
- 布局规则：`references/LAYOUT_SPEC.md` + `scripts/layout.py`；
- 契约与自查：`references/OUTPUT_CONTRACT.md` + `scripts/check.py`；
- 本地实测：`TEST.md`。