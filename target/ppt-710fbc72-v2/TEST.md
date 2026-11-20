# TEST —— 本地实测记录（ppt-710fbc72 v2，academic-slide-adapt 2.0.0）

环境：Windows 11 + Git Bash(MSYS2)；`python` = Anaconda Python 3.13.9；
python-pptx 1.0.2 / Pillow 12.3.0 / numpy 2.3.5 / matplotlib 3.10.6 / reportlab 5.0.0（后两者
仅用于示例输入图生成与版本记录，Skill 运行时只依赖 python-pptx + Pillow）。
cairosvg / svgwrite 不可用（与本 Skill 无关——预览走 PIL，不依赖 SVG 库）。
无 LibreOffice / uno：预览为 PIL 示意图（如实标注，不产伪 PDF）。
所有命令在 Skill 根目录 `ppt-710fbc72-v2/` 执行。日期：2026-11-21（Asia/Shanghai）。

## 0. 语法编译检查

命令：
```bash
python -m py_compile scripts/common.py scripts/extract.py scripts/deckplan.py \
    scripts/adopt_plan.py scripts/adapt_pptx.py scripts/pptx_toolkit.py \
    scripts/preview.py scripts/audit.py scripts/main.py \
    scripts/validate_result.py scripts/check_contract.py scripts/make_template.py
```
结果：**成功**（exit 0，`ALL_COMPILE_OK`，12 个脚本全过）。

## 1. 正式冒烟（示例案例，内置模板回退路径，两阶段全流程）

命令：
```bash
python scripts/main.py --case examples/case.json --out D:/BuildTemp/smoke-ppt-710fbc72-v2
```
结果：**成功（exit 0）**，status=`success`，**10 页 = 目标 10 页**，CP3 契约门
**G1–G8 全过**。产出（D:/BuildTemp/smoke-ppt-710fbc72-v2/）：

| 文件 | 大小 | 校验 |
|-|-|-|
| `example-catalyst-201_deck.pptx` | 116.9 KB | python-pptx 重开 ok；10 slides；2 张嵌入图；10 页均有 speaker notes；页脚/页码全册一致 |
| `example-catalyst-201_cover_preview.png` | 55.7 KB | PNG 签名 ok，1280×720（SCHEMATIC 标注） |
| `example-catalyst-201_slides_contact_schematic.png` | 133 KB | PNG 签名 ok，10 页联系表 |
| `adopt_plan.json` | 16.8 KB | **适配方案**：模板审计（builtin：1 母版/11 版式枚举、主题字体 Calibri、12 个主题色）、10 页版式分配、批量规则 0 偏差、3 条图表放置计划、gates 全 ok |
| `result.json` | 32.6 KB | status=success；case_id 一致；output_contract 7 个字段全部镜像进顶层；21 条检查全 ok；`verification.contract_gates` 8/8 ok |
| `spec.json` / `content.json` / `audit.json` / `render_log.json` / `summary.txt` | — | 见下审计摘要 |

