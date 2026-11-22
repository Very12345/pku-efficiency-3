# failure-modes.md — 失败分支 B01–B24 与决策规则 D1–D16 对照表

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
