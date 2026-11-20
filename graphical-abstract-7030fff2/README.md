# Graphical Abstract Skill — README

面向「玻尔产品周赛 · 北大专区 · 学术效率」第三期题目 `graphical-abstract-7030fff2`
（Graphical Abstract 图形摘要，figures 组）制作的 Skill 包。只负责制作，不负责提交。

## 一、这是什么

一个可被 DeepSeek Harness 加载执行的 Skill：给定科研材料（`case.json` + `task.md` + 材料文件），
自动完成 **实体/关系/数据抽取（带来源定位）→ 确定性版面（问题→方法→结果→结论）→ 数据编码与图例
→ 可编辑分层 SVG 源 → PNG/PDF 渲染件 → 自查审计 → 结构化 result.json** 的全流程。

核心承诺（可在 `TEST.md` 复核）：

1. **不编造数据**：图上每个数值都能在材料中定位（`data-src`），缺值只进 `uncertainty` 并占位。
2. **同输入同输出**：布局为纯函数，两次运行 SVG/PNG 逐字节一致（sha256 见 `TEST.md`）。
3. **可继续编辑**：SVG 文字是真 `<text>`、7 个命名图层、元素带溯源属性，可在 Inkscape/Illustrator 续改。
4. **可复核**：`result.json` 回显案例 `output_contract` 全部字段，并带 `sources/uncertainty/change_records/audit`。

## 二、运行方法

### 依赖

- Python ≥ 3.9（本机实测 3.13.9 / Anaconda）
- 标准库即可出全套产物；可选增强：`Pillow`（常用字体渲染）、`matplotlib`（矢量 PDF + 高质量 PNG）。
  均缺失时自动回退纯 Python PNG（文字占位框并如实记录 `render_log.json`）。
- 不需要 cairosvg / svgwrite / inkscape / LibreOffice。

### 命令

```bash
cd <skill root>
python scripts/main.py \
  --case examples/case.json \
  --task examples/task.md \
  --material examples/material.md \
  --out <输出目录>
```

参数：

| 参数 | 默认 | 说明 |
|-|-|-|
| `--case` | （必填） | 案例 `case.json` 绝对或相对路径 |
| `--task` | `<case 目录>/task.md` | 任务说明（含 `# 问题/方法/结果/结论` 小节则映射为面板要点） |
| `--material` | 来自 `case.json.source_material` | 材料文件或目录（md/txt/tex/json/csv…） |
| `--out` | `<skill>/out` | 输出目录（官方运行时为 `/app/output`） |
| `--raster-scale` | `constraints.raster_scale`（2） | PNG 相对画布放大倍数 |
| `--pdf` / `--no-pdf` | `constraints.pdf`（true） | 是否生成 PDF 预览 |

退出码：`0` 成功（可含警告→status=partial）、`1` 输入错误、`2` 内部错误（stderr 有说明）。

### 产物

见 `references/OUTPUT_CONTRACT.md`：`<case_id>_graphical_abstract.svg/.png/.pdf`、
`result.json`、`spec.json`、`content.json`、`audit.json`、`render_log.json`。

### 最小示例

`examples/` 内含合成案例（**示例，非正式案例**）：`case.json` + `task.md` + `material.md`，
示例产物在 `examples/output/`（SVG/PNG/PDF/result.json/render_log.json），运行上面的命令即可复现。

## 三、与题目评分维度的对应

`references/RUBRIC_MAP.md` 给出五维（实际效果 40 / 使用增益 25 / 创新增益 15 / 可靠体验 10 /
生态贡献 10，另 +5 GitHub 链接）逐评分点的落点与证据。

## 四、限制与说明（诚实清单）

1. 布局是「结构稳定」的确定性版式，不是期刊级美术设计；复杂图（多通路、大图网络）需在 SVG 中二次调整，
   引擎保证的是结构与溯源一致性而非像素级美观。
2. PNG 预览为渲染示意：字体采用本机可用字体（中文优先 Microsoft YaHei/SimHei），跨机可能替换；
   正式出版请基于 SVG 源在目标环境导出。
3. 抽取规则是保守启发式：材料中的自由文本（非 `键: 值` 行、非箭头行）不会强行猜数值；
   复杂嵌套结构请优先用 JSON 字段表达。
4. 三译文假阳性已内置防御：`output_contract` 字段冲突时镜像进 `output_contract_echo`，不覆盖信封。
5. PDF 依赖 matplotlib；官方运行时若无 matplotlib 则 PDF 自动跳过并写明原因（PNG 仍保证）。

## 五、失败处理速查

| 失败 | 处置 |
|-|-|
| `case.json` 打不开 | exit 1，stderr 说明；不写半成品 result.json |
| 材料缺失 | 继续运行并记 `uncertainty`；实体/数据为空时 status=partial |
| 数值缺 | 图上「数值缺失」占位 + `audit.missing_values` + `uncertainty` |
| 渲染库全缺 | 纯 Python PNG 兜底（zlib+struct），`render_log.json` 记录 |
| 布局溢出 | 自动缩字号/截断并记 `layout_log`；仍越界的进 `audit.bounds` |
| 结果不一致 | `audit.determinism_probe`（spec hash）定位是哪份输入变化导致 |

详细失败模式表见 `SKILL.md` §4；本地实测记录见 `TEST.md`。

## 六、发布

- `GITHUB_URL.txt`：第一行占位链接，由发布代理覆写为公开仓库精确地址；第二行为本作品相对路径。
- 本包不包含任何平台凭据、预置答案或隐藏测试数据。