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

# 科研数据图表生成与编辑（scientific-figure-craft）v2

面向「玻尔产品周赛 · 北大专区 · 学术效率 · 第三期」 challenge-1bd90d8a（figures 组）。

v2 相对 v1 的实质强化：**执行决策显性化** —— ① 六个检查点（CP1–CP6）把
「读源数据 → 出图 → 调样式 → 校验标注 → 交付可编辑文件」拆成可判定门；
② 十八个决策规则（D1–D18）覆盖材料异常/契约四形态/状态一致性/失败分支；
③ 图元↔源数据双向映射由 `mapcheck.py` 机器核对（不再靠人工抽查）；
④ 校验由 `figcheck.py` 以 G1–G8 硬门收口，status 与产物严格自洽。

**执行顺序（先读契约，再抽取，后生成，最后自评）**：
**① 读 `references/output-contract.md`（交付什么、G1–G8 硬门）→
② CP1 盘点材料 → ③ CP2 抽取（extract.json）→ ④ CP3 `spec_lint` 生成门 →
⑤ CP4 `main.py` 生成 SVG/PNG/PDF → ⑥ CP5 双校验（`mapcheck` + `figcheck` + 确定性）→
⑦ CP6 契约落地 → ⑧ 按 `references/rubric-map.md` 逐条自评五维覆盖。**

---

## 1. 用途与适用条件

- **适用**：平台固定 3 个案例（数据图表生成 / 样式调整 / 标注校验 / 源数据关联 /
  可编辑源文件与导出）。也可用于任何「数据表或生物源材料 → 可编辑科研图」请求。
- **不适用/边界**：不负责统计方法选择与显著性计算本身（显著性标注只转述源数据
  给出的 p 值，D6）；不负责实验设计；不替用户下科学结论。文字转述不能替代
  真实运行证据。
- **运行环境**：Python 3.8+ 标准库 + Pillow（渲染 PNG/PDF）。matplotlib/cairosvg/
  svgwrite 均非必需。无网络依赖。

## 2. 输入与输出

### 输入（平台运行期）
- `/input/case.json` —— 案例说明（case_id、figure 规格、data 引用、output_contract 等）。
- `/input/task.md` —— 任务说明。
- 材料：源数据表（CSV/TSV/JSON）；含生物源文献时用于 figure03 类网络/机制图
  （entities_file JSON / material 文本）。
- 本 Skill 安装在 `/skills/weekly-skill`（自包含；脚本用 `os.path.dirname(__file__)`
  自定位，不依赖当前工作目录）。

### case.json 的组织形态（脚本兼容）
顶层对象（或 `{"cases":[...]}` / 数组取第一项），可含：
- `case_id`/`id`：案例标识（result.json 必须回显）。
- `title`、`dataset_version`：元信息。
- `task_file`：task.md 路径（缺省自动找同目录 task.md）。
- `data`/`data_files`/`sources`：源数据（也可放案例同目录由脚本自动发现）。
- `figures`（或 `figure`/`figure_spec`）：一个或多个图规格，结构见
  `templates/figure_map.schema.json`（id/type/title/width/height/style/filter/
  x/y/hue/error{column,semantics}/annotations/entities/relations/panels/…）。
- `output_contract`：result.json 必须包含的字段（四种形态均可：list /
  {name:type} / {fields:[...]} / {fields:{name:type}}）。
- `manual_confirmations`：人工确认记录（原样带入 result）。

### 输出（/app/output，一律 UTF-8）
- `figure-<id>.svg` —— 可编辑分层矢量源（`<g id="layer-*">` 分层：坐标轴/数据/文字/
  图例/标注；`<metadata id='provenance'>` 溯源块；每个数据图元带 `data-*` 属性；
  **文字始终是真实 `<text>`，永不转曲**，G5 机器检查）。
