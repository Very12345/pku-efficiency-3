# examples — 最小调用示例（示例，非正式案例）

> 本节全部为**合成演示**，仅说明接口与完整使用流程，**不冒充、不等同于平台
> 正式案例结果**。正式案例由组织方提供，平台以固定 3 案例运行本 Skill。
>
> **包内不预置任何产物**：PDF/PNG/SVG 属平台不支持的文件类型，且预置产物会被
> 误当"正式答案"。示例产物一律**运行时现场生成**，期望清单见
> `EXPECTED-OUTPUT.md`。

## 三个示例分别检验哪个机制

| 文件 | 演示能力 | 主要检验的机制 |
|-|-|-|
| `case.json`（schematic） | 机制/信号通路示意图：实体 6、关系 5、分组 3、图例 3；产出可编辑 SVG + PNG + PDF + `result.json` | **M1**（kind 必须可映射、containment 用分组）、**M2**（内嵌清单与 `data-*`）、**M4**（DPI/色彩/文字可编辑）、**M5**（字体结论） |
| `case_chart.json`（chart） | 数据表驱动图表：图例/颜色来自 `sources/data-table.csv` 的类别 | **M1**（调色板 ≥ 类别数、表外类别 = G8 INVALID）；改数据即重绘 |
| `case_edit.json`（edit） | 源文件级编辑：对**上一步真实生成**的 `figure.svg` 做增量修改 | **M2**（读内嵌清单做增量编辑）与其**盲区**（目标不存在时 `change_records` 为 0 但退出码仍 0） |

## 运行（自定位，任意 cwd 可跑；产物写在包外）

```bash
SKILL_DIR="$(cd "$(dirname "<本 SKILL.md 的实际路径>")" && pwd)"

# ① 三示例端到端 + 契约门
python "$SKILL_DIR/scripts/run_examples.py" --out /tmp/sse-examples

# ② 单例（M1/M2/M4/M5 一起被激活）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples" --out /tmp/sse-sch

# ③ 编辑（M2）：先出图，再在源文件上增量修改
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case_edit.json"     --edit-svg /tmp/sse-sch/figure.svg --out /tmp/sse-edit

# ④ 两个"推翻实验"：机制判据只有在能被推翻时才算被检验过
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples"     --edit-svg <一个没有内嵌清单的 svg> --out /tmp/sse-rej      # 期望 exit 2（M2）
python "$SKILL_DIR/scripts/spec_lint.py" --manifest <把某 kind 改成 gibberish 的清单>                                                                  # 期望 exit 1（M1）
```

各命令的实测退出码与读数见 `TEST.md` §V1–§V6。

## 示例材料的性质

`sources/figure03-note.md` 与 `sources/data-table.csv` 是**为演示写的合成材料**
（内容自洽、句式模仿真实论文图注），**不是任何真实论文的数据**。
用它们跑出来的图只能作为接口演示，**不得**当作正式案例答案提交。
