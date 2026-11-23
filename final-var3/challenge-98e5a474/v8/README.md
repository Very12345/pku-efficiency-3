# challenge-98e5a474 — 科研示意图生成与编辑（v8 · 契约四形态 × 边界值矩阵版）

> 玻尔产品周赛 · 北大专区 · 学术效率 · 第三期（efficiency-3）· 组: figures
> 题目：科研示意图生成与编辑（challenge-98e5a474）
> **本版主轴 = 输出契约的边界行为**：平台给的 `output_contract` 可能是任意形状，
> 所以把"每个键都回显对、且不出现 `null`"做成**可运行的 31 行注入矩阵**：
> 六种容器形态 × 边界值 × 非法类型 × 缺字段，逐行真跑主流程 + 独立契约校验器，
> 记录实测退出码 / `status` / 回显值（含类型）/ G5 判定 / **是否静默通过**。
> 出图算法与全部 CLI 参数名/默认值/退出码语义**未改动**。

## 这是什么

一个可被 Agent 调用的 Skill：把科研案例的**来源材料**（论文摘录、表格、PDF）
变成**可编辑图稿（分层 SVG）＋合规导出件（PNG/PDF）＋可核验记录（result.json）**，
并支持对已有图稿做**源文件级编辑**。

四条主张：

1. **图画对** — 实体、关系、方向、数值、单位逐条可回溯到材料（CP1 lint +
   `data-*` 溯源属性 + G8 表外类别硬门）；
2. **图可改** — 文字是 `<text>`、图层是 `layer-*`、SVG 内嵌 ER 清单；
3. **图能投** — 导出预检（DPI/字体/色彩/PDF 结构）自动执行并记录；
4. **★ 契约边界面量得出来（本版重点）** — `scripts/contract_matrix.py` 把
   `output_contract` 的**任意形状**注入一遍：**31/31 行拿到可判定读数、
   27 行 VALID、4 行 INVALID（`null` 与类型冲突被抓住）、16 行"静默通过"逐条点名**。

## 目录结构

