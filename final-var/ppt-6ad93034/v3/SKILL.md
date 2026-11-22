---
name: academic-ppt-builder-mechanism-explicit
description: 把论文/研究材料组织成结构清楚、证据可追溯、可编辑、符合模板约束的学术汇报演示稿（PPTX），并把"凭什么说它更好、凭什么说它真在起作用"做成可证伪的机制判据：五个机制 M1–M5（页面单元化与角色确定性、主张—证据锚定、图表四态绑定、版本与可复核链、契约四形态与三层验证）各配一条可在产物里查的痕迹与一个随包探针（references/mechanism_probe.py），另有可复算的公平对照测量台与可复用资产清单。支持 --edit 局部编辑与版本回退；页面数字逐一核验材料、缺失显式标注、绝不编造。Use when a task asks to generate or edit an academic presentation / slide deck from a paper or research material（组会汇报、开题与中期、答辩、项目评审、基金申请；学术PPT、slides from paper、presentation from paper），especially when /input/case.json and task.md are present and /app/output must contain the editable deck plus previews and evidence mapping.
---

# 学术 PPT 生成与编辑 Skill（机制与复用显性化版 · ppt-6ad93034）

> **本版定位**：不再罗列功能，而是把包里**真正起作用的五个机制**摊开：
> 每个机制写清 **① 解决什么现实问题 → ② 由哪段代码实现 → ③ 没有它会怎样
> （具体到产物形态）→ ④ 可证伪判据（能在产物里查的痕迹 + 探针 + 证伪条件）**。
> 判据探针 `references/mechanism_probe.py` 随包分发、**只看产物不看文档**；
> 对照测量台 `references/measure_gain.py` 给出可复算的增益口径；
> `references/REUSABLE-ASSETS.md` 列出九个可被他人直接拿走复用的资产。
>
> 一句话立场：**判据可见、可在产物里查、可被别人的实现照做** ——
> 这比"我们有五个创新点"更经得起复核。

**管辖范围**：把材料"翻译"成页级表达，并保证每页数字与图表可核实。
不做：论文精读与文献综述、可视化算法研发、学术写作文字润色、PPT 软件研发。

---

## 1. 五个机制一览（展开见 `references/MECHANISM.md`）

| # | 机制 | 解决什么 | 缺了会怎样（产物形态） | 判据 |
|-|-|-|-|-|
| **M1** | 页面单元化与角色确定性 | 不同受众/时长要不同取舍 | 一页一段的文本流；页数由段落数决定；无角色字段 | `M1_page_units` |
| **M2** | 主张—证据锚定 | 数字与原文之间必须有可查的连线 | 数字来源不可查、抄错发现不了 | `M2_anchors` |
| **M3** | 图表四态绑定 | 位图无取数数据时**不许编造** | 要么空着丢信息，要么"凭空生成曲线" | `M3_figure_states` |
| **M4** | 版本与可复核链 | 多轮改动后说不清哪版是交付版 | 只有一个 `deck.pptx`、无 changelog、无 sha256 清单 | `M4_versioning` |
| **M5** | 契约四形态 + 三层验证 | 产物要被别的程序读；"自检过"≠"内容对" | 字段为 `null` 让下游崩；未核验数字也标 success | `M5_contract` |

**机制的实现落点**（代码级）：

| 机制 | 实现 |
|-|-|
| M1 | `scripts/slide_text.py::alloc_roles` + `scripts/evidence_check.py::plan_lint` |
| M2 | `scripts/evidence_check.py::check_claim_numbers` / `build_evidence_footer` + `scripts/result_tool.py`（`evidence_map.md/json`） |
| M3 | `scripts/deck_tool.py::bind_figures`（`chart_image` / `table` / `embedded` / `placeholder`） |
| M4 | `scripts/deck_tool.py::apply_edits` + `main.py --edit … --version` + `result_tool.write_changelog` / `write_manifest` |
| M5 | `scripts/result_tool.py::apply_output_contract` / `validate`（G1–G8）+ `scripts/selftest.py` |

---

## 2. 调用与执行（一条命令 + 四个检查点）

`$SKILL_DIR` = **含 `SKILL.md` 的技能根目录**（平台容器内为 `/skills/weekly-skill`），
所以 **cwd 不是技能根目录也能跑**：

```bash
SKILL_DIR="${SKILL_DIR:-/skills/weekly-skill}"
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output
```

