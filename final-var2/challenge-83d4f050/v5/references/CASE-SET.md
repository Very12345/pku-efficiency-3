# CASE-SET.md — 合成案例题集（3 案例 · 逐案实测 · 含失效边界）

> **本文件是"题集 + 实测台账"**：每个案例给出**输入**、**期望产出结构**、**可接受区间**、
> **难度层**，并附**本机实跑结果**（退出码 / status / gates / 实体边数 / 告警 / 契约回显）。
> 表内数字全部来自包外副本上的真实运行，复跑命令见 §5；**没有手写数字**。
>
> ⚠ 本目录三个案例都是 **Skill 自带的合成案例**，与平台固定 3 个正式案例**无关**；
> 正式案例的材料由组织方提供，**禁止**把这里的实体/边/数值抄进正式输出。

## 1. 题集总览

| 槽位 | 案例 id | 题材 | 主实体类型 | 难度层 | 材料形态 | 关键考点 |
|---|---|---|---|---|---|---|
| 内置 | `example-egfr-mapk` | 受体酪氨酸激酶级联（EGFR→RAS→RAF→MEK→ERK→MYC） | 蛋白/复合物 | **L1** | 实体表 + 关系节 + 数据映射 | 基线示例：线性主链 + 一个负反馈 + 同名蛋白按区室拆分 |
| 新增 A | `synth-immune-synapse-tcr` | 免疫突触近膜信号（TCR–CD3→ZAP70→LAT→PLCγ1→钙→NFAT 入核） | 复合物/激酶/第二信使 | **L2** | 实体表（**无数值列**）+ 关系节 12 条 | **材料无数值 ⇒ 禁止颜色数据映射**；跨膜募集导致的"逆流边"；同一蛋白跨区室 |
| 新增 B | `synth-plant-hormone-mirna` | 植物激素 + 转录后调控（乙烯→EIN3→ERF1 / miR164→NAC1） | **基因 / RNA** / 蛋白 | **L2** | 实体表（**含数值列**）+ 关系节 8 条 | **有数值 ⇒ 必须画色带**；基因/转录本类型判定；**并行分支**不得串联；无胞外实体 |

**三个槽位刻意互补**：内置案例检验"标准通路图"；案例 A 检验"没有数值时不许编造数据编码"；
案例 B 检验"有数值时必须真的编码"与"主实体不是蛋白"（基因/RNA 类型与书写）。
把 A 与 B 放在一起，任何"只会一种套路"的做法都会在其中一侧暴露。

## 2. 逐案规格（输入 → 期望产出结构 → 可接受区间）

### 2.1 内置示例 `example-egfr-mapk`（L1）

- **输入**：`examples/case.json` + `examples/task.md` + `examples/materials/example_material.md`
  + 已核验规格 `examples/model.example.json`。
- **期望产出结构**：`result.json`（信封 19 键 + `custom_demo_field`/`custom_list_field` 两个自定义字段，
  按四形态回显且**无 null**）+ `diagram.svg`（7 层 `layer-*`）+ `diagram.png` + `diagram.pdf`
  + `model.json` + `topology.json` + `legend_audit.json`，共 **7 件**。
- **可接受区间**：`status=success`、`gates 8/8`、`self_check.failures=0`、`self_check.warnings=0`、
  实体 9 / 边 9 / 区室 4、`data_mapping.field="表达量"`。
- **难度层 L1**：线性主链 + 一个反馈环；材料结构化，草稿抽取器可解析。

### 2.2 案例 A `synth-immune-synapse-tcr`（L2 · 无数值）

- **输入**：`examples/cases/immune-synapse/{case.json,task.md,material.md,model.json}`。
- **期望产出结构**：同上 7 件；`output_contract` 三个自定义字段
  （`figure_spec_version` / `required_compartments` / `expected_export_formats`）全部回显。
- **可接受区间**：`status=success`、`gates 8/8`、**`self_check.failures=0`**、
  `self_check.warnings ≤ 3`（本案例实测恰为 **3** 条，逐条可解释，见 §3.2）、
  实体 12 / 边 12 / 区室 4、`data_mapping.field=""`（**材料无数值 ⇒ 不许编码数据**）。
- **难度层 L2**：跨膜受体 + 募集事件（存在"由胞质指向膜"的边）+ 同一蛋白跨区室（NFAT / 核内 NFAT）
  + 抑制边（SHP-1）+ **无数值分支**。

### 2.3 案例 B `synth-plant-hormone-mirna`（L2 · 有数值）

- **输入**：`examples/cases/plant-hormone/{case.json,task.md,material.md,model.json}`。
- **期望产出结构**：同上 7 件；`output_contract` 三字段全部回显；
  图例必须**画出色带并标"低/高"**（材料给了 0.31–0.88 的表达量）。
- **可接受区间**：`status=success`、`gates 8/8`、`self_check.failures=0`、`self_check.warnings=0`、
  实体 8 / 边 8 / 区室 **2**（无胞外实体）、`data_mapping.field="表达量"`。
