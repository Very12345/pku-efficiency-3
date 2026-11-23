# TEST.md — v8 验收记录（全部本机真跑；命令与输出摘要原样保留）

> 所有命令都在**包外临时副本**里执行（先 `cp -r <本包> <临时目录>`），
> 因为在本包目录里跑脚本会生成 `__pycache__`，打包形态门会 FAIL。
> 本文件所有数字都是跑出来的。逐行矩阵见 `references/CONTRACT-MATRIX.md`。

- 环境：Windows 11（10.0.22621）· CPython **3.13.9** · Pillow 12.3.0 · reportlab 5.0.0 · 本机有中文字体
- 被测包：本包（v8），**基线 9 个脚本逐字节未改**，其余 6 个既有脚本原样并入，另加 `scripts/contract_matrix.py`
- 复跑总耗时：约 80 秒（smoke + 矩阵 164 行 + 既有回归三件套）

## T1 · 合规形态

```bash
python validate_pkg.py <本包目录>
```

实测：`[PASS]`，**49 个文件**（上限 50），0 条 FAIL、0 条 warn。
检查项：扩展名白名单、文件数、单文件大小、合计体积、无符号链接、无 `__pycache__`/`.pyc`、
全部 UTF-8、每个 `.py` 可 `py_compile`、包内无本机绝对路径、`SKILL.md` frontmatter 含
`name` 与 `description`。

## T2 · 主流程可跑（示例案例）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out <临时输出目录>
```

实测：退出码 **0**，`status=success`，`check_ok=true`，G1–G10 **全 true**、`issues=[]`，
`result.json` 顶层键 **18 个**，产物 **7 件**。

## T3 · ★ 本包的轴：契约四形态 × 边界值矩阵

```bash
python "$SKILL_DIR/scripts/contract_matrix.py" --out <临时> --json <临时>/cm.json
```

实测输出摘要（原样）：

```json
{ "verdict": "attention", "contract_doc_matches": true,
  "contract_fields": 18, "check_required_fields": 9,
  "contract_fields_not_checked": ["workorder","extraction","entities","relations",
                                  "evidence","verify","canvas","fonts","execution"],
  "counts": { "rows": 164, "input_rows": 22, "output_rows": 106, "form_rows": 36,
              "violating_rows": 141, "silent_pass": 96, "defects": 10,
              "silent_uncovered": 86, "setup_errors": 0 },
  "defects": ["in-01","in-03","in-04","in-05","in-19","in-22",
              "nest-08","nest-09","nest-10","nest-11"] }
