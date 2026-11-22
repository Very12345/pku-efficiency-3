# TEST —— 本地实测记录（ppt-710fbc72 / academic-slide-adapt 2.0.0，文本资源形态）

环境：Windows 11 + Git Bash(MSYS2)；`python` = Anaconda Python 3.13.9；
python-pptx 1.0.2 / Pillow 12.3.0 / numpy 2.3.5 / matplotlib 3.10.6（后两者仅用于
版本记录，Skill 运行时只依赖 python-pptx + Pillow）。
无 LibreOffice / uno ⇒ 预览为 PIL 示意图（如实标注，不产伪 PDF）。
日期：2026-11-22（Asia/Shanghai）。

约定：`$SKILL_DIR` = 本包根目录（平台装到 `/skills/weekly-skill`）；
`$RUN` = 任意**可写**临时目录（示例材料复制到这里，包内保持只读）。
**所有命令都在 cwd ≠ `$SKILL_DIR` 的情况下执行过**（见 §3），因此命令里的
`"$SKILL_DIR"` 前缀是必需的，不是装饰。

```bash
SKILL_DIR=<本包根目录>
RUN=<临时目录>; mkdir -p "$RUN"
cp -r "$SKILL_DIR/examples" "$RUN/examples"          # §1–§2 的基准用例
python "$SKILL_DIR/scripts/make_synthetic_inputs.py" --dir "$RUN/examples"
```

## 0. 语法编译检查

```bash
cd "$SKILL_DIR" && python -m py_compile scripts/*.py && rm -rf scripts/__pycache__
```
结果：**成功**（exit 0，13 个脚本 `common / extract / deckplan / adopt_plan /
adapt_pptx / pptx_toolkit / preview / audit / main / validate_result /
check_contract / make_template / make_synthetic_inputs` 全部通过）。
> 交付前务必删掉 `scripts/__pycache__`：二进制 `.pyc` 属于平台拒绝的资源类型。

## 1. 正式冒烟（示例案例，运行时生成的回退模板，两阶段全流程）

```bash
cd "$RUN"
python "$SKILL_DIR/scripts/make_synthetic_inputs.py" --dir examples
python "$SKILL_DIR/scripts/main.py" --case examples/case.json --task examples/task.md \
    --out examples/output
```
结果：**成功（exit 0）**，`status=success`，**10 页 = 目标 10 页**，CP3 契约门
**G1–G8 全过**（`check_contract` exit 0）。产出（`examples/output/`）：

| 文件 | 大小 | 校验 |
|-|-|-|
| `example-catalyst-201_deck.pptx` | 80,692 B | python-pptx 重开 ok；10 slides；2 张嵌入图；10 页 speaker notes；页脚/页码自第 2 页起统一；sha256 前缀 `c41cb2ce6db055ce` |
| `example-catalyst-201_cover_preview.png` | 55,727 B | PNG 签名 ok，1280×720，SCHEMATIC 标注 |
| `example-catalyst-201_slides_contact_schematic.png` | 133,421 B | PNG 签名 ok，10 页联系表 |
| `adopt_plan.json` | 16,696 B | 阶段一方案：模板审计（builtin：1 母版 / 11 版式 / 占位符清单 / 主题字体 Calibri + 12 个主题色）、10 页版式分配、批量规则 0 偏差、3 条图表放置计划、`gates` 全 ok |
| `result.json` | 32,148 B | status=success；case_id 一致；`output_contract` 7 个键全部回显顶层且为**真实值**；21 条检查全 `ok`；`verification.contract_gates` 8/8 ok |
| `spec.json` / `content.json` / `audit.json` / `render_log.json` / `summary.txt` | — | 见下方审计摘要 |
| `_runtime/builtin.pptx` | 27,522 B | 案例未给模板 ⇒ **运行时现场生成**的回退模板（16:9），来源记入 `template_audit.template_source` 与 `uncertainty` |

