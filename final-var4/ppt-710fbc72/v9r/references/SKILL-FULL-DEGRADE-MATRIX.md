---
name: academic-slide-adapt
description: >-
  Academic slide deck creation from research material with real template
  adaptation (学术 PPT 模板与格式适配), shipped with a measured dependency
  degradation probe and a minimum-viable-environment list: scripts/degrade_probe.py
  simulates a missing python-pptx / Pillow / lxml / matplotlib / numpy / yaml /
  reportlab (controlled ImportError shadowing on PYTHONPATH) or a missing
  LibreOffice (empty PATH), runs the real pipeline and the single-purpose
  entries as child processes, and records the measured exit code, whether
  result.json was still written, the status, how many artifacts survived,
  which uncertainty entry explains it, and where the run actually broke. Use
  when the task says "make an academic presentation / 学术PPT / 学术汇报 /
  论文转PPT / adapt this paper into slides / 套模板 / 模板适配 / 按模板生成PPT /
  deck from paper", when a starting deck must be re-edited on its own template,
  or when someone asks "what still works if python-pptx is missing".
---

# Academic Slide Adapter（学术 PPT 模板与格式适配）— 缺依赖降级链实测

做学术汇报 PPT，并且**把"缺依赖会怎样"逐个测出来**：用受控导入拦截（`PYTHONPATH`
前置一个 `import` 即抛 `ImportError` 的同名包）模拟 python-pptx / Pillow / lxml /
matplotlib / numpy / yaml / reportlab 缺失，用空 `PATH` 模拟 LibreOffice 缺失，
逐个跑真实入口，记录**实测**降级形态——产物还剩什么、`status` 变成什么、是否仍写
`result.json`、退出码是多少、在哪一步断的。

- Skill 版本：`2.0.0`（两阶段工作流 + CP1–CP3 门，与基线同源）
- **Skill 根 = 本文件所在目录**；下文 `$SKILL_DIR` 都指它，命令在**任意 cwd** 下都能跑
- 核心入口：`$SKILL_DIR/scripts/main.py`
- **本轴入口**：`$SKILL_DIR/scripts/degrade_probe.py`（10 个场景 + 投毒有效性校验）
- **资源形态**：只含 UTF-8 文本，≤50 个、单文件 ≤500KB、合计 ≤2MB、无符号链接

**执行顺序**：
**① 读 `references/OUTPUT_CONTRACT.md`（字段契约 + G1–G8）** →
**② 跑一次正式流程（`main.py`）** → **③ 跑 `degrade_probe.py` 拿降级证据** →
**④ 按 `references/DEGRADE-MATRIX.md` 核对"最小可用环境"与"彻底不可用清单"** →
**⑤ 按 `references/RUBRIC_MAP.md` 五维自评**。

---

## 1. 实测结论（先给结论，再给判据）

| 判据 | 结果 |
|-|-|
| **硬依赖**（拿掉 ⇒ 整条流程失败） | **`python-pptx` · `Pillow` · `lxml`** |
| **非依赖**（拿掉 ⇒ 与基线逐项相同） | `numpy` · `matplotlib` · `yaml` · `reportlab` · **LibreOffice** |
| 投毒未生效的场景 | **0**（每个场景都用 `python -c "import X"` 单独验证） |
| **静默通过**（该失败却 exit 0 + `success`） | **0** |

- **干净基线**：exit=0、`status=success`、`--out` **12** 个产物、`result.json`
  **28** 个顶层键（契约回显全算上；示例案例自身回显 4 键）、deck + 2 PNG
- **任何硬依赖缺失**：exit=1、`status=failed`、`--out` **只剩 1 个产物**
  （`result.json`，14 个顶层键）、deck 无、PNG 0 张、`uncertainty` 1 条
  （`item=pipeline`，note 是原始异常文本）

⇒ 本包的降级是**两态**的：要么完整交付，要么**诚实失败**（写失败信封 + 原因），
**没有第三种"看起来成功但少了东西"的形态**。

## 2. 两条命令

**① 正式流程**（产物写 `--out`，两阶段自动完成）：

```bash
SKILL_DIR=<本包根目录>          # 平台装到 /skills/weekly-skill
python "$SKILL_DIR/scripts/main.py" --case <case.json> [--task <task.md>] \
    [--work <材料基目录>] [--template <模板.pptx>] \
    [--starting-deck <deck.pptx>] --out <输出目录>
```

平台正式运行时：`--case /input/case.json --task /input/task.md --work /app/work --out /app/output`。

**② 缺依赖降级实测**（`--run` 必须包外；包内跑会留下 `__pycache__`，资源契约拒收）：

```bash
RUN=<包外可写目录>
python "$SKILL_DIR/scripts/degrade_probe.py" --skill "$SKILL_DIR" --run "$RUN" \
    --json "$RUN/degrade_report.json" --markdown "$RUN/degrade.md"
# exit 0 = 每个场景都按声明、且投毒全部生效（无静默通过）
python "$SKILL_DIR/scripts/degrade_probe.py" --skill "$SKILL_DIR" --list   # 只列场景
```

