# challenge-98e5a474 — 科研示意图生成与编辑（决策系统版 / v1）

> 玻尔产品周赛 · 北大专区 · 学术效率 · 第三期（efficiency-3）· 组: figures
> 题目：科研示意图生成与编辑（challenge-98e5a474）
> **本变体的强化轴 = 决策显性化**：把"材料 → 图稿 → 导出"链路上所有会出岔子的
> 地方枚举成带编号的决策规则（D1–D16），每条规则配一个降级档位（L0–L3）、
> 一个脚本执行锚点和一条恢复条件；并新增一份把"全部检查名"列全的对照表
> （`references/CHECK-INDEX.md`）与一个能自动对拍"文档承诺 vs 代码事实"的
> 只读工具（`scripts/doccheck.py`）。算法与 CLI 接口**未改动**。

## 这是什么

一个可被 Agent 调用的 Skill：把科研案例的**来源材料**（论文摘录、表格、PDF）
变成**可编辑图稿（分层 SVG）＋合规导出件（PNG/PDF）＋可核验记录（result.json）**，
并支持对已有图稿做**源文件级编辑**。

它按"决策系统"写，而不是按"顺利流程"写：

1. **图画对** — 实体/关系/方向/数值/单位逐条可回溯（CP1 lint + `data-*` 溯源 + G8 硬门）；
2. **图可改** — 文字是 `<text>`、图层是 `layer-*`、SVG 内嵌 ER 清单，编辑只动被指明的元素；
3. **图能投** — 导出预检（DPI/字体/色彩/PDF 结构）自动执行并留记录；
4. **出错可解释** — 每个边界情况都有一张脸：编号（D）、档位（L）、锚点（脚本/检查名/退出码）。

## 目录结构

```
SKILL.md                    # 技能本体：决策模型、D1–D16、失败分支表、锚点对拍表、执行骨架
README.md                   # 本文件：定位、依赖、适用范围、限制、维护
TEST.md                     # 本机实测记录（含 D 规则逐条对应的实测档位）
GITHUB_URL.txt              # 公开仓库链接（第一行）
scripts/                    # 15 个既有脚本 + doccheck.py（本次新增，只读对拍工具）
references/
  OUTPUT_CONTRACT.md        # result.json 契约 + G1–G8 硬门（**字段块逐字保留**）
  CHECK-INDEX.md            # **新增**：全部检查名的完整清单（级别 + 科学含义）
  EDIT-ACTION-SCHEMA.md     # **新增**：编辑动作 → 字段名 → 记录 的对照表与反模式
  failure-modes.md          # 题面 12 类失败形态 → 检测 → D 规则 → L 档位（四点对齐）
  RUBRIC_MAP.md             # 五维评分（40/25/15/10/10）→ 本包文件/机制
  ER_MANIFEST.md            # ER 清单规范（绘图唯一数据源）
  DRAWING_GRAMMAR.md        # 图形语法：关系语义→箭头/线型/颜色/分组/图例
assets/                     # relation-dict.json（连接规则字典）+ checklist.json（CP 自查清单）
examples/                   # 最小示例（schematic / chart / edit + 合成材料 + EXPECTED-OUTPUT.md）
```

## 快速开始（命令自定位，任意 cwd 可跑）

```bash
# 0) 指定技能根（= 本 SKILL.md 所在目录）
SKILL_DIR="$(cd "$(dirname "<本 SKILL.md 的实际路径>")" && pwd)"

# 1) 逻辑自测（全部 PASS 为正常，退出码 0）
python "$SKILL_DIR/scripts/selftest.py"

# 2) 文档承诺 vs 代码事实 对拍（只读；退出码 0 = 无 FAIL）
python "$SKILL_DIR/scripts/doccheck.py"

# 3) 一条命令跑通示例并校验契约（schematic → chart → edit + G1–G8）
python "$SKILL_DIR/scripts/run_examples.py" --out /tmp/sse-examples

# 4) 单跑一个示例（--case 可指文件，也可指目录），并顺带打印对拍报告
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples"     --out /tmp/sse-out --doc-check
python "$SKILL_DIR/scripts/validate_result.py"     --case "$SKILL_DIR/examples/case.json" --result /tmp/sse-out/result.json
```

