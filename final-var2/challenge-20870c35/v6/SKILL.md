---
name: academic-talk-organizer
description: >
  组织学术汇报内容（学术 PPT 页面组织）：从论文/研究材料到可讲、可编辑、证据可追溯的演示文件。
  当输入包含科研论文材料、研究报告、组会/答辩/评审任务、听众与时长、页数与模板约束、讲稿或备注需求，
  关键词如 学术汇报、答辩PPT、组会汇报、slides、deck、页码规划、讲稿、备注、问答准备、听众适配、
  叙事顺序、汇报内容组织、evidence mapping、模板适配、plan contract、quality gates、
  决策规则、状态一致性、失败注入、降级实测、静默失败、增益对照、机制、可复用资产、
  多案例泛化、题集、失效边界 时使用本 Skill：
  读真实材料 → 抽取研究问题/方法/结果/局限 → 生成页级计划（scaffold_plan）并经计划契约门
  P1–P8（validate_plan + assets/plan.schema.json）校验 → python-pptx 生成可编辑 .pptx
  （模板适配或内置主题；确定性元素命名 + 讲稿/备注 + 图占位）→ verify_deck 校验
  → PIL 渲染 PNG 预览 → evidence_audit 逐字审计 → finalize_result 写含证据映射、来源、
  不确定性、审计链路的 result.json。严格以真实文件为准，不臆造数据，不提交预制答案；
  二进制示例输入（PDF/PNG）由 make_synthetic_inputs.py 在运行时生成，包内只含 UTF-8 文本资源。
  本包是 **v6 全维合并版**：把「决策显性化（v1）· 增益可验证（v2）· 机制与复用（v3）·
  失败注入演练（v4）· 多案例泛化题集（v5）」五条线的实质内容合成一个包，
  SKILL.md 按 **输入→执行→失败→增益→机制→复用** 重排并索引到各 reference。
---

# 学术汇报内容组织（academic-talk-organizer）· v6 全维合并版

面向「玻尔产品周赛 · 学术效率 · 第三期」challenge-20870c35（slides 组）。
把**已有**的论文/研究材料组织成：结构清楚、证据可追溯、可编辑、符合听众与模板约束的学术汇报产物。
本 Skill 不负责论文精读成文、写作成稿与科研绘图本身（相邻课题负责），只负责
**从已有内容材料到可讲页面的组织与交付**。

> **题面两条硬约束（Runtime contract 原文）**：
> ① `Skill resources: at most 50 UTF-8 text files, 500KB each and 2MB total, no symlinks.`
> ② `Runtime artifacts may be binary and are retained independently of final JSON validity.`
> ⇒ 提交资源**只有文本**（`.md/.py/.json/.txt/.csv/.yaml/.yml`），`.pptx/.png/.pdf` 等**一律由脚本运行时生成**；
> 包内不含任何本机绝对路径、无 `__pycache__`、无符号链接。逐类处置见 §6。

## 0. 这个包由五条线合成（读之前先知道每部分回答什么问题）

| 线 | 回答的问题 | 主要落点 | 详细 |
|-|-|-|-|
| v1 决策显性化 | **该怎么做、失败时怎么办** 从散文变成规则 | §3 检查点 CP1–CP6、§4 决策规则 D1–D23、`scripts/check_status_matrix.py`（状态自洽性机器判定） | §4 · `references/failure-modes.md` |
| v2 增益可验证 | **加载本 Skill 相对基础形态多出了什么** | `COMPARE.md`（对照口径 + 不利结果）、`scripts/gain_ab.py`、`references/GAIN-PROTOCOL.md` | §5 |
| v3 机制与复用 | **为什么这些步骤不能省、哪些能整块拿走** | 八个机制 M1–M8、可复用资产清单、`assets/page-gold-standard.json` | §7 · `references/MECHANISM-REUSE.md` |
| v4 失败注入演练 | **坏输入会不会静默通过** | `scripts/fault_inject.py`（四族 14 条注入 + 1 条对照真跑）、`references/VALIDATION-EVIDENCE.md` 第 I 部 | §6 |
| v5 多案例泛化 | **换个题材还成不成立** | `examples/cases/` 两个合成案例、`references/VALIDATION-EVIDENCE.md` 第 II 部 | §8 |

