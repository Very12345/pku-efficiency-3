# challenge-98e5a474 — 科研示意图生成与编辑（全维合并最强版 / v6）

> 玻尔产品周赛 · 北大专区 · 学术效率 · 第三期（efficiency-3）· 组: figures
> 题目：科研示意图生成与编辑（challenge-98e5a474）
> **本包是 union 包**：把五条强化轴合并到同一套脚本与文档上 ——
> **决策显性化**（D1–D16 / L0–L3）· **增益可验证**（F1–F8 / I1–I10 / R1–R13）·
> **机制显性 + 复用**（M1–M5 / A1–A12）· **失败注入**（四形态 × 25 条）·
> **多案例泛化**（5 案 2 题材 + 5 条越界探针）。`SKILL.md` 按
> **输入 → 执行 → 失败 → 增益 → 机制 → 复用** 重排，并逐节索引到各 reference。
> 出图算法与全部 CLI 参数名/默认值/退出码语义**未改动**。

## 这是什么

一个可被 Agent 调用的 Skill：把科研案例的**来源材料**（论文摘录、表格、PDF）
变成**可编辑图稿（分层 SVG）＋合规导出件（PNG/PDF）＋可核验记录
（result.json）**，并支持对已有图稿做**源文件级编辑**。

四条主张（前三条是能力，第四条是本包的重点）：

1. **图画对** — 实体、关系、方向、数值、单位逐条可回溯到材料
   （CP1 lint + `data-*` 溯源属性 + G8 表外类别硬门）；
2. **图可改** — 文字是 `<text>`、图层是 `layer-*`、SVG 内嵌 ER 清单，
   编辑只改被指明的元素；
3. **图能投** — 导出预检（DPI/字体/色彩/PDF 结构）自动执行并记录；
4. **坏得明白、边界量得出来** — 25 类故障注入各有固定的退出码/`status`/
   痕迹；5 个案例 + 5 条探针各带"可接受区间"与"期望/实测/是否满足"；
   **没测过的一律按"未测量"标注**（平台分数、`line`/`scatter` 分支、
   真实论文 PDF、>60 节点拓扑、EPS/TIFF 与期刊字体审计）。

## 目录结构

```
SKILL.md                       # 技能本体（输入→执行→失败→增益→机制→复用 六段 + 自查 + 禁止）
README.md                      # 本文件
TEST.md                        # 本机实测记录（T1–T11：功能 / 注入 / 题集）
GITHUB_URL.txt                 # 公开仓库链接（第一行）
scripts/                       # 17 个脚本
  main.py                      #   流水线入口（含依赖门 + 字典兜底）
  fault_inject.py              #   ★四形态故障注入器（25 条，只动包外副本）
  case_probe.py                #   ★题集执行器（5 案 + 5 探针，对可接受区间）
  spec_lint.py / checks.py / layout.py / svgbuilder.py / render.py
  manifest.py / edit.py / pdftext.py / textfont.py / report.py
  validate_result.py / selftest.py / run_examples.py / extract.py / doccheck.py
references/
  OUTPUT_CONTRACT.md           #   result.json 契约 + G1–G8 + 四形态 + 四个读数面（字段块逐字不变）
  FAULT-MATRIX.md              #   ★25 行实测注入矩阵 + 6 条盲区 + 2 个缺陷修复对照
  CASE-SET.md                  #   ★题集 + 逐案实测 + 6 条泛化边界 + 画布预算公式
  GAIN-PROTOCOL.md             #   对照协议 F1–F8 + 指标 I1–I10 + 实测 R1–R13 + 记账模板
  MECHANISM.md                 #   M1–M5 完整机制（没有它会怎样 / 可证伪判据 / 已知盲区）
  REUSABLE-ASSETS.md           #   12 项可复用资产 + 5 级采纳阶梯
  failure-modes.md             #   题面 12 类失败形态 → 检测 → 处置 → 档位
  CHECK-INDEX.md               #   全部检查名（doccheck 事实源 / 机制判据 / 指标取值）
  EDIT-ACTION-SCHEMA.md        #   编辑动作 → 字段名 → 记录（含实测矩阵与反模式）
  ER_MANIFEST.md · DRAWING_GRAMMAR.md · RUBRIC_MAP.md
assets/                        # relation-dict.json（连接规则字典）+ checklist.json（CP1–CP5）
examples/                      # 包内三示例（schematic / chart / edit）
examples/cases/                # ★两个新题材的合成案例（细胞生物学机制图 / 转录组热图）
```

## 快速开始（命令自定位，任意 cwd 可跑；产物全部写在包外）

