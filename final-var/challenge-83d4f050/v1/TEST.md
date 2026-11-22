# TEST.md — 自测方法、期望输出与实测记录（决策显性化版）

> 本文件回答两件事：**别人怎么复跑这套自测**、**每一步期望看到什么**；
> 后面是 2026-11-22 在本机的真实输出（命令、退出码、sha16、文件清单），供独立复核。
> 所有实测都在**包外临时目录的副本**上执行，`cwd` 不是技能根（顺带验证自定位）；
> 包内不跑任何脚本，避免 `__pycache__` 污染技能资源。

## 0. 三步自测（任何人可复跑）

```bash
export SKILL_DIR=/path/to/challenge-83d4f050        # 含 SKILL.md 的那一层；容器里是 /skills/weekly-skill

# 1) 主路径：已核验规格 → 期望 exit 0
python3 "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
    --model-file "$SKILL_DIR/examples/model.example.json" --out /tmp/t2
# 2) 契约独立复查 → 期望 exit 0（C01–C07 全 pass）
python3 "$SKILL_DIR/scripts/check_contract.py" --result /tmp/t2/result.json \
    --case "$SKILL_DIR/examples/case.json"
# 3) 图面/模型/图例/导出全检 → 期望 exit 0（30 项、fails=0）
python3 "$SKILL_DIR/scripts/validate_figure.py" --out /tmp/t2
```

判据三条：第 1 步 exit 0 且 `/tmp/t2` 出现 7 个文件；第 2、3 步 exit 0；
`result.json` 顶层含 `references/OUTPUT_CONTRACT.md` §2 全部字段 + `case.json`
`output_contract` 全部字段，且**顶层无 null**。

## 1. 期望输出速查（含退出码语义）

| 场景 | 命令要点 | 期望 status / exit | 产物 |
|---|---|---|---|
| 已核验规格 + 预览齐全 | `--model-file ...` | `success` / **0** | 7 件，gates 8/8 |
| 自动草稿（未核验） | 省略 `--model-file` | `partial` / **2** | 7 件，`uncertainty` 提示逐条复核 |
| 只要 SVG | `--formats svg` | `partial` / **2** | 5 件，`gates.g5_png=false` |
| 只要 PNG | `--formats png` | `partial` / **2** | PNG 正常，exports 为空 |
| 规格不过 schema | `--model-file bad.json` | `failed` / **3** | 仅 `result.json`（最小信封，见 §6） |
| 材料不可解析/为空 | 空材料目录 + `--materials-dir` | `failed` / **3** | 仅 `result.json` |

**退出码语义（决策规则 D22 的判定基准）**：`0 = success 全流程通过`、`2 = partial（有降级但有产物）`、
`3 = failed（阻断，不产出可编辑源）`。三者与 `status`、`gates` 必须自洽；不一致时**以退出码为真**。

## 2. 实测环境

| 项 | 值 |
|---|---|
| 日期（+08） | 2026-11-22 |
| Python | 3.13.9（`python`，Windows 控制台，入口已 reconfigure UTF-8） |
| 可选依赖 | matplotlib ✅、Pillow ✅ |
| 运行位置 | 包外临时目录副本，`cwd` = 临时根目录（**不是**技能根） |
| 包内是否跑过脚本 | 否（合规硬门：包内不得出现 `__pycache__`/`.pyc`） |

## 3. CLI 组合矩阵（全部实跑，2026-11-22）

| 组合 | 命令要点 | 实测 exit | status | gates | 备注 |
|---|---|---|---|---|---|
| A | `--case` + `--model-file` | 0 | success | 8/8 | 主路径，PNG 203655 B |
| B | A + `--task examples/task.md` | 0 | success | 8/8 | 显式任务文本不影响结构 |
| C | A + `--verbose` | 0 | success | 8/8 | 仅增加 stderr 信息 |
| D | A + `--dpi 300` | 0 | success | 8/8 | PNG 变为 252382 B |
| E | A + `--formats svg` | 2 | partial | 7/8（`g5_png=false`） | SVG sha16 与 A **逐字节相同** |
| F | A + `--formats png` | 2 | partial | 8/8 | 缺 PDF 导出 → 降为 partial |
| G | A + `--materials-dir <材料目录>` | 0 | success | 8/8 | **基线版此组合崩溃**，见 §8 |

