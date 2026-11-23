---
name: biological-mechanism-pathway-diagram
description: >-
  把科研机制/通路材料（文本、Markdown、表格或 PDF 中的通路描述）转成可逐条核验的
  生物机制图与通路图：从真实材料抽取实体与相互作用（激活/抑制/结合/修饰/转运），
  按区室约束布局（胞外—膜—胞质—核），生成带语义箭头的可编辑分层 SVG 源文件及
  PNG/PDF 预览，自动执行拓扑审计与图例/数据编码审计，并输出符合契约的 result.json。
  Use when the task asks to draw, generate, edit, re-export or validate a biological
  mechanism map, pathway diagram, signaling cascade, regulatory network or flow
  diagram (figures group of the biology mechanism & pathway challenge), including
  tasks that require editable sources with per-element provenance.
  本版增量：随包提供字节级确定性探针 `scripts/determinism.py` 与 `references/DETERMINISM.md` 实测表（逐产物 sha256、易变字段逐条点名、三条稳定化配方）。
---

# biological-mechanism-pathway-diagram（合规文本包 · 图件运行时生成）

机制图的科学性不看图画得是否复杂，而看三件事：**每个实体和每条边能否回溯到输入材料或
权威命名；图例、颜色映射与图形本身是否自洽；别人能否打开可编辑源文件改一个标签并重新
导出。** 本 Skill 围绕这三件事设计，并把"正确"从口头承诺变成机器可执行的检查点
（CP1–CP4）与决策规则（D1–D12）。

## 0. 资源形态（先读这条，它决定包怎么用）

本包**只包含文本资源**，遵守运行时契约的硬约束：
`at most 50 UTF-8 text files, 500KB each and 2MB total, no symlinks`。

- 允许的扩展名只有七种：`.md .py .json .txt .csv .yaml .yml`；
- 包内**没有任何图片 / PDF / 演示文稿等二进制文件**——`diagram.svg`、`diagram.png`、
  `diagram.pdf` 一律由 `scripts/` 在**运行时现场生成**（`pathway_svg.py` 写 SVG，
  `mpl_backend.py` 渲染 PNG/PDF；matplotlib 缺失时降级为仅 SVG 并如实记录）；
- `examples/output/` 里只有示例案例上实跑得到的 **JSON 产物**与文字化的
  `examples/EXPECTED-OUTPUT.md`（应产出文件清单与契约字段），不是预置图件；
- 运行期产物（含二进制图件）写在 `--out` 目录，属于运行时资产，与"技能资源"是两件事：
  技能资源必须全是文本，运行产物可以任意格式。

## 1. 用途与适用条件

- 适用：生物机制图 / 通路图 / 信号级联 / 调控网络 / 流程图 / 图表编辑；同样适用于
  "把一段机制文字变成图""修改他人图稿的一个错误箭头""按数据给节点上色""补图例"。
- 不适用：数值统计与统计分析结论、实验方案设计、论文写作与版式美化（相邻课题负责）。
  本 Skill 只对图形中的科学内容表达、布局、可编辑性与导出质量负责。
- 运行前提：Python 3（标准库即可生成可编辑 SVG；matplotlib 可选，用于 PNG/PDF 预览，
  缺失时自动降级并如实记录）。

## 2. 输入与输出

**输入（平台运行时）**
- `/input/case.json`——固定字段：`case_id`（必填标识）、`title`、`task`、
  `materials`（材料文件路径列表）、`render`（画布尺寸，可选）、`output_contract`
  （契约字段，凡声明字段必须出现在 result.json 顶层，缺省按类型给 "" / [] / {} / false）。
- `/input/task.md`——任务说明（可能引用图号、材料范围、必需元素、导出格式）。
- `/input/**` 或材料目录——科研材料（正文/表格/PDF 等），**必须实际读取文件内容**，
  不得根据文件名猜测内容，不得用领域标签脑补数据。

**输出（平台运行时，写入 /app/output）**
- `result.json`——结构化结果，字段见 `references/OUTPUT_CONTRACT.md`（含 case_id、
  status、deliverables、scientific_content、evidence_sources、topology、
  legend_audit、gates、uncertainty、change_records、export_checks、self_check 及
  case.json output_contract 的全部字段）。
