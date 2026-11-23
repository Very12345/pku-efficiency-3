# TEST.md — 本机实测记录（v7 字节级可复现版 · 2026-11-23 +08）

> 本文件记录**本包交付版本**的真实执行结果：命令、退出码与关键输出，供复核。
> 环境：Windows 11 / Anaconda Python 3.13.9（命令 `python`）/
> python-pptx 1.0.2、Pillow 12.3.0、matplotlib 3.10.6、PyMuPDF(fitz) 1.28.0、
> pypdf 6.14.2；**无 LibreOffice** —— 预览一律 PIL 近似渲染并如实标注。
>
> **全部命令都在包外的临时副本上执行**（把本包复制到临时目录后以该副本为 `$SKILL_DIR`，
> 输出写到另一个临时目录），cwd 固定为 `/tmp`（**不是**技能根目录），
> 同时验证 SKILL.md 的 `$SKILL_DIR` 自定位写法。包内不写入任何测试产物；
> `determinism.py` 的子进程带 `PYTHONDONTWRITEBYTECODE=1`，探测过程也不产生 `__pycache__`。

## T1 编译与文件形态 —— 通过

```bash
cd "$SKILL_DIR/scripts" && python -m py_compile *.py
# py_compile OK: 12 files   （11 个基线脚本 + 本版新增 determinism.py）
```

包内只有 `.md/.py/.json/.txt` 四类扩展名，30+3 个文件，无二进制、无符号链接。

## T2 运行期生成示例模板 —— 通过（exit 0）

```bash
python "$SKILL_DIR/scripts/make_template.py" --out "$SKILL_DIR/examples"
# status=ok  bytes=28420  starter_slides=1  layouts=11
# renamed_layouts=[{8:"Picture with Caption"->"Figure Slide"},{5:"Title Only"->"Reference Slide"}]
```

模板为**运行期生成**：包内不携带任何 `.pptx`（技能资源只允许 UTF-8 文本文件）。
T2 之后示例案例走"模板适配分支"（`template.kind=file`）；不跑 T2 则走内置版式分支
（`kind=builtin`）——两条分支都做过 CP0 实测（T4 场景 F）。

## T3 端到端冒烟（示例案例）—— 通过（exit 0，result.json 顶层 19 键）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
  --task "$SKILL_DIR/examples/task.md" --spec "$SKILL_DIR/examples/deck-spec.json" \
  --out "$TMP/out"
