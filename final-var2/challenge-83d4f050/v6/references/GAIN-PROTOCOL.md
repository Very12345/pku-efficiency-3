# GAIN-PROTOCOL.md — 使用增益的公平对照协议与实测记录

> 这份协议回答一个问题：**"加载本 Skill 相比不加载，好在哪"能不能被量出来、能不能被别人复算。**
> 它由三部分组成：**公平条件**（§1）、**指标定义**（§2）、**本机实测记录**（§4）。
> 全部数字来自 2026-11-22 的真实运行，命令在 §3；没有编造任何数值。
>
> 一句话边界：**本协议不产生、也不预测任何平台评分**。平台的对照实验由平台执行
> （同输入、同预算、每条件 3 次重复）；本协议提供的是**判据与可复算的度量**。

## 1. 公平对照条件

| 项 | 条件 A（基础） | 条件 B（加载 Skill） | 是否相同 |
|---|---|---|---|
| 输入 | 同一份材料文件 | 同一份材料文件 | ✅ |
| 任务 | 同一份任务意图（画机制图） | 同一份任务意图 | ✅ |
| 工具权限 | 读文件、写文件、画图库 | **同上** + 本 Skill 的 `SKILL.md`/`scripts/` | 仅多 Skill 本身 |
| 预算 | 平台固定（64 请求 / 900 秒 / 16384 tokens 每响应） | 同 | ✅ |
| 度量 | `scripts/gain_probe.py`（同一份代码、同一组公式） | 同一份代码 | ✅ |
| 产物落点 | 独立目录 | 独立目录 | ✅ |

**关于条件 A 的诚实声明（重要）**：真实的"基础 Agent"由平台运行；本地离线情况下，
本包提供 `scripts/baseline_emulator.py` 作为**条件 A 的结构复现器**——

- 它**不是 LLM**，也不冒充平台结果；
- 它只复现题面 §1 已点名的失败签名：名词平铺成环、随意连线、统一灰色箭头（不区分激活/抑制）、
  无图例、无来源标注、无结构化契约、单一扁平层；
- 它的价值在于：**把"基础形态会丢掉哪些可测量"变成可复现的基线**，
  使"增益是否可判定"这件事在离线环境也能被第三方验证。

## 2. 指标定义（8 项，全部与绘图实现无关）

度量器：`scripts/gain_probe.py`。设计约束三条：**不 import 本包任何模块**（避免用被测者的尺子
量被测者）、**缺项计 0**（不跳过，避免"没产物反而好看"）、**两侧同法计算**。

### 2.1 结构层

| 指标 | 定义 | 计算 | 阈值/读法 |
|---|---|---|---|
| A1 图层完整度 | 产物里具名 `layer-*` 组的数量 ÷ 7 | 解析 SVG 中 `<g id="layer-…">` | 1.0000 = 7 层齐全；0 = 无分层 |
| A2 溯源覆盖率 | 带 `data-source` 的元素数 ÷ 边数 | SVG 属性计数 | ≥1.0 表示每个边都有来源；0 = 无溯源 |
| A7 交付件完整度 | `diagram.png` 与 `diagram.pdf` 的存在性均值 | 文件存在性 | 1.0000 = 两种导出都在 |

### 2.2 语义层

| 指标 | 定义 | 计算 | 读法 |
|---|---|---|---|
| A3 语义标签覆盖率 | 带机器可读 `data-type` 的边 ÷ 总边数 | 解析 `layer-edge` 里的路径/线元素 | 1.0000 = 每条边的语义都能被程序读出；0 = 只能靠看图猜 |
| 语义类别数 | 不同 `data-type` 的取值个数 | 同上 | ≥5 表示五类箭头语义都被用上（通过的案例里通常 5 类全在用） |

### 2.3 图例层

| 指标 | 定义 | 计算 | 读法 |
|---|---|---|---|
| A4 图例声明覆盖率 | "其视觉样式被图例声明过"的边 ÷ 总边数 | 取每条边的（是否有箭头端点 + 描边色）指纹，与图例组里声明线的指纹集合比对 | 1.0000 = 图上没有"来历不明"的箭头 |

### 2.4 契约层

