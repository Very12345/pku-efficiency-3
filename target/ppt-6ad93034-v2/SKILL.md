---
name: academic-ppt-builder-v2
description: 把论文/研究材料组织成结构清楚、证据可追溯、可编辑、符合模板约束的学术汇报演示稿（PPTX）。加载后按"读实际文件→抽主线与页级证据→页面蓝图与角色分配→CP2 lint→模板槽位建稿+图表绑定→预览渲染+QA→CP4 导出校验（G1–G8）→带全部 output_contract 字段的 result.json"全流程执行；支持 --edit 局部编辑与版本回退；页面数字逐一核验材料、缺失显式标注、绝不编造。Use when a task asks to generate or edit an academic presentation / slide deck from a paper or research material（组会汇报、开题与中期、答辩、项目评审、基金申请；学术PPT、slides from paper、presentation from paper），especially when /input/case.json and task.md are present and /app/output must contain the editable deck plus previews and evidence mapping.
---

# 学术 PPT 生成与编辑 Skill v2（学术效率 · ppt-6ad93034）

> 目标：把固定科研材料变成**结构清楚、证据可追溯、可编辑、符合模板约束**的
> 学术汇报产物（可打开、可播放、可编辑、可复核），并支持**多轮局部编辑与
> 版本回退**。本 Skill 不负责论文精读/文献综述、不负责可视化算法本身、
> 不负责学术写作文字润色、不负责 PPT 软件研发；它负责把材料"翻译"成页级
> 表达并保证每页数字与图表可核实。

**执行顺序（先读契约，再规划，后生成，最后验证）**：
① 读 `references/OUTPUT_CONTRACT.md`（交付什么、哪些字段必须回显、G1–G8 门）
→ ② 按 `references/DECK_SPEC.md` 页面蓝图规划页序与页级角色（写 plan.json）
→ ③ CP2 `plan_lint` 结构校验（不过按 D4 记录偏差后酌情继续）→
④ `main.py` 建稿（extract→slide_text→deck_tool→render_qa）→
⑤ CP4 校验（`selftest` 自检 + `result_tool` G1–G8 契约门）→
⑥ 按 `references/RUBRIC_MAP.md` 五维自评覆盖。

## 1. 用途与适用条件

- **适用**：给定一篇（或一份）研究材料（md/txt/html/csv/json；PDF 先抽文本），
  固定受众/时长/页数上限/模板，组织成一版带演讲备注、页级证据、渲染预览的
  可编辑 PPTX；并支持后续按指令**局部编辑**（改要点/加备注/重排页序/换图表）
  与**版本回退**。
- **适用但不限于**：组会（方法+下一步）、答辩（贡献+局限）、评审/基金
  （对齐指标+可行性）、同行（对比+复现细节）。受众通过 `spec.audience` 传入，
  影响讲稿语气（`slide_text.AUDIENCE_TONES`）。
- **边界**：材料确实缺失实验数据/图表/局限段落时，本 Skill **不臆造**，改在
  `uncertainty` 与 `unverified_claims` 中如实标注；论文图是位图且无取数数据时
  只放"诚实占位"，绝不凭空生成曲线；渲染预览明确标注"非 PowerPoint 导出"。

## 2. 输入与输出

**输入**（平台约定，本地等价目录亦可）：
- `/input/case.json`：`case_id`、`title`、`inputs{task_md, material[]}`、
  `spec{audience, duration_minutes, max_slides, template/template_pptx/starting_deck,
  style…}`、可选 `output_contract`（声明需镜像到 result.json 顶层的字段）。
- `/input/task.md`：任务说明（存在时读取）。
- `material` 指向的实际文件：正文、数据表等。**先读实际文件，不要凭文件名猜内容**
  （deck_extract.py 强制）。

**输出**（写 `/app/output`，本地等价 `--out` 目录）：
- `work/deck.pptx`（可编辑源，每页备注+证据脚注）、`work/plan.json`（页面模型，
  可编辑源）、`work/table_cache/`、`work/material_view.json`
- `work/preview/slide_*.png` + `preview/preview.pdf`（预览渲染，标注"非 PowerPoint
  导出"；输出根 `preview/` 另有一份副本）
- `result.json`（output_contract 全字段 + case_id，禁 null）、`evidence_map.md`
  + `evidence_map.json`（双形态页级证据映射）、`changelog.jsonl`、`manifest.json`、
  `logs/`

## 3. 运行环境与依赖

