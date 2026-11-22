# MECHANISM.md — 机制、增益、复用与增改（合并自四份专题文档）

> **为什么合成一份**：交付包有 **50 文件上限**，而"机制/增益/复用/增改"这四件事本来讲的是
> 同一条链条 —— *机制为什么成立 → 增益怎么被测量 → 别人怎么拿走 → 相对基线改了什么*。
> 合并只动**编排**，**不动任何一条实质内容**，四部分各自保留原来的小节编号与表格。
>
> | 原文档 | 在本文件的哪一部分 |
> |-|-|
> | `references/MECHANISM.md` 第一部分（机制与边界） | **第一部分** |
> | `references/MECHANISM.md` 第一部分 第二部分 + `references/MECHANISM.md` 第二部分附节（增益协议与对照方案） | **第二部分** |
> | `references/MECHANISM.md` 第一部分 第三部分（可复用资产与路径） | **第三部分** |
> | `references/MECHANISM.md` 第四部分（相对基线的逐条增改） | **第四部分** |
>
> 四部分全文照搬，只把各自的一级标题降为二级标题。

---

## 第一部分 · 机制：本包凭什么不一样，以及"没有它会怎样"

# MECHANISM.md — 本包的独特机制，以及"没有它会怎样"

本文件回答「**创新增益 15 分**」与「**生态贡献 10 分**」最容易被含糊带过的两个问题：

1. **本包相对常规做法（通用绘图库、现成模板、一次性脚本）到底有什么不一样？**
2. **如果拿掉这个机制，具体会发生什么坏事？** —— 说不清第二问的"创新"只是功能罗列。

本文件按四个机制逐条回答，每个机制都给出：**它是什么 → 常规做法是什么 →
没有它会怎样（具体症状）→ 本包的实现落点 → 怎么复验**。

---

## 0. 一句话概括本包的机制主张

> 常规做法把"图"当**输出**；本包把"图"当**可回溯的证据**。
> 因此每个图元都必须带着回到源数据的钥匙，且这个"钥匙链"由程序闭合、由门禁判定，
> 而不是靠人目视确认。

这条主张展开就是下面四个机制 —— 它们是**互相咬合的一套**，不是四个独立功能。

---

## 1. 机制一：**三向闭合**（SVG ↔ manifest ↔ 源表值）

### 1.1 它是什么

同一份数据在三个地方各有一份表示：

| 位置 | 表示 | 谁写它 |
|-|-|-|
| SVG 的图元元素 | `data-role` / `data-column` / `data-row-index` / `data-value` / `data-cite` | 渲染引擎 `chartkit.py` |
| `data_manifest.json` | `{svg_id, role, source:{column,row_index,value,…}}` | 渲染引擎 |
| 源数据表 | 真实的 CSV/TSV/JSON 行 | 案例提供方（**本包不改**） |

**三向闭合 = 三处互为索引，且第三处由程序重读核对**：
① manifest 里登记的每个 `svg_id` 必须在 SVG 里存在；
② SVG 数据层里的每个图元必须在 manifest 里登记；
③ manifest 里 `column + row_index + value` 必须与**重读源表**得到的值一致（容差 1e-9）。

### 1.2 常规做法是什么

直接画：把数值读进内存 → 交给绘图库 → 出图。
图上没有任何回到源数据的线索，`manifest` 这个概念根本不存在。

### 1.3 没有它会怎样（具体症状，逐条可辩）

| 症状 | 为什么必然发生 |
|-|-|
| **"这根柱子的数字是哪个文件的哪一行？"回答不了** | 图元与数据之间没有任何持久化的索引；只能靠当时的脚本反推 |
| **列错位不会被发现** | 如果脚本把 `se_um3` 当成 `mean_um3` 画，图面完全正常（同类量级也不一定差很远），没有任何机制会报警 |
| **数据版本换了一版，图没更新也看不出来** | 图与数据之间没有版本绑定；`sha256` 无处比对 |
| **返修时只能重画** | 找不到"哪个图元对应哪一行"，就无法做定点修改 |
| **多面板/多图时错位风险成倍** | 每个 panel 各自一次"读-画"，没有共用的映射层 |

### 1.4 本包的实现落点

| 落点 | 文件 / 函数 |
|-|-|
| 图元写溯源属性 | `scripts/chartkit.py`（`Scene` 元素生成处） |
| 生成 manifest | `scripts/chartkit.py`（`export_figure` 汇总） |
| 三向核对（含重读源表） | `scripts/mapcheck.py` |
| 门禁 | G3（图元数 1:1）· G4（每个数据图元至少一条源定位）· **G5 的 Q5 判定** |

### 1.5 怎么复验

```bash
python "$SKILL_DIR/scripts/mapcheck.py" --dir <out> --case <case.json>
# 期望：SUMMARY: ALL PASS (121 checked / 0 mismatched / 0 unmatched)
# 选一行手工反查：
grep -o 'data-column="[^"]*" data-row-index="[0-9]*" data-value="[^"]*"' <out>/figure-*.svg | head -1
# 再用该 column/row_index 去源 CSV 取值，应当逐位相同（容差 1e-9）
```

