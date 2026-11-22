# TEST.md — 本机真实验收记录（合规重打包版）

> 记录本包在**本机真实执行**的结果，供他人复核。所有命令都可在你自己的机器上重跑。
>
> - 机器：Windows 11（10.0.22621）；Python 3.13.9（Anaconda，命令 `python`）；
>   Pillow 12.3.0；reportlab 5.0.0；`cairosvg/svgwrite` 不可用（本包也不需要）。
> - 复现方式：把本包整体复制到**临时目录**（下文记作 `<TMP>/pkg`），把 cwd 设为
>   `<TMP>`——**故意不是技能根**，用来验证自定位。下文命令中的 `<TMP>` 与
>   `$SKILL_DIR` 都是占位符，包内不含任何本机绝对路径。
> - 阈值声明：本文件只记录本机实测值，不代表平台正式评分。

## T0 合规自检（形态硬门）—— PASS

```bash
python validate_pkg.py <本包目录>
```

```
[PASS] challenge-9034312d  files=39
```

- 扩展名白名单：`39` 个文件全部为 `.md`(13) / `.json`(15) / `.py`(9) / `.txt`(1) / `.csv`(1)；
- 文件数 **39**（上限 50）；总字节 **265,733 B ≈ 259.5 KB**（上限 2 MB）；最大单文件
  `scripts/main.py` **21,943 B ≈ 21.4 KB**（上限 500 KB）；
- 无 `__pycache__`/`*.pyc`、无符号链接、无 `.pdf/.png/.svg/.pptx` 等非文本资源；
- 全部文件可 UTF-8 解码；包内**无本机绝对路径**（自检命令见 `README.md §8`，
  字体探测候选路径的处理见 T7）。

## T1 编译检查 —— 通过

```bash
python -m py_compile "$SKILL_DIR"/scripts/*.py     # COMPILE OK（9 个脚本全过）
```

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

| 用例 | 命令形态 | exit | case_id | status | verify_ok | check_ok | G1–G10 |
|-|-|-|-|-|-|-|-|
| A | `--case <示例目录>`（目录形态，自动取 case.json + task.md） | **0** | demo-biotech-route-01 | success | true | true | 10/10，issues=[] |
| B | `--case <case.json> --task <task.md>` | **0** | demo-biotech-route-01 | success | true | true | 10/10，issues=[] |
| C | 追加 `--merge <mutation>`（编辑既有图稿） | **0** | demo-biotech-route-01 | success | true | true | 10/10，issues=[] |
| D | `--case <apparatus_spec.example.json>`（apparatus 三桶布局） | **0** | demo-apparatus-001 | success | true | true | 10/10，issues=[] |

每次运行产出 7 个文件（`<out>/<case_id>/`）：

```
evidence.json      实体/关系 locator+quote + 材料 sha256（route 例：实体 10 / 关系 9 / 证据 19 条 / 材料 2 个）
layout.json        布局模型（route 例 3 列：文库构建/筛选/鉴定，步骤编号 1..7 连续）
figure.svg         可编辑分层 SVG（5 层 layer:*；<text> 真实文本；实体组带 data-source）
figure.png         PNG 预览（200 DPI；PIL + 本机中文字体；无字体时 fonts[].found=false 并降级）
figure.pdf         PDF 预览（reportlab 矢量，CID 字体 STSong-Light）
verify_report.json 校验报告（图层/文本/箭头/编号/图例/连接规则 + spec_sha16）
result.json        18 个顶层字段（含 output_contract + evidence + verify + checksum）
```

**自查命令**（对任何一次新运行的结果）：

```bash
python "$SKILL_DIR/scripts/check.py" <TMP>/out-A/demo-biotech-route-01/result.json
# → exit 0，{"ok": true, "gates": {G1..G10 全 true}, "issues": []}
```

