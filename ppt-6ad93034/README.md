# README.md — 学术 PPT 生成与编辑 Skill（学术效率 · slides 组）

本包是玻尔产品周赛·北大专区·学术效率·第三期题目 `ppt-6ad93034`（学术 PPT
生成与编辑，组 slides）的参赛 Skill。加载本 Skill 后，Agent 可把固定的科研
材料组织成结构化、证据可追溯、可编辑并符合模板要求的学术汇报演示稿。

## 1. 快速开始

```bash
# 1) 最小示例（材料为虚构，标注"示例，非正式案例"）
python scripts/main.py --case examples/case.json --out D:/BuildTemp/smoke-ppt-6ad93034

# 2) 校验 result.json 契约
python scripts/check_contract.py D:/BuildTemp/smoke-ppt-6ad93034/result.json examples/case.json

# 3) 演示局部编辑与版本记录（演示稿迭代）
python scripts/main.py --case examples/case.json \
    --out D:/BuildTemp/smoke-ppt-6ad93034-edit \
    --edit examples/edit_demo.json --version v2
```

平台运行形态：输入 `/input/case.json` + `/input/task.md`（材料按 case 指向），
在 `/app/work` 工作，产物写 `/app/output`（含 `result.json`），即
`python scripts/main.py --case /input/case.json --out /app/output`。

## 2. 目录结构

```
SKILL.md                    # 技能本体（YAML frontmatter + 执行步骤/异常/自查）
scripts/
  main.py                   # 编排：读入→抽取→规划→建稿→预览→result.json→自检
  material.py               # 读实际材料：章节/数据表/图·表提及/PDF 兜底
  planner.py                # 页序与页级叙事角色分配、主张证据绑定
  charting.py               # 数据表→matplotlib 重绘（不改数据）
  deck_builder.py           # python-pptx 建稿：模板槽位/备注/证据脚注/防溢出
  render.py                 # PIL 每页 PNG + reportlab PDF 预览（标注预览）
  result.py                 # result.json / evidence_map / changelog / manifest
  check_contract.py         # 契约校验（验收用）
  common.py                 # 路径自定位/字体/数字核验等公共工具
templates/default.json       # 默认模板 spec（颜色/字体/页脚/槽位，可参数化）
references/
  OUTPUT_CONTRACT.md        # result.json 结构契约
  RUBRIC_MAP.md             # 五维评分 → 设计覆盖对照
  TEMPLATE_SPEC.md          # 模板槽位与约束规范
examples/                   # 最小示例（虚构材料，标注"示例，非正式案例"）
GITHUB_URL.txt              # 公开作品链接（占位，发布代理覆写）
TEST.md                     # 本地实测记录
```

## 3. 依赖

| 依赖 | 版本 | 用途 | 缺失时的行为 |
|-|-|-|-|
| python-pptx | >=0.6.21（实测 1.0.2） | 可编辑 PPTX | 致命：无法建稿 |
| matplotlib | >=3.5（实测 3.10.6） | 数据表重绘图表 | 降级为 PPTX 原生可编辑表格 |
| Pillow | >=9（实测 12.3.0） | PNG 预览 | 预览缺 PNG，PDF 不受影响 |
| numpy | 任意 | 图表 | 随 matplotlib |
| reportlab | 任意（实测 5.0） | PDF 预览 | 跳过 PDF，记入 warning |
| cairosvg/svgwrite | 不使用 | — | 不依赖 |

安装：`pip install python-pptx matplotlib pillow numpy reportlab`。
运行期不要修改模板/材料；模板通过 `--template` 或 case `spec` 切换。

## 4. 输入格式（case.json）

```jsonc
{
  "case_id": "…",
  "title": "…",
  "inputs": {"task_md": "task.md", "material": ["paper.md", "results.csv"]},
  "spec": {
    "template": "default",            // 或 {"template_pptx": "…"} / {"starting_deck": "…"}
    "audience": "组会",               // 组会|答辩|评审|同行|基金
    "duration_minutes": 10,
    "max_slides": 8,
    "style": {"colors": {"accent": "#2E7D32"}}   // 可选覆盖模板
  },
  "output_contract": {"deck": "dict", "previews": "dict"}  // 可选，镜像到 result.json
}
```
材料路径相对 case.json 所在目录解析；缺失文件会被记录而非静默跳过。

