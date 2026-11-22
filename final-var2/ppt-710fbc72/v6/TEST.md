# TEST — 实测记录（ppt-710fbc72 / academic-slide-adapt 4.0.0 · 全维合并版）

> 本包是 union 包（决策规则 ∪ 增益协议 ∪ 机制 ∪ 故障演练 ∪ 题集）。本文件把**全部实测**收在一处：
> §0–§10 是核心流水线的实测（冒烟 / 确定性 / 自定位 / 失败分支 / 起始 deck / CP3 / 对照 / 限制 / 合规），
> **§11 是故障注入演练的实测**（18 场景，明细见 `references/FAULT-MATRIX.md`），
> **§12 是题集泛化的实测**（3 案例，明细见 `references/CASE-SET.md`）。
> 两节的数字与两份 reference 同源；若发生冲突，以本节复跑命令的输出为准。

环境：Windows 11 + Git Bash(MSYS2)；`python` = Anaconda Python 3.13.9；
python-pptx 1.0.2 / Pillow 12.3.0 / numpy 2.3.5（numpy 仅用于版本记录，运行只依赖
python-pptx + Pillow）。无 LibreOffice / uno ⇒ 预览为 PIL 示意图（如实标注，
不产伪 PDF）。日期：2026-11-22（Asia/Shanghai）。

本文件的组织方式与 `SKILL.md` 的决策规则对齐：**每个测试小节标注它验证的是哪
条决策规则（D#）与哪个失败分支（B##）**，这样"哪条规则被实测过、哪条只是设计"
一眼可分。

约定：`$SKILL_DIR` = 本包根目录（平台装到 `/skills/weekly-skill`）；
`$RUN` = 任意**可写**临时目录（示例材料复制到这里，包内保持只读）。
**所有命令都在 cwd ≠ `$SKILL_DIR` 的情况下执行过**，因此命令里的
`"$SKILL_DIR"` 前缀是必需的而非装饰。**本包内从未执行过任何脚本**（避免生成
`__pycache__` 触发合规 FAIL）。

```bash
SKILL_DIR=<本包根目录>; RUN=<临时目录>; mkdir -p "$RUN"
cp -r "$SKILL_DIR/examples" "$RUN/examples"
python "$SKILL_DIR/scripts/make_synthetic_inputs.py" --dir "$RUN/examples"
```

| 小节 | 验证对象 | 结果 |
|-|-|-|
| §0 | 语法编译 | 13/13 脚本通过 |
| §1 | 正式冒烟（D5 回退模板路径） | exit 0 / 10 页 / CP3 8/8 |
| §2 | 确定性（D16 无关，纯重跑） | 11/12 产物逐字节相同 |
| §3 | 自定位（命令在无关 cwd 可跑） | exit 0 |
| §4 | 失败分支实测 B01/B07/B21/B23 | 4/4 与规则一致 |
| §5 | 起始 deck 编辑（D-起始）与契约回显（D13） | 5→10 页、null=0 |
| §6 | CP3 独立复查（G1–G8） | 8/8 + exit 0 |
| §7 | 与基础做法的对照 | 见下（非平台白板） |
| §8 | 已知限制 | 如实列出 |
| **§11** | **故障注入演练（18 场景 / 4 家族）** | **0 个静默失败；退出码 0/1/2 三档实测** |
| **§12** | **题集泛化（3 案例 / 3 难度层）** | **0 个超出声明区间；1 个已声明边界命中** |

## 0. 语法编译检查

```bash
cd "$SKILL_DIR" && python -m py_compile scripts/*.py && rm -rf scripts/__pycache__
```
结果：**成功**（exit 0；13 个脚本 `common / extract / deckplan / adopt_plan /
adapt_pptx / pptx_toolkit / preview / audit / main / validate_result /
check_contract / make_template / make_synthetic_inputs` 全部通过）。
> 交付前务必删掉 `scripts/__pycache__`：`.pyc` 属平台拒绝的资源类型。

## 1. 正式冒烟 · 走 D5（案例未给模板 → 运行时回退模板）两阶段全流程

