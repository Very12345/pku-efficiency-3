# TEST.md — 自测、度量与实测记录（增益可验证版）

> 三部分：**怎么自测**（§0–§1）、**怎么量增益**（§2）、**2026-11-22 的实测数字**（§3–§9）。
> 所有运行都在**包外临时目录副本**上执行、`cwd` 不是技能根；包内不跑脚本（避免 `__pycache__`）。

## 0. 自测三步

```bash
export SKILL_DIR=/path/to/challenge-83d4f050

python3 "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
    --model-file "$SKILL_DIR/examples/model.example.json" --out /tmp/t2   # 期望 exit 0
python3 "$SKILL_DIR/scripts/check_contract.py" --result /tmp/t2/result.json \
    --case "$SKILL_DIR/examples/case.json"                                # 期望 exit 0
python3 "$SKILL_DIR/scripts/validate_figure.py" --out /tmp/t2             # 期望 exit 0
```

判据：第 1 步 exit 0 且出现 **7 件产物**；第 2、3 步 exit 0；
`result.json` 顶层含契约 §2 全部字段 + `output_contract` 全部字段且**无 null**。

## 1. 度量一步（本版新增）

```bash
python3 "$SKILL_DIR/scripts/baseline_emulator.py" \
    --material "$SKILL_DIR/examples/materials/example_material.md" --out /tmp/condA
python3 "$SKILL_DIR/scripts/gain_probe.py" --compare /tmp/condA /tmp/t2 \
    --material "$SKILL_DIR/examples/materials/example_material.md" \
    --case "$SKILL_DIR/examples/case.json"          # 加 --json 可得机器可读结果
```

判据：读数为"两侧同法、缺项计 0"；条件 A 的 A1–A7 应为 0，A8 应两侧相同（诚实项）。

## 2. 指标与期望读数（定义见 `references/GAIN-PROTOCOL.md` §2）

| 指标 | 期望（条件 B） | 期望（条件 A） |
|---|---|---|
| A1 图层完整度 | 1.0000（7 层） | 0.0000 |
| A2 溯源覆盖率 | 1.0000 | 0.0000 |
| A3 语义标签覆盖率 | 1.0000（5 类） | 0.0000 |
| A4 图例声明覆盖率 | 1.0000 | 0.0000 |
| A5 契约信封覆盖 | 19/19 = 1.0000 | 0.0000（无 `result.json`） |
| A6 审计产物 | 1.0000 | 0.0000 |
| A7 导出件 | 1.0000（PNG+PDF） | 0.0000 |
| A8 材料实体名覆盖率 | 1.0000 | **1.0000（不算差异点）** |

## 3. CLI 组合矩阵（实跑，2026-11-22）

| 组合 | 命令要点 | 实测 exit | status | gates | 备注 |
|---|---|---|---|---|---|
| A | `--case` + `--model-file` | 0 | success | 8/8 | PNG 203655 B |
| B | A + `--task examples/task.md` | 0 | success | 8/8 | — |
| C | A + `--verbose` | 0 | success | 8/8 | 仅 stderr 信息增加 |
| D | A + `--dpi 300` | 0 | success | 8/8 | PNG 252382 B |
| E | A + `--formats svg` | 2 | partial | 7/8（`g5_png=false`） | SVG sha16 与 A 相同 → A7 = 0.5000 |
| F | A + `--formats png` | 2 | partial | 8/8 | 缺 PDF → partial |
| G | A + `--materials-dir <目录>` | 0 | success | 8/8 | 基线版崩溃，见 §8 |

## 4. T1 编译与主路径 —— 通过

`python -m py_compile scripts/*.py`：13/13 通过（11 个原有 + `gain_probe.py` + `baseline_emulator.py`）。

```
[main] case_id=example-egfr-mapk status=success entities=9 edges=9 bands=4 verified=True
diagram.svg 27f344a0dfb2e90f 17771 | diagram.png 9137715961238f3f 203655
diagram.pdf 108045 | result.json 28918 | model.json f93a20a283492f73 11418
topology.json eb826fc5557fccfc 1434 | legend_audit.json efdb1805c839d648 1807
exit=0   耗时 2.51 s
```

## 5. T2 对照读数（`gain_probe.py --compare` 原始输出）

```
== A-baseline ==  files=2  svg=1  layers=0  edges=10  semantic_tags=0  legend_declared=0/10
   data_source=0  contract_keys=0/19  status=None  gates=0/8  png=False pdf=False  coverage=1.0
   score: A1=0.0000 A2=0.0000 A3=0.0000 A4=0.0000 A5=0.0000 A6=0.0000 A7=0.0000 A8=1.0000
== B-skill ==     files=7  svg=1  layers=7  edges=9   semantic_tags=5  legend_declared=9/9
   data_source=18 contract_keys=19/19 status=success gates=8/8 png=True pdf=True coverage=1.0
   score: A1=1.0000 A2=1.0000 A3=1.0000 A4=1.0000 A5=1.0000 A6=1.0000 A7=1.0000 A8=1.0000
```

