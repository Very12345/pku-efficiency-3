---
name: scientific-figure-craft
description: >
  科研数据图表生成与编辑 Skill（多案例泛化与题集版）。当输入包含科研数据表格
  （CSV/TSV/JSON）、统计结果、实验记录或生物源材料，或需要生成/编辑示意图、
  机制图、流程图、柱状图、折线图、散点图、箱线图、热图、扇区图、通路图、
  多面板组合图（关键词：figure、chart、plot、diagram、数据图、科研绘图、
  机制图、通路图、graphical abstract、SVG、可编辑图稿、制图、出图）时使用。
  本版把"只会在自带示例上跑通"这件事当作头号风险，因此自带两个**题材不同**的
  合成案例（生态学湖泊中试 panel 图 / 材料科学 Mg-Zn 合金 scatter+network 图）
  组成题集，逐案给出输入、期望产出结构、可接受区间、难度层与**实测结果**，
  并逐条写明泛化到哪里会失效（references/CASE-SET.md）。两个案例与九种图型探针
  共查出 4 处"文档声明支持但实现不工作"的缺陷（heatmap 全废 / auto 从未生效 /
  material_file 接不上 / 无规格时凭空造图），全部已修并留实测对照。
---

# 科研数据图表生成与编辑（scientific-figure-craft）· 多案例泛化与题集版

面向「玻尔产品周赛 · 北大专区 · 学术效率 · 第三期」 `challenge-1bd90d8a`（figures 组）。

> **本包形态**：只含 UTF-8 文本资源（`.md/.py/.json/.txt/.csv`），**零二进制**
> （无 `.pptx/.png/.pdf/.svg`、无字体文件、无 `__pycache__`）；所有图与预览由
> `scripts/main.py` 运行时生成。命令一律用 `$SKILL_DIR` 自定位，cwd 不影响执行。
> 五维评分（实际效果 40 / 使用增益 25 / 创新增益 15 / 可靠体验 10 / 生态贡献 10）
> 的逐条落点见 `references/RUBRIC_MAP.md`。

**本版的主张**：一个只在自己自带示例上跑通的 Skill，等于**什么都没证明**。
所以本版做了一个题集：**两个题材不同的案例**，用同一套代码跑，把每案的
输入 / 期望结构 / 可接受区间 / 难度层 / 实测结果都写下来，
再**逐条交代泛化边界**（`references/CASE-SET.md`）。

---

## 1. 先看结论：题集压出了什么

跑题集不是"再跑一遍确认没问题"，它**真的压出了问题**——4 处"文档写了、代码没做"：

| # | 问题 | 由谁暴露 | 修前实测 | 修后实测 |
|-|-|-|-|-|
| **P5** | network 只给 `material_file`（材料文本 `ENTITY:`/`REL:` 行）时**必然失败** —— `extract.py` 早就实现了解析，但生成路径只认 `entities_file`(JSON) | 案例 B | `exit 2 / partial`，`通路图需要 entities（节点）列表。` | `exit 0 / completed / 2 张图 / G1–G8 全过` |
| **P6** | **`heatmap` 在任何输入下都失败**（色阶插值三处写法错误：`int("#4",16)`、井号重复、浮点套 `02x`） | 图型探针 | `exit 2`，`ValueError: invalid literal for int() with base 16: '#4'` | `exit 0 / completed`，色阶 `#440154…#fde725` |
| **P7** | **`type: "auto"` 从来没生效**（`infer_type` 把字面量 `"auto"` 原样返回） | 图型探针 | `exit 2`，`不支持的图型：auto` | `exit 0 / completed` |
| **P8** | 案例没有任何图规格时会**凭空画一张占位图**（P7 修好后暴露的编造风险） | 图型探针 | 可能报 `completed` 且画出案例没要求的图 | `exit 1 / failed` + `uncertainty`，磁盘无 `figure-*` |

四条全部是**纯增量修法**（新增分支 / 改正一行），CLI 参数与退出码语义未变。
逐条证据（含探针输入、实测输出、改了哪几行）见 `references/FAULT-MATRIX.md` §5。

> **诚实声明**：这四条不是"读代码猜出来的"，是**跑出来的**。反过来说，
> 它们能存在这么久，恰恰说明**之前的测试只覆盖了 happy path**。
> 这是本版把"题集"当作交付物而不是当作举例的原因。

---

## 2. 适用条件与边界

