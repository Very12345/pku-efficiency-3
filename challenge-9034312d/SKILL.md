---
name: apparatus-and-route-diagrams
description: >-
  依据科研材料生成「实验装置与技术路线图」可编辑图稿（SVG 分层源文件 + PNG/PDF 预览 +
  result.json）。适合实验装置结构、步骤顺序、材料流向与技术路线的绘图任务；每个图面实体
  可追溯到输入材料，交付可被他人打开、修改并复跑出同一张图的产物，并诚实记录来源、不确定性与修改记录。
---

# 实验装置与技术路线图 Skill（challenge-9034312d · figures 组）

本 Skill 把「装置怎么搭、步骤怎么走、物料从哪来到哪去、技术路线分几个阶段」的文本材料，
变成一张可编辑的科研图稿。核心不为「画得漂亮」，而是保证**每个实体可追溯、连接与顺序成立、
交付物可被打开修改并复跑出同一张图**。

## 1. 用途

- 依据案例材料（装置清单/装配说明/方法段落/工艺描述）抽取**实体、关系、步骤、流向**，
  生成结构化中间表示（SIR）；
- 按图类（route / apparatus / flow / hybrid）确定性布图：阶段分列、步骤编号、正交连线、
  箭头方向、图例映射、数据映射；
- 交付三件套：**可编辑分层 SVG 源文件**（`<text>` 真实文本，可被 Inkscape/文本编辑器直接改）、
  **PNG/PDF 预览**、**result.json**（含 output_contract 全部字段 + case_id）；
- 对每个关键元素标注来源（source）、版本（checksum）、导出检查结果。

不承担：数据分析与数值拟合、实验方案本身的科学合理性判断、论文排版与期刊投稿格式适配。

## 2. 适用条件

- 输入：`/input/case.json`（必读）+ `/input/task.md`（可选）；
- case.json 可为结构化（`entities`/`relations`/`figure_type`/`canvas`）或自由文本
  （`text`/`materials_text`）；两者均可处理，结构缺失时走文本解构并如实标注
  `extraction=text-heuristic`；
- 输出：写入 `/app/output`（本 Skill 用 `--out` 指定输出根目录）。

## 3. 输入输出接口

```
python scripts/main.py --case /input/case.json [--task /input/task.md]
                       --out /app/output [--dpi 200]
                       [--figure-type route|apparatus|flow|hybrid]
                       [--width-mm N] [--height-mm N] [--title "…"]
                       [--merge /app/work/override.json]
```

产出（相对输出根目录，实际以 <case_id> 为子目录）：

| 文件 | 说明 |
|-|-|
| `figure.svg` | **可编辑分层源文件**（图层: title/arrows/entities/legend；实体组带 data-entity/data-source；`<text>` 可编辑） |
| `figure.png` | PNG 预览（PIL + 本机中文字体，默认 200 DPI） |
| `figure.pdf` | PDF 预览（reportlab，CID 中文字体，矢量） |
| `layout.json` | 结构化布局模型（SIR → 几何的中间证据，可复核重绘） |
| `result.json` | 结构化结果（contract 全字段 + case_id，见 `references/OUTPUT_CONTRACT.md`） |

脚本自定位：所有脚本通过 `os.path.dirname(__file__)` 找到技能根，**不依赖运行时 cwd**；
模板配色默认取 `templates/palette.json`（相对技能根）。

## 4. 执行步骤

按顺序执行，每步都在真实文件上操作，**不依据领域标签猜内容、不编造数据**：

### 步骤 0 · 读实际文件
1. `read /input/case.json`（真实读取，禁止假设内容）；
2. 如有 `read /input/task.md`；记录两者为 `sources`。
3. 判断结构：有结构化列表 → 直接使用；只有文本 → 标记将走文本解构。

### 步骤 1 · 抽实体关系数据（结构化中间表示）
1. 运行 `python scripts/main.py --case /input/case.json --task /input/task.md --out /app/output`
   （先用默认参数跑一遍，拿到初版 SIR 与图稿）；
2. **Agent 必须复核中间表示**：
   - 实体名称与材料是否一致、同类部件是否区分；
   - 关系/箭头方向是否与正文一致（严禁反向或凭空补齐连接）；
   - 步骤编号是否与正文顺序逐条对应；
   - 图例颜色与图内图形是否一致；
3. 需要修正时，写 `/app/work/override.json`（`{"entities":[{id,...}],"relations":[{id,...}],"change_notes":[...]}`），
   再带 `--merge` 重跑：同名 id 替换、新 id 追加，修正动作自动写入 change_record。

### 步骤 2 · 做可编辑源文件
1. 确认 `figure.svg` 生成且可编辑：
   - 实体是真实 `<text>`（不是路径），有 `<g id="entity-X" data-source="…">` 分组；
   - 有 title/arrows/entities/legend 分层命名；
