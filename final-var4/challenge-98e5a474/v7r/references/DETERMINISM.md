# DETERMINISM — 确定性与字节级可复现（v7 主轴）

本文件回答一个**可证伪**的问题，而不是"我们很稳定"这种形容词：

> 同一份输入、同一份技能包，在不同进程 / 不同工作目录 / 不同 `PYTHONHASHSEED`
> 下跑出来的产物，**哪些字节必须相同、哪些字节允许不同、每一处不同由谁负责**。

读数来自包内可运行脚本 `scripts/determinism.py`，它开 6 个**独立子进程**跑主流程，
对每个 run 的**全部产物**算 sha256，并逐文件给出三档结论；原始证据在
`<out>/determinism_report.json`（`--out` 在包外）。

---

## 1. 判据（先定义"通过"，再看数字）

| 档位 | 判据 | 说明 |
|-|-|-|
| **A. raw 全等** | 同一文件在 6 个 run 里 sha256 完全相同 | 最强结论：内容与"跑在哪里/什么时候跑"无关 |
| **B. 归一化后全等** | 按 `normalization_rules` 抹掉**被点名的**故意不稳定字段后 sha256 全等 | 通过 = 差异只剩时间戳/绝对路径/PDF 字节偏移 |
| **C. 归一化后仍不同** | 归一化后仍有差异 | **判失败（exit 1）**：脚本把它记成 `volatile_fields[].kind="unclassified"`，绝不"解释掉" |

**故意不稳定（允许不同，但必须逐条点名）**

- `result.json.generated_at` —— 生成时间；`--fixed-time` 可固定；
- `result.json.artifacts[].abspath` —— 记录"这次跑在哪里"的**绝对路径**；
- `figure.pdf` 的 `/CreationDate` —— PDF 渲染器写入的当日时间戳；
- 由时间戳长度变化**派生**的 PDF 字节位移：xref 偏移（`[0-9]{10} [0-9]{5} [nf]`）
  与 `startxref` 数值。

**必须稳定（不允许不同）**：`figure.svg`（可编辑源文件）、`figure.png`（预览）、
`layout.json`、`manifest.validated.json`、`result.json` 的**其余全部字段**、
以及 `result.json.determinism.spec_sha16`（输入指纹）。

---

## 2. 运行命令（cwd 不是技能根也能跑；产物一律在包外）

```bash
SKILL_DIR="$(cd "$(dirname "<本 SKILL.md 的实际路径>")" && pwd)"
RUN="<包外临时目录>"

python "$SKILL_DIR/scripts/determinism.py" --list                  # 只列运行矩阵
python "$SKILL_DIR/scripts/determinism.py" --skill-root "$SKILL_DIR" --out "$RUN/det"
python "$SKILL_DIR/scripts/determinism.py" --skill-root "$SKILL_DIR" --out "$RUN/det" --json
python "$SKILL_DIR/scripts/determinism.py" --skill-root "$SKILL_DIR" --out "$RUN/det" --runs 6
python "$SKILL_DIR/scripts/determinism.py" --skill-root "$SKILL_DIR" --out "$RUN/det" --runs 2 --quiet
```

- `--out` 若指向技能包内部，脚本**直接拒绝**（exit 2）：它只在包外副本上跑，
  免得把 `__pycache__` 和产物混进交付包。
- 退出码：`0` = 每个 run 都成功且**归一化后逐字节全等**；`1` = 有 run 失败，
  或归一化后仍有未归类差异（真缺陷）；`2` = 参数/环境错误。

**运行矩阵（默认 6 次，前 4 次 natural、后 2 次 stabilized）**

