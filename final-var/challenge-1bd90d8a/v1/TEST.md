# TEST.md — 真机实测记录（决策显性化版）

本文件记录的都是**本机真实跑出来的**结果，不是设计意图。所有实测都在**包外临时目录**
进行（包内不跑脚本，避免产生 `__pycache__` 污染提交物）。

- 环境：Windows 10 · CPython **3.13.9**（Anaconda） · Pillow **12.3.0** · 无网络访问
- 被测对象：本包目录的副本（`$PKG`），示例案例 `$PKG/examples/case.json`（2 张图：
  `fig-01` panel(bar+line) + `fig-02` network）
- 时间：2026-11-22 +08

---

## T1 编译与导入

```
python -m py_compile $PKG/scripts/*.py      → exit 0（10/10 脚本通过）
```

10 个脚本：`main.py` `chartkit.py` `extract.py` `spec_lint.py` `figcheck.py`
`mapcheck.py` `verify_rerun.py` `check_contract.py` `cjkfont.py` `svgtext.py`。

## T2 主链路冒烟（cwd 不在技能根目录）

```bash
cd <包外临时目录>                       # 故意让 cwd != 技能根
python "$PKG/scripts/main.py" --case "$PKG/examples/case.json" \
       --out "$TMP/out" --work "$TMP/work" --style nature
```

**实测输出**：
```
[main] case_id=example-science-figure-01 status=completed figures=['fig-01','fig-02'] failed=[]
[main] gates: G1=OK G2=OK G3=OK G4=OK G5=OK G6=OK G7=OK G8=OK all_pass=OK
```
- **exit code = 0**（`completed` 且 G1–G8 全过）
- 产物 **11 个文件**：`figure-fig-01.svg/.png/.pdf`、`figure-fig-02.svg/.png/.pdf`、
  `data_manifest.json`、`validation.json`、`figcheck_report.json`、`mapcheck_report.json`、
  `result.json`
- `result.json` 顶层键 **29 个**，契约核心字段（`case_id`/`status`/`outputs`/
  `uncertainty`/`change_records`/`sources`）齐备

## T3 四条复核命令全部 exit 0

| 命令 | 实测原文（节选） | exit |
|-|-|-|
| `check_contract.py --result $TMP/out/result.json --case …` | `SUMMARY: PASS (required=18 missing=0 null=0 contract_missing=0)` | 0 |
| `figcheck.py --dir $TMP/out --case …` | `GATES: G1=OK G2=OK G3=OK G4=OK G5=OK G6=OK G7=OK G8=OK` / `SUMMARY: ALL GATES PASS` | 0 |
| `mapcheck.py --dir $TMP/out --case …` | `[PASS] fig-01: 79 elements, 0 orphans` / `[PASS] fig-02: 42 elements, 0 orphans` / `SUMMARY: ALL PASS (121 checked / 0 mismatched / 0 unmatched)` | 0 |
| `verify_rerun.py --case … --out $TMP/out` | `SUMMARY: DETERMINISTIC (identical=9 differ=0 missing=0)` | 0 |

## T4 确定性再跑（本版修掉了一处真实缺陷）

```bash
python "$PKG/scripts/main.py" --case "$PKG/examples/case.json" --out $TMP/out   --style nature
python "$PKG/scripts/main.py" --case "$PKG/examples/case.json" --out $TMP/out2  --style nature
# 逐文件 sha256 对拍
```

**修复前**（基线包的实测）：11 个产物里 **5 个** 字节不同 ——
`figure-fig-01.pdf`、`figure-fig-02.pdf`、`figcheck_report.json`、`mapcheck_report.json`、
`result.json`。

**根因**（已定位，非猜测）：Pillow 写 PDF 时会写入当前时间戳
（`/CreationDate (D:…Z)`、`/ModDate (D:…Z)`）。PDF 字节变了 → `artifacts_sha256`
里的 pdf 条目跟着变 → `result.json` 也变。两份报告文件的差异来自各自的 `dir` 字段
（两次运行的输出目录名不同），属环境变量，不是图面差异。

