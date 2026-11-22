---
name: scientific-figure-craft
description: >
  科研数据图表生成与编辑 Skill（v2，带检查点 CP1–CP6 与决策规则 D1–D18）。
  当输入包含科研数据表格（CSV/TSV/JSON）、统计结果、实验记录、生物源材料，
  或需要生成/编辑示意图、机制图、流程图、柱状图、折线图、散点图、箱线图、热图、
  扇区图、通路图、多面板组合图（关键词：figure、chart、plot、diagram、数据图、
  科研绘图、机制图、通路图、graphical abstract、SVG、可编辑图稿、制图、出图）时使用。
  流程：读实际文件（CP1）→ 抽取字段/实体（CP2）→ spec lint（CP3）→ 生成可编辑
  分层 SVG（每个图元带 data-* 溯源属性）+ PNG/PDF 预览 → 双校验（figcheck G1–G8 /
  mapcheck 数据↔图元双向核对 + 确定性再跑）→ 按契约写 result.json（输出契约四形态
  回显，禁止 null）。严格以真实文件为准，不臆造数据、不提交预制答案。
---

# 科研数据图表生成与编辑（scientific-figure-craft）v2 · 整合版（决策层 + 增益层 + 机制层）

> 本包整合了基线 Skill 与 3 个强化层,各层对应不同的评分维度:可靠体验 10 + 实际效果 40 · 使用增益 25 · 创新增益 15 + 生态贡献 10。
> 各层内容**不重复**:决策层给规则与失败分支;增益层给对照协议与指标口径;机制层给机制说明与可复用资产。
> 建议使用顺序:先用「决策层」跑通并处理异常,再用「增益层」证明并度量改善,最后用「机制层」复用与扩展。
> 各层的原始文件都完整保留在本包内,不是摘要 —— 下面每一层都是可以独立执行的完整规范。

## 本包文件索引

- `COMPARE.md`
- `GITHUB_URL.txt`
- `README.md`
- `REFINEMENT-NOTES.md`
- `TEST.md`
- `examples/EXPECTED-OUTPUT.md`
- `examples/README.md`
- `examples/baseline_agent.py`
- `examples/case.json`
- `examples/data.csv`
- `examples/entities.json`
- `examples/material.md`
- `examples/measure_ab.py`
- `examples/task.md`
- `references/GAIN-PROTOCOL.md`
- `references/MECHANISM.md`
- `references/OUTPUT_CONTRACT.md`
- `references/REUSE-KIT.md`
- `references/RUBRIC_MAP.md`
- `references/audit-rules.md`
- `references/encoding-spec.md`
- `references/failure-modes.md`
- `references/typesetting-presets.md`
- `references/workorder-field-map.md`
- `scripts/chartkit.py`
- `scripts/check_contract.py`
- `scripts/cjkfont.py`
- `scripts/extract.py`
- `scripts/figcheck.py`
- `scripts/main.py`
- `scripts/mapcheck.py`
- `scripts/spec_lint.py`
- `scripts/svgtext.py`
- `scripts/verify_rerun.py`
- `templates/entity_glossary.json`
- `templates/figure_map.schema.json`
- `templates/journal_styles.json`
- `templates/result.template.json`
- `examples/output/data_manifest.example.json`
- `examples/output/figcheck_report.example.json`
- `examples/output/mapcheck_report.example.json`
- `examples/output/result.example.json`
- `examples/output/validation.example.json`

---

# 【决策层】决策规则与失败分支（目标维度:可靠体验 10 + 实际效果 40）

---
name: scientific-figure-craft
description: >
  科研数据图表生成与编辑 Skill（决策显性化版）。当输入包含科研数据表格
  （CSV/TSV/JSON）、统计结果、实验记录或生物源材料，或需要生成/编辑示意图、
  机制图、流程图、柱状图、折线图、散点图、箱线图、热图、扇区图、通路图、
  多面板组合图（关键词：figure、chart、plot、diagram、数据图、科研绘图、
  机制图、通路图、graphical abstract、SVG、可编辑图稿、制图、出图）时使用。
  本版把执行过程中的每一个分支决定写成可查表的决策规则（D1–D16：触发条件 →
  动作 → 失败降级），并配一张失败分支表（FM-M/FM-D/FM-R/FM-E/FM-C/FM-X 六族，逐条给出
  检出点、处置与 result.json 落痕字段）。流程：读契约 → CP1 盘点材料 → CP2 抽取
  字段与实体 → CP3 规格门 → CP4 生成分层可编辑 SVG + PNG/PDF 预览 → CP5 双校验
  （数据↔图元双向核对 + G1–G8 硬门 + 确定性再跑）→ CP6 契约落地。严格以真实文件
  为准，不臆造数据、不提交预制答案。
---

## 科研数据图表生成与编辑（scientific-figure-craft）· 决策显性化版

面向「玻尔产品周赛 · 北大专区 · 学术效率 · 第三期」 challenge-1bd90d8a。
本版**只强化一件事**：把「遇到岔路时该走哪条」从隐含经验变成可核对的决定。

> **本包形态**：全部资源均为 UTF-8 文本（`.md/.py/.json/.txt/.csv`），**零二进制**
> ——没有 `.pptx/.png/.pdf/.svg`、没有字体文件、没有 `__pycache__`。交付的图与预览
> 一律由 `scripts/main.py` 在运行时现场生成，因此包内不存在"预制答案"。
> 所有命令以 `$SKILL_DIR`（本文件所在目录的绝对路径）为前缀，cwd 不影响执行。
> 五维评分的逐条落点见 `references/RUBRIC_MAP.md`。

**为什么要把决策写出来**：本类图题的失误几乎都不是"画不出来"，而是**在岔路上默认选错**
——缺列时顺手补一个、量级可疑时顺手改一下、字体缺字时当作正常、契约字段缺了就写 null。
这些选择单看都"合理"，合起来就让图不可信。决策规则表把每个岔路的**触发条件**写死，
再给出**失败时的降级动作**，使同一输入在不同人的手里走到同一个结果。

---

### 1. 适用条件与边界

**适用**：平台固定的 3 个案例（数据图表生成 / 样式调整 / 标注校验 / 源数据关联 /
可编辑源文件与导出），以及任何「数据表或生物源材料 → 可编辑科研图」的请求。

**不适用**（明确划出去，不越界承诺）：
- 统计方法的选择、显著性的计算与检验 —— 本 Skill 只**转述**材料已给的 p 值与检验名（D6）。
- 实验方案与实验路线设计。
- 替用户下科学结论。文字说明不能替代实际运行证据。

**运行环境**：Python 3.8+ 标准库 + Pillow（渲染 PNG/PDF）。matplotlib / cairosvg /
svgwrite 均**非必需**。不访问网络。

---

### 2. 自定位约定（本 Skill 可在任意 cwd 下运行）

`$SKILL_DIR` = **本 SKILL.md 所在目录的绝对路径**（平台安装期为 `/skills/weekly-skill`）。
脚本内部一律用 `os.path.dirname(os.path.abspath(__file__))` 解析 `templates/` 与
`references/`，所以 cwd 与技能根不一致也能跑。

```bash
# bash：设一次，后续命令照抄
SKILL_DIR=/skills/weekly-skill
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output
```
```powershell
# PowerShell：把占位符换成技能包的实际绝对路径（平台为 /skills/weekly-skill）
$SKILL_DIR = "<技能包绝对路径>"
python "$SKILL_DIR\scripts\main.py" --case \input\case.json --out \app\output
```
不确定安装位置时，用一行命令打印自定位结果：
```bash
python -c "import sys;sys.path.insert(0,r'<SKILL_DIR>/scripts');import chartkit;print(chartkit.skill_root())"
```

---

### 3. 输入与输出

#### 3.1 运行期输入

| 来源 | 内容 | 缺失时的处置 |
|-|-|-|
| `/input/case.json` | case_id、figures 规格、data 引用、output_contract、manual_confirmations | **必需**；不可解析 → `status=failed` + 最小诚实信封（FM-M5） |
| `/input/task.md` | 任务说明（要几张图、图型、目标样式、图面约束） | 缺 → 自动找同目录 `task.md`；仍无 → 记 `uncertainty`（D14） |
| 源数据表 | CSV / TSV / JSON | 一个都没有 → **不得** `completed`（CP1 判定） |
| 生物源材料 | `entities_file` JSON 或 `material` 文本（figure03 类网络/机制图） | 缺 → 机制图按 FM-M1 降级 |

`case.json` 的组织形态（脚本全部兼容）：顶层对象，或 `{"cases":[...]}`，或数组取第一项；
图规格可放 `figures` / `figure` / `figure_spec`；数据可放 `data` / `data_files` / `sources`，
也可由脚本在同目录自动发现。

#### 3.2 产出（`/app/output`，一律 UTF-8）

| 文件 | 性质 | 硬要求 |
|-|-|-|
| `figure-<id>.svg` | 可编辑分层矢量源 | `<g id="layer-*">` 分层；`<metadata id='provenance'>` 溯源块；每个数据图元带 `data-*`；**文字始终是真实 `<text>`，永不转曲**（G5 机器检查） |
| `figure-<id>.png` / `.pdf` | 同场景预览 | 与 SVG 逐元素一致；PDF 元数据时间戳归一化（见 §6 FM-E6） |
| `data_manifest.json` | 图元 ↔ 源数据映射 | 每个图元登记 `column + row_index + value`（或实体 `id/cite`），与 SVG 的 `data-*` 同名对齐 |
| `validation.json` | 标注校验清单 | 八类检查逐项给出 `ok/warn/fail` |
| `mapcheck_report.json` | 数据↔图元双向核对报告 | `mismatched=0 unmatched=0` |
| `figcheck_report.json` | G1–G8 硬门报告 | `all_pass=true` |
| `result.json` | 结构化结果 | 契约字段全回显（四形态，禁 null）+ case_id + status/sources/uncertainty/change_records/checkpoints/gates/artifacts_sha256 |
| `/app/work/`（`--work`） | 中间产物 | `extract.json`、`spec_lint.json` |

---

### 4. 执行链路（S0–S7，六个检查点是判定门）

#### S0 定位与读契约
读 `references/OUTPUT_CONTRACT.md`（字段契约 + G1–G8）与 `references/audit-rules.md`
（检查标准）；读 `/input/case.json` 记录 `case_id`、figures 列表、output_contract 形态；
读 `/input/task.md` 提炼图面约束；确认 `$SKILL_DIR`。

> **顺序不可换**：契约先读、材料后读。先读契约的作用是让后续每一步都知道「要交什么」，
> 避免画完才发现少了必需产物。

#### S1 **CP1 材料盘点** —— 先看文件，再谈内容

```bash
python "$SKILL_DIR/scripts/extract.py" --case /input/case.json --out /app/work --json
```