- `diagram.svg`——**可编辑源文件**：分层 `<g>`（layer-compartment / layer-edge /
  layer-entity / layer-label / layer-title / layer-legend / layer-meta），每个元素带
  `data-id / data-type / data-source / data-compartment` 属性，改一个标签即可重新导出。
- `diagram.png`、`diagram.pdf`——预览/矢量导出（同一布局引擎渲染，与 SVG 一致）。
- `model.json`——机制规格（规范化实体/边/图例模型，独立复核实体清单与边清单用）。
- `topology.json`、`legend_audit.json`——拓扑审计与图例/数据编码审计产物。

## 3. 执行步骤（检查点流水线）

> 全部脚本位于技能根目录的 `scripts/` 下；脚本通过 `os.path.dirname(__file__)` 自定位，
> **不依赖当前工作目录**。本文档所有命令都用 `$SKILL_DIR` 指向技能根目录
> （含 `SKILL.md` 的那一层），因此从任意 cwd 复制粘贴都能跑。先确定一次：
>
> ```bash
> # 平台容器：技能被安装在 /skills/weekly-skill
> export SKILL_DIR=/skills/weekly-skill
> # 本机 / 其他环境：指向你解压出来的包根目录（可用 pwd 确认该目录下有 SKILL.md）
> # export SKILL_DIR=/path/to/challenge-83d4f050
> python3 "$SKILL_DIR/scripts/main.py" --help   # 自检：打印参数帮助即路径正确
> ```
>
> `--case examples/case.json` 这类相对路径也可用：main.py 先按 cwd 解析，
> 找不到时再回退到技能根目录解析（`--model-file`、`--materials-dir` 请写完整路径）。

### CP1：先读真实文件（禁止跳过）
用 `read` 读取 `/input/case.json` 与 `/input/task.md`，再用 `read`/`glob` 列出并读取
材料目录中的每个文件（正文、表格、PDF 文稿）。提取三样东西：
1. 任务要求（画什么图、必须覆盖哪些元素、导出格式）；
2. 事实（实体、区室、相互作用、方向、数据数值）；**每个事实记录出处（文件+行号）**；
3. 约束（色调、符号、模板风格、图号要求）。
材料缺失/目录为空时 main.py 的 CP1 检查会直接 failed——先补齐材料或改用 --model-file。

### CP2：生成机制规格（schema 门前置）
```bash
python3 "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output --verbose
```
- 对结构化材料（表格、`A | 动词 | B` 行、`- A 动词 B（证据）`、数据映射声明），
  `scripts/extract.py` 生成"草稿规格" `model.json`，每条实体/边带源文件与行号。
- 草稿/手工规格必须先通过 `assets/mechanism-spec.schema.json`（类型枚举/必需字段；
  对**原始未归一化**规格校验，防止未知类型被静默改写成 other）。schema 不过 → failed，
  修正规格后重跑。
- 纯散文材料或 PDF 无法结构化时，main.py 会如实报告 `failed`——此时进入 CP2b 手工建规格。

### CP2b：手工建规格（散文/PDF 材料）
Agent 阅读材料文本，按 `references/mechanism-spec.md` §1 的结构手写
`/app/work/model.json`（实体/边/来源/图例），然后：
```bash
python3 "$SKILL_DIR/scripts/main.py" --model-file /app/work/model.json \
    --case /input/case.json --out /app/output
```

### CP3：人工核验规格（Agent 必须逐条核对，不得直接交付草稿）
打开 `/app/work/model.json`（或草稿产物），逐条对照**实际读到的材料文本**：
- 实体是否真实存在、名称书写是否正确（基因斜体/蛋白正体、物种前缀、复合物与家族成员）；
- 相互作用类型是否判对（结合/激活/抑制/修饰/转运），方向是否与原文一致；
- 证据强度（strong/moderate/weak）、uncertain、反馈环标记、区室归属是否正确；
- 材料未提及但图画了的内容：source.kind 必须标 `assumption` 或 `common_knowledge`，
  并在 `uncertainty` 中说明原因；
- 数据值（表达量等）必须能定位到来源行，否则不得用于图面颜色编码。
核对完成把 `extraction.verified_by_agent` 置为 `true`，在 `change_records` 逐条记录
"改了什么/为什么改"，再用上面的 `--model-file` 命令重跑。
> 使用 `templates/relation-checklist-template.md`（实体/边/图例/拓扑/导出五表）作为核对
> 载体，逐行填写出处——这张表是核验与追溯的执行证据。

