# 实验装置与技术路线图 Skill · v7（确定性轴）· README

本包是「科研绘图：生成图稿，也保留可编辑来源」这道题的 Skill。
它把装置清单/装配说明/工艺描述/技术路线文本变成**可编辑、可追溯、可复跑**的图稿：
分层 SVG 源文件 + PNG/PDF 预览 + `evidence.json`（证据链）+ `result.json`（含 `output_contract` 全字段）。

**v7 这一版的轴是「确定性与字节级可复现」**：新增 `scripts/determinism.py` 与
`references/DETERMINISM.md`，把"复跑出同一张图"做成可复核的字节证据。

## 1. 依赖与安装

| 项 | 要求 | 说明 |
|-|-|-|
| Python | 3.10+（实测 3.13.9） | 只用标准库即可跑主流程 |
| Pillow | 可选 | PNG 预览；缺则 `figure.png` 不产出并写入 `uncertainty` |
| reportlab | 可选（**在导入期依赖 Pillow**） | PDF 预览；缺则 `figure.pdf` 不产出 |
| 中文字体 | 可选 | 缺失时 `result.json.fonts` 记 `found=false`，SVG/PDF 不受影响 |

安装：把本目录放到技能根（平台为 `/skills/weekly-skill`），无需 `pip install`；
可选依赖按需 `pip install Pillow reportlab`。**没有构建步骤，没有编译产物。**

## 2. 适用范围与已知限制

**适用**：装置结构（部件/接口/装配）、步骤顺序（工艺描述→编号流程图）、材料流向
（分流/合流/回流/废料出口）、技术路线（阶段与里程碑）四类图；已有一张图要改（`--merge`）。

**不适用/不承担**：数据分析与数值拟合；实验方案本身的科学合理性判断；论文排版与期刊格式适配。

**限制（如实列出）**：

1. 布局是**确定性启发式**（阶段分列 / 装置三桶 / 正交连线），不追求最优排版；
   实体数 > 24 时拥挤度未评估。
2. 自由文本输入走**文本解构兜底**，实体/关系保留率会下降（同系列实测：实体保留率
   0.200–0.667、关系保留率 0.000–0.357）；此时 `extraction=text-heuristic`。
3. 预览件（PNG/PDF）需要可选依赖；缺失时 `status=partial`、`check.py` 的 G4 会报错（退出码 3）。
4. **确定性结论的边界**：跨操作系统、跨 Pillow/reportlab 版本的字节级一致**未实测**
   （见 `references/DETERMINISM.md` §7）。

## 3. 快速开始

```bash
SKILL_DIR=/skills/weekly-skill          # 或本地解包目录

# ① 主流程：一个示例案例
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out /tmp/out
# ② 契约门
python "$SKILL_DIR/scripts/check.py" /tmp/out/demo-biotech-route-01/result.json
# ③ ★ 本包的轴：确定性自证
python "$SKILL_DIR/scripts/determinism.py" --json /tmp/determinism_report.json
```

## 4. 文件清单（49 个文件；上限 50）

```
SKILL.md  README.md  TEST.md  GITHUB_URL.txt
scripts/   main.py  gain_evidence.py  model.py  layout.py  render_svg.py  export_preview.py
           svg_verify.py  check.py  fonts.py  preflight.py  fault_inject.py  case_set_run.py
           decision_probe.py  gain_probe.py  bare_baseline.py  determinism.py ★
assets/    connection_rules.json
templates/ palette.json  component-connection-checklist.md  entity-relation-checklist.csv
references/ OUTPUT_CONTRACT.md  RUBRIC_MAP.md  failure-modes.md  vocabulary.md
           figure-blueprint.md  GAIN-PROTOCOL.md（含原 MECHANISM.md 全文）
           FAULT-MATRIX.md（含原 CASE-SET.md 全文）  case-set.json  comparison-data.json
           DETERMINISM.md ★
examples/  case.json  task.md  README.md  EXPECTED-OUTPUT.md  apparatus_spec.example.json
           route_spec.example.json  route_spec.mutation.example.json
           cases/dtms-stage-route-01/{case.json,task.md}
           cases/mbr-wastewater-flow-01/{case.json,task.md}
           output/demo-apparatus-001/{result.json,artifacts.json}
           output/demo-biotech-route-01/{result.json,artifacts.json}
```

> **两处合并（为守住 ≤50 文件硬门，内容逐字保留）**：
> `references/MECHANISM.md` → 并入 `references/GAIN-PROTOCOL.md` 尾部；
> `references/CASE-SET.md` → 并入 `references/FAULT-MATRIX.md` 尾部。
> 每处并入都在宿主文件里写了「合并说明 + 路径更正」。脚本里的旧 docstring 路径指向宿主文件附录。

## 5. 本次（v7）实测摘要

| 项 | 实测 |
|-|-|
| 主流程 smoke | 退出码 **0**、`status=success`、`check_ok=true`、G1–G10 全 true、`result.json` 顶层键 **18**、产物 **7** 件 |
| 确定性探针（8 次运行：raw 4 + stabilized 4） | raw 逐字节一致 **5/7**；stabilized **7/7**；未解释漂移 **0**；`verdict=pass` |
| 漂移源（全部已声明） | `result.json` 的 `change_record[].time`、`execution.out_dir`；`figure.pdf` 的 `/CreationDate` `/ModDate` `/ID` |
| 既有回归（脚本逐字节未改） | 题集跑批 `cases=4 passed=4 failed=0`；故障注入 `injections=32 exit_mismatch=0 preflight_missed=0`；决策探针 `total=20 on_table=20 deviations=[]` |

逐条命令与输出见 `TEST.md`；确定性逐字段说明见 `references/DETERMINISM.md`。

## 6. 维护

- **新增非确定性字段必须先声明再改代码**（v7 的 D13）：写进 `references/DETERMINISM.md`
  的声明清单，否则确定性探针会以 `unexplained>0` 报 `attention`（退出码 3）。
- **改动 `scripts/*.py` 后**：跑 `determinism.py` 复核确定性是否被破坏；
  跑 `fault_inject.py` 与 `decision_probe.py` 复核失败分支是否仍与 `failure-modes.md` 一致。
- **平台硬门**：只允许 `.md/.py/.json/.txt/.csv/.yaml/.yml`；≤50 文件；单文件 ≤500 KB；
  合计 ≤2 MB；无符号链接；无 `__pycache__`。加文件前先看 §4 的清单与合并说明。
- **既有合并（非本轮）**：`references/DECISION-CASES.md` 的内容早已并入
  `references/failure-modes.md` 附录 C（见该文件头部）；`decision_probe.py` 的 docstring 旧路径
  即指那里，20 条决策用例正是对那张表跑的。
- **已知既有脚本缺陷（未修）**：`scripts/preflight.py` 在 **GBK 控制台**直接运行会在打印
  ✅ 时抛 `UnicodeEncodeError`（它没像 `main.py` 那样 `reconfigure(encoding="utf-8")`），
  导致 `--json` 报告来不及落盘。规避：`PYTHONIOENCODING=utf-8 python scripts/preflight.py …`
  （实测退出码 0、`ok=true`）。