**适用**：平台固定 3 个案例维度（数据图表生成 / 样式调整 / 标注校验 / 源数据关联 /
可编辑源文件与导出）；也适用于任何「数据表或生物源材料 → 可编辑科研图」的请求。
**九种图型**（`bar/line/scatter/box/heatmap/pie/network/panel/auto`）均已实测可用（§6）。

**不适用**：统计方法的选择与显著性计算（只**转述**材料给的 p 值与检验名）；
实验方案设计；替用户下科学结论。

**运行环境**：Python 3.8+ 标准库 + Pillow（渲染 PNG/PDF 预览）。
matplotlib / cairosvg / svgwrite 均非必需。不访问网络。

> ⚠️ **部署前自检**：`python -c "import PIL; print(PIL.__version__)"`。
> 缺 Pillow 时渲染层会优雅降级，但**校验层**（`figcheck.py`）会抛 `ImportError`
> 并把整次运行打成 `failed`（已登记缺陷，见 `references/FAULT-MATRIX.md` D2）。

---

## 3. 自定位约定

`$SKILL_DIR` = **本 SKILL.md 所在目录的绝对路径**（平台安装期为 `/skills/weekly-skill`）。
脚本用 `os.path.dirname(os.path.abspath(__file__))` 解析 `templates/`、`references/`，
**cwd 与技能根不同也能跑**（题集的每次实测都从包外目录启动验证了这一点）。

```bash
# bash
SKILL_DIR=/skills/weekly-skill
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output
```
```powershell
# PowerShell
$SKILL_DIR = "<技能包绝对路径>"        # 平台为 /skills/weekly-skill
python "$SKILL_DIR\scripts\main.py" --case \input\case.json --out \app\output
```
自定位自查：`python -c "import sys;sys.path.insert(0,r'<SKILL_DIR>/scripts');import chartkit;print(chartkit.skill_root())"`

---

## 4. 输入与输出

### 4.1 输入

| 来源 | 内容 | 缺失时 |
|-|-|-|
| `/input/case.json` | `case_id`、`figures` 规格、`data` 引用、`output_contract`、`manual_confirmations` | **必需**；不存在/不可解析 → 6 键最小诚实信封 + exit 1 |
| `/input/task.md` | 任务说明 | 自动找同目录；仍无 → 记 `uncertainty` |
| 源数据表 | CSV / TSV / JSON | 一个都没有 → `partial` + exit 2，点名缺失 |
| 生物源材料 | `material` 文本（`ENTITY:`/`REL:` 显式行）或 `entities_file` JSON | 机制图降级，并在 `uncertainty` 说明 |

`case.json` 形态兼容：顶层对象 / `{"cases":[...]}` / 数组取首项；
图规格可放 `figures` / `figure` / `figure_spec`；数据可放 `data` / `data_files` / `sources`。

### 4.2 输出（`/app/output`，UTF-8）

| 文件 | 硬要求 |
|-|-|
| `figure-<id>.svg` | 分层 `<g id="layer-*">`；`<metadata id='provenance'>`；图元带 `data-*`；**文字永远是真实 `<text>`，不转曲** |
| `figure-<id>.png` / `.pdf` | 与 SVG 逐元素同源；PDF 元数据时间戳已归一化 |
| `data_manifest.json` | 每图元登记 `column + row_index + value`（或实体 `id`/`cite`），与 SVG `data-*` 同名对齐 |
| `validation.json` | 八类标注检查逐项 `ok/warn/fail` |
| `mapcheck_report.json` / `figcheck_report.json` | 双向核对 / G1–G8 硬门 |
| `result.json` | 契约字段全回显（四形态，禁 null）+ 审计字段 |
| `/app/work/` | `extract.json`、`spec_lint.json` |

---

## 5. 执行链路（CP1–CP6）

