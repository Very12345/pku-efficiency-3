# TEST（v4）—— 失败注入与恢复演练实测记录

> 本文件是 **v4（失败注入与恢复演练包）** 的实测记录：所有场景数字来自本轮
> `scripts/fault_inject.py` 的一次真实运行（18 条场景记录），基线部分只在有出处时才写。
> 命令占位符：`$SKILL_DIR` = 本包根目录（平台装到 `/skills/weekly-skill`）；
> `$RUN` = 包外**可写**临时目录。**包内全程只读，不在包内执行任何脚本。**

---

## 0. 环境

| 项 | 值 |
|-|-|
| 系统 | Windows 11 + Git Bash（MSYS2） |
| Python | 3.13.9（报告自身的 `python` 字段也是 `3.13.9`） |
| 运行时依赖 | python-pptx 1.0.2 / Pillow 12.3.0 |
| 预览 | **无 LibreOffice / PowerPoint** ⇒ 预览为 PIL 示意图（如实标注，不产伪 PDF） |
| 被测案例 | 示例案例 `example-catalyst-201`（合成数据，非平台正式案例） |
| 合成图件 | `fig1.png` / `fig2.png`（`make_synthetic_inputs.py`，exit 0） |
| 报告生成时间 | 2026-11-22 19:51:53 +0800（Asia/Shanghai） |

18 个场景的总耗时 **23.63 秒**（逐场景 `seconds` 求和）：最快 **0.48 秒**
（`d03-out-unwritable`，它连门都没到就退出了），最慢 **2.01 秒**
（`k02-tamper-contract`，多跑了一次独立校验器）。每个场景都是**一个全新子进程**，
所以上表的时间不共享任何进程内状态。

---

## 1. 故障注入总结果

**18 个场景 / 0 个静默失败 / 退出码 0。**

报告的顶层字段直接写死了前两个：`scenario_count = 18`、`silent_failures = 0`；
逐场景的 `silent_failure` 全为 `false`，`mismatch` 全为空列表。

### 1.1 各家族的场景数

| 标签 | 场景数 | 场景 |
|-|-|-|
| `control` | **1** | `c00-control` |
| `input` | **6** | `i01`–`i06` |
| `template` | **3** | `t01`–`t03` |
| `dependency` | **4** | `d01`–`d04` |
| `contract` | **4** | `k01`–`k04` |
| **合计** | **18** | 4 个故障家族 + 1 个控制组，共 5 类标签 |

### 1.2 三个维度的分布（互相自洽，各自合计 18）

| 维度 | 分布 |
|-|-|
| 退出码 | `0` → **13** 个；`1` → **4** 个（`i01`/`i02`/`d01`/`d02`）；`2` → **1** 个（`d03`） |
| `result.json` 的 `status` | `success` → **13**；`failed` → **4**；**无 `result.json`** → **1**（`d03`） |
| 产物文件数 | 12 个 → **13** 个场景；仅 1 个（只有 `result.json`）→ **4** 个；**0 个** → **1** 个（`d03`） |
| 判定 | `as-declared` → **17**；`HOST-DIFF` → **1**（`d04`） |

> **「跑不下去」是多少个？** 退出码非 0 的是 **5 个**（`i01`、`i02`、`d01`、`d02`、`d03`），
> 这就是 `references/FAULT-MATRIX.md` §1 说的「5 与 13」里的 5。注意别把它和报告里
> `must_not_succeed = true` 的 **7 个** 混为一谈：后者多算的 2 个是 `k02`/`k03` ——
> 它们的 `main.py` 是干净跑通的（exit 0），**不允许成功的是随后的独立校验器**。

**独立校验器只跑了 3 个场景**（`c00-control`、`k02-tamper-contract`、`k03-artifact-missing`）：
报告里只有这 3 条带 `gate_*` 字段。其余 15 个场景**没有**跑门，
所以「它们也能过 G1–G8」不在本次证据范围内。

---

## 2. 逐场景实测表

`unc` = 该次运行 `result.json` 顶层 `uncertainty` 的条数（`—` = 没有 `result.json`，
无从谈起）。`判定` 为该场景的 `verdict` 字段原文。

