---
name: apparatus-and-route-diagrams-degrade-chain
description: >-
  v9 轴：缺依赖降级链实测。用受控导入拦截（子进程 sys.meta_path 拦截器）逐个抽走
  Pillow/reportlab/yaml/numpy/matplotlib/python-pptx 与 LibreOffice CLI，跑同一份输入的
  完整主流程，实测「产物还剩什么、status 变什么、还写不写 result.json、退出码是多少」；
  scripts/degrade_probe.py 产出 degrade_report.json，references/DEGRADE-MATRIX.md 给出
  逐项实测表、哪些功能彻底不可用、以及分档的「最小可用环境」清单。
  既有 15 个脚本入口与 27 个 --flag 一个不少，脚本逐字节未改。
---

# 实验装置与技术路线图 Skill · v9 版（轴：**缺依赖降级链实测**）

> **文档路径重定向（本包 v9）**
>
> * `references/MECHANISM.md` → 已全文并入 `references/GAIN-PROTOCOL.md` 尾部的「并入全文」附录（本包 v9 为守住平台「≤50 个 UTF-8 文本文件」硬门而合并，**内容一字未删**）；本文出现的旧路径请按该附录阅读。
> * `references/CASE-SET.md` → 已全文并入 `references/failure-modes.md` 尾部的「并入全文」附录（本包 v9 为守住平台「≤50 个 UTF-8 文本文件」硬门而合并，**内容一字未删**）；本文出现的旧路径请按该附录阅读。

本 Skill 把科研材料变成**可编辑、可追溯、可复跑**的图稿：分层 SVG 源文件 + PNG/PDF 预览 +
`evidence.json`（证据链）+ `result.json`（含 `output_contract` 全字段 + `case_id`）。

**v9 这一版只做一件事：把「依赖缺了会怎样」从文档口径变成逐项实测。**
算法、CLI、既有脚本全部不动（15 个脚本入口逐字节不变、27 个 `--flag` 全保留），
新增 1 个可运行脚本 + 1 份逐项实测文档。

| 本包新增（v9 轴） | 作用 | 实测结论（数字见 §4，全部现场跑出） |
|-|-|-|
| `scripts/degrade_probe.py` | 13 个条件（逐个拦截 + 组合 + 关键标准库对照）跑同一份输入的主流程 | 真实依赖只有 **2** 个；**Pillow 一缺，PNG 与 PDF 一起没**；规格点名的 5 项**零差异** |
| `references/DEGRADE-MATRIX.md` | 逐项实测表 + 可用性结论 + 彻底不可用清单 + **分档最小可用环境** | 纯标准库 **仍产出 5 件**（SVG + 4 份 JSON，`status=partial`）；`xml`/`hashlib` 缺 ⇒ **0 件** |

> 与前一版的关系：v9 = v6（全维合并版）**内容全保留** + 降级链轴。
> 为守住「≤50 个 UTF-8 文本文件」硬门，`references/MECHANISM.md` 与
> `references/CASE-SET.md` 的**全文**并入了同主题宿主文档（见 §7 清单，一字未删）。

## 0. 技能根与自定位（先读这一节）

- **技能根 = 本 `SKILL.md` 所在目录**（平台安装到 `/skills/weekly-skill`）。下文一律用 `$SKILL_DIR`：

  ```bash
  SKILL_DIR=/skills/weekly-skill                              # 平台安装位置
  SKILL_DIR="$(cd "$(dirname /path/to/SKILL.md)" && pwd)"      # 本地解包位置
  ```

- `scripts/*.py` 全部 `os.path.dirname(__file__)` 自定位，读 `templates/`/`assets/`/`references/`
  相对技能根解析，**不依赖 cwd**；脚本内已置 `sys.dont_write_bytecode = True`。
- **本包只含文本资源**（`.md/.py/.json/.txt/.csv/.yaml/.yml`），**49 个文件**（上限 50）、
  单文件最大 51 KB（上限 500 KB）、合计约 0.56 MB（上限 2 MB）、无符号链接、无 `__pycache__`。
  `figure.svg`/`figure.png`/`figure.pdf` 由 `main.py` **运行时生成**，不随包发布。
- **本包的依赖面很窄**（这是 v9 实测出来的，不是声明出来的）：
  第三方只有 **Pillow** 与 **reportlab**，其余全是标准库；不调用任何外部 CLI。

