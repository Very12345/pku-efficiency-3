# README.md — 学术 PPT 生成与编辑 Skill（ppt-6ad93034）

把固定的科研材料（论文正文 / 数据表 / 任务说明）组织成**结构清楚、证据可追溯、
可编辑、符合模板约束**的学术汇报产物（PPTX + 演讲备注 + 页级证据映射 + 预览），
并支持**多轮局部编辑与版本回退**、**双形态页级证据映射**、**G1–G8 导出校验门**。

- 五维评分的逐点覆盖与复核命令：[`references/RUBRIC_MAP.md`](references/RUBRIC_MAP.md)
- `result.json` 字段契约与硬性门：[`references/OUTPUT_CONTRACT.md`](references/OUTPUT_CONTRACT.md)
- 页面蓝图与模板槽位：[`references/DECK_SPEC.md`](references/DECK_SPEC.md)
- 编辑操作目录与决策树：[`references/EDIT_OPS.md`](references/EDIT_OPS.md)
- 失败模式 / 降级 / 状态一致性：[`references/failure-modes.md`](references/failure-modes.md)
- 本机实测记录（退出码、产物清单、验收判据）：[`TEST.md`](TEST.md)
- 最小示例与应产出清单：[`examples/README.md`](examples/README.md)、[`examples/EXPECTED-OUTPUT.md`](examples/EXPECTED-OUTPUT.md)

## 1. 快速开始

`$SKILL_DIR` = **含 `SKILL.md` 的技能根目录**（平台评测容器里是
`/skills/weekly-skill`）。所有命令都写成 `$SKILL_DIR/…` 形式，因此
**cwd 不是技能根目录时同样能跑**；脚本内部也用 `os.path.dirname(__file__)` 自定位。

```bash
SKILL_DIR="${SKILL_DIR:-/skills/weekly-skill}"          # 换成你的实际安装路径
OUT="${OUT:-/tmp/ppt-out}"                              # 输出目录（包外）

# 1) 完整流水线：建稿 + 预览 + result.json + 证据映射 + 清单
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out "$OUT"

# 2) 校验 result.json 契约（CP4 G1–G8 硬性门，exit 0 = 通过）
python "$SKILL_DIR/scripts/result_tool.py" --result "$OUT/result.json" \
    --out-dir "$OUT" --case "$SKILL_DIR/examples/case.json" \
    --envelope "$SKILL_DIR/templates/result_envelope.json"

# 3) 产物自检（all_pass=true 为通过）
python "$SKILL_DIR/scripts/selftest.py" --out "$OUT" --case "$SKILL_DIR/examples/case.json"

# 4) 局部编辑 + 版本归档（演示稿迭代）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
    --out "${OUT}-edit" --edit "$SKILL_DIR/examples/edit_demo.json" --version v2
```

平台运行形态：输入 `/input/case.json` + `/input/task.md`（材料路径由 case 指向），
工作目录 `/app/work`，产物写 `/app/output`（含 `result.json`）：

```bash
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output
```

> ⚠ 步骤 2 的 `--case` **必须传**：契约回显字段（`output_contract`）只有在拿到
> `case.json` 时才能核对是否**逐项回显且非 null**。漏传会让"契约全回显"看起来失败。

## 2. 目录结构

```
SKILL.md                    # 技能本体：frontmatter + 用途/输入输出/步骤 CP1–CP4/
                            #   决策规则 D1–D12/异常处理/自查清单/诚实红线
README.md                   # 本文件：依赖/安装/用法/限制/维护
TEST.md                     # 本机真实实测记录（退出码、产物、双跑、异常路径）
GITHUB_URL.txt              # 公开作品链接
scripts/                    # 四层职责（extract / build / render / verify）+ 编排 + 维护
  main.py                   # 编排：CP1–CP4 检查点 + 端到端流水线 + --edit 模式
  deck_extract.py           # extract：读实际材料（case/task/md/txt/html/csv/pdf）
  slide_text.py             # build：页面文案生成（角色分配/主张/备注骨架）
  deck_tool.py              # build：模板槽位建稿 + 四态图表绑定 + 编辑操作
  render_qa.py              # render：PIL 预览 PNG + reportlab PDF + 渲染 QA
  evidence_check.py         # verify：数字/证据核验 + 证据脚注 + CP2 plan_lint
  result_tool.py            # verify：result 信封 + 双形态证据映射 + G1–G8 契约门
  selftest.py               # verify：端到端产物自检
  deck_common.py            # 公共：路径自定位/字体探测/哈希/原子写/日志
  make_examples.py          # 维护：用真实运行重建 examples/output 并净化绝对路径
templates/
  default.json              # 默认模板 spec（颜色/字体/页脚/槽位，可参数化）
  result_envelope.json      # 结果信封声明（result.json 字段类型，G8 依据）
references/
  OUTPUT_CONTRACT.md        # result.json 契约 + G1–G8 硬性门 + 判读规则
  RUBRIC_MAP.md             # 五维评分（40/25/15/10/10）→ 具体文件与复核命令
  DECK_SPEC.md              # 页面蓝图（论文结构→页面结构）+ 模板槽位约束
  EDIT_OPS.md               # 编辑操作目录 + 决策树（演示稿迭代）
  failure-modes.md          # 失败模式/降级策略/契约四形态/状态一致性/退出码
examples/                   # 最小示例（虚构材料，标注"示例，非正式案例"）
  case.json / task.md / material.md / results.csv / edit_demo.json
  EXPECTED-OUTPUT.md        # 纯文字列出应产出的全部文件与契约字段
  output/                   # 一次真实运行的**文本**产物副本（.example. 命名）
```

