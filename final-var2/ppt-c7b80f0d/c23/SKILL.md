# 论文转学术 PPT（paper-to-academic-ppt） · 整合版（增益层 + 机制层）

> 本包整合了基线 Skill 与 2 个强化层,各层对应不同的评分维度:使用增益 25 · 创新增益 15 + 生态贡献 10。
> 各层内容**不重复**:决策层给规则与失败分支;增益层给对照协议与指标口径;机制层给机制说明与可复用资产。
> 建议使用顺序:先用「决策层」跑通并处理异常,再用「增益层」证明并度量改善,最后用「机制层」复用与扩展。
> 各层的原始文件都完整保留在本包内,不是摘要 —— 下面每一层都是可以独立执行的完整规范。

## 本包文件索引

- `GITHUB_URL.txt`
- `README.md`
- `TEST.md`
- `examples/EXPECTED-OUTPUT.md`
- `examples/README.md`
- `examples/case.json`
- `examples/deck-spec.json`
- `examples/task.md`
- `references/GAIN-PROTOCOL.md`
- `references/MECHANISM.md`
- `references/OUTPUT_CONTRACT.md`
- `references/REUSE-KIT.md`
- `references/RUBRIC_MAP.md`
- `references/failure-modes.md`
- `references/layer-naming.md`
- `references/slide-blueprint.md`
- `scripts/assetkit.py`
- `scripts/check_contract.py`
- `scripts/cli_io.py`
- `scripts/deckgen.py`
- `scripts/export_check.py`
- `scripts/gain_probe.py`
- `scripts/main.py`
- `scripts/make_synthetic_inputs.py`
- `scripts/make_template.py`
- `scripts/ooxml_kit.py`
- `scripts/preview.py`
- `scripts/spec_lint.py`
- `examples/materials/paper-mini.txt`
- `examples/output/README-EXAMPLE.md`
- `examples/output/evidence_map.example.json`
- `examples/output/evidence_mapping.example.md`
- `examples/output/result.example.json`

---

# 【增益层】公平对照协议与可测指标（目标维度:使用增益 25）

---
name: paper-to-academic-ppt
description: 把论文/研究材料转换成主线清晰、证据可追溯、可编辑的学术汇报 PPT。本版把"加载它到底强在哪"写成可测量的断言（GA1–GA5）与一条可复跑的命令（scripts/gain_probe.py），并用同一套评审函数对"朴素单遍流水线 / 本 Skill / 去掉页级方案的消融臂"三臂逐格测量；执行链为 Step 0–Step 6 + 闸门 Q1–Q3，异常按 H01–H14 处置。产物含可编辑 .pptx、逐页证据映射（md + json 同源）、近似预览与契约完整的 result.json。Use when a task asks to turn a paper or research material into an academic slide deck (论文转PPT、学术汇报PPT、slides from paper、presentation from paper), especially when /input/case.json and task.md are present and /app/output must contain the editable deck plus previews.
---

## 论文转学术 PPT（增益可验证版 · paper-to-academic-ppt）

学术汇报 PPT 这类任务最容易出现的一种失败是："看起来做完了，但说不出比不做强在哪里"。
本版本把这件事反过来做：**先写下要证明的增益断言，再给出测量它的命令，最后才谈流程**。

三个部件：

1. **执行链**（§4 Step 0–Step 6，含闸门 Q1/Q2/Q3）——保证每次运行都产出可交付物；
2. **处置规则**（§5 H01–H14）——保证出问题时行为可判定、降级有记录；
3. **增益测量**（§6 GA1–GA5 + `scripts/gain_probe.py`）——保证"更强"这句话可以被第三方在
   本机重跑出来，而不是靠叙述。

**不负责**：论文精读结论的生成、科研绘图本身的图形设计、学术写作润色。
**不使用预制答案**：正式运行只依据案例实际提供的文件；`examples/` 只演示接口。

---

### 1. 适用与触发

- `/input/case.json` + `/input/task.md` 存在，要求在 `/app/output` 产出演示产物；
- 或用户直接要求"把这篇论文做成学术 PPT / slides from this paper / 组会汇报"。

**适用**：单篇论文或研究报告 → 8–20 页学术汇报（页级主张 + 图表定位 + 讲解备注 +
模板适配 + 渲染记录）。**不适用**：判断论文结论真假、重画科研图、润色正文、
与材料无关的通用幻灯片——越界请求写进 `uncertainty` 并拒绝。

**与其他版本的关系**：本版包含"决策显性化"的全部内容（H01–H14 与五类异常一一对应），
并额外提供 §6 的可测断言与对照执行件。若只想看判断规则，读 §5 即可。

### 2. 输入输出与自定位

| 方向 | 路径（以环境实际挂载为准） | 内容 |
|-|-|-|
| 输入 | `/input/case.json` | `case_id`、`output_contract`、材料/模板定位、受众与页数约束 |
| 输入 | `/input/task.md` | 任务说明（存在时读取；缺失不阻断） |
| 工作 | `/app/work` | 抽取文本与图片、页级方案 `deck-spec.json` |
| 输出 | `/app/output` | `result.json`、`academic_deck.pptx`、`preview-approx-*.png`、`evidence_mapping.md`、`evidence_map.json`、`chart-*.png/.svg` |

