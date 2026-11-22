# TEST.md — 本机真实验收记录（决策显性化版）

> 本文件记录本包在**本机真实执行**的结果，供他人复核。所有命令都能在你自己机器上重跑。
>
> - 机器：Windows 11（10.0.22621）；Python 3.13.9（Anaconda，命令 `python`）；
>   Pillow 12.3.0；reportlab 5.0.0；`cairosvg/svgwrite` 不可用（本包也不需要）。
> - 复现方式：把本包整体复制到**临时目录**（下文记作 `<TMP>/pkg`），把 cwd 设为 `<TMP>`
>   —— **故意不是技能根**，用来验证自定位。`<TMP>` 与 `$SKILL_DIR` 都是占位符，
>   包内不含任何本机绝对路径。
> - 阈值声明：本文件只记录本机实测值，不代表平台正式评分。

## T0 合规自检（形态硬门）—— PASS

```bash
python validate_pkg.py <本包目录>
```

- 扩展名白名单：全部文件为 Markdown / Python / JSON / 纯文本 / CSV 五类文本扩展名；
  **无** PDF / PNG / SVG / PPTX 等二进制或矢量资源；
- 文件数见文末 T8 的实测值（上限 50）；最大单文件 `scripts/main.py`（上限 500KB）；
- 无 `__pycache__`/`*.pyc`、无符号链接；全部文件可 UTF-8 解码；
- 包内**无本机绝对路径**（自检命令见 `README.md §8`；字体探测候选路径的处理见 T7）。

## T1 编译检查 —— 通过

```bash
python -m py_compile "$SKILL_DIR"/scripts/*.py     # 全部脚本 COMPILE OK
```

`decision_probe.py` 与 `bare_baseline.py` 也包含在这一步里（本版新增两个脚本，
均为纯标准库、脚本首部置 `sys.dont_write_bytecode = True`）。

## T2 冒烟：四种调用形态 —— 全部 exit 0

```bash
cd <TMP>                                  # cwd 不是技能根
SKILL_DIR="<TMP>/pkg"
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out <TMP>/out-A
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
  --task "$SKILL_DIR/examples/task.md" --out <TMP>/out-B
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
  --task "$SKILL_DIR/examples/task.md" \
  --merge "$SKILL_DIR/examples/route_spec.mutation.example.json" --out <TMP>/out-C
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/apparatus_spec.example.json" \
  --out <TMP>/out-D
```

实测（本轮记录）：

| 用例 | 命令形态 | exit | 耗时 | case_id | status | verify_ok | 顶层键 | check | G1–G10 |
|-|-|-|-|-|-|-|-|-|-|
| A | `--case <示例目录>` | **0** | 0.404 s | demo-biotech-route-01 | success | true | **18** | `ok:true` | 10/10，issues=[] |
| B | `--case <case.json> --task <task.md>` | **0** | 0.477 s | demo-biotech-route-01 | success | true | **18** | `ok:true` | 10/10，issues=[] |
| C | 追加 `--merge <mutation>` | **0** | 0.455 s | demo-biotech-route-01 | success | true | **18** | `ok:true` | 10/10，issues=[] |
| D | `--case <apparatus_spec.example.json>` | **0** | 0.429 s | demo-apparatus-001 | success | true | **18** | `ok:true` | 10/10，issues=[] |

每次运行产出 7 个文件（`<out>/<case_id>/`）：`evidence.json`、`layout.json`、`figure.svg`、
`figure.png`、`figure.pdf`、`verify_report.json`、`result.json`。

**自查命令**（对任何一次新运行的结果）：

```bash
python "$SKILL_DIR/scripts/check.py" <TMP>/out-A/demo-biotech-route-01/result.json
# → exit 0，{"ok": true, "gates": {G1..G10 全 true}, "issues": []}
```

## T3 确定性：同输入两次运行 —— 4 个文件逐字节一致

| 文件 | det-A / det-B sha256 前缀 | 结论 |
|-|-|-|
| `figure.svg` | `f8b01ce26b622187…` | SAME（逐字节） |
| `layout.json` | `c6c8e155bb6cd7f1…` | SAME（逐字节） |
| `evidence.json` | `42c4e6c263d80f12…` | SAME（逐字节） |
| `verify_report.json` | `5ed91e2a4a13df1d…` | SAME（逐字节） |
| `result.json` | — | 仅 `change_record` 时间戳与 `execution.out_dir` 不同（预期差异） |

**与包内冻结示例对拍**：`figure.svg`（`f8b01ce26b622187`）与 `layout.json`
（`c6c8e155bb6cd7f1`）跟 `examples/output/` 里冻结的那份**完全一致**；
`evidence.json` 的 sha 会随运行目录变化 —— 因为它的 `sources[].path` 记的是**运行时**
解析出来的真实输入路径（这是刻意的：证据要能指向实际读的那份材料），
所以跨目录对拍时比内容不比 sha。`verify_report.json` 里的 `determinism.spec_sha16`
是布局确定性探针，与目录无关，跨运行恒定。

