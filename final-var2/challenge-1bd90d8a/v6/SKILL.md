---
name: scientific-figure-craft
description: >
  科研数据图表生成与编辑 Skill（全维合并版 v6：决策显性化 + 增益可测 + 机制显性 +
  故障注入 + 多案例题集）。当输入包含科研数据表格（CSV/TSV/JSON）、统计结果、
  实验记录或生物源材料，或需要生成/编辑示意图、机制图、流程图、柱状图、折线图、
  散点图、箱线图、热图、扇区图、通路图、多面板组合图（关键词：figure、chart、
  plot、diagram、数据图、科研绘图、机制图、通路图、graphical abstract、SVG、
  可编辑图稿、制图、出图）时使用。主线：读契约 → 盘点材料 → 抽取 → 规格门 →
  生成分层可编辑 SVG + PNG/PDF → 双校验（数据↔图元双向核对 + G1–G8 + 确定性）→
  契约落地。本版把"执行决策、增益测量、支撑机制、故障恢复、跨案例泛化"五条证据链
  合并为一份可复跑的交付物：规则见 §3，失败面见 §4，增益见 §5，机制见 §6，
  复用与题集见 §7/§8，全部索引到 references/。严格以真实文件为准，不臆造数据、
  不提交预制答案。
---

# 科研数据图表生成与编辑（scientific-figure-craft）· v6 全维合并版

面向「玻尔产品周赛 · 北大专区 · 学术效率 · 第三期」 `challenge-1bd90d8a`（figures 组）。

> **本包形态**：全部资源是 UTF-8 文本（`.md/.py/.json/.txt/.csv`），**零二进制**
> （无 `.pptx/.png/.pdf/.svg`、无字体文件、无 `__pycache__`）；交付的图与预览一律由
> `scripts/main.py` **运行时生成**，因此包内不存在"预制答案"。
> 所有命令用 `$SKILL_DIR` 自定位，**cwd 不是技能根也能跑**（每一次实测都从包外目录启动）。

**本版是什么**：它不是"再加一个功能"，而是把四条证据链收进同一个包，并按
**输入 → 执行 → 失败 → 增益 → 机制 → 复用** 的顺序重排，使评审读一份文件就能定位全部证据：

| 证据链 | 一句话 | 在哪 |
|-|-|-|
| **执行** | 每个岔路都有决策规则 D1–D18（触发 → 动作 → 降级） | §3 + `references/failure-modes.md` |
| **失败** | 23 条故障注入逐行实测 + 8 处真实缺陷登记（1 处未修） | §4 + `references/EVIDENCE.md` 第一部分 |
| **增益** | 12 项机器可判定指标的 A/B 对照协议与实测 | §5 + `references/MECHANISM.md` 第二部分 |
| **机制** | 四个互相咬合的机制，各自回答"没有它会怎样" | §6 + `references/MECHANISM.md` 第一部分 |
| **复用 / 泛化** | 两案题集（不同题材）+ 九种图型探针 + 泛化边界 | §7/§8 + `references/EVIDENCE.md` 第二部分 + `references/MECHANISM.md` 第三部分 |

> **合并说明（透明）**：为守住"≤50 个文本文件"的硬门，本版把四份专题文档合并为
> `references/MECHANISM.md`（机制 / 增益 / 复用 / 增改 四部分），把两份实证文档合并为
> `references/EVIDENCE.md`（故障矩阵 / 案例题集 两部分）。**只动编排，没有任何内容被删除**；
> 被合并文档原有的小节编号与表格一字未改，脚本注释里出现的旧文件名即指这两份的对应部分。

---

## 1. 输入（契约先行，先知道要交什么）

### 1.1 运行期输入

| 来源 | 内容 | 缺失时的实测行为 |
|-|-|-|
| `/input/case.json` | `case_id`、`figures` 规格、`data` 引用、`output_contract`、`manual_confirmations` | **必需**；不存在/不可解析 → 6 键最小诚实信封 + exit 1；**没有任何图规格 → failed + exit 1（不臆造）** |
| `/input/task.md` | 任务说明（要几张图、图型、目标样式、图面约束） | 自动找同目录；仍无 → 记 `uncertainty` |
| 源数据表 | CSV / TSV / JSON | 一个都没有 → `partial` + exit 2，**点名缺失路径** |
| 生物源材料 | `material` 文本（`ENTITY:` / `REL:` 显式行）**或** `entities_file` JSON | 两条路径均可走通（材料文本那条由本版修复，见 §4-P5） |

