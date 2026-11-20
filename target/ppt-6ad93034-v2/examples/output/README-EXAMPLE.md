# examples/output — 示意输出（示例，非正式案例）

本目录是 `examples/case.json` + `examples/task.md` 用 **v2 流水线**
（`python scripts/main.py --case examples/case.json --out <输出目录>`）在本机
真实跑出的**示意产物副本**，文件名统一带 `.example.` 标注。**它们不是、也不
代表平台正式 3 个固定案例的输出**；正式案例由平台提供，Skill 在运行时依据
实际输入重新生成全部产物。

| 文件 | 说明 |
|-|-|
| `deck.example.pptx` | 可编辑演示源（6 页：cover/overview/question/method/result/takeaway；每页含演讲备注 + 证据脚注；结果页嵌入 charts 重绘图） |
| `result.example.json` | result.json 全文（output_contract 四形态回显 + case_id + G 门通过 + run_meta.checkpoints 全 true + environment） |
| `plan.example.json` | 页面模型（index/role/title/claims/evidence/figure/notes）——可编辑源 |
| `material_view.example.json` | 材料抽取视图（章节/数据表/图·表提及） |
| `evidence_map.example.md` | 逐页证据映射（人读表格，mapped 行） |
| `evidence_map.example.json` | 逐页证据映射（机器可读，与 md 同源） |
| `changelog.example.jsonl` | 版本记录（本次运行 start/图绑定/build 等） |
| `manifest.example.json` | 全部产物 sha256（来自冒烟运行的快照，路径相对该运行输出目录） |
| `chart-results.example.png` | 从 results.csv 原样重绘的示例图（matplotlib，未改数据） |
| `preview/slide_*.example.png` + `preview.example.pdf` | 每页 PIL 预览 + reportlab 文本预览（**非 PowerPoint 导出**，文件名与 result.previews.method 如实标注） |

复跑命令见 `examples/README.md`。正式运行时 Agent 必须依据案例实际提供的
论文与模板重新生成全部内容；本目录任何文件不得冒充正式案例结果。