**包体形态（平台硬约束）**：随包资源只有 UTF-8 文本
（`.md/.py/.json/.txt/.csv/.yaml/.yml`），**≤50 文件 / 单文件 ≤500KB / 合计
≤2MB，无符号链接、无二进制**（题面 Runtime contract 原文：
*"at most 50 UTF-8 text files, 500KB each and 2MB total, no symlinks"*）。
运行产物里的二进制件
（`deck.pptx`、预览 `*.png`、预览 `*.pdf`）与 `changelog.jsonl` **不入包**，
一律由运行时生成 —— 完整清单见 [`examples/EXPECTED-OUTPUT.md`](examples/EXPECTED-OUTPUT.md)。

## 3. 依赖

| 依赖 | 版本 | 用途 | 缺失时的行为 |
|-|-|-|-|
| python-pptx | >=0.6.21 | 可编辑 PPTX | **致命**：无法建稿（如实报 partial/failed） |
| matplotlib | >=3.5 | 数据表重绘图表 | 降级为 PPTX 原生可编辑表格（D9） |
| Pillow | >=9 | PNG 预览 | 预览缺 PNG，G5 报错、自检不通过 |
| numpy | 任意 | 图表 | 随 matplotlib |
| reportlab | 任意 | PDF 预览 | 跳过 PDF，记入 warning（D8） |
| fitz / pypdf / pdfplumber | 任选其一 | PDF 材料文本抽取 | Agent 抽文本到 `work/materials/*.txt` 后重跑（D3） |

安装：`pip install python-pptx matplotlib pillow numpy reportlab`。
仅标准库亦可运行到"材料读取 + plan + result 元信息"的程度（无 PPTX 时状态降为 partial）。

## 4. 输入格式（`case.json`）

```jsonc
{
  "case_id": "…",
  "title": "…",
  "inputs": {"task_md": "task.md", "material": ["paper.md", "results.csv"]},
  "spec": {
    "template": "default",            // 或 {"template_pptx": "…"} / {"starting_deck": "…"}
    "audience": "组会",               // 组会|答辩|评审|同行|基金 —— 影响讲稿语气
    "duration_minutes": 10,
    "max_slides": 6,                  // 3–20
    "style": {"colors": {"accent": "#2E7D32"}}   // 可选：覆盖模板任意键
  },
  "output_contract": {"deck": "dict", "previews": "dict", "is_example": "bool"}
}
```

材料路径相对 `case.json` 所在目录解析；缺失文件写入 `material_warnings`
而非静默跳过（D1）。`output_contract` 声明的字段会按**四形态**（`""/[]/{}/false/0`）
镜像到 `result.json` 顶层，**禁 null**。

## 5. 主要命令

| 命令 | 作用 |
|-|-|
| `python "$SKILL_DIR/scripts/main.py" --case C --out O` | 完整流水线（C=case.json，O=输出目录） |
| `--template <spec.json>` | 换模板 spec（默认 `templates/default.json`） |
| `--input-dir <dir>` | `--case` 为相对路径时的基准目录 |
| `--max-slides N` | 覆盖 `spec.max_slides`（3–20） |
| `--edit <edits.json> --version v2` | 局部编辑 + 版本归档（`work/deck_v2.pptx`） |
| `--no-chart` | 强制关闭图表重绘（降级为原生表格，对照试验用） |
| `--draft` | 草稿模式（跳过 PDF 预览） |
| `--verbose` | 详细日志 |
| `python "$SKILL_DIR/scripts/result_tool.py" --result R --out-dir O [--case C] [--envelope E]` | CP4 契约门 G1–G8；`0=通过 / 1=有未过项 / 2=result 不可读` |
| `python "$SKILL_DIR/scripts/selftest.py" --out O [--case C] [--pptx P] [--slides N]` | 产物自检；`0=全过 / 1=有未过项` |
| `python "$SKILL_DIR/scripts/evidence_check.py" --claim "…" --material M` | 单条主张数字核验；`0=全部找到 / 1=有缺失` |
| `python "$SKILL_DIR/scripts/make_examples.py" [--dry-run]` | 维护：真跑示例并重建 `examples/output/`（自动净化绝对路径） |

退出码语义与失败分类见 [`references/failure-modes.md`](references/failure-modes.md) §0/§1–§7。

## 6. 输出与验收

