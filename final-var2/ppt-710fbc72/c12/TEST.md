# TEST — 实测记录（ppt-710fbc72 / academic-slide-adapt 3.2.0 · 增益可验证版）

环境：Windows 11 + Git Bash(MSYS2)；`python` = Anaconda Python 3.13.9；
python-pptx 1.0.2 / Pillow 12.3.0 / numpy 2.3.5（numpy 仅用于版本记录）。
无 LibreOffice / uno ⇒ 预览为 PIL 示意图（如实标注，不产伪 PDF）。
日期：2026-11-22（Asia/Shanghai）。

本文件的组织方式与 `SKILL.md` §2 的**增益指标映射**对齐：§1–§6 是常规冒烟与
鲁棒性，**§7 是对照实验的复跑结果**（也就是 `references/GAIN-PROTOCOL.md` §6 的
数字是怎么来的）。**每条实测都标注它对应哪条指标（Qn/En）或决策规则（D#）**，
这样"哪条指标有实测支撑"一眼可分。

约定：`$SKILL_DIR` = 本包根目录（平台装到 `/skills/weekly-skill`）；
`$RUN` = 任意**可写**临时目录。**所有命令都在 cwd ≠ `$SKILL_DIR` 时执行**；
**本包内从未执行过任何脚本**（避免生成 `__pycache__` 触发合规 FAIL）。

| 小节 | 验证对象 | 结果 |
|-|-|-|
| §0 | 语法编译 | 13/13 脚本通过 |
| §1 | 正式冒烟 | exit 0 / 10 页 / CP3 8/8 |
| §2 | 确定性（E3） | 11/12 产物逐字节相同 |
| §3 | 自定位 | exit 0（无关 cwd） |
| §4 | 鲁棒性 D6 / D16 | 与规则一致 |
| §5 | 起始 deck 编辑 | 5→10 页、无残留页 |
| §6 | 契约回显（Q8/D13） | 真值 + null=0 |
| §7 | **公平对照（Q1–Q8 / E1–E4）** | 见协议 §6 |
| §8 | 已知限制 | 如实列出 |

## 0. 语法编译

```bash
cd "$SKILL_DIR" && python -m py_compile scripts/*.py && rm -rf scripts/__pycache__
```
结果：**成功**（exit 0；13 个脚本全部通过）。交付前务必删 `scripts/__pycache__`。

## 1. 正式冒烟（Q1/Q2/Q3/Q4/Q5/Q6/Q7/Q8 全链路）

```bash
cd "$RUN"
python "$SKILL_DIR/scripts/make_synthetic_inputs.py" --dir examples
python "$SKILL_DIR/scripts/main.py" --case examples/case.json --task examples/task.md \
    --out examples/output
```

结果：**成功（exit 0）**，`status=success`，**10 页 = 目标 10 页**，CP3 契约门
**G1–G8 全过**。

| 指标 | 实测值 | 备注 |
|-|-|-|
| Q1 页数达成度 | 10 / 10 = **1.0** | |
| Q2 讲稿覆盖率 | **1.0**（10/10 页有非空 notes） | |
| Q3 证据定位覆盖率 | **13/13 = 100%**；定位串形态 `material.md:15` | `traceability.evidence_loc_frac` |
| Q4 页脚/页码 | 自第 2 页起统一（封面无页脚，口径 `(N-1)/N`） | `layout.footer_uniform=ok` |
| Q5 图表放置 | 图 **2/2** 上图；`figure_adjust` 无拉伸 | aspect 1.4286 == 源图 |
| Q6 模板继承记录 | `layout_used` **10** 条（builtin：1 母版 / 11 版式） | 含主题字体 Calibri + 12 主题色 |
| Q7 方案↔执行一致性 | `adopt_plan_applied` **10/10**，偏差 **0** | `adopt_plan.consistency=ok` |
| Q8 契约 | G1–G8 **8/8**；顶层 **null = 0**；21 条检查全 ok | |

