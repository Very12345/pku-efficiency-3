# TEST.md — 本机实测记录（challenge-98e5a474 v2）

> 实测环境：Windows 10 / Python
> `D:\Code\anaconda\python.exe`（3.13），matplotlib/Pillow/numpy/
> reportlab/pypdf(PyMuPDF=fitz 可用)；**无 cairosvg/svgwrite**（与
> 平台运行时一致，预览走 matplotlib 镜像）。
> 全部命令在包根目录执行，脚本自定位不依赖 cwd。

## T0 语法编译（验收：每题 `python -m py_compile scripts/*.py` 全过）

```bash
python -m py_compile scripts/*.py      # 15 个脚本全部通过，退出码 0
```

## T1 自测（35 项 PASS，含 v2 新模块）

```bash
python scripts/selftest.py
# selftest: all checks passed（35 项 PASS；退出码 0）
```

覆盖：kind 词表映射/未知 kind 标记、布局（裁剪/分层）、SVG 分层+内嵌
清单可编辑性、chart 三导出+映射一致、图例双向、编辑动作、**spec_lint
CP1（好清单 valid / 坏清单捕获 unknown+legend+containment）**、
**textfont 探针（本机解析到 Microsoft YaHei, cjk_ok=True，确定性）**、
**extract 草稿（从 figure03-note.md 抽取到 TNF-α…IL6 六实体+关系）**、
**pdftext（合成 PDF 构造样本，fitz backend 不崩；stdlib 回退路径可
抽取 Tj 文本）**、**validate_result G 门（缺产物/假成功被拒）**、
checklist CP1–CP5 齐备。

## T2 冒烟（主脚本真实出图，exit 0，产物真实落盘）

| 命令 | 结果 |
|-|-|
| `python scripts/main.py --case examples/case.json --out D:/BuildTemp/smoke-challenge-98e5a474-v2` | **exit 0**；SPEC_LINT(CP1) VALID（0 fails/0 warns）→ CHECK SUMMARY success（0 fails/0 warns）→ `figure.svg`(15.2KB) + `figure.pdf`(37.9KB) + `figure.png`(124KB) + `result.json` |
| `python scripts/main.py --case examples/case_chart.json --out .../chart` | **exit 0**；figure.svg(9.7KB)/figure.pdf(18.8KB)/figure.png(106KB) |
| `python scripts/main.py --case examples/case_edit.json --edit-svg examples/output/figure.svg --out .../edit` | **exit 0**；change_records = [rename, relabel, note]；未改动元素保持；status=success |

schematic 冒烟检查明细（result.json verification.checks）：
svg.editable_text ok(19 `<text>`,0 path化) · svg.layers ok(6 层) ·
svg.manifest_embedded ok · svg.data_entity_attrs ok(6/6) ·
svg.data_relation_attrs ok(5/5) · svg.data_source_attrs ok(5/5) ·
bitmap.dpi_print ok(18cm 有效 ~635 DPI ≥300) · bitmap.colourspace ok(RGBA) ·
pdf.header/pages/fonts_embedded ok · legend.missing_kinds ok ·
font.cjk ok(Microsoft YaHei, CJK True) · traceability 100% →
**CHECK SUMMARY: success (0 fails, 0 warns, 0 acks)**。

## T3 契约门（G1–G8）

```bash
python scripts/validate_result.py --case examples/case.json \
    --result examples/output/result.json
# VALID ... satisfies OUTPUT_CONTRACT (G1-G8 gates pass, contract echoed)；退出码 0
```
三类产物（schematic/chart/edit）result.json 均 VALID；output_contract
回显（case.json 带 4 键 → 顶层 case_id/status/figure_type/
entities_relations/deliverables 全部非 null）。

## T4 确定性（CP5，同目录双跑逐字节一致）

```bash
# 同一输出目录、--fixed-time 固定 generated_at，跑两遍：
sha1sum figure.svg result.json   # 两遍完全一致
```
实测：
- figure.svg sha `dc210745a68f7c556d0ebd484cb3f79ac3f706f1` **两跑相同**；
- result.json sha `be75e847ffefb91dec01d31520090abae4778f66` **两跑相同**
  （用 --fixed-time 时）；
- 探针 `result.json.determinism.spec_sha16 = 2394674982ab3a42`；
- 不用 --fixed-time 时差异**仅限 `generated_at`**；输出目录不同时
  artifacts[].abspath 必然不同（含绝对路径），属如实差异。

## T5 新职责脚本实测

| 命令 | 结果 |
|-|-|
| `python scripts/extract.py --inputs examples/sources/figure03-note.md --out examples/output/work/draft-entities.json` | exit 0；**17 实体 / 4 关系 / 5 组**（候选草稿，含重复需复核）；全部带 `_draft`+`source`+`_line`；`spec_lint` 对它判 INVALID（缺图例）——证明"草稿必须复核后才可绘图"的门有效 |
| `python scripts/textfont.py --probe` | exit 0；resolved family=Microsoft YaHei, cjk_ok=True（164 个字体族） |
| `python scripts/pdftext.py --pdf D:/BuildTemp/pdftext-demo.pdf --out /tmp/pdftext-out` | exit 0；backend=fitz，1 页 61 字符，文本正确（"TNF-alpha binds TNFR1."）；stdlib 回退路径经合成 PDF 单独验证可抽取 Tj 文本 |

## T6 失败分支实测（异常处理，如实记录）

| 场景 | 结果 |
|-|-|
| 无 manifest 且无 entities/relations | `fetch_manifest` 抛错 → 写出 `status=failed` 的 result.json（pipeline fail 明细），退出码 1 |
| 渲染异常 | 捕获 → failed result.json，工作不丢失 |
| case.json 缺失 | 退出码 2，明确 FATAL 日志 |
| spec_lint 坏清单（未知 kind/缺图例/containment 无分组） | lint `{"valid": false, "fail_count": N}`，退出码 1；经 main.py 集成时 status 降为 partial |
| PDF 加密 | 抛出明确"encrypted"错误，不伪造文本 |
| edit 目标无内嵌清单 | 拒绝源文件级编辑并说明 |

> 复核：以上全部为本机真实运行输出，命令列于此即可复跑；示例产物
> 全部标注"示例，非正式案例"。