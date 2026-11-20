# TEST.md — 本地实测记录（v2；运行者：制作子代理 agent-54，2026-11-20 22:5x +08）

> 本文件记录 v2 包在本机的真实执行结果，供复核。机器：Windows / Anaconda
> Python 3.13.9（命令 `python`）；python-pptx 1.0.2、Pillow 12.3.0、
> matplotlib 3.10.6、PyMuPDF(fitz) 1.28.0、pypdf 6.14.2。
> 无 LibreOffice —— 预览一律 PIL 近似渲染并如实标注。

## T1 编译与导入检查 —— 通过

```bash
python -m py_compile scripts/*.py        # COMPILE OK
python -c "import sys; sys.path.insert(0,'scripts'); import assetkit, deckgen, ooxml_kit, preview, spec_lint, export_check, main; print('imports OK')"
# imports OK
```

## T2 冒烟：示例案例端到端 —— 通过（exit 0，export_check valid:true 无 warning）

```bash
python scripts/main.py --case examples/case.json --spec examples/deck-spec.json \
  --out D:/BuildTemp/t2-ppt
python scripts/export_check.py --result D:/BuildTemp/t2-ppt/result.json \
  --out-dir D:/BuildTemp/t2-ppt --case examples/case.json
```

输出摘要（截取自运行日志）：

```
case_id      : example-ppt-c7b80f0d
status       : completed
deck         : academic_deck.pptx (8 slides)
previews     : 7 files
evidence_map : evidence_mapping.md (entries=6, gaps=0)
spec_lint    : OK
self_check   : OK
```

`export_check.py`：`{"valid": true, "errors": [], "warnings": []}`，exit 0。

**实际产出文件（13 个）**：`academic_deck.pptx`、`chart-Fig_1.png/.svg`、
`evidence_mapping.md`、`evidence_map.json`、`preview-approx-cover.png` +
`preview-approx-001..006.png`、`result.json`。

复核要点（v2 新增项）：
- 模板适配：`template.kind=file`、`starter_slides_removed=1`（template_mode=replace）、
  layouts 按名匹配 `{"Title Slide":1, "Title and Content":5, "Figure Slide":1,
  "Reference Slide":1}`；
- **CP1 lint**：spec_lint valid=true（6 页全 claim/evidence，0 gap）；
- **OOXML 层**（`ooxml_kit.py` 独立复核）：zip_sanity ok（3 必需部件 + XML 良构）、
  命名审计 unnamed=0（全部对象带 layer-naming 前缀）、8/8 页均有 notes（含封面/收尾）；
- **双形态证据映射**：`evidence_map.json` 与 `evidence_mapping.md` 同源
  （rows=6，gap 行 0）；
- result.json 的 output_contract 字段（title/main_claim/slides/notes_separated/
  render_state）全部回显为真实值，无 null；`run_meta.checkpoints`
  `{cp1_spec_lint:true, cp2_build:true, cp3_export_check:true}`。

## T3 确定性：同输入两次运行 —— 内容级一致（zip 外壳时间戳除外）

```bash
python scripts/main.py --case examples/case.json --spec examples/deck-spec.json --out A
python scripts/main.py --case examples/case.json --spec examples/deck-spec.json --out B
```

- 两个 deck 的内部 XML/媒体部件**逐部件 sha256 一致**（diff parts = []）；
- 将 zip 条目时间戳归一到 1980-01-01 后重哈希：A/B 均为 `d255bea1e9d98338`（一致）——
  **内容确定**；原始 zip 字节因条目写入时间戳不同而不逐字节一致（非内容变化）。

## T4 PDF 抽取链路 —— 通过（assetkit.py）

用 PyMuPDF 现场生成 2 页 PDF，再跑素材层抽取器：

```bash
python scripts/assetkit.py --pdf D:/BuildTemp/pdf-v2-mini.pdf --out D:/BuildTemp/pdf-extract-v2
# {"status":"ok","tool":"pymupdf","pages_parsed":2,"text_chars":103,"images_extracted":0}
```

输出含页标记文本 `[PAGE 1] ... [PAGE 2]`，抽取工具与页数如实记入 sources。

## T5 DEMO 骨架路径（无 spec）—— 通过（如实 partial）

```bash
python scripts/main.py --case demo-case.json --out ... --demo
# status=partial, template kind=builtin, 5 slides,
# spec_source=auto-skeleton, CP1 lint 问题按 D4 记录进 uncertainty
```

## T6 材料缺失的诚实失败路径 —— 通过

```bash
python scripts/main.py --case missing-case.json --out ...
# status=failed, material_status=unreadable, deck=None,
# contract 字段按类型给 ''/{}，未编造内容
```

## T7 v2 调试中修复的问题（诚实记录）

1. `spec_lint.py` 初版 bullet 超长判断代码冗余（误留 walrus 表达式）→ 清理为单一
   CJK 加权判断；
2. `deckgen.py` 封面/收尾页原无 notes → 补写讲解备注，export_check warnings 清零；
3. GA 系 spec 的 `data_encoding` 编码键为 `channel` 而非 `kind` → spec_lint 兼容两者；
   color_scale 图例按 range 标记（渐变条）→ lint 特判 symbol="gradient"；
4. GA `audit` 初版 src 检查对布局元素误报 47 个 → 收窄为 entity:/relation:/datum:/icon
   科学元素（0 误报）。

## 限制（如实声明）

- 预览为 PIL 近似渲染，不是 PowerPoint/LibreOffice 渲染引擎结果；换机后字体可能
  替换 —— .pptx 内已写主题字体 + 双 typeface 缓解；
- 本机无 LibreOffice，未能在本机生成真 PDF（SKILL 支持有 LibreOffice 时用 soffice
  转换并改写 rendered_with）；
- 素材为合成示例，仅验证管道正确性，与正式案例无关。