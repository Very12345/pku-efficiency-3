---
name: academic-slide-adapt
description: >-
  Academic slide deck creation from research material with real template
  adaptation (学术 PPT 模板与格式适配), built on six interlocking mechanisms:
  (M1) plan-before-build — a machine-readable adaptation plan fixing the
  template audit and page→layout assignment before any slide is rendered;
  (M2) contract-before-render with an independent CP3 gate G1–G8 that reopens
  the pptx and rescans artifacts instead of trusting self-reports; (M3)
  evidence binding — every on-slide claim carries a `file:line` locator and
  unattributed numbers never reach a slide; (M4) planned-vs-applied consistency
  audit with per-page deviation records; (M5) runtime generation of every
  binary asset (templates, figures, previews) so the package stays pure text
  under the resource contract; (M6) deterministic bytes, so the same input
  reproduces the same deck hash. Read the actual paper/material and the actual
  template, extract the storyline (question → method → results → limitations),
  respect the frozen audience/duration/slide count, embed figures/tables
  contain-fit with figure numbers cross-checked, add per-slide speaker notes
  plus an appendix evidence map, and deliver an editable .pptx, previews and a
  verifiable result.json. Each mechanism states what breaks without it, and how
  a third party can falsify it. Use when the task says "make an academic
  presentation / 学术PPT / 学术汇报 / 论文转PPT / adapt this paper into
  slides / 套模板 / 模板适配 / 按模板生成PPT / deck from paper", or when a
  starting deck must be re-edited on its own template.
---

# Academic Slide Adapter（学术 PPT 模板与格式适配）— 机制与复用显性化版 3.3

本 Skill 把论文/研究材料组织成**结构清楚、证据可追溯、可编辑、符合模板要求**
的学术汇报。本版本的写法与前两版不同：它先把**六个机制**（M1–M6）讲清楚——每个
机制解决一个具体的退化通路，并给出"没有它会怎样"与"怎么证伪它"；再把包内资产
按**可复用单元**列出来（含参数与继承的保证），使别人能只拿走其中一层。

- Skill 版本：`3.3.0`（机制显性化 + 复用清单）
- **Skill 根 = 本文件所在目录**，下文 `$SKILL_DIR` 即指它；命令在**任意 cwd**
  下都能跑（脚本用 `os.path.dirname(__file__)` 自定位，不依赖 cwd）
- 唯一入口：`$SKILL_DIR/scripts/main.py`
- **资源形态**：只含 UTF-8 文本（`.md/.py/.json/.txt`），≤50 文件 / 单文件
  ≤500KB / 合计 ≤2MB / 无符号链接；所有二进制**运行时生成** —— 这本身是 M5

配套文档：机制详解 `references/MECHANISM.md`；资产清单与复用步骤
`references/REUSABLE-ASSETS.md`；对照协议与实测 `references/GAIN-PROTOCOL.md`；
字段契约 `references/OUTPUT_CONTRACT.md`。

---

## 1. 六个机制（摘要；详解见 `references/MECHANISM.md`）

| # | 机制 | 一句话 | 落点（文件 + 运行时字段） | 没有它会怎样 |
|-|-|-|-|-|
| **M1** | 方案先行 | 模板审计与页→版式分配在动手前固化成 `adopt_plan.json` | `scripts/adopt_plan.py` → `result.json.adopt_plan` / `template_audit.layout_used` | "读一页填一页"：出错只能整册返工，且**没有中间判据可核对** |
| **M2** | 契约先行 + CP3 硬门 | 交付形状先定；结束后由**不信自述**的校验器从磁盘重扫并逐门判定 | `references/OUTPUT_CONTRACT.md` · `scripts/check_contract.py` → `verification.contract_gates` | 产物缺件与 `null` 占位只能在人眼看时才发现 |
| **M3** | 证据定位绑定 | 每条主张带 `文件:行`；无定位的数值不上页面 | `scripts/extract.py` · `scripts/audit.py` → `slide_evidence[].evidence[].loc` / `traceability.evidence_loc_frac` | 页面"看起来对"但无法核对某个数字是不是原文里的那个 |
| **M4** | 方案↔执行一致性 | 计划与实际**逐页对照**，不一致逐条留痕 | `scripts/adapt_pptx.py` → `template_audit.adopt_plan_applied` / `adopt_plan_deviations` | 方案与产物脱钩，M1 退化成装饰文档 |
| **M5** | 二进制运行时生成 | 包内只放文本，模板/示例图/预览现场生成 | `scripts/make_template.py` · `make_synthetic_inputs.py` | 必须往包里塞 `.pptx`/`.png` ⇒ 触题面资源约束，**可能整包被拒收** |
| **M6** | 确定性字节 | 几何为纯函数 + `deterministic_zip()` 固定 zip 时间戳 | `scripts/pptx_toolkit.py` → 同输入同 deck 哈希 | 每次跑出不同哈希，"产物是不是跑出来的"不可核 |

