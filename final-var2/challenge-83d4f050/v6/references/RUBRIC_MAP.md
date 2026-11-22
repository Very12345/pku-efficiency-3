# RUBRIC_MAP.md — 评分五维 → 本 Skill 设计覆盖

> 本题最强高分信号之一：五维评分逐条落到**可执行产物或可复跑命令**上，而不是文件清单。
> 文件名按合规包要求为 `references/RUBRIC_MAP.md`（与 `OUTPUT_CONTRACT.md` 并列全大写）。
> 题面评分维度：**实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 ·
> 生态贡献 10 · GitHub 公开链接 +5**（合计 105）。证据路径相对 Skill 根 `$SKILL_DIR`。
> **文字自述不替代实际运行证据**——每条落点都给出脚本、产物或命令。
> 与"不加载 Skill 的基础 Agent"的对照口径见 `references/GAIN-PROTOCOL.md` 附录 A。
> 本包为**合规重打包版**：只收 `.md/.py/.json/.txt/.csv/.yaml/.yml` 七种文本资源，
> SVG/PNG/PDF 等图件一律由 `scripts/` 在运行时生成（见 `examples/EXPECTED-OUTPUT.md`）。

## 1. 实际效果（40 分）

| 评分点 | 本 Skill 覆盖 | 证据位置（本包内） |
|-|-|-|
| 任务完成度 15 | "读机制材料—定实体与关系—定布局与图例—出源文件与导出件"完整闭环，四个检查点全部是**可执行门**：CP1 读真实文件（材料缺失直接 failed）→ CP2 机制规格（自动草稿或 `--model-file`，再过 schema 门）→ CP3 确定性布局 + SVG/PNG/PDF 渲染 + 双审计 → CP4 写 `result.json` 并判定 status | 入口 `scripts/main.py`（CP1–CP4 与退出码 0/2/3）；流程叙述见 `SKILL.md` §3 |
| 结果正确性 15 | 实体类型（gene/protein/complex/rna/small_molecule/other）、箭头语义（activation/inhibition/binding/modification/transport）、通路方向与区室、数据编码全部**可机器校验**：`topology.py`（P01–P08 方向/区室/同名消歧/重复边/自环/反馈）、`legend_audit.py`（L01–L08、E01–E02 图例覆盖/箭头=图例/颜色⊆图例∪映射/虚线语义/线宽/数值溯源）、schema 门对 **raw** 规格校验防静默归一 | `scripts/topology.py`、`scripts/legend_audit.py`、`scripts/validate_figure.py`、`assets/mechanism-spec.schema.json`；规则依据 `references/legend-encoding.md`、`references/mechanism-spec.md` |
| 结果完整性 5 | 实体/边/图例项/并行分支/反馈环全覆盖：示例案例实测 9 实体 / 9 边 / 4 区室 / 5 类箭头全在用 / 负反馈环右侧绕行 / 弱证据虚线；产物 4+3 类（SVG·PNG·PDF·result.json + model.json·topology.json·legend_audit.json） | `examples/output/result.json`（实跑，含 `scientific_content.counts`）；`examples/EXPECTED-OUTPUT.md`（应产出清单与契约字段） |
| 结果可核验性 5 | 追溯链可独立复核：材料行号 → 实体/边 `source[]` → SVG 元素 `data-source` → `evidence_sources` → `export_checks[].sha256` → `change_records`；审计产物独立落盘（topology.json / legend_audit.json），契约可独立复查 | `references/OUTPUT_CONTRACT.md`；`scripts/check_contract.py`（独立 CLI，exit 0/2/3）、`scripts/validate_figure.py` |

## 2. 使用增益（25 分）

