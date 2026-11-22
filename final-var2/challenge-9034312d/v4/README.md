# challenge-9034312d · 实验装置与技术路线图 Skill（故障注入与恢复演练版）

玻尔产品周赛 · 北大专区 · 学术效率第三期（efficiency-3）· figures 组。
把「装置怎么搭、步骤怎么走、物料从哪来到哪去、技术路线分几个阶段」的科研材料，
变成一张**可编辑、可追溯、可复核**的科研图稿：分层 SVG 源文件 + PNG/PDF 预览
+ 证据链 + 结构化 `result.json`。

- 工作单：`apparatus_and_technical_route`（题面「组织方具体输入修订」）
- Skill 名（YAML frontmatter）：`apparatus-and-route-diagrams`
- 公开作品入口：`GITHUB_URL.txt`（单行）
- 本版主题：**先证明它在坏条件下不会骗人，再谈画得好不好**

## 0. 本版与基线的差别（一句话：算法不动，把"会坏的地方"全部跑一遍并补一道闸门）

| | 基线 | 本版 |
|-|-|-|
| 主流程 `scripts/main.py` | 9 个脚本 | **逐字节不变**（CLI、默认值、退出码语义一致） |
| 是否知道"坏条件下会怎样" | 靠阅读代码推断 | **32 条注入实测**（`references/FAULT-MATRIX.md`） |
| 静默失败（退出码 0 但实际没做对） | 未系统排查 | **实测 9 条**，逐条给位点与复核办法 |
| 运行前闸门 | 无 | **新增 `scripts/preflight.py`**（四类 finding，实测拦住 9/9 静默缺陷） |
| 故障演练工具 | 无 | **新增 `scripts/fault_inject.py`**（可重跑、只改沙箱副本） |

> 为什么值得单独做这一版：题面「可靠体验」10 分里有一项是**异常处理**，
> 而"异常处理做得好不好"只有注入过才知道。这一版把这件事从形容词变成了数字。

## 1. 目录结构

```
SKILL.md                   Skill 本体（自定位 §0；主线五步 + 0.5 闸门；D1–D12 与 F1–F4）
README.md                  本文件（用途/依赖/调用/限制/维护）
TEST.md                    本机真实验收记录（合规、可跑、32 条注入、负例）
GITHUB_URL.txt             GitHub 公开链接（单行）
references/
  OUTPUT_CONTRACT.md       result.json 契约：18 个顶层字段 + G1–G10（字段块逐字保留）
  RUBRIC_MAP.md            ★ 评分五维（40/25/15/10/10）逐条落点与对照方案
  FAULT-MATRIX.md          ★★ 本版核心：32 条四形态注入的实测矩阵 + 9 条静默 + 8 条缺口
  failure-modes.md         失败模式（按四形态重写，每条指向矩阵行号）+ 打包门 R1–R6
  figure-blueprint.md      布局蓝图（图元/模板/命名/导出/扩展）
  vocabulary.md            术语表（kind/关系/图类/命名/状态）
scripts/
  main.py                  一键流水线（编排）        ← 与基线逐字节相同
  preflight.py             ★ 本版新增：运行前闸门（输入/结构/资产/依赖）
  fault_inject.py          ★ 本版新增：32 条故障注入与恢复演练
  gain_evidence.py         证据抽取（CP1）
  model.py                 SIR：实体/关系/步骤/流向解析
  layout.py                确定性布图
  render_svg.py            手写分层 SVG
  export_preview.py        PNG(PIL) + PDF(reportlab)
  svg_verify.py            SVG 校验 + 连接规则审计
  check.py                 契约门 G1–G10
  fonts.py                 中文字体探测
assets/                    connection_rules.json（规则字典）+ result_example.json
templates/                 palette.json + 组件连接核对清单(.md) + 实体关系核对表(.csv)
examples/                  最小调用示例（示例，非正式案例）+ 文本类运行产物
```

**包形态（平台硬约束）**：只含 `.md/.py/.json/.txt/.csv/.yaml/.yml`；无 `__pycache__`、
无 `.pyc`、无 `.pdf/.png/.svg/.pptx`；无符号链接；无本机绝对路径。
`figure.svg`/`figure.png`/`figure.pdf` 由脚本运行时现场生成。

## 2. 依赖

| 依赖 | 用途 | 缺失时（**以下为实测，不是推测**） |
|-|-|-|
| Python 3.10+（标准库） | 解析 / 证据 / 布局 / 写 SVG / 校验 | 必需 |
| Pillow（PIL） | `figure.png` 预览 | ⚠ **PNG 与 PDF 会一起失败**：reportlab 内部也 `import PIL` ⇒ 两个导出件都缺 ⇒ 契约门 G4 失败、退出码 3（矩阵 F3-01） |
| reportlab | `figure.pdf` 预览 | 只 PDF 缺失 ⇒ `status=partial`、`uncertainty[scope=pdf]`，退出码仍 0（矩阵 F3-02） |
| 本机中文字体（msyh / simhei / Noto CJK…） | PNG 中文渲染 | `fonts[].found=false` + `uncertainty[scope=fonts]`；`status` 仍 `success`，但 `check.py` 的 G10 判失败 ⇒ 退出码 3（矩阵 F3-03） |

