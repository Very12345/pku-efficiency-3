# TEST —— 本地实测记录（ppt-710fbc72，academic-slide-adapt）

环境：Windows 11 + Git Bash(MSYS2)；`python` = Anaconda Python 3.13.9；
python-pptx 1.0.2 / Pillow 12.3.0 / numpy 2.3.5 / matplotlib 3.10.6 / reportlab 5.0.0（后两者
仅用于示例输入图生成与版本记录，Skill 运行时只依赖 python-pptx + Pillow）。
cairosvg / svgwrite 不可用（与本 Skill 无关——预览走 PIL，不依赖 SVG 库）。
无 LibreOffice / uno：预览为 PIL 示意图（如实标注，不产伪 PDF）。
所有命令在 Skill 根目录 `ppt-710fbc72/` 执行。

## 0. 语法编译检查

命令：
```bash
python -m py_compile scripts/common.py scripts/extract.py scripts/deckplan.py \
    scripts/pptxbuild.py scripts/preview.py scripts/audit.py scripts/main.py \
    scripts/validate_result.py scripts/make_template.py
```
结果：**成功**（exit 0，`ALL_COMPILE_OK`）。

## 1. 正式冒烟（示例案例，内置模板回退路径）

命令：
```bash
python scripts/main.py --case examples/case.json --task examples/task.md --out D:/BuildTemp/smoke-ppt-710fbc72
```
结果：**成功（exit 0）**，status=`success`，**10 页 = 目标 10 页**。
产出（D:/BuildTemp/smoke-ppt-710fbc72/）：

| 文件 | 大小 | 校验 |
|-|-|-|
| `example-catalyst-201_deck.pptx` | 58.6 KB | python-pptx 重开 ok；10 slides；3 张嵌入图；10 页均有 speaker notes；页脚/页码全册一致 |
| `example-catalyst-201_cover_preview.png` | 55.6 KB | PNG 签名 ok，1280×720，460 种颜色（非空白） |
| `example-catalyst-201_slides_contact_schematic.png` | 133 KB | PNG 签名 ok，10 页联系表 |
| `result.json` | 27.5 KB | status=success；case_id 一致；output_contract 7 个字段全部镜像进顶层；无 uncertainty |
| `spec.json` / `content.json` / `audit.json` / `render_log.json` / `summary.txt` | — | 审计 16 检查 + `result.contract` 全 ok |

审计摘要（audit.json）：`pptx.reopen` 10 slides、`pptx.slide_count` 10==10、
`content.claim_coverage` 全通过、`xref.figure_refs` 2 个图号全部解析、
`xref.figure_placement` 2/2 上图、`notes.present` 10/10、`layout.overflow` 0、
`layout.font_floor` 无、`layout.footer_uniform` ok、`traceability.evidence_loc` 13/13=100%、
`result.contract` ok。模板审计：`opened_from=builtin`（case 未给模板 → 内置回退），
版式套用 `Title Slide`（封面）+ `Title and Content`（内容页），无占位符回退。

## 2. 确定性复现（同输入 → 逐字节相同）

命令：同一命令在**同一输出目录**连跑三次，用 sha256 对拍产物：

```text
spec.json                                      identical == True
content.json                                   identical == True
audit.json                                     identical == True
<case>_deck.pptx                               identical == True   （zip 时间戳已固定化）
<case>_cover_preview.png                       identical == True
<case>_slides_contact_schematic.png            identical == True
result.json：除 generated_at 外逐字节相同（abspath 字段在换目录时变化，属预期）
```
**通过**：页计划为确定性纯函数；pptx 经 `_deterministic_zip` 后同输入同字节。

## 3. 鲁棒性用例

### 3a. 模板打不开（损坏文件）→ 回退内置模板
```bash
python scripts/main.py --case examples/case.json --task examples/task.md \
    --template D:/BuildTemp/broken_template.pptx --out D:/BuildTemp/r1
```
结果：**成功**；`template_audit.opened_from=builtin`、`template_errors` 1 条、status=success。

### 3b. 显式有效模板路径（模板套用路径）
```bash
python scripts/main.py --case examples/case.json --task examples/task.md \
    --template templates/builtin.pptx --out D:/BuildTemp/r2
```
结果：**成功**；`opened_from=case_template`。

### 3c. 起始 deck 编辑（3 页旧 deck → 重排 10 页，沿用其模板）
```bash
python scripts/main.py --case examples/case.json --task examples/task.md \
    --starting-deck D:/BuildTemp/start_deck.pptx --out D:/BuildTemp/r3
```
结果：**成功**；`template_audit.dropped_original_slides=3`、
`change_records[0].action=edit_starting_deck`（before 3 → after 10 记录齐全）。

### 3d. 小页数 + 英文 + 无材料文件 + 源图缺失
输入：`robust-case.json`（slide_count=6、language=en、source_material=[]、
figures 指向不存在的图片）。结果：**成功（exit 0）**，status=`partial`；
8 页（6 目标 → 确定性裁剪保留附录 2 页）、figures 1/1（占位框）、
uncertainty 如实列出：`no readable material`、`figure 1 source image`、
xref 警告（正文引用 图2 不在图清单）。**无编译/渲染失败，无不实字段。**

### 3e. 契约校验 CLI
```bash
python scripts/validate_result.py --case examples/case.json --result examples/output/result.json
# VALID - result.json conforms to OUTPUT_CONTRACT ; exit 0
python scripts/validate_result.py --case D:/BuildTemp/robust-case.json --result D:/BuildTemp/r4/result.json
# VALID ; exit 0
```

## 4. 对照（增益方向，非平台白板）

同一示例案例、同一内置模板：只跑 `examples/` 材料直接造册（无本 Skill 管线的
朴素方式：整段搬正文 + 无版式审计 + 无页脚/页码 + 无讲义 + 无证据映射）对比
本 Skill 输出：本输出具备 `slide_evidence`（13/13 主张带 `文件:行`）、
`template_audit`（版式/占位符继承可查）、逐页 notes、统一页脚页码、图号交叉
引用检查全部通过。平台正式对照（3 案例 × 3 次复跑）由组织方执行，本项仅为
设计方向的局部记录，不冒充成绩。

## 5. 已知限制（如实）

- 预览为 PIL 示意图（`preview_is_schematic=true`），非像素级导出；PDF 导出需
  PowerPoint/LibreOffice，本机无，故未产 PDF（如实记录于 render_log.json）；
- CJK 行高为估算，极端字体环境可能与 PowerPoint 实际排版有偏差（有溢出报告兜底）；
- 主题色通过占位符继承保持，未解析主题 XML 取色板（README/TEMPLATE.md 已注明）。