1. 逐个列出案例材料，对每个源文件算 sha256 并记录 `dataset_version`，确认存在性与行数。
2. **禁止**：不读文件就按文件名/标签猜内容；把材料摘要当源数据用；编造列。
3. **CP1 判定**：`case_id` 已取到 ∧ task.md 已找到（或已记 `uncertainty`）∧
   数据文件至少发现一个。**任一不满足 → status 不得为 `completed`。**

#### S2 **CP2 抽取实体-关系-数据**
- 数值图：逐列画像 `{列名, 语义(x/y/误差/样本量/分类), 单位(从列名括号提取), 取值范围, 空值位置}`。
- 机制/通路图：从 `entities_file` 直接装载；材料文本支持显式行语法
  `ENTITY: <id> | <label> | <group> | <cite>` 与 `REL: <from> -> <to> | <label> | <type>`；
  其余段落按 `templates/entity_glossary.json` 词表扫描，命中项标 `uncertain=true`
  —— **必须由 Agent 对照源材料原文确认后才可上图**（D4）。
- **CP2 判定**：每列语义无歧义 ∧ 每个实体/关系有来源 ∧ 不确定候选已显式记录。

#### S3 **CP3 规格门（spec lint）**

```bash
python "$SKILL_DIR/scripts/spec_lint.py" --spec /input/case.json --case /input/case.json
# 退出码：0 = valid（可进入生成）；2 = 有 error（不得进入生成）；1 = 用法/文件错误
```
- **CP3 判定**：图型合法 ∧ 列存在 ∧ 误差语义常规 ∧ 显著性有锚点与来源 ∧ 网络边不悬空。
- lint 结果写入 `result.json.spec_lint` 与 `checkpoints.cp3_spec_lint`。

#### S4 **CP4 生成可编辑源与渲染**

```bash
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output \
      --work /app/work [--task /input/task.md] [--style nature] [--dpi 300] [--note "人工调整"]
# 退出码：0 = completed 且 G1–G8 全过；2 = partial；1 = failed
```
- 多图按 `figures[]` 依次处理；**单图失败不阻塞其他图**（status 降为 `partial`）。
- **CP4 判定**：每张图 SVG+PNG+PDF 齐全 ∧ SVG 分层且含溯源 ∧ 预览可打开。

#### S5 **CP5 双校验 + 确定性再跑**

```bash
python "$SKILL_DIR/scripts/mapcheck.py"  --dir /app/output --case /input/case.json
python "$SKILL_DIR/scripts/figcheck.py"  --dir /app/output --case /input/case.json
python "$SKILL_DIR/scripts/verify_rerun.py" --case /input/case.json --out /app/output
```
- **mapcheck**：manifest 元素必须在 SVG 中存在；SVG 数据层图元必须在 manifest 登记；
  `column+row_index+value` 三元组**重读源文件逐行核对**（容差 1e-9）。
- **figcheck（G1–G8）**：契约 → 文件 → SVG 可编辑性（分层/溯源/未转曲/无外部实体）→
  预览 → 六项标注校验无 fail → status 自洽。
- **verify_rerun**：同输入重跑，SVG/PNG/PDF/manifest/validation 字节级稳定
  （`result.json` 只允许时间戳类字段不同）。
- **CP5 判定**：G1–G8 全过 ∧ mapcheck 0 mismatch ∧ 确定性通过或差异已如实记录。
  任何 `fail` → 修 spec 后重跑；`warn` → 判断处置并写入 `uncertainty`。

#### S6 **CP6 契约落地与字段覆盖复核**

```bash
python "$SKILL_DIR/scripts/check_contract.py" --result /app/output/result.json --case /input/case.json
# 退出码 0 = PASS（missing=0 null=0 contract_missing=0）；1 = 有缺口
```
- 契约四形态逐项回显；缺失字段按**声明容器类型**给 `""`/`[]`/`{}`/`false`/`0`，**绝不写 null**。
- `status` 与产物事实严格一致（G8）。视觉终检：打开 SVG/PNG 核对坐标、单位、图例、
  显著性星号、实体名拼写。
- **CP6 判定**：`output_contract_applied` ∧ `gates.all_pass` ∧ `artifacts_sha256` 已记录。

#### S7 交付前逐项过自查清单
见 §8。

---

### 5. 决策规则表（D1–D16）

每条格式固定为「**触发条件 → 动作 → 动作失败时的降级**」。执行时遇到岔路，
先在下表找到对应行再动手；表中未覆盖的岔路按 D10 处理（记 `uncertainty` 并降级），
**不得静默自行发明规则**。

| # | 触发条件（何时进入这条规则） | 动作（默认选择） | 失败/不可行时的降级 | 落痕字段 |
|-|-|-|-|-|
| D1 | 要在图上画任何一个图形元素 | 该元素必须具备溯源（文件/列/行 或 实体 id/cite） | 无法溯源 → **不画该元素**；确有必要则画虚线占位 | `data_manifest.json` 该元素 `source`；占位则记 `uncertainty` |
| D2 | 生成坐标轴 | 轴标签带单位（源数据有单位时）；刻度范围覆盖数据并留 5% 余量 | 单位无法从列名或元数据获得 → 保留无单位标签并记 `warn` | `validation.json` `axis-units` |
| D3 | 画图例 | 每个系列恰有一个图例项，系列 id 与图例 id 一致（引擎自动校验） | 无法一一对应 → **修 spec 后重跑**，不得带病交付 | `validation.json` `legend-mapping`（fail 阻止 completed） |
| D4 | 引用任何科学实体名（基因/蛋白/物种/化合物/通路名） | 取源材料原文，**不翻译、不"优化"拼写** | 无法确认 → 保留原文 + `uncertain=true`，对照原文确认后才上图 | `extract.json` `uncertain`；`uncertainty` |
| D5 | 文本含 CJK 字符 | 使用 CJK 字体族回退链 | PIL 渲染缺字 → SVG 照常（回退链），PNG 记 `warn` | `uncertainty`；`validation.json` `cjk-font` |
| D6 | 需要标注显著性 | 星号数量与 p 值**必须与源标注一致**；只转述，不自行计算统计量；图注写明 p 值来源与检验方法 | 源未给 p 值或检验名 → 不画该显著性标注，并记 `uncertainty` | `validation.json` `significance`；`figure_meta.annotation_footnotes` |
| D7 | 输出 SVG | 必须分层（背景/坐标/数据/标注/图例）、元素 id 稳定、含 metadata 溯源块 | 引擎不可用时**保 SVG 先落盘**，其余产物缺失如实记录 | `gates.G5` |
| D8 | 画误差线 | 语义（SE / SD / CI）以源元数据 `spec.error.semantics` 为准，写入 manifest 并校验 | 源未标语义 → 记 `uncertainty`，**不猜语义** | `data_manifest.json` `error_value`；`validation.json` |
| D9 | 遇到空值 / NaN | 不补造。默认「跳过该点并计数」 | 整列无值 → 该字段报错并记 `uncertainty`，**不臆造数值** | `validation.json` `null-handling`；`uncertainty` |
| D10 | 任何维度未能完成 | `status=partial` + `uncertainty` 写明原因与可复验路径 | —— （这是兜底规则，**禁止**把失败写成完成） | `status`；`uncertainty`（G8 强制） |
| D11 | 发生任何人工修改或参数调整 | 写 `change_records`（时间戳 + 内容）；`--note` 追加一条 | —— | `change_records` |
| D12 | 需要在"加载 Skill / 不加载"之间做对照 | 双方使用**同一输入文件、同一数据版本、同一导出参数**；本包侧的同输入重跑必须字节级稳定 | 出现字节差异 → `verify_rerun` 定位随机源（如时间戳）并修掉，不得用"看起来一样"搪塞 | `artifacts_sha256`；`verify_rerun` 报告 |
| D13 | 标签过长 / 图例遮挡 / 网络节点标签重叠 | 标签自动旋转 30°；图例自动移出绘图区；复杂网络手给节点 x/y | 调整后仍重叠 → 记 `warn` 并在 `uncertainty` 说明 | `validation.json` `adjustments` / `occlusion` |
| D14 | `task.md` 缺失，或图片规格在 case 与 task 之间不一致 | 以 `case.json` 的 `figures[]` 为执行依据；task.md 缺失记 `uncertainty`；两者冲突 → **记冲突并以 case 为准**，在 `change_records` 写明 | —— | `uncertainty`；`change_records` |
| D15 | 处理 `output_contract` | 四种形态（名字列表 / 名称→类型 / 嵌套 fields 列表 / 嵌套 fields 映射）**全部完整回显**；缺失按声明容器类型给空值，禁止 null | 契约声明了本 Skill 不产出的字段 → **不做假映射**，给容器类型空值并写明原因 | `output_contract_applied`；`uncertainty`（FM-C3） |
| D16 | 准备写 `status` | 与产物事实严格自洽：有 `fail`/缺口 → 不得 `completed`；无任何图 → `failed`；`failed_figures` 与 `uncertainty` 互不矛盾 | —— | `status`；`gates.G8` |

#### 5.1 决策优先级（两条规则同时命中时）

1. **诚实优先于完整**：D10（如实降级）压过任何"把字段填满"的冲动；D15 的禁 null 与
   D10 不冲突——空值给**声明容器类型的空值**，不是编造内容。
2. **可核验优先于好看**：D1 / D3 / D6 / D8 四条涉及"图上写了什么"的规则，
   在任何与"图面美观"冲突的场合一律取前者。
3. **保源优先于保预览**：D5 / D7 在渲染能力不足时，先保证 SVG 与全部 JSON 落盘。
4. **阻断优先于带病交付**：D3 / D6 的 `fail` 会阻止 `completed`，必须先修 spec。

---

### 6. 失败分支表（FM 六族：M 材料 / D 数据 / R 图面 / E 导出 / C 契约 / X 依赖）

完整推理与复验命令见 `references/failure-modes.md`（**41 条**编号条目）；下表是执行时的
**速查分支表（37 条）+ §6.7 补充分支（4 条）**。两处的 FM 编号完全一致，可用
`grep -o 'FM-[MDREXC][0-9]*' SKILL.md references/failure-modes.md | sort -u` 对拍。

#### 6.1 FM-M 材料分支

| 分支 | 触发条件 | 检出点 | 处置 | 落痕 |
|-|-|-|-|-|
| FM-M1 | 材料文件不存在 | CP1 盘点 | 不猜内容，明确列出缺失路径 | `status=partial`；`uncertainty` |
| FM-M2 | 材料存在但 0 行 / 空表 | `load_table` | 明示为空，该图不产出 | `failed_figures` |
| FM-M3 | 材料是扫描件 / 受保护 PDF，无法直接抽取 | extract / 平台 pdf-text-tool | 先用平台工具转文本；仍不可读 → 说明工具与限制 | `uncertainty` |
| FM-M4 | 生物源材料表述含糊，实体无法确认 | 词表扫描命中 | 候选标 `uncertain`，对照原文确认后才上图（D4） | `extract.json`；`uncertainty` |
| FM-M6 | `case.json` 不存在 / 不可解析 / `--out` 不可写 | 入口 | 写**最小诚实信封**：`case_id`+`status=failed`+`error`+traceback 摘要+`sources`+`change_records` | `result.json.status=failed`；退出码 1 |

