# README.md — 科研数据图表生成与编辑 Skill（机制与复用显性版）

`challenge-1bd90d8a` · 玻尔产品周赛 · 北大专区 · 学术效率 · 第三期

本包把「科研数据表 / 生物源材料 → 可直接投稿的可编辑图稿」做成一条**可回溯、
可校验、可复现、可被机器接手**的链路，并把支撑这条链路的**四个机制**与
**可复用资产**显式写出来（`references/MECHANISM.md` / `references/REUSE-KIT.md`）。

---

## 1. 依赖与安装

| 项 | 要求 |
|-|-|
| Python | 3.8+（开发与实测环境：CPython **3.13.9**） |
| 必需 | 标准库 |
| 推荐 | `Pillow`（渲染 PNG/PDF 预览）。缺失时**自动降级**：SVG 与全部 JSON 照常产出，PNG/PDF 记为缺失并写入 `uncertainty` |
| 仅对照工具需要 | `matplotlib`（**只有** `examples/baseline_agent.py` 用它构造"基准条件"；主链路完全不依赖） |
| 非必需 | `cairosvg` / `svgwrite` —— 本包不使用 |
| 网络 | **不需要**，脚本内不做网络访问 |
| 字体 | 运行时自动扫描常见字体目录；可用环境变量 `FONT_PATHS` 追加 |

```bash
pip install Pillow            # 可选但推荐
pip install matplotlib        # 仅在复跑对照实验时需要
```

**无需安装本包**：`scripts/` 是纯标准库模块，按路径直接调用即可。

---

## 2. 怎么调用

`$SKILL_DIR` = 本包所在目录的绝对路径（平台安装期为 `/skills/weekly-skill`）。
脚本用 `os.path.dirname(os.path.abspath(__file__))` 自定位资源，**cwd 与技能根不同也能跑**。

```bash
SKILL_DIR=/skills/weekly-skill

# 主链路（环 E1→E8 一次跑完）
python "$SKILL_DIR/scripts/main.py" \
       --case /input/case.json --out /app/output --work /app/work --style nature

# 四道复核 —— 每道对应一个机制（见 §3.1）
python "$SKILL_DIR/scripts/mapcheck.py"       --dir /app/output --case /input/case.json   # M1
python "$SKILL_DIR/scripts/figcheck.py"       --dir /app/output --case /input/case.json   # M1+M3+M4
python "$SKILL_DIR/scripts/verify_rerun.py"   --case /input/case.json --out /app/output   # M4②
python "$SKILL_DIR/scripts/check_contract.py" --result /app/output/result.json --case /input/case.json  # M4①
```

### 2.1 全部命令行参数

| 参数 | 默认 | 说明 |
|-|-|-|
| `--case` | 必需 | `case.json` 路径 |
| `--out` | `out` | 产物目录 |
| `--work` | 无 | 中间产物目录（`extract.json`、`spec_lint.json`） |
| `--task` | 自动发现 | 显式指定 `task.md` |
| `--data` | 自动发现 | 显式指定数据文件（`;` 分隔多个） |
| `--style` | `default` | 样式预设：`default`/`nature`/`cell`/`prism`/`minimal`/`ppt` |
| `--dpi` | 预设值 | PNG 渲染分辨率，覆盖样式预设 |
| `--note` | 无 | 追加一条人工变更记录进 `change_records` |
| `--lang` | `zh` | 标签语言：`zh` / `en` |
| `--no-pdf` | 关 | 跳过 PDF 预览 |

### 2.2 退出码语义

| 脚本 | 0 | 1 | 2 |
|-|-|-|-|
| `main.py` | `completed` 且 G1–G8 全过 | `failed` | `partial` |
| `figcheck.py` | G1–G8 全过 | 有门未过 | — |
| `mapcheck.py` | 0 mismatch / 0 unmatched | 有 mismatch | — |
| `spec_lint.py` | spec 合法 | 用法/文件错误 | spec 有 error（**不得进入生成**） |
| `check_contract.py` | 字段覆盖完整 | 有 missing/null | 契约文档或 result 不可读 |
| `verify_rerun.py` | 确定性通过 | 有非时间戳差异 | — |

---

## 3. 设计：四个咬合机制

本包的机制主张是：**把图当可回溯的证据，而不是当输出。** 落地为四个机制：

