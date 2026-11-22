# challenge-98e5a474 — 科研示意图生成与编辑（失败注入与恢复演练版 / v4）

> 玻尔产品周赛 · 北大专区 · 学术效率 · 第三期（efficiency-3）· 组: figures
> 题目：科研示意图生成与编辑（challenge-98e5a474）
> **本变体的强化轴 = 可靠性可证伪**：新增一个**可运行的失败注入器**
> `scripts/fault_inject.py`（输入 / 模板 / 依赖 / 契约 四形态 × 25 条），
> 把每一种坏法都真的注入到**包外副本**上跑一遍主流程，并把
> "注入什么 → 期望行为 → 实测退出码 / status / uncertainty → 是否静默失败"
> 逐行写成 `references/FAULT-MATRIX.md`。本轮 **25/25 符合期望、0 条静默失败**，
> 并且注入过程**发现并修掉了两个真实缺陷**（详见下文「本版修的两个缺陷」）。
> 出图的算法与全部 CLI 参数名/默认值/退出码语义**未改动**。

## 这是什么

一个可被 Agent 调用的 Skill：把科研案例的**来源材料**（论文摘录、表格、PDF）
变成**可编辑图稿（分层 SVG）＋合规导出件（PNG/PDF）＋可核验记录
（result.json）**，并支持对已有图稿做**源文件级编辑**。

本版多问一个问题：**当东西被弄坏时，它怎么表现？** 三条主张：

1. **图画对** — 实体、关系、方向、数值、单位逐条可回溯到材料
   （CP1 lint + `data-*` 溯源属性 + G8 表外类别硬门）；
2. **图可改** — 文字是 `<text>`、图层是 `layer-*`、SVG 内嵌 ER 清单，
   编辑只改被指明的元素；
3. **坏得明白** — 25 类故障注入的真实退出码、`status`、`uncertainty` 与
   检查名固定在矩阵里；**"出了事却什么都没留下"被判为技能失效**（静默律）。

## 目录结构

```
SKILL.md                       # 技能本体（四形态故障模型 / S0–S7 / 已知盲区 / 五维映射 / 自查）
README.md                      # 本文件：依赖、适用范围、限制、维护
TEST.md                        # 本机实测记录（含 25 条注入与两个缺陷的修复前后对照）
GITHUB_URL.txt                 # 公开仓库链接（第一行）
scripts/
  main.py                      # 流水线入口（含依赖门 + relation-dict 兜底，见下）
  fault_inject.py              # ★本版新增：四形态故障注入与恢复演练（只动包外副本）
  spec_lint.py / checks.py / validate_result.py / ...   # 与基线逐字节相同
references/
  FAULT-MATRIX.md              # ★本版新增：25 行实测矩阵 + 6 条盲区 + 2 条缺陷修复记录
  OUTPUT_CONTRACT.md           # result.json 契约（字段块逐字不变）
  RUBRIC_MAP.md / failure-modes.md / CHECK-INDEX.md / EDIT-ACTION-SCHEMA.md
  ER_MANIFEST.md / DRAWING_GRAMMAR.md
assets/
  relation-dict.json           # 连接规则字典（kind→arrow/line/dash/color）
  checklist.json               # CP1–CP5 自查清单
examples/                      # 最小示例（schematic / chart / edit + 合成材料 + EXPECTED-OUTPUT.md）
```

## 快速开始（命令自定位，任意 cwd 可跑；产物全部写在包外）

