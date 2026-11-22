# TEST.md — 本机实测记录、负路径实测与验收判据

> 记录本包在**本机的真实执行结果**：命令、退出码、关键数值、产物清单。
> 全部命令都写成 `$SKILL_DIR/…` 形式并**在包外目录执行**（证明不依赖
> cwd = 技能根目录），输出一律写临时目录，**绝不在包内跑脚本**
> （否则生成 `scripts/__pycache__/`，验收器直接 FAIL）。
>
> 测试机：Windows 11 / Python 3.13.9；库实测版本：python-pptx 1.0.2 ·
> matplotlib 3.10.6 · Pillow 12.3.0 · reportlab 5.0.0 · numpy 可用；
> 无 LibreOffice —— 预览一律 PIL/reportlab 近似渲染并如实标注（`previews.method`）。

## T1 编译与导入 —— 通过

```bash
python -m py_compile "$SKILL_DIR"/scripts/*.py        # 10/10，exit 0
python -c "import sys; sys.path.insert(0,'$SKILL_DIR/scripts'); import deck_common, evidence_check, deck_extract, slide_text, deck_tool, render_qa, result_tool, selftest, make_examples, main; print('imports OK')"
# imports OK
```

## T2 冒烟：示例案例端到端（**验收主命令**）—— 通过（exit 0）

```bash
SKILL_DIR="<技能包绝对路径>"
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <临时输出目录>
```

末行与关键字段：

```
STATUS=success case_id=ppt-6ad93034-example-001 deck=work/deck.pptx slides=6
run_meta.checkpoints = {cp1_extract: true, cp2_plan: true, cp3_build: true, cp4_verify: true}
```

产物 25 个：`result.json`、`evidence_map.md`、`evidence_map.json`、`manifest.json`、
`changelog.jsonl`、`logs/run_*.log`、`work/deck.pptx`、`work/plan.json`、
`work/material_view.json`、`work/chart_results.csv.png`、`work/table_cache/results.csv`、
`work/preview/slide_01..06.png`、`work/preview/preview.pdf`、
`preview/slide_01..06.png`、`preview/preview.pdf`。

- 6 页角色依次 `cover / overview / question / method / result / takeaway`；
- 6/6 页有演讲备注（【讲解】【证据】【图表】）与证据脚注；
- 结果页 `figure.kind=chart_image`（重绘自 `results.csv`，note 标注重绘来源）；
- `evidence.unverified_claims` 为空；`run_meta.spec_lint = {"valid": true, "problems": [],
  "counts": {"pages": 6, "gaps": 1, "unverified": 0}}`（唯一 gap 是封面，规则允许）。

## T3 契约门与自检（独立复核命令）—— 均通过

```bash
python "$SKILL_DIR/scripts/result_tool.py" --result <out>/result.json --out-dir <out> \
    --case "$SKILL_DIR/examples/case.json" --envelope "$SKILL_DIR/templates/result_envelope.json"
# {"valid": true, "errors": [], "warnings": [], "gates": {G1..G8 全 true}}   exit 0

python "$SKILL_DIR/scripts/selftest.py" --out <out> --case "$SKILL_DIR/examples/case.json"
# all_pass: true（7/7）                                                        exit 0
```

契约覆盖核对：`OUTPUT_CONTRACT.md` §1 的 17 个顶层字段**全部在顶层**、缺项 0、
`null` 值 **0 个**；`deck` / `evidence` / `previews` 必备键缺项 0；
示例 `output_contract` 声明的 4 个字段按类型回显（`is_example` 为 **bool** `false`）。

`result.json` 顶层键（写出顺序）：
`case_id, title, status, created_at, skill_version, deck, evidence, previews, sources,
uncertainty, change_records, log, checks, evidence_map_json, manifest, environment,
is_example, run_meta`。

## T4 编辑模式 + 版本归档 —— 通过（exit 0）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <out-edit> \
    --edit "$SKILL_DIR/examples/edit_demo.json" --version v2      # exit 0