- **难度层 L2**：主实体是**基因与转录本**（不是蛋白）；两条并行分支（ERF1 / miR164）；
  两条负反馈（含弱证据虚线）；**有数值分支**。

## 3. 逐案实测结果（2026-11-22 +08，包外副本，Python 3.13 + matplotlib + Pillow）

| 案例 | 路径 | 实测 exit | status | gates | 实体/边/区室 | SVG 层 | PNG/PDF | failures/warnings | 告警 id | data_mapping.field | 契约字段回显（四形态） | 用时 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `builtin-example-egfr-mapk` | 已核验规格 | `0` | `success` | `8/8` | 9/9/4 | 7 | 有 / 有 | 0 / 0 | 无 | `表达量` | 无 | 1.16s |
| `case-a-immune-synapse` | 已核验规格 | `0` | `success` | `8/8` | 12/12/4 | 7 | 有 / 有 | 0 / 3 | P03, P07, L03 | `` | figure_spec_version→"", required_compartments→[], expected_export_formats→[] | 1.2s |
| `case-b-plant-hormone` | 已核验规格 | `0` | `success` | `8/8` | 8/8/2 | 7 | 有 / 有 | 0 / 0 | 无 | `表达量` | figure_spec_version→"", required_compartments→[], expected_export_formats→[] | 1.33s |
| `builtin-example-egfr-mapk` | 草稿路径（自动抽取，未人工核验） | `2` | `partial` | 8/8 | 9/9/4 | - | - | - | - | - | - | 1.12s |
| `case-a-immune-synapse` | 草稿路径（自动抽取，未人工核验） | `2` | `partial` | 8/8 | 12/12/4 | - | - | - | - | - | - | 1.32s |
| `case-b-plant-hormone` | 草稿路径（自动抽取，未人工核验） | `2` | `partial` | 8/8 | 8/8/2 | - | - | - | - | - | - | 1.19s |

### 3.1 两份独立 CLI 的复查（对"已核验路径"的产物）

| 案例 | `check_contract.py --result <out>/result.json --case <case.json>` | `validate_figure.py --out <out>` |
|---|---|---|
| `builtin-example-egfr-mapk` | exit `0`（`contract|ok|case=example-egfr-mapk|status=success|checks=7`） | exit `0`（`standalone-verify|ok=True|fails=0|warns=0`） |
| `case-a-immune-synapse` | exit `0`（`contract|ok|case=synth-immune-synapse-tcr|status=success|checks=7`） | exit `0`（`standalone-verify|ok=True|fails=0|warns=3`） |
| `case-b-plant-hormone` | exit `0`（`contract|ok|case=synth-plant-hormone-mirna|status=success|checks=7`） | exit `0`（`standalone-verify|ok=True|fails=0|warns=0`） |

### 3.2 案例 A 的 3 条 warn：为什么是可接受的，以及它教了什么

| warn | 含义 | 本案例为何出现 | 处置 |
|---|---|---|---|
| `P03` | 通路方向（是否存在逆流边） | `r3 ZAP70→TCR–CD3`、`r4 ZAP70→LAT` 是由胞质指向膜的**募集/磷酸化**事件，与"自上而下"的区室流方向相反 | 属**真实生物学**：膜募集事件本来就逆着区室流。审计只给 `warn` 不给 `fail`，Agent 需在 `uncertainty` 说明"方向来自材料原意" |
| `P07` | 逆流边未标注 `feedback` | 同上两条边不是反馈环 | 同上；若误标 `feedback=true` 反而会把募集事件说成反馈 |
| `L03` | 数据映射字段缺失 | 材料**没有**数值列 ⇒ `data_mapping.field=""` | **正确行为**：`legend_audit` 提醒"图例未声明数据映射"，而不是让包编造一个数值字段 |

> **这 3 条 warn 是案例 A 的设计目的**：它检验"审计给出告警时，Agent 是照抄告警、还是回头核对材料"。
> 结论写进 `uncertainty` 比把 `warn` 消掉更重要 —— 本案例的 `status` 仍是 `success`，因为 warn 不阻断。

## 4. 泛化到哪里会失效（如实声明，逐条可复验）