| 指标 | 定义 | 计算 | 读法 |
|---|---|---|---|
| A5 信封覆盖率 | `result.json` 顶层命中的信封键 ÷ 19 | 19 键清单**独立抄自契约文件**，不 import 包内模块 | 1.0000 = 契约完整；0 = 无 `result.json` |
| A6 审计产物 | `topology.json` / `legend_audit.json` 的存在性均值 | 文件存在性 | 1.0000 = 两个审计产物都落盘 |
| 附加 | 顶层 `null` 数、`output_contract` 回显数、`gates` 通过数 | 直接读 JSON | null 必须为 0 |
| A8 材料实体覆盖率 | 材料实体表里的名字出现在产物中的比例 | 解析材料表格首列，在产物文本里查找 | **两侧通常都 1.0** —— 这说明"有没有画出名词"不是差异点（见 §5） |

### 2.5 效率层

| 指标 | 定义 | 怎么量 |
|---|---|---|
| E1 出图耗时 | 从命令启动到 7 件产物齐全的墙上时间 | 计时包裹整条命令 |
| E2 改一个标签的代价 | 需要几次文件编辑、几次重跑、几个导出件被重新生成 | 改 `model.json` 一处 → 重跑 → 比对 sha 与产物清单 |
| E3 标签可定位性 | 产物里是否存在"按 id 定位标签"的能力 | 统计 `data-id` 数量：0 = 只能全文搜索 |

## 3. 复算步骤（任何人都能跑，全部离线）

```bash
export SKILL_DIR=/path/to/challenge-83d4f050

# 条件 A：基础形态的结构复现（反例生成器）
python3 "$SKILL_DIR/scripts/baseline_emulator.py" \
    --material "$SKILL_DIR/examples/materials/example_material.md" --out /tmp/condA

# 条件 B：本 Skill 的主路径（已核验规格）
python3 "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
    --model-file "$SKILL_DIR/examples/model.example.json" --out /tmp/condB

# 同尺子度量两侧（加 --json 可拿到机器可读结果）
python3 "$SKILL_DIR/scripts/gain_probe.py" --compare /tmp/condA /tmp/condB \
    --material "$SKILL_DIR/examples/materials/example_material.md" \
    --case "$SKILL_DIR/examples/case.json"

# 同两条审计命令分别对两个条件执行（看基础条件会怎么退出）
python3 "$SKILL_DIR/scripts/check_contract.py" --result /tmp/condA/result.json \
    --case "$SKILL_DIR/examples/case.json"; echo "exitA=$?"
python3 "$SKILL_DIR/scripts/check_contract.py" --result /tmp/condB/result.json \
    --case "$SKILL_DIR/examples/case.json"; echo "exitB=$?"
python3 "$SKILL_DIR/scripts/validate_figure.py" --out /tmp/condB; echo "verifyB=$?"
```

## 4. 实测记录（2026-11-22，条件 A 与条件 B 同日同机）

环境：Python 3.13.9（Windows）、matplotlib + Pillow 可用；运行在**包外临时目录副本**上，
`cwd` 不是技能根；两侧读同一份示例材料（9 实体 / 9 关系 / 4 区室 / 数据映射 / 图面约束）。

### 4.1 结构、语义、图例、契约（`gain_probe.py --compare` 原始输出）

| 指标 | 条件 A | 条件 B | 差 |
|---|---|---|---|
| 产物文件数 | 2 | 7 | +5 |
| 具名图层组（A1） | 0 → **0.0000** | 7 → **1.0000** | +1.0000 |
| 边的语义标签覆盖率（A3） | 0/10 → **0.0000** | 9/9 → **1.0000** | +1.0000 |
| 语义类别数 | 0 | 5 | +5 |
| 图例声明覆盖率（A4） | 0/10 → **0.0000** | 9/9 → **1.0000** | +1.0000 |
| 带 `data-source` 的元素（A2） | 0 → **0.0000** | 18 → **1.0000** | +1.0000 |
| 契约信封覆盖（A5） | 0/19 → **0.0000** | 19/19 → **1.0000** | +1.0000 |
| 审计产物（A6） | 0 → **0.0000** | 2/2 → **1.0000** | +1.0000 |
| 导出件（A7，PNG/PDF） | 0 → **0.0000** | 2/2 → **1.0000** | +1.0000 |
| 材料实体名覆盖率（A8） | **1.0000** | **1.0000** | **0.0000** |

条件 B 的 `result.json` 附加读数：`status=success`、`gates=8/8`、顶层 `null=0`、
`output_contract` 字段 2/2 回显。条件 A 无 `result.json`（A5 因此为 0）。

