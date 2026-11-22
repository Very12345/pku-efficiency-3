# examples/ — 最小调用示例（**示例，非正式案例**）

本目录是**流水线的最小调用示例**：一组虚构输入 + 一份纯文字的结果清单，
用于说明接口、调用方式与完整使用流程。

| 文件 | 说明 |
|-|-|
| `case.json` | 最小案例输入（虚构材料：蛋白质二级结构预测），声明 `output_contract` 待回显字段（含 bool 形态 `is_example`） |
| `task.md` | 任务说明（受众/时长/页数/交付要求） |
| `material.md` | 虚构研究材料（摘要/引言/方法/结果/讨论局限/结论） |
| `results.csv` | 虚构数据表（Q3/Q8/SOV/参数/时延），供图表重绘与数字核验 |
| `edit_demo.json` | 演示局部编辑操作（`update_bullet` / `add_note` / `reorder_pages`） |
| `EXPECTED-OUTPUT.md` | **纯文字**列出本示例应产出的全部文件（含二进制产物清单）与契约字段——替代原先随包的 `.pptx/.png/.pdf` 示意件 |
| `output/` | 一次**真实运行**产生的**文本**产物副本（`.example.` 命名；二进制产物不入包，见 `EXPECTED-OUTPUT.md`） |

> ⚠ **本目录全部材料为虚构示例**，仅用于演示 Skill 接口；**它们不是、也不
> 代表平台正式 3 个固定案例的输出**。正式案例由平台提供，Skill 在运行时依据
> 实际输入重新生成全部产物，包内不含任何预制答案。

## 复跑命令（自定位，cwd 不是技能根目录也能跑）

先确定技能根目录（含 `SKILL.md` 的目录）；平台安装形态下它就是
`/skills/weekly-skill`：

```bash
SKILL_DIR="${SKILL_DIR:-/skills/weekly-skill}"          # 或改成你的实际安装路径
OUT="${OUT:-/tmp/ppt-example-out}"                      # 输出目录（包外，避免污染技能包）

# 1) 完整流水线
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out "$OUT"

# 2) CP4 契约校验（G1–G8，exit 0 = 通过）
python "$SKILL_DIR/scripts/result_tool.py" --result "$OUT/result.json" \
    --out-dir "$OUT" --case "$SKILL_DIR/examples/case.json" \
    --envelope "$SKILL_DIR/templates/result_envelope.json"

# 3) 产物自检（all_pass=true 为通过）
python "$SKILL_DIR/scripts/selftest.py" --out "$OUT" --case "$SKILL_DIR/examples/case.json"

# 4) 局部编辑 + 版本归档（演示稿迭代）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
    --out "${OUT}-edit" --edit "$SKILL_DIR/examples/edit_demo.json" --version v2
```

预期：步骤 1 打印 `STATUS=success case_id=ppt-6ad93034-example-001 …` 且
exit 0；步骤 2 打印 `{"valid": true, …}` 且 exit 0；步骤 3 打印
`all_pass: true`。本机实测记录（含退出码与产物清单）见
[`../TEST.md`](../TEST.md)；应产出的文件清单见
[`EXPECTED-OUTPUT.md`](EXPECTED-OUTPUT.md)。
