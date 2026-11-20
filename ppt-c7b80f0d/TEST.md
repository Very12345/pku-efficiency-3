# TEST.md — 本地实测记录（运行者：制作子代理 agent-48，2026-11-20 22:30 +08）

> 本文件记录本包在本机的真实执行结果，供复核。机器：Windows / Anaconda
> Python 3.13.9（命令 `python`）；python-pptx 1.0.2、Pillow 12.3.0、
> matplotlib 3.10.6、PyMuPDF(fitz) 1.28.0、pypdf 6.14.2、pdfplumber 0.11.7。
> 无 LibreOffice —— 预览一律 PIL 近似渲染并如实标注。

## T1 编译与导入检查 —— 通过

```bash
python -m py_compile scripts/*.py && echo COMPILE OK
# COMPILE OK
python -c "import sys; sys.path.insert(0,'scripts'); import deck_builder, preview, pdf_extract, main, validate; print('imports OK')"
# imports OK
```

## T2 冒烟：示例案例端到端 —— 通过（exit 0，validate valid:true）

```bash
python scripts/main.py --case examples/case.json --spec examples/deck-spec.json \
  --out D:/BuildTemp/smoke-ppt-c7b80f0d
python scripts/validate.py --result D:/BuildTemp/smoke-ppt-c7b80f0d/result.json \
  --out-dir D:/BuildTemp/smoke-ppt-c7b80f0d --case examples/case.json
```

输出摘要（截取自运行日志）：

```
case_id      : example-ppt-c7b80f0d
status       : completed
deck         : academic_deck.pptx (8 slides)
previews     : 7 files
evidence_map : evidence_mapping.md (entries=6, gaps=0)
sources      : 1  uncertainty: 0  changes: 2
self_check   : OK
```

`validate.py` 输出：`{"valid": true, "errors": [], "warnings": [], ...}`，exit 0。

**实际产出文件（12 个）**：

```text
academic_deck.pptx       57,148 B   可编辑源，8 页；模板适配成功
chart-Fig_1.png          10,900 B   重建图（Table 1 数据，已嵌入 deck）
chart-Fig_1.svg          20,363 B   重建图 SVG 可编辑源
evidence_mapping.md       1,211 B   页级证据映射（6 页全 mapped，0 gap）
preview-approx-cover.png 24,162 B
preview-approx-001..006  24–61 KB   每页 PIL 近似预览
result.json               5,203 B   契约字段全部回显 + case_id
```

复核要点（python-pptx 重开验证）：
- 页数 8 ≤ 上限 8（`page_budget_met: true`）；版式使用
  `{"Title Slide":1, "Title and Content":5, "Figure Slide":1, "Reference Slide":1}`
  证明 layout 名匹配生效；模板 `guard=placeholder-fill-only; master/footer/colors untouched`；
- 内容页备注全部写入 notes_slide，结构为
  `核心主张 / 讲解备注 / 对本页追问时可用证据`（与页面文字分离，notes_separated=true）；
- Table 1 以 5×5 表格嵌入，表头 `System | ROUGE-L F1 | BLEU-4 | Specificity | Latency` 与论文一致；
- 重建图注释 `reconstructed_from_table`，数值来自 spec（spec 由原文 Table 1 导出）；
- result.json 的 output_contract 字段（title/main_claim/slides/notes_separated/render_state）
  全部回显为真实值，无 null。

## T3 PDF 解析链路 —— 通过

用 reportlab 现场生成 2 页 PDF，再跑抽取器：

```bash
python scripts/pdf_extract.py --pdf D:/BuildTemp/pdf-mini.pdf --out D:/BuildTemp/pdf-extract-out
# {"status":"ok","tool":"pymupdf","pages_parsed":2,"text_chars":191,"images_extracted":0}
```

输出含页标记文本 `[PAGE 1] ... [PAGE 2]`，抽取工具与页数如实记入 sources。

## T4 DEMO 骨架路径（无 spec）—— 通过（如实 partial）

```bash
python scripts/main.py --case D:/BuildTemp/demo-case.json --out ... --demo
# status=partial, template kind=builtin, 5 slides,
# spec_source=auto-skeleton, evidence gaps=1（显式记录），uncertainty=1
```

## T5 材料缺失的诚实失败路径 —— 通过

```bash
python scripts/main.py --case D:/BuildTemp/missing-case.json --out ...
# status=failed, material_status=unreadable, deck=None,
# uncertainty 记录原因，contract 字段按类型给 ''/{}，未编造内容
```

## T6 测试中发现并修复的问题（诚实记录）

1. `SlidePlaceholder` 无 `.clear()`（需 `.text_frame.clear()`）→ 已修（标题页分支）；
2. `_print_summary` 漏传 `out_dir` → 已修；
3. 素材/模板相对路径曾只按输出目录解析 → 现按 “spec 目录→case 目录→输出目录”
   逐级解析（`discover_materials`/`_resolve_template_path`）；
4. result.json 里 `run_meta.self_check` 曾写到未合并的 dict → 已改写到结果副本；
5. matplotlib 图内 CJK 标题在 DejaVu 下缺字形 → 图题/文件名改为 ASCII 安全
   （中文完整图注放在幻灯片图注与 evidence_mapping）。

## 限制（如实声明）

- 预览为 PIL 近似渲染，不是 PowerPoint/LibreOffice 渲染引擎结果；换机后字体
  可能替换 —— .pptx 内已同时写 latin 与 east-asian typeface 缓解；
- 本机无 LibreOffice，未能在本机生成真 PDF（SKILL 支持有 LibreOffice 时
  用 soffice 转换并改写 rendered_with）；
- 素材为合成示例，仅验证管道正确性，与正式案例无关。