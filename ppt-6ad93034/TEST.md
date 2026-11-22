# TEST.md — 本地实测记录与验收判据

> 本文件记录本包在**本机的真实执行结果**（命令、退出码、产物、关键数值），供独立复核。
> 全部命令都写成 `$SKILL_DIR/…` 形式，**在包外目录执行**（cwd 不是技能根目录），
> 输出一律写临时目录，不污染技能包。
>
> 测试机：Windows 11 / Python 3.13.9；库实测版本：python-pptx 1.0.2 ·
> matplotlib 3.10.6 · Pillow 12.3.0 · reportlab 5.0.0 · numpy 可用；
> 无 LibreOffice —— 预览一律 PIL/reportlab 近似渲染并如实标注（`previews.method`）。

## T1 编译与导入检查 —— 通过

```bash
python -m py_compile "$SKILL_DIR"/scripts/*.py     # 10/10 通过，exit 0
python -c "import sys; sys.path.insert(0,'$SKILL_DIR/scripts'); import deck_common, evidence_check, deck_extract, slide_text, deck_tool, render_qa, result_tool, selftest, make_examples, main; print('imports OK')"
# imports OK
```

## T2 冒烟：示例案例端到端（**验收主命令**）—— 通过（exit 0）

**在包外目录执行**（证明 SKILL.md 的命令不依赖 cwd = 技能根目录）：

```bash
SKILL_DIR="<技能包绝对路径>"
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <临时输出目录>
```

运行日志末行：

```
STATUS=success case_id=ppt-6ad93034-example-001 deck=work/deck.pptx slides=6
```

退出码 **0**；`run_meta.checkpoints` 四门全 true：
`{cp1_extract: true, cp2_plan: true, cp3_build: true, cp4_verify: true}`。

**产出文件（真实存在，25 个）**：
`result.json`、`evidence_map.md`、`evidence_map.json`、`manifest.json`（25 项 sha256）、
`changelog.jsonl`、`logs/run_*.log`、
`work/deck.pptx`、`work/plan.json`、`work/material_view.json`、
`work/chart_results.csv.png`、`work/table_cache/results.csv`、
`work/preview/slide_01..06.png`、`work/preview/preview.pdf`、
`preview/slide_01..06.png`、`preview/preview.pdf`。

内容核验（python-pptx 重新打开 + result.json 逐字段）：
- 6 页角色依次 `cover / overview / question / method / result / takeaway`；
- 6/6 页均有演讲备注（【讲解】【证据】【图表】）与证据脚注；
- 结果页（第 5 页）`figure.kind=chart_image`（重绘自 `results.csv`，note 标注重绘来源），
  `table_id=results.csv`，`image=work/chart_results.csv.png`；
- `evidence.unverified_claims` 为空（页面数字全部可在材料中找到）；
- `evidence_map.json` 与 `evidence_map.md` 同源（6 行）；`run_meta.spec_lint` 为
  `{"valid": true, "problems": [], "counts": {"pages": 6, "gaps": 1, "unverified": 0}}`
  —— 唯一的 `gap` 是封面页（封面无主张，属规则允许的无证据页）。

**CP4 契约门与自检（独立复核命令）**：

```bash
python "$SKILL_DIR/scripts/result_tool.py" --result <out>/result.json --out-dir <out> \
    --case "$SKILL_DIR/examples/case.json" --envelope "$SKILL_DIR/templates/result_envelope.json"
# {"valid": true, "errors": [], "warnings": []}      exit 0

python "$SKILL_DIR/scripts/selftest.py" --out <out> --case "$SKILL_DIR/examples/case.json"
# all_pass: true（7/7：pptx_reopen / result_json / contract_keys / unverified_claims /
#           evidence_map_md / evidence_map_json / previews）        exit 0
```

**契约字段覆盖核对（对 `references/OUTPUT_CONTRACT.md` 逐字段）**：

| 核对项 | 结果 |
|-|-|
| `OUTPUT_CONTRACT.md` §1 声明的 17 个顶层字段（case_id … run_meta） | **全部出现在 `result.json` 顶层**，缺项 0 |
| `templates/result_envelope.json` 的 `required_fields` | 缺项 0 |
| `deck` 必备键（editable/format/template/slide_count/slides/notes/receipt） | 缺项 0 |
| `evidence` 必备键（map/unverified_claims/material_warnings） | 缺项 0 |
| `previews` 必备键（pngs/pdf/method/warnings） | 缺项 0 |
| `output_contract` 回显（示例声明 `case_id/deck/evidence/previews/is_example`） | 4 项类型正确回显；`is_example` 为 **bool**（`false`） |
| `result.json` 中值为 `null` 的顶层字段 | **0 个** |

