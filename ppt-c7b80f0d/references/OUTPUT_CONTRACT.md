# OUTPUT_CONTRACT.md — result.json 契约（唯一评分产物）

本文件定义 Skill 每次运行后必须产出的 `result.json` 结构、「全部 output_contract
字段」的回显规则（四形态）、状态词汇与诚实性硬约束。

- `scripts/main.py` 按本契约**生成** result.json；
- `scripts/check_contract.py` 按本契约 §1 的顶层字段清单**逐字段核对**（exit 0 = 全覆盖）；
- `scripts/export_check.py` 按本契约做交付前导出检查（exit 0 = 通过，G1–G8）。

契约同时适用于平台案例（`case.json` 声明 `output_contract`）与自带最小契约（§5）。

## 1. 顶层字段清单（**必须全部出现**，`check_contract.py` 逐条核对）

| 字段 | 类型 | 含义 / 生成位置 |
|-|-|-|
| `case_id` | str | 与 `case.json` 的 `case_id` **逐字一致**（G1） |
| `task` | str | 固定为 `academic-presentation-from-paper` |
| `status` | str | `completed` / `partial` / `failed`（§3 词汇表，G3） |
| `output_contract` | obj | 案例声明字段的回显容器（四形态见 §2） |
| `deck` | obj 或 null | 可编辑演示文件记录（file/path/slide_count/editable/notes_*/template/layouts_used/overflow_guard/auto_slides） |
| `evidence_mapping` | obj | 页级证据映射（file/entries/gaps），md 于人复核 |
| `evidence_map_json` | str 或 null | 机器可读映射文件名（与 md 同源） |
| `spec_lint` | obj | CP1 结构性 lint 结果（valid/problems/counts） |
| `previews` | list | 渲染预览记录 `[{slide,file,kind}]`，无 Office 引擎时 `kind=pil-approximation` |
| `charts` | list | 重建图记录 `[{slide,ref,chart}]`（`reconstructed_from_table` 声明） |
| `sources` | list | 事实依据：材料路径、抽取工具、页数/字数/图片数 |
| `uncertainty` | list | 不确定性与降级说明（**不得留空装作无问题**） |
| `change_records` | list | 修改记录 `[{time,what,why}]` |
| `run_meta` | obj | 运行元信息（python/库版本/rendered_with/skill_version/checkpoints/self_check） |
| `title` | str | 契约语义字段：deck 标题（真实值） |
| `main_claim` | str | 契约语义字段：全文一句话结论（真实值） |
| `slides` | list | 契约语义字段：每页 `{page,title,claim}` |
| `render_state` | obj | 契约语义字段：previews/rendered_with/deck_file/evidence_mapping_file |
| `notes_separated` | bool | 契约语义字段：备注与页面文字是否分离生成 |

> 契约回显字段（`title`/`main_claim`/`slides`/`render_state`/`notes_separated` 及案例
> 额外声明的字段）由 `main.py:apply_output_contract()` 追加到顶层；**任何声明字段禁止为 null**。

参考形态（真实运行时字段值以本次案例为准，路径均为运行期相对/环境路径）：

```jsonc
{
  "case_id": "平台给定案例 id（必须与 case.json 完全一致）",
  "task": "academic-presentation-from-paper",
  "status": "completed | partial | failed",
  "output_contract": { /* 与 case.json 中声明一致；未知字段按类型给 ''/[]/{} */ },
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
  "evidence_mapping": { "file": "evidence_mapping.md", "entries": 6, "gaps": [] },
  "evidence_map_json": "evidence_map.json",
  "spec_lint": { "valid": true, "problems": [], "counts": { "slides": 6 } },
  "previews": [
    { "slide": 0, "file": "preview-approx-cover.png", "kind": "pil-approximation" },
    { "slide": 1, "file": "preview-approx-001.png",  "kind": "pil-approximation" }
  ],
  "charts": [ /* {slide, ref, chart:{file,png,svg,note}} */ ],
  "sources": [
    { "type": "paper_material", "path": "<运行期输入路径>", "pages_parsed": 12,
      "text_chars": 58432, "images_extracted": 4, "tool": "pymupdf" }
  ],
  "uncertainty": ["预览为 PIL 近似渲染，非 PowerPoint/LibreOffice 渲染引擎结果；", "…"],
  "change_records": [
    { "time": "YYYY-MM-DDTHH:MM:SS+0800", "what": "开始运行", "why": "case xxx" }
  ],
  "run_meta": {
    "python": "3.13.9", "platform": "<运行时平台串>", "ppt_version": "1.0.2",
    "pillow_version": "12.3.0", "matplotlib_available": true,
    "pdf_tools": {"fitz": true, "pypdf": true, "pdfplumber": true},
    "rendered_with": "pil-approximation (no PowerPoint/LibreOffice attached)",
    "preview_fidelity": "approximate — PIL re-composition, not PowerPoint rendering",
    "preview_font": "<运行时探测到的字体路径，未探测到则为 null>",
    "spec_source": "<--spec 路径 | auto-skeleton>",
    "duration_seconds": 1.34,
    "skill_version": "2.1.0",
    "checkpoints": { "cp1_spec_lint": true, "cp2_build": true, "cp3_export_check": true },
    "self_check": { "ok": true, "problems": [] }
  },
  "title": "…", "main_claim": "…", "slides": [ /* … */ ],
  "render_state": { /* … */ }, "notes_separated": true
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
   且 spec 由 Agent 从原文导出，**脚本不产生任何科学数据**。
2. 图片缺失 → 显式占位框 + `uncertainty` 说明，**严禁**用示意图冒充论文原图。
3. 无 PowerPoint/LibreOffice 时预览一律 `kind=pil-approximation` 且
   `run_meta.rendered_with` 写明；文件名为 `preview-approx-*`。
4. 每个素材来源（PDF 抽取器/文本/模板）都进 `sources`；抽取工具不可用如实记录。
5. 每次改动进 `change_records`。
6. 模板为"占位符级"适配：只填占位符、不碰 master、不覆盖页脚/配色；回退必须记录。
7. **逐页证据映射**：`evidence_mapping.md` 表行数 = 声明 entries；每个 gap 在表中有
   "EVIDENCE GAP" 行；`evidence_map.json` 与 md 同源（同一 spec 生成）。
8. 不编造软件状态：`matplotlib_available`/`pdf_tools`/`rendered_with` 都来自真实探测。

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

## 6. 校验命令（均在任意 cwd 下可用）

```bash
python "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json \
  --contract "$SKILL_DIR/references/OUTPUT_CONTRACT.md"          # §1 顶层字段覆盖，exit 0/1
python "$SKILL_DIR/scripts/export_check.py" --result <out>/result.json \
  --out-dir <out> [--case /input/case.json]                      # G1–G8，exit 0/1
```