**自定位**：`$SKILL_DIR` = `SKILL.md` 所在目录。脚本以
`os.path.dirname(os.path.abspath(__file__))` 自解析并 `sys.path.insert` 本目录，
**cwd 不是技能根也能跑**；因此所有命令统一写成：

```bash
SKILL_DIR="<SKILL.md 所在目录>"      # 平台安装到 /skills/weekly-skill 时即该路径
python "$SKILL_DIR/scripts/spec_lint.py" --spec /app/work/deck-spec.json
```

输入不在 `/input` 时，先探测 `CASE_PATH` / `OUTPUT_DIR` / cwd 下的 `case.json`，
**以实际可读文件为准**（H14）。

### 3. 资源清单（相对 `$SKILL_DIR`）

| 文件 | 作用 | 独立 CLI |
|-|-|-|
| `scripts/main.py` | 端到端编排（Q1 → 抽取 → 构建 → 预览 → Q3 → result.json） | `--case --out` 必填 |
| `scripts/gain_probe.py` | **本版新增**：三臂公平对照执行件（§6），产物只写 `--out` | `--out` 必填；`--arms`、`--repeat`、`--json` 可选 |
| `scripts/assetkit.py` | 素材层：材料定位、PDF 文本/图片抽取、表格数字重建图 | `--pdf --out` |
| `scripts/deckgen.py` | 生成层：模板适配、页级排版、备注、证据映射页、形状命名 | 打印记录 |
| `scripts/ooxml_kit.py` | OOXML 层：主题字体注入、命名、zip/XML 健全检查、命名审计 | 传 `.pptx` |
| `scripts/spec_lint.py` | **闸门 Q1**：deck-spec 结构校验（BL-1…BL-4） | `--spec` |
| `scripts/export_check.py` | **闸门 Q3**：契约 + 容器 + 命名 + 证据表一致性（G1–G8） | `--result --out-dir [--case]` |
| `scripts/check_contract.py` | 契约字段覆盖核对（读 `references/OUTPUT_CONTRACT.md` §1） | `--result --contract [--case]` |
| `scripts/preview.py` | PIL 近似预览（无 Office 引擎时的诚实渲染） | 打印记录 |
| `scripts/make_template.py` | 运行期生成回退模板（包内不携带二进制模板） | `--out [--name] [--no-starter]` |
| `scripts/make_synthetic_inputs.py` | 运行期生成合成夹具（几何占位图 + 两页 ASCII PDF） | `--out` |
| `scripts/cli_io.py` | 控制台加固（UTF-8 + `errors="replace"`） | 被各入口导入 |
| `references/OUTPUT_CONTRACT.md` | result.json 顶层字段 + 四形态回显 + G1–G8（**必读**） | — |
| `references/GAIN-PROTOCOL.md` | **本版新增**：公平对照协议 + 指标定义 + 真实对照记录 | — |
| `references/failure-modes.md` | 五类失败分支的处置与退出码（与 H01–H14 同号） | — |
| `references/slide-blueprint.md` | 论文→页面蓝图映射 + deck-spec schema + 证据表格式 | — |
| `references/RUBRIC_MAP.md` | 五维评分落点（以使用增益为主轴）+ 复核命令 | — |
| `references/layer-naming.md` | 分层命名规范（对象名 = 可编辑性的机器可查证据） | — |
| `examples/` | 最小示例（合成案例，明确标注"示例，非正式案例"） | — |

依赖：`python-pptx` 必需；`Pillow` 预览；`matplotlib` 可选（重建图）；
`PyMuPDF`/`pypdf`/`pdfplumber` 任一即可读 PDF。逐级回退见 §5 与 `failure-modes.md`。

### 4. 执行链 Step 0 – Step 6（闸门 Q1–Q3）

| Step | 动作 | 出口条件 |
|-|-|-|
| **0** | 读 `task.md` 与 `/input/case.json`：取 `case_id`、`output_contract`、材料/模板、受众与页数约束；解析 `$SKILL_DIR` | 已能说出"必须回显哪些字段" |
| **1** | **读实际文件**（不许按标签假设内容）：`python "$SKILL_DIR/scripts/assetkit.py" --pdf "<材料路径>" --out /app/work/extract` | `sources[]` 里有真实工具与页数/字数 |
| **2** | 按 `slide-blueprint.md` §1 把章节重写为 问题→方法→证据→结论→局限 的可讲页序，并抽页级证据（编号/页码/图注/数值单位**逐字**） | 每张拟上页的图/表都有定位 |
| **3** | 写 `/app/work/deck-spec.json`（schema 见 `slide-blueprint.md` §3），然后跑 **闸门 Q1**：`python "$SKILL_DIR/scripts/spec_lint.py" --spec /app/work/deck-spec.json` | `{"valid": true}`；有偏差按 H05 处置 |
| **4** | **闸门 Q2**（构建）：`python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md --spec /app/work/deck-spec.json --out /app/output` | 进程结束且 `./out/academic_deck.pptx` 存在（或按 H11 如实降级） |
| **5** | 预览与渲染记录：无 Office 引擎时 PIL 近似（文件名 + `previews[].kind` + `rendered_with` 三处标注）；检测到 `soffice` 则产真 PDF 并改写（H13） | 预览文件真实落盘 |
| **6** | 写 result.json 并跑 **闸门 Q3**：`python "$SKILL_DIR/scripts/export_check.py" --result /app/output/result.json --out-dir /app/output --case /input/case.json`，再跑 `check_contract.py` 核对 19 个顶层字段 | 两道门 exit 0；随后按 `RUBRIC_MAP.md` 自评 |

