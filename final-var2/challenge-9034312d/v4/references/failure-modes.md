# failure-modes.md — 失败模式与四形态处置表（本版据 32 条注入实测重写）

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
