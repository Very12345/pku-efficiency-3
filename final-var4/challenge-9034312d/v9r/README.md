# 实验装置与技术路线图 Skill · v9（降级链轴）· README

本包是「科研绘图：生成图稿，也保留可编辑来源」这道题的 Skill。
它把装置清单/装配说明/工艺描述/技术路线文本变成**可编辑、可追溯、可复跑**的图稿：
分层 SVG 源文件 + PNG/PDF 预览 + `evidence.json`（证据链）+ `result.json`（含 `output_contract` 全字段）。

**v9 这一版的轴是「缺依赖降级链实测」**：新增 `scripts/degrade_probe.py` 与
`references/DEGRADE-MATRIX.md`，用受控导入拦截逐个抽走依赖，实测每个降级档位还剩什么、
`status` 变什么、还写不写 `result.json`、退出码是多少，并给出**分档最小可用环境**。

## 1. 依赖与安装（实测出来的依赖面）

| 档位 | 需要什么 | 能产出什么（实测） | `status` | 退出码 |
|-|-|-|-|-|
| ① 纯标准库 | Python 3.10+（实测 3.13.9） | **5 件**：`figure.svg` + `evidence.json` + `layout.json` + `verify_report.json` + `result.json` | `partial` | 3 |
| ② + Pillow | `pip install Pillow` | **6 件**（+ `figure.png`） | `success` | 0 |
| ③ + reportlab | `pip install reportlab`（**且必须有 Pillow**） | **7 件**（+ `figure.pdf`） | `success` | 0 |

**明确不需要**（抽走零差异）：`yaml`、`numpy`、`matplotlib`、`python-pptx`、LibreOffice CLI。
**怎么都救不了**（缺了连 `result.json` 都没有）：`xml`（`xml.etree.ElementTree`）、`hashlib`。

> ★ **重要实测事实**：`reportlab` 在**导入期**就 `from PIL import Image`（`reportlab/lib/utils.py:15`），
> 所以 **Pillow 是唯一的"硬"依赖** —— 它一缺，PNG 与 PDF **一起**没有（不是"PNG 靠 PIL、
> PDF 靠 reportlab"的并列关系）。安装顺序：**Pillow 在前**。

安装：把本目录放到技能根（平台为 `/skills/weekly-skill`）。
**没有构建步骤，没有编译产物。**

## 2. 适用范围与已知限制

**适用**：装置结构、步骤顺序、材料流向、技术路线四类图；已有一张图要改（`--merge`）。

**不适用/不承担**：数据分析与数值拟合；实验方案本身的科学合理性判断；论文排版与期刊格式适配。

**限制（如实列出）**：

1. 纯标准库环境下**没有预览件**（`exports=[]`），`check.py` 的 G4 会报错、`main.py` 返回 **3** ——
   这是契约门在诚实报错，不是失败被掩盖。要交 PNG/PDF 预览就得装 ②/③ 档。
2. 自由文本输入走文本解构兜底，实体/关系保留率会下降；此时 `extraction=text-heuristic`。
3. `reportlab` 的 PDF 输出含生成时间与文档 ID；做字节级对拍时需 `RL_INVARIANT=1`
   （同系列 v7 包的确定性轴已实测这一点）。
4. 本轮降级矩阵只在 **Windows 11 + CPython 3.13.9** 上跑；拦截机制是纯 Python，预期可移植但**未实测**。

## 3. 快速开始

```bash
SKILL_DIR=/skills/weekly-skill          # 或本地解包目录

# ① 主流程
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out /tmp/out
# ② 契约门
python "$SKILL_DIR/scripts/check.py" /tmp/out/demo-biotech-route-01/result.json
# ③ ★ 本包的轴：降级链（13 条件，约 3.4 秒）
python "$SKILL_DIR/scripts/degrade_probe.py" --json /tmp/degrade_report.json
# ④ 只关心真实依赖
python "$SKILL_DIR/scripts/degrade_probe.py" --only c01-no-PIL --only c02-no-reportlab
```

## 4. 文件清单（49 个文件；上限 50）

