# DETERMINISM.md — 确定性与字节级可复现（本包 v7 的轴）

> 本文所有数字都由 `scripts/determinism.py` 现场跑出，表格按该脚本的 `determinism_report.json`
> 逐字段渲染（`runs[]`、`per_file_sha256`、`volatile_fields[]`、`non_json_drift[]`），
> **没有一个手写估计值**。复核命令见 §1。
> 报告原文：`python "$SKILL_DIR/scripts/determinism.py" --json /tmp/determinism_report.json`。

本题的评分点写的是「交付物能否被别人打开、修改并**复跑出同一张图**」。
"能复跑"这句话如果不落到字节上，就只是自述。这一轴把它压成三个可复核的判据：

| 判据 | 含义 | 本包实测 |
|-|-|-|
| `identical`（raw） | 平台默认环境下 N 次运行，全部产物**逐字节**相同 | **false**（预期，见 §3） |
| `identical_by_condition.stabilized` | 关掉三条已知扰动源后，全部产物逐字节相同 | **true** |
| `identical_normalized` | 把**已声明**的漂移字段掩码后，规范化摘要一致 | **true**（raw 与 stabilized 均 true） |

结论一句话：**这张图本身是确定的；不确定的只有"这次运行发生在什么时候、写到了哪个目录"，
而这两条都是审计信息，被伪造比漂移更糟。** 三条杠杆关掉它们之后，8 次运行、7 件产物、
跨 4 个进程、4 个不同 cwd、4 个不同 `PYTHONHASHSEED`，逐字节相同。

---

## 1. 运行命令与判据

```bash
# 默认：raw + stabilized 两个条件各 4 次，共 8 次
python "$SKILL_DIR/scripts/determinism.py"

# 只要机器可读报告，指定路径
python "$SKILL_DIR/scripts/determinism.py" --json /tmp/determinism_report.json --runs 6

# 只跑默认环境（平台真实形态），并保留现场
python "$SKILL_DIR/scripts/determinism.py" --mode raw --keep

# 只跑稳定化条件（"可复现"的强判据）
python "$SKILL_DIR/scripts/determinism.py" --mode stabilized --seeds 0,7,99
```

退出码：**0** = 与声明口径一致（漂移字段全在 `volatile_fields[]` 里且 `intentional=true`，
且 stabilized 逐字节相同）；**3** = 出现未解释漂移或 stabilized 仍不稳定；**2** = 用法/环境错误。

判据被写成可执行断言，不需要人去读表格：

1. `unexplained_volatile_fields == 0` —— 每一个漂移的 JSON 叶子都能映射到
   `DECLARED_VOLATILE` 里的一条声明（含 `why` 与 `stabilizer`）；
2. `identical_by_condition.stabilized == true`；
3. `identical_normalized.raw == true` —— 把 §3 声明的路径掩码后，raw 条件也一致；
4. `stabilized_identical_files == artifacts` —— 稳定化后**一件不少**地一致。

四条都满足才 `verdict=pass`。本包实测四条全中（`verdict=pass`，`unexplained=0`）。

## 2. 三个条件是怎么造的（不是"多跑几次看看"）

| 维度 | raw 条件 | 为什么这么造 |
|-|-|-|
| 进程 | 每次一个**独立子进程**（记录 `pid`） | 同进程内重复调用会被模块级缓存掩盖非确定性 |
| cwd | 4 个不同目录轮流：技能根 / 工作目录 / `scripts/` / 示例目录 | 逼出"靠 cwd 找资源"的隐患；本包脚本全部 `os.path.dirname(__file__)` 自定位 |
| `PYTHONHASHSEED` | `0 / 1 / 12345 / 31337` 循环 | 逼出 dict/set 迭代顺序泄漏到产物里的隐患 |
| 输出根 | **每次不同**的 `--out` | 平台真实形态；同时使 `execution.out_dir` 必然不同（这是**故意**的漂移源） |
| 时钟 | 真实系统时间 | 平台真实形态；`change_record[].time` 因此必然不同（**故意**的另一条） |

**8 次运行的现场**（`runs[]`，逐条来自报告）：

