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
---

# biological-mechanism-pathway-diagram（合规文本包 · 图件运行时生成） · 整合版（决策层 + 增益层）

> 本包整合了基线 Skill 与 2 个强化层,各层对应不同的评分维度:可靠体验 10 + 实际效果 40 · 使用增益 25。
> 各层内容**不重复**:决策层给规则与失败分支;增益层给对照协议与指标口径;机制层给机制说明与可复用资产。
> 建议使用顺序:先用「决策层」跑通并处理异常,再用「增益层」证明并度量改善,最后用「机制层」复用与扩展。
> 各层的原始文件都完整保留在本包内,不是摘要 —— 下面每一层都是可以独立执行的完整规范。

## 本包文件索引

- `COMPARE.md`
- `GITHUB_URL.txt`
- `README.md`
- `TEST.md`
- `worklog.md`
- `assets/mechanism-spec.schema.json`
- `assets/palettes.json`
- `assets/result.template.json`
- `examples/EXPECTED-OUTPUT.md`
- `examples/README.md`
- `examples/case.json`
- `examples/model.example.json`
- `examples/task.md`
- `references/GAIN-PROTOCOL.md`
- `references/OUTPUT_CONTRACT.md`
- `references/RUBRIC_MAP.md`
- `references/failure-modes.md`
- `references/legend-encoding.md`
- `references/mechanism-spec.md`
- `scripts/baseline_emulator.py`
- `scripts/check_contract.py`
- `scripts/extract.py`
- `scripts/gain_probe.py`
- `scripts/layout.py`
- `scripts/legend_audit.py`
- `scripts/main.py`
- `scripts/model.py`
- `scripts/mpl_backend.py`
- `scripts/pathway_svg.py`
- `scripts/result_writer.py`
- `scripts/topology.py`
- `scripts/validate_figure.py`
- `templates/relation-checklist-template.md`
- `examples/materials/example_material.md`
- `examples/output/legend_audit.json`
- `examples/output/model.json`
- `examples/output/result.json`
- `examples/output/topology.json`

---

# 【决策层】决策规则与失败分支（目标维度:可靠体验 10 + 实际效果 40）

---
name: biological-mechanism-pathway-diagram
description: >-
  把机制/通路材料转成可逐条质疑的生物机制图与通路图：先落一份声明式机制规格，
  再按区室约束确定性布局，输出可编辑分层 SVG 源文件与 PNG/PDF 预览，并自动跑
  拓扑审计与图例/数据编码审计，最后写出契约化 result.json。
  本版的重点是**决策显性化**：22 条决策规则 D1–D23（触发信号 / 动作 / 失败时降级）
  与五类失败分支表一一对应，遇到边界情况按表处置而不是临场发挥。
  Use when the task asks to draw, generate, edit, re-export or validate a biological
  mechanism map, pathway diagram, signaling cascade, regulatory network or flow
  diagram (figures group of the biology mechanism & pathway challenge), including
  tasks that require editable sources with per-element provenance.
---

## biological-mechanism-pathway-diagram（决策显性化版 · 文本包 · 图件运行时生成）

机制图是**一份可以被逐条质疑的机制陈述**，不是装饰性插图。本 Skill 把"画对"拆成两件事：
**每一步都有明文决策规则**（§1 的 D1–D23），以及**每一种失败都有明文处置与记录位点**
（§2 的五类失败分支表）。脚本只负责执行与审计；**遇到边界情况时，Agent 查规则表，不临场发挥**。

判断一次运行是否合格，只看三条：每个实体和每条边能否回溯到材料原文或权威命名；
图例、颜色映射与图面是否自洽；别人能否打开可编辑源文件改掉一个标签并重新导出。

### 0. 本文档怎么读（三步）

1. **先读 §0–§2**：资源形态（什么能放进包）、规则表（怎么办）、失败分支表（出错了怎么办）。
2. **再读 §3**：CP1–CP5 流水线——每条 CP 后面括号里标注了相关的 D 规则编号。
3. **交付前读 §7 自查清单**：逐条打勾，任何一条打不上就不要报 `success`。

资源形态受运行时契约约束：`at most 50 UTF-8 text files, 500KB each and 2MB total,
no symlinks`。因此本包**只有文本**（`.md .py .json .txt .csv .yaml .yml` 七种扩展名）；
`diagram.svg` / `diagram.png` / `diagram.pdf` 一律由 `scripts/` 在 `--out` 目录**运行时生成**，
包里看不到图是设计而不是缺失。运行产物可以任意格式，技能资源必须全是文本。

### 1. 决策规则 D1–D23（触发信号 → 动作 → 失败时降级）

用法：**先找到触发信号所在的行，按"动作"执行；若动作也无法完成，走"失败时降级"这一列，
并把降级理由写进该行指定的记录位点。** 不要跳过记录位点——记录位点就是可核验性的落点。

#### 1.1 材料与实体判定（D1–D7）

