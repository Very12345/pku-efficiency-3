# README — Academic Slide Adapter（学术 PPT 模板与格式适配 · 增益可验证版 3.2.0）

`ppt-710fbc72`（玻尔产品周赛·北大专区·学术效率）的本地可运行 Skill 包。

一句话：**把论文/研究材料变成合模板、可编辑、证据可追溯的学术汇报；并且把"比
基础 Agent 好在哪"写成一份能被第三方复跑推翻的对照协议。**

本包的一个特点是把"增益"当工程问题处理：`references/GAIN-PROTOCOL.md` 定义了
A/B 两臂、六条公平性约束（同输入 / 同模板 / 同版本 / 同环境 / 同预算 / 不预置
答案）、八条质量指标 Q1–Q8 与四条效率指标 E1–E4，以及作者**真实跑过**的对照
记录（含对自方不利的差异项：耗时约 3.8×、重跑并非全字节一致、需人工复查的记录
更多）。`SKILL.md` §2 把每条指标映射到具体执行动作，因此"哪条证据由谁产出"是可
查的。

## 运行方法

环境：Python 3.9+；运行依赖 `python-pptx`、`Pillow`。
本机实测环境：Python 3.13.9 / python-pptx 1.0.2 / Pillow 12.3.0 / numpy 2.3.5
（numpy 仅用于版本记录）。无 LibreOffice / PowerPoint 时预览为 PIL 示意图
（如实标注，**不产伪 PDF**）。

`$SKILL_DIR` = 本包根目录（平台装到 `/skills/weekly-skill`）。**下面所有命令在
任意 cwd 下都能跑**：脚本用 `os.path.dirname(__file__)` 自定位，不依赖 cwd。

一键全流程：

```bash
python "$SKILL_DIR/scripts/main.py" --case <case.json> --task <task.md> --out <out>
```

平台正式运行（材料相对路径在 `/app/work` 内解析）：

```bash
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md \
    --work /app/work --out /app/output
```

显式指定模板 / 起始 deck：

```bash
python "$SKILL_DIR/scripts/main.py" --case <case.json> --template <模板.pptx> --out <out>
python "$SKILL_DIR/scripts/main.py" --case <case.json> --starting-deck <现有deck.pptx> --out <out>
```

跑通自带示例（示例图不随包，先现场合成）：

```bash
SKILL_DIR=<本包根目录>; RUN=<任意可写目录>
cp -r "$SKILL_DIR/examples" "$RUN/examples"
python "$SKILL_DIR/scripts/make_synthetic_inputs.py" --dir "$RUN/examples"
python "$SKILL_DIR/scripts/main.py" --case "$RUN/examples/case.json" \
    --task "$RUN/examples/task.md" --out "$RUN/out"
```

分阶段独立运行（排查与复跑；`--out` 语义：`extract/deckplan/preview/audit` 收
**目录**，`adopt_plan/adapt_pptx/make_template` 收**文件**）：

```bash
RUN=<可写目录>; CASE=<case.json>; TASK=<task.md>
python "$SKILL_DIR/scripts/make_template.py" --out "$RUN/builtin.pptx"
python "$SKILL_DIR/scripts/extract.py"  --case "$CASE" --task "$TASK" --out "$RUN"
python "$SKILL_DIR/scripts/deckplan.py" --content "$RUN/content.json" --out "$RUN"
python "$SKILL_DIR/scripts/adopt_plan.py" --content "$RUN/content.json" \
    --spec "$RUN/spec.json" --builtin "$RUN/builtin.pptx" --out "$RUN/adopt_plan.json"
python "$SKILL_DIR/scripts/adapt_pptx.py" --content "$RUN/content.json" \
    --spec "$RUN/spec.json" --adopt-plan "$RUN/adopt_plan.json" \
    --builtin "$RUN/builtin.pptx" --out "$RUN/<case>_deck.pptx"
python "$SKILL_DIR/scripts/preview.py" --content "$RUN/content.json" \
    --spec "$RUN/spec.json" --out "$RUN"
python "$SKILL_DIR/scripts/audit.py" --content "$RUN/content.json" \
    --spec "$RUN/spec.json" --out "$RUN" --adopt-plan "$RUN/adopt_plan.json"
```

> **E2 的机制**：`spec.json`（内容侧）与 `adopt_plan.json`（模板侧）是两个独立
> 阶段产物 —— **只换模板时不必重抽内容**，只需要重跑 `adopt_plan` + `adapt_pptx`
> 两个阶段。分步命令正是为这种返工定位设计的。

契约校验与 CP3 门：

```bash
python "$SKILL_DIR/scripts/validate_result.py" --case <case.json> --result <out>/result.json
python "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json \
    --out-dir <out> --case <case.json>
```

## 退出码语义

| 退出码 | 含义 | 典型触发 |
|-|-|-|
| **0** | 流程完成（**不等于**全绿：`status` 可能是 `partial`，请看 result.json） | 正常结束；`validate_result.py` 打 `VALID`；`check_contract.py` 打 `{"valid": true}` |
| **1** | 流水线失败 | case 不可解析（D1）、无可用模板（D6）、依赖缺失（D5/D14 降级）、保存失败（D16） |
| **2** | `--out` 不可写 / 参数错误 | 输出路径是普通文件或无权限（D16） |

退出码 0 时**仍必须**读 `result.json.status`。

## 增益怎么核验（本包的重点）

三步，全部可复跑（完整协议见 `references/GAIN-PROTOCOL.md`）：