| 评分点 | 本 Skill 覆盖 | 证据位置（本包内） |
|-|-|-|
| 质量增益 15 | 基础 Agent 的典型失败（名词平铺成圈、箭头不区分激活/抑制、无图例、无源文件、通路方向颠倒）被本 Skill 的**机器审计**逐条挡住：拓扑 + 图例/编码审计 + 契约门任一 fail 就不允许 `status=success`；对照口径（同输入、同工具权限、可核验判据）写在 `references/GAIN-PROTOCOL.md` 附录 A | `references/GAIN-PROTOCOL.md` 附录 A（对照方案与判据）、`scripts/topology.py`、`scripts/legend_audit.py`、`scripts/validate_figure.py`、`TEST.md` 实测段 |
| 效率增益 5 | 结构化材料一步出草稿（`extract.py`）；改一个标签无需重画——改 `model.json` 后 `--model-file` 重跑即重导出 SVG/PNG/PDF（0 次重画、1 次重跑）；一个 JSON 规格驱动两条渲染后端（SVG 手写图层 + matplotlib），杜绝两版图不一致；关系核对清单模板把人工核验变成逐行填空 | `scripts/extract.py`、`scripts/layout.py`、`scripts/pathway_svg.py`、`scripts/mpl_backend.py`、`templates/relation-checklist-template.md` |
| 增益可验证性 5 | 增益不靠自述：`check_contract.py` 与 `validate_figure.py` 各自有明确退出码（0 通过 / 2 有告警 / 3 失败），`self_check.determinism`（model_sha16 / svg_sha16）承诺同输入同输出，`TEST.md` 记录可复跑命令与逐文件 sha256 | `TEST.md`（T1–T9，含双跑确定性）、`scripts/check_contract.py`、`scripts/validate_figure.py`、`result.json.self_check.determinism` |

## 3. 创新增益（15 分）

| 评分点 | 本 Skill 覆盖 | 证据位置（本包内） |
|-|-|-|
| 新增能力 5 | ① 机制文字 → 图元与边边界的**结构化映射**（动词→5 类箭头 + 证据强度→线宽 + 弱证据→虚线）；② **机制规格 schema 门前置**（对 raw 规格校验，未知类型不会被静默改写成 other，而是 failed）；③ 拓扑 / 图例编码双 linter；④ 可编辑分层 SVG 自动生成（7 个 `layer-*` 组 + `data-id/data-type/data-source`） | `scripts/extract.py`、`scripts/validate_figure.py`（`check_schema`）、`scripts/topology.py`、`scripts/legend_audit.py`、`scripts/pathway_svg.py`、`assets/mechanism-spec.schema.json` |
| 方法改进 5 | ① 单一 JSON 规格驱动双渲染后端（零漂移）；② 审计矩阵（M/T/P/L/E/S/F/D 系列）把"图例↔图面一致、来源可核、方向正确"从目检变为机器强制；③ 确定性布局与去时间戳 SVG（同输入双跑逐字节一致）；④ 调色板 / glyph 语义集中于 `assets/palettes.json`，改一处全图与图例同步 | `scripts/layout.py`、`scripts/validate_figure.py`、`scripts/model.py`、`assets/palettes.json`；实测见 `TEST.md` T4 |
| 创新证据 5 | 与常规绘图方案的边界写清楚了：通用画图工具不保留机制语义与来源链，本 Skill 用枚举 schema + 稳定审计 id（P/L/E/T/F/S/D）+ 确定性探针证明"**正确 vs 像**"的差异是可检查的；CJK 实体名与字体缺失被显式化处理（SVG 用 CSS 字体栈，PNG 缺中文字体时告警） | `references/legend-encoding.md`、`references/mechanism-spec.md`、`references/failure-modes.md`、`TEST.md` |

## 4. 可靠体验（10 分）

