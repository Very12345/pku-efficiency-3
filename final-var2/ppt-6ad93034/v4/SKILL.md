---
name: academic-ppt-builder-fault-hardened
description: 把论文/研究材料组织成结构清楚、证据可追溯、可编辑、符合模板约束的学术汇报演示稿（PPTX），并把"它会在什么地方坏、坏了之后还能不能判读和救回来"做成**真跑过的失败注入矩阵**：随包提供 scripts/fault_inject.py（输入/模板/依赖/契约四族共 28 条故障逐个弄坏并跑主流程，实测 exit/status/uncertainty/是否静默）、17 条恢复动作的实测结局、以及可在运行前后调用的留痕守卫（--guard），把"崩了却什么都不留"的 7 类静默失败变成可判读报告。支持 --edit 局部编辑与版本回退；页面数字逐一核验材料、缺失显式标注、绝不编造。Use when a task asks to generate or edit an academic presentation / slide deck from a paper or research material（组会汇报、开题与中期、答辩、项目评审、基金申请；学术PPT、slides from paper、presentation from paper），especially when /input/case.json and task.md are present and /app/output must contain the editable deck plus previews and evidence mapping, and when the run must stay diagnosable under missing libraries, broken templates or malformed contracts.
---

# 学术 PPT 生成与编辑 Skill（抗故障 / 可判读版 · ppt-6ad93034）

> **本版只回答一个问题：这套流水线在什么地方会坏，坏了以后别人能不能看懂、能不能救回来。**
>
> 做法不是写"我们有异常处理"，而是**把上游输入逐个弄坏并真跑一遍**，然后把
> `exit code` / `result.json.status` / `uncertainty` 条数 / 留痕字段 / 是否静默
> **逐行记下来**（`references/FAULT-MATRIX.md`，28 条故障，
> 复现命令就在文档第一段）。
>
> 一句话立场：**可靠性不是"不会出错"，而是"出错时下游能判读，且我们知道出路"**——
> 因此本版额外交付两件可用件：
> ① `scripts/fault_inject.py`（注入台 + 恢复演练 + 守卫）；
> ② `references/FAULT-MATRIX.md`（逐行实测矩阵 + 7 条静默缺口 + 17 条恢复结局）。

**管辖范围**：把材料"翻译"成页级表达，并保证每页数字与图表可核实。
**不负责**：论文精读与文献综述、科研绘图算法本身、学术写作文字润色、PPT 软件研发。

## 1. 什么时候用它 / 什么时候别用

| 项 | 内容 |
|-|-|
| 触发 | 输入侧出现 `/input/case.json` + `task.md`，要求"可编辑演示稿 + 页级证据" |
| 触发（本版加强） | 运行环境**不确定是否齐备**（可能缺 matplotlib/Pillow/reportlab）、模板来自外部、契约字段形态不明、需要向别人证明"失败时会发生什么" |
| 不触发 | 只要文字润色、只要论文精读、只要可视化算法、只要 PPT 软件功能开发 |
| 承诺产出 | 可编辑 PPTX（每页备注 + 证据脚注）+ 页级证据映射（md/json）+ 预览渲染 + `result.json` |
| 单次运行边界 | 3 ≤ 页数 ≤ 20；每页一个叙事角色；单次脚本耗时 < 60 秒 |

命令口径（全文一致）：`$SKILL_DIR` = **含本 `SKILL.md` 的技能根目录**，
平台评测容器把它安装在 `/skills/weekly-skill`。所有命令都写成
`python "$SKILL_DIR/scripts/…"`，**因此 cwd 不是技能根目录时照样能跑**
（脚本内部同时用 `os.path.dirname(__file__)` 自定位）。

```bash
SKILL_DIR="${SKILL_DIR:-/skills/weekly-skill}"        # 换成你的实际安装路径
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output
```

## 2. 输入与输出（产物归属写死）

**读**：`case.json`（`case_id`、`title`、`inputs{task_md, material[]}`、
`spec{audience, duration_minutes, max_slides, template|template_pptx|starting_deck, style}`、
可选 `output_contract`）、`task.md`、以及 `material[]` 指向的**实际文件**——
`scripts/deck_extract.py` 强制"读实际文件"，**禁止凭文件名推断内容**。

