# README.md — 生物机制图与通路图 Skill（决策显性化版）

> 题目：玻尔产品周赛·北大专区·学术效率·第三期 — `challenge-83d4f050`（生物机制与通路图，组：figures）。
> 平台固定 3 个案例，参赛者只提交 Skill 与运行必需的**文本**资源。

## 1. 这个 Skill 解决什么

把科研机制/通路材料转成**可逐条质疑的机制图**：实体（基因/蛋白/复合物/RNA/小分子/区室）与
相互作用（激活/抑制/结合/修饰/转运）全部 source-bound；图例、颜色映射与图面自洽；
交付可编辑分层 SVG 源 + PNG/PDF 预览 + 审计产物 + 契约化 `result.json`。

**本版的定位是"决策显性化"**：三件事在真实运行里最容易出错——**边界情况怎么判**、
**失败了怎么退**、**退到什么程度算诚实**。因此本版把它们写成两张可查的表：

| 表 | 位置 | 内容 |
|---|---|---|
| 决策规则表 | `SKILL.md` §1 | D1–D23，每条三列：**触发信号 / 动作 / 失败时降级（含记录位点）**；分材料、语义、图例、资产依赖、契约状态五组 |
| 失败分支表 | `SKILL.md` §2 + `references/failure-modes.md` | 五类分支（材料异常 / 资产缺失 / 依赖缺失 / 契约四形态 / 状态一致性），F01–F22 与 D 规则一一对应 |

## 2. 资源形态（本包最重要的约定）

包内**只有文本**：`.md .py .json .txt .csv .yaml .yml` 七种扩展名，无二进制、无符号链接、
无 `__pycache__`。图件全部由 `scripts/` 在 `--out` 目录**运行时生成**：

| 产物 | 生成者 | 缺失时 |
|---|---|---|
| `diagram.svg`（可编辑源，7 层 + `data-*` 溯源） | `scripts/pathway_svg.py`（纯标准库） | 不适用：SVG 必须产出，否则 `failed` |
| `diagram.png` | `scripts/mpl_backend.py`（matplotlib；Pillow 可选） | 降级：只交付 SVG，`partial` + exit 2（见 D16/F10） |
| `diagram.pdf` | 同上 | 同上 |
| `model.json` / `topology.json` / `legend_audit.json` / `result.json` | `scripts/main.py` 流水线 | 不适用（流程自身产物） |

## 3. 快速开始（自定位，cwd 不是技能根也能跑）

```bash
export SKILL_DIR=/skills/weekly-skill            # 平台容器安装路径
# export SKILL_DIR=/path/to/challenge-83d4f050   # 本机解压后的包根目录

python3 "$SKILL_DIR/scripts/main.py" --help      # 自检：能打印帮助即路径正确

# 1) 已核验规格（推荐：人工核验后正式出图）
python3 "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
    --model-file "$SKILL_DIR/examples/model.example.json" --out /app/output

# 2) 自动草稿（产出 partial，提示逐条复核）
python3 "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out /app/output-draft

# 3) 独立复查
python3 "$SKILL_DIR/scripts/check_contract.py" --result /app/output/result.json \
    --case "$SKILL_DIR/examples/case.json"     # exit 0 = 契约通过
python3 "$SKILL_DIR/scripts/validate_figure.py" --out /app/output   # exit 0 = 全检查通过
```

平台运行时输入是 `/input/case.json` + `/input/task.md`（+ 材料目录），输出写 `/app/output`：

```bash
python3 "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output --verbose
```

**退出码语义**（决策规则 D22 的判定基准）：`0 = success`、`2 = partial（有降级但有产物）`、
`3 = failed（阻断）`。三者与 `status`、`gates` 必须自洽；不自洽时以退出码为真。

**CLI 参数**（与 `scripts/main.py` 的 argparse 逐字一致）：
`--case`、`--task`、`--out`、`--materials-dir`（可重复）、`--model-file`、`--formats`、`--dpi`、`--verbose`。
7 种组合的实测退出码见 `TEST.md` §3。

## 4. 目录结构

```
SKILL.md                 入口：资源形态 / 决策规则 D1–D23 / 失败分支表 / CP1–CP5 / 自查清单
README.md                本文件：定位、依赖、CLI、限制、维护
TEST.md                  自测方法 + 2026-11-22 实测记录（CLI 矩阵、失败信封、降级、确定性）
COMPARE.md               与"不加载 Skill 的基础 Agent"的同输入对照判据（按 D 规则组织）
worklog.md               构建记录：本版做了什么、为什么、验证结果（含缺陷修复）
GITHUB_URL.txt           公开作品链接（单行）
scripts/                 11 个脚本：build = extract/model/main；render = layout/pathway_svg/mpl_backend；
                         verify = topology/legend_audit/validate_figure/check_contract/result_writer
references/              OUTPUT_CONTRACT.md（§10 状态一致性矩阵）/ RUBRIC_MAP.md /
                         mechanism-spec.md / legend-encoding.md / failure-modes.md（F01–F22）
assets/                  mechanism-spec.schema.json / palettes.json / result.template.json
templates/               relation-checklist-template.md（CP3 人工核验载体，五张表）
examples/                合成示例：case.json / task.md / materials/ / model.example.json /
                         README.md / EXPECTED-OUTPUT.md / output/（实跑 JSON 产物）
```

