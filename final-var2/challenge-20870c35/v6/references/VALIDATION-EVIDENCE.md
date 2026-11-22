# VALIDATION-EVIDENCE.md — 失败注入矩阵 + 多案例题集（v6 合并版）

> 由 `references/FAULT-MATRIX.md`（v4）与 `references/CASE-SET.md`（v5）合并，内容逐字保留。
> 两段分别回答两个问题：**坏输入会不会静默通过**（第 I 部）与**换题材还成不成立**（第 II 部）。


---

# 【合并段】失败注入矩阵（原文，含 15 行实测）

> 本段原为独立文件 `references/FAULT-MATRIX.md`，在 v6（union 包）中并入本文件以守住「≤50 文件」硬门；**内容逐字保留**，未删减。

# FAULT-MATRIX.md — 失败注入 × 期望 × **实测**（15 行，含对照组）

> 本表由 `scripts/fault_inject.py` 在**包外一次性沙箱**里逐条真跑 `scripts/main.py` 采集：
> 表内每一个退出码 / `status` / `uncertainty` 条目 / `change_records` 步数都是**该次运行的真实输出**，
> 没有一行是手写推断。生成器会把同样的表（含逐条 evidence）写到沙箱里
> （`<sandbox>/FAULT-MATRIX.generated.md` 与 `<sandbox>/fault_matrix.json`），可自行复算比对。
>
> 采样环境：Python 3.13.9 · python-pptx 1.0.2 · Pillow 12.3.0 · pypdf 6.14.2 · win32 · UTC 2026-11-22T11:55:32Z
> · 模式 `full`（**未**加 `--skip-previews`）。

## 0. 复现命令

```bash
SKILL_DIR="<本包根目录>"                 # 含 SKILL.md 的那个目录
python "$SKILL_DIR/scripts/fault_inject.py" --list
python "$SKILL_DIR/scripts/fault_inject.py" --sandbox "/tmp/ato-fault"          # 15 行全跑
python "$SKILL_DIR/scripts/fault_inject.py" --sandbox "/tmp/ato-fault" --inject F07,F12
python "$SKILL_DIR/scripts/fault_inject.py" --sandbox "/tmp/ato-fault" --skip-previews   # 更快，语义不变
```

退出码：`0` = 全部 MATCH 且无静默失败；`1` = 有 MISMATCH 或静默失败；`2` = 参数用法错误 /
**检测到 `--sandbox` 落在技能包内部**（在包内跑会生成 `__pycache__` 使提交包不合规，脚本主动拒绝）。

> **先归一化基线，再注入**：每条注入开跑前，脚本先用本包自带的
> `scripts/make_synthetic_inputs.py` 把示例案例的二进制输入（`dataset_card.pdf` / `fig2.png`）
> 现场补齐，使**未注入时的基线为 `completed`**（`F00` 对照组）。
> 不做这一步，示例案例本身就缺 `dataset_card.pdf`，每条注入都会退化成 `partial`，
> 矩阵就分不清「故障造成的降级」与「示例案例本身不完整造成的降级」。
> 用 `--no-prime` 可关掉（此时基线回到 `partial`，归因能力下降）。

## 1. 汇总：注入什么 → 期望行为 → 实测 → 是否静默失败

| # | 族 | 注入什么 | 期望行为（设计上应走的路径） | 实测 `exit` | 实测 `status` | 实测 `uncertainty` 条数 | 实测 `change_records` 步数 | `result.json` | **静默失败** | 判定 |
|-|-|-|-|-|-|-|-|-|-|-|-|
| `F00` | 对照 | **不做任何注入**（二进制输入已补齐） | `exit=0` / `completed` | `0` | `completed` | 3 | 9 | 有（20 键） | 否 | MATCH |
| `F01` | 输入 | `case.json` 被截断成非法 JSON | `exit=1` / `failed`，写最小失败信封 | `1` | `failed` | 0 | 2 | 有（8 键） | 否 | MATCH |
| `F02` | 输入 | `case.json` 可读但缺 `case_id` | `exit=0` / `partial`，P1 门报 `missing:case_id` | `0` | `partial` | 4 | 10 | 有（20 键） | 否 | MATCH |
| `F03` | 输入 | 声明的材料 `experiment_log.md` 不在盘上 | `exit=0` / `partial`，`kind=missing` | `0` | `partial` | 5 | 9 | 有（20 键） | 否 | MATCH |
| `F04` | 输入 | 材料清单与材料目录都清空（0 材料） | `exit=0` / `partial`，只出结构性页面 | `0` | `partial` | 5 | 9 | 有（20 键） | 否 | MATCH |
| `F05` | 输入 | 加入 1 页**无文本层** PDF（扫描件） | `exit=0` / `partial`，如实记「未能解析」 | `0` | `partial` | 4 | 9 | 有（20 键） | 否 | MATCH |
| `F06` | 模板 | `template` 指向的文件不存在 | `exit=0` / `completed` + 记明未沿用模板 | `0` | `completed` | 3 | 9 | 有（20 键） | 否 | MATCH |
| `F07` | 模板 | 模板文件在盘上但**容器损坏**（非 OOXML） | `exit=0` / `completed`，回落内置主题并记明 | `0` | `completed` | 3 | 9 | 有（20 键） | 否 | MATCH |
| `F08` | 模板 | 合法 16:9 模板**自带 3 张示例页** | `exit=0` / `completed`，母版沿用、自带页丢弃 | `0` | `completed` | 2 | 9 | 有（20 键） | 否 | MATCH |
| `F09` | 依赖 | `import pptx` 被遮罩（python-pptx 缺失） | `exit=0` / `partial`，跳过 deck、其余照常 | `0` | `partial` | 4 | 8 | 有（20 键） | 否 | MATCH |
| `F10` | 依赖 | `import PIL` 被遮罩（Pillow 缺失） | `exit=0` / `partial`，预览跳过（非致命） | `0` | `partial` | 5 | 9 | 有（20 键） | 否 | MATCH |
| `F11` | 依赖 | `pypdf`/`PyPDF2` 被遮罩 | `exit=0` / `partial`，PDF 记未解析 | `0` | `partial` | 4 | 9 | 有（20 键） | 否 | MATCH |
| `F12` | 契约 | `task.md` 的 `output_contract` 块被截断（非法 JSON） | `exit=0` / `partial`，契约解析失败要落痕 | `0` | `partial` | 4 | 10 | 有（20 键） | 否 | MATCH |
| `F13` | 契约 | `task.md` 声明空契约 `{}`（零字段） | `exit=0` / `partial`，契约解析失败要落痕 | `0` | `partial` | 4 | 10 | 有（20 键） | 否 | MATCH |
| `F14` | 契约 | 契约多声明 1 个本包产不出的字段 | `exit=0` / `completed`，四形态回显**禁 null** | `0` | `completed` | 3 | 9 | 有（**21** 键） | 否 | MATCH |

