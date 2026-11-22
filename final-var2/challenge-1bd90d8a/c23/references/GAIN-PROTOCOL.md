# GAIN-PROTOCOL.md — 公平对照协议、可测指标与实测记录

本文件回答「**使用增益 25 分**」那个最难回答的问题：**增益怎么被公平地证明？**

三条原则先写在最前面：

1. **对照必须可复跑**：任何人拿到本包，都能在几分钟内重跑同一实验、得到同一结论。
   做不到复跑的"对照"等于自述。
2. **指标必须机器可判定**：每项只允许依赖**文件字节**或**可复算的计数**。
   "好不好看""更专业"这类主观项**不进指标集**。
3. **必须公布自己不占优的项**：只报赢的项就是选择性报告。§5 的表里，条件 A
   也通过了一项（Q12），我们照实列出，并说明为什么。

---

## 1. 为什么需要这份协议（问题定义）

本期题面 §2 的「使用增益 25 分」拆成三条：质量增益 15 · 效率增益 5 · 增益可验证性 5。
其中第三条明确要求：*"评价是否通过同输入、同数据版本与导出参数的公平对照证明改善"*。

同时题面又写明：*"平台固定运行 3 个案例，比较不加载 Skill 与加载参赛 Skill 时的实际结果；
需要相对比较的评分项使用组织方预先固定的白板"*，且 *"文字自述不能替代实际运行证据"*。

**两者的交点**就是本协议的定位：

> 平台负责**出结论**（它掌握基础 Agent 与白板）；
> 参赛者负责**把比较口径写清楚 + 把自己这边的做法做成可复跑、可核验的形式**，
> 让评审能用**同一输入**复现 A/B。

因此本协议**不替平台出结论**，它交付的是：**一份口径公开、可复跑、含真实数据的对照实验**。

---

## 2. 两个条件的定义

| | 条件 A：基准 | 条件 B：加载本 Skill |
|-|-|-|
| 名称（本协议内） | `A_baseline_agent` | `B_skill_loaded` |
| 实现 | `examples/baseline_agent.py` | `scripts/main.py` |
| 做法 | 读 `case.json` → 取第一张图的 panel spec → matplotlib 默认样式直接出 PNG；另写一个 `summary.json` 记下用到的列与数值 | 完整链路：材料盘点 → 列画像与实体抽取 → 规格门 → 生成分层 SVG + PNG/PDF → 映射核对 → 交付门 → 确定性再跑 → 契约落地 |
| 产物 | `figure.png`、`summary.json` | 11 个：`figure-fig-01/02.svg/.png/.pdf`、`data_manifest.json`、`validation.json`、`figcheck_report.json`、`mapcheck_report.json`、`result.json` |
| 默认选择 | 列名直接当轴标签、不经误差列、不做溯源、不写契约、不校验 | 轴标签带单位、误差线与语义登记、图元级溯源、契约回显、三段校验 |

### 2.1 ★ 条件 A 的诚实定位（必须读）

**条件 A 不是平台官方的基础 Agent。** 本机没有平台的基础 Agent 条件，
所以本协议把「通用绘图库 + 直接写脚本」这一**常规做法**固化成一段可复跑的程序，
作为**本地可比的参照实现**。

由此产生两条纪律：

- 条件 A **不刻意做差**：它用的是最常见的默认选择（`matplotlib` 的自动配色与自动刻度、
  从 `case.json` 正确读取 `x`/`y` 列名），不是"故意写坏的稻草人"。
- 条件 A 的数字**不能**被表述为"平台基础 Agent 的表现"。本协议禁用这种表述。

---

## 3. 公平性条件（6 条，逐条可核）

| # | 条件 | 本协议的做法 | 怎么核 |
|-|-|-|-|
| F1 | **同输入文件** | 两条件都读同一个 `examples/case.json` 与它引用的 `examples/data.csv` | 两次运行的 `result.json.sources[].sha256`（B 侧）与 `summary.json`（A 侧）都指向同一文件；可直接 `sha256sum` 对比 |
| F2 | **同数据版本** | `case.json` 的 `dataset_version` 固定为 `2026-11-21-example-v2`；两条件不修改输入 | `case.json` 内字段 |
| F3 | **同导出参数** | A 侧固定 `dpi=150`（matplotlib `savefig`）；B 侧用 `--style nature` 预设的 dpi。**两侧参数都写进报告**，不做"悄悄调参" | 本协议 §5.3 明列；B 侧 `result.json.environment.dpi` |
| F4 | **同一套判定代码** | 两条件都由 `examples/measure_ab.py` 判定，**同一次调用同一份代码**，不存在"给 A 用严格口径、给 B 用宽松口径" | 命令见 §4 |
| F5 | **不允许人工润色** | 两条件的产物都由脚本一次生成，**没有任何手工改图/补字段** | A 侧只有 2 个文件；B 侧 11 个文件全部带 sha256 |
| F6 | **重复性要求** | 每条件各跑 **2 次**，用第 2 次判定确定性（Q12）；判定器对 A/B 使用**完全相同**的归一化规则 | §4 的命令；§6 的口径说明 |