| # | 触发信号 | 动作 | 失败时降级（记录位点） |
|---|---|---|---|
| D1 | 材料写了实体但**没写上下游方向** | 只画结合类无向语义边，`uncertain=true`，布局不给箭头方向暗示 | 连结合关系也无法判定 → **不画该边**，在 `uncertainty` 写明"材料未给出关系依据"（宁可少画，不可编） |
| D2 | 同名**基因与蛋白**同时出现 | 拆成两个实体：gene 用斜体大写名、protein 用正体名，`note` 写判定依据 | 无法区分 → 合并为一个实体并 `uncertain=true`，在 `uncertainty` 说明（P04） |
| D3 | **同一种分子出现在多个区室**（如胞质 ERK / 核内 ERK） | 按区室拆实体，各自 `note` 注明去向；跑 P04b 确认区室归属 | 区室无法判定 → 归 `other` 并置 `uncertain=true`（不猜膜内/膜外） |
| D4 | 材料数值与图面意图**矛盾** | 以材料原文为准；矛盾点同时写 `uncertainty` 与 `change_records` | 数值不可解释 → 该实体**禁止**用颜色编码，退回类型默认色并在图例注明"该值不参与映射"（E01/T03） |
| D5 | 材料是 **PDF/扫描件** | 先抽文本另存为 `.md` 材料，再走 CP2；或直接 CP2b 手工建规格，`extraction.method=manual` | 抽取与手工都不可行 → `status=failed`，`reason` 写明并给补救路径（换材料 / `--model-file`） |
| D6 | 材料**只有实体、没有关系** | 正常画实体与区室，`edges=[]`，图例只列实体；`status=partial` 并说明"边清单为空" | 实体也为空 → `failed`，**不画空图凑数** |
| D7 | `case.json` 的 materials 路径失效或目录为空 | 依次尝试：case 相对路径 → `--materials-dir <目录>` → case 同目录下的材料文件 | 三处都没有 → CP1.3 fail → `failed`（实测 exit 3，只写 `result.json`） |

#### 1.2 语义与拓扑判定（D8–D11）

| # | 触发信号 | 动作 | 失败时降级（记录位点） |
|---|---|---|---|
| D8 | 动词**不在五类语义枚举**内（"调控""影响""参与"） | 按材料字面就近判为 activation / inhibition，并在 `note` 写判据 | 判据不足 → 归 `binding` + `uncertain=true`（P 系列不阻断，但必须留痕） |
| D9 | 出现**逆流边**（下游 → 上游） | 反馈/回流：`feedback=true`，右侧绕行；非反馈：给出科学理由（转运/转位/修饰回落） | 无理由 → 改方向或删边；保留则必须在 `uncertainty` 说明（P03/P07） |
| D10 | **重复边**（同 from/to/type 出现多次） | 合并为一条，`source[]` 保留全部来源行 | 语义确实不同 → 保留两条，各写 `subtype` 区分（P05） |
| D11 | **自环**（A → A，如自磷酸化） | 允许，但必须写 `subtype` 并在 `note` 说明机制 | 无机制依据 → 删除该边（P06） |

#### 1.3 图例与数据编码（D12–D15）

| # | 触发信号 | 动作 | 失败时降级（记录位点） |
|---|---|---|---|
| D12 | 图面用了某类型，**图例没列** | 阻断：补图例项，重跑（L01/L02 是 fail） | 类型枚举拼错 → 修正 `type` 后重跑；不得"用了却不列" |
| D13 | 画布颜色**不在图例 ∪ 映射**内 | 阻断：改回图例色，或把该编码方式补进图例（L05） | 无法归属 → 该元素改用类型默认色并记 `uncertainty` |
| D14 | 数值**找不到来源行** | 阻断：补 `source`；或降为 `assumption` 并进 `uncertainty` | 降级后该值**不得**用于颜色/线宽编码（E01/T03） |
| D15 | 数值范围退化（全等值 / 只有一个值） | 关闭插值，用类型默认色，图例注明"本案例无梯度" | 材料声明了 0–1 归一化但样本退化 → 按声明域画色带，实体用默认色（`legend_audit` 记录） |

#### 1.4 资产与依赖缺失（D16–D18）

| # | 触发信号 | 动作 | 失败时降级（记录位点） |
|---|---|---|---|
| D16 | `import matplotlib` 失败 | 只交付可编辑 SVG，`status=partial`、exit 2、G5=false，原因写入 `export_checks` + `uncertainty` | **绝不**伪造 PNG/PDF；`deliverables.previews/exports` 保持空数组 |
| D17 | 系统缺中文字体 | SVG 用 CSS 字体栈（查看端决定字体，不受影响）；PNG 渲染告警并记录 `font` | 仍渲染出乱码 → 改为 ASCII 标签 + 图注中文，并把替换记录进 `change_records` |
| D18 | 包内资产缺失（`assets/palettes.json` / `assets/mechanism-spec.schema.json` / `templates/relation-checklist-template.md`） | 调色板 → 回退 `scripts/model.py` 内置默认并记 `uncertainty`；schema → S01 warn 不阻断；核对清单 → 用本文档 §7 清单代替 | **不得**因为少一个资产就静默改变图例/配色语义；三处缺失都要在当前运行的 `uncertainty` 留痕 |

#### 1.5 契约四形态与状态一致性（D19–D23）

