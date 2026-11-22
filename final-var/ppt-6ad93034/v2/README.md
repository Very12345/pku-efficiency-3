# README.md — 学术 PPT 生成与编辑 Skill（增益可验证版 · ppt-6ad93034）

把固定的科研材料组织成**结构清楚、证据可追溯、可编辑、符合模板约束**的学术汇报产物：
可编辑 PPTX + 每页演讲备注 + 页级证据映射（md/json）+ 渲染预览 + `result.json`；
支持**多轮局部编辑与版本回退**。

**这一版的重点是"增益可验证"**：随包给出与"不加载 Skill 的基础 Agent"的
**公平对照协议**、五项质量与三项效率指标的精确公式、一个可复跑且**随包分发**的
测量脚本（[`references/measure_gain.py`](references/measure_gain.py)），以及在本机
**真实跑出来的对照记录**（含一条如实保留的负面指标）。

| 想找什么 | 去哪看 |
|-|-|
| 增益怎么算、怎么证伪、实测数字 | [`references/GAIN-PROTOCOL.md`](references/GAIN-PROTOCOL.md) ★本版核心 |
| 五维评分逐点落点与复核命令 | [`references/RUBRIC_MAP.md`](references/RUBRIC_MAP.md) |
| `result.json` 字段契约与 G1–G8 门 | [`references/OUTPUT_CONTRACT.md`](references/OUTPUT_CONTRACT.md) |
| 失败模式 / 降级 / 状态一致性 / 退出码 | [`references/failure-modes.md`](references/failure-modes.md) |
| 页面蓝图与模板槽位 | [`references/DECK_SPEC.md`](references/DECK_SPEC.md) |
| 编辑操作目录与决策树 | [`references/EDIT_OPS.md`](references/EDIT_OPS.md) |
| 本机实测记录（命令 / 退出码 / 负路径） | [`TEST.md`](TEST.md) |
| 最小示例与应产出清单 | [`examples/README.md`](examples/README.md)、[`examples/EXPECTED-OUTPUT.md`](examples/EXPECTED-OUTPUT.md) |

## 1. 快速开始

`$SKILL_DIR` = **含 `SKILL.md` 的技能根目录**（平台容器内为 `/skills/weekly-skill`）。
所有命令都写成 `$SKILL_DIR/…`，所以 **cwd 不是技能根目录也能跑**。

```bash
SKILL_DIR="${SKILL_DIR:-/skills/weekly-skill}"
OUT="${OUT:-/tmp/ppt-out}"

# ① 端到端：建稿 + 预览 + result.json + 证据映射 + manifest
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out "$OUT"

# ② 契约门（exit 0 = 通过；--case 必须传，否则无法核对契约回显）
python "$SKILL_DIR/scripts/result_tool.py" --result "$OUT/result.json" \
    --out-dir "$OUT" --case "$SKILL_DIR/examples/case.json" \
    --envelope "$SKILL_DIR/templates/result_envelope.json"

# ③ 产物自检（all_pass=true 为通过）
python "$SKILL_DIR/scripts/selftest.py" --out "$OUT" --case "$SKILL_DIR/examples/case.json"

# ④ 局部编辑 + 版本归档
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
    --out "${OUT}-edit" --edit "$SKILL_DIR/examples/edit_demo.json" --version v2
```

平台运行形态：输入 `/input/case.json` + `/input/task.md`，产物写 `/app/output`：

```bash
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output
```

## 2. 复跑"使用增益"对照（本版特有）

```bash
# 关键：在【包外】运行，避免在技能包里生成 __pycache__（平台预检会拒收整包）
cp "$SKILL_DIR/references/measure_gain.py" /tmp/
python /tmp/measure_gain.py --skill-dir "$SKILL_DIR" \
    --case "$SKILL_DIR/examples/case.json" \
    --case <你的第二个 case.json> \
    --work /tmp/gain-work --out /tmp/gain-report.json
```

