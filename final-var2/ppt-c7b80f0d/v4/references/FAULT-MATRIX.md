# FAULT-MATRIX.md — 失败注入矩阵与恢复演练（v4 主轴）

> 本文件回答的是**可靠体验（10 分）+ 可验证性**这一维最容易被空谈的问题：
> **"把东西弄坏之后，这条流水线是'响亮地失败并留下记录'，还是'安静地成功'？"**
>
> 表里**每一个数字都是跑出来的**：`scripts/fault_inject.py` 把主流程当黑盒，
> 每条注入真的删掉/写坏一个文件、真的用 `meta_path` 钩子屏蔽一个依赖，然后在
> **包外沙箱**里跑一次 `main.py`，读回 `result.json` 与退出码，再撤掉故障重跑一遍。
> 表格由脚本渲染（`--emit-matrix`），**不接受手抄**：
> 改了实现就重跑，数字自己会变，谎报活不过一次复跑。

---

## 1. 怎么复跑（30 秒，包外）

```bash
# 1) 把技能复制到包外（绝不在包内跑：__pycache__ 会让技能资源不合规）
cp -r "$SKILL_DIR" /tmp/skill-fault-drill
# 2) 跑全量注入 + 恢复演练，渲染矩阵与 JSON 报告
python /tmp/skill-fault-drill/scripts/fault_inject.py \
    --out /tmp/fault-report --emit-matrix /tmp/fault-report/matrix.md
# 退出码：0 = 全部注入都被记录且恢复干净；1 = 有静默失败或恢复失败；
#         2 = 环境不可用（健康基线自己都跑不通，注入结论无意义）；3 = 用法/输入错误
# 3) 只看某几条（调试用）
python /tmp/skill-fault-drill/scripts/fault_inject.py --out /tmp/fault-report \
    --only DP-01,TP-02,CT-01
```

输出：
- `/tmp/fault-report/fault-report.json` —— 全量结构化证据（每条注入的退出码、status、
  留痕命中、结构化探针、恢复结果、耗时）；
- `/tmp/fault-report/matrix.md` —— 下面 §3 这张表（本文件即由它渲染）。

**写盘纪律**：脚本只写 `--out` / `--work`；所有子进程带 `PYTHONDONTWRITEBYTECODE=1`
（不产生 `__pycache__`）；唯一需要"破坏技能包"的一条（CT-03 契约文档缺失）破坏的是
**技能的临时副本**；子进程的 `cwd` 是沙箱而不是技能根，因此这一轮注入**顺带**复核了
"cwd 不是技能根也能跑"的承诺。

---

## 2. 判定口径（由代码决定，不由眼睛决定）

| 判定 | 定义（`fault_inject.verdict()` 原文语义） |
|-|-|
| **静默失败** | 子进程 `exit 0` **且** `status=completed` **且** 注入特征在 `uncertainty`/`change_records`/`sources`/`deck_error`/审计字段里**一次都没出现** **且** 没有结构化探针反驳"一切正常" |
| **与文档不一致** | 实测退出码不在文档集合内，**或** status 不在文档集合内，**或** 故障指纹没被记录（文本命中或结构化探针） |
| **恢复成功** | 撤掉故障、同一条命令重跑 ⇒ `exit 0` + `status=completed` |

两类证据缺一不可：`needles`（人复核会去 grep 的文本指纹）与 `probe`（从产物本身算出来的
结构化断言，例如"每个被声明的契约字段都回显了且非 null"）。**"我们记录了"这句话不能靠散文**。

---

## 3. 实测矩阵（24 条注入 · 由 `fault_inject.py` 生成）

<!-- MATRIX-BEGIN -->
<!-- 本表由 scripts/fault_inject.py --emit-matrix 从真实运行数据渲染。不要手改数字：改脚本后重跑即可。 -->

