# TEST.md — 本地实测记录（v2；运行者：制作子代理 agent-63，2026-11-21 02:0x +08）

> 本文件记录 v2 包在本机的真实执行结果，供独立复核。机器：Windows 11 /
> Python 3.13.9（命令 `python`）；库实测版本：python-pptx 1.0.2 ·
> matplotlib 3.10.6 · Pillow 12.3.0 · reportlab 5.0.0 · numpy 可用；
> cairosvg/svgwrite 未使用；无 LibreOffice —— 预览一律 PIL/reportlab
> 近似渲染并如实标注（`previews.method`）。
> 所有测试在包根目录运行，输出写 `D:/BuildTemp/`（包外），不污染技能包。

## T1 编译与导入检查 —— 通过

```bash
python -m py_compile scripts/*.py        # 9/9 通过
python -c "import sys; sys.path.insert(0,'scripts'); import deck_common, evidence_check, deck_extract, slide_text, deck_tool, render_qa, result_tool, selftest, main; print('imports OK')"
# imports OK
```

## T2 冒烟：示例案例端到端（验收命令）—— 通过（exit 0）

```bash
python scripts/main.py --case examples/case.json --out D:/BuildTemp/smoke-ppt-6ad93034-v2
```

输出摘要（运行日志末行）：

```
STATUS=success case_id=ppt-6ad93034-example-001 deck=work/deck.pptx slides=6
```

退出码 **0**；`run_meta.checkpoints` 四门全 true：
`{cp1_extract: true, cp2_plan: true, cp3_build: true, cp4_verify: true}`。

**产出文件（真实存在，26 个）**：`work/deck.pptx`、`work/plan.json`、
`work/material_view.json`、`work/chart_results.csv.png`、`work/table_cache/`
`results.csv`、`work/preview/slide_01..06.png` + `preview.pdf`、根 `result.json`、
`evidence_map.md`、`evidence_map.json`、`changelog.jsonl`、`manifest.json`、
`preview/`（6 PNG + PDF）、`logs/run_*.log`。

内容核验（python-pptx 重新打开）：
- 6 页角色依次：cover / overview / question / method / result / takeaway；
- 6/6 页均有演讲备注（【讲解】【证据】【图表】）；每页有证据脚注；
- 结果页（第 5 页）figure.kind=`chart_image`（重绘自 results.csv，figure
  note 标注重绘来源），claims=3（含"表中数值直接取自源数据，未取整、未编造"）；
- `result.json.evidence.unverified_claims` 为空（页面数字全部可在材料中找到）；
- `evidence_map.json` 与 `evidence_map.md` 同源（rows=6，gap=0）。

**CP4 契约门（独立复核命令，exit 0）**：

```bash
python scripts/result_tool.py --result D:/BuildTemp/smoke-ppt-6ad93034-v2/result.json \
    --out-dir D:/BuildTemp/smoke-ppt-6ad93034-v2 --case examples/case.json \
    --envelope templates/result_envelope.json
# {"valid": true, "errors": [], "warnings": []}
python scripts/selftest.py --out D:/BuildTemp/smoke-ppt-6ad93034-v2 --case examples/case.json
# all_pass: true（7/7：pptx_reopen / result_json / contract_keys / unverified_claims /
#           evidence_map_md / evidence_map_json / previews）
```

output_contract 五字段（case_id/deck/evidence/previews/is_example）均回显到
result.json 顶层且无 null（G2）；`is_example: true` 由案例声明默认给 bool 空值。

## T3 编辑模式 + 版本归档（演示稿迭代）—— 通过（exit 0）

```bash
python scripts/main.py --case examples/case.json --out D:/BuildTemp/smoke-edit-v2 \
    --edit examples/edit_demo.json --version v2
python scripts/result_tool.py --result D:/BuildTemp/smoke-edit-v2/result.json \
    --out-dir D:/BuildTemp/smoke-edit-v2 --case examples/case.json \
    --envelope templates/result_envelope.json    # exit 0
```

- `work/deck_v2.pptx` 与 `work/deck.pptx` 并存（版本可回退）；
- `changelog.jsonl` 记录本次运行的 3 个编辑 op（update_bullet / add_note /
  reorder_pages，页面 5 与全部页序）；
- 编辑文本经数字再核验（update_bullet 中 "82.4% 对 81.1%" 可在材料中找到 →
  verified=true）。

## T4 页数变体（--max-slides 10）—— 通过（exit 0）

```bash
python scripts/main.py --case examples/case.json --out D:/BuildTemp/smoke-10-v2 --max-slides 10
```
`slides=10`，角色分配：cover + overview + background + discussion + limitation
+ question + method + result ×2 + takeaway（富余页先插背景/讨论/局限，再增加
结果页——蓝图规则 DECK_SPEC.md §1）。契约门 exit 0。

