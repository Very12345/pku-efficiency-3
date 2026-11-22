---
name: biological-mechanism-pathway-diagram
description: >-
  把机制/通路材料转成可逐条核验的生物机制图与通路图，并让"它比基础 Agent 好在哪"
  变成可测的量：结构化机制规格 → 区室约束布局 → 可编辑分层 SVG 源 + PNG/PDF 预览 →
  拓扑与图例/数据编码审计 → 契约化 result.json；每一步都留下可被第三方独立测量的产物。
  附带与"不加载 Skill 的基础 Agent"的公平对照协议（同输入 / 同工具 / 同预算）、
  8 项结构指标的独立度量器，以及本机实跑的对照记录。
  Use when the task asks to draw, generate, edit, re-export or validate a biological
  mechanism map, pathway diagram, signaling cascade, regulatory network or flow
  diagram (figures group of the biology mechanism & pathway challenge), including
  tasks that require editable sources with per-element provenance.
---

# biological-mechanism-pathway-diagram（增益可验证版 · 文本包 · 图件运行时生成）

本包的第一原则：**"更好"必须能被量出来。** 因此流程里每一个环节都产出一份可被外部脚本读取的
证据（分层结构、溯源属性、语义标签、图例声明、契约信封、审计产物），而"增益"由
`scripts/gain_probe.py` 用同一把尺子同时量两个条件：**基础形态**与**加载本 Skill**。

> 包内**只有文本资源**（`.md .py .json .txt .csv .yaml .yml`）：契约要求
> `at most 50 UTF-8 text files, 500KB each and 2MB total, no symlinks`。
> `diagram.svg` / `diagram.png` / `diagram.pdf` 一律由 `scripts/` 在 `--out` 目录**运行时生成**。

## 0. 增益主张（每条都给出度量方式与阈值）

| # | 主张 | 度量 | 判定命令 | 期望 |
|---|---|---|---|---|
| G1 | 产物是**可编辑分层源**，不是一张扁平图 | 具名图层组数 `layer_groups` | `gain_probe.py --dir <out>` | ≥ 7 |
| G2 | 每个实体/边都带**机器可读溯源** | SVG 中 `data-source=` 计数 | 同上 | ≥ 边数 |
| G3 | 边语义**机器可判**（不是靠看图猜） | 带 `data-type` 的边 / 总边数 | 同上 | 1.0000 |
| G4 | 图例**声明了**图面上在用的每种箭头 | 图例声明覆盖的边 / 总边数 | 同上 | 1.0000 |
| G5 | 结果是**契约化**的，可被独立复查 | 信封键覆盖 / 19 | `check_contract.py` exit 0 | 19/19 |
| G6 | 关键判据**留了审计产物** | `topology.json` + `legend_audit.json` | `gain_probe.py` | 2/2 |
| G7 | 交付件不止一张图 | PNG + PDF 存在性 | `gain_probe.py` | 2/2 |
| G8 | 同输入**可复现** | 双跑 sha256 | `TEST.md` §7 | 5/6 逐字节一致 |

**这些主张不是设计意图，而是能被第三方复算的数字**；本机实测值见 §7 与
`references/GAIN-PROTOCOL.md` §4。

## 1. 三类可测指标（定义写在协议里，命令可复制）

| 类别 | 指标 | 怎么量 | 量在哪 |
|---|---|---|---|
| 质量（结构性正确性） | 语义标签覆盖率、图例声明覆盖率、溯源属性覆盖率、图层完整度 | `scripts/gain_probe.py --dir <out>` | `references/GAIN-PROTOCOL.md` §2.1–2.3 |
| 契约一致性 | 信封键覆盖、顶层 null 数、`output_contract` 回显、G1–G8 门 | `scripts/check_contract.py` + `--json` 输出 | 同上 §2.4 |
| 效率 | 从材料到 7 件产物的耗时；改一个标签的代价（文件编辑数 / 重跑次数 / 重导出件数） | 计时 + 产物 sha 对比 | 同上 §2.5、§4.2 |

