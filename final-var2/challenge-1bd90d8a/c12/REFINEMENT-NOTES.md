# REFINEMENT-NOTES.md — 本版相对基线的逐条增改（可 diff 验证）

**本版 = 增益可验证版**（`v2`）。起点是 `work/efficiency-3/final/challenge-1bd90d8a/`
（已投出的合规基线包），本文件逐条列出改了什么、为什么改、怎么自己验。

> 本文件**不是**"变更记录/补注"式的尾巴注释 —— 每条改动都落在**具体文件的具体段落**
> 上，且都能用一条命令复核。任何一条复核不成立，请以复核结果为准。

---

## 0. 增改总览

| # | 类型 | 落点 | 性质 |
|-|-|-|-|
| 1 | **新增核心文件** | `references/GAIN-PROTOCOL.md` | ★ 本版主件：公平对照协议（6 条公平性条件 + 归一化规则 + 边界声明）+ 12 项指标定义 + 实测记录 + 迁移建议 |
| 2 | **新增工具** | `examples/baseline_agent.py` | 条件 A（基准做法）的可复跑参照实现 |
| 3 | **新增工具** | `examples/measure_ab.py` | 12 项指标的 A/B 度量器（同一份代码判两侧） |
| 4 | 结构重写 | `SKILL.md` | 正文按"增益可验证"语境重写：新增 §0（核心主张与证据边界）、执行链路重编号为**阶段 G0–G8**（每阶段有进入/退出条件）、决策规则重组为**规则 R1–R14**（每条挂一个可测后果）、失败分支按"打击哪项指标"归类、新增 §7 实测增益 |
| 5 | 结构重写 | `references/failure-modes.md` | 由"七类散表"重排为 **F-A..F-G 七组、49 条分支**，分组依据 = 它打击哪一项指标；每条补触发条件与落痕字段 |
| 6 | 结构重写 | `references/RUBRIC_MAP.md` | 五维逐个重写；**使用增益一节展开为三行逐点对照并指向 GAIN-PROTOCOL**；新增"指标表 ↔ 代码指标集逐条对应"的自查项 |
| 7 | 新增文件 | `README.md` | 依赖（新增 matplotlib 仅为条件 A 需要）、参数表、退出码表、设计三不变量、**对照实验入口表**、维护表（含"指标一致性铁律"） |
| 8 | 新增文件 | `TEST.md` | 9 组真机实测 + 6 条未解决项，含 **T5 完整 A/B 表**与 **T6 确定性缺陷的发现与修复全过程** |
| 9 | 新增文件 | `REFINEMENT-NOTES.md` | 本文件 |
| 10 | **代码修复** | `scripts/chartkit.py` | 新增 `stamp_pdf_deterministic()` + `_adjust_xref_offsets()`；`png_to_pdf()` 落盘后调用 → 修掉 PDF 时间戳导致的确定性缺陷（**由本版的对照实验发现**） |
| 11 | 新增段落 | `examples/README.md` §5 | 说明两个对照工具的角色、跑法与三条使用纪律 |
| 12 | 重写 | `GITHUB_URL.txt` | 指向本变体目录（单行） |

---

## 1. 本版为什么"值得单独存在"（与"加一段话"的区别）

判断一个变体是否合格，标准是：**它的强化是否沿某个评分维度做出了实质内容增改。**
本版的强化对象是「使用增益 25 分」，具体成立方式：

| 判断项 | 本版的情况 |
|-|-|
| 是否新增了**协议**（不是描述） | 是：`GAIN-PROTOCOL.md` 给出 6 条公平性条件、归一化规则、12 项指标的逐项判定规则 |
| 是否新增了**可跑的工具** | 是：`baseline_agent.py`（条件 A）+ `measure_ab.py`（判定器），两者都进包且能跑 |
| 是否有**真实数据**（不是编的） | 是：A 1/12、B 12/12 逐项数字，全部可由 §4 的命令复跑得到 |
| 是否**公布自己不占优的项** | 是：Q12 上条件 A 通过、B 修复前不通过；`GAIN-PROTOCOL.md` §5.3① 专门解释这一项 |
| 是否**驱动了实际改进** | 是：对照实验发现 PDF 时间戳缺陷 → 修复 → 交付件 sha256 才具备证据力（§3） |
| 是否只是"追加注释段" | **不是**：`SKILL.md` 是重编号重组织的正文，`failure-modes.md` 是重分组重写的全表 |

---

## 2. 逐条改动与复核方式

### 2.1 `references/GAIN-PROTOCOL.md`（新增，本版主件）

```bash
test -f <本包>/references/GAIN-PROTOCOL.md && echo present
grep -c '^| \*\*Q' <本包>/references/GAIN-PROTOCOL.md      # 12 项指标定义
```

文件结构：§1 问题定义 → §2 两条件定义（含 §2.1 条件 A 的诚实定位）→ §3 公平性条件
（F1–F6 + §3.1 归一化规则）→ §4 复跑命令 → §5 指标定义 + 实测 + §5.3 三项必须解释的地方
+ §5.4 效率侧 → §6 判定口径的边界（本协议不做的事）→ §7 由协议驱动的真实改进
→ §8 迁移建议。

### 2.2 `examples/baseline_agent.py` + `examples/measure_ab.py`（新增工具）

```bash
python -m py_compile <本包>/examples/baseline_agent.py <本包>/examples/measure_ab.py   # exit 0
python <本包>/examples/baseline_agent.py --case <本包>/examples/case.json --out $T/condA
python <本包>/examples/measure_ab.py --label A --case <本包>/examples/case.json --out $T/condA
```

