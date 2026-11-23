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
  本版（v7r）在基线骨架之上追加一条可跑的确定性判据：scripts/determinism.py 跨进程 / 跨 cwd / 跨 PYTHONHASHSEED 连跑 N 次，对输出目录内全部产物做 sha256 比对，并按 N1–N4 归一化规则逐字段定位不稳定来源（时间戳 / 运行根路径 / 自引用哈希 / PDF 内嵌日期）。
---

# 科研数据图表生成与编辑（scientific-figure-craft）v2

面向「玻尔产品周赛 · 北大专区 · 学术效率 · 第三期」 challenge-1bd90d8a（figures 组）。

> **本包形态**：只含 UTF-8 文本资源（`.md/.py/.json/.txt/.csv`），**没有任何二进制**
> （无 `.pptx/.png/.pdf/.svg/` 字体/`__pycache__`）；交付的图与预览一律由
> `scripts/main.py` **运行时生成**。所有命令用 `$SKILL_DIR` 自定位，cwd 不影响执行。
> 五维评分（实际效果 40 / 使用增益 25 / 创新增益 15 / 可靠体验 10 / 生态贡献 10）
> 的逐条落点见 `references/RUBRIC_MAP.md`。

v2 相对 v1 的实质强化：**执行决策显性化** —— ① 六个检查点（CP1–CP6）把
「读源数据 → 出图 → 调样式 → 校验标注 → 交付可编辑文件」拆成可判定门；
② 十八个决策规则（D1–D18）覆盖材料异常/契约四形态/状态一致性/失败分支；
③ 图元↔源数据双向映射由 `mapcheck.py` 机器核对（不再靠人工抽查）；
④ 校验由 `figcheck.py` 以 G1–G8 硬门收口，status 与产物严格自洽。

**执行顺序（先读契约，再抽取，后生成，最后自评）**：
**① 读 `references/OUTPUT_CONTRACT.md`（交付什么、G1–G8 硬门）→
② CP1 盘点材料 → ③ CP2 抽取（extract.json）→ ④ CP3 `spec_lint` 生成门 →
⑤ CP4 `main.py` 生成 SVG/PNG/PDF → ⑥ CP5 双校验（`mapcheck` + `figcheck` + 确定性）→
⑦ CP6 契约落地（`check_contract` 复核字段覆盖）→ ⑧ 按 `references/RUBRIC_MAP.md` 逐条自评五维覆盖。**

> **自定位（本 Skill 必须能在任意 cwd 下运行）**：所有命令用 `$SKILL_DIR` 前缀——
> 它是**本文件所在目录的绝对路径**（平台安装期为 `/skills/weekly-skill`）。
> 脚本内部一律用 `os.path.dirname(os.path.abspath(__file__))` 解析
> `templates/`、`references/`，所以**cwd 与技能根目录不同也不影响**。
>
> ```bash
> # bash：先设一次，后续命令照抄
> SKILL_DIR=/skills/weekly-skill          # 安装到别处就填那个绝对路径
> python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output
> ```
> ```powershell
> # PowerShell（把占位符换成技能包的实际绝对路径；平台为 /skills/weekly-skill）
> $SKILL_DIR = "<技能包绝对路径>"
> python "$SKILL_DIR\scripts\main.py" --case \input\case.json --out \app\output
> ```
> 若不确定安装位置，可在任意目录用一行命令打印自定位结果：
> ```bash
> python -c "import sys,os;sys.path.insert(0,r'<SKILL_DIR>/scripts');import chartkit;print(chartkit.skill_root())"
> ```

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
1. 读取 `references/OUTPUT_CONTRACT.md`（G1–G8 与字段/类型）与
   `references/audit-rules.md`（检查标准）。
2. 读取 `/input/case.json` → 记录 `case_id`、figure 列表、output_contract 形态。
3. 读取 `/input/task.md` → 提炼：要几张图、图型、目标样式/期刊、数据来源、
   图面约束（轴单位、误差线语义、显著性、样本量、图例要求）。
