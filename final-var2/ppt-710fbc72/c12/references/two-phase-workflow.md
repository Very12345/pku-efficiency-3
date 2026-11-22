# two-phase-workflow.md — 两阶段工作流（先方案，后执行）

v2 的核心组织方式。把"论文 + 模板 → pptx + 预览"拆成两个可分开核对、可
复跑、可审计的阶段，任何一步都对真实文件操作，绝不靠预制答案。

```
                    ┌──────────────  阶段一：适配方案（PLAN）  ──────────────┐
  case.json ──► extract.py ──► content.json（主张/图/表 + 来源定位）
  task.md ────┘
                  deckplan.py ──► spec.json（页结构方案：页序/页型/claims/evidence）
                                     │
  template.pptx ─┐                   ▼
  starting deck ─┼──► adopt_plan.py ──► adopt_plan.json
  （两条都缺时由  │      · 模板结构审计（母版/版式/占位符/主题）
   ensure_builtin │      · 页 → 版式分配（recommended_layout_idx）
   现场生成 16:9  │      · 批量规则评估（batch.rules/deviations）
   内 置 回 退 模  │      · 图表放置计划（figure_plan）
   板；二进制不随 │      ★ CP1：gates 全绿或偏差已记录（D4）
   包分发）    ───┘   └───────────────────────────────────────────┘

                    ┌──────────────  阶段二：执行与验证（EXECUTE） ──────────┐
  adopt_plan.json ─┐
  content/spec ────┼──► adapt_pptx.py ──► <case>_deck.pptx
                    │      · 按方案套用版式/占位符（偏差记录，不静默）
                    │      · 字号阶梯 / 页脚页码 / 图表 contain-fit / 逐页备注
                    ▼
                  preview.py ──► 封面预览 + 全册联系表（PIL 示意图，诚实标注）
                    ▼
                  audit.py ──► audit.json（真实产物逐项检查，含方案↔执行一致性）
                    ▼
                  result.json（output_contract 全字段 + adopt_plan 摘要 + status）
                    ▼
                  validate_result.py + check_contract.py
                    ★ CP2：pptx 可重开/页数一致
                    ★ CP3：契约门 G1–G8（exit 0 才算交付门通过）
                    └────────────────────────────────────────────────────────┘
```

## 为什么两阶段

1. **可判标准前置**：阶段一先把"模板结构 + 每页用哪个版式 + 批量规则 + 图表
   放哪"固化成机器可读方案（`adopt_plan.json`），评审与复跑者能在动手前核
   对方案是否合理，而不是事后看结果猜；
2. **方案 ↔ 执行一致性可查**：阶段二逐页套用方案，不一致（如推荐版式缺
   角色）记入 `template_audit.adopt_plan_deviations` —— 这是"模板是否被真实
   套用"的直接证据；
3. **失败定位**：两阶段各自产出中间文件；任一阶段失败都能从 `uncertainty`
   与日志定位，不会出现"整段粘进默认模板"式的整册返工。

## 检查点

| 检查点 | 时机 | 内容 | 不过的处置 |
|-|-|-|-|
| **CP1** | 阶段一无写完 | `adopt_plan.json.gates`（G1 模板可开 / G2 版式已枚举 / G3 每页有版式 / G4 批量偏差已披露） | 按 D4：先修方案；确属案例硬约束无法满足 → 继续但记录，status 降 partial |
| **CP2** | 阶段二构建后 | pptx 可被 python-pptx 重开；页数 = spec.json；逐页备注存在 | 记录到 `verification.checks`，status 相应降级 |
| **CP3** | 交付前 | `check_contract.py` G1–G8 全过（exit 0） | 修产物或如实保留 warning；绝不让失败伪装为 success |

## 两阶段的命令（等价于 `main.py` 单命令）

`$SKILL_DIR` = 本包根目录（平台装到 `/skills/weekly-skill`）；命令在任意 cwd
下都能跑。`--out` 语义：`extract/deckplan/preview/audit` 收**目录**，
`adopt_plan/adapt_pptx` 收**文件**（与各脚本 `--help` 一致）。

