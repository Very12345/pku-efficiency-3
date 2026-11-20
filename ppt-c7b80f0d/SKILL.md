---
name: paper-to-academic-ppt
description: 把论文/研究材料转换成主线清晰、证据可追溯、可编辑的学术汇报 PPT。加载后按"读实际文件→抽主线与证据→页级 deck-spec→模板适配生成可编辑 .pptx→渲染预览→写带全部 output_contract 字段的 result.json"全流程执行，页级主张、图表编号引用、讲解备注分离生成，缺失证据显式标注、不编造数据。Use when a task asks to turn a paper or research material into an academic slide deck (论文转PPT、学术汇报PPT、slides from paper、presentation from paper), especially when /input/case.json and task.md are present and /app/output must contain the editable deck plus previews.
---

# 论文转学术 PPT（paper-to-academic-ppt）

本 Skill 负责"论文内容 → 可讲、可核验、可编辑的学术汇报 PPT"这条链路：
在给定论文/材料与模板约束下，重写为 **页级离散表达**（一页一个主张、主张挂图/表/结论定位），
产出可在目标软件中打开、放映、逐页编辑的 `.pptx`，并交付可复核的 `result.json` 与渲染预览。

**不负责**：论文精读结论的生成、科研绘图本身的图形设计、学术写作润色。
**不使用预制答案**：正式运行只依据案例实际提供的文件，示例仅说明接口。

---

## 1. 用途与适用条件

- 输入一份科研材料（论文 PDF / 文本文稿）＋案件约束（audience / 时长 / 页数 / 模板），
  输出一套学术汇报：
  - 主线成立、页序可讲（问题→方法→证据→结论→局限）；不是按段落顺序搬运；
  - 每页内容可回溯到论文的图/表/章节/页码（页级证据映射）；
  - 在组织方模板内排布（模板占位符约束；无模板时用自带学术版式）；
  - 讲解备注与页面文字**分离**生成（notes_slide）；
  - 源文件可编辑（.pptx），并有渲染预览（无 PowerPoint/LibreOffice 时为
    PIL 近似预览，如实标注）。
- 触发场景：`/input/case.json` + `task.md`（平台固定案例）；或用户直接要求
  "把这篇论文做成学术 PPT / slides from this paper"。

## 2. 输入输出

| 方向 | 路径（以环境实际挂载为准） | 内容 |
|-|-|-|
| 输入 | `/input/case.json` | case_id、output_contract（期望的 result.json 字段）、材料/模板定位、audience/时长/页数约束 |
| 输入 | `/input/task.md` | 任务说明（存在时读取） |
| 工作 | `/app/work` | 中间产物：PDF 抽取文本、图片、deck-spec.json |
| 输出 | `/app/output` | `result.json`、`academic_deck.pptx`、`preview-approx-*.png`、`evidence_mapping.md` 等 |

> 路径自适应：Skill 资源以本文件所在目录为根（下称 `$SKILL_DIR`）自定位；
> 平台安装到 `/skills/weekly-skill` 时 `$SKILL_DIR=/skills/weekly-skill`。
> 若运行时输入不在 `/input`，先探测环境变量（如 `CASE_PATH`/`OUTPUT_DIR`）或
> cwd 中的 `case.json`，**以实际可读文件为准**，不要假设未实现的路径。

## 3. 资源清单（$SKILL_DIR）

| 文件 | 作用 |
|-|-|
| `scripts/main.py` | 端到端入口：材料→.pptx→预览→result.json→自检 |
| `scripts/deck_builder.py` | 模板适配 + 页级排版 + 备注 + 证据映射页 |
| `scripts/pdf_extract.py` | PDF 文本/图片实际抽取（fitz→pypdf→pdfplumber 回退） |
| `scripts/preview.py` | PIL 近似预览 + 从表格数字重建图（matplotlib，PNG+SVG） |
| `scripts/validate.py` | result.json 契约独立校验（exit 0/1） |
| `references/OUTPUT_CONTRACT.md` | result.json 契约（必读） |
| `references/TEMPLATE_GUIDE.md` | deck-spec.json schema + 模板适配规则 |
| `references/RUBRIC_MAP.md` | 评分维度→实现覆盖映射 |
| `examples/` | 最小示例（标注"示例，非正式案例"） |

依赖（Python）：`python-pptx` 必需；`Pillow` 用于预览；`matplotlib` 可选（重建图）；
`PyMuPDF / pypdf / pdfplumber` 任选其一即支持 PDF 解析（无则用 DSH 自带 PDF
读取导出文本后传入）。脚本会逐级回退并如实记录。

## 4. 执行步骤（S0–S6）