#### 6.2 FM-D 数据分支

| 分支 | 触发条件 | 检出点 | 处置 | 落痕 |
|-|-|-|-|-|
| FM-D1 | x/y/误差列名在表中找不到 | `spec_lint` E3 + 列画像 | 用画像修正列名；**禁止补造列** | `failed_figures`；修正后重跑 |
| FM-D2 | 部分格子为空 | 画像 `n_null` | 跳过该点并计数；整列无值 → 报错 | `uncertainty`（含数量） |
| FM-D3 | 数值与标题语义差 10 倍以上 | 无自动判据 | `warn` 保留原值并标可疑，**不"修正"** | `uncertainty`；`warnings` |
| FM-D4 | 轴标签没有单位 | `axis-units` | 从列名括号提取，或按源元数据补 unit | `validation.warnings` |
| FM-D5 | 分不清误差线是 SE / SD / CI | `spec.error.semantics` | 按源元数据写 semantics；源未标 → 记 `uncertainty` | `validation.json` |
| FM-D6 | `filter` 条件在表中无匹配行 | `apply_row_filter` | 报错并列出该列可用取值 | `failed_figures` |
| FM-D7 | box/pie 需要的统计量源未提供 | `presets` 直供检查 | 只用源给的最小/中位/四分位；**不代算** | 转述声明 |

#### 6.3 FM-R 图面分支

| 分支 | 触发条件 | 检出点 | 处置 | 落痕 |
|-|-|-|-|-|
| FM-R1 | 刻度文字互相重叠 / 标签过长 | 字体实测 | 自动旋转 30° | `validation.adjustments` |
| FM-R2 | 图例或标注盖住数据 | `occlusion` 真实测量 | 图例移出绘图区；网络图手给节点坐标 | `validation` `occlusion` warn |
| FM-R3 | PNG 中文出现方框 / 乱码 | `cjk-font` 校验 | SVG 回退链照常；PNG 记 warn（D5） | `uncertainty`；`environment.fonts` |
| FM-R4 | 图例项与数据系列对不上 | `legend-mapping` | 自动对齐；无法对齐 → 修 spec 后重跑 | `validation` fail → 阻止交付 |
| FM-R5 | 有星号但没有对应线段（或反之） | `significance` | 修 `annotations` 使线段数与文字数相等 | `validation` fail |
| FM-R6 | 留白后画布无空间画图 | `compute_plot_area` | 报错并提示增大画布或减小边距 | `failed_figures` |
| FM-R7 | 网络关系引用了未知节点 | E8 + warnings | 不画该边并记录 warning | `validation.warnings` |

#### 6.4 FM-E 导出分支

| 分支 | 触发条件 | 检出点 | 处置 | 落痕 |
|-|-|-|-|-|
| FM-E1 | SVG 文字被转成路径 | `figcheck` G5 `real_text` | 用本包管线重新生成；编辑器保存时勿选"转曲" | `gates.G5` |
| FM-E2 | SVG 扁平、无 `data-*` | G5 `layers` / `provenance` | 用官方管线重生成 | `gates.G5` |
| FM-E3 | SVG 含 `DOCTYPE` / 外部实体（XXE） | G5 `no_xxe` | 拒绝生成含外部实体的产物 | `gates.G5` |
| FM-E4 | PNG 打不开 / 空文件 | G6 open + verify | 查 Pillow 与路径；缺失时**保 SVG** | `gates.G6` |
| FM-E5 | PDF 不以 `%PDF` 开头 | G6 | 重新渲染；仍失败则跳过该预览并警告 | `gates.G6` |
| FM-E6 | 同一输入两次运行的 `.pdf` 字节不同 | `verify_rerun` / `artifacts_sha256` | PDF 写入器会写入当前时间戳 → 生成后**把 `/CreationDate`、`/ModDate`、`/ID` 归一化为固定值**（`chartkit.stamp_pdf_deterministic`，同步修正 xref 偏移） | `artifacts_sha256` 两次一致 |
| FM-E7 | 重跑后 SVG/JSON 字节不同（非时间戳） | `verify_rerun` | 定位随机源（字典序、浮点格式、时间戳入图）并修掉；确实无法消除 → 如实记录差异 | `artifacts_sha256` |
| FM-E8 | Pillow 缺失 | `chartkit.HAS_PIL` | **保 SVG 与全部 JSON**，PNG/PDF 记为缺失并写明安装方式 | `uncertainty`；G6 |

#### 6.5 契约四形态分支（与 FM 并列，属 G2）

| 分支 | 触发条件 | 处置 | 落痕 |
|-|-|-|-|
| FM-C1 | 形态①的列表里混入非字符串项 | 跳过非法项，其余照常回显 | `output_contract_applied=true` + `uncertainty` |
| FM-C2 | 形态②/④ 声明了未知类型名 | 按字符串容器给 `""`（**绝不 null**） | 同上 |
| FM-C3 | 契约声明了本 Skill 不产出的字段 | **不做假映射**：给声明容器类型的空值，并写明"该字段本 Skill 不产出" | `uncertainty` |
| FM-C4 | 完全没有 `output_contract` | `output_contract_applied=false`，只写本 Skill 自有字段，**不臆造契约字段** | `output_contract_applied` |
| FM-C5 | 契约声明与产物不一致 | `check_contract.py` 返回 1 并列出 missing/null 字段；修复后重跑 | `check_contract` 报告 |

#### 6.6 依赖与模板分支

| 分支 | 触发条件 | 处置 | 落痕 |
|-|-|-|-|
| FM-X1 | `templates/journal_styles.json` 缺失或 JSON 损坏 | **回退内置默认样式**继续出图，不中断 | `environment.style`；`uncertainty` |
| FM-X2 | `templates/entity_glossary.json` 缺失 | 回退内置"关系类型→颜色/线型"默认表；词表扫描跳过 | `uncertainty` |
| FM-X3 | `scripts/` 不完整（被单独复制走） | import 立即失败；命令非零退出并打印缺失模块，**不产出半成品 result** | 退出码 1 |

#### 6.7 补充分支（速查表外的 4 条，编号与 failure-modes.md 一致）

以下 4 条同属 FM 族，但在日常执行中出现频次低，故放在速查表之外；
编号与 `references/failure-modes.md` 一致，便于交叉检索。

| 分支 | 触发条件 | 处置 | 落痕 |
|-|-|-|-|
| FM-E9 | 导出 DPI / 色彩空间不满足投稿要求 | 选对应样式预设（`nature`/`cell` = 300 dpi），并记录实际导出参数 | `environment.dpi` / `environment.style` |
| FM-X4 | 字体目录不可读 / 环境无 CJK 字体 | SVG 回退链照常；PNG 记 warn；可用环境变量 `FONT_PATHS` 指定字体目录 | `environment.fonts`；`uncertainty` |
| FM-X5 | `--out` / `--work` 目录不可写 | 写最小诚实信封（`status=failed` + `error` + traceback 摘要） | `status=failed`；退出码 1 |
| FM-X6 | `templates/figure_map.schema.json` 缺失 | 脚本不依赖该文件（它只作文档/人读用途）；lint 仍按内置规则跑 | 不属于运行故障，无需落痕 |
| FM-X7 | 案例材料要求联网而环境无网络 | 本包零网络依赖；按 FM-M1 记为材料缺失并降级，不得伪造数据 | `uncertainty` |

---

### 7. 检查点速查

| CP | 名称 | 判定（全部满足才算过） |
|-|-|-|
| CP1 | 材料盘点 | `case_id` 已取 ∧ task.md 已读或已记 `uncertainty` ∧ 数据文件已发现 |
| CP2 | 抽取 | 每列语义无歧义 ∧ 实体/关系有来源 ∧ 不确定候选已记录 |
| CP3 | 规格门 | 图型/列/误差语义/显著性锚点/网络边 无 error |
| CP4 | 导出 | 每图 SVG+PNG+PDF 存在 ∧ SVG 分层含溯源 ∧ 预览可打开 |
| CP5 | 双校验 | G1–G8 全过 ∧ mapcheck 0 mismatch ∧ 确定性通过或已如实记录 |
| CP6 | 契约 | 四形态字段全回显（无 null）∧ status 自洽 ∧ `artifacts_sha256` 已记录 |

---

### 8. 交付前自查清单

- [ ] 图上每个有数据的图元 100% 能回到源数据（`mapcheck` 0 mismatch）。
- [ ] 轴标签带单位（源数据带单位时）；刻度范围覆盖数据并留白。
- [ ] 图例与系列一一对应（`legend-mapping`）。
- [ ] 显著性星号与 p 值/来源一致（转述，不自行计算）。
- [ ] 科学实体名与源材料原文一致，未"修正"拼写；不确定项已标记。
- [ ] SVG 分层、含 metadata 溯源、真实 `<text>` 未转曲；PNG/PDF 存在且可打开。
- [ ] `result.json` 契约字段齐全（四形态）+ `case_id` 正确 + status/sources/uncertainty/
      change_records 诚实；G1–G8 全过。
- [ ] 中文标签字体回退生效，或已记 `uncertainty`。
- [ ] 同输入重跑字节级稳定（含 PDF），或差异已如实记录。
- [ ] 无编造数据、无网络访问、无凭据写入。

---

### 9. 脚本与资源清单（相对 `$SKILL_DIR`）

