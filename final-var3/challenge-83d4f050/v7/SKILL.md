---
name: biological-mechanism-pathway-diagram
description: >-
  把科研机制/通路材料转成可逐条核验的生物机制图与通路图（真实材料抽取实体与相互作用 →
  区室约束确定性布局 → 可编辑分层 SVG 源 + PNG/PDF 预览 → 拓扑与图例/数据编码双审计 →
  契约化 result.json），并且**把"同输入重跑是否得到同一份产物"做成可复算的测量**：
  随包提供可运行的字节级确定性探针 `scripts/determinism.py`（跨进程/跨 cwd/跨
  PYTHONHASHSEED 连跑 N 次，对全部产物做 sha256 比对，逐字段点名易变项，并给出三条
  稳定化配方）与实测表 `references/DETERMINISM.md`、机器可读报告 `determinism_report.json`。
  Use when the task asks to draw, generate, edit, re-export or validate a biological
  mechanism map, pathway diagram, signaling cascade, regulatory network or flow
  diagram (figures group of the biology mechanism & pathway challenge), or when a
  reviewer needs byte-level evidence that such a figure pipeline is reproducible.
---

# biological-mechanism-pathway-diagram · v7（确定性 / 字节级可复现）

机制图的科学性不看图画得多复杂，而看三件事：**每个实体和每条边能否回溯到材料；图例、颜色映射与
图形本身是否自洽；别人能否打开可编辑源文件改一个标签并重新导出。** 本版在此基础上再加一条可被
第三方复算的要求：**同一份输入重跑，产出的字节必须可预测**——不能预测的部分必须被**逐字段点名**。

## 1. 这一版解决什么问题

"确定性"通常只是一句写在文档里的承诺（"同输入结果一致"）。本版把它变成**三条判据 + 一台探针 + 一张实测表**：

| 判据 | 内容 | 谁能复算 |
|-|-|-|
| **J1 原始字节稳定清单** | 存在一个明确清单，其成员在任何 cwd / 任何 `PYTHONHASHSEED` / 任何进程下 sha256 相同 | `scripts/determinism.py`（5 次运行） |
| **J2 易变清单逐字段点名** | 不稳定的产物必须指出**哪个字节 / 哪个 JSON 路径**不稳定，并区分"故意"与"缺陷" | `determinism_report.json → volatile_fields[] / byte_diff` |
| **J3 稳定化后逐字节一致** | 施加文档化规则后全部产物哈希一致（三条独立证据同真） | `stabilization.json_projection / pdf_normalization / env_recipe` |

只满足 J1 不算"可复现"（那只是"大部分稳定"）。判据、实测表与配方全文见
`references/DETERMINISM.md`（本版的轴文档）。

**本机实测一句话版**：7 个产物里 **5 个**（`diagram.svg` `diagram.png` `model.json` `topology.json`
`legend_audit.json`）在 5 次跨 cwd / 跨哈希种子的运行间**逐字节相同**；`diagram.pdf` 只差
**1 处、1–2 个字节**（`/CreationDate` 的秒位，偏移 104020 起）；`result.json` 差在**8 个 JSON 路径**
（4 条时间戳 + 3 条 cwd 泄漏路径 + 1 条二阶字节数）。固定 cwd 并设 `SOURCE_DATE_EPOCH` 后，
**唯一**不可复现的只剩 3 条变更记录与 1 条 provenance 的**时间戳字段**。

## 2. 用途与适用条件

- **适用**：生物机制图 / 通路图 / 信号级联 / 调控网络 / 流程图的生成、编辑、重导出与校验；
  也适用于"把一段机制文字变成图""改他人图稿的一个错误箭头""按数据给节点上色""补图例"。
- **额外适用（本版新增）**：需要向评审证明"这条绘图流水线是可复现的"——用同一份 `model.json`
  在别的机器上重跑，拿 §4 里那 5 个 sha256 直接对拍，不需要"看着差不多"。
- **不适用**：数值统计与统计结论、实验方案设计、论文写作与版式美化（相邻课题负责）。
- **运行前提**：Python 3（标准库即可产出可编辑 SVG 与全部审计产物）；`matplotlib` 可选，
  只影响 PNG/PDF 预览（缺它时按 `partial` 降级并如实记录，详见 `references/failure-modes.md`）。

## 3. 资源形态（先读，它决定包怎么用）

本包**只含文本资源**，遵守运行时契约：`at most 50 UTF-8 text files, 500KB each and 2MB total, no symlinks`。

