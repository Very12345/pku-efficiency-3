# examples/output — 示意输出（示例，非正式案例）

> ⚠ 本目录全部产物均为**示例输出**，由本机 v2 流水线在 examples/case.json 与
> examples/apparatus_spec.example.json 上真实运行生成，**不是组织方正式案例的
> 结果**。正式案例与白板由平台提供，本包不携带任何预制答案。

## 产物一览

| 目录 | 图类 | figure.svg sha256 | verify |
|-|-|-|-|
| `demo-biotech-route-01/`（CRISPR 文库筛选技术路线，route） | route | `f8b01ce2…` | ok=true，G1–G10 全过，status=success |
| `demo-apparatus-001/`（冷冻干燥机装置，apparatus） | apparatus | `c6d422fe…` | ok=true，G1–G10 全过，status=success |

每个目录含 7 个文件：

```
evidence.json      证据链（实体/关系 locator+quote + 材料 sha256）
layout.json        布局模型（SIR→几何，可复核重绘）
figure.svg         可编辑分层 SVG 源文件（5 层 layer:*；<text> 真实文本可编辑）
figure.png         PNG 预览（200 DPI，PIL + 本机中文字体）
figure.pdf         PDF 预览（reportlab 矢量 CID 字体）
verify_report.json 校验报告（图层/文本/箭头/编号/图例/连接规则 + spec_sha16 确定性探针）
result.json        结构化结果（output_contract 全字段 + case_id + evidence + verify）
```

## 复跑方式（同输入 → 同产物）

```bash
# route 示例
python scripts/main.py --case examples/case.json --task examples/task.md --out D:/BuildTemp/repro-route
# apparatus 示例
python scripts/main.py --case examples/apparatus_spec.example.json --out D:/BuildTemp/repro-app
```

确定性：同输入下 `figure.svg / layout.json / evidence.json / verify_report.json`
逐字节一致（见 TEST.md T3 实测）；`result.json` 仅 `change_record` 时间戳与
`execution.out_dir`（输出路径参数）不同，`checksum` 一致。

## 编辑示例（mutation）

`examples/route_spec.mutation.example.json` 演示「编辑既有图稿」：作为 `--merge`
传给 main.py，同名 id 替换（如 E5 标签）、新 id 追加（E11 对照孔 + R10 复筛回流 +
R11 流向），动作自动写入 change_record。复跑：

```bash
python scripts/main.py --case examples/case.json --task examples/task.md \
  --merge examples/route_spec.mutation.example.json --out D:/BuildTemp/repro-merge
```