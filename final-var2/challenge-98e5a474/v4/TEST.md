# TEST.md — 本机实测记录（v4 · 失败注入与恢复演练版）

> 实测环境：Windows 10/11 + Python **3.13.9 (Anaconda)**；matplotlib 3.10.6、
> Pillow 12.3.0、numpy 2.3.5、reportlab 与 PyMuPDF(fitz) 可用；
> **无 cairosvg / svgwrite**（与平台运行时同类：预览走 matplotlib 镜像）。
> 所有命令用 `$SKILL_DIR` 指向技能根（= 本 SKILL.md 所在目录），**脚本自定位
> 不依赖 cwd**；示例产物一律写在**包外**临时目录。
>
> **不要在包内跑脚本**：会生成 `__pycache__`，导致打包形态验收 FAIL。
> 复跑方式：把本包复制到任意临时目录，按下面命令逐条执行。
>
> 本文件分两半：**T1–T8 是功能实测**（出图链路，与基线同源）；
> **T9 是故障注入实测**（本版新增，25 行矩阵的原始记录）。

## T0 形态与自定位

```bash
find "$SKILL_DIR" -type f | wc -l          # 上限 50
du -sb "$SKILL_DIR"                        # 上限 2 MB
find "$SKILL_DIR" -type f -printf '%s %p\n' | sort -rn | head -1   # 单文件上限 500 KB
```

本机实测：**39 个文件**（上限 50）· 合计 **395,620 B ≈ 386 KB**（上限 2 MB）·
最大单文件 **46,380 B**（`scripts/fault_inject.py`，上限 500 KB）。

- 扩展名仅 `.md/.py/.json/.txt/.csv`（均属许可的 7 种文本类型）；
- **无** `__pycache__/`、`*.pyc`、`*.pdf`、`*.png`、`*.svg`、`*.pptx`、
  `*.jsonl`、`*.zip`、字体文件、符号链接；
- 包内无本机绝对路径残留（脚本只用 `os.path.dirname(__file__)` 自定位，
  文档统一用 `$SKILL_DIR` 与临时目录）。

## T1 语法编译（验收：全部脚本通过，退出码 0）

```bash
python -m py_compile "$SKILL_DIR"/scripts/*.py     # exit 0
```

实测：17 个脚本（15 个与基线逐字节相同 + v1 的 `doccheck.py` + 本版新增 `fault_inject.py`）全部编译通过，`exit 0`。

## T2 逻辑自测

```bash
python "$SKILL_DIR/scripts/selftest.py"
# 实测：[PASS] ×35 → "selftest: all checks passed"，exit 0
```

覆盖 kind 词表映射、布局裁剪与分层、SVG 分层 + 内嵌清单可编辑性、chart 三导出 +
映射一致、图例双向、编辑动作、**spec_lint CP1（好清单 valid / 坏清单捕获
unknown + legend + containment）**、textfont 探针、extract 草稿、pdftext 回退、
validate_result G 门、checklist CP1–CP5 齐备。

## T3 冒烟：主脚本真实出图（验收：exit 0 + 产物落盘）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out <tmp>/out1
```

实测：**exit 0** · `SPEC_LINT (CP1): VALID (0 fails, 0 warns)` ·
`CHECK SUMMARY: success (0 fails, 0 warns, 0 acks)` ·
`schema` 产物 `figure.svg 15241 B` + `figure.pdf 37944 B` + `figure.png 165063 B` +
`result.json`。**`result.json` 顶层 23 键**（21 个契约字段 + 2 个
`output_contract` 回显键），`status=success`，`verification.spec_lint.valid=true`。

## T4 契约门（验收：VALID，退出码 0）

```bash
python "$SKILL_DIR/scripts/validate_result.py" \
    --case "$SKILL_DIR/examples/case.json" --result <tmp>/out1/result.json
# 实测：VALID: ... satisfies OUTPUT_CONTRACT (G1-G8 gates pass, contract echoed).  exit 0
```

## T5 确定性（CP5，验收：两次运行 figure.svg 逐字节一致）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out <tmp>/d1 \
    --fixed-time 2026-01-01T00:00:00+0800      # exit 0
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out <tmp>/d2 \
    --fixed-time 2026-01-01T00:00:00+0800      # exit 0
```