度量器 `scripts/gain_probe.py` 刻意**不 import 本包任何模块**（否则就是"用被测者自己的尺子
量被测者"），只读产物目录；缺项计 0，避免"没产物反而好看"。

## 2. 运行流程（每一步都留下可测产物）

```bash
export SKILL_DIR=/skills/weekly-skill        # 平台容器；本机指向含 SKILL.md 的那一层
python3 "$SKILL_DIR/scripts/main.py" --help  # 自检：路径正确即打印参数帮助
```

| 阶段 | 做什么 | 落下的可测产物 | 相关决策 |
|---|---|---|---|
| CP1 读真实文件 | 读 `case.json`、`task.md`、材料文件；事实逐条记出处 | `change_records` 首条（case/材料/任务长度） | P1、P6 |
| CP2 机制规格 | 结构化材料出草稿；散文/PDF 手工建规格；**raw 规格先过 schema 门** | `model.json`（实体/边/来源/图例） | P2 |
| CP3 人工核验 | 逐条对照材料；`verified_by_agent=true`；记改动 | `change_records`、核对清单 | P7 |
| CP4 布局 + 渲染 + 双审计 | 确定性布局 → 分层 SVG → PNG/PDF → 拓扑审计 + 图例/编码审计 | `diagram.svg`（7 层 + `data-*`）、`topology.json`、`legend_audit.json` | P3、P4、P8 |
| CP5 契约与终态 | 写 `result.json`，判定 `status`/退出码/门的自洽 | `result.json`（信封 19 键 + 契约回显） | P5、P9 |

主命令（已核验规格路径）：

```bash
python3 "$SKILL_DIR/scripts/main.py" \
    --case "$SKILL_DIR/examples/case.json" \
    --model-file "$SKILL_DIR/examples/model.example.json" --out /app/output
```

散文/PDF 材料走手工规格（`extraction.method=manual`）：

```bash
python3 "$SKILL_DIR/scripts/main.py" --model-file /app/work/model.json \
    --case /input/case.json --out /app/output
```

**退出码即测量口径**：`0 = success（gates 8/8）`、`2 = partial（有降级但有产物）`、
`3 = failed（阻断）`。三者与 `status`、`gates` 必须自洽（规则 P9）。

## 3. 影响可测指标的决策点（P1–P10）

只列**会改变上面任何一项度量**的决策；纯粹的执行细节不在这里重复。

| # | 触发信号 | 动作 | 失败时降级 |
|---|---|---|---|
| P1 | 材料路径解析不到（case 相对路径失败） | 用 `--materials-dir <目录>` 显式给材料目录（多目录可重复给） | 仍无材料 → `failed`（exit 3），`uncertainty` 给补救路径 |
| P2 | 草稿规格里出现枚举外的 `type`/`edge.type` | **阻断渲染**：按 schema 违规清单改正后重跑（raw 规格校验，不会被静默改写成 other） | 改不动 → `failed`，把违规项原文写进 `reason` |
| P3 | 图面用了某类型但图例没列 | 阻断：补图例项 → 重跑（这条直接决定 G4） | 类型名拼错 → 先修 `type` 再重跑 |
| P4 | 画布颜色不在图例 ∪ 映射内 | 阻断：改回图例色或扩图例 | 无法归属 → 改类型默认色 + 记 `uncertainty` |
| P5 | 契约字段无值 | 先判形态再填空：标量 `""` / 列表 `[]` / 布尔 `false` / 数值·字典 `0`·`{}`；**顶层禁 null** | 形态判不定 → 按列表给 `[]` 并说明理由 |
| P6 | 材料没写上下游方向 | 只画结合类无向语义边（`uncertain=true`），不臆造方向 | 连结合依据都没有 → 不画该边，写 `uncertainty` |
| P7 | 自动草稿未被人工核验 | `status=partial`（exit 2）+ `uncertainty` 提示逐条复核；**不得**报 success | 无法核验（材料不可读）→ `failed` |
| P8 | matplotlib / 中文字体缺失 | 只交付 SVG：`partial` + exit 2 + `gates.g5_png=false`，`previews/exports=[]`，原因入 `export_checks` | **绝不**伪造预览；SVG 不得因此缺层或缺 `data-*` |
| P9 | `status` / 退出码 / `gates` 不一致 | 以退出码为真重算，取更保守档，写 `uncertainty` | 修不好就停在保守档，不谎报 success |
| P10 | `--formats` 只请求了部分格式 | 未请求的格式不算失败：`partial` + 空数组 + 说明；已请求的格式必须真产出 | 请求了但产出失败 → 按 P8 降级并记录 |

