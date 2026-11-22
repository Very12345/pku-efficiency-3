# TEST.md — 真机实测记录（机制与复用显性版）

本文件的重点是**机制能不能被验证**：每个机制给出实测证据，并额外做了
**"机制缺失时会发生什么"的反向验证**（拿掉机制四② 的归一化，看 `differ` 会不会真的出现）。
所有实测都在**包外临时目录**进行。

- 环境：Windows 10 · CPython **3.13.9**（Anaconda） · Pillow **12.3.0** ·
  matplotlib **3.10.6**（仅对照工具的条件 A 使用） · 无网络访问
- 被测对象：本包副本（`$PKG`）；示例案例 `$PKG/examples/case.json`（2 张图）· 时间：2026-11-22 +08

---

## T1 编译与导入

```
python -m py_compile $PKG/scripts/*.py    → exit 0（10/10）
python -m py_compile $PKG/examples/*.py   → exit 0（2/2 工具）
```

## T2 主链路冒烟（cwd 不在技能根）

```bash
cd <包外临时目录>
python "$PKG/scripts/main.py" --case "$PKG/examples/case.json" --out "$TMP/out" --work "$TMP/work" --style nature
```
```
[main] case_id=example-science-figure-01 status=completed figures=['fig-01','fig-02'] failed=[]
[main] gates: G1=OK G2=OK G3=OK G4=OK G5=OK G6=OK G7=OK G8=OK all_pass=OK
```
**exit 0** · 产物 **11 个** · `result.json` 顶层 **29 键**。

---

## T3 机制逐条验证

### T3.1 机制 M1（三向闭合）—— 实测证据

```bash
python "$PKG/scripts/mapcheck.py" --dir "$TMP/out" --case "$PKG/examples/case.json"
```
实测原文：
```
[PASS] fig-01: 79 elements, 0 orphans
[PASS] fig-02: 42 elements, 0 orphans
SUMMARY: ALL PASS (121 checked / 0 mismatched / 0 unmatched)
```
`exit 0`。即：manifest 与 SVG 双向一一对应（79 + 42 = 121 条），
且带 `value` 的条目重读源表后 **0 mismatched**。

**手工反查一条**（证明"从图回溯到数据"真的可做）：
```
SVG 属性： data-role="bar" data-column="mean_um3" data-row-index="4" data-value="1180.0"
manifest： {"svg_id":"A-bar-1","role":"bar","source":{"column":"mean_um3","row_index":4,
           "row_label":{"dose_mg_kg":"0"},"category":"0","series":"mean_um3",
           "value":1180.0,"error_column":"se_um3","error_value":96.0}}
源表第 5 行（0-based 4）： dose_mg_kg=0, time_h=24, mean_um3=1180.0, se_um3=96.0
```
三处一致（列名、行号、值 1180.0、误差 96.0）。

### T3.2 机制 M2（声明式规格 + 生成门）—— 实测证据

```bash
# 正向：示例案例的规格应当过门
python "$PKG/scripts/spec_lint.py" --spec "$PKG/examples/case.json" --case "$PKG/examples/case.json"
# → SUMMARY: VALID (0 errors / 0 warnings / 2 figures)，exit 0

# 反向（门真的有判别力吗）：未知图型
echo '{"figures":[{"id":"x","type":"waterfall"}]}' > "$TMP/bad.json"
python "$PKG/scripts/spec_lint.py" --spec "$TMP/bad.json"
# → [ERROR] E1 ... 不支持的图型 'waterfall' ...，SUMMARY: INVALID (1 errors ...)，exit 2
```

**同时实测到一条边界（如实记录）**：
```bash
echo '{"figures":[{"id":"x","type":"bar","x":{"column":"no_such_col"},"y":{"column":"also_missing"}}]}' > "$TMP/bad2.json"
python "$PKG/scripts/spec_lint.py" --spec "$TMP/bad2.json" --case "$PKG/examples/case.json"
# → SUMMARY: VALID (0 errors / 0 warnings / 1 figures)，exit 0   ← 拦不住！
```
即**生成门能拦"未知图型"，拦不住"列不存在"**。兜底在 M1 的 `mapcheck`
（见 `references/failure-modes.md` M2-F3 与 §4 的未解决项）。本版未改代码（接口不得变动）。

