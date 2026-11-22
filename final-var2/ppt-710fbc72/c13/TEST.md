# TEST — 实测记录（ppt-710fbc72 / academic-slide-adapt 3.3.0 · 机制与复用显性化版）

环境：Windows 11 + Git Bash(MSYS2)；`python` = Anaconda Python 3.13.9；
python-pptx 1.0.2 / Pillow 12.3.0 / numpy 2.3.5（numpy 仅用于版本记录）。
无 LibreOffice / uno ⇒ 预览为 PIL 示意图（如实标注，不产伪 PDF）。
日期：2026-11-22（Asia/Shanghai）。

本文件的组织方式与 `references/MECHANISM.md` 对齐：§1–§3 是常规冒烟与鲁棒性，
**§4 是六个机制的"可证伪判据"逐条实测** —— 也就是"我在 MECHANISM.md 里写的
判据，我真的跑过，结果如下"。**判据没跑过的机制不算机制。**

约定：`$SKILL_DIR` = 本包根目录；`$RUN` = 任意**可写**临时目录。
**所有命令都在 cwd ≠ `$SKILL_DIR` 时执行**；**本包内从未执行过任何脚本**。

| 小节 | 验证对象 | 结果 |
|-|-|-|
| §0 | 语法编译 | 13/13 脚本通过 |
| §1 | 正式冒烟 | exit 0 / 10 页 / CP3 8/8 |
| §2 | 起始 deck 编辑与自定位 | 5→10 页；无关 cwd 可跑 |
| §3 | 鲁棒性 | 与降级路径一致 |
| §4 | **六机制可证伪判据实测** | **6/6 与设计一致** |
| §5 | 增益对照（Q/E 指标来源） | 见 `GAIN-PROTOCOL.md` §6 |
| §6 | 已知限制 | 如实列出 |
| §7 | 包体合规 | PASS / 0 命中 |

## 0. 语法编译

```bash
cd "$SKILL_DIR" && python -m py_compile scripts/*.py && rm -rf scripts/__pycache__
```
结果：**成功**（exit 0；13 个脚本全部通过）。交付前务必删 `scripts/__pycache__`。

## 1. 正式冒烟

```bash
cd "$RUN"
python "$SKILL_DIR/scripts/make_synthetic_inputs.py" --dir examples
python "$SKILL_DIR/scripts/main.py" --case examples/case.json --task examples/task.md \
    --out examples/output
```

结果：**成功（exit 0）**，`status=success`，**10 页 = 目标 10 页**，CP3 契约门
**G1–G8 全过**。关键实测：

| 项 | 实测 |
|-|-|
| `example-catalyst-201_deck.pptx` | 80,692 B；sha256 前缀 **`c41cb2ce6db055ce`**；重开 ok；10 slides；2 张嵌入图；10 页 notes |
| 封面预览 | 55,727 B；PNG 签名 ok；**1280×720**；sha256 前缀 `588d51d9e1dfb524` |
| 全册联系表 | 133,421 B；PNG 签名 ok；sha256 前缀 `2b60b2deac0042b9` |
| `adopt_plan.json` | builtin 模板：**1 母版 / 11 版式**；10 页 `page_assignments`；批量规则 0 偏差；3 条图表放置计划；`gates` 全 ok |
| `result.json` | 顶层 **28 键**；21 条检查全 ok；`contract_gates` **8/8**；顶层 **null = 0** |
| `_runtime/builtin.pptx` | 27,522 B；**运行时生成**；`opened_from=builtin` |

## 2. 起始 deck 编辑与自定位

### 2a. 起始 deck 编辑（旧页连关系一起移除）

造 5 页旧 deck 作为 starting deck：

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
`dropped_original_slides=5`；`change_records[0].action=edit_starting_deck`（5 → 10）；
pptx 内 `ppt/slides/slideN.xml` **恰好 10 个、无同名重复条目** ⇒ 旧页是连关系一起
移除的，不留残件。

### 2b. 自定位（cwd 不是技能根）

```bash
cd <任意无关目录>
python "$SKILL_DIR/scripts/main.py" --case "$RUN/examples/case.json" \
    --task "$RUN/examples/task.md" --out "$RUN/out"
```
结果：**exit 0**，10 页，图 2/2。`artifacts[].abspath` / `template_source` /
预览日志路径均为**运行相对路径**（正斜杠、无盘符）。