| 评分点 | 本 Skill 覆盖 | 证据位置（本包内） |
|-|-|-|
| 调用与易用性 3 | 单一入口 + 稳定 CLI：`python3 "$SKILL_DIR/scripts/main.py" --case <case.json> --out <out_dir>`（可选 `--model-file/--task/--materials-dir/--formats/--dpi/--verbose`）；`SKILL.md` 的命令与 `scripts/` 实际入口逐字一致，且用 `$SKILL_DIR` 自定位（cwd 不是技能根也能跑） | `SKILL.md` §3、`README.md` §2、`scripts/main.py` 的 `argparse` 定义 |
| 运行稳定性 4 | 覆盖线性/分支/反馈/多区室四种通路形态（示例含全部形态），重复运行结构一致；matplotlib 缺失时自动降级为"仅 SVG + 显式记录"，绝不假装有预览；PDF/PNG 导出失败不让 SVG 源失效 | `TEST.md`（T2/T3/T4）、`scripts/mpl_backend.py` 降级分支、`scripts/main.py` 的 preview try/except |
| 异常处理 3 | 失败模式表 + 决策规则双覆盖：材料缺失/为空、PDF 扫描件、方向缺失、基因与蛋白同名、多区室同一蛋白、数值与图面矛盾、规格不过 schema、图例缺项、数值无源、字体缺失、导出失败、元素过多不可读——每项都有处置与记录位置 | `references/failure-modes.md`（对照表）、`SKILL.md` §4（D1–D12）与 §8（速查表） |

## 5. 生态贡献（10 分）

| 评分点 | 本 Skill 覆盖 | 证据位置（本包内） |
|-|-|-|
| 文档完整性 3 | 说明（`SKILL.md`）/ 依赖与安装（`README.md` §5）/ 自测（`TEST.md`）/ 对照（`references/GAIN-PROTOCOL.md` 附录 A/B）/ 构建与重打包记录（`worklog.md`）+ references 8 件（`OUTPUT_CONTRACT.md`、`RUBRIC_MAP.md`、`mechanism-spec.md`（§9 含原 `legend-encoding.md` 全文）、`failure-modes.md`、`MECHANISM.md`、`GAIN-PROTOCOL.md`、`FAULT-MATRIX.md`、`CASE-SET.md`）+ assets 3 件 + 模板 + examples 输入与期望输出 | 包根与 `references/`、`assets/`、`templates/`、`examples/` |
| 资源可复用性 4 | 可复用件：机制规格 schema（`assets/mechanism-spec.schema.json`）、调色板与 glyph 语义（`assets/palettes.json` + `legend-encoding.md`）、关系核对模板（`templates/relation-checklist-template.md`）、四个可独立调用的校验 CLI（`check_contract.py`/`validate_figure.py`/`topology.py`/`legend_audit.py`）、示例材料与已核验模型（`examples/`） | `assets/`、`templates/`、`scripts/`、`examples/` |
| 分享推广价值 3 | 沉淀为可复用规则而非一次性脚本：箭头语义=科学论断、图例/图面/数据三方一致、数值必须溯源、拓扑方向与区室约束、契约四形态回显——可直接作为机制图题集 / 绘图规范 / 校验清单的起点；公开链接见 `GITHUB_URL.txt` | `references/*`、`GITHUB_URL.txt` |

## 6. GitHub 公开作品链接（+5 分）

`GITHUB_URL.txt` 为单行公开仓库定位：
`https://github.com/Very12345/pku-efficiency-3/tree/main/challenge-83d4f050`。
评审无需登录即可打开该目录并看到 `SKILL.md` 与全部文本资源（本包不含任何二进制，
所有图件由脚本在运行时生成，因此链接内不存在无法预览的图元文件）。

## 7. 相对 build 基础包与 v2 的覆盖变化

**算法/接口层（v2 已建立，本版不改）**

- 新增：CP1–CP4 检查点流水线 + 决策规则 D1–D12（`SKILL.md`）；
- 新增：机制规格 schema 门（`assets/mechanism-spec.schema.json`，对 raw 规格校验防静默归一）；
- 新增：`topology.py`（P 系列）与 `legend_audit.py`（L/E 系列）双审计、独立 `check_contract.py`；
  审计产物 topology.json / legend_audit.json 落盘；
- 新增：`templates/relation-checklist-template.md`（人工核验执行载体）、`assets/result.template.json`；
- 强化：契约四形态回显 + G1–G8 硬性门；未人工核验的草稿 / schema 不过 / 门不过时不允许 `success`；
  SVG 去时间戳（确定性）；数值溯源 E01 成为阻断检查；
- 修复（基包缺陷）：抽取器对 `A 动词 B` 的 left 尾随空格；约束行被误抽为实体。

**资源形态层（本合规重打包版新增）**

