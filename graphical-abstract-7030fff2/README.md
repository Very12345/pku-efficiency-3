# graphical-abstract v2 — 图形摘要（efficiency-3 / graphical-abstract-7030fff2）

依据固定科研材料生成或编辑可复用的单页科研图稿（图形摘要）：实体/关系/数据
**source-bound（每个元素带 `data-src` 可溯源）**、四要素（问题→方法→结果→结论）
单页可读、同输入同布局可复现，交付**可编辑分层 SVG 源** + PNG/PDF 渲染件 +
可复核 `result.json`。

包内**只有文本资源**（`.md/.py/.json/.txt`）：无二进制、无预置 `.svg/.png/.pdf`、无字体文件、
无 `__pycache__`。SVG 与渲染件一律**运行时生成**；修改记录见 git 与结果里的 `change_records`。

## 自定位（重要）

所有命令都以 `$SKILL_DIR`（本文件所在目录）为基准，**不要求 cwd = 技能根**：

```bash
SKILL_DIR=/skills/weekly-skill     # 官方评测容器；本机则写解压后的绝对路径
# 不确定时向上探测：
SKILL_DIR="$(pwd)"; while [ ! -f "$SKILL_DIR/SKILL.md" ] && [ "$SKILL_DIR" != "/" ]; do SKILL_DIR="$(dirname "$SKILL_DIR")"; done
```

## 快速开始

```bash
# 0) 方案先行（推荐）：生成设计方案骨架（真实抽取实体/关系/数据并带来源）
python "$SKILL_DIR/scripts/scaffold.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/plan.json
#    → Agent 阅读材料后填充 plan.four_elements（四句"一句话说明"），定稿 plan.json

# 1) 正式出图（可带 --plan；不带则走默认流程）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
       --plan "$SKILL_DIR/examples/plan.example.json" --out /tmp/ga-out

# 2) 契约自查（退出码即判据：0 = 顶层覆盖信封 ∪ 案例契约，且无 null）
python "$SKILL_DIR/scripts/check_contract.py" --result /tmp/ga-out/result.json \
       --case "$SKILL_DIR/examples/case.json"

# 3) 规格 lint 独立检查（已由 main.py 内嵌执行）
python "$SKILL_DIR/scripts/spec_lint.py" --spec /tmp/ga-out/spec.json --content /tmp/ga-out/content.json

# 4) 官方案例形态
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md --out /app/output
```

产出（均在 `--out`）：`<case_id>_graphical_abstract.svg`（可编辑分层源）、
`<case_id>_graphical_abstract.png/.pdf`（预览）、`spec.json`（图面规格）、
`content.json`（规范化抽取）、`audit.json` + `render_log.json`（自查/渲染日志）、
`result.json`（契约完整 + case_id + plan/spec_lint）。

## 主要参数

| 参数 | 说明 |
|-|-|
| `--case` | case.json 路径（必填） |
| `--task` | task.md（缺省自动找 `<case_dir>/task.md`） |
| `--material` | 材料文件或目录（缺省用 case.source_material） |
| `--plan` | 设计方案 plan.json（`scripts/scaffold.py` 生成，Agent 定稿；可选） |
| `--raster-scale` | PNG 分辨率倍率（默认取 constraints） |
| `--pdf / --no-pdf` | PDF 预览开关（默认取 constraints） |
| `--out` | 输出目录（默认 `<skill>/out`） |

## 依赖

- 必需：Python ≥3.8（核心流程只用标准库，可出纯 Python PNG）；
- 可选（逐级回退并如实记录）：`matplotlib`（默认渲染 + PDF）、`Pillow`（二级渲染）；
- 字体：运行时探测候选路径（`C:/Windows/Fonts`、`/usr/share/fonts`、`/System/Library/Fonts`），
  找不到则降级并在 `render_log.json` / `uncertainty` 记录；**SVG 里的 `<text>` 始终是真文字**；
- 不联网：不下载模板/字体/数据；
- 本机实测：Windows / Python 3.13.9（Anaconda）/ matplotlib 3.10.6 / Pillow 12.3，记录见 `TEST.md`。

## 关键方法与 v2 增强

1. **方案先行（plan-schema）**：scaffold 出方案骨架 → Agent 定稿四要素 → 方案 lint
   （CP1）后才绘制 —— "先想清楚表达什么，再动笔"；
2. **四要素知识文档（ga-four-elements.md）**：问题/方法/结果/结论每面板"必须表达 /
   只进图注"的边界 + Q-M-R-C 必齐不变式，audit 四要素覆盖检查执行；
3. **SVG 分层命名规范（layer-naming.md）**：7 层 `layer:*` 契约 + `data-*` 溯源属性
   + 真 `<text>` 可编辑 + 命名机器校验（audit.layer_naming）；
4. **双 lint 门**：绘制前方案 lint（`spec_lint.py --lint-plan`）+ 绘制后规格 lint
   （`spec_lint.py --spec`）——图例↔数据一致性、无源不上画布、编码词表、画布夹紧；
5. **契约升级**：output_contract **四形态回显**（禁止 null）+ G1–G8 硬性门 +
   plan/spec_lint 进信封；`scripts/check_contract.py` 提供独立 exit-code 判据；
6. **三资产成组（assets/）**：spec_template.json（方案模板）+ result_example.json
   （结果示例）+ example_material.txt（材料写法样例）—— 他人可直接复制套用；
7. 保留 v1 全部能力：确定性布局（同输入同 spec hash）、数据编码↔图例自动一致、
   实体覆盖率 100%、后端回退链、色盲安全色板、导出检查。

## 限制

- 渲染预览后端可能降级（如实记录 backend 与 font）；
- 实体抽取依赖材料文本结构，复杂材料需 Agent 复核；
- 本 Skill 负责图形内容的科学表达与版式，不保证论文/材料结论本身正确。

## 失败处理

异常分类、退出码语义与降级策略见 `references/failure-modes.md`（以及 `SKILL.md` §4
决策规则 D1–D10 / §5 异常表）：缺数值、实体歧义、文字溢出、字体缺失、画布超限、
导出失败、依赖缺失、契约字段缺失、lint 不过。一切降级写入 `result.json` 的
`uncertainty` 与 `change_records`，`status` 不得虚报。

## 自测与维护

- `TEST.md`：本地实测记录（命令、产物、结果、复现判据）；
- `references/RUBRIC_MAP.md`：评分五维（40/25/15/10/10）→ 覆盖对照（自查用）；
- `references/OUTPUT_CONTRACT.md`：result.json 契约 + G1–G8；
- `examples/EXPECTED-OUTPUT.md`：示例案例的期望产物清单与契约字段；
- 版本号在 `scripts/common.py` `SKILL_VERSION`（v2 = `2.0.0`）；修改历史见 git 与
  result.json `change_records`。