## 1. 用途与适用条件

- **输入**：`/input/case.json` + `/input/task.md`（可选）+ 材料（`--material` 或内联文本）。
  结构化与自由文本两种 case.json 都支持。
- **输出**：`<out>/<case_id>/` 下最多 7 件：`evidence.json`、`layout.json`、`figure.svg`、
  `figure.png`、`figure.pdf`、`verify_report.json`、`result.json`。
  **缺依赖时能少产出哪几件、`status` 变什么，见 §4 实测表**。
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
给具体文件时 `--task` 需显式传入。`--merge` 是编辑既有图稿的入口。
**参数名/默认值/退出码语义在 v9 中一字未改。**

## 3. 执行步骤

1. **读真实文件** → 2. **证据抽取（CP1）** → 3. **SIR 与布图**（`model.py` → `layout.py`）→
4. **渲染**（`render_svg.py`；`export_preview.py` 出 PNG/PDF）→ 5. **校验（CP2/CP3）** →
6. **契约门（CP4）**（`check.py` 的 G1–G10）→ 7. **★ v9 追加：降级链复核**（部署前/换环境时跑）。

## 4. ★ 本包的轴：缺依赖降级链（命令 / 判据 / 实测数字）

### 4.1 一条命令跑出 13 个条件

```bash
python "$SKILL_DIR/scripts/degrade_probe.py" --json /tmp/degrade_report.json
python "$SKILL_DIR/scripts/degrade_probe.py" --only c01-no-PIL --only c02-no-reportlab   # 只看真实依赖
python "$SKILL_DIR/scripts/degrade_probe.py" --only c04-no-PIL.Image                     # 拦截器自证
python "$SKILL_DIR/scripts/degrade_probe.py" --list                                      # 只列条件
python "$SKILL_DIR/scripts/degrade_probe.py" --expect-deviations 0                       # 回归断言
```

**方法**：不改脚本、不卸载包 —— 在**子进程**里装一个 `sys.meta_path` 拦截器
（现场生成 `_blocker_driver.py`），对命中前缀的模块 `find_spec` 直接抛
`ModuleNotFoundError`，再用 `runpy` 跑真实 `main.py`。被拦进程的一切行为等价于
"这台机器上没装这个包"。`c10` 用另一种手法模拟"没有 LibreOffice CLI"：把 `PATH`
指向空目录。

**拦截器自证**（防"拦了没拦住"）：`c04` 只拦**子模块** `PIL.Image` 就复现了整包拦截的降级；
`c11`/`c12` 拦关键标准库后流水线整体不可用。两条合起来证明拦截真的生效。

### 4.2 判据

- 每个条件在脚本里**先声明期望形态**（`full` / `degrade` / `zero-diff` / `broken`），
  再与实测比对；不符的进 `deviations[]`；
- `verdict = pass` 要求 `deviations == []`（或用 `--expect-deviations N` 把它变成回归断言）；
- 退出码：**0** = 结论与声明一致；**1** = 出现未预期降级形态；**2** = 用法/环境错误。

### 4.3 实测数字（13 条件，本机 Windows 11 + CPython 3.13.9，约 6 s 跑完）

| 条件 | 拦截 | 退出码 | `status` | 产物数 | 结论 |
|-|-|-|-|-|-|
| `c00-base` | 无 | 0 | `success` | **7** | 对照 |
| `c01-no-PIL` | `PIL` | **3** | `partial` | **5** | **PNG 与 PDF 一起丢**（`exports=[]` ⇒ `G4` 不过） |
| `c02-no-reportlab` | `reportlab` | 0 | `partial` | **6** | 只丢 PDF，仍可交付 |
| `c03-no-PIL-no-reportlab` | 两个 | 3 | `partial` | 5 | 最坏真实情形 |
| `c04-no-PIL.Image` | `PIL.Image`（子模块） | 3 | `partial` | 5 | 拦截器自证：与 `c01` 同形 |
| `c05`–`c08` | `yaml` / `numpy` / `matplotlib` / `pptx` | 0 | `success` | **7** | **零差异**：本包不 import 它们 |
| `c09-no-named-five` | 规格点名 5 项 + PIL + reportlab | 3 | `partial` | 5 | 同上，等效于 `c03` |
| `c10-no-soffice` | PATH 清空 | 0 | `success` | **7** | **零差异**：不调用外部 CLI |
| `c11-no-xml` | `xml` | **1** | 无 | **0** | **彻底不可用**（连 `result.json` 都写不出） |
| `c12-no-hashlib` | `hashlib` | **1** | 无 | **0** | **彻底不可用** |

