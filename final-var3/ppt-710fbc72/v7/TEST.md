# TEST —— 本地实测记录（v7 · 确定性与字节级可复现）

环境：Windows 11 + Git Bash(MSYS2)；`python` = Anaconda **Python 3.13.9**；
python-pptx 1.0.2 / Pillow 12.3.0。无 LibreOffice ⇒ 预览为 PIL 示意图（如实标注）。
日期：2026-11-23（Asia/Shanghai）。

约定：`$SKILL_DIR` = 本包根目录；`$RUN` = **包外**可写临时目录。
**所有命令都是在 cwd ≠ `$SKILL_DIR` 的情况下执行的**（否则 `"$SKILL_DIR"` 前缀就
没有意义了），并且**从不在包内跑脚本**——包内执行会留下 `scripts/__pycache__/*.pyc`，
而 `.pyc` 是题面资源契约明确拒收的类型。

```bash
SKILL_DIR=<本包根目录>
RUN=<包外临时目录>; mkdir -p "$RUN"
cp -r "$SKILL_DIR/examples" "$RUN/examples"                 # §1 的基准用例
python "$SKILL_DIR/scripts/make_synthetic_inputs.py" --dir "$RUN/examples"
```

## 0. 语法编译检查

```bash
cd "$SKILL_DIR" && python -m py_compile scripts/*.py && rm -rf scripts/__pycache__
```
结果：**成功**（exit 0，14 个脚本含本轴新增的 `determinism.py` 全部通过）。
> 交付前务必删掉 `scripts/__pycache__`。

## 1. 正式流程冒烟（main.py）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$RUN/examples/case.json" \
    --task "$RUN/examples/task.md" --out "$RUN/out"; echo "exit=$?"
```

实测输出（原文）：

```
figure ready: examples/figs/fig1.png (11108 B)
figure ready: examples/figs/fig2.png (15422 B)
audit ok: 19 checks, fails=0, warns=0
main ok: case=example-catalyst-201 status=success slides=10 contract_gates=ok out=out
exit=0
```

- **exit = 0**，`status=success`，10 页，`contract_gates=ok`
- `result.json` **顶层键 28 个**（= 24 个信封/固定字段 + 示例案例契约回显 4 个）。
  信封/固定字段：`case_id, skill, status, workorder, task_summary,
  title, subtitle, audience, duration_minutes, language, slide_count, main_result,
  artifacts, slide_evidence, template_audit, adopt_plan, verification, sources,
  uncertainty, change_records, status_notes, generated_at, generator,
  tool_versions` + 契约回显 4 个（`template_inheritance, evidence_per_slide,
  notes_per_slide, preview_png`）——**无 `null` 占位**
- `--out` 下 **12 个产物**：`deck.pptx`、`cover_preview.png`、
  `slides_contact_schematic.png`、`result.json`、`spec.json`、`adopt_plan.json`、
  `content.json`、`audit.json`、`render_log.json`、`summary.txt`、
  `_PREVIEW_ARE_SCHEMATIC.txt`、`_runtime/builtin.pptx`
- 单次耗时 **≈1.2–2.2 s**

## 2. 契约门（validate_result.py + check_contract.py）

```bash
python "$SKILL_DIR/scripts/validate_result.py" --case "$RUN/examples/case.json" \
    --result "$RUN/out/result.json"; echo "validate exit=$?"
python "$SKILL_DIR/scripts/check_contract.py" --result "$RUN/out/result.json" \
    --out-dir "$RUN/out" --case "$RUN/examples/case.json" > "$RUN/gates.json"; echo "gates exit=$?"
```

实测：`validate exit=0`；`gates exit=0`，`gates.json` 中 `"valid": true`，
**G1–G8 全部 `ok`**（`run_gates` 逐项明细见 `result.json.verification.contract_gates`）。

## 3. ★ 本轴核心：determinism.py（16 次受控重跑）

```bash
python "$SKILL_DIR/scripts/determinism.py" --skill "$SKILL_DIR" --run "$RUN/det" \
    --runs 3 --json "$RUN/det.json" --markdown "$RUN/det.md"; echo "exit=$?"
```

实测输出（末尾 4 行原文）：

```
[determinism] json  -> <RUN>/det.json
[determinism] table -> <RUN>/det.md
[determinism] runs=16 L1_bin=True L2_json=False L3_json=True L4_stabilised=True undeclared=0
[determinism] verdict: PASS — 16 次运行（跨进程 / 跨 cwd / 跨 PYTHONHASHSEED / 相对与绝对参数）中：
  全部二进制交付物 L1 逐字节一致；全部 JSON 记录在 L4（去掉声明的时间戳、宿主锚点、锚点派生摘要）后
  收敛为单一值；声明表外出现差异的字段 0 条