### S0 定位与读题
1. 读取 `task.md`（若存在）与 `/input/case.json`，记录 `case_id`。
2. 解析 `case.json` 关键字段：`output_contract`（必须回显到 result.json 的全部字段）、
   材料路径（`material/paper/pdf/documents` 等）、模板路径、`audience/duration_minutes/slide_count`。
3. 定位 Skill 根 `$SKILL_DIR`；所有脚本用
   `python $SKILL_DIR/scripts/main.py ...` 绝对路径调用（脚本内部用
   `os.path.dirname(__file__)` 自定位，不依赖 cwd）。

### S1 读实际文件（不许假设内容）
4. 用脚本实际抽取论文材料：
   ```bash
   python $SKILL_DIR/scripts/pdf_extract.py --pdf <材料路径> --out /app/work/extract
   ```
   - PDF → 页标记文本（`[PAGE n]`）+ 图片（`fig-p<页>-<序号>.png`）+ extract_report.json；
   - 文本/LaTeX → 直接读取；
   - PDF 加密/图片型扫描件/无 PDF 库 → 用 DSH 自带 PDF 读取能力转出文本（`.txt`
     Fallback），**如实记录工具**；仍不可读 → 按 S7 异常表处理，不得补造。
5. 通读抽取文本，记录论文元信息（标题/作者/venue）与各章页码。

### S2 抽实体与证据数据
6. 抽主线：问题（P）→ 方法（M）→ 证据（E）→ 结论（C）→ 局限（L），形成页序骨架。
7. 抽**页级证据**：每张图/表/公式/关键结论的编号、所在页码、图注或必要说明、
   数值与单位（数字、单位、方法名**逐字**从原文带出，绝不改写）。
8. 区分：论文原生图 vs 可从表格数字重建的图（reconstructed_chart）；
   **示意图不是实验数据**，不得混称。

### S3 生成 deck-spec.json（页级大纲）
9. 按 `references/TEMPLATE_GUIDE.md` §3 的 schema 编写 `/app/work/deck-spec.json`：
   - 每页：`claim`（一句话主张）+ 短语化 `bullets`（≤6 条、≤110 字/条）+ `figure/table`
     （ref 与论文一致）+ `notes`（过渡/强调/被问补充，**不复制页面文字**）
     + `evidence`（ref + page + quote）；
   - 无法定位证据的页 → `evidence_gap: true`（显式标注，不许假装有证据）；
   - `constraints.template_path` 指向组织方模板（case 材料中找到时）；
10. 结构上禁止"段落切片"页：任何页 `bullets` 超过信息上限或 `evidence` 为空且未标
    gap，即视为不合规，需重写。

### S4 构建可编辑源（.pptx）
11. 运行端到端入口：
    ```bash
    python $SKILL_DIR/scripts/main.py \
      --case /input/case.json --task /input/task.md \
      --spec /app/work/deck-spec.json --out /app/output
    ```
    `main.py` 依次：读 case → 定位材料/模板 → 抽取 → 构建 deck
    （组织方模板 placeholder-fill-only，或内置 16:9 学术版式）→ 备注写入 notes_slide
    → 生成证据映射页与 `evidence_mapping.md` → 重建图（PNG+SVG）→ PIL 近似预览
    → 组装 result.json（含全部 output_contract 字段）→ 自检并打印摘要。
12. 组织方模板适配遵守 `references/TEMPLATE_GUIDE.md` §2 三铁律：
    只填占位符、不碰 master、布局按名匹配→索引回退→内置版式。
    **不覆盖模板页脚/配色**；模板不可用 → 回退内置版式并记录。
    模板为起始演示（含起始页）时，`constraints.template_mode="replace"` 会移除
    起始页仅留版式/母版（记录 `starter_slides_removed`），默认 `"layouts"` 保留。
    页数受 `constraints.slide_count` 约束：自动“主线/证据映射”页可用
    `auto_outline`/`auto_evidence_slide` 开关控制；超限时
    `deck.page_budget_met=false` 且写入 uncertainty（S7 按“合并/精简”处置）。

### S5 导出渲染与验证
13. 无 PowerPoint/LibreOffice 时：预览为 **PIL 近似**（`preview-approx-*.png`），
    文件名与 `run_meta.rendered_with` 均如实标注 `pil-approximation`；
    若环境有 LibreOffice：`soffice --headless --convert-to pdf ...` 生成真 PDF
    放进 `/app/output/previews/`，并把 rendered_with 改为 `libreoffice`。
14. 用 python-pptx 重开 deck，核对页数、标题序列、备注存在、图表编号与 evidence 一致。
15. 独立校验：
    ```bash
    python $SKILL_DIR/scripts/validate.py --result /app/output/result.json \
      --out-dir /app/output --case /input/case.json
    # {"valid": true} 且 exit 0 才可视为通过
    ```

