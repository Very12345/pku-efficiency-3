# TEST.md — 本机实测记录（v9 降级链实测版 · 2026-11-23 +08）

> 本文件记录**本包交付版本**的真实执行结果：命令、退出码与关键输出，供复核。
> 环境：Windows 11 / Anaconda Python 3.13.9（命令 `python`）/
> python-pptx 1.0.2、Pillow 12.3.0、matplotlib 3.10.6、PyMuPDF(fitz) 1.28.0、
> pypdf 6.14.2、PyYAML 可用；**无 LibreOffice**（`soffice` 不在 PATH 上）。
>
> **全部命令都在包外的临时副本上执行**（把本包复制到临时目录后以该副本为 `$SKILL_DIR`），
> cwd 固定为 `/tmp`（**不是**技能根目录），同时验证 `$SKILL_DIR` 自定位写法。
> 探针与主流程的子进程都带 `PYTHONDONTWRITEBYTECODE=1`，包内不留 `__pycache__`。

## T1 编译与文件形态 —— 通过

```bash
cd "$SKILL_DIR/scripts" && python -m py_compile *.py
# py_compile OK: 12 files   （11 个基线脚本 + 本版新增 degrade_probe.py）
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
# previews=7  charts=1  evidence_map=evidence_mapping.md (entries=6, gaps=0)
# spec_lint=OK  self_check=OK  exit=0   产出 13 个文件
```

## T4 ★降级链矩阵（本版主轴）—— 8 个场景 + 9 个依赖探测

```bash
python "$SKILL_DIR/scripts/degrade_probe.py" --out "$TMP/dg" --redact-paths \
  --emit-md "$TMP/dg/DEGRADE-MATRIX.md" --json "$TMP/dg/degrade_matrix.json"
# [dep-graph] import pptx=ok; import PIL=ok; import matplotlib=ok; import numpy=ok; import yaml=ok;
#             import pptx(-PIL)=FAIL; import matplotlib(-numpy)=FAIL; import matplotlib(-PIL)=FAIL;
#             import PIL(-pptx)=ok
# scenarios=8 result_written=5 full=5 honest_partial=0 crash=3 silent=0        exit=0
```

| 场景 | 屏蔽 | exit | `result.json` | status | 剩余产物 | 预览 | 重建图文件 | uncertainty | 判定 |
|-|-|-|-|-|-|-|-|-|-|
| S0 基线 | （无） | 0 | 是 | completed | 13 | 7 | 2 | 1 | full success |
| S1 | `pptx` | 1 | **否** | — | **0** | 0 | 0 | 0 | crash（导入期失败） |
| S2 | `PIL` | 1 | **否** | — | **0** | 0 | 0 | 0 | crash（导入期失败） |
| S3 | `matplotlib` | 0 | 是 | completed | 11 | 7 | **0** | 2 | full success（降级被记录） |
| S4 | `numpy` | 0 | 是 | completed | 11 | 7 | **0** | 2 | full success（降级被记录） |
| S5 | `yaml` | 0 | 是 | completed | 13 | 7 | 2 | 1 | 与基线一致 |
| S6 | `pptx,PIL` | 1 | **否** | — | **0** | 0 | 0 | 0 | crash（导入期失败） |
| S7 | PATH 剥离 soffice | 0 | 是 | completed | 13 | 7 | 2 | 1 | 与基线一致 |

关键细节（从 `degrade_matrix.json` 抄出）：

- S1/S2/S6 的失败导入原文：`ModuleNotFoundError: No module named 'pptx' (blocked by degrade_probe)`
  / `... No module named 'PIL' ...`，输出目录**完全为空**（连 `result.json` 都没有）→
  **响亮失败**，不是静默降级；
- S3 的 `uncertainty` 第 2 条：`reconstructed chart skipped: matplotlib missing: No module named
  'matplotlib' (blocked by degrade_probe)`；`charts` 记录仍在（1 条）但 `chart-Fig_1.png/svg`
  不落盘 → 产物从 13 降到 11；
- S4 同理，原因写的是 `No module named 'numpy'`（matplotlib 因 numpy 缺失而失效）；
- 依赖关系实测：`import pptx`（屏蔽 PIL）**失败**、`import matplotlib`（屏蔽 numpy / PIL）**失败**、
  `import PIL`（屏蔽 pptx）**成功** ⇒ 硬依赖应表述为"python-pptx（含其 Pillow 依赖）"；
