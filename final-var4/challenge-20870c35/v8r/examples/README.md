# examples/ — 最小调用示例（合成输入，非平台正式案例）

本目录只做一件事：让使用者在**不接触正式案例**的情况下验证接口、跑通 CP1–CP5 全链路、
看清 `result.json` 的契约形态。

> **正式评分由平台执行**：平台固定运行 3 个案例（`/input/case.json` + `/input/task.md` + 材料），
> 并以相同内容分别交给基础 Agent 与加载本 Skill 的 Agent。
> 本目录的示例**不是**那 3 个案例，示例输出也**不得**当作正式案例的答案使用。

## 1. 本目录内容

| 文件 | 内容 | 合成声明 |
|-|-|-|
| `case.json` | 示例案例定义：`case_id=example-synthalign-talk-01`、组会汇报、20 分钟、12 页、听众描述、材料清单、`output_contract`（16 字段） | 案例与数值均为演示自拟 |
| `task.md` | 示例任务说明（四步组织要求 + 输出要求 + 运行期路径 + output_contract 声明） | 示例 |
| `materials/paper_extract.md` | 示例"论文主体"：摘要/引言/方法/结果/局限，含 92.3%、80.9%、87.5% 等**构造**数值 | 构造数据，不代表任何真实研究 |
| `materials/figures.md` | 示例图表清单（Fig. 2 / Fig. 3 / Table 1 的引用与配图说明） | 示例 |
| `materials/dataset_card.pdf` | **运行时生成**（见下）：演示 PDF 解析路径（pypdf） | 生成物，非真实数据卡片 |
| `materials/fig2.png` | **运行时生成**（见下）：演示"图表引用 → 图片绑定"路径 | 纯几何示意图，不含任何测量值 |
| `output/result.example.json` | 在**本示例输入**上真实运行得到的 `result.json`（文件名带 `.example` 以示非正式案例结果） | 由本 Skill 实跑产生 |
| `output/self_check.example.json` | 同一次运行的自检记录（validate / contract / 门快照 / 确定性探针） | 由本 Skill 实跑产生 |
| `EXPECTED-OUTPUT.md` | 该 Skill 在一个案例上应产出的**完整文件清单与契约字段**（文字版，替代随包二进制产物） | 说明文档 |

## 2. 为什么随包没有二进制

题面运行契约只允许 UTF-8 文本资源（≤50 个文本文件、单文件 ≤500KB、合计 ≤2MB、无符号链接），
所以示例用到的 PDF 与 PNG **不随包提交**，由脚本在运行时现场生成：

```bash
# $SKILL_DIR = 本包根目录（含 SKILL.md；脚本自定位，cwd 不必是技能根）
python "$SKILL_DIR/scripts/make_synthetic_inputs.py"            # -> materials/dataset_card.pdf + fig2.png
python "$SKILL_DIR/scripts/make_synthetic_inputs.py" --template # 额外生成 synthetic_template.pptx（演示模板适配）
```

生成器是确定性的、零第三方依赖（PDF 为手工构造的最小 PDF，PNG 为纯几何示意图），
每个生成物都带 `SYNTHETIC EXAMPLE` 标注 —— 不会被误认为真实科研数据。

## 3. 怎么跑（完整示例流程）

```bash
# 1) 生成示例输入（二进制资源不随包）
python "$SKILL_DIR/scripts/make_synthetic_inputs.py"

# 2) 跑主流程（一条命令完成 抽取→计划门→.pptx→校验→预览→证据审计→result.json→自检）
python "$SKILL_DIR/scripts/main.py" \
  --case "$SKILL_DIR/examples/case.json" \
  --out  "$OUT"

# 3) 独立复核（全部退出码 0 = 通过）
python "$SKILL_DIR/scripts/validate_result.py" "$OUT/result.json"
python "$SKILL_DIR/scripts/check_contract.py"  "$OUT/result.json"
python "$SKILL_DIR/scripts/evidence_audit.py"  "$OUT/result.json"
python "$SKILL_DIR/scripts/verify_deck.py" "$OUT/editable_deck.pptx" \
       --expect-pages 12 --plan "$OUT/talk_plan.json"
python "$SKILL_DIR/scripts/selftest.py" "$OUT" --package-check "$SKILL_DIR"
```

`--out` 由调用者给出（任选目录；**不要**写回本目录，以免把运行产物混进提交资源）。
`output/` 里的两个 `*.example.json` 就是上面第 2 步在示例输入上的真实产物。

## 4. 使用边界

- 示例材料里的 `case_id`、数值、图表引用均为构造数据，**不得**据其下任何科学结论；
- 示例未附带 Fig. 3 / Table 1 的图片文件，用于演示"图表缺失 → 页内诚实占位框"的降级路径；
- 平台正式案例请用 `/input/case.json` 调用（见 `SKILL.md` §2、§4）。
