# failure-modes.md — 失败模式与处置对照表（v2）

覆盖材料异常 / 模板异常 / 布局溢出 / 导出失败 / 契约与状态一致性等场景。
每项给出：**识别 → 处置 → 记录位置 → 对应决策规则 D#**。与 `SKILL.md` §5
决策规则配套；被降级的任何步骤必须把"发生了什么 + 影响"写进
`uncertainty` / `change_records`，并在最终回复中说明限制。

## 1. 输入与材料异常

| # | 失败模式 | 识别 | 处置 | 记录 | D |
|-|-|-|-|-|-|
| F01 | case.json 缺失/不可解析 | JSON 读取异常 | 立即失败（exit 1），不产半成品冒充成功 | stderr | D1 |
| F02 | 材料文件缺失 | `_locate` 找不到 | 以 case.json 结构化字段继续；缺失源进 uncertainty，**绝不编造** | `uncertainty` + `sources` | D2 |
| F03 | 材料不可读（二进制/编码） | read_text 抛异常 | 仅登记来源（不假装已读内容），内容从 case.json 抽取 | `sources.note` | D2 |
| F04 | 材料为扫描件/无文本层 | 抽取文本为空 | 不 OCR 冒充；如实标注，有图仍可引用 | `uncertainty` + `sources` | D3 |
| F05 | 数值无来源 | 材料中找不到 `file:line` | 不上页面，进 `uncertainty`（key_numbers/claims 只在有 loc 时上页） | `uncertainty` | D2 |

## 2. 模板异常

| # | 失败模式 | 识别 | 处置 | 记录 | D |
|-|-|-|-|-|-|
| F06 | 模板缺失 | 路径不存在 | 回退链 case→starting deck→**运行时生成的内置回退模板**（`make_template.ensure_builtin()`）；回退与生成原因都记录 | `template_audit.template_errors` / `opened_from` + `uncertainty` | D6 |
| F07 | 模板损坏/加密/打不开 | open 抛异常 | 记错误并回退下一级 | `template_errors` | D6 |
| F08 | 全链模板失败 | 三个候选全抛异常（含内置模板生成失败） | **失败并写 status=failed 的 result.json**，不静默用默认样式冒充已套用；生成失败只返回原因字符串，不抛栈 | result.json(status=failed) + `uncertainty` | D6 |
| F09 | 版式缺所需占位符 | `layout_provides` 缺 title/subtitle/body | 手绘文本框按页计划几何落位，记录 fallback | `layout_fallback_used` + `adopt_plan.layout_gaps` | D6 |
| F10 | 方案↔执行不一致 | 推荐版式在阶段二不可用 | best-fit 替代并逐条记录 | `template_audit.adopt_plan_deviations` | D7 |
| F11 | 主题读失败 | theme1.xml 不可读 | 主题记录仅填 error，不影响构建 | `theme.error` | D7 |

## 3. 布局与内容异常

| # | 失败模式 | 识别 | 处置 | 记录 | D |
|-|-|-|-|-|-|
| F12 | 文本框溢出 | 字号阶梯落到 12pt 仍放不下 | 只报告溢出，**绝不压到不可读** | `layout.overflow` | D8 |
| F13 | 标题过长 | 单行超容器估算宽度 | 先尝试降号；仍不行就截断到容器上限并记录 | `layout.overflow` + `uncertainty` | D8 |
| F14 | 页数超目标 | planned > slide_count | deckplan 确定性裁剪（合并讨论+局限→删议程→合并结果页）；**不静默丢证据页** | `change_records` + `page_budget_met` | D9 |
| F15 | 源图缺失/嵌入失败 | `file_exists=false` 或 add_picture 抛异常 | 灰底图位占位框（图号+标题+来源保留） | `uncertainty` + `figure_adjust`(placed=false) | D5 |
| F16 | 图号不一致 | 正文引用 ∉ 图清单 | xref warn；保留原文引用，不擅改编号 | `xref.figure_refs` | D5 |

## 4. 导出与运行环境

| # | 失败模式 | 识别 | 处置 | 记录 | D |
|-|-|-|-|-|-|
| F17 | 无 LibreOffice/PPT | 未检测到可执行导出器 | **不产伪 PDF**；预览为 PIL 示意图并标注 SCHEMATIC | `render_log.json` + `preview_is_schematic` | D11 |
| F18 | 预览字体缺失 | 标准字体目录探测 + CJK 文件扫描均失败 | 回退 PIL 内置位图字体，按文件名如实记录（日志不写本机路径） | `render_log.json`（`fallback_default=true`）+ `uncertainty` | D11 |
| F19 | 保存中途失败 | prs.save 抛异常 | 先落盘已生成部分产物，报错含已写路径；写 failed result.json | stderr + `result.json(status=failed)` | D12 |
| F21 | python-pptx 缺失 | `import pptx` 失败 | 内置回退模板无法生成（模板链只剩案例模板/起始 deck）；构建阶段失败时按 D12 写出含原因的 `status=failed` result.json，不伪装成功 | `uncertainty` + `result.json(status)` | D6/D12 |
| F22 | PIL 缺失 | `import PIL` 失败 | 预览阶段失败：**不产出空 PNG 冒充成功**，记明"预览不可用"并把限制写进 result.json | `uncertainty` + `render_log.json` | D11/D12 |
| F23 | `--out` 不可写 | makedirs/open 抛异常 | 立即报错退出并说明路径；若已有部分产物则保留现场，不写半截 JSON | stderr | D12 |
| F20 | 契约字段未知/无值 | output_contract 键在 result 里没有对应值 | 已知语义的键先取**本次运行真实值**（`preview_png`/`evidence_per_slide`/`notes_per_slide`/`template_inheritance` 等，取不到才回落类型默认）；其余按声明类型给 `""` / `[]` / `{}` / `0` / `false`，**禁止 null**；PDF 类键恒 `false`（能力确实缺失） | result 顶层回显 + `verification.contract_echo_derived` | D10 |