| ID | 形态 | 注入什么（真实故障） | 期望行为（文档口径） | 实测退出码 | 实测 status | 实测留痕（uncertainty / 审计字段 / 结构化探针） | 静默失败 | 与文档一致 | 已知缺口 | 恢复后实测 |
|-|-|-|-|-|-|-|-|-|-|-|
| IN-01 | ① 输入形态 | `--case` 指向不存在的文件（case.json 不存在） | main.py → 3；不产出 result.json（不发明产物） | 3 | `None` | case file not found; no_result_written=✓ | 否 | 是 | 无 | —（后置校验类，无重跑语义） |
| IN-02 | ① 输入形态 | case.json 是**损坏的 JSON**（截断在 `{ "case_id": `） | main.py → 3；仍写出 `status=failed` + `error=case_unreadable` 的 result.json | 3 | `failed` | case_unreadable; status_failed=✓; result_written=✓ | 否 | 是 | 无 | exit 0 / `completed` ✅ 回到 completed |
| IN-03 | ① 输入形态 | case.json 声明的**材料路径不存在** | `material_status=unreadable`；不建 deck；**绝不写 completed** | 1 | `failed` | no readable paper material found; unreadable; material_marked_unreadable=✓; not_completed=✓ | 否 | 是 | 无 | exit 0 / `completed` ✅ 回到 completed |
| IN-04 | ① 输入形态 | 材料文件存在但**内容为空**（0 字节） | 与材料缺失同类处置：`status≠completed`、无 deck、有 uncertainty 说明 | 1 | `failed` | no readable paper material found; not_completed=✓; no_deck=✓ | 否 | 是 | 无 | exit 0 / `completed` ✅ 回到 completed |
| IN-05 | ① 输入形态 | **完全不给页级方案**（无 `--spec`、无 `--demo`） | 不得静默成功：`spec_lint` 报无方案、无 deck ⇒ exit 1 且 `status=failed`（R2-FIX-03/03b 前：exit 0 + self_check.ok + 只写 partial） | 1 | `failed` | no spec loaded; no_spec_recorded=✓; not_silent_success=✓ | 否 | 是 | 无 | exit 0 / `completed` ✅ 回到 completed |
| IN-06 | ① 输入形态 | `--spec` 是**损坏的 JSON**（截断） | 文档未写此分支；底线：**不得静默成功**，且降级后仍写出可读的 result.json（R2-FIX-07 前：裸 JSONDecodeError 崩溃、连产物都没有） | 1 | `failed` | JSONDecodeError; non_zero_exit=✓; result_written=✓; status_failed=✓ | 否 | 是 | 无 | exit 0 / `completed` ✅ 回到 completed |
| IN-07 | ① 输入形态 | 页数上限被压到 `slide_count=3`（方案本身 6 页） | `deck.page_budget_met=false` + uncertainty；**绝不静默丢弃证据页** | 0 | `completed` | page budget; budget_flag_false=✓; deck_still_built=✓; no_evidence_page_dropped=✓ | 否 | 是 | 无 | exit 0 / `completed` ✅ 回到 completed |
| IN-08 | ① 输入形态 | **陈旧产物**：同一 `--out` 先成功跑一遍，再以空材料重跑（覆盖检查） | 重跑必须用本次结果覆盖 result.json，不得让上一轮的 completed 冒充本轮 | 1 | `failed` | no readable paper material; first_run_clean=✓; result_overwritten=✓; second_run_not_completed=✓ | 否 | 是 | 无 | exit 0 / `completed` ✅ 回到 completed |
| TP-01 | ② 模板形态 | 方案声明的组织方模板**文件不存在** | 正常分支：回退内置 16:9 版式、`deck.template.kind=builtin` + uncertainty，仍交付 | 0 | `completed` | builtin; fell_back_to_builtin=✓; still_delivered=✓ | 否 | 是 | 无 | exit 0 / `completed` ✅ 回到 completed |
| TP-02 | ② 模板形态 | 模板文件存在但**内容不是 OOXML**（文本改名 .pptx，`Presentation()` 抛错） | `deck.template.error` 记录 + 回退内置版式 + uncertainty；产物仍可交付 | 0 | `partial` | builtin; fell_back_to_builtin=✓; error_recorded=✓; still_delivered=✓ | 否 | 是 | 无 | exit 0 / `completed` ✅ 回到 completed |
| TP-03 | ② 模板形态 | 模板文件是 **0 字节**（半截下载/写盘中断的典型形态） | 同 TP-02：如实记录 error 并回退内置版式 | 0 | `partial` | builtin; fell_back_to_builtin=✓ | 否 | 是 | 无 | exit 0 / `completed` ✅ 回到 completed |
| TP-04 | ② 模板形态 | 模板路径指向**空目录**（给了模板目录但里面没有 .pptx） | `resolve_template → builtin`，按正常分支继续 | 0 | `completed` | builtin; fell_back_to_builtin=✓ | 否 | 是 | 无 | exit 0 / `completed` ✅ 回到 completed |
| TP-05 | ② 模板形态 | 模板是**半截 .pptx**（真容器被截断一半） | 同 TP-02：记录 error、回退内置版式、不生成假文件 | 0 | `partial` | builtin; fell_back_to_builtin=✓; error_recorded=✓; still_delivered=✓ | 否 | 是 | 无 | exit 0 / `completed` ✅ 回到 completed |
| DP-01 | ③ 依赖形态 | **缺 `python-pptx`**（meta_path 钩子让 `import pptx` 抛 ImportError） | 文档 §2.3：`deck=null` + 状态降级 + `deck_error` + uncertainty，**不生成假文件**；（R2-FIX-01 前这里是裸 ImportError 崩溃、连 result.json 都没有） | 1 | `failed` | pptx; result_written=✓; deck_null=✓; deck_error_recorded=✓; status_downgraded=✓; non_zero_exit=✓ | 否 | 是 | 无 | exit 0 / `completed` ✅ 回到 completed |
| DP-02 | ③ 依赖形态 | **缺 `Pillow`**（`from PIL import Image` 抛 ImportError）——注意 python-pptx 自己也依赖 Pillow，所以这一条实际覆盖的是「渲染栈整体缺失」 | 文档 §2.3：`previews=[]`、状态降级、如实说明且**不生成假产物**；（R2-FIX-01 前这里是裸 ImportError 崩溃、连 result.json 都没有） | 1 | `failed` | PIL; previews_empty=✓; status_downgraded=✓; deck_error_recorded=✓; no_fake_artifacts=✓ | 否 | 是 | 无 | exit 0 / `completed` ✅ 回到 completed |
| DP-03 | ③ 依赖形态 | **缺 `matplotlib`**（重建图后端不可用；材料/方案/契约都正常） | 跳过重建图、保留引用与数字，`charts[].chart.reason` + uncertainty；主交付物不受影响 | 0 | `completed` | reconstructed chart skipped; chart_skipped_with_reason=✓; matplotlib_flagged=✓; deck_still_built=✓ | 否 | 是 | 无 | exit 0 / `completed` ✅ 回到 completed |
| DP-04 | ③ 依赖形态 | 材料是 PDF 而 **PDF 后端全缺**（fitz/pypdf/pdfplumber 同时被屏蔽） | 不做 OCR 冒充；`run_meta.pdf_tools` 全 false 如实记录，状态降级 | 1 | `failed` | no readable paper material; all_pdf_backends_flagged=✓; not_completed=✓ | 否 | 是 | 无 | exit 0 / `completed` ✅ 回到 completed |
| CT-01 | ④ 契约形态 | `output_contract` 声明**未知字段**（四种形态混合，其中一个声明值就是 `null`） | 四形态规则：全部回显、**任何声明字段禁止 null**；`check_contract --case` exit 0 | 0 | `completed` | output_contract; declared_fields_echoed=✓; no_declared_field_is_null=✓; check_contract_exit_0=✓ | 否 | 是 | 无 | exit 0 / `completed` ✅ 回到 completed |
| CT-02 | ④ 契约形态 | `output_contract` 用**形态④（字段清单 list）**，含一个包内不存在的名字 | 每个名字按类型给空值回显、禁止 null；`check_contract --case` exit 0（R2-FIX-04 前：list 形态不填语义字段 → main.py exit 1） | 0 | `completed` | output_contract; declared_fields_echoed=✓; no_declared_field_is_null=✓; check_contract_exit_0=✓ | 否 | 是 | 无 | exit 0 / `completed` ✅ 回到 completed |
| CT-03 | ④ 契约形态 | **契约文档本身缺失**（在技能的**临时副本**里删掉 `references/OUTPUT_CONTRACT.md`） | 契约同源门兜住：`self_check.ok=false` + main.py → 1，且问题项点名契约 | 1 | `completed` | contract document not found; result_written=✓; self_check_ok_false=✓; self_check_names_contract=✓ | 否 | 是 | 无 | —（后置校验类，无重跑语义） |
| CT-04 | ④ 契约形态 | 交付后**人为删掉 result.json 的两个顶层字段**（`run_meta` / `evidence_map_json`） | `check_contract` exit 1 并逐个列出缺失字段；`export_check` 报 missing required key | 0 | `completed` | run_meta; check_contract_exit_1=✓; check_contract_lists_both=✓; export_check_exit_1=✓ | 否 | 是 | 无 | —（后置校验类，无重跑语义） |
| CT-05 | ④ 契约形态 | `case_id` 对不上：case.json 没有 `case_id`，且交付后被改成另一个值 | G1：`case_id` 非空**且与 case 一致** → 与案例不一致时 `export_check` 应判 error——**实测是已知缺口**，见备注 | 0 | `completed` | case_id; case_id_fell_back=✓; export_check_reported_error=✗ | 否 | 是 | 是 — G1 的实现只断言 result.json 自己的 `case_id` 非空，**不与 case.json 对照**；对照承诺只写在 OUTPUT_CONTRACT.md §5 的表里。测试者已按人复核清单覆盖，但脚本门不拦——如实记... | exit 0 / `completed` ✅ 回到 completed |
| ST-01 | ⑤ 状态一致性 | **伪造状态**：真实降级（某页 `evidence_gap`）后，把 `status` 手改成 `completed` | 不变量 I1–I6 禁止此形态；期望导出门能判 error——**实测是已知缺口**，见备注 | 0 | `completed` | gap; honest_status_was_not_completed=✓; export_check_caught_forgery=✗ | 否 | 是 | 是 — 静态产物校验器看不到「上一次运行的真实状态」，无法区分伪造与真 completed；本行如实记为**检测能力缺口**，不假装已覆盖。 | —（后置校验类，无重跑语义） |
| ST-02 | ⑤ 状态一致性 | **抹掉降级记录**：某页 `evidence_gap` 后把 `uncertainty` 清空（违反「降级必须留痕」） | 「uncertainty 为空」只允许出现在整条链路无降级时；期望能检出——**实测是已知缺口** | 0 | `partial` | uncertainty; gap; honest_run_had_uncertainty=✓; export_check_caught_erasure=✗ | 否 | 是 | 是 — 清空 uncertainty 后，产物自身仍是自洽的（status=partial 与 evidence 缺口一致），静态校验器没有「应有的 uncertainty」基线可比对 ⇒ 记为**检测能力缺口**。 | —（后置校验类，无重跑语义） |