```bash
# 0) 指定技能根（= 本 SKILL.md 所在目录）
SKILL_DIR="$(cd "$(dirname "<本 SKILL.md 的实际路径>")" && pwd)"

# 1) 逻辑自测（35 项，退出码 0 为正常）
python "$SKILL_DIR/scripts/selftest.py"

# 2) 一条命令跑通三示例并校验契约（schematic → chart → edit + 各跑 G1–G8）
python "$SKILL_DIR/scripts/run_examples.py" --out /tmp/sse-examples

# 3) 单跑一个示例（--case 可指文件，也可指目录）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out /tmp/sse-out
python "$SKILL_DIR/scripts/validate_result.py" \
    --case "$SKILL_DIR/examples/case.json" --result /tmp/sse-out/result.json

# 4) ★ 失败注入与恢复演练（25 条，约 40 s；退出码 0 = 全部符合期望）
python "$SKILL_DIR/scripts/fault_inject.py" --skill-root "$SKILL_DIR" --out /tmp/sse-fault
#    只看清单 / 只跑某形态 / 只跑某几条
python "$SKILL_DIR/scripts/fault_inject.py" --list
python "$SKILL_DIR/scripts/fault_inject.py" --skill-root "$SKILL_DIR" --out /tmp/f --form dependency
python "$SKILL_DIR/scripts/fault_inject.py" --skill-root "$SKILL_DIR" --out /tmp/f --only D13,D18,D21
```

正式运行（平台）：`/input/case.json` + `/input/task.md` → 读材料 →
`extract.py` 抽候选草稿 → 写 `/app/work/entities.json` → `main.py` →
`/app/output/{figure.svg,figure.png,figure.pdf,result.json}` → `validate_result.py`。

## 失败注入器（本版新增能力的用法）

- **它做什么**：把整包复制到临时 scratch 目录，在那里**故意弄坏**四种东西
  —— 输入（case/材料）、模板（清单/分组/图例/连接规则字典）、依赖
  （PDF 库/matplotlib/Pillow/CJK 字体/加密 PDF/渲染崩溃）、契约
  （`output_contract` 声明缺失或形状不符）—— 然后真实跑一遍 `main.py`。
- **它不改什么**：不改被测脚本的逻辑、不改 CLI 参数名、不改退出码语义；
  注入手段只有"动夹具 / 动数据 / 动 `PYTHONPATH` 上的 `sitecustomize` /
  在副本里包一层模块"四种。每次跑完原包 sha 不变。
- **它判什么**：每条记录都要求"留痕"（非零退出码 / `status` /
  `checks.fails|warns` / `uncertainty` 至少一个）。**四者全空 ⇒ 静默失败
  ⇒ 判该行不合格**。另有 `must_trace` 指定"这一条必须出现的检查名"。
- **它顺手复核**：部分条目跑完主流程后再跑一条**独立**命令
  （`validate_result.py` 或 `spec_lint.py`），把复核器自己的退出码也记进矩阵。
  D23（契约形状不符）就是靠这条交叉验证才没被主流程的 `success` 骗过去。
- **产物**：`<out>/fault-matrix.json`（机器可读，25 条全字段）+ 终端表格。

## 本版修的三个缺陷（两处纯增量 + 一处文档更正，逐条点名）

由注入发现、**先复现崩溃再加增量修复**；`main.py` 的 CLI 参数名/默认值/
退出码语义均未改动，其余 13 个脚本逐字节未动。

| # | 缺陷 | 修复前（实测） | 增量 | 修复后（实测） |
|-|-|-|-|-|
| 1 | `assets/relation-dict.json` 损坏会让 CP1 门里的 `json.load` 抛异常冒泡 | `exit 1` + 裸 `JSONDecodeError` traceback，**连 `result.json` 都不写** | `main.py`：读字典处包 `try/except`；`summarize()` 之后补一条 `spec_lint.corpus` warn（**+18 / −2 行**） | `exit 0` / `success` / 23 键 / `warns=[spec_lint.corpus]`，图稿照常交付 |
| 2 | 缺 matplotlib / Pillow 时在 import 期直接崩，不留失败记录 | `exit 1` + 裸 `ModuleNotFoundError`，**无 `result.json`** | `main.py`：`import render` / `import checks` 各包 `try/except`，解析完 case、建好输出目录后加一道**依赖门**调用既有 `_write_failed_result`（**+27 / −5 行**） | `exit 1` / `failed` / `fails=[pipeline]` / `uncertainty` 写明缺失模块与安装提示 |
| 3 | `--edit-svg` 分支把 `edit_from_svg()` 返回的编辑问题**整个丢掉** ⇒ 编辑被拒也看不出来 | 错误字段名夹具：`change_records=0`、`exit 0`、**stdout 无 `[edit]` 提示**（旧文档却写着「会打印」） | `main.py` 该分支收集 `ed_issues`、一致地打印并写进 `result.json.uncertainty`（**+8/−1 行**） | 同一夹具 → `uncertainty` 出现 `edit issue: edit.relabel`；正常夹具仍 `change_records=3` |