- `figure-<id>.png` / `figure-<id>.pdf` —— 同一图元场景的预览（逐元素一致）。
- `data_manifest.json` —— 图元 ↔ 源数据映射（文件/列/行/值；svg_id 对齐）。
- `validation.json` —— 标注校验清单（八类检查）。
- `mapcheck_report.json` / `figcheck_report.json` —— CP5 双校验报告（含 G1–G8）。
- `result.json` —— 结构化结果：output_contract 全部字段（四形态，禁止 null）+
  `case_id` + `status`/`sources`/`uncertainty`/`change_records`/`checkpoints`/
  `gates`/`artifacts_sha256` 等，如实记录。
- `/app/work/`（--work）——中间产物：`extract.json`、`spec_lint.json`。

## 3. 执行步骤（S0–S6，含检查点 CP1–CP6）

### S0 定位与读契约
1. 读取 `references/output-contract.md`（G1–G8 与字段/类型）与
   `references/audit-rules.md`（检查标准）。
2. 读取 `/input/case.json` → 记录 `case_id`、figure 列表、output_contract 形态。
3. 读取 `/input/task.md` → 提炼：要几张图、图型、目标样式/期刊、数据来源、
   图面约束（轴单位、误差线语义、显著性、样本量、图例要求）。
4. 定位 `$SKILL_DIR`（本文件所在目录）；所有命令用绝对路径/脚本自定位。

### S1 **CP1 材料盘点**（先看文件，再谈内容）
1. 列出案例材料（同目录表格/文献文件），对每个源文件先算 sha256 并记录版本
   （`dataset_version`），确认存在性与行数。
2. **禁止**：不读文件就按文件名/标签猜内容；把材料摘要当源数据用；编造列。
3. 检查点 CP1：`case_id` 已取、task.md 已找到或已记 uncertainty、数据文件已发现
   （一个都没有 → status 不得 completed）。

### S2 **CP2 抽取实体-关系-数据**（extract.py，写 /app/work/extract.json）
```bash
python $SKILL_DIR/scripts/extract.py --case /input/case.json --out /app/work
```
- 数值图：逐列画像 {列名, 语义(x/y/误差/样本量/分类), 单位（从列名括号提取）,
  取值范围, 空值位置}（字段映射见 `references/workorder-field-map.md`）。
- 机制/通路图（figure03 生物源材料）：从 entities_file(JSON) 直接装载；
  材料文本支持显式行语法 `ENTITY: <id> | <label> | <group> | <cite>` 与
  `REL: <from> -> <to> | <label> | <type>`；其余段落按 `templates/entity_glossary.json`
  词表扫描，命中项标 `uncertain=true` —— **Agent 对照源材料原文确认后才可上图**。
- 检查点 CP2：数值列语义无歧义；每个实体/关系有来源（cite/文件）；不确定候选
  已显式记录。

### S3 **CP3 figure spec lint**（生成门）
```bash
python $SKILL_DIR/scripts/spec_lint.py --spec /input/case.json --case /input/case.json
# {"valid": true} 才可进入生成；有 error 按 D4 决策后记录并修复
```
- 检查点 CP3：图型合法、列存在、误差语义常规、显著性有锚点+来源、网络边不悬空。
- lint 结果写进 result.json 的 `spec_lint` 与 checkpoints.cp3_spec_lint。

### S4 **CP4 生成可编辑源与渲染**（核心，必须真实运行）
```bash
python $SKILL_DIR/scripts/main.py --case /input/case.json --out /app/output \
      --work /app/work [--task /input/task.md] [--style nature]
```
- 脚本自定位；以 /app/work 为中间产物目录；最终产物写 /app/output。
- 多张图按 `figures[]` 依次处理，单图失败不阻塞其他图（status=partial）。
- 检查点 CP4：每张图 SVG+PNG+PDF 齐全；SVG 分层、含溯源；PNG/PDF 可打开。