产物实测：`example-catalyst-201_deck.pptx` 80,692 B / sha256 前缀
`c41cb2ce6db055ce` / 重开 ok / 10 slides / 2 张嵌入图 / 10 页 notes；
封面预览 55,727 B（1280×720）、联系表 133,421 B（10 页），PNG 签名均有效；
`_runtime/builtin.pptx` 27,522 B（**运行时现场生成**，来源记入
`template_audit.template_source` 与 `uncertainty`）。

## 2. 确定性（E3）

同输出目录连跑两次后逐文件 sha256 对拍：

```text
12 个文件中 11 个逐字节相同（11 / 12）
唯一差异文件：result.json
差异 top-level 键：generated_at、uncertainty
deck sha256：两次均 c41cb2ce6db055ce
```

**差异根因（写入协议 §6 E3 那一行）**：`uncertainty[0].note` 写的是回退模板的
**实际来源** —— 首次 `generated-at-runtime`、第二次 `reused-generated`。这是运行
事实，抹平它反而让"这份模板是否现场生成"变得不可查。

## 3. 自定位（cwd 不是技能根）

```bash
cd <任意无关目录>
python "$SKILL_DIR/scripts/main.py" --case "$RUN/examples/case.json" \
    --task "$RUN/examples/task.md" --out "$RUN/out"
```
结果：**exit 0**，10 页，图 2/2。`artifacts[].abspath` / `template_source` /
预览日志路径均为**运行相对路径**（正斜杠，无盘符）；材料与图表路径按调用方给的
形式记录（传相对即相对、传绝对即绝对）。

## 4. 鲁棒性（D6 / D16）

### 4a. 模板损坏 → 回退（D6）

```bash
printf 'NOT A ZIP FILE' > "$RUN/fix_broken.pptx"
python "$SKILL_DIR/scripts/main.py" --case "$RUN/examples/case.json" \
    --task "$RUN/examples/task.md" --template "$RUN/fix_broken.pptx" --out "$RUN/r1"
```
结果：**exit 0**、`opened_from=builtin`、`template_errors` **1** 条、
`adopt_plan_applied=10/10`。⇒ 坏模板不让整册失败，而是记错误后走回退链。

### 4b. `--out` 指向普通文件（D16）

```bash
printf 'x' > "$RUN/plainfile"
python "$SKILL_DIR/scripts/main.py" --case "$RUN/examples/case.json" --out "$RUN/plainfile"
```
结果：**exit 2**；stderr 两行说明（含 `cannot write to --out`）；**无半截 JSON、
无裸栈**。退出码 2 与"流水线失败"的 1 刻意区分。

### 4c. 依赖缺失（python-pptx）

```bash
mkdir -p "$RUN/fake/pptx"
printf 'raise ImportError("simulated: python-pptx not installed")\n' > "$RUN/fake/pptx/__init__.py"
PYTHONPATH="$RUN/fake" python "$SKILL_DIR/scripts/main.py" --case "$RUN/examples/case.json" \
    --task "$RUN/examples/task.md" --out "$RUN/r4"
```
结果：**exit 1**；`$RUN/r4/result.json` 存在且 `status=failed`，
`uncertainty[0].note` 留 `ImportError: simulated: python-pptx not installed`。
⇒ 依赖缺失**仍写出 result.json**，把原因留在盘上。

## 5. 起始 deck 编辑（5 页旧 deck → 计划 10 页）

```bash
python - <<'PY'
from pptx import Presentation
from pptx.util import Inches
import os
prs = Presentation(); prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
for i in range(5):
    s = prs.slides.add_slide(prs.slide_layouts[0]); s.shapes.title.text = f"旧页 {i+1}"
os.makedirs("<RUN>/fix", exist_ok=True); prs.save("<RUN>/fix/start_deck.pptx")
PY
python "$SKILL_DIR/scripts/main.py" --case "$RUN/examples/case.json" \
    --task "$RUN/examples/task.md" --starting-deck "$RUN/fix/start_deck.pptx" --out "$RUN/r5"
```
结果：**exit 0**；`opened_from=starting_deck`、`slide_count=10`、
`dropped_original_slides=5`；`change_records[0]` =
`{"action":"edit_starting_deck","before":{"slides":5},"after":{"slides":10},...}`；
pptx 内 `ppt/slides/slideN.xml` **恰好 10 个、无同名重复条目** ⇒ 旧页连关系一起
移除，不留残件。

