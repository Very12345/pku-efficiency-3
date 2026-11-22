# 最小示例（示例，非正式案例）

本目录演示 Skill 的最小调用接口；**所有内容均为合成示意数据，不是任何真实
论文结果，平台正式案例由组织方提供**。包内不含预制答案：示例产物由本 Skill
在你自己的机器上现场跑出来。

## 输入

| 文件 | 作用 |
|-|-|
| `case.json` | 最小案例：Cu-ZnO/γ-Al₂O₃ 催化剂 CO₂ 加氢制甲醇（合成数据），10 页 / 12 分钟 / zh，带 `output_contract`（7 个契约键） |
| `task.md` | 任务说明（示例） |
| `material.md` | 材料原文（含 `# 方法/结果/…` 小节与图注，供 `文件:行` 定位） |
| `figs/fig1.png` `figs/fig2.png` | 两张**运行时合成**的几何示意位图（带 `SCHEMATIC / 示意` 水印，不含伪造数值）——由 `scripts/make_synthetic_inputs.py` 现场生成，不随包分发 |

## 调用方式

下面的命令在**任意 cwd** 下都能跑：`$SKILL_DIR` 是本包根目录（平台把 Skill 装在
`/skills/weekly-skill`），脚本自身用 `os.path.dirname(__file__)` 定位 Skill 根，
所有输入输出路径都由命令行显式给出。

```bash
SKILL_DIR=<本包根目录>
RUN=<任意可写目录>                     # 示例材料会被复制到这里，包内保持只读

# 0) 准备可跑的示例输入：复制示例目录 + 现场合成两张占位图（Skill 资源只允许文本）
cp -r "$SKILL_DIR/examples" "$RUN/examples"
python "$SKILL_DIR/scripts/make_synthetic_inputs.py" --dir "$RUN/examples"

# 1) 一键全流程（两阶段：方案 → 执行 → 验证）
python "$SKILL_DIR/scripts/main.py" --case "$RUN/examples/case.json" \
    --task "$RUN/examples/task.md" --out "$RUN/out"
```

平台正式运行时不走示例材料，直接指向挂载的输入（命令同上，只换路径）：

```bash
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md \
    --work /app/work --out /app/output
```

## 示意输出（真实运行产物）

`$RUN/out/` 会得到完整一套产物；`examples/output/` 里保留的只是其中的**文本**部分
（二进制按平台硬门随包分发）：`result.json`、`summary.txt`、`render_log.json`，
以及两个说明文件 `_LABEL_example.txt` / `_PREVIEW_ARE_SCHEMATIC.txt`。
逐文件清单与实测内容见 **`EXPECTED-OUTPUT.md`**；要点：

| 文件 | 说明 |
|-|-|
| `<case>_deck.pptx` | 可编辑源（10 页、逐页备注、页脚页码、图表 contain-fit；运行时生成） |
| `<case>_cover_preview.png` | 封面预览（PIL 示意图，见文件内 SCHEMATIC 标注；运行时生成） |
| `<case>_slides_contact_schematic.png` | 全册联系表示意图（运行时生成） |
| `result.json` | 结构化结果（output_contract 7 键全部回显顶层 + case_id/status/sources/uncertainty/change_records；status=success） |
| `spec.json` | 页结构方案（与 pptx 同一计划，复跑可核对） |
| `adopt_plan.json` | **适配方案**（模板审计 + 页→版式分配 + 批量规则 + 图表计划） |
| `content.json` / `audit.json` / `render_log.json` / `summary.txt` | 抽取 / 自查 / 渲染日志 / 摘要 |
| `_runtime/builtin.pptx` | 案例未给模板时现场生成的回退模板（已给模板时不产生） |

方案样例（`plan.sample.json` / `adopt_plan.sample.json`）即由上述真实运行生成
并加注"示例"标识，不是预制答案。

## 验证命令

独立复核（两个校验器都不信任 `result.json` 的自述，会从磁盘重扫真实产物）：

```bash
# 契约字段齐备 → VALID
python "$SKILL_DIR/scripts/validate_result.py" \
    --case "$RUN/examples/case.json" --result "$RUN/out/result.json"

# CP3 硬性门 G1–G8 → {"valid": true}
python "$SKILL_DIR/scripts/check_contract.py" \
    --result "$RUN/out/result.json" --out-dir "$RUN/out" --case "$RUN/examples/case.json"
```

两项都必须 **exit 0**；任何一条不过，按 `references/failure-modes.md` 定位并把
偏差写入 `result.json.uncertainty`，不要静默继续。
