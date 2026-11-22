# RUBRIC_MAP.md — 五维评分逐条映射到本包的文件与机制

原题满分 100：**实际效果 40 / 使用增益 25 / 创新增益 15 / 可靠体验 10 / 生态贡献 10**
（另加 GitHub 公开作品链接附加分 5）。本文件把题面每个评分点落到**本包的具体文件或机制**上，
并给出**自证命令/字段**。运行记录见 `TEST.md`，对照方案见 `COMPARE.md`。

> 阅读顺序建议：先看本表第 1 列（题面评分点）→ 第 2 列（本包落点，均可在包内打开）→
> 第 3 列（怎么自己验证，全部是机器判定）。

## 1. 实际效果（40 分）

| 评分点 | 分 | 本包落点（文件 / 机制） | 自证 |
|-|-|-|-|
| 任务完成度 | 15 | 端到端一条命令 `scripts/main.py`：报告目标(`report_goal`)→听众画像→叙事顺序→页级计划→讲稿备注→问答准备**闭环**；`scripts/scaffold_plan.py` + `templates/talk_config.json`；页数按时长推导并**校准到任务冻结页数** | `TEST.md` T2：12 页 deck、每页备注；`plan_gates.gates[P3] pages=12 target=12` |
| 结果正确性 | 15 | 页内容逐字取自源材料 `claim`/`quote`；`scripts/evidence_audit.py` 逐页**逐字**核验并检查行号落在章节区间；数字不在源文本逐字出现 → 警告；结论强度按证据类型自动分级（strong/medium/weak，P7 词法门） | `TEST.md` T3c；`result.audit.evidence.summary{content_pages:10, ok_pages:10, errors:0}` |
| 结果完整性 | 5 | 六个方面齐备：主线 `main_line`、页结构 `pages`、图表引用 `figure_ref/figure_file`、讲解逻辑 `one_liner`+`notes`、模板约束 `artifacts.deck_mode/template_used`、导出渲染 `previews/` + `preview_manifest.json` | `result.json` 直接可核；`examples/EXPECTED-OUTPUT.md` 给出完整清单 |
| 结果可核验性 | 5 | 每页 `evidence{source_file, section, line_no, locator, quote, strength}`；`evidence_map.json` 反向映射；`evidence_audit.json` 逐页审计；**三道审计随结果内嵌** `result.audit{plan_gates,evidence,deck,gates}`；取舍过程全记 `change_records` | `scripts/validate_result.py` + `scripts/evidence_audit.py` 退出码 0；`selftest.py` 复核 |

## 2. 使用增益（25 分）

| 评分点 | 分 | 本包落点（文件 / 机制） | 自证 |
|-|-|-|-|
| 质量增益 | 15 | 与"基础 Agent 逐段搬摘要"的**逐项可判定差异**写在 `COMPARE.md`（13 行对照表）；实现落点：叙事模板三套（`templates/talk_config.json` 按组会/答辩/评审改块权重与顺序）、一页一主张 + 证据强度、每页【主张/证据/讲解/备答】备注、`qa` 备用页预埋追问、计划契约先行（`assets/plan.schema.json` + `scripts/validate_plan.py` P1–P8） | `COMPARE.md` §1 每行都指向 `result.json`/`talk_plan.json` 的可判定字段；同材料换 `report_type` 页序即变（可 diff） |
| 效率增益 | 5 | 一条命令完成 抽取→计划门→`.pptx`→`verify_deck`→预览→证据审计→`result.json`→自检；返工面收敛为"改 `talk_plan.json`/`talk_config.json` 再跑"；`--skip-previews` 可再省时间 | `TEST.md` T2/T6 实测单次约 1.6–3.1 秒；命令数=1 |
| 增益可验证性 | 5 | **不自报分数**（题面禁止文字自述替代运行证据）：对照由平台在固定 3 案例执行，本包提供 A/B 口径、判定命令与**不利于本包的对照结果**；同输入双跑确定性由 `self_check.determinism` 与 `scripts/selftest.py` 的 `determinism_probe` 证明 | `COMPARE.md` §2/§3/§4；`TEST.md` T4 双跑：JSON 逐字节相同、12 张 PNG 逐字节相同、投影 sha 相同 |
| 降级下的增益可见性 | （并入上两项） | 依赖缺失/材料异常时仍产出可用部分（`status=partial` + `deck_limitation` + `uncertainty`），不会"零产物" | `TEST.md` T8–T13 六条分支，含负例 T12 |

## 3. 创新增益（15 分）