| 步 | 动作 | 题集里的实测表现 |
|-|-|-|
| **CP1** | 盘材料：列文件、算 sha256、记行数列名 | 案例 A：`sources[0].rows=16`、7 列全记（含**未被任何图引用的** `turbidity_NTU`）；案例 B：`data.csv` 8 列全记 + `material.md` 以 `role=material_file` 入 `sources` |
| **CP2** | 抽取：列画像 + 实体/关系（`extract.py`） | 案例 B 的 `extract.json` 给出 **7 实体 / 7 关系**，与 `material.md` 的显式行一一对应 |
| **CP3** | 规格门：`spec_lint.py`（exit 2 = 有 error） | 两案均 `SUMMARY: VALID (0 errors / 0 warnings)` |
| **CP4** | 生成：`main.py` → Scene → SVG + PNG/PDF | 案例 A 1 张图（panel × 2 子面板）；案例 B 2 张图（scatter + network） |
| **CP5** | 双校验 + 确定性 | A：`99 checked / 0 mismatched / 0 unmatched`、`DETERMINISTIC (identical=6 differ=0)`；B：`74 checked / 0 mismatched / 0 unmatched`、`identical=9 differ=0` |
| **CP6** | 契约落地：`check_contract.py` | A：**29 键**（形态②含 2 个非标准字段）；B：**27 键**（形态② + **字段别名** `data_manifest`/`validation`/`editable_sources`/`renders`） |

```bash
S=/skills/weekly-skill; OUT=/app/output; WORK=/app/work; CASE=/input/case.json
python "$S/scripts/extract.py"        --case "$CASE" --out "$WORK" --json
python "$S/scripts/spec_lint.py"      --spec "$CASE" --case "$CASE"
python "$S/scripts/main.py"           --case "$CASE" --out "$OUT" --work "$WORK" --style nature
python "$S/scripts/mapcheck.py"       --dir "$OUT" --case "$CASE"
python "$S/scripts/figcheck.py"       --dir "$OUT" --case "$CASE"
python "$S/scripts/verify_rerun.py"   --case "$CASE" --out "$OUT"
python "$S/scripts/check_contract.py" --result "$OUT/result.json" --case "$CASE"
```

`main.py` 全部参数：`--case`（必需）· `--out` · `--work` · `--task` · `--data` ·
`--style`（`default`/`nature`/`cell`/`prism`/`minimal`/`ppt`）· `--dpi` · `--note` ·
`--lang`（`zh`/`en`）· `--no-pdf`。
退出码：`0` = completed 且 G1–G8 全过 / `2` = partial / `1` = failed。

---

## 6. 题集（两个不同题材 + 九种图型）

完整题集见 **`references/CASE-SET.md`**（每案：输入 / 期望产出结构 / 可接受区间 / 难度层 / 实测结果 / 复跑命令）。

| 编号 | 题材 | 图型 | 难度 | 一跑就出的结果 |
|-|-|-|-|-|
| **A** | 湖泊中试富营养化（生态/环境） | `panel`（bar + line） | 中 | `exit 0 / completed` · 29 键 · `99 checked / 0 mismatched` · **1.4 s** |
| **B** | Mg-Zn 合金体外降解（材料/生物材料） | `scatter` + `network` | 高 | `exit 0 / completed` · 27 键 · `74 checked / 0 mismatched` · **0.9 s**（首轮曾失败 → P5） |

**两案的差异是刻意的**：数据源类型（纯表格 vs 表格+材料文本）、图型（panel vs scatter+network）、
契约形态（含非标准字段 vs 走字段别名）、误差语义（单一 SE vs SD 与 SE 并存）、
未引用列（1 列 vs 3 列）。**只有这样才能压出"只在示例上成立"的假设。**

**九种图型探针**（`TEST.md` T10）：`bar/line/scatter/box/heatmap/pie/network/panel/auto`
逐型构造最小案例跑一遍 → 修完 P5–P8 后**全部通过**。

---

## 7. 决策规则（D1–D18，其中 5 条来自题集与探针的结论）