| # | 触发信号 | 动作 | 失败时降级（记录位点） |
|---|---|---|---|
| D19 | `case.json` 的 `output_contract` 声明了字段 | 先判**形态**再填空：①标量→`""` ②列表→`[]` ③布尔→`false` ④数值/字典→`0`/`{}`；声明值是 `null` 时按 ① 处理 | 形态无法判定（值为对象数组）→ 按 ② 给 `[]` 并在 `uncertainty` 写明判据；**任何情况下顶层不得出现 `null`** |
| D20 | 契约回显失败（`check_contract.py` 非 0） | 按报出的缺项补齐：缺字段按 D19 四形态填空，多出 `null` 的字段改成对应空值 | 同一缺项连续两次修不好 → 停止重跑，在 `uncertainty` 写明缺哪个字段与原因，`status` 不得为 `success` |
| D21 | 走到 **exit 3 / status=failed** 之后仍要交付 | 注意实测：failed 路径只写**最小信封**（14 个顶层键），缺 `title / skill / data_mapping / extraction / export_checks / provenance` 六项 | 补写这六项（值按 D19 空值形态）后再自查；**不得**把 failed 谎报为 success，也不得用 result.json 冒充完整交付 |
| D22 | `status` / `gates` / **退出码**三者互相矛盾 | 以**退出码为真**重算：0 ⇔ success（且 gates 8/8、提取已核验、有预览）；2 ⇔ partial；3 ⇔ failed | 修不了矛盾 → 取更保守的一档（success→partial→failed），并在 `uncertainty` 写明"三元组不一致及取值理由" |
| D23 | 命令报"找不到文件"或 cwd 不是技能根 | 用自定位写法：`SKILL_DIR` 指向含 `SKILL.md` 的那一层，命令一律 `python3 "$SKILL_DIR/scripts/main.py" ...`；先跑 `--help` 自检 | 仍失败 → 用脚本内 `__file__` 自定位特性，改在技能根外任意 cwd 重试；把失败命令原文记入 `change_records` |

> 规则表的边界（诚实声明）：`--materials-dir` 在基线版会以
> `TypeError: path should be string... not list` 崩溃（实测 exit 1）；本包已修（见 `worklog.md` §4），
> 修复只做入参归一化，**不改 CLI 参数名与退出码语义**。

### 2. 失败分支总表（五类 · 与 `references/failure-modes.md` 的 F 编号一一对应）

| 类别 | 分支 | 触发信号 | 处置与降级 | 记录位点 | F 编号 | 关联规则 |
|---|---|---|---|---|---|---|
| **材料异常** | 材料缺失/目录为空 | CP1.3 fail | `failed`（exit 3），给补救路径 | `status/reason/uncertainty` | F01 | D7 |
| | PDF/扫描件不可结构化 | extract method=manual-required | 抽文本或手工建规格（CP2b） | `extraction.method` | F02 | D5 |
| | 方向缺失 | 边无法定向 | 无向语义 + `uncertain=true` | `uncertainty` | F03 | D1 |
| | 同名歧义 | P04 | 拆两个实体或合并 + `uncertain` | `note/uncertainty` | F04 | D2 |
| | 数值矛盾 | 人工核验 | 以原文为准，双处标注 | `uncertainty + change_records` | F05 | D4 |
| | 只有实体无关系 / 全空 | 边清单或实体清单为空 | `partial`（有实体）或 `failed`（全空） | `status/scientific_content.counts` | F06 | D6 |
| **资产缺失** | `palettes.json` 缺失 | 读资产失败 | 回退内置默认调色板 | `uncertainty` | F07 | D18 |
| | `mechanism-spec.schema.json` 缺失 | S01 warn | 用内置默认 schema，不阻断 | `self_check` | F08 | D18 |
| | 核对清单模板缺失 | 模板路径不存在 | 用 SKILL.md §7 清单代替 | `change_records` | F09 | D18 |
| **依赖缺失** | matplotlib 不可用 | import 异常 | 仅 SVG + `partial` + exit 2 | `export_checks/uncertainty` | F10 | D16 |
| | Pillow 缺失 | 尺寸校验降级 | PNG 交给 matplotlib 写，尺寸校验降为 warn | `self_check.warnings` | F11 | D16 |
| | 中文字体缺失 | 渲染告警 | SVG 不受影响；PNG 记录 font 与告警 | `export_checks` | F12 | D17 |
| **契约四形态** | ① 标量字段 | 声明值为 str | 无值填 `""` | `result.json` 顶层 | F13 | D19/D20 |
| | ② 列表字段 | 声明值为 list | 无值填 `[]` | 同上 | F14 | D19/D20 |
| | ③ 布尔字段 | 声明值为 bool | 无值填 `false` | 同上 | F15 | D19/D20 |
| | ④ 数值/字典字段 | 声明值为 number/dict | 无值填 `0` / `{}` | 同上 | F16 | D19/D20 |
| **状态不一致** | schema 门失败 | CP2 S01 fail | `failed`（exit 3），只写最小信封 | `status/reason` | F17 | D21 |
| | 契约回显失败 | `check_contract.py` 非 0 | 按缺项补齐后重跑 | `result.json` | F18 | D20 |
| | failed 路径信封不全 | 实测 14 键、缺 6 项 | 补写 6 项空值（见 D21） | `result.json` | F19 | D21 |
| | status/退出码矛盾 | 三者不一致 | 以退出码为真，取更保守档 | `uncertainty` | F20 | D22 |
| **可读性/导出** | 图面元素过多 | 布局溢出/字号过小 | 收缩节点或拆子图，记 `layout.warnings` | `layout.warnings` | F21 | — |
| | 目标导出格式不支持 | F01_xxx fail | 至少交付 SVG + PNG，其余如实说明 | `export_checks` | F22 | — |