模板适配的三条铁律（Step 4 内）：**只填占位符、不碰 master、不覆盖页脚/配色**；
布局按名匹配 → 索引回退 → 内置版式；`template_mode="replace"` 时移除起始页并记
`starter_slides_removed`。页数超限按 H08 合并非证据页，**绝不静默丢弃证据页**。

预算纪律：64 次模型请求 / 900 秒 / 单响应 16384 tokens（含推理）。先把 Step 1–3
落盘成中间件再增量交付；脚本本身秒级，不占模型预算大头。

### 5. 处置规则 H01–H14

每条四段：**触发**（怎么认出）→ **首选**（先做什么）→ **降级**（首选不成立时）→
**记录**（写进哪个字段）。退出码语义统一见 `references/failure-modes.md` §1。

| # | 触发 | 首选 | 降级 | 记录 |
|-|-|-|-|-|
| H01 | `case.json` 缺失/不可解析 | 以 `status=failed` 收尾，不发明产物 | 完全不可读时不创建输出目录 | `case_unreadable`；`main.py` → 3 |
| H02 | 材料路径不存在 | 只产出元信息 result，不构建 deck | 状态降 `failed`，语义字段给类型空值 | `material_status=unreadable`、`sources[].reason` |
| H03 | PDF 加密 | 试空口令一次 | 改用外部 `.txt`（`--materials`），工具如实记 | `uncertainty[]` + `sources[].tool`；assetkit → 2 |
| H04 | PDF 无文本层（扫描件） | 标注"图像型 PDF"，仍引用可抽取的图 | **不做 OCR 冒充** | `uncertainty[]` + `sources[].tool` |
| H05 | Q1 lint 报偏差 | 按报错逐条修 spec 再跑 | 案例硬约束确实无法满足 → 继续构建但状态降 `partial`，偏差双写 | `spec_lint.problems` + `uncertainty[]` + `change_records[]` |
| H06 | 未提供模板 | 用内置 16:9 学术版式（正常分支） | 需要真模板时 `make_template.py` 现产 | `deck.template.kind="builtin"` + `uncertainty[]` |
| H07 | 模板不存在/损坏/占位符不足 | 回退内置版式并继续 | 名匹配 → 索引回退 → 补画文本框（登记命名） | `deck.template.kind/guard/error` + `layouts_used` |
| H08 | 页数超 `slide_count` | 合并非证据页（封面/过渡/收尾优先） | **绝不静默丢弃证据页**；仍超限如实标记 | `page_budget_met=false` + `change_records[]` |
| H09 | 图/表抽不出 | 保留显式占位框（注明"需补齐，非原图"） | 引用与定位照留，不伪造图片 | `figure.placed=null` + `placeholder=true` |
| H10 | 重建图失败 | 跳过图，保留表引用与原文数字 | **不估算补齐数字** | `charts[].chart.reason` + `run_meta.matplotlib_available` |
| H11 | 缺 `python-pptx` | `deck=null`、状态降级、如实说明 | **不生成假文件**；result.json 仍契约完整 | `deck_error` + `uncertainty[]` + `status` |
| H12 | 字体/Pillow 缺失 | 降级 PIL 默认字体继续；deck 内 latin+ea 双写 | Pillow 完全缺失 → `previews=[]` 并说明 | `run_meta.preview_font`（可 null）+ `rendered_with` |
| H13 | 有/无渲染引擎 | 有 `soffice` → 真 PDF；无 → PIL 近似 | 近似必须三处标注，不得称为真实渲染 | `run_meta.rendered_with` + `previews[].kind` |
| H14 | 输入不在 `/input`／契约出现未知字段 | 探测 `CASE_PATH`/`OUTPUT_DIR`/cwd；四形态回显，未知字段 `setdefault` | 都不可读 → H01；**任何声明字段禁止 null** | `run_meta.case_file` + `result.output_contract` |

> 兜底：**任何一条降级发生后**，`uncertainty[]`（发生了什么 + 影响）与
> `change_records[]`（何时 + 为什么）必须**同时**有对应条目；否则
> `run_meta.self_check.ok=false`，`main.py` 退出码 1。