**15 行全 MATCH，0 行静默失败。** 其中 4 行的**期望值在实测后被修订**（`F06`/`F07`/`F08`/`F14`），
修订理由逐条写在 §2 对应条目里 —— 修订分两类：
① **改的是代码**（`F07`/`F14`：第一轮实测暴露真实缺陷，已按纯增量修，见 §3）；
② **改的是我自己原先的期望**（`F06`/`F08`：原判 `partial` 与契约 §3 的 `completed` 定义冲突，
实测证明原期望本身标错）。

## 2. 逐条实测证据（注入 → 实测字段原文）

每条给出：注入动作 · 实测命令形状 · 实测 `exit`/`status` · 实测 `uncertainty` 条目原文 ·
实测 `change_records` 步名 · 产物落盘 · 耗时。

### `F00` 对照组 · 无注入
- **注入**：无（仅确保 `output_contract` 声明齐备）。prime 生成：`dataset_card.pdf`、`fig2.png`。
- **实测**：`exit=0` · `status=completed` · 顶层 **20** 键 · `uncertainty` **3** 条 · `change_records` 9 步
  （`start, environment, input, material, figure-binding, plan, deck-source, deck, audit`）。
- **实测 `uncertainty` 原文**：`证据定位为行级/章节级近似锚点（L<行号> · §<章节>）` /
  `PNG 预览为 Pillow 模拟渲染，非 Office 真实栅格化` / `案例未提供模板或起始演示文件`。
- **产物**：`editable_deck.pptx` **存在** · `previews/` **13 个文件** · `talk_plan.json` 12 页 ·
  `plan_gates.json` `valid=true` · `self_check.json` 存在 · 耗时 1.60 s。
- **stdout 末行（原文）**：`status=completed pages=12 deck=True validate_valid=True contract_valid=True`
- **结论**：基线是一条完整成功路径 ⇒ 下面 15 条的 `partial` 都可以被**归因到注入的那一个故障**上。

### `F01` 输入 · `case.json` 非法 JSON
- **注入**：把 `case.json` 截断成 `{"case_id": "brok`（少右引号与右花括号）。
- **实测**：`exit=1` · `status=failed` · 顶层 **8** 键（缺 `report_goal/audience/duration_min/slide_count/summary/main_line/pages/evidence_map/contract`）
  · `uncertainty` **0** 条 · `change_records` **2** 步（`start, environment`）。
- **实测 `result.error` 原文**：`case.json unreadable: Invalid control character at: line 2 column 19 (char 20)`
- **产物**：`editable_deck.pptx` 无 · `previews/` 无 · `self_check.json` **有** · 耗时 0.55 s。
- **是否静默**：**否** —— 退出码非 0、stdout 有 `FATAL:` 一行、`result.json` 里 `error` 字段带原始异常文本。
- **边界（如实写明）**：这条路径**不组装 `uncertainty`**（`uncertainty` 由 CP5 组装，而 CP1 就已 return）。
  「失败原因」这一语义由 `result.error` + `change_records` 承担，**不是**由 `uncertainty` 承担 ——
  读 `uncertainty` 拿不到原因的人会误判，故在此点名。

### `F02` 输入 · 缺 `case_id`
- **注入**：删除 `case.json` 的 `case_id` 键。实测回落后 `result.case_id = "case"`（取文件名）。
- **实测**：`exit=0` · `status=partial` · 20 键 · `uncertainty` **4** 条 · `change_records` **10** 步
  （比基线多 `plan-gate`）。
- **实测 `uncertainty` 多出的一条原文**：`计划门 P1–P8 未全过（见 plan_gates.json / result.audit.plan_gates）`
- **实测 `plan_gates.json`**：`valid=false`，`errors=["P1 missing:case_id"]`，`summary="gates=8 ok=7"`；
  P2–P8 全部 `ok=true`。
- **产物**：deck 有（67424 B） · previews 13 · `selfcheck` 有 · 耗时 1.25 s。
- **结论**：缺 `case_id` **不只是**换个名字 —— 它会顺着 P1 门把整轮降级为 `partial` 并留下 uncertainty。
  这条链条是真实的、可复核的，不是设计文档里的设想。

### `F03` 输入 · 声明的材料不存在
- **注入**：`materials` 里加入 `materials/experiment_log.md`（磁盘上没有该文件）。
- **实测**：`exit=0` · `status=partial` · 20 键 · `uncertainty` **5** 条 · `change_records` 9 步。
- **实测 `uncertainty` 多出的两条原文**：
  `以下材料未能解析为文本：['experiment_log.md']` /
  `case.json 声明但磁盘上不存在的材料：['materials/experiment_log.md']`
- **产物**：deck 有 · previews 13 · `plan_gates` `valid=true` · 耗时 1.22 s。
- **结论**：同一份缺失材料被**两条**独立记录覆盖（一条讲「未解析」、一条讲「声明了但不在盘上」），
  复核者不会把「文件不在」误读成「文件在但读不出」。

### `F04` 输入 · 零材料
- **注入**：`materials` 置空数组，并删除材料目录内容。
- **实测**：`exit=0` · `status=partial` · 20 键 · `uncertainty` **5** 条 · `change_records` 9 步
  （含 `framing` 步）。
- **实测 `uncertainty` 多出的两条原文**：
  `若干页面由源材料章节间接概括而成（无逐句主张）` /
  `没有任何材料被解析为文本（材料为空，或全部不可解析/不存在）`
- **产物**：仍写出 12 页 deck（66613 B）· previews 13 · 耗时 1.26 s。
- **结论**：零材料**不中断运行**，但把「没有事实依据」写进 `uncertainty` 而不是伪装成有证据的页面。

