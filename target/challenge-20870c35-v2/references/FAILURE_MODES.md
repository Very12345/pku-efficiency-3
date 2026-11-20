# FAILURE_MODES.md — 失败模式处置手册（可靠体验维度的显性证据）

> 对应高分 intent 的 `failure-modes.md`。凡触发下表任一情形，一律**如实写入
> `change_records` 与 `uncertainty`**（含 `status` 降级），绝不编造缺失状态或数据。
> 决策规则 D1–D14（SKILL.md §6）与本表一一对应，机器分支见 `main.py`。

## 失败模式表

| # | 情形 | 处置 | 决策规则 | status |
|-|-|-|-|-|
| F1 | 材料在 case.json 声明但磁盘不存在 | `sources[]` 记 `kind=missing`；相关页面缺证据；不编造内容 | D1 | partial（若影响主线） |
| F2 | 文本/PDF 解析失败或 PDF 无 pypdf | 记 `parsed=false` + 原因；该材料主张不进入页规划 | D2 | partial |
| F3 | PDF 抽取丢公式/符号/布局 | 以抽取文本为准并注明"抽取代理"，页内不补造公式 | D3 | 记录（completed 可保持） |
| F4 | 论文缺图/图分辨率低/图文件损坏 | 页内**诚实占位框**（标注"材料未提供图片文件"），notes 提示对照原文；坏图跳过 | D4 | 记录 |
| F5 | 无模板 / 模板路径失效 / 模板打不开 | 内置主题（16:9 母版），`artifacts.template_used/deck_mode` 注明 | D5 | 记录 |
| F6 | 模板适配中母版/版式不兼容 | 仅沿用可用版式；异常写入 change_records | D5 | partial（若核心页建不出） |
| F7 | 冻结页数与时长推导冲突 | 以任务冻结页数为准（P3），写入 plan_gates 说明 | D6 | 记录 |
| F8 | 听众信息缺失 | 按 familiar + 中等证据深度保守处理，audience.notes 说明可覆写 | D7 | 记录 |
| F9 | 材料中某块无直接主张 | 用该块章节概括成页（`derived=true`，strength=weak）并记录 | D8 | 记录 |
| F10 | 计划门 P1–P8 未全过 | 记录 errors；仍生成 honest 产物；status→partial；uncertainty 列出 | D9 | partial |
| F11 | deck 生成抛错 | 若已在异常前写入中间产物则保留并说明；`status=failed` + traceback 入 change_records | D10 | failed |
| F12 | verify_deck 发现问题（页数/备注/命名/OPC） | 记录 entries；status→partial；不宣称"校验通过" | D11 | partial |
| F13 | 预览渲染失败/超时 | 非致命：仍写 result.json；`--skip-previews` 可跳过缩略图 | D12 | partial（预览维度） |
| F14 | 证据审计发现引文未逐字命中 | 记录条目（derived 页按概括语）；可修则重跑，不可修如实保留 | D13 | partial |
| F15 | 页内数字与源材料不一致（合理换算/截断） | validate_result 警告级提示；人工核对后忽略但需在 change_records 说明 | D14 | 记录 |
| F16 | 超时/预算（64 请求/900s/16k token） | 尽早落盘中间产物（talk_plan/deck/result 草稿）；收尾补 self_check；保存部分结果并说明限制 | D10/D12 | partial |
| F17 | 重复运行不确定性（时间戳等） | G9 探针记录"剔除记录性时间戳的内容投影 sha"；TEST.md 双跑实测 | — | 记录 |
| F18 | 平台/CLI 环境无 LibreOffice/PowerPoint | 预览用 PIL 模拟 + 水印 + manifest 限制说明；deck 仍可编辑主交付 | — | 记录 |
| F19 | output_contract 声明缺失字段 | apply_contract 按容器类型初始化（""/[]/{}/0，禁 null），missing_required 记录 | — | 记录 |
| F20 | 包约束超限（>50 文件/>500KB/文件/>2MB 总/符号链接/__pycache__） | selftest --package-check 拦截（G10）；打包前必须通过 | — | 打包阻断 |

## 状态一致性规则

1. `status` 只取 {completed, partial, failed}，降级必有对应 uncertainty 条目；
2. 每个 uncertainty/change_records 条目都要有"能垫付的具体事实"（文件路径、错误信息、行号）；
3. 不允许"已覆盖"标注未覆盖证据；不允许把占位/概括描述为逐字引文。