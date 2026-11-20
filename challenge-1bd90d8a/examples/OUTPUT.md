# 示例输出说明（示意输出，非正式案例）

> 以下输出由 `python scripts/main.py --case examples/case.json --out <out>` 在示例输入上
> 真实生成，仅用于展示接口与完整流程；**正式评分使用平台固定的 3 个案例，与示例无关**。
> 本目录只包含文本示意（case.json / task.md / data.csv / entities.json / 本说明）；
> 生成的 SVG/PNG/PDF 等二进制产物见 TEST.md 实测记录（示例运行目录），不入包。

## 示例产物清单（运行 main.py 后出现于 --out 目录）

| 文件 | 说明 |
|-|-|
| `figure-fig-01.svg` | 示例 Figure 1 可编辑分层 SVG（面板 A：24 h 剂量-响应柱状图，SE 误差线，** p=0.004 显著性标注；面板 B：时间曲线，按剂量分组）。每个柱/点带 `data-column`/`data-row-index` 等溯源属性 |
| `figure-fig-01.png` / `.pdf` | 同一图元场景的 PNG/PDF 预览 |
| `figure-fig-02.svg` | 示例 Figure 2 机制通路图（Wnt 信号转导简化图：7 节点 7 关系，激活箭头/抑制阻滞线，节点带 `data-cite` 来源） |
| `figure-fig-02.png` / `.pdf` | 预览 |
| `data_manifest.json` | 图元 ↔ 源数据（文件/列/行/值）映射，svg_id 对齐 |
| `validation.json` | 8 类标注校验结果 |
| `result.json` | 契约化结果（output_contract 字段 + case_id；status/sources/uncertainty/change_records 如实） |

## 数值核验示例（示例 Figure 1 面板 A）

源数据 `data.csv` 中 `time_h=24` 的行：剂量 0/1/5/20 mg/kg → 肿瘤体积均值
1180 / 902 / 610 / 485 μm³。SVG 中四根柱子的 `data-value` 依次为
1180.0 / 902.0 / 610.0 / 485.0，柱高与数值成比例（约 506/387/262/208 px，前底对齐）——
即"每个图元能回到源数据行"的直接演示。显著性线段位于 0 与 20 mg/kg 柱间，
`data-p_value=0.004`，来源注于图注（one-way ANOVA + Tukey HSD，转述非计算）。

## 快速验证

```bash
python scripts/main.py --case examples/case.json --out D:/BuildTemp/smoke-1bd90d8a
python scripts/validate_result.py --dir D:/BuildTemp/smoke-1bd90d8a --case examples/case.json
# 期望：status=completed，validate 全部 PASS
```