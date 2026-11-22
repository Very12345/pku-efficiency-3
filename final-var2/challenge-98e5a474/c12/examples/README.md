# examples — 最小调用示例与**对照夹具**（示例，非正式案例）

> 本节全部为**合成演示**，仅说明接口与完整使用流程，**不冒充、不等同于平台
> 正式案例结果**。正式案例由组织方提供，平台以固定 3 案例运行本 Skill。
>
> **这组示例同时是 `references/GAIN-PROTOCOL.md` 的对照夹具（F6：固定不改）。**
> 改夹具等于改题，任何对照读数都会作废。

## 三个示例

| 文件 | 演示能力 | 对照记录里的角色 |
|-|-|-|
| `case.json`（schematic） | 机制/信号通路示意图：实体 6、关系 5、分组 3、图例 3；产出可编辑 SVG + PNG + PDF + `result.json` | 协议 R1/R2/R3 的输入；同时演示契约四形态回显（声明 5 个键 → `""`/`[]`/`{}`/`0`/`false`） |
| `case_chart.json`（chart） | 数据表驱动图表：图例/颜色直接来自 `sources/data-table.csv` 的类别 | 协议 R4（三示例端到端）与 **R6（改数据后重跑）**的输入 |
| `case_edit.json`（edit） | 源文件级编辑：对**上一步真实生成**的 `figure.svg` 做增量修改，before→after 写入 `change_records` | 协议 R10（正向 7 条记录）与 **R11（目标不存在 → 0 条记录却不报错）**的输入 |

## 运行（自定位，任意 cwd 可跑；产物写在包外）

```bash
SKILL_DIR="$(cd "$(dirname "<本 SKILL.md 的实际路径>")" && pwd)"

# ① 三示例端到端 + 契约门（协议 R4：实测 exit 0，墙钟 ≈5 s）
python "$SKILL_DIR/scripts/run_examples.py" --out /tmp/gp-examples

# ② 单例 + 契约门（协议 R1/R3，即对照记录里的 B 臂）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out /tmp/gp-a
python "$SKILL_DIR/scripts/validate_result.py"     --case "$SKILL_DIR/examples/case.json" --result /tmp/gp-a/result.json

# ③ 确定性双跑（协议 R5）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples"     --out /tmp/gp-d1 --fixed-time 2026-01-01T00:00:00+0800
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples"     --out /tmp/gp-d2 --fixed-time 2026-01-01T00:00:00+0800

# ④ 编辑（协议 R10/R11）
python "$SKILL_DIR/scripts/main.py"     --case "$SKILL_DIR/examples/case_edit.json"     --edit-svg /tmp/gp-a/figure.svg --out /tmp/gp-edit
```

以上命令的实测退出码与读数见 `TEST.md` §M3–§M7；对照口径见
`references/GAIN-PROTOCOL.md` §1。

## 示例材料的性质

`sources/figure03-note.md` 与 `sources/data-table.csv` 是**为演示写的合成材料**
（内容自洽、句式模仿真实论文图注），**不是任何真实论文的数据**。
用它们跑出来的图只能作为接口演示，**不得**当作正式案例答案提交。
