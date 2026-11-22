# Academic Slide Adapter — 学术 PPT 模板与格式适配 Skill（slides 组，v2 文本资源形态）

`ppt-710fbc72`（玻尔产品周赛·北大专区·学术效率）的本地可运行 Skill 包。

功能：把论文/研究材料组织成结构清楚、证据可追溯、可编辑、符合模板要求的
学术汇报 —— **两阶段工作流**：先出**适配方案**（模板母版/版式/占位符审计 +
页→版式分配 + 批量规则 + 图表放置计划，`adopt_plan.json`，CP1 门），再按方案
真实套用模板（占位符继承可查、方案↔执行一致性可查）建册，逐页主张+图号引用+
讲稿备注、页→来源证据映射附录、统一页脚页码、图表等比适配，交付
`deck.pptx` + PNG 预览 + `result.json`（CP3 契约门 G1–G8 通过）。

**本包只含 UTF-8 文本资源**（`.md/.py/.json/.txt`，≤50 个、单文件 ≤500KB、
合计 ≤2MB、无符号链接）：模板、示例图、预览等二进制一律**运行时生成**
（见 `SKILL.md` §9），所以仓库里看不到 `.pptx`/`.png`。

## 运行方法

环境：Python 3.9+；依赖 `python-pptx`、`Pillow`（运行必需）。
本机实测：Python 3.13.9 / python-pptx 1.0.2 / Pillow 12.3.0 / numpy 2.3.5。
无 LibreOffice/PPT 时预览为 PIL 示意图（如实标注，**不产伪 PDF**）。

`$SKILL_DIR` = 本包根目录（平台装到 `/skills/weekly-skill`）。**下面所有命令在
任意 cwd 下都能跑**：脚本用 `os.path.dirname(__file__)` 自定位，不依赖 cwd。

一键全流程（产物写 `--out`，两阶段自动完成）：

```bash
python "$SKILL_DIR/scripts/main.py" --case <case.json> --task <task.md> --out <out>
```

- 材料相对路径默认相对 `case.json` 所在目录解析；平台环境在 `/app/work`
  内解析（`--work /app/work`），正式运行即：

```bash
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md \
    --work /app/work --out /app/output
```

- 显式指定模板 / 起始 deck（覆盖 case.json 内字段）：

```bash
python "$SKILL_DIR/scripts/main.py" --case <case.json> --template <模板.pptx> --out <out>
python "$SKILL_DIR/scripts/main.py" --case <case.json> --starting-deck <现有deck.pptx> --out <out>
```

- 跑通自带示例（示例图不随包，先现场合成；见 `examples/README.md`）：

```bash
SKILL_DIR=<本包根目录>; RUN=<任意可写目录>
cp -r "$SKILL_DIR/examples" "$RUN/examples"
python "$SKILL_DIR/scripts/make_synthetic_inputs.py" --dir "$RUN/examples"
python "$SKILL_DIR/scripts/main.py" --case "$RUN/examples/case.json" \
    --task "$RUN/examples/task.md" --out "$RUN/out"
```

- 分阶段独立运行（排查/复跑，见 `references/two-phase-workflow.md`；
  `extract/deckplan/preview/audit` 的 `--out` 是**目录**，
  `adopt_plan/adapt_pptx` 的 `--out` 是**文件**）：

```bash
RUN=<可写目录>; CASE=<case.json>; TASK=<task.md>
python "$SKILL_DIR/scripts/make_template.py" --out "$RUN/builtin.pptx"    # 仅当案例未给模板
# 阶段一：方案
python "$SKILL_DIR/scripts/extract.py"  --case "$CASE" --task "$TASK" --out "$RUN"
python "$SKILL_DIR/scripts/deckplan.py" --content "$RUN/content.json" --out "$RUN"
python "$SKILL_DIR/scripts/adopt_plan.py" --content "$RUN/content.json" \
    --spec "$RUN/spec.json" --builtin "$RUN/builtin.pptx" --out "$RUN/adopt_plan.json"
# 阶段二：构建 + 预览 + 审计
python "$SKILL_DIR/scripts/adapt_pptx.py" --content "$RUN/content.json" \
    --spec "$RUN/spec.json" --adopt-plan "$RUN/adopt_plan.json" \
    --builtin "$RUN/builtin.pptx" --out "$RUN/<case>_deck.pptx"
python "$SKILL_DIR/scripts/preview.py" --content "$RUN/content.json" \
    --spec "$RUN/spec.json" --out "$RUN"
python "$SKILL_DIR/scripts/audit.py" --content "$RUN/content.json" \
    --spec "$RUN/spec.json" --out "$RUN" --adopt-plan "$RUN/adopt_plan.json"
```

> 分步只产出中间件与 pptx/预览；**评分产物 `result.json` 由 `main.py` 统一写出**
> （它把审计结果、契约回显与 CP3 门串成一份），分步用于定位与复跑核对。


- 契约校验 + CP3 契约门（独立工具，exit 0 才算通过）：

```bash
python "$SKILL_DIR/scripts/validate_result.py" --case <case.json> --result <out>/result.json
python "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json \
    --out-dir <out> --case <case.json>
```