## T4 契约字段覆盖 —— 18/18，无缺项

`result.json` 顶层键与 `references/OUTPUT_CONTRACT.md`「顶层字段清单」逐条比对
（四个用例各查一次）：

```
case_id title status workorder figure_type extraction entities relations
output_contract evidence verify canvas fonts sources uncertainty change_record execution checksum
→ 18/18 命中，缺失：无，多余：无
```

`output_contract` 四段（`editable_sources`/`exports`/`data_mapping`/`element_traceability`）
均为列表且非 null；`exports` 含 png + pdf 两项（含 `width_px/height_px/dpi/font_ttf`）。

## T5 自定位：cwd 与技能根无关 —— 通过

```bash
cd /            # cwd 换到完全无关的位置
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
  --task "$SKILL_DIR/examples/task.md" --out <TMP>/out-E
# → exit 0，check_ok=true
```

`scripts/*.py` 用 `os.path.dirname(__file__)` 定位技能根来读 `templates/`、`assets/`；
`decision_probe.py` 额外把每个用例的子进程 `cwd` 显式设成该用例自己的工作目录，
并且传参前一律 `os.path.abspath` —— 所以探针本身在任何 cwd 下都成立。

## T6 决策用例：20/20 与本包规范一致（本版核心验收）

```bash
python "$SKILL_DIR/scripts/decision_probe.py" --out <TMP>/decisions --json <TMP>/decisions/obs.json
# → exit 0；总耗时 10.434 s（20 个用例，含每次起子进程的启动开销）
# → summary: {"total": 20, "on_table": 20, "deviations": []}
```

逐条观测值（`exit / status / verify.errors / verify.warnings / uncertainty[].scope / 失败门`）
见 `references/DECISION-CASES.md §0`。要点：

- **error 级规则违规四处**（D13/D15/D16/D17）全部得到 `exit 3 + status=partial +
  verify.ok=false + uncertainty[scope=rule_violation] + G9 失败` —— 五处证据同时出现；
- **warn 级规则两处**（D14 `product-terminal`、D18 `recycle-review`）只写 `warnings`，
  `status` 保持 `success`：**warn 永不降级**是显式约定，由本用例钉住；
- **干净失败两处**：D01 退出码 2 且无产物；D02 退出码 1 且写 `failed/result.json`；
- **安静缺陷四处**（D06 全断头后顺序兜底、D09 非法类别归一化、D11/D12 规则资产空/缺失）
  如实观测为"不报错"，并在 `references/failure-modes.md §3` 逐条给出复核办法。

> 未覆盖的 7 行分支（无 Pillow/reportlab、无中文字体、手工改状态、`--merge` 非法端点等）
> 为什么不在自动探针里、以及各自怎么验，见 `references/DECISION-CASES.md §2`。

## T7 负例：连接规则违规被如实拦截（设计行为，非缺陷）

```bash
python "$SKILL_DIR/scripts/main.py" --case <TMP>/neg.json --out <TMP>/out-NEG
# neg.json: apparatus 图，D1(device) --flow--> M1(material)，即"物料作流向终点"
```

实测：`exit 3`（0.437 s）、`status=partial`、`verify.ok=false`、
`verify.errors=[apparatus-flow-into-material]`、`uncertainty[scope=rule_violation]`、
`check.py` 在 G9 报失败。**算法拒绝冒充成功**，这就是评分维度「可靠体验」要的异常处置。

## T8 本包规模（实测）

| 项 | 值 | 上限 |
|-|-|-|
| 文件数 | 见 `validator` 输出（≤50） | 50 |
| 总字节 | 见 `validator` 输出（< 2 MB） | 2 MB |
| 最大单文件 | `scripts/main.py`（< 500 KB） | 500 KB |

## T9 对照下界的可复跑性（本版新增，供 v2 的对照协议引用）

```bash
python "$SKILL_DIR/scripts/bare_baseline.py" --case <某 case.json> --out <TMP>/bare
# → exit 0；stdout 给出 entities_drawn / relations_drawn / dangling_endpoints_kept /
#   source_binding=none / gates_run=[] / status_field=null
```

它**不是交付路径**，只用来给"不加载 Skill 会怎样"提供一个可测量的下界。
本包（v1）只附实现与复跑方式，供你自建对照；协议化的三条件对照
（下界 / 本包 / 同代码关掉门禁 + 预注册指标 + 实跑记录）在**同题的 v2 包**里，不在本包内。

## 限制（如实声明）

- 渲染后端实测为 PIL + reportlab；无 Pillow/reportlab 时按 D12 降级为 `partial`，
  SVG 源文件与证据链不受影响；
- PNG 中文字体依赖本机 TTF；无字体时 `fonts[].found=false` 如实记录（D14），不伪造；
- 实体抽取依赖材料文本结构；复杂表格/多图材料需 Agent 复核证据链（CP1）；
- 示例材料与产物均为**合成**（标注「示例，非正式案例」），与平台正式案例无关；
- 本文件记录的是**本机**执行结果，不是平台正式分数。
