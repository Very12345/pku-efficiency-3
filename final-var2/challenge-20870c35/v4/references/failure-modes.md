# failure-modes.md — 失败模式处置手册（可靠体验维度的显性证据）

> 对应高分 intent 的 `failure-modes.md`。凡触发下表任一情形，一律**如实写入
> `change_records` 与 `uncertainty`**（含 `status` 降级），绝不编造缺失状态或数据。
> 决策规则 D1–D17（SKILL.md §6）与本表一一对应，机器分支见 `main.py` / `deck_builder.py`，
> 实测证据见 `TEST.md` §8（T8–T13，含负例）。

## 失败模式表

| # | 情形 | 处置 | 决策规则 | status |
|-|-|-|-|-|
| F1 | 材料在 case.json 声明但磁盘不存在 | `sources[]` 记 `kind=missing`（含 `path/file/kind/parsed/note`）；`evidence_map` 保留该条目；相关页面缺证据；不编造内容 | D1 | partial |
| F2 | 文本/PDF 解析失败或 PDF 无 pypdf | 记 `parsed=false` + 原因；该材料主张不进入页规划 | D2 | partial |
| F3 | PDF 抽取丢公式/符号/布局 | 以抽取文本为准并注明"抽取代理"，页内不补造公式 | D3 | 记录（completed 可保持） |
| F4 | 论文缺图/图分辨率低/图文件损坏 | 页内**诚实占位框**（标注"材料未提供图片文件"），notes 提示对照原文；坏图跳过 | D4 | 记录 |
| F5 | 无模板 / 模板路径失效 / 模板打不开 | 内置主题（16:9 母版），`artifacts.template_used/deck_mode` 注明 | D5 | 记录 |
| F6 | 模板适配中母版/版式不兼容 | 仅沿用可用版式；异常写入 change_records | D5 | partial（若核心页建不出） |
| F7 | 冻结页数与时长推导冲突 | 以任务冻结页数为准（P3），写入 plan_gates 说明 | D6 | 记录 |
| F8 | 听众信息缺失 | 按 familiar + 中等证据深度保守处理，audience.notes 说明可覆写 | D7 | 记录 |
| F9 | 材料中某块无直接主张 | 用该块章节概括成页（`derived=true`，strength=weak）并记录 | D8 | 记录 |
| F10 | 计划门 P1–P8 未全过 | 记录 errors；仍生成 honest 产物；status→partial；uncertainty 列出 | D9 | partial |
| F11 | deck 生成抛错（依赖已具备） | 保留异常前已写入的中间产物；`status=failed` + 异常入 `change_records` 与 `uncertainty` | D10 | failed |
| F12 | verify_deck 发现问题（页数/备注/命名/OPC） | 记录 entries；status→partial；不宣称"校验通过" | D11 | partial |
| F13 | 预览渲染失败/超时 | 非致命：仍写 result.json；`--skip-previews` 可跳过缩略图 | D12 | partial（预览维度） |
| F14 | 证据审计发现引文未逐字命中 | 记录条目（derived 页按概括语）；可修则重跑，不可修如实保留 | D13 | partial |
| F15 | 页内数字与源材料不一致（合理换算/截断） | validate_result 警告级提示；人工核对后忽略但需在 change_records 说明 | D14 | 记录 |
| F16 | 超时/预算（64 请求/900s/16k token） | 尽早落盘中间产物（talk_plan/deck/result 草稿）；收尾补 self_check；保存部分结果并说明限制 | D10/D12 | partial |
| F17 | 重复运行不确定性（时间戳等） | G9 探针记录"剔除记录性时间戳的内容投影 sha"；TEST.md 双跑实测（JSON 逐字节相同、PNG 逐字节相同） | — | 记录 |
| F18 | 平台/CLI 环境无 LibreOffice/PowerPoint | 预览用 PIL 模拟 + 水印 + manifest 限制说明；deck 仍可编辑主交付 | — | 记录 |
| F19 | output_contract 声明缺失字段 | apply_contract 按容器类型初始化（""/[]/{}/0，禁 null），missing_required 记录 | — | 记录 |
| F20 | 包约束超限（>50 文件/单文件 >500KB/合计 >2MB/符号链接/`__pycache__`） | `selftest --package-check` 拦截（G10）；打包前必须通过；扩展名白名单由提交前验收脚本核对 | — | 打包阻断 |
| **F21** | **缺 `python-pptx`（或 Pillow 连带不可用）** | **不崩**：跳过 deck，`artifacts.editable_deck=null` + `deck_limitation` + uncertainty 一条 + change_records 记明；页计划/计划门/预览/result.json/self_check 照常产出，命令仍返回 **0** | D15 | partial |
| **F22** | **模板/起始演示文件自带示例页** | 保留其母版与版式（模板约束不破坏），**丢弃自带页**后按冻结计划重建；`deck_mode.template_slides_present/dropped` + change_records 记明；保证最终页数 == 冻结页数 | D16 | 记录（completed 可保持） |
| **F23** | **材料为空 / 全部不可解析** | 只产出结构性页面；`status=partial` + uncertainty 明写"没有任何材料被解析为文本"；不据文件名/标签补造内容 | D17 | partial |
| **F24** | **本机绝对路径可能随产物外泄**（作者机器 `X:\...`/UNC 出现在 `sources[].path`、`figure_file`、`template_used`、错误文本里） | 写盘前由 `common.portable_path/sanitize_output` 改写为**相对案例目录**的正斜杠路径；消息内嵌路径就地改写；POSIX 运行期路径（`/input`、`/app`）原样保留 | — | 记录（`change_records` 可选说明） |
| **F25** | **示例二进制资源不能随包**（题面只允许 UTF-8 文本资源） | 示例 PDF/PNG/模板不随包：`scripts/make_synthetic_inputs.py` 运行时生成（零依赖手工 PDF + Pillow 纯几何示意图，均带 `SYNTHETIC` 标注）；示例输出二进制改为 `examples/EXPECTED-OUTPUT.md` 文字清单 | — | 打包阻断（存在二进制即不合规） |
| **F26** | **中文字体缺失或字形不适用** | 运行时按候选路径探测系统字体（Windows/Linux/macOS），结果（仅文件名）记入 `result.json.environment.cjk_font` 与 `previews/preview_manifest.json`；找不到则用 Pillow 内置位图字体，manifest 记明字形可能缺失 | — | 记录 |

