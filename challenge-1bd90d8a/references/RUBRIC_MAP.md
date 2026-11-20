# RUBRIC_MAP — 五维评分 → 设计覆盖对照

对照官方评分维度（实际效果 40 / 使用增益 25 / 创新增益 15 / 可靠体验 10 / 生态贡献 10，
另加 GitHub 公开链接 5），逐项说明本包如何覆盖，以及提交前 Agent 的自查落点。
「文字自述不能替代实际运行证据」——每一项的覆盖都以**可运行脚本 + 示例实测记录（TEST.md）**为证据。

## 1. 实际效果（40 分）

| 评分点 | 分值 | 本包覆盖 | 证据/自查落点 |
|-|-|-|-|
| 任务完成度 | 15 | 完整链路：读 case.json → 发现数据 → 抽列映射 → 生成分层 SVG → PNG/PDF → manifest/validation/result.json；panel 支持一次出多面板；network 支持机制/通路图（figure03 生物源材料：从文献文本抽实体关系，逐元素带 cite 来源） | SKILL.md S0–S5；scripts/main.py；examples 全链路实测（TEST.md） |
| 结果正确性 | 15 | 数据↔图元绑定（data-* 属性 + data_manifest.json）；轴单位/刻度范围/误差线与列语义绑定；显著性只转述 p 值并注来源；实体名以源材料原文为准；异步校验脚本独立复核 | validation.json 的 provenance/axis-units/significance 检查；validate_result.py 复算 |
| 结果完整性 | 5 | 六类检查点齐备：科学实体（data-* 溯源）· 空间关系（network 边/panel 布局）· 数据编码（柱高/点位/热图色阶/扇区角度/误差线长度）· 图例标注（legend-mapping 自动对齐）· 可编辑源文件（分层 SVG）· 导出格式（SVG+PNG+PDF、dpi、字体族回退） | OUTPUT_CONTRACT.md §1/§3/§4；示例含 bar+line panel 与 network 两类 |
| 结果可核验性 | 5 | 源文件 sha256/版本/行列记录；图元↔行号映射；change_records 时间戳；同输入字节级稳定（无随机） | result.json sources + change_records + environment；D12 |

## 2. 使用增益（25 分）

| 评分点 | 分值 | 本包覆盖 | 证据/自查落点 |
|-|-|-|-|
| 质量增益 | 15 | 相比基础 Agent 裸画：错误识别自动挡（缺列报错不猜、空值策略记录、图例错配自动校验、CJK 字体回退 + 警告、遮挡检测、量级异常 warn）；"画得像但不准"的典型失败在此被逐项拦截 | SKILL.md D1–D12；validation.json 检查项（8 类）；示例中 bar 数值-柱高比例实测 |
| 效率增益 | 5 | 一次 `main.py` 调用产出全链路（规格→SVG/PNG/PDF→manifest→校验→result.json）；列映射自动推断；面板递归；无需手动量刻度 | SKILL.md S3；scripts/main.py 单一入口 |
| 增益可验证性 | 5 | 同输入同参数重跑字节级稳定；空白对照（无 data 文件 → partial 不臆造）；示例与 TEST.md 记录命令、产物、通过率 | TEST.md；validate_result.py 29/29 类检查 |

## 3. 创新增益（15 分）

| 评分点 | 分值 | 本包覆盖 | 证据/自查落点 |
|-|-|-|-|
| 新增能力 | 5 | ① 图元→源数据双向映射（SVG data-* 属性 ↔ data_manifest.json，svg_id 对齐）；② 图例-系列自动对齐校验；③ 中文标注字体回退（SVG 回退链 + PNG 缺字警告）；④ 手写 XML 分层 SVG（非转曲、非位图，可编辑）；⑤ 期刊样式预设可复用 | OUTPUT_CONTRACT.md §4；figure_engine.py `_prim_attrs`/`scene_to_svg`；styles/presets.json |
| 方法改进 | 5 | 同一图元场景（Scene）双端输出：SVG（矢量编辑）与 PNG/PDF（Pillow 渲染）**逐元素同源**，避免"矢量好看位图不同"；面板复用同一引擎；网络图按 type 自动着色（激活/抑制/磷酸化/转录） | figure_engine.py Scene 设计；示例 PNG↔SVG 一致性验证 |
| 创新证据 | 5 | 相对基础 Agent/通用绘图库的边界写明（SKILL.md §7 限制）；示例实测证明"数据→图元可回溯、图例不失配、字不乱码、可编辑" | TEST.md 实测记录；RUBRIC_MAP 本文档 |

## 4. 可靠体验（10 分）

| 评分点 | 分值 | 本包覆盖 | 证据/自查落点 |
|-|-|-|-|
| 调用与易用性 | 3 | 单一 CLI；任意 cwd 可运行（`os.path.dirname(__file__)` 自定位）；case.json 多形态兼容（顶层/数组/cases[]/figure/figures）；task.md 自动发现 | SKILL.md §2/§3；main.py `load_case/discover_*` |
| 运行稳定性 | 4 | 单图失败不阻塞其余（status=partial）；不同数据规模（无行/多文件/多面板）均有明确路径；字体环境自适应（Windows/Linux/macOS 字体目录 + FONT_PATHS）；Pillow 缺失时保 SVG | main.py 图循环 try/except；FontMap；异常分支表 SKILL.md §5 |
| 异常处理 | 3 | 缺列/空值/量级异常/标签过长（自动旋转）/遮挡（检测+warn）/字体缺失/CJK/导出失败均有处置与记录；失败分支表 + D9/D10 诚实策略 | SKILL.md §5 失败分支表；validation.json warnings/adjustments |

## 5. 生态贡献（10 分）

| 评分点 | 分值 | 本包覆盖 | 证据/自查落点 |
|-|-|-|-|
| 文档完整性 | 3 | SKILL.md（完整可执行）/README.md（运行、依赖、限制、失败处理）/OUTPUT_CONTRACT.md（全部契约）/RUBRIC_MAP.md（评分覆盖）/TEST.md（实测记录）/examples（最小示例） | 本包文件清单一览 |
| 资源可复用性 | 4 | 期刊样式预设（styles/presets.json 可加新期刊）；图型引擎可独立 import（figure_engine.py 库化）；校验脚本独立复用；规格契约开放（任何人可写 spec 出图） | OUTPUT_CONTRACT.md §5；figure_engine 库接口 |
| 分享推广价值 | 3 | 直接可用于任何"数据表→投稿级可编辑图"场景；生物机制图样例可复用为通路图模板；示例与契约让新用户 5 分钟上手 | examples/ + README 快速开始 |

## 6. GitHub 公开链接（5 分，附加）

- 根路径 `GITHUB_URL.txt` 第一行为公开仓库链接，第二行为本交付目录相对路径。
- 发布代理将覆写为精确链接；发布后须用未登录浏览器打开确认可访问。

## 提交前快速核对（Agent 自查）

1. `python scripts/main.py --case examples/case.json --out <tmp>` → status=completed，SVG/PNG/PDF/manifest/validation/result 六件齐。
2. `python scripts/validate_result.py --dir <tmp> --case examples/case.json` → 全部 PASS。
3. result.json 含 output_contract 全部字段 + case_id；uncertainty/change_records 诚实。
4. 每张正式案例图的 data_manifest 抽查 3–5 个元素坐标/值与源表一致。
5. 无编造数据、无预制答案、无凭据、无网络依赖声明被违背。