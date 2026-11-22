# TEST.md — 本机实测、机制判据复跑与验收判据

> 记录本包在**本机的真实执行结果**：命令、退出码、关键数值、产物清单。
> 全部命令写成 `$SKILL_DIR/…` 形式并**在包外目录执行**（证明不依赖
> cwd = 技能根目录），输出一律写临时目录。**绝不在包内跑脚本** ——
> 包内运行会生成 `scripts/__pycache__/`，验收器直接 FAIL；随包的探针与测量台
> 同样必须在**包外**运行。
>
> 测试机：Windows 11 / Python 3.13.9；库实测版本：python-pptx 1.0.2 ·
> matplotlib 3.10.6 · Pillow 12.3.0 · reportlab 5.0.0 · numpy 可用；
> 无 LibreOffice —— 预览一律 PIL/reportlab 近似渲染并如实标注。

## T1 编译与导入 —— 通过

```bash
python -m py_compile "$SKILL_DIR"/scripts/*.py        # 10/10，exit 0
python -c "import sys; sys.path.insert(0,'$SKILL_DIR/scripts'); import deck_common, evidence_check, deck_extract, slide_text, deck_tool, render_qa, result_tool, selftest, make_examples, main; print('imports OK')"
# imports OK
# 随包工具（在包外跑）：py_compile / import 均通过
python -m py_compile "$SKILL_DIR"/references/mechanism_probe.py "$SKILL_DIR"/references/measure_gain.py
```

## T2 冒烟：示例案例端到端（**验收主命令**）—— exit 0

```bash
SKILL_DIR="<技能包绝对路径>"
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <临时输出目录>
```

```
STATUS=success case_id=ppt-6ad93034-example-001 deck=work/deck.pptx slides=6
run_meta.checkpoints = {cp1_extract: true, cp2_plan: true, cp3_build: true, cp4_verify: true}
```

产物 25 个：`result.json`、`evidence_map.md/json`、`manifest.json`、`changelog.jsonl`、
`logs/run_*.log`、`work/deck.pptx`、`work/plan.json`、`work/material_view.json`、
`work/chart_results.csv.png`、`work/table_cache/results.csv`、
`work/preview/slide_01..06.png`、`work/preview/preview.pdf`、
`preview/slide_01..06.png`、`preview/preview.pdf`。

## T3 契约门与自检 —— 均通过（exit 0）

```bash
python "$SKILL_DIR/scripts/result_tool.py" --result <out>/result.json --out-dir <out> \
    --case "$SKILL_DIR/examples/case.json" --envelope "$SKILL_DIR/templates/result_envelope.json"
# {"valid": true, "errors": [], "warnings": [], "gates": {G1..G8 全 true}}   exit 0

python "$SKILL_DIR/scripts/selftest.py" --out <out> --case "$SKILL_DIR/examples/case.json"
# all_pass: true（7/7）                                                        exit 0
```

契约覆盖：`OUTPUT_CONTRACT.md` §1 的 17 个顶层字段全部在顶层、缺项 0、`null` **0 个**；
`deck`/`evidence`/`previews` 必备键缺项 0；示例 `output_contract` 的 4 个字段按类型回显。

## T4 ★ 机制判据探针实测（本版核心实测）

```bash
cp "$SKILL_DIR/references/mechanism_probe.py" <tmp>/     # 包外运行
python <tmp>/mechanism_probe.py --out <示例案例输出> --out <留出案例输出>
```

**真实运行上的判据结果**：

| 输出 | 状态 | M1 页单元 | M2 证据锚定 | M3 图表四态 | M4 版本链 | M5 契约 | 退出码 |
|-|-|-|-|-|-|-|-|
| 示例案例（6 页） | `success` | PASS | PASS | PASS | PASS | PASS | 0 |
| 留出案例（8 页） | `partial` | PASS | PASS | PASS | PASS | PASS | 0 |

**关键计数（由探针从产物算出）**：

| 项 | 示例案例 | 留出案例 |
|-|-|-|
| `M2.counts.numeric_claims` | 6 | 8 |
| `M2.counts.numeric_claims_with_evidence` | 6 | 8 |
| `M2.counts.unverified_claims` | 0 | 0 |
| `M3.kind_counts` | `{chart_image: 1, none: 5}` | `{chart_image: 1, none: 7}` |
| `M4.deck_versions` | `['deck.pptx']` | `['deck.pptx']` |
| 顶层 `null` 字段 | 0 | 0 |

