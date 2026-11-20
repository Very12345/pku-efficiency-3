# TEST.md — 本地实测记录（v2；运行者：制作子代理 agent-54，2026-11-20 22:5x +08）

> 本文件记录 v2 包在本机的真实执行结果，供复核。机器：Windows / Anaconda
> Python 3.13.9（命令 `python`）；matplotlib 3.10.6、Pillow 12.3.0。
> 无 LibreOffice；渲染后端 matplotlib（Pillow/纯 Python 为回退链）。

## T1 编译与导入检查 —— 通过

```bash
python -m py_compile scripts/*.py        # COMPILE OK
```

## T2 冒烟：示例案例默认流程 —— 通过（status=success，双 lint 通过）

```bash
python scripts/main.py --case examples/case.json --out D:/BuildTemp/t2-ga
```

`result.json` 关键字段：

```
status        : success
plan          : {source: "none", lint: {valid: true}}
spec_lint     : {valid: true, spec_sha16: 92a22433141dc61a}
four_element  : missing=[]（Q-M-R-C 全上画布）
layer_naming  : bad=[], missing=[], elements_without_src=0（7 层全绿）
determinism   : spec_sha16=9bcb54b29fe658d4（同输入同布局探针）
deliverables  : 4（svg + png + pdf + spec.json）
```

产出文件（9 个）：`example-micelle-001_graphical_abstract.{svg,png,pdf}`、
`result.json`、`spec.json`、`content.json`、`audit.json`、`render_log.json`、
`_LABEL_example.txt`。

## T3 方案先行全流程（scaffold → 方案定稿 → --plan）—— 通过

```bash
# 1) 生成方案骨架（真实抽取实体/关系/数据并带 src；four_elements 待 Agent 填充）
python scripts/scaffold.py --case examples/case.json --out plan.json
#    → lint.valid=false，problems=4（四个 four_elements 未填）—— 预期行为，提示定稿

# 2) 定稿后的方案（本包提供 examples/plan.example.json）
python scripts/main.py --case examples/case.json --plan examples/plan.example.json \
  --out D:/BuildTemp/t3-ga
```

结果：`status=success`；`result.plan.lint.valid=true`；`result.spec_lint.valid=true`；
`result.plan.source` 指向方案文件（plan 覆盖图面约束，内容仍来自材料）。

## T4 确定性：同输入两次运行 —— 逐字节一致

```bash
python scripts/main.py --case examples/case.json --out A
python scripts/main.py --case examples/case.json --out B
```

- `example-micelle-001_graphical_abstract.svg` 两次 sha256 前缀一致（same=True）；
- `spec.json` 两次一致；`audit.determinism_probe.spec_sha16` 两次同为
  `9bcb54b29fe658d4`（同内容同约束 → 同布局）。

## T5 方案 lint 拦截（四要素未填即失败）—— 通过

```bash
python scripts/scaffold.py --case examples/case.json --out plan.json
# lint.valid=false, problems=4:
#   plan.four_elements.question/method/results/conclusion missing（一句话说明）
# → 想不清楚表达什么，不允许动笔（lint_plan 是绘制前的 CP1 门）
```

## T6 v2 调试中修复的问题（诚实记录）

1. Windows GBK 控制台无法打印 `µ`（µg/mL）→ 在 `spec_lint.py` / `scaffold.py`
   CLI 开头加 stdout/stderr UTF-8 reconfigure；
2. `audit.encoding_consistency` 本就对 `float(value)` 归一化比较 —— 确认与
   spec_lint 的 legend 检查互补（一个查数值上画布，一个查图例↔数据一致）；
3. `audit.layer_naming` 初版对布局元素（panel_rail/point/legend 等）误报
   elements_without_src → 收窄为 entity:/relation:/datum:/icon 科学元素
   （实测 0 误报）；
4. `spec_lint` 初版不认识 `data_encoding[].channel` 键 → 兼容 `channel|kind`。

## 限制（如实声明）

- 渲染后端本文档实测为 matplotlib；在无 matplotlib/Pillow 环境自动降级
  （纯 Python PNG，文字占位并注明），方法见 `SKILL.md` §7；
- 实体抽取依赖材料文本结构；复杂表格/多图材料需要 Agent 复核抽取结果；
- 示例材料与结果均为合成（标注"示例，非正式案例"），与平台正式案例无关。