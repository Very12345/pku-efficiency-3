# TEST.md — 本机实测记录（challenge-98e5a474 合规形态包）

> 实测环境：Windows 10/11 + Python **3.13.9 (Anaconda)**；
> 已装 matplotlib / Pillow / numpy / reportlab / PyMuPDF(fitz)；
> **无 cairosvg/svgwrite**（与平台运行时同类：预览走 matplotlib 镜像）。
> 所有命令用 `$SKILL_DIR` 指向技能根（= 本 SKILL.md 所在目录），
> **脚本自定位不依赖 cwd**；示例产物全部写在包外临时目录。
>
> 复跑方式：把本包复制到任意临时目录，按下面命令逐条执行即可。

## T0 打包形态（验收：只有 UTF-8 文本、数量/体积达标、无残留）

```bash
find "$SKILL_DIR" -type f | wc -l        # 34 个文件（上限 50）
du -sb "$SKILL_DIR"                      # 275838 B ≈ 269 KB（上限 2 MB）
find "$SKILL_DIR" -type f -printf '%s %p\n' | sort -rn | head -1
#                                         # 最大单文件 23016 B（scripts/main.py，上限 500KB）
```

- 扩展名仅 `.md/.py/.json/.txt/.csv`（均属许可的 7 种文本类型之一）；
- **无** `__pycache__/`、`*.pyc`、`*.pdf`、`*.png`、`*.svg`、`*.pptx`、
  `*.jsonl`、`*.zip`、字体文件、符号链接；
- 包内绝对路径残留检查无命中：不含 Windows 盘符绝对路径（形如「盘符 + 冒号
  + 反斜杠」）、不含 `/Users/` 前缀、不含 UNC 扩展前缀、不含 `/d/Work` 这类
  本机 staging 路径（脚本只用 `os.path.dirname(__file__)` 自定位，文档统一
  用 `$SKILL_DIR` 与临时目录）。

## T1 语法编译（验收：15 个脚本全过，退出码 0）

```bash
python -m py_compile "$SKILL_DIR"/scripts/*.py     # exit 0
```

## T2 自测（本机实测：35 项 PASS / 0 FAIL，退出码 0）

```bash
python "$SKILL_DIR/scripts/selftest.py"
# [PASS] ×35 → "selftest: all checks passed"，exit 0
```

覆盖：kind 词表映射/未知 kind 标记、布局裁剪与分层、SVG 分层+内嵌清单可
编辑性、chart 三导出+映射一致、图例双向、编辑动作（含残留引用解析）、
**spec_lint CP1（好清单 valid / 坏清单捕获 unknown+legend+containment）**、
**textfont 探针（本机解析到 Microsoft YaHei, cjk_ok=True，确定性）**、
**extract 草稿（从合成材料抽到 TNF-α…IL6 等实体+4 条关系）**、
**pdftext（backend 探测 + stdlib 回退不崩）**、
**validate_result G 门（缺产物/假成功均被拒）**、checklist CP1–CP5 齐备。

## T3 冒烟：主脚本真实出图（验收：exit 0 + 产物落盘）

| 命令 | 实测结果 |
|-|-|
| `python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out <tmp>/out1` | **exit 0**；SPEC_LINT(CP1) **VALID (0 fails/0 warns)** → CHECK SUMMARY **success (0 fails, 0 warns, 0 acks)** → `figure.svg` 15241 B + `figure.pdf` 37929 B + `figure.png` 124129 B + `result.json` |
| 同上但 **cwd 在包外**（只给绝对路径） | **exit 0**，输出与上一致 —— 证明自定位成立 |
| `python "$SKILL_DIR/scripts/run_examples.py" --out <tmp>/examples` | **exit 0**；schematic / chart / edit 三步各 exit 0，三份 `result.json` 的 G1–G8 契约校验各 **exit 0（VALID）** |

schematic 冒烟检查明细（`result.json.verification.checks`，全部 ok）：
`svg.editable_text`（19 个 `<text>`，0 个被 path 化的文字）· `svg.layers`（6 个
语义图层）· `svg.manifest_embedded` · `svg.manifest_matches` ·
`svg.data_entity_attrs` 6/6 · `svg.data_relation_attrs` 5/5 ·
`svg.data_source_attrs` 5/5 · `pdf.header/pages/fonts_embedded` ·
`bitmap.dimensions` 4500×2580 · `bitmap.dpi_print`（18 cm 宽有效 ≈635 DPI ≥300）·
`bitmap.colourspace` RGBA · `legend.missing_kinds` / `legend.orphan_items` ·
`font.cjk`（Microsoft YaHei, True）· `traceability` 实体 6/6、关系 5/5（100%）。

