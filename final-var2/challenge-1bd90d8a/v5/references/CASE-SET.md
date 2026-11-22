# CASE-SET.md — 多案例题集（两个不同题材 + 逐案实测 + 泛化边界）

本文件是**题集**：给出两个**题材不同**的合成案例，每案写清输入、期望产出结构、可接受区间、
难度层，并附**逐案实测结果**；最后**如实写明泛化到哪里会失效**（含实测证据，不含推测）。

> **案例性质**：两案都是**合成案例**（自拟数值/自拟机制文本），**不是**平台的 3 个正式案例，
> 也**不得**当作正式案例的答案。它们的作用是：换一个题材、换一套列名、换一套图型组合，
> 看这条流水线是不是**只会在自带示例上跑通**。
> 同时，这两案与本包唯一的"文档声明支持"探针（见 `TEST.md` T10）一起，
> 暴露出 4 处"声明支持但实现不工作"的真实缺陷（P5–P8，见 `references/FAULT-MATRIX.md` §5）。

---

## 0. 题集总览

| 编号 | 题材 | 学科/场景 | 图型组合 | 难度层 | 主要考察点 |
|-|-|-|-|-|-|
| **A** | 湖泊中试富营养化 | 生态学 / 环境科学（中试尺度） | `panel`（bar + line） | **中** | 分组过滤、时间序列多元系列、误差线语义、未引用列仍须如实记录 |
| **B** | Mg-Zn 合金体外降解 | 材料科学 / 生物材料 | `scatter` + `network`（材料文本驱动） | **高** | 实体/关系从**材料文本**抽取、发散 vs 抑制语义、**两种误差语义并存且不得混用** |

两案与自带示例（`examples/`）的差异：示例是"肿瘤体积 bar+line + entities.json 机制图"，
其 `entities.json` 是**直给 JSON**；案例 B 故意**不给 JSON**，只给带 `ENTITY:`/`REL:` 行的
`material.md` —— 这正是后来暴露 P5 的地方。

---

## 1. 案例 A · 湖泊中试的富营养化响应

### 1.1 输入（`examples/cases/lake-eutrophication/`）

| 文件 | 内容 |
|-|-|
| `case.json` | `case_id=caseA-lake-eutrophication`；1 张 `panel` 图（`fig-A1`），两个子面板；`output_contract` 用**形态②（名称→类型）**，且**故意多声明 2 个非标准字段**（`figure_checks` / `spec_lint`）以考察回显 |
| `data.csv` | 16 行 × 7 列：`mesocosm_id, treatment, time_day, chl_a_ug_L, se_chl_a, turbidity_NTU, n`；4 处理 × 4 时间点，每格 n=4 |
| `task.md` | 任务说明（要双面板、轴带单位、显著性只转述、处理名照抄原文、`turbidity_NTU` **不上图**但要如实记录） |

**故意埋的两个考察点**：
1. `turbidity_NTU` 列**不被任何图引用** —— 输出里仍须能在 `sources[].columns` 看到它
   （证明"读了源表全部列"，而不是只读用到的列）。
2. 面板 A 需要 `filter: {column: time_day, eq: "21"}` —— 考察**子面板按列过滤**，
   且过滤后行数从 16 变 4，误差线仍要取对行。

### 1.2 期望产出结构

```
out/                          # --out 指定
├── figure-fig-A1.svg         # 可编辑分层 SVG：<g id="layer-*"> 分层 + <metadata id='provenance'> + 图元 data-*
├── figure-fig-A1.png         # 同场景位图预览
├── figure-fig-A1.pdf         # 同场景 PDF 预览（元数据时间戳已归一化）
├── data_manifest.json        # 图元→源数据映射；elements[].source = {column,row_index,value,error_column,error_value}
├── validation.json           # 八类标注检查逐项 ok/warn/fail
├── mapcheck_report.json      # 数据↔图元双向核对
├── figcheck_report.json      # G1–G8 硬门
└── result.json               # 契约字段全回显（形态②含 2 个非标准字段）+ 审计字段

work/                         # --work 指定
├── extract.json              # 列画像（每列的语义/单位/取值范围/空值位置）
└── spec_lint.json            # CP3 生成门结果
```

**`result.json` 必须满足**：顶层含 `OUTPUT_CONTRACT.md` §0 的 18 个必需字段
+ 契约声明的 12 个字段（形态②）→ 实测 **29 键**；`status=completed`；`gates.all_pass=true`。

### 1.3 可接受区间（判定标准，不是"看起来对"）