### S5 **CP5 双校验**（main.py 内自动执行，也可单独复核）
```bash
python $SKILL_DIR/scripts/mapcheck.py  --dir /app/output --case /app/input/case.json
python $SKILL_DIR/scripts/figcheck.py  --dir /app/output --case /app/input/case.json
python $SKILL_DIR/scripts/verify_rerun.py --case /app/input/case.json --out /app/output
```
- **mapcheck（数据↔图元双向）**：manifest 元素必须在 SVG 存在；SVG 数据层图元必须
  在 manifest 登记；`column+row_index+value` 三元组重读源文件逐行核对（容差 1e-9）。
- **figcheck（G1–G8）**：契约 → 文件 → SVG 可编辑性（分层/溯源/未转曲/无 XXE）→
  预览 → 六项标注校验无 fail → status 自洽。
- **verify_rerun（确定性）**：同输入重跑，SVG/PNG/manifest/validation 字节级稳定
  （result.json 仅时间戳不同，做归一化对比）。
- 检查点 CP5：G1–G8 全过、mapcheck 0 mismatch、确定性通过或如实记录差异。
  任何 `fail` → 修复后重跑；`warn` → 判断处置并写入 uncertainty。

### S6 **CP6 契约落地与自查**
1. result.json 顶层必须含 output_contract 全部字段（四形态任一；缺失按声明容器
   类型给 `""`/`[]`/`{}`/`false`/`0`，**绝不写 null**）。
2. `status` 与产物事实严格一致（G8）：有 fail/缺口 → 不得 completed。
3. 视觉终检：用浏览器打开 SVG / 查看 PNG（坐标、单位、图例、显著性星号、实体名拼写）。
4. 检查点 CP6：`output_contract_applied`、`gates.all_pass`、artifacts_sha256 已记录。

### S7 自查清单（提交前逐项过）
- [ ] 每张图：图上有数据的图元 100% 能回到源数据（mapcheck 0 mismatch）。
- [ ] 轴标签带单位（源数据带单位时）；刻度范围覆盖数据并留白。
- [ ] 图例 ↔ 系列一一对应（legend-mapping）。
- [ ] 显著性星号与 p 值/来源一致（转述，不自行计算）。
- [ ] 科学实体名与源材料原文一致，未"修正"拼写；不确定项已标记。
- [ ] SVG 分层可编辑、含 metadata 溯源、真实 `<text>` 未转曲；PNG/PDF 存在可打开。
- [ ] result.json 契约字段齐全（四形态）+ case_id 正确 + status/sources/uncertainty/
      change_records 诚实；G1–G8 全过。
- [ ] 中文标签字体回退生效或已记 uncertainty。
- [ ] 无编造数据、无网络访问、无凭据写入；同输入重跑字节级稳定或如实记录差异。

## 4. 决策规则（D1–D18，遇到分支时按此决策并在 result 留痕）

- **D1 数据到图元绑定**：每个图形元素必须有溯源（文件/列/行）。无法溯源的元素
  不画，或画成虚线占位并在 uncertainty 说明原因。
- **D2 量级与单位**：轴标签必须带单位（源数据有单位时）；刻度范围覆盖数据并留
  5% 余量；发现 10 倍以上量级异常 → warn 并保留原值，不"修正"。
- **D3 图例-系列对应**：每个系列恰有一个图例项；系列 id 与图例 id 一致
  （引擎自动校验并记录，G7）。
- **D4 科学实体命名**：实体名取自源材料原文；不翻译、不"优化"拼写。无法确认 →
  保留原文 + uncertain 标记，对照原文确认后才上图。
- **D5 中文字体**：含 CJK 的标签使用 CJK 字体族回退链；PIL 渲染缺字 → validation
  warn + uncertainty 记录，SVG 不受影响。
- **D6 显著性标注**：星号数量与 p 值必须与源标注一致；只转述，不自行计算统计量；
  图注写明 p 值来源与检验方法。
