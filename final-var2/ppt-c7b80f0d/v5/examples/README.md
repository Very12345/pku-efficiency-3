# examples/ — 最小调用示例（合成案例，**非正式案例**）

本目录演示本 Skill 的接口与完整使用流程。**它不包含任何正式案例的答案**：
正式评分的 3 个固定案例由平台提供，Skill 在运行时依据 `/input/case.json` 与
`/input/task.md` 重新生成全部内容。

| 文件 | 作用 |
|-|-|
| `case.json` | 示例案例输入（case_id / 材料 / 模板 / 受众 / 页数上限 / `output_contract` 声明） |
| `task.md` | 示例任务说明（与正式案例同形态） |
| `deck-spec.json` | 示例页级方案（Agent 在真实案例里要先写这份方案，再跑生成） |
| `materials/paper-mini.txt` | **合成**论文材料（人物、机构、数值均虚构；仅用于打通管道） |
| `EXPECTED-OUTPUT.md` | 在示例案例上应产出的文件清单 + `result.json` 契约字段（**文字清单**，替代随包携带二进制产物） |
| `output/` | 由本 Skill 在示例案例上**实际运行产生**的示意结果副本（文本形态；二进制产物见 `EXPECTED-OUTPUT.md`） |

## 依赖

- Python ≥ 3.8；`python-pptx`（构建 deck）、`Pillow`（预览）；
- `matplotlib`（重建图与合成 PDF 夹具）、`PyMuPDF`/`pypdf`/`pdfplumber` 任一（PDF 抽取）——均可选，缺失时逐级回退并如实记录。

## 复跑示例（三条命令，任意 cwd 均可）

```bash
SKILL_DIR="<本包根目录>"          # 例：/skills/weekly-skill 或本仓库 ppt-c7b80f0d/

# 1) 现场生成示例模板（.pptx 是二进制资源，不随包携带，必须运行时生成）
python "$SKILL_DIR/scripts/make_template.py" --out "$SKILL_DIR/examples"

# 2) 端到端跑示例案例（产出 result.json / .pptx / 预览 / 逐页证据映射）
python "$SKILL_DIR/scripts/main.py" \
  --case "$SKILL_DIR/examples/case.json" \
  --task "$SKILL_DIR/examples/task.md" \
  --spec "$SKILL_DIR/examples/deck-spec.json" \
  --out "<某个空输出目录>"

# 3) 两道交付门
python "$SKILL_DIR/scripts/export_check.py" --result "<out>/result.json" \
  --out-dir "<out>" --case "$SKILL_DIR/examples/case.json"
python "$SKILL_DIR/scripts/check_contract.py" --result "<out>/result.json" \
  --contract "$SKILL_DIR/references/OUTPUT_CONTRACT.md"
```

第 1 步可跳过：模板文件不存在时 `main.py` 会自动回退到内置 16:9 学术版式
（`deck.template.kind = "builtin"`），这是正常且被记录的分支，不是失败。

## 可选：生成合成测试夹具

```bash
python "$SKILL_DIR/scripts/make_synthetic_inputs.py" --out "<某个临时目录>"
# 产出 fig-placeholder.png（纯几何占位框，标注"非研究数据"）、
#      synthetic-two-page.pdf（ASCII 填充文本，用于测 PDF 抽取链路）、
#      synth-report.json（生成了什么 / 跳过了什么 / 用了哪个后端）
python "$SKILL_DIR/scripts/assetkit.py" --pdf "<tmp>/synthetic-two-page.pdf" --out "<tmp>/extract"
```

## 说明与限制

- `materials/paper-mini.txt` 是**合成材料**：其中的 ExampleNet、作者名、ROUGE-L 数值
  都是虚构的，用于验证"材料 → 页级方案 → deck → 证据映射 → result.json"这条链路；
  不得把它的任何数字当作科研结论。
- `output/` 下是上述合成案例的真实运行结果副本，文件名统一带 `.example.`；
  路径类字段已净化为包内相对路径，便于跨机复核。
- `deck-spec.json` 中的 `"template_path": "template-example.pptx"` 指向运行时生成的
  示例模板；生成后由生成器按名匹配布局（`Title Slide` / `Fig` 相关 `Figure Slide` /
  `Reference Slide`），并使用 `template_mode="replace"` 移除模板自带的 1 个起始页。

---

## 题集：`examples/cases/`（两个**不同题材**的合成案例）

本目录的 `case.json` 是**最小示例**（计算机题材，8 页）。除此之外，
`cases/` 下还有两个用于**泛化验证**的合成案例，各自是一个完整目录：

| 目录 | 题材 | 文件 |
|-|-|-|
| `cases/case-muon-battery/` | 实验物理 / 无损检测（μ 子透射成像分辨电池析锂） | `case.json` · `material.md` · `deck-spec.json` · `expected.json` |
| `cases/case-sleep-cohort/` | 临床流行病学（睡眠时长与代谢综合征横断面关联） | 同上四件 |

`expected.json` 给出**机器可检的验收区间**：页数区间、证据映射行数下限、
`must_keep_verbatim`（必须逐字出现在产物文字里的数字）、`must_not_claim`
（不得出现的越界表述，例如把横断面关联写成"导致"）。逐案实跑与结果见
`references/CASE-SET.md`。

```bash
# 逐案真跑并对验收区间（务必在包外副本上跑）
cp -r "$SKILL_DIR" /tmp/skill-set
python /tmp/skill-set/scripts/run_case_set.py --out /tmp/case-out     --include-example --emit-md /tmp/case-out/case-set.md
# 退出码 0 = 全部在区间内；1 = 有案例越界（报告点名）
```

**注意**：`deck-spec.json` 在真实案例里应当由 Agent 在读完材料后**现写**；
放在案例目录里只是为了让你能离线复跑题集，**不是**预置答案——
它只包含页级主张、证据定位与图表引用，全部来自 `material.md`。

**加一个新案例**只需四个文件（`case.json` / 材料 / `deck-spec.json` / `expected.json`），
`run_case_set.py` 会自动发现，无需改脚本；流程见 `references/CASE-SET.md` §5。
