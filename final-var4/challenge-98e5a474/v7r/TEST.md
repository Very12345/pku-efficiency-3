# TEST — 本机实测记录（v7 · 确定性与字节级可复现版）

本文件只写**真跑过的命令与输出摘要**；没有跑过的一律标注"未测量"。
所有命令都在**包外副本**上执行（`cp -r <包> <tmp>/pkg`），因此包内不会产生
`__pycache__`；`--out` 一律指向包外。

| 项 | 值 |
|-|-|
| 日期 | 2026-11-23（Asia/Shanghai） |
| Python | 3.13.9（Anaconda） |
| 版本 | matplotlib 3.10.6 · Pillow 12.3.0 · numpy 2.3.5（另有 reportlab / lxml / fitz / pypdf 可用） |
| 平台 | Windows，本机 NTFS |
| 测试副本 | `<tmp>/pkg`（包外） |

---

## T1 · 逻辑自测（35 项）

```bash
python "$SKILL_DIR/scripts/selftest.py"
```

输出摘要：`[PASS]` 行 **35** 条，最后一行 `selftest: all checks passed`，**退出码 0**。
其中与确定性相关的两项：
`[PASS] validate_result: missing artifacts rejected`、
`[PASS] checklist: CP1..CP5 present`。

## T2 · 主流程 smoke（schematic 示例）

```bash
python -B "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out "$RUN/out"
```

输出摘要（尾部）：

```
[sse]    [check] traceability.entities      ok   6/6 entities carry source+evidence (100.0%)
[sse]    [check] traceability.relations     ok   5/5 relations carry source (100.0%)
[sse] CHECK SUMMARY: success (0 fails, 0 warns, 0 acks)
[sse] wrote <RUN>/out/result.json
[sse]    figure   svg    figure.svg (15241 bytes)
[sse]    pdf      pdf    figure.pdf (37944 bytes)
[sse]    preview  png    figure.png (165063 bytes)
```

- **退出码 0**；`result.json` **顶层键 23 个**（含契约回显的
  `deliverables` / `entities_relations`）：
  `artifacts, case_id, change_records, data_mapping, deliverables, determinism,
  entities_relations, evidence, figure_type, generated_at, generator, legend_mapping,
  main_result, skill, sources, status, status_notes, task_summary, title, tool_versions,
  uncertainty, verification, workorder`；
- `status=success`，`verification.checks.fail_count=0`，
  artifacts = `figure(svg) / preview(png) / pdf(pdf)`；
- `--case` 传**目录**也成立（`examples` → `examples/case.json`），这是文档里写的用法。

## T3 · 契约门（独立校验器）

```bash
python -B "$SKILL_DIR/scripts/validate_result.py" \
    --case "$SKILL_DIR/examples/case.json" --result "$RUN/out/result.json"
```

输出：`VALID: result.json at <RUN>/out/result.json satisfies OUTPUT_CONTRACT
(G1-G8 gates pass, contract echoed).`，**退出码 0**。

## T4 · 三个包内示例端到端

```bash
python -B "$SKILL_DIR/scripts/run_examples.py" --out "$RUN/examples"
```

输出摘要：`> PASS` 行 **6** 条（schematic / chart / edit 各两步），`FAIL` 0 条，
三份 result.json 全部 VALID，末行
`EXAMPLES: all steps passed; artifacts under <RUN>/examples`，**退出码 0**。

## T5 · 文档 ↔ 代码对拍

```bash
python -B "$SKILL_DIR/scripts/doccheck.py" --root "$SKILL_DIR"
```

```
  check ids: 64 documented / 91 present in scripts
  rule families: F[12], S[8]  (declared 20 ids; 11 of them also named in SKILL.md)
  cli flags: 33 documented / 31 declared in scripts
doc-check: CONSISTENT (0 fails, 0 warns)
```

**退出码 0**。意义：SKILL/README/TEST 里点名的每个检查名都能在 `scripts/` 找到、
每个 `--flag` 都真实存在（含本版新增的 `determinism.py` 的 10 个 flag）——
这是"文档没有承诺代码做不到的事"的机器判据。

## T6 · ★ 确定性矩阵（本版主轴，默认 6 次）

```bash
python -B "$SKILL_DIR/scripts/determinism.py" --skill-root "$SKILL_DIR" --out "$RUN/det"
```

输出摘要（表格 + 结论行）：