## 5. 依赖与环境

- **运行必需**：Python 3.8+，**仅标准库**（可编辑 SVG、机制规格、审计、契约均无第三方依赖）。
- **可选**：`matplotlib`（PNG/PDF 预览）、`Pillow`（PNG 尺寸校验）。
  缺失时的行为由 **D16/F10–F11** 规定：只交付 SVG、`partial`、exit 2、如实记录，**不假装有预览**。
- **字体**：SVG 用 CSS 标准字体栈（无需随包字体文件）；PNG/PDF 由 matplotlib 选系统字体，
  缺中文字体时告警并写入 `export_checks`（D17/F12）。包内不含任何 `.ttf/.otf`。
- **本机路径**：脚本用 `os.path.dirname(__file__)` 自定位；包内文本**不含任何本机绝对路径**
  （实测扫描：0 命中，无需豁免项）。PNG/PDF 的字体由 matplotlib 的字体管理器按**字体族名**
  解析（`fm.findfont`），脚本里不硬编码任何系统字体目录，因此跨平台迁移时不需要改路径。
- **实测环境**：Python 3.13.9 + matplotlib + Pillow（2026-11-22，见 `TEST.md` §2）。

## 6. 决策规则速览（完整版见 `SKILL.md` §1）

| 组 | 规则 | 一句话 |
|---|---|---|
| 材料与实体 | D1–D7 | 方向缺失不臆造；同名拆实体；多区室拆实体；数值矛盾以原文为准；PDF 走人工；只有实体无关系照交付并说明；材料三级查找 |
| 语义与拓扑 | D8–D11 | 枚举外动词就近归类并留痕；逆流边标反馈或给理由；重复边合并保来源；自环必须写机制依据 |
| 图例与编码 | D12–D15 | 图例缺项/颜色越界/数值无源 **一律阻断**；数值范围退化则关闭插值并注明 |
| 资产与依赖 | D16–D18 | matplotlib/字体缺失 → 降级但绝不伪造；包内资产缺失 → 回退内置默认并留痕 |
| 契约与状态 | D19–D23 | 四形态填空、**禁止 null**；failed 后补 6 项信封；三元组以退出码为真；命令自定位 |

## 7. 失败分支速览（完整版见 `SKILL.md` §2 与 `references/failure-modes.md`）

| 类别 | 分支数 | 典型处置 |
|---|---|---|
| 材料异常 | F01–F06 | 缺材料 → `failed` + 补救路径；PDF → 抽文本或手工规格；方向缺失 → 无向 + uncertain |
| 资产缺失 | F07–F09 | 调色板回退内置；schema 缺失记 warn 不阻断；模板缺失用 SKILL.md §7 清单代替 |
| 依赖缺失 | F10–F12b | 仅 SVG + `partial`；字体告警；显式 `--formats svg` 不算失败 |
| 契约四形态 | F13–F16 | 标量 `""` / 列表 `[]` / 布尔 `false` / 数值字典 `0`·`{}`，顶层不得 null |
| 状态一致性 | F17–F20 | schema 门 → `failed`；契约缺项 → 补齐；failed 信封缺 6 项 → 补写；三元组矛盾 → 取保守档 |

**每条失败都必须落到记录位点**（`status`/`reason`/`uncertainty`/`change_records`/`self_check`/
`export_checks`/`layout.warnings`/`legend_audit`/`topology` 之一）；记录位点为空 = 交付缺陷。

## 8. 适用范围与限制

- 适用：机制图 / 通路图 / 信号级联 / 调控网络 / 流程图 / 图表编辑，包括"改一个错误箭头"
  "按数据给节点上色""补图例""按模板重导出"。
- 不适用：数值统计与统计分析结论、实验方案设计、论文写作与版式美化（相邻课题负责）；
  本 Skill 只对图形中的科学内容表达、布局、可编辑性与导出质量负责。
- 自动抽取器只处理结构化语句（表格 / `A | 动词 | B` / `- A 动词 B（证据）`）；散文与 PDF
  依赖 Agent 手工抽取并用 `--model-file` 重跑（CP2b/CP3 强制）——"准确率优先于全自动"。
- 图件不在包内（运行时生成）；PDF 与 `result.json` 含时间戳，不作确定性承诺；
  完整失败模式与边界见 `references/failure-modes.md` 与 `TEST.md` §11。

## 9. 维护与更新

- 改颜色/线宽 → 只改 `assets/palettes.json`（全图与图例同步）；
- 改契约/门 → `references/OUTPUT_CONTRACT.md` + `scripts/check_contract.py` + `scripts/result_writer.py` 三处同步；
- 改校验规则 → `scripts/{topology,legend_audit,validate_figure}.py`，并更新 `references/mechanism-spec.md` 的校验一览；
- **改决策规则 → 必须同步 `SKILL.md` §1、§2 与 `references/failure-modes.md` 的 F 编号**（三处一一对应是本版的核心约定）；
- 改完跑 `TEST.md` 全套 → 更新实测记录 → 在 `worklog.md` 追加一条带时间的记录；
- **明令禁止**：向包内添加二进制资源或 `__pycache__`（图件必须运行时生成）。
