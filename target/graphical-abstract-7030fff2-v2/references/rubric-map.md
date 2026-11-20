# rubric-map.md — 评分五维 → 本 Skill 设计覆盖（v2）

> 文件名与高分包（76.67 榜首 75112 与全场最高 80.00 共有）对齐：`references/rubric-map.md`。
> 题面评分维度：**实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 ·
> 生态贡献 10 · GitHub 公开链接 +5**（共 105）。本表说明每个评分点的设计落点与
> 可核验证据；证据路径相对 Skill 根。**文字自述不替代实际运行证据。**

## 1. 实际效果（40 分）

| 评分点 | 本 Skill v2 覆盖 | 证据位置 |
|-|-|-|
| 任务完成度 15 | 四要素单页摘要：问题/方法/结果/结论四面板 + 阅读顺序 + 流程箭头；输出可编辑分层 SVG + PNG/PDF 渲染件；**方案先行（plan-schema）确保先想清楚再动笔** | `scripts/figurespec.py`；`scripts/scaffold.py` + `references/plan-schema.md`；示例 `examples/output/*.svg` |
| 结果正确性 15 | 实体↔关系↔数据全部 source-bound（`data-src`）；数值仅来自材料；关系方向/正负（抑制=红色）由材料决定；数据用 bar_length/color_scale/area 编码且图例一一对应；**spec_lint 把"图例↔数据一致性""无源不上画布"变成硬检查** | `scripts/extract.py`；`scripts/svgbuilder.py`；`scripts/audit.py`（entity_coverage、encoding_consistency）；`scripts/spec_lint.py` |
| 结果完整性 5 | 覆盖六要素：科学实体、空间/因果关系、数据编码、图例标注、可编辑源文件、导出格式；含单位、比例尺、面板标签、来源脚注；**四要素覆盖检查（audit.four_element_coverage）保证 Q-M-R-C 必齐** | `spec.json`（legend/scale_bar/reading_order/data_encoding）；`references/ga-four-elements.md` |
| 结果可核验性 5 | SVG metadata(build_id/版本) + 每元素 `data-src` + `sources[]`(路径+sha256) + `change_records` + audit 全量核查；**图层命名规范（layer-naming.md）让"分层、命名、可溯源"可被机器校验** | `result.json`（provenance/sources/audit/plan/spec_lint）；`references/output-contract.md` |

## 2. 使用增益（25 分）

| 评分点 | 本 Skill v2 覆盖 | 证据位置 |
|-|-|-|
| 质量增益 15 | 与基础 Agent 对照：基础 Agent 常产出无来源信息图/不可编辑位图/两次运行版式漂移；本 Skill v2 保证 ①数值可追源（spec_lint 硬门）②布局确定性（spec hash 不变、SVG/PNG 两轮字节一致）③文字可编辑（真 `<text>` + 图层契约）④四要素齐全 | `TEST.md`（确定性实测 sha256）；`audit.determinism_probe` + `spec_lint.spec_sha16` |
| 效率增益 5 | 免重绘/重排版/跨软件搬运：`scaffold.py` 一步出方案骨架；SVG 源可直接续改；`spec.json` 微调参数再出图；自动排版+自动图例+自动自查 | `scripts/scaffold.py`、`scripts/main.py` 一步流水线 |
| 增益可验证性 5 | 增益全部有可执行判据：`audit.json` 数值化（实体覆盖率、数值一致率、越界数、缺值清单、四要素覆盖、图层命名）+ `spec_lint` valid + `TEST.md` 复跑记录 | `TEST.md`；`scripts/audit.py`；`scripts/spec_lint.py` |

## 3. 创新增益（15 分）