| # | 触发 | 动作 | 失败降级 |
|-|-|-|-|
| D1 | 要画任何图形元素 | 必须可溯源（文件/列/行 或 实体 id/cite） | 无法溯源 → 不画；必要时虚线占位 + `uncertainty` |
| D2 | 生成坐标轴 | 轴标签带单位；刻度覆盖数据 + 5% 余量 | 单位拿不到 → 保留无标签 + `warn` |
| D3 | 画图例 | 每系列恰一图例项，id 一致 | 无法对齐 → 修 spec 重跑（`fail` 阻止 completed） |
| D4 | 引用科学实体名 | 取材料原文，不翻译、不改拼写（案例 B 的 `Cl-`/`Mg(OH)2`/`MgZn2`/`MC3T3-E1` 即实测） | 不确定 → 保留原文 + `uncertain`，确认后才上图 |
| D5 | 文本含 CJK | CJK 字体族回退链 | PNG 缺字 → 记 `warn` |
| D6 | 标注显著性 | 只转述材料给的 p 值与检验名 | 源没给 → **不画**该标注 + `uncertainty` |
| D7 | 输出 SVG | 分层 + 稳定 id + metadata 溯源块 | 渲染不可用 → **先保 SVG 落盘** |
| D8 | 画误差线 | 语义（SE/SD/CI）以源元数据为准，**多语义并存时逐图区分**（案例 B 实测：B1=SD、细胞图=SE，混用即错） | 源未标 → 记 `uncertainty`，**不猜** |
| D9 | 遇空值/NaN | 不补造，跳过并计数 | 整列无值 → 报错 + `uncertainty` |
| D10 | 任何维度未完成 | `status=partial` + 写明原因与复验路径 | ——（兜底：**禁止**把失败写成完成） |
| D11 | 人工改动 | 写 `change_records`（时间戳+内容） | —— |
| D12 | 做 A/B 对照 | 同输入、同版本、同导出参数；本包侧重跑须字节级稳定 | 有差异 → 定位随机源，不搪塞 |
| D13 | 样式模板缺失/损坏，或 `--style` 不是已知预设 | 回退 default，并写 `uncertainty` 点名缺什么、有哪些可用 | ——（回退**不得静默**） |
| **D13-2** | **案例一个图规格都没有** | **不臆造占位图**：图规格取空列表 + `uncertainty` + `status=failed` | ——（宁可失败，不可编造） |
| D14 | 标签过长 / 图例遮挡 / 节点重叠 | 旋转 30°、图例移出绘图区、手给节点坐标（案例 B 的 7 节点网络图实测 `occlusion=warn`，属正常告警） | 仍重叠 → `warn` + `uncertainty` |
| **D14-2** | **机制图只给了材料文本**（`material_file`，无 `entities.json`） | **走 `ENTITY:`/`REL:` 显式行解析**并附 `cite`；自然语言段落只作候选，**不上图** | 解析不到显式行 → 空图 + `uncertainty`（P5 修好的就是这条） |
| D15 | `output_contract` 是四形态之外的形态 | 不回显任何契约字段，`output_contract_applied=false` + 说明 | ——（**不得谎报已应用**） |
| D16 | 契约声明本 Skill 不产出的字段 | 给声明容器类型的空值 + 写明"本 Skill 不产出" | ——（**不做假映射**） |
| D17 | 契约含非法项（数字/空串/非字符串） | **跳过该项**，其余照常回显 | ——（判定口径 = **非空字符串才算字段**） |
| D18 | 写 `status` | 与产物事实严格自洽：有 `fail`/缺口 → 不得 `completed`；无图 → `partial`/`failed` | —— |

**优先级**：① 诚实 > 完整 ② 可核验 > 好看 ③ 保源 > 保预览 ④ 阻断 > 带病交付。

---

## 8. 泛化边界（摘要，完整版见 `references/CASE-SET.md` §4）

已经**不会**失效（本轮修好）：heatmap、`type:"auto"`、只给材料文本的机制图、无图规格的案例。

仍然**会**失效或**不适用**：

1. **需要统计推断**（p 值计算、拟合、检验）—— 只转述，不代算（D6）。
2. **只有自由文本、没有 `ENTITY:` 显式行** —— 自然语言只作候选，机制图可能为空。
3. **缺 Pillow 的环境** —— 校验层会抛错，整次运行 `failed`（已登记缺陷，见 FAULT-MATRIX D2）。
4. **网络图 > 约 20 节点且不手给坐标** —— 自动布局是启发式，标签会重叠（`warn` 不阻断）。
5. **`matrix` 需要长表聚合** —— heatmap 要的是二维矩阵，长表得先聚合。
6. **`box` 的四分位、`pie` 的百分比** —— 用 `presets` 直供 / 引擎归一化，**不代算**。
7. **未测项**：非 UTF-8 输入、超长文本、图像尺寸越界、并发写冲突、磁盘满。

---

## 9. 交付前自查

- [ ] **跑过两个题集案例**：都 `exit 0 / completed / G1–G8 全过 / mapcheck 0 mismatch`
- [ ] 九种图型探针全通过（`TEST.md` T10）
- [ ] `check_contract` `missing=0 null=0`；`verify_rerun` 归一化后 `differ=0`
- [ ] 轴标签带单位；图例↔系列一一对应；显著性只转述；实体名与原文一致
- [ ] **误差语义逐图核对**（多语义并存时不得混用）
- [ ] **未被图引用的源列**仍出现在 `sources[].columns`
- [ ] SVG 分层、含 metadata、真实 `<text>` 未转曲；PNG/PDF 可打开
- [ ] `status` 与产物事实自洽；`uncertainty` 里没有"已知却没说"的事项
- [ ] 无编造数据、无网络访问、无凭据写入