> **本包的一句话主张**：一个学术汇报 Skill 的可信度不来自"在示例上跑通了"，
> 而来自三件事同时成立 —— **正常路径可复现**（§3）、**坏路径不静默**（§6）、
> **换题材不崩且边界公开**（§8）。三件事在本包里都有**实测记录**，不是声明。

## 1. 用途与适用条件

- **适用**：平台固定 3 个案例（组会 / 答辩 / 评审类型的学术汇报内容组织），要求：
  提取研究问题-方法-结果-局限主线 → 页级主张+图表引用+讲解顺序 → 按模板生成可编辑演示文件
  与讲稿/备注 → 每页保留源材料定位并检查导出渲染。
- **不适用/边界**：不承接论文精读成稿、学术写作、科研绘图素材生产；不代替用户下科学结论；
  页面内容一律取自源材料逐字引文（`quote`），不改写事实、不补造数据。
- **运行环境**：Python 3.8+，必需第三方库仅 `python-pptx` 与 `Pillow`；
  `pypdf`（或 PyPDF2）为 PDF 可选解析器，缺失时按「未解析」如实降级，不影响其余链路。
  全包无网络依赖、无 cwd 依赖（脚本全部用 `os.path.dirname(__file__)` 自定位）。
  **缺任何依赖都不崩**：`python-pptx` 缺失 → 跳过 deck 并降级为 `partial`（其余产物照常）；
  `Pillow` 缺失 → 跳过预览（非致命）；`pypdf` 缺失 → PDF 记未解析。见 §4 的 D15。
- **本机实测环境**：Python 3.13.9 / python-pptx 1.0.2 / Pillow 12.3.0 / pypdf 6.14.2（记录见 `TEST.md`）。

## 2. 输入

### 2.1 平台运行期输入

| 路径 | 内容 |
|-|-|
| `/input/case.json` | 案例标识 `case_id`、`title`、`report_goal`、`audience`、`duration_min`、`slide_count`、`report_type`、`materials`（材料清单，可为 `{path,role}`）、`template`/`start_deck`（可选模板或起始演示）、`figure_files`（可选 图表引用→图片路径 映射）、`output_contract`（可选字段声明） |
| `/input/task.md` | 任务说明；可能含 output_contract 声明（fenced JSON 或字段表） |
| 材料目录 | `case.json` 中列出的文本/PDF（缺省取 `<case 目录>/materials`），类型不限：`.md/.txt/.pdf` 与图片附件 |

**必须实际读取文件内容**（`main.py` 已按真实路径读取并逐文件解析记录），
不得根据标签/文件名预设内容。`main.py` 自动发现材料目录中的 md/txt/pdf/图片。

### 2.2 三处"输入决定行为"的开关（**先看这里，能省一轮返工**）

| 输入字段 | 决定什么 | 实测边界（**必读**） |
|-|-|-|
| `report_type` | 叙事块顺序与块集合（`templates/talk_config.json` 配置驱动）。`defense` 含 `agenda`+`innovation_limits`；`review` **结论先行**（`conclusion` 早于 `method`）；`group_meeting` 无 `agenda` | ⚠️ **不在配置里的类型会被静默替换成 `group_meeting`**（`agenda` 页消失）。权威值看 `talk_plan.json.narrative.report_type`；要支持新类型请在 `templates/talk_config.json` 加配置（纯 JSON，无需改代码）。见 §8.2 |
| `slide_count` / `duration_min` | 冻结页数（P3 门）与每页秒数 | ⚠️ **页数被硬钳制在 [6, 30]**（`scaffold_plan.py`），越界时案例里的值会被静默改写、**不报不确定度**。把输入值当"请求值"，**以 `result.json.slide_count` 为准**。见 §8.2 |
| `materials` 的语言/句式 | 能否产出**逐字引文页** | ⚠️ claim 分类词表**以中文研究动词为主**。纯英文材料能抽出 claim（实测 6 条）但会被全部归为 `general`，导致**内容页全部退化为概括页**（实测 11/11）。v6 已把这种情形升级为可见降级（D21），但**不会**因此产出引文页。见 §8.2 |

### 2.3 输出（`--out`，平台运行期即 `/app/output`）