**这张表是"可核验性"的骨架**：任何一次运行结束时，如果表里任一分支被触发，
它的"记录位点"里必须能找到对应内容；找不到就是漏记，属于交付缺陷。

### 3. 执行流水线 CP1–CP5（括号内为相关决策规则）

> 所有脚本通过 `os.path.dirname(__file__)` 自定位，**与 cwd 无关**。命令统一用 `$SKILL_DIR`
> （含 `SKILL.md` 的那一层）：平台容器 `export SKILL_DIR=/skills/weekly-skill`；本机指向包根。

#### CP1 读真实文件（D1–D7、D23）
用 `read` 读 `/input/case.json`、`/input/task.md`，再逐个读材料文件。产出三样东西：
**任务要求**、**事实（实体/区室/相互作用/方向/数值）**、**约束（色调/符号/图号/导出格式）**。
每个事实记出处（文件 + 行号）。材料缺失时 CP1.3 直接 fail——先按 D7 的三级查找补齐。

#### CP2 生成或提供机制规格（D5、D8、D17–D18）
```bash
python3 "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output --verbose
```
结构化材料（表格 / `A | 动词 | B` / `- A 动词 B（证据）`）由 `scripts/extract.py` 出草稿 `model.json`，
草稿先过 `assets/mechanism-spec.schema.json`（**对未归一化规格校验**，未知类型不会被静默改写）。
散文/PDF 材料走 CP2b：Agent 按 `references/mechanism-spec.md` §1 手写 `/app/work/model.json`，再
```bash
python3 "$SKILL_DIR/scripts/main.py" --model-file /app/work/model.json \
    --case /input/case.json --out /app/output
```

#### CP2b 手工建规格（D5）
手写规格时逐条对照材料：实体类型、区室、边类型、方向、证据强度、来源行号。
写完先自查 D8/D9/D10/D11 四条语义规则，再交给 CP3。

#### CP3 人工核验（本文档 §7 · 强制）
逐条核对草稿与材料原文；核对完成后把 `extraction.verified_by_agent` 置 `true`，
在 `change_records` 记"改了什么/为什么改"。用 `templates/relation-checklist-template.md`
（实体/边/图例/拓扑/导出五张表）作为核验载体——**这张表就是核验动作的执行证据**。
未核验的草稿**永远不能**报 `success`（见 D22）。

#### CP4 布局、渲染与双审计（D1、D3、D9、D12–D15）
- `scripts/layout.py` 按区室带确定性布局（胞外→膜→胞质→核；跨膜受体在膜带内；反馈环右侧绕行）；
- `scripts/pathway_svg.py` 写可编辑分层 SVG（7 个 `layer-*` 组 + `data-id/data-type/data-source`）；
- `scripts/mpl_backend.py` 渲染 PNG/PDF（缺失时按 D16 降级）；
- `scripts/topology.py` 拓扑审计 P01–P08；`scripts/legend_audit.py` 图例/编码审计 L01–L08、E01–E02；
- `scripts/validate_figure.py` 聚合 M/T/P/L/E/S/F/D 检查 + 契约后置检查 + 确定性探针。

#### CP5 写 result.json 并自查（D19–D22）
`status` 三值按 §2 表；交付前逐条过 §7 清单；然后跑两个独立复查命令：
```bash
python3 "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json --case <case.json>
python3 "$SKILL_DIR/scripts/validate_figure.py" --out <out>
```
两条都 exit 0 才允许写 `success`。

### 4. 输入输出速览

**输入**：`case.json`（`case_id/title/task/materials/render/output_contract`）、`task.md`、材料文件。
**输出**（`--out` 目录，全部运行时生成）：`result.json`（唯一评分产物）、`diagram.svg`（可编辑源，
7 层 + `data-*` 溯源）、`diagram.png`、`diagram.pdf`、`model.json`（机制规格）、
`topology.json`、`legend_audit.json`。字段契约与硬性门 G1–G8 见 `references/OUTPUT_CONTRACT.md`。

### 5. 实体与箭头语义速查

| 实体类型 | 图形 | 书写 | 箭头类型 | 端点 | 颜色 |
|---|---|---|---|---|---|
| gene | 矩形（直角） | *斜体*大写 | activation | 实心三角 | 绿 |
| protein | 圆角矩形 | 正体 | inhibition | 端点横杠 | 红 |
| complex | 圆角矩形 + 内描边 | 成分间 "–" | binding | 无端点 | 蓝 |
| rna | 圆角矩形（虚线边） | 正体 | modification | 圆点（可带 P） | 橙 |
| small_molecule | 圆形 | 正体 | transport | 菱形 | 紫 |

- 线宽编码证据强度：strong 2.8 / moderate 2.2 / weak 1.6；**虚线只表示证据弱或不确定**，与类型无关。
- 颜色与线宽集中在 `assets/palettes.json`（缺省回退 `scripts/model.py` 内置值，见 D18）。
- 命名/区室/导出的完整规范见 `references/mechanism-spec.md` 与 `references/legend-encoding.md`。

### 6. 布局与图例硬约束