```bash
cd "$RUN"
python "$SKILL_DIR/scripts/make_synthetic_inputs.py" --dir examples
python "$SKILL_DIR/scripts/main.py" --case examples/case.json --task examples/task.md \
    --out examples/output
```

结果：**成功（exit 0）**，`status=success`，**10 页 = 目标 10 页**，CP3 契约门
**G1–G8 全过**（`check_contract` exit 0）。关键实测值：

| 项 | 实测 |
|-|-|
| pptx | `example-catalyst-201_deck.pptx` 80,692 B；sha256 前缀 `c41cb2ce6db055ce`；python-pptx 重开 ok；10 slides；2 张嵌入图；10 页 speaker notes |
| 封面预览 | 55,727 B；PNG 签名 ok；1280×720；SCHEMATIC 标注 |
| 全册联系表 | 133,421 B；PNG 签名 ok；10 页联系表 |
| `adopt_plan.json` | 阶段一方案：builtin 模板 1 母版 / 11 版式 / 占位符清单 / 主题字体 Calibri + 12 主题色；10 页版式分配；批量规则 **0 偏差**；3 条图表放置计划；`gates` 全 ok |
| `result.json` | `status=success`；**顶层 28 键**；`output_contract` 7 键全部回显且为**真实值**；21 条检查全 `ok`；`contract_gates` **8/8 ok**；**顶层 null 值个数 = 0** |
| `_runtime/builtin.pptx` | 27,522 B；**运行时现场生成**的回退模板（16:9）；来源记入 `template_audit.template_source` 与 `uncertainty` |

审计摘要（`audit.json`，21 条全 `ok`）：`artifact.*.exists`（pptx / 两预览 /
spec / adopt_plan）· `pptx.reopen` 10 slides · `pptx.slide_count` 10==10 ·
`content.claim_coverage` · `xref.figure_refs` · `xref.figure_placement` 2/2 上图 ·
`notes.present` 10/10 · `layout.overflow` 0 · `layout.font_floor` 无 ·
`layout.footer_uniform` ok · `preview.cover_png` / `preview.contact_png` 签名 ok ·
`traceability.evidence_loc` 13/13 = 100% · `adopt_plan.consistency`（10/10 页按
方案套用、0 偏差）· `adopt_plan.gates` ok · `result.contract` ok ·
`result.contract_gates` ok。

> **D5 实测要点**：案例没有模板时，Skill 不是"没有模板就报错"，而是**现场生成
> 真实母版/版式/占位符**再照常审计继承关系；来源在 `template_audit.opened_from`
> 里记成 `builtin`，并进 `uncertainty`（**不冒充案例给的模板**）。

## 2. 确定性复现（同输入 + 同输出目录连跑两次）

```bash
RUN2=<可写目录>; mkdir -p "$RUN2"; cp -r "$SKILL_DIR/examples" "$RUN2/examples"
python "$SKILL_DIR/scripts/make_synthetic_inputs.py" --dir "$RUN2/examples"
python "$SKILL_DIR/scripts/main.py" --case "$RUN2/examples/case.json" \
    --task "$RUN2/examples/task.md" --out "$RUN2/out"
cp -r "$RUN2/out" "$RUN2/snap1"
python "$SKILL_DIR/scripts/main.py" --case "$RUN2/examples/case.json" \
    --task "$RUN2/examples/task.md" --out "$RUN2/out"
# 逐文件 sha256 对拍 snap1/ vs out/
```

结果：

```text
12 个文件中 11 个逐字节相同（byte-identical 11 / 12）
唯一差异文件：result.json
其差异 top-level 键：generated_at、uncertainty
deck sha256：两次均 c41cb2ce6db055ce
```

**差异根因（如实记录）**：`uncertainty[0].note` 里那一句写的是回退模板的**实际
来源**——第一次运行是 `generated-at-runtime`（现场生成），第二次是
`reused-generated`（复用已生成的那份）。**这是运行事实的如实记录，不是随机性**
；把它抹平反而会让"这份模板到底是不是现场生成的"变得不可查。

页计划与适配方案是确定性纯函数；pptx 经 `deterministic_zip()` 固定 zip 条目
时间戳（并折叠同名条目）后同输入同字节；回退模板生成同样是确定性的。
`artifacts.abspath` 记录的是**运行相对路径**，因此换输出目录只改路径字样，不会
把本机盘符带进记录。

