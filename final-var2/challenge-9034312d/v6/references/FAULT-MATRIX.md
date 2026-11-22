# FAULT-MATRIX.md — 四形态故障注入矩阵（全部为实测值）

> 本文件是 `scripts/fault_inject.py` **现场跑出来的结果**，不是设计意图的复述。
> 每一条都做了同一件事：把一个真实的坏条件注入到主流程入口 → 跑 `scripts/main.py`
> （或对产物跑 `scripts/check.py`）→ 只用**机器可读的判决位点**记录发生了什么：
> 退出码、`status`、`uncertainty[].scope`、`verify.ok`、`verify.errors[]/warnings[]`、
> `check.py` 的失败门号、产物清单。
>
> 复跑（在**包外**临时目录里，不会往技能包里写文件）：
>
> ```bash
> OUT=$(mktemp -d)
> python "$SKILL_DIR/scripts/fault_inject.py" --out "$OUT" --json "$OUT/fault-report.json"
> python "$SKILL_DIR/scripts/fault_inject.py" --list        # 只看注入表和期望值
> python "$SKILL_DIR/scripts/fault_inject.py" --only F2-*   # 只跑一类
> ```
>
> `fault_inject.py` 每次注入都把技能根复制成**沙箱副本**再改副本（原包只读），
> 并用 `PYTHONDONTWRITEBYTECODE=1` 调用被测脚本，所以跑完包内不会多出
> `__pycache__`/`.pyc`，也不会改动任何随包文件。

## 0. 这一轮实测的运行环境与规模

| 项 | 值 |
|-|-|
| 探针 | `scripts/fault_inject.py`（本包新增） |
| 解释器 | CPython 3.13.9 · `win32` · Pillow / reportlab / 中文字体均可用 |
| 注入条数 | **32 条**（输入 11 · 模板 8 · 依赖 3 · 契约 10；其中 1 条为不注入的对照行） |
| 期望 vs 实测 | 退出码与期望不符 **0** 条 · 静默判定与期望不符 **0** 条 |
| 静默失败 | 实测 **10** 条（**缺陷型 9 条** + 合理型 1 条） |
| 单条注入耗时 | 0.13–0.71 s（每条都要复制一次技能根沙箱副本，副本约 270 KB） |

### 健康臂（所有注入的对照基准）

| 观测量 | 健康臂实测 |
|-|-|
| 退出码 | 0 |
| `status` | `success` |
| 实体 / 关系 | 6 / 5 |
| 导出件 | pdf, png |
| `verify.ok` | true |
| `uncertainty` 域 | — |
| 产物文件 | evidence.json, figure.pdf, figure.png, figure.svg, layout.json, result.json, verify_report.json |

> 健康臂用的是本探针自带的**合成**案例（`FaultLab` 装置图：物料→阀→反应腔→出料阀→收集瓶），
> 标注为非正式案例。它的作用是给后面每一行一个"没坏的时候是什么样"的参照。

---

## 1. 输入形态（11 条）

| # | 注入什么 | 期望退出码 | 实测退出码 | 实测 `status` | 实测 `uncertainty[].scope` | `check.py` 失败门 | preflight | 静默失败 |
|-|-|-|-|-|-|-|-|-|
| F1-01 | --case <不存在的路径>（文件与目录都不存在） | 2 | 2 | `—` | — | — | n/a | 否 |
| F1-02 | case.json 写成非法 JSON（多一个逗号） | 1 | 1 | `failed` | pipeline | — | 拦住(3) | 否 |
| F1-03 | case.json 内容是 JSON 数组 [] | 1 | 1 | `failed` | pipeline | — | 拦住(3) | 否 |
| F1-04 | case.json 只有 {}, 无实体也无文本 | 3 | 3 | `failed` | relations, rule_violation | — | 拦住(3) | 否 |
| F1-05 | case.json 只给 text 字段（触发文本解构） | 0 | 0 | `success` | relations | — | 放过(0) | 否 |
| F1-06 | 在健康案例里加一条 from=D2 to=NOPE 的关系（D2 另有连线） | 0 | 0 | `success` | — | — | 拦住(1) | **是** |
| F1-07 | 新增一个只有一条断头关系的实体 D5（断头被丢弃后它没有连线） | 0 | 0 | `partial` | orphan_entities | — | 拦住(1) | 否 |
| F1-08 | 两条实体用同一个 id | 0 | 0 | `partial` | orphan_entities | — | 拦住(1) | 否 |
| F1-09 | 对健康案例追加 --merge <不存在的路径> | 1 | 1 | `failed` | pipeline | — | 拦住(3) | 否 |
| F1-10 | 追加 --material <不存在的路径>（材料被引用但读不到） | 0 | 0 | `success` | — | — | 拦住(1) | **是** |
| F1-11 | 显式给一个不存在的 task.md 路径 | 0 | 0 | `success` | — | — | 拦住(1) | **是** |

