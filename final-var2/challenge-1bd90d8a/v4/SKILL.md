---
name: scientific-figure-craft
description: >
  科研数据图表生成与编辑 Skill（故障注入与恢复演练版）。当输入包含科研数据表格
  （CSV/TSV/JSON）、统计结果、实验记录或生物源材料，或需要生成/编辑示意图、
  机制图、流程图、柱状图、折线图、散点图、箱线图、热图、扇区图、通路图、
  多面板组合图（关键词：figure、chart、plot、diagram、数据图、科研绘图、
  机制图、通路图、graphical abstract、SVG、可编辑图稿、制图、出图）时使用。
  本版把"异常处理到底有没有生效"变成**可执行实验**：scripts/fault_inject.py 把
  输入/模板/依赖/契约四形态逐个故意弄坏、跑主流程、记录实测退出码与 status 与
  uncertainty 字段，矩阵见 references/FAULT-MATRIX.md（23 条，含 6 条查出的真实缺陷
  与 1 条未修的韧性缺口，全部如实登记）。主链路仍是：读契约 → 盘点材料 → 抽取 →
  规格门 → 生成分层可编辑 SVG + PNG/PDF 预览 → 双校验与确定性再跑 → 契约落地。
  严格以真实文件为准，不臆造数据、不提交预制答案。
---

# 科研数据图表生成与编辑（scientific-figure-craft）· 故障注入与恢复演练版

面向「玻尔产品周赛 · 北大专区 · 学术效率 · 第三期」 `challenge-1bd90d8a`（figures 组）。

> **本包形态**：只含 UTF-8 文本资源（`.md/.py/.json/.txt/.csv`），**零二进制**
> （无 `.pptx/.png/.pdf/.svg`、无字体文件、无 `__pycache__`）；所有图与预览由
> `scripts/main.py` 运行时生成。命令一律用 `$SKILL_DIR` 自定位，cwd 不影响执行。
> 五维评分（实际效果 40 / 使用增益 25 / 创新增益 15 / 可靠体验 10 / 生态贡献 10）
> 的逐条落点见 `references/RUBRIC_MAP.md`。

**本版只主张一件事**：*"我们写了异常处理"* 和 *"异常处理真的生效了"* 是两回事，
前者是文档，后者只能靠**注入故障 + 重跑 + 看输出**证明。
`scripts/fault_inject.py` 就是那台实验台；`references/FAULT-MATRIX.md` 是它的实验记录本，
**连自己查出来的、没修好的缺陷一起登在上面**。

---

## 1. 先看结论：注入查出了什么

23 条注入（输入 7 / 模板 5 / 依赖 4 / 契约 7）跑完后，`mismatch=0`，但更重要的是
**修正前有 6 条"查不到原因"或"说法与事实不符"**：

| # | 查出的问题 | 类别 | 现在的状态 |
|-|-|-|-|
| P1 | 契约里一个空字符串 `""` 被 G2 当成"必须存在的字段" → 完整契约被判**失败**（降到 partial/exit 2） | 契约 | **已修**，`main.py`+`figcheck.py` 统一"非空字符串才算字段" |
| P2 | 案例没给图规格时，失败记录只留渲染层的"不支持的图型：auto"，**真实原因丢失** | 输入 | **已修**，失败记录追加规格自带说明 |
| P3 | 样式模板缺失/损坏/预设名拼错，三种情况**全静默**（`uncertainty=[]` 且 `completed`） | 模板 | **已修**，回退必须写 `uncertainty` |
| P4 | 契约是四形态之外的裸字符串时**谎报** `output_contract_applied=true` | 契约 | **已修**，如实置 false + 说明 |
| D2 | Pillow 缺失时**降级路径失效**：`chartkit` 会优雅降级，但 `figcheck` 顶层 `from PIL` 未保护 → 整体 FATAL，已写出的 SVG 在 `result.json` 里**消失** | 依赖 | **未修，如实登记**（改它要动校验器语义，越界） |
| N1–N3 | 关系词表回退无痕 / schema 模板从不被读取 / 模块缺失时不写信封 | 边界 | 登记说明，不改代码 |

逐条的注入操作、实测退出码、实测 `status`、实测 `uncertainty` 原文、是否静默失败
→ **`references/FAULT-MATRIX.md`**（那张表是逐行实测的，不是设计意图）。

