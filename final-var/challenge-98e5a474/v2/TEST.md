# TEST.md — 本机实测记录（v2 · 增益可验证版）

> 实测环境：Windows 10/11 + Python **3.13.9 (Anaconda)**；matplotlib 3.10.6；
> 已装 matplotlib / Pillow / numpy / reportlab / PyMuPDF(fitz)；**无 cairosvg/svgwrite**
> （与平台运行时同类：预览走 matplotlib 镜像）。
> 全部命令用 `$SKILL_DIR` 指向技能根（= 本 SKILL.md 所在目录），**脚本自定位不依赖 cwd**；
> 示例产物一律写在包外临时目录。
>
> **本文件是 `references/GAIN-PROTOCOL.md` §3 的原始读数来源**：协议里 R1–R13
> 的每个数字都能在本文件里找到对应的命令与观测。
> 复跑方式：把本包复制到任意临时目录，按下面命令逐条执行。**不要在包内跑脚本**，
> 否则会生成 `__pycache__` 影响打包形态验收。

## M0 形态与自定位

```bash
find "$SKILL_DIR" -type f | wc -l          # 上限 50
du -sb "$SKILL_DIR"                        # 上限 2 MB
find "$SKILL_DIR" -type f -printf '%s %p\n' | sort -rn | head -1   # 单文件上限 500 KB
```

- 扩展名仅 `.md/.py/.json/.txt/.csv`；
- **无** `__pycache__/`、`*.pyc`、`*.pdf`、`*.png`、`*.svg`、字体文件、符号链接；
- 包内**无**本机绝对路径（盘符形式、`/Users/`、UNC 扩展前缀、staging 路径均无命中）。

## M1 语法与自测

```bash
python -m py_compile "$SKILL_DIR"/scripts/*.py     # exit 0（含新增的 doccheck.py）
python "$SKILL_DIR/scripts/selftest.py"            # exit 0
```

实测：`selftest: all checks passed`，退出码 **0**。

## M2 文档一致性对拍

```bash
PYTHONDONTWRITEBYTECODE=1 python -B "$SKILL_DIR/scripts/doccheck.py"
```

实测输出：

```
doc-check: root=<技能根>
  documents: README.md, SKILL.md, TEST.md, examples/EXPECTED-OUTPUT.md,
             examples/README.md, references/CHECK-INDEX.md,
             references/EDIT-ACTION-SCHEMA.md, references/GAIN-PROTOCOL.md,
             references/OUTPUT_CONTRACT.md, references/RUBRIC_MAP.md,
             references/failure-modes.md, scripts/doccheck.py
  check ids: 64 documented / 82 present in scripts
  rule families: F[12], G[8], R[13]  (declared 33 ids; 29 of them also named in SKILL.md)
  cli flags: 26 documented / 24 declared in scripts
doc-check: CONSISTENT (0 fails, 0 warns)
```

- 对拍内容：① 文档里出现的**每个**检查名必须在 `scripts/` 里真实存在（多写 = FAIL）；
  ② 代码里的**每个**检查名必须被文档解释（少写 = WARN）；③ 规则编号连续无缺号；
  ④ 文档点名的每个 `--flag` 必须真实存在。
- 该工具**只读**：不写文件、不联网、不改退出码语义。

## M3 冒烟：单例端到端（协议 R1 / R2 / R3）

| 命令 | 实测结果 |
|-|-|
| `python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out <tmp>/r1` | **exit 0**；墙钟 **1.53 s**；`status=success`；`figure.svg` **15241 B** + `figure.png` **124129 B** + `figure.pdf` **37929 B** + `result.json`（顶层 **23** 键） |
| 同上，**cwd 在包外** | **exit 0**；1.53 s；`figure.svg` sha256 `163e20f75dc51d9ffb09fd1b6520f2ab7e6e7ff858dfedec64265328b6ffe61e`，与上一行**完全相同** |
| `python "$SKILL_DIR/scripts/validate_result.py" --case "$SKILL_DIR/examples/case.json" --result <tmp>/r1/result.json` | **exit 0**；`VALID: … satisfies OUTPUT_CONTRACT (G1-G8 gates pass, contract echoed).` |
| 同上加 `--doc-check` | **exit 0**；日志多出 `DOC-CHECK …` 行；**产物与不带该参数时逐字节一致** |

## M4 三示例端到端（协议 R4）

```bash
python "$SKILL_DIR/scripts/run_examples.py" --out <tmp>/ex
```

实测：**exit 0**；墙钟 **4.99 s**；schematic / chart / edit 三步各 **exit 0**；
三份 `result.json` 的 G1–G8 各 **exit 0（VALID）**；顶层键分别 **23 / 21 / 21**。

## M5 确定性、数据传播、失败分支（协议 R5–R9、R11–R13）

