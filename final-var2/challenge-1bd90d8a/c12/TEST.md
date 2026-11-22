# TEST.md — 真机实测记录（增益可验证版）

本文件的所有数字都是**本机真实跑出来的**。所有实测都在**包外临时目录**进行
（包内不跑脚本，避免产生 `__pycache__` 污染提交物）。

- 环境：Windows 10 · CPython **3.13.9**（Anaconda） · Pillow **12.3.0** ·
  matplotlib **3.10.6**（仅对照实验的条件 A 使用） · 无网络访问
- 被测对象：本包目录的副本（`$PKG`）；示例案例 `$PKG/examples/case.json`
  （2 张图：`fig-01` panel(bar+line) + `fig-02` network）
- 时间：2026-11-22 +08

---

## T1 编译与导入

```
python -m py_compile $PKG/scripts/*.py        → exit 0（10/10 脚本通过）
python -m py_compile $PKG/examples/*.py       → exit 0（2/2 工具通过）
```

## T2 主链路冒烟（cwd 不在技能根目录）

```bash
cd <包外临时目录>                     # 故意让 cwd != 技能根
python "$PKG/scripts/main.py" --case "$PKG/examples/case.json" \
       --out "$TMP/out" --work "$TMP/work" --style nature
```

**实测输出**：
```
[main] case_id=example-science-figure-01 status=completed figures=['fig-01','fig-02'] failed=[]
[main] gates: G1=OK G2=OK G3=OK G4=OK G5=OK G6=OK G7=OK G8=OK all_pass=OK
```
- **exit code = 0**（`completed` 且 G1–G8 全过）
- 产物 **11 个**；`result.json` 顶层 **29 键**，六个核心键齐备

## T3 四条复核命令（实测原文）

| 命令 | 实测输出 | exit |
|-|-|-|
| `check_contract.py` | `SUMMARY: PASS (required=18 missing=0 null=0 contract_missing=0)` | 0 |
| `figcheck.py` | `GATES: G1=OK … G8=OK` / `SUMMARY: ALL GATES PASS` | 0 |
| `mapcheck.py` | `[PASS] fig-01: 79 elements, 0 orphans` / `[PASS] fig-02: 42 elements, 0 orphans` / `SUMMARY: ALL PASS (121 checked / 0 mismatched / 0 unmatched)` | 0 |
| `verify_rerun.py` | `SUMMARY: DETERMINISTIC (identical=9 differ=0 missing=0)` | 0 |

## T4 契约四形态回显（示例案例用形态②）

实测回显 13 个契约字段，`null` 计数 **0**：
`case_id` `status` `title` `sources` `outputs` `editable_source` `rendered_preview`
`field_mapping` `validation_report` `uncertainty` `change_records` `checkpoints` `gates`。
别名映射生效：`editable_source → editable_sources`（2 个 SVG 名）、
`rendered_preview → renders`、`field_mapping → "data_manifest.json"`、
`validation_report → "validation.json"`。

## T5 ★ A/B 对照实验（本版的核心实测）

命令见 `references/GAIN-PROTOCOL.md` §4。逐项实测（`examples/measure_ab.py` 输出）：

| # | 指标 | A `A_baseline_agent` | B `B_skill_loaded` |
|-|-|-|-|
| Q1 | 可编辑矢量源 | MISS `svg_files=0` | **PASS** `svg_files=2` |
| Q2 | 分层可编辑 | MISS `layer_groups=0` | **PASS** `layer_groups=4` |
| Q3 | 图元级溯源 | MISS `data_role=0 source_attrs=0` | **PASS** `data_role=79 source_attrs=54` |
| Q4 | 机器可读映射 | MISS `absent/unparsable` | **PASS** `parsed` |
| Q5 | 数值可逐行回核 | MISS `rows_checked=0 mismatched=0` | **PASS** `rows_checked=24 mismatched=0` |
| Q6 | 轴单位 | MISS `declared=['mg/kg','μm³'] present=[]` | **PASS** `present=['mg/kg','μm³']` |
| Q7 | 误差线语义 | MISS `error_column=se_um3 marks=0 semantics_recorded=False` | **PASS** `marks=12 semantics_recorded=True` |
| Q8 | 多图覆盖 | MISS `figures_in_case=2 svg_out=0` | **PASS** `svg_out=2` |
| Q9 | 结果信封 | MISS `result.json_keys=0 core_complete=False` | **PASS** `result.json_keys=29 core_complete=True` |
| Q10 | 源文件 sha256 | MISS `sources=0 with_sha256=0` | **PASS** `sources=2 with_sha256=2` |
| Q11 | 变更记录 | MISS `change_records=0` | **PASS** `change_records=7` |
| Q12 | 重跑确定性 | **PASS** `identical=2 differ=0` | **PASS** `identical=10 differ=1`（归一化后通过） |
| | **合计** | **1 / 12** | **12 / 12** |