```bash
SKILL_DIR=<本包根目录>; RUN=<可写目录>          # 中间件与产物都放 RUN（不限 cwd）
CASE=/input/case.json; TASK=/input/task.md

# 案例未给模板/起始 deck 时，先现场生成回退模板（二进制不随包分发）
python "$SKILL_DIR/scripts/make_template.py" --out "$RUN/builtin.pptx"

# 阶段一
python "$SKILL_DIR/scripts/extract.py"  --case "$CASE" --task "$TASK" --work /app/work --out "$RUN"
python "$SKILL_DIR/scripts/deckplan.py" --content "$RUN/content.json" --out "$RUN"
python "$SKILL_DIR/scripts/adopt_plan.py" --content "$RUN/content.json" \
    --spec "$RUN/spec.json" --builtin "$RUN/builtin.pptx" --out "$RUN/adopt_plan.json"

# 阶段二
python "$SKILL_DIR/scripts/adapt_pptx.py" --content "$RUN/content.json" \
    --spec "$RUN/spec.json" --adopt-plan "$RUN/adopt_plan.json" \
    --builtin "$RUN/builtin.pptx" --out "$RUN/<case>_deck.pptx"
python "$SKILL_DIR/scripts/preview.py" --content "$RUN/content.json" \
    --spec "$RUN/spec.json" --out "$RUN"
python "$SKILL_DIR/scripts/audit.py" --content "$RUN/content.json" \
    --spec "$RUN/spec.json" --out "$RUN" \
    --build-audit "$RUN/<case>_deck.build_audit.json" \
    --adopt-plan "$RUN/adopt_plan.json"

# 验证（对 main.py 写出的 result.json）
python "$SKILL_DIR/scripts/validate_result.py" --case "$CASE" --result /app/output/result.json
python "$SKILL_DIR/scripts/check_contract.py" --result /app/output/result.json \
    --out-dir /app/output --case "$CASE"
```

> 平台/常规使用走一条命令完成两阶段（并写出评分产物 `result.json`）；
> 分步命令用于排查与复跑核对 —— **分步不产 `result.json`**：

```bash
python "$SKILL_DIR/scripts/main.py" --case "$CASE" [--task "$TASK"] \
    [--work /app/work] --out /app/output
```

---

## 附：两阶段与效率指标 E2（v2 补充：为什么分阶段能省返工）

`references/GAIN-PROTOCOL.md` 的 **E2（返工步数）** 不是靠"我们设计得好"来支撑的，
而是靠**阶段产物的边界**来支撑的。本节说明这条机制，并给出"什么变了要重跑什么"的
判定表。

### 阶段产物的边界

```text
内容侧产物（只依赖 case/task/材料）       模板侧产物（只依赖模板）
  content.json   ← extract.py              adopt_plan.json ← adopt_plan.py
  spec.json      ← deckplan.py             <case>_deck.pptx ← adapt_pptx.py
                                           预览 PNG         ← preview.py
```

**关键性质**：`spec.json` 由 `deckplan.py` 从 `content.json` 算出，**与模板无关**；
`adopt_plan.json` 由 `adopt_plan.py` 从 (`content.json`, `spec.json`, 模板) 算出。
因此两侧可以独立重跑 —— 这就是 E2 能下降的机制原因。

### 什么变了，要重跑什么

| 变更 | 需要重跑 | 不需要重跑 | 说明 |
|-|-|-|-|
| 材料/论文内容变了 | `extract` → `deckplan` → `adopt_plan` → `adapt_pptx`（+预览/审计） | — | 内容侧全链 |
| **只换了模板** | `adopt_plan` → `adapt_pptx`（+预览/审计） | `extract` / `deckplan` | **模板侧两个阶段**，这是 E2 的核心场景 |
| 只改了页数/受众 | `deckplan` → `adopt_plan` → `adapt_pptx` | `extract` | 页计划变了，方案要重算 |
| 只改了输出目录 | 全部（因为 `artifacts.abspath` 记录运行相对路径） | — | 换目录会改路径字样，但 deck/PNG 的**字节不变** |
| 只想核对方案是否合理 | 只跑 `adopt_plan` 并人工读 `adopt_plan.json` | 后续阶段 | **动手前就能否掉一个坏方案** |

### 为什么"整册重建"是常规做法的默认代价

常规做法没有阶段产物：模板信息（母版/版式/占位符）是在生成每一页时**临时读取**的，
因此换模板必然要重新生成全部页面，而且**没有任何中间产物可以事先核对**。相比之下
本包把模板侧信息固化成 `adopt_plan.json`（含 `layouts` 全量清单、每页
`recommended_layout_idx`、`batch` 规则评估、`figure_plan`），于是：

- 换模板 = 重跑两个阶段（不是整册重写）；
- 方案是否合理 = 打开一份 JSON 读（不必先生成 10 页再看）。

### 与 Q7 的关系

分阶段还带来一个副作用：`adopt_plan_applied` / `adopt_plan_deviations` 让"模板侧
重跑"与"手工改产物"可以被区分开 —— 前者会留下与实际一致的偏差记录，后者不会
（偏差字段会与产物不符，`audit.py` 的 `adopt_plan.consistency` 会 warn）。
两阶段因此不只是省时间，也是**可核验性的前提**。