**它们的依赖顺序**（这也是排查时的顺序）：**M5 最外层**（包能不能被接收）→
**M2**（交付物是否完整）→ **M1/M3/M4**（内容是否可信）→ **M6**（过程是否可复验）。
抽掉链条上游的机制，下游的判据会连带失效 —— 完整连锁表见
`references/MECHANISM.md` §7。

## 2. 可复用资产（摘要；参数与示例见 `references/REUSABLE-ASSETS.md`）

| 资产 | 路径 | 可独立运行 | 复用场景 |
|-|-|-|-|
| **A** 模板适配层 | `scripts/pptx_toolkit.py` + `scripts/adapt_pptx.py` | ✅ | 自带内容管线，只借"套模板 + 占位符继承 + contain-fit" |
| **B** 阶段一方案器 | `scripts/adopt_plan.py` | ✅ | 先审模板结构再决定每页版式 |
| **C** 确定性页计划器 | `scripts/deckplan.py` | ✅（**无第三方依赖**） | 想要"论文章节 → 页型序列"的确定性映射 |
| **D** 审计与契约工具 | `scripts/audit.py` · `validate_result.py` · `check_contract.py` | ✅ | 给自己的 Skill 加独立校验与硬门 |
| **E** 运行时资源生成器 | `scripts/make_template.py` · `make_synthetic_inputs.py` | ✅ | 包体受限但需要真实模板/图件 |
| **F** 示例题集与页级金标准 | `examples/` | 作为输入 | 快速验证管线；照抄"案例 → 契约"形态 |

**三个复用场景**（详细命令见 `references/REUSABLE-ASSETS.md` §8）：
① 只用模板适配层（自带内容管线）；② 接进已有管线（只要方案与校验）；③ 当作对照
基线（做自己的增益实验，须遵守"两臂同模板"约束）。

## 3. 执行流程（两阶段 + CP1–CP3）

命令与 `scripts/` 的实际入口**逐字一致**。

```bash
python "$SKILL_DIR/scripts/main.py" --case <case.json> [--task <task.md>] \
    [--work <材料基目录>] [--template <模板.pptx>] \
    [--starting-deck <deck.pptx>] --out <输出目录>
```

平台正式运行：

```bash
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md \
    --work /app/work --out /app/output
```

跑通自带示例（示例图不随包，需现场合成 —— 这是 M5 的直接体现）：

```bash
SKILL_DIR=<本包根目录>; RUN=<任意可写目录>
cp -r "$SKILL_DIR/examples" "$RUN/examples"
python "$SKILL_DIR/scripts/make_synthetic_inputs.py" --dir "$RUN/examples"
python "$SKILL_DIR/scripts/main.py" --case "$RUN/examples/case.json" \
    --task "$RUN/examples/task.md" --out "$RUN/out"
```

### 3.1 阶段一 · 方案（PLAN）—— 建立 M1 的判据

1. **读真实文件**（不凭文件名猜内容）：`case.json` + `task.md`；逐个读
   `source_material` 并逐行编号（**M3 的数据来源**：`content.json` 每条带
   `文件:行` 与材料 sha256）。
