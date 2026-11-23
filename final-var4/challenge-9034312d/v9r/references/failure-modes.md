# failure-modes.md — 失败模式（四形态实测）+ 决策规则全表 + 决策用例（合并版）


> 本文合并三份同主题材料，**内容不删**：① 按四形态重写的失败模式与实测值（本文件 §1–§8，数字来自 `references/FAULT-MATRIX.md`）；② 决策规则 D1–D20 与状态聚合优先级（附录 A）；③ 27 行失败分支表（附录 B）；④ 20 个可复跑的决策用例（原 `DECISION-CASES.md`，现为附录 C；若你在 `scripts/decision_probe.py` 的注释里看到该路径，指的就是附录 C；由 `scripts/decision_probe.py` 现场合成并观测）。

> 这份文件不写"大概会怎样"，只写**跑过之后是什么样**。每一条都指向
> `references/FAULT-MATRIX.md` 里的具体行号（F1-xx / F2-xx / F3-xx / F4-xx），
> 那一行有注入手法、实测退出码、`status`、`uncertainty[].scope` 与失败门号。
>
> 读法：先看 §1 的速查（我遇到了什么 → 该查哪一条），再看 §2–§5 的分域明细
> （处置动作 + 机器可判位点），最后看 §6 的缺口清单（**本包当前会安静放过什么**）。

## 0. 四个观测位点（任何一次运行都能取到，无需额外工具）

| 位点 | 怎么取 | 它回答 |
|-|-|-|
| **退出码** | `main.py` 的 `$?`：`0`/`1`/`2`/`3` | 这次运行"能不能交付"（`3` = 已出图但契约门不过） |
| **`status`** | `result.json` 的 `status`：`success`/`partial`/`failed` | 交付物自己怎么评价自己 |
| **`uncertainty[].scope`** | `result.json` 的 `uncertainty[]` | 有哪些已知缺口被记录在案（`png`/`pdf`/`fonts`/`sources`/`relations`/`orphan_entities`/`rule_violation`/`ambiguity`/`pipeline`） |
| **`check.py` 的 `gates`** | `check.py <result.json>` 的 `gates`/`issues` | 契约门 G1–G10 哪一关卡了 |

> **三个位点必须一起看**：实测存在 `status=success` 而退出码 `3` 的行（F3-03），
> 也存在 `status=success`、退出码 `0`、但**审计根本没跑**的行（F2-04/F2-05/F2-07）。
> 只看其中任何一个都会得出错误结论。

## 1. 速查：现象 → 查哪条

| 你看到的现象 | 先看 | 一句话处置 |
|-|-|-|
| 退出码 2、stderr 有 `FATAL:`、没有产物 | F1-01 | 路径给错；`--case` 接受 case.json 本体或其所在目录 |
| 退出码 1、只有 `<out>/failed/result.json` | F1-02/F1-03/F1-09 | 输入不可解析，或 `--merge` 路径错；修 JSON 再跑 |
| 退出码 3、`status=failed`、`uncertainty` 有 `relations`+`rule_violation` | F1-04 | 空壳输入（无实体也无文本）；补材料，别指望"空图" |
| 退出码 0 但图里少了箭头，`uncertainty` 却是空的 | **F1-06** | 断头关系被静默丢弃（缺口 A）；比对输入/输出关系条数 |
| 退出码 0、`status=partial`、`scope=orphan_entities` | F1-07/F1-08 | 有实体失去全部连接（断头或 id 重复后改名）；补连接 |
| `status=success` 但 `evidence.source_files[]` 少了一个文件 | **F1-10** | `--material` 指到了不存在的路径（缺口 B） |
| `status=success` 但图里没有任何"任务书"痕迹 | **F1-11** | `--task` 指到了不存在的路径（缺口 C） |
| 配色跟你要的不一样，但什么错都没报 | **F2-01/F2-02/F2-06** | 配色静默回落默认值（缺口 D） |
| `verify.ok=true` 但你心里没底"到底审了没" | **F2-04/F2-05/F2-07** | 规则集为空 ⇒ 审计空转（缺口 E，最危险） |
| 进程直接崩、提示 `ModuleNotFoundError` | F2-08 | 包内脚本被删/没装全；这是**硬失败**，反而好查 |
| `status=partial`、`scope=png` 与 `pdf` 同时出现 | **F3-01** | 缺 Pillow 会连带 PDF 一起失败（reportlab 依赖 PIL） |
| `status=partial`、只有 `scope=pdf` | F3-02 | 只缺 reportlab；PNG 仍在，G4 仍可通过 |
| `status=success` 但退出码 3、`scope=fonts` | **F3-03** | 缺中文字体：D9/D14 不改 `status`，但 G10 判失败（口径冲突） |
| `check.py` 报 G2/G3/G4/G5/G6 | F4-01…F4-07 | 契约四段/文件/映射/溯源有问题；按门号补 |
| `check.py` 报 G9/G10 | F4-08 | `verify` 没全绿却自称 `success`；先修违规，别改 `status` |
| `check.py` 抛 `AttributeError: 'str' object has no attribute 'get'` | **F4-04** | `output_contract` 被写成了字符串（缺口 H）；改回对象 |
| `check.py` 抛 `JSONDecodeError` | F4-09 | `result.json` 被截断/写坏；重跑主流程 |

## 2. 输入形态（F1，11 条）

