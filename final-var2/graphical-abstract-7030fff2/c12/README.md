# graphical-abstract — 图形摘要 Skill（文档轴 B：增益可验证）

把一项研究压进**单页**：研究问题 → 方法 → 核心结果 → 结论；交付**可编辑分层 SVG**
（不是位图截图）+ PNG/PDF 预览 + 字段完整的 `result.json`（来源、状态、不确定性、
变更记录、契约四形态回显）。数值只来自材料，**不编造**。

本包的特点不在功能清单更长，而在**"改进幅度能被别人复算"**：

| 你会拿到的 | 位置 | 作用 |
|-|-|-|
| 对照协议 | [`references/GAIN-PROTOCOL.md`](references/GAIN-PROTOCOL.md) | 定义条件 A（加载本 Skill）/ B（不加载 Skill 的基础做法）/ B+（把 B 的最强项补满）；写明可比条件、指标口径、复算命令与局限 |
| 只读测量器 | `scripts/gain_harness.py` | 对**任意**输出目录算同一组指标（G1–G8），自己不出图、不参与流水线 |
| 真实对照记录 | GAIN-PROTOCOL §4 | 本机实跑 A/B/B+ 的原始指标，含**对 A 不利**的观测（A 单次更慢、B 也确定性、A 的溯源覆盖率是 0.903 而非 1.000） |

一句话口径：**A 的收益在"结构可核验 + 免返工"，不在单次速度**（见 GAIN-PROTOCOL §5）。

## 0. 自定位（所有命令以此为基准）

```bash
SKILL_DIR=/skills/weekly-skill        # 官方评测容器
SKILL_DIR=/abs/path/to/<skill-root>   # 本机解压位置
SKILL_DIR="$(pwd)"; while [ ! -f "$SKILL_DIR/SKILL.md" ] && [ "$SKILL_DIR" != "/" ]; do SKILL_DIR="$(dirname "$SKILL_DIR")"; done
```

## 1. 出图（四步）

```bash
# ① 方案先行：生成骨架（含真实抽取结果与来源定位）→ 读材料后填 four_elements
python "$SKILL_DIR/scripts/scaffold.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/plan.json

# ② CP1 门：方案 lint（exit 0 才继续绘制）
python "$SKILL_DIR/scripts/spec_lint.py" --lint-plan --plan /tmp/plan.json

# ③ 出图（一次命令产出 SVG/PNG/PDF/spec/content/audit/render_log/result.json）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --plan /tmp/plan.json --out /tmp/ga-out

# ④ 契约自查（exit 0 = 顶层覆盖「信封 18 键 ∪ 案例契约」且无 null）
python "$SKILL_DIR/scripts/check_contract.py" --result /tmp/ga-out/result.json --case "$SKILL_DIR/examples/case.json"
```

官方案例形态：

```bash
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --task /input/task.md --out /app/output
```

## 2. 复算增益（三步）

```bash
# ① 你的做法跑一遍（或用本包的 A 条件）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/ga-A

# ② 用同一把尺子量（--case 取契约期望字段，--material 供数值可定位性比对）
python "$SKILL_DIR/scripts/gain_harness.py" --out /tmp/ga-A \
       --case "$SKILL_DIR/examples/case.json" --material "$SKILL_DIR/examples/material.md" \
       --label A --json /tmp/ga-A-report.json

# ③ 想比确定性就再跑一次，然后比较结构指纹
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/ga-A2 >/dev/null
python "$SKILL_DIR/scripts/gain_harness.py" --compare /tmp/ga-A /tmp/ga-A2
```

指标含义（详细口径见 GAIN-PROTOCOL §3）：**G1** 可编辑性（分层数 / 真 `<text>` / 字形引用）、
**G2** 溯源覆盖率（`data-src` ÷ 科学元素）、**G3** 四要素覆盖、**G4** 数值可定位率、
**G5** 契约完整率、**G6** 结构确定性、**G7** 证据文件完备性、**G8** 效率（单次墙钟 + 返工步数）。

## 3. 参数

| 参数 | 说明 |
|-|-|
| `--case` | `case.json`（必填） |
| `--task` | `task.md`（缺省自动找 `<case_dir>/task.md`） |
| `--material` | 材料文件或目录（缺省用 `case.source_material`） |
| `--plan` | 设计方案（`scaffold.py` 生成、Agent 定稿；可选） |
| `--raster-scale` | PNG 分辨率倍率（默认取 `figure_constraints`） |
| `--pdf` / `--no-pdf` | PDF 开关（默认取 `figure_constraints`） |
| `--out` | 输出目录（默认 `<skill>/out`） |

`scripts/gain_harness.py` 的参数：`--out` / `--case` / `--material` / `--label` / `--json` / `--compare A B`。

## 4. 依赖

- **必需**：Python ≥ 3.8，核心流程只用标准库（含纯 Python PNG 回退）；测量器只用标准库；
- **可选**：`matplotlib`（默认渲染 + PDF）、`Pillow`（二级渲染）——缺失时逐级回退并记录；
- **字体**：运行期探测候选路径（`C:/Windows/Fonts`、`/usr/share/fonts`、`/System/Library/Fonts`），
  找不到就降级；**SVG 的 `<text>` 始终是真文字**，可编辑性不随渲染降级丢失；
- **不联网**；测量器**不写任何图**。

## 5. 结果里有哪些可核验字段

`result.json`：`case_id` / `status` / `deliverables[]` / `provenance.source_files[]`(含 sha256) /
`sources[]` / `uncertainty[]` / `warnings[]` / `change_records[]` / `audit` / `plan` / `spec_lint` /
契约字段顶层回显（`output_contract_echo` 记录保留键冲突）。
`audit.json`：实体覆盖率、数值编码一致性、越界、缺值、四要素覆盖、图层命名、确定性探针。
`render_log.json`：实际后端与字体、降级告警。

字段级契约（**唯一评分产物**）见 [`references/OUTPUT_CONTRACT.md`](references/OUTPUT_CONTRACT.md)；
评分维度对应见 [`references/RUBRIC_MAP.md`](references/RUBRIC_MAP.md)。

## 6. 限制（如实声明）

- 本地对照的条件 B 是**最小复现脚本**，不是真实无 Skill 的 LLM Agent；机制层面的差距可归因，
  但正式对照以平台白板为准；
- 指标是结构与文本级判据，不评价美观与领域结论；
- 渲染后端可能降级；降级后 PNG 文字可能为占位框（SVG 不受影响）；
- 单案例、单机的观测**不构成统计显著性**；`examples/` 是合成示例，与平台正式案例无关。

## 7. 维护

- 版本号：`scripts/common.py` 的 `SKILL_VERSION`；改动历史见 git 与 `result.json.change_records`；
- 新增指标：先在 `references/GAIN-PROTOCOL.md` §3 登记口径，再在 `scripts/gain_harness.py` 实现，
  最后在 `TEST.md` 记录一条真实数字 —— **三处齐了才算加了一个指标**；
- 新增图层/元素类型：登记 `references/layer-naming.md`，同步 `scripts/audit.py` 的 `EXPECTED_LAYERS`；
- 更新对照记录时：**连同不利观测一起更新**，只报有利项会让整个协议失去可信度。