- 允许扩展名仅七种：`.md .py .json .txt .csv .yaml .yml`；包内**没有任何二进制**；
- `diagram.svg` / `diagram.png` / `diagram.pdf` 一律由 `scripts/` 在**运行时**生成；
- `examples/output/` 只有示例案例上实跑得到的 JSON 产物与文字化 `examples/EXPECTED-OUTPUT.md`；
- `determinism_report.json` 是**本机实跑的一次确定性测量报告**（不是预置答案、不是正式案例结果）。

## 4. 命令行总览（自定位，cwd 不是技能根也能跑）

```bash
export SKILL_DIR=/skills/weekly-skill          # 平台容器安装路径；本机改成含 SKILL.md 的那一层
python3 "$SKILL_DIR/scripts/main.py" --help    # 自检：能打印帮助即路径正确
```

| 入口 | 参数 | 说明 |
|-|-|-|
| `scripts/main.py` | `--case --task --out --materials-dir --model-file --formats --dpi --verbose` | 单一主入口；`--formats` 默认 `svg,png,pdf`；`--dpi` 默认 150；`--materials-dir` 可重复 |
| `scripts/check_contract.py` | `--result --case` | 独立复查 `result.json`（信封字段 / 禁止 null / 契约回显 / G1–G8） |
| `scripts/validate_figure.py` | `--out --case` | 对已产出的输出目录做独立复检（`--case` 可选，`model.json` 权威） |
| `scripts/determinism.py` | `--skill --case --model-file --runs --work --report --formats --dpi --python --strict --clean --json` | **本版新增**：字节级确定性探针（见下） |

```bash
# 标准一次运行（示例案例；正式运行时把 --case 换成 /input/case.json）
python3 "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" \
    --model-file "$SKILL_DIR/examples/model.example.json" \
    --out /app/output --formats svg,png,pdf --verbose

# 本版新增：确定性测量（默认 5 次运行，报告写到包根；应退出 0）
python3 "$SKILL_DIR/scripts/determinism.py" --runs 5 \
    --work /tmp/det --report "$SKILL_DIR/determinism_report.json"
```

**退出码**：

| 脚本 | 0 | 2 | 3 | 4 |
|-|-|-|-|-|
| `main.py` | `status=success` | `status=partial` | `status=failed`（材料/schema 层阻断） | — |
| `determinism.py` | 规范化后全部产物逐字节一致 | 主流程某次非期望退出（环境/输入问题） | 规范化后仍不一致（真不可复现） | 参数/路径错误 |
| `check_contract.py` | 契约通过 | — | — | — （失败为 1） |
| `validate_figure.py` | 全检查通过 | — | — | — （失败为 1） |

## 5. 本版方法：把"可复现"测出来

### 5.1 探针做了什么

每次运行都是**新解释器进程**，命令字面量逐字相同（`--out out` 用相对路径，使 `provenance.command`
在各次运行间一致），只轮转两个变量：**cwd**（技能根 / `scripts` / 案例目录 / `examples` / 工作根）
与 **`PYTHONHASHSEED`**（`0` / `1` / `12345` / `random` / 不设置）。每次运行后立刻对输出目录
**全部产物**取 sha256，再跨运行比对。

### 5.2 实测结果（CPython 3.13.9 / win32 / matplotlib 3.10.6 / Pillow 12.3.0）

| 产物 | 字节 | sha256（前 16 位） | 不同哈希数 | 判定 |
|-|-|-|-|-|
| `diagram.svg` | 17771 | `27f344a0dfb2e90f` | 1 | ✅ 稳定 |
| `diagram.png` | 203655 | `9137715961238f3f` | 1 | ✅ 稳定（PNG 无 `tIME` 块，只有恒定的 `tEXt`） |
| `model.json` | 11418 | `f93a20a283492f73` | 1 | ✅ 稳定 |
| `topology.json` | 1434 | `eb826fc5557fccfc` | 1 | ✅ 稳定 |
| `legend_audit.json` | 1807 | `efdb1805c839d648` | 1 | ✅ 稳定 |
| `diagram.pdf` | 108045 | `79fdc09f7310e7dd`（第 1 次） | **5** | ❌ 仅 `/CreationDate` 秒位（1–2 字节） |
| `result.json` | 28888–29056 | `257ca36c870501f0`（第 1 次） | **5** | ❌ 8 个 JSON 路径（见下） |

**易变字段（观测到的全部差异路径）**：

