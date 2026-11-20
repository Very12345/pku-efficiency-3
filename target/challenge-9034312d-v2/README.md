# challenge-9034312d 实验装置与技术路线图 Skill v2

玻尔产品周赛·北大专区·学术效率·第三期（efficiency-3）· figures 组。
依据科研材料生成或编辑**可编辑**的装置图/技术路线图（分层 SVG 源文件 +
PNG/PDF 预览 + 证据链 + result.json）。

v2 相对 v1（`build/challenge-9034312d`）的加强点见 `COMPARE.md`；本目录为
v2 制作产物（只制作，不提交平台、不发布仓库）。

## 运行方法

```bash
# 结构化案例（推荐；运行时以 /input/case.json 与 /app/output 为准）
python scripts/main.py --case /input/case.json --task /input/task.md --out /app/output

# 带材料文件/目录（案例引用的 md/txt/csv/tex）
python scripts/main.py --case /input/case.json --task /input/task.md \
  --material /app/work/material.md --out /app/output

# 最小示例（本包自带，见 examples/；产物标注「示例，非正式案例」）
python scripts/main.py --case examples/case.json --task examples/task.md \
  --out D:/BuildTemp/smoke-9034312d-v2

# 编辑既有图稿（增量修改：同名 id 替换、新 id 追加）
python scripts/main.py --case examples/case.json --task examples/task.md \
  --merge examples/route_spec.mutation.example.json --out D:/BuildTemp/smoke-merge

# 交付自查（G1–G10 契约门）
python scripts/check.py <out>/<case_id>/result.json
```

输出（`<out>/<case_id>/`）：`evidence.json`（证据链）、`figure.svg`（可编辑源文件）、
`figure.png`、`figure.pdf`、`layout.json`（结构化中间表示）、
`verify_report.json`（校验/规则审计）、`result.json`（contract 全字段 + case_id）。

## 结构

```
SKILL.md                 Skill 本体（YAML frontmatter；决策规则 D1–D12 + 检查点 CP1–CP4）
scripts/                 流水线脚本（main 编排；gain_evidence/render_svg/svg_verify/check 等）
references/              规范文档 5 份（OUTPUT_CONTRACT/RUBRIC_MAP/vocabulary/figure-blueprint/failure-modes）
templates/               可复用模板 3 件（palette + 组件连接核对清单 + 实体关系核对表 CSV）
assets/                  可复用资产 2 件（connection_rules 规则字典 + result 形态示例）
examples/                最小示例（结构案例 + 装置案例 + 编辑用例 + 真实运行产物）
README.md / TEST.md / COMPARE.md / worklog.md / GITHUB_URL.txt
```

## 依赖

| 依赖 | 用途 | 缺失时 |
|-|-|-|
| Python 3.10+（标准库） | 解析/证据/布局/写 SVG/校验 | —（必需） |
| Pillow（PIL） | PNG 预览 | 仅 PNG 缺失，status=partial |
| reportlab | PDF 预览 | 仅 PDF 缺失，status=partial |
| 本机中文字体（msyh/simhei 等） | PNG 中文渲染 | fonts.found=false 如实记录 |

`cairosvg/svgwrite/python-pptx` 不需要：SVG 为手写 XML，预览直接从同一布局模型渲染；
全部脚本只用标准库 + PIL + reportlab，可降级运行。

## 关键方法（v2）

1. **证据先行（CP1）**：`gain_evidence.py` 从真实材料抽取实体/关系并带
   locator+quote 与材料 sha256，evidence.json 落盘；
2. **连接规则资产（CP2）**：`assets/connection_rules.json`（类别词表 + 连接语义规则）
   由 `svg_verify.py` 机器审计，error 级违规强制 status=partial（D11）；
3. **校验闭环（CP3）**：`svg_verify.py` 检查图层/可编辑文本/箭头/编号连续性/图例↔图元/
   规则，产出 verify_report.json + 确定性探针 spec_sha16；
4. **契约门（CP4）**：`check.py` G1–G10 硬性门（含 status 诚实性）；
5. **确定性**：同输入必得同布局（figure.svg/layout.json/evidence.json/verify_report.json
   双跑逐字节一致，TEST.md T3）。

## 限制

- 只负责绘图表达与可编辑交付；**不**做数值拟合、方案科学性判断、投稿格式适配；
- 文本无结构化时走朴素解构（仅串联步骤），设备连接需 Agent 复核（D2）；
- 复杂装配图局部放大未内置，可在 Inkscape 微调源文件并如实记录 manual-edit；
- 正式案例评分由平台执行，`examples/` 仅为接口演示（示例，非正式案例）。

## 失败处理

管线异常/输入缺失 → `main.py` 兜底写出 status=failed 的 result.json；单个预览失败 →
保留已有产物并 status=partial（D10）；svg_verify error 级规则违规 → status=partial
（D11）；所有不确定性写入 `result.json.uncertainty`（scope+issue+action），修改记录
写入 `change_record`。完整失败模式表见 `references/failure-modes.md`。

## 维护

- 图元/配色：`scripts/model.py` 顶部 KINDS/RELATION_KINDS + `templates/palette.json` +
  `assets/connection_rules.json` + `references/vocabulary.md`（四处同步）；
- 布局规则：`references/figure-blueprint.md` + `scripts/layout.py`；
- 校验规则：`assets/connection_rules.json` + `scripts/svg_verify.py`；
- 契约与自查：`references/OUTPUT_CONTRACT.md` + `scripts/check.py`（G1–G10）；
- 本地实测：`TEST.md`；三方对照：`COMPARE.md`。