- 删除全部非文本资源（`examples/output/diagram.pdf|png|svg`）与 `__pycache__`，包内只留七种文本扩展名；
- 图件全部改为**运行时生成**：`scripts/main.py` + `pathway_svg.py` + `mpl_backend.py` 现场产出
  `diagram.svg`（可编辑源，7 层）、`diagram.png`、`diagram.pdf`；缺 matplotlib 时降级并如实记录；
- `examples/output/**` 改为"示例案例上的实跑 JSON + 文字化期望输出"（`EXPECTED-OUTPUT.md`），
  并清除全部本机绝对路径痕迹（provenance 只记相对/环境路径）；
- 文档文件名对齐合规形态（`OUTPUT_CONTRACT.md` / `RUBRIC_MAP.md`），`SKILL.md` 改为 `$SKILL_DIR` 自定位命令。

## 8. 使用增益（25 分）—— 8 项可测指标（R1/v2 逐字保留）

| 评分点 | 落点 | 证据位置 | 可复算命令 |
|---|---|---|---|
| 质量增益 15 | **8 项结构/契约指标**在基础形态与本 Skill 上分别度量（A1–A8），差异全部可复现：图层 0→7、语义标签 0→5、图例声明 0/10→9/9、溯源 0→18、契约 0/19→19/19、审计产物 0→2、导出 0→2 | `references/GAIN-PROTOCOL.md` §4.1；`references/RUBRIC_MAP.md` 本节 | `gain_probe.py --compare A B` |
| 效率增益 5 | E1 出图 2.51 s / 7 件；E2 改一个标签 = 1 次编辑 + 1 次重跑（1.76 s，3 个导出件全部重生成）；E3 标签可精确定位（`data-id` 齐备，基础形态为 0） | 同上 §4.3 | 见 §3 复算步骤 |
| 增益可验证性 5 | 度量器**不 import 本包模块**、缺项计 0、两侧同法；指标公式写死在协议 §2；两条审计命令对两侧同法执行（exit 1 vs exit 0） | `references/GAIN-PROTOCOL.md` §2–§4.2、`scripts/gain_probe.py` | `gain_probe.py` / `check_contract.py` / `validate_figure.py` |

**诚实边界（写进落点里，见协议 §5）**：材料实体名覆盖率两侧都是 1.0000 ——
"把名词写对"不是增益来源；增益来自语义、来源与可复核结构。协议不把美观度包装成数字。
## 9. 创新增益（15 分）—— 机制落点（R1/v3 逐字保留）

| 评分点 | 落点 | 证据位置 |
|---|---|---|
| 新增能力 5 | 六条机制作为一个**互相咬合的链**（不是功能清单）：规格先行 / raw 门 / 双审计 / 分层与溯源 / 确定性探针 / 契约化终态；每条都说明它解决的是哪一类"看起来对但其实是错"的失效 | `references/MECHANISM.md` §1–§3 |
| 方法改进 5 | ① 校验点放在**原始规格**上（避免静默归一，M2）；② 审计产物独立落盘，可被第三方读取；③ 确定性与去时间戳；④ 契约三元组（status/退出码/gates）一致；⑤ 决策捷径按"哪条机制坏了"组织（修机制不修图） | `SKILL.md` §1/§3、`scripts/validate_figure.py`、`TEST.md` §9 |
| 创新证据 5 | 每条机制都给**消融实验式的验证信号**（枚举外类型 → exit 3；同两条命令对无机制产物 → exit 1；双跑 → 5/6 逐字节一致），并明确写出**边界**（科学判断上限、美观度不承诺、跨领域必须重定义枚举） | `references/MECHANISM.md` §2/§5、`TEST.md` §6 |
## 10. 生态贡献（10 分）—— 资产与复用（R1/v3 逐字保留）