| # | 机制 | 一句话 | 主要落点 |
|-|-|-|-|
| **M1** | 三向闭合 | SVG 图元 `data-*` ↔ `data_manifest.json` ↔ **重读源表**的值，三处互为索引且程序核对 | `chartkit.py` + `mapcheck.py` |
| **M2** | 声明式规格 + 生成门 | 先写可校验的图规格，过门才进渲染 | `figure_map.schema.json` + `spec_lint.py` |
| **M3** | 单一场景双端输出 | 一个 `Scene` 同时导出分层 SVG 与 PNG/PDF，逐元素同源 | `chartkit.py` + `svgtext.py` |
| **M4** | 契约四形态回显 + 确定性归一化 | 契约全兼容禁 null；时间戳归一化让 `sha256` 成为证据 | `main.py` + `check_contract.py` + `chartkit.stamp_pdf_deterministic` |

**每个机制"没有它会怎样"的具体症状、实现落点与复验命令**见
`references/MECHANISM.md`；四个机制如何咬合（含咬合图与"拿掉任何一个的连带损失"）
见同文件 §5。

### 3.1 复核命令 ↔ 机制 的对应

| 命令 | 验证哪个机制 | 期望 |
|-|-|-|
| `mapcheck.py` | **M1** | `mismatched=0 unmatched=0` |
| `spec_lint.py` | **M2** | exit 0（`valid=true`） |
| `figcheck.py`（G5/G6） | **M3** | `real_text` / `layers` / `no_xxe` 全过；PNG 可开、PDF 以 `%PDF` 开头 |
| `check_contract.py` | **M4①** | `missing=0 null=0 contract_missing=0` |
| `verify_rerun.py` | **M4②** | `differ=0` |

---

## 4. 适用范围与限制

**适用**：平台固定 3 个案例；也适用于任何「数据表或生物源材料 → 可编辑科研图」的请求。
支持八种图型：`bar` / `line` / `scatter` / `box` / `heatmap` / `pie` / `network` / `panel`
（`panel` 可递归嵌套；`type: auto` 按列语义自动推断）。

**限制（如实声明）**：
- 不做统计推断——显著性只转述材料给的 p 值。
- 机制/通路图自动布局是启发式的；复杂通路建议在 spec 手给节点坐标。
- PDF 预览是光栅预览嵌入 PDF；矢量可编辑源以 SVG 为准。
- 中文字体依赖运行环境；缺字体时 SVG 走回退链、PNG 记 warn。
- **`spec_lint.py` 不核对列存在性**（实测：引用不存在的列仍返回 `VALID`、exit 0）；
  M2 的"生成门"不是唯一防线，真实兜底是 M1 的三向核对。本版未改代码（接口不得变动）。
- **四个机制各自的边界**见 `references/MECHANISM.md` §6（相对通用绘图库 / 现成模板 /
  一次性脚本的对照表）。简短版：M1 只保证可回溯（不保证数据本身正确）；
  M3 只保证双端同源（不保证美观）；M4 只保证可被机器接手且可复现（不保证字段的业务含义正确）。
- 本包**不含任何二进制资源**，也不含预制成品图。

---

## 5. 维护

| 要改什么 | 改哪里 | 注意事项 |
|-|-|-|
| 加一个期刊样式 | `templates/journal_styles.json` 加一个键 | 不用改代码（M2-R3） |
| 加一种关系类型的着色/线型 | `templates/entity_glossary.json` | 不用改代码 |
| 加一个标注检查项 | `scripts/chartkit.py` 的校验段 + `references/OUTPUT_CONTRACT.md` §4 | 契约是机器可读的，改契约 = 同时改文档与脚本 |
| 新增必需字段 | `references/OUTPUT_CONTRACT.md` 的 `REQUIRED-FIELDS` 块 + `scripts/main.py` 写入处 | 字段名不得只改一处 |
| 加一张图的图型 | `scripts/chartkit.py` 的场景构建 + `templates/figure_map.schema.json` | CLI 接口不得变 |
| 加一项对照指标 | `examples/measure_ab.py` 加一个 `metric(...)` + `references/GAIN-PROTOCOL.md` §5.1 | 指标集与文档必须同步 |
| **改机制说明** | `references/MECHANISM.md` | 改了机制必须同时更新"没有它会怎样"的表格与复验命令 |
| **加可复用资产** | `references/REUSE-KIT.md` §1 分级表 + §3 验收清单 | 需要写清"复制即用 / 换键即用 / 需理解后改造" |