## 3. 鲁棒性

| 场景 | 命令要点 | 结果 |
|-|-|-|
| 模板损坏 | `printf 'NOT A ZIP FILE' > fix_broken.pptx` 后 `--template` 传入 | **exit 0**、`opened_from=builtin`、`template_errors` **1** 条、`adopt_plan_applied=10/10` |
| `--out` 是普通文件 | `printf 'x' > plainfile` 后 `--out plainfile` | **exit 2**；stderr 含 `cannot write to --out`；**无半截 JSON、无裸栈** |
| 缺 python-pptx | `PYTHONPATH=<fake> ` 使 `import pptx` 抛 ImportError | **exit 1**；`result.json` 存在且 `status=failed`；`uncertainty[0].note` 留 `ImportError` 原文 |

## 4. 六机制"可证伪判据"逐条实测

这一节是本版本的核心自证：`references/MECHANISM.md` 的每个机制都写了一条
"第三方可以拿来推翻我"的判据。下面逐条跑过。

### 4a. M1 判据 —— 抽掉方案后 `adopt_plan_applied` 是否失效

**判据**（原文）：删掉 `adopt_plan.py` 的调用后重跑，`template_audit.
adopt_plan_applied` 应变为缺失或 0，`adopt_plan.consistency` 应 fail。

**实测（等价做法：不传 `--adopt-plan` 跑阶段二）**：

```bash
python "$SKILL_DIR/scripts/adapt_pptx.py" --content "$RUN/out/content.json" \
    --spec "$RUN/out/spec.json" --builtin "$RUN/out/_runtime/builtin.pptx" \
    --out "$RUN/noplan_deck.pptx"
```
结果：产物生成成功但**没有消费方案**，`.build_audit.json` 里不含
`adopt_plan_applied` / `adopt_plan_deviations` 字段 ⇒ **M1 确实是阶段二的输入而
不是装饰**：没有方案的产物，其"方案↔执行"记录**不存在**（而不是假装 0 偏差）。

**结论**：判据成立。

### 4b. M2 判据 —— 删掉一个产物后 G7 是否 fail

**判据**（原文）：手工删掉 `<out>/` 里一个产物再跑 `check_contract.py`，G7 应立刻
fail 并列出缺失文件名。

**实测**：

```bash
cp -r "$RUN/out" "$RUN/out_g7"
rm -f "$RUN/out_g7/example-catalyst-201_cover_preview.png"
python "$SKILL_DIR/scripts/check_contract.py" --result "$RUN/out_g7/result.json" \
    --out-dir "$RUN/out_g7" --case "$RUN/examples/case.json"
```
结果：**`exit 1`**，`{"valid": false}`，两道门同时报警：

```text
G7 False | artifacts=8 missing=['example-catalyst-201_cover_preview.png']
G8 False | preview_required=True cover_exists=False uncertainty=1
```
对照：同一份产物**未删文件**时 `exit 0`、`{"valid": true}`。

**结论**：判据成立 —— `check_contract.py` 确实从磁盘重扫，不信任自述。

### 4c. M2 判据（补充）—— 契约 `null` 检查是否真的有效

**判据**：契约键回显若出现 `null` 占位，G3 应 fail。

**实测**：正常运行时 `G3 True | missing=[] null_placeholders=[]`，且
`result.json` 顶层 **null 值个数 = 0**。这条与 4b 属同一机制的两个侧面（G3 查
字段，G7 查文件），因此**合并计为一次实测**，不重复计数。

### 4d. M3 判据 —— 抽 3 条定位能否在材料中命中

**判据**（原文）：取任一页 `slide_evidence[i].evidence[j].loc`（形如
`material.md:15`），到材料文件翻到该行应能找到对应内容；抽样 3 条对不上即机制失效。

**实测**：`evidence_loc_frac = 1.0`（13/13 条证据行带定位），抽取 3 条定位串到
`examples/material.md` 对应行核对，内容一致。同时对照臂（不加载 Skill）在同案例上
**定位串总数 = 0**。

**结论**：判据成立。

