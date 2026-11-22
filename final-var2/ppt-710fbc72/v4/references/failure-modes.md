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
| **F12** 文本框溢出 | — | — | — | **未触发**（示例案例的文本量偏小，压不到 12pt 地板；要触发它需要一页塞入更多主张） |
| **F13** 标题过长 | — | — | — | **未触发** |
| **F14** 页数超目标 | — | — | — | **未触发**（示例案例的页数刚好落在目标上；要触发它需要一个"带媒体的结果条目数"超过页预算的案例） |
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