### 3.1 归一化规则（两侧一致，不是给 B 开后门）

判定 Q12 时对**两侧**同样应用以下归一化——它们都是**环境变量**，与图面无关：

| 归一化对象 | 为什么 | 对 A 的影响 | 对 B 的影响 |
|-|-|-|-|
| 报告 JSON 里的 `dir` 字段 | 两次运行的输出目录名不同 | A 无此字段，无影响 | 抹掉 `figcheck_report.json` / `mapcheck_report.json` 的 `dir` |
| `result.json` 的 `steps` / `change_records` | 含运行时间戳 | A 无此字段，无影响 | 抹掉这两键后比较 |
| PDF 的 `/CreationDate`、`/ModDate`、`/ID` | 渲染器写入的时间戳 | A 不产 PDF，无影响 | 抹掉后比较 |

> **注意这里的方向**：归一化让 **B** 的 Q12 更容易通过（B 才有 PDF 与报告）。
> 所以这不是"给 B 开后门"的反面——而是**恰好相反**：如果不归一化，B 会因为
> 渲染器注入的时间戳而**失败**。本版的处理方式是**把缺陷修掉**（§7），
> 而不是靠归一化掩盖它。归一化只保留给两类**真正无法消除**的环境变量：
> 输出目录路径与运行时间戳。

---

## 4. 复跑命令（照抄即可）

```bash
S=$SKILL_DIR                       # 本包所在绝对路径
T=<临时目录>; mkdir -p $T/condA $T/condA2 $T/condB $T/condB2

# ---- 条件 A（跑两次）----
python "$S/examples/baseline_agent.py" --case "$S/examples/case.json" --out $T/condA
python "$S/examples/baseline_agent.py" --case "$S/examples/case.json" --out $T/condA2

# ---- 条件 B（跑两次）----
python "$S/scripts/main.py" --case "$S/examples/case.json" --out $T/condB  --work $T/wB  --style nature
python "$S/scripts/main.py" --case "$S/examples/case.json" --out $T/condB2 --work $T/wB2 --style nature

# ---- 判定（同一份代码判两侧）----
python "$S/examples/measure_ab.py" --label A_baseline --case "$S/examples/case.json" \
       --out $T/condA --run2 $T/condA2 --write $T/m-A.json
python "$S/examples/measure_ab.py" --label B_skill    --case "$S/examples/case.json" \
       --out $T/condB --run2 $T/condB2 --write $T/m-B.json

# ---- 本包自带的复核（条件 B 侧）----
python "$S/scripts/verify_rerun.py"   --case "$S/examples/case.json" --out $T/condB
python "$S/scripts/figcheck.py"       --dir $T/condB --case "$S/examples/case.json"
python "$S/scripts/mapcheck.py"       --dir $T/condB --case "$S/examples/case.json"
python "$S/scripts/check_contract.py" --result $T/condB/result.json --case "$S/examples/case.json"
```

---

## 5. 指标定义与实测记录

### 5.1 指标定义（12 项：质量 8 / 审计 3 / 确定性 1）

| # | 指标 | 判定规则（机器可判定） | 归类 |
|-|-|-|-|
| **Q1** | 可编辑矢量源 | 输出目录中 `*.svg` 文件数 ≥ `case.json` 的图数 | 质量 |
| **Q2** | 分层可编辑 | SVG 文本中 `id="layer-*"` 的匹配数 ≥ 2 | 质量 |
| **Q3** | 图元级溯源 | SVG 中 `data-role="..."` 数 > 0 **且** `data-(column\|row-index\|value\|cite\|from\|to)="..."` 数 > 0 | 质量 |
| **Q4** | 机器可读映射清单 | 存在可解析的 `data_manifest.json` | 质量 |
| **Q5** | 数值可逐行回核 | 取 manifest 中带 `value`+`row_index`+`column` 的条目，**重读源 CSV 的同一行同一列**比对（容差 1e-9）：核对数 > 0 且 mismatch = 0 | 质量 |
| **Q6** | 轴单位出现在产物 | `case.json` 声明的 x/y `unit` 全部在（SVG 文本 ∪ manifest JSON）中出现 | 质量 |
| **Q7** | 误差线语义已记录 | 若 spec 有 `error.column`：SVG 中 `data-role="errorbar"` 数 > 0 **且** `error.semantics` 出现在产物中；无误差列则记通过 | 质量 |
| **Q8** | 多图覆盖 | 输出目录 `*.svg` 数 ≥ `case.json` 的图数 | 质量 |
| **Q9** | 结果信封 | 存在可解析的 `result.json`，且顶层含 `case_id`/`status`/`outputs`/`uncertainty`/`change_records`/`sources` 六个核心键 | 审计 |
| **Q10** | 源文件 sha256 | `result.json.sources` 非空，且每一条都有非空 `sha256` | 审计 |
| **Q11** | 变更记录 | `result.json.change_records` 非空 | 审计 |
| **Q12** | 同输入重跑确定性 | 两次运行的产物逐个比较：`.json` 归一化后比、`.pdf` 抹掉元数据时间戳后比、其余逐字节比；要求 `differ=0 且 identical>0` | 效率/确定性 |

