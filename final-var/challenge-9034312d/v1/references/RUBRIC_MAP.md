# RUBRIC_MAP.md — 评分五维 → 本包设计覆盖（决策显性化版）

题面评分维度：**实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 · 生态贡献 10
· GitHub 公开链接 +5**。下表逐维说明本包的设计覆盖与**可核验证据落点**——
证据路径相对技能根，文字自述不替代实际运行证据。

**本版的一句话差异**：基线已经做到"能出图 + 能自检"；本版补的是**判决的一致性**——
把"遇到异常怎么办"从脚本里的隐式分支，升格为 20 条带**证据位点**的决策规则
（`SKILL.md §6`）与 27 行失败分支矩阵（`references/failure-modes.md §2`），
并给出 20 个**可复跑**的判决用例（`references/DECISION-CASES.md` + `scripts/decision_probe.py`）。
因此本表每一行都尽量指向**某个能被第三方重跑的判决**，而不是形容词。

## 0. 速查表

| # | 维度 | 分值 | 主要落点 | 可复跑的验证 |
|-|-|-|-|-|
| 1 | 实际效果 | 40 | `scripts/main.py` 一键出图 + `render_svg.py`/`export_preview.py` + `layout.py` + `examples/` | `main.py` 跑示例 → `exit 0`（实测 0.40–0.48 s）；`check.py` → `ok:true`（18/18 顶层键） |
| 2 | 使用增益 | 25 | 证据先行（CP1）+ 连接规则机器审计（CP2）+ `--merge` 增量改图 + **判决可复算** | `decision_probe.py` 20/20 与规范一致；对照协议见 §2 |
| 3 | 创新增益 | 15 | SIR → 确定性布图 → 三后端同布局 + **D1–D20 规则化判决 + 证据位点** | `verify_report.json.determinism.spec_sha16` 跨运行恒定；改 `connection_rules.json` 即改审计结论 |
| 4 | 可靠体验 | 10 | **本版主战场**：`SKILL.md §6/§7` + `failure-modes.md`（规则索引/27 行矩阵/4 条安静缺陷）+ `check.py` 退出码 0/1/2/3 + 状态聚合优先级 | `decision_probe.py` 观测表；负例 `exit 3` |
| 5 | 生态贡献 | 10 | 6 份 `references/` + 2 份 `templates/` + 规则字典 + **判决用例集**（可搬到同类题） | 改 `assets/connection_rules.json` 或 `templates/palette.json` 后重跑即生效 |
| +5 | GitHub 链接 | 5 | 根目录 `GITHUB_URL.txt`（单行） | 未登录浏览器可打开 |

## 1. 实际效果（40）= 完成度15 + 正确性15 + 完整性5 + 可核验性5

| 评分点 | 覆盖方式 | 证据位置 |
|-|-|-|
| 任务完成度 15 | 材料 → 可编辑分层 SVG + PNG/PDF + `evidence/layout/verify_report/result.json`，**不是文字描述或截图**；四图类（route/apparatus/flow/hybrid）自动选模板 | `scripts/main.py`；实测四形态均 `exit 0` 且各产出 7 文件（`TEST.md` T2） |
| 结果正确性 15 | ①每条实体/关系带 `locator`+`quote`；②连接规则机器审计（类别词表/`sequence` 只连步骤/`connect` 需结构件/装置图物料不作终点/回流需复核）；③断头关系丢弃并留痕；④编号 1..N 连续；⑤图例 kind == 图面 kind | `gain_evidence.py`；`svg_verify.py`；`result.json.evidence/verify`；**判决用例 D05/D13/D15/D16/D17** |
| 结果完整性 5 | 覆盖题面六类要素：科学实体（`entities`）、空间关系（`layout.json` 的 x/y/w/h）、数据编码（kind→形状/配色）、图例标注、可编辑源文件（分层 SVG）、导出格式（PNG/PDF） | `layout.json`；`figure.svg` 五层 `layer:*`；`templates/palette.json` |
| 结果可核验性 5 | 图稿/源文件/证据清单/布局模型/校验报告全落盘；确定性探针证明同输入同布局；**判决行为本身也可核验**（20 个用例的期望 vs 实测） | `evidence.json`+`layout.json`+`verify_report.json`+`result.json`；`references/DECISION-CASES.md`；`examples/output/` |

## 2. 使用增益（25）= 质量15 + 效率5 + 增益可验证性5

