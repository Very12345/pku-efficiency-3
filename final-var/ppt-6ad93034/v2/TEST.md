# TEST.md — 本机实测、对照复算与验收判据

> 全部命令写成 `$SKILL_DIR/…` 形式并**在包外目录执行**（证明不依赖
> cwd = 技能根目录），输出一律写临时目录。**绝不在包内跑脚本** ——
> 包内运行会生成 `scripts/__pycache__/`，验收器直接 FAIL；对照测量脚本同理，
> 请先复制到包外再跑。
>
> 测试机：Windows 11 / Python 3.13.9；库实测版本：python-pptx 1.0.2 ·
> matplotlib 3.10.6 · Pillow 12.3.0 · reportlab 5.0.0 · numpy 可用；
> 无 LibreOffice —— 预览一律 PIL/reportlab 近似渲染并如实标注。

## T1 编译与导入 —— 通过

```bash
python -m py_compile "$SKILL_DIR"/scripts/*.py        # 10/10，exit 0
python -c "import sys; sys.path.insert(0,'$SKILL_DIR/scripts'); import deck_common, evidence_check, deck_extract, slide_text, deck_tool, render_qa, result_tool, selftest, make_examples, main; print('imports OK')"
# imports OK
```

## T2 冒烟：示例案例端到端（**验收主命令**，也是对照的"条件 S"）—— exit 0

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

逐页结构（**Q1/Q4/Q5 的判定面**，实测）：

| 页 | role | claims | notes | evidence_footer |
|-|-|-|-|-|
| 1 | cover | 0 | 1 | ✅ |
| 2 | overview | 2 | 2 | ✅ |
| 3 | question | 2 | 1 | ✅ |
| 4 | method | 4 | 1 | ✅ |
| 5 | result | 3 | 1 | ✅ |
| 6 | takeaway | 2 | 2 | ✅ |

⇒ Q1 = 6/6 = 1.0；Q4 = 1.0；Q5 = 1.0；`evidence.unverified_claims` 为空。

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

## T4 编辑模式 + 版本归档 —— 通过（exit 0）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <out-edit> \
    --edit "$SKILL_DIR/examples/edit_demo.json" --version v2      # exit 0
```

`work/deck_v2.pptx` 与 `work/deck.pptx` 并存；`changelog.jsonl` 记录 3 条 op；
编辑引入的文本同样过数字核验（"82.4% 对 81.1%" 可在材料中找到）。

**对"增益"的意义**：E1 编辑粒度实测为 `local_op_with_version_archive`、
E2 版本归档 ≥1 —— 对照协议里 B 侧这两项恒为 0（整稿重生成）。

## T5 页数变体（`--max-slides 10`）—— 通过（exit 0）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <out-10> --max-slides 10
# slides=10；cover → overview → background → discussion → limitation
#            → question → method → result → result → takeaway
```

## T6 图表降级（`--no-chart`）—— 通过（exit 0）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <out-nc> --no-chart
```

结果页 `figure.kind=table`（原生可编辑表格），`status` 仍 `success`。
**这一条是"对照条件可控"的证据**：开关存在，两个条件才能真正对齐。

## T7 负路径 —— 状态与退出码自洽

### T7a 材料缺失（D1）

```bash
python "$SKILL_DIR/scripts/main.py" --case <missing-case.json> --out <out-missing>
# STATUS=partial case_id=ppt-6ad93034-missing-001 deck= slides=0     exit 1
```

- `deck.slide_count=0`：**不编造 deck**；`work/deck.pptx` 不存在；
- `evidence.material_warnings` 列出缺失项（`输入缺失：does-not-exist.md（role=material-1）`）；
- `output_contract` 仍按四形态回显（`is_example=false`）。

### T7b case.json 不可读（D1 末列）

```bash
python "$SKILL_DIR/scripts/main.py" --case <不存在的 case.json> --out <out-badcase>
# ERROR case load failed: 找不到 case 文件: …                        exit 2
```

写出最小 `{"case_id":"unknown","status":"failed","error":"…","created_at":"…"}`。

### T7c 数字核验负例（D2）

```bash
python "$SKILL_DIR/scripts/evidence_check.py" --claim "S2-Attn 的 Q3 精度达到 82.4%" \
    --material "$SKILL_DIR/examples/material.md"        # ok=True  missing=[]       exit 0
