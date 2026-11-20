---
name: academic-ppt-builder
description: 把论文/研究材料组织成可编辑学术汇报演示稿（PPTX）。Use when 需要从论文、文献材料或 data 表格生成或编辑学术 PPT：组会汇报、开题/中期、答辩、项目评审、基金申请；覆盖内容取舍与页序规划、页级主张与证据映射、图表数据绑定（重绘/原图/诚实占位）、模板槽位约束、演讲备注、导出预览渲染、多轮局部编辑与版本回退。
---

# 学术 PPT 生成与编辑 Skill（学术效率 · slides 组）

> 目标：把固定科研材料变成**结构清楚、证据可追溯、可编辑、符合模板约束**的
> 学术汇报产物。本 Skill 不负责论文精读/文献综述、不负责可视化算法本身、
> 不负责文字润色、不负责 PPT 软件研发；它负责把材料“翻译”成幻灯片并保证
> 每页数字与图表可核实。

## 1. 用途与适用条件

- **适用**：给定一篇（或一份）研究材料（md/txt/html/csv/json，PDF 先抽文本），
  固定受众/时长/页数上限，组织成一版带演讲备注、页级证据、导出预览的 PPTX。
- **适用但不限于**：组会（方法+下一步）、答辩（贡献+局限）、评审/基金
  （对齐指标+可行性）、同行（对比+复现细节）。受众通过 `spec.audience` 传入，
  影响讲稿语气（`planner.AUDIENCE_TONES`）。
- **边界**：材料确实缺失实验数据/图表/局限段落时，本 Skill **不臆造**，改在
  `uncertainty` 与 `unverified_claims` 中如实标注；位图论文图无取数数据时只放
  “诚实占位”，绝不凭空生成曲线。

## 2. 输入与输出

**输入**（平台约定，本地等价目录亦可）：
- `/input/case.json`：`case_id`、`title`、`inputs{task_md, material[]}`、
  `spec{audience, duration_minutes, max_slides, template/template_pptx/starting_deck,
  style…}`、可选 `output_contract`。
- `/input/task.md`：任务说明。
- `material` 指向的实际文件：正文、数据表等。**先读实际文件，不要凭文件名猜内容**。

**输出**（写 `/app/output`，本地等价 `--out` 目录）：
- `work/deck.pptx`（可编辑源）、`work/plan.json`（页面模型）、`work/table_cache/`
- `work/preview/slide_*.png` + `preview.pdf`（预览渲染，标注“非 PowerPoint 导出”）
- `result.json`（output_contract 全字段 + case_id）、`evidence_map.md`、
  `changelog.jsonl`、`manifest.json`、`logs/`

## 3. 运行环境与依赖

- Python 3.8+；依赖：`python-pptx>=0.6.21`、`matplotlib>=3.5`、`Pillow>=9`、
  `numpy`；`reportlab` 可选（缺席时 PDF 预览自动跳过并说明）。
- 全部脚本**自定位**（`os.path.dirname(__file__)`），从任何 cwd 都能运行；
  运行命令统一以**技能根目录**（含 SKILL.md 的目录）为准：
  ```bash
  cd <技能根>\npython scripts/main.py --case /input/case.json --out /app/output
  ```
  若 cwd 不可控，写成 `python <技能根绝对路径>/scripts/main.py ...`。

## 4. 执行步骤（严格遵守顺序）

### Step 0 — 读实际输入
1. `python scripts/main.py --case /input/case.json --out /app/output`，
   或用 read 工具先人工确认 case.json 与 task.md 内容、材料清单。
2. **PDF 材料**：若输入含 PDF 且环境无 fitz/pypdf/pdfplumber，脚本会提示；
   这时由 Agent 用自身读图/读文能力把原文抽取为 `/app/work/materials/*.txt`
   后重跑（在 `uncertainty` 记录抽取方式）。
3. 检查 `inputs.material` 中每个文件确实存在；缺失的写进 warning 而不是跳过。