## 4. 契约与硬性门（可测判定）

- 唯一评分产物是 `result.json`：信封 19 键（`case_id/title/status/contract_version/skill/
  deliverables/scientific_content/evidence_sources/data_mapping/extraction/export_checks/
  topology/legend_audit/self_check/gates/uncertainty/change_records/files/provenance`）
  ＋ `case.json` 里 `output_contract` 声明的全部字段（按四形态回显，**无 null**）。
- 硬性门 G1–G8：`case_id` 非空、契约回显、`status` 三值、SVG 7 层良构、PNG 可开、
  图例覆盖在用类型、实体/边带 `source`、两个审计产物存在。任一门 error → 不得 `success`。
- 字段定义与判定细则见 `references/OUTPUT_CONTRACT.md`；机器入口：
  ```bash
  python3 "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json --case <case.json>
  python3 "$SKILL_DIR/scripts/validate_figure.py" --out <out>
  ```

## 5. 语义与编码速查（机器判定的对象）

| 实体类型 | 图形 | 书写 | 边类型 | 端点 | 颜色 |
|---|---|---|---|---|---|
| gene | 直角矩形 | *斜体*大写 | activation | 实心三角 | 绿 |
| protein | 圆角矩形 | 正体 | inhibition | 横杠 | 红 |
| complex | 圆角矩形+内描边 | 成分间 "–" | binding | 无端点 | 蓝 |
| rna | 圆角矩形（虚线边） | 正体 | modification | 圆点（可带 P） | 橙 |
| small_molecule | 圆形 | 正体 | transport | 菱形 | 紫 |

- 证据强度 → 线宽（strong 2.8 / moderate 2.2 / weak 1.6）；**虚线只表示弱证据或不确定**。
- 数据编码：有数值时按映射画色带并标"低/高"；无值用类型默认色并在图例注明。
- 这些不是画法偏好，而是**审计器读取的字段**（`data-type` / `data-evidence` / 图例声明），
  G3、G4 两项指标直接由它们决定。

## 6. 降级与失败（每条都改变某个度量，必须留痕）

| 情形 | 终态 | 度量上的表现 | 记录位点 |
|---|---|---|---|
| 草稿未核验 | `partial` / exit 2 | 契约与结构指标可满，但 `extraction.verified_by_agent=false` | `uncertainty`、`extraction` |
| 只交付 SVG | `partial` / exit 2 | G7 降为 1/2，`gates.g5_png=false` | `deliverables`、`export_checks` |
| schema 门不过 | `failed` / exit 3 | 只写最小信封（实测 14 键、信封 13/19） | `status`、`reason` |
| 材料不可解析 | `failed` / exit 3 | 无产物，`reason=manual-required` | `reason`、`uncertainty` |
| 审计发现 fail | `partial` 或 `failed` | G4/G5 掉分，`self_check.failures` 非空 | `self_check`、对应审计产物 |

完整分支（F01–F22，含资产缺失、字体缺失、导出失败、元素过多）见 `references/failure-modes.md`。

## 7. 本机对照实测摘要（2026-11-22，全部真跑）

**条件 A** = `scripts/baseline_emulator.py`（把题面点名的基础 Agent 失败签名做成确定性复现器：
名词平铺成环、统一灰箭头、无图例、无溯源、无契约、单一扁平层）；
**条件 B** = 本 Skill 的主路径。两侧读**同一份材料**、用**同一个度量器**。

