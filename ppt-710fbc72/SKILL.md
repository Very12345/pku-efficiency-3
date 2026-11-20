---
name: academic-slide-adapt
description: >-
  Academic slide deck creation from research material with real template
  adaptation (学术 PPT 模板与格式适配): read the actual paper/material and
  template files, extract the research storyline (question → method →
  results → limitations) with per-item source locators, plan a page structure
  that respects a fixed audience/duration/slide count, apply the given
  PowerPoint template through its real master/layout/placeholder inheritance
  (falling back with full disclosure when placeholders are missing), embed
  figures/tables contain-fit with figure numbers cross-checked against the
  text, add per-slide speaker notes plus an appendix evidence map, and deliver
  an editable .pptx, PNG previews and a verifiable result.json. Use when the
  task says "make an academic presentation / 学术PPT / 学术汇报 / 论文转PPT /
  adapt this paper into slides / 套模板 / 模板适配 / 按模板生成PPT / deck
  from paper", or when a starting deck must be re-edited on its own template.
---

# Academic Slide Adapter（学术 PPT 模板与格式适配）Skill — slides 组

把论文/研究材料组织成**结构清楚、证据可追溯、可编辑、符合模板要求**的学术汇报：
从封面到结论逐页讲清主线，每页带着主张、图表引用与讲稿，并附「页 → 论文位置」
证据映射附录。**对版式科学负责**：模板是否真实套用（母版/版式/占位符继承可查）、
页内内容与源论文与图表是否对得上、整册能否被他人按记录复跑并逐页核对。

- Skill 版本：`1.0.0`
- Skill 根：本文件所在目录（下文所有相对路径均相对 Skill 根）
- 核心脚本：`scripts/main.py`（一条命令完成全流程）

---

## 1. 用途与适用条件

**适用**：给定论文/实验材料要求产出学术汇报幻灯片，且要求可编辑 pptx、
渲染预览和可复核来源；尤其适用于"必须套用指定模板/在起始 deck 上改编"的
场景。读取**真实文件**，绝不凭文件名/标签猜内容。

**适用输入形态**（至少其一）：

| 输入 | 说明 |
|-|-|
| `case.json` | 必读。`case_id / title / subtitle / authors / affiliation / research_question / methods / results / discussion / limitations / conclusion / figures / tables / audience / duration_minutes / slide_count / language / template / starting_deck / source_material / output_contract`（均可省略，缺项走材料抽取或默认值） |
| `task.md` | 任务说明：受众、时长、页数、交付要求；`# 背景/方法/结果/结论` 小节会被抽取 |
| 材料文件 | `source_material` 指明的 md/txt/tex/csv 等；提供主张与数值的真正来源（`文件:行` 定位） |
| 模板 | `template` 指明的 `.pptx`（或 `--template` 显式指定）；缺省用 Skill 内置回退模板 `templates/builtin.pptx` |
| 起始 deck | `starting_deck` 指明的 `.pptx`（在其上改编：沿用母版/版式/主题，替换页面内容，记录 change_records） |
| `output_contract` | 案例自带的交付契约；每个字段原样进 `result.json` 顶层（契约见 `references/OUTPUT_CONTRACT.md`） |

**不适用/明确边界**：本 Skill 不代写科学内容（材料中没有的数值绝不补造）、
不做动画/切换效果、不解析主题 XML 取色板；预览在无 LibreOffice/PPT 环境为
PIL 示意图（如实标注，不冒充像素级导出）。

## 2. 输入与输出

**输入路径约定（Runtime contract）**：官方案例运行时 `/input/case.json` 与
`task.md` 由平台挂载，材料按案例提供；在 `/app/work` 内解析相对路径。
本机/任意环境：`--case <case.json>` 显式指定。

**输出**：全部写到 `--out` 指定目录（官方约定 `/app/output`；本机默认自选）：

| 文件 | 内容 |
|-|-|
| `<case_id>_deck.pptx` | **可编辑源**：按模板版式/占位符写入，逐页主张/图表/讲稿备注，统一页脚页码 |
| `<case_id>_cover_preview.png` | 封面预览（PIL 示意图，命名与文件内标注 SCHEMATIC） |
| `<case_id>_slides_contact_schematic.png` | 全册联系表（PIL 示意图） |
| `result.json` | **结构化结果**（契约见 `references/OUTPUT_CONTRACT.md`） |
| `spec.json` / `content.json` | 页计划 / 规范化抽取（含来源定位） |
| `audit.json` / `render_log.json` / `summary.txt` | 自查报告 / 渲染日志 / 摘要 |

