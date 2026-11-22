# TEST.md — 本地实测记录（文档轴 B：增益可验证）

> 全部命令在**包外私有暂存目录**执行（`SKILL_DIR` 指向包副本，`<tmp>` 为暂存目录），
> 因此同时验证"自定位"与"包内不留运行残留"。数字原样粘贴，未做四舍五入以外的修饰。
> 环境：Windows 10/11 · Anaconda Python **3.13.9** · matplotlib **3.10.6** · Pillow **12.3.0**。
>
> 本轮改动性质：**文档轴 B（增益可验证）** —— 新增
> [`references/GAIN-PROTOCOL.md`](references/GAIN-PROTOCOL.md) 与只读测量器
> `scripts/gain_harness.py`；SKILL/README/RUBRIC_MAP/failure-modes 重写。
> **出图脚本的算法与 CLI 参数名未改动**；对照相关的实跑在包外完成。

## T1 编译检查（含新增测量器）—— 通过

```bash
python -m py_compile "$SKILL_DIR"/scripts/*.py
echo $?                                            # 0
```

`scripts/` 现为 11 个 `.py`：原 10 个（main / extract / figurespec / svgbuilder / preview /
audit / spec_lint / scaffold / check_contract / common）+ 新增 `gain_harness.py`。

## T2 出图（默认流程）—— 通过

```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <tmp>/outA
echo $?      # 0
```

实测：`result.json` 顶层 **26 键** · `status=success` · `spec_lint.valid=true`。

## T3 契约自查 —— 通过

```bash
python "$SKILL_DIR/scripts/check_contract.py" --result <tmp>/outA/result.json --case "$SKILL_DIR/examples/case.json"
echo $?      # 0    （信封 18 键 ∪ 案例契约 8 字段全覆盖、无 null）
```

## T4 方案先行链 —— 通过

```bash
python "$SKILL_DIR/scripts/scaffold.py"  --case "$SKILL_DIR/examples/case.json" --out <tmp>/plan_skel.json   # 0
python "$SKILL_DIR/scripts/spec_lint.py"  --lint-plan --plan <tmp>/plan_skel.json                            # 1（骨架未定稿，CP1 门按设计拦住）
python "$SKILL_DIR/scripts/spec_lint.py"  --lint-plan --plan "$SKILL_DIR/examples/plan.example.json"         # 0
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --plan "$SKILL_DIR/examples/plan.example.json" --out <tmp>/outB  # 0
```

## T5 增益测量（条件 A = 加载本 Skill）—— 原始输出

```bash
python "$SKILL_DIR/scripts/gain_harness.py" --out <tmp>/outA \
       --case "$SKILL_DIR/examples/case.json" --material "$SKILL_DIR/examples/material.md" --label A
```

```
editable  = {layers: 7, layer_names: [layer:annotations, layer:background, layer:data,
             layer:entities, layer:legend, layer:panels, layer:relations],
             text_nodes: 61, glyph_use_nodes: 0}
provenance= {src_attrs: 56, science_elems: 62, coverage: 0.903}
four_els  = 4 / 4
numbers   = 16 个图面数值，其中 14 个可在材料中定位（残差: "001" = case_id 的一部分,
            "6.5" = 比例尺刻度，版面派生值，非科学数据）
contract  = {expected: 8, covered: 8, missing_or_null: [], verdict: "complete",
             result_toplevel_keys: 26}
evidence  = {result_json: true, audit_json: true, render_log: true, spec_json: true}
```

## T6 增益测量（条件 B = 不加载 Skill 的基础做法）—— 原始输出

条件 B 由**最小复现脚本**执行（`svg.fonttype` 保持 matplotlib 默认；脚本全文见
[`references/GAIN-PROTOCOL.md`](references/GAIN-PROTOCOL.md) §6）：

```bash
python baseline_one_shot.py --case "$SKILL_DIR/examples/case.json" --out <tmp>/outBase
echo $?      # 0
python "$SKILL_DIR/scripts/gain_harness.py" --out <tmp>/outBase \
       --case "$SKILL_DIR/examples/case.json" --material "$SKILL_DIR/examples/material.md" --label B
```