`case.json` 形态兼容：顶层对象 / `{"cases":[...]}` / 数组取首项（**实测**取首项并忽略干扰项）；
图规格可放 `figures` / `figure` / `figure_spec`；数据可放 `data` / `data_files` / `sources`。

### 1.2 输出契约（唯一评分产物是 `result.json`）

`references/OUTPUT_CONTRACT.md` 是**机器可读契约**：`check_contract.py` 直接解析其中的
`REQUIRED-FIELDS` 块。**该字段块逐字受保护**，本版未改任何字段名或结构。

```
/app/output/                                     /app/work/
├── figure-<id>.svg   分层可编辑矢量源（<g id="layer-*"> + <metadata id='provenance'> + data-*）
├── figure-<id>.png   同场景位图预览              ├── extract.json     列画像 + 实体/关系
├── figure-<id>.pdf   同场景 PDF 预览（时间戳归一化）  └── spec_lint.json    CP3 生成门结果
├── data_manifest.json   图元 ↔ 源数据（column/row_index/value 或 实体 id/cite）
├── validation.json      八类标注检查逐项 ok/warn/fail
├── mapcheck_report.json 数据↔图元双向核对（容差 1e-9）
├── figcheck_report.json G1–G8 硬门
└── result.json          契约字段全回显（四形态，禁 null）+ case_id + status/sources/
                         uncertainty/change_records/checkpoints/gates/artifacts_sha256
```

**契约四形态全部兼容**：① 字段名列表 ② 名称→类型 ③ 嵌套 `fields` 列表 ④ 嵌套 `fields` 映射；
已知别名映射到**真实产物**（`editable_source` → `editable_sources`、`field_mapping` →
`"data_manifest.json"`、`validation_report` → `"validation.json"` …）；声明了本 Skill 不产出的字段
→ 给**声明容器类型的空值**并写明原因，**不做假映射、绝不写 null**。

---

## 2. 执行（CP1–CP6：每一步都有可判定的门）

| 步 | 动作 | 命令 | 退出条件（不满足即降级） |
|-|-|-|-|
| **CP1** | 材料盘点：列文件、算 sha256、记行数列名 | `extract.py --case … --out … --json` | `case_id` 已取 ∧ task.md 已读或已记 `uncertainty` ∧ 至少一个数据文件 |
| **CP2** | 抽取：列画像 + 实体/关系（含**材料文本**的 `ENTITY:`/`REL:` 行） | 同上 | 每列语义无歧义 ∧ 每个实体/关系有来源 ∧ 不确定候选已记录 |
| **CP3** | 规格门 | `spec_lint.py --spec … --case …`（**exit 2 = 有 error**） | 图型合法 ∧ 列存在 ∧ 误差语义常规 ∧ 显著性有锚点/来源 ∧ 网络边不悬空 |
| **CP4** | 生成：规格 → `Scene` → SVG + PNG/PDF | `main.py --case … --out … --work … --style nature` | 每图三形态齐全 ∧ SVG 分层含溯源 ∧ 预览可打开 |
| **CP5** | 双校验 + 确定性 | `mapcheck.py` / `figcheck.py` / `verify_rerun.py` | `mismatched=0 unmatched=0` ∧ G1–G8 全过 ∧ 归一化后 `differ=0` |
| **CP6** | 契约落地 | `check_contract.py --result … --case …` | `missing=0 null=0 contract_missing=0` ∧ `status` 与产物自洽 |

```bash
S=/skills/weekly-skill; OUT=/app/output; WORK=/app/work; CASE=/input/case.json
python "$S/scripts/extract.py"        --case "$CASE" --out "$WORK" --json     # CP1+CP2
python "$S/scripts/spec_lint.py"      --spec "$CASE" --case "$CASE"           # CP3（门）
python "$S/scripts/main.py"           --case "$CASE" --out "$OUT" --work "$WORK" --style nature  # CP4
python "$S/scripts/mapcheck.py"       --dir "$OUT" --case "$CASE"             # CP5
python "$S/scripts/figcheck.py"       --dir "$OUT" --case "$CASE"             # CP5
python "$S/scripts/verify_rerun.py"   --case "$CASE" --out "$OUT"             # CP5（确定性）
python "$S/scripts/check_contract.py" --result "$OUT/result.json" --case "$CASE"  # CP6
```