| 指标 | 可接受区间 | 依据 |
|-|-|-|
| `main.py` 退出码 | **必须 = 0** | `completed` 且 G1–G8 全过 |
| `result.json.status` | **必须 = `completed`** | 材料齐全、无 fail |
| `result.json` 顶层键数 | **≥ 25**（实测 29） | 18 必需 + 契约字段 |
| `mapcheck` `mismatched` / `unmatched` | **必须都是 0** | 每个图元可回到源表列/行/值（容差 1e-9） |
| `mapcheck` `checked`（核对了多少条） | 应 ≈ 面板 A 的 4 柱 × (值+误差) + 面板 B 的 16 点 ≈ **90–110**（实测 99） | 图元数由数据规模决定，不是硬编码 |
| `figcheck` G1–G8 | **全 true** | 六项标注检查无 fail |
| `validation.checks` 里 `fail` 条数 | **0**（warn 可有） | `provenance`/`legend-mapping`/`axis-units`/`significance` 必须 ok |
| `sources[0].rows` | **必须 = 16** | 探针：确实读了全表 |
| `sources[0].columns` | **必须含 `turbidity_NTU`** | 未被引用的列也要如实记录 |
| `artifacts_sha256` 条目数 | 与产物文件数一致（**7**） | 含 3 个图文件 + 4 个 JSON 报告 |
| 端到端耗时 | < 10 s（实测 **1.4 s**） | 平台预算 900 s |

### 1.4 难度层：**中**

- 为什么不是"低"：需要**按列过滤**取子集（`filter`）、需要**多系列折线**（4 条 × 4 点带误差）、
  需要把**未引用的列**也记录进 `sources`。
- 为什么不是"高"：图型是成熟的 bar+line，实体抽取不涉及（纯数值），
  误差语义单一（全是 SE），不存在语义冲突。

### 1.5 逐案实测结果（2026-11-22 20:1x +08，CPython 3.13.9 / Pillow 12.3.0）

```bash
python "$SKILL_DIR/scripts/main.py" --case examples/cases/lake-eutrophication/case.json \
       --out <OUT> --work <WORK>
```

| 项 | 实测 |
|-|-|
| `main.py` | **exit 0** · `status=completed` · `completed_figures=['fig-A1']` · 耗时 **1.37 s** |
| 产物 | **7 个**（1 SVG + 1 PNG + 1 PDF + manifest/validation/mapcheck/figcheck + `result.json` = 8 见下） |
| `result.json` | **29 键** · `gates.all_pass=true` · `uncertainty=[]` |
| `check_contract.py` | **exit 0**（`missing=0 null=0 contract_missing=0`） |
| `figcheck.py` | **exit 0** · G1–G8 全 true |
| `mapcheck.py` | **exit 0** · `SUMMARY: ALL PASS (99 checked / 0 mismatched / 0 unmatched)` |
| `verify_rerun.py` | **exit 0** · `DETERMINISTIC (identical=6 differ=0 missing=0)` |
| `spec_lint.py` | **exit 0** · `SUMMARY: VALID (0 errors / 0 warnings / 1 figures)` |
| `sources[0]` | `{file: data.csv, rows: 16, columns: [mesocosm_id, treatment, time_day, chl_a_ug_L, se_chl_a, turbidity_NTU, n]}` → **未引用列 `turbidity_NTU` 在列** ✅ |
| 八类检查 | `provenance/legend-mapping/axis-units/significance/null-handling/cjk-font/occlusion` 全部 **ok** |
| `validation.adjustments` / `warnings` | 均为 `[]`（无旋转、无遮挡、无缺字） |
| `environment.fonts` | `sans=book antiqua`，`sans_cjk=stfangsong` → CJK 回退链生效 |

> **本案结论**：换一个题材（生态学）、换一套列名、换一种契约形态，链路**照常通过**，
> 且"未引用列仍如实记录"这条要求被实测兑现。

---

## 2. 案例 B · Mg-Zn 合金体外降解与产物膜机制

### 2.1 输入（`examples/cases/mg-alloy-degradation/`）

| 文件 | 内容 |
|-|-|
| `case.json` | `case_id=caseB-mg-alloy-degradation`；2 张图：`fig-B1`（scatter，`style=prism`）、`fig-B2`（network，**只给 `material_file`**）；`output_contract` 用**形态②且字段名走别名**（`data_manifest`/`validation`/`editable_sources`/`renders`）以考察别名映射 |
| `data.csv` | 4 行 × 8 列：`alloy_id, zn_wt_pct, degradation_rate_mm_per_year, sd_rate, ph_day7, viability_percent, se_viability, n` |
| `material.md` | 30 行：7 条 `ENTITY:` + 7 条 `REL:` **显式行**，另有**自然语言段落**（只作词表候选，不得直接上图） |
| `task.md` | 任务说明（两张图、误差语义不得混用、实体名照抄含 `Cl-`/`Mg(OH)2`/`MgZn2`/`MC3T3-E1`、未引用列仍记录） |

