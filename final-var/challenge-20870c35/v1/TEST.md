# TEST.md — 本地实测记录（challenge-20870c35 · v1 决策显性化版）

- 测试时间：2026-11-22 18:05–18:20 +08（Asia/Shanghai）
- 测试机：Windows（Git Bash / MSYS2），Python 3.13.9（Anaconda）
- 被测对象：本目录全部文件（14 个既有脚本 + **本版新增 `scripts/check_status_matrix.py`**）
- 测试方式：把包**复制到包外临时目录**（本机为系统临时盘下的纯 ASCII 目录）再跑，
  **不在提交目录里跑任何脚本**——否则会生成 `__pycache__`，平台预检直接判定不合规
- 覆盖：语法编译 / 合成输入 / 主流程 smoke / **状态矩阵正例与负例** / 缺失材料降级 /
  缺 `python-pptx` 降级 / 双跑确定性 / 全链路自检与包约束

## 0. 环境与依赖

```
$ python --version
Python 3.13.9
$ python -c "import pptx,PIL,pypdf; print(pptx.__version__, PIL.__version__, pypdf.__version__)"
1.0.2 12.3.0 6.14.2
```

必需依赖只有 `python-pptx` + `Pillow`；`pypdf`/`PyPDF2` 为 PDF 可选解析器；
`scripts/make_synthetic_inputs.py` 零第三方依赖。缺任何一个都不崩（见 §5）。

## 1. 语法检查（T1）

```
$ cd <pkg>/scripts && for f in *.py; do python -m py_compile "$f" || exit 1; done
COMPILE_FAIL=0            # 15/15 脚本全部通过（含本版新增的 check_status_matrix.py），无 FAIL
```

## 2. 合成输入再生成（T0）

```
$ python scripts/make_synthetic_inputs.py
[synthetic-inputs] written=['dataset_card.pdf', 'fig2.png']
[synthetic-inputs] note=SYNTHETIC EXAMPLE - generated placeholder, not real research data
exit=0
```

PDF 为手工构造的最小 PDF（可被 pypdf 抽取文本），PNG 为纯几何示意图（带 `SYNTHETIC` 标注）。

## 3. 主流程 smoke（T2 · 验收形态）

```
$ python scripts/main.py --case examples/case.json --out <W>/out-A
[plan] 12 pages, narrative=group_meeting, audience=familiar, P-gates valid=True
[deck] 12 slides, mode=built-in-theme, verify valid=True
[preview] wrote 13 preview files (PIL simulation)
[done] status=completed deck_ok=True preview_ok=True plan_gates=True evidence_audit=True validate_valid=True contract_valid=True
exit=0
```

## 4. ★ 状态矩阵检查器（T3 正例 / T4 负例）

**(T3) 对正常产物：13 条规则全过，退出码 0**

```
$ python scripts/check_status_matrix.py <W>/out-A
status-matrix check of .../out-A (status=completed)
  [ok] C1 case_id 非空 · C2 pages 非空 · C3 len(pages)==slide_count（12=12）
  [ok] C4 内容页有 locator + quote（缺定位的页=无）· C5 无孤儿引用 · C6 uncertainty 三要素齐全
  [ok] S1 deck 存在且 deck_audit.valid（deck_slides=12 pages=12）
  [ok] S2 plan_gates.valid=True errors=[] · S3 evidence.valid=True（content_pages=10 ok_pages=10 errors=0）
  [ok] S4 全部文本材料已解析 · S5 previews cover+manifest 存在 · S6 无 deck_limitation · S7 无降级条目
=> CONSISTENT (13 rules checked, 0 violations)
exit=0
```

**(T4) 负例：把 `status=completed` 的 result.json 改出矛盾（加 `deck_limitation`）后**

```
$ python scripts/check_status_matrix.py <W>/tamper.json
  [XX] S6 completed ⇒ 无 deck_limitation    deck_limitation='tampered'
=> INCONSISTENT (13 rules checked, 1 violations)
exit=1
```

⇒ 检查器**能真的抓出状态与内容矛盾**，不是恒真脚本；正常产物仍退出 0。

## 5. 降级分支（T5 / T6）

**(T5) 把 `case.json` 复制到材料目录之外（4 个材料全部找不到）**