| 现象 | 根因 | 处置（本包的实际行为） | D# | 实测行 |
|-|-|-|-|-|
| case 文件不存在 | 路径给错 / 挂载失败 | stderr 打 `FATAL:`，退出码 **2**，**不写任何产物** | D1 | F1-01 |
| case.json JSON 语法坏 | 传输截断 / 手工编辑 | 兜底写 `<out>/failed/result.json`，`status=failed`，`scope=pipeline`，退出码 **1** | D2 | F1-02 |
| case.json 顶层是数组/标量 | 上游把列表当对象 | 同上走兜底失败，不把数组当字典用 | D2 | F1-03 |
| 空壳对象（无实体无文本） | 模板没填 | 出图失败但**诚实降级**：`status=failed`，`scope=relations`+`rule_violation`，退出码 **3** | D2 | F1-04 |
| 只有自由文本 | 材料未结构化 | 文本解构 `extraction=text-heuristic`，只串联相邻步骤，记 `scope=relations`，**不降级** | D2 | F1-05 |
| 关系端点不存在（但两端实体还有别的连线） | 解析错 / 材料本身缺 | 丢弃该关系、不画断头；⚠ **不写 uncertainty**（缺口 A），只在 `verify.checks.no_dangling` 留痕 | D3 | F1-06 |
| 断头导致某实体失去全部连接 | 同上 | 先丢断头，再由孤儿触发 `status=partial` + `scope=orphan_entities` | D3→D11 | F1-07 |
| 实体 id 重复 | 同类部件没区分 | 重命名 `<id>_2`；改名后无连接 ⇒ 同样 `partial`+`orphan_entities` | D8→D11 | F1-08 |
| `--merge` 指向不存在的文件 | 修正入口参数错 | 兜底失败：退出码 **1**、`status=failed`、`scope=pipeline` | D2 | F1-09 |
| `--material` 指向不存在的文件 | 材料路径错 | ⚠ **安静继续**：不进 `sources`、不记 uncertainty；唯一痕迹是 `evidence.source_files[]` 少一条 | D4 | F1-10 |
| `--task` 指向不存在的文件 | 任务书路径错 | ⚠ **安静继续**：照样出图，无任何标记 | D2 | F1-11 |

**处置原则**：输入域**不猜内容**。读不到就少登记，绝不补造；能继续就用
`uncertainty` 留痕，不能继续就用非零退出码 + `failed/result.json`。

## 3. 模板 / 资产形态（F2，8 条）

| 现象 | 根因 | 处置（本包的实际行为） | 实测行 |
|-|-|-|-|
| `--palette` 指向不存在的路径 | 参数写错 | ⚠ 静默回落代码内默认配色，退出码 0、无标记 | F2-01 |
| `--palette` 是坏 JSON | 文件损坏 | ⚠ 同上（解析失败按"没有自定义配色"处理） | F2-02 |
| `--palette` 是空对象 `{}` | 有意用默认值 | ✅ **合理**：与内置配色合并，行为不变（属合法写法，不算缺陷） | F2-03 |
| `--rules` 指向不存在的路径 | 参数写错 | ⚠⚠ **审计整体空转**：规则集为空、`status=success`、退出码 0 | F2-04 |
| `--rules` 是坏 JSON | 文件损坏 | ⚠⚠ 同上（最容易"看起来全绿却没审"的一种） | F2-05 |
| 包内 `templates/palette.json` 被删 | 打包漏文件 | ⚠ 静默回落默认配色 | F2-06 |
| 包内 `assets/connection_rules.json` 被删 | 打包漏文件 | ⚠⚠ 审计空转，与 F2-04 同因不同源 | F2-07 |
| 包内 `scripts/render_svg.py` 被删 | 打包漏文件 | ✅ **硬失败**：`ModuleNotFoundError`，退出码 1、无产物、无兜底结果 | F2-08 |

**这一族的结论**：**代码资产缺失是响亮的，数据资产缺失是安静的。**
坏掉的 JSON 比坏掉的 `.py` 难发现得多，因为它不会崩，只会"用默认值继续"。
⇒ 交付前必须显式确认三件事：`--rules` 存在、可解析、`rules[]` 非空；
`--palette` 存在且可解析；包内 `assets/` 与 `templates/` 两个目录都在。
`scripts/preflight.py` 就是用来自动做这三件事的（见 §7）。

## 4. 依赖形态（F3，3 条）

| 现象 | 根因 | 处置（本包的实际行为） | D# | 实测行 |
|-|-|-|-|-|
| 无 Pillow | 环境未装 | PNG 失败 ⇒ `scope=png`；**但 reportlab 内部也 import PIL，PDF 一起失败** ⇒ 两个导出件都缺 ⇒ G4 失败、退出码 **3** | D10 | F3-01 |
| 无 reportlab | 环境未装 | 只 PDF 失败 ⇒ `scope=pdf`、`status=partial`；PNG 仍在，G4 通过、退出码 **0** | D10 | F3-02 |
| 无中文字体 | 容器无 CJK 字体 | `fonts[role=png].found=false` + `scope=fonts`；**`status` 仍为 `success`**（D9），但 `check.py` G10 把它算作降级不确定性 ⇒ 退出码 **3** | D9 | F3-03 |

**三条实测发现**（都在真跑之后才确认，写进 `SKILL.md §4` 与矩阵 §5.1）：

1. **依赖会互相牵连**：Pillow ⇄ reportlab。"只降级一个导出件"是乐观假设，
   实测中 PIL 的缺失会让两个导出件全灭。
2. **`status` 与退出码是两件事**：`status=success` + 退出码 3 是可能且合理的一档
   （已出图、但契约门不过），F3-03 就是这种。
3. **降级要写进 `uncertainty` 才算数**：F3-01/F3-02/F3-03 都把原因写进了
   `uncertainty[].scope`，第三方据此可以复现你的判断；只写在日志里的降级不算。

## 5. 契约形态（F4，10 条）

