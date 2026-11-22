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

---

# 附录 A：失败分支 B01–B24 完整表 —— 原「决策显性化版」的 `failure-modes.md` 全文并入

> 合并说明（union 包，为守住 ≤50 文件硬门）：本附录是另一条叙述线的**全文**。
> 上半部分按 **F##**（失败模式）组织并接到六个机制上；本附录按 **B##**（失败分支）
> 组织并接到 **D1–D16** 决策规则上，末节给出 B↔D 速查。两套编号**指向同一批代码路径**，
> 内容一字未删，供不同检索习惯的读者使用。

本表是 `SKILL.md` §3 的**完整版**。设计约定：

- **分支号 B##** 是"出了什么事"的索引；**规则号 D##** 是"该怎么处置"的索引。
  两者在 `SKILL.md` §2/§3 同名出现，可互相跳转。
- 每一行给出五列：**识别信号 → 首档处置 → 末档处置（真正的降级）→ 记录字段
  （逐字路径）→ 规则号**。执行时按下表**最后一档动作**走，不要临场发明处置。
- 被降级的任何步骤都必须把"发生了什么 + 影响"写进 `uncertainty` /
  `change_records`，并在最终回复里说明限制。**状态词汇诚实**：有降级就不是
  `success`（判定表见 `SKILL.md` §2.5）。

---

## 1. 材料异常（B01–B05 · D1–D4）

| # | 分支 | 识别信号 | 首档处置 | 末档降级 | 记录字段 |
|-|-|-|-|-|-|
| **B01** | case 缺失 / 非 JSON | 读文件抛异常、`json.load` 抛 `JSONDecodeError` | 停止流水线 | 写 `status=failed` 的 result.json（`case_id`=文件名词干），退出码 **1**；**不产出冒充成功的半成品** | stderr + `result.json(status)` + `uncertainty` |
| **B02** | 材料文件不存在 | `_locate()` 找不到路径 | 改用 `case.json` 结构化字段继续 | 缺失项逐条进 uncertainty；`sources` 里仍登记该来源并标 `exists:false`；**绝不编造内容** | `uncertainty` + `sources[].exists` |
| **B03** | 材料不可读（编码错 / 二进制） | `read_text` 抛异常 | 登记来源、跳过正文 | **不假装读过内容**；内容全部退回 case 结构化字段 | `sources[].note` |
| **B04** | 扫描件 / 无文本层 | 抽取结果为空字符串 | 有图仍按图清单引用 | 如实标注"图像型材料，未做 OCR"；不引入任何编造转写 | `uncertainty` + `sources[].note` |
| **B05** | 数值/结论无 `文件:行` 定位 | 定位正则无命中 | 该条不上页面 | 进 `uncertainty`；若某页因此无任何主张 → 合并进相邻页并记 `change_records`，不保留空页 | `uncertainty` + `change_records` |

## 2. 模板与版式异常（B06–B11 · D5–D8）

| # | 分支 | 识别信号 | 首档处置 | 末档降级 | 记录字段 |
|-|-|-|-|-|-|
| **B06** | 模板路径不存在 | `case.template` 指向的文件缺失 | 回退链下一级（`starting_deck`） | 再下一级 = 运行时生成的回退模板，来源记 `opened_from=builtin` | `template_audit.template_errors` / `opened_from` |
| **B07** | 模板损坏 / 加密 / 非 pptx | `Presentation()` 抛异常 | 记录异常原文后回退下一级 | 同上；异常原文保留在 `template_errors`，便于定位是哪种损坏 | `template_audit.template_errors` |
| **B08** | 全链模板失败 | 三个候选（case 模板 / 起始 deck / 运行时回退）全失败 | 停止构建 | `status=failed` 的 result.json；**不静默改用默认样式冒充"已套用模板"** | `result.json(status=failed)` + `uncertainty` |
| **B09** | 案例未给模板也未给起始 deck | 两个字段都为空 | 运行时现场生成 16:9 回退模板（真实母版/版式/占位符） | 生成失败（无 python-pptx）→ `ensure_builtin()` 返回**原因字符串而非抛栈**，按 B08 处理 | `template_audit.opened_from=builtin` + `uncertainty` |
| **B10** | 版式缺所需占位符 | `layout_provides()` 缺 `title`/`subtitle`/`body`（`text` 类侧栏不算 body） | 按 best-fit 选替代版式 | 仍缺角色 → **手绘文本框**按页计划几何落位，记 fallback；两条路径都留痕 | `template_audit.layout_fallback_used` + `adopt_plan.layout_gaps` |
| **B11** | 推荐版式在阶段二不可用（方案↔执行不一致） | 方案里的 `recommended_layout_idx` 与实际不符 | best-fit 替代 | **逐条**记偏差，绝不静默改变；偏差条数 > 0 时状态至少 partial | `template_audit.adopt_plan_deviations` |

