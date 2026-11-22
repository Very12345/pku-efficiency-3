# paper-to-academic-ppt — 论文转学术 PPT（efficiency-3 / ppt-c7b80f0d）

把论文/研究材料转换成**主线清晰、证据可追溯、可编辑**的学术汇报演示的 Skill 包。
平台加载本 Skill 后在 3 个固定案例上真实运行；**本包不含任何预制答案**。

设计主线（与本题五维评分逐条对应，见 `references/RUBRIC_MAP.md`）：

```
契约先行 → 方案先行 → 生成 → 双形态校验 → 逐条自评
OUTPUT_CONTRACT.md   deck-spec.json + spec_lint   main.py   export_check + check_contract   RUBRIC_MAP.md
```

## 快速开始（任意 cwd 均可，`$SKILL_DIR` = SKILL.md 所在目录）

```bash
SKILL_DIR="<本包根目录>"        # 平台安装到 /skills/weekly-skill 时即该路径

# 1) 蓝图 lint（CP1：写 deck-spec 后必跑）
python "$SKILL_DIR/scripts/spec_lint.py" --spec /app/work/deck-spec.json

# 2) 端到端生成（正式案例形态）
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md \
  --spec /app/work/deck-spec.json --out /app/output

# 3) 两道交付门
python "$SKILL_DIR/scripts/export_check.py"  --result /app/output/result.json \
  --out-dir /app/output --case /input/case.json
python "$SKILL_DIR/scripts/check_contract.py" --result /app/output/result.json \
  --contract "$SKILL_DIR/references/OUTPUT_CONTRACT.md" --case /input/case.json
```

产出（均在 `--out` 目录）：`academic_deck.pptx`（可编辑源，对象分层命名）、
`preview-approx-*.png`（PIL 近似预览，如实标注）、`evidence_mapping.md` +
`evidence_map.json`（逐页证据映射，双形态同源）、`result.json`（契约完整 + case_id）、
可选 `chart-*.png/.svg`（从论文表格数字重建的图）。

## 最小示例（合成案例，非正式案例）

```bash
python "$SKILL_DIR/scripts/make_template.py" --out "$SKILL_DIR/examples"   # ① 生成示例模板（二进制，运行期现产）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
  --spec "$SKILL_DIR/examples/deck-spec.json" --out "<空输出目录>"          # ② 跑示例
```

① 可跳过：模板不存在时生成器自动回退内置 16:9 学术版式
（`deck.template.kind="builtin"`），这是正常且被记录的分支，不是失败。
示例输入/预期产物/净化说明见 `examples/README.md`、`examples/EXPECTED-OUTPUT.md`。

## 用法与调用方式

完整流程见 `SKILL.md` §4（S0–S6，含 CP1/CP3 检查点与 D1–D11 决策规则）：
读题 → 抽实际材料 → **蓝图规划**（`references/slide-blueprint.md` §1）→ 写
`deck-spec.json`（schema 见 slide-blueprint §3）→ **CP1 lint** → `main.py` 构建
模板适配的 .pptx 与预览 → **CP3 export_check + check_contract** →
按 `references/RUBRIC_MAP.md` 自评。主要参数：

| 参数 | 必填 | 说明 |
|-|-|-|
| `--case` | 是 | case.json 路径（目录时取其内 case.json） |
| `--task` | 否 | task.md（存在时读取，advisory） |
| `--spec` | 否* | Agent 写好的页级 deck-spec.json；缺省仅 `--demo` 允许自动骨架 |
| `--materials` | 否 | 覆盖材料目录/文件（优先级高于 case 内声明） |
| `--out` | 是 | 输出目录（最终产物落位） |
| `--demo` | 否 | 允许自动骨架 spec（仅演示用，状态如实降为 partial） |

## 依赖

- 必需：Python ≥3.8，`python-pptx`（构建 .pptx），`Pillow`（预览渲染）；
- 可选（逐级回退并如实记录，见 `references/failure-modes.md` §2.3）：
  - PDF 解析：`PyMuPDF(fitz)` ≻ `pypdf` ≻ `pdfplumber`（全无 → 用自带 PDF 读取转 `.txt` 传入）；
  - 重建图：`matplotlib`（缺失 → 跳过图并记录）；
  - 预览字体：运行时探测 `C:/Windows/Fonts` ≻ `/System/Library/Fonts` ≻ `/usr/share/fonts`
    ≻ PIL 默认（可用环境变量 `SKILL_PREVIEW_FONT` 覆盖）。
- 参考运行环境（`TEST.md` 记录）：Windows / Python 3.13.9 / python-pptx 1.0.2 /
  Pillow 12.3 / matplotlib 3.10.6 / PyMuPDF 1.28，**无 LibreOffice**（预览一律 PIL 近似）。

## 关键方法与机制