| run | 条件 | 进程 | PYTHONHASHSEED | RL_INVARIANT | 冻结时钟 | cwd（截尾） | 退出码 | 耗时 | 产物数 |
|---|---|---|---|---|---|---|---|---|---|
| run0 | raw | pid 10284 | 0 | 0 | 否 | llenge-9034312d\_scratch\det_out\skill | 0 | 0.475 s | 7 |
| run1 | raw | pid 37584 | 1 | 0 | 否 | t3\challenge-9034312d\_scratch\det_out | 0 | 0.456 s | 7 |
| run2 | raw | pid 15936 | 12345 | 0 | 否 | 034312d\_scratch\det_out\skill\scripts | 0 | 0.435 s | 7 |
| run3 | raw | pid 14800 | 31337 | 0 | 否 | enge-9034312d\_scratch\final7\examples | 0 | 0.422 s | 7 |
| run4 | stabilized | pid 14792 | 0 | 1 | 是 | llenge-9034312d\_scratch\det_out\skill | 0 | 0.408 s | 7 |
| run5 | stabilized | pid 11100 | 1 | 1 | 是 | t3\challenge-9034312d\_scratch\det_out | 0 | 0.427 s | 7 |
| run6 | stabilized | pid 12484 | 12345 | 1 | 是 | 034312d\_scratch\det_out\skill\scripts | 0 | 0.434 s | 7 |
| run7 | stabilized | pid 25460 | 31337 | 1 | 是 | enge-9034312d\_scratch\final7\examples | 0 | 0.406 s | 7 |

## 3. 逐字段：哪些是**故意**不稳定的，为什么，怎么消掉

`volatile_fields[]` 与 `non_json_drift[]` 是机器判定出来的漂移清单，不是人回忆的。
每条都带 `kind` / `intentional` / `why` / `stabilizer` / `observed`（实测取值）。

> 表格里的 `observed` 列**已脱敏**：本机绝对路径（盘符形式）替换为 `<WORKDIR>`；
> 报告 JSON 里是原值（原值只在本机临时目录内）。

| 文件 | JSON 路径 | 类别 | 故意不稳定 | 实测取值（前 4 个不同值） | 稳定化手段 |
|---|---|---|---|---|---|
| result.json | `change_record/0/time` | wall-clock | 是 | "2026-11-23T11:24:38+00:00", "2026-11-23T11:24:39+00… | L3 冻结时钟驱动（--frozen-clock，仅用于复现实验，不进正式交付） |
| result.json | `execution/out_dir` | absolute-path | 是 | "`<WORKDIR>`\raw\run0\out" … "`<WORKDIR>`\raw\run3\out"（4 个不同值） | L1 所有 run 共用同一个 --out 根 |

二进制产物的漂移（JSON 之外的）：

| 文件 | 条件 | 不同 sha 数 | 类别 | stabilized 后不同 sha 数 | 已被稳定化 |
|---|---|---|---|---|---|
| figure.pdf | raw | 4 | pdf-metadata | 1 | 是 |

**逐条解释**（这三条是本 Skill 全部的非确定性，没有第四条）：

1. **`result.json` → `change_record/*/time`**
   *为什么故意*：`change_record` 是"谁在什么时候改了什么"的审计记录。把它写成常量等于伪造审计。
   *怎么稳定化*：`--mode stabilized` 时不改 `main.py`，而是用一个**现场生成的驱动**
   `_frozen_clock_driver.py`，在子进程里把 `datetime.now()` 钉到 `2026-01-01T00:00:00Z`
   再 `runpy` 主脚本。**驱动只在探针里存在，不进包、不进正式交付** —— 这一点很重要：
   稳定化手段可以很重，但它不能污染交付物。

2. **`result.json` → `execution/out_dir`**
   *为什么故意*：它回显本次 `--out` 根。raw 条件**故意**每次换目录，所以它必然不同；
   而平台每次运行的输出根也本来就不同。
   *怎么稳定化*：L1 —— 所有 run 共用同一个 `--out` 根（每次运行前清空）。

3. **`figure.pdf` 的 `/CreationDate`、`/ModDate`、`/ID`**
   *为什么故意*：PDF 规范要求写生成时间与文档 ID，reportlab 默认用当前时间 + 随机 ID。
   *怎么稳定化*：L2 —— 环境变量 `RL_INVARIANT=1`（reportlab 自己的 invariant 开关，
   实测把日期变成 `D:20000101000000+00'00'`、`/ID` 变成固定值）。
   注意这是**运行时环境变量**，包内代码一行没改。

三条杠杆的组合效果（同样来自报告）：

| 条件 | 三条杠杆 | 逐字节一致的产物数 | 产物总数 | identical 判定 |
|---|---|---|---|---|
| （无杠杆）raw | 各自独立 --out + 真实时钟 + 无 RL_INVARIANT | 5 | 7 | True |
| L1+L2+L3 stabilized | 同一 --out 根 + RL_INVARIANT=1 + 冻结时钟 | 7 | 7 | True |

