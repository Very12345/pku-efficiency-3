# REFINEMENT-NOTES.md — 本版相对基线的逐条增改（可 diff 验证）

**本版 = 决策显性化版**（`v1`）。起点是 `work/efficiency-3/final/challenge-1bd90d8a/`
（已投出的合规基线包），本文件逐条列出**改了什么、为什么改、怎么自己验**。

> 本文件**不是**"变更记录/补注"式的尾巴注释 —— 每条改动都落在**具体文件的
> 具体段落**上，并且都能用一条命令复核。若有任何一条你复核不成立，请以复核结果为准。

---

## 0. 增改总览

| # | 类型 | 落点 | 性质 |
|-|-|-|-|
| 1 | 结构重写 | `SKILL.md` | 正文按"决策显性化"语境重写；执行链路重编号为 S0–S7；决策规则由 D1–D18 重组为 **D1–D16**（合并/去重、补全"触发条件 → 动作 → 失败降级 → 落痕字段"四段式）；新增 §5.1 决策优先级 |
| 2 | 新增章节 | `SKILL.md` §6 | 失败分支表按 **FM-M / FM-D / FM-R / FM-E / FM-C / FM-X 六族、41 条分支**重排（原为一张 13 行的单表） |
| 3 | 结构重写 | `references/failure-modes.md` | 由"七类散表"重排为与 `SKILL.md` §6 **编号一一对应**的六族体系；每条补"触发条件"与"落痕字段"两列；新增复验命令段 |
| 4 | 结构重写 | `references/RUBRIC_MAP.md` | 五维逐个重写；可靠体验一节展开为**六族 41 条**的逐族对照 + 官方点名五类情形的落点索引 |
| 5 | 新增文件 | `README.md` | 新增参数表（§2.1，10 个参数）、**退出码语义表**（§2.2，6 个脚本）、设计三不变量（§3）、维护表（§5） |
| 6 | 新增文件 | `TEST.md` | 8 组真机实测 + 5 条未解决项（含一条**实测发现的真实缺口**） |
| 7 | 新增文件 | `REFINEMENT-NOTES.md` | 本文件 |
| 8 | **代码修复** | `scripts/chartkit.py` | 新增 `stamp_pdf_deterministic()` + `_adjust_xref_offsets()`；`png_to_pdf()` 落盘后调用它 → 修掉 PDF 时间戳导致的**确定性缺陷** |
| 9 | 新增文件 | `examples/baseline_agent.py` | 基准条件（不加载 Skill）的可复跑参照实现，供对照实验使用 |
| 10 | 新增文件 | `examples/measure_ab.py` | A/B 度量工具（12 项机器可判定指标） |
| 11 | 新增 | `examples/README.md` §5 | 说明"零二进制"约束与基线脚本的定位 |
| 12 | 重写 | `GITHUB_URL.txt` | 指向本变体目录（单行） |

---

## 1. 质检清单：为什么决策规则从 D1–D18 变成 D1–D16

不是"删了两条"，而是**去重与合并**，并给每条补齐四段式结构。对照：

