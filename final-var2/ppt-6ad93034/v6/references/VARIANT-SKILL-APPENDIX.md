# VARIANT-SKILL-APPENDIX.md — v4 / v5 的 SKILL 正文原文（溯源用）

> **为什么要这份附录**：v6 的 `SKILL.md` 按本轮规范要求**重排为「输入 → 执行 → 失败 → 增益 →
> 机制 → 复用」并逐节索引**，因此措辞与 v4/v5 不同。为了做到"union 包不丢内容"，
> 这里把 v4 与 v5 的 SKILL 正文**逐字保留**，供对照与溯源；
> 两者的**证据文件**（`FAULT-MATRIX.md` / `CASE-SET.md` / `fault_inject.py` /
> `case_check.py` / `examples/cases/**`）已在 v6 中**逐字节并入**，无需在此重复。
>
> 阅读顺序：先读 v6 的 `SKILL.md`（整合版），需要追溯某一版本原始表述时再看本附录。

---

# 附录 C：v4（抗故障 / 可判读版）SKILL 正文 —— 原文逐字保留

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

---

# 附录 D：v5（多案例泛化版）SKILL 正文 —— 原文逐字保留

# 学术 PPT 生成与编辑 Skill（多案例泛化版 · ppt-6ad93034）

> **本版回答的问题是：这套流程换一个题材还灵吗？换一种材料结构呢？**
>
> 做法不是再写几个"适用范围"，而是**把两个不同题材的案例连同可接受区间一起放进包里**，
> 再用 `scripts/case_check.py` 真跑、真判、真报缺口：
> 实测结果（含四种边界变形的结论）全在 `references/CASE-SET.md`。
>
> 一句话立场：**"能跑通"不等于"换个案例还行"**——
> 所以本版把"还行"写成**可执行的判据**（`_case_set.expect`），
> 并如实标出**做不到的地方**（`_case_set.known_gaps` + §7 失效边界）。

**管辖范围**：把材料"翻译"成页级表达，并保证每页数字与图表可核实。
**不负责**：论文精读与文献综述、科研绘图算法本身、学术写作文字润色、PPT 软件研发。

## 1. 题集一览：两个题材、两个难度层

| | 案例 A `case-a-perovskite` | 案例 B `case-b-climate-text` |
|-|-|-|
| 题材 | 实验科学 / 材料器件（钙钛矿界面钝化） | 理论 / 文献计量（气候政策议题迁移） |
| 难度层 | **基础层**：数值表齐备（CSV）、章节清晰 | **困难层**：**无任何数值表**、位图无取数、6 页上限、带大量方括号引用 |
| 输入 | `case.json` `material.md` `jv.csv` `task.md` | `case.json` `material.md` `task.md` |
| 受众/时长/页数 | 答辩 / 12 min / 8 页 | 同行 / 8 min / 6 页 |
| 最关键的检验 | 数值表**原样重绘**；结论数字不得走样 | **不许凭空画曲线**（禁 `chart_image`）；引用编号可回指 |

**两个案例都不是答案**：材料是虚构论文正文与数据，`examples/cases/**` 里没有任何 `result.json`
或成品幻灯片。平台固定案例由组织方提供，本包不为它预制任何结果。

## 2. 命令口径与快速开始

`$SKILL_DIR` = **含本 `SKILL.md` 的技能根目录**（平台容器内为 `/skills/weekly-skill`），
所有命令都写成 `python "$SKILL_DIR/scripts/…"`，**cwd 不是技能根目录时照样能跑**。

```bash
SKILL_DIR="${SKILL_DIR:-/skills/weekly-skill}"
OUT=/app/output

# ① 主流程（对平台给的 case.json 跑一遍）
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out "$OUT"

# ② 契约门 G1–G8（`--case` 必须传，否则无法核对契约回显）
python "$SKILL_DIR/scripts/result_tool.py" --result "$OUT/result.json" \
    --out-dir "$OUT" --case /input/case.json \
    --envelope "$SKILL_DIR/templates/result_envelope.json"     # {"valid": true} 且 exit 0

# ③ 产物自检
python "$SKILL_DIR/scripts/selftest.py" --out "$OUT" --case /input/case.json   # all_pass=true

# ④ 泛化台：把包内两个合成案例各跑一遍并判定（开发期用，约 5 秒）
python "$SKILL_DIR/scripts/case_check.py" --list
python "$SKILL_DIR/scripts/case_check.py" --pkg "$SKILL_DIR" --work <包外目录> --probes

# ⑤ 局部编辑 + 版本归档
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out "$OUT" \
    --edit edits.json --version v2
```

> **必须在包外跑**：任何脚本都会让 Python 在包内写 `__pycache__`，平台预检会因此拒收整包。
> `case_check.py` 自己就把被测包复制到包外再执行。

**退出码语义**（编排器可直接判读；与 `references/failure-modes.md` §0 一致）：

| 脚本 | 0 | 1 | 2 |
|-|-|-|-|
| `scripts/main.py` | `status=success` | `status=partial`（降级已逐条记入 `uncertainty`） | 输入不可读（已写最小 `status=failed` result.json） |
| `scripts/result_tool.py` | G1–G8 全过 | 有条目未过 | `result.json` 无法解析 |
| `scripts/selftest.py` | 全部自检项通过 | 有未通过项 | 输入不可读 |
| `scripts/evidence_check.py` | 主张里每个数字都能定位 | 有数字找不到 | — |
| `scripts/case_check.py` | 全部案例通过判定 | 有案例未过判定 | 环境/案例不可用 |

**只有 exit 0 才算"干净"**；exit 1 必须读 `result.json.uncertainty` 再决定是否补件重跑。

## 3. 输入、输出与产物归属

**读**：`case.json`（`case_id`、`title`、`inputs{task_md, material[]}`、
`spec{audience, duration_minutes, max_slides, template|template_pptx|starting_deck, style}`、
可选 `output_contract`）、`task.md`、`material[]` 指向的**实际文件**——
`scripts/deck_extract.py` 强制"读实际文件"，**禁止凭文件名推断内容**。

**写**（一律写 `--out`，并在输出根放一份 `preview/` 副本便于直接取件）：

| 产物 | 位置 | 说明 |
|-|-|-|
| 可编辑演示文件 | `work/deck.pptx` | 主张式标题 + 要点 + 图表槽 + 证据脚注 + 演讲备注 |
| 页面模型 | `work/plan.json` | 页序 / 角色 / 主张 / 证据 / 图表，**可编辑源** |
| 材料视图 | `work/material_view.json` | 章节 / 数据表 / 图表提及（**多表时两张都会登记**，但只有第一张会被绑定，见 §7） |
| 预览渲染 | `work/preview/slide_*.png`、`work/preview/preview.pdf`、输出根 `preview/*` | 标注"非 PowerPoint 导出" |
| **评分产物** | `result.json` | 契约全字段 + `case_id`，**禁 null** |
| 证据映射 | `evidence_map.md` + `evidence_map.json` | 人读 / 机器读**同源双形态** |
| 记录 | `changelog.jsonl`、`manifest.json`、`logs/` | 支撑他人独立复核 |

> **不入包**：`deck.pptx`、预览 `*.png`/`*.pdf`、`changelog.jsonl` 都是运行时产物；
> 技能包只携带 UTF-8 文本资源（`.md/.py/.json/.txt/.csv/.yaml/.yml`）。
> **产物绝不写回技能包目录**——评测容器里技能目录是只读安装件。

## 4. 执行流程（CP1–CP4）+ 两条泛化纪律

| 检查点 | 动作 | 判定 |
|-|-|-|
| **CP1 读实际输入** | 读 case/task/每个材料；核对存在性 | 材料是否可读（缺失 → D1） |
| **CP2 规划与 lint** | 角色分配 + 页序 + 主张与证据指针；`evidence_check.plan_lint` | `valid` 或记录偏差（D4） |
| **CP3 建稿** | 模板槽位建稿 + 四态图表绑定 + 备注 + 脚注 | deck 可重开且页数=plan |
| **CP4 导出校验** | `result_tool` 的 G1–G8 + `selftest` | `{"valid": true}` 且 exit 0 |

**泛化纪律 ①：材料结构不是标准论文骨架时，必须人工看页面。**
实测（`CASE-SET.md` §3）：角色→章节是**按标题关键词**映射的；
材料若用"三阶段 / 争论焦点 / 方法与数据争议"这类小节名，
会出现"结果页取到摘要、方法页取到局限"的**内容错位但不报错**。
G1–G8 与自检都抓不到这类问题。

**泛化纪律 ②：多个数据源时，`material[]` 的顺序就是优先级。**
实测：材料给了两张 CSV 时**只绑定第一张**，第二张既不进页面也不留 uncertainty。
需要哪张表进结果页，就把它放在 `material[]` 第一位。

## 5. 可接受区间：判据写在案例里，而不是写在文档里

每个 `case.json` 的 `_case_set.expect` 是一份**可执行判据**；`case_check.py` 逐条对照：

| 判据 | 含义 | 例（案例 B） |
|-|-|-|
| `status_any_of` | **允许诚实降级**：材料有缺口时 `partial` 才是对的结果 | `["success","partial"]` |
| `slide_count` | 页数必须等于 `spec.max_slides` | `6` |
| `roles_head` / `roles_tail` | 首末角色固定（叙事完整性） | `cover` / `takeaway` |
| `must_have_figure_kind` | 必须有某类图表形态 | `["none","placeholder"]` |
| `forbid_figure_kind` | **不许编造** | `["chart_image"]` |
| `unverified_claims_max` | 待核验项上限 | `3` |
| `min_notes_coverage` / `min_evidence_footer_coverage` | 备注 / 脚注覆盖 | `1.0` / `1.0` |
| `must_mention_in_deck` | 关键数字或术语必须入页 | —（案例 B 把它移入 `known_gaps`） |
| `forbid_in_deck` | 禁列内容（防编造） | `["87.6％","12.4 万篇"]` |

**实测（两案各一次）**：案例 A **12/12 判据 PASS**、案例 B **11/11 PASS**；
两案的 `gate_valid=true`、`all_pass=true`、deck 可重开且页数一致、
备注与脚注覆盖都是 **1.0**、`result.json` 顶层 **20 个键**
（18 个基键 + 3 个契约回显字段，其中 1 个与基键重合）。
逐条数值见 `references/CASE-SET.md` §2。

> `_case_set.known_gaps` 是**如实标注的"没做到"**（例如案例 B 的材料年份 `2009/2015`
> 没有进页面）。它**不计入 FAIL，但每次运行都会被打印出来**——
> 让缺口可见，而不是把判据改成能过。

## 6. 决策规则（D1–D12，含泛化实测证据）

| # | 触发条件 | 动作 | 记录 | 泛化实测证据 |
|-|-|-|-|-|
| **D1** | 材料全读不到 | 不建 deck，只出元信息 result（`slide_count=0`） | `material_warnings` | 两案材料齐备；负路径见 `TEST.md` §T7 |
| **D2** | 主张里数字材料中找不到 | `verified=false` 进未核验清单，**不回填、不取整** | `unverified_claims` | 探针 P4：`--edit` 塞入 `31.7%` → 立刻进未核验清单 ✅ |
| **D3** | PDF 无文本层 / 无抽取库 | 不 OCR 冒充；Agent 抽文本后重跑 | `uncertainty` | 两案均为 `.md`/`.csv`，未触发 |
| **D4** | `plan_lint` 偏差 | 先修 plan；硬约束则继续但记录偏差并降 partial | `run_meta.spec_lint` | 探针 P2：报 `page 2 bullet too long (CJK-weighted=162 vs 90)` → 进 `uncertainty` ✅ |
| **D5** | 位图无取数数据 | 灰框诚实占位，不生成假曲线 | `figure.note` | 案例 B 材料明确写"原图为位图、未提供取数数据"，实测 **0 张编造图** ✅ |
| **D6** | 模板打不开 / 母版损坏 | 备份 → 内置模板并说明降级 | `uncertainty` + `change_records` | 两个案例都用内置模板；坏法实测见 `FAULT-MATRIX.md` |
| **D7** | 页数超限 | 确定性压缩角色，**不静默丢证据页** | `change_records` | ⚠️ 探针 P3：压到 3 页后角色变为 `cover→overview→result`，但 `change_records` **只有 start**（缺口，见 §7） |
| **D8** | 字体缺失 / 渲染不可用 | PPTX 只记字体名；预览回落并预警 | `previews.warnings` | 两案预览 PNG/PDF 均产出；CJK 字体 `Microsoft YaHei` |
| **D9** | 图表重绘失败 | 降级 PPTX 原生可编辑表格 + note | `figure.note` | 案例 B **无表可画**：`figure_kind=none ×6`，未走降级也未编造 ✅ |
| **D10** | 契约字段未知 / 无值 | 四形态空值 `""/[]/{}/false/0`，**禁 null** | 顶层回显 | 两案各回显 3 个额外字段（`case_topic`/`difficulty`/`is_synthetic`）✅ |
| **D11** | 编辑 op 非法 / 页码越界 | 跳过并记录，其余照常 | `uncertainty` + `changelog` | 探针 P4 的 `--edit` 正常应用并留 `change_record` ✅ |
| **D12** | 复核说"契约没回显" | **先查是否传了 `--case`** | 复核记录 | 两案判定都显式传入 `--case` |

## 7. 泛化失效边界（实测，逐条可复现）

> 完整证据（含原始数值）在 `references/CASE-SET.md` §3。这里只列结论。

