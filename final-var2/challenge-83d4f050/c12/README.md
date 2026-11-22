# README.md — 生物机制图与通路图 Skill（增益可验证版）

> 题目：玻尔产品周赛·北大专区·学术效率·第三期 — `challenge-83d4f050`（生物机制与通路图，组：figures）。
> 平台固定 3 个案例；参赛者只提交 Skill 与运行必需的**文本**资源。

## 1. 这个 Skill 是什么

把机制/通路材料转成**可逐条核验、且"好在哪"可被量出来**的机制图。

两件事并重：

| 面向 | 做法 | 产物 |
|---|---|---|
| 出图 | 声明式机制规格 → 区室约束确定性布局 → 可编辑分层 SVG + PNG/PDF → 拓扑与图例/编码审计 → 契约化 `result.json` | 7 件产物（见 §4） |
| 证明增益 | **公平对照协议**（同输入/同工具/同预算）+ **独立度量器**（不依赖本包模块）+ 实测记录 | `references/GAIN-PROTOCOL.md`、`scripts/gain_probe.py` |

一句话：**流程里的每一步都产出能被外部脚本读取的证据**（分层、`data-*` 溯源、语义标签、
图例声明、契约信封、审计产物），因此"更好"不需要靠自述——`gain_probe.py` 用同一把尺子
同时量基础形态与加载 Skill 的产物，两侧读数直接可比。

## 2. 资源形态

包内**只有文本**：`.md .py .json .txt .csv .yaml .yml` 七种扩展名；无二进制、无符号链接、
无 `__pycache__`。契约原文：`at most 50 UTF-8 text files, 500KB each and 2MB total, no symlinks`。
`diagram.svg` / `diagram.png` / `diagram.pdf` 全部由 `scripts/` 在 `--out` 目录**运行时生成**。

## 3. 快速开始

```bash
export SKILL_DIR=/skills/weekly-skill            # 容器路径；本机指向含 SKILL.md 的那一层
python3 "$SKILL_DIR/scripts/main.py" --help      # 自检

# 主路径（已核验规格）→ 期望 exit 0、7 件产物
python3 "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
    --model-file "$SKILL_DIR/examples/model.example.json" --out /app/output

# 两条独立审计 → 期望 exit 0
python3 "$SKILL_DIR/scripts/check_contract.py" --result /app/output/result.json \
    --case "$SKILL_DIR/examples/case.json"
python3 "$SKILL_DIR/scripts/validate_figure.py" --out /app/output

# 量一次增益（条件 A 复现器 vs 本 Skill）
python3 "$SKILL_DIR/scripts/baseline_emulator.py" \
    --material "$SKILL_DIR/examples/materials/example_material.md" --out /tmp/condA
python3 "$SKILL_DIR/scripts/gain_probe.py" --compare /tmp/condA /app/output \
    --material "$SKILL_DIR/examples/materials/example_material.md" \
    --case "$SKILL_DIR/examples/case.json"
```

平台运行：输入 `/input/case.json` + `/input/task.md`（+ 材料），输出 `/app/output`。

**退出码语义**：`0 = success`、`2 = partial（有降级但有产物）`、`3 = failed（阻断）`；
与 `status`、`gates` 三者必须自洽（规则 P9）。

**CLI 参数**（与 `scripts/main.py` argparse 逐字一致）：`--case --task --out --materials-dir
（可重复） --model-file --formats --dpi --verbose`；7 种组合的实测退出码见 `TEST.md` §3。

## 4. 产出（`--out` 目录，全部运行时生成）

| 文件 | 作用 | 缺省是否必需 |
|---|---|---|
| `result.json` | **唯一评分产物**：信封 19 键 + `output_contract` 全部字段（无 null） | 必需 |
| `diagram.svg` | **可编辑源**：7 个 `layer-*` 组 + `data-id/data-type/data-source` | 必需（缺则 failed） |
| `diagram.png` / `diagram.pdf` | 预览与矢量导出（同一布局引擎） | 可选（缺则 partial） |
| `model.json` | 机制规格（规范化实体/边/图例） | 必需 |
| `topology.json` / `legend_audit.json` | 拓扑审计（P01–P08）与图例/编码审计（L/E 系列） | 必需 |

