# EXPECTED-OUTPUT.md — 示例案例上应产出的清单（文字形态）

> 用途：替代随包携带的二进制示例产物。本文件用**文字**列出"在
> `examples/case.json` 上跑一次 `scripts/main.py` 应得到什么"，
> 使示例可被复核而不必把 `.pptx` / `.png` / `.svg` 放进技能资源目录
> （技能资源只允许 UTF-8 文本文件）。
>
> 复跑命令与依赖见 `../README.md`；实际运行结果副本（文本部分）见 `../output/`。

## 1. 输出文件清单（`--out <out>` 目录内，共 13 个）

| 文件 | 形态 | 说明 |
|-|-|-|
| `result.json` | 文本 | **唯一评分产物**：§2 的契约字段全部出现 |
| `academic_deck.pptx` | 二进制（运行时生成） | 可编辑演示源；本示例 8 页：封面 + 6 内容页 + 收尾（`auto_outline`/`auto_evidence_slide` 在本示例 spec 中关闭） |
| `preview-approx-cover.png` + `preview-approx-001..006.png` | 二进制（运行时生成） | 7 张 PIL 近似预览（**非** PowerPoint/LibreOffice 渲染），文件名带 `approx` |
| `evidence_mapping.md` | 文本 | 逐页证据映射表（人复核），本示例 6 行 = `entries` |
| `evidence_map.json` | 文本 | 同上，机器可读（与 md 同源） |
| `chart-Fig_1.png` | 二进制（运行时生成） | 由 spec 声明的 Table 1 数字**重建**的图（`reconstructed_from_table`） |
| `chart-Fig_1.svg` | 文本 | 重建图的可编辑矢量源（本包不携带，运行时生成） |

> 说明：`.pptx`/`.png` 属于"运行时产物"，题面明确允许它们在运行期以二进制形态存在
> （`Runtime artifacts may be binary and are retained independently of final JSON validity`），
> 但它们**不得作为技能资源随包提交** —— 因此本目录只保留文字清单与文本结果副本。

## 2. `result.json` 顶层契约字段（本示例实际取得的值，摘要）

| 字段 | 本示例期望值（形态） |
|-|-|
| `case_id` | `example-ppt-c7b80f0d`（与 `case.json` 逐字一致） |
| `task` | `academic-presentation-from-paper` |
| `status` | `completed`（无缺口、CP1 通过；任何降级都必须改成 `partial`/`failed`） |
| `output_contract` | case 声明的 6 个字段（title/main_claim/slides/evidence_mapping/render_state/notes_separated）原样回显 |
| `deck` | `file=academic_deck.pptx`、`slide_count=8`、`editable=true`、`notes_included=true`、`notes_separated=true`、`template.kind=file`、`template.starter_slides_removed=1`、`layouts_used={"Title Slide":1,"Title and Content":5,"Figure Slide":1,"Reference Slide":1}`、`theme_fonts.applied=true` |
| `evidence_mapping` | `file=evidence_mapping.md`、`entries=6`、`gaps=[]` |
| `evidence_map_json` | `evidence_map.json` |
| `spec_lint` | `valid=true`、`problems=[]`、`counts.slides=6` |
| `previews` | 7 条，每条 `kind=pil-approximation`（slide 0 为封面） |
| `charts` | 1 条：`slide=4`、`ref=Fig. 1（重建）`、`chart.note` 声明 `reconstructed_from_table` |
| `sources` | 1 条：`type=paper_material`、`tool=direct-read`、`text_chars=2983`、`pages_parsed=0` |
| `uncertainty` | `[]`（本示例无降级；若有降级必须逐条列出） |
| `change_records` | ≥2 条（start run / run finished） |
| `run_meta` | `rendered_with=pil-approximation (...)`、`skill_version=2.1.0`、`checkpoints={cp1_spec_lint:true, cp2_build:true, cp3_export_check:true}`、`self_check.ok=true` |
| 契约语义字段 | `title` / `main_claim` 为真实值；`slides` 6 项（page/title/claim）；`render_state` 含 previews 数、rendered_with、deck_file、evidence_mapping_file；`notes_separated=true` |

> 上表与 `references/OUTPUT_CONTRACT.md` §1 的 19 个字段一一对应；允许为 `null` 的只有
> `deck` 与 `evidence_map_json`，且**仅在材料不可读的失败运行**中（本示例两者均非空）。

## 3. 两条交付门（都应 exit 0）

```bash
python "$SKILL_DIR/scripts/export_check.py" --result <out>/result.json \
  --out-dir <out> --case "$SKILL_DIR/examples/case.json"
# {"valid": true, "errors": [], "warnings": [], "case_id": "example-ppt-c7b80f0d", "status": "completed"}

python "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json \
  --contract "$SKILL_DIR/references/OUTPUT_CONTRACT.md" --case "$SKILL_DIR/examples/case.json"
# {"valid": true, "fields_contracted": 19, "fields_present": 19, "missing": [], ...}
```

## 4. 不应出现的东西

- 不应出现任何**本机绝对路径**（带盘符的 Windows 路径、用户主目录路径、UNC 前缀）
  —— 示例结果里的路径已净化为包内相对路径；
- 不应出现**预制答案**：正式 3 个案例的输入与期望输出由平台提供，本目录只描述示例案例；
- 不应把示意图/重建图说成论文原图：重建图必须在 `charts[].chart.note` 声明 `reconstructed_from_table`；
- 不应在无 Office 引擎时把预览说成真实渲染：文件名与 `kind`/`rendered_with` 三处都必须标注近似。
