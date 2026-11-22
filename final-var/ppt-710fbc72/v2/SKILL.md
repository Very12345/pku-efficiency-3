---
name: academic-slide-adapt
description: >-
  Academic slide deck creation from research material with real template
  adaptation (学术 PPT 模板与格式适配) and a measurable gain protocol: read the
  actual paper/material and the actual template, extract the research storyline
  (question → method → results → limitations) with per-item source locators,
  fix the page structure against the frozen audience/duration/slide count, then
  run a two-phase workflow — phase 1 writes a machine-readable adaptation plan
  (adopt_plan: template master/layout/placeholder audit + page→layout
  assignment + batch rules + figure placement), phase 2 applies that plan
  through the given PowerPoint template's real placeholder inheritance (falling
  back with full disclosure when placeholders are missing), embeds
  figures/tables contain-fit with figure numbers cross-checked against the text,
  adds per-slide speaker notes plus an appendix evidence map, and delivers an
  editable .pptx, PNG previews and a verifiable result.json (CP3 gate:
  check_contract G1–G8). Every claim about improvement is backed by a fair
  control protocol against a baseline agent working on the SAME input and the
  SAME template (references/GAIN-PROTOCOL.md), with measurable quality and
  efficiency indicators rather than prose. Use when the task says "make an
  academic presentation / 学术PPT / 学术汇报 / 论文转PPT / adapt this paper
  into slides / 套模板 / 模板适配 / 按模板生成PPT / deck from paper", or when a
  starting deck must be re-edited on its own template.
---

# Academic Slide Adapter（学术 PPT 模板与格式适配）— 增益可验证版 3.2

本 Skill 把论文/研究材料组织成**结构清楚、证据可追溯、可编辑、符合模板要求**
的学术汇报。与"把正文粘进默认模板"的差别不止在功能，而在于**每一个"我们更好"
的说法都配一条可复跑的测量口径**：`references/GAIN-PROTOCOL.md` 定义了对照臂、
公平约束、质量指标 Q1–Q8 与效率指标 E1–E4，本文件在执行流程里标出每个动作**对
应哪条指标**，这样"增益"不是形容词而是一串能被第三方算出来的数。

因此本文件的结构是：**§2 增益指标 ↔ 执行动作映射**（先看要交付什么证据）→
**§3 决策规则 D1–D16**（每条含"失败时的降级"，并注明它保护哪条指标）→
**§4 执行流程（两阶段 + 三个检查点）** → §5 自查 → §6 资源形态。

- Skill 版本：`3.2.0`（增益可验证 / 指标—动作一一对应）
- **Skill 根 = 本文件所在目录**，下文 `$SKILL_DIR` 即指它；命令在**任意 cwd**
  下都能跑（脚本用 `os.path.dirname(__file__)` 自定位，不依赖 cwd）
- 唯一入口：`$SKILL_DIR/scripts/main.py`
- **资源形态**：只含 UTF-8 文本（`.md/.py/.json/.txt`），≤50 文件 / 单文件
  ≤500KB / 合计 ≤2MB / 无符号链接；模板、示例图、预览等二进制**运行时生成**（§6）

---

## 1. 快速上手

```bash
SKILL_DIR=<本包根目录>
python "$SKILL_DIR/scripts/main.py" --case <case.json> [--task <task.md>] \
    [--work <材料基目录>] [--template <模板.pptx>] \
    [--starting-deck <deck.pptx>] --out <输出目录>
```

平台正式运行：

```bash
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md \
    --work /app/work --out /app/output
```

先跑通自带示例（示例图不随包，需现场合成）：

```bash
SKILL_DIR=<本包根目录>; RUN=<任意可写目录>
cp -r "$SKILL_DIR/examples" "$RUN/examples"
python "$SKILL_DIR/scripts/make_synthetic_inputs.py" --dir "$RUN/examples"
python "$SKILL_DIR/scripts/main.py" --case "$RUN/examples/case.json" \
    --task "$RUN/examples/task.md" --out "$RUN/out"
```

**契约字段一律以 `references/OUTPUT_CONTRACT.md` 为准**（那是唯一评分产物的
定义）；**增益口径与对照协议以 `references/GAIN-PROTOCOL.md` 为准**。

## 2. 增益指标 ↔ 执行动作映射

这张表是本版本的主索引：左列是 `GAIN-PROTOCOL.md` 定义的指标，右列是**本 Skill
里负责产生该证据的具体动作与落点**。交付前按这张表逐行核对。