```bash
# 0) 指定技能根（= 本 SKILL.md 所在目录）
SKILL_DIR="$(cd "$(dirname "<本 SKILL.md 的实际路径>")" && pwd)"

# 1) 逻辑自测（35 项，退出码 0 为正常）
python "$SKILL_DIR/scripts/selftest.py"

# 2) 三示例端到端 + 契约门（schematic → chart → edit，各跑 G1–G8）
python "$SKILL_DIR/scripts/run_examples.py" --out /tmp/sse-examples

# 3) ★ 故障演练：四形态 25 条注入（退出码 0 = 全部符合期望）
python "$SKILL_DIR/scripts/fault_inject.py" --skill-root "$SKILL_DIR" --out /tmp/sse-fault
python "$SKILL_DIR/scripts/fault_inject.py" --skill-root "$SKILL_DIR" --out /tmp/f --form dependency
python "$SKILL_DIR/scripts/fault_inject.py" --list

# 4) ★ 题集：5 案 + 5 探针（退出码 0 = 全部落在声明的可接受区间内）
python "$SKILL_DIR/scripts/case_probe.py" --skill-root "$SKILL_DIR" --out /tmp/sse-cases
python "$SKILL_DIR/scripts/case_probe.py" --skill-root "$SKILL_DIR" --out /tmp/c --group new
python "$SKILL_DIR/scripts/case_probe.py" --list

# 5) 文档↔代码对拍（0 fails / 0 warns）
python "$SKILL_DIR/scripts/doccheck.py" --root "$SKILL_DIR"
```

正式运行（平台）：`/input/case.json` + `/input/task.md` → 读材料 →
`extract.py` 抽候选草稿 → 写 `/app/work/entities.json` → `main.py` →
`/app/output/{figure.svg,figure.png,figure.pdf,result.json}` → `validate_result.py`。

## 两个"会自己找错"的工具（本包的复用价值所在）

| 工具 | 做什么 | 为什么可信 |
|-|-|-|
| `scripts/fault_inject.py` | 把**输入 / 模板 / 依赖 / 契约**四形态逐个故意弄坏，真实跑一遍主流程，记录退出码、`status`、`uncertainty`、fail/warn 检查名与 stdout 尾部 | ①只读原包（整包复制到 tempdir 再弄坏副本）②不改被测脚本逻辑 ③**静默失败判据**（exit 0 + success + 无任何痕迹 ⇒ 判失效）④部分条目还跑**独立复核器**（`validate_result.py` / `spec_lint.py`）交叉验证 |
| `scripts/case_probe.py` | 对每个案例真跑、把产物量化、逐条对照该案**声明的可接受区间**，另跑 5 条越界探针记录失效点 | ①区间是显式声明的 ②报告写"期望/实测/是否满足"三列 ③`canvas_overflow` 这类量**上游检查根本不产出** ④`--out` 指包内会被拒绝 |

两者都能对**别的同族技能包**运行（`--skill-root` 指向别处即可）—— 这是它们
能被别的题复用的原因（见 `references/REUSABLE-ASSETS.md`）。

## 本包由实测发现并修掉的三个真实缺陷

| # | 缺陷 | 修复前实测 | 增量 | 修复后实测 |
|-|-|-|-|-|
| 1 | `assets/relation-dict.json` 损坏 ⇒ CP1 门里 `json.load` 异常冒泡 | `exit 1` + 裸 `JSONDecodeError`，**连 result.json 都不写** | `main.py` 读字典处包 `try/except` + `summarize()` 后补一条 `spec_lint.corpus` warn（**+18/−2 行**） | `exit 0` / `success` / `warns=[spec_lint.corpus]` |
| 2 | 缺 matplotlib / Pillow ⇒ import 期直接崩，不留失败记录 | `exit 1` + 裸 `ModuleNotFoundError`，**无 result.json** | `main.py`：`import render`/`import checks` 各包 `try/except` + 依赖门调用既有 `_write_failed_result`（**+27/−5 行**） | `exit 1` / `failed` / `fails=[pipeline]` / `uncertainty` 写明缺失模块 |
| 3 | `--edit-svg` 分支丢弃编辑问题 ⇒ 编辑被拒也看不出来 | 错误字段名夹具：`change_records=0`、`exit 0`、**stdout 无 `[edit]` 提示** | `main.py` 该分支收集并打印 `ed_issues`，同时写进 `uncertainty`（**+8/−1 行**） | `uncertainty` 出现 `edit issue: edit.relabel`；正常夹具仍 3 条记录 |
| 3 | 包内示例与新案例的 `style.canvas` 声明小于自身内容 ⇒ 图被 `viewBox` 裁掉且不报 warn | 内容 2090 px vs 声明 1500 px，最右节点整块在图外 | **数据修正**（未动脚本）：声明改 `2300×880` / `2300×900`，并在题集加常驻判据 `canvas_overflow: False` | 两案 `canvas_overflow=False`，10/10 项落在区间 |