- Python 3.8+；依赖：`python-pptx>=0.6.21`（建稿必需）、`matplotlib>=3.5`、
  `Pillow>=9`、`numpy`（随 matplotlib）；`reportlab` 可选（缺席时 PDF 预览自动
  跳过并如实说明）。PDF 抽取任选 fitz/pypdf/PyPDF2/pdfplumber 之一，缺则按 D3。
- 全部脚本**自定位**（`os.path.dirname(__file__)`），从任何 cwd 都能运行；统一
  以**技能根目录**（含 SKILL.md 的目录）为准：
  ```bash
  python scripts/main.py --case /input/case.json --out /app/output
  ```
  若 cwd 不可控，写成 `python <技能根绝对路径>/scripts/main.py ...`。

## 4. 执行步骤（含检查点 CP1–CP4，严格遵守顺序）

### CP1 — 读实际输入（材料可读性检查点）
1. 运行 `python scripts/main.py --case /input/case.json --out /app/output`；
   脚本读 case.json 与 task.md、核对 `inputs.material` 中每个文件确实存在，
   缺失的写进 `material_warnings` 而不是跳过（D1）。
2. **PDF 材料**：环境无 fitz/pypdf/pdfplumber 时脚本会提示（D3）；这时由
   Agent 用自身读图/读文能力把原文抽取为 `/app/work/materials/*.txt` 后重跑，
   并在 `uncertainty` 记录抽取方式。
3. 材料状态进入 `material_status`（ok/partial/missing）：missing 时按 D1
   只产出元信息 result，**绝不编造 deck**。

### S1 — 抽取主线与实体关系数据
脚本自动完成并落盘 `work/material_view.json`：章节（§标题+正文）、数据表
（表头+行）、图/表提及（图N/表N/Figure N/Table N）、研究问题/摘要/方法/
结果/局限/结论定位与候选句。**数字核验**：`evidence_check.check_claim_numbers`
对每条入页主张的材料原文做匹配，找不到的数字进 `unverified_claims`（D2）。

### S2 — 页面规划（页序 + 页级叙事角色）+ **CP2 plan_lint**
`slide_text.build_plan` 按 `spec.max_slides`（3–20，默认 8）确定性分配角色：
封面 → 主线 → 〔背景/讨论/局限按页数〕 → 问题 → 方法 → 结果×n → 结论与下一步
（蓝图见 DECK_SPEC.md §1）。每页为**一个主张**服务；结果页优先由数据表驱动
（表→2 条量化主张+"数值直接取自源数据"注记），无表才回落结果段落散文。
页序、角色、主张、证据指针写入 `work/plan.json`（可编辑源）。
**CP2 检查点**：`evidence_check.plan_lint` 校验每页 role/title/要点上限/证据
规则；`{"valid": false}` 时按 **D4** 决定：先修 plan，确属案例硬约束无法满足
则继续建稿但**显式记录偏差**，状态降 partial。

### S3 — 图表绑定（数据驱动，诚实优先）
`deck_tool.bind_figures` 四态（DECK_SPEC.md §4）：
- 材料提供数值型数据表 → matplotlib **原样重绘**（标签/数值不改动，标注重绘来源）；
- 无 matplotlib 或数据非数值列或 `--no-chart` → 降级为 PPTX **原生可编辑表格**；
- 材料直接给图片文件 → 原样嵌入；
- 论文图是位图且无取数数据 → 灰框"诚实占位"，不生成假曲线（D5）。
绑定记录在 `plan.json` 与 `result.evidence`。

### S4 — 生成可编辑 PPTX（CP3）
`deck_tool.build_deck`（python-pptx）：
- 模板约束三级来源（DECK_SPEC.md §2）：`template_pptx` 沿用母版版式只填内容
  槽位；`starting_deck` 先备份到 `work/original_inputs/` 再按计划重排页面；
  无外部模板用 `templates/default.json`（case `spec.style` 可覆盖）。
- 每页：主张式标题 + 要点（≤7 条，单条 ≤90 字，字号自动收敛 ≥12pt 防溢出）
  + 图表槽 + **证据脚注**（图/表/章节） + **演讲者备注**（讲解要点 + 证据 +
  图表说明 + 溢出提示；与页面文字分离生成）。
- 保存 `work/deck.pptx`；页级构建回执写入 result（每页字号/图表细节）。
**CP3 检查点**：deck 文件存在、python-pptx 可重开、页数与 plan 一致。

### S5 — 导出渲染预览 + 渲染 QA
`render_qa.render_all`：每页一张 PNG（PIL 画布复刻标题/要点/图表/占位/页脚）+
逐页版式 PDF（reportlab，可选）。文件名与 result 均标注**"预览渲染（PIL/
reportlab），非 PowerPoint 导出"**；CJK 字体缺失、PDF 不可用等如实进
`previews.warnings`。`render_qa.qa_report` 追加每页检查（溢出估计/
CJK 字体/预览存在）到 `run_meta.render_qa`。