| # | id | 家族 | 注入 | 实测 exit | 实测 status | unc | 判定 |
|-|-|-|-|-|-|-|-|
| 1 | `c00-control` | control | 无注入（原样跑通示例案例） | 0 | `success` | 1 | as-declared |
| 2 | `i01-missing-case` | input | `--case` 指向不存在的 `case.json` | 1 | `failed` | 1 | as-declared |
| 3 | `i02-garbage-case` | input | `case.json` 被截断（非法 JSON） | 1 | `failed` | 1 | as-declared |
| 4 | `i03-material-missing` | input | `source_material` 指向不存在的文件 | 0 | `success` | **3** | as-declared |
| 5 | `i04-material-binary` | input | 材料存在但不是 UTF-8 | 0 | `success` | **2** | as-declared |
| 6 | `i05-task-missing` | input | `--task` 指向不存在的 `task.md` | 0 | `success` | 1 | as-declared |
| 7 | `i06-figures-missing` | input | 案例引用的两张图被删除 | 0 | `success` | **3** | as-declared |
| 8 | `t01-template-missing` | template | `--template` 指向不存在的文件 | 0 | `success` | 1 | as-declared |
| 9 | `t02-template-corrupt` | template | 模板存在但不是 zip | 0 | `success` | 1 | as-declared |
| 10 | `t03-startdeck-corrupt` | template | 起始 deck 损坏 | 0 | `success` | 1 | as-declared |
| 11 | `d01-no-pptx` | dependency | 假 `pptx` 包：`import` 即抛 `ImportError` | 1 | `failed` | 1 | as-declared |
| 12 | `d02-no-pil` | dependency | 假 `PIL` 包：同上 | 1 | `failed` | 1 | as-declared |
| 13 | `d03-out-unwritable` | dependency | `--out` 指向一个普通文件 | **2** | （无 `result.json`） | — | as-declared |
| 14 | `d04-out-readonly` | dependency | `--out` 是只读目录（`chmod 0444`） | 0 | `success` | 1 | **HOST-DIFF** |
| 15 | `k01-caseid-mismatch` | contract | `case_id` 被改名 | 0 | `success` | 1 | as-declared |
| 16 | `k02-tamper-contract` | contract | 跑完删一个契约键，再跑独立门 | 0 | `success` | 1 | as-declared |
| 17 | `k03-artifact-missing` | contract | 跑完删封面预览，再跑独立门 | 0 | `success` | 1 | as-declared |
| 18 | `k04-work-nonexistent` | contract | `--work` 指向不存在的目录 | 0 | `success` | 1 | as-declared |

> `k02`/`k03` 的「实测 exit」是 `main.py` 的退出码（**0**，因为它俩确实是干净跑完的）。
> 这两个场景要看的是**独立门**的退出码 —— 见 §3。

### 2.1 几条实测细节（都能在报告里逐字复核）

- **`i01` / `i02` / `d01` / `d02` 的产物只有 `result.json` 一个**（没产 pptx、没产 PNG），
  `uncertainty` 的 `item` 都是 `pipeline`，`note` 里保留**原始异常文本**：
  `i02` 是 `JSONDecodeError: Expecting value: line 1 column 32 (char 31)`；
  `d01` 是 `ImportError: simulated: python-pptx not installed`；
  `d02` 是 `ImportError: simulated: Pillow not installed`
  （`d02` **没有产出空 PNG 冒充成功**）。`i01` 的原文含本机绝对路径，此处不转录。
- **`d03` 是 18 个场景里唯一没有 `result.json` 的**：out 目录 0 个文件，
  stderr 末行是 `main FAILED: cannot write to --out '../out_is_a_file': FileExistsError: [WinError 183]`
  （原文其后还有一段本机路径，此处略去）。**它刻意走退出码 2**：`--out` 不可写意味着
  连「诚实失败的记录」都没地方放，所以不往别处写半截 JSON。
- **`i03` 的三条 `uncertainty`** 依次是：`source material material_v2_final.md`
  （note: `file missing -> content derived only from case.json + task.md`）、
  `no readable material`（note: `no material text; decks are driven by case.json structure only`）、
  `builtin fallback template`。**它仍然产出 10 页 / 12 个产物**。
- **`i04` 的记录里带着原始解码错误**：
  `not UTF-8 text: 'utf-8' codec can't decode byte 0xff in position 0: invalid start byte`。
- **`i06` 逐图各一条**：`figure 1 source image` / `figure 2 source image`，
  note 都是 `source image missing/unavailable -> placeholder box with caption; original caption kept`。
  ⚠ 但该场景的 `figures_embedded` **仍报 2/2**（它数的是「按计划落位的图表引用」，
  不是「成功嵌入的位图」）—— 见 §5 第 1 条。
