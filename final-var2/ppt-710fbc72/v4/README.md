# Academic Slide Adapter —— 失败注入与恢复演练包（v4）

**一句话定位**：这是一个**失败注入与恢复演练包**。它在基线能力（一册可编辑、可讲、
证据可追溯的学术汇报 pptx）之上，新增 `scripts/fault_inject.py` 与
`references/FAULT-MATRIX.md`，把「文档声称的降级行为」变成「18 个场景的实测结果」——
每条降级路径都真的被触发过一次，并留下退出码、`status`、`uncertainty` 与产物清单。

> 本包不新增任何生成能力。它新增的是**证据**：证明既有降级路径真实存在、
> 退出码语义稳定、独立校验器不信任自述。

---

## 1. 依赖与环境

| 项 | 值 |
|-|-|
| 运行时依赖 | **python-pptx**、**Pillow**（Skill 运行时只用这两个；numpy / matplotlib 仅用于版本记录） |
| 实测 Python | **3.13.9** |
| 实测系统 | **Windows 11 + Git Bash（MSYS2）** |
| 预览 | 本机**无 LibreOffice / PowerPoint** ⇒ 预览为 **PIL 示意图**，并在产物里如实标注，不冒充像素级导出 |
| 可选工具 | LibreOffice（仅在需要真实 PDF 导出时）；本包的实测环境没有它 |

`scripts/fault_inject.py` 只用标准库（`argparse / json / os / shutil / subprocess /
sys / time`），不引入新依赖。这一点很重要：**演练工具本身不能成为新的依赖风险**。

---

## 2. 快速上手：在**包外**副本上跑故障注入

必须在**包外的可写副本**上跑。原因不是洁癖：在包内执行 `scripts/*.py` 会留下
`scripts/__pycache__/*.pyc`，而 `.pyc` 是提交契约明确拒绝的资源类型。
脚本自己也做了这件事——它**默认拒绝**把 `--run` 设在包内，需要显式
`--allow-in-package` 才放行。

### 2.1 全量 18 个场景（与 `references/FAULT-MATRIX.md` 一致）

```bash
SKILL_DIR=<本包根目录>            # 平台装到 /skills/weekly-skill
RUN=<任意可写临时目录>

cp -r "$SKILL_DIR" "$RUN/pkg"
python "$RUN/pkg/scripts/fault_inject.py" --skill "$RUN/pkg" --run "$RUN/faultrun" \
    --json "$RUN/fault-report.json" --markdown "$RUN/fault-table.md"
# 实测：18 个场景 / 0 个静默失败 / 退出码 0
```

两个输出文件是**同一次测量**的两种形态：`--json` 给机器读（逐场景全字段），
`--markdown` 给人读（矩阵表）。不存在「表格是一个数、报告是另一个数」。

### 2.2 只跑你关心的场景

```bash
# 先看有哪些场景
python "$RUN/pkg/scripts/fault_inject.py" --list

# 只跑两条（逗号分隔，不要空格）
python "$RUN/pkg/scripts/fault_inject.py" --skill "$RUN/pkg" --run "$RUN/faultrun2" \
    --only i01-missing-case,k03-artifact-missing

# 排除掉慢的/不关心的
python "$RUN/pkg/scripts/fault_inject.py" --skill "$RUN/pkg" --run "$RUN/faultrun3" \
    --skip d01-no-pptx,d02-no-pil --timeout 180
```

| 参数 | 作用 |
|-|-|
| `--list` | 列出全部场景 id 后退出，不跑任何东西 |
| `--only <id,id>` | 只跑指定场景 |
| `--skip <id,id>` | 排除指定场景 |
| `--timeout <s>` | 单场景超时（默认 180 秒） |
| `--json` / `--markdown` | 报告落盘路径 |
| `--allow-in-package` | 放行「在包内跑」——**除非你知道自己在做什么，别用** |

**退出码语义**（三档，均有实测）：`0` = 全部场景与声明一致；`1` = **至少一个场景
静默失败**；`2` = 用法/环境错误（例如工作目录被设在包内而遭拒绝）。
把「静默失败」单独做成非零退出码，是因为它正是本演练要抓的东西——
一个场景「跑完了」不等于它「跑对了」。

### 2.3 单场景的观测点

每个场景都记录这些字段，判断降级是否诚实时**看这五个**：

1. `exit` —— 进程退出码；
2. `result_json_written` + `status` —— 有没有诚实记录、记录写了什么；
3. `uncertainty_count` / `uncertainty_items` —— 降级是否**在案**；
4. `artifact_files` —— 到底产出了几个文件（`0` 个是最诚实的一种失败）；
5. `gate_exit` / `gate_valid` / `gate_failed` —— 独立校验器怎么说（仅 3 个场景跑门）。

---

## 3. 18 个场景一览

四个故障家族 + 一个控制组，共 **5 类标签**：`control` 1、`input` 6、`template` 3、
`dependency` 4、`contract` 4 = **18**。

> 下表 `exit` / `status` / `unc` 三列全部从本次实测报告逐条读出，不是设计值。
> 完整的注入手法、期望行为与原始 evidence 见 `references/FAULT-MATRIX.md` §2/§3。

