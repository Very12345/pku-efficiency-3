# DETERMINISM.md — 哪些字节是**故意**不稳定的，以及怎么把它稳定下来

> 本文件是本版（v7）主轴的可复核说明：**同输入 → 同字节**。
> 全部数字来自 `scripts/determinism.py` 的真实运行（本机 Windows 11 / Python 3.13.9 /
> python-pptx 1.0.2 / Pillow 12.3.0 / matplotlib 3.10.6），原始报告随包：
> `references/determinism_report.json`（默认模式）与
> `references/determinism_report-hashsalt.json`（固定 SVG 盐模式）。
> 两份报告中的本机绝对路径已替换为 `<PROBE_DIR>` / `<SKILL_DIR>` / `<CASE_DIR>` /
> `<PYTHON>` 占位符（`--redact-paths`）；**哈希、计数、布尔与观测值全部是实测原值**。

## 0. 为什么这个问题值得单独做一层

"再跑一次能不能得到同一份东西"在本题里不是洁癖，而是**结果可核验性**的一部分：
复核者拿到 `result.json` 与 `academic_deck.pptx` 后，如果重新跑一遍得到的哈希与之无关，
那么"可复跑出同一版式"这句话就无法用机器验证。反过来，只要能把**不稳定的每一个字节**
点名列出来并给出稳定化手段，可复现性就从"信心"变成"判据"。

三种强度，本包只承诺能被实测背书的那一种：

| 强度 | 判据 | 本包实测 |
|-|-|-|
| ① 原始字节一致 | 每次运行的产物 sha256 完全相同 | **False**（13 个产物中有 3 个含故意不稳定的字节，见 §3） |
| ② 规范化后一致 | 只按**写死在代码里的白名单**做规范化，其余差异一律算失败 | **True**（13/13，未解释差异 0） |
| ③ 稳定化后一致 | 探针**物理重写**不稳定部分（固定 zip 成员时间、去 `<dc:date>`、按序重命名 SVG id、规范化 JSON），再逐文件比对 | **True**（13/13 字节一致） |

## 1. 运行命令与退出码

```bash
SKILL_DIR="<SKILL.md 所在目录>"

# 默认：5 次运行，每次独立进程 + 不同 cwd + 不同 PYTHONHASHSEED，并产出稳定化副本
python "$SKILL_DIR/scripts/determinism.py" --out "<探针工作目录>" --runs 5 --stabilize

# 根因旋钮：把 matplotlib 的 svg.hashsalt 固定住（证明随机 id 的来源）
python "$SKILL_DIR/scripts/determinism.py" --out "<探针工作目录>" --runs 5 \
  --svg-hashsalt v7-fixed --stabilize

# 消除"输出目录身份"字段：全部运行写进同一个输出目录
python "$SKILL_DIR/scripts/determinism.py" --out "<探针工作目录>" --runs 3 --out-mode same-dir

# 报告要随包/入库时去掉本机绝对路径
python "$SKILL_DIR/scripts/determinism.py" --out "<探针工作目录>" --redact-paths
```

| 退出码 | 含义 |
|-|-|
| 0 | 全部子运行 exit 0，且规范化后一致（开了 `--stabilize` 时要求稳定化后**字节**一致） |
| 1 | 存在**未解释差异**，或规范化/稳定化后仍不一致 |
| 2 | 参数或输入错误（`--runs < 2`、`--seeds` 非法、case/spec 不可读、入口不存在） |
| 3 | 至少一次子运行失败（非零退出，或没写出 `result.json`） |

探针**不改动被探测的 Skill**：子进程一律带 `PYTHONDONTWRITEBYTECODE=1`，因此探测不会在技能
目录里留下 `__pycache__`；所有写入都落在 `--out` 指定的探针目录。

## 2. 报告结构（`determinism_report.json`）

| 键 | 含义 |
|-|-|
| `runs[]` | 每次运行的 `index / run_dir / cwd / pyhashseed / argv / exit_code / result_status / files` |
| `per_file_sha256` | 逐文件、逐次运行的**原始字节** sha256 |
| `per_file_canonical_sha256` | 逐文件、逐次运行的**规范化后** sha256 |
| `byte_identical_per_file` / `canonical_identical_per_file` | 两级判定，逐文件布尔 |
| `identical` / `identical_canonical` / `identical_stabilized` | 三个强度总判定（§0 表） |
| `volatile_fields[]` | `result.json` 里被**解释过**的不稳定字段：`pointer / kind / reason / observed / stabilization` |
| `volatile_files[]` | 容器级证据：zip 成员时间与成员载荷是否一致、SVG 的 `<dc:date>` 与 id 序列、PNG 是否有 `tIME` |
| `unexplained_diffs[]` | 命中不了任何白名单规则的差异；**非空即退出码 1** |
| `svg_id_sequences_stable` | SVG 元素 id 序列在各次运行间是否逐位相同（`--svg-hashsalt` 的判据） |