```
SKILL.md                            本文件（决策规则 D1–D16 + 失败分支 FM-* + CP1–CP6）
README.md                           使用说明（依赖 / 安装 / 调用 / 设计 / 限制 / 维护）
TEST.md                             真机实测记录（冒烟 / 确定性 / 契约 / 异常 / 合规）
REFINEMENT-NOTES.md                 本版相对基线的逐条增改清单与 diff 定位
GITHUB_URL.txt                      公开作品链接（单行）
scripts/main.py                     编排入口：CP1→CP6，产出产物 + result.json（--case/--out）
scripts/chartkit.py                 渲染引擎（Scene → SVG/PNG/PDF + 八类校验 + PDF 确定性归一化）
scripts/extract.py                  CP2：列画像 + 实体/关系抽取（extract.json）
scripts/spec_lint.py                CP3：figure spec 结构校验（E1–E10，exit 2 = 有 error）
scripts/figcheck.py                 CP5：G1–G8 硬门 + 六类检查点
scripts/mapcheck.py                 CP5：数据↔图元双向映射 + 源值核对（容差 1e-9）
scripts/verify_rerun.py             D12：确定性再跑验证 / artifacts sha256
scripts/check_contract.py           CP6：result.json 字段覆盖自查（解析 OUTPUT_CONTRACT.md）
scripts/cjkfont.py                  中文字体发现与回退
scripts/svgtext.py                  SVG 文本转义/清理 + 防转曲检查
templates/figure_map.schema.json    图规格声明式契约
templates/result.template.json      result.json 信封模板
templates/journal_styles.json       期刊样式预设（default/nature/cell/prism/minimal/ppt）
templates/entity_glossary.json      连接规则字典 + 实体词表
references/OUTPUT_CONTRACT.md       结果契约（机器可读必需字段块 + G1–G8 + 四形态规则）
references/RUBRIC_MAP.md            五维评分（40/25/15/10/10）→ 本包落点逐条对照
references/failure-modes.md         失败模式全表（FM-M/D/R/E/C/X 六族 41 条 + 复验命令）
references/workorder-field-map.md   输入 → 字段 → 输出 映射链
references/audit-rules.md           审计规则（检查项 / 级别 / 处置）
references/encoding-spec.md         CJK / 单位 / 实体命名 / SVG 编码规范
references/typesetting-presets.md   期刊排版预设说明
examples/                           最小示例（合成输入，非正式案例）
```

调用方式（脚本自定位，任意 cwd 均可）：
```bash
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output
python "$SKILL_DIR/scripts/check_contract.py" --result /app/output/result.json --case /input/case.json
python "$SKILL_DIR/scripts/figcheck.py" --dir /app/output --case /input/case.json
python "$SKILL_DIR/scripts/mapcheck.py" --dir /app/output --case /input/case.json
python "$SKILL_DIR/scripts/verify_rerun.py" --case /input/case.json --out /app/output
```

---

### 10. 限制（如实声明，不掩饰）

- **不做统计推断**：显著性计算、拟合、检验一律不在本 Skill 范围，只转述材料已给的数值（D6）。
- **机制/通路图自动布局是启发式的**（按 group 分层 + 行内分布）；复杂通路建议在 spec
  里手给节点 x/y（D13）。
- **PDF 预览是光栅预览嵌入 PDF**（供检查用）；投稿要求的矢量可编辑源以 SVG 为准。
- **中文字体依赖运行环境**：自动扫描常见字体目录，`FONT_PATHS` 可扩展；缺字体时
  SVG 靠回退链、PNG 记 warn（D5）。
- **词表扫描只是候选提示**，不替代 Agent 对源材料的确认（D4）。
- **资源形态**：包内只含 UTF-8 文本，零二进制；所有图与预览运行时生成，
  因此包内不存在可被误当"预制答案"的成品图。

---

# 【增益层】公平对照协议与可测指标（目标维度:使用增益 25）

---
name: scientific-figure-craft
description: >
  科研数据图表生成与编辑 Skill（增益可验证版）。当输入包含科研数据表格
  （CSV/TSV/JSON）、统计结果、实验记录或生物源材料，或需要生成/编辑示意图、
  机制图、流程图、柱状图、折线图、散点图、箱线图、热图、扇区图、通路图、
  多面板组合图（关键词：figure、chart、plot、diagram、数据图、科研绘图、
  机制图、通路图、graphical abstract、SVG、可编辑图稿、制图、出图）时使用。
  本版把「加载本 Skill 到底带来了什么可测的改变」写成可复跑的对照协议
  （references/GAIN-PROTOCOL.md）：12 项机器可判定指标 + A/B 公平比较条件 +
  本包真实跑出的对照记录。执行上仍走同一条链路：读契约 → 盘点材料 → 抽取
  字段与实体 → 规格门 → 生成分层可编辑 SVG + PNG/PDF 预览 → 双校验与确定性
  再跑 → 契约落地。严格以真实文件为准，不臆造数据、不提交预制答案。
---

## 科研数据图表生成与编辑（scientific-figure-craft）· 增益可验证版

面向「玻尔产品周赛 · 北大专区 · 学术效率 · 第三期」 challenge-1bd90d8a。

本版只强化一个维度：**使用增益 25 分**。做法是把「加载后到底变好了什么」
从一句主观判断，变成**一组可复跑的测量**。

> **本包形态**：全部资源均为 UTF-8 文本（`.md/.py/.json/.txt/.csv`），**零二进制**
> ——没有 `.pptx/.png/.pdf/.svg`、没有字体文件、没有 `__pycache__`。交付的图与预览
> 一律由 `scripts/main.py` 在运行时现场生成，因此包内不存在"预制答案"。
> 所有命令以 `$SKILL_DIR`（本文件所在目录的绝对路径）为前缀，cwd 不影响执行。
> 五维评分的逐条落点见 `references/RUBRIC_MAP.md`。

---

### 0. 本版的核心主张与它的证据边界

**主张**：本 Skill 的价值可以被**测量**，而不是只能被**声称**。测量方式是：
在**同一份合成输入**上跑两种条件（基准做法 / 加载本 Skill），
用 **12 项机器可判定指标**逐项打分，并**公布全部分数，包括自己不占优的那一项**。

**测量口径（先说清，避免误读）**：

| 项 | 规定 |
|-|-|
| 输入 | 本包 `examples/case.json` + `examples/data.csv`（**合成示例**，非平台案例） |
| 条件 A | `examples/baseline_agent.py` —— 基准条件（不加载 Skill）的常规做法：matplotlib 直接出 PNG，不写溯源、不写契约 |
| 条件 B | `scripts/main.py` —— 加载本 Skill 的完整链路 |
| 指标 | 12 项（质量 8 / 审计 3 / 效率-确定性 1），每项只依赖文件字节或可复算计数 |
| 判定 | `examples/measure_ab.py`，两份条件同一套代码判定 |
| 结果 | A **1/12**，B **12/12**（逐项数字见 `references/GAIN-PROTOCOL.md` §5） |

**证据边界（必须同时读）**：

1. **条件 A 不是平台官方的基础 Agent**，而是把"通用绘图库 + 直接写脚本"这一常规做法
   **固化成可复跑代码**的参照实现。它**不刻意做差**，但它也**不是**平台上那个基础 Agent。
2. **本地合成示例上的对照数据 ≠ 平台的评分结果**。题面写明平台会用固定 3 案例、
   相同内容分别交给两种条件；本包的对照是**给评审复跑用的、口径公开的同一实验**，
   不是替平台出结论。
3. 因此本包**不声称任何"提升 x%"**。12 项指标的**通过数**是可复算的事实；
   "提升多少分"不在本包的声称范围内。

---

### 1. 适用条件与边界

**适用**：平台固定 3 个案例（数据图表生成 / 样式调整 / 标注校验 / 源数据关联 /
可编辑源文件与导出）；同时适用于任何「数据表或生物源材料 → 可编辑科研图」的请求。

**不适用**：
- 统计方法的选择、显著性计算与检验（本 Skill 只**转述**材料给的 p 值与检验名，见 §4 规则 R6）。
- 实验方案与实验路线设计。
- 替用户下科学结论。

**运行环境**：Python 3.8+ 标准库 + Pillow（渲染 PNG/PDF）。matplotlib / cairosvg /
svgwrite 均非必需。不访问网络。

---

### 2. 自定位约定

`$SKILL_DIR` = **本 SKILL.md 所在目录的绝对路径**（平台安装期为 `/skills/weekly-skill`）。
脚本内部用 `os.path.dirname(os.path.abspath(__file__))` 解析 `templates/` 与 `references/`，
所以 cwd 与技能根不一致也能跑。

```bash
# bash
SKILL_DIR=/skills/weekly-skill
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output
```
```powershell
# PowerShell：把占位符换成技能包的实际绝对路径（平台为 /skills/weekly-skill）
$SKILL_DIR = "<技能包绝对路径>"
python "$SKILL_DIR\scripts\main.py" --case \input\case.json --out \app\output
```
自定位自查（任意目录）：
```bash
python -c "import sys;sys.path.insert(0,r'<SKILL_DIR>/scripts');import chartkit;print(chartkit.skill_root())"
```

---

### 3. 输入与输出

#### 3.1 运行期输入

| 来源 | 内容 | 缺失时 |
|-|-|-|
| `/input/case.json` | `case_id`、`figures` 规格、`data` 引用、`output_contract`、`manual_confirmations` | **必需**；不可解析 → `status=failed` + 最小诚实信封，退出码 1 |
| `/input/task.md` | 任务说明 | 自动找同目录 `task.md`；仍无 → 记 `uncertainty` |
| 源数据表 | CSV / TSV / JSON | 一个都没有 → **不得** `completed` |
| 生物源材料 | `entities_file` JSON 或 `material` 文本 | 机制图按 §6 规则降级 |

`case.json` 形态兼容：顶层对象 / `{"cases":[...]}` / 数组取首项；图规格可放
`figures` / `figure` / `figure_spec`；数据可放 `data` / `data_files` / `sources`，也可自动发现。

#### 3.2 产出（`/app/output`，UTF-8）

| 文件 | 性质 | 硬要求 | 谁读它 |
|-|-|-|-|
| `figure-<id>.svg` | 可编辑分层矢量源 | `<g id="layer-*">` 分层；`<metadata id='provenance'>`；图元带 `data-*`；**文字是真实 `<text>`，永不转曲** | G5 / 指标 Q1·Q2 |
| `figure-<id>.png` / `.pdf` | 同场景预览 | 与 SVG 逐元素一致；PDF 元数据时间戳已归一化 | G6 / 指标 Q12 |
| `data_manifest.json` | 图元 ↔ 源数据映射 | 每图元登记 `column + row_index + value`（或实体 `id/cite`） | 指标 Q3·Q4·Q5 |
| `validation.json` | 标注校验清单 | 八类检查逐项 `ok/warn/fail` | G7 |
| `mapcheck_report.json` | 数据↔图元双向核对 | `mismatched=0 unmatched=0` | 指标 Q5 |
| `figcheck_report.json` | G1–G8 硬门报告 | `all_pass=true` | G1–G8 |
| `result.json` | 结构化结果信封 | 契约字段全回显（禁 null）+ 审计字段（sources/change_records/uncertainty） | 指标 Q9·Q10·Q11 |
| `/app/work/` | 中间产物 | `extract.json`、`spec_lint.json` | 人工复核 |

---

### 4. 执行链路（阶段 G0–G8，"门"是唯一的前进条件）

设计上把流程切成 **9 个阶段**，每个阶段有**明确的进入条件与退出条件**；
任何一阶段不满足退出条件，就按 §6 的规则降级或阻断，**不允许"先往下走回头再补"**。

