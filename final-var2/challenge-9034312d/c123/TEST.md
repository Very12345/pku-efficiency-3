# TEST.md — 本机真实验收记录（机制与复用显性化版）

> 本文件记录本包在**本机真实执行**的结果。所有命令都能在你自己机器上重跑。
>
> - 环境：Windows 11（10.0.22621）· Python 3.13.9（Anaconda）· Pillow 12.3.0 ·
>   reportlab 5.0.0 · `cairosvg/svgwrite` 不可用（本包不需要）。
> - 复现方式：把本包整体复制到**临时目录**（下文记作 `<TMP>/pkg`），cwd 设为 `<TMP>`
>   —— **故意不是技能根**，用来验证自定位。`<TMP>`/`$SKILL_DIR` 都是占位符。
> - 阈值声明：只记录本机实测值，不代表平台正式评分。

## T0 合规自检（形态硬门）

```bash
python validate_pkg.py <本包目录>            # 期望 [PASS]，0 条 FAIL
```

资源只含 Markdown / Python / JSON / 纯文本 / CSV 五类文本扩展名；无 `__pycache__`/`*.pyc`、无符号链接、无二进制/矢量资源；
全部 UTF-8 可解码；包内无本机绝对路径（见 `README.md §9`）。

## T1 编译检查

```bash
python -m py_compile "$SKILL_DIR"/scripts/*.py      # 全部 COMPILE OK
```

本版新增 `scripts/bare_baseline.py`（三层机制的反例实现）与 `scripts/gain_probe.py`
（指标复算器），均纯标准库、首部置 `sys.dont_write_bytecode = True`。

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

| 用例 | exit | 耗时 | case_id | status | verify_ok | 顶层键 | check | G1–G10 |
|-|-|-|-|-|-|-|-|-|
| A 目录形态 | **0** | 0.431 s | demo-biotech-route-01 | success | true | **18** | `ok:true` | 10/10，issues=[] |
| B 文件形态 | **0** | 0.544 s | demo-biotech-route-01 | success | true | **18** | `ok:true` | 10/10，issues=[] |
| C `--merge` 编辑 | **0** | 0.539 s | demo-biotech-route-01 | success | true | **18** | `ok:true` | 10/10，issues=[] |
| D apparatus 示例 | **0** | 0.436 s | demo-apparatus-001 | success | true | **18** | `ok:true` | 10/10，issues=[] |

每次产出 7 个文件：`evidence.json`、`layout.json`、`figure.svg`、`figure.png`、
`figure.pdf`、`verify_report.json`、`result.json`。

## T3 M2 验收：同输入同目录两轮 —— 4 个文件逐字节一致

| 文件 | sha16 | 结论 |
|-|-|-|
| `figure.svg` | `f8b01ce26b622187` | SAME |
| `layout.json` | `c6c8e155bb6cd7f1` | SAME |
| `evidence.json` | `6f17c365b82ea617` | SAME |
| `verify_report.json` | `5ed91e2a4a13df1d` | SAME |
| `result.json` | — | 仅 `change_record` 时间戳与 `execution.out_dir` 不同（预期） |

前两行的 sha 与包内冻结的 `examples/output/` 完全一致；
`verify_report.json` 里的 `determinism.spec_sha16` 是 M2 的几何指纹，与目录无关、跨运行恒定。

**跨目录注意**：`evidence.json` 的 `sources[].path` 记的是运行时真实输入路径（M1 取证需要），
换目录跑它的 sha 会变。要对拍"内容是否一致"，请用
`figure.svg`/`layout.json`/`verify_report.json`。这条同时写在 `SKILL.md §9`、
`README.md §6` 与 `references/REUSE-GUIDE.md §3`（作为搬运陷阱 T2）。

## T4 契约字段覆盖 —— 18/18

```
case_id title status workorder figure_type extraction entities relations
output_contract evidence verify canvas fonts sources uncertainty change_record execution checksum
→ 18/18 命中，缺失：无，多余：无
```

字段定义以 `references/OUTPUT_CONTRACT.md` 为准（**该文件是契约的唯一权威处**，
其它文档只引用、不改写）。

## T5 自定位

```bash
cd /    # 换到完全无关的 cwd
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
  --task "$SKILL_DIR/examples/task.md" --out <TMP>/out-E      # exit 0, check_ok=true
```

## T6 三层机制的反例对照（本版核心验收）

```bash
SKILL_DIR=<本包目录>; CASE=<case.json>; TMP=<临时目录>

python "$SKILL_DIR/scripts/bare_baseline.py" --case "$CASE" --out "$TMP/c0"   # 三层全拿掉
python "$SKILL_DIR/scripts/main.py"          --case "$CASE" --out "$TMP/c1"   # 本包
printf '{}' > "$TMP/empty-rules.json"
python "$SKILL_DIR/scripts/main.py" --case "$CASE" --rules "$TMP/empty-rules.json" --out "$TMP/c2"  # 只关审计
python "$SKILL_DIR/scripts/gain_probe.py" --result "$TMP/c1/<case_id>/result.json" --baseline "$TMP/c0"
```

