# TEST.md — 本机实测记录（v6 · 全维合并最强版）

> 实测环境：Windows 10/11 + Python **3.13.9 (Anaconda)**；matplotlib 3.10.6、
> Pillow 12.3.0、numpy 2.3.5、reportlab 与 PyMuPDF(fitz)、lxml 可用；
> **无 cairosvg / svgwrite**（与平台运行时同类：预览走 matplotlib 镜像）。
> 所有命令用 `$SKILL_DIR` 指向技能根（= 本 SKILL.md 所在目录），**脚本自定位
> 不依赖 cwd**；示例与新案例的产物一律写在**包外**临时目录。
>
> **不要在包内跑脚本**：会生成 `__pycache__`，导致打包形态验收 FAIL。
> 复跑方式：把本包复制到任意临时目录，按下面命令逐条执行。
>
> 本文件按轴组织：**T1–T4 形态与编译**、**T5–T8 出图链路**、**T9 失败注入**、
> **T10 题集**、**T11 文档对拍**、**T12 未测量**。

## T0 形态与自定位

```bash
find "$SKILL_DIR" -type f | wc -l          # 上限 50
du -sb "$SKILL_DIR"                        # 上限 2 MB
find "$SKILL_DIR" -type f -printf '%s %p\n' | sort -rn | head -1   # 单文件上限 500 KB
```

本机实测：**49 个文件**（上限 50）· 合计 **492,074 B ≈ 480 KB**（上限 2 MB）·
最大单文件 **46,380 B**（`scripts/fault_inject.py`，上限 500 KB）。

- 扩展名仅 `.md/.py/.json/.txt/.csv`（均属许可的 7 种文本类型）；
- **无** `__pycache__/`、`*.pyc`、`*.pdf`、`*.png`、`*.svg`、`*.pptx`、
  `*.jsonl`、`*.zip`、字体文件、符号链接；
- 包内无本机绝对路径残留（脚本只用 `os.path.dirname(__file__)` 自定位，
  文档统一用 `$SKILL_DIR` 与临时目录）。

## T1 语法编译（验收：18 个脚本全过，退出码 0）

```bash
python -m py_compile "$SKILL_DIR"/scripts/*.py     # exit 0
```

实测：18 个脚本（15 个与基线**逐字节相同** + v1 的 `doccheck.py` + 两处纯增量的
`main.py` + 新增的 `fault_inject.py` / `case_probe.py`）全部编译通过。

## T2 逻辑自测

```bash
python "$SKILL_DIR/scripts/selftest.py"
# 实测：[PASS] ×35 → "selftest: all checks passed"，exit 0
```

覆盖 kind 词表映射、布局裁剪与分层、SVG 分层 + 内嵌清单可编辑性、chart 三导出 +
映射一致、图例双向、编辑动作、**spec_lint CP1**、textfont 探针、extract 草稿、
pdftext 回退、validate_result G 门、checklist CP1–CP5 齐备。

## T3 冒烟：主脚本真实出图（验收：exit 0 + 产物落盘）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out <tmp>/o1
```

实测：**exit 0** · `SPEC_LINT (CP1): VALID (0 fails, 0 warns)` ·
`CHECK SUMMARY: success (0 fails, 0 warns, 0 acks)` ·
产物 `figure.svg 15241 B` + `figure.pdf 37944 B` + `figure.png 6900×2640` +
`result.json`（**23 键** = 21 契约字段 + 2 个 `output_contract` 回显键）。

## T4 一键复现三示例（验收：三步各 exit 0，三份契约各 VALID）

```bash
python "$SKILL_DIR/scripts/run_examples.py" --out <tmp>/ex     # exit 0
```

## T5 契约门（验收：VALID，退出码 0）

```bash
python "$SKILL_DIR/scripts/validate_result.py" \
    --case "$SKILL_DIR/examples/case.json" --result <tmp>/o1/result.json
# 实测：VALID: ... satisfies OUTPUT_CONTRACT (G1-G8 gates pass, contract echoed).  exit 0
```

## T6 确定性（CP5，验收：两次运行 figure.svg 逐字节一致）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out <tmp>/d1 \
    --fixed-time 2026-01-01T00:00:00+0800      # exit 0
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out <tmp>/d2 \
    --fixed-time 2026-01-01T00:00:00+0800      # exit 0
```

实测两跑 `figure.svg` **逐字节一致**（sha256 前缀 `24eab86e4c29da42…`）；
`result.json` 去掉 `artifacts[].abspath` 后完全相同。

## T7 两个新题材案例（验收：各 exit 0 + 契约 VALID）

