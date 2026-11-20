# RUBRIC_MAP.md — 五维评分 → 本作品设计覆盖

本题评分维度（实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 ·
生态贡献 10，另加 GitHub 公开链接 5）。本表把每个评分点映射到作品内的具体
设计，便于评审/复跑对照。原则：**自述不算证据，全部用可复跑命令与产出文件
对照**（见 TEST.md 与本目录 README.md）。

## 实际效果（40）

| 评分点 | 作品覆盖 | 证据位置 |
|-|-|-|
| 任务完成度 15 | 读实际 case 文件 → 抽取主线 → 页序+页级叙事角色 → 生成可编辑 PPTX + 每页演讲备注 + 导出预览。页数与页序由 `spec.max_slides` 决定并记录在 `deck.slides[].role`。 | `scripts/main.py` 流水线；`scripts/planner.py alloc_roles` |
| 结果正确性 15 | 页面上每个数字与材料交叉核验：`check_claim_numbers()`，材料中找不到的数字进 `evidence.unverified_claims`；图表只重绘自真实数据表（`charting.py`），位图无数据只做诚实占位；不取整不编造。 | `scripts/common.py`、`scripts/charting.py`、`references/OUTPUT_CONTRACT.md §4` |
| 结果完整性 5 | 六类要素全覆盖：主线、页结构（roles）、图表引用（figure.ref + evidence footer）、讲解逻辑（notes）、模板约束（template spec）、导出渲染（PNG+PDF 预览）。 | `result.json deck.slides` / `previews` |
| 结果可核验性 5 | `sources[].sha256` 对拍输入；`manifest.json` 对拍全部产出；`evidence_map.md` 逐页人读映射；`changelog.jsonl` 版本记录；`check_contract.py` 自动校验。 | `scripts/result.py`、`scripts/check_contract.py` |

## 使用增益（25）

| 评分点 | 作品覆盖 | 证据位置 |
|-|-|-|
| 质量增益 15 | 与"基础 Agent 把摘要整段塞页"对照：本 Skill 强制 每页一个叙事角色、≤7 条要点、字号自动收敛不溢出、证据脚注每页可见、图表可编辑（PPTX 原生表格或重绘图）。 | `deck_builder.py _fit_size`、`planner.py`、TEST.md 对照记录 |
| 效率增益 5 | 一次 `--edit` 局部修改（改字号/换页码/改一条主张/重排页序）不需要全部重做；`--version` 归档历史版本，回退=复制旧版重放。 | `main.py apply_edits`、`changelog.jsonl` |
| 增益可验证性 5 | 同一 case 用基础流程与本 Skill 各跑一次并逐页 diff（TEST.md 记录命令与产物），成果提供 `--no-chart` 等降级开关保证可比条件。 | `TEST.md`、`examples/README.md` |

## 创新增益（15）

| 评分点 | 作品覆盖 | 证据位置 |
|-|-|-|
| 新增能力 5 | 页序规划（roles 分配器 alloc_roles）+ 页级主张的证据绑定（每页 evidence footer / notes）+ 图表-数据绑定（表→重绘图或原生可编辑表格）+ 局部编辑与版本回退（--edit + deck_v{n}）。基础 Agent 没有这些可复现能力。 | `planner.py`、`deck_builder.py`、`main.py` |
| 方法改进 5 | 确定性内容取舍规则（方法≤4 条、结果表→2 条量化主张、无表才回落散文）、数量核验器（claim↔material）、模板槽位约束驱动（不写死字号颜色）。 | `planner.py`、`common.py check_claim_numbers`、`templates/default.json` |
| 创新证据 5 | 相对题面"常见失败清单"（16 行）逐条给出机制：整段塞页→要点上限；抄错数字→数字核验器；占位图/凭空曲线→仅重绘真实数据表；模板被覆盖→模板 spec 与外部模板保留母版；改一页坏全稿→局部编辑+版本记录；导出字体/溢出→_fit_size+字体回落。 | 本表各列 + `references/TEMPLATE_SPEC.md` + TEST.md |

## 可靠体验（10）

| 评分点 | 作品覆盖 | 证据位置 |
|-|-|-|
| 调用与易用性 3 | 单条命令 `python scripts/main.py --case … --out …`；SKILL.md 写明调用方式、输入输出、异常处理表。 | `SKILL.md`、`README.md` |
| 运行稳定性 4 | 不同材料形态（md/txt/csv/html/PDF 兜底）、不同页数（3–20 自动分配）、不同模板（default / template_pptx / starting_deck）下持续产出；每步独立 try/except，失败降级并记 uncertainty；`--no-chart` 降级原生表格。 | `main.py`、`material.py`、`deck_builder.py` |
| 异常处理 3 | 专项处置：论文缺图→占位；位图无数据→不重绘；模板槽位不足/页数超限→按 max_slides 压缩并记录；字体缺失→PIL 回落+预警；导出失败→部分产物+failed/partial 状态；PDF 不可用→跳过并说明。 | `SKILL.md` 异常表、`render.py`、`charting.py` |

## 生态贡献（10）

| 评分点 | 作品覆盖 | 证据位置 |
|-|-|-|
| 文档完整性 3 | README（运行/依赖/限制/失败处理）、OUTPUT_CONTRACT.md、RUBRIC_MAP.md、TEMPLATE_SPEC.md、TEST.md、examples/README.md。 | 根目录与 references/ |
| 资源可复用性 4 | 模板 spec 可参数化（templates/default.json）；脚本模块化（material/planner/deck_builder/charting/render/result/check_contract）；数据表→原生 PPTX 表格无需 matplot；最小示例可整体复制运行。 | `templates/`、`scripts/`、`examples/` |
| 分享推广价值 3 | 沉淀"学术汇报页面骨架方法"：roles 分配规则、证据脚注约定、版本记录格式均可直接复用到其他汇报工具；示例案例标注"示例，非正式案例"供教学。 | `planner.py` 注释、`examples/` |

## GitHub 公开链接（5，额外分）

`GITHUB_URL.txt` 第一行为公开仓库链接（发布代理覆写为最终精确链接），第二行
为站内相对路径；评审无需登录即可打开并定位本作品。

## 对照建议（评审复跑）

1. 基础 Agent：给同一 case 直接让它做 PPT（无 SKILL.md）。
2. 本 Skill：加载本包按 SKILL.md 运行。
3. 对比 `deck.slides` 的 roles、verified 比例、备用 notes、模板约束命中、
   `check_contract.py` 通过率；逐页 diff 见 TEST.md 记录方法。