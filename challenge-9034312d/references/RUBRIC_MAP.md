# RUBRIC_MAP.md — 评分五维 → 本 Skill 设计覆盖（challenge-9034312d）

题面评分维度：**实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 ·
生态贡献 10 · GitHub 公开链接 +5**。下表逐维说明本 Skill 的设计覆盖与
**可核验证据落点**（证据路径相对 Skill 根；文字自述不替代实际运行证据）。

**一句话总览**：本包把「从材料到可编辑图稿」拆成
**证据（`gain_evidence.py`）→ 结构化中间表示（`model.py`）→ 确定性布图（`layout.py`）
→ 渲染（`render_svg.py`/`export_preview.py`）→ 校验（`svg_verify.py`/`check.py`）→ 契约（`result.json`）**
六段可独立复核的流水线，每一段都有落盘证据、失败分支（D1–D12）与可执行门（CP1–CP4、G1–G10）。

## 0. 评分维度 → 文件/机制映射（速查表）

| # | 维度 | 分值 | 主要落点（文件 / 机制） | 可复跑的验证 |
|-|-|-|-|-|
| 1 | 实际效果 | 40 | `scripts/main.py`（一键出图）+ `scripts/render_svg.py`（可编辑分层 SVG）+ `scripts/export_preview.py`（PNG/PDF）+ `scripts/layout.py`（数据映射/空间关系）+ `examples/` | `main.py` 跑示例 → `exit 0`；`check.py` → `ok:true`（G1–G10） |
| 2 | 使用增益 | 25 | `scripts/gain_evidence.py`（证据先行）+ `scripts/svg_verify.py`（连接规则/编号/图例机器审计）+ `--merge` 增量改图 | 见 §2 的**对照方案**：同一输入下「裸 Agent 手改」与「本 Skill」的检查项差异可逐条复算 |
| 3 | 创新增益 | 15 | `scripts/model.py`（SIR）+ `scripts/layout.py`（确定性布图）+ `assets/connection_rules.json`（可扩展规则资产）+ `verify_report.json.determinism.spec_sha16` | 同输入双跑 4 个文件逐字节一致（`TEST.md` T3）；改规则文件即改变审计结论 |
| 4 | 可靠体验 | 10 | `references/failure-modes.md`（D1–D12 + 打包门 R1–R6）+ `scripts/check.py`（退出码 0/1/3 语义）+ `main.py` 兜底 `failed/result.json` | 负例（连接违规）→ `exit 3` 且 `status=partial`（`TEST.md` T6） |
| 5 | 生态贡献 | 10 | 文档完整性（`SKILL.md`/`README.md`/`TEST.md`/`references/` 5 份/`templates/` 2 份）+ 可复用资产（规则字典/配色/核对清单/result 形态示例）+ `GITHUB_URL.txt` | 资产可被第三方直接改：改 `assets/connection_rules.json` 或 `templates/palette.json` 后重跑即生效 |
| +5 | GitHub 公开链接 | 5 | 根目录 `GITHUB_URL.txt`（单行公开链接；第二行可写相对文件路径） | 未登录浏览器打开该链接可见本作品 |

> **为什么这一节是最强信号**：题面明说「质量与增益以平台固定案例、基础 Agent/Skill Agent
> 对照结果和可核验记录为依据；文字自述不能替代实际运行证据」。因此本表每行都给出
> **能被第三方复跑的命令或可复算的差异**，而不是形容词。

## 1. 实际效果（40 分）＝ 完成度15 + 正确性15 + 完整性5 + 可核验性5

| 评分点 | 本 Skill 覆盖 | 证据位置 |
|-|-|-|
| 任务完成度 15 | 输入材料 → 直接产出可用的装置图/技术路线图：**可编辑分层 SVG 源文件 + PNG/PDF 渲染件 + evidence/layout 中间表示**，不是文字描述或截图；四个图类（route/apparatus/flow/hybrid）自动选布局模板 | `scripts/main.py` 一键流水线；四个图类示例：`examples/case.json`（route）、`examples/apparatus_spec.example.json`（apparatus）；产物清单与实测值见 `examples/EXPECTED-OUTPUT.md` |
| 结果正确性 15 | 实体名称与数量、接口对应、上下游顺序、箭头方向、标注与来源一致：**证据先行**（每条实体/关系带 locator+quote）→ **连接规则审计**（`assets/connection_rules.json` 机器检查类别词表/方向/语义）→ 断头箭头自动过滤并记录 | `scripts/gain_evidence.py`（证据链）；`scripts/svg_verify.py`（规则审计）；`result.json.evidence/verify` |
| 结果完整性 5 | 覆盖题面六类要素：科学实体（`entities`）、空间关系（`layout.json` 的 x/y/w/h）、数据编码（kind→形状/配色）、图例标注（legend↔kind 自动一致）、可编辑源文件（分层 SVG）、导出格式（PNG/PDF） | `layout.json`；`figure.svg` 五层 `layer:*`；`templates/palette.json` |
| 结果可核验性 5 | 图稿/源文件/证据清单/布局模型/校验报告全落盘，他人可独立复核与重绘；确定性探针 `spec_sha16` 证明同输入同布局 | `evidence.json` + `layout.json` + `verify_report.json` + `result.json`（`checksum`/`change_record`/`uncertainty`）；包内保留两个示例的**文本类**产物于 `examples/output/` |