审计摘要（`audit.json`，21 条全 `ok`）：`artifact.*.exists`（pptx/两预览/spec/
adopt_plan）、`pptx.reopen` 10 slides、`pptx.slide_count` 10==10、
`content.claim_coverage`、`xref.figure_refs`、`xref.figure_placement` 2/2 上图、
`notes.present` 10/10、`layout.overflow` 0、`layout.font_floor` 无、
`layout.footer_uniform` ok、`preview.cover_png`/`preview.contact_png` 签名 ok、
`traceability.evidence_loc` 13/13 = 100%、**`adopt_plan.consistency`（10/10 页按
方案套用、0 偏差）**、`adopt_plan.gates` ok、`result.contract` ok、
`result.contract_gates` ok。

契约回显实测（`result.json` 顶层）：`template_inheritance=true`、
`slide_count=10`、`audience="催化方向课题组组会"`、`language="zh"`、
`evidence_per_slide=true`、`notes_per_slide=true`、`preview_png=true`；
派生来源见 `verification.contract_echo_derived`；`uncertainty` 记录"内置回退模板
为运行时生成"这一条；`verification.traceability.evidence_loc_frac=1.0`。

**为此交付的文本产物**即上面这次运行的 `result.json` / `summary.txt` /
`render_log.json`（二进制按平台硬门不随包分发）。可复现性核对（在另一处临时目录
按同样命令重跑）：

```text
example-catalyst-201_deck.pptx                 sha256 == 随包记录  c41cb2ce6db055ce
example-catalyst-201_cover_preview.png         sha256 == 随包记录  588d51d9e1dfb524
example-catalyst-201_slides_contact_schematic.png  sha256 == 随包记录  2b60b2deac0042b9
spec.json / adopt_plan.json / content.json / render_log.json
    与随包样例结构逐字段相同（仅"记录的路径字符串"因输出目录不同而不同）
```

即**三个二进制产物逐字节可重建**，随包文本记录与运行结果同构。

## 2. 确定性复现（同输入 → 除时间戳外逐字节相同）

同一命令对**同一输出目录**连跑两次，逐文件 sha256 对拍：

```text
13 个文件（含 _runtime/builtin.pptx）中 12 个 identical == True
唯一差异：result.json —— 顶层 key 差异 = ['generated_at']（其余逐字节相同）
```

**通过**：页计划与适配方案是确定性纯函数；pptx 经 `deterministic_zip()` 固定
zip 条目时间戳（并折叠同名条目）后同输入同字节；回退模板生成同样是确定性的。
`artifacts.abspath` 记录的是**运行相对路径**，因此换输出目录只会改变路径字样，
不会把本机盘符带进记录。

## 3. 自定位（cwd 不是技能根目录）

```bash
cd <任意无关目录>            # 例如系统临时目录
python "$SKILL_DIR/scripts/main.py" --case "$RUN/examples/case.json" \
    --task "$RUN/examples/task.md" --out "$RUN/out"
```
结果：**exit 0**，`status=success`，10 页、图 2/2 上图。路径记录的真实行为
（按 `scripts/common.py` 的 `portable_path()` / `slash()`）：

- `result.json.artifacts[].abspath`、`template_audit.template_source`、
  `verification.render.*.path` 记的是**运行相对路径**（相对当前工作目录、
  正斜杠）——上面这次运行里形如
  `eff3-ppt710-smoke/selfloc/out/_runtime/builtin.pptx`，**不含盘符或用户目录**；
- 材料与图表路径由 `extract._locate()` 解析后记录：**调用方传相对路径 → 记录为
  相对路径**（随包示例即如此，形如 `examples/figs/fig1.png`）；调用方传绝对路径
  → 记录为该解析结果（例如容器里的 `/app/work/figs/fig1.png`）。这是真实 I/O
  路径，不是包内残留：**包内文件本身 0 处本机路径**（`validate_pkg.py` PASS +
  `grep -rn` 无命中，见 §7）。

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
    --spec "$RUN/spec.json" --out "$RUN" \
    --build-audit "$RUN/example-catalyst-201_deck.build_audit.json" \
    --adopt-plan "$RUN/adopt_plan.json"
