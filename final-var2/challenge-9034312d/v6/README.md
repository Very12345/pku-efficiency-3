# challenge-9034312d · 实验装置与技术路线图 Skill（全维合并版）

玻尔产品周赛 · 北大专区 · 学术效率第三期（efficiency-3）· figures 组。
把「装置怎么搭、步骤怎么走、物料从哪来到哪去、技术路线分几个阶段」的科研材料，
变成一张**可编辑、可追溯、可复核**的科研图稿：分层 SVG 源文件 + PNG/PDF 预览
+ 证据链 + 结构化 `result.json`。

- 工作单：`apparatus_and_technical_route`（题面「组织方具体输入修订」）
- Skill 名（YAML frontmatter）：`apparatus-and-route-diagrams`
- 公开作品入口：`GITHUB_URL.txt`（单行）
- 本版定位：**把五条线并进同一个包，并用一份整合 SKILL.md 重排索引**

## 0. 五条线（本版 = 全维合并）

| 线 | 一句话 | 主证据文件 | 新增脚本 |
|-|-|-|-|
| 决策显性化 | 异常怎么判、判完怎么办，写成可执行规则与可复跑用例 | `references/failure-modes.md`（附录 A/B/C） | `scripts/decision_probe.py` |
| 增益可验证 | "加载它好了多少"做成预注册协议 + 真跑记录（含负面结果） | `references/GAIN-PROTOCOL.md` + `comparison-data.json` | `scripts/bare_baseline.py`、`scripts/gain_probe.py` |
| 机制与复用 | 三层机制各自"没有它会怎样"+ 15 项可复用资产与四步搬运流程 | `references/MECHANISM.md` | — |
| 失败注入与恢复 | 32 条四形态故障注入实测 + 运行前闸门把静默失败变响 | `references/FAULT-MATRIX.md` | `scripts/fault_inject.py`、`scripts/preflight.py` |
| 多案例泛化 | 4 个合成案例（三种图类）+ 期望表 + 泛化损失量化 | `references/CASE-SET.md` + `case-set.json` | `scripts/case_set_run.py` |

> 合并原则：**内容不删**。同主题材料合并成一份文档，并在文首写清合并来源与阅读顺序。

## 1. 目录结构与"文件合并对照"

```
SKILL.md                   ★ 唯一入口：按「输入→执行→失败→增益→机制→复用」重排
README.md                  本文件（结构 / 合并对照 / 依赖 / 用法 / 限制 / 维护）
TEST.md                    本机真实验收记录（合规、4 案跑批、32 条注入、负例、泛化探针）
GITHUB_URL.txt             GitHub 公开链接（单行）
references/
  OUTPUT_CONTRACT.md       result.json 契约 + G1–G10 + 故障视角读法 + 最小形态示例
  RUBRIC_MAP.md            ★ 五维（40/25/15/10/10）逐条落点与可复核证据
  failure-modes.md         ★ 四形态实测失败模式 + D1–D20 全表 + 27 行失败分支表 + 20 个决策用例
  FAULT-MATRIX.md          ★ 32 条故障注入实测矩阵 + 9 条静默 + 8 条缺口 + 闸门效果
  GAIN-PROTOCOL.md         ★ 公平对照协议 + 实跑记录 + 三层机制反例摘要
  MECHANISM.md             ★ 三层机制与逐层反例 + 15 项可复用资产与四步复用流程
  CASE-SET.md              ★ 题集逐案说明：输入/期望结构/可接受区间/难度/实测/失效边界
  case-set.json            题集期望表（机器可读）
  comparison-data.json     对照实验原始数据（两版字段并集）
  vocabulary.md            术语表与词表（kind / 关系 / 图类 / 命名 / 状态）
  figure-blueprint.md      布局蓝图（图元 / 模板落点 / 命名 / 导出 / 扩展）
scripts/                   15 个自定位脚本（编排 / 闸门 / 演练 / 跑批 / 证据 / 模型 / 布图 /
                           渲染 / 校验 / 契约 / 字体 / 对照下界 / 指标复算 / 决策探针）
assets/connection_rules.json
templates/                 palette.json + 组件连接核对清单(.md) + 实体关系核对表(.csv)
examples/                  示例输入、题集案例、文本类运行产物、期望产物清单（README 已并入
                           原 output/README-EXAMPLE.md 的正文）
```

**文件合并对照**（合并后内容逐字保留，只是换了位置；括号内为合并来源）：