## 2. 使用增益（25 分）＝ 质量15 + 效率5 + 增益可验证性5

**对照方案（基准做法 vs 加载本 Skill 后的做法）**——题面要求「需要相对比较的评分项使用
组织方预先固定的白板」，白板由平台提供；下面给出**可本地复算**的对照维度：

| 对照维度 | 基准做法（不加载 Skill 的基础 Agent） | 加载本 Skill 后 | 怎么验证 |
|-|-|-|-|
| 实体溯源 | 图上的盒子/箭头只写名称，出处靠自述 | 每个实体/关系带 `locator`+`quote`，落盘 `evidence.json` 并回显 `result.json.evidence` | 打开 `result.json.evidence.items`：条数 = 实体数 + 关系数（route 例 10+9=19） |
| 连接/方向正确性 | 靠肉眼，方向反了/凭空补连接不会被发现 | `svg_verify.py` 机器审计（`sequence` 只连步骤、`connect` 至少一端结构件、装置图物料不作流向终点、回流需复核） | 跑 `TEST.md` T6 负例：error 级违规 ⇒ `exit 3`、`status=partial` |
| 编号与图例一致性 | 手写编号易断号；图例与图形颜色/形状易不一致 | 编号 1..N 连续性 + 「图例 kind 集合 == 图面 kind 集合」自动校验 | `verify_report.json.checks.numbering_continuous` / `legend_kinds` 均为 true |
| 返工成本 | 改一个标注通常要重画或手工改图 | `--merge` 同名替换/新 id 追加，动作写入 `change_record`（`by=agent`） | 跑 `--merge examples/route_spec.mutation.example.json`：实体 10→11、关系 9→11、`checksum` 变化 |

| 评分点 | 本 Skill 覆盖 | 证据位置 |
|-|-|-|
| 质量增益 15 | 相对基础 Agent「画得像却错」：①实体全部 source-bound（evidence）②连接规则机器审计（类别/方向/语义）③步骤编号与正文逐条对照（G8）④图例↔图元一致（G9）⑤布局确定性 | `scripts/svg_verify.py`；`SKILL.md §4`；`TEST.md` 实测 |
| 效率增益 5 | 一键 `python "$SKILL_DIR/scripts/main.py"` 从材料到成图；`--merge` 增量修正免重画（编辑既有图稿）；重复运行零人工干预 | `README.md §3`；`main.py` 的 `--merge/--material/--figure-type` |
| 增益可验证性 5 | 同输入复跑确定性一致（无随机）；`TEST.md` 记录两次运行 sha256 对比；`check.py` G1–G10 全部可执行 | `TEST.md` T3（双跑 sha）；`scripts/check.py` |

## 3. 创新增益（15 分）＝ 新增能力5 + 方法改进5 + 创新证据5

| 评分点 | 本 Skill 覆盖 | 证据位置 |
|-|-|-|
| 新增能力 5 | 从装置清单/工艺描述解析「实体—连接—步骤—流向」结构化中间表示（SIR）→ 再据其布图与自检；**证据先行**（gain_evidence）+ **连接规则资产驱动审计**（connection_rules.json 可扩展）双创新 | `scripts/model.py`（SIR）；`scripts/gain_evidence.py`；`assets/connection_rules.json` |
| 方法改进 5 | ①三后端共享同一布局模型（SVG/PIL/reportlab 几何一致）②获取素材即校验（svg_verify 内置在流水线）③确定性探针（同输入同布局可复现）④`--merge` 编辑闭环写入 change_record | `scripts/layout.py`+`render_svg.py`+`export_preview.py`；`verify_report.json.determinism` |
| 创新证据 5 | 边界与价值文档化：与现有绘图方案的差异（可编辑源+溯源+机器校验）、适用条件、限制、失败清单 | `README.md`、`references/figure-blueprint.md`、`references/failure-modes.md` |

## 4. 可靠体验（10 分）＝ 调用易用3 + 运行稳定4 + 异常处理3

