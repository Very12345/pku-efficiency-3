# FAULT-MATRIX — 故障注入与恢复演练实测矩阵（v4）

本文件是一份**实测记录**，不是设计意图清单。每一行的「实测」列都来自
`scripts/fault_inject.py` 的一次真实运行：注入一个具体故障 → 起一个全新的
`scripts/main.py` 子进程 → 读回它真实给出的 exit code、`result.json.status`、
`uncertainty` 条目、以及产物落盘情况。

> **复跑命令**（在**包外**的临时副本上跑；脚本自身会拒绝把工作目录放进包内）：
>
> ```bash
> RUN=<可写临时目录>; cp -r "$SKILL_DIR" "$RUN/pkg"
> python "$RUN/pkg/scripts/fault_inject.py" --skill "$RUN/pkg" --run "$RUN/faultrun" \
>     --json "$RUN/fault-report.json" --markdown "$RUN/fault-table.md"
> # 实测：18 个场景，0 个静默失败，退出码 0
> ```
>
> 本矩阵对应的那次运行：Python 3.13.9（Windows 11 + Git Bash）；示例案例
> `example-catalyst-201`；合成图件 `fig1.png` / `fig2.png`（`make_synthetic_inputs.py`，
> exit 0）；18 个场景全部 `as-declared`（含 1 个 `HOST-DIFF`，见 §3）。

---

## 1. 四条结论（先看这个，再看表）

1. **「跑不下去」与「跑歪了」是两类问题，本包的处置方式不同。**
   前者（case 读不了、依赖没装、`--out` 不可写）走 **exit≠0 + 不冒充成功**；
   后者（材料没了、模板坏了、图丢了）走 **继续跑 + 逐条记录 + 状态词汇诚实**。
   18 个场景里各有 5 与 13 个，没有一个是"静默地假装一切正常"。
2. **独立校验器真的独立。** 两次篡改（删契约键、删产物）都被
   `check_contract.py` 从磁盘重扫后判为不合格（G3 / G7+G8），
   而 `result.json` 自己的自述仍然是 `status=success`。**自述与判定是两条路。**
3. **有 4 处降级只落在 `uncertainty`，没有影响 `status`**（i03/i04/i06/k04 中的
   材料与图件类）。它们**不是静默失败**（记录在案、可检索），但确实不会把状态
   拉低到 `partial`。这是本包**已经承认的粗糙点**，逐条列在 §4。
4. **有 1 处是宿主平台差异，不是包的问题**（d04：Windows 上 `chmod 0444` 拦不住
   写入）。矩阵把它标成 `HOST-DIFF` 而不是 `as-declared`，避免把平台行为记成机制。

## 2. 实测矩阵（18 个场景）

图例：`exit` = `main.py` 退出码；`独立门` = `check_contract.py` 的退出码
（仅控制组与 k02/k03 跑）；`unc` = `result.json` 顶层 `uncertainty` 条数。