```
result.json            # 唯一评分产物：契约字段 + 主结果 + 证据定位 + status/sources/
                       #   uncertainty/change_records/environment + audit{plan_gates,evidence,deck,gates}
talk_plan.json         # 页级计划（叙事顺序、每页主张/证据/讲稿/问答）——可编辑中间产物
plan_gates.json        # 计划契约门 P1–P8 结果（assets/plan.schema.json 驱动）
evidence_map.json      # 源文件 → {用到它的页, 图表引用} 反向映射
evidence_audit.json    # 逐页逐字引文审计（含 derived/占位/数字对源说明）
deck_audit.json        # deck 机器校验（打开/页数/备注/claim 元素/OPC/规范化 sha）
editable_deck.pptx     # 可编辑演示文件（python-pptx；模板适配或内置主题；确定性元素命名）
                       #   ← 运行期产物（二进制），不进提交资源
previews/
  cover_preview.png    # 封面预览（PIL 模拟，如实标注）        ← 运行期产物
  slide_0NN.png        # 逐页缩略图（PIL 模拟）                ← 运行期产物
  preview_grid.png     # 整包缩略网格                          ← 运行期产物
  preview_manifest.json# 预览清单、渲染方法、字体探测结果与限制说明
self_check.json        # validate_result + check_contract + 门 + 确定性探针
```

> `result.json` 里的路径一律是**可移植形式**：写盘时把本机绝对路径改写成相对案例目录的路径
> （如 `materials/fig2.png`），POSIX 运行期路径（`/input/...`、`/app/output/...`）原样保留。
> 产物清单与实测数量见 `examples/EXPECTED-OUTPUT.md`；字段契约全文见 `references/OUTPUT_CONTRACT.md`
> （该文件的字段块在 v6 中**逐字未改**）。

## 3. 执行（检查点 CP1–CP6，按序执行，别跳步）

> **自定位（重要）**：`$SKILL_DIR` = 本包根目录（含 `SKILL.md` 的那个目录；
> 平台安装后即 `/skills/weekly-skill`）。所有脚本用 `os.path.dirname(__file__)` 自定位，
> **命令与当前 cwd 无关** —— 在任意目录执行下面任何一条都能跑通。

### CP1 · 输入契约
1. 读 `case.json` 与 `task.md`（约束 + 可能的 output_contract）；缺任一关键字段按 §4 的
   D6/D7/D19 处置并记录。**同时按 §2.2 检查三处开关**（汇报类型是否已配置、页数是否会被钳制、材料语言）。
2. 解析材料目录（含显式清单 + 自动发现）；缺失/未解析材料如实标记（D1/D2）。
3. 解析模板/起始演示（显式参数 > case 字段 > 材料目录扫描）（D5/D18）；解析前先确认能打开。
4. 环境预检：探测 `python-pptx`/`Pillow`/`pypdf` 与系统中文字体，写入
   `result.json.environment` 与 `change_records`（决定本次能产出哪些产物，见 D15）。

### CP2 · 计划门
5. 运行主流程（一条命令完成 抽取→规划→.pptx→校验→预览→审计→result.json→自检）：
   ```bash
   python "$SKILL_DIR/scripts/main.py" \
     --case /input/case.json \
     --task /input/task.md \
     --out /app/output
   ```
   - 内部：`scaffold_plan.build_plan` 产出页计划并写 `talk_plan.json`；
     `validate_plan.validate_plan` 按 `assets/plan.schema.json` 执行 P1–P8，
     结果写 `plan_gates.json`；未全过 → D9 降级（继续生成 honest 产物，不中断）。
   - 退出码：**0** = 已产出通过 validate+contract 的 `result.json`（其 `status` 说明
     `completed` 还是 `partial`）；**1** = 没有可用的契约结果；**2** = 参数用法错误。
6. 需要手工精修计划时：改 `talk_plan.json`/`talk_config.json` 后重跑（注意重跑会重新 scaffold，
   如需锁定请修改 `talk_config.json` 的规则）。