## 3. 自定位（cwd 不是技能根目录）

```bash
cd <任意无关目录>
python "$SKILL_DIR/scripts/main.py" --case "$RUN/examples/case.json" \
    --task "$RUN/examples/task.md" --out "$RUN/out"
```

结果：**exit 0**，`status=success`，10 页，图 2/2 上图。路径记录的真实行为
（按 `scripts/common.py` 的 `portable_path()` / `slash()`）：

- `result.json.artifacts[].abspath`、`template_audit.template_source`、
  `verification.render.*.path` 记的是**运行相对路径**（相对当前工作目录、正斜杠）
  —— 本次运行形如 `eff3-ppt710-smoke/selfloc/out/_runtime/builtin.pptx`，
  **不含盘符或用户目录**；
- 材料与图表路径由 `extract._locate()` 解析后记录：**调用方传相对路径 → 记录为
  相对路径**；调用方传绝对路径 → 记录为该解析结果（容器里即 `/app/work/...`）。
  这是真实 I/O 路径，不是包内残留：包内文件本身 **0 处本机路径**（§8 复核）。

分步命令（`references/two-phase-workflow.md` 的形态，同样在无关 cwd 下执行）：

```bash
python "$SKILL_DIR/scripts/make_template.py" --out "$RUN/builtin.pptx"
python "$SKILL_DIR/scripts/extract.py"  --case "$RUN/examples/case.json" \
    --task "$RUN/examples/task.md" --out "$RUN"
python "$SKILL_DIR/scripts/deckplan.py" --content "$RUN/content.json" --out "$RUN"
python "$SKILL_DIR/scripts/adopt_plan.py" --content "$RUN/content.json" \
    --spec "$RUN/spec.json" --builtin "$RUN/builtin.pptx" --out "$RUN/adopt_plan.json"
python "$SKILL_DIR/scripts/adapt_pptx.py" --content "$RUN/content.json" \
    --spec "$RUN/spec.json" --adopt-plan "$RUN/adopt_plan.json" \
    --builtin "$RUN/builtin.pptx" --out "$RUN/example-catalyst-201_deck.pptx"
python "$SKILL_DIR/scripts/preview.py" --content "$RUN/content.json" \
    --spec "$RUN/spec.json" --out "$RUN"
python "$SKILL_DIR/scripts/audit.py" --content "$RUN/content.json" \
    --spec "$RUN/spec.json" --out "$RUN" --adopt-plan "$RUN/adopt_plan.json"
```
结果：全部 **exit 0**（`opened_from=builtin`、`adopt_plan_applied=10`、
`deviations=0`、审计 0 fail / 0 warn）。**`--out` 语义不同**：
`extract/deckplan/preview/audit` 收**目录**，`adopt_plan/adapt_pptx/make_template`
收**文件**（与各脚本 `--help` 一致）。

## 4. 失败分支实测（B01 / B07 / B21 / B23）

这一节是本次版本的重点：**决策规则不能只是文档里的一张表，必须有一条真实运行
与之对应**。

### 4a. B07 — 模板损坏 → 回退（D6）

```bash
printf 'NOT A ZIP FILE' > "$RUN/fix_broken.pptx"
python "$SKILL_DIR/scripts/main.py" --case "$RUN/examples/case.json" \
    --task "$RUN/examples/task.md" --template "$RUN/fix_broken.pptx" --out "$RUN/t1"
```
结果：**exit 0**，`status=success`，`opened_from=builtin`，
`template_errors` **1 条**（原文 `case_template: Package not found at '...'`），
`adopt_plan_applied=10/10`。
> 即：**坏的模板不会让整册失败**，而是记一笔错误后走回退链；错误原文保留在
> `template_audit.template_errors`，能区分"路径不存在"与"文件损坏"。