| 指标 | 定义（简） | 本 Skill 里谁负责产出 | 落点字段 / 文件 |
|-|-|-|-|
| **Q1** 页数达成度 | 实际页数 / `case.slide_count` | `deckplan.py` 的确定性页结构（cover→…→evidence_map→thankyou）+ 超页裁剪 | `spec.json` / `result.json.slide_count` |
| **Q2** 逐页讲稿覆盖率 | 有非空 notes 的页数 / 总页数 | `adapt_pptx.py` 逐页写 speaker notes（主张 / 证据 / 建议时长） | `result.json.main_result.notes_pages` |
| **Q3** 来源可追溯率 | 带 `文件:行` 定位串的页数 / 总页数 | `extract.py` 逐行编号抽取，主张携带来源定位 | `result.json.slide_evidence[].evidence[].loc` / `traceability.evidence_loc_frac` |
| **Q4** 页脚/页码一致性 | 底部带页脚或页码的页数 / 总页数 | `adapt_pptx.py` 批量规则：封面外统一页脚 + 页码 | `audit.json` 的 `layout.footer_uniform` |
| **Q5** 图表放置完整率 | 嵌入图数 / `case.figures`；且宽高比 == 源图 | `adopt_plan.py` 算 contain-fit 比例 → `adapt_pptx.py` 按比例放置（绝不拉伸） | `template_audit.figure_adjust[].aspect_preserved` |
| **Q6** 模板继承可查性 | `layout_used` 条数 / 总页数 | `adopt_plan.py` 审计母版/版式/占位符 → `adapt_pptx.py` 逐页套用并记录实际版式 | `result.json.template_audit.layout_used` |
| **Q7** 方案↔执行一致性 | `adopt_plan_applied` / 计划页数 | 阶段二消费阶段一方案；不一致逐条记偏差 | `template_audit.adopt_plan_applied` / `adopt_plan_deviations` |
| **Q8** 契约完整率 | G1–G8 通过数 / 8；顶层 null 个数 = 0 | `check_contract.py` 独立重扫 + 契约四形态回显 | `verification.contract_gates` / 顶层键 |
| **E1** 单册墙钟 | 端到端子进程耗时中位数 | 一条命令跑完两阶段（避免人工串联） | — |
| **E2** 返工步数 | 输入变更后需重跑的阶段数 | 阶段产物解耦：`spec.json`（内容侧）与 `adopt_plan.json`（模板侧）分离 | — |
| **E3** 重跑字节一致性 | 逐字节相同产物数 / 总数 | `deterministic_zip()` 固定 zip 条目时间戳；几何为纯函数 | — |
| **E4** 人工核对工作量 | 证据行数 + 审计检查行数 | 全部结论落盘，人只需核对已有记录 | `audit.json` + `result.json.slide_evidence` |

> **口径提醒**：Q4 的满分通常是 `(N-1)/N`（封面一般无页脚）；E1 的绝对值依赖
> 机器，跨机只看两臂比值；E4 的数值越大代表人要看的越多，**不是越大越好**。

## 3. 决策规则 D1–D16（每条注明保护哪条指标）

三要素：**触发条件 → 动作 → 失败时的降级**。每条末尾的 `[Qn/En]` 表示它保护哪条
增益指标 —— 也就是说，这条规则存在的理由就是"不这么办该指标会掉"。

### 3.1 输入层（D1–D4）

| # | 触发条件 | 动作 | 失败时的降级 | 保护 |
|-|-|-|-|-|
| **D1** | `--case` 不存在或不是合法 JSON | 立即停止，写 `status=failed` 的 result.json（`case_id` 取文件名词干），退出码 **1** | 不可降级；**绝不**用空壳 case 跑出"看起来像 PPT"的东西 | Q8 |
| **D2** | 材料文件缺失 / 编码失败 / 非文本 | 以 `case.json` 结构化字段继续；缺失项进 `uncertainty`，来源标 `exists:false` | 结构化字段也为空时退化为章节标题页，仍**不编造内容**，状态 partial | Q3 |
| **D3** | 材料是扫描件（无文本层） | 如实标注"图像型材料，未做 OCR"；有图仍按图清单引用 | 不引入任何编造的转写文本 | Q3 |
| **D4** | 材料里的数值/结论没有 `文件:行` 定位 | 该条**不上页面**，进 `uncertainty` | 某页因此无主张 → 合并进相邻页并记 `change_records`，不保留空页 | Q3 / Q1 |

### 3.2 模板层（D5–D8）

