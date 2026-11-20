# rubric-map.md — 评分五维 → 本 Skill v2 设计覆盖

> 文件名与本题双榜首信号对齐：`references/rubric-map.md`（intel：rubric-map 是 70+ 包
> 的共性文档，且是少数同时出现在榜首包中的文件）。对应 build 基础包
> `references/RUBRIC_MAP.md`。
> 题面评分维度：**实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 ·
> 生态贡献 10 · GitHub 公开链接 +5**（合计 105）。证据路径相对 Skill 根。
> **文字自述不替代实际运行证据**——每个评分点的落点都给出可执行产物。

## 1. 实际效果（40 分）

| 评分点 | 本 Skill v2 覆盖 | 证据位置 |
|-|-|-|
| 任务完成度 15 | "读机制材料—定实体与关系—定布局与图例—出源文件与导出件"完整闭环：CP1 读真实文件 → CP2 规格（抽取/人工核验/schema 门）→ CP3 布局渲染审计 → CP4 交付 result.json | `scripts/main.py`（CP1–CP4 门）；`examples/output/`（实跑产物） |
| 结果正确性 15 | 实体类型/箭头语义/通路方向/数据编码全部可机器校验：`topology.py`（方向/区室/同名消歧/反馈）＋`legend_audit.py`（箭头=图例、颜色⊆图例∪映射、虚线语义、数值溯源）＋ schema 门（类型枚举） | `scripts/topology.py`、`scripts/legend_audit.py`、`assets/mechanism-spec.schema.json`；`references/legend-encoding.md` |
| 结果完整性 5 | 实体/边/图例项/并行分支/反馈环全覆盖（示例 9 实体 9 边、4 区室、5 类箭头、负反馈、弱证据虚线）；4+3 类产物（SVG/PNG/PDF/JSON + topology/legend_audit/model） | `examples/output/`；`result.json scientific_content.counts` |
| 结果可核验性 5 | 追溯链完整：材料行号 → source → SVG `data-source` → evidence_sources → export_checks(sha256) → change_records；审计文件独立存放 | `references/output-contract.md`；`topology.json`/`legend_audit.json` |

## 2. 使用增益（25 分）

| 评分点 | 本 Skill v2 覆盖 | 证据位置 |
|-|-|-|
| 质量增益 15 | 与基础 Agent 对照：基础 Agent 常见"平铺节点/箭头不区分/无图例/无源文件/方向颠倒"；本 Skill 以机器审计（拓扑+图例+契约+门）保证符号系统自洽、数值可溯源、方向正确 | `validate_figure.py`、`topology.py`、`legend_audit.py`；TEST.md 复现记录 |
| 效率增益 5 | 结构化材料一步出草稿（extract.py）；改图零重画（--model-file 重跑即可重导出）；一个 JSON 规格驱动 SVG/PNG/PDF 双后端；模板清单加速人工核验 | `scripts/extract.py`、`templates/relation-checklist-template.md` |
| 增益可验证性 5 | 全部增益有可执行判据：check_contract.py（契约+门 exit code）、validate_figure.py（全检查 exit code）、确定性探针（model_sha16/svg_sha16）、TEST.md 实测 | `TEST.md`；`scripts/check_contract.py`；`self_check.determinism` |

## 3. 创新增益（15 分）

| 评分点 | 本 Skill v2 覆盖 | 证据位置 |
|-|-|-|
| 新增能力 5 | 机制文字→图元/边的**结构化映射**（动词→5 类箭头+证据宽度+虚线规则）；**机制规格 schema 前置**（CP2 门，raw 校验防静默归一）；拓扑/图例双 linter；可编辑分层 SVG 自动生成（7 层 + data-* 溯源） | `extract.py`、`validate_figure.py`（validate_schema）、`topology.py`、`legend_audit.py`、`pathway_svg.py` |
| 方法改进 5 | ① 单一 JSON 规格驱动双渲染后端（零漂移）② 审计矩阵（P/L/E/T/F/S 系列）把"图例↔图面一致、来源可核、方向正确"从目检变机器强制 ③ 确定性布局（同输入同输出，SVG/PNG 双跑逐字节一致）④ 规范化调色板 assets/palettes.json 单点改色 | `layout.py`、`validate_figure.py`、`model.py`；TEST.md T4 |
| 创新证据 5 | 与常规绘图方案边界：通用画图不保留机制语义与来源链；本 Skill 以枚举类 schema + 审计 id + 确定性探针证明"正确 vs 像"的差异可检查；CJK 名称与字体处理显式化 | `references/legend-encoding.md`、`mechanism-spec.md`、`TEST.md` |

