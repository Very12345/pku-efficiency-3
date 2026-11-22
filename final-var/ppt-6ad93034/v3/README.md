# README.md — 学术 PPT 生成与编辑 Skill（机制与复用显性化版 · ppt-6ad93034）

把固定的科研材料组织成**结构清楚、证据可追溯、可编辑、符合模板约束**的学术汇报产物：
可编辑 PPTX + 每页演讲备注 + 页级证据映射（md/json）+ 渲染预览 + `result.json`；
支持**多轮局部编辑与版本回退**。

**这一版做两件事**：
① **把机制写成可证伪的判据** —— 五个机制 M1–M5，每个都说清"**缺了会怎样**"，
并配一条能在产物里查的痕迹；随包探针 [`references/mechanism_probe.py`](references/mechanism_probe.py)
只读产物、会在机制痕迹被破坏时报 FAIL（负例控制见 [`references/MECHANISM.md`](references/MECHANISM.md) §5）。
② **把可复用的东西交出去** —— 九个可独立拿走的资产（契约+信封、判据探针、对照测量台、
页面骨架与角色词表、编辑操作目录、模板参数、数字核验器、示例冒烟题集、契约与状态规范），
清单与复用命令见 [`references/REUSABLE-ASSETS.md`](references/REUSABLE-ASSETS.md)。

| 想找什么 | 去哪看 |
|-|-|
| 五个机制、"缺了会怎样"、判据 | [`references/MECHANISM.md`](references/MECHANISM.md) ★本版核心 |
| 能拿走的资产与复用命令 | [`references/REUSABLE-ASSETS.md`](references/REUSABLE-ASSETS.md) ★本版核心 |
| 公平对照协议、指标公式、实测记录 | [`references/GAIN-PROTOCOL.md`](references/GAIN-PROTOCOL.md) |
| 五维评分逐点落点 | [`references/RUBRIC_MAP.md`](references/RUBRIC_MAP.md) |
| `result.json` 契约与 G1–G8 门 | [`references/OUTPUT_CONTRACT.md`](references/OUTPUT_CONTRACT.md) |
| 失败模式 / 降级 / 状态一致性 / 退出码 | [`references/failure-modes.md`](references/failure-modes.md) |
| 页面蓝图与模板槽位 | [`references/DECK_SPEC.md`](references/DECK_SPEC.md) |
| 编辑操作目录与决策树 | [`references/EDIT_OPS.md`](references/EDIT_OPS.md) |
| 本机实测记录（命令 / 退出码 / 负路径 / 探针） | [`TEST.md`](TEST.md) |
| 最小示例与应产出清单 | [`examples/README.md`](examples/README.md)、[`examples/EXPECTED-OUTPUT.md`](examples/EXPECTED-OUTPUT.md) |

## 1. 快速开始

`$SKILL_DIR` = **含 `SKILL.md` 的技能根目录**（平台容器内为 `/skills/weekly-skill`）。
所有命令都写成 `$SKILL_DIR/…`，因此 **cwd 不是技能根目录也能跑**。

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

# ④ 机制判据探针（M1–M5，期望 5/5 PASS、exit 0）
python "$SKILL_DIR/references/mechanism_probe.py" --out "$OUT"

# ⑤ 局部编辑 + 版本归档
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
    --out "${OUT}-edit" --edit "$SKILL_DIR/examples/edit_demo.json" --version v2