### Step 1 — 抽取主线与实体关系数据
脚本自动完成并落盘 `work/material_view.json`：章节（§标题+正文）、数据表
（表头+行）、图/表提及（图N/表N/Figure N/Table N）、研究问题/摘要/方法/
结果/局限/结论定位与候选句。**数字核验**：`common.check_claim_numbers` 对
每条入页主张的材料原文做匹配，找不到的数字进 `unverified_claims`。

### Step 2 — 页面规划（页序 + 页级叙事角色）
`planner.alloc_roles` 按 `spec.max_slides`（3–20，默认 8）确定性分配角色：
封面 → 主线 → 〔背景/讨论/局限按页数〕 → 问题 → 方法 → 结果×n → 结论与下一步。
每页为**一个主张**服务；结果页优先由数据表驱动（表→2 条量化主张+“数值直接取自
源数据”注记），无表才回落结果段落散文。页序、角色、主张、证据指针写入
`work/plan.json`（这是**可编辑源**，也是后续局部编辑的输入）。

### Step 3 — 图表绑定（数据驱动，诚实优先）
- 材料提供数值型数据表 → matplotlib **原样重绘**（`charting.build_chart`，
  标签/数值不改动）→ 嵌入 `chart_image`。
- 无 matplotlib 或数据非数值列 → 降级为 PPTX **原生可编辑表格**（`table`）。
- 材料直接给图片文件 → 原样嵌入（`embedded`）。
- 论文图是位图且无取数数据 → 灰框“诚实占位”，不生成假曲线（`placeholder`）。
结论页从不凭空出图。绑定记录在 `plan.json` 与 `result.evidence`。

### Step 4 — 生成可编辑 PPTX
`deck_builder.build_deck`（python-pptx）：
- 模板约束：无外部模板用 `templates/default.json`（颜色/字体/页脚/槽位全部
  参数化，case `spec.style` 可覆盖）；有 `template_pptx`/`starting_deck` 则
  沿用其母版版式、只填内容槽位；起始稿先备份到 `original_inputs/`。
- 每页：主张式标题 + 要点（≤7 条，单条 ≤90 字，字号自动收敛 ≥12pt 防溢出）
  + 图表槽 + **证据脚注**（图/表/章节） + **演讲者备注**（讲解要点 + 证据 +
  图表说明 + 溢出提示）。
- 保存 `work/deck.pptx`；页级构建回执写入 result（每页字号/图表细节）。

### Step 5 — 导出渲染预览
`render.render_all`：每页一张 PNG（PIL 画布复刻标题/要点/图表/占位/页脚）+
逐页版式 PDF（reportlab）。文件名与 result 均标注 **“预览渲染（PIL/reportlab），
非 PowerPoint 导出”**；CJK 字体缺失、PDF 不可用等如实进 `previews.warnings`。

### Step 6 — 写 result.json 与记录
`result.build_result` 一次写出：`case_id` + `deck`（slide_count、逐页
index/role/title/claims/evidence/figure/notes）+ `evidence`（map、
unverified_claims、material_warnings）+ `previews` + `sources[].sha256` +
`uncertainty` + `change_records` + `status` + `environment`（实测库版本），
并按 `case.json.output_contract` 声明的字段镜像到顶层（容器类型默认值）。
同时生成 `evidence_map.md`、`changelog.jsonl`、`manifest.json`（全部产物
sha256，支撑他人独立复核与复跑）。

### Step 7 — 自查（本步骤结束前必做）
```bash
python scripts/check_contract.py /app/output/result.json /input/case.json
```
必须输出 `"valid": true`。再核对：
- PPTX 可重新打开（脚本已自检 `pptx_reopen`），页数与 plan 一致；
- 每页有备注与证据脚注；
- `unverified_claims` 与 `uncertainty` 逐条有解释，不为 0 而假装干净；
- 预览 PNG/PDF 存在且内容与页面模型一致（视觉抽查封面与结果页）。

### Step 8 — 增量编辑（演示稿迭代，可选但推荐）
多轮修改不推翻整稿：手写一个编辑 JSON（字段见 `examples/edit_demo.json`），
```bash
python scripts/main.py --case /input/case.json --out /app/output \
    --edit edits.json --version v2
```
支持 `update_bullet / add_bullet / remove_bullet / add_note / retitle /
reorder_pages / set_figure`。每次修改在 `changelog.jsonl` 记一条
`{version, op, page, target, reason}`，`deck_v2.pptx` 与 `deck.pptx` 并存、
`plan.json` 更新——改坏了回退 = 复制旧版本重跑。所有改动不得引入材料外数字
（脚本会再次核验新增/修改主张的数字）。