- 流向自上而下：胞外 → 膜 → 胞质 → 核；跨膜受体必须在膜带内；核内因子在核框内（D3、P04b）。
- 图例必须覆盖图面在用的**全部**实体类型与边类型，色值与线宽与图面**逐值一致**（D12/D13）。
- 有数值时按映射画色带并标"低/高"；无数值时用类型默认色并在图例注明（D15）。

### 7. 交付前自查清单（逐条打勾，任一条打不上就不报 success）

- [ ] 我实际读了 `case.json` / `task.md` / 全部材料，没有按文件名猜内容（D7、D23）；
- [ ] 实体、边、图例项与材料一一对应，每条都有 `source`（文件:行）（D14）；
- [ ] 基因/蛋白/复合物/RNA/小分子没有混用，命名符合规范（D2、D3）；
- [ ] 每个箭头语义 = 图例声明；虚线只出现在弱证据/不确定处（D8、D12）；
- [ ] 数据映射（颜色/线宽/大小）与图例、图面三方一致，数值可溯源（D13、D14、D15）；
- [ ] 可编辑分层 SVG 已生成、7 层齐全且 well-formed；PNG/PDF 或明确记录原因（D16、D17）；
- [ ] `result.json` 契约字段齐全（含 `output_contract` 全部字段，按 D19 四形态），**顶层无 null**；
- [ ] `topology.json` / `legend_audit.json` 已产出；`uncertainty` / `change_records` 诚实（§2 表）；
- [ ] `status` 与 exit code、gates 三元组一致（D22）；failed 路径按 D21 补齐信封；
- [ ] 命令与产物记入 `TEST.md`；任何跳过或降级都有对应记录位点。

### 8. 反预制答案规则

`examples/` 里的一切都是**演示示例（非正式案例）**：图内与 `result.json` 均带示例标记。
正式运行**禁止**把示例的实体、边或数值抄进正式输出；平台案例的材料与示例不同，
必须现场从真实材料推导（D1–D7 都是为这件事服务的）。`assets/result.template.json` 只是结构模板，
不得冒充运行产物；不给自己编造任何评分数字。

### 9. 限制与维护

- SVG 为手写图层制式，供 SVG 生态（浏览器、Inkscape、draw.io 导入、脚本改属性）编辑；
  不做 Word/PPT 内嵌（需要时另用 office 类 Skill 二次嵌入）。
- 自动抽取只处理结构化语句；散文/PDF 走 CP2b 人工抽取，这是"准确率优先于全自动"的刻意设计。
- 图件不在包内，每次运行现场生成；PDF 与 `result.json` 含时间戳，**不作确定性承诺**
  （确定性承诺 = SVG/PNG/model/topology/legend_audit，见 `TEST.md`）。
- 改动流程：改色 → `assets/palettes.json`；改契约/门 → `references/OUTPUT_CONTRACT.md` +
  `scripts/check_contract.py` + `scripts/result_writer.py` 三处同步；改校验规则 → `topology.py` /
  `legend_audit.py` / `validate_figure.py` 并更新 `references/mechanism-spec.md`。
  改完跑 `TEST.md` 全套，再在 `worklog.md` 追加一条带时间的记录。
- **明令禁止**：向包内添加二进制资源或 `__pycache__`（图件必须运行时生成）。

### 10. 文件索引（相对 `$SKILL_DIR`）

| 文件 | 作用 |
|---|---|
| `references/OUTPUT_CONTRACT.md` | 字段契约 + 四形态回显 + G1–G8 硬性门 + **§10 状态一致性矩阵** |
| `references/failure-modes.md` | 失败模式表（F01–F22，与本文档 §2 一一对应） |
| `references/RUBRIC_MAP.md` | 五维评分（40/25/15/10/10）逐条落点 |
| `references/mechanism-spec.md` | 机制规格结构、命名与区室规范、校验一览 |
| `references/legend-encoding.md` | 箭头语义、数据编码、调色板与审计规则 |
| `assets/mechanism-spec.schema.json` | CP2 的 schema 门（对 raw 规格校验） |
| `assets/palettes.json` | 调色板与 glyph 语义（单点改色） |
| `assets/result.template.json` | `result.json` 结构模板（示例） |
| `templates/relation-checklist-template.md` | CP3 人工核验载体（五张表） |
| `scripts/main.py` | 单一入口（CP1–CP5、退出码 0/2/3） |
| `scripts/{extract,model,layout,pathway_svg,mpl_backend,topology,legend_audit,validate_figure,check_contract,result_writer}.py` | 抽取 / 规格 / 布局 / 渲染 / 审计 / 契约 / 写盘 |
| `examples/` | 最小可运行示例（输入 + `EXPECTED-OUTPUT.md` + 实跑 JSON 产物） |
| `README.md` / `TEST.md` / `COMPARE.md` / `worklog.md` | 依赖与用法 / 自测与实测 / 对照方案 / 构建与修复记录 |

---

# 【增益层】公平对照协议与可测指标（目标维度:使用增益 25）