| # | 场景 ID | 家族 | 注入什么 | 实测 exit | 实测 status | unc |
|-|-|-|-|-|-|-|
| 1 | `c00-control` | control | 无注入（原样跑通示例案例，作为基线对照） | 0 | `success` | 1 |
| 2 | `i01-missing-case` | input | `--case` 指向不存在的 `case.json` | 1 | `failed` | 1 |
| 3 | `i02-garbage-case` | input | `case.json` 内容被截断（非法 JSON） | 1 | `failed` | 1 |
| 4 | `i03-material-missing` | input | `source_material` 指向不存在的文件（结构化字段仍在） | 0 | `success` | 3 |
| 5 | `i04-material-binary` | input | 材料文件存在但不是 UTF-8（二进制字节） | 0 | `success` | 2 |
| 6 | `i05-task-missing` | input | `--task` 指向不存在的 `task.md` | 0 | `success` | 1 |
| 7 | `i06-figures-missing` | input | `case.figures` 指定的 `fig1.png` / `fig2.png` 被删除 | 0 | `success` | 3 |
| 8 | `t01-template-missing` | template | `--template` 指向不存在的文件（案例本身也没给模板） | 0 | `success` | 1 |
| 9 | `t02-template-corrupt` | template | 模板文件存在但不是 zip（损坏的 pptx） | 0 | `success` | 1 |
| 10 | `t03-startdeck-corrupt` | template | 起始 deck 损坏（编辑模式入口不可用） | 0 | `success` | 1 |
| 11 | `d01-no-pptx` | dependency | `PYTHONPATH` 前置一个 `import` 即抛 `ImportError` 的假 `pptx` 包 | 1 | `failed` | 1 |
| 12 | `d02-no-pil` | dependency | 同法伪造 `PIL`（Pillow）导入失败 | 1 | `failed` | 1 |
| 13 | `d03-out-unwritable` | dependency | `--out` 指向一个普通文件（目录创建必然失败） | **2** | （无 `result.json`） | — |
| 14 | `d04-out-readonly` | dependency | `--out` 是只读目录（`chmod 0444`） | 0 | `success` | 1 |
| 15 | `k01-caseid-mismatch` | contract | 把 `case.json` 的 `case_id` 改成别的值 | 0 | `success` | 1 |
| 16 | `k02-tamper-contract` | contract | 跑完后删掉 `result.json` 顶层一个 `output_contract` 键，再跑独立门 | 0 | `success` | 1 |
| 17 | `k03-artifact-missing` | contract | 跑完后删掉封面预览 PNG，再跑独立门 | 0 | `success` | 1 |
| 18 | `k04-work-nonexistent` | contract | `--work` 指向不存在的材料基目录 | 0 | `success` | 1 |

**合计：18 个场景，0 个静默失败，17 个 `as-declared` + 1 个 `HOST-DIFF`（`d04`）。**

数字自洽性：`exit=0` 的场景 13 个 / `exit=1` 4 个 / `exit=2` 1 个（=18）；
产 12 个产物的 13 个 / 只产 `result.json` 的 4 个 / 产 0 个的 1 个（=18）。
`status` 为 `success` 13 个、`failed` 4 个、无 `result.json` 1 个（=18）。

---

## 4. 四条最重要的实测结论

### ① 「跑不下去」与「跑歪了」是两类问题，处置方式不同

前者（`--case` 读不了、JSON 非法、依赖缺失、`--out` 不可写）走 **`exit≠0` + 不冒充成功**，
共 **5 个**场景（`i01`、`i02`、`d01`、`d02`、`d03`）。
后者（材料没了、模板坏了、图丢了）走 **继续跑 + 逐条记录 + 状态词汇诚实**，其余 **13 个**。
18 个场景里**没有一个是静默地假装一切正常**（`silent_failures = 0`）。

这条分野的实际意义：消费方可以用「退出码」当**是否可用**的判据，
用「`uncertainty`」当**可信到什么程度**的判据，两者不混用。

### ② 独立校验器真的独立

两次篡改都被 `scripts/check_contract.py` **从磁盘重扫**后判不合格：

- `k02`：删契约键 → 独立门 `exit=1`、`valid=false`、失败门 **`G3`**；
- `k03`：删封面预览 → 独立门 `exit=1`、`valid=false`、失败门 **`G7`,`G8`**。

而这两次运行自己的 `result.json` 顶层**仍然写着 `status=success`**。
**自述与判定是两条路**——这正是本包「不让 Skill 自己给自己发合格证」的实测形态。

### ③ 有 4 处降级只落在 `uncertainty`，不改 `status`

`i03` / `i04` / `i06` / `k04` 这几处的材料与图件类降级，都记了 `uncertainty`
（分别 3、2、3、1 条），但 `status` 维持 `success`。它们**不是静默失败**
（记录在案、可检索、可自动判读），但确实不会把状态拉低到 `partial`。
逐条理由与消费方应对方式见 `references/FAULT-MATRIX.md` **§4**。

### ④ 有 1 处是宿主平台差异，不是包的问题