**三条必须一起读的说明**：

1. **A 通过 Q12 是我们不占优的一项**：A 只有 2 个产物且都不含时间戳，
   字节稳定是"廉价"的。**照实列出，不隐瞒。**
2. **B 的 Q12 原始输出是 `identical=10 differ=1`**：差的是 `result.json`，
   实质原因只有两个 pdf 的 sha256。根因与修复见 T6。
3. **条件 A 不是平台官方基础 Agent**，而是本包内置的常规做法参照实现；
   本地数字不等于平台评分（`GAIN-PROTOCOL.md` §2.1 / §6）。

## T6 ★ 由对照实验发现并修掉的确定性缺陷

**发现路径**：跑 Q12 → `differ=1` → 打开 `result.json` 对拍 → 定位到两个 pdf sha256 →
`cmp -l` 显示两份 PDF 仅差 **4 字节** → 抓到 `/CreationDate` / `/ModDate`。

```
VAL /artifacts_sha256/figure-fig-01.pdf  bf7470b4…6ce  !=  a2174efe…110
VAL /artifacts_sha256/figure-fig-02.pdf  376fb81f…c3d  !=  3b6c3420…e9d
# cmp -l condB/figure-fig-01.pdf condB2/figure-fig-01.pdf | wc -l   → 4（跨秒跑）
# 同一秒内连续跑的两次则为 2 字节（两个时间戳字段该位相同）
```

字节差随两次运行的时间关系变化（`cmp -l` 实测）：

| 两次运行间隔 | 字节差 | 差异所在 |
|-|-|-|
| 同一秒内（连续跑） | **2 字节** | 仅秒数个位 |
| 跨秒（`sleep 3`） | **4 字节** | `/CreationDate` 与 `/ModDate` 各 1 处 |

跨秒实测原文：`run1 /CreationDate (D:20261122102217Z)` vs `run2 (D:20261122102221Z)`。

**根因**：Pillow 写 PDF 时注入当前时间戳
`/CreationDate (D:20261122095608Z)`、`/ModDate (D:20261122095608Z)`。

**修复**：`scripts/chartkit.py` 新增
`stamp_pdf_deterministic()`（归一化 `/CreationDate`、`/ModDate`、`/ID`）
与 `_adjust_xref_offsets()`（同步修正 xref 中指向新位置的对象字节偏移），
由 `png_to_pdf()` 在 `page.save(...)` 之后调用。

**修复前后对照（逐文件）**：

| 产物 | 修复前 | 修复后 |
|-|-|-|
| `figure-fig-01.pdf` | DIFF（4 字节） | **SAME** |
| `figure-fig-02.pdf` | DIFF | **SAME** |
| `figure-fig-01.svg` / `figure-fig-02.svg` | SAME | SAME |
| `figure-fig-01.png` / `figure-fig-02.png` | SAME | SAME |
| `data_manifest.json` / `validation.json` | SAME | SAME |
| `figcheck_report.json` / `mapcheck_report.json` | DIFF（仅 `dir` 字段） | DIFF（仅 `dir` 字段） |
| `result.json` | DIFF（`dir`/`steps`/`change_records` + 两个 pdf sha） | DIFF（仅 `dir`/`steps`/`change_records`，**pdf sha 已一致**） |

**独立复核**：

| 检查 | 结果 |
|-|-|
| `verify_rerun.py` | `SUMMARY: DETERMINISTIC (identical=9 differ=0 missing=0)`，exit 0 |
| 两次运行 PDF 的 sha256 | `figure-fig-01.pdf` = `079e25da602210c5…`；`figure-fig-02.pdf` = `0dad9ca7ab18c094…`（两侧相同） |
| PDF 文件大小 | 343392 B → **343392 B**（新旧时间戳等长，字节数不变） |
| `pypdf` 解析 | 1 页；`/CreationDate = D:20000101000000Z`、`/ModDate` 同值 |
| `PIL.Image.open()` | 修复前**与**修复后均 `cannot identify image file`（Pillow 栅格化 PDF 需 Ghostscript）⇒ **既有行为，未引入退化** |