> **实测**：示例案例上 `121 checked / 0 mismatched / 0 unmatched`；其中 24 条带
> `value` 的条目被 `examples/measure_ab.py` 的 Q5 再次重读源表核对，`mismatched=0`。

---

## 2. 机制二：**声明式规格 + 生成门**（先校验能不能画，再画）

### 2.1 它是什么

图不是"写代码画出来"的，而是**先写一份声明式规格**（`case.json` 的 `figures[]`
或独立的 `figure_spec.json`，结构见 `templates/figure_map.schema.json`），
再由引擎解释这份规格去画。规格在进入渲染**之前**先过一道结构校验（生成门）：
图型是否受支持、必需的列引用是否存在、误差线语义是否常规、显著性的锚点与来源是否齐、
网络边是否悬空。**门不过就不进渲染。**

### 2.2 常规做法是什么

直接写绘图代码。参数散在代码里，改一次样式要改代码；出错是在渲染时或渲染后才发现。

### 2.3 没有它会怎样

| 症状 | 为什么 |
|-|-|
| **错误在渲染阶段才爆** | 画到一半发现列名不对，前面的计算白做；多图时更浪费 |
| **样式无法复用** | 字号/线宽/配色写在代码里，"下一个案例套用上次的样式"要手工抄 |
| **规格无法被别人接手** | 别人要复现你的图，必须读你的代码；而规格是可读、可 diff、可参数化的 |
| **同一份数据换图型 = 重写脚本** | 声明式的好处正是"换 `type` 即可"，命令式做不到 |

### 2.4 本包的实现落点

| 落点 | 文件 |
|-|-|
| 规格契约（含每种图型的特有字段） | `templates/figure_map.schema.json`；`references/OUTPUT_CONTRACT.md` §6 |
| 生成门（E1–E10） | `scripts/spec_lint.py`（**exit 2 = 有 error，不得进入生成**） |
| 规格解释器 | `scripts/chartkit.py`（含 `type: auto` 的自动推断） |
| 样式三层合并 | 内置默认 → `templates/journal_styles.json` 预设 → spec 内联键（**加新期刊 = 加一个键，不改代码**） |

### 2.5 怎么复验

```bash
# 门能拦住：未知图型
echo '{"figures":[{"id":"x","type":"waterfall"}]}' > /tmp/bad.json
python "$SKILL_DIR/scripts/spec_lint.py" --spec /tmp/bad.json     # exit 2, [ERROR] E1

# 换样式不改代码：
python "$SKILL_DIR/scripts/main.py" --case <case> --out <out1> --style default
python "$SKILL_DIR/scripts/main.py" --case <case> --out <out2> --style cell
```

> **已知边界（实测，不掩饰）**：`spec_lint.py` 能拦住"未知图型"，但**拦不住
> "引用了不存在的列"**（实测返回 `SUMMARY: VALID`、exit 0）。因此"生成门"不是唯一防线 ——
> 机制一的三向核对才是兜底（列不存在必然 mismatch）。这条边界写在
> `references/failure-modes.md` 与 `TEST.md` 的未解决项里。

---

## 3. 机制三：**单一场景双端输出**（矢量源与位图预览不可能不一致）

### 3.1 它是什么

渲染时先构造一个**与输出格式无关的中间场景** `Scene`（一组带坐标、样式、溯源属性的
图元），然后由同一个 `Scene` 分别导出：

- 手写 XML 的**分层 SVG**（矢量、可编辑、文字是真实 `<text>`）；
- 用 Pillow 栅格化的 **PNG**；
- 把 PNG 嵌入的 **PDF** 预览。

三种产物**逐元素同源**。

### 3.2 常规做法是什么

两条独立路径：matplotlib 出 PNG/PDF，另一条路径（或手工导出）出 SVG。
或者干脆只出位图。

### 3.3 没有它会怎样

| 症状 | 为什么 |
|-|-|
| **矢量和位图不一致** | 两条路径各自的字体、坐标取整、裁剪行为不同，同一份数据能画出"看起来不同"的两张图；评审不知道以哪张为准 |
| **PNG 好看但 SVG 不可编辑** | 常见做法是把文字转曲（保证字体不错位），结果图再也改不了字 |
| **改一处要改两处** | 修复只在一条路径上做了，另一条路径仍带缺陷，且没人会发现 |
| **文字转曲 = 丢失可编辑性** | 投稿被要求改标签时，只能重新生成整张图 |

### 3.4 本包的实现落点

| 落点 | 说明 |
|-|-|
| `Scene` 数据结构 | `scripts/chartkit.py` |
| SVG 导出（分层 + `metadata` 溯源 + 真实 `<text>`） | `chartkit.py`；防转曲检查在 `scripts/svgtext.py` |
| PNG/PDF 导出 | `chartkit.py` 的 `export_figure` / `png_to_pdf` |
| 门禁 | G5（`real_text` / `layers` / `no_xxe`）· G6（PNG 可开、PDF 以 `%PDF` 开头） |
| **额外收益** | 因为是同一个 Scene，**PDF 的时间戳缺陷只需在一处修**（见机制四） |