### `F05` 输入 · 无文本层 PDF（扫描件）
- **注入**：用 `pypdf.PdfWriter` 造 1 页空白 PDF（595×842，可打开、不可抽文本），登记进 `materials`。
- **实测**：`exit=0` · `status=partial` · 20 键 · `uncertainty` **4** 条 · `change_records` 9 步。
- **实测 `uncertainty` 多出的一条原文**：`以下材料未能解析为文本：['scanned_supplement.pdf']`
- **产物**：deck 有 · previews 13 · `plan_gates` `valid=true` · 耗时 1.26 s。
- **该行暴露并已修的真实缺陷**：第一轮实测（修前）中这份扫描件被记为 **`parsed=true`**、
  `char_count=15`，`status` 因此是 `completed` —— 即「无文本层」被静默当成一次成功解析。
  已按纯增量修 `scripts/evidence.py`（见 §3 Fix 2）；修后实测为 `parsed=false` + 上面那条 uncertainty。

### `F06` 模板 · 模板路径不存在
- **注入**：`case.json` 加 `"template": "templates/frozen_master.pptx"`（磁盘上没有该文件）。
- **实测**：`exit=0` · `status=completed` · 20 键 · `uncertainty` **3** 条 · `change_records` 9 步。
- **实测 `uncertainty` 里对应的一条原文**：`案例未提供模板或起始演示文件`
- **实测 `artifacts.deck_mode`**：`mode=built-in-theme`，`template_path=None`。
- **期望修订（诚实记录）**：原声明 `partial`，实测 `completed`。契约 §3 的 `completed` 定义是
  「材料全部解析 + 计划门全过 + deck 写入且 verify 通过 + 预览渲染 + 证据审计与自检通过」，
  **「必须用上模板」不在其中**，本次也没有因此丢内容。这不是掩盖：`uncertainty` 里确实有
  「案例未提供模板」一条，`deck_mode` 也如实写 `built-in-theme`。故按契约语义把期望改为 `completed`。

### `F07` 模板 · 模板存在但容器损坏
- **注入**：写一个扩展名 `.pptx`、内容为 `PK\x03\x04 this is not a zip container at all…` 的文件，
  并把 `case.json.template` 指向它。
- **实测**：`exit=0` · `status=completed` · 20 键 · `uncertainty` **3** 条 · `change_records` 9 步。
- **实测 `uncertainty` 里对应的一条原文（截断）**：
  `案例指定的模板存在但无法打开（PackageNotFoundError: Package not found at 'materials/f…`
- **实测 `artifacts.deck_mode`**：`mode=built-in-theme`，`template_load_error` 记录异常类型与原文。
- **第一轮实测（修前）**：`exit=1` · `status=failed` · deck 未生成 · stdout：
  `[deck] FAILED: Package not found at '…/materials/frozen_master.pptx'`，且 traceback 打到 stderr。
  ⇒ **一次坏模板打死整轮运行**，与 `failure-modes.md` 的 D5（模板打不开 → 用内置主题）直接矛盾。
- **期望修订（诚实记录）**：原声明 `exit=1/partial`（按修前实测写的），**已改为** `exit=0/completed`。
  改的是**代码**（§3 Fix 1 + Fix 6），不是把期望挪到能过为止：修后同样条件下 deck 正常生成、
  退出码 0、降级原因同时出现在 `change_records` 与 `uncertainty` 两处。

### `F08` 模板 · 合法模板自带 3 张示例页
- **注入**：用 python-pptx 生成 16:9 模板（`slide_width=13.333in`），预置 **3** 张带
  `TEMPLATE SAMPLE PAGE n - must be dropped` 文本的空白版式页，`case.json.template` 指向它。
- **实测**：`exit=0` · `status=completed` · 20 键 · `uncertainty` **2** 条 · `change_records` 9 步。
- **实测 `artifacts.deck_mode`**：`mode=template-adapt`，`template_slides_present=3`，
  `template_slides_dropped=3`，`template_load_error=None`。
- **实测 `talk_plan.json`**：`pages=12`，`slide_target=12` ⇒ **最终页数 == 冻结页数**（自带 3 页未溢出）。
- **期望修订（诚实记录）**：原声明 `partial`，实测 `completed`。D16 的「丢弃自带页」是**正常功能**，
  不是降级：母版/版式被沿用、页数守约、无内容损失。把它标成 `partial` 反而是**错标**。

### `F09` 依赖 · python-pptx 缺失
- **注入**：沙箱内放 `_deps/pptx.py`（抛 `ImportError`），以 `PYTHONPATH` 前置；脚本目录优先于
  `PYTHONPATH`、`PYTHONPATH` 优先于 `site-packages`，因此**无需卸载真包**即可让主流程观察到缺依赖。
- **实测**：`exit=0` · `status=partial` · 20 键 · `uncertainty` **4** 条 · `change_records` **8** 步（基线 9 步，少 `deck-source`）。
- **实测 `uncertainty` 里对应的一条原文（截断）**：
  `运行环境缺少 python-pptx（python-pptx 不可用（fault_inject: simulated missing dep…`
- **产物**：`editable_deck.pptx` **无** · previews **13**（照常） · `plan_gates valid=true` · 耗时 1.07 s。
- **stdout 原文**：`[deck] SKIPPED (dependency missing): python-pptx 不可用（fault_inject: simulated missing dependency 'pptx'）`
- **结论**：`exit=0` 且 `status=partial` —— 缺 deck 依赖**不会**被报成崩溃，而页计划/计划门/预览/`result.json` 全部照常落盘。

### `F10` 依赖 · Pillow 缺失
- **注入**：`_deps/PIL.py` 遮罩。
- **实测**：`exit=0` · `status=partial` · 20 键 · `uncertainty` **5** 条 · `change_records` 9 步（含 `preview` 步）。
- **实测 `uncertainty` 里新增的两条原文（截断）**：
  `PNG 预览渲染失败或未执行` /
  `运行环境缺少 python-pptx（python-pptx 不可用（fault_inject: simulated missing dep…`