实测 `figure.svg` sha256 两跑相同：`24eab86e4c29da42ab4bdb1f212ec415…`；
`result.json` 在去掉 `artifacts[].abspath`（输出目录不同）后**完全相同**。

## T6 失败分支（基础异常处理，实测退出码语义）

| 场景 | 实测 |
|-|-|
| `--case <不存在的文件>` | **exit 2**，`FATAL: case not found: …`，不写产物 |
| `--case <空目录>` | **exit 2**，`FATAL: no case.json found under directory: …` |
| case 无 manifest/entities，work 区也没有 `entities.json` | **exit 1**，写出 `status=failed` 的 `result.json`（`fails=[pipeline]`） |
| manifest 含未知 kind（`gibberish-relays`） | **exit 1**，`SPEC_LINT (CP1): INVALID (1 fails)` → `status=partial` |
| 编辑目标 SVG 无内嵌清单 | **exit 2** + 明确说明需先用本 Skill 生成 |

> 更细的四形态注入（含材料缺失、字典损坏、缺库、契约形状不符等）见 **T9**。

## T7 一键复现三示例（验收：三步各 exit 0，三份契约各 VALID）

```bash
python "$SKILL_DIR/scripts/run_examples.py" --out <tmp>/ex
```

实测 **exit 0**：

| 步 | 退出码 | status | 顶层键数 |
|-|-|-|-|
| schematic | 0 | success | 23 |
| chart | 0 | success | 21 |
| edit | 0 | success | 21 |
| schematic:contract / chart:contract / edit:contract | 0 / 0 / 0 | VALID / VALID / VALID | — |

## T8 文档↔代码对拍（验收：0 fails / 0 warns，退出码 0）

```bash
python "$SKILL_DIR/scripts/doccheck.py" --root "$SKILL_DIR"
# 实测：check ids 64 documented / 85 present in scripts
#       rule families F[12] · cli flags 30 documented / 28 declared
#       doc-check: CONSISTENT (0 fails, 0 warns)   exit 0
```

## T9 ★ 失败注入与恢复演练（本版核心，验收：25/25 符合期望，退出码 0）

```bash
python "$SKILL_DIR/scripts/fault_inject.py" --skill-root "$SKILL_DIR" --out <tmp>/fault
# 实测：25 case(s) → "fault-inject: 25/25 conform to the documented expectation"
#       "silent-failure candidates: (none)"   exit 0
# 原始机器可读记录：<tmp>/fault/fault-matrix.json（25 条全字段）
```

实测耗时约 **40 s**（每条注入含 1 次整包复制 + 1 次真实主流程子进程，
D15–D17 另含一次 `pdftext.py` 子进程）。完整 25 行矩阵（含每条的
`注入 / 期望 / 实测退出码 / status / uncertainty / fail-warn 检查名 /
是否静默`）见 `references/FAULT-MATRIX.md` §3；这里是**汇总与关键行**：

| 形态 | 用例 | 符合期望 | 静默失败 | 退出码分布 |
|-|-|-|-|-|
| 输入 damaged | D01–D06 | 6/6 | 0 | `0`×2、`1`×1、`2`×3 |
| 模板/夹具 damaged | D07–D14 | 9/9 | 0 | `0`×6、`1`×3 |
| 依赖 damaged | D15–D21 | 7/7 | 0 | `0`×4、`1`×3 |
| 契约 damaged | D22–D24 | 3/3 | 0 | `0`×2、`1`×1 |
| **合计** | **25** | **25** | **0** | — |

关键行（其余见矩阵）：

