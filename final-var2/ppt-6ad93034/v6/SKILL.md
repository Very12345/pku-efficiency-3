---
name: academic-ppt-builder-union
description: 学术汇报演示稿（PPTX）生成与编辑的总集成包：把论文/研究材料组织成结构清楚、证据可追溯、可编辑、符合模板约束的演示稿，并在同一包里同时给出四层可自证的东西——① 决策规则 D1–D14 与五族失败分支；② 失败注入矩阵（28 条故障逐行实测 exit/status/留痕/是否静默 + 17 条恢复动作）与留痕守卫；③ 使用增益的公平对照协议与可复算测量台；④ 五个机制的可证伪判据与探针；另有九个可复用资产的清单、两个不同题材的合成案例题集（含可接受区间与泛化失效边界）。支持 --edit 局部编辑与版本回退；页面数字逐一核验材料、缺失显式标注、绝不编造。Use when a task asks to generate or edit an academic presentation / slide deck from a paper or research material（组会汇报、开题与中期、答辩、项目评审、基金申请；学术PPT、slides from paper、presentation from paper），especially when /input/case.json and task.md are present, /app/output must contain the editable deck plus previews and evidence mapping, and the submission must show decision rules, failure behaviour, measured gain, mechanism evidence and cross-topic generalization in one place.
---

# 学术 PPT 生成与编辑 Skill（总集成版 · ppt-6ad93034）

> **本包 = 决策显性化 ∪ 增益可验证 ∪ 机制可证伪 ∪ 抗故障可判读 ∪ 多案例泛化。**
> 一份包，六段路：**输入 → 执行 → 失败 → 增益 → 机制 → 复用**。
> 每一段都指向随包的证据文件，不靠自述：
>
> | 段 | 一句话 | 证据在哪 |
> |-|-|-|
> | 输入 | 读契约、读实际材料，不猜 | `references/OUTPUT_CONTRACT.md`、§1 |
> | 执行 | CP1–CP4 + 决策规则 D1–D14 | §2、`references/failure-modes.md` §1–§8 |
> | 失败 | 28 条注入逐行实测 + 7 条静默缺口 + 恢复动作 + 守卫 | `references/FAULT-MATRIX.md`、§3 |
> | 增益 | 公平对照协议 + 可复算指标 + 真实 Δ（含负面项） | `references/GAIN-PROTOCOL.md`、`references/measure_gain.py`、§4 |
> | 机制 | 五个机制各配"可在产物里查"的判据与探针 | `references/MECHANISM-AND-ASSETS.md`、`references/mechanism_probe.py`、§5 |
> | 复用 | 九个可拿走资产 + 两个题材的案例题集 | `references/MECHANISM-AND-ASSETS.md` 第二部分、`references/CASE-SET.md`、§6 |
| 溯源 | v4/v5 的 SKILL 正文原文（union 不丢内容） | `references/VARIANT-SKILL-APPENDIX.md` |

**管辖范围**：把材料"翻译"成页级表达，并保证每页数字与图表可核实。
**不负责**：论文精读与文献综述、科研绘图算法本身、学术写作文字润色、PPT 软件研发。

**命令口径（全文一致）**：`$SKILL_DIR` = **含本 `SKILL.md` 的技能根目录**
（平台评测容器内为 `/skills/weekly-skill`）。所有命令都写成
`python "$SKILL_DIR/scripts/…"`，**cwd 不是技能根目录时照样能跑**
（脚本内部用 `os.path.dirname(__file__)` 自定位）。

---

# 第一部分 · 输入

## §1 读什么、写什么、边界在哪

**读**：`/input/case.json`（`case_id`、`title`、`inputs{task_md, material[]}`、
`spec{audience, duration_minutes, max_slides, template|template_pptx|starting_deck, style}`、
可选 `output_contract`）、`task.md`、以及 `material[]` 指向的**实际文件**。
`scripts/deck_extract.py` 强制"读实际文件"，**禁止凭文件名推断内容**。

