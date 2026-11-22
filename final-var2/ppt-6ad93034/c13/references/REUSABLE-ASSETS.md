# REUSABLE-ASSETS.md — 可复用资产清单、复用命令与移植说明

> **这份文档解决什么问题**：题面「生态贡献 10 分」考的是"作品本体、模板、页面骨架、
> 图表重绘脚本、题集与页级金标准能否被他人**直接复用**"，以及是否有"分享推广价值"。
> 本文把本包里**可以脱离本 Skill 单独拿走的东西**列成清单：每一项给
> **是什么 / 拿走它 / 怎么用 / 依赖 / 适用范围与不适用**。
>
> 一个前提取自题面：**本包不含任何正式案例的答案**；下面所有"题集/金标准"都是
> **虚构示例 + 一次真实运行的文本副本**，用途是接口冒烟与契约对拍，不是评分答案。

---

## 1. 资产总览（按"拿走之后能干什么"排序）

| # | 资产 | 位置 | 依赖 | 拿走它能干什么 |
|-|-|-|-|-|
| A1 | **结果信封 + 契约文档** | `templates/result_envelope.json`、`references/OUTPUT_CONTRACT.md` | 无（纯 JSON + 文档） | 给**任何**产出 `result.json` 的工具当校验依据（G8 就是读它） |
| A2 | **机制判据探针** | `references/mechanism_probe.py` | 标准库（M4 的 pptx 重开需 python-pptx） | 对任意一次运行的产物做 M1–M5 痕迹检查，**不依赖本包其余代码** |
| A3 | **增益测量台** | `references/measure_gain.py`（同目录另有对照协议文档） | python-pptx（仅条件 B 建基线稿用） | 对**任何"材料 → 结构化工件"的 Skill** 做同一口径的对照测量 |
| A4 | **页面骨架与角色词表** | `scripts/slide_text.py`（`ROLE_LABELS`、`AUDIENCE_TONES`、`alloc_roles`） | 标准库 | 把"论文结构 → 页面角色"的取舍规则搬到别的演示生成器 |
| A5 | **编辑操作目录** | `references/EDIT_OPS.md` + `scripts/deck_tool.py::apply_edits` | python-pptx | 给"局部改稿 + 版本归档"提供一套现成的 op 词表与决策树 |
| A6 | **模板参数文件** | `templates/default.json` | 无 | 换配色/字体/页脚**不改代码**；可作为别家模板的 schema 参考 |
| A7 | **数字核验器** | `scripts/evidence_check.py::check_claim_numbers` | 标准库 | 任何"页面/报告 vs 原文"的数字一致性检查（CLI 可直接用） |
| A8 | **示例即冒烟题集** | `examples/`（case/task/material/csv/edit_demo + `EXPECTED-OUTPUT.md`） | 无 | 新实现的接口冒烟与产物清单对拍 |
| A9 | **契约形态与状态一致性规则** | `references/failure-modes.md` §4/§5/§6 | 无 | 给别人写"降级要留痕"的规范时可直接引用（四形态表、状态自洽表） |

---

## 2. 逐项复用命令（复制即用）

### A1 结果信封 + 契约文档

```bash
# 把信封拷到你自己的验证器旁边
cp "<SKILL_DIR>/templates/result_envelope.json" ./schema/result_envelope.json
# 用它校验任何 result.json（本包的 result_tool 已内置这条逻辑，G8）
python "<SKILL_DIR>/scripts/result_tool.py" --result <你的>/result.json --out-dir <你的> \
    --case <你的>/case.json --envelope ./schema/result_envelope.json
```

**复用点**：`required_fields` 与字段类型声明是**数据**，不是代码；
你可以只拿走这个 JSON，用自己语言的验证器实现同一份检查。

### A2 机制判据探针（**最独立的一个资产**）

```bash
python "<SKILL_DIR>/references/mechanism_probe.py" --out <任意一次运行的输出目录>
# 期望：M1–M5 全 PASS，退出码 0；有 FAIL 时退出码 1
```

- 它只读 `result.json` + 产物文件；
- **可配合你自己的 Skill**：只要你的产物里有 `deck.slides[].role`、
  `claims[].evidence`、`figure.kind`、`deck_editable`、`changelog/manifest`，
  同一探针就能用；
- 它写出的报告文件名固定为 `mechanism-probe-report.json`（写在**当前工作目录**，
  所以在包外跑）。

### A3 增益测量台

```bash
cp "<SKILL_DIR>/references/measure_gain.py" <tmp>/     # 必须在包外跑，避免 __pycache__
python <tmp>/measure_gain.py --skill-dir "<你的技能包>" \
    --case <case1.json> --case <case2.json> --work <tmp>/work --out <tmp>/gain-report.json
```

- 条件 B 的基线生成器（`build_baseline_deck`）是**确定性**的，可被替换成
  你自己的基线实现（例如"只抽摘要"）；
- 五项质量指标（Q1/Q3/Q4/Q5/Q6）只依赖 `result.json` 与产物目录，
  **换成别的领域的结构化工件也能用**（把字段名映射改到 `metric_skill` 里即可）。

### A4 页面骨架与角色词表

```python
import sys; sys.path.insert(0, "<SKILL_DIR>/scripts")
from slide_text import ROLE_LABELS, AUDIENCE_TONES, alloc_roles   # 不触发任何 I/O
```

- `ROLE_LABELS` 是九种叙事角色（cover/overview/background/question/method/
  result/discussion/limitation/takeaway）与中文标签；
- `alloc_roles` 是**纯函数式**的确定性分配：输入材料视图 + spec，输出页级角色序列；
- **移植提示**：把"角色 → 页面模板"的映射换成你自己模板的版式名即可，
  规则本身（富余页先插背景/讨论/局限，再增加结果页）与领域无关。