**三条静默行（F1-06 / F1-10 / F1-11）到底安静在哪：**

- **F1-06**：断头关系被丢弃（`verify.checks.no_dangling=true`），但**不写 `uncertainty`**，
  `status` 仍是 `success`。SKILL.md 的 D3 承诺"丢弃并记入 uncertainty"，实测只留下
  一个**关系条数差**（输入 6 条 → 输出 5 条）。⇒ 文档承诺与实现的缺口，见 §4。
- **F1-10**：`--material` 指到不存在的文件时，`evidence.source_files[]` 少一条，
  其余一切正常 —— 没有告警、没有 uncertainty。**证据条数变少是唯一痕迹。**
- **F1-11**：`--task` 指到不存在的文件时照样出图，`status=success`，无任何标记。
  在官方运行时（`/input/task.md`）这条不会触发；但在"用户自己给路径"的用法下会。

**F1-01 / F1-02 / F1-03 / F1-04 / F1-09 的处置是对的**：输入不可用就干净失败，
分别给退出码 2（无产物）、1（兜底 `failed/result.json`）、3（空壳输入 ⇒ 门拦下）。
这五条说明**输入域的失败分支是硬的**。

---

## 2. 模板 / 资产形态（8 条）

| # | 注入什么 | 期望退出码 | 实测退出码 | 实测 `status` | 实测 `uncertainty[].scope` | `check.py` 失败门 | preflight | 静默失败 |
|-|-|-|-|-|-|-|-|-|
| F2-01 | 追加 --palette <不存在的路径> | 0 | 0 | `success` | — | — | 拦住(3) | **是** |
| F2-02 | --palette 指向写坏的 palette.json | 0 | 0 | `success` | — | — | 拦住(3) | **是** |
| F2-03 | --palette 指向内容为 {} 的文件 | 0 | 0 | `success` | — | — | 放过(0) | 是`*` |
| F2-04 | 追加 --rules <不存在的路径> | 0 | 0 | `success` | — | — | 拦住(3) | **是** |
| F2-05 | --rules 指向写坏的 connection_rules.json | 0 | 0 | `success` | — | — | 拦住(3) | **是** |
| F2-06 | 在沙箱副本里删除 templates/palette.json 后运行 | 0 | 0 | `success` | — | — | 拦住(1) | **是** |
| F2-07 | 在沙箱副本里删除 assets/connection_rules.json 后运行 | 0 | 0 | `success` | — | — | 拦住(1) | **是** |
| F2-08 | 在沙箱副本里删除 scripts/render_svg.py 后运行 | — | 1 | `—` | — | — | 放过(0) | 否 |

> `是*` = 合理型静默（空对象就是"用默认值"的合法写法，不算缺陷）。

**这一族的结论最刺眼，也最有价值：`--rules` / `--palette` 写错时，本包会安静地
"用默认值继续跑"。** 具体表现：

- `--rules <不存在>` / `--rules <坏 JSON>` ⇒ `_load_rules()` 返回 `{}` ⇒
  **连接语义审计整体空转**：`verify.checks.connection_rules` 仍可能是 `true`，
  `status=success`，退出码 0。你交出去的图**没有被审计过，而且看不出来**。
