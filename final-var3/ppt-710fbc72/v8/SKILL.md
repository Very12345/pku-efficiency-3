---
name: academic-slide-adapt
description: >-
  Academic slide deck creation from research material with real template
  adaptation (学术 PPT 模板与格式适配), plus a runnable output-contract matrix:
  scripts/contract_matrix.py injects each container form (string / array /
  object / number / boolean / nested) and each boundary value (empty string,
  empty array, empty object, 0, false, null, oversized, non-ASCII key, absent
  contract, non-object contract) into case.json's output_contract, runs the real
  two-phase pipeline as a child process, re-runs the independent CP3 gate, and
  records the measured exit code, status, echoed key set, widget type actually
  written, whether a null placeholder escaped, and whether a violation was
  silent. Use when the task says "make an academic presentation / 学术PPT /
  学术汇报 / 论文转PPT / adapt this paper into slides / 套模板 / 模板适配 /
  按模板生成PPT / deck from paper", for a starting deck that must be re-edited
  on its own template, or when a reviewer asks "what exactly does this Skill do
  when the contract is empty / null / not an object".
---

# Academic Slide Adapter（学术 PPT 模板与格式适配）— 契约形态与边界值矩阵

做学术汇报 PPT，并且**把交付契约的每一种形态都真跑一遍**：契约声明字符串、数组、
对象、数值、布尔、嵌套六种容器形态，以及空串/空数组/空对象/`0`/`false`/`null`/
超长/非 ASCII 键/缺契约/空契约/非对象契约等边界值——逐个注入 `case.json`，跑真实
管线，再用**独立门**复查一次，把 exit、`status`、回显键集合、实际写出的类型、
有没有 `null` 漏出去、以及**这次失败是被谁发现的**全部记下来。

- Skill 版本：`2.0.0`（两阶段工作流 + CP1–CP3 门，与基线同源）
- **Skill 根 = 本文件所在目录**；下文 `$SKILL_DIR` 都指它，命令在**任意 cwd**
  下都能跑（脚本用 `os.path.dirname(__file__)` 自定位）
- 核心入口：`$SKILL_DIR/scripts/main.py`
- **本轴入口**：`$SKILL_DIR/scripts/contract_matrix.py`（26 个用例 + 独立门复查）
- **资源形态**：只含 UTF-8 文本，≤50 个、单文件 ≤500KB、合计 ≤2MB、无符号链接

**执行顺序**：
**① 读 `references/OUTPUT_CONTRACT.md`（字段契约 + G1–G8 门）** →
**② 跑一次正式流程（`main.py`）→ ③ 跑 `contract_matrix.py` 拿契约行为证据** →
**④ 按 `references/CONTRACT-MATRIX.md` 核对"静默通过清单"与"未覆盖声明"** →
**⑤ 按 `references/RUBRIC_MAP.md` 五维自评**。

---

## 1. 契约回显是怎么工作的（读代码得出的三条事实）

| 事实 | 位置 | 含义 |
|-|-|-|
| 契约只从 **`case.json.output_contract`** 读取 | `extract.extract()` → `content["output_contract"]` | 写在 `task.md` 里的契约**不被识别** |
| 回显发生在**流程末尾**，且只补"结果里还没有的键" | `main._echo_output_contract()` | 已知语义的键取**本次运行真实值**，未知键取**类型默认值**（`""/[]/{}/0/false`），**绝不填 `null`** |
| G3 只检查**顶层**：键存在 且 非 `null` | `check_contract.run_gates()` | 判定粒度是顶层键，不看子键，也不校验"回显值是否等于声明值" |

第三条是**本轴实测出来的关键边界**：G3 通过**不等于**回显值等于声明值——见 §4。

## 2. 一条命令（正式流程）

```bash
SKILL_DIR=<本包根目录>          # 平台装到 /skills/weekly-skill
python "$SKILL_DIR/scripts/main.py" --case <case.json> [--task <task.md>] \
    [--work <材料基目录>] [--template <模板.pptx>] \
    [--starting-deck <deck.pptx>] --out <输出目录>
```

平台正式运行时：`--case /input/case.json --task /input/task.md --work /app/work --out /app/output`。

## 3. 一条命令（契约矩阵实验）

```bash
RUN=<包外可写目录>              # 包内跑会留下 __pycache__，资源契约拒收
python "$SKILL_DIR/scripts/contract_matrix.py" --skill "$SKILL_DIR" --run "$RUN" \
    --json "$RUN/contract_matrix_report.json" --markdown "$RUN/contract_matrix.md"
# exit 0 = 没有任何用例"静默通过"
python "$SKILL_DIR/scripts/contract_matrix.py" --skill "$SKILL_DIR" --list   # 只列用例
```