| 阶段 | 名称 | 进入条件 | 退出条件（全部满足才进下一阶段） |
|-|-|-|-|
| **G0** | 读契约 | — | 已读 `references/OUTPUT_CONTRACT.md` 的字段块与 G1–G8；已知 `case_id` 与 `output_contract` 形态 |
| **G1** | 材料盘点 | G0 完成 | 每个源文件有 sha256 ∧ 行数与列名已记 ∧ task.md 已读或已记 `uncertainty` ∧ 至少一个数据文件存在 |
| **G2** | 抽取 | G1 完成 | 每列语义无歧义 ∧ 实体/关系有来源 ∧ 不确定候选已记录 |
| **G3** | 规格门 | G2 完成 | `spec_lint` 无 error（exit 0） |
| **G4** | 生成 | G3 完成 | 每图 SVG + PNG + PDF 齐全 ∧ SVG 分层含溯源 ∧ 预览可打开 |
| **G5** | 映射核对 | G4 完成 | `mapcheck` `mismatched=0 unmatched=0` |
| **G6** | 交付门 | G5 完成 | `figcheck` G1–G8 全过，六项标注检查无 `fail` |
| **G7** | 确定性 | G6 完成 | 同输入重跑，全部产物在归一化后逐字节一致（含 PDF） |
| **G8** | 契约落地 | G7 完成 | `check_contract` PASS（`missing=0 null=0 contract_missing=0`）∧ status 与产物自洽 |

#### 4.1 命令（每一阶段一条，可单独重放）

```bash
SKILL_DIR=/skills/weekly-skill; OUT=/app/output; WORK=/app/work; CASE=/input/case.json

# G1+G2 材料盘点与抽取
python "$SKILL_DIR/scripts/extract.py"     --case "$CASE" --out "$WORK" --json
# G3 规格门（exit 2 = 有 error，不得进入 G4）
python "$SKILL_DIR/scripts/spec_lint.py"   --spec "$CASE" --case "$CASE"
# G4 生成（exit 0=completed / 2=partial / 1=failed）
python "$SKILL_DIR/scripts/main.py"        --case "$CASE" --out "$OUT" --work "$WORK" --style nature
# G5 映射核对
python "$SKILL_DIR/scripts/mapcheck.py"    --dir "$OUT" --case "$CASE"
# G6 交付门
python "$SKILL_DIR/scripts/figcheck.py"    --dir "$OUT" --case "$CASE"
# G7 确定性（同时产出 artifacts sha256 报告）
python "$SKILL_DIR/scripts/verify_rerun.py" --case "$CASE" --out "$OUT"
# G8 契约落地
python "$SKILL_DIR/scripts/check_contract.py" --result "$OUT/result.json" --case "$CASE"
```

#### 4.2 main.py 的全部参数

`--case`（必需）· `--out` · `--work` · `--task` · `--data` · `--style`
（`default`/`nature`/`cell`/`prism`/`minimal`/`ppt`）· `--dpi` · `--note` · `--lang`（`zh`/`en`）·
`--no-pdf`。

---

### 5. 规则集（R1–R14：分支决定如何影响"可测结果"）

本版的规则表不重复叙述"遇事怎么办"，而是**每条规则都挂一个可测后果**——
这就是它与其他版本的区别：规则的存在理由，是让**指标**能通过。

| # | 规则（分支决定） | 对应指标 | 若不做，指标会怎样 |
|-|-|-|-|
| **R1** | 每个图元必须有溯源（文件/列/行，或实体 id/cite）；无法溯源则**不画**，必要时虚线占位并记 `uncertainty` | Q1 · Q3 · Q4 · Q5 | Q3 的 `data-*` 计数为 0，Q4 无 manifest，Q5 无行可核 |
| **R2** | 轴标签带单位（源数据有单位时）；刻度范围覆盖数据并留 5% 余量 | Q6 | Q6 报"declared 有、present 无" |
| **R3** | 每个系列恰有一个图例项；图例 id = 系列 id | G6 的 `legend-mapping` | G6 出 `fail` → status 不得 `completed` |
| **R4** | 科学实体名取源材料原文，**不翻译、不"优化"拼写**；不确定的保留原文 + `uncertain` | 人工可核（`data-cite`） | 实体名与原文不符，图上内容不可信 |
| **R5** | 含 CJK 的文本走 CJK 字体回退链 | G6 的 `cjk-font` | PNG 出现方框；`environment.fonts` 无 CJK 记录 |
| **R6** | 显著性星号数量与 p 值**只转述**源标注；源未给 p 值则**不画**该标注 | G6 的 `significance` | 出 `fail`（线段数与文字数不等）或凭空造统计量 |
| **R7** | 误差线语义（SE/SD/CI）以源元数据为准并写入 manifest | Q7 | Q7 报"有误差线但语义未记录" |
| **R8** | 空值不补造：跳过该点并计数；整列无值 → 报错 | `validation` 的 `null-handling` | `uncertainty` 无空值记录，与产物不符 |
| **R9** | 任何未完成维度 → `status=partial` + `uncertainty` 写明原因与复验路径 | G8 | G8 出 `fail`（虚报完成） |
| **R10** | 人工修改写 `change_records`（时间戳 + 内容）；`--note` 追加 | Q11 | Q11 计数为 0，交付无人工痕迹可查 |
| **R11** | 输出 SVG 必须分层、含 metadata 溯源块、文字不转曲 | Q1 · Q2 · G5 | Q1/Q2 为 0，G5 出 `fail` |
| **R12** | **对抗测量污染**：比较两条件时，输入文件、数据版本、导出参数必须相同且写进报告；本包侧同输入重跑必须字节级稳定 | Q12 | Q12 出差异 → `artifacts_sha256` 失去证据力（本版已修，见 §7） |
| **R13** | 源文件 sha256 + 行列数写入 `result.json.sources`；每个产物 sha256 写入 `artifacts_sha256` | Q10 | Q10 计数为 0，结果不可核验 |
| **R14** | `output_contract` 四形态（名字列表 / 名称→类型 / 嵌套 fields 列表 / 嵌套 fields 映射）全部完整回显；缺失字段按**声明容器类型**给空值，**禁 null** | G8 | G8 的 `contract_missing` > 0 |

#### 5.1 规则冲突时的优先级

1. **诚实 > 完整**：R9 压过任何"把字段填满"的冲动；R14 的禁 null 与 R9 不冲突
   （空值给**声明容器类型的空值**，不是编造内容）。
2. **可核验 > 好看**：R1 / R3 / R6 / R7 涉及"图上写了什么"，与"图面美观"冲突时一律取前者。
3. **保源 > 保预览**：R5 / R11 在渲染能力不足时，先保证 SVG 与全部 JSON 落盘。
4. **阻断 > 带病交付**：R3 / R6 的 `fail` 阻止 `completed`，必须先修 spec。

---

### 6. 失败分支的处理（按"它会让哪一项指标失败"归类）

与 §5 同构：失败分支不按"错误类型"排，而按**它打击哪一项可测能力**排。
完整的症状/检出点/处置/落痕见 `references/failure-modes.md`。

#### 6.1 打击 Q1–Q2（可编辑矢量源）

| 分支 | 触发 | 处置 |
|-|-|-|
| SVG 未生成 | 渲染异常 | 保全部 JSON 落盘，`uncertainty` 写明；`status` 降级 |
| SVG 扁平 / 无 `data-*` | G5 `layers`/`provenance` | 用本包管线重生成 |
| 文字被转曲 | G5 `real_text` | 重新生成；编辑器保存时勿选"转曲/轮廓化" |
| 含 `DOCTYPE`/外部实体 | G5 `no_xxe` | 拒绝生成含外部实体的产物 |

#### 6.2 打击 Q3–Q5（图元 ↔ 源数据闭合）

| 分支 | 触发 | 处置 |
|-|-|-|
| 图元无溯源 | R1 判定 | 不画该元素；确有必要则虚线占位 + `uncertainty` |
| manifest 与 SVG 图元数不等 | G3 判定（1:1） | 修生成逻辑后重跑；**不得手改 manifest 迁就** |
| 源表值与 manifest 值不符 | `mapcheck` 重读源表（容差 1e-9） | 定位列/行错位；**不得放宽容差** |
| 列名在表中不存在 | 列画像 + `mapcheck` | 用画像修正列名；**禁止补造列**（注意：`spec_lint` 实测**不查列存在性**，见 §8 未解决项） |
| 数值与标题语义差 10 倍以上 | 无自动判据 | `warn` 保留原值并标可疑，**不"修正"** |

#### 6.3 打击 Q6（单位与量级）

| 分支 | 触发 | 处置 |
|-|-|-|
| 轴标签无单位 | `axis-units` | 从列名括号提取，或按源元数据补 unit；补不到则记 `warn` |
| 刻度范围裁剪数据 | `range-covers-data` | 重算范围并留 5% 余量 |

#### 6.4 打击 Q7–Q8（标注与图面）

| 分支 | 触发 | 处置 |
|-|-|-|
| 误差线语义未记录 | R7 | 按源元数据写 semantics；源未标 → `uncertainty`（**不猜**） |
| 图例与系列错配 | `legend-mapping` | 自动对齐；无法对齐 → 修 spec 后重跑（`fail` 阻断） |
| 显著性缺配对 | `significance` | 修 `annotations` 使线段数 = 文字数（`fail` 阻断） |
| 刻度重叠 / 标签过长 | 字体实测 | 自动旋转 30°，记 `adjustments` |
| 图例或标注遮挡数据 | `occlusion` 真实测量 | 图例移出绘图区；网络图手给节点坐标 |
| 中文缺字（PNG） | `cjk-font` | SVG 回退链照常；PNG 记 `warn` |
| 网络边悬空 | `E8` | 不画该边并记 `warning` |

#### 6.5 打击 Q9–Q11（结果信封与审计）

| 分支 | 触发 | 处置 |
|-|-|-|
| 契约形态写坏（四形态任一） | `apply_output_contract` 类型检查 | 跳过非法项；未知类型给 `""`；**不产出的字段不做假映射**；无契约则 `output_contract_applied=false` |
| 契约声明与产物不一致 | `check_contract` exit 1 | 列出 missing/null 字段，修复后重跑 |
| 源文件读不到 sha256 | G1 | 记 `uncertainty`，不得留空 |
| 无人工修改记录 | R10 | 若确实无人工修改，保持 `change_records` 为空数组并说明；**不得编造** |

#### 6.6 打击 Q12（确定性 —— 增益可验证性的地基）