### CP3 · 生成与校验门
7. 案例自带模板/起始演示 → python-pptx **打开并沿用其母版与版式**，页数按冻结计划重建
   （模板自带的示例页会被丢弃，见 D16；最终页数 == 冻结页数）；打开失败则按 D18 回落内置主题。
   无模板则用包内置主题（16:9 母版+主题色+底栏）。
   每个 Skill 创建的图形元素带确定性命名（`page-claim-NN`/`page-figure-NN` …）。
   图片文件按引用号绑定（`Fig. 2 → materials/fig2.png`）；材料没有对应图片 → 页内诚实占位框（D4）。
8. `verify_deck` 校验 deck（打开、页数==计划、每页备注与 claim 元素、OPC 完整），
   结果写 `deck_audit.json`；未过 → D11。缺 `python-pptx` → D15。

### CP4 · 渲染门
9. 预览自动为 **PIL 模拟渲染**（每张 PNG 带水印，`preview_manifest.json` 说明渲染方法、
   字体探测结果与占位图清单）；`--skip-previews` 可跳过逐页缩略图只留封面+网格。

### CP5 · 审计与收口门
10. `evidence_audit` 逐页逐字核验引文（derived 页按概括语如实记录），写 `evidence_audit.json`；
    未过 → D13。**另查 D21**：抽出主张却一条都没逐字上页时升级为可见降级。
11. `finalize_result` 组装 result.json（output_contract 四形态回显，禁 null）+
    `self_check.json`（validate + contract + 门快照 + 确定性探针）；`selftest.py`
    可对任意输出目录独立复核（G1–G10 + `--package-check` 包约束 G10）。
12. 人工核对 §9 自查清单后再收尾；按需精修后重跑。

### CP6 · 三件"自证"事（交付前必须做，别跳过）
13. **换题材复跑**（v5）：两个合成案例都要 `exit 0`，并对照 §8.1 的期望结构表逐项核。
    ```bash
    OUT="<包外空目录>"
    python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/cases/case-a-muon-defense/case.json" --out "$OUT/a"
    python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/cases/case-b-scrna-review/case.json"   --out "$OUT/b"
    ```
14. **失败注入演练**（v4）：在**包外**沙箱里把四族 14 条注入 + 1 条对照逐个注入并真跑，要求 **0 静默失败**。
    ```bash
    python "$SKILL_DIR/scripts/fault_inject.py" --sandbox "<包外空目录>"      # 15 行（14 条注入 + 1 条对照组）全跑
    python "$SKILL_DIR/scripts/fault_inject.py" --list                      # 只看注入清单
    ```
    脚本会**主动拒绝** `--sandbox` 落在技能包内部（包内跑会生成 `__pycache__` 而使提交包不合规）。
15. **状态自洽性机器判定**（v1）：把"状态与文件内容是否自相矛盾"变成退出码。
    ```bash
    python "$SKILL_DIR/scripts/check_status_matrix.py" <out>
    ```
16. **增益对照可复算**（v2，可选但推荐）：`scripts/gain_ab.py` 在同一输入上对照
    "不加载 Skill 的基础形态"，输出 A/B 两臂的结构化指标；口径与**不利于本包的结果**
    见 `COMPARE.md` 与 `references/GAIN-PROTOCOL.md`。

## 4. 失败（决策规则 D1–D23 + 三处留痕）

> 全表（含优先级裁决与代码对应）见 `references/failure-modes.md`。以下是最常用的部分。

