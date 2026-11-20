# rubric-map.md — 五维评分 → 本包设计覆盖（v2）

官方题面评分维度（实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 ·
生态贡献 10 + GitHub 附加 5）与本题交付要求（可编辑演示文件 / 页级证据映射 /
渲染与版本记录）逐项映射到本 Skill v2 的实现位置。自查时逐行核对——
**文字自述不替代实际运行证据**，每条"覆盖"都对应可运行脚本或已落盘文档。

## 1. 五维映射表

| 评分维度 | 分值 | 评分点 | 本包覆盖（v2 证据位置） |
|-|-|-|-|
| 实际效果 | 40 | 任务完成度 15 | `SKILL.md` 执行流程 S0–S6 + 决策规则 D1–D10；`scripts/main.py` 端到端（CP1 lint → assetkit 抽取 → deckgen 构建 → 导出检查）；本机 smoke（TEST.md T2）跑通 8 页 deck，status=completed |
| | | 结果正确性 15 | 页级主张/图表编号对齐：deck-spec 每页 `claim/figure/table/evidence`（`references/slide-blueprint.md` §3）；数字单位不改写：`references/result-contract.md` §4；图缺失=显式占位（deckgen `_place_figure`，绝不冒充原图）；`scripts/export_check.py` G 门校验 |
| | | 结果完整性 5 | 必需页齐全：封面/主线/证据/结论/证据映射页自动补齐（deckgen `auto_outline/auto_evidence_slide`）；六类要素覆盖见本表尾部"六要素速查" |
| | | 结果可核验性 5 | **逐页证据映射表**：`evidence_mapping.md`（人读）+ `evidence_map.json`（机器读）+ 每页证据进 result.json；导出件可复核：preview PNG + export_check 可复跑 |
| 使用增益 | 25 | 质量增益 15 | 与"不加载 Skill"的差异：页级主张化（claim 字段强制 + `spec_lint` BL-1）、长段落→短语（BL-2 + overflow_guard）、备注与页面文字分离（notes_slide，含封面/收尾页）、模板占位符约束（placeholder-fill-only）；对照白板由平台产生，本包不预写答案 |
| | | 效率增益 5 | 一键 `main.py --case --spec --out`；`--demo` 骨架快速验证；脚本总时长 <10s（小 deck）；人工修改下降来自 overflow_guard + 模板自动回退 + 形状命名（对象按名可找） |
| | | 增益可验证性 5 | TEST.md 同输入重复运行记录；`export_check.py --case` 契约回显校验；预览 + 双形态证据映射均落盘 |
| 创新增益 | 15 | 新增能力 5 | ① PDF 实际抽取（`assetkit.extract_pdf`，fitz→pypdf→pdfplumber 逐级回退）② 页级图表定位与占位保护 ③ 模板占位符约束（layout 名匹配 + master 不动）④ 备注/页面分离（notes_separated=true）⑤ 从论文表格重建图（PNG+可编辑 SVG）⑥ **OOXML 层精修**：主题字体注入 + 分层命名（`ooxml_kit`，新）⑦ **CP1 spec lint**（`spec_lint`，新）⑧ 导出检查器（OOXML 容器 + 命名审计 + 证据表一致性，`export_check`，新） |
| | | 方法改进 5 | 主线五段式蓝图（`slide-blueprint.md` §1 映射表）→ 页序非段落切片；证据映射页由 spec 自动生成；正确性由"引用必须带论文定位"结构性强制（BL-3） |
| | | 创新证据 5 | `references/rubric-map.md` 本表 + `references/layer-naming.md`（命名规范）+ TEST.md 实测 + examples 最小案例，均随包可复核 |
| 可靠体验 | 10 | 调用与易用性 3 | SKILL.md frontmatter 触发词 + 三步调用（读案例→写 spec→跑 main.py）；README.md 完整步骤；脚本相对技能根自定位，无硬编码绝对路径 |
| | | 运行稳定性 4 | 三级库回退（PDF/字体/图表）；模板不可读→内置版式回退并记录；输入缺失→诚实 failed/partial；CP1 lint 问题记录后继续（D4）；同 deck 两次运行对象名序列一致（layer-naming.md §5） |
| | | 异常处理 3 | SKILL.md §5 异常表（材料缺失/加密/扫描件/图抽不出/模板不可用/占位符不足/字体缺失/页数超限/重建图失败/spec 缺失）+ D 规则决策分支 |
| 生态贡献 | 10 | 文档完整性 3 | README.md + references/ 四份文档（result-contract/rubric-map/slide-blueprint/layer-naming）+ TEST.md + COMPARE.md（三方对照） |
| | | 资源可复用性 4 | 脚本可独立运行（均有 CLI）；deck-spec schema 即页级大纲模板（slide-blueprint.md §3）；蓝图映射表（§1）与逐页映射表格式（§2）可直接套用；内置学术版式（ACADEMIC_THEME）与 ooxml_kit 可平移到"PPT 生成与编辑/模板适配"两题 |
| | | 分享推广价值 3 | 最小案例（examples/）+ 示例产物（标注"示例，非正式案例"）+ GITHUB_URL.txt 公开链接（发布代理覆写） |
| GitHub 附加 | 5 | 公开作品链接 | `GITHUB_URL.txt` 第一行仓库链接；发布代理最终覆写并验证可公开访问 |

## 2. 六类要素覆盖速查（题面交付要求）

| 题面要素 | v2 实现 |
|-|-|
| 1 主线提取 | spec.meta + slides 数组即叙事骨架；`slide-blueprint.md` §1 蓝图映射；`spec_from_case_meta` 仅 DEMO |
| 2 页结构与信息分层 | bullet 短语化（spec_lint BL-2）+ claim 一言主张 + layout_hint 词表 |
| 3 图表引用与证据保留 | figure/table/evidence 带 ref+page+quote；缺失显式标注；**逐页映射表双形态** |
| 4 讲解逻辑与备注 | notes 字段→notes_slide（含封面/收尾页），存过渡/强调/被问补充，与页面文字分离 |
| 5 模板约束与版面适配 | 组织方模板 placeholder-fill-only；layout 名关键词匹配→索引回退→内置版式；主题字体注入 |
| 6 导出渲染与可编辑性 | .pptx 可编辑源（形状命名）+ PIL 近似预览（诚实标注）+ matplotlib PNG/SVG 重建图 + **export_check OOXML/容器/命名/证据表校验** |

## 3. 与 v1 相比的覆盖变化

- 新增：CP1 spec lint（把"每页主张/证据/BL 规则"从自述变成可执行门）；
- 新增：逐页证据映射表双形态（md + json）与导出检查器（OOXML 容器、命名审计、
  证据表行数一致性 G7）；
- 新增：OOXML 分层命名规范（layer-naming.md）与主题字体注入（换机不丢中文字体）；
- 强化：备注覆盖封面/收尾页；`uncertainty` 显式记录主题字体与 lint 偏差。