### 6. 增益可验证化：断言 GA1–GA5 与测量方式

**口径先讲清楚**：题面的权威对照是平台用"基础 Agent vs 加载本 Skill 的 Agent"跑出的
白板结果，参赛者不提供隐藏测试。本节给的是**可以在本机复跑的结构性对照**——
它把"基础 Agent 会怎么做"实现成一条朴素单遍流水线（`gain_probe.py` 的 `baseline` 臂），
因此差异是**可逐格复核的事实**，而不是分数预测。完整协议与边界见
`references/GAIN-PROTOCOL.md`。

| 断言 | 指标（同 `_review` 测量） | 判据 | 复核命令 |
|-|-|-|-|
| **GA1 页级主张** | `claim_coverage`（带非空 claim 的页占比）、`placeholder_claims` | 加载后 `substantive_claim_coverage = 1.0` 且 `placeholder_claims = 0`；基线为 `0.0` | `python "$SKILL_DIR/scripts/gain_probe.py" --out <scratch> --arms baseline,skill,ablation --repeat 2` |
| **GA2 证据可追溯** | `evidence_rows`（md 表行数）、`evidence_locations`（json 中带定位且 `status≠gap` 的行数） | 加载后两数与声明 `entries` 一致且 > 0；基线为 `0` | 同上；报告见 `<scratch>/gain-report.json` |
| **GA3 契约完整性** | `contract_fields_present`（/19） | 加载后 `19/19` 且无 null；基线仅 7 | 同上 + `check_contract.py` |
| **GA4 备注分离与溢出保护** | `notes_pages`、`over_limit_frames` | 加载后备注页数 = 总页数且超限框 = 0；基线备注 0 页且存在超限框 | 同上 |
| **GA5 交付返工点** | `rework_points`（同一套一致性检查的失败计数） | 加载后 `0`；基线 6；去掉页级方案的消融臂 ≥ 1 | 同上 |

**三臂的定位**（`--arms baseline,skill,ablation`）：

- `baseline` = 朴素单遍流水线（段落切块贴页、无证据映射、无 lint、无模板适配、
  不分离备注、不按契约产出）——"不加载本 Skill"的可执行代理；
- `skill` = 本包 `main.py` 全链路，输入与基线完全相同（同 case、同材料、同页数上限）；
- `ablation` = `main.py --demo`：脚本与契约机制都在，**只去掉 Agent 写的页级方案**
  与 Q1 前置门，用来隔离"方案先行"这一项机制的贡献。

`gain_probe.py` 只写 `--out` 指定目录，且给所有子进程设 `PYTHONDONTWRITEBYTECODE=1`，
**因此可以在包内原地运行而不产生 `__pycache__`**。其余脚本请在包外副本上运行
（Python 会在 `scripts/` 下写字节码缓存，而技能资源只允许文本文件）。

### 7. 交付自查（逐条）

- [ ] 已读真实 case.json / task.md / 材料；`sources[]` 有真实工具与页数/字数；
- [ ] 每页有 `claim`；bullets 短语 ≤6 条；`evidence` 或 `evidence_gap` 二选一；
- [ ] **Q1** 通过或偏差按 H05 双写；
- [ ] 页上数字/单位/方法名/图号与原文逐字一致（抽查 ≥3 处）；
- [ ] 页序可讲，无"段落切片页"；
- [ ] 备注与页面文字分离，含封面/收尾页，`notes_separated=true`；
- [ ] 模板：占位符填充、master 未动、页脚未覆盖；否则 `template.guard` 注明回退；
- [ ] `/app/output` 有 `result.json`（19 字段 + `case_id`）、`.pptx`、预览、
      `evidence_mapping.md` + `evidence_map.json`；
- [ ] **Q3** `export_check.py` exit 0（G1–G8 无 error）；`check_contract.py` exit 0；
- [ ] 降级双写（`uncertainty` + `change_records`）齐全，无编造软件状态或科学数据；
- [ ] 如引用增益数据，**必须写明它是本机结构性对照（GA1–GA5）而非平台白板分数**。

### 8. 限制与口径边界

- 预览是 **PIL 近似渲染**，不等于 PowerPoint/LibreOffice 结果；
- PDF 图片抽取依赖库与版式，个别图只以显式占位框呈现（**不代表**论文原图）；
- 模板适配为"占位符级"，SmartArt 不重排；模板自带形状不改名；
- 结论正确性上限 = 论文原文；本 Skill 不验证论文结论；
- **对照口径**：`gain_probe.py` 的 `baseline` 是"基础 Agent 行为"的可执行代理，
  不是对某个具体 LLM 的测量；它测的是**结构差异**（有无页级主张/证据映射/契约/备注分离/
  溢出保护），不预测平台分数。`wall_seconds` 依赖机器与案例规模，只作效率参考。
- 包内只携带文本资源（`.md/.py/.json/.txt/.csv/.yaml/.yml`）；模板、预览、重建图一律
  运行时生成，首次运行前需 `python-pptx`（缺失按 H11 降级）。