| 现象 | 根因 | `check.py` 实测报的门 | 处置 | 实测行 |
|-|-|-|-|-|
| `output_contract` 整段缺失 | 老版本产物 / 写盘截断 | G2 G3 G4 G5 G6 G10 | 重跑主流程；缺键立刻暴露 | F4-01 |
| `exports` 为 `null` | 空值当容器 | G2 G4 G10 | 改成 `[]`（四段一律列表，`null` 违规） | F4-02 |
| 四段都是 `[]` | 占位没填 | G3 G4 G5 G6 G10 | 空列表合法但交付物为零 ⇒ 必须真跑出产物 | F4-03 |
| `output_contract` 是字符串 | 类型错 | ⚠ 抛 `AttributeError`（无门号） | 改回对象；这是检查器健壮性缺口（缺口 H） | F4-04 |
| `exports[].path` 指向不存在的文件 | 移动/删除产物 | G4 G10 | 产物与清单必须对齐 | F4-05 |
| `data_mapping` 少一行 | 映射漏填 | G5 G10 | 与实体一一对应 | F4-06 |
| 溯源少一条 `arrow-*` | 只填了实体 | G6 G10 | 实体与箭头都要有 `element_traceability` 行 | F4-07 |
| `verify_report.ok=false` 但 `status=success` | 状态撒谎 | G9 G10 | **先修违规**，不要改 `status` | F4-08 |
| `result.json` 不可解析 | 写盘截断 | G1 | 重跑；不要手改 JSON | F4-09 |

**契约族实测 9/9 全部被拦下，且门号与注入对得上** —— 这是整套流水线里最硬的一环。
唯一的粗糙点是 F4-04（类型错时抛栈而不是给门号）。

## 6. 缺口清单：本包当前**会安静放过**的 9 条

> 处理原则：既有脚本的 CLI、默认值、退出码语义**一律不改**（改了就与已投递的包
> 失去可比性）。所以这些缺口不靠改代码消除，而靠 **`scripts/preflight.py` 提前拦**
> 与 **`references/FAULT-MATRIX.md` 如实记录**。

| 缺口 | 注入行 | 静默表现 | 闸门能否拦住 | 人手复核办法 |
|-|-|-|-|-|
| A 断头关系不留痕 | F1-06 | 关系被丢弃但不写 uncertainty（D3 承诺了要写） | ✅ warn `relation-dangling` | 比对输入/输出关系条数；看 `verify.checks.no_dangling` |
| B 材料缺失无告警 | F1-10 | `source_files[]` 少一条 | ✅ warn `material-missing` | 核对 `evidence.source_files[]` 与你要给的材料清单 |
| C 任务书缺失无告警 | F1-11 | 照样出图 | ✅ warn `task-missing` | 核对 `result.json.sources` 里有没有 `role=task` |
| D 配色静默回落 | F2-01/F2-02/F2-06 | 用默认配色 | ✅ error/warn `palette-*` | 看 `output_contract.editable_sources[]` 的配色来源，或直接看 PNG |
| E **审计整段空转** | F2-04/F2-05/F2-07 | `verify.ok=true` 但一条规则都没跑 | ✅ error `rules-missing/unparsable/empty` | 核对 `--rules` 是否存在且 `rules[]` 非空 |
| F Pillow 连带 PDF | F3-01 | 两个导出件同时丢 ⇒ G4 失败 | ✅ warn `dep-pillow-missing` | 看 `output_contract.exports[]` 的 `kind` 列表 |
| G 字体缺失时 status/退出码冲突 | F3-03 | `status=success` + 退出码 3 | ✅ warn `dep-cjk-font-missing` | 同时读 `status` 与 `gates_false`，别只看一个 |
| H 契约类型错时抛栈 | F4-04 | 退出码非 0，但无门号 | ➖（属 `check.py` 领域） | 看 stderr 最后一行 |
| I 代码资产缺失 | F2-08 | 硬失败（响亮） | ➖（闸门只检数据/输入） | `ModuleNotFoundError` 一眼可见 |

## 7. 恢复路径：三道门，按顺序过

```
① preflight.py（运行前）   输入/结构/资产/依赖 ── 0 干净 / 1 warn / 3 error
        │  提前拦掉 §6 的 A–G 七类静默缺口（实测 9/9，0 漏网）
        ▼
② main.py（运行中）        证据→布图→渲染→审计→契约 ── 0 / 1 / 2 / 3
        │  自带 D1–D12 处置 + uncertainty 记账
        ▼
③ check.py（运行后）        G1–G10 契约门 ── 0 全过 / 1 有 issue
```

三门的**分工不是重复**：闸门管"进去的东西对不对"，主流程管"画出来的对不对"，
契约门管"出来交的东西全不全"。任何一门报错都**不要**去改门，改的是它指向的输入。

## 8. 资源形态与打包门（R1–R6）—— 预检会直接拒包，必须包内自查

> 依据题面英文契约原文：*Skill resources: at most 50 UTF-8 text files, 500KB each and
> 2MB total, no symlinks. Runtime artifacts may be binary and are retained independently
> of final JSON validity.* 违反形态门的包在预检阶段就被判「不支持的文件类型」或
> 「文件数量超限」，**与算法质量无关**。