## 6. 契约回显取真实值（Q8 / D13）

```bash
python "$SKILL_DIR/scripts/validate_result.py" --case "$RUN/examples/case.json" \
    --result "$RUN/examples/output/result.json"
python "$SKILL_DIR/scripts/check_contract.py" --result "$RUN/examples/output/result.json" \
    --out-dir "$RUN/examples/output" --case "$RUN/examples/case.json"
```
结果：两项均 **exit 0**；前者 `VALID - result.json conforms to OUTPUT_CONTRACT`，
后者 `{"valid": true}`，G1–G8 逐门 `ok`（G7 `artifacts=8 missing=[]`）。

| 契约键 | 实测值 |
|-|-|
| `template_inheritance` | `True` |
| `slide_count` | `10` |
| `audience` | `"催化方向课题组组会"` |
| `language` | `"zh"` |
| `evidence_per_slide` | `True` |
| `notes_per_slide` | `True` |
| `preview_png` | `True` |
| **顶层 null 值个数** | **0** |

`verification.contract_echo_derived` =
`{"template_inheritance": true, "evidence_per_slide": true,
"notes_per_slide": true, "preview_png": true}`。

## 7. 公平对照实验（Q1–Q8 / E1–E4 的实测来源）

协议见 `references/GAIN-PROTOCOL.md` §2–§5；下面是本次实际执行步骤与结果摘要。

### 7.1 准备（C1/C2 落实）

```bash
RUN=<可写目录>; mkdir -p "$RUN"; cd "$RUN"
cp -r "$SKILL_DIR/examples" "$RUN/input"
python "$SKILL_DIR/scripts/make_synthetic_inputs.py" --dir "$RUN/input"   # 两臂共用同一批图
mkdir -p "$RUN/input/tpl"
python "$SKILL_DIR/scripts/make_template.py" --out "$RUN/input/tpl/template.pptx"
# 令 case.json 的 template = "tpl/template.pptx" —— 两臂都从这一字段解析
```

### 7.2 运行两臂（各 3 次，`time.perf_counter()` 包住子进程）

| 臂 | 命令 | 3 次耗时（s） | 中位数 |
|-|-|-|-|
| A（基础 Agent） | `plain_baseline_arm.py --case input/case.json --out armA/out/deck.pptx` | 0.392 / 0.375 / 0.470 | **0.392** |
| B（本 Skill） | `main.py --case input/case.json --task input/task.md --out armB/out` | 1.508 / 1.512 / 1.384 | **1.508** |

两臂均 **rc=0**。B 臂 `template_audit`：`opened_from=case_template`、
`template_fallback_used=false`、`layouts=11` ⇒ **C2「同模板」已落实**。

### 7.3 同一套规则测量两臂