```
editable  = {layers: 0, text_nodes: 0, glyph_use_nodes: 435}     ← 文字被轮廓化，改字必须回原工具
provenance= {src_attrs: 0, science_elems: 0, coverage: 0.0}
four_els  = 0 / 4
contract  = {expected: 8, covered: 0, verdict: "absent", result_toplevel_keys: 4}
evidence  = {audit_json: false, render_log: false, spec_json: false}
运行时告警 = 177 条 "Glyph … missing from font(s) DejaVu Sans"，涉及 59 个不同字形
             （中文标签在 PNG 中缺失；A 侧的 render_log.json 记录 font="Microsoft YaHei,SimHei,Arial,Segoe UI" 且 warnings=[]）
```

## T7 增益测量（条件 B+ = 把 B 的可编辑性补到最强）—— 原始输出

```bash
python bplus.py --case "$SKILL_DIR/examples/case.json" --out <tmp>/outBplus   # 仅多一行 rcParams["svg.fonttype"]="none"
```

```
editable  = {layers: 0, text_nodes: 38, glyph_use_nodes: 12}
four_els  = 1 / 4（仅 results）
numbers   = 15 个图面数值，7 个可定位（残差含坐标轴刻度 20/40/60/80 与浮点格式差异 18.0/85.0/72.0/95.0）
contract  = {expected: 8, covered: 0, verdict: "absent"}
```

## T8 结构确定性（G6）—— 两组条件各自两次运行

```bash
python "$SKILL_DIR/scripts/gain_harness.py" --compare <tmp>/outA <tmp>/outA2
{"dir_a": "outA", "dir_b": "outA2", "structure_identical": true, "diff_keys": []}
python "$SKILL_DIR/scripts/gain_harness.py" --compare <tmp>/outBase <tmp>/outBase2
{"dir_a": "outBase", "dir_b": "outBase2", "structure_identical": true, "diff_keys": []}
```

⇒ **B 也做到了两次一致**：确定性不是本包的独占优势（已写入 GAIN-PROTOCOL §4.3）。

## T9 效率（G8）—— 两次独立会话的墙钟实测

```
会话 1：A = 2.441 s / 2.156 s      B = 1.707 s / 1.514 s
会话 2：A = 2.331 s             B = 1.329 s
```

⇒ **A 单次更慢**（多出的时间用于抽取、方案 lint、图层化、audit 与契约回填）；
A 的效率收益体现在"首次运行即达标"（契约 26 键 + `check_contract.py` exit 0，返工步数 0），
而 B 未达标（契约 0/8，无 audit/render_log/spec）。此口径已写入 GAIN-PROTOCOL §5 的"可以说/不可以说"。

## T10 自定位与失败分支 —— 符合契约

```bash
cd / && python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out <tmp>/outC
echo $?      # 0（cwd 与技能根无关）
python "$SKILL_DIR/scripts/main.py" --case <tmp>/nope.json --out <tmp>/nopeout
echo $?      # 1（硬输入错误，不留半成品）
```

## T11 合规验收（`validate_pkg.py`）—— 见回报栏

包体：**38 文件**（上限 50）· 扩展名集合 `{.md,.py,.json,.txt}` ·
无二进制 / 无 `.svg` 预置件 / 无 `__pycache__` / 无符号链接 / 无本机绝对路径
（保留的 `C:/Windows/Fonts` 等为跨平台字体探测候选路径，属探测逻辑）。

## 12. 本轴未做的事（诚实边界）

- 条件 B 是**最小复现脚本**，不是真实无 Skill 的 LLM Agent；平台官方对照以白板为准；
- 未做多案例、多机重复实验，因此不对"统计显著性"作任何声明；
- 未改出图算法与 CLI 参数名；未平台提交、未联网、未动 `submit/`、`build/`、`target/`、`publish/`、`traces/`。