## 3. 执行步骤

第 1–6 步由脚本流水线执行（`python scripts/main.py --case <case.json>
[--task <task.md>] [--work <材料基目录>] [--template <模板.pptx>]
[--starting-deck <deck.pptx>] --out <输出目录>`）；作为 Agent，你**必须**在
调用脚本之外阅读真实文件并复核抽取/落版，偏差写进 `result.json` 的
`change_records` / `uncertainty`。**不得用预制答案替代实际运行。**

### 步骤 1 —— 读实际文件（不要凭标签猜内容）
1. 读取 `case.json`（UTF-8）；失败即报错退出并说明，不留虚假产物。
2. 解析 `source_material` 相对路径（相对 case 目录/`--work`/`/app/work`），
   逐个读取材料原文，逐行编号。
3. 读取 `task.md`：受众、时长、页数、语言与交付要求。
4. 定位模板/起始 deck：`case.json["template"]` → `case.json["starting_deck"]`
   → 内置 `templates/builtin.pptx`；用 python-pptx 打开并枚举
   母版/版式/占位符（`template_audit.layouts`），打不开就回退下一级。

### 步骤 2 —— 抽取主张/图表/数据（source-bound）
运行 `scripts/extract.py`：规范化 question/methods/results/discussion/
limitations/conclusion、figures（含 `文件:行` 来源与图片文件）、tables、
关键数值；并用材料小节标题（`# 方法/结果…`）与图注行（`图1 …` / `Table 1 …`）
补抽。**规则**：每个条目带 `source`（`文件:行` 或 `case.json[字段]`）；
材料中找不到源头的数值**不得上页面**，进 `uncertainty`。复核段落是否进入
正确的故事环节（背景/方法/结果/讨论/局限/结论）。

### 步骤 3 —— 页级规划（确定性、受页数约束）
运行 `scripts/deckplan.py`：固定骨架 cover→background→methods→
results×N（每图/表一页）→discussion→limitations→conclusion→
evidence_map 附录→thankyou（agenda 可选，sup 页数滑动插入）；页数超目标时
按确定性裁剪：合并讨论+局限 → 删议程 → 合并最后两张结果页。每页给出
**页级主张 claims、图表引用 figure_refs/table_refs、讲稿 notes（含建议时长）、
证据 evidence[{claim, loc}]**。

### 步骤 4 —— 生成可编辑 pptx（模板适配层）
运行 `scripts/pptxbuild.py`：
- 按页型选版式（cover 需 title+subtitle，其余需 title+content body；`text`
  类占位符不算 body，防止正文进窄列）；单 body 且宽度≥50% 画布优先；
- 内容写进占位符→**继承模板主题字体/颜色**（不覆盖 run 字体）；缺占位符→
  手绘文本框回退并记录（`layout_fallback_used`）；
- 字号阶梯（32→12pt）按占位符真实几何估算换行，溢出只降字号、最低 12pt，
  再溢出就报告，绝不压到不可读；
- 图表等比 contain-fit（不拉伸），图注 `图N 标题 [来源: …]`；表格原生 table；
- 封面外统一页脚+页码；逐页写 speaker notes（主张/证据/建议时长）；
- 模板套用审计（版式、占位符继承、图片缩放日志）写进 `template_audit`。

### 步骤 5 —— 导出渲染件（诚实标注）
运行 `scripts/preview.py`：无 LibreOffice 时产出 **PIL 示意图**封面 + 全册
联系表，文件命名含 `schematic`、首图叠加免责声明、`render_log.json` 记录
渲染后端与字体探测；**PDF 导出能力缺失如实记录，不产伪 PDF**。

### 步骤 6 —— 自查（audit）+ 写 result.json
运行 `scripts/audit.py` 在**真实产物**上检查：pptx 可被 python-pptx 重开、
页数与计划一致、计划主张出现在页面上、图号交叉引用一致、逐页备注齐全、
无溢出/字号落底、页脚页码一致、PNG 有效、证据定位覆盖率≥90%。
随后写 `result.json`：`output_contract` 全部字段镜像进顶层 + 信封字段
（`case_id/status/main_result/artifacts/slide_evidence/template_audit/
verification/sources/uncertainty/change_records/generated_at/…`），并附加
`result.contract` 自查检查。`status`：全绿=success；有 warn/fail=partial
（必须写明限制）；管线未完成=failed。

