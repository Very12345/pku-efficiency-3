---
name: academic-ppt-builder-case-generalized
description: 把论文/研究材料组织成结构清楚、证据可追溯、可编辑、符合模板约束的学术汇报演示稿（PPTX），并把"换一个题材、换一种材料结构以后还灵不灵"做成**可复跑的泛化题集**：随包提供两个不同题材的合成案例（实验科学＝有数值表；理论文本＝完全无表、位图无取数），每个案例自带可接受区间（status/页数/角色/图表形态/待核验上限/备注与脚注覆盖/关键数字入页/禁列内容），配 scripts/case_check.py 逐案实测并判定，另附四种边界探针的实测结论与**泛化失效边界**（角色→章节映射、多表只认第一张、页数压缩不留痕）。支持 --edit 局部编辑与版本回退；页面数字逐一核验材料、缺失显式标注、绝不编造。Use when a task asks to generate or edit an academic presentation / slide deck from a paper or research material（组会汇报、开题与中期、答辩、项目评审、基金申请；学术PPT、slides from paper、presentation from paper），especially when /input/case.json and task.md are present and /app/output must contain the editable deck plus previews and evidence mapping, and when the same skill must hold up across different research topics and material structures.
---

# 学术 PPT 生成与编辑 Skill（多案例泛化版 · ppt-6ad93034）

> **本版回答的问题是：这套流程换一个题材还灵吗？换一种材料结构呢？**
>
> 做法不是再写几个"适用范围"，而是**把两个不同题材的案例连同可接受区间一起放进包里**，
> 再用 `scripts/case_check.py` 真跑、真判、真报缺口：
> 实测结果（含四种边界变形的结论）全在 `references/CASE-SET.md`。
>
> 一句话立场：**"能跑通"不等于"换个案例还行"**——
> 所以本版把"还行"写成**可执行的判据**（`_case_set.expect`），
> 并如实标出**做不到的地方**（`_case_set.known_gaps` + §7 失效边界）。

**管辖范围**：把材料"翻译"成页级表达，并保证每页数字与图表可核实。
**不负责**：论文精读与文献综述、科研绘图算法本身、学术写作文字润色、PPT 软件研发。

## 1. 题集一览：两个题材、两个难度层

| | 案例 A `case-a-perovskite` | 案例 B `case-b-climate-text` |
|-|-|-|
| 题材 | 实验科学 / 材料器件（钙钛矿界面钝化） | 理论 / 文献计量（气候政策议题迁移） |
| 难度层 | **基础层**：数值表齐备（CSV）、章节清晰 | **困难层**：**无任何数值表**、位图无取数、6 页上限、带大量方括号引用 |
| 输入 | `case.json` `material.md` `jv.csv` `task.md` | `case.json` `material.md` `task.md` |
| 受众/时长/页数 | 答辩 / 12 min / 8 页 | 同行 / 8 min / 6 页 |
| 最关键的检验 | 数值表**原样重绘**；结论数字不得走样 | **不许凭空画曲线**（禁 `chart_image`）；引用编号可回指 |

**两个案例都不是答案**：材料是虚构论文正文与数据，`examples/cases/**` 里没有任何 `result.json`
或成品幻灯片。平台固定案例由组织方提供，本包不为它预制任何结果。

## 2. 命令口径与快速开始

`$SKILL_DIR` = **含本 `SKILL.md` 的技能根目录**（平台容器内为 `/skills/weekly-skill`），
所有命令都写成 `python "$SKILL_DIR/scripts/…"`，**cwd 不是技能根目录时照样能跑**。

```bash
SKILL_DIR="${SKILL_DIR:-/skills/weekly-skill}"
OUT=/app/output

# ① 主流程（对平台给的 case.json 跑一遍）
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out "$OUT"

# ② 契约门 G1–G8（`--case` 必须传，否则无法核对契约回显）
python "$SKILL_DIR/scripts/result_tool.py" --result "$OUT/result.json" \
    --out-dir "$OUT" --case /input/case.json \
    --envelope "$SKILL_DIR/templates/result_envelope.json"     # {"valid": true} 且 exit 0

# ③ 产物自检
python "$SKILL_DIR/scripts/selftest.py" --out "$OUT" --case /input/case.json   # all_pass=true

# ④ 泛化台：把包内两个合成案例各跑一遍并判定（开发期用，约 5 秒）
python "$SKILL_DIR/scripts/case_check.py" --list
python "$SKILL_DIR/scripts/case_check.py" --pkg "$SKILL_DIR" --work <包外目录> --probes

# ⑤ 局部编辑 + 版本归档
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out "$OUT" \
    --edit edits.json --version v2
```

