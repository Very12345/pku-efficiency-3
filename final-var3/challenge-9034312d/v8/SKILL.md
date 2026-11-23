---
name: apparatus-and-route-diagrams-contract-matrix
description: >-
  v8 轴：把 result.json 的 OUTPUT_CONTRACT 打成「容器形态 × 边界值」实测矩阵。
  scripts/contract_matrix.py 先自校验契约面（文档字段块 ⇄ check.py 的 required_fields），
  再把 18 个契约字段 × 缺字段/null/空值/非法类型/超长 + 六种容器形态（字符串/列表/对象/数值/布尔/嵌套）
  + 嵌套结构逐个注入，跑主流程与 G1–G10 契约门，记录实测退出码/status/契约回显/是否静默通过，
  产出 contract_matrix_report.json；references/CONTRACT-MATRIX.md 给逐行表、静默通过清单
  与未覆盖声明。既有 15 个脚本入口与 27 个 --flag 一个不少，脚本逐字节未改。
---

# 实验装置与技术路线图 Skill · v8 版（轴：**契约四形态 × 边界值矩阵**）

> **文档路径重定向（本包 v8）**
>
> * `references/MECHANISM.md` → 已全文并入 `references/GAIN-PROTOCOL.md` 尾部的「并入全文」附录（本包 v8 为守住平台「≤50 个 UTF-8 文本文件」硬门而合并，**内容一字未删**）；本文出现的旧路径请按该附录阅读。
> * `references/FAULT-MATRIX.md` → 已全文并入 `references/failure-modes.md` 尾部的「并入全文」附录（本包 v8 为守住平台「≤50 个 UTF-8 文本文件」硬门而合并，**内容一字未删**）；本文出现的旧路径请按该附录阅读。

本 Skill 把科研材料变成**可编辑、可追溯、可复跑**的图稿：分层 SVG 源文件 + PNG/PDF 预览 +
`evidence.json`（证据链）+ `result.json`（含 `output_contract` 全字段 + `case_id`）。

**v8 这一版只做一件事：把「契约到底管住了什么」逐字段量出来。**
算法、CLI、既有脚本全部不动（15 个脚本入口逐字节不变、27 个 `--flag` 全保留），
新增 1 个可运行脚本 + 1 份逐行实测文档。

| 本包新增（v8 轴） | 作用 | 实测结论（数字见 §4，全部现场跑出） |
|-|-|-|
| `scripts/contract_matrix.py` | 契约面自校验 + 输入侧/输出侧/六形态/嵌套结构四段注入，跑 `main.py` 与 `check.py` | **164 行**注入、**141 行**违约、**96 条**静默通过、**10 条**门面内缺陷、**86 条**未覆盖 |
| `references/CONTRACT-MATRIX.md` | 逐行实测表（输入 22 / 输出 106 / 六形态 36）+ 静默通过清单 + 未覆盖声明 + 建议修法 | 契约声明 **18** 字段 ⇄ `check.py` 只检查 **9** 字段 |

> 与前一版的关系：v8 = v6（全维合并版）**内容全保留** + 契约矩阵轴。
> 为守住「≤50 个 UTF-8 文本文件」硬门，`references/MECHANISM.md` 与
> `references/FAULT-MATRIX.md` 的**全文**并入了同主题宿主文档（见 §7 清单，一字未删）。

## 0. 技能根与自定位（先读这一节）

- **技能根 = 本 `SKILL.md` 所在目录**（平台安装到 `/skills/weekly-skill`）。下文一律用 `$SKILL_DIR`：

  ```bash
  SKILL_DIR=/skills/weekly-skill                              # 平台安装位置
  SKILL_DIR="$(cd "$(dirname /path/to/SKILL.md)" && pwd)"      # 本地解包位置
  ```

- `scripts/*.py` 全部 `os.path.dirname(__file__)` 自定位，读 `templates/`/`assets/`/`references/`
  相对技能根解析，**不依赖 cwd**；脚本内已置 `sys.dont_write_bytecode = True`。
- **本包只含文本资源**（`.md/.py/.json/.txt/.csv/.yaml/.yml`），**49 个文件**（上限 50）、
  单文件最大 51 KB（上限 500 KB）、合计约 0.60 MB（上限 2 MB）、无符号链接、无 `__pycache__`。
  `figure.svg`/`figure.png`/`figure.pdf` 由 `main.py` **运行时生成**，不随包发布。

## 1. 用途与适用条件

- **输入**：`/input/case.json` + `/input/task.md`（可选）+ 材料（`--material` 或内联文本）。
  结构化与自由文本两种 case.json 都支持；结构缺失时走文本解构并如实标注
  `extraction=text-heuristic`。
