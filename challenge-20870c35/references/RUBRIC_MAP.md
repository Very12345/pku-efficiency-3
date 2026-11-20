# RUBRIC_MAP.md — 五维评分 → 本 Skill 设计覆盖

原题满分 100（实际效果 40 / 使用增益 25 / 创新增益 15 / 可靠体验 10 / 生态贡献 10），
另加 GitHub 公开作品链接 5 分。下表逐评分点标注本包内的**可执行覆盖**（文件/行为），
以及对应的**自证方法**（运行记录见 `TEST.md`）。

## 1. 实际效果（40）

| 评分点 | 分值 | 覆盖设计 | 证据/自证 |
|-|-|-|-|
| 任务完成度 | 15 | 端到端产出"可直接上台"材料：报告目标(`report_goal`)→成功标准；听众画像 → 背景/术语比例；叙事顺序 → 页计划；逐页主张+一句话讲稿；问答准备页与每题回答要点 | `scripts/planner.py`, `templates/talk_config.json`, `scripts/main.py`；本机实测产出 12 页 deck + 讲稿备注 |
| 结果正确性 | 15 | 页内容逐字取自源材料（`quote`），数字可对源（`validate_result` 警告级校验）；图/表引用绑定源材料出现的引用号；结论强度与证据类型匹配（strong/medium/weak 自动判定） | `scripts/evidence.py`；`scripts/validate_result.py` 的 numbers-traceable 检查 |
| 结果完整性 | 5 | 覆盖六方面：主线(`main_line`)、页结构(`pages`)、图表引用(`figure_ref`)、讲解逻辑(`one_liner`+`notes`)、模板约束(`template_used`/layout 复用)、导出渲染(`previews/`) | `main.py` 的 result.json 组装；`self_check.json` |
| 结果可核验性 | 5 | 每页 `evidence{source_file, section, line_no, locator, quote, strength}`；`evidence_map.json` 反向映射；`change_records` 记录全部取舍 | `OUTPUT_CONTRACT.md` §2；`validate_result.py` 校验证据源都声明在 `sources` |

## 2. 使用增益（25）

| 评分点 | 分值 | 覆盖设计 | 证据/自证 |
|-|-|-|-|
| 质量增益 | 15 | 与"基础 Agent 逐段搬摘要"对照：叙事模板按听众/时长重排页序（组会/答辩/评审三套权重），一页一主张、每页有讲解一句话与备答，`qa` 备用页预埋追问 | `templates/talk_config.json` 可对比不同 `report_type` 的页分配 |
| 效率增益 | 5 | 一条命令 `python scripts/main.py --case … --out …` 完成 抽取→规划→.pptx→预览→result.json→自检，人工返工面收敛到"改 `talk_plan.json`/`talk_config.json` 再跑" | `TEST.md` 实测单次运行时间 |
| 增益可验证性 | 5 | 公平对照记录：同一案例输入，本包产出含逐页证据定位的可编辑 deck；对比项（无 Skill）在 `README.md` 说明；全部运行记录落盘（`TEST.md`、`examples/sample-output/self_check.json`） | 平台 3 案例×3 复跑即基准对照 |

## 3. 创新增益（15）

| 评分点 | 分值 | 覆盖设计 | 证据/自证 |
|-|-|-|-|
| 新增能力 | 5 | 听众适配（expert/familiar/lay → 背景比例 10/18/30%）、页级规划（`planner.py` 页预算分配）、问答预演（局限/强结果主张 → 追问 → 回答要点 → 备用页）自动生成 | `planner.py::resolve_audience/build_question_bank` |
| 方法改进 | 5 | 叙事模板化（每汇报类型一套"块+权重+顺序"，存 `templates/talk_config.json` 可编辑）；证据强度自动分级；图表引用绑定（`_bind_figure` 按引用号匹配材料图片，无图时诚实占位） | `planner.py::_bind_figure`、`templates/talk_config.json` |
| 创新证据 | 5 | 与"论文目录逐页搬运"的差异写入 `narrative_template.md`；输出可对照：同一材料在不同 `report_type` 下页结构与顺序不同 | `examples/` 两套示意可对照 |

## 4. 可靠体验（10）

| 评分点 | 分值 | 覆盖设计 | 证据/自证 |
|-|-|-|-|
| 调用与易用性 | 3 | 触发词在 SKILL.md frontmatter `description`；一条命令全流程；`SKILL.md` 步骤化 + 自查清单 | `SKILL.md` |
| 运行稳定性 | 4 | 无网络依赖、纯标准库 + python-pptx + Pillow；材料缺失/PDF 无解析器/模板缺失均有分支；重复运行确定性（无随机） | `TEST.md` 两次运行记录 |
| 异常处理 | 3 | 缺图→诚实占位；图分辨率/格式坏→跳过并记录；PDF 无 pypdf→按未解析记录并降级 partial；模板缺失→内置主题；导出/预览失败→仍写 result.json（status/uncertainty/change_records 如实） | `main.py` try/except 分支 + `change_records` 样例 |

## 5. 生态贡献（10）

| 评分点 | 分值 | 覆盖设计 | 证据/自证 |
|-|-|-|-|
| 文档完整性 | 3 | `README.md`（运行/依赖/限制/失败处理）、`references/OUTPUT_CONTRACT.md`、`references/RUBRIC_MAP.md`、`templates/narrative_template.md`、`SKILL.md` 自含 | 本包文件清单 |
| 资源可复用性 | 4 | 可编辑模板与规则：`templates/talk_config.json`（改权重即改行为）、页级规划器与证据抽取器独立成模块（`planner.py`/`evidence.py` 可单独 import）、`examples/` 最小用例 | `scripts/` 模块化导入 |
| 分享推广价值 | 3 | 汇报案例组织方法、问答准备经验、诚实降级规范沉淀于文档；`GITHUB_URL.txt` 提供公开链接 | `GITHUB_URL.txt`, `README.md` |

## 6. GitHub 链接（+5）

`GITHUB_URL.txt` 第一行 = 公开仓库链接（发布代理覆写为精确链接），第二行 = 本作品相对路径。