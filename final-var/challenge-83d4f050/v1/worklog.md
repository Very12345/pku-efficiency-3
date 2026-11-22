# worklog.md — 本版构建记录（决策显性化版 · 2026-11-22）

> 起点：已投出的合规基线包 `final/challenge-83d4f050/`（36 文件，纯文本形态）。
> 本文件记录本版**做了什么实质改动、为什么、怎么验证**。算法与 CLI 接口保持不变
> （唯一例外见 §4：一处入参归一化的缺陷修复，已在 §4 逐条说明并附修复前后实测）。

## 1. 本版的定位与三条改动

基线包已经解决了"合规形态"（纯文本、图件运行时生成）和"流程图显性化"（CP + D1–D12）。
本版沿**可靠体验 10 + 实际效果 40** 这条轴继续做实质改造，落成三件事：

| # | 改动 | 目标维度 | 落点 |
|---|---|---|---|
| 1 | 决策规则从 12 条平铺 → **23 条分五组、每条三列（触发信号 / 动作 / 失败时降级）** | 实际效果、可靠体验 | `SKILL.md` §1 |
| 2 | 新增**五类失败分支总表**（材料异常 / 资产缺失 / 依赖缺失 / 契约四形态 / 状态一致性），F01–F22 与 D 规则一一对应并指定记录位点 | 可靠体验、结果可核验性 | `SKILL.md` §2 + `references/failure-modes.md` |
| 3 | 新增**状态一致性矩阵**与 failed 路径实测信封 | 结果可核验性、异常处理 | `references/OUTPUT_CONTRACT.md` §10、`TEST.md` §6 |

## 2. 为什么这样改（而不是再堆功能）

- 基线包的 D1–D12 只回答"遇到什么情况怎么办"，**没有回答"如果这么办也办不成，退到哪里"**。
  真实运行里最贵的错误不是"没规则"，而是"按规则做了但做不成，于是临场发挥"。
  本版把每一行补上第三列（失败时降级 + 记录位点），并把记录位点固定在 `result.json` 的真实字段上。
- 基线包的失败文档只覆盖两块（材料阶段、规格/校验阶段）。本题面在"可靠体验"里明确要求覆盖
  **材料异常 / 字体或图元缺失 / 导出失败 / 元素过多 / 数据与图示矛盾**，
  而"资产缺失（palettes/schema/模板）""契约四形态""状态不一致"这三类在基线里没有独立处置条目。
  本版把它们补成独立分支（F07–F09、F13–F16、F17–F20）。
- **契约四形态**必须写清"无值填什么"。基线契约文件里已有四形态表，但决策层没有告诉 Agent
  "先判形态再填空"以及"声明值为 null 时怎么办"。本版把它变成 D19/D20 两条可执行规则。

## 3. 逐文件改动清单（相对基线包）

| 文件 | 改动性质 | 要点 |
|---|---|---|
| `SKILL.md` | **重写**（18.2 KB → 21.5 KB） | §0 三步读法；§1 D1–D23 五组三列；§2 五类失败分支表（F 编号 + 记录位点 + 关联 D）；§3 CP1–CP5 每步标注相关 D；§4 退出码语义；§7 自查清单按 D 规则重排；§10 文件索引 |
| `references/failure-modes.md` | **重写**（4.2 KB → 7.9 KB） | F01–F22；每条含"触发信号（怎么发现）"+ 实测退出码/键数 + 关联 D 规则 + 记录位点 |
| `references/OUTPUT_CONTRACT.md` | **增补 §10**（§1–§9 字段块逐字保留） | §10 状态一致性矩阵（status × exit × gates）+ failed 路径实测信封（14 键、缺 6 项） |
| `references/RUBRIC_MAP.md` | **重写** | 五维落点改按"本版落点 / 证据位置 / 本版相对基线新增"三列；新增决策规则演练覆盖表 |
| `README.md` | **重写** | 新增"决策规则速览""失败分支速览"两节；CLI 参数与退出码语义集中到 §3；限制按本版重写 |
| `TEST.md` | **重写** | 新增 CLI 组合矩阵（7 组合）、失败路径信封实测、`--materials-dir` 修复前后对照、决策规则演练覆盖 |
| `COMPARE.md` | **重写** | 对照判据按 D 规则组织（每条规则 → 可判定差异 → 复算命令） |
| `scripts/main.py` | **1 处缺陷修复** | `--materials-dir` 入参归一化（见 §4），其余脚本逐字节未动 |

