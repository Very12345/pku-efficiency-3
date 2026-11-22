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

# 科研数据图表生成与编辑（scientific-figure-craft）· 决策显性化版

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

## 1. 适用条件与边界

**适用**：平台固定的 3 个案例（数据图表生成 / 样式调整 / 标注校验 / 源数据关联 /
可编辑源文件与导出），以及任何「数据表或生物源材料 → 可编辑科研图」的请求。

**不适用**（明确划出去，不越界承诺）：
- 统计方法的选择、显著性的计算与检验 —— 本 Skill 只**转述**材料已给的 p 值与检验名（D6）。
- 实验方案与实验路线设计。
- 替用户下科学结论。文字说明不能替代实际运行证据。

**运行环境**：Python 3.8+ 标准库 + Pillow（渲染 PNG/PDF）。matplotlib / cairosvg /
svgwrite 均**非必需**。不访问网络。

---

## 2. 自定位约定（本 Skill 可在任意 cwd 下运行）

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

## 3. 输入与输出

### 3.1 运行期输入

| 来源 | 内容 | 缺失时的处置 |
|-|-|-|
| `/input/case.json` | case_id、figures 规格、data 引用、output_contract、manual_confirmations | **必需**；不可解析 → `status=failed` + 最小诚实信封（FM-M5） |
| `/input/task.md` | 任务说明（要几张图、图型、目标样式、图面约束） | 缺 → 自动找同目录 `task.md`；仍无 → 记 `uncertainty`（D14） |
| 源数据表 | CSV / TSV / JSON | 一个都没有 → **不得** `completed`（CP1 判定） |
| 生物源材料 | `entities_file` JSON 或 `material` 文本（figure03 类网络/机制图） | 缺 → 机制图按 FM-M1 降级 |

`case.json` 的组织形态（脚本全部兼容）：顶层对象，或 `{"cases":[...]}`，或数组取第一项；
图规格可放 `figures` / `figure` / `figure_spec`；数据可放 `data` / `data_files` / `sources`，
也可由脚本在同目录自动发现。

### 3.2 产出（`/app/output`，一律 UTF-8）

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

## 4. 执行链路（S0–S7，六个检查点是判定门）

### S0 定位与读契约
读 `references/OUTPUT_CONTRACT.md`（字段契约 + G1–G8）与 `references/audit-rules.md`
（检查标准）；读 `/input/case.json` 记录 `case_id`、figures 列表、output_contract 形态；
读 `/input/task.md` 提炼图面约束；确认 `$SKILL_DIR`。

> **顺序不可换**：契约先读、材料后读。先读契约的作用是让后续每一步都知道「要交什么」，
> 避免画完才发现少了必需产物。

### S1 **CP1 材料盘点** —— 先看文件，再谈内容

```bash
python "$SKILL_DIR/scripts/extract.py" --case /input/case.json --out /app/work --json
```

1. 逐个列出案例材料，对每个源文件算 sha256 并记录 `dataset_version`，确认存在性与行数。
2. **禁止**：不读文件就按文件名/标签猜内容；把材料摘要当源数据用；编造列。
3. **CP1 判定**：`case_id` 已取到 ∧ task.md 已找到（或已记 `uncertainty`）∧
   数据文件至少发现一个。**任一不满足 → status 不得为 `completed`。**

### S2 **CP2 抽取实体-关系-数据**
- 数值图：逐列画像 `{列名, 语义(x/y/误差/样本量/分类), 单位(从列名括号提取), 取值范围, 空值位置}`。
- 机制/通路图：从 `entities_file` 直接装载；材料文本支持显式行语法
  `ENTITY: <id> | <label> | <group> | <cite>` 与 `REL: <from> -> <to> | <label> | <type>`；
  其余段落按 `templates/entity_glossary.json` 词表扫描，命中项标 `uncertain=true`
  —— **必须由 Agent 对照源材料原文确认后才可上图**（D4）。
- **CP2 判定**：每列语义无歧义 ∧ 每个实体/关系有来源 ∧ 不确定候选已显式记录。

### S3 **CP3 规格门（spec lint）**

```bash
python "$SKILL_DIR/scripts/spec_lint.py" --spec /input/case.json --case /input/case.json
# 退出码：0 = valid（可进入生成）；2 = 有 error（不得进入生成）；1 = 用法/文件错误
```
- **CP3 判定**：图型合法 ∧ 列存在 ∧ 误差语义常规 ∧ 显著性有锚点与来源 ∧ 网络边不悬空。
- lint 结果写入 `result.json.spec_lint` 与 `checkpoints.cp3_spec_lint`。

### S4 **CP4 生成可编辑源与渲染**