```

退出码 **1**（预期：`defects` 非空）。耗时约 **24 s**。

**四段各自的行数与结论**

| 段 | 行数 | 跑什么 | 结论摘要 |
|-|-|-|-|
| ① 契约面自校验 | — | 文档字段块 ⇄ `check.py` 的 `required_fields` | 文档与脚本清单一致（18=18）；**机器门只覆盖 9 个** |
| ② 输入侧 `in-*` | 22 | `main.py` 全流程 | 违约 **18** 行：`failed` **3** · `partial` **3** · `success` **12**（其中 **6** 行有 `uncertainty` 或 `text-heuristic`，**6** 行零信号） |
| ③ 输出侧 `out-*` | 106 | `check.py` 的 G1–G10 | 与④合计 142 行：`gate` **35** · `crash` **9** · `issues-only` **6** · `none` **92** |
| ④ 六形态 + 嵌套 | 36 | `check.py` | 六形态逐个进 6 个代表字段；`nest-01..05` 被 G2/G3/G4/G5/G6 拦下，`nest-08/09/10/11` 静默通过 |

被触发的门（③④ 142 行的 `gates_failed` 直方图）：**G1 15 · G2 9 · G3 10 · G4 10 · G5 17 · G6 10 · G7 7 · G10 24**（G8/G9 未被本矩阵触发：G8 只在 route/flow 编号断裂时生效，G9 读的是 `verify_report.json`）。

**静默通过（96 条）的构成**

| 段 | 实测信号 | 归类 | 行数 |
|-|-|-|-|
| 输出侧 | `none` | 未覆盖（设计边界） | 59 |
| 六形态 | `none` | 未覆盖 | 15 |
| 输入侧 | `success+recorded` | **门面内缺陷** | 6 |
| 输入侧 | `success-zero-signal` | 未覆盖（产物仍合规） | 6 |
| 输出侧 | `issues-only` | 仅报 issue（契约只承诺"报 issue"） | 6 |
| 输出侧 | `none`（期望 gate） | **门面内缺陷** | 4 |

**十条门面内缺陷**（逐条证据在 `references/CONTRACT-MATRIX.md` §6）：

| id | 现象 | 实测 |
|-|-|-|
| `in-01` `in-03` `in-04` `in-05` `in-22` | `entities` 给字符串/对象/0/null/元素为字符串 | 退出码 0、`status=success`、`uncertainty` 1 条（契约状态表要求 `partial`） |
| `in-19` | `case.json = {}` | 退出码 0、`status=success`、`uncertainty` 1 条 |
| `nest-08` `nest-09` `nest-10` | `result.json.verify.ok` = `"true"` / `1` / 整个 `verify` 段清空 | `check.py` 退出码 **0**、`ok=true`、`issues=0`（G9 读的是 `verify_report.json`） |
| `nest-11` | `entities=[]` 且 `data_mapping=[]` | `check.py` 退出码 **0**、`ok=true`（G5 的"行数==实体数"两个 0 也相等） |

**回归模式（把"缺陷数没变"变成断言）**：

```bash
python "$SKILL_DIR/scripts/contract_matrix.py" --expect-defects 10
```

实测：`verdict=pass`、退出码 **0**。

**分段/单条复跑**：

```bash
python "$SKILL_DIR/scripts/contract_matrix.py" --section form --only form-03       # 6 行（verify 的六形态）
python "$SKILL_DIR/scripts/contract_matrix.py" --section output --only nest-08 --only nest-09
```

实测（`--section form --only form-03`）：`rows=6`、`violating=5`、`silent_pass=5`、`defects=0`、退出码 **0**。

## T4 · 既有回归（脚本逐字节未改，本次重跑）

| 脚本 | 实测 |
|-|-|
| 题集跑批 `case_set_run.py` | `{"cases": 4, "passed": 4, "failed": 0, "without_expectation": 0, "text_only_probes": 4}`，退出码 **0** |
| 故障注入 `fault_inject.py` | `{"injections": 32, "silent_defects": 9, "exit_mismatch": 0, "silent_mismatch": 0, "preflight_ran": 21, "preflight_caught": 21, "preflight_missed_silent_defects": 0}` |
| 决策探针 `decision_probe.py` | `{"total": 20, "on_table": 20, "deviations": []}`，退出码 **0** |
| 增益对照 | C0：`svg_bytes=3180`、`svg_text_elems=11`、无 `layout.json`/`result.json`；C1：`Q5_png_bytes=54982`、`Q5_pdf_bytes=4448`、`Q6_status_honest=true` |
| 运行前闸门 | `PYTHONIOENCODING=utf-8 python "$SKILL_DIR/scripts/preflight.py" --case "$SKILL_DIR/examples" --deps --json <临时>/pf.json` ⇒ `{"ok": true, "exit": 0, "counts": {"error": 0, "warn": 0, "total": 0}}` |

> 交叉印证：`fault_inject.py` 自己报了 **9** 条"静默缺陷"（它测的是注入后主流程的静默），
> 而本轴的矩阵报了 **10** 条"门面内缺陷"（它测的是契约声明 vs 机器门）。
> 两个数字不同不是矛盾：**前者测"注入会不会静默"，后者测"门有没有承诺过"** ——
> 这正是 v8 补上的视角。

## T5 · 本次**发现**的既有脚本问题（未修，逐条点名）

| 现象 | 证据 | 为什么不修 |
|-|-|-|
| 非对象形态塞进 `output_contract`/`entities`/`relations` 时 `check.py` 抛未捕获异常（`AttributeError`），退出码 1 但**没有结构化报告** | `check.py` 对 `oc.get(...)`/`e.get(...)` 直接调用；③④段实测 **9** 条 `crash`：`out-entities-wrongtype`、`out-entities-huge`、`out-relations-wrongtype`、`out-relations-huge`、`out-output_contract-wrongtype`、`form-00-str`、`form-01-str`、`form-01-nested`、`nest-05` | 修它要动 `check.py` 的判据（非纯增量），会改变退出码语义；规范禁止 |
| `scripts/preflight.py` 在 GBK 控制台打印 ✅ 抛 `UnicodeEncodeError` | 直接运行报 `'gbk' codec can't encode character '\u2705'`；加 `PYTHONIOENCODING=utf-8` 后退出码 0、`ok=true` | 输出编码问题，规避方式写进 README §6 |
| `scripts/decision_probe.py` 的 docstring 指向 `references/DECISION-CASES.md`（该文件不在包内） | `grep -rn "DECISION-CASES" scripts/`；`references/failure-modes.md` 头部已说明它并入附录 C | 既有合并（v6 起），非本轮引入；本轮只补"路径指向哪里"，不加文件 |

## T6 · 本次**没有**测的（如实列出）

| 未测项 | 为什么 |
|-|-|
| 平台固定 3 个案例 | 材料与白板由组织方提供，参赛者不可见；本包数字全部来自合成案例 |
| 真实模型臂对照 | 未起模型臂；`references/GAIN-PROTOCOL.md` 只给可执行下界 C0 |
| 画布真实溢出（D8） | 需极大实体规模；矩阵规模上限 120 实体 |
| 并发重入 / 多进程写同一 `--out` | 探针串行执行 |
| SVG 内部结构违约（手改 layer/id） | 归 `scripts/svg_verify.py` 的 CP2/CP3，不在 G1–G10 |
| PDF/PNG 二进制层面的契约 | 矩阵只看 `result.json` 与 `check.py` 的 G1–G10 |
| 行覆盖率 | 本矩阵测的是**契约面**，不是代码覆盖率 |
| Linux/macOS 上的同一矩阵 | 本轮只在 Windows 11 + CPython 3.13.9 实测 |
| 任何分数 | 本包不宣称具体分数；评分由平台执行 |
