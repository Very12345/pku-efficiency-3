# TEST.md — 本版验收记录（全部为本机真跑；命令与观测原样保留）

> 所有命令都在**包外临时副本**里执行（先 `cp -r <本包> <临时目录>`），
> 因为在本包目录里跑脚本会生成 `__pycache__`，打包形态门 R5 会 FAIL。
> 本文件所有数字都是跑出来的；没有估计值，也没有"应当如此"。
> 数字的逐项权威处：故障类 → `references/FAULT-MATRIX.md`；题集类 → `references/CASE-SET.md`；
> 增益类 → `references/GAIN-PROTOCOL.md`。

- 环境：Windows 11（10.0.22621）· CPython **3.13.9** · Pillow 12.3.0 · reportlab 5.0.0 · 本机有中文字体
- 被测包：本包（v6 全维合并版），基线 9 个脚本**逐字节未改**，其余 6 个脚本原样并入
- 复跑总耗时：约 60 秒（4 案跑批 ×2 + 32 条注入 + 20 条决策用例 + 对照三条件 + 确定性对拍）

## T1 · 合规形态

```bash
python validate_pkg.py <本包目录>
```

实测：`[PASS]`，**49 个文件**（上限 50），0 条 FAIL、0 条 warn。
检查项：扩展名白名单（`.md/.py/.json/.txt/.csv/.yaml/.yml`）、文件数、单文件大小、
合计体积、无符号链接、无 `__pycache__`/`.pyc`、全部 UTF-8、每个 `.py` 均可 `py_compile`、
包内不含本机绝对路径（Windows 盘符+反斜杠形态、`/Users/`、Windows 长路径前缀）。

> **49/50 是合并的结果**：五条线的同主题材料做了合并（映射见 `README.md §1`），
> 内容逐字保留。新增文件前请先看那条对照表。

## T2 · 主流程可跑（示例案例）

```bash
python scripts/main.py --case examples --out <临时输出目录>
```

实测：退出码 **0**，`status=success`，`check_ok=true`，`gates` G1–G10 全 true、`issues=[]`，
`result.json` 顶层键 **18 个**，产物 7 件
（`evidence.json` / `layout.json` / `figure.svg` / `figure.png` / `figure.pdf` /
`verify_report.json` / `result.json`）。

## T3 · 确定性（同输入两轮对拍）

| 文件 | 结果 |
|-|-|
| `figure.svg` | ✅ 一致 `f8b01ce26b622187` |
| `layout.json` | ✅ 一致 `c6c8e155bb6cd7f1` |
| `verify_report.json` | ✅ 一致 `5ed91e2a4a13df1d` |
| `evidence.json` | ✅ 一致（同目录同输入） |
| `result.json` | ⚠ **不一致**：含 `change_record[].time`（ISO8601）与 `execution.out_dir` |

⇒ 需要"可复现"的三个文件（SVG / 布局 / 校验报告）逐字节一致；`result.json` 因时间戳天然不同，
比对内容时应排除 `change_record[].time` 与 `execution.out_dir`。这一条是**如实说明**，不是缺陷。

## T4 · 题集跑批（4 案，三种图类，三个难度层）

```bash
python scripts/case_set_run.py --out <临时目录> --json <临时目录>/report.json --text-only
```

实测：`cases=4 · passed=4 · failed=0 · without_expectation=0`，脚本退出码 **0**。

| case_id | 图类 | 难度 | 退出码 | `status` | 实体 | 关系 | `verify.ok` | 告警 | `spec_sha16` |
|-|-|-|-|-|-|-|-|-|-|
| `apparatus-spec-01` | apparatus | 低 | 0 | success | 6 | 5 | true | — | `4603787adcb287d7` |
| `demo-biotech-route-01` | route | 低 | 0 | success | 10 | 9 | true | — | `e04e9d47e8ca0099` |
| `dtms-stage-route-01` | route | 高 | 0 | success | 18 | 18 | true | `recycle-review` | `cb33950dedb47795` |
| `mbr-wastewater-flow-01` | flow | 中 | 0 | success | 14 | 14 | true | `recycle-review` | `5b65c6612f7714e0` |

**泛化探针（`--text-only`）实测**：实体保留率 **0.200–0.667**、关系保留率 **0.000–0.357**；
`apparatus-spec-01` 的 5 条关系**全部丢失** + 4 个孤实体 ⇒ `status` 由 `success` 变 **`partial`**；
两案丢失 `recycle-review` 告警（回流未被识别）；`demo-biotech-route-01` 只剩 2 实体 1 关系仍报
`success` ⇒ **输入退化不自动降级状态**。逐案表格见 `references/CASE-SET.md §6`。