| 分支 | 触发 | 处置 |
|-|-|-|
| **PDF 两次运行字节不同** | `verify_rerun` / `artifacts_sha256` | **根因**：Pillow 写 PDF 会注入当前时间戳（`/CreationDate`、`/ModDate`）→ PDF 字节变 → sha256 变 → `artifacts_sha256` 不再是证据。**处置**：`chartkit.stamp_pdf_deterministic()` 把这两个字段（及 `/ID`）归一化为固定值，并同步修正 xref 的对象字节偏移。**本版已实现并实测通过**（见 §7） |
| 报告文件的 `dir` 字段不同 | 换输出目录重跑 | 属**环境变量**（两次运行目录不同），判定时归一化；`verify_rerun` 已作此处理 |
| 其他非时间戳差异 | `verify_rerun` 报差异 | 定位随机源（字典遍历序、浮点格式、时间戳入图）并修掉；无法消除则**如实记录** |
| Pillow 缺失 | `chartkit.HAS_PIL` | 保 SVG + 全部 JSON；PNG/PDF 记缺失并写明安装方式 |

---

### 7. 本版实测的增益记录（真实数据，含自己不占优的一项）

完整协议与逐项原始计数见 `references/GAIN-PROTOCOL.md`。此处只列**结论级**数字：

#### 7.1 12 项指标对照（合成示例，条件 A vs 条件 B）

| # | 指标 | A 基准 | B 本包 |
|-|-|-|-|
| Q1 | 可编辑矢量源（SVG 数 ≥ 图数） | ✗ 0 个 | ✓ 2 个 |
| Q2 | 分层可编辑（`layer-*` 组） | ✗ 0 | ✓ 4 |
| Q3 | 图元级溯源（`data-role` / 源属性） | ✗ 0 / 0 | ✓ 79 / 54 |
| Q4 | 机器可读映射清单 | ✗ 无 | ✓ 有 |
| Q5 | 数值可逐行回核 | ✗ 0 行 | ✓ 24 行核对 / 0 不符 |
| Q6 | 轴单位出现在产物中 | ✗ `mg/kg`、`μm³` 均缺 | ✓ 两项均在 |
| Q7 | 误差线语义已记录 | ✗ 0 条误差线 / 未记录 | ✓ 12 条 / 已记录 |
| Q8 | 多图覆盖（案例 2 张图） | ✗ 0 个 SVG | ✓ 2 个 SVG |
| Q9 | 结果信封（`result.json` 核心字段） | ✗ 无 `result.json` | ✓ 29 键 / 核心齐 |
| Q10 | 源文件 sha256 | ✗ 0 | ✓ 2/2 |
| Q11 | 变更记录 | ✗ 0 | ✓ 7 条 |
| Q12 | 同输入重跑确定性 | ✓（仅 2 个产物） | ✓（11 个产物，归一化后全一致） |
| | **合计** | **1 / 12** | **12 / 12** |

**A 唯一通过的是 Q12**，因为它的产物只有 2 个、且都不含时间戳 —— 这一项**我们不占优**，
如实列出。B 在其余 11 项全部通过，其中 Q12 是**修掉 PDF 时间戳缺陷后**才通过的：
修复前 B 在 Q12 上**也是不通过的**（pdf 字节每次都不同）。

#### 7.2 效率侧（可测的效率量）

| 量 | 实测值 | 说明 |
|-|-|-|
| 端到端耗时（2 张图 + 双校验 + 契约落地，含全部 11 产物） | **1.51 秒**（3 次：1.72 / 1.47 / 1.34 s） | 远低于平台 900 秒预算 |
| 命令数 | **1 条**主命令 + 4 条复核命令 | 复核命令可单独重放，也可整体省略（`main.py` 内部已跑） |
| 重绘轮次 | 改样式 = 改 `--style` 预设键，**不重写代码** | 三层合并（内置默认 → 预设 → spec 内联） |
| 该量**不**用于横向对比 | A 侧耗时更短（约 0.9 s），因为**它做的事更少** | 不对"谁更快"下结论：A 快是因为不产出溯源/契约/校验。**效率增益的正确读法**是"B 用 1.5 秒换取 12 项指标里的 11 项" |

> 这一条很重要：**"更快"本身不是增益**。本包不做"耗时缩短 x%"这类声称，
> 因为条件 A 的耗时少是任务做得少造成的，不是它更高效。

---

### 8. 检查清单与限制

#### 8.1 交付前逐项过

- [ ] `mapcheck` 0 mismatch（Q5）
- [ ] `figcheck` G1–G8 全过、六项标注检查无 fail（G6）
- [ ] `verify_rerun` 归一化后 `differ=0`（Q12）
- [ ] `check_contract` PASS、`null=0`（G8）
- [ ] 轴标签带单位、图例与系列对应、显著性只转述（Q6 / R3 / R6）
- [ ] 实体名与源材料原文一致，未"修正"拼写（R4）
- [ ] 中文标签字体回退生效或已记 `uncertainty`（R5）
- [ ] `result.json` 的 `sources.sha256` / `artifacts_sha256` / `change_records` / `uncertainty` 诚实（Q10 / Q11 / R9）
- [ ] 无编造数据、无网络访问、无凭据写入

#### 8.2 限制（如实声明）

- **不做统计推断**：显著性计算、拟合、检验不在范围内，只转述（R6）。
- **机制/通路图自动布局是启发式的**；复杂通路建议在 spec 手给节点坐标。
- **PDF 预览是光栅预览嵌入 PDF**；矢量可编辑源以 SVG 为准。
- **中文字体依赖运行环境**；缺字体时 SVG 走回退链、PNG 记 warn（R5）。
- **对照实验的边界**：条件 A 是本包内置的常规做法参照实现，**不是平台官方基础 Agent**；
  本地数字**不等于**平台评分（见 §0）。
- **`spec_lint.py` 不核对列存在性**（实测：引用不存在的列仍返回 `SUMMARY: VALID`、exit 0）；
  真实兜底在 G5 的 `mapcheck`（列不存在必然 mismatch）。本版**未改代码**，
  因为 CLI 与算法接口不得变动。
- **包内零二进制**；所有图与预览运行时生成，因此没有可被误当"预制答案"的成品图。

---

### 9. 资源清单（相对 `$SKILL_DIR`）

```
SKILL.md                            本文件（阶段 G0–G8 + 规则 R1–R14 + 失败分支分类 + 实测增益）
README.md                           使用说明（依赖 / 安装 / 参数 / 退出码 / 设计 / 限制 / 维护）
TEST.md                             真机实测记录（含 A/B 对照与确定性修复的前后对比）
REFINEMENT-NOTES.md                 本版相对基线的逐条增改与 diff 定位
GITHUB_URL.txt                      公开作品链接（单行）
scripts/main.py                     主入口：阶段 G0→G8 一次跑完（--case/--out）
scripts/chartkit.py                 渲染引擎（Scene → SVG/PNG/PDF + 八类校验 + PDF 确定性归一化）
scripts/extract.py                  列画像 + 实体/关系抽取（extract.json）
scripts/spec_lint.py                规格门（E1–E10；exit 2 = 有 error）
scripts/figcheck.py                 G1–G8 硬门 + 六类检查点
scripts/mapcheck.py                 数据↔图元双向映射 + 源值核对（容差 1e-9）
scripts/verify_rerun.py             确定性再跑 / artifacts sha256
scripts/check_contract.py           字段覆盖自查（解析 OUTPUT_CONTRACT.md）
scripts/cjkfont.py                  中文字体发现与回退
scripts/svgtext.py                  SVG 文本转义/清理 + 防转曲检查
examples/baseline_agent.py          ★ 条件 A：基准做法的可复跑参照实现
examples/measure_ab.py              ★ 12 项指标的 A/B 度量器
examples/case.json / data.csv / …   合成示例输入（非平台案例）
templates/*.json                    图规格 schema / 结果信封模板 / 期刊样式预设 / 实体词表
references/OUTPUT_CONTRACT.md       结果契约（机器可读字段块 + G1–G8 + 四形态）
references/GAIN-PROTOCOL.md         ★ 本版核心：公平对照协议 + 指标定义 + 实测记录
references/RUBRIC_MAP.md            五维评分 → 本包落点（增益一节指向 GAIN-PROTOCOL）
references/failure-modes.md         失败模式全表（按"打击哪项指标"归类）
references/workorder-field-map.md   输入 → 字段 → 输出 映射链
references/audit-rules.md           审计规则（检查项 / 级别 / 处置）
references/encoding-spec.md         CJK / 单位 / 实体命名 / SVG 编码规范
references/typesetting-presets.md   期刊排版预设说明
```

`references/GAIN-PROTOCOL.md` 是本版相对其他版本**独有的文件**，也是"使用增益 25 分"的
主证据：它给出协议、指标定义、判定口径与实测记录。

---

# 【机制层】机制说明与可复用资产（目标维度:创新增益 15 + 生态贡献 10）

---
name: scientific-figure-craft
description: >
  科研数据图表生成与编辑 Skill（机制与复用显性版）。当输入包含科研数据表格
  （CSV/TSV/JSON）、统计结果、实验记录或生物源材料，或需要生成/编辑示意图、
  机制图、流程图、柱状图、折线图、散点图、箱线图、热图、扇区图、通路图、
  多面板组合图（关键词：figure、chart、plot、diagram、数据图、科研绘图、
  机制图、通路图、graphical abstract、SVG、可编辑图稿、制图、出图）时使用。
  本版把支撑这条链路的四个咬合机制写成可检验的说明（references/MECHANISM.md：
  三向闭合 / 声明式规格+生成门 / 单一场景双端输出 / 契约四形态回显+确定性归一化），
  并给出可复用资产清单与三条复用路径（references/REUSE-KIT.md）。
  执行链路：读契约 → 盘点材料 → 抽取字段与实体 → 规格门 → 生成分层可编辑
  SVG + PNG/PDF 预览 → 三向核对 → 交付门 → 确定性再跑 → 契约落地。
  严格以真实文件为准，不臆造数据、不提交预制答案。
---

## 科研数据图表生成与编辑（scientific-figure-craft）· 机制与复用显性版

面向「玻尔产品周赛 · 北大专区 · 学术效率 · 第三期」 challenge-1bd90d8a。

本版只强化两个维度：**创新增益 15** 与 **生态贡献 10**。做法是把本包赖以成立的
四个机制**写清楚**（含"没有它会怎样"），并把可复用资产与复用步骤**列出来**。

> **本包形态**：全部资源均为 UTF-8 文本（`.md/.py/.json/.txt/.csv`），**零二进制**
> ——没有 `.pptx/.png/.pdf/.svg`、没有字体文件、没有 `__pycache__`。交付的图与预览
> 一律由 `scripts/main.py` 在运行时现场生成，因此包内不存在"预制答案"。
> 所有命令以 `$SKILL_DIR`（本文件所在目录的绝对路径）为前缀，cwd 不影响执行。
> 五维评分的逐条落点见 `references/RUBRIC_MAP.md`。

---

### 1. 机制主张：把"图"当可回溯的证据，而不是当输出

常规做法把图当**输出**：数据进、图出来，中间过程不留痕。
本包把图当**可回溯的证据**：每个图元都带着回到源数据的钥匙，
且这条"钥匙链"由程序闭合、由门禁判定，不靠目视确认。

