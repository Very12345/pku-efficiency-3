# challenge-98e5a474 — 科研示意图生成与编辑（v7 · 确定性与字节级可复现版）

> 玻尔产品周赛 · 北大专区 · 学术效率 · 第三期（efficiency-3）· 组: figures
> 题目：科研示意图生成与编辑（challenge-98e5a474）
> **本版主轴 = 确定性**：把"同一份输入跑两遍必须一样"变成**可运行的 6 进程矩阵 +
> 三档判据（V1–V6）+ 逐字节实测表**，并明确区分"**故意**不稳定"（时间戳、绝对路径、
> PDF `/CreationDate`）与"**意外**不稳定"（归一化后仍不同 ⇒ 判失败）。
> 出图算法与全部 CLI 参数名/默认值/退出码语义**未改动**。

## 这是什么

一个可被 Agent 调用的 Skill：把科研案例的**来源材料**（论文摘录、表格、PDF）
变成**可编辑图稿（分层 SVG）＋合规导出件（PNG/PDF）＋可核验记录（result.json）**，
并支持对已有图稿做**源文件级编辑**。

四条主张：

1. **图画对** — 实体、关系、方向、数值、单位逐条可回溯到材料（CP1 lint +
   `data-*` 溯源属性 + G8 表外类别硬门）；
2. **图可改** — 文字是 `<text>`、图层是 `layer-*`、SVG 内嵌 ER 清单，编辑只改被指明的元素；
3. **图能投** — 导出预检（DPI/字体/色彩/PDF 结构）自动执行并记录；
4. **★ 图可复现（本版重点）** — `scripts/determinism.py` 在 6 个独立进程里
   （不同 cwd × 不同 `PYTHONHASHSEED` × 可选 `SOURCE_DATE_EPOCH`）跑主流程，
   对**全部产物**逐字节比对：**4 个产物 raw 全等、PDF 设 `SOURCE_DATE_EPOCH` 后 raw 全等、
   `result.json` 归一化后全等、0 条未归类差异**（实测见下）。

## 目录结构

```
SKILL.md                       # 技能本体（输入→执行→确定性→失败→契约→增益/机制/复用 + 自查 + 禁止）
README.md                      # 本文件
TEST.md                        # 本机实测记录（T1–T12：功能 / 确定性 / 注入 / 题集）
GITHUB_URL.txt                 # 公开仓库链接（第一行）
scripts/                       # 19 个脚本
  main.py                      #   流水线入口（含依赖门 + 字典兜底）
  determinism.py               #   ★确定性矩阵执行器（6 进程 × 全产物 sha256，只动包外副本）
  fault_inject.py              #   四形态故障注入器（25 条，只动包外副本）
  case_probe.py                #   题集执行器（5 案 + 5 探针，对可接受区间）
  spec_lint.py / checks.py / layout.py / svgbuilder.py / render.py
  manifest.py / edit.py / pdftext.py / textfont.py / report.py
  validate_result.py / selftest.py / run_examples.py / extract.py / doccheck.py
references/
  DETERMINISM.md               #   ★本版主轴：三档判据 + 逐文件实测表 + volatile_fields 逐字段 + 稳定化命令
  OUTPUT_CONTRACT.md           #   result.json 契约 + G1–G8 + 四形态回显（字段块逐字不变）
  FAULT-MATRIX.md              #   25 行实测注入矩阵 + 6 条盲区 + 缺陷修复对照
  CASE-SET.md                  #   题集 + 逐案实测 + 6 条泛化边界 + 画布预算公式
  STRENGTH-AXES.md             #   §A 对照协议 F1–F8/I1–I10 · §B 机制 M1–M5 · §C 可复用资产 A1–A12
  failure-modes.md             #   题面 12 类失败形态 → 检测 → 处置 → 档位
  CHECK-INDEX.md / EDIT-ACTION-SCHEMA.md / ER_MANIFEST.md / DRAWING_GRAMMAR.md / RUBRIC_MAP.md
assets/                        # relation-dict.json（连接规则字典）+ checklist.json（CP1–CP5）
examples/                      # 包内三示例（schematic / chart / edit）
examples/cases/                # 两个不同题材的合成案例（细胞生物学机制图 / 转录组热图）
```

## 快速开始（命令自定位，任意 cwd 可跑；产物全部写在包外）

