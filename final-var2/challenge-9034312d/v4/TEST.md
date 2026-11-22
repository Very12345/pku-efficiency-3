# TEST.md — 本版验收记录（全部为本机真跑，命令与观测原样保留）

> 本文件记录**这一版**做过哪些验证、结果是什么。所有命令都写全了怎么复跑；
> 所有数字都是跑出来的，不是估计。跑测试的位置一律是**包外临时副本**，
> 因为直接在本包目录里跑脚本会生成 `__pycache__`（打包形态门 R5 会 FAIL）。

- 环境：Windows 11（10.0.22621）· CPython **3.13.9** · Pillow 12.3.0 · reportlab 5.0.0 · 本机有中文字体
- 被测包：本包（v4 故障注入与恢复演练版），`scripts/main.py` 等既有脚本**未做任何修改**
- 复跑总耗时：约 40 秒（含 32 条注入、两次主流程、一次负例）

## T1 · 合规形态（包本身）

```bash
python validate_pkg.py <本包目录>
```

期望与实测：`[PASS]`，无 `FAIL`。检查项：扩展名白名单（`.md/.py/.json/.txt/.csv/.yaml/.yml`）、
文件数 ≤50、单文件 ≤500KB、合计 ≤2MB、无符号链接、无 `__pycache__`/`.pyc`、
全部文件为 UTF-8 且不含本机绝对路径（Windows 盘符+反斜杠形态、`/Users/`、Windows 长路径前缀）、
每个 `.py` 都能 `py_compile` 通过。

> 复跑后请再用 `find <本包目录> -name '__pycache__' -o -name '*.pyc'` 确认无输出
> —— 演练与自测都会在**副本**里跑，但这一条是"确实没写回原包"的机械证据。

## T2 · 主流程可跑（示例案例，包外副本）

```bash
cd <包外副本>
python scripts/main.py --case examples --out <临时输出目录>
```

实测：**退出码 0**，`status=success`，`verify_ok=true`，`check_ok=true`，
`gates` G1–G10 **全 true**，`issues=[]`。
`result.json` 顶层键 **18 个**：
`canvas / case_id / change_record / checksum / entities / evidence / execution /
extraction / figure_type / fonts / output_contract / relations / sources / status /
title / uncertainty / verify / workorder`。

产物 7 件（示例案例 `demo-biotech-route-01`，10 实体 / 9 关系）：

| 文件 | 字节 | sha256 前 16 位 |
|-|-|-|
| `evidence.json` | 7 224 | `0a1103c3fd002bd5` |
| `layout.json` | 10 911 | `c6c8e155bb6cd7f1` |
| `figure.svg` | 10 532 | `f8b01ce26b622187` |
| `figure.png` | 54 982 | `990ab3a46d80c2b7` |
| `figure.pdf` | 4 448 | `74c12f06aec28bf4` |
| `verify_report.json` | 699 | `5ed91e2a4a13df1d` |
| `result.json` | 13 802 | `4ff16a0f8ff8bf2e` |

PNG 尺寸 2362×1496 px @200 DPI（= 300 mm × 190 mm 画布 / 25.4 × 200）；
PDF 为矢量（reportlab CID 字体 `STSong-Light`）；`spec_sha16 = e04e9d47e8ca0099`。

## T3 · 确定性（同输入两轮对拍）

```bash
python scripts/main.py --case examples --out <临时输出目录 A>
python scripts/main.py --case examples --out <临时输出目录 B>
# 逐文件比对 sha256
```

实测（4/5 逐字节一致）：

| 文件 | 结果 |
|-|-|
| `figure.svg` | ✅ 一致 `f8b01ce26b622187` |
| `layout.json` | ✅ 一致 `c6c8e155bb6cd7f1` |
| `verify_report.json` | ✅ 一致 `5ed91e2a4a13df1d` |
| `evidence.json` | ✅ 一致 `0a1103c3fd002bd5`（同目录同输入；换目录时 `sources[].path` 会变，这是取证需要） |
| `result.json` | ⚠ **不一致**：含 `change_record[].time`（ISO8601 时间戳）与 `execution.out_dir` |

> **结论**：真正需要"可复现"的三个文件（SVG / 布局 / 校验报告）逐字节一致；
> `result.json` 因时间戳天然不同 —— 若要比对内容，比对除 `change_record[].time`
> 与 `execution.out_dir` 之外的字段。这一条不是缺陷，但必须说清，否则会被误判为"不确定"。

## T4 · 故障注入演练（本版核心，32 条）

```bash
python scripts/fault_inject.py --out <临时目录> --json <临时目录>/report.json
```

实测（两次独立运行，`summary` 完全一致）：