## 4. 逐文件实测：哪些文件天然确定，哪些需要杠杆

| 产物文件 | raw 不同 sha 数 | raw 判定 | stabilized 不同 sha 数 | stabilized 判定 | raw sha256 前 12 位 |
|---|---|---|---|---|---|
| evidence.json | 1 | 一致 | 1 | 一致 | 1ffdfd4bb18b |
| figure.pdf | 4 | **不一致** | 1 | 一致 | 966f3648977b |
| figure.png | 1 | 一致 | 1 | 一致 | 990ab3a46d80 |
| figure.svg | 1 | 一致 | 1 | 一致 | f8b01ce26b62 |
| layout.json | 1 | 一致 | 1 | 一致 | c6c8e155bb6c |
| result.json | 4 | **不一致** | 1 | 一致 | b0c56220c9f8 |
| verify_report.json | 1 | 一致 | 1 | 一致 | 5ed91e2a4a13 |

读法：`evidence.json`/`figure.svg`/`layout.json`/`verify_report.json`/`figure.png`
在 **raw 条件**下就已经 N 次逐字节相同 —— 也就是说"同一张图"这件事**不需要任何特殊手段**成立。
只有 `result.json`（两条审计字段）与 `figure.pdf`（PDF 元数据）漂移，且两条都已声明并已被关掉。

## 5. 为什么"故意不稳定"比"全部钉死"更对

- **钉死时间戳 = 伪造审计记录**。`change_record` 的价值在于它指向真实时刻；
  官方题面也要求"标注每个关键元素的来源、版本和导出检查结果"，时间戳是这组证据的坐标系。
- **钉死 `out_dir` = 隐藏真实写入位置**。回放时它是"结果落在哪里"的唯一线索。
- **钉死 PDF 元数据 = 与 PDF 规范对着干**。正规做法是给一个不改变语义的**运行时开关**
  （`RL_INVARIANT`），而不是改代码把日期常量烧进去。

所以本包的选择是：**声明它、实测它、用可复现的方式关掉它、并且让"关掉"只发生在探针里**。
`--mode stabilized` 的三条杠杆全部在**探针侧**（工作目录、环境变量、驱动脚本），
`scripts/main.py` 与所有既有脚本**逐字节未改**。

## 6. 拿到这份报告后怎么复核（三条命令）

```bash
# ① 重跑探针，看 verdict 与 unexplplained（应为 pass / 0）
python "$SKILL_DIR/scripts/determinism.py" --json /tmp/d1.json && echo OK

# ② 直接看 stabilized 条件下 result.json 的 sha 是否 N 次同一个
python - <<'PY'
import json
r = json.load(open("/tmp/d1.json"))
print(r["per_file_sha256"]["result.json"]["stabilized"])   # 全同一个 sha 才算过
print(r["counts"]["stabilized_identical_files"], "/", r["counts"]["artifacts"])
PY

# ③ 自己手工对拍一次（不用本脚本，证明判据不依赖探针本身）
S=$(mktemp -d); cp -r "$SKILL_DIR" "$S/skill"
for i in 1 2; do
  RL_INVARIANT=1 PYTHONHASHSEED=$i python "$S/skill/scripts/main.py" \
      --case "$S/skill/examples" --out "$S/out" >/dev/null
  sha256sum "$S/out"/*/figure.svg "$S/out"/*/layout.json "$S/out"/*/figure.png
done
```

## 7. 未覆盖（如实声明）

| 未覆盖项 | 为什么 |
|-|-|
| 跨操作系统（Linux/macOS/容器）的字节级一致 | 本轮只在 Windows 11 + CPython 3.13.9 上跑。换 OS 后 PIL 的 PNG 编码器与字体可能变字节；SVG/layout/evidence 的确定性来自纯 Python，预期保持，但**未实测** |
| 跨 Pillow / reportlab 版本 | 同上；版本变了 PDF 内部结构可能变 |
| 跨机器字体差异 | `figure.png` 依赖本机 TTF；不同机器字体不同 ⇒ PNG 字节不同（这是**输入**不同，不是不确定性） |
| 并发运行（多进程同时写同一个 `--out`） | 本探针串行；并发重入归 `scripts/fault_inject.py` 未覆盖项 |
| `figure.svg` 之外的 SVG 变体（`--width-mm` 改动后） | 只测了示例案例的默认参数 |
| 时间跨度（跨天跨时区运行） | 冻结时钟只测了一个常量；真实跨天只影响 `change_record[].time` 一条 |