4. 定位 `$SKILL_DIR`（本文件所在目录）；所有命令用绝对路径/脚本自定位
   （见上文「自定位」：cwd 不是技能根目录也照跑）。

### S1 **CP1 材料盘点**（先看文件，再谈内容）
1. 列出案例材料（同目录表格/文献文件），对每个源文件先算 sha256 并记录版本
   （`dataset_version`），确认存在性与行数。
2. **禁止**：不读文件就按文件名/标签猜内容；把材料摘要当源数据用；编造列。
3. 检查点 CP1：`case_id` 已取、task.md 已找到或已记 uncertainty、数据文件已发现
   （一个都没有 → status 不得 completed）。

### S2 **CP2 抽取实体-关系-数据**（extract.py，写 /app/work/extract.json）
```bash
python "$SKILL_DIR/scripts/extract.py" --case /input/case.json --out /app/work
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
python "$SKILL_DIR/scripts/spec_lint.py" --spec /input/case.json --case /input/case.json
# {"valid": true} 才可进入生成；有 error 按 D4 决策后记录并修复
# 退出码：0 = valid；2 = 有 error（不得进入 CP4）；1 = 用法/文件错误
```
- 检查点 CP3：图型合法、列存在、误差语义常规、显著性有锚点+来源、网络边不悬空。
- lint 结果写进 result.json 的 `spec_lint` 与 checkpoints.cp3_spec_lint。

### S4 **CP4 生成可编辑源与渲染**（核心，必须真实运行）
```bash
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output \
      --work /app/work [--task /input/task.md] [--style nature] [--dpi 300] [--note "人工调整"]
# 退出码：0 = completed 且 G1–G8 全过；2 = partial；1 = failed
```
- 脚本自定位；以 /app/work 为中间产物目录；最终产物写 /app/output。
- 多张图按 `figures[]` 依次处理，单图失败不阻塞其他图（status=partial）。
- 检查点 CP4：每张图 SVG+PNG+PDF 齐全；SVG 分层、含溯源；PNG/PDF 可打开。

### S5 **CP5 双校验**（main.py 内自动执行，也可单独复核）
```bash
python "$SKILL_DIR/scripts/mapcheck.py"  --dir /app/output --case /input/case.json
python "$SKILL_DIR/scripts/figcheck.py"  --dir /app/output --case /input/case.json
python "$SKILL_DIR/scripts/verify_rerun.py" --case /input/case.json --out /app/output
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
2. **字段覆盖用命令复核**（不靠目检）：
```bash
python "$SKILL_DIR/scripts/check_contract.py" --result /app/output/result.json --case /input/case.json
# PASS（missing=0 null=0 contract_missing=0）才算契约落地；退出码 1 = 有缺口
```
3. `status` 与产物事实严格一致（G8）：有 fail/缺口 → 不得 completed。
4. 视觉终检：用浏览器打开 SVG / 查看 PNG（坐标、单位、图例、显著性星号、实体名拼写）。
5. 检查点 CP6：`output_contract_applied`、`gates.all_pass`、artifacts_sha256 已记录。

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

## 7. 脚本与资源速览（相对 `$SKILL_DIR`）

```
SKILL.md                      本文件（CP1–CP6 + D1–D18 + 自定位调用）
README.md                     使用说明（依赖/安装/调用/设计/限制/维护）
TEST.md                       真机实测记录（编译/冒烟/确定性/契约/异常/合规）
COMPARE.md                    对照方案（基准做法 vs 加载后）+ 结构三方对照
GITHUB_URL.txt                公开作品链接（单行）
scripts/main.py               编排入口：CP1→CP6，生成产物 + result.json（--case/--out）
scripts/chartkit.py           渲染引擎（Scene → SVG/PNG/PDF + 八类校验，可 import 复用）
scripts/extract.py            CP2：列画像 + 实体/关系抽取（extract.json）
scripts/spec_lint.py          CP3：figure spec 结构校验（E1–E10，exit 2 = 有 error）
scripts/figcheck.py           CP5：G1–G8 硬门 + 六类检查点（交付审计）
scripts/mapcheck.py           CP5：数据↔图元双向映射 + 源值核对（容差 1e-9）
scripts/verify_rerun.py       D18：确定性再跑验证 / artifacts sha256
scripts/check_contract.py     CP6：result.json 字段覆盖自查（解析 OUTPUT_CONTRACT.md）
scripts/cjkfont.py            中文字体发现与回退（编码规范执行端之一）
scripts/svgtext.py            SVG 文本转义/清理 + 防转曲检查（编码规范执行端之一）
templates/figure_map.schema.json   图规格声明式契约（JSON Schema 风格）
templates/result.template.json     result.json 信封模板
templates/journal_styles.json      期刊样式预设（default/nature/cell/prism/minimal/ppt）
templates/entity_glossary.json     连接规则字典 + 实体词表
references/OUTPUT_CONTRACT.md     结果契约（§0 机器可读必需字段 + G1–G8 + 四形态规则）
references/RUBRIC_MAP.md          五维评分（40/25/15/10/10）→ 本包文件与机制逐条对照
references/workorder-field-map.md 输入→字段→输出 映射链
references/audit-rules.md         审计规则（检查项/级别/处置）
references/encoding-spec.md       CJK/单位/实体命名/SVG 编码规范
references/typesetting-presets.md 期刊排版预设说明
references/failure-modes.md       失败模式与处置（材料/数据/渲染/导出/契约/依赖/状态）
examples/                      最小示例（合成输入，非正式案例）：README.md / case.json /
                               task.md / data.csv / entities.json / material.md /
                               EXPECTED-OUTPUT.md（预期产物文字清单）/ output/（真实运行的契约 JSON）