## T7 耗时与产物规模

```
run 1: 1.72s exit=0 files=11
run 2: 1.47s exit=0 files=11
run 3: 1.34s exit=0 files=11
mean of 3 runs: 1.51s
```

条件 A 单次约 0.9 s（产物 2 个）。**不对"谁更快"下结论** —— A 快是因为做的事更少
（不出 SVG、不写契约、不校验）。正确读法见 `GAIN-PROTOCOL.md` §5.4。

## T8 异常路径（全部实测）

| 场景 | 命令 | 实测 |
|-|-|-|
| `case.json` 不存在 | `main.py --case <不存在>` | **exit 1**；stderr `[main] FATAL FileNotFoundError`；**仍写出最小诚实信封**：顶层 6 键 `['case_id','change_records','error','sources','status','uncertainty']`，`status='failed'` |
| 未知图型 | `spec_lint.py --spec <type=waterfall>` | **exit 2**，`[ERROR] E1 … 不支持的图型 'waterfall'` |
| 缺必需参数 | `spec_lint.py`（无参） | **exit 2**（argparse；与"spec 有 error"同码，见未解决项） |
| 契约字段有缺口 | `check_contract.py --result <最小信封 result>` | **exit 1**，`SUMMARY: FAIL (required=5 missing=0 null=0 contract_missing=8)` |
| `scripts/` 不完整 | `python <残缺目录>/main.py` | import 立即失败，非零退出，**不产出半成品 result** |

## T9 资源形态合规

```
python <efficiency-3>/validate_pkg.py <本包>   → [PASS] v2  files=41
```
> 规模（实测）：41 个文件 / 427903 字节 / 最大单文件 85203 字节（`scripts/chartkit.py`）。
> 上限为 50 文件 / 单文件 500KB / 合计 2MB，均在硬门内。

包内 **0 个二进制**；`__pycache__`/`*.pyc` 计数 **0**；无本机绝对路径
（唯一的候选路径字符串是 `scripts/cjkfont.py` 的跨平台字体探测常量，属探测逻辑本身）。

---

## 未解决项（如实记录）

1. **对照实验的条件 A 不是平台官方基础 Agent**：本机没有该条件。本包的 A 条件是把
   "通用绘图库 + 直接写脚本"固化成可复跑代码的**参照实现**（不刻意做差，但也不是它）。
   因此本包**不声称**任何"提升百分比"，只声称 12 项指标的**通过数**（可复算事实）。
2. **`spec_lint.py` 不做列存在性核对**（实测）：用
   `{"figures":[{"id":"x","type":"bar","x":{"column":"no_such_col"},"y":{"column":"also_missing"}}]}`
   配 `--case` 跑，实测 `SUMMARY: VALID (0 errors / 0 warnings / 1 figures)`、exit 0。
   即"未知图型"能拦住（E1），"列不存在"拦不住。本版**未改代码**（CLI 与算法不得变动）；
   兜底在 `mapcheck`（列不存在必然 mismatch）。已记入 `references/failure-modes.md`。
3. **两份报告文件的 `dir` 字段**：`figcheck_report.json` / `mapcheck_report.json`
   记录输出目录，换目录重跑时不同。**未修** —— 该字段是"报告在哪里产出"的诚实记录。
   `verify_rerun.py` 把它归为环境变量，因此 T3 的 `identical=9 differ=0` 与
   T6 的原始逐字节对拍不矛盾。
4. **PDF 栅格化未本地验证**：本机 Pillow 无 Ghostscript，无法把 PDF 转回像素做逐像素
   比对；"PDF 与 PNG 逐元素一致"由同一个 `Scene` 生成保证，另以 `%PDF` 头 + 页数 +
   `pypdf` 解析成功作为可用性证据。
5. **用法错误与业务错误共用退出码**（`spec_lint.py`、`check_contract.py` 都用 2）。
   **未修**（会动 CLI 语义）。区分方式：用法错误打印 `usage:` 前缀，业务错误打印
   `[ERROR] Exx` / 报告前缀。
6. **条件 A 的耗时未做多次统计**（只观察了单次约 0.9 s）。因为它不用于任何结论，
   所以未按 3 次取均值；这一点在 `GAIN-PROTOCOL.md` §5.4 已说明"不做耗时声称"。
