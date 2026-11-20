---
name: academic-talk-organizer
description: >
  组织学术汇报内容（学术 PPT 页面组织）：从论文/研究材料到可讲、可编辑、证据可追溯的演示文件。
  当输入包含科研论文材料、研究报告、组会/答辩/评审任务、听众与时长、页数与模板约束、讲稿或备注需求，
  关键词如 学术汇报、答辩PPT、组会汇报、slides、deck、页码规划、讲稿、备注、问答准备、听众适配、
  叙事顺序、汇报内容组织、evidence mapping、模板适配 时使用本 Skill：读真实材料 → 抽取研究问题/
  方法/结果/局限 → 按听众与时长规划页级主张、图表引用与讲解顺序 → python-pptx 生成可编辑 .pptx
  （模板适配或内置主题）→ PIL 渲染 PNG 预览 → 写含证据映射、来源与不确定性的 result.json。
  严格以真实文件为准，不臆造数据，不提交预制答案。
---

# 学术汇报内容组织（academic-talk-organizer）

面向「玻尔产品周赛 · 学术效率 · 第三期」challenge-20870c35（slides 组）。
把**已有**的论文/研究材料组织成：结构清楚、证据可追溯、可编辑、符合听众与模板约束的学术汇报产物。
本 Skill 不负责论文精读成文、写作成稿与科研绘图本身（相邻课题负责），只负责
**从已有内容材料到可讲页面的组织与交付**。

## 1. 用途与适用条件

- **适用**：平台固定 3 个案例（组会 / 答辩 / 评审类型的学术汇报内容组织），要求：
  提取研究问题-方法-结果-局限主线 → 页级主张+图表引用+讲解顺序 → 按模板生成可编辑演示文件与讲稿/备注
  → 每页保留源材料定位并检查导出渲染。
- **不适用/边界**：不承接论文精读成稿、学术写作、科研绘图素材生产；不代替用户下科学结论；
  页面内容一律取自源材料逐字引文（`quote`），不改写事实、不补造数据。
- **运行环境**：Python 3.8+，必需第三方库仅 `python-pptx` 与 `Pillow`；
  `pypdf`（或 PyPDF2）为 PDF 可选解析器，缺失时按「未解析」如实降级，不影响其余链路。
  全包无网络依赖、无 cwd 依赖（脚本全部用 `os.path.dirname(__file__)` 自定位）。

## 2. 输入与输出

### 输入（平台运行期）

| 路径 | 内容 |
|-|-|
| `/input/case.json` | 案例标识 `case_id`、`title`、`report_goal`、`audience`、`duration_min`、`slide_count`、`report_type`、`materials`（材料清单，可为 `{path,role}`）、`template`/`start_deck`（可选模板或起始演示）、`figure_files`（可选 图表引用→图片路径 映射）、`output_contract`（可选字段声明） |
| `/input/task.md` | 任务说明；可能含 output_contract 声明（fenced JSON 或字段表） |
| 材料目录 | `case.json` 中列出的文本/PDF（缺省取 `<case 目录>/materials`），类型不限：`.md/.txt/.pdf` 与图片附件 |

**必须实际读取文件内容**（`main.py` 已按真实路径读取并逐文件解析记录），
不得根据标签/文件名预设内容。`main.py` 自动发现材料目录中的 md/txt/pdf/图片。

### 输出（--out，平台运行期即 /app/output）

```
result.json            # 结构化结果：主结果 + 证据定位 + status/sources/uncertainty/change_records
talk_plan.json         # 页级计划（叙事顺序、每页主张/证据/讲稿/问答）——可编辑中间产物
evidence_map.json      # 源文件 → {用到它的页, 图表引用} 反向映射
editable_deck.pptx     # 可编辑演示文件（python-pptx；模板适配或内置主题）
previews/
  cover_preview.png    # 封面预览（PIL 模拟，如实标注）
  slide_0NN.png        # 逐页缩略图（PIL 模拟）
  preview_grid.png     # 整包缩略网格
  preview_manifest.json# 预览清单与限制说明
self_check.json        # validate_result + check_contract 双自检报告
```