| # | 场景 ID | 家族 | 注入的故障 | 期望行为（声明） | 实测 exit | 独立门 | 实测 status | unc | 静默失败 | 判定 |
|-|-|-|-|-|-|-|-|-|-|-|
| 1 | `c00-control` | control | 无注入（原样跑通示例案例） | exit 0 / success / 产物齐全 / G1–G8 全过 | **0** | **0**（`valid=true`） | `success` | 1 | 否 | as-declared |
| 2 | `i01-missing-case` | input | `--case` 指向不存在的 `case.json` | exit 1 / `status=failed` / 不产 pptx | **1** | — | `failed` | 1 | 否 | as-declared |
| 3 | `i02-garbage-case` | input | `case.json` 被截断（非法 JSON） | exit 1 / `failed` / 不抛裸栈 | **1** | — | `failed` | 1 | 否 | as-declared |
| 4 | `i03-material-missing` | input | `source_material` 指向不存在的文件 | 按 D2 继续：`sources[].exists=false` + 记录 | 0 | — | `success` | **3** | 否 | as-declared |
| 5 | `i04-material-binary` | input | 材料存在但不是 UTF-8 | 按 F03 只登记来源，不假装读过 | 0 | — | `success` | **2** | 否 | as-declared |
| 6 | `i05-task-missing` | input | `--task` 指向不存在的 `task.md` | 流程继续（`task_summary` 为空） | 0 | — | `success` | 1 | 否 | as-declared |
| 7 | `i06-figures-missing` | input | `case.figures` 指定的两张图被删除 | 按 D5/F15 留占位框 + 逐图记录 | 0 | — | `success` | **3** | 否 | as-declared |
| 8 | `t01-template-missing` | template | `--template` 指向不存在的文件 | 回退链到运行时内置模板并继续 | 0 | — | `success` | 1 | 否 | as-declared |
| 9 | `t02-template-corrupt` | template | 模板存在但不是 zip | 记 `template_errors` 后回退并继续 | 0 | — | `success` | 1 | 否 | as-declared |
| 10 | `t03-startdeck-corrupt` | template | 起始 deck 损坏 | 同回退链；不出现 `edit_starting_deck` | 0 | — | `success` | 1 | 否 | as-declared |
| 11 | `d01-no-pptx` | dependency | `pptx` 导入即抛 `ImportError` | exit 1 / `failed` / 带原始异常文本 | **1** | — | `failed` | 1 | 否 | as-declared |
| 12 | `d02-no-pil` | dependency | `PIL` 导入即抛 `ImportError` | exit 1 / `failed` / 不产空 PNG | **1** | — | `failed` | 1 | 否 | as-declared |
| 13 | `d03-out-unwritable` | dependency | `--out` 指向一个普通文件 | exit 2 / **不写半截 JSON** | **2** | — | （无 `result.json`） | — | 否 | as-declared |
| 14 | `d04-out-readonly` | dependency | `--out` 是只读目录（`chmod 0444`） | POSIX 下应报错 | 0 | — | `success` | 1 | 否 | **HOST-DIFF** |
| 15 | `k01-caseid-mismatch` | contract | `case.json` 的 `case_id` 被改名 | G1 两边一致 → 门仍全过 | 0 | — | `success` | 1 | 否 | as-declared |
| 16 | `k02-tamper-contract` | contract | 跑完删掉一个契约键，再跑独立门 | 独立门判不合格（G3） | 0 | **1**（`valid=false`，失败门 `G3`） | `success` | 1 | 否 | as-declared |
| 17 | `k03-artifact-missing` | contract | 跑完删掉封面预览，再跑独立门 | 独立门逐文件扫出缺失（G7） | 0 | **1**（`valid=false`，失败门 `G7`,`G8`） | `success` | 1 | 否 | as-declared |
| 18 | `k04-work-nonexistent` | contract | `--work` 指向不存在的目录 | 路径解析回落到 case 目录，材料仍读到 | 0 | — | `success` | 1 | 否 | as-declared |

**合计：18 个场景，0 个静默失败，0 个未声明差异（`d04` 已按宿主差异单独归类）。**

## 3. 逐场景实测明细（含判定依据用的字段）

### 3.1 control

**`c00-control`** — 无注入，用来给其余 17 个场景当参照。
实测：exit 0，`status=success`，10 页，产物 12 个，
`check_contract` exit 0 / `valid=true` / 失败门 `[]`，
`figures_embedded=2/2`，`change_records=[]`，`uncertainty=1`（只因案例未给模板而记"内置回退模板为运行时生成"）。

> 控制组的 `uncertainty` **非空但状态是 `success`**：因为这条记录是
> 「案例没给模板 ⇒ 现场生成」的**运行事实**，不是降级。这正是 G8 要求
> 「非 success 必须有 uncertainty」而**不要求**「有 uncertainty 必须非 success」的原因。

### 3.2 input 家族（6 个）

| 场景 | 真实回读到的证据 |
|-|-|
| `i01-missing-case` | `uncertainty[0] = {"item":"pipeline","note":"FileNotFoundError: [Errno 2] No such file or directory: '...\\absent_case.json'"}`；out 目录里**只有 `result.json` 一个文件**（没产 pptx/PNG）；stderr 一行 `main FAILED: [Errno 2] ...` |
| `i02-garbage-case` | `uncertainty[0].note = "JSONDecodeError: Expecting value: line 1 column 32 (char 31)"`；同样**只有 `result.json`**；退出码 1 |
| `i03-material-missing` | `uncertainty` 3 条：`source material material_v2_final.md`（note: *file missing -> content derived only from case.json + task.md*）、`no readable material`、`builtin fallback template`；`sources[0].exists=false`；**仍然产出 10 页 / 12 个产物**，页面主张全部来自 `case.json` 的结构化字段 |
| `i04-material-binary` | `uncertainty` 2 条，其中 `note = "not UTF-8 text: 'utf-8' codec can't decode byte 0xff in position 0: invalid start byte"` —— 记录里**带原始解码错误**，没有一个字是编造的 |
| `i05-task-missing` | exit 0、success、**`uncertainty` 里没有专门条目**（`task_summary` 为空字符串）。见 §4 第 2 条 |
| `i06-figures-missing` | `uncertainty` 逐图各一条：`figure 1 source image` / `figure 2 source image`，note = *source image missing/unavailable -> placeholder box with caption; original caption kept*。**注意 `figures_embedded` 仍报 2/2**（它数的是"按计划落位的图表引用"，不是"成功嵌入的位图"）。见 §4 第 1 条 |

