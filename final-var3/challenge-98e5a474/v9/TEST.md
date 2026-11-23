# TEST — 本机实测记录（v9 · 缺依赖降级链实测版）

本文件只写**真跑过的命令与输出摘要**；没有跑过的一律标注"未测量"。
所有命令都在**包外副本**上执行（`cp -r <包> <tmp>/pkg`），因此包内不会产生
`__pycache__`；`--out` 一律指向包外。

| 项 | 值 |
|-|-|
| 日期 | 2026-11-23（Asia/Shanghai） |
| Python | 3.13.9（Anaconda） |
| 版本 | matplotlib 3.10.6 · Pillow 12.3.0 · numpy 2.3.5 · PyYAML 6.0.3 · lxml · python-pptx · PyMuPDF(fitz) · pypdf · reportlab 均可用；**本机未安装 LibreOffice**（`which soffice` 为空） |
| 平台 | Windows，本机 NTFS |
| 测试副本 | `<tmp>/pkg`（包外） |

---

## T1 · 逻辑自测（35 项）

```bash
python "$SKILL_DIR/scripts/selftest.py"
```

`[PASS]` 行 **35** 条，末行 `selftest: all checks passed`，**退出码 0**。

## T2 · 主流程 smoke（schematic 示例）

```bash
python -B "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out "$RUN/out"
```

尾部实测：

```
[sse]    figure   svg    figure.svg (15241 bytes)
[sse]    pdf      pdf    figure.pdf (37944 bytes)
[sse]    preview  png    figure.png (165063 bytes)
```

**退出码 0**；`result.json` **顶层键 23**；`status=success`，`fail_count=0`。

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

## T5 · ★ 依赖降级矩阵（本版主轴，16 条探针）

```bash
python -B "$SKILL_DIR/scripts/degrade_probe.py" --skill-root "$SKILL_DIR" --out "$RUN/dg"
```

实测输出（逐条；`status` 来自 `result.json`）：

| id | 缺什么 | exit | status | tier | silent | 产物 |
|-|-|-|-|-|-|-|
| G00 | （对照） | 0 | success | full | False | figure:svg, preview:png, pdf:pdf |
| G01 | `matplotlib` | **1** | **failed** | **unavailable** | False | （无） |
| G02 | `PIL` | **1** | **failed** | **unavailable** | False | （无） |
| G03 | `numpy` | **1** | **failed** | **unavailable** | False | （无） |
| G03b | `numpy`（chart bar） | **1** | **failed** | **unavailable** | False | （无） |
| G03c | `numpy`（chart heatmap+matrix） | **1** | **failed** | **unavailable** | False | （无） |
| G04 | `yaml` | 0 | success | full | False | 三件齐全 |
| G05 | `pptx` | 0 | success | full | False | 三件齐全 |
| G06 | `lxml` | 0 | success | full | False | 三件齐全 |
| G07 | `fitz`+`pypdf`+`PyPDF2`（来源=真实 PDF） | 0 | success | full | False | 三件齐全 |
| G08 | `reportlab` | 0 | success | full | False | 三件齐全 |
| G09 | LibreOffice CLI（PATH 净化） | 0 | success | full | False | 三件齐全 |
| G10 | 全部可选依赖 | 0 | success | full | False | 三件齐全 |
| H01 | `fitz`+`pypdf`+`PyPDF2`（`pdftext.py`） | 0 | — | **degraded-usable** | False | `.txt` + `.extract.json` |
| H02 | `lxml`（`case_probe.py --only …`） | 0 | — | **degraded-usable** | False | `case-report.json` |
| H03 | `reportlab`（chart 路径） | 0 | success | full | False | 三件齐全 |

汇总行：`probes=16 tiers={"full": 9, "unavailable": 5, "degraded-usable": 2} silent=0(-)`，
**退出码 0**，总墙钟 **18.3 秒**。

**关键读数（机器可读原文在 `degrade-matrix.json`）**

| 关键读数 | 实测 |
|-|-|
| 缺关键依赖时是否留痕 | G01/G02/G03*：`exit 1`、`status=failed`、`fails=['pipeline']`、`uncertainty[0] = "missing runtime dependency: … (pip install matplotlib pillow numpy)"` —— **不是裸追栈** |
| `numpy` 的真实地位 | 三条探针一致：**传递依赖**（matplotlib 硬依赖 numpy）⇒ 缺它连 schematic 也起不来；失败原因标签仍是 `render.matplotlib`，**只有 `uncertainty` 原文写出 `injected absence: numpy`** |
| PDF 抽取降级链 | H01：`backend = "stdlib"`、`pages = 1`、**抽到 52 字**（夹具字面量长度 52） |
| 题集 XML 后端降级 | H02：`xml_backend = "stdlib"`、`conforming = 1/1`、`deviating = []` |
| "不在运行路径上"是否实测证明 | `yaml`/`pptx`/`reportlab`/LibreOffice CLI 各有独立探针，全部 `full`（产物与基线相同） |
| 静默降级 | **0**（`silent_ids = []`） |