### 9. 维护

- 版本号：`scripts/main.py` 的 `VERSION`（当前 `2.1.0`）；
- 分层约定：素材进 `assetkit.py`，生成进 `deckgen.py`，OOXML 细节进 `ooxml_kit.py`
  （新对象类型先在 `ooxml_kit.PREFIX_BY_KIND` 注册命名前缀）；
- **改任一条 H 规则** → 同步改 `references/failure-modes.md` 同号条目与
  `references/RUBRIC_MAP.md` 复核命令；
- **改任一 GA 指标或判据** → 同步改 `references/GAIN-PROTOCOL.md` §3 的指标定义，
  并在 `TEST.md` 追加一次新跑出的对照数字（不许沿用旧数字）；
- 修改记录同时进 result.json 的 `change_records` 与 git 提交历史。

---

# 【机制层】机制说明与可复用资产（目标维度:创新增益 15 + 生态贡献 10）

---
name: paper-to-academic-ppt
description: 把论文/研究材料转换成主线清晰、证据可追溯、可编辑的学术汇报 PPT。本版把包拆成三层：机制层（9 项独特机制，每项都写明"没有它会怎样"，见 references/MECHANISM.md）、执行层（阶段 1–7 + 关口 K1–K3 + 机制触发规则 M01–M14）、证据层（增益对照 GA1–GA5 与 scripts/gain_probe.py 三臂实测）。产物含可编辑 .pptx、双形态逐页证据映射、近似预览与契约完整的 result.json；另附可复用资产清单与五步移植流程（references/REUSE-KIT.md）。Use when a task asks to turn a paper or research material into an academic slide deck (论文转PPT、学术汇报PPT、slides from paper、presentation from paper), especially when /input/case.json and task.md are present and /app/output must contain the editable deck plus previews.
---

## 论文转学术 PPT（机制与复用显性版 · paper-to-academic-ppt）

同一件事可以用三种方式讲清楚："我按步骤做了"、"我比别人强"、"我为什么这样做、拿掉会怎样"。
前两种容易流于自述，第三种可以被别人验证。本版本按第三种的深度组织：

| 层 | 文件 | 回答的问题 |
|-|-|-|
| **机制层** | `references/MECHANISM.md` | 这套做法里**哪些是机制**（不是功能堆叠）、**没有它会怎样** |
| **执行层** | 本文件 §4–§5 | 具体怎么做（阶段 1–7、关口 K1–K3）、异常怎么处置（M01–M14） |
| **证据层** | `references/GAIN-PROTOCOL.md` + `scripts/gain_probe.py` | 怎么证明它更强（GA1–GA5，三臂本机对照，可复跑） |
| **复用层** | `references/REUSE-KIT.md` | 别人怎么把它搬到自己的题上（可复用资产 + 五步流程） |

**不负责**：论文精读结论的生成、科研绘图本身的图形设计、学术写作润色。
**不使用预制答案**：正式运行只依据案例实际提供的文件；`examples/` 只演示接口。

---

### 1. 适用与触发

- `/input/case.json` + `/input/task.md` 存在，要求在 `/app/output` 产出演示产物；
- 或用户直接要求"把这篇论文做成学术 PPT / slides from this paper / 组会汇报"。

**适用**：单篇论文或研究报告 → 8–20 页学术汇报（页级主张 + 图表定位 + 讲解备注 +
模板适配 + 渲染记录）。**不适用**：判断论文结论真假、重画科研图、润色正文、
与材料无关的通用幻灯片 —— 越界请求写进 `uncertainty` 并拒绝。

### 2. 输入输出与自定位

| 方向 | 路径（以环境实际挂载为准） | 内容 |
|-|-|-|
| 输入 | `/input/case.json` | `case_id`、`output_contract`、材料/模板定位、受众与页数约束 |
| 输入 | `/input/task.md` | 任务说明（存在时读取；缺失不阻断） |
| 工作 | `/app/work` | 抽取文本与图片、页级方案 `deck-spec.json` |
| 输出 | `/app/output` | `result.json`、`academic_deck.pptx`、`preview-approx-*.png`、`evidence_mapping.md`、`evidence_map.json`、`chart-*.png/.svg` |

**自定位（机制 M9）**：`$SKILL_DIR` = `SKILL.md` 所在目录；脚本以
`os.path.dirname(os.path.abspath(__file__))` 自解析并 `sys.path.insert` 本目录。
命令一律写成 `"$SKILL_DIR/scripts/xxx.py"`，**cwd 不是技能根也能跑**：

```bash
SKILL_DIR="<SKILL.md 所在目录>"      # 平台安装到 /skills/weekly-skill 时即该路径
python "$SKILL_DIR/scripts/spec_lint.py" --spec /app/work/deck-spec.json
```

输入不在 `/input` 时，探测 `CASE_PATH` / `OUTPUT_DIR` / cwd 下的 `case.json`，
以实际可读文件为准（M14）。

### 3. 资源清单（相对 `$SKILL_DIR`）