### 3.3 template 家族（3 个）

| 场景 | 真实回读到的证据 |
|-|-|
| `t01-template-missing` | `opened_from=builtin`，`template_errors=0`；`uncertainty` 记"内置回退模板为运行时生成"。**注意：路径不存在时 `template_errors` 是 0 条** —— 回退链是在候选枚举阶段就跳过的，不是"打开失败" |
| `t02-template-corrupt` | `opened_from=builtin`，**`template_errors=1`** —— 损坏的模板是真的"打开失败"，所以有一条错误记录。这是 `template_errors` 非空的唯一一个注入场景 |
| `t03-startdeck-corrupt` | `opened_from=builtin`，`template_errors=1`，`change_records=[]` —— **没有出现 `edit_starting_deck`**，因为没有编辑成功；`dropped_original_slides` 也没被写成一个假数字 |

> 三个模板场景的 `status` 都是 `success` 而不是 `partial`：回退链是本包的
> **设计路径**（案例未给模板是常态，见 `SKILL.md` §1 与 D5），不是异常。
> 判别法：`uncertainty` 里说的是"回退到了哪里"，而不是"丢失了什么"。

### 3.4 dependency 家族（4 个）

| 场景 | 真实回读到的证据 |
|-|-|
| `d01-no-pptx` | exit 1；`status=failed`；`uncertainty[0] = "ImportError: simulated: python-pptx not installed"`（**原始异常文本被保留**）；产物只有 `result.json` |
| `d02-no-pil` | 同上，note = `ImportError: simulated: Pillow not installed`；**没有产出空 PNG 冒充成功** |
| `d03-out-unwritable` | exit **2**；**out 目录里 0 个文件**（连 `result.json` 都没写）；stderr 两行，末行是 `main FAILED: cannot write to --out '../out_is_a_file': FileExistsError: [WinError 183] ...` |
| `d04-out-readonly` | exit 0、`status=success`、12 个产物**照常写出** —— Windows 上 `chmod 0444` 不阻止写入。声明的是 POSIX 行为，实测环境是 Windows，故判定 `HOST-DIFF` 而非 `as-declared` |

> `d03` 是本矩阵里**唯一一个"没有 result.json"**的场景，这是刻意的：
> `--out` 不可写意味着连"诚实失败"的记录都没地方放，所以走退出码 2，
> 而不是写半截 JSON 到别处。

### 3.5 contract 家族（4 个）

| 场景 | 真实回读到的证据 |
|-|-|
| `k01-caseid-mismatch` | 产物文件名随 `case_id` 一起变成 `renamed-by-hand-999_cover_preview.png`，`stdout` 写 `case=renamed-by-hand-999`；因为 `result.case_id` 与 `case.json.case_id` **两边一起改了**，G1 仍通过 |
| `k02-tamper-contract` | 篡改动作 = `removed top-level contract key 'template_inheritance' from result.json`；随后独立门 **exit 1 / `valid=false` / 失败门 `['G3']`**（`detail` 里 `missing=['template_inheritance']`）。此场景**我们不按 `main.py` 的退出码判定** —— 它是一次干净运行，篡改发生在运行之后 |
| `k03-artifact-missing` | 篡改动作 = `deleted example-catalyst-201_cover_preview.png`；独立门 **exit 1 / `valid=false` / 失败门 `['G7','G8']`**（G7 列出缺失文件名，G8 因为契约要求 preview 而预览不在） |
| `k04-work-nonexistent` | `--work` 不存在时，材料仍被 `case.json` 所在目录解析到；exit 0、success、图表 2/2 上图 |

> `k02`/`k03` 的价值不在退出码，而在**证伪了"自述可以替代判定"**：
> 两次篡改后 `result.json` 顶层仍然写着 `status=success`，而独立校验器
> 从磁盘重扫后直接判不合格。这正是本包的**「契约先行 + 独立校验」机制的
可证伪判据**：如果校验器只是复述 `result.json` 的自述，这两次篡改就抓不出来。

## 4. 已知粗糙点（如实列出，不粉饰）

这一节是本文件最该被读的部分：**以下 4 条是本次演练暴露出来的、本包确实做得不够好的地方。**