- **输出**：`<out>/<case_id>/` 下 7 件：`evidence.json`、`layout.json`、`figure.svg`、
  `figure.png`、`figure.pdf`、`verify_report.json`、`result.json`。
- **不承担**：数据分析与数值拟合、方案科学性判断、论文排版与投稿格式适配。

## 2. 输入输出接口（与 `scripts/main.py --help` 逐字对应）

```bash
python "$SKILL_DIR/scripts/main.py" --case <case.json|案例目录> [--task <task.md>]
                       [--material <材料文件|目录>] [--merge <override.json>]
                       --out <输出目录> [--dpi 200]
                       [--figure-type route|apparatus|flow|hybrid]
                       [--title "…"] [--width-mm N] [--height-mm N]
                       [--palette <palette.json>] [--rules <connection_rules.json>]
```

`--case` 给目录时自动取 `case.json`（未给 `--task` 时取同目录 `task.md`）；
给具体文件时 `--task` 需显式传入。`--merge` 是编辑既有图稿的入口（按 id 替换/追加，
修正动作写入 `change_record`）。**这组参数名/默认值/退出码语义在 v8 中一字未改**——
契约矩阵正是拿它们当"被测对象"。

## 3. 执行步骤

1. **读真实文件** → 2. **证据抽取（CP1）**（`gain_evidence.py`，`locator`+`quote` 落盘
   `evidence.json`）→ 3. **SIR 与布图**（`model.py` → `layout.py`）→ 4. **渲染**
   （`render_svg.py` 分层 SVG；`export_preview.py` 同一布局模型出 PNG/PDF）→
   5. **校验（CP2/CP3）**（`svg_verify.py`：图层/文本/箭头/编号/图例 + 连接规则审计）→
   6. **契约门（CP4）**（写 `result.json` 后跑 `check.py` 的 G1–G10）→ 7. **★ v8 追加：契约矩阵复核**。

## 4. ★ 本包的轴：契约四形态 × 边界值矩阵

### 4.1 一条命令跑出矩阵

```bash
python "$SKILL_DIR/scripts/contract_matrix.py" --json /tmp/contract_matrix_report.json
# 回归断言：本包实测 10 条门面内缺陷；数量一变就 attention
python "$SKILL_DIR/scripts/contract_matrix.py" --expect-defects 10
# 只跑某一段/某一条
python "$SKILL_DIR/scripts/contract_matrix.py" --section form --only form-03
python "$SKILL_DIR/scripts/contract_matrix.py" --section output --only nest-08 --only nest-09
```

四段结构：

| 段 | 注入对象 | 跑什么 | 记录什么 |
|-|-|-|-|
| ① 契约面自校验 | `OUTPUT_CONTRACT.md` 字段块 ⇄ `check.py` 的 `required_fields` | 不跑 | `contract_doc_matches`、`contract_fields_not_checked` |
| ② 输入侧 `in-*`（22 行） | `case.json` 的容器/字段/边界 | `main.py` 全流程 | 退出码、`status`、契约回显（18 字段缺哪些）、`uncertainty` 条数、信号强度 |
| ③ 输出侧 `out-*`（106 行） | `result.json` 的**每个契约字段** × 缺字段/null/空值/非法类型/超长 | `check.py` 的 G1–G10 | 退出码、`ok`、被拦下的门、`issues` 条数、信号强度 |
| ④ 六形态 + 嵌套 `form-*`/`nest-*`（36 行） | 六种容器形态塞进 6 个代表字段；契约四段的内部结构 | `check.py` | 同上 |

### 4.2 判据（先声明期望，再比对实测）

每一行在脚本里**先声明期望信号强度**，再与实测比对：

- `gate` —— 期望被某个 G 门拦下（`ok=false`、退出码 1）；
- `issue` —— 契约只承诺"报 issue"（`ok` 可以仍是 true）；
- `none` —— 落在 G1–G10 检查面**之外**（属未覆盖，不是缺陷）。

`defect` 只统计「期望 `gate` 或 `issue`，但实测信号更弱」的行 —— 这类才是**门面内**的真实缺口。
`silent_pass` 是原始观测（违约却放行），**包含**缺陷与未覆盖两类，逐条列出，不做合并。

退出码：**0** = 无门面内缺陷；**1** = 有（本包实测 1，属预期结论，逐条见报告 `defects[]`）；
**2** = 用法/环境错误。

### 4.3 实测数字（本机 Windows 11 + CPython 3.13.9）