```
  file                         raw    nat-raw  nat-norm  all-norm
  figure.pdf                   DIFF   DIFF     same      same  (2e0bc44431cd)
  figure.png                   same   same     same      same  (71fb5f387258)
  figure.svg                   same   same     same      same  (24eab86e4c29)
  layout.json                  same   same     same      same  (932d9d314b1b)
  manifest.validated.json      same   same     same      same  (3fee6c0cba90)
  result.json                  DIFF   DIFF     same      same  (5b1d90365bcf)
[det] identical(raw)=False natural(raw)=False natural(norm)=True stabilized-pair(norm)=True all(norm)=True volatile=4 unclassified=0
[det] verdict: BYTE-IDENTICAL-AFTER-DOCUMENTED-NORMALISATION：差异只剩被逐条点名的故意不稳定字段（时间戳/绝对路径），其余字节全等
[det] wrote <RUN>/det/determinism_report.json
```

**退出码 0**。6 次运行的实测明细（`determinism_report.json`）：

| run | profile | `PYTHONHASHSEED` | `SOURCE_DATE_EPOCH` | exit | status | 墙钟 | `figure.pdf` 的 `/CreationDate` |
|-|-|-|-|-|-|-|-|
| 1 | natural | `0` | 未设 | 0 | success | 1.26 s | `D:20261123191521+08'00'` |
| 2 | natural | `0` | 未设 | 0 | success | 1.27 s | `D:20261123191522+08'00'` |
| 3 | natural | `1` | 未设 | 0 | success | 1.29 s | `D:20261123191523+08'00'` |
| 4 | natural | 未设（随机） | 未设 | 0 | success | 1.13 s | `D:20261123191524+08'00'` |
| 5 | stabilized | 未设 | `1767225600` | 0 | success | 1.23 s | `D:20260101000000Z` |
| 6 | stabilized | `7` | `1767225600` | 0 | success | 1.38 s | `D:20260101000000Z` |

| 文件 | 字节 | sha256（前 12 位，6 次） | raw 全等 | 归一化后 |
|-|-|-|-|-|
| `figure.svg` | 15,241 | `24eab86e4c29` ×6 | ✅ | ✅ |
| `figure.png` | 165,063 | `71fb5f387258` ×6 | ✅ | ✅ |
| `layout.json` | 3,333 | `932d9d314b1b` ×6 | ✅ | ✅ |
| `manifest.validated.json` | 4,967 | `3fee6c0cba90` ×6 | ✅ | ✅ |
| `figure.pdf` | 37,944 / 37,938 | natural：`2e0bc44431cd` `5166d5fa1b9d` `47d73bf1d8f3` `c15af6d66e2c`；stabilized：`c06682bd8336` ×2 | ❌（仅 `/CreationDate`） | ✅ `6f375f3d99d4` ×6 |
| `result.json` | 9,872 | natural：`5b1d90365bcf` `ac555ab6c808` `ce856d9a9f15` `50362341e649`；stabilized：`14066c43f8d8` `74a06363e2cf` | ❌（仅 3 条 `abspath`） | ✅ `236b85c8dea5` ×6 |
| `determinism.spec_sha16` | — | `3af4c86b04dc57c1` ×6 | ✅ | ✅ |

`volatile_fields` 实测 **4 条**：`figure.pdf` 的 `/CreationDate`（byte-token）+
`result.json` 的 `/artifacts/{0,1,2}/abspath`（json-value）；
`unclassified_differences = 0`。

## T7 · 确定性的边界用法（真跑过）

| 命令 | 实测 |
|-|-|
| `determinism.py --list` | 打印 6 行运行矩阵（profile / cwd / seed / SOURCE_DATE_EPOCH），退出码 0 |
| `determinism.py --runs 2 --quiet` | 只跑 natural 组 ⇒ 结论行 `stabilized-pair(norm)=None`（不足 2 次就不下结论），`all(norm)=True`，**退出码 0** |
| `determinism.py --runs 6 --json` | 报告 21 个顶层键，stdout 可被 `json.loads` 直接消费 |
| `determinism.py --out <技能包内部>` | **被拒绝**：`[det] FATAL: --out 不能指向技能包内部…本脚本只动包外副本`，**退出码 2** |

## T8 · 稳定化复验（把结论交给第三方命令，而不是交给本文档）

```bash
# 同一输出目录重跑两次：连 abspath 都一致
python -B "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out "$RUN/same" --fixed-time 2026-01-01T00:00:00+0000
sha256sum "$RUN/same/figure.svg" "$RUN/same/figure.png" "$RUN/same/result.json"
python -B "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out "$RUN/same" --fixed-time 2026-01-01T00:00:00+0000
sha256sum "$RUN/same/figure.svg" "$RUN/same/figure.png" "$RUN/same/result.json"

# 只验 PDF：设 SOURCE_DATE_EPOCH 后两次 PDF 必须同 sha
SOURCE_DATE_EPOCH=1767225600 python -B "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out "$RUN/p1" --fixed-time 2026-01-01T00:00:00+0000
SOURCE_DATE_EPOCH=1767225600 python -B "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out "$RUN/p2" --fixed-time 2026-01-01T00:00:00+0000
sha256sum "$RUN/p1/figure.pdf" "$RUN/p2/figure.pdf"
```

