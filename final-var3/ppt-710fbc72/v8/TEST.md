# TEST —— 本地实测记录（v8 · 契约四形态 × 边界值矩阵）

环境：Windows 11 + Git Bash(MSYS2)；`python` = Anaconda **Python 3.13.9**；
python-pptx 1.0.2 / Pillow 12.3.0。无 LibreOffice ⇒ 预览为 PIL 示意图（如实标注）。
日期：2026-11-23（Asia/Shanghai）。

约定：`$SKILL_DIR` = 本包根目录；`$RUN` = **包外**可写临时目录。
**所有命令都在 cwd ≠ `$SKILL_DIR` 下执行**，并且**从不在包内跑脚本**——包内执行会
留下 `scripts/__pycache__/*.pyc`，而 `.pyc` 是题面资源契约明确拒收的类型。

```bash
SKILL_DIR=<本包根目录>
RUN=<包外临时目录>; mkdir -p "$RUN"
cp -r "$SKILL_DIR/examples" "$RUN/examples"
python "$SKILL_DIR/scripts/make_synthetic_inputs.py" --dir "$RUN/examples"
```

## 0. 语法编译检查

```bash
python -m py_compile "$SKILL_DIR"/scripts/*.py    # 在包外临时副本上做
```
结果：**成功**（exit 0，14 个脚本含本轴新增的 `contract_matrix.py` 全部通过）。

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
- `result.json` **顶层键 25 个**（= 21 个信封字段 + 示例案例的
  `output_contract` 回显 4 个：`template_inheritance / evidence_per_slide /
  notes_per_slide / preview_png`）。**完整信封（契约回显全算上）是 28 键**，
  这正是 §3 表格里各个注入用例的 24–26 键与之对得上的原因
- `--out` 下 **12 个产物**（含 `deck.pptx` 与两张 PNG）

## 2. 契约门

```bash
python "$SKILL_DIR/scripts/validate_result.py" --case "$RUN/examples/case.json" \
    --result "$RUN/out/result.json"; echo "validate exit=$?"
python "$SKILL_DIR/scripts/check_contract.py" --result "$RUN/out/result.json" \
    --out-dir "$RUN/out" --case "$RUN/examples/case.json" > "$RUN/gates.json"; echo "gates exit=$?"
```

实测：`validate exit=0`；`gates exit=0`，`"valid": true`，**G1–G8 全 `ok`**。
G3 的 detail 原文：`missing=[] null_placeholders=[]`。

## 3. ★ 本轴核心：contract_matrix.py（26 个用例）

```bash
python "$SKILL_DIR/scripts/contract_matrix.py" --skill "$SKILL_DIR" --run "$RUN/cm" \
    --json "$RUN/cm.json" --markdown "$RUN/cm.md"; echo "exit=$?"
```

实测输出末尾（原文）：

```
[contract_matrix] json  -> <RUN>/cm.json
[contract_matrix] table -> <RUN>/cm.md
[contract_matrix] 26 cases, 0 silent pass(es), 0 caught by the gate
exit=0
```

**逐用例实测（`cm.json` 的 `cases[]` 摘要）**：

| 用例 | 注入 | exit | 门 exit | status | 契约键 | 回显 | null | result 顶层键 | 判定 |
|-|-|-|-|-|-|-|-|-|-|
| A01-string | 字符串形态 | 0 | 0 | success | 1 | 1 | 0 | 25 | 按声明 |
| A02-list | 数组形态 | 0 | 0 | success | 1 | 1 | 0 | 25 | 按声明 |
| A03-object | 对象形态 | 0 | 0 | success | 1 | 1 | 0 | 25 | 按声明 |
| A04-number | 数值形态 | 0 | 0 | success | 1 | 1 | 0 | 25 | 按声明 |
| A05-boolean | 布尔形态 | 0 | 0 | success | 1 | 1 | 0 | 25 | 按声明 |
| A06-nested | 嵌套对象 | 0 | 0 | success | 1 | 1 | 0 | 25 | 按声明 |
| B01-empty-string | 空串 | 0 | 0 | success | 1 | 1 | 0 | 25 | 按声明 |
| B02-empty-list | 空数组 | 0 | 0 | success | 1 | 1 | 0 | 25 | 按声明 |
| B03-empty-object | 空对象 | 0 | 0 | success | 1 | 1 | 0 | 25 | 按声明 |
| B04-zero | 数值 0 | 0 | 0 | success | 1 | 1 | 0 | 25 | 按声明 |
| B05-false | 布尔 false | 0 | 0 | success | 1 | 1 | 0 | 25 | 按声明 |
| B06-null | 值 null | 0 | 0 | success | 1 | 1 | **0** | 25 | 按声明 |
| B07-very-long | 3000 字符值 | 0 | 0 | success | 1 | 1 | 0 | 25 | 按声明 |
| B08-very-long-key | 256 字符键 | 0 | 0 | success | 1 | 1 | 0 | 25 | 按声明 |
| B09-nonascii | 中文键 | 0 | 0 | success | 1 | 1 | 0 | 25 | 按声明 |
| B10-missing-key | 无 `output_contract` | 0 | 0 | success | 0 | 0 | 0 | 24 | 按声明 |
| B11-empty-contract | `{}` | 0 | 0 | success | 0 | 0 | 0 | 24 | 按声明 |
| B12-unknown-prefix | 语义未覆盖键 | 0 | 0 | success | 1 | 1 | 0 | 25 | 按声明 |
| B13-derived-known | 语义已知键 | 0 | 0 | success | 2 | 2 | 0 | 26 | 按声明 |
| B14-preview-false | `preview_png:false` | 0 | 0 | success | 1 | 1 | 0 | 25 | 按声明 |
| C01-case-missing | `--case` 不存在 | 1 | 1 | failed | — | 0 | 0 | 14 | 按声明 |
| C02-case-broken | 非法 JSON | 1 | 1 | failed | — | 0 | 0 | 14 | 按声明 |
| C03-contract-not-object | 契约是字符串 | **1** | 1 | **failed** | — | 0 | 0 | **14** | 按声明（信封降级） |
| C04-contract-list | 契约是数组 | **1** | 1 | **failed** | — | 0 | 0 | **14** | 按声明（信封降级） |
| C05-empty-case-object | `case.json = {}` | 0 | 0 | **partial** | 0 | 0 | 0 | 24 | 按声明 |
| C06-case-is-directory | `--case` 指向目录 | 1 | 1 | failed | — | 0 | 0 | 14 | 按声明 |