```bash
# 0) 指定技能根（= 本 SKILL.md 所在目录）
SKILL_DIR="$(cd "$(dirname "<本 SKILL.md 的实际路径>")" && pwd)"
RUN="<包外临时目录>"     # 例如 /tmp/sse-run

# 1) 逻辑自测（35 项，退出码 0 为正常）
python "$SKILL_DIR/scripts/selftest.py"

# 2) 三示例端到端 + 契约门（schematic → chart → edit，各跑 G1–G8）
python "$SKILL_DIR/scripts/run_examples.py" --out "$RUN/examples"

# 3) ★ 确定性矩阵：6 个独立进程 × 全产物 sha256（退出码 0 = 归一化后逐字节全等）
python "$SKILL_DIR/scripts/determinism.py" --skill-root "$SKILL_DIR" --out "$RUN/det"
python "$SKILL_DIR/scripts/determinism.py" --list                    # 只列运行矩阵
python "$SKILL_DIR/scripts/determinism.py" --skill-root "$SKILL_DIR" --out "$RUN/det" --runs 6 --json

# 4) 故障演练：四形态 25 条注入（退出码 0 = 全部符合期望）
python "$SKILL_DIR/scripts/fault_inject.py" --skill-root "$SKILL_DIR" --out "$RUN/fault"

# 5) 题集：5 案 + 5 探针（退出码 0 = 全部落在声明的可接受区间内）
python "$SKILL_DIR/scripts/case_probe.py" --skill-root "$SKILL_DIR" --out "$RUN/cases"

# 6) 文档↔代码对拍（只需 0 fails）
python "$SKILL_DIR/scripts/doccheck.py" --root "$SKILL_DIR"
```

正式运行（平台）：`/input/case.json` + `/input/task.md` → 读材料 →
`extract.py` 抽候选草稿 → 写 `/app/work/entities.json` → `main.py` →
`/app/output/{figure.svg,figure.png,figure.pdf,result.json}` → `validate_result.py`。

## 确定性读数（本版的核心证据，均为本机实测）

| 文件 | 6 次运行 sha256（前 12 位） | 判据 | 结论 |
|-|-|-|-|
| `figure.svg`（15,241 B） | `24eab86e4c29` ×6 | V2 | **raw 全等** |
| `figure.png`（165,063 B） | `71fb5f387258` ×6 | V2 | **raw 全等** |
| `layout.json`（3,333 B） | `932d9d314b1b` ×6 | V2 | **raw 全等** |
| `manifest.validated.json`（4,967 B） | `3fee6c0cba90` ×6 | V2 | **raw 全等** |
| `figure.pdf`（37,944 / 37,938 B） | natural 4 个不同 sha；**stabilized `c06682bd8336` ×2** | V4 | 唯一变量 `/CreationDate`；设 `SOURCE_DATE_EPOCH` 后 **raw 全等** |
| `result.json`（9,872 B） | 6 个不同 sha；归一化后 `236b85c8dea5` ×6 | V3 | 唯一变量是 3 条 `artifacts[].abspath` |
| `determinism.spec_sha16` | `3af4c86b04dc57c1` ×6 | V6 | 输入与 CP1 判定完全一致 |

汇总：`identical_after_normalization = true`、`unclassified_differences = 0`、
`verdict = BYTE-IDENTICAL-AFTER-DOCUMENTED-NORMALISATION`、退出码 **0**；
6 次运行墙钟 1.13–1.38 秒/次。逐字段解释与稳定化命令见 `references/DETERMINISM.md`。

## 三个"会自己找错"的工具（本包的复用价值所在）

| 工具 | 做什么 | 为什么可信 |
|-|-|-|
| `scripts/determinism.py` | 6 个独立进程（不同 cwd / `PYTHONHASHSEED` / 可选 `SOURCE_DATE_EPOCH`）跑主流程，对全部产物算 sha256，输出 `determinism_report.json`（`runs[]`/`per_file_sha256`/`identical`/`volatile_fields[]`） | ①只读原包（整包复制到 tempdir 再跑副本）②不改被测脚本逻辑 ③**故意不稳定必须逐条点名**，归类不了的一律判失败（`unclassified_differences`）④归一化规则公开在报告里，第三方可复跑推翻 |
| `scripts/fault_inject.py` | 把**输入 / 模板 / 依赖 / 契约**四形态逐个故意弄坏，真实跑一遍主流程，记录退出码、`status`、`uncertainty`、fail/warn 检查名与 stdout 尾部 | ①只读原包 ②不改被测逻辑 ③**静默失败判据**（exit 0 + success + 无痕迹 ⇒ 判失效）④部分条目跑独立复核器交叉验证 |
| `scripts/case_probe.py` | 对每个案例真跑、把产物量化、逐条对照该案**声明的可接受区间**，另跑 5 条越界探针记录失效点 | ①区间是显式声明的 ②报告写"期望/实测/是否满足"三列 ③`canvas_overflow` 这类量上游检查根本不产出 ④`--out` 指包内会被拒绝 |

