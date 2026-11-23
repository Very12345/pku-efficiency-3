# examples/output — 示意结果副本（示例，非正式案例）

本目录是 `examples/case.json` + `examples/deck-spec.json` 用**本包真实运行**后的
**文本类结果副本**，文件名统一带 `.example.` 标记。它们**不是**平台 3 个固定案例
的输出；正式案例由平台提供，Skill 在运行时依据实际输入重新生成全部产物。

| 文件 | 说明 |
|-|-|
| `result.example.json` | 真实 `result.json`（19 个顶层契约字段：`output_contract` 回显 + `deck` + `spec_lint` + 双形态证据映射 + `uncertainty` + `run_meta`）。**仅路径类字段做了净化**（见下），其余值与运行结果一致 |
| `evidence_mapping.example.md` | 逐页证据映射表（每页 → 论文 p.1–p.4 的图/表/章节定位），由 `main.py` 生成 |
| `evidence_map.example.json` | 同一映射的机器可读形态（与 md 同源，均由同一 deck-spec 生成） |

**为什么没有 `.pptx` / `.png` / `.svg`**：题面硬约束规定技能资源只能是 UTF-8 文本文件
（≤50 个、单文件 ≤500KB、合计 ≤2MB、无符号链接），因此可编辑演示源、渲染预览与重建图
一律**运行时生成**、不随包携带。它们在本示例上的完整清单见 `../EXPECTED-OUTPUT.md`。

**净化说明（逐条）**：

- `deck.template.path`：运行机绝对路径 → `examples/template-example.pptx`
  （该模板本身也是运行期由 `scripts/make_template.py` 现产，不随包携带）；
- `sources[].path`：运行机绝对路径 → `examples/materials/paper-mini.txt`；
- `charts[].chart.file`：运行机绝对路径 → 文件名 `chart-Fig_1.png`（与 `--out` 同目录）；
- `run_meta.case_file` / `run_meta.spec_source`：→ `examples/case.json` / `examples/deck-spec.json`；
- `run_meta.preview_font` **保留** `C:/Windows/Fonts/msyh.ttc`：它是
  `scripts/preview.py` 中登记的**跨平台字体探测候选路径**之一（不是某次调试残留），
  在缺少该字体的机器上会被自动跳过并降级为 PIL 默认字体；
- 追加 `run_meta.example_note` 明确标注"本记录已净化、其余值为真实运行结果"。

复跑命令（任意 cwd，`$SKILL_DIR` = SKILL.md 所在目录）：

```bash
python "$SKILL_DIR/scripts/make_template.py" --out "$SKILL_DIR/examples"
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
  --spec "$SKILL_DIR/examples/deck-spec.json" --out "<空输出目录>"
python "$SKILL_DIR/scripts/export_check.py" --result "<out>/result.json" \
  --out-dir "<out>" --case "$SKILL_DIR/examples/case.json"
python "$SKILL_DIR/scripts/check_contract.py" --result "<out>/result.json" \
  --contract "$SKILL_DIR/references/OUTPUT_CONTRACT.md"
```

注意：`examples/materials/paper-mini.txt` 为**合成示例论文**（人物/机构/数据均虚构），
仅用于演示接口；正式运行时 Agent 必须依据案例实际提供的论文与模板重新生成全部内容。
