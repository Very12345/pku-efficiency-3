# examples/ — 最小调用示例（合成数据，非正式案例）

**本目录的一切都是"怎么用"的演示，不是答案。** 平台固定的 3 个正式案例由组织方
提供（`/input/case.json`、`task.md` 与材料），本 Skill 不在包内携带任何正式案例
结果，也不接受把这里的示例内容当作正式案例的产出。

## 目录内容

| 路径 | 说明 |
|-|-|
| `case.json` | 合成示例案例：Cu-ZnO/γ-Al₂O₃ 催化剂 CO₂ 加氢制甲醇（**虚构数值**），含 10 页目标、受众、时长、图表清单与 `output_contract` |
| `task.md` | 该示例的任务说明（受众/时长/页数/交付要求） |
| `material.md` | 示例"论文材料"正文（38 行），带 `# 背景/方法/结果/讨论/限制/结论` 小节，供抽取与 `文件:行` 定位 |
| `minimal_example.md` | 最小调用示例与输出说明 |
| `plan.sample.json` | **页结构方案样例**（`deckplan` 的真实运行结果，标注为示例） |
| `adopt_plan.sample.json` | **适配方案样例**（两阶段工作流·阶段一 `adopt_plan` 的真实运行结果，标注为示例） |
| `output/` | 示例运行留下的**文本**产物（`result.json` / `summary.txt` / `render_log.json` + 两个说明文件），见 `output/_LABEL_example.txt` |
| `EXPECTED-OUTPUT.md` | 该 Skill 在示例案例上**应产出的文件清单与契约字段**（替代随包分发的二进制产物） |

## 示例图由脚本现场合成

`case.json` 引用的 `figs/fig1.png`、`figs/fig2.png` **不在包内**（Skill 资源只允许
UTF-8 文本文件，≤50 个、单文件 ≤500KB、合计 ≤2MB）。运行示例前先合成占位图：

```bash
python "$SKILL_DIR/scripts/make_synthetic_inputs.py" --dir <示例目录>
```

占位图是**纯几何示意图**：只有边框、坐标框线、色块与曲线，并带
`SCHEMATIC / 示意` 水印，**不含任何伪造的测量数值**——它们只负责让图表放置、
等比 contain-fit、图号交叉引用这些真实链路跑起来。正式案例使用平台提供的真实
材料与图件，不改写、不补造。

## 一键跑通示例（见 `minimal_example.md` 与根目录 `SKILL.md` §3）

```bash
SKILL_DIR=<本包根目录>            # 平台装到 /skills/weekly-skill
RUN=<任意可写目录>
cp -r "$SKILL_DIR/examples" "$RUN/examples"
python "$SKILL_DIR/scripts/make_synthetic_inputs.py" --dir "$RUN/examples"
python "$SKILL_DIR/scripts/main.py" --case "$RUN/examples/case.json" \
    --task "$RUN/examples/task.md" --out "$RUN/out"
```

产物写进 `$RUN/out/`；`examples/output/` 里保留的是**文本**产物，二进制产物
（pptx / PNG 预览）按平台硬门不随包分发，上面一条命令即可原样重建。