| 文件 | 层 | 作用 | 独立 CLI |
|-|-|-|-|
| `scripts/main.py` | 执行 | 端到端编排（K1 → 抽取 → 构建 → 预览 → K3 → result.json） | `--case --out` 必填 |
| `scripts/spec_lint.py` | 执行 | **关口 K1**：deck-spec 结构校验（BL-1…BL-4） | `--spec` |
| `scripts/export_check.py` | 执行 | **关口 K3**：契约 + 容器 + 命名 + 证据表一致性（G1–G8） | `--result --out-dir [--case]` |
| `scripts/check_contract.py` | 执行 | 契约字段覆盖核对（**直接读** `OUTPUT_CONTRACT.md`，机制 M1） | `--result --contract [--case]` |
| `scripts/assetkit.py` | 执行 | 素材层：材料定位、PDF 文本/图片抽取、表格数字重建图 | `--pdf --out` |
| `scripts/deckgen.py` | 执行 | 生成层：模板适配、页级排版、备注、证据映射页、形状命名 | 打印记录 |
| `scripts/ooxml_kit.py` | 执行 | OOXML 层：主题字体注入（机制 M5）、命名（M6）、容器检查 | 传 `.pptx` |
| `scripts/preview.py` | 执行 | PIL 近似预览（无 Office 引擎时的诚实渲染） | 打印记录 |
| `scripts/make_template.py` | 执行 | 运行期生成回退模板（机制 M7） | `--out [--name] [--no-starter]` |
| `scripts/make_synthetic_inputs.py` | 执行 | 运行期生成合成夹具（机制 M7） | `--out` |
| `scripts/cli_io.py` | 执行 | 控制台加固（机制 M8） | 被各入口导入 |
| `scripts/gain_probe.py` | 证据 | 三臂公平对照执行件（GA1–GA5；只写 `--out`） | `--out` 必填 |
| `references/MECHANISM.md` | 机制 | 9 项机制 + "没有它会怎样" | — |
| `references/REUSE-KIT.md` | 复用 | 可复用资产清单 + 五步移植流程 + 检查清单 | — |
| `references/GAIN-PROTOCOL.md` | 证据 | 对照协议 + 指标定义 + 真实对照记录 | — |
| `references/OUTPUT_CONTRACT.md` | 契约 | result.json 顶层字段 + 四形态 + G1–G8（**必读**） | — |
| `references/failure-modes.md` | 执行 | 五类异常处置（与 M01–M14 同号）+ 对增益断言的影响 | — |
| `references/slide-blueprint.md` | 执行 | 论文→页面蓝图映射 + deck-spec schema + 证据表格式 | — |
| `references/RUBRIC_MAP.md` | 证据 | 五维落点（以创新增益/生态贡献为主轴）+ 复核命令 | — |
| `references/layer-naming.md` | 执行 | 分层命名规范（机制 M6） | — |
| `examples/` | 复用 | 最小示例（合成案例，明确标注"示例，非正式案例"） | — |

依赖：`python-pptx` 必需；`Pillow` 预览；`matplotlib` 可选（重建图）；
`PyMuPDF`/`pypdf`/`pdfplumber` 任一即可读 PDF。逐级回退见 §5 与 `failure-modes.md`。

### 4. 执行阶段 1–7（关口 K1–K3）

| 阶段 | 动作 | 关口 / 出口条件 |
|-|-|-|
| **1 定位** | 读 `task.md` 与 `/input/case.json`：取 `case_id`、`output_contract`、材料/模板、受众与页数约束；解析 `$SKILL_DIR` | 能说出"必须回显哪些字段" |
| **2 读实际文件** | `python "$SKILL_DIR/scripts/assetkit.py" --pdf "<材料路径>" --out /app/work/extract`；PDF 走三级回退（M03/M04） | `sources[]` 有真实工具与页数/字数 |
| **3 蓝图** | 按 `slide-blueprint.md` §1 把章节重写为可讲页序；抽页级证据（编号/页码/图注/数值单位**逐字**） | 每张拟上页的图/表都有定位 |
| **4 写方案 + K1** | 写 `/app/work/deck-spec.json`（schema 见 `slide-blueprint.md` §3），跑 **K1**：`python "$SKILL_DIR/scripts/spec_lint.py" --spec /app/work/deck-spec.json` | `{"valid": true}`；有偏差按 M05 处置 |
| **5 构建** | `python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md --spec /app/work/deck-spec.json --out /app/output` | `.pptx` 存在（或按 M11 如实降级） |
| **6 渲染记录** | 无 Office 引擎 → PIL 近似（文件名 + `previews[].kind` + `rendered_with` 三处标注）；检测到 `soffice` → 真 PDF 并改写（M13） | 预览文件真实落盘 |
| **7 写结果 + K3** | 写 result.json，跑 **K3**：`export_check.py`（G1–G8）+ `check_contract.py`（19 字段） | 两道门 exit 0；再按 `RUBRIC_MAP.md` 自评 |

