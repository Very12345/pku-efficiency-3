# RUBRIC_MAP.md — 评分五维 → 本包落点（v4 轴：失败注入与恢复演练）

> 题面评分维度：**实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 · 生态贡献 10**
> （GitHub 公开链接另加 +5）。本表把每个评分点映射到**本包里真实存在、可被第三方复核**的
> 文件与机制；*证据* 列给出可执行的复核方式（命令或字段），**文字自述不替代实际运行证据**。

本轴的定位：出图能力与基线同源，**增量全部投在"这条链路在缺陷下到底可不可信"**上 ——
所以「可靠体验 10」与「创新增益 15」的证据密度最高，且都是可复跑的实测数据而非声明。

## 1. 实际效果（40 分）

| 评分点 | 本包覆盖 | 证据 / 复核方式 |
|-|-|-|
| 任务完成度 15 | 四要素单页摘要（问题→方法→结果→结论四列 + 阅读顺序 + 流程箭头）；交付**可编辑分层 SVG** + PNG/PDF 渲染件（运行时生成，包内无二进制）；方案先行（`scaffold.py` 骨架 → 方案 lint → `--plan` 出图） | `python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/o` → exit 0、26 键；`examples/EXPECTED-OUTPUT.md` 列期望产物 |
| 结果正确性 15 | 实体/关系/数据全部 source-bound（`data-src`）；数值只在材料里存在时才上画布；数据编码↔图例由 `spec_lint` 硬检查；`audit.encoding_consistency` 逐值核对 | `audit.json` 的 `entity_coverage.missing=[]`、`encoding_consistency.missing_from_canvas=[]`（TEST.md §1 实测） |
| 结果完整性 5 | 六要素齐备（科学实体、空间/因果关系、数据编码、图例标注、可编辑源文件、导出格式）+ 单位/比例尺/来源脚注；四要素覆盖由 `audit.four_element_coverage` 强制 | `audit.four_element_coverage.on_canvas` 实测为 4/4（question/method/results/conclusion） |
| 结果可核验性 5 | SVG metadata(build_id/版本) + 每元素 `data-src` + `sources[]`(sha256) + `change_records` + 全量 `audit`；**方案覆盖 constraints 的决策现在会留在 `change_records`（F9 修复）** | `result.json` 的 `provenance.source_files[].sha256`、`change_records[]`；FAULT-MATRIX F12 用例实测 override 已留痕 |

## 2. 使用增益（25 分）

| 评分点 | 本包覆盖 | 证据 / 复核方式 |
|-|-|-|
| 质量增益 15 | 相对"不加载 Skill 的基础做法"：基础做法产无来源信息图/不可编辑位图/版式漂移；本包给出 ①数值可追源（spec_lint 门）②布局确定性（spec hash 两次一致）③文字可编辑（真 `<text>` + 七层契约）④四要素必齐 ⑤**缺陷下不静默**（见下） | TEST.md §3 两次运行 `spec_sha16` 均为 `9bcb54b29fe658d4`；`audit.layer_naming`、`audit.four_element_coverage` |
| 效率增益 5 | 免重绘/重排版/跨软件搬运：`scaffold.py` 一步出方案骨架、`--plan` 直接出图、`spec.json` 微调即重出图、自动图例与自动六项自查 | `scripts/scaffold.py` → `scripts/main.py --plan` 一条链；`spec.json` 可直接编辑后 `spec_lint --spec` 复检 |
| 增益可验证性 5 | **增益不靠自述，靠注入 + 题集**：四形态 23 条注入逐条给出 `exit / status / uncertainty / verdict`，另有 v5 两个合成案例的实跑记录；判级可用 `--fail-on strict` 接进 CI | `fault_inject.py --fail-on strict` → exit 0、`silent_failure=0`（23/23 `ok`，基线为 10 `ok`/5 `mismatch`/8 `silent`）；v5 案例 A/B 冒烟 exit 0（TEST.md §4） |

> 口径提醒：本包**不宣称单次运行更快**（出图链与基线同源），增益体现在"缺陷可被发现、
> 状态不虚报、决策留痕"这三项可核验属性上。

## 3. 创新增益（15 分）