```

调用方式（脚本自定位，**任意 cwd 均可**；`$SKILL_DIR` = 本文件所在绝对路径，
平台为 `/skills/weekly-skill`）：
```bash
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output
python "$SKILL_DIR/scripts/check_contract.py" --result /app/output/result.json --case /input/case.json
python "$SKILL_DIR/scripts/figcheck.py" --dir /app/output --case /input/case.json
python "$SKILL_DIR/scripts/mapcheck.py" --dir /app/output --case /input/case.json
```

本包示例（与正式案例无关，仅验证接口）：见 `examples/README.md` 与
`examples/EXPECTED-OUTPUT.md`。**包内不含任何图或预览的二进制文件**——
`figure-*.svg/png/pdf` 一律由 `main.py` 运行时生成。

## 8. 限制（如实声明）

- 统计（显著性计算、拟合、检验）不在本 Skill 范围：只转述材料已给的 p 值/统计量。
- 机制/通路图的自动布局为启发式（按 group 分层 + 行内分布）；复杂图建议在 spec
  手给节点 x/y（D13）。
- PDF 预览 = 光栅预览嵌入 PDF（检查用）；投稿要求的矢量可编辑源以 SVG 为准。
- 中文字体依赖运行环境字体（Windows/常见 Linux 字体目录自动发现；FONT_PATHS 可扩展）；
  缺字体时 SVG 靠回退链、PNG 记 warn（D5）。
- **资源形态**：本包只含 UTF-8 文本资源（`.md/.py/.json/.txt/.csv`），**不含任何二进制**；
  `figure-*.svg/png/pdf` 与全部预览一律由 `scripts/main.py` 在运行时生成，
  因此包内也没有可被误当"预制答案"的成品图。
- 词表扫描只做候选提示，不替代 Agent 对源材料的确认（D4）。

---

## 附:本版增量 —— 字节级可复现轴

> 本节是本版（**v7r**）相对上面正文的**唯一增量**：正文 §1–§8（含 H1 标题、`$SKILL_DIR` 命令、
> 参数表、契约说明、CP1–CP6、D1–D18）与基线逐字一致，本节只补上本轴的**可运行命令、判据与实测数字**。
> 逐字段详解与稳定化配方见 `references/DETERMINISM.md`；本轴的完整论述另存
> `references/SKILL-FULL-字节级可复现轴.md`（正文之外的长文，不参与执行流程）。

本题的「结果可核验性」不是一句形容词 —— 它等价于一个问题：
**别人拿同一份 `case.json` 和同一组参数再跑一次，能不能得到同一张图、同一份 `result.json`？**
本版把这个问题做成可执行的东西：`scripts/determinism.py`。

### 附.1 本轴断言与证据

| # | 断言 | 可复跑证据 |
|-|-|-|
| A1 | 可编辑源（`figure-*.svg`）、预览位图（`figure-*.png`）、`data_manifest.json`、`validation.json` 是**逐字节可复现**的 | `determinism.py` 实测 **6/11** 个产物文件在 5 次重复中字节全同 |
| A2 | `result.json` 与两份报告**逐字节不同**，但差异 100% 落在四类已知字段上，施加 N1–N4 后完全一致 | 阶梯 exit **2**；`volatile_classes = {"run_root_path": 2, "self_reference_hash": 2, "timestamp": 2}`，**无 `unknown`** |
| A3 | 产物里还有 **4 处**本机绝对路径，不影响同机重跑，但会影响换机复现 | `abs_path_leaks` 4 条，逐条列出文件与字段（见附.5） |
| A4 | 脚本自定位：`cwd` 轮转 4 种角色（运行目录 / 系统临时目录 / 案例目录 / 技能根）都产出同样结果 | 5 次运行的 `cwd_role` 与 `exit`/`status`/键数完全相同 |

### 附.2 先跑这一条命令（本轴核心）

```bash
# $SKILL_DIR = 本文件所在目录（平台安装期为 /skills/weekly-skill）
python "$SKILL_DIR/scripts/determinism.py" \
    --case /input/case.json --runs 5 \
    --seeds 0,1,12345,7,99 --mode isolated \
    --workroot /app/work/det --out /app/work/det/determinism_report.json