| 合并后的文件 | 吸收了 | 为什么合并 |
|-|-|-|
| `references/GAIN-PROTOCOL.md` | `COMPARISON-RECORD-20261122.md`、`COMPARISON-SUMMARY.md` | 三份都在回答"怎么比、比出了什么"，分开读容易只看到协议看不到数字 |
| `references/failure-modes.md` | `DECISION-CASES.md`、旧版 D1–D20 表 / 状态聚合 / 失败分支表 | "应当怎么判"与"实测判成什么"放一起才能互相验证 |
| `references/MECHANISM.md` | `REUSE-GUIDE.md` | 机制与"怎么搬走"是同一件事的两面 |
| `references/OUTPUT_CONTRACT.md` | `assets/result_example.json` | 契约与它的最小形态示例应在一处，避免两处漂移 |
| `examples/output/<case>/artifacts.json` | 该案例的 `evidence.json`/`layout.json`/`verify_report.json` | 三份同为"运行产物"，合并后与 `result.json` 并列更清楚 |
| `examples/README.md` | `examples/output/README-EXAMPLE.md` | 都在说明"示例与运行产物"，且都指向 `EXPECTED-OUTPUT.md` |

> 合并的硬约束来自题面：*at most 50 UTF-8 text files*。合并是**换位置**，
> 不是删内容 —— 每份来源文档的正文（含表格与实测数字）都完整保留在合并文件里。

## 2. 依赖

| 依赖 | 用途 | 缺失时（**实测**，不是推测） |
|-|-|-|
| Python 3.10+（标准库） | 解析 / 证据 / 布局 / 写 SVG / 校验 | 必需 |
| Pillow（PIL） | `figure.png` 预览 | ⚠ PNG **与 PDF 一起失败**（reportlab 内部也 import PIL）⇒ 两个导出件都缺 ⇒ G4 失败、退出码 3（FAULT-MATRIX F3-01） |
| reportlab | `figure.pdf` 预览 | 只 PDF 缺失 ⇒ `status=partial` + `uncertainty[scope=pdf]`，退出码 0（F3-02） |
| 本机中文字体 | PNG 中文渲染 | `scope=fonts` 记录；`status` 仍 `success` 但 G10 判失败 ⇒ 退出码 3（F3-03） |

不需要 `cairosvg` / `svgwrite` / `python-pptx`：SVG 是手写 XML，预览与源文件共用同一布局模型。
字体候选路径在 `scripts/fonts.py`（`%WINDIR%` 优先、正斜杠形式，属跨平台探测逻辑）；
PDF 用 reportlab 内置 CID 字体 `STSong-Light`。

## 3. 快速开始

```bash
SKILL_DIR=/skills/weekly-skill      # 技能根 = 含 SKILL.md 的目录

# ① 运行前闸门（不写产物，只读检查；退出码 0/1/3）
python "$SKILL_DIR/scripts/preflight.py" --case /input/case.json --task /input/task.md --deps

# ② 正常出图
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md --out /app/output

# ③ 交付自查（G1–G10）
python "$SKILL_DIR/scripts/check.py" /app/output/<case_id>/result.json

# ④ 题集跑批（4 案；退出码 0 = 全 PASS）
python "$SKILL_DIR/scripts/case_set_run.py" --out /tmp/run --json /tmp/run/report.json

# ⑤ 泛化探针：只留 text 字段重跑，量化结构化信息消失后的损失
python "$SKILL_DIR/scripts/case_set_run.py" --text-only --out /tmp/run-flat

# ⑥ 故障演练（32 条；只改沙箱副本，不动本包）
python "$SKILL_DIR/scripts/fault_inject.py" --out /tmp/fault --json /tmp/fault/report.json

# ⑦ 增益对照三条件（C0 下界 / C1 本包 / C2 关掉门禁）+ 指标复算
python "$SKILL_DIR/scripts/bare_baseline.py" --case <case.json> --out /tmp/c0
printf '{}' > /tmp/empty-rules.json
python "$SKILL_DIR/scripts/main.py" --case <case.json> --out /tmp/c2 --rules /tmp/empty-rules.json
python "$SKILL_DIR/scripts/gain_probe.py" --result /app/output/<case_id>/result.json --baseline /tmp/c0

# ⑧ 决策用例探针（20 条观测）
python "$SKILL_DIR/scripts/decision_probe.py" --out /tmp/decisions --json /tmp/decisions/obs.json
```

产物写入 `<out>/<case_id>/`：`evidence.json`、`layout.json`、`figure.svg`、`figure.png`、
`figure.pdf`、`verify_report.json`、`result.json`（7 个文件）。

## 4. 实测结论速览（数字的唯一权威处是各 reference）

| 测试 | 结果 | 证据 |
|-|-|-|
| 题集跑批（4 案，三种图类） | `cases=4 · passed=4 · failed=0`；G1–G10 四次全过 | `references/CASE-SET.md §5` |
| 泛化探针（`--text-only`） | 实体保留率 0.200–0.667、关系保留率 **0.000**–0.357；装置图降级 `partial` | `references/CASE-SET.md §6` |
| 故障注入（32 条） | 退出码与期望不符 **0**；静默失败 **10**（缺陷型 9）；闸门漏网静默缺陷 **0** | `references/FAULT-MATRIX.md §5/§7` |
| 决策用例（20 条） | 观测表 20/20 与期望一致（`deviations=[]`） | `references/failure-modes.md` 附录 C |
| 增益对照（C0/C1/C2） | Q1 0.00→1.00、Q2 1→0、Q3 0→3（C1−C2 归因于规则层）；**耗时变大** | `references/GAIN-PROTOCOL.md` 附录 A |
| 确定性 | 同输入同目录：`figure.svg`/`layout.json`/`verify_report.json` 逐字节一致 | `TEST.md` T3 |