```

- `work/deck_v2.pptx` 与 `work/deck.pptx` **并存**（可回退），`work/plan.json` 同步更新；
- `changelog.jsonl` 记录 3 条 op（`update_bullet` / `add_note` / `reorder_pages`）；
- 编辑引入的文本同样过数字核验（"82.4% 对 81.1%" 可在材料中找到，D2/F6.4）。

## T5 页数变体（`--max-slides 10`）—— 通过（exit 0）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <out-10> --max-slides 10
# slides=10；角色：cover → overview → background → discussion → limitation
#              → question → method → result → result → takeaway
```

## T6 图表降级（`--no-chart`）—— 通过（exit 0）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <out-nc> --no-chart
```

结果页 `figure.kind=table`（降级为 **PPTX 原生可编辑表格**，note 说明重绘被关闭），
其余页 `figure.kind=none`；`status` 仍为 `success` —— 这是**已记录的受控降级**
而非失败（D9/F3.2；与 F5.1 的"有降级却标 success"区别在于：此处的降级由调用方
显式开关触发，且 `figure.note` 有对应说明）。

## T7 负路径（**本版重点**）：三族的真实降级记录

### T7a 材料缺失 → F1.1 —— 通过（exit 1）

```bash
# case 的 inputs.material 指向不存在的文件：["does-not-exist.md"]
python "$SKILL_DIR/scripts/main.py" --case <missing-case.json> --out <out-missing>
# STATUS=partial case_id=ppt-6ad93034-missing-001 deck= slides=0    exit 1
```

- `status=partial`、`deck.slide_count=0`：**不编造 deck**；
- `evidence.material_warnings` 如实列出缺失项（`输入缺失：does-not-exist.md（role=material-1）`）；
- `output_contract` 仍按四形态回显（`is_example=false`）；
- **未构建 `work/deck.pptx`** —— 这正是 D1 的判定点：材料缺失时宁可不出稿。

### T7b case.json 不可读 → F1.1 末列 —— 通过（exit 2）

```bash
python "$SKILL_DIR/scripts/main.py" --case <不存在的 case.json> --out <out-badcase>
# ERROR case load failed: 找不到 case 文件: …        exit 2
```

写出最小 `{"case_id":"unknown","status":"failed","error":"…","created_at":"…"}`，
**绝不假装成功**；exit 2 表示输入侧问题，重跑无用（§0 判读约定）。

### T7c 数字核验负例 → F1.4 / D2 —— 通过（exit 1）

```bash
python "$SKILL_DIR/scripts/evidence_check.py" --claim "S2-Attn 的 Q3 精度达到 82.4%" \
    --material "$SKILL_DIR/examples/material.md"        # ok=True  missing=[]      exit 0
python "$SKILL_DIR/scripts/evidence_check.py" --claim "某指标为 99.9%（材料中不存在）" \
    --material "$SKILL_DIR/examples/material.md"        # ok=False missing=['99.9%'] exit 1
```

**材料里没有的数字不放行**：`missing` 非空即 exit 1，且在完整流程中该主张会被
标成 `verified=false` 进 `unverified_claims`。

## T8 留出案例上的真实降级（F2.4 / D4 的活样本）

在**新写的一份留出材料**（多基准对照，8 页上限）上运行：

```bash
python "$SKILL_DIR/scripts/main.py" --case <holdout>/case.json --out <out-holdout>
# STATUS=partial   exit 1   slides=8
```

`run_meta.spec_lint` 原文：

```json
{"valid": false,
 "problems": ["page 6 bullet too long (chars=91, CJK-weighted=143 vs limit=90)"],
 "counts": {"pages": 8, "gaps": 1, "unverified": 0}}