1. **读 §2–§5 的协议**：确认两臂定义、公平约束、指标口径；
2. **照 §5 的命令跑一遍**：现场合成占位图 → 生成共享模板 → 跑 A 臂 → 跑 B 臂 →
   用同一套测量规则测两臂 → 对拍确定性；
3. **照 §8 的清单核对**：特别是 C2 那一条 —— B 臂的
   `template_audit.opened_from` 必须是 `case_template` 且
   `template_fallback_used=false`；若为 `builtin`，说明"同模板"没落实，对照无效。

**本次实测的关键数字**（合成示例案例、同一模板，详见协议 §6）：

| 指标 | A 臂 | B 臂 |
|-|-|-|
| 页数 / 讲稿覆盖率 / 来源定位串 | 3 / 0.0 / 0 | 10 / 1.0 / 16 |
| 页脚页码覆盖页数 / CP3 契约门 | 0 / 无 | 9 / 8-of-8 |
| `result.json` 顶层键数 | 无 result.json | 28 |
| 单册墙钟中位数 | 0.392 s | 1.508 s |
| 同输入重跑字节一致产物 | — | 11 / 12 |

**边界**（必须与数字一起读）：这是作者在**合成示例**上的实测，**不是平台分数**；
平台的三案例 × 三重复对照由组织方执行。未测项（人工排版耗时、跨模板族泛化、
PDF 导出保真）在协议 §7.2 逐条列出，不含糊过去。

## 输入说明（case.json 主要字段）

| 字段 | 说明 |
|-|-|
| `case_id / title / subtitle` | 案例标识 / 讲稿标题 / 副标题 |
| `research_question / methods / results / discussion / limitations / conclusion` | 各环节主张数组；每项可带 `text`+`source`（`文件:行`）或 `figure_refs`/`table_refs` |
| `figures` | `[{id, file, caption, source}]`；`file` 相对 case 目录解析 |
| `tables` | `[{id, caption, source, rows}]`（rows 为二维数组或 CSV 路径） |
| `audience / duration_minutes / slide_count / language` | 固定受众/时长/页数/语言（zh\|en） |
| `template / starting_deck / source_material` | 模板 / 起始 deck / 材料文件（可为数组） |
| `output_contract` | 交付契约对象（自动镜像进 result.json 顶层，四形态回显，走 D13） |

## 输出说明

`<case_id>_deck.pptx`（可编辑源，含逐页笔记）· `<case_id>_cover_preview.png` +
`<case_id>_slides_contact_schematic.png`（PIL 示意图，**非像素级导出**）·
`adopt_plan.json`（阶段一方案）· `result.json`（契约见
`references/OUTPUT_CONTRACT.md`）· `spec.json` / `content.json` / `audit.json` /
`render_log.json` / `summary.txt`；案例未给模板时另有 `_runtime/builtin.pptx`。

`result.json` 顶层除信封字段外会把案例 `output_contract` 的**每个键**回显上去
（**禁止 null**）：已知语义的键取**本次运行真实值**（走 D13），派生明细记在
`verification.contract_echo_derived`；PDF 导出类键恒 `false` —— 无
PowerPoint/LibreOffice 时不产伪 PDF（D14）。

## 限制与已知边界

- 预览是 **PIL 示意图**（`preview_is_schematic=true`），不是像素级导出；PDF 导出
  需 PowerPoint/LibreOffice，本机无（D14）。**因此"导出渲染一致性"测不到像素差异**；
- CJK 行高为估算，极端字体环境可能与 PowerPoint 实际排版有偏差（有溢出报告 D9 兜底）；
- 主题色/主题字体是**只读记录**（读 `theme1.xml`），不改写主题 XML（D8）；
- 内置回退模板主题的 ea（CJK）字体为空（python-pptx 默认模板特性）；
- 复杂 SmartArt / 艺术字 / 动画 / 切换不在范围；
- **不代写科学内容**：材料里没有的数值、结论、图件绝不补造（D4）；
- **E1 的绝对耗时依赖机器**，跨机对比只看两臂比值（本次约 3.8×）；
- 包内**无二进制资源**：模板与示例图由脚本运行时生成。

## 目录

`SKILL.md` 主文档（指标映射 + D1–D16 + 两阶段 + CP1–CP3）· `scripts/`（13 个：
main / extract / deckplan / adopt_plan / adapt_pptx / preview / audit /
validate_result / check_contract / pptx_toolkit / make_template /
make_synthetic_inputs / common）· `references/`（OUTPUT_CONTRACT · RUBRIC_MAP ·
**GAIN-PROTOCOL（对照协议 + 实测记录）** · failure-modes · template_guide ·
checklist · batch-rules · two-phase-workflow）· `examples/` 最小示例（合成数据，
非正式案例）· `TEST.md` 实测记录 · `GITHUB_URL.txt` 公开链接。

## 维护

- 版本：Skill `3.2.0`（`scripts/common.py` 的 `SKILL_VERSION`）。
- **新增能力时同步做两件事**：① `SKILL.md` §2 的指标映射表加行（说明它产出哪条
  证据）；② 若涉及新降级路径，在 §3 加决策规则并在 `failure-modes.md` 加条目。
  **只有动作、没有指标落点的功能不算增益。**
- 若改动了会影响 Q/E 指标的行为，**必须重跑 `references/GAIN-PROTOCOL.md` §5 的
  对照步骤并更新 §6 实测记录** —— 否则文档里的数字就与代码脱节。
- 改动后至少复跑 `TEST.md` §1 冒烟与 §2 确定性；交付前用包外验收器
  `validate_pkg.py` 复核扩展名白名单、文件数、体积、无绝对路径。
