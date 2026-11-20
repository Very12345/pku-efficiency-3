# RUBRIC_MAP.md — 五维评分 → 本 Skill（v2）设计覆盖

原题满分 100（实际效果 40 / 使用增益 25 / 创新增益 15 / 可靠体验 10 / 生态贡献 10），
另加 GitHub 公开作品链接 5 分。下表逐评分点标注本包内的**可执行覆盖**（文件/行为）
以及**自证方法**（运行记录见 `TEST.md`，机器门见 `references/QUALITY_GATES.md`）。

## 1. 实际效果（40）

| 评分点 | 分值 | v2 覆盖设计 | 证据/自证 |
|-|-|-|-|
| 任务完成度 | 15 | 端到端产出"可直接上台"材料：报告目标(`report_goal`)→成功标准；听众画像 → 背景/术语比例；叙事顺序 → 页计划（计划门 P3 校验冻结页数）；逐页主张+一句话讲稿；问答准备页与每题回答要点 | `scripts/scaffold_plan.py`、`templates/talk_config.json`、`scripts/main.py`；示例实测 12 页 deck + 每页备注 |
| 结果正确性 | 15 | 页内容逐字取自源材料（`quote`），**证据审计**逐字核验（`evidence_audit.py`）；数字可对源（`validate_result` 警告级）；图/表引用绑定源材料出现的引用号；结论强度与证据类型匹配（strong/medium/weak 自动判定 + P7 词法门） | `scripts/evidence.py`、`scripts/evidence_audit.py`、`scripts/validate_result.py` |
| 结果完整性 | 5 | 覆盖六方面：主线(`main_line`)、页结构(`pages`)、图表引用(`figure_ref`)、讲解逻辑(`one_liner`+`notes`)、模板约束(`template_used`/layout 复用)、导出渲染(`previews/`) | `main.py`/`finalize_result.py` 组装；`result.json` 自含 `audit` |
| 结果可核验性 | 5 | 每页 `evidence{source_file, section, line_no, locator, quote, strength}`；`evidence_map.json` 反向映射；`evidence_audit.json` 逐页审计；`change_records` 记录全部取舍 | `OUTPUT_CONTRACT.md` §2/§4；`validate_result.py` + `selftest.py` 复核 |

## 2. 使用增益（25）

| 评分点 | 分值 | v2 覆盖设计 | 证据/自证 |
|-|-|-|-|
| 质量增益 | 15 | 与"基础 Agent 逐段搬摘要"对照：叙事模板按听众/时长重排页序（组会/答辩/评审三套权重），一页一主张、每页有讲解一句话与备答，`qa` 备用页预埋追问；计划契约 + 计划门（P1–P8）确保"先定方案后生成" | `templates/talk_config.json`、`assets/plan.schema.json`、`scripts/validate_plan.py` |
| 效率增益 | 5 | 一条命令 `python scripts/main.py --case … --out …` 完成 抽取→计划门→.pptx→verify_deck→预览→证据审计→result.json→自检，人工返工面收敛到"改 `talk_plan.json`/`talk_config.json` 再跑" | `TEST.md` 实测单次运行时间与产出 |
| 增益可验证性 | 5 | 公平对照记录：同一案例输入，本包产出含逐页证据定位 + 每页审计条目的可编辑 deck；对照项（无 Skill）在 `README.md` 说明；运行记录落盘（`TEST.md`、`examples/output/self_check.json`、双跑确定性） | 平台 3 案例×3 复跑即基准对照；G9 确定性探针 |

## 3. 创新增益（15）

| 评分点 | 分值 | v2 覆盖设计 | 证据/自证 |
|-|-|-|-|
| 新增能力 | 5 | 听众适配（expert/familiar/lay → 背景比例 10/18/30%）、页级规划 + 计划契约门（`validate_plan` P1–P8）、问答预演（局限/强结果主张 → 追问 → 回答要点 → 备用页）自动生成 | `scaffold_plan.py::resolve_audience/build_question_bank`、`validate_plan.py` |
| 方法改进 | 5 | 叙事模板化（每汇报类型一套"块+权重+顺序"）；证据强度自动分级；图表引用绑定（按引用号匹配材料图片，无图时诚实占位）；**证据逐字审计**、**deck 机器校验**（打开/页数/备注/确定性命名）把"可溯源/可编辑"从承诺变成可查证据 | `scaffold_plan.py::_bind_figure`、`evidence_audit.py`、`verify_deck.py` |
| 创新证据 | 5 | 与"论文目录逐页搬运"的差异写在 `narrative_template.md`；输出可对照：同一材料在不同 `report_type` 下页结构与顺序不同（`talk_config.json` 三套配置可 diff）；计划门/审计产物落盘即创新证据 | `examples/` 输出、`plan_gates.json`/`evidence_audit.json`/`deck_audit.json` |