```bash
python "$SKILL_DIR/scripts/main.py" \
    --case "$SKILL_DIR/examples/cases/case_mitophagy.json" --out <tmp>/mito
python "$SKILL_DIR/scripts/main.py" \
    --case "$SKILL_DIR/examples/cases/case_expr_heatmap.json" --out <tmp>/heat
```

实测：两案均 **exit 0** / `success` / 0 fail 0 warn / `result.json` **23 键**；
机制图 `figure.svg 14504 B` + `figure.png 6900×2700`；热图
`figure.svg 25481 B` + `figure.png 2700×1560`。

## T8 失败分支（基础异常处理，实测退出码语义）

| 场景 | 实测 |
|-|-|
| `--case <不存在的文件>` | **exit 2** + `FATAL: case not found: …`，不写产物 |
| `--case <空目录>` | **exit 2** + `FATAL: no case.json found under directory: …` |
| case 无 manifest/entities | **exit 1** + `status=failed` 的 result.json（`fails=[pipeline]`） |
| manifest 含未知 kind | **exit 1** + `partial`（`spec_lint.spec.relation_kind`） |
| 声明不支持的 `chart_type` | **exit 1** + `failed`（`fails=[pipeline]`），无产物 |

## T9 ★ 失败注入与恢复演练（验收：25/25 符合期望，退出码 0）

```bash
python "$SKILL_DIR/scripts/fault_inject.py" --skill-root "$SKILL_DIR" --out <tmp>/fi
# 实测：25 case(s) → "fault-inject: 25/25 conform to the documented expectation"
#       "silent-failure candidates: (none)"   exit 0
```

| 形态 | 用例 | 符合期望 | 静默 | 退出码分布 |
|-|-|-|-|-|
| 输入 damaged | D01–D06 | 6/6 | 0 | `0`×2、`1`×1、`2`×3 |
| 模板/夹具 damaged | D07–D14 | 9/9 | 0 | `0`×6、`1`×3 |
| 依赖 damaged | D15–D21 | 7/7 | 0 | `0`×4、`1`×3 |
| 契约 damaged | D22–D24 | 3/3 | 0 | `0`×2、`1`×1 |
| **合计** | **25** | **25** | **0** | — |

关键行（完整 25 行见 `references/FAULT-MATRIX.md` §3）：

| id | 一句话 | 实测 |
|-|-|-|
| D13 | 规则字典写成非法 JSON | `0` / `success` / `warns=[spec_lint.corpus]`（修复后；修复前裸 traceback 且无 result.json） |
| D18/D19 | 屏蔽 matplotlib / Pillow | `1` / `failed` / `fails=[pipeline]` + `uncertainty` 写明缺失模块 |
| D20 | 无 CJK 字体 | `0` / `success` / `warns=[font.cjk]` + uncertainty |
| D23 | 契约形状不符 | 主流程 `0`/`success`，**独立复核器** `validate_result.py` → `exit 1 INVALID`（G5） |
| D09b | 关系方向对调 | `0` / `success`，`spec_lint` 全 ok ⇒ **盲区 A2** |

**注入隔离自检**：每次注入都 `copytree` 到 tempdir 再弄坏副本（原包 sha 不变）；
D18–D20 只改 `PYTHONPATH` 上的 `sitecustomize`（不改被测脚本）；
`--out` 指向包内会被拒绝（`exit 2`）。

## T10 ★ 题集（验收：10/10 落在声明区间，退出码 0）

```bash
python "$SKILL_DIR/scripts/case_probe.py" --skill-root "$SKILL_DIR" --out <tmp>/rep
# 实测：10 item(s) → "case-probe: 10/10 item(s) conform to their declared expectations"
#       exit 0
```