`main.py` 全部参数：`--case`（必需）· `--out` · `--work` · `--task` · `--data` ·
`--style`（`default`/`nature`/`cell`/`prism`/`minimal`/`ppt`）· `--dpi` · `--note` ·
`--lang`（`zh`/`en`）· `--no-pdf`。
退出码：`0` = completed 且 G1–G8 全过 / `2` = partial / `1` = failed。

---

## 3. 决策规则（D1–D18：触发 → 动作 → 失败降级 → 落痕）

**为什么要有这张表**：图题的失误几乎都不是"画不出来"，而是**在岔路上默认选错**
—— 缺列时顺手补一个、量级可疑时顺手改一下、字体缺字当作正常、契约字段缺了就写 null。
把每个岔路的触发条件写死，同一输入在不同人手里才会走到同一个结果。

| # | 触发条件 | 动作（默认选择） | 失败/不可行时的降级 | 落痕字段 |
|-|-|-|-|-|
| D1 | 要在图上画任何图形元素 | 必须具备溯源（文件/列/行，或实体 id/cite） | 无法溯源 → **不画**；必要时虚线占位 | `data_manifest` 的 `source`；`uncertainty` |
| D2 | 生成坐标轴 | 轴标签带单位；刻度覆盖数据 + 5% 余量 | 单位拿不到 → 保留无标签 + `warn` | `validation` `axis-units` |
| D3 | 画图例 | 每系列恰一图例项，系列 id = 图例 id | 无法对齐 → **修 spec 重跑**，不带病交付 | `validation` `legend-mapping`（fail 阻止 completed） |
| D4 | 引用任何科学实体名 | 取源材料原文，**不翻译、不"优化"拼写**（如 `Cl-`/`Mg(OH)2`/`MgZn2`/`MC3T3-E1`） | 无法确认 → 保留原文 + `uncertain` | `extract.json`；`uncertainty` |
| D5 | 文本含 CJK | CJK 字体族回退链 | 缺字 → SVG 照常，PNG 记 `warn` | `environment.fonts`；`validation` `cjk-font` |
| D6 | 需要标注显著性 | 星号数与 p 值**与源一致**；只转述，不自行计算；图注写明来源与检验名 | 源未给 p 值/检验名 → **不画**该标注 | `validation` `significance` |
| D7 | 输出 SVG | 分层（背景/坐标/数据/标注/图例）+ 稳定 id + metadata 溯源块 | 渲染不可用 → **先保 SVG 落盘** | `gates.G5` |
| D8 | 画误差线 | 语义（SE/SD/CI）以源元数据为准；**多语义并存时逐图区分，不得混用** | 源未标 → 记 `uncertainty`，**不猜** | `data_manifest` `error_value` |
| D9 | 遇空值 / NaN | 不补造；跳过该点并计数 | 整列无值 → 报错 + `uncertainty` | `validation` `null-handling` |
| D10 | 任何维度未完成 | `status=partial` + 写明原因与可复验路径 | ——（兜底规则：**禁止**把失败写成完成） | `status`；`uncertainty`（G8 强制） |
| D11 | 发生人工修改或参数调整 | 写 `change_records`（时间戳 + 内容）；`--note` 追加 | —— | `change_records` |
| D12 | 要做"加载 / 不加载"对照 | 同一输入、同一数据版本、同一导出参数；本包侧同输入重跑须字节级稳定 | 有字节差异 → 定位随机源并修掉，不搪塞 | `artifacts_sha256`（协议见 §5） |
| D13 | 样式模板缺失/损坏，或 `--style` 不是已知预设 | **回退 default，并写 `uncertainty` 点名缺什么、有哪些可用** | ——（回退**不得静默**） | `uncertainty`；`environment.style` |
| D13-2 | **案例一个图规格都没有** | **不臆造占位图**：图规格取空列表 + `uncertainty` + `status=failed` | ——（宁可失败，不可编造） | `status`；`uncertainty` |
| D14 | 标签过长 / 图例遮挡 / 节点标签重叠 | 标签旋转 30°；图例移出绘图区；复杂网络**手给节点 x/y** | 仍重叠 → `warn` + `uncertainty` | `validation` `adjustments`/`occlusion` |
| D14-2 | 机制图只给了**材料文本**（`material_file`） | 走 `ENTITY:`/`REL:` **显式行**解析并附 `cite`；自然语言段落只作候选，**不上图** | 解析不到显式行 → 空图 + `uncertainty` | `extract.json`；`uncertainty` |
| D15 | 处理 `output_contract` | 四形态全部完整回显；缺失按声明容器类型给空值，禁 null | 契约声明了不产出的字段 → **不做假映射**，给空值并写明原因 | `output_contract_applied` |
| D16 | 契约形态是**四形态之外**（如裸字符串） | **不回显任何契约字段，如实置 `output_contract_applied=false`** + 说明 | ——（**不得谎报已应用**） | `output_contract_applied`；`uncertainty` |
| D17 | 契约含非法项（数字 / 空串 / 非字符串） | **跳过该项**，其余照常回显（判定口径：**非空字符串才算字段**） | —— | `output_contract_applied` |
| D18 | 准备写 `status` | 与产物事实严格自洽：有 `fail`/缺口 → 不得 `completed`；无任何图 → `failed` | ——（`failed_figures`/`uncertainty`/`change_records` 互不矛盾） | `status`；`gates.G8` |