```
$ python scripts/main.py --case <W>/case-missing.json --out <W>/out-M --quiet
status=partial pages=12 deck=True validate_valid=True contract_valid=True      # exit=0
sources = [(paper_extract.md, missing, False), (figures.md, missing, False),
           (dataset_card.pdf, missing, False), (not_on_disk.pdf, missing, False)]
uncertainty = 7 条
$ python scripts/check_status_matrix.py <W>/out-M --quiet ; exit=0            # 状态自洽
```

⇒ 对应 **B-M1 / D1**：材料缺失不崩、如实标 `kind=missing`、状态降 `partial`、状态仍自洽。

**(T6) 遮蔽 `python-pptx`（`PYTHONPATH` 注入一个 import 即抛错的 `pptx.py`）**

```
$ PYTHONPATH=<W>/shim python scripts/main.py --case examples/case.json --out <W>/out-X --quiet
[deck] SKIPPED (dependency missing): python-pptx 不可用（pptx blocked for the degradation test）
status=partial pages=12 deck=False validate_valid=True contract_valid=True      # exit=0
editable_deck=None   deck_limitation=python-pptx 不可用（…）
$ python scripts/check_status_matrix.py <W>/out-X --quiet ; exit=0             # 状态自洽
```

⇒ 对应 **B-D1 / D15**：缺 deck 依赖时**命令仍返回 0**，页计划与状态如实降级，且不触发状态矛盾。

## 6. 双跑确定性（T7）

同一条命令写到两个目录，逐项比对：

| 文件 | A vs B |
|-|-|
| `evidence_map.json` / `plan_gates.json` / `deck_audit.json` / `evidence_audit.json` | **逐字节相同** |
| `previews/*.png`（12 张） | **逐字节相同（12/12）** |
| `previews/preview_manifest.json` | 仅生成时间不同（记录性字段） |
| `talk_plan.json` / `result.json` | 内容相同，仅 `generated_at` / `change_records[].at` 不同 |

内容投影 sha（剔除记录性时间戳）A/B 完全一致，与基线一致：

```
plan_sha16                   = 1dcff19cb479cba9ada62c9ddab260135bf12f5c22aa0e39a3f569b151336120
evidence_map_sha16           = 6a5d2847678c36dcb38e1f186f00a87e90d8a19af46117b00246247941d86214
deck 规范化 sha16            = 6d17df3f4c09de46490fb81ddb15b2bb03dd053dac1677b76f19f7e1c6dfc27e
```

⇒ 对应 **D19**：差异只是记录性时间戳，探针剔除后逐位一致。

## 7. 全链路自检与包约束（T8）

```
$ python scripts/selftest.py <W>/out-A --package-check <pkg>
"summary": "checks=6 errors=0"
"summary": "text=41 total_bytes=392755 max_file=42426"     # 包约束审计
exit=0
```

- `validate`：checks **10/10 ok**，`errors=[]`，`warnings=[]`
- `contract_check`：`declared=16 missing=0 wrong_type=0`（对 `case.json + task.md`）
- `audit.gates`：G1–G9 = true，G10 = null（设计如此，包约束由 `selftest --package-check` 执行）
- `audit.plan_gates`：P1–P8 全过（`P3 pages=12 target=12`）
- `audit.evidence.summary`：`{pages_total:12, content_pages:10, ok_pages:10, errors:0, derived_pages:0, unavailable_text:0}`
- `audit.deck`：`valid=true`，12 张幻灯片，每页 `notes_nonempty=true`

## 8. 提交资源形态（不进运行期）

```
提交目录（不含运行产物）: 41 个文件；扩展名 = .md / .py / .json / .txt（全部在允许的七种之内）
最大单文件: examples/output/result.example.json = 42,426 B（上限 500KB）
无符号链接；无 __pycache__/*.pyc（实测：所有脚本都在包外副本上运行）
```

> ⚠ 上表 §7 的 `text=41 total_bytes=392755` 是**包副本含运行期产物时**的数字；
> 提交目录本身不含二进制，实际更小。

## 9. 已知限制

- 预览是 Pillow 模拟渲染（带水印），**不是** Office 真实栅格化；
- `result.audit.gates.G10` 设计为 `null`（由 `selftest --package-check` 执行），非缺陷；
- 证据定位是行级/章节级近似锚点，源材料更新后需按引文复核；
- `check_status_matrix.py` 只判"文件内部自洽"，不判"内容是否正确"——正确性由
  `validate_result` / `evidence_audit` / `verify_deck` 分工负责；
- 平台 3 案例 × 3 复跑由平台执行，本节只给出本机可复现性证据。
