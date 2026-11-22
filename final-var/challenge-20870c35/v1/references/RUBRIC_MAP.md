# RUBRIC_MAP.md — 五维评分逐条映射（v1 决策显性化版）

原题满分 100：**实际效果 40 / 使用增益 25 / 创新增益 15 / 可靠体验 10 / 生态贡献 10**，
另加 GitHub 公开作品链接附加分 5。本版新增的不是功能，而是**决策层**：规则、分支、
状态矩阵与一个把状态一致性变成退出码的检查器。下表把每个评分点落到**本包的具体文件或机制**，
并给出**复跑命令**（全部机器判定，不靠文字自述）。实测记录见 [TEST.md](TEST.md)。

> 读法：第 1 列 = 题面评分点；第 2 列 = 本包落点（可在包内打开）；第 3 列 = 怎么自己验证。

## 1. 实际效果（40 分）

| 评分点 | 分 | 本包落点 | 复跑/判定 |
|-|-|-|-|
| 任务完成度 | 15 | 一条命令闭环：`scripts/main.py`（CP1 输入契约 → CP2 计划门 → CP3 生成门 → CP4 渲染门 → CP5 审计收口）；页数由 `templates/talk_config.json`（听众 × 时长）推导并**校准到任务冻结页数**（P3 门）；每页讲稿备注与 `qa` 备用页 | `python "$SKILL_DIR/scripts/main.py" --case examples/case.json --out OUT` → 退出码 0；`plan_gates.gates[P3]` 显示 `pages=12 target=12` |
| 结果正确性 | 15 | 页内容逐字取自源材料（`claim`/`quote`）；`scripts/evidence_audit.py` 逐页**逐字**核验并检查行号落在章节区间；数字不在源文本逐字出现 → 警告级列出；证据强度按词法门分级（strong/medium/weak，P7） | `TEST.md` §7：`audit.evidence.summary{content_pages:10, ok_pages:10, errors:0}`；`validate` 10/10 checks ok |
| 结果完整性 | 5 | 六个方面齐备：主线 `main_line`、页结构 `pages`、图表引用 `figure_ref/figure_file`、讲解逻辑 `one_liner`+`notes`、模板约束 `artifacts.deck_mode/template_used`、导出渲染 `previews/` + `preview_manifest.json` | `result.json` 直接可查；清单见 `examples/EXPECTED-OUTPUT.md` |
| 结果可核验性 | 5 | 每页 `evidence{source_file, section, line_no, locator, quote, strength}`；`evidence_map.json` 反向映射；`evidence_audit.json` 逐页审计；三道审计随结果内嵌 `result.audit{plan_gates,evidence,deck,gates}`；**取舍与降级全量记 `change_records`**（D20 要求冲突时全部命中项留痕） | `validate_result.py` / `evidence_audit.py` / `verify_deck.py` 退出码 0；`selftest.py` 全链路 |

## 2. 使用增益（25 分）

| 评分点 | 分 | 本包落点 | 复跑/判定 |
|-|-|-|-|
| 质量增益 | 15 | 与"基础 Agent 逐段搬摘要"的**逐项可判定差异**见 `COMPARE.md`（13 行对照表）；实现落点：三套叙事模板（组会/答辩/评审）、一页一主张 + 证据强度、每页【主张/证据/讲解/备答】备注、`qa` 备用页预埋追问、**计划契约先行**（`assets/plan.schema.json` + `validate_plan.py` P1–P8） | 同材料改 `report_type` 后 `talk_plan.json` 的 `narrative.order_blocks` 与 `audience.background_ratio` 随之变化（可 diff） |
| 效率增益 | 5 | 一条命令完成 抽取→计划门→deck→校验→预览→审计→result→自检；返工面收敛为"改 `talk_plan.json`/`talk_config.json` 再跑"；`--skip-previews` 可再省时间 | `TEST.md` §3/§5：单次运行约 1.6–3.1 秒；命令数 = 1 |
| 增益可验证性 | 5 | **不自报分数**：对照由平台在固定 3 案例上执行；本包给出 A/B 口径与**不利于本包的对照结果**（`COMPARE.md` §4）；同输入双跑确定性由 `self_check.determinism` 证明 | `TEST.md` §6：4 个 JSON 逐字节相同、12 张 PNG 逐字节相同、投影 sha 相同 |
| 降级下的增益可见性 | （并入上两项） | 依赖缺失/材料异常时仍产出可用部分，且**状态与记录一致**——不出现"零产物"或"假成功" | `TEST.md` §5（T5/T6）：两条降级路径均退出码 0、`status=partial`、检查器判定自洽 |

## 3. 创新增益（15 分）