| JSON 路径 | 性质 | 稳定化 |
|-|-|-|
| `$.provenance.ts`、`$.change_records[0..2].ts` | **故意**：真实运行时间（秒级） | 投影掩码 |
| `$.provenance.case_file`、`$.change_records[0..1].why` | **缺陷级：cwd 泄漏**（`portable_path()` 在路径不属于技能根时退化为"相对当前工作目录"渲染） | 投影掩码，或**固定 cwd** |
| `$.self_check.checks[30].detail` | 二阶：内含上一步 `result.json` 的字节数 | 随路径字段一起掩码 |

⇒ 因此"字节级可复现"在本包里等价于**把 cwd 与输入一起固定**；只固定输入是不够的。

### 5.3 稳定化配方（三条，各有实测）

1. **JSON 投影**（比对用，不改产物）：掩码"时间戳/主机/路径"类键与观测到的易变路径 → 规范化序列化 → 比 sha256。实测 5 次运行归一为 1 个哈希。
2. **PDF 规范化**（比对用）：`/CreationDate`、`/ModDate`、`/ID` → 固定占位。实测 5 次运行归一为 1 个哈希（本机 PDF 无 `/ModDate`、无 `/ID`）。
3. **环境配方**（不改脚本就能拿到原始字节一致）：`cd "$SKILL_DIR"` 固定 cwd + `SOURCE_DATE_EPOCH=1577836800`，两次运行参数逐字相同。实测：**除 `result.json` 外全部产物原始字节一致**（含 PDF），`result.json` 残余差异**恰好 4 条时间戳路径**（`change_records[0..2].ts`、`provenance.ts`），投影后一致。

> 用法建议：CI/复检里用配方 1+2 判"内容是否真的变了"；要与他人对拍原始字节时用配方 3 并把
> §5.2 的 5 个哈希作为比对基准。**不要在需要 `success` 的场景里省略 `--formats`**（见 §7）。

## 6. 主流程 CP1–CP5

- **CP1 先读真实文件**：读 `case.json` / `task.md` / 材料目录里**每个文件**（正文、表格、PDF），
  提取任务要求、事实（实体/区室/相互作用/方向/数值）与约束，**每个事实记出处（文件+行号）**。
  材料缺失时 CP1 直接 `failed`（退出码 3）——先补齐材料或改用 `--model-file`。
- **CP2 机制规格 + schema 门**：结构化材料由 `scripts/extract.py` 生成草稿 `model.json`；
  草稿/手工规格先对**原始未归一化**规格过 `assets/mechanism-spec.schema.json`（未知类型 → `failed`，不静默改写）。
- **CP2b 散文/PDF 材料**：Agent 读材料后按 `references/mechanism-spec.md §1` 手写 `model.json`，
  用 `--model-file` 重跑（`extraction.method` 记 `manual`）。
- **CP3 人工核验**：打开规格逐条对照材料原文（命名、边类型、方向、证据强度、区室、数值来源），
  核对完成把 `extraction.verified_by_agent` 置 `true` 并在 `change_records` 逐条记录改动；
  用 `templates/relation-checklist-template.md` 五表作为核验载体。**未核验的自动草稿只能是 `partial`。**
- **CP4 布局、渲染与双审计**：`layout.py` 区室带确定性布局（胞外→膜→胞质→核，反馈环右侧绕行）；
  `pathway_svg.py` 写 7 层可编辑 SVG；`mpl_backend.py` 渲染 PNG/PDF；`topology.py`（P01–P08）与
  `legend_audit.py`（L01–L08、E01–E02）出审计 JSON；`validate_figure.py` 聚合 M/T/P/L/E/S/F/D 系列检查 + 确定性探针。
- **CP5 写 `result.json` 并自查**：字段与硬门以 `references/OUTPUT_CONTRACT.md` 为唯一权威
  （信封字段、四形态回显禁止 null、G1–G8）。交付前逐条过 SKILL 自查清单（材料实读、来源齐全、
  命名规范、箭头=图例、数据三方一致、SVG 可编辑且 7 层、契约齐全、审计产物在、`uncertainty`/`change_records` 诚实）。

## 7. 决策规则（与本轴相关，遇情况先查表）