| 评分点 | 分 | 本包落点（文件 / 机制） | 自证 |
|-|-|-|-|
| 新增能力 | 5 | ① **听众适配**：`expert/familiar/lay` → 背景/术语页占比 10/18/30%（`scaffold_plan.resolve_audience`）；② **页级规划 + 计划契约门**：`assets/plan.schema.json` 驱动的 P1–P8 机器门；③ **问答预演**：每条局限/风险与 strong 结果自动生成追问→回答要点→`qa` 备用页（`scaffold_plan.build_question_bank`） | `plan_gates.json` P1–P8 逐条；`pages[]` 中 `qa` 页；`talk_plan.json.audience.background_ratio` |
| 方法改进 | 5 | ① 叙事模板化（"块+权重+顺序"配置驱动）；② **证据逐字审计**（引文 vs 实际读取文本 + 行号区间 + 数字对源）；③ **deck 机器校验**（可打开/页数/备注/`page-claim-NN` 元素/OPC/规范化 sha）；④ **运行时资源生成**（示例二进制不随包，`scripts/make_synthetic_inputs.py`）；⑤ **产物路径净化**（`common.portable_path/sanitize_output`：本机绝对路径写盘前改写为相对形式，POSIX 运行期路径保留） | `evidence_audit.json` / `deck_audit.json` / `preview_manifest.json`；`examples/output/*.example.json` 中无盘符路径；包内 grep 盘符绝对路径无命中 |
| 创新证据 | 5 | 与"论文目录逐页搬运"的差异写在 `templates/narrative_template.md`；同一材料在不同 `report_type` 下页结构与顺序不同（三套配置可 diff）；计划门/证据审计/deck 审计/确定性探针**落盘即证据**；对照口径与不利结果见 `COMPARE.md` | `COMPARE.md` §1/§4；`examples/output/result.example.json` 的 `audit` 三段 |

## 4. 可靠体验（10 分）

| 评分点 | 分 | 本包落点（文件 / 机制） | 自证 |
|-|-|-|-|
| 调用与易用性 | 3 | 触发词写在 `SKILL.md` frontmatter `description`；**自定位**（`$SKILL_DIR` + `os.path.dirname(__file__)`，cwd 任意）；一条命令全流程；`SKILL.md` §4 检查点 CP1–CP5 + §6 决策规则 D1–D17 + §7 自查清单 + §9 资源形态 | `TEST.md` T7：cwd 为无关目录时主流程与自检脚本均退出码 0 |
| 运行稳定性 | 4 | 无网络依赖；必需依赖仅 python-pptx + Pillow（+ 可选 pypdf）；**缺依赖不崩**（D15）；材料缺失/空材料/PDF 无解析器/无模板/模板自带页/预览失败各有分支；重复运行确定性（无随机；`determinism` 探针 + 双跑 sha） | `TEST.md` T8–T13（六条分支，5 条退出码 0 + 负例 T12 退出码 1）、T4 双跑一致 |
| 异常处理 | 3 | `references/failure-modes.md`：**F1–F26** 失败模式表 + 决策规则 D1–D17 + 状态一致性规则（`completed/partial/failed` 的判定与"不得静默降级/不得虚报通过"）；退出码语义 0/1/2 明确；`result.json.uncertainty` 每条含 `item/impact/mitigation` | 全表见该文件；`TEST.md` T8–T13 每条都能对上表内条目 |

## 5. 生态贡献（10 分）

| 评分点 | 分 | 本包落点（文件 / 机制） | 自证 |
|-|-|-|-|
| 文档完整性 | 3 | `SKILL.md`（用途/适用条件/调用方式/输入输出/异常处置/资源形态）、`README.md`（运行/依赖/限制/维护）、`TEST.md`（可复现的实测命令与观测值）、`COMPARE.md`（对照口径）、`references/` 七份规范、`examples/README.md` + `examples/EXPECTED-OUTPUT.md`、`references/OUTPUT_CONTRACT.md`（字段契约全表） | 文件清单见 `README.md` 首段；`selftest.py --package-check` 报文本文件数 |
| 资源可复用性 | 4 | 可编辑规则：`templates/talk_config.json`（改权重即改行为）、`assets/plan.schema.json`（改模式即改校验）、`assets/result.template.json`（信封模板）；`scripts/` 14 个模块可独立 import/CLI（`validate_result`/`check_contract`/`evidence_audit`/`verify_deck`/`validate_plan`/`selftest`/`make_synthetic_inputs`）；`templates/slide-checklist-template.md`（上台前逐页核对，人可复用） | 各脚本 `--help`/独立 CLI；`TEST.md` T3 四件套独立复核 |
| 分享推广价值 | 3 | 沉淀"从材料到可讲页面"的页级组织方法、问答准备经验、证据审计规范、**失败模式表**与**资源形态合规做法**（§9 + `TEST.md` §8）；`GITHUB_URL.txt` 提供公开链接（第一行仓库、第二行作品路径） | `GITHUB_URL.txt`；`SKILL.md` §9；`references/failure-modes.md` |

## 6. GitHub 公开链接（+5）

`GITHUB_URL.txt` 第一行为仓库链接，第二行为本作品在本提交目录中的相对路径
（题面要求评审无需登录即可打开并找到本作品）。

## 7. 本次重打包相对上一版改了什么（与评分维度的关系）

| 维度 | 改动 |
|-|-|
| 实际效果 | 保留全部算法与 CLI；修复**模板自带页导致页数超出冻结值**（D16）、**材料缺失时崩溃**（`figure_refs` KeyError）、**无材料时仍报 completed**（D17）三处真实缺陷 |
| 使用增益 | 新增 `COMPARE.md`（13 行可判定差异 + A/B 口径 + 不利结果），把"增益怎么证明"写成可执行口径 |
| 创新增益 | 新增运行时资源生成（`make_synthetic_inputs.py`）与产物路径净化（`common.portable_path`）两项机制，并写进文档 |
| 可靠体验 | 决策规则扩到 D1–D17、失败模式扩到 F1–F26、退出码语义明确、六条降级分支实测（`TEST.md` §8） |
| 生态贡献 | 文档重写并逐条对齐实现；示例二进制改为运行时生成 + `EXPECTED-OUTPUT.md` 文字清单；包内只剩 40 个文本文件 |