## 3. 核心方法（五个突破方向的落点）

1. **报告目标**：`report_goal` 写入封面与成功标准；缺省按汇报类型给默认成功标准
   （组会=讲清进度与风险；答辩=创新点与边界、证据链；评审=结论的证据强度与适用范围）。
2. **听众**：听众描述 → `expert`/`familiar`/`lay`，决定背景/术语页占比（10%/18%/30%）
   与术语表收录（`planner.py::resolve_audience`）。
3. **叙事顺序**：每汇报类型一套「块+权重+顺序」（`templates/talk_config.json`，可编辑）：
   组会=问题—进度—方法—结果—风险—问答；答辩=…创新点边界后置；评审=结论先行。
   页数按时长×60/85s 推导，**校准到任务冻结页数**，而不是跟随论文章节长度。
4. **重点信息**：一页一主张（`claim` 逐字自源材料）+ 一句话讲稿（`one_liner`）+
   证据强度分级（含数值/统计/图表引用→strong；结果动词→medium；间接概括→weak）。
5. **问答准备**：每条局限/风险主张与每条 strong 结果各生成一条预判追问与回答要点
   （指向证据定位），收拢到 `qa` 备用页；讲稿备注含【本页主张】【证据】【讲解】【备答】。

## 4. 执行步骤（按序执行，别跳步）

> 技能根 `$SKILL_ROOT` = 包含 `SKILL.md` 的目录（平台安装后为 `/skills/weekly-skill`）。
> 所有脚本自定位，运行命令与当前 cwd 无关。

1. **读真实文件**（不要假设内容）
   - `case.json`（`case_id`/`report_goal`/`audience`/`duration_min`/`slide_count`/`report_type`/`materials`/`template`/`output_contract`）
   - `task.md`（任务约束；若声明 output_contract 逐条记录）
   - 材料目录清单（`/input` 下的文本、PDF、图片，缺省取 `<case 目录>/materials`）
2. **建工作目录并暂存中间产物**：`mkdir -p /app/work /app/output`；需要长加工时复制材料到 `/app/work`
3. **运行主流程**（一条命令完成 抽取→规划→.pptx→预览→result.json→自检）：
   ```bash
   python3 "$SKILL_ROOT/scripts/main.py" \
     --case /input/case.json \
     --task /input/task.md \
     --out /app/output
   ```
   - 案例自带模板/起始演示（`case.json` 的 `template`/`start_deck`，或目录中文件名含
     template/master/start/deck 的 .pptx，或 `--template <路径>`）：脚本用 python-pptx **打开并沿用
     其母版与版式**新增页面（模板约束不破坏）；无模板则用包内内置主题（16:9 母版+主题色+底栏）。
   - 机器无 LibreOffice/PowerPoint 时预览自动降级为 **PIL 模拟渲染**（每张 PNG 带水印，manifest 说明
     限制）；`--skip-previews` 可跳过逐页缩略图只留封面+网格。
4. **检查产物与自检**
   ```bash
   python3 "$SKILL_ROOT/scripts/validate_result.py" /app/output/result.json
   python3 "$SKILL_ROOT/scripts/check_contract.py" /app/output/result.json
   ```
   退出码 0 = 通过；`self_check.json` 已内嵌两者报告。`result.json` 中 `status=partial` 时逐条阅读
   `uncertainty` 与 `change_records`，能修则修（如补材料、传模板），不能修则如实保留。
5. **人工核对自查清单（§7）后再收尾**；按需精修 `talk_plan.json`/`talk_config.json` 后重跑。

## 5. 脚本与资源清单