```

平台运行形态：输入 `/input/case.json` + `/input/task.md`，产物写 `/app/output`：

```bash
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output
```

> ⚠ **两条自我约束**：① 绝不在技能包目录里运行任何脚本（会生成 `scripts/__pycache__/`，
> 平台预检直接拒收整包）；② 步骤 ② 的 `--case` 必须传。

## 2. 五个机制（一句话版）

| # | 机制 | 缺了会怎样 | 判据 / 复核 |
|-|-|-|-|
| M1 | 页面单元化与角色确定性（`alloc_roles`） | 退化成"一页一段"的文本流，页数由段落数决定、页间无分工 | 每页 `role` 非空，`slide_count` = 页数 |
| M2 | 主张—证据锚定（`check_claim_numbers`） | 数字与原文之间失去可查的连线，抄错发现不了 | 每条数字主张有 `evidence`；`unverified_claims` 有解释 |
| M3 | 图表四态绑定（`bind_figures`） | 位图无数据时要么丢信息，要么"凭空生成曲线" | `chart_image` 的图片与表文件都在；无数据只 `placeholder` |
| M4 | 版本与可复核链（`apply_edits` + changelog + manifest） | 只有一个 deck、改动无记录、交付字节无法对拍 | deck 可重开且页数一致；多版本并存；changelog/manifest 在 |
| M5 | 契约四形态 + 三层验证（`apply_output_contract` + G1–G8） | 字段 `null` 让下游崩；未核验数字也标 success | 顶层无 `null`；契约字段逐项回显；`{"valid": true}` |

展开（实现位置、产物退化形态、证伪条件、负例控制）见
[`references/MECHANISM.md`](references/MECHANISM.md)。

## 3. 目录结构

```
SKILL.md                    # 技能本体：frontmatter + 机制表 + CP1–CP4 + 工具三件 + 自查清单
README.md                   # 本文件：机制速览/用法/可复用资产/目录/依赖/限制/维护
TEST.md                     # 本机真实实测记录（含探针实测与负例控制）
GITHUB_URL.txt              # 公开作品链接
scripts/                    # 四层职责 + 编排 + 维护（算法与 CLI 接口保持稳定）
  main.py                   # 编排：CP1–CP4 + --edit 模式
  deck_extract.py           # extract：读实际材料（case/task/md/txt/html/csv/pdf）
  slide_text.py             # build：角色分配（M1）+ 页面文案骨架
  deck_tool.py              # build：模板槽位建稿 + 四态图表绑定（M3）+ 编辑操作（M4）
  render_qa.py              # render：PIL 预览 + reportlab PDF + 渲染 QA
  evidence_check.py         # verify：数字核验（M2）+ 证据脚注 + CP2 plan_lint
  result_tool.py            # verify：result 信封 + 双形态证据映射 + G1–G8（M5）
  selftest.py               # verify：端到端产物自检
  deck_common.py            # 公共：自定位/字体探测/哈希/原子写/日志
  make_examples.py          # 维护：真跑示例重建 examples/output 并净化机器路径
templates/
  default.json              # 默认模板 spec（参数化，可直接拿走复用）
  result_envelope.json      # 结果信封声明（G8 依据，可直接拿走复用）
references/
  OUTPUT_CONTRACT.md        # result.json 契约 + G1–G8 + 判读规则
  RUBRIC_MAP.md             # 五维评分（40/25/15/10/10）→ 文件与复核命令
  MECHANISM.md              # ★ 五个机制 + "缺了会怎样" + 判据 + 负例控制
  REUSABLE-ASSETS.md        # ★ 九个可复用资产 + 复用命令 + 移植步骤 + 边界
  GAIN-PROTOCOL.md          # 公平对照协议 + 指标公式 + 实测记录 + 证伪判据
  mechanism_probe.py        # ★ 机制判据探针（只读产物；包外运行）
  measure_gain.py           # ★ 对照测量台（两侧指标实现；包外运行）
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

## 4. 可复用资产（九个，详见 `references/REUSABLE-ASSETS.md`）