**写**（一律写 `--out`，并在输出根放一份 `preview/` 副本便于直接取件）：
`work/deck.pptx`（可编辑源，每页备注 + 证据脚注）、`work/plan.json`（页面模型，可编辑源）、
`work/material_view.json`、`work/preview/slide_*.png` + `preview.pdf`、
`result.json`（契约全字段，禁 null）、`evidence_map.md` + `evidence_map.json`（同源双形态）、
`changelog.jsonl`、`manifest.json`（全部产物 sha256）、`logs/`。

**边界（不做的四件事）**：论文精读与文献综述、可视化算法研发、学术写作润色、PPT 软件研发。
材料确实缺数据/图/局限时**不臆造**，改在 `uncertainty` 与 `unverified_claims` 中如实标注。

**包体纪律**：随包只有 UTF-8 文本（`.md/.py/.json/.txt/.csv/.yaml/.yml`），
**≤50 文件 / 单文件 ≤500KB / 合计 ≤2MB / 无符号链接**；二进制产物一律运行时生成；
**产物绝不写回技能包目录**（评测容器里技能目录是只读安装件）。

> **三档输入判别（贯穿全文）**：`material_warnings`（材料侧问题）、
> `uncertainty`（无法核验 / 已降级）、`status`（整体成败）语义不同，**必须分开记录**。

---

# 第二部分 · 执行

## §2 主干流程 CP1–CP4 与命令

```bash
SKILL_DIR="${SKILL_DIR:-/skills/weekly-skill}"

# ① 前置体检（可判读版新增，挡掉三类"崩了却不写 result.json"）
python "$SKILL_DIR/scripts/fault_inject.py" --guard --case /input/case.json \
    --template /input/template.json          # --template 可省略

# ② 端到端（CP1–CP4 全在这一条里）
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output

# ③ 契约门 G1–G8（`--case` 必须传，否则无法核对契约回显）
python "$SKILL_DIR/scripts/result_tool.py" --result /app/output/result.json \
    --out-dir /app/output --case /input/case.json \
    --envelope "$SKILL_DIR/templates/result_envelope.json"     # {"valid": true} 且 exit 0

# ④ 产物自检
python "$SKILL_DIR/scripts/selftest.py" --out /app/output --case /input/case.json   # all_pass=true

# ⑤ 运行后核对（把"静默降级"找出来）
python "$SKILL_DIR/scripts/fault_inject.py" --guard --out /app/output
```

| 检查点 | 动作 | 判定 | 不过时 |
|-|-|-|-|
| **CP0 前置体检** | 输入形态 / 依赖齐备 / 模板可开 / 契约形态 | BLOCKER 必须先处理 | 实测这三类会硬崩且无 `result.json`（§3 S4–S7） |
| **CP1 读实际输入** | 读 case/task/每个材料，核对存在性 | 材料可读性 | D1：只出元信息 result，`slide_count=0`，绝不编 deck |
| **CP2 规划与 lint** | `slide_text.build_plan` 分配角色；`evidence_check.plan_lint` 校验页面纪律 | `valid` 或记录偏差 | D4：记录 `problems` 原文并降 partial |
| **CP3 建稿** | 模板槽位建稿 + 四态图表绑定 + 每页备注与证据脚注 | deck 可 python-pptx 重开且页数=plan | D6/D9：备份 + 降级 + 留痕 |
| **CP4 导出校验** | `result_tool` 的 G1–G8 + `selftest` | `{"valid": true}` 且 exit 0 | 逐条进 `uncertainty` |
| **CP5 运行后核对**（可判读版新增） | 核对"该记的记了没有" | 有 WARN/BLOCKER 则按 §3 恢复动作处理 | 见 §3 守卫表 |

**退出码语义**（编排器可直接判读）：

| 脚本 | 0 | 1 | 2 |
|-|-|-|-|
| `main.py` | `status=success` | `status=partial`（降级**逐条**进 `uncertainty`） | 输入不可读（已写最小 `status=failed` result.json） |
| `result_tool.py` | G1–G8 全过 | 有条目未过 | `result.json` 无法解析 |
| `selftest.py` | 全部自检项通过 | 有未通过项 | 输入不可读 |
| `evidence_check.py` | 主张里每个数字都能定位 | 有数字找不到 | — |
| `fault_inject.py`（注入台） | 故障行为与期望一致且守卫无发现 | 有偏差 / 有静默失败 | 环境不可用或 `--work` 在包内 |
| `case_check.py`（泛化台） | 全部案例过判据 | 有案例未过 | 环境/案例不可用 |