## 4. T1 编译检查 —— 通过

```bash
python -m py_compile "$SKILL_DIR"/scripts/*.py
```
11 个脚本全部通过（`validate_pkg.py` 也会对每个 `.py` 做 `py_compile`，结果一致）。

## 5. T2 主路径冒烟 —— 通过（exit 0 / success / gates 8/8）

```bash
python3 "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
    --model-file "$SKILL_DIR/examples/model.example.json" --out <tmp>/t2
```

```
[main] case_id=example-egfr-mapk status=success entities=9 edges=9 bands=4 verified=True
  produced  diagram.svg        27f344a0dfb2e90f   17771 bytes
  produced  diagram.png        9137715961238f3f  203655 bytes
  produced  diagram.pdf        （含时间戳，每次不同） 108045 bytes
  produced  result.json        （含时间戳）          28918 bytes
  produced  model.json         f93a20a283492f73   11418 bytes
  produced  topology.json      eb826fc5557fccfc    1434 bytes
  produced  legend_audit.json  efdb1805c839d648    1807 bytes
exit=0     耗时 2.51 s
```

`self_check`：`failures=0`、`warnings=0`；`gates` 8/8；契约信封 19/19 键；顶层 `null` 0 个；
`output_contract` 两个自定义字段回显（str / list）。实体 9 / 边 9 / 区室 4 / 5 类箭头全在用。

## 6. T3 失败路径的信封实测（D21 / F19 的依据）—— 发现并记录

```bash
# 把示例规格首个实体的 type 改成 "banana"（raw 规格直接过 schema 门）
python3 "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
    --model-file <tmp>/bad.json --out <tmp>/t7
```

```
SUMMARY {"status": "failed", "reason": "机制规格未通过 schema 门"}      exit=3
产物：只有 result.json
顶层键（14）：case_id, change_records, contract_version, deliverables, evidence_sources,
             files, gates, legend_audit, reason, scientific_content, self_check,
             status, topology, uncertainty
信封覆盖：13/19 —— 缺 title, skill, data_mapping, extraction, export_checks, provenance
check_contract.py → exit 1（contract|fail|...|checks=7）
validate_figure.py → exit 1（ok=False）
```

⇒ 决策规则 **D21** 因此写成"failed 后若要交付，先补这 6 项空值"；
这不是缺陷辩护，而是把实测行为写进规则表，避免回放 Agent 把 failed 结果当成完整契约交付。

## 7. T4 降级路径与确定性（都真跑过）

**确定性双跑（同输入两次运行）**

| 文件 | 双跑 sha16 | 结论 |
|---|---|---|
| `diagram.svg` | `27f344a0dfb2e90f` / `27f344a0dfb2e90f` | 逐字节一致 |
| `diagram.png` | `9137715961238f3f` / `9137715961238f3f` | 逐字节一致 |
| `model.json` | `f93a20a283492f73` / `f93a20a283492f73` | 逐字节一致 |
| `topology.json` | `eb826fc5557fccfc` / `eb826fc5557fccfc` | 逐字节一致 |
| `legend_audit.json` | `efdb1805c839d648` / `efdb1805c839d648` | 逐字节一致 |
| `diagram.pdf` | `9ffb77958af0c8a7` / `e978238bc095b6a0` | **差异**（matplotlib 内嵌 `CreationDate`） |

⇒ 确定性承诺 = SVG / PNG / model / topology / legend_audit；PDF 与 `result.json` 含时间戳，不承诺。

**只请求 SVG（F12b）**：exit 2、`partial`、`gates.g5_png=false`、`previews=[]`、`exports=[]`，
SVG sha16 仍是 `27f344a0dfb2e90f`（与全量运行**逐字节相同**）→ 预览能力缺失不影响可编辑源。

