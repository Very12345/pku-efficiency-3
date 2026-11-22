# README.md — 生物机制图与通路图 Skill（合规文本包）

> 题目：玻尔产品周赛·北大专区·学术效率·第三期 — `challenge-83d4f050`
> （生物机制与通路图，组：figures）。
> 本题面固定 3 个案例由平台提供，参赛者只提交 Skill 与运行必需的**文本**资源。

## 1. 这是什么

一个可被 Agent 调用的 Skill，把科研机制/通路材料转成**可逐条质疑的机制图**：
实体（基因/蛋白/复合物/RNA/小分子/区室）与相互作用（激活/抑制/结合/修饰/转运）
全部 source-bound，图例 / 数据编码与图面自洽，交付可编辑分层 SVG 源 + PNG/PDF 预览
+ 审计产物 + 契约化 `result.json`。

**资源形态（本包最重要的约定）**：包内**只有文本文件**，扩展名限定
`.md .py .json .txt .csv .yaml .yml` 七种，无二进制、无符号链接、无 `__pycache__`。
`diagram.svg` / `diagram.png` / `diagram.pdf` 全部由 `scripts/` 在**运行时生成**：

| 产物 | 生成者 | 缺失时 |
|-|-|-|
| `diagram.svg`（可编辑源，7 层 + `data-*` 溯源） | `scripts/pathway_svg.py`（纯标准库） | 不适用：SVG 必须产出，否则 `failed` |
| `diagram.png` | `scripts/mpl_backend.py`（matplotlib，可选 Pillow 校验尺寸） | 降级：只交付 SVG，`status=partial` 并写入 `uncertainty`/`export_checks` |
| `diagram.pdf` | 同上 | 同上 |
| `model.json` / `topology.json` / `legend_audit.json` / `result.json` | `scripts/main.py` 流水线 | 不适用（流程自身产物） |

## 2. 快速开始（自定位，cwd 不是技能根也能跑）

```bash
# 技能根目录 = 含 SKILL.md 的那一层
export SKILL_DIR=/skills/weekly-skill          # 平台容器安装路径
# export SKILL_DIR=/path/to/challenge-83d4f050  # 本机解压后的包根目录

# 1) 已核验规格路径（人工核验后正式出图；推荐）
python3 "$SKILL_DIR/scripts/main.py" \
    --case "$SKILL_DIR/examples/case.json" \
    --model-file "$SKILL_DIR/examples/model.example.json" \
    --out /app/output

# 2) 自动草稿路径（产出 partial，提示 Agent 逐条复核）
python3 "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out /app/output-draft

# 3) 独立复查（两个 CLI 各自有明确退出码）
python3 "$SKILL_DIR/scripts/check_contract.py" --result /app/output/result.json \
    --case "$SKILL_DIR/examples/case.json"      # exit 0 = 契约通过
python3 "$SKILL_DIR/scripts/validate_figure.py" --out /app/output   # exit 0 = 全检查通过
```

平台运行时：输入是 `/input/case.json` 与 `/input/task.md`（+ 材料目录），输出写 `/app/output`：

```bash
python3 "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output --verbose
```

相对路径 `--case examples/case.json` 也可用（main.py 先按 cwd 解析，找不到再回退技能根）；
`--model-file` / `--materials-dir` 请写完整路径。

## 3. 输入与输出

**输入**：`case.json`（`case_id`/`title`/`task`/`materials`/`render`/`output_contract`）
＋ `task.md` ＋ 材料文件（文本、Markdown、表格；PDF 由 Agent 抽文或用 `--model-file`
手工建规格）。

**输出**（`--out` 目录）：`result.json`（契约，见 `references/OUTPUT_CONTRACT.md`）、
`diagram.svg`（7 层可编辑源，`data-id`/`data-type`/`data-source`）、
`diagram.png`、`diagram.pdf`（同一布局引擎渲染，与 SVG 一致）、`model.json`（机制规格）、
`topology.json` / `legend_audit.json`（审计产物）。

## 4. 目录结构

```
SKILL.md                 入口：资源形态 / 用途 / 输入输出 / CP1–CP5 检查点 / D1–D12 决策规则 / 自查
README.md                本文件：依赖、安装、适用范围、限制、维护
TEST.md                  自测方法、期望输出与实测记录（含本机 sha256 与确定性双跑）
COMPARE.md               与"不加载 Skill 的基础 Agent"的同输入对照方案与可复算判据
worklog.md               构建与合规重打包记录（改了什么、为什么、验证结果）
GITHUB_URL.txt           公开作品链接（单行）
scripts/                 12 个脚本：
                           build   = extract / model / main
                           render  = layout / pathway_svg / mpl_backend
                           verify  = topology / legend_audit / validate_figure /
                                     check_contract / result_writer
                           drill   = fault_inject（失败注入与恢复演练，见 §7）
references/              OUTPUT_CONTRACT.md / RUBRIC_MAP.md / mechanism-spec.md /
                         legend-encoding.md / failure-modes.md /
                         FAULT-MATRIX.md（四形态故障注入实测矩阵）
assets/                  mechanism-spec.schema.json / palettes.json / result.template.json
templates/               relation-checklist-template.md（关系核对清单，CP3 核验载体）
examples/                合成示例案例：case.json / task.md / materials/ /
                         model.example.json / README.md / EXPECTED-OUTPUT.md /
                         output/（示例案例实跑得到的 JSON 产物）
```