正式运行（平台）：`/input/case.json` + `/input/task.md` → 读材料 →
`extract.py` 抽取候选草稿 → 写 `/app/work/entities.json` → `main.py` →
`/app/output/{figure.svg,figure.png,figure.pdf,result.json}`。

## 决策系统速查（完整表见 SKILL.md §3）

| 你想要 | 看哪 | 判据 |
|-|-|-|
| 知道"这种情况该怎么办" | SKILL.md §3.3（D1–D16） | 每条 = 触发 → 动作 → 降级 → 恢复条件 |
| 知道"降级降到了哪一档" | SKILL.md §3.2（L0–L3） | L1 继续跑但记 `uncertainty`；L2 产物在、`status=partial`；L3 不产图 |
| 知道"这条规则代码里在哪" | SKILL.md §3.5（锚点对拍表） | 每行都有可跑的对拍命令 |
| 知道"某个检查名什么意思" | `references/CHECK-INDEX.md` | 逐条列出，含级别与科学含义 |
| 知道"编辑为什么没生效" | `references/EDIT-ACTION-SCHEMA.md` | 字段名必须 `relation_id`/`entity_id` |
| 验证文档没吹牛 | `scripts/doccheck.py` | 退出码 0 = 文档与代码一致 |

## 依赖

- Python 3.9+（本机实测 3.13）；运行必需 **matplotlib、Pillow、numpy**，reportlab 可选；
- PDF 抽取按 fitz → pypdf → PyPDF2 → **stdlib 回退**（zlib + `Tj/TJ`）逐级降级，
  无任何第三方 PDF 库也能跑，backend 如实写进 result.json（→ D14）；
- 无 cairosvg/svgwrite 依赖 —— PNG/PDF 预览是同一 layout+manifest 的 matplotlib
  镜像（语义一致、非逐像素，已在 SKILL.md 与 `uncertainty` 标注）；
- `scripts/doccheck.py` **只用标准库**（`argparse/json/os/re/sys`），无额外依赖；
- 安装（可选，仅提升预览保真度）：`pip install matplotlib pillow numpy reportlab pymupdf`；
  字体：CJK 依系统字体，`scripts/textfont.py --list` 可查本机能否渲染中文
  （缺失时 SVG 文字仍在，PNG 可能缺字并按 D11 记 `uncertainty`）。

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

- 预览为 matplotlib 镜像，**非逐像素**；PDF 字体嵌入审计为**尽力而为**；
- CJK 渲染依系统字体（`textfont.py` 探测）；无字体时 SVG 文字仍在，PNG 可能缺字；
- `extract.py` 只产**候选草稿**（`_draft` 标注），方向与关系必须人工复核；
- 示例材料（`examples/sources/*`）是**合成演示**，不是真实论文数据；
- **`edit.*` 类问题目前只出现在 stdout 日志**，不写进 `result.json`、不改退出码
  （见 `references/CHECK-INDEX.md` §3 与 D10）——所以本包要求用
  "请求条数 vs `change_records` 条数"人工对拍，不假装它已被机器覆盖；
- 走 `--edit-svg` 时 case 里的 `edits` 字段不生效（要用 `edit_requests`）；
- TIFF/EPS 导出路径与真实期刊字体嵌入要求未逐项实测，故不声称。

## 维护

- 版本与接口：`SKILL.md` §6 资源表为唯一权威；`main.py --help` 与实际参数逐字一致；
  改 CLI 参数名必须同步 SKILL.md、README、TEST.md；
- **决策规则与代码同步**：任何脚本新增/改名检查时，跑 `python "$SKILL_DIR/scripts/doccheck.py"`；
  它会把"文档提到但代码没有"与"代码有但文档没提"都列出来（前者 FAIL、后者 WARN）；
- 契约：`references/OUTPUT_CONTRACT.md` 是 result.json 的唯一契约（G1–G8 硬门），
  改契约要同时改 `scripts/validate_result.py`、`scripts/report.py` 与
  `examples/EXPECTED-OUTPUT.md`；**契约字段块本身不得改动**；
- 回归三连：`selftest.py`（逻辑）+ `run_examples.py`（端到端 + 契约门）+
  `doccheck.py`（文档一致性），三者全绿才算可发布；打包形态另跑外部验收器；
- 发布：`GITHUB_URL.txt` 第一行为公开仓库链接，发布前用未登录窗口确认可访问。