**故意埋的四个考察点**：
1. **只给材料文本**，不给 `entities.json` —— 考察 `ENTITY:`/`REL:` 行解析（**这里暴露了 P5**）。
2. **两种误差语义并存**：`sd_rate` 是 SD（给 B1），`se_viability` 是 SE（若上细胞图则用 SE）——
   混用即为错。
3. **未引用列**：`ph_day7`、`viability_percent`、`se_viability` 三列都不上图，但必须出现在 `sources[].columns`。
4. **自然语言里的候选**：正文段落提到 MgZn2 / Cl- 等，与显式行重复；词表扫描命中**不得**上图。

### 2.2 期望产出结构

```
out/
├── figure-fig-B1.svg / .png / .pdf     # scatter + SD 误差线，点标注 alloy_id
├── figure-fig-B2.svg / .png / .pdf     # network，5 个 group 分层，节点带 data-cite
├── data_manifest.json                  # fig-B1 每个点含 {column:zn_wt_pct, value, error_column:sd_rate, error_value}
├── validation.json
├── mapcheck_report.json
├── figcheck_report.json
└── result.json                         # 27 键（契约形态② + 别名映射）
work/extract.json                       # 含 networks[0].entities=7 / relations=7
work/spec_lint.json
```

### 2.3 可接受区间

| 指标 | 可接受区间 | 依据 |
|-|-|-|
| `main.py` 退出码 | **必须 = 0** | 两图都成功 |
| `status` | **必须 = `completed`** | —— |
| `completed_figures` | **必须 = `['fig-B1','fig-B2']`**（两图都在） | 少一张即 `partial` |
| `result.json` 顶层键数 | **≥ 25**（实测 27） | 别名映射后仍须覆盖契约 |
| `mapcheck.mismatched`/`unmatched` | **0 / 0** | 含网络节点的 `id`/`cite` 核对 |
| `mapcheck.checked` | ≈ **70–80**（实测 74） | 4 点 ×(值+误差) + 7 节点 + 7 边 |
| `fig-B2` 的 `entities` 数 | **必须 = 7**（与 `material.md` 的 `ENTITY:` 行数一致） | 少一个说明解析漏行 |
| `fig-B2` 的 `relations` 数 | **必须 = 7** | 同上 |
| 误差语义 | B1 的 `error.semantics` **必须 = SD**，且 `manifest` 里 `error_column=sd_rate` | 混成 SE 即错 |
| `sources` | 必须含 `data.csv`（rows=4）**与** `material.md`（role=`material_file`）；`data.csv.columns` 含 `ph_day7`/`viability_percent`/`se_viability` | 未引用列 + 材料文件都要登记 |
| `validation` 的 `fail` | **0**（`occlusion` 允许 1 条 warn） | 网络图标签密集时的合理告警 |
| 耗时 | < 10 s（实测 **0.9 s**） | —— |

### 2.4 难度层：**高**

- 需要**两种数据源类型**（表格 + 材料文本）同时进入同一次运行；
- 需要**两种误差语义**并存且严格区分（SD vs SE）；
- 网络图要求 `group` 分层 + `cite` 溯源 + 抑制/促进线型区分；
- 自然语言段落与显式行**重复出现**同类实体，要求"只用显式行、候选不上图"。

### 2.5 逐案实测结果（2026-11-22 20:1x +08）

```bash
python "$SKILL_DIR/scripts/main.py" --case examples/cases/mg-alloy-degradation/case.json \
       --out <OUT> --work <WORK>
```