### CP4：布局、渲染与双审计（脚本自动，须通读结果）
- `layout.py` 按区室带确定性布局（胞外→膜→胞质→核，核嵌入胞质带；跨膜受体在膜带内；
  反馈环右侧绕行）；`pathway_svg.py` 写可编辑分层 SVG；`mpl_backend.py` 渲染 PNG/PDF。
- `topology.py` 拓扑审计（P01–P08：id/端点/方向/同名消歧/重复边/自环/反馈标注/区室词表）；
- `legend_audit.py` 图例与数据编码审计（L01–L08, E01–E02：图例覆盖、箭头=图例、
  颜色⊆图例∪映射、虚线语义、线宽映射、图层命名、数值溯源、色带端点）；
- `validate_figure.py` 聚合 M/T/P/L/E/S/F/D 系列检查 + 契约后置检查 +
  确定性探针（model_sha16/svg_sha16）；`check_contract.py` 独立复查 result.json 契约
  与 G1–G8 硬性门。任何 `fail` 会把 status 降为 partial/failed，必须处理。

### CP5：写 result.json 并自查（交付前逐条过）
- status：`success`（阻断检查全过 + 提取已人工核验 + 门 G1–G8 全过）／`partial`
  （有 fail/warn 或自动草稿未核验，全部列明）／`failed`（无法产出源文件或 schema 不过）。
- 自查清单（对照 `references/OUTPUT_CONTRACT.md` §1）：
- [ ] 我实际读取了 case.json / task.md / 全部材料，没有凭文件名猜内容；
- [ ] 实体、边、图例项与材料一一对应，每条都有 source（文件:行）；
- [ ] 基因/蛋白/复合物/小分子/区室没有混用，命名规范（mechanism-spec.md §2）；
- [ ] 每个箭头语义 = 图例声明；虚线只在证据弱/不确定时出现；
- [ ] 数据映射（颜色/线宽/大小）与图例、图面三方一致，数值可溯源；
- [ ] SVG 可编辑源已生成、7 层齐全且 well-formed；PNG/PDF 预览（或明确记录缺失原因）；
- [ ] result.json 契约字段齐全（含 output_contract 声明字段），无 null；
- [ ] topology.json / legend_audit.json 生成；uncertainty / change_records 诚实；
- [ ] 命令与产物记录到 TEST.md，任何失败都有说明。

## 4. 决策规则（D1–Dn，遇情况先查表）

| # | 情形 | 决策 |
|---|---|---|
| D1 | 材料未写上下游方向 | 不臆造方向：画结合类无向边并标 uncertain；必要时只给无方向暗示的布局 |
| D2 | 同名基因与蛋白同时出现 | 拆成两个实体（基因斜体/蛋白正体），note 写明依据；无法区分则标 uncertain |
| D3 | 同一蛋白多区室（如胞质 ERK / 核内 ERK） | 按区室拆实体，每个实体 note 注明去向，避免跨膜语义混淆（P04b） |
| D4 | 材料数值与图面意图矛盾 | 以材料原文为准；在 uncertainty 与 change_records 都标注矛盾点 |
| D5 | 逆流边（下游→上游） | 若为反馈/回流：标 `feedback=true` 右侧绕行；否则必须给科学理由并在 uncertainty 说明（P03/P07） |
| D6 | 材料为 PDF/扫描件 | 用工具抽取文本转成文本材料，或人工建规格（CP2b），记录 extraction.method |
| D7 | 图例缺在用类型 / 颜色不在图例内 | 阻断：补图例或改回图例色，重跑（L01/L02/L05 是 fail） |
| D8 | 数据值缺来源 | 阻断：补充 source；或降为 assumption 并进 uncertainty（E01/T03） |
| D9 | matplotlib/字体缺失 | 保留可编辑 SVG；PNG/PDF 缺失如实记录；字体缺失告警并写 export_checks（SVG 不受影响） |
| D10 | 图面元素过多不可读 | 减小字号/收缩节点，或拆分子图并记录 layout.warnings |
| D11 | 机制规格 schema 不过 | 阻断渲染（failed）：按 schema 违规清单修正后重跑（CP2） |
| D12 | 材料无实体/关系 | 明确 failed，不画空图凑数，给出补救路径（补材料或 --model-file） |

