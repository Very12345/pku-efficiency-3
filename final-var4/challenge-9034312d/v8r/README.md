# 实验装置与技术路线图 Skill · v8（契约矩阵轴）· README

本包是「科研绘图：生成图稿，也保留可编辑来源」这道题的 Skill。
它把装置清单/装配说明/工艺描述/技术路线文本变成**可编辑、可追溯、可复跑**的图稿：
分层 SVG 源文件 + PNG/PDF 预览 + `evidence.json`（证据链）+ `result.json`（含 `output_contract` 全字段）。

**v8 这一版的轴是「契约四形态 × 边界值矩阵」**：新增 `scripts/contract_matrix.py` 与
`references/CONTRACT-MATRIX.md`，把"契约声明了什么"与"机器门实际拦住了什么"做成 164 行可跑差异矩阵。

## 1. 依赖与安装

| 项 | 要求 | 说明 |
|-|-|-|
| Python | 3.10+（实测 3.13.9） | 只用标准库即可跑主流程 |
| Pillow | 可选 | PNG 预览；缺则 `figure.png` 不产出并写入 `uncertainty` |
| reportlab | 可选（**在导入期依赖 Pillow**） | PDF 预览；缺则 `figure.pdf` 不产出 |
| 中文字体 | 可选 | 缺失时 `result.json.fonts` 记 `found=false` |

安装：把本目录放到技能根（平台为 `/skills/weekly-skill`），无需 `pip install`。
**没有构建步骤，没有编译产物。**

## 2. 适用范围与已知限制

**适用**：装置结构、步骤顺序、材料流向、技术路线四类图；已有一张图要改（`--merge`）。

**不适用/不承担**：数据分析与数值拟合；实验方案本身的科学合理性判断；论文排版与期刊格式适配。

**限制（如实列出）**：

1. **契约面不完整**（本轴实测出的最重要一条）：`references/OUTPUT_CONTRACT.md` 声明 18 个顶层字段，
   而 `scripts/check.py` 的 `required_fields` 只覆盖 **9** 个；另外 9 个
   （`workorder` `extraction` `entities` `relations` `evidence` `verify` `canvas` `fonts` `execution`）
   **没有存在性检查**。含义：**不能把 `check.py` 退出码当作契约合规的充分证据**。
2. **10 条门面内缺陷**已逐条测出并记录（见 `references/CONTRACT-MATRIX.md` §6）：
   结构段非列表时 `status` 仍可能是 `success`；`result.json.verify.ok` 与 `verify_report.json.ok`
   之间没有一致性校验；`entities=[]` 且 `data_mapping=[]` 时 G5 会"空对空"通过。
   **本轮未改脚本**（改判据会动 G9/G10 语义与退出码，规范禁止），只做了测量、归类、修法建议与回归断言。
3. 自由文本输入走文本解构兜底，实体/关系保留率会下降；此时 `extraction=text-heuristic`。
4. 预览件需要可选依赖；缺失时 `status=partial`、`check.py` 的 G4 报错（退出码 3）。

## 3. 快速开始

```bash
SKILL_DIR=/skills/weekly-skill          # 或本地解包目录

# ① 主流程
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out /tmp/out
# ② 契约门
python "$SKILL_DIR/scripts/check.py" /tmp/out/demo-biotech-route-01/result.json
# ③ ★ 本包的轴：契约矩阵（默认严格模式：有门面内缺陷 ⇒ 退出码 1）
python "$SKILL_DIR/scripts/contract_matrix.py" --json /tmp/cm.json
# ④ ★ 回归用法：断言"缺陷数没变" ⇒ 退出码 0
python "$SKILL_DIR/scripts/contract_matrix.py" --expect-defects 10
```

## 4. 文件清单（49 个文件；上限 50）