**规则冲突优先级**：① **诚实 > 完整**（D10 压过"把字段填满"；D15 的禁 null 与它不冲突）
② **可核验 > 好看**（D1/D3/D6/D8）③ **保源 > 保预览**（D5/D7 先保 SVG 与全部 JSON）
④ **阻断 > 带病交付**（D3/D6 的 `fail` 拦住 `completed`）。

---

## 4. 失败（注入实测 → 已知缺陷 → 恢复策略）

**声明层**：`references/failure-modes.md`（材料 / 数据 / 图面 / 导出 / 契约 / 依赖六族，逐条给出
症状、检出点、处置、落痕字段）。**实证层**：`references/EVIDENCE.md` 第一部分
（`scripts/fault_inject.py` 的 **23 条**四形态注入逐行实测：注入什么 → 实测退出码 → 实测
`status` → 实测 `uncertainty` 原文 → **是否静默失败**）。

```bash
# 全套（包外工作目录；源包只读，脚本自己复制副本，因此包内不会留 __pycache__）
python "$SKILL_DIR/scripts/fault_inject.py" --src "$SKILL_DIR" --workdir /tmp/fw
# 定点复核（例如契约与模板两组）
python "$SKILL_DIR/scripts/fault_inject.py" --src "$SKILL_DIR" --only K1,K6,T1,T2 --keep
```
判据：**`cases=23 mismatch=0`**（`2` = 有实测与文档声明对不上的，即注入台找到了问题）。

### 4.1 注入查出的 8 处真实缺陷（全部已修，纯增量）

| # | 缺陷 | 暴露方式 | 修前实测 | 修后实测 |
|-|-|-|-|-|
| P1 | 契约里一个 `""` 被 G2 当成"必须存在的字段" → 完整契约被判失败 | 注入 K1 | `exit 2 / partial / G2=false` | `exit 0 / completed / G2=true` |
| P2 | 缺图规格时失败记录丢掉真实原因 | 注入 I6 | 只报 `不支持的图型：auto` | 追加"案例未提供任何图规格…" |
| P3 | 样式模板缺失/损坏、`--style` 拼错 **三种情况全静默** | 注入 T1/T2/T5 | `uncertainty=[]` 且 `completed` | 每种都写 `uncertainty` 并列出可用预设 |
| P4 | 契约是四形态之外的裸字符串时**谎报** `applied=true` | 注入 K6 | `applied=true`（其实没写任何字段） | `applied=false` + 说明 |
| P5 | network 只给 `material_file` **必然失败**（`extract.py` 能解析，生成路径没接上） | 案例 B | `exit 2`，`通路图需要 entities（节点）列表。` | `exit 0 / completed / 2 张图` |
| P6 | **`heatmap` 在任何输入下都失败**（色阶插值三处写法错误） | 图型探针 | `ValueError: invalid literal for int() with base 16: '#4'` | `exit 0 / completed` |
| P7 | **`type: "auto"` 从来没生效**（`infer_type` 把字面量 `"auto"` 原样返回） | 图型探针 | `不支持的图型：auto` | `exit 0 / completed` |
| P8 | 案例没有任何图规格时会**凭空画一张占位图**（P7 修好后暴露） | 图型探针 | 可能报 `completed` 且画出没要求的图 | `exit 1 / failed` + `uncertainty`，磁盘无 `figure-*` |