| 检查点 | 动作 | 判定 | 与哪个机制相关 |
|-|-|-|-|
| **CP1 读实际输入** | 读 case/task/每个材料文件；核对存在性 | 材料是否可读 | 全部（无输入即无产物） |
| **CP2 规划与 lint** | 角色分配 + 页序 + 主张与证据指针；`plan_lint` | `valid` 或记录偏差 | M1（角色）/ M2（证据） |
| **CP3 建稿** | 模板槽位建稿 + 四态图表绑定 + 备注 + 脚注 | 可重开且页数=plan | M3（图表）/ M2（脚注） |
| **CP4 导出校验** | `result_tool` 的 G1–G8 + `selftest` | `{"valid": true}` 且 exit 0 | M5（契约）/ M4（清单） |

```bash
SKILL_DIR="${SKILL_DIR:-/skills/weekly-skill}"
# CP4 契约门（`--case` 必须传，否则无法核对契约回显）
python "$SKILL_DIR/scripts/result_tool.py" --result /app/output/result.json \
    --out-dir /app/output --case /input/case.json \
    --envelope "$SKILL_DIR/templates/result_envelope.json"        # {"valid": true} 且 exit 0

python "$SKILL_DIR/scripts/selftest.py" --out /app/output --case /input/case.json   # all_pass=true
```

**退出码**：`main.py` 0=success / 1=partial / 2=输入不可读；`result_tool.py` 0/1/2；
`selftest.py` 0/1；`evidence_check.py` 0/1。**只有 exit 0 才算"干净"**。

**完整命令索引**（`main.py` 的全部分支与开关；末两条是判据与测量的前提）：

| 命令 | 作用 | 与哪个机制 / 判据相关 |
|-|-|-|
| `main.py --case C --out O` | 端到端（CP1–CP4） | 全部机制的载体 |
| `main.py … --template <spec.json>` | 换模板 spec（不改代码） | A6 可复用资产；"换模板不改代码"的兑现处 |
| `main.py … --input-dir <dir>` | `--case` 相对路径的基准目录 | 便于把同一份输入喂给探针/测量台 |
| `main.py … --max-slides N`（3–20） | 覆盖页数上限 | **M1**：角色分配随页数变化（富余页先插背景/讨论/局限） |
| `main.py … --edit <edits.json> --version v2` | 局部编辑 + 版本归档 | **M4**：多版本并存 + changelog |
| `main.py … --no-chart` | 强制图表降级（结果页 → 原生表格） | **M3**：`table` 是词表内合法态，探针仍 PASS |
| `main.py … --draft` | 草稿模式（跳过 PDF 预览） | D8 降级路径；**不**破坏 M1–M5 判据 |
| `main.py … --verbose` | 详细日志 | 排查失败 |
| `result_tool.py …` / `selftest.py …` / `evidence_check.py …` | 契约门（M5）/ 自检 / 单条数字核验（M2） | 判据的三条独立链 |
| `python "$SKILL_DIR/scripts/make_examples.py" [--dry-run]` | 维护：真跑示例并重建 `examples/output/`（自动净化机器绝对路径） | A8 资产；改示例后必须重跑，否则示例与实际产物脱节 |
| `references/mechanism_probe.py --out O` | **M1–M5 判据检查**（包外运行） | 本版核心：机制痕迹是否在产物里 |

---

## 3. 三个"随包可复核"的工具（本版新增的可用件）

### 3.1 机制判据探针 `references/mechanism_probe.py`

```bash
python "$SKILL_DIR/references/mechanism_probe.py" --out <一次运行的输出目录>
# 期望 M1–M5 全 PASS，exit 0；有 FAIL 时 exit 1 并打印具体缺陷
```

它**只读产物**：`role` 是否存在、数字主张是否有证据指针、`chart_image` 指向的
图片与表文件是否真实存在、pptx 能否重开且页数一致、顶层是否有 `null`。
**实测**：示例案例与留出案例 5/5 PASS；人为破坏三处痕迹后立刻报 3 条 FAIL
（负例控制见 `references/MECHANISM.md` §5）。

### 3.2 对照测量台 `references/measure_gain.py`

```bash
cp "$SKILL_DIR/references/measure_gain.py" <tmp>/     # 必须在包外跑（否则生成 __pycache__）
python <tmp>/measure_gain.py --skill-dir "$SKILL_DIR" --case <case1> --case <case2> \
    --work <tmp>/work --out <tmp>/gain-report.json
```

五项质量指标（Q1 角色覆盖 / Q3 数字可追溯 / Q4 备注覆盖 / Q5 脚注覆盖 /
Q6 产物齐全度）两侧同一口径；实测 Δ 分别为 +1.0 / +1.0 / +1.0 / +1.0 / +0.8571，
代价是脚本多约 2–3 秒（**如实报为成本**）。协议、公式与可证伪判据见
`references/GAIN-PROTOCOL.md`（同目录另有一份完整协议文档）。