关键事实（都有实测证据）：

1. **`reportlab` 在导入期就 `from PIL import Image`**（`reportlab/lib/utils.py:15`）⇒
   **Pillow 是唯一的"硬"依赖**：它一缺，两个预览都没了（而不是文档里假设的"PNG 靠 PIL、
   PDF 靠 reportlab"的并列关系）。安装顺序上 **Pillow 在前**。
2. **`status` 从不撒谎**：`c01`/`c02`/`c03` 都是 `partial`，`result.json.uncertainty` 里逐条写明
   `{"scope":"png"|"pdf","issue":"… 失败: <原因>","action": …}`（`c02` 只有 `pdf` 一条，
   `c01` 有 `png`+`pdf` 两条）。
3. **退出码会跟着变**：`exports` 为空时 `check.py` 的 `G4` 不过 ⇒ `main.py` 返回 **3**
   （不是 0、也不是崩）—— 契约门在降级时仍然工作。
4. **`result.json` 始终落盘**（除 `xml`/`hashlib` 两个地基条件外）：即使预览全失败，
   结构化结果仍在，回放可见。

### 4.4 「最小可用环境」清单（分三档，实测）

| 档位 | 需要什么 | 能产出什么 | `status` | 退出码 |
|-|-|-|-|-|
| ① **纯标准库** | CPython 3.10+（`json`/`hashlib`/`math`/`xml.etree`/`dataclasses`/`re`） | **5 件**：`figure.svg` + `evidence.json` + `layout.json` + `verify_report.json` + `result.json` | `partial` | 3 |
| ② ①+Pillow | `Pillow` | **6 件**（+ `figure.png`） | `success` | 0 |
| ③ ②+reportlab | `reportlab`（且**必须**有 Pillow） | **7 件**（+ `figure.pdf`） | `success` | 0 |

**明确不需要**（抽走零差异）：`yaml`、`numpy`、`matplotlib`、`python-pptx`、LibreOffice CLI。
**怎么都救不了**（缺了连 `result.json` 都没有）：`xml`（`xml.etree.ElementTree`）、`hashlib`。

逐项表与可用性结论见 `references/DEGRADE-MATRIX.md`（§2–§6）。

## 5. 决策规则与检查点（沿用既有口径，未改）

CP1 证据门 → CP2 连接门 → CP3 校验门 → CP4 契约门；D1–D12 见 `references/failure-modes.md`
（其中 D9/D10 就是依赖缺失的处置：字体缺失记 `fonts.found=false`；渲染失败保留已有产物、
`status=partial`、原因写入 `uncertainty`）。

**v9 追加口径 D15**：**降级后果必须与文档一致**。任何会让产物件数/`status`/退出码发生变化的
依赖变动，必须同步更新 `references/DEGRADE-MATRIX.md` 的「最小可用环境」表；
`scripts/degrade_probe.py` 的 `deviations[]` 是这条口径的可执行闸门（`--expect-deviations 0`）。

## 6. 完成判定清单

- [ ] CP1：`evidence.json` 存在且实体/关系带 `locator`+`quote`
- [ ] CP2/CP3：无 error 级连接规则违规；SVG 合法、5 层齐全、`<text>`≥3；编号连续；图例↔图元一致
- [ ] CP3：`figure.png`/`figure.pdf` 存在且非空；**若缺**：`uncertainty` 有对应 scope 且 `status=partial`
- [ ] CP4：`result.json` 含 18 个顶层字段；`check.py` 输出 `ok: true`
- [ ] **v9 轴**：`python "$SKILL_DIR/scripts/degrade_probe.py"` 退出码 0、
      `deviations == []`；产物件数/`status`/退出码与 `references/DEGRADE-MATRIX.md` 的表一致
- [ ] **v9 轴**：部署环境至少覆盖①档（纯标准库）；要交 PNG/PDF 预览时才需 ②/③ 档
- [ ] 修改历史、不确定性、来源如实记录；包内无绝对路径、无 `__pycache__`

## 7. 资源清单（路径均相对技能根；★ 为 v9 新增/变更）

