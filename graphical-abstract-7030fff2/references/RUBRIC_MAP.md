# RUBRIC_MAP.md — 评分五维 → 本 Skill 设计覆盖（v2）

> **本文件是本期最强高分信号**：76.67 分榜首（75112）与全场最高（80.00）共有的唯一文档
> 就是"评分维度映射"。成员包内固定路径为 `references/RUBRIC_MAP.md`（根目录 `SKILL.md`
> §7 有同表速查版）。
> 题面评分维度：**实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 ·
> 生态贡献 10 · GitHub 公开链接 +5**（共 105）。本表说明每个评分点的设计落点与
> 可核验证据；证据路径相对 Skill 根。**文字自述不替代实际运行证据。**

## 1. 实际效果（40 分）

| 评分点 | 本 Skill v2 覆盖 | 证据位置 |
|-|-|-|
| 任务完成度 15 | 四要素单页摘要：问题/方法/结果/结论四面板 + 阅读顺序 + 流程箭头；输出可编辑分层 SVG + PNG/PDF 渲染件（**运行时生成，包内不留二进制**）；**方案先行（plan-schema）确保先想清楚再动笔** | `scripts/figurespec.py`；`scripts/scaffold.py` + `references/plan-schema.md`；`examples/EXPECTED-OUTPUT.md`（期望产物清单）+ `examples/output/spec.json`（实跑图面规格） |
| 结果正确性 15 | 实体↔关系↔数据全部 source-bound（`data-src`）；数值仅来自材料；关系方向/正负（抑制=红色）由材料决定；数据用 bar_length/color_scale/area 编码且图例一一对应；**spec_lint 把"图例↔数据一致性""无源不上画布"变成硬检查** | `scripts/extract.py`；`scripts/svgbuilder.py`；`scripts/audit.py`（entity_coverage、encoding_consistency）；`scripts/spec_lint.py` |
| 结果完整性 5 | 覆盖六要素：科学实体、空间/因果关系、数据编码、图例标注、可编辑源文件、导出格式；含单位、比例尺、面板标签、来源脚注；**四要素覆盖检查（audit.four_element_coverage）保证 Q-M-R-C 必齐** | `spec.json`（legend/scale_bar/reading_order/data_encoding）；`references/ga-four-elements.md` |
| 结果可核验性 5 | SVG metadata(build_id/版本) + 每元素 `data-src` + `sources[]`(路径+sha256) + `change_records` + audit 全量核查；**图层命名规范（layer-naming.md）让"分层、命名、可溯源"可被机器校验** | `result.json`（provenance/sources/audit/plan/spec_lint）；`references/OUTPUT_CONTRACT.md` |

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
| 创新证据 5 | 与常规方案边界：单页信息图工具不保留可编辑源与溯源；本 Skill 以 `data-src` 逐元素挂接来源、以 hash 证明复现性、以 layer-naming + four-element 检查证明结构完整；CJK 实体名无碰撞 | `references/layer-naming.md`、`references/OUTPUT_CONTRACT.md`、`TEST.md` 复现实验 |

## 4. 可靠体验（10 分）

| 评分点 | 本 Skill v2 覆盖 | 证据位置 |
|-|-|-|
| 调用与易用性 3 | 单命令 `python "$SKILL_DIR/scripts/main.py" --case <case> --out <dir>`（自定位，cwd 任意）；可选 `--plan`（方案先行）；输入形态兼容；文档含调用示例与逐字段说明 | `README.md`、`SKILL.md` §0（自定位调用）；`examples/README.md` |
| 运行稳定性 4 | 后端/字体回退链（matplotlib→Pillow→纯 Python PNG；Windows/macOS/Linux 字体候选探测）；异常不静默（逐级记录）；同输入结构一致（spec hash）；方案/规格 lint 在绘制前后双门拦截 | `scripts/preview.py`、`scripts/spec_lint.py`、`TEST.md`（确定性实测） |
| 异常处理 3 | 失败模式表全覆盖：材料异常/模板缺失/依赖缺失/契约四形态/状态一致性 + 缺数值/实体歧义/文字溢出/字体缺失/画布超限/导出失败/方案 lint 不过，各自有处置与记录位点；退出码语义明确（0/1/2） | `references/failure-modes.md`（专文）；`SKILL.md` §4 决策规则 + §5 异常表；`scripts/check_contract.py`（exit code 判据） |