## 3. 场景与判据

| 场景 | 缺什么 | 实测 exit | status | 产物 | deck |
|-|-|-|-|-|-|
| 01 | `pptx` | **1** | `failed` | 1 | 无 |
| 02 | `PIL` | **1** | `failed` | 1 | 无 |
| 03 | `matplotlib` | 0 | `success` | 12 | 有 |
| 04 | `numpy` | 0 | `success` | 12 | 有 |
| 05 | `yaml` | 0 | `success` | 12 | 有 |
| 06 | `lxml` | **1** | `failed` | 1 | 无 |
| 07 | `reportlab` | 0 | `success` | 12 | 有 |
| 08 | LibreOffice（PATH 置空） | 0 | `success` | 12 | 有 |
| 09 | 全部 7 个 Python 依赖（合并） | **1** | `failed` | 1 | 无 |
| 10 | `PIL` + **预先生成真实源图**（对照） | **1** | `failed` | 1 | 无 |

**判定口径**：每个场景都先声明"应该 exit 几 / status 是什么 / 是否该写 result.json /
该不该产 deck"，再与实测比对。**"静默通过" = 与声明不符但 exit 0 且 `status=success`**
——实测 0 个。另有独立一道闸：**投毒有效性**——若 `python -c "import X"` 在投毒环境
下仍成功，说明这个场景什么都没测到，直接判失败（实测 0 个）。

## 4. 三条最容易踩错的结论

### 4.1 `lxml` 是**间接硬依赖**，本包代码一次都没 import 它

`grep` 实测本包 `scripts/*.py` **无一处**引用 `lxml`（XML 走标准库
`xml.etree.ElementTree`）；但 `python-pptx` 自己在**包级**做 `from lxml import etree`，
所以**缺 lxml 等于缺 pptx**。⇒ **只按"本包 import 了什么"列依赖清单会漏掉真依赖。**

### 4.2 `PIL` 缺了是**硬失败**，不是"只是没有预览"

`preview.py` 在**模块级** `from PIL import Image, ImageDraw, ImageFont`，而预览是主
流程第 5 步 ⇒ 整条流程失败，**deck 也不产出**。对照场景（先预生成真实源图再投毒）
结果相同，证明这条失败与"材料里有没有图"无关。

### 4.3 LibreOffice 缺失**完全无影响**，因为管线从不调用它

`preview.py` 从不 shell out 到 `soffice`：它画 **PIL 示意图**，并在
`render_log.json`（`renderer` + `honest_note`）、`_PREVIEW_ARE_SCHEMATIC.txt`、
`result.json.main_result.preview_is_schematic` **三处**如实标注。装了 LibreOffice
也不会让预览变成真 PDF——那是**已被明确放弃并披露的能力**，不是缺环境项。

## 5. 「最小可用环境」（实测口径）

```bash
python -m pip install "python-pptx>=0.6.21" "Pillow>=9.0"
# lxml 会作为 python-pptx 的依赖自动装上；不要手工省略
```

| 项 | 实测版本 | 可省？ | 理由 |
|-|-|-|-|
| Python | 3.13.9 | 否 | 代码注释法与 `X \| None` 注解 ⇒ 需 **3.9+** |
| `python-pptx` | 1.0.2 | **否** | 建/读 pptx（阶段一审计 + 阶段二构建 + G4 重开） |
| `Pillow` | 12.3.0 | **否** | 预览（模块级 import）、示例图、字体探测 |
| `lxml` | 已装 | **否** | `pptx` 的包级依赖 ⇒ 装了 pptx 就有 |
| 系统字体 | — | 可省 | 找不到就回退 PIL 内置位图字体并如实记录 |
| LibreOffice / uno | 未装 | **可省** | 实测无影响；预览本就是示意图 |
| `numpy`/`matplotlib`/`yaml`/`reportlab` | 已装 | **可省** | 仅 `tool_versions` 记版本 |
| 网络 | — | **可省** | 全流程离线 |

最小环境的验收：`main.py` 与 `check_contract.py` 都 exit 0，`--out` 下 12 个产物、
`result.json` 28 个顶层键。逐项实测见 **`references/DEGRADE-MATRIX.md`**。

## 6. 决策规则（D1–D12）

