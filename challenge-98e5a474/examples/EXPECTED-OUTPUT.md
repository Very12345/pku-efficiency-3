# EXPECTED-OUTPUT — 示例案例应产出的文件与契约字段（文字版）

> 本文件替代旧版的 `examples/output/**` 预置产物。**包内不再预置任何
> 图稿或渲染件**（PDF/PNG/SVG 属于平台不支持的文件类型，且预置产物会
> 被误当"正式答案"）。示例产物一律由本 Skill **运行时现场生成**，
> 生成方法见 `examples/README.md` 与 `scripts/run_examples.py`。
>
> 所有示例产物都必须在 `result.json.status_notes` 或独立 README 中标明
> **"示例，非正式案例"**，不得冒充平台正式案例结果。

## 0. 一键复现（推荐）

```bash
python "$SKILL_DIR/scripts/run_examples.py" --out /tmp/sse-examples
# 依次跑 schematic → chart → edit，并对每份 result.json 跑 G1–G8 契约校验
```

## 1. schematic 示例（`examples/case.json`）

命令：

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
    --out /tmp/sse-examples/schematic
```

应产出（相对 `--out`）：

| 文件 | 角色（result.json `artifacts[].role`） | 内容要求 |
|-|-|-|
| `figure.svg` | `figure`（可编辑源文件） | 文字全部是 `<text>`（无 path 化）；语义图层 `layer-background/groups/edges/nodes/legend/footer`；元素带 `id` 与 `data-entity`/`data-relation`/`data-source`；`<metadata id="er-manifest">` 内嵌完整 ER 清单（供 `--edit-svg` 增量编辑） |
| `figure.png` | `preview`（渲染预览） | matplotlib 镜像同一 layout+manifest；18 cm 打印宽有效 DPI ≥300；色彩 RGB/RGBA |
| `figure.pdf` | `pdf`（导出件） | 矢量 PDF，页数与结构检查通过（字体嵌入审计为尽力而为） |
| `result.json` | — | 唯一评分产物，字段契约见 `references/OUTPUT_CONTRACT.md` |
| `layout.json`（`--work` 目录） | — | 布局中间产物（canvas/nodes/edges），过程证据 |
| `manifest.validated.json`（`--work` 目录） | — | 规范化 + 校验后的 ER 清单（CP1 输入） |

`result.json` 顶层应出现的键（与 `references/OUTPUT_CONTRACT.md` §1 逐项一致）：

```
case_id, skill, status, workorder, task_summary, figure_type, title,
main_result, artifacts, evidence, legend_mapping, data_mapping,
verification, determinism, sources, uncertainty, change_records,
status_notes, generated_at, generator, tool_versions
```

再叠加 `case.json.output_contract` 声明的键（本示例 5 个：
`case_id` / `status` / `figure_type` / `entities_relations` / `deliverables`，
四形态回显、禁 `null`）。

应通过的门：CP1 `spec_lint.valid = true`（0 fail）→ CP2 `verification.checks`
全 ok（0 fail / 0 warn / 0 ack）→ CP3 `validate_result.py` 输出 `VALID`
（G1–G8）→ `status = "success"`。

## 2. chart 示例（`examples/case_chart.json`）

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case_chart.json" \
    --out /tmp/sse-examples/chart
```

应产出：`figure.svg`（`svg.fonttype=none`，文字保持可编辑）+ `figure.png`
+ `figure.pdf` + `result.json`。数据来自 `examples/sources/data-table.csv`
的 4 个类别（ctrl / inhibitor-A / inhibitor-B / inhibitor-C）；图例、颜色
映射与坐标单位均由该表生成，`data_mapping` 应逐类别列出颜色，调色板长度
≥ 类别数，`data_mapping.unit` 出现在轴标签上（G8：不得出现表外类别）。

## 3. edit 示例（`examples/case_edit.json`）— 源文件级编辑

编辑示例**必须以上一步真实生成的 SVG 为输入**（包内不预置 SVG）：

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case_edit.json" \
    --edit-svg /tmp/sse-examples/schematic/figure.svg \
    --out /tmp/sse-examples/edit
```

应产出：同名 `figure.svg`/`figure.png`/`figure.pdf` + `result.json`，其中：

- `change_records` 恰好 3 条，动作依次为 `rename`（E2 → `TNFR1 (receptor)`）、
  `relabel`（R5 标签显式化）、`note`；每条含 before→after 与 reason；
- **未改动元素保持原样**（实体/关系数不变，其余 `data-entity` 节点的名称与
  位置与输入 SVG 一致）；
- 编辑后重跑 CP2 + CP3 仍为 `success` / `VALID`（旧标签无残留）。

## 4. 失败分支的期望产物（同样要真跑，不许声称）

| 场景 | 期望 |
|-|-|
| `--case` 指向不存在的文件 | 退出码 2，stderr/stdout 明确 `FATAL`，不写产物 |
| `--case` 指向目录但无 case-like JSON | 退出码 2，`no case.json found under directory: …` |
| case 无 `manifest` 且无 `entities/relations`，且 work 区无 `entities.json` | 退出码 1，写出 `status=failed` 的 `result.json`（`pipeline` fail 明细） |
| manifest 有未知 kind / containment 未用分组 / 图例缺项 | CP1 `spec_lint.valid=false` → `status=partial`，退出码 1，明细在 `verification.spec_lint.issues` |
| 无 CJK 字体 | `font.cjk` warn（或 `render.cjk_ok=false`），SVG 文字仍在，`uncertainty` 记录 |
| 编辑目标 SVG 无内嵌清单 | 退出码 2，明确"需先用本 Skill 生成"的说明 |

## 5. 已知的示例外差异（如实标注）

- 预览件是**语义一致、非逐像素**的 matplotlib 镜像（无 cairosvg 环境）；
- PDF 字体嵌入审计为尽力而为；
- 示例的实体名/数值只来自 `examples/sources/` 下的合成演示材料，**不是
  真实论文数据**，不可用于任何正式结论。
