# challenge-98e5a474 — 科研示意图生成与编辑（多案例泛化与题集版 / v5）

> 玻尔产品周赛 · 北大专区 · 学术效率 · 第三期（efficiency-3）· 组: figures
> 题目：科研示意图生成与编辑（challenge-98e5a474）
> **本变体的强化轴 = 泛化可测量**：新增**两个不同题材**的合成案例
> （细胞生物学 PINK1/Parkin 线粒体自噬机制图 · 转录组三条件表达矩阵热图），
> 外加一个可运行的题集执行器 `scripts/case_probe.py` —— 它逐案真跑、
> 把产物量化成数字、再对照**该案声明的可接受区间**逐条判定，另跑一组
> **故意越界**的探针，把"泛化到哪里会失效"量成表格
> （`references/CASE-SET.md` §4）。本轮 **10/10 项落在声明区间内**，
> 并因此发现并修好一处真实缺陷（画布声明小于内容 ⇒ 图被 viewBox 裁掉）。
> 出图算法与全部 CLI 参数名/默认值/退出码语义**未改动**。

## 这是什么

一个可被 Agent 调用的 Skill：把科研案例的**来源材料**（论文摘录、表格、PDF）
变成**可编辑图稿（分层 SVG）＋合规导出件（PNG/PDF）＋可核验记录
（result.json）**，并支持对已有图稿做**源文件级编辑**。

本版多问一个问题：**换个题材、换个图型、把规模放大，还成立吗？** 三条主张：

1. **图画对** — 实体、关系、方向、数值、单位逐条可回溯到材料
   （CP1 lint + `data-*` 溯源属性 + G8 表外类别硬门）；
2. **图可改** — 文字是 `<text>`、图层是 `layer-*`、SVG 内嵌 ER 清单；
3. **能力有边界，且边界是量出来的** — 5 个案例 + 5 条越界探针，逐条给出
   "期望区间 / 实测值 / 是否满足"；没测过的题材一律按"未测量"标注。

## 目录结构

```
SKILL.md                       # 技能本体（题集 / 泛化边界 / 画布预算规则 / S0–S7 / 五维映射）
README.md                      # 本文件：依赖、适用范围、限制、维护
TEST.md                        # 本机实测记录（含 10 项题集运行结果）
GITHUB_URL.txt                 # 公开仓库链接（第一行）
scripts/
  main.py                      # 流水线入口
  case_probe.py                # ★本版新增：题集执行器（逐案真跑 + 对区间 + 边界探针）
  spec_lint.py / checks.py / layout.py / ...        # 与基线逐字节相同
references/
  CASE-SET.md                  # ★本版新增：题集 + 逐案实测 + 六条泛化边界 + 画布预算规则
  OUTPUT_CONTRACT.md           # result.json 契约（字段块逐字不变）
  RUBRIC_MAP.md / failure-modes.md / CHECK-INDEX.md / EDIT-ACTION-SCHEMA.md
  ER_MANIFEST.md / DRAWING_GRAMMAR.md
assets/
  relation-dict.json           # 连接规则字典（kind→arrow/line/dash/color）
  checklist.json               # CP1–CP5 自查清单
examples/
  case.json / case_chart.json / case_edit.json      # 包内三示例（schematic/chart/edit）
  sources/…                                          # 示例来源材料（合成）
  cases/                       # ★本版新增：两个新题材的合成案例
    README.md                  #   两案的任务说明与难度层
    case_mitophagy.json        #   ① 细胞生物学机制图
    case_expr_heatmap.json     #   ② 转录组表达矩阵热图
    sources/mitophagy-note.md · sources/expression-table.csv
  EXPECTED-OUTPUT.md           # 示例期望产物（文字清单；产物运行时生成）
```

## 快速开始（命令自定位，任意 cwd 可跑；产物全部写在包外）