**26 个用例分三族**：

| 族 | 数量 | 内容 |
|-|-|-|
| **A 容器形态** | 6 | 字符串 / 数组 / 对象 / 数值 / 布尔 / 嵌套 |
| **B 边界值** | 14 | 空串、空数组、空对象、`0`、`false`、`null`、超长值、超长键名、非 ASCII 键、**缺** `output_contract`、空契约 `{}`、语义未覆盖键名、语义已知键（对照）、`preview_png: false` |
| **C 输入完整性** | 6 | `--case` 不存在 / case.json 非法 JSON / 契约是字符串 / 契约是数组 / case.json 为 `{}` / `--case` 指向目录 |

## 4. 实测结论（本机 python 3.13.9，26 个用例）

- **26/26 按声明**；**静默通过 0 个**；被独立门拦下 0 个
- **顶层出现 `null` 占位的用例：0/26**（含契约自己声明 `null` 的那个）
- 契约是对象的 20 个用例里，**契约键未回显：0 个**；容器类型被改：0 个
- 六种容器形态全部**保持声明类型**，取类型默认值：
  字符串→`""`、数组→`[]`、对象→`{}`、数值→`0`、布尔→`false`、嵌套→`{}`
- `0` 与 `false` **没有被 falsy 判断吞掉**（键仍在，值正确）
- 没有契约 / 空契约：回显 0 键，**G3 仍全过**（`missing=[]`）
- **契约声明 `preview_png: false` 时，顶层回显是 `true`**，同时
  `contract_echo_derived` 记 `{"preview_png": true}`、G8 记
  `preview_required=False`——**实测两处"值被改写"之一，见 §5**
- **契约不是对象（字符串/数组）时**：`AttributeError: 'str' object has no
  attribute 'items'` 被捕获 → `exit=1`、`status=failed`；中间产物仍落盘 10 个，
  但 `result.json` 只剩 **14 个顶层键**（完整信封 28 键）——**实测两处之二**
- 完整信封（契约回显全算上）**28 个顶层键**；示例案例自身回显 4 键时为 **25 键**；`--out` 下 **12 个产物**（含 deck 与两张 PNG）

逐用例明细见 **`references/CONTRACT-MATRIX.md`**（由实测报告渲染，非手抄）。

## 5. 两处"值被改写"：为什么算有意、代价是什么

### 5.1 契约 `false` → 回显 `true`

契约里的布尔不是"事实声明"，而是"这次需要什么"。管线确实产出了预览（预览是默认
交付物），把真值写成 `false` 才是撒谎。**关键是改写不自静默**：同时进
`contract_echo_derived`（可查"这个 true 从哪来"）与 G8 的 `preview_required`（按
契约原值判定）。

### 5.2 非对象契约 → 诚实失败 + 信封降级

`_echo_output_contract()` 直接对契约调用 `.items()`，契约是字符串/数组时抛
`AttributeError`。异常在流程末尾，于是：产物基本齐全、`result.json` 只剩失败信封
（14 键）、独立门判 `valid=false`。

**判定**：不是静默（管线承认失败且写明原因），但是**信封降级**——失败记录本身很薄。
本轴**只报告不修**：既有脚本按规范逐字节保持不变；真要修只有一行
（入口处 `contract = contract if isinstance(contract, dict) else {}`），属于改变既有
行为，超出本轴范围。

## 6. "静默通过"的判定口径（本轴的核心概念）

一个用例只有**同时**满足三条才算静默通过：

1. 实测违反了该用例声明的判据（exit / status / 全键回显 / 无 null / 容器类型）；
2. 管线自己 **exit 0 且 `status=success`**；
3. **独立门 `check_contract.py` 也返回 0**。

不满足第 3 条 → 记 `被门拦下`（验证器正常工作）；不满足第 2 条 → 记 `信封降级`
（管线承认失败）。**这条口径就是为了不把"验证器抓到了"误报成缺陷。**

## 7. 决策规则（D1–D12）