## 状态一致性规则

1. `status` 只取 {completed, partial, failed}，降级必有对应 `uncertainty` 条目；
2. 每个 `uncertainty` / `change_records` 条目都要有"能垫付的具体事实"（文件名、错误信息、行号、门编号）；
3. 不允许"已覆盖"标注未覆盖证据；不允许把占位/概括描述为逐字引文；
4. **不允许静默降级**：产物缺失（deck/预览/某材料）必须在 `artifacts`/`sources`/`uncertainty` 三处之一可见；
5. **不允许虚报通过**：`verify_deck` / `evidence_audit` / 计划门未全过时不得声称"已校验通过"；
6. 退出码语义与状态一致：0 = 已有契约结果的诚实产出（可能 `partial`）；1 = 没有可用契约结果。

## 实测对照（TEST.md §8）

| 失败模式 | 实测测试 | 观测 |
|-|-|-|
| F1 / F23 | T8（声明材料不存在）、T13（材料为空） | `status=partial`；`sources` 分别出现 `kind=missing` 与 `(none)`；uncertainty 各有一条 |
| F2 | T9（遮蔽 pypdf/PyPDF2） | PDF `parsed=false` + 原因；其余材料照常出页 |
| F21 | T11（遮蔽 python-pptx）、T10（遮蔽 Pillow） | `status=partial`；deck 跳过、`deck_limitation` 记明；T11 仍产出 12 页计划与预览 |
| F22 | T5（带 1 张自带页的模板） | `template_slides_present=1 / dropped=1`；最终 12 张幻灯片 == 冻结页数 |
| F24 | T7a / 全部产物的路径扫描 | `sources[].path` 均为 `materials/...`；包内 grep「盘符 + 反斜杠」形式的绝对路径无命中 |
| F11 | T12（`case.json` 不可读） | 最小失败信封（`status=failed` + `error`，且 error 文本已净化）；退出码 1 |