---
name: biological-mechanism-pathway-diagram
description: >-
  把机制/通路材料转成可逐条核验的生物机制图与通路图，并让"它比基础 Agent 好在哪"
  变成可测的量：结构化机制规格 → 区室约束布局 → 可编辑分层 SVG 源 + PNG/PDF 预览 →
  拓扑与图例/数据编码审计 → 契约化 result.json；每一步都留下可被第三方独立测量的产物。
  附带与"不加载 Skill 的基础 Agent"的公平对照协议（同输入 / 同工具 / 同预算）、
  8 项结构指标的独立度量器，以及本机实跑的对照记录。
  Use when the task asks to draw, generate, edit, re-export or validate a biological
  mechanism map, pathway diagram, signaling cascade, regulatory network or flow
  diagram (figures group of the biology mechanism & pathway challenge), including
  tasks that require editable sources with per-element provenance.
---

## biological-mechanism-pathway-diagram（增益可验证版 · 文本包 · 图件运行时生成）

本包的第一原则：**"更好"必须能被量出来。** 因此流程里每一个环节都产出一份可被外部脚本读取的
证据（分层结构、溯源属性、语义标签、图例声明、契约信封、审计产物），而"增益"由
`scripts/gain_probe.py` 用同一把尺子同时量两个条件：**基础形态**与**加载本 Skill**。

> 包内**只有文本资源**（`.md .py .json .txt .csv .yaml .yml`）：契约要求
> `at most 50 UTF-8 text files, 500KB each and 2MB total, no symlinks`。
> `diagram.svg` / `diagram.png` / `diagram.pdf` 一律由 `scripts/` 在 `--out` 目录**运行时生成**。

### 0. 增益主张（每条都给出度量方式与阈值）

| # | 主张 | 度量 | 判定命令 | 期望 |
|---|---|---|---|---|
| G1 | 产物是**可编辑分层源**，不是一张扁平图 | 具名图层组数 `layer_groups` | `gain_probe.py --dir <out>` | ≥ 7 |
| G2 | 每个实体/边都带**机器可读溯源** | SVG 中 `data-source=` 计数 | 同上 | ≥ 边数 |
| G3 | 边语义**机器可判**（不是靠看图猜） | 带 `data-type` 的边 / 总边数 | 同上 | 1.0000 |
| G4 | 图例**声明了**图面上在用的每种箭头 | 图例声明覆盖的边 / 总边数 | 同上 | 1.0000 |
| G5 | 结果是**契约化**的，可被独立复查 | 信封键覆盖 / 19 | `check_contract.py` exit 0 | 19/19 |
| G6 | 关键判据**留了审计产物** | `topology.json` + `legend_audit.json` | `gain_probe.py` | 2/2 |
| G7 | 交付件不止一张图 | PNG + PDF 存在性 | `gain_probe.py` | 2/2 |
| G8 | 同输入**可复现** | 双跑 sha256 | `TEST.md` §7 | 5/6 逐字节一致 |

**这些主张不是设计意图，而是能被第三方复算的数字**；本机实测值见 §7 与
`references/GAIN-PROTOCOL.md` §4。

### 1. 三类可测指标（定义写在协议里，命令可复制）

| 类别 | 指标 | 怎么量 | 量在哪 |
|---|---|---|---|
| 质量（结构性正确性） | 语义标签覆盖率、图例声明覆盖率、溯源属性覆盖率、图层完整度 | `scripts/gain_probe.py --dir <out>` | `references/GAIN-PROTOCOL.md` §2.1–2.3 |
| 契约一致性 | 信封键覆盖、顶层 null 数、`output_contract` 回显、G1–G8 门 | `scripts/check_contract.py` + `--json` 输出 | 同上 §2.4 |
| 效率 | 从材料到 7 件产物的耗时；改一个标签的代价（文件编辑数 / 重跑次数 / 重导出件数） | 计时 + 产物 sha 对比 | 同上 §2.5、§4.2 |

度量器 `scripts/gain_probe.py` 刻意**不 import 本包任何模块**（否则就是"用被测者自己的尺子
量被测者"），只读产物目录；缺项计 0，避免"没产物反而好看"。

### 2. 运行流程（每一步都留下可测产物）

```bash
export SKILL_DIR=/skills/weekly-skill        # 平台容器；本机指向含 SKILL.md 的那一层
python3 "$SKILL_DIR/scripts/main.py" --help  # 自检：路径正确即打印参数帮助
```

| 阶段 | 做什么 | 落下的可测产物 | 相关决策 |
|---|---|---|---|
| CP1 读真实文件 | 读 `case.json`、`task.md`、材料文件；事实逐条记出处 | `change_records` 首条（case/材料/任务长度） | P1、P6 |
| CP2 机制规格 | 结构化材料出草稿；散文/PDF 手工建规格；**raw 规格先过 schema 门** | `model.json`（实体/边/来源/图例） | P2 |
| CP3 人工核验 | 逐条对照材料；`verified_by_agent=true`；记改动 | `change_records`、核对清单 | P7 |
| CP4 布局 + 渲染 + 双审计 | 确定性布局 → 分层 SVG → PNG/PDF → 拓扑审计 + 图例/编码审计 | `diagram.svg`（7 层 + `data-*`）、`topology.json`、`legend_audit.json` | P3、P4、P8 |
| CP5 契约与终态 | 写 `result.json`，判定 `status`/退出码/门的自洽 | `result.json`（信封 19 键 + 契约回显） | P5、P9 |

主命令（已核验规格路径）：

```bash
python3 "$SKILL_DIR/scripts/main.py" \
    --case "$SKILL_DIR/examples/case.json" \
    --model-file "$SKILL_DIR/examples/model.example.json" --out /app/output
```