```
SKILL.md                       # 技能本体（输入与契约→执行→契约矩阵→失败→契约门→增益/机制/复用 + 自查 + 禁止）
README.md                      # 本文件
TEST.md                        # 本机实测记录（T1–T12：功能 / 契约矩阵 / 注入 / 题集）
GITHUB_URL.txt                 # 公开仓库链接（第一行）
scripts/                       # 19 个脚本
  main.py                      #   流水线入口（含依赖门 + 字典兜底）
  contract_matrix.py           #   ★契约四形态 × 边界值矩阵（31 行注入，只动包外副本）
  fault_inject.py              #   四形态故障注入器（25 条，只动包外副本）
  case_probe.py                #   题集执行器（5 案 + 5 探针，对可接受区间）
  spec_lint.py / checks.py / layout.py / svgbuilder.py / render.py
  manifest.py / edit.py / pdftext.py / textfont.py / report.py
  validate_result.py / selftest.py / run_examples.py / extract.py / doccheck.py
references/
  CONTRACT-MATRIX.md           #   ★本版主轴：判据 S1–S5 + 逐行实测表 + 静默通过清单 + 未覆盖声明
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
RUN="<包外临时目录>"

# 1) 逻辑自测（35 项，退出码 0 为正常）
python "$SKILL_DIR/scripts/selftest.py"

# 2) 三示例端到端 + 契约门（schematic → chart → edit，各跑 G1–G8）
python "$SKILL_DIR/scripts/run_examples.py" --out "$RUN/examples"

# 3) ★ 契约矩阵：31 行注入（退出码 0 = 每行都拿到可判定读数）
python "$SKILL_DIR/scripts/contract_matrix.py" --skill-root "$SKILL_DIR" --out "$RUN/cm"
python "$SKILL_DIR/scripts/contract_matrix.py" --list
python "$SKILL_DIR/scripts/contract_matrix.py" --skill-root "$SKILL_DIR" --out "$RUN/cm" --only R13,R17,R27

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

## 契约矩阵读数（本版的核心证据，均为本机实测）

| 计数 | 值 | 说明 |
|-|-|-|
| 行数 / 已测量 / 无法测量 | **31 / 31 / 0** | 每行都真跑主流程 + 独立契约校验器 ⇒ 退出码 0 |
| VALID / INVALID | **27 / 4** | INVALID 的是 R16（契约声明 `null`）与 R24–R26（契约键与既有字段类型冲突） |
| **静默通过** | **16** | R06 R07 R09 R13 R14 R15 R17 R18 R21 R22 R23 R27 R28 R29 R30 R31 |
| `main_exit == 0` | **31/31** | 契约形状问题**从不**让主流程非零退出 ⇒ 必须靠契约门发现 |
| `status` 分布 | `{"success": 31}` | 同上 |
| 形态 / 边界覆盖 | 12 种形态 · 24 种边界 | 字符串/数组/对象/数值/布尔/嵌套 × 空串/空数组/0/超长/字面量/null/非法类型/缺字段 |
| 矩阵墙钟 | 67 秒 | 31 行 × 独立 scratch 副本（交付前自证用，评分轮不必跑） |

**四类静默通过（Agent 必须知道的三条边界）**

| 静默 | 命中行 | 被静默接受的是什么 |
|-|-|-|
| **S4** | R27–R31 | 顶层 `output_contract` 形状非法（缺失/`null`/`[]`/字符串/`{}`）⇒ **G5 整段跳过** |
| **S1** | R17 R18 R09 R15 | 未知类型词被当字符串（`"whatever"`、`""`、`"null"`、超长串）⇒ 回显 `""` 且 VALID |
| **S3** | R06 R07 R21 R22 R23 | 结构化提示（嵌套对象/带元素数组）被降级为空容器，**值形状没有任何门在查** |
| **S2** | R13 R14 | 字面量被当"类型"：声明 `12` 回显 `0`、声明 `true` 回显 `false` |

逐行表（含每行的回显值与类型）见 `references/CONTRACT-MATRIX.md` §3。

## 三个"会自己找错"的工具（本包的复用价值所在）

| 工具 | 做什么 | 为什么可信 |
|-|-|-|
| `scripts/contract_matrix.py` | 把 `output_contract` 的六种容器形态 × 边界值 × 非法类型 × 缺字段逐个注入 `case.json`，每行真跑主流程 + `validate_result.py`，记录退出码/`status`/回显值(类型)/G5/静默判定 | ①只读原包（整包复制到 tempdir）②不改被测脚本逻辑 ③**静默通过判据公开**（S1–S5）④每行都有 `--timeout`，无法测量会被记成 `unmeasurable` 而不是静默跳过 |
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
本版新增的 `scripts/contract_matrix.py` 不改任何既有文件。**

## 依赖

- Python 3.9+（实测 3.13.9）；运行必需：**matplotlib、Pillow、numpy**，reportlab 可选。
  **缺依赖不会裸崩**：会写 `failed` 的 `result.json` 并提示 `pip install matplotlib pillow numpy`；
- `contract_matrix.py` 与 `doccheck.py` **只用标准库**，不引入新依赖；
- PDF 抽取按 fitz → pypdf → PyPDF2 → **stdlib 回退**逐级降级，`backend` 如实写进结果；
- `case_probe.py` 的 XML 良构校验优先 lxml，缺 lxml 自动用标准库 `xml.etree`；
- 无 cairosvg/svgwrite 依赖 —— PNG/PDF 是同一 layout+manifest 的 matplotlib 镜像
  （语义一致、非逐像素，已在 `uncertainty` 标注）；
- 字体：CJK 依赖系统字体，`scripts/textfont.py --probe` 可查；缺失时 SVG 文字仍在，
  PNG 可能缺字并记 `font.cjk` warn + `uncertainty`。

## 适用范围

- 适用：机制/信号通路示意图、结构关系图、流程图、实验装置图、数据图
  （bar/line/scatter/heatmap）的**生成与源文件级编辑**；也适用于
  "**调用方给的输出契约形状不确定**"这类接口稳健性要求（本版主轴）；
- **已实测覆盖**：schematic（两条不同题材）+ chart 的 bar 与 heatmap + edit；
  契约矩阵 31 行（schematic 基线）；
- **未逐项实测**：平台真实 `output_contract` 字段清单、`oneOf`/联合类型、值形状
  （数组元素/对象内部字段类型）、并发与中断、`result.json` 超 500KB 后的平台行为、
  chart/edit 基线的契约交互、`line`/`scatter` 分支、真实论文 PDF、EPS/TIFF 导出、
  期刊字体嵌入审计、平台真实打分；
- 不适用：统计方法的数值计算与选择、海报封面等版式设计、艺术插画与图像美化、
  论文正文与文献综述写作（题面明确排除）。

## 资源形态（本题硬约束，已逐条满足）

- 包内**只有 UTF-8 文本文件**，扩展名限于 `.md/.py/.json/.txt/.csv/.yaml/.yml`；
- **不预置** PDF/PNG/SVG/TIFF/PPTX 等二进制或平台不支持的类型，也不放
  `__pycache__/`、`*.pyc`；所有图稿与渲染件由脚本**运行时生成**；
- 文件数 ≤50（本包 **49**）、单文件 ≤500KB（最大 `scripts/fault_inject.py` 46,380 B）、
  总计 **530,034 B ≈ 518 KB**（上限 2 MB）、无符号链接；
- 包内无本机绝对路径（脚本只用 `__file__` 自定位，文档用 `$SKILL_DIR`）；
  与字体相关的字符串只出现在跨平台字体探测逻辑里，不是本机运行痕迹。

## 限制（诚实标注）

- 预览为 matplotlib 镜像，非逐像素；PDF 字体嵌入审计为尽力而为；
- **契约门的边界**：G5 只保证"声明的键存在且**顶层容器类型**对得上"，
  不保证"声明被理解" —— 16 行静默通过就是这条边界的实测证据；
  值形状、联合类型、平台真实字段清单**均未测量**；
- `extract.py` 产出的是**候选草稿**（`_draft` 标注），最终清单必须人工复核方向与关系 ——
  **语义方向错拦不住**（`FAULT-MATRIX` 盲区 A2）；
- 四形态注入只覆盖**注册过的 25 条**、题集只覆盖**5 案 + 5 探针**、契约矩阵覆盖
  **31 行注入**；拦不住的盲区在 `references/FAULT-MATRIX.md` §4 与 `SKILL.md` §4 公开；
- 示例与新案例（`examples/**`）全部是**合成演示**，不是真实论文数据，不得当作正式案例答案提交。

## 维护

- 版本与接口：`SKILL.md` §⑦ 资源表为唯一权威；`main.py --help` 与实际参数逐字一致；
  改动 CLI 参数名时必须同步 `SKILL.md`、`README.md`、`TEST.md`（`doccheck.py` 会对拍）；
- 契约：`references/OUTPUT_CONTRACT.md` 是 result.json 的唯一契约（G1–G8），
  改契约要同时改 `scripts/validate_result.py`、`report.py` 与 `examples/EXPECTED-OUTPUT.md`；
  **字段块一个字都不许动**；
- **新增/修改任何失败分支后必须同步三处**：①`fault_inject.py` 的 registry
  ②`FAULT-MATRIX.md` 的对应行（含实测数字）③本文档的缺陷表；
  **新增/修改契约判据同理**：①`contract_matrix.py` 的 `ROWS` 与 `judge_silent()`
  ②`references/CONTRACT-MATRIX.md` 的逐行表与静默清单（含新实测数字）③`TEST.md` 的 T 条目；
  **只加行不加判据**会导致"行数涨了、结论没变"，等同于自述；
- 回归六件套：`selftest.py`（逻辑）+ `run_examples.py`（三示例端到端）+
  `contract_matrix.py`（31 行契约注入）+ `fault_inject.py`（25 条注入）+
  `case_probe.py`（5 案 + 5 探针）+ `doccheck.py`（文档↔代码对拍），全绿才算可发布；
- 发布：`GITHUB_URL.txt` 第一行为公开仓库链接，发布前用未登录窗口确认可访问。
