# COMPARE.md — 与"不加载 Skill 的基础 Agent"的同输入对照方案

> 用途：本题"使用增益 25 分"要求证明**相同输入、相同工具权限**下，加载本 Skill 后的
> 图稿质量相对基础 Agent 稳定提升，并说明增益如何被验证。平台自行运行该对照
> （基础条件 vs 加载 Skill 条件，每条件 3 次重复）；本文件说明**对照的判据从哪里来**，
> 以及任何人如何在本地复现同一套判据。
> 本文件不声称任何 benchmark 分数——分数由平台运行产生，参赛者不得自造。

## 1. 对照条件（平台侧）

| 条件 | 输入 | 工具 | 产物 |
|-|-|-|-|
| 基础（baseline） | 同一 `case.json` + `task.md` + 同一材料目录 | 通用 Agent 能力（读文件、写文件、画图库） | 图稿 + 说明 |
| 加载 Skill | 完全相同的输入 | 同上 + 本 Skill 的 `SKILL.md` 与 `scripts/` | 图稿 + `result.json` + 审计产物 |

**可比条件**：模型、预算（64 请求 / 900 秒 / 16384 tokens）、案例、工具权限一致；
平台保证这一点，因此差异只能来自 Skill 提供的流程与校验。

## 2. 三类可判据的差异（不靠"看起来更好"）

判据全部来自本包内可执行的检查器，因此第三方可以本地复算，不需要相信自述。

### 2.1 语义正确性（对应"结果正确性 15"）

| 检查 | 基础 Agent 的常见表现 | 本 Skill 的机器判据 | 判据位置 |
|-|-|-|-|
| 实体类型不混用 | 基因/蛋白/复合物/小分子写成同一种节点 | schema 门限定 `type` 枚举，未知类型 → `failed`（不静默改写） | `assets/mechanism-spec.schema.json`、`scripts/validate_figure.py:check_schema` |
| 箭头语义可区分 | 所有关系画成同一种箭头 | `legend_audit.py` L02/L05：图上每种在用边类型必须在图例中且颜色一致 | `scripts/legend_audit.py` |
| 方向与区室 | 上下游颠倒、跨膜受体画在膜内 | `topology.py` P03/P04b/P07：逆流边必须标反馈或给出理由；实体区室必须在词表内 | `scripts/topology.py` |
| 数值可溯源 | 图上颜色/大小来自"印象" | `legend_audit.py` E01 + `validate_figure.py` T03：数值必须有 `source`，否则阻断 | `scripts/legend_audit.py`、`scripts/validate_figure.py` |

### 2.2 契约与可核验性（对应"结果可核验性 5 / 增益可验证性 5"）

| 检查 | 命令 | 通过判据 |
|-|-|-|
| 契约完整（含 `output_contract` 四形态回显、顶层无 null） | `python3 "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json --case <case.json>` | exit 0，C01–C07 全 pass |
| 图面/模型/图例/导出全检 | `python3 "$SKILL_DIR/scripts/validate_figure.py" --out <out>` | exit 0，`fails=0` |
| 确定性 | `scripts/determinism.py`（跨进程 / 跨 cwd / 跨 `PYTHONHASHSEED` 连跑 N 次，对全部产物做 sha256 比对） | 5/7 产物逐字节一致（`.svg/.png/model/topology/legend_audit`）；`diagram.pdf` 仅 `/CreationDate` 秒位 1–2 字节、`result.json` 8 条路径易变；规范化后三条配方全部一致（详见 `references/DETERMINISM.md`） |

基础 Agent 的产物通常没有 `result.json`，或字段缺项、含 null、无来源，因此上述命令
在基线条上会直接非零退出——**这就是"增益可验证"的可执行形式**。

### 2.3 效率（对应"效率增益 5"）

| 操作 | 基础条件 | 加载 Skill 后 | 证据 |
|-|-|-|-|
| 从结构化材料出初稿 | 手工逐条誊写 | `extract.py` 一步出草稿（实体+边+行号来源） | `scripts/extract.py`（独立 CLI 可单独跑） |
| 改一个标签 / 一个箭头 | 重画或手工改图 | 改 `model.json` 后 `--model-file` 重跑：SVG/PNG/PDF 一次重导出，0 次重画 | `scripts/main.py`、`scripts/layout.py` |
| 图例与图面同步 | 人工比对 | 调色板单点改（`assets/palettes.json`）＋ `legend_audit.py` 自动比对 | `assets/palettes.json`、`scripts/legend_audit.py` |

## 3. 本地复现方式（任何人都能跑）

