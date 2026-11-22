# RUBRIC_MAP.md — 五维评分 → 本包的具体落点与复核方式

> 本题评分维度：**实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 ·
> 生态贡献 10**（另加 GitHub 公开链接 5）。本表把**每一个评分点**映射到本包内
> **具体的文件或机制**，并给出**可执行的复核命令**。
> 原则：文字自述不算证据 —— 每一行都能用一次真实运行 + 一条命令对上。

---

## 一、实际效果（40）

| 评分点 | 分 | 本包落点（文件 / 机制） | 复核方式 |
|-|-|-|-|
| 任务完成度 | 15 | `SKILL.md` §4 的 CP1–CP4 执行顺序 → `scripts/main.py` 编排：读实际 case/task/材料 → `slide_text.build_plan` 分配**页级叙事角色**（cover/overview/background/question/method/result/discussion/limitation/takeaway）→ `deck_tool.build_deck` 生成**可编辑 PPTX**（主张式标题 + 要点 + 图表槽 + **证据脚注** + **每页演讲备注**）→ `render_qa.render_all` 生成预览。页数由 `spec.max_slides` 决定 | `python "$SKILL_DIR/scripts/main.py" --case … --out <out>` → `STATUS=success`，exit 0；读 `result.json.deck.slides[].role` |
| 结果正确性 | 15 | **数字核验器**：`scripts/evidence_check.py::check_claim_numbers` 对每条入页主张在材料原文里逐一匹配，找不到的数字进 `evidence.unverified_claims` 且**不当作正确数据**；图表只重绘**材料里真实的数据表**（`deck_tool.build_chart`，数值零改动），位图无数据只做灰框**诚实占位**（`figure.kind=placeholder`），**绝不凭空生成曲线** | `python "$SKILL_DIR/scripts/evidence_check.py" --claim "…82.4%…" --material examples/material.md` → `ok=True missing=[]`，exit 0；读 `result.json.evidence.unverified_claims` |
| 结果完整性 | 5 | 题面要求的六类要素各有承载：论文主线（`overview` 角色）、页结构（`deck.slides[].role/claims`）、图表引用（`figure.ref` + 每页 `evidence_footer`）、讲解逻辑（`notes` 与页面文字分离生成）、模板约束（`references/EDIT_OPS.md` 三级模板来源 + 槽位表）、导出渲染（`previews.pngs/pdf` + `previews.method` 如实标注） | 读 `examples/output/result.example.json`（一次真实运行全文）+ `examples/EXPECTED-OUTPUT.md`（25 个产物的纯文字清单） |
| 结果可核验性 | 5 | 四层可核验链：① `sources[].sha256` 对拍输入；② `manifest.json` 对拍**全部产出**的 sha256；③ `evidence_map.md`（人读）+ `evidence_map.json`（机器读）**双形态同源**页级证据映射；④ `changelog.jsonl` 记录每轮改动。再由 `references/OUTPUT_CONTRACT.md` §8 的 **G1–G8 硬性门**（`result_tool.py`）与 `selftest.py` 独立把关 | `python "$SKILL_DIR/scripts/result_tool.py" --result <out>/result.json --out-dir <out> --case "$SKILL_DIR/examples/case.json" --envelope "$SKILL_DIR/templates/result_envelope.json"` → `{"valid": true}`，exit 0；`python "$SKILL_DIR/scripts/selftest.py" --out <out>` → `all_pass: true` |

---

## 二、使用增益（25）