python "$SKILL_DIR/scripts/evidence_check.py" --claim "某指标为 99.9%（材料中不存在）" \
    --material "$SKILL_DIR/examples/material.md"        # ok=False missing=['99.9%'] exit 1
```

## T8 ★ 公平对照：本机真实测量（本版核心实测）

**测量条件**：同一解释器、同一库版本、两侧同一测量脚本、两个案例
（包内示例 + 一个为对照新写的 8 页留出案例）。**在包外运行测量脚本**：

```bash
cp "$SKILL_DIR/references/measure_gain.py" <tmp>/
python <tmp>/measure_gain.py --skill-dir "$SKILL_DIR" \
    --case "$SKILL_DIR/examples/case.json" --case <holdout>/case.json \
    --work <tmp>/work --out <tmp>/gain-report.json
```

**汇总（进入结论的 5 项）**

| 指标 | B 均值 | S 均值 | Δ |
|-|-|-|-|
| Q1 页级角色覆盖率 | 0.0000 | 1.0000 | **+1.0000** |
| Q3 数字主张可追溯率 | 0.0000 | 1.0000 | **+1.0000** |
| Q4 演讲备注覆盖率 | 0.0000 | 1.0000 | **+1.0000** |
| Q5 证据脚注覆盖率 | 0.0000 | 1.0000 | **+1.0000** |
| Q6 可复核产物齐全度 | 0.1429 | 1.0000 | **+0.8571** |

**逐案例细节**

| 项 | 案例 A（示例，6 页） | 案例 B（留出，8 页） |
|-|-|-|
| 条件 S 状态 / 退出码 | `success` / 0 | **`partial` / 1** |
| 条件 S 数字主张 | 6 条，全部带证据指针 | 8 条，全部带证据指针 |
| 条件 S `unverified_claims` | 0 | 0 |
| 条件 S 正文字号集合 | {15, 17} pt（自适应收缩） | {15, 17} pt |
| 条件 S `uncertainty` 条数 | 0 | **1**（第 6 页主张 91 字，越界 1 字，D4 记录） |
| 条件 S 预览工件 | 7（6 PNG + 1 PDF） | 9（8 PNG + 1 PDF） |
| 条件 S 脚本耗时 | 2.303 s | 2.837 s |
| 条件 B 脚本耗时 | 0.370 s | 0.021 s |
| Q2（**仅报出，不进结论**） | B 1.0 / S 1.0 | B 1.0 / **S 0.875** |

**必须一起读的两条**：① 案例 B 的 S 侧是 `partial`（越界 1 字也照样降级留痕，
没有为了让对照好看而放宽纪律）；② Q2 在 S 侧更低、在 B 侧"意外合规"，
故**不作为对照依据**（理由见 `GAIN-PROTOCOL.md` §3.3）——这条负面结果被原样保留。

**总耗时对比（如实列出，属成本）**：B 合计 0.391 s，S 合计 5.14 s，差 +4.75 s；
相对 Runtime contract 的 900 秒预算占比 <1%。**本包不主张"更快"。**

## T9 对照协议的资格检查（结论成立的前置条件）

| 前置条件 | 本机状态 |
|-|-|
| 两侧同一 `case.json` / `task.md` / 材料 | ✅ 由测量脚本传入同一路径 |
| 两侧同一 `spec.max_slides` / 模板 | ✅ 均从同一 `case.json` 读取 |
| 两侧同一解释器与库版本 | ✅ 同一 `python`（报告记录版本） |
| 两侧同一测量脚本与归一化口径 | ✅ `references/measure_gain.py` |
| 两侧都不使用 `--edit` | ✅ 均为基础命令 |
| 结论可证伪 | ✅ `GAIN-PROTOCOL.md` §5 给出 5 条证伪条件与复核命令 |

## T10 确定性：同输入双跑 —— 内容级一致

| 比对对象 | 结果 |
|-|-|
| `work/deck.pptx` 逐部件 sha256（zip 条目按名排序） | **64/64 一致**，差异 0 |
| `result.json`（剔除时间戳后逐叶比对） | 仅 1 处：`deck.slides[4].figure.image`（各自输出目录路径） |
| `work/plan.json`（同上） | 仅 1 处：`pages[4].figure.image` |

⇒ **逐页 diff 公平**：同一 case、同一 spec、无 `--edit` 时结构确定，
差异只在时间戳与机器路径前缀。

## 验收对照

| 验收项 | 结果 |
|-|-|
| 主命令在包外 cwd 执行且 exit 0 | ✅ `slides=6`、25 产物、checkpoints 4/4 true |
| 契约字段覆盖与 `null` 检查 | ✅ 17/17 顶层、0 缺项、0 个 `null` |
| 契约门与自检 | ✅ `{"valid": true}` exit 0；`all_pass=true` exit 0 |
| 编辑链路与版本归档 | ✅ `deck_v2.pptx` 与 `deck.pptx` 并存，changelog 有记录 |
| 页数变体 / 图表降级 | ✅ 10 页 / `table` 降级，均 exit 0 |
| 负路径三例 | ✅ partial+1 / failed+2 / missing 非空+1 |
| **公平对照可复跑** | ✅ 测量脚本随包；两案例 10 项指标全部由产物算出，报告留档 |
| 对照结论可证伪 | ✅ 5 条证伪条件 + 复核命令 |
| 确定性双跑 | ✅ deck 64/64 一致；result/plan 各仅 1 处机器路径差异 |
| 包体形态 | ✅ 见下节 |

## 包体自检（提交前必跑）

```bash
python <efficiency-3>/validate_pkg.py <本包目录>          # 期望 PASS，0 FAIL
grep -rnE '[A-Za-z]:[\\/]{1,2}' <本包目录>                # 期望只命中字体探测候选路径
```

判读规则：
- **唯一允许的命中**是运行时字体探测候选路径（`scripts/deck_common.py` 的
  `_WIN_FONTS` 与 README §8 的说明）；除此之外不得有任何命中。
- 允许的扩展名只有 `.md/.py/.json/.txt/.csv/.yaml/.yml`；`references/measure_gain.py`
  也是文本 `.py`，符合白名单。
- **二进制产物一律不入包**（`deck.pptx`、预览 PNG/PDF、`changelog.jsonl`）。
- `scripts/__pycache__/` 提交前必须删除；**测量脚本不要在包内运行**。

## 已知限制（本机验证结论）

- 对照是**受控脚本级**对照：条件 B 是题面点名失败形态的确定性代理实现，
  不是平台官方的 Agent 级对照；平台对照由平台生成（`GAIN-PROTOCOL.md` §7）。
- 样本仅 2 例（平台为 3 固定案例 × 3 次重复），本表不能替代那 9 次运行。
- 未测量真实人工返工小时数，只给可记录的代理量（E1/E2/E3）。
- 预览是 PIL/reportlab 渲染，**不是** PowerPoint 导出件；无 CJK 字体只影响预览。
- 换行估算为字符宽度模型，极端长公式/高密度中文场景仍可能需人工微调。
- `figure.image` 与 `sources[].path` 是**本次运行机器**的实际路径；跨机复跑前缀自然不同。
- `case.json` 不可读时只写**最小** failed result（不满足完整契约字段）—— D1 的刻意取舍。
- 每次运行 <10 秒（本机约 2–3 秒），远低于 900 秒预算。