```
结果：全部 **exit 0**（`opened_from=builtin`、`adopt_plan_applied=10`、
`deviations=0`、审计 0 fail/0 warn）。注意 `--out` 语义不同：
`extract/deckplan/preview/audit` 收**目录**，`adopt_plan/adapt_pptx/make_template`
收**文件**，与 `--help` 一致。

## 4. 鲁棒性用例（全部为真实运行）

### 4a. 模板打不开（损坏文件）→ 回退
```bash
printf 'NOT A ZIP FILE' > "$RUN/fix/broken_template.pptx"
python "$SKILL_DIR/scripts/main.py" --case "$RUN/examples/case.json" \
    --template "$RUN/fix/broken_template.pptx" --out "$RUN/r1"
```
结果：**exit 0**，`status=success`，`opened_from=builtin`、`template_errors` 1 条、
`adopt_plan_applied=10/10`。

### 4b. 显式有效模板（模板套用路径）
```bash
python "$SKILL_DIR/scripts/main.py" --case "$RUN/examples/case.json" \
    --template "$RUN/r1/_runtime/builtin.pptx" --out "$RUN/r2"
```
结果：**exit 0**，`opened_from=case_template`、`adopt_plan_applied=10/10`。

### 4c. 起始 deck 编辑（3 页旧 deck → 重建 10 页，沿用其母版）
```bash
python "$SKILL_DIR/scripts/main.py" --case "$RUN/examples/case.json" \
    --starting-deck "$RUN/fix/start_deck.pptx" --out "$RUN/r3"
```
结果：**exit 0**，`opened_from=starting_deck`、`dropped_original_slides=3`、
`change_records[0].action=edit_starting_deck`（3 → 10）；产出的 pptx **只有 10 个
`ppt/slides/slideN.xml`、zip 无同名条目**（旧页连关系一起移除，不留残件）。

### 4d. 契约校验与 CP3 门（独立工具，从磁盘重扫）
```bash
python "$SKILL_DIR/scripts/validate_result.py" --case "$RUN/examples/case.json" \
    --result "$RUN/examples/output/result.json"       # VALID ; exit 0
python "$SKILL_DIR/scripts/check_contract.py" --result "$RUN/examples/output/result.json" \
    --out-dir "$RUN/examples/output" --case "$RUN/examples/case.json"   # valid=true ; exit 0