```

```
case_id      : example-ppt-c7b80f0d
status       : completed
deck         : academic_deck.pptx (8 slides)
previews     : 7 files
evidence_map : evidence_mapping.md (entries=6, gaps=0)
spec_lint    : OK
sources      : 1  uncertainty: 0  changes: 2
self_check   : OK
```

`result.json` 顶层 **19 个键**（与 `OUTPUT_CONTRACT.md` §1 的 19 个字段逐条一致）：
`case_id, status, task, deck, evidence_mapping, evidence_map_json, spec_lint, previews,
charts, sources, uncertainty, change_records, run_meta, output_contract, title, main_claim,
slides, render_state, notes_separated`；`output_contract` 回显 6 个案例声明字段
（`title/main_claim/slides/evidence_mapping/render_state/notes_separated`）。

产出文件 13 个：`result.json`、`academic_deck.pptx`、`chart-Fig_1.png`、`chart-Fig_1.svg`、
`evidence_mapping.md`、`evidence_map.json`、`preview-approx-cover.png` +
`preview-approx-001..006.png`；`run_meta.checkpoints={cp1_spec_lint:true, cp2_build:true,
cp3_export_check:true}`、`self_check={ok:true, problems:[]}`、
`deck.template={kind:file, starter_slides_removed:1}`、`notes_separated=true`。

## T4 ★CP0 复现判据（本版主轴）—— 五组实测

### 场景 A：逐运行独立输出目录（默认），5 次，`--stabilize`

```bash
python "$SKILL_DIR/scripts/determinism.py" --out "$TMP/det" --runs 5 --stabilize
# [run i] exit=0 status=completed files=13 cwd=…/run-i 或 …/cwd-alt-i  seed=0/1/2/0/1
# identical : False (raw bytes) | canonical: True | stabilized: True
# volatile  : 5 explained json pointer(s), 3 file(s), 0 unexplained
# verdict   : deterministic (canonical)      exit=0
```

| 指标 | 实测 |
|-|-|
| 产物数 / 子运行数 | 13 / 5（全部 exit 0，`status=completed`） |
| 原始字节一致 | **False** —— 10/13 一致；不同者为 `academic_deck.pptx`、`chart-Fig_1.svg`、`result.json` |
| 规范化后一致 | **True**（13/13） |
| 稳定化后字节一致 | **True**（13/13，稳定化副本 5/5 相同） |
| 未解释差异 | **0** |
| 已解释 JSON 指针 | `/change_records/0/time`、`/change_records/1/time`、`/run_meta/timestamp`、`/run_meta/duration_seconds`、`/charts/0/chart/file`(out-dir-identity) |
| zip 成员载荷一致 | **True**（差异只在成员 mtime，观测值如 `19:06:04/06/08/10/12`） |
| SVG 元素 id | 每次 83 个，**12 个位置逐次不同**（样本 `ma34cbb377e`、`m58785d8163`、`p032a41b656`） |
| 探针耗时 | 5 次运行合计 **7.7 s**（单次端到端 1.32–1.48 s） |

### 场景 B：同目录（消除"输出目录身份"）

```bash
python "$SKILL_DIR/scripts/determinism.py" --out "$TMP/detB" --runs 3 --out-mode same-dir --stabilize
# identical: False | canonical: True | stabilized: True | unexplained 0 | exit 0
# volatile_fields 从 5 条降为 4 条（/charts/0/chart/file 消失）
```

### 场景 C：固定 matplotlib 的 SVG 盐（根因验证）

```bash
python "$SKILL_DIR/scripts/determinism.py" --out "$TMP/detC" --runs 5 \
  --svg-hashsalt v7-fixed --stabilize
# identical: False | canonical: True | stabilized: True | unexplained 0 | exit 0
# svg_id_sequences_stable = True （id_positions_differing: 0，默认模式为 12）
```

再对 5 次运行的 `chart-Fig_1.svg` 单独去掉 `<dc:date>` 内容后比对哈希：

```
raw sha (5 runs)     : 32db66ba… 11758f62… be318c8c… f3ca3ed1… ddc99648…   identical=False
dc:date-stripped sha : 62f4261d822d4055 ×5                                  identical=True
```

⇒ 固定盐后 SVG 的唯一残余差异就是 `<dc:date>`；随机来源 = `matplotlib.backends.backend_svg.
RendererSVG._make_id` 在 `rcParams['svg.hashsalt'] is None` 时用 `str(uuid.uuid4())`。

### 场景 D：探针自证（两次独立探测的可复现部分）

```bash
python "$SKILL_DIR/scripts/determinism.py" --out "$TMP/detD" --runs 3 --no-timestamp && \
  cp "$TMP/detD/determinism_report.json" "$TMP/r1.json" && \
python "$SKILL_DIR/scripts/determinism.py" --out "$TMP/detD" --runs 3 --no-timestamp
# per_file_canonical_sha256 两次完全相同：True
# per_file_sha256（原始字节）两次不同：符合预期（它记录的正是故意不稳定的字节）
```

### 场景 E：阴性对照（证明探针不是"永远说 OK"）

```bash
# 在包外副本里放一个会写随机数的入口，然后让探针去跑它
python "$SKILL_DIR/scripts/determinism.py" --out "$TMP/detE" --runs 3 \
  --entry "$TMP/_nondet_selftest_entry.py"