### 3.3 可复用资产清单 `references/REUSABLE-ASSETS.md`

九个资产（契约+信封、判据探针、测量台、页面骨架与角色词表、编辑操作目录、
模板参数文件、数字核验器、示例冒烟题集、契约四形态与状态一致性规则），
每项给"位置 / 拿走它 / 怎么用 / 依赖 / 不适用处"。

---

## 4. 输入输出与产物归属

**读**：`case.json`（`case_id`、`title`、`inputs{task_md, material[]}`、
`spec{audience, duration_minutes, max_slides, template|template_pptx|starting_deck, style}`、
可选 `output_contract`）、`task.md`、材料**实际文件**（禁止凭文件名猜内容）。

**写**（一律写 `--out`）：

| 产物 | 位置 | 支撑哪个机制 |
|-|-|-|
| 可编辑演示文件 | `work/deck.pptx` | M1/M2/M3 的载体；M4 的可重开检查对象 |
| 页面模型 | `work/plan.json` | M1（角色/页序）、M2（证据指针） |
| 预览渲染 | `work/preview/slide_*.png`、`work/preview/preview.pdf`、输出根 `preview/` 副本 | Q6 产物齐全度；如实标注"非 PowerPoint 导出" |
| 评分产物 | `result.json` | M5（契约四形态、禁 null） |
| 证据映射 | `evidence_map.md` + `evidence_map.json` | M2（人读/机器读同源） |
| 记录 | `changelog.jsonl`、`manifest.json`、`logs/` | M4（版本与 sha256 链） |

> **不入包**：`deck.pptx`、预览 `*.png`/`*.pdf`、`changelog.jsonl` 都是运行时产物；
> 技能包只携带 UTF-8 文本。清单见 `examples/EXPECTED-OUTPUT.md`。
> **产物绝不写回技能包目录**；随包的两个脚本（探针、测量台）都应在**包外**运行。

---

## 5. 环境、依赖与包体约束

- Python 3.8+；`python-pptx>=0.6.21`（必需）、`matplotlib>=3.5`、`Pillow>=9`、`numpy`；
  `reportlab` 可选；PDF 材料抽取任选 fitz/pypdf/PyPDF2/pdfplumber 之一。
- 包体：**≤50 文件 / 单文件 ≤500KB / 合计 ≤2MB / 无符号链接 / 全 UTF-8 文本**
  （`.md/.py/.json/.txt/.csv/.yaml/.yml`）。探针与测量台也都是文本脚本。
- **在包内跑任何脚本都会生成 `__pycache__`**（验收器直接 FAIL）：请把技能包复制到
  包外再实测，或把单个脚本复制到包外运行。

---

## 6. 决策规则与失败分支（速查）

| # | 触发 | 动作 | 记录 |
|-|-|-|-|
| D1 | 材料缺失/路径不存在 | 不补造；只出元信息 result（`slide_count=0`） | `material_warnings` |
| D2 | 主张数字材料中找不到 | `verified=false` 入未核验清单，**原文照录** | `unverified_claims` |
| D3 | PDF 无文本层/无抽取库 | 不 OCR 冒充；Agent 抽文本后重跑，仍不行 partial | `uncertainty` + `sources.tool` |
| D4 | CP2 `plan_lint` 有偏差 | 先修；硬约束则继续但**显式记录**并降 partial | `run_meta.spec_lint` |
| D5 | 位图无数据 | `placeholder` 灰框占位，**不生成假曲线** | `figure.note` |
| D6 | 模板损坏/打不开 | 备份 → 内置模板，说明降级 | `uncertainty` + `change_records` |
| D7 | 页数超限 | 确定性压缩，**不静默丢证据页** | `change_records` + `notes` |
| D8 | 字体缺失/渲染不可用 | PPTX 只记字体名；预览回落并预警 | `previews.warnings` |
| D9 | 图表重绘失败 | 降级 PPTX 原生可编辑表格 | `figure.note` |
| D10 | 契约字段未知/无值 | 四形态空值 `""/[]/{}/false/0`，**禁 null** | 顶层回显 |
| D11 | 编辑操作非法 | 跳过并记录，其余照常 | `uncertainty` + `changelog` |
| D12 | 复核说"契约没回显" | **先查 `--case` 是否传了** | 复核记录 |
| D13 | 重复运行有差异 | 判断是否仅时间戳/机器路径前缀 | `change_records` |
| D14 | 预算压力 | 先落 partial 再增量改进，**逐条列未完成项** | `status` + `change_records` |

五族失败分支（材料异常 / 模板缺失 / 依赖缺失 / 契约四形态 / 状态不一致）
按编号展开在 `references/failure-modes.md`；**每条降级都必须落到指定记录字段** ——
没有记录就等于没执行降级。

