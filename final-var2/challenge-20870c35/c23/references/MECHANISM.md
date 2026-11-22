# MECHANISM.md — 本包的独特机制，以及"没有它会怎样"

本文件回答"创新增益"真正被问的那一问：**本包相对常规做法，多了什么别人不容易稳定复现的东西？**
每个机制按四段写：**机制 → 落点（文件 + 运行时字段）→ 没有它会怎样（具体退化现象 + 本包实测证据）
→ 可证伪判据（第三方能推翻它的检查）**。

> 实测证据全部来自本包跑过的对照与降级用例：
> `references/GAIN-PROTOCOL.md` §6、`references/gain-run-record.json`、`TEST.md`。
> 数字不是估算值，可逐项复跑核对。

## 0. 一句话定位

常规做法是"**读材料 → 直接写页**"；本包是"**定契约 → 排页 → 生成 → 审证据 → 收口**"，
每一环都产出**别人可以独立复算的机器可读记录**。所谓机制，就是这条链上不可省略的那几环。

## 1. M1 计划契约门先行（plan-before-build）

- **机制**：先产出页级计划（`talk_plan.json`），再用 `assets/plan.schema.json` 驱动的 P1–P8
  机器门校验它（页数是否等于冻结值、每页是否有主张与证据定位、强度词法是否合法……），
  **通过了才生成 deck**；未通过也不中断，而是产出诚实的降级结果。
- **落点**：`scripts/scaffold_plan.py`（计划）、`scripts/validate_plan.py`（门）、
  `assets/plan.schema.json`（单点真相）、`result.json` 的 `plan_gates` / `audit.plan_gates`
  与 `summary.pages_total`、`pages[].claim/one_liner/strength/evidence`。
- **没有它会怎样**：页数会跟着**材料长度**走，而不是跟着**时长与冻结要求**走。
  本包实测：基础形态臂（A 臂）按"每页 5 段"只排出 **3 页**，与冻结 12 页相差 9 页，
  必须人工返工一轮才能对齐（`gain-run-record.json.arms.A.pages_before_rework = 3`、
  `rerun_rounds_to_frozen = 2`）；本包臂（B 臂）首轮即 12 页、0 返工。
  没有计划门，"页数对不对"只能靠人眼数。
- **可证伪判据**：`python "$SKILL_DIR/scripts/validate_plan.py" <out>/talk_plan.json
  --materials-dir <材料目录>` 退出码应为 0；`plan_gates.gates[P3].pages` 应等于 `target`。
  若把 `case.slide_count` 改成 7 而不改计划，P3 必须报错——报不出即为门失效。

## 2. M2 逐字证据审计（evidence-audit-before-delivery）

- **机制**：交付前对**每一页**的主张/引文做逐字比对——`quote` 必须真的出现在**实际读取**的源文本中，
  行号要落在该文件的章节区间内，页面上的数字若在源文本中找不到就列为警告；
  由框架概括而成的页面必须标 `derived=true` 并把强度降到 `weak`。
- **落点**：`scripts/evidence_audit.py`、`evidence_audit.json`（逐页 entries + summary）、
  `evidence_map.json`（源文件 → 用到它的页与图表引用）、`result.audit.evidence`、
  `pages[].evidence{source_file,section,line_no,locator,quote,strength}`。
- **没有它会怎样**：页面上的论断无法回溯"从哪来"，改写事实与凭印象写数字都不会被发现。
  本包实测：B 臂 12 页中内容页 10 页、`ok_pages=10`、`errors=0`、`unavailable_text=0`，
  且 `evidence.source_file` 无孤儿引用（全部落在 `sources[]` 中）；
  对照的 A 臂**没有任何定位字段**，第三方只能逐字读它的 slide 才能猜出处。
- **可证伪判据**：把 `result.json` 里某页 `quote` 改成源文本中不存在的句子后重跑
  `evidence_audit.py <out>/result.json`，必须失败（退出码非 0 / `errors>0`）。
  若仍报 valid，则审计是恒真脚本。

## 3. M3 叙事配置化：同一份材料，按听众与时长换页序

- **机制**：每类汇报（组会/答辩/评审）是一套可编辑的"块 + 权重 + 顺序"配置；
  听众描述映射到背景比例（专家 10% / 熟悉 18% / 非专业 30%）；页预算由时长推导后
  **校准到任务冻结页数**。改配置即改行为，不必改代码。