**基线对照**（同一夹具、未注入任何故障）：`main.py` exit 0 / `status=completed` / 8 页 / 顶层字段 19 / 预览 7 个 / uncertainty 0 条 / `export_check` exit 0 / `check_contract` exit 0。

**统计（本次实测）**：注入 24 条 · **静默失败 0 条** · 与文档口径不一致 0 条 · 有恢复动作的 19 条中回到 `exit 0 + completed` 的 19 条 · 已知检测缺口 3 条。

**需要解释的行**：

- `CT-05`：结构上无法检出（见缺口说明）　**已知缺口**：G1 的实现只断言 result.json 自己的 `case_id` 非空，**不与 case.json 对照**；对照承诺只写在 OUTPUT_CONTRACT.md §5 的表里。测试者已按人复核清单覆盖，但脚本门不拦——如实记为缺口。
- `ST-01`：结构上无法检出（见缺口说明）　**已知缺口**：静态产物校验器看不到「上一次运行的真实状态」，无法区分伪造与真 completed；本行如实记为**检测能力缺口**，不假装已覆盖。
- `ST-02`：结构上无法检出（见缺口说明）　**已知缺口**：清空 uncertainty 后，产物自身仍是自洽的（status=partial 与 evidence 缺口一致），静态校验器没有「应有的 uncertainty」基线可比对 ⇒ 记为**检测能力缺口**。