| 场景 | 命令要点 | 实测读数 |
|-|-|-|
| R5 确定性双跑 | `main.py … --fixed-time 2026-01-01T00:00:00+0800` ×2（不同输出目录） | 两次 `figure.svg` **逐字节一致**（sha256 同上）；两份 `result.json` **唯一差异键 = `artifacts`**（`abspath` 不同），去 `abspath` 后对象完全相同 |
| R6 数据传播 | 复制 `case_chart.json`，把数据表数值翻倍后重跑 | `figure.svg` sha256 由 `fd54b008e1fa10…` 变为 `29c52b9887efa9…` ⇒ **图随数据重绘** |
| R7 材料缺失 | case 的 `sources` 指向不存在文件 | **exit 0**、`status=success`；`sources` 为空数组、`uncertainty` **3** 条；日志 `WARN: source material referenced but not found` |
| R8 未知 kind | manifest 某关系 kind 改 `gibberish`：先单跑 `spec_lint.py`，再走 `main.py` | `spec_lint.py` **exit 1** / `spec_lint: INVALID (CP1)`；`main.py` 产物照出但 `status=partial`、`verification.spec_lint.valid=false`、`fails=[spec_lint.spec.relation_kind]`、命令 **exit 1** |
| R9 无依据即停 | case 无 manifest 且 work 区无 `entities.json` | **exit 1**；写出 `status=failed` 的 `result.json`，`fails=[pipeline]`；日志：`Nothing is drawn without a manifest: inventing entities would violate the no-fabrication rule.` |
| R11 编辑目标不存在 | `{"action":"relabel","relation_id":"R99"}` + `--edit-svg` | 日志 `[edit] fail unknown relation R99`；`change_records` **0** 条；**exit 0**；`validate_result.py` 仍 **VALID** ⇒ **该失败不进 result.json，必须靠条数对拍发现**（协议 G4） |
| R12 草稿抽取 | `extract.py --inputs "$SKILL_DIR/examples/sources/figure03-note.md" --out <tmp>/draft.json` | **exit 0**；墙钟 **0.12 s**；输出 `17 entities, 4 relations, 5 groups`，**全部带 `_draft`** |
| R13 追加导出 | `main.py … --exports tiff,eps` | **exit 0**；产出 `figure.svg/.png/.tiff/.eps` + `result.json`；TIFF **≈ 46 MB**（未压缩 4500×2580@300dpi） |
| 契约四形态 | 契约声明 string/array/object/number/boolean 五个键 | 回显得到 `""` / `[]` / `{}` / `0` / `false`，**无 `null`**，G5 通过 |
| 其它参数 | `--dpi 150` / `--base-name fig03` / `--no-lint` / `--skip-checks` | 各 **exit 0**；`--dpi 150` 时 PNG 由 124129 B 降到 **47805 B**；`--base-name fig03` 产物改名；`--no-lint` 时 `verification.spec_lint` 为 **空对象 `{}`**；`--skip-checks` 时 `verification.checks` **为空**且 `status` 仍为 `success`（⇒ 协议 G1 禁止这类运行计入对照记录） |

## M6 编辑正向路径（协议 R10）

| 命令 | 实测结果 |
|-|-|
| `main.py --case <edit.json> --edit-svg <上一步生成的 figure.svg>`，动作 = `relabel` / `flip_direction` / `rename` / `remove_entity` / `note`（字段名正确） | **exit 1**（本次夹具删掉 E3 后触发 `spec.group_member` fail ⇒ `status=partial`）；`change_records` 共 **7** 条：`relabel`、`flip_direction`、`rename`、`cascade_remove_relation`×2、`remove_entity`、`note`；实体 6→5、关系 5→3；`figure.svg` 与编辑前**不同**（增量改后重绘）；`validate_result.py` 仍 **VALID** |
| 同动作但用错误字段名（`target` 而不是 `relation_id`/`entity_id`） | 日志 `[edit] fail unknown relation …`；`change_records` **0** 条；退出码不受影响 ⇒ 协议 G4 的现场证据 |
| `edit.py <figure.svg> <edits.json>`（独立入口） | 位置参数用法有效；无参数时打印用法 |
| `--edit-svg` + 无内嵌清单的 SVG | **exit 2**；`FATAL: no embedded ER manifest in … cannot do a source-preserving edit` |

## M7 契约门明细（五维"实际效果"的证据）

- `result.json` 顶层 **21/21** 覆盖 `references/OUTPUT_CONTRACT.md` §1 全部字段；
  `case.json` 另声明 2 个契约键（`entities_relations`、`deliverables`）→ 共 **23** 键；
- schematic 冒烟的 `verification.checks` 实测：`svg.editable_text`（真实 `<text>`）·
  `svg.layers` · `svg.manifest_embedded` · `svg.manifest_matches` ·
  `svg.data_entity_attrs` 6/6 · `svg.data_relation_attrs` 5/5 ·
  `svg.data_source_attrs` 5/5 · `pdf.header/pages/fonts_embedded` ·
  `bitmap.dimensions` 4500×2580 · `bitmap.dpi_print`（18 cm 宽有效 ≈635 DPI ≥300）·
  `bitmap.colourspace` · `legend.missing_kinds` / `legend.orphan_items` ·
  `font.cjk`（True）· `traceability.entities` 6/6 · `traceability.relations` 5/5。

## M8 未实测项（**这一节是协议 F8 的执行结果，不是可省略的备注**）

| 未实测项 | 为什么没测 | 影响哪个结论 |
|-|-|-|
| 基线臂（不加载 Skill）在同一夹具上的读数 | 本包不预置基线答案（题面禁止）；平台对照由组织方执行 | 协议 §3 的对照列、§4 的"更高分"结论 |
| 人工修改量 / 返工轮次的跨臂比较 | 需要基线臂读数 | I9 的跨臂结论 |
| 端到端耗时的跨臂比较 | 同上；且耗时受机器负载影响 | I10 的跨臂结论 |
| 科学结论（机制/方向）正确性的对照 | 属 native/LLM Judge 范围 | §4 最后一行的"未测量" |
| TIFF/EPS 在目标期刊模板下的逐项合规 | 缺目标模板 | I8 的 tiff/eps 分支 |
| 真实期刊 PDF 字体嵌入硬性要求 | 缺期刊要求文档 | `pdf.fonts_embedded` 的判定强度 |
| 无 CJK 字体机器上的中文渲染效果 | 本机有 CJK 族 | I8 的 `font.cjk` 分支（本机恒为 True） |

> 结论：**本文件只支撑"本技能一侧可复跑、判据固定、降级有记录"**，
> 不支撑任何跨臂比较。跨臂结论需要真实运行基线臂后按
> `references/GAIN-PROTOCOL.md` §5 的模板重新记账。