- **D7 可编辑性**：SVG 必须分层（背景/坐标/数据/标注/图例各一层）、元素 id 稳定、
  含 metadata 溯源块；禁止转曲、禁止把文字变路径（G5 real_text 机器检查）。
- **D8 误差线语义**：SE/SD/CI 以源元数据为准（spec.error.semantics），写入
  manifest 并校验。
- **D9 空值/缺失**：不补造。默认「跳过该点并计数记录」；若整列无值 → 该字段报错
  并列 uncertainty，不臆造数值。
- **D10 部分结果**：任何未完成维度 → status=partial + uncertainty 说明原因与
  可复验路径，禁止把失败写成完成（G8）。
- **D11 版本与变更**：源文件 sha256 记录；所有人工修改必须写 change_records
  （时间戳+内容；`--note` 追加）。
- **D12 公平对照**：同输入同参数重复运行结果字节级稳定（SVG/PNG/manifest/
  validation；无随机、固定图元顺序）；对比"加载 Skill vs 不加载"保持相同
  输入、数据版本与导出参数。
- **D13 遮挡与图例越界**：标签过长自动旋转 30°；图例自动移出绘图区；网络图标签
  重叠时手给节点 x/y，重跑后 occlusion 应降为 0（调整记录在 adjustments）。
- **D14 映射闭合**：mapcheck 检查"每个数据图元↔源数据行/值"双向闭合；未闭合的
  元素不得上图或必须虚线占位 + uncertainty。
- **D15 契约四形态**：output_contract 的 list / {name:type} / {fields:[...]} /
  {fields:{name:type}} 四种形态都要完整回显；缺省值按声明容器类型；禁止 null。
- **D16 状态一致性**：status 与产物事实严格自洽（有 fail → partial/不得 completed；
  无图 → failed）；failed_figures/uncertainty/change_records 互不矛盾。
- **D17 样式规则化**：期刊样式一律走 `templates/journal_styles.json` 预设或 spec
  内联覆盖，形成可复用配置而非一次性手工调整；加新期刊 = 加预设键。
- **D18 再跑证据**：重跑验证（verify_rerun）对比 sha256；SVG/JSON 应字节级稳定；
  时间戳类字段差异如实记录，不掩盖。

## 5. 检查点速查（CP1–CP6 判定）

| CP | 内容 | 判定（全部满足才算过） |
|-|-|-|
| CP1 | 材料盘点 | case_id 已取；task.md 已读或已记 uncertainty；数据文件已发现（缺 → 不 completed） |
| CP2 | 抽取 | 每列语义无歧义；实体/关系有来源；不确定候选已记录 |
| CP3 | spec lint | type/id/列/误差语义/显著性锚点/网络边 无 error |
| CP4 | 导出 | 每图 SVG+PNG+PDF 存在；SVG 分层含溯源；预览可打开 |
| CP5 | 双校验 | G1–G8 全过；mapcheck 0 mismatch；确定性通过或如实记录 |
| CP6 | 契约 | 四形态字段全回显（无 null）；status 自洽；artifacts_sha256 记录 |

## 6. 异常处理（失败分支表，完整推理见 references/failure-modes.md）

| 情形 | 处置 | result 记录 |
|-|-|-|
| 数据文件缺失/为空 | 报 SpecError，明确缺失路径；不猜内容 | status=partial；uncertainty=缺失文件 |
| 缺列（x/y/误差列） | extract 画像修正列名；推断失败→报错列出可用列 | failed_figures + uncertainty |
| 空值/NaN | 跳过并计数；整列无值→报错 | uncertainty 记空值策略与数量 |
| 数值量级异常 | warn 保留原值，标注可疑 | uncertainty |
| 标签过长/刻度重叠 | 自动旋转 30°（记录 adjustments） | validation.adjustments |
| 图例遮挡数据 | 自动移出绘图区（记录 adjustments） | validation.adjustments |
| CJK 字体缺失 | SVG 回退链照常生成；PNG 记 warn | uncertainty |
| 显著性缺配对 | validation fail → 修 spec 后重跑 | 阻止 completed（G7/G8） |
| 网络关系悬空 | 不画该边并记录 warning | validation.warnings |
| 导出失败（写文件/Pillow 缺失） | 保留下一步产物（SVG 先行），记录警告 | warnings/uncertainty |
| 题目给 PDF 生物源 | 用平台 pdf-text-tool/ocr-tool 提取文本 → 词表/行语法抽取 → 手写 spec 重绘 | sources 记录 PDF sha256 |
| 契约字段先天缺 | 按声明容器类型给默认值（禁止 null） | output_contract_applied |
| 手动改图 | `--note` 追加 change record（时间戳+说明） | change_records |