> 度量器早期版本曾把 `<defs>` 里的箭头 marker 误计为一条边（条件 A 显示 11 条），
> 现已剔除 `<defs>`；图例声明比对也不再把"无箭头的 binding 图例线"漏掉。
> 这两处修正都为了让两侧**同法**计算——修正过程保留在本记录里，避免"改了尺子没留痕"。

## 6. T3 两条审计命令对两侧同法执行

| 命令 | 条件 A | 条件 B |
|---|---|---|
| `check_contract.py` | exit **1**，`missing result.json` | exit **0**，`contract\|ok\|…\|checks=7` |
| `validate_figure.py` | exit **1**，`ok=False` | exit **0**，`ok=True\|fails=0\|warns=0` |

## 7. T4 效率实测（E1–E3）

| 指标 | 条件 A | 条件 B |
|---|---|---|
| E1 出图耗时 | 即时（仅 SVG + 说明） | 2.51 s / 7 件 |
| E2 改一个标签 | 需直接改图；无规格、无导出流水线 | 1 次编辑 + 1 次重跑（1.76 s）；SVG/PNG sha16 变化；SVG/PNG/PDF 全部重生成；新标签出现在 SVG |
| E3 标签可定位性 | `data-id` = 0 | `data-id`/`data-type`/`data-source` 齐备 |

## 8. T5 `--materials-dir` 缺陷修复（前后对照）

| 版本 | 实测 |
|---|---|
| 基线版 | exit **1**，`TypeError: _path_normpath: path should be string… not list`，无 `result.json` |
| 本版 | exit **0**，`status=success`，7 件产物 |

根因：argparse `action="append"` 给 **list**，`resolve_paths()` 按 **str** 处理。
修复只做入参归一化（list/str 都接受），不改参数名与退出码语义。详见 `worklog.md` §4。

## 9. T6 降级与确定性

**确定性双跑**：`diagram.svg` `27f344a0dfb2e90f`/`27f344a0dfb2e90f` ✅；
`diagram.png` `9137715961238f3f`/`9137715961238f3f` ✅；`model.json` `f93a20a283492f73`/同 ✅；
`topology.json` `eb826fc5557fccfc`/同 ✅；`legend_audit.json` `efdb1805c839d648`/同 ✅；
`diagram.pdf` `9ffb77958af0c8a7`/`e978238bc095b6a0` ❌（matplotlib 内嵌 `CreationDate`）。
⇒ 确定性承诺 5/6；PDF 与 `result.json` 含时间戳不承诺。

**降级路径**
| 场景 | exit | status | 指标表现 |
|---|---|---|---|
| `--formats svg` | 2 | partial | A7 = 0.5000，`gates.g5_png=false`，SVG 与全量运行逐字节相同 |
| `--formats png` | 2 | partial | A7 = 0.5000，PNG 正常 203655 B |
| 自动草稿（未核验） | 2 | partial | 结构指标满、`verified_by_agent=false`、`warnings=1`（`P03` 待人确认） |
| schema 门失败 | 3 | failed | 只有 `result.json`（14 键、信封 13/19），A1–A7 全 0 |
| 材料不可解析 | 3 | failed | `reason=manual-required`，只有 `result.json` |

## 10. 合规自检

| 项 | 实测 | 上限 |
|---|---|---|
| 文件数 | 见 `validate_pkg.py` 汇报（38） | 50 |
| 扩展名 | 仅白名单七种 | `.md .py .json .txt .csv .yaml .yml` |
| 二进制 / `__pycache__` / 符号链接 | 无 | 禁止 |
| 包内本机盘符绝对路径 | **0 命中**（排除 URL 方案前缀后；无需豁免项） | 禁止 |
| 单文件 / 总字节 | 均远低于 500KB / 2MB | 500KB / 2MB |

## 11. 未解决项（如实）

1. 条件 A 是**结构复现器**，不是真实基础 Agent；平台真实对照以平台运行为准。
2. 度量器不覆盖美观度与科学判断上限（协议 §5 已声明）。
3. failed 路径的最小信封是脚本既有行为（14 键）；本版在协议与失败表里记录，
   未改脚本（属接口层）。
4. PDF/`result.json` 非确定性；PNG 跨 matplotlib 版本可能变化（结构一致优先于字节一致）。
5. Windows GBK 控制台下中文摘要显示为乱码（文件内容始终 UTF-8）。
