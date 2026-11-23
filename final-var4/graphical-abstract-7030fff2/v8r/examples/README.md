# examples/ — 最小调用示例（合成案例，非正式案例）

> **本目录下的案例、材料与输出全部是合成的**，用于演示 Skill 接口与完整调用流程。
> 平台固定的 3 个正式案例由组织方提供（运行时挂载到 `/input/case.json` + `task.md`），
> **参赛者不提交正式案例、白板或预制答案**。本目录的任何内容都不得冒充正式案例结果。

## 文件

| 文件 | 作用 |
|-|-|
| `case.json` | 示例案例输入：`case_id / title / source_material / entities / relations / data / figure_constraints / output_contract` |
| `task.md` | 示例任务说明，含 `# 研究问题 / # 方法 / # 结果 / # 结论` 小节（按语义映射到四面板） |
| `material.md` | 示例科研材料：数值与机制关系的真实来源（`文件名:行号` 即 `data-src` 的定位依据） |
| `plan.example.json` | 已定稿的设计方案（方案先行 `--plan` 输入；四要素已填一句话说明） |
| `EXPECTED-OUTPUT.md` | **运行本示例后应产出的文件清单与契约字段（纯文本说明，替代预置二进制产物）** |
| `output/` | 本包在**本示例上实际运行**产生的文本产物（`result.json / spec.json / content.json / audit.json / render_log.json`），供对照；**已标注为示例，且路径已归一化为相对路径** |

## 三步跑通（cwd 任意，命令自定位）

```bash
# 1) 指定技能根目录（官方评测容器为 /skills/weekly-skill；本机为解压后的目录）
SKILL_DIR="$(pwd)"                     # 若当前就在技能根目录；否则写绝对路径
while [ ! -f "$SKILL_DIR/SKILL.md" ] && [ "$SKILL_DIR" != "/" ]; do SKILL_DIR="$(dirname "$SKILL_DIR")"; done

# 2) 方案先行（可选但推荐）：生成方案骨架 → Agent 按材料填充 four_elements
python "$SKILL_DIR/scripts/scaffold.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/plan.json

# 3) 出图（默认流程 / 带定稿方案）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/ga-out
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
       --plan "$SKILL_DIR/examples/plan.example.json" --out /tmp/ga-out-plan
```

两条命令都应 **exit 0** 且 `/tmp/ga-out*/result.json` 的 `status` 为 `success`
（示例案例四要素齐全、无缺值、无越界）。期望产物见 `EXPECTED-OUTPUT.md`。

## 关于 `output/` 里的 JSON

- 它们是**本包流水线在该合成示例上的真实运行结果**（不是手写、不是正式案例）；
- 其中的绝对路径已**归一化为相对技能根的相对路径**（如 `examples/task.md`），
  以便在任意机器/容器里阅读；实跑时 `content.json` 的 `provenance.source_files`
  会显示当次运行的实际路径，这是预期差异；
- `output/` 中**不含**渲染件（`.svg/.png/.pdf`）——本包不携带任何二进制或 `.svg` 资源，
  渲染件一律由 `scripts/svgbuilder.py` + `scripts/preview.py` **运行时生成**；
- `examples/output/result.json`、`audit.json` 等文件名与实跑产物同名，这是为了直接对照契约；
  正式案例的评分产物由平台在 `/app/output/result.json` 生成。

## 本版附带的契约矩阵报告：`contract_matrix.example.json`

该文件是 `scripts/contract_matrix.py` 把 **26 种契约形态与边界值**逐个注入**本示例案例**
之后真跑得到的**原始矩阵**（26 次真实出图），只加了 `_label` 字段说明它是示例：

| 关键字段 | 值 |
|-|-|
| `summary.rows` / `ok` / `mismatch` / `silent_failure` / `crash` | 26 / 26 / 0 / 0 / 0 |
| `summary.nulls_in_result_top_level` / `nulls_in_contract_fields` | 0 / 0 |
| `summary.check_contract_failures` | 0 |
| `summary.rows_with_nested_null_only` | 26（无 `--plan` 时 `plan.hash=null`，属已声明的形态） |
| `rows[].echo_observed` | 每行的回显位置（`top` / `echo`）与 JSON 类型 |

复跑同一份矩阵：

```bash
python "$SKILL_DIR/scripts/contract_matrix.py" --out /tmp/cm --fail-on strict
```

逐行期望、判级口径与静默通过清单见 `references/CONTRACT-MATRIX.md`。
