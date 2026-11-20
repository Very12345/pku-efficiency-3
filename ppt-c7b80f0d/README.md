# paper-to-academic-ppt — 论文转学术 PPT（efficiency-3 / ppt-c7b80f0d）

把论文/研究材料转换成**主线清晰、证据可追溯、可编辑**的学术汇报演示的 Skill 包。
平台加载本 Skill 后在 3 个固定案例上真实运行；本包不含任何预制答案。

## 快速开始

```bash
# 1) 最小示例（示例材料在 examples/ 下）
python scripts/main.py --case examples/case.json --spec examples/deck-spec.json \
  --out <output_dir>

# 2) 平台案例形态（正式运行）
python scripts/main.py --case /input/case.json --task /input/task.md \
  --spec /app/work/deck-spec.json --out /app/output

# 3) 独立校验
python scripts/validate.py --result <output_dir>/result.json --out-dir <output_dir> \
  [--case examples/case.json]
```

产出（均在 `--out` 目录）：
`academic_deck.pptx`（可编辑源）、`preview-approx-*.png`（PIL 近似预览，如实标注）、
`evidence_mapping.md`（页级证据映射）、`result.json`（契约完整 + case_id）、
可选 `chart-*.png/.svg`（从论文表格数字重建的图）。

## 用法与调用方式

完整流程见 `SKILL.md` §4（S0–S6）：读题 → 抽取实际文件 → 抽主线/证据 →
写 `deck-spec.json`（页级大纲 schema 见 `references/TEMPLATE_GUIDE.md`）→
`main.py` 构建模板适配的 .pptx 与预览 → `validate.py` 自检。
主要参数：

| 参数 | 必填 | 说明 |
|-|-|-|
| `--case` | 是 | case.json 路径（目录时取其内 case.json） |
| `--task` | 否 | task.md（存在时读取，advisory） |
| `--spec` | 否* | Agent 写好的页级 deck-spec.json；缺省仅 `--demo` 允许自动骨架 |
| `--materials` | 否 | 覆盖材料目录/文件（优先级高于 case 内声明） |
| `--out` | 是 | 输出目录（最终产物落位） |
| `--demo` | 否 | 允许自动骨架 spec（仅演示用） |

## 依赖

- 必需：Python ≥3.8，`python-pptx`，`Pillow`；
- 可选（逐级回退并如实记录）：
  - PDF 解析：`PyMuPDF(fitz)` ≻ `pypdf` ≻ `pdfplumber`（无 → 用 DSH 读取转 .txt 输入）；
  - 重建图：`matplotlib`（缺失 → 跳过图并记录）；
  - 预览：Windows 字体 msyh/simhei… ≻ Linux DejaVu/Noto ≻ PIL 默认字体。
- 本机实测环境：Windows / Python 3.13.9（Anaconda）/ python-pptx 1.0.2 /
  Pillow 12.3 / matplotlib 3.10.6 / PyMuPDF 1.28 / pypdf 6.14 / pdfplumber 0.11.7，
  **无 LibreOffice**（预览一律 PIL 近似）。

## 关键方法

1. **主线五段式**：问题→方法→证据→结论→局限形成页序，杜绝段落切片；
2. **页级主张 + 证据强制**：deck-spec 每页 `claim` + `evidence`（或显式
   `evidence_gap`），图/表编号与论文对齐，数值不改写；
3. **模板占位符约束**：组织方模板只填占位符、不动 master、布局名匹配→索引回退→
   内置 16:9 学术版式；模板页脚配色不被覆盖；
4. **备注分离生成**：notes_slide 存过渡/强调/被问补充，不复制页面文字；
5. **诚实渲染**：无 Office 渲染引擎时预览为 PIL 近似（文件带 approx 标记，
   run_meta.rendered_with 记录）；缺失图=显式占位；PDF 抽取工具如实记录。

## 限制

- 预览为近似渲染，非 PowerPoint/LibreOffice 实际渲染；
- PDF 图片抽取依赖库与版式，个别图以占位框呈现；
- 模板适配为"占位符级"，不重排 SmartArt 等复杂版式；
- 结果正确性上限 = 论文原文；本 Skill 不负责验证论文结论。

## 失败处理

异常分类与处置见 `SKILL.md` §5 异常表（材料缺失/PDF 加密/扫描件/图抽不出/
模板不可用/占位符不足/字体缺失/页数超限/重建图失败/spec 缺失）。
一切降级都会写入 result.json 的 `uncertainty` 与 `change_records`。

## 自测与维护

- `TEST.md`：本地实测记录（命令、产物、结果）；
- `references/RUBRIC_MAP.md`：评分五维→本包覆盖对照（自查用）；
- `references/OUTPUT_CONTRACT.md`：result.json 契约；
- 版本号在 `scripts/main.py` VERSION；修改历史见 git 与 change_records。