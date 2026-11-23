# DETERMINISM.md — 字节级可复现：逐字段实测与稳定化配方（v7 轴）

> 本文件里**每一个数字都来自 `scripts/determinism.py` 的一次真实运行**，
> 生成它的命令逐字写在 §2。机器可读原始证据是同目录的
> `determinism_report.json`（isolated 5 次重复）与
> `determinism_inplace_report.json`（inplace 3 次重复）。

---

## 1. 这一轴回答什么

两个问题，都只能用跑出来的数字回答：

1. **同输入同参数，连跑 N 次，产物是不是逐字节一样？**
2. **不一样的那些，差在哪个字段？是故意留的信息，还是没控制住的随机？**

判定口径分两级，缺一不可：

| 级别 | 判据 | 为什么需要它 |
|-|-|-|
| `identical` | 原始字节 sha256 全同 | 最强：任何人拿到同一份输入都能得到同一份字节 |
| `normalized_identical` | 施加归一化规则 N1–N4 之后全同 | 把「诚实留痕导致的不稳定」与「真正的不可复现」分开 |

只报第一级会把「时间戳不同」误判为缺陷；只报第二级会掩盖真正的随机性。两级都报，并**逐字段列出**差异，才是可验证的说法。

## 2. 复跑命令（逐字）

```bash
# ① 跨进程 / 跨 cwd / 跨 PYTHONHASHSEED：每一次都换一个输出目录
python "$SKILL_DIR/scripts/determinism.py" \
    --case /input/case.json --runs 5 \
    --seeds 0,1,12345,7,99 --mode isolated \
    --workroot /app/work/det --out /app/work/det/determinism_report.json

# ② 同一绝对输出目录：把「输出目录绝对路径」这个变量排除，只看剩余不确定性
python "$SKILL_DIR/scripts/determinism.py" \
    --case /input/case.json --runs 3 --mode inplace \
    --workroot /app/work/det-inplace \
    --out /app/work/det-inplace/determinism_inplace_report.json
```

`--json` 把报告打到 stdout；`--keep` 保留各次运行的输出目录与归一化副本；
`--main` 可指向**另一个包**的 `main.py`，用同一把尺子量别人。

## 3. 确定性阶梯（退出码就是结论）

| 退出码 | 含义 | 本次实测 |
|-|-|-|
| 0 | 全部产物**逐字节相同**（最强） | 未达到，原因与配方见 §8 |
| **2** | **字节级不同，但归一化后完全一致** ⇒ 不确定性 100% 被 N1–N4 解释 | **isolated = 2；inplace = 2** |
| 3 | 归一化后仍有差异 ⇒ 存在**未解释**的不确定性（报告会给首个差异文件与字节偏移） | 未出现 |
| 1 | 用法错误，或至少一次运行没产出可解析的 `result.json`（无法判定） | 未出现 |

本次重复运行的实测参数：5 次独立进程；cwd 轮转 ['run-dir', 'system-temp', 'case-dir', 'skill-root', 'run-dir']；PYTHONHASHSEED 轮转 [0, 1, 12345, 7, 99]；每次 exit=[0]、status=['completed']、result.json 顶层 [29] 键；单次墙钟约 1.34 秒，整轮 6.97 秒。

## 4. 归一化规则 N1–N4：哪些是**故意**不稳定的

| 规则 | 作用对象 | 逐字段实测结果 | 稳定化做法 |
|-|-|-|-|
| 规则 | 作用对象 | 逐字段实测结果 | 稳定化做法 |
|-|-|-|-|
| **N1** | `result.json` 里键名为 `ts` 的值 | `steps[*].ts` 命中 28 次、`change_records[*].ts` 命中 24 次；两次运行的样例间隔 1 秒左右（同一天内）
| **N2** | `figcheck_report.json` / `mapcheck_report.json` 的 `dir`，以及 JSON 字符串里出现的本次运行根路径 | 各命中 4 次；inplace 模式下这一类整体消失（见 §7） | 改写为相对路径 |
| **N3** | `result.json` 的 `artifacts_sha256.<file>` | 两个 PDF 各命中 4 次；因为 PDF 的内嵌日期变了，这个**自引用哈希**跟着变 | 用归一化后的 sha256 回填（本脚本 pass-2 就是这么算的） |
| **N4** | PDF 里的 `/CreationDate`、`/ModDate` | 两个 PDF 都是 `date_only_diff=True`，首个差异偏移分别是 343132, 72397 | 日期字节替换成固定值 |

