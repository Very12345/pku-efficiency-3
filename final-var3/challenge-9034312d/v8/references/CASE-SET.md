# CASE-SET.md — 题集（4 个合成案例）与逐案实测结果

> 本文件是"多案例泛化"这一轴的正面材料：**4 个案例、4 次真跑、每个案例给出输入形态、
> 期望产出结构、可接受区间、难度层、实测值**，最后如实写明**泛化到哪里会失效**。
> 全部数字来自 `scripts/case_set_run.py` 的一次现场运行（命令见 §1），没有任何估计值。
>
> ⚠ 所有案例都是**合成案例**：材料为演示接口而虚构，与组织方固定案例无关；
> 正式案例、白板与评分由平台提供/执行。本文件**不预测任何分数**。

## 0. 题集一览（本版新增 2 个不同题材 + 基线的 2 个示例作锚点）

| # | case_id | 题材 | 图类 | 难度层 | 实体/关系 | 它在考什么 |
|-|-|-|-|-|-|-|
| **C-1** | `mbr-wastewater-flow-01` | 环境工程 · 市政污水处理 | `flow` | 中 | 14 / 14 | **物质流向**：分流、合流、回流、两条废料支路、出水两路 |
| **C-2** | `dtms-stage-route-01` | 分子生物学 · CRISPRi 全基因组筛选 | `route` | 高 | 18 / 18 | **阶段路线**：4 阶段 + 2 里程碑 + 依赖方向 + 返工回流 + 编号逐条对照 |
| C-3 | `demo-biotech-route-01` | 分子生物学 · CRISPR 文库药筛 | `route` | 低 | 10 / 9 | 最简线性主链（基线自带示例，作低难度锚点） |
| C-4 | `apparatus-spec-01` | 实验装置 · 冷冻干燥机 | `apparatus` | 低 | 6 / 5 | 单层装配 + 三桶布局 + 装置图特有限制（基线自带示例） |

C-1 / C-2 是**本版新增**的两个不同题材案例，落在 `examples/cases/`；
C-3 / C-4 是基线自带示例，登记进题集以覆盖"最简形态"与"装置图"两个锚点
（`apparatus` 图类不覆盖的话，装置图特有的 `apparatus-flow-into-material` 与
`product-terminal` 两条规则就没有案例去验）。

## 1. 怎么复跑（三条命令）

```bash
# ① 只列题集与期望（不执行）
python "$SKILL_DIR/scripts/case_set_run.py" --list

# ② 逐案跑 + 与期望结构比对（退出码 0 = 全 PASS）
python "$SKILL_DIR/scripts/case_set_run.py" --out <临时目录> --json <临时目录>/report.json

# ③ 追加"泛化探针"：把每个案例压扁成只留 text 字段再跑一遍，测结构化信息消失后的损失
python "$SKILL_DIR/scripts/case_set_run.py" --text-only --out <临时目录>
```

脚本行为：题集成员以 `references/case-set.json` 的 `case_path` 登记项为准
（没有登记表时才扫描 `--cases-root` 下的子目录）；每个案例跑 `main.py` 并收集
退出码 / `status` / 实体关系数 / `verify.ok` / `errors[]` / `warnings[]` /
`spec_sha16` / PNG·PDF 字节 / 失败门号，再与该案的期望逐项比对。

**期望写成"区间 + 不变量"而不是定值**，理由：合法改动（例如按材料补一条真实连接）
不该被判 FAIL，但**结构性丢失**（少一条回流、少一个终点、方向反了）必须被判 FAIL。

## 2. C-1 · 市政污水 MBR 工段物质流向图（`flow`，难度 中）

**输入**：`examples/cases/mbr-wastewater-flow-01/{case.json,task.md}`
（结构化 14 实体 / 14 关系；每个实体带 `source` 指向 `task.md §1.1–§3.3`）。

**期望产出结构**：

| 产物 | 期望 |
|-|-|
| `figure.svg` | 分层（5 层 `layer:*`），14 个 `entity-*` 组，14 条 `arrow-*`；回流 `R8` 为虚线 |
| `evidence.json` | 28 条证据（14 实体 + 14 关系），`locator` 指向 `task.md §…` |
| `result.json` | `output_contract` 四段齐全；`entities` 14、`relations` 14；`uncertainty` 为空 |
| `figure.png` / `figure.pdf` | 非空；PNG 尺寸 == 画布 × DPI |