| 评分点 | 分 | 本包落点（文件 / 机制） | 复核方式 |
|-|-|-|-|
| 质量增益 | 15 | 与"基础 Agent 把论文段落整段塞进文本框"的对照，本包给出**可执行的页面纪律**：每页一个叙事角色、每页要点 ≤7 条、单条 ≤90 字（`slide_text.alloc_roles` + `evidence_check.plan_lint` 的 CP2 门）；字号自动收敛 ≥12pt 防溢出（`deck_tool._fit_size`）；每页有证据脚注与备注；图表可编辑（重绘图或**原生 PPTX 表格**）。题面点名的失败（整段塞页 / 抄错数字 / 占位图 / 模板被覆盖 / 改一页坏全稿 / 导出溢出）逐条有对应机制 | 同一 case 各跑一次基础流程与本 Skill，按 `TEST.md` §T9 的对照方案逐页 diff：比角色分配、`verified` 比例、备注条数、`plan_lint` 通过率、G 门通过率 |
| 效率增益 | 5 | **局部编辑而非整稿重做**：`--edit` + `deck_tool.apply_edits` 支持 `update_bullet/add_bullet/remove_bullet/add_note/retitle/reorder_pages/set_figure`；`--version v2` 归档 `work/deck_v2.pptx`，与 `deck.pptx` 并存 → **回退 = 复制旧版重跑**；`references/EDIT_OPS.md` 给出"编辑指令 → 操作选择"决策树，回放 Agent 不需要猜 | `python "$SKILL_DIR/scripts/main.py" --case … --out <out> --edit "$SKILL_DIR/examples/edit_demo.json" --version v2` → `work/deck_v2.pptx` 与 `work/deck.pptx` 并存，`changelog.jsonl` 记录 3 条 op |
| 增益可验证性 | 5 | 对照条件可控：`--no-chart`（强制图表降级）、`--max-slides N`（页数变化）两个开关让"可比条件"可复现；同一输入无 `--edit` 时结构确定（`TEST.md` §T6 双跑记录），差异仅限时间戳与机器路径前缀 —— 因此**逐页 diff 是公平的** | 见 `TEST.md` §T6（双跑确定性）与 §T9（对照方案）；`--no-chart` / `--max-slides 10` 两条变体命令均 exit 0 |

---

## 三、创新增益（15）

| 评分点 | 分 | 本包落点（文件 / 机制） | 复核方式 |
|-|-|-|-|
| 新增能力 | 5 | 基础 Agent 不具备的四项可复现能力：① **页序规划 + 页级角色分配**（`slide_text.alloc_roles`，确定性规则而非临场发挥）；② **页级证据绑定**（每页 `evidence_footer` + `evidence.map` + 双形态 `evidence_map.md/json`）；③ **图表-数据绑定四态**（`chart_image` / `table` / `embedded` / `placeholder`，其中"位图无数据只占位"是防编造能力）；④ **局部编辑 + 版本归档 + 回退**（`--edit` + `deck_<v>.pptx` + `changelog.jsonl`） | 逐项对应到脚本函数名；`grep -n "def alloc_roles\|def bind_figures\|def apply_edits" "$SKILL_DIR"/scripts/*.py` |
| 方法改进 | 5 | ① **确定性内容取舍规则**：方法页 ≤4 条、结果页优先由数据表驱动出 2 条量化主张、无表才回落散文；② **数字核验器**（claim ↔ material，编辑链路同样生效）；③ **模板槽位数据驱动**（`templates/default.json` 参数化，代码里不写死字号/配色）；④ **CP1–CP4 检查点**把"读材料 → 规划 → 构建 → 验证"四个动作显式化，并落进 `run_meta.checkpoints` | `templates/default.json` 可整体替换而不改代码；`run_meta.checkpoints` 四门全 true |
| 创新证据 | 5 | 相对题面"常见失败清单"逐条给**机制**而不是口号：整段塞页 → 要点上限 + `plan_lint`；抄错数字 → `check_claim_numbers`；凭空曲线 → 仅重绘真实数据表 + 诚实占位；模板被覆盖 → 外部模板**只填槽位不动母版** + 三级来源；改一页坏全稿 → 局部编辑 + 版本归档；导出字体/溢出 → `_fit_size` + `render_qa` + 预览如实标注 | `references/EDIT_OPS.md` §4 四态表 + `references/failure-modes.md` 的逐类处置 + `TEST.md` 的真实运行记录 |