## T6 · 依赖矩阵的边界用法（真跑过）

| 命令 | 实测 |
|-|-|
| `degrade_probe.py --list` | 打印 16 条（id / 缺什么 / 名称 / 为什么要测），退出码 0 |
| `--only G01,H01 --quiet` | `probes=2 tiers={"unavailable": 1, "degraded-usable": 1} silent=0`，退出码 0 |
| `--out <技能包内部>` | **被拒绝**：`[dg] FATAL: --out 不能指向技能包内部…本脚本只动包外副本`，**退出码 2** |
| 夹具 | heatmap 夹具由 `examples/case_chart.json` 派生（`chart_type=heatmap` + 2×3 合成 `matrix`）；PDF 夹具用**标准库**现场生成（FlateDecode 压缩，字面量 52 字符） |

## T7 · 故障注入（既有可靠性回归，证明本版没破坏能力）

```bash
python -B "$SKILL_DIR/scripts/fault_inject.py" --skill-root "$SKILL_DIR" --out "$RUN/fi"
```

末行 `fault-inject: 25/25 conform to the documented expectation`，**退出码 0**。

## T8 · 题集（跨题材回归）

```bash
python -B "$SKILL_DIR/scripts/case_probe.py" --skill-root "$SKILL_DIR" --out "$RUN/cases"
```

末行 `case-probe: 10/10 item(s) conform to their declared expectations`，**退出码 0**。

## T9 · 文档 ↔ 代码对拍

```bash
python -B "$SKILL_DIR/scripts/doccheck.py" --root "$SKILL_DIR"
```

`doc-check: CONSISTENT (0 fails, 0 warns)`，**退出码 0**。意义：本版新增的
`degrade_probe.py` 的 8 个 flag 与文档里点名的检查名都逐一对上。

## T10 · 最小可用环境的独立复核

```bash
python -c "import json;r=json.load(open('<RUN>/dg/degrade-matrix.json',encoding='utf-8'));\
print([(m['module'], m['required'], m['evidence_probe']) for m in r['minimal_env']])"
```

本机实测输出（节选）：

```
[('PIL', 'yes', 'G02'), ('matplotlib', 'yes', 'G01'), ('numpy', 'yes', 'G03'),
 ('LibreOffice CLI', 'no', 'G09'), ('PyPDF2', 'no', 'G07'), ('fitz', 'no', 'G07'),
 ('lxml', 'no', 'G06'), ('pptx', 'no', 'G05'), ('pypdf', 'no', 'G07'),
 ('reportlab', 'no', 'G08'), ('yaml', 'no', 'G04')]
```

⇒ 交付/部署时必须保证 `matplotlib` + `Pillow` + `numpy` 可用；其余可选。

## T11 · 形态与合规自查（仓库自带的合规验收器）

```bash
python <efficiency-3 仓库>/validate_pkg.py <包目录>
```

实测 `[PASS]`：文件 **49**（上限 50）、单文件 ≤500KB（最大 `scripts/fault_inject.py` 46,380 B）、
总计 **533,393 B ≈ 521 KB**（上限 2 MB）、扩展名只用
`.md/.py/.json/.txt/.csv`、无 `__pycache__`/`*.pyc`、无符号链接、无本机绝对路径。

包内自查（在包目录上跑；两条都必须 **0 命中**）：

```bash
# 本机绝对路径：0 命中（模式用 chr(92) 拼出，避免把检测串本身写进文档）
python -c 'import os,re;bs=chr(92);pat=re.compile("[A-Za-z]:"+re.escape(bs*2));print("abs-path hits:",sum(1 for r,_,fs in os.walk(".") for f in fs if pat.search(open(os.path.join(r,f),encoding="utf-8",errors="replace").read())))'
# 假变体形态（末尾注释段/变更记录段）：0 命中（跳过本文件，因为这几行检查命令自身就在本文件里）
python -c 'import os;print("trailing-note hits:",sum(1 for r,_,fs in os.walk(".") for f in fs if f!="TEST.md" and ("末尾注释段" in open(os.path.join(r,f),encoding="utf-8",errors="replace").read() or "变更记录段" in open(os.path.join(r,f),encoding="utf-8",errors="replace").read())))'
```

## T12 · 未测量项（本文件**不**为它们背书）

半损坏的库（装了但版本/ABI 不匹配、缺 DLL）；跨 OS / 跨 Python 版本；
缺 CJK 字体（属 `font.cjk` 那条链路）；matplotlib 后端依赖（FreeType 等）；
只读输出目录与磁盘满；`--skip-checks`/`--no-lint` 叠加缺依赖；
`numpy` 缺失时的失败原因标签为何写成 `render.matplotlib`（实测现象已记录，
**成因未查**）。逐条理由见 `references/DEGRADE-MATRIX.md` §7。