| 门 | 规则 | 处置 | 检查方式 |
|-|-|-|-|
| R1 文本白名单 | 只允许 `.md .py .json .txt .csv .yaml .yml`（小写）；**不得**有 `.pdf/.png/.jpg/.pptx/.svg/.jsonl/.zip/.pyc/.ttf` | 二进制/矢量资源一律删除，改为运行时生成（本包的 `figure.svg/png/pdf` 即如此） | 按扩展名扫描 |
| R2 文件数 | ≤ **50**（按 `outputs/` 计；平台会把同一份复制到 `results/`，同样 ≤50） | 合并冗余文档；示例产物只留**文本类** | 数文件 |
| R3 体积 | 单文件 ≤ **500KB**，合计 ≤ **2MB** | 精简大 JSON；不要把整套运行产物塞进包 | 统计字节 |
| R4 符号链接 | 不允许 `symlink` | 复制实体文件，不要用链接"省空间" | `os.path.islink` |
| R5 无 `__pycache__` | 不得有 `__pycache__/`、`*.pyc` | 所有脚本首部置 `sys.dont_write_bytecode = True`；**冒烟/自测后务必删掉脚本目录下的 `__pycache__`** | 扫描 |
| R6 无本机绝对路径 | 包内文本不得含本机绝对路径（盘符 + 反斜杠、`/Users/…`、UNC 前缀） | 改成相对路径或运行时值；**字体探测候选路径**属跨平台探测逻辑，写正斜杠形式、Windows 根优先取 `%WINDIR%`，可保留但要在交付说明里点名 | `grep -rnE '(^\|[^A-Za-z])[A-Za-z]:[\\/]' <包目录>` 应无输出（`https://` 不会被命中）；`python validate_pkg.py <包目录>` 应 PASS |

| 常见触发 | 现象 | 处置 |
|-|-|-|
| 包内放了 `figure.pdf` / `*.png` 预览 | 预检报 `unsupported Skill resource: …` | 删；改为运行时由 `export_preview.py` 生成 |
| 示例目录把整套运行产物都带上 | 预检报「文件数量 N 超过上限 50」 | 只留文本类证据（`evidence/layout/verify_report/result`），其余靠复跑 |
| 自测没清 `__pycache__` | 形态门 FAIL（R5） | 删 `scripts/__pycache__/`；脚本已置 `dont_write_bytecode` 防复现 |
| 文档里粘了本机临时输出目录 | 形态门 FAIL（R6），并会误导回放 Agent | 一律写 `<TMP>`/`$SKILL_DIR`/`/input`/`/app/output` 这类占位与运行时路径 |

---

## 附录 A · 决策规则全表（D1–D20，按失败域分组）与状态聚合优先级

> 摘自已归档的决策显性化版 `failure-modes.md`：每条给出**触发 → 动作 → 失败时的降级 → 证据位点**四列。与 §2–§5 的四形态实测表互为补充：§2–§5 说"实测是什么"，本附录说"应当怎么判"。





---

## 附录 B · 失败分支表（27 行："你看到什么 → 后果 → 去哪里核对"）



---

## 附录 C · 20 个可复跑的决策用例（原 `DECISION-CASES.md`；期望判决 vs 实测观测值）

> **文件名变更说明**：`scripts/decision_probe.py` 的注释里仍写着
> `references/DECISION-CASES.md`，那指的是本附录。脚本注释不动是为了保持 R1 产物逐字节不变。

> 复跑：`python "$SKILL_DIR/scripts/decision_probe.py" --out <临时目录> --json <临时目录>/obs.json`。表里的"退出码"是被测流水线 `main.py` 的退出码，不是探针的。

> 本文件是 SKILL.md §7 失败分支表的**可执行伴生件**：把「异常 → 处置」写成 20 个
> 可现场合成的输入形态，逐条给出**期望判决**与**实测观测值**。
> 复跑方式（一次跑完 20 个用例，只做观测，不在技能包内落任何文件）：
>
> ```bash
> python "$SKILL_DIR/scripts/decision_probe.py" --out <临时目录> --json <临时目录>/obs.json
> ```
>
> 退出码 0 = 探针跑完。表里的「退出码」是被测流水线 `main.py` 的退出码，不是探针的。
> 观测口径：`status` / `verify.ok` / `verify.errors[].rule` / `verify.warnings[].rule` /
> `uncertainty[].scope` / `check.py` 报出的失败门号 —— 这六项任何一次运行都能取到，
> 所以判决可被第三方逐条复核。

## 0. 观测值汇总表（实跑记录）

环境：Windows，Python 3.13.9，Pillow/reportlab 均可用（因此 PNG/PDF 均成功生成）；
`--out` 指向包外临时目录；跑完观测表 20/20 与本节期望一致（`summary.on_table = 20`，
`deviations = []`）。