审计摘要（audit.json，21 checks 全部 `ok`）：
`artifact.*.exists`（pptx/cover/contact/spec/**adopt_plan**）、`pptx.reopen` 10 slides、
`pptx.slide_count` 10==10、`content.claim_coverage` 全通过、
`xref.figure_refs`、`xref.figure_placement` 2/2 上图、`notes.present` 10/10、
`layout.overflow` 0、`layout.font_floor` 无、`layout.footer_uniform` ok、
`preview.cover_png`/`preview.contact_png` 签名 ok、`traceability.evidence_loc` 13/13=100%、
**`adopt_plan.consistency`（10/10 页按方案套用，0 偏差）**、`adopt_plan.gates` ok、
`result.contract` ok、`result.contract_gates` ok。
模板审计：`opened_from=builtin`（case 未给模板 → 内置回退，`template_errors=[]`），
主题继承：latin=Calibri、ea=空（内置模板默认）、accent1–6 等 12 色记录在
`template_audit.theme`；`adopt_plan_applied=10/10`。

## 2. 确定性复现（同输入 → 除时间戳外逐字节相同）

命令：同一命令对**同一输出目录**连跑两次，sha256 对拍：

```text
spec.json                                      identical == True
content.json                                   identical == True
audit.json                                     identical == True
adopt_plan.json                                identical == True      （v2 方案确定性）
<case>_deck.pptx                               identical == True   （zip 时间戳固定化）
<case>_cover_preview.png                       identical == True
<case>_slides_contact_schematic.png            identical == True
summary.txt                                    identical == True
result.json：除 generated_at 外逐字节相同（同一目录双跑实测 key 差异 = ['generated_at']）
```

**通过**：页计划与适配方案为确定性纯函数；pptx 经 `_deterministic_zip` 后同
输入同字节。换输出目录时 `artifacts.abspath` 与 audit 内绝对路径字段变化，
属预期（v1 同口径）。

## 3. 契约校验与 CP3 门（独立工具）

```bash
python scripts/validate_result.py --case examples/case.json --result examples/output/result.json
# VALID - result.json conforms to OUTPUT_CONTRACT ; exit 0
python scripts/check_contract.py --result examples/output/result.json \
    --out-dir examples/output --case examples/case.json
# {"valid": true} ; exit 0  （G1–G8 全过）
```

## 4. 鲁棒性用例

### 4a. 模板打不开（损坏文件）→ 回退内置模板
```bash
python scripts/main.py --case examples/case.json --task examples/task.md \
    --template D:/BuildTemp/broken_template.pptx --out D:/BuildTemp/r1-v2
```
结果：**成功**；`template_audit.opened_from=builtin`、`template_errors` 1 条、
`adopt_plan_applied=10/10`、status=success。

### 4b. 显式有效模板路径（模板套用路径）
```bash
python scripts/main.py --case examples/case.json --task examples/task.md \
    --template templates/builtin.pptx --out D:/BuildTemp/r2-v2
```
结果：**成功**；`opened_from=case_template`、`adopt_plan_applied=10/10`、
status=success。

### 4c. 起始 deck 编辑（3 页旧 deck → 重排 10 页，沿用其模板）
```bash
python scripts/main.py --case examples/case.json --task examples/task.md \
    --starting-deck D:/BuildTemp/start_deck.pptx --out D:/BuildTemp/r3-v2
```
结果：**成功**；`template_audit.dropped_original_slides=3`、
`change_records[0].action=edit_starting_deck`（before 3 → after 10 记录齐全）、
status=success。

### 4d. 契约校验 CLI（独立复查，含 CP3 门）
```bash
python scripts/validate_result.py --case examples/case.json --result D:/BuildTemp/smoke-ppt-710fbc72-v2/result.json   # VALID ; exit 0
python scripts/check_contract.py --result D:/BuildTemp/smoke-ppt-710fbc72-v2/result.json \
    --out-dir D:/BuildTemp/smoke-ppt-710fbc72-v2 --case examples/case.json   # valid=true ; exit 0
```

## 5. 对照（增益方向，非平台白板）

同一示例案例、同一内置模板：只跑 `examples/` 材料直接造册（朴素方式：整段搬
正文 + 无版式审计 + 无页脚/页码 + 无讲义 + 无证据映射 + **无适配方案**）对比
本 Skill v2 输出：

| 维度 | 朴素基线 | v2 输出 |
|-|-|-|
| 模板套用 | 无（默认版式硬填） | 两阶段方案：`adopt_plan.json`（母版/版式/占位符枚举+主题字体色）→ 10/10 页按方案套用，0 偏差 |
| 页级证据 | 无 | `slide_evidence` 10 页 + 13/13 主张带 `文件:行` |
| 批量一致性 | 无 | 批量规则 R1–R8：页脚/页码/标题位置/字号阶梯统一，audit 4 项检查 ok |
| 讲稿 | 无 | 10/10 页 speaker notes（主张/证据/建议时长） |
| 契约门 | 无 | CP3 G1–G8 全过（`check_contract.py` exit 0） |
| 诚实降级 | 无 | 失败模式 20 项 + D1–D12 + 状态一致性纪律 |

平台正式对照（3 案例 × 3 次复跑）由组织方执行，本项仅为设计方向的局部记录，
不冒充成绩。

## 6. 已知限制（如实）

- 预览为 PIL 示意图（`preview_is_schematic=true`），非像素级导出；PDF 导出需
  PowerPoint/LibreOffice，本机无，故未产 PDF（如实记录于 render_log.json）；
- CJK 行高为估算，极端字体环境可能与 PowerPoint 实际排版有偏差（有溢出报告兜底）；
- 主题色/主题字体为只读记录（读 theme1.xml），不做主题 XML 改写；
- 内置模板主题 ea 字体为空（python-pptx 默认模板特性），CJK 由系统字体回退承担，
  已在 theme 记录中如实呈现。