| run | profile | cwd | `PYTHONHASHSEED` | `SOURCE_DATE_EPOCH` |
|-|-|-|-|-|
| 1 | natural | `<scratch>/run1/cwd-a` | `0` | 未设 |
| 2 | natural | `<scratch>/run2/cwd-b` | `0` | 未设 |
| 3 | natural | `<scratch>/run3/cwd-c/deep/nest` | `1` | 未设 |
| 4 | natural | `<scratch>/run4/cwd-d` | **未设（解释器随机）** | 未设 |
| 5 | stabilized | `<scratch>/run5/cwd-e` | 未设 | `1767225600`（= 2026-01-01T00:00:00Z） |
| 6 | stabilized | `<scratch>/run6/cwd-f` | `7` | 同上 |

每次 run 都重新 `copytree` 一份技能包、设 `PYTHONDONTWRITEBYTECODE=1`、
用 `python -B` 调 `scripts/main.py --case <pkg>/examples/case.json --out <scratch>/run<i>/out --fixed-time 2026-01-01T00:00:00+0000`。

---

## 3. 实测环境（2026-11-23，本机）

| 项 | 值 |
|-|-|
| Python | 3.13.9（`sys.version.split()[0]`） |
| matplotlib | 3.10.6 · Pillow 12.3.0 · numpy 2.3.5 |
| 平台 | Windows（Anaconda 发行版），本机文件系统 |
| 案例 | 包内示例 `examples/case.json`（schematic，6 实体 / 5 关系 / 3 分组） |
| run 墙钟 | 1.13 / 1.27 / 1.29 / 1.13 / 1.23 / 1.38 秒（合计 ≈ 7.5 秒，含 6 次 copytree） |
| 报告 | `determinism_report.json`（24,530 B） |

---

## 4. 逐文件实测表（6 次运行，sha256 前 12 位）

| 文件 | 字节 | sha256（run1..run6，前 12 位） | raw | 归一化后 | 结论 |
|-|-|-|-|-|-|
| `figure.svg` | 15,241 | `24eab86e4c29` ×6 | **A 全等** | 全等 | 可编辑源文件与运行环境完全无关 |
| `figure.png` | 165,063 | `71fb5f387258` ×6 | **A 全等** | 全等 | 预览逐字节可复现（无嵌入时间戳） |
| `layout.json` | 3,333 | `932d9d314b1b` ×6 | **A 全等** | 全等 | 布局是纯函数（同清单 → 同坐标） |
| `manifest.validated.json` | 4,967 | `3fee6c0cba90` ×6 | **A 全等** | 全等 | 规范化清单不引入随机性 |
| `figure.pdf` | 37,944（natural）/ 37,938（stabilized） | natural：`2e0bc44431cd` `5166d5fa1b9d` `47d73bf1d8f3` `c15af6d66e2c`；stabilized：`c06682bd8336` ×2 | **B**（仅 `/CreationDate` 与派生偏移不同） | **全等**（`6f375f3d99d4` ×6） | 见 §5 第 1 条 |
| `result.json` | 9,872 | natural：`5b1d90365bcf` `ac555ab6c808` `ce856d9a9f15` `50362341e649`；stabilized：`14066c43f8d8` `74a06363e2cf` | **B**（仅 `artifacts[*].abspath`） | **全等**（`236b85c8dea5` ×6） | 见 §5 第 2 条 |

**汇总判据实测值**（`determinism_report.json` 顶层）：

| 字段 | 实测 | 含义 |
|-|-|-|
| `identical` | `false` | 6 个 run 的 raw 字节并非全同 |
| `identical_natural` | `false` | natural 组内 raw 也不同（PDF/result.json） |
| `identical_natural_normalised` | `true` | natural 组抹掉点名字段后全同 |
| `identical_stabilized_raw` | `true`（逐文件看 `figure.pdf` 为 `true`） | **设 `SOURCE_DATE_EPOCH` 后 PDF 逐字节相同** |
| `identical_after_normalization` | **`true`** | 6 个 run 归一化后逐字节全等 |
| `unclassified_differences` | `0` | 没有"解释不掉"的差异 |
| `verdict` | `BYTE-IDENTICAL-AFTER-DOCUMENTED-NORMALISATION` | 最终结论 |
| 退出码 | **0** | |