## 3. 内容、版式几何与图表异常（B12–B17 · D9–D12b）

| # | 分支 | 识别信号 | 首档处置 | 末档降级 | 记录字段 |
|-|-|-|-|-|-|
| **B12** | 文本框溢出 | 字号阶梯落到 12pt 仍放不下 | 沿阶梯（32→28→24→20→18→16→14→12pt）逐级下调 | **只报告，不再压字号**；页脚字号不受影响；**绝不压到不可读** | `audit.layout.overflow` + `layout.font_floor` |
| **B13** | 标题过长 | 单行估算宽度超容器 | 先降号 | 仍超 → 按容器上限截断并记录；不出现不可见的溢出文字 | `layout.overflow` + `uncertainty` |
| **B14** | 计划页数超 `slide_count` | `planned > slide_count` | 固定顺序裁剪：合并 discussion+limitations | → 删 agenda → 合并最后两张结果页；**证据页（evidence_map 附录）最后才动**，任何裁剪写 change_records | `change_records` + `page_budget_met` |
| **B15** | 源图缺失 / 嵌入抛异常 | `file_exists=false` 或 `add_picture` 抛异常 | 保留图位（图号+标题+来源照写） | **灰底图位占位框**，不伪造图形、不留空白页；状态 partial | `figure_adjust.placed=false` + `uncertainty` |
| **B16** | 正文引用图号 ∉ 图清单 | 交叉引用校验失败 | 记 xref warn | **保留原文引用不擅改编号**；若图清单本身为空 → 正文图号降级为文字描述 | `audit.xref.figure_refs` |
| **B17** | 嵌入图宽高比 ≠ 源图（容差 1e-3） | 实测 `w/h` 与源图不一致 | 重算 contain-fit 后重放 | 仍异常 → 按原图比例锁定并记录 | `template_audit.figure_adjust` |

## 4. 环境、依赖与交付异常（B18–B24 · D13–D16）

| # | 分支 | 识别信号 | 首档处置 | 末档降级 | 记录字段 |
|-|-|-|-|-|-|
| **B18** | 无 LibreOffice / PowerPoint | 探测不到可执行导出器 | 预览改走 PIL 路径 | 封面 + 全册联系表，文件名含 `schematic`，图内叠加免责声明；**不产伪 PDF** | `render_log.json` + `preview_is_schematic=true` |
| **B19** | 预览字体缺失 | 标准字体目录探测 + CJK 文件扫描均未命中 | 回退 PIL 内置位图字体 | 按**字体文件名/索引**记录；日志里**不写本机路径** | `render_log.json`（`fallback_default=true`） |
| **B20** | 契约键在本 Skill 里无天然对应值 | 键在 result 里没有对应值 | 已知语义的键先取**本次运行真实值**（`preview_png` / `evidence_per_slide` / `notes_per_slide` / `template_inheritance` / `slide_count` / `audience` / `language`） | 其余按声明容器类型给 `""` / `[]` / `{}` / `0` / `false`；**禁止 `null`**；PDF 导出类键恒 `false` | result 顶层 + `verification.contract_echo_derived` |
| **B21** | python-pptx 缺失 | `import pptx` 失败 | 模板链退化为"案例模板 / 起始 deck" | 构建阶段失败 → 写含 `ImportError` 原文的 `status=failed` result.json，不伪装成功 | `uncertainty` + `result.json(status)` |
| **B22** | Pillow 缺失 | `import PIL` 失败 | 预览阶段显式失败 | **不产出空 PNG 冒充成功**；"预览不可用"写进 result.json | `uncertainty` + `render_log.json` |
| **B23** | `--out` 不可写（父路径是普通文件 / 无权限） | `makedirs` / `open` 抛异常 | 立即报错并说明目标路径 | 退出码 **2**；**不写半截 JSON**；若已有部分产物则保留现场 | stderr |
| **B24** | 保存中途失败 | `prs.save` 抛异常 | 先落盘已生成的部分产物 | 报错信息包含已写路径；写 `status=failed` 的 result.json，现场不丢 | stderr + `result.json(status=failed)` |

