---
name: academic-ppt-builder-decision-explicit
description: 把论文/研究材料组织成结构清楚、证据可追溯、可编辑、符合模板约束的学术汇报演示稿（PPTX），并把"每一步该做什么、不满足什么条件时改走哪条路"写成可查的决策规则 D1–D14 与失败分支表。加载后按"读实际文件→抽主线与页级证据→页面蓝图与角色分配→构建前结构裁决→模板槽位建稿+图表绑定→预览渲染+渲染 QA→导出契约校验（G1–G8）→带全部 output_contract 字段的 result.json"执行；支持 --edit 局部编辑与版本回退；页面数字逐一核验材料、缺失显式标注、绝不编造。Use when a task asks to generate or edit an academic presentation / slide deck from a paper or research material（组会汇报、开题与中期、答辩、项目评审、基金申请；学术PPT、slides from paper、presentation from paper），especially when /input/case.json and task.md are present and /app/output must contain the editable deck plus previews and evidence mapping.
---

# 学术 PPT 生成与编辑 Skill（决策显性化版 · ppt-6ad93034）

> **本版定位**：同一套算法与 CLI 之上，把"该怎么做"从散文式流程升级为
> **可逐条检索、可逐条考核的决策规则**：每条规则固定写成
> **触发条件 → 动作 → 失败时的降级去向**，并给出记录字段；异常路径由
> §6 失败分支表按"材料异常 / 模板缺失 / 依赖缺失 / 契约四形态 / 状态不一致"
> 五族展开，与 `references/failure-modes.md` 的编号一一对应。
> 目标：让回放 Agent 在材料缺页、模板打不开、库缺失、契约字段缺省、状态自相矛盾
> 这五类现实噪声下**不靠临场猜测**，也不会把"降级"包装成"成功"。

**管辖范围**：把材料"翻译"成页级表达，并保证每页数字与图表可核实。
超出范围的四件事本 Skill 不做：论文精读与文献综述、可视化算法研发、
学术写作文字润色、PPT 软件自身的研发。

---

## 1. 调用前的三项声明

| 声明项 | 内容 |
|-|-|
| 触发场景 | 输入侧出现 `/input/case.json` + `task.md`，且要求产出"可编辑演示稿 + 页级证据" |
| 不触发场景 | 只要文字润色、只要论文精读、只要可视化算法、只要 PPT 软件功能开发 |
| 单次运行边界 | 3 ≤ 页数 ≤ 20；每页一个叙事角色；单次运行脚本耗时 < 60 秒 |

命令口径（全文统一）：`$SKILL_DIR` = **含 `SKILL.md` 的技能根目录**，
平台评测容器把它安装在 `/skills/weekly-skill`。

```bash
SKILL_DIR="${SKILL_DIR:-/skills/weekly-skill}"   # 换成你的实际安装路径
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output
```

因此 **cwd 不是技能根目录时照样可跑**（脚本内部同时用 `os.path.dirname(__file__)`
自定位）。`--case` / `--out` 才是输入输出路径，允许绝对路径或相对 cwd 的路径。

---

## 2. 输入契约与产物归属

**读什么**：`case.json`（`case_id`、`title`、`inputs{task_md, material[]}`、
`spec{audience, duration_minutes, max_slides, template|template_pptx|starting_deck, style}`、
可选 `output_contract`）、`task.md`、以及 `material[]` 指向的**实际文件**。
`scripts/deck_extract.py` 强制"读实际文件"——**禁止凭文件名推断内容**。

**写什么**（一律写 `--out` 目录，并另有输出根 `preview/` 副本便于直接取件）：

| 产物 | 位置 | 性质 |
|-|-|-|
| 可编辑演示文件 | `work/deck.pptx` | 每页主张式标题 + 要点 + 图表槽 + 证据脚注 + 演讲备注 |
| 页面模型 | `work/plan.json` | 页序/角色/主张/证据/图表，**可编辑源** |
| 材料视图 | `work/material_view.json` | 章节、数据表、图表提及、结构化定位 |
| 预览渲染 | `work/preview/slide_*.png`、`work/preview/preview.pdf`、`preview/*` | 标注"非 PowerPoint 导出" |
| 评分产物 | `result.json` | 契约全字段 + `case_id`，**禁 null** |
| 证据映射 | `evidence_map.md` + `evidence_map.json` | 人读/机器读**同源双形态** |
| 记录 | `changelog.jsonl`、`manifest.json`（全部产物 sha256）、`logs/` | 支撑他人独立复核 |