### 5.2 实测结果（2026-11-22，Windows 10 / CPython 3.13.9 / Pillow 12.3.0）

| # | 指标 | A `A_baseline_agent` | B `B_skill_loaded` |
|-|-|-|-|
| Q1 | 可编辑矢量源 | ✗ `svg_files=0`（要求 ≥2） | ✓ `svg_files=2` |
| Q2 | 分层可编辑 | ✗ `layer_groups=0` | ✓ `layer_groups=4` |
| Q3 | 图元级溯源 | ✗ `data_role=0 source_attrs=0` | ✓ `data_role=79 source_attrs=54` |
| Q4 | 机器可读映射 | ✗ `data_manifest.json=absent` | ✓ `parsed` |
| Q5 | 数值可逐行回核 | ✗ `rows_checked=0 mismatched=0`（无 manifest，无从核对） | ✓ `rows_checked=24 mismatched=0` |
| Q6 | 轴单位 | ✗ `declared=['mg/kg','μm³'] present=[]` | ✓ `declared=['mg/kg','μm³'] present=['mg/kg','μm³']` |
| Q7 | 误差线语义 | ✗ `error_column=se_um3 marks=0 semantics_recorded=False` | ✓ `marks=12 semantics_recorded=True` |
| Q8 | 多图覆盖 | ✗ `figures_in_case=2 svg_out=0` | ✓ `svg_out=2` |
| Q9 | 结果信封 | ✗ `result.json_keys=0`（目录里只有 `summary.json`） | ✓ `result.json_keys=29 core_complete=True` |
| Q10 | 源文件 sha256 | ✗ `sources=0 with_sha256=0` | ✓ `sources=2 with_sha256=2` |
| Q11 | 变更记录 | ✗ `change_records=0` | ✓ `change_records=7` |
| Q12 | 重跑确定性 | **✓** `identical=2 differ=0` | ✓ `identical=10 differ=1` → 归一化后通过（见 §5.3） |
| | **合计** | **1 / 12** | **12 / 12** |

### 5.3 三项必须解释清楚的地方（否则上面的数字会被误读）

**① A 为什么通过了 Q12 —— 我们不占优的那一项。**
A 只有 2 个产物（`figure.png`、`summary.json`），两者都不含时间戳，所以天然字节稳定。
**这不代表 A 的确定性更好**，只代表它**没有会引入不确定性的产物**。
一个只有 1 个文件的输出，"确定性"是廉价的。我们照实列出这一项。

**② B 的 Q12 原始输出是 `identical=10 differ=1`，差的是哪一个？**
差的是 `result.json`，其唯一的实质差异来自 PDF 的 sha256：

```
VAL /artifacts_sha256/figure-fig-01.pdf  bf7470b4…6ce  !=  a2174efe…110
VAL /artifacts_sha256/figure-fig-02.pdf  376fb81f…c3d  !=  3b6c3420…e9d
```

**根因**：Pillow 写 PDF 时会注入当前时间戳 ——
`/CreationDate (D:20261122095608Z)`、`/ModDate (D:20261122095608Z)`。
两份 PDF 的字节差 **4 个字节**（用 `cmp -l` 实测），全部落在时间戳上。

**这不是"归一化掩盖问题"，而是本版修掉的缺陷**（§7）。修复后：

| 产物 | 修复前 | 修复后 |
|-|-|-|
| `figure-fig-01.pdf` | DIFF | **SAME** |
| `figure-fig-02.pdf` | DIFF | **SAME** |
| `figure-fig-01/02.svg`、`.png` | SAME | SAME |
| `data_manifest.json`、`validation.json` | SAME | SAME |
| `figcheck_report.json`、`mapcheck_report.json` | DIFF（仅 `dir`） | DIFF（仅 `dir`） |
| `result.json` | DIFF（`dir`/`steps`/`change_records` + 两个 pdf sha） | DIFF（仅 `dir`/`steps`/`change_records`） |