三者都能对**别的同族技能包**运行（`--skill-root` 指向别处即可）—— 这是它们
能被别的题复用的原因（见 `references/STRENGTH-AXES.md` §C）。

## 既有脚本的纯增量修复（由早前的故障注入发现，本版逐字节保留）

| # | 缺陷 | 修复前实测 | 增量 | 修复后实测 |
|-|-|-|-|-|
| 1 | `assets/relation-dict.json` 损坏 ⇒ CP1 门里 `json.load` 异常冒泡 | `exit 1` + 裸 `JSONDecodeError`，**连 result.json 都不写** | `main.py` 读字典处包 `try/except` + `summarize()` 后补一条 `spec_lint.corpus` warn（+18/−2 行） | `exit 0` / `success` / `warns=[spec_lint.corpus]` |
| 2 | 缺 matplotlib / Pillow ⇒ import 期直接崩，不留失败记录 | `exit 1` + 裸 `ModuleNotFoundError`，**无 result.json** | `main.py`：`import render`/`import checks` 各包 `try/except` + 依赖门调用既有 `_write_failed_result`（+27/−5 行） | `exit 1` / `failed` / `fails=[pipeline]` / `uncertainty` 写明缺失模块 |
| 3 | `--edit-svg` 分支丢弃编辑问题 ⇒ 编辑被拒也看不出来 | 错误字段名夹具：`change_records=0`、`exit 0`、stdout 无 `[edit]` 提示 | `main.py` 该分支收集并打印 `ed_issues`，同时写进 `uncertainty`（+8/−1 行） | `uncertainty` 出现 `edit issue: edit.relabel`；正常夹具仍 3 条记录 |
| 4 | 示例与新案例的 `style.canvas` 声明小于自身内容 ⇒ 图被 `viewBox` 裁掉且不报 warn | 内容 2090 px vs 声明 1500 px，最右节点整块在图外 | **数据修正**（未动脚本）：声明改 `2300×880` / `2300×900`，并在题集加常驻判据 `canvas_overflow: False` | 两案 `canvas_overflow=False`，10/10 项落在区间 |

细节与逐行证据：缺陷 1/2 见 `references/FAULT-MATRIX.md` §5，缺陷 4 见
`references/CASE-SET.md` §5。**除 `main.py` 的三处纯增量外，其余脚本逐字节未动；
本版新增的 `scripts/determinism.py` 不改任何既有文件。**

## 依赖

- Python 3.9+（实测 3.13.9）；运行必需：**matplotlib、Pillow、numpy**，reportlab 可选。
  **缺依赖不会裸崩**：会写 `failed` 的 `result.json` 并提示 `pip install matplotlib pillow numpy`；
- `determinism.py` 与 `doccheck.py` **只用标准库**，不引入新依赖；
- PDF 抽取按 fitz → pypdf → PyPDF2 → **stdlib 回退**逐级降级，`backend` 如实写进结果；
- `case_probe.py` 的 XML 良构校验优先 lxml，**缺 lxml 自动用标准库 `xml.etree`**；
- 无 cairosvg/svgwrite 依赖 —— PNG/PDF 是同一 layout+manifest 的 matplotlib 镜像
  （语义一致、非逐像素，已在 `uncertainty` 标注）；
- 字体：CJK 依赖系统字体，`scripts/textfont.py --probe` 可查；缺失时 SVG 文字仍在，
  PNG 可能缺字并记 `font.cjk` warn + `uncertainty`。

## 适用范围

