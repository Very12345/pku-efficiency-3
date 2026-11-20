# TEST.md — 本地实测记录

> 测试机：Windows + Anaconda Python 3.13.9（本目录 python 命令）。
> 库版本实测：python-pptx 1.0.2 · matplotlib 3.10.6 · Pillow 12.3.0 ·
> reportlab 5.0 · numpy 可用；cairosvg/svgwrite 未使用。
> 时间：2026-11-20（Asia/Shanghai）。所有测试均在包根目录运行，
> 输出写到 `D:/BuildTemp/`（包外），避免污染技能包。

## 0. 语法检查

```
python -m py_compile scripts/*.py
```
结果：9/9 通过（common, material, planner, charting, deck_builder, render,
result, main, check_contract）。

## 1. 冒烟测试（验收命令）

```
python scripts/main.py --case examples/case.json --out D:/BuildTemp/smoke-ppt-6ad93034
```
结果：`STATUS=success case_id=ppt-6ad93034-example-001 deck=work\deck.pptx slides=6`；退出码 0。

产出文件（真实存在）：
- `work/deck.pptx`（6 页可编辑演示文件，含 media/image1.png 重绘图）
- `work/plan.json`（页面模型：index/role/title/claims/evidence/figure/notes）
- `work/table_cache/results.csv`（源数据表副本）
- `work/preview/slide_01.png … slide_06.png` + `preview/preview.pdf`
- `work/material_view.json`、`logs/run_*.log`
- `result.json`、`evidence_map.md`、`changelog.jsonl`、`manifest.json`
- `preview/`（输出根，共 6 张 PNG + PDF）

内容核验（python-pptx 重新打开）：
- 6 页角色依次：cover / overview / question / method / result / takeaway；
- 每页含演讲备注（【讲解】【证据】【图表】）与页级证据脚注；
- 第 3 页主张=材料中"研究问题：…"原句；第 5 页主张引用表数据
  "results.csv 为 82.4（Q3 (%)）"，配套重绘图来自 results.csv（未改数据）；
- 证据映射：`result.json.evidence.map` 6 条，`unverified_claims` 为空。

## 2. 契约校验（验收命令）

```
python scripts/check_contract.py D:/BuildTemp/smoke-ppt-6ad93034/result.json examples/case.json
```
结果：`"valid": true`，problems 为空；退出码 0。同时验证了
`case.json.output_contract` 声明的 5 个字段（case_id/deck/evidence/previews/
is_example）均已镜像到 result.json 顶层。

## 3. 局部编辑 + 版本归档

```
python scripts/main.py --case examples/case.json --out D:/BuildTemp/smoke-edit \
    --edit examples/edit_demo.json --version v2
```
结果：`STATUS=success slides=6`；应用 3 个 op（update_bullet / add_note /
reorder_pages）。核验：
- `work/deck_v2.pptx` 与 `work/deck.pptx` 并存（版本可回退）；
- `changelog.jsonl` 记录 3 条 `{version:"v2", op, page, target, reason}`；
- contract 校验 `valid: true`。
- UTF-8 完整性：编辑 reason（"把结果主张改成更清晰的对比表述"）读回一致。

## 4. 模板/配置变体

```
python scripts/main.py --case examples/case.json --out D:/BuildTemp/smoke-10 --max-slides 10
```
结果：`slides=10`，角色分配为 cover+overview+background+question+method+
result×4+takeaway（10 页时插入 2 个额外结果页 + 背景/讨论自动展开）。

```
python scripts/main.py --case examples/case.json --out D:/BuildTemp/smoke-nc --no-chart
```
结果：`STATUS=success`；图表降级为 PPTX 原生可编辑表格
（figure.kind="table"，note 说明 matplotlib 重绘被关闭）。

## 5. 异常/降级路径

```
# 构造缺文件的 case（material 指向不存在的文件）
python scripts/main.py --case D:/BuildTemp/broken_case.json --out D:/BuildTemp/smoke-broken
```
结果：仍产出 6 页 deck；`result.json.material_warnings` 如实列出 3 条缺失
（missing_material.md / results.csv / task.md）；`evidence.unverified_claims`
3 条（无数据支撑的主张被标记而非编造）；状态 success（核心产物完成）
但所有缺失与未核验项均有解释。

## 6. 验收对照

| 验收项 | 结果 |
|-|-|
| 验收命令 `python scripts/main.py --case examples/case.json --out D:/BuildTemp/smoke-ppt-6ad93034` 真实产出 | ✅ deck.pptx + 6 PNG + PDF + result.json 等 12+ 文件 |
| SKILL.md 完整（frontmatter name/description + 用途/适用/输入输出/步骤/异常/自查） | ✅（第 0/5/6 节核验） |
| OUTPUT_CONTRACT.md 定义 result.json 契约 | ✅（check_contract.py 依据它自动校验） |
| 不编造数据 | ✅ unverified_claims 机制 + 诚实占位 + 样例标注"示例，非正式案例" |

## 7. 已知限制（本机验证结论）

- 预览为 PIL/reportlab 渲染，**不是** PowerPoint 导出件；如需要 Office 级
  PDF，请在有 PowerPoint/LibreOffice 的机器上用 office_convert 转换 deck.pptx。
- 预览绘制使用主机字体（微软雅黑）；无 CJK 字体环境只影响预览，不影响 pptx。
- 换行估算是字符宽度模型，极端长公式密度可能需要人工微调（已记录在
  README 限制节）。
- 每次运行时间 <60 秒（本机实测约 2–3 秒），符合 Runtime contract 900 秒
  预算的多案例复跑要求。