## 5. 状态一致性纪律

- `success` 必须是"真全绿"（无 fail/warn 检查、CP3 G1–G8 全过）；
- 任何降级（模板回退、图位占位、溢出、偏差、预览示意）→ status 至少
  `partial`，且 `uncertainty`/`change_records` 逐条说明；
- `failed` 只用于"流水线未完成"（case 不可解析、无可用模板等），并仍写出
  failed result.json 不丢现场；
- 分数、白板、对照结果由组织方产生，**本 Skill 绝不编造**。
---

## 6. 降级路径与六个机制的归属（v3 补充）

本节把上文的失败模式接到 `references/MECHANISM.md` 的 M1–M6 上。**判据**：每个
降级动作都必须能回答"它在保护哪个机制"，答不上来的动作就不该存在。

| 失败模式 | 降级动作 | 守护的机制 | 判据（复跑即可验） | 记录字段 |
|-|-|-|-|-|
| F01 case 缺失/坏 JSON | 停止，`status=failed`，退出码 1 | **M2**（契约不能被伪造完成） | 用不存在的 `--case` 跑 → `status=failed` + exit 1 | stderr + `result.json(status)` |
| F02/F03/F04 材料异常 | 结构化字段继续，绝不编造 | **M3**（无来源内容不上页） | 抽查 `uncertainty` 条目与 `sources[].exists` | `uncertainty` / `sources` |
| F05 数值无定位 | 该条不上页面 | **M3** | 定位串总数下降（**正确的下降**，不该掩盖） | `uncertainty` |
| F06/F07 模板缺失/损坏 | 逐级回退，每级留痕 | **M1**（方案必须基于真实模板） | `template_errors` 条数 == 失败级数 | `template_errors` |
| F08 全链模板失败 | `status=failed` | **M2** | 不出现"用了默认样式但声称已套用" | `result.json(status)` |
| F09 版式缺占位符 | 手绘文本框 + 留痕 | **M4**（计划与实际必须对照） | `layout_fallback_used=true` 且偏差可读 | `layout_fallback_used` |
| F10 方案↔执行不一致 | best-fit + 逐条偏差 | **M4** | 篡改 `recommended_layout_idx` → `applied` 下降 + `deviations` 出现（`TEST.md` §4e） | `adopt_plan_deviations` |
| F11 主题读失败 | 只记 `theme.error` | **M1** | `theme` 里不出现推测的字体名 | `theme.error` |
| F12/F13 溢出/标题过长 | 字号地板 12pt + 报告 | —（不属六机制，属版面纪律） | `layout.overflow` 非空且字号未低于 12pt | `layout.overflow` / `font_floor` |
| F14 页数超目标 | 固定顺序裁剪，证据页最后 | **M3**（证据不能被静默牺牲） | `change_records` 里有裁剪记录且证据页仍在 | `change_records` |
| F15/F16 图缺失/图号不一致 | 灰底占位框 / xref warn | **M4**（不静默改变图号语义） | `figure_adjust.placed=false`；原文图号未被改写 | `figure_adjust` / `xref.figure_refs` |
| F17/F18 无导出后端/字体缺失 | PIL 示意图 + 按文件名记录 | **M2**（能力缺失如实披露，不谎报） | `preview_is_schematic=true`；`render_log.json` 无本机路径 | `render_log.json` |
| F20 契约键无值 | 真实值 → 类型默认，禁 `null` | **M2** | `null_placeholders=[]` 且顶层 null 个数 = 0 | `contract_echo_derived` |
| F21/F22 依赖缺失 | 写含 ImportError 原文的 failed result | **M2 / M5** | `uncertainty[0].note` 含原始异常文本 | `uncertainty` + `result.json(status)` |
| F23 `--out` 不可写 | exit 2，不写半截 JSON | **M2** | 目标目录内**没有** result.json | stderr |
| F19/F24 保存/流水线中断 | 先落盘部分产物，再写 failed result | **M2 / M6** | 已生成产物仍在；本轮不参与哈希对拍 | `result.json(status)` |

### 三个"不要做"（与 MECHANISM.md §8 的边界一致）

1. **不要为了让指标好看而隐瞒降级**：`status` 与 `uncertainty` 是配对使用的 ——
   有降级必然至少 `partial`，G8 会检查"非 `success` 必须有 `uncertainty`"。
2. **不要用推测值填字段**：主题读不到就写 `error`（F11），字体探测不到就写
   `fallback_default`（F18），**不猜测**。
3. **不要静默改变语义**：图号（F16）、版式（F10）、页数（F14）三处最容易被"顺手
   修正"，本包要求一律先记录再处置。

**维护约定**：新增失败模式时同步做三件事 —— ① 本表加行并指定守护的机制；②
`SKILL.md` §5 的降级路径速查表加行；③ 若该降级影响可测行为，更新
`references/MECHANISM.md` 对应小节的"可证伪判据"与 `TEST.md` §4 的实测记录。
