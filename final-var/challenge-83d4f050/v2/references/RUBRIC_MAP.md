# RUBRIC_MAP.md — 五维评分落点（增益可验证版）

> 题面五维：**实际效果 40 · 使用增益 25 · 创新增益 15 · 可靠体验 10 · 生态贡献 10**（+ GitHub 链接 5）。
> 本版的落点重心在**使用增益 25**：把"好在哪"变成别人能复算的指标，并把每个指标绑到具体文件与命令。
> 证据路径相对技能根 `$SKILL_DIR`；所有数字来自 2026-11-22 的实测（见 `TEST.md` 与
> `references/GAIN-PROTOCOL.md` §4）。

## 1. 实际效果（40 分）

| 评分点 | 落点 | 证据位置 |
|---|---|---|
| 任务完成度 15 | CP1→CP5 全流程；每一步都留下**可被外部脚本读取的产物**（规格 / 分层 SVG / 审计 / 契约），因此"完成"不等于"跑完"，而是"产物可复核" | `SKILL.md` §2、`scripts/main.py`、`TEST.md` §5 |
| 结果正确性 15 | 语义（5 类箭头）、拓扑（P01–P08）、图例与数据编码（L01–L08、E01–E02）、规格 schema 门四重机器判定；**正确性同时被度量**（A3 语义标签覆盖率、A4 图例声明覆盖率） | `scripts/{topology,legend_audit,validate_figure}.py`、`references/GAIN-PROTOCOL.md` §2 |
| 结果完整性 5 | 示例案例实测 9 实体 / 9 边 / 4 区室 / 5 类箭头全在用；产出 7 件（含两个审计产物） | `TEST.md` §5、`examples/EXPECTED-OUTPUT.md` |
| 结果可核验性 5 | 追溯链（材料行号 → `source` → `data-source` → `evidence_sources` → `export_checks.sha256` → `change_records`）+ 两条独立审计命令 + **降级也有可测足迹** | `references/OUTPUT_CONTRACT.md`、`references/failure-modes.md` §6、`TEST.md` §5–§9 |

## 2. 使用增益（25 分）—— 本版主攻项

| 评分点 | 落点 | 证据位置 | 可复算命令 |
|---|---|---|---|
| 质量增益 15 | **8 项结构/契约指标**在基础形态与本 Skill 上分别度量（A1–A8），差异全部可复现：图层 0→7、语义标签 0→5、图例声明 0/10→9/9、溯源 0→18、契约 0/19→19/19、审计产物 0→2、导出 0→2 | `references/GAIN-PROTOCOL.md` §4.1；`references/RUBRIC_MAP.md` 本节 | `gain_probe.py --compare A B` |
| 效率增益 5 | E1 出图 2.51 s / 7 件；E2 改一个标签 = 1 次编辑 + 1 次重跑（1.76 s，3 个导出件全部重生成）；E3 标签可精确定位（`data-id` 齐备，基础形态为 0） | 同上 §4.3 | 见 §3 复算步骤 |
| 增益可验证性 5 | 度量器**不 import 本包模块**、缺项计 0、两侧同法；指标公式写死在协议 §2；两条审计命令对两侧同法执行（exit 1 vs exit 0） | `references/GAIN-PROTOCOL.md` §2–§4.2、`scripts/gain_probe.py` | `gain_probe.py` / `check_contract.py` / `validate_figure.py` |

**诚实边界（写进落点里，见协议 §5）**：材料实体名覆盖率两侧都是 1.0000 ——
"把名词写对"不是增益来源；增益来自语义、来源与可复核结构。协议不把美观度包装成数字。

## 3. 创新增益（15 分）