模板适配三铁律（阶段 5 内）：**只填占位符、不碰 master、不覆盖页脚/配色**；
布局按名匹配 → 索引回退 → 内置版式；`template_mode="replace"` 时移除起始页并记
`starter_slides_removed`。页数超限按 M08 合并非证据页，**绝不静默丢弃证据页**。

预算纪律：64 次模型请求 / 900 秒 / 单响应 16384 tokens（含推理）。先把阶段 2–4
落盘成中间件再增量交付；脚本本身秒级，不占模型预算大头。

### 5. 机制触发规则 M01–M14

每条四段：**触发** → **首选举措** → **降级路径** → **记录字段**。
与 `references/failure-modes.md` §2 同号（该处多一列"对增益断言的影响"）。

| # | 触发 | 首选 | 降级路径 | 记录 |
|-|-|-|-|-|
| M01 | `case.json` 缺失/不可解析 | `status=failed` 收尾，不发明产物 | 完全不可读时不建输出目录 | `case_unreadable`；`main.py` → 3 |
| M02 | 材料路径不存在 | 只产元信息 result，不构建 deck | 状态降 `failed`，语义字段给类型空值 | `material_status=unreadable` + `sources[].reason` |
| M03 | PDF 加密 | 试空口令一次 | 外部 `.txt`（`--materials`），工具如实记 | `uncertainty[]` + `sources[].tool` |
| M04 | PDF 无文本层（扫描件） | 标注"图像型 PDF"，仍引用可抽取的图 | **不做 OCR 冒充** | `uncertainty[]` + `sources[].tool` |
| M05 | K1 lint 报偏差 | 按报错逐条修 spec 再跑 K1 | 硬约束确实无法满足 → 继续构建，状态降 `partial`，偏差双写 | `spec_lint.problems` + `uncertainty[]` + `change_records[]` |
| M06 | 未提供模板 | 内置 16:9 学术版式（正常分支，M7 无二进制包袱） | 需要真模板时 `make_template.py` 现产 | `deck.template.kind="builtin"` + `uncertainty[]` |
| M07 | 模板不存在/损坏/占位符不足 | 回退内置版式并继续 | 名匹配 → 索引回退 → 补画文本框（登记命名，M6） | `deck.template.kind/guard/error` + `layouts_used` |
| M08 | 页数超 `slide_count` | 合并非证据页（封面/过渡/收尾优先） | **绝不静默丢弃证据页** | `page_budget_met=false` + `change_records[]` |
| M09 | 图/表抽不出 | 保留**显式占位框**（M4 的诚实语义） | 引用与定位照留，不伪造图片 | `figure.placed=null` + `placeholder=true` |
| M10 | 重建图失败 | 跳过图，保留表引用与原文数字 | 不估算补齐 | `charts[].chart.reason` + `run_meta.matplotlib_available` |
| M11 | 缺 `python-pptx` | `deck=null`、状态降级、如实说明 | **不生成假文件** | `deck_error` + `uncertainty[]` + `status` |
| M12 | 字体/Pillow 缺失 | 降级 PIL 默认字体继续；deck 内 latin+ea 双写（M5） | Pillow 全缺 → `previews=[]` 并说明 | `run_meta.preview_font`（可 null）+ `rendered_with` |
| M13 | 有/无渲染引擎 | 有 `soffice` → 真 PDF；无 → PIL 近似 | 近似三处标注，不得称为真实渲染 | `run_meta.rendered_with` + `previews[].kind` |
| M14 | 输入不在 `/input`／契约出现未知字段 | 探测 `CASE_PATH`/`OUTPUT_DIR`/cwd；四形态回显，未知字段 `setdefault` | 都不可读 → M01；**声明字段禁止 null** | `run_meta.case_file` + `result.output_contract` |

> 兜底：**任何降级发生后**，`uncertainty[]`（发生了什么 + 影响）与 `change_records[]`
> （何时 + 为什么）必须**同时**有条目；否则 `self_check.ok=false`，`main.py` → 1。

### 6. 机制 → 证据 → 复核命令