## T5 ★ 探针负例控制（证明判据不是"恒真"）

把一次真实运行的输出复制一份，人为破坏三处机制痕迹：
① 清空第 1 页 `role`（打 M1）；② 把第 5 页 `figure.image` 指向不存在的文件（打 M3）；
③ 在顶层加一个值为 `null` 的字段（打 M5）。重跑探针：

```
== negctl  status=success
   M1_page_units      FAIL ['page 1 缺少 role']
   M2_anchors         PASS
   M3_figure_states   FAIL ["page 5 标为 chart_image 但图片文件不存在: 'work/does-not-exist.png'"]
   M4_versioning      PASS
   M5_contract        FAIL ['顶层存在 null 字段: [...]']
```

退出码 **1**。⇒ 探针**具备区分能力**：机制痕迹被破坏时会 FAIL；
未被破坏的 M2/M4 仍 PASS，说明它**只报真实缺陷**。

## T6 编辑模式 + 版本归档（M4 的用户面）—— 通过（exit 0）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <out-edit> \
    --edit "$SKILL_DIR/examples/edit_demo.json" --version v2      # exit 0
```

- `work/deck_v2.pptx` 与 `work/deck.pptx` **并存**（可回退），`work/plan.json` 同步更新；
- `changelog.jsonl` 记录 3 条 op（`update_bullet` / `add_note` / `reorder_pages`）；
- 编辑引入的文本同样过数字核验（"82.4% 对 81.1%" 可在材料中找到）—— **M2 在编辑链路上仍然生效**。

## T7 页数变体（`--max-slides 10`）—— 通过（exit 0）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <out-10> --max-slides 10
# slides=10；cover → overview → background → discussion → limitation
#            → question → method → result → result → takeaway
```

## T8 图表降级（`--no-chart`）—— 通过（exit 0）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <out-nc> --no-chart
```

结果页 `figure.kind=table`（原生可编辑表格），`status` 仍 `success`。
**探针口径**：`table` 是词表内的合法态，所以 `M3_figure_states` 仍 PASS ——
M3 判的是"**不许出现无数据来源的图**"，不是"必须有 `chart_image`"。

## T9 负路径（状态与退出码自洽）

### T9a 材料缺失（D1）

```bash
python "$SKILL_DIR/scripts/main.py" --case <missing-case.json> --out <out-missing>
# STATUS=partial case_id=ppt-6ad93034-missing-001 deck= slides=0     exit 1
```

- `deck.slide_count=0`：**不编造 deck**（`work/deck.pptx` 不存在）；
- `evidence.material_warnings` 列出缺失项；
- **探针在此场景下 M1 会 FAIL**（没有 slides）—— 这是**如实反映**而非缺陷，
  解释在 `references/failure-modes.md` §1 的对照表里。

### T9b case.json 不可读（D1 末列）

```bash
python "$SKILL_DIR/scripts/main.py" --case <不存在的 case.json> --out <out-badcase>
# ERROR case load failed: 找不到 case 文件: …                        exit 2
```

写出最小 `{"case_id":"unknown","status":"failed","error":"…","created_at":"…"}`。

### T9c 数字核验负例（D2 / M2）

```bash
python "$SKILL_DIR/scripts/evidence_check.py" --claim "S2-Attn 的 Q3 精度达到 82.4%" \
    --material "$SKILL_DIR/examples/material.md"        # ok=True  missing=[]       exit 0
python "$SKILL_DIR/scripts/evidence_check.py" --claim "某指标为 99.9%（材料中不存在）" \
    --material "$SKILL_DIR/examples/material.md"        # ok=False missing=['99.9%'] exit 1
```

## T10 公平对照（复算入口，协议见 `references/GAIN-PROTOCOL.md`）

```bash
cp "$SKILL_DIR/references/measure_gain.py" <tmp>/
python <tmp>/measure_gain.py --skill-dir "$SKILL_DIR" \
    --case "$SKILL_DIR/examples/case.json" --case <holdout>/case.json \
    --work <tmp>/work --out <tmp>/gain-report.json