### 4b. B01 — case.json 缺失 → 立即失败（D1）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$RUN/nope.json" --out "$RUN/t2"
```
结果：**exit 1**；stderr 一行 `main FAILED: [Errno 2] No such file or directory: ...`；
`$RUN/t2/result.json` = `status=failed`，`case_id="nope"`（取文件名词干），
`uncertainty[0].note` 保留 `FileNotFoundError` 原文。
> **不产半成品冒充成功**：目录里只有一份说明失败的 result.json。

### 4c. B23 — `--out` 指向普通文件 → 不可写（D16）

```bash
printf 'x' > "$RUN/plainfile"
python "$SKILL_DIR/scripts/main.py" --case "$RUN/examples/case.json" --out "$RUN/plainfile"
```
结果：**exit 2**；stderr 两行（`main FAILED: FileExistsError...` +
`main FAILED: cannot write to --out 'plainfile': ...`）；**不产生半截 JSON、
不抛裸栈**。
> 退出码 **2** 与"流水线失败"的 1 刻意区分：参数/输出位置错误不需要人去查
> result.json。

### 4d. B21/B22 — 依赖缺失（python-pptx / Pillow）→ 诚实失败（D5/D14）

```bash
mkdir -p "$RUN/fake/pptx" "$RUN/fake/PIL"
printf 'raise ImportError("simulated: python-pptx not installed")\n' > "$RUN/fake/pptx/__init__.py"
printf 'raise ImportError("simulated: Pillow not installed")\n' > "$RUN/fake/PIL/__init__.py"
PYTHONPATH="$RUN/fake" python "$SKILL_DIR/scripts/main.py" --case "$RUN/examples/case.json" \
    --task "$RUN/examples/task.md" --out "$RUN/t4a"
```
结果：**exit 1**；stderr `main FAILED: simulated: python-pptx not installed`；
`$RUN/t4a/result.json` 存在且 `status=failed`，
`uncertainty[0].note = "ImportError: simulated: python-pptx not installed"`。
> 依赖缺失时**仍写出 result.json**（含 ImportError 原文），把"为什么没跑成"
> 留在盘上，而不是只在终端里滚过去。

| 分支 | 期望 | 实测 | 一致 |
|-|-|-|-|
| B01 | exit 1 + failed result | exit 1 + `status=failed` | ✅ |
| B07 | 回退 + 错误记录 | `opened_from=builtin` + 1 条 error | ✅ |
| B21 | exit 1 + ImportError 进 result | exit 1 + `uncertainty` 留原文 | ✅ |
| B23 | exit 2 + 不写半截 JSON | exit 2 + 无 JSON 产出 | ✅ |

## 5. 起始 deck 编辑与契约回显

### 5a. 起始 deck 编辑（旧页连关系一起移除）

先造一份 5 页旧 deck 作为 starting deck，再让 Skill 在其母版上重建计划页数：

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
    --task "$RUN/examples/task.md" --starting-deck "$RUN/fix/start_deck.pptx" --out "$RUN/t5"
```

结果：**exit 0**；`opened_from=starting_deck`、`slide_count=10`、
`dropped_original_slides=5`；`change_records[0]` =
`{"action":"edit_starting_deck","before":{"slides":5},"after":{"slides":10},...}`；
产出的 pptx 里 **`ppt/slides/slideN.xml` 恰好 10 个、无同名重复条目** ⇒
旧页是**连关系一起移除**的，不留残件。

### 5b. 契约回显取真实值（D13/B20）

```bash
python "$SKILL_DIR/scripts/validate_result.py" --case "$RUN/examples/case.json" \
    --result "$RUN/out/result.json"
```

结果：`VALID - result.json conforms to OUTPUT_CONTRACT`，**exit 0**。
`result.json` 顶层实测（不是类型默认值，而是本次运行推出的真值）：

| 键 | 实测值 |
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
"notes_per_slide": true, "preview_png": true}` —— **这四个 true 是从哪来的也
一并留档**，避免"回显了一个 true 但没人知道依据"。

## 6. CP3 独立复查（G1–G8）

```bash
python "$SKILL_DIR/scripts/check_contract.py" --result "$RUN/out/result.json" \
    --out-dir "$RUN/out" --case "$RUN/examples/case.json"