## 5. 关键机制（为什么比「让 Agent 直接画」更可靠）

1. **证据先行（M1 / CP1）**：每条实体/关系带 `locator`+`quote`，每份材料带 `sha256`
   —— 「每个实体可追溯」从自述变成证据（来源绑定率实测 0.00 → 1.00）。
2. **确定性布局 + 规格探针（M2 / CP3）**：布局是纯函数，`spec_sha16` 是"同输入同布局"的指纹；
   SVG/PNG/PDF 三后端共享同一布局模型。
3. **规则资产的机器审计（M3 / CP2）**：连接语义做成可编辑 JSON，error 级强制降级、
   warn 级只提示（`recycle-review` 等）；改 JSON 即改审计结论。
   ⚠ `--rules` 写错时审计会静默空转 —— 这是实测缺口，靠闸门拦住。
4. **契约门（CP4）**：G1–G10 与 `references/OUTPUT_CONTRACT.md` 一一对应；
   9 条契约注入实测 9/9 被拦下、门号准确。
5. **运行前闸门**：把 9 条静默缺陷在运行前变成 finding（实测 0 漏网）。
6. **可核验的增益与边界**：增益有协议与真跑记录（含负面结果），
   泛化有量化保留率，故障有 32 条实测矩阵 —— 全部可被第三方复跑。

## 6. 限制（如实声明）

- 只负责**绘图表达**与**可编辑交付**：不做数值拟合、不判断实验方案科学性、不做排版适配；
- 材料无结构化实体时走**文本解构**，只串联相邻步骤 —— 实测关系保留率可低至 **0**，
  且不一定会让 `status` 降级；需要 Agent 先补结构化实体；
- 装置图为**单层装配**（三桶布局）；多级嵌套与局部放大视图**不支持**；
- 实体数 > 24 或阶段数 > 5 **未测**；图内数值注记不强制渲染；
- 未覆盖的故障形态：磁盘写满、输出目录只读、超长材料、并发重复运行、容器挂载缺失；
- 本包全部实测数字来自**合成案例**与本机环境（Windows 11 · CPython 3.13.9），
  **不构成**对平台正式评分的预测；正式案例、白板与评分由平台提供/执行；
- 本包不宣称任何具体分数。

## 7. 失败处理

三道门按顺序过，**任何一门报错都改输入，不要改门**：

```
preflight.py（运行前：输入/结构/资产/依赖）
   → main.py（运行中：D1–D12 + uncertainty 记账）
      → check.py（运行后：G1–G10）
```

现象 → 规则号 → 处置 → 证据位点，逐条见 `references/failure-modes.md §1`；
32 条注入的实测行为与 8 条缺口见 `references/FAULT-MATRIX.md`。

## 8. 维护

- **图元/配色四处同步**：`scripts/model.py` 的 `KINDS`/`RELATION_KINDS`、
  `templates/palette.json`、`assets/connection_rules.json`、`references/vocabulary.md`；
- **布局规则**：`references/vocabulary.md` 附录 A（布局蓝图）+ `scripts/layout.py`；
- **审计规则**：`assets/connection_rules.json` + `scripts/svg_verify.py`；
- **契约与自查**：`references/OUTPUT_CONTRACT.md` + `scripts/check.py`；
- **闸门规则**：`scripts/preflight.py` 的四组 checks（加静默风险 → 加 finding，别改 `main.py`）；
- **故障语料**：`scripts/fault_inject.py` 的 `_specs()`（每条注入一行，加行即加覆盖面）；
- **题集**：`examples/cases/` + `references/case-set.json`（新增案例必须登记，见 SKILL.md D13/D14）；
- **评分覆盖**：`references/RUBRIC_MAP.md`（改动后逐维复核落点是否仍成立）；
- **实测记录**：`TEST.md`；示例期望产物：`examples/EXPECTED-OUTPUT.md`。

## 9. 打包自检（提交前）

```bash
python validate_pkg.py <本包目录>                          # 期望 [PASS]
grep -rnE '(^|[^A-Za-z])[A-Za-z]:[\\/]' <本包目录>         # 期望无输出（https:// 不误报）
find <本包目录> -name '__pycache__' -o -name '*.pyc'       # 期望无输出
```

> 本版是**合并版**，文件数接近上限（49/50）：新增文件时优先把同主题内容并入既有文档，
> 或合并"同一案例的多份文本产物"（见 §1 的合并对照），不要为了凑数删实质内容。