2. 如画布溢出/文字折行异常，用 `--width-mm/--height-mm` 调整画布或精简标签重跑；
3. 复杂图（多阶段回流、跨列长箭头）可在 Inkscape 微调后保存，并在 change_record 增补
   `action: manual-edit` 记录修改内容（保持诚实）。

### 步骤 3 · 导出渲染
1. 确认 `figure.png` 与 `figure.pdf` 生成（渲染失败会如实写入 uncertainty 与 status=partial）；
2. 检查字体：PNG 依赖本机 TTF（fonts.py 候选表），缺失时 result.json.fonts 会记录 found=false；
3. 预览打开目测：箭头方向、编号、图例、无断头箭头、无重叠盒子。

### 步骤 4 · 写 result.json + 交付自查
1. 确认输出目录含 `result.json`（`output_contract.editable_sources/exports/data_mapping/
   element_traceability` + `case_id/status/sources/uncertainty/change_record/checksum`）；
2. 运行自查：`python scripts/check.py <result.json>`，全绿（`ok: true`）才算完成；
3. 自查发现的问题（缺文件、SVG 不可解析、编号断号、断头箭头）必须修复后重跑，不得隐瞒。

## 5. 异常处理

| 情况 | 处置 |
|-|-|
| case.json 不存在/不可解析 | 立即终止并写 status=failed 的 result.json，说明原因；**不猜内容** |
| 无结构化实体，仅文本 | 走文本解构；extraction=text-heuristic；uncertainty 列出解构方式；status 按孤儿实体降级为 partial |
| 关系指向不存在的实体 | 丢弃该关系并在 uncertainty 记录「断头箭头已过滤」，由 Agent 复核 |
| PNG/PDF 渲染失败 | 保留已有产物，status=partial，uncertainty 记录异常；SVG 源文件仍在 |
| 本机无中文字体 | fonts.found=false 记入 result.json；SVG/PDF 仍可用（字体名声明/CID），如实说明 |
| 画布溢出 | 自动等比压缩到请求画布；或由 Agent 调整 width/height 重跑 |
| 领域信息冲突/缺失 | 记入 uncertainty 的 scope+issue+action，不擅自补造数据 |
| 管线整体异常 | main.py 兜底写 status=failed result.json 并打印 traceback；不自称成功 |

## 6. 自查清单（完成判定）

- [ ] 实体≥1 且与输入材料一致，source 出处可追溯（缺失者已列入 uncertainty 或人工补齐）
- [ ] 关系两端实体均存在（无断头箭头），方向与正文一致
- [ ] route/flow 图步骤编号连续（1..N）
- [ ] figure.svg 是合法 XML、含分层 `<g>`、`<text>` 可编辑元素 ≥3
- [ ] figure.png / figure.pdf 存在且非空（失败已如实降级）
- [ ] result.json 字段齐全（见 OUTPUT_CONTRACT.md），status 诚实
- [ ] `python scripts/check.py <result.json>` 输出 ok:true（或列出的 issues 已全部修复）
- [ ] 修改历史（change_record）、不确定性（uncertainty）、来源（sources）均已如实记录

## 7. 边界与诚实原则

- 本 Skill 只负责**绘图表达**与**可编辑交付**；不判断实验方案科学性，不做数值拟合；
- 每个实体/关系尽量携带 source；拿不到 source 就标 null 并计入 uncertainty；
- 不伪造软件状态（如中文字体缺失）、不编造科研数据/数值；
- 正式案例的评分由平台执行；`examples/` 仅为接口演示（其中 result 标注「示例，非正式案例」）。

## 8. 资源清单（相对技能根）

- `scripts/main.py` — 一键流水线（解析→布图→导出→result.json→自查）
- `scripts/model.py` — SIR：实体/关系/步骤/流向解析与文本解构兜底
- `scripts/layout.py` — 确定性布图引擎（图元库+布局模板落点）
- `scripts/export_svg.py` — 手写分层 SVG（可编辑源文件）
- `scripts/export_preview.py` — PIL PNG + reportlab PDF 预览（同一布局模型）
- `scripts/check.py` — 交付自查
- `scripts/fonts.py` — 中文字体探测与降级
- `templates/palette.json` — 图元配色模板
- `references/OUTPUT_CONTRACT.md` — result.json 契约
- `references/RUBRIC_MAP.md` — 评分维度→设计覆盖映射
- `references/LAYOUT_SPEC.md` — 布局/图元规范
- `examples/` — 最小调用示例（非正式案例）

依赖（运行环境已具备，全部可降级）：Python 3.10+ 标准库；Pillow（PNG 预览）；
reportlab（PDF 预览）。`python-pptx` 非必需（本 Skill 交付 SVG 源文件）。