| 项 | 类型 | exit | status | 实体/关系/分组 | 类别 | 画布（声明→内容） | 溢出 | SVG B | PNG px | 耗时 |
|-|-|-|-|-|-|-|-|-|-|-|
| `example-schematic-001` | case | 0 | success | 6 / 5 / 3 | — | 2300×880 → 2090×90 | 否 | 15241 | 6900×2640 | ~1.7 s |
| `example-chart-002` | case | 0 | success | — | 4 | 不适用 | — | 9737 | 2700×1560 | ~1.4 s |
| `example-edit-003` | case | 0 | success | 6 / 5 / 3 | — | 2300×880 → 2090×90 | 否 | ~15352 | 6900×2640 | ~1.5 s |
| `synth-mitophagy-101` | case | 0 | success | 6 / 5 / 3 | — | 2300×900 → 2090×90 | 否 | 14504 | 6900×2700 | ~1.7 s |
| `synth-expression-heatmap-102` | case | 0 | success | — | 3 | 不适用 | — | 25481 | 2700×1560 | ~2.0 s |
| `B1-unsupported-chart-type` | probe | **1** | failed | — | — | — | — | 无产物 | — | ~0.9 s |
| `B2-dense-chain-declared-canvas` | probe | 0 | success | 18 / 17 / 1 | — | 1500×900 → **6530×90** | **是** | 29846 | 4500×2700 | ~1.3 s |
| `B3-dense-chain-auto-canvas` | probe | 0 | success | 18 / 17 / 1 | — | **6609×500** → 6530×90 | 否 | 29765 | **19827×1500** | ~1.5 s |
| `B4-special-characters` | probe | 0 | success | 6 / 5 / 3 | — | 2300×880 → 2090×90 | 否 | 15373 | 6900×2640 | ~1.5 s |
| `B5-containment-without-group` | probe | **1** | partial | 6 / 6 / 3 | — | 2300×880 → 2090×90 | 否 | 15617 | 6900×2640 | ~1.5 s |

两条 `exit 1` 是**探针**，声明的期望就是"被拦下"（B1 → `pipeline`；
B5 → `spec_lint.spec.containment_group`）。全部 SVG **良构 XML**（lxml 校验）；
B4 里 `&amp;` 出现、原始 `<up>` 不出现（转义正确）。

### T10.1 由题集发现并修掉的画布缺陷（数据修正，未动脚本）

| 夹具 | 修复前 | 实测内容 | 后果 | 修复后 |
|-|-|-|-|-|
| `examples/case.json` | 画布 `1500×860` | 2090×90 | 最右节点 E6 整块在 viewBox 外被裁，checks 仍 0 fail 0 warn | `2300×880`，`canvas_overflow=False` |
| `examples/cases/case_mitophagy.json` | 画布 `1500×900` | 2090×90 | 同上 | `2300×900`，`canvas_overflow=False` |

根因：**显式声明 `style.canvas` 时布局不再自动扩展**（`layout.py` 的确定性
行为），SVG `viewBox`、PNG、PDF 都按声明尺寸裁剪。处置：按
`references/CASE-SET.md` §5 的预算公式改声明尺寸，并在 `case_probe.py` 里加
**常驻判据** `canvas_overflow: False`。`scripts/*.py` 未改动。

### T10.2 由实测修掉的第三处问题（编辑问题不可见，纯增量）

| 项 | 实测 |
|-|-|
| 夹具 | `case_edit.json` 的动作字段名写错（`target` / `value` 而不是 `relation_id` / `to`），走 `--edit-svg` |
| 修复前 | `exit 0` / `success` / `change_records=0`，**stdout 与 result.json 都没有任何痕迹** |
| 增量 | `main.py` 该分支收集 `ed_issues`、一致地打印并写进 `uncertainty`（**+8/−1 行**） |
| 修复后 | 同一夹具 → `uncertainty` 出现 `edit issue: edit.relabel`；正常夹具仍 `change_records=3` |
| 顺带更正 | 旧文档称「走 `--edit-svg` 时 `edits` 字段不生效」——**实测两字段都生效**（`edits` 优先），已改正 |

## T11 文档↔代码对拍（验收：0 fails / 0 warns，退出码 0）

```bash
python "$SKILL_DIR/scripts/doccheck.py" --root "$SKILL_DIR"
# 实测：check ids 64 documented / 89 present in scripts
#       cli flags 31 documented / 29 declared
#       doc-check: CONSISTENT (0 fails, 0 warns)   exit 0
```

## T12 未实测 / 不声称

- **平台真实打分**：本文件不含任何分数，不做"能拿多少分"的推断；
- **`line` / `scatter` 两个 chart 分支**：代码路径存在，本轮题集未覆盖，**不声称**；
- **真实论文 PDF 材料**：未逐项实测（注入矩阵用合成 PDF 覆盖了加密件拒绝、
  扫描件抽到 0 字、无第三方库走 stdlib 回退三种情形）；
- **>60 节点 / 网状环状拓扑 / 多子图排版 / EPS·TIFF 导出 / 期刊字体嵌入审计**：
  均未实测，**不声称**；
- **基线臂对照**：本包**没有**跑过"不加载 Skill 的基线 Agent"，因此
  `references/GAIN-PROTOCOL.md` 里凡是"比基线更好/更快/更省"的结论一律标为
  **未测量**（协议 F8），本文件不为它们背书；
- 示例与新案例（`examples/**`）全部是**合成演示**，不得作为正式案例答案提交。