| 规则 | 情形 | 处置（全部如实记录到 `uncertainty` / `change_records`） |
|-|-|-|
| D1 | 材料缺失 | `sources` 中 `kind=missing`；status 视影响降 `partial`；不编造其内容 |
| D2 | 材料是 PDF 且无 pypdf / 解析失败 | 记录 `parsed=false` + 原因；其余材料照常 |
| D3 | PDF 抽取丢公式/符号；**或抽取到 0 个非空文本行**（扫描件） | 前者 quote 以抽取文本为准并注明代理方式；后者**记未解析**（v4 修正，不再冒充成功解析） |
| D4 | 论文缺图/图分辨率低/图损坏 | 页内**诚实占位框**（标注"材料未提供图片文件"），notes 提示对照原文；坏图跳过 |
| D5 | 无模板/模板路径失效 | 采用内置主题并在 `artifacts.template_used`/`deck_mode` 注明 + `uncertainty` 记明 |
| D9 | 计划门 P1–P8 未全过 | 记录 errors；仍生成 honest 产物；`status→partial`；uncertainty 列出 |
| D15 | 缺 `python-pptx`（或连带 Pillow） | **不崩**：跳过 deck，`status→partial`，`editable_deck=null` + `deck_limitation`；其余照常落盘，命令仍返回 **0** |
| D16 | 模板自带示例页 | 保留母版/版式，**丢弃自带页**后按冻结计划重建；最终页数 == 冻结页数 |
| D17 | 材料为空 / 全部不可解析 | 只产出结构性页面；`status→partial` + uncertainty 明写；不据标签补造内容 |
| **D18** | **模板存在但不是合法 OOXML** | `try` 打开失败 → 记 `template_load_error` → **回落内置主题**；异常进 `change_records`(step=`deck-source`) 与 `uncertainty`；**不得**把整轮记成 `failed` |
| **D19** | **`task.md` 声明了 output_contract 却用不起来** | 解析器带回**具体原因**；写 `change_records`(step=`contract`) + `uncertainty`，`status→partial` |
| **D20** | **契约声明了本包产不出的字段** | 按声明容器类型回落 `""`/`[]`/`{}`/`0`，**禁止 `null`**；`contract.applied` 记录全部已回显字段 |
| **D21** | **抽出主张却一条都没逐字上页** | 判据：主张 ≥3 且 内容页 >0 且 `derived_pages >= content_pages` ⇒ `change_records`(step=`audit`) + `uncertainty`，`status→partial`。**不**把概括页伪装成引文页 |
| **D22** | **未知 `report_type`** | 静默退回 `group_meeting`（`agenda` 消失）。**已知边界，未修**：以 `talk_plan.json.narrative.report_type` 为准；见 §8.2 |
| **D23** | **`slide_count` 落在 [6,30] 之外** | 硬钳制且不报不确定度。**已知边界，未修**：以 `result.json.slide_count` 为准；见 §8.2 |

### 4.1 三处留痕：降级必须"看得见"

`status` 只是一个结论；要能独立复核，原因必须在**三处**同时对得上
（`scripts/fault_inject.py` 的"非静默"判定就用这张表）：

| 落点 | 字段 | 复核方式 |
|-|-|-|
| ① 状态 | `status`（`completed`/`partial`/`failed`） | 读 `result.json.status`；`failed` 时再看 `error` |
| ② 声明 | `uncertainty[]`（每条 `{item, impact, mitigation}`） | **≥1 条**才算这条降级被声明过 |
| ③ 过程 | `change_records[]`（每条 `{at, step, action}`） | 按 `step` 过滤（`material`/`deck`/`deck-source`/`preview`/`plan-gate`/`contract`/`audit`） |

细粒度补充落点（不替代上表）：`artifacts.editable_deck=null` + `deck_limitation`（缺 pptx）、
`artifacts.deck_mode.template_load_error`（模板打不开）、`sources[].parsed/kind/note`（材料）、
`audit.plan_gates.valid`、`contract.declared_source`/`contract.applied[]`。

> **统计口径提醒（v5 实测后补）**：`status=completed` 只表示"契约五条件满足"，
> **不**表示"页面都有逐字引文"或"冻结页数被完全遵守"。后两者要分别看
> `evidence_audit.derived_pages` 与 `result.json.slide_count`（与案例输入比对）。

## 5. 增益（相对基础形态多出了什么，以及**不利于本包**的结果）

- **对照口径 + 逐项可判定差异 + 不利结果**：`COMPARE.md`（基础做法 vs 加载本 Skill，
  每行都指向 `result.json`/`talk_plan.json` 的可判定字段）。
- **可复算脚本**：`scripts/gain_ab.py`（A 臂 = 内置确定性基线模拟器，B 臂 = 本 Skill；
  输出 A/B 两臂的结构化指标）。口径全文与**机器可读对照记录**见 `references/GAIN-PROTOCOL.md`
  （附录内联了原 `gain-run-record.json` 的 JSON，可原样存成文件使用）。
- **不自报分数**：题面禁止文字自述替代运行证据 ⇒ 本包只提供口径、判定命令与**不利结果**，
  正式对照由平台在固定案例上执行。同输入双跑的确定性由 `self_check.json.determinism`
  与 `selftest.py` 的 `determinism_probe` 证明（`TEST.md` T4：JSON 与 PNG 逐字节相同）。