这条主张落地为**四个互相咬合的机制**（详见 `references/MECHANISM.md`）：

| # | 机制 | 一句话 | 没有它会怎样（最要命的一条） |
|-|-|-|-|
| **M1** | **三向闭合** | SVG 图元的 `data-*` ↔ `data_manifest.json` ↔ **重读源表**的值，三处互为索引且由程序核对 | "这根柱子的数字来自哪一行"永远回答不了；列错位不会被发现 |
| **M2** | **声明式规格 + 生成门** | 先写可校验的图规格，过门（`spec_lint` 无 error）才进渲染 | 错误推迟到渲染阶段才爆；样式无法复用；别人无法接手你的图 |
| **M3** | **单一场景双端输出** | 一个与格式无关的 `Scene` 同时导出分层 SVG 与 PNG/PDF，逐元素同源 | 矢量与位图能画出"看起来不同"的两张图，评审不知道以哪张为准 |
| **M4** | **契约四形态回显 + 确定性归一化** | 契约四形态全兼容、禁 `null`；把渲染器注入的时间戳归一化，让 `sha256` 成为证据 | 下游拿到 `null` 要写特判；`sha256` 每次都变，于是没人拿它当证据 |

#### 1.1 为什么必须一起看（咬合图）

```
   M2 声明式规格 ──spec_lint 生成门──►  M3 单一场景 Scene
                                            │
                        ┌───────────────────┴───────────────────┐
                        ▼                                       ▼
              分层 SVG（带 data-*）                    PNG / PDF 预览
                        │                                       │
                        ▼                                       └─ M4② 元数据归一化
              data_manifest.json（M1）                              → sha256 成为证据
                        │  重读源表三向核对
                        ▼
              result.json（M4① 四形态回显 / 禁 null / 覆盖可命令化自查）
```

**拿掉任何一个，其余机制的收益都会被削弱**：M1 没了，M3 的"双端同源"就失去意义
（同源但无法回溯）；M3 没了，M1 的 `data-*` 与位图脱钩；M2 没了，错误推迟到渲染阶段；
M4 没了，前三个机制的成果无法被下游消费、也无法证明"是同一份"。

---

### 2. 适用条件与边界

**适用**：平台固定 3 个案例（数据图表生成 / 样式调整 / 标注校验 / 源数据关联 /
可编辑源文件与导出）；也适用于任何「数据表或生物源材料 → 可编辑科研图」的请求。

**不适用**：统计方法选择与显著性计算（只**转述**材料给的 p 值）；实验方案设计；
替用户下科学结论。

**运行环境**：Python 3.8+ 标准库 + Pillow（渲染 PNG/PDF）。matplotlib / cairosvg /
svgwrite 非必需（`examples/baseline_agent.py` 用 matplotlib，但那是对照工具，不是主链路）。
不访问网络。

---

### 3. 自定位约定

`$SKILL_DIR` = 本 SKILL.md 所在目录的绝对路径（平台安装期为 `/skills/weekly-skill`）。
脚本用 `os.path.dirname(os.path.abspath(__file__))` 自定位 `templates/` 与 `references/`，
**cwd 与技能根不同也能跑**。

```bash
# bash
SKILL_DIR=/skills/weekly-skill
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output
```
```powershell
# PowerShell
$SKILL_DIR = "<技能包绝对路径>"      # 平台为 /skills/weekly-skill
python "$SKILL_DIR\scripts\main.py" --case \input\case.json --out \app\output
```
自定位自查：`python -c "import sys;sys.path.insert(0,r'<SKILL_DIR>/scripts');import chartkit;print(chartkit.skill_root())"`

---

### 4. 输入与输出

#### 4.1 输入

| 来源 | 内容 | 缺失时 |
|-|-|-|
| `/input/case.json` | `case_id`、`figures` 规格、`data` 引用、`output_contract`、`manual_confirmations` | **必需**；不可解析 → `status=failed` + 最小诚实信封（6 键），exit 1 |
| `/input/task.md` | 任务说明 | 自动找同目录；仍无 → 记 `uncertainty` |
| 源数据表 | CSV / TSV / JSON | 一个都没有 → **不得** `completed` |
| 生物源材料 | `entities_file` JSON 或 `material` 文本 | 机制图按 §7 降级 |

`case.json` 形态兼容：顶层 / `{"cases":[...]}` / 数组取首项；图规格可放
`figures` / `figure` / `figure_spec`；数据可放 `data` / `data_files` / `sources`。

#### 4.2 输出（`/app/output`，UTF-8）—— 注意每项都标注了它服务于哪个机制

| 文件 | 服务于 | 硬要求 |
|-|-|-|
| `figure-<id>.svg` | M1 · M3 | 分层 `<g id="layer-*">`；`<metadata id='provenance'>`；图元带 `data-*`；**文字永远是真实 `<text>`，不转曲** |
| `figure-<id>.png` / `.pdf` | M3 · M4② | 与 SVG 逐元素同源；PDF 元数据时间戳已归一化 |
| `data_manifest.json` | **M1** | 每个图元登记 `column + row_index + value`（或实体 `id`/`cite`），与 SVG 的 `data-*` 同名对齐 |
| `validation.json` | M1 · M4 | 八类检查逐项 `ok/warn/fail` |
| `mapcheck_report.json` | **M1** | 三向核对报告：`mismatched=0 unmatched=0` |
| `figcheck_report.json` | M1 · M3 · M4 | G1–G8 硬门报告：`all_pass=true` |
| `result.json` | **M4①** | 契约四形态全回显（禁 null）+ `case_id` + 审计字段 |
| `/app/work/` | M2 | `extract.json`、`spec_lint.json` |

---

### 5. 执行链路（每一环标注它依赖哪个机制）

| 环 | 名称 | 关键动作 | 依赖机制 | 退出条件 |
|-|-|-|-|-|
| **E0** | 读契约 | 读 `references/OUTPUT_CONTRACT.md`（字段块 + G1–G8） | M4① | 已知契约形态与 `case_id` |
| **E1** | 材料盘点 | 列文件、算 sha256、记行数与列名 | — | 至少一个数据文件存在 |
| **E2** | 抽取 | 列画像 + 实体/关系抽取（`extract.py`） | M2 | 每列语义无歧义；不确定候选已记录 |
| **E3** | **规格门** | `spec_lint.py`；**exit 2 = 有 error，不得进 E4** | **M2** | `valid=true` |
| **E4** | 生成 | `main.py`：规格 → `Scene` → SVG + PNG/PDF | **M3** | 每图三形态齐全 |
| **E5** | **三向核对** | `mapcheck.py`：SVG ↔ manifest ↔ **重读源表** | **M1** | `mismatched=0 unmatched=0` |
| **E6** | 交付门 | `figcheck.py`：G1–G8 + 六项标注检查 | M1 · M3 · M4 | 无 `fail` |
| **E7** | 确定性 | `verify_rerun.py`：归一化后逐字节比较 | **M4②** | `differ=0` |
| **E8** | 契约落地 | `check_contract.py`：字段覆盖 | **M4①** | `missing=0 null=0` |

```bash
S=/skills/weekly-skill; OUT=/app/output; WORK=/app/work; CASE=/input/case.json
python "$S/scripts/extract.py"       --case "$CASE" --out "$WORK" --json      # E1+E2
python "$S/scripts/spec_lint.py"     --spec "$CASE" --case "$CASE"            # E3（门）
python "$S/scripts/main.py"          --case "$CASE" --out "$OUT" --work "$WORK" --style nature  # E4
python "$S/scripts/mapcheck.py"      --dir "$OUT" --case "$CASE"              # E5（M1）
python "$S/scripts/figcheck.py"      --dir "$OUT" --case "$CASE"              # E6
python "$S/scripts/verify_rerun.py"  --case "$CASE" --out "$OUT"              # E7（M4②）
python "$S/scripts/check_contract.py" --result "$OUT/result.json" --case "$CASE"  # E8（M4①）
```

`main.py` 参数：`--case`（必需）· `--out` · `--work` · `--task` · `--data` · `--style` ·
`--dpi` · `--note` · `--lang` · `--no-pdf`。退出码：`0`=completed / `2`=partial / `1`=failed。

---

### 6. 规则集（按"缺了它会破坏哪个机制"组织）

与常见的"遇事怎么办"列表不同，本表每条规则都标出**它保护哪个机制**——
规则的存在理由是可追溯的。

#### 6.1 保护 M1（三向闭合）的规则

| # | 规则 | 保护方式 |
|-|-|-|
| **M1-R1** | 每个图元必须有溯源（文件/列/行，或实体 `id`/`cite`）；无法溯源则**不画**，必要时虚线占位并记 `uncertainty` | 保证 manifest 里没有"无主的图元"，也保证图上没有"无源的图元" |
| **M1-R2** | `data-*` 属性名与 manifest 字段名**同名对齐**（`data-column` ↔ `source.column`） | 保证双向检索不需要翻译表 |
| **M1-R3** | 值与源表比对**容差 1e-9**，**不得放宽**；不符即 mismatch | 保证"重读源表"这一步真的有判别力 |
| **M1-R4** | 源文件 sha256 + 行列数写入 `result.json.sources` | 保证"哪一版数据"可核 |
| **M1-R5** | 科学实体名取源材料原文，不翻译、不"优化"拼写；不确定的保留原文 + `uncertain` | 保证图上文字可回到材料 |

#### 6.2 保护 M2（声明式规格 + 生成门）的规则

| # | 规则 | 保护方式 |
|-|-|-|
| **M2-R1** | 图必须由规格（`figures[]` / `figure_spec.json`）驱动，不写一次性绘图代码 | 保证"换图型/换样式"不改代码 |
| **M2-R2** | `spec_lint` 有 error **不得进入生成** | 让门真的成为门 |
| **M2-R3** | 样式三层合并（内置默认 → 预设 → spec 内联）；加期刊 = 加预设键 | 保证样式是配置而非代码 |
| **M2-R4** | 误差线语义（SE/SD/CI）以源元数据为准，源未标则记 `uncertainty`（**不猜**） | 保证规格里的语义字段有真实来源 |

#### 6.3 保护 M3（单一场景双端输出）的规则

| # | 规则 | 保护方式 |
|-|-|-|
| **M3-R1** | 渲染必须先构造与格式无关的 `Scene`，再由它导出各端 | 这是"逐元素同源"的前提 |
| **M3-R2** | SVG 必须分层（背景/坐标/数据/标注/图例）、元素 id 稳定、含 `metadata` 溯源块 | 保证可编辑性与可定位性 |
| **M3-R3** | **文字永不允许转曲**（G5 `real_text` 机器检查） | 保证交付件可再编辑 |
| **M3-R4** | 单图失败不阻塞其他图（`status=partial`）；Pillow 缺失时**保 SVG 与全部 JSON** | 保证降级不丢源 |