> **诚实声明（两条）**：
> ① P6/P7 说明"文档声明支持"与"代码真的支持"曾有四处分叉（heatmap 全废、auto 从未生效、
>    material_file 接不上、无规格时会编造图）—— 全部由**探针**（`TEST.md` T10）查出，不是靠读代码猜的。
> ② D2 那一条说明本包的"优雅降级"承诺**只在渲染层成立、在校验层不成立**。
> 我们没有把它藏进"已知限制"里含糊带过，而是给出注入方法、实测输出和运行期规避建议（§6）。

---

## 2. 适用条件与边界

**适用**：平台固定 3 个案例维度（数据图表生成 / 样式调整 / 标注校验 / 源数据关联 /
可编辑源文件与导出）；也适用于任何「数据表或生物源材料 → 可编辑科研图」的请求。

**不适用**：统计方法的选择与显著性计算（本 Skill 只**转述**材料给的 p 值与检验名）；
实验方案设计；替用户下科学结论。

**运行环境**：Python 3.8+ 标准库 + Pillow（渲染 PNG/PDF 预览）。
matplotlib / cairosvg / svgwrite 均非必需。不访问网络。

> ⚠️ **部署前自检（本版新增，源于 D2 的实测）**：
> ```bash
> python -c "import PIL, sys; print('Pillow', PIL.__version__, sys.version.split()[0])"
> ```
> 打印不出来就先 `pip install Pillow`。**不要假设**缺 Pillow 时包会优雅降级 ——
> 渲染层会降级，但校验层会抛错并把整次运行打成 `failed`（详见 FAULT-MATRIX.md §5-D2）。

---

## 3. 自定位约定

`$SKILL_DIR` = **本 SKILL.md 所在目录的绝对路径**（平台安装期为 `/skills/weekly-skill`）。
脚本用 `os.path.dirname(os.path.abspath(__file__))` 解析 `templates/`、`references/`，
**cwd 与技能根不同也能跑**（本版把这一点也纳入了注入实验：所有 23 次主流程都是从
包外临时目录启动的）。

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

| 来源 | 内容 | 缺失时（实测行为，见 FAULT-MATRIX） |
|-|-|-|
| `/input/case.json` | `case_id`、`figures` 规格、`data` 引用、`output_contract`、`manual_confirmations` | **必需**；不存在/不可解析 → 最小诚实信封（6 键）+ exit 1（I1/I2） |
| `/input/task.md` | 任务说明 | 自动找同目录；仍无 → 记 `uncertainty` |
| 源数据表 | CSV / TSV / JSON | 一个都没有 → `partial` + exit 2，且**点名缺失**（I3/I4） |
| 生物源材料 | `entities_file` JSON 或 `material` 文本 | 机制图降级（FM-M1） |

`case.json` 形态兼容：顶层对象 / `{"cases":[...]}` / 数组取首项（数组形态实测：I5）；
图规格可放 `figures` / `figure` / `figure_spec`；数据可放 `data` / `data_files` / `sources`。

### 4.2 输出（`/app/output`，UTF-8）

| 文件 | 硬要求 |
|-|-|
| `figure-<id>.svg` | 分层 `<g id="layer-*">`；`<metadata id='provenance'>`；图元带 `data-*`；**文字永远是真实 `<text>`，不转曲**（G5） |
| `figure-<id>.png` / `.pdf` | 与 SVG 逐元素同源；PDF 元数据时间戳已归一化 |
| `data_manifest.json` | 每图元登记 `column + row_index + value`（或实体 `id`/`cite`），与 SVG 的 `data-*` 同名对齐 |
| `validation.json` | 八类标注检查逐项 `ok/warn/fail` |
| `mapcheck_report.json` | 数据↔图元双向核对：`mismatched=0 unmatched=0` |
| `figcheck_report.json` | G1–G8 硬门报告 |
| `result.json` | 契约字段全回显（四形态，禁 null）+ `case_id` + status/sources/uncertainty/change_records/checkpoints/gates/artifacts_sha256 |
| `/app/work/` | 中间产物 `extract.json`、`spec_lint.json` |