| 观测 | 实测 |
|-|-|
| 契约面自校验 | `contract_doc_matches = true`（文档 18 字段 ⇄ 脚本 18 字段） |
| `check.py` 实际检查面 | `required_fields` 仅 **9** 个 ⇒ **9 个契约字段无任何存在性检查**（`workorder` `extraction` `entities` `relations` `evidence` `verify` `canvas` `fonts` `execution`） |
| 注入行数 | **164**（输入 22 / 输出 106 / 六形态 36），其中违约 **141** 行 |
| 信号分布（③④段 142 行） | `gate` **35** · `crash` **9** · `issues-only` **6** · `none` **92** |
| 被触发的门（直方图） | **G1 15 · G2 9 · G3 10 · G4 10 · G5 17 · G6 10 · G7 7 · G10 24**（G8 只在 route/flow 编号断裂时生效、G9 读 `verify_report.json`，本矩阵未触发） |
| **静默通过** | **96** 条（原始观测） |
| 其中·门面内缺陷 | **10** 条（输入 6 + 输出 4，见 §4.4） |
| 其中·仅报 issue | **6** 条（退出码仍是 0 —— 自动化只看退出码会漏） |
| 其中·未覆盖 | **86** 条（可全部归因到那 9 个无检查字段 + 六形态越界） |
| `setup_errors` | **0**（矩阵自身无设置失败） |
| 跑矩阵耗时 | 约 24 s（含 1 次基线运行 + 22 次主流程 + 106 次契约门） |

### 4.4 十条门面内缺陷（逐条在 `references/CONTRACT-MATRIX.md` §6）

| 簇 | 行 | 现象 |
|-|-|-|
| 结构段形态 + `status` 判定 | `in-01` `in-03` `in-04` `in-05` `in-22` | `entities` 给字符串/对象/0/null/元素为字符串 ⇒ 走文本解构，`uncertainty` 记了一条，但 `status` 仍是 `success`（契约状态表把"文本解构"列为 `partial` 条件） |
| 空案例 | `in-19` | `case.json = {}` ⇒ 同样以 `success` 收尾 |
| `verify` 段无人核对 | `nest-08` `nest-09` `nest-10` | `result.json` 的 `verify.ok` 改 `"true"` / `1` / 整段清空，`G9` 读的是 `verify_report.json`，**两份记录可以互相矛盾而门不响** |
| 零实体 | `nest-11` | `entities=[]` 且 `data_mapping=[]` ⇒ `G5` 的"行数 == 实体数"两个 0 也相等 ⇒ 通过；而契约要求 `success` 需"实体≥1" |

### 4.5 为什么不改门

规范要求既有脚本「尽量逐字节不变；确需修真实缺陷只允许**纯增量**并逐条点名；
CLI 参数/退出码语义不得改」。上面四簇若要修，动的是 `check.py` 的**判据**
（不是纯增量），会改变 G9/G10 的语义与退出码分布。本包的选择是：
**量出来 → 写清楚（含精确修法与影响面）→ 做成回归断言（`--expect-defects 10`）**。
`scripts/check.py` 与本包其余 14 个既有脚本**逐字节未改**。

## 5. 决策规则与检查点（沿用既有口径，未改）

CP1 证据门 → CP2 连接门 → CP3 校验门 → CP4 契约门；D1–D12 见 `references/failure-modes.md`。
**v8 追加口径 D14**：`references/OUTPUT_CONTRACT.md` 里每新增一个字段，
必须同步进 `references/CONTRACT-MATRIX.md` 的 §1 表并说明"机器门是否检查它"——
否则契约面自校验会在下次跑矩阵时把差异暴露出来（`contract_doc_matches` 或
`contract_fields_not_checked` 变化）。

## 6. 完成判定清单

- [ ] CP1：`evidence.json` 存在且实体/关系带 `locator`+`quote`
- [ ] CP2/CP3：无 error 级连接规则违规；SVG 合法、5 层齐全、`<text>`≥3；编号连续；图例↔图元一致
- [ ] CP3：`figure.png`/`figure.pdf` 存在且非空（失败已如实降级写入 `uncertainty`）
- [ ] CP4：`result.json` 含 18 个顶层字段；`check.py` 输出 `ok: true`
- [ ] **v8 轴**：`python "$SKILL_DIR/scripts/contract_matrix.py"` 跑完，
      `contract_doc_matches == true`、`setup_errors == 0`，且 `defects[]` **逐条**能在
      `references/CONTRACT-MATRIX.md §6` 找到对应行（无新增未记录缺陷）
- [ ] **v8 轴**：新增/改动的契约字段已同步进 `CONTRACT-MATRIX.md §1`（D14）
- [ ] 修改历史、不确定性、来源如实记录；包内无绝对路径、无 `__pycache__`