## 6. 失败注入演练（v4；"坏路径不静默"的机器证据）

```bash
python "$SKILL_DIR/scripts/fault_inject.py" --sandbox "<包外空目录>"      # 建议：全跑
python "$SKILL_DIR/scripts/fault_inject.py" --sandbox "<包外空目录>" --inject F07,F12
python "$SKILL_DIR/scripts/fault_inject.py" --sandbox "<包外空目录>" --skip-previews   # 更快，语义不变
```

- **四族 14 条注入 + 1 条对照**：I 输入形态（`case.json` 非法 / 缺 `case_id` / 材料缺失 / 零材料 / 无文本层 PDF）、
  T 模板形态（路径失效 / 容器损坏 / 自带示例页）、D 依赖形态（python-pptx / Pillow / pypdf 导入遮罩）、
  C 契约形态（契约块非法 JSON / 空契约 / 多声明字段）。
- **先归一化基线**：脚本自动补齐示例二进制输入，使对照组 `F00` 为 `completed`
  —— 否则每条注入都会是 `partial`，分不清"故障造成的降级"和"示例不完整造成的降级"。
- **判定是四要素齐全性**（退出码 + `status` + ≥1 条 `uncertainty` + ≥1 条 `change_records`），
  缺任一即 `silent_failure`；脚本退出码 `0` = 全 MATCH 且 0 静默失败。
- **实测结果**：15 行全 MATCH、**0 静默失败**；逐行的实测退出码/status/uncertainty 原文/耗时
  在 `references/VALIDATION-EVIDENCE.md` **第 I 部**。
- **该演练反向暴露并已修的 4 类真实缺陷**（逐条：文件 / 增删行数 / 理由，见该文件 §3）：
  ① 模板容器损坏**打死整轮**（`deck_builder.py` + `main.py`）；
  ② 无文本层 PDF 被记成**成功解析**（`evidence.py`）；
  ③ 契约块不可用时被**静默吞掉**（`common.py` + `main.py`）；
  ④ 契约字段落 **`null`**，与 `OUTPUT_CONTRACT.md` §1「禁止 null」矛盾（`common.py`）。

## 7. 机制（为什么这些步骤不能省）与复用（哪些能整块拿走）

- **八个机制 M1–M8**（计划契约门先行 / 逐字证据审计 / 叙事配置化 / 问答预演 /
  模板适配与自带页丢弃 / 契约四形态与状态可见性 / 运行时文本化资源 / 确定性探针）：
  每个机制的"没有它会怎样"与**可证伪判据**见 `references/MECHANISM-REUSE.md` §1、§9。
- **可复用资产清单与复用步骤**：同文件 §2（页级金标准 `assets/page-gold-standard.json`、
  叙事模板 `templates/talk_config.json`、计划 schema、校验脚本、`templates/HUMAN-TEMPLATES.md` 人核清单）。
- **跨包迁移**：`fault_inject.py`（换成自己的 `--case` 即可复用四族注入法）、
  `check_status_matrix.py`（状态自洽性判据）、`selftest.py --package-check`（资源形态硬门）。

## 8. 多案例泛化（v5；"换题材还成不成立"）

### 8.1 两个合成案例（不同题材，都在 `examples/cases/`，均可直接复跑）

| 案例 | 题材 | 汇报类型 | 时长/页数 | 难度 | 实测 |
|-|-|-|-|-|-|
| `case-a-muon-defense` | 凝聚态实验物理（μSR 内场分布反演） | `defense` 答辩 | 25 min / 15 页 | L2 | `exit 0` · `completed` · P-gates 8/8 · `evidence_audit 11/11 ok, derived 3` |
| `case-b-scrna-review` | 计算生物学（单细胞计数去噪） | `review` 评审 | 12 min / 8 页 | L3 | `exit 0` · `completed` · P-gates 8/8 · `evidence_audit 5/5 ok, derived 1` |

- **可判定的期望产出结构 + 可接受区间 + 难度层 + 逐案实测**：`references/VALIDATION-EVIDENCE.md`
  **第 II 部** §1/§2。B 案的块顺序里 `conclusion` 出现在 `method`/`results` **之前**
  ⇒ 叙事确实是**配置驱动**而非硬编码（同一套脚本、两种题材、两种量级）。
