# RUBRIC_MAP.md — 五维评分落点（决策显性化版）

> 题面五维：**实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 · 生态贡献 10**（+ GitHub 公开链接 5）。
> 本表按维度列出**可执行落点**：脚本、产物、命令、规则编号。文字自述不算证据，
> 每条都指向别人能复跑的东西。证据路径相对技能根 `$SKILL_DIR`。
>
> **本版的落点重心 = 决策层**：`SKILL.md` §1（D1–D23）+ §2（五类失败分支表）
> + `references/failure-modes.md`（F01–F22 一一对应）+ `references/OUTPUT_CONTRACT.md` §10（状态一致性矩阵）。
> 这三处共同把"遇到边界情况怎么办"从临场判断变成查表执行。

## 1. 实际效果（40 分）

| 评分点 | 本版落点 | 证据位置 | 本版相对基线新增 |
|---|---|---|---|
| 任务完成度 15 | CP1→CP2/CP2b→CP3→CP4→CP5 五个检查点各自绑定决策规则；每步的"能否继续"由规则表判定而不是感觉 | `SKILL.md` §3、`scripts/main.py`（退出码 0/2/3） | 每条 CP 标注相关 D 规则；CP2b 独立成节（散文/PDF 材料路径） |
| 结果正确性 15 | 语义/拓扑/图例/数值四类正确性各有机器判定：P01–P08、L01–L08、E01–E02、schema 门（对 raw 规格）；**判错时的处置也写死**（D8 就近归类 + 留痕、D9 反馈环标注或说明） | `scripts/{topology,legend_audit,validate_figure}.py`、`assets/mechanism-spec.schema.json` | D8 补齐"动词不在五类枚举内"的处置；D10/D11 补重复边与自环规则 |
| 结果完整性 5 | 实体/边/图例/分支/反馈环全覆盖；示例 9 实体 / 9 边 / 4 区室 / 5 类箭头全在用；产出 7 件 | `TEST.md` §5、`examples/EXPECTED-OUTPUT.md` | 完整性判据写成 D6（只有实体无关系时也照样交付并说明） |
| 结果可核验性 5 | 追溯链：材料行号 → `source[]` → SVG `data-source` → `evidence_sources` → `export_checks[].sha256` → `change_records`；**每条失败分支都指定了记录位点**（§2 表最后一列） | `references/OUTPUT_CONTRACT.md`、`scripts/check_contract.py`、`SKILL.md` §2 | 五类失败分支 × 记录位点矩阵（新增）；failed 路径信封实测（`TEST.md` §6） |

## 2. 使用增益（25 分）

| 评分点 | 本版落点 | 证据位置 | 本版相对基线新增 |
|---|---|---|---|
| 质量增益 15 | 基础 Agent 的五类典型退化（平铺成圈 / 箭头不分类型 / 无图例 / 无源文件 / 方向颠倒）逐条对应到机器审计；**审计不过时的处置也写死**（D12/D13/D14 三级降级） | `COMPARE.md` §2 判据表、`scripts/topology.py`、`scripts/legend_audit.py` | 降级路径明确到"改成类型默认色 / 降 assumption / 删边" |
| 效率增益 5 | 改一个标签 = 1 次文件编辑 + 1 次重跑（实测 1.76 s，SVG/PNG/PDF 全部重生成）；结构化材料一步出草稿；调色板单点改色 | `TEST.md` §3、`scripts/extract.py`、`assets/palettes.json` | 把"重跑成本"写进决策点：D18 说明缺资产时**不重画**而是回退默认并留痕 |
| 增益可验证性 5 | 两个独立 CLI 有明确退出码（0/2/3），`self_check.determinism` 承诺同输入同输出；`COMPARE.md` 给同输入对照的复算命令 | `TEST.md` §7、`scripts/check_contract.py`、`scripts/validate_figure.py` | 退出码语义与 status 的**三元组一致性规则 D22**（新增） |

## 3. 创新增益（15 分）

| 评分点 | 本版落点 | 证据位置 | 本版相对基线新增 |
|---|---|---|---|
| 新增能力 5 | ① 机制文字 → 图元/边的结构化映射；② raw 规格 schema 门前置；③ 拓扑 + 图例编码双 linter；④ 可编辑分层 SVG（7 层 + `data-*`）；⑤ **决策规则表本身**（把边界情况的处置编码成可查表的规则） | `scripts/extract.py`、`scripts/validate_figure.py`、`scripts/pathway_svg.py`、`SKILL.md` §1 | D1–D23 三分组（材料/语义/契约）替代基线的 D1–D12 平铺 |
| 方法改进 5 | 单一 JSON 规格驱动双渲染后端（零漂移）；审计矩阵 M/T/P/L/E/S/F/D；确定性布局；调色板集中 | `scripts/layout.py`、`scripts/model.py`、`TEST.md` §7 | 决策规则与检查 id 双向绑定（每条 D 都注明由哪个 P/L/E/S 检查触发） |
| 创新证据 5 | 写清与通用绘图工具的边界：通用工具不保留机制语义与来源链；本包用枚举 schema + 稳定检查 id + 确定性探针证明"正确 vs 像"可检查 | `references/legend-encoding.md`、`references/mechanism-spec.md`、`TEST.md` §9 | §9 决策规则演练覆盖表（哪条规则被哪次真实运行演练到） |