```bash
# 0) 指定技能根（= 本 SKILL.md 所在目录）
SKILL_DIR="$(cd "$(dirname "<本 SKILL.md 的实际路径>")" && pwd)"

# 1) 逻辑自测（35 项，退出码 0 为正常）
python "$SKILL_DIR/scripts/selftest.py"

# 2) 一条命令跑通包内三示例并校验契约（schematic → chart → edit + 各跑 G1–G8）
python "$SKILL_DIR/scripts/run_examples.py" --out /tmp/sse-examples

# 3) ★ 跑题集：5 个案例 + 5 条边界探针，逐条对"可接受区间"（退出码 0 = 全部落在区间内）
python "$SKILL_DIR/scripts/case_probe.py" --skill-root "$SKILL_DIR" --out /tmp/sse-cases
python "$SKILL_DIR/scripts/case_probe.py" --skill-root "$SKILL_DIR" --out /tmp/c --group new
python "$SKILL_DIR/scripts/case_probe.py" --list

# 4) 单跑一个新案例
python "$SKILL_DIR/scripts/main.py" \
    --case "$SKILL_DIR/examples/cases/case_mitophagy.json" --out /tmp/sse-mito
python "$SKILL_DIR/scripts/validate_result.py" \
    --case "$SKILL_DIR/examples/cases/case_mitophagy.json" --result /tmp/sse-mito/result.json
```

正式运行（平台）：`/input/case.json` + `/input/task.md` → 读材料 →
`extract.py` 抽候选草稿 → 写 `/app/work/entities.json` → `main.py` →
`/app/output/{figure.svg,figure.png,figure.pdf,result.json}` → `validate_result.py`。

## 题集执行器（本版新增能力的用法）

- **它做什么**：对每个案例真跑一次 `main.py`，从产物里量出
  实体/关系/分组/类别计数、`fail/warn` 数、产物角色、溯源覆盖率、
  SVG 是否良构 XML、**画布是否溢出**、顶层键数、耗时；再逐条对照该案的
  `expect` 区间，写"期望 / 实测 / 是否满足"；
- **它还做什么**：跑 5 条故意越界的探针（不支持的图型、18 节点长链×2、
  特殊字符、containment 未分组），把"失效点"变成可复现的记录；
- **它不改什么**：只读技能包；夹具与产物写 `--out`；`--out` 指向包内会被拒绝；
- **它判什么**：`conforms = 全部判据都 ok`；任一条不符即在报告里打印
  期望/实测差值，进程退出码 1；
- **产物**：`<out>/case-report.json`（逐案全字段）+ 终端表格。

## 本版修的缺陷（一处数据修正 + 一处纯增量 + 一处文档更正）

| # | 缺陷 | 修复前实测 | 处置 | 修复后实测 |
|-|-|-|-|-|
| 1 | 包内示例与新案例的画布声明小于自身内容 ⇒ 图被 `viewBox` 裁掉且不报 warn | 内容 2090 px vs 声明 1500 px | **数据修正**：声明改 `2300×880` / `2300×900`；题集加常驻判据 `canvas_overflow: False` | 两案 `canvas_overflow=False`，10/10 落在区间 |
| 2 | `--edit-svg` 分支把编辑问题整个丢掉（编辑被拒也看不出来） | 错误字段名夹具：`change_records=0`、`exit 0`、**stdout 无提示** | `main.py` 该分支收集 `ed_issues`、一致地打印并写进 `uncertainty`（**+8/−1 行**） | `uncertainty` 出现 `edit issue: edit.relabel`；正常夹具仍 3 条记录 |
| 3 | 旧文档称「走 `--edit-svg` 时 `edits` 字段不生效」 | 实测两字段都生效（各 3 条） | **更正文档**（`EDIT-ACTION-SCHEMA.md` §2.2 + `SKILL.md`） | 真正的坑改述为「字段名写错 ⇒ 请求被拒」 |

> 除第 2 项的 **+8/−1 行**外，`scripts/*.py` 与基线逐字节相同
> （`case_probe.py` 是新增文件）。

## 原先的缺陷记录（画布）

| 夹具 | 修复前 | 后果（实测） | 修复后 |
|-|-|-|-|
| `examples/case.json` | 画布 `1500×860`，内容 2090×90 | 最右节点 E6 落在 x=1850–2090，**整块在 viewBox 外被裁**，且 checks 报 0 fail 0 warn | `2300×880`，`canvas_overflow=False` |
| `examples/cases/case_mitophagy.json` | 画布 `1500×900` | 同上 | `2300×900`，`canvas_overflow=False` |

根因是**夹具把画布声明小了**：显式声明 `style.canvas` 时布局不会再自动扩展
（`layout.py` 的确定性行为），而 SVG `viewBox` 与 PNG/PDF 都按声明尺寸裁剪。
处置：按 `references/CASE-SET.md` §5 的预算公式改声明尺寸，并在题集里加一条
**常驻判据** `canvas_overflow: False`，以后画布算小会被题集直接报偏离。
`scripts/*.py` 本轮**未改动**。