> **不入包的产物**：`deck.pptx`、预览 `*.png`、预览 `*.pdf`、`changelog.jsonl`
> 都是**运行时产物**，由上面那条命令现场生成并登记进 `manifest.json`；
> 技能包只携带 UTF-8 文本资源。一次成功运行的完整清单见
> `examples/EXPECTED-OUTPUT.md`。**产物绝不写回技能包目录。**

---

## 3. 环境与包体自我约束

- Python 3.8+；`python-pptx>=0.6.21`（建稿必需）、`matplotlib>=3.5`、`Pillow>=9`、
  `numpy`；`reportlab` 可选（缺席跳过 PDF 预览并如实说明，规则 D8）；
  PDF 材料抽取任选 fitz/pypdf/PyPDF2/pdfplumber 之一，全缺时走 D3。
- 包体约束（自我声明、运行期同样适用）：**≤50 个文件、单文件 ≤500KB、
  合计 ≤2MB、无符号链接、全部为 UTF-8 文本**（`.md/.py/.json/.txt/.csv/.yaml/.yml`）。
  新增能力请并入既有文档/脚本，**不要往包里塞 PPTX/PNG/PDF/JSONL**；
  技能目录在评测容器里是只读安装件。

---

## 4. 五阶段主干流程（阶段间有裁决点）

> 与"一路往前跑"的写法不同：**每个阶段结束都有一个裁决点**（V1–V5），
> 裁决不通过时按 §5 的对应 D 规则转向，而不是继续硬走。

| 阶段 | 做什么 | 产出 | 裁决点 |
|-|-|-|-|
| P1 抽取 | 读 case/task/全部材料；切章节、抓数据表、抓图/表提及、定位问题/方法/结果/局限 | `work/material_view.json` | **V1**：材料是否至少有一份可读？ |
| P2 规划 | 按 `spec.max_slides` 确定性分配页级角色，写页序/主张/证据指针 | `work/plan.json` | **V2**：`evidence_check.plan_lint` 是否 `valid`？ |
| P3 建稿 | 模板槽位建稿 + 四态图表绑定 + 每页备注与证据脚注 | `work/deck.pptx` | **V3**：deck 能否被 python-pptx 重开且页数=plan？ |
| P4 渲染 | PIL 逐页 PNG + reportlab 逐页 PDF + 渲染 QA | `work/preview/*`、`preview/*` | **V4**：至少 1 张 PNG 是否生成？ |
| P5 收口 | `result.json` + 双形态证据映射 + changelog + manifest | 输出根六个文件 | **V5**：`result_tool` 是否 `{"valid": true}`？ |

**V2 细节**：`plan_lint` 校验每页 role/title/要点上限/长度/证据规则。
`{"valid": false}` 时**先修 plan**；只有确认属于案例硬约束（如 `max_slides`
本身就小于必需页数）才允许"继续建稿 + 显式记录偏差 + 状态降 partial"（D4）。

**V5 细节**：契约门与自检**两条命令都要跑**，缺一条不算通过：

```bash
SKILL_DIR="${SKILL_DIR:-/skills/weekly-skill}"
python "$SKILL_DIR/scripts/result_tool.py" --result /app/output/result.json \
    --out-dir /app/output --case /input/case.json \
    --envelope "$SKILL_DIR/templates/result_envelope.json"
# 期望 {"valid": true} 且 exit 0（G1–G8，见 references/OUTPUT_CONTRACT.md §8）

python "$SKILL_DIR/scripts/selftest.py" --out /app/output --case /input/case.json
# 期望 all_pass=true
```

`--case` **必须传**：契约回显字段（`output_contract`）只有在拿到 `case.json`
时才能核对"逐项回显且非 null"。漏传会让"契约全回显"看起来失败 —— 这是
本 Skill 最容易被误判的一处（规则 D12 专门管它）。

---

## 5. 决策规则表 D1–D14（触发条件 → 动作 → 失败时的降级）

> 读法：先按"触发条件"定位规则号，再执行"动作"；动作本身失败时走"降级去向"列。
> 每条规则的记录字段是**硬要求**：没有记录就等于没执行降级。