## 7. 脚本与资源速览（$SKILL_DIR 相对）

```
SKILL.md                      本文件（v2：CP1–CP6 + D1–D18）
README.md                     使用说明 / TEST.md 实测记录 / COMPARE.md 三方对照
scripts/main.py               编排入口：CP1→CP6，生成产物 + result.json
scripts/chartkit.py           渲染引擎（Scene → SVG/PNG/PDF + 八类校验）
scripts/extract.py            CP2：列画像 + 实体/关系抽取（extract.json）
scripts/spec_lint.py          CP3：figure spec 结构校验（E1–E10）
scripts/figcheck.py           CP5：G1–G8 硬门 + 六类检查点（交付审计）
scripts/mapcheck.py           CP5：数据↔图元双向映射 + 源值核对
scripts/verify_rerun.py       D18：确定性再跑验证 / artifacts sha256
scripts/cjkfont.py            中文字体发现与回退（编码规范执行端之一）
scripts/svgtext.py            SVG 文本转义/清理（编码规范执行端之一）
templates/figure_map.schema.json   图规格声明式契约（JSON Schema 风格）
templates/result.template.json     result.json 信封模板
templates/journal_styles.json      期刊样式预设（default/nature/cell/prism/minimal/ppt）
templates/entity_glossary.json     连接规则字典 + 实体词表
references/output-contract.md     result.json / validation / manifest / spec 契约 + G1–G8
references/rubric-map.md          五维评分 → 设计覆盖对照
references/workorder-field-map.md 输入→字段→输出 映射链
references/audit-rules.md         审计规则（检查项/级别/处置）
references/encoding-spec.md       CJK/单位/实体命名/SVG 编码规范
references/typesetting-presets.md 期刊排版预设说明
references/failure-modes.md       失败模式与处置（M/D/R/E 四类）
examples/                     最小示例（case.json/task.md/data.csv/entities.json/
                               material.md/OUTPUT.md/output 真实产物，标注非正式案例）
```

调用方式（脚本自定位，任意 cwd 均可；`$SKILL_DIR` 为安装根，如 `/skills/weekly-skill`）：
```bash
python $SKILL_DIR/scripts/main.py --case /input/case.json --out /app/output
python $SKILL_DIR/scripts/figcheck.py --dir /app/output --case /input/case.json
python $SKILL_DIR/scripts/mapcheck.py --dir /app/output --case /input/case.json
```

## 8. 限制（如实声明）

- 统计（显著性计算、拟合、检验）不在本 Skill 范围：只转述材料已给的 p 值/统计量。
- 机制/通路图的自动布局为启发式（按 group 分层 + 行内分布）；复杂图建议在 spec
  手给节点 x/y（D13）。
- PDF 预览 = 光栅预览嵌入 PDF（检查用）；投稿要求的矢量可编辑源以 SVG 为准。
- 中文字体依赖运行环境字体（Windows/常见 Linux 字体目录自动发现；FONT_PATHS 可扩展）；
  缺字体时 SVG 靠回退链、PNG 记 warn（D5）。
- 词表扫描只做候选提示，不替代 Agent 对源材料的确认（D4）。