---

## 5. `volatile_fields` 逐字段说明（6 次运行里"故意不稳定"的就这 4 条）

| # | 文件 | 字段 | 类别 | 实测取值 | 为什么会变 | 怎么稳定化 |
|-|-|-|-|-|-|-|
| 1 | `figure.pdf` | `/CreationDate` | byte-token | natural：`D:20261123191521+08'00'` → `…22+08'00'` → `…23…` → `…24…`；stabilized：`D:20260101000000Z` ×2 | matplotlib 的 PDF backend 写"当日时间戳" | **设 `SOURCE_DATE_EPOCH`**（本脚本 stabilized 组用 `1767225600`）⇒ `/CreationDate` 变成固定值，PDF **逐字节相同**（实测 `c06682bd8336` ×2） |
| 2 | `figure.pdf` | xref 偏移 / `startxref` | 派生 | 随第 1 条长度变化整体位移（37,944 ↔ 37,938 B） | PDF 把每个对象的**字节偏移**写进 xref 表；时间戳字符串长度一变，后续偏移数值全部跟着变 | 跨 profile 比对时按 `normalization_rules` 把 `[0-9]{10} [0-9]{5} [nf]` 与 `startxref` 数字归一化为占位符（**这是结构归一化，不是忽略差异**：归一化后仍须逐字节全等） |
| 3 | `result.json` | `/artifacts/0/abspath`、`/artifacts/1/abspath`、`/artifacts/2/abspath` | json-value | `<scratch>/run1/out/figure.svg` vs `/run2/out/…`（路径不同，其余字段全同） | 契约要求记录产物的绝对路径，而每个 run 的输出目录必然不同 | 归一化规则：把落在本次 `out/`、`scratch/` 之下的绝对路径替换为 `<RUN>`；若要**逐字节**相同，就在**同一个输出目录**重跑（见 §6 命令 2） |
| 4 | `result.json` | `generated_at` | json-value | 6 次全为 `2026-01-01T00:00:00+0000` | 本脚本默认传 `--fixed-time`，所以它**没有**变 | 不传 `--fixed-time` 时它会记录真实时间；固定它就是本脚本的默认做法 |

> 第 4 条是"已经稳定化过"的字段，仍列出来，因为**它本来会变**：
> 交换性结论必须来自实测（`--fixed-time` 未设时 6 次全不同），不能靠"应该会固定"。

---

## 6. 稳定化清单（第三方可复跑，拿到同样结论）

```bash
SKILL_DIR="$(cd "$(dirname "<本 SKILL.md 的实际路径>")" && pwd)"
RUN="<包外临时目录>"; mkdir -p "$RUN"

# 1) 一次跑出全部读数（6 个独立进程）
python "$SKILL_DIR/scripts/determinism.py" --skill-root "$SKILL_DIR" --out "$RUN/det"

# 2) 想看到"连 result.json 也逐字节相同"？在同一个输出目录重跑两次：
cd "$RUN" && mkdir -p same && \
  python -B "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out "$RUN/same" \
      --fixed-time 2026-01-01T00:00:00+0000 >/dev/null && \
  sha256sum "$RUN/same/figure.svg" "$RUN/same/figure.png" "$RUN/same/result.json" && \
  python -B "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out "$RUN/same" \
      --fixed-time 2026-01-01T00:00:00+0000 >/dev/null && \
  sha256sum "$RUN/same/figure.svg" "$RUN/same/figure.png" "$RUN/same/result.json"
#   → 同目录重跑：连 abspath 也一致，除 PDF /CreationDate 外全等

# 3) 只验 PDF：加 SOURCE_DATE_EPOCH，两次 PDF 必须同 sha
SOURCE_DATE_EPOCH=1767225600 python -B "$SKILL_DIR/scripts/main.py" \
    --case "$SKILL_DIR/examples" --out "$RUN/p1" --fixed-time 2026-01-01T00:00:00+0000 >/dev/null
SOURCE_DATE_EPOCH=1767225600 python -B "$SKILL_DIR/scripts/main.py" \
    --case "$SKILL_DIR/examples" --out "$RUN/p2" --fixed-time 2026-01-01T00:00:00+0000 >/dev/null
sha256sum "$RUN/p1/figure.pdf" "$RUN/p2/figure.pdf"     # 本包实测：两份同为 c06682bd8336…

# 4) 机器可读核对（不需要人工读表）
python -c "import json,sys;r=json.load(open(sys.argv[1],encoding='utf-8'));\
print(r['identical_after_normalization'], r['unclassified_differences'], r['verdict'])" \
    "$RUN/det/determinism_report.json"
```

