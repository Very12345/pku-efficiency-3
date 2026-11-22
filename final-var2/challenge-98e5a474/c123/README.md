# challenge-98e5a474 — 科研示意图生成与编辑（机制显性版 / v3）

> 玻尔产品周赛 · 北大专区 · 学术效率 · 第三期（efficiency-3）· 组: figures
> 题目：科研示意图生成与编辑（challenge-98e5a474）
> **本变体的强化轴 = 机制与复用显性化**：新增 `references/MECHANISM.md`
> （五个具名机制 M1–M5，每个都写清"是什么 / 没有它会怎样 / 可证伪判据 / 已知盲区"）
> 与 `references/REUSABLE-ASSETS.md`（12 项可复用资产 A1–A12 + 5 级采纳阶梯 L0–L4
> + 复用时最容易踩的坑）。算法与 CLI 接口**未改动**。

## 这是什么

一个可被 Agent 调用的 Skill：把科研案例的**来源材料**变成**可编辑图稿（分层 SVG）
＋合规导出件（PNG/PDF）＋可核验记录（result.json）**，并支持对已有图稿做
**源文件级编辑**。它的设计不是"堆功能"，而是**五个可以被单独拿掉来检验的机制**：

| 机制 | 一句话 | 没有它会怎样（摘要） |
|-|-|-|
| **M1 方案先行** | 画之前先过 CP1 lint | 未知关系类型被悄悄画成箭头；错误在成品里才暴露 |
| **M2 源文件自描述** | ER 清单内嵌进 SVG | 改一个标签要重画整张图；无法做源文件级增量编辑 |
| **M3 抽取四段回退** | fitz→pypdf→PyPDF2→stdlib，backend 如实记录 | 没装 PDF 库就完全读不了；或抽不出却继续往下走 |
| **M4 导出预检** | DPI/色彩/文字可编辑/PDF/字体逐项查 | 图能用但投不出去，改要重导 |
| **M5 单一字体事实源** | render/checks/result 共用同一个探针 | 三处各猜一个字体，结论互相矛盾 |

每个机制的完整说明（含**可证伪判据**与**已知盲区**）见 `references/MECHANISM.md`。

**三条主张**：图画对（可溯源）、图可改（可选可拆可增量）、机制可被拆开检验（可证伪）。

## 目录结构

```
SKILL.md                       # 技能本体：机制索引、机制—流程映射、退出码/降级语义、自查
README.md                      # 本文件（含"复用本包"的入口）
TEST.md                        # 本机实测记录（含每个机制判据的实测读数）
GITHUB_URL.txt                 # 公开仓库链接（第一行）
scripts/                       # 15 个既有脚本 + doccheck.py（新增，只读对拍工具）
references/
  MECHANISM.md                 # **新增**：M1–M5 完整机制（是什么/没有它会怎样/可证伪判据/盲区）
  REUSABLE-ASSETS.md           # **新增**：A1–A12 资产 + L0–L4 采纳阶梯 + 复用步骤 + 三个坑
  OUTPUT_CONTRACT.md           # result.json 契约 + G1–G8 硬门（**字段块逐字保留**）
  CHECK-INDEX.md               # **新增**：全部检查名清单（机制的判据取值来源）
  EDIT-ACTION-SCHEMA.md        # **改写**：只做路由与判据，字段表以 scripts/edit.py 为准
  failure-modes.md             # 失败形态 → 检测 → 处置 → 相关机制
  RUBRIC_MAP.md                # 五维评分（40/25/15/10/10）→ 本包文件/机制
  ER_MANIFEST.md               # ER 清单规范（绘图唯一数据源）
  DRAWING_GRAMMAR.md           # 图形语法：关系语义→箭头/线型/颜色/分组/图例
assets/                        # relation-dict.json（连接规则字典）+ checklist.json（CP 清单）
examples/                      # 最小示例（schematic / chart / edit + 合成材料）
```

## 快速开始（命令自定位，任意 cwd 可跑）

```bash
# 0) 指定技能根（= 本 SKILL.md 所在目录）
SKILL_DIR="$(cd "$(dirname "<本 SKILL.md 的实际路径>")" && pwd)"

# 1) 逻辑自测（全部 PASS 为正常，退出码 0）
python "$SKILL_DIR/scripts/selftest.py"

# 2) 一条命令跑通三示例并校验契约
python "$SKILL_DIR/scripts/run_examples.py" --out /tmp/sse-examples

# 3) 文档与代码是否仍然一致（机制的判据是否还成立）
PYTHONDONTWRITEBYTECODE=1 python -B "$SKILL_DIR/scripts/doccheck.py"

# 4) 单跑一例 + 契约门
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out /tmp/sse-out
python "$SKILL_DIR/scripts/validate_result.py" \
    --case "$SKILL_DIR/examples/case.json" --result /tmp/sse-out/result.json
```

正式运行（平台）：`/input/case.json` + `/input/task.md` → 读材料 →
`extract.py`（M3 为材料可读性兜底）→ 写 `/app/work/entities.json` →
`spec_lint.py`（**M1 门**）→ `main.py` →
`/app/output/{figure.svg,figure.png,figure.pdf,result.json}`（M2/M4/M5）→
编辑走 `--edit-svg`（M2）→ `validate_result.py` 收口。

## 对照表：想知道什么，看哪里