### 3.5 怎么复验

```bash
python "$SKILL_DIR/scripts/figcheck.py" --dir <out> --case <case.json>   # G5/G6
grep -c '<text' <out>/figure-fig-01.svg        # > 0 → 文字仍是文本，未转曲
grep -o 'id="layer-[a-z]*"' <out>/figure-fig-01.svg | sort -u   # 分层存在
```

> **实测**：示例案例的 `figure-fig-01.svg` 有 4 个 `layer-*` 组、29 处 `<text>`。

---

## 4. 机制四：**契约四形态回显 + 确定性归一化**（结果可被机器接手）

### 4.1 它是什么

两部分，都指向同一目标 —— **让 result.json 成为机器可用的交付信封**：

**① 契约四形态回显**：`output_contract` 允许四种写法（字段名列表 / 名称→类型 /
嵌套 `fields` 列表 / 嵌套 `fields` 映射），引擎全部兼容；缺失字段按**声明的容器类型**
给空值（`""`/`[]`/`{}`/`false`/`0`），**绝不写 `null`**；已知别名（如
`editable_source` → `editable_sources`）映射到真实产物而不是打空。

**② 确定性归一化**：渲染器会往产物里写**当前时间戳**。本包在 PDF 落盘后
把 `/CreationDate`、`/ModDate`、`/ID` 就地归一化为固定值，
并同步修正交叉引用表里指向新位置的对象字节偏移。这样"同输入 → 同字节 → 同 `sha256`"。

### 4.2 常规做法是什么

`result.json` 字段随缘：有的字段缺失、有的写成 `null`、有的字段名与契约不一致。
产物里带着时间戳，`sha256` 每次都不同 —— **于是没人拿 sha256 当证据**。

### 4.3 没有它会怎样

| 症状 | 为什么 |
|-|-|
| **下游拿到 `null` 就得写特判** | 契约的意义就是让下游不用猜；`null` 把这个意义消掉了 |
| **契约换一种写法就崩** | 四形态是实际会遇到的（不同案例作者写法不同）；只兼容一种，换案例就要改代码 |
| **`sha256` 不能当证据** | 每次运行都变，无法回答"你交的和我验的是不是同一份" |
| **"同输入可复现"无法证明** | 交付件不可复现时，"结果可核验性"只剩口头承诺 |
| **回归测试无法做** | 没有稳定的基线哈希，就无法检测"这次改动是否意外改变了产物" |

### 4.4 本包的实现落点

| 落点 | 说明 |
|-|-|
| 四形态解析与别名映射 | `scripts/main.py` 的 `apply_output_contract` |
| 字段覆盖自查（**机器可读契约**） | `scripts/check_contract.py` 直接解析 `references/OUTPUT_CONTRACT.md` 的 `REQUIRED-FIELDS` 块 |
| PDF 确定性归一化 | `scripts/chartkit.py` 的 `stamp_pdf_deterministic()` + `_adjust_xref_offsets()` |
| 确定性验证 | `scripts/verify_rerun.py`（对 JSON 归一化时间戳/路径，对 PDF 归一化元数据，其余逐字节） |
| 门禁 | G2（契约字段全在且非 null）· G7（确定性）· G8（契约落地） |

### 4.5 怎么复验

```bash
# 四形态
python "$SKILL_DIR/scripts/check_contract.py" --result <out>/result.json --case <case.json>
# 期望：SUMMARY: PASS (required=18 missing=0 null=0 contract_missing=0)

# 确定性
python "$SKILL_DIR/scripts/verify_rerun.py" --case <case.json> --out <out>
# 期望：SUMMARY: DETERMINISTIC (identical=9 differ=0 missing=0)
```

> **实测（这是本包最有说服力的一条变更，含受控对照）**：
> **修复前**两次运行会有 **5 个**产物字节不同 —— 两份 PDF + 两份报告（仅 `dir` 字段）
> + `result.json`（因 pdf 的 sha256 变化）。PDF 的差异经 `cmp -l` 定位在
> `/CreationDate` / `/ModDate` 上，**字节数取决于两次运行的时间关系**：
> 同一秒内跑 = **2 字节**；跨秒跑 = **4 字节**。
> **修复后（同样跨秒跑）**：分辨率的产物全部字节一致，`verify_rerun` 报
> `identical=9 differ=0`；PDF 元数据固定为 `D:20000101000000Z`。
> 反向验证（注释掉归一化调用再跑）则稳定复现 5 个 DIFF —— 见 `TEST.md` T3.5。

---

## 5. 四个机制如何咬合（不是四个独立功能）