| 评分点 | 本 Skill 覆盖 | 证据位置 |
|-|-|-|
| 调用与易用性 3 | 单命令从输入走到导出；`SKILL.md §0` 给出 `$SKILL_DIR` 解析方式与四种调用形态；脚本自定位（`os.path.dirname(__file__)`），**任何 cwd 可运行** | `SKILL.md §0/§3`；各脚本头部；`TEST.md` T2/T5 |
| 运行稳定性 4 | 不同装置复杂度/不同路线结构/纯文本材料均可连续产图（结构化/文本解构双路径）；布局确定性无随机；规则资产缺失时静默降级（`--rules` 指不到文件仍 `exit 0`） | `TEST.md` T2/T3；`main.py` 兜底 `failed/result.json` |
| 异常处理 3 | 材料异常（缺失/歧义/冲突）、模板与依赖缺失（Pillow/reportlab/字体/规则资产）、**契约四形态**（四段列表 + 禁止 null）、状态一致性（error 违规 ⇒ 不得 success）均有识别与处置：D1–D12 决策规则 + 打包门 R1–R6 | `SKILL.md §5`；`references/failure-modes.md`；`main.py`/`check.py` 退出码语义 |

## 5. 生态贡献（10 分）＝ 文档3 + 复用4 + 分享3

| 评分点 | 本 Skill 覆盖 | 证据位置 |
|-|-|-|
| 文档完整性 3 | 使用说明（`README.md`）、输入约定与调用方式（`SKILL.md §2/§3`）、图元规范（`references/figure-blueprint.md`）、导出参数（`SKILL.md §3` 产出表 + `README.md §2` 依赖表）、示例与期望产物（`examples/README.md` + `examples/EXPECTED-OUTPUT.md`）、限制（`README.md §5`）、维护（`README.md §7`）齐全 | 全部文档：`SKILL.md`/`README.md`/`TEST.md`/5 份 `references/`/2 份 `templates/` |
| 资源可复用性 4 | **`assets/connection_rules.json`（连接规则字典，改它即改审计结论）**、`templates/palette.json`（图元配色）、`templates/component-connection-checklist.md` + `templates/entity-relation-checklist.csv`（核对模板）、`assets/result_example.json`（结果形态示例）、SIR 模型与导出脚本（`scripts/*.py`，全部自定位可搬走）均可直接复用或扩展 | `assets/`、`templates/`、`scripts/*` |
| 分享推广价值 3 | 沉淀可分享的图例规范、布局经验、连接规则字典、失败清单（D1–D12）与打包门（R1–R6）；`GITHUB_URL.txt` 提供公开作品入口 | `references/figure-blueprint.md`、`references/failure-modes.md`、`GITHUB_URL.txt` |

## 6. GitHub 公开作品链接（+5 分）

- `GITHUB_URL.txt` **第一行**：公开仓库中本作品所在位置的直链
  （当前值：<https://github.com/Very12345/pku-efficiency-3/tree/main/challenge-9034312d>）；
- 可选**第二行**写本次提交目录内的相对文件路径（如需指向具体文件）；
- 题面要求「提交前请用未登录 GitHub 的浏览器窗口打开一次，确认能看到作品」；
  本包不含需要登录才能访问的地址。

## 7. 多维落点自检（改包后照做）

```bash
# ① 五维里所有"可执行"落点是否仍然成立
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out /tmp/out   # exit 0
python "$SKILL_DIR/scripts/check.py" /tmp/out/demo-biotech-route-01/result.json   # exit 0, ok:true
# ② 确定性（创新增益/增益可验证性的机器证据）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out /tmp/det-B # figure.svg sha 应与上次一致
# ③ 负例（可靠体验：error 违规必须被拦截）
python "$SKILL_DIR/scripts/main.py" --case <违例案例> --out /tmp/neg                # 期望 exit 3, status=partial
```

## 8. 覆盖缺口（诚实声明）

- 图内标注「数值」（温度/浓度等原值注记）：材料含可标注原值时实体 `props` 可带，
  渲染端当前不强标数值注记——属明确边界（本 Skill 聚焦装置/流程/路线表达，不做数值拟合）；
- 复杂装配图的局部放大视图未内置：建议在 Inkscape 微调源文件并如实记录 `manual-edit`；
- 装置图深度（多级装配/嵌套接口）：三桶布局可表达单层装配，深层结构需 Agent
  拆分画布或增补 `stage` 列（限制见 `failure-modes.md`）；
- 平台正式案例上的分数由组织方评分器给出；本包只保证「可运行、可复核、可复现、诚实降级」，
  不宣称任何具体分数；
- 包内 `examples/output/` 的冻结 `result.json` 引用的 `figure.svg/png/pdf` 不随包发布
  （平台只收文本资源），因此对该冻结文件跑 `check.py` 会如实报 G3/G4——正确自查对象是
  新跑出来的 `result.json`（见 `examples/README.md §3`）。