四条规则**全部被触发过**：normalization_rules_applied = `N1`, `N2`, `N3`, `N4`。
也就是说，两级判定之间的差距不是猜的，是逐条命中记录下来的；报告里 `volatile_classes` 的键就是这四条规则的编号。

## 5. 实测总表（isolated，5 次重复，11 个产物文件）

| 产物 | 字节 | 原始字节相同 | 归一化后相同 |
|-|-:|-|-|
| `data_manifest.json` | 28979 | ✅ 是 | ✅ 是 |
| `figure-fig-01.png` | 281926 | ✅ 是 | ✅ 是 |
| `figure-fig-01.svg` | 21303 | ✅ 是 | ✅ 是 |
| `figure-fig-02.png` | 122579 | ✅ 是 | ✅ 是 |
| `figure-fig-02.svg` | 11931 | ✅ 是 | ✅ 是 |
| `validation.json` | 2526 | ✅ 是 | ✅ 是 |
| `figcheck_report.json` | 8429 | ❌ 否 | ✅ 是 |
| `figure-fig-01.pdf` | 343392 | ❌ 否 | ✅ 是 |
| `figure-fig-02.pdf` | 72656 | ❌ 否 | ✅ 是 |
| `mapcheck_report.json` | 27617 | ❌ 否 | ✅ 是 |
| `result.json` | 9780 | ❌ 否 | ✅ 是 |

- **逐字节相同 6/11 个**：`data_manifest.json`, `figure-fig-01.png`, `figure-fig-01.svg`, `figure-fig-02.png`, `figure-fig-02.svg`, `validation.json`
- **存在差异 5 个**：`figcheck_report.json`, `figure-fig-01.pdf`, `figure-fig-02.pdf`, `mapcheck_report.json`, `result.json`
- 文件集合本身完全一致（`file_set_identical = True`）—— 没有「某次少写了一个文件」这种更严重的问题。

## 6. 逐字段实测：不稳定字段清单（`volatile_fields`）

| 产物 | 字段路径（list 下标折叠为 `[*]`） | 命中次数 | 类别 | 实测样例（左 → 右） |
|-|-|-:|-|-|
| `figcheck_report.json` | `.dir` | 4 | `run_root_path` | `<RUNROOT>\out` → `<RUNROOT>\out` |
| `mapcheck_report.json` | `.dir` | 4 | `run_root_path` | `<RUNROOT>\out` → `<RUNROOT>\out` |
| `result.json` | `.artifacts_sha256.figure-fig-01.pdf` | 4 | `self_reference_hash` | `71c359ab50cdac0e9392b3faebc7695cb356ac8cf9847a1a3690997109eecea4` → `c246e2a8911bec9a1d0b75aeb97b27a81cf6bc6315698ad88fe46fa66e8b1d85` |
| `result.json` | `.artifacts_sha256.figure-fig-02.pdf` | 4 | `self_reference_hash` | `7d551f3bb4ea6443cb1c73cb80fc2de36f2aeb69272f258b5e4ae362a3b604f0` → `b31937192aa8b1134077ee0d6268c96c1312a5969330ef30e943f657eb7c7d2f` |
| `result.json` | `.change_records[*].ts` | 24 | `timestamp` | `2026-11-23T19:49:35+08:00` → `2026-11-23T19:49:36+08:00` |
| `result.json` | `.steps[*].ts` | 28 | `timestamp` | `2026-11-23T19:49:35+08:00` → `2026-11-23T19:49:36+08:00` |

上表每一行的「命中次数」= 该字段在 4 次两两比较里出现的次数（例如 `steps[*].ts` 有 7 个元素 × 4 次比较 = 28）。

类别计数 `{"run_root_path": 2, "self_reference_hash": 2, "timestamp": 2}`：`timestamp` 对应 N1，`run_root_path` 对应 N2，
`self_reference_hash` 对应 N3；**没有出现 `unknown`** —— 没有任何一条差异是解释不了的。

