---
name: scientific-figure-craft
description: >
  科研数据图表生成与编辑 Skill。当输入包含科研数据表格（CSV/TSV/JSON）、统计结果、实验记录、
  或需要生成/编辑示意图、机制图、流程图、柱状图、折线图、散点图、箱线图、热图、扇区图、
  通路图、多面板组合图（关键词如 figure、chart、plot、diagram、数据图、科研绘图、机制图、
  通路图、graphical abstract、SVG、可编辑图稿、制图、出图）时使用本 Skill：
  从源数据抽取实体/关系/数值 → 生成可编辑分层 SVG（每个图元带 data-* 溯源属性）→
  输出 PNG/PDF 预览 → 标注校验 → 按输出契约写 result.json。严格以真实文件为准，
  不臆造数据、不提交预制答案。
---

# 科研数据图表生成与编辑（scientific-figure-craft）

面向「玻尔产品周赛·学术效率·第三期」的 challenge-1bd90d8a（figures 组）。
本 Skill 帮助 Agent 把源数据/科研材料**真正走通**：读源数据 → 抽取实体-关系-数值 →
生成可编辑图稿 → 导出渲染 → 标注校验 → 交付可复核的 result.json。

## 1. 用途与适用条件

- **适用**：平台固定 3 个案例（图表生成 / 样式调整 / 标注校验 / 源数据关联 / 可编辑导出）。
  也可用于任何「数据表 → 可编辑科研图」的一般请求。
- **不适用/边界**：不负责统计方法选择与显著性计算本身（显著性标注只转述源数据给出的 p 值）；
  不负责实验设计；不替用户下科学结论。文字转述不能替代真实运行证据。
- **运行环境**：Python 3.8+ 标准库 + Pillow（渲染 PNG/PDF）。matplotlib/cairosvg/svgwrite
  均非必需。无网络依赖。

## 2. 输入与输出

### 输入（平台运行期）
- `/input/case.json` —— 案例说明（含 figure 规格、data 引用、output_contract 等）。
- `/input/task.md` —— 任务说明。
- 材料：源数据表（CSV/TSV/JSON）、可能含生物源文献（如 PDF，用于 figure03 提取实体关系）。
- 本 Skill 安装在 `/skills/weekly-skill`（自包含，脚本用 `os.path.dirname(__file__)` 自定位，
  不依赖当前工作目录）。

### case.json 的组织形态（脚本兼容）
顶层对象（或 `{"cases":[...]}` / 数组取第一项），可含：
- `case_id` / `id`：案例标识（result.json 必须回显）。
- `title`、`dataset_version`：元信息。
- `task_file`：task.md 路径（缺省自动找同目录 task.md）。
- `data` / `data_files`：源数据（也可放案例同目录由脚本自动发现）。
- `figures`（或 `figure` / `figure_spec`）：一个或多个图规格，每项：
  - `id`、`type`（bar/line/scatter/box/heatmap/pie/network/panel/auto）、`title`、`subtitle`、
    `width`、`height`、`style`（default/nature/cell/prism/minimal/ppt）、`filter`（如
    `{"column":"time_h","eq":"24"}`）、`data_file`、`order`、列映射（x/y/hue/error/…）、
    `annotations`（显著性）、`entities_file`（network）。
  - 列映射缺省时引擎会按列名推断（time/dose → x，se/sem/sd → 误差线，低基数列 → 分类）。
- `output_contract`：result.json 必须包含的字段（list 或 {name:type}）。
- `manual_confirmations`：人工确认记录（原样带入 result）。

### 输出（/app/output，一律 UTF-8）
- `figure-<id>.svg` —— 可编辑分层矢量源（`<g id="layer-*">` 分层：坐标轴/数据/文字/图例/标注；
  `<metadata id='provenance'>` 溯源块；每个数据图元带 `data-*` 属性可回溯到源文件/列/行）。
- `figure-<id>.png` —— PNG 预览（同一图元场景渲染，与 SVG 逐元素一致）。
- `figure-<id>.pdf` —— 预览 PDF（PNG 嵌入；仅作检查用，可编辑源是 SVG）。
- `data_manifest.json` —— 图元 ↔ 源数据映射（文件/列/行/值/哈希）。
- `validation.json` —— 标注校验清单（溯源/图例-系列/轴单位/范围/显著性/CJK 字体/遮挡/空值）。
- `result.json` —— 结构化结果：output_contract 全部字段 + `case_id` +
  `status`/`sources`/`uncertainty`/`change_records`/`outputs`/`renders` 等，如实记录。

## 3. 执行步骤（按顺序，缺一不可）

### S0 读取实际文件（先看文件，再谈内容）
1. 读取 `/input/case.json` → 记录 `case_id`、figure 列表、output_contract 字段清单。
2. 读取 `/input/task.md`（或 `task_file` 指向的文件）→ 提炼：要几张图、每张图型、
   目标样式/期刊、数据来源、每图图面约束（轴单位、误差线语义、显著性、样本量、图例要求）。