#### 6.4 保护 M4（契约回显 + 确定性归一化）的规则

| # | 规则 | 保护方式 |
|-|-|-|
| **M4-R1** | 契约四形态全部完整回显；缺失字段按**声明容器类型**给 `""`/`[]`/`{}`/`false`/`0`，**绝不 `null`** | 让下游不用写特判 |
| **M4-R2** | 已知别名映射到**真实产物**（`editable_source` → `editable_sources`、`field_mapping` → `"data_manifest.json"` 等），不打空 | 保证回显是"有内容"的回显 |
| **M4-R3** | 契约声明了本 Skill 不产出的字段 → **不做假映射**，给容器类型空值 + 写明原因 | 保证回显不变成编造 |
| **M4-R4** | PDF 落盘后归一化 `/CreationDate`、`/ModDate`、`/ID`，并同步修正 xref 偏移 | 让"同输入 → 同字节 → 同 sha256"成立 |
| **M4-R5** | 确定性判定只归一化**真正无法消除的环境变量**（输出目录路径、运行时间戳）；其余逐字节 | 保证归一化不是掩盖缺陷的手段 |
| **M4-R6** | `status` 与产物事实严格自洽：有 `fail`/缺口 → 不得 `completed`；无图 → `failed` | 保证信封本身不撒谎 |

#### 6.5 规则冲突优先级

1. **诚实 > 完整**：M4-R6 压过"把字段填满"；M4-R1 的禁 null 与它不冲突。
2. **可核验 > 好看**：M1-R1 · M1-R3 · M3-R3 优先于图面美观。
3. **保源 > 保预览**：M3-R4 在能力不足时先保 SVG 与全部 JSON。
4. **阻断 > 带病交付**：图例错配、显著性缺配对的 `fail` 阻止 `completed`。

---

### 7. 失败分支（按"它破坏哪个机制"分组）

完整版（含触发条件、检出点、落痕字段、复验命令）见 `references/failure-modes.md`。

| 组 | 破坏的机制 | 典型分支 | 处置要点 |
|-|-|-|-|
| **G-M1** | 三向闭合 | 图元无溯源 · manifest 与 SVG 图元数不等 · 值与源表不符 · 列名不存在 · SVG 有未登记图元 | 不画无源图元；**不得手改 manifest 迁就**；**不得放宽容差**；列不存在 → `failed_figures` |
| **G-M2** | 声明式规格 | 未知图型 · 缺必需字段 · 列引用错 · 误差语义不明 · 显著性无锚点/来源 · 网络边悬空 | 门不过不进生成；误差语义不猜；显著性无来源就不画 |
| **G-M3** | 单场景双端输出 | SVG 扁平 · 文字转曲 · 含外部实体（XXE）· PNG 损坏 · PDF 头损坏 · 画布空间不足 | 用本包管线重生成；**拒绝生成含外部实体的产物**；缺失时先保 SVG |
| **G-M4** | 契约与确定性 | 契约形态写坏 · 声明了不产出的字段 · **PDF 两次运行字节不同** · 报告 `dir` 字段不同 · `status` 与事实不符 | 契约按容器类型给空值；**PDF 元数据归一化**（见下）；`dir` 属环境变量；状态强制降级 |
| **G-X** | 横切（材料/依赖/环境） | 材料缺失/为空/扫描件/含糊 · 编码异常 · `case.json` 不可解析 · 模板缺失 · 字体缺失 · `scripts/` 不完整 · task.md 缺失或冲突 | 不猜内容；回退内置默认；保 SVG；写最小诚实信封；**不伪造数据** |

#### 7.1 G-M4 里那条最值得单独说的：PDF 时间戳

**症状**：同一输入两次运行，`figure-*.pdf` 的 `sha256` 不同 → `result.json.artifacts_sha256`
的 pdf 条目跟着变 → `verify_rerun` 报差异。

**根因（实测定位）**：Pillow 写 PDF 时注入当前时间戳 ——
`/CreationDate (D:…Z)`、`/ModDate (D:…Z)`。`cmp -l` 显示两份 PDF 仅差 **4 个字节**，
全部落在时间戳上。

**处置**：`chartkit.stamp_pdf_deterministic()` 把这三个字段（含 `/ID`）就地归一化为固定值，
`_adjust_xref_offsets()` 同步修正交叉引用表中指向新位置的对象字节偏移。
**只改元数据字节、不改页面内容。**

**实测效果**：修复前 5 个产物字节不同（两份 PDF + 两份报告 + `result.json`），
修复后分辨率的产物**全部一致**，`verify_rerun` 报 `DETERMINISTIC (identical=9 differ=0)`，
PDF 大小不变（343392 B，新旧时间戳等长），`pypdf` 仍能解析（1 页）。

**为什么归到 M4**：它直接决定 `sha256` 能不能当证据 ——
这是机制四存在的全部理由。

---

### 8. 复用（生态贡献的实质：别人能拿走什么）

**资产清单与三条复用路径见 `references/REUSE-KIT.md`**；此处只给索引：

| 想拿走多少 | 路径 | 拿走什么 | 验证标准 |
|-|-|-|-|
| 只想要可编辑科研图 | 路径一（约 10 分钟） | `chartkit` + `cjkfont` + `svgtext` + 两份模板 | SVG 存在、分层、含 `<text>`、图元带 `data-*` |
| 想要可核验的交付链路 | 路径二（约 30 分钟） | 再加 `mapcheck`/`figcheck`/`verify_rerun`/`check_contract` + 契约文档 | 四个校验器全 exit 0 |
| 想要"证明增益 + 说明机制" | 路径三（约 1 小时） | 再加 `baseline_agent`/`measure_ab` + 协议与机制模板 | 两侧都有对照报告；协议写了"不做的事" |

**复用时的十条验收清单**见 `REUSE-KIT.md` §3；
**不要带走的五项**（本包特有，带了会误导）见 `REUSE-KIT.md` §4。

---

### 9. 交付前自查

- [ ] `mapcheck` 0 mismatch（M1）
- [ ] 任取一个 `data-column`/`data-row-index` 回源表能对上（M1）
- [ ] `spec_lint` exit 0（M2）
- [ ] `figcheck` G1–G8 全过、六项标注检查无 `fail`（M1/M3/M4）
- [ ] SVG 分层、含 `metadata`、真实 `<text>` 不转曲（M3）
- [ ] `verify_rerun` 归一化后 `differ=0`（M4②）
- [ ] `check_contract` `missing=0 null=0`（M4①）
- [ ] 实体名与源材料原文一致，未"修正"拼写（M1-R5）
- [ ] 中文标签字体回退生效或已记 `uncertainty`（G-X）
- [ ] 无编造数据、无网络访问、无凭据写入

---

### 10. 限制（如实声明）

- **不做统计推断**：显著性计算、拟合、检验不在范围内，只转述材料给的数值。
- **机制/通路图自动布局是启发式的**；复杂通路建议在 spec 手给节点坐标。
- **PDF 预览是光栅预览嵌入 PDF**；矢量可编辑源以 SVG 为准。
- **中文字体依赖运行环境**；缺字体时 SVG 走回退链、PNG 记 warn。
- **`spec_lint.py` 不核对列存在性**（实测：引用不存在的列仍返回 `SUMMARY: VALID`、exit 0）。
  即"生成门"（M2）不是唯一防线；真实兜底是 M1 的三向核对（列不存在必然 mismatch）。
  本版**未改代码**（CLI 与算法接口不得变动）。
- **四个机制都有边界**：M1 只保证"可回溯"，不保证"数据本身正确"；
  M3 只保证"双端同源"，不保证"图面美观"；M4 只保证"可被机器接手且可复现"，
  不保证"契约字段的业务含义正确"。`references/MECHANISM.md` §6 给出相对
  通用绘图库 / 现成模板 / 一次性脚本的**边界对照表**。
- **包内零二进制**；所有图与预览运行时生成。

---

### 11. 资源清单（相对 `$SKILL_DIR`）

```
SKILL.md                            本文件（机制主张 + M1–M4 + 链路 E0–E8 + 规则 + 分支 + 复用索引）
README.md                           使用说明 + §6 复用步骤（三条路径的可操作版本）
TEST.md                             真机实测记录（机制逐条实测 + 复用验收实测 + 未解决项）
REFINEMENT-NOTES.md                 本版相对基线的逐条增改与 diff 定位
GITHUB_URL.txt                      公开作品链接（单行）
scripts/main.py                     主入口（E1→E8）
scripts/chartkit.py                 渲染引擎（Scene → SVG/PNG/PDF + 八类校验 + PDF 确定性归一化）
scripts/extract.py                  列画像 + 实体/关系抽取
scripts/spec_lint.py                生成门（E1–E10；exit 2 = 有 error）
scripts/figcheck.py                 G1–G8 硬门 + 六类检查点
scripts/mapcheck.py                 三向核对（SVG ↔ manifest ↔ 重读源表）
scripts/verify_rerun.py             确定性再跑 / artifacts sha256
scripts/check_contract.py           字段覆盖自查（解析 OUTPUT_CONTRACT.md）
scripts/cjkfont.py                  中文字体发现与回退
scripts/svgtext.py                  SVG 文本转义/清理 + 防转曲检查
examples/baseline_agent.py          条件 A（基准做法）的可复跑参照实现
examples/measure_ab.py              12 项机器可判定指标的 A/B 度量器
examples/case.json / data.csv / …   合成示例输入（非平台案例）
templates/*.json                    图规格 schema / 结果信封模板 / 期刊样式预设 / 实体词表
references/MECHANISM.md             ★ 本版主件：四个机制 + "没有它会怎样" + 咬合图 + 边界对照表
references/REUSE-KIT.md             ★ 本版主件：资产清单（A/B/C 分级）+ 三条复用路径 + 验收清单 + 不要带走的东西
references/GAIN-PROTOCOL.md         公平对照协议 + 指标定义 + 实测记录（B 轴资产，本版一并保留）
references/RUBRIC_MAP.md            五维评分 → 本包落点（创新与生态两节指向本版的机制/复用文件）
references/failure-modes.md         失败模式全表（按"破坏哪个机制"分组）
references/workorder-field-map.md   输入 → 字段 → 输出 映射链
references/audit-rules.md           审计规则（检查项 / 级别 / 处置）
references/encoding-spec.md         CJK / 单位 / 实体命名 / SVG 编码规范
references/typesetting-presets.md   期刊排版预设说明
```

**本版独有的三份文件**：`references/MECHANISM.md`、`references/REUSE-KIT.md`，
以及 `examples/measure_ab.py`（与 `baseline_agent.py` 配对的度量器）。
它们分别对应「创新增益 15」与「生态贡献 10」两个维度。