| 用例 | 输入形态 | 规则 | 退出码 | `status` | `verify.ok` | `verify.errors` | `verify.warnings` | `uncertainty[].scope` | 失败门 |
|-|-|-|-|-|-|-|-|-|-|
| D01 | `case.json` 不存在 | D1 | **2** | —（无产物） | — | — | — | — | — |
| D02 | `case.json` JSON 语法坏 | D2/D19 | **1** | `failed` | — | — | — | `pipeline` | G3 G4 G9 |
| D03 | 结构化 `entities`、无 `relations` | D3 | **0** | `success` | true | — | — | — | — |
| D04 | 只有 `text`，无结构化实体 | D3 | **0** | `success` | true | — | — | `relations` | — |
| D05 | 一条关系端点不存在 | D5→D6 | **0** | `partial` | true | — | — | `orphan_entities` | — |
| D06 | 全部关系端点不存在 | D5→顺序兜底 | **0** | `success` | true | — | — | — | — |
| D07 | 实体缺 `source` | D11/D15 | **3** | `partial` | false | — | — | `sources` `rule_violation` | G9 |
| D08 | 实体 id 重复 | D7→D6 | **0** | `partial` | true | — | — | `orphan_entities` | — |
| D09 | 类别与关系种类均非法 | D9 | **0** | `success` | true | — | — | — | — |
| D10 | 画布 60×40 mm、12 个实体 | D8 | **0** | `success` | true | — | — | — | — |
| D11 | `--rules` 指向空对象文件 | D9/D10 | **0** | `success` | true | — | — | — | — |
| D12 | `--rules` 指向不存在的路径 | D9/D10 | **0** | `success` | true | — | — | — | — |
| D13 | 装置图 `flow` 终点是 `material` | D18 | **3** | `partial` | false | `apparatus-flow-into-material` | — | `rule_violation` | G9 |
| D14 | 装置图产物继续流向下一装置 | D10 | **0** | `success` | true | — | `product-terminal` | — | — |
| D15 | `sequence` 连到 `material` | D18 | **3** | `partial` | false | `sequence-step-only` | — | `rule_violation` | G9 |
| D16 | `connect` 两端都不是结构件 | D18 | **3** | `partial` | false | `connect-structural` | — | `rule_violation` | G9 |
| D17 | 自环关系 | D18 | **3** | `partial` | false | `no-self-loop` | — | `rule_violation` | G9 |
| D18 | `recycle` 回流 | D10 | **0** | `success` | true | — | `recycle-review` | — | — |
| D19 | 空壳 case（无实体无文本） | D3/D18 | **3** | `failed` | false | — | — | `relations` `rule_violation` | G3 G9 |
| D20 | `figure_type` 为非法值 | D9 | **0** | `success` | true | — | — | — | — |

## 1. 分域读法

### 1.1 输入域（D01–D04）

- **D01** 是最干净的失败：没有产物、退出码 2、stderr 一行 `FATAL:`。它**不会**写
  `result.json` —— 输入都不存在，就没有可声明的结果。
- **D02** 走兜底：`main()` 捕获异常后写 `<out>/failed/result.json`，退出码 1。
  注意它的 `uncertainty[].scope` 是 `pipeline`，且 `check.py` 会报 G3/G4/G9 ——
  **这是预期的**：兜底结果本来就不含图稿，门报失败恰恰说明门是有效的。
- **D03** 与 **D04** 的差别只在 `extraction`（结构化 vs `text-heuristic`）与
  是否记 `uncertainty[scope=relations]`；两者都可能是 `success`，因为
  「缺结构化数据」不是交付缺陷，而是需要 Agent 复核的信号（CP1）。
- **D04** 的 `status` 是 `success` 而非 `partial`，这一条容易误判：**文本解构本身不降级**。
  真正触发降级的是它之后的孤儿实体（见 D05）。

### 1.2 连接正确性域（D05–D08、D13–D18）

- **D05**：断头关系被丢弃（`no_dangling=true`），但被丢弃后 `E3` 失去全部连接 →
  按 D6 记 `orphan_entities` → `partial`。**这是两条规则串联生效的样本。**
- **D06**：三条关系全被丢弃 → 关系集合为空 → 模型改走顺序兜底（`source=text:order`）
  → 不产生孤儿实体 → **`success` 且不报错**。这是本包**已知的"安静"缺陷**，
  SKILL.md §10 第 1 条与 failure-modes.md §4 都点名了；复核办法：看
  `relations[].source` 是否全为 `text:order`、以及输入关系条数与输出关系条数之差。
- **D08**：重复 id 被重命名为 `E1_2`，重命名后该实体无连接 → D6 → `partial`。
- **D13/D15/D16/D17**：四条 error 级规则违规 ∶ 退出码 3、`status=partial`、
  `verify.ok=false`、`uncertainty[scope=rule_violation]`、`check.py` 在 G9 报失败。
  **五处证据同时出现**，所以"违规被拦截"不是自述。
- **D14/D18**：两条 warn 级规则只写 `verify.warnings`，`status` 保持 `success`。
  **warn 永不降级**是 §4 状态聚合优先级的显式约定。

### 1.3 模板与依赖域（D09–D12）

- **D09**：非法类别 `步骤步骤` 与非法关系 `莫名其妙关系` 被静默归一化（→ `step`/`flow`），
  随后词表审计自然通过。**安静缺陷 #2**：原始非法值不留痕，复核办法见 SKILL.md §10 第 2 条。
- **D11/D12**：`--rules` 指向空文件或不存在的路径时，审计按"无规则"通过，
  退出码仍为 0。**安静缺陷 #3**：看起来全绿、实际没审。
- D10（画布 60×40 mm 装 12 个实体）不降级：等比缩放居中，原请求值留在
  `canvas.requested`，实际值在 `canvas.width_mm/height_mm`，差值是既定行为不是丢数据。

### 1.4 契约与状态域（D07、D19）

- **D07** 是"契约门能拦住不完整交付"的样本：实体缺 `source` 本不降级（D11），
  但它同时让 `verify.checks.entity_source_coverage=false` 连带拖垮
  `verify.ok`（`all = 无 issues 且无 errors`），于是被 G9 拦下、退出码 3。
  **处置顺序很重要**：先补 `source`（这是真问题），再重跑，而不是去改门。
- **D19**：空壳输入走到 `verify.ok=false` + 无 SVG，G3/G9 报失败，
  最终 `status=failed`、退出码 3。注意 `verify.errors` 为空而 `uncertainty` 里有
  `rule_violation` —— 这是 `main.py` 对"校验未通过"的统一记账口径；读表时不要
  只看 `errors` 就下结论。

## 2. 与 SKILL.md §7 失败分支表的对应

SKILL.md §7 的 27 行里，D01–D20 覆盖其中 20 行；剩下 7 行需要在探针之外单独构造，
原因与做法如下（**不放进 decision_probe.py，避免伪造依赖状态**）：