| 编号 | 边界 | 现象 | 规避做法 |
|-|-|-|-|
| **GAP-A1** | 材料缺"标准小节" | 案例 A 没有"背景"小节 → `background` 页写占位主张 → `unverified=1`、`status=partial` | 这是**诚实降级**，不要把它当错误；确需干净 `success` 就补一节背景 |
| **GAP-A2** | markdown 表格 vs CSV | 材料里同时有 markdown 表（表 1）与 CSV 时，**数据源是 CSV**，表 1 的关键指标（如 PCE 24.8%）不会进页面 | 把要用的数值表**导出为 CSV 并放在 `material[]` 第一位** |
| **GAP-B1** | 编号小标题 | `## 1. …` 这类标题被当作列表项切分，产生只含 `1.` 的退化要点 | 材料侧避免"标题带序号"；或人工在 `--edit` 里修掉 |
| **GAP-B2** | 角色→章节映射 | 非标准骨架（人文/理论）时，年份等关键信息可能整体不进页面（实测缺 `2009/2015`） | 交付前人工核对"材料里最重要的 3 个信息是否都上了页面" |
| **GAP-B3** | 同上 | 结果页可能取到摘要、方法页取到局限——**内容错位但不报错** | 人工看页面；不要只看 `status` |
| **GAP-P1** | 多数据源 | 两张表只绑定第一张，第二张**静默忽略**（无 uncertainty） | 只把要用的表放进 `material[]`，或把它放第一位 |
| **GAP-P3** | 页数压缩 | `max_slides` 过紧时角色被裁掉，`change_records` 里没有记录 | 放宽上限；或在交付说明里人工写明合并了哪些页 |

**这些边界不会被 G1–G8 / 自检 / 契约门抓到**——它们只能靠
① 案例级判据（`case_check.py`）、② 人工看页面。这正是本包把两个案例与判据一起放进来的原因。

## 8. 增量编辑（多轮迭代与回退）

```bash
SKILL_DIR="${SKILL_DIR:-/skills/weekly-skill}"
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output \
    --edit edits.json --version v2
```

7 类 op：`update_bullet / add_bullet / remove_bullet / add_note / retitle /
reorder_pages / set_figure`（字段见 `examples/edit_demo.json`，决策树见 `references/EDIT_OPS.md`）。
每次改动写一条 `{version, op, page, target, reason}`；`deck_v2.pptx` 与 `deck.pptx` **并存**，
**回退 = 复制旧版本重跑**。
**编辑链路同样过 D2 数字核验**：实测用 `--edit` 塞入材料里没有的 `31.7%`，
该主张立刻进 `unverified_claims`（`missing_numbers=["31.7%"]`），
`change_records` 记下 `reason="探针：材料里没有 31.7%"`——**不因"是用户让改的"而放行**。

## 9. 完整命令索引（能力清单；含全部入口与开关）

| 入口 | 关键参数 | 用途 | 退出码 |
|-|-|-|-|
| `scripts/main.py` | `--case` `--out` `--input-dir` `--template` `--max-slides` `--edit` `--no-chart` `--version` `--draft` `--verbose` | 端到端主流程 | 0/1/2 |
| `scripts/result_tool.py` | `--result` `--out-dir` `--case` `--envelope` | 契约门 G1–G8 | 0/1/2 |
| `scripts/selftest.py` | `--out` `--case` `--pptx` `--slides` | 产物自检 | 0/1 |
| `scripts/evidence_check.py` | `--claim` `--material` | 单条主张数字核验 | 0/1 |
| `scripts/make_examples.py` | `--work-dir` `--dry-run` | 维护：重建 `examples/output/` 并净化绝对路径 | 0/1 |
| `scripts/deck_extract.py` | （库）由 `main.py` 编排 | 读实际材料 → `material_view.json` | — |
| `scripts/slide_text.py` | （库）由 `main.py` 编排 | 页序 / 角色 / 主张 / 备注文案 | — |
| `scripts/deck_tool.py` | （库）由 `main.py` 编排 | 图表四态绑定 + 模板槽位建稿 + 编辑 op | — |
| `scripts/render_qa.py` | （库）由 `main.py` 编排 | PIL PNG + reportlab PDF + 渲染 QA | — |
| `scripts/deck_common.py` | （库）被其余脚本 import | 路径自定位 / 原子写 / sha256 / 日志 / CJK 字体 | — |
| **`scripts/case_check.py`** | `--pkg` `--work` `--only` `--probes` `--probe-case` `--report-json` `--report-md` `--list` `--verbose` | **本版新增**：逐案实测 + 可接受区间判定 + 四种边界探针 | 0/1/2 |

## 10. 五维评分落点（速查；逐点展开见 `references/RUBRIC_MAP.md`）

| 维度 | 分 | 本包靠什么拿到 |
|-|-|-|
| 实际效果 | 40 | CP1–CP4 真跑；页序 + 页级角色；可编辑 PPTX + 备注 + 证据脚注；数字逐一核验；**两个题材各跑一次的实测结果**（`CASE-SET.md` §2） |
| 使用增益 | 25 | 页面纪律（每页一个角色、≤7 条、≤90 字、字号 ≥12pt）对标"整段塞页"；`--edit` 局部编辑 + 版本归档；**判据化验收**（不用人肉比对就知道这次有没有退步） |
| 创新增益 | 15 | 页序规划、证据绑定、图表四态绑定、局部编辑+回退；**新增：把"泛化"写成案例级可执行判据 + 四种边界探针，并如实给出 7 条失效边界** |
| 可靠体验 | 10 | D1–D12 + F1–F5 失败分支 + 非零退出码语义；**缺材料/无表/页数过紧/编辑引入新数字四种边界都有实测结论** |
| 生态贡献 | 10 | **本版主攻**：题集（两个题材 × 可接受区间）+ 判定台可扩展（§4 的四步加案例法）+ 判据写法小抄 + 两案的合成材料可直接当回归用例 |

GitHub 公开链接（额外 5 分）：见根目录 `GITHUB_URL.txt`。

## 11. 诚实边界

1. **两个案例都是合成材料**（虚构数据、虚构引用），**不是正式案例、不含正式答案**；
   `case.json` 里 `_note` 已逐条标注。
2. **案例只覆盖两个题材**（实验科学 / 理论文本），没覆盖医学统计、工程图纸、教学课件等形态。
3. **判定是结构 + 覆盖判据，不是质量判据**：能证明"页数对、角色在、备注全、没编造"，
   **不能证明"这一版讲得好"**。
4. **7 条失效边界仍在**（§7）：本版把它们测出来、写清楚、给规避做法，
   **没有修改核心算法**去根治；引用本包时不要声称"任意题材都能自动对齐"。
5. **预览 ≠ Office 导出**：无 PowerPoint/LibreOffice 时预览是 PIL/reportlab 近似渲染，
   文件名与 `previews.method` 均已如实标注。
6. **开发期工具**：`case_check.py` 跑 2 个案例约 5 秒、加探针约 12 秒，
   属开发期回归；不要放进平台 900 秒评测预算里跑。

---

# 附录 E–G：v1 / v2 / v3 的 README 与 TEST 正文 —— 原文逐字保留

> 为什么保留：这三个版本的 README/TEST 记录了各自的**实测过程和判据**
> （例如 v2 的对照复算步骤、v3 的探针负例控制），是 union 包的可溯源材料。
>
> **路径对照（正文里出现的旧文件名 → v6 中的位置）**：
>
> | 正文中的旧名 | v6 中的位置 |
> |-|-|
> | `references/DECK_SPEC.md` | `references/EDIT_OPS.md` 的下半部分（"附：页面蓝图与模板槽位"） |
> | `references/MECHANISM.md` | `references/MECHANISM-AND-ASSETS.md` 第一部分 |
> | `references/REUSABLE-ASSETS.md` | `references/MECHANISM-AND-ASSETS.md` 第二部分 |
> | `examples/README.md` | `examples/EXPECTED-OUTPUT.md` 的末节（"附：examples/ 目录说明"） |
>
> 其余文件名在 v6 中保持不变。

## 附录 E：v1（决策显性化版） README 正文（原文逐字保留）

本包把固定的科研材料（论文正文 / 数据表 / 任务说明）组织成**结构清楚、证据可追溯、
可编辑、符合模板约束**的学术汇报产物：可编辑 PPTX + 每页演讲备注 + 页级证据映射
（md/json 双形态）+ 渲染预览 + `result.json`，并支持**多轮局部编辑与版本回退**。

**这一版的重点不是多几个功能，而是"决策可查"**：主干流程被拆成 5 个阶段，
每个阶段后面都有裁决点；所有分叉写成规则 D1–D14（**触发条件 → 动作 →
失败时的降级去向**）与失败分支表 F1–F5；每条降级都必须落到具体记录字段上，
**没有记录就等于没执行降级**。

- 五维评分逐点落点与复核命令 → [`references/RUBRIC_MAP.md`](references/RUBRIC_MAP.md)
- `result.json` 字段契约与 G1–G8 硬性门 → [`references/OUTPUT_CONTRACT.md`](references/OUTPUT_CONTRACT.md)
- 失败模式逐族展开（与 §6 分支表编号对应）→ [`references/failure-modes.md`](references/failure-modes.md)
- 页面蓝图与模板槽位 → [`references/DECK_SPEC.md`](references/DECK_SPEC.md)
- 编辑操作目录与决策树 → [`references/EDIT_OPS.md`](references/EDIT_OPS.md)
- 本机实测记录（命令 / 退出码 / 产物 / 负路径） → [`TEST.md`](TEST.md)
- 最小示例与应产出清单 → [`examples/README.md`](examples/README.md)、[`examples/EXPECTED-OUTPUT.md`](examples/EXPECTED-OUTPUT.md)

## 1. 快速开始

`$SKILL_DIR` = **含 `SKILL.md` 的技能根目录**（平台评测容器里是 `/skills/weekly-skill`）。
所有命令都写成 `$SKILL_DIR/…`，所以 **cwd 不是技能根目录时同样能跑**；
脚本内部也用 `os.path.dirname(__file__)` 自定位。

```bash
SKILL_DIR="${SKILL_DIR:-/skills/weekly-skill}"     # 换成你的实际安装路径
OUT="${OUT:-/tmp/ppt-out}"                         # 输出目录（包外）

# ① 端到端：建稿 + 预览 + result.json + 证据映射 + manifest
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out "$OUT"

# ② 契约门 G1–G8（exit 0 = 通过；--case 必须传）
python "$SKILL_DIR/scripts/result_tool.py" --result "$OUT/result.json" \
    --out-dir "$OUT" --case "$SKILL_DIR/examples/case.json" \
    --envelope "$SKILL_DIR/templates/result_envelope.json"

# ③ 产物自检（all_pass=true 为通过）
python "$SKILL_DIR/scripts/selftest.py" --out "$OUT" --case "$SKILL_DIR/examples/case.json"

# ④ 局部编辑 + 版本归档
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
    --out "${OUT}-edit" --edit "$SKILL_DIR/examples/edit_demo.json" --version v2
```

平台运行形态：输入 `/input/case.json` + `/input/task.md`，产物写 `/app/output`：

```bash
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output
```

> ⚠ 步骤 ② 的 `--case` **必须传**，否则无法核对 `output_contract` 是否逐项回显
> （这是规则 D12 处理的那一类误判：先查参数，再怀疑实现）。

## 2. 五个阶段与五个裁决点

| 阶段 | 动作 | 裁决点 | 不通过时 |
|-|-|-|-|
| P1 抽取 | 读 case/task/全部材料，切章节、抓表、抓图表提及 | V1 材料是否有可读内容 | 走 D1 |
| P2 规划 | 角色分配 + 页序 + 页级主张与证据指针 | V2 `plan_lint` 是否 valid | 走 D4 / D7 |
| P3 建稿 | 模板槽位建稿 + 四态图表绑定 + 备注 + 脚注 | V3 deck 能否重开且页数=plan | 走 D6 / D9 |
| P4 渲染 | PIL 逐页 PNG + reportlab PDF + 渲染 QA | V4 是否至少 1 张 PNG | 走 D8 |
| P5 收口 | result.json + 双形态证据映射 + changelog + manifest | V5 契约门是否 `{"valid": true}` | 走 D10 / D12 |

规则表 D1–D14 与分支表 F1–F5 见 [`SKILL.md`](SKILL.md) §5/§6；
逐族展开（识别信号 → 处置 → 记录位置 → 用户可见后果）见
[`references/failure-modes.md`](references/failure-modes.md)。

## 3. 目录结构

```
SKILL.md                    # 技能本体：frontmatter + 阶段/裁决点 + D1–D14 + F1–F5 + 自查清单
README.md                   # 本文件：依赖/用法/目录/限制/维护
TEST.md                     # 本机真实实测记录（含负路径与退出码）
GITHUB_URL.txt              # 公开作品链接
scripts/                    # 四层职责 + 编排 + 维护（算法与 CLI 接口保持稳定）
  main.py                   # 编排：P1–P5 + 裁决点 + --edit 模式
  deck_extract.py           # extract：读实际材料（case/task/md/txt/html/csv/pdf）
  slide_text.py             # build：角色分配 + 页面文案骨架
  deck_tool.py              # build：模板槽位建稿 + 四态图表绑定 + 编辑操作
  render_qa.py              # render：PIL 预览 + reportlab PDF + 渲染 QA
  evidence_check.py         # verify：数字核验 + 证据脚注 + CP2 plan_lint
  result_tool.py            # verify：result 信封 + 双形态证据映射 + G1–G8
  selftest.py               # verify：端到端产物自检
  deck_common.py            # 公共：自定位/字体探测/哈希/原子写/日志
  make_examples.py          # 维护：真跑示例重建 examples/output 并净化机器路径
templates/
  default.json              # 默认模板 spec（颜色/字体/页脚/槽位，可参数化）
  result_envelope.json      # 结果信封声明（G8 依据）
references/
  OUTPUT_CONTRACT.md        # result.json 契约 + G1–G8 + 判读规则
  RUBRIC_MAP.md             # 五维评分（40/25/15/10/10）→ 文件与复核命令
  DECK_SPEC.md              # 页面蓝图 + 模板槽位约束
  EDIT_OPS.md               # 编辑操作目录 + 决策树
  failure-modes.md          # 失败模式 / 降级 / 契约四形态 / 状态一致性 / 退出码
examples/                   # 最小示例（虚构材料，标注"示例，非正式案例"）
  case.json / task.md / material.md / results.csv / edit_demo.json
  EXPECTED-OUTPUT.md        # 纯文字列出应产出的全部文件与契约字段
  output/                   # 一次真实运行的**文本**产物副本（.example. 命名）
```