**自动草稿（未人工核验）**：exit 2、`partial`、`extraction.verified_by_agent=false`、
`self_check.failures=0` 但 `warnings=1`（`P03`：一条逆流边待人确认）、`gates 8/8`、
`uncertainty` 1 条 —— 正是留给 Agent 核验的信号（CP3）。

**材料不可解析**：`materials=[]` + 空 `--materials-dir` → exit 3、`failed`、
`reason="材料中未找到可结构化解析的实体/关系…"`，只写 `result.json`。

## 8. T5 `--materials-dir` 崩溃修复（真实缺陷 → 真实修复）

| 阶段 | 命令 | 实测结果 |
|---|---|---|
| 修复前（基线版） | `main.py --case examples/case.json --model-file examples/model.example.json --out t --materials-dir examples/materials` | exit **1**，`TypeError: _path_normpath: path should be string, bytes or os.PathLike, not list`，**没有 result.json** |
| 修复后（本包） | 同上 | exit **0**，`status=success`，7 个产物 |

根因：`--materials-dir` 用 `action="append"`（argparse 给 **list**），而 `resolve_paths()`
按 **str** 处理（`materials_arg.split(os.pathsep)`），把整个 list 当路径传给 `os.path.abspath`；
同一个 list 在 `collect_material_paths()` 里却是按 list 迭代的——两处对同一参数的类型约定不一致。
修复只做**入参归一化**（list / str 都接受），不改参数名、不改退出码语义、不改任何算法。

## 9. T6 决策规则的演练覆盖（A 轴自证）

| 决策规则 | 怎么被真正演练到 | 证据 |
|---|---|---|
| D16 / D17（依赖缺失降级） | `--formats svg`、`--formats png` | §7 与 §3 的 E/F 行 |
| D19 / D20（契约四形态） | 示例 `output_contract` 两字段回显；`check_contract.py` C05 | §5 |
| D21 / F19（failed 信封） | schema 门失败路径 | §6 |
| D22（状态一致性） | 同一输入的 success/partial/failed 三种组合退出码 | §1、§3、§6 |
| D7（材料三级查找） | `--materials-dir` 组合 + 空材料目录 | §3 G 行、§7 |
| D23（自定位） | 全部命令在 `cwd≠技能根` 下执行 | §2 |
| D1–D6 / D8–D15 | 示例案例含：同蛋白跨区室（ERK / 核内 ERK）、负反馈环、弱证据虚线、数值映射、5 类箭头 | §5 的 `scientific_content` 结构 |

## 10. 合规自检（本包文本形态）

| 项 | 实测 | 上限 |
|---|---|---|
| 文件数 | 见包根汇报（`validate_pkg.py`） | 50 |
| 扩展名 | 仅白名单七种 | `.md .py .json .txt .csv .yaml .yml` |
| 包内二进制 | 无（图件运行时生成） | 禁止 |
| `__pycache__` / `.pyc` | 无 | 禁止 |
| 包内本机盘符绝对路径 | **0 命中**（扫描规则：字母+冒号+分隔符，且排除 URL 方案前缀；无需豁免项） | 禁止 |
| 单文件 / 总字节 | 见汇报（均远低于 500KB / 2MB） | 500KB / 2MB |

## 11. 未解决项与边界（如实）

1. **failed 路径的最小信封**是脚本既有行为（§6 实测）；本版选择"写进决策规则 + 给出补齐步骤"，
   而没有改脚本（改动会触及接口层，超出本次"文档与规则层"的范围）。
2. 自动抽取器只处理结构化语句；散文与 PDF 依赖 Agent 手工建规格（CP2b/CP3），这是刻意设计。
3. PDF 与 `result.json` 含时间戳，不作确定性承诺（§7）。
4. PNG 字节随 matplotlib 版本变化；`examples/EXPECTED-OUTPUT.md` 已声明"结构一致优先于字节一致"。
5. 本包不运行、也不伪造平台的对照实验与分数；对照判据见 `COMPARE.md`（不声称任何 benchmark 分数）。
6. Windows 控制台默认 GBK 会把中文摘要显示成乱码（**文件内容始终 UTF-8**）；
   用 `chcp 65001` 或 UTF-8 终端即可。