`d04`：Windows 上 `chmod 0444` **拦不住写入**，所以「只读目录」这条判据在本机
无法验证——实测 `exit=0`、`status=success`、12 个产物照常写出。
矩阵把它标成 `HOST-DIFF` 而不是 `as-declared`，**并保留原始实测**，
而不是删掉这一行装作没测。

---

## 5. 它能证明什么 / 不能证明什么

| 能证明 | 依据 |
|-|-|
| **包内每条降级路径真实可触发** | 18 个场景各注入一个具体故障，全部由真实子进程跑出结果 |
| **退出码语义稳定** | `0` / `1` / `2` 三档各有实测；`d03` 是唯一无 `result.json` 的场景，刻意如此 |
| **校验器不信任自述** | `k02`/`k03` 两次篡改后自述仍 `success`，独立门判 `G3` / `G7`,`G8` 不合格 |
| **失败是「诚实失败」而非裸栈** | `i01`/`i02`/`d01`/`d02` 的 `uncertainty` 里保留**原始异常文本**；`d02` 不产空 PNG 冒充成功 |
| **回退链是设计路径而非异常** | 3 个 template 场景 `opened_from=builtin` 且状态仍 `success`，判别看的是「回退到哪」而非「丢了什么」 |

| 不能证明 | 原因 |
|-|-|
| **平台评分 / 排名** | 本包与平台打分无关；演练只回答「跑不跑得下去、跑歪了没」 |
| **真实案例的失败率** | 故障是**人为伪造注入**的，不是生产故障分布，不能反推真实事故率 |
| **跨平台行为** | 只在 Windows 11 本机测过；`d04` 那条恰恰说明 POSIX 行为在本机测不到 |
| **生成质量好坏** | 演练验证的是**降级路径与契约一致性**，不验证「这一册讲得好不好」——
后者需要公平对照（同输入、同模板、两个臂），本包不含那套装置 |

---

## 6. 限制（如实）

1. **故障是伪造注入的**，不是真实生产故障：假 pptx 包（`import` 即抛）、损坏文件、
   删文件、指向幽灵路径。它能覆盖代码路径，但**不能代替真实事故复盘**。
2. **只覆盖 Windows 本机**。`d03` 的 `[WinError 183]`、`d04` 的 `chmod` 失效都带平台印记；
   Linux 上的表现未实测。
3. **`d04` 这条宿主差异无法在本机验证**——需要 POSIX 环境才能证伪或证实「只读目录」被拦。
4. **门只跑了 3 个场景**（`c00`、`k02`、`k03`）。其余 15 个场景记录的是 `main.py` 行为，
   没有同时跑 `check_contract.py`，所以「这些场景的产物也能过 G1–G8」**不在本矩阵的证据内**。
5. **18 个场景不构成穷举**。它覆盖的是四类高频退化形态，不是「所有可能的失败」。

---

## 7. 维护：怎么加一个场景

四步，顺序不要颠倒：

1. **在 `scripts/fault_inject.py` 的 `scenarios()` 里加一条**，必须同时写清
   `expect`（期望 `exit` / `status`）与 `must_not_succeed`（该场景**不允许**跑成成功）。
   只写「注入什么」而不写「期望什么」，等于没有判据。
2. **真跑一次**（`--only <新 id>` 即可），确认它没被判成 `silent_failure`。
3. **把实测补进 `references/FAULT-MATRIX.md` 的 §2（矩阵行）与 §3（该家族的明细）**。
   §2 的 `exit` / `status` / `unc` 必须来自报告文件，**不要凭记忆填**。
4. **若发现了新的粗糙点**（记录在案但不改状态、或宿主差异），追加进 §4。
   如果该模式**改变了状态语义**，还要同步 `references/failure-modes.md` 与
   `SKILL.md` 的降级路径表——三处必须是同一个说法。

两条注入纪律（加场景时同样适用）：**不要在包内跑**；**一个场景一个全新子进程**
（同进程复用会让上一个故障的残留状态污染下一个测量）。

---

## 8. 目录里与本演练相关的文件

| 路径 | 作用 |
|-|-|
| `scripts/fault_inject.py` | 注入器 + 测量器：一个场景 = 一个全新子进程，产出 JSON 报告与 Markdown 矩阵 |
| `references/FAULT-MATRIX.md` | **本包的核心成果**：18 个场景的实测矩阵 + 逐场景证据 + §4 已知粗糙点 |
| `references/failure-modes.md` | 写的是**应该发生什么**（F01–F24 + D1–D16）；与实测对不上的地方全部收在 FAULT-MATRIX §4 |
| `scripts/check_contract.py` | 独立校验器：不信 `result.json` 的自述，从磁盘重扫 G1–G8 |
| `scripts/main.py` | 被测主流程（本演练不改它，只观测它） |
| `TEST.md` | 本轮的实测记录（逐场景表 + 两次篡改的原文证据 + 已知未覆盖项） |
| `examples/` | 最小调用示例（合成数据，非正式案例） |

> 复跑约定：所有命令里的 `$SKILL_DIR` 是本包根、`$RUN` 是包外可写临时目录。
> 包内保持只读，**二进制产物与 `.pyc` 不随包分发**。