| SKILL.md §7 行 | 为什么不在探针里 | 怎么验 |
|-|-|-|
| 19 无 Pillow | 需要卸载/屏蔽依赖，探针不应改环境 | 在隔离环境里 `pip uninstall pillow` 后重跑 D03，期望 `status=partial` + `uncertainty[scope=png]` |
| 20 无 reportlab | 同上 | 同上，期望 `uncertainty[scope=pdf]` |
| 21 无中文字体 | 需要无字体环境 | 容器里不装 CJK 字体重跑，期望 `fonts[role=png].found=false` |
| 24 `verify.ok=false` 却报 `success` | 这是"门是否有效"的反向检查 | 手工把某次 `result.json` 的 `status` 改成 `success` 再跑 `check.py`，期望 G10 报失败 |
| 25 `--merge` 引入非法端点 | 需要两步（先跑再合并） | 先跑 D03，再用一份 `{"relations":[{"id":"R9","from":"E1","to":"NOPE"}]}` 重跑，期望 G6/G7/G9 报失败 |
| 26 人工改 SVG 未记录 | 需要人工编辑动作 | 手改 `figure.svg` 后比对 `checksum` 与 `change_record` |
| 27 未预期异常 | D02/D19 已覆盖同类路径 | 见 D02 |

## 3. 这份用例集的用途（不只是自测）

1. **回归**：任何对 `model.py`/`svg_verify.py`/`check.py` 的改动，跑一遍探针就知道
   20 条判决有没有被改坏（`verdict` 列会直接标出偏离项）。
2. **交接**：新接手的人不用读完整代码，读这张表就知道"什么输入会得到什么状态"。
3. **复用**：这 20 个输入形态本身就是一份**绘图类 Skill 的异常语料**，
   可以直接搬到同类题（装置图/流程图/路线图/机制图）上做交叉验证。
4. **诚实边界**：D06/D09/D11/D12 四行记录的是**本包当前会安静放过的缺陷**。
   把它们写进用例集，是为了让下一次改进有明确靶子，而不是假装满分。

## 4. 如果你的观测与本节不符

按这个顺序查，别先怀疑探针：

1. 退出码不同 → 先看 stderr 最后一行。`2` = 输入路径没给对；`1` = 流水线抛异常。
2. 退出码对但 `status` 不同 → 按 SKILL.md §4 的状态聚合优先级逐条比对，
   看是 D12（导出失败）、D18（error 违规）、还是 D6（孤儿实体）先命中。
3. `status` 对但 `errors` 不同 → 检查你的 `--rules`（D11/D12 会让审计为空转）。
   默认规则资产在 `assets/connection_rules.json`；若你传了自定义文件，
   用 `python -c "import json;print(json.load(open('<你的rules>',encoding='utf-8')))"` 看内容。
4. 全都对但 `gates_false` 不同 → 那多半是环境差异（缺 Pillow/reportlab 会让 G4 失败），
   不是判决差异；G 门报的失败项本身就是证据。

---

> ## 合并迁入 · 原 `references/CASE-SET.md`（本包 R3 变体 v9 合并；**内容逐字保留**）
>
> **为什么合并**：泛化失效边界是失败模式的一类（输入退化），且平台对 Skill 资源有「≤50 个 UTF-8 文本文件」的硬门。
> 为守住该门，本包把 `references/CASE-SET.md` 全文并入本文件尾部（不改一字、不删一段）。
> **路径更正**：无脚本 docstring 指向 `references/CASE-SET.md`（`scripts/case_set_run.py` 读的是机器可读的 `references/case-set.json`，仍在包内），因此本次合并不产生悬空路径。

## 并入全文 · `references/CASE-SET.md`

# CASE-SET.md — 题集（4 个合成案例）与逐案实测结果

> 本文件是"多案例泛化"这一轴的正面材料：**4 个案例、4 次真跑、每个案例给出输入形态、
> 期望产出结构、可接受区间、难度层、实测值**，最后如实写明**泛化到哪里会失效**。
> 全部数字来自 `scripts/case_set_run.py` 的一次现场运行（命令见 §1），没有任何估计值。
>
> ⚠ 所有案例都是**合成案例**：材料为演示接口而虚构，与组织方固定案例无关；
> 正式案例、白板与评分由平台提供/执行。本文件**不预测任何分数**。

## 0. 题集一览（本版新增 2 个不同题材 + 基线的 2 个示例作锚点）

| # | case_id | 题材 | 图类 | 难度层 | 实体/关系 | 它在考什么 |
|-|-|-|-|-|-|-|
| **C-1** | `mbr-wastewater-flow-01` | 环境工程 · 市政污水处理 | `flow` | 中 | 14 / 14 | **物质流向**：分流、合流、回流、两条废料支路、出水两路 |
| **C-2** | `dtms-stage-route-01` | 分子生物学 · CRISPRi 全基因组筛选 | `route` | 高 | 18 / 18 | **阶段路线**：4 阶段 + 2 里程碑 + 依赖方向 + 返工回流 + 编号逐条对照 |
| C-3 | `demo-biotech-route-01` | 分子生物学 · CRISPR 文库药筛 | `route` | 低 | 10 / 9 | 最简线性主链（基线自带示例，作低难度锚点） |
| C-4 | `apparatus-spec-01` | 实验装置 · 冷冻干燥机 | `apparatus` | 低 | 6 / 5 | 单层装配 + 三桶布局 + 装置图特有限制（基线自带示例） |

C-1 / C-2 是**本版新增**的两个不同题材案例，落在 `examples/cases/`；
C-3 / C-4 是基线自带示例，登记进题集以覆盖"最简形态"与"装置图"两个锚点
（`apparatus` 图类不覆盖的话，装置图特有的 `apparatus-flow-into-material` 与
`product-terminal` 两条规则就没有案例去验）。