| # | 触发条件（可观测） | 动作（正常路径） | 失败时的降级去向 | 记录字段 |
|-|-|-|-|-|
| **D1** | `material_status ∈ {missing}`：case 指向的文件一个都读不到 | 不构建 deck，只产出元信息 result（`deck.slide_count=0`） | 若连 case.json 都读不到 → 只写最小 `status=failed` result 后 exit 2 | `status`、`evidence.material_warnings` |
| **D2** | `check_claim_numbers` 对某条入页主张返回 `missing` 非空 | 该主张 `verified=false` 入 `unverified_claims`；**不回填、不取整、不按印象改** | 若整页主张都不可核 → 该页降为"待核验页"，在备注里明说，不改写材料原文 | `evidence.unverified_claims` |
| **D3** | PDF 材料无文本层，或环境无任何抽取库 | 不 OCR 冒充：Agent 用自身读图/读文能力抽成 `<out>/work/materials/*.txt` 后重跑 | 重跑仍读不出 → `status=partial` 并说明"该材料未计入页级证据" | `uncertainty`、`sources[].tool` |
| **D4** | `plan_lint` 返回 `{"valid": false}` | 先修 plan（改角色/删超长要点/降页数）后重跑 lint | 确属案例硬约束无法满足 → 继续建稿但把 `problems` 原文记入 `spec_lint`，状态降 partial | `run_meta.spec_lint`、`uncertainty` |
| **D5** | 材料里的图是位图且没有任何数值数据表 | 只放**灰框诚实占位**（`figure.kind=placeholder`），标注"原图未提供取数数据" | 若连位图文件也没有 → `figure.kind=none`，页面上不出现该图编号之外的任何声称 | `deck.slides[].figure.note` |
| **D6** | `template_pptx` 打不开 / 母版损坏 | 备份原文件到 `work/original_inputs/`，改内置 `templates/default.json`，说明降级 | 内置模板也读不到 → 用代码内 `DEFAULT_SPEC` 常量建稿，仍记降级 | `uncertainty`、`change_records` |
| **D7** | `plan_lint` 报 `pages=N > max_slides` | 按 `max_slides` 确定性压缩角色分配（先合并讨论/背景，再合并结果页） | **不静默丢证据页**：被合并页的证据脚注并入保留页，并在备注写明合并 | `run_meta.spec_lint`、`change_records` |
| **D8** | 预览阶段字体回落默认字体 / reportlab 缺席 / 渲染抛错 | 字体问题照常出 PNG 并把 `cjk_font_available=false` 记入 warnings；无 reportlab 则 `previews.pdf=""` | 渲染整体失败 → 跳过预览、G5 记 error、状态 partial，**绝不用别的图冒充预览** | `previews.warnings`、`uncertainty` |
| **D9** | 图表重绘失败（无 matplotlib / 无非数值列 / `--no-chart`） | 降级为 PPTX **原生可编辑表格**，保留引用与表题 | 连表格文件也找不到 → `figure.kind=none` + 脚注保留引用，注明"仅引用未插图" | `figure.note`、`uncertainty` |
| **D10** | `output_contract` 声明的字段在运行值里缺失 | 按**四形态**给同型空值：`string→""`、`list→[]`、`dict→{}`、`bool→false`、`number→0`，**禁 null** | 声明了未知类型 → 按运行时值的类型给同型空值，并在 `uncertainty` 记"未声明类型" | `result.json` 顶层回显 |
| **D11** | `--edit` 的 op 未知、页码/下标越界、`reorder_pages` 不是 1..N 的置换 | 跳过该条 op，其余 op 照常应用；置换不合法时**整条拒绝**（避免静默丢页） | 编辑后重跑数字核验仍不过 → 该主张 `verified=false`，**不因"是用户让改的"放行** | `uncertainty`、`changelog.jsonl` skipped |
| **D12** | 复核者报告"契约字段没回显" | **先核对是否传了 `--case`**；再核 `output_contract` 是否真的声明了该字段 | 确认参数齐全且字段已声明仍不回显 → 报 bug 并附 `result.json` 顶层键清单，不靠手改 JSON 掩盖 | 复核记录（不写入 result） |
| **D13** | 同一输出目录重复运行 | 结构确定输出：同输入同 spec 无 `--edit` 时逐页结构一致 | 出现结构差异 → 说明差异是否来自机器路径前缀/时间戳；非此二者即视为缺陷并记录 | `change_records` |
| **D14** | 预算压力（模型请求/时长接近上限） | 先落盘部分产物（partial result）再增量改进；脚本 <60 秒，把预算留给材料阅读与讲稿微调 | 已无预算继续 → 交 partial 并**逐条列出未完成项**，不用"进行中"含糊措辞 | `status=partial`、`change_records` |