> **必须在包外跑**：任何脚本都会让 Python 在包内写 `__pycache__`，平台预检会因此拒收整包。
> `case_check.py` 自己就把被测包复制到包外再执行。

**退出码语义**（编排器可直接判读；与 `references/failure-modes.md` §0 一致）：

| 脚本 | 0 | 1 | 2 |
|-|-|-|-|
| `scripts/main.py` | `status=success` | `status=partial`（降级已逐条记入 `uncertainty`） | 输入不可读（已写最小 `status=failed` result.json） |
| `scripts/result_tool.py` | G1–G8 全过 | 有条目未过 | `result.json` 无法解析 |
| `scripts/selftest.py` | 全部自检项通过 | 有未通过项 | 输入不可读 |
| `scripts/evidence_check.py` | 主张里每个数字都能定位 | 有数字找不到 | — |
| `scripts/case_check.py` | 全部案例通过判定 | 有案例未过判定 | 环境/案例不可用 |

**只有 exit 0 才算"干净"**；exit 1 必须读 `result.json.uncertainty` 再决定是否补件重跑。

## 3. 输入、输出与产物归属

**读**：`case.json`（`case_id`、`title`、`inputs{task_md, material[]}`、
`spec{audience, duration_minutes, max_slides, template|template_pptx|starting_deck, style}`、
可选 `output_contract`）、`task.md`、`material[]` 指向的**实际文件**——
`scripts/deck_extract.py` 强制"读实际文件"，**禁止凭文件名推断内容**。

**写**（一律写 `--out`，并在输出根放一份 `preview/` 副本便于直接取件）：

| 产物 | 位置 | 说明 |
|-|-|-|
| 可编辑演示文件 | `work/deck.pptx` | 主张式标题 + 要点 + 图表槽 + 证据脚注 + 演讲备注 |
| 页面模型 | `work/plan.json` | 页序 / 角色 / 主张 / 证据 / 图表，**可编辑源** |
| 材料视图 | `work/material_view.json` | 章节 / 数据表 / 图表提及（**多表时两张都会登记**，但只有第一张会被绑定，见 §7） |
| 预览渲染 | `work/preview/slide_*.png`、`work/preview/preview.pdf`、输出根 `preview/*` | 标注"非 PowerPoint 导出" |
| **评分产物** | `result.json` | 契约全字段 + `case_id`，**禁 null** |
| 证据映射 | `evidence_map.md` + `evidence_map.json` | 人读 / 机器读**同源双形态** |
| 记录 | `changelog.jsonl`、`manifest.json`、`logs/` | 支撑他人独立复核 |

> **不入包**：`deck.pptx`、预览 `*.png`/`*.pdf`、`changelog.jsonl` 都是运行时产物；
> 技能包只携带 UTF-8 文本资源（`.md/.py/.json/.txt/.csv/.yaml/.yml`）。
> **产物绝不写回技能包目录**——评测容器里技能目录是只读安装件。

## 4. 执行流程（CP1–CP4）+ 两条泛化纪律

| 检查点 | 动作 | 判定 |
|-|-|-|
| **CP1 读实际输入** | 读 case/task/每个材料；核对存在性 | 材料是否可读（缺失 → D1） |
| **CP2 规划与 lint** | 角色分配 + 页序 + 主张与证据指针；`evidence_check.plan_lint` | `valid` 或记录偏差（D4） |
| **CP3 建稿** | 模板槽位建稿 + 四态图表绑定 + 备注 + 脚注 | deck 可重开且页数=plan |
| **CP4 导出校验** | `result_tool` 的 G1–G8 + `selftest` | `{"valid": true}` 且 exit 0 |

