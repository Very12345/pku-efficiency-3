# FAULT-MATRIX.md — 四族失败注入与恢复的逐行实测矩阵

> **本文件的每一行都是真跑出来的，不是设计意图表。**
> `scripts/fault_inject.py` 把上游输入逐个弄坏（输入 / 模板 / 依赖 / 契约四族，共 28 条），
> 每条都在**包外副本**上跑一次完整的 `scripts/main.py`，然后回读
> `result.json` / `manifest.json` / `changelog.jsonl` / `logs/`，判定它到底留了什么痕。
>
> 复现命令（`$SKILL_DIR` = 本技能根目录，`<包外目录>` 必须是包外的可写目录，
> 包内跑会生成 `__pycache__` 而被平台预检拒收）：
>
> ```bash
> python "$SKILL_DIR/scripts/fault_inject.py" --list
> python "$SKILL_DIR/scripts/fault_inject.py" --pkg "$SKILL_DIR" --work <包外目录> --with-recovery
> ```
>
> 本轮实测环境：Python 3.13 + python-pptx 1.0.2 + matplotlib 3.10.6 + Pillow 12.3.0 +
> reportlab 5.0.0；28 条故障全部执行，总耗时约 60 秒（每条 1–3 秒）。

## 0. 判读口径（先看这 11 列怎么读）

| 列 | 含义 |
|-|-|
| exit | `main.py` 实测退出码（0=success / 1=partial / 2=输入不可读） |
| status | `result.json.status` 实测值（`—` = 根本没写出 `result.json`） |
| unc | `result.json.uncertainty` 条数 |
| mw | `evidence.material_warnings` 条数（材料类问题单独记，不与 uncertainty 混用） |
| cr | `change_records` 条数（>1 表示除 `start` 外确实还记了东西） |
| slides | `deck.slide_count`（0 = 未建 deck，D1 的诚实路径） |
| reopen | deck 能否被 python-pptx 重新打开（数字 = 实际页数） |
| 留痕 | **结构化**留痕字段（`uncertainty=1` 这类具体条目数；不把 JSON 里出现过键名当留痕） |
| 静默 | **Yes = 出了问题却没有任何可判读的记录**（最坏情况）；No = 有据可查 |
| 设计期望 | `references/failure-modes.md` 与决策规则 D1–D12 对该情形的期望（`-` = 只取证不预设） |
| 一致 | 实测 vs 设计期望：✅ 一致 / ⚠️ **偏离（§2 逐条解释）** / 取证 |

**留痕分三级**（本矩阵最重要的一个区分）：

| 等级 | 判定 | 下游能否判读 |
|-|-|-|
| `product` | 写进了 `result.json` / `changelog.jsonl` / `manifest.json` | 能 |
| `stdout-only` | 只有 stdout 里一行 Traceback，**没有任何产物** | 不能（编排器只看产物） |
| `none` | 连报错都没有 | 不能 |

只有 `product` 算"有据可查"。`stdout-only` 与 `none` 在本矩阵里都计为**静默失败**。

## 1. 逐行实测矩阵（28 条）