**可接受区间**：实体 **14–18**、关系 **14–20**；`status=success`；`verify.ok=true`；
退出码 **0**；**允许** `recycle-review` 告警（回流存在时必须人工复核，属设计行为）；
**禁止** error 级违规（`no-self-loop` / `sequence-step-only` / `connect-structural` /
`apparatus-flow-into-material`）。

**不变量**（缺一即判不合格）：两条废料支路（栅渣、剩余污泥）存在且为终点；回流
方向 `D5→D4` 且 `kind=recycle`；出水分两路（`D8→P1`、`D8→P2`）；14 个实体全带 `source`。

**实测**（结构化输入）：

| 观测量 | 实测 |
|-|-|
| 退出码 / `status` | **0** / `success` |
| 实体 / 关系 | **14 / 14**（与输入一致，无丢弃） |
| `verify.ok` / 失败门 | **true** / 无 |
| 规则告警 | `recycle-review` ×1（预期内） |
| `uncertainty` 域 | 空 |
| `spec_sha16` | `5b65c6612f7714e0` |
| `figure.png` / `figure.pdf` | 53 567 B / 5 149 B |
| 单轮耗时 | 0.58 s |

## 3. C-2 · CRISPRi 全基因组筛选四阶段技术路线图（`route`，难度 高）

**输入**：`examples/cases/dtms-stage-route-01/{case.json,task.md}`
（结构化 18 实体 / 18 关系；14 `step` + 2 `milestone` + 1 `product` + 1 `data`）。

**期望产出结构**：

| 产物 | 期望 |
|-|-|
| `figure.svg` | 4 个阶段分列；步骤编号 1..N 连续；2 个里程碑单独成组（不与步骤混排） |
| `evidence.json` | 36 条证据；`locator` 指向 `task.md §2.1–§5.3` |
| `result.json` | `entities` 18、`relations` 18；`verify.checks.numbering_continuous=true` |
| `figure.png` / `figure.pdf` | 非空；PNG 尺寸 == 画布 × DPI |

**可接受区间**：实体 **18–24**、关系 **18–26**；`status=success`；`verify.ok=true`；
退出码 **0**；允许 `recycle-review`（返工回流 `R18`）；禁止 error 级违规。

**不变量**：`sequence` 只出现在 step/phase/milestone 之间（里程碑属允许端点）；
里程碑 → 下一阶段首步是 `depend` 而非 `sequence`；编号 1..N 连续；
`product`（候选基因清单）与 `data`（计数矩阵）都无出边（否则触发 `product-terminal`）。

**实测**：

| 观测量 | 实测 |
|-|-|
| 退出码 / `status` | **0** / `success` |
| 实体 / 关系 | **18 / 18** |
| `verify.ok` / 失败门 | **true** / 无 |
| 规则告警 | `recycle-review` ×1 |
| `uncertainty` 域 | 空 |
| `spec_sha16` | `cb33950dedb47795` |
| `figure.png` / `figure.pdf` | 82 561 B / 5 421 B |
| 单轮耗时 | 0.69 s |

> 这一案是本轮**难度最高**的一个：18 个实体、4 个阶段、2 个里程碑、1 条返工回流，
> 编号与阶段出口任一环节错位都会被 G8 或规则审计抓到，实测仍然一遍过。

## 4. C-3 / C-4 · 基线自带的两个示例（低难度锚点）

| 观测量 | C-3 `demo-biotech-route-01`（route） | C-4 `apparatus-spec-01`（apparatus） |
|-|-|-|
| 退出码 / `status` | 0 / `success` | 0 / `success` |
| 实体 / 关系 | 10 / 9 | 6 / 5 |
| `verify.ok` / 门 | true / 无 | true / 无 |
| 规则告警 | 无 | 无（`apparatus-flow-into-material` 未触发、`product-terminal` 未触发） |
| `spec_sha16` | `e04e9d47e8ca0099` | `4603787adcb287d7` |
| PNG / PDF 字节 | 54 982 / 4 448 | 28 884 / 3 889 |
| 单轮耗时 | 0.69 s | 0.71 s |

## 5. 逐案实测总表（`case_set_run.py` 一次运行的完整结果）

| case_id | 图类 | 难度 | 退出码 | `status` | 实体 | 关系 | `verify.ok` | 告警 | `spec_sha16` | 结论 |
|-|-|-|-|-|-|-|-|-|-|-|-|
| `apparatus-spec-01` | apparatus | 低 | 0 | `success` | 6 | 5 | true | — | `4603787adcb287d7` | **PASS** |
| `demo-biotech-route-01` | route | 低 | 0 | `success` | 10 | 9 | true | — | `e04e9d47e8ca0099` | **PASS** |
| `dtms-stage-route-01` | route | 高 | 0 | `success` | 18 | 18 | true | `recycle-review` | `cb33950dedb47795` | **PASS** |
| `mbr-wastewater-flow-01` | flow | 中 | 0 | `success` | 14 | 14 | true | `recycle-review` | `5b65c6612f7714e0` | **PASS** |