| id | 一句话 | 实测退出码 / status / 痕迹 |
|-|-|-|
| D13 | `relation-dict.json` 写成非法 JSON | `0` / `success` / `warns=[spec_lint.corpus]`（**修复后**；修复前是裸 traceback 且无 result.json） |
| D18 | 屏蔽 matplotlib | `1` / `failed` / `fails=[pipeline]` + uncertainty 写出缺失模块 |
| D19 | 屏蔽 PIL | `1` / `failed` / 同上（matplotlib 自身依赖 Pillow） |
| D20 | 无 CJK 字体 | `0` / `success` / `warns=[font.cjk]` + uncertainty（PNG 可能缺字，SVG 文字仍在） |
| D23 | 契约声明类型与实际形状不符 | 主流程 `0` / `success`，但**独立复核器** `validate_result.py` → `exit 1 INVALID`（G5） |
| D09b | 关系方向被对调 | `0` / `success`，`spec_lint` 全 ok ⇒ **已知盲区 A2**（结构门判不了语义） |

### T9.1 两个真实缺陷的修复前后实测对照

| # | 场景 | 修复前 | 修复后 |
|-|-|-|-|
| 1 | `assets/relation-dict.json` 损坏 | `exit 1`，stdout 只有 `json.decoder.JSONDecodeError` traceback，**`<out>/result.json` 不存在** | `exit 0` / `success` / 23 键 / `warns=[spec_lint.corpus]`，`figure.svg` 等产物齐全 |
| 2 | 缺 matplotlib（或 Pillow） | `exit 1`，`ModuleNotFoundError` 裸 traceback，**无 `result.json`** | `exit 1` / `failed` / `fails=[pipeline]` / `uncertainty[0]="missing runtime dependency: …"`，产物目录保留 |

复现命令（修复后行为）：

```bash
python "$SKILL_DIR/scripts/fault_inject.py" --skill-root "$SKILL_DIR" --out <tmp>/f \
    --only D13,D18,D19
```

### T9.1b 第三处修复：`--edit-svg` 分支的编辑问题曾经完全不可见

| 项 | 实测 |
|-|-|
| 夹具 | `case_edit.json` 的动作字段名写错（`target` / `value` 而不是 `relation_id` / `to`），走 `--edit-svg` |
| 修复前 | `exit 0` / `status=success` / `change_records=0`，**stdout 无 `[edit]` 提示、result.json 无痕迹**（该分支把 `edit_from_svg()` 的 `ed_issues` 丢掉了） |
| 增量 | `main.py`：该分支收集 `ed_issues`、与另一条分支一致地打印，并写进 `result.json.uncertainty`（**+8/−1 行**） |
| 修复后 | 同一夹具 → `uncertainty` 出现 `edit issue: edit.relabel`；正常夹具仍 `change_records=3` |
| 顺带更正 | 旧文档称「走 `--edit-svg` 时 `edits` 字段不生效」——**实测两字段都生效**，已在 `EDIT-ACTION-SCHEMA.md` §2.2 改正 |

### T9.2 注入隔离自检（证明"演练脚本自己不失效"）

| 自检 | 实测 |
|-|-|
| 每次注入是否改动原包 | **否**（`shutil.copytree` 到 tempdir；25 次运行后原包文件 sha 不变） |
| 注入是否改被测脚本逻辑 | **否**（D18–D20 只改 `PYTHONPATH` 上的 `sitecustomize`；D21 只在副本里包一层抛异常的 `build_schematic_svg`） |
| `--out` 指向包内 | **拒绝**：`exit 2`，`FATAL: --out must not be inside the skill package` |
| 独立复核器 | D01/D22/D23/D24 跑 `validate_result.py`；D08/D09/D10/D13/D14 跑 `spec_lint.py`，结论一并入矩阵 |

## T10 未实测 / 不声称

- **TIFF/EPS 导出**（`--exports tiff,eps`）与真实期刊 PDF 字体嵌入审计：
  本机未逐项验证，**不声称**；
- **平台真实打分**：本文件不含任何分数，不做任何"能拿多少分"的推断；
- `fault_inject.py` 只覆盖**注册过的 25 条**注入，不代表穷尽所有故障；
  6 条已知盲区在 `references/FAULT-MATRIX.md` §4 与 `SKILL.md` §7 公开列出
  （材料内容不可读、方向语义错、独立 `spec_lint.py` 对坏字典仍会崩、
  Pillow 与 matplotlib 缺失去别、`--skip-checks` 自选降级、加密 PDF 主流程不感知）；
- 示例输入与产物均标注"示例，非正式案例"，不得作为正式案例答案或预置答案提交。
