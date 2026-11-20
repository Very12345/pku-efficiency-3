# RUBRIC_MAP —— 评分五维 → 本 Skill 设计覆盖

题面评分维度（每项只计一次，综合 3 个固定案例与提交材料）：
**实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 · 生态贡献 10 · GitHub 公开链接 +5**（共 105）。
本表说明每个评分点的设计落点与可核验证据。证据路径均相对 Skill 根。

## 1. 实际效果（40 分）

| 评分点 | 本 Skill 覆盖 | 证据位置 |
|-|-|-|
| 任务完成度 15 | 四要素单页摘要：研究问题/方法/核心结果/结论固定四面板 + 阅读顺序编号 + 流程箭头；输出可编辑源 + 渲染件 | `scripts/figurespec.py`（面板/编码/流程）；示例 `examples/output/*.svg` |
| 结果正确性 15 | 实体↔关系↔数据全部 source-bound：每个元素带 `data-src`；数值仅来自材料；关系方向/正负（抑制=红色）由材料决定；数据用 bar_length/color_scale/area 编码且图例一一对应 | `scripts/extract.py`（抽取与溯源）、`scripts/svgbuilder.py`（`data-src`/`data-entity-id` 属性）、`scripts/audit.py`（entity_coverage、encoding_consistency 全量校验） |
| 结果完整性 5 | 覆盖六要素：科学实体、空间/因果关系、数据编码、图例标注、可编辑源文件、导出格式（SVG+PNG+PDF）；含单位、比例尺、面板标签、来源脚注 | `spec.json`（legend/scale_bar/reading_order/data_encoding）；页脚图例+比例尺在 `figurespec._footer` |
| 结果可核验性 5 | SVG metadata(build_id/skill 版本) + 每个元素 `data-src` + `sources[]`(路径+sha256) + `change_records` + `audit` 全量核查，第三方可独立复核 | `result.json`（provenance/sources/audit）；`OUTPUT_CONTRACT.md` §2/§6 |

## 2. 使用增益（25 分）

| 评分点 | 本 Skill 覆盖 | 证据位置 |
|-|-|-|
| 质量增益 15 | 与不加载 Skill 的基础 Agent 对照：基础 Agent 常产出无来源信息图/不可编辑位图/两次运行版式漂移；本 Skill 保证 ①数值可追源 ②布局确定性（同输入 spec hash 不变、SVG/PNG 两次运行字节一致）③文字可编辑。对照方案：基础 Agent 空跑 vs 加载 Skill 跑同一案例，比较 entity 覆盖率/编码一致性/可编辑性 | `TEST.md`（确定性实测 sha256：SVG/PNG 两轮逐字节相同）；`audit.determinism_probe` |
| 效率增益 5 | 免重绘/重排版/跨软件搬运：SVG 源可直接在 Inkscape/Illustrator 续改，`spec.json` 可微调参数再出图；自动排版+自动图例+自动自查替代手工对齐 | `scripts/figurespec.py`、`scripts/main.py` 一步流水线 |
| 增益可验证性 5 | 增益全部有可执行判据：`audit.json` 数值化（实体覆盖率、数值一致率、越界数、缺值清单）；对照复跑命令即验证 | `TEST.md`；`scripts/audit.py`；`OUTPUT_CONTRACT.md` §6 |

## 3. 创新增益（15 分）

| 评分点 | 本 Skill 覆盖 | 证据位置 |
|-|-|-|
| 新增能力 5 | 「实体—关系—数据—面板」四元抽取与统一图面规格：从实验记录/材料文本自动补事实（`A -> B (label)`、`键: 值 单位`），再映射到视觉通道；基础 Agent/常规绘图工具（PPT/Visio）不做抽取与溯源 | `scripts/extract.py`、`figurespec.py` |
| 方法改进 5 | ①确定性布局引擎（纯函数，同输入同输出）②数据编码 ↔ 图例自动一致性校验 ③分层命名+溯源属性规约 ④导出检查（良构/签名/尺寸/灰度可区分）作为流水线固定环节 | `scripts/figurespec.py`、`audit.py`、`svgbuilder.py`、`preview.py`；`references/TEMPLATE.md` |
| 创新证据 5 | 与常规方案的边界：单页信息图工具不保留可编辑源与溯源；本 Skill 以 `data-src` 逐元素挂接来源、以 hash 证明复现性；CJK 实体名无碰撞（slug 保留 Unicode 词字符） | `OUTPUT_CONTRACT.md`、`TEST.md` 复现实验、`common.slug` 注释 |

## 4. 可靠体验（10 分）

| 评分点 | 本 Skill 覆盖 | 证据位置 |
|-|-|-|
| 调用与易用性 3 | 单命令 `python scripts/main.py --case <case> --out <dir>`；输入形态兼容（实体/关系/数据缺省、文本补充）；文档含调用示例与逐字段说明 | `README.md`、`SKILL.md` §2/§3 |
| 运行稳定性 4 | 后端回退链（matplotlib→Pillow→纯 Python PNG）保证多数环境可出图；异常不静默（逐级记录）；同输入结构一致 | `scripts/preview.py`、`TEST.md` 稳定性用例 |
| 异常处理 3 | 失败模式表全覆盖：缺数值/实体歧义/文字溢出/字体缺失/画布超限/导出失败各自有处置与记录位点 | `SKILL.md` §4 表；`audit.py` 各检查项 |

## 5. 生态贡献（10 分）

| 评分点 | 本 Skill 覆盖 | 证据位置 |
|-|-|-|
| 文档完整性 3 | SKILL.md/README.md/TEST.md/OUTPUT_CONTRACT.md/RUBRIC_MAP.md/TEMPLATE.md：用途、依赖、安装、路径、来源、限制、失败处理、自查齐备 | 各文档 |
| 资源可复用性 4 | 图层结构+命名规约、图例样式、面板模板、`spec.json` 中间规格、示例案例可直接改数值复用于他题；脚本零第三方强依赖（stdlib+PIL/matplotlib 可选） | `TEMPLATE.md`、`examples/`、`scripts/` |
| 分享推广价值 3 | 单页摘要的「面板—要点」映射、视觉通道映射表、色盲安全色板、导出检查项沉淀为可复用规则；GITHUB_URL.txt 提供公开作品入口 | `TEMPLATE.md`、`GITHUB_URL.txt` |

## 6. GitHub 公开作品链接（+5 分）

`GITHUB_URL.txt` 第一行为公开仓库链接（发布代理覆写为精确地址），第二行为本作品相对路径 `graphical-abstract-7030fff2/`；
技能包内布局即仓库内布局（build/graphical-abstract-7030fff2/），评审无需登录即可打开定位作品。