两个合成案例：`clean`（8 实体 / 7 关系）与 `defective`（12 实体 / 13 关系，**预注入 5 类缺陷**）。
压缩结论（完整逐项值见 `references/COMPARISON-SUMMARY.md`）：

| 观测量 | 三层全拿掉 | 本包 | 只关审计 |
|-|-|-|-|
| Q1 来源绑定率（M1） | **0.00** | **1.00** | 1.00 |
| `layout.json` 是否存在（M2） | 无 | 有 | 有 |
| PNG / PDF 字节（M2） | **0 / 0** | 39 136–47 080 / 4 028–4 522 | 同本包 |
| 断头端点外露（M3，缺陷案例） | **1** | **0** | 0 |
| 违规暴露条数（M3，缺陷案例） | **0** | **3** | **0** |
| 违规暴露条数（M3，干净案例） | 0 | **0** | **0** |
| `figure.svg` sha16（缺陷案例） | — | `46dcf42a9749a89c` | **同左** |
| `layout.json` sha16（缺陷案例） | — | `e661e8c3b770ecae` | **同左** |
| `verify_report.json` sha16（缺陷案例） | — | `6ab174447ee34a4a` | `1c04d7a51ba92920` |
| `status`（缺陷案例） | 无该字段 | `partial` + 退出码 **3** | 同本包 |

**三条可引用的判定**：
①**M3 可单独归因**：本包与"只关审计"两臂的 `figure.svg`/`layout.json` sha 完全相同，
只有 `verify_report.json` 与违规条数不同（3 → 0）——差异只能来自规则审计；
②**M3 不凭空造违规**：干净案例上两臂的违规都是 0（负面观察，如实记录）；
③**M1/M2 的差是"从无到有"**：来源绑定率 0.00 → 1.00、PNG/PDF 从 0 字节占位变真实导出件。

## T7 负例与降级路径

| 场景 | 命令 | 期望与实测 |
|-|-|-|
| error 级规则违规（M3） | apparatus 图里 `device --flow--> material` | **实测 `exit 3`、`status=partial`、`verify.errors=[apparatus-flow-into-material]`、`uncertainty[scope=rule_violation]`、G9 失败**（0.403 s） |
| `--rules` 指向空对象（M3 空转） | `--rules <空 json>` | 不报错、违规条数 0；**这正是本包用来给 M3 单独归因的条件**，在正式交付里属缺陷（`SKILL.md §9` 第 2 条） |
| `--rules` 指向不存在路径 | 同上 | 静默跳过审计（读规则异常被吞），退出码按其余检查定 |
| `--palette` 指向自定义配色 | `--palette <palette.json>` | 正常出图；**`spec_sha16` 会变**（配色是布局输入的一部分，设计使然） |
| 无 Pillow / reportlab | 隔离环境卸载后重跑 | 无对应导出件、`status=partial`、`uncertainty[scope=png\|pdf]`（D4） |
| 无中文字体 | 不装 CJK 字体重跑 | `fonts[role=png].found=false` 如实记录（D5），SVG/PDF 不受影响 |
| `--case` 文件不存在 | `--case <不存在>` | `exit 2`，stderr 一行 `FATAL:`，不写产物（D9） |
| JSON 不可解析 | 坏 `case.json` | `exit 1`，写 `<out>/failed/result.json`（D10） |

## T8 本包规模

| 项 | 值 | 上限 |
|-|-|-|
| 文件数 | 见 `validator` 输出 | 50 |
| 总字节 | 见 `validator` 输出 | 2 MB |
| 最大单文件 | `scripts/main.py` | 500 KB |

> 本版新增 4 份 `references/` 与 2 个脚本（共 6 个文件），文件数已接近上限的一半；
> 后续如需再加文档，**先合并而不是继续新增**（清单里已有可合并的候选：
> `GAIN-PROTOCOL.md` 与 `COMPARISON-SUMMARY.md` 的题头部分）。

## 限制（如实声明）

- 机制对照只跑了 apparatus 图类的两个合成案例（route/flow/hybrid 未测）；
- 反例实现是**一个**下界，不是所有既有方案的代表；换更聪明的方案差距会缩小；
- 对照为单轮（避免"多跑取最好"的选择性报告），不做统计显著性结论；
- 渲染后端为 PIL + reportlab；缺任一即按 D4 降级；
- 示例材料与产物均为**合成**（标注「示例，非正式案例」），与平台正式案例无关；
- 本文件记录的是**本机**执行结果，不是平台正式分数。