# unexplained_diffs = [{"pointer": "/roll", "kind": "unclassified", "observed": [0.0059…, 0.5759…, 0.9815…]}]
# identical: False | canonical: False | byte_identical_per_file: {"artifact.txt": true, "result.json": false}
# exit=1
```

⇒ 检测器对被注入的不确定性会**点名到字段**并给出非零退出；同时不会因为一个文件坏
就把稳定文件也说成不稳定。

### 场景 F：模板适配分支（`template.kind=file`）也做一轮

```bash
python "$SKILL_DIR/scripts/make_template.py" --out "$SKILL_DIR/examples"   # 先生成示例模板
python "$SKILL_DIR/scripts/determinism.py" --out "$TMP/detT" --runs 5 --stabilize
# identical: False | canonical: True | stabilized: True | unexplained 0 | exit=0
```

⇒ 内置版式分支与模板适配分支结论一致（13 个产物、同样的 5 条已解释指针、3 个含不稳定字节的文件）。

## T5 两道交付门 —— 通过（均 exit 0）

```bash
python "$SKILL_DIR/scripts/export_check.py" --result "$TMP/out/result.json" \
  --out-dir "$TMP/out" --case "$SKILL_DIR/examples/case.json"
# {"valid": true, "errors": [], "warnings": [], "case_id": "example-ppt-c7b80f0d", "status": "completed"}

python "$SKILL_DIR/scripts/check_contract.py" --result "$TMP/out/result.json" \
  --contract "$SKILL_DIR/references/OUTPUT_CONTRACT.md" --case "$SKILL_DIR/examples/case.json"
# {"valid": true, "fields_contracted": 19, "fields_present": 19, "missing": [],
#  "present_but_null": [], "case_contract_missing": []}
```

## T6 负路径 —— 退出码语义符合承诺

```bash
python "$SKILL_DIR/scripts/main.py" --case "$TMP/nope/case.json" --out "$TMP/out-missing"
# case file not found: …            exit=3

python "$SKILL_DIR/scripts/spec_lint.py" --spec "$TMP/broken-spec.json"
# {"valid": false, "problems": ["slide #1: missing one-line claim", "slide #1: 9 bullets > 6",
#   "slide #1: no evidence entries and evidence_gap not set (must be one of them)",
#   "missing deck takeaway sentence (closing slide)", "missing limitations sentence (closing slide)"],
#   "counts": {"slides": 1, "evidence_gaps": 0, "unmapped": 1}}          exit=1
```

CP0 自身的负路径：`--runs 1` → exit 2（单次运行无法谈可复现）；
入口不存在 → exit 2；子运行失败 → exit 3。

## T7 自定位（cwd 不是技能根）—— 通过

以上全部命令的 cwd 都是 `/tmp`，脚本与 `--case/--spec` 都用 `"$SKILL_DIR/..."`
绝对路径（或包外副本的绝对路径），无一条依赖 cwd；`make_template.py --out "$SKILL_DIR/examples"`
也只在技能目录下写运行期产物。

## T8 与既有版本的一致性（能力未丢）

```bash
python - <<'PY'
import hashlib, os
base = "<baseline>/scripts"; v7 = "<this pkg>/scripts"
h = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
same = diff = miss = 0
for rel in sorted(os.listdir(base)):
    if rel.endswith(".py"):
        a, b = os.path.join(base, rel), os.path.join(v7, rel)
        if not os.path.exists(b): miss += 1
        elif h(a) == h(b): same += 1
        else: diff += 1
print(same, diff, miss)
PY
```

实测输出：`11 0 0` —— 11 个基线脚本**逐字节相同**，0 个不同，0 个缺失；
`scripts/determinism.py` 是唯一新增入口。

整包对拍（相对基线）：**24 个文件逐字节未变**；改动的 6 个是
`GITHUB_URL.txt`（本轮链接）、`SKILL.md` / `README.md` / `TEST.md`（按本版轴重写），
以及 `references/RUBRIC_MAP.md` / `references/failure-modes.md`（仅在既有表格的对应行内
补入本版落点与 CP0 分支，未删改原有条目）；新增 4 个文件 = `scripts/determinism.py` +
`references/DETERMINISM.md` + 两份 `determinism_report*.json`。

11 个既有入口的 CLI 参数名、默认值与退出码语义均未改动（`determinism.py` 为新增入口，
不改变任何既有语义）；参数清单见 `SKILL.md` §3。

> 本机对拍命令与整包 diff 结论已在上方复述；`validate_pkg.py` 的合规验收由主对话独立复跑
> （包内不跑脚本，避免留下 `__pycache__`）。