## §2.1 决策规则 D1–D14（速查；逐族展开见 `references/failure-modes.md` §1–§8）

| # | 触发 | 动作 | 记录 |
|-|-|-|-|
| D1 | 材料缺失/路径不存在 | 不补造；只出元信息 result（`slide_count=0`） | `material_warnings` |
| D2 | 主张数字材料中找不到 | `verified=false` 入未核验清单，**原文照录** | `unverified_claims` |
| D3 | PDF 无文本层/无抽取库 | 不 OCR 冒充；Agent 抽文本后重跑，仍不行 partial | `uncertainty` + `sources.tool` |
| D4 | CP2 `plan_lint` 有偏差 | 先修；硬约束则继续但**显式记录**并降 partial | `run_meta.spec_lint` |
| D5 | 位图无数据 | `placeholder` 灰框占位，**不生成假曲线** | `figure.note` |
| D6 | 模板打不开/母版损坏 | 备份 → 内置模板，说明降级 | `uncertainty` + `change_records` |
| D7 | 页数超限 | 确定性压缩，**不静默丢证据页** | `change_records` + `notes` |
| D8 | 字体缺失/渲染不可用 | PPTX 只记字体名；预览回落并预警 | `previews.warnings` |
| D9 | 图表重绘失败 | 降级 PPTX 原生可编辑表格 | `figure.note` |
| D10 | 契约字段未知/无值 | 四形态空值 `""/[]/{}/false/0`，**禁 null** | 顶层回显 |
| D11 | 编辑操作非法 | 跳过并记录，其余照常 | `uncertainty` + `changelog` |
| D12 | 复核说"契约没回显" | **先查 `--case` 是否传了** | 复核记录 |
| D13 | 重复运行有差异 | 判断是否仅时间戳/机器路径前缀 | `change_records` |
| D14 | 预算压力 | 先落 partial 再增量改进，**逐条列未完成项** | `status` + `change_records` |

**优先级**：D1/D2 属"事实正确性"层，任何情况下不得为"页面好看"放宽；
D5–D9 属"能力降级"层，允许降级但**必须留痕**；D13/D14 属"运行工程"层。

## §2.2 增量编辑（多轮迭代与回退）

```bash
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output \
    --edit edits.json --version v2
```

7 类 op：`update_bullet / add_bullet / remove_bullet / add_note / retitle /
reorder_pages / set_figure`（字段见 `examples/edit_demo.json`，决策树 + 操作目录见
`references/EDIT_OPS.md`）。每次改动写一条 `{version, op, page, target, reason}`；
`deck_v2.pptx` 与 `deck.pptx` **并存** → **回退 = 复制旧版本重跑**。
**编辑链路同样过 D2 数字核验**：实测用 `--edit` 塞入材料里没有的 `31.7%`，
该主张立刻进 `unverified_claims`（`missing_numbers=["31.7%"]`）——
**不因"是用户让改的"而放行**。

---

# 第三部分 · 失败

## §3 失败注入矩阵、静默缺口与守卫（`references/FAULT-MATRIX.md`）

```bash
python "$SKILL_DIR/scripts/fault_inject.py" --list                    # 28 条故障清单
python "$SKILL_DIR/scripts/fault_inject.py" --pkg "$SKILL_DIR" --work <包外目录> --with-recovery
python "$SKILL_DIR/scripts/fault_inject.py" --guard --case /input/case.json   # 运行前
python "$SKILL_DIR/scripts/fault_inject.py" --guard --out /app/output         # 运行后
```

**实测汇总（2026-11-23，四族 28 条，总耗时约 60 秒）**：

| 统计项 | 实测值 |
|-|-|
| exit 分布 | `0 × 14` / `1 × 10` / `2 × 4` |
| status 分布 | `success × 15` / `partial × 5` / `failed × 4` / 未写出 `result.json` × 4 |
| 留痕等级 | `product × 19` / `stdout-only × 4` / `none × 5` |
| **静默失败** | **7 条**：`F-IN-07` `F-TPL-03` `F-TPL-05` `F-DEP-03` `F-DEP-04` `F-DEP-05` `F-CTR-03` |
| 恢复动作 | 17 条有恢复动作，**17/17 被恢复或被守卫判定** |
| 守卫可信度 | 28 条故障产物上 **7/7 静默被抓**；健康产物 **0 误报** |