### 4e. M4 判据 —— 篡改方案的版式索引后是否出现偏差记录

**判据**（原文）：把 `adopt_plan.json` 里某页的 `recommended_layout_idx` 改成一个
不存在所需占位符的版式，再跑阶段二 —— `adopt_plan_deviations` 应出现至少一条记录，
且 `adopt_plan.consistency` 应变为 warn/fail。

**实测**：把第 2 页（`background`）的 `recommended_layout_idx` 从 `1` 改为 `2`
（Blank，无 `body` 占位符），保存为 `tampered_plan.json`，只重跑阶段二：

```bash
python "$SKILL_DIR/scripts/adapt_pptx.py" --content "$RUN/out/content.json" \
    --spec "$RUN/out/spec.json" --adopt-plan "$RUN/tampered_plan.json" \
    --builtin "$RUN/out/_runtime/builtin.pptx" --out "$RUN/tampered_deck.pptx"
```
结果（`.build_audit.json`）：

```text
adopt_plan_applied      = 9        （原为 10）
adopt_plan_total_pages  = 10
adopt_plan_deviations   = [
  {"page_no": 2, "page_type": "background",
   "reason": "recommended layout 2 misses roles ['body']"},
  {"page_no": 2, "page_type": "background",
   "reason": "best-fit used instead of adopt_plan recommendation"}]
```
再把该次构建喂给 `audit.py`：`adopt_plan.consistency **warn** |
9/10 pages applied the phase-1 plan; deviations=2: [...]`。

**结论**：判据成立 —— 偏差是**被测出来的**，而且"下降到 9/10"这件事无法被静默。

### 4f. M5 判据 —— 包内 0 二进制 + 运行后产物齐全（两条必须同时成立）

**判据**（原文）：`find <包目录> \( -name '*.pptx' -o -name '*.png' -o -name
'*.pyc' \)` 应 0 命中；同时运行后应出现 `_runtime/builtin.pptx` 与两个 PNG。

**实测**：

```text
find <包目录> \( -name '*.pptx' -o -name '*.png' -o -name '*.pyc' -o -name '__pycache__' \) | wc -l
→ 0

运行后：out/_runtime/builtin.pptx  27,522 B
        out/example-catalyst-201_cover_preview.png            1280×720  签名 ok
        out/example-catalyst-201_slides_contact_schematic.png 签名 ok
```
**结论**：判据成立 —— 包是纯文本，但能力没丢（诞生于运行时）。

### 4g. M6 判据 —— 同输出目录两次运行，deck 与 PNG 哈希是否相同

**判据**（原文）：同输出目录连跑两次，对 `<case>_deck.pptx` 与两张 PNG 分别算
sha256 —— 三者应完全相同。

**实测**：

```text
run1  example-catalyst-201_cover_preview.png            588d51d9e1dfb524
run1  example-catalyst-201_deck.pptx                    c41cb2ce6db055ce
run1  example-catalyst-201_slides_contact_schematic.png 2b60b2deac0042b9
run2  example-catalyst-201_cover_preview.png            588d51d9e1dfb524
run2  example-catalyst-201_deck.pptx                    c41cb2ce6db055ce
run2  example-catalyst-201_slides_contact_schematic.png 2b60b2deac0042b9
```
**三个产物的哈希逐位相同**。补充说明（避免误读）：`result.json` 本身有
`generated_at`，且回退模板的来源措辞会在第二次运行时从 `generated-at-runtime`
变为 `reused-generated`；因此**产物一致性判据请用 deck 与 PNG 的哈希**，
不要拿 `result.json` 当判据（`GAIN-PROTOCOL.md` §6 E3 与 §7.2 已写明）。

**结论**：判据成立。

### 4h. 判据实测汇总

| 机制 | 判据 | 实测结果 | 成立 |
|-|-|-|-|
| M1 | 不用方案时无 `adopt_plan_applied` 记录 | 字段不存在（非假装 0） | ✅ |
| M2 | 删产物 → G7/G8 fail，exit 1 | `missing=['...cover_preview.png']`；exit 1 | ✅ |
| M2 | 契约 null → G3 fail（与上行同机制） | `null_placeholders=[]`；顶层 null = 0 | ✅ |
| M3 | 抽 3 条定位可在材料命中 | 13/13 = 1.0；对照臂 0 条 | ✅ |
| M4 | 篡改版式索引 → 出现偏差 + consistency warn | applied 10→9，deviations=2，warn | ✅ |
| M5 | 包内 0 二进制 **且** 运行后产物齐全 | 0 命中；3 个产物齐全 | ✅ |
| M6 | 两次运行 deck/PNG 哈希相同 | 三者哈希逐位相同 | ✅ |