---

## 5. 状态一致性纪律

- `success` 必须是"真全绿"：全部审计检查 `ok`、CP3 G1–G8 全过、**无任何降级
  条目**；
- 任何降级（模板回退、图位占位、方案偏差、溢出、预览示意、契约键回落）→
  状态至少 `partial`，且 `uncertainty` / `change_records` **逐条**说明；
- `failed` 只用于"流水线未完成"（B01 不可解析、B08 无可用模板、B21/B22 依赖
  缺失导致构建失败、B24 保存失败），并仍写出 failed result.json 不丢现场；
- 分数、白板、平台对照结果由组织方产生，**本 Skill 绝不编造**。

## 6. 分支 ↔ 规则 速查

| 分支区间 | 主题 | 规则区间 |
|-|-|-|
| B01–B05 | 输入与材料 | D1–D4 |
| B06–B11 | 模板与版式 | D5–D8 |
| B12–B17 | 版式几何与图表 | D9–D12b |
| B18–B24 | 环境、依赖与交付 | D13–D16 |

**维护约定**：新增决策规则时必须同步做三件事 —— ① `SKILL.md` §2 加行；
② `SKILL.md` §3 加分支；③ 本表加同号条目并给出 `result.json` 的记录字段名。
缺任何一件，规则就无法被第三方复核。

---

# 附录 C：失败模式 ↔ 实测对照 —— 原「失败注入演练版」的 `failure-modes.md` §6 全文并入

> 合并说明（union 包）：本附录把**上文每一条失败模式**接到
> `references/FAULT-MATRIX.md` 的 18 个真实场景上，并明确标出**哪些模式从未被触发过**。
> 章节号沿用原文（§6 / §6.1），内容一字未删。

## 6. 实测对照：这些失败模式真的被触发过吗（v4 · 与 `FAULT-MATRIX.md` 互链）

上文是**应该发生什么**。下表是**实际发生了什么** —— 每一行都来自
`scripts/fault_inject.py` 的一次真实运行（注入 → 起全新 `main.py` 子进程 → 读回
退出码 / `status` / `uncertainty`）。**没有场景能触发的模式，明确标"未触发"**，
不要把它当成已验证。