```

结果：**exit 0**，`{"valid": true}`，逐门 `ok`：

| 门 | detail（实测原文节选） |
|-|-|
| G1 | `result.case_id='example-catalyst-201' case.case_id='example-catalyst-201'` |
| G2 | `status='success'` |
| G3 | `missing=[] null_placeholders=[]` |
| G4 | `deck=example-catalyst-201_deck.pptx reopened; 10 slides` |
| G5 | `slide_evidence entries=10` |
| G6 | `opened_from='builtin' layouts=11` |
| G7 | `artifacts=8 missing=[]` |
| G8 | `preview_required=True cover_exists=True uncertainty=1` |

> `check_contract.py` 从磁盘独立重扫（自己重开 pptx、自己扫产物清单），
> **不信任 result.json 的自述**。这是"可核验性"这一项的硬证据。

## 7. 决策规则的验证方法（SOP：新规则怎么才算"测过"）

本包把可靠性押在"每条决策规则都能被指认"上，因此**新增一条规则时必须同时给它一条
测试**，否则规则只是文档。本节的 SOP 是三步：

| 步骤 | 做什么 | 通过标准 |
|-|-|-|
| 1 | 构造触发条件（坏模板 / 缺 case / 只读输出 / 缺依赖 / 缺图 / 超页…） | 能稳定复现该分支，不需要改动包内代码 |
| 2 | 跑 `main.py` 或对应分步命令，记录**退出码**与 `result.json` 的差异 | 退出码与 §2.5 的状态判定一致（0/1/2 三档） |
| 3 | 在 `result.json` 里定位**规则承诺的记录字段**并截图/摘录原文 | 字段真实存在且内容可读（不是空数组、不是 null） |

### 已按本 SOP 验证过的规则（§4 的实测）

| 规则 | 触发条件 | 退出码 | 承诺的记录字段（实测原文节选） |
|-|-|-|-|
| **D1**（B01） | `--case` 指向不存在的文件 | **1** | `status=failed`；`uncertainty[0].note` = `FileNotFoundError: [Errno 2] No such file or directory: '.../nope.json'` |
| **D6**（B07） | `--template` 指向损坏文件（内容为文本） | **0**（回退成功） | `opened_from=builtin`；`template_errors` **1** 条，原文 `case_template: Package not found at '...'` |
| **D16**（B23） | `--out` 指向普通文件 | **2** | stderr `main FAILED: cannot write to --out 'plainfile': FileExistsError...`；**未产出 result.json** |
| **D5/D16**（B21） | `PYTHONPATH` 注入抛 `ImportError` 的假 `pptx` 模块 | **1** | `status=failed`；`uncertainty[0].note` = `ImportError: simulated: python-pptx not installed` |
| 起始 deck 编辑 | `--starting-deck` 传 5 页旧 deck | **0** | `dropped_original_slides=5`；`change_records[0].action=edit_starting_deck`（before 5 → after 10） |
| **D13**（B20） | 正常运行后读契约回显 | **0** | 7 个契约键均为真实值；`contract_echo_derived` 列出派生来源；顶层 null = **0** |

### 尚未单独构造测试的规则（如实列出）

以下规则**已实现且被正常路径覆盖**，但**没有**像上表那样构造专门的触发用例 ——
它们在本次交付中属于"设计已写、专项未测"：

- **D3**（扫描件/无文本层）：示例案例的材料是文本，未准备图像型材料；
- **D9/D10** 的字号地板与标题截断：需要构造超长文本输入才能触发；
- **D11** 的页数裁剪：需要把 `slide_count` 调到小于计划页数；
- **D12** 的源图缺失占位框：需要删掉合成图后再跑；
- **D14/D15** 的字体回退分支：本机探测到了可用字体，未命中回退；
- **D2/D4/D12b** 的部分子分支同理。

**这不是"已测"** —— 如果要让它们也进入上表，需要按同一 SOP 补构造用例；
在此之前，`SKILL.md` §2 对它们的描述应理解为**设计意图**而非实测结论。

## 8. 与基础做法的对照（增益方向，非平台白板）

同一示例案例、同一模板、同一台机器：朴素做法（把各环节正文整段塞进默认版式的
正文占位符、图按原始尺寸直接放、无版式方案 / 无来源定位 / 无页脚页码 / 无讲稿 /
无 result.json）对比本 Skill 输出：

| 维度 | 朴素基线（实测） | 本 Skill（实测） |
|-|-|-|
| 页数 | 3 | 10 |
| out 目录文件数 | 1 | 12 |
| 讲稿覆盖率 | 0.0 | 1.0 |
| 带 `文件:行` 定位的页数 / 定位串总数 | 0 / 0 | 3 / 16 |
| 页脚或页码覆盖页数 | 0 | 9 |
| 嵌入图页数 / 图总数 | 1 / 2 | 2 / 3 |
| 原生表格页数 | 0 | 1 |
| 嵌入图宽高比 | 1.4286（= 源图） | 1.4286（= 源图） |
| PNG 预览（签名有效） | 0 | 2（1280×720 / 2000×1580） |
| result.json 顶层键数 | 无 result.json | 28 |
| 页级证据条目 / 证据行 | 无 | 10 / 13 |
| CP3 契约门 | 无 | 8 / 8 |
| 单册墙钟耗时（3 次中位数） | 0.392 s | 1.508 s |
| 画的版式 | Title Slide + Title and Content | Title Slide + Title and Content |
| 画布 | 12192000×6858000 EMU | 12192000×6858000 EMU |

时间代价 +1.116 s 换的是上表全部可核验记录项；**两臂模板与画布相同**，差异来自
流程而不是模板来源。完整协议与指标定义见 `references/GAIN-PROTOCOL.md`。

**平台正式对照**（3 案例 × 3 次复跑、基础 Agent vs Skill Agent）由组织方执行；
本表只是作者在合成示例上的局部实测，**不冒充成绩**。

## 9. 已知限制（如实）

- 预览为 PIL 示意图（`preview_is_schematic=true`），**非像素级导出**；PDF 导出需
  PowerPoint/LibreOffice，本机无，故未产 PDF（记录在 `render_log.json`，
  相应地 `output_contract` 中 PDF 类字段恒为 `false`）；
- CJK 行高为估算，极端字体环境可能与 PowerPoint 实际排版有偏差（有溢出报告 B12
  兜底）；
- 主题色/主题字体为**只读记录**（读 `theme1.xml`），不改写主题 XML；
- 内置回退模板主题的 ea（CJK）字体为空（python-pptx 默认模板特性），CJK 由
  系统/预览字体回退承担，已在 `template_audit.theme` 中如实呈现；
- 本机无 `reportlab` / `cairosvg` 依赖需求，Skill 不依赖它们；
- 路径记录策略（§3）：`artifacts.abspath` / `template_source` / 预览日志路径恒为
  运行相对路径；**材料与图表路径按调用方给的形式记录**（传相对即相对、传绝对即
  绝对）。跨目录比对 JSON 时字样会不同 —— 那是记录差异，不是产物差异
  （pptx / PNG 仍逐字节一致）；
- **确定性不是"全文件逐字节"**：result.json 里有两处会变 —— `generated_at`
  （时间戳）与 `uncertainty` 中回退模板的来源措辞（§2）。宣称"完全逐字节可复现"
  是不准确的，本文按实测写 11/12。
- 包内**不含任何二进制资源**（模板、示例图、预览、产物都在运行时生成），因此
  首次运行前若案例不给模板，需要可写的 `--out` 目录来放 `_runtime/builtin.pptx`。

## 10. 包体合规自证（硬门）

```bash
cd <efficiency-3 工作目录>
# 1) 权威验收：扩展名白名单 / ≤50 文件 / 单文件 ≤500KB / 合计 ≤2MB / 无符号链接 /
#    无 __pycache__ / UTF-8 可读 / py_compile / 无本机绝对路径标记
python validate_pkg.py <包目录>                       # PASS, 0 FAIL, 0 warn