1. **缺图不会把状态拉低。** `i06` 里两张源图都被删掉，`uncertainty` 逐图记了
   两条，但 `status` 仍是 `success`，且 `main_result.figures_embedded` 仍报
   `2/2`（该字段数的是"计划落位的图表引用数"）。**后果**：只看 `status` 的
   消费方会以为图都进去了。**建议判别法**：同时读 `uncertainty` 里
   `figure * source image` 类条目与 `template_audit.figure_adjust[].placed`。
2. **`--task` 缺失没有专属记录。** `i05` 里 `task_summary` 为空，但
   `uncertainty` 没有一条说"任务说明没读到"。**后果**：`--task` 拼错路径时
   运行记录不会提醒。**建议判别法**：检查 `result.json.task_summary` 是否为空。
3. **材料/图件类降级不改变 `status`。** 只有 `case.json` 不可解析、全链模板失败、
   依赖缺失、`--out` 不可写这几条才会让状态离开 `success`。`D2/D3/D4/D5/F03/F15`
   这些"内容侧"降级全部只进 `uncertainty`。**理由**（不是借口）：这些场景下
   本包**仍然产出了一册完整、可讲、证据可追溯的汇报**，把它标成 `partial`
   会让真正有损的场景失去区分度；但这条取舍应当由消费方知道。
4. **宿主差异会打乱"只读目录"这条判据。** `d04` 在 Windows 上无法用 `chmod`
   模拟；矩阵把它标成 `HOST-DIFF` 并保留原始实测，而不是删掉这一行装作没测。

> §4 的 1–3 条都是「记录在案但不改状态」。如果你的消费方需要"状态敏感"的
> 行为，请直接读 `uncertainty` 的 `item` 前缀（`source material` / `figure` /
> `builtin fallback template` / `pipeline`），它比 `status` 更细。

## 5. 四个故障家族的注入方法（可照做）

| 家族 | 注入手法 | 为什么这么注入 |
|-|-|-|
| **input** | 复制示例目录后再改：删 `--case` 目标；写半截 JSON；把 `source_material` 指向幽灵文件；写非 UTF-8 字节；删 `figs/*.png`；把 `--task` 指向不存在的路径 | 每个子场景只动**一个**输入，保证观测到的差异可归因 |
| **template** | `--template` / `--starting-deck` 指向不存在的路径，或指向内容是 `NOT A ZIP FILE` 的假 pptx | 覆盖"缺失"与"损坏"两条不同代码路径（前者在枚举阶段即跳过，后者真的抛异常） |
| **dependency** | 在 `PYTHONPATH` **前置**一个 `import` 即 `raise ImportError(...)` 的假包（`pptx` / `PIL`），从而在不卸载任何东西的前提下模拟缺依赖；`--out` 指向普通文件；`--out` 指向 `chmod 0444` 的目录 | 假包方式是**可逆**的：子进程退出后环境恢复原状，不会污染后续场景 |
| **contract** | 跑完**之后**再改产物：删一个 `output_contract` 键；删一张预览 PNG；然后跑 `scripts/check_contract.py` 读它自己的 JSON 判定 | 关键在"之后"：先拿到一次干净、全绿的结果，再破坏它，才能证明**判定确实看了磁盘**而不是复述自述 |

**两条注入纪律**（也是本脚本被写出来的原因）：

1. **不要在包内跑任何东西。** `scripts/__pycache__/*.pyc` 一出现，
   提交合规硬门就会失败（`.pyc` 是平台拒绝的资源类型）。
   `fault_inject.py` 默认拒绝把 `--run` 设在包内，需要显式
   `--allow-in-package` 才放行。
2. **一个场景一个全新子进程。** 同进程内复用会让上一个故障的残留状态
   （临时目录、已生成的回退模板、导入缓存）污染下一个测量。

## 6. 这份矩阵与 `failure-modes.md` 的关系

- `references/failure-modes.md` 写的是**应该发生什么**（F01–F24 + D1–D16）；
- 本文件写的是**实际发生了什么**（18 个真实子进程的回读结果）；
- 两者对不上的地方，全部收在 §4，**不修改文档去迎合实测，也不修改实测去迎合文档**。

新增失败模式时的维护约定：① 在 `fault_inject.py` 的 `scenarios()` 里加一条
（含 `expect` 与 `must_not_succeed`）；② 真跑一次并把实测列补进 §2/§3；
③ 若发现新粗糙点，追加进 §4；④ 若该模式改变了状态语义，同步
`references/failure-modes.md` 与 `SKILL.md` 的降级路径表。