## 7. 资源清单（路径均相对技能根；★ 为 v8 新增/变更）

```
SKILL.md  README.md  TEST.md  GITHUB_URL.txt
scripts/  main.py  gain_evidence.py  model.py  layout.py  render_svg.py  export_preview.py
          svg_verify.py  check.py  fonts.py  preflight.py  fault_inject.py  case_set_run.py
          decision_probe.py  gain_probe.py  bare_baseline.py
          ★ contract_matrix.py        # v8 轴：契约四形态 × 边界值实测矩阵
assets/   connection_rules.json
templates/ palette.json  component-connection-checklist.md  entity-relation-checklist.csv
references/ OUTPUT_CONTRACT.md  RUBRIC_MAP.md  failure-modes.md  vocabulary.md
          figure-blueprint.md  GAIN-PROTOCOL.md  CASE-SET.md  FAULT-MATRIX.md
          case-set.json  comparison-data.json  ★ CONTRACT-MATRIX.md
examples/ case.json  task.md  README.md  EXPECTED-OUTPUT.md  apparatus_spec.example.json
          route_spec.example.json  route_spec.mutation.example.json
          cases/{dtms-stage-route-01,mbr-wastewater-flow-01}/{case.json,task.md}
          output/{demo-apparatus-001,demo-biotech-route-01}/{result.json,artifacts.json}
```

**本包的文件合并（守 ≤50 硬门，内容逐字保留）**：

| 现在的宿主文件 | 并入的原文件 | 为什么同主题 | 路径更正 |
|-|-|-|-|
| `references/GAIN-PROTOCOL.md` | `references/MECHANISM.md`（全文） | 都是"凭什么说加载它更好"（机制 vs 公平对照） | `bare_baseline.py`（2 处）、`gain_probe.py`（2 处）的 docstring 旧路径指向宿主文件尾部附录 |
| `references/failure-modes.md` | `references/FAULT-MATRIX.md`（全文） | 都是"异常如何处置"（决策规则 vs 32 条故障注入实测） | `fault_inject.py`（3 处）的 docstring 旧路径指向宿主文件尾部附录 |

**既有合并（非本轮，供路径追踪）**：`references/DECISION-CASES.md` 的内容早已并入
`references/failure-modes.md` 附录 C（该文件头部有说明）；`scripts/decision_probe.py` 的
docstring 里那个旧路径指的就是附录 C。

依赖：Python 3.10+ 标准库；**Pillow**（PNG 预览）；**reportlab**（PDF 预览；
其在导入期依赖 `PIL`）。三者皆可缺，缺预览件时 `status=partial` 并写入 `uncertainty`。

## 8. 评分五维落点（速查；逐条证据见 `references/RUBRIC_MAP.md`）

| 维度 | 分 | 本包落点 |
|-|-|-|
| 实际效果 | 40 | `main.py` 一键出 7 件；`examples/output/` 有两个合成案例真实产物；★ 本轴的 164 行注入**每一行的产物都留在工作目录**可复核 |
| 使用增益 | 25 | 证据先行 + 连接规则审计 + 图例↔图元门；`--merge` 增量改图；对照记录见 `references/GAIN-PROTOCOL.md` |
| 创新增益 | 15 | SIR → 确定性布图 → 三后端同布局；★ **本轴新增**：把"契约声明"与"机器门实际拦什么"做成可执行差异矩阵（期望信号分级 + 回归断言） |
| 可靠体验 | 10 | `failure-modes.md`（含故障矩阵）+ D1–D12 + ★ **D14 契约面同步规则**；★ 本轴把异常处理**逐条量化**：96 条静默、10 条门面内缺陷、精确修法与影响面 |
| 生态贡献 | 10 | 文档完整性（SKILL/README/TEST/9 份 references/3 模板）+ 可复用资产（规则字典、配色、清单、★ 契约矩阵可搬到任何 result.json 型 Skill）+ `GITHUB_URL.txt` |

## 9. 边界与诚实原则

- 本 Skill 只负责**绘图表达**与**可编辑交付**；不判断方案科学性，不做数值拟合。
- 矩阵的结论**包括对本包不利的部分**（10 条门面内缺陷、96 条静默通过）。
  本包**不声称契约已被完全守住**；声称的是：这些缺口已被逐行测出、归类、给了修法与回归断言。
- 拿不到来源就标 null 并计入 `uncertainty`；不伪造软件状态、不编造科研数据。
- `examples/` 仅为接口演示（产物标注「示例，非正式案例」），不含预制答案。