**规则之间的优先级**：D1/D2 属"事实正确性"层，优先级最高，任何时候不得为了
"页面好看"而放宽；D6–D9 属"能力降级"层，允许降级但必须留痕；D13/D14 属
"运行工程"层，只影响过程记录，不影响产物结构。

---

## 6. 失败分支表（按五族展开，与 `references/failure-modes.md` 编号一致）

### F1 材料异常族

| 分支 | 识别信号 | 处置 | 记录 | 规则 |
|-|-|-|-|-|
| F1.1 全部材料读不到 | `material_status=missing` | 只写元信息 result，**不编 deck** | `material_warnings` | D1 |
| F1.2 部分材料读不到 | `material_status=partial` | 用已读到的继续；缺的那份显式标出，页面上不得出现只有它才有的数字 | `material_warnings` | D1 |
| F1.3 只有空白/占位材料 | 章节数为 0 且无数据表 | 状态 partial，说明"材料无可用结构"，不硬凑页面 | `uncertainty` | D1/D2 |
| F1.4 数字对不上 | `check_claim_numbers` 有 missing | 主张降级为未核验，**原文照录** | `unverified_claims` | D2 |
| F1.5 数据表缺列/非数值 | 图表绑定判定 | 降级原生表格，仍可逐格改 | `figure.note` | D9 |

### F2 模板缺失族

| 分支 | 识别信号 | 处置 | 记录 | 规则 |
|-|-|-|-|-|
| F2.1 `template_pptx` 损坏 | `Presentation()` 抛错 | 备份 → 内置 JSON 模板 | `uncertainty`+`change_records` | D6 |
| F2.2 版式/占位符不足 | 母版版式枚举不足 | 复用最接近版式 + 新增文本框，**绝不改母版**；仍不够则减要点而不是缩字号 <12pt | `change_records` | D6/D7 |
| F2.3 `starting_deck` 需适配 | 起始稿存在 | 先备份到 `work/original_inputs/` 再重排，每处改动一条记录 | `change_records` | D6 |
| F2.4 页数超限 | `plan_lint` 报超限 | 确定性压缩角色，不静默丢证据页 | `spec_lint` | D7 |
| F2.5 `spec.style` 缺键 | 键缺失 | 用模板默认值；模板是数据不是代码 | `change_records` | D6 |

### F3 依赖缺失族

| 分支 | 缺失项 | 后果与处置 | 记录 | 规则 |
|-|-|-|-|-|
| F3.1 | `python-pptx` | **致命**：无法建稿 → 如实报 partial/failed，说清缺什么 | `uncertainty` | D6 |
| F3.2 | `matplotlib` | 结果页降级原生表格 | `figure.note` | D9 |
| F3.3 | `Pillow` | 预览 PNG 不产出 → G5 报错、自检 previews 不过 | `previews.warnings` | D8 |
| F3.4 | `reportlab` | 跳过 PDF 预览，PNG 不受影响（G5 仅 warning） | `previews.warnings` | D8 |
| F3.5 | CJK 字体 | 预览方块但 **PPTX 不受影响** | `previews.warnings` | D8 |
| F3.6 | 字体探测全失败 | 回落 PIL 默认字体并预警；**不下载、不内嵌字体文件** | `uncertainty` | D8 |

### F4 契约四形态族

| 分支 | 情形 | 处置 | 规则 |
|-|-|-|-|
| F4.1 | 字段声明为 `string` | 无真实值给 `""` | D10 |
| F4.2 | 字段声明为 `list` / `dict` | 给 `[]` / `{}` | D10 |
| F4.3 | 字段声明为 `bool` / `number` | 给 `false` / `0`（**注意 bool 不是 0**） | D10 |
| F4.4 | 字段类型未声明 | 按运行时值类型给同型空值并记 uncertainty | D10 |
| F4.5 | 复核说"没回显" | 先确认 `--case` 已传、字段确实已声明 | D12 |