散文/PDF 材料走手工规格（`extraction.method=manual`）：

```bash
python3 "$SKILL_DIR/scripts/main.py" --model-file /app/work/model.json \
    --case /input/case.json --out /app/output
```

**退出码即测量口径**：`0 = success（gates 8/8）`、`2 = partial（有降级但有产物）`、
`3 = failed（阻断）`。三者与 `status`、`gates` 必须自洽（规则 P9）。

### 3. 影响可测指标的决策点（P1–P10）

只列**会改变上面任何一项度量**的决策；纯粹的执行细节不在这里重复。

| # | 触发信号 | 动作 | 失败时降级 |
|---|---|---|---|
| P1 | 材料路径解析不到（case 相对路径失败） | 用 `--materials-dir <目录>` 显式给材料目录（多目录可重复给） | 仍无材料 → `failed`（exit 3），`uncertainty` 给补救路径 |
| P2 | 草稿规格里出现枚举外的 `type`/`edge.type` | **阻断渲染**：按 schema 违规清单改正后重跑（raw 规格校验，不会被静默改写成 other） | 改不动 → `failed`，把违规项原文写进 `reason` |
| P3 | 图面用了某类型但图例没列 | 阻断：补图例项 → 重跑（这条直接决定 G4） | 类型名拼错 → 先修 `type` 再重跑 |
| P4 | 画布颜色不在图例 ∪ 映射内 | 阻断：改回图例色或扩图例 | 无法归属 → 改类型默认色 + 记 `uncertainty` |
| P5 | 契约字段无值 | 先判形态再填空：标量 `""` / 列表 `[]` / 布尔 `false` / 数值·字典 `0`·`{}`；**顶层禁 null** | 形态判不定 → 按列表给 `[]` 并说明理由 |
| P6 | 材料没写上下游方向 | 只画结合类无向语义边（`uncertain=true`），不臆造方向 | 连结合依据都没有 → 不画该边，写 `uncertainty` |
| P7 | 自动草稿未被人工核验 | `status=partial`（exit 2）+ `uncertainty` 提示逐条复核；**不得**报 success | 无法核验（材料不可读）→ `failed` |
| P8 | matplotlib / 中文字体缺失 | 只交付 SVG：`partial` + exit 2 + `gates.g5_png=false`，`previews/exports=[]`，原因入 `export_checks` | **绝不**伪造预览；SVG 不得因此缺层或缺 `data-*` |
| P9 | `status` / 退出码 / `gates` 不一致 | 以退出码为真重算，取更保守档，写 `uncertainty` | 修不好就停在保守档，不谎报 success |
| P10 | `--formats` 只请求了部分格式 | 未请求的格式不算失败：`partial` + 空数组 + 说明；已请求的格式必须真产出 | 请求了但产出失败 → 按 P8 降级并记录 |

### 4. 契约与硬性门（可测判定）

- 唯一评分产物是 `result.json`：信封 19 键（`case_id/title/status/contract_version/skill/
  deliverables/scientific_content/evidence_sources/data_mapping/extraction/export_checks/
  topology/legend_audit/self_check/gates/uncertainty/change_records/files/provenance`）
  ＋ `case.json` 里 `output_contract` 声明的全部字段（按四形态回显，**无 null**）。
- 硬性门 G1–G8：`case_id` 非空、契约回显、`status` 三值、SVG 7 层良构、PNG 可开、
  图例覆盖在用类型、实体/边带 `source`、两个审计产物存在。任一门 error → 不得 `success`。
- 字段定义与判定细则见 `references/OUTPUT_CONTRACT.md`；机器入口：
  ```bash
  python3 "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json --case <case.json>
  python3 "$SKILL_DIR/scripts/validate_figure.py" --out <out>
  ```

### 5. 语义与编码速查（机器判定的对象）

| 实体类型 | 图形 | 书写 | 边类型 | 端点 | 颜色 |
|---|---|---|---|---|---|
| gene | 直角矩形 | *斜体*大写 | activation | 实心三角 | 绿 |
| protein | 圆角矩形 | 正体 | inhibition | 横杠 | 红 |
| complex | 圆角矩形+内描边 | 成分间 "–" | binding | 无端点 | 蓝 |
| rna | 圆角矩形（虚线边） | 正体 | modification | 圆点（可带 P） | 橙 |
| small_molecule | 圆形 | 正体 | transport | 菱形 | 紫 |

- 证据强度 → 线宽（strong 2.8 / moderate 2.2 / weak 1.6）；**虚线只表示弱证据或不确定**。
- 数据编码：有数值时按映射画色带并标"低/高"；无值用类型默认色并在图例注明。
- 这些不是画法偏好，而是**审计器读取的字段**（`data-type` / `data-evidence` / 图例声明），
  G3、G4 两项指标直接由它们决定。

### 6. 降级与失败（每条都改变某个度量，必须留痕）