## 5. 实体、命名规范速查

| 类型 | 图形 | 书写 |
|---|---|---|
| 基因 gene | 矩形、无圆角 | 斜体（如 *MYC*），大写；物种前缀按权威命名 |
| 蛋白质 protein | 圆角矩形 | 正体（如 MYC 蛋白） |
| 复合物 complex | 圆角矩形+内描边 | 成分间用 "–"（如 PI3K–AKT 复合物） |
| RNA | 圆角矩形虚线边 | 正体 |
| 小分子/配体 | 圆形 | 正体（如 ATP、PIP3） |

完整规范见 `references/mechanism-spec.md`（命名/区室/导出）与
`references/legend-encoding.md`（箭头语义/数据编码/调色板）。

## 6. 相互作用语义（箭头类型=科学论断）

| 类型 | 箭头 | 颜色 | 语义 |
|---|---|---|---|
| activation 激活/促进 | 实心三角形 | 绿 #2E7D32 | 促进/激活 |
| inhibition 抑制/阻断 | 端点横杠 (T-bar) | 红 #C0392B | 抑制/阻断 |
| binding 结合/互作/募集 | 无箭头实线 | 蓝 #1F4E79 | 物理结合、募集 |
| modification 修饰 | 端点圆点，可带"P"标签 | 橙 #B9770E | 磷酸化/泛素化等 |
| transport 转运/转位 | 端点菱形 | 紫 #6C3483 | 转运、转位、内化 |

- 边宽 = 证据强度：strong 2.8 / moderate 2.2 / weak 1.6；
- **虚线只表达"证据弱/间接/不确定"**，与边类型无关（L06 强制）；
- 反馈环：`edge.feedback=true`，布局在右侧绕行，箭头回到上游节点；
- 颜色/线宽集中在 `assets/palettes.json`，改一处全图与图例同步。

## 7. 布局与图例规范

- 信号流向自上而下：胞外→膜→胞质→核；跨膜受体必须在膜带内；核内因子在核框内。
- 图例必须覆盖图面上所有用到的实体类型与边类型；图例色/线宽与图面实际使用逐值一致
  （L01/L02/L04/L05/L07 强制）。
- 数据编码（若材料给数值）：实体填充色按映射字段插值（默认 表达量 低 #FFF7E0 → 高
  #1F4E79），图例画出色带与"低/高"标签；没有数值时用类型默认色并在图例注明。

## 8. 异常处理（速查，完整版见 references/failure-modes.md）

| 异常 | 处置 | 记录位置 |
|---|---|---|
| 材料缺方向（不知上下游） | 只画无向边语义（结合类），标注 uncertain；不臆造方向 | uncertainty + 边 uncertain=true |
| 同名基因/蛋白歧义 | 分成两个实体并注明；无法区分时标 uncertain 并说明 | uncertainty |
| 输入数据与图示矛盾 | 以材料原文为准，图与 result 都标注矛盾点 | uncertainty + change_records |
| 材料为 PDF 无法结构化解析 | Agent 抽文本转成文本材料或手工建 model.json（--model-file） | extraction.method=manual |
| 机制规格不过 schema 门 | 阻断，修正后重跑（D11） | status=failed |
| 字体/图元缺失 | SVG 用系统字体栈；PNG 缺中文字体时告警并写入 export_checks | preview warnings |
| 预览导出失败 | 保留 SVG 源文件，status=partial，说明 matplotlib 是否可用 | deliverables/status |
| 图面元素过多不可读 | 减小默认字号/收缩节点宽度，或拆分子图并记录 | layout.warnings + uncertainty |
| 目标格式不支持 | 至少交付 SVG + PNG；其他格式如实说明不支持 | export_checks |
| 材料里没有实体/关系 | 明确 failed，不画空图凑数，给出补救路径 | status=failed |

## 9. 反预制答案规则（重要）

- `examples/` 目录中的一切（case、材料、模型、输出）都是**演示示例，非正式案例**：
  图内与 result.json 均带"示例"标记。正式运行**禁止**把 examples 的实体/边/数值抄入
  正式输出；平台案例的材料与示例材料不同，必须现场从真实材料推导。