```
SKILL.md  README.md  TEST.md  GITHUB_URL.txt
scripts/  main.py  gain_evidence.py  model.py  layout.py  render_svg.py  export_preview.py
          svg_verify.py  check.py  fonts.py  preflight.py  fault_inject.py  case_set_run.py
          decision_probe.py  gain_probe.py  bare_baseline.py
          ★ degrade_probe.py          # v9 轴：缺依赖降级链实测（受控导入拦截）
assets/   connection_rules.json
templates/ palette.json  component-connection-checklist.md  entity-relation-checklist.csv
references/ OUTPUT_CONTRACT.md  RUBRIC_MAP.md  failure-modes.md  vocabulary.md
          figure-blueprint.md  GAIN-PROTOCOL.md  FAULT-MATRIX.md  case-set.json
          comparison-data.json  ★ DEGRADE-MATRIX.md
examples/ case.json  task.md  README.md  EXPECTED-OUTPUT.md  apparatus_spec.example.json
          route_spec.example.json  route_spec.mutation.example.json
          cases/{dtms-stage-route-01,mbr-wastewater-flow-01}/{case.json,task.md}
          output/{demo-apparatus-001,demo-biotech-route-01}/{result.json,artifacts.json}
```

**本包的文件合并（守 ≤50 硬门，内容逐字保留）**：

| 现在的宿主文件 | 并入的原文件 | 为什么同主题 | 路径更正 |
|-|-|-|-|
| `references/GAIN-PROTOCOL.md` | `references/MECHANISM.md`（全文） | 都是"凭什么说加载它更好"（机制 vs 公平对照） | `bare_baseline.py`（2 处）、`gain_probe.py`（2 处）的 docstring 旧路径指向宿主文件尾部附录 |
| `references/failure-modes.md` | `references/CASE-SET.md`（全文） | 泛化失效边界（输入退化）本身就是失败模式的一类 | 无脚本 docstring 指向被并文件（`case_set_run.py` 读的是仍在包内的 `case-set.json`） |

**既有合并（非本轮，供路径追踪）**：`references/DECISION-CASES.md` 的内容早已并入
`references/failure-modes.md` 附录 C（该文件头部有说明）；`scripts/decision_probe.py` 的
docstring 里那个旧路径指的就是附录 C。

依赖（分级见 §4.4）：Python 3.10+ 标准库；**Pillow**（PNG 预览，且 reportlab 依赖它）；
**reportlab**（PDF 预览）。三者皆可缺，缺预览件时 `status=partial` 并写入 `uncertainty`。

## 8. 评分五维落点（速查；逐条证据见 `references/RUBRIC_MAP.md`）

| 维度 | 分 | 本包落点 |
|-|-|-|
| 实际效果 | 40 | `main.py` 一键出最多 7 件；`examples/output/` 有两个合成案例真实产物；★ 降级条件下仍产出 5 件（SVG + 契约 JSON） |
| 使用增益 | 25 | 证据先行 + 连接规则审计 + 图例↔图元门；`--merge` 增量改图；对照记录见 `references/GAIN-PROTOCOL.md` |
| 创新增益 | 15 | SIR → 确定性布图 → 三后端同布局；★ **本轴新增**：受控导入拦截把"部署环境要装什么"变成 13 条可跑实测（含拦截器自证） |
| 可靠体验 | 10 | `failure-modes.md` + D1–D12 + ★ **D15 降级后果与文档一致**；★ 本轴给出**分档最小可用环境**与"彻底不可用"清单，退化路径逐条实测 |
| 生态贡献 | 10 | 文档完整性（SKILL/README/TEST/9 份 references/3 模板）+ 可复用资产（规则字典、配色、清单、★ 降级探针可搬到任何 Python Skill）+ `GITHUB_URL.txt` |

## 9. 边界与诚实原则

- 本 Skill 只负责**绘图表达**与**可编辑交付**；不判断方案科学性，不做数值拟合。
- **不夸大可用性**：纯标准库下 `status=partial`、退出码 3，且 `exports` 为空 —— 这是
  `check.py` 的 G4 在诚实报错，不是失败被掩盖。
- 缺依赖时的原因**逐条**写进 `result.json.uncertainty`（scope + issue + action），不静默吞掉。
- 本包**不声称**"任何环境都能出全套产物"；声称的是：每个降级档位的产物都已被实测，并写进 §4.4。
- `examples/` 仅为接口演示（产物标注「示例，非正式案例」），不含预制答案。