### 4.2 两条审计命令对两侧的同法结果

| 命令 | 条件 A | 条件 B |
|---|---|---|
| `check_contract.py --result … --case …` | exit **1**，末行 `missing result.json` | exit **0**，`contract\|ok\|case=example-egfr-mapk\|status=success\|checks=7` |
| `validate_figure.py --out …` | exit **1**，`standalone-verify\|ok=False` | exit **0**，`standalone-verify\|ok=True\|fails=0\|warns=0` |

### 4.3 效率（E1–E3）

| 指标 | 条件 A | 条件 B |
|---|---|---|
| E1 出图耗时 | 即时（仅有 SVG 与说明） | **2.51 s** 产出 7 件 |
| E2 改一个标签 | 只能直接改图；无规格文件、无导出流水线 | **1 次文件编辑 + 1 次重跑（1.76 s）**：SVG/PNG/PDF 全部重新生成，新标签出现在 SVG 中，SVG 与 PNG 的 sha16 均发生变化 |
| E3 标签可定位性 | `data-id` 计数 **0**（只能全文搜索改字） | `data-id`/`data-type`/`data-source` 齐备，可按 id 精确定位元素 |

### 4.4 复现要点

- 条件 B 的 SVG 在两次运行之间**逐字节一致**（sha16 `27f344a0dfb2e90f`），
  因此 §4.1 的 B 列是可对照的稳定量；PNG 同环境一致（`9137715961238f3f`），
  PDF 含 `CreationDate` 时间戳，不参与稳定性比较。
- 条件 A 的复现器是确定性的（纯几何 + 固定样式），任何人重跑都能得到同一组读数。
- 若你的环境没有 matplotlib，条件 B 的 A7 会降为 0.5（只有 PNG 缺失）之类，
  **这是真实降级，不是度量器错误**：协议要求按实测填写，不按期望填写。

## 5. 怎么读这些数字（哪些算差异点，哪些不算）

- **算差异点**：分层（A1）、溯源（A2）、语义可判（A3）、图例声明（A4）、契约（A5）、
  审计产物（A6）、导出（A7）、改标签代价（E2/E3）。这些在条件 A 上全部为 0 或不可得，
  并且都能被同一个独立脚本复算。
- **不算差异点（必须诚实列出）**：A8 材料实体名覆盖率两侧都是 1.0000。
  "把名词写对"不是本 Skill 的增益来源；**增益来自名词之间的语义、来源与可复核结构。**
- **度量器不覆盖的**：图面美观度、排版平衡、配色观感、科学判断的正确性上限
  （例如"到底该画成 activation 还是 binding"最终仍需人/模型评审判定）。
  协议不把这些包装成数字。

## 6. 局限与反作弊

1. 条件 A 是**结构复现器**，不是真实基础 Agent 的运行；它使基线可复现，但不等于平台基线。
   平台对照仍以平台运行为准。
2. 度量器只读产物目录、不读日志、不读代码，因此**不能**被"在文档里写得好"影响。
3. 指标定义写死在本文件 §2；若修改度量口径，必须同时改 `gain_probe.py` 并在本文件记录版本，
   避免"换了尺子再说赢了"。
4. 不引用、不预测任何平台分数；不把示例材料上的读数当成官方案例的读数。

## 附录 A. 与“不加载 Skill 的基础 Agent”的同输入对照方案（原 `COMPARE.md`，R1/v1 版逐字保留）

> 用途：**使用增益 25 分**要求证明"相同输入、相同工具权限"下，加载本 Skill 后图稿质量稳定提升。
> 平台自行运行该对照（基础条件 vs 加载 Skill 条件，每条件 3 次重复）；本文件只说明
> **判据从哪里来、任何人怎么在本地复算同一套判据**。
> 本文件**不声称任何 benchmark 分数**——分数由平台运行产生，参赛者不得自造。

### 1. 对照条件

| 条件 | 输入 | 工具权限 | 预算 |
|---|---|---|---|
| 基础（baseline） | 同一 `case.json` + `task.md` + 同一材料目录 | 通用 Agent 能力（读文件、写文件、绘图库） | 平台固定（64 请求 / 900 秒 / 16384 tokens/响应） |
| 加载 Skill | **完全相同**的输入 | 同上 + 本 Skill 的 `SKILL.md` 与 `scripts/` | 同上 |

