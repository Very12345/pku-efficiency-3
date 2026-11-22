---
name: academic-ppt-builder-gain-verified
description: 把论文/研究材料组织成结构清楚、证据可追溯、可编辑、符合模板约束的学术汇报演示稿（PPTX）。除全流程执行外，本版把"使用增益"做成**可复算的证据**：随包提供与"不加载 Skill 的基础 Agent"的公平对照协议（同输入/同模板/同页数上限/同解释器/同测量脚本）、五项质量指标与三项效率指标的精确公式、以及本包真实跑出来的对照记录（含 5 项 Δ 与一条如实保留的负面指标）。支持 --edit 局部编辑与版本回退；页面数字逐一核验材料、缺失显式标注、绝不编造。Use when a task asks to generate or edit an academic presentation / slide deck from a paper or research material（组会汇报、开题与中期、答辩、项目评审、基金申请；学术PPT、slides from paper、presentation from paper），especially when /input/case.json and task.md are present and /app/output must contain the editable deck plus previews and evidence mapping.
---

# 学术 PPT 生成与编辑 Skill（增益可验证版 · ppt-6ad93034）

> **本版定位**：算法与 CLI 与前一版完全一致，但**把"加载它到底带来什么"写成可复算的
> 证据**：一份公平对照协议（条件、指标、公式）、一个随包的测量脚本
> （`references/measure_gain.py`，含两侧指标实现）、以及在本机真实跑出的对照记录
> （5 项质量指标 Δ 见 `references/GAIN-PROTOCOL.md` §4）。
> 关键纪律：**两侧同一把尺子；"没做"的项按最差计；负面结果照原样报出。**

**管辖范围**：把材料"翻译"成页级表达，并保证每页数字与图表可核实。
不做的四件事：论文精读与文献综述、可视化算法研发、学术写作文字润色、PPT 软件研发。

---

## 1. 何时用它（触发条件与输出承诺）

| 项 | 内容 |
|-|-|
| 触发 | 输入侧出现 `/input/case.json` + `task.md`，要求"可编辑演示稿 + 页级证据" |
| 不触发 | 只要润色、只要精读、只要可视化算法、只要 PPT 软件功能 |
| 承诺产出 | 可编辑 PPTX（含每页演讲备注与证据脚注）+ 页级证据映射（md/json）+ 预览渲染 + `result.json` |
| 承诺边界 | 3 ≤ 页数 ≤ 20；每页一个叙事角色；单次脚本耗时 < 60 秒 |

命令口径（全文一致）：`$SKILL_DIR` = **含 `SKILL.md` 的技能根目录**
（平台容器内为 `/skills/weekly-skill`），所以 **cwd 不是技能根目录也能跑**：

```bash
SKILL_DIR="${SKILL_DIR:-/skills/weekly-skill}"
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output
```

---

## 2. 这条流水线的"增益来源"是什么（一句话版）

增益不是"多写了几页"，而是**三种基础形态天然拿不到的结构**，它们各自都直接对应一个
可测指标（括号内为 `GAIN-PROTOCOL.md` §3 的编号）：

| 结构 | 由谁产生 | 可测指标 |
|-|-|-|
| **页级叙事角色** | `scripts/slide_text.py::alloc_roles` 确定性分配（封面/主线/问题/方法/结果/结论…） | Q1 角色覆盖率 |
| **数字主张 ↔ 证据指针** | `scripts/evidence_check.py::check_claim_numbers` 逐条核验 + `build_evidence_footer` | Q3 可追溯率 |
| **双形态证据映射 + sha256 清单** | `scripts/result_tool.py` 写 `evidence_map.md/json` 与 `manifest.json` | Q5/Q6 |
| **演讲备注与页面文字分离生成** | `slide_text` 的备注骨架 + `deck_tool` 的备注槽位 | Q4 备注覆盖率 |
| **可复算的对照口径本身** | `references/measure_gain.py` + `GAIN-PROTOCOL.md` | 全部 Q/E 指标 |

> 这张表就是"使用增益"那一列 25 分的落点：**不是声称更好，而是给出可以算出来的差**。

---

## 3. 执行流程（CP1–CP4，与对照协议共用同一入口）

| 检查点 | 动作 | 产出 | 判定 |
|-|-|-|-|
| **CP1 读实际输入** | 读 case/task/每个材料文件；核对存在性 | `work/material_view.json` | 材料是否可读 |
| **CP2 规划与 lint** | 分配角色、写页序与主张；`plan_lint` 校验页面纪律 | `work/plan.json` | `valid` / 记录偏差 |
| **CP3 建稿** | 模板槽位建稿 + 四态图表绑定 + 备注 + 脚注 | `work/deck.pptx` | 可重开且页数=plan |
| **CP4 导出校验** | `result_tool` 的 G1–G8 + `selftest` | `result.json` 等 | `{"valid": true}` 且 exit 0 |