`result.json` 顶层键实测（按写出顺序）：
`case_id, title, status, created_at, skill_version, deck, evidence, previews, sources,
uncertainty, change_records, log, checks, evidence_map_json, manifest, environment,
is_example, run_meta`。

## T3 编辑模式 + 版本归档（演示稿迭代）—— 通过（exit 0）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <out-edit> \
    --edit "$SKILL_DIR/examples/edit_demo.json" --version v2      # exit 0
python "$SKILL_DIR/scripts/result_tool.py" --result <out-edit>/result.json \
    --out-dir <out-edit> --case "$SKILL_DIR/examples/case.json" \
    --envelope "$SKILL_DIR/templates/result_envelope.json"        # exit 0
```

- `work/deck_v2.pptx` 与 `work/deck.pptx` **并存**（版本可回退），`work/plan.json` 同步更新；
- `changelog.jsonl` 记录本次运行的编辑 op（`update_bullet` / `add_note` / `reorder_pages`）；
- 编辑引入的文本同样过数字核验（`update_bullet` 里的 “82.4% 对 81.1%” 可在材料中找到）。

## T4 页数变体（`--max-slides 10`）—— 通过（exit 0）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
    --out <out-10> --max-slides 10
# slides=10
```

角色分配实测：`cover → overview → background → discussion → limitation →
question → method → result → result → takeaway`（富余页先插背景/讨论/局限，再增加
结果页 —— 蓝图规则见 `references/DECK_SPEC.md` §1）。契约门 exit 0。

## T5 图表降级（`--no-chart`）—— 通过（exit 0）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
    --out <out-nc> --no-chart
```

结果页 `figure.kind=table`（降级为 **PPTX 原生可编辑表格**，note 说明重绘被
`--no-chart` 关闭），其余 5 页 `figure.kind=none`；`status` 仍为 `success`
（降级路径被显式记录，属可控降级而非失败）。

## T6 确定性：同输入双跑 —— 内容级一致（如实记录）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <det-A>
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <det-B>
```

| 比对对象 | 结果 |
|-|-|
| `work/deck.pptx` 内部部件（zip 条目按名排序后逐部件 sha256） | **64 个部件全部一致**，差异部件 0 个 |
| `result.json`（剔除时间戳字段后逐叶比对） | **仅 1 处不同**：`deck.slides[4].figure.image`（指向各自输出目录的图表文件） |
| `work/plan.json`（同上） | **仅 1 处不同**：`pages[4].figure.image`（同一原因） |

结论：**内容确定**；原始字节差异只来自 ① zip 条目写入时间戳、②
`figure.image` 的机器路径前缀。同一输出目录连跑两次则 `plan.json` 完全一致、
`result.json` 剔除时间戳后完全一致。

## T7 负路径：材料缺失 / case 不可读 —— 状态与退出码自洽

**T7a 材料文件缺失**（case 指向不存在的材料）:

```bash
python "$SKILL_DIR/scripts/main.py" --case <missing-case.json> --out <out-missing>
# STATUS=partial case_id=ppt-6ad93034-missing-001 deck= slides=0     exit 1
```

- `status=partial`、`deck.slide_count=0`（**不编造 deck**，D1）；
- `evidence.material_warnings` 如实列出：`['输入缺失：no-material.md（role=material-1）',
  'task.md 缺失: task.md']`；
- `output_contract` 仍按四形态回显（`is_example=false`）。

**T7b case.json 本身不可读**:

```bash
python "$SKILL_DIR/scripts/main.py" --case <不存在的 case.json> --out <out-badcase>
# ERROR case load failed: 找不到 case 文件: …                     exit 2
```

写出最小 `{"case_id":"unknown","status":"failed","error":"…","created_at":"…"}`，
**绝不假装成功**。

## T8 单条主张数字核验（`evidence_check.py` CLI）—— 通过

```bash
python "$SKILL_DIR/scripts/evidence_check.py" \
    --claim "S2-Attn 的 Q3 精度达到 82.4%" --material "$SKILL_DIR/examples/material.md"
# ok=True missing=[]            exit 0

python "$SKILL_DIR/scripts/evidence_check.py" \
    --claim "某指标为 99.9%（材料中不存在）" --material "$SKILL_DIR/examples/material.md"
# ok=False missing=['99.9%']    exit 1
```

## T9 对照方案（供评审复跑；**本机未执行，也不由参赛者提供白板/对照结果**）

题面要求"比较不加载 Skill 与加载参赛 Skill 时的实际结果"，并明确
**对照由平台提供/生成**。本包提供的是**可执行的对照协议**，不是自造的白板：