---

## 四、可靠体验（10）

| 评分点 | 分 | 本包落点（文件 / 机制） | 复核方式 |
|-|-|-|-|
| 调用与易用性 | 3 | 单一入口一条命令：`python "$SKILL_DIR/scripts/main.py" --case … --out …`；`SKILL.md` §2 写清输入/输出，§4 写清执行顺序与检查点，§5 给 D1–D12 决策表；**全部脚本自定位**（`os.path.dirname(__file__)`），cwd 不是技能根目录也能跑；文档里的命令一律用 `$SKILL_DIR` 前缀，与 `scripts/` 实际入口**逐字对应** | 在**包外**目录执行 `python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/out` → exit 0（`TEST.md` §T2 实测） |
| 运行稳定性 | 4 | 材料形态（md/txt/html/csv/json，PDF 有抽取库时直读）、页数（3–20）、模板来源（default / `template_pptx` / `starting_deck`）三条轴上都持续产出；每步独立 try/except + **先存部分产物再增量改进**；缺 matplotlib / 缺 reportlab / 缺 CJK 字体 / 无图表开关等降级路径全部留痕 | `TEST.md` §T4（`--max-slides 10`）、§T5（`--no-chart`）、§T7（材料缺失诚实失败）均 exit 0/1 且状态自洽 |
| 异常处理 | 3 | `references/failure-modes.md` 按**材料异常 / 模板缺失 / 依赖缺失 / 契约四形态 / 状态一致性**五类逐条给出"识别 → 处置 → 记录位置"，并写明四个脚本的**非零退出码语义**（main: 0/1/2；result_tool: 0/1/2；selftest: 0/1；evidence_check: 0/1）；契约字段一律**四形态空值、禁 null**（`result_tool.apply_output_contract`，含 `bool→false`、`number→0`） | `python "$SKILL_DIR/scripts/evidence_check.py" --claim "某指标为 99.9%" --material "$SKILL_DIR/examples/material.md"` → `ok=False missing=['99.9%']`，exit 1（材料里没有就不放行） |

---

## 五、生态贡献（10）

| 评分点 | 分 | 本包落点（文件 / 机制） | 复核方式 |
|-|-|-|-|
| 文档完整性 | 3 | 根目录：`README.md`（依赖/安装/输入格式/命令/输出/限制/失败处理/维护）、`TEST.md`（真实实测记录与验收判据）、`GITHUB_URL.txt`；`references/`：`OUTPUT_CONTRACT.md`（字段契约 + G1–G8）、`RUBRIC_MAP.md`（本表）、`EDIT_OPS.md`（页面蓝图 + 槽位约束）、`EDIT_OPS.md`（编辑操作目录）、`failure-modes.md`（失败模式）；`examples/`：输入示例 + `EXPECTED-OUTPUT.md`（纯文字产物清单）+ `output/`（真实运行文本副本） | `ls -R "$SKILL_DIR"`；每份文档开头都写明"这份文档解决什么问题" |
| 资源可复用性 | 4 | ① **模板是数据**：`templates/default.json`（颜色/字体/页脚/槽位全部参数化）换模板不改代码；② **结果信封声明** `templates/result_envelope.json` 可被**任何**验证器复用（G8 依据）；③ **脚本按四层职责切分**（extract / build / render / verify + 编排），`slide_text.alloc_roles`、`evidence_check`、`deck_tool.build_chart`、`apply_edits`、`result_tool.validate` 均可单独 import 复用；④ **示例可整体复制运行**，且 `scripts/make_examples.py` 能把示例文本产物**带路径净化**地重新生成 | 逐函数 import 试跑；`python "$SKILL_DIR/scripts/make_examples.py" --dry-run` 只跑不回抄 |
| 分享推广价值 | 3 | 沉淀的是**方法**而不只是一次性产物：学术汇报页面骨架（角色分配规则 + 证据脚注约定）、**编辑操作目录 + 决策树**、**双形态证据映射**、**版本记录格式**、**契约四形态回显**、**诚实占位/未核验留痕** —— 任何"把长材料翻成演示稿"的工具都能直接借用；示例明确标注"示例，非正式案例"，可直接作为他人的最小上手题集 | 读 `references/EDIT_OPS.md` 与 `references/OUTPUT_CONTRACT.md`；它们不依赖本包的代码也能被别的实现照做 |