# 2) 等价直查：盘符 + 反斜杠形态（用正则字符类书写，避免本文件自身含该字面量）
grep -rnE '[A-Za-z]:[\]' <包目录>                     # 0 命中
grep -rnE '[/]Users[/]'  <包目录>                     # 0 命中

# 3) 二进制残留
find <包目录> \( -name '__pycache__' -o -name '*.pyc' \)   # 0 命中
```

| 硬门 | 限制 | 实测 |
|-|-|-|
| 文件数 | ≤ 50 | **37** |
| 单文件 | ≤ 500KB | 最大 32,352 B（`examples/output/result.json`） |
| 合计 | ≤ 2MB | 347,357 B（约 339 KB） |
| 扩展名 | 仅 `.md/.py/.json/.txt` | 全部命中白名单，无 `.pdf/.pptx/.png/.svg/.jsonl/.pyc` |
| 符号链接 | 不允许 | 0 个 |
| UTF-8 可读 + `py_compile` | 全部通过 | 13/13 脚本编译通过 |
| 本机绝对路径 | 0 处 | `validate_pkg.py` PASS + 穷举扫描 0 命中 |
| `__pycache__` | 不允许 | 已删除（交付前最后一步执行，验证器已复核） |


---

## 11. 故障注入演练实测（union 新增轴 · 明细见 `references/FAULT-MATRIX.md`）

**验证对象**：本包在"东西坏掉"时的真实行为 —— 退出码、`status`、`uncertainty` 字段，
以及**是否静默失败**。装置：`scripts/fault_inject.py`（18 个场景 / 4 个故障家族 / 1 个控制组）。

```bash
RUN=<包外可写目录>; cp -r "$SKILL_DIR" "$RUN/pkg"
python "$RUN/pkg/scripts/fault_inject.py" --skill "$RUN/pkg" --run "$RUN/faultrun" \
    --json "$RUN/fault-report.json" --markdown "$RUN/fault-table.md"