细节与逐行证据：缺陷 1/2 见 `references/FAULT-MATRIX.md` §5，
缺陷 3 见 `references/CASE-SET.md` §5。**除上述两处 `main.py` 纯增量外，
其余 15 个脚本逐字节未动。**

## 依赖

- Python 3.9+（实测 3.13.9）；运行必需：**matplotlib、Pillow、numpy**，
  reportlab 可选。**缺依赖不会裸崩**：会写 `failed` 的 `result.json` 并提示
  `pip install matplotlib pillow numpy`；
- PDF 抽取按 fitz → pypdf → PyPDF2 → **stdlib 回退**（zlib + Tj/TJ）逐级降级，
  无任何第三方 PDF 库也能跑，`backend` 如实写进结果；
- `case_probe.py` 的 XML 良构校验优先用 lxml，**缺 lxml 自动用标准库
  `xml.etree`**（报告记 `xml_backend`），无新增硬依赖；
- 无 cairosvg/svgwrite 依赖 —— PNG/PDF 预览是同一 layout+manifest 的
  matplotlib 镜像（语义一致、非逐像素，已在 `uncertainty` 标注）；
- 字体：CJK 依赖系统字体，`scripts/textfont.py --probe` 可查；缺失时 SVG
  文字仍在，PNG 可能缺字并记 `font.cjk` warn + `uncertainty`。

## 适用范围

- 适用：机制/信号通路示意图、结构关系图、流程图、实验装置图、数据图
  （bar/line/scatter/heatmap）的**生成与源文件级编辑**；输入可为
  Markdown/文本/CSV/PDF 材料或已有图稿。
- **已实测覆盖**：schematic（两条不同题材）+ chart 的 bar 与 heatmap + edit；
  **未逐项实测**：`line`/`scatter` 分支、真实论文 PDF、>60 节点或网状/环状
  拓扑、多子图排版、EPS/TIFF 导出、期刊字体嵌入审计、平台真实打分。
- 不适用：统计方法的数值计算与选择、海报封面等版式设计、艺术插画与
  图像美化、论文正文与文献综述写作（题面明确排除）。

## 资源形态（本题硬约束，已逐条满足）

- 包内**只有 UTF-8 文本文件**，扩展名限于 `.md/.py/.json/.txt/.csv/.yaml/.yml`；
- **不预置** PDF/PNG/SVG/TIFF/PPTX 等二进制或平台不支持的类型，也不放
  `__pycache__/`、`*.pyc`；所有图稿与渲染件由脚本**运行时生成**；
- 文件数 ≤50（本包 **49**）、单文件 ≤500KB、总计 ≤2MB（本包 492,074 B ≈ 480 KB）、
  无符号链接；
- 包内无本机绝对路径（脚本只用 `__file__` 自定位，文档用 `$SKILL_DIR`）；
  与字体相关的字符串只出现在跨平台字体探测逻辑里，不是本机运行痕迹。

## 限制（诚实标注）

- 预览为 matplotlib 镜像，非逐像素；PDF 字体嵌入审计为尽力而为；
- `extract.py` 产出的是**候选草稿**（`_draft` 标注），最终清单必须人工复核
  方向与关系 —— 四个读数面都记录着：**语义方向错拦不住**（`FAULT-MATRIX` 盲区 A2）；
- 四形态注入只覆盖**注册过的 25 条**、题集只覆盖**5 案 + 5 探针**；
  六条拦不住的盲区在 `references/FAULT-MATRIX.md` §4 与 `SKILL.md` §3 公开；
- 示例与新案例（`examples/**`）全部是**合成演示**，不是真实论文数据，
  不得当作正式案例答案提交。

## 维护

- 版本与接口：`SKILL.md` §7 资源表为唯一权威；`main.py --help` 与实际参数
  逐字一致；改动 CLI 参数名时必须同步 `SKILL.md`、`README.md`、`TEST.md`；
- 契约：`references/OUTPUT_CONTRACT.md` 是 result.json 的唯一契约（G1–G8），
  改契约要同时改 `scripts/validate_result.py`、`report.py` 与
  `examples/EXPECTED-OUTPUT.md`；**字段块一个字都不许动**；
- **新增/修改任何失败分支后必须同步三处**：①`fault_inject.py` 的 registry
  ②`FAULT-MATRIX.md` 的对应行（含实测数字）③本文档的缺陷表；
  新增/修改案例同理：①夹具 ②`case_probe.py` 的 registry ③`CASE-SET.md`；
  **不许只改文档不改工具**（那会退化成"自述"）；
- 回归五件套：`selftest.py`（逻辑）+ `run_examples.py`（三示例端到端）+
  `fault_inject.py`（25 条注入）+ `case_probe.py`（5 案 + 5 探针）+
  `doccheck.py`（文档↔代码对拍），全绿才算可发布；
- 发布：`GITHUB_URL.txt` 第一行为公开仓库链接，发布前用未登录窗口确认可访问。