| 基线 | 本版 | 变化 |
|-|-|-|
| D1 数据到图元绑定 | **D1** | 补齐"触发条件"与"落痕字段" |
| D2 量级与单位 | **D2** | 拆成"轴标签"与"刻度范围"两个触发检查点 |
| D3 图例-系列对应 | **D3** | 补降级动作（"修 spec 后重跑"）与阻断语义 |
| D4 科学实体命名 | **D4** | 补"失败时保留原文 + uncertain" |
| D5 中文字体 | **D5** | 补"SVG 走回退链、PNG 记 warn"的分工 |
| D6 显著性标注 | **D6** | 补"源未给 p 值则不画"这一条降级（基线未写） |
| D7 可编辑性 | **D7** | 补"保 SVG 先落盘" |
| D8 误差线语义 | **D8** | 补"源未标语义就记 uncertainty，不猜" |
| D9 空值/缺失 | **D9** | 同 |
| D10 部分结果 | **D10** | 提升为**兜底规则**（表外岔路的统一出口） |
| D11 版本与变更 | **D11** | 同 |
| D12 公平对照 | **D12** | 补"出现字节差异必须定位随机源，不得用'看起来一样'搪塞" |
| D13 遮挡与图例越界 | **D13** | 补"调整后仍重叠则记 warn" |
| —— | **D14（新）** | `task.md` 缺失 / case 与 task 冲突时的裁决规则（基线**没有**这条；实际运行会碰到） |
| D15 契约四形态 | **D15** | 同（编号后移） |
| D16 状态一致性 | **D16** | 同（编号后移） |
| D17 样式规则化 | 并入 `README.md` §5 维护表 | 它讲的是"改样式去哪儿改"，属使用说明，不属执行时岔路 |
| D18 再跑证据 | 并入 **D12** 与 **FM-E6/E7** | 「重跑验证」是 D12（公平对照）的执行手段；具体差异的分支处置归 FM-E6（时间戳）与 FM-E7（其他随机源） |

**净结果**：执行链路上的岔路 16 条，条条四段式；D17 去使用说明、D18 拆进 D12+FM-E。

---

## 2. 逐条改动与复核方式

### 2.1 `SKILL.md`

```bash
diff -u <基线>/SKILL.md <本包>/SKILL.md | head -200
```
预期看到：§4 的 S0–S7（含每个 CP 的"判定"小节）、§5 决策规则表、
§5.1 决策优先级、§6 六族失败分支表、§8 自查清单（10 项）、§10 限制（6 条）。

> **不变量（故意没动）**：YAML frontmatter 的 `name: scientific-figure-craft`；
> 所有命令示例的形式（`python "$SKILL_DIR/scripts/<script>.py" --<arg> …`）；
> 脚本名与 CLI 参数名。**算法与接口一字未改。**

### 2.2 `references/failure-modes.md`

```bash
# 六族分布（实测）
for f in M D R E C X; do
  printf "FM-%s: %s
" "$f" "$(grep -o "FM-$f[0-9]*" <本包>/references/failure-modes.md | sort -u | wc -l)"
done
# SKILL.md 与 failure-modes.md 的编号必须完全一致（期望空输出）
comm -3 <(grep -o 'FM-[MDREXC][0-9]*' <本包>/SKILL.md | sort -u)         <(grep -o 'FM-[MDREXC][0-9]*' <本包>/references/failure-modes.md | sort -u)
```
实测六族分布（**共 41 条编号**）：
FM-M **6** / FM-D **7** / FM-R **7** / FM-E **9** / FM-C **5** / FM-X **7**。
`SKILL.md` §6 速查表收录 **37 条**（主干高频项），§6.7 补录另 **4 条**
（FM-E9 / FM-X4 / FM-X5 / FM-X6 / FM-X7 五条中，FM-X4..X7 与 FM-E9 归入补充，
速查表原有 FM-X1..X3）—— 两处相加为 41，**编号集合完全一致**（上面的 `comm -3` 实测为空）。

**编号一致性自查结论（实测）**：`comm -3` 对拍 `SKILL.md` 与
`references/failure-modes.md` 的 FM 编号集合，**输出为空**，即两处编号一一对应。

### 2.3 `scripts/chartkit.py`（唯一的代码改动）

```bash
grep -n "stamp_pdf_deterministic\|_adjust_xref_offsets" <本包>/scripts/chartkit.py
```

**改的是什么**：`png_to_pdf()` 在 `page.save(...)` 之后多调用一次
`stamp_pdf_deterministic(pdf_path)`。该函数把 PDF 里的
`/CreationDate`、`/ModDate`、`/ID` 就地替换为固定值，并调用
`_adjust_xref_offsets()` 同步修正交叉引用表中指向新位置的对象字节偏移。
**只改元数据字节，不改页面内容；不改任何 CLI 参数、不改任何函数签名。**

**为什么必须改（实测，不是推测）**：