- `--palette <不存在|坏 JSON>` ⇒ 静默回落代码内默认配色，产物无任何标记。
- 这两个容错**本身是设计选择**（对照实验的 C2 条件正是靠 `--rules {}` 构造），
  但"交付时也这样"就是缺陷 —— 所以本包新增了 `scripts/preflight.py`，
  把这两个条件提前变成 error 级 finding（实测退出码 3，见 §3 的 preflight 列）。
- **F2-08 是反面对照**：删掉 `scripts/render_svg.py` 时，`main.py` 在模块级 import
  就崩（`ModuleNotFoundError: No module named 'render_svg'`），退出码 1、无产物、
  无兜底结果。⇒ **代码资产缺失是硬失败，数据资产缺失是静默降级** —— 这个不对称
  值得记住：坏掉的 JSON 比坏掉的代码更难发现。

---

## 3. 依赖形态（3 条）

| # | 注入什么 | 期望退出码 | 实测退出码 | 实测 `status` | 实测 `uncertainty[].scope` | `check.py` 失败门 | preflight | 静默失败 |
|-|-|-|-|-|-|-|-|-|
| F3-01 | PYTHONPATH 前置一个 import 即抛 ImportError 的 PIL 影子模块 | 3 | 3 | `partial` | pdf, png | — | 拦住(1) | 否 |
| F3-02 | PYTHONPATH 前置一个 import 即抛 ImportError 的 reportlab 影子模块 | 0 | 0 | `partial` | pdf | — | 拦住(1) | 否 |
| F3-03 | 把 WINDIR 指向空目录，使 4 条 Windows 候选字体路径全部不存在 | 3 | 3 | `success` | fonts | — | 拦住(1) | 否 |

**三条实测发现（都不是设计时预料到的）：**

1. **没有 Pillow 会把 PDF 一起拖下水**：`reportlab` 内部也 `import PIL`，
   所以影子 PIL 让 PNG/PDF **双双失败** ⇒ 两个导出件都缺失 ⇒ 契约门 G4 失败、
   退出码 3（不是只有 PNG 受影响、退出码 0）。这一条只有在真跑之后才知道，
   已写进 `references/failure-modes.md` 的依赖降级表。
2. **只缺 reportlab 时仍然可以交付**：PNG 在，G4 通过，退出码 0，`status=partial`
   且 `uncertainty[scope=pdf]` 记录在案 —— 这是**正确的诚实降级**。
3. **缺中文字体时 `status` 与退出码不一致**：`status=success`（D14 明确说字体缺失
   不改 status），但 `check.py` 的 G10 把 `scope=fonts` 列为"降级不确定性"，
   于是退出码 3。两个口径冲突，见 §4。

**注入手法说明（可被第三方复核）**：依赖缺失不是靠卸载包模拟的（那会污染环境），
而是用 `PYTHONPATH` 前置一个 `__init__.py` 里 `raise ImportError(...)` 的同名影子包；
字体缺失靠把 `WINDIR` 指向空目录，使 4 条 Windows 候选路径全部落空。
两种手法都**只影响这一次子进程**，跑完即失效。

---

## 4. 契约形态（10 条，含 1 条对照）

| # | 注入什么 | 期望退出码 | 实测退出码 | 实测 `status` | 实测 `uncertainty[].scope` | `check.py` 失败门 | preflight | 静默失败 |
|-|-|-|-|-|-|-|-|-|
| F4-00 | 不注入，直接用主流程跑出来的 result.json 过 check.py | 0 | 0 | `success` | — | — | n/a | — |
| F4-01 | 从 result.json 删掉 output_contract 键 | 1 | 1 | `success` | — | G10, G2, G3, G4, G5, G6 | n/a | 否 |
| F4-02 | 把 output_contract.exports 置为 null | 1 | 1 | `success` | — | G10, G2, G4 | n/a | 否 |
| F4-03 | editable_sources/exports/data_mapping/element_traceability 全部置 [] | 1 | 1 | `success` | — | G10, G3, G4, G5, G6 | n/a | 否 |
| F4-04 | 把 output_contract 换成字符串 "ok" | 1 | 1 | `success` | — | <check.py 未输出可解析 JSON> | n/a | 否 |
| F4-05 | 把 exports[0].path 改成一个不存在的文件名 | 1 | 1 | `success` | — | G10, G4 | n/a | 否 |
| F4-06 | 从 data_mapping 删掉一行 | 1 | 1 | `success` | — | G10, G5 | n/a | 否 |
| F4-07 | 删掉一条 element=arrow-* 的溯源行 | 1 | 1 | `success` | — | G10, G6 | n/a | 否 |
| F4-08 | 把 verify_report.json 的 ok 改成 false，result.json 仍写 success | 1 | 1 | `success` | — | G10, G9 | n/a | 否 |
| F4-09 | 把 result.json 截掉一半 | 1 | 1 | `<不可解析: JSONDecodeError>` | — | G1 | n/a | 否 |