细节与逐行证据见 `references/FAULT-MATRIX.md` §5。

## 依赖

- Python 3.9+（实测 3.13.9）；运行必需：**matplotlib、Pillow、numpy**，
  reportlab 可选。**缺依赖不会裸崩**：会写 `failed` 的 `result.json` 并提示
  `pip install matplotlib pillow numpy`；
- PDF 抽取按 fitz → pypdf → PyPDF2 → **stdlib 回退**（zlib + Tj/TJ）逐级降级，
  无任何第三方 PDF 库也能跑，`backend` 如实写进结果；
- 无 cairosvg/svgwrite 依赖 —— PNG/PDF 预览是同一 layout+manifest 的
  matplotlib 镜像（语义一致、非逐像素，已在 `uncertainty` 标注）；
- 字体：CJK 依赖系统字体，`scripts/textfont.py --probe` 可查；缺失时 SVG
  文字仍在，PNG 可能缺字并记 `font.cjk` warn + `uncertainty`。

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
- 包内无本机绝对路径（脚本只用 `__file__` 自定位，文档用 `$SKILL_DIR`）；
  与字体相关的字符串只出现在**跨平台字体探测逻辑**里（Windows 字体目录、
  Linux/Noto 目录等候选路径），不是本机某次运行留下的痕迹。

## 限制（诚实标注）

- 预览为 matplotlib 镜像，非逐像素；PDF 字体嵌入审计为尽力而为；
- `extract.py` 产出的是**候选草稿**（`_draft` 标注），最终清单必须人工复核
  方向与关系 —— 矩阵里 D09b 明确记录了"**方向被对调时结构门拦不住**"；
- **`fault_inject.py` 只覆盖注册过的 25 条注入**，不代表穷尽所有故障；
  已知 6 条盲区（材料内容不可读、方向语义错、独立 `spec_lint.py` 对坏字典
  仍会崩、Pillow 与 matplotlib 缺失去别、`--skip-checks` 自选降级、加密 PDF
  主流程不感知）已在 `references/FAULT-MATRIX.md` §4 与 SKILL.md §7 公开；
- 示例材料（`examples/sources/*`）是**合成演示**，不是真实论文数据。

## 维护

- 版本与接口：`SKILL.md` §8 资源表为唯一权威；`main.py --help` 与实际参数
  逐字一致；改动 CLI 参数名时必须同步 SKILL.md、README、TEST.md；
- 契约：`references/OUTPUT_CONTRACT.md` 是 result.json 的唯一契约（G1–G8），
  改契约要同时改 `scripts/validate_result.py`、`report.py` 与
  `examples/EXPECTED-OUTPUT.md`；
- **新增/修改任何故障分支后必须同步三处**：①`fault_inject.py` 的 registry
  ②`references/FAULT-MATRIX.md` 的对应行（含实测数字）③本 README 的缺陷表；
  **不许只改文档不改注入**（那会退化成"自述"）；
- 回归三件套：`selftest.py`（逻辑）+ `run_examples.py`（端到端 + 契约门）+
  `fault_inject.py`（25 条注入）+ `doccheck.py`（文档↔代码对拍），全绿才算可发布；
- 发布：`GITHUB_URL.txt` 第一行为公开仓库链接，发布前用未登录窗口确认可访问。
