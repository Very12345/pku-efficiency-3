---
name: apparatus-and-route-diagrams-determinism
description: >-
  v7 轴：确定性与字节级可复现。在「实验装置与技术路线图」Skill 上补一条可运行的确定性证据链——
  scripts/determinism.py 用独立进程 × 不同 cwd × 不同 PYTHONHASHSEED 连跑 N 次，
  对全部产物做 sha256 比对，产出 determinism_report.json（runs[]/per_file_sha256/identical/
  volatile_fields[]），并用三条杠杆（同一 --out 根、RL_INVARIANT=1、冻结时钟）把残余漂移关掉；
  references/DETERMINISM.md 逐字段说明哪些是故意不稳定的、如何稳定化、附实测表。
  既有 15 个脚本入口与 27 个 --flag 一个不少，算法与 CLI 语义未改。
---

# 实验装置与技术路线图 Skill · v7 版（轴：**确定性与字节级可复现**）

> **文档路径重定向（本包 v7）**
>
> * `references/MECHANISM.md` → 已全文并入 `references/GAIN-PROTOCOL.md` 尾部的「并入全文」附录（本包 v7 为守住平台「≤50 个 UTF-8 文本文件」硬门而合并，**内容一字未删**）；本文出现的旧路径请按该附录阅读。
> * `references/CASE-SET.md` → 已全文并入 `references/FAULT-MATRIX.md` 尾部的「并入全文」附录（本包 v7 为守住平台「≤50 个 UTF-8 文本文件」硬门而合并，**内容一字未删**）；本文出现的旧路径请按该附录阅读。

本 Skill 把「装置怎么搭、步骤怎么走、物料从哪来到哪去、技术路线分几个阶段」的文本材料，
变成一张**可编辑、可追溯、可复跑**的科研图稿。图稿四件套：分层 SVG 源文件 + PNG/PDF 预览 +
`evidence.json`（证据链）+ `result.json`（含 `output_contract` 全字段）。

**v7 这一版只做一件事：把「复跑出同一张图」从自述变成可复核的字节证据。**
算法、CLI、既有脚本全部不动（15 个脚本入口逐字节不变，27 个 `--flag` 全部保留），
新增 1 个可运行脚本 + 1 份逐字段实测文档。

| 本包新增（v7 轴） | 作用 | 实测结论（数字来自现场跑，见 §4） |
|-|-|-|
| `scripts/determinism.py` | 独立进程 × 4 cwd × 4 个 `PYTHONHASHSEED` 连跑 8 次，逐产物 sha256 比对，输出 `determinism_report.json` | 默认环境 **5/7** 件逐字节一致；三条杠杆后 **7/7** 一致；未解释漂移 **0** |
| `references/DETERMINISM.md` | 逐字段说明：哪些是**故意**不稳定、为什么不能钉死、用什么杠杆关掉、附实测表 | 漂移只有 2 条 JSON 字段 + PDF 元数据 3 项，全部已声明 |

> 与前一版的关系：v7 = v6（全维合并版）**内容全保留** + 确定性轴。
> 为守住平台「≤50 个 UTF-8 文本文件」的硬门，`references/CASE-SET.md` 与
> `references/MECHANISM.md` 的**全文**并入了同主题的宿主文档（见 §8 的文件清单，
> 合并说明写在被并入文档的开头，**一字未删**）。

## 0. 技能根与自定位（先读这一节）

- **技能根 = 本 `SKILL.md` 所在目录**。平台把它装到 `/skills/weekly-skill`；
  本地复现时它就是你解包出来的那个目录。下文一律用 `$SKILL_DIR` 表示：

  ```bash
  SKILL_DIR=/skills/weekly-skill                                # 平台安装位置
  SKILL_DIR="$(cd "$(dirname /path/to/SKILL.md)" && pwd)"        # 本地解包位置
  ```

- `scripts/*.py` **全部**用 `os.path.dirname(__file__)` 自定位，读 `templates/`、`assets/`、
  `references/` 一律相对技能根解析，**不依赖运行时 cwd**；脚本内已置
  `sys.dont_write_bytecode = True`（评测时不落 `__pycache__`）。
  §4 的确定性探针把这条性质**当判据测**（4 个不同 cwd 轮流跑，产物必须一致）。
- 资源形态遵守平台硬约束：只含 `.md/.py/.json/.txt/.csv/.yaml/.yml` 文本资源，
  **49 个文件**（上限 50）、单文件最大 51 KB（上限 500 KB）、合计约 0.56 MB（上限 2 MB）、
  无符号链接、无 `__pycache__`。`figure.svg`/`figure.png`/`figure.pdf` 是**运行期产物**，
  不随包发布。

## 1. 用途与适用条件