```bash
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output \
      --work /app/work [--task /input/task.md] [--style nature] [--dpi 300] [--note "人工调整"]
# 退出码：0 = completed 且 G1–G8 全过；2 = partial；1 = failed
```
- 多图按 `figures[]` 依次处理；**单图失败不阻塞其他图**（status 降为 `partial`）。
- **CP4 判定**：每张图 SVG+PNG+PDF 齐全 ∧ SVG 分层且含溯源 ∧ 预览可打开。

### S5 **CP5 双校验 + 确定性再跑**

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

### S6 **CP6 契约落地与字段覆盖复核**

```bash
python "$SKILL_DIR/scripts/check_contract.py" --result /app/output/result.json --case /input/case.json
# 退出码 0 = PASS（missing=0 null=0 contract_missing=0）；1 = 有缺口
```
- 契约四形态逐项回显；缺失字段按**声明容器类型**给 `""`/`[]`/`{}`/`false`/`0`，**绝不写 null**。
- `status` 与产物事实严格一致（G8）。视觉终检：打开 SVG/PNG 核对坐标、单位、图例、
  显著性星号、实体名拼写。
- **CP6 判定**：`output_contract_applied` ∧ `gates.all_pass` ∧ `artifacts_sha256` 已记录。

### S7 交付前逐项过自查清单
见 §8。

---

## 5. 决策规则表（D1–D16）

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

### 5.1 决策优先级（两条规则同时命中时）

1. **诚实优先于完整**：D10（如实降级）压过任何"把字段填满"的冲动；D15 的禁 null 与
   D10 不冲突——空值给**声明容器类型的空值**，不是编造内容。
2. **可核验优先于好看**：D1 / D3 / D6 / D8 四条涉及"图上写了什么"的规则，
   在任何与"图面美观"冲突的场合一律取前者。
3. **保源优先于保预览**：D5 / D7 在渲染能力不足时，先保证 SVG 与全部 JSON 落盘。
4. **阻断优先于带病交付**：D3 / D6 的 `fail` 会阻止 `completed`，必须先修 spec。

---

## 6. 失败分支表（FM 六族：M 材料 / D 数据 / R 图面 / E 导出 / C 契约 / X 依赖）

完整推理与复验命令见 `references/failure-modes.md`（**41 条**编号条目）；下表是执行时的
**速查分支表（37 条）+ §6.7 补充分支（4 条）**。两处的 FM 编号完全一致，可用
`grep -o 'FM-[MDREXC][0-9]*' SKILL.md references/failure-modes.md | sort -u` 对拍。

### 6.1 FM-M 材料分支

| 分支 | 触发条件 | 检出点 | 处置 | 落痕 |
|-|-|-|-|-|
| FM-M1 | 材料文件不存在 | CP1 盘点 | 不猜内容，明确列出缺失路径 | `status=partial`；`uncertainty` |
| FM-M2 | 材料存在但 0 行 / 空表 | `load_table` | 明示为空，该图不产出 | `failed_figures` |
| FM-M3 | 材料是扫描件 / 受保护 PDF，无法直接抽取 | extract / 平台 pdf-text-tool | 先用平台工具转文本；仍不可读 → 说明工具与限制 | `uncertainty` |
| FM-M4 | 生物源材料表述含糊，实体无法确认 | 词表扫描命中 | 候选标 `uncertain`，对照原文确认后才上图（D4） | `extract.json`；`uncertainty` |
| FM-M6 | `case.json` 不存在 / 不可解析 / `--out` 不可写 | 入口 | 写**最小诚实信封**：`case_id`+`status=failed`+`error`+traceback 摘要+`sources`+`change_records` | `result.json.status=failed`；退出码 1 |

### 6.2 FM-D 数据分支

| 分支 | 触发条件 | 检出点 | 处置 | 落痕 |
|-|-|-|-|-|
| FM-D1 | x/y/误差列名在表中找不到 | `spec_lint` E3 + 列画像 | 用画像修正列名；**禁止补造列** | `failed_figures`；修正后重跑 |
| FM-D2 | 部分格子为空 | 画像 `n_null` | 跳过该点并计数；整列无值 → 报错 | `uncertainty`（含数量） |
| FM-D3 | 数值与标题语义差 10 倍以上 | 无自动判据 | `warn` 保留原值并标可疑，**不"修正"** | `uncertainty`；`warnings` |
| FM-D4 | 轴标签没有单位 | `axis-units` | 从列名括号提取，或按源元数据补 unit | `validation.warnings` |
| FM-D5 | 分不清误差线是 SE / SD / CI | `spec.error.semantics` | 按源元数据写 semantics；源未标 → 记 `uncertainty` | `validation.json` |
| FM-D6 | `filter` 条件在表中无匹配行 | `apply_row_filter` | 报错并列出该列可用取值 | `failed_figures` |
| FM-D7 | box/pie 需要的统计量源未提供 | `presets` 直供检查 | 只用源给的最小/中位/四分位；**不代算** | 转述声明 |

### 6.3 FM-R 图面分支

