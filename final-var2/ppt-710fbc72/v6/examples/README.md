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

## `cases/` — 题集（两个新题材案例，v5 新增）

`examples/cases/` 下另有两个**不同题材**的合成案例，用来验证"换题材、换页预算、
换输入完整度还成不成立"；`examples/` 下的那个案例是本套题集的 **L0 基线**。

| 路径 | 难度层 | 说明 |
|-|-|-|
| `cases/case_manifest.json` | — | 题集清单：每案的**难度层 / 期望产出结构 / 可接受区间 / 这案在考什么**。测量脚本据此对拍，不靠人眼判断 |
| `cases/case-b-gnn-potential-301/` | **L1 结构完整** | 计算材料：图神经网络势函数 + 固态电解质 Li₆PS₅Cl 的锂离子输运 MD。12 页 / 15 min；`case.json` 给全部结构化字段（39 条 `material.md:N` 定位） |
| `cases/case-c-uhi-remote-302/` | **L2 退化输入** | 城市环境遥感：地表温度反演与热岛归因。9 页 / 10 min；`case.json` **只给最小 12 键**，六个故事线字段全部缺席 —— 主线必须从 `material.md` 的 `#` 小节里抽出来 |

一键跑满三案并与声明区间对拍（**在包外副本上跑**）：

```bash
RUN=<包外可写目录>; cp -r "$SKILL_DIR" "$RUN/pkg"
python "$RUN/pkg/scripts/run_case_set.py" --skill "$RUN/pkg" \
    --cases "$RUN/pkg/examples" --run "$RUN/caseset" \
    --json "$RUN/caseset.json" --markdown "$RUN/caseset.md"
# 实测：3 个案例 / 0 个超出声明区间 / 1 个已声明边界命中 / 退出码 0
```

各案的输入形态、可接受区间、逐案实测数字，以及**泛化到哪里会失效**
（案例 B 的页预算边界、"只有表格"的结果页丢主张、单页主张过多被丢、
以及跨模板族/真 PDF/英文/起始 deck/长材料/多图并排这六项未覆盖）
全部写在 `references/CASE-SET.md`。**题集不是白板、不是分数预测、也不能当质量证明。**

> 三个案例目录里都**没有** `figs/*.png`（包里只能放文本）。`run_case_set.py` 会把案例
> **先复制到包外**，再对副本跑 `make_synthetic_inputs.py --out-dir <副本>/figs`，
> 然后才跑主流程 —— 既不违反硬门，也不会在包里留下 `.pyc` 或图片。

## 同目录的姊妹装置：失败注入演练（union 包内含）

本包另带一套**失败注入演练** `scripts/fault_inject.py`（18 场景 / 4 个故障家族：
input / template / dependency / contract），把"文档声称的降级行为"变成实测的
退出码 / `status` / `uncertainty`，并判定**是否静默失败**；明细见
`references/FAULT-MATRIX.md`。它与本目录无关，但同属"自证装置"：

```bash
RUN=<包外可写目录>; cp -r "$SKILL_DIR" "$RUN/pkg"
python "$RUN/pkg/scripts/fault_inject.py" --skill "$RUN/pkg" --run "$RUN/faultrun"
# 实测：18 个场景 / 0 个静默失败 / 退出码 0
```