```
            声明式规格（机制二）
                   │  spec_lint 生成门拦住结构错误
                   ▼
        单一场景 Scene（机制三）—— 一次构造
                   │
       ┌───────────┴────────────┐
       ▼                        ▼
 分层 SVG（带 data-*）      PNG / PDF 预览
       │                        │
       │                        └─ 机制四②：元数据归一化 → sha256 成为证据
       ▼
 data_manifest.json（机制一）
       │  重读源表三向核对
       ▼
 result.json（机制四①）—— 四形态回显、禁 null、字段覆盖可命令化自查
```

**咬合关系**：机制二保证"能画的才画"；机制三保证"矢量与位图同源"，因此
机制一的溯源属性在 SVG 与 PNG 上对应同一批图元；机制四把整条链路的结果
变成**可被机器接手、且可复现**的信封。**拿掉任何一个，其余机制的收益都会被削弱**：

| 拿掉 | 连带损失 |
|-|-|
| 机制一 | 机制三的双端同源失去意义（同源但无法回溯到数据）；结果正确性只剩目视 |
| 机制二 | 错误推迟到渲染阶段；样式无法复用，机制四的契约里 `style` 字段也无从验证 |
| 机制三 | 机制一的 `data-*` 与位图脱钩；改一处要改两处，机制四的确定性维护成本翻倍 |
| 机制四 | 前三个机制的成果无法被下游消费，也无法证明"同一份" |

---

## 6. 相对"现有方案"的边界（创新证据 5 分的诚实写法）

| 对照对象 | 它强在哪 | 本包强在哪 | 本包**不**声称的 |
|-|-|-|-|
| 通用绘图库（matplotlib / plotly / seaborn） | 图型最全、生态最大、统计绘图成熟 | **可回溯性**（图元级溯源 + 程序化三向核对）、**可编辑交付**（分层 SVG + 真实文本）、**契约化结果信封**、**可复现** | 不声称图型比它们多；不声称渲染质量更好 |
| 现成期刊模板 / 排版工具 | 版式精细、符合投稿习惯 | **样式规则化**（预设 + spec 内联，加期刊 = 加键）、样式与数据链路绑定 | 不声称版式更专业 |
| 一次性绘图脚本 | 上手最快、最灵活 | 有门禁、有失败分支、有落痕、可复跑、可确定性验证 | 不声称比手写脚本"更快"——手写在小任务上确实更快 |

**边界声明的意义**：本期题面要求"评价是否证明新增能力相对已有方案的**边界与价值**"。
上表的作用就是**把边界写出来** —— 一个不说边界的"创新"是无法被验证的。

---

## 7. 这套机制怎么迁移到别的题（生态贡献的实质）

四个机制本身与"科研绘图"无关，它们是**交付型 Skill 的通用骨架**：

| 机制 | 迁移到别的题的形态 |
|-|-|
| 一 · 三向闭合 | 任何"从源材料产出结构化交付物"的题：交付物元素 ↔ 中间映射 ↔ 源材料，三处互为索引 + 重读源材料核对 |
| 二 · 声明式规格 + 生成门 | 任何"先决定做什么、再做"的题：把待办写成可校验的规格，校验不过不进执行 |
| 三 · 单一场景双端输出 | 任何"同一内容要多形态交付"的题（可编辑源 + 预览 + 导出件）：先建中立中间表示，再各端导出 |
| 四 · 契约回显 + 确定性归一化 | 任何"结果要被机器接手"的题：契约多形态兼容、禁 null、把渲染器注入的时间戳归一化，让 sha256 成为证据 |

具体到本包的**可复用资产清单与复用步骤**，见 `README.md` §6 与
`references/MECHANISM.md` 第一部分 第三部分。


---

## 第二部分 · 增益：公平对照协议、可测指标与实测记录

# MECHANISM.md 第二部分 — 公平对照协议、可测指标与实测记录

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
字节差（`cmp -l` 实测）**取决于两次运行的时间关系**：同一秒内连续跑 = **2 字节**；
跨秒跑（`sleep 3`）= **4 字节**（两个时间戳字段的秒数个位各 1 处）。全部落在时间戳上。

**这不是"归一化掩盖问题"，而是本版修掉的缺陷**（§7）。为了把这件事变成**受控对照**，
本版还做了一次**反向验证**：把 `stamp_pdf_deterministic` 的调用注释掉（其余代码不动），
`sleep 3` 后连跑两次 → **稳定复现 5 个 DIFF**（两份 PDF + `result.json` + 两份报告）；
把调用恢复后再 `sleep 3` 连跑两次 → 分辨率产物**全部 SAME**，
PDF 元数据固定为 `D:20000101000000Z`。**同一实验、只切换一个变量**。

修复后：

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


### 附 · 对照方案速览（原 `references/MECHANISM.md` 第二部分附节，与"直接调通用绘图库"的三方对照）

本文件回答「使用增益 25 分」最容易被扣的那一问：**增益怎么被公平地证明**。
题面写明：*平台固定运行 3 个案例，比较不加载 Skill 与加载参赛 Skill 时的实际结果；
需要相对比较的评分项使用组织方预先固定的白板。* ——因此：