题面要求"需要相对比较的评分项使用组织方预先固定的白板"（白板由平台提供）。
本包给出的是**可本地复算**的对照维度——注意本版新增了最后一列：**判决差异**，
它是本版相对基线的主要增益来源。

| 对照维度 | 基础做法（不加载 Skill） | 加载本包后 | 怎么验证 |
|-|-|-|-|
| 实体溯源 | 盒子/箭头只有名称，出处靠自述 | 每条带 `locator`+`quote`，落盘 `evidence.json` 并回显 `result.json.evidence` | 条数应为实体数 + 关系数（route 例 10+9=19） |
| 连接/方向正确性 | 靠肉眼，反向/凭空补连接发现不了 | `svg_verify.py` 机器审计，error 级强制 `partial` | 判决用例 **D13/D15/D16/D17**：均 `exit 3` + G9 失败 |
| 编号与图例一致性 | 手写编号易断号 | 编号 1..N + 图例 kind 集合自动校验 | `verify_report.json.checks.numbering_continuous/legend_kinds` |
| **异常处置一致性** | 同一个异常在不同轮次可能被不同对待 | **D1–D20 规定动作，同一异常永远同一处置**；`decision_probe.py` 把 20 条判决钉住 | 跑 `decision_probe.py`，`summary.deviations` 必须为空 |
| **失败是否被暴露** | 出错时倾向"先出一张图" | error 级违规 ⇒ 退出码 3 且 `status=partial`（**拒绝冒充成功**） | 判决用例 D13/D15/D16/D17；负例见 `TEST.md` T7 |
| 返工成本 | 改一个标注通常要重画 | `--merge` 同名替换/新 id 追加，动作写入 `change_record` | 跑 `--merge route_spec.mutation.example.json`：实体 10→11、关系 9→11、`checksum` 变化 |

| 评分点 | 覆盖方式 | 证据位置 |
|-|-|-|
| 质量增益 15 | 五项质量门 + 一处新增：**判决不再随运行变化**（规则 + 用例双钉） | `svg_verify.py`；`decision_probe.py`；`TEST.md` T6 |
| 效率增益 5 | 单命令出图（实测 0.40–0.48 s）；`--merge` 增量修正免重画；**异常不用人猜**（查 D# 即得处置） | `README.md §3`；`TEST.md` T2；`SKILL.md §6` |
| 增益可验证性 5 | 双跑确定性（4 文件逐字节一致）+ G1–G10 可执行 + **20 个判决用例可复跑** | `TEST.md` T3/T6；`references/DECISION-CASES.md` |

## 3. 创新增益（15）= 新增能力5 + 方法改进5 + 创新证据5

| 评分点 | 覆盖方式 | 证据位置 |
|-|-|-|
| 新增能力 5 | ①从装置清单/工艺描述解析「实体—连接—步骤—流向」结构化中间表示（SIR）；②证据先行；③**规则资产驱动的机器审计**；④**判决规则化 + 证据位点**（每条规则都必须能被某次运行复现） | `model.py`；`gain_evidence.py`；`assets/connection_rules.json`；`SKILL.md §6` |
| 方法改进 5 | ①三后端共享同一布局模型；②校验内建于流水线；③确定性探针；④`--merge` 编辑闭环写入 `change_record`；⑤**状态聚合优先级**（多缺陷同时出现时 `status` 取值唯一） | `layout.py`+`render_svg.py`+`export_preview.py`；`verify_report.json.determinism`；`SKILL.md §4` |
| 创新证据 5 | 边界与价值文档化：与既有绘图方案的差异、适用条件、限制、**4 条安静缺陷的复核办法** | `README.md §0/§5`；`references/figure-blueprint.md`；`references/failure-modes.md §3` |

## 4. 可靠体验（10）= 调用易用3 + 运行稳定4 + 异常处理3

| 评分点 | 覆盖方式 | 证据位置 |
|-|-|-|
| 调用与易用性 3 | 单命令从输入到导出；`SKILL.md §0` 给 `$SKILL_DIR` 解析与三分钟上手；脚本自定位，任何 cwd 可运行 | `SKILL.md §0/§2`；`TEST.md` T2/T5 |
| 运行稳定性 4 | 结构化/文本解构双路径；布局无随机；规则资产缺失时静默降级（判决用例 D11/D12 钉住这一行为）；**20 个异常形态逐条有确定处置** | `TEST.md` T3/T6；`main.py` 兜底 `failed/result.json` |
| 异常处理 3 | 材料异常 / 模板缺失 / 依赖缺失 / 契约四形态 / 状态不一致**五类全覆盖**，每类给"触发→动作→降级→证据位点"四要素；退出码 0/1/2/3 有明确语义 | `SKILL.md §6/§7`；`references/failure-modes.md §2`；`references/DECISION-CASES.md` |

