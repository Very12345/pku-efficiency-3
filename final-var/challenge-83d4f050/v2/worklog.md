# worklog.md — 本版构建记录（增益可验证版 · 2026-11-22）

> 起点：已投出的合规基线包 `final/challenge-83d4f050/`（36 文件，纯文本形态）。
> 本版沿**使用增益 25** 这条轴做实质改造：把"更好"变成可复算的量。
> 算法与 CLI 接口保持不变；唯一触碰脚本的改动是一处入参归一化的缺陷修复（§4）。

## 1. 本版做了什么（三件新增 + 五处重写）

| # | 动作 | 目标维度 | 落点 |
|---|---|---|---|
| 1 | **新增公平对照协议**：条件定义、8 项指标、复算命令、实测记录、局限与反作弊 | 使用增益 25 | `references/GAIN-PROTOCOL.md` |
| 2 | **新增独立度量器**：不 import 本包模块，`--dir`/`--compare`/`--json`，缺项计 0 | 使用增益、生态贡献 | `scripts/gain_probe.py` |
| 3 | **新增条件 A 复现器**：把题面点名的基础 Agent 失败签名做成确定性基线（反例生成器） | 使用增益、创新证据 | `scripts/baseline_emulator.py` |
| 4 | SKILL.md 重写：以"增益主张 → 度量 → 阈值"开篇；流程按"产出即测量"组织；决策点收敛为影响指标的 P1–P10 | 全维度 | `SKILL.md` |
| 5 | failure-modes.md 重写：F01–F22 每条加"**可测足迹**"列（哪项指标会掉、退出码变成什么） | 可靠体验 | `references/failure-modes.md` |
| 6 | TEST.md / README.md / RUBRIC_MAP.md 重写：以指标与复算为主线 | 生态贡献、可验证性 | 三个文件 |
| 7 | `COMPARE.md` 并入协议后**删除**（避免两处对照口径不一致） | 一致性 | 文件移除 |
| 8 | OUTPUT_CONTRACT.md 增补 §10：契约合规的可测判定（命令 + 期望读数 + 与 A5 的对应）；§1–§9 字段块逐字保留 | 可核验性 | `references/OUTPUT_CONTRACT.md` |

## 2. 为什么用"独立度量器 + 条件复现器"这套做法

- **只用自述证明增益**没有说服力；**用本包自己的审计器证明增益**是循环论证
  （等于用被测者的尺子量被测者）。因此度量器不 import 本包任何模块，只读产物目录。
- 真实条件 A 由平台运行，离线无法复现；但题面 §1 已经把基础 Agent 的失败签名写得很具体
  （平铺成环、箭头不分类型、无图例、只出位图、数值无来源）。把它们做成**确定性复现器**，
  就把"基线"从"想象"变成"可复跑的对照臂"——**它是反例生成器，不是绘图方案，也不冒充平台结果。**
- 指标选择遵循一条原则：**必须与绘图实现无关**（分层、溯源、语义标签、图例声明、契约、审计、
  导出），这样换一个 Skill、换一个题目也能用同一把尺子。

## 3. 关键实测（详见 `TEST.md` 与协议 §4）

| 项 | 条件 A | 条件 B |
|---|---|---|
| 产物文件数 | 2 | 7 |
| 图层 / 语义标签 / 图例声明 / 溯源 / 契约 / 审计 / 导出 | 全 0 | 7 / 5 类 / 9-9 / 18 / 19-19 / 2 / 2 |
| `check_contract.py` | exit 1 | exit 0 |
| `validate_figure.py` | exit 1 | exit 0 |
| 改一个标签 | 只能改图 | 1 次编辑 + 1 次重跑（1.76 s） |
| 材料实体名覆盖率 | 1.0000 | 1.0000（**不算差异点**，已写进协议 §5） |

出图耗时 2.51 s / 7 件；确定性 5/6 文件逐字节一致（PDF 含时间戳）。

## 4. 缺陷修复：`--materials-dir` 崩溃（唯一触碰脚本的一处）

**修复前**（基线版，包外临时目录副本实测）：
```
main.py --case examples/case.json --model-file examples/model.example.json \
        --out <tmp> --materials-dir examples/materials
→ exit 1；TypeError: _path_normpath: path should be string, bytes or os.PathLike, not list
  没有 result.json
```
**根因**：该选项用 argparse `action="append"`（得到 list），`collect_material_paths()` 也按 list 迭代，
但 `resolve_paths()` 按 str 处理 —— 同一参数两处类型约定不一致，只要用到这个被文档写明的选项就硬崩。
**修复**：入参归一化（list/tuple/str 都接受；str 仍按 `os.pathsep` 拆分）。
不改参数名、默认值、退出码语义与任何算法/产物格式。
**修复后**：`exit 0`、`status=success`、`gates 8/8`、7 件产物。

> 这条修复对"使用增益"也有意义：它让条件 B 在材料路径不在 `case.json` 里时仍然可用，
> 而条件 A 的复现器只读显式给出的材料文件——两侧的输入条件因此仍然公平。

## 5. 验收（2026-11-22，包外临时目录副本）

| 项 | 命令 | 结果 |
|---|---|---|
| 编译 | `py_compile scripts/*.py` | 13/13 通过 |
| 主路径 | `main.py --case … --model-file …` | exit 0 / success / gates 8/8 / 2.51 s |
| 契约 | `check_contract.py` | exit 0 |
| 全检 | `validate_figure.py` | exit 0（30 项） |
| 对照 | `gain_probe.py --compare A B` | 见 §3（读数已写入协议 §4） |
| 条件 A | `baseline_emulator.py` | exit 0，2 件产物 |
| 降级 | `--formats svg` / `--formats png` | exit 2 / partial |
| 阻断 | 非法 `type` 规格 | exit 3 / failed / 14 键 |
| 合规 | `validate_pkg.py` | 见包根汇报（PASS，0 FAIL） |

## 6. 未解决项（如实）

- 条件 A 是结构复现器，不等于平台基线；协议 §6 已声明，且不预测任何分数。
- 度量器不覆盖美观度与科学判断上限。
- failed 路径的 14 键最小信封是脚本既有行为；本版记录而未改脚本（接口层）。
- `gain_probe.py` 的样式指纹按"有无箭头端点 + 描边色"比对；若图例用渐变/图案填充表示箭头，
  需要扩展指纹定义并同步更新协议 §2。当前示例与其高分同族形态均未使用该表现方式。
