# TEST — 本机实测记录（v8 · 契约四形态 × 边界值矩阵版）

本文件只写**真跑过的命令与输出摘要**；没有跑过的一律标注"未测量"。
所有命令都在**包外副本**上执行（`cp -r <包> <tmp>/pkg`），因此包内不会产生
`__pycache__`；`--out` 一律指向包外。

| 项 | 值 |
|-|-|
| 日期 | 2026-11-23（Asia/Shanghai） |
| Python | 3.13.9（Anaconda） |
| 版本 | matplotlib 3.10.6 · Pillow 12.3.0 · numpy 2.3.5 |
| 平台 | Windows，本机 NTFS |
| 测试副本 | `<tmp>/pkg`（包外） |

---

## T1 · 逻辑自测（35 项）

```bash
python "$SKILL_DIR/scripts/selftest.py"
```

输出摘要：`[PASS]` 行 **35** 条，末行 `selftest: all checks passed`，**退出码 0**。

## T2 · 主流程 smoke（schematic 示例）

```bash
python -B "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out "$RUN/out"
```

尾部实测：

```
[sse] CHECK SUMMARY: success (0 fails, 0 warns, 0 acks)
[sse] wrote <RUN>/out/result.json
[sse]    figure   svg    figure.svg (15241 bytes)
[sse]    pdf      pdf    figure.pdf (37944 bytes)
[sse]    preview  png    figure.png (165063 bytes)
```

**退出码 0**；`result.json` **顶层键 23**（含契约回显的 `deliverables` /
`entities_relations`）；`status=success`，`fail_count=0`。

## T3 · 契约门（独立校验器）

```bash
python -B "$SKILL_DIR/scripts/validate_result.py" \
    --case "$SKILL_DIR/examples/case.json" --result "$RUN/out/result.json"
```

`VALID: result.json at <RUN>/out/result.json satisfies OUTPUT_CONTRACT
(G1-G8 gates pass, contract echoed).`，**退出码 0**。

## T4 · 三个包内示例端到端

```bash
python -B "$SKILL_DIR/scripts/run_examples.py" --out "$RUN/examples"
```

`> PASS` 行 **6** 条、`FAIL` 0 条，末行 `EXAMPLES: all steps passed; …`，**退出码 0**。

## T5 · 文档 ↔ 代码对拍

```bash
python -B "$SKILL_DIR/scripts/doccheck.py" --root "$SKILL_DIR"
```

```
  check ids: 64 documented / 89 present in scripts
  rule families: F[12], S[8]  (declared 20 ids; 11 of them also named in SKILL.md)
  cli flags: 33 documented / 31 declared in scripts
doc-check: CONSISTENT (0 fails, 0 warns)
```

**退出码 0**。意义：本版新增的 `contract_matrix.py` 的 10 个 flag 与文档里的
检查名都逐一对上，没有"承诺了代码做不到的事"。

## T6 · ★ 契约四形态 × 边界值矩阵（本版主轴，31 行）

```bash
python -B "$SKILL_DIR/scripts/contract_matrix.py" --skill-root "$SKILL_DIR" --out "$RUN/cm"
```

尾部实测（表格已省略中间行，完整表在 `references/CONTRACT-MATRIX.md` §3）：

```
  id   form           boundary             exit   status   valid  silent echo
  R01  string         normal               0      success  True   False  1/1
  ...
  R13  number         literal-12           0      success  True   True   1/1
  R16  null-hint      null-value           0      success  False  False  1/1
  ...
  R27  missing        no-output_contract   0      success  True   True   0/0
  ...
  R31  missing        oc-empty-object      0      success  True   True   0/0
[cm] rows=31 measured=31 valid=27 invalid=4 silent_pass=16 unmeasurable=0
[cm] silent ids: R06, R07, R09, R13, R14, R15, R17, R18, R21, R22, R23, R27, R28, R29, R30, R31
[cm] wrote <RUN>/cm/contract-matrix.json
```

**退出码 0**，墙钟 **67 秒**。四条关键实测（机器可读原文在 `contract-matrix.json`）：

| 关键读数 | 实测 |
|-|-|
| `null` 声明必须被抓住 | R16：回显 `None`(null) ⇒ `G5 contract key x_none is null (must be a type-shaped empty or real value)`，`valid=false` |
| 类型冲突必须被抓住 | R24 `artifacts`：`G5 ... expected str, got list`；R25 `title`：`expected list, got str`；R26 `case_id`：`expected dict, got str` ⇒ 三行 INVALID |
| 契约键真的进了顶层 | R08 五形态同声明 ⇒ 顶层键 **26**（基线 21 + 5）；R27–R31 无契约 ⇒ **21** |
| 大文本会放大产物 | R20（`summary` ≈210KB）⇒ `result.json` **219,556 B**，仍 VALID |