未改动的部分：`scripts/` 其余 10 个脚本、`assets/*`、`templates/*`、`examples/*`、
`references/{mechanism-spec,legend-encoding}.md`、`GITHUB_URL.txt` 的仓库根、
契约 §1–§9 的字段名与结构（**逐字保留**）。

## 4. 缺陷修复：`--materials-dir` 崩溃（唯一触碰脚本的一处）

**现象**（在包外临时目录副本上复现，基线版）：

```
python3 scripts/main.py --case examples/case.json --model-file examples/model.example.json \
    --out <tmp> --materials-dir examples/materials
→ exit 1
  TypeError: _path_normpath: path should be string, bytes or os.PathLike, not list
  输出目录里没有 result.json
```

**根因**：`--materials-dir` 在 argparse 里是 `action="append"`（得到 **list**），
`collect_material_paths()` 也按 list 迭代；但 `resolve_paths()` 按 **str** 处理
（`materials_arg.split(os.pathsep)`），于是把整个 list 当单个路径交给 `os.path.abspath`。
同一个参数在两处有**不同的类型约定**，只要运行者用到这个已被文档写明的选项就会硬崩。

**修复**：只做入参归一化——list / tuple / str 三种形态都接受，str 仍按 `os.pathsep` 拆分。
不改参数名、不改默认值、不改退出码语义、不改任何算法或产物格式。

**修复后实测**（同一命令）：`exit 0`、`status=success`、`gates 8/8`、7 个产物齐全。

> 为什么值得动脚本：这是**文档里写明的选项**，回放 Agent 在官方案例上很可能用到它
> （案例材料不一定写在 `case.json` 里）。一个必然崩溃的选项属于可靠性缺陷，不是风格问题。

## 5. 验收（2026-11-22，全部在包外临时目录副本上执行）

| 项 | 命令 | 结果 |
|---|---|---|
| 编译 | `python -m py_compile scripts/*.py` | 11/11 通过 |
| 主路径 | `main.py --case examples/case.json --model-file examples/model.example.json` | exit **0**、success、gates 8/8、7 件产物、耗时 2.51 s |
| 契约 | `check_contract.py --result <out>/result.json --case examples/case.json` | exit **0**（C01–C07 全 pass） |
| 全检 | `validate_figure.py --out <out>` | exit **0**（30 项、fails=0） |
| 降级 | `--formats svg` / `--formats png` | exit **2**、partial；SVG 与全量运行逐字节相同（sha16 `27f344a0dfb2e90f`） |
| 阻断 | 非法 `type`（`banana`）规格 | exit **3**、failed、只写最小信封（14 键） |
| 确定性 | 同输入双跑 | SVG/PNG/model/topology/legend_audit 逐字节一致；PDF 仅时间戳不同 |
| 自定位 | 全部命令在 `cwd≠技能根` 下执行 | 通过 |
| 合规 | `python validate_pkg.py <pkg>` | 见包根汇报（PASS，0 FAIL） |

## 6. 未解决项（如实）

- failed 路径的最小信封是脚本既有行为；本版选择"写进决策规则 D21 并给出补齐步骤"，
  没有改脚本（属于接口层，超出本次"决策与文档层"的范围）。见 `TEST.md` §11 第 1 条。
- 本版没有新增脚本或资产；创新点集中在"决策与失败分支的显性化"，
  不声称它带来了分数提升——增益判据见 `COMPARE.md`，由平台对照运行产生。