| # | 资产 | 拿走它能干什么 |
|-|-|-|
| A1 | `templates/result_envelope.json` + `references/OUTPUT_CONTRACT.md` | 给任何产出 `result.json` 的工具当校验依据 |
| A2 | `references/mechanism_probe.py` | 对任意一次运行的产物做 M1–M5 痕迹检查（**最独立**） |
| A3 | `references/measure_gain.py` | 对任何"材料 → 结构化工件"的 Skill 做同口径对照测量 |
| A4 | `scripts/slide_text.py` 的 `ROLE_LABELS` / `alloc_roles` | 把"材料结构 → 页面角色"的取舍规则搬走 |
| A5 | `references/EDIT_OPS.md` + `apply_edits` | 局部改稿 + 版本归档的 op 词表与决策树 |
| A6 | `templates/default.json` + `--template` | 换配色/字体/页脚**不改代码** |
| A7 | `scripts/evidence_check.py`（CLI/函数） | 任何"页面/报告 vs 原文"的数字一致性检查 |
| A8 | `examples/` + `EXPECTED-OUTPUT.md` | 新实现的接口冒烟与产物清单对拍 |
| A9 | `references/failure-modes.md` §4/§5/§6 | 契约四形态表与状态一致性表，可直接当规范引用 |

## 5. 依赖

| 依赖 | 版本 | 用途 | 缺失时的行为 |
|-|-|-|-|
| python-pptx | >=0.6.21 | 可编辑 PPTX；M4 探针重开检查 | **致命**：如实报 partial/failed |
| matplotlib | >=3.5 | 数据表重绘图表（M3 的 `chart_image`） | 降级 PPTX 原生可编辑表格（D9） |
| Pillow | >=9 | PNG 预览 | 预览缺 PNG → G5 报错、自检不过（D8） |
| numpy | 任意 | 图表 | 随 matplotlib |
| reportlab | 任意 | PDF 预览 | 跳过 PDF，记 warning（D8） |
| fitz / pypdf / pdfplumber | 任选其一 | PDF 材料抽取 | Agent 抽文本后重跑（D3） |

安装：`pip install python-pptx matplotlib pillow numpy reportlab`。
**探针与测量台只依赖标准库**（探针的 pptx 重开检查在缺 python-pptx 时如实报 FAIL，
不会假装通过）。

## 6. 输入格式（`case.json`）

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

## 7. 命令索引与退出码

| 命令 | 作用 | 退出码 |
|-|-|-|
| `main.py --case C --out O` | 端到端（CP1–CP4） | 0=success / 1=partial / 2=输入不可读 |
| `--template <spec.json>` | 换模板 spec（A6） | — |
| `--input-dir <dir>` | `--case` 相对路径的基准目录 | — |
| `--max-slides N` | 覆盖页数上限（3–20） | — |
| `--edit <edits.json> --version v2` | 局部编辑 + 版本归档（M4） | 同上 |
| `--no-chart` | 强制图表降级（M3 的 `table` 态） | — |
| `--draft` | 草稿模式（跳过 PDF 预览） | — |
| `--verbose` | 详细日志 | — |
| `result_tool.py --result R --out-dir O --case C --envelope E` | 契约门 G1–G8（M5） | 0=通过 / 1=有未过项 / 2=result 不可读 |
| `selftest.py --out O --case C [--pptx P] [--slides N]` | 产物自检 | 0=全过 / 1=有未过项 |
| `evidence_check.py --claim "…" --material M` | 单条数字核验（M2） | 0=全部找到 / 1=有缺失 |
| `make_examples.py [--dry-run]` | 重建示例文本产物 | 0 / 2=输入不可读 |
| `references/mechanism_probe.py --out O` | 机制判据 M1–M5（包外运行） | 0=5/5 通过 / 1=有 FAIL / 2=输入不可读 |
| `references/measure_gain.py --skill-dir D --case C …` | 对照测量（包外运行） | 0=完成 / 2=输入不可读 |

## 8. 输出与验收

- `work/deck.pptx`（可编辑）、`work/plan.json`（页面模型）
- `preview/slide_*.png`、`preview/preview.pdf`（+ `work/preview/` 同名副本）
- `result.json`（契约全字段 + `run_meta`）、`evidence_map.md/json`（双形态）
- `changelog.jsonl`、`manifest.json`（全部产物 sha256）、`logs/`

**验收判据**：`result_tool.py` → `{"valid": true}` 且 exit 0（G1–G8 全过）；
`selftest.py` → `all_pass=true`；**机制探针 5/5 PASS**；PPTX 可被 python-pptx 重新打开
且页数与 plan 一致；每页有备注与证据脚注；`unverified_claims` 与 `uncertainty` 逐条可解释。