- **`t01` 与 `t02` 是两条不同的代码路径**：`t01`（路径不存在）的 `template_errors` 是 **0** 条
  （回退链在候选枚举阶段就跳过了它），`t02`（文件存在但损坏）的 `template_errors` 是 **1** 条
  （真的打开失败）。两者最终 `opened_from` 都是 `builtin`，状态都是 `success`。
- **`t03`（起始 deck 损坏）没有出现 `edit_starting_deck`**：`change_records` 为空列表，
  `template_errors` 1 条 —— 编辑没成功，就**没有把一个假数字写进记录**。
- **`k01` 改名后文件名跟着变**：stdout 写着 `case=renamed-by-hand-999`，
  但 `result.case_id` 与 `case.json.case_id` 是**一起改的**，所以 G1 仍通过。
- **`k04` 的路径回落生效**：`--work` 不存在时，材料仍由 `case.json` 所在目录解析到，
  exit 0、`success`、图 2/2 上图。
- **`c00-control` 的 `uncertainty` 非空（1 条）但状态是 `success`**：那条说的是
  「案例没给模板 ⇒ 回退模板在运行时现场生成（`_runtime/builtin.pptx`）」，
  属于**运行事实**而非降级。这正是门要求「非 `success` 必须有 `uncertainty`」、
  而**不要求**「有 `uncertainty` 必须非 `success`」的原因。

---

## 3. 两次篡改的原文证据（独立门 vs 自述）

两次篡改都发生在**一次干净运行之后**，所以要看的是独立门 `check_contract.py` 的判定。
报告里没有名为 `tamper` 的字段，**篡改动作记录在 `inject` 字段**里，判定记录在
`gate_exit` / `gate_valid` / `gate_failed` 三个字段里。

### 3.1 `k02-tamper-contract` —— 删一个契约键

| 字段 | 实测值 |
|-|-|
| `inject`（篡改动作） | 跑完后删掉 `result.json` 顶层的一个 `output_contract` 键（伪造「全部字段都已回显」），再跑 `check_contract.py` |
| `exit` / `status`（`main.py` 自述） | **0** / **`success`**（stdout: `main ok: case=example-catalyst-201 status=success slides=10 contract_gates=ok`） |
| `gate_exit` | **1** |
| `gate_valid` | **`false`** |
| `gate_failed` | **`["G3"]`** |

### 3.2 `k03-artifact-missing` —— 删一个产物

| 字段 | 实测值 |
|-|-|
| `inject`（篡改动作） | 跑完后删掉封面预览 PNG，再跑 `check_contract.py`（G7 逐文件扫产物） |
| `exit` / `status`（`main.py` 自述） | **0** / **`success`** |
| `gate_exit` | **1** |
| `gate_valid` | **`false`** |
| `gate_failed` | **`["G7","G8"]`** |

**这两条为什么重要**：两次篡改后 `result.json` 顶层**依然写着 `status=success`**，
而独立校验器从磁盘重扫后直接判不合格。**自述与判定是两条路** ——
「Skill 不能自己给自己发合格证」这句话，在这里有两次可复跑的实测。

对照：`c00-control`（未篡改）的独立门是 `gate_exit=0` / `gate_valid=true` /
`gate_failed=[]`，即 **G1–G8 全过**。有了这个对照，`k02`/`k03` 的失败才可归因到篡改本身。

---

## 4. 继承自基线的实测（只在有出处时写）

基线在示例案例上的冒烟口径，在本包的控制场景 `c00-control` 上**同样成立**。
逐项对出处如下（`c00` 一列全部来自本轮场景记录）：

| 基线冒烟项 | 基线出处 | `c00-control` 实测复核 |
|-|-|-|
| 一册 10 页 | 基线 `TEST.md` §1（10 页 = 目标 10 页） | 报告 `stdout_tail` = `main ok: case=example-catalyst-201 status=success slides=10 contract_gates=ok` |
| `exit 0` / `status=success` | 基线 `TEST.md` §1 | `exit=0`、`status="success"` |
| CP3 契约门全过 | 基线 `TEST.md` §1 与 §5（`verification.contract_gates` 8/8 ok） | `gate_exit=0`、`gate_valid=true`、`gate_failed=[]` —— 报告侧只有「全过/失败门列表」，**「8/8」这个计数出自基线记录** |
| 产物 12 个文件 | 基线 `TEST.md` §1 的产物清单 | `artifact_files` 长度 = **12**（含 `_runtime/builtin.pptx` 与 `_PREVIEW_ARE_SCHEMATIC.txt` 两个运行期文件） |
| 两张图都上图 | 基线 `TEST.md` §1（2 张嵌入图） | `figures_embedded=2` / `figures_total=2` |
| 版式零偏差 | 基线 `TEST.md` §1（10/10 页按方案套用） | `change_records=[]`（无计划外改动） |
| 契约字段全回显 | 基线 `TEST.md` §1（7 个键全部回显顶层） | `result_top_keys` 共 **28** 个顶层键，含 `output_contract` 相关键 |
| `evidence_loc_frac = 1.0` | 基线 `TEST.md` §1 与 §5（`verification.traceability.evidence_loc_frac=1.0`） | **本包注入报告不采集该字段**（它只记退出码/状态/`uncertainty`/产物）；此项**未重新测量**，数值仅继承基线记录 |

