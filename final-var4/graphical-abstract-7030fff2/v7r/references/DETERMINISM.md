# DETERMINISM.md — 字节级可复现性：判据、实测表与稳定化办法

> 本文件回答一个只能用实验回答的问题：**同一份输入，跑两次，产物到底一不一样？**
> 全部数字来自 `scripts/determinism.py` 在**包外临时副本**上的真实运行
> （Windows / Python 3.13.9 / matplotlib 3.10.6，2026-11-23）；机器可读原件见
> [`../examples/determinism_report.example.json`](../examples/determinism_report.example.json)。
> **本文件不证明**跨机器、跨 Python/绘图库版本的字节一致（见 §7），也不把"时间戳不同"
> 说成"不确定性" —— 哪些是**故意**不稳定的字段，逐条列在 §5。

---

## 1. 三层判据（本 Skill 承诺的等级）

| 等级 | 判据 | 实测结论（本机） |
|-|-|-|
| **L0 `raw`** | 每个产物文件 `sha256` 全等，含时间戳字段 | **不成立**（`result.json` / `render_log.json` / `*.pdf` 三个文件含真实时间或调用路径） |
| **L1 `canonical`** | 掩掉**已声明**的易变字段后全等 | **成立**：8/8 文件一致，0 处未解释差异 |
| **L2 `structural`** | `result.json` 的语义字段逐项相等 + `audit.determinism_probe.spec_sha16` 相等 | **成立**：5 次运行 `spec_sha16` 全为 `9bcb54b29fe658d4` |

默认判据是 **L1**（`--fail-on normalized`）：`exit 0` 当且仅当"掩码后所有产物一致"。
`--fail-on raw` 是**更严的等级**，本包在本机实测**故意**返回 `exit 1`（见 §5）；
`--fail-on none` 只采数据，永远 `exit 0`。

**运行命令**（cwd 任意；`$SKILL_DIR` = 本包根，`--out` 必须在包外）：

```bash
# 默认：3 次，3 种 cwd 形态（skill / 空临时目录 / 案例目录），3 种 PYTHONHASHSEED
python "$SKILL_DIR/scripts/determinism.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/det

# 加严到 5 次、5 个种子（含"不设置"），并打印报告
python "$SKILL_DIR/scripts/determinism.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/det \
       --runs 5 --hashseeds 0,1,42,12345,- --json

# 要求逐字节相同（预期 exit 1，用来复核 §5 的易变清单）
python "$SKILL_DIR/scripts/determinism.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/det --fail-on raw
```

退出码：`0` = 达到所选等级；`1` = 未达到（报告逐文件列出哪一层不一致）；`2` = 用法/环境错误
（`--out` 落在包内、案例不存在、`--runs` 越界）。

---

## 2. 实测：逐产物比对（5 次运行）

命令：`--runs 5 --hashseeds 0,1,42,12345,-`（cwd 循环 skill / 空目录 / 案例目录），
案例 `examples/case.json`（sha256 `8396f5599ac85d65…`），报告 `seconds_total = 11.67 s`。

| 产物 | 字节 | 类型 | `raw` 全等 | `normalized` 全等 | 首次运行 sha256（前 16） |
|-|-|-|-|-|-|
| `spec.json` | 42,986 | text | ✅ | ✅ | `722c493b27c6b9be` |
| `content.json` | 6,979 | text | ✅ | ✅ | `d6825571d33eaa41` |
| `audit.json` | 2,169 | text | ✅ | ✅ | `653e22cc61602082` |
| `<case>_graphical_abstract.svg` | 32,455 | text | ✅ | ✅ | `370a037e2bafb9ee` |
| `<case>_graphical_abstract.png` | 397,555 | binary | ✅ | ✅ | `23e992772bdaf934` |
| `result.json` | 6,709 | text | ❌ | ✅ | `2959001ec24b4683` |
| `render_log.json` | 645 | text | ❌ | ✅ | `9a94df51915c6e61` |
| `<case>_graphical_abstract.pdf` | 148,129 | pdf | ❌ | ✅ | `50efac5cc8368a03` |

**读数方式**：`raw ❌ / normalized ✅` 的每一行，都在 §5 里有对应的**已声明**易变项；
`normalized ❌` 才是真问题 —— 本次为 0 行，`unexplained_differences = 0`。

运行矩阵（同一份输入）：