| # | 情形 | 决策（做什么 / 记在哪） |
|-|-|-|
| D1 | `case.json` 缺失/不可解析 | 立即失败（exit 1）并说明原因，不产半成品冒充成功 |
| D2 | 材料缺失/不可读 | 用 case.json 结构化字段继续；缺失项进 `uncertainty`，**绝不编造** |
| D3 | 材料无文本层 | 不 OCR 冒充，如实标注"图像型材料" |
| D4 | CP1 方案门有偏差 | 先修方案；确属案例硬约束 → 继续但显式记录，`status` 降 `partial` |
| D5 | 图/表抽不出 | 保留带图号+来源的占位框，不伪造 |
| D6 | 模板缺失/损坏/全链失败 | 回退 case→starting deck→运行时内置模板；全链失败写 `status=failed` |
| D7 | 方案↔执行不一致 / 主题读失败 | best-fit 替代并逐条记录偏差 |
| D8 | 文本框溢出 | 字号阶梯只降到 12pt，仍溢出就报告 |
| D9 | 页数超限 | 确定性裁剪并记录，优先合并非证据页 |
| D10 | 契约字段未知/无值 | 已知语义取真值；未知键按四形态给 `""/[]/{}/0/false`，**禁止 null** |
| D11 | 字体缺失 / 无 LibreOffice | 标准字体目录探测 → PIL 内置位图字体；**不产伪 PDF**，预览标注 SCHEMATIC |
| D12 | 保存失败/流水线异常 | 先落盘已生成的部分产物，报错含已写路径；写 `status=failed` 的 result.json |

**D11 补充（本轴实测加强）**：`preview.py` 对 LibreOffice 的能力缺口是**设计上的
放弃**，不是运行时探测失败；请在评估"环境是否完整"时把它排除（实测缺它无影响）。
**D12 补充**：硬依赖缺失走的就是 D12 这条路径——写失败信封、`uncertainty` 带原始
异常文本、exit 1。实测失败信封是 **14 个顶层键**（完整信封 28 键），产物只剩
`result.json` 一个。

**本轴新增的交付前动作**（不属于 D1–D12）：
**R1** 跑 `degrade_probe.py`，要求 exit 0（含"投毒全部生效"）；
**R2** 若正式运行环境的依赖清单与 §5 的「最小可用环境」不一致，逐条在
`references/DEGRADE-MATRIX.md` §6 更新并重跑矩阵——**不许靠"应该没事"跳过**。

## 7. 自查清单

- [ ] `main.py` 跑通，exit 0，`result.json` 28 个顶层键、无 null
- [ ] `check_contract.py` G1–G8 全过、exit 0
- [ ] `degrade_probe.py` 跑通，exit 0；**投毒未生效 = 0**、**静默通过 = 0**
- [ ] 环境里的 `python-pptx` / `Pillow` / `lxml` 三个硬依赖**都在**（版本见 `README.md`）
- [ ] 环境里缺 `numpy`/`matplotlib`/`yaml`/`reportlab`/LibreOffice 时**不需要**任何
      额外处理（实测无影响）——但也不要把它们写进"必需依赖"
- [ ] `references/DEGRADE-MATRIX.md` 的表格与实际报告一致（重新生成而非手改）
- [ ] 未使用预制答案、未提交正式案例结果

## 8. 目录结构

```
<skill root>/                      # = $SKILL_DIR
  SKILL.md                 本文档（硬依赖/非依赖实测 + 最小可用环境 + D1–D12）
  README.md                使用说明 / 依赖 / 限制 / 维护
  TEST.md                  本地实测记录（含 degrade_probe.py 真实输出摘要）
  GITHUB_URL.txt           GitHub 公开链接
  references/
    OUTPUT_CONTRACT.md     result.json 字段契约 + CP3 G1–G8（**只读，逐字保留**）
    DEGRADE-MATRIX.md      ★本轴：10 场景逐项实测 + 最小可用环境 + 彻底不可用清单
    RUBRIC_MAP.md          五维评分 → 本包哪个文件/机制
    failure-modes.md       失败模式与降级策略
    template_guide.md      模板使用指南
    checklist.md           适配检查清单
    batch-rules.md         批量一致性规则
    two-phase-workflow.md  两阶段工作流图示与分步命令
  scripts/
    main.py                编排入口（两阶段 + CP1/CP3）
    degrade_probe.py       ★本轴：受控导入拦截 + PATH 置空 + 投毒有效性校验
    extract.py / deckplan.py / adopt_plan.py / adapt_pptx.py / preview.py / audit.py
    validate_result.py / check_contract.py
    pptx_toolkit.py / make_template.py / make_synthetic_inputs.py / common.py
  examples/                最小示例（合成数据）
```

## 9. 维护

- **改动任何 `import` 语句或依赖版本 → 必须重跑 `degrade_probe.py`** 并重新渲染
  `references/DEGRADE-MATRIX.md`；声明表只允许"新增场景 + 写明理由"，**不允许为了
  让矩阵变绿而放宽声明**（实测与声明不符时，正确动作是改**期望值**并写明原因）。
- **本轴的核心防腐点**：`lxml` 这种"不 import 但被依赖"的情况。新增第三方依赖后，
  先跑一次"把它拿掉"的场景，再决定要不要写进 `README.md` 的必需依赖。
- 交付前包外验收：`python validate_pkg.py <包目录>`。
- 二进制资源永不入包。