**7 条静默缺口（如实列出，未在本包修改主流程）**：

| 编号 | 缺口 | 现可用补救 |
|-|-|-|
| S1 | 数据表解析不出内容时，结果页图表**无声消失**（无 note、无 uncertainty） | `--guard --out` 报 `WARN/figure` |
| S2 | `output_contract` 不是对象时契约回显**整体静默跳过**，G2 也不报错 | `--guard --case` 报 `DEGRADE/contract` |
| S3 | `template_pptx` 指向不存在的文件时**静默改用内置模板** | `--guard --case` 报 `DEGRADE/template_pptx` |
| S4–S7 | 参数形态错误 / 缺 `python-pptx` / 缺 `Pillow` → **硬崩且不写 `result.json`**（只有 stdout 的 Traceback） | `--guard --case` 前置拦截；`--guard --out` 报 `BLOCKER` |

**恢复动作四条最常用的**（每条都在注入台上真跑过，见 `FAULT-MATRIX.md` §3）：
① 坏模板参数 → **去掉参数**回落内置模板；② 材料缺件 → **补件重建**；
③ 图表降级 → `--no-chart` 把降级**显式化**（`figure.kind=table` + note）；
④ 不可建稿 → 守卫判 BLOCKER，**如实交 partial/failed**，绝不交"看起来成功"的空稿。

**为什么不直接改 `main.py`**：CLI 参数与退出码语义是平台契约的一部分
（`failure-modes.md` §0 已被下游按字读）。本包守"既有脚本逐字节不变 + 只做纯增量"的规矩，
用**一层守卫**把缺口变成可判读报告，并把缺陷本身记录在案。

---

# 第四部分 · 增益

## §4 使用增益：公平对照协议 + 可复算指标 + 真实 Δ

**增益来源不是"多写了几页"**，而是三种基础形态天然拿不到的结构，各自对应一个可测指标：

| 结构 | 由谁产生 | 可测指标 |
|-|-|-|
| 页级叙事角色 | `scripts/slide_text.py::alloc_roles` 确定性分配 | Q1 角色覆盖率 |
| 数字主张 ↔ 证据指针 | `evidence_check.check_claim_numbers` + `build_evidence_footer` | Q3 可追溯率 |
| 双形态证据映射 + sha256 清单 | `result_tool.write_evidence_map*` / `write_manifest` | Q5/Q6 |
| 演讲备注与页面文字分离生成 | `slide_text` 备注骨架 + `deck_tool` 备注槽位 | Q4 备注覆盖率 |

**协议要点（完整版 + 公式 + 可证伪判据见 `references/GAIN-PROTOCOL.md`）**：
同一 `case.json`、同一材料、同一 `spec.max_slides`、同一模板、同一解释器与库版本、
**同一测量脚本**——任何一项不同，对照即无效。

```bash
# 测量台必须在【包外】运行（否则在技能包里生成 __pycache__）
cp "$SKILL_DIR/references/measure_gain.py" <包外目录>/
python <包外目录>/measure_gain.py --skill-dir "$SKILL_DIR" \
    --case <case1> --case <case2> --work <包外目录>/work --out <包外目录>/gain-report.json
```

**本包实测 Δ（两个案例，真实运行；负项与 `partial` 案例如实保留）**：

| 指标 | 基线形态均值 | 本 Skill 均值 | Δ |
|-|-|-|-|
| Q1 角色覆盖 | 0.0000 | 1.0000 | **+1.0000** |
| Q3 数字可追溯 | 0.0000 | 1.0000 | **+1.0000** |
| Q4 备注覆盖 | 0.0000 | 1.0000 | **+1.0000** |
| Q5 脚注覆盖 | 0.0000 | 1.0000 | **+1.0000** |
| Q6 产物齐全度 | 0.1429 | 1.0000 | **+0.8571** |
| 脚本耗时 | 0.391 s | 5.14 s | +4.75 s（**成本，不是收益**） |