| 评分点 | 落点 | 证据位置 |
|---|---|---|
| 文档完整性 3 | `SKILL.md` / `README.md` / `TEST.md` / `worklog.md` + references 8 件（含 `MECHANISM.md`（§7 含原 `ASSET-INDEX.md` 全文）、`GAIN-PROTOCOL.md`、`FAULT-MATRIX.md`、`CASE-SET.md`）+ assets 3 件 + 模板 + examples；README 含"复用三步" | 包根与各目录 |
| 资源可复用性 4 | **资产清单 A1–A11**（schema / 调色板 / 箭头语义 / 核对清单 / 四个校验 CLI / 契约模板 / 流水线骨架 / 示例 / 失败表 / 机制写法 / 对照口径），每项注明"复用前必须替换的内容"；三类复用场景 + 命令级三步 + 适配检查表 + 常见坑 | `references/MECHANISM.md` §7（原 `ASSET-INDEX.md`） |
| 分享推广价值 3 | 沉淀为可迁移的**方法论**："机制链 + 消融说明 + 资产清单"这套写法可用于任何 Skill 类作品；并把本包踩过的坑（先归一化再校验、只搬渲染不搬审计、复用示例数据）写成警告 | `references/MECHANISM.md` §2/§7 |
## 11. 可靠体验（10 分）—— 故障矩阵逐格落点（R2/v4 逐字保留）

| 评分点 | 本包给出的**实测**证据 | 复跑命令 |
|-|-|-|
| 运行稳定性 4 | 四形态 24 场景中，**没有一条路径是"退出 0 但什么也没发生"**；`silent_failures=[]`（修复前为 3 条，见 FAULT-MATRIX.md §4） | `fault_inject.py --out <dir>` → `SUMMARY` 行 |
| 异常处理 3 | 每个故障都有**明确终态**：入口拒绝 `exit 1`、阻断 `exit 3/failed`、降级 `exit 2/partial` 且 `gates.g5_png=false`、留痕降级 `exit 0/success + uncertainty`；三处曾被静默吞掉的降级已改为留痕 | 同上；`--family 依赖` / `--family 契约` 可单跑 |
| 调用与易用性 3 | 演练脚本本身有三条使用路径（全量 / 按形态 / 按 id），并有 `--json` 机器可读报告；报告与文档中的数字同源，**文档数字不是手写的** | `fault_inject.py --help` |
| 恢复能力（本包自加判据） | 6 个场景定义了修复动作，复跑全部回到 `exit 0 / success / gates 8/8` —— "失败可恢复"不是承诺而是读数 | `fault_inject.py` 输出里的 `recovery` 段 |

> **诚实边界**：演练覆盖的是**行为面**（退出码、状态、留痕、产物清单），
> 不评价图面美观，也不代表平台固定 3 个正式案例上的得分。边界与未覆盖项见 `FAULT-MATRIX.md` §6。
## 12. 实际效果 / 生态贡献 —— 题集逐条落点（R2/v5 逐字保留）

| 评分点 | 本包证据 | 复算方式 |
|-|-|-|
| 任务完成度 15（跨题材） | 3 个**题材不重叠**的合成案例都能走完"读材料→定实体关系→定布局图例→出源文件与导出件"闭环：实测 `exit 0 / success / gates 8/8`（9/9、12/12、8/8 实体边数） | `CASE-SET.md` §3 的表；命令见 §5 |
| 结果正确性 15（类型与方向） | 案例 B 的主实体是**基因与 RNA**（不是蛋白）；案例 A 的**无数值**分支强制关闭颜色编码（`data_mapping.field` 为空）——两条相反的轴各有实测读数 | 同上；`data_mapping` 与 `scientific_content.entities[].type` |
| 结果可核验性 5 | 每个案例给出"期望产出结构"与"可接受区间"，并配两份独立 CLI 的退出码（`check_contract.py` / `validate_figure.py` 三案皆 exit 0） | `CASE-SET.md` §3.1 |
| 资源可复用性 4 | 题集本身就是可复用资源：案例目录自带 `case.json` / `task.md` / `material.md` / **已核验 `model.json`**；加新案例的三步流程写在 `CASE-SET.md` §6，并要求写明失效边界（N10） | 目录 + `CASE-SET.md` §6 |
| 分享推广价值 3 | **失效边界 F1–F10 是公开成果**：明确写出"散文材料 / PDF / 枚举外类型 / 契约语义回显"这些不会做的事，避免别人踩坑 | `CASE-SET.md` §4 |