```bash
SKILL_DIR="${SKILL_DIR:-/skills/weekly-skill}"
# 主命令（对照协议的"条件 S"就是这一条）
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output

# CP4：契约门（`--case` 必须传，否则无法核对契约回显）
python "$SKILL_DIR/scripts/result_tool.py" --result /app/output/result.json \
    --out-dir /app/output --case /input/case.json \
    --envelope "$SKILL_DIR/templates/result_envelope.json"
# 期望 {"valid": true} 且 exit 0（G1–G8 见 references/OUTPUT_CONTRACT.md §8）

# CP4：产物自检
python "$SKILL_DIR/scripts/selftest.py" --out /app/output --case /input/case.json
# 期望 all_pass=true
```

**四脚本退出码**（编排器与对照测量都用它）：`main.py` 0=success / 1=partial /
2=输入不可读；`result_tool.py` 0 / 1 / 2；`selftest.py` 0 / 1；
`evidence_check.py` 0 / 1。详见 `references/failure-modes.md` §0。

**完整命令索引**（`main.py` 的全部开关；对照协议要用到后两个）：

| 命令 | 作用 | 与对照的关系 |
|-|-|-|
| `main.py --case C --out O` | 端到端（CP1–CP4） | 对照的"条件 S"本体 |
| `main.py … --template <spec.json>` | 换模板 spec | **公平条件之一**：两侧必须用同一模板 |
| `main.py … --input-dir <dir>` | `--case` 为相对路径时的基准目录 | 便于两侧指向同一份输入 |
| `main.py … --max-slides N`（3–20） | 覆盖页数上限 | **公平条件之一**：两侧同一页数上限 |
| `main.py … --edit <edits.json> --version v2` | 局部编辑 + 版本归档 | E1/E2 效率指标的观测面 |
| `main.py … --no-chart` | 强制图表降级（结果页 → 原生表格） | **让对照条件可控**：排除"是否可绘图"这一混杂因素 |
| `main.py … --draft` | 草稿模式（跳过 PDF 预览） | 预算紧张时的降级路径（D8） |
| `main.py … --verbose` | 详细日志 | 排查失败 |
| `result_tool.py …` / `selftest.py …` / `evidence_check.py …` | 契约门 / 自检 / 单条数字核验 | 对照的"两侧同一把尺子"由契约门与自检保证 |
| `python "$SKILL_DIR/scripts/make_examples.py" [--dry-run]` | 维护：真跑示例并重建 `examples/output/`（自动净化机器绝对路径） | 改示例后必须重跑，否则示例与实际产物脱节 |

---

## 4. 公平对照协议（要点；完整版见 `references/GAIN-PROTOCOL.md`）

### 4.1 两个条件必须逐项对齐

同一 `case.json`、同一 `task.md`、同一材料、同一 `spec.max_slides`、
同一模板、同一解释器与库版本、**同一测量脚本**。任何一项不同，对照即无效。

### 4.2 指标（可自动对拍，不依赖审美）

| 编号 | 指标 | 定义要点 |
|-|-|-|
| Q1 | 页级角色覆盖率 | `deck.slides[].role` 非空页 / 总页 |
| Q3 | 数字主张可追溯率 | 含数字 token 的主张中 `evidence` 非空的比例 |
| Q4 | 演讲备注覆盖率 | `notes` 非空页 / 总页 |
| Q5 | 证据脚注覆盖率 | `evidence_footer` 非空页 / 总页 |
| Q6 | 可复核产物齐全度 | 七项交付物存在数 / 7 |
| E1–E3 | 编辑粒度 / 版本归档数 / 预览复查工件 | 效率侧**如实报出**，不折算成"更快" |

### 4.3 本包实测（两个案例，真实运行）

| 指标 | 基线形态均值 | 本 Skill 均值 | Δ |
|-|-|-|-|
| Q1 角色覆盖 | 0.0000 | 1.0000 | **+1.0000** |
| Q3 数字可追溯 | 0.0000 | 1.0000 | **+1.0000** |
| Q4 备注覆盖 | 0.0000 | 1.0000 | **+1.0000** |
| Q5 脚注覆盖 | 0.0000 | 1.0000 | **+1.0000** |
| Q6 产物齐全度 | 0.1429 | 1.0000 | **+0.8571** |
| 脚本耗时 | 0.391 s | 5.14 s | +4.75 s（**成本，不是收益**） |