| # | 触发条件 | 动作 | 失败时的降级 | 保护 |
|-|-|-|-|-|
| **D5** | 案例既未给模板也未给起始 deck | 运行时现场生成 16:9 回退模板（真实母版/版式/占位符），`opened_from=builtin` 并进 `uncertainty` | 无 python-pptx → `ensure_builtin()` 返回原因字符串而非抛栈，按 D8 处理 | Q6 |
| **D6** | 模板 / 起始 deck 打不开（损坏、加密、格式不符） | 逐级回退 `case.template` → `starting_deck` → 运行时回退模板；**每级失败都进** `template_errors` | 三级全失败 → `status=failed`，不静默用默认样式冒充"已套用" | Q6 / Q8 |
| **D7** | 推荐版式缺该页型所需占位符（cover 要 title+subtitle；正文页要 title+body，`text` 类侧栏不算 body） | best-fit 选替代版式；仍缺角色就**手绘文本框**按计划几何落位 | 两条路径都写 `adopt_plan_deviations` / `layout_fallback_used`；偏差 > 0 时状态至少 partial | Q6 / Q7 |
| **D8** | 主题读取失败（`theme1.xml` 不可读） | 主题字段只填 `theme.error`，**不影响构建** | 不猜测主题值，`theme` 里不写任何推测出的字体名 | Q6 |

### 3.3 版式与内容层（D9–D12b）

| # | 触发条件 | 动作 | 失败时的降级 | 保护 |
|-|-|-|-|-|
| **D9** | 正文超出占位符真实几何 | 字号阶梯 32→28→24→20→18→16→14→**12**pt 逐级下调 | 落 12pt 仍溢出：**只报告不继续压**（`layout.overflow`）；页脚字号不受影响 | Q1 |
| **D10** | 标题单行超过容器估算宽度 | 先降号 | 仍超 → 按容器上限截断并记录；不出现看不见的溢出文字 | Q1 / Q4 |
| **D11** | 计划页数 > `case.slide_count` | 固定顺序裁剪：合并 discussion+limitations → 删 agenda → 合并最后两张结果页 | **证据页（evidence_map）最后才动**；任何裁剪写 `change_records` | Q1 / Q3 |
| **D12** | 图表源文件缺失或嵌入抛异常 | 保留图位占位框（图号 + 标题 + 来源照写） | 灰底占位框，不伪造图形、不留空白页；`figure_adjust.placed=false` | Q5 |
| **D12b** | 正文引用图号 ∉ 图清单 | 记 `xref.figure_refs` warn | **保留原文引用不擅改编号**；图清单本身为空时正文图号降级为文字描述 | Q5 |

### 3.4 交付与状态层（D13–D16）

| # | 触发条件 | 动作 | 失败时的降级 | 保护 |
|-|-|-|-|-|
| **D13** | `output_contract` 的键在本 Skill 里没有天然对应值 | **已知语义的键先取本次运行真实值**（`preview_png` / `evidence_per_slide` / `notes_per_slide` / `template_inheritance` / `slide_count` / `audience` / `language`） | 其余按键声明的容器类型给 `""` / `[]` / `{}` / `0` / `false`；**禁止 null**；PDF 类键恒 `false`；派生明细进 `contract_echo_derived` | Q8 |
| **D14** | 无 LibreOffice / PowerPoint | 预览走 PIL 示意图：封面 + 全册联系表，文件名含 `schematic`，图内叠加免责声明 | **不产伪 PDF**；`preview_is_schematic=true` | Q8（诚实披露） |
| **D15** | 预览字体探测全失败 | 回退 PIL 内置位图字体，按**文件名/索引**记录 | 日志不写本机路径 | Q8 |
| **D16** | 保存中途失败 / 流水线异常 | 先落盘已生成的部分产物，报错含已写路径，再写 `status=failed` 的 result.json | 现场不丢；**绝不写半截 JSON**；`--out` 不可写时退出码 **2** | Q8 |

### 3.5 状态判定（三档）

| 状态 | 判定条件 | 典型触发 |
|-|-|-|
| `success` | 全部审计检查 `ok` + CP3 G1–G8 全过 + **无任何降级条目** | — |
| `partial` | 出现任一 warn/fail，或命中 D2/D3/D4/D7/D10/D12/D13/D14/D15 的降级分支 | 回退模板、图位占位、方案偏差、预览仅示意图 |
| `failed` | 流水线未完成：D1 / D5(无 pptx) / D6(全链失败) / D16 | case 不可解析、无可用模板、保存失败 |

## 4. 执行流程（两阶段 + CP1–CP3，均标注产出哪条增益证据）

命令与 `scripts/` 的实际入口**逐字一致**。

