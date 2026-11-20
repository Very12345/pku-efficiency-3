# OUTPUT_CONTRACT.md — result.json 契约（结构化）

本文件定义 Skill 每次运行后必须产出的 `result.json` 结构、"全部 output_contract 字段"
的映射规则、状态词汇与诚实性约束。`scripts/main.py` 按本契约生成，
`scripts/validate.py` 按本契约做独立自检（exit 0=通过）。

## 1. 顶层结构

```jsonc
{
  // —— 平台标识 ——
  "case_id": "平台给定案例 id（必须与 case.json 完全一致）",
  "task": "academic-presentation-from-paper",

  // —— 主结果状态（诚实词汇，只减不增）——
  "status": "completed | partial | failed",

  // —— 输入契约回显（见 §2）——
  "output_contract": { /* 与 case.json 中声明一致；未知字段按类型给 ''/[]/{} */ },

  // —— 可编辑演示文件 ——
  "deck": {
    "file": "academic_deck.pptx",
    "path": "academic_deck.pptx",
    "slide_count": 8,
    "editable": true,
    "notes_included": true,
    "notes_separated": true,           // 备注与页面文字分离生成
    "template": { "kind": "builtin|file", "path": "...", "basename": "...", "guard": "..." },
    "layouts_used": { "Title Slide": 1, "Title and Content": 6 },
    "overflow_guard": { "max_bullets": 6, "max_chars_bullet": 110 }
  },

  // —— 页级证据映射 ——
  "evidence_mapping": { "file": "evidence_mapping.md", "entries": 6, "gaps": [] },

  // —— 导出渲染 ——
  "previews": [
    { "slide": 0, "file": "preview-approx-cover.png", "kind": "pil-approximation" },
    { "slide": 1, "file": "preview-approx-001.png",  "kind": "pil-approximation" }
  ],
  "charts": [ /* reconstructed_chart 的记录：{slide, ref, chart:{file,png,svg,note}} */ ],

  // —— 事实依据（不许编造）——
  "sources": [
    { "type": "paper_material", "path": "...", "pages_parsed": 12, "text_chars": 58432,
      "images_extracted": 4, "tool": "pymupdf" }
  ],

  // —— 不确定性与诚实说明 ——
  "uncertainty": ["预览为 PIL 近似渲染，非 PowerPoint/LibreOffice 渲染引擎结果；",
                  "某些页含显式证据缺口：……"],

  // —— 修改记录 ——
  "change_records": [
    { "time": "2026-11-20T22:30:00+0800", "what": "开始运行", "why": "case xxx" }
  ],

  // —— 运行元信息 ——
  "run_meta": {
    "python": "3.13.9", "platform": "...", "ppt_version": "1.0.2",
    "pillow_version": "12.3.0", "matplotlib_available": true,
    "pdf_tools": {"fitz": true, "pypdf": true, "pdfplumber": true},
    "rendered_with": "pil-approximation (no PowerPoint/LibreOffice attached)",
    "preview_fidelity": "approximate — PIL re-composition, not PowerPoint rendering",
    "preview_font": "C:/Windows/Fonts/msyh.ttc",
    "spec_source": "<--spec 路径 | auto-skeleton>",
    "duration_seconds": 1.34,
    "skill_version": "1.0.0",
    "self_check": { "ok": true, "problems": [] }
  }
}
```

## 2. output_contract 回显规则（全部字段）

- 平台案例的 `case.json` 会在 `output_contract` 下声明期望字段（名称/类型/容器）。
  **result.json 必须把每个声明的字段原样回显到顶层**，规则与历史验证一致：
  - 有真实值 → 写真实值（数值不得改写）；
  - 无真实值但契约声明了容器 → 写类型对应空值：字符串 `""`、列表 `[]`、字典 `{}`；
  - **任何契约字段禁止为 `null`**。
- 若案例同时声明了 `case_id`，二者必须逐字一致。
- 本包自带默认契约（`output_contract` 缺省时按 §1 顶层结构输出）。

## 3. 状态词汇（status）

| 值 | 含义 | 触发条件举例 |
|-|-|-|
| `completed` | 全部正常：材料可读、deck 生成、预览生成、**无未标注证据缺口** | 正常端到端跑通 |
| `partial` | 产物存在但有限制 | 有显式 `evidence_gap`；图无法提取（以占位框标注）；重建图表被跳过；模板不可用已回退并记录 |
| `failed` | 无法产出可交付物 | 材料不可读/加密且无文本输入；case.json 损坏 |

状态只能如实填写；**不允许**把 partial/failed 标成 completed，也不允许在
uncertainty 缺省时假装无不确定项。

## 4. 诚实性硬约束（violations → 校验失败）

1. 数字、单位、方法名、结论表述必须与论文原文一致；"从 Table X 重建的图"
   必须在 `charts[].chart.note` 里声明 `reconstructed_from_table`，数值取自 spec
   且 spec 必须由 Agent 从原文导出，脚本不产生任何科学数据。
2. 图片缺失 → 显式占位框 + `uncertainty` 说明，**严禁**用示意图冒充论文原图。
3. 无 PowerPoint/LibreOffice 时预览一律 `kind=pil-approximation` 且
   `run_meta.rendered_with` 写明；文件名为 `preview-approx-*`。
4. 每个素材来源（PDF 抽取器/文本/模板）都进 `sources`，抽取工具不可用如实记录。
5. 每次改动进 `change_records`。

## 5. 校验命令

```bash
python scripts/validate.py --result <out>/result.json --out-dir <out> [--case <case.json>]
# 输出 {"valid": true|false, ...}；exit 0 通过 / 1 不通过
```