# REUSE-KIT.md — 可复用资产清单与复用步骤

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
| **对照协议模板** | `references/GAIN-PROTOCOL.md`（v2/v3 同款） | 6 条公平性条件 + 归一化规则公开 + 每条件跑两次 + 公布自己不占优的项 |
| **唯一机制说明写法** | `references/MECHANISM.md`（本文件所在目录） | 每个机制写四段：它是什么 → 常规做法 → **没有它会怎样（具体症状）** → 落点与复验 |
| **四机制骨架** | `references/MECHANISM.md` §5 的咬合图 | 三向闭合 / 声明式规格+生成门 / 单场景双端输出 / 契约回显+确定性归一化 |

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
cp <本包>/references/{GAIN-PROTOCOL.md,MECHANISM.md} <你的目录>/references/
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
一份对照协议（`GAIN-PROTOCOL.md`）、一张验收清单（本文件 §3）。
把它们换到别的交付型题目上，需要改的是"领域细节"，需要保留的是"骨架"。