```bash
python "$SKILL_DIR/scripts/main.py" --case <case.json> [--task <task.md>] \
    [--work <材料基目录>] [--template <模板.pptx>] \
    [--starting-deck <deck.pptx>] --out <输出目录>
```

### 4.1 阶段一 · 方案（PLAN）→ 产出 Q6/Q7 的前置判据 + E2 的解耦基础

1. **读真实文件**：`case.json` + `task.md`（失败走 D1）；逐个读
   `source_material` 并逐行编号 —— `content.json` 每条带 `文件:行` 与材料
   sha256（**这是 Q3 的数据来源**；缺失走 D2/D3/D4）。
2. **模板链解析**：`case.template` → `starting_deck` → 运行时回退模板
   （D5/D6）。
3. **页结构方案**：`deckplan.py` → `spec.json`：
   cover → background → methods → results×N（每图/表一页）→ discussion →
   limitations → conclusion → evidence_map 附录 → thankyou（页数充裕时插
   agenda）；超页走 D11。**这是 Q1 的数据来源。**
4. **适配方案 + CP1**：`adopt_plan.py` 打开真实模板，枚举母版 / 版式 /
   占位符 (idx/name/宽高) / 画布尺寸 / 主题字体色 → 逐页打版式分给
   `recommended_layout_idx`（D7）→ 评估批量规则（页脚 / 页码 / 标题位置 /
   字号阶梯 / 图表缩放，偏差进 `batch.deviations`，**这是 Q4 的前置**）→ 产出
   图表放置计划含 contain-fit 比例（**这是 Q5 的前置**）。
   **CP1 门**：`adopt_plan.json.gates`（G1 模板可开 / G2 版式已枚举 / G3 每页有
   版式 / G4 批量偏差已披露）。不平衡先修方案（D7）；确属硬约束则继续但显式
   记录、状态降 partial。

> E2 的机制就在这里：`spec.json` 是**内容侧**产物、`adopt_plan.json` 是**模板侧**
> 产物。只换模板时只重跑模板侧，不必重抽内容 —— 这是"返工步数"能降下来的原因。

### 4.2 阶段二 · 构建与验证（EXECUTE）→ 产出 Q2/Q4/Q5/Q6/Q7/Q8

5. **建册 + CP2**：`adapt_pptx.py` 消费 `adopt_plan.json` —— 每页套推荐版式
   （缺占位符走 D7）；内容写进占位符以继承模板主题；溢出走 D9；图表 contain-fit
   （D12/D12b）；封面外统一页脚+页码（**Q4**）；逐页写 speaker notes（**Q2**）。
   起始 deck 模式下**旧页连关系一起移除**（不留旧片），页数与计划一致，替换
   过程进 `change_records`。
   **CP2**：pptx 可被 python-pptx 重开、页数 = `spec.json`、逐页备注存在。
6. **预览**：`preview.py` 按 D14/D15 出封面 + 全册联系表示意图。
7. **自查 + result.json**：`audit.py` 在真实产物上跑 21 项检查（重开 / 页数 /
   主张覆盖 / 图号交叉引用 / 备注齐全 / 溢出 / 字号落底 / 页脚一致 / PNG 有效性 /
   证据定位覆盖率 / 方案↔执行一致性）；`main.py` 汇总成 `result.json`
   （契约回显走 D13，状态判定走 §3.5）。
8. **CP3 契约门**（**Q8**）+ 人工复核（§5）。

## 5. 检查点与自查

| 检查点 | 时机 | 判据 | 不过怎么办 |
|-|-|-|-|
| **CP1** | 阶段一结束 | `adopt_plan.json.gates.ok == true`，或偏差逐条披露 | 先修方案；硬约束无法满足 → 继续 + 记录 + partial（D7） |
| **CP2** | 构建完成 | pptx 可重开 + 页数一致 + 每页有备注 | 记入 `verification.checks`，状态相应降级 |
| **CP3** | 交付前 | `check_contract.py` G1–G8 全过（exit 0） | 修产物或如实保留 warning；**绝不让失败伪装 success** |

```bash
python "$SKILL_DIR/scripts/validate_result.py" --case <case.json> --result <out>/result.json
python "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json \
    --out-dir <out> --case <case.json>
```

`check_contract.py` 从磁盘独立重扫（自己重开 pptx、自己扫产物清单），**不信任
result.json 的自述**。

### 交付前逐行核对 §2 的指标映射