> 生成命令：`python "$SKILL_DIR/scripts/fault_inject.py" --out <报告目录> --emit-matrix <矩阵文件> --work <包外沙箱>`；协议 `fault-inject/1.0`；Python 3.13.9；Windows-11-10.0.22621-SP0。
<!-- MATRIX-END -->

---

## 4. 这一轮注入**改掉了什么**（逐条点名，可被 diff 复核）

先说结论：**R2 起点（未注入演练之前）的包在这套注入下会暴露 4 类真实缺陷**。它们不是
"文档没写"，而是**文档承诺了、代码没做到**——这正是失败注入的意义。修复全部是
**纯增量**：不改任何 CLI 参数名/默认值/退出码语义，健康路径的行为逐字节不变。

改动总量（`diff -u` 统计，对基线 `final/ppt-c7b80f0d/`）：

```
scripts/main.py     +109 / −19   （542 → 633 行）
scripts/deckgen.py  + 29 / − 4   （650 → 675 行）
其余 9 个 scripts/*.py：逐字节不变（cmp 通过）
```

| 修复 | 文件 · 改动锚点（`diff -u` hunk） | 增 / 删（含注释行） | 真实缺陷（修复前**实测**） | 理由（引用文档原文） |
|-|-|-|-|-|
| `R2-FIX-01` | `main.py` `@@ -46` 导入块；`@@ -223`/`@@ -242`/`@@ -299` 三处 `deckgen is not None` 守卫；`@@ -421` `_run_meta` 字体探测 | +29 / −6 | 缺 `python-pptx`（DP-01）时 `import deckgen`、缺 `Pillow`（DP-02）时 `import preview` 在**模块级**抛 `ImportError`：整个进程崩溃、exit 1、**连 result.json 都没有**（DP-02 还顺带说明：python-pptx 自己依赖 Pillow，所以"只缺 Pillow"在现实中就是"渲染栈整体缺失"） | `failure-modes.md` §2.3："`python-pptx` 缺失 ⇒ `deck` 为 `null`，状态 `partial`/`failed`，如实说明——**不生成假文件**"。崩溃不是"如实说明"，是**连说明都没有** |
| `R2-FIX-02` | `main.py` `@@ -308` 预览块；`@@ -335` 状态阶梯 | +12 / −0 | 预览渲染失败时只追加一条 uncertainty，`status` 仍报 `completed` | 同 §2.3："`Pillow` ⇒ 预览渲染失败：`previews = []`，**状态降级并说明**" |
| `R2-FIX-03` | `main.py` `@@ -403` 调用点、`@@ -460` 签名、`@@ -471` `self_check` 主体 | +15 / −5 | **无 `--spec` 且无 `--demo`** 时：`exit 0` + `self_check.ok=true` + `status=partial` + `deck=null` —— 一次"什么都没交付"的运行却报成功（IN-05）；且 `export_check` 的 import 失败会让 `self_check` 自己崩 | 交付门的意义就是拦住"没有可交付物"的运行。退出码语义**未变**：仍是 0 = 自检无 error / 1 = 自检有 error（新增的只是"无 deck 记入 problems"） |
| `R2-FIX-03b` | `main.py` `@@ -342` | +6 / −0 | 同上的状态词：无 deck 时只写 `partial` | `OUTPUT_CONTRACT.md` §3：`failed` = "**无法产出可交付物**"。没有 deck 就是没有可交付物 |
| `R2-FIX-04` | `main.py` `apply_output_contract` `@@ -76` + `@@ -103` | +13 / −1 | `output_contract` 是**形态④（字段清单 list）**或案例**根本不声明**时，`title`/`main_claim`/`slides`/`render_state`/`notes_separated` 不落顶层 ⇒ `check_contract` 缺字段 ⇒ main.py exit 1（CT-02） | `OUTPUT_CONTRACT.md` §2 末句："本包自带最小契约：`output_contract` 缺省时**按 §1 顶层结构输出**"。四种形态是**并列**的，不能只有 dict 形态可用 |
| `R2-FIX-05` | `deckgen.py` `open_adapted_presentation` `@@ -197` | +15 / −1 | 模板"存在但打不开"（文本改名 `.pptx` / 0 字节 / 半截 zip）时 `build_deck` 直接返回 `file=None` ⇒ **整个 deck 没了**，`deck.template.error` 也没人写（TP-02/03/05） | `failure-modes.md` §2.2："模板损坏 / 老式 `.ppt`（`Presentation()` 抛错）⇒ **回退内置版式**；绝不改写 master 与页脚"。而且"没打开"恰好是最强的"没碰 master"证明 |
| `R2-FIX-08` | `deckgen.py` `_fill_body_placeholder` `@@ -239`/`@@ -254`、调用点 `@@ -525` | +14 / −3 | 图文同页（`layout_hint="figure"` → `Picture with Caption`）时，页级 bullets 被写进 **idx 1 的图片占位符**，随后插图把它覆盖 ⇒ 该页文字从幻灯片 XML 里**彻底消失**，且没有任何字段记录这次丢失（题集 G1 实测：`90.8`/`88.6` 两个透射率不见了） | 这是**静默内容丢失**，比任何崩溃都危险：产物能被正常打开、导出检查全绿。修法：跳过图片占位符，图文同页时正文改走左半幅文本框 |
| `R2-FIX-06` | `main.py` `@@ -242`/`@@ -267`/`@@ -335` | +12 / −0 | 模板损坏并回退后 `status` 仍报 `completed` | `OUTPUT_CONTRACT.md` §3 把"**模板回退**"列在 `partial` 的触发条件里。但"案例没给模板 / 模板文件不存在"是文档定义的**正常分支**——两者必须分开：损坏回退 ⇒ `partial`，缺席回退 ⇒ `completed` |
| `R2-FIX-07` | `main.py` `@@ -223` spec 加载块 | +23 / −6 | `--spec` 是损坏 JSON 时 `json.load` 抛 `JSONDecodeError`，**直接终止进程、无产物**（IN-06） | 与 IN-02（case.json 损坏 ⇒ exit 3 + 仍写 `status=failed` 的 result.json）**不对称**：同类输入异常应走同一条"降级 + 记录 + 仍写产物"的路 |