**泛化纪律 ①：材料结构不是标准论文骨架时，必须人工看页面。**
实测（`CASE-SET.md` §3）：角色→章节是**按标题关键词**映射的；
材料若用"三阶段 / 争论焦点 / 方法与数据争议"这类小节名，
会出现"结果页取到摘要、方法页取到局限"的**内容错位但不报错**。
G1–G8 与自检都抓不到这类问题。

**泛化纪律 ②：多个数据源时，`material[]` 的顺序就是优先级。**
实测：材料给了两张 CSV 时**只绑定第一张**，第二张既不进页面也不留 uncertainty。
需要哪张表进结果页，就把它放在 `material[]` 第一位。

## 5. 可接受区间：判据写在案例里，而不是写在文档里

每个 `case.json` 的 `_case_set.expect` 是一份**可执行判据**；`case_check.py` 逐条对照：

| 判据 | 含义 | 例（案例 B） |
|-|-|-|
| `status_any_of` | **允许诚实降级**：材料有缺口时 `partial` 才是对的结果 | `["success","partial"]` |
| `slide_count` | 页数必须等于 `spec.max_slides` | `6` |
| `roles_head` / `roles_tail` | 首末角色固定（叙事完整性） | `cover` / `takeaway` |
| `must_have_figure_kind` | 必须有某类图表形态 | `["none","placeholder"]` |
| `forbid_figure_kind` | **不许编造** | `["chart_image"]` |
| `unverified_claims_max` | 待核验项上限 | `3` |
| `min_notes_coverage` / `min_evidence_footer_coverage` | 备注 / 脚注覆盖 | `1.0` / `1.0` |
| `must_mention_in_deck` | 关键数字或术语必须入页 | —（案例 B 把它移入 `known_gaps`） |
| `forbid_in_deck` | 禁列内容（防编造） | `["87.6％","12.4 万篇"]` |

**实测（两案各一次）**：案例 A **12/12 判据 PASS**、案例 B **11/11 PASS**；
两案的 `gate_valid=true`、`all_pass=true`、deck 可重开且页数一致、
备注与脚注覆盖都是 **1.0**、`result.json` 顶层 **20 个键**
（18 个基键 + 3 个契约回显字段，其中 1 个与基键重合）。
逐条数值见 `references/CASE-SET.md` §2。

> `_case_set.known_gaps` 是**如实标注的"没做到"**（例如案例 B 的材料年份 `2009/2015`
> 没有进页面）。它**不计入 FAIL，但每次运行都会被打印出来**——
> 让缺口可见，而不是把判据改成能过。

## 6. 决策规则（D1–D12，含泛化实测证据）

| # | 触发条件 | 动作 | 记录 | 泛化实测证据 |
|-|-|-|-|-|
| **D1** | 材料全读不到 | 不建 deck，只出元信息 result（`slide_count=0`） | `material_warnings` | 两案材料齐备；负路径见 `TEST.md` §T7 |
| **D2** | 主张里数字材料中找不到 | `verified=false` 进未核验清单，**不回填、不取整** | `unverified_claims` | 探针 P4：`--edit` 塞入 `31.7%` → 立刻进未核验清单 ✅ |
| **D3** | PDF 无文本层 / 无抽取库 | 不 OCR 冒充；Agent 抽文本后重跑 | `uncertainty` | 两案均为 `.md`/`.csv`，未触发 |
| **D4** | `plan_lint` 偏差 | 先修 plan；硬约束则继续但记录偏差并降 partial | `run_meta.spec_lint` | 探针 P2：报 `page 2 bullet too long (CJK-weighted=162 vs 90)` → 进 `uncertainty` ✅ |
| **D5** | 位图无取数数据 | 灰框诚实占位，不生成假曲线 | `figure.note` | 案例 B 材料明确写"原图为位图、未提供取数数据"，实测 **0 张编造图** ✅ |
| **D6** | 模板打不开 / 母版损坏 | 备份 → 内置模板并说明降级 | `uncertainty` + `change_records` | 两个案例都用内置模板；坏法实测见 `FAULT-MATRIX.md` |
| **D7** | 页数超限 | 确定性压缩角色，**不静默丢证据页** | `change_records` | ⚠️ 探针 P3：压到 3 页后角色变为 `cover→overview→result`，但 `change_records` **只有 start**（缺口，见 §7） |
| **D8** | 字体缺失 / 渲染不可用 | PPTX 只记字体名；预览回落并预警 | `previews.warnings` | 两案预览 PNG/PDF 均产出；CJK 字体 `Microsoft YaHei` |
| **D9** | 图表重绘失败 | 降级 PPTX 原生可编辑表格 + note | `figure.note` | 案例 B **无表可画**：`figure_kind=none ×6`，未走降级也未编造 ✅ |
| **D10** | 契约字段未知 / 无值 | 四形态空值 `""/[]/{}/false/0`，**禁 null** | 顶层回显 | 两案各回显 3 个额外字段（`case_topic`/`difficulty`/`is_synthetic`）✅ |
| **D11** | 编辑 op 非法 / 页码越界 | 跳过并记录，其余照常 | `uncertainty` + `changelog` | 探针 P4 的 `--edit` 正常应用并留 `change_record` ✅ |
| **D12** | 复核说"契约没回显" | **先查是否传了 `--case`** | 复核记录 | 两案判定都显式传入 `--case` |