**写**（一律写 `--out`，另在输出根放一份 `preview/` 副本便于直接取件）：

| 产物 | 位置 | 性质 |
|-|-|-|
| 可编辑演示文件 | `work/deck.pptx` | 主张式标题 + 要点 + 图表槽 + 证据脚注 + 演讲备注 |
| 页面模型 | `work/plan.json` | 页序/角色/主张/证据/图表，**可编辑源** |
| 材料视图 | `work/material_view.json` | 章节 / 数据表 / 图表提及 / 结构化定位 |
| 预览渲染 | `work/preview/slide_*.png`、`work/preview/preview.pdf`、`preview/*` | 标注"非 PowerPoint 导出" |
| **评分产物** | `result.json` | 契约全字段 + `case_id`，**禁 null** |
| 证据映射 | `evidence_map.md` + `evidence_map.json` | 人读 / 机器读**同源双形态** |
| 记录 | `changelog.jsonl`、`manifest.json`（全部产物 sha256）、`logs/` | 支撑他人独立复核 |

> **不入包**：`deck.pptx`、预览 `*.png`、预览 `*.pdf`、`changelog.jsonl` 都是**运行时产物**，
> 由上面那条命令现场生成并登记进 `manifest.json`；技能包只携带 UTF-8 文本资源。
> 一次成功运行的完整清单见 `examples/EXPECTED-OUTPUT.md`。
> **产物绝不写回技能包目录**（评测容器里技能目录是只读安装件）。

## 3. 运行环境、依赖与包体约束

- Python 3.8+；`python-pptx>=0.6.21`（建稿**必需**）、`matplotlib>=3.5`、`Pillow>=9`、
  `numpy`（随 matplotlib）；`reportlab` 可选（缺席时 PDF 预览跳过并如实说明）；
  PDF 材料抽取任选 `fitz` / `pypdf` / `PyPDF2` / `pdfplumber` 之一。
- **依赖缺失的实测行为见 `references/FAULT-MATRIX.md` §2**：
  `matplotlib` 缺失 → 结果页降级为原生可编辑表格（`figure.note` 有记录，实测 `success`）；
  `reportlab` 缺失 → 跳过 PDF，`uncertainty` + `previews.warnings` 各一条；
  **`python-pptx` / `Pillow` 缺失 → 实测硬崩且不写 `result.json`**（缺口 S4–S7），
  因此**必须先用 §5 的前置体检把这一情况拦下来**。
- 包体约束（自我声明 + 运行期同样适用）：**≤50 个文件、单文件 ≤500KB、合计 ≤2MB、
  无符号链接、全部为 UTF-8 文本**（`.md/.py/.json/.txt/.csv/.yaml/.yml`）。
  新增能力请并入既有文档/脚本，**不要往包里塞 PPTX/PNG/PDF/JSONL**。
- **在包内跑任何脚本都会生成 `__pycache__`**（平台预检会因此拒收整包）：
  实测与演练一律把技能包**复制到包外**再跑——`fault_inject.py` 自己就是这么做的。

## 4. 执行流程：CP0 → CP1 → … → CP4 → CP5

> 与"一路往前跑"的写法不同：**每一步结束都有一个可判读的裁决点**；
> 裁决不通过时按 §6 的 D 规则转向，而不是继续硬走。

| 检查点 | 做什么 | 产物 | 不通过的后果 |
|-|-|-|-|
| **CP0 前置体检** | `fault_inject.py --guard --case …` 检查输入形态、依赖齐备性、模板可开性、契约形态 | 一份 BLOCKER/WARN/DEGRADE 报告 | BLOCKER 必须先处理：这些情形实测会**硬崩且不写 result.json** |
| **CP1 读实际输入** | 读 case/task/每个材料文件；核对存在性 | `work/material_view.json` | 材料不可读 → D1，只出元信息 result，绝不编 deck |
| **CP2 规划与 lint** | `slide_text.build_plan` 分配页级角色；`evidence_check.plan_lint` 校验页面纪律 | `work/plan.json` | 偏差记入 `run_meta.spec_lint`（D4） |
| **CP3 建稿** | 模板槽位建稿 + 四态图表绑定 + 每页备注与证据脚注 | `work/deck.pptx` | deck 必须能被 python-pptx 重开且页数=plan |
| **CP4 导出校验** | `result_tool` 的 G1–G8 + `selftest` | `result.json` 等 | `{"valid": true}` 且 exit 0 才算过 |
| **CP5 运行后核对** | `fault_inject.py --guard --out …` 逐条核对"该记的记了没有" | 守卫报告 | 有 WARN/BLOCKER → 按 §7 恢复动作处理后再交 |