### 6.1 二进制产物的差异定位

| 产物 | 字节数（两次） | 首个差异偏移 | 是否**仅限**内嵌日期 | 内嵌了什么 |
|-|-:|-:|-|-|
| `figure-fig-01.pdf` | 343392 / 343392 | 343132 | ✅ 是（date_only_diff=True） | `/CreationDate (D:20261123114936Z)`, `/ModDate (D:20261123114936Z)` |
| `figure-fig-02.pdf` | 72656 / 72656 | 72397 | ✅ 是（date_only_diff=True） | `/CreationDate (D:20261123114936Z)`, `/ModDate (D:20261123114936Z)` |

PNG **不在**上表里，因为它逐字节相同。实测确认 Pillow 写出的 PNG 里没有 `tIME` 也没有 `iTXt` 时间块，
所以 PNG 不会像 PDF 那样自带时间戳。（包内既有的 `verify_rerun.py` 早就从同一现象出发，
用 `_pdf_date_strip()` 做归一化；本脚本把它推广成两级判定 + 逐字段定位。）

## 7. 对照实验：把「输出目录」这个变量排除（inplace，3 次）

| 产物 | 字节 | 原始字节相同 | 归一化后相同 |
|-|-:|-|-|
| `data_manifest.json` | 28979 | ✅ 是 | ✅ 是 |
| `figcheck_report.json` | 8429 | ✅ 是 | ✅ 是 |
| `figure-fig-01.png` | 281926 | ✅ 是 | ✅ 是 |
| `figure-fig-01.svg` | 21303 | ✅ 是 | ✅ 是 |
| `figure-fig-02.png` | 122579 | ✅ 是 | ✅ 是 |
| `figure-fig-02.svg` | 11931 | ✅ 是 | ✅ 是 |
| `mapcheck_report.json` | 27617 | ✅ 是 | ✅ 是 |
| `validation.json` | 2526 | ✅ 是 | ✅ 是 |
| `figure-fig-01.pdf` | 343392 | ❌ 否 | ✅ 是 |
| `figure-fig-02.pdf` | 72656 | ❌ 否 | ✅ 是 |
| `result.json` | 9780 | ❌ 否 | ✅ 是 |

- isolated 模式的不稳定类别：`{"run_root_path": 2, "self_reference_hash": 2, "timestamp": 2}`
- inplace 模式的不稳定类别：`{"self_reference_hash": 2, "timestamp": 2}`

**对照结论（这才是本节的价值）**：inplace 模式下 `run_root_path` 这一类**整体消失**，
`figcheck_report.json` 与 `mapcheck_report.json` 也回到逐字节相同 ——
说明这两个报告的唯一不稳定来源就是它们把**输出目录绝对路径**写进了 `dir` 字段。
剩下两类（时间戳、自引用哈希）与输出目录无关，换哪种模式都在。

## 8. 怎么真的拿到阶梯 0（配方 + 本包的取舍）

| 差异来源 | 做法 | 代价 |
|-|-|-|
| `steps[*].ts` / `change_records[*].ts`（N1） | 启动前冻结时钟（`libfaketime`），或把 `chartkit.now_ts()` 换成固定值 | 丢掉「这次运行是什么时候跑的」这条审计线索；题面 §3 要求「来源与修改记录」可核验，本包**选择保留** |
| `figcheck_report.json.dir` / `mapcheck_report.json.dir`（N2） | 把 `dir` 改写成相对路径 | 要改既有脚本的产物字段，本轮规范要求既有脚本尽量逐字节不变，故只登记不改 |
| PDF 的 `/CreationDate`、`/ModDate`（N4） | 由 Pillow 在保存时写入；保存后做一次字节替换即可 | 需要一步后处理；预览件元数据本来就是噪声 |

把「归一化后一致」升级成「字节一致」的最小后处理（与本节 N1–N4 是同一套规则，可直接 import 复用）：