```

`uncertainty` 对应一条 `CP2 plan lint 有偏差已记录（D4）: page 6 bullet too long …`。
这是**故意留下的真实记录**：越界 1 个字符也照样降级并留痕，而不是悄悄截断或改口径。
（契约门 `result_tool` 仍 `{"valid": true}` exit 0 —— 状态与门是两回事。）

## T9 确定性：同输入双跑 —— 内容级一致（如实记录）

| 比对对象 | 结果 |
|-|-|
| `work/deck.pptx` 内部部件（zip 条目按名排序后逐部件 sha256） | **64/64 一致**，差异部件 0 |
| `result.json`（剔除时间戳后逐叶比对） | 仅 1 处不同：`deck.slides[4].figure.image`（各自输出目录的图表路径） |
| `work/plan.json`（同上） | 仅 1 处不同：`pages[4].figure.image`（同一原因） |

结论：**内容确定**；原始字节差异只来自 zip 条目时间戳与机器路径前缀（D13）。

## 验收对照

| 验收项 | 结果 |
|-|-|
| 主命令在包外 cwd 执行且 exit 0 | ✅ `STATUS=success … slides=6`，25 个产物，裁决点 4/4 true |
| `result.json` 覆盖 `OUTPUT_CONTRACT.md` §1 全部字段 | ✅ 17/17 在顶层，0 缺项，0 个 `null` |
| 契约门与自检 | ✅ `{"valid": true}` exit 0；`all_pass=true` exit 0 |
| 编辑链路与版本归档 | ✅ `deck_v2.pptx` 与 `deck.pptx` 并存，changelog 有记录 |
| 页数变体 / 图表降级 | ✅ 10 页 / `table` 降级，均 exit 0 |
| 负路径三例（材料缺失 / case 不可读 / 数字缺失） | ✅ partial+1 / failed+2 / missing 非空+1 |
| 留出案例上的降级留痕 | ✅ `spec_lint.problems` 原文 + `uncertainty` 对应条目（T8） |
| 确定性双跑 | ✅ deck 逐部件 64/64 一致；result/plan 各仅 1 处机器路径差异 |
| 文档命令与脚本 `argparse` 逐字对应 | ✅ 全部文档命令均为 `"$SKILL_DIR/scripts/…"` 形式 |
| 包体形态 | ✅ 见下节 |

## 包体自检（提交前必跑）

```bash
# 1) 合规验收器：期望 PASS，0 条 FAIL
python <efficiency-3>/validate_pkg.py <本包目录>

# 2) 本机绝对路径残留检查（任意盘符 + 分隔符）
grep -rnE '[A-Za-z]:[\\/]{1,2}' <本包目录>
```

判读规则：
- **唯一允许的命中**是运行时字体探测的候选路径字符串（`scripts/deck_common.py`
  的 `_WIN_FONTS` 与 README §8 的说明）—— 它属于跨平台探测逻辑，不含任何
  "本机某次运行留下的痕迹"；除此之外不得有任何命中。
- 允许的扩展名只有 `.md/.py/.json/.txt/.csv/.yaml/.yml`；
- **二进制产物一律不入包**：`deck.pptx`、预览 `*.png`、预览 `*.pdf` 由运行时生成
  （清单见 `examples/EXPECTED-OUTPUT.md`）；`changelog.jsonl` 亦不入包；
- `examples/output/` 只放**文本**副本，且由 `scripts/make_examples.py` 自动把机器
  绝对路径净化成包内相对路径；
- `scripts/__pycache__/` 是运行时垃圾，提交前必须删除（否则验收器直接 FAIL）。

## 已知限制（本机验证结论）

- 预览是 PIL/reportlab 渲染，**不是** PowerPoint 导出件；需 Office 级 PDF 请在装有
  PowerPoint/LibreOffice 的机器上转换 `work/deck.pptx`。
- 预览使用主机字体（跨平台候选探测）；无 CJK 字体环境只影响预览，不影响 pptx，
  该事实写入 `previews.warnings`。
- 换行估算是字符宽度模型，极端长公式/高密度中文场景仍可能需人工微调（README §8）。
- `figure.image` 与 `sources[].path` 是**本次运行机器**的实际路径；跨机复跑前缀自然
  不同，内容不受影响（包内示例已由 `make_examples.py` 净化）。
- `case.json` 不可读时只写**最小** failed result（含 `case_id/status/error/created_at`），
  不满足完整契约字段 —— 这是 D1 的刻意取舍：输入侧失败优先"如实说明"而不是"凑字段"。
- 每次运行 <10 秒（本机实测约 2–3 秒），远低于 Runtime contract 的 900 秒预算。