| 评分点 | 落点 | 证据位置 |
|---|---|---|
| 新增能力 5 | ① 机制文字 → 图元/边的结构化映射；② raw 规格 schema 门；③ 拓扑 + 图例/编码双审计；④ 可编辑分层 SVG；⑤ **独立度量器 + 公平对照协议**（把"增益"从自述变成第三方可复算的量） | `scripts/{extract,validate_figure,topology,legend_audit,pathway_svg,gain_probe}.py` |
| 方法改进 5 | 单一 JSON 规格驱动双渲染后端（零漂移）；审计矩阵 M/T/P/L/E/S/F/D；确定性探针；调色板单点改色；**降级的可测足迹**（失败也要在指标上可辨认） | `scripts/layout.py`、`references/failure-modes.md`、`TEST.md` §7 |
| 创新证据 5 | 与现有方案的边界写清楚：通用绘图工具不保留机制语义与来源链；本包用枚举 schema + 稳定检查 id + 确定性探针 + 独立度量器证明"正确 vs 像"的差异**可检查、可复算** | `references/GAIN-PROTOCOL.md` §5–§6 |

## 4. 可靠体验（10 分）

| 评分点 | 落点 | 证据位置 |
|---|---|---|
| 调用与易用性 3 | 单一入口 + 稳定 CLI；命令用 `$SKILL_DIR` 自定位；**7 种 CLI 组合实测**（含退出码）；`--materials-dir` 崩溃已修（基线 exit 1 → 本版 exit 0） | `SKILL.md` §2、`TEST.md` §3/§8 |
| 运行稳定性 4 | 四形态通路（线性/分支/反馈/多区室）；缺 matplotlib 自动降级且 SVG 逐字节不变；双跑 sha16 一致（5/6 文件，PDF 含时间戳） | `TEST.md` §7 |
| 异常处理 3 | F01–F22 全部带**可测足迹**（哪项指标会掉、退出码会变成什么），处置与记录位点固定 | `references/failure-modes.md`、`SKILL.md` §6 |

## 5. 生态贡献（10 分）

| 评分点 | 落点 | 证据位置 |
|---|---|---|
| 文档完整性 3 | `SKILL.md` / `README.md` / `TEST.md` / `worklog.md` + references 6 件（含 **GAIN-PROTOCOL.md**）+ assets 3 件 + 模板 + examples | 包根与各目录 |
| 资源可复用性 4 | 机制规格 schema、调色板、核对清单、四个校验 CLI、**独立度量器**（可拿去量任何绘图 Skill 的产物）、**条件 A 复现器**（可复用到别的"机制→图"任务） | `scripts/gain_probe.py`、`scripts/baseline_emulator.py`、`assets/`、`templates/` |
| 分享推广价值 3 | "公平对照 + 独立度量 + 缺项计 0"这套做法可直接搬到其他 Skill 类赛题；公开链接见 `GITHUB_URL.txt` | `references/GAIN-PROTOCOL.md`、`GITHUB_URL.txt` |

## 6. GitHub 公开作品链接（+5 分）

单行定位：`https://github.com/Very12345/pku-efficiency-3/tree/main/final-var/challenge-83d4f050/v2`。
目录内可直接读到协议、度量器与实测记录；包内无二进制（图件运行时生成）。

## 7. 本版相对基线的覆盖变化（逐条）

1. **新增 `references/GAIN-PROTOCOL.md`**：公平条件、8 项指标定义、复算命令、实测记录、局限。
   `COMPARE.md` 的内容已并入本文件（避免两处口径不一致），原文件从包中移除。
2. **新增 `scripts/gain_probe.py`**：不依赖本包模块的独立度量器（`--dir` / `--compare` / `--json`）。
3. **新增 `scripts/baseline_emulator.py`**：条件 A 的结构复现器（反例生成器，仅供对照）。
4. **SKILL.md 重写**：以"增益主张 → 度量 → 阈值"开篇（§0），流程按"产出即测量"组织（§2），
   决策点只保留影响可测指标的 10 条（P1–P10）；新增 §7 实测摘要与 §9 诚实边界。
5. **failure-modes.md 重写**：F01–F22 每条增加"可测足迹"列，把降级处理也变成可复核读数。
6. **TEST.md / README.md / worklog.md / RUBRIC_MAP.md 重写**：以指标与复算为主线。
7. **OUTPUT_CONTRACT.md 增补 §10**：契约合规的可测判定（命令 + 期望读数 + 与指标 A5 的对应）；
   §1–§9 字段块**逐字保留**。
8. **缺陷修复**：`--materials-dir` 入参归一化（见 `worklog.md` §4），其余脚本未改。