不需要 `cairosvg` / `svgwrite` / `python-pptx`：SVG 是手写 XML，预览与源文件共用同一
布局模型。字体探测候选路径在 `scripts/fonts.py`（`%WINDIR%` 优先、正斜杠形式）；
PDF 用 reportlab 内置 CID 字体 `STSong-Light`。

## 3. 快速开始（cwd 不是技能根也能跑）

```bash
SKILL_DIR=/skills/weekly-skill      # 技能根 = 含 SKILL.md 的目录

# ① 先过闸门（本版新增；不写产物，只读检查）
python "$SKILL_DIR/scripts/preflight.py" --case /input/case.json \
  --task /input/task.md --deps

# ② 正常出图（官方运行时形态：/input/* → /app/output）
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md \
  --out /app/output

# ③ 交付自查（G1–G10；退出码 0 = 全过）
python "$SKILL_DIR/scripts/check.py" /app/output/<case_id>/result.json

# ④ 示例案例（--case 给目录时自动取目录下 case.json + task.md）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out /tmp/out

# ⑤ 编辑既有图稿（同名 id 替换、新 id 追加，动作写入 change_record）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
  --task "$SKILL_DIR/examples/task.md" \
  --merge "$SKILL_DIR/examples/route_spec.mutation.example.json" --out /tmp/out-merge

# ⑥ 故障演练（本版新增；只改沙箱副本，不动本包）
python "$SKILL_DIR/scripts/fault_inject.py" --out /tmp/fault --json /tmp/fault/report.json
```

产物写入 `<out>/<case_id>/`：`evidence.json`、`layout.json`、`figure.svg`、
`figure.png`、`figure.pdf`、`verify_report.json`、`result.json`（7 个文件）。

**退出码速查**：

| 脚本 | 0 | 1 | 2 | 3 |
|-|-|-|-|-|
| `main.py` | 成功且契约门全过 | 流水线异常（仍落盘 `failed/result.json`） | 输入缺失 | 已出图但契约门不过 |
| `check.py` | G1–G10 全过 | 有 issue | 用法错误 | — |
| `preflight.py` | 无 finding | 只有 warn（可继续，但已告警） | 用法错误 | 有 error（建议先修） |
| `fault_inject.py` | 演练跑完 | 探针自身出错 | — | — |

## 4. 关键机制（为什么比「让 Agent 直接画」更可靠）

1. **证据先行（CP1）**：`gain_evidence.py` 从真实材料抽取实体/关系，逐条带 `locator`
   与 `quote` 及材料 `sha256`，落盘 `evidence.json` 并回显进 `result.json.evidence`
   —— 「每个实体可追溯」从自述变成证据。
2. **连接规则资产（CP2）**：`assets/connection_rules.json` 把类别词表与连接语义
   （sequence / connect / 流向 / 自环 / 回流 / 装置图物料不作终点）做成**可扩展**规则，
   由 `svg_verify.py` 机器审计；error 级违规强制 `status=partial`（D10）。
   ⚠ 实测缺口：`--rules` 写错时审计会**静默空转**（矩阵 F2-04/F2-05），故有闸门。
3. **校验闭环（CP3）**：`svg_verify.py` 检查 SVG 合法 XML、5 层图层、可编辑 `<text>`、
   箭头与关系一一对应、无断头、编号 1..N 连续、图例 kind == 图面 kind，并给确定性探针
   `spec_sha16`（同输入同布局的机器证据）。
4. **契约门（CP4）**：`check.py` 执行 G1–G10（含 status 诚实性），与
   `references/OUTPUT_CONTRACT.md` 一一对应。实测 9 条契约注入 9/9 被拦下，门号准确。
5. **运行前闸门（本版新增）**：`preflight.py` 把"静默失败"在运行前变成 finding ——
   输入/结构/资产/依赖四类，共 20 余种 `code`。实测对 9 条静默缺陷 0 漏网。
6. **确定性**：布局是纯函数（无随机、无时间依赖）；同输入同目录下 `figure.svg`、
   `layout.json`、`verify_report.json` 逐字节一致（`TEST.md` T3 有 sha256 记录）。
7. **可编辑性**：SVG 文字是真实 `<text>`（不是路径描边），实体组带
   `data-entity/data-source/data-kind/data-stage/data-step-no`；可在 Inkscape 或文本编辑器
   直接改，改完把改动补进 `change_record`（`action: manual-edit`）。

## 5. 本版实测结论摘要（完整数据在 `references/FAULT-MATRIX.md`）