**包体形态（平台硬约束）**：随包资源只有 UTF-8 文本
（`.md/.py/.json/.txt/.csv/.yaml/.yml`），**≤50 文件 / 单文件 ≤500KB / 合计 ≤2MB、
无符号链接、无二进制**（题面 Runtime contract 原文：*"at most 50 UTF-8 text files,
500KB each and 2MB total, no symlinks"*）。二进制产物（`deck.pptx`、预览 `*.png`、
预览 `*.pdf`）与 `changelog.jsonl` **不入包**，由运行时生成 —— 清单见
[`examples/EXPECTED-OUTPUT.md`](examples/EXPECTED-OUTPUT.md)。

## 4. 依赖

| 依赖 | 版本 | 用途 | 缺失时的行为 |
|-|-|-|-|
| python-pptx | >=0.6.21 | 可编辑 PPTX | **致命**：无法建稿，如实报 partial/failed（D6） |
| matplotlib | >=3.5 | 数据表重绘图表 | 降级 PPTX 原生可编辑表格（D9） |
| Pillow | >=9 | PNG 预览 | 预览缺 PNG → G5 报错、自检不过（D8） |
| numpy | 任意 | 图表 | 随 matplotlib |
| reportlab | 任意 | PDF 预览 | 跳过 PDF，记 warning（D8） |
| fitz / pypdf / pdfplumber | 任选其一 | PDF 材料抽取 | Agent 抽文本后重跑（D3） |

安装：`pip install python-pptx matplotlib pillow numpy reportlab`。
只装标准库也能跑到"材料读取 + 规划 + 元信息 result"的程度（状态降 partial）。

## 5. 输入格式（`case.json`）

```jsonc
{
  "case_id": "…",
  "title": "…",
  "inputs": {"task_md": "task.md", "material": ["paper.md", "results.csv"]},
  "spec": {
    "template": "default",            // 或 {"template_pptx": "…"} / {"starting_deck": "…"}
    "audience": "组会",               // 组会|答辩|评审|同行|基金 —— 影响讲稿语气
    "duration_minutes": 10,
    "max_slides": 6,                  // 3–20
    "style": {"colors": {"accent": "#2E7D32"}}   // 可选：覆盖模板任意键
  },
  "output_contract": {"deck": "dict", "previews": "dict", "is_example": "bool"}
}
```

材料路径相对 `case.json` 所在目录解析；缺失文件写入 `material_warnings` 而非静默
跳过（D1）。`output_contract` 声明的字段按**四形态**（`""/[]/{}/false/0`）镜像到
`result.json` 顶层，**禁 null**（D10）。

## 6. 命令索引与退出码

| 命令 | 作用 | 退出码 |
|-|-|-|
| `main.py --case C --out O` | 端到端（P1–P5） | 0=success / 1=partial / 2=输入不可读 |
| `--template <spec.json>` | 换模板 spec | — |
| `--input-dir <dir>` | `--case` 相对路径的基准目录 | — |
| `--max-slides N` | 覆盖页数上限（3–20） | — |
| `--edit <edits.json> --version v2` | 局部编辑 + 版本归档 | 同上（编辑失败降 partial） |
| `--no-chart` | 强制图表降级（对照试验） | — |
| `--draft` | 草稿模式（跳过 PDF 预览） | — |
| `--verbose` | 详细日志 | — |
| `result_tool.py --result R --out-dir O --case C --envelope E` | 契约门 G1–G8 | 0=通过 / 1=有未过项 / 2=result 不可读 |
| `selftest.py --out O --case C [--pptx P] [--slides N]` | 产物自检 | 0=全过 / 1=有未过项 |
| `evidence_check.py --claim "…" --material M` | 单条数字核验 | 0=全部找到 / 1=有缺失 |
| `make_examples.py [--dry-run]` | 重建示例文本产物 | 0 / 2=输入不可读 |

**编排器判读约定**：只有 exit 0 才算这次运行"干净"；exit 1 必须读
`result.json.uncertainty` 再决定是否补件重跑；exit 2 是输入侧问题，重跑无用。
完整分类见 [`references/failure-modes.md`](references/failure-modes.md) §0。

## 7. 输出与验收

- `work/deck.pptx`：可编辑演示文件（主张式标题 + 要点 + 图表槽 + 证据脚注 + 演讲备注）
- `work/plan.json`：页面模型（可编辑源）
- `work/preview/slide_*.png`、`work/preview/preview.pdf`、输出根 `preview/` 副本
- `result.json`：契约全字段 + `case_id` + `run_meta`（checkpoints / spec_lint / render_qa / gate）
- `evidence_map.md` + `evidence_map.json`：双形态同源页级证据映射
- `changelog.jsonl`、`manifest.json`（全部产物 sha256）、`logs/`

**验收判据**：`result_tool.py` → `{"valid": true}` 且 exit 0（G1–G8 全过）；
`selftest.py` → `all_pass=true`；PPTX 可被 python-pptx 重新打开且页数与 plan 一致；
每页有备注与证据脚注；`unverified_claims` 与 `uncertainty` 逐条可解释。

## 8. 限制与已知问题（诚实声明）

1. **预览 ≠ Office 导出**：无 PowerPoint/LibreOffice 时 PNG/PDF 由 PIL/reportlab
   按页面模型渲染，供肉眼检查；需要 Office 级 PDF 请在装有 Office 的机器上转换。
2. **CJK 字体**：预览依赖主机字体，按跨平台候选链探测（Windows `C:/Windows/Fonts`
   → macOS `/System/Library/Fonts` → Linux `/usr/share/fonts`）；找不到时预览出现
   方块但 **PPTX 不受影响**，事实写入 `previews.warnings`。包内**不含任何字体文件**。
3. **版式视觉微差**：PIL 预览与 PowerPoint 实际渲染有像素级差异；溢出防护按字符
   宽度估算，极端长词/高公式密度场景仍需人工微调。
4. **机器路径**：`deck.slides[].figure.image` 与 `sources[].path` 记录**本次运行机器**
   的实际路径（属产物不属包内容）；包内示例已由 `make_examples.py` 净化为相对路径。
5. **PDF 材料**：无抽取库时需 Agent 抽文本后重跑（D3）并在 `uncertainty` 记录方式。
6. **确定性**：同一输入、同一 spec、无 `--edit` 时结构确定；差异仅限时间戳与机器
   路径前缀（D13；双跑记录见 [`TEST.md`](TEST.md) §T6）。
7. **不适用**：论文综述/精读、可视化算法研发、文案润色、PPT 软件研发；SmartArt
   等智慧型占位符不重排；论文图是位图且无取数数据时**只占位不重绘**（D5）。

## 9. 失败处理（一页速查）

| 遇到什么 | 哪条规则 | 会看到什么 |
|-|-|-|
| 材料全缺 / 部分缺 | D1 | `material_warnings` 非空；`deck.slide_count=0`（全缺）；状态 partial |
| 页面数字材料里找不到 | D2 | `evidence.unverified_claims` 有该条，**不当作正确数据** |
| PDF 抽不出文本 | D3 | `uncertainty` 记抽取方式；仍不行则 partial |
| `plan_lint` 有偏差 | D4 | `run_meta.spec_lint.problems` 原文 + 状态 partial |
| 位图无数据 | D5 | `figure.kind=placeholder`（灰框占位），无凭空曲线 |
| 模板打不开 | D6 | `change_records` + `uncertainty` 记降级到内置模板 |
| 页数超限 | D7 | `spec_lint` 报超限；压缩后**不静默丢证据页** |
| 字体/PDF 渲染问题 | D8 | `previews.warnings`；PDF 可空但 PNG 仍在 |
| 图表重绘失败 | D9 | `figure.kind=table`（原生可编辑表格） |
| 契约字段缺值 | D10 | 顶层回显四形态空值，**无 null** |
| 编辑 op 非法 | D11 | `uncertainty` + `changelog` 的 skipped 记录，其余照常 |
| 复核说"契约没回显" | D12 | 先确认 `--case` 已传、字段确已声明 |
| 重复运行出现差异 | D13 | 判断是否仅时间戳/路径前缀 |
| 预算紧张 | D14 | 先落 partial，**逐条列出未完成项** |

## 10. 生态与复用

- **函数级可复用件**：`slide_text.alloc_roles`（角色分配）、
  `evidence_check.check_claim_numbers` / `plan_lint`（数字核验 + 页面纪律）、
  `deck_tool.build_chart`（表→图）、`deck_tool.apply_edits`（编辑操作）、
  `result_tool.validate`（G 门）。
- **模板与代码分离**：换配色/字体/页脚只改 `templates/*.json`；结果信封
  `templates/result_envelope.json` 可被任何验证器复用。
- **方法可迁移**：阶段+裁决点结构、D 规则表、失败分支表、双形态证据映射、
  编辑操作目录、版本记录格式、契约四形态回显 —— 可直接搬到其他
  "长材料 → 演示稿"的工具里。
- **示例即冒烟题集**：`examples/` 是最小上手输入，标注"示例，非正式案例"。

## 11. 维护

- 改脚本或文档后，按 [`TEST.md`](TEST.md) 的命令清单自测一遍；
- 改示例相关代码后跑 `python "$SKILL_DIR/scripts/make_examples.py"` 重建
  `examples/output/` 的文本副本（自动净化机器绝对路径）；
- 提交前自检包体：只允许的七种扩展名、≤50 文件、单文件 ≤500KB、合计 ≤2MB、
  无 `__pycache__`、无本机绝对路径。

## 附录 E：v1（决策显性化版） TEST 正文（原文逐字保留）

> 记录本包在**本机的真实执行结果**：命令、退出码、关键数值、产物清单。
> 全部命令都写成 `$SKILL_DIR/…` 形式并**在包外目录执行**（证明不依赖
> cwd = 技能根目录），输出一律写临时目录，**绝不在包内跑脚本**
> （否则生成 `scripts/__pycache__/`，验收器直接 FAIL）。
>
> 测试机：Windows 11 / Python 3.13.9；库实测版本：python-pptx 1.0.2 ·
> matplotlib 3.10.6 · Pillow 12.3.0 · reportlab 5.0.0 · numpy 可用；
> 无 LibreOffice —— 预览一律 PIL/reportlab 近似渲染并如实标注（`previews.method`）。

## T1 编译与导入 —— 通过

```bash
python -m py_compile "$SKILL_DIR"/scripts/*.py        # 10/10，exit 0
python -c "import sys; sys.path.insert(0,'$SKILL_DIR/scripts'); import deck_common, evidence_check, deck_extract, slide_text, deck_tool, render_qa, result_tool, selftest, make_examples, main; print('imports OK')"
# imports OK
```

## T2 冒烟：示例案例端到端（**验收主命令**）—— 通过（exit 0）

```bash
SKILL_DIR="<技能包绝对路径>"
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <临时输出目录>
```

末行与关键字段：

```
STATUS=success case_id=ppt-6ad93034-example-001 deck=work/deck.pptx slides=6
run_meta.checkpoints = {cp1_extract: true, cp2_plan: true, cp3_build: true, cp4_verify: true}
```

产物 25 个：`result.json`、`evidence_map.md`、`evidence_map.json`、`manifest.json`、
`changelog.jsonl`、`logs/run_*.log`、`work/deck.pptx`、`work/plan.json`、
`work/material_view.json`、`work/chart_results.csv.png`、`work/table_cache/results.csv`、
`work/preview/slide_01..06.png`、`work/preview/preview.pdf`、
`preview/slide_01..06.png`、`preview/preview.pdf`。

- 6 页角色依次 `cover / overview / question / method / result / takeaway`；
- 6/6 页有演讲备注（【讲解】【证据】【图表】）与证据脚注；
- 结果页 `figure.kind=chart_image`（重绘自 `results.csv`，note 标注重绘来源）；
- `evidence.unverified_claims` 为空；`run_meta.spec_lint = {"valid": true, "problems": [],
  "counts": {"pages": 6, "gaps": 1, "unverified": 0}}`（唯一 gap 是封面，规则允许）。

## T3 契约门与自检（独立复核命令）—— 均通过

```bash
python "$SKILL_DIR/scripts/result_tool.py" --result <out>/result.json --out-dir <out> \
    --case "$SKILL_DIR/examples/case.json" --envelope "$SKILL_DIR/templates/result_envelope.json"
# {"valid": true, "errors": [], "warnings": [], "gates": {G1..G8 全 true}}   exit 0

python "$SKILL_DIR/scripts/selftest.py" --out <out> --case "$SKILL_DIR/examples/case.json"
# all_pass: true（7/7）                                                        exit 0
```

契约覆盖核对：`OUTPUT_CONTRACT.md` §1 的 17 个顶层字段**全部在顶层**、缺项 0、
`null` 值 **0 个**；`deck` / `evidence` / `previews` 必备键缺项 0；
示例 `output_contract` 声明的 4 个字段按类型回显（`is_example` 为 **bool** `false`）。