exit=0
```

逐次实测（`$RUN/det.json` 的 `runs[]`，16 次**全部 exit 0 / status=success / 12 个产物**）：

| run | 条件 | cwd | 参数形态 | PYTHONHASHSEED | exit | 秒 |
|-|-|-|-|-|-|-|
| c1-1 | c1 独立进程 | cwdA | absolute | (unset) | 0 | 1.594 |
| c1-2 | c1 | cwdA | absolute | (unset) | 0 | 1.501 |
| c1-3 | c1 | cwdA | absolute | (unset) | 0 | 1.426 |
| c2-1 | c2 隔 1.2 s | cwdA | absolute | (unset) | 0 | 1.562 |
| c2-2 | c2 | cwdA | absolute | (unset) | 0 | 1.570 |
| c2-3 | c2 | cwdA | absolute | (unset) | 0 | 1.840 |
| c3-1 | c3 跨 cwd | cwdB/nest1 | absolute | (unset) | 0 | 1.544 |
| c3-2 | c3 | cwdB/nest1/nest2 | absolute | (unset) | 0 | 1.441 |
| c3-3 | c3 | cwdB | absolute | (unset) | 0 | 1.416 |
| c4-1 | c4 跨 hashseed | cwdA | absolute | 0 | 0 | 1.531 |
| c4-2 | c4 | cwdA | absolute | 1 | 0 | 1.562 |
| c4-3 | c4 | cwdA | absolute | 12345 | 0 | 1.550 |
| c4-4 | c4 | cwdA | absolute | (unset) | 0 | 1.527 |
| c5-1 | c5 相对参数 | cwdC | relative | (unset) | 0 | 2.193 |
| c5-2 | c5 | cwdC | relative | (unset) | 0 | 1.947 |
| c5-3 | c5 | cwdC | relative | (unset) | 0 | 1.740 |

**逐文件 sha256（全 16 次合并）**：

| 产物（相对 `--out`） | 原始 sha256 分组数 | 判定 |
|-|-|-|
| `example-catalyst-201_deck.pptx` | **1** | 16/16 逐字节一致 |
| `example-catalyst-201_cover_preview.png` | **1** | 16/16 逐字节一致 |
| `example-catalyst-201_slides_contact_schematic.png` | **1** | 16/16 逐字节一致 |
| `_runtime/builtin.pptx` | **1** | 16/16 逐字节一致 |
| `summary.txt` | **1** | 16/16 逐字节一致 |
| `_PREVIEW_ARE_SCHEMATIC.txt` | **1** | 16/16 逐字节一致 |
| `adopt_plan.json` | 3 | L3 收敛为 1 |
| `content.json` | 2 | L3 收敛为 1 |
| `spec.json` | 2 | L3 收敛为 1 |
| `render_log.json` | 14 | L3 收敛为 1 |
| `audit.json` | 4 | L4 收敛为 1 |
| `result.json` | 16 | L4 收敛为 1 |

稳定文件的 sha256 实测值：

```
deck.pptx                    c41cb2ce6db055ce5a0cb064384bbe3ac5eaa9c1e1d57478bdc911a50621a416
cover_preview.png            588d51d9e1dfb5242c4ae8ed4aa750ad0a6cdc68217a0543f7804543a51d6882
slides_contact_schematic.png 2b60b2deac0042b963bdd0b97e81d161c860d82eea88d3f39bc88ccb439fafbd
_runtime/builtin.pptx        f75fa66e4ebf88d1069df49adf7dbf7fe748c5e2f54c83e93d9e0f3e95c82995
```

**独立生成器跨 cwd 检查**（`determinism.py` 在准备阶段自动做）：

```bash
python "$SKILL_DIR/scripts/make_template.py" --out "$RUN/a/builtin.pptx"   # cwd = ...

实测：两个不同 cwd 下各跑一次，exit 均为 0，sha256 均为
f75fa66e4ebf88d1069df49adf7dbf7fe748c5e2f54c83e93d9e0f3e95c82995  → 相同
```

**字段级归因**（`volatile_field_attribution`，共 **41** 条，分布实测）：

| 归类 | 条数 | 例 |
|-|-|-|
| **故意**·宿主锚定（`HOST_ANCHOR`） | 34 | `artifacts[0].abspath`、`audit.json.checks[0].detail`、`render_log.json.cover.path` |
| **故意**·锚点派生摘要（`DERIVED_FROM_ANCHORED`） | 6 | `artifacts[i].checks.sha256`、`verification.traceability.hashes.spec_sha256` |
| **故意**·时间戳（`NONDETERMINISM`） | 1 | `generated_at` |
| **未声明** | **0** | — |

## 4. 边界与失败路径（实测）

```bash
# 4.1 拒绝把 --run 放进包内（避免 __pycache__ 污染提交包）
python "$SKILL_DIR/scripts/determinism.py" --skill "$SKILL_DIR" --run "$SKILL_DIR/scratch"
#   → stderr 打印拒绝理由，exit=2
# 4.2 未知条件名
python "$SKILL_DIR/scripts/determinism.py" --skill "$SKILL_DIR" --run "$RUN/det" --condition c9
#   → 打印已知条件列表，exit=2
# 4.3 只跑部分条件（调试）
python "$SKILL_DIR/scripts/determinism.py" --skill "$SKILL_DIR" --run "$RUN/det2" --condition c1,c4
#   → 正常执行，exit=0
```

## 5. 对照：本轴新增脚本没有改动任何既有脚本

```bash
for f in "$SKILL_DIR"/scripts/*.py; do ...; done   # 与基线包逐文件 cmp
```
实测：基线 13 个 `scripts/*.py` **逐字节相同**（`cmp` 无输出）；新增文件仅
`scripts/determinism.py` 1 个。CLI 参数、退出码语义未动。

## 6. 未通过 / 已知限制

1. **L2 单独不通过**（`L2_json=False`）：`spec/adopt_plan/content/render_log/audit/result`
   里带宿主锚点与锚点派生摘要。这不是缺陷，是设计取舍（见 `references/DETERMINISM.md`
   §3.2–§3.4）：路径是评审的定位符，删不得；判据因此定在 L4。
2. **未做跨机器比对**：16 次 run 全在同一台机器、同一个 Python 3.13.9。
3. **未覆盖**：并发写同一 `--out`；`--starting-deck`/`--template` 分支的确定性
   （本实验跑的是"案例未给模板"的回退路径，`opened_from=builtin`）。
4. `determinism.py` 会把整包复制到 `--run/skill` 再执行（被测的是包里那份字节，
   同时避免污染提交包）——因此**磁盘占用 ≈ 包体积 × 1**，属预期行为。