- **落点**：`templates/talk_config.json`、`templates/narrative_template.md`、
  `scripts/scaffold_plan.py::resolve_audience`、`result.json` 的
  `audience{expertise,background_ratio,evidence_depth}` 与 `summary.narrative_order`。
- **没有它会怎样**：同一套页序应付所有场合——组会讲不出进度与风险，答辩讲不出创新点边界。
  常规做法里"听众适配"通常只写在提示词里，**不落字段**，因此无法被复核。
- **可证伪判据**：同一份材料把 `report_type` 在 `group_meeting` / `defense` / `review` 之间切换，
  `talk_plan.json` 的 `narrative.order_blocks` 与 `audience.background_ratio` 必须随之变化；
  若三者产物完全一致，说明配置没有生效。

## 4. M4 问答预演与备用页

- **机制**：每条局限/风险主张与每条 `strong` 结果各生成一条预判追问与回答要点（指向证据定位），
  收拢到 `qa` 备用页；每页讲稿备注固定为【本页主张】【证据】【讲解】【备答】四段。
- **落点**：`scripts/scaffold_plan.py` 的问答库构建、`pages[].qa[]{question,answer_points}`、
  deck 的 speaker notes（由 `deck_audit.slides[].notes_nonempty` 逐页核验）。
- **没有它会怎样**：被追问时没有准备，备注缺失或与页面文字重复。
  本包实测：B 臂讲稿覆盖率 **1.0**、问答条目 **4** 条；A 臂讲稿覆盖率 **0.0**、问答 **0** 条。
- **可证伪判据**：`deck_audit.slides[].notes_nonempty` 应逐页为 true；
  `Σ len(pages[].qa)` 应 ≥ 局限/风险页数 + strong 结果页数的较小者。

## 5. M5 模板适配：沿用母版版式，但不让模板自带页破坏冻结页数

- **机制**：案例给了模板/起始演示就**沿用它的母版与版式**，同时**丢弃它自带的示例页**、
  按冻结计划重建整份 deck；每个由本 Skill 创建的元素带确定性命名
  （`page-claim-NN` / `page-figure-NN` / `page-footer-NN`），使"这一页的主张在哪里"可被机器定位。
- **落点**：`scripts/deck_builder.py::build_deck`、`artifacts.deck_mode{mode,template_slides_present,
  template_slides_dropped}`、`artifacts.template_used`、`deck_audit` 的 `claim_element`/`figure_element`。
- **没有它会怎样**：两条典型退化——① 直接新建 deck，完全丢掉组织方的模板约束；
  ② 保留模板自带页，导致最终页数 = 冻结页数 + 自带页数（页数不符是评审一眼能看出的硬伤）。
  本包实测（`TEST.md`）：带 1 张自带页的模板 → `template_slides_present=1 / dropped=1`，
  最终 12 张幻灯片 == 冻结 12 页。
- **可证伪判据**：`python "$SKILL_DIR/scripts/verify_deck.py" <out>/editable_deck.pptx
  --expect-pages <N> --plan <out>/talk_plan.json` 退出码 0，且 `deck_audit.slides` 长度 == N。

## 6. M6 契约四形态回显 + 状态可见性（禁 null、禁静默降级、禁虚报）

- **机制**：案例/题面声明的 `output_contract` 字段**只增不减**地注入顶层，缺失时按容器类型
  初始化为 `""` / `[]` / `{}` / `0` / `False`（**永不 null**）；同时任何降级必须在
  `status` + `uncertainty` + `change_records` 三处留痕。
- **落点**：`scripts/common.py::apply_contract`、`scripts/check_contract.py`、
  `result.json.contract{declared_source,applied}`、`self_check.contract_check`、
  `artifacts.deck_limitation`、`references/failure-modes.md` 的"状态一致性规则"。
- **没有它会怎样**：字段缺失→下游解析崩；`null` 冒充空值→判分器把它当未产出；
  静默降级→"看起来完成了"。本包实测（降级用例）：遮蔽 `python-pptx` 后
  `status=partial`、`editable_deck=null`、`deck_limitation` 有值、`uncertainty` 4 条，
  而**命令仍返回 0**、页计划与预览照常——把"缺什么"说清楚，而不是崩掉或假装成功。