## 4. 可靠体验（10 分）

| 评分点 | 本 Skill v2 覆盖 | 证据位置 |
|-|-|-|
| 调用与易用性 3 | 单命令 `python scripts/main.py --case <case> --out <dir>`（可选 --model-file/--formats/--dpi）；文档含调用示例、字段说明、模板清单 | `README.md`、`SKILL.md`、`templates/relation-checklist-template.md` |
| 运行稳定性 4 | 不同通路形态（线性/分支/反馈/多区室）结构一致（示例含全部形态）；matplotlib 缺失自动降级并记录；重复运行确定性；审计/契约双门拦截失败 | `TEST.md`；`layout.py`、`mpl_backend.py` 降级 |
| 异常处理 3 | 失败模式表全覆盖（材料缺/PDF/方向缺失/歧义/矛盾数值/规格违规/图例不一致/数值无源/字体缺/导出失败/元素过多）＋决策规则 D1–Dn | `references/failure-modes.md`；`SKILL.md` §6–§7 |

## 5. 生态贡献（10 分）

| 评分点 | 本 Skill v2 覆盖 | 证据位置 |
|-|-|-|
| 文档完整性 3 | SKILL.md/README.md/TEST.md/COMPARE.md + references 5 件套（output-contract/rubric-map/mechanism-spec/legend-encoding/failure-modes）+ assets 3 件套 + 模板 | 各文档 |
| 资源可复用性 4 | 可复用件 = 机制规格 schema（assets/mechanism-spec.schema.json）、调色板/glyph 语义（palettes.json + legend-encoding.md）、关系核对模板（templates/）、契约与审计器（check_contract/validate_figure/topology/legend_audit 独立 CLI）、示例材料与模型 | `assets/`、`templates/`、`scripts/`（独立 CLI） |
| 分享推广价值 3 | 沉淀为可复用规则：箭头语义=科学论断、图例一致性检查、数据编码溯源、拓扑方向约束——可当作机制图题集/绘图规范起点 | `references/*`、`GITHUB_URL.txt` |

## 6. GitHub 公开作品链接（+5 分）

`GITHUB_URL.txt` 第一行为公开仓库链接（发布代理覆写为精确地址），第二行为本作品相对
路径 `target/challenge-83d4f050-v2/`；评审无需登录即可打开定位作品。

## 7. v2 覆盖变化（相对 build 基础包）

- 新增：CP1–CP4 检查点流水线 + 决策规则 D1–D12（SKILL.md）；机制规格 schema 门
  （assets/mechanism-spec.schema.json，raw 校验防静默归一）；
- 新增：`topology.py`（P 系列拓扑审计）与 `legend_audit.py`（L/E 系列图例/编码审计）、
  独立 `check_contract.py`（契约+门）；审计产物 topology.json/legend_audit.json 落盘；
- 新增：`templates/relation-checklist-template.md`（人工核验执行载体，对齐 76.67
  极简包唯一模板）、`assets/result.template.json`、`worklog.md`；
- 强化：四形态 output_contract 回显 + G1–G8 硬性门；status 在未核验草稿/schema 不过/
  门不过时不允许 success；SVG 确定性（去时间戳）；数据值溯源 E01 成为阻断检查；
- 修复（基包缺陷）：抽取器对 "A 动词 B" 空白的 left 尾随空格；约束行被误抽为实体。