## 注入演练实测对照（v4；完整表见 references/FAULT-MATRIX.md）

上表是**设计**，下表是**实测**：`scripts/fault_inject.py` 把四族 14 条注入 + 1 条对照逐个注入并真跑主流程，
每条记录真实退出码 / `status` / `uncertainty` / `change_records` 步数 / 是否静默失败。

| 注入族 | 覆盖的形态 | 实测 `exit` | 实测 `status` | 静默失败 |
|-|-|-|-|-|
| 对照组 `F00` | 无注入（基线） | 0 | completed | 否 |
| 输入 `F01`–`F05` | 非法 `case.json` / 缺 `case_id` / 材料缺失 / 零材料 / 无文本层 PDF | 1,0,0,0,0 | failed + partial×4 | 否 |
| 模板 `F06`–`F08` | 模板路径失效 / 容器损坏 / 自带示例页 | 0,0,0 | completed×3 | 否 |
| 依赖 `F09`–`F11` | python-pptx / Pillow / pypdf 缺失 | 0,0,0 | partial×3 | 否 |
| 契约 `F12`–`F14` | 契约块非法 JSON / 空契约 / 多声明字段 | 0,0,0 | partial×2 + completed | 否 |

**新增决策规则（由实测逼出来的三条）**：

| 规则 | 触发 | 处置 | 实测行 |
|-|-|-|-|
| **D18** | 模板存在但不是合法 OOXML（容器损坏） | `try` 打开失败 → 记 `template_load_error` → **回落内置主题**；异常进 `change_records`(step=`deck-source`) 与 `uncertainty`；**不得**把整轮记成 `failed` | `F07` |
| **D19** | `task.md` 声明了 output_contract 却用不起来（非法 JSON / 空对象 / 表格字段 <5） | 解析器带回**具体原因**；编排器写 `change_records`(step=`contract`) + `uncertainty`，`status→partial`；回落顺序 `case.json` > 内置默认 | `F12`·`F13` |
| **D20** | 契约声明了本包产不出的字段 | 按声明容器类型回落 `""`/`[]`/`{}`/`0`，**禁止 `null`**（与 `OUTPUT_CONTRACT.md` §1 一致）；`contract.applied` 记录全部已回显字段 | `F14` |

**状态一致性（补充一句）**：`completed` 的判定**不含**"必须用上模板"——模板缺失/不可用时走内置主题，
只要 `uncertainty` 明确记了这件事，`status` 仍是 `completed`（`F06`/`F07`/`F08` 实测如此）。
反过来，**契约声明不可用**会让 `status→partial`（`F12`/`F13`），因为此时我们无法确知要求的字段全集。
这两条边界是实测划出来的，不是先验设定。

**修前 vs 修后（三处真实缺陷，逐条点名见 FAULT-MATRIX.md §3）**：

| 注入 | 修前实测 | 修后实测 |
|-|-|-|
| `F07` 模板容器损坏 | `exit=1` / `failed` / deck 未生成 / traceback | `exit=0` / `completed` / deck 有 / 降级两处留痕 |
| `F05` 无文本层 PDF | `parsed=true` / `char_count=15` / `completed` | `parsed=false` + OCR 提示 / `partial` |
| `F12`·`F13` 契约不可用 | 无 `contract` 步、无对应 `uncertainty`、`completed` | `contract` 步 + `uncertainty` / `partial` |
| `F14` 多声明字段 | 字段 `null` / `contract_check` 失败 / `exit=1` | 字段 `""` / `contract_check` 通过 / `exit=0` |