**复现方式（可被 diff 复核）**：把 `scripts/main.py` 与 `scripts/deckgen.py` 回退到
基线版本（`final/ppt-c7b80f0d/scripts/`），再按 §1 跑一遍注入 —— DP-01、DP-02、IN-05、
IN-06、TP-02、TP-03、TP-05、CT-02 这 8 条会立刻翻红（4 条崩溃/无产物、3 条"deck 整个丢失"、
1 条契约缺字段 exit 1）。修复后即 §3 的 0 静默失败 / 0 口径不一致 / 19-19 恢复成功。

**为什么这些修复算"纯增量"而不是重写**：

- 所有 `try/except`、`is not None` 守卫、`setdefault` 都**只在异常路径上生效**；
  健康路径（材料可读 + 方案可读 + `python-pptx`/`Pillow` 在场）的返回值与调用序列不变；
- **CLI 参数名、默认值、文档化的退出码语义一个都没改**；
- 唯一新增的函数参数是 `self_check(result, out_dir, demo=False)`（模块内部函数，
  默认值保证旧调用方式仍然合法）；
- 修完以后 §3 的基线对照仍是 `exit 0 / completed / 8 页 / 19 顶层字段 / 7 预览 / 0 uncertainty`，
  与修复前逐项相同。

---

## 5. 怎么读这张表（给复核者的三句话）