- result.json 的来源/数值/评分一律按本次运行实际填写；不给自己编造 benchmark 分数。
- `assets/result.template.json` 仅为结构模板（示例），不得冒充运行产物。

## 10. 限制与维护

- SVG 为手写图层制式，供 SVG 生态（浏览器、Inkscape、draw.io 导入、脚本改属性）编辑；
  不做 Word/PPT 内嵌途径（如需可另用 office 类 Skill 二次嵌入）。
- 自动抽取器只处理结构化语句；散文材料依赖 Agent 人工抽取（CP3 强制），这是刻意设计
  ——准确率优先于全自动。
- 图件不是随包资源：本包不含 SVG/PNG/PDF，每次运行由脚本在 `--out` 目录现场生成；
  因此"包里看不到图"是设计而非缺失（见 §0 与 `examples/EXPECTED-OUTPUT.md`）。
- 风格常量集中在 `assets/palettes.json`（缺省时回退 `scripts/model.py` 内置默认值）；
  契约/门集中在 `references/OUTPUT_CONTRACT.md`；改动时同步更新 TEST.md 实测记录，
  并在 `worklog.md` 追加一条带时间的变更记录。

## 11. 参考资料（技能内相对路径，均相对 `$SKILL_DIR`）

- `references/mechanism-spec.md`——机制规格与绘图规范（命名/区室/导出/校验一览）。
- `references/legend-encoding.md`——箭头语义/数据编码/调色板/审计规则。
- `references/OUTPUT_CONTRACT.md`——result.json 字段契约 + G1–G8 硬性门（机器校验基准）。
- `references/RUBRIC_MAP.md`——五维评分（40/25/15/10/10）→ 本包文件与机制逐条映射。
- `references/failure-modes.md`——失败模式、降级策略与处置记录位置。
- `assets/mechanism-spec.schema.json`——机制规格 schema（CP2 门）。
- `assets/palettes.json`——调色板/glyph 语义（单点改色）。
- `assets/result.template.json`——result.json 结构模板。
- `templates/relation-checklist-template.md`——关系核对清单（CP3 人工核验载体）。
- `examples/`——最小可运行示例：输入（`case.json`/`task.md`/`materials/`/`model.example.json`）
  ＋ 期望输出说明（`EXPECTED-OUTPUT.md`）＋ 实跑 JSON 产物（`output/`），全部标注"示例，非正式案例"。
- `README.md`——依赖/安装/适用范围/限制/维护；`TEST.md`——怎么自测与期望输出；
  `COMPARE.md`——与基础 Agent 的同输入对照方案；`worklog.md`——构建与合规重打包记录。

## 附:本版增量 —— 字节级确定性（同输入重跑的 sha256 清单）

> 上文 §0–§11 是基线正文，逐字保留。本章只写本版在基线上**新增**的那一条轴：
> 把"同输入重跑是否得到同一份产物"从一句承诺变成可复算的测量。完整论述、逐行证据与
> 未覆盖声明见 `references/DETERMINISM.md`（本版轴文档）；机器可读结果见包根
> `determinism_report.json`（本机实跑产物，不是预置答案、不是正式案例结果）。

### A1. 新增入口与运行命令

| 入口 | 参数 | 说明 |
|-|-|-|
| `scripts/determinism.py` | `--skill --case --model-file --no-model-file --runs --work --report --out --formats --dpi --python --strict --clean --json --verbose` | **本版新增**：字节级确定性探针（只依赖标准库） |

基线入口的参数面（本次复跑逐条可用）：`scripts/main.py --case --task --out --materials-dir --model-file
--formats --dpi --verbose`（`--formats` 默认 `svg,png,pdf`，`--dpi` 默认 150，`--materials-dir` 可重复）；
独立复查入口 `scripts/check_contract.py --result <out>/result.json --case <case.json>` 与
`scripts/validate_figure.py --out <out> --case <case.json>`。