**改动规模（逐文件点名，相对合规基线）**：`scripts/main.py` **+109 / −7**、
`scripts/figcheck.py` **+8 / −4**、`scripts/chartkit.py` **+60 / −4**（含 P6/P7 与
**PDF 元数据确定性归一化**）。**CLI 参数名、默认值、退出码语义一字未改**；
其余 `scripts/*.py` **逐字节不变**。新增文件：`scripts/fault_inject.py`。

### 4.2 1 处**未修**的已知缺口（如实登记）

| 项 | 实测 |
|-|-|
| 注入 | 用 `PYTHONPATH` 上的 stub 让 `import PIL` 抛 `ImportError`（`fault_inject.py --only D2`） |
| 实测 | **exit 1** · `status=failed` · `result.json` 只剩 **6 键** · traceback 落在 `figcheck.py: from PIL import Image` |
| 后果 | `chartkit` 本可优雅降级（保 SVG 与全部 JSON），但**校验层**抛错 → 已写出的 2 个 SVG **不进入 `result.json.outputs`** |
| 为什么没修 | 修它要改校验器语义（G6 的判定条件），超出"只修真实缺陷、不改退出码语义"的边界 |
| 运行期规避 | **部署前自检**：`python -c "import PIL; print(PIL.__version__)"`；缺失则先 `pip install Pillow` |

另有 3 条**已知边界**（不改代码，只登记）：关系词表回退无痕（装饰层，不影响数据闭合）；
`figure_map.schema.json` 从不被运行时读取（纯文档）；`scripts/*.py` 缺失时**不写**
`result.json`（`import` 早于兜底逻辑，须同时看退出码）。

### 4.3 恢复策略总表（遇到什么，做什么）

| 情形 | 处置 | `result` 落痕 |
|-|-|-|
| 数据文件缺失 / 为空 | 报错并**点名列名或路径**；不猜内容 | `status=partial`；`uncertainty` |
| 部分图失败 | **不阻塞**其余图；`status=partial` | `failed_figures` |
| 缺列 / 列名写错 | 用列画像修正；推断失败 → 报错**列出可用列** | `failed_figures`；`uncertainty` |
| 空值 / NaN | 跳过并计数；整列无值 → 报错 | `uncertainty`（含数量） |
| 量级异常（10 倍以上） | `warn` 保留原值并标可疑，**不"修正"** | `uncertainty` |
| 标签过长 / 图例遮挡 | 自动旋转 30° / 图例移出绘图区 | `validation.adjustments` |
| CJK 字体缺失 | SVG 走回退链；PNG 记 `warn` | `uncertainty`；`environment.fonts` |
| 显著性缺配对 | `validation` fail → 修 spec 重跑 | 阻止 `completed`（G7/G8） |
| 导出失败（写文件 / Pillow 缺失） | 保 SVG 与全部 JSON 先落盘 ← **注意 §4.2 的缺口** | `warnings`；`uncertainty` |
| 样式模板缺失/损坏 / `--style` 拼错 | 回退 default + **留痕** | `uncertainty` |
| 契约先天缺字段 / 含非法项 / 形态非法 | 按容器类型给空值 / 跳过非法项 / 如实置 `applied=false` | `output_contract_applied` |
| 人工改图 | `--note` 追加一条 change record | `change_records` |

---

## 5. 增益（怎么被公平地测量，而不是被声称）

**主证据**：`references/MECHANISM.md` 第二部分（含原 `GAIN-PROTOCOL.md` 全文与
原 `COMPARE.md` 的对照方案）。要点：

- **口径公开**：条件 A = `examples/baseline_agent.py`（把"通用绘图库 + 直接写脚本"这一常规做法
  **固化成可复跑代码**的参照实现）；条件 B = `scripts/main.py` 的完整链路。同一份合成输入、
  同一数据版本、同一导出参数。
- **指标机器可判定**：**12 项**（质量 8 / 审计 3 / 效率-确定性 1），每项只依赖文件字节或可复算计数；
  判定器 `examples/measure_ab.py` 对两份条件用**同一套代码**打分。
- **实测结果**：A **1/12**、B **12/12**；**A 唯一通过的那一项我们也如实列出**（Q12 确定性的
  子集），并说明它为什么通过（产物少且不含时间戳），**不把它藏起来**。
