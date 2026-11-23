# TEST.md — 本机实测记录（v8 契约矩阵版 · 2026-11-23 +08）

> 本文件记录**本包交付版本**的真实执行结果：命令、退出码与关键输出，供复核。
> 环境：Windows 11 / Anaconda Python 3.13.9（命令 `python`）/
> python-pptx 1.0.2、Pillow 12.3.0、matplotlib 3.10.6、PyMuPDF(fitz) 1.28.0、
> pypdf 6.14.2；**无 LibreOffice** —— 预览一律 PIL 近似渲染并如实标注。
>
> **全部命令都在包外的临时副本上执行**（把本包复制到临时目录后以该副本为 `$SKILL_DIR`），
> cwd 固定为 `/tmp`（**不是**技能根目录），同时验证 `$SKILL_DIR` 自定位写法。
> 包内不写入任何测试产物；矩阵与主流程的子进程都带 `PYTHONDONTWRITEBYTECODE=1`。

## T1 编译与文件形态 —— 通过

```bash
cd "$SKILL_DIR/scripts" && python -m py_compile *.py
# py_compile OK: 12 files   （11 个基线脚本 + 本版新增 contract_matrix.py）
```

## T2 运行期生成示例模板 —— 通过（exit 0）

```bash
python "$SKILL_DIR/scripts/make_template.py" --out "$SKILL_DIR/examples"
# status=ok  bytes=28420  starter_slides=1  layouts=11
```

## T3 端到端冒烟（示例案例）—— 通过（exit 0，result.json 顶层 19 键）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
  --task "$SKILL_DIR/examples/task.md" --spec "$SKILL_DIR/examples/deck-spec.json" \
  --out "$TMP/out"
# case_id=example-ppt-c7b80f0d  status=completed  deck=academic_deck.pptx (8 slides)
# previews=7  evidence_map=evidence_mapping.md (entries=6, gaps=0)  spec_lint=OK
# self_check=OK  exit=0
```

> **修复后回归**：把 T2/T3 在"已含 3 处纯增量修复"的 `main.py` 上重跑，结果不变
> （`status=completed`、`self_check=OK`、exit 0）；示例案例的 `output_contract` 是 dict
> 形态，修复只影响"未知布尔/数值声明 + 非法输入"这些此前会静默走样的分支。

## T4 ★CP4 契约矩阵 —— 修复前 / 修复后对照（本版主轴）

```bash
python "$SKILL_DIR/scripts/contract_matrix.py" --out "$TMP/m" --redact-paths \
  --before-fix "$TMP/before.json" --emit-md "$TMP/m/CONTRACT-MATRIX.md"
```

### 修复前（把 `main.py` 还原成基线版本后同一矩阵）

```
cells=28 exit0=23 result=28 selfcheck_ok=23 match=21 mismatch_recorded=2
caught_by_gate=5 incomplete_surface=5 crash=0 silent=5            exit=1
silent: A04 声明 number=0 回显 str=''
        A11 声明 bool=True 回显 bool=False
        A12 声明 bool=False 回显 str=''
        B02 声明 number=123 回显 str=''
        D03 清单中的非法元素（7/None）被静默丢弃
```

### 修复后（交付版本）

```
cells=28 exit0=23 result=28 selfcheck_ok=23 match=28 mismatch_recorded=0
caught_by_gate=5 incomplete_surface=5 crash=0 silent=0            exit=0
```

| 指标 | 修复前 | 修复后 |
|-|-|-|
| 写出 `result.json` | 28/28 | 28/28 |
| exit 0 的单元 | 23 | 23 |
| 回显符合期望（match） | 21 | **28** |
| 被记录/被门拦住（mismatch-recorded） | 2 | 0（全部转化为 match） |
| 内部自检点名问题的单元 | 5 | 5（"声明不全/非法容器"→ 19 字段面不完整，**被点名**） |
| **静默通过** | **5** | **0** |
| 崩溃 | 0 | 0 |
| 矩阵退出码 | 1 | **0** |

单元覆盖：① 字段→类型提示 ×14、② 字段→说明 ×2、③ 布尔开关 ×1、④ 字段清单 ×6、
契约容器 ×5（共 28）。矩阵总耗时约 **50 s**（每单元一次真跑，单次端到端 1.3–1.5 s）。

### 修复后关键单元的实际回显（从 `contract-matrix-data.json` 抄出）

| 单元 | 边界值 | 实际回显 |
|-|-|-|
| A04 | 声明 `0` | `cell_num_hint = 0`（number，不再塌缩成 `""`） |
| A11 | 声明 `true`（未知字段） | `cell_bool_true = true`（不再取反成 false） |
| A12 | 声明 `false`（未知字段） | `cell_bool_false = false`（不再变成 `""`） |
| A13/A14 | `notes_separated` 声明 true/false | 均回显 **deck 的真实状态** `true`（语义字段真实值优先） |
| B02 | 说明位写数字 `123` | `cell_desc_num = 123` |
| D03 | 清单混入 `7`/`null` | 非字符串元素被跳过，并写入 `uncertainty`（"contains 2 non-string entries … skipped instead of being echoed"） |
| E01 | 无 `output_contract` 键 | 回显 `{}`；顶层 19 字段**不完整** → 自检点名 `output contract fields missing: title, main_claim, slides, render_state, notes_separated`，exit 1 |
| E02 | 容器是字符串 | 回显 `{}` + `uncertainty` 记录"declared as str … no declared field was honoured"，exit 1 |
| E03 | 容器是 `null` | 同上（记录 + 门点名） |
| E05 | 只声明 1 个未知字段 | 回显该字段 + 19 字段面不完整被点名，exit 1 |

### 矩阵的负路径与自检

```bash
python "$SKILL_DIR/scripts/contract_matrix.py" --out "$TMP/n1" --only A01 \
  --entry "$TMP/_always_fail_entry.py"     # 入口不写 result.json → exit 3