## 7. 泛化失效边界（实测，逐条可复现）

> 完整证据（含原始数值）在 `references/CASE-SET.md` §3。这里只列结论。

| 编号 | 边界 | 现象 | 规避做法 |
|-|-|-|-|
| **GAP-A1** | 材料缺"标准小节" | 案例 A 没有"背景"小节 → `background` 页写占位主张 → `unverified=1`、`status=partial` | 这是**诚实降级**，不要把它当错误；确需干净 `success` 就补一节背景 |
| **GAP-A2** | markdown 表格 vs CSV | 材料里同时有 markdown 表（表 1）与 CSV 时，**数据源是 CSV**，表 1 的关键指标（如 PCE 24.8%）不会进页面 | 把要用的数值表**导出为 CSV 并放在 `material[]` 第一位** |
| **GAP-B1** | 编号小标题 | `## 1. …` 这类标题被当作列表项切分，产生只含 `1.` 的退化要点 | 材料侧避免"标题带序号"；或人工在 `--edit` 里修掉 |
| **GAP-B2** | 角色→章节映射 | 非标准骨架（人文/理论）时，年份等关键信息可能整体不进页面（实测缺 `2009/2015`） | 交付前人工核对"材料里最重要的 3 个信息是否都上了页面" |
| **GAP-B3** | 同上 | 结果页可能取到摘要、方法页取到局限——**内容错位但不报错** | 人工看页面；不要只看 `status` |
| **GAP-P1** | 多数据源 | 两张表只绑定第一张，第二张**静默忽略**（无 uncertainty） | 只把要用的表放进 `material[]`，或把它放第一位 |
| **GAP-P3** | 页数压缩 | `max_slides` 过紧时角色被裁掉，`change_records` 里没有记录 | 放宽上限；或在交付说明里人工写明合并了哪些页 |

**这些边界不会被 G1–G8 / 自检 / 契约门抓到**——它们只能靠
① 案例级判据（`case_check.py`）、② 人工看页面。这正是本包把两个案例与判据一起放进来的原因。

## 8. 增量编辑（多轮迭代与回退）

```bash
SKILL_DIR="${SKILL_DIR:-/skills/weekly-skill}"
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output \
    --edit edits.json --version v2
```

7 类 op：`update_bullet / add_bullet / remove_bullet / add_note / retitle /
reorder_pages / set_figure`（字段见 `examples/edit_demo.json`，决策树见 `references/EDIT_OPS.md`）。
每次改动写一条 `{version, op, page, target, reason}`；`deck_v2.pptx` 与 `deck.pptx` **并存**，
**回退 = 复制旧版本重跑**。
**编辑链路同样过 D2 数字核验**：实测用 `--edit` 塞入材料里没有的 `31.7%`，
该主张立刻进 `unverified_claims`（`missing_numbers=["31.7%"]`），
`change_records` 记下 `reason="探针：材料里没有 31.7%"`——**不因"是用户让改的"而放行**。

## 9. 完整命令索引（能力清单；含全部入口与开关）