| 形态 | 注入 | 结论 |
|-|-|-|
| 输入 | 11 条 | 缺文件退出码 2 / 坏 JSON 与坏 `--merge` 退出码 1 / 空壳退出码 3；**2 条静默**（`--material`、`--task` 指错 = 不报错） |
| 模板·资产 | 8 条 | `--rules`/`--palette` 坏或缺失 ⇒ **静默回落/审计空转**（5 条静默）；删 `.py` 则硬失败 |
| 依赖 | 3 条 | 全部诚实降级并写 `uncertainty`；**发现**：缺 Pillow 会连带 PDF 一起死 |
| 契约 | 10 条 | 9/9 被 G 门拦下、门号准确；**粗糙点**：类型错时 `check.py` 抛栈而非给门号 |

一句话：**输入域与契约域是硬的，数据/配置类缺失是软的**。本版的对策不是把算法改聪明，
而是加一道运行前闸门 + 把每条静默缺口写进文档，让下一个人不必重跑 32 条注入才知道边界。

## 6. 限制（如实声明）

- 只负责**绘图表达**与**可编辑交付**：不做数值拟合、不判断实验方案科学性、
  不做论文排版与期刊投稿格式适配；
- 材料无结构化实体时走**文本解构**（`extraction=text-heuristic`，朴素串联步骤），
  设备连接需 Agent 复核（D2）；
- 复杂装配图的**局部放大视图**未内置：可在 Inkscape 微调源文件并如实记录 `manual-edit`；
- 装置图为**单层装配**（三桶布局：输入物料 → 装置 → 产物/废料）；深层嵌套需拆画布；
- 图内数值注记：材料给出可标注原值时可放进实体 `props`，当前渲染端不强标数值；
- **故障矩阵覆盖的是枚举样本，不是穷举**：未覆盖磁盘写满、输出目录只读、超长材料、
  并发重复运行、时区/编码差异、容器挂载缺失等；
- 正式案例、白板与评分由平台提供/执行；`examples/` 仅为接口演示（**示例，非正式案例**），
  不冒充正式结果、不含预制答案。

## 7. 失败处理

三道门按顺序过，**任何一门报错都改输入，不要改门**：

```
preflight.py（运行前：输入/结构/资产/依赖）→ main.py（运行中：D1–D12）
→ check.py（运行后：G1–G10）
```

管线异常或输入缺失 → `main.py` 兜底写出 `status=failed` 的 `result.json`（含 error 与
traceback 摘要）；单个预览失败 → 保留已有产物并 `status=partial`（D10）；`svg_verify`
有 error 级违规 → `status=partial` 且 `check.py` 退出码 3（D10）；所有不确定性写入
`result.json.uncertainty`（`scope+issue+action`），修改历史写入 `change_record`。
逐条现象与位点见 `references/failure-modes.md`，实测数据见 `references/FAULT-MATRIX.md`。

## 8. 维护

- 图元/配色：`scripts/model.py` 顶部 `KINDS`/`RELATION_KINDS` + `templates/palette.json`
  + `assets/connection_rules.json` + `references/vocabulary.md`（**四处同步**）；
- 布局规则：`references/figure-blueprint.md` + `scripts/layout.py`；
- 校验规则：`assets/connection_rules.json` + `scripts/svg_verify.py`；
- 契约与自查：`references/OUTPUT_CONTRACT.md` + `scripts/check.py`（G1–G10）；
- 闸门规则：`scripts/preflight.py` 的 `check_inputs/check_structure/check_assets/check_deps`
  四组（加新的静默风险就加一条 finding，别去改 `main.py`）；
- 故障语料：`scripts/fault_inject.py` 的 `_specs()` —— 每条注入一行，加行即加覆盖面；
- 评分覆盖：`references/RUBRIC_MAP.md`（改动后逐维复核落点是否仍成立）；
- 本地实测：`TEST.md`；示例期望产物：`examples/EXPECTED-OUTPUT.md`；
- 打包门：改包后重跑 §9 的两条自检。

## 9. 打包自检（提交前）

```bash
# 形态：扩展名白名单 / 文件数 ≤50 / 单文件 ≤500KB / 合计 ≤2MB / 无符号链接 / 无 pyc
python validate_pkg.py <本包目录>          # 期望 [PASS]

# 残留：包内不应出现本机绝对路径。用「前缀非字母」的字符类写法检索「盘符+斜杠」，
# 这样 URL 里的 https:// 不会被误报，也免得把路径字面量本身写进文档。
grep -rnE '(^|[^A-Za-z])[A-Za-z]:[\\/]' <本包目录>       # 期望无输出

# 演练后确认包内没被污染（本版新增；fault_inject 只改副本，这条是复核它真没写包内）
find <本包目录> -name '__pycache__' -o -name '*.pyc'      # 期望无输出
```