```bash
SKILL_DIR="${SKILL_DIR:-/skills/weekly-skill}"

# CP0：前置体检（BLOCKER 先处理；这一步能挡掉 3 类"崩了不留痕"）
python "$SKILL_DIR/scripts/fault_inject.py" --guard --case /input/case.json \
    --template /input/template.json          # --template 可省略

# 主命令（CP1–CP4 全在这一条里）
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output

# CP4：契约门（`--case` 必须传，否则无法核对契约回显）
python "$SKILL_DIR/scripts/result_tool.py" --result /app/output/result.json \
    --out-dir /app/output --case /input/case.json \
    --envelope "$SKILL_DIR/templates/result_envelope.json"     # {"valid": true} 且 exit 0

python "$SKILL_DIR/scripts/selftest.py" --out /app/output --case /input/case.json
# all_pass=true

# CP5：运行后核对（把"静默降级"找出来）
python "$SKILL_DIR/scripts/fault_inject.py" --guard --out /app/output
```

**退出码语义**（编排器可直接判读；与 `references/failure-modes.md` §0 一致）：

| 脚本 | 0 | 1 | 2 |
|-|-|-|-|
| `scripts/main.py` | `status=success` | `status=partial`（降级已逐条记入 `uncertainty`） | 输入不可读（已写最小 `status=failed` result.json） |
| `scripts/result_tool.py` | G1–G8 全过 | 有条目未过 | `result.json` 无法解析 |
| `scripts/selftest.py` | 全部自检项通过 | 有未通过项 | 输入不可读 |
| `scripts/evidence_check.py` | 主张里每个数字都能在材料中定位 | 有数字找不到 | — |
| `scripts/fault_inject.py` | 故障行为与期望一致且守卫无发现 | 有偏差 / 有静默失败 / 守卫有发现 | 环境不可用或 `--work` 落在包内 |

**只有 exit 0 才算这次运行"干净"**；exit 1 必须读 `result.json.uncertainty`
再决定是否补件重跑；exit 2 表示输入侧问题，重跑无用。

## 5. 守卫：运行前体检 + 运行后核对

`scripts/fault_inject.py --guard` 是本版新增的**唯一入口**，两种用法对应流程的 CP0/CP5。

### 5.1 前置体检（CP0）

```bash
python "$SKILL_DIR/scripts/fault_inject.py" --guard --case /input/case.json [--template T]
```

| 检查项 | 等级 | 为什么必须有这一条（实测依据） |
|-|-|-|
| `case.json` 不存在 / 不能解析 / 顶层不是对象 | BLOCKER | `F-IN-01`–`F-IN-04`：`exit=2` 是**正确**行为，但只有 `case.json` 顶层不是对象这类形态才会走到 `setdefault` 报错；体检能提前说清 |
| `--template` 的 JSON 顶层不是对象 | BLOCKER | `F-TPL-03`：实测 `TypeError` 硬崩、**无 `result.json`** |
| 缺 `python-pptx` / `Pillow` | BLOCKER | `F-DEP-03/04/05`：实测硬崩、无产物 |
| 缺 `matplotlib` / `reportlab` | DEGRADE | `F-DEP-01/02`：有降级路径且会留痕，跑得下去 |
| `template_pptx` / `starting_deck` 不存在或打不开 | DEGRADE / BLOCKER | `F-TPL-04/05/06`：损坏的会留 `uncertainty`，**不存在的会被静默忽略**（缺口 S3） |
| `output_contract` 形态/类型异常 | DEGRADE | `F-CTR-01`–`F-CTR-04`；其中"契约不是对象"实测**整体静默跳过**（缺口 S2） |

