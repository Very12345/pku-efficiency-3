# RUBRIC_MAP — 评分维度 → v2 设计覆盖

官方评分维度：**实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 ·
生态贡献 10**（另加 GitHub 公开链接 5 分）。下表逐维说明 v2 的设计如何
覆盖每个评分点，以及证据落在哪个文件。自查时**文字自述不替代运行
证据**——每条"覆盖"都对应可运行脚本或已落盘产物。

## 1. 实际效果（40）

| 评分点 | 分值 | v2 覆盖 | 证据位置 |
|-|-|-|-|
| 任务完成度 | 15 | 完整"材料→图稿→导出"链路：读实际文件 →（extract 候选草稿）→ ER 清单 → CP1 lint → 可编辑 SVG → PNG/PDF → result.json；3 示例（schematic/chart/edit）各跑通并留真实产物 | `SKILL.md` 执行步骤、`examples/output/*`、`TEST.md` |
| 结果正确性 | 15 | 实体/关系/方向/层级逐条绑定 `source+evidence`；关系 kind 规范化（**激活≠抑制**，激活/抑制/招募/转录/因果/包含），方向以材料原文为准；**CP1 spec_lint 门**：kind 可映射、containment 必须用分组不画箭头、图例双向一致、chart 调色板≥类别数；数据表外的类别=G8 硬门 | `references/DRAWING_GRAMMAR.md`、`assets/relation-dict.json`、`scripts/spec_lint.py`、`scripts/checks.py`、`scripts/validate_result.py` |
| 结果完整性 | 5 | 三类示意图要素全覆盖：实体、关系、分组框、子图/模块标题、图例（来源标注）、单位（轴上）、来源脚注；chrome 元素含 `<title>/<desc>` 与版权/来源页脚 | `scripts/svgbuilder.py`（layer-background/groups/edges/nodes/legend/footer） |
| 可核验性 | 5 | 每个图元带 `data-entity/data-relation/data-canon/data-source` 与内嵌 ER 清单（`<metadata id=er-manifest>`）；`verification.checks`+`spec_lint` 记录全部检查明细；`validate_result.py` G1–G8 可独立复验 | `scripts/svgbuilder.py`、`scripts/checks.py`（svg.data_*_attrs）、`scripts/validate_result.py` |

## 2. 使用增益（25）

| 评分点 | 分值 | v2 覆盖 | 证据位置 |
|-|-|-|-|
| 质量增益 | 15 | 同一输入/画布/导出参数下：正确性检查（CP1 lint + 图例一致性 + 方向语义 + 溯源 + DPI/字体/色彩 + 颜色×类别数）每次运行自动执行并计入 result.json；**生成→检查→编辑→再校验**闭环；对比白板由平台产生 | `scripts/spec_lint.py`、`scripts/checks.py`、`SKILL.md` S0–S7 |
| 效率增益 | 5 | 素材→图稿一条命令（main.py）；`extract.py --inputs 材料 --out draft.json` 现场生成**候选 ER 清单**（含定位）减少人工抽取；数据改动只改 manifest 即可重绘；编辑任务直接从 SVG 内嵌清单增量修改，无需重新抽取 | `scripts/main.py`、`scripts/extract.py`、`scripts/edit.py` |
| 增益可验证性 | 5 | 同源材料对照记录；`TEST.md` 复跑记录（同一示例三遍复跑 + 失败用例异常路径）+ `--fixed-time` 确定性双跑 sha 对拍；示例产物全部落盘 | `TEST.md`、`examples/output/`、`verification.determinism` |

## 3. 创新增益（15）

