# paper-to-academic-ppt v2 — 论文转学术 PPT（efficiency-3 / ppt-c7b80f0d）

把论文/研究材料转换成**主线清晰、证据可追溯、可编辑**的学术汇报演示的 Skill 包
（v2 加强包）。平台加载本 Skill 后在 3 个固定案例上真实运行；本包不含任何预制答案。

v2 相对 build 基包的增强方向：**对齐高分意图结构（references 三件套 + 脚本三层）**，
具体见 `COMPARE.md`（build 基础 vs 高分结构 vs v2 三方对照）。

## 快速开始

```bash
# 1) 蓝图 lint（CP1，写 deck-spec 后必跑）
python scripts/spec_lint.py --spec examples/deck-spec.json

# 2) 最小示例（示例材料在 examples/ 下）
python scripts/main.py --case examples/case.json --spec examples/deck-spec.json \
  --out <output_dir>

# 3) 平台案例形态（正式运行）
python scripts/main.py --case /input/case.json --task /input/task.md \
  --spec /app/work/deck-spec.json --out /app/output

# 4) 导出检查（CP3 交付门：契约回显 + OOXML 容器 + 命名 + 证据表一致性）
python scripts/export_check.py --result <output_dir>/result.json --out-dir <output_dir> \
  [--case examples/case.json]
```

产出（均在 `--out` 目录）：
`academic_deck.pptx`（可编辑源，对象分层命名）、`preview-approx-*.png`（PIL 近似预览，
如实标注）、`evidence_mapping.md` + `evidence_map.json`（逐页证据映射，双形态同源）、
`result.json`（契约完整 + case_id）、可选 `chart-*.png/.svg`（从论文表格数字重建的图）。

## 用法与调用方式

完整流程见 `SKILL.md` §4（S0–S6，含 CP1/CP3 检查点与 D1–D10 决策规则）：
读题 → 抽实际材料 → **蓝图规划**（`references/slide-blueprint.md` §1）→ 写
`deck-spec.json`（schema 见 slide-blueprint §3）→ **CP1 lint** → `main.py` 构建
模板适配的 .pptx 与预览 → **CP3 export_check** → 按 `references/rubric-map.md` 自评。
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
  Pillow 12.3 / matplotlib 3.10.6 / PyMuPDF 1.28 / pypdf 6.14，**无 LibreOffice**
  （预览一律 PIL 近似）；实测记录见 `TEST.md`。

## 关键方法与 v2 增强

1. **蓝图先行**：论文结构→页面结构映射（slide-blueprint.md §1），页序
   问题→方法→证据→结论→局限，杜绝段落切片；
2. **CP1 spec lint**：claim/evidence/BL 规则结构化为可执行校验（`spec_lint.py`）；
3. **页级主张 + 证据强制 + 双形态逐页证据映射**：每个 slide 的 claim + evidence
   （或显式 evidence_gap）；`evidence_mapping.md`（人读）+ `evidence_map.json`
   （机器读）同源生成，导出检查器校验表行数与 gap 行；
4. **三层脚本（对齐高分意图）**：assetkit（素材：PDF 抽取/重建图）→ deckgen
   （页面生成）→ ooxml_kit（OOXML 精修：主题字体、分层命名、容器健全检查）；
5. **模板占位符约束**：组织方模板只填占位符、不动 master、布局名匹配→索引回退→
   内置 16:9 学术版式；模板页脚配色不被覆盖；
6. **备注分离生成**：notes_slide 存过渡/强调/被问补充（含封面/收尾页），不复制页面文字；
7. **CP3 导出检查器**：OOXML zip/XML 健全（G5）、形状命名审计（layer-naming.md）、
   证据表一致性（G7）、契约回显（G2）等 G1–G8 硬性门；
8. **诚实渲染**：无 Office 渲染引擎时预览为 PIL 近似（文件带 approx 标记）；
   缺失图=显式占位；PDF 抽取工具如实记录。

## 限制

- 预览为近似渲染，非 PowerPoint/LibreOffice 实际渲染；
- PDF 图片抽取依赖库与版式，个别图以占位框呈现；
- 模板适配为"占位符级"，不重排 SmartArt 等复杂版式；
- 结果正确性上限 = 论文原文；本 Skill 不负责验证论文结论。

## 失败处理

异常分类与处置见 `SKILL.md` §5 决策规则 D1–D10 与 §6 异常表
（材料缺失/PDF 加密/扫描件/图抽不出/模板不可用/占位符不足/字体缺失/页数超限/
重建图失败/spec 缺失/lint 偏差）。一切降级都会写入 result.json 的
`uncertainty` 与 `change_records`。

## 自测与维护

- `TEST.md`：本地实测记录（命令、产物、结果）；
- `references/rubric-map.md`：评分五维→本包覆盖对照（自查用）；
- `references/result-contract.md`：result.json 契约 + G1–G8 硬性门；
- `references/slide-blueprint.md`：蓝图映射 + deck-spec schema + 证据表格式；
- `references/layer-naming.md`：PPTX 分层命名规范；
- 版本号在 `scripts/main.py` VERSION（v2=2.0.0）；修改历史见 git 与 change_records。