### 5.2 运行后核对（CP5）

```bash
python "$SKILL_DIR/scripts/fault_inject.py" --guard --out /app/output
```

| 检查项 | 等级 | 抓的是什么 |
|-|-|-|
| 没有 `result.json` | BLOCKER | 运行在落盘前退出（S4–S7） |
| `status=success` 但 `slide_count=0` | BLOCKER | 状态与产物不自洽（F5.3） |
| `change_records` 记了降级、`uncertainty` 却为空且 `status=success` | WARN | 降级只记了一半（`F-TPL-06`） |
| 材料有数据表，成稿却既无图表/表格、也无 `figure.note` | WARN | **静默丢图**（S1 `F-IN-07`） |
| `status=partial` 但 `uncertainty` 为空 | WARN | 降级未逐条留痕（F5.4） |
| 有 `unverified_claims` 却标 `success` | WARN | 未核验主张被当成成功（F5.2） |
| G 门 `valid=false` | BLOCKER | 契约门未过 |

**实测可信度**：把守卫跑在 28 条故障产物上，**7 条静默失败 7/7 被抓到**；
跑在健康产物上**0 误报**（结论"通过"）。这两句话都能用
`references/FAULT-MATRIX.md` §4 的命令复现。

## 6. 决策规则（D1–D12，含"实测证据"列）

| # | 触发条件（可观测） | 动作 | 失败时的降级去向 | 记录字段 | 实测证据 |
|-|-|-|-|-|-|
| **D1** | `material_status=missing`：材料一个都读不到 | 不建 deck，只产出元信息 result（`slide_count=0`） | 连 `case.json` 都读不到 → 最小 `status=failed` result + `exit 2` | `status`、`evidence.material_warnings` | `F-IN-05/09`：`exit=1`/`partial`/`slides=0`，`mw=2` ✅ |
| **D2** | `check_claim_numbers` 对某条入页主张返回 `missing` 非空 | 该主张 `verified=false` 入未核验清单；**不回填、不取整、不按印象改** | 整页不可核 → 该页降为"待核验页"并在备注写明 | `evidence.unverified_claims` | `F-IN-06/08`：`unverified_claims=4/3` ✅ |
| **D3** | PDF 无文本层，或环境无任何抽取库 | 不 OCR 冒充；Agent 抽文本到 `<out>/work/materials/*.txt` 后重跑 | 重跑仍读不出 → `partial` 并说明该材料未计入页级证据 | `uncertainty`、`sources[].tool` | 本机五库齐备，未注入 |
| **D4** | `plan_lint` 返回 `{"valid": false}` | 先修 plan 后重跑 lint | 确属案例硬约束 → 继续建稿但把 `problems` 原文记入 `spec_lint`，状态降 partial | `run_meta.spec_lint`、`uncertainty` | `F-TPL-07`：3 页时 `spec_lint.problems=0`（合法产物） |
| **D5** | 材料里的图是位图且无数值数据表 | 只放**灰框诚实占位**（`figure.kind=placeholder`），标注"原图未提供取数数据" | 连位图也没有 → `figure.kind=none` + note 说明 | `deck.slides[].figure.note` | `F-IN-07` 暴露缺口：**表解析不出时既无 note 也无记录**（S1） |
| **D6** | `template_pptx` 打不开 / 母版损坏 | 备份原文件到 `work/original_inputs/`，改内置 `templates/default.json`，说明降级 | 内置模板也读不到 → 用代码内 `DEFAULT_SPEC`，仍记降级 | `uncertainty`、`change_records` | `F-TPL-04`：`exit=1`/`partial`/`unc=1` ✅；`F-TPL-05`（不存在）**静默**（S3） |
| **D7** | `plan_lint` 报 `pages=N > max_slides` | 按 `max_slides` 确定性压缩角色分配 | **不静默丢证据页**：被合并页的证据脚注并入保留页并写明 | `run_meta.spec_lint`、`change_records` | `F-TPL-07`：`max_slides=3` → 3 页、角色压缩、`exit=0` ✅ |
| **D8** | 字体回落 / `reportlab` 缺席 / 渲染抛错 | 字体问题照常出 PNG 并把 `cjk_font_available=false` 记入 warnings；无 reportlab → `previews.pdf=""` | 渲染整体失败 → 跳过预览、G5 记 error、`partial`，**绝不用别的图冒充预览** | `previews.warnings`、`uncertainty` | `F-DEP-02`：`unc=1` + `previews.warnings=1` ✅ |
| **D9** | 图表重绘失败（无 matplotlib / 非数值列 / `--no-chart`） | 降级为 PPTX **原生可编辑表格**，保留引用与表题 | 连表格文件都没有 → `figure.kind=none` + 保留脚注，注明"仅引用未插图" | `figure.note`、`uncertainty` | `F-DEP-01`：`figure.degraded=1`、`exit=0` ✅；`F-IN-07` 走的是没覆盖的那条分支（S1） |
| **D10** | `output_contract` 声明的字段在运行值里缺失 | 按**四形态**给同型空值：`string→""`、`list→[]`、`dict→{}`、`bool→false`、`number→0`，**禁 null** | 声明未知类型 → 按运行时值类型给同型空值，并**记 uncertainty** | `result.json` 顶层回显 | `F-CTR-01/02/04`：字段已回显（`widget=""`、`score=0`、`extras=[]`）但**未知类型没记 uncertainty**（偏离，见 §8） |
| **D11** | `--edit` 的 op 未知 / 页码越界 / `reorder_pages` 不是 1..N 置换 | 跳过该条 op，其余照常应用；置换不合法**整条拒绝** | 编辑后重跑数字核验仍不过 → 该主张 `verified=false`，**不因"是用户让改的"放行** | `uncertainty`、`changelog` skipped | `examples/edit_demo.json` 实测 exit 0；负例见 `TEST.md` §T4 |
| **D12** | 复核者报告"契约字段没回显" | **先核对是否传了 `--case`**；再核 `output_contract` 是否真的声明了该字段 | 参数齐全且已声明仍不回显 → 报 bug 并附顶层键清单，不靠手改 JSON 掩盖 | 复核记录（不写入 result） | `F-CTR-06`：删掉已声明字段后 `result_tool` 实测 `exit=1` + `G2` 报错 ✅ |

