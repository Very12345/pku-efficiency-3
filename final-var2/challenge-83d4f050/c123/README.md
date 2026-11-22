# README.md — 生物机制图与通路图 Skill（机制与复用版）

> 题目：玻尔产品周赛·北大专区·学术效率·第三期 — `challenge-83d4f050`（生物机制与通路图，组：figures）。
> 平台固定 3 个案例；参赛者只提交 Skill 与运行必需的**文本**资源。

## 1. 这个 Skill 的机制（一句话版）

**先把机制写成规格，再让规格生成图，并让每一个环节都能被机器审计与复核。**
六条机制互相咬合：规格先行（M1）→ 原始规格过 schema 门（M2）→ 渲染出可编辑分层源与溯源（M4）
→ 拓扑 + 图例/编码双审计（M3）→ 确定性探针（M5）→ 契约化终态（M6）。

每条机制都配一句**"没有它会怎样"**——完整版见 `references/MECHANISM.md`：

| 机制 | 没有它会怎样（摘要） | 可验证信号 |
|---|---|---|
| M1 规格先行 | 图与来源脱钩：改一个标签要重画，导出件之间漂移 | `model.json` 存在；改规格一次即重导出全部图件 |
| M2 raw schema 门 | 未知类型被静默改写成 `other`，错误论断被"画得很专业" | 枚举外类型 → 实测 **exit 3 / failed** |
| M3 双审计 | 图例与图面不一致、方向颠倒、数值无来源只能靠人眼 | 两个审计产物落盘；对无机制产物同命令 **exit 1** |
| M4 分层 + 溯源 | 只能交位图：改不了、追不回 | 7 个 `layer-*` 组、`data-source` ≥ 边数（实测 18） |
| M5 确定性探针 | "评审看到的图"与"提交的图"无法判定是否同一张 | 双跑 SVG/PNG/model/topology/legend_audit **逐字节一致** |
| M6 契约化终态 | 结果无法被机器复核，成功与失败在产物上无区别 | 信封 19/19、null 0、gates 8/8、exit 0 |

## 2. 资源形态

包内**只有文本**：`.md .py .json .txt .csv .yaml .yml`；
契约原文 `at most 50 UTF-8 text files, 500KB each and 2MB total, no symlinks`。
`diagram.svg` / `diagram.png` / `diagram.pdf` 由 `scripts/` 在 `--out` 目录**运行时生成**。

## 3. 快速开始

```bash
export SKILL_DIR=/skills/weekly-skill            # 容器路径；本机指向含 SKILL.md 的那一层
python3 "$SKILL_DIR/scripts/main.py" --help      # 自检

python3 "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
    --model-file "$SKILL_DIR/examples/model.example.json" --out /app/output    # 期望 exit 0（7 件产物）

python3 "$SKILL_DIR/scripts/check_contract.py" --result /app/output/result.json \
    --case "$SKILL_DIR/examples/case.json"                                     # 期望 exit 0
python3 "$SKILL_DIR/scripts/validate_figure.py" --out /app/output              # 期望 exit 0
```

平台运行：输入 `/input/case.json` + `/input/task.md`（+ 材料目录），输出 `/app/output`。

**退出码 = 终态**：`0 = success`、`2 = partial（有降级但有产物）`、`3 = failed（阻断）`；
三者与 `status`、`gates` 必须一致。

**CLI 参数**（与 argparse 逐字一致）：`--case --task --out --materials-dir（可重复） --model-file --formats --dpi --verbose`。

## 4. 目录结构

```
SKILL.md                       机制分解 M1–M6 / 流程 / 决策捷径 K1–K10 / 资产摘要与复用三步
README.md                      本文件
TEST.md                        自测 + 2026-11-22 实测（CLI 矩阵、机制验证信号、降级、确定性）
worklog.md                     构建记录（本版新增了什么、为什么、验收）
GITHUB_URL.txt                 公开作品链接（单行）
references/
  MECHANISM.md                 ★核心：机制详解 + 消融分析 + 依赖链 + 边界
  ASSET-INDEX.md               ★核心：可复用资产清单 + 复用三步 + 适配检查表 + 常见坑
  OUTPUT_CONTRACT.md           字段契约 + 四形态 + G1–G8 + §10 机制→字段映射
  RUBRIC_MAP.md                五维落点（创新增益与生态贡献按机制与资产逐条落点）
  failure-modes.md             F01–F26，按"破坏了哪条机制"归类
  mechanism-spec.md            规格结构、命名与区室规范
  legend-encoding.md           箭头语义、数据编码、调色板
scripts/                       13 个脚本（build / render / verify / 对照 四组，退出码 0/2/3）
assets/  templates/  examples/ schema·调色板·模板 / 核对清单 / 最小可运行示例
```