- **L1→L2→L3 的难度不是"材料更长"**，而是**约束互相冲突**（B 案：12 分钟 + 结论先行 +
  两个互相矛盾的指标必须同时上页）。

### 8.2 泛化边界（**如实写明**，每条都有实测支撑）

| # | 边界 | 实测行为 | 状态 |
|-|-|-|-|
| 1 | 未知 `report_type` | `status=completed`、P-gates 8/8，但 `talk_plan.narrative.report_type` 变成 `group_meeting`、`agenda` 页消失、`uncertainty` 无相关条目 | ⚠️ **已知边界，未修**（D22）。要以 `talk_plan.json.narrative.report_type` 为准 |
| 2 | `slide_count` 越界（实测 `duration_min=5, slide_count=40`） | 产出 **30** 页；`timing.seconds_per_slide=10.0`；P3 门比对**钳制后**目标故仍通过；无钳制说明 | ⚠️ **已知边界，未修**（D23）。根因 `scaffold_plan.py` 的 `max(6, min(30, ...))`；以 `result.json.slide_count` 为准 |
| 3 | 纯英文材料（实测 876 字符） | 修前：`completed` 但 `derived_pages=11/11`（11 个内容页全无逐字引文）⇒ 静默质量损失；修后：`partial` + `uncertainty` 增至 5 条（写明"抽出 6 条主张但一条都没逐字上页"） | ✅ **已修**（D21），附两案回归证据（两案仍 `completed`，未被误伤） |
| 4 | 听众信息缺失 | `expertise=familiar`、`background_ratio=0.18`、`audience.notes` 写明可覆写 | ✅ 按 D7 诚实降级（设计内） |

**未验证方向（明确声明没有实测数据，不作断言）**：材料数 >2 / 超长材料 / 非中非英材料 /
真实有文本层 PDF（该路径由 §6 的注入覆盖）/ 同一案例重复三次 / 模板适配下的两个新案例。

## 9. 自查清单（收尾前逐项确认）

- [ ] `result.json` 存在；`case_id` 与输入一致；`status` ∈ {completed, partial, failed}
- [ ] `output_contract` 声明字段全部出现在 result.json 顶层（`self_check.json → contract_check.valid == true`；四形态回显、无 null）
- [ ] **§2.2 三处开关已核**：`talk_plan.json.narrative.report_type` 与案例一致；
      `result.json.slide_count` 与案例冻结页数一致（不一致即被钳制）；
      材料语言是否在 claim 分类覆盖内（看 `evidence_audit.derived_pages` 是否等于 `content_pages`）
- [ ] `plan_gates.json` 与 `result.audit.plan_gates` 存在；P1–P8 未全过时 uncertainty 有对应条目
- [ ] 每一页（除封面/目录/问答备用页）都有 `evidence[0].locator`（L行号 · §章节）+ `quote` 原句
- [ ] `evidence_audit.json` 逐页核对过：逐字命中或 derived 概括语如实标注；所有 `evidence.source_file` 都能在 `sources[]` 中找到
- [ ] `editable_deck.pptx` 存在且能被打开（verify_deck 复核）；每页有讲稿备注；页数 == 计划
- [ ] 预览 PNG 存在且每张带「PIL 模拟预览」水印；`preview_manifest.json` 已说明限制与字体探测结果
- [ ] 数字可信：页面上的数字在源材料中可定位（warnings 已审查）
- [ ] 没有预置正式答案：`examples/` 仅为合成的接口示例（`case_id` 形如 `example-*`/`synth-*`），平台案例从 `/input` 实际读取
- [ ] 依赖缺失/材料异常时**如实降级**：`status=partial` + `uncertainty` + `change_records`（见 §4）
- [ ] **两个合成案例都跑过**且与 `references/VALIDATION-EVIDENCE.md`（第 II 部）§2 的期望结构表逐项对得上
- [ ] **失败注入演练跑过且为 0 静默失败**：`fault_inject.py --sandbox <包外目录>` 退出码 0；
      矩阵里没有 `silent_failure=true` 的行；每行要么 MATCH，要么写着"期望修订说明"并给出为什么原期望是错的