python "$SKILL_DIR/scripts/contract_matrix.py" --out "$TMP/n2" --only ZZ9   # exit 2
python "$SKILL_DIR/scripts/contract_matrix.py" --out "$TMP/n3" --case "$TMP/nope.json"  # exit 2
python "$SKILL_DIR/scripts/contract_matrix.py" --out "$TMP/n4" --only A04,A11,A12,B02,D03
# 子集回归：cells=5 exit0=5 match=5 silent=0 → exit 0
```

## T5 三处纯增量修复（逐条点名，含风险控制）

| # | 位置 | 改动 | 依据（实测单元） | 风险控制 |
|-|-|-|-|-|
| F1 | `scripts/main.py: apply_output_contract()` | 未知字段名 + 布尔声明：`v is True → semantic.get(k, False)` 改为 `isinstance(v, bool) → semantic.get(k, v)` | A11 声明 true 回显 false；A12 声明 false 回显 `""` | 语义字段（`notes_separated` 等）仍优先取本次运行真实值 → A13/A14 行为不变（实测 match） |
| F2 | 同上 | 新增数值型声明分支（`int/float` 且排除 `bool`）：如实回显数字 | A04 声明 0、B02 声明 123 均回显 `""` | 只在"声明值本身是数字"时生效；str/list/dict/None 分支逻辑未改（A01–A03/A05–A08 实测 match 不变） |
| F3 | 同上 | ④ 清单中的非字符串元素、以及非法契约容器（字符串/`null`）不再静默：写入 `result["uncertainty"]` | D03 的 `7`/`null` 与 E02/E03 此前完全无痕 | 只在输入确实非法时追加一条 `uncertainty`；正常案例不触发（示例案例回归 uncertainty 仍为 1 条"模板回退"） |

**CLI 参数名/默认值/退出码语义未改动**（`main.py` 的 7 个 flag、其余脚本的 flag 全部保持，
见 `SKILL.md` §3）；除 `apply_output_contract()` 外 `main.py` 其余部分与另外 10 个脚本逐字节不变。

## T6 两道交付门 —— 通过（均 exit 0）

```bash
python "$SKILL_DIR/scripts/export_check.py" --result "$TMP/out/result.json" \
  --out-dir "$TMP/out" --case "$SKILL_DIR/examples/case.json"
# {"valid": true, "errors": [], "warnings": [], "status": "completed"}
python "$SKILL_DIR/scripts/check_contract.py" --result "$TMP/out/result.json" \
  --contract "$SKILL_DIR/references/OUTPUT_CONTRACT.md" --case "$SKILL_DIR/examples/case.json"
# {"valid": true, "fields_contracted": 19, "fields_present": 19, "missing": [], "present_but_null": []}
```

## T7 负路径（主流程）—— 退出码语义符合承诺

```bash
python "$SKILL_DIR/scripts/main.py" --case "$TMP/nope/case.json" --out "$TMP/x"   # exit 3
python "$SKILL_DIR/scripts/spec_lint.py" --spec "$TMP/broken-spec.json"           # exit 1（列出 5 条问题）
```

## T8 与既有版本的一致性（能力未丢）

```bash
# 逐文件 sha256 对拍（基线包 scripts/ vs 本包 scripts/）
# 实测：11 个基线脚本中 10 个逐字节相同；main.py 有 3 处纯增量修复（T5 逐条点名）；
#       本包新增 contract_matrix.py（新入口）
```

整包对拍（相对基线）：24 个文件逐字节未变；改动 7 个 = `GITHUB_URL.txt`（本轮链接）、
`SKILL.md` / `README.md` / `TEST.md`（按本版轴重写）、`scripts/main.py`（3 处修复）、
`references/RUBRIC_MAP.md` / `references/failure-modes.md`（在既有表格对应行内补入本版落点
与契约边界条目，未删改原有条目）；新增 4 个文件 = `scripts/contract_matrix.py` +
`references/CONTRACT-MATRIX.md` + 两份矩阵记录 JSON。

> 合规验收（`validate_pkg.py`）由主对话独立复跑：包内不跑脚本，避免留下 `__pycache__`。