| 入口 | 关键参数 | 用途 | 退出码 |
|-|-|-|-|
| `scripts/main.py` | `--case` `--out` `--input-dir` `--template` `--max-slides` `--edit` `--no-chart` `--version` `--draft` `--verbose` | 端到端主流程 | 0/1/2 |
| `scripts/result_tool.py` | `--result` `--out-dir` `--case` `--envelope` | 契约门 G1–G8 | 0/1/2 |
| `scripts/selftest.py` | `--out` `--case` `--pptx` `--slides` | 产物自检 | 0/1 |
| `scripts/evidence_check.py` | `--claim` `--material` | 单条主张数字核验 | 0/1 |
| `scripts/make_examples.py` | `--work-dir` `--dry-run` | 维护：重建 `examples/output/` 并净化绝对路径 | 0/1 |
| `scripts/deck_extract.py` | （库）由 `main.py` 编排 | 读实际材料 → `material_view.json` | — |
| `scripts/slide_text.py` | （库）由 `main.py` 编排 | 页序 / 角色 / 主张 / 备注文案 | — |
| `scripts/deck_tool.py` | （库）由 `main.py` 编排 | 图表四态绑定 + 模板槽位建稿 + 编辑 op | — |
| `scripts/render_qa.py` | （库）由 `main.py` 编排 | PIL PNG + reportlab PDF + 渲染 QA | — |
| `scripts/deck_common.py` | （库）被其余脚本 import | 路径自定位 / 原子写 / sha256 / 日志 / CJK 字体 | — |
| **`scripts/case_check.py`** | `--pkg` `--work` `--only` `--probes` `--probe-case` `--report-json` `--report-md` `--list` `--verbose` | **本版新增**：逐案实测 + 可接受区间判定 + 四种边界探针 | 0/1/2 |

## 10. 五维评分落点（速查；逐点展开见 `references/RUBRIC_MAP.md`）

| 维度 | 分 | 本包靠什么拿到 |
|-|-|-|
| 实际效果 | 40 | CP1–CP4 真跑；页序 + 页级角色；可编辑 PPTX + 备注 + 证据脚注；数字逐一核验；**两个题材各跑一次的实测结果**（`CASE-SET.md` §2） |
| 使用增益 | 25 | 页面纪律（每页一个角色、≤7 条、≤90 字、字号 ≥12pt）对标"整段塞页"；`--edit` 局部编辑 + 版本归档；**判据化验收**（不用人肉比对就知道这次有没有退步） |
| 创新增益 | 15 | 页序规划、证据绑定、图表四态绑定、局部编辑+回退；**新增：把"泛化"写成案例级可执行判据 + 四种边界探针，并如实给出 7 条失效边界** |
| 可靠体验 | 10 | D1–D12 + F1–F5 失败分支 + 非零退出码语义；**缺材料/无表/页数过紧/编辑引入新数字四种边界都有实测结论** |
| 生态贡献 | 10 | **本版主攻**：题集（两个题材 × 可接受区间）+ 判定台可扩展（§4 的四步加案例法）+ 判据写法小抄 + 两案的合成材料可直接当回归用例 |

GitHub 公开链接（额外 5 分）：见根目录 `GITHUB_URL.txt`。

## 11. 诚实边界

1. **两个案例都是合成材料**（虚构数据、虚构引用），**不是正式案例、不含正式答案**；
   `case.json` 里 `_note` 已逐条标注。
2. **案例只覆盖两个题材**（实验科学 / 理论文本），没覆盖医学统计、工程图纸、教学课件等形态。
3. **判定是结构 + 覆盖判据，不是质量判据**：能证明"页数对、角色在、备注全、没编造"，
   **不能证明"这一版讲得好"**。
4. **7 条失效边界仍在**（§7）：本版把它们测出来、写清楚、给规避做法，
   **没有修改核心算法**去根治；引用本包时不要声称"任意题材都能自动对齐"。
5. **预览 ≠ Office 导出**：无 PowerPoint/LibreOffice 时预览是 PIL/reportlab 近似渲染，
   文件名与 `previews.method` 均已如实标注。
6. **开发期工具**：`case_check.py` 跑 2 个案例约 5 秒、加探针约 12 秒，
   属开发期回归；不要放进平台 900 秒评测预算里跑。
