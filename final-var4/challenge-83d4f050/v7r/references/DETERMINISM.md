# DETERMINISM.md — 字节级可复现：判据、实测表与稳定化配方（v7 轴）

> 本文件是 v7 的**轴文档**：把"同输入重跑得到同一份产物"从一句承诺变成
> 可被第三方复算的测量。权威测量器 = `scripts/determinism.py`（只依赖标准库）。
> 机器可读结果 = 包根 `determinism_report.json`（本机实跑产物，不是预置答案）。
> `result.json` 字段语义仍以 `references/OUTPUT_CONTRACT.md` 为准，本文件不改变契约。

## 1. 可复现的可操作定义（三条判据）

| # | 判据 | 含义 | 本文实测 |
|-|-|-|-|
| J1 | **原始字节稳定清单** | 有一个明确的产物清单，在任何 cwd / 任何 `PYTHONHASHSEED` / 任何进程下 sha256 都相同 | 7 个产物中 **5 个**稳定：`diagram.svg` `diagram.png` `model.json` `topology.json` `legend_audit.json` |
| J2 | **易变清单被逐字段点名** | 不稳定的产物必须被指出**具体哪个字节/哪个 JSON 路径**不稳定，且区分"故意"与"缺陷" | `diagram.pdf`：**只有 1 处**（`/CreationDate` 的秒位，1–2 字节）；`result.json`：**8 个 JSON 路径** |
| J3 | **稳定化后逐字节一致** | 施加文档化规则后，全部产物 sha256 相同（三条独立证据同时成立） | JSON 投影 ✓ · PDF 规范化 ✓ · 固定 cwd + `SOURCE_DATE_EPOCH` ✓ |

三条都成立 ⇒ 才允许在文档里写"可复现"。**只满足 J1 不算**（那只是"大部分稳定"）。

## 2. 怎么跑

```bash
export SKILL_DIR=/skills/weekly-skill          # 含 SKILL.md 的那一层
python3 "$SKILL_DIR/scripts/determinism.py" --help

# 默认：5 次运行（跨进程 / 跨 cwd / 跨 PYTHONHASHSEED），报告写到包根
python3 "$SKILL_DIR/scripts/determinism.py" --runs 5 \
    --work /tmp/det --report /tmp/determinism_report.json

# 只输机器可读结果；严格模式：要求原始字节也完全一致
python3 "$SKILL_DIR/scripts/determinism.py" --json > /tmp/det.json
python3 "$SKILL_DIR/scripts/determinism.py" --strict      # 原始不一致 → 退出码 3
```

退出码：`0` = 规范化后全部一致；`2` = 主流程在某次运行里非期望退出（环境/输入问题，不是不确定性问题）；
`3` = 规范化后仍不一致（真不可复现）；`4` = 参数/路径错误。

**它做了什么**（每次运行都是一个新解释器进程，参数逐字相同，只有 cwd 与 `PYTHONHASHSEED` 在轮转）：

| 运行 | cwd（相对工作根） | PYTHONHASHSEED | 退出码 | status | 耗时 | `result.json` 字节 |
|-|-|-|-|-|-|-|
| 1 | `pkg`（技能根） | `0` | 0 | success | 1.97 s | 29056 |
| 2 | `pkg/scripts` | `1` | 0 | success | 2.30 s | 29056 |
| 3 | `case`（案例目录） | `12345` | 0 | success | 2.00 s | 28888 |
| 4 | `pkg/examples` | `random` | 0 | success | 2.00 s | 29056 |
| 5 | `.`（工作根） | 不设置 | 0 | success | 1.98 s | 28903 |

> 命令字面量固定为 `python <pkg>/scripts/main.py --case <case.json> --model-file <model.json> --out out --formats svg,png,pdf --dpi 150 --verbose`；
> `--out out` 是**相对**参数，因此 `provenance.command` 在各次运行间逐字相同，差异只可能来自 cwd / 哈希种子 / 时间本身。

## 3. 实测表 1：逐产物 sha256（5 次运行）

| 产物 | 字节 | sha256（前 16 位） | 不同哈希数 | 逐字节一致 |
|-|-|-|-|-|
| `diagram.svg` | 17771 | `27f344a0dfb2e90f` | 1 | ✅ |
| `diagram.png` | 203655 | `9137715961238f3f` | 1 | ✅ |
| `model.json` | 11418 | `f93a20a283492f73` | 1 | ✅ |
| `topology.json` | 1434 | `eb826fc5557fccfc` | 1 | ✅ |
| `legend_audit.json` | 1807 | `efdb1805c839d648` | 1 | ✅ |
| `diagram.pdf` | 108045 | （每次不同，示例 `79fdc09f…`） | **5** | ❌ 仅 `/CreationDate` 秒位（1–2 字节） |
| `result.json` | 28888–29056 | （每次不同，示例 `257ca36c…`） | **5** | ❌ 8 个 JSON 路径（见下） |