> 契约族的"实测 `status`"一列显示的是**被改坏之前**那份产物里的值（注入本身不动 `status`），
> 有意义的观测量是最后一列的**失败门号**与退出码。

**这一族 9/9 全部被拦下，且门号指得很准**：缺 `output_contract` ⇒ G2+G3+G4+G5+G6；
`exports=null` ⇒ G2+G4；四段置空 ⇒ G3+G4+G5+G6；导出件路径不存在 ⇒ G4；
`data_mapping` 少一行 ⇒ G5；溯源少一条箭头 ⇒ G6；`status` 撒谎 ⇒ G9+G10；
坏 JSON ⇒ G1。**契约门是这套流水线里最硬的一环。**

唯一的粗糙点是 **F4-04**：`output_contract` 类型错（字符串）时，`check.py` 在
`oc.get(...)` 处抛 `AttributeError: 'str' object has no attribute 'get'`，
只留下栈、不给门号与 issue 列表。它**不会假绿**（退出码仍是 1），但错误信息对使用者
不友好。这属于检查器的健壮性缺口，已记入 §5 的已知缺口，本包**未改** `check.py`。

---

## 5. 汇总与逐行说明

| 指标 | 值 |
|-|-|
| `injections` | 32 |
| `controls` | 1 |
| `silent_observed` | 10 |
| `silent_expected` | 10 |
| `silent_defects` | 9 |
| `silent_benign` | 1 |
| `silent_mismatch` | 0 |
| `exit_mismatch` | 0 |
| `preflight_ran` | 21 |
| `preflight_caught` | 18 |
| `preflight_missed_silent_defects` | 0 |

**"静默失败"的判定口径（脚本里写死，可复核）**：故障存在，但下列机器可判信号
**一个都没出现** —— 退出码≠0、`status∈{partial,failed}`、`uncertainty` 非空、
`verify.ok=false`、`verify.errors[]/warnings[]` 非空、`check.py` 退出码≠0。
⇒ "产物看起来完全正常，问题只在人读细节时才看得见"。

**逐行设计与发现说明**（节选自 `fault_inject.py` 的 `_specs()`，脚本里逐条可读）：