- [ ] **Q1** pptx 页数 == `case.slide_count`（或裁剪已记 `change_records`）
- [ ] **Q2** 每页都有非空 speaker notes（`notes_present == 10/10` 之类）
- [ ] **Q3** 抽查 ≥3 条 `claim → 文件:行` 能在材料里找到；`evidence_loc_frac` 已记
- [ ] **Q4** 封面外每页有页脚或页码；`layout.footer_uniform` 为 ok
- [ ] **Q5** 图数 == `case.figures` 条数；`figure_adjust` 无拉伸记录
- [ ] **Q6** `template_audit.layout_used` 有每页的版式名 + master + 来源
- [ ] **Q7** `adopt_plan_applied` == 计划页数；偏差逐条可读（含 0 偏差的记录）
- [ ] **Q8** `check_contract.py` exit 0 + `{"valid": true}`；顶层 null 个数 = 0
- [ ] 命中过的每条 D 规则都能在 `result.json` 里找到对应字段
- [ ] 状态词汇诚实：有降级就不是 `success`
- [ ] 输出目录内**没有本机绝对路径**（记录一律是运行相对路径或环境路径）
- [ ] **没有**把"未测的东西"写成已测（对照协议 §7.2 的未测清单要同步更新）

## 6. 产物清单与资源形态

| 文件 | 角色 |
|-|-|
| `<case_id>_deck.pptx` | 可编辑源：套版式/占位符、逐页主张+图表+讲稿备注、统一页脚页码 |
| `<case_id>_cover_preview.png` | 封面预览（PIL 示意图，命名与文件内均标注 SCHEMATIC） |
| `<case_id>_slides_contact_schematic.png` | 全册联系表（PIL 示意图） |
| `result.json` | **唯一评分产物**（契约见 `references/OUTPUT_CONTRACT.md`） |
| `adopt_plan.json` | 阶段一方案：模板审计 + 页→版式分配 + 批量规则 + 图表计划 |
| `spec.json` / `content.json` | 页结构方案 / 规范化抽取（含来源定位）—— E2 解耦的两侧 |
| `audit.json` / `render_log.json` / `summary.txt` | 自查报告 / 渲染日志 / 摘要 |
| `_runtime/builtin.pptx` | 案例未给模板/起始 deck 时现场生成的回退模板 |

```text
<skill root>/                      # = $SKILL_DIR（平台装到 /skills/weekly-skill）
  SKILL.md                本文档（指标映射 + D1–D16 + 两阶段 + CP1–CP3）
  README.md               使用说明 / 依赖 / 限制 / 失败处理 / 维护
  TEST.md                 本地实测记录（含增益对照的复跑结果）
  GITHUB_URL.txt          GitHub 公开链接
  references/
    OUTPUT_CONTRACT.md    result.json 结构与字段契约 + CP3 G1–G8（必读）
    RUBRIC_MAP.md         评分五维 → 设计覆盖映射
    GAIN-PROTOCOL.md      ★ 公平对照协议 + 指标定义 + 实测记录（本版重点）
    failure-modes.md      失败模式与降级策略
    template_guide.md     模板使用指南（母板/版式/占位符/主题/字号阶梯）
    checklist.md          收尾验收清单
    batch-rules.md        批量一致性规则 R1–R8
    two-phase-workflow.md 两阶段工作流图示与分步命令
  scripts/                13 个脚本（main / extract / deckplan / adopt_plan /
                          adapt_pptx / preview / audit / validate_result /
                          check_contract / pptx_toolkit / make_template /
                          make_synthetic_inputs / common）
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

## 7. 维护

- 版本常量：`scripts/common.py` 的 `SKILL_VERSION`
- 分层约定：素材抽取 `extract.py` / 页计划 `deckplan.py` / 阶段一方案
  `adopt_plan.py` / 阶段二构建 `adapt_pptx.py` / PPTX 底层 `pptx_toolkit.py` /
  验证 `audit.py` + `validate_result.py` + `check_contract.py` / 二进制生成
  `make_template.py` + `make_synthetic_inputs.py`
- **新增能力时同步做两件事**：① §2 指标映射表加行（说明它产出哪条证据）；
  ② 若涉及新降级路径，在 §3 加决策规则并在 `failure-modes.md` 加条目。
  **只有动作、没有指标落点的功能不算增益**。
- 改动后至少复跑 `TEST.md` §1 冒烟与 §2 确定性；若改动了会影响 Q/E 指标的行为，
  **必须重跑 `references/GAIN-PROTOCOL.md` §5 的对照步骤并更新 §6 实测记录**。
- 交付前跑包外验收 `python validate_pkg.py <包目录>`。