# 实测输出末行：18 scenarios, 0 silent failure(s)，退出码 0
```

| 家族 | 场景数 | 命中/验证的规则 |
|-|-|-|
| control（无注入） | 1 | 参照组：CP3 8/8、`valid=true`、产物 12 个 |
| input | 6 | D1（case 缺失/坏 JSON）· D2（材料缺失/非 UTF-8）· D12（图件缺失） |
| template | 3 | D6（模板缺失 / 损坏 / 起始 deck 损坏，实测 `template_errors` 0 或 1 条） |
| dependency | 4 | D16（依赖缺失 → exit 1）· `--out` 不可写 → **exit 2、不写半截 JSON** |
| contract | 4 | G1（case_id 一致）· **G3（删契约键）** · **G7+G8（删产物）** |

**实测要点**（全部来自本次运行，逐行见 `FAULT-MATRIX.md` §2–§3）：

1. **18 个场景 / 0 个静默失败**，`fault_inject.py` 退出码 **0**。
2. **退出码三档实测**：`0`（跑完，status 可为 success/partial）· `1`（中途失败但写出诚实的
   `status=failed`；`uncertainty[0].note` 含原始 `ImportError` / `FileNotFoundError` /
   `JSONDecodeError` 文本）· `2`（`--out` 不可写，**产物目录内 0 个文件**）。
3. **独立门真的独立**：两次"跑完再篡改"都被 `check_contract.py` 判不合格 ——
   删一个契约键 → `valid=false`、失败门 **G3**；删封面预览 → `valid=false`、失败门 **G7, G8**；
   而 `result.json` 自己的自述仍是 `status=success`。**组内唯一通过的是控制组（valid=true）。**
4. **宿主差异如实保留**：`--out` 只读目录（`chmod 0444`）在 Windows 上拦不住写入，
   实测照常成功 → 该场景标记 `HOST-DIFF`，**不改判据、不改成"通过"**。
5. **已知粗糙点 3 条**（`FAULT-MATRIX.md` §4，同时写进 `SKILL.md` §3.5）：
   缺图只进 `uncertainty` 不改 `status`（且 `figures_embedded` 仍报 2/2）；
   `--task` 缺失没有专属记录（只有空 `task_summary`）；材料/图件类降级一律不拉低 `status`。

**未覆盖**：真实生产故障（本次是**伪造注入**）、非 Windows 宿主、平台侧评测失败。
`d04` 那条宿主差异在本机**无法**验证，故不宣称。

## 12. 题集泛化实测（union 新增轴 · 明细见 `references/CASE-SET.md`）

**验证对象**：换题材、换页预算、换输入完整度之后，契约层与证据层是否仍然成立。
装置：`scripts/run_case_set.py` + `examples/cases/case_manifest.json`（把可接受区间
**事先声明**，再由脚本对拍）。

```bash
RUN=<包外可写目录>; cp -r "$SKILL_DIR" "$RUN/pkg"
python "$RUN/pkg/scripts/run_case_set.py" --skill "$RUN/pkg" \
    --cases "$RUN/pkg/examples" --run "$RUN/caseset" \
    --json "$RUN/caseset.json" --markdown "$RUN/caseset.md"
