# TEST.md — 本机实测记录（v3 · 机制显性版）

> 实测环境：Windows 10/11 + Python **3.13.9 (Anaconda)**；matplotlib 3.10.6；
> 已装 matplotlib / Pillow / numpy / reportlab / PyMuPDF(fitz)；**无 cairosvg/svgwrite**。
> 全部命令用 `$SKILL_DIR` 指向技能根（= 本 SKILL.md 所在目录），**脚本自定位不依赖 cwd**；
> 示例产物一律写在包外临时目录。
>
> **本文件的组织方式是"按机制取证"**：V1–V5 依次给出 M1–M5 的实测读数，
> V6 给出跨机制的联合判据读数，V7 给出未实测项。
> `references/MECHANISM.md` 里每个机制的"可证伪判据"都能在这里找到对应实测。
>
> 复跑方式：把本包复制到任意临时目录，按下面命令逐条执行。**不要在包内跑脚本**，
> 否则会生成 `__pycache__` 影响打包形态验收。

## V0 形态与自定位

```bash
find "$SKILL_DIR" -type f | wc -l        # 上限 50
du -sb "$SKILL_DIR"                      # 上限 2 MB
find "$SKILL_DIR" -type f -printf '%s %p\n' | sort -rn | head -1   # 单文件上限 500 KB
```

- 扩展名仅 `.md/.py/.json/.txt/.csv`；**无** `__pycache__/`、`*.pyc`、`*.pdf`、
  `*.png`、`*.svg`、字体文件、符号链接；
- 包内**无**本机绝对路径（盘符形式、`/Users/`、UNC 扩展前缀、staging 路径均无命中）。

## V1 机制 M1（方案先行）与本包自测

```bash
python -m py_compile "$SKILL_DIR"/scripts/*.py     # exit 0（含新增 doccheck.py）
python "$SKILL_DIR/scripts/selftest.py"            # exit 0
```

实测：`selftest: all checks passed`，退出码 **0**；自测内含
CP1 好/坏清单断言、G 门拒绝假成功、pdftext 回退、字体探针确定性、CP1–CP5 齐备。

**M1 的判据实测**：

| 输入 | 命令 | 实测 |
|-|-|-|
| 好清单（示例 manifest 抽出） | `spec_lint.py --manifest <good>.json` | **exit 0**，`spec_lint: VALID (CP1)`，`spec.legend_missing_kinds` 与 `spec.data_mapping` 均为 ok |
| 坏清单（把某关系 kind 改成 `gibberish`） | `spec_lint.py --manifest <bad>.json` | **exit 1**，`spec_lint: INVALID (CP1)`，`[fail] spec.relation_kind  relation R4 kind 'gibberish' not in canonical vocabulary` |
| 坏清单走主流程 | `main.py --case <bad-kind>.json` | 产物照出（svc 15206 B）但 **exit 1**、`status=partial`、`verification.spec_lint.valid=false`、`fails=[spec_lint.spec.relation_kind]` |
| 无清单 | `main.py --case <无 manifest 的 case>` | **exit 1**；写 `status=failed`；`fails=[pipeline]`；日志：`Nothing is drawn without a manifest: inventing entities would violate the no-fabrication rule.` |

⇒ M1 的"正向判据"与"推翻条件"都被真实观测到（坏清单**没有**被放过）。

## V2 机制 M2（源文件自描述）