## 1. 怎么复跑（三条命令）

```bash
# ① 只列题集与期望（不执行）
python "$SKILL_DIR/scripts/case_set_run.py" --list

# ② 逐案跑 + 与期望结构比对（退出码 0 = 全 PASS）
python "$SKILL_DIR/scripts/case_set_run.py" --out <临时目录> --json <临时目录>/report.json

# ③ 追加"泛化探针"：把每个案例压扁成只留 text 字段再跑一遍，测结构化信息消失后的损失
python "$SKILL_DIR/scripts/case_set_run.py" --text-only --out <临时目录>
```

脚本行为：题集成员以 `references/case-set.json` 的 `case_path` 登记项为准
（没有登记表时才扫描 `--cases-root` 下的子目录）；每个案例跑 `main.py` 并收集
退出码 / `status` / 实体关系数 / `verify.ok` / `errors[]` / `warnings[]` /
`spec_sha16` / PNG·PDF 字节 / 失败门号，再与该案的期望逐项比对。

**期望写成"区间 + 不变量"而不是定值**，理由：合法改动（例如按材料补一条真实连接）
不该被判 FAIL，但**结构性丢失**（少一条回流、少一个终点、方向反了）必须被判 FAIL。

## 2. C-1 · 市政污水 MBR 工段物质流向图（`flow`，难度 中）

**输入**：`examples/cases/mbr-wastewater-flow-01/{case.json,task.md}`
（结构化 14 实体 / 14 关系；每个实体带 `source` 指向 `task.md §1.1–§3.3`）。

**期望产出结构**：

| 产物 | 期望 |
|-|-|
| `figure.svg` | 分层（5 层 `layer:*`），14 个 `entity-*` 组，14 条 `arrow-*`；回流 `R8` 为虚线 |
| `evidence.json` | 28 条证据（14 实体 + 14 关系），`locator` 指向 `task.md §…` |
| `result.json` | `output_contract` 四段齐全；`entities` 14、`relations` 14；`uncertainty` 为空 |
| `figure.png` / `figure.pdf` | 非空；PNG 尺寸 == 画布 × DPI |

**可接受区间**：实体 **14–18**、关系 **14–20**；`status=success`；`verify.ok=true`；
退出码 **0**；**允许** `recycle-review` 告警（回流存在时必须人工复核，属设计行为）；
**禁止** error 级违规（`no-self-loop` / `sequence-step-only` / `connect-structural` /
`apparatus-flow-into-material`）。

**不变量**（缺一即判不合格）：两条废料支路（栅渣、剩余污泥）存在且为终点；回流
方向 `D5→D4` 且 `kind=recycle`；出水分两路（`D8→P1`、`D8→P2`）；14 个实体全带 `source`。

**实测**（结构化输入）：

| 观测量 | 实测 |
|-|-|
| 退出码 / `status` | **0** / `success` |
| 实体 / 关系 | **14 / 14**（与输入一致，无丢弃） |
| `verify.ok` / 失败门 | **true** / 无 |
| 规则告警 | `recycle-review` ×1（预期内） |
| `uncertainty` 域 | 空 |
| `spec_sha16` | `5b65c6612f7714e0` |
| `figure.png` / `figure.pdf` | 53 567 B / 5 149 B |
| 单轮耗时 | 0.58 s |

## 3. C-2 · CRISPRi 全基因组筛选四阶段技术路线图（`route`，难度 高）

**输入**：`examples/cases/dtms-stage-route-01/{case.json,task.md}`
（结构化 18 实体 / 18 关系；14 `step` + 2 `milestone` + 1 `product` + 1 `data`）。

**期望产出结构**：

| 产物 | 期望 |
|-|-|
| `figure.svg` | 4 个阶段分列；步骤编号 1..N 连续；2 个里程碑单独成组（不与步骤混排） |
| `evidence.json` | 36 条证据；`locator` 指向 `task.md §2.1–§5.3` |
| `result.json` | `entities` 18、`relations` 18；`verify.checks.numbering_continuous=true` |
| `figure.png` / `figure.pdf` | 非空；PNG 尺寸 == 画布 × DPI |

**可接受区间**：实体 **18–24**、关系 **18–26**；`status=success`；`verify.ok=true`；
退出码 **0**；允许 `recycle-review`（返工回流 `R18`）；禁止 error 级违规。

**不变量**：`sequence` 只出现在 step/phase/milestone 之间（里程碑属允许端点）；
里程碑 → 下一阶段首步是 `depend` 而非 `sequence`；编号 1..N 连续；
`product`（候选基因清单）与 `data`（计数矩阵）都无出边（否则触发 `product-terminal`）。

**实测**：

| 观测量 | 实测 |
|-|-|
| 退出码 / `status` | **0** / `success` |
| 实体 / 关系 | **18 / 18** |
| `verify.ok` / 失败门 | **true** / 无 |
| 规则告警 | `recycle-review` ×1 |
| `uncertainty` 域 | 空 |
| `spec_sha16` | `cb33950dedb47795` |
| `figure.png` / `figure.pdf` | 82 561 B / 5 421 B |
| 单轮耗时 | 0.69 s |

> 这一案是本轮**难度最高**的一个：18 个实体、4 个阶段、2 个里程碑、1 条返工回流，
> 编号与阶段出口任一环节错位都会被 G8 或规则审计抓到，实测仍然一遍过。

## 4. C-3 / C-4 · 基线自带的两个示例（低难度锚点）