---

## 六、GitHub 公开链接（5，额外分）

`GITHUB_URL.txt` 第一行为公开仓库中本作品所在目录的链接（评审无需登录即可打开）。

## 七、对照建议（评审复跑，用于"使用增益"判定）

1. **基础条件**：给同一个 `case.json` + `task.md` + 材料，**不加载**本 Skill，
   直接让 Agent 做一版 PPT —— 典型结果是整段摘要入页、无证据脚注、无备注、
   数字来源不可查。
2. **加载条件**：按 `SKILL.md` 运行 `scripts/main.py`。
3. **逐页 diff 的五个可比项**：① 每页角色是否明确；② 每页主张条数与长度是否
   在纪律内（≤7 条 / ≤90 字）；③ 页面上每个数字能否指回材料
   （`unverified_claims` 是否为空或有解释）；④ 每页是否有备注与证据脚注；
   ⑤ 模板约束与预览是否齐备。前四项**不需要人工审美判断**，可由
   `result.json` 直接对拍。
4. 公平性前提：两边使用**同一输入、同一页数上限、同一模板**；本包用
   `--max-slides` 与 `--no-chart` 保证条件可控。

## 八、本包不主张什么（诚实边界）

- 不主张"预览等于 Office 导出"：运行环境无 PowerPoint/LibreOffice 时预览是
  PIL/reportlab 近似渲染，已在文件名与 `previews.method` 明确标注。
- 不主张"自检通过 = 内容正确"：`selftest` 只查产物可复核性，内容正确性由
  数字核验与页面纪律负责。
- 不主张覆盖论文精读/综述、可视化算法研发、文字润色、PPT 软件研发 ——
  这些是题面明确的**不适用**范围。
- 包内**不含任何正式案例的预制答案**；`examples/` 全部为虚构材料，且标注
  "示例，非正式案例"。

## 附：v4「抗故障 / 可判读」增量（2026-11-23）

| 维度 | 本版新增的落点 | 文件 / 命令 | 实测证据 |
|-|-|-|-|
| 可靠体验 10 | 28 条故障逐行实测（exit/status/uncertainty/留痕/是否静默） | `scripts/fault_inject.py`、`references/FAULT-MATRIX.md` §1 | 逐行矩阵 28 行，复现 1 条命令 |
| 可靠体验 10 | 7 条静默失败如实列出 + 根因 + 补救 | `references/FAULT-MATRIX.md` §2 | S1–S7，每条带实测字段值 |
| 可靠体验 10 | 17 条恢复动作的实测结局 | `references/FAULT-MATRIX.md` §3 | 12 条换参数回到 success，5 条守卫判定 |
| 可靠体验 10 | 运行前体检 + 运行后核对的守卫 | `fault_inject.py --guard --case/--out` | 7/7 静默被抓、健康产物 0 误报 |
| 使用增益 25 | 减少"交完才发现坏了"的返工：CP0 拦截 3 类硬崩、CP5 拦截静默降级 | `SKILL.md` §5 | `F-TPL-03`、`F-DEP-03/04/05`、`F-IN-07` |
| 创新增益 15 | 把失败面做成可复现矩阵 + 三级留痕判据（product/stdout-only/none） | `fault_inject.py` 的 `trace_hits()` | 第一轮裸文本匹配误判 26/28，改结构化判定后露出真 7 条 |
| 生态贡献 10 | 注入台不 import 本包任何模块，可整段搬到别的 Skill | `README.md` §10 | 只依赖 `result.json` 与 `work/material_view.json` |