- 生成内置回退模板（默认 `--out` 到系统临时目录；也可 `--cache-dir <dir>`）：

```bash
python "$SKILL_DIR/scripts/make_template.py" --out <dir>/builtin.pptx
```

## 输入说明（case.json 主要字段）

| 字段 | 说明 |
|-|-|
| `case_id / title / subtitle` | 案例标识 / 讲稿标题 / 副标题 |
| `research_question / methods / results / discussion / limitations / conclusion` | 各环节主张数组；每项可带 `text`+`source`（`文件:行`）或 `figure_refs`/`table_refs` |
| `figures` | `[{id, file, caption, source}]`；`file` 相对 case 目录 |
| `tables` | `[{id, caption, source, rows}]`（rows 为二维数组或 CSV 路径） |
| `audience / duration_minutes / slide_count / language` | 固定受众/时长/页数/语言（zh\|en） |
| `template / starting_deck / source_material` | 模板 / 起始 deck / 材料文件（可为数组） |
| `output_contract` | 交付契约对象（自动镜像进 result.json 顶层，四形态回显） |

## 输出说明

`<case_id>_deck.pptx`（可编辑源，含逐页笔记）、`<case_id>_cover_preview.png` +
`<case_id>_slides_contact_schematic.png`（PIL 示意图预览，**非像素级导出**，
详见 `render_log.json`）、`adopt_plan.json`（**适配方案**，两阶段之阶段一）、
`result.json`（契约见 `references/OUTPUT_CONTRACT.md`）、
`spec.json/content.json/audit.json/render_log.json/summary.txt`；案例未给模板时
另生成 `_runtime/builtin.pptx`（回退模板）。
平台环境按 Runtime contract 使用 `/input/case.json`、`/app/work`、`/app/output`。
输出目录内的示例形状见 `examples/EXPECTED-OUTPUT.md`。

`result.json` 顶层除信封字段外，还会把案例 `output_contract` 的**每个键**回显
上去（禁止 null）：已知语义的键取**本次运行真实值**（例如 `preview_png`、
`evidence_per_slide`、`notes_per_slide`、`template_inheritance` 由真实产物推出），
派生明细记在 `verification.contract_echo_derived`；PDF 导出类键恒为 `false`，
因为无 PowerPoint/LibreOffice 时不产伪 PDF —— 这一点在 `uncertainty` 中说明。

## 预期增益（相对基础 Agent）

- **先方案后执行**：模板审计 + 页→版式分配在动手前定稿（adopt_plan.json），
  方案↔执行一致性可查（`adopt_plan_applied` / `adopt_plan_deviations`）；
- 模板真实套用：版式/占位符继承关系进 `template_audit`（含主题字体/色），
  缺失回退有记录；
- 内容与来源绑定：每页主张可追溯到 `文件:行`（材料另记 sha256），图号↔正文
  交叉引用自动核验；
- 整册一致性：批量规则（页脚/页码/标题位置/字号阶梯/图表缩放）统一+审计；
- 逐页讲稿：每页 notes 含主张/证据/建议时长，可直接开讲；
- 诚实失败：缺图/缺字体/缺 LibreOffice/方案偏差全部记录，不静默产出"像 PPT
  但不可用"的结果；CP3 契约门（G1–G8）把交付变成硬门。

## 限制与失败处理

详见 `SKILL.md` §4/§5（决策规则 D1–D12 + 异常处理表）与
`references/failure-modes.md`。要点：无 LibreOffice/PPT 时预览为 PIL 示意图
（如实标注）；字体缺失走"标准目录探测 → CJK 扫描 → PIL 内置字体"回退链并记录；
模板打不开自动回退下一条（含运行时生成的内置模板）；材料缺失/数值缺失绝不
编造、进 `uncertainty`；流水线异常写出 `status=failed` 的 result.json 不丢现场。

## 目录

`SKILL.md` 主文档 · `scripts/`（main / extract / deckplan / **adopt_plan** /
**adapt_pptx** / preview / audit / validate_result / **check_contract** /
pptx_toolkit / **make_template** / **make_synthetic_inputs** / common）·
`references/`（OUTPUT_CONTRACT / RUBRIC_MAP / template_guide / checklist /
batch-rules / two-phase-workflow / failure-modes）· `examples/` 最小示例
（合成数据，非正式案例；含 `README.md`、`EXPECTED-OUTPUT.md`、方案样例与文本
产物）· `TEST.md` 实测记录 · `GITHUB_URL.txt` 公开链接。
**包内无二进制资源**：模板与示例图由脚本运行时生成。

## 维护

- 版本：Skill `2.0.0`（`scripts/common.py` 的 `SKILL_VERSION`）。
- 改动后至少复跑 `TEST.md` §1 冒烟与 §2 确定性，确认全绿再交付。
- 二进制资源永不入包：模板用 `scripts/make_template.py` 生成、示例图用
  `scripts/make_synthetic_inputs.py` 生成，产物由运行产生；交付前用包外验收器
  `validate_pkg.py` 复核扩展名白名单、文件数、体积、无绝对路径。