## 5. 生态贡献（10）= 文档3 + 复用4 + 分享3

| 评分点 | 覆盖方式 | 证据位置 |
|-|-|-|
| 文档完整性 3 | 使用说明（`README.md`，含 `§0 这一版改了什么`）、输入约定与调用（`SKILL.md §2`）、图元规范（`figure-blueprint.md`）、导出参数、示例与期望产物、限制（含安静缺陷）、维护（含"先改规范再改实现"的流程）齐全 | `SKILL.md`/`README.md`/`TEST.md`/6 份 `references/`/2 份 `templates/` |
| 资源可复用性 4 | 规则字典（改它即改审计结论）、配色模板、两份核对清单、结果形态示例、SIR 与导出脚本、**判决用例集 + 探针脚本**（可直接搬到同类题） | `assets/`、`templates/`、`scripts/*`、`references/DECISION-CASES.md` |
| 分享推广价值 3 | 沉淀图例规范、布局经验、连接规则字典、失败分支矩阵、安静缺陷清单、打包门 R1–R6；`GITHUB_URL.txt` 公开入口 | `references/figure-blueprint.md`、`references/failure-modes.md`、`GITHUB_URL.txt` |

## 6. GitHub 公开作品链接（+5）

- `GITHUB_URL.txt` **第一行**：公开仓库中本作品所在位置的直链；
- 可选第二行写提交目录内的相对文件路径；
- 题面要求"提交前用未登录 GitHub 的浏览器窗口打开一次"；本包不含需登录的地址。

## 7. 多维落点自检（改包后照做）

```bash
SKILL_DIR=/skills/weekly-skill

# ① 五维里所有"可执行"落点是否仍然成立
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out /tmp/out   # exit 0
python "$SKILL_DIR/scripts/check.py" /tmp/out/demo-biotech-route-01/result.json   # exit 0, ok:true

# ② 确定性（创新增益/增益可验证性的机器证据）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out /tmp/det-B
#   figure.svg sha 应与上次一致

# ③ 判决行为（本版新增，可靠体验的核心证据）
python "$SKILL_DIR/scripts/decision_probe.py" --out /tmp/decisions --json /tmp/decisions/obs.json
#   summary.deviations 必须为空；不为空就先查 references/DECISION-CASES.md §4

# ④ 负例（error 违规必须被拦截）
python "$SKILL_DIR/scripts/main.py" --case <违例案例> --out /tmp/neg   # 期望 exit 3, status=partial
```

## 8. 覆盖缺口（诚实声明）

- 图内**数值注记**不强制渲染：材料含可标注原值时实体 `props` 可带，渲染端当前不强标
  （本 Skill 聚焦装置/流程/路线表达，不做数值拟合）；
- **局部放大视图**未内置：建议在 Inkscape 微调源文件并如实记录 `manual-edit`；
- 装置图深度为**单层装配**（三桶布局）；深层嵌套需 Agent 拆画布或增补 `stage` 列；
- **4 条安静缺陷**（见 `references/failure-modes.md §3`）本版只做到"点名 + 给复核办法"，
  没有改成自动降级——因为把所有包都打成 `partial` 会让状态失去区分度；
- 20 个判决用例覆盖 27 行分支中的 20 行；**剩余 7 行需要改环境或人工动作才能构造**
  （无 Pillow/reportlab、无中文字体、手工改状态、`--merge` 非法端点等），
  逐条怎么验见 `references/DECISION-CASES.md §2`；
- 平台正式案例上的分数由组织方评分器给出；本包只保证「可运行、可复核、可复现、诚实降级」，
  **不宣称任何具体分数**；
- 包内 `examples/output/` 的冻结 `result.json` 引用的 `figure.svg/png/pdf` 不随包发布
  （平台只收文本资源），因此对该冻结文件跑 `check.py` 会如实报 G3/G4——正确自查对象是
  新跑出来的 `result.json`（见 `examples/README.md §3`）。