### S6 写 result.json（main.py 自动生成，Agent 复核）
16. 结果含：`case_id`（与 case.json 逐字一致）、`status`
    （completed/partial/failed 诚实词汇）、`output_contract` 回显（未知声明字段
    按类型给 `""/[]/{}`，**禁止 null**）、`deck`（含 template guard 与
    overflow_guard）、`evidence_mapping`、`previews`、`sources`（材料与抽取工具）、
    `uncertainty`、`change_records`、`run_meta`（含 rendered_with/skill_version/self_check）。
    契约细节以 `references/OUTPUT_CONTRACT.md` 为准。
17. 诚实性硬约束：不编造科学数据；数值/单位不改写；图缺失=显式占位框；
    预览近似如实标注；每步改动进 change_records。

预算纪律：总 64 次模型请求 / 900 秒 / 单响应 16384 tokens（含推理）。先 S1–S3
产出中间件，再逐段增量交付；脚本运行本身 <10s，不消耗模型预算大头。

## 5. 异常处理表（S7）

| 异常 | 识别 | 处置 | 记录 |
|-|-|-|-|
| 材料缺失 | case 指向的文件不存在 | 不补造；可产出仅元信息的 result | status=failed，sources.reason |
| PDF 加密 | 抽取失败且报 encrypted | 尝试空口令；失败则请 DSH 读取/用户补充，如实报告 | status=partial/failed，uncertainty |
| PDF 无文本层（扫描件） | 文本抽取为空 | 不 OCR 冒充；标注"图像型 PDF"，若有图片仍可引用 | uncertainty + sources.tool |
| 图/表抽不出 | images 为空或损坏 | 页面保留**显式占位框**（标注"需补齐，非原图"），不伪造 | figure.placed=placeholder |
| 模板不可用/损坏 | open 失败 | 内置学术版式回退 | deck.template.guard |
| 模板占位符不足 | 无 title/body/picture 占位符 | 仅内置版式下补画文本框；模板模式下绝不添加冲突对象 | layouts_used + uncertainty |
| 字体缺失 | 预览字体回退到 default | PIL default font 继续渲染预览，字体来源如实记录 | run_meta.preview_font |
| 页数超限 | spec.slides > 约束 | 截断或合并并记录；绝不静默丢弃证据页 | change_records + uncertainty |
| 重建图失败（无 matplotlib） | chart reason 字段 | 跳过图，保留引用与占位 | charts[].chart.reason |
| spec 缺失 | --spec 无可读文件 | 仅 `--demo` 允许骨架（标 skeleton）；正式运行必须由 Agent 写真实 spec | spec_source |

被降级的任何步骤都必须把"发生了什么 + 影响"写进 result.json 的
`uncertainty`/`change_records`，并在最终回复中说明限制。

## 6. 自查清单（S8，交付前逐条）

- [ ] 已读取真实 case.json / task.md / 论文文件，无内容来自标签假设；
- [ ] deck-spec.json 每页有 claim；bullets 为短语且 ≤6 条；evidence 或
      evidence_gap 二选一；
- [ ] 页上数字/单位/方法名/图号与论文逐字一致（抽查 3 处以上）；
- [ ] 页序可讲：问题→方法→证据→结论→局限；无"段落切片"页；
- [ ] notes 与页面文字分离，notes_slide 已写入（notes_separated=true）；
- [ ] 组织方模板：占位符填充、master 未动、页脚未覆盖；否则 template.guard 注明回退；
- [ ] /app/output 内存在：result.json（全部 output_contract 字段 + case_id）、
      academic_deck.pptx（可编辑）、preview-approx-*.png（或 LibreOffice PDF）、
      evidence_mapping.md；
- [ ] `validate.py` 输出 valid=true 且 exit 0；
- [ ] status/uncertainty/change_records 诚实，无编造软件状态或科学数据；
- [ ] 材料缺失/部分产物均已在回复中说明限制。

## 7. 限制（如实声明）

- 预览默认是 PIL 近似渲染，不等同于 PowerPoint/LibreOffice 渲染结果；
- PDF 图片抽取依赖 pdf 库可用性与版式，个别图可能只以占位框呈现；
- 模板为"占位符级"适配：复杂智慧型占位符（SmartArt 等）不重排；
- 本 Skill 生成内容与结构，不保证论文结论本身正确（结论以论文为准）。

## 8. 维护

- 版本：`scripts/main.py` 内 `VERSION`；运行方法/依赖/限制见 `README.md`；
- 修改记录维护在 result.json `change_records` 与 git 提交历史；
- 新案例可新增 `examples/` 下的最小示例（标注"示例，非正式案例"）验证接口。