| | 修复前 | 修复后 |
|-|-|-|
| 两次运行 `figure-fig-01.pdf` 的 sha256 | **不同** | **相同** |
| 两次运行 `figure-fig-02.pdf` 的 sha256 | **不同** | **相同** |
| `result.json.artifacts_sha256` 的 pdf 条目 | 随之不同 | 随之相同 |
| `verify_rerun.py` | 报 pdf 差异 | `SUMMARY: DETERMINISTIC (identical=9 differ=0)` |

对"结果可核验性 5 分"的意义：交付件 sha256 只有在**同输入可复现**时才构成证据；
修复前 pdf 的 sha256 是随运行时间变化的，作为证据是无效的。

复核命令（在包外临时目录）：
```bash
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out $TMP/a --style nature
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out $TMP/b --style nature
python "$SKILL_DIR/scripts/verify_rerun.py" --case "$SKILL_DIR/examples/case.json" --out $TMP/a
# 期望最后一行：SUMMARY: DETERMINISTIC (identical=9 differ=0 missing=0)
```

### 2.4 `examples/`

新增两个**可复跑**的对照工具（都是纯文本 `.py`，符合资源形态硬门）：

| 文件 | 作用 | 与正式案例的关系 |
|-|-|-|
| `examples/baseline_agent.py` | 基准条件（不加载 Skill）的常规做法参照实现：读 `case.json` → matplotlib 直接出 PNG + `summary.json` | **不参与评分**，只用于本地对照度量；它读的是 `examples/case.json`（合成示例），不是平台案例 |
| `examples/measure_ab.py` | 12 项机器可判定指标的度量器（质量 8 项 + 审计 3 项 + 确定性 1 项），对任意输出目录打分 | 同上 |

两者都**不产出也不可能被误当"预制答案"**：它们输出的是自拟合成案例上的图与指标 JSON。

---

## 3. 本版**没有**改的东西（避免误伤）

- **算法**：`chartkit.py` 的 `Scene` 构建、SVG 生成、八类校验逻辑、图型推断 —— 一字未动。
- **CLI 接口**：`main.py` 的 10 个参数、其余 9 个脚本的参数名与退出码语义 —— 一字未动。
- **`references/OUTPUT_CONTRACT.md`**：字段块**逐字保留**（`REQUIRED-FIELDS` 的 18 个字段名、
  G1–G8 判定表、四形态规则、别名映射表、各产物 JSON 示例）。本版在该文件上**零改动**。
- **`templates/*.json`**：四个模板文件逐字节相同。
- **`examples/` 的输入文件**（`case.json` / `data.csv` / `entities.json` / `material.md` /
  `task.md`）与 `examples/output/` 的 5 个契约 JSON —— 逐字节相同。

复核命令：
```bash
# 契约与模板、示例输入应当逐字节相同（0 行输出 = 相同）
for f in references/OUTPUT_CONTRACT.md templates/*.json examples/*.md examples/*.csv \
         examples/*.json examples/output/*.json; do
  diff -q "<基线>/$f" "<本包>/$f" || echo "DIFFERS: $f"
done
```

---

## 4. 迁移建议（这套做法怎么用到别的交付型 Skill）

1. **先列岔路，再写规则**：把流程里"遇到 A 就做 B，做不成怎么办"全部写出来，
   每条补上**落痕字段**——没有落痕的规则等于没写。
2. **失败按来源分族编号**：族号让 `result.json` 的读者一眼定位失败来源；
   编号要在 SKILL 与 references 之间**一致**，否则文档会互相矛盾。
3. **把"阻断"和"降级"分开**：涉及"图上写了什么"的失败（图例错配、显著性缺配对）
   应当**阻断** `completed`；涉及"能力不足"的失败（缺字体、缺 Pillow）应当**降级**并留痕。
4. **确定性要当成可核验性的一部分**：交付件的 sha256 只有在同输入可复现时才有意义。
   本包的教训是：**渲染器自身会往产物里写时间戳**（PDF 的 `/CreationDate`），
   不处理它，`artifacts_sha256` 就不是证据。