## T5 · 故障注入演练（32 条，四形态）

```bash
python scripts/fault_inject.py --out <临时目录> --json <临时目录>/report.json
```

实测：

| 指标 | 实测 |
|-|-|
| 注入条数 | **32**（输入 11 · 模板 8 · 依赖 3 · 契约 10；含 1 条不注入的对照行） |
| 退出码与期望不符 | **0** |
| 静默判定与期望不符 | **0** |
| 实测静默 | **10**（缺陷型 **9** + 合理型 1） |
| preflight 提前拦住 | **18 / 21**（另 11 条为契约族或 case 本身不存在） |
| **preflight 漏掉的静默缺陷** | **0** |
| 单条注入耗时 | 0.13–0.71 s |

**不污染的自证**：演练后对**包副本**做 `find -name '__pycache__' -o -name '*.pyc'` → 无输出；
原因是每条注入只改 `<out>/<注入号>/skill/` 沙箱副本，且子进程带 `PYTHONDONTWRITEBYTECODE=1`。

## T6 · 决策用例探针（20 条）

```bash
python scripts/decision_probe.py --out <临时目录> --json <临时目录>/obs.json
```

实测：退出码 **0**，汇总 `{"total": 20, "on_table": 20, "deviations": []}` ——
20 条用例的判决与 `references/failure-modes.md` 附录 C 的表**完全一致**
（含 4 条 error 级违规 ⇒ 退出码 3 / `status=partial`；2 条 warn 级 ⇒ 不降级；
1 条空壳输入 ⇒ `status=failed`）。

## T7 · 增益对照三条件 + 指标复算

```bash
python scripts/bare_baseline.py --case <case.json> --out <C0 目录>
python scripts/main.py --case <case.json> --out <C1 目录>
printf '{}' > <临时>/empty-rules.json
python scripts/main.py --case <case.json> --out <C2 目录> --rules <临时>/empty-rules.json
python scripts/gain_probe.py --result <C1>/<case_id>/result.json --baseline <C0 目录>
```

实测（示例 route 案例，原样数值）：

| 观测量 | C0 下界 | C1 本包 |
|-|-|-|
| 产物 | 仅 `figure.svg`（3 180 B、`<text>` 11 个）、**无** `layout.json`/`result.json` | 7 件；`figure.png` 54 982 B、`figure.pdf` 4 448 B |
| `png_bytes` / `pdf_bytes` | **0 / 0**（0 字节占位） | 54 982 / 4 448 |
| `spec` 指纹 | 无 | `svg` `f8b01ce26b622187` / `layout` `c6c8e155bb6cd7f1` / `verify` `5ed91e2a4a13df1d` |
| Q1 来源绑定率 | 0.00（无该字段） | **1.00** |
| Q6 状态诚实性 | 无 `status` 字段 | **true** |

⇒ 与 `references/GAIN-PROTOCOL.md` 附录 A 记录的方向一致：**质量维度全面从"无"到"有"**；
但**耗时与体积是变大的**（协议附录 A 里记的是 0.10 s → 0.44–0.59 s、~2 KB → ~78–105 KB），
本包**不声称运行更快**。

## T8 · 形态自检（提交前必跑）

```bash
python validate_pkg.py <本包目录>                          # 期望 PASS
grep -rnE '(^|[^A-Za-z])[A-Za-z]:[\\/]' <本包目录>         # 期望无输出
find <本包目录> -name '__pycache__' -o -name '*.pyc'       # 期望无输出
```

## T9 · 本次**没有**测的（如实列出）

| 未测项 | 为什么 |
|-|-|
| 平台固定 3 个案例 | 材料与白板由组织方提供，参赛者不可见；本包数字全部来自合成案例 |
| 真实模型臂的对照（裸 Agent vs 加载 Skill） | 本轮未起模型臂；协议 §3 只给可执行下界 C0，并明确"不对任何模型的分数作断言" |
| Linux / 容器环境的注入与跑批 | 本轮仅 Windows 11 + CPython 3.13.9；`WINDIR` 注入手法在 Linux 下需换等价物（方法同构，未实测） |
| 实体数 > 24 / 阶段数 > 5 | 未纳入题集；布局拥挤度未评估 |
| 磁盘写满、输出目录只读、超长材料、并发重入、时区/编码差异 | 未纳入本轮故障语料（`FAULT-MATRIX.md §8` 已列出） |
| 任何分数 | 本包不宣称具体分数；评分由平台执行 |