实现位置：`scripts/result_tool.py::apply_output_contract`；
校验位置：G2（齐全 + 非 null）与 G8（`templates/result_envelope.json` 类型合规）。

### F5 状态不一致族

| 分支 | 不一致形态 | 处置 | 规则 |
|-|-|-|-|
| F5.1 | 有降级却标 `success` | 逐条把降级原因补进 `uncertainty` 后降为 `partial` | D4/D8/D14 |
| F5.2 | 有未核验主张却标 `success` | 同上降为 `partial` | D2 |
| F5.3 | 无 deck 却标 `success` | 必为缺陷：降 `failed` 并说明 | D1 |
| F5.4 | `partial` 但 `uncertainty` 为空 | 不自洽：补齐每条降级原因的对应条目 | D4/D14 |
| F5.5 | 预览被当作 Office 导出件 | 立即更正措辞：文件名与 `previews.method` 都以"预览渲染"为准 | D8 |

> **三层不许互相顶替**：`selftest` 查"产物在不在、能不能开、页数对不对"；
> `result_tool` 查"契约合不合规"；内容正确性由 `evidence_check` 的数字核验与
> `plan_lint` 的页面纪律负责。三者都过，也**不等于**内容正确。

---

## 7. 能力索引（入口 → 命令 → 定位命令）

| 入口 | 命令 | 什么时候用 |
|-|-|-|
| 端到端编排 | `python "$SKILL_DIR/scripts/main.py" --case C --out O` | 主路径；含 P1–P5 与 V1–V5 |
| 换模板 | `--template <spec.json>` | 组织方给定配色/字体/页脚时 |
| case 相对路径基准 | `--input-dir <dir>` | `--case` 写相对路径时 |
| 页数覆盖 | `--max-slides N`（3–20） | 页数上限与 spec 不一致、或做对照试验 |
| 局部编辑 + 版本 | `--edit <edits.json> --version v2` | 多轮改稿；不推翻整稿 |
| 强制图表降级 | `--no-chart` | 对照试验或环境无 matplotlib |
| 草稿模式 | `--draft` | 跳过 PDF 预览抢时间 |
| 详细日志 | `--verbose` | 排查失败时 |
| 契约门 | `python "$SKILL_DIR/scripts/result_tool.py" --result R --out-dir O --case C --envelope E` | V5 必跑；`0=通过/1=有未过项/2=不可读` |
| 产物自检 | `python "$SKILL_DIR/scripts/selftest.py" --out O --case C [--pptx P] [--slides N]` | V5 必跑；`0=全过/1=有未过项` |
| 单条数字核验 | `python "$SKILL_DIR/scripts/evidence_check.py" --claim "…" --material M` | 抽查某条主张；`0=全部找到/1=有缺失` |
| 示例重建 | `python "$SKILL_DIR/scripts/make_examples.py" [--dry-run]` | 维护：真跑示例并净化机器绝对路径 |

**退出码语义**（编排器可直接判读）：`main.py`：0=`success` / 1=`partial` /
2=输入不可读；`result_tool.py`：0 / 1 / 2；`selftest.py`：0 / 1；
`evidence_check.py`：0 / 1。**只有 exit 0 才算这次运行"干净"**；exit 1 必须读
`result.json.uncertainty` 再决定是否补件重跑；exit 2 表示输入侧问题，重跑无用。

---

## 8. 增量编辑（演示稿迭代）

```bash
SKILL_DIR="${SKILL_DIR:-/skills/weekly-skill}"
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output \
    --edit edits.json --version v2
```

支持 `update_bullet / add_bullet / remove_bullet / add_note / retitle /
reorder_pages / set_figure`（字段见 `examples/edit_demo.json`，
决策树见 `references/EDIT_OPS.md`）。每次修改在 `changelog.jsonl` 写一条
`{version, op, page, target, reason}`；`deck_v2.pptx` 与 `deck.pptx` **并存**，
改坏了回退 = 复制旧版本重跑（并补一条回退记录）。
**编辑链路同样过 D2 数字核验**：编辑引入的新数字材料里没有 → 该主张降级为未核验。

---

