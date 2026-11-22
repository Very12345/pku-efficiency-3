# examples/ — 最小可运行示例（示范用，非正式案例）

> **这里的 case、材料、模型、输出全部是 Skill 自带的合成演示**，与平台固定 3 个正式案例
> **无关**。正式运行时平台会给出 `/input/case.json`、`/input/task.md` 和真实材料；
> **禁止**把本目录的实体/边/数值抄进正式输出（SKILL.md §9 反预制答案规则）。

## 目录内容

| 文件 | 作用 |
|-|-|
| `case.json` | 示例案例输入：`case_id`/`title`/`task`/`materials`/`render`/`output_contract`（含两个自定义契约字段，用于演示四形态回显） |
| `task.md` | 示例任务说明（要求覆盖的实体、边、图例、导出件） |
| `materials/example_material.md` | 示例科研材料：实体表 + 关系节 + 数据映射 + 图面约束（带行号可溯源） |
| `model.example.json` | **已人工核验**的机制规格（`extraction.verified_by_agent=true`），用于走"已核验路径" |
| `output/` | 在 `case.json` 上**实跑**得到的 JSON 产物（`result.json` / `model.json` / `topology.json` / `legend_audit.json`），用于展示契约与审计的真实结构 |
| `EXPECTED-OUTPUT.md` | 该示例案例应产出的完整文件清单与契约字段（文字形式；替代预置的图件） |

> **为什么 `output/` 里没有 SVG/PNG/PDF**：技能资源必须是文本文件，图件一律由
> `scripts/` 在运行时生成。要看到图，请按下面命令跑一次——产物会写进你指定的 `--out`。

## 题集（`examples/cases/`，本版新增）

除本目录的内置示例外，`examples/cases/` 还有两个**互补的合成案例**，完整规格与实测见
`references/CASE-SET.md`：

| 目录 | 题材 | 与内置示例的差别 | 难度层 |
|-|-|-|-|
| `cases/immune-synapse/` | 免疫突触 TCR 近膜信号 | 材料**没有数值列**（不许颜色编码）；含膜募集类逆流边；同一蛋白跨区室 | L2 |
| `cases/plant-hormone/` | 植物激素 + 转录后调控 | 主实体是**基因与 RNA**；材料**有数值列**（必须画色带）；两条并行分支 | L2 |

```bash
python3 "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/cases/plant-hormone/case.json" --model-file "$SKILL_DIR/examples/cases/plant-hormone/model.json" --out /tmp/out-b
```

## 怎么跑（自定位，任意 cwd）

```bash
export SKILL_DIR=/path/to/challenge-83d4f050        # 含 SKILL.md 的那一层
python3 "$SKILL_DIR/scripts/main.py" \
    --case "$SKILL_DIR/examples/case.json" \
    --model-file "$SKILL_DIR/examples/model.example.json" \
    --out /tmp/example-out
# 期望：exit 0（status=success，gates 8/8），/tmp/example-out 下出现 7 个文件
ls /tmp/example-out
```

对照路径（自动草稿、未人工核验 → `status=partial`、缺省 exit 2）：

```bash
python3 "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/example-draft
```

## 期望看到什么

- `result.json`：`status=success`、`gates` 8 项全 `pass`、`self_check.failures=0`、
  `output_contract` 的两个自定义字段回显到顶层且**无 null**；
- `diagram.svg`：7 个 `layer-*` 组，元素带 `data-id`/`data-type`/`data-source`；
- `topology.json`：P 系列检查（方向/区室/同名消歧/反馈环标注）；
- `legend_audit.json`：L/E 系列检查（图例覆盖、颜色⊆图例∪映射、虚线语义、数值溯源）。

完整字段清单见 `EXPECTED-OUTPUT.md`；实测记录与 sha256 见包根 `TEST.md`。
