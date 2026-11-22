# COMPARE.md — 对照方案（基础做法 vs 加载本 Skill）与可判定差异点

本文件回答「使用增益 25 分」最容易被扣的那一问：**增益怎么被公平地证明**。

> **本包的对照分成两层**：本文件给"哪种做法更可判定"的机制层口径；
> 可复跑的**指标定义、复跑命令与实测数字**（含不利于本包的两项）见
> [`references/GAIN-PROTOCOL.md`](references/GAIN-PROTOCOL.md)，
> 原始记录见 [`references/gain-run-record.json`](references/gain-run-record.json)。
> 两者一致：本文件不作任何量化宣称，量化一律以协议与原始记录为准。

题面写明：*平台固定运行 3 个案例，比较不加载 Skill 与加载参赛 Skill 时的实际结果；
需要相对比较的评分项使用组织方预先固定的白板。* 因此：

- **对照由平台执行**：参赛者不自造白板、不自报分数、不伪造提升百分比；
- 参赛者要做的是 ① 把"加载后"的做法写成**可复跑、可核验**的形式，
  ② 把**比较口径**写清楚，让评审能用同一输入复现 A/B。

> 本文件**不声称任何本地测得的"提升百分比"**。本机没有平台的基础 Agent 条件，
> 编造增益数字属于题面明令禁止的"文字自述替代实际运行证据"。
> 下表列的是**可机器判定的差异点**与**判定命令**，评审在固定 3 案例上各跑一次即可得结论。

## 1. 两种条件的做法差异（同输入、同案例版本、同导出参数）

| 环节 | 基准做法（不加载 Skill 的基础 Agent） | 加载本 Skill 后 | 差异是否可机器判定 |
|-|-|-|-|
| 材料盘点 | 常按文件名/标签假设内容，或跳过盘点直接写页 | CP1：按真实路径读取每个材料，逐文件记 `parsed/char_count/sections`；缺失记 `kind=missing` | ✅ `result.json.sources[]` + `change_records` 的 material 记录 |
| 页数与时长的关系 | 页数按材料长度堆出来，与"20 分钟/12 页"脱节 | 页预算由 `templates/talk_config.json`（听众×时长）推导并**校准到任务冻结页数**（P3 门） | ✅ `plan_gates.gates[P3] pages=<N> target=<N>`；`slide_count` |
| 叙事顺序 | 按论文目录逐节搬运 | 每汇报类型一套"块+权重+顺序"（组会/答辩/评审），背景比例按听众先验调整（10/18/30%） | ✅ `talk_plan.json.narrative.order_blocks` 与 `audience.background_ratio`；三套配置可 diff |
| 逐页主张 | 每页多段文字，无唯一结论 | **一页一主张**（`claim` 逐字取自源材料）+ 一句话讲稿（`one_liner`）+ 证据强度分级 | ✅ `pages[].claim/one_liner/strength`；`validate_result` 检查每页 claim 非空 |
| 图表引用 | 图号与页内结论常不对应，或引用不存在的图 | `figure_ref` 从材料逐字抽取；有图片文件则**真的嵌入** deck，无则页内**诚实占位框**并记录 | ✅ `pages[].figure_ref/figure_file`、`deck_builder` 的 `figure_inserted`、`evidence_audit` 的 `figure_bound` |
| 证据可追溯 | 无法回溯"这句话从哪来" | 每页 `evidence{source_file, section, line_no, locator, quote, strength}`；行号落在章节区间内 | ✅ `evidence_audit`：`content_pages/ok_pages/errors`，逐页 `line_ok` |
| 引文保真 | 常出现"改写事实"或凭印象写数字 | 引文逐字比对实际读取的源文本；数字不在源文本逐字出现 → 警告级列出 | ✅ `evidence_audit.entries[]` 的逐页 `notes`、`validate_result` 的数字警告 |
| 问答准备 | 无，或与页面重复 | 每条局限/风险主张与每条 strong 结果各生成预判追问 + 回答要点，收拢到 `qa` 备用页 | ✅ `pages[]` 中 `block=qa` 的 `qa[]{question, answer_points}`；每页备注【备答】 |
| 讲稿/备注 | 备注缺失或与页面文字重复 | 每页备注 = 【本页主张】【证据】【讲解】【备答】四段 | ✅ `verify_deck` 的 `notes_nonempty`（逐页） |
| 模板约束 | 直接新建 deck，或用图替代模板 | 有模板/起始演示 → 沿用其**母版与版式**；自带示例页丢弃以免页数超出冻结值 | ✅ `artifacts.deck_mode{mode,template_slides_present,template_slides_dropped}` |
| 导出与渲染 | 只有 .pptx，无任何渲染检查 | PIL 模拟预览（带水印 + `preview_manifest.json` 说明限制）+ 逐页布局可查 | ✅ `artifacts.previews`、`preview_manifest.json` |
| 可编辑性 | 元素名随机，人难以定位 | 确定性元素命名 `page-claim-NN`/`page-figure-NN`/`page-footer-NN`；deck 侧校验 | ✅ `deck_audit` 的 `claim_element`/`figure_element`、`verify_deck` 退出码 |
| 失败处置 | 静默失败或直接崩 | 材料缺失/PDF 无解析器/无模板/缺依赖/预览失败/计划门未过 —— 全部有分支并写 `uncertainty`+`change_records` | ✅ 同一命令在不同依赖条件下的 `status` 与 `uncertainty`（见 `TEST.md` T8–T13） |
| 可复跑性 | 依赖交互式会话，无法复现同一份产物 | 同输入同参数：内容投影 sha 相同、PNG 逐字节相同 | ✅ `self_check.determinism` + `selftest.py` 的 `determinism_probe` |
| 结果形态 | 常常只有自由文本，字段随缘 | `result.json` 契约化（缺失字段按类型初始化，禁 null），`check_contract.py` 自动核对 | ✅ `check_contract.py` 退出码 0 与 `contract_check.missing_required=[]` |