```bash
export SKILL_DIR=/skills/weekly-skill          # 含 SKILL.md 的那一层
python3 "$SKILL_DIR/scripts/determinism.py" --help

# 默认 5 次运行（跨进程 / 跨 cwd / 跨 PYTHONHASHSEED），报告写到包根；退出码应为 0
python3 "$SKILL_DIR/scripts/determinism.py" --runs 5 \
    --work /tmp/det --report "$SKILL_DIR/determinism_report.json"

python3 "$SKILL_DIR/scripts/determinism.py" --json > /tmp/det.json    # 只要机器可读结果
python3 "$SKILL_DIR/scripts/determinism.py" --strict                 # 原始字节不一致 → 退出码 3
```

退出码：`0` = 规范化后全部产物逐字节一致；`2` = 主流程某次非期望退出（环境/输入问题，不是
不确定性问题）；`3` = 规范化后仍不一致（真不可复现）；`4` = 参数/路径错误。

每次运行都是**新解释器进程**，命令字面量逐字相同（`--out out` 用相对路径，使 `provenance.command`
在各次运行间一致），只轮转两个变量：**cwd**（技能根 / `scripts` / 案例目录 / `examples` / 工作根）
与 **`PYTHONHASHSEED`**（`0` / `1` / `12345` / `random` / 不设置）。每次运行后立刻对输出目录
**全部产物**取 sha256，再跨运行比对。

### A2. 判据（三条都成立才允许写"可复现"）

| # | 判据 | 内容 |
|-|-|-|
| J1 | 原始字节稳定清单 | 存在明确清单，其成员在任何 cwd / 任何 `PYTHONHASHSEED` / 任何进程下 sha256 相同 |
| J2 | 易变清单被逐字段点名 | 不稳定的产物必须指出**哪个字节 / 哪个 JSON 路径**不稳定，并区分"故意"与"缺陷" |
| J3 | 稳定化后逐字节一致 | 施加文档化规则后全部产物哈希一致（JSON 投影 / PDF 规范化 / 环境配方三条独立证据同真） |

只满足 J1 不算"可复现"（那只是"大部分稳定"）。

### A3. 实测数字：逐产物 sha256（5 次运行）

环境：CPython **3.13.9** / win32 / matplotlib **3.10.6** / Pillow **12.3.0**。

| 产物 | 字节 | sha256（前 16 位） | 不同哈希数 | 判定 |
|-|-|-|-|-|
| `diagram.svg` | 17771 | `27f344a0dfb2e90f` | 1 | ✅ 稳定 |
| `diagram.png` | 203655 | `9137715961238f3f` | 1 | ✅ 稳定（PNG 无 `tIME` 块，只有恒定的 `tEXt`） |
| `model.json` | 11418 | `f93a20a283492f73` | 1 | ✅ 稳定 |
| `topology.json` | 1434 | `eb826fc5557fccfc` | 1 | ✅ 稳定 |
| `legend_audit.json` | 1807 | `efdb1805c839d648` | 1 | ✅ 稳定 |
| `diagram.pdf` | 108045 | `79fdc09f7310e7dd`（每次不同，示例） | **5** | ❌ 仅 `/CreationDate` 秒位（1–2 字节，偏移 104020 起） |
| `result.json` | 28888–29056 | `257ca36c870501f0`（每次不同，示例） | **5** | ❌ 8 个 JSON 路径（见下表） |

**一句话版**：7 个产物里 **5 个**在 5 次跨 cwd / 跨哈希种子的运行间逐字节相同；`diagram.pdf` 只差
**1 处、1–2 个字节**；`result.json` 差在 **8 个 JSON 路径**。这 5 个稳定产物是 sha256 可跨机比对的：
它们的字节只由（模型 × 布局 × 图例）决定，不含时间戳、不含绝对路径。

**复跑核对（2026-11-23，同环境）**：这 5 个稳定 sha256 用 `--runs 5` 重跑后**逐位一致**；两个不稳定
产物的示例哈希按设计每次不同（`distinct_sha256 = 5`），可复现的结论是**差异位置与长度**，不是哈希本身。

**易变字段（观测到的全部差异路径，`determinism_report.json → volatile_fields[]`）**：

| JSON 路径 | 性质 | 稳定化 |
|-|-|-|
| `$.provenance.ts`、`$.change_records[0..2].ts` | **故意**：真实运行时间（秒级） | 投影掩码 |
| `$.provenance.case_file`、`$.change_records[0..1].why` | **缺陷级：cwd 泄漏**（`portable_path()` 在路径不属于技能根时退化为"相对当前工作目录"渲染） | 投影掩码，或**固定 cwd** |
| `$.self_check.checks[30].detail` | 二阶：内含上一步 `result.json` 的字节数 | 随路径字段一起掩码 |