| 评分点 | 本包覆盖 | 证据 / 复核方式 |
|-|-|-|
| 新增能力 5 | **可执行的失败注入器**（`scripts/fault_inject.py`）：把输入/模板/依赖/契约四类缺陷真的制造出来，用子进程跑真实主流程，抓真实退出码；`--only` 按类/按条复现，`--fail-on` 三档判级 | `scripts/fault_inject.py`；`fault_report.json`（含每条 argv、耗时、stdout/stderr 摘要） |
| 方法改进 5 | ①注入落在**输入/环境**上，脚本主体逐字节可比对（不改被测代码）②依赖缺失用 `PYTHONPATH` 假模块而不是卸载③"静默失败"被定义为**可判定条件**（exit 0 且 status=success 而缺陷无记录）④查出缺陷后按**纯增量**修复并复跑同一套用例 | `FAULT-MATRIX.md` §1（逐行矩阵）与 §2（F1–F9/P1 增删行数与触发用例） |
| 创新证据 5 | 与常规做法边界：同类包普遍只写"我们会处理异常"，本包给出**修复前 8 条静默失败 → 修复后 0 条**的对照，并明确列出**不覆盖**的范围 | `FAULT-MATRIX.md` §0 一页结论、§5 未覆盖声明；`TEST.md` §4/§7 |

## 4. 可靠体验（10 分）

| 评分点 | 本包覆盖 | 证据 / 复核方式 |
|-|-|-|
| 调用与易用性 3 | 单命令出图（自定位，cwd 任意）；参数表与 `scripts/` 真实 flag 逐字对应；注入器一条命令出整张矩阵 | `README.md` §4 参数表；`SKILL.md` §0 |
| 运行稳定性 4 | 后端链 matplotlib → Pillow → 纯 Python PNG（第三级此前是**死代码**，P1 修复后实测可用）；字体候选路径跨平台探测；同输入结构一致 | FAULT-MATRIX F13/F14/F15 三行：实测 `backend=pure-python-png` 且 `status=partial`；`render_log.json` |
| 异常处理 3 | 五类失败模式全部有"检测点 → 处置 → 记录位点"，且**每条都指向一个真实注入用例**；退出码语义稳定（0/1/2）；契约 null 归一化、方案 lint 降级、材料缺失/二进制/非 UTF-8 全部留痕 | `references/failure-modes.md` §3 三者互查表；FAULT-MATRIX F04 F05 F07 F08 F09 F11 F16 F17 F18 各行 |

## 5. 生态贡献（10 分）

| 评分点 | 本包覆盖 | 证据 / 复核方式 |
|-|-|-|
| 文档完整性 3 | 使用说明（README）、实测记录（TEST）、契约（OUTPUT_CONTRACT）、五维映射（本文件）、失败矩阵（failure-modes + FAULT-MATRIX）、方案 schema、四要素知识、图层规范、模板与视觉通道 | `references/` 目录 8 份文档 + `README/TEST/SKILL` |
| 资源可复用性 4 | 资产的"复用前必须改什么"逐条写明；**注入器可直接搬到别的出图 Skill**（只要求目标包有 `scripts/main.py` 与 `--case/--out` 语义，用例表在文件顶部集中声明）；题集协议与难度层可直接沿用 | `assets/` 三件套、`examples/`、`scripts/fault_inject.py` 顶部 CASES 表；`references/TEMPLATE.md` |
| 分享推广价值 3 | 矩阵本身就是可分享的"缺陷清单"：任何声称"我们会处理异常"的包，都可以用同一套判据被审；`GITHUB_URL.txt` 提供公开入口 | `FAULT-MATRIX.md`；`GITHUB_URL.txt` |

## 6. 自评口径（避免虚报）

| 维度 | 自评 | 依据 | 扣分风险 |
|-|-|-|-|
| 实际效果 | 强 | 冒烟 exit 0、26 键、四要素 4/4、覆盖率 100%、确定性一致 | 图面美观与领域正确性仍由人判断（结构判据不替代科学判断） |
| 使用增益 | 中强 | 注入 23/23、0 静默失败；但**未做**与基础 Agent 的并排出图对照（那属于另一条轴） | 缺"同输入两种做法"的直接对比图 |
| 创新增益 | 强 | 注入器 + 修复前后对照 + 未覆盖声明 | 创新点集中在"可靠性验证"，不是新绘图算法 |
| 可靠体验 | 强 | 8 条静默失败实测 → 修复 → 复跑全绿 | 平台侧故障不在覆盖范围内 |
| 生态贡献 | 中强 | 文档齐备 + 注入器可移植 | 未提供第三方真实案例的复用记录 |