## 5. 依赖与环境

- **运行必需**：Python 3.8+，**仅标准库**（可编辑 SVG、机制规格、审计、契约全部无第三方依赖）。
- **可选**：`matplotlib`（渲染 PNG/PDF 预览；缺失时自动降级为仅 SVG 并如实记录）、
  `Pillow`（校验 PNG 尺寸/可打开性；缺失时该检查降级为 warn）。
- 安装（可选依赖）：`pip install matplotlib pillow`。
- 实测环境（`TEST.md` 有原始输出）：Python 3.13 + matplotlib + Pillow；
  纯标准库路径（`--formats svg`）在无 matplotlib 环境下同样可用。
- **字体**：SVG 使用 CSS 标准字体栈，由查看端决定实际字体，无需随包字体文件；
  PNG/PDF 由 matplotlib 选用系统字体，材料含中文而系统缺中文字体时**告警**并写入
  `export_checks`/`uncertainty`（不静默产出乱码图）。包内不含任何 `.ttf/.otf`。
- **无本机路径依赖**：脚本用 `os.path.dirname(__file__)` 自定位；包内文本不含本机盘符
  绝对路径（示例产物中的 provenance 只记相对路径或容器环境路径）。自检方式见 `TEST.md` §13。

## 6. 适用范围与限制

- 适用：机制图 / 通路图 / 信号级联 / 调控网络 / 流程图 / 图表编辑，包括"改一个错误箭头"
  "按数据给节点上色""补图例""按模板重导出"。
- 不适用：数值统计与统计分析结论、实验方案设计、论文写作与版式美化（相邻课题负责）；
  本 Skill 只对图形中的科学内容表达、布局、可编辑性与导出质量负责。
- 自动抽取器只处理结构化语句（表格 / `A | 动词 | B` / `- A 动词 B（证据）`）；
  散文与 PDF 材料依赖 Agent 人工抽取并用 `--model-file` 重跑（CP2b/CP3 强制），
  这是"准确率优先于全自动"的刻意设计。
- 图件不在包内，是运行时产物；包里"看不到图"是设计而非缺失
  （见 `SKILL.md` §0 与 `examples/EXPECTED-OUTPUT.md`）。
- PDF 与 `result.json` 含时间戳，不作为确定性承诺对象；确定性承诺 = SVG / PNG / model /
  topology / legend_audit（同输入双跑逐字节一致）。
- 完整失败模式见 `references/failure-modes.md`；构建与变更见 `worklog.md`。

## 7. 故障演练（`scripts/fault_inject.py`，本版新增）

把技能复制到**包外**目录，逐个"弄坏"一处输入/资产/依赖/契约，跑真实主流程并记录
**退出码 / `status` / `gates` / `uncertainty` / 产物清单**，判定该故障是显式暴露还是被静默吞掉：

```bash
cp -r "$SKILL_DIR" /tmp/fault-skill                       # 绝不在包内跑（会留 __pycache__）
python3 /tmp/fault-skill/scripts/fault_inject.py     --skill /tmp/fault-skill --out /tmp/fault-out          # 24 场景，约 1 分钟
# 退出码 0 = 全部符合期望；1 = 有场景不符（必须看报告）
```

- 四形态：**输入**（case/材料/规格坏）· **模板**（包内资产缺失或损坏）·
  **依赖**（matplotlib/Pillow/格式请求）· **契约**（`output_contract` 四形态与校验 CLI）；
- 参数：`--skill`（默认本脚本所在技能）`--out`（报告目录）`--family`（只跑某形态）
  `--only`（按 id 前缀挑场景）`--json/--md`（报告文件名）`--keep`（保留临时副本）；
- 产物：`fault-report.json`（机器可读）+ `FAULT-MATRIX.generated.md`（同表 Markdown）；
- **实测台账**（含修复前后对比、恢复演练与未覆盖边界）见 `references/FAULT-MATRIX.md`。

> 该演练在本版里**真的发现了 3 处静默失败**（丢边不留痕、调色板回退不留痕、CP1 warn 被丢弃），
> 已用**纯增量**补丁修掉：`model.py` 381→437 行、`main.py` 482→512 行，
> 删除行数为 0、CLI 参数与退出码语义未改（逐条点名见 FAULT-MATRIX.md §4.1）。

## 8. 维护与更新

- 改颜色/线宽：只改 `assets/palettes.json`（全图与图例同步）；
- 改契约/门：`references/OUTPUT_CONTRACT.md` + `scripts/check_contract.py`
  + `scripts/result_writer.py` 三处同步；
- 改校验规则：`scripts/topology.py` / `legend_audit.py` / `validate_figure.py`，
  并更新 `references/mechanism-spec.md` 的校验一览；
- 改完跑 `TEST.md` 全套（本版共 T1–T11/T12/T13，见其目录），更新实测记录，并在 `worklog.md` 追加一条带时间的记录；
- 明令禁止：向包内添加二进制资源（`.png/.pdf/.svg/.pptx/.ttf/...`）或 `__pycache__`——
  图件必须运行时生成，包内只留七种文本扩展名。