| 失败模式 | 触发场景（`FAULT-MATRIX.md`） | 实测退出码 | 实测 status | 与本文声明的差异 |
|-|-|-|-|-|
| **F01** case 缺失 / 不可解析 | `i01-missing-case`、`i02-garbage-case` | **1** | `failed` | 一致（`uncertainty[0].note` 含原始 `FileNotFoundError` / `JSONDecodeError` 文本） |
| **F02** 材料文件缺失 | `i03-material-missing` | 0 | `success` | 一致（`uncertainty` 3 条；页面由 `case.json` 结构化字段支撑） |
| **F03** 材料不可读（二进制/编码） | `i04-material-binary` | 0 | `success` | 一致（`sources[].note` 带原始解码错误原文） |
| **F04** 扫描件 / 无文本层 | — | — | — | **未触发**（本机造不出真实扫描件） |
| **F05** 数值无来源 | — | — | — | **未触发**（示例案例的定位齐全） |
| **F06** 模板缺失 | `t01-template-missing` | 0 | `success` | **有一处细节**：路径不存在时 `template_errors` 是 **0 条**（回退链在候选枚举阶段就跳过，不是"打开失败"） |
| **F07** 模板损坏 / 加密 | `t02-template-corrupt` | 0 | `success` | 一致（`template_errors` **1 条**——本矩阵里唯一非空的场景） |
| **F08** 全链模板失败 | — | — | — | **未触发**（需同时让内置模板生成也失败） |
| **F09** 版式缺所需占位符 | — | — | — | **未触发**（需换模板族） |
| **F10** 方案↔执行不一致 | — | — | — | **未触发**（示例案例偏差实测为 0） |
| **F11** 主题读失败 | — | — | — | **未触发** |
| **F12** 文本框溢出 | — | — | — | **未触发**（示例文本量偏小；见 `CASE-SET.md` §4.3 的相关实测） |
| **F13** 标题过长 | — | — | — | **未触发** |
| **F14** 页数超目标 | — | — | — | **未触发**（示例页数刚好；见 `CASE-SET.md` §4.1 的相关实测） |
| **F15** 源图缺失 / 嵌入失败 | `i06-figures-missing` | 0 | `success` | **有差异**：`uncertainty` 逐图记了两条，但 `status` **仍是 success**，且 `figures_embedded` 仍报 2/2 —— 见 `FAULT-MATRIX.md` §4.1 |
| **F16** 图号不一致 | — | — | — | **未触发** |
| **F17** 无 LibreOffice/PPT | 全部 18 场景 | 0 | — | 一致（`preview_is_schematic=true`，从源头上就没有伪 PDF） |
| **F18** 预览字体缺失 | — | — | — | **未触发**（本机字体探测命中） |
| **F19 / F24** 保存中途失败 | — | — | — | **未触发**（需让 `prs.save` 真的抛异常；未构造） |
| **F21** python-pptx 缺失 | `d01-no-pptx` | **1** | `failed` | 一致（`ImportError` 原文保留在 `uncertainty`） |
| **F22** Pillow 缺失 | `d02-no-pil` | **1** | `failed` | 一致（**没有产出空 PNG 冒充成功**） |
| **F23** `--out` 不可写 | `d03-out-unwritable` | **2** | （无 `result.json`） | 一致（产物目录内 **0 个文件**，不写半截 JSON） |
| **F20** 契约字段未知/无值 | 全部 18 场景 | 0 | — | 一致（顶层 `null` 个数实测 **0**） |
| （新增）宿主差异 | `d04-out-readonly` | 0 | `success` | **Windows 上 `chmod 0444` 拦不住写入**，故标 `HOST-DIFF`，不改判据 |

### 6.1 从这张表能读出的三件事

1. **覆盖是部分的。** 18 个场景验证了 **F01/F02/F03/F06/F07/F15/F17/F20/F21/F22/F23**；
   F04/F05/F08/F09/F10/F11/F12/F13/F14/F16/F18/F19/F24 **没有**被触发过。
   后者的"处置"仍只是**设计声明**，请不要把它们当成已验证行为 —— 这也是
   `SKILL.md` §4 决策规则表里逐条标注"触发场景"的原因。
2. **有一处声明与实测不符**（F15）：图缺失只进 `uncertainty`，不改 `status`。
   本文**不修改 F15 的声明去迎合实测**，而是把差异登记在
   `FAULT-MATRIX.md` §4.1 与本表最后一行，供使用方自行判断。
3. **退出码语义是稳的**：`1`（跑不完但写出诚实的 failed）与 `2`（连记录都没地方写）
   在所有相关场景里没有串档。

> 复跑：`references/FAULT-MATRIX.md` §1 的一条命令会重建本表的全部数字。
> 新增失败模式时，请把它加进 `fault_inject.py` 的场景表并**真跑一次**再填本表。