## T4 契约门（验收：三份 result.json 均 VALID，退出码 0）

```bash
python "$SKILL_DIR/scripts/validate_result.py" \
    --case "$SKILL_DIR/examples/case.json" --result <tmp>/out1/result.json
# VALID: ... satisfies OUTPUT_CONTRACT (G1-G8 gates pass, contract echoed).  exit 0
```

- `result.json` 顶层键 **21/21** 覆盖 `references/OUTPUT_CONTRACT.md` §1 全部字段；
- 额外回显 `case.json.output_contract` 声明的 2 个键（`entities_relations`、
  `deliverables`，四形态默认值），顶层共 **23** 键；
- chart / edit 两份 result.json 各 **21** 键，`validate_result.py` 同样 VALID。

## T5 确定性（CP5，验收：两次运行 figure.svg 逐字节一致）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out <tmp>/d1 \
    --fixed-time 2026-01-01T00:00:00+0800      # exit 0
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out <tmp>/d2 \
    --fixed-time 2026-01-01T00:00:00+0800      # exit 0
```

实测 `figure.svg` sha256 两跑相同：
`163e20f75dc51d9ffb09fd1b6520f2ab7e6e7ff858dfedec64265328b6ffe61e`。
`result.json` 在 `--fixed-time` 下除 `artifacts[].abspath`（输出目录不同）
外一致；不加 `--fixed-time` 时差异**仅限 `generated_at`**——这是如实差异。

## T6 失败分支（异常处理，实测退出码语义）

| 场景 | 实测 |
|-|-|
| `--case <不存在的文件>` | **exit 2**，`FATAL: case not found: … (pass a case.json file or a directory containing case.json)`，不写产物 |
| `--case <空目录>` | **exit 2**，`FATAL: no case.json found under directory: …` |
| case 无 manifest/entities，work 区也没有 `entities.json` | **exit 1**，写出 `status=failed` 的 `result.json`（`verification.checks.fails=[pipeline]`），工作不丢失 |
| manifest 含未知 kind（`gibberish`） | **exit 1**，`SPEC_LINT (CP1): INVALID (1 fails, 0 warns)` → `status=partial`、`verification.spec_lint.valid=false`，明细可查 |
| 渲染致命异常 | 捕获 → 写 `status=failed` 的 result.json（代码路径同上报错分支） |
| 编辑目标 SVG 无内嵌清单 | 退出码 2 + 明确说明需先用本 Skill 生成 |

## T7 辅助脚本实测

| 命令 | 实测结果 |
|-|-|
| `python "$SKILL_DIR/scripts/extract.py" --inputs "$SKILL_DIR/examples/sources/figure03-note.md" --out <tmp>/draft.json` | exit 0；**17 实体 / 4 关系 / 5 组**（候选草稿，含重复需人工复核）；全部带 `_draft`+`source`+行号；`spec_lint` 对草稿判 INVALID（缺图例）——证明"草稿必须复核后才可绘图"的门有效 |
| `python "$SKILL_DIR/scripts/textfont.py" --probe` | exit 0；本机 164 个字体族，resolved family=Microsoft YaHei, cjk_ok=True |
| `python "$SKILL_DIR/scripts/textfont.py" --list` | exit 0；逐候选族打印 `[x]/[ ]` 与最终解析结果 |
| `--help`（main / spec_lint / extract / pdftext / textfont / validate_result / run_examples） | 逐个 **exit 0**；此前 `spec_lint.py --help` 在 Windows GBK 控制台会因帮助文本中的箭头字符触发 `UnicodeEncodeError`，现 8 个 CLI 入口在导入区统一加 `sys.stdout/stderr.reconfigure(errors="replace")` 兜底（try/except 包裹，不改任何逻辑与接口），窄编码控制台不再崩溃 |

> 复核：以上全部为本机真实运行输出，命令列于此即可复跑（示例产物写在
> 包外临时目录）。示例输入与产物均标注"示例，非正式案例"，不得作为正式
> 案例答案或预置答案提交。**未实测**：TIFF/EPS 导出（`--exports tiff,eps`）
> 与真实期刊 PDF 字体嵌入审计，本机未逐项验证，故不声称。