## 4. 可靠体验（10）

| 评分点 | 分值 | v2 覆盖设计 | 证据/自证 |
|-|-|-|-|
| 调用与易用性 | 3 | 触发词在 SKILL.md frontmatter `description`；一条命令全流程；SKILL.md 步骤化 + 自查清单 + 决策规则 D1–D14 + 检查点 CP1–CP5 | `SKILL.md` |
| 运行稳定性 | 4 | 无网络依赖、纯标准库 + python-pptx + Pillow；材料缺失/PDF 无解析器/模板缺失/页数冲突均有分支；重复运行确定性（无随机；G9 探针 + TEST 双跑） | `TEST.md` 两次运行记录与 sha |
| 异常处理 | 3 | 缺图→诚实占位；图坏→跳过并记录；PDF 无 pypdf→按未解析记录并降级 partial；模板缺失→内置主题；计划门未过→降级并记录（不中断产生 honest 结果）；导出/预览失败→仍写 result.json；全量表见 `references/FAILURE_MODES.md` | `main.py` 分支 + `change_records` 样例 + FAILURE_MODES.md |

## 5. 生态贡献（10）

| 评分点 | 分值 | v2 覆盖设计 | 证据/自证 |
|-|-|-|-|
| 文档完整性 | 3 | `README.md`（运行/依赖/限制/失败处理）、`references/OUTPUT_CONTRACT.md`、`references/RUBRIC_MAP.md`、`references/PLAN_CONTRACT.md`、`references/QUALITY_GATES.md`、`references/FAILURE_MODES.md`、`references/DECK_RULES.md`、`references/EVIDENCE_AUDIT.md`、`templates/slide-checklist-template.md`、`SKILL.md` 自含 | 本包文件清单（≤50 文本文件，G10 机器查） |
| 资源可复用性 | 4 | 可编辑模板与规则：`templates/talk_config.json`（改权重即改行为）、计划模式 `assets/plan.schema.json`（改模式即改校验）、信封模板 `assets/result.template.json`、模块化脚本（`evidence.py`/`scaffold_plan.py`/`evidence_audit.py` 等可独立 import/CLI）、`examples/` 最小用例 | `scripts/` 模块化导入与独立 CLI |
| 分享推广价值 | 3 | 汇报案例组织方法、问答准备经验、逐页核对清单、诚实降级规范沉淀于文档；`GITHUB_URL.txt` 提供公开链接 | `GITHUB_URL.txt`, `README.md`, `templates/slide-checklist-template.md` |

## 6. GitHub 链接（+5）

`GITHUB_URL.txt` 第一行 = 公开仓库链接，第二行 = 本作品相对路径。

## 7. 与基包 (build/challenge-20870c35) 的自评差距

| 维度 | v1 基包 | v2 加强包 |
|-|-|-|
| 计划先行 | planner 单文件 | scaffold_plan + **plan.schema.json + validate_plan（P1–P8 机器门）** |
| 证据可溯源性 | quote 承诺 + validate 警告级 | **逐页逐字审计**（evidence_audit）+ 数字对源 + 双形态映射 |
| 生成/校验分离 | deck_builder/render ↔ validate/contract | 增加 **verify_deck**（打开/页数/备注/命名/OPC）、**selftest**（G1–G10 全链路） |
| 可编辑性证据 | 无 | **确定性元素命名**（page-claim-NN …）+ deck_audit 机器证据 |
| 可靠性文档 | SKILL §6 表 | **failure-modes.md（20 项）** + quality-gates.md + 决策规则 D1–D14 |
| 确定性 | 未提 | G9 探针（内容投影 sha、剔除记录时间戳）+ TEST 双跑 sha 记录 |