## T5 图表降级（--no-chart）—— 通过（exit 0）

```bash
python scripts/main.py --case examples/case.json --out D:/BuildTemp/smoke-nc-v2 --no-chart
```
结果页 figure.kind=`table`（PPTX 原生可编辑表格降级），note 说明图表重绘被
`--no-chart` 关闭；其余 5 页 figure.kind=`none`。

## T6 确定性：同输入双跑 —— 内容级一致（如实记录）

两次运行到**不同输出目录**：

```bash
python scripts/main.py --case examples/case.json --out D:/BuildTemp/det-A-v2
python scripts/main.py --case examples/case.json --out D:/BuildTemp/det-B-v2
```

- deck.pptx 内部部件（zip 条目按文件名排序后逐部件 sha256）：A/B 均为
  `edecf9d198e66c964d772c2616f2e013c1aada7eabbd98a0041ad34d39ed30b8` —— **一致**；
- plan.json / result.json 在去除时间戳（created_at / run_meta.timestamp /
  generated_at / log 文件名）后**唯一差异**是
  `deck.slides[4].figure.image` 与 `plan.pages[4].figure.image` —— 指向本地
  **绝对路径**的图表文件（随 --out 目录名变化，属机器本地路径，非内容差异）；
- 同一输出目录运行两次：plan.json 完全一致、result.json 去除时间戳后完全一致
  （`identical: True`）。

结论：**内容确定**；原始字节因 zip 条目写入时间戳与绝对路径不同而不逐字节
一致（如实声明，非内容变化）。

## T7 材料缺失的诚实失败路径（D1）—— 通过（exit 1，status=partial）

```bash
python scripts/main.py --case D:/BuildTemp/missing-case.json --out D:/BuildTemp/smoke-missing-v2
```
- `STATUS=partial`，exit 1；result.json `status=partial`、
  `material_status=unreadable`、`deck.slide_count=0`（**不编造 deck**）；
- `evidence.material_warnings` 如实列出缺失文件（no-material.md / task.md）；
- case.json 本身不可读时 exit 2 且写最小 `status=failed` result.json。

## T8 单条主张数字核验（evidence_check CLI）—— 通过

```bash
python scripts/evidence_check.py --claim "S2-Attn 的 Q3 精度达到 82.4%" --material examples/material.md
# ok=True missing=[]      exit 0
python scripts/evidence_check.py --claim "某指标为 99.9%（材料中不存在）" --material examples/material.md
# ok=False missing=['99.9%']   exit 1
```

## 验收对照

| 验收项 | 结果 |
|-|-|
| 验收命令 `python scripts/main.py --case examples/case.json --out D:/BuildTemp/smoke-ppt-6ad93034-v2` 真实产出 exit 0 | ✅ STATUS=success，26 个产物，checkpoints 4/4 true |
| result.json 契约在 OUTPUT_CONTRACT.md 定义且自动校验 | ✅ G1–G8 全过 + result_envelope.json 类型 (G8) |
| 确定性双跑 | ✅ deck 逐部件 sha256 一致；同目录 result/plan 去除时间戳后完全一致（如实记录绝对路径差异） |
| SKILL.md 完整（frontmatter + 用途/输入输出/执行步骤 CP1–CP4/异常/自查 + 决策规则 D1–D12 + 检查点） | ✅ |
| 脚本自定位（os.path.dirname(__file__)），任意 cwd 可跑 | ✅（本测试全部在包根运行；脚本内部全部自定位） |
| 高分意图结构（edit_ops 目录 / result 信封 / evidence_check / render_qa / selftest） | ✅ 见 COMPARE.md |
| 不编造数据 | ✅ unverified_claims 机制 + 诚实占位 + 样例标注"示例，非正式案例" |

## 已知限制（本机验证结论）

- 预览为 PIL/reportlab 渲染，**不是** PowerPoint 导出件；如需 Office 级 PDF，
  请在装有 PowerPoint/LibreOffice 的机器上用 office_convert 转换 deck.pptx。
- 预览绘制使用主机字体（微软雅黑）；无 CJK 字体环境只影响预览，不影响 pptx。
- 换行估算是字符宽度模型，极端长公式密度可能需要人工微调（已记录 README）。
- figure.image / plan 里的图表路径为本地绝对路径，跨机复跑会自然改变（内容
  不受影响）。
- 每次运行 <10 秒（本机实测约 2–3 秒），符合 Runtime contract 900 秒预算的
  三案例复跑要求。