| 你想知道 | 看哪 | 判据 |
|-|-|-|
| 本包到底创新在哪 | `MECHANISM.md` 的 M1–M5 | 每个机制都有"没有它会怎样"与可证伪判据 |
| 某个机制是不是真的在起作用 | `MECHANISM.md` 各节的"可证伪判据" | 判据是可跑命令或可读字段 |
| 某个机制的边界在哪 | `MECHANISM.md` 各节的"已知盲区" | 明确写出测不到什么（如 M2 的 `edit.*` 不进 result.json） |
| 我能拿走哪一块 | `REUSABLE-ASSETS.md` §1（A1–A12） | 每项给"复用方式 + 采纳验证" |
| 拿走要改多少 | `REUSABLE-ASSETS.md` §2（L0–L4） | 从"只读参考"到"整套方法"五级 |
| 抄过去最容易错在哪 | `REUSABLE-ASSETS.md` §4 | 三个坑：只抄文件不抄判据、改判据不更新文档、把示例当答案 |
| 某个检查名什么意思 | `CHECK-INDEX.md` | 逐条列出，含级别与科学含义 |
| 文档有没有吹牛 | `scripts/doccheck.py` | exit 0 = 文档提到的检查名都在代码里真实存在 |

## 复用本包（入口，详细步骤见 `REUSABLE-ASSETS.md` §3）

```bash
# L1：只想要"契约校验器 / 文档对拍器 / 字体探针"三个纯工具
cp "$SKILL_DIR/scripts/validate_result.py" "$SKILL_DIR/scripts/doccheck.py" \
   "$SKILL_DIR/scripts/textfont.py" <你的项目>/tools/

# L2：还想复用夹具与字典（题集 / 金标准 / 关系字典 / 检查点清单）
cp -r "$SKILL_DIR/examples" <你的项目>/tests/fixtures/sse/
cp "$SKILL_DIR/assets/relation-dict.json" "$SKILL_DIR/assets/checklist.json" <你的项目>/assets/

# L3：还想复用"源文件自描述"模式（写进去 + 读出来，两个都要做）
#     见 REUSABLE-ASSETS.md §3.4；关键不变式：读不到内嵌清单必须明确拒绝
```

**复用验证（不能省）**：L1 的每个工具都要对自己的坏输入也被拒；
L2 的夹具改造后仍要三示例全 `exit 0`；L3 必须验证"无内嵌清单 → 非零退出"。

## 依赖

- Python 3.9+（本机实测 3.13）；运行必需 **matplotlib、Pillow、numpy**，reportlab 可选；
- PDF 抽取按 **M3 的四段回退**逐级降级（fitz → pypdf → PyPDF2 → stdlib），
  backend 如实写进 result.json；
- 无 cairosvg/svgwrite 依赖 —— PNG/PDF 预览是同一 layout+manifest 的 matplotlib
  镜像（语义一致、**非逐像素**，已在 SKILL.md 与 `uncertainty` 标注；这是 M4 判据强度的边界）；
- `scripts/doccheck.py` **只用标准库**；
- 安装（可选，仅提升预览保真度与 M3 首选后端）：`pip install matplotlib pillow numpy
  reportlab pymupdf`；字体：CJK 依系统字体（**M5**），
  `scripts/textfont.py --list` 可查（缺失时 SVG 文字仍在，PNG 可能缺字）。

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

## 限制（诚实标注，并按机制归类）

| 限制 | 影响的机制 | 说明 |
|-|-|-|
| 预览为同源镜像、非逐像素 | M4 | 预检仍执行，但"预览保真"判据强度下降 |
| PDF 字体嵌入审计为尽力而为 | M4 | 不等于目标期刊的硬性要求 |
| CJK 依系统字体 | M5、M4 | 无字体时 SVG 文字仍在，PNG 可能缺字并记 warn |
| `extract.py` 只产候选草稿 | M1 | 草稿必须复核后才能过门 |
| `edit.*` 问题只进 stdout | **M2 的已知盲区** | 靠"请求条数 vs `change_records` 条数"对拍 |
| `--edit-svg` 时 `edits` 字段不生效 | M2 | 用 `edit_requests` |
| stdlib 回退抽取质量取决于 PDF 编码 | M3 | 回退成功 ≠ 抽全 |
| TIFF/EPS 期刊级合规未逐项实测 | M4 | 故不声称 |
| 示例材料是合成内容 | — | 不是真实论文数据 |

## 维护

- 版本与接口：`SKILL.md` §7 资源表为唯一权威；`main.py --help` 与实际参数逐字一致；
- **机制修改纪律**（见 `MECHANISM.md` 末节）：改任何机制 → 先更新它的可证伪判据 →
  同步受影响的下游 → 重跑 `selftest.py` 与 `doccheck.py` → 在 `TEST.md` 补一条实测读数；
  **没有实测读数的机制判据视为未验证**；
- 判据同步：`doccheck.py` 会检查"文档提到的检查名"是否仍真实存在
  （多写 = FAIL，少写 = WARN），因此它是机制判据的守门人；
- 资产维护：新增可复用资产时同步登记到 `REUSABLE-ASSETS.md` 的 A 表并给出
  "采纳验证"；没有验证方式的资产不登记；
- 回归三连：`selftest.py` + `run_examples.py` + `doccheck.py` 全绿才可发布；
- 发布：`GITHUB_URL.txt` 第一行为公开仓库链接，发布前用未登录窗口确认可访问。
