# RUBRIC_MAP — 评分维度 → 设计覆盖

官方评分维度：**实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 ·
生态贡献 10**（另加 GitHub 公开链接 5 分）。下表逐维说明本 Skill 包的
设计如何覆盖每个评分点，以及证据落在哪个文件。

## 1. 实际效果（40）

| 评分点 | 分值 | 覆盖设计 | 证据位置 |
|-|-|-|-|
| 任务完成度 | 15 | 完整"材料→图稿→导出"链路：读材料 → ER 清单 → 可编辑 SVG → PNG/PDF → result.json；3 个示例（schematic/chart/edit）各跑通并留真实产物 | `SKILL.md` 执行步骤、`examples/output/*`、`TEST.md` |
| 结果正确性 | 15 | 实体/关系/方向/层级逐条绑定 `source+evidence`；关系 kind 规范化（激活/抑制/招募/转录/包含），方向以材料原文为准；图例与图面箭头双向校验，缺项/孤儿项即 fail/warn；图表类别↔颜色↔图例由同一数据表生成 | `references/ER_MANIFEST.md`、`scripts/manifest.py`、`scripts/checks.py` |
| 结果完整性 | 5 | 覆盖示意图的实体、关系、分组、图例、子图编号/标题、单位、来源脚注；图表含轴标签+单位 | `scripts/svgbuilder.py`（layer-nodes/edges/groups/legend/footer） |
| 可核验性 | 5 | 每个图元带 `data-entity/data-relation/data-source` 与内嵌 manifest；`verification.checks` 记录全部检查明细；`validate_result.py` 可独立复验 | `scripts/svgbuilder.py`、`scripts/validate_result.py` |

## 2. 使用增益（25）

| 评分点 | 分值 | 覆盖设计 | 证据位置 |
|-|-|-|-|
| 质量增益 | 15 | 同一输入/画布/导出参数下，正确性检查（图例一致性、方向语义、溯源完整性、DPI/字体/色彩检查）在每次运行自动执行并计入 result.json；方形"画图即核验"闭环 | `scripts/checks.py`、`SKILL.md` Step 4-5 |
| 效率增益 | 5 | 素材→图稿一条命令；数据改动只改 manifest 即可重绘（数据驱动重绘）；编辑任务直接从已有 SVG 内嵌清单增量修改，无需重新抽取 | `scripts/main.py`、`scripts/edit.py` |
| 增益可验证性 | 5 | 同源材料对照记录（Task 记录基准条件）；`verification.checks`+`TEST.md` 复跑记录即公平对照证据；示例产物全部落盘 | `TEST.md`、`examples/output/` |

## 3. 创新增益（15）

| 评分点 | 分值 | 覆盖设计 | 证据位置 |
|-|-|-|-|
| 新增能力 | 5 | ①文字材料→ER 清单抽取（中英文关系动词词表，含歧义检测，未知类型 fail 而非猜）；②数据表驱动图例重绘；③导出前合规检查（DPI/字体/色彩/文字可编辑性） | `scripts/manifest.py`（词表）、`scripts/checks.py`、`scripts/render.py` |
| 方法改进 | 5 | SVG 内嵌 ER manifest（`<metadata id=er-manifest>`）→ 真正的"源文件自包含修改"；手写分层 SVG（语义图层+id+data-*）+ matplotlib 镜像预览保持语义一致；matplotlib `svg.fonttype=none` 保住文字可编辑（默认 path 会毁掉可编辑性，这是本次实测发现并规避的坑） | `scripts/svgbuilder.py`、`scripts/edit.py`、`scripts/render.py`、`TEST.md` 第 4 节 |
| 创新证据 | 5 | selftest 23 项 + 3 条冒烟链路（schematic/chart/edit）真实运行记录；SVG 结构与 PNG 调色板程序化审计 | `scripts/selftest.py`、`TEST.md` |

## 4. 可靠体验（10）

| 评分点 | 分值 | 覆盖设计 | 证据位置 |
|-|-|-|-|
| 调用与易用性 | 3 | YAML frontmatter 规范触发；一条命令出图；`--case/--manifest/--out` 均支持绝对路径，脚本自定位不依赖 cwd | `SKILL.md`、`scripts/main.py` |
| 运行稳定性 | 4 | 三图型（schematic/chart/编辑）重复运行稳定；无 cairosvg/svgwrite 环境下用镜像渲染降级并如实标注；产物原子写出；失败时仍写 failed result.json | `scripts/render.py`、`scripts/main.py` |
| 异常处理 | 3 | 来源缺失（列出清单+写 uncertainty）、材料矛盾（方向/图例冲突→检查 fail）、数据与图例不符、字体缺失（CJK 探测+警告）、导出失败 → 全部识别并落到 result.json，不静默绕过 | `scripts/checks.py`、`SKILL.md` 异常处理表 |

## 5. 生态贡献（10）

| 评分点 | 分值 | 覆盖设计 | 证据位置 |
|-|-|-|-|
| 文档完整性 | 3 | SKILL.md/README/规范三件套/示例任务书/测试记录；依赖与安装方式、运行方法、限制、失败处理齐全 | `README.md`、`SKILL.md`、`references/*` |
| 资源可复用性 | 4 | ER 清单规范、配色/箭头/图例规范、导出预检(DPI 300/字体/色彩)、可复用脚本（main/render/checks/edit/validate/selftest） | `references/ER_MANIFEST.md`、`scripts/*` |
| 分享推广价值 | 3 | 合成示例题集（schematic/chart/edit 三件套）标注"示例，非正式案例"可直接复跑；GITHUB_URL.txt 指向公开仓库 | `examples/*`、`GITHUB_URL.txt` |

## GitHub 附加分（5）

`GITHUB_URL.txt` 第一行 `https://github.com/Very12345/pku-efficiency-3`，
第二行给出本作品相对路径；发布代理将覆写为精确链接并保证未登录可访问。

## 对照口径提示

"白板/基础 Agent 对照"由平台执行。本包在自身夹具上保留的对照证据：
`TEST.md` 记录了**同一示例三遍复跑 + 失败用例的异常路径输出**，供
评审按相同输入/画布/导出参数复核我们的稳定增益。