## 9. 自检清单（逐项勾选；括号内是对应的 D 规则）

- [ ] 已读 `case.json` + `task.md` + 全部实际材料文件，未凭文件名猜内容（P1/V1）
- [ ] 材料缺失/部分缺失已分别记入 `material_warnings`，未混淆为 `uncertainty`（D1）
- [ ] 页数 = `spec.max_slides`（或更少且原因已记录）；每页有 index/role/title（D4/D7）
- [ ] 每页主张 ≤7 条、单条 ≤90 字、标题 ≤60 字；无整段摘要塞页（D4）
- [ ] 页面上每个数字都能指回材料；`unverified_claims` 为空或有逐条解释（D2）
- [ ] 图表四态（`chart_image`/`table`/`embedded`/`placeholder`）均为真，无凭空曲线（D5/D9）
- [ ] 字号 ≥12pt；页脚/页码唯一来源；外部模板母版未被改动（D6）
- [ ] 每页有演讲备注与证据脚注（D5）
- [ ] deck 可被 python-pptx 重开且页数与 plan 一致（V3）
- [ ] 预览 PNG ≥1 且 `previews.method` 如实标注"预览"（D8）
- [ ] `result_tool.py` 输出 `{"valid": true}` 且 exit 0（G1–G8）（V5/D12）
- [ ] `selftest.py` `all_pass=true`（V5）
- [ ] 契约字段全部回显、无 `null`；**核对时已把 `--case` 传给 `result_tool.py`**（D10/D12）
- [ ] `changelog.jsonl` 有本次记录；`manifest.json` 含全部产物 sha256（D13）
- [ ] `status` 与每一列出的 `uncertainty` 一一对应，无"降级却标 success"（F5）
- [ ] 包体：只有 `.md/.py/.json/.txt/.csv/.yaml/.yml`，无二进制、无 `__pycache__`、≤50 文件（§3）

---

## 10. 五维评分落点（速查；逐点展开见 `references/RUBRIC_MAP.md`）

| 维度 | 分 | 本包靠什么拿到 |
|-|-|-|
| 实际效果 | 40 | P1–P5 真跑（`scripts/main.py`）；页序 + 页级角色；可编辑 PPTX + 每页备注 + 证据脚注；数字逐一核验（`evidence_check`）；`sources[].sha256` + `manifest.json` + 双形态证据映射 + G1–G8 门 |
| 使用增益 | 25 | 页面纪律（每页一个角色、≤7 条、≤90 字、字号 ≥12pt 不溢出）对标"整段塞页"；`--edit` 局部编辑 + 版本归档减少返工；`--no-chart` / `--max-slides` 让对照条件可复现 |
| 创新增益 | 15 | 四项基础 Agent 难稳定实现的能力：页序规划（`alloc_roles`）、证据绑定（证据脚注 + 双形态映射）、图表-数据四态绑定（含"位图无数据只占位"）、局部编辑 + 版本回退（`apply_edits` + `deck_<v>.pptx`） |
| 可靠体验 | 10 | **本版主攻**：D1–D14 决策规则 + F1–F5 失败分支表 + 五阶段裁决点 V1–V5 + 四脚本非零退出码语义 + 契约四形态（禁 null）；每条规则均带记录字段，降级不留痕即视为未执行 |
| 生态贡献 | 10 | 文档齐全（README/TEST/OUTPUT_CONTRACT/RUBRIC_MAP/DECK_SPEC/EDIT_OPS/failure-modes + 示例）；模板与结果信封参数化可复用；脚本按四层职责切分可单独 import |

GitHub 公开链接（额外 5 分）：见根目录 `GITHUB_URL.txt`。

---

## 11. 诚实边界（不主张什么）

1. **预览 ≠ Office 导出**：无 PowerPoint/LibreOffice 环境时预览是 PIL/reportlab
   近似渲染，文件名与 `previews.method` 均已如实标注。
2. **自检通过 ≠ 内容正确**：三层核验各管一段，互不顶替（见 §6 末段）。
3. **不覆盖**：论文精读/综述、可视化算法研发、文字润色、PPT 软件研发。
4. **不预制答案**：本 Skill 不含任何正式案例的答案；`examples/` 为虚构材料，
   明确标注"示例，非正式案例"，也不冒充正式案例结果。