2. **模板链解析**：`case.template` → `starting_deck` → 运行时回退模板
   （`make_template.ensure_builtin()`；**M5**）。
3. **页结构方案**：`deckplan.py` → `spec.json`：cover → background → methods →
   results×N（每图/表一页）→ discussion → limitations → conclusion →
   evidence_map 附录 → thankyou（页数充裕时插 agenda）。
4. **适配方案 + CP1**：`adopt_plan.py` 枚举母版 / 版式 / 占位符 (idx/name/宽高) /
   画布尺寸 / 主题字体色 → 逐页给 `recommended_layout_idx` → 评估批量规则
   （页脚 / 页码 / 标题位置 / 字号阶梯 / 图表缩放，偏差进 `batch.deviations`）→
   产出图表放置计划（含 contain-fit 比例）。**这是 M1**。
   **CP1 门**：`adopt_plan.json.gates`（G1 模板可开 / G2 版式已枚举 / G3 每页有
   版式 / G4 批量偏差已披露）。不平衡先修方案；确属硬约束则继续但显式记录。

### 3.2 阶段二 · 构建与验证（EXECUTE）—— 让 M4/M6 可测

5. **建册 + CP2**：`adapt_pptx.py` 消费 `adopt_plan.json` —— 每页套推荐版式
   （缺占位符则 best-fit 或手绘文本框，**偏差逐条记 M4 的字段**）；内容写进
   占位符以继承模板主题；字号阶梯 32→12pt 抗溢出；图表等比 contain-fit；封面外
   统一页脚+页码；逐页写 speaker notes。起始 deck 模式下**旧页连关系一起移除**，
   替换过程进 `change_records`。
   **CP2**：pptx 可被 python-pptx 重开、页数 = `spec.json`、逐页备注存在。
6. **预览**：`preview.py` 出封面 + 全册联系表示意图（无 LibreOffice 时不产伪 PDF）。
7. **自查 + result.json**：`audit.py` 在真实产物上跑 21 项检查（重开 / 页数 /
   主张覆盖 / 图号交叉引用 / 备注齐全 / 溢出 / 字号落底 / 页脚一致 / PNG 有效性 /
   证据定位覆盖率 / **方案↔执行一致性（M4）**）；`main.py` 汇总成 `result.json`。
8. **CP3 契约门**（**M2**）+ 人工复核。

## 4. 检查点与验收入口

| 检查点 | 时机 | 判据 | 不过怎么办 |
|-|-|-| - |
| **CP1** | 阶段一结束 | `adopt_plan.json.gates.ok == true`，或偏差逐条披露 | 先修方案；硬约束无法满足 → 继续 + 记录 + partial |
| **CP2** | 构建完成 | pptx 可重开 + 页数一致 + 每页有备注 | 记入 `verification.checks`，状态相应降级 |
| **CP3** | 交付前 | `check_contract.py` G1–G8 全过（exit 0） | 修产物或如实保留 warning；**绝不让失败伪装 success** |

```bash
python "$SKILL_DIR/scripts/validate_result.py" --case <case.json> --result <out>/result.json
python "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json \
    --out-dir <out> --case <case.json>
```

`check_contract.py` 从磁盘独立重扫（**自己重开 pptx、自己扫产物清单**），不信任
result.json 的自述 —— 这正是 M2 与"自己给自己打分"的分界线。

## 5. 降级路径速查（触发条件 → 降级 → 记录字段）

完整版（含识别信号）见 `references/failure-modes.md`。这里只列**最常被问到的
几条**，并标出它保护哪个机制：