**两条一致性铁律**：
① `references/OUTPUT_CONTRACT.md` 是**机器可读**的（`check_contract.py` 直接解析
其 `REQUIRED-FIELDS` 块）；改契约 = 同时改两处。
② `references/MECHANISM.md` 的复验命令必须与实际 CLI 逐字一致；
改了脚本参数就要同步改机制说明，否则机制说明会变成误导。

---

## 6. 复用步骤（生态贡献的可操作版本）

完整清单（A/B/C 三级资产表 + 三条路径 + 十条验收清单 + "不要带走的五项"）见
`references/REUSE-KIT.md`。这里给出**可直接照做的三步**。

### 步骤 1：选路径（想拿走多少）

| 路径 | 耗时 | 拿走什么 | 适用场景 |
|-|-|-|-|
| **路径一 · 可编辑科研图** | 约 10 分钟 | ⚠ **全部 10 个脚本** + `templates/*.json` + 输入文件（实测：`main.py` import 阶段就需要 6 个同族模块，只拿 3 个脚本会 `ModuleNotFoundError`） | 你只需要"出一张能改的科研图" |
| **路径二 · 可核验交付链路** | 约 30 分钟 | 再加 `scripts/{mapcheck,figcheck,verify_rerun,check_contract}.py` + `references/OUTPUT_CONTRACT.md` | 你需要"结果能被别人复核" |
| **路径三 · 证明增益 + 说明机制** | 约 1 小时 | 再加 `examples/{baseline_agent,measure_ab}.py` + `references/{GAIN-PROTOCOL,MECHANISM}.md` | 你需要"向别人证明这套做法更好" |

### 步骤 2：按路径改（每条都写清"要同时改两处"的地方）

```bash
# 路径一（实测：main.py 的 import 依赖决定最小集合 = 全部脚本）
cp <本包>/scripts/*.py                                      <你的>/scripts/
cp <本包>/templates/*.json                                  <你的>/templates/
cp <本包>/examples/{case.json,data.csv,entities.json,material.md} <你的>/examples/
# 路径二（追加契约文档与字段自查器说明）
cp <本包>/references/OUTPUT_CONTRACT.md                     <你的>/references/
# 路径三（追加）
cp <本包>/examples/{baseline_agent.py,measure_ab.py}        <你的>/examples/
cp <本包>/references/{GAIN-PROTOCOL.md,MECHANISM.md}        <你的>/references/
```

**必须成对修改的三处**（改一处不改另一处会立刻被抓到）：

| 改什么 | 第一处 | 第二处 |
|-|-|-|
| 新增必需字段 | 契约文档的 `REQUIRED-FIELDS` 块 | 写入 `result.json` 的代码 |
| 新增标注检查项 | 引擎的校验段 | 契约文档的检查项表 |
| 换图型 | 引擎的场景构建 | 规格 schema |

### 步骤 3：按清单验收（复制完照着打勾）

- [ ] `python -m py_compile scripts/*.py` 全过
- [ ] 在你的案例上 `main.py` exit 0，契约字段齐备且无 `null`
- [ ] `figure-*.svg` 含 `id="layer-*"`、`<metadata id='provenance'>`、`<text>`，无 `<path>` 替字
- [ ] `mapcheck.py` `mismatched=0`；任取一个 `data-column`/`data-row-index` 回源表能对上
- [ ] `figcheck.py` G1–G8 全过
- [ ] `verify_rerun.py` 报 `differ=0`（**若报 PDF 差异 → 你没拿走机制 M4②**）
- [ ] `check_contract.py` `missing=0 null=0`
- [ ] 包内无 `__pycache__` / `*.pyc`；无本机绝对路径；扩展名在白名单内

> **路径二最常见的坑**：只改文档不改代码（或反之）。本包的 `check_contract.py`
> 是**直接解析契约文档**的，所以"文档说要有、代码没写"会被立刻抓到 ——
> 这正是把契约做成机器可读的价值。

### 不要带走的五项

见 `references/REUSE-KIT.md` §4。要点：本包的合成数据、12 项指标集原样、
本地成绩数字、`GITHUB_URL.txt`、以及任何写成"结论"的措辞 ——
**机制与步骤才是可复用的部分，数字会过时。**