- **可证伪判据**：`check_contract.py` 报 `missing_required=[] wrong_type=[]`；
  且 `result.json` 顶层不存在 `null` 值；对任一降级运行，`uncertainty` 条目必须三要素齐全。

## 7. M7 运行时文本化资源（包内零二进制）

- **机制**：提交资源只保留 UTF-8 文本；示例 PDF/PNG/模板改由脚本在运行期生成
  （零第三方依赖的最小 PDF + 纯几何示意图），字体改为运行时按候选路径探测，
  产物写盘前把本机绝对路径改写成相对形式。
- **落点**：`scripts/make_synthetic_inputs.py`、`scripts/common.py::portable_path/sanitize_output`、
  `scripts/render.py::font_status`、`examples/EXPECTED-OUTPUT.md`（用文字替代随包二进制产物）。
- **没有它会怎样**：包会因为**二进制资源**或**文件数超限**在平台预检被直接拒收
  （题面硬门：≤50 个 UTF-8 文本文件、单文件 ≤500KB、合计 ≤2MB、无符号链接）。
  本包实测：提交目录 **46 个文件、全部为允许的七种文本扩展名**、无 `__pycache__`、
  无符号链接、无本机绝对路径（字体候选路径除外，属跨平台探测逻辑）。
- **可证伪判据**：`python "$SKILL_DIR/scripts/selftest.py" <out> --package-check "$SKILL_DIR"`
  的 `package_constraints` 段应 `errors=[]`；提交目录内 `grep` 盘符形式绝对路径应无命中。

## 8. M8 确定性探针（同输入可重跑）

- **机制**：对计划与证据映射做"**剔除记录性时间戳**的内容投影 sha"，并记录 deck 的规范化 sha；
  双跑后可逐项比对，把"确定性"从形容词变成可核对的三个哈希。
- **落点**：`scripts/common.py::deterministic_sha`、`finalize_result.py`、
  `self_check.determinism{plan_sha16,evidence_map_sha16,deck_pptx_normalized_sha16}`、
  `selftest.py` 的 `determinism_probe`。
- **没有它会怎样**：无法区分"内容变了"与"只是时间戳变了"，评审无法复现同一份产物，
  "可复跑"就只是口号。本包实测（双跑）：`evidence_map/plan_gates/deck_audit/evidence_audit`
  逐字节相同、12 张 PNG 逐字节相同、三个投影 sha 相同，差异只在 `generated_at` 一类记录性字段。
- **可证伪判据**：同一条命令跑两次，`self_check.determinism` 的三个 sha 应逐位相同；
  `selftest.py` 的 `determinism_probe` 检查应为 ok。

## 9. 机制组合效应：去掉一环会连锁失效

| 去掉的机制 | 直接后果 | 连锁后果 |
|-|-|-|
| M1 计划门 | 页数随材料长度漂移（实测首轮 3 vs 冻结 12） | M2 无稳定的页面主张可审；M8 的投影 sha 失去意义 |
| M2 证据审计 | 引文是否逐字命中不可知 | M6 的 `status` 失去降级依据；评审只能信任文字 |
| M3 叙事配置 | 页序与听众无关 | M1 的 P 门里"块顺序/比例"条款形同虚设 |
| M4 问答预演 | 备注与备用页消失（实测覆盖率 1.0 → 0.0） | 实际效果中的"问答准备"整块缺失 |
| M5 模板适配 | 页数被模板自带页顶破 | M1 的 P3 门与 M5 的自带页丢弃必须成对存在 |
| M6 契约与状态 | 字段缺失/静默降级 | 平台侧无法解析结果；降级被误当成功 |
| M7 文本化资源 | 预检拒收（二进制/超限） | 整包 0 分，与算法质量无关 |
| M8 确定性探针 | "可复跑"无法证明 | 双跑差异只能靠人眼比对 |

## 10. 与常规做法的边界（本包不做什么）

- 不做论文精读成稿、学术写作成稿、科研绘图素材生产（相邻课题负责）；
- 不判断科学结论的真伪，只保证"页面上说的能回到材料"；
- 不提供 Office 像素级渲染（预览是 PIL 示意并如实标注）；
- 不替平台做对照结论：对照装置与指标定义随包提供，**平台白板由组织方执行**。