- **不做的事**：**不声称任何"提升 x%"**。本地合成示例上的对照数字 ≠ 平台评分；
  A 侧耗时更短（约 0.9 s vs 1.5 s）**不是效率增益** —— 它做的事更少。本包**不做**"耗时缩短 x%"式声称。
- **可复跑**：
  ```bash
  python "$SKILL_DIR/examples/baseline_agent.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/A
  python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/B --style nature
  python "$SKILL_DIR/examples/measure_ab.py" --a /tmp/A --b /tmp/B --case "$SKILL_DIR/examples/case.json"
  ```
- **平台侧对照由平台执行**（题面：固定 3 案例、相同内容分别交给基础 Agent 与加载 Skill 的 Agent）；
  参赛者要交的是"**可复跑的形态 + 公开的口径**"，不是自造白板、自报分数。

---

## 6. 机制（四个互相咬合的机制，各自回答"没有它会怎样"）

**主证据**：`references/MECHANISM.md` 第一部分（含边界对照表：相对通用绘图库 / 现成模板 /
一次性脚本，本包各机制的**边界在哪、不保证什么**）。

| # | 机制 | 一句话 | 没有它会怎样 |
|-|-|-|-|
| **M1** | **三向闭合** | SVG 图元的 `data-*` ↔ `data_manifest.json` ↔ **重读源表**的值，三处互为索引且由 `mapcheck.py` 机器核对（容差 1e-9） | "这根柱子的数字来自哪一行"永远回答不了；列错位不会被发现 |
| **M2** | **声明式规格 + 生成门** | 图由可校验的规格驱动，过门（`spec_lint` 无 error）才进渲染；样式三层合并（内置 → 预设 → spec 内联） | 错误推迟到渲染阶段才爆；样式无法复用；别人无法接手你的图 |
| **M3** | **单一场景双端输出** | 一个与格式无关的 `Scene` 同时导出分层 SVG 与 PNG/PDF，逐元素同源；文字**永不转曲** | 矢量与位图能画出"看起来不同"的两张图，评审不知道以哪张为准 |
| **M4** | **契约四形态回显 + 确定性归一化** | 四形态全兼容、禁 `null`；把渲染器注入的 PDF 时间戳归一化，让 `sha256` 成为证据 | 下游拿到 `null` 要写特判；`sha256` 每次都变，于是没人拿它当证据 |

**拿掉任何一个，其余机制的收益都会被削弱**：M1 没了，M3 的"双端同源"失去意义；
M3 没了，M1 的 `data-*` 与位图脱钩；M2 没了，错误推迟到渲染阶段；M4 没了，
前三个机制的成果既无法被下游消费、也无法证明"是同一份"。

**实测支撑**（全部可复跑）：案例 A `mapcheck 99 checked / 0 mismatched`；
案例 B `74 checked / 0 mismatched`；两案 `verify_rerun` 均 `DETERMINISTIC`；
PDF 时间戳修复前后 `cmp -l` 只差 4 个字节（全部落在 `CreationDate`/`ModDate`），
归一化后两个 PDF 逐字节一致（详见 `references/MECHANISM.md` 第一部分 §7）。

**边界（不夸大）**：M1 只保证"可回溯"，**不保证数据本身正确**；M3 只保证"双端同源"，
**不保证图面美观**；M4 只保证"可被机器接手且可复现"，**不保证契约字段的业务含义正确**。

---

## 7. 复用（别人能拿走什么）

**主证据**：`references/MECHANISM.md` 第三部分（资产清单 A/B/C 分级 + 三条复用路径 +
验收清单 + "不要带走的东西"）。

| 想拿走多少 | 路径 | 拿走什么 | 验收标准 |
|-|-|-|-|
| 只想要可编辑科研图 | 路径一（约 10 分钟） | `chartkit` + `cjkfont` + `svgtext` + 模板 | SVG 存在、分层、含 `<text>`、图元带 `data-*` |
| 想要可核验的交付链路 | 路径二（约 30 分钟） | 再加 `mapcheck`/`figcheck`/`verify_rerun`/`check_contract` + 契约文档 | 四个校验器全 exit 0 |
| 想要"证明增益 + 说明机制 + 自带回归" | 路径三（约 1 小时） | 再加 `baseline_agent`/`measure_ab`/`fault_inject` + 题集与实证文档 | 两侧都有对照报告；注入台 `mismatch=0`；题集两案全过 |