| 运行 | cwd | `PYTHONHASHSEED` | 退出码 | 墙钟 |
|-|-|-|-|-|
| run0 | `<skill-root>` | `0` | 0 | 2.29 s |
| run1 | `<out>/cwd1`（空目录） | `1` | 0 | 2.04 s |
| run2 | `<case-dir>` | `42` | 0 | 2.33 s |
| run3 | `<skill-root>` | `12345` | 0 | 2.36 s |
| run4 | `<out>/cwd4`（空目录） | 未设置 | 0 | 2.56 s |

⇒ cwd 与哈希种子**都没有进入产物**：8 个文件在 L1 层全部一致，`spec_sha16` 五次相同。
（这也是"脚本自定位"的可测后果：`main.py` 的相对路径一律以 `case.json` / `--out` 为基准解析。）

---

## 3. 三层是怎么算出来的（口径，不是黑箱）

1. 每次运行：独立子进程 `python -B <sandbox>/scripts/main.py --case <abs> --out <run_i>`；
   环境里显式设置 `PYTHONHASHSEED`，并设 `PYTHONDONTWRITEBYTECODE=1`（不在任何地方留 `.pyc`）。
2. 跑完后遍历该次运行目录的**全部文件**（不只交付物），记录 `sha256` 与字节数。
3. 对每个文件再做一次**归一化哈希**：文本文件按掩码规则改写后求 sha256；PDF 做字节级掩码。
4. 跨运行比较：相对路径集合必须相同；逐文件比较 `raw` 与 `normalized` 两种哈希。
5. 另做**字段级**比对：解析每次的 `result.json`，把 JSON 树摊平成 `路径 → 值`，
   逐个路径找差异，并按 §5 的规则表**分类**；分类不上的一律记为 `UNEXPLAINED`（会直接导致
   `verdict=unstable` 与 `exit 1`）。

归一化规则（写在报告 `normalization.rules` 里，可复核）：

| 规则 | 作用对象 | 替换为 |
|-|-|-|
| ISO-8601 时间戳 | 全部文本产物 | `<TS>` |
| 运行目录 / 技能目录 / 案例目录（同时匹配 JSON 里的反斜杠转义写法） | 全部文本产物 | `<RUN>` / `<SKILL>` / `<CASE>` |
| `/CreationDate`、`/ModDate`、`/ID` | PDF 字节 | `D:<TS>` / `[<X> <X>]` |

---

## 4. 报告怎么读（`determinism_report.json`）

| 键 | 含义 |
|-|-|
| `runs[]` | 每次运行的 `cwd` 标签、`pythonhashseed`、`exit`、`seconds`、`argv`（路径已符号化） |
| `per_file_sha256` | 文件 → 每次运行的 `sha256` 列表（**未掩码**，可直接对拍） |
| `per_file{}` | 文件 → `bytes / kind / raw_identical / normalized_identical` |
| `identical{raw, normalized, per_file_*}` | 两个等级的总体结论 + 逐文件布尔 |
| `volatile_fields[]` | 字段级差异，含 `class`（`V1`/`V2`/…）、`values_per_run`、`why`、`stabilized_by` |
| `volatile_rules[]` | 已声明易变项的完整规则表（就是 §5 的表） |
| `unexplained_differences[]` | **分类不上的差异**（=真实不确定性）；非空即 `verdict=unstable` |
| `structure_probe` | 各次 `audit.determinism_probe.spec_sha16` 与是否全等 |
| `verdict` | `byte-stable` / `canonical-stable` / `unstable` |
| `checks` | 汇总计数：比较了几个文件、几个 raw/normalized 一致、未解释几条、总耗时 |

---

## 5. 哪些字段是**故意**不稳定的，怎么稳定化

| 编号 | 位置 | 类型 | 为什么故意不稳定 | 稳定化办法 | 实测证据 |
|-|-|-|-|-|-|
| **V1** | `result.json: generated_utc` | 真时间戳 | 契约要求"这次运行是什么时候产生的"，属于溯源信息 | L1 掩码为 `<TS>`；**不要**把它改成常量（会破坏溯源） | 5 次运行分别为 `…T11:40:22Z`…`…T11:40:26Z` |
| **V2** | `result.json: change_records[*].ts` | 真时间戳 | 变更记录的时间必须真实 | 同上 | `2026-11-23T19:40:22+0800` / `…:24` / `…:26` |
| **V3** | `*.pdf: /CreationDate`（`/ModDate` 同族） | 渲染库元数据 | matplotlib 的 PDF 后端把当前时间写进文件头 | ① L1 掩码；② **真要消除**：设 `SOURCE_DATE_EPOCH=<unix 秒>`（实测见下） | `SOURCE_DATE_EPOCH=1700000000` 下两次 PDF **逐字节相同**（`3e00d54352b170c0…`，148,123 B），头里为 `D:20231114221320Z` |
| **V4** | `render_log.json: requested.png/pdf` | 调用者自己的输出路径 | 每次运行的 `--out` 不同（正是被测变量） | L1 掩码为 `<RUN>`；该文件是**透明性中间产物**，不在 `deliverables` 里，交付物本身不含绝对路径 | 两次运行该字段分别指向 `run0/…`、`run1/…` |