## T3 确定性：同输入两次运行 —— 4 个文件逐字节一致

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out <TMP>/det-A
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out <TMP>/det-B
```

| 文件 | det-A / det-B sha256 前缀 | 结论 |
|-|-|-|
| `figure.svg` | `f8b01ce26b622187…` | SAME（逐字节） |
| `layout.json` | `c6c8e155bb6cd7f1…` | SAME（逐字节） |
| `evidence.json` | `c49c19588b681e9c…` | SAME（逐字节） |
| `verify_report.json` | `5ed91e2a4a13df1d…` | SAME（逐字节） |
| `result.json` | — | 仅 `change_record` 时间戳与 `execution.out_dir` 不同（预期差异） |

**与包内冻结示例对拍**（`examples/output/`）：`layout.json`、`verify_report.json`
逐字节相同（`c6c8e155bb6cd7f1…` / `5ed91e2a4a13df1d…`；apparatus 例为
`a0fd97d31d1a84c8…` / `ff5c2a254f88b450…`），`evidence.json` 除合规净化过的
`sources[].path` 字段外逐字节相同 ⇒ 包内示例产物确由本包脚本在同一输入上真实运行产生，
且可被任何人重跑复现。

## T4 契约字段覆盖 —— 18/18，无缺项

`result.json` 顶层键与 `references/OUTPUT_CONTRACT.md`「顶层字段清单」逐条比对
（三组用例各查一次：A、D、C）：

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
文档中的命令一律写成 `python "$SKILL_DIR/scripts/main.py" …`，
且 `SKILL.md §0` 给出 `$SKILL_DIR` 的解析方式（平台安装位置 `/skills/weekly-skill`）。

## T6 负例：连接规则违规被如实拦截（设计行为，非缺陷）

构造违规案例（apparatus 内 V1 流向物料、V2 `sequence` 连容器、V3 产物反向流入装置）后运行：

```bash
python "$SKILL_DIR/scripts/main.py" --case <TMP>/neg-violation.json --out <TMP>/out-NEG
```

结果：

- `exit 3`（契约门未过，**不冒充成功**）；`status=partial`；`verify_ok=false`；
- `check.py` issues：`G9: verify_report 未全绿: {status: attention, errors: 2, warnings: 1, …}`；
- `result.json.verify.errors`：`sequence-step-only`、`apparatus-flow-into-material`（error 级）；
  `warnings`：`product-terminal`（warn 级，仅提示复核）；
- `result.json.uncertainty` 追加 `scope=rule_violation` ⇒ 按 D11 强制 partial。

## T7 资源形态：二进制/矢量文件改为运行时生成

| 原形态 | 本包做法 | 验证 |
|-|-|-|
| `examples/output/*/figure.svg`、`figure.png`、`figure.pdf` | **不随包发布**；由 `main.py` 运行时生成 | T2 每次运行都产出这 3 个文件 |
| `examples/output/*/{evidence,layout,verify_report,result}.json` | 保留（纯文本证据），并把本机绝对路径净化为相对/运行时值 | T3 对拍一致；T0 无路径泄漏 |
| 字体 `.ttf/.otf` 资源 | 不打包；运行时按候选路径探测（`scripts/fonts.py`，`%WINDIR%` 优先） | 无字体时 `fonts[].found=false` + 降级（D9） |
| `templates/*.pptx` 回退模板 | 本题不使用 PPTX（图稿走手写 SVG）；无需回退模板脚本 | 包内无 `.pptx` |

## 限制（如实声明）

- 渲染后端实测为 PIL + reportlab；无 Pillow/reportlab 时按 D10 降级为 `partial`
  （PNG 或 PDF 缺失），SVG 源文件与证据链不受影响；
- PNG 中文字体依赖本机 TTF；无字体时 `fonts[].found=false` 如实记录（D9），不伪造；
- 实体抽取依赖材料文本结构；复杂表格/多图材料需 Agent 复核证据链（CP1）；
- 示例材料与产物均为**合成**（标注「示例，非正式案例」），与平台正式案例无关；
- 本文件记录的是**本机**执行结果，不是平台正式分数。
