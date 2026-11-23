# DETERMINISM.md — 字节级可复现性：哪些字段故意不稳定、怎么稳定化

> **本文件所有数字来自真跑**：`scripts/determinism.py` 把同一份输入连跑 5 次，
> 每次都换掉进程、cwd、`--out` 形态与 `PYTHONHASHSEED`，再对**全部产物**做 sha256 比对。
> 复现命令（`$SKILL_DIR` = 含 SKILL.md 的包根；cwd 任意）：
>
> ```bash
> python "$SKILL_DIR/scripts/determinism.py" \
>     --case "$SKILL_DIR/examples" \
>     --out-root /tmp/det --report /tmp/det/determinism_report.json --runs 5
> # 期望：raw identical=False，content-projection identical=True，
> #       normalized-archive identical=True，leaks=0，退出码 0
> ```
>
> 实测环境：Python 3.13.9 / Windows（win32）/ python-pptx 1.0.2 / Pillow 12.3.0 /
> pypdf 6.14.2；案例 = 包内合成示例案例 `example-synthalign-talk-01`。

## 0. 一句话结论

**raw 字节 5 次全同 = False；内容投影 5 次全同 = True；归一化归档 5 次全同 = True。**
即：产物**内容**逐字节可复现，唯一不可复现的是两类**容器/记录元数据** ——
JSON 里的运行时刻戳，与 `.pptx` 这个 zip 容器的成员时间戳。
两者都被逐字段点明，并给出稳定化后的哈希（下表 `stable sha256` 三列完全相同）。

## 1. 运行计划（每次 run 故意换什么）

| run | cwd | `--out` 形态 | PYTHONHASHSEED | exit | 墙钟（一次实测） |
|-|-|-|-|-|-|
| run0 | 空临时目录 | **绝对路径** | 0 | 0 | 1.637 s |
| run1 | 沙箱内技能副本根 | `../out1`（相对） | 1 | 0 | 1.592 s |
| run2 | 沙箱内技能副本根 | `../out2`（相对） | 2 | 0 | 1.534 s |
| run3 | 空临时目录 | **绝对路径** | 4 | 0 | 1.750 s |
| run4 | 沙箱内技能副本根 | `../out4`（相对） | 8 | 0 | 1.549 s |

> 墙钟只作参考：它随机器负载与杀毒/索引进程波动（早期一次同口径实测为 1.06–1.16 s）。
> **判据不看墙钟**，只看 §6 的四个布尔。

- **跨进程**：每次 run 都是新的 `subprocess`，且被调用入口是**沙箱内的技能副本**
  `<sandbox>/skill/scripts/main.py` —— 包内原目录全程只读，不会留下 `__pycache__`。
- **cwd 无关性**：三种 `--out` 形态解析到**同一个**绝对输出目录；任何"cwd 进了产物内容"
  的行为都会让逐文件 sha256 立刻分叉（实测没有）。
- **哈希随机化**：`PYTHONHASHSEED` 逐次不同（0/1/2/4/8），证明产物不依赖 `set`/`dict` 迭代序。

## 2. 逐文件实测（5 次 run 的 sha256 去重计数）

| 产物 | 字节数 | raw 唯一值 | 稳定化后唯一值 | 稳定化口径 |
|-|-|-|-|-|
| `talk_plan.json` | 23717 | **5** | **1** | 剔除时间戳键后按键排序哈希（json-projection） |
| `previews/preview_manifest.json` | 2285 | **5** | **1** | 同上 |
| `result.json` | 42516 | **5** | **1** | 同上 |
| `self_check.json` | 4044 | **5** | **1** | 同上 |
| `editable_deck.pptx` | 67641 | **5** | **1** | 按成员名排序、逐成员哈希解压内容（跳过 `docProps/core.xml`） |
| `deck_audit.json` | 4173 | 1 | 1 | raw 已一致 |
| `evidence_audit.json` | 5018 | 1 | 1 | raw 已一致 |
| `evidence_map.json` | 405 | 1 | 1 | raw 已一致 |
| `plan_gates.json` | 1325 | 1 | 1 | raw 已一致 |
| `previews/cover_preview.png` | 97357 | 1 | 1 | raw 已一致 |
| `previews/preview_grid.png` | 101149 | 1 | 1 | raw 已一致 |
| `previews/slide_002.png` … `slide_011.png`（10 张） | 53358–68692 | 各 1 | 各 1 | raw 已一致 |