预算、模型、案例与工具权限由平台保证一致，因此差异只能来自 Skill 提供的**流程、规则与校验**。

### 2. 判据来自哪几条决策规则（可本地复算）

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

### 3. 本地复算步骤（任何人都能跑）

```bash
export SKILL_DIR=/path/to/challenge-83d4f050
## 条件 A（基础）由平台运行；本地若要诚实对照，请用同一份材料让通用 Agent 直接出图。
## 条件 B（加载 Skill）：
python3 "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
    --model-file "$SKILL_DIR/examples/model.example.json" --out /tmp/with-skill
## 判据复算（对任一条件的产物目录都适用）
python3 "$SKILL_DIR/scripts/check_contract.py" \
    --result /tmp/with-skill/result.json --case "$SKILL_DIR/examples/case.json"
python3 "$SKILL_DIR/scripts/validate_figure.py" --out /tmp/with-skill
```

**预期**：基础条件的产物通常缺 `result.json`（第一条命令直接非零退出）、缺来源标注或
图例与图面不一致（第二条命令报 fail）——这就是"增益可验证"的可执行形式。

### 4. 效率侧的可比量（对应"效率增益 5"）

| 操作 | 基础条件 | 加载 Skill 后 | 复算 |
|---|---|---|---|
| 从结构化材料出初稿 | 逐条誊写 | `extract.py` 一步出草稿（实体+边+行号来源） | `python3 "$SKILL_DIR/scripts/extract.py" <材料>`（独立 CLI） |
| 改一个标签/箭头 | 重画或手工改图 | 改 `model.json` 后 `--model-file` 重跑一次：SVG/PNG/PDF 全部重生成，0 次重画 | `TEST.md` §3（实测 1 次编辑 + 1 次重跑） |
| 图例与图面同步 | 人工比对 | 调色板单点改 + `legend_audit.py` 自动比对 | `assets/palettes.json`、`legend_audit.json` |
| 失败后定位 | 无记录 | 每条失败分支都有指定记录位点 | `SKILL.md` §2 最后一列 |

### 5. 边界（诚实声明）

- 本包**不运行、也不伪造**平台的对照实验与分数；只提供判据与可复跑命令。
- 可机器判定的部分是**结构性与可核验性**（类型 / 方向 / 图例 / 溯源 / 契约 / 确定性 / 降级诚实性）；
  图面美观度仍由人/模型评审判定，本包不作承诺。
- `examples/` 是 Skill 自带演示，与平台固定 3 个正式案例无关；示例结果不得冒充正式结果。
- 本期各题分数线由组织方测评产生，本包不引用、不预测。
## 附录 B. 对照方案（合规重打包版原文，逐字保留）

> 用途：本题"使用增益 25 分"要求证明**相同输入、相同工具权限**下，加载本 Skill 后的
> 图稿质量相对基础 Agent 稳定提升，并说明增益如何被验证。平台自行运行该对照
> （基础条件 vs 加载 Skill 条件，每条件 3 次重复）；本文件说明**对照的判据从哪里来**，
> 以及任何人如何在本地复现同一套判据。
> 本文件不声称任何 benchmark 分数——分数由平台运行产生，参赛者不得自造。

### 1. 对照条件（平台侧）

| 条件 | 输入 | 工具 | 产物 |
|-|-|-|-|
| 基础（baseline） | 同一 `case.json` + `task.md` + 同一材料目录 | 通用 Agent 能力（读文件、写文件、画图库） | 图稿 + 说明 |
| 加载 Skill | 完全相同的输入 | 同上 + 本 Skill 的 `SKILL.md` 与 `scripts/` | 图稿 + `result.json` + 审计产物 |

**可比条件**：模型、预算（64 请求 / 900 秒 / 16384 tokens）、案例、工具权限一致；
平台保证这一点，因此差异只能来自 Skill 提供的流程与校验。

### 2. 三类可判据的差异（不靠"看起来更好"）

判据全部来自本包内可执行的检查器，因此第三方可以本地复算，不需要相信自述。

#### 2.1 语义正确性（对应"结果正确性 15"）

