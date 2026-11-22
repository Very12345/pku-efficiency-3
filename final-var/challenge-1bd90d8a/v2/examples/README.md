# examples/ — 最小示例（合成输入，非平台正式案例）

本目录是 Skill 自带的**最小可跑示例**，用途只有一个：让使用者在**不接触正式案例**的
情况下验证接口、跑通 CP1–CP6 全链路、看清 `result.json` 的契约形态。

> **正式评分由平台执行**：平台固定 3 个案例（`/input/case.json` + `/input/task.md` +
> 材料），并以相同内容分别交给基础 Agent 与加载本 Skill 的 Agent。
> 本目录的示例**不是**那 3 个案例，也**不得**当作正式案例的答案使用。

## 1. 输入文件（全部是自拟的合成文本，非真实实验数据）

| 文件 | 内容 | 合成声明 |
|-|-|-|
| `case.json` | 示例案例定义：`fig-01` panel（bar + line，`style: nature`）+ `fig-02` network；含 `output_contract`（四形态兼容）与 `manual_confirmations` | 案例、图规格、p 值均为演示自拟 |
| `task.md` | 示例任务说明（要两张图、约束：图元可溯源/轴带单位/显著性只转述/实体名以原文为准） | 示例 |
| `data.csv` | 8 行合成数据：`dose_mg_kg, time_h, mean_um3, se_um3, n` | 数值为演示用，**非真实实验测量** |
| `entities.json` | 7 节点 / 7 关系的 Wnt 通路简化实体表（含 `cite` 来源与手工布局坐标） | 演示用通路骨架，不代表文献结论 |
| `material.md` | 生物源材料写法示例：`ENTITY:` / `REL:` 显式行语法 + 自然语言段落（后者仅作词表候选，需对照原文确认） | 示例 |
| `output/` | **真实运行产物**中的 5 个契约 JSON（图/预览不入包，见下） | 由本 Skill 在示例输入上实际运行产生 |

## 2. 怎么跑

`$SKILL_DIR` = 本包所在绝对路径（脚本自定位，**cwd 不必是技能根目录**）：

```bash
python $SKILL_DIR/scripts/main.py --case $SKILL_DIR/examples/case.json --out <OUT> --style nature
python $SKILL_DIR/scripts/check_contract.py --result <OUT>/result.json --case $SKILL_DIR/examples/case.json
python $SKILL_DIR/scripts/figcheck.py --dir <OUT> --case $SKILL_DIR/examples/case.json
python $SKILL_DIR/scripts/mapcheck.py --dir <OUT> --case $SKILL_DIR/examples/case.json
python $SKILL_DIR/scripts/verify_rerun.py --case $SKILL_DIR/examples/case.json --out <OUT>
```

期望：四条命令全部 exit 0，`result.json.status = completed`，G1–G8 全过，
mapcheck `0 mismatched / 0 unmatched`。完整预期产物清单见 `EXPECTED-OUTPUT.md`。

## 3. 为什么本目录里看不到图

平台预检只接受 UTF-8 文本资源（`*.svg`/`*.png`/`*.pdf` 属不支持类型），因此本包
**不预置任何图或预览**：`figure-*.svg/png/pdf` 一律在运行时由 `scripts/main.py`
现场生成。`output/` 里保留的 5 个 JSON 是同一场景真实运行产生的报告，
归档时只做了两处路径净化（详见 `EXPECTED-OUTPUT.md` §5）。

## 4. 复用建议

- 换数据：把 `data.csv` 换成自己的表，按列名改 `case.json` 的 `x/y/error/filter`
  即可出图（列语义缺省会自动推断，见 `references/workorder-field-map.md`）。
- 换样式：`case.json` 里写 `"style": "cell"` 等命名预设，或加 `templates/journal_styles.json` 新键。
- 做机制图：按 `material.md` 的 `ENTITY:` / `REL:` 行语法准备材料，或用 `entities.json`
  直接给节点坐标（复杂通路建议手给 `x/y`，见 `SKILL.md` D13）。

## 5. 对照工具（`baseline_agent.py` / `measure_ab.py`）—— 本版的核心资产

这两个脚本把「加载本 Skill 到底带来了什么可测的改变」做成**可复跑的实验**。
完整协议（公平性条件、指标定义、归一化规则、边界声明）见
`references/GAIN-PROTOCOL.md`；这里只说怎么用。

### 5.1 两个角色

| 脚本 | 角色 | 产物 |
|-|-|-|
| `baseline_agent.py` | **条件 A（基准做法）**：读 `case.json` → 取第一张图的 panel spec → matplotlib 默认样式直接出 PNG + `summary.json`。刻意采用最常见的默认选择，**不刻意做差** | `figure.png`、`summary.json` |
| `measure_ab.py` | **判定器**：12 项机器可判定指标（质量 8 / 审计 3 / 确定性 1），每项给出通过与否 + 可复算计数 | stdout JSON（`--write` 可落盘） |

### 5.2 怎么跑（照抄）

```bash
S=$SKILL_DIR; T=<临时目录>; mkdir -p $T/condA $T/condA2 $T/condB $T/condB2

python "$S/examples/baseline_agent.py" --case "$S/examples/case.json" --out $T/condA
python "$S/examples/baseline_agent.py" --case "$S/examples/case.json" --out $T/condA2
python "$S/scripts/main.py" --case "$S/examples/case.json" --out $T/condB  --work $T/wB  --style nature
python "$S/scripts/main.py" --case "$S/examples/case.json" --out $T/condB2 --work $T/wB2 --style nature

python "$S/examples/measure_ab.py" --label A_baseline --case "$S/examples/case.json" --out $T/condA --run2 $T/condA2 --write $T/m-A.json
python "$S/examples/measure_ab.py" --label B_skill    --case "$S/examples/case.json" --out $T/condB --run2 $T/condB2 --write $T/m-B.json
```

期望：A **1/12**、B **12/12**（逐项数字见 `references/GAIN-PROTOCOL.md` §5.2）。

### 5.3 三条使用纪律

1. **两边同输入、同导出参数**，并把参数写进报告 —— 不做"悄悄调参"。
2. **指标只允许依赖文件字节或可复算计数**；主观项（美观、专业度）不进指标集。
3. **必须公布自己不占优的项**：本包里条件 A 也通过了 Q12（它的 2 个产物都不含时间戳）。
   只报赢的项就是选择性报告。

### 5.4 这两个脚本**不是**评分材料

它们读的是本目录的**合成示例**，产出自拟案例上的图与指标 JSON，与平台案例无关。
题面明写"文字自述不能替代实际运行证据"，因此本包**不据此宣称任何平台增益百分比**。