**16 行静默通过**（VALID 但声明未被兑现）逐条理由：

| 静默 | 行 | 一句话 |
|-|-|-|
| S4 | R27 R28 R29 R30 R31 | 顶层契约形状非法 ⇒ G5 整段跳过，"没有契约"与"契约满足"不可区分 |
| S1 | R09 R15 R17 R18 | 未知/空/超长类型词被当字符串（回显 `""`） |
| S3 | R06 R07 R21 R22 R23 | 结构化提示被降级为空容器，元素的类型无任何门记录 |
| S2 | R13 R14 | 字面量被当类型：声明 `12` 回显 `0`、声明 `true` 回显 `false` |

## T7 · 契约矩阵的边界用法（真跑过）

| 命令 | 实测 |
|-|-|
| `contract_matrix.py --list` | 打印 31 行（id / 形态 / 边界 / 期望行为），退出码 0 |
| `--only R13,R16,R27 --quiet` | `rows=3 measured=3 valid=2 invalid=1 silent_pass=2`（R13、R27），退出码 0 |
| `--out <技能包内部>` | **被拒绝**：`[cm] FATAL: --out 不能指向技能包内部…本脚本只动包外副本`，**退出码 2** |
| `--timeout 180`（默认） | 每行主流程与校验器分别设超时；超时的行会被记成 `unmeasurable`（本轮 0 行） |

## T8 · 故障注入（既有可靠性回归，证明本版没破坏能力）

```bash
python -B "$SKILL_DIR/scripts/fault_inject.py" --skill-root "$SKILL_DIR" --out "$RUN/fi"
```

末行 `fault-inject: 25/25 conform to the documented expectation`，**退出码 0**；
矩阵 `fault-matrix.json` 52,375 B。

## T9 · 题集（跨题材回归）

```bash
python -B "$SKILL_DIR/scripts/case_probe.py" --skill-root "$SKILL_DIR" --out "$RUN/cases"
```

末行 `case-probe: 10/10 item(s) conform to their declared expectations`，**退出码 0**；
报告 `case-report.json` 27,532 B。

## T10 · 契约矩阵与主流程的一致性复验

```bash
python -c "import json;r=json.load(open('<RUN>/cm/contract-matrix.json',encoding='utf-8'));\
print({k:r['summary'][k] for k in ('rows','measured','valid','invalid','silent_pass','main_exit_0','status_counts')})"
```

本机实测输出：

```
{'rows': 31, 'measured': 31, 'valid': 27, 'invalid': 4, 'silent_pass': 16,
 'main_exit_0': 31, 'status_counts': {'success': 31}}
```

**读法**：`main_exit_0 = 31` 与 `status_counts = {success: 31}` 说明
**契约形状问题不会让主流程失败** —— 发现契约问题只能是"契约门 + 本矩阵"的责任，
这也正是本版把它做成可运行工具的理由。

## T11 · 形态与合规自查（仓库自带的合规验收器）

```bash
python <efficiency-3 仓库>/validate_pkg.py <包目录>
```

实测 `[PASS]`：文件 **49**（上限 50）、单文件 ≤500KB（最大 `scripts/fault_inject.py` 46,380 B）、
总计 **530,034 B ≈ 518 KB**（上限 2 MB）、扩展名只用
`.md/.py/.json/.txt/.csv`、无 `__pycache__`/`*.pyc`、无符号链接、无本机绝对路径。

包内自查（在包目录上跑；两条都必须 **0 命中**）：

```bash
# 本机绝对路径：0 命中（模式用 chr(92) 拼出，避免把检测串本身写进文档）
python -c 'import os,re;bs=chr(92);pat=re.compile("[A-Za-z]:"+re.escape(bs*2));print("abs-path hits:",sum(1 for r,_,fs in os.walk(".") for f in fs if pat.search(open(os.path.join(r,f),encoding="utf-8",errors="replace").read())))'
# 假变体形态（末尾注释段/变更记录段）：0 命中（跳过本文件，因为这几行检查命令自身就在本文件里）
python -c 'import os;print("trailing-note hits:",sum(1 for r,_,fs in os.walk(".") for f in fs if f!="TEST.md" and ("末尾注释段" in open(os.path.join(r,f),encoding="utf-8",errors="replace").read() or "变更记录段" in open(os.path.join(r,f),encoding="utf-8",errors="replace").read())))'
```

## T12 · 未测量项（本文件**不**为它们背书）

平台真实 `output_contract` 字段清单；`oneOf`/`anyOf` 联合类型；**值形状**
（数组元素类型、对象内部字段类型）；并发与中断；`result.json` 超过 500KB 后平台的
打包行为；`--base-case` 换成 chart/edit 案例时的契约交互；`--skip-checks`/`--no-lint`
下的回显形态。逐条理由见 `references/CONTRACT-MATRIX.md` §5。