| 场景 | 命令 | 实测 |
|-|-|-|
| 正常生成 | `main.py --case examples --out <t>/p1` | **exit 0**；`figure.svg` **15241 B**；`verification.checks` 中 `svg.editable_text` / `svg.layers` / `svg.manifest_embedded` / `svg.manifest_matches` 均 ok；`svg.data_entity_attrs` 6/6、`svg.data_relation_attrs` 5/5、`svg.data_source_attrs` 5/5 |
| 编辑正向路径 | `main.py --case <edit.json> --edit-svg <figure.svg>`（5 个动作，字段名正确） | **exit 1**（夹具删 E3 触发 `spec.group_member`）；`change_records` **7** 条：`relabel`、`flip_direction`、`rename`、`cascade_remove_relation`×2、`remove_entity`、`note`；实体 6→5、关系 5→3；`figure.svg` 与编辑前不同；契约仍 **VALID** |
| **推翻实验**（无内嵌清单） | `main.py --case <edit.json> --edit-svg <plain.svg>` | **exit 2**；`FATAL: no embedded ER manifest in … cannot do a source-preserving edit` ⇒ 拒绝猜，M2 的正向证据 |
| **盲区取证**（目标不存在） | `relabel` 指向 `R99` | 日志 `[edit] fail unknown relation R99`；`change_records` **0** 条；**exit 0**、契约仍 VALID ⇒ **M2.4 盲区现场证据**（必须靠条数对拍） |

⇒ M2 的"增量编辑"与"拒绝无清单编辑"都被真实观测到；
同时**盲区也被实测**，写在 `MECHANISM.md` §M2.4 而不是藏起来。

## V3 机制 M4（导出预检）与 M5（字体事实源）

正常运行的检查明细（`result.json.verification.checks`）实测：

| 检查名 | 实测值 | 对应机制 |
|-|-|-|
| `bitmap.dimensions` | 4500×2580 | M4 |
| `bitmap.dpi_print` | 18 cm 宽有效 ≈**635 DPI**（阈值 300） | M4 |
| `bitmap.colourspace` | RGBA（RGB 族） | M4 |
| `svg.editable_text` | ok（真实 `<text>`，无 path 化） | M2/M4 |
| `pdf.header` / `pdf.pages` / `pdf.fonts_embedded` | 可读 / 页数正常 / 尽力而为审计 | M4 |
| `font.cjk` | True | M5 |
| `traceability.entities` / `traceability.relations` | 6/6、5/5（100%） | M1/M4 |

**M4 的推翻实验（可复现）**：

| 实验 | 命令 | 期望的推翻效果 |
|-|-|-|
| 降 DPI 到阈值下 | `main.py --case examples --out <t> --dpi 150` | **exit 0**（实测 PNG 由 124129 B 降到 **47805 B**）⇒ 说明 DPI 确实在变；若此时 `bitmap.dpi_print` **仍然 ok**，则判据失效（属需要复核的情形） |
| 追加导出 | `main.py … --exports tiff,eps` | **exit 0**；产出 `figure.tiff`（≈**46 MB**，未压缩 4500×2580@300dpi）与 `figure.eps` ⇒ `artifact.tiff` / `artifact.eps` 参与检查 |
| 跳过检查 | `main.py … --skip-checks` | **exit 0**、`status=success`，但 `verification.checks` **为空** ⇒ 明确标注"该次运行不得当作交付版本" |

**M5 的判据实测**：

| 命令 | 实测 |
|-|-|
| `textfont.py --probe` | **exit 0**；输出含 `cjk_ok: true` 与解析到的族；同机重复调用结论一致（`selftest.py` 断言确定性） |
| `textfont.py --list` | **exit 0**；逐候选族打印 `[x]/[ ]` 与最终解析结果 ⇒ "可定位性"成立 |

## V4 机制 M3（抽取四段回退）

| 场景 | 命令 | 实测 |
|-|-|-|
| 正常抽取 | `pdftext.py --pdf <可抽取.pdf> --out <d>` | **exit 0**；backend 字段反映实际使用的后端 |
| 文件不存在 | `pdftext.py --pdf <nope.pdf> --out <d>` | **exit 2**；`FATAL: pdf not found` |
| 伪造 PDF 头 | `pdftext.py --pdf <garbage.pdf> --out <d>` | **exit 1**（不崩、不产出伪文本） |
| 草稿抽取（材料是 md） | `extract.py --inputs examples/sources/figure03-note.md --out <draft>` | **exit 0**；`17 entities, 4 relations, 5 groups`，全部带 `_draft` |

