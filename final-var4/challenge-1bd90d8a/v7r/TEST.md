# TEST.md — v7（字节级可复现轴）真机实测记录

> 所有命令都在**包外**的临时副本上跑（复制到系统临时目录后再执行），
> 包内不产生 `__pycache__`。下面每条都给出**命令 + 真实输出摘要**。

环境：Windows / Python 3.13.9 / Pillow 12.3.0。

---

## T1 语法编译（10 个既有入口 + 本版新增入口）

```bash
python -m py_compile scripts/*.py
```

结果：**exit 0，11/11 脚本编译通过**（`chartkit` `check_contract` `cjkfont` `determinism`
`extract` `figcheck` `main` `mapcheck` `spec_lint` `svgtext` `verify_rerun`）。

## T2 端到端冒烟（包外副本）

```bash
cp -r v7 /tmp/v7 && cd /tmp/v7
python scripts/main.py --case examples/case.json --out /tmp/out --work /tmp/work
```

输出摘要（逐字）：

```
[main] case_id=example-science-figure-01 status=completed figures=['fig-01', 'fig-02'] failed=[]
[main] gates: G1=OK G2=OK G3=OK G4=OK G5=OK G6=OK G7=OK G8=OK all_pass=OK
EXIT=0
```

产物 11 个：`figure-fig-01/02.svg|.png|.pdf`（6）、`data_manifest.json`、`validation.json`、
`mapcheck_report.json`、`figcheck_report.json`、`result.json`。
`result.json` 顶层 **29 键**，`status=completed`，`gates.all_pass=true`，`outputs` 6 项。

## T3 既有入口逐个跑（能力未丢验证）

| 命令 | 实测 |
|-|-|
| `python scripts/check_contract.py --result /tmp/out/result.json --case examples/case.json` | `SUMMARY: PASS (required=18 missing=0 null=0 contract_missing=0)`，exit 0 |
| `python scripts/figcheck.py --dir /tmp/out --case examples/case.json --json` | `all_pass=True`，`G1..G8` 全 True，exit 0 |
| `python scripts/mapcheck.py --dir /tmp/out --case examples/case.json --json` | `all_pass=True`，`summary={'checked': 121, 'mismatches': 0, 'unmatched': 0}`，exit 0 |
| `python scripts/spec_lint.py --spec examples/case.json --case examples/case.json --json` | `{"valid": true, "counts": {"figures": 2, "errors": 0, "warnings": 0}}`，exit 0 |
| `python scripts/extract.py --case examples/case.json --out /tmp/extract --json` | 输出 `tables[]`（`data.csv` 列画像），exit 0 |
| `python scripts/verify_rerun.py --record-only --dir /tmp/out` | 逐文件 sha256 列表（`data_manifest.json: a40ab7d3…`），exit 0 |
| `python scripts/verify_rerun.py --case examples/case.json --out /tmp/out --rerun-dir /tmp/rerun` | 见 T5 |

## T4 ★ 本版新增：字节级可复现实测（isolated，5 次）

```bash
python scripts/determinism.py --case examples/case.json --runs 5 \
    --seeds 0,1,12345,7,99 --mode isolated \
    --workroot /tmp/iso --out /tmp/iso/determinism_report.json
```

真实输出（尾部）：

```
   [     SAME] data_manifest.json
   [NORM-SAME] figcheck_report.json
   [NORM-SAME] figure-fig-01.pdf
   [     SAME] figure-fig-01.png
   [     SAME] figure-fig-01.svg
   [NORM-SAME] figure-fig-02.pdf
   [     SAME] figure-fig-02.png
   [     SAME] figure-fig-02.svg
   [NORM-SAME] mapcheck_report.json
   [NORM-SAME] result.json
   [     SAME] validation.json
   [volatile] figcheck_report.json.dir ×4  class=run_root_path
   [volatile] mapcheck_report.json.dir ×4  class=run_root_path
   [volatile] result.json.artifacts_sha256.figure-fig-01.pdf ×4  class=self_reference_hash
   [volatile] result.json.artifacts_sha256.figure-fig-02.pdf ×4  class=self_reference_hash
   [volatile] result.json.change_records[*].ts ×24  class=timestamp
   [volatile] result.json.steps[*].ts ×28  class=timestamp
[determinism] identical=False normalized_identical=True => exit 2
```

**exit 2**：字节级不同但归一化后完全一致（阶梯 2）。5 次运行 `exit=[0,0,0,0,0]`、
`status=completed` ×5、顶层 `29` 键 ×5；cwd 轮转
`['run-dir','system-temp','case-dir','skill-root','run-dir']`；
`PYTHONHASHSEED=[0,1,12345,7,99]`；单次运行 1.26–1.45 秒（均值 1.34 秒），整轮 6.97 秒。

## T5 既有确定性口径（对照，说明两把尺子互补）

```bash
python scripts/verify_rerun.py --case examples/case.json --out /tmp/out --rerun-dir /tmp/rerun
```

实测输出：`SUMMARY: DETERMINISTIC (identical=9 differ=0 missing=0)`，exit 0；
其中 `figure-fig-02.pdf: SAME (PDF 仅内嵌日期差异)`、`result.json: SAME (ts/自哈希/manual 归一化后一致)`。

`verify_rerun.py` 只对比 `result.json` 登记的那几个产物，并把 `result.json` 的时间戳与
PDF 的内嵌日期归一化掉，因此它报 `DETERMINISTIC`。`determinism.py` 的尺子更严：
它对比**输出目录内全部文件**、跑跨进程/跨 cwd/跨哈希种子、并逐字段列出差异来源。
两者结论不矛盾 —— 前者回答「同一台机器重跑会不会得到同一张图」，
后者回答「哪些字节不稳定、为什么、怎么稳定」。

## T6 对照实验（inplace，把「输出目录」变量排除）

```bash
python scripts/determinism.py --case examples/case.json --runs 3 --mode inplace \
    --workroot /tmp/inp --out /tmp/inp/determinism_inplace_report.json
```

实测：**exit 2**；逐字节相同 8/11；`volatile_classes = {"self_reference_hash": 2, "timestamp": 2}` ——
`run_root_path` 这一类**整体消失**，证明 `figcheck_report.json` / `mapcheck_report.json`
的唯一不稳定来源就是 `dir` 字段。

## T7 边界与异常

| 用例 | 命令 | 实测 |
|-|-|-|
| `--runs 1` | `determinism.py --case … --runs 1` | 拒绝：`--runs 至少为 2（1 次无法判定确定性）`，exit 1 |
| 案例不存在 | `determinism.py --case nope.json` | `FATAL FileNotFoundError`，exit 1 |
| `--main` 指向别处 | `determinism.py --main <另一个包的 main.py>` | 正常跑，报告里 `main` 字段指过去（可用于同口径对照） |
| 缺 Pillow | 见 `references/DEGRADE-MATRIX.md`（另一路探针实测） | SVG 仍在，PNG/PDF 与 figcheck 报告缺失，`result.json` 降级为 6 键 |

## T8 报告可移植性与合规

```bash
# validate_pkg.py 用的就是同一组本机路径标记（盘符前缀 / 用户目录 / UNC 前缀），
# 把包与报告一起扫一遍：
python validate_pkg.py .
```

实测：报告与文档在**同一组标记**下 0 命中 —— 本机绝对路径已被替换成
`<WORKSPACE>` / `<CASEDIR>` / `<SKILL_DIR>` / `<TMP>` / `<ABS>` 占位符。

```bash
python validate_pkg.py <本包目录>
```

见提交前的合规验收记录（`[PASS]`，0 条 FAIL）。