**产物可能不齐**——这是本版特意测过的：I3/I4/I6/I7 都只产出**部分**图（3 个文件或 0 个文件），
而 `result.json` 一定写出来并如实说清缺什么。**"有 result.json"不等于"全部成功"**，
请读 `status` 与 `uncertainty`。

---

## 5. 执行链路（CP1–CP6，每步都标了"这步失败会怎样"）

> 与"只写 happy path"的做法不同，下表第三列是**这步出错时的实测表现**，
> 括号里的编号是 `references/FAULT-MATRIX.md` 的注入用例号，可逐条复跑核对。

| 步 | 动作 | 这步出错时（实测） |
|-|-|-|
| **CP1** | 盘材料：列文件、算 sha256、记行数列名；读 `task.md` | 数据表缺失 → `partial` + `uncertainty` 点名（**I3**）；表为空 → 同上（**I4**）；case.json 不存在/坏 → 6 键信封 + exit 1（**I1/I2**） |
| **CP2** | 抽取：列画像 + 实体/关系（`extract.py`） | 模块缺失 → import 失败、**不写信封**、exit 1（**D4**） |
| **CP3** | 规格门：`spec_lint.py`（exit 2 = 有 error，不得进 CP4） | 列名写错 → 图失败但流程继续（**I7**）；压根没图规格 → `partial` 且失败记录点名原因（**I6**） |
| **CP4** | 生成：`main.py` → Scene → SVG + PNG/PDF | 缺 Pillow → **本应降级却 FATAL**（**D2**，已知缺陷） |
| **CP5** | 双校验：`mapcheck`（数据↔图元）+ `figcheck`（G1–G8）+ `verify_rerun`（确定性） | 契约含 `""` → 曾误判 G2（**K1**，已修）；Pillow 缺失 → 在 figcheck 处抛错（**D2**） |
| **CP6** | 契约落地：`check_contract.py` 复核字段覆盖 | 契约形态非法 → 曾谎报 applied=true（**K6**，已修）；无契约 → `applied=false` 且不臆造（**K5**） |

命令（脚本自定位，任一 cwd 均可；`S`/`OUT`/`WORK`/`CASE` 为示例变量）：

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

## 6. 故障注入实验台（本版核心）

```bash
# 全套 23 条（包外工作目录；源包只读，脚本自己复制副本）
python "$SKILL_DIR/scripts/fault_inject.py" \
       --src "$SKILL_DIR" --workdir /tmp/fault-work --out /tmp/fault-work/report.json

# 只复核某几条（例如刚改过的契约相关）
python "$SKILL_DIR/scripts/fault_inject.py" --src "$SKILL_DIR" --only K1,K6,T2 --keep
```

**四形态与检查重点**

| 族 | 注入对象 | 本族要回答的问题 |
|-|-|-|
| **I** 输入 | case.json / 源数据表（删、写坏、清空、改列名、改数组形态） | 材料坏了，会不会**假装成功**？ |
| **T** 模板 | `templates/*.json` 删或写坏；`--style` 拼错 | 装饰层回退会不会**悄悄生效**？ |
| **D** 依赖 | 删 `scripts/*.py`；屏蔽 Pillow；清空字体目录 | 可选件缺失时**降到哪一层**？ |
| **K** 契约 | 四形态 + 无契约 + 非法形态 + 不产出字段 | 契约不齐时是**补齐**、**留空**还是**撒谎**？ |

**退出码语义**：`0` = 全部用例实测与期望一致；`2` = 有对不上的（`summary.mismatches` 列出编号）；
`1` = 用法错误。**注意 `2` 是注入台的判定失败，不是被测包的失败**——它意味着
"包的行为与文档声明不一致"，正是这套实验要找的东西。

---

## 7. 决策规则（D1–D18，其中 4 条来自注入结论）