实测（等价于 `determinism.py` 的 run5/run6）：两份 PDF 同为 `c06682bd8336…`；
`figure.svg` / `figure.png` 与 6 次矩阵里的 sha 相同（`24eab86e4c29…` / `71fb5f387258…`）。

**同一输出目录重跑两次的实测**（`--out` 固定为同一个目录，`--fixed-time` 固定）：

| 文件 | 第 1 次 | 第 2 次 | 结论 |
|-|-|-|-|
| `figure.svg` | `24eab86e4c29da42…` | `24eab86e4c29da42…` | 逐字节相同 |
| `figure.png` | `71fb5f387258cffb…` | `71fb5f387258cffb…` | 逐字节相同 |
| `result.json` | `9ec1dc2d82acf10e…` | `9ec1dc2d82acf10e…` | **连 `abspath` 也相同**（因为输出目录没变） |
| `figure.pdf` | `669f7702d93a8e23…` | `a3f4c1ef5f47e321…` | 只有 `/CreationDate` 不同 ⇒ 需要 `SOURCE_DATE_EPOCH`（上一段的 p1/p2 实测同 sha） |

## T9 · 故障注入（既有可靠性回归，证明本版没破坏能力）

```bash
python -B "$SKILL_DIR/scripts/fault_inject.py" --skill-root "$SKILL_DIR" --out "$RUN/fi"
```

末行：`fault-inject: 25/25 conform to the documented expectation`，**退出码 0**；
矩阵写在 `<RUN>/fi/fault-matrix.json`（52,372 B）。

## T10 · 题集（跨题材回归）

```bash
python -B "$SKILL_DIR/scripts/case_probe.py" --skill-root "$SKILL_DIR" --out "$RUN/cases"
```

末行：`case-probe: 10/10 item(s) conform to their declared expectations`，**退出码 0**。
样例（边界探针 B5，containment 未落到分组）：

```
=== [B5-containment-without-group] 边界：containment 关系未落到任何分组 ===
    actual    : exit=1 status=partial result.json=True (1.4s)
    checks    : fails=['spec_lint.spec.containment_group']
      [ok]   exit   expected=1          observed=1
      [ok]   status expected='partial'  observed='partial'
    verdict   : CONFORMS
```

## T11 · 形态与合规自查（仓库自带的合规验收器）

```bash
python <efficiency-3 仓库>/validate_pkg.py <包目录>
```

实测 `[PASS]`：文件 **49**（上限 50）、总计 **538,134 B ≈ 525 KB**（上限 2 MB）、
最大单文件 `scripts/fault_inject.py` 46,380 B（上限 500 KB）、
扩展名只用了 `.md/.py/.json/.txt/.csv`、无 `__pycache__`/`*.pyc`、无符号链接、
无本机绝对路径。

包内自查（在包目录上跑 grep 即可复现；两条都必须 **0 命中**）：

```bash
# 本机绝对路径：0 命中（模式用 chr(92) 拼出，避免把检测串本身写进文档）
python -c 'import os,re;bs=chr(92);pat=re.compile("[A-Za-z]:"+re.escape(bs*2));print("abs-path hits:",sum(1 for r,_,fs in os.walk(".") for f in fs if pat.search(open(os.path.join(r,f),encoding="utf-8",errors="replace").read())))'
# 假变体形态（末尾注释段/变更记录段）：0 命中
python -c 'import os;print("trailing-note hits:",sum(1 for r,_,fs in os.walk(".") for f in fs if f!="TEST.md" and ("末尾注释段" in open(os.path.join(r,f),encoding="utf-8",errors="replace").read() or "变更记录段" in open(os.path.join(r,f),encoding="utf-8",errors="replace").read())))'
# （跳过本文件，因为这几行检查命令的文本自身就在本文件里）
```

## T12 · 未测量项（本文件**不**为它们背书）

跨操作系统 / 跨 matplotlib 版本 / 跨文件系统的字节稳定性；chart 图型的确定性矩阵；
`--exports tiff,eps` 的 TIFF/EPS 字节稳定性；并发与中断；平台真实打分与白板。
逐条理由见 `references/DETERMINISM.md` §8。