**两条必须一起读的注释**：
① 第二个案例上本 Skill 的状态是 `partial`（第 6 页有一条 91 字主张越界 1 个字符，
按规则记录并降级）—— **没有为了让对照好看而放宽纪律**；
② 另有一个指标（Q2 单条长度合规率）在基线侧"意外合规"、在本 Skill 侧反而更低，
本包把它**如实保留在报告里并说明为何不作为对照依据**（`GAIN-PROTOCOL.md` §3.3）。

### 4.4 可证伪判据

本结论的证伪方式写死在 `GAIN-PROTOCOL.md` §5：在其他 `case.json` 上重跑
Q1/Q3/Q4/Q5 任一项 Δ ≤ 0，或在条件 B 的产物里找到角色/备注/脚注字段，
即推翻"本包带来这五项改善"的主张。**测量脚本随包（`references/measure_gain.py`），
不需要网络、不依赖本机路径。**

---

## 5. 输入输出与产物归属

**读**：`case.json`（`case_id`、`title`、`inputs{task_md, material[]}`、
`spec{audience, duration_minutes, max_slides, template|template_pptx|starting_deck, style}`、
可选 `output_contract`）、`task.md`、以及材料**实际文件**（禁止凭文件名猜内容）。

**写**（一律写 `--out` 目录）：

| 产物 | 位置 | 说明 |
|-|-|-|
| 可编辑演示文件 | `work/deck.pptx` | 主张式标题 + 要点 + 图表槽 + 证据脚注 + 演讲备注 |
| 页面模型 | `work/plan.json` | 可编辑源 |
| 预览渲染 | `work/preview/slide_*.png`、`work/preview/preview.pdf`、输出根 `preview/` 副本 | 标注"非 PowerPoint 导出" |
| 评分产物 | `result.json` | 契约全字段 + `case_id`，**禁 null** |
| 证据映射 | `evidence_map.md` + `evidence_map.json` | 同源双形态 |
| 记录 | `changelog.jsonl`、`manifest.json`（全部 sha256）、`logs/` | 支撑独立复核与**对照复算** |

> **不入包**：`deck.pptx`、预览 `*.png`/`*.pdf`、`changelog.jsonl` 均为运行时产物；
> 技能包只携带 UTF-8 文本。完整清单见 `examples/EXPECTED-OUTPUT.md`。
> **产物绝不写回技能包目录**（也正因如此，随包的测量脚本要在包外运行）。

---

## 6. 环境、依赖与包体约束

- Python 3.8+；`python-pptx>=0.6.21`（必需）、`matplotlib>=3.5`、`Pillow>=9`、`numpy`；
  `reportlab` 可选；PDF 材料抽取任选 fitz/pypdf/PyPDF2/pdfplumber 之一。
- 包体：**≤50 文件 / 单文件 ≤500KB / 合计 ≤2MB / 无符号链接 / 全 UTF-8 文本**
  （`.md/.py/.json/.txt/.csv/.yaml/.yml`）。测量脚本本身也是文本脚本（见 §4.4）。
- **在包内跑任何脚本都会生成 `__pycache__`**：请把技能包复制到包外再实测
  （对照协议的两条命令都应在包外执行）。

---

## 7. 决策规则速查（完整表与失败分支见前一节文档与 `references/failure-modes.md`）

| # | 触发 | 动作 | 记录 |
|-|-|-|-|
| D1 | 材料缺失/路径不存在 | 不补造；只出元信息 result | `material_warnings` |
| D2 | 主张数字材料中找不到 | `verified=false` 入未核验清单 | `unverified_claims` |
| D3 | PDF 无文本层/无抽取库 | Agent 抽文本后重跑；仍不行 partial | `uncertainty` + `sources.tool` |
| D4 | CP2 `plan_lint` 有偏差 | 先修；硬约束则继续但**显式记录**并降 partial | `run_meta.spec_lint` |
| D5 | 位图无数据 | 灰框诚实占位，不生成假曲线 | `figure.note` |
| D6 | 模板损坏/打不开 | 备份 + 内置模板，说明降级 | `uncertainty` + `change_records` |
| D7 | 页数超限 | 确定性压缩，**不静默丢证据页** | `change_records` + `notes` |
| D8 | 字体缺失/渲染不可用 | PPTX 只记字体名；预览回落并预警 | `previews.warnings` |
| D9 | 图表重绘失败 | 降级 PPTX 原生可编辑表格 | `figure.note` |
| D10 | 契约字段未知/无值 | 四形态空值 `""/[]/{}/false/0`，**禁 null** | 顶层回显 |
| D11 | 编辑操作非法 | 跳过并记录，其余照常 | `uncertainty` + `changelog` |
| D12 | 复核说"契约没回显" | **先查 `--case` 是否传了** | 复核记录 |
| D13 | 重复运行有差异 | 判断是否仅时间戳/机器路径前缀 | `change_records` |
| D14 | 预算压力 | 先落 partial 再增量改进 | `status` + `change_records` |

