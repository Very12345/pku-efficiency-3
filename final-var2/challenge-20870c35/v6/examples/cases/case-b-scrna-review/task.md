# 任务说明（合成案例 B，非正式案例）

> 本 task.md 与同目录 case.json 是**合成泛化案例**的输入，用于检验流水线在
> 「短时长 + 评审类型 + 指标互相矛盾」这一组合下的表现，不是平台正式测试案例。

## 汇报任务

请围绕材料 `materials/scrna_extract.md`（论文主体）与 `materials/figures.md`（图表清单，
**本案例不提供图片文件**），组织一场 **12 分钟、8 页**的**评审答辩**汇报：

1. 提取研究问题、方法、结果与局限形成主线（评审场景下**结论先行**，证据强度判定放在最前）；
2. 设计页级主张、图表引用与讲解顺序（听众：评审专家组，熟悉指标口径）；
3. 生成可编辑演示文件及每页讲稿/备注；为每条局限与每条强结果准备问答；
4. 为每页内容保留论文或材料定位（源文件 · 行号 · 章节），并检查导出渲染；
5. **两个互相矛盾的指标必须同时上页**（MSE 改善 10.9% 与泊松似然改善 0.4%），
   不得只挑有利的那个；材料没给图片的图表引用如实标注占位。

## 输出要求

- 可编辑演示文件：页级结构、主张、图表、讲稿/备注齐全，能围绕论文主线讲清楚；
- 页级证据映射：每页内容对应论文章节或数据行，引用准确、未改写事实；
- 渲染与版本记录：源文件、导出件、字体/模板与修改记录可复核；
- 每案例返回结构化结果 `result.json`，保留输入标识、主结果、证据/来源定位、
  运行状态与不确定性；如实记录 status / sources / uncertainty / change records，
  不编造数据。

## 运行期输入位置

- 输入：`/input/case.json` 与 `/input/task.md`（本案例中即本目录）
- 工作目录：`/app/work`
- 最终产物：`/app/output`（含 `result.json` 与可编辑源文件、渲染预览）

## output_contract（声明字段清单）

```json
{"output_contract": [
  "case_id", "status", "title", "report_goal", "audience",
  "duration_min", "slide_count", "summary", "main_line", "pages",
  "evidence_map", "artifacts", "sources", "uncertainty",
  "change_records", "contract"
]}
```

> 运行时应同时读取 `case.json` 与 `task.md` 的真实内容，以实际文件为准，
> 不要根据本文件或任何标签预先假定源材料内容。
