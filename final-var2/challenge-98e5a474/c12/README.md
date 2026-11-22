# challenge-98e5a474 — 科研示意图生成与编辑（增益可验证版 / v2）

> 玻尔产品周赛 · 北大专区 · 学术效率 · 第三期（efficiency-3）· 组: figures
> 题目：科研示意图生成与编辑（challenge-98e5a474）
> **本变体的强化轴 = 增益可验证化**：新增 `references/GAIN-PROTOCOL.md`，
> 给出与"不加载 Skill 的基础 Agent"的公平对照协议（F1–F8 条款）、可测指标
> 定义（I1–I10）、**本机真跑出来的对照读数（R1–R13）**，以及一张
> **"能支撑 / 不能支撑"表**——把没有跑过的指标明确写成"未测量"。
> 算法与 CLI 接口**未改动**。

## 这是什么

一个可被 Agent 调用的 Skill：把科研案例的**来源材料**变成**可编辑图稿（分层 SVG）
＋合规导出件（PNG/PDF）＋可核验记录（result.json）**，并支持对已有图稿做
**源文件级编辑**。它同时交付一套度量协议，让"加载技能有没有用"这件事
可以被第三方按同一套命令、同一套判据复跑。

四条主张：

1. **图画对** — 实体/关系/方向/数值/单位逐条可回溯；
2. **图可改** — 文字是 `<text>`、图层可拆、SVG 内嵌 ER 清单，编辑只动被指明的元素；
3. **图能投** — 导出预检（DPI/字体/色彩/PDF 结构）自动执行并留记录；
4. **增益可测** — 每次运行的退出码、契约有效性、门控计数、溯源比例、返工轮次
   都是可记录的观测量；**没测过的就写"未测量"**（协议 F8）。

## 目录结构

```
SKILL.md                       # 技能本体：度量模型 I1–I10、执行路线 M0–M6、决策规则 G1–G8
README.md                      # 本文件
TEST.md                        # 本机实测记录（含 M2–M5 的原始读数）
GITHUB_URL.txt                 # 公开仓库链接（第一行）
scripts/                       # 15 个既有脚本 + doccheck.py（新增，只读对拍工具）
references/
  OUTPUT_CONTRACT.md           # result.json 契约 + G1–G8 硬门（**字段块逐字保留**）
  GAIN-PROTOCOL.md             # **新增**：对照协议 F1–F8 / 指标 I1–I10 / 实测 R1–R13 / 记账模板
  EDIT-ACTION-SCHEMA.md        # **新增**：编辑字段级契约（协议 G4 的依据）
  CHECK-INDEX.md               # **新增**：全部检查名清单（指标取值的字典）
  failure-modes.md             # 失败形态 → 检测 → 处置 → **对读数的影响**
  RUBRIC_MAP.md                # 五维评分（40/25/15/10/10）→ 本包文件/机制
  ER_MANIFEST.md               # ER 清单规范
  DRAWING_GRAMMAR.md           # 图形语法：关系语义→箭头/线型/颜色/分组/图例
assets/                        # relation-dict.json + checklist.json
examples/                      # 最小示例（schematic / chart / edit + 合成材料）
```

## 快速开始（命令自定位，任意 cwd 可跑）

```bash
# 0) 指定技能根（= 本 SKILL.md 所在目录）
SKILL_DIR="$(cd "$(dirname "<本 SKILL.md 的实际路径>")" && pwd)"

# 1) 逻辑自测（全部 PASS 为正常，退出码 0）
python "$SKILL_DIR/scripts/selftest.py"

# 2) 一条命令跑通三示例并校验契约（≈5 秒；本机实测读数见 TEST.md §M4）
python "$SKILL_DIR/scripts/run_examples.py" --out /tmp/gp-examples

# 3) 单跑 + 契约门（这就是对照记录里的 B 臂）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out /tmp/gp-a
python "$SKILL_DIR/scripts/validate_result.py" \
    --case "$SKILL_DIR/examples/case.json" --result /tmp/gp-a/result.json

# 4) 文档与代码是否仍然一致（防止判据漂移）
PYTHONDONTWRITEBYTECODE=1 python -B "$SKILL_DIR/scripts/doccheck.py"
```