- `work/deck.pptx`：可编辑演示文件（每页主张式标题 + 要点 + 图表槽 + 证据脚注 + 演讲备注）
- `work/plan.json`：页面模型（页序/角色/主张/证据/图表），**可编辑源**
- `work/preview/slide_*.png`、`preview/preview.pdf`：预览渲染（**非 PowerPoint
  导出**，文件名与 `previews.method` 均已如实标注）
- `result.json`：契约全字段 + `case_id` + `run_meta`（checkpoints / spec_lint /
  render_qa / gate），见 [`references/OUTPUT_CONTRACT.md`](references/OUTPUT_CONTRACT.md)
- `evidence_map.md` + `evidence_map.json`：双形态页级证据映射（同源生成）
- `changelog.jsonl`、`manifest.json`（全部产物 sha256）、`logs/`

**验收判据**：`result_tool.py` 输出 `{"valid": true}` 且 exit 0（G1–G8 全过）；
`selftest.py` `all_pass=true`；PPTX 可被 python-pptx 重新打开且页数与 plan 一致；
每页有备注与证据脚注；`unverified_claims` 与 `uncertainty` 逐条可解释。

## 7. 限制与已知问题（诚实声明）

1. **预览 ≠ Office 导出**：运行环境无 PowerPoint/LibreOffice 时，PNG/PDF 由
   PIL/reportlab 按页面模型渲染，供肉眼检查版式与内容；如需 Office 级 PDF，
   请在装有 PowerPoint/LibreOffice 的机器上转换 `work/deck.pptx`。
2. **CJK 字体**：预览绘制依赖主机字体，按跨平台候选链探测（Windows
   `C:/Windows/Fonts` 的微软雅黑/黑体/宋体 → macOS `/System/Library/Fonts`
   的 PingFang/Songti → Linux `/usr/share/fonts` 的 Noto/文泉驿/DejaVu）；
   找不到 CJK 字体时预览出现方块，**pptx 不受影响**，该事实写入
   `previews.warnings`。包内**不携带任何字体文件**，这些路径只是运行时探测候选。
3. **版式视觉微差**：PIL 预览的换行与 PowerPoint 实际渲染存在像素级差异；
   溢出防护按字符宽度估算，极端长词/公式密度场景仍可能需人工微调。
4. **机器路径**：`deck.slides[].figure.image` 与 `sources[].path` 记录的是**本次
   运行所在机器**的实际路径（产物而非包内容）；跨机复跑时前缀随之变化，内容不变。
   包内示例产物已由 `scripts/make_examples.py` 净化成包内相对路径。
5. **PDF 材料**：环境无抽取库时需 Agent 抽文本后重跑（D3），并在 `uncertainty` 记录方式。
6. **确定性生成**：同一输入无 `--edit` 时产物结构确定；仅时间戳与机器路径前缀不同
   （双跑记录见 [`TEST.md`](TEST.md) §T6）。
7. **不适用**：不做论文综述/精读、不做可视化算法研发、不做文案润色、不做 PPT
   软件研发；复杂智慧型占位符（SmartArt）不重排；论文图是位图且无取数数据时
   **只占位不重绘**。

## 8. 失败处理

- 逐步骤 try/except + 先存部分产物：单个步骤失败不吞原因，写入 `uncertainty`，
  `status` 降 `partial`，尽量交付其余产物。
- 输入不可读 → 写最小 `status=failed` 的 `result.json`（含错误原因），
  绝不假装成功（D1）。
- `--edit` 的非法操作（未知 op / 页码不存在 / 非置换页序）→ 跳过 + 记录，
  其余 ops 照常应用（D11）。
- 完整失败分类（材料 / 模板 / 依赖 / 契约四形态 / 状态一致性 / 编辑链路 /
  资源形态）与**排查顺序**见 [`references/failure-modes.md`](references/failure-modes.md)。

## 9. 生态与复用

- **可复用的函数级组件**：`slide_text.alloc_roles`（页面角色分配）、
  `evidence_check.check_claim_numbers` / `plan_lint`（数字核验 + 页面纪律）、
  `deck_tool.build_chart`（表→图）、`deck_tool.apply_edits`（编辑操作）、
  `result_tool.validate`（G 门）。
- **模板与代码分离**：换配色/字体/页脚只改 `templates/*.json`；结果信封
  `templates/result_envelope.json` 可被任何验证器复用。
- **方法可迁移**：页面骨架（roles + 证据脚注 + 双形态证据映射 + 编辑操作目录 +
  版本记录 + 契约四形态）可直接搬到其他"长材料 → 演示稿"的工具里。
- **示例即题集**：`examples/` 是一组最小上手输入，明确标注"示例，非正式案例"，
  可直接作为他人的冒烟用例。

## 10. 维护

- 改了脚本或文档后，按 [`TEST.md`](TEST.md) 的八条命令自测一遍；
- 改了示例相关代码后，跑 `python "$SKILL_DIR/scripts/make_examples.py"`
  重新生成 `examples/output/` 的文本副本（会自动净化机器绝对路径）；
- 提交前自检包体：只有允许的七种文本扩展名、≤50 文件、单文件 ≤500KB、
  合计 ≤2MB、无 `__pycache__`、无本机绝对路径。