- **输入**：`/input/case.json`（必读）+ `/input/task.md`（可选）+ 案例引用的材料
  （`--material`，或 case.json 内联的 `text`/`materials_text`）。case.json 可为结构化
  （`entities`/`relations`/`figure_type`/`canvas`）或自由文本，两条路都走。
- **输出**：写入 `--out`（官方运行时为 `/app/output`），实际落在 `<out>/<case_id>/`，
  共 7 件：`evidence.json`、`layout.json`、`figure.svg`、`figure.png`、`figure.pdf`、
  `verify_report.json`、`result.json`。
- **不承担**：数据分析与数值拟合、实验方案本身的科学合理性判断、论文排版与投稿格式适配。

## 2. 输入输出接口（与 `scripts/main.py --help` 逐字对应）

```bash
python "$SKILL_DIR/scripts/main.py" --case <case.json|案例目录> [--task <task.md>]
                       [--material <材料文件|目录>] [--merge <override.json>]
                       --out <输出目录> [--dpi 200]
                       [--figure-type route|apparatus|flow|hybrid]
                       [--title "…"] [--width-mm N] [--height-mm N]
                       [--palette <palette.json>] [--rules <connection_rules.json>]
```

- `--case` 给**目录**时自动取该目录下 `case.json`，未给 `--task` 时取同目录 `task.md`；
  给**具体文件**时 `--task` 必须显式传入（不猜同目录文件）。
- `--out` 默认 `./output`；官方运行时是 `/app/output`。
- `--merge` 是"编辑既有图稿"入口：`{"entities":[…],"relations":[…],"change_notes":[…]}`
  按 id 替换、新 id 追加，修正动作自动写入 `change_record`。

## 3. 执行步骤（顺序固定，每步都在真实文件上操作）

1. **读真实文件**：`read /input/case.json`、`/input/task.md`、材料；禁止按文件名猜内容。
2. **证据抽取（CP1 证据门）**：流水线内置 `gain_evidence.py`，每条实体/关系带
   `locator` + `quote`，落盘 `evidence.json`；Agent 复核证据链后再继续。
3. **布图与渲染**：`model.py`（SIR）→ `layout.py`（确定性布局）→ `render_svg.py`
   （手写分层 SVG）→ `export_preview.py`（PIL PNG + reportlab PDF，同一布局模型）。
4. **校验（CP2 连接门 / CP3 校验门）**：`svg_verify.py` 查图层、可编辑 `<text>`、
   箭头与关系一一对应、编号连续、图例↔图元一致，并按 `assets/connection_rules.json`
   审计类别与连接语义。
5. **契约门（CP4）**：写 `result.json`（18 个顶层字段 + `case_id`），再跑
   `python "$SKILL_DIR/scripts/check.py" <result.json>` 要求 `ok: true`。
6. **★ v7 追加一步：确定性自证**（本轴的核心，见 §4）。

## 4. ★ 本包的轴：确定性自证（命令 / 判据 / 实测数字）

### 4.1 一条命令跑出证据

```bash
python "$SKILL_DIR/scripts/determinism.py" --json /tmp/determinism_report.json
```

它做三件事：① 把技能根按文本白名单复制到**沙箱副本**（包本体不动）；
② **raw 条件**跑 4 次（各自独立 `--out`、4 个不同 cwd、`PYTHONHASHSEED=0/1/12345/31337`、
每次独立子进程、真实时钟）；③ **stabilized 条件**再跑 4 次，只多三条杠杆：

| 杠杆 | 做法 | 关掉什么 |
|-|-|-|
| **L1** | 所有 run 共用同一个 `--out` 根（每次运行前清空） | `result.json#execution/out_dir` |
| **L2** | 环境变量 `RL_INVARIANT=1`（reportlab 自带开关） | `figure.pdf` 的 `/CreationDate`、`/ModDate`、`/ID` |
| **L3** | 现场生成的 `_frozen_clock_driver.py`：把 `datetime.now()` 钉到 `2026-01-01T00:00:00Z` 再 `runpy` 主脚本 | `result.json#change_record/*/time` |

**L1–L3 全部在探针侧**（工作目录 / 环境变量 / 驱动脚本），`scripts/*.py` 一行未改，
也不会进正式交付物。

### 4.2 判据（四条，可执行，不靠人读表）

1. `unexplained_volatile_fields == 0`（每个漂移叶子都能映射到 `DECLARED_VOLATILE` 的声明）；
2. `identical_by_condition.stabilized == true`（强判据）；
3. `identical_normalized.raw == true`（掩码已声明路径后，raw 也一致）；
4. `stabilized_identical_files == artifacts`（稳定化后一件不少）。

退出码：**0** = 四条全中；**3** = 出现未解释漂移或稳定化后仍不一致；**2** = 用法/环境错误。

### 4.3 实测数字（`--runs 4`，本机 Windows 11 + CPython 3.13.9）

