# DECISION-CASES.md — 20 个决策用例（期望判决 vs 实测观测值）

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
