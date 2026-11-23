# TEST.md — v7 验收记录（全部本机真跑；命令与输出摘要原样保留）

> 所有命令都在**包外临时副本**里执行（先 `cp -r <本包> <临时目录>`），
> 因为在本包目录里跑脚本会生成 `__pycache__`，打包形态门会 FAIL。
> 本文件所有数字都是跑出来的；没有估计值，也没有"应当如此"。
> 逐字段的确定性证据表见 `references/DETERMINISM.md`。

- 环境：Windows 11（10.0.22621）· CPython **3.13.9** · Pillow 12.3.0 · reportlab 5.0.0 · 本机有中文字体
- 被测包：本包（v7），**基线 9 个脚本逐字节未改**，其余 6 个既有脚本原样并入，另加 `scripts/determinism.py`
- 复跑总耗时：约 50 秒（smoke + 确定性 8 次运行 + 既有回归三件套）

## T1 · 合规形态

```bash
python validate_pkg.py <本包目录>
```

实测：`[PASS]`，**49 个文件**（上限 50），0 条 FAIL、0 条 warn。
检查项：扩展名白名单（`.md/.py/.json/.txt/.csv/.yaml/.yml`）、文件数、单文件大小、
合计体积、无符号链接、无 `__pycache__`/`.pyc`、全部 UTF-8、每个 `.py` 均可 `py_compile`、
包内不含本机绝对路径、`SKILL.md` 的 YAML frontmatter 含 `name` 与 `description`。

## T2 · 主流程可跑（示例案例）

```bash
cd <临时目录>
SKILL_DIR=<包副本>
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out <临时输出目录>
```

实测：退出码 **0**，`status=success`，`check_ok=true`，`gates` G1–G10 **全 true**、`issues=[]`，
`result.json` 顶层键 **18 个**，产物 **7 件**
（`evidence.json` / `layout.json` / `figure.svg` / `figure.png` / `figure.pdf` /
`verify_report.json` / `result.json`）。

## T3 · ★ 本包的轴：确定性（8 次运行）

```bash
python "$SKILL_DIR/scripts/determinism.py" --out <临时> --json <临时>/determinism_report.json --runs 4
```

实测输出摘要（原样）：

```json
{ "verdict": "pass", "case_id": "demo-biotech-route-01", "runs": 8, "artifacts": 7,
  "identical": false,
  "identical_by_condition": { "raw": false, "stabilized": true },
  "identical_normalized": { "raw": true, "stabilized": true },
  "raw_identical_files": 5, "stabilized_identical_files": 7,
  "volatile_fields": ["change_record/0/time", "execution/out_dir"], "unexplained": 0 }
```

退出码 **0**。8 次运行现场（`runs[]`）：

| 条件 | 次数 | 独立 pid | cwd | PYTHONHASHSEED | RL_INVARIANT | 冻结时钟 | 单次耗时 |
|-|-|-|-|-|-|-|-|
| raw | 4 | 4 个互不相同 | 4 个不同目录 | 0 / 1 / 12345 / 31337 | 否 | 否 | 0.33–0.37 s |
| stabilized | 4 | 4 个互不相同 | 4 个不同目录 | 0 / 1 / 12345 / 31337 | 是 | 是 | 0.32–0.39 s |

逐文件判定（`per_file_sha256` 的不同 sha 数）：

| 产物 | raw | stabilized |
|-|-|-|
| `evidence.json` | 1（一致） | 1 |
| `layout.json` | 1（一致） | 1 |
| `figure.svg` | 1（一致） | 1 |
| `figure.png` | 1（一致） | 1 |
| `verify_report.json` | 1（一致） | 1 |
| `result.json` | **4（不一致）** | 1 |
| `figure.pdf` | **4（不一致）** | 1 |

⇒ 在**平台默认环境**下，"同一张图"（SVG/布局/证据/校验/PNG）已经逐字节相同；
`result.json` 与 `figure.pdf` 各带一条**审计性**漂移（时间戳、输出路径、PDF 元数据），
两条都在报告里逐条声明并给出稳定化手段，稳定化后 **7/7 逐字节相同**。

**非 JSON 漂移**：`figure.pdf` 在 raw 下 **4 个不同 sha**、稳定化后 **1 个**（`resolved_by_stabilizer=true`）。

**手工对拍（不用探针，独立复核）**：