⇒ 因此"字节级可复现"在本包里等价于**把 cwd 与输入一起固定**；只固定输入是不够的。

### A4. 稳定化配方（三条，各有实测）

1. **JSON 投影**（比对用，不改产物）：掩码"时间戳/主机/路径"类键与观测到的易变路径（本机实测掩码
   **9 条路径**）→ `sort_keys` 规范化序列化 → 比 sha256。实测 5 次运行归一为 1 个哈希。
2. **PDF 规范化**（比对用）：`/CreationDate`、`/ModDate`、`/ID` → 固定占位。实测 5 次运行归一为
   1 个哈希（本机 PDF 无 `/ModDate`、无 `/ID`）。
3. **环境配方**（不改脚本即可拿到原始字节一致）：`cd "$SKILL_DIR"` 固定 cwd +
   `SOURCE_DATE_EPOCH=1577836800`，两次运行参数逐字相同。实测：`identical_except_result_json = true`、
   `pdf_identical = true`，除 `result.json` 外全部产物原始字节一致（含 PDF）；`result.json` 残余差异
   **恰好 4 条时间戳路径**（`change_records[0..2].ts`、`provenance.ts`），投影后一致。

### A5. 本轴决策要点（遇情况先查表）

| # | 情形 | 决策 |
|-|-|-|
| A-D1 | 需要"可复现"的结论 | 先跑 `scripts/determinism.py --runs 5`；**不要**只凭"看起来一样"下结论（J1/J2/J3 三条都要过） |
| A-D2 | 产物原始字节不一致 | 先看 `volatile_fields`：只有时间戳 → 属**故意**；出现路径字段 → 检查 cwd 是否漂移；出现其它字段 → 当缺陷处理并写入 `uncertainty` |
| A-D3 | 报告要与他人对拍 | 用固定 cwd + `SOURCE_DATE_EPOCH` 配方重跑，并比对 A3 的 5 个稳定哈希（跨机对比注意库版本/字体差异，不要过度声称） |
| A-D4 | 只需 SVG（`--formats svg`） | 允许，但 `status` 会降为 `partial`（`F01_png`/`F01_pdf` 记为失败）；需要 `success` 就始终请求 `svg,png,pdf` |

### A6. 未覆盖声明（不要当成测过）

跨机器/跨平台的字节一致（本表只是同一台 Windows + 上述解释器/库版本）；字体替换引起的漂移；
并发运行（同输入并行写同一输出目录）；`--materials-dir` / `TASK_OUTPUT` 等其它入口的确定性；
平台评测容器的时钟与环境变量。全文见 `references/DETERMINISM.md §7`。

### A7. 本轴文件

- `scripts/determinism.py`——**本版新增入口**（只依赖标准库）。
- `references/DETERMINISM.md`——**本版轴文档**：判据 J1–J3、逐产物实测表、易变字段、三条稳定化配方、未覆盖声明。
- `determinism_report.json`——本机实跑的机器可读报告（`runs[] / per_file_sha256 / identical / volatile_fields[] / byte_diff / stabilization / verdict`）。
- `references/failure-modes.md` 的 **FM-D1–FM-D6**：字节漂移、cwd 泄漏、同秒侥幸、PDF 时间戳、PNG 时间块、跨机对比过度声称。

### A8. 复现本章全部数字

```bash
export SKILL_DIR=/path/to/challenge-83d4f050
python3 "$SKILL_DIR/scripts/determinism.py" --runs 5 \
    --work /tmp/det --report /tmp/determinism_report.json      # 退出码应为 0
python3 - <<'PY'
import json
d = json.load(open("/tmp/determinism_report.json", encoding="utf-8"))
print(d["identical"], d["stable_artifacts"], d["volatile_artifacts"])
print([f["json_path"] for f in d["volatile_fields"]])
print(d["stabilization"]["pdf_normalization"]["identical"],
      d["stabilization"]["env_recipe"]["pdf_identical"],
      d["stabilization"]["env_recipe"]["result_json_diff_paths"])
PY
```