报告含逐案例的 `quality`（Q1–Q6）、`diagnostics`、`efficiency`（E1–E3）与
`deltas`，以及两侧退出码；汇总在 `aggregate`。指标定义、公平条件、真实记录与
**证伪判据**见 [`references/GAIN-PROTOCOL.md`](references/GAIN-PROTOCOL.md)。

> 一句话口径：**两侧同一把尺子；"没做"的项按最差计；负面结果照原样报出。**
> 本包**不主张**"比基础 Agent 跑得快"（实测多出约 2–3 秒脚本开销，已如实列出）。

## 3. 目录结构

```
SKILL.md                    # 技能本体：frontmatter + 增益来源表 + CP1–CP4 + 对照要点 + 自查清单
README.md                   # 本文件：用法/对照复跑/目录/依赖/限制/维护
TEST.md                     # 本机真实实测记录（含负路径与对照复算入口）
GITHUB_URL.txt              # 公开作品链接
scripts/                    # 四层职责 + 编排 + 维护（算法与 CLI 接口保持稳定）
  main.py                   # 编排：CP1–CP4 + --edit 模式
  deck_extract.py           # extract：读实际材料（case/task/md/txt/html/csv/pdf）
  slide_text.py             # build：角色分配 + 页面文案骨架
  deck_tool.py              # build：模板槽位建稿 + 四态图表绑定 + 编辑操作
  render_qa.py              # render：PIL 预览 + reportlab PDF + 渲染 QA
  evidence_check.py         # verify：数字核验 + 证据脚注 + CP2 plan_lint
  result_tool.py            # verify：result 信封 + 双形态证据映射 + G1–G8
  selftest.py               # verify：端到端产物自检
  deck_common.py            # 公共：自定位/字体探测/哈希/原子写/日志
  make_examples.py          # 维护：真跑示例重建 examples/output 并净化机器路径
templates/
  default.json              # 默认模板 spec（参数化）
  result_envelope.json      # 结果信封声明（G8 依据）
references/
  OUTPUT_CONTRACT.md        # result.json 契约 + G1–G8 + 判读规则
  RUBRIC_MAP.md             # 五维评分（40/25/15/10/10）→ 文件与复核命令
  GAIN-PROTOCOL.md          # ★ 公平对照协议 + 指标公式 + 实测记录 + 证伪判据
  measure_gain.py           # ★ 随包测量脚本（两侧指标实现，包外运行）
  DECK_SPEC.md              # 页面蓝图 + 模板槽位约束
  EDIT_OPS.md               # 编辑操作目录 + 决策树
  failure-modes.md          # 失败模式 / 降级 / 契约四形态 / 状态一致性 / 退出码
examples/                   # 最小示例（虚构材料，标注"示例，非正式案例"）
  case.json / task.md / material.md / results.csv / edit_demo.json
  EXPECTED-OUTPUT.md        # 纯文字列出应产出的全部文件与契约字段
  output/                   # 一次真实运行的**文本**产物副本（.example. 命名）
```

**包体形态（平台硬约束）**：随包资源只有 UTF-8 文本
（`.md/.py/.json/.txt/.csv/.yaml/.yml`），**≤50 文件 / 单文件 ≤500KB / 合计 ≤2MB、
无符号链接、无二进制**（题面 Runtime contract 原文：*"at most 50 UTF-8 text files,
500KB each and 2MB total, no symlinks"*）。二进制产物（`deck.pptx`、预览 `*.png`/`*.pdf`）
与 `changelog.jsonl` **不入包**，由运行时生成。

## 4. 依赖

| 依赖 | 版本 | 用途 | 缺失时的行为 |
|-|-|-|-|
| python-pptx | >=0.6.21 | 可编辑 PPTX | **致命**：如实报 partial/failed |
| matplotlib | >=3.5 | 数据表重绘图表 | 降级 PPTX 原生可编辑表格（D9） |
| Pillow | >=9 | PNG 预览 | 预览缺 PNG → G5 报错、自检不过（D8） |
| numpy | 任意 | 图表 | 随 matplotlib |
| reportlab | 任意 | PDF 预览 | 跳过 PDF，记 warning（D8） |
| fitz / pypdf / pdfplumber | 任选其一 | PDF 材料抽取 | Agent 抽文本后重跑（D3） |