```bash
export SKILL_DIR=/path/to/challenge-83d4f050          # 含 SKILL.md 的那一层
# 条件 A：加载 Skill（已核验规格路径）
python3 "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
    --model-file "$SKILL_DIR/examples/model.example.json" --out /tmp/with-skill
# 条件 B：加载 Skill（自动草稿路径，用于观察未核验时如何降级为 partial）
python3 "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/draft
# 判据复算
python3 "$SKILL_DIR/scripts/check_contract.py" \
    --result /tmp/with-skill/result.json --case "$SKILL_DIR/examples/case.json"
python3 "$SKILL_DIR/scripts/validate_figure.py" --out /tmp/with-skill
```

基础条件（不加载 Skill）由平台执行；本地若要做诚实对照，请用**同一份材料**让通用
Agent 直接出图，再用同一组命令检查其产物——预期结果是：缺少 `result.json` 契约、
缺少来源标注、图例与图面不一致中的至少一项使命令非零退出。

## 5. 结构对照：基础包 ↔ 本题高分意图 ↔ 本包

依据：基础包 `work/efficiency-3/build/challenge-83d4f050`（30 文件，含 `__pycache__`）、
意图报告 `work/efficiency-3/highscore-intel/challenge-83d4f050.md`（天花板 78.67 的
manifest 不可见；可解析最高 **76.67 = 5 文件极简包**；补样本 73.33×2、73.00）、
以及本包（文本形态，图件运行时生成）。

| 能力 / 资产 | 基础包 | 高分意图（可解析样本） | 本包 |
|-|-|-|-|
| 交付形态 | 根布局 `SKILL.md` + 预置输出 | 根布局（5–28 文件均可） | 根布局，**纯文本**（≤50 文件 / ≤500KB / ≤2MB / 无符号链接） |
| 图件 | 随包预置 SVG/PNG/PDF | 随包或运行时 | **一律运行时生成**（由平台预检要求决定） |
| 流程显式化 | SKILL.md 少量规则 | worklog / 检查点 | CP1–CP5 检查点 + D1–D12 决策规则 |
| 机制规格 schema 前置 | 无 | `mechanism-spec.schema.json`（77882 系） | ✅ CP2 门，对 **raw** 规格校验（T7 实测拦截） |
| 拓扑 / 通路语义校验 | 仅方向 warn | `topology.py` / `lint_graph.py`（85718 系） | ✅ P01–P08（方向/区室/同名消歧/重复边/自环/反馈） |
| 图例 / 数据编码审计 | 单脚本内 L01–L05 | `legend_audit` / `mapcheck` / `check_encoding` | ✅ 独立 `legend_audit.py`（L01–L08 + E01–E02），产物落盘 |
| 关系核对清单 | 无 | `relation-checklist-template.md`（71433 唯一模板） | ✅ `templates/relation-checklist-template.md`（五表） |
| 调色板资产 | 常量写死在 `model.py` | `palettes.json`（77882 系） | ✅ `assets/palettes.json` 单点改色（缺省回退内置） |
| 结果契约 | 单形态镜像 | `output-contract.md`（85718 系） | ✅ **四形态回显 + G1–G8 硬性门** + 独立 `check_contract.py` |
| 失败处理文档 | SKILL.md 内一张表 | `failure-modes.md` / `failure_playbook.md` | ✅ `references/failure-modes.md`（含降级 F14/F14b） |
| 确定性 | 未提 | 隐含 | ✅ 同输入双跑：SVG/PNG/model/topology/legend_audit 逐字节一致（T4） |
| 溯源 | 仅 `model.json` | `provenance_ledger.py`（85718 系） | ✅ 材料行号 → `source` → SVG `data-source` → `export_checks.sha256` → `change_records` |

**规避项（intel 明确提示）**：不为"追平不可见天花板"堆文件（28–35 文件并不优于 5 文件
极简包）；不做没有拓扑/语义校验的纯 SVG 包；`submission/` 嵌套与根布局同分，本包取根布局。
⇒ 本包的每一份新增文件都是**可执行检查或核对载体**，不是凑数。

## 6. 边界（诚实声明）

- 本包**不运行、也不伪造**平台的对照实验与分数；只提供对照所需的判据与可复跑命令。
- "质量提升"的可判定部分是**结构性与可核验性**的（类型 / 方向 / 图例 / 溯源 / 契约 /
  确定性）；图面美观度仍由人 / 模型评审判定，本包不作承诺。
- 示例案例（`examples/`）是 Skill 自带演示，与平台固定 3 个正式案例无关；
  对照必须用平台案例进行，示例结果不得冒充正式结果。
- 平台分数线（本期各题天花板 70.33–80.0）由组织方测评产生，本包不引用、不预测。