```
SKILL.md  README.md  TEST.md  GITHUB_URL.txt
scripts/   main.py  gain_evidence.py  model.py  layout.py  render_svg.py  export_preview.py
           svg_verify.py  check.py  fonts.py  preflight.py  fault_inject.py  case_set_run.py
           decision_probe.py  gain_probe.py  bare_baseline.py  degrade_probe.py ★
assets/    connection_rules.json
templates/ palette.json  component-connection-checklist.md  entity-relation-checklist.csv
references/ OUTPUT_CONTRACT.md  RUBRIC_MAP.md  failure-modes.md（含原 CASE-SET.md 全文）
           vocabulary.md  figure-blueprint.md  GAIN-PROTOCOL.md（含原 MECHANISM.md 全文）
           FAULT-MATRIX.md  case-set.json  comparison-data.json  DEGRADE-MATRIX.md ★
examples/  case.json  task.md  README.md  EXPECTED-OUTPUT.md  apparatus_spec.example.json
           route_spec.example.json  route_spec.mutation.example.json
           cases/dtms-stage-route-01/{case.json,task.md}
           cases/mbr-wastewater-flow-01/{case.json,task.md}
           output/demo-apparatus-001/{result.json,artifacts.json}
           output/demo-biotech-route-01/{result.json,artifacts.json}
```

> **两处合并（为守住 ≤50 文件硬门，内容逐字保留）**：
> `references/MECHANISM.md` → 并入 `references/GAIN-PROTOCOL.md` 尾部；
> `references/CASE-SET.md` → 并入 `references/failure-modes.md` 尾部。
> 每处并入都在宿主文件里写了「合并说明 + 路径更正」。脚本里的旧 docstring 路径指向宿主文件附录。

## 5. 本次（v9）实测摘要

| 项 | 实测 |
|-|-|
| 主流程 smoke | 退出码 **0**、`status=success`、`check_ok=true`、G1–G10 全 true、`result.json` 顶层键 **18**、产物 **7** 件 |
| 降级矩阵 | **13 个条件**，总耗时 **3.37 s**（单条件 0.09–0.40 s），`verdict=pass`、`deviations=[]` |
| 真实依赖 | 只有 **2** 个：Pillow、reportlab（后者依赖前者） |
| 规格点名依赖 | `yaml` / `numpy` / `matplotlib` / `python-pptx` / LibreOffice CLI **全部零差异**（7 件产物、`success`、退出码 0） |
| 缺 Pillow | 退出码 **3**、`status=partial`、**5 件**（PNG 与 PDF 一起丢） |
| 缺 reportlab | 退出码 **0**、`status=partial`、**6 件**（只丢 PDF） |
| 缺 xml / hashlib | 退出码 **1**、**0 件**（连 `result.json` 都没有） |
| 既有回归（脚本逐字节未改） | 题集跑批 `cases=4 passed=4 failed=0`；故障注入 `injections=32 exit_mismatch=0`；决策探针 `total=20 on_table=20 deviations=[]` |

逐条命令与输出见 `TEST.md`；逐项矩阵见 `references/DEGRADE-MATRIX.md`。

## 6. 维护

- **改依赖就要同步矩阵**（v9 的 D15）：任何会让产物件数/`status`/退出码变化的依赖变动，
  必须同步 `references/DEGRADE-MATRIX.md` §6 的「最小可用环境」表；
  `degrade_probe.py` 的 `deviations[]` 是这条口径的可执行闸门（`--expect-deviations 0`）。
- **部署到新环境时先跑** `degrade_probe.py --list` 看条件表，再按 §1 的档位决定装哪些包。
- **平台硬门**：只允许 `.md/.py/.json/.txt/.csv/.yaml/.yml`；≤50 文件；单文件 ≤500 KB；
  合计 ≤2 MB；无符号链接；无 `__pycache__`。加文件前先看 §4 的清单与合并说明。
- **既有合并（非本轮）**：`references/DECISION-CASES.md` 的内容早已并入
  `references/failure-modes.md` 附录 C（见该文件头部）；`decision_probe.py` 的 docstring 旧路径即指那里。
- **已知既有脚本缺陷（未修）**：`scripts/preflight.py` 在 GBK 控制台打印 ✅ 抛
  `UnicodeEncodeError`，`--json` 报告来不及落盘。规避：`PYTHONIOENCODING=utf-8`（实测退出码 0、`ok=true`）。
- **已知口径更正**：`references/failure-modes.md` 里"无 Pillow ⇒ PNG 降级"的说法，
  按本轴实测应理解为"**PNG 与 PDF 一起降级**"（reportlab 依赖 PIL）；决策规则 D9/D10 本身不变。