| 观测量 | C-3 `demo-biotech-route-01`（route） | C-4 `apparatus-spec-01`（apparatus） |
|-|-|-|
| 退出码 / `status` | 0 / `success` | 0 / `success` |
| 实体 / 关系 | 10 / 9 | 6 / 5 |
| `verify.ok` / 门 | true / 无 | true / 无 |
| 规则告警 | 无 | 无（`apparatus-flow-into-material` 未触发、`product-terminal` 未触发） |
| `spec_sha16` | `e04e9d47e8ca0099` | `4603787adcb287d7` |
| PNG / PDF 字节 | 54 982 / 4 448 | 28 884 / 3 889 |
| 单轮耗时 | 0.69 s | 0.71 s |

## 5. 逐案实测总表（`case_set_run.py` 一次运行的完整结果）

| case_id | 图类 | 难度 | 退出码 | `status` | 实体 | 关系 | `verify.ok` | 告警 | `spec_sha16` | 结论 |
|-|-|-|-|-|-|-|-|-|-|-|-|
| `apparatus-spec-01` | apparatus | 低 | 0 | `success` | 6 | 5 | true | — | `4603787adcb287d7` | **PASS** |
| `demo-biotech-route-01` | route | 低 | 0 | `success` | 10 | 9 | true | — | `e04e9d47e8ca0099` | **PASS** |
| `dtms-stage-route-01` | route | 高 | 0 | `success` | 18 | 18 | true | `recycle-review` | `cb33950dedb47795` | **PASS** |
| `mbr-wastewater-flow-01` | flow | 中 | 0 | `success` | 14 | 14 | true | `recycle-review` | `5b65c6612f7714e0` | **PASS** |

**汇总（脚本自己算的）**：`cases=4 · passed=4 · failed=0 · without_expectation=0`。
四个案例覆盖了三种 `figure_type`（route / flow / apparatus）与三个难度层，
契约门 G1–G10 在四次运行里全部通过（`gates_false` 全为空）。

## 6. ★ 泛化到哪里会失效（实测，不是猜测）

`--text-only` 把每个案例**压扁**成只留 `text` 字段的版本再跑（模拟"材料没有结构化实体"
的真实场景）。两轮的差就是"结构化信息消失后本包还能保住什么"：

| case_id | 实体保留率 | 关系保留率 | 丢失的规则告警 | 文本版 `status` |
|-|-|-|-|-|
| `apparatus-spec-01` | 0.667（6→4） | **0.000（5→0）** | — | **`partial`** |
| `demo-biotech-route-01` | 0.200（10→2） | 0.111（9→1） | — | `success` |
| `dtms-stage-route-01` | 0.389（18→7） | 0.333（18→6） | **`recycle-review`** | `success` |
| `mbr-wastewater-flow-01` | 0.429（14→6） | 0.357（14→5） | **`recycle-review`** | `success` |

**据此可以明确说出三件事：**

1. **结构化输入是本包的主航道**：4 个案例里实体保留率 0.20–0.67，关系保留率
   0.00–0.36 —— 文本解构**只能串联相邻步骤**，分流/合流/回流/依赖/里程碑会整体丢失。
   C-2、C-1 这两案的核心考点（返工回流、污泥回流）在文本形态下**完全消失**
   （`recycle-review` 告警不再出现，即回流关系根本没被识别出来）。
2. **装置图在文本形态下最危险**：C-4 的 5 条关系**全部丢失**（保留率 0.00），
   4 个孤实体触发 `orphan_entities`，`status` 从 `success` 掉到 **`partial`**。
   ⇒ **给装置图时不要只喂一段文字**；至少提供"部件清单 + 接口/连接清单"。
3. **静默风险随覆盖率下降而上升**：文本版里 `demo-biotech-route-01` 仍然报
   `success`（2 实体 1 关系），也就是说**输入退化不会自动让状态降级**——
   只有出现孤儿实体时才会（C-4）。这是本包已知的诚实边界，复核办法是同时看
   `extraction`（应为 `text-heuristic`）与实体数是否与材料规模相称。

### 其他已知失效边界（未实测，如实标注）

| 边界 | 状态 |
|-|-|
| 实体数 > 24 或阶段数 > 5 | **未测**；布局会变拥挤，需要靠 `--width-mm/--height-mm` 调画布 |
| 多级嵌套装配 / 局部放大视图 | **不支持**（本包只做单层装配）；可在 Inkscape 微调并记 `manual-edit` |
| 装置图中的"物料作为流向终点" | 会被判 **error**（`apparatus-flow-into-material`）并降级 `partial`——这是规则设计，不是缺陷 |
| 图内数值注记（浓度、流速等） | **不强制渲染**：材料给的可标注值只能进实体 `props` |
| 非 UTF-8 材料 / 超长材料 / 并发运行 | **未测** |
| 平台固定 3 个案例 | **不可见**，本文件与 `case-set.json` 均不预测其表现 |

## 7. 题集怎么复用（生态贡献）

- **换题材**：复制 `examples/cases/<任一案>` 两份文件（`case.json` + `task.md`），
  改 `entities`/`relations`/`source` 指向新材料的章节号；在
  `references/case-set.json` 里登记 `case_path` 与期望区间即可被批量跑批；
- **加判据**：`case-set.json` 的 `invariants` 是给人读的设计意图；机器判据在
  `expect_no_errors` / `allowed_warnings` / `forbidden_errors` / 实体关系区间 —— 想
  让某条不变量变成机器门，就把它翻译成 `forbidden_errors` 里的一条规则名；
- **测泛化**：任何新案例都能用 `--text-only` 立刻得到"结构化 vs 纯文本"的保留率，
  这对"这个题材到底需不需要结构化输入"是个廉价而客观的判据；
- **不适用于**：用本表去推断平台固定案例的表现（材料与白板都不在我们手上）。