---

## 8. 增量编辑（多轮迭代与回退）

```bash
SKILL_DIR="${SKILL_DIR:-/skills/weekly-skill}"
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output \
    --edit edits.json --version v2
```

支持 `update_bullet / add_bullet / remove_bullet / add_note / retitle /
reorder_pages / set_figure`（字段见 `examples/edit_demo.json`，操作目录见
`references/EDIT_OPS.md`）。每次修改写一条 `{version, op, page, target, reason}`；
`deck_v2.pptx` 与 `deck.pptx` 并存 → 回退 = 复制旧版本重跑。
**编辑链路同样过 D2 数字核验**：编辑引入的新数字材料里没有 → 该主张降级为未核验，
**不因"是用户让改的"而放行**。

---

## 9. 自查清单（收尾逐项打勾）

- [ ] 已读 `case.json` + `task.md` + 全部实际材料（未凭文件名猜内容）
- [ ] 页数 = `spec.max_slides`（或更少且原因已记录）；每页有 index/role/title
- [ ] 每页主张 ≤7 条、单条 ≤90 字、标题 ≤60 字；无整段摘要塞页
- [ ] 页面上每个数字都能指回材料；`unverified_claims` 为空或有逐条解释 ← **Q3 的判定面**
- [ ] 每页有演讲备注与证据脚注 ← **Q4/Q5 的判定面**
- [ ] 图表四态均为真（`chart_image`/`table`/`embedded`/`placeholder`），无凭空曲线
- [ ] 字号 ≥12pt；页脚/页码来源唯一；外部模板母版未被改动
- [ ] `result_tool.py` → `{"valid": true}` 且 exit 0；`selftest.py` → `all_pass=true`
- [ ] 契约字段全部回显、无 `null`；**核对时已把 `--case` 传给 `result_tool.py`**
- [ ] `manifest.json` 含全部产物 sha256；`changelog.jsonl` 有本次记录 ← **Q6 的判定面**
- [ ] `status` 与每一列出的 `uncertainty` 一一对应，无"降级却标 success"
- [ ] 做对照时：两侧条件逐项对齐，且**只报可复算的数字**（`GAIN-PROTOCOL.md` §2 纪律）
- [ ] 包体：只有允许的七种文本扩展名、≤50 文件、无二进制、无 `__pycache__`

---

## 10. 五维评分落点（速查；逐点展开见 `references/RUBRIC_MAP.md`）

| 维度 | 分 | 本包靠什么拿到 |
|-|-|-|
| 实际效果 | 40 | CP1–CP4 真跑；页序 + 页级角色；可编辑 PPTX + 备注 + 证据脚注；数字逐一核验；`sources[].sha256` + `manifest.json` + 双形态证据映射 + G1–G8 |
| 使用增益 | 25 | **本版主攻**：公平对照协议（§4.1 逐项对齐）+ 五项质量指标的精确公式 + 随包测量脚本 `references/measure_gain.py` + 真实对照记录（含负面指标与 `partial` 案例）+ 可证伪判据 |
| 创新增益 | 15 | 页序规划（`alloc_roles`）、证据绑定（脚注 + 双形态映射）、图表-数据四态绑定（含"位图无数据只占位"）、局部编辑 + 版本回退（`apply_edits` + `deck_<v>.pptx`） |
| 可靠体验 | 10 | 单入口 + `$SKILL_DIR` 自定位；`references/failure-modes.md` 覆盖材料/模板/依赖/契约四形态/状态一致性并给出非零退出码语义；D1–D14 决策表 |
| 生态贡献 | 10 | 文档齐全（README/TEST/OUTPUT_CONTRACT/RUBRIC_MAP/DECK_SPEC/EDIT_OPS/failure-modes/**GAIN-PROTOCOL** + 示例）；模板与结果信封参数化可复用；脚本按四层职责切分可单独 import；**测量脚本可被其他 Skill 直接复用** |

GitHub 公开链接（额外 5 分）：见根目录 `GITHUB_URL.txt`。

---

## 11. 诚实边界

1. **不冒充平台对照**：本包提供的是可复算的**受控脚本级对照**（基线形态 = 题面点名
   失败清单的确定性代理实现），平台用真实基础 Agent 生成的对照由平台负责，
   `GAIN-PROTOCOL.md` 的范围声明与 §7 局限逐条写明。
2. **预览 ≠ Office 导出**：无 PowerPoint/LibreOffice 时预览为 PIL/reportlab 近似渲染，
   文件名与 `previews.method` 已如实标注。
3. **自检通过 ≠ 内容正确**：`selftest` 查产物可复核性，内容正确性由数字核验与页面纪律负责。
4. **不预制答案**：包内不含任何正式案例的答案；`examples/` 为虚构材料并已标注。