```
结果：两项 **exit 0**；G1–G8 逐门 `ok`（G7 artifacts=8 missing=[]）。

### 4e. 依赖缺失 / 输入缺失 / 输出不可写（诚实失败，不抛裸栈）
```bash
# 模拟缺 python-pptx / 缺 Pillow（把同名模块放进 PYTHONPATH 使其导入即抛 ImportError）
PYTHONPATH=<fake-pptx> python "$SKILL_DIR/scripts/main.py" --case ... --out "$RUN/nopttx"
PYTHONPATH=<fake-PIL>  python "$SKILL_DIR/scripts/main.py" --case ... --out "$RUN/nopil"
python "$SKILL_DIR/scripts/main.py" --case "$RUN/missing.json" --out "$RUN/d1"
python "$SKILL_DIR/scripts/main.py" --case "$RUN/examples/case.json" --out "$RUN/afile"   # afile 是普通文件
```
结果：
- 缺 python-pptx：**exit 1**，stderr 一行 `main FAILED: ...`，`result.json` =
  `status=failed` + `uncertainty[0].note = "ImportError: simulated: python-pptx not installed"`；
- 缺 Pillow：同上（`status=failed`，原因如实记录）；
- case.json 缺失：**exit 1**，`result.json` = `status=failed`（case_id 取文件名 stem，
  异常原因进 `uncertainty`）；
- `--out` 指向普通文件：**exit 2**，stderr 两行说明"管道错误 + 目标不可写"，
  不产生半截 JSON、不抛裸栈（见 failure-modes F23）。

## 5. 对照（增益方向，非平台白板）

同一示例案例、同一模板：朴素做法（整段正文塞进默认版式、无版式审计、无页脚
页码、无讲义、无证据映射、**无适配方案**）对比本 Skill 输出：

| 维度 | 朴素基线 | 本 Skill 输出（实测字段） |
|-|-|-|
| 模板套用 | 无（默认版式硬填） | 两阶段方案：`adopt_plan.json`（母版/版式/占位符 + 主题字体色）→ 10/10 页按方案套用、0 偏差 |
| 页级证据 | 无 | `slide_evidence` 10 页 + 13/13 主张带 `文件:行`（`evidence_loc_frac=1.0`） |
| 批量一致性 | 无 | 批量规则：页脚/页码/标题位置/字号阶梯统一，audit 4 项检查 `ok` |
| 讲稿 | 无 | 10/10 页 speaker notes（主张/证据/建议时长） |
| 起始 deck 改编 | 手工删页（旧页易残留） | 旧页连关系移除，`dropped_original_slides=3` + `change_records` |
| 契约门 | 无 | CP3 G1–G8 全过（`check_contract.py` exit 0） |
| 诚实降级 | 无 | 失败模式 23 项 + D1–D12 + 状态一致性纪律（§4 全部实测） |

平台正式对照（3 案例 × 3 次复跑、基础 Agent vs Skill Agent）由组织方执行；
本表只是设计方向的局部记录，**不冒充成绩**。

## 6. 已知限制（如实）

- 预览为 PIL 示意图（`preview_is_schematic=true`），非像素级导出；PDF 导出需
  PowerPoint/LibreOffice，本机无，故未产 PDF（记录在 `render_log.json`，
  相应地 `output_contract` 中 PDF 类字段恒为 `false`）；
- CJK 行高为估算，极端字体环境可能与 PowerPoint 实际排版有偏差（有溢出报告兜底）；
- 主题色/主题字体为只读记录（读 `theme1.xml`），不改写主题 XML；
- 内置回退模板主题的 ea（CJK）字体为空（python-pptx 默认模板特性），CJK 由
  系统/预览字体回退承担，已在 `template_audit.theme` 中如实呈现；
- 本机无 `reportlab`/`cairosvg` 依赖需求，Skill 不依赖它们；
- 路径记录策略（见 §3）：`artifacts.abspath` / `template_source` / 预览日志路径
  恒为运行相对路径；**材料与图表路径按调用方给的形式记录**——传相对路径即相对，
  传绝对路径即绝对（容器里就是 `/input`、`/app/work`）。因此跨目录/跨盘符比对
  JSON 记录时字样会不同，那是记录差异，不是产物差异（pptx/PNG 仍逐字节一致）；
- 包内**不含任何二进制资源**（模板、示例图、预览、产物都在运行时生成），
  因此首次运行前若案例不给模板，需要可写的 `--out` 目录来放 `_runtime/builtin.pptx`。

## 7. 包体合规自证（硬门）

```bash
cd /d/Work/科学挑战赛/work/efficiency-3
# 1) 权威验收：扩展名白名单 / ≤50 文件 / ≤500KB 单个 / ≤2MB 合计 / 无符号链接 /
#    无 __pycache__ / UTF-8 可读 / py_compile / 无本机绝对路径标记（盘符与 UNC 前缀）
python validate_pkg.py final/ppt-710fbc72              # PASS, 0 FAIL, 0 warn

# 2) 等价直查：盘符 + 反斜杠形态（用正则字符类书写，避免本文件自身含该字面量）
grep -rnE '[A-Za-z]:[\]' final/ppt-710fbc72            # 0 命中
#    用户目录形态
grep -rnE '[/]Users[/]' final/ppt-710fbc72             # 0 命中

# 3) 二进制残留
find final/ppt-710fbc72 \( -name '__pycache__' -o -name '*.pyc' \)    # 0 命中
```

| 硬门 | 限制 | 实测 |
|-|-|-|
| 文件数 | ≤ 50 | **37** |
| 单文件 | ≤ 500KB | 最大 32,352 B（`examples/output/result.json`） |
| 合计 | ≤ 2MB | 326,376 B |
| 扩展名 | 仅 `.md/.py/.json/.txt` | 全部命中白名单，无 `.pdf/.pptx/.png/.svg/.jsonl/.pyc` |
| 符号链接 | 不允许 | 0 个 |
| UTF-8 可读 + `py_compile` | 全部通过 | 13/13 脚本编译通过 |
| 本机绝对路径 | 0 处 | `validate_pkg.py` PASS + 穷举扫描 0 命中 |
| `__pycache__` | 不允许 | 已删除（交付前最后一步执行，验证器已复核） |