3. 列出案例材料（同目录表格/文献文件），对每个源文件先算 sha256 并记录版本号
   （`dataset_version`），确认存在性与行数。
4. **禁止**：不读文件就按文件名/标签猜内容；把材料摘要当源数据用；编造不存在的列。

### S1 抽取实体-关系-数据（写到 /app/work/extract.json）
- 数值图：逐列记录 {列名, 语义(x/y/误差/样本量), 取值范围, 单位, 空值位置}。
- 机制/通路图（如 figure03 为生物源材料）：从文献文字（可用平台 pdf-text-tool / ocr-tool，
  无则用纯文本）抽取实体 {id, label, group, cite(来源图表/行)} 与关系
  {from, to, label, type(激活/抑制/磷酸化/转录…)}；**每个实体/关系标注其来源**（段落/图号），
  拼错与"修正拼写"均不允许——科学实体名以源材料原文为准。
- 数值到图元：明确每根柱子/每个点/每个单元来自哪一列哪一行（行号 = 源数据出现顺序）。

### S2 设计图规格（写到 /app/work/figure_spec.json）
- 按 task.md 选图型；把 S1 的列映射写进 spec；误差线注明语义（SE/SD/CI）；显著性只转述
  材料中的 p 值并在脚注写明来源与检验方法；多面板用 `panel` + `panels[]`。
- 样式：按目标期刊选 `style`（nature 300dpi 等），或给出自定义 `layout` 边距与字号。
- 中文标签：交给引擎字体族回退链（SVG 不受影响；PNG 缺字会在 validation 记 warn 并如实说明）。

### S3 生成可编辑源文件与渲染（核心，必须真实运行）
```bash
python /skills/weekly-skill/scripts/main.py --case /input/case.json --out /app/output
```
- 以 `/app/work` 为工作目录（临时文件、中间 spec 放这里）；最终产物写 `/app/output`。
- 上面的命令只依赖脚本自定位（`os.path.dirname(__file__)`），不用 cd 到技能根。
- 脚本会输出：分层 SVG + PNG + PDF + data_manifest.json + validation.json + result.json。
- 若案例含多张图，脚本按 `figures[]` 依次处理，单图失败不阻塞其他图（status=partial）。

### S4 校验与人工检查
1. 读 `/app/output/validation.json`：任何 `fail` 必须修复后重跑；`warn` 逐条判断处置：
   - 遮挡（occlusion）：网络图可给节点补 `x/y` 坐标手工布局；柱图标签过长可调 `width` 或
     `x.tick_rotation`；图例遮挡自动移出绘图区（脚本已内置，check 记录）。
   - CJK 字体缺失：PNG 缺字时记录 uncertainty（SVG 浏览器打开仍正常）。
2. 用浏览器/图片查看工具打开 PNG 做**视觉终检**（坐标、单位、图例、显著性星号、实体名拼写）。
3. 逐图核对 `data_manifest.json`：抽 3-5 个图元，验证其坐标/数值与源表一致。

### S5 写 result.json（脚本已生成，Agent 复核后增补）
- 确保 output_contract 每个字段都在 result.json 顶层（脚本已自动映射；别名如
  `editable_source`/`rendered_preview`/`field_mapping`/`validation_report` 已绑定真实产物）。
- `status`：completed（全部图+校验完成）/ partial（有图失败或材料缺失，须列 uncertainty）/
  failed（无法运行）。
- `uncertainty`：凡有保留（缺列、空值策略、字体缺字、手动改位置、无法核验的统计）都写。
- `change_records`：脚本自动记录步骤；人工修改用
  `python main.py --case ... --out /app/output --note "手工调整..."` 追加，带时间戳。
- `sources`：每个源文件的 file/sha256/rows/版本。

### S6 自查清单（提交前逐项过）
- [ ] 每张图：图上有数据的图元 100% 能回到源数据（data-* 或 manifest）。
- [ ] 轴标签带单位（源数据带单位时）；刻度范围覆盖数据并留白。
- [ ] 图例 ↔ 系列一一对应（脚本自动校验 legend-mapping）。
- [ ] 显著性星号与 p 值/来源一致（转述，不自行计算）。
- [ ] 科学实体名与源材料原文一致，未"修正"拼写。
- [ ] SVG 分层可编辑、含 metadata 溯源、无转曲；PNG/PDF 存在可打开。
- [ ] result.json 契约字段齐全 + case_id 正确 + status/sources/uncertainty/change_records 诚实。
- [ ] 中文标签字体回退生效或已记 uncertainty。
- [ ] 无编造数据、无网络访问、无凭据写入。

## 4. 决策规则（D1–D12，遇到分支时按此决策并在 result 留痕）