| # | 情形 | 决策（做什么 / 记在哪） |
|-|-|-|
| D1 | `case.json` 缺失/不可解析/指向目录 | 立即失败（exit 1）并说明原因，不产半成品冒充成功 |
| D2 | 材料缺失/不可读 | 用 case.json 结构化字段继续；缺失项进 `uncertainty`，**绝不编造** |
| D3 | 材料无文本层 | 不 OCR 冒充，如实标注"图像型材料" |
| D4 | CP1 方案门有偏差 | 先修方案；确属硬约束 → 继续但显式记录，`status` 降 `partial` |
| D5 | 图/表抽不出 | 保留带图号+来源的占位框，不伪造 |
| D6 | 模板缺失/损坏/全链失败 | 回退 case→starting deck→运行时内置模板；全链失败写 `status=failed` |
| D7 | 方案↔执行不一致 / 主题读失败 | best-fit 替代并逐条记录偏差 |
| D8 | 文本框溢出 | 字号阶梯只降到 12pt，仍溢出就报告 |
| D9 | 页数超限 | 确定性裁剪并记录，优先合并非证据页 |
| D10 | 契约字段未知/无值 | 已知语义取真值（并记 `contract_echo_derived`）；未知键按四形态给 `""/[]/{}/0/false`，**禁止 null**；PDF 导出类键恒 false |
| D11 | 字体缺失 / 无 LibreOffice | 标准字体目录探测 → PIL 内置位图字体；不产伪 PDF，预览标注 SCHEMATIC |
| D12 | 保存失败/流水线异常 | 先落盘已生成的部分产物，报错含已写路径；写 `status=failed` 的 result.json |

**本轴新增的交付前动作**（不属于 D1–D12）：
**R1** 跑 `contract_matrix.py`，要求 exit 0；**R2** 若有用例判为静默通过，逐条在
`references/CONTRACT-MATRIX.md` §6 补进"未覆盖/已知代价"，**不许删用例让它变绿**；
**R3** 正式案例若自带 `output_contract`，抽查 ≥2 个键确认回显类型与声明一致。

## 8. 自查清单

- [ ] `main.py` 跑通，exit 0，`result.json` 顶层覆盖契约全部字段、**无 `null`**
- [ ] `check_contract.py` G1–G8 全过、exit 0
- [ ] `contract_matrix.py` 跑通，exit 0；**静默通过 = 0**
- [ ] 契约里每个键的**容器类型**与声明一致（字符串/数组/对象/数值/布尔）
- [ ] 契约里 `0` / `false` / `""` / `[]` / `{}` 这些 falsy 值**仍然出现在顶层**
- [ ] 已知语义的键出现在 `verification.contract_echo_derived` 里，可查来源
- [ ] `references/CONTRACT-MATRIX.md` 的用例表与实际报告一致（重新生成而非手改）
- [ ] 未使用预制答案、未提交正式案例结果

## 9. 目录结构

```
<skill root>/                      # = $SKILL_DIR
  SKILL.md                 本文档（契约回显三条事实 + 26 用例判据 + D1–D12）
  README.md                使用说明 / 依赖 / 限制 / 维护
  TEST.md                  本地实测记录（含 contract_matrix.py 真实输出摘要）
  GITHUB_URL.txt           GitHub 公开链接
  references/
    OUTPUT_CONTRACT.md     result.json 字段契约 + CP3 G1–G8（**只读，逐字保留**）
    CONTRACT-MATRIX.md     ★本轴：26 用例逐行实测 + 静默通过清单 + 未覆盖声明
    RUBRIC_MAP.md          五维评分 → 本包哪个文件/机制
    failure-modes.md       失败模式与降级策略
    template_guide.md      模板使用指南
    checklist.md           适配检查清单
    batch-rules.md         批量一致性规则
    two-phase-workflow.md  两阶段工作流图示与分步命令
  scripts/
    main.py                编排入口（两阶段 + CP1/CP3）
    contract_matrix.py     ★本轴：容器形态 × 边界值矩阵 + 独立门复查
    extract.py / deckplan.py / adopt_plan.py / adapt_pptx.py / preview.py / audit.py
    validate_result.py / check_contract.py
    pptx_toolkit.py / make_template.py / make_synthetic_inputs.py / common.py
  examples/                最小示例（合成数据）
```

## 10. 维护

- 改契约回显逻辑（`main._echo_output_contract` / `check_contract.run_gates`）→
  **必须重跑 `contract_matrix.py`** 并重新渲染 `references/CONTRACT-MATRIX.md`；
- 新增用例只能"加"，不能为了让矩阵变绿而**放宽声明**；实测与声明不符时，
  正确动作是**改声明的期望值并写明理由**（本轴就是这么处理 `C03`/`C04`/`C05` 的）；
- 交付前包外验收：`python validate_pkg.py <包目录>`；
- 二进制资源永不入包。