### 步骤 7 —— 收尾与人工复核
- 打开 PNG 目视：封面主标题/副标题/作者单位、联系表每页标题与主张无乱码；
- 打开 pptx：版式继承、图表不拉伸、页脚页码一致、备注可读；
- 同输入重跑一次：`spec.json` 结构一致、`result.json` 仅时间戳差异；
- 复核证据映射：抽查 ≥3 条 `claim → 文件:行` 能在材料里找到；
- 人工确认与修改写进 `change_records`。

## 4. 异常处理（失败模式表）

| 情形 | 处理 | 记录位置 |
|-|-|-|
| `case.json` 缺失/不可解析 | 立即失败（exit 1）并说明原因，不产半成品冒充成功 | stderr |
| 模板缺失/打不开 | 回退链 case 模板→starting deck→内置模板；回退原因记录 | `template_audit.template_errors` / `template_fallback_used` |
| 版式缺所需占位符 | 手绘文本框按计划几何落位，记录 fallback | `template_audit.layout_fallback_used` |
| 材料/数值缺失 | 以现有材料继续；缺失项进 uncertainty，**绝不编造** | `uncertainty` + `audit` |
| 文本框溢出 | 字号阶梯只降到 12pt，仍溢出则报告 | `audit.layout.overflow / font_floor` |
| 源图文件缺失/嵌入失败 | 灰底图位占位框（图号+标题+来源保留） | `uncertainty` + `template_audit.figure_adjust` |
| 字体缺失（预览渲染） | PIL 字体回退链（msyh→simhei→默认），字体名如实记录 | `render_log.json` + `uncertainty` |
| 导出失败/无 LibreOffice | 不产伪 PDF；预览标注 SCHEMATIC，能力缺失如实说明 | `render_log.json` + `preview_is_schematic` |
| 保存中途失败 | 先落盘部分产物，报错含已写路径；写 failed result.json | stderr / `result.json(status=failed)` |

## 5. 自查清单（每次运行后逐项确认）

- [ ] 读取的是真实文件（case.json/task.md/材料/模板），不是凭标签假设内容
- [ ] 模板被真实套用：`template_audit.layouts/layout_used` 记录了
      母版/版式/占位符继承关系，可查（抽查页型对应的版式名）
- [ ] 每页主张带 `claim→文件名:行` 定位；抽查 ≥3 条能在材料中找到
- [ ] 图号与正文引用一致（audit `xref.figure_refs/placement` 通过）；
      图表等比放入（`figure_adjust` 无拉伸）
- [ ] 逐页 speaker notes 存在；页脚/页码全册一致
- [ ] `result.json` 含 `output_contract` 全部字段 + case_id + status +
      sources + uncertainty + change_records（`result.contract` 检查 ok）
- [ ] pptx 可被 python-pptx 重开（`pptx.reopen`）、页数=计划（`spec.json`）
- [ ] 预览 PNG 存在且非空白；渲染后端/字体回退在 `render_log.json` 如实记录
- [ ] 未有「看起来热闹但无来源」的装饰性页面/数据

## 6. 目录结构

```
<skill root>/
  SKILL.md                本文档
  README.md               使用说明 / 依赖 / 限制 / 失败处理
  TEST.md                 本地实测记录
  GITHUB_URL.txt          GitHub 公开链接占位（发布代理覆写）
  references/
    OUTPUT_CONTRACT.md    result.json 结构与字段契约
    RUBRIC_MAP.md         评分五维 → 设计覆盖映射
    TEMPLATE.md           模板适配规则 / 版式字号阶梯 / 复用指南
  scripts/
    main.py               编排入口（命令行）
    extract.py            主张/图/表/数值抽取（来源定位）
    deckplan.py           确定性页计划（页型/裁剪/证据映射）
    pptxbuild.py          模板适配 + pptx 生成（占位符继承/字号阶梯/图表）
    preview.py            PIL 示意图预览（封面+联系表，诚实标注）
    audit.py              真实产物自查（重开/覆盖/图号/溢出/页脚/确定性）
    validate_result.py    result.json 契约校验（VALID, exit 0）
    make_template.py      内置回退模板再生成
    common.py             公共工具（路径自定位/字号阶梯/字体/颜色/哈希）
  templates/
    builtin.pptx          内置回退模板（16:9，真实母版/版式/占位符）
  examples/
    case.json / task.md / material.md / figs/   最小示例输入（合成数据，非正式案例）
    output/*              示例输出（标注「示例，非正式案例」）
```

脚本不硬编码绝对路径：`scripts/common.py` 用 `os.path.dirname(__file__)`
自定位 Skill 根；所有输入输出路径由命令行显式给出（官方运行时为
`/input`、`/app/work`、`/app/output`）。