**PDF 到底差几个字节**（`cmp -l` 实测，取决于两次运行的时间关系）：
同一秒内连续跑 = **2 字节**；跨秒跑（`sleep 3`）= **4 字节**（两个时间戳字段的秒数个位各 1 处）。

**修复**：`scripts/chartkit.py` 新增 `stamp_pdf_deterministic()`，
在 PDF 落盘后把 `/CreationDate`、`/ModDate`、`/ID` 就地归一化为固定值，
并同步修正交叉引用表里指向新位置的对象字节偏移（`_adjust_xref_offsets()`）。
本函数只改元数据字节、不改页面内容。

**修复后实测**：

| 产物 | 跨 3 次运行 |
|-|-|
| `figure-fig-01.svg` / `figure-fig-02.svg` | SAME |
| `figure-fig-01.png` / `figure-fig-02.png` | SAME |
| `figure-fig-01.pdf` / `figure-fig-02.pdf` | **SAME**（修复前 DIFF） |
| `data_manifest.json` / `validation.json` | SAME |
| `figcheck_report.json` / `mapcheck_report.json` | 仅 `dir` 字段不同（输出目录名不同，属环境变量） |
| `result.json` | 仅 `dir` / `steps[].ts` / `change_records[].ts` 不同（时间戳与路径，属环境变量） |

判定口径（写在 `references/OUTPUT_CONTRACT.md` 的 D18 位置）：
**去掉「输出目录路径」与「时间戳」两类环境变量后，全部产物逐字节一致。**

PDF 有效性独立复核（`pypdf`）：修复前 1 页、元数据含当前时间；修复后 1 页、
`/CreationDate = D:20000101000000Z`、`/ModDate` 同值 —— 页数不变、可正常解析。
`PIL.Image.open()` 对修复前后的 PDF 均报 `cannot identify image file`
（Pillow 需要 Ghostscript 才能栅格化 PDF），**属既有行为，修复未引入退化**。

## T5 耗时

同一示例案例连跑 3 次（含全部 11 个产物与两轮校验）：

```
run 1: 1.72s exit=0 files=11
run 2: 1.47s exit=0 files=11
run 3: 1.34s exit=0 files=11
mean of 3 runs: 1.51s
```

即「2 张图 + 双校验 + 契约落地」约 **1.5 秒**级别，远低于平台 900 秒预算。

## T6 契约四形态回显

| 形态 | 写法 | 实测 |
|-|-|-|
| ① 字段名列表 | `["case_id","status","outputs"]` | 顶层补齐 ✅ |
| ② 名称→类型 | `{"outputs":"array","title":"string"}` | 按类型给 `[]`/`""` ✅ |
| ③ 嵌套 fields 列表 | `{"fields":["case_id","sources"]}` | 同 ① ✅ |
| ④ 嵌套 fields 映射 | `{"fields":{"title":"string"}}` | 同 ② ✅ |

示例案例用的是形态②，实测回显字段：`case_id` `status` `title` `sources` `outputs`
`editable_source` `rendered_preview` `field_mapping` `validation_report` `uncertainty`
`change_records` `checkpoints` `gates` —— **13/13 全部出现在顶层**，
`null` 计数 **0**。别名映射生效：`editable_source → editable_sources`（2 个 SVG 名）、
`rendered_preview → renders`、`field_mapping → "data_manifest.json"`、
`validation_report → "validation.json"`。

## T7 异常路径（全部实测）

| 场景 | 命令 | 实测 |
|-|-|-|
| `case.json` 不存在 | `main.py --case <不存在的路径> --out $TMP/ex1` | **exit 1**；stderr 打印 `[main] FATAL FileNotFoundError: [Errno 2] …`；**仍写出最小诚实信封** `result.json`，顶层 6 键 = `['case_id','change_records','error','sources','status','uncertainty']`，`status='failed'`，`error` 为异常类型 + 消息 |
| spec 用了未知图型 | `spec_lint.py --spec <type=waterfall>` | **exit 2**，`[ERROR] E1 … 不支持的图型 'waterfall'`，`SUMMARY: INVALID (1 errors / 0 warnings / 1 figures)` |
| `spec_lint.py` 缺必需参数 | `spec_lint.py`（无参） | **exit 2**（argparse 用法错误，与"spec 有 error"同码，见未解决项 4） |
| 契约字段有缺口 | `check_contract.py --result <最小信封 result>` | **exit 1**，`SUMMARY: FAIL (required=5 missing=0 null=0 contract_missing=8)`，逐条列出 `[MISSING] checkpoints` / `[MISSING] gates` 等 |
| 单独复制走 `scripts/` 的一部分 | `python <残缺目录>/main.py` | import 立即失败，非零退出，**不产出半成品 result** |
| Pillow 缺失（未在本机复现，按代码路径声明） | 见 `references/failure-modes.md` FM-E8 | 保 SVG + 全部 JSON，PNG/PDF 记缺失 |