| # | 期望行为（文档承诺） | 实测是否一致 |
|-|-|-|
| F1-01 | 立即终止，不猜内容（D1） | 一致：退出码 2、无产物 |
| F1-02 | 兜底写 `status=failed` 的 result.json（D2/D19） | 一致 |
| F1-03 | 类型错也走兜底失败路径 | 一致 |
| F1-04 | 空壳输入诚实降级，不给空图 | 一致：`status=failed`、G3/G9 报失败 |
| F1-05 | 文本解构不降级，但记 `scope=relations`（D3） | 一致 |
| F1-06 | 断头关系丢弃**并记入 uncertainty** | **不一致：静默丢弃**（缺口 A） |
| F1-07 | 丢断头 → 失去全部连接 → 孤儿降级（D5→D6） | 一致：`partial` + `orphan_entities` |
| F1-08 | 重命名保唯一，改名后孤儿触发降级（D7→D6） | 一致 |
| F1-09 | 修正入口给错路径必须干净失败 | 一致：退出码 1、`scope=pipeline` |
| F1-10 | 材料读不到时不伪造，只登记实读文件（D4） | 行为一致，但**无告警**（缺口 B） |
| F1-11 | 任务书读不到时照样出图 | 行为一致，但**无告警**（缺口 C） |
| F2-01/02 | 配色缺失/损坏回落默认值 | 行为一致，但**无告警**（缺口 D） |
| F2-03 | 空对象 = 用默认值（合法） | 一致（合理型静默） |
| F2-04/05 | 规则缺失/损坏 ⇒ 审计空转 | 行为一致，但**无告警**（缺口 E，最危险） |
| F2-06/07 | 包内资产缺失 ⇒ 回落默认 | 行为一致，但**无告警**（缺口 E） |
| F2-08 | 代码资产缺失 ⇒ 硬失败 | 一致：`ModuleNotFoundError`、退出码 1 |
| F3-01 | PNG 失败降级，PDF 不受影响（D12） | **不一致**：reportlab 也依赖 PIL，两个都失败 ⇒ 退出码 3（发现 1） |
| F3-02 | PDF 失败降级，PNG 仍在（D12） | 一致 |
| F3-03 | 字体缺失只记录、不改 status（D14） | status 一致，但 G10 判失败 ⇒ 退出码 3（发现 2） |
| F4-01…09 | 契约缺陷必须被 G 门拦下 | 一致：9/9 拦下，门号准确（F4-04 的呈现方式粗糙） |

### §5.1 三条值得单独记住的实测发现

1. **数据坏掉比代码坏掉更难发现**：删一个 `.py` 是 `ModuleNotFoundError`（响亮），
   写错一个 `.json` 路径是"审计空转 + 全绿"（安静）。交付前必须显式检查
   `--rules` / `--palette` 的**存在性、可解析性与非空性**。
2. **依赖之间会互相牵连**：Pillow 缺失会连带 PDF 一起死（reportlab 内部 import PIL），
   所以"只降级一个导出件"的乐观假设不成立；两个都没了就会触发 G4 失败。
3. **`status` 与退出码不是同一件事**：`status=success` 且退出码 3 是**可能且合理**的
   （已出图但契约门不过）。只看 `status` 会漏掉门失败，只看退出码会误判交付物不可用。

---

## 6. 缺口清单（诚实记录，本包**未**改动任何既有脚本）

> 处理原则：`scripts/main.py` / `check.py` / `layout.py` 等既有脚本的 CLI、默认值、
> 退出码语义**一律不动**（动它们会让已投递的包失去可比性）。因此下面这些缺口
> **不靠改代码消除，而靠 `scripts/preflight.py` 提前拦 + 本文件如实记录**。

| # | 缺口 | 实测证据 | 影响 | 处置 |
|-|-|-|-|-|
| A | 断头关系被静默丢弃，不写 uncertainty（与 D3 的承诺不符） | F1-06 | 非法关系被"自动修好"，看不出来 | preflight `relation-dangling`(warn)；或读 `verify.checks.no_dangling` + 输入/输出关系条数差 |
| B | `--material` 指到不存在的文件时无任何告警 | F1-10 | 证据条数悄悄变少 | preflight `material-missing`(warn) |
| C | `--task` 指到不存在的文件时无任何告警 | F1-11 | 任务书没被读到，图仍照画 | preflight `task-missing`(warn) |
| D | `--palette` 缺失/损坏静默回落默认配色 | F2-01/F2-02 | 交上去的配色可能不是你想要的 | preflight `palette-missing/unparsable` |
| E | `--rules` 缺失/损坏、包内规则资产被删 ⇒ **审计空转且全绿** | F2-04/05/06/07 | 最危险：看起来合规，实际没审 | preflight `rules-missing/unparsable/empty`(error) |
| F | 缺 Pillow 会连带 PDF 失败（reportlab 依赖 PIL） | F3-01 | 两个导出件同时丢失 ⇒ G4 失败 | preflight `--deps` 的 `dep-pillow-missing`(warn) |
| G | 缺字体时 `status=success` 但 G10 判失败（两条口径冲突） | F3-03 | 退出码 3 与 status 不一致，易误读 | 本文件 §5.1 第 3 条明确写出；preflight `dep-cjk-font-missing`(warn) |
| H | `output_contract` 类型错时 `check.py` 抛栈（无门号） | F4-04 | 错误信息不可读，但不假绿 | 待上游修；本包不改 `check.py` |