## 5. 异常处理表

| 情形 | 处置 | 记录位置 |
|-|-|-|
| 材料文件缺失 | 记 warning，继续处理其余文件 | `evidence.material_warnings` |
| PDF 无法抽文本 | Agent 人工抽取到 work/materials/*.txt 后重跑；仍不行则 partial | `uncertainty` |
| 主张里的数字材料中找不到 | 该主张 `verified=false` 入 unverified_claims，**不当作正确数据** | `evidence.unverified_claims` |
| 论文图是位图且无数据 | `placeholder` 灰框占位，不生成假图 | `plan.json figure.note` |
| 数据表非数值列/无 matplotlib | 降级原生可编辑表格；`--no-chart` 可强制 | `uncertainty` + `figure.note` |
| 页数超限/槽位不足 | 按 max_slides 确定性压缩（角色分配器），并记录在讲稿备注 | `change_records` |
| 模板/起始稿打不开 | 备份原文件、改内置默认模板，说明降级 | `uncertainty` + `change_records` |
| 字体缺失 | PPTX 只记字体名由打开端替换；预览回落并预警 | `previews.warnings` |
| 预览/PDF 渲染失败 | 不阻断 PPTX；跳过并说明 | `uncertainty`、status=partial |
| 任何步骤抛错 | 独立 try/except，尽量产出部分结果，绝不假装成功 | `status`：success/partial/failed |

**材料缺失、无法判断、运行失败必须分开说明**（分别在 uncertainty /
unverified_claims / status 中），三者的处理规则不同。

## 6. 自查清单（收尾逐项打勾）

- [ ] SKILL 前置：已读 /input/case.json + task.md + 全部实际材料文件
- [ ] 页面：页数=spec.max_slides（或更少且原因已记录）；每页有 index/role/title
- [ ] 内容：每页主张 ≤7 条、单条 ≤90 字、标题 ≤60 字；无整段摘要塞页
- [ ] 数字：页面上每个数字都能指回材料（unverified_claims 为空或有解释）
- [ ] 图表：chart_image/table/embedded/placeholder 四态均真实（无凭空曲线）
- [ ] 模板：字号 ≥12pt；页脚/页码存在且来源唯一；外部模板母版未被动过
- [ ] 备注：每页演讲者备注含讲解+证据；证据脚注每页存在
- [ ] 导出：deck.pptx 可重新打开；preview/*.png 与 preview.pdf 存在
- [ ] 契约：`check_contract.py` valid=true；output_contract 字段全部镜像
- [ ] 记录：changelog.jsonl 有本次运行记录；manifest.json 含全部产物 sha256
- [ ] 诚实：status 与列出的每一项 uncertainty 一一对应，无隐瞒

## 7. 诚实性红线（违反即失败）

1. 不编造：材料里没有的数字、指标、图、结论一律不写；写了的必须能在
   `sources` 中定位。
2. 不假装：渲染/导出失败就说失败（partial/failed），不能把预览冒充
   PowerPoint 导出件。
3. 不预制答案：本 Skill 不含任何正式案例的答案；每个案例都从实际输入现算。
4. 预算纪律：64 个模型请求 / 900 秒 / 16k tokens 内完成；脚本本身 <60 秒，
   预留时间给材料阅读与讲稿微调；先存部分产物再增量改进。

## 8. 版本与复用

- 脚本自定位，模板与材料分离：换模板不改代码（改 `templates/*.json` 或提供
  `template_pptx`）；换材料不改模板。
- 参考文档：`references/OUTPUT_CONTRACT.md`（result.json 契约）、
  `references/TEMPLATE_SPEC.md`（模板约束）、`references/RUBRIC_MAP.md`
  （五维评分覆盖对照）；`examples/` 为最小示例（示例，非正式案例）。