## 5. 主要命令

| 命令 | 作用 |
|-|-|
| `python scripts/main.py --case C --out O` | 完整流水线（C 为 case.json，O 为输出目录） |
| `--template <spec.json>` | 换模板 spec |
| `--max-slides N` | 覆盖页数上限（3–20） |
| `--edit <edits.json> --version v2` | 局部编辑（改主张/备注/页序等）+ 版本归档 |
| `--no-chart` | 强制关闭图表重绘（降级原生表格，对照试验用） |
| `--draft` | 草稿模式（跳过 PDF 预览） |
| `python scripts/check_contract.py R [C]` | 校验 result.json 契约，exit 0=通过 |

## 6. 输出与验收

- `work/deck.pptx`：可编辑演示文件（每页备注+证据脚注）。
- `work/plan.json`：页面模型（页序/角色/主张/证据/图表），可编辑源。
- `work/preview/slide_*.png`、`preview.pdf`：预览渲染（**非 PowerPoint 导出**，
  文件名与 result `previews.method` 已如实标注）。
- `result.json`：contract 全字段 + case_id（见 references/OUTPUT_CONTRACT.md）；
- `evidence_map.md`、`changelog.jsonl`、`manifest.json`（产物 sha256）、`logs/`。

验收判据：`check_contract.py` 输出 `valid: true`；PPTX 可重新打开、页数与
plan 一致；每页有备注与证据；unverified_claims/uncertainty 逐条可解释。

## 7. 限制与已知问题（诚实声明）

1. **预览 ≠ Office 导出**：运行环境无 PowerPoint/LibreOffice，PNG/PDF 由
   PIL/reportlab 按页面模型渲染，供肉眼检查版式；如需要 Office 级 PDF，
   请在安装 PowerPoint/LibreOffice 的机器上用 `office_convert` 将 deck.pptx
   转 PDF（参考 office-pptx 技能）。
2. **CJK 字体**：预览绘制依赖主机字体（优先微软雅黑）；无 CJK 字体时预览
   出现方块但 pptx 不受影响（warnings 记录）。
3. **版式视觉微差**：PIL 预览的换行与 PowerPoint 的实际渲染存在像素级差异；
   溢出防护按字符宽度估算，极端长词/公式密度场景仍可能需人工微调。
4. **PDF 文本抽取**：材料为 PDF 且环境无抽取库时需 Agent 人工抽文本
   （SKILL.md Step 0 处置）。
5. **确定性生成**：同一输入无 `--edit` 时产物确定；时间戳与 sha256 除外。
6. **不适用**：本 Skill 不做论文综述撰写、不做可视化算法研发、不精修文案
   措辞、不开发 PPT 软件本身；论文图位图无数据时只占位不重绘。

## 8. 失败处理

- 逐步骤 try/except：单个步骤失败不吞掉原因，写入 `uncertainty`，
  `status` 降为 `partial`，尽量交付其余产物。
- 输入不可读 → `failed` 最小 result.json（含错误原因），绝不假装成功。
- `--edit` 中非法操作（页码不存在、未知 op）→ 跳过并记 `uncertainty`，
  其余 ops 照常应用。
- 复跑失败排查顺序：库版本（result.environment）→ 材料路径 → 模板 spec
  → 编辑 JSON。

## 9. 生态与复用

- 模块化脚本可直接复用：`planner.alloc_roles`（页面角色分配）、
  `common.check_claim_numbers`（数字核验）、`charting.build_chart`（表→图）、
  `deck_builder`（模板槽位建稿）。
- 模板与代码分离：换配色/字体/页脚只改 `templates/*.json`。
- 示例与题集：`examples/` 提供最小示例；页面骨架方法（roles + 证据脚注 +
  版本记录）可迁移到任何汇报生成工具。

## 10. 评分对照

五个评分维度的设计覆盖见 `references/RUBRIC_MAP.md`；实测记录见 `TEST.md`。