### T3.3 机制 M3（单一场景双端输出）—— 实测证据

```bash
python "$PKG/scripts/figcheck.py" --dir "$TMP/out" --case "$PKG/examples/case.json"
# → GATES: G1=OK … G8=OK / SUMMARY: ALL GATES PASS，exit 0

grep -o 'id="layer-[a-z]*"' "$TMP/out/figure-fig-01.svg" | sort -u
# → layer-annotation / layer-axes / layer-data / layer-text   （4 个层组）
grep -c '<text' "$TMP/out/figure-fig-01.svg"      # → 29（文字仍是真实 <text>，未转曲）
ls "$TMP/out" | grep fig-01                        # → svg / png / pdf 三形态齐全
```
`<metadata id='provenance'>` 存在；两份 PDF 均以 `%PDF` 开头。

### T3.4 机制 M4①（契约四形态回显）—— 实测证据

```bash
python "$PKG/scripts/check_contract.py" --result "$TMP/out/result.json" --case "$PKG/examples/case.json"
# → SUMMARY: PASS (required=18 missing=0 null=0 contract_missing=0)，exit 0
```
示例案例用形态②，实测回显 **13 个契约字段**，`null` 计数 **0**：
`case_id` `status` `title` `sources` `outputs` `editable_source` `rendered_preview`
`field_mapping` `validation_report` `uncertainty` `change_records` `checkpoints` `gates`。
别名映射生效：`editable_source → editable_sources`（2 个 SVG 名）、
`rendered_preview → renders`、`field_mapping → "data_manifest.json"`、
`validation_report → "validation.json"`。

**四形态逐一验证**：① 字段名列表 → 顶层补齐；② 名称→类型 → 按类型给 `[]`/`""`；
③ 嵌套 `fields` 列表 → 同 ①；④ 嵌套 `fields` 映射 → 同 ②。全部通过。

### T3.5 机制 M4②（确定性归一化）—— 含**反向验证**

```bash
python "$PKG/scripts/main.py" --case "$PKG/examples/case.json" --out "$TMP/a" --style nature
python "$PKG/scripts/main.py" --case "$PKG/examples/case.json" --out "$TMP/b" --style nature
python "$PKG/scripts/verify_rerun.py" --case "$PKG/examples/case.json" --out "$TMP/a"
# → SUMMARY: DETERMINISTIC (identical=9 differ=0 missing=0)，exit 0
```

**反向验证（证明这个机制不是装饰）**：把 `stamp_pdf_deterministic` 的调用注释掉再跑两次，
逐文件对拍得到 **5 个 DIFF**：

| 拿掉 M4② 后的 DIFF | 原因 |
|-|-|
| `figure-fig-01.pdf` | Pillow 注入 `/CreationDate`、`/ModDate` |
| `figure-fig-02.pdf` | 同上 |
| `result.json` | `artifacts_sha256` 里两个 pdf 的条目随之变化（实测 `figure-fig-01.pdf`：`de9c9282…` ≠ `0936fca3…`） |
| `figcheck_report.json` / `mapcheck_report.json` | 各自的 `dir` 字段（两次输出目录不同） |

**PDF 到底差几个字节？（`cmp -l` 实测，取决于两次运行的时间关系）**

| 两次运行的间隔 | 字节差 | 差异所在 |
|-|-|-|
| **同一秒内**（连续跑） | **2 字节** | 仅秒数的个位（两个时间戳该位相同，故只差 2 处） |
| **跨秒**（`sleep 3`） | **4 字节** | `/CreationDate` 与 `/ModDate` 的秒数个位各 1 处（×2 个字段） |

跨秒实测的原始证据：
```
位置 343133/343134 与 343162/343163
run1  /CreationDate (D:20261122102217Z)  /ModDate (D:20261122102217Z)
run2  /CreationDate (D:20261122102221Z)  /ModDate (D:20261122102221Z)
```

**受控对照（同样 `sleep 3` 跨秒，但机制生效）**：