- 产物总数 **21**（8 个顶层产物 + `previews/` 下 13 个：cover、grid、manifest 与 10 张逐页缩略图）。
- **raw 唯一值 = 1 的产物：16 个**；raw 有差异的：5 个（上表前 5 行，5 次 run 各不同值）。
- **稳定化后唯一值 > 1 的产物：0 个。**
- 产物树整体哈希：raw 5 个不同值 / 稳定化后 **1 个值** `b7b531d96c9d67ac…` /
  归一化归档后 **1 个值** `79d2050196f529e0…`。

## 3. 逐字段：哪些是**故意**不稳定的

`determinism_report.json` 的 `volatile_fields[]` 是权威清单，逐条对应下表。

| # | 字段 | 类别 | 故意？ | 为什么必须不稳定 | 怎么稳定化 | 实测观测 |
|-|-|-|-|-|-|-|
| 1 | `result.json.generated_at`、`self_check.json.generated_at` | 记录性时间戳 | ✅ 故意 | 诚实记录本次运行时刻；题面要求变更记录可复核，时间戳不能用假值 | `stable_json_view()` 剔除 `generated_at/at/ts/timestamp/created/modified` 后按键排序哈希 | 两次 run 相差 14 秒 |
| 2 | `*.change_records[].at`（result.json 里共 22 处键路径） | 记录性时间戳 | ✅ 故意 | 每条取舍/降级动作的真实发生时刻 | 同上（键名 `at` 在剔除集合内） | 三次 run 三个不同值 |
| 3 | `result.json.environment.*`（`python`/`platform`/`python_pptx`/`pillow`/`pypdf`/`cjk_font`） | 运行环境记录 | ✅ 故意 | 如实记录本次运行环境；同机不变，换机必然变 —— 这是特征不是缺陷 | `ENV_KEYS` 并入剔除集合 | 本机 5 次完全一致（3.13.9 / win32 / pptx 1.0.2 / msyh.ttc） |
| 4 | `editable_deck.pptx` 的 **zip 容器成员时间戳** | 容器元数据 | ✅ 故意 | `python-pptx` 用 `zipfile.ZipFile(...).writestr()` 写包；CPython 的 `writestr` 发现 `date_time` 早于 1980 时**填入当前本地时间**（源码位于 `zipfile.ZipInfo`；python-pptx 的 `opc/serialized.py:239` 只传 `compression`，没有设置 `date_time`），因此整包 raw sha256 每次不同 | ① 稳定化哈希只算**解压后的成员内容**（跳过 `docProps/core.xml`），与 `verify_deck.normalize_pptx_sha()` 同口径；② `--normalize` 另写一份 `date_time=(1980,1,1,0,0,0)`、成员名排序、压缩级别固定的归档副本，其 **raw** sha256 也可复现 | 本机 5 次 run：raw 唯一值 = **5**（每次都落在不同秒 ⇒ 5 个不同时间戳）；**87 个 zip 成员解压后字节完全相同** |
| 5 | `previews/*.png`（13 张） | 二进制渲染 | ❌ 非故意 | 本包渲染路径不含 `tIME` 时间戳 chunk（实测 PNG chunk 序列 = IHDR + 2×IDAT + IEND，无任何时间类 chunk） | 不需要（raw 已一致）；若换 Pillow 版本引入差异，会落到 `files_varying_raw` 并按 `raw-bytes` 稳定化 | 13 张 PNG 的 raw sha256 在 5 次 run 中一致 |
| 6 | 产物里的**绝对路径** | 机器路径 | ❌ 非故意（**不允许**） | 作者机器路径若写进产物，会把一次运行变成不可跨机复核（题面硬门） | `common.sanitize_output()` 写盘前把本机路径改写为相对案例目录；本探针用 `path_leak_scan()` **独立复扫**每次 run 的 8 个 JSON 产物（盘符路径、UNC 前缀、`/Users/`、`/home/<user>/` 四类正则） | 5 次 run × 每次 8 个 JSON 产物 = **0 命中** |
| 7 | `--out` 传入形态（绝对 / `../` 相对） | 调用形态 | ✅ 故意 | 评测机上 cwd 与 `--out` 形态未知；故意混用用来证明调用形态不进入产物内容 | 产物只出现相对案例目录的路径（OUTPUT_CONTRACT.md §0） | 两种形态解析到同一输出内容，逐文件 sha256 相同 |
| 8 | 沙箱目录名（`--out-root`、临时 cwd） | 临时目录 | ✅ 故意 | 沙箱名由调用者给（本次 `out0`/`cwd0`…），若它进了产物就说明路径没被可移植化 | `path_leak_scan()` + `<ROOT>/` 占位替换 | 产物不含沙箱绝对路径（0 命中） |