- **D1 数据到图元绑定**：每个图形元素必须有溯源（文件/列/行）。无法溯源的元素不画，
  或画成虚线占位并在 uncertainty 说明原因。
- **D2 量级与单位**：轴标签必须带单位（源数据有单位时）；刻度范围覆盖数据并留 5% 余量；
  发现 10 倍以上量级异常（数值 vs 标题语义）→ warn 并保留原值，不"修正"。
- **D3 图例-系列对应**：每个系列恰有一个图例项；系列 id 与图例 id 一致（引擎自动校验并记录）。
- **D4 科学实体命名**：实体名取自源材料原文；不翻译、不"优化"拼写。无法确认 → 保留原文 +
  加 uncertain 标记。
- **D5 中文字体**：含 CJK 的标签使用 CJK 字体族回退链（YaHei/Noto CJK/思源/文泉驿/SimHei）；
  PIL 渲染缺字 → validation warn + uncertainty 记录，SVG 不受影响。
- **D6 显著性标注**：星号数量与 p 值必须与源标注一致；只转述，不自行计算统计量；
  在脚注/图注写明 p 值来源与检验方法。
- **D7 可编辑性**：SVG 必须分层（背景/坐标/数据/标注/图例各一层）、元素 id 稳定、
  含 metadata 溯源块；禁止转曲、禁止把文字变路径。
- **D8 误差线语义**：SE/SD/CI 以源元数据为准（spec.error.semantics），写入 manifest 并校验。
- **D9 空值/缺失**：不补造。默认「跳过该点并计数记录」；若整列无值 → 该字段报错并列
  uncertainty，不臆造数值。
- **D10 部分结果**：任何未完成维度 → status=partial + uncertainty 说明原因与可复验路径，
  禁止把失败写成完成。
- **D11 版本与变更**：源文件 sha256 记录；所有人工修改必须写 change_records（时间戳+内容）。
- **D12 公平对照**：同输入同参数重复运行结果字节级稳定（无随机、固定 seed 语义）；
  对比"加载 Skill vs 不加载"时保持相同输入、数据版本与导出参数。

## 5. 异常处理（失败分支表）

| 情形 | 处置 | result 记录 |
|-|-|-|
| 数据文件缺失/为空 | 报 SpecError，明确缺失路径；不猜内容 | status=partial；uncertainty=缺失文件 |
| 缺列（x/y/误差列不存在） | 自动按列名推断；推断失败→报错列出可用列 | failed_figures + uncertainty |
| 空值/NaN | 跳过并计数；整列无值→报错 | uncertainty 记空值策略与数量 |
| 数值量级异常 | warn 保留原值，标注可疑 | uncertainty |
| 标签过长/刻度重叠 | 自动旋转 30°（记录 adjustments） | validation.adjustments |
| 图例遮挡数据 | 自动移出绘图区（记录 adjustments） | validation.adjustments |
| CJK 字体缺失 | SVG 用回退链照常生成；PNG 记 warn | uncertainty |
| 导出失败（写文件/Pillow 缺失） | 保留下一步产物（SVG 先行），记录警告 | warnings/uncertainty |
| 题目给 PDF 生物源 | 用平台 pdf-text-tool/ocr-tool 提取文本 → 抽实体关系 → 手写 spec 重绘 | sources 记录 PDF sha256 |
| 手动改图 | `--note` 追加 change record（时间戳+说明） | change_records |

## 6. 脚本与资源速览（相对本 Skill 根目录）

```
SKILL.md                    本文件
scripts/main.py             主入口：case.json → 图稿/渲染/manifest/validation/result.json
scripts/figure_engine.py    渲染引擎（手写 XML SVG + Pillow PNG/PDF；图类型全套）
scripts/validate_result.py  独立复核 out 目录（契约/文件/SVG/PNG/PDF）
styles/presets.json         期刊样式预设（default/nature/cell/prism/minimal/ppt）
references/OUTPUT_CONTRACT.md  result.json / manifest / validation / figure spec 契约
references/RUBRIC_MAP.md      五维评分 → 设计覆盖对照
examples/                   最小示例（标注为示例，非正式案例）
```

调用方式（脚本自定位，任意 cwd 均可）：
```bash
python /skills/weekly-skill/scripts/main.py --case /input/case.json --out /app/output
python /skills/weekly-skill/scripts/validate_result.py --dir /app/output --case /input/case.json
```

## 7. 限制（如实声明）

- 统计（显著性计算、拟合、检验）不在本 Skill 范围：只转述材料已给的 p 值/统计量。
- 机制/通路图的自动布局为启发式（分层 + 按组分行）；复杂图建议在 spec 中手给节点 x/y。
- PDF 预览 = 光栅预览嵌入 PDF（检查用）；投稿要求的矢量可编辑源以 SVG 为准。
- 中文字体依赖运行环境字体（Windows/常见 Linux 字体目录自动发现；FONT_PATHS 可扩展）。