## 5. 目录结构

```
SKILL.md                    增益主张 / 指标 / 流程 / 决策点 P1–P10 / 实测摘要
README.md                   本文件
TEST.md                     自测 + 2026-11-22 实测（CLI 矩阵、对照读数、降级、确定性）
worklog.md                  构建记录（本版新增了什么、为什么、验收）
GITHUB_URL.txt              公开作品链接（单行）
references/
  GAIN-PROTOCOL.md          ★本版核心：公平对照协议 + 8 项指标定义 + 实测记录 + 局限
  OUTPUT_CONTRACT.md        字段契约 + 四形态 + G1–G8 + §10 契约合规的可测判定
  RUBRIC_MAP.md             五维评分落点（使用增益按指标逐条落点）
  failure-modes.md          F01–F22，每条带"可测足迹"
  mechanism-spec.md         规格结构、命名与区室规范
  legend-encoding.md        箭头语义、数据编码、调色板
scripts/                    13 个脚本（原 11 个 + gain_probe + baseline_emulator）
assets/  templates/  examples/
```

## 6. 依赖与环境

- **运行必需**：Python 3.8+，**仅标准库**（SVG、规格、审计、契约、度量器都无第三方依赖）。
- **可选**：`matplotlib`（PNG/PDF）、`Pillow`（PNG 尺寸校验）。缺失即降级为仅 SVG
  （`partial` + exit 2 + A7 指标掉到 0），**不伪造预览**。
- **字体**：SVG 用 CSS 字体栈（包内不含字体文件）；PNG/PDF 由 matplotlib 选系统字体，缺中文字体时告警。
- **本机路径**：脚本 `__file__` 自定位；包内文本**无任何本机绝对路径**（实测 0 命中，无豁免项）。
  字体由 matplotlib 的字体管理器按**字体族名**解析，脚本中不硬编码系统字体目录。
- 实测环境：Python 3.13.9 + matplotlib + Pillow（2026-11-22）。

## 7. 这套增益口径怎么用（也适用于别的绘图 Skill）

1. 先定义**与实现无关**的指标（本包：分层 / 溯源 / 语义标签 / 图例声明 / 契约 / 审计 / 导出）；
2. 度量器**不 import 被测包**，缺项计 0；
3. 两侧**同法计算**，把基线做成可复现的复现器（本包：`baseline_emulator.py`）；
4. 把"不算差异点的项"也写出来（本包：材料实体名覆盖率两侧同为 1.0）；
5. 把测量命令、环境、时间写进协议，任何人可复算。

## 8. 适用范围与限制

- 适用：机制图/通路图/信号级联/调控网络/流程图/图表编辑，含"改一个箭头""按数据上色""补图例"。
- 不适用：数值统计与统计结论、实验方案设计、论文写作与版式美化（相邻课题负责）。
- 自动抽取只处理结构化语句；散文/PDF 走手工规格（CP2 的手工路径），"准确率优先于全自动"。
- **度量器量的是结构性与可核验性，不评判美观度**；真实对照由平台运行，本包只保证判据可复算。
- 图件不在包内；PDF 与 `result.json` 含时间戳，不作确定性承诺（确定性 = SVG/PNG/model/topology/legend_audit）。

## 9. 维护与更新

- 改颜色 → `assets/palettes.json`；改契约/门 → 契约文件 + `check_contract.py` + `result_writer.py` 三处同步；
- **改指标口径 → 必须同时改 `references/GAIN-PROTOCOL.md` §2 与 `scripts/gain_probe.py`**，
  并在协议里记版本（防止"换尺子再说赢了"）；
- 改校验规则 → `topology.py` / `legend_audit.py` / `validate_figure.py`，同步 `mechanism-spec.md`；
- 改完跑 `TEST.md` 全套 → 更新记录 → 在 `worklog.md` 追加一条带时间的条目；
- **禁止**向包内添加二进制或 `__pycache__`。