| 评分点 | 分值 | v2 覆盖 | 证据位置 |
|-|-|-|-|
| 新增能力 | 5 | ①材料→候选 ER 清单抽取（中英文关系动词词表、歧义检测、未知类型 fail 而非猜，`extract.py`）；②**CP1 生成前 lint 门**（关系词典一致性、containment 分组约束、调色板×类别数）；③PDF 文本抽取（stdlib 回退 + 诚实降级，`pdftext.py`）；④数据表驱动图例重绘；⑤导出前合规检查（DPI/字体/色彩/文字可编辑性/data-* 溯源审计） | `scripts/extract.py`、`scripts/pdftext.py`、`scripts/spec_lint.py`、`scripts/checks.py` |
| 方法改进 | 5 | SVG 内嵌 ER manifest → 源文件自包含修改；手写分层 SVG（语义图层+id+data-*）+ matplotlib 镜像预览保持语义一致；matplotlib `svg.fonttype=none` 保住文字可编辑（默认 path 会毁掉可编辑性，基包实测发现并规避）；**共享字体探针 textfont.py** 让 render/checks/result 三方同源 | `scripts/svgbuilder.py`、`scripts/edit.py`、`scripts/render.py`、`scripts/textfont.py` |
| 创新证据 | 5 | 自测 26+ 项（含新模块 spec_lint/textfont/extract/pdftext/validate G 门）+ 3 条冒烟链路真实运行记录；PDF 构造样本验证 stdlib 回退不崩；SVG 结构与 PNG 调色板程序化审计 | `scripts/selftest.py`、`TEST.md` |

## 4. 可靠体验（10）

| 评分点 | 分值 | v2 覆盖 | 证据位置 |
|-|-|-|-|
| 调用与易用性 | 3 | YAML frontmatter 规范触发；一条命令出图；`--case/--manifest/--out` 均支持绝对路径，脚本 `os.path.dirname(__file__)` 自定位不依赖 cwd；face 明确的失败信息 | `SKILL.md`、`scripts/main.py` |
| 运行稳定性 | 4 | 三图型（schematic/chart/编辑）重复运行稳定；无 cairosvg/svgwrite 环境用镜像渲染降级并如实标注；PDF 无第三方库时 stdlib 回退；产物原子写出；失败仍写 failed result.json；确定性 sha 探针 | `scripts/render.py`、`scripts/pdftext.py`、`scripts/main.py` |
| 异常处理 | 3 | 来源缺失、材料矛盾（方向冲突→取有证据者+uncertainty）、kind 无法映射（fail 不猜箭头）、数据与图例不符、颜色×类别数不符、字体缺失（CJK 探测+警告）、PDF 加密/扫描件、导出失败 → 全部识别并落到 result.json | `scripts/checks.py`、`SKILL.md` 异常表 D1–D12、`references/FAILURE_MODES.md` |

## 5. 生态贡献（10）

| 评分点 | 分值 | v2 覆盖 | 证据位置 |
|-|-|-|-|
| 文档完整性 | 3 | SKILL.md/README/规范五件套/示例任务书/测试记录；依赖与字体安装、运行方法、限制、失败处理齐全 | `README.md`、`SKILL.md`、`references/*` |
| 资源可复用性 | 4 | **机器可读连接规则字典**（assets/relation-dict.json，kind→arrow/line/dash/color 可直接复用）、CP 自查清单（assets/checklist.json）、ER 清单规范+图形语法规范（DRAWING_GRAMMAR.md）、导出预检与验证脚本 | `assets/*`、`references/DRAWING_GRAMMAR.md`、`scripts/*` |
| 分享推广价值 | 3 | 合成示例题集（schematic/chart/edit 三件套）标注"示例，非正式案例"可直接复跑；失败模式文档沉淀实践；GITHUB_URL.txt 指向公开仓库 | `examples/*`、`references/FAILURE_MODES.md`、`GITHUB_URL.txt` |

## GitHub 附加分（5）

`GITHUB_URL.txt` 第一行
`https://github.com/Very12345/pku-efficiency-3/tree/main/target/challenge-98e5a474-v2`，
第二行给出本作品相对路径；发布代理将覆写并保证未登录可访问。

## 对照口径提示

"白板/基础 Agent 对照"由平台执行。本包在自身夹具上保留的对照证据：
`TEST.md` 记录了同一示例三遍复跑 + 失败用例的异常路径输出 + 确定性
双跑 sha 对拍，供评审按相同输入/画布/导出参数复核稳定增益。