# TEST.md — 本地实测记录（文档轴 C：机制与复用）

> 命令全部在**包外私有暂存目录**执行（`SKILL_DIR` 指向包副本），数字原样记录。
> 环境：Windows 10/11 · Anaconda Python **3.13.9** · matplotlib **3.10.6** · Pillow **12.3.0**。
>
> 本轮改动性质：**文档轴 C（机制与复用）** —— 新增
> [`references/MECHANISM.md`](references/MECHANISM.md)、[`references/REUSE-KIT.md`](references/REUSE-KIT.md)、
> `references/GAIN-PROTOCOL.md`、`scripts/gain_harness.py`；SKILL / README / RUBRIC_MAP / failure-modes 重写。
> **出图脚本的算法与 CLI 参数名未改动**；负控实验与对照均在包外完成。

## T1 编译检查（11 个脚本）—— 通过

```bash
python -m py_compile "$SKILL_DIR"/scripts/*.py
echo $?      # 0
```

## T2 基准出图 —— 通过

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <tmp>/outA
echo $?      # 0
```

实测：`result.json` 顶层 **26 键** · `status=success` · `determinism_probe=9bcb54b29fe658d4` ·
`four_element_coverage.missing=[]` · `layer_naming.bad=[]`。

## T3 三道门（M2 的规格门 + M3 的契约门）—— 通过

```bash
python "$SKILL_DIR/scripts/spec_lint.py"     --spec <tmp>/outA/spec.json --content <tmp>/outA/content.json   # 0
python "$SKILL_DIR/scripts/check_contract.py" --result <tmp>/outA/result.json --case "$SKILL_DIR/examples/case.json"  # 0
```

## T4 方案先行链 —— 通过

```bash
scaffold.py --case examples/case.json --out <tmp>/plan_skel.json      # 0（骨架生成）
spec_lint.py --lint-plan --plan <tmp>/plan_skel.json                  # 1（K7：four_elements 待填，门按设计拦住）
spec_lint.py --lint-plan --plan examples/plan.example.json            # 0（定稿方案放行）
main.py --case examples/case.json --plan examples/plan.example.json --out <tmp>/outB   # 0
```

## T5 机制负控实验（证明门真的会挡）—— E1/E2 通过，E3 暴露已知边界

```bash
# E1：从 spec 删掉 1 个元素的 src
python "$SKILL_DIR/scripts/spec_lint.py" --spec <tmp>/spec_nosrc.json --content <tmp>/outA/content.json
#   → valid=false, problems=["elements without source provenance: ['el_21']"]，exit 1
# E2：从 legend 删掉 1 个条目
python "$SKILL_DIR/scripts/spec_lint.py" --spec <tmp>/spec_nolegend.json --content <tmp>/outA/content.json
#   → valid=false, problems=["color_scale datum '细胞存活率 (50 µg/mL)' missing gradient legend entry …"]，exit 1
# E3：把 case.json 里"释放率 pH 5.5 (48 h)"由材料中的 85 % 改成 84 %
python "$SKILL_DIR/scripts/main.py" --case <tmp>/case_bad.json --out <tmp>/outBad
#   → exit 0、status=success、uncertainty=[]、missing_values=[]，
#     SVG 里同时出现 84（来自 case）与 85（来自材料要点文本）⇒ **未拦截**
```

| 实验 | 改动量 | 结果 | 结论 |
|-|-|-|-|
| E1 删 `src` | 1 处 | **exit 1**，problems 指名元素 `el_21` | M1 的"无源不上画布"是可执行判据 |
| E2 删图例条目 | 1 处 | **exit 1**，problems 指名数据与图例失联 | M2 的"图例↔数据一致"是可执行判据 |
| E3 case 与材料冲突 | 1 处 | **exit 0，未拦** | M1 信任 `case.json` 数据字段，**不做与材料正文的交叉核对** ⇒ 已写入 `MECHANISM.md` §2④ 与 `failure-modes.md` §5 |

## T6 结构确定性 —— 一致

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <tmp>/outA2 >/dev/null
python "$SKILL_DIR/scripts/gain_harness.py" --compare <tmp>/outA <tmp>/outA2
# → structure_identical: true
```

## T7 自定位与输入失败 —— 符合契约

```bash
cd / && python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <tmp>/outC
echo $?      # 0
python "$SKILL_DIR/scripts/main.py" --case <tmp>/nope.json --out <tmp>/nopeout
echo $?      # 1（不留半成品）
```

## T8 增益测量（M1/M3 的量化对照）

```bash
python "$SKILL_DIR/scripts/gain_harness.py" --out <tmp>/outA --case "$SKILL_DIR/examples/case.json" \
       --material "$SKILL_DIR/examples/material.md" --label A
python baseline_one_shot.py --case "$SKILL_DIR/examples/case.json" --out <tmp>/outBase
python "$SKILL_DIR/scripts/gain_harness.py" --out <tmp>/outBase --case "$SKILL_DIR/examples/case.json" \
       --material "$SKILL_DIR/examples/material.md" --label B
```

```
A：layers=7  text=61  glyph_use=0   coverage=0.903  four=4/4  contract=8/8 complete  顶层 26 键
B：layers=0  text=0   glyph_use=435 coverage=0.000  four=0/4  contract=0/8 absent    顶层 4 键
B 运行告警：177 条 "Glyph … missing from font(s) DejaVu Sans"，涉及 59 个字形（中文标签缺失）
A 的 render_log：backend=matplotlib，font="Microsoft YaHei,SimHei,Arial,Segoe UI"，warnings=[]
```

完整口径、B+ 条件（把 B 的可编辑性补满）与**对 A 不利**的观测（单次墙钟 A 更慢、B 也确定性、
覆盖率 0.903 而非 1.000）见 [`references/GAIN-PROTOCOL.md`](references/GAIN-PROTOCOL.md) §4/§5。

## T9 复用路径验证（REUSE-KIT §4 第 3 步）—— 通过

```bash
python "$SKILL_DIR/scripts/gain_harness.py" --out <任意输出目录> --label mine
```

测量器对**非本包产出**的目录同样工作（T8 的 B 条件就是用它量的）：不依赖包内图、
不写任何文件（除可选 `--json` 报告）。

## T10 合规验收（`validate_pkg.py`）—— 见回报栏

包体：**40 文件**（上限 50）· 扩展名集合 `{.md,.py,.json,.txt}` · 无二进制 / 无预置渲染件 /
无 `__pycache__` / 无符号链接 / 无本机绝对路径（保留的 `C:/Windows/Fonts` 等为跨平台字体探测候选路径）。

## 11. 本轴未做的事（诚实边界）

- 负控实验各只做**一处改动**，验证的是"门会挡"而非覆盖率统计；
- E3 暴露的边界**未修复**（修复需改动算法层，本包不改算法），只记录 + 给出人工替代流程；
- 对照是单案例、单机、可复现观测，不做统计显著性声明；条件 B 是最小复现脚本，不是真实无 Skill 的 LLM Agent；
- 未改出图算法与 CLI 参数名；未平台提交、未联网、未动 `submit/`、`build/`、`target/`、`publish/`、`traces/`。