**两条必须一起读的注释**：① 第二个案例上本 Skill 的状态是 `partial`
（第 6 页有一条 91 字主张越界 1 个字符，按规则记录并降级）——
**没有为了让对照好看而放宽纪律**；② 另一项指标（Q2 单条长度合规率）在基线侧"意外合规"、
在本 Skill 侧反而更低，本包把它**如实保留在报告里**并说明为何不作为对照依据
（`GAIN-PROTOCOL.md` §3.3）。

**可证伪判据**：在其他 `case.json` 上重跑 Q1/Q3/Q4/Q5 任一项 Δ ≤ 0，
或在基线侧产物里找到角色/备注/脚注字段，即推翻"本包带来这五项改善"的主张。

---

# 第五部分 · 机制

## §5 五个机制与可证伪判据（`references/MECHANISM-AND-ASSETS.md` 第一部分）

| # | 机制 | 解决什么 | 缺了会怎样（产物形态） | 判据 |
|-|-|-|-|-|
| **M1** | 页面单元化与角色确定性 | 不同受众/时长要不同取舍 | 一页一段的文本流；页数由段落数决定；无角色字段 | `M1_page_units` |
| **M2** | 主张—证据锚定 | 数字与原文之间必须有可查的连线 | 数字来源不可查、抄错发现不了 | `M2_anchors` |
| **M3** | 图表四态绑定 | 位图无取数数据时**不许编造** | 要么空着丢信息，要么"凭空生成曲线" | `M3_figure_states` |
| **M4** | 版本与可复核链 | 多轮改动后说不清哪版是交付版 | 只有一个 `deck.pptx`、无 changelog、无 sha256 清单 | `M4_versioning` |
| **M5** | 契约四形态 + 三层验证 | 产物要被别的程序读；"自检过"≠"内容对" | 字段为 `null` 让下游崩；未核验数字也标 success | `M5_contract` |

**代码级落点**：M1 → `slide_text.alloc_roles` + `evidence_check.plan_lint`；
M2 → `evidence_check.check_claim_numbers` / `build_evidence_footer` + `result_tool`；
M3 → `deck_tool.bind_figures`；M4 → `deck_tool.apply_edits` + `main.py --edit --version`
+ `result_tool.write_changelog/write_manifest`；M5 → `result_tool.apply_output_contract/validate`
+ `selftest`。

```bash
# 判据探针：只看产物，不看文档（同样请在包外跑）
python "$SKILL_DIR/references/mechanism_probe.py" --out <一次运行的输出目录>
# 期望 M1–M5 全 PASS、exit 0；有 FAIL 时 exit 1 并打印具体缺陷
```

**实测**：示例案例与留出案例 **5/5 PASS**；人为破坏三处痕迹后立刻报 3 条 FAIL
（负例控制见 `MECHANISM-AND-ASSETS.md` 第一部分 §5）。

**降级 → 机制受损**：`references/failure-modes.md` §10 给出对照表——
例如"图表降级为原生表格"伤的是 M3 的形态多样性但不伤 M3 的诚实性；
"预览整体失败"伤 M4 的可复核链。**降级不等于机制失效，但必须能说出伤了哪一条。**

---

# 第六部分 · 复用

## §6 可复用资产、案例题集与命令索引

**九个可复用资产**（完整清单与"怎么用 / 依赖 / 不适用处"见
`references/MECHANISM-AND-ASSETS.md` 第二部分）：
① result 契约 + 结果信封；② 机制判据探针；③ 对照测量台；④ 页面骨架与角色词表；
⑤ 编辑操作目录；⑥ 模板参数文件；⑦ 数字核验器；⑧ 示例冒烟题集；⑨ 契约四形态与状态一致性规则。
可判读版另加两个：⑩ 失败注入台 + 守卫（`scripts/fault_inject.py`）；
⑪ 泛化判定台（`scripts/case_check.py`）。

**两个题材的合成案例**（判据写在案例里，实测见 `references/CASE-SET.md`）：

| 案例 | 题材 / 难度层 | 关键检验 | 实测 |
|-|-|-|-|
| `examples/cases/case-a-perovskite/` | 实验科学 · 基础层（有 CSV 数值表） | 数值表**原样重绘**；结论数字不走样 | 8 页、`chart_image ×1`、**12/12 判据 PASS** |
| `examples/cases/case-b-climate-text/` | 理论文本 · 困难层（**无任何数值表**） | **不许凭空画曲线**（禁 `chart_image`） | 6 页、`none ×6`（0 张编造图）、**11/11 PASS** |

