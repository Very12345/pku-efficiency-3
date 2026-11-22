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
