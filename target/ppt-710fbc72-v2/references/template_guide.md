# template_guide.md — 模板使用指南（母版 / 版式 / 占位符 / 主题）

本文档描述 v2 模板适配层（`pptx_toolkit.py` + `adopt_plan.py` + `adapt_pptx.py`）
的**模板规范**：母版–版式–占位符三层结构如何枚举、页型→版式如何分配、
主题字体/主题色如何继承与记录、字号阶梯、图表缩放、页脚页码与回退规则。
第三方模板与内置模板走同一套规则；"套用是否真实发生"以 `adopt_plan.json`
与 `template_audit` 的机器记录为准，不是口头承诺。

## 1. 模板解析链

```
case.json["template"]  →  case.json["starting_deck"]  →  <skill>/templates/builtin.pptx
```

- 模板缺失/损坏/加密：自动回退下一级，`template_errors` 记录每条失败原因；
- 打开成功后在 `adopt_plan.json.template` 记录**模板来源、来源标签
  （case_template/starting_deck/builtin）、画布尺寸、每个母版、每个版式、
  每个占位符（idx/name/宽高）**——这就是"母版/版式/占位符继承关系可查"的
  原始证据；
- `starting_deck` 视为需编辑的起始文件：替换其页面内容但**继续沿用其母版/
  版式/主题**（`dropped_original_slides` 记录被替换页数，写入 change_records）。

## 2. 母版 / 版式 / 占位符 三层结构（如何枚举）

1. **母版（master）**：`layout.slide_master` —— 主题字体/主题色/背景的宿主，
   一个模板通常 1 个母版；记录其 name。
2. **版式（layout）**：`prs.slide_layouts[idx]` —— 页面的骨架；记录 idx/name/
   所属母版/该版式全部占位符清单（idx/name/宽高）。
3. **占位符（placeholder）**：`layout.placeholders` / `slide.placeholders` ——
   真正可填的槽位；按 idx 与名称分类：
   - `title`（idx 范围 0–?，名称含 title/标题）；
   - `subtitle`（名称含 subtitle/副标题）；
   - **content body**（名称含 content/body/object/内容）——正文槽位；
   - `text`（Section Header / Comparison 的侧栏文字）——**不算正文**，防止
     正文被塞进窄列。

`scripts/pptx_toolkit.py` 的 `layout_scores()` 输出即这份枚举记录。

## 3. 页型 → 版式分配（_best_layout / adopt_plan page_assignments）

| 页型 | 需求占位符角色 |
|-|-|
| cover / thankyou | title（标题）+ subtitle（副标题） |
| 其余页 | title + content 风格 body（名称含 content/body/object/内容） |

打分要点：
- `text` 占位符不算 body；单 body 且宽度 ≥ 50% 画布宽 → 加分（整幅正文优先）；
- 无任何版式满足 → 退回 Blank/手工文本框，`layout_fallback_used=true` 记录，
  文本框几何按页计划决定，不做无依据摆位；
- **v2 两阶段**：`adopt_plan.py` 先在阶段一逐页算出版式分配（
  `page_assignments.recommended_layout_idx` 等，全部落在 adopt_plan.json），
  `adapt_pptx.py` 在阶段二按方案套用；方案与执行不一致时记入
  `template_audit.adopt_plan_deviations`，绝不静默改变。

## 4. 主题字体 / 主题色（v2 只读记录）

- 从模板包内 `ppt/theme/theme1.xml` 尽力读取 **latin 字体、ea（CJK）字体、
  主题色方案（dk1/lt1/accent1–6）**，记入 `adopt_plan.json.template.theme` 与
  `template_audit.theme`；读不到时 `theme.error` 如实记录，不影响构建；
- 内容写进占位符时**不覆盖 run 字体**（继承模板主题字体），只设置字号/
  加粗/强调色；手绘文本框（回退路径）才显式设字体名（CJK 优先
  Microsoft YaHei / SimHei，西文 Arial）；
- 预览（PIL）的字号回退链见 `scripts/common.py probe_font_candidates`
  （msyh→simhei→默认），字体名如实写入 render_log.json。

## 5. 字号 / 间距阶梯（common.fit_font_size）

- 阶梯：32 → 28 → 26 → 24 → 22 → 20 → 18 → 16 → 14 → 12（pt），只降不升；
- 每段按有效长度（CJK 全宽 1.0 / 西文 0.55）估算换行行数，行高 = 字号×1.28，
  与占位符真实宽高比对；
- 地板 12pt：再放不下就**报告溢出**（`layout.overflow` warn），绝不静默压到
  不可读；落到 <14pt 的盒子进 `layout.font_floor` 记录；
- 页脚/页码：封面外每页左下标题（≤45 字符）+ 右下页码，9pt 灰，
  `layout.footer_uniform` 校验全册一致（批量规则见 batch-rules.md）。

## 6. 图表适配（contain-fit / 图注 / 缺失占位）

- 等比 contain-fit：`scale = min(box_w/img_w, box_h/img_h)`，绝不拉伸；
  `figure_adjust` 与 `adopt_plan.json.figure_plan` 记录每图容器与比例；
- 图注行固定 `图N  标题  [来源: material.md:行]`，10pt 灰；表格用 python-pptx
  原生 table（表头深蓝底白字），表下注同图注格式；
- 源图缺失 → 灰底图位占位框（带图号+标题+"源图缺失，见 uncertainty"），
  标题与来源仍保留，不编造图片；
- 图号一致性由 audit `xref.figure_refs`（正文引用 ⊂ 图清单）与
  `xref.figure_placement`（图清单 ⊆ 结果页放置）双向检查。

## 7. 渲染 / 预览

无 LibreOffice/uno 时**不产伪 PDF**：预览为按同一页计划绘制的 PIL 示意图
（封面 + 全册联系表），PNG 命名与文件内均标注 `SCHEMATIC`，`render_log.json`
记录渲染后端与字体探测结果。真实像素级导出请用 PowerPoint/LibreOffice
打开 pptx 后导出 PDF（能力缺失如实记录，不静默成功）。

## 8. 复用指南

- 换模板：`--template <任意.pptx>`（自定义母版/版式/占位符均可审计+套用）；
- 换页数/时长/语言：`case.json` 的 `slide_count` / `duration_minutes` /
  `language`（en 时页型/标题/讲义自动切英文）；
- 单独生成适配方案：`python scripts/adopt_plan.py --content <out>/content.json
  --spec <out>/spec.json --builtin templates/builtin.pptx --out adopt_plan.json`；
- 重新生成内置模板：`python scripts/make_template.py --out templates/builtin.pptx`；
- 校验：`python scripts/validate_result.py --case <case> --result <out>/result.json` +
  `python scripts/check_contract.py --result <out>/result.json --out-dir <out> --case <case>`。

## 9. 已知限制（诚实说明）

- 主题色/主题字体读 theme1.xml 为**只读记录**；如需改写主题（换色板）不在
  本 Skill 范围；
- CJK 文本行高为估算，极端字体环境下可能与 PowerPoint 实际排版有偏差，
  以 audit 溢出报告为准；
- 复杂智慧型占位符（SmartArt、图表图表对象）不重排；预览非像素级导出；
- 动画/切换效果不在本 Skill 范围。