⇒ M3 的"边界处理"与"诚实报告"都被观测到；stdlib 回退路径由
`selftest.py` 断言"回退不崩"。

## V5 跨机制联合判据

| 联合判据 | 命令 | 实测 |
|-|-|-|
| "换了 cwd 也能跑"（M1–M5 全链路自定位） | `cd <包外> && main.py --case <绝对路径> --out <t>` | **exit 0**；`figure.svg` sha256 `163e20f75dc51d9ffb09fd1b6520f2ab7e6e7ff858dfedec64265328b6ffe61e`，与包内运行**完全相同** |
| "同输入可复现" | `--fixed-time 2026-01-01T00:00:00+0800` ×2 | 两次 `figure.svg` **逐字节一致**；两份 `result.json` **唯一差异键 = `artifacts`**（`abspath`） |
| "改数据图就变"（M1+M2 联动） | chart 数据表数值翻倍后重跑 | `figure.svg` sha256 由 `fd54b008e1fa10…` → `29c52b9887efa9…` |
| "三示例端到端" | `run_examples.py --out <t>` | **exit 0**；三步各 exit 0；三份契约各 VALID；顶层键 23 / 21 / 21 |
| "契约四形态" | 契约声明 5 种类型的键 | 回显得到 `""` / `[]` / `{}` / `0` / `false`，**无 `null`**，G5 通过 |
| "文档与代码没漂移" | `PYTHONDONTWRITEBYTECODE=1 python -B scripts/doccheck.py` | **exit 0**；`check ids: 64 documented / 82 present in scripts`；`rule families: F[12], M[5], S[8]`；`cli flags: 26 documented / 24 declared`；无 FAIL 无 WARN |

## V6 辅助入口

| 命令 | 实测 |
|-|-|
| `main.py --base-name fig03` | **exit 0**；产物改名 `fig03.svg/.png/.pdf` |
| `main.py --work <dir>` | **exit 0**；`layout.json`、`manifest.validated.json` 写到指定目录 |
| `main.py --no-lint` | **exit 0**，但 `verification.spec_lint` 为**空对象 `{}`** ⇒ M1 被关闭，必须显式标注 |
| `main.py --doc-check` | **exit 0**；日志追加 `DOC-CHECK …` 行；**产物与不带该参数时逐字节一致** |
| `edit.py <figure.svg> <edits.json>` | 位置参数用法有效；无参数时打印用法 |
| `--help`（main / spec_lint / pdftext / extract / textfont / validate_result / run_examples / doccheck） | 各 **exit 0**；窄编码控制台由导入区的 `reconfigure(errors="replace")` 兜底 |
| `--case <空目录>` / `<不存在的文件>` | **exit 2**；`FATAL: no case.json found under directory: …` / `FATAL: case not found: …` |

## V7 未实测项（不声称）

| 未实测 | 涉及机制 | 为什么 |
|-|-|-|
| M4 判据的完整推翻矩阵（把 DPI 降到阈值下并核对 `bitmap.dpi_print` 是否翻为 warn） | M4 | 本次只记录了"DPI 变了、PNG 体积随之变化"，未逐档核对检查值 |
| stdlib 回退的抽取**质量**（抽全率） | M3 | 需要一个编码复杂的真实 PDF 作对照 |
| OCR 路径 | M3 | 超出本技能范围（本技能的职责是如实报告不可抽取） |
| 无 CJK 字体机器上的渲染效果 | M5、M4 | 本机有 CJK 族，`font.cjk` 恒为 True |
| TIFF/EPS 在目标期刊模板下的逐项合规 | M4 | 缺目标模板 |
| 在不加载本 Skill 的基线 Agent 上的任何读数 | 全局 | 平台对照由组织方执行；本包不预置基线答案 |

> 结论：本文件支撑的是"**M1–M5 各自的判据在本机被真实观测到，且各机制的已知盲区
> 也被实测**"，不支撑任何跨臂结论，也不支撑上表 V7 里的项目。
