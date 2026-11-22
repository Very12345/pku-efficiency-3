# README.md — 生物机制图与通路图 Skill（全维合并版 · 文本包）

> 本包是 Round 2 的**全维合并版**：把 R1 的三条轴（决策显性化 / 增益可验证 / 机制与复用）
> 与 R2 的两条轴（失败注入与恢复演练 / 多案例泛化与题集）**合成一个包**，
> 并按"输入 → 执行 → 失败 → 增益 → 机制 → 复用"重排 `SKILL.md`。
> 全部内容都可复算：每个数字都能用包内命令重跑出来。

## 1. 这是什么

把一份生物机制/通路材料变成**可逐条质疑**的机制图：声明式机制规格 → 区室约束确定性布局
（胞外→膜→胞质→核）→ 可编辑分层 SVG 源 + PNG/PDF 预览 → 拓扑审计 + 图例/数据编码审计
→ 契约化 `result.json`。同时把四个通常只写在文档里的问题变成读数：

| 问题 | 机制 | 复跑入口 |
|-|-|-|
| 出错时会怎样？ | 失败注入器（输入/模板/依赖/契约四形态 × 24 场景） | `scripts/fault_inject.py` → `references/FAULT-MATRIX.md` |
| 比基础 Agent 好在哪？ | 8 项可机读指标的公平对照 | `scripts/gain_probe.py` + `scripts/baseline_emulator.py` → `references/GAIN-PROTOCOL.md` |
| 为什么这样设计？ | 机制分解 M1–M6 + 消融（"去掉会退化成什么"） | `references/MECHANISM.md` |
| 换一个题材还灵吗？ | 3 个互补合成案例 + 泛化失效边界 F1–F10 | `examples/cases/` + `references/CASE-SET.md` |

## 2. 快速开始（自定位，cwd 不是技能根也能跑）

```bash
# 技能根目录 = 含 SKILL.md 的那一层
export SKILL_DIR=/skills/weekly-skill           # 平台容器
# export SKILL_DIR=/path/to/challenge-83d4f050  # 本机解压后的包根目录

# 1) 已核验规格路径（人工核验后正式出图；期望 exit 0 / status=success / gates 8/8）
python3 "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
    --model-file "$SKILL_DIR/examples/model.example.json" --out /app/output
# 2) 自动草稿路径（产出 partial 并提示逐条复核；期望 exit 2）
python3 "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out /app/output
# 3) 独立复查（两条都必须 exit 0）
python3 "$SKILL_DIR/scripts/check_contract.py" --result /app/output/result.json --case "$SKILL_DIR/examples/case.json"
python3 "$SKILL_DIR/scripts/validate_figure.py" --out /app/output

# 4) 失败注入与恢复演练（务必在包外副本上跑；期望 exit 0、SUMMARY 里 silent_failures=[]）
cp -r "$SKILL_DIR" /tmp/fault-skill
python3 /tmp/fault-skill/scripts/fault_inject.py --skill /tmp/fault-skill --out /tmp/fault-out

# 5) 增益对照（同材料、同尺子量两个条件）
python3 "$SKILL_DIR/scripts/baseline_emulator.py" --material "$SKILL_DIR/examples/materials/example_material.md" --out /tmp/condA
python3 "$SKILL_DIR/scripts/gain_probe.py" --compare /tmp/condA /app/output --material "$SKILL_DIR/examples/materials/example_material.md" --json
```

> ⚠ **一律不要在包内跑脚本**：`python3 <pkg>/scripts/main.py` 会在 `scripts/__pycache__/`
> 留下字节码，而技能资源硬门禁止非文本/多余文件。复制到 `/tmp` 再跑。

## 3. 输入与输出

**输入**：`case.json`（`case_id`/`title`/`task`/`materials`/`render`/`output_contract`）
＋ `task.md` ＋ 材料文件（文本、Markdown、表格；PDF 由 Agent 抽文或手写规格）。

**输出**（`--out` 目录，全部运行时生成）：`result.json`（唯一评分产物）、
`diagram.svg`（7 层可编辑源，`data-id`/`data-type`/`data-source`）、`diagram.png`、`diagram.pdf`、
`model.json`（机制规格）、`topology.json` / `legend_audit.json`（审计产物）—— 共 7 件。

## 4. 目录结构

