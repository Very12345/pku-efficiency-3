---
name: biological-mechanism-pathway-diagram
description: >-
  把科研机制/通路材料（文本、Markdown、表格或 PDF 中的通路描述）转成可逐条核验的
  生物机制图与通路图：从真实材料抽取实体与相互作用（激活/抑制/结合/修饰/转运），
  按区室约束布局（胞外—膜—胞质—核），生成带语义箭头的可编辑分层 SVG 源文件及
  PNG/PDF 预览，自动校验图例与数据编码一致性，并输出符合契约的 result.json。
  Use when the task asks to draw, generate, edit, re-export or validate a biological
  mechanism map, pathway diagram, signaling cascade, regulatory network or flow
  diagram (figures group of the biology mechanism & pathway challenge), including
  tasks that require editable sources with per-element provenance.
---

# biological-mechanism-pathway-diagram

研究流程图的科学性判断不看图画得是否复杂，而看三件事：每一个实体和每一条边能否回溯到
输入材料或权威命名；图例、颜色映射与图形本身是否自洽；别人能否打开可编辑源文件改一个
标签并重新导出。本 Skill 围绕这三件事设计。

## 1. 用途与适用条件

- 适用：生物机制图 / 通路图 / 信号级联 / 调控网络 / 流程图 / 图表编辑；同样适用于
  “把一段机制文字变成图”“修改他人图稿的一个错误箭头”“按数据给节点上色”“补图例”。
- 不适用：数值统计与统计分析结论、实验方案设计、论文写作与版式美化（这些由相邻课题负责）。
  本 Skill 只对图形中的科学内容表达、布局、可编辑性与导出质量负责。
- 运行前提：Python 3（标准库即可生成可编辑 SVG；matplotlib 可选，用于 PNG/PDF 预览，
  缺失时自动降级并如实记录）。

## 2. 输入与输出

**输入（平台运行时）**
- `/input/case.json`——固定字段：`case_id`（必填标识）、`title`、`task`、
  `materials`（材料文件路径列表）、`render`（画布尺寸，可选）、`output_contract`
  （契约字段，凡声明字段必须出现在 result.json 顶层，缺省按类型给 "" / [] / {}）。
- `/input/task.md`——任务说明（可能引用图号、材料范围、必需元素、导出格式）。
- `/input/**` 或材料目录——科研材料（正文/表格/PDF 等），**必须实际读取文件内容**，
  不得根据文件名猜测内容，不得用领域标签脑补数据。

**输出（平台运行时，写入 /app/output）**
- `result.json`——结构化结果，字段见 `references/OUTPUT_CONTRACT.md`（含
  case_id、status、deliverables、scientific_content、evidence_sources、uncertainty、
  change_records、export_checks、self_check 及 case.json output_contract 的全部字段）。
- `diagram.svg`——**可编辑源文件**：分层 `<g>`（layer-compartment / layer-edge /
  layer-entity / layer-label / layer-title / layer-legend / layer-meta），每个元素带
  `data-id / data-type / data-source` 属性，改一个标签即可重新导出。
- `diagram.png`、`diagram.pdf`——预览/矢量导出（同一布局引擎渲染，与 SVG 一致）。
- `model.json`——规范化的实体/边/图例模型（独立复核实体清单与边清单用）。

## 3. 执行步骤

> 全部脚本位于技能根目录的 `scripts/` 下；脚本通过 `os.path.dirname(__file__)` 自定位，
> 不依赖当前工作目录。命令示例均以技能根目录相对路径书写；平台容器中技能被安装为
> `/skills/weekly-skill`，等价路径为 `cd /skills/weekly-skill && python3 scripts/main.py ...`。

### 步骤 0：先读真实文件（禁止跳过）
用 `read` 读取 `/input/case.json` 与 `/input/task.md`，再用 `read`/`glob` 列出并读取
材料目录中的每个文件（正文、表格、PDF 文稿）。提取三样东西：
1. 任务要求（要画什么图、必须覆盖哪些元素、导出格式）；
2. 事实（实体、区室、相互作用、方向、数据数值）；**每个事实记录出处（文件+段落/行号）**；
3. 约束（色调、符号、模板风格、图号要求）。

### 步骤 1：生成草稿模型
```bash
python3 scripts/main.py --case /input/case.json --out /app/output --verbose
```
- 对结构化材料（表格、`A | 动词 | B` 行、`- A 激活 B（证据）`、数据映射声明），
  `scripts/extract.py` 会生成“草稿模型” `model.json`，每条实体/边带源文件与行号。