| # | 触发 | 动作 | 失败降级 |
|-|-|-|-|
| D1 | 要画任何图形元素 | 必须可溯源（文件/列/行 或 实体 id/cite） | 无法溯源 → 不画；必要时虚线占位 + `uncertainty` |
| D2 | 生成坐标轴 | 轴标签带单位；刻度覆盖数据 + 5% 余量 | 单位拿不到 → 保留无标签 + `warn` |
| D3 | 画图例 | 每系列恰一图例项，id 一致 | 无法对齐 → 修 spec 重跑（`fail` 阻止 completed） |
| D4 | 引用科学实体名 | 取材料原文，不翻译、不改拼写 | 不确定 → 保留原文 + `uncertain`，确认后才上图 |
| D5 | 文本含 CJK | CJK 字体族回退链 | PNG 缺字 → 记 `warn`（SVG 不受影响） |
| D6 | 标注显著性 | 只转述材料给的 p 值与检验名 | 源没给 → **不画**该标注 + `uncertainty` |
| D7 | 输出 SVG | 分层 + 稳定 id + metadata 溯源块 | 渲染不可用 → **先保 SVG 落盘** |
| D8 | 画误差线 | 语义（SE/SD/CI）以源元数据为准 | 源未标 → 记 `uncertainty`，**不猜** |
| D9 | 遇空值/NaN | 不补造，跳过并计数 | 整列无值 → 报错 + `uncertainty` |
| D10 | 任何维度未完成 | `status=partial` + 写明原因与复验路径 | ——（兜底：**禁止**把失败写成完成） |
| D11 | 人工改动 | 写 `change_records`（时间戳+内容） | —— |
| D12 | 做 A/B 对照 | 同输入、同版本、同导出参数；本包侧重跑须字节级稳定 | 有差异 → 定位随机源，不搪塞 |
| **D13** | **样式模板缺失/损坏，或 `--style` 不是已知预设** | **回退 default，并写一条 `uncertainty` 点名缺什么、有哪些可用** | ——（本版由 P3 新增：回退**不得静默**） |
| **D13-2** | **案例一个图规格都没有**（`figures`/`figure`/`figure_spec` 全缺） | **不臆造占位图**：图规格取空列表 + `uncertainty` 说明 + `status=failed` | ——（本版由 P8 新增：宁可失败，不可编造） |
| D14 | 标签过长 / 图例遮挡 / 节点重叠 | 旋转 30°、图例移出绘图区、手给节点坐标 | 仍重叠 → `warn` + `uncertainty` |
| **D15** | **`output_contract` 是四形态之外的形态** | **不回显任何契约字段，`output_contract_applied=false` + 说明** | ——（本版由 P4 新增：**不得谎报已应用**） |
| D16 | 契约声明本 Skill 不产出的字段 | 给声明容器类型的空值 + 写明"本 Skill 不产出" | ——（**不做假映射**） |
| D17 | 契约含非法项（数字/空串/非字符串） | **跳过该项**，其余照常回显 | ——（本版由 P1 新增：判定口径 = **非空字符串才算字段**） |
| D18 | 写 `status` | 与产物事实严格自洽：有 `fail`/缺口 → 不得 `completed`；无图 → `partial`/`failed` | —— |

**规则冲突优先级**：① 诚实 > 完整（D10 压过"把字段填满"）② 可核验 > 好看（D1/D3/D6/D8）
③ 保源 > 保预览（D5/D7 先保 SVG 与 JSON）④ 阻断 > 带病交付（D3/D6 的 `fail` 拦住 `completed`）。

---

## 8. 交付前自查

- [ ] 跑过 `fault_inject.py`，`mismatch=0`（或已知 mismatch 都已登记在 FAULT-MATRIX.md）
- [ ] `mapcheck` 0 mismatch；`spec_lint` exit 0；`figcheck` G1–G8 全过
- [ ] `verify_rerun` 归一化后 `differ=0`；`check_contract` `missing=0 null=0`
- [ ] 轴标签带单位；图例↔系列一一对应；显著性只转述；实体名与原文一致
- [ ] SVG 分层、含 metadata、真实 `<text>` 未转曲；PNG/PDF 可打开
- [ ] `status` 与产物事实自洽；`uncertainty` 里没有"已知却没说"的事项
- [ ] 中文标签字体回退生效或已记 `uncertainty`
- [ ] 无编造数据、无网络访问、无凭据写入

---

## 9. 资源清单（相对 `$SKILL_DIR`）

