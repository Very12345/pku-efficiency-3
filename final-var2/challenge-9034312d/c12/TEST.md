# TEST.md — 本机真实验收记录（增益可验证化版）

> 本文件记录本包在**本机真实执行**的结果。所有命令都能在你自己机器上重跑。
>
> - 环境：Windows 11（10.0.22621）· Python 3.13.9（Anaconda）· Pillow 12.3.0 ·
>   reportlab 5.0.0 · `cairosvg/svgwrite` 不可用（本包不需要）。
> - 复现方式：把本包整体复制到**临时目录**（下文记作 `<TMP>/pkg`），cwd 设为 `<TMP>`
>   —— **故意不是技能根**，用来验证自定位。`<TMP>`/`$SKILL_DIR` 都是占位符。
> - 阈值声明：本文件只记录本机实测值，不代表平台正式评分。

## T0 合规自检（形态硬门）

```bash
python validate_pkg.py <本包目录>          # 期望 [PASS]，0 条 FAIL
```

资源只含 Markdown / Python / JSON / 纯文本 / CSV 五类文本扩展名；无 `__pycache__`/`*.pyc`、无符号链接、
无二进制与矢量资源；全部 UTF-8 可解码；包内无本机绝对路径
（自检命令见 `README.md §8`；字体探测候选路径的处理见 T7）。

## T1 编译检查

```bash
python -m py_compile "$SKILL_DIR"/scripts/*.py     # 全部 COMPILE OK
```

本版新增 `scripts/gain_probe.py` 与 `scripts/bare_baseline.py`，均纯标准库、
首部置 `sys.dont_write_bytecode = True`。

## T2 冒烟：四种调用形态 —— 全部 exit 0

```bash
cd <TMP>; SKILL_DIR="<TMP>/pkg"
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out <TMP>/out-A
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
  --task "$SKILL_DIR/examples/task.md" --out <TMP>/out-B
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
  --task "$SKILL_DIR/examples/task.md" \
  --merge "$SKILL_DIR/examples/route_spec.mutation.example.json" --out <TMP>/out-C
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/apparatus_spec.example.json" --out <TMP>/out-D
```

实测：

| 用例 | exit | 耗时 | case_id | status | verify_ok | 顶层键 | check | G1–G10 |
|-|-|-|-|-|-|-|-|-|
| A 目录形态 | **0** | 0.493 s | demo-biotech-route-01 | success | true | **18** | `ok:true` | 10/10，issues=[] |
| B 文件形态 | **0** | 0.542 s | demo-biotech-route-01 | success | true | **18** | `ok:true` | 10/10，issues=[] |
| C `--merge` 编辑 | **0** | 0.552 s | demo-biotech-route-01 | success | true | **18** | `ok:true` | 10/10，issues=[] |
| D apparatus 示例 | **0** | 0.488 s | demo-apparatus-001 | success | true | **18** | `ok:true` | 10/10，issues=[] |

每次产出 7 个文件：`evidence.json`、`layout.json`、`figure.svg`、`figure.png`、
`figure.pdf`、`verify_report.json`、`result.json`。

## T3 确定性：同输入同目录两轮 —— 4 个文件逐字节一致

| 文件 | sha16（两轮相同） | 结论 |
|-|-|-|
| `figure.svg` | `f8b01ce26b622187` | SAME |
| `layout.json` | `c6c8e155bb6cd7f1` | SAME |
| `evidence.json` | `37492fe3d85d0eb5` | SAME |
| `verify_report.json` | `5ed91e2a4a13df1d` | SAME |
| `result.json` | — | 仅 `change_record` 时间戳与 `execution.out_dir` 不同（预期） |

**跨目录注意**（本版特意写明，避免把路径差误读成结果差）：
`evidence.json` 的 `sources[].path` 记的是**运行时真实输入路径**（取证需要），
所以把包复制到另一个目录再跑，它的 sha **会变**。
要判断"内容是否一致"，请比对 `figure.svg`/`layout.json`/`verify_report.json`，
或忽略 `evidence.json` 里的 `path` 字段。这条也写进了 `SKILL.md §8` 与对照记录。

## T4 契约字段覆盖 —— 18/18

```
case_id title status workorder figure_type extraction entities relations
output_contract evidence verify canvas fonts sources uncertainty change_record execution checksum
→ 18/18 命中，缺失：无，多余：无
```

`output_contract` 四段均为列表且非 null；`exports` 含 png + pdf
（`width_px/height_px/dpi/font_ttf`）。字段定义以 `references/OUTPUT_CONTRACT.md` 为准。

## T5 自定位