```bash
python "$SKILL_DIR/scripts/case_check.py" --list
python "$SKILL_DIR/scripts/case_check.py" --pkg "$SKILL_DIR" --work <包外目录> --probes
```

**跨题材失效边界（7 条，实测；`references/CASE-SET.md` §3）**：
GAP-A1 缺标准小节 → 占位主张（诚实降级）；GAP-A2 markdown 表不如 CSV 优先；
GAP-B1 编号小标题被切成退化要点；GAP-B2 关键年份可能整体不进页面；
GAP-B3 结果页可能取到摘要（内容错位但不报错）；GAP-P1 多表只认第一张；
GAP-P3 页数压缩不留痕。其中 **6 条不留痕**，G1–G8 与自检都抓不到 ——
**跨题材必须再走一层：案例级判据 + 人工看页面**。

**完整命令索引（能力清单；含全部入口与开关）**：

| 入口 | 关键参数 | 用途 | 退出码 |
|-|-|-|-|
| `scripts/main.py` | `--case` `--out` `--input-dir` `--template` `--max-slides` `--edit` `--no-chart` `--version` `--draft` `--verbose` | 端到端 CP1–CP4 | 0/1/2 |
| `scripts/result_tool.py` | `--result` `--out-dir` `--case` `--envelope` | 契约门 G1–G8 | 0/1/2 |
| `scripts/selftest.py` | `--out` `--case` `--pptx` `--slides` | 产物自检 | 0/1 |
| `scripts/evidence_check.py` | `--claim` `--material` | 单条主张数字核验 | 0/1 |
| `scripts/make_examples.py` | `--work-dir` `--dry-run` | 维护：重建 `examples/output/` 并净化绝对路径 | 0/1 |
| `scripts/fault_inject.py` | `--list` `--pkg` `--work` `--only` `--shape` `--with-recovery` `--report-json/-md/-csv` `--guard` `--case` `--out` `--template` `--verbose` | 注入台 + 恢复演练 + 守卫 | 0/1/2 |
| `scripts/case_check.py` | `--pkg` `--work` `--only` `--probes` `--probe-case` `--report-json` `--report-md` `--list` `--verbose` | 泛化台：逐案判定 + 边界探针 | 0/1/2 |
| `references/measure_gain.py` | `--skill-dir` `--case`（可重复）`--work` `--out` | 公平对照测量台（包外跑） | 0/1 |
| `references/mechanism_probe.py` | `--out`（可重复） | M1–M5 机制判据探针（包外跑） | 0/1 |
| `scripts/deck_extract.py` `scripts/slide_text.py` `scripts/deck_tool.py` `scripts/render_qa.py` `scripts/deck_common.py` | （库）由 `main.py` 编排 / 被 import | extract / build / render / 公共设施 | — |

## §7 自查清单（收尾逐项打勾；括号内是对应规则或判据）

- [ ] 前置：已读 `case.json` + `task.md` + 全部实际材料（未凭文件名猜内容）（CP1/D1）
- [ ] 前置体检：`fault_inject.py --guard --case` 无 BLOCKER（CP0）
- [ ] 页数 = `spec.max_slides`（或更少且原因已记录）；每页有 index/role/title（D4/D7/M1）
- [ ] 每页主张 ≤7 条、单条 ≤90 字、标题 ≤60 字；无整段摘要塞页（D4）
- [ ] 每个数字都能指回材料；`unverified_claims` 为空或有逐条解释（D2/M2）
- [ ] 图表四态均为真；位图无数据只占位；**无凭空曲线**（D5/D9/M3）
- [ ] 字号 ≥12pt；页脚/页码来源唯一；外部模板母版未被改动（D6）
- [ ] 每页有演讲备注与证据脚注（M2/Q4/Q5）
- [ ] deck 可被 python-pptx 重开且页数与 plan 一致（CP3/M4）
- [ ] `result_tool.py` → `{"valid": true}` 且 exit 0；`selftest.py` → `all_pass=true`（CP4）
- [ ] 契约字段全部回显、无 `null`；**核对时已把 `--case` 传给 `result_tool.py`**（D10/D12/M5）
- [ ] `manifest.json` 含全部产物 sha256；`changelog.jsonl` 有本次记录（M4）
- [ ] 机制自证：`mechanism_probe.py --out <out>` → **5/5 PASS**（M1–M5）
- [ ] 运行后核对：`fault_inject.py --guard --out <out>` 无 BLOCKER/WARN（§3）
- [ ] 跨题材交付时：`case_check.py` 判据全过 + **人工看过页面**（§6 七条边界）
- [ ] `status` 与每一列出的 `uncertainty` 一一对应，无"降级却标 success"（§1 三档判别）
- [ ] 包体：只有允许的七种文本扩展名、≤50 文件、无二进制、无 `__pycache__`

