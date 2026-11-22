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

## 附：每条命令对应的决策规则（v1 补充）

分步运行时，每一步都可能触发降级。下表把上文的命令序列与 `SKILL.md` §2 的决策
规则逐条对上，**便于在复跑失败时直接定位是哪个阶段、哪条规则**。

| 阶段 | 命令 | 主要决策规则 | 失败时先看什么 |
|-|-|-|-|
| 模板准备 | `make_template.py --out ...` | D5（案例未给模板时现场生成） | 是否因缺 python-pptx 而返回原因字符串 |
| 抽取 | `extract.py --case ... --out <dir>` | **D1**（case 不可解析）/ **D2/D3**（材料异常）/ **D4**（无定位） | `sources[].exists` 与 `uncertainty` |
| 页计划 | `deckplan.py --content ... --out <dir>` | **D11**（超页裁剪） | `change_records` 里是否有 `page_budget` 类记录 |
| 方案 | `adopt_plan.py ... --out <file>` | **D5/D6**（模板链）/ **D7**（版式缺口）/ **D8**（主题） | `adopt_plan.json` 的 `gates` 与 `layout_gaps` |
| 构建 | `adapt_pptx.py ... --out <file>` | **D7**（偏差）/ **D9/D10**（溢出/标题）/ **D12/D12b**（图表） | `.build_audit.json` 的 `adopt_plan_deviations` 与 `figure_adjust` |
| 预览 | `preview.py ... --out <dir>` | **D14/D15**（无导出后端 / 字体缺失） | `render_log.json` 的 `fallback_default` |
| 审计 | `audit.py ... --out <dir>` | 汇总各规则结果 | `audit.json` 里 level != ok 的条目 |
| 契约 | `validate_result.py` / `check_contract.py` | **D13**（契约回显）/ D2–D16 的记录完整性 | `valid` 字段与逐门 `detail` |

**两条实操约定**：

1. **`--out` 语义不同**（与各脚本 `--help` 一致）：`extract / deckplan / preview /
   audit` 收**目录**；`adopt_plan / adapt_pptx / make_template` 收**文件**。传错会
   得到 `IsADirectoryError` 一类错误，那不是降级，是调用错误。
2. **分步不产 `result.json`** —— 它是 `main.py` 的职责（它负责契约回显与 CP3 门）。
   因此**分步运行不构成一次可提交交付**；定位完成后应回到一条命令重跑。