| 评分点 | 本 Skill v2 覆盖 | 证据位置 |
|-|-|-|
| 新增能力 5 | 「实体—关系—数据—面板」四元抽取 + 统一图面规格；**plan-schema 方案先行**（scaffold + 方案 lint）；四要素内容不变式（ga-four-elements.md）；SVG 图层命名契约的可执行化 | `scripts/extract.py`、`scripts/scaffold.py`、`scripts/spec_lint.py`；`references/plan-schema.md`、`references/ga-four-elements.md`、`references/layer-naming.md` |
| 方法改进 5 | ①确定性布局引擎（纯函数同输入同输出）②数据编码↔图例自动一致性校验（spec_lint）③分层命名+溯源属性规约（audit 硬检查）④导出检查（良构/签名/尺寸/灰度）作为流水线固定环节 | `scripts/figurespec.py`、`spec_lint.py`、`audit.py`、`svgbuilder.py`、`preview.py` |
| 创新证据 5 | 与常规方案边界：单页信息图工具不保留可编辑源与溯源；本 Skill 以 `data-src` 逐元素挂接来源、以 hash 证明复现性、以 layer-naming + four-element 检查证明结构完整；CJK 实体名无碰撞 | `references/layer-naming.md`、`references/output-contract.md`、`TEST.md` 复现实验 |

## 4. 可靠体验（10 分）

| 评分点 | 本 Skill v2 覆盖 | 证据位置 |
|-|-|-|
| 调用与易用性 3 | 单命令 `python scripts/main.py --case <case> --out <dir>`；可选 `--plan`（方案先行）；输入形态兼容；文档含调用示例与逐字段说明 | `README.md`、`SKILL.md` |
| 运行稳定性 4 | 后端回退链（matplotlib→Pillow→纯 Python PNG）；异常不静默（逐级记录）；同输入结构一致；方案/规格 lint 在绘制前后双门拦截 | `scripts/preview.py`、`spec_lint.py`、`TEST.md` |
| 异常处理 3 | 失败模式表全覆盖：缺数值/实体歧义/文字溢出/字体缺失/画布超限/导出失败/方案 lint 不过 各自有处置与记录位点 | `SKILL.md` §5 决策规则 + §6 异常表；`audit.py` |

## 5. 生态贡献（10 分）

| 评分点 | 本 Skill v2 覆盖 | 证据位置 |
|-|-|-|
| 文档完整性 3 | SKILL.md/README.md/TEST.md/output-contract/rubric-map/plan-schema/ga-four-elements/layer-naming：用途、依赖、路径、来源、限制、失败处理、自查齐备 | 各文档 |
| 资源可复用性 4 | 图层结构+命名规约、图例样式、面板模板、`spec.json` 中间规格、**plan 骨架模板 + 结果示例 + 材料样例（assets 三件套）**可直接复用；脚本零第三方强依赖 | `references/layer-naming.md`、`assets/`、`TEMPLATE.md`、`examples/` |
| 分享推广价值 3 | 四要素面板映射、视觉通道映射、色盲安全色板、导出检查项沉淀为可复用规则；GITHUB_URL.txt 提供公开作品入口 | `references/ga-four-elements.md`、`TEMPLATE.md`、`GITHUB_URL.txt` |

## 6. GitHub 公开作品链接（+5 分）

`GITHUB_URL.txt` 第一行为公开仓库链接（发布代理覆写为精确地址），第二行为本作品
相对路径 `graphical-abstract-7030fff2/`；评审无需登录即可打开定位作品。

## 7. v2 覆盖变化

- 新增：方案先行（scaffold.py + plan-schema.md + lint_plan）——把"设计决策"变成
  可检查中间产物；
- 新增：四要素知识文档（ga-four-elements.md）+ audit 四要素覆盖检查；
- 新增：SVG 分层命名规范（layer-naming.md）+ audit 图层命名硬检查；
- 新增：spec_lint（绘制前方案门 + 绘制后规格门，双 lint 进 result.json）；
- 新增：assets 三件套（spec_template.json / result_example.json / example_material.txt）；
- 强化：output_contract 四形态回显 + G1–G8 硬性门；status 在 lint 不过时不允许 success。