```bash
S=$(mktemp -d); cp -r "$SKILL_DIR" "$S/skill"
for i in 1 2; do
  RL_INVARIANT=1 PYTHONHASHSEED=$i python "$S/skill/scripts/main.py" \
    --case "$S/skill/examples" --out "$S/out" >/dev/null
  sha256sum "$S/out"/*/figure.svg "$S/out"/*/layout.json "$S/out"/*/figure.png
done
```

实测：两轮 `figure.svg` / `layout.json` / `figure.png` 的 sha256 **两两相同**
（`figure.svg f8b01ce26b62…` / `layout.json c6c8e155bb6c…` / `figure.png 990ab3a46d80…`，前 12 位）。

## T4 · 既有回归（脚本逐字节未改，本次重跑）

| 脚本 | 命令 | 实测 |
|-|-|-|
| 题集跑批 | `python "$SKILL_DIR/scripts/case_set_run.py" --out <临时> --json <临时>/r.json --text-only` | `{"cases": 4, "passed": 4, "failed": 0, "without_expectation": 0, "text_only_probes": 4}`，退出码 **0** |
| 故障注入 | `python "$SKILL_DIR/scripts/fault_inject.py" --out <临时> --json <临时>/r.json` | `{"injections": 32, "silent_defects": 9, "exit_mismatch": 0, "silent_mismatch": 0, "preflight_ran": 21, "preflight_caught": 21, "preflight_missed_silent_defects": 0}` |
| 决策探针 | `python "$SKILL_DIR/scripts/decision_probe.py" --out <临时> --json <临时>/o.json` | `{"total": 20, "on_table": 20, "deviations": []}`，退出码 **0** |
| 增益对照 | `bare_baseline.py` → `main.py` → `gain_probe.py` | C0：`svg_bytes=3180`、`svg_text_elems=11`、无 `layout.json`/`result.json`、`png_bytes=0`；C1：`Q5_png_bytes=54982`、`Q5_pdf_bytes=4448`、`Q6_status_honest=true`、`svg_sha16=f8b01ce26b622187` |
| 运行前闸门 | `PYTHONIOENCODING=utf-8 python "$SKILL_DIR/scripts/preflight.py" --case "$SKILL_DIR/examples" --deps --json <临时>/pf.json` | `{"ok": true, "exit": 0, "counts": {"error": 0, "warn": 0, "total": 0}}`，退出码 **0** |

## T5 · 本次**发现**的既有脚本问题（未修，逐条点名）

| 现象 | 证据 | 为什么不修 |
|-|-|-|
| `scripts/preflight.py` 在 GBK 控制台直接运行时打印 ✅ 抛 `UnicodeEncodeError`，`--json` 报告来不及落盘 | 直接运行：`UnicodeEncodeError: 'gbk' codec can't encode character '\u2705'`；加 `PYTHONIOENCODING=utf-8` 后退出码 0、`ok=true` | 规范要求既有脚本尽量逐字节不变；这是**输出编码**问题，规避方式已写进 README §6 |
| `scripts/decision_probe.py` 的 docstring 指向 `references/DECISION-CASES.md`（该文件不在包内） | `grep -rn "DECISION-CASES" scripts/`；`references/failure-modes.md` 头部已说明它并入附录 C | 既有合并（v6 起），非本轮引入；本轮只补"路径指向哪里"的说明，不加文件 |

## T6 · 本次**没有**测的（如实列出）

| 未测项 | 为什么 |
|-|-|
| 平台固定 3 个案例 | 材料与白板由组织方提供，参赛者不可见；本包数字全部来自合成案例 |
| 真实模型臂对照（裸 Agent vs 加载 Skill） | 未起模型臂；`references/GAIN-PROTOCOL.md` 只给可执行下界 C0 |
| 跨操作系统 / 跨 Pillow·reportlab 版本的字节级一致 | 见 `references/DETERMINISM.md` §7；本轮只在 Windows 11 + CPython 3.13.9 实测 |
| 并发运行（多进程写同一 `--out`） | 探针串行执行 |
| 实体数 > 24 / 阶段数 > 5 | 未纳入题集，布局拥挤度未评估 |
| 磁盘写满、输出目录只读、超长材料、时区差异 | 未纳入本轮语料 |
| 任何分数 | 本包不宣称具体分数；评分由平台执行 |