- 纯散文材料或 PDF 无法结构化时，`main.py` 会如实报告 `failed`——此时进入步骤 2 手工建模型。

### 步骤 2：核对草稿（Agent 必须逐条人工核验，不得直接交付草稿）
1. 打开 `/app/work/model.json`（草稿），逐条对照**实际读到的材料文本**：
   - 实体是否真实存在、名称书写是否正确（基因斜体/蛋白正体、物种前缀、复合物与家族成员）；
   - 相互作用类型是否判对（结合/激活/抑制/修饰/转运），方向是否与原文一致；
   - 证据强度（strong/moderate/weak）、uncertain 标记、区室归属是否正确；
   - 材料未提及但图画了的内容：source.kind 必须标 `assumption` 或 `common_knowledge`，
     并在 `uncertainty` 中说明原因。
2. 人工修正后把 `extraction.verified_by_agent` 置为 `true`，并在 `change_records` 中逐条
   记录“改了什么/为什么改”。
3. 重新验证：
```bash
python3 scripts/main.py --model-file /app/work/model.json --case /input/case.json --out /app/output
```

### 步骤 3：布局与渲染（脚本自动完成）
- `layout.py` 按区室带布局：胞外(0) → 细胞膜(1) → 细胞质(2) → 细胞核(3，嵌入胞质带内)；
  跨膜受体放在膜带内；反馈环/回流边在画布右侧绕行；同层水平相连。
- `svg_backend.py` 写可编辑分层 SVG；`mpl_backend.py` 用同一布局渲染 PNG/PDF 预览。

### 步骤 4：校验（脚本自动完成，仍须 agent 通读结果）
`scripts/validate.py` 检查：实体 id 唯一、边端点存在、每个实体/边都有来源、图例覆盖全部在用
类型、箭头语义与图例一致、节点与边颜色 ⊆ 图例∪数据映射（区室带/标题等装饰色不参与语义
校验）、通路方向（非反馈边必须上游→下游）、SVG well-formed、PNG/PDF 可打开、
result.json 契约字段齐全。任何 `fail` 会把 status 降为 partial/failed，必须处理。

### 步骤 5：写 result.json（脚本自动完成）
按 `references/OUTPUT_CONTRACT.md` 写出；`uncertainty`/`change_records` 如实记录：
- status 取值：`success`（所有阻断性检查通过）／`partial`（有 fail 或预览缺失但有 SVG）／
  `failed`（无法产出源文件或材料不可解析）。
- 来源：每条实体/边至少一条 source（材料路径、kind、行号）。
- 禁止编造：没有的软件状态、没有的数值、没有的评分一并如实说明。

### 步骤 6：自查清单（交付前逐条过）
- [ ] 我实际读取了 case.json / task.md / 全部材料，没有凭文件名猜内容；
- [ ] 实体、边、图例项与材料一一对应，每条都有 source；
- [ ] 基因/蛋白/复合物/小分子/区室没有混用，命名规范（见 DIAGRAM_SPEC.md）；
- [ ] 每个箭头语义 = 图例声明；虚线只在证据弱/不确定时出现；
- [ ] 数据映射（颜色/线宽/大小）与图例、图面三方一致；
- [ ] SVG 可编辑源已生成且 well-formed；PNG/PDF 预览（或明确记录缺失原因）；
- [ ] result.json 契约字段齐全；uncertainty / change_records 诚实；
- [ ] 命令与产物在 TEST.md 记录，任何失败都有说明。

## 4. 实体与命名规范（摘要，完整版见 references/DIAGRAM_SPEC.md）

| 类型 | 图形 | 书写 |
|---|---|---|
| 基因 gene | 矩形、无圆角 | 斜体（如 *MYC*），大写；物种前缀按权威命名 |
| 蛋白质 protein | 圆角矩形 | 正体（如 MYC 蛋白） |
| 复合物 complex | 圆角矩形+内描边 | 成分间用 "–"（如 PI3K–AKT 复合物） |
| RNA | 圆角矩形虚线边 | 正体 |
| 小分子/配体 | 圆形 | 正体（如 ATP、PIP3） |

同名基因与蛋白必须分开画（如 `MYC（基因）` 与 `MYC` 蛋白），并在 note 里注明依据；
同义名/旧名以材料或权威数据库为准，保留一个新名+同义名备注，不做无依据归一。