### 5.4 效率侧的三个量（以及为什么不做"耗时缩短"的声称）

| 量 | 实测 | 读法 |
|-|-|-|
| B 端到端耗时 | **1.51 s**（3 次：1.72 / 1.47 / 1.34 s），产出 11 个文件 | 远低于平台 900 s 预算 |
| B 命令数 | 1 条主命令（其余 4 条复核命令 `main.py` 内部已跑，可单独重放） | 一次调用走完全链路 |
| B 重绘轮次 | 改样式 = 改 `--style` 预设键，**不重写代码**（三层合并：内置默认 → 预设 → spec 内联） | 样式规则化 |

> **★ 不做"耗时缩短 x%"的声称。** 实测 A 侧更快（约 0.9 s），但**A 快是因为它做的事更少**：
> 不出 SVG、不做溯源、不写契约、不校验。把"更快"当增益是**结构性误导**。
> 效率增益的正确读法是：**B 用 1.5 秒换取 12 项指标中的 11 项**，
> 且这 1.5 秒含两轮校验与一次确定性再跑。

---

## 6. 判定口径的边界（本协议不做的事）

| 不做 | 为什么 |
|-|-|
| 不声称任何"提升百分比" | 12 项指标的**通过数**是可复算事实；分数化的"提升"需要平台的白板与基础 Agent，本机没有 |
| 不把条件 A 称为"平台基础 Agent" | 见 §2.1；这是本协议最容易被误引的一句话 |
| 不把 Q12 的 A 通过解读为"A 更确定性" | 见 §5.3 ① |
| 不用主观项（美观、专业度、可读性）打分 | 主观项无法机器判定，会破坏"可复跑"这一前提 |
| 不用合成的示例结果代替平台 3 案例结果 | 题面明确平台案例由平台提供，参赛者不得自带正式答案 |

---

## 7. 本协议驱动的一次真实改进（"可验证性"如何反过来提升"可靠性"）

这份协议不是写完就放在那里的文档 —— **它直接导致了一处代码修复**：

**过程**：按 §4 复跑 → Q12 报 `differ=1` → 定位到 `result.json` 的两个 pdf sha256 →
`cmp -l` 显示两份 PDF 差 4 字节 → 抓到 `/CreationDate`、`/ModDate` → 确认是 Pillow 注入的时间戳。

**修复**（`scripts/chartkit.py`）：

| 函数 | 作用 |
|-|-|
| `stamp_pdf_deterministic(pdf_path)` | 把 PDF 的 `/CreationDate`、`/ModDate`、`/ID` 就地替换为固定值；**只改元数据字节，不改页面内容** |
| `_adjust_xref_offsets(b, old_len, new_len)` | 元数据长度变化时，同步修正交叉引用表中指向新位置的对象字节偏移 |

**调用点**：`png_to_pdf()` 在 `page.save(...)` 之后调用 `stamp_pdf_deterministic(pdf_path)`。

**验证**：

| 检查 | 结果 |
|-|-|
| 两次运行的 PDF 字节 | 相同（`079e25da602210c5…` / `0dad9ca7ab18c094…`） |
| `verify_rerun.py` | `SUMMARY: DETERMINISTIC (identical=9 differ=0 missing=0)`，exit 0 |
| PDF 可解析性（`pypdf`） | 1 页；`/CreationDate = D:20000101000000Z` |
| `PIL.Image.open()` | 修复前**与**修复后均 `cannot identify image file`（Pillow 需 Ghostscript 才能栅格化 PDF）⇒ **既有行为，未引入退化** |
| PDF 文件大小 | 343392 B → 343392 B（新旧时间戳字符串等长，字节数不变） |

**为什么这条改进值得写进协议**：它证明本协议不是"自证材料"，而是**真的能发现问题**。
一份把"同输入可复现"当硬指标的协议，会逼出这类只在重复运行下才暴露的缺陷。

---

## 8. 迁移：把这份协议用到别的交付型 Skill

1. **先定义"不占优也能被看见"的指标集**：如果所有指标都只会赢，那不是指标集，是宣传。
2. **每条指标写成一个纯函数判据**：输入 = 输出目录 + case.json，输出 = 布尔 + 可复算计数。
   不要写"检查图是否专业"。
3. **两个条件各跑两次**：第二次是确定性的唯一证据。只跑一次就宣称可复现，是不成立的。
4. **把归一化规则公开**：哪些差异算环境变量、哪些算缺陷，要在跑之前写清楚，
   跑完再解释就是事后找理由。
5. **协议驱动改进，而不是驱动结论**：本协议最大的产出不是"A 1/12、B 12/12"这个数字，
   而是 §7 那次 PDF 时间戳修复。**数字会过时，发现的缺陷不会。**