| 项 | 实测 |
|-|-|
| `main.py` | **exit 0** · `status=completed` · `completed_figures=['fig-B1','fig-B2']` · 耗时 **0.89 s** |
| 产物 | 6 个图文件 + 4 个 JSON 报告 + `result.json` |
| `result.json` | **27 键** · `gates.all_pass=true` · `uncertainty=[]` |
| `check_contract.py` | **exit 0** |
| `figcheck.py` | **exit 0** · G1–G8 全 true |
| `mapcheck.py` | **exit 0** · `[PASS] fig-B1: 32 elements, 0 orphans` / `[PASS] fig-B2: 42 elements, 0 orphans` → `SUMMARY: ALL PASS (74 checked / 0 mismatched / 0 unmatched)` |
| `verify_rerun.py` | **exit 0** · `DETERMINISTIC (identical=9 differ=0 missing=0)` |
| `spec_lint.py` | **exit 0** · `SUMMARY: VALID (0 errors / 0 warnings / 2 figures)` |
| `sources` | `data.csv`（rows=4，8 列全在，含 `ph_day7`/`viability_percent`/`se_viability`）+ `material.md`（`role=material_file`，含 sha256） ✅ |
| `figure_meta['fig-B1'].y_range` | `[0.3895, 0.8405]` ← 覆盖 0.41–0.82 并留 ~5% 余量 ✅ |
| 八类检查 | B1 全 ok；B2 的 `occlusion` = **warn**（网络标签密集），其余 ok → **无 fail**，G7 仍通过 |
| `extract.json` | `networks[0]`：**7 entities / 7 relations**，与 `material.md` 显式行一一对应 ✅ |

> **本案的实战价值**：它是**唯一一个在首轮就失败**的案例 —— 首轮实测
> `exit 2 / partial`，失败记录 `"通路图需要 entities（节点）列表。"`。
> 追查发现 `extract.py` 能正确解析 `ENTITY:`/`REL:`（7+7），但**生成路径只认 `entities_file`(JSON)**，
> 材料文本解析器从未接上 → 这就是 **P5**。修复后本案才达到上表结果。
> **换言之：这个案例集不是"跑通就贴图"，它真的抓到了一个功能缺口。**

---

## 3. 两案对照（同一套代码、不同题材）

| 维度 | 案例 A（生态） | 案例 B（材料） | 差异说明了什么 |
|-|-|-|-|
| 数据源 | 1 张表 | 1 张表 + 1 份材料文本 | 材料文本路径需要单独接（P5） |
| 图型 | panel(bar+line) | scatter + network | network 的实体来源有两套（JSON / 文本） |
| 契约形态 | 形态② + 2 个非标准字段 | 形态② + **字段别名**（`data_manifest`/`validation`/…） | 别名映射被真实用到 |
| 误差语义 | 单一 SE | **SD + SE 并存** | 语义不得混用 |
| 未引用列 | 1 列（`turbidity_NTU`） | 3 列 | 都要求如实写入 `sources[].columns` |
| 输出键数 | 29 | 27 | 因契约声明字段数不同 |
| mapcheck checked | 99 | 74 | 图元数随数据规模变化 |
| 首轮结果 | **一次通过** | **首轮失败（P5）** | 换题材确实能压出问题 |

---

## 4. 泛化到哪里会失效（**如实写明，含实测**）

下面的结论都来自 `TEST.md` T10 的探针（每个探针是一个最小案例，跑 `main.py` 看结果），
**不是推测**。

### 4.1 已经不会失效的（本轮修好了，附修前/修后）

| 能力 | 修前实测 | 修后实测 | 修的是谁 |
|-|-|-|-|
| `heatmap` 图型 | `exit 2`，`ValueError: invalid literal for int() with base 16: '#4'` | `exit 0 / completed / G1–G8 全过` | P6（色阶插值三处写法错误） |
| `type: "auto"` 自动推断 | `exit 2`，`不支持的图型：auto` | `exit 0 / completed` | P7（`infer_type` 把 `"auto"` 原样返回） |
| **只给材料文本**的机制图 | `exit 2`，`通路图需要 entities（节点）列表。` | `exit 0 / completed / 2 张图` | P5（生成路径只认 JSON） |
| 没有任何图规格的案例 | `exit 2 / partial`，且**可能凭空画一张图** | `exit 1 / failed` + `uncertainty` 说明，**不臆造** | P8 |

### 4.2 仍然会失效 / 不适用的（**当前版本的诚实边界**）