- **对照由平台执行，参赛者不自造白板、不自报分数**；
- 参赛者要做的是：① 把「加载后」的做法写成**可复跑、可核验**的形式；
  ② 把**比较口径**写清楚，让评审能用同一输入复现 A/B。

> 本文件**不声称任何本地测得的"提升百分比"**：本机没有平台的基础 Agent 条件，
> 编造增益数字属于题面明令禁止的「文字自述替代实际运行证据」。
> 下表列的是**可判定的差异点**与**判定命令**，评审在固定 3 案例上跑一次即可得结论。

## 1. 两种条件的做法差异（同输入、同数据版本、同导出参数）

| 环节 | 基准做法（不加载 Skill 的基础 Agent） | 加载本 Skill 后 | 差异是否可机器判定 |
|-|-|-|-|
| 材料盘点 | 常见直接按文件名/标签假设内容，或跳过盘点直接画 | SKILL.md CP1：先列文件、算 sha256、记录行数与列名；缺文件 → 不猜内容并记 `uncertainty` | ✅ `result.json.checkpoints.cp1_material_survey` + `sources[].sha256` |
| 数据→图元映射 | 数值凭记忆/口算填进绘图代码，无从回溯 | `chartkit` 给每个图元写 `data-column`/`data-row-index`/`data-value`；`mapcheck.py` 重读源表逐行核对 | ✅ `mapcheck` `mismatches=0 unmatched=0`（G3/G4） |
| 标注校验 | 目视检查，图例/单位/显著性常错配 | 八类校验（溯源/图例-系列/轴单位/范围/CJK/显著性/空值/遮挡）逐项给出 level，fail 阻止 `completed` | ✅ `validation.json` checks + `figcheck` G7 |
| 中文与字体 | 直接输出中文，PNG 出现方框无人记录 | CJK 回退链（SVG）+ 运行环境字体扫描（PNG）；缺字记 warn/uncertainty | ✅ `environment.fonts` + `cjk-font` 检查项 |
| 可编辑交付 | 常给位图或"文字转曲"的 SVG | 分层 SVG（`<g id="layer-*">` + `<metadata id='provenance'>`），真实 `<text>` 不转曲 | ✅ `figcheck` G5（`real_text`/`layers`/`no_xxe`） |
| 重绘轮次 | 每次改图 = 重跑脚本 + 手工调，参数散失 | 样式走 `templates/journal_styles.json` 命名预设 + spec 内联键（三层合并），改样式=改配置 | ✅ 同输入换 `--style` 只改预设键，产物差异可 diff |
| 结果信封 | 常常没有结构化结果，或字段随缘 | `result.json` 契约化（四形态回显、禁 null），`check_contract.py` 自动核对覆盖 | ✅ `check_contract.py` `PASS` |
| 可复跑性 | 依赖交互式会话，无法复现同一张图 | 同输入同参数字节级稳定；`verify_rerun.py` 出确定性报告 | ✅ `verify_rerun.py` `DETERMINISTIC` |

## 2. A/B 比较口径（建议评审按此执行，双方条件完全对等）

| 项 | 规定 |
|-|-|
| 输入 | 平台固定案例的 `case.json` / `task.md` / 源数据文件，**同一份、同一版本**（记录 sha256） |
| 导出参数 | 同一 `--style`、同一 `--dpi`、同一图幅（`width`/`height` 来自 spec） |
| 条件 A | 基础 Agent 按同一任务说明直接产出图与结果 |
| 条件 B | 基础 Agent + 本 Skill（`SKILL.md` 流程，命令见 SKILL.md §3） |
| 判定 1：科学正确性 | 图元数值 vs 源表（逐元素）、轴单位量级、误差线语义、显著性锚点、实体名拼写 |
| 判定 2：标注完整性 | 六类检查点是否齐备（科学实体/空间关系/数据编码/图例标注/可编辑源文件/导出格式） |
| 判定 3：可编辑性 | 源文件是否分层可编辑、文字是否仍为文本、预览是否可打开 |
| 判定 4：效率 | 从输入到可交付图的**命令数/重绘轮次**，以及是否需要人工改图 |
| 复跑 | 条件 B 的产物可用 `verify_rerun.py` 复核确定性；条件 A 同样输入重复一次以示公平 |

> 说明：判定 1–3 本包都有现成的机器报告可对拍（`mapcheck_report.json`、
> `figcheck_report.json`、`validation.json`），无需人工重算。

## 3. 三方结构对照（写作形态层面）