**两个工具都不参与评分**：它们读的是包内**合成示例**（`examples/case.json`），
不接触平台案例；产出的是自拟案例上的图与指标 JSON，不可能被误当"预制答案"。

### 2.3 `scripts/chartkit.py`（唯一代码改动）

```bash
grep -n "stamp_pdf_deterministic\|_adjust_xref_offsets" <本包>/scripts/chartkit.py
```

**改的是什么**：`png_to_pdf()` 在 `page.save(...)` 之后多调用一次
`stamp_pdf_deterministic(pdf_path)`；该函数把 PDF 的 `/CreationDate`、`/ModDate`、`/ID`
就地替换为固定值，并调用 `_adjust_xref_offsets()` 同步修正 xref 中指向新位置的对象字节偏移。
**只改元数据字节、不改页面内容；不改任何 CLI 参数、不改任何函数签名。**

**怎么发现的**（这条比改动本身重要）：本版的对照实验要求"每条件跑两次"（§3 条件 F6），
于是 Q12 报出 `differ=1` → 定位到 `result.json` 的两个 pdf sha256 → `cmp -l` 显示两份 PDF
差 **4 字节** → 抓到时间戳。**如果协议不要求跑第二次，这个缺陷不会被发现。**

**实测对照**：

| | 修复前 | 修复后 |
|-|-|-|
| 两次运行 `figure-fig-01.pdf` sha256 | 不同 | **相同**（`079e25da602210c5…`） |
| 两次运行 `figure-fig-02.pdf` sha256 | 不同 | **相同**（`0dad9ca7ab18c094…`） |
| `result.json.artifacts_sha256` 的 pdf 条目 | 随之不同 | 随之相同 |
| `verify_rerun.py` | 报 pdf 差异 | `SUMMARY: DETERMINISTIC (identical=9 differ=0 missing=0)` |
| PDF 文件大小 | 343392 B | 343392 B（新旧时间戳等长） |
| PDF 可解析性（`pypdf`） | 1 页 | 1 页；`/CreationDate = D:20000101000000Z` |

### 2.4 `SKILL.md`

```bash
diff -u <基线>/SKILL.md <本包>/SKILL.md | head -200
```
预期看到：§0 核心主张与证据边界（含 3 条证据边界）、§4 阶段表 G0–G8（含进入/退出条件）、
§4.2 参数表、§5 规则表 R1–R14（每条带"对应指标"与"若不做指标会怎样"）、
§5.1 规则优先级、§6 失败分支六类（按指标归类）、§7 实测增益（含 A 通过的 Q12）、
§8 检查清单与限制。

> **不变量（故意没动）**：YAML frontmatter 的 `name: scientific-figure-craft`；
> 所有命令示例的形式；脚本名与 CLI 参数名。**算法与接口一字未改。**

### 2.5 `references/failure-modes.md`

```bash
for g in A B C D E F G; do printf "F-%s: %s\n" "$g" "$(grep -o "F-$g[0-9]*" <本包>/references/failure-modes.md | sort -u | wc -l)"; done
# 实测 F-A 4 / F-B 7 / F-C 3 / F-D 10 / F-E 8 / F-F 5 / F-G 12 = 49 条编号
```

分组依据 = **它打击哪一项指标**（F-A→Q1/Q2、F-B→Q3/Q4/Q5、F-C→Q6、F-D→Q7/Q8、
F-E→Q9/Q10/Q11、F-F→Q12、F-G 横切）。这与"按错误类型分组"的写法不同，
是本版定位的直接体现。

---

## 3. 本版**没有**改的东西（避免误伤）

- **算法**：`chartkit.py` 的 `Scene` 构建、SVG 生成、八类校验逻辑、图型推断 —— 一字未动。
- **CLI 接口**：`main.py` 的 10 个参数、其余 9 个脚本的参数名与退出码语义 —— 一字未动。
- **`references/OUTPUT_CONTRACT.md`**：字段块**逐字保留**（`REQUIRED-FIELDS` 的 18 个字段名、
  G1–G8 判定表、四形态规则、别名映射表、各产物 JSON 示例）。本版在该文件上**零改动**。
- **`templates/*.json`**：四个模板逐字节相同。
- **`examples/` 的输入文件与 `examples/output/` 的 5 个契约 JSON**：逐字节相同。

```bash
# 应当无输出（= 逐字节相同）
for f in references/OUTPUT_CONTRACT.md templates/*.json examples/*.md examples/*.csv \
         examples/*.json examples/output/*.json; do
  diff -q "<基线>/$f" "<本包>/$f" || echo "DIFFERS: $f"
done
```

---

## 4. 迁移建议

1. **先定义"不占优也能被看见"的指标集**：如果所有指标都只会赢，那不是指标集，是宣传。
2. **每条指标写成一个纯函数判据**：输入 = 输出目录 + case.json，输出 = 布尔 + 可复算计数。
3. **两个条件各跑两次**：第二次是确定性的唯一证据。本版的 PDF 缺陷就是靠第二次跑出来的。
4. **把归一化规则公开**：哪些差异算环境变量、哪些算缺陷，要在跑之前写清楚；
   跑完再解释就是事后找理由。并且要说明**归一化的方向性**（本版给 B 归一化的地方更多，
   因此 §3.1 专门说明这不是开后门，而是缺陷已另行修掉）。
5. **协议驱动改进，而不是驱动结论**：本版最大的产出不是"A 1/12、B 12/12"，
   而是那次 PDF 时间戳修复。**数字会过时，发现的缺陷不会。**