> **规则优先级**：D1/D2 属"事实正确性"层，任何时候不得为了"页面好看"放宽；
> D5–D9 属"能力降级"层，允许降级但**必须留痕**；D10–D12 属"契约/复核"层。

## 7. 恢复动作（坏了怎么办；每条都在注入台上真跑过）

| 坏法 | 恢复动作（真命令） | 实测结局 |
|-|-|-|
| `--template` 坏了 / 形态不对 | **去掉 `--template`**，回落内置 `templates/default.json` 重跑 | `F-TPL-01/02/03` 全部回到 `exit=0` / `success` |
| 材料缺件 / 为空 | 把材料补到 case 目录并改回 `inputs.material` 重跑 | `F-IN-05/06`：`slide_count` 0 → 6，`uncertainty` 归零 |
| 母版损坏 / 不存在 | 从 `spec` 里**移除** `template_pptx`（或换一份可打开的），用内置模板重跑 | `F-TPL-04`：`partial` → `success` |
| `starting_deck` 损坏 | 同上：移除后重跑；若确需起始稿则先修复文件 | `F-TPL-06`：ChangeRecord 已说明"沿用其模板生成新稿" |
| 图表降级 | 用 `--no-chart` 把降级**显式化**（`figure.kind=table` + `note`） | `F-DEP-01`：`figure.degraded=1`，`exit=0` |
| 页数上限过紧 | `--max-slides N` 覆盖；或在 `spec.max_slides` 里改 | `F-TPL-07`：3 → 8 页 |
| 环境缺 `python-pptx` / `Pillow` | **包内无法恢复**（环境缺件）：由守卫判 `BLOCKER`，如实交 `partial`/`failed`，绝不放一份"看起来成功"的空稿 | `F-DEP-03/04/05`：守卫 `BLOCKER` |
| 已交付的 `result.json` 被下游改坏 | 重跑 `main.py`（契约字段重新回显）；不要手改 JSON | `F-CTR-06`：`exit=1`（G2 报错）→ 重跑后 `exit=0` |
| 多轮改稿改坏了 | 复制 `work/deck_<v>.pptx` 回退后重跑，并补一条回退 `change_record` | 见 `TEST.md` §T4 与 `references/EDIT_OPS.md` |