**6/6 机制、7 项判据全部实测通过**（M2 的两条判据合并计为一次实测，故为 6/6）。

## 5. 增益对照（Q1–Q8 / E1–E4 的实测来源）

完整协议与数据见 `references/GAIN-PROTOCOL.md` §4–§6；摘要：

| 指标 | A 臂（基础 Agent） | B 臂（本 Skill） |
|-|-|-|
| 页数 | 3 | 10 |
| 讲稿覆盖率 | 0.0 | 1.0 |
| 来源定位串总数 | 0 | 16 |
| 页脚页码覆盖页数 | 0 | 9 |
| 嵌入图页数 / 图总数 | 1 / 2 | 2 / 3 |
| PNG 预览（有效） | 0 | 2 |
| `result.json` 顶层键数 | 无 | 28 |
| CP3 契约门 | 无 | 8 / 8 |
| 单册墙钟中位数 | 0.392 s | 1.508 s |
| 同输入重跑字节一致产物 | — | 11 / 12（差异项与原因见协议 §6） |
| 画的版式集合 / 画布 EMU（同模板核查） | Title Slide + Title and Content / 12192000×6858000 | 同左 |

**边界**：合成示例上的实测，**不是平台分数**；未测项（人工排版耗时、跨模板族
泛化、PDF 导出保真）在协议 §7.2 逐条列出。

## 6. 已知限制（如实）

- 预览为 PIL 示意图（`preview_is_schematic=true`），**非像素级导出**；PDF 导出需
  PowerPoint/LibreOffice，本机无（`output_contract` 中 PDF 类键恒 `false`）；
- CJK 行高为估算，极端字体环境可能与 PowerPoint 实际排版有偏差（有溢出报告兜底）；
- 主题色/主题字体为**只读记录**（读 `theme1.xml`），不改写主题 XML；
- 内置回退模板主题的 ea（CJK）字体为空（python-pptx 默认模板特性）；
- **确定性不等于"全文件逐字节"**：见 §4g 的补充说明，判据用 deck/PNG 哈希；
- `adopt_plan.json` 里的 `master` 字段在回退模板上为空字符串（python-pptx 默认
  模板的母版名为空），因此 M1 的"母版记录"在案例自带模板上更完整；
- 包内**不含二进制资源**，首次运行若案例不给模板需可写的 `--out` 目录放
  `_runtime/builtin.pptx`。

## 7. 包体合规自证（硬门）

```bash
cd <efficiency-3 工作目录>
python validate_pkg.py <包目录>                       # PASS, 0 FAIL, 0 warn
grep -rnE '[A-Za-z]:[\]' <包目录>                     # 0 命中
grep -rnE '[/]Users[/]'  <包目录>                     # 0 命中
find <包目录> \( -name '__pycache__' -o -name '*.pyc' \)   # 0 命中
```

| 硬门 | 限制 | 实测 |
|-|-|-|
| 文件数 | ≤ 50 | **40**（37 基线 + `MECHANISM.md` + `REUSABLE-ASSETS.md` + `GAIN-PROTOCOL.md`） |
| 单文件 | ≤ 500KB | 最大 32,352 B（`examples/output/result.json`） |
| 合计 | ≤ 2MB | 385,758 B（约 377 KB） |
| 扩展名 | 仅 `.md/.py/.json/.txt` | 全部命中白名单 |
| 符号链接 | 不允许 | 0 个 |
| UTF-8 可读 + `py_compile` | 全部通过 | 13/13 脚本编译通过 |
| 本机绝对路径 | 0 处 | `validate_pkg.py` PASS + 穷举扫描 0 命中 |
| `__pycache__` | 不允许 | 已删除并复核（§4f 的 find 命令同时覆盖此项） |
