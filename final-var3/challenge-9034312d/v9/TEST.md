# TEST.md — v9 验收记录（全部本机真跑；命令与输出摘要原样保留）

> 所有命令都在**包外临时副本**里执行（先 `cp -r <本包> <临时目录>`），
> 因为在本包目录里跑脚本会生成 `__pycache__`，打包形态门会 FAIL。
> 本文件所有数字都是跑出来的。逐项矩阵见 `references/DEGRADE-MATRIX.md`。

- 环境：Windows 11（10.0.22621）· CPython **3.13.9** · 本机已装 Pillow 12.3.0 / reportlab 5.0.0
  （降级条件靠**受控导入拦截**模拟"没装"，不是真卸载）
- 被测包：本包（v9），**基线 9 个脚本逐字节未改**，其余 6 个既有脚本原样并入，另加 `scripts/degrade_probe.py`
- 复跑总耗时：约 30 秒（smoke + 13 条件降级矩阵 + 既有回归三件套）

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

## T3 · ★ 本包的轴：缺依赖降级链（13 条件）

```bash
python "$SKILL_DIR/scripts/degrade_probe.py" --out <临时> --json <临时>/degrade_report.json
```

实测输出摘要（原样，节选）：

```json
{ "verdict": "pass",
  "base_artifacts": ["evidence.json","figure.pdf","figure.png","figure.svg",
                     "layout.json","result.json","verify_report.json"],
  "deviations": [] }
```

退出码 **0**；13 个条件总耗时 **3.37 s**（单条件 0.09–0.40 s）。逐条件实测：

| id | 拦截 | 退出码 | `status` | 产物数 | 丢掉的产物 | `uncertainty` scope | 实测形态 |
|-|-|-|-|-|-|-|-|
| `c00-base` | — | 0 | `success` | 7 | — | — | 对照 |
| `c01-no-PIL` | `PIL` | **3** | `partial` | **5** | `figure.png` `figure.pdf` | `png` `pdf` | 降级 |
| `c02-no-reportlab` | `reportlab` | 0 | `partial` | **6** | `figure.pdf` | `pdf` | 降级 |
| `c03-no-PIL-no-reportlab` | 两个 | 3 | `partial` | 5 | `figure.png` `figure.pdf` | `png` `pdf` | 降级 |
| `c04-no-PIL.Image` | `PIL.Image` | 3 | `partial` | 5 | `figure.png` `figure.pdf` | `png` `pdf` | **拦截器自证**：与 `c01` 同形 |
| `c05-no-yaml` | `yaml` | 0 | `success` | 7 | — | — | **零差异** |
| `c06-no-numpy` | `numpy` | 0 | `success` | 7 | — | — | **零差异** |
| `c07-no-matplotlib` | `matplotlib` | 0 | `success` | 7 | — | — | **零差异** |
| `c08-no-pptx` | `pptx` | 0 | `success` | 7 | — | — | **零差异** |
| `c09-no-named-five` | 规格点名 5 + PIL + reportlab | 3 | `partial` | 5 | `figure.png` `figure.pdf` | `png` `pdf` | 降级（等效 `c03`） |
| `c10-no-soffice` | PATH 清空 | 0 | `success` | 7 | — | — | **零差异** |
| `c11-no-xml` | `xml` | **1** | 无 | **0** | 全部 7 件 | — | **彻底不可用** |
| `c12-no-hashlib` | `hashlib` | **1** | 无 | **0** | 全部 7 件 | — | **彻底不可用** |

`c11` / `c12` 的 stderr 尾部（原样）：
`ModuleNotFoundError: No module named 'xml' (blocked by degrade_probe)` /
`ModuleNotFoundError: No module named 'hashlib' (blocked by degrade_probe)`。

**分档最小可用环境（由报告 `minimal_env` 计算，非手写）**

| 档位 | 需要什么 | 实测产物 | `status` | 退出码 |
|-|-|-|-|-|
| ① 纯标准库 | CPython 3.10+ | 5 件（`evidence.json` `figure.svg` `layout.json` `result.json` `verify_report.json`） | `partial` | 3 |
| ② + Pillow | `Pillow` | 6 件（+ `figure.png`） | 成功路径见 `c05`–`c08` 对照口径 | 0 |
| ③ + reportlab | `reportlab`（依赖 Pillow） | 7 件（+ `figure.pdf`） | 同② | 0 |

**根因证据（`reportlab` 依赖 `PIL`）**：拦截 `PIL` 后 `import reportlab.pdfgen.canvas` 的
回溯尾部为

```
File ".../reportlab/lib/utils.py", line 15, in <module>
    from PIL import Image
ModuleNotFoundError: No module named 'PIL' (blocked by degrade_probe)
```

