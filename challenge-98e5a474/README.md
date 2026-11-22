# challenge-98e5a474 — 科研示意图生成与编辑 Skill

> 玻尔产品周赛 · 北大专区 · 学术效率 · 第三期（efficiency-3）· 组: figures
> 题目：科研示意图生成与编辑（challenge-98e5a474）
> 本包为**合规形态包**：基于上一版 v2 包（算法与 CLI 不变）做搬家 + 补文档 +
> 清残留 —— 删掉平台不支持的文件类型、清掉本机绝对路径、补齐五维评分映射。

## 这是什么

一个可被 Agent 调用的 Skill：把科研案例的**来源材料**（论文摘录、表格、
PDF）变成**可编辑图稿（分层 SVG）＋合规导出件（PNG/PDF）＋可核验记录
（result.json）**，并支持对已有图稿做**源文件级编辑**。

三句话主张：

1. **图画对** — 实体、关系、方向、数值、单位全部可回溯到来源材料
   （CP1 lint + `data-*` 溯源属性 + G8 表外类别硬门）；
2. **图可改** — 文字是 `<text>`、图层是 `layer-*` 分组、SVG 内嵌 ER
   清单，编辑请求只改被指明的元素，未改动元素保持原样；
3. **图能投** — 导出预检（DPI/字体/色彩/PDF 结构）自动执行并记录。

## 目录结构

```
SKILL.md                 # 技能本体（用途/自定位/执行步骤 S0–S7/D1–D12/五维映射/自查/禁止）
README.md                # 本文件：依赖、适用范围、限制、维护
TEST.md                  # 本机实测记录（自测 / 三示例 exit code / 契约门 / 确定性）
GITHUB_URL.txt           # 公开仓库链接（第一行）
scripts/                 # 15 个可运行脚本（入口 main.py，自测 selftest.py，复现 run_examples.py）
references/              # OUTPUT_CONTRACT / RUBRIC_MAP / ER_MANIFEST / DRAWING_GRAMMAR / failure-modes
assets/                  # relation-dict.json（连接规则字典）+ checklist.json（CP 自查清单）
examples/                # 最小示例（schematic/chart/edit + 合成来源材料 + EXPECTED-OUTPUT.md）
```

## 快速开始（命令自定位，任意 cwd 可跑）

```bash
# 0) 指定技能根（= 本 SKILL.md 所在目录）
SKILL_DIR="$(cd "$(dirname "<本 SKILL.md 的实际路径>")" && pwd)"

# 1) 逻辑自测（全部 PASS 为正常，退出码 0）
python "$SKILL_DIR/scripts/selftest.py"

# 2) 一条命令跑通示例并校验契约（schematic → chart → edit + G1–G8）
python "$SKILL_DIR/scripts/run_examples.py" --out /tmp/sse-examples

# 3) 单跑一个示例（--case 可指文件，也可指目录）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out /tmp/sse-out
python "$SKILL_DIR/scripts/validate_result.py" \
    --case "$SKILL_DIR/examples/case.json" --result /tmp/sse-out/result.json
```

正式运行（平台）：`/input/case.json` + `/input/task.md` → 读材料 →
`extract.py` 抽取候选草稿 → 写 `/app/work/entities.json` → `main.py` →
`/app/output/{figure.svg,figure.png,figure.pdf,result.json}`。

## 依赖

- Python 3.9+（本机实测 3.13）；运行必需：**matplotlib、Pillow、numpy**，
  reportlab 可选（缺失也能出图，PDF 由 matplotlib 后端产出）；
- PDF 抽取按 fitz → pypdf → PyPDF2 → **stdlib 回退**（zlib + Tj/TJ）逐级
  降级，无任何第三方 PDF 库也能跑，backend 如实写进 result.json；
- 无 cairosvg/svgwrite 依赖 —— PNG/PDF 预览是同一 layout+manifest 的
  matplotlib 镜像（语义一致、非逐像素，已在 SKILL.md 与 uncertainty 标注）；
- 安装（可选，仅用于提升预览保真度）：`pip install matplotlib pillow numpy
  reportlab pymupdf`；字体：CJK 依赖系统字体，`scripts/textfont.py --list`
  可查本机能否渲染中文（缺失时 SVG 文字仍在，PNG 可能缺字并记入 uncertainty）。

## 适用范围

- 适用：机制/信号通路示意图、结构关系图、流程图、实验装置图、数据图
  （bar/line/scatter/heatmap）的**生成与源文件级编辑**；输入可为
  Markdown/文本/CSV/PDF 材料或已有图稿。
- 不适用：统计方法的数值计算与选择、海报封面等版式设计、艺术插画与
  图像美化、论文正文与文献综述写作（题面明确排除）。

## 资源形态（本题硬约束，已逐条满足）

- 包内**只有 UTF-8 文本文件**，扩展名限于 `.md/.py/.json/.txt/.csv/.yaml/.yml`；
- **不预置** PDF/PNG/SVG/TIFF/PPTX 等二进制或平台不支持的类型，也不放
  `__pycache__/`、`*.pyc`；所有图稿与渲染件由脚本**运行时生成**；
- 文件数 ≤50、单文件 ≤500KB、总计 ≤2MB、无符号链接；
- 包内无本机绝对路径（脚本只用 `__file__` 自定位，文档用 `$SKILL_DIR`）。

## 限制（诚实标注）

- 预览为 matplotlib 镜像，非逐像素；PDF 字体嵌入审计为尽力而为；
- CJK 渲染依系统字体（`textfont.py` 探测）；无字体时 SVG 文字仍在，
  PNG 可能缺字并写入 uncertainty；
- `extract.py` 产出的是**候选草稿**（`_draft` 标注），最终清单必须人工
  复核方向与关系，避免把抽取草稿当正式答案；
- 示例材料（`examples/sources/*`）是**合成演示**，不是真实论文数据。

## 维护

- 版本与接口：`SKILL.md` §6 资源表为唯一权威；`main.py --help` 与实际
  参数逐字一致；改动 CLI 参数名时必须同步 SKILL.md、README、TEST.md；
- 契约：`references/OUTPUT_CONTRACT.md` 是 result.json 的唯一契约
  （G1–G8 硬门），改契约要同时改 `scripts/validate_result.py`、`report.py`
  与 `examples/EXPECTED-OUTPUT.md`；
- 回归：任何改动后跑 `selftest.py`（逻辑）+ `run_examples.py`（端到端 +
  契约门）+ `validate_pkg.py`（打包形态），三者全绿才算可发布；
- 发布：`GITHUB_URL.txt` 第一行为公开仓库链接，发布前用未登录窗口确认可访问。