**汇总（脚本自己算的）**：`cases=4 · passed=4 · failed=0 · without_expectation=0`。
四个案例覆盖了三种 `figure_type`（route / flow / apparatus）与三个难度层，
契约门 G1–G10 在四次运行里全部通过（`gates_false` 全为空）。

## 6. ★ 泛化到哪里会失效（实测，不是猜测）

`--text-only` 把每个案例**压扁**成只留 `text` 字段的版本再跑（模拟"材料没有结构化实体"
的真实场景）。两轮的差就是"结构化信息消失后本包还能保住什么"：

| case_id | 实体保留率 | 关系保留率 | 丢失的规则告警 | 文本版 `status` |
|-|-|-|-|-|
| `apparatus-spec-01` | 0.667（6→4） | **0.000（5→0）** | — | **`partial`** |
| `demo-biotech-route-01` | 0.200（10→2） | 0.111（9→1） | — | `success` |
| `dtms-stage-route-01` | 0.389（18→7） | 0.333（18→6） | **`recycle-review`** | `success` |
| `mbr-wastewater-flow-01` | 0.429（14→6） | 0.357（14→5） | **`recycle-review`** | `success` |

**据此可以明确说出三件事：**

1. **结构化输入是本包的主航道**：4 个案例里实体保留率 0.20–0.67，关系保留率
   0.00–0.36 —— 文本解构**只能串联相邻步骤**，分流/合流/回流/依赖/里程碑会整体丢失。
   C-2、C-1 这两案的核心考点（返工回流、污泥回流）在文本形态下**完全消失**
   （`recycle-review` 告警不再出现，即回流关系根本没被识别出来）。
2. **装置图在文本形态下最危险**：C-4 的 5 条关系**全部丢失**（保留率 0.00），
   4 个孤实体触发 `orphan_entities`，`status` 从 `success` 掉到 **`partial`**。
   ⇒ **给装置图时不要只喂一段文字**；至少提供"部件清单 + 接口/连接清单"。
3. **静默风险随覆盖率下降而上升**：文本版里 `demo-biotech-route-01` 仍然报
   `success`（2 实体 1 关系），也就是说**输入退化不会自动让状态降级**——
   只有出现孤儿实体时才会（C-4）。这是本包已知的诚实边界，复核办法是同时看
   `extraction`（应为 `text-heuristic`）与实体数是否与材料规模相称。

### 其他已知失效边界（未实测，如实标注）

| 边界 | 状态 |
|-|-|
| 实体数 > 24 或阶段数 > 5 | **未测**；布局会变拥挤，需要靠 `--width-mm/--height-mm` 调画布 |
| 多级嵌套装配 / 局部放大视图 | **不支持**（本包只做单层装配）；可在 Inkscape 微调并记 `manual-edit` |
| 装置图中的"物料作为流向终点" | 会被判 **error**（`apparatus-flow-into-material`）并降级 `partial`——这是规则设计，不是缺陷 |
| 图内数值注记（浓度、流速等） | **不强制渲染**：材料给的可标注值只能进实体 `props` |
| 非 UTF-8 材料 / 超长材料 / 并发运行 | **未测** |
| 平台固定 3 个案例 | **不可见**，本文件与 `case-set.json` 均不预测其表现 |

## 7. 题集怎么复用（生态贡献）

- **换题材**：复制 `examples/cases/<任一案>` 两份文件（`case.json` + `task.md`），
  改 `entities`/`relations`/`source` 指向新材料的章节号；在
  `references/case-set.json` 里登记 `case_path` 与期望区间即可被批量跑批；
- **加判据**：`case-set.json` 的 `invariants` 是给人读的设计意图；机器判据在
  `expect_no_errors` / `allowed_warnings` / `forbidden_errors` / 实体关系区间 —— 想
  让某条不变量变成机器门，就把它翻译成 `forbidden_errors` 里的一条规则名；
- **测泛化**：任何新案例都能用 `--text-only` 立刻得到"结构化 vs 纯文本"的保留率，
  这对"这个题材到底需不需要结构化输入"是个廉价而客观的判据；
- **不适用于**：用本表去推断平台固定案例的表现（材料与白板都不在我们手上）。