| 情形 | 降级动作 | 记录字段 | 保护 |
|-|-|-|-|
| `case.json` 缺失/坏 JSON | 停止，写 `status=failed`，退出码 **1**（不产半成品） | stderr + `result.json(status)` | M2 |
| 材料缺失 / 不可读 / 扫描件 | 以结构化字段继续；**绝不编造** | `uncertainty` + `sources[].exists` | M3 |
| 数值找不到 `文件:行` | 该条**不上页面** | `uncertainty` | M3 |
| 模板缺失 / 损坏 | 回退链 case → 起始 deck → 运行时回退模板 | `template_errors` / `opened_from` | M1/M5 |
| 全链模板失败 | `status=failed`，不静默用默认样式冒充"已套用" | `result.json(status)` | M2 |
| 推荐版式缺占位符 | best-fit 或手绘文本框，**偏差逐条记** | `layout_fallback_used` / `adopt_plan_deviations` | M4 |
| 文本框溢出（落 12pt 仍放不下） | **只报告不继续压** | `layout.overflow` / `font_floor` | — |
| 页数超目标 | 固定顺序裁剪；证据页最后才动 | `change_records` | M3 |
| 图表源缺失 | 灰底图位占位框（图号+标题+来源保留） | `figure_adjust.placed=false` | — |
| 契约键无天然值 | 真实值优先 → 类型默认；**禁止 null** | `contract_echo_derived` | M2 |
| 无 LibreOffice/PPT | PIL 示意图，**不产伪 PDF** | `render_log.json` / `preview_is_schematic` | M2 |
| 保存中途失败 | 先落盘已生成产物，再写 failed result | stderr + `result.json(status)` | M2 |

**状态判定**：`success` = 全绿且无任何降级条目；`partial` = 出现 warn/fail 或命中
任一降级分支；`failed` = 流水线未完成（case 不可解析 / 无可用模板 / 保存失败）。

## 6. 产物清单与资源形态（M5 的说明）

| 文件 | 角色 |
|-|-|
| `<case_id>_deck.pptx` | 可编辑源：套版式/占位符、逐页主张+图表+讲稿备注、统一页脚页码 |
| `<case_id>_cover_preview.png` | 封面预览（PIL 示意图，命名与文件内均标注 SCHEMATIC） |
| `<case_id>_slides_contact_schematic.png` | 全册联系表（PIL 示意图） |
| `result.json` | **唯一评分产物**（契约见 `references/OUTPUT_CONTRACT.md`） |
| `adopt_plan.json` | 阶段一方案：模板审计 + 页→版式分配 + 批量规则 + 图表计划（M1） |
| `spec.json` / `content.json` | 页结构方案 / 规范化抽取（含来源定位，M3） |
| `audit.json` / `render_log.json` / `summary.txt` | 自查报告 / 渲染日志 / 摘要 |
| `_runtime/builtin.pptx` | 案例未给模板/起始 deck 时**运行时生成**的回退模板（M5） |

```text
<skill root>/                      # = $SKILL_DIR（平台装到 /skills/weekly-skill）
  SKILL.md                本文档（六机制 + 资产清单 + 两阶段 + 检查点）
  README.md               使用说明 / 依赖 / 复用入口 / 限制 / 维护
  TEST.md                 本地实测记录（含机制可证伪判据的实测）
  GITHUB_URL.txt          GitHub 公开链接
  references/
    OUTPUT_CONTRACT.md    result.json 结构与字段契约 + CP3 G1–G8（必读）
    RUBRIC_MAP.md         评分五维 → 设计覆盖映射
    MECHANISM.md          ★ 六机制详解 + "没有它会怎样" + 可证伪判据
    REUSABLE-ASSETS.md    ★ 资产清单与三个复用场景
    GAIN-PROTOCOL.md      公平对照协议 + 实测记录
    failure-modes.md      失败模式与降级策略
    template_guide.md     模板使用指南（母板/版式/占位符/主题/字号阶梯）
    checklist.md          收尾验收清单
    batch-rules.md        批量一致性规则 R1–R8
    two-phase-workflow.md 两阶段工作流图示与分步命令
  scripts/                13 个脚本（见 §2 的资产表）
  examples/               最小示例（合成数据，非正式案例）
```

题面硬约束 *at most 50 UTF-8 text files, 500KB each and 2MB total, no
symlinks* ⇒ 本包只含文本资源，全部二进制改为运行时生成：

