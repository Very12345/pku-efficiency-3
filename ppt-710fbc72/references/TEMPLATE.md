# TEMPLATE.md — 模板适配层规则与复用指南

本文档描述 pptxbuild 的模板适配规则、页型版式约定、字号/间距阶梯、图表
缩放策略与失败处置。第三方模板与内置模板都走同一套规则。

## 1. 模板解析链

```
case.json["template"]  →  case.json["starting_deck"]  →  <skill>/templates/builtin.pptx
```

- 模板缺失或不可解析：自动回退下一级，`template_errors` 记录原因；
- 打开成功后在 `template_audit.layouts` 记录**母版名、每个版式、每个占位符
  （idx/name/宽高）**，这就是"母版/版式/占位符继承关系可查"的原始记录；
- `starting_deck` 视为需编辑的起始文件：打开后替换其页面内容，但继续沿用
  其母版/版式/主题（`dropped_original_slides` 记录被替换页数，写入
  `change_records`）。

## 2. 版式选择（_best_layout）

按页型给出需求角色，逐版式打分，取最高分：

| 页型 | 需求占位符角色 |
|-|-|
| cover / thankyou | title（标题）+ subtitle（副标题） |
| 其余页 | title + content 风格 body（名称含 content/body/object/内容） |

打分要点：
- `text`/`Text Placeholder`（Section Header、Comparison 的侧栏文字）**不算** body，
  防止正文被塞进窄列；
- 单 body 且宽度 ≥ 50% 画布宽 → 加分（整幅正文优先）；
- 无任何版式满足 → 退回 Blank/手工文本框（`layout_fallback_used=true` 记录），
  文本框几何按页计划决定，不做无依据摆位。

主题继承：内容写进占位符时**不覆盖 run 字体**（继承模板主题字体），只设置
字号/加粗/强调色；手绘文本框（回退路径）才显式设字体名（CJK 优先
Microsoft YaHei / SimHei，西文 Arial）。

## 3. 页型与页计划（deckplan）

固定骨架：cover → background(问题) → methods → results×N（每图/表一页）→
discussion → limitations → conclusion → **evidence_map（附录：页→来源定位表）**
→ thankyou；agenda 在页数充裕时插入。页数超目标时的确定性裁剪顺序：
1) 合并 discussion+limitations；2) 删除 agenda；3) 合并最后两张结果页。

每页携带：`page_type / title / claims / figure_refs / table_refs /
evidence[{claim, loc}] / notes`（讲义含建议时长：总分钟÷页数）。

## 4. 字号 / 间距阶梯（common.fit_font_size）

- 阶梯：32 → 28 → 26 → 24 → 22 → 20 → 18 → 16 → 14 → 12（pt），只降不升；
- 每段按有效长度（CJK 全宽 1.0 / 西文 0.55）估算换行行数，行高 = 字号×1.28，
  与占位符真实宽高比对；
- 地板 12pt：再放不下就**报告溢出**（`layout.overflow` warn），绝不静默
  压到不可读；落到 <14pt 的盒子进 `layout.font_floor` 记录。
- 页脚/页码：封面外每页左下标题（≤45 字符）+ 右下页码，9pt 灰色，
  `layout.footer_uniform` 校验全册一致。

## 5. 图表适配（_contain_fit / _add_figure）

- 等比 contain-fit：`scale = min(box_w/img_w, box_h/img_h)`，仅给目标容器传入
  宽度或高度时另一维自动等比，**绝不拉伸**；`figure_adjust` 记录 scale；
- 图注行固定 `图N  标题  [来源: material.md:行]`，10pt 灰；
- 源图缺失 → 灰底图位占位框（带图号+标题+"源图缺失，见 uncertainty"），
  标题与来源仍保留，不编造图片；
- 表格用 python-pptx 原生 table（表头深蓝底白字），表下注同图注格式；
- 图号一致性由 audit `xref.figure_refs`（正文引用 ⊂ 图清单）与
  `xref.figure_placement`（图清单 ⊆ 结果页放置）双向检查。

## 6. 渲染 / 预览

无 LibreOffice/uno 时**不产伪 PDF**：预览为按同一页计划绘制的 PIL 示意图
（封面 + 全册联系表），PNG 命名与文件内均标注 `SCHEMATIC`，`render_log.json`
记录渲染后端与字体探测结果（缺字体真实记录回退）。真实像素级导出请用
PowerPoint/LibreOffice 打开 pptx 后导出 PDF。

## 7. 复用指南

- 换模板：`--template <任意.pptx>`（含自定义母版/版式/占位符的模板均可审计+套用）；
- 换页数/时长：`case.json` 的 `slide_count` / `duration_minutes`（或 task.md 说明）；
- 换语言：`language: en` 时页型/标题/讲义自动切英文；
- 重新生成内置模板：`python scripts/make_template.py --out templates/builtin.pptx`；
- 校验：`python scripts/validate_result.py --case <case> --result <out>/result.json`。

## 8. 已知限制（诚实说明）

- 主题色/主题字体通过占位符继承保持，未解析主题 XML 取色板（如需取用
  模板强调色可后续扩展）；
- CJK 文本行高为估算，极端字体环境下可能与 PowerPoint 实际排版有偏差，
  以 audit 溢出报告为准；
- 预览非像素级导出；动画/切换效果不在本 Skill 范围。