| 分支 | 触发条件 | 检出点 | 处置 | 落痕 |
|-|-|-|-|-|
| FM-R1 | 刻度文字互相重叠 / 标签过长 | 字体实测 | 自动旋转 30° | `validation.adjustments` |
| FM-R2 | 图例或标注盖住数据 | `occlusion` 真实测量 | 图例移出绘图区；网络图手给节点坐标 | `validation` `occlusion` warn |
| FM-R3 | PNG 中文出现方框 / 乱码 | `cjk-font` 校验 | SVG 回退链照常；PNG 记 warn（D5） | `uncertainty`；`environment.fonts` |
| FM-R4 | 图例项与数据系列对不上 | `legend-mapping` | 自动对齐；无法对齐 → 修 spec 后重跑 | `validation` fail → 阻止交付 |
| FM-R5 | 有星号但没有对应线段（或反之） | `significance` | 修 `annotations` 使线段数与文字数相等 | `validation` fail |
| FM-R6 | 留白后画布无空间画图 | `compute_plot_area` | 报错并提示增大画布或减小边距 | `failed_figures` |
| FM-R7 | 网络关系引用了未知节点 | E8 + warnings | 不画该边并记录 warning | `validation.warnings` |

### 6.4 FM-E 导出分支

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

### 6.5 契约四形态分支（与 FM 并列，属 G2）

| 分支 | 触发条件 | 处置 | 落痕 |
|-|-|-|-|
| FM-C1 | 形态①的列表里混入非字符串项 | 跳过非法项，其余照常回显 | `output_contract_applied=true` + `uncertainty` |
| FM-C2 | 形态②/④ 声明了未知类型名 | 按字符串容器给 `""`（**绝不 null**） | 同上 |
| FM-C3 | 契约声明了本 Skill 不产出的字段 | **不做假映射**：给声明容器类型的空值，并写明"该字段本 Skill 不产出" | `uncertainty` |
| FM-C4 | 完全没有 `output_contract` | `output_contract_applied=false`，只写本 Skill 自有字段，**不臆造契约字段** | `output_contract_applied` |
| FM-C5 | 契约声明与产物不一致 | `check_contract.py` 返回 1 并列出 missing/null 字段；修复后重跑 | `check_contract` 报告 |

### 6.6 依赖与模板分支

| 分支 | 触发条件 | 处置 | 落痕 |
|-|-|-|-|
| FM-X1 | `templates/journal_styles.json` 缺失或 JSON 损坏 | **回退内置默认样式**继续出图，不中断 | `environment.style`；`uncertainty` |
| FM-X2 | `templates/entity_glossary.json` 缺失 | 回退内置"关系类型→颜色/线型"默认表；词表扫描跳过 | `uncertainty` |
| FM-X3 | `scripts/` 不完整（被单独复制走） | import 立即失败；命令非零退出并打印缺失模块，**不产出半成品 result** | 退出码 1 |

### 6.7 补充分支（速查表外的 4 条，编号与 failure-modes.md 一致）

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

## 7. 检查点速查

| CP | 名称 | 判定（全部满足才算过） |
|-|-|-|
| CP1 | 材料盘点 | `case_id` 已取 ∧ task.md 已读或已记 `uncertainty` ∧ 数据文件已发现 |
| CP2 | 抽取 | 每列语义无歧义 ∧ 实体/关系有来源 ∧ 不确定候选已记录 |
| CP3 | 规格门 | 图型/列/误差语义/显著性锚点/网络边 无 error |
| CP4 | 导出 | 每图 SVG+PNG+PDF 存在 ∧ SVG 分层含溯源 ∧ 预览可打开 |
| CP5 | 双校验 | G1–G8 全过 ∧ mapcheck 0 mismatch ∧ 确定性通过或已如实记录 |
| CP6 | 契约 | 四形态字段全回显（无 null）∧ status 自洽 ∧ `artifacts_sha256` 已记录 |

---

## 8. 交付前自查清单

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

## 9. 脚本与资源清单（相对 `$SKILL_DIR`）

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

## 10. 限制（如实声明，不掩饰）

- **不做统计推断**：显著性计算、拟合、检验一律不在本 Skill 范围，只转述材料已给的数值（D6）。
- **机制/通路图自动布局是启发式的**（按 group 分层 + 行内分布）；复杂通路建议在 spec
  里手给节点 x/y（D13）。
- **PDF 预览是光栅预览嵌入 PDF**（供检查用）；投稿要求的矢量可编辑源以 SVG 为准。
- **中文字体依赖运行环境**：自动扫描常见字体目录，`FONT_PATHS` 可扩展；缺字体时
  SVG 靠回退链、PNG 记 warn（D5）。
- **词表扫描只是候选提示**，不替代 Agent 对源材料的确认（D4）。
- **资源形态**：包内只含 UTF-8 文本，零二进制；所有图与预览运行时生成，
  因此包内不存在可被误当"预制答案"的成品图。