### S6 — 写 result.json、双形态证据映射与记录
`result_tool.build_result` 一次写出：`case_id` + `deck`（slide_count、逐页
index/role/title/claims/evidence/figure/notes）+ `evidence`（map、
unverified_claims、material_warnings）+ `previews` + `sources[].sha256` +
`uncertainty` + `change_records` + `status` + `environment`（实测库版本）+
`run_meta`（checkpoints 等），并按 `case.json.output_contract` 声明的字段镜像
到顶层（**四形态容器默认值，禁止 null**，D10）。同时生成 `evidence_map.md`
（人读）+ `evidence_map.json`（机器读，双形态同源）、`changelog.jsonl`、
`manifest.json`（全部产物 sha256，支撑他人独立复核与复跑）。

### CP4 — 导出校验（交付门）
```bash
python scripts/result_tool.py --result /app/output/result.json \
    --out-dir /app/output --case /input/case.json \
    --envelope templates/result_envelope.json
# {"valid": true} 且 exit 0 才算通过（G1–G8，见 OUTPUT_CONTRACT.md §8）
python scripts/selftest.py --out /app/output --case /input/case.json
# all_pass=true
```
再核对：PPTX 可重新打开、页数与 plan 一致；每页有备注与证据脚注；预览
PNG/PDF 存在；`unverified_claims` 与 `uncertainty` 逐条有解释，不为 0 而假装
干净。所有检查点进入 `run_meta.checkpoints`。

### S7 — 增量编辑（演示稿迭代，可选但推荐）
多轮修改不推翻整稿：手写一个编辑 JSON（字段见 `examples/edit_demo.json`，
操作目录见 `references/EDIT_OPS.md`）：
```bash
python scripts/main.py --case /input/case.json --out /app/output \
    --edit edits.json --version v2
```
支持 `update_bullet / add_bullet / remove_bullet / add_note / retitle /
reorder_pages / set_figure`。每次修改在 `changelog.jsonl` 记一条
`{version, op, page, target, reason}`，`deck_v2.pptx` 与 `deck.pptx` 并存、
`plan.json` 更新——改坏了回退 = 复制旧版本重跑。**所有改动不得引入材料外数字**
（编辑链路同样过数字核验，D5/D11）。

## 5. 决策规则（D1–D12）