> 说明：最后一行是**有意留白**，不是漏测。故障注入报告的观测面是「降级与退出码」，
> 不是「抽取质量」；把基线的 1.0 直接搬过来说成「本轮实测」会是虚报。

---

## 5. 已知未覆盖 / 未修复

以下 4 条与 `references/FAULT-MATRIX.md` **§4** 一一对应，此处只列结论与影响：

1. **缺图只进 `uncertainty`，不改 `status`**（FAULT-MATRIX §4.1）。
   `i06` 里两张源图都被删除，`uncertainty` 逐图记了 2 条，但 `status` 仍是 `success`，
   且 `figures_embedded` 仍报 `2/2`。**只看 `status` 的消费方会误以为图都进去了。**
   ⇒ 判别法：同时读 `uncertainty` 里 `figure * source image` 类条目与
   `template_audit.figure_adjust[].placed`。
2. **`--task` 缺失没有专属记录**（FAULT-MATRIX §4.2）。`i05` 里 `task_summary` 为空，
   但 `uncertainty` 只有 1 条（且是回退模板那条），**没有一条说「任务说明没读到」**。
   ⇒ `--task` 路径拼错时，运行记录不会提醒；判别法是检查 `result.json.task_summary` 是否为空。
3. **内容侧降级不改 `status`**（FAULT-MATRIX §4.3）。只有 `case.json` 不可解析、
   全链模板失败、依赖缺失、`--out` 不可写这几条才会让状态离开 `success`；
   `D2/D3/D4/D5/F03/F15` 这些「内容侧」降级全部只进 `uncertainty`。
   ⇒ 需要状态敏感行为时，请直接读 `uncertainty` 的 `item` 前缀
   （`source material` / `figure` / `builtin fallback template` / `pipeline`），它比 `status` 更细。
4. **Windows 上无法验证「只读目录」这一条**（FAULT-MATRIX §4.4）。`d04` 用 `chmod 0444`
   模拟只读目录，但本机（Windows）**拦不住写入**：实测 exit 0、`success`、12 个产物照常写出。
   ⇒ 该场景标为 `HOST-DIFF` 而非 `as-declared`；要在 POSIX 环境复测才能判定。

另有一条**证据范围**上的限制：**独立门只跑了 3 个场景**，其余 15 个场景的产物
没有经过 G1–G8 复扫（见 §1）。

---

## 6. 复跑方法

```bash
SKILL_DIR=<本包根目录>            # 平台装到 /skills/weekly-skill
RUN=<包外可写临时目录>

cp -r "$SKILL_DIR" "$RUN/pkg"
python "$RUN/pkg/scripts/fault_inject.py" --skill "$RUN/pkg" --run "$RUN/faultrun" \
    --json "$RUN/fault-report.json" --markdown "$RUN/fault-table.md"
# 期望输出行（末行摘要）：18 个场景 / 0 个静默失败 / 退出码 0
```

期望的机器可读复核点：`scenario_count = 18`、`silent_failures = 0`、
逐场景 `silent_failure` 全 `false`、`mismatch` 全 `[]`、
`k02` 的 `gate_failed = ["G3"]`、`k03` 的 `gate_failed = ["G7","G8"]`、
`c00-control` 的 `gate_valid = true`。

只想快速复核关键几条（不必跑满 18 个）：

```bash
python "$RUN/pkg/scripts/fault_inject.py" --list
python "$RUN/pkg/scripts/fault_inject.py" --skill "$RUN/pkg" --run "$RUN/quick" \
    --only c00-control,k02-tamper-contract,k03-artifact-missing,d03-out-unwritable
```

> 复跑前请确认 `$RUN/pkg` 是**包外副本**：脚本默认拒绝把工作目录设在包内，
> 因为 `scripts/__pycache__/*.pyc` 一出现就会破坏提交资源契约。