| 维度 | 本包上一版（v1 基础包） | 本期高分包共性形态 | 本包（合规重打包版） |
|-|-|-|-|
| `SKILL.md` 位置 | 根 | 根（`outputs/SKILL.md`） | 根 ✅ |
| 规范前置 | 无 `references/` | references 三件套（审计/编码/字段映射） | 7 份 references（含契约 + 评分映射 + 失败模式 + 字段映射 + 审计 + 编码 + 排版） |
| 脚本 | 单引擎 + 单入口 | 生成/校验/收尾分文件 | 10 个脚本：生成（chartkit/main/extract/spec_lint）+ 校验（figcheck/mapcheck/verify_rerun/check_contract）+ 文字（cjkfont/svgtext） |
| 契约 | 无机器可读契约 | schema/template | `OUTPUT_CONTRACT.md` 含机器可读字段块 + `templates/{figure_map.schema,result.template}.json`，由 `check_contract.py` 执行 |
| 示例 | 无 | example-data + spec + 报告 | `examples/` 最小可跑案例 + 真实运行产物（契约 JSON）+ `EXPECTED-OUTPUT.md` 文字清单 |
| 二进制资源 | 有（预置 PDF/PNG 产物） | 部分有 | **0 个二进制**：全部资源为 UTF-8 文本，图/预览一律运行时由 `scripts/main.py` 生成 |
| 文本文件数 | 18（含 `__pycache__`） | 7 / 9 / 34 | 38（上限 50；含示例产物 JSON） |

## 4. 本包相对上一版的实质改动（全部可 diff 验证）

1. **资源形态合规化**：删除 `__pycache__`/`*.pyc`、示例产物中的 `*.pdf`/`*.png`/`*.svg`
   ——这些正是平台预检点名的 `unsupported Skill resource` 与文件数超限来源；
   图与预览改为运行时生成，示例产物改为**文字清单 + 契约 JSON**（见 `examples/EXPECTED-OUTPUT.md`）。
2. **去本机痕迹**：包内所有文本不再出现本机绝对路径（含字符探测候选路径改为运行时拼装）。
3. **契约可执行化**：新增 `scripts/check_contract.py`，把「字段是否覆盖」从人工目检变成一条命令；
   `manual_confirmations` 现在真正进入 `result.json`（此前文档承诺但脚本未落地）。
4. **文档严谨性**：统一 references 命名（`OUTPUT_CONTRACT.md`/`RUBRIC_MAP.md`）、
   修正 SKILL.md 中 `/app/input` 之类的路径不一致、补齐失败模式中的「模板缺失/依赖缺失/契约四形态/状态一致性」。
5. **不变的部分**：算法与 CLI 接口一字未改（`--case/--out/--work/--task/--data/--style/--dpi/--note/--lang/--no-pdf`），
   因此上一版通过预检的同族骨架（唯一过检那枪 69.33 分）的能力被完整保留。


---

## 第三部分 · 复用：可复用资产清单与复用步骤

# MECHANISM.md 第三部分 — 可复用资产清单与复用步骤

本文件是「**生态贡献 10 分**」（尤其"资源可复用性 4 分"）的主证据。
它回答的是：**别人拿到本包，能直接拿走什么、按什么步骤拿走、拿走之后能验证什么。**

---

## 1. 资产清单（按"可直接复用"的程度分层）

**分层依据**：A 级 = 复制文件即可用（不含本包特有内容）；B 级 = 需要换数据/换键；
C 级 = 需要理解机制后自行改造（但骨架可直接照搬）。

### A 级：复制即用（无本包特有内容）

> **依赖提醒**：`scripts/main.py` 在 import 阶段需要全部 6 个同族模块
> （`chartkit`/`extract`/`figcheck`/`mapcheck`/`spec_lint`/`verify_rerun`），
> 因此"只拿 3 个脚本就能跑 main.py"是**不成立**的（实测详见 §2 路径一的修正说明）。
> 单文件级的复用以"只 import、不调 main"的方式使用（见下表用法列）。

| 资产 | 文件 | 复用方式 | 前置条件 |
|-|-|-|-|
| **分层可编辑 SVG 渲染引擎** | `scripts/chartkit.py` | `import chartkit` 后构造 `Scene` 并调用导出，或直接把它放进你的包 | 需同目录有 `cjkfont.py`、`svgtext.py`（同族依赖） |
| **中文字体发现与回退** | `scripts/cjkfont.py` | 直接复制；或用 `python cjkfont.py` 盘点当前环境字体 | 无（纯标准库 + 可选 PIL） |
| **SVG 文本转义与防转曲检查** | `scripts/svgtext.py` | 直接复制 | 无 |
| **JSON 字段覆盖自查器** | `scripts/check_contract.py` | 直接复制；把它的 `--contract` 指向你自己的契约文档（需含 `REQUIRED-FIELDS` 机器可读块） | 你的契约文档要用同样的块语法 |
| **确定性再跑验证器** | `scripts/verify_rerun.py` | 直接复制；它按"JSON 归一化时间戳/路径、PDF 归一化元数据、其余逐字节"比较 | 无 |
| **PDF 元数据确定性归一化** | `scripts/chartkit.py` 的 `stamp_pdf_deterministic()` + `_adjust_xref_offsets()` | 单独取出这两个函数，放进你已有的 PDF 生成流程（`save` 之后调用） | 无（正则 + 字节操作） |
| **数据↔图元双向核对器** | `scripts/mapcheck.py` | 直接复制；约定你自己的 manifest/report 结构即可（结构在本包 `references/OUTPUT_CONTRACT.md` §5） | 你的产物要有对应的命名约定 |
| **A/B 对照判定器** | `examples/measure_ab.py` | 直接复制；改指标集即可（本包的 12 项只是示例集） | matplotlib 仅条件 A 需要 |
| **基准做法参照实现** | `examples/baseline_agent.py` | 直接复制；作为"不加载 Skill"的对照臂 | matplotlib |