| # | 族 | 注入什么 | exit | status | unc | mw | cr | slides | reopen | 留痕 | 静默 | 设计期望 | 一致 | 恢复 |
|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|
| F-IN-01 | input | case.json 不存在 | 2 | failed | 0 | 0 | 0 | 0 | — | error=找不到 case 文件: `<path>` | No | 2/failed | ✅ | — |
| F-IN-02 | input | case.json 是半截 JSON | 2 | failed | 0 | 0 | 0 | 0 | — | error=Expecting ',' delimiter: line 4 column 1 (char 5 | No | 2/failed | ✅ | — |
| F-IN-03 | input | case.json 顶层是数组不是对象 | 2 | failed | 0 | 0 | 0 | 0 | — | error='list' object has no attribute 'setdefault' | No | 2/failed | ✅ | — |
| F-IN-04 | input | case.json 内容为 null | 2 | failed | 0 | 0 | 0 | 0 | — | error='NoneType' object has no attribute 'setdefault' | No | 2/failed | ✅ | — |
| F-IN-05 | input | 材料全部指向不存在的路径 | 1 | partial | 1 | 2 | 1 | 0 | — | uncertainty=1 · material_warnings=2 | No | 1/partial | ✅ | recovered |
| F-IN-06 | input | 材料文件存在但内容为空 | 1 | partial | 0 | 0 | 1 | 6 | 6 | unverified_claims=4 | No | 1/partial | ✅ | recovered |
| F-IN-07 | input | 材料被换成与声明用途不符的内容（CSV 里是散文） | 0 | success | 0 | 0 | 1 | 6 | 6 | — | **Yes** | 1/partial | ⚠️ | recovered |
| F-IN-08 | input | 材料字节非法（非 UTF-8） | 1 | partial | 0 | 1 | 1 | 6 | 6 | material_warnings=1 · unverified_claims=3 | No | -/- | 取证 | — |
| F-IN-09 | input | 材料指向目录而不是文件 | 1 | partial | 1 | 2 | 1 | 0 | — | uncertainty=1 · material_warnings=2 | No | -/- | 取证 | — |
| F-IN-10 | input | task.md 缺失（材料齐全） | 0 | success | 0 | 1 | 1 | 6 | 6 | material_warnings=1 | No | -/- | 取证 | recovered |
| F-TPL-01 | template | `--template` 指向损坏 JSON | 0 | success | 1 | 0 | 1 | 6 | 6 | uncertainty=1 | No | 0/success | ✅ | recovered |
| F-TPL-02 | template | `--template` 指向不存在的路径 | 0 | success | 1 | 0 | 1 | 6 | 6 | uncertainty=1 | No | 0/success | ✅ | recovered |
| F-TPL-03 | template | `--template` 是数组不是对象 | 1 | — | 0 | 0 | 0 | 0 | — | Traceback | **Yes** | 0/success | ⚠️ | recovered |
| F-TPL-04 | template | `spec.template_pptx` 损坏（非 zip） | 1 | partial | 1 | 0 | 1 | 0 | — | uncertainty=1 | No | 1/partial | ✅ | recovered |
| F-TPL-05 | template | `spec.template_pptx` 不存在 | 0 | success | 0 | 0 | 1 | 6 | 6 | — | **Yes** | -/- | 取证 | recovered |
| F-TPL-06 | template | `spec.starting_deck` 损坏 | 0 | success | 0 | 0 | 2 | 6 | 6 | change_records=2 | No | 1/partial | ⚠️ | recovered |
| F-TPL-07 | template | 页数上限小于必需页数（max_slides=3） | 0 | success | 0 | 0 | 1 | 3 | 3 | — | No | -/- | 取证 | recovered |
| F-DEP-01 | dependency | matplotlib 缺失 | 0 | success | 0 | 0 | 1 | 6 | 6 | figure.degraded=1 | No | 0/success | ✅ | recovered |
| F-DEP-02 | dependency | reportlab 缺失 | 0 | success | 1 | 0 | 1 | 6 | 6 | uncertainty=1 · previews.warnings=1 | No | 0/success | ✅ | — |
| F-DEP-03 | dependency | python-pptx 缺失（建稿轮子没了） | 1 | — | 0 | 0 | 0 | 0 | — | Traceback | **Yes** | 1/partial | ⚠️ | recovered |
| F-DEP-04 | dependency | Pillow 缺失（预览画布没了） | 1 | — | 0 | 0 | 0 | 0 | — | Traceback | **Yes** | -/- | 取证 | recovered |
| F-DEP-05 | dependency | 渲染链整体缺失（PIL + reportlab） | 1 | — | 0 | 0 | 0 | 0 | — | Traceback | **Yes** | -/- | 取证 | recovered |
| F-CTR-01 | contract | `output_contract` 声明未知类型 | 0 | success | 0 | 0 | 1 | 6 | 6 | widget | No | 0/success | ✅ | — |
| F-CTR-02 | contract | `output_contract` 类型名写成数字 | 0 | success | 0 | 0 | 1 | 6 | 6 | score | No | 0/success | ✅ | — |
| F-CTR-03 | contract | `output_contract` 是字符串不是对象 | 0 | success | 0 | 0 | 1 | 6 | 6 | — | **Yes** | 0/success | ✅ | recovered |
| F-CTR-04 | contract | `output_contract` 是字段名列表 | 0 | success | 0 | 0 | 1 | 6 | 6 | extras | No | 0/success | ✅ | — |
| F-CTR-05 | contract | 完全没有 `output_contract` | 0 | success | 0 | 0 | 1 | 6 | 6 | — | No | 0/success | ✅ | — |
| F-CTR-06 | contract | 已声明的契约字段被从 result.json 删除 | 1 | success | 0 | 0 | 1 | 6 | 6 | G2 declared output_contract field missing | No | 1/- | ✅ | recovered |

**汇总**（由 `--report-json` 的实测记录直接统计）：

| 统计项 | 实测值 |
|-|-|
| exit 分布 | `0 × 14` / `1 × 10` / `2 × 4` |
| status 分布 | `success × 15` / `partial × 5` / `failed × 4` / **未写出 result.json × 4** |
| 留痕等级 | `product × 19` / `stdout-only × 4` / `none × 5` |
| **静默失败** | **7 条**：`F-IN-07` `F-TPL-03` `F-TPL-05` `F-DEP-03` `F-DEP-04` `F-DEP-05` `F-CTR-03` |
| deck 可重开 | 14 条建了 deck 的故障 **14/14 都能被 python-pptx 重开且页数与 result 一致** |
| 与设计期望偏离 | 4 条：`F-IN-07` `F-TPL-03` `F-TPL-06` `F-DEP-03` |

## 2. 静默失败清单（7 条）——注入台真正的产出

> 这 7 条是**本包的真实缺口**，不是假想。每条都附：现象（实测）→ 根因（代码位置）
> → 后果 → **现可用的补救**。它们在 §4 的守卫里全部被抓到。

### S1 `F-IN-07` — 材料换成散文后，结果页图表**无声消失**（留痕 `none`）

- **现象**：把 `results.csv` 换成一段散文（列结构没了）。实测 `exit=0`、`status=success`、
  `uncertainty=[]`、`change_records=1`（只有 start）；第 5 页原本是 `chart_image`，
  现在 `figure.kind=none`、`note=""`。
- **根因**：数据表解析不出可用列 → 没有可绑定的表 → 结果页走"无表回落散文"分支。
  该分支**既没写 `figure.note`、也没写 uncertainty**：`failure-modes.md` 的 D9
  只覆盖"重绘失败（无 matplotlib / 非数值列 / `--no-chart`）"，
  **没覆盖"表根本没解析出来"**。
- **后果**：读者无法区分"这篇材料本来就没有图"与"有图但降级失败"——正是题面点名
  的失败形态的反面（题面点的是"放占位图或凭空生成曲线"，这里是**静默丢图**）。
- **现可用补救**：`--guard --out`（§4.2）报
  `WARN [figure] 材料里有 1 张数据表，但成稿里既没有图表/表格、也没有任何 note…`。

### S2 `F-CTR-03` — `output_contract` 写成字符串，契约回显被**整体跳过**（留痕 `none`）

- **现象**：`"output_contract": "case_id,deck,evidence"`。实测 `exit=0`、`status=success`、
  `uncertainty=[]`；`result.json` 里契约字段**一个都没回显**，而 G2 也不报错
  （它只在 `isinstance(oc, dict)` 时才逐字段核）。
- **根因**：`scripts/result_tool.py::apply_output_contract` 只处理 `dict` / `list`
  两种形态，其他形态**静默 return**；`validate()` 的 G2 是同款条件判断。
- **后果**：一旦组织方把契约写成非对象形态，交出的 `result.json` 会缺字段，
  却仍然显示"G1–G8 全过"——**这是最容易被误判成"契约全回显"的一类假通过**。
- **现可用补救**：`--guard --case` 报
  `DEGRADE [contract] output_contract 不是对象（str）——契约回显会被整体跳过`。

### S3 `F-TPL-05` — 指定的母版不存在，**静默改用内置模板**（留痕 `none`）

- **现象**：`spec.template_pptx = "no_such_master.pptx"`（文件不存在）。
  实测 `exit=0`、`status=success`、`uncertainty=[]`、`change_records=1`。
- **根因**：主流程把相对路径解析为"存在则用、不存在则**保留原字符串**"，
  之后 `build_deck` 拿到一个不存在的路径就按"没有母版"处理。
  **代码没有区分"组织方没给母版"与"给了但读不到"**（D6 只覆盖"打不开"）。
- **后果**：模板约束被悄悄放弃，成稿与组织方母版不一致，而记录里看不出来。
  对照 `F-TPL-04`（文件在但损坏）实测就留了 `uncertainty=1`——**同一类问题的两条路径
  待遇不同**，这就是缺口所在。
- **现可用补救**：`--guard --case` 报 `DEGRADE [template_pptx] … 指向的文件不存在`。

### S4–S7 `F-TPL-03` / `F-DEP-03` / `F-DEP-04` / `F-DEP-05` — **硬崩，只留 stdout 的 Traceback**

| 故障 | 实测 | 崩在哪 | 后果 |
|-|-|-|-|
| `F-TPL-03` | `exit=1`、无 `result.json` | `scripts/deck_tool.py::merge_spec` 对 list 取字符串下标 → `TypeError` | 模板参数形态传错就整轮无产物 |
| `F-DEP-03` | `exit=1`、无 `result.json` | `deck_tool` 顶层 `from pptx import Presentation` 失败 | 缺建稿库时连"最小 failed result"都写不出来 |
| `F-DEP-04` | `exit=1`、无 `result.json` | `render_qa` 顶层 `from PIL import Image` 失败 | 缺 Pillow 时整轮无产物 |
| `F-DEP-05` | `exit=1`、无 `result.json` | 同上（PIL + reportlab 一起缺） | 渲染链全缺时整轮无产物 |

- **根因（同一类）**：依赖与参数的校验发生在 `main.py` 的 `try/except` **之外**——
  模块顶层 `import` 与 `merge_spec` 调用都在保护范围外。`main.py` 里的四个
  `try/except` 保护的是"读 case / 读材料 / 规划 / 建稿"，管不到"解释器启动期"与"spec 合并期"。
- **后果**：编排器看到 `exit=1` 却拿不到 `result.json`，无法区分"输入坏"与"环境缺件"，
  与 `failure-modes.md` §0 的退出码契约不一致
  （那里写的 exit 1 = `status=partial` 且留 `uncertainty`，实测这四条不成立）。
- **现可用补救**：`--guard --case` 前置体检把这三类（参数形态 / 缺库 / 坏母版）
  **在执行前**变成显式 `BLOCKER`；`--guard --out` 后置核对把"没有 result.json"报成 `BLOCKER`。

> **为什么本版不直接改 `main.py`**：CLI 参数与退出码语义是平台契约的一部分
> （`failure-modes.md` §0 已被下游按字读）。本版的选择是**加一层守卫**而不是改主流程语义：
> `scripts/fault_inject.py --guard` 可在运行前后调用，把上面 7 条静默失败全部变成
> 可判读的报告，且**不改变任何既有 `--flag` 与退出码**。缺陷本身如实记录在此，
> 供维护者按"纯增量 + 逐条点名"的规矩后续修复。

## 3. 恢复演练（17 条真实恢复动作的实测结局）

> 注入只证明"会坏"，恢复演练证明"坏了有出路"。每条都是**真命令 + 真回读**，不是文案。
> `recovered` = 恢复动作跑通且状态回到预期；`unrecoverable` = 包内命令无法恢复（如实标注）。

| 故障 | 恢复动作 | 恢复后实测 | 结局 |
|-|-|-|-|
| `F-IN-05` | 把材料补回 case 目录并改回 `inputs.material` | `exit=0` / `success` | recovered |
| `F-IN-06` | 同上（补回非空材料） | `exit=0` / `success` | recovered |
| `F-IN-10` | 补回被删掉的 `task.md` | `exit=0` / `success` | recovered |
| `F-TPL-01` | 去掉坏 `--template`，回落内置 `templates/default.json` | `exit=0` / `success` | recovered |
| `F-TPL-02` | 同上 | `exit=0` / `success` | recovered |
| `F-TPL-03` | 同上（**这一条本是硬崩**，去掉坏参数后 exit=0） | `exit=0` / `success` | recovered |
| `F-TPL-04` | 移除损坏的 `template_pptx`，用内置模板重跑 | `exit=0` / `success` | recovered |
| `F-TPL-07` | `--max-slides 8` 覆盖过紧的上限 | `exit=0` / `success`（8 页） | recovered |
| `F-DEP-01` | `--no-chart` 把降级显式化（`figure.kind=table` + note） | `exit=0` / `success`，`figure.degraded=1` | recovered |
| `F-CTR-06` | 重跑 `main.py`，契约字段被重新回显 | `exit=0` / `success` | recovered |
| `F-IN-07` | `--guard` 运行前体检 + 运行后核对（把静默降级变成报告） | 守卫报告 1 条 `WARN/figure` | recovered |
| `F-TPL-05` | `--guard` 运行前体检 | 守卫报告 1 条 `DEGRADE/template_pptx` | recovered |
| `F-TPL-06` | `--guard` 运行前体检 + 运行后核对 | 守卫报告 2 条（`DEGRADE/starting_deck` + `WARN/consistency`） | recovered |
| `F-CTR-03` | `--guard` 运行前体检 | 守卫报告 1 条 `DEGRADE/contract` | recovered |
| `F-DEP-03` | `--guard` 运行后核对（判定 BLOCKER，不可建稿） | 守卫报告 1 条 `BLOCKER/result` | recovered |
| `F-DEP-04` | `--guard` 运行后核对 | 守卫报告 1 条 `BLOCKER/result` | recovered |
| `F-DEP-05` | `--guard` 运行后核对 | 守卫报告 1 条 `BLOCKER/result` | recovered |

**恢复结论**：17 条有恢复动作的故障 **17/17 都被恢复或被守卫判定**；
其中 12 条靠**改输入 / 换参数**直接回到 `success`，5 条靠**守卫**把"静默"变成"可判读的报告"。

**没有恢复动作的 11 条**都是"取证行"，本来就不需要恢复：
`case.json` 不可读（`exit=2` + 最小 `status=failed result.json` 就是正确行为，实测 4/4 都做到了）、
`max_slides=3` 边界（照做出 3 页是正确行为）、`output_contract` 缺省形态（没声明就不需要回显）、
`F-DEP-02`（reportlab 缺失只影响 PDF 预览，已如实进 `uncertainty` + `previews.warnings`）。

**最值得抄走的四条恢复动作**：

1. **坏模板参数 → 去掉参数**：回落内置 `templates/default.json` 比"猜着修模板"稳
   （实测 `F-TPL-01/02/03` 全部 `exit=0`）；
2. **材料缺件 → 补件重建**，而不是在缺件状态下硬拼 deck
   （`F-IN-05/06` 恢复后 `slide_count` 从 0 回到 6、`uncertainty` 归零）；
3. **图表降级 → `--no-chart` 显式化**：让降级有 `figure.kind=table` + `note`，
   不要留下"看起来本来就没图"的页面（`F-DEP-01` 恢复后 `figure.degraded=1`）；
4. **不可建稿 → 守卫判定 BLOCKER 并如实交 partial/failed**，
   绝不交一个"看起来成功"的空稿。

## 4. 守卫：把静默失败变成可判读报告

### 4.1 运行前体检（`--guard --case`）

```bash
python "$SKILL_DIR/scripts/fault_inject.py" --guard --case /input/case.json \
    --template /input/template.json      # --template 可选；传了就会一并体检
```

| 检查 | 等级 | 对应注入故障 |
|-|-|-|
| `case.json` 不存在 / 不能解析 / 顶层不是对象 | BLOCKER | `F-IN-01`–`F-IN-04` |
| `--template` 不是 JSON 对象 | BLOCKER（会 `TypeError` 硬崩且不写 `result.json`） | `F-TPL-03` |
| 缺 `python-pptx` / `Pillow` | BLOCKER | `F-DEP-03` / `F-DEP-04` / `F-DEP-05` |
| 缺 `matplotlib` / `reportlab` | DEGRADE（有降级路径） | `F-DEP-01` / `F-DEP-02` |
| `template_pptx` / `starting_deck` 不存在或打不开 | DEGRADE / BLOCKER | `F-TPL-04` / `F-TPL-05` / `F-TPL-06` |
| `output_contract` 形态或类型声明异常 | DEGRADE | `F-CTR-01`–`F-CTR-04` |

### 4.2 运行后核对（`--guard --out`）

```bash
python "$SKILL_DIR/scripts/fault_inject.py" --guard --out /app/output
```

| 检查 | 等级 | 抓的是哪条静默失败 |
|-|-|-|
| 没有 `result.json` | BLOCKER | S4–S7（硬崩无产物） |
| `status=success` 但 `slide_count=0` | BLOCKER | F5.3 状态不自洽 |
| `change_records` 有降级记录但 `uncertainty` 为空且 `status=success` | WARN | `F-TPL-06`（降级只记在 change_records） |
| 材料有数据表，但成稿没有图表/表格、也没有 `figure.note` | WARN | S1 `F-IN-07` 静默丢图 |
| `status=partial` 但 `uncertainty` 为空 | WARN | F5.4 |
| 有 `unverified_claims` 却标 `success` | WARN | F5.2 |
| G 门 `valid=false` | BLOCKER | 契约门未过 |

**守卫自身的实测效果**：

| 守卫跑在哪 | 实测结果 |
|-|-|
| 28 条故障的产物 | 7 条静默失败 **7/7 被抓到** |
| 健康产物（`F-CTR-05` 的输出，6 页、G 门全过） | **0 误报**，结论"通过" |
| 退出码 | 有 BLOCKER/WARN → `exit 1`；干净 → `exit 0` |

## 5. 本矩阵没有覆盖的注入面（诚实边界）

1. **并发 / 中断**：没有注入"运行到一半被 kill""两个进程同时写同一个 `--out`"。
   这类故障需要操作系统级信号注入，超出本台范围；相关推理只写在 `failure-modes.md`，
   **没有实测证据**，不要当已知结论引用。
2. **真实 PPTX 母版语义**：`F-TPL-04/05/06` 用的是"非 zip / 不存在"两种坏法，
   没覆盖"zip 合法但母版版式被删空"。后者要构造真实的畸形 PPTX，
   属二进制资源，不入包（平台只收 UTF-8 文本资源）。
3. **超大材料**：没有注入 GB 级材料 / 上万行数据表；性能边界未实测。
4. **字体缺失**：CJK 字体回落路径只做了"读 `previews.warnings`"的检查，
   没有真的卸掉系统字体（那需要改机器状态）。
5. **平台侧预检**：本台只在本地跑 `main.py`，**不模拟**平台预检
   （≤50 文件 / 单文件 ≤500KB / 合计 ≤2MB / 扩展名白名单）。
   那部分由 `validate_pkg.py <包>` 负责，与本文件互补。
6. **真机 Office**：环境里没有 PowerPoint / LibreOffice，所有"可打开"结论都是
   python-pptx 重开，不是 Office 渲染。

## 6. 三条可抄走的工程规则

1. **"有记录"必须按结构化字段判定**，不能按"日志里出现过这个词"。
   本台第一轮实现就是按裸文本匹配，结果把 JSON 键名（`"uncertainty"`）当成了留痕，
   26/28 行被误判为"非静默"；改成读字段内容后才露出真正的 7 条。
   **判据写松了比没有判据更危险。**
2. **降级必须落到指定字段**：`change_records` 记"我做了什么"，
   `uncertainty` 记"我为什么没能做得更好"，两者不能互相顶替
   （`F-TPL-06` 正好是只有前者、没有后者的活样本）。
3. **崩在 `try/except` 之外最危险**：模块顶层 `import` 与 spec 合并都在保护范围外，
   所以"前置体检"必须由独立脚本承担，不能指望主流程自己兜住。