**本版新增的可复用资产**：`scripts/fault_inject.py`（把"异常处理"变成 23 条可复跑实验）、
`examples/cases/**`（两个不同题材的题集，换数据即用）、`references/EVIDENCE.md`（逐行实测）。

---

## 8. 泛化（题集 + 九种图型：不只在自己示例上跑通）

**主证据**：`references/EVIDENCE.md` 第二部分（案例题集：每案给输入、期望产出结构、
**可接受区间**、难度层、逐案实测、复跑命令，以及**泛化边界**）。

| 编号 | 题材 | 图型 | 难度 | 实测 |
|-|-|-|-|-|
| **A** | 湖泊中试富营养化（生态/环境） | `panel`（bar + line） | 中 | exit 0 · 29 键 · `99 checked / 0 mismatched` · 1.4 s · 未引用列仍在 `sources[].columns` |
| **B** | Mg-Zn 合金体外降解（材料/生物材料） | `scatter` + `network`（材料文本驱动） | 高 | exit 0 · 27 键 · `74 checked / 0 mismatched` · 0.9 s · **首轮曾失败（P5）** |

**九种图型探针**：`bar / line / scatter / box / heatmap / pie / network / panel / auto`
逐型构造最小案例实测 → 修完 P5–P8 后**全部通过**（修前 `heatmap` 与 `auto` 完全不工作）。

**泛化边界（如实声明）**：
- **已经不会失效**（本轮修好）：heatmap、`type:"auto"`、只给材料文本的机制图、无图规格的案例。
- **仍然会失效 / 不适用**：需要统计推断（只转述不代算）；材料只有自由文本、没有 `ENTITY:` 显式行
  （候选不上图，机制图可能为空）；缺 Pillow 的环境（§4.2 缺口）；网络图 > 约 20 节点且不手给坐标
  （`occlusion` warn）；`matrix` 需先聚合长表；`box` 四分位与 `pie` 百分比**不代算**。
- **未测项**（不声称）：非 UTF-8 输入、超长文本、图像尺寸越界、并发写冲突、磁盘满。

---

## 9. 交付前自查清单

- [ ] 跑过 `fault_inject.py`：`cases=23 mismatch=0`（或 mismatch 已逐条登记）
- [ ] 跑过题集两案：都 `exit 0 / completed / G1–G8 全过 / mapcheck 0 mismatch`
- [ ] 九种图型探针全通过（`references/EVIDENCE.md` 第二部分 §4.1）
- [ ] `check_contract` `missing=0 null=0`；`verify_rerun` 归一化后 `differ=0`
- [ ] A/B 对照可复跑：`baseline_agent.py` + `measure_ab.py` 两侧都有报告
- [ ] 轴标签带单位；图例↔系列一一对应；显著性只转述；**误差语义逐图区分不混用**
- [ ] 实体名与源材料原文一致（未"修正"拼写）；不确定项已标记
- [ ] **未被任何图引用的源列**仍出现在 `sources[].columns`
- [ ] SVG 分层、含 metadata、真实 `<text>` 未转曲；PNG/PDF 可打开
- [ ] `result.json` 契约字段齐全（四形态）+ `case_id` 正确 + `status` 自洽
- [ ] 中文标签字体回退生效或已记 `uncertainty`
- [ ] 无编造数据、无网络访问、无凭据写入；部署前 `import PIL` 自检已做

---

## 10. 资源索引（相对 `$SKILL_DIR`）