- [ ] **状态自洽性机器判定通过**：`check_status_matrix.py <out>` 退出码 0
- [ ] **资源形态硬门**（题面 Runtime contract）：只含 `.md/.py/.json/.txt/.csv/.yaml/.yml`；≤50 个 UTF-8 文本文件；
      单文件 ≤500KB；合计 ≤2MB；无符号链接；无 `__pycache__`/`.pyc`；**无本机绝对路径残留**
      （`python "$SKILL_DIR/scripts/selftest.py" <out> --package-check "$SKILL_DIR"` 机器查 + 人工 grep 盘符绝对路径）
- [ ] 包内**不存在任何**该七种扩展名之外的文件；二进制示例输入由 `make_synthetic_inputs.py` 运行时生成

## 10. 资源形态：为什么包内没有二进制，以及逐类处置

题面只允许 UTF-8 文本资源作为 Skill 资源（runtime artifacts 不在此列），因此本包**只用文本**表达规则、
脚本与示例；所有二进制一律改由脚本现场生成：

| 原本常见的二进制资源 | 本包的做法 |
|-|-|
| 内置模板 `*.pptx` | **不随包**：`deck_builder._new_deck()` 用 python-pptx 现场构建 16:9 母版/主题；案例自带模板时直接读取平台提供的模板 |
| 示例图 `*.png` | **不随包**：`scripts/make_synthetic_inputs.py` 用 Pillow 画纯几何示意图（带 `SYNTHETIC` 标注，不含测量值） |
| 示例 PDF | **不随包**：同一脚本手工构造最小 PDF（零第三方依赖、字节确定、pypdf 可解析） |
| 示例输出 `*.pptx/*.png/*.svg` | **不随包**：改为 `examples/EXPECTED-OUTPUT.md` 用**文字**列出应产出文件清单与实测数量 |
| 示例输出 `*.json` | **随包但净化**：只保留 `result.example.json` / `self_check.example.json`，且其中路径全部为相对形式 |
| 字体 `*.ttf/*.otf` | **不随包**：运行时按候选路径探测系统字体（`/usr/share/fonts`、`/System/Library/Fonts`、`C:/Windows/Fonts`），探测结果记入 `result.json.environment.cjk_font` 与 `preview_manifest.json`；找不到则用 Pillow 内置位图字体并在 manifest 记明 |
| `scripts/__pycache__`、`*.pyc` | **不随包**：提交前删除（`selftest.py --package-check` 的 G10 会检查） |

## 11. v6 的文件合并映射（守住 ≤50 文件，**内容未删**）

v6 把五条线的文档与资源合并到 49 个文件（上限 50）。**同一主题的 reference 文档被合并，逐字保留**：

| 合并后 | 由哪些文件合并（内容逐字保留）——**下表右列是合并前的原名，已不在包内** |
|-|-|
| `references/VALIDATION-EVIDENCE.md` | 原名 `FAULT-MATRIX.md`（v4）+ `CASE-SET.md`（v5）+ `assets/case-set.json`（v3，附录内联 JSON） |
| `references/failure-modes.md` | 原名 `failure-modes.md`（本包）+ `decision-rules.md`（v1） |
| `references/MECHANISM-REUSE.md` | 原名 `MECHANISM.md`（v3）+ `REUSE-KIT.md`（v3） |
| `references/CONTRACT-GATES.md` | 原名 `plan-contract.md` + `quality-gates.md` |
| `references/DECK-EVIDENCE-RULES.md` | 原名 `deck-rules.md` + `evidence-audit.md` |
| `references/GAIN-PROTOCOL.md` | 原名 `GAIN-PROTOCOL.md`（v2）+ `gain-run-record.json`（v2，附录内联 JSON） |
| `templates/HUMAN-TEMPLATES.md` | 原名 `narrative_template.md` + `slide-checklist-template.md` |
| `examples/cases/*/materials/paper_and_figures.md` | 每案的 `*_extract.md` + `figures.md`（两案各合一） |

> 每个合并段都在**段首**写明"本段原为独立文件 `X`"，因此可以逐段追溯回原文件；
> 指向旧路径的**交叉引用已同步改写**（14 个文件、共 48 行）。