- **实测 `previews/`**：目录存在、**0 个文件**（render 抛错被 `main.py` 的 `except` 接住，非致命）。
- **实测到的**连带效应**（如实记录，非设计预设）**：遮罩 `PIL` 会**同时**让 python-pptx 不可用
  ——因为 python-pptx 自身依赖 PIL —— 所以本行的 deck 也被跳过。
  ⇒ 在真实缺 Pillow 的环境里，本包会同时丢 deck 与预览；两者各自在 `uncertainty` 有独立条目，
  退出码仍为 0。stdout 有 `[preview] FAILED (non-fatal): …` 一行。

### `F11` 依赖 · pypdf 缺失
- **注入**：`_deps/pypdf.py` + `_deps/PyPDF2.py` 遮罩（同时堵住新旧两个包名）。
- **实测**：`exit=0` · `status=partial` · 20 键 · `uncertainty` **4** 条 · `change_records` 9 步。
- **实测 `uncertainty` 里对应的一条原文**：`以下材料未能解析为文本：['dataset_card.pdf']`
- **产物**：deck **有**（67641 B） · previews 13 · 耗时 1.46 s。
- **结论**：`pypdf` 是**可选**解析器：缺它只影响 PDF 材料的证据抽取，md 材料与 deck 链路照常。