- 模块可导入性（12 个模块）：屏蔽 `pptx` 或 `PIL` 时只剩 **7/12**
  （`deckgen` / `ooxml_kit` / `preview` / `export_check` / `main` 全部失败）；
  其余场景 **12/12**；
- LibreOffice 静态扫描：11 个管线脚本命中 3 处（`main.py:314`、`preview.py:6`、`preview.py:11`，
  全是注释/字符串），**0 处调用**；配合 S7 与 S0 行为一致 ⇒ "有无 LibreOffice 不影响产物"；
- 探针耗时：8 个场景 + 9 个依赖探测约 **32 s**。

### 探针的负路径与自检

```bash
python "$SKILL_DIR/scripts/degrade_probe.py" --out "$TMP/n1" --only S0-baseline \
  --entry "$TMP/_writes_nothing.py"      # 基线对照都失败 → exit 3（探针环境有问题）
python "$SKILL_DIR/scripts/degrade_probe.py" --out "$TMP/n2" --only ZZ          # exit 2
python "$SKILL_DIR/scripts/degrade_probe.py" --out "$TMP/n3" --case "$TMP/nope.json"  # exit 2
python "$SKILL_DIR/scripts/degrade_probe.py" --out "$TMP/n4" \
  --only S1-no-pptx,S3-no-matplotlib,S7-no-soffice                              # 子集 → exit 0
```

实测：`baseline_control_fail exit=3`、`no_scenario exit=2`、`bad_case exit=2`、`subset exit=0`。

## T5 环境前置（CP5）快跑 —— 约 10 s

```bash
python "$SKILL_DIR/scripts/degrade_probe.py" --out "$TMP/cp5" \
  --only S0-baseline,S2-no-PIL,S3-no-matplotlib
# S0 full success / S2 crash(no result.json) / S3 full success(重建图不落盘)
# ⇒ 结论：Pillow 属于硬依赖；matplotlib 缺失可以继续但必须记录
```

## T6 两道交付门 —— 通过（均 exit 0）

```bash
python "$SKILL_DIR/scripts/export_check.py" --result "$TMP/out/result.json" \
  --out-dir "$TMP/out" --case "$SKILL_DIR/examples/case.json"
# {"valid": true, "errors": [], "warnings": [], "status": "completed"}
python "$SKILL_DIR/scripts/check_contract.py" --result "$TMP/out/result.json" \
  --contract "$SKILL_DIR/references/OUTPUT_CONTRACT.md" --case "$SKILL_DIR/examples/case.json"
# {"valid": true, "fields_contracted": 19, "fields_present": 19, "missing": [], "present_but_null": []}
```

## T7 主流程负路径 —— 退出码语义符合承诺

```bash
python "$SKILL_DIR/scripts/main.py" --case "$TMP/nope/case.json" --out "$TMP/x"   # exit 3
python "$SKILL_DIR/scripts/spec_lint.py" --spec "$TMP/broken-spec.json"           # exit 1（列出 5 条问题）
```

补充实测（工具级降级 vs 入口级崩溃的区别）：在屏蔽 `pptx` 的子进程里跑
`make_template.py`（把 `scripts/` 放进 `PYTHONPATH`，因为除 `main.py` 外的入口按
`python "$SKILL_DIR/scripts/x.py"` 方式设计）实测 **exit=2**，报告里如实写着
`{"status": "unavailable", "errors": ["python-pptx not importable: No module named 'pptx' (blocked)"]}`，
且**不产出任何 `.pptx`**。⇒ 工具级入口会优雅降级（退出码 2 = 后端不可用），
而端到端入口 `main.py` 会在**导入期**就失败（exit 1、0 产物）——两者不可混为一谈。

## T8 与既有版本的一致性（能力未丢）

```bash
# 逐文件 sha256 对拍（基线包 scripts/ vs 本包 scripts/）
# 实测：11 个基线脚本 11/11 逐字节相同，0 不同、0 缺失；本包只新增 degrade_probe.py
```

整包对拍（相对基线）：24 个文件逐字节未变；改动 6 个 = `GITHUB_URL.txt`（本轮链接）、
`SKILL.md` / `README.md` / `TEST.md`（按本版轴重写）、`references/RUBRIC_MAP.md` /
`references/failure-modes.md`（在既有表格对应行内补入本版落点与依赖缺失实测，未删改原有条目）；
新增 4 个文件 = `scripts/degrade_probe.py` + `references/DEGRADE-MATRIX.md` +
`references/degrade-matrix-data.json`（+ 本文件）。

> 合规验收（`validate_pkg.py`）由主对话独立复跑：包内不跑脚本，避免留下 `__pycache__`。