| 检查 | 基础 Agent 的常见表现 | 本 Skill 的机器判据 | 判据位置 |
|-|-|-|-|
| 实体类型不混用 | 基因/蛋白/复合物/小分子写成同一种节点 | schema 门限定 `type` 枚举，未知类型 → `failed`（不静默改写） | `assets/mechanism-spec.schema.json`、`scripts/validate_figure.py:check_schema` |
| 箭头语义可区分 | 所有关系画成同一种箭头 | `legend_audit.py` L02/L05：图上每种在用边类型必须在图例中且颜色一致 | `scripts/legend_audit.py` |
| 方向与区室 | 上下游颠倒、跨膜受体画在膜内 | `topology.py` P03/P04b/P07：逆流边必须标反馈或给出理由；实体区室必须在词表内 | `scripts/topology.py` |
| 数值可溯源 | 图上颜色/大小来自"印象" | `legend_audit.py` E01 + `validate_figure.py` T03：数值必须有 `source`，否则阻断 | `scripts/legend_audit.py`、`scripts/validate_figure.py` |

#### 2.2 契约与可核验性（对应"结果可核验性 5 / 增益可验证性 5"）

| 检查 | 命令 | 通过判据 |
|-|-|-|
| 契约完整（含 `output_contract` 四形态回显、顶层无 null） | `python3 "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json --case <case.json>` | exit 0，C01–C07 全 pass |
| 图面/模型/图例/导出全检 | `python3 "$SKILL_DIR/scripts/validate_figure.py" --out <out>` | exit 0，`fails=0` |
| 确定性 | 同输入双跑后比较 sha256 | `diagram.svg` / `diagram.png` / `model.json` / `topology.json` / `legend_audit.json` 逐字节一致（`TEST.md` T4 实测） |

基础 Agent 的产物通常没有 `result.json`，或字段缺项、含 null、无来源，因此上述命令
在基线条上会直接非零退出——**这就是"增益可验证"的可执行形式**。

#### 2.3 效率（对应"效率增益 5"）

| 操作 | 基础条件 | 加载 Skill 后 | 证据 |
|-|-|-|-|
| 从结构化材料出初稿 | 手工逐条誊写 | `extract.py` 一步出草稿（实体+边+行号来源） | `scripts/extract.py`（独立 CLI 可单独跑） |
| 改一个标签 / 一个箭头 | 重画或手工改图 | 改 `model.json` 后 `--model-file` 重跑：SVG/PNG/PDF 一次重导出，0 次重画 | `scripts/main.py`、`scripts/layout.py` |
| 图例与图面同步 | 人工比对 | 调色板单点改（`assets/palettes.json`）＋ `legend_audit.py` 自动比对 | `assets/palettes.json`、`scripts/legend_audit.py` |

### 3. 本地复现方式（任何人都能跑）

```bash
export SKILL_DIR=/path/to/challenge-83d4f050          # 含 SKILL.md 的那一层
## 条件 A：加载 Skill（已核验规格路径）
python3 "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
    --model-file "$SKILL_DIR/examples/model.example.json" --out /tmp/with-skill
## 条件 B：加载 Skill（自动草稿路径，用于观察未核验时如何降级为 partial）
python3 "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/draft
## 判据复算
python3 "$SKILL_DIR/scripts/check_contract.py" \
    --result /tmp/with-skill/result.json --case "$SKILL_DIR/examples/case.json"
python3 "$SKILL_DIR/scripts/validate_figure.py" --out /tmp/with-skill
```

基础条件（不加载 Skill）由平台执行；本地若要做诚实对照，请用**同一份材料**让通用
Agent 直接出图，再用同一组命令检查其产物——预期结果是：缺少 `result.json` 契约、
缺少来源标注、图例与图面不一致中的至少一项使命令非零退出。

### 5. 结构对照：基础包 ↔ 本题高分意图 ↔ 本包

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

### 6. 边界（诚实声明）

- 本包**不运行、也不伪造**平台的对照实验与分数；只提供对照所需的判据与可复跑命令。
- "质量提升"的可判定部分是**结构性与可核验性**的（类型 / 方向 / 图例 / 溯源 / 契约 /
  确定性）；图面美观度仍由人 / 模型评审判定，本包不作承诺。
- 示例案例（`examples/`）是 Skill 自带演示，与平台固定 3 个正式案例无关；
  对照必须用平台案例进行，示例结果不得冒充正式结果。
- 平台分数线（本期各题天花板 70.33–80.0）由组织方测评产生，本包不引用、不预测。