## 4. 可靠体验（10 分）

| 评分点 | 本版落点 | 证据位置 | 本版相对基线新增 |
|---|---|---|---|
| 调用与易用性 3 | 单一入口 + 稳定 CLI；命令一律 `$SKILL_DIR` 自定位；**CLI 组合矩阵实测**（7 种组合，含退出码） | `SKILL.md` §3、`README.md` §2、`TEST.md` §3 | 修复 `--materials-dir` 崩溃（基线实测 exit 1 → 本版 exit 0）；矩阵覆盖 7 种组合 |
| 运行稳定性 4 | 线性/分支/反馈/多区室四形态；matplotlib 缺失自动降级且 SVG 逐字节不变；重复运行 sha16 一致 | `TEST.md` §7、`scripts/mpl_backend.py` | 降级后 SVG sha16 与全量运行相同的实测证据 |
| 异常处理 3 | **五类失败分支表**（材料异常 / 资产缺失 / 依赖缺失 / 契约四形态 / 状态一致性）+ F01–F22 处置与记录位点；每条 D 规则都有"失败时降级"列 | `SKILL.md` §1–§2、`references/failure-modes.md`、`OUTPUT_CONTRACT.md` §10 | 新增：资产缺失三分支（F07–F09）、契约四形态分支（F13–F16）、状态不一致分支（F17–F20） |

## 5. 生态贡献（10 分）

| 评分点 | 本版落点 | 证据位置 | 本版相对基线新增 |
|---|---|---|---|
| 文档完整性 3 | `SKILL.md`（规则+流程+自查）/`README.md`（依赖、限制、维护）/`TEST.md`（复跑与实测）/`COMPARE.md`（对照口径）/`worklog.md`（构建与修复记录）+ references 5 件 + assets 3 件 + 模板 + examples | 包根与 `references/`、`assets/`、`templates/`、`examples/` | failure-modes 从 18 行扩为 22 条 F 分支并绑定 D 规则 |
| 资源可复用性 4 | 机制规格 schema、调色板、关系核对模板、四个独立校验 CLI、示例材料与已核验规格；**规则表本身也可复用**（换成别的图种仍适用"触发信号→动作→降级"结构） | `assets/`、`templates/`、`scripts/`、`examples/`、`SKILL.md` §1 | 决策规则表按"可移植"写：不绑定具体通路，只绑定图形语义 |
| 分享推广价值 3 | 沉淀为可复用规则：箭头语义=科学论断、图例/图面/数据三方一致、数值必须溯源、拓扑方向与区室约束、四形态回显、**失败分支必须落记录位点** | `references/*`、`GITHUB_URL.txt` | 失败分支→记录位点矩阵可作为同类绘图题的验收清单模板 |

## 6. GitHub 公开作品链接（+5 分）

`GITHUB_URL.txt` 为单行公开定位：
`https://github.com/Very12345/pku-efficiency-3/tree/main/final-var/challenge-83d4f050/v1`。
目录内可直接看到 `SKILL.md` 与全部文本资源；包内**没有任何二进制**（图件由脚本运行时生成），
因此链接里不存在无法预览的图元文件。

## 7. 本版相对基线的覆盖变化（逐条）

1. **SKILL.md 重写**：§1 从"12 条平铺决策"变为"**23 条分组决策 + 三列（触发信号 / 动作 / 失败时降级）**"；
   §2 新增**五类失败分支总表**（材料异常 / 资产缺失 / 依赖缺失 / 契约四形态 / 状态一致性），
   每行带 F 编号、记录位点、关联 D 规则；§4 新增退出码三值语义与三元组一致性；§10 新增文件索引。
2. **failure-modes.md 重写**：F 编号体系重排为 F01–F22 并与 D 规则一一对应；
   每条给出"触发信号（怎么发现）"，并附 2026-11-22 的实测退出码/键数。
3. **OUTPUT_CONTRACT.md 增补 §10**：状态一致性矩阵（status × exit × gates）+ failed 路径实测信封；
   **§1–§9 的字段块逐字保留**（仅追加说明，未改字段名或结构）。
4. **TEST.md 重写**：新增 CLI 组合矩阵（7 组合）、失败路径信封实测、`--materials-dir` 修复前后对照、
   决策规则演练覆盖表；实测数字全部来自 2026-11-22 的临时目录副本运行。
5. **README.md 重写**：新增"决策规则速览"与"失败分支速览"两节，依赖/限制/维护按本版重写。
6. **COMPARE.md 重写**：对照判据按 D 规则重新组织（哪条规则产出哪个可判定差异）。
7. **worklog.md 重写**：记录本版的三项实质改动（决策表、失败分支表、`--materials-dir` 缺陷修复）。