| 机制 | 关键证据 | 复核命令（可当场跑） |
|-|-|-|
| M1 契约同源 | `check_contract` 读到 19/19、`missing=[]` | `python "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json --contract "$SKILL_DIR/references/OUTPUT_CONTRACT.md"` |
| M2 方案先行 + K1 | 消融臂 `substantive_claim_coverage` 1.0 → 0.0、`evidence_rows` 6 → 1 | `python "$SKILL_DIR/scripts/gain_probe.py" --out <scratch> --arms baseline,skill,ablation --repeat 2` |
| M3 双形态证据映射 | `evidence_rows = 6`、`evidence_locations = 6`，且等于声明 `entries` | 同上 + `export_check.py` 的 G7 |
| M4 占位诚实语义 | `.pptx` 内可按 `figure-*-placeholder` 前缀检索到占位框 | `python "$SKILL_DIR/scripts/ooxml_kit.py" <out>/academic_deck.pptx` |
| M5 主题字体注入 | `theme1.xml` 含 `Microsoft YaHei` 与 `Calibri`；`deck.theme_fonts.applied=true` | `python "$SKILL_DIR/scripts/ooxml_kit.py" <out>/academic_deck.pptx` |
| M6 对象分层命名 | `named_shapes` 基线 0 vs 全链路 3（模板在场）/ 17（内置版式） | `gain_probe.py` 报告的 `named_shapes` |
| M7 仅文本资源 | 包内只有 7 种扩展名、无二进制 | `python <repo>/validate_pkg.py <pkg>`（合规验收器） |
| M8 关口/退出码/字节码卫生 | 非 UTF-8 控制台仍 exit 1 且 stdout 可 UTF-8 解码；原地跑 `gain_probe` 后 `__pycache__` 计数 0 | `TEST.md` 的控制台加固项与字节码卫生项 |
| M9 自定位 | cwd 在别处与 cwd 在技能根**都 exit 0** | `TEST.md` 的两种调用风格项 |

`MECHANISM.md` §2 对每项机制给出"常规做法 / 本包做法 / **没有它会怎样** / 边界"四段，
其中"没有它会怎样"要么是本机实测数字，要么是本族代码或本平台上有据可查的真实故障。

### 7. 复用（详见 `references/REUSE-KIT.md`）

五步：**R1 搬骨架**（`scripts/` + 契约 + 命名规范）→ **R2 换题面与输入契约**
（改 `OUTPUT_CONTRACT.md` §1 字段清单即可，`check_contract.py` 读的就是它）→
**R3 换蓝图映射**（`slide-blueprint.md` §1/§3）→ **R4 换配色与命名前缀**
（`ACADEMIC_THEME`、`PREFIX_BY_KIND`）→ **R5 跑五条校验命令并写回新数字**。
移植检查清单与"已知不可直接复用的部分"见该文件 §3/§4。

### 8. 交付自查（逐条）

- [ ] 已读真实 case.json / task.md / 材料；`sources[]` 有真实工具与页数/字数；
- [ ] 每页有 `claim`；bullets 短语 ≤6 条；`evidence` 或 `evidence_gap` 二选一；
- [ ] **K1** 通过或偏差按 M05 双写；
- [ ] 页上数字/单位/方法名/图号与原文逐字一致（抽查 ≥3 处）；页序可讲，无"段落切片页"；
- [ ] 备注与页面文字分离，含封面/收尾页，`notes_separated=true`；
- [ ] 模板：占位符填充、master 未动、页脚未覆盖；否则 `template.guard` 注明回退；
- [ ] `/app/output` 有 `result.json`（19 字段 + `case_id`）、`.pptx`、预览、双形态证据映射；
- [ ] **K3** `export_check.py` 与 `check_contract.py` 均 exit 0（G1–G8 无 error、无 null）；
- [ ] 降级双写齐全；无编造软件状态或科学数据；
- [ ] 引用增益数字时写明它是**本机结构性对照**（GA1–GA5），不是平台白板分数。

### 9. 限制与口径边界

- 预览是 **PIL 近似渲染**，不等于 PowerPoint/LibreOffice 结果；本机无 LibreOffice；
- PDF 图片抽取依赖库与版式，个别图只以显式占位框呈现（**不代表**论文原图）；
- 模板适配为"占位符级"，SmartArt 不重排；模板自带形状不改名；
- 结论正确性上限 = 论文原文；本 Skill 不验证论文结论；
- **对照口径**：`gain_probe.py` 的 `baseline` 是"基础 Agent 行为"的可执行代理，
  不是对某个具体 LLM 的测量；`wall_seconds` 只反映脚本开销，不等于端到端总耗时更短；
  平台白板对照仍是权威口径。单一示例案例的结论不可外推到所有论文类型。
- 包内只携带文本资源（`.md/.py/.json/.txt/.csv/.yaml/.yml`）；模板、预览、重建图一律
  运行时生成（机制 M7），首次运行前需 `python-pptx`（缺失按 M11 降级）。

### 10. 维护

- 版本号：`scripts/main.py` 的 `VERSION`（当前 `2.1.0`）；
- 分层约定：素材进 `assetkit.py`，生成进 `deckgen.py`，OOXML 细节进 `ooxml_kit.py`
  （新对象类型先在 `ooxml_kit.PREFIX_BY_KIND` 注册前缀，再同步 `layer-naming.md`）；
- **三处同步铁律**：改 M 规则 → 同步 `failure-modes.md` 同号条目与 `RUBRIC_MAP.md`；
  改机制 → 同步 `MECHANISM.md`（必须仍能回答"没有它会怎样"）；
  改 GA 指标 → 同步 `GAIN-PROTOCOL.md` §3 并在 `TEST.md` 追加**新跑出的**数字；
- 新增可复用资产 → 追加到 `REUSE-KIT.md` §1，写清"位置 / 形态 / 怎么用"；
- 修改记录同时进 result.json 的 `change_records` 与 git 提交历史。