```python
import sys; sys.path.insert(0, "<SKILL_DIR>/scripts")
from determinism import NormCtx, normalize_bytes, sha256_bytes

ctx = NormCtx(roots=[run_root, workspace_root], norm_sha={})   # 根路径替换 = N2
for name, path in artifacts.items():
    raw = open(path, "rb").read()
    print(name, sha256_bytes(normalize_bytes(name, raw, ctx)))  # 归一化后的 sha256
```

> **为什么不直接把时间戳删掉**：本包把 `change_records` 的 ts 当作「谁在什么时候改了图」的证据，
> 把 PDF 的 CreationDate 当作预览件元数据。为了刷一个「字节级复现」的漂亮数字而删掉它们，
> 属于**用假稳定换指标**。本轴的立场是：把不稳定字段逐个点名，并同时给出归一化与稳定化两条路。

## 9. 另一类问题：产物里的绝对路径

同机重跑时它们**不产生差异**（路径不变），所以不会出现在 §6 的不稳定字段里；
但换目录或换机器后，同一份产物的字节就会变。实测清单（`abs_path_leaks`）：

| 产物 | 字段 | 实测样例（报告里已脱敏成占位符） | 影响 |
|-|-|-|-|
| `figcheck_report.json` | `.dir` | `<WORKSPACE>\run-0\out` | 换目录或换机器后，同一份产物的字节会变 |
| `mapcheck_report.json` | `.dir` | `<WORKSPACE>\run-0\out` | 换目录或换机器后，同一份产物的字节会变 |
| `result.json` | `.steps[*].action` | `<CASEDIR>\task.md` | 换目录或换机器后，同一份产物的字节会变 |
| `result.json` | `.change_records[*].action` | `<CASEDIR>\task.md` | 换目录或换机器后，同一份产物的字节会变 |

这 4 处**如实登记、本轮不改**：改它们要动既有脚本的产物字段。

对照：`determinism.py` 自己写出的报告是**可移植**的 —— 所有本机绝对路径在写出前被替换成
`<WORKSPACE>` / `<CASEDIR>` / `<SKILL_DIR>` / `<TMP>` 占位符，所以这份报告可以直接进包、直接给别人看。

## 10. 结论

- 重复 5 次（独立进程 + cwd 轮转 + PYTHONHASHSEED 轮转，mode=isolated），每次产出 11 个产物文件。
- 字节级全同：False；归一化后全同：True。
- 字节不同的文件：figcheck_report.json, figure-fig-01.pdf, figure-fig-02.pdf, mapcheck_report.json, result.json
- 不稳定字段：figcheck_report.json.dir×4[run_root_path]; mapcheck_report.json.dir×4[run_root_path]; result.json.artifacts_sha256.figure-fig-01.pdf×4[self_reference_hash]; result.json.artifacts_sha256.figure-fig-02.pdf×4[self_reference_hash]; result.json.change_records[*].ts×24[timestamp]; result.json.steps[*].ts×28[timestamp]
- 产物文本中另有 4 处绝对路径（同机重跑不影响，换目录/换机器会破坏字节一致性）：figcheck_report.json.dir; mapcheck_report.json.dir; result.json.change_records[*].action; result.json.steps[*].action

- 阶梯结论：**exit 2 —— 字节级不同但归一化后相同 => 差异已被 N1–N4 完全解释**（isolated）；inplace 同为 exit 2。
- 一句话：**可编辑源（SVG）、预览位图（PNG）、`data_manifest.json`、`validation.json` 是逐字节可复现的；
  `result.json` 与两份报告的不稳定性 100% 来自时间戳 / 输出目录绝对路径 / 自引用哈希 / PDF 内嵌日期这四类，
  四类都已被逐字段点名。**

## 11. 未解决项（如实写）

1. 阶梯 0 未在本机达到；配方见 §8，未做的是「冻结时钟」那一步（本包选择保留审计时间戳）。
2. `figcheck_report.json.dir` / `mapcheck_report.json.dir` 仍是绝对路径，未改脚本。
3. 本轮只在 Windows 10 + Python 3.13.9（本机实测） 上实测；Linux 上 PDF 由哪个库写 `/CreationDate` 需重测（N4 规则本身与库无关）。
4. 未测并发（两个进程同时写同一个输出目录）。
