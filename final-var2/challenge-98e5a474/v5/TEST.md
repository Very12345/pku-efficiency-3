# TEST.md — 本机实测记录（v5 · 多案例泛化与题集版）

> 实测环境：Windows 10/11 + Python **3.13.9 (Anaconda)**；matplotlib 3.10.6、
> Pillow 12.3.0、numpy 2.3.5、reportlab 与 PyMuPDF(fitz)、lxml 可用；
> **无 cairosvg / svgwrite**（与平台运行时同类：预览走 matplotlib 镜像）。
> 所有命令用 `$SKILL_DIR` 指向技能根（= 本 SKILL.md 所在目录），**脚本自定位
> 不依赖 cwd**；示例与新案例的产物一律写在**包外**临时目录。
>
> **不要在包内跑脚本**：会生成 `__pycache__`，导致打包形态验收 FAIL。
> 复跑方式：把本包复制到任意临时目录，按下面命令逐条执行。
>
> 前半 T1–T8 是功能实测（出图链路，与基线同源）；**T9 是题集实测**
> （本版新增：5 个案例 + 5 条边界探针，逐条对可接受区间）。

## T0 形态与自定位

```bash
find "$SKILL_DIR" -type f | wc -l          # 上限 50
du -sb "$SKILL_DIR"                        # 上限 2 MB
find "$SKILL_DIR" -type f -printf '%s %p\n' | sort -rn | head -1   # 单文件上限 500 KB
```

本机实测：**44 个文件**（上限 50）· 合计 **378,928 B ≈ 369 KB**（上限 2 MB）·
最大单文件 **27,421 B**（`scripts/case_probe.py`，上限 500 KB）。

- 扩展名仅 `.md/.py/.json/.txt/.csv`（均属许可的 7 种文本类型）；
- **无** `__pycache__/`、`*.pyc`、`*.pdf`、`*.png`、`*.svg`、`*.pptx`、
  `*.jsonl`、`*.zip`、字体文件、符号链接；
- 包内无本机绝对路径残留（脚本只用 `os.path.dirname(__file__)` 自定位，
  文档统一用 `$SKILL_DIR` 与临时目录）。

## T1 语法编译（验收：全部脚本通过，退出码 0）

```bash
python -m py_compile "$SKILL_DIR"/scripts/*.py     # exit 0
```

实测：17 个脚本（15 个与基线逐字节相同 + v1 的 `doccheck.py` + 本版新增 `case_probe.py`）全部编译通过，`exit 0`。

## T2 逻辑自测

```bash
python "$SKILL_DIR/scripts/selftest.py"
# 实测：[PASS] ×35 → "selftest: all checks passed"，exit 0
```

## T3 一键复现包内三示例（验收：三步各 exit 0，三份契约各 VALID）

```bash
python "$SKILL_DIR/scripts/run_examples.py" --out <tmp>/ex
```

实测 **exit 0**，6 个步骤全 PASS：

| 步 | 退出码 | status | 顶层键数 |
|-|-|-|-|
| schematic | 0 | success | 23 |
| chart | 0 | success | 21 |
| edit | 0 | success | 21 |
| schematic:contract / chart:contract / edit:contract | 0 / 0 / 0 | VALID / VALID / VALID | — |

## T4 单案冒烟（两个新题材各跑一遍）

```bash
python "$SKILL_DIR/scripts/main.py" \
    --case "$SKILL_DIR/examples/cases/case_mitophagy.json" --out <tmp>/mito
python "$SKILL_DIR/scripts/main.py" \
    --case "$SKILL_DIR/examples/cases/case_expr_heatmap.json" --out <tmp>/heat
python "$SKILL_DIR/scripts/validate_result.py" \
    --case "$SKILL_DIR/examples/cases/case_mitophagy.json" --result <tmp>/mito/result.json
```

实测：两案均 **exit 0**、`CHECK SUMMARY: success (0 fails, 0 warns, 0 acks)`、
`result.json` **23 键**、契约 **VALID**。机制图案例产物
`figure.svg 14504 B` + `figure.png 6900×2700` + `figure.pdf`；热图案例
`figure.svg 25481 B` + `figure.png 2700×1560` + `figure.pdf`。

## T5 契约门（验收：VALID，退出码 0）