- 适用：机制/信号通路示意图、结构关系图、流程图、实验装置图、数据图
  （bar/line/scatter/heatmap）的**生成与源文件级编辑**；输入可为
  Markdown/文本/CSV/PDF 材料或已有图稿；也适用于"**同一份材料必须两次出图一致**"
  这类可复现性要求（本版主轴）。
- **已实测覆盖**：schematic（两条不同题材）+ chart 的 bar 与 heatmap + edit；
  确定性矩阵 6 次运行（schematic 示例）。
- **未逐项实测**：`line`/`scatter` 分支、真实论文 PDF、>60 节点拓扑、多子图排版、
  EPS/TIFF 导出、期刊字体嵌入审计、**跨 OS/跨 matplotlib 版本的字节稳定性**、
  chart 图型的确定性、平台真实打分。
- 不适用：统计方法的数值计算与选择、海报封面等版式设计、艺术插画与图像美化、
  论文正文与文献综述写作（题面明确排除）。

## 资源形态（本题硬约束，已逐条满足）

- 包内**只有 UTF-8 文本文件**，扩展名限于 `.md/.py/.json/.txt/.csv/.yaml/.yml`；
- **不预置** PDF/PNG/SVG/TIFF/PPTX 等二进制或平台不支持的类型，也不放
  `__pycache__/`、`*.pyc`；所有图稿与渲染件由脚本**运行时生成**；
- 文件数 ≤50（本包 **49**）、单文件 ≤500KB（最大 `scripts/fault_inject.py` 46,380 B）、
  总计 ≤2MB（本包 538,134 B ≈ 525 KB）、无符号链接；
- 包内无本机绝对路径（脚本只用 `__file__` 自定位，文档用 `$SKILL_DIR`）；
  与字体相关的字符串只出现在跨平台字体探测逻辑里，不是本机运行痕迹。

## 限制（诚实标注）

- 预览为 matplotlib 镜像，非逐像素；PDF 字体嵌入审计为尽力而为；
- **确定性矩阵的边界**：6 次运行只证明"这 6 次之间没有意外差异"，不能外推为
  "任意次数都稳定"；`determinism.py` 归一化的是**已点名的**字段（时间戳、绝对路径、
  PDF xref 偏移），任何**未归类**差异都会被记成 `kind="unclassified"` 并让退出码非零；
- `extract.py` 产出的是**候选草稿**（`_draft` 标注），最终清单必须人工复核方向与关系 ——
  四个读数面都记录着：**语义方向错拦不住**（`FAULT-MATRIX` 盲区 A2）；
- 四形态注入只覆盖**注册过的 25 条**、题集只覆盖**5 案 + 5 探针**、确定性矩阵覆盖
  **6 次运行**；拦不住的盲区在 `references/FAULT-MATRIX.md` §4 与 `SKILL.md` §4 公开；
- 示例与新案例（`examples/**`）全部是**合成演示**，不是真实论文数据，不得当作正式案例答案提交。

## 维护

- 版本与接口：`SKILL.md` §⑦ 资源表为唯一权威；`main.py --help` 与实际参数逐字一致；
  改动 CLI 参数名时必须同步 `SKILL.md`、`README.md`、`TEST.md`（`doccheck.py` 会对拍，
  漏改会以 fail/warn 报出来）；
- 契约：`references/OUTPUT_CONTRACT.md` 是 result.json 的唯一契约（G1–G8），
  改契约要同时改 `scripts/validate_result.py`、`report.py` 与 `examples/EXPECTED-OUTPUT.md`；
  **字段块一个字都不许动**；
- **新增/修改任何失败分支后必须同步三处**：①`fault_inject.py` 的 registry
  ②`FAULT-MATRIX.md` 的对应行（含实测数字）③本文档的缺陷表；
  **新增/修改确定性判据同理**：①`determinism.py` 的判据与 `normalization_rules`
  ②`references/DETERMINISM.md` 的逐字段表（含新实测数字）③`TEST.md` 的 T 条目；
- 回归六件套：`selftest.py`（逻辑）+ `run_examples.py`（三示例端到端）+
  `determinism.py`（6 进程确定性）+ `fault_inject.py`（25 条注入）+
  `case_probe.py`（5 案 + 5 探针）+ `doccheck.py`（文档↔代码对拍），全绿才算可发布；
- 发布：`GITHUB_URL.txt` 第一行为公开仓库链接，发布前用未登录窗口确认可访问。