**这 5 个稳定产物是 sha256 可跨机比对的**：它们的字节只由（模型 × 布局 × 图例）决定，
不含时间戳、不含绝对路径（`diagram.svg` 的 provenance 注释只写 skill/version/contract/**case_id**）。
⇒ 第三方拿同一份 `model.json` 重跑，可以直接拿这 5 个数对拍，不需要"看着差不多"。

`diagram.png` 为什么不含时间元数据：PNG 块清单一实测为
`IHDR(13) · tEXt(58) · pHYs(9) · IDAT(65536×3 + 6863) · IEND(0)`，**没有 `tIME` 块**
（`png_metadata_probe.has_time_chunk = false`）。matplotlib 只写一个恒定的 `tEXt`（软件标识）。

## 4. 实测表 2：易变字段逐字段点名（`result.json`）

跨 5 次运行观测到的**全部**差异路径（`determinism_report.json → volatile_fields`）：

| # | JSON 路径 | 性质 | 观测到的值（示例） | 稳定化处理 |
|-|-|-|-|-|
| 1 | `$.provenance.ts` | **故意**：真实运行时间 | `2026-11-23T19:26:00+0800` / `…19:26:02+0800` | 投影掩码 |
| 2–4 | `$.change_records[0..2].ts` | **故意**：变更记录时间 | 同上 | 投影掩码 |
| 5 | `$.provenance.case_file` | **缺陷级**：随 **cwd** 变化 | `<WORK>/case/case.json` / `case.json` / `case/case.json` | 投影掩码；或固定 cwd |
| 6–7 | `$.change_records[0].why` `$.change_records[1].why` | **缺陷级**：同上（路径被相对化到当前 cwd） | `case=<WORK>/case/case.json, …` / `case=case.json, …` | 同上 |
| 8 | `$.self_check.checks[30].detail` | **二阶**：内含上一步 `result.json` 的字节数（`29056` / `28888` / `28903`） | `result.json (28309 bytes)` … | 随路径字段一起掩码 |

**根因（重要，且是本次新发现）**：`scripts/main.py` 的 `portable_path()` 在"路径不在技能根内"时
会退化为**相对当前工作目录**渲染。于是同一份输入、同一条命令，只要进程 cwd 不同，
`result.json` 里的路径字段与体积就会变。**这不是时间戳问题，是 cwd 泄漏**——
所以"确定性与字节级可复现"这条轴上，**cwd 必须与输入一起固定**。

投影掩码规则（写进报告 `stabilization.json_projection.rule`，可独立复算）：
键名匹配 `ts|time|timestamp|datetime|date|created|modified|mtime|elapsed|duration|runtime|host|user|pid|cwd|abspath|abs_path`
的字段、值为**绝对路径**的位置类键、以及**观测到**的易变路径 → 统一替换为 `<VOLATILE>`，
再以 `sort_keys` 规范化序列化后取 sha256。本机实测掩码 **9 条路径**后在 5 次运行间哈希相同（`distinct_sha256 = 1`）。

## 5. 实测表 3：`diagram.pdf` 的字节级证据

| 项 | 实测 |
|-|-|
| 文件大小 | 108045 字节（5 次运行完全相同） |
| 差异区间 | **1 处**，落在 `/CreationDate` 的秒位上（偏移 `104020` 起；两次测量分别为「偏移 104020、长度 2」与「偏移 104021、长度 1」——差几位取决于两次运行的秒数） |
| 上下文 | `…d v3.10.6).` **`/CreationDate (D:20261123190648+08'00')`** `>>.endobj.xref…` ↔ `…(D:20261123190654+08'00')…` |
| 命中的易变 token | `/CreationDate`（**只有这一个**） |
| `/ModDate` | 不存在 |
| `/ID` | 不存在（`pdf_has_id = false`） |
| 稳定化 | `PDF_DATE_RE`/`PDF_ID_RE` 规范化 → 5 次运行归一为**同一个哈希**（`distinct_sha256 = 1`，`hits = ["/CreationDate|/ModDate"]`） |

即：PDF 的不可复现性**只有秒位那 1–2 个字节**，来自 matplotlib PDF 后端的创建时间。
把 `/CreationDate` 归零（或下面配方 C）就完全可复现——不需要重写渲染后端。

## 6. 稳定化配方（三条，各自有实测）

### 配方 A：JSON 投影（比对用，不改产物）
按 §4 规则掩码 → 规范化 → 比 sha256。实测：`result.json` 5 次运行归一（`distinct_sha256 = 1`）。
用途：CI 里判"报告内容是否真的变了"，而不是"时间戳变没变"。

### 配方 B：PDF 规范化（比对用，不改产物）
```text
/CreationDate (D:…)  →  /CreationDate (D:00000000000000+00'00')
/ModDate (D:…)       →  同上
/ID [<…> <…>]        →  /ID [<00><00>]        （本机实测 PDF 里没有 /ID）
```
实测：5 次运行 → 1 个哈希。

### 配方 C：环境配方（**不改脚本**就能拿到原始字节一致）
```bash
# cwd 固定为技能根；两次运行参数逐字相同；输出目录同名（后一次覆盖前一次）
cd "$SKILL_DIR"
SOURCE_DATE_EPOCH=1577836800 python3 scripts/main.py --case examples/case.json \
    --model-file examples/model.example.json --out out --formats svg,png,pdf --dpi 150
SOURCE_DATE_EPOCH=1577836800 python3 scripts/main.py --case examples/case.json \
    --model-file examples/model.example.json --out out --formats svg,png,pdf --dpi 150
```

实测（`determinism_report.json → stabilization.env_recipe`）：

| 断言 | 实测值 |
|-|-|
| 两次运行之间**除 `result.json` 外**全部产物原始字节一致 | ✅ `identical_except_result_json = true` |
| `diagram.pdf` 两次原始字节一致（`SOURCE_DATE_EPOCH` 被 matplotlib 3.10.6 采用） | ✅ `pdf_identical = true` |
| 残余的 `result.json` 差异路径 | **恰好 4 个**：`$.change_records[0].ts` `$.change_records[1].ts` `$.change_records[2].ts` `$.provenance.ts` |
| 这 4 条路径投影后一致 | ✅ `result_json_projected_identical = true` |

⇒ **结论（可直接引用）**：把 cwd 固定到技能根并设 `SOURCE_DATE_EPOCH`，
本 Skill 的全部产物里**唯一**不可复现的东西就是 3 条变更记录与 1 条 provenance 的**时间戳字段**；
其余字节（含 PDF、PNG、SVG、三份审计 JSON）完全可复现。

## 7. 未覆盖声明（本轴没测的东西，不要当成测过）

1. **跨机器/跨平台的字节一致**：本表是同一台 Windows + CPython 3.13.9 + matplotlib 3.10.6 + Pillow 12.3.0。
   `diagram.png`/`diagram.pdf` 含库版本与字体子集信息，换库版本/换平台**预期**不同（未实测，故不声称）。
2. **字体替换引起的漂移**：只验证了"本机字体环境下稳定"，没有卸载字体做对照（v9 的降级轴覆盖缺依赖，不覆盖缺字体）。
3. **并发运行**（同输入并行跑两个进程写同一输出目录）：未覆盖。
4. **`--materials-dir` / `TASK_OUTPUT` 等其它入口的确定性**：本表只用 `--case/--model-file/--out/--formats/--dpi`。
5. **`time.time()` 分辨率以下的抖动**：时间戳只到秒（`%Y-%m-%dT%H:%M:%S%z`），故"同秒"是可能事件；
   §6 配方 C 已用 `sleep 1.2` 强制错开（脚本内置），避免"同秒侥幸通过"。
6. **平台评测容器的时钟/环境变量**：不可见，不推测。

## 8. 与基线断言的差别（为什么这条轴是新增的，不是重述）

基线（`final/challenge-83d4f050`）在 `TEST.md T4` / `COMPARE.md §2.2` 里只有一条粗断言：
"同输入双跑后 `diagram.svg` / `diagram.png` / `model.json` / `topology.json` / `legend_audit.json` 逐字节一致"。
本版把它加强为可复算的完整测量：

| 维度 | 基线断言 | v7 实测 |
|-|-|-|
| 运行次数 | 2 | **5** |
| cwd | 隐含同一个（未声明） | **5 个不同 cwd**（技能根 / scripts / case / examples / 工作根） |
| `PYTHONHASHSEED` | 未提 | **5 种**（0 / 1 / 12345 / random / 不设置） |
| 产物范围 | 5 个（**故意漏掉 PDF 与 result.json**） | **全部 7 个**，并把 PDF/result.json 的不稳定**定位到字节与字段** |
| 稳定化 | 无 | **3 条配方**，各有实测数字 |
| 机器可读 | 无 | `determinism_report.json`（`runs[] / per_file_sha256 / identical / volatile_fields[] / byte_diff / stabilization`） |

## 9. 复现本文件全部数字

```bash
export SKILL_DIR=/path/to/challenge-83d4f050        # 含 SKILL.md 的那一层
python3 "$SKILL_DIR/scripts/determinism.py" --runs 5 \
    --work /tmp/det --report /tmp/determinism_report.json      # 退出码应为 0
python3 - <<'PY'
import json
d = json.load(open("/tmp/determinism_report.json", encoding="utf-8"))
print(d["identical"], d["stable_artifacts"], d["volatile_artifacts"])
print([f["json_path"] for f in d["volatile_fields"]])
print(d["stabilization"]["pdf_normalization"]["identical"],
      d["stabilization"]["env_recipe"]["pdf_identical"],
      d["stabilization"]["env_recipe"]["result_json_diff_paths"])
PY
```
