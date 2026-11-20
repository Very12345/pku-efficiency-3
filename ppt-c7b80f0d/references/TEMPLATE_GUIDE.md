# TEMPLATE_GUIDE.md — 模板适配与页级大纲（deck-spec.json schema）

## 1. 模板判定顺序（Skill 运行期）

1. `spec.constraints.template_path`（Agent 在案例材料中发现组织方模板后写入）；
2. 缺省时读 `case.json` 的 `template.path` / `template` 字段；
3. 路径是目录 → 在其中找 `*.pptx / *.potx`（再 `.ppt`）；
4. 都不可用 → **内置 16:9 学术版式**（`deck_builder.ACADEMIC_THEME`），
   并在 result.json 的 `deck.template.guard` 中如实记录回退。

模板文件不可读/损坏 → 回退内置版式，`uncertainty` 记录原因，不中断运行。

## 2. 组织方模板的三条铁律

| 铁律 | 做法 | 代码位置 |
|-|-|-|
| 只填占位符 | title(idx 0/11)、body(idx 1/2)、picture(type 18) 占位符各自填充；**不新增与模板冲突的对象** | `deck_builder._fill_title_placeholder/_fill_body_placeholder/_place_figure` |
| 不碰 master | 不改 `prs.slide_masters`；配色、页脚、母版图形原样保留 | `open_adapted_presentation` 仅 `Presentation(path)` + add_slide |
| 布局按名匹配 | 依据 `layout_hint` 关键词匹配 layout 名（title/cover、section/divider、figure/picture、table/chart、content/body、reference/thanks…）；无匹配→按 hint 索引回退→首张可用布局 | `deck_builder.LAYOUT_KEYWORDS/_match_layout_index` |

**起始演示（starter deck）**：模板文件可能自带若干起始页。`constraints.template_mode`：
- `"layouts"`（默认）：保留起始页，在其后追加本 Spec 的页；
- `"replace"`：移除起始页，仅复用其版式与母版（正确做法——起始页内容不是
  论文内容，不应混入成品）；移除数量记入 `deck.template.starter_slides_removed`。

内置版式页脚（页码/标题）只在**非模板**模式下添加（`_add_footer`），避免覆盖
组织方页脚。

## 3. deck-spec.json schema（= 页级大纲模板，他人可直接复用）

```jsonc
{
  "case_id": "与 case.json 一致",
  "deck_title": "汇报标题（即论文标题）",
  "output_name": "academic_deck",                    // .pptx 文件名（可选）
  "meta": {
    "title": "论文标题",
    "authors": "作者",
    "venue": "会议/期刊", "date": "日期",
    "audience": "对象（评审/组会/答辩…）",
    "duration_minutes": 15
  },
  "takeaway": "整体一句话结论",
  "limitations": "局限与展望",
  "constraints": {
    "slide_count": 8,                      // 页数上限；超限会自动标 page_budget_met=false
    "template_path": "模板绝对路径（推荐）或相对路径（按 spec 目录→case 目录→输出目录解析）",
    "template_mode": "layouts | replace",  // starter deck 的保留/替换（见 §2）
    "auto_outline": true,                  // 自动“汇报主线”页（默认 true）
    "auto_evidence_slide": true            // 自动“证据映射”页（默认 true；页数吃紧时关掉）
  },
  "slides": [
    {
      "page": 1,                                     // 页序 = 讲解顺序
      "layout_hint": "title|section|content|figure|table|two-content|reference",
      "claim": "本页一句话主张（页级核心，非段落）",
      "title": "页标题（短，≤40 字）",
      "bullets": ["短语要点...", ["二级要点", 1]],   // 短语化，≤6 条/页
      "figure": {
        "ref": "Fig. 1",                            // 论文图编号
        "label": "图注（来自论文，未改写）",
        "source_page": "p.3",
        "kind": "paper_figure | reconstructed_chart",
        "image": "相对路径（抽取出的原图，或重建图 PNG）"
      },
      "table": { "ref": "Table 2", "source_page": "p.5",
                 "rows": [["header1","header2"],["v1","v2"]] },
      "notes": "讲解备注：过渡/强调点/被问到时补充的证据；不得复制页面文字",
      "evidence": [
        { "type": "figure|table|section|claim", "ref": "Fig. 1",
          "page": "p.3", "quote": "论文原文短引（可选）" }
      ],
      "evidence_gap": false                          // 无法定位证据时必须 true
    }
  ],
  "skeleton": false                                   // true = 自动骨架（仅 demo）
}
```

规则：
- **每页必须有 `claim` 与 `evidence`（或显式 `evidence_gap: true`）**——这是
  结构性强制，防止 Agent 交"段落切片"页。
- `bullets` 是**短语**不是整句段落；超长会被截断并记录（overflow_guard）。
- `notes` 与页面文字分离：写在 `notes_slide`，供演讲者视图使用。
- 图/表编号与论文一致；数值与单位由 Agent 从原文带出，脚本不生成科学数据。

## 4. 重建图（reconstructed_chart）

当论文提供数值表格、且页面主张需要可视化该数据时：

```jsonc
"figure": {
  "ref": "Fig. 3（重建）", "kind": "reconstructed_chart", "source_page": "p.6",
  "data": { "categories": ["A","B","C"],
            "series": [ { "name": "本文方法", "values": [0.92, 0.88, 0.95], "kind": "bar" } ] }
}
```

脚本产出 `chart-<ref>.png`（嵌入 pptx）+ `chart-<ref>.svg`（可编辑源），
并在 `charts[].chart.note` 标注 `reconstructed_from_table`。
matplotlib 缺失 → 跳过并如实记录，**不以手绘冒充**。

## 5. 字体与渲染

- `.pptx` 内中英文字体统一写 `latin + east-asian` 双 typeface
  （`deck_builder._set_run_font`，默认 Microsoft YaHei / Calibri），换机打开不丢中文字体。
- 预览：PIL 近似渲染（`preview.py`），字体按
  `msyh → simhei → simsun → arial → DejaVu → PIL default` 回退；
  预览文件一律 `preview-approx-*` + 水印，诚实声明不是 PowerPoint 渲染。
- 导出 PDF：本包不假装能转换；如环境有 LibreOffice，可
  `soffice --headless --convert-to pdf <deck>.pptx`，并把 PDF 放进 `previews/`，
  run_meta.rendered_with 记录为 `libreoffice`（本仓库测试环境无 LibreOffice，
  默认按 PIL 近似。）