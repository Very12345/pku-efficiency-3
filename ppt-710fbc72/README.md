# Academic Slide Adapter — 学术 PPT 模板与格式适配 Skill

`ppt-710fbc72`（学术效率第三期 / slides 组）的本地可运行 Skill 包。
功能：把论文/研究材料组织成结构清楚、证据可追溯、可编辑、符合模板要求的
学术汇报 —— 真实套用模板（母版/版式/占位符继承可查）、逐页主张+图号引用+
讲稿备注、页→来源证据映射附录、统一页脚页码、图表等比适配、整册审计，
并交付 `deck.pptx` + PNG 预览 + `result.json`。

## 运行方法

环境：Python 3.9+；依赖 `python-pptx`、`Pillow`（运行必需），
`matplotlib` 仅用于生成示例输入图，`numpy/reportlab` 非必需。
本机实测：Python 3.13.9 / python-pptx 1.0.2 / Pillow 12.3.0。

一键全流程（产物写 `--out`）：

```bash
python scripts/main.py --case examples/case.json --task examples/task.md --out D:/BuildTemp/out1
```

- 材料相对路径默认相对 `case.json` 所在目录解析；平台环境在 `/app/work`
  内解析（`--work /app/work`）。
- 显式指定模板 / 起始 deck（覆盖 case.json 内字段）：

```bash
python scripts/main.py --case <case.json> --template <模板.pptx> --out <out>
python scripts/main.py --case <case.json> --starting-deck <现有deck.pptx> --out <out>
```

- 契约校验（独立工具）：

```bash
python scripts/validate_result.py --case <case.json> --result <out>/result.json   # VALID, exit 0
```

- 重新生成内置回退模板：`python scripts/make_template.py`

## 输入说明（case.json 主要字段）

| 字段 | 说明 |
|-|-|
| `case_id / title / subtitle` | 案例标识 / 讲稿标题 / 副标题 |
| `research_question / methods / results / discussion / limitations / conclusion` | 各环节主张数组；每项可带 `text`+`source`（`文件:行`），results 项可带 `figure_refs`/`table_refs` |
| `figures` | `[{id, file, caption, source}]`；`file` 相对 case 目录 |
| `tables` | `[{id, caption, source, rows}]`（rows 为二维数组或 CSV 路径） |
| `audience / duration_minutes / slide_count / language` | 固定受众/时长/页数/语言（zh|en） |
| `template / starting_deck / source_material` | 模板 / 起始 deck / 材料文件（可为数组） |
| `output_contract` | 交付契约对象（自动镜像进 result.json 顶层） |

## 输出说明

`<case_id>_deck.pptx`（可编辑源，含逐页笔记）、`*_cover_preview.png` +
`*_slides_contact_schematic.png`（PIL 示意图预览，**非像素级导出**，详见
`render_log.json`）、`result.json`（契约见 `references/OUTPUT_CONTRACT.md`）、
`spec.json/content.json/audit.json/summary.txt`。
平台环境按 Runtime contract 使用 `/input/case.json`、`/app/work`、`/app/output`。

## 预期增益（相对基础 Agent）

- 模板真实套用：版式/占位符继承关系进 `template_audit`，缺失回退有记录；
- 内容与来源绑定：每页主张可追溯到 `文件:行`，图号↔正文交叉引用自动核验；
- 整册一致性：字号阶梯、页脚/页码、图注格式统一生成+审计；
- 逐页讲稿：每页 notes 含主张/证据/建议时长，可直接开讲；
- 诚实失败：缺图/缺字体/缺 LibreOffice 全部记录，不静默产出"像 PPT
  但不可用"的结果。

## 限制与失败处理

详见 `SKILL.md` §4 异常处理表与 `references/TEMPLATE.md` §8 已知限制。要点：
无 LibreOffice/PPT 时预览为 PIL 示意图（如实标注）；字体缺失走回退链并记录；
模板打不开自动回退内置模板；材料缺失/数值缺失绝不编造、进 `uncertainty`；
流水线异常写出 `status=failed` 的 result.json 不丢现场。

## 目录

`SKILL.md` 主文档 · `scripts/` 流水线（main/extract/deckplan/pptxbuild/
preview/audit/validate_result/make_template/common）· `references/`
（OUTPUT_CONTRACT/RUBRIC_MAP/TEMPLATE）· `templates/builtin.pptx` 内置回退
模板 · `examples/` 最小示例（合成数据，非正式案例）· `TEST.md` 本地实测记录
· `GITHUB_URL.txt` 公开仓库链接占位。

## 维护

- 版本：Skill `1.0.0`；脚本内型号 `SKILL_VERSION`（`scripts/common.py`）。
- 改动后至少复跑 `TEST.md` §0 编译检查与 §1 冒烟，确认全绿再交付。
- 内置模板为 Skill 资源（二进制，不计入文本文件限额），可从
  `scripts/make_template.py` 再生成。