## T8 资源形态合规

```
[PASS] v1  files=38
```
> 规模（实测）：38 个文件 / 404639 字节 / 最大单文件 85203 字节（scripts/chartkit.py）
- 文件数 / 总字节 / 最大单文件均在硬门内（具体数字见交付回报）
- 包内 **0 个二进制**；`__pycache__` / `*.pyc` 计数 **0**
- 包内无本机绝对路径：本机盘符加反斜杠形式的路径、用户目录前缀（形如
  "盘符冒号反斜杠 Users"）、UNC 前缀一律不出现在任何文本文件里
- 唯一的例外是 `scripts/cjkfont.py` 里的 **Windows 字体目录常量**——它是
  **跨平台运行时字体探测的候选路径字符串**，属于探测逻辑本身，不是本机某次运行的痕迹
  （判别法：该字符串是"程序去猜字体在哪"，而不是"某次运行把结果写回来了"；
  校验器对该文件不报 FAIL，见交付回报的说明）

---

## 未解决项（如实记录）

1. **`spec_lint.py` 不做列存在性核对**（实测发现，已记入 `references/failure-modes.md` FM-D1）：
   用 `{"figures":[{"id":"x","type":"bar","x":{"column":"no_such_col"},
   "y":{"column":"also_missing"}}]}` 配 `--case` 跑，**实测 `SUMMARY: VALID (0 errors /
   0 warnings / 1 figures)`、exit 0** —— 即"未知图型"能拦住（E1），但"列不存在"拦不住。
   本版**未改代码**（CLI 与算法不得变动，且改动会波及 lint 规则编号）。
   规避方式写在 `SKILL.md` 的 CP3 判定里：**CP3 之后仍须核对 `extract.json` 的列画像**；
   真正的兜底是 CP5 的 `mapcheck`（它重读源表逐行核对，列不存在必然 mismatch）。
2. **平台官方对照未做**：本机没有平台的基础 Agent 条件，因此本包**不声称**任何
   "相对基础 Agent 提升 x%" 的数字。实测 A/B 记录只放在 **v2/v3** 两个版本中；
   本版（决策显性化版）不重复该实验，避免同一份数据在三个版本里被重复宣称。
   本版可判定的证据仅限于 T3/T4 的机器报告，这些是可复跑的确定事实。
3. **两份报告文件的 `dir` 字段**：`figcheck_report.json` / `mapcheck_report.json`
   会把输出目录写进报告，换目录重跑时该字段不同。**未修** —— 该字段是"这份报告
   在哪里产出"的诚实记录，抹掉反而降低可核验性。判定按 T4 的归一化口径处理。
   （注：`verify_rerun.py` 自己把该字段归为环境变量，因此 T3 的 `DETERMINISTIC
   (identical=9 differ=0)` 与 T4 的原始逐字节对拍不矛盾。）
4. **PDF 栅格化未本地验证**：本机 Pillow 无 Ghostscript，无法把 PDF 转回像素做逐像素
   比对；PDF 与 PNG 的"逐元素一致"由同一个 `Scene` 生成保证，另以 `%PDF` 头 + 页数 +
   `pypdf` 解析成功作为可用性证据。
5. **`spec_lint.py` / `check_contract.py` 的用法错误与业务错误共用退出码**
   （都用 2）。**未修**（改退出码会动 CLI 语义）。区分方式：用法错误在 stderr 打印
   `usage:` 前缀，业务错误打印 `[ERROR] Exx` 前缀。