## 4. 稳定化算法（三段，逐段可核对）

```
① JSON 产物（.json）
   parse -> 递归剔除 TS_KEYS ∪ ENV_KEYS -> sort_keys=True 再序列化
   -> 把 <本机路径前缀> 换成占位符 -> sha256            # stable_method = "json-projection"

② zip 容器（.pptx / .zip）
   ZipFile(namelist) 排序 -> 跳过 docProps/core.xml -> sha256( name \0 sha256(entry) \n 序列 )
                                                       # stable_method = "zip-payload(no core.xml)"

③ 其它（.png 等二进制）
   原始字节 sha256                                       # stable_method = "raw-bytes"

另有 --normalize（默认开）：把每个 run 的产物树复制一份，
  .json 写稳定化视图、zip 重写为固定 date_time 的归档、其它原样复制，
  再对整棵树算 raw sha256 —— 实测 5 个 run 得到同一个值。
```

`per_file_sha256` 里每个文件都带 `stable_method`，因此"这一行是按哪种口径判定的"永远可查。

## 5. 稳定化视图的唯一性核对（`stable_view`）

| 文件 | 剔除的字段路径（实测） | 5 次 run 的稳定化 sha256 唯一值 |
|-|-|-|
| `talk_plan.json` | `generated_at` | **1** |
| `previews/preview_manifest.json` | `generated_at` | **1** |
| `result.json` | `change_records[0..21].at` + `environment.*`（共 22 + 6 条） | **1** |
| `self_check.json` | `generated_at` | **1** |
| `evidence_map.json` | 无（本来就没有时间戳） | **1** |

## 6. 门与退出码

| 项 | 实测 |
|-|-|
| 各 run 退出码 | 全部 **0** |
| `result.json` 顶层键数（每次 run） | 全部 **20** |
| `raw_byte_identical` | False（见 §3 第 1/2/4 行） |
| `content_projection_identical` | **True** |
| `normalized_archive_identical` | **True** |
| `no_machine_path_leak` | **True**（0 命中） |
| `overall_pass` | **True** |
| 探针自身退出码 | **0** |

判据原文（写在报告 `gate.criterion` 里）：

```
overall_pass = 全部 run exit 0
               且 稳定化后产物树完全一致
               且 产物无本机绝对路径
               且 无产物在某次 run 中缺失
```

> **注意**：`overall_pass=True` **不等于** raw 字节相同。本包不把"raw 不同"
> 藏起来 —— 它出现在 `identical=False`、`files_varying_raw` 与 `zip_metadata_only_files`
> 三处，并且每个差异都有一条 `volatile_fields` 解释到具体源码行为。

## 7. 未解决 / 未覆盖

- **未做**"把 `.pptx` 的 raw 字节也变成确定性的"：那需要改 `deck_builder.py` 的写包方式
  （自定义 `ZipInfo.date_time`），属于改既有脚本的**行为**，本轮明确不做。
  本包给的是**等价物**：`--normalize` 产出的归档副本 raw 可复现。
- **未测跨机器**：只在 Windows + Python 3.13.9 上实测。跨机器的 `environment` 与
  字体探测结果**必然**不同（那是设计内行为，已在 §3 第 3 行登记）。
- **未测并发**：5 个 run 串行；两个进程同时写同一个 `--out` 未测。
- **未测长时漂移**：run 间隔约 1 秒；跨天/跨时区的 `generated_at` 形态（ISO8601 UTC）
  由 `common.utc_now()` 保证格式稳定，但未做跨时区实跑。

## 8. 复核清单

1. 跑 §头部命令 → `content-projection identical=True`、`leaks=0`、退出码 0。
2. 打开报告，核对 `files_varying_raw` 恰为
   `["editable_deck.pptx","previews/preview_manifest.json","result.json","self_check.json","talk_plan.json"]`，
   且 `files_varying_stable` 为空列表。
3. 核对 `zip_metadata_only_files == ["editable_deck.pptx"]`。
4. 任取两次 run 的 `editable_deck.pptx`，用
   `python -c "import zipfile,hashlib;z=zipfile.ZipFile(p);print([hashlib.sha256(z.read(n)).hexdigest()[:12] for n in sorted(z.namelist())][:3])"`
   比较成员内容哈希 → 应完全相同。
5. 读 `<sandbox>/normalized/run0/editable_deck.pptx` 与 `run1` 的同名文件 → raw sha256 相同。