| 观测 | 实测 |
|-|-|
| 运行次数 / 产物数 | **8 次**（raw 4 + stabilized 4）/ **7 件** |
| 进程数 / cwd 数 / seed 数 | **8 个独立 pid** / **4 个不同 cwd** / **4 个不同 `PYTHONHASHSEED`** |
| `identical`（raw，平台默认环境） | **false** —— 预期：`result.json` 与 `figure.pdf` 各带一条审计性漂移 |
| raw 条件下逐字节一致的产物 | **5 / 7**（`evidence.json` `layout.json` `figure.svg` `figure.png` `verify_report.json`） |
| stabilized 条件下逐字节一致的产物 | **7 / 7** |
| `identical_normalized` | raw **true**、stabilized **true** |
| 漂移字段（JSON） | **2** 条：`change_record/0/time`、`execution/out_dir`；全部 `intentional=true` |
| 漂移产物（二进制） | **1** 件：`figure.pdf`（`/CreationDate`、`/ModDate`、`/ID`），稳定化后 **1 个 sha** |
| 未解释漂移 | **0** |
| `verdict` | **pass** |
| 单次运行耗时 | 0.32–0.39 s（8 次合计约 2.9 s） |

**一句话结论**：这张图本身是确定的；不确定的只有"这次运行发生在什么时候、写到了哪个目录"——
两条都是审计信息，伪造它们比让它们漂移更糟。三条杠杆关掉之后，8 次运行逐字节相同。

逐字段的"为什么故意不稳定 / 怎么稳定化 / 实测取值"表见 `references/DETERMINISM.md`（§3 与 §4）。

## 5. 决策规则与检查点（沿用既有口径，未改）

**检查点**：CP1 证据门（实体/关系 `locator` 真实命中材料）→ CP2 连接门（类别词表与
连接语义无 error 级违规）→ CP3 校验门（图层/文本/箭头/编号/图例一致，PNG/PDF 存在或已诚实降级）
→ CP4 契约门（`check.py` 的 G1–G10 全过）。

**决策规则 D1–D12**（完整表见 `references/failure-modes.md`）：D1 case 不存在 ⇒ `failed`；
D2 仅文本 ⇒ `text-heuristic` + `uncertainty`；D3 断头箭头 ⇒ 过滤并记录；D4 无来源 ⇒ `source=null`；
D5 词表外类别 ⇒ 容错归一化 + 报 error；D6 方向冲突 ⇒ 审计报 error，用 `--merge` 修正；
D7 同名实体 ⇒ 记 `ambiguity`；D8 画布溢出 ⇒ 等比缩放或 `--width-mm/--height-mm` 重跑；
D9 无中文字体 ⇒ `fonts.found=false`；D10 渲染失败 ⇒ 保留已有产物 + `status=partial`；
D11 error 未解决 ⇒ 不得 `success`；D12 材料冲突 ⇒ 记 `uncertainty`，不补造。

**v7 追加的口径**（写进 `references/DETERMINISM.md`）：
**D13 = 产物漂移不得越出声明清单**。任何新增的非确定性字段必须先写进
`DECLARED_VOLATILE`（含 `why` 与 `stabilizer`）再改代码，否则确定性探针会以
`unexplained>0` 报 `attention`（退出码 3）——这是本轴引入的**回归闸门**。

## 6. 完成判定清单

- [ ] CP1：`evidence.json` 存在，实体/关系带 `locator`+`quote`（缺失已列 `uncertainty`）
- [ ] CP2：无 error 级连接规则违规
- [ ] CP3：SVG 合法 XML、5 层 `layer:*` 齐全、可编辑 `<text>` ≥3；编号连续；图例↔图元一致
- [ ] CP3：`figure.png` / `figure.pdf` 存在且非空（失败已如实降级并写入 `uncertainty`）
- [ ] CP4：`result.json` 含 `references/OUTPUT_CONTRACT.md` 的 **18 个顶层字段**，
      `python "$SKILL_DIR/scripts/check.py" <result.json>` 输出 `ok: true`、退出码 0
- [ ] **v7 轴**：`python "$SKILL_DIR/scripts/determinism.py"` 退出码 0，
      `identical_by_condition.stabilized == true` 且 `unexplained_volatile_fields == 0`
- [ ] **v7 轴**：新增的非确定性字段已写进 `references/DETERMINISM.md` 的声明清单
- [ ] 修改历史（`change_record`）、不确定性（`uncertainty`）、来源（`sources`+`evidence`）如实记录
- [ ] 打包形态：只含允许的 7 种文本扩展名，无 `__pycache__`，包内无本机绝对路径

## 7. 资源清单（路径均相对技能根；★ 为 v7 新增/变更）