| # | 情形 | 决策（做什么 | 记录在哪） |
|-|-|-|-|
| D1 | 材料缺失/路径不存在 | 不补造；仅产出元信息 result，deck 不构建 | status=partial/failed；material_warnings |
| D2 | 主张里的数字材料中找不到 | 该主张 verified=false 入 unverified_claims，不当作正确数据 | evidence.unverified_claims |
| D3 | PDF 无文本层/无抽取库 | 不 OCR 冒充；Agent 抽文本到 work/materials/*.txt 后重跑，仍不行则 partial | uncertainty + sources.tool |
| D4 | CP2 plan_lint 有偏差 | 先修 plan；确属案例硬约束 → 构建继续但显式记录偏差，状态降 partial | run_meta.spec_lint + uncertainty |
| D5 | 论文图是位图且无数据 | placeholder 灰框占位，不生成假曲线 | plan.json figure.note |
| D6 | 模板损坏/占位符不足/打不开 | 备份原文件、改内置默认模板，说明降级 | uncertainty + change_records |
| D7 | 页数超限/槽位不足 | 按 max_slides 确定性压缩（角色分配器），不静默丢证据页，并记录 | change_records + notes |
| D8 | 字体缺失 / 导出渲染不可用 | PPTX 只记字体名由打开端替换；预览回落 default 并预警；PDF 不可用跳过说明 | previews.warnings + uncertainty |
| D9 | 图表重绘失败（无 matplotlib 等） | 降级 PPTX 原生可编辑表格，保留引用 | figure.note + uncertainty |
| D10 | 契约字段未知/无值 | 按四形态给类型对应空值 `""/[]/{}/0/false`，**禁止 null**；语义字段取真实值 | result 顶层回显 |
| D11 | 编辑操作非法（页码不存在/未知 op/非置换页序） | 跳过并记 uncertainty，其余 ops 照常应用 | uncertainty + changelog skipped |
| D12 | 预算/时间压力 | 先存部分产物（partial result）再增量改进；脚本 <60 秒，把模型预算留给材料阅读与讲稿微调 | status=partial + change_records |

## 6. 异常处理表（与 D 规则配套）

| 异常 | 识别 | 处置 | 记录 |
|-|-|-|-|
| 材料文件缺失 | case 指向的文件不存在 | D1 | material_warnings |
| PDF 无法抽文本 | 抽取为空/无库 | D3 | uncertainty + sources.tool |
| 主张数字不可核 | check_claim_numbers 缺 token | D2 | evidence.unverified_claims |
| 位图无数据 | 材料图无表格 | D5 | figure.note="诚实占位" |
| 图表重绘失败 | matplotlib 异常/缺列 | D9 | figure.note + uncertainty |
| 页数超限 | plan > max_slides | D7 | change_records |
| 模板/起始稿打不开 | open 失败 | D6 | uncertainty + change_records |
| 字体缺失 | 预览字体回落 default | D8 | previews.warnings |
| 预览/PDF 失败 | render 异常 | D8 | previews.warnings + status=partial |
| 编辑未应用 | 非法 op/页码 | D11 | uncertainty + changelog |
| 任意步骤抛错 | except 分支 | 尽量产出部分结果，绝不假装成功 | status: success/partial/failed |

**材料缺失、无法判断、运行失败必须分开说明**（分别在 material_warnings /
uncertainty / status 中），三者的处理规则不同。

## 7. 自查清单（收尾逐项打勾）

- [ ] 前置：已读 /input/case.json + task.md + 全部实际材料文件（CP1）
- [ ] 页面：页数=spec.max_slides（或更少且原因已记录）；每页有 index/role/title
- [ ] CP2：plan_lint 通过或有偏差且已记录（D4）；蓝图按 DECK_SPEC §1
- [ ] 内容：每页主张 ≤7 条、单条 ≤90 字、标题 ≤60 字；无整段摘要塞页
- [ ] 数字：页面上每个数字都能指回材料（unverified_claims 为空或有解释）
- [ ] 图表：chart_image/table/embedded/placeholder 四态均真实（无凭空曲线）
- [ ] 模板：字号 ≥12pt；页脚/页码存在且来源唯一；外部模板母版未被动过
- [ ] 备注：每页演讲者备注含讲解+证据；证据脚注每页存在
- [ ] 导出：deck.pptx 可重新打开；preview/*.png 与 preview.pdf 存在
- [ ] CP4：`result_tool.py` 输出 valid=true 且 exit 0（G1–G8 全过）；
      `selftest.py` all_pass=true
- [ ] 契约：output_contract 字段全部镜像、无 null；result.json 符合
      templates/result_envelope.json（G8）
- [ ] 记录：changelog.jsonl 有本次运行记录；manifest.json 含全部产物 sha256
- [ ] 诚实：status 与列出的每一项 uncertainty 一一对应，无隐瞒

## 8. 诚实性红线（违反即失败）

1. 不编造：材料里没有的数字、指标、图、结论一律不写；写了的必须能在
   `sources` 中定位（编辑链路同样生效）。
2. 不假装：渲染/导出失败就说失败（partial/failed），不能把预览冒充
   PowerPoint 导出件；不把"自检通过"当"内容正确"。
3. 不预制答案：本 Skill 不含任何正式案例的答案；每个案例都从实际输入现算；
   `examples/` 仅为接口示意（标注"示例，非正式案例"）。
4. 预算纪律：64 个模型请求 / 900 秒 / 16k tokens 内完成；脚本本身 <60 秒，
   预留时间给材料阅读与讲稿微调；先存部分产物再增量改进。

## 9. 版本与复用

- 脚本自定位（`os.path.dirname(__file__)`），四层职责：**extract**
  （deck_extract）/ **build**（slide_text + deck_tool）/ **render**
  （render_qa）/ **verify**（evidence_check + result_tool + selftest）+ 编排
  main.py，对齐高分包 deck_tool/result_tool/evidence_check/render_qa/selftest/
  slide_text 分工；
- 模板与材料分离：换模板不改代码（改 `templates/*.json` 或提供
  `template_pptx`）；换材料不改模板；结果信封（templates/result_envelope.json）
  与契约文档可被任何验证器复用；
- 参考文档：`references/OUTPUT_CONTRACT.md`（result.json 契约 + G1–G8）、
  `references/DECK_SPEC.md`（页面蓝图+模板约束）、`references/EDIT_OPS.md`
  （编辑操作目录）、`references/RUBRIC_MAP.md`（五维评分覆盖对照）；
  `examples/` 为最小示例（示例，非正式案例）。