## 2. A/B 比较口径（建议评审按此执行，双方条件完全对等）

| 项 | 规定 |
|-|-|
| 输入 | 平台固定案例的 `/input/case.json`、`/input/task.md` 与材料，**同一份、同一版本** |
| 条件 A | 基础 Agent 按同一任务说明直接产出汇报材料与结果 |
| 条件 B | 基础 Agent + 本 Skill（`SKILL.md` §4 的 CP1–CP5 流程；命令见 §4） |
| 判定 1：内容正确性 | 页面 `claim`/数字/图号能否在源材料逐字定位（`evidence_audit` 逐页 `quote_found` 与 `numbers_not_in_source`） |
| 判定 2：结构完整性 | 冻结页数、主线四要素（问题/方法/结果/局限）、每页主张与讲稿、问答备用页是否齐备 |
| 判定 3：可编辑与渲染 | 可编辑 `.pptx` 是否可打开、元素是否命名可定位、是否有可检查的渲染预览与字体/模板记录 |
| 判定 4：效率 | 从输入到可交付材料的**命令数/返工轮次**（本包为一条命令；返工=改 `talk_plan.json`/`talk_config.json` 后重跑） |
| 判定 5：失败可见性 | 材料异常/依赖缺失时，产物与 `uncertainty` 是否如实说明限制（不得静默降级或编造） |
| 复跑 | 条件 B 的产物可用 `selftest.py` 复核确定性与包约束；条件 A 同样输入重复一次以示公平 |

## 3. 为什么这不是"自说自话"

- 上表每一行的"是否可机器判定"列都指向**本包脚本自己产出、且可由第三方脚本复核**的结构化字段；
- `TEST.md` 给出本机真实运行的命令、退出码与观测值（含**负例**：缺依赖/缺材料时降到 `partial`）；
- 本包不提交任何预制答案：`examples/` 只是自拟的合成接口示例，正式案例由平台在运行期提供
  （`examples/README.md` 已声明，`result.json` 的 `case_id` 也不冒充正式案例）。

## 4. 已知不利于本包的对照结果（如实写明）

- **预览不是 Office 真实栅格化**：`previews/*.png` 是 Pillow 模拟渲染，字体与版式与 PowerPoint 打开效果存在差异，
  故"导出渲染"一项只证明"布局可检查"，不证明"与 Office 逐像素一致"；
- **模板适配只保证母版/版式与页数约束**：起始演示文件里原有的示例页会被丢弃（记入 `change_records`），
  若某案例要求"在自带页面上就地改写"，本包当前不读取起始 deck 的既有文字，需要用材料文本重建该页；
- **证据定位是行级/章节级近似锚点**：源材料更新后行号可能偏移，需按引文原文复核。