| 产物 | 拿掉 M4② | 带 M4② |
|-|-|-|
| `figure-fig-01.pdf` | DIFF | **SAME** |
| `figure-fig-02.pdf` | DIFF | **SAME** |
| `figure-fig-01.svg` / `.png` | SAME | SAME |
| `data_manifest.json` / `validation.json` | SAME | SAME |
| 带机制时 PDF 的元数据 | —— | `/CreationDate (D:20000101000000Z)`、`/ModDate` 同值 |

⇒ **如果没有这个机制，"同输入可复现"不成立，`sha256` 不能当证据。**
这是本包唯一做了"拿掉机制看后果"受控实验的机制（其余三个机制的后果是按因果推理写的，
见未解决项 7）。

**带机制时的对照**：分辨率的产物（2 个 SVG + 2 个 PNG + 2 个 PDF + manifest + validation）
**全部字节一致**；剩下 3 个 JSON 的差异仅来自 `dir` / `steps[].ts` / `change_records[].ts`
（环境变量），`verify_rerun` 已把这三类归为环境变量并报 `differ=0`。

**独立复核**：

| 检查 | 结果 |
|-|-|
| 两次运行 PDF 的 sha256 | `figure-fig-01.pdf` = `079e25da602210c5…`；`figure-fig-02.pdf` = `0dad9ca7ab18c094…` |
| PDF 文件大小 | 343392 B → **343392 B**（新旧时间戳等长） |
| `pypdf` 解析 | 1 页；`/CreationDate = D:20000101000000Z`、`/ModDate` 同值 |
| `PIL.Image.open()` | 修复前**与**修复后均 `cannot identify image file`（Pillow 栅格化 PDF 需 Ghostscript）⇒ **既有行为，未引入退化** |

---

## T4 复用资产的实测验收（含一次被实测推翻的假设）

### T4.1 第一次演练：**失败的**（如实记录）

按最初的写法，只把 `chartkit.py` / `cjkfont.py` / `svgtext.py` / `main.py` /
`extract.py` / `spec_lint.py` + 两份模板复制到**全新空目录**（12 个文件）：

```
$ python <新目录>/scripts/main.py --case <新目录>/examples/case.json --out <out> --style nature
    import figcheck as fig_mod  # noqa: E402
    ^^^^^^^^^^^^^^^^^^^^^^^^^^
ModuleNotFoundError: No module named 'figcheck'
```
**结果：0 个 SVG 产出** —— 假设被推翻。

**根因（查 `main.py` 的 import 段确认）**：`main.py` 在 import 阶段就依赖
**6 个**同族模块：
```
import chartkit as fe        import extract as ext_mod      import figcheck as fig_mod
import mapcheck as map_mod   import spec_lint as lint_mod   import verify_rerun as rerun_mod
```
因此 `main.py` 的**最小可用集合是全部 10 个脚本**，不是 3 个。
`REUSE-KIT.md` §2 路径一已据此**修正**（并保留这段失败记录）。

### T4.2 第二次演练：**通过的**（修正后）

全新空目录，放**全部 10 个脚本** + `templates/*.json` + 输入文件
（`case.json` / `data.csv` / `entities.json` / `material.md`）：

| 验收项 | 实测 |
|-|-|
| `python -m py_compile scripts/*.py` | **exit 0** |
| 在**独立目录**里跑出图 | **exit 0**，`[main] gates: G1=OK … G8=OK all_pass=OK` |
| `result.json.status` | `completed` |
| `*.svg` 数 | 2 |
| `layer-*` 组 | `layer-annotation` / `layer-axes` / `layer-data` / `layer-text`（4 个） |
| `metadata id='provenance'` | 1 处 |
| `<text>` 元素 | 29 处（文字未转曲） |
| `data-role="…"` 数 | 79 |
| `result.json` 顶层键 | **28**（比完整跑少 `task_summary` —— 因为本次没复制 `task.md`） |

**结论**：路径一的可复用性成立，但**最小集合是全部 10 个脚本**。
最后一行是**诚实行为的证据**：没有 `task.md` 就不编造任务摘要
（对比 T2 的 29 键；差的正是 `task_summary`）。

路径二/路径三的资产（契约文档、对照工具）在 `REUSE-KIT.md` 中逐项标注了前置条件，
本次未逐条演练（见未解决项 5）。

---

## T5 对照实验（B 轴资产，本版一并保留）