1. 两边使用**同一** `case.json` + `task.md` + 材料 + 模板 + 页数上限。
2. 基础条件：不加载本 Skill，直接要求 Agent 产出同一页数的一版 PPT。
3. 加载条件：按 `SKILL.md` 运行 `scripts/main.py`。
4. 五项**可自动对拍**的指标（前四项不需要人工审美判断）：
   - ① 每页是否有明确叙事角色（`deck.slides[].role`）；
   - ② 每页主张条数/长度是否在纪律内（`plan_lint` 的 `counts`/`problems`）；
   - ③ 页面数字能否指回材料（`evidence.unverified_claims` 是否为空或有解释）；
   - ④ 每页是否有演讲备注与证据脚注（`deck.notes` / `evidence_footer`）；
   - ⑤ 模板约束与预览是否齐备（`previews.pngs/pdf`、字号 `receipt`）。
5. 效率侧可记录的返工量：`changelog.jsonl` 的编辑条数与 `--version` 归档次数
   （本包支持局部编辑，因此"改一页"不需要整稿重跑）。

## 验收对照

| 验收项 | 结果 |
|-|-|
| 验收主命令在**包外 cwd** 执行且 exit 0 | ✅ `STATUS=success … slides=6`，25 个产物，checkpoints 4/4 true |
| `result.json` 顶层字段覆盖 `OUTPUT_CONTRACT.md` §1 全部字段 | ✅ 17/17 在顶层，0 缺项，0 个 `null` |
| 契约门与自检 | ✅ `result_tool` `{"valid": true}` exit 0；`selftest` `all_pass=true` exit 0 |
| 编辑链路与版本归档 | ✅ `work/deck_v2.pptx` 与 `work/deck.pptx` 并存，changelog 有记录，契约门 exit 0 |
| 页数变体 / 图表降级 | ✅ `--max-slides 10` → 10 页；`--no-chart` → 结果页降级 `table`；均 exit 0 |
| 确定性双跑 | ✅ deck 逐部件 64/64 一致；result/plan 各仅 1 处机器路径差异 |
| 负路径（材料缺失 / case 不可读） | ✅ `partial`+exit 1 / `failed`+exit 2，且不编造 deck |
| 文档与脚本命令逐字对应 | ✅ 全部文档命令均为 `"$SKILL_DIR/scripts/…"` 形式，与脚本 `argparse` 定义一致 |
| 包体形态（只含允许的文本扩展名、无二进制、无 `__pycache__`） | ✅ 见 §「包体自检」 |

## 包体自检（提交前必跑）

```bash
# 1) 合规验收器：期望 PASS，0 条 FAIL
python <efficiency-3>/validate_pkg.py <本包目录>

# 2) 本机绝对路径残留检查（任意盘符 + 分隔符）；期望**只**命中字体探测候选
grep -rnE '[A-Za-z]:[\\/]{1,2}' <本包目录>
```

判读规则：
- 唯一的允许命中是**运行时字体探测的候选路径字符串**（`scripts/deck_common.py`
  的 `_WIN_FONTS` 与 README §7 对它的说明）——它属于跨平台探测逻辑，不含任何
  "本机某次运行留下的痕迹"；除此之外**不得有任何命中**。
- 复核时不要用 `find`/`grep` 去拼带反斜杠的字面量模式（Windows 上转义差异大，
  容易自造出假命中）；需要精确复核就用验收器的输出。
- 允许的扩展名只有 `.md/.py/.json/.txt/.csv/.yaml/.yml`；
- **二进制产物一律不入包**：`deck.pptx`、预览 `*.png`、预览 `*.pdf` 由运行时生成
  （清单见 `examples/EXPECTED-OUTPUT.md`）；`changelog.jsonl` 亦不入包；
- `examples/output/` 只放**文本**副本，且由 `scripts/make_examples.py` 自动把
  机器绝对路径净化成包内相对路径；
- `scripts/__pycache__/` 属运行时垃圾，提交前必须删除（否则验收器直接 FAIL）。

## 已知限制（本机验证结论）

- 预览是 PIL/reportlab 渲染，**不是** PowerPoint 导出件；需 Office 级 PDF 时请在
  装有 PowerPoint/LibreOffice 的机器上转换 `work/deck.pptx`。
- 预览绘制使用主机字体（跨平台候选探测）；无 CJK 字体环境只影响预览，不影响 pptx，
  该事实写入 `previews.warnings`。
- 换行估算是字符宽度模型，极端长公式/高密度中文场景可能需要人工微调（见 README §7）。
- `figure.image` 与 `sources[].path` 是**本次运行所在机器**的实际路径；跨机复跑前缀
  自然不同，内容不受影响（包内示例已由 `make_examples.py` 净化）。
- `case.json` 不可读时只写**最小** failed result（含 `case_id/status/error/created_at`），
  不满足完整契约字段——这是 D1 的刻意取舍：输入侧失败时优先"如实说明"而不是"凑字段"。
- 每次运行 <10 秒（本机实测约 2–3 秒），远低于 Runtime contract 的 900 秒预算。