| 评分点 | 分 | 本包落点 | 复跑/判定 |
|-|-|-|-|
| 新增能力 | 5 | ① **听众适配**（`expert/familiar/lay` → 背景/术语页占比 10/18/30%）；② **页级规划 + 计划契约门**（schema 驱动的 P1–P8）；③ **问答预演**（每条局限/风险与 strong 结果生成追问→回答要点→`qa` 备用页）；④ **本版新增：状态矩阵 + 机器检查器**——把"`status` 是否与文件内容一致"变成 13 条规则与退出码 | `plan_gates.json` P1–P8；`pages[]` 中 `block=qa`；`check_status_matrix.py` 正/负例见 `TEST.md` §4 |
| 方法改进 | 5 | ① 叙事模板化（"块+权重+顺序"配置驱动）；② 证据逐字审计；③ deck 机器校验（打开/页数/备注/命名/OPC/规范化 sha）；④ 运行时资源生成（示例二进制不随包）；⑤ 产物路径净化（本机绝对路径写盘前改写成相对形式） | `evidence_audit.json` / `deck_audit.json` / `preview_manifest.json`；包内 grep 盘符绝对路径无命中 |
| 创新证据 | 5 | 与"论文目录逐页搬运"的差异写在 `templates/narrative_template.md`；计划门/证据审计/deck 审计/确定性探针**落盘即证据**；**决策规则与优先级裁决**（`SKILL.md` §4/§5、`references/decision-rules.md`）给出每条规则的代码位置与落点字段 | `COMPARE.md` §1/§4；`examples/output/result.example.json` 的 `audit` 三段；`decision-rules.md` 的"代码位置"列 |

## 4. 可靠体验（10 分）

| 评分点 | 分 | 本包落点 | 复跑/判定 |
|-|-|-|-|
| 调用与易用性 | 3 | 触发判据表（`SKILL.md` §1：命中几条即触发）；**自定位**（`$SKILL_DIR` + `os.path.dirname(__file__)`，cwd 任意）；一条命令全流程；执行顺序表给出每个检查点的进入/出口条件 | `TEST.md` §3/§5：所有命令在包外 cwd 执行且退出码符合预期 |
| 运行稳定性 | 4 | 无网络依赖；必需依赖仅 python-pptx + Pillow（+ 可选 pypdf）；**缺依赖不崩**（D15，命令仍返回 0）；材料缺失/空材料/PDF 无解析器/无模板/模板自带页/预览失败各有分支；重复运行确定性 | `TEST.md` §5/§6：两条降级路径 + 双跑一致 |
| 异常处理 | 3 | **五族失败分支表**（B-M/B-T/B-D/B-C/B-S）+ 决策规则 D1–D20 + **优先级裁决**（D20）+ 状态判定矩阵（§6）+ 反向约束（禁虚报完成、禁伪降级）；退出码语义 0/1/2 明确；`uncertainty` 每条含 `item/impact/mitigation` | `references/failure-modes.md` 全表；`TEST.md` §4/§5；`check_status_matrix.py`（13 条规则） |

## 5. 生态贡献（10 分）

| 评分点 | 分 | 本包落点 | 复跑/判定 |
|-|-|-|-|
| 文档完整性 | 3 | `SKILL.md`（触发判据/执行顺序/规则表/分支表/状态矩阵/合规）、`README.md`（快速开始/依赖/规则速查/维护）、`TEST.md`（可复现命令与观测值）、`COMPARE.md`（对照口径）、`references/` 八份规范（**新增 `decision-rules.md`**）、`examples/` 说明与预期输出清单 | 文件清单见 `README.md` 首段；`selftest.py --package-check` 报文件数 |
| 资源可复用性 | 4 | 可编辑规则：`templates/talk_config.json`（改权重即改行为）、`assets/plan.schema.json`（改模式即改校验）；`scripts/` 15 个模块可独立 CLI；**本版新增 `check_status_matrix.py` 可被任何产出 `result.json` 的同类 Skill 直接复用**（规则集与实现分离）；`templates/slide-checklist-template.md`（上台前逐页核对） | 各脚本 `--help` / 独立 CLI；`TEST.md` §4/§7 独立复核 |
| 分享推广价值 | 3 | 沉淀"从材料到可讲页面"的页级组织方法、问答准备经验、证据审计规范、**五族失败分支与状态矩阵**（可直接移植到别的 Skill 包）、**资源形态合规做法**（§9 与 `TEST.md` §8）；`GITHUB_URL.txt` 提供公开链接 | `GITHUB_URL.txt`；`SKILL.md` §9/§10；`references/failure-modes.md` §7 |

## 6. GitHub 公开链接（+5）

`GITHUB_URL.txt` 第一行为作品所在目录链接（评审无需登录即可打开）。

## 7. 本版相对基线的实质增改（逐条）

| 类型 | 内容 |
|-|-|
| 新增文件 | `references/decision-rules.md`（D1–D20 全文 + 优先级裁决 + 代码位置 + 与 F 表映射）、`scripts/check_status_matrix.py`（13 条规则的状态一致性检查器） |
| 重写文件 | `SKILL.md`（改为决策式结构：触发判据 → 执行顺序表 → 规则表 → 优先级 → 状态矩阵 → 五族分支）、`references/failure-modes.md`（从平铺编号改为五族分支 + 一致性规则 + 实测证据）、`README.md`（规则速查 + 维护口径）、`TEST.md`（新增状态矩阵正/负例与两条降级路径实测） |
| 补充说明 | `references/OUTPUT_CONTRACT.md` 仅重写页首说明并新增 §7（决策规则 ↔ 字段对照）；**§1–§6 的字段块逐字未动** |
| 未改动 | `scripts/` 既有 14 个脚本、`templates/`、`assets/`、`examples/`、`COMPARE.md` —— 算法与 CLI 接口保持不变 |