| 情形 | 终态 | 度量上的表现 | 记录位点 |
|---|---|---|---|
| 草稿未核验 | `partial` / exit 2 | 契约与结构指标可满，但 `extraction.verified_by_agent=false` | `uncertainty`、`extraction` |
| 只交付 SVG | `partial` / exit 2 | G7 降为 1/2，`gates.g5_png=false` | `deliverables`、`export_checks` |
| schema 门不过 | `failed` / exit 3 | 只写最小信封（实测 14 键、信封 13/19） | `status`、`reason` |
| 材料不可解析 | `failed` / exit 3 | 无产物，`reason=manual-required` | `reason`、`uncertainty` |
| 审计发现 fail | `partial` 或 `failed` | G4/G5 掉分，`self_check.failures` 非空 | `self_check`、对应审计产物 |

完整分支（F01–F22，含资产缺失、字体缺失、导出失败、元素过多）见 `references/failure-modes.md`。

### 7. 本机对照实测摘要（2026-11-22，全部真跑）

**条件 A** = `scripts/baseline_emulator.py`（把题面点名的基础 Agent 失败签名做成确定性复现器：
名词平铺成环、统一灰箭头、无图例、无溯源、无契约、单一扁平层）；
**条件 B** = 本 Skill 的主路径。两侧读**同一份材料**、用**同一个度量器**。

| 指标 | 条件 A（基础形态） | 条件 B（加载 Skill） | 差 |
|---|---|---|---|
| 产物文件数 | 2（`figure.svg` + `notes.md`） | 7（SVG/PNG/PDF/result/model/topology/legend_audit） | +5 |
| 具名图层组 | 0 | 7 | +7 |
| 边的**语义标签**数 | 0 | 5（5 类语义全在用） | +5 |
| 图例声明的边 / 总边数 | 0 / 10 | 9 / 9 | — |
| 带 `data-source` 的元素 | 0 | 18 | +18 |
| 契约信封键覆盖 | 0/19（无 `result.json`） | 19/19 | +19 |
| `check_contract.py` | exit 1（`missing result.json`） | exit 0（7 项全 pass） | — |
| `validate_figure.py` | exit 1（`ok=False`） | exit 0（30 项、fails=0） | — |
| 材料实体名覆盖率 | 1.0000 | 1.0000 | **0（不是差异点）** |

**效率侧（同一天实测）**：条件 B 全新一次运行 2.51 s 产出 7 件；
**改一个标签** = 1 次文件编辑 + 1 次重跑（1.76 s），SVG/PNG/PDF 全部重新生成、标签出现在 SVG 里；
条件 A 的产物**没有元素 id 也没有 `data-*`**（`data-id` 计数 = 0），标签只能靠文本搜索定位，
且没有导出流水线——"改规格再重导出"这条路径在基础形态里不存在。

复算命令（任何人都能跑）：

```bash
python3 "$SKILL_DIR/scripts/baseline_emulator.py" --material <材料> --out /tmp/condA
python3 "$SKILL_DIR/scripts/main.py" --case <case.json> --model-file <model.json> --out /tmp/condB
python3 "$SKILL_DIR/scripts/gain_probe.py" --compare /tmp/condA /tmp/condB --material <材料>
```

完整协议、指标定义与逐条记录见 **`references/GAIN-PROTOCOL.md`**。

### 8. 反预制答案规则

`examples/` 全部是**演示示例（非正式案例）**；正式运行禁止抄示例的实体/边/数值。
`scripts/baseline_emulator.py` 是**对照用的反例生成器**：它的产物是刻意的坏例子，
**不得**作为正式案例输出、不得冒充平台对照结果。本包不写、也不预测任何平台评分。

### 9. 边界与诚实声明

- 度量器量的是**结构性与可核验性**（分层、溯源、语义标签、图例声明、契约、导出），
  **不评判图面美观**；美观度由人/模型评审判定。
- 条件 A 是**结构复现器**，不是平台基础 Agent 的真实运行；真实对照由平台执行（同输入、同预算、
  每条件 3 次重复）。本包只保证"判据可复算"。
- 确定性承诺 = SVG / PNG / model / topology / legend_audit；PDF 与 `result.json` 含时间戳。
- 图件不在包内（运行时生成）；PDF 与 `result.json` 含时间戳，不作确定性承诺。

### 10. 文件索引（相对 `$SKILL_DIR`）

| 文件 | 作用 |
|---|---|
| `references/GAIN-PROTOCOL.md` | **本版核心新增**：公平对照协议、8 项指标定义、复算命令、实测记录、局限 |
| `references/OUTPUT_CONTRACT.md` | 字段契约 + 四形态 + G1–G8 + §10 契约合规的可测判定 |
| `references/failure-modes.md` | F01–F22 失败分支（每条注明它在哪个度量上留痕） |
| `references/RUBRIC_MAP.md` | 五维评分落点（使用增益 25 分按指标逐条落点） |
| `references/mechanism-spec.md` / `legend-encoding.md` | 规格与绘图规范、箭头语义与数据编码 |
| `scripts/gain_probe.py` | 独立度量器（不依赖本包模块；`--dir` / `--compare`） |
| `scripts/baseline_emulator.py` | 条件 A 结构复现器（反例生成器，仅供对照） |
| `scripts/main.py` | 单一入口（CP1–CP5，退出码 0/2/3） |
| `assets/` `templates/` `examples/` | schema/调色板/结果模板、核对清单、最小可运行示例 |
| `README.md` / `TEST.md` / `worklog.md` | 依赖与用法 / 自测与实测记录 / 构建记录（`COMPARE.md` 已并入 GAIN-PROTOCOL） |