## 3. 逐字段实测：哪些是故意不稳定的

### 3.1 `result.json` 内的不稳定字段（实测 5 次，`volatile_fields` 共 5 条）

| JSON 指针 | 类别 | 为什么不稳定 | 实测观测值 | 稳定化 |
|-|-|-|-|-|
| `/run_meta/timestamp` | timestamp | `main._run_meta()` 写入开始时刻（`time.strftime`） | `2026-11-23T19:06:03+0800`、`…05+0800`、`…07+0800`、`…09+0800`、`…11+0800` | 稳定化副本替换为 `<volatile:timestamp>` |
| `/change_records/0/time` | timestamp | `main.run()` 起始记录 | `…19:06:02+0800` … `…19:06:10+0800`（5 次各不同） | 同上 |
| `/change_records/1/time` | timestamp | `main.run()` 结束记录 | `…19:06:04+0800` … `…19:06:12+0800` | 同上 |
| `/run_meta/duration_seconds` | duration | 墙钟耗时（示例案例实测 1.32–1.48 s） | `1.35 / 1.36 / 1.32 / 1.48 / 1.35` | 替换为 `<volatile:duration>` |
| `/charts/0/chart/file` | **out-dir identity** | `assetkit.make_chart` 返回的是写入 `--out` 的**绝对路径**，因此值随输出目录变化 | `…\<run-i>\chart-Fig_1.png`（i=0..4） | 稳定化副本把本次运行的 `--out` 前缀重写为 `<OUT>` |

`out-dir identity` 不是"随机"，而是**输出位置本来就是输入的一部分**：判据是"把各次运行自己的
`--out` 前缀改写掉之后，值是否完全相等"。探针按这条判据验证（Windows 下 `os.path.join` 会
产生 `a/b\run-0` 这样的混合分隔符，所以两侧先统一成 `/` 再比），验证不过就落进
`unexplained_diffs` 而非被放过。用 `--out-mode same-dir` 可以让这一类**整类消失**（实测
`volatile_fields` 从 5 条降到 4 条，只剩时间戳与时长）。

> **由此暴露的一条真实限制（未在本轮修改脚本）**：`result.json` 的 `charts[].chart.file`
> 携带本机绝对输出路径，使交付物无法做到"位置无关"。见 §6 未解决项。

### 3.2 `academic_deck.pptx`：容器成员时间戳（实测）

| 项 | 实测 |
|-|-|
| 原始字节一致 | **False**（5 次运行哈希各异） |
| 成员载荷一致 | **True**（`member_payloads_identical: true`：所有 zip 成员内容逐字节相同） |
| 观测到的成员时间 | `2026-11-23T19:06:04`、`…06`、`…08`、`…10`、`…12`（随运行变化） |
| 根因 | `python-pptx` 写包时走 `zipfile.ZipFile.writestr(<str name>)`，Python 用**当前本地时间**构造该成员的 `ZipInfo` |
| 稳定化 | 用固定 `date_time=(1980,1,1,0,0,0)` 重写容器（保留成员顺序、压缩方式、属性）→ 稳定化后 5/5 字节一致 |
| 规范化判据 | "成员名 → 成员 sha256"映射（排除时间戳），5 次一致 |

### 3.3 `chart-Fig_1.svg`：渲染时间 + 随机元素 id（实测）

| 项 | 实测 |
|-|-|
| `<dc:date>` | 每次运行都不同，例：`2026-11-23T19:06:04.003111`、`2026-11-23T19:06:05.891479` |
| 元素 id 数 | 每次 83 个 |
| 默认模式下 id 序列 | 与第 1 次相比有 **12 个位置不同**，样本：`ma34cbb377e`、`m58785d8163`、`p032a41b656` |
| `--svg-hashsalt v7-fixed` 后 | id 序列**逐位相同**（`id_positions_differing: 0`，`svg_id_sequences_stable: true`） |
| 固定盐后再去掉 `<dc:date>` | 5/5 运行哈希完全相同（`62f4261d822d4055` ×5） |
| 根因（源码级） | `matplotlib.backends.backend_svg.RendererSVG._make_id`：`salt = mpl.rcParams['svg.hashsalt']`，为 `None` 时退化为 `str(uuid.uuid4())` —— **每次渲染一个新 uuid** |
| 稳定化（事后） | 去 `<dc:date>` 内容 + 按文档顺序把 id 重命名为 `L0…L82`（同时改写 `#id` / `url(#id)` 引用，长 id 先替换避免前缀冲突）→ 稳定化后 5/5 字节一致 |

### 3.4 PNG：7 张预览 + 1 张重建图（实测）

| 项 | 实测 |
|-|-|
| 原始字节一致 | **True**（`preview-approx-cover.png` + `preview-approx-001..006.png` + `chart-Fig_1.png` 共 8 张，5 次运行逐字节相同） |
| `tIME` 块 | **无**（Pillow 与 matplotlib Agg 默认都不写时间块；探针仍会检测并在存在时剔除） |