## 依赖

- Python 3.9+（实测 3.13.9）；运行必需：**matplotlib、Pillow、numpy**，
  reportlab 可选；
- `case_probe.py` 的 XML 良构校验优先用 lxml，**缺 lxml 自动用标准库
  `xml.etree`**（报告记 `xml_backend`），没有新增硬依赖；
- PDF 抽取按 fitz → pypdf → PyPDF2 → **stdlib 回退**（zlib + Tj/TJ）逐级降级；
- 无 cairosvg/svgwrite 依赖 —— PNG/PDF 是同一 layout+manifest 的 matplotlib
  镜像（语义一致、非逐像素，已在 `uncertainty` 标注）；
- 字体：CJK 依赖系统字体，`scripts/textfont.py --probe` 可查；
  缺失时 SVG 文字仍在，PNG 可能缺字并记 `font.cjk` warn + `uncertainty`。

## 适用范围

- 适用：机制/信号通路示意图、结构关系图、流程图、实验装置图、数据图
  （bar/line/scatter/heatmap）的**生成与源文件级编辑**；输入可为
  Markdown/文本/CSV/PDF 材料或已有图稿。
- **已实测覆盖**：schematic（两条不同题材）+ chart 的 bar 与 heatmap +
  edit；**未逐项实测**：line/scatter 分支、真实论文 PDF 材料、>60 节点或
  网状/环状拓扑、多子图排版、EPS/TIFF 导出（详见 `references/CASE-SET.md` §4）。
- 不适用：统计方法的数值计算与选择、海报封面等版式设计、艺术插画与
  图像美化、论文正文与文献综述写作（题面明确排除）。

## 资源形态（本题硬约束，已逐条满足）

- 包内**只有 UTF-8 文本文件**，扩展名限于 `.md/.py/.json/.txt/.csv/.yaml/.yml`；
- **不预置** PDF/PNG/SVG/TIFF/PPTX 等二进制或平台不支持的类型，也不放
  `__pycache__/`、`*.pyc`；所有图稿与渲染件由脚本**运行时生成**；
- 文件数 ≤50、单文件 ≤500KB、总计 ≤2MB、无符号链接；
- 包内无本机绝对路径（脚本只用 `__file__` 自定位，文档用 `$SKILL_DIR`）；
  与字体相关的字符串只出现在跨平台字体探测逻辑里，不是本机运行痕迹。

## 限制（诚实标注）

- 题集覆盖**两个新题材**，不代表别的题材；§4 的六条边界就是当前测到的极限
  （G1 图型白名单、G2 长链+小画布会被静默裁、G3 不声明画布的代价、
  G4 转义已正确、G5 containment 可拦、G6 **语义方向错拦不住**）；
- 预览为 matplotlib 镜像，非逐像素；PDF 字体嵌入审计为尽力而为；
- `extract.py` 产出的是**候选草稿**（`_draft` 标注），最终清单必须人工复核
  方向与关系；数值一律逐字抄表、**不换算单位**；
- 示例与新案例（`examples/**`）都是**合成演示**，不是真实论文数据，
  也不得当作正式案例答案提交。

## 维护

- 版本与接口：`SKILL.md` §7 资源表为唯一权威；`main.py --help` 与实际参数
  逐字一致；改动 CLI 参数名时必须同步 SKILL.md、README、TEST.md；
- 契约：`references/OUTPUT_CONTRACT.md` 是 result.json 的唯一契约（G1–G8），
  改契约要同时改 `scripts/validate_result.py`、`report.py` 与
  `examples/EXPECTED-OUTPUT.md`；
- **加案例的三步法**（`references/CASE-SET.md` §6）：放夹具 → 在
  `case_probe.py` 的 registry 加一条（含 `expect` 区间）→ 跑 `--only` 看实测，
  若与区间不符先查夹具，再决定是不是新的泛化边界；
- 回归四件套：`selftest.py`（逻辑）+ `run_examples.py`（三示例端到端）+
  `case_probe.py`（5 案 + 5 探针）+ `doccheck.py`（文档↔代码对拍），全绿才可发布；
- 发布：`GITHUB_URL.txt` 第一行为公开仓库链接，发布前用未登录窗口确认可访问。