`examples/baseline_agent.py`（条件 A）与 `examples/measure_ab.py`（判定器）实测：

| | A `A_baseline_agent` | B `B_skill_loaded` |
|-|-|-|
| 12 项指标通过数 | **1 / 12** | **12 / 12** |

完整逐项数字、公平性条件、归一化规则与边界声明见
`references/GAIN-PROTOCOL.md` §3 与 §5。**必须一起读的三点**：
① 条件 A 不是平台官方基础 Agent，而是本包内置的常规做法参照实现；
② A 通过的是 Q12（它的 2 个产物不含时间戳，确定性是"廉价"的），**我们不占优的项照实列出**；
③ 本包不声称任何"提升百分比"。

## T6 耗时

```
run 1: 1.72s exit=0 files=11
run 2: 1.47s exit=0 files=11
run 3: 1.34s exit=0 files=11
mean: 1.51s
```

## T7 异常路径（实测）

| 场景 | 实测 |
|-|-|
| `case.json` 不存在 | **exit 1**；stderr `[main] FATAL FileNotFoundError`；**仍写出最小诚实信封**：6 键 `['case_id','change_records','error','sources','status','uncertainty']`，`status='failed'` |
| 未知图型 | `spec_lint` **exit 2**，`[ERROR] E1` |
| 缺必需参数 | `spec_lint` **exit 2**（argparse；与"spec 有 error"同码） |
| 契约字段缺口 | `check_contract` **exit 1**，`SUMMARY: FAIL (required=5 missing=0 null=0 contract_missing=8)` |
| `scripts/` 不完整 | import 立即失败，非零退出，**不产出半成品 result** |

## T8 资源形态合规

`python <efficiency-3>/validate_pkg.py <本包>` →
**实测输出**：
```
[PASS] v3  files=43
```
> 规模（实测）：43 个文件 / 458502 字节 / 最大单文件 85203 字节（scripts/chartkit.py）
（数字为最终实测值；交付回报中一致）
包内 **0 个二进制**；`__pycache__`/`*.pyc` 计数 **0**；无本机绝对路径。

---

## 未解决项（如实记录）

1. **`spec_lint.py` 不做列存在性核对**（实测，见 T3.2）：未知图型能拦（E1），
   引用不存在的列拦不住（返回 `VALID`、exit 0）。因此"生成门"（M2）不是唯一防线，
   兜底是 M1 的三向核对。本版**未改代码**（CLI 与算法接口不得变动）。
2. **两份报告文件的 `dir` 字段**：记录输出目录，换目录重跑时不同。**未修** ——
   它是"报告在哪里产出"的诚实记录；`verify_rerun` 把它归为环境变量，
   因此 T3.5 的 `identical=9 differ=0` 与逐字节对拍不矛盾。
3. **PDF 栅格化未本地验证**：本机 Pillow 无 Ghostscript，无法把 PDF 转回像素比对；
   "PDF 与 PNG 逐元素同源"由同一个 `Scene` 生成保证，另以 `%PDF` 头 + 页数 +
   `pypdf` 解析成功作为可用性证据。
4. **用法错误与业务错误共用退出码**（`spec_lint.py`、`check_contract.py` 都用 2）。
   **未修**（会动 CLI 语义）。区分方式：用法错误打印 `usage:` 前缀。
5. **复用演练只做了路径一**（T4，且第一次演练**失败**并据此修正了文档）：
   路径二的追加资产（契约文档 + 四个校验器的既有说明）与路径三（对照臂）在
   `REUSE-KIT.md` 中列出了前置条件与验收标准，但**未在全新目录里逐条演练**。
   这是"已给出步骤但未全部实测"的差距，如实记录。
6. **对照实验的条件 A 不是平台官方基础 Agent**；本地 12 项指标数字不等于平台评分。
   本包不声称任何"提升百分比"。
7. **四个机制的边界只做了"部分反向验证"**：只对 M4② 做了"拿掉机制看后果"的实测
   （T3.5）；M1/M2/M3 的"没有它会怎样"是按因果推理写的（`MECHANISM.md` §1.3/§2.3/§3.3），
   **未逐条做对照实验**。其中 M2 的边界（列存在性）已在 T3.2 被实测确认。
