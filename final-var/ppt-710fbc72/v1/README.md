# README — Academic Slide Adapter（学术 PPT 模板与格式适配 · 决策显性化版 3.1.0）

`ppt-710fbc72`（玻尔产品周赛·北大专区·学术效率）的本地可运行 Skill 包。

一句话：**把论文/研究材料变成"结构清楚、证据可追溯、可编辑、合模板"的学术
汇报，并且让每一次降级都有具名规则可查。**

本包与其他"论文转 PPT"工具的分界线不在功能数量，而在于**决策是可索引的**：
执行中任何异常都能落到一条决策规则（D1–D16）与一个失败分支（B01–B24），
读者先查编号就知道该降级到哪一档、记录写在哪个字段、状态该判
`success`/`partial`/`failed`。因此 `SKILL.md` 的主结构是决策表与失败分支表，
工作流围绕它们组织。

## 运行方法

环境：Python 3.9+；运行依赖 `python-pptx`、`Pillow`。
本机实测环境：Python 3.13.9 / python-pptx 1.0.2 / Pillow 12.3.0 / numpy 2.3.5。
无 LibreOffice / PowerPoint 时预览为 PIL 示意图（如实标注，**不产伪 PDF**）。

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

分阶段独立运行（排查与复跑；见 `references/two-phase-workflow.md`。
注意 `--out` 语义：`extract/deckplan/preview/audit` 收**目录**，
`adopt_plan/adapt_pptx/make_template` 收**文件**）：

```bash
RUN=<可写目录>; CASE=<case.json>; TASK=<task.md>
python "$SKILL_DIR/scripts/make_template.py" --out "$RUN/builtin.pptx"   # 仅当案例未给模板
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

> 分步只产出中间件与 pptx/预览；**唯一评分产物 `result.json` 由 `main.py` 统一
> 写出**（它把审计结果、契约回显与 CP3 门串成一份）。分步用于定位与复跑核对。

契约校验与 CP3 门：

```bash
python "$SKILL_DIR/scripts/validate_result.py" --case <case.json> --result <out>/result.json
python "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json \
    --out-dir <out> --case <case.json>
```

## 退出码语义（脚本契约的一部分）

| 退出码 | 含义 | 典型触发 |
|-|-|-|
| **0** | 流程完成（**不等于**全绿：`status` 可能是 `partial`，请看 result.json） | 正常结束；`validate_result.py` 打 `VALID`；`check_contract.py` 打 `{"valid": true}` |
| **1** | 流水线失败 | case 不可解析（B01）、无可用模板（B08）、依赖缺失导致构建失败（B21/B22）、保存失败（B24） |
| **2** | `--out` 不可写 / 参数错误 | 输出路径是普通文件或无权限（B23） |

**约定**：退出码 0 时**仍必须**读 `result.json.status`；本包从不把降级伪装成
成功。

## 决策规则与失败分支（本包的主结构）

- `SKILL.md` §2 = **决策规则总表 D1–D16**（触发条件 → 动作 → 失败时的降级），
  分四层：输入（D1–D4）／模板（D5–D8）／版式与内容（D9–D12b）／交付与状态
  （D13–D16）；
- `SKILL.md` §3 = **失败分支处置表 B01–B24**（识别信号 → 首档 → 末档 → 记录字段）；
- `references/failure-modes.md` = 两张表的完整版，含每个分支的**逐字记录字段名**；
- `SKILL.md` §2.5 = **状态判定表**（`success`/`partial`/`failed` 各自的可判定条件，
  不靠感觉）。

新读者建议的阅读顺序：`SKILL.md` §2 → §3 → `references/failure-modes.md` →
`references/OUTPUT_CONTRACT.md`（字段契约是评分依据）。

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
`<case_id>_slides_contact_schematic.png`（PIL 示意图，**非像素级导出**，详见
`render_log.json`）· `adopt_plan.json`（阶段一方案）· `result.json`（契约见
`references/OUTPUT_CONTRACT.md`）· `spec.json` / `content.json` / `audit.json` /
`render_log.json` / `summary.txt`；案例未给模板时另有 `_runtime/builtin.pptx`。

`result.json` 顶层除信封字段外会把案例 `output_contract` 的**每个键**回显上去
（**禁止 null**）：已知语义的键取**本次运行真实值**（`preview_png`、
`evidence_per_slide`、`notes_per_slide`、`template_inheritance` 等由真实产物
推出，走 D13），派生明细记在 `verification.contract_echo_derived`；PDF 导出类
键恒为 `false` —— 无 PowerPoint/LibreOffice 时不产伪 PDF（D14），这一点在
`uncertainty` 中说明。

## 限制与已知边界

详见 `SKILL.md` §2/§3 与 `references/failure-modes.md`。要点：

- 预览是 **PIL 示意图**（`preview_is_schematic=true`），不是像素级导出；PDF
  导出需 PowerPoint/LibreOffice，本机无，故未产 PDF（D14/B18）；
- CJK 行高为估算，极端字体环境可能与 PowerPoint 实际排版有偏差（有溢出报告
  B12 兜底）；
- 主题色/主题字体是**只读记录**（读 `theme1.xml`），不改写主题 XML（D8）；
- 内置回退模板主题的 ea（CJK）字体为空（python-pptx 默认模板特性），CJK 由
  系统/预览字体回退承担，已在 `template_audit.theme` 如实呈现；
- 复杂 SmartArt / 艺术字 / 动画 / 切换不在范围；
- **不代写科学内容**：材料里没有的数值、结论、图件绝不补造（D4），缺项一律进
  `uncertainty`；
- 包内**无二进制资源**（只含 `.md/.py/.json/.txt`）：模板与示例图由
  `scripts/make_template.py`、`scripts/make_synthetic_inputs.py` 运行时生成。

## 目录

`SKILL.md` 主文档（决策表 D1–D16 + 分支表 B01–B24）· `scripts/`（13 个：
main / extract / deckplan / adopt_plan / adapt_pptx / preview / audit /
validate_result / check_contract / pptx_toolkit / make_template /
make_synthetic_inputs / common）· `references/`（OUTPUT_CONTRACT · RUBRIC_MAP ·
**failure-modes（B01–B24 完整版）** · template_guide · checklist · batch-rules ·
two-phase-workflow）· `examples/` 最小示例（合成数据，非正式案例）· `TEST.md`
实测记录 · `GITHUB_URL.txt` 公开链接。

## 维护

- 版本：Skill `3.1.0`（`scripts/common.py` 的 `SKILL_VERSION`）。
- **新增决策规则必须同步三处**：① `SKILL.md` §2 加行；② `SKILL.md` §3 加分支；
  ③ `references/failure-modes.md` 加同号条目并给出 `result.json` 记录字段名。
  缺任何一处，规则就无法被第三方复核。
- 改动后至少复跑 `TEST.md` §1 冒烟与 §2 确定性；交付前用包外验收器
  `validate_pkg.py` 复核扩展名白名单、文件数、体积、无绝对路径。
- 二进制资源永不入包：模板用 `scripts/make_template.py` 生成、示例图用
  `scripts/make_synthetic_inputs.py` 生成，产物由运行产生。
