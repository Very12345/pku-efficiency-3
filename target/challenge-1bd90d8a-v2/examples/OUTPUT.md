# 示例输出说明（示意输出，非正式案例）

> 本目录（examples/）是 Skill 自带**最小示例**，用于演示调用方式、CP1–CP6 全链路、
> 契约四形态回显与双校验；**正式评分使用平台固定的 3 个案例，与示例无关**。
> `examples/output/` 下的产物（`*.example.*`）由
> `python scripts/main.py --case examples/case.json --out <out> --style nature`
> 在本机示例输入上**真实生成**（TEST.md T7 与实时运行逐字节对拍），仅作示意，
> 不冒充正式案例结果。

## 输入文件

| 文件 | 说明 |
|-|-|
| `case.json` | 示例案例：fig-01 `panel`（bar+line，`style:"nature"`）+ fig-02 `network`（Wnt 通路）；含 output_contract 四形态字段声明、manual_confirmations |
| `task.md` | 示例任务说明（两张图：剂量-时间响应柱状图/时间曲线 + 机制通路图） |
| `data.csv` | 示例源数据（8 行：dose_mg_kg / time_h / mean_um3 / se_um3 / n） |
| `entities.json` | 示例生物源实体/关系（7 节点 7 关系，含 cite 来源、手工布局坐标） |
| `material.md` | 示例生物源材料（ENTITY:/REL: 行语法 + 词表扫描样例） |
| `output/` | 示例产物（*.example.*，见下） |

## 示例产物清单（examples/output/，真实运行所得）

| 文件 | 说明 |
|-|-|
| `figure-fig-01.example.svg` | 示例 Figure 1 可编辑分层 SVG（面板 A：24 h 剂量-响应柱状图，SE 误差线，** p=0.004 显著性标注；面板 B：时间曲线，按剂量分 4 系列）。每个柱/点带 `data-column`/`data-row-index`/`data-value` 等溯源属性；分层 `<g id="layer-*">`、`<metadata id='provenance'>` |
| `figure-fig-01.example.png` / `.pdf` | 同一图元场景的 PNG/PDF 预览 |
| `figure-fig-02.example.svg` | 示例 Figure 2 机制通路图（Wnt 信号转导简化图：激活箭头/抑制阻滞线，节点带 `data-cite` 来源，边带关系语义色/线型） |
| `figure-fig-02.example.png` / `.pdf` | 预览 |
| `data_manifest.example.json` | 图元 ↔ 源数据（文件/列/行/值）映射，svg_id 对齐 |
| `validation.example.json` | 八类标注校验结果（溯源/图例-系列/轴范围/CJK/显著性/遮挡/轴单位/空值） |
| `mapcheck_report.example.json` | 数据↔图元双向核对报告（121 checked / 0 mismatched / 0 unmatched） |
| `figcheck_report.example.json` | 交付审计报告（G1–G8 全过 + 六类检查点逐项盖戳） |
| `result.example.json` | 契约化结果（output_contract 四形态字段全回显 + case_id + checkpoints + gates；status=completed） |

## 数值核验示例（示例 Figure 1 面板 A）

源数据 `data.csv` 中 `time_h=24` 的行：剂量 0/1/5/20 mg/kg → 肿瘤体积均值
1180 / 902 / 610 / 485 μm³。SVG 中四根柱子的 `data-value` 依次为
1180.0 / 902.0 / 610.0 / 485.0，柱高与数值成比例（约 510.8/390.5/264.1/210 px，
前底对齐）——即「每个图元能回到源数据行」的直接演示。显著性线段位于 0 与 20 mg/kg
柱间，`data-p_value=0.004`，来源注于图注（one-way ANOVA + Tukey HSD，转述非计算）。
`mapcheck_report.example.json` 记录了逐元素的 文件→列→行→值 核对明细。

## 快速验证

```bash
python scripts/main.py --case examples/case.json --out D:/BuildTemp/smoke-1bd90d8a
python scripts/figcheck.py --dir D:/BuildTemp/smoke-1bd90d8a --case examples/case.json
# 期望：status=completed，GATES: G1–G8 = OK，exit 0
python scripts/mapcheck.py --dir D:/BuildTemp/smoke-1bd90d8a --case examples/case.json
# 期望：ALL PASS（121 checked / 0 mismatched / 0 unmatched），exit 0
```

完整实测记录（命令/产物 sha256/确定性结论）见 `TEST.md`。