---

## 10. 资源清单（相对 `$SKILL_DIR`）

```
SKILL.md                            本文件（题集结论 + CP1–CP6 + D1–D18 + 泛化边界）
README.md                           依赖/安装/调用/退出码/自检/维护
TEST.md                             真机实测（两案逐条 + 九种图型探针 + 回归）
COMPARE.md                          与"直接调通用绘图库"的对照方案
GITHUB_URL.txt                      公开作品链接（单行）
scripts/main.py                     编排入口 CP1→CP6（--case/--out）
scripts/chartkit.py                 渲染引擎（Scene → SVG/PNG/PDF + 八类校验；本版修了 heatmap/auto）
scripts/extract.py                  CP2：列画像 + 实体/关系抽取（含材料文本解析）
scripts/spec_lint.py                CP3：规格门（E1–E10；exit 2 = 有 error）
scripts/figcheck.py                 CP5：G1–G8 硬门
scripts/mapcheck.py                 CP5：数据↔图元双向核对（容差 1e-9）
scripts/verify_rerun.py             确定性再跑 / artifacts sha256
scripts/check_contract.py           CP6：契约字段覆盖自查
scripts/cjkfont.py                  中文字体发现与回退
scripts/svgtext.py                  SVG 文本转义/清理 + 防转曲检查
scripts/fault_inject.py             四形态故障注入台（23 条，可定点复跑）
templates/journal_styles.json       期刊样式预设（回退行为见 D13）
templates/figure_map.schema.json    图规格声明式契约（仅文档，运行期不读取）
templates/result.template.json      result.json 信封模板
templates/entity_glossary.json      关系规则字典 + 实体词表
references/CASE-SET.md              ★ 本版主件：两案题集（输入/期望结构/可接受区间/难度层/实测/泛化边界）
references/FAULT-MATRIX.md          四形态故障注入的逐行实测（23 条 + P1–P8 缺陷登记）
references/OUTPUT_CONTRACT.md       结果契约（机器可读字段块 + G1–G8 + 四形态）
references/RUBRIC_MAP.md            五维评分 → 本包落点
references/failure-modes.md         失败模式全表
references/audit-rules.md           审计规则
references/encoding-spec.md         CJK/单位/实体命名/SVG 编码规范
references/typesetting-presets.md   期刊排版预设说明
references/workorder-field-map.md   输入 → 字段 → 输出 映射链
examples/                           自带最小示例（肿瘤体积 bar+line + entities.json 机制图）
examples/cases/lake-eutrophication/     ★ 案例 A 输入（case.json / data.csv / task.md）
examples/cases/mg-alloy-degradation/    ★ 案例 B 输入（case.json / data.csv / material.md / task.md）
```

调用方式：

```bash
# 题集两案（判据：都 exit 0 / completed / G1–G8 全过）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/cases/lake-eutrophication/case.json" --out /tmp/outA
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/cases/mg-alloy-degradation/case.json" --out /tmp/outB
# 平台正式案例
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output
```

---

## 11. 限制（如实声明，不掩饰）

1. **题集只覆盖 2 个题材 + 9 种图型**，不等于覆盖全部科研图场景：热图长表聚合、
   大规模网络图（>20 节点）、统计推断、非表格数据（如流式、时序数据库）都**没有**实测。
2. **两个案例是合成的**，不是平台正式案例；数值与机制文本均为自拟，不得当正式案例答案。
3. **D2 是未修的已知缺口**：缺 Pillow 时 `figcheck` 抛错 → 整次 `failed`，SVG 不进 `outputs`。
4. **模块缺失时没有 `result.json`**：`import chartkit` 早于 `main()` 兜底逻辑，须同时看退出码。
5. **不做统计推断**；机制图自动布局是启发式；PDF 是光栅预览嵌入；字体依赖运行环境。
6. **`spec_lint` 不核对列存在性**（实测：引用不存在的列仍 `VALID`），真实兜底在 `mapcheck`
   （列不存在必然 mismatch）。本版**未改这段逻辑**（属校验器语义，不在"修真实缺陷"的边界内）。