```
SKILL.md                        本文件（输入 → 执行 → 决策 → 失败 → 增益 → 机制 → 复用 → 泛化）
README.md                       依赖/安装/调用/退出码/目录/维护
TEST.md                         真机实测记录（含注入、题集、探针、A/B、回归的实测摘录）
GITHUB_URL.txt                  公开作品链接（单行）

scripts/main.py                 编排入口 CP1→CP6（--case/--out/--work/--task/--data/--style/--dpi/--note/--lang/--no-pdf）
scripts/chartkit.py             渲染引擎（Scene → SVG/PNG/PDF + 八类校验 + PDF 确定性归一化 + 色阶）
scripts/extract.py              CP2：列画像 + 实体/关系抽取（含材料文本 ENTITY/REL 行）
scripts/spec_lint.py            CP3：生成门（E1–E10；exit 2 = 有 error）
scripts/figcheck.py             CP5：G1–G8 硬门（--dir/--case）
scripts/mapcheck.py             CP5：数据↔图元双向核对（--dir/--case，容差 1e-9）
scripts/verify_rerun.py         确定性再跑 / artifacts sha256（--case/--out/--rerun-dir/--record-only）
scripts/check_contract.py       CP6：契约字段覆盖自查（--result/--case/--contract）
scripts/cjkfont.py              中文字体发现与回退
scripts/svgtext.py              SVG 文本转义/清理 + 防转曲检查
scripts/fault_inject.py         ★ 四形态故障注入台（23 条；--src/--workdir/--out/--only/--keep/--timeout）

templates/journal_styles.json   期刊样式预设（default/nature/cell/prism/minimal/ppt）
templates/figure_map.schema.json 图规格声明式契约（仅文档，运行期不读取）
templates/result.template.json  result.json 信封模板
templates/entity_glossary.json  关系规则字典 + 实体词表

references/EVIDENCE.md          ★ 第一部分 故障矩阵（23 条逐行实测 + P1–P8）/ 第二部分 案例题集
references/MECHANISM.md         ★ 第一部分 机制 / 第二部分 增益协议与对照 / 第三部分 复用 / 第四部分 增改
references/OUTPUT_CONTRACT.md   结果契约（机器可读字段块 + G1–G8 + 四形态）—— 逐字受保护
references/RUBRIC_MAP.md        五维评分（40/25/15/10/10）→ 本包文件与机制逐条对照
references/failure-modes.md     失败模式全表（六族）+ 本表的实测复核状态
references/audit-rules.md       审计规则（检查项/级别/处置）
references/encoding-spec.md     CJK/单位/实体命名/SVG 编码规范
references/typesetting-presets.md 期刊排版预设说明
references/workorder-field-map.md 输入 → 字段 → 输出 映射链

examples/case.json + data.csv + entities.json + material.md + task.md
                                自带最小示例（肿瘤体积 bar+line + entities.json 机制图）
examples/baseline_agent.py      ★ 条件 A：基准做法的可复跑参照实现
examples/measure_ab.py          ★ 12 项指标的 A/B 度量器
examples/EXPECTED-OUTPUT.md     示例案例的预期产物清单（文字契约）
examples/output/*.json          示例案例的真实运行产物（契约 JSON）
examples/cases/lake-eutrophication/     ★ 案例 A 输入（case.json / data.csv / task.md）
examples/cases/mg-alloy-degradation/    ★ 案例 B 输入（case.json / data.csv / material.md / task.md）
```

**最常用的四条命令**：

```bash
# ① 正式案例
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output --work /app/work
# ② 题集两案（回归）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/cases/lake-eutrophication/case.json" --out /tmp/outA
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/cases/mg-alloy-degradation/case.json" --out /tmp/outB
# ③ 故障注入（23 条，判据 mismatch=0）
python "$SKILL_DIR/scripts/fault_inject.py" --src "$SKILL_DIR" --workdir /tmp/fw
# ④ A/B 增益对照
python "$SKILL_DIR/examples/measure_ab.py" --a /tmp/A --b /tmp/B --case "$SKILL_DIR/examples/case.json"
```

---

## 11. 限制（如实声明，不掩饰）

1. **1 处已知缺口未修**：缺 Pillow 时校验层抛错 → 整次 `failed`，SVG 不进 `outputs`（§4.2）。
   部署前必须自检 `import PIL`。
2. **模块缺失时没有 `result.json`**：`import chartkit` 早于兜底逻辑，须同时看退出码。
3. **不做统计推断**：显著性计算、拟合、检验一律不在范围内，只转述材料已给的数值（D6）。
4. **机制/通路图自动布局是启发式**；复杂通路建议在 spec 手给节点 x/y（D14）。
5. **PDF 预览是光栅预览嵌入 PDF**；投稿要求的矢量可编辑源以 SVG 为准。
6. **中文字体依赖运行环境**；缺字体时 SVG 走回退链、PNG 记 warn（D5）。
7. **词表扫描只是候选提示**，不替代 Agent 对源材料的确认（D4）。
8. **`spec_lint` 不核对列存在性**（实测：引用不存在的列仍 `VALID`）；真实兜底在 M1 的
   `mapcheck`（列不存在必然 mismatch）。本版**未改**这段逻辑（属校验器语义）。
9. **泛化边界与未测项**见 §8；**对照数字不等于平台评分**见 §5。
10. **包内零二进制**；所有图与预览运行时生成，因此没有可被误当"预制答案"的成品图。