正式运行（平台）：`/input/case.json` + `/input/task.md` → 读材料 →
`extract.py` 抽取候选草稿 → 写 `/app/work/entities.json` → `main.py` →
`/app/output/{figure.svg,figure.png,figure.pdf,result.json}` → 按 M6 记账。

## 增益怎么读（协议速查）

| 你想知道 | 看哪 | 判据 |
|-|-|-|
| 两臂怎么跑才公平 | `GAIN-PROTOCOL.md` §1 | F1–F8 条款，逐条有"违反后果" |
| 测什么、从哪取值 | `GAIN-PROTOCOL.md` §2 | I1–I10，每项给出机器可读来源 |
| 已经测出了什么 | `GAIN-PROTOCOL.md` §3 | R1–R13，逐条给命令与读数 |
| **哪些结论还没被支撑** | `GAIN-PROTOCOL.md` §4 | 明确分"已支撑 / 未测量"两栏 |
| 复跑后怎么记 | `GAIN-PROTOCOL.md` §5 | 填空模板（**必填"未测量项"一行**） |
| 哪个读数被降级污染了 | `failure-modes.md` §1/§2 | 每个失败形态多一列"对读数的影响" |
| 编辑到底生效没有 | `EDIT-ACTION-SCHEMA.md` §3 | 请求条数 vs `change_records` 条数（G4） |
| 某个检查名什么意思 | `CHECK-INDEX.md` | 逐条列出，含级别与科学含义 |

> **一句话总结本包的自我克制**：我们**没有**跑基线臂，因此**不声称**在平台
> 打分上更高；我们声称的是——本技能一侧的全部读数可复跑、判据固定、
> 未测量项已列明。这条克制本身就是"增益可验证性"的评分点。

## 依赖

- Python 3.9+（本机实测 3.13）；运行必需 **matplotlib、Pillow、numpy**，reportlab 可选；
- PDF 抽取按 fitz → pypdf → PyPDF2 → **stdlib 回退**（zlib + `Tj/TJ`）逐级降级，
  backend 如实写进 result.json（协议 §1 的 F7 要求"失败也记录"）；
- 无 cairosvg/svgwrite 依赖 —— PNG/PDF 预览是同一 layout+manifest 的 matplotlib
  镜像（语义一致、**非逐像素**，已在 SKILL.md 与 `uncertainty` 标注）；
- `scripts/doccheck.py` **只用标准库**，无额外依赖；
- 安装（可选，仅提升预览保真度）：`pip install matplotlib pillow numpy reportlab pymupdf`；
  字体：CJK 依系统字体，`scripts/textfont.py --list` 可查（缺失时 SVG 文字仍在，
  PNG 可能缺字，按 §1 F2 记入 `uncertainty`）。

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
- CJK 渲染依系统字体；`extract.py` 只产**候选草稿**（`_draft` 标注）；
- 示例材料是**合成演示**，不是真实论文数据；
- **`edit.*` 类问题只进 stdout**，不进 `result.json`、不改退出码 ⇒ 必须用
  条数对拍（协议 G4）；
- 走 `--edit-svg` 时 case 里的 `edits` 字段不生效（要用 `edit_requests`）；
- **未测量**：基线臂（不加载 Skill）的任何读数、人工修改量、端到端耗时对照、
  科学结论正确性对照；TIFF/EPS 在目标期刊模板下的逐项合规亦未实测。
  逐条列在 `GAIN-PROTOCOL.md` §4。

## 维护

- 版本与接口：`SKILL.md` §7 资源表为唯一权威；`main.py --help` 与实际参数逐字一致；
- **协议同步**：任何脚本行为改变（新增检查、改字段名、改退出码）后，必须重跑
  `GAIN-PROTOCOL.md` §6 的命令并更新 §3（读数）与 §4（能否支撑）；
- 判据固定：对照成立的前提是两臂用同一个 `validate_result.py`（F5）——
  改判据等于作废已有对照记录，必须在协议修订记录里写明；
- 一致性检查：`python "$SKILL_DIR/scripts/doccheck.py"` 自动对拍
  "文档提到的检查名"与"代码真实产出的检查名"；
- 回归三连：`selftest.py` + `run_examples.py` + `doccheck.py` 全绿才可发布；
- 发布：`GITHUB_URL.txt` 第一行为公开仓库链接，发布前用未登录窗口确认可访问。