```

实测汇总（两侧同一脚本、同一口径）：Q1/Q3/Q4/Q5 均由 0.0000 提升到 1.0000，
Q6 由 0.1429 提升到 1.0000；脚本耗时 0.391 s → 5.14 s（**如实报为成本**）。
其中留出案例的 S 侧状态为 `partial`（一条 91 字主张越界 1 字符，按 D4 记录降级），
**没有为了让对照好看而放宽纪律**；另有一条负面指标（单条长度合规率）原样保留在
协议文档 §3.3 中并说明为何不作为对照依据。

## T11 确定性：同输入双跑 —— 内容级一致

| 比对对象 | 结果 |
|-|-|
| `work/deck.pptx` 逐部件 sha256（zip 条目按名排序） | **64/64 一致**，差异 0 |
| `result.json`（剔除时间戳后逐叶比对） | 仅 1 处：`deck.slides[4].figure.image`（各自输出目录路径） |
| `work/plan.json`（同上） | 仅 1 处：`pages[4].figure.image` |

⇒ **复核与逐页 diff 是公平的**：同输入同 spec 无 `--edit` 时结构确定，
差异只在时间戳与机器路径前缀。

## 验收对照

| 验收项 | 结果 |
|-|-|
| 主命令在包外 cwd 执行且 exit 0 | ✅ `slides=6`、25 产物、checkpoints 4/4 true |
| 契约字段覆盖与 `null` 检查 | ✅ 17/17 顶层、0 缺项、0 个 `null` |
| 契约门与自检 | ✅ `{"valid": true}` exit 0；`all_pass=true` exit 0 |
| **机制判据 M1–M5** | ✅ 两个真实输出 5/5 PASS；负例控制 3 条 FAIL（证明有区分能力） |
| 编辑链路与版本归档 | ✅ `deck_v2.pptx` 与 `deck.pptx` 并存，changelog 有记录 |
| 页数变体 / 图表降级 | ✅ 10 页 / `table` 降级（M3 仍 PASS），均 exit 0 |
| 负路径三例 | ✅ partial+1 / failed+2 / missing 非空+1 |
| 公平对照可复跑 | ✅ 测量台随包；10 项指标全部由产物算出 |
| 确定性双跑 | ✅ deck 64/64 一致；result/plan 各仅 1 处机器路径差异 |
| 包体形态 | ✅ 见下节 |

## 包体自检（提交前必跑）

```bash
python <efficiency-3>/validate_pkg.py <本包目录>          # 期望 PASS，0 FAIL
grep -rnE '[A-Za-z]:[\\/]{1,2}' <本包目录>                # 期望只命中字体探测候选路径
```

判读规则：
- **唯一允许的命中**是运行时字体探测候选路径（`scripts/deck_common.py` 的
  `_WIN_FONTS` 与 README §9 的说明）；除此之外不得有任何命中。
- 允许的扩展名只有 `.md/.py/.json/.txt/.csv/.yaml/.yml`；
  `references/mechanism_probe.py`、`references/measure_gain.py` 均为文本 `.py`，符合白名单。
- **二进制产物一律不入包**（`deck.pptx`、预览 PNG/PDF、`changelog.jsonl`）；
  探针写出的 `mechanism-probe-report.json` 也**不要**放进包里（它写在运行时工作目录）。
- `scripts/__pycache__/` 提交前必须删除；**两个随包脚本都不要在包内运行**。

## 已知限制（本机验证结论）

- **判据是必要条件**：探针 PASS 只说明"机制痕迹在"，不说明"这一版讲得好"；
  内容质量由 `evidence_check` 与人工复核负责。
- 对照是**受控脚本级**对照（基线 = 题面点名失败形态的确定性代理实现），
  不是平台官方的 Agent 级对照；范围声明与局限见 `references/GAIN-PROTOCOL.md`。
- 探针的 M5 在**没有 `case.json`** 时退化为"顶层不得有 null"，
  无法核对 `output_contract` 声明字段是否逐项回显（那需要 case 文件）。
- 预览是 PIL/reportlab 渲染，**不是** PowerPoint 导出件；无 CJK 字体只影响预览。
- 换行估算为字符宽度模型，极端长公式/高密度中文场景仍可能需人工微调。
- `figure.image` 与 `sources[].path` 是**本次运行机器**的实际路径；跨机复跑前缀自然不同。
- `case.json` 不可读时只写**最小** failed result（不满足完整契约字段）—— D1 的刻意取舍。
- 每次运行 <10 秒（本机约 2–3 秒），远低于 900 秒预算。