| 资源 | 处置 | 入口 |
|-|-|-|
| 回退模板 `.pptx` | 不随包；案例给模板时用真实文件，都缺时现场生成 | `scripts/make_template.py`（`ensure_builtin()`；也可单跑 `--out <dir>/builtin.pptx`） |
| 示例输入图 `.png` | 不随包；运行前合成纯几何占位图（带 SCHEMATIC 水印，无伪造数值） | `scripts/make_synthetic_inputs.py --dir <示例目录>` |
| 预览 `.png` / 产物 `.pptx` | 运行时生成，写入 `--out` | `scripts/main.py` |
| 字体 `.ttf/.otf` | 不随包；按标准字体目录探测（Windows 目录取自环境变量 `WINDIR`/`SystemRoot`，另有 `/usr/share/fonts`、`/System/Library/Fonts` 等候选），找不到回退 PIL 内置位图字体 | `scripts/common.py`（`font_dirs()` / `probe_font_candidates()`） |

脚本不硬编码绝对路径：`common.py` 用 `os.path.dirname(__file__)` 自定位；真实
I/O 路径全部由命令行给出（官方运行时 `/input`、`/app/work`、`/app/output`）；
写进 JSON 的路径一律便携形式（运行相对、正斜杠）。

## 7. 交付前自查

- [ ] 读的是真实文件（case/task/材料/模板），不是凭标签假设内容
- [ ] **M1**：`adopt_plan.json.gates.ok` 为真，或偏差逐条写明（CP1）
- [ ] **M2**：`check_contract.py` exit 0 + `{"valid": true}`；顶层 null 个数 = 0
- [ ] **M3**：每条页级主张带 `claim → 文件名:行`；抽查 ≥3 条能在材料中命中
- [ ] **M4**：`adopt_plan_applied` == 计划页数；偏差可读（含 0 偏差时的记录）
- [ ] **M5**：包内 `*.pptx / *.png / *.pyc` **0 命中**，但运行后产物齐全
- [ ] **M6**：同输出目录连跑两次，deck 与 PNG 的 sha256 相同
- [ ] 模板继承可查：`layout_used` 每页一条（版式名 + master + 来源）
- [ ] 逐页 speaker notes 非空；页脚/页码自封面之后全册一致
- [ ] 图号交叉引用通过；图表等比（`figure_adjust` 无拉伸记录）
- [ ] 输出目录内**没有本机绝对路径**（记录一律是运行相对路径或环境路径）
- [ ] 状态词汇诚实：有降级就不是 `success`
- [ ] **没有**把"未测的东西"写成已测（对照协议 §7.2 的未测清单要同步更新）

## 8. 维护

- 版本常量：`scripts/common.py` 的 `SKILL_VERSION`
- 分层约定：素材抽取 `extract.py` / 页计划 `deckplan.py` / 阶段一方案
  `adopt_plan.py` / 阶段二构建 `adapt_pptx.py` / PPTX 底层 `pptx_toolkit.py` /
  验证 `audit.py` + `validate_result.py` + `check_contract.py` / 二进制生成
  `make_template.py` + `make_synthetic_inputs.py`
- **新增机制时同步做三件事**：① 本节 §1 加行（含"没有它会怎样"）；②
  `references/MECHANISM.md` 加同号小节（四段结构：机制 / 落点 / 没有它会怎样 /
  可证伪判据）；③ 若该机制引入新的可复用单元，在
  `references/REUSABLE-ASSETS.md` 加资产条目并给出参数与继承的保证。
  **没有可证伪判据的机制不算机制**。
- 若改动了影响产出或字段的行为，须重跑 `references/GAIN-PROTOCOL.md` §5 的对照
  步骤并更新其 §6 实测记录，同时复核 `MECHANISM.md` 里引用的数字。
- 改动后至少复跑 `TEST.md` §1 冒烟与 §2 确定性；交付前跑包外验收
  `python validate_pkg.py <包目录>`。