| # | 情形 | 决策 |
|-|-|-|
| D1 | 需要"可复现"的结论 | 先跑 `scripts/determinism.py --runs 5`；**不要**只凭"看起来一样"下结论（J1/J2/J3 三条都要过） |
| D2 | 产物原始字节不一致 | 先看 `volatile_fields`：只有时间戳 → 属**故意**；出现路径字段 → 检查 cwd 是否漂移；出现其它字段 → 当缺陷处理并写入 `uncertainty` |
| D3 | 报告要与他人对拍 | 用固定 cwd + `SOURCE_DATE_EPOCH` 配方重跑，并比对 §5.2 的 5 个稳定哈希（跨机对比时注意库版本/字体差异，不要过度声称） |
| D4 | 只需 SVG（`--formats svg`） | 允许，但 `status` 会降为 `partial`（`F01_png`/`F01_pdf` 记为失败）；需要 `success` 就始终请求 `svg,png,pdf` |
| D5 | 材料未写上下游方向 | 不臆造方向：画结合类无向边并标 `uncertain` |
| D6 | 同名基因与蛋白同时出现 | 拆成两个实体（基因斜体 / 蛋白正体），note 写明依据；无法区分则标 `uncertain` |
| D7 | 同一蛋白多区室（胞质 ERK / 核内 ERK） | 按区室拆实体（P04b），note 注明去向 |
| D8 | 材料数值与图面意图矛盾 | 以材料原文为准，`uncertainty` 与 `change_records` 双记 |
| D9 | 数据值缺来源 | 阻断：补 `source`，或降为 `assumption` 并进 `uncertainty`（E01/T03） |
| D10 | 机制规格不过 schema 门 | 阻断渲染（`failed`），按违规清单修正后重跑（CP2） |
| D11 | `matplotlib` / 字体缺失 | 保留可编辑 SVG；PNG/PDF 缺失如实记录并写 `export_checks`；`status=partial` |
| D12 | 材料里没有实体/关系 | 明确 `failed`，不画空图凑数，给出补救路径（补材料或 `--model-file`） |

## 8. 异常处理与留痕

完整清单见 `references/failure-modes.md`（本版新增 **FM-D1–FM-D6**：字节漂移、cwd 泄漏、
同秒侥幸、PDF 时间戳、PNG 时间块、跨机对比过度声称）。三条通则：
**① 任何降级都要有留痕位置**（`uncertainty` / `change_records` / `export_checks` / 检查项 id）；
**② 任何 `fail` 都要落到 `status`**（不得 `success`）；**③ 不确定就写不确定，不要补造。**

## 9. 反预制答案

`examples/` 里的一切（case / 材料 / 模型 / 输出 / 本版报告）都是**演示**：图内与 `result.json` 均带示例标记。
正式运行**禁止**把示例的实体/边/数值抄进正式输出；平台案例材料与示例不同，必须现场从真实材料推导。
不给自己编造 benchmark 分数；`determinism_report.json` 只描述**本机这一次测量**，不是分数也不是正式案例结果。

## 10. 限制与维护

- SVG 为手写图层制式（浏览器 / Inkscape / draw.io / 脚本可编辑）；不做 Word/PPT 内嵌途径。
- 自动抽取器只处理结构化语句；散文材料依赖 Agent 人工抽取（CP3 强制）——准确率优先于全自动。
- **确定性结论的适用范围**：同一平台 + 同一解释器/库版本/字体环境（换版本或换平台时
  `diagram.png`/`diagram.pdf` 预期不同，未实测，不声称）；并发写同一输出目录未覆盖。
- 风格常量集中 `assets/palettes.json`；契约与门集中 `references/OUTPUT_CONTRACT.md`；
  改动后同步更新 `TEST.md` 实测记录并在 `worklog.md` 追加一条带时间的记录。

## 11. 文件索引

- `references/DETERMINISM.md`——**本版轴文档**：判据 J1–J3、逐产物实测表、易变字段、三条稳定化配方、未覆盖声明。
- `determinism_report.json`——本机实跑的机器可读报告（`runs[] / per_file_sha256 / identical / volatile_fields[] / byte_diff / stabilization / verdict`）。
- `references/OUTPUT_CONTRACT.md`——`result.json` 字段契约 + G1–G8 硬门（唯一权威）。
- `references/RUBRIC_MAP.md`——五维评分（40/25/15/10/10）→ 本包文件与机制。
- `references/failure-modes.md`——失败模式与降级策略（含本版 FM-D 系列）。
- `references/mechanism-spec.md` / `references/legend-encoding.md`——机制规格、命名、区室、箭头语义与数据编码。
- `scripts/main.py`（主入口）、`extract.py`、`layout.py`、`pathway_svg.py`、`mpl_backend.py`、
  `topology.py`、`legend_audit.py`、`validate_figure.py`、`check_contract.py`、`result_writer.py`、`model.py`、
  **`determinism.py`（本版新增）**。
- `assets/`——机制规格 schema、调色板、result 模板；`templates/relation-checklist-template.md`——CP3 核验载体。
- `examples/`——最小可运行示例（输入 + 期望输出说明 + 实跑 JSON 产物）；`README.md` / `TEST.md` / `COMPARE.md` / `worklog.md`。