| 指标 | 条件 A（基础形态） | 条件 B（加载 Skill） | 差 |
|---|---|---|---|
| 产物文件数 | 2（`figure.svg` + `notes.md`） | 7（SVG/PNG/PDF/result/model/topology/legend_audit） | +5 |
| 具名图层组 | 0 | 7 | +7 |
| 边的**语义标签**数 | 0 | 5（5 类语义全在用） | +5 |
| 图例声明的边 / 总边数 | 0 / 10 | 9 / 9 | — |
| 带 `data-source` 的元素 | 0 | 18 | +18 |
| 契约信封键覆盖 | 0/19（无 `result.json`） | 19/19 | +19 |
| `check_contract.py` | exit 1（`missing result.json`） | exit 0（7 项全 pass） | — |
| `validate_figure.py` | exit 1（`ok=False`） | exit 0（30 项、fails=0） | — |
| 材料实体名覆盖率 | 1.0000 | 1.0000 | **0（不是差异点）** |

**效率侧（同一天实测）**：条件 B 全新一次运行 2.51 s 产出 7 件；
**改一个标签** = 1 次文件编辑 + 1 次重跑（1.76 s），SVG/PNG/PDF 全部重新生成、标签出现在 SVG 里；
条件 A 的产物**没有元素 id 也没有 `data-*`**（`data-id` 计数 = 0），标签只能靠文本搜索定位，
且没有导出流水线——"改规格再重导出"这条路径在基础形态里不存在。

复算命令（任何人都能跑）：

```bash
python3 "$SKILL_DIR/scripts/baseline_emulator.py" --material <材料> --out /tmp/condA
python3 "$SKILL_DIR/scripts/main.py" --case <case.json> --model-file <model.json> --out /tmp/condB
python3 "$SKILL_DIR/scripts/gain_probe.py" --compare /tmp/condA /tmp/condB --material <材料>
```

完整协议、指标定义与逐条记录见 **`references/GAIN-PROTOCOL.md`**。

## 8. 反预制答案规则

`examples/` 全部是**演示示例（非正式案例）**；正式运行禁止抄示例的实体/边/数值。
`scripts/baseline_emulator.py` 是**对照用的反例生成器**：它的产物是刻意的坏例子，
**不得**作为正式案例输出、不得冒充平台对照结果。本包不写、也不预测任何平台评分。

## 9. 边界与诚实声明

- 度量器量的是**结构性与可核验性**（分层、溯源、语义标签、图例声明、契约、导出），
  **不评判图面美观**；美观度由人/模型评审判定。
- 条件 A 是**结构复现器**，不是平台基础 Agent 的真实运行；真实对照由平台执行（同输入、同预算、
  每条件 3 次重复）。本包只保证"判据可复算"。
- 确定性承诺 = SVG / PNG / model / topology / legend_audit；PDF 与 `result.json` 含时间戳。
- 图件不在包内（运行时生成）；PDF 与 `result.json` 含时间戳，不作确定性承诺。

## 10. 文件索引（相对 `$SKILL_DIR`）

| 文件 | 作用 |
|---|---|
| `references/GAIN-PROTOCOL.md` | **本版核心新增**：公平对照协议、8 项指标定义、复算命令、实测记录、局限 |
| `references/OUTPUT_CONTRACT.md` | 字段契约 + 四形态 + G1–G8 + §10 契约合规的可测判定 |
| `references/failure-modes.md` | F01–F22 失败分支（每条注明它在哪个度量上留痕） |
| `references/RUBRIC_MAP.md` | 五维评分落点（使用增益 25 分按指标逐条落点） |
| `references/mechanism-spec.md` / `legend-encoding.md` | 规格与绘图规范、箭头语义与数据编码 |
| `scripts/gain_probe.py` | 独立度量器（不依赖本包模块；`--dir` / `--compare`） |
| `scripts/baseline_emulator.py` | 条件 A 结构复现器（反例生成器，仅供对照） |
| `scripts/main.py` | 单一入口（CP1–CP5，退出码 0/2/3） |
| `assets/` `templates/` `examples/` | schema/调色板/结果模板、核对清单、最小可运行示例 |
| `README.md` / `TEST.md` / `worklog.md` | 依赖与用法 / 自测与实测记录 / 构建记录（`COMPARE.md` 已并入 GAIN-PROTOCOL） |
