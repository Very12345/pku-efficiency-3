# result-contract.md — 结果契约（结构化，v2）

本文件定义 Skill 每次运行后必须产出的 `result.json` 结构、「全部 output_contract
字段」的回显规则（四形态）、状态词汇与诚实性硬约束。`scripts/main.py` 按本契约生成，
`scripts/export_check.py` 按本契约做交付前导出检查（exit 0=通过）。

> 文件名与高分包（80.00）对齐：`references/result-contract.md`。本契约同时适用于
> 平台案例（`case.json` 声明 `output_contract`）与自带最小契约（见 §5）。

## 1. 顶层结构

```jsonc
{
  // —— 平台标识 ——
  "case_id": "平台给定案例 id（必须与 case.json 完全一致）",
  "task": "academic-presentation-from-paper",

  // —— 主结果状态（诚实词汇，只减不增）——
  "status": "completed | partial | failed",

  // —— 输入契约回显（见 §2 四形态）——
  "output_contract": { /* 与 case.json 中声明一致；未知字段按类型给 ''/[]/{} */ },

  // —— 可编辑演示文件 ——
  "deck": {
    "file": "academic_deck.pptx",
    "path": "academic_deck.pptx",
    "slide_count": 8,
    "editable": true,
    "notes_included": true,
    "notes_separated": true,           // 备注与页面文字分离生成（含封面/收尾页）
    "template": { "kind": "builtin|file", "path": "...", "basename": "...",
                  "guard": "...", "starter_slides_removed": 0 },
    "layouts_used": { "Title Slide": 1, "Title and Content": 6 },
    "overflow_guard": { "max_bullets": 6, "max_chars_bullet": 110 },
    "auto_slides": { "outline": true, "evidence": true }
  },

  // —— 页级证据映射（逐页映射表：md 复核 + json 机器可读）——
  "evidence_mapping": { "file": "evidence_mapping.md", "entries": 6, "gaps": [] },
  "evidence_map_json": "evidence_map.json",

  // —— 方案先行的 lint 门（CP1）——
  "spec_lint": { "valid": true, "problems": [], "counts": { "slides": 6 } },

  // —— 导出渲染 ——
  "previews": [
    { "slide": 0, "file": "preview-approx-cover.png", "kind": "pil-approximation" },
    { "slide": 1, "file": "preview-approx-001.png",  "kind": "pil-approximation" }
  ],
  "charts": [ /* reconstructed_chart 记录：{slide, ref, chart:{file,png,svg,note}} */ ],

  // —— 事实依据（不许编造）——
  "sources": [
    { "type": "paper_material", "path": "...", "pages_parsed": 12, "text_chars": 58432,
      "images_extracted": 4, "tool": "pymupdf" }
  ],

  // —— 不确定性与诚实说明 ——
  "uncertainty": ["预览为 PIL 近似渲染，非 PowerPoint/LibreOffice 渲染引擎结果；", "…"],

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
    "skill_version": "2.0.0",
    "checkpoints": { "cp1_spec_lint": true, "cp2_build": true, "cp3_export_check": true },
    "self_check": { "ok": true, "problems": [] }
  }
}
```

## 2. output_contract 回显规则（四形态）

平台案例的 `case.json` 在 `output_contract` 下声明期望字段，声明有四种形态，
**每种都必须回显、任何声明字段禁止为 null**：

| 形态 | case 声明示例 | result.json 处理 |
|-|-|-|
| ① 字段→类型提示（dict，值为 str/list 等） | `"title": "字符串"` | 有真实值写真实值；无则按容器给 `""` / `[]` / `{}` |
| ② 字段→说明（dict，值为任意描述） | `"render_state": "渲染记录"` | 有真实值写真实值；无则 `""` |
| ③ 布尔开关 | `"notes_separated": true` | 回显真实布尔（deck 是否分离备注） |
| ④ 字段清单（list of 名称） | `["title","slides"]` | 每个名称按 `""`（或可推断容器 `[]`）回显 |

- 语义字段（`title/main_claim/slides/notes_separated/render_state`）取本次运行的
  真实值（见 §1 语义映射），不写空值；
- 若案例同时声明 `case_id`，与 result.json 顶层 `case_id` 必须逐字一致；
- 本包自带最小契约：`output_contract` 缺省时按 §1 顶层结构输出。

## 3. 状态词汇（status）

| 值 | 含义 | 触发条件举例 |
|-|-|-|
| `completed` | 全部正常：材料可读、deck 生成、预览生成、**无未标注证据缺口、CP1 lint 通过** | 正常端到端跑通 |
| `partial` | 产物存在但有限制 | 有显式 `evidence_gap`；图无法提取（占位框标注）；重建图跳过；模板回退；**CP1 lint 有偏差但按 D 规则记录后继续** |
| `failed` | 无法产出可交付物 | 材料不可读/加密且无文本输入；case.json 损坏 |

状态只能如实填写；**不允许**把 partial/failed 标成 completed，也不允许在
uncertainty 缺省时假装无不确定项。

## 4. 诚实性硬约束（violations → 导出检查失败）

1. 数字、单位、方法名、结论表述必须与论文原文一致；"从 Table X 重建的图"
   必须在 `charts[].chart.note` 里声明 `reconstructed_from_table`；数值取自 spec
   且 spec 由 Agent 从原文导出，脚本不产生任何科学数据。
2. 图片缺失 → 显式占位框 + `uncertainty` 说明，**严禁**用示意图冒充论文原图。
3. 无 PowerPoint/LibreOffice 时预览一律 `kind=pil-approximation` 且
   `run_meta.rendered_with` 写明；文件名为 `preview-approx-*`。
4. 每个素材来源（PDF 抽取器/文本/模板）都进 `sources`；抽取工具不可用如实记录。
5. 每次改动进 `change_records`。
6. 模板为"占位符级"适配：只填占位符、不碰 master、不覆盖页脚/配色；回退必须记录。
7. **逐页证据映射**：`evidence_mapping.md` 表行数 = 声明 entries；每个 gap 在表中有
   "EVIDENCE GAP" 行；`evidence_map.json` 与 md 同源（同一 spec 生成）。

## 5. 硬性门（G1–G8，导出检查器逐条执行）

| 门 | 判定 | 违反后果 |
|-|-|-|
| G1 | `case_id` 非空且与 case 一致 | error |
| G2 | `output_contract` 声明字段全部回显、无 null | error |
| G3 | `status` ∈ {completed, partial, failed} | error |
| G4 | deck 文件存在、python-pptx 可重开、页数与 result 一致 | error |
| G5 | OOXML 容器健全（zip 必需部件存在 + XML 良构） | error |
| G6 | 每个声明的 preview 文件存在且标记近似 | error |
| G7 | evidence_mapping 文件存在且表行数 = entries | error（warning 级：gap 行缺失） |
| G8 | `run_meta.rendered_with` 有记录 | warning（不拦交付） |

## 6. 校验命令

```bash
python scripts/export_check.py --result <out>/result.json --out-dir <out> [--case <case.json>]
# 输出 {"valid": true|false, ...}；exit 0 通过 / 1 不通过
```