### A5 编辑操作目录

```bash
# 操作词表（7 类）与决策树：直接当规范用
sed -n '1,80p' "<SKILL_DIR>/references/EDIT_OPS.md"
# 参考实现
python "<SKILL_DIR>/scripts/main.py" --case <case.json> --out <out> \
    --edit "<SKILL_DIR>/examples/edit_demo.json" --version v2
```

7 类 op：`update_bullet / add_bullet / remove_bullet / add_note / retitle /
reorder_pages / set_figure`；每次改动写一条
`{version, op, page, target, reason}`，旧版本以 `deck_<version>.pptx` 归档。

### A6 模板参数文件

```bash
cp "<SKILL_DIR>/templates/default.json" ./my-template.json   # 改颜色/字体/页脚即可
python "<SKILL_DIR>/scripts/main.py" --case <case> --out <out> --template ./my-template.json
```

**复用点**：颜色、字体族、页脚文案、槽位尺寸全部是数据；
"换模板不改代码"这条承诺由 `--template` 兑现（`merge_spec` 负责合并与覆盖）。

### A7 数字核验器（CLI 与函数两种用法）

```bash
python "<SKILL_DIR>/scripts/evidence_check.py" --claim "Q3 达到 82.4%" --material <材料文件>
# ok=True missing=[]  → exit 0；有缺失 → exit 1（可直接作为 CI 判据）
```

```python
import sys; sys.path.insert(0, "<SKILL_DIR>/scripts")
from evidence_check import check_claim_numbers, find_numeric_tokens
ok, missing = check_claim_numbers("Q3 达到 82.4%", open("material.md", encoding="utf-8").read())
```

### A8 示例即冒烟题集

```bash
# 只跑不回抄（验证接口，不改动包内文件）
python "<SKILL_DIR>/scripts/make_examples.py" --dry-run
# 真跑并重建 examples/output 的文本副本（会净化机器绝对路径）
python "<SKILL_DIR>/scripts/make_examples.py"
```

对拍清单在 `examples/EXPECTED-OUTPUT.md`（纯文字列出应产出的全部文件与契约字段）。
**注意**：示例是虚构材料，已标注"示例，非正式案例"，**不得冒充正式案例结果**。

### A9 契约形态与状态一致性规则

直接引用 `references/failure-modes.md` 的两张表：
§4「契约四形态」（`string→""`、`list→[]`、`dict→{}`、`bool→false`、`number→0`、禁 null）
与 §6「状态一致性」（`success`/`partial`/`failed` 各允许与禁止什么）。
这两张表**与实现解耦**，写给任何团队的"降级规范"都能用。

---

## 3. 移植到别的演示生成器（最小步骤）

1. **先立契约**：确定你的 `result.json` 顶层字段，写完 `OUTPUT_CONTRACT.md`，
   放一份 `templates/result_envelope.json`；
2. **带探针开发**：把 `references/mechanism_probe.py` 的 M1–M5 判据接到你的产物上
   （字段名不同就改探针里的取值路径，判据本身不用改）；
3. **接数字核验**：把你"页面文字 → 原文定位"的那一步换成 `check_claim_numbers`；
4. **补降级表**：照着 `failure-modes.md` 的编号方式写你自己的 D/F 规则，
   每条都指定记录字段（**没有记录 = 没执行降级**）；
5. **最后接测量台**：用 `measure_gain.py` 跑一遍，得到你自己的 Q1–Q6 基线
   —— **不要引用本包的 Δ 数字**，那是在本包案例上测的。

---

## 4. 复用边界（不适用的情况）

| 资产 | 不适用 / 需要改造 |
|-|-|
| A2 探针 | 产物里没有 `deck.slides[]` 这类结构化页级字段时需先做字段映射；M4 的 pptx 重开检查需要 python-pptx |
| A3 测量台 | 条件 B 的基线生成器是**演示场景专用**；换领域要重写 `build_baseline_deck`，否则基线不代表该领域的常见失败形态 |
| A4 角色词表 | 面向"研究材料 → 汇报"的场景；教学课件/商业提案的叙事角色不同，需替换词表 |
| A5 编辑 op | 只覆盖页面文本/备注/页序/图表引用；**不覆盖**动画、切换、SmartArt 重排 |
| A6 模板 JSON | 是"参数化模板"而非 OOXML 母版；需要真实母版时用 `spec.template_pptx`（本包只填槽位、不动母版） |
| A8 示例 | **虚构材料**，只能用于接口冒烟；任何对外材料中必须保留"示例，非正式案例"的标注 |

---

## 5. 版本与兼容

- 资产之间**没有隐式耦合**：A1/A2/A3/A9 只依赖 `result.json` 与产物目录；
  A4/A7 只依赖标准库；A5/A6 依赖 python-pptx 与 JSON。
- 探针与测量台都是**单文件脚本**，无第三方依赖（除上文写明的一处），
  可整文件拷走；如需改造，改文件内的判据/指标函数即可，不必动本包其他部分。
- 版本对齐：本包 `result.json` 的路径字段一律**相对输出目录**，
  因此探针/测量台在跨机复跑时不需要改路径逻辑（前缀不同不影响判据）。

---

## 6. 一句话总结

**本包可被拿走的不是"一个 PPT 生成器"，而是四件可独立使用的东西**：
一份**契约 + 信封**（A1/A9）、一个**判据探针**（A2）、一个**对照测量台**（A3）、
一套**页面骨架与编辑词表**（A4/A5/A6/A7/A8）。
它们共同的性质是：**判据可见、可在产物里查、可被别人的实现照做**。
