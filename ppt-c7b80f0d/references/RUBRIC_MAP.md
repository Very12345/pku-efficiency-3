# RUBRIC_MAP.md — 五维评分 → 本包设计覆盖

官方题面评分维度（每题 100 分 + GitHub 公开链接附加 5 分）与本题交付要求
（可编辑演示文件 / 页级证据映射 / 渲染与版本记录）逐项映射到本 Skill 的
实现位置。自查时逐行核对，保证"文字自述不替代实际运行证据"。

| 评分维度 | 分值 | 评分点 | 本包覆盖（证据位置） |
|-|-|-|-|
| 实际效果 | 40 | 任务完成度 15 | `SKILL.md` 执行步骤 S1–S6：读实际文件→抽主线→页序叙事骨架→可编辑 .pptx→渲染→result.json；`scripts/main.py` 端到端；`examples/` 最小案例跑通 |
| | | 结果正确性 15 | 页级主张与图表编号对齐：`deck-spec.json` 每个 slide 的 `claim/figure/table/evidence` 结构（`references/TEMPLATE_GUIDE.md` §3）；数字/单位不改写：OUTPUT_CONTRACT 诚实性硬约束 §4；图缺失=显式占位，禁止冒名；`scripts/validate.py` 校验一致性 |
| | | 结果完整性 5 | 必需页齐全：标题/主线/证据/结论/证据映射页由 `deck_builder.py` 全自动补齐；六类要素（主线、页结构、图表引用、讲解逻辑、模板约束、导出渲染）分别映射见下表 |
| | | 结果可核验性 5 | `evidence_mapping.md` 页级定位 + `references/OUTPUT_CONTRACT.md` + 预览 PNG + validate.py 可复跑；每页证据条目进 result.json |
| 使用增益 | 25 | 质量增益 15 | 与"不加载 Skill"的差异点：页级主张化改造（claim 字段强制）、长段落→短语改写（bullets 上限+短语约束）、备注与页面文字分离生成（notes 字段独立写入 notes_slide）、模板占位符约束排版（layout 按名匹配+placeholder-fill-only 保护）；对照白板由平台产生，本包不预写答案 |
| | | 效率增益 5 | 一键 `main.py --case --spec --out`；`--demo` 骨架快速验证；脚本总时长 <10s（小 deck）；人工修改页数下降来自 overflow_guard + 模板适配自动回退 |
| | | 增益可验证性 5 | `TEST.md` 同输入重复运行记录；`scripts/validate.py --case` 契约回显校验；预览+evidence map 均落盘可查 |
| 创新增益 | 15 | 新增能力 5 | ① PDF 实际抽取（pdf_extract.py，fitz→pypdf→pdfplumber 逐级回退）② 页级图表定位与占位保护（figure ref 缺失→占位框而非伪造图）③ 模板占位符约束排版（layout 名匹配+master 不动）④ 备注/页面内容分离生成（notes_separated=true）⑤ 从论文表格数字"重建图"（reconstructed_chart：PNG+可编辑 SVG，matplotlib 可选） |
| | | 方法改进 5 | 主线五段式骨架（问题→方法→证据→结论→局限）→ 页序 not 段落切片；证据映射页由 spec 证据自动生成；正确性由"引用必须带 paper 定位字段"结构性强制 |
| | | 创新证据 5 | `references/RUBRIC_MAP.md` 本表 + `TEST.md` 实测记录 + `examples/` 最小案例文件，均随包可复核 |
| 可靠体验 | 10 | 调用与易用性 3 | SKILL.md 触发词（name/description frontmatter）+ 三步调用（读案例→写 spec→跑 main.py）；README.md 完整步骤；相对技能根自定位，无硬编码绝对路径 |
| | | 运行稳定性 4 | 三级库回退（PDF/字体/图表）；模板不可读→内置版式回退并记录；缺失/损坏输入→诚实 failed/partial 而非崩溃；deque 可重复运行（smoke 两遍测试） |
| | | 异常处理 3 | SKILL.md S7 异常表：图表无法提取、公式为图片、PDF 加密、模板占位符不足、字体缺失、页数超限、材料缺失；每种→识别+处置+记录 |
| 生态贡献 | 10 | 文档完整性 3 | README.md（方法/依赖/限制/失败处理）+ references/ 三份契约/指南 + TEST.md |
| | | 资源可复用性 4 | 脚本可独立运行（均有 `if __name__=='__main__'` CLI）；`deck-spec.json` schema 即页级大纲模板（TEMPLATE_GUIDE.md §3）；evidence_mapping 模板；内置学术版式（ACADEMIC_THEME）可直接套用 |
| | | 分享推广价值 3 | 最小案例（examples/）+ 灰度示例产物（标注"示例，非正式案例"）+ GITHUB_URL.txt 公开链接（发布代理覆写） |
| GitHub 附加 | 5 | 公开作品链接 | `GITHUB_URL.txt` 第一行仓库链接；发布代理最终覆写并验证可公开访问 |

## 六类要素覆盖速查

| 题面要素 | 实现 |
|-|-|
| 1 主线提取 | spec.meta + slides 数组顺序即叙事骨架；`spec_from_case_meta` 只在 DEMO 模式生成骨架 |
| 2 页结构与信息分层 | bullet 短语化约束（MAX_BULLETS/MAX_CHARS_BULLET）+ claim 一言主张 + 层级 level |
| 3 图表引用与证据保留 | figure/table/evidence 字段带 ref+page+quote；缺失显式标注 |
| 4 讲解逻辑与备注 | notes 字段→notes_slide，字段值存"过渡/强调/被问补充"，与页面文字分离 |
| 5 模板约束与版面适配 | 组织方模板 placeholder-fill-only；layout 名关键词匹配→索引回退→内置版式 |
| 6 导出渲染与可编辑性 | .pptx 可编辑源 + PIL 近似预览（诚实标注）+ matplotlib PNG/SVG 图 + validate.py 重开校验 |