| 文件 | 作用 |
|-|-|
| `scripts/main.py` | 编排器：材料解析→规划→decks→预览→result.json→自检（唯一入口） |
| `scripts/evidence.py` | 材料加载（md/txt/PDF-pypdf）与主张/证据锚点抽取 |
| `scripts/planner.py` | 页级规划：听众→背景比例、叙事顺序、一页一主张、问答预演 |
| `scripts/deck_builder.py` | python-pptx 生成/模板适配可编辑 .pptx（含讲稿备注、图占位） |
| `scripts/render.py` | PIL 模拟预览（封面/逐页/网格 + manifest） |
| `scripts/validate_result.py` | result.json 结构+文件+数字可对源 校验（可独立 CLI） |
| `scripts/check_contract.py` | output_contract 字段齐全性校验（可独立 CLI） |
| `scripts/common.py` | 共享工具：路径自定位、JSON IO、output_contract 应用 |
| `templates/talk_config.json` | 可编辑叙事规则：每类型页权重/顺序/问答模板 |
| `templates/narrative_template.md` | 叙事模板人类可读版 |
| `references/OUTPUT_CONTRACT.md` | result.json 契约（字段/类型/status 语义/复核命令） |
| `references/RUBRIC_MAP.md` | 五维评分 → 设计覆盖对照 |
| `references/METHODS.md` | 取舍逻辑与诚实降级约定 |
| `examples/` | 最小调用示例（明确标注「示例，非正式案例」） |

## 6. 异常处理

| 情形 | 处置（全部如实记录到 result.json 的 uncertainty/change_records） |
|-|-|
| 材料缺失 | `sources` 中 kind=missing；status 视影响降 `partial`；不编造其内容 |
| 材料是 PDF 且无 pypdf | 记录 parsed=false + 原因；其余材料照常，相关页证据弱化或缺失 |
| 论文缺图/图分辨率低/图文件损坏 | 页内**诚实占位框**（标注"材料未提供图片文件"），notes 提示对照原文；坏图跳过 |
| 无模板/模板路径失效 | 采用内置主题并在 artifacts.template_used/deck_mode 注明 |
| 公式/符号丢失（PDF 抽取） | quote 以抽取文本为准并注明抽取代理方式 |
| 导出/预览失败 | 非致命：仍写 result.json（status 视情况 partial），异常写入 change_records |
| 超时/预算 | 中间产物（talk_plan/editable_deck/result 草稿）尽早落盘，收尾时补 self_check；保存部分结果并说明限制 |
| 页面数字与源不一致 | `validate_result.py` 给警告；人工核对，误报（合理换算）可忽略但需说明 |

## 7. 自查清单（收尾前逐项确认）

- [ ] `result.json` 存在；`case_id` 与输入一致；`status` ∈ {completed, partial, failed}
- [ ] `output_contract` 声明字段全部出现在 result.json 顶层（`self_check.json → contract_check.valid == true`）
- [ ] 每一页（除封面/目录/问答备用页）都有 `evidence[0].locator`（L行号 · §章节）+ `quote` 原句
- [ ] 所有 `evidence.source_file` 都能在 `sources[]` 中找到（自检 errors=0）
- [ ] `editable_deck.pptx` 存在且能被打开（python-pptx 可读）；每页有讲稿备注
- [ ] 预览 PNG 存在且每张带「PIL 模拟预览」水印；`preview_manifest.json` 已说明限制
- [ ] 数字可信：页面上的数字在源材料中可定位（warnings 已审查）
- [ ] 没有预置正式答案：examples/ 仅为接口示例，平台案例从 /input 实际读取
- [ ] 文件约束：≤50 个 UTF-8 文本文件、单文件 ≤500KB、总计 ≤2MB、无符号链接（打包前用 find/du 核对）

## 8. 平台约束（Runtime contract 要点）

- 平台把本 Skill 安装到 `/skills/weekly-skill` 后在**固定 3 个案例 × 3 次复跑**上运行；
- 输入 `/input/case.json` + `task.md`；在 `/app/work` 干中间活；最终产物 `result.json` +
  可编辑源 + 渲染预览放 `/app/output`；`result.json` 必须含 output_contract 全部字段与 `case_id`；
- 诚实记录 `status/sources/uncertainty/change_records`；不编造缺失软件状态与科学数据；
- 执行预算：64 个模型请求 / 900 秒 / 每响应 16384 token（含推理）；尽早保存部分成果，渐进改进。