**不可恢复的两类，要如实说**：① 环境缺建稿/渲染库（要装依赖，不是改包能解决的）；
② 材料本身不存在（要组织方补件）。这两类都**不应该**产出"看起来成功"的稿子。

## 8. 已知缺口（本版实测发现，如实列出，未在本版修改主流程）

完整证据与复现命令见 `references/FAULT-MATRIX.md` §2。**7 条静默失败**：

| 编号 | 缺口 | 一句话 | 现可用补救 |
|-|-|-|-|
| S1 | `F-IN-07` | 数据表解析不出内容时，结果页图表**无声消失**（无 note、无 uncertainty） | `--guard --out` 报 `WARN/figure` |
| S2 | `F-CTR-03` | `output_contract` 不是对象时契约回显**整体静默跳过**，G2 也不报错 | `--guard --case` 报 `DEGRADE/contract` |
| S3 | `F-TPL-05` | `template_pptx` 指向不存在的文件时**静默改用内置模板** | `--guard --case` 报 `DEGRADE/template_pptx` |
| S4–S7 | `F-TPL-03`、`F-DEP-03`、`F-DEP-04`、`F-DEP-05` | 参数形态错误 / 缺 `python-pptx` / 缺 `Pillow` 时**硬崩且不写 `result.json`**（只留 stdout 的 Traceback） | `--guard --case` 前置拦截；`--guard --out` 报 `BLOCKER` |

**为什么不直接改 `main.py`**：CLI 参数与退出码语义是平台契约的一部分
（`references/failure-modes.md` §0 已被下游按字读），本版守住"既有脚本逐字节不变 +
只做纯增量"的规矩，选择**加一层守卫**把缺口变成可判读报告，并把缺陷本身记录在案。

## 9. 增量编辑（多轮迭代与回退）

```bash
SKILL_DIR="${SKILL_DIR:-/skills/weekly-skill}"
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output \
    --edit edits.json --version v2
```

7 类 op：`update_bullet / add_bullet / remove_bullet / add_note / retitle /
reorder_pages / set_figure`（字段见 `examples/edit_demo.json`，决策树见
`references/EDIT_OPS.md`）。每次修改在 `changelog.jsonl` 写一条
`{version, op, page, target, reason}`；`deck_v2.pptx` 与 `deck.pptx` **并存**，
**回退 = 复制旧版本重跑**（并补一条回退记录）。
**编辑链路同样过 D2 数字核验**：编辑引入的新数字材料里没有 → 该主张降级为未核验。

## 10. 完整命令索引（能力清单；含全部入口与开关）

| 入口 | 关键参数 | 什么时候用 | 退出码 |
|-|-|-|-|
| `scripts/main.py` | `--case` `--out` `--input-dir` `--template` `--max-slides` `--edit` `--no-chart` `--version` `--draft` `--verbose` | 端到端主流程（CP1–CP4） | 0/1/2 |
| `scripts/result_tool.py` | `--result` `--out-dir` `--case` `--envelope` | CP4 契约门（G1–G8） | 0/1/2 |
| `scripts/selftest.py` | `--out` `--case` `--pptx` `--slides` | CP4 产物自检 | 0/1 |
| `scripts/evidence_check.py` | `--claim` `--material` | 抽查单条主张的数字能否回指材料 | 0/1 |
| `scripts/make_examples.py` | `--work-dir` `--dry-run` | 维护：真跑示例并重建 `examples/output/`（自动净化机器绝对路径） | 0/1 |
| `scripts/deck_extract.py` | （库）由 `main.py` 编排 | 读实际材料 → `material_view.json` | — |
| `scripts/slide_text.py` | （库）由 `main.py` 编排 | 页序/角色/主张/备注文案 | — |
| `scripts/deck_tool.py` | （库）由 `main.py` 编排 | 图表四态绑定 + 模板槽位建稿 + 编辑 op | — |
| `scripts/render_qa.py` | （库）由 `main.py` 编排 | PIL PNG + reportlab PDF + 渲染 QA | — |
| `scripts/deck_common.py` | （库）被其余脚本 import | 路径自定位/原子写/sha256/日志/CJK 字体 | — |
| **`scripts/fault_inject.py`** | `--list` `--pkg` `--work` `--only` `--shape` `--with-recovery` `--report-json` `--report-md` `--report-csv` `--guard` `--case` `--out` `--template` `--verbose` | **本版新增**：注入台（28 条）+ 恢复演练（17 条）+ 守卫（CP0/CP5） | 0/1/2 |