### B 级：换数据/换键即用

| 资产 | 文件 | 怎么改 |
|-|-|-|
| **期刊/模板样式预设** | `templates/journal_styles.json` | 加一个键 = 加一个样式（字号/线宽/配色/dpi/边距）。**不用改代码** |
| **图规格声明式契约** | `templates/figure_map.schema.json` | 加图型 = 加一个 `type` 分支与其特有字段；引擎按同一 schema 解释 |
| **结果信封模板** | `templates/result.template.json` | 换案例时替换示例值；字段名与契约保持一致 |
| **实体/关系连接规则字典** | `templates/entity_glossary.json` | 加关系类型 → 颜色/线型；词表扫描的候选来源也在这里 |
| **最小可跑示例** | `examples/case.json` + `data.csv` + `entities.json` + `material.md` + `task.md` | 把 `data.csv` 换成自己的表，按列名改 `case.json` 的 `x`/`y`/`error`/`filter` |

### C 级：需理解机制后改造（但骨架可直接照搬）

| 资产 | 文件 | 复用要点 |
|-|-|-|
| **契约先行 + 门禁式执行链路** | `SKILL.md` 的执行链路章节 | 把流程切成有"进入/退出条件"的阶段，任何阶段不满足就降级或阻断 |
| **失败分支的按后果分组法** | `references/failure-modes.md` | 不按错误类型分组，而按"它打击哪一项可测能力"分组 —— 这样分支表可以直接当**验收清单**用 |
| **对照协议模板** | `references/MECHANISM.md` 第一部分 第二部分（v2/v3 同款） | 6 条公平性条件 + 归一化规则公开 + 每条件跑两次 + 公布自己不占优的项 |
| **唯一机制说明写法** | `references/MECHANISM.md` 第一部分（本文件所在目录） | 每个机制写四段：它是什么 → 常规做法 → **没有它会怎样（具体症状）** → 落点与复验 |
| **四机制骨架** | `references/MECHANISM.md` 第一部分 §5 的咬合图 | 三向闭合 / 声明式规格+生成门 / 单场景双端输出 / 契约回显+确定性归一化 |

---

## 2. 三条复用路径（按"你想拿走多少"分）

### 路径一：只想要"可编辑科研图"（最小拿走，约 10 分钟）

> ⚠ **实测修正（2026-11-22）**：本路径最初写成"只复制 3 个脚本 + 2 个模板"，
> **实测不成立** —— `main.py` 在 import 阶段就需要 `figcheck` / `mapcheck` /
> `spec_lint` / `verify_rerun` / `extract` / `chartkit` 六个模块：
> ```
> ModuleNotFoundError: No module named 'figcheck'
> ```
> 因此 `main.py` 的最小可用集合是**全部 10 个脚本**（见下方实测）。
> 如果你只想拿渲染引擎，应走"只 import 不调 main"的用法（见 §2.1）。

```bash
# 1) 复制全部 10 个脚本（main.py 的 import 依赖）+ 模板
cp <本包>/scripts/*.py <你的目录>/scripts/
cp <本包>/templates/*.json <你的目录>/templates/

# 2) 准备输入：case.json + 它引用的数据/材料文件
cp <本包>/examples/{case.json,data.csv,entities.json,material.md} <你的目录>/examples/

# 3) 出图
python <你的目录>/scripts/main.py --case <你的目录>/examples/case.json --out <out> --style nature
```

**实测（2026-11-22，全新空目录，只放上述文件）**：`py_compile` exit 0；
`main.py` exit 0；`status=completed`；G1–G8 全 OK。验收项：

| 检查 | 实测 |
|-|-|
| `*.svg` 数 | 2 |
| `layer-*` 组 | `layer-annotation` / `layer-axes` / `layer-data` / `layer-text`（4 个） |
| `metadata id='provenance'` | 1 处 |
| `<text>` 元素 | 29 处（文字未转曲） |
| `data-role="…"` 数 | 79 |

> 注：本次演练未复制 `task.md`，因此 `result.json` 有 28 键而非 29 键（少的正是
> `task_summary`）—— 这是**诚实的行为**：没有 task.md 就不编造任务摘要。

### 路径二：想要"可核验的交付链路"（中等拿走，约 30 分钟）

在路径一的基础上再拿走三个校验器与契约文档：

```bash
cp <本包>/scripts/{mapcheck.py,figcheck.py,verify_rerun.py,check_contract.py} <你的目录>/scripts/
cp <本包>/references/OUTPUT_CONTRACT.md <你的目录>/references/
```