| 指标 | 实测 |
|-|-|
| 注入条数 | **32**（输入 11 · 模板 8 · 依赖 3 · 契约 10；其中 1 条是不注入的对照行） |
| 退出码与期望不符 | **0** |
| 静默判定与期望不符 | **0** |
| 实测静默 | **10**（缺陷型 **9** + 合理型 1） |
| preflight 实跑条数 | 21 |
| preflight 提前拦住 | **18** |
| **preflight 漏掉的静默缺陷** | **0** |
| 单条注入耗时 | 0.13–0.71 s |

逐行数据见 `references/FAULT-MATRIX.md` §1–§5（每行都有注入手法、期望退出码、
实测退出码、实测 `status`、实测 `uncertainty[].scope`、`check.py` 失败门号、
闸门结论、是否静默）。

**"不污染"的自证**：演练前后对包内做
`find <包> -name '__pycache__' -o -name '*.pyc'` → **无输出**。
原因是每条注入只改 `<out>/<注入号>/skill/` 里的沙箱副本，
且所有子进程都带 `PYTHONDONTWRITEBYTECODE=1`。

## T5 · 闸门负例（`preflight.py` 能不能真的叫停）

构造一个同时带 5 个问题的输入（缺 canvas / `--task` 指错 / `--material` 指错 /
悬空关系 / `--rules` 坏 JSON）：

```bash
python scripts/preflight.py --case <neg>/case.json --rules <neg>/rules.json \
  --task <neg>/absent-task.md --material <neg>/absent-mat.md --deps
```

实测输出（原样）：

```
⚠ warn   [input/canvas-defaulted] case 未给 canvas，将用默认 297×180 mm
⚠ warn   [input/task-missing] 显式给的 --task 不存在（main.py 会安静地不读任务书，产物无任何标记）
⚠ warn   [input/material-missing] --material 指向的文件不存在：absent-mat.md
⚠ warn   [structure/relation-dangling] 1 条关系端点不存在：['R1(E1->E9)']（会被静默丢弃，只在 verify.checks.no_dangling 留痕）
❌ error  [asset/rules-unparsable] 自定义 --rules 不可解析（JSON 语法错误：第 1 行第 3 列（Expecting property name enclosed in double quotes））⇒ 审计按「无规则」通过
合计 1 error / 4 warn · 退出码 3
```

⇒ **退出码 3**（有 error），4 条 warn 也各自点明"main.py 会安静地……"，
与 `FAULT-MATRIX.md §6` 的缺口 B/C/D/E 一一对应（F1-10 / F1-11 / F2-01 / F2-05）。

另跑健康输入（`--case examples --deps`）⇒ **退出码 0，无 finding** ——
说明闸门不会对干净输入乱报（这一条同样重要：一个永远报警的闸门等于没有）。

## T6 · 契约门负例（`check.py` 的拦截能力）

不单独手工造负例，而是由 `fault_inject.py` 的契约族代劳（F4-01…F4-09 共 9 条）：
9/9 全部被拦下，退出码 1，且门号与注入对得上（例如删 `output_contract` ⇒
G2/G3/G4/G5/G6 同时报；`exports=null` ⇒ G2/G4；`status` 撒谎 ⇒ G9/G10）。

> 已知粗糙点：F4-04（`output_contract` 被写成字符串）时 `check.py` 抛
> `AttributeError: 'str' object has no attribute 'get'`，只留栈、不给门号。
> **不假绿**（退出码仍非 0），但信息不友好 —— 记录在矩阵 §6 缺口 H，本版**未改** `check.py`。

## T7 · 形态自检（提交前必跑）

```bash
python validate_pkg.py <本包目录>                              # 期望 PASS
grep -rnE '(^|[^A-Za-z])[A-Za-z]:[\\/]' <本包目录>             # 期望无输出（https:// 不误报）
find <本包目录> -name '__pycache__' -o -name '*.pyc'           # 期望无输出
```

## T8 · 本次**没有**测的（如实列出）

| 未测项 | 为什么 |
|-|-|
| 平台固定 3 个案例上的表现 | 案例与白板由平台提供，参赛者不可见；本包数字全部来自合成案例 |
| 与"不加载 Skill 的裸 Agent"的质量对照 | 本版聚焦故障行为，未起裸 Agent 臂（另有一份包专门做增益对照） |
| Linux / 容器环境的注入结果 | 本轮仅 Windows 11 + CPython 3.13.9；`WINDIR` 注入手法在 Linux 下需换等价物（方法同构，未实测） |
| 并发/重入、磁盘写满、超长材料、时区与编码差异 | 未纳入本轮 32 条语料（矩阵 §8 已列出） |
| 任何分数 | 本包不宣称具体分数；评分由平台执行 |
