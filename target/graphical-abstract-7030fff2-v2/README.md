# graphical-abstract v2 — 图形摘要（efficiency-3 / graphical-abstract-7030fff2）

依据固定科研材料生成或编辑可复用的单页科研图稿（图形摘要）：实体/关系/数据
**source-bound（每个元素带 `data-src` 可溯源）**、四要素（问题→方法→结果→结论）
单页可读、同输入同布局可复现，交付**可编辑分层 SVG 源** + PNG/PDF 渲染件 +
可复核 `result.json`。v2 加强包相对 build 基包的变化见 `COMPARE.md`。

## 快速开始

```bash
# 0) 方案先行（推荐，v2）：生成设计方案骨架（真实抽取实体/关系/数据并带来源）
python scripts/scaffold.py --case examples/case.json --out plan.json
#    → Agent 阅读材料后填充 plan.four_elements（四句"一句话说明"），定稿 plan.json

# 1) 正式出图（可带 --plan；不带则走默认流程）
python scripts/main.py --case examples/case.json --plan plan.json --out <output_dir>

# 2) 规格 lint 独立检查（已由 main.py 内嵌执行）
python scripts/spec_lint.py --spec <output_dir>/spec.json --content <output_dir>/content.json

# 3) 官方案例形态
python scripts/main.py --case /input/case.json --out /app/output
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
| `--out` | 输出目录 |

## 依赖

- 必需：Python ≥3.8（标准库即可出纯 Python PNG）；
- 可选（逐级回退并如实记录）：`matplotlib`（默认渲染 + PDF）、`Pillow`（二级渲染）；
- 本机实测：Windows / Python 3.13.9（Anaconda）/ matplotlib 3.10.6 / Pillow 12.3，
  记录见 `TEST.md`。

## 关键方法与 v2 增强

1. **方案先行（plan-schema）**：scaffold 出方案骨架 → Agent 定稿四要素 → 方案 lint
   （CP1）后才绘制 —— "先想清楚表达什么，再动笔"；
2. **四要素知识文档（ga-four-elements.md）**：问题/方法/结果/结论每面板"必须表达 /
   只进图注"的边界 + Q-M-R-C 必齐不变式，audit 四要素覆盖检查执行；
3. **SVG 分层命名规范（layer-naming.md）**：7 层 `layer:*` 契约 + `data-*` 溯源属性
   + 真 `<text>` 可编辑 + 命名机器校验（audit.layer_naming）；
4. **双 lint 门**：绘制前方案 lint（lint_plan）+ 绘制后规格 lint（lint）——图例↔数据
   一致性、无源不上画布、编码词表、画布夹紧（spec_lint.py）；
5. **契约升级**：output_contract **四形态回显**（禁止 null）+ G1–G8 硬性门 +
   plan/spec_lint 进信封；
6. **三资产成组（assets/）**：spec_template.json（方案模板）+ result_example.json
   （结果示例）+ example_material.txt（材料写法样例）—— 他人可直接复制套用；
7. 保留 v1 全部能力：确定性布局（同输入同 spec hash）、数据编码↔图例自动一致、
   实体覆盖率 100%、后端回退链、色盲安全色板、导出检查。

## 限制

- 渲染预览后端可能降级（如实记录 backend）；
- 实体抽取依赖材料文本结构，复杂材料需 Agent 复核；
- 本 Skill 负责图形内容的科学表达与版式，不保证论文/材料结论本身正确。

## 失败处理

异常分类与处置见 `SKILL.md` §4 决策规则 D1–D10 与 §5 异常表
（缺数值/实体歧义/文字溢出/字体缺失/画布超限/导出失败/lint 不过）。一切降级
写入 `result.json` 的 `uncertainty` 与 `change_records`。

## 自测与维护

- `TEST.md`：本地实测记录（命令、产物、结果）；
- `references/rubric-map.md`：评分五维→覆盖对照（自查用）；
- `references/output-contract.md`：result.json 契约 + G1–G8；
- 版本号在 `scripts/common.py` `SKILL_VERSION`（v2=2.0.0）；修改历史见 git
  与 result.json `change_records`。