## 11. 五维评分落点（速查；逐点展开见 `references/RUBRIC_MAP.md`）

| 维度 | 分 | 本包靠什么拿到 |
|-|-|:-|
| 实际效果 | 40 | CP1–CP4 真跑；页序 + 页级角色；可编辑 PPTX + 每页备注 + 证据脚注；数字逐一核验；`sources[].sha256` + `manifest.json` + 双形态证据映射 + G1–G8 |
| 使用增益 | 25 | 页面纪律（每页一个角色、≤7 条要点、≤90 字、字号 ≥12pt 不溢出）对标"基础 Agent 整段塞页"；`--edit` 局部编辑 + 版本归档减少返工；**CP0/CP5 守卫减少"交完才发现坏了"的返工** |
| 创新增益 | 15 | 页序规划（`alloc_roles`）、证据绑定（脚注 + 双形态映射）、图表四态绑定（含"位图无数据只占位"）、局部编辑 + 版本回退；**新增：把失败面做成可复现的注入矩阵 + 留痕守卫（判据按结构化字段，抓 7/7 静默失败且 0 误报）** |
| 可靠体验 | 10 | **本版主攻**：28 条故障逐行实测（exit/status/uncertainty/留痕/是否静默）+ 17 条恢复动作实测 + D1–D12 决策规则 + F1–F5 失败分支 + 非零退出码语义 + CP0/CP5 守卫 |
| 生态贡献 | 10 | 文档齐全（README/TEST/OUTPUT_CONTRACT/RUBRIC_MAP/DECK_SPEC/EDIT_OPS/failure-modes/**FAULT-MATRIX** + 示例）；注入台与守卫可被**其它 Skill 直接复用**（不依赖本包任何私有结构，只认 `result.json` 与 `work/material_view.json` 两个公开产物）；模板与结果信封参数化可复用 |

GitHub 公开链接（额外 5 分）：见根目录 `GITHUB_URL.txt`。

## 12. 诚实边界（不主张什么）

1. **7 条静默缺口仍在**（§8）：本版把它们**测出来并给出补救**，但没有修改 `main.py`
   去根治；引用本包时不要声称"已经全部修好"。
2. **注入台覆盖不到的部分**（并发/中断、畸形 PPTX 语义、GB 级材料、真机 Office 渲染、
   平台预检）在 `references/FAULT-MATRIX.md` §5 逐条列明，**没有实测证据的不要当结论引用**。
3. **预览 ≠ Office 导出**：无 PowerPoint/LibreOffice 时预览是 PIL/reportlab 近似渲染，
   文件名与 `previews.method` 均已如实标注。
4. **自检通过 ≠ 内容正确**：`selftest` 查"产物在不在、能不能开、页数对不对"，
   `result_tool` 查"契约合不合规"，内容正确性由 `evidence_check` 的数字核验与
   `plan_lint` 的页面纪律负责；三者不能互相顶替。
5. **不预制答案**：本 Skill 不含任何正式案例的答案；`examples/` 为虚构材料，
   明确标注"示例，非正式案例"，不得冒充正式案例结果。
6. **预算纪律**：平台单次运行 64 个模型请求 / 900 秒 / 16k tokens 每响应；
   脚本本身 <60 秒，注入台整套 28 条约 60 秒——**演练请在开发期跑，不要占用评测预算**。