三条**没有**被列为易变、因而必须真的一致的东西（也就成了本轴的硬判据）：
图面规格 `spec.json`、抽取结果 `content.json`、自查报告 `audit.json`、
可编辑源文件 `.svg`、栅格预览 `.png`。其中 `.png` 是二进制且含 39 万字节 —— 它一致，
说明"渲染 → 编码"整条链没有隐藏的随机源。

---

## 6. 阴性对照：这个判据是**可被证伪**的

一个"永远返回一致"的检查器没有价值。为了证明它会抓到真问题，在一份**包外副本**里
把 `scripts/common.py` 的 `write_json()` 改成给每个 dict 注入一个随机数（`_negctrl`），
其余完全不动：

```bash
# 仅用于对照，不属于交付内容；在包外副本上做
python "$SKILL_DIR/scripts/determinism.py" --case <case.json> --out /tmp/det-neg
```

| 项目 | 实测值 |
|-|-|
| `verdict` | **`unstable`** |
| 退出码 | **1** |
| `checks.raw_identical_files` | **2 / 8** |
| `checks.normalized_diff_files` | `audit.json`、`content.json`、`render_log.json`、`result.json`、`spec.json`（5 个） |
| `unexplained_differences` | **1**：`result.json:_negctrl`，三次取值 `0.8320856471072144` / `0.4523033340273882` / `0.9031130976072681` |

⇒ 注入的随机性被**逐层抓出**（文件级 + 字段级），且被正确归类为"未解释"。

---

## 7. 边界与未覆盖（如实声明）

- **不承诺跨机器/跨版本字节一致**：`spec.json` 与 `content.json` 只依赖输入与纯 Python 逻辑，
  跨平台预期一致；但 `.png` 由 matplotlib/Pillow 编码，`.pdf` 由 matplotlib PDF 后端生成，
  **换库版本或换 OS 就可能变字节**（本包的 L1 判据是"同一台机器、同一套依赖、同一份输入"）。
- **字体参与 .png 的像素**：本机探测到 `Microsoft YaHei / SimHei / Arial / Segoe UI`；
  换机器字体集合不同 → `.png` 会不同，这是**环境差异**而非不确定性。
  `preview.py` 在无字体时的回退（占位框）同样会被如实记录，见 `references/DEGRADE-MATRIX.md`。
- **`render_log.json` 记录的是 `--out` 的绝对路径**（调用者自己的目录）。它不进 `deliverables`、
  不会被当成交付路径；但如果你把它当交付物外发，请先掩码。
- **并行/并发不在本轴**：本脚本串行跑 N 次；两个进程同时写同一个 `--out` 的行为未测。
- **不测"跨平台换行符"**：所有写文件都走 `newline="\n"`（Windows 上也不产生 CRLF）；
  这一点由 `common.write_json/write_text` 保证，本脚本的实测覆盖了文本产物 sha256 一致。
- 本轴**不覆盖**平台侧（容器挂载、配额、超时）—— 那些见 `references/DEGRADE-MATRIX.md` 的
  未覆盖声明与 `references/FAULT-MATRIX.md` 的四形态注入。

---

## 8. 在真实交付里怎么用

1. **改完任何脚本后**先跑 L1：`--runs 3` 约 4–12 s（含 3 次完整出图），远低于 900 s 预算。
2. `exit 0` 之后，再看 `unexplained_differences` 是否为空 —— 空的才算通过，退出码只是入口。
3. 如果你需要把产物交给别人做**逐字节**对拍，按 §5 稳定化：
   `SOURCE_DATE_EPOCH`（PDF）+ 掩码 `generated_utc` / `change_records[*].ts`（`result.json`）。
4. 想复核"证据不是自述"：直接比对 `per_file_sha256` 里每次运行的哈希；
   报告里的路径已符号化，可直接贴给第三方。