安装：`pip install python-pptx matplotlib pillow numpy reportlab`。
只装标准库也能跑到"材料读取 + 规划 + 元信息 result"的程度（状态降 partial）。

## 5. 输入格式（`case.json`）

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
    "style": {"colors": {"accent": "#2E7D32"}}
  },
  "output_contract": {"deck": "dict", "previews": "dict", "is_example": "bool"}
}
```

材料路径相对 `case.json` 所在目录解析；缺失文件写入 `material_warnings` 而非静默跳过。
`output_contract` 声明的字段按**四形态**（`""/[]/{}/false/0`）镜像到 `result.json` 顶层，**禁 null**。

## 6. 命令索引与退出码

| 命令 | 作用 | 退出码 |
|-|-|-|
| `main.py --case C --out O` | 端到端（CP1–CP4；也是对照的"条件 S"） | 0=success / 1=partial / 2=输入不可读 |
| `--template <spec.json>` | 换模板 spec | — |
| `--input-dir <dir>` | `--case` 相对路径的基准目录 | — |
| `--max-slides N` | 覆盖页数上限（3–20） | — |
| `--edit <edits.json> --version v2` | 局部编辑 + 版本归档 | 同上 |
| `--no-chart` | 强制图表降级（对照试验） | — |
| `--draft` | 草稿模式（跳过 PDF 预览） | — |
| `--verbose` | 详细日志 | — |
| `result_tool.py --result R --out-dir O --case C --envelope E` | 契约门 G1–G8 | 0=通过 / 1=有未过项 / 2=result 不可读 |
| `selftest.py --out O --case C [--pptx P] [--slides N]` | 产物自检 | 0=全过 / 1=有未过项 |
| `evidence_check.py --claim "…" --material M` | 单条数字核验 | 0=全部找到 / 1=有缺失 |
| `make_examples.py [--dry-run]` | 重建示例文本产物 | 0 / 2=输入不可读 |
| `references/measure_gain.py --skill-dir D --case C [--case C2] --work W --out R` | 公平对照测量（包外运行） | 0=测量完成 / 2=输入不可读 |

**编排器判读**：只有 exit 0 才算这次运行"干净"；exit 1 必须读
`result.json.uncertainty` 再决定是否补件重跑；exit 2 是输入侧问题，重跑无用。

## 7. 输出与验收

- `work/deck.pptx`：可编辑演示文件（主张式标题 + 要点 + 图表槽 + 证据脚注 + 演讲备注）
- `work/plan.json`：页面模型（可编辑源）
- `preview/slide_*.png`、`preview/preview.pdf`（+ `work/preview/` 同名副本）
- `result.json`：契约全字段 + `case_id` + `run_meta`（checkpoints / spec_lint / render_qa / gate）
- `evidence_map.md` + `evidence_map.json`：双形态同源页级证据映射
- `changelog.jsonl`、`manifest.json`（全部产物 sha256）、`logs/`

**验收判据**：`result_tool.py` → `{"valid": true}` 且 exit 0（G1–G8 全过）；
`selftest.py` → `all_pass=true`；PPTX 可被 python-pptx 重新打开且页数与 plan 一致；
每页有备注与证据脚注；`unverified_claims` 与 `uncertainty` 逐条可解释。

## 8. 限制与已知问题（诚实声明）

1. **对照的性质**：本包给的是**受控脚本级对照**（基线 = 题面点名失败清单的确定性
   代理实现），不是平台官方的 Agent 级对照；`GAIN-PROTOCOL.md` 的范围声明与 §7 局限
   逐条写明，结论只在声明范围内成立。
2. **预览 ≠ Office 导出**：无 PowerPoint/LibreOffice 时 PNG/PDF 由 PIL/reportlab 渲染；
   需要 Office 级 PDF 请在装有 Office 的机器上转换 `work/deck.pptx`。
3. **CJK 字体**：预览依赖主机字体，按跨平台候选链探测（Windows `C:/Windows/Fonts`
   → macOS `/System/Library/Fonts` → Linux `/usr/share/fonts`）；找不到时预览出现方块但
   **PPTX 不受影响**，事实写入 `previews.warnings`。包内**不含任何字体文件**。
4. **版式视觉微差**：PIL 预览与 PowerPoint 实际渲染有像素级差异；溢出防护按字符宽度
   估算，极端长词/高公式密度场景仍需人工微调。
5. **机器路径**：`deck.slides[].figure.image` 与 `sources[].path` 记录**本次运行机器**的
   实际路径（属产物不属包内容）；包内示例已由 `make_examples.py` 净化为相对路径。
6. **PDF 材料**：无抽取库时需 Agent 抽文本后重跑（D3）并在 `uncertainty` 记录方式。
7. **确定性**：同一输入、同一 spec、无 `--edit` 时结构确定，差异仅限时间戳与机器路径
   前缀 —— 这正是"逐页 diff 公平"的前提。
8. **不适用**：论文综述/精读、可视化算法研发、文案润色、PPT 软件研发；SmartArt 等
   智慧型占位符不重排；论文图是位图且无取数数据时**只占位不重绘**。

## 9. 失败处理（一页速查）

| 遇到什么 | 规则 | 会看到什么 |
|-|-|-|
| 材料全缺 / 部分缺 | D1 | `material_warnings` 非空；全缺时 `deck.slide_count=0` |
| 页面数字材料里找不到 | D2 | `unverified_claims` 有该条，**不当作正确数据** |
| PDF 抽不出文本 | D3 | `uncertainty` 记抽取方式；仍不行则 partial |
| `plan_lint` 有偏差 | D4 | `run_meta.spec_lint.problems` 原文 + 状态 partial |
| 位图无数据 | D5 | `figure.kind=placeholder`（灰框占位） |
| 模板打不开 | D6 | `change_records` + `uncertainty` 记降级 |
| 页数超限 | D7 | 压缩后**不静默丢证据页** |
| 字体/PDF 渲染问题 | D8 | `previews.warnings`；PDF 可空但 PNG 仍在 |
| 图表重绘失败 | D9 | `figure.kind=table`（原生可编辑表格） |
| 契约字段缺值 | D10 | 顶层四形态空值，**无 null** |
| 编辑 op 非法 | D11 | `uncertainty` + `changelog` skipped，其余照常 |
| 复核说"契约没回显" | D12 | 先确认 `--case` 已传、字段确已声明 |
| 重复运行出现差异 | D13 | 判断是否仅时间戳/路径前缀 |
| 预算紧张 | D14 | 先落 partial，**逐条列出未完成项** |

## 10. 生态与复用

- **函数级可复用件**：`slide_text.alloc_roles`、`evidence_check.check_claim_numbers` /
  `plan_lint`、`deck_tool.build_chart`、`deck_tool.apply_edits`、`result_tool.validate`。
- **测量台可复用**：`references/measure_gain.py` 的四个指标函数只依赖
  `result.json` 与产物目录，**任何"材料 → 结构化工件"的 Skill 都能改用同一口径自证增益**。
- **模板与代码分离**：换配色/字体/页脚只改 `templates/*.json`；结果信封可被任何验证器复用。
- **方法可迁移**：公平条件清单、指标公式、证伪判据、双形态证据映射、编辑操作目录、
  契约四形态回显 —— 可直接搬到其他"长材料 → 演示稿"的工具里。

## 11. 维护

- 改脚本或文档后，按 [`TEST.md`](TEST.md) 的命令清单自测一遍；
- 改示例相关代码后跑 `python "$SKILL_DIR/scripts/make_examples.py"` 重建
  `examples/output/` 的文本副本（自动净化机器绝对路径）；
- 改了衡量口径或流程后，**同步更新 `GAIN-PROTOCOL.md` 的实测表**（重跑测量脚本），
  不要把旧数字留在文档里；
- 提交前自检包体：只允许的七种扩展名、≤50 文件、单文件 ≤500KB、合计 ≤2MB、
  无 `__pycache__`、无本机绝对路径。