```
SKILL.md                 入口：资源形态 / 输入 / 执行 / 失败 / 增益 / 机制 / 复用 / 决策规则 / 自查
README.md                本文件：依赖、安装、用法、四方读数、限制、维护
TEST.md                  自测方法与实测记录（T1–T13：含增益复算、故障演练、三案例题集）
GITHUB_URL.txt           公开作品链接（单行）
worklog.md               构建、合规重打包与五轴合并日志
scripts/                 14 个脚本：
                           build   = extract / model / main
                           render  = layout / pathway_svg / mpl_backend
                           verify  = topology / legend_audit / validate_figure /
                                     check_contract / result_writer
                           drill   = fault_inject（失败注入与恢复演练）
                           measure = gain_probe（独立度量器）/ baseline_emulator（条件 A 反例）
references/              OUTPUT_CONTRACT.md（契约 + 状态矩阵 + 可测判定 + 机制映射）
                         RUBRIC_MAP.md（五维落点 + §8–§12 四套新维度）
                         failure-modes.md（失败处置五个视图）
                         FAULT-MATRIX.md（24 场景四形态实测 + 恢复演练 + 三处静默失败修复）
                         GAIN-PROTOCOL.md（8 项指标 + 对照协议 + 附录 A/B 对照方案全文）
                         MECHANISM.md（M1–M6 机制 + §7 资产清单与复用三步）
                         CASE-SET.md（3 案题集 + 逐案实测 + 失效边界 F1–F10）
                         mechanism-spec.md（规格/命名/区室 + §9 符号语义与数据编码）
assets/                  mechanism-spec.schema.json / palettes.json / result.template.json
templates/               relation-checklist-template.md（关系核对清单，CP3 核验载体）
examples/                内置示例（case.json / task.md / materials/ / model.example.json /
                         README.md / EXPECTED-OUTPUT.md / output/ 实跑 JSON 产物）
examples/cases/          两个互补合成案例（各含 case.json / task.md / material.md / model.json）
                           immune-synapse/  跨膜募集 + 无数值（12 实体 / 12 边 / 4 区室）
                           plant-hormone/   基因-RNA + 有数值（8 实体 / 8 边 / 2 区室）
```

## 5. 依赖与环境

- **运行必需**：Python 3.8+，**仅标准库**（可编辑 SVG、机制规格、审计、契约、失败注入、
  增益度量全部无第三方依赖）。
- **可选**：`matplotlib`（PNG/PDF 预览；缺失时降级为仅 SVG 并如实记录）、
  `Pillow`（PNG 尺寸校验；缺失时降级为 warn）。安装：`pip install matplotlib pillow`。
- 实测环境：Python 3.13 + matplotlib + Pillow；纯标准库路径（`--formats svg`）同样可用。
- **字体**：SVG 用 CSS 标准字体栈（查看端决定字体）；PNG/PDF 由 matplotlib 选系统字体，
  缺中文字体时告警并写入 `export_checks`/`uncertainty`。包内不含任何 `.ttf/.otf`。
- **无本机路径依赖**：脚本用 `os.path.dirname(__file__)` 自定位；包内文本不含本机盘符绝对路径。

## 6. 适用范围与限制

- **适用**：机制图 / 通路图 / 信号级联 / 调控网络 / 流程图 / 图表编辑；也包括
  "先确认这条流水线在坏输入下的行为、以及换题材是否还灵"的前期判断。
- **不适用**：数值统计与统计结论、实验方案设计、论文写作与版式美化（相邻课题负责）。
- **明说的边界**：本包泛化的是"实体—关系—区室—图例"这套结构，**不是**"从任意自然语言/PDF
  自动读懂机制"。散文材料与 PDF 走人工建规格；枚举外类型直接 `failed`；契约自定义字段只保证
  "形态回显"不保证语义；逆流边只给 `warn`；失败注入演练的 stub 只能覆盖 `ImportError`/`RuntimeError`
  两类依赖故障，不能模拟"依赖装了一半"。逐条见 `references/CASE-SET.md` §4 与 `FAULT-MATRIX.md` §6。
- 图件不在包内，是运行时产物；确定性承诺 = SVG/PNG/model/topology/legend_audit；
  `result.json` 与 PDF 含时间戳。

## 7. 四个可复算读数（本机实测，2026-11-22 +08）

| 读数 | 结果 | 复跑入口 |
|-|-|-|
| 失败注入矩阵 | 24 场景 **24/24 符合期望**、**0 静默失败**、恢复演练 **6/6** | `scripts/fault_inject.py` |
| 增益对照（8 项指标） | 结构/溯源/语义/图例/契约/审计/导出 条件 A `0.0` → 条件 B `1.0`；实体名覆盖两侧均 `1.0`（如实标为非差异点） | `scripts/gain_probe.py --compare` |
| 机制消融 | M1–M6 每条给出"去掉会退化成什么"与可验证信号（含 schema 门 `exit 3`、双审计对基础形态 `exit 1`） | `references/MECHANISM.md` §2 |
| 题集 | 3 个题材不重叠的案例 **exit 0 / success / gates 8/8**（实体边 9/9、12/12、8/8）；案例 A 3 条 warn 逐条可解释 | `references/CASE-SET.md` §3/§5 |

## 8. 维护与更新

- 改颜色/线宽：只改 `assets/palettes.json`（全图与图例同步）；
- 改契约/门：`references/OUTPUT_CONTRACT.md` + `scripts/check_contract.py` +
  `scripts/result_writer.py` 三处同步；
- 改校验规则：`scripts/topology.py` / `legend_audit.py` / `validate_figure.py`，
  并同步 `references/mechanism-spec.md` §5 的校验一览；
- 改语义枚举：`assets/mechanism-spec.schema.json` + `references/mechanism-spec.md` §9；
- **改任何脚本后必须**：跑 `TEST.md` 全套 → 跑 `scripts/fault_inject.py` 并把新台账写回
  `references/FAULT-MATRIX.md` → 在 `worklog.md` 追加带时间的记录；
- 明令禁止：向包内添加二进制资源（`.png/.pdf/.svg/.pptx/.ttf/...`）或 `__pycache__`；
  图件必须运行时生成。