```

它做四件事（缺一不可）：

1. 每一次重复都是**独立进程**（`subprocess`），不是同进程里复用；
2. 每次换一个 **cwd**（运行目录 → 系统临时目录 → 案例目录 → 技能根，循环）；
3. 每次换一个 **`PYTHONHASHSEED`**（证明产物不依赖 dict/set 的哈希顺序）；
4. 每次换一个**输出目录绝对路径**（`--mode isolated`），把「路径泄漏进产物」也一起测。

然后对**输出目录里的全部文件**（不是只对 `result.json` 里登记的那几个）做 sha256 比对，
并给出两级判定：`identical`（原始字节）与 `normalized_identical`（归一化之后）。

对照实验：把「输出目录」这个变量单独排除 ——

```bash
python "$SKILL_DIR/scripts/determinism.py" --case /input/case.json \
    --runs 3 --mode inplace --workroot /app/work/det-inplace \
    --out /app/work/det-inplace/determinism_inplace_report.json
```

`--mode inplace` 让每次重复都写**同一个绝对输出目录**。实测逐字节相同的文件从 6/11 升到 **8/11**，
`run_root_path` 这一类**整体消失** —— 证明 `figcheck_report.json` / `mapcheck_report.json`
的唯一不稳定来源就是那个 `dir` 字段。

### 附.3 判据：退出码四档阶梯

| 退出码 | 含义 | 拿到它意味着 |
|-|-|-|
| 0 | 全部产物逐字节相同 | 最强；任何人同输入都能得到同一份字节 |
| 2 | 字节级不同，但归一化后完全一致 | 不确定性 100% 被 N1–N4 解释，**不是随机** |
| 3 | 归一化后仍有差异 | 存在未解释的不确定性，报告给首个差异文件与字节偏移 |
| 1 | 至少一次运行没产出可解析的 `result.json` | 无法判定（先修主流程） |

### 附.4 归一化规则 N1–N4（哪些是**故意**不稳定的）

| 规则 | 对象 | 为什么这样定 |
|-|-|-|
| **N1** | JSON 里键名为 `ts` 的值 → `<TS>` | `chartkit.now_ts()` 记的是本地时间；本包把它当审计线索**故意保留** |
| **N2** | 本次运行根路径 → `<RUNROOT>` | `figcheck_report.json` / `mapcheck_report.json` 的 `dir` 写的是输出目录绝对路径 |
| **N3** | `artifacts_sha256.<file>` → 该文件归一化后的 sha256 | 自引用哈希：PDF 日期一变，它跟着变，但不代表内容变了 |
| **N4** | PDF 的 `/CreationDate`、`/ModDate` → `(D:0)` | Pillow 保存 PDF 时嵌的当前时间；实测这是 PDF 唯一的差异来源（`date_only_diff=True`） |

实测四条规则**全部被触发过**（`normalization_rules_applied = N1, N2, N3, N4`），
且 `volatile_fields` 里没有一条 `unknown` —— 差异是被逐字段解释完的，不是"总体看起来差不多"。

### 附.5 实测数字（本机：Windows + Python 3.13.9）

```
重复 5 次（独立进程）× cwd 轮转 × PYTHONHASHSEED={0,1,12345,7,99}
每次 exit=0、status=completed、result.json 顶层 29 键
→ identical=False，normalized_identical=True，阶梯 exit 2
```

| 项 | 实测值 | 落在报告的哪个字段 |
|-|-|-|
| 运行规模 | 5 次独立进程 × 4 种 cwd 角色 × `PYTHONHASHSEED={0,1,12345,7,99}`，`mode=isolated` | `runs[]` / `cwd_roles` |
| 产物文件集合 | **11 个**，`file_set_identical=true`；5/5 次都产出可解析 `result.json` | `files` / `runs_with_result_json=5` |
| 两级判定 | `identical=false`、`normalized_identical=true` → **阶梯 2** | `ladder` |
| 逐字节相同 | **6/11**：`data_manifest.json`、`validation.json`、`figure-fig-01.svg`、`figure-fig-01.png`、`figure-fig-02.svg`、`figure-fig-02.png` | `identical_files` |
| 逐字节不同 | **5/11**：`result.json`、`figcheck_report.json`、`mapcheck_report.json`、`figure-fig-01.pdf`、`figure-fig-02.pdf` | `differing_files` |
| 差异分类 | `{"run_root_path": 2, "self_reference_hash": 2, "timestamp": 2}`，**无 `unknown`** | `volatile_classes` |
| 归一化命中 | `N1, N2, N3, N4` 四条全部被触发 | `normalization_rules_applied` |
| 单次耗时 | 5 次全跑 **6.97 秒** | `elapsed_seconds` |
| 对照实验（`--mode inplace`，3 次） | 逐字节相同 **8/11**，`run_root_path` 类整体消失，耗时 5.19 秒 | `determinism_inplace_report.json` |
| PDF 差异性质 | 两份 PDF 均 `date_only_diff=true`，首个差异偏移 **343132** / **72397** 字节（都在文件尾部） | `binary_notes` |
| 产物中的绝对路径 | **4 条**：`figcheck_report.json.dir`、`mapcheck_report.json.dir`、`result.json.steps[*].action`、`result.json.change_records[*].action` | `abs_path_leaks` |

两份机器可读报告随包发布：`determinism_report.json`（isolated，5 次）与
`determinism_inplace_report.json`（inplace，3 次）。

### 附.6 决策规则（DET1–DET12：分支决定怎么影响「可复现」）

- **DET1 源文件指纹优先**：先对每个输入文件算 sha256 并写进 `result.json.sources`；没有指纹的产物不可复核。
- **DET2 不写运行时间进图**：SVG/PNG 里不得出现时间戳（实测 PNG 无 `tIME`/`iTXt`，SVG 无时间字段）；时间只允许出现在 `result.json.steps[].ts` 与 `change_records[].ts`。
- **DET3 自引用哈希只记别的文件**：`artifacts_sha256` 在 `result.json` 尚未写出时计算，不含自身；一旦发现包含自身，说明写入顺序被打乱。
- **DET4 路径不得进位**：产物 JSON 里的 `file` 字段一律是**相对 `/app/output` 的文件名**；确需写绝对路径的字段（`figcheck_report.dir`）已在 `references/DETERMINISM.md` §9 点名。
- **DET5 判定分级**：先看 `identical`，不同再看 `normalized_identical`；**不允许**用"归一化后一样"掩盖 `unknown` 类差异。
- **DET6 阶梯不入 status**：确定性是**运行属性**，不写进 `result.json.status`；`status` 只描述产物完整性（completed/partial/failed）。
- **DET7 cwd 无关**：任何脚本不得读 `os.getcwd()` 决定资源位置；`cwd` 只用于写用户给的相对路径。
- **DET8 环境如实记录**：`result.json.environment` 记 Python 版本、Pillow 版本、实际发现的字体、dpi、`no_network`；缺 Pillow 时如实记 `null` 而不是编一个版本号。
- **DET9 跨机差异要说清**：换机器/换目录后字节不一致时，先看是不是附.5 点名的绝对路径字段，再考虑环境（字体/库版本），不要笼统归因于"环境不同"。
- **DET10 契约与确定性分开判**：契约字段齐不齐看 `check_contract.py`，字节稳不稳看 `determinism.py`；两个都过才算这一段可交付。
- **DET11 诚实优先于漂亮数字**：为了让阶梯好看而删除时间戳属于**伪造可复现**；正确做法是保留审计字段 + 提供归一化与稳定化两条路。
- **DET12 差异必须落到字段**：报"有差异"时必须给出「文件 + 字段路径 + 类别 + 样例」；只给一个布尔值不算证据。

### 附.7 失败分支（与本轴相关的部分）

| 情形 | 处置 | 落痕 |
|-|-|-|
| 某次运行的 `result.json` 缺失/不可解析 | 阶梯直接判 1（无法判定），不拿剩下几次硬算 | 报告 `runs[].errors` |
| 归一化后仍有差异 | 阶梯 3，报告给首个差异文件与字节偏移；**不得改判成 2** | `differing_files` + `volatile_fields.unknown` |
| 文件集合在不同运行间不一致 | `file_set_identical=false`，优先查写盘失败/竞态 | 报告顶层字段 |
| PDF 差异不止日期 | `date_only_diff=false`，按"未解释差异"处理 | `binary_notes[].first_diff_offset` |
| 产物里出现非预期绝对路径 | 记进 `abs_path_leaks` 并在文档点名 | 报告顶层字段 |
| Windows 控制台编码非 UTF-8 | 脚本只对 stdout/stderr 做 `errors="replace"`；报告文件始终 UTF-8 | 不影响产物 |
| 缺 Pillow | 主流程降级（PNG/PDF 记缺失），确定性实测照跑并如实记阶梯 | `environment.pillow=null` |

### 附.8 本轴入口与参数

| 脚本 | 参数 | 作用 |
|-|-|-|
| `scripts/determinism.py` | `--case --runs --seeds --mode --workroot --out --main --json --keep --timeout --abs-policy --quiet` | ★ 本版新增：字节级可复现实测台（附.2 的命令即用它） |

与包内既有的 `verify_rerun.py` 是**两个互补口径**，不要互相替代：

| 口径 | 覆盖 | 输出 |
|-|-|-|
| `verify_rerun.py`（既有，正文 §3 S5） | 只对比 `result.json` 登记的那几个产物；`result.json` 做时间戳归一化、PDF 做日期剔除 | 一句话 + 逐文件 SAME/DIFF |
| `determinism.py`（本版新增） | **输出目录内全部文件**；跨进程/跨 cwd/跨哈希种子；两级判定 + 逐字段定位 + 绝对路径扫描 | 机器可读 `determinism_report.json` |

**限制与未解决项**：

- 阶梯 0 需要冻结时钟；本包选择保留审计时间戳，因此同机重跑落在阶梯 2（配方见 `references/DETERMINISM.md` §8）。
- `figcheck_report.json.dir` / `mapcheck_report.json.dir` 仍是绝对路径（未改既有脚本）；换机复现前先看附.5 的 4 条泄漏。
- 本轮只在 Windows + Python 3.13.9 实测；Linux 上 PDF 的 `/CreationDate` 由哪个库写需重测。
- 未测并发写同一输出目录的场景。