```bash
cd /    # 换到完全无关的 cwd
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
  --task "$SKILL_DIR/examples/task.md" --out <TMP>/out-E     # exit 0, check_ok=true
```

## T6 增益对照：三个条件 × 两个案例（本版核心验收）

```bash
# C0 下界 / C1 本包 / C2 同代码关掉门禁
python "$SKILL_DIR/scripts/bare_baseline.py" --case <c>/case.json --out <c>/c0
python "$SKILL_DIR/scripts/main.py" --case <c>/case.json --out <c>/c1
printf '{}' > <c>/empty-rules.json
python "$SKILL_DIR/scripts/main.py" --case <c>/case.json --rules <c>/empty-rules.json --out <c>/c2
# 指标复算（独立于包内模块）
python "$SKILL_DIR/scripts/gain_probe.py" --result <c>/c1/<case_id>/result.json --baseline <c>/c0
```

压缩结论（完整逐项值见 `references/COMPARISON-RECORD-20261122.md §2`）：

| 观察 | C0 下界 | C1 本包 | C2 关掉门禁 |
|-|-|-|-|
| 干净案例：退出码 / status | 0 / 无该字段 | 0 / success | 0 / success |
| 缺陷案例：退出码 / status | 0 / 无该字段 | **3 / partial** | 3 / partial |
| Q1 来源绑定率 | 0.00 | **1.00** | 1.00 |
| Q2 断头端点外露（缺陷案例） | **1** | **0** | 0 |
| Q3 违规暴露（缺陷案例） | 0 | **3** | **0** |
| Q3 违规暴露（干净案例） | 0 | **0** | **0** |
| Q5 PNG / PDF 字节 | 0 / 0 | 39 136–47 080 / 4 028–4 522 | 同 C1 |
| `figure.svg` sha16（缺陷案例） | — | `46dcf42a9749a89c` | `46dcf42a9749a89c` |
| `verify_report.json` sha16（缺陷案例） | — | `6ab174447ee34a4a` | `1c04d7a51ba92920` |
| 单轮耗时 | 0.100–0.112 s | 0.497–0.593 s | 0.485–0.489 s |

**三条可引用的判定**：①C1 与 C2 的 SVG/layout sha 完全相同 ⇒ Q3 的 3 条差只能归因于规则审计；
②干净输入上 C1 与 C2 的 Q3 都是 0 ⇒ 门禁在无缺陷输入上不产生可测差异（负面观察，如实记录）；
③本包比下界**慢** 4.4–5.3 倍，运行效率**无**增益（另一条负面观察）。

## T7 负例与降级路径

| 场景 | 命令 | 期望与实测 |
|-|-|-|
| error 级规则违规 | apparatus 图里 `device --flow--> material` | **实测 `exit 3`、`status=partial`、`verify.errors=[apparatus-flow-into-material]`、`uncertainty[scope=rule_violation]`、G9 失败**（0.49 s） |
| 无 Pillow | 隔离环境卸载后重跑 T2-A | 无 `figure.png`、`status=partial`、`uncertainty[scope=png]`（D10） |
| 无 reportlab | 同上 | 无 `figure.pdf`、`status=partial`、`uncertainty[scope=pdf]`（D10） |
| 无中文字体 | 不装 CJK 字体重跑 | `fonts[role=png].found=false`、如实记录（D13），SVG/PDF 不受影响 |
| `--rules` 指向空文件 | 见 T6 的 C2 | 不报错、退出码按其余检查定；**这正是 C2 条件的构造方式**，在正式交付里属缺陷（见 `SKILL.md §8`） |
| `--case` 文件不存在 | `--case <不存在>` | `exit 2`，stderr 一行 `FATAL:`，不写产物（D1） |
| JSON 不可解析 | 坏 `case.json` | `exit 1`，写 `<out>/failed/result.json`（D2） |

## T8 本包规模

| 项 | 值 | 上限 |
|-|-|-|
| 文件数 | 见 `validator` 输出 | 50 |
| 总字节 | 见 `validator` 输出 | 2 MB |
| 最大单文件 | `scripts/main.py` | 500 KB |

## 限制（如实声明）

- 渲染后端为 PIL + reportlab；缺任一即按 D10 降级为 `partial`，SVG 与证据链不受影响；
- PNG 中文字体依赖本机 TTF；缺字体时如实记录，不伪造；
- 实体抽取依赖材料文本结构；复杂表格/多图材料需 Agent 复核证据链（CP1）；
- 对照实验为 **2 个合成案例 × 3 条件 × 1 轮**，不做统计显著性结论；
- 示例材料与产物均为**合成**（标注「示例，非正式案例」），与平台正式案例无关；
- 本文件记录的是**本机**执行结果，不是平台正式分数。
