# COMPARE.md — 对照口径：本 Skill 与"不加载 Skill 的基础 Agent"

> 用途：**使用增益 25 分**要求证明"相同输入、相同工具权限"下，加载本 Skill 后图稿质量稳定提升。
> 平台自行运行该对照（基础条件 vs 加载 Skill 条件，每条件 3 次重复）；本文件只说明
> **判据从哪里来、任何人怎么在本地复算同一套判据**。
> 本文件**不声称任何 benchmark 分数**——分数由平台运行产生，参赛者不得自造。

## 1. 对照条件

| 条件 | 输入 | 工具权限 | 预算 |
|---|---|---|---|
| 基础（baseline） | 同一 `case.json` + `task.md` + 同一材料目录 | 通用 Agent 能力（读文件、写文件、绘图库） | 平台固定（64 请求 / 900 秒 / 16384 tokens/响应） |
| 加载 Skill | **完全相同**的输入 | 同上 + 本 Skill 的 `SKILL.md` 与 `scripts/` | 同上 |

预算、模型、案例与工具权限由平台保证一致，因此差异只能来自 Skill 提供的**流程、规则与校验**。

## 2. 判据来自哪几条决策规则（可本地复算）

下表每一行都是"基础 Agent 的常见做法 → 本 Skill 的规则与检查 → 用什么命令复算"。
判据全部是机器判定，因此第三方不需要相信自述。

| 决策规则 | 基础条件的常见结果 | 加载 Skill 后的判定 | 复算方式 |
|---|---|---|---|
| **D12 / D13**（图例覆盖与颜色越界） | 画了节点与箭头但不给图例，或图例色与图面不一致 | 图面在用的类型必须全部在图例里，颜色必须 ⊆ 图例 ∪ 映射；否则 `L01/L02/L05` **fail** | `validate_figure.py --out <out>`（exit 0 = 通过） |
| **D8**（箭头语义） | 所有关系画成同一种箭头 | 5 类语义各有端点/颜色；`L02` 校验"图上的箭头数 = 图例声明的箭头数" | 同上；另见 `legend_audit.json` |
| **D9 / D3**（方向与区室） | 上下游颠倒、跨膜受体画在膜内、核内因子画在胞外 | `P03`（逆流边必须标反馈或给理由）、`P04b`（区室必须在词表内） | `topology.json` 的 P 系列条目 |
| **D14**（数值溯源） | 颜色/大小来自"印象"，无来源 | 数值必须有 `source`；`E01` 对无源数值**阻断** | `legend_audit.json` 的 E01；`validate_figure.py` |
| **D19 / D20**（契约四形态） | 通常没有 `result.json`，或字段缺项、含 null | 信封 19 键 + `output_contract` 全部字段回显，**顶层无 null** | `check_contract.py --result <out>/result.json --case <case.json>` |
| **D16 / D22**（降级与状态一致性） | 缺预览时仍声称"已完成" | 缺预览 → `partial` + exit 2 + `gates.g5_png=false`，`previews=[]` | `echo $?` 与 `result.json.status / gates` 三者对拍 |
| **D21**（failed 后的交付） | 失败后没有产物也没有说明 | `failed` 仍写最小信封（14 键）并在 `uncertainty` 给补救路径 | 见 `TEST.md` §6 的实测记录 |
| **D23**（自定位） | 命令假设 `cwd` = 项目根，换目录即失败 | 命令用 `$SKILL_DIR`，脚本 `__file__` 自定位，任意 `cwd` 可跑 | 在临时目录副本、`cwd≠技能根`下复跑 `TEST.md` §0 |

## 3. 本地复算步骤（任何人都能跑）

```bash
export SKILL_DIR=/path/to/challenge-83d4f050
# 条件 A（基础）由平台运行；本地若要诚实对照，请用同一份材料让通用 Agent 直接出图。
# 条件 B（加载 Skill）：
python3 "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
    --model-file "$SKILL_DIR/examples/model.example.json" --out /tmp/with-skill
# 判据复算（对任一条件的产物目录都适用）
python3 "$SKILL_DIR/scripts/check_contract.py" \
    --result /tmp/with-skill/result.json --case "$SKILL_DIR/examples/case.json"
python3 "$SKILL_DIR/scripts/validate_figure.py" --out /tmp/with-skill
```

**预期**：基础条件的产物通常缺 `result.json`（第一条命令直接非零退出）、缺来源标注或
图例与图面不一致（第二条命令报 fail）——这就是"增益可验证"的可执行形式。

## 4. 效率侧的可比量（对应"效率增益 5"）

| 操作 | 基础条件 | 加载 Skill 后 | 复算 |
|---|---|---|---|
| 从结构化材料出初稿 | 逐条誊写 | `extract.py` 一步出草稿（实体+边+行号来源） | `python3 "$SKILL_DIR/scripts/extract.py" <材料>`（独立 CLI） |
| 改一个标签/箭头 | 重画或手工改图 | 改 `model.json` 后 `--model-file` 重跑一次：SVG/PNG/PDF 全部重生成，0 次重画 | `TEST.md` §3（实测 1 次编辑 + 1 次重跑） |
| 图例与图面同步 | 人工比对 | 调色板单点改 + `legend_audit.py` 自动比对 | `assets/palettes.json`、`legend_audit.json` |
| 失败后定位 | 无记录 | 每条失败分支都有指定记录位点 | `SKILL.md` §2 最后一列 |

## 5. 边界（诚实声明）

- 本包**不运行、也不伪造**平台的对照实验与分数；只提供判据与可复跑命令。
- 可机器判定的部分是**结构性与可核验性**（类型 / 方向 / 图例 / 溯源 / 契约 / 确定性 / 降级诚实性）；
  图面美观度仍由人/模型评审判定，本包不作承诺。
- `examples/` 是 Skill 自带演示，与平台固定 3 个正式案例无关；示例结果不得冒充正式结果。
- 本期各题分数线由组织方测评产生，本包不引用、不预测。
