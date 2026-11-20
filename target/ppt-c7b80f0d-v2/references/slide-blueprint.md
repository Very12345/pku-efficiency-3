# slide-blueprint.md — 论文→PPT 页面蓝图 + 页级大纲 schema（v2）

> 文件名与高分包（80.00）对齐：`references/slide-blueprint.md`。
> 本文档是全流程的规划依据：先按 §1 把论文结构映射为页面蓝图，再按 §3 的
> deck-spec schema 落盘，`scripts/spec_lint.py` 做结构性 lint，`deckgen` 按蓝图实现。

## 1. 论文结构 → 页面结构的蓝图映射（Blueprint）

学术 PPT 不是"把段落切成行"，而是一次结构重写。下列映射给出"论文章节 →
页面骨架"的**默认蓝图**；Agent 依据案例实际内容增删页，但必须保持
问题→方法→证据→结论→局限的**可讲页序**，且每页都能回溯论文定位。

| 论文/材料内容 | 蓝图页（默认） | 布局 hint | 本页必须挂的证据 | 备注职责 |
|-|-|-|-|-|
| 标题/作者/venue/摘要首句 | 封面（Title） | `title` | 摘要有引言出处 | 开场句 + 被问背景的出处 |
| 引言/动机/相关工作 §1 | 研究问题（Problem） | `content` | §1 关键句 + 页码 | 讲痛点，被问基线引段落 |
| 方法/系统设计 §2（可能 2-3 页） | 方法（Method ×N） | `content` / `figure` | §2 小节 + Fig 编号 | 强调关键设计决策 |
| 核心结果 §3 图/表 | 证据（Evidence ×N） | `figure` / `table` | Fig. 编号 / Table 编号 + 数据定位 | 逐图逐表讲，数值不改写 |
| 讨论/结论 §4 | 结论（Conclusion） | `content` | §4 结论句 | 收束到贡献 |
| 局限/展望 §4/§5 | 局限（Limitations） | `content` | 局限原文 | 被问"能否上线"时引用 |
| 参考文献 | 谢谢/讨论页（Closing） | `reference` | 关键引用编号 | 引导提问回证据映射页 |

**蓝图规则（BL-1…BL-4，spec_lint 强制）**：
- BL-1　每页一个 `claim`（一句话主张），不是段落标题；
- BL-2　`bullets` 为短语，≤6 条/页、字数和 ≤110（CJK 加权），禁止整段粘贴；
- BL-3　每页 `evidence`（图/表/章节 + 页码）或显式 `evidence_gap: true`，二选一；
- BL-4　页序按上表骨架推进，出现"段落切片页"（无主张、顺序照搬正文）即不合规。

## 2. 页级证据映射表（逐页映射表格式）

蓝图落盘后，`main.py` 从 deck-spec 自动生成**两种同源产物**：
`evidence_mapping.md`（人复核，markdown 表）与 `evidence_map.json`（机器可读）。

```markdown
# 页级证据映射（复核用）

| 页 | 标题 | 主张（一句话） | 证据定位 | 状态 |
|---|---|---|---|---|
| P01 | 研究问题：评语通用、缺上下文 | 代码评审自动化受限于… | §1 Introduction (p.1) | mapped |
| P02 | 方法：索引→检索→条件生成 | ExampleNet 用三阶段… | §2 Method (p.2) | mapped |
| P03 | 证据：检索量 vs 质量 | 重建图：ROUGE-L F1 先升后降 | Table 1 (p.3); Fig. 1 (p.3) | mapped |
| P04 | 局限 | 局限明确：合成基准、索引内存… | §4 Limitations (p.4) | gap |
```

`evidence_map.json` 每行：`{page, title, claim, location, status, evidence:[{
type, ref, page, quote}]}` —— 与 md 同源（同一 spec 的 `slides`），
导出检查器（export_check.py）校验二者一致性。

## 3. deck-spec.json schema（= 页级大纲模板，可直接复用）

```jsonc
{
  "case_id": "与 case.json 一致",
  "deck_title": "汇报标题（即论文标题）",
  "output_name": "academic_deck",                    // .pptx 文件名（可选）
  "meta": {
    "title": "论文标题", "authors": "作者", "venue": "会议/期刊", "date": "日期",
    "audience": "对象（评审/组会/答辩…）", "duration_minutes": 15
  },
  "takeaway": "整体一句话结论",
  "limitations": "局限与展望",
  "constraints": {
    "slide_count": 8,                      // 页数上限；超限自动标 page_budget_met=false
    "template_path": "模板绝对路径（推荐）或相对路径",
    "template_mode": "layouts | replace",  // starter deck 保留/替换（见 §4）
    "auto_outline": true,                  // 自动“汇报主线”页
    "auto_evidence_slide": true            // 自动“证据映射”页
  },
  "slides": [
    {
      "page": 1,
      "layout_hint": "title|section|content|figure|table|two-content|reference",
      "claim": "本页一句话主张（页级核心，非段落）",
      "title": "页标题（短，≤40 字）",
      "bullets": ["短语要点...", ["二级要点", 1]],   // 短语化，≤6 条/页
      "figure": {
        "ref": "Fig. 1", "label": "图注（论文原文，未改写）",
        "source_page": "p.3",
        "kind": "paper_figure | reconstructed_chart",
        "image": "相对路径（原图或重建图 PNG）"
      },
      "table": { "ref": "Table 2", "source_page": "p.5",
                 "rows": [["header1","header2"],["v1","v2"]] },
      "notes": "讲解备注：过渡/强调/被问补充证据；不得复制页面文字",
      "evidence": [
        { "type": "figure|table|section|claim", "ref": "Fig. 1",
          "page": "p.3", "quote": "论文原文短引（可选）" }
      ],
      "evidence_gap": false                 // 无法定位证据时必须 true
    }
  ],
  "skeleton": false                          // true = 自动骨架（仅 demo）
}
```

用法：用 `python scripts/spec_lint.py --spec <deck-spec.json>` 做 CP1 lint；
lint 通过前不得进入生成（偏差须按 SKILL 决策规则 D4 记录后继续）。

## 4. 模板适配与重建图（沿用 v1 规则，v2 实现位置变化）

- 模板判定顺序与"三条铁律"：`scripts/deckgen.py`（原 deck_builder.py，职责并入
  deckgen 层）：只填占位符（title idx0/11、body idx1/2、picture type18）、
  不碰 master（`Presentation(path)` + add_slide）、布局按名匹配→索引回退→内置版式；
- 起始演示（starter deck）`template_mode="replace"` 移除起始页仅留版式/母版，
  移除数记录 `starter_slides_removed`；
- 字体：`scripts/ooxml_kit.py` 的 `set_theme_fonts`（主题 major/minor 字体，CJK 安全）
  + `set_shape_font`（latin + east-asian 双 typeface）；预览仍为 PIL 近似；
- 重建图：`scripts/assetkit.make_chart`（matplotlib → PNG + 可编辑 SVG，缺失回退），
  `charts[].chart.note` 标注 `reconstructed_from_table`；数值取自 spec，不产生科学数据。