## 5. 生态贡献（10 分）

| 评分点 | 本 Skill v2 覆盖 | 证据位置 |
|-|-|-|
| 文档完整性 3 | SKILL.md / README.md / TEST.md / OUTPUT_CONTRACT.md / RUBRIC_MAP.md（本文件）/ failure-modes.md / plan-schema.md / ga-four-elements.md / layer-naming.md / TEMPLATE.md / examples/README.md / examples/EXPECTED-OUTPUT.md：用途、依赖、参数、路径、来源、限制、失败处理、自查、维护齐备 | 各文档（根目录 + `references/` + `examples/`） |
| 资源可复用性 4 | 图层结构+命名规约、图例样式、面板模板、`spec.json` 中间规格、**plan 骨架模板 + 结果示例 + 材料样例（assets 三件套）**、可复制的最小示例（`examples/`）与两个 exit-code 自查器（`spec_lint.py` / `check_contract.py`）可直接复用；脚本零第三方强依赖（matplotlib/Pillow 均可选） | `references/layer-naming.md`、`assets/`、`references/TEMPLATE.md`、`examples/`、`scripts/check_contract.py` |
| 分享推广价值 3 | 四要素面板映射、视觉通道映射、色盲安全色板、导出检查项沉淀为可复用规则；纯文本包便于直接 fork/PR；`GITHUB_URL.txt` 提供公开作品入口 | `references/ga-four-elements.md`、`references/TEMPLATE.md`、`GITHUB_URL.txt` |

## 6. GitHub 公开作品链接（+5 分）

`GITHUB_URL.txt` 第一行为公开仓库中**本作品**的精确链接
（`https://github.com/Very12345/pku-efficiency-3/tree/main/graphical-abstract-7030fff2`），
第二行为本作品在该仓库中的相对路径 `graphical-abstract-7030fff2/`；
评审无需登录即可打开定位作品。

## 7. v2 覆盖变化

- 新增：方案先行（scaffold.py + plan-schema.md + lint_plan）——把"设计决策"变成
  可检查中间产物；
- 新增：四要素知识文档（ga-four-elements.md）+ audit 四要素覆盖检查；
- 新增：SVG 分层命名规范（layer-naming.md）+ audit 图层命名硬检查；
- 新增：spec_lint（绘制前方案门 + 绘制后规格门，双 lint 进 result.json）；
- 新增：assets 三件套（spec_template.json / result_example.json / example_material.txt）；
- 强化：output_contract 四形态回显 + G1–G8 硬性门；status 在 lint 不过时不允许 success。

## 8. 合规重打包（2026-11-22）——资源形态变更说明

为满足题面英文契约（`Skill resources: at most 50 UTF-8 text files, 500KB each and
2MB total, no symlinks`）与平台预检，本包的资源形态做了如下收敛，**评分维度覆盖不变**：

- 删除全部二进制与 `.svg` 预置件（原 `examples/output/*.svg/.png/.pdf`）→ 改由
  `scripts/svgbuilder.py` + `scripts/preview.py` **运行时生成**，期望清单见
  `examples/EXPECTED-OUTPUT.md`；
- 删除 `__pycache__`/`*.pyc`；包内**不再有任何绝对路径**（示例产物路径已归一化为相对路径；
  仅保留跨平台字体探测候选路径字符串 `C:/Windows/Fonts/...` 等，属探测逻辑而非运行残留）；
- 文档名对齐必备清单：`references/OUTPUT_CONTRACT.md`、`references/RUBRIC_MAP.md`、
  `references/failure-modes.md`；
- 新增 `scripts/check_contract.py`（契约自查，exit code 判据）与 `examples/README.md`、
  `examples/EXPECTED-OUTPUT.md`。