```bash
python "$SKILL_DIR/scripts/validate_result.py" \
    --case "$SKILL_DIR/examples/case.json" --result <tmp>/out1/result.json
# 实测：VALID: ... satisfies OUTPUT_CONTRACT (G1-G8 gates pass, contract echoed).  exit 0
```

## T6 确定性（CP5，验收：两次运行 figure.svg 逐字节一致）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out <tmp>/d1 \
    --fixed-time 2026-01-01T00:00:00+0800      # exit 0
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out <tmp>/d2 \
    --fixed-time 2026-01-01T00:00:00+0800      # exit 0
```

实测两跑 `figure.svg` **逐字节相同**；`result.json` 在去掉
`artifacts[].abspath`（输出目录不同）后完全相同。

> **注**：本轮的示例画布从 `1500×860` 改为 `2300×880`（原因见 T9.2），
> 因此 `figure.svg` 的 sha 与 v4 包不同；**同一份包内**双跑仍然一致。

## T7 失败分支（基础异常处理，实测退出码语义）

| 场景 | 实测 |
|-|-|
| `--case <不存在的文件>` | **exit 2**，`FATAL: case not found: …`，不写产物 |
| `--case <空目录>` | **exit 2**，`FATAL: no case.json found under directory: …` |
| case 无 manifest/entities | **exit 1**，写出 `status=failed` 的 `result.json`（`fails=[pipeline]`） |
| manifest 含未知 kind | **exit 1**，`SPEC_LINT (CP1): INVALID` → `status=partial` |
| 声明不支持的 `chart_type` | **exit 1**，`status=failed`，`fails=[pipeline]`，**无产物**（题集 B1 常驻覆盖） |

## T8 文档↔代码对拍（验收：0 fails / 0 warns，退出码 0）

```bash
python "$SKILL_DIR/scripts/doccheck.py" --root "$SKILL_DIR"
# 实测：check ids 64 documented / 87 present in scripts
#       rule families F[12], S[8] · cli flags 30 documented / 28 declared
#       doc-check: CONSISTENT (0 fails, 0 warns)   exit 0
```

## T9 ★ 题集实测（本版核心，验收：10/10 落在声明区间，退出码 0）

```bash
python "$SKILL_DIR/scripts/case_probe.py" --skill-root "$SKILL_DIR" --out <tmp>/cases
# 实测：10 item(s) → "case-probe: 10/10 item(s) conform to their declared expectations"
#       exit 0；原始机器可读记录 <tmp>/cases/case-report.json
```

耗时约 **15 s**（10 项 × 一次真实主流程子进程，每项 0.9–2.0 s）。

### T9.1 逐项实测

| 项 | 类型 | exit | status | 实体/关系/分组 | 类别 | 画布（声明→内容） | 溢出 | SVG B | PNG px | 键 | 耗时 |
|-|-|-|-|-|-|-|-|-|-|-|-|
| `example-schematic-001` | case | 0 | success | 6 / 5 / 3 | — | 2300×880 → 2090×90 | 否 | 15241 | 6900×2640 | 23 | 1.75 s |
| `example-chart-002` | case | 0 | success | — | 4 | 不适用 | — | 9737 | 2700×1560 | 21 | 1.43 s |
| `example-edit-003` | case | 0 | success | 6 / 5 / 3 | — | 2300×880 → 2090×90 | 否 | 15352 | 6900×2640 | 21 | 1.45 s |
| `synth-mitophagy-101` | case | 0 | success | 6 / 5 / 3 | — | 2300×900 → 2090×90 | 否 | 14504 | 6900×2700 | 23 | 1.67 s |
| `synth-expression-heatmap-102` | case | 0 | success | — | 3 | 不适用 | — | 25481 | 2700×1560 | 23 | 1.99 s |
| `B1-unsupported-chart-type` | probe | **1** | failed | — | — | — | — | （无产物） | — | 23 | 0.88 s |
| `B2-dense-chain-declared-canvas` | probe | 0 | success | 18 / 17 / 1 | — | 1500×900 → **6530×90** | **是** | 29846 | 4500×2700 | 23 | 1.30 s |
| `B3-dense-chain-auto-canvas` | probe | 0 | success | 18 / 17 / 1 | — | **6609×500** → 6530×90 | 否 | 29765 | **19827×1500** | 23 | 1.53 s |
| `B4-special-characters` | probe | 0 | success | 6 / 5 / 3 | — | 2300×880 → 2090×90 | 否 | 15373 | 6900×2640 | 23 | 1.50 s |
| `B5-containment-without-group` | probe | **1** | partial | 6 / 6 / 3 | — | 2300×880 → 2090×90 | 否 | 15617 | 6900×2640 | 23 | 1.51 s |

- 两条 `exit 1` 是**探针**，声明的期望就是"被拦下"：
  B1 → `fails=[pipeline]`（不支持的图型）；B5 → `fails=[spec_lint.spec.containment_group]`。
- 全部项的 `figure.svg` 都是**良构 XML**（lxml 校验通过）；
  特殊字符探针里 `&amp;` 出现、原始 `<up>` 不出现（转义正确）。
- 机制图/编辑/特殊字符/containment 四案的 `traceability_entities` 均为 **1.0（100%）**。

### T9.2 本轮由题集发现并修掉的一处真实缺陷（数据修正，未动脚本）

| 夹具 | 修复前声明 | 实测内容 | 后果 | 修复后 |
|-|-|-|-|-|
| `examples/case.json` | `1500×860` | 2090×90 | 最右节点 E6 落在 x=1850–2090，**整块在 viewBox 外被裁**，而 checks 仍是 0 fail 0 warn | `2300×880`，`canvas_overflow=False` |
| `examples/cases/case_mitophagy.json` | `1500×900` | 2090×90 | 同上 | `2300×900`，`canvas_overflow=False` |

根因：**显式声明 `style.canvas` 时布局不会再自动扩展**（`layout.py` 的确定性
行为），SVG `viewBox`、PNG、PDF 都按声明尺寸裁剪。处置：按
`references/CASE-SET.md` §5 的预算公式（`width ≥ 370×(最大层号) + 节点宽 + 40`）
改声明尺寸，并在 `case_probe.py` 里加**常驻判据** `canvas_overflow: False`，
以后画布算小会被题集直接报偏离。`scripts/*.py` 本轮未改动。

### T9.2b 由题集发现的第二处问题（编辑问题不可见，纯增量修复）

| 项 | 实测 |
|-|-|
| 夹具 | `case_edit.json` 的动作字段名写错（`target` / `value` 而不是 `relation_id` / `to`），走 `--edit-svg` |
| 修复前 | `exit 0` / `status=success` / `change_records=0`，**stdout 连 `[edit] …` 都没有**（`--edit-svg` 分支把 `edit_from_svg()` 的 `ed_issues` 丢掉了） |
| 增量 | `main.py`：该分支收集 `ed_issues`、与另一条分支一致地打印，并把每条写进 `result.json.uncertainty`（**+8/−1 行**，其余脚本逐字节未动） |
| 修复后 | 同一夹具 → `uncertainty` 出现 `edit issue: edit.relabel`；正常夹具（3 条动作）仍为 `change_records=3` |
| 顺带更正 | 旧文档称「走 `--edit-svg` 时 `edits` 字段不生效」——**实测两字段都生效**（各 3 条），已在 `references/EDIT-ACTION-SCHEMA.md` §2.2 与 `SKILL.md` 改正 |

### T9.3 题集自身的自检

| 自检 | 实测 |
|-|-|
| 是否只读技能包 | **是**（案例输入从包里读；夹具与产物写 `--out`；跑完包内文件不变） |
| `--out` 指向包内 | **拒绝**：`exit 2`，`FATAL: --out must not be inside the skill package` |
| 缺 lxml 能否跑 | 能（`xml.etree` 兜底，报告记 `xml_backend`） |
| 判据是否可比 | 每案 `expect` 显式声明；报告里逐条写 `expected / observed / ok` |
| 偏离是否可见 | 有偏离时打印 `DEVIATION <id>: <判据> expected … got …`，进程 `exit 1` |

## T10 未实测 / 不声称

- **`line` / `scatter` 两个 chart 分支**：代码路径存在，但本轮题集没有覆盖，
  **不声称**已验证；
- **真实论文 PDF 材料**：未逐项实测（v4 的注入矩阵用合成 PDF 测过加密件
  拒绝、扫描件抽到 0 字、无第三方库走 stdlib 回退）；
- **>60 节点、网状/环状拓扑、多子图排版、EPS/TIFF 导出、真实期刊字体嵌入审计**：
  均未实测，**不声称**；
- **平台真实打分**：本文件不含任何分数，不做"能拿多少分"的推断；
- 示例与新案例（`examples/**`）全部是**合成演示**，不得作为正式案例答案提交。