### `F12` 契约 · `task.md` 契约块被截断
- **注入**：把 `task.md` 末尾 ```json 契约块替换成 `{"output_contract": ["case_id", "status", "title"`（缺 `]}`）。
- **实测**：`exit=0` · `status=partial` · 20 键 · `uncertainty` **4** 条 · `change_records` **10** 步
  （比基线多 `contract` 步）。
- **实测 `uncertainty` 多出的一条原文（截断）**：
  `task.md 里存在 output_contract 声明，但无法解析出可用字段清单（output_contract NOT applie…`
- **实测 `contract.declared_source`**：`case.json`（本行 `case.json` 仍声明了契约，故字段仍齐全）。
- **该行暴露并已修的真实缺陷**：第一轮实测（修前）里契约块被静默忽略 —— `change_records` **没有** `contract` 步、
  `uncertainty` **没有**对应条目、`status` 仍是 `completed`。已按纯增量修
  `scripts/common.py` + `scripts/main.py`（见 §3 Fix 3 + Fix 5）。

### `F13` 契约 · 声明空契约 `{}`
- **注入**：`task.md` 契约块替换为 `{}`；同时删除 `case.json` 的 `output_contract`，
  使全部契约来源都落空 ⇒ 必须回落内置默认契约。
- **实测**：`exit=0` · `status=partial` · 20 键 · `uncertainty` **4** 条 · `change_records` **10** 步（含 `contract`）。
- **实测 `contract.declared_source`**：`built-in default`；`contract.applied` **14** 个字段。
- **实测结果（关键）**：即便契约声明为空，`result.json` 顶层仍有 **20** 个键，
  题面要求的 `case_id`/`status`/`pages`/`sources`/`uncertainty`/`change_records` 一个不缺
  ⇒ **契约只增不减**在「声明为空」这条极端分支上也成立。
- **该行暴露并已修的真实缺陷**：同 `F12`（修前空契约被静默接受，`status` 仍 `completed`）。

### `F14` 契约 · 多声明一个本包产不出的字段
- **注入**：`task.md` 契约 = 16 个标准字段 + `example_only_field_marker`；
  `case.json.output_contract` 只声明 2 个（制造两个来源的冲突）。
- **实测**：`exit=0` · `status=completed` · 顶层 **21** 键（比基线多出该标记字段）
  · `uncertainty` 3 条 · `change_records` 9 步 · deck 有 · 耗时 1.61 s。
- **实测该字段的值**：`""`（空串），**不是 `null`**；`self_check.json.contract_check.valid=true`。
- **第一轮实测（修前）**：该字段值为 **`null`**，`contract_check` 判 `missing_required=["example_only_field_marker"]`，
  `contract_valid=False` ⇒ `main.py` 返回 **`exit=1`**（尽管 `status` 已是 `partial`）。
  根因：`common.CONTRACT_TYPE_DEFAULTS["any"] = None`，类型未声明的字段直接落 `null`，
  与 `references/OUTPUT_CONTRACT.md` §1「四形态回显，**禁止 null**」**自相矛盾**。
- **期望修订（诚实记录）**：原声明 `exit=1/partial`（按修前实测写的），**已改为** `exit=0/completed`；
  改的是**代码**（§3 Fix 4），修后同一注入下字段为 `""`、契约校验通过、退出码 0。

## 3. 由本演练暴露、并已修复的真实缺陷（逐条点名）

> 口径：**只做纯增量**。不改任何 CLI 参数名 / 默认值 / 退出码语义；不改任何既有键名与容器类型；
> 不删任何既有逻辑分支。下表 `+/-` 行为 `diff -u` 统计的**改动行数**（含新增注释行）。

| # | 文件 | +/- 行 | 触发它的注入行 | 修的是什么 | 修后行为 |
|-|-|-|-|-|-|
| Fix 1 | `scripts/deck_builder.py` | +24 / -1 | `F07` | `build_deck` 直接 `Presentation(template_path)`；模板存在但容器损坏时异常**穿透到編排器**，被记成 `status=failed`、退出码 1，违反 D5 | 先 `try` 打开；失败则记 `template_load_error` 并回落 `_new_deck()`（内置主题）。新增键 `template_expected`/`template_load_error`（`None`，不删旧键） |
| Fix 2 | `scripts/evidence.py` | +12 / -0 | `F05` | 无文本层 PDF 被记 `parsed=true`（`char_count=15`，只含 `--- page 1 ---` 分隔行），`status` 因此假 `completed` | 抽取后若**没有任何非空贯通文本行**，记 `parsed=false` + 明确 note（提示先 OCR），并 `return`；不影响有文本层的 PDF |
| Fix 3 | `scripts/common.py` | +27 / -2（与 Fix 4 合计） | `F12`·`F13` | `parse_output_contract_from_task` 对「契约块存在但不可用」只 `continue`，调用方拿不到原因 | 新增 `failed` 原因列表（非法 JSON / 空契约 / 表格字段 <5 / 无契约键），落到返回的 `note`；`specs` 语义不变 |
| Fix 4 | `scripts/common.py` | +5 / -0（含在上面 27 行内） | `F14` | `CONTRACT_TYPE_DEFAULTS["any"]=None` 使类型未声明的契约字段落 **`null`**，违反 OUTPUT_CONTRACT.md §1「禁止 null」 | `apply_contract` 里 `default is None → ""`；仍保留 `"null"` 映射用于**显式**声明 `"type":"null"` 的场景 |
| Fix 5 | `scripts/main.py` | +29 / -0（与 Fix 6 合计） | `F12`·`F13` | 契约解析失败的 `note` 被丢弃（`ts, _note = ...`），既不进 `change_records` 也不进 `uncertainty`，`status` 仍 `completed` | 捕获 `note`；契约块存在却不可用时写 `change_records`（新步名 `contract`）+ `uncertainty`，并按「无法判断」把 `status` 降为 `partial` |
| Fix 6 | `scripts/main.py` | +12 / -0（含在上面 29 行内） | `F07` | 模板回落后，降级原因只在 `artifacts.deck_mode`，只读 `uncertainty` 的复核者看不到 | `deck_mode.template_load_error` 非空时追加一条 `uncertainty`（含异常类型与原因 + 修复建议）。`status` 不改（模板缺失不在契约 §3 的 `completed` 五条件内） |

**未改动的脚本**（逐字节不变，共 12 个；**此句的主体是 v4 那一版包** —— v6 里 `main.py` 另含 v5 的 Fix 7，合计 +53 / -0）：
`check_contract.py`、`evidence_audit.py`、`finalize_result.py`、`make_synthetic_inputs.py`、`render.py`、
`scaffold_plan.py`、`selftest.py`、`validate_plan.py`、`validate_result.py`、`verify_deck.py`
（其余为本次新增的 `fault_inject.py`）。

**CLI / 退出码自查**：`main.py` 的 `--case --out --task --materials --template --skip-previews --quiet`
七个参数名、`required` 与默认值全部未动；`exit 0/1/2` 三分语义未动
（唯一可观察变化是 `F07`/`F14` 从 `1` 变成**应当的** `0`，这正是 Fix 1/Fix 4 的目的）。

## 4. 覆盖边界：这张表**没有**证明什么

写明未覆盖面，避免把本表读成"全形态已验"：

1. **注入器不改主流程**：所有注入都发生在沙箱的**输入/环境**侧，不改 `scripts/*.py`。
   ⇒ 它验证的是「输入/依赖/契约坏掉时编排器怎么反应」，**不**验证「主流程代码本身被写坏时会怎样」。
2. **依赖缺失用导入遮罩模拟**，不是真的卸载。遮罩抛的是 `ImportError`（比真实的
   `ModuleNotFoundError` 更宽），可能比真实环境**更容易**被捕获。真实缺包环境请按 `README.md`
   的依赖表核验；两者行为已在 `F09`/`F10`/`F11` 的 stdout 里被区分记录。
3. **`F10` 的连带效应**（Pillow 缺失 ⇒ python-pptx 也不可用）是**实测观察**，
   未做"只缺 Pillow 而不缺 python-pptx"的隔离环境验证 —— 那需要在真实环境卸载 Pillow 再装回，
   超出本沙箱能力。故该行的 deck 缺失**不能**单独归因给 Pillow。
4. **未覆盖的失败形态**（已知未注入）：磁盘写满 / 只读输出目录 / 路径权限拒绝 /
   超长材料导致超时 / 平台 900 秒预算被打满 / `case.json` 是合法 JSON 但键类型全错
   （如 `slide_count` 是字符串）/ 材料是超大 PDF。这些**没有实测数据**，本表不作任何断言。
5. **未做重复性统计**：每行只跑 **1** 次。耗时栏是单次观测（0.52–1.76 s），
   不构成性能结论；`status`/`exit` 属于确定性输出（同输入同结果），但**未**用双跑比对 sha 证明。
   双跑一致性由包内 `self_check.json.determinism` 与 `references/CONTRACT-GATES.md` 的 G 门另行覆盖。
6. **对照组的 `completed` 依赖 prime**：若在**没有**预生成二进制输入的环境里跑本脚本
   （或显式 `--no-prime`），`F00` 会回落成 `partial`，其余各行的归因强度随之下降。
   本表数据均为 `prime` 开启下的实测。
7. **平台侧行为不在本表范围**：本表演练的是**本包脚本**的降级语义，
   不代表评测平台会如何记录这些降级（平台日志、预检与队列状态均不在本包可控范围内）。


---

# 【合并段】多案例泛化题集（原文，含 3 条失效边界）

> 本段原为独立文件 `references/CASE-SET.md`，在 v6（union 包）中并入本文件以守住「≤50 文件」硬门；**内容逐字保留**，未删减。

# CASE-SET.md — 多案例泛化题集（v5）

> **本文件里的每一个数字都来自真跑**，不是在别的案例上测完再推算的。
> 运行方式见 §0；两个合成案例的输入在 `examples/cases/`；边界探针（§4）的输入是临时改造的
> 副本，**不随包提交**（它们的作用是"如实定位泛化到哪里失效"，不是提供更多示例）。
> 所有数值均为**空构造的合成数据**，不代表任何真实研究，不得被引用为科学结论。

## 0. 复现命令

```bash
SKILL_DIR="<本包根目录>"
OUT="<包外空目录>"
for c in case-a-muon-defense case-b-scrna-review; do
  python "$SKILL_DIR/scripts/main.py" \
    --case "$SKILL_DIR/examples/cases/$c/case.json" \
    --task "$SKILL_DIR/examples/cases/$c/task.md" \
    --out "$OUT/$c"
done
```

采集环境：Python 3.13.9 · python-pptx 1.0.2 · Pillow 12.3.0 · pypdf 6.14.2 · win32
（**包外目录**运行；包内跑会生成 `__pycache__` 而使提交包不合规）。

## 1. 题集总览

| 案例 | 题材 | 汇报类型 | 听众 | 时长 | 冻结页数 | 难度层 | 主要考察点 |
|-|-|-|-|-|-|-|-|
| `case-a-muon-defense` | 凝聚态**实验物理**（μSR 内场分布反演） | `defense`（学位答辩） | 答辩委员会（expert） | 25 min | 15 | **L2 中** | 方法页/结果页的数值证据链；**三条局限必须靠前**；图表引用存在但图片文件缺席 → 诚实占位 |
| `case-b-scrna-review` | 计算**生物学**（单细胞计数去噪） | `review`（评审答辩） | 评审专家组（expert） | 12 min | 8 | **L3 偏难** | **结论先行**的块顺序；**两个互相矛盾的指标必须同时上页**；短时长下的取舍压缩 |

> **为什么是这两个题材**：它们与 `examples/` 里的最小示例（NLP 跨语言句子对齐）在
> **学科、汇报类型、时长量级、页数量级**四个维度上都不同 —— 这样才能检验"换题材还成不成立"，
> 而不是"同样的东西再跑一遍"。两个案例都**不提供图片文件**，用来走通"引用存在、文件缺席"的
> 诚实占位路径（`deck_mode` 与 `preview_manifest` 会记明）。

## 2. 逐案：输入 / 期望产出结构 / 可接受区间 / 实测结果

### 2.1 `case-a-muon-defense`

**输入**：`case.json`（`report_type=defense`、`audience` 为答辩委员会描述、`duration_min=25`、
`slide_count=15`、`materials` 两项）+ `task.md`（含 `output_contract` 声明块）+
`materials/muon_extract.md`（1165 字符，5 个章节）+ `materials/figures.md`（438 字符）。

**期望产出结构**（可判定的清单）：

| 项 | 期望 | 可接受区间 |
|-|-|-|
| 页数 | == 冻结页数 15 | 恰好 15（P3 门） |
| 块顺序 | 答辩叙事，含 `agenda` 与 `innovation_limits`（"局限/创新边界"后置块） | 顺序中 `motivation` 在 `method` 之前、`innovation_limits` 在 `results` 之后 |
| 结果页数 | 3–5 页 | 实测 4（页 7–10） |
| 局限/边界块页数 | ≥ 2 页 | 实测 2（页 11–12） |
| `qa` 备用页 | ≥ 1 页 | 实测 2 页（页 14–15） |
| 问答条数 | ≥ 2 条（每条局限 + 每条 strong 结果） | 实测 3 条 |
| 图表引用 | 与源材料一致，不许臆造 | 实测 `Fig. 1` 绑定到页 7，页内为**诚实占位**（无图片文件） |
| `status` | `completed` | 实测 `completed` |
| `result.json` 顶层键 | 契约 16 字段齐全 | 实测 20 键（契约字段 + `audit`/`environment`/`generated_*`） |
| 证据审计 | `valid=true`、`errors=0` | 实测 `11/11 ok`、`derived=3` |

**实测（真跑一次）**：

```
[plan] 15 pages, narrative=defense, audience=expert, P-gates valid=True
[deck] 15 slides, mode=built-in-theme, verify valid=True
[preview] wrote 14 preview files (PIL simulation)
[done] status=completed deck_ok=True preview_ok=True plan_gates=True evidence_audit=True
       validate_valid=True contract_valid=True
EXIT=0
```

- 叙事顺序（实测）：`title, agenda, motivation, background, method, results, innovation_limits, conclusion, qa`
- `main_line` 计数（实测）：`research_question=1, method=2, results=4, limitations=2, conclusion=1`
- 逐页强度（实测）：`strong` ×6 · `medium` ×1 · `weak`(derived) ×3 · 结构页 ×5
- `plan_gates`（实测）：`gates=8 ok=8`，`P3 detail = "pages=15 target=15"`
- `evidence_audit`（实测）：`content_pages=11, ok_pages=11, errors=0, derived_pages=3`
- 产物（实测）：`editable_deck.pptx`（15 页，verify 通过）· `previews/` 14 个文件 · `uncertainty` 4 条

### 2.2 `case-b-scrna-review`

**输入**：`case.json`（`report_type=review`、`duration_min=12`、`slide_count=8`）+
`task.md` + `materials/scrna_extract.md`（1077 字符）+ `materials/figures.md`（408 字符）。

**期望产出结构**：

| 项 | 期望 | 可接受区间 |
|-|-|-|
| 页数 | == 冻结页数 8 | 恰好 8（P3 门） |
| 块顺序 | **结论先行**：`conclusion` 出现在 `method`/`results` **之前** | 实测顺序中 `conclusion` 位于第 3 页 |
| 两个矛盾指标 | 同时出现在页面上（10.9% 与 0.4%） | 两者都必须能在 `pages[].claim` 或 `evidence[].quote` 里找到 |
| 结果页数 | 2–3 页 | 实测 2（页 5–6） |
| `qa` 备用页 | 1 页 | 实测 1 页（页 8） |
| 问答条数 | ≥ 2 条 | 实测 2 条 |
| `status` | `completed` | 实测 `completed` |
| 证据审计 | `valid=true`、`errors=0` | 实测 `5/5 ok`、`derived=1` |

**实测（真跑一次）**：

```
[plan] 8 pages, narrative=review, audience=expert, P-gates valid=True
[deck] 8 slides, mode=built-in-theme, verify valid=True
[preview] wrote 8 preview files (PIL simulation)
[done] status=completed ... validate_valid=True contract_valid=True
EXIT=0
```

- 叙事顺序（实测）：`title, agenda, conclusion, method, results, innovation_limits, qa`
  ⇒ **结论先行成立**：`conclusion` 在 `method`/`results` 之前，与 `templates/talk_config.json`
  里 `review` 的块顺序一致。
- `main_line` 计数（实测）：`research_question=0, method=1, results=2, limitations=1, conclusion=1`
- 图表引用（实测）：`Table 1` 绑定页 4、`Fig. 1` 绑定页 6，均为诚实占位
- `plan_gates`（实测）：`gates=8 ok=8`，`P3 detail = "pages=8 target=8"`
- `evidence_audit`（实测）：`content_pages=5, ok_pages=5, errors=0, derived_pages=1`
- 产物（实测）：`editable_deck.pptx`（8 页）· `previews/` 8 个文件 · `uncertainty` 4 条

> **该案暴露的结构性事实**：`main_line.research_question = 0`。原因是 `review` 叙事里
> **没有 `motivation` 块**（结论先行的代价），而 `main_line.research_question` 只由
> `motivation` 块填充。⇒ 读 `main_line` 的下游消费者必须允许该键为空数组，
> 不能假设四种汇报类型都有研究问题条。

## 3. 两案对比：换题材/换类型真正改变了什么（实测，非推断）

| 维度 | case A（物理 · 答辩） | case B（生物 · 评审） | 变化来自 |
|-|-|-|-|
| 块顺序 | `...motivation, background, method, results, innovation_limits, conclusion...` | `...conclusion, method, results, innovation_limits...` | `report_type` 驱动的叙事配置 |
| 页数 | 15 | 8 | 案例冻结页数（P3 门） |
| `agenda` 页 | 有（页 2） | 有（页 2） | 配置 |
| `motivation` 页 | 有（页 3） | **无** | 评审类型的块集合 |
| `background` 页 | 有（页 4，derived/weak） | **无** | 同上 |
| 问答条数 | 3 | 2 | 强结果数 + 局限数 |
| 逐字证据页 | 8/11 内容页有逐字引文 | 4/5 | 材料句式与 claim 分类覆盖度 |

⇒ 同一套脚本在**两个学科、两种汇报类型、两种量级**上都产出了契约完整、门全过、可复核的结果，
**没有**依赖任何与题材绑定的硬编码分支（`templates/talk_config.json` 是配置而非代码）。

## 4. 泛化到哪里会失效（**如实写明**，每条都有实测支撑）

下面四条都是**真跑出来的**，不是推测。前三条**没有修**（属于设计取舍或已知边界），
第四条**已修并给出回归证据**。

### 4.1 未知 `report_type` 会被静默替换，且 `agenda` 页会消失 ❌ 未修（已知边界）

- **探针**：把 case A 的 `report_type` 改成 `workshop_retreat`（本包配置里没有的类型）。
- **实测**：`status=completed` · 15 页 · P-gates 8/8 全过；`talk_plan.json.narrative.report_type`
  被记成 **`group_meeting`**（不是输入的 `workshop_retreat`），块顺序变成
  `title, motivation, background, method, results, conclusion_risk, qa` ——
  **`agenda` 页消失**（组会模板不含目录页），且 `uncertainty` **没有**任何相关条目（仍是 4 条通用项）。
- **失效率**：任何不在 `templates/talk_config.json` 三个类型（`group_meeting`/`defense`/`review`）
  内的汇报类型，都会**静默**退回组会模板。
- **为什么没修**：退回默认模板本身是合理的兜底（不该让未知类型直接失败），
  但"静默"这一点是真实缺陷。**本包选择如实披露而不是悄悄改行为**：如果要用未知类型，
  请先在 `templates/talk_config.json` 里加一条配置（配置是纯 JSON，不需要改代码）。
- **给使用者的判据**：跑之前确认 `report_type` ∈ 三个已配置值；否则 `talk_plan.json.narrative.report_type`
  会与 `case.json` 不一致，**以 `talk_plan.json` 的值为准**。

### 4.2 页数被硬钳制在 [6, 30]，极端冲突**不报不确定度** ❌ 未修（已知边界）

- **探针**：case A 改为 `duration_min=5, slide_count=40`（5 分钟讲 40 页，物理上不可行）。
- **实测**：产出 **30** 页（不是 40）；`result.json.slide_count=30`；`timing={"duration_min":5.0,
  "slide_target":30,"seconds_per_slide":10.0}`；`P3 detail="pages=30 target=30"` —— 
  **P3 门通过了**，因为它比对的是"已钳制后的目标"，而不是输入里的 40；
  `uncertainty` 仍只有 4 条通用项，**没有**任何"页数被钳制"的说明。
- **根因（源码可查）**：`scripts/scaffold_plan.py` 里 `slide_target = max(6, min(30, int(slide_target)))`。
- **失效率**：`slide_count` 或时长推导结果落在 [6,30] 之外时，冻结页数被静默改写；
  5 分钟/30 页 ⇒ 10 秒每页，仍被报为 `completed`。
- **为什么没修**：钳制是防崩的合理设计，改它会影响所有已验收案例的页数。
  **本条的正确用法**：把 `slide_count` 当作"请求值"，**以下游 `result.json.slide_count` 为准**；
  若两者不等，说明被钳制了（可自行对比）。

### 4.3 非中文材料：能抽到主张，但页面全部退化成概括页 ⚠️ **已修（Fix 7）**，并给出回归证据

- **探针**：把 case A 的材料换成**纯英文**论文体（876 字符，含摘要/方法/结果/局限四个小节）。
- **修前实测**：`status=completed` · P-gates 8/8 全过 · **`derived_pages=11 / content_pages=11`**
  —— 11 个内容页**全部**是无逐字引文的概括页，`strength` 全部 `weak`，
  而 `status` 仍是 `completed`、`uncertainty` 里没有这一条。**典型的静默质量损失。**
- **根因（实测定位）**：`scripts/evidence.py` 能抽出英文 claim（实测 **6** 条，`strength=strong`），
  但 claim 分类器（`classify_claim`）是**中文研究动词驱动**的，英文句全部落成 `kind=general`，
  规划器无法把它们路由进 `method`/`results`/`limits` 块 ⇒ 只能生成 `derived` 概括页。
- **已修（Fix 7，纯增量）**：`scripts/main.py` 增加判据 ——
  「抽到的主张 ≥ 3 条」且「内容页 > 0」且「`derived_pages >= content_pages`」⇒
  写 `change_records`(step=`audit`) + `uncertainty`，`status → partial`。
  判据刻意收紧，**设计内的 D8 概括页（claims 本来就少）不会误伤**。
- **修后实测（同一探针）**：`status=partial`（退出码仍 `0`），`uncertainty` 由 4 条增至 **5** 条，
  新增条目原文：`材料中共抽出 6 条候选主张，但它们一条都没有被逐字引用到页面上
  （11 个内容页全部是概括页 derived=true）`；`change_records` 尾部出现第二个 `audit` 步。
- **回归确认（同一次修复后重跑两案）**：case A 与 case B 仍为 `status=completed`
  （`derived_pages` 分别为 3/11 与 1/5，均未触发该判据）⇒ 修复**没有**影响正常中文案例。
- **仍然失效的部分**：Fix 7 只把"静默"变成"可见"，**没有**让英文材料产出逐字证据页 ——
  claim 分类词表仍是中文的。要用英文材料跑出完整证据链，需要扩展 `classify_claim` 的词表
  （本版不做：那属于算法改动，超出"纯增量"边界）。

### 4.4 未验证的方向（明确声明**没有**实测数据）

以下方向本版**没有**跑过，因此不作任何断言（不是"应该没问题"，是"不知道"）：

1. **超过两个材料文件、材料间数值互相矛盾** —— 只测了 2 个材料；跨材料的矛盾数字由
   `validate_result.py` 给警告，但矛盾的取舍规则未测。
2. **超长材料**（比如 5 万字符以上的整篇论文）—— 未测截断行为与耗时。
3. **非中非英材料**（日/俄等）—— 未测。
4. **真实 PDF**（有文本层）—— 两个合成案例**都不含 PDF**；PDF 路径由 v4 的
   `references/VALIDATION-EVIDENCE.md` 覆盖（含"无文本层 PDF"的注入实测），但**本文件不重复声称**。
5. **同一案例重复三次**（平台是 3 案例 × 3 复跑）—— 本文件只记录**单次**运行；
   双跑一致性由 `TEST.md` 的确定性探针另行覆盖，**不是**同一件事。
6. **模板适配模式下的两个新案例** —— 两案都是 `mode=built-in-theme`（案例未提供模板）；
   模板路径由 case A/B 之外的既有 `TEST.md` T5 与 v4 的 `F06`/`F07`/`F08` 覆盖。

## 5. 这套题集能被别人怎么复用

- **可整块拿走**：`examples/cases/` 下每个案例是自包含的（`case.json` + `task.md` + `materials/`），
  换掉 `materials/` 与 `case.json` 的描述字段就是一个新案例，**不需要改任何代码**。
- **可作对照基线**：§2 的"期望产出结构"表刻意写成**可判定项**（页数、块顺序、页数区间、
  问答条数、审计数值），可以直接当验收脚本的判据。
- **可作反例使用**：§4.1–4.3 三个探针是**故意造出来的失败输入**，用来验证"降级是否可见"，
  比正例更有判别力；它们不随包提交，但重建步骤已在文中写清（改 `case.json` 的一个字段）。
- **难度分层**：L1 = `examples/`（NLP，20 min/12 页，有 PDF）→ L2 = case A（物理，25 min/15 页，
  无图片）→ L3 = case B（生物，12 min/8 页，结论先行 + 矛盾指标）。L3 不是"更长的材料"，
  而是"约束彼此冲突"，因此更难。

---

# 【合并段】机器可读案例清单（原 `assets/case-set.json`）

> v6 把该 JSON 并入本文以守住文件数硬门；内容逐字保留，需要机器读取时原样存成 `.json` 即可。

```json
{
  "asset": "case-set",
  "asset_version": "1.0",
  "purpose": "可复用题集骨架：把'一场汇报的输入'参数化成三个可直接复制的 case.json 模板。它们只定义输入（听众/时长/页数/报告类型/材料清单形状），不含任何内容答案；正式案例的内容由使用方自己填。",
  "how_to_use": [
    "复制其中一个模板为新的 case.json，填入 case_id / title / report_goal 与真实 materials 路径；",
    "把 output_contract 保持为 16 个内置字段（或按需追加）；",
    "python \"$SKILL_DIR/scripts/main.py\" --case <新 case.json> --out <out>，再按 references/CONTRACT-GATES.md 复核。"
  ],
  "contract_note": "三个模板的 output_contract 与本包 DEFAULT_CONTRACT_FIELDS 对齐；追加字段遵守'契约只增不减、禁 null'。",
  "templates": [
    {
      "template_id": "case-template-group-meeting",
      "report_type": "group_meeting",
      "audience_example": "组会：同组研究生与导师，熟悉本领域、不熟悉本工作的技术细节",
      "duration_min": 20,
      "slide_count": 12,
      "narrative_focus": "问题—进度—方法—结果—风险—问答",
      "success_criteria_example": [
        "讲清当前进度与两个主要风险",
        "关键数字能定位到源材料",
        "提前准备对局限与下一步的追问"
      ],
      "materials_shape": [
        {"path": "materials/paper_extract.md", "role": "论文主体（摘要/引言/方法/结果/局限）"},
        {"path": "materials/figures.md", "role": "图表清单与引用定位"}
      ]
    },
    {
      "template_id": "case-template-defense",
      "report_type": "defense",
      "audience_example": "答辩：评审专家，关注创新点、边界与证据强度",
      "duration_min": 15,
      "slide_count": 14,
      "narrative_focus": "问题—方法—结果—创新点与边界（后置）—结论—问答",
      "success_criteria_example": [
        "创新点与适用边界各有一页明确主张",
        "证据强度分级与结论强度匹配",
        "预判机制/数据/对照类追问"
      ],
      "materials_shape": [
        {"path": "materials/thesis_extract.md", "role": "论文主体"},
        {"path": "materials/figures.md", "role": "图表清单"},
        {"path": "materials/dataset_card.pdf", "role": "数据卡片（PDF 解析路径）"}
      ]
    },
    {
      "template_id": "case-template-review",
      "report_type": "review",
      "audience_example": "评审：同行评议人，关注结论的证据强度与适用范围",
      "duration_min": 10,
      "slide_count": 10,
      "narrative_focus": "结论先行—证据链—方法可信度—局限与适用范围—问答",
      "success_criteria_example": [
        "结论先行的首页给出结论与其证据强度",
        "每个结论都能回溯到源材料位置",
        "明确写出适用范围与不适用情形"
      ],
      "materials_shape": [
        {"path": "materials/report_extract.md", "role": "研究报告主体"},
        {"path": "materials/figures.md", "role": "图表清单"}
      ]
    }
  ],
  "output_contract": [
    "case_id", "status", "title", "report_goal", "audience", "duration_min",
    "slide_count", "summary", "main_line", "pages", "evidence_map", "artifacts",
    "sources", "uncertainty", "change_records", "contract"
  ],
  "disclaimer": "三个模板均为输入骨架（合成），不含任何正式案例的内容或答案；不得当作平台案例的作答使用。"
}
```