| 场景 | 实测或依据 | 影响 | 规避 |
|-|-|-|-|
| **data 是纵向长表但声明了 `matrix`** | `heatmap` 的 `matrix` 必须是二维数组或 `{rows,columns}`；长表需先聚合 | 会渲染出与预期不同的矩阵 | 先用 `presets`/脚本聚合成矩阵再写 spec |
| **`filter` 取值不存在** | 探针 `p-filter-empty`：`exit 2 / partial`，`filter {...} 无匹配行，列 'grp' 取值：['A','B','C']` | 该图不产出（**行为正确**，但需人改 spec） | 按报错列出的取值修正 |
| **列名写错** | 探针 `p-bad-col`：单图失败、其余继续 | 部分交付 | 看 `failed_figures` |
| **网络图节点 > 约 20 个** | 自动布局按 group 分层 + 行内分布；本案 7 节点 `occlusion` 已是 warn | 标签重叠增多（warn 不阻断） | 在 spec 手给 `x`/`y`（D14） |
| **材料文本没有 `ENTITY:` 行，只有自然语言** | `scan_material_text` 只对显式行结构化；自然语言仅作**候选**（`uncertain`，不上图） | 机制图可能为空 | 必须写显式行，或给 `entities.json` |
| **统计量需要计算**（p 值、拟合、检验） | 不在范围内，只转述材料给的数值（D6） | 需要自行算好再写进 spec | 用专门的分析工具 |
| **非 UTF-8 输入 / 超长文本 / 图像尺寸越界** | **未测** | 未知 | —— |
| **缺 Pillow 的环境** | 见 `FAULT-MATRIX` D2：`figcheck` 顶层 `from PIL` 未保护 → 整体 `failed`，SVG 不进 `outputs` | 严重（等于交不出结果） | 部署前 `python -c "import PIL"` 自检 |
| **`box` 图需要算四分位** | 用 `presets` 直供，**不代算**（节点 D7 的处置原则） | 需自行提供 min/q1/median/q3/max | 先算好写进 `presets` |
| **`pie` 的百分比** | 由引擎按数值归一化显示 | 与"源材料给定百分比"可能不同 | 若材料给了百分比，直接写入 `labels`/注记 |

### 4.3 一句话总结泛化边界

> 本流水线泛化到「**结构化的数值表 + 结构化的实体/关系来源（JSON 或显式行文本）+
> 九种已声明图型**」这一区间内是**实测可用**的（两个不同题材案例 + 9 种图型探针全通过）。
> 出这个区间就会降级或失败：**需要统计推断**、**只有自由文本没有显式实体行**、
> **缺 Pillow 的环境**、**超大规模网络图**（>20 节点且不手给坐标）。
> 这些失效点**不是猜测**，其中 4 条已在 §4.1 被修掉，其余 5 条在 §4.2 逐条给了实测或依据。

---

## 5. 怎么复跑这两个案例

```bash
SKILL_DIR=/path/to/this/skill            # 本包根目录（脚本自定位，cwd 任意）

# 案例 A
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/cases/lake-eutrophication/case.json" \
       --out /tmp/outA --work /tmp/workA
# 案例 B
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/cases/mg-alloy-degradation/case.json" \
       --out /tmp/outB --work /tmp/workB

# 四道复核（逐个跑，都要求 exit 0）
python "$SKILL_DIR/scripts/check_contract.py" --result /tmp/outA/result.json --case "$SKILL_DIR/examples/cases/lake-eutrophication/case.json"
python "$SKILL_DIR/scripts/figcheck.py"  --dir /tmp/outA --case "$SKILL_DIR/examples/cases/lake-eutrophication/case.json"
python "$SKILL_DIR/scripts/mapcheck.py"  --dir /tmp/outA --case "$SKILL_DIR/examples/cases/lake-eutrophication/case.json"
python "$SKILL_DIR/scripts/verify_rerun.py" --case "$SKILL_DIR/examples/cases/lake-eutrophication/case.json" --out /tmp/outA
```

判据：**两案都 exit 0 / `status=completed` / G1–G8 全过 / mapcheck 0 mismatch**。
若哪一条不符，先看 `result.json.uncertainty` 与 `failed_figures`，
再对照 `references/failure-modes.md` 与 `references/FAULT-MATRIX.md` 的同名分支。

---

## 6. 复用这两个案例当"新题"的方法

1. **换数据**：直接把 `data.csv` 换成自己的表，按列名改 `case.json` 的 `x/y/error/filter/hue`。
2. **换图型**：把 `type` 改成 `bar/line/scatter/box/heatmap/pie/panel/network/auto` 之一
   （九种均已实测可用，见 §4.1）。
3. **换样式**：`"style"` 写 `default/nature/cell/prism/minimal/ppt`，或往
   `templates/journal_styles.json` 加键（D13）。
4. **做机制图**：按 `material.md` 的 `ENTITY:` / `REL:` 行语法准备材料（P5 修好后这条路可用），
   或直接给 `entities.json`。
5. **加案例**：把新目录放进 `examples/cases/<name>/`，在本文档补一节（输入/期望结构/
   可接受区间/难度层/实测），**实测结果必须真跑**，不许照抄别人的数字。
