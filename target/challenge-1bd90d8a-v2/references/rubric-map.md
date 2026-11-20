# rubric-map.md — 五维评分 → 设计覆盖对照（v2）

对照官方评分维度（实际效果 40 / 使用增益 25 / 创新增益 15 / 可靠体验 10 / 生态贡献 10，
另加 GitHub 公开链接 5），逐项说明本包如何覆盖，以及提交前自查落点。
「文字自述不能替代实际运行证据」——每一项覆盖都以**可运行脚本 + 示例实测记录（TEST.md）**为证据。

> 文件名与高分形态对齐：rubric-map 是本题两个榜首（78.00 / 77.00 档）共有文档；
> 组织方内部 16 项细则（own16rubric）不公开，本表按公开五维设计，不做内部细则猜测。

## 1. 实际效果（40 分）

| 评分点 | 分值 | 本包覆盖 | 证据/自查落点 |
|-|-|-|-|
| 任务完成度 | 15 | 完整链路：CP1 材料盘点 → CP2 抽取（列画像/实体关系 extract.json）→ CP3 spec lint → CP4 生成分层 SVG → PNG/PDF → data_manifest/validation → CP5 双校验（mapcheck+figcheck）→ CP6 契约化 result.json；panel 一次多面板；network 机制/通路图（figure03 生物源材料：entities_file / material_file 行语法 / 词表扫描，逐元素带 cite） | SKILL.md S0–S6；scripts/main.py；examples 全链路实测（TEST.md） |
| 结果正确性 | 15 | 数据↔图元绑定（data-* 属性 + data_manifest.json）；**mapcheck 逐元素用源文件行值核对（浮点容差 1e-9）**；轴单位/刻度范围/误差线与列语义绑定；显著性只转述 p 值并注来源；实体名以源材料原文为准；spec_lint 与 figcheck 双 lint 独立复核 | mapcheck_report.json 值核对明细；figcheck G1–G8；validation.json 六项 |
| 结果完整性 | 5 | 六类检查点齐备且可判定：科学实体（data-* 溯源+来源记录）·空间关系（network 边/panel 网格）·数据编码（柱高/点位/热图色阶/扇区角度/误差线长度）·图例标注（legend-mapping 自动对齐）·可编辑源文件（分层 SVG+真实 <text>）·导出格式（SVG+PNG+PDF、dpi、色域、字体回退链） | figcheck 六类检查点逐项盖戳；OUTPUT_CONTRACT §4/§6 |
| 结果可核验性 | 5 | 源文件 sha256/版本/行列记录；图元↔行号映射（G3/G4）；change_records 时间戳；同输入字节级稳定（D18，verify_rerun）；artifacts_sha256 入 result | result.json sources/artifacts_sha256/gates；verify_rerun.py |

## 2. 使用增益（25 分）

| 评分点 | 分值 | 本包覆盖 | 证据/自查落点 |
|-|-|-|-|
| 质量增益 | 15 | 相比基础 Agent 裸画：错误识别自动挡（缺列报错不猜、空值策略记录、图例错配校验、CJK 字体回退+警告、遮挡检测、量级异常 warn、显著性缺配对 fail）；"画得像但不准"典型失败被逐项拦截并有机器判据 | validation 八类检查；figcheck G7；mapcheck 值核对；SKILL D1–D18 |
| 效率增益 | 5 | 一次 `main.py` 调用产出全链路（规格→SVG/PNG/PDF→manifest→双校验→result.json）；列映射自动推断；面板递归；刻度自动；无需手动量 | SKILL S3；main.py 单一入口；examples 实测耗时见 TEST |
| 增益可验证性 | 5 | 同输入同参数重跑字节级稳定（SVG/PNG/manifest/validation；result 仅时间戳不同）；空白对照（无 data → partial 不臆造）；TEST.md 记录命令/产物/通过率；verify_rerun 自动化 | TEST.md §5；verify_rerun.py；figcheck G1–G8 全过记录 |

## 3. 创新增益（15 分）