1. **看"静默失败"列**。它全为"否"才是这个包敢说自己"可靠"的前提；任何一格"是"
   都意味着一次"坏了但说自己没事"的运行。
2. **看"实测 status"与"实测退出码"列**。退出码是给流水线的，status 是给合同读者的，
   两者必须同时可信：`exit 3 + status=failed`（case 不可解析）与 `exit 0 + completed`
   （健康基线）之间的每一条，都在表里有自己的行。
> **互补的第二个盲区**：失败注入覆盖"**故障形态**"，但覆盖不到"**题材与产物结构**"。
> `references/CASE-SET.md` §3 记录了题集抓到的两个同类问题（其中 G1 就是上表的 R2-FIX-08：
> 页级文字被插图静默覆盖）。两份演练合起来才是完整的可靠性证据。

3. **看"已知缺口"列**。三格写着"是"——那是**如实申报的检测能力边界**（静态产物校验器
   看不到历史状态、G1 不外联 case.json）。我们宁可让缺口可见，也不愿让它变成一次
   静默通过；对应的人工兜底动作见 `references/failure-modes.md` §5。

---

## 6. 如何扩展这套演练（生态贡献：它不只为这一道题而写）

`fault_inject.py` 的注入目录是一张 `injections()` 列表：每条 = 一个真实故障 + 文档口径
期望 + 恢复动作 + 可选结构化探针。给新场景加一条注入只需要：

```python
def my_case(fx, work, fid):
    # fx 里已经有 case.json / materials/ / task.md / spec.json / out/ 的干净夹具
    save_json(fx["spec"], load_json(fx["spec"]) | {"slides": []})
    run = _run(main_argv(fx), _child_env())
    run["probe"] = {"did_not_crash": run["exit_code"] is not None}
    return run, observe(fx["out"], run, ["no slides"])

rows.append(dict(id="XX-01", family="input",
                 injection="把方案改成空 slides",
                 expected="文档口径……",
                 expect=dict(exit=[1], status=["failed"], needles=["no slides"],
                             probe=["did_not_crash"]),
                 fn=my_case, recover=restore))
```

同一套判定（静默失败 / 文档一致性 / 恢复）会自动生效；渲染出的矩阵可以逐条对上
`references/failure-modes.md` 的退出码表。**移植到别的 Skill 时**：把 `SKILL_DIR` 指向
那个包、把 `fixture()` 换成它的最小案例即可——`--skill` 参数就是为此准备的。