**实测到的三条硬结论**：

1. **`null` 占位 0/26**：契约自己声明 `null`（B06）时，顶层回显的是 `""` 而不是
   `null`——"禁止 null 占位"是硬约束。
2. **falsy 值没有被吞掉**：`0`（B04）、`false`（B05）、`""`（B01）、`[]`（B02）、
   `{}`（B03）全部**仍然出现在顶层**。
3. **静默通过 0 个**：包括两条本来会静默的路径（非对象契约），实测它们
   **exit=1 + `status=failed`**，独立门也返回 1，所以不构成静默。

**实测到的两处"值被改写"**：

| 用例 | 契约声明 | 顶层实测 | 同时记录在哪 | 是否静默 |
|-|-|-|-|-|
| `B14-preview-false` | `preview_png: false` | `true` | `contract_echo_derived={"preview_png": true}`；G8 `preview_required=False` | 否（可查来源、门按原值判定） |
| `C03` / `C04` | 契约不是对象 | 顶层无该键、整份 `result.json` 降级为 14 键失败信封 | `uncertainty[0].note = "AttributeError: 'str' object has no attribute 'items'"` | 否（管线承认失败） |

**容器类型保持**（`echoed_types`，实测）：

```
A01 str→str   A02 list→list   A03 dict→dict   A04 int→int
A05 bool→bool A06 dict→dict   B06 null→str    B09 中文键→str
```

**派生值可查**（`contract_echo_derived`，实测非空的两个用例）：

```
B13-derived-known : {"preview_png": true, "notes_per_slide": true}
B14-preview-false : {"preview_png": true}
```

## 4. 开关与失败路径（实测）

```bash
python "$SKILL_DIR/scripts/contract_matrix.py" --skill "$SKILL_DIR" --list
#   → 打印 26 个用例的 id / 家族 / 注入说明，exit 0
python "$SKILL_DIR/scripts/contract_matrix.py" --skill "$SKILL_DIR" --run "$RUN/cm2" --only A01,B06,C03
#   → 只跑 3 个用例，exit 0
python "$SKILL_DIR/scripts/contract_matrix.py" --skill "$SKILL_DIR" --run "$SKILL_DIR/scratch"
#   → 拒绝：stderr 说明包内跑会留下 __pycache__，exit 2
```

## 5. 对照：本轴没有改动任何既有脚本

实测：基线 13 个 `scripts/*.py` **逐字节相同**（`cmp` 无输出）；新增文件仅
`scripts/contract_matrix.py` 1 个。CLI 参数、退出码语义未动。
因此 §3 表格里 `C03`/`C04` 的崩溃是**基线已有行为**——本轴的贡献是把它测出来、
写清代价，而不是改掉它。

## 6. 未通过 / 已知限制

1. **`C03`/`C04` 的 `result.json` 降级为 14 键**（完整信封 28 键）：失败发生在
   `_echo_output_contract()`，此时 `result` 字典已构造但尚未写盘，异常路径改写了
   一份只含失败信封的 `result.json`。中间产物（10 个文件，含 deck 与两张 PNG）
   仍在。**只报告不修**（改既有脚本超出本轴范围）。
2. **`task.md` 里的契约不被识别**：本矩阵只测 `case.json.output_contract`。
3. **已知语义键只测了 2 个**（`preview_png` / `notes_per_slide`）：
   `_derive_contract_value()` 覆盖的其它前缀（template/evidence/editable/slide_count/
   figure…）未逐条实测。
4. **只判顶层**：G3 的判定粒度是顶层键；契约对象的**子键**是否要回显未测
   （按契约原文，粒度就是顶层）。
5. **未测并发**：多进程同时写同一 `--out`。
6. **`--out` 不可写**：已由 v4/v6 的 `fault_inject.py` 覆盖（`d03`/`d04`），此处不重复。
