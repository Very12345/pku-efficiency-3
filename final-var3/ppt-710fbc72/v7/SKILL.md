---
name: academic-slide-adapt
description: >-
  Academic slide deck creation from research material with real template
  adaptation (学术 PPT 模板与格式适配), shipped with a runnable byte-reproducibility
  probe and a per-field stability map: scripts/determinism.py drives the real
  pipeline N times across separate OS processes, three different working
  directories, four PYTHONHASHSEED values and relative-vs-absolute argument
  forms, hashes every produced file, and reports which JSON field paths differ
  and whether each one is a declared wall-clock stamp, a declared host anchor
  (the run's own cwd / out dir / case dir), or an undeclared defect. Use when
  the task says "make an academic presentation / 学术PPT / 学术汇报 / 论文转PPT /
  adapt this paper into slides / 套模板 / 模板适配 / 按模板生成PPT / deck from
  paper", when a starting deck must be re-edited on its own template, or when a
  reviewer asks "if I run this again, do I get the same deck".
---

# Academic Slide Adapter（学术 PPT 模板与格式适配）— 确定性与字节级可复现

做学术汇报 PPT，并且**证明它可复现**：同一份输入、同一份模板，无论跑在哪个
进程、哪个工作目录、哪个 `PYTHONHASHSEED` 下，可编辑 `.pptx` 与两张预览图都是
**逐字节相同**的；唯一会变的字段被**逐条列名、逐条给出理由**，而不是一句
"因为我们写了时间戳"。

- Skill 版本：`2.0.0`（两阶段工作流 + CP1–CP3 门，与基线同源）
- **Skill 根 = 本文件所在目录**；下文所有 `$SKILL_DIR` 都指它。脚本用
  `os.path.dirname(__file__)` 自定位，命令在**任意 cwd** 下都能跑。
- 核心入口：`$SKILL_DIR/scripts/main.py`（一条命令完成两阶段全流程）
- **本轴入口**：`$SKILL_DIR/scripts/determinism.py`（16 次受控重跑 + 字段级归因）
- **资源形态**：只含 UTF-8 文本（`.md/.py/.json/.txt`），≤50 个、单文件
  ≤500KB、合计 ≤2MB、无符号链接；模板/图片/预览一律**运行时生成**。

**执行顺序**：
**① 读 `references/OUTPUT_CONTRACT.md`（交付什么、G1–G8 门）** →
**② 跑一次正式流程（`main.py`）** → **③ 跑 `determinism.py` 拿复现性证据** →
**④ 按 `references/DETERMINISM.md` 逐条核对"易变字段清单"** →
**⑤ 按 `references/RUBRIC_MAP.md` 五维自评**。

---

## 1. 本轴要回答的两个问题

| 问题 | 谁回答 | 判据 |
|-|-|-|
| **同一输入重跑，产物是否一样？** | `scripts/determinism.py` | 二进制交付物 **L1**（原始字节）全条件一致；JSON 记录在 **L4** 后收敛为单一值 |
| **不一样的那些字段，是谁、为什么？** | `references/DETERMINISM.md` §3–§5 | 每个差异字段都落在四张声明表之一；**声明表外差异 = 0 条** |

这两问缺一不可。只给"一致"会掩盖被删掉的字段；只给"字段清单"又没法判好坏。
所以本包把两者做成一个可执行实验：**跑 → 测 → 归因 → 逐条列名**。

## 2. 一条命令（正式流程）

```bash
SKILL_DIR=<本包根目录>          # 平台装到 /skills/weekly-skill
python "$SKILL_DIR/scripts/main.py" --case <case.json> [--task <task.md>] \
    [--work <材料基目录>] [--template <模板.pptx>] \
    [--starting-deck <deck.pptx>] --out <输出目录>
```

平台正式运行时：

```bash
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md \
    --work /app/work --out /app/output
```

## 3. 一条命令（复现性实验）

```bash
RUN=<包外可写目录>              # 必须包外：包内跑会留下 __pycache__/*.pyc
python "$SKILL_DIR/scripts/determinism.py" --skill "$SKILL_DIR" --run "$RUN" \
    --runs 3 --json "$RUN/determinism_report.json" --markdown "$RUN/determinism.md"
# exit 0 = 二进制交付物 L1 一致 + 全部 JSON 记录在 L4 后收敛 + 声明表外差异 0 条
```

脚本自己会拒绝把 `--run` 放进包里（除非显式 `--allow-in-package`），因为
`__pycache__`/`.pyc` 是题面资源契约明确拒收的类型。

**五个受控条件（这是本轴的实验设计，不是顺手多跑几次）**：

| 条件 | 变了什么 | 专门抓什么缺陷 |
|-|-|-|
| `c1` | 同 cwd、同 env，3 个**独立进程** | 进程内状态、时钟、临时文件名 |
| `c2` | 停 1.2 s 后再跑 3 次 | 是否只对时序/jitter 敏感 |
| `c3` | cwd 换成 1 层嵌套 / 2 层嵌套 / 脚手架根 | 记录里混进了调用者自己的目录 |
| `c4` | `PYTHONHASHSEED` = 0 / 1 / 12345 / 未设置 | `set`/`dict` 迭代顺序泄进产物 |
| `c5` | 相对参数 vs 绝对参数（同一 cwd 显式启动） | 参数形态改变了记录内容 |

## 4. 判据：四层一致性（L1–L4）

| 层 | 做法 | 谁应该通过 |
|-|-|-|
| **L1 原始** | 直接比 sha256 | 不含时间戳、不含宿主路径的产物：`.pptx`、两张 `.png`、`summary.txt`、`_runtime/builtin.pptx` |
| **L2 去时间戳** | 去掉 `NONDETERMINISM` 表里的字段 | 还不够：路径记录仍在（见 L3） |
| **L3 归锚点** | 再把"调用者目录 / 输出目录 / 用例目录"替换成 `<CWD>/<OUT>/<CASEDIR>` 记号 | `spec.json`、`adopt_plan.json`、`content.json`、`render_log.json` |
| **L4 再去派生摘要** | 最后把**锚点文件的 sha256** 换成 `<DERIVED>` 记号 | 全部 JSON：`audit.json`、`result.json` 也在此层收敛为单一值 |

**为什么要 L4**：`result.json.artifacts[].checks.sha256` 是 `spec.json` 的摘要，
而 `spec.json` 里带着锚点路径。摘要**不可能**在锚点变化时保持不变——它不是
"不确定"，是**级联**。把已知原因替换成记号后再比，问的才是真问题：
**除了列出来的原因，还有没有别的东西在变？** 答案是 0 条。

### 实测数字（本机 python 3.13.9，16 次运行，全部 exit 0、status=success）

- 产物 12 个/次；**6 个文件 L1 逐字节一致（16/16 次）**：
  `deck.pptx`、`cover_preview.png`、`slides_contact_schematic.png`、
  `_runtime/builtin.pptx`、`summary.txt`、`_PREVIEW_ARE_SCHEMATIC.txt`
- `make_template.py` 单独在两处不同 cwd 各跑一次：**sha256 相同**
  （`f75fa66e4ebf88d1…`）
- 全部 6 个 JSON 记录在 **L4 后收敛为单一值**（各自唯一值数 = 1）
- **声明表外出现差异的字段：0 条**；逐字段归因共 41 条，分布：
  宿主锚定 34 · 锚点派生摘要 6 · 时间戳 1
- 单次流程耗时 1.36–1.69 s（16 次合计 24.4 s）

完整逐字段表见 **`references/DETERMINISM.md`**（由实测报告渲染，非手抄）。

## 5. 四张声明表（"故意不稳定"的白名单）

`scripts/determinism.py` 顶部把"允许不一样的字段"写成四张**精确**表，表外出现
差异就是失败：

| 表 | 含义 | 本包实测条数 |
|-|-|-|
| `NONDETERMINISM` | 墙钟戳、解释器/依赖版本 | 1 |
| `HOST_ANCHOR` | 值 = 运行发生**在哪里**的函数（调用者 cwd、输出目录、用例目录、宿主字体集） | 34 |
| `INVOCATION_FORM` | 同一次运行内稳定，但"给了相对路径"与"给了绝对路径"两种调用形态之间不同 | 4 类 |
| `DERIVED_FROM_ANCHORED` | **锚点记录的摘要**（sha256）或引用运行期模板路径的说明文字 | 6 |

**为什么这些字段不能直接删掉**：
`references/OUTPUT_CONTRACT.md` 规定 `artifacts[].abspath` 记"相对当前运行目录的
便携路径"，`unexpected` 之外的每一处路径都是评审用来**找到那个文件**的定位符。
把它们改成与 cwd 无关的常量，就等于把契约里的定位能力拿掉。所以本包的取舍是：
**保留定位符，把不稳定性显式列名并给出稳定化办法**（§6），而不是偷偷改成常量。

## 6. 怎么把"不稳定"变成"稳定"（按字段类别给做法）

| 字段类别 | 现状 | 想让它逐字节一致，需要动什么 |
|-|-|-|
| `generated_at` / `render_log.generated_at` | 墙钟戳 | 不建议改：冻死时间戳是**说谎**。要在 CI 里比对，请用 L2/L4 层 |
| `artifacts[].abspath`、`*.detail`、`cover.path`、`contact_sheet.path`、`template.source` | 运行期算出的路径 | 若要把"跨 cwd 也逐字节一致"变成硬指标，需要把记录锚点从"当前工作目录"改成"输出目录"，并同步修改 `references/OUTPUT_CONTRACT.md` 的措辞——**本包不动契约文本**，因此这一条作为已知取舍如实列出 |
| `spec.json.pages[].figures_on_page[].file`、`content.json.figures[].file_abs`、`sources[].path` | 原样记录 `--case` 给出的路径 | `--case` 用**相对路径**给出时记录即为相对路径；两种调用形态的差异已列入 `INVOCATION_FORM` |
| `*.checks.sha256`、`verification.traceability.hashes.*`、`audit.json.hashes.*` | 锚点记录的摘要 | 随上游稳定而自动稳定：**先把上游锚点稳定化，摘要自然一致** |
| 字体探测字段 | 宿主字体目录的函数 | 同一镜像内稳定；本包按**文件名**记录，不含本机路径 |
| `tool_versions.*` | 宿主解释器/依赖版本 | 固定镜像即固定 |

## 7. 决策规则（D1–D12）

| # | 情形 | 决策（做什么 / 记在哪） |
|-|-|-|
| D1 | `case.json` 缺失或不可解析 | 立即失败（exit 1）并说明原因，不产半成品冒充成功 | 
| D2 | 材料缺失/不可读 | 用 case.json 的结构化字段继续；缺失项进 `uncertainty`，**绝不编造** |
| D3 | 材料无文本层 | 不 OCR 冒充，如实标注"图像型材料" |
| D4 | CP1 方案门有偏差 | 先修方案；确属案例硬约束 → 继续但显式记录，`status` 降 `partial` |
| D5 | 图/表抽不出 | 保留带图号+来源的占位框，不伪造，记入 `figure_adjust`/`uncertainty` |
| D6 | 模板缺失/损坏/全链失败 | 回退 case→starting deck→运行时内置模板；全链失败写 `status=failed` |
| D7 | 方案↔执行不一致 / 主题读失败 | best-fit 替代并逐条记录偏差；主题只记 `error` |
| D8 | 文本框溢出 | 字号阶梯只降到 12pt，仍溢出就报告，绝不压到不可读 |
| D9 | 页数超限 | 确定性裁剪并记录；优先合并非证据页，绝不静默丢证据页 |
| D10 | 契约字段未知/无值 | 已知语义的键取本次运行真值；未知键按四形态给 `""/[]/{}/0/false`，**禁止 null** |
| D11 | 字体缺失 / 无 LibreOffice | 按标准字体目录探测 → PIL 内置位图字体；不产伪 PDF，预览标注 SCHEMATIC |
| D12 | 保存失败/流水线异常 | 先落盘已生成的部分产物，报错含已写路径；写 `status=failed` 的 result.json |

**本轴新增的复核动作**（不属于 D1–D12，是交付前额外一步）：
**R1** 跑 `determinism.py`，要求 exit 0；**R2** 若 exit 1，逐条读
`unexpected_volatile`，每条要么修掉、要么在四张声明表里写明理由——**不许
"大概是因为时间戳"**。

## 8. 自查清单

- [ ] `main.py` 跑通，exit 0，`result.json` 覆盖契约全部字段、无 null
- [ ] `check_contract.py` G1–G8 全过、exit 0
- [ ] `determinism.py` 跑通，exit 0；**L1 二进制一致 / L4 全 JSON 收敛 / 未声明差异 0 条** 三项都为真
- [ ] `references/DETERMINISM.md` 里的字段表与实际报告一致（重新生成而非手改）
- [ ] 输出目录内没有本机绝对路径**泄漏进包里**（运行时产物在 `--out`，不进提交包）
- [ ] 抽查 ≥3 条 `claim → 文件:行` 能在材料里找到
- [ ] 图号与正文引用一致；图表等比放入；页脚/页码全册一致
- [ ] 未使用预制答案、未提交正式案例结果

## 9. 目录结构

```
<skill root>/                      # = $SKILL_DIR
  SKILL.md                 本文档（确定性判据 L1–L4 + 四张声明表 + D1–D12）
  README.md                使用说明 / 依赖 / 限制 / 维护
  TEST.md                  本地实测记录（含 determinism.py 的真实输出摘要）
  GITHUB_URL.txt           GitHub 公开链接
  references/
    OUTPUT_CONTRACT.md     result.json 字段契约 + CP3 G1–G8（**只读，逐字保留**）
    DETERMINISM.md         ★本轴：实测报告 + 逐字段易变说明 + 稳定化办法
    RUBRIC_MAP.md          五维评分 → 本包哪个文件/机制
    failure-modes.md       失败模式与降级策略
    template_guide.md      模板使用指南（母版/版式/占位符/主题）
    checklist.md           适配检查清单
    batch-rules.md         批量一致性规则
    two-phase-workflow.md  两阶段工作流图示与分步命令
  scripts/
    main.py                编排入口（一条命令两阶段 + CP1/CP3）
    determinism.py         ★本轴：受控重跑 + 三层/四层一致性 + 字段级归因
    extract.py / deckplan.py / adopt_plan.py / adapt_pptx.py / preview.py / audit.py
    validate_result.py / check_contract.py
    pptx_toolkit.py / make_template.py / make_synthetic_inputs.py / common.py
  examples/                最小示例（合成数据）
```

## 10. 维护

- 版本：`scripts/common.py` 的 `SKILL_VERSION`；
- **改了管线任何一步 → 必须重跑 `determinism.py`**，并把新报告重新渲染进
  `references/DETERMINISM.md`；声明表只能"新增并写明理由"，不能为了让脚本
  通过而放宽匹配（表里每个键都能被 `_matches` 精确解释）；
- 交付前跑包外验收：`python validate_pkg.py <包目录>`；
- 二进制资源**永不入包**：模板由 `make_template.py` 生成、示例图由
  `make_synthetic_inputs.py` 生成、产物由运行期产生。