`result.json` 顶层键（写出顺序）：
`case_id, title, status, created_at, skill_version, deck, evidence, previews, sources,
uncertainty, change_records, log, checks, evidence_map_json, manifest, environment,
is_example, run_meta`。

## T4 编辑模式 + 版本归档 —— 通过（exit 0）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <out-edit> \
    --edit "$SKILL_DIR/examples/edit_demo.json" --version v2      # exit 0
```

- `work/deck_v2.pptx` 与 `work/deck.pptx` **并存**（可回退），`work/plan.json` 同步更新；
- `changelog.jsonl` 记录 3 条 op（`update_bullet` / `add_note` / `reorder_pages`）；
- 编辑引入的文本同样过数字核验（"82.4% 对 81.1%" 可在材料中找到，D2/F6.4）。

## T5 页数变体（`--max-slides 10`）—— 通过（exit 0）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <out-10> --max-slides 10
# slides=10；角色：cover → overview → background → discussion → limitation
#              → question → method → result → result → takeaway
```

## T6 图表降级（`--no-chart`）—— 通过（exit 0）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <out-nc> --no-chart
```

结果页 `figure.kind=table`（降级为 **PPTX 原生可编辑表格**，note 说明重绘被关闭），
其余页 `figure.kind=none`；`status` 仍为 `success` —— 这是**已记录的受控降级**
而非失败（D9/F3.2；与 F5.1 的"有降级却标 success"区别在于：此处的降级由调用方
显式开关触发，且 `figure.note` 有对应说明）。

## T7 负路径（**本版重点**）：三族的真实降级记录

### T7a 材料缺失 → F1.1 —— 通过（exit 1）

```bash
# case 的 inputs.material 指向不存在的文件：["does-not-exist.md"]
python "$SKILL_DIR/scripts/main.py" --case <missing-case.json> --out <out-missing>
# STATUS=partial case_id=ppt-6ad93034-missing-001 deck= slides=0    exit 1
```

- `status=partial`、`deck.slide_count=0`：**不编造 deck**；
- `evidence.material_warnings` 如实列出缺失项（`输入缺失：does-not-exist.md（role=material-1）`）；
- `output_contract` 仍按四形态回显（`is_example=false`）；
- **未构建 `work/deck.pptx`** —— 这正是 D1 的判定点：材料缺失时宁可不出稿。

### T7b case.json 不可读 → F1.1 末列 —— 通过（exit 2）

```bash
python "$SKILL_DIR/scripts/main.py" --case <不存在的 case.json> --out <out-badcase>
# ERROR case load failed: 找不到 case 文件: …        exit 2
```

写出最小 `{"case_id":"unknown","status":"failed","error":"…","created_at":"…"}`，
**绝不假装成功**；exit 2 表示输入侧问题，重跑无用（§0 判读约定）。

### T7c 数字核验负例 → F1.4 / D2 —— 通过（exit 1）

```bash
python "$SKILL_DIR/scripts/evidence_check.py" --claim "S2-Attn 的 Q3 精度达到 82.4%" \
    --material "$SKILL_DIR/examples/material.md"        # ok=True  missing=[]      exit 0
python "$SKILL_DIR/scripts/evidence_check.py" --claim "某指标为 99.9%（材料中不存在）" \
    --material "$SKILL_DIR/examples/material.md"        # ok=False missing=['99.9%'] exit 1
```

**材料里没有的数字不放行**：`missing` 非空即 exit 1，且在完整流程中该主张会被
标成 `verified=false` 进 `unverified_claims`。

## T8 留出案例上的真实降级（F2.4 / D4 的活样本）

在**新写的一份留出材料**（多基准对照，8 页上限）上运行：

```bash
python "$SKILL_DIR/scripts/main.py" --case <holdout>/case.json --out <out-holdout>
# STATUS=partial   exit 1   slides=8
```

`run_meta.spec_lint` 原文：

```json
{"valid": false,
 "problems": ["page 6 bullet too long (chars=91, CJK-weighted=143 vs limit=90)"],
 "counts": {"pages": 8, "gaps": 1, "unverified": 0}}
```

`uncertainty` 对应一条 `CP2 plan lint 有偏差已记录（D4）: page 6 bullet too long …`。
这是**故意留下的真实记录**：越界 1 个字符也照样降级并留痕，而不是悄悄截断或改口径。
（契约门 `result_tool` 仍 `{"valid": true}` exit 0 —— 状态与门是两回事。）

## T9 确定性：同输入双跑 —— 内容级一致（如实记录）

| 比对对象 | 结果 |
|-|-|
| `work/deck.pptx` 内部部件（zip 条目按名排序后逐部件 sha256） | **64/64 一致**，差异部件 0 |
| `result.json`（剔除时间戳后逐叶比对） | 仅 1 处不同：`deck.slides[4].figure.image`（各自输出目录的图表路径） |
| `work/plan.json`（同上） | 仅 1 处不同：`pages[4].figure.image`（同一原因） |

结论：**内容确定**；原始字节差异只来自 zip 条目时间戳与机器路径前缀（D13）。

## 验收对照

| 验收项 | 结果 |
|-|-|
| 主命令在包外 cwd 执行且 exit 0 | ✅ `STATUS=success … slides=6`，25 个产物，裁决点 4/4 true |
| `result.json` 覆盖 `OUTPUT_CONTRACT.md` §1 全部字段 | ✅ 17/17 在顶层，0 缺项，0 个 `null` |
| 契约门与自检 | ✅ `{"valid": true}` exit 0；`all_pass=true` exit 0 |
| 编辑链路与版本归档 | ✅ `deck_v2.pptx` 与 `deck.pptx` 并存，changelog 有记录 |
| 页数变体 / 图表降级 | ✅ 10 页 / `table` 降级，均 exit 0 |
| 负路径三例（材料缺失 / case 不可读 / 数字缺失） | ✅ partial+1 / failed+2 / missing 非空+1 |
| 留出案例上的降级留痕 | ✅ `spec_lint.problems` 原文 + `uncertainty` 对应条目（T8） |
| 确定性双跑 | ✅ deck 逐部件 64/64 一致；result/plan 各仅 1 处机器路径差异 |
| 文档命令与脚本 `argparse` 逐字对应 | ✅ 全部文档命令均为 `"$SKILL_DIR/scripts/…"` 形式 |
| 包体形态 | ✅ 见下节 |

## 包体自检（提交前必跑）

```bash
# 1) 合规验收器：期望 PASS，0 条 FAIL
python <efficiency-3>/validate_pkg.py <本包目录>

# 2) 本机绝对路径残留检查（任意盘符 + 分隔符）
grep -rnE '[A-Za-z]:[\\/]{1,2}' <本包目录>
```

判读规则：
- **唯一允许的命中**是运行时字体探测的候选路径字符串（`scripts/deck_common.py`
  的 `_WIN_FONTS` 与 README §8 的说明）—— 它属于跨平台探测逻辑，不含任何
  "本机某次运行留下的痕迹"；除此之外不得有任何命中。
- 允许的扩展名只有 `.md/.py/.json/.txt/.csv/.yaml/.yml`；
- **二进制产物一律不入包**：`deck.pptx`、预览 `*.png`、预览 `*.pdf` 由运行时生成
  （清单见 `examples/EXPECTED-OUTPUT.md`）；`changelog.jsonl` 亦不入包；
- `examples/output/` 只放**文本**副本，且由 `scripts/make_examples.py` 自动把机器
  绝对路径净化成包内相对路径；
- `scripts/__pycache__/` 是运行时垃圾，提交前必须删除（否则验收器直接 FAIL）。

## 已知限制（本机验证结论）

- 预览是 PIL/reportlab 渲染，**不是** PowerPoint 导出件；需 Office 级 PDF 请在装有
  PowerPoint/LibreOffice 的机器上转换 `work/deck.pptx`。
- 预览使用主机字体（跨平台候选探测）；无 CJK 字体环境只影响预览，不影响 pptx，
  该事实写入 `previews.warnings`。
- 换行估算是字符宽度模型，极端长公式/高密度中文场景仍可能需人工微调（README §8）。
- `figure.image` 与 `sources[].path` 是**本次运行机器**的实际路径；跨机复跑前缀自然
  不同，内容不受影响（包内示例已由 `make_examples.py` 净化）。
- `case.json` 不可读时只写**最小** failed result（含 `case_id/status/error/created_at`），
  不满足完整契约字段 —— 这是 D1 的刻意取舍：输入侧失败优先"如实说明"而不是"凑字段"。
- 每次运行 <10 秒（本机实测约 2–3 秒），远低于 Runtime contract 的 900 秒预算。

---

## 附录 F：v2（增益可验证版） README 正文（原文逐字保留）

把固定的科研材料组织成**结构清楚、证据可追溯、可编辑、符合模板约束**的学术汇报产物：
可编辑 PPTX + 每页演讲备注 + 页级证据映射（md/json）+ 渲染预览 + `result.json`；
支持**多轮局部编辑与版本回退**。

**这一版的重点是"增益可验证"**：随包给出与"不加载 Skill 的基础 Agent"的
**公平对照协议**、五项质量与三项效率指标的精确公式、一个可复跑且**随包分发**的
测量脚本（[`references/measure_gain.py`](references/measure_gain.py)），以及在本机
**真实跑出来的对照记录**（含一条如实保留的负面指标）。

| 想找什么 | 去哪看 |
|-|-|
| 增益怎么算、怎么证伪、实测数字 | [`references/GAIN-PROTOCOL.md`](references/GAIN-PROTOCOL.md) ★本版核心 |
| 五维评分逐点落点与复核命令 | [`references/RUBRIC_MAP.md`](references/RUBRIC_MAP.md) |
| `result.json` 字段契约与 G1–G8 门 | [`references/OUTPUT_CONTRACT.md`](references/OUTPUT_CONTRACT.md) |
| 失败模式 / 降级 / 状态一致性 / 退出码 | [`references/failure-modes.md`](references/failure-modes.md) |
| 页面蓝图与模板槽位 | [`references/DECK_SPEC.md`](references/DECK_SPEC.md) |
| 编辑操作目录与决策树 | [`references/EDIT_OPS.md`](references/EDIT_OPS.md) |
| 本机实测记录（命令 / 退出码 / 负路径） | [`TEST.md`](TEST.md) |
| 最小示例与应产出清单 | [`examples/README.md`](examples/README.md)、[`examples/EXPECTED-OUTPUT.md`](examples/EXPECTED-OUTPUT.md) |

## 1. 快速开始

`$SKILL_DIR` = **含 `SKILL.md` 的技能根目录**（平台容器内为 `/skills/weekly-skill`）。
所有命令都写成 `$SKILL_DIR/…`，所以 **cwd 不是技能根目录也能跑**。

```bash
SKILL_DIR="${SKILL_DIR:-/skills/weekly-skill}"
OUT="${OUT:-/tmp/ppt-out}"

# ① 端到端：建稿 + 预览 + result.json + 证据映射 + manifest
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out "$OUT"

# ② 契约门（exit 0 = 通过；--case 必须传，否则无法核对契约回显）
python "$SKILL_DIR/scripts/result_tool.py" --result "$OUT/result.json" \
    --out-dir "$OUT" --case "$SKILL_DIR/examples/case.json" \
    --envelope "$SKILL_DIR/templates/result_envelope.json"

# ③ 产物自检（all_pass=true 为通过）
python "$SKILL_DIR/scripts/selftest.py" --out "$OUT" --case "$SKILL_DIR/examples/case.json"

# ④ 局部编辑 + 版本归档
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
    --out "${OUT}-edit" --edit "$SKILL_DIR/examples/edit_demo.json" --version v2
```

平台运行形态：输入 `/input/case.json` + `/input/task.md`，产物写 `/app/output`：

```bash
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output
```

## 2. 复跑"使用增益"对照（本版特有）

```bash
# 关键：在【包外】运行，避免在技能包里生成 __pycache__（平台预检会拒收整包）
cp "$SKILL_DIR/references/measure_gain.py" /tmp/
python /tmp/measure_gain.py --skill-dir "$SKILL_DIR" \
    --case "$SKILL_DIR/examples/case.json" \
    --case <你的第二个 case.json> \
    --work /tmp/gain-work --out /tmp/gain-report.json
```

报告含逐案例的 `quality`（Q1–Q6）、`diagnostics`、`efficiency`（E1–E3）与
`deltas`，以及两侧退出码；汇总在 `aggregate`。指标定义、公平条件、真实记录与
**证伪判据**见 [`references/GAIN-PROTOCOL.md`](references/GAIN-PROTOCOL.md)。

> 一句话口径：**两侧同一把尺子；"没做"的项按最差计；负面结果照原样报出。**
> 本包**不主张**"比基础 Agent 跑得快"（实测多出约 2–3 秒脚本开销，已如实列出）。

## 3. 目录结构

```
SKILL.md                    # 技能本体：frontmatter + 增益来源表 + CP1–CP4 + 对照要点 + 自查清单
README.md                   # 本文件：用法/对照复跑/目录/依赖/限制/维护
TEST.md                     # 本机真实实测记录（含负路径与对照复算入口）
GITHUB_URL.txt              # 公开作品链接
scripts/                    # 四层职责 + 编排 + 维护（算法与 CLI 接口保持稳定）
  main.py                   # 编排：CP1–CP4 + --edit 模式
  deck_extract.py           # extract：读实际材料（case/task/md/txt/html/csv/pdf）
  slide_text.py             # build：角色分配 + 页面文案骨架
  deck_tool.py              # build：模板槽位建稿 + 四态图表绑定 + 编辑操作
  render_qa.py              # render：PIL 预览 + reportlab PDF + 渲染 QA
  evidence_check.py         # verify：数字核验 + 证据脚注 + CP2 plan_lint
  result_tool.py            # verify：result 信封 + 双形态证据映射 + G1–G8
  selftest.py               # verify：端到端产物自检
  deck_common.py            # 公共：自定位/字体探测/哈希/原子写/日志
  make_examples.py          # 维护：真跑示例重建 examples/output 并净化机器路径