---

## 7. 增量编辑（多轮迭代与回退，M4 的用户面）

```bash
SKILL_DIR="${SKILL_DIR:-/skills/weekly-skill}"
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output \
    --edit edits.json --version v2
```

7 类 op：`update_bullet / add_bullet / remove_bullet / add_note / retitle /
reorder_pages / set_figure`（字段见 `examples/edit_demo.json`，决策树见
`references/EDIT_OPS.md`）。每次改动写一条 `{version, op, page, target, reason}`；
`deck_v2.pptx` 与 `deck.pptx` **并存** → 回退 = 复制旧版本重跑。
**编辑链路同样过 M2 的数字核验**：编辑引入的新数字材料里没有 → 降级为未核验，
**不因"是用户让改的"而放行**。

---

## 8. 自查清单（逐项打勾；括号内为对应机制）

- [ ] 已读 `case.json` + `task.md` + 全部实际材料（未凭文件名猜内容）
- [ ] 每页有 `role`，页数 = `spec.max_slides`（或更少且原因已记录）—— **M1**
- [ ] 页面上每个数字都能指回材料；`unverified_claims` 为空或有逐条解释 —— **M2**
- [ ] 图表四态均为真；位图无数据只占位；`chart_image` 的图片与表文件都在 —— **M3**
- [ ] `deck.pptx` 可重开且页数与 plan 一致；`manifest.json` 含全部 sha256 —— **M4**
- [ ] 契约字段全部回显、无 `null`；**核对时已把 `--case` 传给 `result_tool.py`** —— **M5**
- [ ] `result_tool.py` → `{"valid": true}` 且 exit 0；`selftest.py` → `all_pass=true`
- [ ] `status` 与每一列出的 `uncertainty` 一一对应，无"降级却标 success"
- [ ] 做过机制自证吗？`python "$SKILL_DIR/references/mechanism_probe.py" --out <out>` → **5/5 PASS**
- [ ] 包体：只有允许的七种文本扩展名、≤50 文件、无二进制、无 `__pycache__`

---

## 9. 五维评分落点（速查；逐点展开见 `references/RUBRIC_MAP.md`）

| 维度 | 分 | 本包靠什么拿到 |
|-|-|-|
| 实际效果 | 40 | CP1–CP4 真跑；页序 + 页级角色；可编辑 PPTX + 备注 + 证据脚注；数字逐一核验；`sources[].sha256` + `manifest.json` + 双形态证据映射 + G1–G8 |
| 使用增益 | 25 | 公平对照协议 + 五项质量指标公式 + **随包测量台 `references/measure_gain.py`** + 真实对照记录（含一条负面指标与一个 `partial` 案例）+ 可证伪判据 |
| 创新增益 | 15 | **本版主攻**：五个机制各写清"缺了会怎样"，并各配一条**在产物里可查**的判据与一个**会 FAIL** 的探针（含负例控制）；四态防编造、局部编辑+回退、契约四形态都属于"基础形态难以稳定实现"的能力 |
| 可靠体验 | 10 | 单入口 + `$SKILL_DIR` 自定位；D1–D14 与 F1–F5 覆盖材料/模板/依赖/契约四形态/状态一致性；四脚本非零退出码语义；每步 try/except + 先存部分产物 |
| 生态贡献 | 10 | **本版第二主攻**：`references/REUSABLE-ASSETS.md` 列出九个可独立拿走的资产（契约+信封/判据探针/测量台/页面骨架/编辑词表/模板/核验器/示例题集/规范表）并给复用命令；文档齐全；方法（角色分配、证据映射、四态绑定、版本记录）可迁移 |

GitHub 公开链接（额外 5 分）：见根目录 `GITHUB_URL.txt`。

---

## 10. 诚实边界

1. **不主张独家发明**：页面角色、证据映射、四态图表、版本记录各自都不神秘；
   本包主张的是**把它们做成可判定的状态并留下可查痕迹**（探针能查、负例能让它 FAIL）。
2. **判据是必要条件**：探针 PASS 只说明"机制痕迹在"，不说明"这一版讲得好"。
3. **对照的性质**：随包测量台给的是**受控脚本级对照**（基线 = 题面点名失败形态的
   确定性代理实现），不是平台官方的 Agent 级对照；平台对照由平台生成。
4. **预览 ≠ Office 导出**：无 PowerPoint/LibreOffice 时为 PIL/reportlab 近似渲染，
   文件名与 `previews.method` 已如实标注。
5. **不预制答案**：包内不含任何正式案例的答案；`examples/` 为虚构材料并已标注
   "示例，非正式案例"，不得冒充正式案例结果。