## 5. 相互作用语义（箭头类型=科学论断）

| 类型 | 箭头 | 颜色 | 语义 |
|---|---|---|---|
| activation 激活/促进 | 实心三角形 | 绿 #2E7D32 | 促进/激活 |
| inhibition 抑制/阻断 | 端点横杠 (T-bar) | 红 #C0392B | 抑制/阻断 |
| binding 结合/互作/募集 | 无箭头实线 | 蓝 #1F4E79 | 物理结合、募集 |
| modification 修饰 | 端点圆点，可带“P”标签 | 橙 #B9770E | 磷酸化/泛素化等 |
| transport 转运/转位 | 端点菱形 | 紫 #6C3483 | 转运、转位、内化 |

- 边宽 = 证据强度：strong 2.8 / moderate 2.2 / weak 1.6；
- **虚线只表达“证据弱/间接/不确定”**，与边类型无关（uncertain 或无强证据时使用）；
- 反馈环：`edge.feedback=true`，布局在右侧绕行，箭头回到上游节点。

## 6. 布局与图例规范

- 信号流向自上而下：胞外→膜→胞质→核；跨膜受体必须在膜带内；核内因子在核内框内。
- 图例必须覆盖图面上所有用到的实体类型与边类型；图例色/线宽与图面实际使用逐值一致
  （校验器 L01/L02/L05 强制）。
- 数据编码（若材料给数值）：实体填充色按映射字段插值（默认 表达量 低 #FFF7E0 → 高
  #1F4E79），图例画出色带与“低/高”标签；没有数值时用类型默认色并在图例注明。

## 7. 异常处理

| 异常 | 处置 | 记录位置 |
|---|---|---|
| 材料缺方向（不知上下游） | 只画无向边语义（结合类），标注 uncertain；不臆造方向 | uncertainty + 边 uncertain=true |
| 同名基因/蛋白歧义 | 分成两个实体并注明；无法区分时标 uncertain 并说明 | uncertainty |
| 输入数据与图示矛盾（如材料数值冲突） | 以材料原文为准，图与 result 都标注矛盾点 | uncertainty + change_records |
| 材料为 PDF 无法结构化解析 | Agent 用工具抽取文本 → 转成文本材料或手工建 model.json（--model-file） | extraction.method=manual |
| 字体/图元缺失 | SVG 用系统字体栈（查看端可替换）；PNG 缺中文字体时告警并写入 export_checks | preview warnings |
| 预览导出失败 | 保留 SVG 源文件，status=partial，reson 写明 matplotlib 是否可用 | deliverables/status |
| 图面元素过多不可读 | 减小默认字号/收缩节点宽度，或拆分子图并记录 | layout.warnings + uncertainty |
| 目标格式不支持 | 至少交付 SVG + PNG；其他格式如实说明不支持 | export_checks |
| 材料里没有实体/关系 | 明确 failed，不画空图凑数，给出补救路径 | status=failed |

## 8. 反预制答案规则（重要）

- `examples/` 目录中的一切（case、材料、输出）都是**演示示例，非正式案例**：图内与
  result.json 均带“示例”标记。正式运行**禁止**把 examples 的实体/边/数值抄入正式输出；
  平台案例的材料与示例材料不同，必须现场从真实材料推导。
- result.json 的来源/数值/评分一律按本次运行实际填写；平台记录模型与 trace，不自己
  编造 benchmark 分数。

## 9. 限制与维护

- SVG 为手写图层制式，供 SVG 生态（浏览器、Inkscape、draw.io 导入、脚本改属性）编辑；
  不做 Word/PPT 内嵌途径（如需可另用 office 类 Skill 二次嵌入）。
- 自动抽取器只处理结构化语句；散文材料依赖 Agent 人工抽取（步骤 2），这是刻意设计
  ——准确率优先于全自动。
- 颜色/形状/字体等风格常量集中在 `scripts/model.py`，改一处全图与图例同步。

## 10. 参考资料（技能内相对路径）

- `references/DIAGRAM_SPEC.md`——绘图规范（形状/箭头/区室/命名/导出参数）。
- `references/OUTPUT_CONTRACT.md`——result.json 字段契约（机器校验基准）。
- `references/RUBRIC_MAP.md`——五维评分 → 本包覆盖映射。
- `examples/`——最小可运行示例（输入+输出，均标注“示例，非正式案例”）。
- `README.md`、`TEST.md`——运行方法、依赖、限制与本机实测记录。