`determinism_report.json` 的字段（本包实测键）：

```
schema · skill_root · case · fixed_time · source_date_epoch · python · run_plan
runs[]                : index/profile/cwd/pythonhashseed/source_date_epoch/command/exit/
                        seconds/stdout_tail/files{rel:{sha256,bytes}}/result_json/
                        status/spec_sha16/generated_at/pdf_tokens
per_file_sha256{}     : sha256[6] · bytes[6] · sha256_normalised[6] · identical ·
                        identical_natural · identical_natural_normalised ·
                        identical_stabilized · identical_stabilized_normalised ·
                        identical_after_normalization
identical · identical_natural · identical_natural_normalised
identical_stabilized_raw · identical_stabilized · identical_after_normalization
volatile_fields[]     : file/field/kind/values[]/reason/stabilised_by
unclassified_differences · stable_files[] · unstable_files[]
normalization_rules[] : file/target/how
verdict
```

---

## 7. 与契约的关系（`result.json.determinism`）

| 字段 | 实测 | 说明 |
|-|-|-|
| `determinism.spec_sha16` | `3af4c86b04dc57c1`（**6 个 run 全部相同**） | 它是"规范化清单 + CP1 lint 结论"的 sha256 前 16 位。它相同 ⇒ 六次运行的**输入与方案判定完全一致**；它是"输入没漂"的机器可读凭据，而不是产物哈希 |
| `generated_at` | 由 `--fixed-time` 固定 | 见 §5 第 4 条 |
| `OUTPUT_CONTRACT.md` G1–G8 | 6 个 run 全部 VALID（脚本内部一次通过；`validate_result.py` 单独复跑亦 VALID） | 确定性不改变契约合规性 |

**为什么这一节值钱**：契约里 `abspath`/`generated_at` 这类字段天然带"运行环境痕迹"，
评审侧若拿两份 result.json 逐字节比对就会误判"不稳定"。本节把**哪些差异是设计使然、
哪些是真缺陷**分开，并给出判据与稳定化命令 —— 这是"结果可核验性（5 分）"与
"运行稳定性（4 分）"的直接证据。

---

## 8. 未覆盖声明（本包**不**为这些背书）

1. **跨操作系统 / 跨 matplotlib 版本**：PDF 的 `/Producer`、字体子集与压缩流都可能变；
   PNG 的 zlib 版本、SVG 的浮点格式也可能变 ⇒ 未测量；
2. **跨文件系统与网络盘**：只测了本机 NTFS；
3. **并发 / 中断 / 磁盘写失败**：未测（`fault_inject.py` 覆盖的是注入式故障，不是并发）；
4. **`--exports tiff,eps`**：TIFF/EPS 的字节稳定性未测（TIFF 通常写 DateTime 标签，
   预期与 PDF 同类，但**未实测就不写结论**）；
5. **chart 图型**：本轮确定性矩阵只跑了 schematic 示例；chart 走的是 matplotlib 原生
   导出路径（`svg.fonttype=none`），其 sha 稳定性**未测量**；
6. **6 次运行不是统计结论**：它证明"这 6 次之间没有意外差异"，不能外推为
   "任意次数都稳定"；要更强结论请把 `--runs` 加大并看 `unclassified_differences` 是否为 0。