| # | 失效边界 | 具体表现（本机实测/代码依据） | 缓解 |
|---|---|---|---|
| F1 | **散文材料**（无实体表、无 `A 动词 B（证据）` 行） | `extract.py` 只认结构化语句；纯散文时 `method="manual-required"`，草稿路径 **exit 3 / failed** | 走 CP2b：Agent 读材料后手写 `model.json`，再 `--model-file` 重跑（本包 3 个案例都提供已核验规格，可直接对照格式） |
| F2 | **PDF / 扫描件** | 抽取器不解析 PDF（`read_text_files()` 直接跳过 `.pdf`）；需要外部工具抽文本 | 用工具抽文本另存 `.md`，或直接手工建规格（`extraction.method=manual`） |
| F3 | **枚举外的实体/边类型** | 规格里出现 `type="banana"` ⇒ schema 门 **exit 3 / failed**（**不会**被静默改写成 `other`） | 改规格，不改图；枚举见 `references/OUTPUT_CONTRACT.md` §6 |
| F4 | **契约字段只保证"形态"，不保证"语义"** | `output_contract` 里声明的字段**一定回显且非 null**，但管道没有真实值时按四形态填空（字符串→`""`、列表→`[]`）——所以案例 A/B 的 `required_compartments` 实测回显为 `[]` 而**不是**案例自己写的那两个区室 | 需要"真实值"的字段应由 Agent 在核验后填；或从 `result.json.scientific_content` 读真实结构（本包用 `counts.compartments` 与 `data_mapping.field` 作为真值来源） |
| F5 | **逆流边会被 warn 而不是 fail** | 案例 A 实测 `P03`/`P07`；若材料复杂（大量膜募集事件），warn 数量会上升 | warn 不阻断 success；但必须逐条在 `uncertainty` 说明，否则"结果可核验性"打折 |
| F6 | **数值退化/缺失** | 案例 A（无数值）`data_mapping.field=""` + `L03 warn`；若材料声明了数值但实体上无值，颜色映射会退回类型默认色 | 见 `references/failure-modes.md`；不要在无数值案例上强行插值 |
| F7 | **区室词表** | 区室名走 `COMPARTMENT_ALIASES` 归一；写"细胞质膜""核内"等非常规词会被归到默认或 `other` 并出 warn | 用材料原文 + 规范词表（`references/mechanism-spec.md` §4） |
| F8 | **图面规模** | 元素很多（粗估 > 40 实体）时布局会拥挤；`layout.warnings` 与 `D10` 规则负责提示，但**本包没有自动分图** | 拆子图或缩小字号；`layout.warnings` 必须写进 `uncertainty` |
| F9 | **字体/渲染环境** | 无 matplotlib ⇒ 只能交付 SVG（`partial`）；系统缺中文字体 ⇒ PNG 告警写 `export_checks`（SVG 不受影响） | 见 `references/failure-modes.md`；不要伪造 PNG/PDF |
| F10 | **契约自定义字段的类型** | 只覆盖 `str/list/bool/number/dict` 五种声明形态；声明成"对象数组"时按 `[]` 处理（D19 的降级分支） | 用四种基本形态声明；复杂结构放 `scientific_content` |

> **一句话总结泛化边界**：本 Skill 泛化的是**"实体—关系—区室—图例"这套结构**，
> 不泛化"从任意自然语言/PDF 里自动读懂机制"。材料越结构化，自动化程度越高；
> 材料越散文，越依赖 Agent 的 CP3 人工核验 —— 这是**刻意设计**（准确率优先于全自动）。

## 5. 复跑命令（任何人可复算）

```bash
export SKILL_DIR=/path/to/<package>          # 含 SKILL.md 的那一层
cp -r "$SKILL_DIR" /tmp/cases-skill          # 一律在包外跑，避免 __pycache__ 污染
cd /tmp

# 三个案例的"已核验规格"路径（期望 exit 0 / status=success / gates 8/8）
for c in "examples/case.json examples/model.example.json" \
         "examples/cases/immune-synapse/case.json examples/cases/immune-synapse/model.json" \
         "examples/cases/plant-hormone/case.json examples/cases/plant-hormone/model.json"; do
  set -- $c
  python3 /tmp/cases-skill/scripts/main.py --case /tmp/cases-skill/$1 \
      --model-file /tmp/cases-skill/$2 --out /tmp/out-$(basename $(dirname $1))
done

# 独立复查（每条都要 exit 0）
python3 /tmp/cases-skill/scripts/check_contract.py --result /tmp/out-examples/result.json \
        --case /tmp/cases-skill/examples/case.json
python3 /tmp/cases-skill/scripts/validate_figure.py --out /tmp/out-examples
```

## 6. 怎么再加一个新案例（复用步骤，对应"生态贡献"）

1. **建目录**：`examples/cases/<name>/`，放 `case.json`（含 `task`、`materials`、`output_contract`）、
   `task.md`、`material.md`、`model.json`（**已人工核验**，`extraction.verified_by_agent=true`）。
2. **选一个与现有案例互补的考点**（例如：多区室同名分子 / 只有抑制边 / 无膜受体 / 反馈环嵌套），
   并**明确它检验的是哪条规则**（对照本文档 §2 的"关键考点"列）。
3. **先跑草稿路径**观察抽取器能读到什么：
   `python3 $SKILL_DIR/scripts/main.py --case <新 case.json> --out /tmp/draft`；
   若 `manual-required`，说明材料是散文 ⇒ 这正是 F1 边界，应在 `model.json` 里人工补全。
4. **再跑已核验路径**，要求 `exit 0 / status=success / gates 8/8 / failures=0`；
   记录 `counts`、`self_check.warnings`、`data_mapping.field` 三个读数。
5. **把新案例追加到本文档 §1/§2/§3 的表里**，并如实写明它的**失效边界**（§4 的格式）。
6. 更新 `TEST.md` 的案例数，并复跑一次 `scripts/fault_inject.py` 确认故障矩阵未被影响。