> 缺口 A–H 全部**不影响正确性结论**（该失败的都失败了，该记录的记录在案），
> 影响的是"人能不能快速看出问题"。把它们列出来，是为了让下一位接手的人不必重跑
> 这 32 条注入才知道边界在哪。

---

## 7. 恢复演练：`scripts/preflight.py` 把 9 条静默缺陷全部提前拦住

`fault_inject.py` 在每条注入**之前**都会跑一次 `scripts/preflight.py`
（同一套输入参数，`--deps` 打开），把它的退出码记进上表的 `preflight` 列：

| preflight 退出码 | 含义 | 本次 32 条注入里的分布 |
|-|-|-|
| 0 | 无 finding（可继续） | 3 条（F1-05 文本解构、F2-03 空 palette 合理型、F2-08 删脚本——闸门只检数据/输入，管不到代码资产） |
| 1 | 只有 warn 级 finding（可继续，但已告警） | 10 条 |
| 3 | 有 error 级 finding（建议先修再跑） | 8 条（F1-02/03/04/09 的输入域 + F2-01/02/04/05 的资产域） |
| n/a | 契约形态（由 `check.py` 负责，不进闸门）+ F1-01（case 本身不存在，闸门无对象可检） | 11 条 |

**关键数字：`preflight_missed_silent_defects = 0`** —— 9 条缺陷型静默行，
`preflight.py` **一条都没放过**（其余 2 条"放过"里，F1-05 不是静默行、
F2-03 是文档化的合法写法）。这正是"失败注入 → 发现静默 → 补一道闸门"的完整闭环：

```
fault_inject.py（32 条注入，发现 9 条静默缺陷）
        │
        ▼
preflight.py（运行前闸门：把静默条件变成 error/warn finding）
        │  0 = 干净 · 1 = 有 warn · 3 = 有 error · 2 = 用法错误
        ▼
main.py（正常出图）→ check.py（交付后验 G1–G10）
```

用法（在正式运行前无脑跑一次即可，它不写产物、不改输入）：

```bash
python "$SKILL_DIR/scripts/preflight.py" --case /input/case.json --task /input/task.md --deps
# 退出码 3 ⇒ 先看 findings 里的 code/action，修完再跑 main.py
```

---

## 8. 这份矩阵证明什么、不证明什么

**能证明**（每条都指向上表某个具体格）：

- 输入域与契约域是**硬的**：11 条输入注入全部按 D1/D2/D19 处置，9 条契约注入
  全部被 G 门拦下并给出准确门号；
- 代码/依赖类缺失会**响亮失败**（`ModuleNotFoundError`、`partial`+`uncertainty`），
  而数据/配置类缺失会**静默降级**（9 条缺陷型静默行集中在 `--rules/--palette/
  --material/--task` 与断头关系上）；
- 这 9 条静默行可以被 `scripts/preflight.py` **全部提前拦下**（本轮实测 0 漏网）；
- 依赖之间存在牵连关系（Pillow ⇄ reportlab），"只坏一个导出件"的假设在实测中不成立。

**不能证明**（不要拿这份矩阵去论证）：

- ❌ 平台正式案例上的得分或稳定性 —— 本轮全部是**合成**注入，与官方 3 个案例无关；
- ❌ "所有可能的故障都覆盖了" —— 32 条是按四形态**枚举出来的样本**，不是穷举；
  未覆盖：磁盘写满、输出目录只读、超长材料、并发重复运行、时区/编码差异、
  平台容器特有的 `/input` 挂载缺失；
- ❌ "静默失败永远不会造成错误交付" —— 恰恰相反：缺口 E 会让一份**没被审计过的图**
  以 `success` 交付出去；本包的对策是闸门 + 文档，不是"算法更聪明"；
- ❌ "退出码 0 就等于没问题" —— 上表有 9 行是退出码 0 + 静默缺陷。