### 3.5 其余文本产物（实测）

`evidence_mapping.md`、`evidence_map.json`：5 次运行**逐字节相同**（不受时间戳影响；
证据表与 json 由同一 spec 生成）。

## 4. 实测场景表（三组数字，全部真跑）

| 场景 | 命令要点 | 运行数 | `identical` | `identical_canonical` | `identical_stabilized` | 未解释差异 | 退出码 |
|-|-|-|-|-|-|-|-|
| A 默认（逐运行独立输出目录） | `--runs 5 --stabilize` | 5 | False | **True** | **True** | 0 | **0** |
| B 同目录 | `--runs 3 --out-mode same-dir --stabilize` | 3 | False | **True** | **True** | 0 | **0** |
| C 固定 SVG 盐 | `--runs 5 --svg-hashsalt v7-fixed --stabilize` | 5 | False | **True** | **True** | 0 | **0** |
| D 探针自证（两次独立探测） | `--no-timestamp` ×2 | 3+3 | — | 两次的 `per_file_canonical_sha256` **完全相同** | — | — | 0 |
| E 阴性对照（检测器自检） | `--entry <一个会写随机数的入口>` | 3 | False | False | — | **1 条（`/roll`，unclassified）** | **1** |
| F 模板适配分支 | 先生成示例模板再 `--runs 5 --stabilize` | 5 | False | **True** | **True** | 0 | **0** |

场景条件（A/C）：独立进程；cwd 交替为 `…/run-i` 与 `…/cwd-alt-i`；
`PYTHONHASHSEED` = `0,1,2,0,1`；子进程 `PYTHONDONTWRITEBYTECODE=1`。

E 的作用是证明"探针不是永远说 OK"：把入口换成一个写随机数的脚本后，
`unexplained_diffs` 立刻点名 `/roll` 且退出码变 1，同时**稳定产物 `artifact.txt` 仍被判为一致**
（不会因为一个文件坏就把整份报告说成"全都不稳定"）。

## 5. 交付侧建议（把判据落到日常）

1. **固定输出目录**：跨机/跨轮对比用同一个 `--out`，`out-dir identity` 类差异自然消失；
2. **需要分发稳定副本时**跑一次 `--stabilize`，把 `stabilized/run-0/` 当作"可对拍的版本"：
   它与任何一次同输入运行稳定化后的哈希相同（实测）；
3. **不要把 `identical=False` 说成"不确定"**：报告会逐项指出哪 3 个文件、哪 5 个字段、为什么；
4. 复核别人的包时，只需 `--redact-paths --no-timestamp` 两次运行，比 `per_file_canonical_sha256`
   即可判断"是不是同一套产物"。

## 6. 未覆盖 / 未解决（如实声明）

1. **只覆盖本包 13 个产物 × 示例案例**：平台 3 个正式案例未在本地跑（其材料为 PDF 时会走
   `assetkit` 的 PDF 分支，该分支的字节稳定性未测）。
2. **未跨机器 / 未跨 Python 版本 / 未跨 zlib 版本**：zip 的压缩字节可能随 zlib 版本变化，
   因此"稳定化后一致"的结论限定在同一解释器与同一压缩库；跨环境只承诺
   "成员载荷一致"这一级（§3.2 的规范化判据）。
3. **未测 LibreOffice/PowerPoint 真渲染**：本机无这两个引擎，预览恒为 PIL 近似；
   `--svg-hashsalt` 只对 matplotlib 生成的 SVG 有效。
4. **`result.json` 的 `charts[].chart.file` 携带本机绝对输出路径**（§3.1）：这是被实测暴露的
   真实限制。本轮**没有改** `assetkit.py` / `main.py`（既有脚本逐字节保持不变），
   只在规范化的 `out-dir identity` 规则里如实记录，并用 `--out-mode same-dir` 给出规避方式。
5. **探针不修补上游**：它只写稳定化副本、不重写交付目录，因此稳定化产物需要交付方自己决定
   是否替换（替换会改变交付字节，属于交付决策而非探测结果）。

## 7. 稳定性设计的三个取舍（为什么这样实现）

1. **白名单写死在代码里，而不是"把观察到的差异都吸收掉"**：后者会让探针永远说 OK，
   等于没有判据。任何不在白名单里的差异都会进 `unexplained_diffs` 并让退出码变 1。
2. **顺序重命名而不是"给 matplotlib 打补丁"**：稳定化只依赖"id 出现顺序稳定"这一条弱假设，
   对任何"按内容生成随机 id"的工具都适用；`--svg-hashsalt` 是**根因**手段，
   用于证明随机来源，不替代通用规范化。
3. **报告自身可复现但不算作产物**：`per_file_sha256` 记录的是不稳定字节，所以报告本身
   天然逐次不同（实测：两次探测的报告 sha256 不同）；可复现的是
   `per_file_canonical_sha256` 与稳定化哈希（实测：两次探测完全相同）。
   报告不参与产物集合的比对，避免自指。