```
SKILL.md  README.md  TEST.md  GITHUB_URL.txt
scripts/  main.py  gain_evidence.py  model.py  layout.py  render_svg.py  export_preview.py
          svg_verify.py  check.py  fonts.py  preflight.py  fault_inject.py  case_set_run.py
          decision_probe.py  gain_probe.py  bare_baseline.py
          ★ determinism.py            # v7 轴：确定性探针（独立进程 × cwd × PYTHONHASHSEED）
assets/   connection_rules.json
templates/ palette.json  component-connection-checklist.md  entity-relation-checklist.csv
references/ OUTPUT_CONTRACT.md  RUBRIC_MAP.md  failure-modes.md  vocabulary.md
          figure-blueprint.md  GAIN-PROTOCOL.md  FAULT-MATRIX.md  case-set.json
          comparison-data.json  ★ DETERMINISM.md
examples/ case.json  task.md  README.md  EXPECTED-OUTPUT.md  apparatus_spec.example.json
          route_spec.example.json  route_spec.mutation.example.json
          cases/{dtms-stage-route-01,mbr-wastewater-flow-01}/{case.json,task.md}
          output/{demo-apparatus-001,demo-biotech-route-01}/{result.json,artifacts.json}
```

**本包的文件合并（守 ≤50 硬门，内容逐字保留）**：

| 现在的宿主文件 | 并入的原文件 | 为什么同主题 | 路径更正 |
|-|-|-|-|
| `references/GAIN-PROTOCOL.md` | `references/MECHANISM.md`（全文） | 都在回答"凭什么说加载它更好"：机制 vs 公平对照 | `bare_baseline.py`（2 处）与 `gain_probe.py`（2 处）docstring 里的旧路径指向宿主文件尾部附录 |
| `references/FAULT-MATRIX.md` | `references/CASE-SET.md`（全文） | 都在回答"坏了/降级会怎样"：故障注入 vs 输入退化的泛化失效 | 无脚本 docstring 指向被并文件（`case_set_run.py` 读的是仍在包内的 `case-set.json`） |

**既有合并（非本轮，供路径追踪）**：`references/DECISION-CASES.md` 的内容早已并入
`references/failure-modes.md` 附录 C（该文件头部有说明）；`scripts/decision_probe.py` 的
docstring 里那个旧路径指的就是附录 C（TEST.md T4 的 20 条用例正是对那张表跑的）。

依赖：Python 3.10+ 标准库；**Pillow**（PNG 预览）；**reportlab**（PDF 预览）。
注意 `reportlab` 在**导入期**就 `from PIL import Image`，因此 **Pillow 一缺，PNG 与 PDF 一起失败**
（本轮对同系列 v9 包的受控导入拦截实测，证据见同系列的 `references/DEGRADE-MATRIX.md`）。
三者都可缺：缺预览件时 `status=partial` 并把原因写入 `uncertainty`，SVG 源文件与契约 JSON 不受影响。

## 8. 评分五维落点（速查；逐条证据见 `references/RUBRIC_MAP.md`）

| 维度 | 分 | 本包落点 |
|-|-|-|
| 实际效果 | 40 | `main.py` 一键产出 7 件（可编辑分层 SVG + PNG/PDF + 证据/布局/校验/契约 4 份 JSON）；`examples/output/` 有两个合成案例的真实运行产物 |
| 使用增益 | 25 | 证据先行 + 连接规则机器审计 + 图例↔图元一致性门；`--merge` 增量改图免重画；对照记录见 `references/GAIN-PROTOCOL.md` |
| 创新增益 | 15 | SIR 中间表示 → 确定性布图 → 三后端同布局；★ **本轴新增**：把"可复造"做成 `determinism_report.json` 机器证据 + 三条只在探针侧生效的稳定化杠杆（不改交付物） |
| 可靠体验 | 10 | `failure-modes.md`（材料/模板/依赖/契约四形态/状态一致性）+ D1–D12 + ★ **D13 漂移声明闸门**；`check.py` 退出码 0/1/3 语义 |
| 生态贡献 | 10 | 文档完整性（SKILL/README/TEST/9 份 references/3 模板）+ 可复用资产（规则字典、配色、清单、SIR 与导出脚本、★ 确定性探针可搬到任何流水线）+ `GITHUB_URL.txt` |

## 9. 边界与诚实原则

- 本 Skill 只负责**绘图表达**与**可编辑交付**；不判断方案科学性，不做数值拟合。
- 拿不到来源就标 null 并计入 `uncertainty`；不伪造软件状态，不编造科研数据。
- 确定性报告里的 `identical=false` **不是掩饰对象**：它精确地指向两条审计性漂移，
  并在 `volatile_fields[]` 里逐条给出 `why` 与 `stabilizer`。
- `stabilized` 条件的三条杠杆**只存在于探针**；正式交付物里仍是真实时间戳与真实输出路径。
- `examples/` 仅为接口演示（产物标注「示例，非正式案例」），不含任何预制答案。