templates/
  default.json              # 默认模板 spec（参数化）
  result_envelope.json      # 结果信封声明（G8 依据）
references/
  OUTPUT_CONTRACT.md        # result.json 契约 + G1–G8 + 判读规则
  RUBRIC_MAP.md             # 五维评分（40/25/15/10/10）→ 文件与复核命令
  GAIN-PROTOCOL.md          # ★ 公平对照协议 + 指标公式 + 实测记录 + 证伪判据
  measure_gain.py           # ★ 随包测量脚本（两侧指标实现，包外运行）
  DECK_SPEC.md              # 页面蓝图 + 模板槽位约束
  EDIT_OPS.md               # 编辑操作目录 + 决策树
  failure-modes.md          # 失败模式 / 降级 / 契约四形态 / 状态一致性 / 退出码
examples/                   # 最小示例（虚构材料，标注"示例，非正式案例"）
  case.json / task.md / material.md / results.csv / edit_demo.json
  EXPECTED-OUTPUT.md        # 纯文字列出应产出的全部文件与契约字段
  output/                   # 一次真实运行的**文本**产物副本（.example. 命名）
```

**包体形态（平台硬约束）**：随包资源只有 UTF-8 文本
（`.md/.py/.json/.txt/.csv/.yaml/.yml`），**≤50 文件 / 单文件 ≤500KB / 合计 ≤2MB、
无符号链接、无二进制**（题面 Runtime contract 原文：*"at most 50 UTF-8 text files,
500KB each and 2MB total, no symlinks"*）。二进制产物（`deck.pptx`、预览 `*.png`/`*.pdf`）
与 `changelog.jsonl` **不入包**，由运行时生成。

## 4. 依赖

| 依赖 | 版本 | 用途 | 缺失时的行为 |
|-|-|-|-|
| python-pptx | >=0.6.21 | 可编辑 PPTX | **致命**：如实报 partial/failed |
| matplotlib | >=3.5 | 数据表重绘图表 | 降级 PPTX 原生可编辑表格（D9） |
| Pillow | >=9 | PNG 预览 | 预览缺 PNG → G5 报错、自检不过（D8） |
| numpy | 任意 | 图表 | 随 matplotlib |
| reportlab | 任意 | PDF 预览 | 跳过 PDF，记 warning（D8） |
| fitz / pypdf / pdfplumber | 任选其一 | PDF 材料抽取 | Agent 抽文本后重跑（D3） |

安装：`pip install python-pptx matplotlib pillow numpy reportlab`。
只装标准库也能跑到"材料读取 + 规划 + 元信息 result"的程度（状态降 partial）。

## 5. 输入格式（`case.json`）

```jsonc
{
  "case_id": "…",
  "title": "…",
  "inputs": {"task_md": "task.md", "material": ["paper.md", "results.csv"]},
  "spec": {
    "template": "default",            // 或 {"template_pptx": "…"} / {"starting_deck": "…"}
    "audience": "组会",               // 组会|答辩|评审|同行|基金 —— 影响讲稿语气
    "duration_minutes": 10,
    "max_slides": 6,                  // 3–20
    "style": {"colors": {"accent": "#2E7D32"}}
  },
  "output_contract": {"deck": "dict", "previews": "dict", "is_example": "bool"}
}
```

材料路径相对 `case.json` 所在目录解析；缺失文件写入 `material_warnings` 而非静默跳过。
`output_contract` 声明的字段按**四形态**（`""/[]/{}/false/0`）镜像到 `result.json` 顶层，**禁 null**。

## 6. 命令索引与退出码

| 命令 | 作用 | 退出码 |
|-|-|-|
| `main.py --case C --out O` | 端到端（CP1–CP4；也是对照的"条件 S"） | 0=success / 1=partial / 2=输入不可读 |
| `--template <spec.json>` | 换模板 spec | — |
| `--input-dir <dir>` | `--case` 相对路径的基准目录 | — |
| `--max-slides N` | 覆盖页数上限（3–20） | — |
| `--edit <edits.json> --version v2` | 局部编辑 + 版本归档 | 同上 |
| `--no-chart` | 强制图表降级（对照试验） | — |
| `--draft` | 草稿模式（跳过 PDF 预览） | — |
| `--verbose` | 详细日志 | — |
| `result_tool.py --result R --out-dir O --case C --envelope E` | 契约门 G1–G8 | 0=通过 / 1=有未过项 / 2=result 不可读 |
| `selftest.py --out O --case C [--pptx P] [--slides N]` | 产物自检 | 0=全过 / 1=有未过项 |
| `evidence_check.py --claim "…" --material M` | 单条数字核验 | 0=全部找到 / 1=有缺失 |
| `make_examples.py [--dry-run]` | 重建示例文本产物 | 0 / 2=输入不可读 |
| `references/measure_gain.py --skill-dir D --case C [--case C2] --work W --out R` | 公平对照测量（包外运行） | 0=测量完成 / 2=输入不可读 |

**编排器判读**：只有 exit 0 才算这次运行"干净"；exit 1 必须读
`result.json.uncertainty` 再决定是否补件重跑；exit 2 是输入侧问题，重跑无用。

## 7. 输出与验收

- `work/deck.pptx`：可编辑演示文件（主张式标题 + 要点 + 图表槽 + 证据脚注 + 演讲备注）
- `work/plan.json`：页面模型（可编辑源）
- `preview/slide_*.png`、`preview/preview.pdf`（+ `work/preview/` 同名副本）
- `result.json`：契约全字段 + `case_id` + `run_meta`（checkpoints / spec_lint / render_qa / gate）
- `evidence_map.md` + `evidence_map.json`：双形态同源页级证据映射
- `changelog.jsonl`、`manifest.json`（全部产物 sha256）、`logs/`

**验收判据**：`result_tool.py` → `{"valid": true}` 且 exit 0（G1–G8 全过）；
`selftest.py` → `all_pass=true`；PPTX 可被 python-pptx 重新打开且页数与 plan 一致；
每页有备注与证据脚注；`unverified_claims` 与 `uncertainty` 逐条可解释。

## 8. 限制与已知问题（诚实声明）

1. **对照的性质**：本包给的是**受控脚本级对照**（基线 = 题面点名失败清单的确定性
   代理实现），不是平台官方的 Agent 级对照；`GAIN-PROTOCOL.md` 的范围声明与 §7 局限
   逐条写明，结论只在声明范围内成立。
2. **预览 ≠ Office 导出**：无 PowerPoint/LibreOffice 时 PNG/PDF 由 PIL/reportlab 渲染；
   需要 Office 级 PDF 请在装有 Office 的机器上转换 `work/deck.pptx`。
3. **CJK 字体**：预览依赖主机字体，按跨平台候选链探测（Windows `C:/Windows/Fonts`
   → macOS `/System/Library/Fonts` → Linux `/usr/share/fonts`）；找不到时预览出现方块但
   **PPTX 不受影响**，事实写入 `previews.warnings`。包内**不含任何字体文件**。
4. **版式视觉微差**：PIL 预览与 PowerPoint 实际渲染有像素级差异；溢出防护按字符宽度
   估算，极端长词/高公式密度场景仍需人工微调。
5. **机器路径**：`deck.slides[].figure.image` 与 `sources[].path` 记录**本次运行机器**的
   实际路径（属产物不属包内容）；包内示例已由 `make_examples.py` 净化为相对路径。
6. **PDF 材料**：无抽取库时需 Agent 抽文本后重跑（D3）并在 `uncertainty` 记录方式。
7. **确定性**：同一输入、同一 spec、无 `--edit` 时结构确定，差异仅限时间戳与机器路径
   前缀 —— 这正是"逐页 diff 公平"的前提。
8. **不适用**：论文综述/精读、可视化算法研发、文案润色、PPT 软件研发；SmartArt 等
   智慧型占位符不重排；论文图是位图且无取数数据时**只占位不重绘**。

## 9. 失败处理（一页速查）

| 遇到什么 | 规则 | 会看到什么 |
|-|-|-|
| 材料全缺 / 部分缺 | D1 | `material_warnings` 非空；全缺时 `deck.slide_count=0` |
| 页面数字材料里找不到 | D2 | `unverified_claims` 有该条，**不当作正确数据** |
| PDF 抽不出文本 | D3 | `uncertainty` 记抽取方式；仍不行则 partial |
| `plan_lint` 有偏差 | D4 | `run_meta.spec_lint.problems` 原文 + 状态 partial |
| 位图无数据 | D5 | `figure.kind=placeholder`（灰框占位） |
| 模板打不开 | D6 | `change_records` + `uncertainty` 记降级 |
| 页数超限 | D7 | 压缩后**不静默丢证据页** |
| 字体/PDF 渲染问题 | D8 | `previews.warnings`；PDF 可空但 PNG 仍在 |
| 图表重绘失败 | D9 | `figure.kind=table`（原生可编辑表格） |
| 契约字段缺值 | D10 | 顶层四形态空值，**无 null** |
| 编辑 op 非法 | D11 | `uncertainty` + `changelog` skipped，其余照常 |
| 复核说"契约没回显" | D12 | 先确认 `--case` 已传、字段确已声明 |
| 重复运行出现差异 | D13 | 判断是否仅时间戳/路径前缀 |
| 预算紧张 | D14 | 先落 partial，**逐条列出未完成项** |

## 10. 生态与复用

- **函数级可复用件**：`slide_text.alloc_roles`、`evidence_check.check_claim_numbers` /
  `plan_lint`、`deck_tool.build_chart`、`deck_tool.apply_edits`、`result_tool.validate`。
- **测量台可复用**：`references/measure_gain.py` 的四个指标函数只依赖
  `result.json` 与产物目录，**任何"材料 → 结构化工件"的 Skill 都能改用同一口径自证增益**。
- **模板与代码分离**：换配色/字体/页脚只改 `templates/*.json`；结果信封可被任何验证器复用。
- **方法可迁移**：公平条件清单、指标公式、证伪判据、双形态证据映射、编辑操作目录、
  契约四形态回显 —— 可直接搬到其他"长材料 → 演示稿"的工具里。

## 11. 维护

- 改脚本或文档后，按 [`TEST.md`](TEST.md) 的命令清单自测一遍；
- 改示例相关代码后跑 `python "$SKILL_DIR/scripts/make_examples.py"` 重建
  `examples/output/` 的文本副本（自动净化机器绝对路径）；
- 改了衡量口径或流程后，**同步更新 `GAIN-PROTOCOL.md` 的实测表**（重跑测量脚本），
  不要把旧数字留在文档里；
- 提交前自检包体：只允许的七种扩展名、≤50 文件、单文件 ≤500KB、合计 ≤2MB、
  无 `__pycache__`、无本机绝对路径。

## 附录 F：v2（增益可验证版） TEST 正文（原文逐字保留）

> 全部命令写成 `$SKILL_DIR/…` 形式并**在包外目录执行**（证明不依赖
> cwd = 技能根目录），输出一律写临时目录。**绝不在包内跑脚本** ——
> 包内运行会生成 `scripts/__pycache__/`，验收器直接 FAIL；对照测量脚本同理，
> 请先复制到包外再跑。
>
> 测试机：Windows 11 / Python 3.13.9；库实测版本：python-pptx 1.0.2 ·
> matplotlib 3.10.6 · Pillow 12.3.0 · reportlab 5.0.0 · numpy 可用；
> 无 LibreOffice —— 预览一律 PIL/reportlab 近似渲染并如实标注。

## T1 编译与导入 —— 通过

```bash
python -m py_compile "$SKILL_DIR"/scripts/*.py        # 10/10，exit 0
python -c "import sys; sys.path.insert(0,'$SKILL_DIR/scripts'); import deck_common, evidence_check, deck_extract, slide_text, deck_tool, render_qa, result_tool, selftest, make_examples, main; print('imports OK')"
# imports OK
```

## T2 冒烟：示例案例端到端（**验收主命令**，也是对照的"条件 S"）—— exit 0

```bash
SKILL_DIR="<技能包绝对路径>"
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <临时输出目录>
```

```
STATUS=success case_id=ppt-6ad93034-example-001 deck=work/deck.pptx slides=6
run_meta.checkpoints = {cp1_extract: true, cp2_plan: true, cp3_build: true, cp4_verify: true}
```

产物 25 个：`result.json`、`evidence_map.md/json`、`manifest.json`、`changelog.jsonl`、
`logs/run_*.log`、`work/deck.pptx`、`work/plan.json`、`work/material_view.json`、
`work/chart_results.csv.png`、`work/table_cache/results.csv`、
`work/preview/slide_01..06.png`、`work/preview/preview.pdf`、
`preview/slide_01..06.png`、`preview/preview.pdf`。

逐页结构（**Q1/Q4/Q5 的判定面**，实测）：

| 页 | role | claims | notes | evidence_footer |
|-|-|-|-|-|
| 1 | cover | 0 | 1 | ✅ |
| 2 | overview | 2 | 2 | ✅ |
| 3 | question | 2 | 1 | ✅ |
| 4 | method | 4 | 1 | ✅ |
| 5 | result | 3 | 1 | ✅ |
| 6 | takeaway | 2 | 2 | ✅ |

⇒ Q1 = 6/6 = 1.0；Q4 = 1.0；Q5 = 1.0；`evidence.unverified_claims` 为空。

## T3 契约门与自检 —— 均通过（exit 0）

```bash
python "$SKILL_DIR/scripts/result_tool.py" --result <out>/result.json --out-dir <out> \
    --case "$SKILL_DIR/examples/case.json" --envelope "$SKILL_DIR/templates/result_envelope.json"
# {"valid": true, "errors": [], "warnings": [], "gates": {G1..G8 全 true}}   exit 0

python "$SKILL_DIR/scripts/selftest.py" --out <out> --case "$SKILL_DIR/examples/case.json"
# all_pass: true（7/7）                                                        exit 0
```

契约覆盖：`OUTPUT_CONTRACT.md` §1 的 17 个顶层字段全部在顶层、缺项 0、`null` **0 个**；
`deck`/`evidence`/`previews` 必备键缺项 0；示例 `output_contract` 的 4 个字段按类型回显。

## T4 编辑模式 + 版本归档 —— 通过（exit 0）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <out-edit> \
    --edit "$SKILL_DIR/examples/edit_demo.json" --version v2      # exit 0
```

`work/deck_v2.pptx` 与 `work/deck.pptx` 并存；`changelog.jsonl` 记录 3 条 op；
编辑引入的文本同样过数字核验（"82.4% 对 81.1%" 可在材料中找到）。

**对"增益"的意义**：E1 编辑粒度实测为 `local_op_with_version_archive`、
E2 版本归档 ≥1 —— 对照协议里 B 侧这两项恒为 0（整稿重生成）。

## T5 页数变体（`--max-slides 10`）—— 通过（exit 0）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <out-10> --max-slides 10
# slides=10；cover → overview → background → discussion → limitation
#            → question → method → result → result → takeaway
```

## T6 图表降级（`--no-chart`）—— 通过（exit 0）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <out-nc> --no-chart
```

结果页 `figure.kind=table`（原生可编辑表格），`status` 仍 `success`。
**这一条是"对照条件可控"的证据**：开关存在，两个条件才能真正对齐。

## T7 负路径 —— 状态与退出码自洽

### T7a 材料缺失（D1）

```bash
python "$SKILL_DIR/scripts/main.py" --case <missing-case.json> --out <out-missing>
# STATUS=partial case_id=ppt-6ad93034-missing-001 deck= slides=0     exit 1
```

- `deck.slide_count=0`：**不编造 deck**；`work/deck.pptx` 不存在；
- `evidence.material_warnings` 列出缺失项（`输入缺失：does-not-exist.md（role=material-1）`）；
- `output_contract` 仍按四形态回显（`is_example=false`）。

### T7b case.json 不可读（D1 末列）

```bash
python "$SKILL_DIR/scripts/main.py" --case <不存在的 case.json> --out <out-badcase>
# ERROR case load failed: 找不到 case 文件: …                        exit 2
```

写出最小 `{"case_id":"unknown","status":"failed","error":"…","created_at":"…"}`。

### T7c 数字核验负例（D2）

```bash
python "$SKILL_DIR/scripts/evidence_check.py" --claim "S2-Attn 的 Q3 精度达到 82.4%" \
    --material "$SKILL_DIR/examples/material.md"        # ok=True  missing=[]       exit 0
python "$SKILL_DIR/scripts/evidence_check.py" --claim "某指标为 99.9%（材料中不存在）" \
    --material "$SKILL_DIR/examples/material.md"        # ok=False missing=['99.9%'] exit 1
```

## T8 ★ 公平对照：本机真实测量（本版核心实测）

**测量条件**：同一解释器、同一库版本、两侧同一测量脚本、两个案例
（包内示例 + 一个为对照新写的 8 页留出案例）。**在包外运行测量脚本**：

```bash
cp "$SKILL_DIR/references/measure_gain.py" <tmp>/
python <tmp>/measure_gain.py --skill-dir "$SKILL_DIR" \
    --case "$SKILL_DIR/examples/case.json" --case <holdout>/case.json \
    --work <tmp>/work --out <tmp>/gain-report.json
```

**汇总（进入结论的 5 项）**

| 指标 | B 均值 | S 均值 | Δ |
|-|-|-|-|
| Q1 页级角色覆盖率 | 0.0000 | 1.0000 | **+1.0000** |
| Q3 数字主张可追溯率 | 0.0000 | 1.0000 | **+1.0000** |
| Q4 演讲备注覆盖率 | 0.0000 | 1.0000 | **+1.0000** |
| Q5 证据脚注覆盖率 | 0.0000 | 1.0000 | **+1.0000** |
| Q6 可复核产物齐全度 | 0.1429 | 1.0000 | **+0.8571** |

**逐案例细节**

| 项 | 案例 A（示例，6 页） | 案例 B（留出，8 页） |
|-|-|-|
| 条件 S 状态 / 退出码 | `success` / 0 | **`partial` / 1** |
| 条件 S 数字主张 | 6 条，全部带证据指针 | 8 条，全部带证据指针 |
| 条件 S `unverified_claims` | 0 | 0 |
| 条件 S 正文字号集合 | {15, 17} pt（自适应收缩） | {15, 17} pt |
| 条件 S `uncertainty` 条数 | 0 | **1**（第 6 页主张 91 字，越界 1 字，D4 记录） |
| 条件 S 预览工件 | 7（6 PNG + 1 PDF） | 9（8 PNG + 1 PDF） |
| 条件 S 脚本耗时 | 2.303 s | 2.837 s |
| 条件 B 脚本耗时 | 0.370 s | 0.021 s |
| Q2（**仅报出，不进结论**） | B 1.0 / S 1.0 | B 1.0 / **S 0.875** |

**必须一起读的两条**：① 案例 B 的 S 侧是 `partial`（越界 1 字也照样降级留痕，
没有为了让对照好看而放宽纪律）；② Q2 在 S 侧更低、在 B 侧"意外合规"，
故**不作为对照依据**（理由见 `GAIN-PROTOCOL.md` §3.3）——这条负面结果被原样保留。

**总耗时对比（如实列出，属成本）**：B 合计 0.391 s，S 合计 5.14 s，差 +4.75 s；
相对 Runtime contract 的 900 秒预算占比 <1%。**本包不主张"更快"。**

## T9 对照协议的资格检查（结论成立的前置条件）

| 前置条件 | 本机状态 |
|-|-|
| 两侧同一 `case.json` / `task.md` / 材料 | ✅ 由测量脚本传入同一路径 |
| 两侧同一 `spec.max_slides` / 模板 | ✅ 均从同一 `case.json` 读取 |
| 两侧同一解释器与库版本 | ✅ 同一 `python`（报告记录版本） |
| 两侧同一测量脚本与归一化口径 | ✅ `references/measure_gain.py` |
| 两侧都不使用 `--edit` | ✅ 均为基础命令 |
| 结论可证伪 | ✅ `GAIN-PROTOCOL.md` §5 给出 5 条证伪条件与复核命令 |

## T10 确定性：同输入双跑 —— 内容级一致

| 比对对象 | 结果 |
|-|-|
| `work/deck.pptx` 逐部件 sha256（zip 条目按名排序） | **64/64 一致**，差异 0 |
| `result.json`（剔除时间戳后逐叶比对） | 仅 1 处：`deck.slides[4].figure.image`（各自输出目录路径） |
| `work/plan.json`（同上） | 仅 1 处：`pages[4].figure.image` |

⇒ **逐页 diff 公平**：同一 case、同一 spec、无 `--edit` 时结构确定，
差异只在时间戳与机器路径前缀。

## 验收对照

| 验收项 | 结果 |
|-|-|
| 主命令在包外 cwd 执行且 exit 0 | ✅ `slides=6`、25 产物、checkpoints 4/4 true |
| 契约字段覆盖与 `null` 检查 | ✅ 17/17 顶层、0 缺项、0 个 `null` |
| 契约门与自检 | ✅ `{"valid": true}` exit 0；`all_pass=true` exit 0 |
| 编辑链路与版本归档 | ✅ `deck_v2.pptx` 与 `deck.pptx` 并存，changelog 有记录 |
| 页数变体 / 图表降级 | ✅ 10 页 / `table` 降级，均 exit 0 |
| 负路径三例 | ✅ partial+1 / failed+2 / missing 非空+1 |
| **公平对照可复跑** | ✅ 测量脚本随包；两案例 10 项指标全部由产物算出，报告留档 |
| 对照结论可证伪 | ✅ 5 条证伪条件 + 复核命令 |
| 确定性双跑 | ✅ deck 64/64 一致；result/plan 各仅 1 处机器路径差异 |
| 包体形态 | ✅ 见下节 |

## 包体自检（提交前必跑）

```bash
python <efficiency-3>/validate_pkg.py <本包目录>          # 期望 PASS，0 FAIL
grep -rnE '[A-Za-z]:[\\/]{1,2}' <本包目录>                # 期望只命中字体探测候选路径
```

判读规则：
- **唯一允许的命中**是运行时字体探测候选路径（`scripts/deck_common.py` 的
  `_WIN_FONTS` 与 README §8 的说明）；除此之外不得有任何命中。
- 允许的扩展名只有 `.md/.py/.json/.txt/.csv/.yaml/.yml`；`references/measure_gain.py`
  也是文本 `.py`，符合白名单。
- **二进制产物一律不入包**（`deck.pptx`、预览 PNG/PDF、`changelog.jsonl`）。
- `scripts/__pycache__/` 提交前必须删除；**测量脚本不要在包内运行**。

## 已知限制（本机验证结论）

- 对照是**受控脚本级**对照：条件 B 是题面点名失败形态的确定性代理实现，
  不是平台官方的 Agent 级对照；平台对照由平台生成（`GAIN-PROTOCOL.md` §7）。
- 样本仅 2 例（平台为 3 固定案例 × 3 次重复），本表不能替代那 9 次运行。
- 未测量真实人工返工小时数，只给可记录的代理量（E1/E2/E3）。
- 预览是 PIL/reportlab 渲染，**不是** PowerPoint 导出件；无 CJK 字体只影响预览。
- 换行估算为字符宽度模型，极端长公式/高密度中文场景仍可能需人工微调。
- `figure.image` 与 `sources[].path` 是**本次运行机器**的实际路径；跨机复跑前缀自然不同。
- `case.json` 不可读时只写**最小** failed result（不满足完整契约字段）—— D1 的刻意取舍。
- 每次运行 <10 秒（本机约 2–3 秒），远低于 900 秒预算。

---

## 附录 G：v3（机制与复用显性化版） README 正文（原文逐字保留）

把固定的科研材料组织成**结构清楚、证据可追溯、可编辑、符合模板约束**的学术汇报产物：
可编辑 PPTX + 每页演讲备注 + 页级证据映射（md/json）+ 渲染预览 + `result.json`；
支持**多轮局部编辑与版本回退**。

**这一版做两件事**：
① **把机制写成可证伪的判据** —— 五个机制 M1–M5，每个都说清"**缺了会怎样**"，
并配一条能在产物里查的痕迹；随包探针 [`references/mechanism_probe.py`](references/mechanism_probe.py)
只读产物、会在机制痕迹被破坏时报 FAIL（负例控制见 [`references/MECHANISM.md`](references/MECHANISM.md) §5）。
② **把可复用的东西交出去** —— 九个可独立拿走的资产（契约+信封、判据探针、对照测量台、
页面骨架与角色词表、编辑操作目录、模板参数、数字核验器、示例冒烟题集、契约与状态规范），
清单与复用命令见 [`references/REUSABLE-ASSETS.md`](references/REUSABLE-ASSETS.md)。

| 想找什么 | 去哪看 |
|-|-|
| 五个机制、"缺了会怎样"、判据 | [`references/MECHANISM.md`](references/MECHANISM.md) ★本版核心 |
| 能拿走的资产与复用命令 | [`references/REUSABLE-ASSETS.md`](references/REUSABLE-ASSETS.md) ★本版核心 |
| 公平对照协议、指标公式、实测记录 | [`references/GAIN-PROTOCOL.md`](references/GAIN-PROTOCOL.md) |
| 五维评分逐点落点 | [`references/RUBRIC_MAP.md`](references/RUBRIC_MAP.md) |
| `result.json` 契约与 G1–G8 门 | [`references/OUTPUT_CONTRACT.md`](references/OUTPUT_CONTRACT.md) |
| 失败模式 / 降级 / 状态一致性 / 退出码 | [`references/failure-modes.md`](references/failure-modes.md) |
| 页面蓝图与模板槽位 | [`references/DECK_SPEC.md`](references/DECK_SPEC.md) |
| 编辑操作目录与决策树 | [`references/EDIT_OPS.md`](references/EDIT_OPS.md) |
| 本机实测记录（命令 / 退出码 / 负路径 / 探针） | [`TEST.md`](TEST.md) |
| 最小示例与应产出清单 | [`examples/README.md`](examples/README.md)、[`examples/EXPECTED-OUTPUT.md`](examples/EXPECTED-OUTPUT.md) |

## 1. 快速开始

`$SKILL_DIR` = **含 `SKILL.md` 的技能根目录**（平台容器内为 `/skills/weekly-skill`）。
所有命令都写成 `$SKILL_DIR/…`，因此 **cwd 不是技能根目录也能跑**。

```bash
SKILL_DIR="${SKILL_DIR:-/skills/weekly-skill}"
OUT="${OUT:-/tmp/ppt-out}"

# ① 端到端：建稿 + 预览 + result.json + 证据映射 + manifest
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out "$OUT"

# ② 契约门（exit 0 = 通过；--case 必须传，否则无法核对契约回显）
python "$SKILL_DIR/scripts/result_tool.py" --result "$OUT/result.json" \
    --out-dir "$OUT" --case "$SKILL_DIR/examples/case.json" \
    --envelope "$SKILL_DIR/templates/result_envelope.json"

# ③ 产物自检（all_pass=true 为通过）
python "$SKILL_DIR/scripts/selftest.py" --out "$OUT" --case "$SKILL_DIR/examples/case.json"

# ④ 机制判据探针（M1–M5，期望 5/5 PASS、exit 0）
python "$SKILL_DIR/references/mechanism_probe.py" --out "$OUT"

# ⑤ 局部编辑 + 版本归档
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
    --out "${OUT}-edit" --edit "$SKILL_DIR/examples/edit_demo.json" --version v2
```

平台运行形态：输入 `/input/case.json` + `/input/task.md`，产物写 `/app/output`：

```bash
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output
```

> ⚠ **两条自我约束**：① 绝不在技能包目录里运行任何脚本（会生成 `scripts/__pycache__/`，
> 平台预检直接拒收整包）；② 步骤 ② 的 `--case` 必须传。

## 2. 五个机制（一句话版）

| # | 机制 | 缺了会怎样 | 判据 / 复核 |
|-|-|-|-|
| M1 | 页面单元化与角色确定性（`alloc_roles`） | 退化成"一页一段"的文本流，页数由段落数决定、页间无分工 | 每页 `role` 非空，`slide_count` = 页数 |
| M2 | 主张—证据锚定（`check_claim_numbers`） | 数字与原文之间失去可查的连线，抄错发现不了 | 每条数字主张有 `evidence`；`unverified_claims` 有解释 |
| M3 | 图表四态绑定（`bind_figures`） | 位图无数据时要么丢信息，要么"凭空生成曲线" | `chart_image` 的图片与表文件都在；无数据只 `placeholder` |
| M4 | 版本与可复核链（`apply_edits` + changelog + manifest） | 只有一个 deck、改动无记录、交付字节无法对拍 | deck 可重开且页数一致；多版本并存；changelog/manifest 在 |
| M5 | 契约四形态 + 三层验证（`apply_output_contract` + G1–G8） | 字段 `null` 让下游崩；未核验数字也标 success | 顶层无 `null`；契约字段逐项回显；`{"valid": true}` |

展开（实现位置、产物退化形态、证伪条件、负例控制）见
[`references/MECHANISM.md`](references/MECHANISM.md)。

## 3. 目录结构

```
SKILL.md                    # 技能本体：frontmatter + 机制表 + CP1–CP4 + 工具三件 + 自查清单
README.md                   # 本文件：机制速览/用法/可复用资产/目录/依赖/限制/维护
TEST.md                     # 本机真实实测记录（含探针实测与负例控制）
GITHUB_URL.txt              # 公开作品链接
scripts/                    # 四层职责 + 编排 + 维护（算法与 CLI 接口保持稳定）
  main.py                   # 编排：CP1–CP4 + --edit 模式
  deck_extract.py           # extract：读实际材料（case/task/md/txt/html/csv/pdf）
  slide_text.py             # build：角色分配（M1）+ 页面文案骨架
  deck_tool.py              # build：模板槽位建稿 + 四态图表绑定（M3）+ 编辑操作（M4）
  render_qa.py              # render：PIL 预览 + reportlab PDF + 渲染 QA
  evidence_check.py         # verify：数字核验（M2）+ 证据脚注 + CP2 plan_lint
  result_tool.py            # verify：result 信封 + 双形态证据映射 + G1–G8（M5）
  selftest.py               # verify：端到端产物自检
  deck_common.py            # 公共：自定位/字体探测/哈希/原子写/日志
  make_examples.py          # 维护：真跑示例重建 examples/output 并净化机器路径
templates/
  default.json              # 默认模板 spec（参数化，可直接拿走复用）
  result_envelope.json      # 结果信封声明（G8 依据，可直接拿走复用）
references/
  OUTPUT_CONTRACT.md        # result.json 契约 + G1–G8 + 判读规则
  RUBRIC_MAP.md             # 五维评分（40/25/15/10/10）→ 文件与复核命令
  MECHANISM.md              # ★ 五个机制 + "缺了会怎样" + 判据 + 负例控制
  REUSABLE-ASSETS.md        # ★ 九个可复用资产 + 复用命令 + 移植步骤 + 边界
  GAIN-PROTOCOL.md          # 公平对照协议 + 指标公式 + 实测记录 + 证伪判据
  mechanism_probe.py        # ★ 机制判据探针（只读产物；包外运行）
  measure_gain.py           # ★ 对照测量台（两侧指标实现；包外运行）
  DECK_SPEC.md              # 页面蓝图 + 模板槽位约束
  EDIT_OPS.md               # 编辑操作目录 + 决策树
  failure-modes.md          # 失败模式 / 降级 / 契约四形态 / 状态一致性 / 退出码
examples/                   # 最小示例（虚构材料，标注"示例，非正式案例"）
  case.json / task.md / material.md / results.csv / edit_demo.json
  EXPECTED-OUTPUT.md        # 纯文字列出应产出的全部文件与契约字段
  output/                   # 一次真实运行的**文本**产物副本（.example. 命名）
```

**包体形态（平台硬约束）**：随包资源只有 UTF-8 文本
（`.md/.py/.json/.txt/.csv/.yaml/.yml`），**≤50 文件 / 单文件 ≤500KB / 合计 ≤2MB、
无符号链接、无二进制**（题面 Runtime contract 原文：*"at most 50 UTF-8 text files,
500KB each and 2MB total, no symlinks"*）。二进制产物（`deck.pptx`、预览 `*.png`/`*.pdf`）
与 `changelog.jsonl` **不入包**，由运行时生成。

## 4. 可复用资产（九个，详见 `references/REUSABLE-ASSETS.md`）

| # | 资产 | 拿走它能干什么 |
|-|-|-|
| A1 | `templates/result_envelope.json` + `references/OUTPUT_CONTRACT.md` | 给任何产出 `result.json` 的工具当校验依据 |
| A2 | `references/mechanism_probe.py` | 对任意一次运行的产物做 M1–M5 痕迹检查（**最独立**） |
| A3 | `references/measure_gain.py` | 对任何"材料 → 结构化工件"的 Skill 做同口径对照测量 |
| A4 | `scripts/slide_text.py` 的 `ROLE_LABELS` / `alloc_roles` | 把"材料结构 → 页面角色"的取舍规则搬走 |
| A5 | `references/EDIT_OPS.md` + `apply_edits` | 局部改稿 + 版本归档的 op 词表与决策树 |
| A6 | `templates/default.json` + `--template` | 换配色/字体/页脚**不改代码** |
| A7 | `scripts/evidence_check.py`（CLI/函数） | 任何"页面/报告 vs 原文"的数字一致性检查 |
| A8 | `examples/` + `EXPECTED-OUTPUT.md` | 新实现的接口冒烟与产物清单对拍 |
| A9 | `references/failure-modes.md` §4/§5/§6 | 契约四形态表与状态一致性表，可直接当规范引用 |

## 5. 依赖

| 依赖 | 版本 | 用途 | 缺失时的行为 |
|-|-|-|-|
| python-pptx | >=0.6.21 | 可编辑 PPTX；M4 探针重开检查 | **致命**：如实报 partial/failed |
| matplotlib | >=3.5 | 数据表重绘图表（M3 的 `chart_image`） | 降级 PPTX 原生可编辑表格（D9） |
| Pillow | >=9 | PNG 预览 | 预览缺 PNG → G5 报错、自检不过（D8） |
| numpy | 任意 | 图表 | 随 matplotlib |
| reportlab | 任意 | PDF 预览 | 跳过 PDF，记 warning（D8） |
| fitz / pypdf / pdfplumber | 任选其一 | PDF 材料抽取 | Agent 抽文本后重跑（D3） |

安装：`pip install python-pptx matplotlib pillow numpy reportlab`。
**探针与测量台只依赖标准库**（探针的 pptx 重开检查在缺 python-pptx 时如实报 FAIL，
不会假装通过）。

## 6. 输入格式（`case.json`）

```jsonc
{
  "case_id": "…",
  "title": "…",
  "inputs": {"task_md": "task.md", "material": ["paper.md", "results.csv"]},
  "spec": {
    "template": "default",            // 或 {"template_pptx": "…"} / {"starting_deck": "…"}
    "audience": "组会",               // 组会|答辩|评审|同行|基金 —— 影响讲稿语气
    "duration_minutes": 10,
    "max_slides": 6,                  // 3–20
    "style": {"colors": {"accent": "#2E7D32"}}
  },
  "output_contract": {"deck": "dict", "previews": "dict", "is_example": "bool"}
}
```

材料路径相对 `case.json` 所在目录解析；缺失文件写入 `material_warnings` 而非静默跳过。
`output_contract` 声明的字段按**四形态**（`""/[]/{}/false/0`）镜像到 `result.json` 顶层，**禁 null**。

## 7. 命令索引与退出码

| 命令 | 作用 | 退出码 |
|-|-|-|
| `main.py --case C --out O` | 端到端（CP1–CP4） | 0=success / 1=partial / 2=输入不可读 |
| `--template <spec.json>` | 换模板 spec（A6） | — |
| `--input-dir <dir>` | `--case` 相对路径的基准目录 | — |
| `--max-slides N` | 覆盖页数上限（3–20） | — |
| `--edit <edits.json> --version v2` | 局部编辑 + 版本归档（M4） | 同上 |
| `--no-chart` | 强制图表降级（M3 的 `table` 态） | — |
| `--draft` | 草稿模式（跳过 PDF 预览） | — |
| `--verbose` | 详细日志 | — |
| `result_tool.py --result R --out-dir O --case C --envelope E` | 契约门 G1–G8（M5） | 0=通过 / 1=有未过项 / 2=result 不可读 |
| `selftest.py --out O --case C [--pptx P] [--slides N]` | 产物自检 | 0=全过 / 1=有未过项 |
| `evidence_check.py --claim "…" --material M` | 单条数字核验（M2） | 0=全部找到 / 1=有缺失 |
| `make_examples.py [--dry-run]` | 重建示例文本产物 | 0 / 2=输入不可读 |
| `references/mechanism_probe.py --out O` | 机制判据 M1–M5（包外运行） | 0=5/5 通过 / 1=有 FAIL / 2=输入不可读 |
| `references/measure_gain.py --skill-dir D --case C …` | 对照测量（包外运行） | 0=完成 / 2=输入不可读 |

## 8. 输出与验收

- `work/deck.pptx`（可编辑）、`work/plan.json`（页面模型）
- `preview/slide_*.png`、`preview/preview.pdf`（+ `work/preview/` 同名副本）
- `result.json`（契约全字段 + `run_meta`）、`evidence_map.md/json`（双形态）
- `changelog.jsonl`、`manifest.json`（全部产物 sha256）、`logs/`

**验收判据**：`result_tool.py` → `{"valid": true}` 且 exit 0（G1–G8 全过）；
`selftest.py` → `all_pass=true`；**机制探针 5/5 PASS**；PPTX 可被 python-pptx 重新打开
且页数与 plan 一致；每页有备注与证据脚注；`unverified_claims` 与 `uncertainty` 逐条可解释。

## 9. 限制与已知问题（诚实声明）

1. **判据是必要条件**：探针 PASS 只说明"机制痕迹在"，不说明"这一版讲得好"。
2. **对照的性质**：`measure_gain.py` 给的是受控脚本级对照（基线 = 题面点名失败形态的
   确定性代理实现），平台官方的 Agent 级对照由平台生成；范围声明与局限见
   `references/GAIN-PROTOCOL.md`。
3. **预览 ≠ Office 导出**：无 PowerPoint/LibreOffice 时 PNG/PDF 由 PIL/reportlab 渲染；
   需要 Office 级 PDF 请在装有 Office 的机器上转换 `work/deck.pptx`。
4. **CJK 字体**：预览依赖主机字体，按跨平台候选链探测（Windows `C:/Windows/Fonts`
   → macOS `/System/Library/Fonts` → Linux `/usr/share/fonts`）；找不到时预览出现方块但
   **PPTX 不受影响**，事实写入 `previews.warnings`。包内**不含任何字体文件**。
5. **版式视觉微差**：PIL 预览与 PowerPoint 实际渲染有像素级差异；溢出防护按字符宽度
   估算，极端长词/高公式密度场景仍需人工微调。
6. **机器路径**：`deck.slides[].figure.image` 与 `sources[].path` 记录**本次运行机器**的
   实际路径（属产物不属包内容）；包内示例已由 `make_examples.py` 净化为相对路径。
7. **PDF 材料**：无抽取库时需 Agent 抽文本后重跑（D3）并在 `uncertainty` 记录方式。
8. **不适用**：论文综述/精读、可视化算法研发、文案润色、PPT 软件研发；SmartArt 等
   智慧型占位符不重排；论文图是位图且无取数数据时**只占位不重绘**。

## 10. 失败处理（一页速查）

| 遇到什么 | 规则 | 会看到什么 |
|-|-|-|
| 材料全缺 / 部分缺 | D1 | `material_warnings` 非空；全缺时 `deck.slide_count=0` |
| 页面数字材料里找不到 | D2 | `unverified_claims` 有该条，**不当作正确数据** |
| PDF 抽不出文本 | D3 | `uncertainty` 记抽取方式；仍不行则 partial |
| `plan_lint` 有偏差 | D4 | `run_meta.spec_lint.problems` 原文 + 状态 partial |
| 位图无数据 | D5 | `figure.kind=placeholder`（灰框占位，M3 的合法交付态） |
| 模板打不开 | D6 | `change_records` + `uncertainty` 记降级 |
| 页数超限 | D7 | 压缩后**不静默丢证据页** |
| 字体/PDF 渲染问题 | D8 | `previews.warnings`；PDF 可空但 PNG 仍在 |
| 图表重绘失败 | D9 | `figure.kind=table`（原生可编辑表格） |
| 契约字段缺值 | D10 | 顶层四形态空值，**无 null** |
| 编辑 op 非法 | D11 | `uncertainty` + `changelog` skipped，其余照常 |
| 复核说"契约没回显" | D12 | 先确认 `--case` 已传、字段确已声明 |
| 重复运行出现差异 | D13 | 判断是否仅时间戳/路径前缀 |
| 预算紧张 | D14 | 先落 partial，**逐条列出未完成项** |

## 11. 维护

- 改脚本或文档后，按 [`TEST.md`](TEST.md) 的命令清单自测一遍（含探针）；
- 改示例相关代码后跑 `python "$SKILL_DIR/scripts/make_examples.py"` 重建
  `examples/output/` 的文本副本（自动净化机器绝对路径）；
- 改了机制实现或判据后，**同步更新 `references/MECHANISM.md` 的判据表与实测行**，
  并重跑探针（含负例控制），不要把旧数字留在文档里；
- 提交前自检包体：只允许的七种扩展名、≤50 文件、单文件 ≤500KB、合计 ≤2MB、
  无 `__pycache__`、无本机绝对路径。

## 附录 G：v3（机制与复用显性化版） TEST 正文（原文逐字保留）

> 记录本包在**本机的真实执行结果**：命令、退出码、关键数值、产物清单。
> 全部命令写成 `$SKILL_DIR/…` 形式并**在包外目录执行**（证明不依赖
> cwd = 技能根目录），输出一律写临时目录。**绝不在包内跑脚本** ——
> 包内运行会生成 `scripts/__pycache__/`，验收器直接 FAIL；随包的探针与测量台
> 同样必须在**包外**运行。
>
> 测试机：Windows 11 / Python 3.13.9；库实测版本：python-pptx 1.0.2 ·
> matplotlib 3.10.6 · Pillow 12.3.0 · reportlab 5.0.0 · numpy 可用；
> 无 LibreOffice —— 预览一律 PIL/reportlab 近似渲染并如实标注。

## T1 编译与导入 —— 通过

```bash
python -m py_compile "$SKILL_DIR"/scripts/*.py        # 10/10，exit 0
python -c "import sys; sys.path.insert(0,'$SKILL_DIR/scripts'); import deck_common, evidence_check, deck_extract, slide_text, deck_tool, render_qa, result_tool, selftest, make_examples, main; print('imports OK')"
# imports OK
# 随包工具（在包外跑）：py_compile / import 均通过
python -m py_compile "$SKILL_DIR"/references/mechanism_probe.py "$SKILL_DIR"/references/measure_gain.py
```

## T2 冒烟：示例案例端到端（**验收主命令**）—— exit 0

```bash
SKILL_DIR="<技能包绝对路径>"
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <临时输出目录>
```

```
STATUS=success case_id=ppt-6ad93034-example-001 deck=work/deck.pptx slides=6
run_meta.checkpoints = {cp1_extract: true, cp2_plan: true, cp3_build: true, cp4_verify: true}
```

产物 25 个：`result.json`、`evidence_map.md/json`、`manifest.json`、`changelog.jsonl`、
`logs/run_*.log`、`work/deck.pptx`、`work/plan.json`、`work/material_view.json`、
`work/chart_results.csv.png`、`work/table_cache/results.csv`、
`work/preview/slide_01..06.png`、`work/preview/preview.pdf`、
`preview/slide_01..06.png`、`preview/preview.pdf`。

## T3 契约门与自检 —— 均通过（exit 0）

```bash
python "$SKILL_DIR/scripts/result_tool.py" --result <out>/result.json --out-dir <out> \
    --case "$SKILL_DIR/examples/case.json" --envelope "$SKILL_DIR/templates/result_envelope.json"
# {"valid": true, "errors": [], "warnings": [], "gates": {G1..G8 全 true}}   exit 0

python "$SKILL_DIR/scripts/selftest.py" --out <out> --case "$SKILL_DIR/examples/case.json"
# all_pass: true（7/7）                                                        exit 0
```

契约覆盖：`OUTPUT_CONTRACT.md` §1 的 17 个顶层字段全部在顶层、缺项 0、`null` **0 个**；
`deck`/`evidence`/`previews` 必备键缺项 0；示例 `output_contract` 的 4 个字段按类型回显。

## T4 ★ 机制判据探针实测（本版核心实测）

```bash
cp "$SKILL_DIR/references/mechanism_probe.py" <tmp>/     # 包外运行
python <tmp>/mechanism_probe.py --out <示例案例输出> --out <留出案例输出>
```

**真实运行上的判据结果**：

| 输出 | 状态 | M1 页单元 | M2 证据锚定 | M3 图表四态 | M4 版本链 | M5 契约 | 退出码 |
|-|-|-|-|-|-|-|-|
| 示例案例（6 页） | `success` | PASS | PASS | PASS | PASS | PASS | 0 |
| 留出案例（8 页） | `partial` | PASS | PASS | PASS | PASS | PASS | 0 |

**关键计数（由探针从产物算出）**：

| 项 | 示例案例 | 留出案例 |
|-|-|-|
| `M2.counts.numeric_claims` | 6 | 8 |
| `M2.counts.numeric_claims_with_evidence` | 6 | 8 |
| `M2.counts.unverified_claims` | 0 | 0 |
| `M3.kind_counts` | `{chart_image: 1, none: 5}` | `{chart_image: 1, none: 7}` |
| `M4.deck_versions` | `['deck.pptx']` | `['deck.pptx']` |
| 顶层 `null` 字段 | 0 | 0 |

## T5 ★ 探针负例控制（证明判据不是"恒真"）

把一次真实运行的输出复制一份，人为破坏三处机制痕迹：
① 清空第 1 页 `role`（打 M1）；② 把第 5 页 `figure.image` 指向不存在的文件（打 M3）；
③ 在顶层加一个值为 `null` 的字段（打 M5）。重跑探针：

```
== negctl  status=success
   M1_page_units      FAIL ['page 1 缺少 role']
   M2_anchors         PASS
   M3_figure_states   FAIL ["page 5 标为 chart_image 但图片文件不存在: 'work/does-not-exist.png'"]
   M4_versioning      PASS
   M5_contract        FAIL ['顶层存在 null 字段: [...]']
```

退出码 **1**。⇒ 探针**具备区分能力**：机制痕迹被破坏时会 FAIL；
未被破坏的 M2/M4 仍 PASS，说明它**只报真实缺陷**。

## T6 编辑模式 + 版本归档（M4 的用户面）—— 通过（exit 0）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <out-edit> \
    --edit "$SKILL_DIR/examples/edit_demo.json" --version v2      # exit 0
```

- `work/deck_v2.pptx` 与 `work/deck.pptx` **并存**（可回退），`work/plan.json` 同步更新；
- `changelog.jsonl` 记录 3 条 op（`update_bullet` / `add_note` / `reorder_pages`）；
- 编辑引入的文本同样过数字核验（"82.4% 对 81.1%" 可在材料中找到）—— **M2 在编辑链路上仍然生效**。

## T7 页数变体（`--max-slides 10`）—— 通过（exit 0）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <out-10> --max-slides 10
# slides=10；cover → overview → background → discussion → limitation
#            → question → method → result → result → takeaway
```

## T8 图表降级（`--no-chart`）—— 通过（exit 0）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <out-nc> --no-chart
```

结果页 `figure.kind=table`（原生可编辑表格），`status` 仍 `success`。
**探针口径**：`table` 是词表内的合法态，所以 `M3_figure_states` 仍 PASS ——
M3 判的是"**不许出现无数据来源的图**"，不是"必须有 `chart_image`"。

## T9 负路径（状态与退出码自洽）

### T9a 材料缺失（D1）

```bash
python "$SKILL_DIR/scripts/main.py" --case <missing-case.json> --out <out-missing>
# STATUS=partial case_id=ppt-6ad93034-missing-001 deck= slides=0     exit 1
```

- `deck.slide_count=0`：**不编造 deck**（`work/deck.pptx` 不存在）；
- `evidence.material_warnings` 列出缺失项；
- **探针在此场景下 M1 会 FAIL**（没有 slides）—— 这是**如实反映**而非缺陷，
  解释在 `references/failure-modes.md` §1 的对照表里。

### T9b case.json 不可读（D1 末列）

```bash
python "$SKILL_DIR/scripts/main.py" --case <不存在的 case.json> --out <out-badcase>
# ERROR case load failed: 找不到 case 文件: …                        exit 2
```

写出最小 `{"case_id":"unknown","status":"failed","error":"…","created_at":"…"}`。

### T9c 数字核验负例（D2 / M2）

```bash
python "$SKILL_DIR/scripts/evidence_check.py" --claim "S2-Attn 的 Q3 精度达到 82.4%" \
    --material "$SKILL_DIR/examples/material.md"        # ok=True  missing=[]       exit 0
python "$SKILL_DIR/scripts/evidence_check.py" --claim "某指标为 99.9%（材料中不存在）" \
    --material "$SKILL_DIR/examples/material.md"        # ok=False missing=['99.9%'] exit 1
```

## T10 公平对照（复算入口，协议见 `references/GAIN-PROTOCOL.md`）

```bash
cp "$SKILL_DIR/references/measure_gain.py" <tmp>/
python <tmp>/measure_gain.py --skill-dir "$SKILL_DIR" \
    --case "$SKILL_DIR/examples/case.json" --case <holdout>/case.json \
    --work <tmp>/work --out <tmp>/gain-report.json
```

实测汇总（两侧同一脚本、同一口径）：Q1/Q3/Q4/Q5 均由 0.0000 提升到 1.0000，
Q6 由 0.1429 提升到 1.0000；脚本耗时 0.391 s → 5.14 s（**如实报为成本**）。
其中留出案例的 S 侧状态为 `partial`（一条 91 字主张越界 1 字符，按 D4 记录降级），
**没有为了让对照好看而放宽纪律**；另有一条负面指标（单条长度合规率）原样保留在
协议文档 §3.3 中并说明为何不作为对照依据。

## T11 确定性：同输入双跑 —— 内容级一致

| 比对对象 | 结果 |
|-|-|
| `work/deck.pptx` 逐部件 sha256（zip 条目按名排序） | **64/64 一致**，差异 0 |
| `result.json`（剔除时间戳后逐叶比对） | 仅 1 处：`deck.slides[4].figure.image`（各自输出目录路径） |
| `work/plan.json`（同上） | 仅 1 处：`pages[4].figure.image` |

⇒ **复核与逐页 diff 是公平的**：同输入同 spec 无 `--edit` 时结构确定，
差异只在时间戳与机器路径前缀。

## 验收对照

| 验收项 | 结果 |
|-|-|
| 主命令在包外 cwd 执行且 exit 0 | ✅ `slides=6`、25 产物、checkpoints 4/4 true |
| 契约字段覆盖与 `null` 检查 | ✅ 17/17 顶层、0 缺项、0 个 `null` |
| 契约门与自检 | ✅ `{"valid": true}` exit 0；`all_pass=true` exit 0 |
| **机制判据 M1–M5** | ✅ 两个真实输出 5/5 PASS；负例控制 3 条 FAIL（证明有区分能力） |
| 编辑链路与版本归档 | ✅ `deck_v2.pptx` 与 `deck.pptx` 并存，changelog 有记录 |
| 页数变体 / 图表降级 | ✅ 10 页 / `table` 降级（M3 仍 PASS），均 exit 0 |
| 负路径三例 | ✅ partial+1 / failed+2 / missing 非空+1 |
| 公平对照可复跑 | ✅ 测量台随包；10 项指标全部由产物算出 |
| 确定性双跑 | ✅ deck 64/64 一致；result/plan 各仅 1 处机器路径差异 |
| 包体形态 | ✅ 见下节 |

## 包体自检（提交前必跑）

```bash
python <efficiency-3>/validate_pkg.py <本包目录>          # 期望 PASS，0 FAIL
grep -rnE '[A-Za-z]:[\\/]{1,2}' <本包目录>                # 期望只命中字体探测候选路径
```

判读规则：
- **唯一允许的命中**是运行时字体探测候选路径（`scripts/deck_common.py` 的
  `_WIN_FONTS` 与 README §9 的说明）；除此之外不得有任何命中。
- 允许的扩展名只有 `.md/.py/.json/.txt/.csv/.yaml/.yml`；
  `references/mechanism_probe.py`、`references/measure_gain.py` 均为文本 `.py`，符合白名单。
- **二进制产物一律不入包**（`deck.pptx`、预览 PNG/PDF、`changelog.jsonl`）；
  探针写出的 `mechanism-probe-report.json` 也**不要**放进包里（它写在运行时工作目录）。
- `scripts/__pycache__/` 提交前必须删除；**两个随包脚本都不要在包内运行**。

## 已知限制（本机验证结论）

- **判据是必要条件**：探针 PASS 只说明"机制痕迹在"，不说明"这一版讲得好"；
  内容质量由 `evidence_check` 与人工复核负责。
- 对照是**受控脚本级**对照（基线 = 题面点名失败形态的确定性代理实现），
  不是平台官方的 Agent 级对照；范围声明与局限见 `references/GAIN-PROTOCOL.md`。
- 探针的 M5 在**没有 `case.json`** 时退化为"顶层不得有 null"，
  无法核对 `output_contract` 声明字段是否逐项回显（那需要 case 文件）。
- 预览是 PIL/reportlab 渲染，**不是** PowerPoint 导出件；无 CJK 字体只影响预览。
- 换行估算为字符宽度模型，极端长公式/高密度中文场景仍可能需人工微调。
- `figure.image` 与 `sources[].path` 是**本次运行机器**的实际路径；跨机复跑前缀自然不同。
- `case.json` 不可读时只写**最小** failed result（不满足完整契约字段）—— D1 的刻意取舍。
- 每次运行 <10 秒（本机约 2–3 秒），远低于 900 秒预算。

---