⇒ 安装顺序 **Pillow 在前**；"缺 Pillow ⇒ 只丢 PNG"的直觉是**错的**。

**复跑示例**：

```bash
python "$SKILL_DIR/scripts/degrade_probe.py" --only c01-no-PIL --only c02-no-reportlab   # 只跑真实依赖
python "$SKILL_DIR/scripts/degrade_probe.py" --only c04-no-PIL.Image                     # 拦截器自证
python "$SKILL_DIR/scripts/degrade_probe.py" --list                                      # 只列条件表（13 条）
python "$SKILL_DIR/scripts/degrade_probe.py" --expect-deviations 0                       # 回归断言 ⇒ 退出码 0
```

`--expect-deviations 0` 实测：`verdict=pass`、退出码 **0**。

## T4 · 既有回归（脚本逐字节未改，本次重跑）

| 脚本 | 实测 |
|-|-|
| 题集跑批 `case_set_run.py` | `{"cases": 4, "passed": 4, "failed": 0, "without_expectation": 0, "text_only_probes": 4}`，退出码 **0** |
| 故障注入 `fault_inject.py` | `{"injections": 32, "silent_defects": 9, "exit_mismatch": 0, "silent_mismatch": 0, "preflight_ran": 21, "preflight_caught": 21, "preflight_missed_silent_defects": 0}` |
| 决策探针 `decision_probe.py` | `{"total": 20, "on_table": 20, "deviations": []}`，退出码 **0** |
| 增益对照 | C0：`svg_bytes=3180`、`svg_text_elems=11`、无 `layout.json`/`result.json`；C1：`Q5_png_bytes=54982`、`Q5_pdf_bytes=4448`、`Q6_status_honest=true` |
| 运行前闸门 | `PYTHONIOENCODING=utf-8 python "$SKILL_DIR/scripts/preflight.py" --case "$SKILL_DIR/examples" --deps --json <临时>/pf.json` ⇒ `{"ok": true, "exit": 0, "counts": {"error": 0, "warn": 0, "total": 0}}` |

> 口径交叉印证：`fault_inject.py` 的"依赖族"注入（F3-*）测的是**脚本内部**的依赖处理，
> 而本轴测的是**整条流水线**在缺包时的行为（含退出码与产物件数）。
> 两者在本包上不矛盾：`fault_inject` 报 `silent_defects=9`，本轴报 `deviations=0`
> —— 前者是"注入后主流程静默"，后者是"降级形态与声明一致"。

## T5 · 本次**发现**的既有脚本问题（未修，逐条点名）

| 现象 | 证据 | 为什么不修 |
|-|-|-|
| `references/failure-modes.md` 的依赖口径把 Pillow/reportlab 当并列依赖 | 本轴 `c01` 实测：缺 Pillow 时 PNG 与 PDF **一起**丢（reportlab 导入期依赖 PIL，回溯见上） | 只补事实：已在 README §6 与本文件点名；决策规则 D9/D10 不变，脚本逐字节未改 |
| `scripts/preflight.py` 在 GBK 控制台打印 ✅ 抛 `UnicodeEncodeError`，`--json` 报告来不及落盘 | 直接运行报 `'gbk' codec can't encode character '\u2705'`；加 `PYTHONIOENCODING=utf-8` 后退出码 0、`ok=true` | 输出编码问题，规避方式写进 README §6 |
| `scripts/decision_probe.py` 的 docstring 指向 `references/DECISION-CASES.md`（该文件不在包内） | `grep -rn "DECISION-CASES" scripts/`；`references/failure-modes.md` 头部已说明它并入附录 C | 既有合并（v6 起），非本轮引入；本轮只补"路径指向哪里"，不加文件 |

## T6 · 本次**没有**测的（如实列出）

| 未测项 | 为什么 |
|-|-|
| 平台固定 3 个案例 | 材料与白板由组织方提供，参赛者不可见；本包数字全部来自合成案例 |
| 真实模型臂对照 | 未起模型臂；`references/GAIN-PROTOCOL.md` 只给可执行下界 C0 |
| 间接依赖（PIL 自己依赖的 zlib/zip 等） | 本探针只拦顶层包/子模块；拦 C 扩展要换手法 |
| 磁盘满 / 输出目录只读 / 无写权限 | 不属"缺依赖"，归 `fault_inject.py` 的模板族与未覆盖项 |
| Python 版本过低（3.9 及以下） | 本探针不换解释器 |
| 字体缺失 | 属"依赖"但走 `fonts.py` 探测链，`fault_inject.py` 的 F3-* 已覆盖 |
| Linux/macOS 上的同一矩阵 | 本轮只在 Windows 11 + CPython 3.13.9 实测；拦截机制是纯 Python，预期可移植但未实测 |
| 任何分数 | 本包不宣称具体分数；评分由平台执行 |