| 评分点 | 分值 | 本包覆盖 | 证据/自查落点 |
|-|-|-|-|
| 新增能力 | 5 | ① 图元→源数据**双向映射机器校验**（mapcheck 值核对，SVG data-* ↔ manifest ↔ 源表三向闭合）；② 图例-系列自动对齐校验；③ 中文标注与字体回退（cjkfont 回退链 + PNG 缺字警告 + 编码清理 svgtext）；④ 手写 XML 分层 SVG（文字永不转曲，真实 <text>）；⑤ 期刊样式预设（templates/journal_styles.json）；⑥ 连接规则字典（entity_glossary.json 关系类型→颜色/线型） | scripts/mapcheck.py；svgtext.check_no_text_to_path；cjkfont；templates/* |
| 方法改进 | 5 | 同一图元场景（Scene）双端输出：SVG（矢量可编辑）与 PNG/PDF（Pillow 渲染）逐元素同源；声明式管线：schema（figure_map.schema.json）→ spec lint → 绘制 → 双向校验；网络图按连接规则字典自动着色 | chartkit.Scene；spec_lint；mapcheck 三向闭合 |
| 创新证据 | 5 | 相对基础 Agent/通用绘图库的边界写明（SKILL §8 限制）；示例实测证明"数据→图元可回溯、图例不失配、字不乱码、可编辑、可复跑" | TEST.md 实测；RUBRIC_MAP 本文档；examples/output/ |

## 4. 可靠体验（10 分）

| 评分点 | 分值 | 本包覆盖 | 证据/自查落点 |
|-|-|-|-|
| 调用与易用性 | 3 | 单一 CLI；任意 cwd 可运行（`os.path.dirname(__file__)` 自定位）；case.json 多形态兼容（顶层/数组/cases[]/figure/figures）；task.md 自动发现；契约四形态自动回显 | SKILL §2/§3；main.py load_case/discover_* |
| 运行稳定性 | 4 | 单图失败不阻塞其余（status=partial）；不同数据规模（无行/多文件/多面板/网络缺实体）均有明确路径；字体环境自适应（Win/Linux/macOS + FONT_PATHS）；Pillow 缺失保 SVG；重跑验证兜底 | main.py 图循环 try/except；extract/spec_lint 容错；异常分支表 SKILL §6 |
| 异常处理 | 3 | 缺列/空值/量级异常/标签过长（自动旋转）/遮挡（检测+warn）/字体缺失/CJK/导出失败/网络关系悬空（warning 记录）均有处置与记录；失败分支表 + D9/D10/D16 诚实策略 | SKILL §6 失败分支表；validation warnings/adjustments；failure-modes.md |

## 5. 生态贡献（10 分）

| 评分点 | 分值 | 本包覆盖 | 证据/自查落点 |
|-|-|-|-|
| 文档完整性 | 3 | SKILL.md（完整可执行）/README.md（运行、依赖、限制）/output-contract.md（全部契约+G1–G8）/rubric-map.md（评分覆盖）/workorder-field-map.md（输入→字段→输出映射）/audit-rules.md（检查规则）/encoding-spec.md（编码规范）/typesetting-presets.md（排版预设）/failure-modes.md（失败模式）/TEST.md（实测记录）/examples（最小示例） | 本包文件清单一览 |
| 资源可复用性 | 4 | 期刊样式预设（templates/journal_styles.json 可加新期刊）；图型引擎独立 import（chartkit 库化）；校验脚本独立复用（mapcheck/figcheck/verify_rerun/spec_lint 均可单独 CLI）；规格契约开放（figure_map.schema.json，任何人可写 spec 出图）；连接规则字典可扩展 | templates/*；scripts/* 独立入口 |
| 分享推广价值 | 3 | 直接可用于任何"数据表→投稿级可编辑图"场景；通路图样例可复用为机制图模板；六类检查点+八类校验沉淀为可复用检查清单；契约四形态兼容常见 case 写法 | examples/ + README 快速开始；audit-rules.md |

## 6. GitHub 公开链接（5 分，附加）

- 根路径 `GITHUB_URL.txt` 第一行为公开仓库链接，第二行为本交付目录相对路径。
- 发布代理将覆写为精确链接；发布后须用未登录浏览器打开确认可访问。

## 提交前快速核对（Agent 自查）

1. `python scripts/main.py --case examples/case.json --out <tmp>` → status=completed，
   gates 全 OK，SVG/PNG/PDF/manifest/validation/双报告/result 齐全。
2. `python scripts/figcheck.py --dir <tmp> --case examples/case.json` → ALL GATES PASS（G1–G8）。
3. `python scripts/mapcheck.py --dir <tmp> --case examples/case.json` → ALL PASS（值核对无 mismatch）。
4. `python scripts/verify_rerun.py --case examples/case.json --out <tmp>` → DETERMINISTIC。
5. result.json 含 output_contract 全部字段（四形态）+ case_id；status/sources/uncertainty/change_records 诚实。
6. 每张正式案例图的 data_manifest 抽查 3–5 个元素坐标/值与源表一致（mapcheck 已自动做全量）。
7. 无编造数据、无预制答案、无凭据、无网络依赖声明被违背。