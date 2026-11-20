# METHODS.md — 内容组织方法说明（关键方法）

本文解释本 Skill 的**取舍逻辑**（为何这样组织），与 `templates/narrative_template.md`
（怎么做）和 `templates/talk_config.json`（机器规则）配套。

## 1. 从"论文压缩"到"汇报设计"的差异点

| 维度 | 基础做法（不加载 Skill） | 本 Skill |
|-|-|-|
| 页数 | 跟随论文章节长度 | 由 `报告目标 + 听众 + 时长` 决定（`slide_count` 缺失时按时长×60/85s 推导） |
| 顺序 | 摘要→引言→方法→结果→讨论 | 按汇报类型叙事序（组会：问题—进度—方法—结果—风险；答辩：…创新点边界后置；评审：结论先行） |
| 每页 | 一段文字 | 唯一主张 + 证据定位 + 一句话讲稿 + 备答 |
| 图表 | 复制论文图表 | 引用号绑定源材料 + 证据强度标注 + 无图诚实占位 |
| 问答 | 无准备 | 局限/强结果 → 预判追问 → 回答要点 → 备用页 |

## 2. 五个突破方向的落点

1. **报告目标**：`report_goal` 写入封面与成功标准；缺省按汇报类型给默认（见 `planner.REPORT_GOAL_MAP`）。
2. **听众**：关键词规则把听众描述映射到 expert/familiar/lay，决定背景与术语页占比与术语表收录。
3. **叙事顺序**：`talk_config.json` 每类型一套 `order`，`planner._alloc_pages` 按权重+固定页分配页数并校准到冻结页数。
4. **重点信息**：一页一主张；`strength` 由 数值/统计记号/图表引用 自动定级；间接概括页显式标注 weak。
5. **问答准备**：每条局限 → 一条追问；每条 strong 结果 → 一条"证据强度"追问；`qa` 备用页收拢。

## 3. 证据抽取与定位（可复核的关键）

- 逐行打锚：`evidence.split_sections` 把材料切为 `{heading, path, start_line, end_line, lines[{no,text}]}`。
- 主张候选：含结果动词/数值/图表引用的行（`FINDING_HINT_RE`），逐字保留原文，绝不复述改写。
- 定位格式：`L<行号> · §<章节>`，配合 `quote` 原句，读者可按行号回查源文件。
- 数字一致性：`validate_result.py` 把每页 claim/one_liner 中的数字与全部源文本比对，不在源中的数字给**警告**（供人复核，不硬拦——硬拦会误伤合理换算）。

## 4. 诚实与降级约定

- PDF 无解析器 → 记为 `parsed:false`，相关页不编造；status 降 `partial`。
- 材料缺失 → `sources` 中 kind=missing，影响写进 uncertainty。
- 无图 → 占位框 + notes 提示"讲解时对照原论文图"。
- 无模板 → 内置主题并注明；有模板 → 打开沿用版式，另记录 template_used。
- 不可用的中间物（坏图片、坏 PDF、缺失字体）全部进 `change_records`/`uncertainty`，不静默修复。