## 9. 限制与已知问题（诚实声明）

1. **判据是必要条件**：探针 PASS 只说明"机制痕迹在"，不说明"这一版讲得好"。
2. **对照的性质**：`measure_gain.py` 给的是受控脚本级对照（基线 = 题面点名失败形态的
   确定性代理实现），平台官方的 Agent 级对照由平台生成；范围声明与局限见
   `references/GAIN-PROTOCOL.md`。
3. **预览 ≠ Office 导出**：无 PowerPoint/LibreOffice 时 PNG/PDF 由 PIL/reportlab 渲染；
   需要 Office 级 PDF 请在装有 Office 的机器上转换 `work/deck.pptx`。
4. **CJK 字体**：预览依赖主机字体，按跨平台候选链探测（Windows `C:/Windows/Fonts`
   → macOS `/System/Library/Fonts` → Linux `/usr/share/fonts`）；找不到时预览出现方块但
   **PPTX 不受影响**，事实写入 `previews.warnings`。包内**不含任何字体文件**。
5. **版式视觉微差**：PIL 预览与 PowerPoint 实际渲染有像素级差异；溢出防护按字符宽度
   估算，极端长词/高公式密度场景仍需人工微调。
6. **机器路径**：`deck.slides[].figure.image` 与 `sources[].path` 记录**本次运行机器**的
   实际路径（属产物不属包内容）；包内示例已由 `make_examples.py` 净化为相对路径。
7. **PDF 材料**：无抽取库时需 Agent 抽文本后重跑（D3）并在 `uncertainty` 记录方式。
8. **不适用**：论文综述/精读、可视化算法研发、文案润色、PPT 软件研发；SmartArt 等
   智慧型占位符不重排；论文图是位图且无取数数据时**只占位不重绘**。

## 10. 失败处理（一页速查）

| 遇到什么 | 规则 | 会看到什么 |
|-|-|-|
| 材料全缺 / 部分缺 | D1 | `material_warnings` 非空；全缺时 `deck.slide_count=0` |
| 页面数字材料里找不到 | D2 | `unverified_claims` 有该条，**不当作正确数据** |
| PDF 抽不出文本 | D3 | `uncertainty` 记抽取方式；仍不行则 partial |
| `plan_lint` 有偏差 | D4 | `run_meta.spec_lint.problems` 原文 + 状态 partial |
| 位图无数据 | D5 | `figure.kind=placeholder`（灰框占位，M3 的合法交付态） |
| 模板打不开 | D6 | `change_records` + `uncertainty` 记降级 |
| 页数超限 | D7 | 压缩后**不静默丢证据页** |
| 字体/PDF 渲染问题 | D8 | `previews.warnings`；PDF 可空但 PNG 仍在 |
| 图表重绘失败 | D9 | `figure.kind=table`（原生可编辑表格） |
| 契约字段缺值 | D10 | 顶层四形态空值，**无 null** |
| 编辑 op 非法 | D11 | `uncertainty` + `changelog` skipped，其余照常 |
| 复核说"契约没回显" | D12 | 先确认 `--case` 已传、字段确已声明 |
| 重复运行出现差异 | D13 | 判断是否仅时间戳/路径前缀 |
| 预算紧张 | D14 | 先落 partial，**逐条列出未完成项** |

## 11. 维护

- 改脚本或文档后，按 [`TEST.md`](TEST.md) 的命令清单自测一遍（含探针）；
- 改示例相关代码后跑 `python "$SKILL_DIR/scripts/make_examples.py"` 重建
  `examples/output/` 的文本副本（自动净化机器绝对路径）；
- 改了机制实现或判据后，**同步更新 `references/MECHANISM.md` 的判据表与实测行**，
  并重跑探针（含负例控制），不要把旧数字留在文档里；
- 提交前自检包体：只允许的七种扩展名、≤50 文件、单文件 ≤500KB、合计 ≤2MB、
  无 `__pycache__`、无本机绝对路径。