**需要改的地方**（逐条对应的"契约一致性铁律"）：

| 改什么 | 同时要改的两处 |
|-|-|
| 新增必需字段 | 契约文档的 `REQUIRED-FIELDS` 块 + 你写入 `result.json` 的那处代码 |
| 新增标注检查项 | 引擎的校验段 + 契约文档的检查项表 |
| 换图型 | 引擎的场景构建 + 规格 schema |

**验证标准**：`figcheck.py` exit 0、`mapcheck.py` `mismatched=0`、
`check_contract.py` `missing=0 null=0`、`verify_rerun.py` `differ=0`。

> ❗ **路径二最常见的坑**：只改了文档没改代码（或反之）。本包的
> `check_contract.py` 是**直接解析契约文档**的，所以"文档说要有、代码没写"会立刻被抓到 ——
> 这正是把契约做成机器可读的价值。

### 路径三：想要"证明增益 + 说明机制"（完整拿走，约 1 小时）

再拿走对照工具、协议模板与机制说明书：

```bash
cp <本包>/examples/{baseline_agent.py,measure_ab.py} <你的目录>/examples/
cp <本包>/references/{MECHANISM.md 第二部分,MECHANISM.md} <你的目录>/references/
```

**改造顺序（建议）**：

1. **先定指标集**：把你关心的能力写成 8–12 条纯函数判据（本包的 Q1–Q12 是示例）。
   判断标准：**如果不做任何事也能全部通过，那这些指标没有区分度。**
2. **再造对照臂**：把"常规做法"固化成一段能跑的代码（本包的 `baseline_agent.py`）。
   纪律：**不刻意做差**。
3. **跑两次**：第二次是确定性的唯一证据。本包的 PDF 时间戳缺陷就是靠第二次跑出来的。
4. **写协议**：6 条公平性条件 + 归一化规则（含**方向性说明**）+ 边界声明。
5. **写机制**：每个机制四段式，**第二段和第三段最关键**（常规做法是什么、没有它会怎样）。

**验证标准**：`measure_ab.py` 对两侧都跑出报告；两侧的公平性条件逐条可核；
协议里明确写了"本协议不做的事"。

---

## 3. 复用时的验收清单（复制完照着打勾）

- [ ] `python -m py_compile scripts/*.py` 全部通过
- [ ] 在你的案例上 `main.py` exit 0，且 `result.json` 的契约字段齐备（无 `null`）
- [ ] `figure-*.svg` 含 `id="layer-*"`、`<metadata id='provenance'>`、`<text>`，无 `<path>` 替字
- [ ] `mapcheck.py` `mismatched=0`；任取一个 `data-column`/`data-row-index` 回源表能对上
- [ ] `figcheck.py` G1–G8 全过
- [ ] `verify_rerun.py` 报 `differ=0`（**若报 PDF 差异，说明你没拿走机制四②**）
- [ ] `check_contract.py` `missing=0 null=0`
- [ ] 包内**无** `__pycache__` / `*.pyc`（跑完脚本记得清）
- [ ] 包内**无**本机绝对路径（字体探测的候选路径字符串除外）
- [ ] 所有资源是允许的文本扩展名（`.md/.py/.json/.txt/.csv/.yaml/.yml`）

---

## 4. 复用**不要**带走的（本包特有，带了会误导）

| 不要带走 | 原因 |
|-|-|
| `examples/` 里的合成数据本身 | 它们是为演示接口自拟的；当成"真实数据"会污染你的案例 |
| 本包的 12 项指标集**原样** | 指标要匹配你的能力面；照抄会得到一堆"两边都不通过"的指标 |
| 本包的成绩数字（A 1/12、B 12/12） | 那是**合成示例**上的本地数字，不是你的结果，更不是平台评分 |
| `GITHUB_URL.txt` | 指的是本包位置 |
| 任何写成"结论"的措辞 | 迁移时应当把"结论"换成你自己的实测，机制与步骤才是可复用的部分 |

---

## 5. 一句话总结复用价值

**本包最可复用的不是那张图，而是这套"让交付物可回溯、可校验、可复现、可被机器接手"
的骨架** —— 四个机制（`MECHANISM.md`）、一套失败分支分组法（`failure-modes.md`）、
一份对照协议（`MECHANISM.md 第二部分`）、一张验收清单（本文件 §3）。
把它们换到别的交付型题目上，需要改的是"领域细节"，需要保留的是"骨架"。


---

## 第四部分 · 增改：相对合规基线的逐条改动与复核命令

# MECHANISM.md 第四部分 — 本版相对基线的逐条增改（可 diff 验证）

**本版 = 决策显性化版**（`v1`）。起点是**合规基线包**（已投出的那一版），本文件逐条列出**改了什么、为什么改、怎么自己验**。

> 本文件**不是**那种追加在文档末尾的说明式注释段 —— 每条改动都落在**具体文件的
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
| 7 | 新增文件 | `references/MECHANISM.md` 第四部分 | 本文件 |
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
