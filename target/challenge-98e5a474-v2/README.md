# challenge-98e5a474 v2 — 科研示意图生成与编辑 Skill

> 玻尔产品周赛 · 北大专区 · 学术效率 · 第三期（efficiency-3）· 组: figures
> 题目: 科学示意图生成与编辑（challenge-98e5a474）
> 本包为 **v2 加强包**（基于 `build/challenge-98e5a474` 基础包 + 高分意图对齐）。

## 这是什么

一个可被 Agent 调用的 Skill：把科研案例的**来源材料**（论文摘录、
表格、PDF）变成**可编辑图稿（分层 SVG）＋合规导出件（PNG/PDF）＋
可核验记录（result.json）**，并支持对已有图稿做**源文件级编辑**。

三句话主张：
1. **图画对** — 实体、关系、方向、数值、单位全部可回溯到来源材料
   （CP1 lint + `data-*` 溯源属性 + G8 表外类别硬门）；
2. **图可改** — 文字是 `<text>`、图层是 `layer-*` 分组、SVG 内嵌 ER
   清单，编辑请求只改被指明的元素，未改动元素保持原样；
3. **图能投** — 导出预检（DPI/字体/色彩/PDF 结构）自动执行并记录。

## 目录结构

```
SKILL.md               # 技能本体（用途/输入输出/执行步骤/异常/自查 + D1–D12 + CP1–CP5）
scripts/               # 14 个可运行脚本（见 SKILL.md §6 资源表）
references/            # OUTPUT_CONTRACT(RUBRIC_MAP(ER_MANIFEST(DRAWING_GRAMMAR(FAILURE_MODES
assets/                # relation-dict.json（连接规则字典）+ checklist.json（CP 自查清单）
examples/              # 最小示例（schematic/chart/edit + 真实产物，标注"示例，非正式案例"）
TEST.md                # 本机实测记录（py_compile/smoke/校验/确定性）
COMPARE.md             # 三方对照：build 基础 vs 高分结构 vs v2
GITHUB_URL.txt         # GitHub 公开链接（发布代理覆写）
```

## 快速开始

```bash
# ① 自测（26+ 项，全部 PASS 为正常）
python scripts/selftest.py

# ② 三类示例真实跑通
python scripts/main.py --case examples/case.json --out /tmp/sse-out
python scripts/main.py --case examples/case_chart.json --out /tmp/sse-out-ch
python scripts/main.py --case examples/case_edit.json \
    --edit-svg examples/output/figure.svg --out /tmp/sse-out-edit

# ③ 契约校验（G1–G8）
python scripts/validate_result.py --case examples/case.json \
    --result /tmp/sse-out/result.json
```

正式运行（平台）：`/input/case.json` + `/input/task.md` → 读材料 →
`extract.py` 抽取候选草稿 → 写 `/app/work/entities.json` → main.py →
`/app/output/{figure.svg,figure.png,figure.pdf,result.json}`。

## 依赖

- Python 3.9+（本机已验：matplotlib / Pillow / numpy / reportlab）；
- PDF 抽取按 fitz → pypdf → PyPDF2 → **stdlib 回退** 逐级降级，无任何
  第三方库也能跑（抽取质量如实记录）；
- 无 cairosvg/svgwrite 依赖 — PNG/PDF 预览是同一 layout+manifest 的
  matplotlib 镜像（语义一致、非逐像素，已在 SKILL.md/result.json 标注）。

## 本题要点对齐

- 评分五维 → 设计覆盖：见 `references/RUBRIC_MAP.md`（交付前逐条自评）；
- 12 类失败形态 → 检测 → 处置：见 `references/FAILURE_MODES.md`；
- 关系语义 → 箭头/线型/颜色：见 `references/DRAWING_GRAMMAR.md` 与
  `assets/relation-dict.json`；
- result.json 契约 + 硬门：见 `references/OUTPUT_CONTRACT.md`。

## 限制（诚实标注）

- 预览为 matplotlib 镜像，非逐像素；PDF 字体嵌入审计为尽力而为；
- CJK 渲染依系统字体（`textfont.py` 探测）；无字体时 SVG 文字仍在，
  PNG 可能缺字并写入 uncertainty；
- `extract.py` 产出的是**候选草稿**（`_draft` 标注），最终清单必须
  人工复核方向与关系，避免把抽取草稿当正式答案。

> 发布说明：`GITHUB_URL.txt` 第一行为
> `https://github.com/Very12345/pku-efficiency-3/tree/main/target/challenge-98e5a474-v2`，
> 发布代理按实际推送覆写或确认。