## 5. 复用（本版重点，完整版见 `references/ASSET-INDEX.md`）

**三步**：

1. **搬骨架**：复制 `scripts/`、`assets/`、`references/OUTPUT_CONTRACT.md` 到新任务，替换 `examples/`；
2. **换语义**：同步改 `assets/mechanism-spec.schema.json`（类型枚举）、`assets/palettes.json`（配色/形状）、
   `references/legend-encoding.md`（语义表）三处——**必须同步，否则图例与图面会不一致**；
3. **验一遍**：主路径 exit 0 → 两条审计 exit 0 → **故意失败用例 exit 3**（验证 schema 门还活着）。

**可复用的资产**（清单见 `ASSET-INDEX.md` §1）：机制规格 schema、调色板与 glyph 语义、箭头语义规范、
关系核对清单、四个独立校验 CLI、契约模板（四形态 + G1–G8）、流水线骨架、最小示例、失败分支表、
机制写法模板、对照口径（含 `gain_probe.py` 独立度量器与 `baseline_emulator.py` 基础形态复现器）。

## 6. 依赖与环境

- **运行必需**：Python 3.8+，**仅标准库**。
- **可选**：`matplotlib`（PNG/PDF）、`Pillow`（尺寸校验）；缺失 → 只交 SVG（`partial` + exit 2 + `gates.g5_png=false`），
  **不伪造预览**，且 SVG 的分层与 `data-*` 不受影响（M4 不因此失效）。
- **字体**：SVG 用 CSS 字体栈（包内无字体文件）；PNG/PDF 由 matplotlib 选系统字体，缺中文字体时告警。
- **本机路径**：脚本 `__file__` 自定位；包内文本**无任何本机绝对路径**（实测 0 命中，无豁免项）。
  字体由 matplotlib 的字体管理器按**字体族名**解析（`fm.findfont`），不硬编码系统字体目录——
  这也是 `ASSET-INDEX.md` 迁移清单里不需要改路径项的原因。
- 实测环境：Python 3.13.9 + matplotlib + Pillow（2026-11-22，见 `TEST.md` §2）。

## 7. 适用范围与限制

- 适用：机制图/通路图/信号级联/调控网络/流程图/图表编辑，含"改一个箭头""按数据上色""补图例"。
- 不适用：数值统计与统计结论、实验方案设计、论文写作与版式美化（相邻课题负责）。
- **机制能保证**：类型不越界、方向与区室有约束、图例与图面一致、数值可溯源、产物可编辑可复现、结果可复核。
- **机制不能保证**：科学判断的最终正确性（该判 activation 还是 binding 仍需评审）、图面美观度、
  跨领域迁移的正确性（必须重定义枚举与配色）。
- 图件不在包内；PDF 与 `result.json` 含时间戳，不作确定性承诺。

## 8. 维护与更新

- 改颜色 → `assets/palettes.json`；改契约/门 → 契约文件 + `check_contract.py` + `result_writer.py` 三处同步；
- 改校验规则 → `topology.py` / `legend_audit.py` / `validate_figure.py`，同步 `mechanism-spec.md` 的校验一览；
- **改机制 → 必须同步更新 `references/MECHANISM.md`（机制说明与消融列）与 `SKILL.md` §1**，
  否则"没有它会怎样"会与实现脱节——这是本版最容易被后续维护破坏的地方；
- 改完跑 `TEST.md` 全套（含故意失败用例）→ 更新记录 → 在 `worklog.md` 追加一条带时间的条目；
- **禁止**向包内添加二进制或 `__pycache__`。