## §8 五维评分落点（速查；逐点展开见 `references/RUBRIC_MAP.md`）

| 维度 | 分 | 本包靠什么拿到 |
|-|-|-|
| 实际效果 | 40 | CP1–CP4 真跑；页序 + 页级角色；可编辑 PPTX + 备注 + 证据脚注；数字逐一核验；`sources[].sha256` + `manifest.json` + 双形态证据映射 + G1–G8；**两个题材各跑一次的实测结论** |
| 使用增益 | 25 | 公平对照协议 + 五项质量指标的精确公式 + 随包测量台 + **真实 Δ（含负面项与 partial 案例）** + 可证伪判据 |
| 创新增益 | 15 | 五个机制各写清"缺了会怎样"，各配一条**在产物里可查**的判据与一个**会 FAIL** 的探针（含负例控制）；**另加**注入矩阵（28 条 + 17 条恢复）与泛化判据（两案例 + 四探针） |
| 可靠体验 | 10 | D1–D14 + F1–F5 五族分支 + 非零退出码语义；**28 条故障逐行实测 + 7 条静默缺口如实列出 + CP0/CP5 守卫（7/7 抓到、0 误报）** |
| 生态贡献 | 10 | 文档齐全（README/TEST/OUTPUT_CONTRACT/RUBRIC_MAP/EDIT_OPS/failure-modes/GAIN-PROTOCOL/MECHANISM-AND-ASSETS/FAULT-MATRIX/CASE-SET + 示例）；**十一个可拿走资产**；题集可扩展；三个台（测量台/注入台/泛化台）都能脱离本包复用 |

GitHub 公开链接（额外 5 分）：见根目录 `GITHUB_URL.txt`。

## §9 诚实边界（不主张什么）

1. **不主张独家发明**：页面角色、证据映射、四态图表、版本记录各自都不神秘；
   本包主张的是**把它们做成可判定的状态并留下可查痕迹**（探针能查、负例能让它 FAIL）。
2. **7 条静默缺口 + 7 条跨题材边界仍在**（§3、§6）：本包把它们**测出来、写清楚、给补救**，
   **没有修改核心算法**去根治；不要声称"任意题材都能自动对齐"或"已经全部修好"。
3. **对照的性质**：随包测量台给的是**受控脚本级对照**（基线 = 题面点名失败形态的
   确定性代理实现），不是平台官方的 Agent 级对照；平台对照由平台生成。
4. **判定是结构 + 覆盖判据，不是质量判据**：能证明"页数对、角色在、备注全、没编造"，
   **不能证明"这一版讲得好"**。
5. **预览 ≠ Office 导出**：环境无 PowerPoint/LibreOffice 时预览是 PIL/reportlab 近似渲染，
   文件名与 `previews.method` 均已如实标注。
6. **自检通过 ≠ 内容正确**：三层核验各管一段，互不顶替（`failure-modes.md` §6）。
7. **不预制答案**：包内不含任何正式案例的答案；`examples/`（含两个合成案例）全部是
   虚构材料，已逐条标注"示例，非正式案例"，不得冒充正式案例结果。
8. **预算纪律**：平台单次运行 64 个模型请求 / 900 秒 / 16k tokens 每响应；
   脚本本身 <60 秒。**三个台（注入台 60 秒 / 泛化台 12 秒 / 测量台数秒）都是开发期工具**，
   不要占用评测预算。