| 指标 | A 臂 | B 臂 |
|-|-|-|
| 页数 | 3 | 10 |
| out 目录文件数 | 1 | 12 |
| Q2 讲稿覆盖率 | 0.0 | 1.0 |
| Q3 定位页数 / 定位串总数 | 0 / 0 | 3 / 16 |
| Q4 页脚页码覆盖页数 | 0 | 9 |
| Q5 嵌入图页数 / 图总数 | 1 / 2 | 2 / 3 |
| Q5 嵌入图宽高比（源图 1.4286） | 1.4286 | 1.4286 |
| 原生表格页数 | 0 | 1 |
| PNG 预览（签名有效） | 0 | 2（1280×720 / 2000×1580） |
| Q8 `result.json` 顶层键数 / null 数 | 无 result.json | 28 / 0 |
| 页级证据条目 / 证据行 | 无 | 10 / 13 |
| Q6 `layout_used` 条数 | 无 | 10 |
| Q7 方案套用页数 / 偏差条数 | 无 | 10 / 0 |
| 自查检查条数（fail/warn） | 无 | 21（0/0） |
| Q8 CP3 门通过数 | 无 | 8 / 8 |
| deck 字节 / sha256 前缀 | 53,039 B / `0ed822f04e873076` | 80,692 B / `c41cb2ce6db055ce` |
| **画的版式集合**（C2） | Title Slide + Title and Content | 同左 |
| **画布 EMU**（C2） | 12192000×6858000 | 同左 |

### 7.4 E3 复跑对拍与 E4 计数

```text
E3：11 / 12 个产物逐字节相同；差异仅 result.json 的 generated_at 与 uncertainty[0].note
E4：需人工复查记录 = 13 条证据行 + 21 条审计检查 = 34（A 臂为 0）
```

### 7.5 本次对照的边界

- 案例是**合成**示例（`example-catalyst-201`，虚指数值），**不是平台正式案例**；
- A 臂是作者按"基础 Agent 最自然做法"实现的**代理臂**，不是平台真实基础 Agent
  的运行记录；
- 未测：人工排版耗时、跨模板族泛化、PDF 导出保真（无 LibreOffice，只能测
  "有/无有效预览"）；
- E1 的绝对值依赖机器，跨机只看两臂比值（本次约 3.8×）。

## 8. 已知限制（如实）

- 预览为 PIL 示意图（`preview_is_schematic=true`），**非像素级导出**；PDF 导出需
  PowerPoint/LibreOffice，本机无，故未产 PDF（`output_contract` 中 PDF 类键恒 `false`）；
- CJK 行高为估算，极端字体环境可能与 PowerPoint 实际排版有偏差（有溢出报告 D9 兜底）；
- 主题色/主题字体为**只读记录**（读 `theme1.xml`），不改写主题 XML；
- 内置回退模板主题的 ea（CJK）字体为空（python-pptx 默认模板特性）；
- 路径记录策略：`artifacts.abspath` / `template_source` / 预览日志恒为运行相对
  路径；材料与图表路径按调用方给的形式记录 —— 跨目录比对 JSON 时字样不同，那是
  记录差异不是产物差异；
- **确定性不是"全文件逐字节"**：见 §2，本次为 11/12，差异项与原因已列；
- 包内**不含二进制资源**，首次运行若案例不给模板需可写的 `--out` 目录放
  `_runtime/builtin.pptx`。

## 9. 包体合规自证（硬门）

```bash
cd <efficiency-3 工作目录>
python validate_pkg.py <包目录>                       # PASS, 0 FAIL, 0 warn
grep -rnE '[A-Za-z]:[\]' <包目录>                     # 0 命中
grep -rnE '[/]Users[/]'  <包目录>                     # 0 命中
find <包目录> \( -name '__pycache__' -o -name '*.pyc' \)   # 0 命中
```

| 硬门 | 限制 | 实测 |
|-|-|-|
| 文件数 | ≤ 50 | **38**（37 基线文件 + `references/GAIN-PROTOCOL.md`） |
| 单文件 | ≤ 500KB | 最大 32,352 B（`examples/output/result.json`） |
| 合计 | ≤ 2MB | 356,005 B（约 348 KB） |
| 扩展名 | 仅 `.md/.py/.json/.txt` | 全部命中白名单 |
| 符号链接 | 不允许 | 0 个 |
| UTF-8 可读 + `py_compile` | 全部通过 | 13/13 脚本编译通过 |
| 本机绝对路径 | 0 处 | `validate_pkg.py` PASS + 穷举扫描 0 命中 |
| `__pycache__` | 不允许 | 已删除并复核 |