# 实测输出末行：3 cases, 0 out of declared range, 1 declared boundary hit(s)，退出码 0
```

| 案例 | 难度层 | 题材 | exit | status | slide_count | 讲稿覆盖 | 证据定位覆盖 | 图表落位 | CP3 门 | 顶层 null | 判定 |
|-|-|-|-|-|-|-|-|-|-|-|-|
| `example-catalyst-201` | L0 基线接口 | 催化化学（CO₂ 加氢制甲醇） | 0 | `success` | 10（=10） | 1.00 | **1.000** | 2/2 | **8/8** | 0 | in-range |
| `case-b-gnn-potential-301` | L1 结构完整 | 计算材料（GNN 势函数 / 固态电解质） | 0 | `partial` | 13（∈[12,13]） | 1.00 | **1.000** | 2/2 | **8/8** | 0 | boundary-hit |
| `case-c-uhi-remote-302` | L2 退化输入 | 城市环境遥感（热岛归因） | 0 | `partial` | 9（=9） | 1.00 | **1.000** | 1/1 | **8/8** | 0 | in-range |

**实测要点**：

1. **三案共同点**：`evidence_loc_frac` 全部 **1.000**、CP3 门全部 **8/8**、顶层 `null`
   全部 **0**、方案套用 **10/10、13/13、9/9 且偏差 0**。换题材/换页预算/换输入完整度后，
   **契约层与证据层没有退化**。
2. **L2 的关键证据**：案例 C 的 `case.json` **不含**六个故事线字段，运行后
   `content.json.supplemented_from_material` 的**六个桶全部为真**，
   六个桶条数 6 / 8 / 7 / 5 / 5 / 3，来源全部形如 `material.md:<行号>`。
3. **两处非 `ok` 检查**（均由 `content.claim_coverage` 报 warn，两案因此 `status=partial`）：
   案例 B 报 **1** 条（p8，**只有表格没有图**的结果页丢掉了自己的主张条目）；
   案例 C 报 **2** 条（p4 一页塞 6 条主张，末尾两条被文本框装不下而丢；
   另一条同属"只有表格"的 p5）。
4. **一处已声明边界**：案例 B 声明 12 页、实测 **13** 页 —— `deckplan` 的"每条结果一页"
   分支要求 `(target-fixed-3) >= result_pages_needed`，该案为 `4 >= 7` 不成立 ⇒ 每条带媒体
   的结果各占一页（7 张）；尾部裁剪**最多回收 3 页**，不足以回到 12。**未修改脚本**，
   登记为已声明边界（区间 `[12, 13]` + 理由）。
5. **未覆盖**（`CASE-SET.md` §4.4）：跨模板族（三案全部 `opened_from=builtin`）·
   真 PDF/像素级导出 · 英文分支 · 起始 deck 编辑 · 上百行长材料 · 单页 3 张以上并排图。

## 13. 本包的合规自证复跑（union 包，文件数贴上限）

```bash
cd <efficiency-3 工作目录>
python validate_pkg.py <本包目录>        # 期望 [PASS]
find <本包目录> \( -name '__pycache__' -o -name '*.pyc' \)   # 期望 0 命中
```

本包是 union 包，**文件数正好 50（上限 50）**，因此为守住硬门把同主题的两份 reference
并成了一份：原 `references/batch-rules.md` 的全文已并入 `references/checklist.md` 的
**附章**（章节编号原样保留，**内容一字未删**）。同理，`failure-modes.md` 与
`two-phase-workflow.md` 各自把另一条叙述线的全文并成了**附录 A / 附录 B**。
⇒ **后续若再超限，继续合并同主题文档，不要删内容。**
