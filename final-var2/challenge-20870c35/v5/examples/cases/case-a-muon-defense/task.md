# 任务说明（合成案例 A，非正式案例）

> 本 task.md 与同目录 case.json 是**合成泛化案例**的输入，用于检验流水线在另一个学科题材
> （凝聚态实验物理）上的稳定性，不是平台正式测试案例，也不含任何预制答案。

## 汇报任务

请围绕材料 `materials/muon_extract.md`（论文主体）与 `materials/figures.md`（图表清单，
**本案例不提供图片文件**），组织一场 **25 分钟、15 页**的**学位答辩**汇报：

1. 提取研究问题、方法、结果与局限形成主线（答辩场景下"边界与局限"必须靠前，不能留到最后一句）；
2. 设计页级主张、图表引用与讲解顺序（听众：答辩委员会，熟悉实验、不熟悉反演细节）；
3. 生成可编辑演示文件及每页讲稿/备注；为每条局限与每条强结果准备问答；
4. 为每页内容保留论文或材料定位（源文件 · 行号 · 章节），并检查导出渲染；
5. 图表引用必须与页内结论对应：**材料没给图片的，页内如实标注占位**，不得伪造图形。

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