```
SKILL.md  README.md  TEST.md  GITHUB_URL.txt
scripts/   main.py  gain_evidence.py  model.py  layout.py  render_svg.py  export_preview.py
           svg_verify.py  check.py  fonts.py  preflight.py  fault_inject.py  case_set_run.py
           decision_probe.py  gain_probe.py  bare_baseline.py  contract_matrix.py ★
assets/    connection_rules.json
templates/ palette.json  component-connection-checklist.md  entity-relation-checklist.csv
references/ OUTPUT_CONTRACT.md  RUBRIC_MAP.md  failure-modes.md（含原 FAULT-MATRIX.md 全文）
           vocabulary.md  figure-blueprint.md  GAIN-PROTOCOL.md（含原 MECHANISM.md 全文）
           CASE-SET.md  case-set.json  comparison-data.json  CONTRACT-MATRIX.md ★
examples/  case.json  task.md  README.md  EXPECTED-OUTPUT.md  apparatus_spec.example.json
           route_spec.example.json  route_spec.mutation.example.json
           cases/dtms-stage-route-01/{case.json,task.md}
           cases/mbr-wastewater-flow-01/{case.json,task.md}
           output/demo-apparatus-001/{result.json,artifacts.json}
           output/demo-biotech-route-01/{result.json,artifacts.json}
```

> **两处合并（为守住 ≤50 文件硬门，内容逐字保留）**：
> `references/MECHANISM.md` → 并入 `references/GAIN-PROTOCOL.md` 尾部；
> `references/FAULT-MATRIX.md` → 并入 `references/failure-modes.md` 尾部。
> 每处并入都在宿主文件里写了「合并说明 + 路径更正」。脚本里的旧 docstring 路径指向宿主文件附录。

## 5. 本次（v8）实测摘要

| 项 | 实测 |
|-|-|
| 主流程 smoke | 退出码 **0**、`status=success`、`check_ok=true`、G1–G10 全 true、`result.json` 顶层键 **18**、产物 **7** 件 |
| 契约面自校验 | `contract_doc_matches=true`（文档 18 字段 ⇄ 脚本 18 字段）；`check.py` 只检查 **9** 个 ⇒ **9 个未覆盖** |
| 矩阵规模 | **164 行**（输入 22 / 输出 106 / 六形态 36），违约 **141** 行，`setup_errors=0`，耗时约 **24 s** |
| 静默通过 | **96** 条（= 门面内缺陷 10 + 仅报 issue 6 + 未覆盖 86） |
| 门面内缺陷 | **10** 条（输入 6 + 输出 4），逐条在 `CONTRACT-MATRIX.md` §6 |
| 严格模式退出码 | **1**（预期；`defects[]` 非空） |
| 回归模式 | `--expect-defects 10` ⇒ `verdict=pass`、退出码 **0** |
| 既有回归（脚本逐字节未改） | 题集跑批 `cases=4 passed=4 failed=0`；故障注入 `injections=32 exit_mismatch=0`；决策探针 `total=20 on_table=20 deviations=[]` |

逐条命令与输出见 `TEST.md`；矩阵逐行表见 `references/CONTRACT-MATRIX.md`。

## 6. 维护

- **改契约就要同步矩阵**（v8 的 D14）：`references/OUTPUT_CONTRACT.md` 每新增/改名一个字段，
  都要同步 `references/CONTRACT-MATRIX.md` §1 并说明"机器门是否检查它"。
- **改 `check.py` 的判据之后**：跑 `contract_matrix.py --expect-defects N`（N 改为新的缺陷数），
  并把 §6 的表与 §8 的修法表一起更新。
- **平台硬门**：只允许 `.md/.py/.json/.txt/.csv/.yaml/.yml`；≤50 文件；单文件 ≤500 KB；
  合计 ≤2 MB；无符号链接；无 `__pycache__`。加文件前先看 §4 的清单与合并说明。
- **既有合并（非本轮）**：`references/DECISION-CASES.md` 的内容早已并入
  `references/failure-modes.md` 附录 C（见该文件头部）；`decision_probe.py` 的 docstring 旧路径即指那里。
- **已知既有脚本缺陷（未修）**：`scripts/preflight.py` 在 **GBK 控制台**直接运行会在打印 ✅ 时抛
  `UnicodeEncodeError`，`--json` 报告来不及落盘。规避：`PYTHONIOENCODING=utf-8`（实测退出码 0、`ok=true`）。