1. **契约先行**：`references/OUTPUT_CONTRACT.md` 列出 result.json 的 19 个顶层字段，
   `scripts/check_contract.py` 直接读该文档逐字段核对 → 文档与代码不会悄悄漂移
   （`main.py` 内置同一道自检，缺失即非零退出）。
2. **方案先行**：先把论文重写成页级 `deck-spec.json`（一页一主张 + 证据定位），
   `scripts/spec_lint.py` 做 CP1 结构性 lint（BL-1…BL-4）后才允许生成。
3. **蓝图映射**：论文结构 → 页面骨架（问题→方法→证据→结论→局限），
   杜绝"把段落切成行"（`references/slide-blueprint.md` §1）。
4. **双形态证据映射**：`evidence_mapping.md`（人复核）+ `evidence_map.json`（机器读）
   同一 spec 生成，导出检查器校验行数 = 声明 entries。
5. **三层脚本**：assetkit（素材：PDF 抽取 / 重建图）→ deckgen（页面生成）→
   ooxml_kit（OOXML 精修：主题字体、分层命名、容器健全检查）。
6. **模板占位符约束**：只填占位符、不动 master、不覆盖页脚/配色；布局名匹配 → 索引回退
   → 内置版式；`template_mode="replace"` 时移除起始页并记录 `starter_slides_removed`。
7. **备注分离**：`notes_slide` 存过渡/强调/被问补充（含封面与收尾页），不复制页面文字。
8. **诚实渲染与运行时资源**：无 Office 引擎时预览为 PIL 近似（文件名 + `kind` +
   `rendered_with` 三处标注）；模板、预览、重建图等二进制**一律运行时生成**，
   技能资源只含 UTF-8 文本文件。

## 目录结构

```
SKILL.md                     执行流程（S0–S6）、决策规则（D1–D11）、自查清单
README.md                    本文件：依赖/安装/用法/限制/维护
TEST.md                      本机真实实测记录（命令 + 退出码 + 结果）
GITHUB_URL.txt               公开作品链接（单行）
references/OUTPUT_CONTRACT.md  result.json 顶层字段清单 + 四形态 + G1–G8
references/RUBRIC_MAP.md      五维评分 → 本包落点 + 对照协议
references/failure-modes.md   失败模式 / 降级策略 / 退出码语义
references/slide-blueprint.md 蓝图映射 + deck-spec schema + 证据表格式
references/layer-naming.md    PPTX 分层命名规范
scripts/main.py               端到端入口（--case/--spec/--out，其余可选）
scripts/assetkit.py / deckgen.py / ooxml_kit.py   素材 / 生成 / OOXML 三层
scripts/spec_lint.py          CP1 结构性 lint
scripts/export_check.py       CP3 导出检查（G1–G8）
scripts/check_contract.py     契约字段覆盖核对
scripts/preview.py            PIL 近似预览
scripts/make_template.py      运行期生成回退模板（不随包携带二进制）
scripts/make_synthetic_inputs.py  运行期生成合成夹具（占位图 + 两页 PDF）
scripts/cli_io.py             控制台加固（非 UTF-8 环境下打印中文不崩）
examples/                     最小示例（合成案例）：case/spec/task/材料/预期产物
```

## 限制

- 预览为**近似**渲染，非 PowerPoint/LibreOffice 实际渲染结果；
- PDF 图片抽取依赖库与版式，个别图会以显式占位框呈现（占位框**不代表**论文原图）；
- 模板适配为"占位符级"，不重排 SmartArt 等复杂版式；
- 结果正确性上限 = 论文原文；本 Skill 不负责验证论文结论；
- 首次运行前需具备 `python-pptx` 才能产出 `.pptx`；缺失时如实降级而非伪造文件。

## 失败处理

异常分类与处置见 `references/failure-modes.md`（材料异常 / 模板缺失 / 依赖缺失 /
契约四形态 / 状态一致性，逐类给出识别→处置→记录位置→退出码），
与 `SKILL.md` §5 的 D1–D11 决策规则一一对应。一切降级都会写入 result.json 的
`uncertainty` 与 `change_records`。

## 自测与维护

- `TEST.md`：本机实测记录（编译/端到端/确定性/失败路径/PDF 链路 + 退出码）；
- `examples/EXPECTED-OUTPUT.md`：示例案例的预期产物与契约字段清单（文字形态）；
- 版本号在 `scripts/main.py` 的 `VERSION`（当前 `2.1.0`）；
- 新增能力：素材能力进 `assetkit.py`，生成逻辑进 `deckgen.py`，OOXML 细节进
  `ooxml_kit.py`（新对象种类先在 `PREFIX_BY_KIND` 注册命名前缀）；
- 新增失败分支必须同时更新 `references/failure-modes.md`；修改记录见 git 与
  result.json 的 `change_records`。