```
SKILL.md                            本文件（注入结论 + CP1–CP6 + D1–D18 + 实验台用法）
README.md                           依赖/安装/调用/退出码/自检/维护
TEST.md                             真机实测记录（含 23 条注入的实测摘录与正常路径回归）
COMPARE.md                          与"直接调通用绘图库"的对照方案
GITHUB_URL.txt                      公开作品链接（单行）
scripts/fault_inject.py             ★ 本版主件：四形态故障注入台（23 条，可 --only 定点复跑）
scripts/main.py                     编排入口 CP1→CP6（--case/--out）
scripts/chartkit.py                 渲染引擎（Scene → SVG/PNG/PDF + 八类校验 + PDF 确定性归一化）
scripts/extract.py                  CP2：列画像 + 实体/关系抽取
scripts/spec_lint.py                CP3：规格门（E1–E10；exit 2 = 有 error）
scripts/figcheck.py                 CP5：G1–G8 硬门（本版修了契约字段判定口径）
scripts/mapcheck.py                 CP5：数据↔图元双向核对（容差 1e-9）
scripts/verify_rerun.py             确定性再跑 / artifacts sha256
scripts/check_contract.py           CP6：契约字段覆盖自查
scripts/cjkfont.py                  中文字体发现与回退
scripts/svgtext.py                  SVG 文本转义/清理 + 防转曲检查
templates/journal_styles.json       期刊样式预设（回退行为见 D13）
templates/figure_map.schema.json    图规格声明式契约（**仅文档，运行期不读取**，见 N2）
templates/result.template.json      result.json 信封模板
templates/entity_glossary.json      关系规则字典 + 实体词表
references/FAULT-MATRIX.md          ★ 本版主件：23 条注入的逐行实测 + 6 条查出的缺陷
references/OUTPUT_CONTRACT.md       结果契约（机器可读字段块 + G1–G8 + 四形态）
references/RUBRIC_MAP.md            五维评分 → 本包落点
references/failure-modes.md         失败模式全表（口径已在 FAULT-MATRIX 中被实测复核）
references/audit-rules.md           审计规则（检查项/级别/处置）
references/encoding-spec.md         CJK/单位/实体命名/SVG 编码规范
references/typesetting-presets.md   期刊排版预设说明
references/workorder-field-map.md   输入 → 字段 → 输出 映射链
examples/                           合成示例输入（非平台案例）
```

调用方式：

```bash
python "$SKILL_DIR/scripts/main.py"           --case /input/case.json --out /app/output
python "$SKILL_DIR/scripts/check_contract.py" --result /app/output/result.json --case /input/case.json
python "$SKILL_DIR/scripts/figcheck.py"       --dir /app/output --case /input/case.json
python "$SKILL_DIR/scripts/mapcheck.py"       --dir /app/output --case /input/case.json
python "$SKILL_DIR/scripts/fault_inject.py"   --src "$SKILL_DIR" --workdir /tmp/fw
```

---

## 10. 限制（如实声明，不掩饰）

1. **注入只覆盖 23 种故障 + 11 条图型/材料探针**（`TEST.md` T10），不是全部故障空间：
   并发写冲突、磁盘满、超长文本、非 UTF-8 输入、图像尺寸越界**没有测**。
2. **`fault_inject.py` 只测"能否如实报告"，不测"图画得对不对"** —— 后者由
   `mapcheck`/`figcheck` 与 `references/audit-rules.md` 负责。
3. **D2 是未修的已知缺口**：缺 Pillow 时渲染层会降级，但 `figcheck` 会把整次运行打成 `failed`，
   已写出的 SVG 不进入 `result.json.outputs`。修它需要改动校验器语义（G6 的判定条件），
   超出"只修真实缺陷且不改退出码语义"的边界，故本轮**只登记、不修**，并给出部署前自检命令（§2）。
4. **模块缺失时不会有 `result.json`**（N3）：`import chartkit` 早于 `main()` 的兜底逻辑。
   下游不能假设"跑过 main.py 就一定有信封"，必须同时看退出码。
5. **不做统计推断**：显著性计算、拟合、检验不在范围内，只转述材料给的数值（D6）。
6. **机制/通路图自动布局是启发式的**；复杂通路建议在 spec 手给节点 x/y（D14）。
7. **PDF 预览是光栅预览嵌入 PDF**；矢量可编辑源以 SVG 为准。
8. **中文字体依赖运行环境**；缺字体时 SVG 走回退链、PNG 记 warn（D5）。
9. **词表扫描只是候选提示**，不替代 Agent 对源材料的确认（D4）。
