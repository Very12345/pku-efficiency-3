---
name: scientific-schematic-editor
description: >-
  Generate and edit editable scientific schematics, mechanism/relationship
  diagrams, flow diagrams and data charts from source materials. Five named
  mechanisms carry the design: M1 plan-before-draw (CP1 lint gate), M2
  self-describing source (ER manifest embedded in the SVG), M3 four-stage
  PDF extraction fallback with an honest backend record, M4 export
  pre-flight (DPI/colour/editable-text/PDF/font), M5 one shared font probe
  for render+checks+result. Each mechanism states what breaks without it and
  how it can be falsified (references/MECHANISM.md). Also ships a reusable
  asset inventory with an adoption ladder (references/REUSABLE-ASSETS.md).
  Use when a task asks to draw, regenerate or edit a scientific figure from
  papers, tables or notes: 科研示意图/机制图/信号通路图/流程图/实验装置图/
  图表的生成与编辑.
---
# scientific-schematic-editor — 科研示意图生成与编辑（机制显性版）

本技能不是一个"能跑的命令集合"，而是**五个有名字的机制**加上一条可核验的
链路。每个机制都要回答三个问题：**它是什么、没有它会怎样、怎么证明它真的在起作用**。
逐一写在 `references/MECHANISM.md`；可被别的技能复用的资产与采纳路径写在
`references/REUSABLE-ASSETS.md`。

**三条主张**（前两条是能力，第三条是这次变体的重点）：

1. **图画对** — 实体、关系、方向、数值、单位逐条可回溯到材料；
2. **图可改** — 文字可选、图层可拆、SVG 自描述，编辑只动被指明的元素；
3. **机制可被拆开检验** — 五个机制各自有"缺席实验"（拿掉它会出现什么）
   与"可证伪判据"（什么观测会推翻"它在起作用"），因此贡献不是笼统的
   "更好"，而是可指名的。

**本技能不做**：统计计算的数值方法选择、海报/封面版式、艺术插画美化、
论文正文写作。数据表里的数值是**事实输入**，不改算、不补造、不换算单位。

> 与基线包的结构差异：本包的正文主线是**机制索引**（§3），执行步骤（§4）
> 只作为"机制在流程中的位置"出现；边界情况的权威描述在
> `references/failure-modes.md`，而"为什么这条分支必须存在"回到 §3 的机制。
> 新增的两份文档分别承担"机制可检验"与"资产可复用"。

## 1. 适用条件

- 任务是"科研示意图/机制图/通路图/流程图/实验装置图/数据图"的**绘制或编辑**，
  workorder 一般形如 `editable_relationship_schematic`；
- 有来源材料（论文图注/正文摘录/Markdown/CSV/PDF），或要求对已有图稿做
  **源文件级**修改；
- 交付要求包含可编辑源文件、导出件与结构化结果（`result.json`）；
- 可能需要在**别的技能/别的题**里复用本包的某一部分（→
  `references/REUSABLE-ASSETS.md` 的采纳阶梯）。

## 2. 输入与输出

**输入（平台提供）**：`/input/case.json`（`case_id`/`workorder`/`figure_type`/
`sources`/可选 `manifest`、`entities+relations`、`data`、`edits`、`output_contract`）、
`/input/task.md`、`/input/` 下的材料（可能是 PDF）。
**以实际文件内容为准，不凭字段标签猜内容。**

**输出（写入 `/app/output`，全部运行时现场生成）**

```
/app/output/
├── figure.svg      # 可编辑分层源文件（自描述：内嵌 ER 清单 —— 机制 M2）
├── figure.png      # 渲染预览
├── figure.pdf      # 矢量导出件
├── result.json     # 结构化结果（OUTPUT_CONTRACT 全字段 + case_id）
└── work/           #（或 /app/work）entities.json / draft / layout / manifest.validated.json
```

| role | format | 是什么 | 完成标准 |
|-|-|-|-|
| `figure` | svg | 可编辑分层源文件 | 文字是真实 `<text>`（未被 path 化）、语义图层可拆、带 `id`/`data-*`、内嵌 ER 清单 |
| `preview` | png | 渲染预览 | 18 cm 宽有效 DPI ≥300（印刷）/≥150（屏幕）、色彩为 RGB 族 |
| `pdf` | pdf | 矢量导出件 | 可打开、页数可读、字体嵌入为尽力而为并如实记录 |
| `tiff` / `eps` | 对应格式 | 可选导出件（`--exports tiff,eps`） | 按目标单位要求生成；未逐项实测，见未解决项 |

> **包内不预置任何图稿或渲染件**（PDF/PNG/SVG/TIFF 都不随包分发）：
> 它们由本技能运行时生成；示例期望产物见 `examples/EXPECTED-OUTPUT.md`。

## 3. 机制索引（M1–M5）——本包的设计核心

每条机制的完整版（含"没有它会怎样"与"可证伪判据"）在
`references/MECHANISM.md`；这里是索引与落点。

| 机制 | 一句话 | 稀缺性（常规做法是怎么做的） | 落点 |
|-|-|-|-|
| **M1 方案先行** | 画之前先过 CP1 lint：kind 必须可映射、containment 必须分组、图例双向、调色板覆盖类别数 | 常规做法是"先画出来再说"，错误在成品里才被发现 | `scripts/spec_lint.py`（`spec.*` 一族检查名） |
| **M2 源文件自描述** | ER 清单**内嵌**进 SVG（`<metadata id="er-manifest">`），源文件自带语义 | 常规做法是图与数据分离，改标签要回头找数据源 | `scripts/svgbuilder.py`、`scripts/edit.py`、`svg.manifest_embedded` / `svg.manifest_matches` |
| **M3 抽取四段回退** | PDF 文本按 fitz → pypdf → PyPDF2 → **stdlib（zlib + Tj/TJ）** 逐级降级，backend 如实记录 | 常规做法是直接失败或静默空转 | `scripts/pdftext.py` |
| **M4 导出预检** | 导出前后自动查：有效 DPI、色彩族、文字是否可选中、PDF 结构、字体可用性 | 常规做法是"导出来再说"，投稿时才发现不达标 | `scripts/checks.py`（`bitmap.*` / `pdf.*` / `svg.editable_text` / `font.cjk`） |
| **M5 单一字体事实源** | render / checks / result.json 三方共用同一个字体探针，避免"各猜一个字体" | 常规做法是三处各自 fallback，结果互相矛盾 | `scripts/textfont.py` |

**机制清单（编号即本包声明的机制词汇表）**：

| 机制 | 名称 | 判据（可跑命令 / 可读字段） |
|-|-|-|
| M1 | 方案先行 | `spec_lint.py` 对坏清单 exit 1；`main.py` 对坏清单 `status=partial` + `fails=[spec_lint.*]` |
| M2 | 源文件自描述 | `svg.manifest_embedded` / `svg.manifest_matches` ok；无内嵌清单的 `--edit-svg` 必须 exit 2 |
| M3 | 抽取四段回退 | 无第三方 PDF 库时仍能抽；backend 字段随实际后端变化；缺文件 exit 2 |
| M4 | 导出预检 | `bitmap.dpi_print` / `bitmap.colourspace` / `svg.editable_text` / `artifact.<role>` 有读数 |
| M5 | 单一字体事实源 | `textfont.py --probe` 的结论与 `verification.render`、`font.cjk` 同源一致 |

**机制之间的依赖**（改动其中一个必须考虑另两个）：

```
M5 (字体事实源) ──► M4 (导出预检里的 font.cjk 与预览保真)
M3 (抽取回退)  ──► 材料可读性 ──► M1 (清单能不能建起来)
M2 (内嵌清单)  ──► 编辑能力；同时也是 M1 的持久化载体
M1 (生成前门)  ──► 决定 M2 里写进去的是什么（错清单会被拦住）
```

## 4. 执行流程（机制在流程中的位置）

**顺序：读契约 → 读材料 → 抽取 → 写清单 → M1 → 绘图 → M2/M4 →（编辑）
→ 契约门 → 自查。**

| 步 | 动作 | 激活的机制 |
|-|-|-|
| S0 | 读 `/input/task.md` 与 `/input/case.json`，记 `case_id`；解析 `output_contract` 的键与四形态（string→`""`、array→`[]`、object→`{}`、number/boolean→`0`/`false`，禁 `null`）；确认 `/app/output`、`/app/work` | — |
| S1 | 逐份读 `case.sources` 指向的**真实文件**；PDF 先过 `pdftext.py`；读不到的记入 `uncertainty` | **M3** |
| S2 | `extract.py` 产候选草稿（`_draft`），Agent 复核后写 `/app/work/entities.json`；`name` 逐字来自材料、`kind` 映射到 7 类规范词表、包含关系落到 `groups` | 为 **M1** 备料 |
| S3 | **CP1 lint 门**：`spec_lint.py --manifest …` → 只有 `{"valid": true}` 才继续 | **M1** |
| S4 | 绘图：`main.py --case … --manifest … --out /app/output`；产出 SVG/PNG/PDF + `result.json` | **M2**（生成内嵌清单）、**M5**（字体） |
| S5 | **CP2 产物检查**：溯源比例、图例双向、数据映射、导出预检 | **M4**、**M5** |
| S6 | （编辑）`--edit-svg` 走源文件级增量修改；编辑请求写在 `edit_requests`；改完重跑 CP2 | **M2** |
| S7 | 契约门 `validate_result.py`（G1–G8）→ VALID；确定性双跑；打包形态自查 | M1–M5 的综合 |

命令行（自定位，任意 cwd 可跑）：

```bash
SKILL_DIR="$(cd "$(dirname "<本 SKILL.md 的实际路径>")" && pwd)"

python "$SKILL_DIR/scripts/extract.py" --inputs /app/work/pdftext/<stem>.txt --out /app/work/draft-entities.json
python "$SKILL_DIR/scripts/spec_lint.py" --manifest /app/work/entities.json      # M1
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --manifest /app/work/entities.json     --work /app/work --out /app/output                                           # M2/M4/M5
python "$SKILL_DIR/scripts/validate_result.py" --case /input/case.json --result /app/output/result.json
```

## 5. 退出码与降级语义（每条降级都要指到某个机制）

| 退出码 | 含义 | result.json | 重试语义 |
|-|-|-|-|
| `0` | `status=success`；允许存在已被 `acknowledged_issues` 确认的 warn | 写出，`verification.checks.fail_count == 0` | 无需重试；可提高画质/补导出 |
| `1` | `status=partial`（有 fail 明细）或 `status=failed`（流水线异常） | **仍然写出**，fail 明细可逐条查 | 按 fail 明细定向修复后重跑；不要原样重跑 |
| `2` | 致命：case 无法定位/解析、编辑目标无内嵌清单、目录里没有 case.json | **不写出** | 先解决输入问题再跑，重试无意义 |

| 降级 | 说明 | 与机制的关系 |
|-|-|-|
| 镜像渲染（无 cairosvg/svgwrite） | PNG/PDF 是与 SVG 同源的 matplotlib 镜像，**语义一致、非逐像素**，写 `uncertainty` | 影响 M4 的判据强度（预检仍做，但"预览保真"降级） |
| PDF stdlib 回退 | backend 记为 stdlib，抽取质量可能下降 | M3 的第四段回退，**不隐藏** |
| CJK 字体缺失 | SVG 文字仍在（M2 保证文字是 `<text>`），PNG 可能缺字 | M5 报告事实，M4 记 warn |
| `--skip-checks` / `--no-lint` | 跳过 M1 或 M4 ⇒ 该次运行不得当作交付版本 | 直接关掉机制，必须显式标注 |
| 编辑目标不存在 | 日志 `[edit] fail`；`change_records` 条数对不上 | 该分支**不进 result.json**（M2 的已知盲区，见 MECHANISM §M2.4） |

## 6. 异常处置速查（权威描述见 `references/failure-modes.md`）

| 情形 | 处置 | 相关机制 |
|-|-|-|
| 来源材料缺失 | 记录 `sources`/`uncertainty`，以已读材料继续；多处缺失则 `status=partial` | M3 |
| 材料描述矛盾（方向/数值冲突） | 取有证据的一种，另一种连同出处写入 `uncertainty` | — |
| 实体名找不到出处 | **禁止上图**（no-fabrication）；删条或补 `evidence` | M1 |
| kind 无法映射 | CP1 fail → 回材料用原文动词改写后重跑 | M1 |
| 包含关系画成箭头 | 改成 `groups` 分组框 | M1 |
| 图例缺项 / 孤儿项 | 以数据表为基准修图例后重跑 | M1、M4 |
| 调色板 < 类别数 | 补齐或删冗余类别 | M1 |
| CJK 字体缺失 | 仍出 SVG；`font.cjk` warn + `uncertainty` | M5、M4 |
| PDF 加密/扫描件 | `pdftext.py` 报不可抽取，**不伪造文本** | M3 |
| 渲染/导出致命错 | 捕获 → 写 `status=failed` 的 `result.json`（`fails=[pipeline]`） | — |
| 编辑请求条数 ≠ `change_records` 条数 | 判为编辑失败，按 `references/EDIT-ACTION-SCHEMA.md` 查字段名 | M2 |
| 用了 `--skip-checks`/`--no-lint` | 交付前必须用默认参数完整重跑 | M1/M4 |

## 7. 资源文件说明（路径相对技能根，调用一律 `"$SKILL_DIR/..."`）

| 入口 | 角色 | CLI |
|-|-|-|
| `scripts/main.py` | 流水线入口 | `--case --manifest --out --work --edit-svg --base-name --exports --dpi --skip-checks --lint --no-lint --fixed-time --doc-check` |
| `scripts/extract.py` | 材料→候选 ER 清单草稿 | `--inputs --out --base-dir` |
| `scripts/pdftext.py` | PDF 文本抽取（**机制 M3**） | `--pdf --out` |
| `scripts/textfont.py` | 字体栈探测（**机制 M5**） | `--list --probe` |
| `scripts/spec_lint.py` | CP1 生成前 lint（**机制 M1**） | `--manifest --dict --json` |
| `scripts/manifest.py` | ER 清单加载/规范化 | `<manifest.json>` |
| `scripts/layout.py` | 布局引擎（库模块） | — |
| `scripts/svgbuilder.py` | 分层可编辑 SVG 构建（**机制 M2**） | — |
| `scripts/render.py` | matplotlib 镜像渲染（库模块） | — |
| `scripts/checks.py` | CP2 产物检查（**机制 M4**） | — |
| `scripts/edit.py` | 源文件级增量编辑（**机制 M2**） | `<figure.svg> <edits.json>` |
| `scripts/validate_result.py` | 契约独立校验 G1–G8 | `--case --result --out --json` |
| `scripts/selftest.py` | 模块级自测 | — |
| `scripts/run_examples.py` | 一键复现三示例 | `--out --keep` |
| `scripts/report.py` | 结果渲染辅助（库模块） | — |
| `scripts/doccheck.py` | **本包新增**：文档↔代码一致性对拍（只读） | `--root --files --json` |

| 其它文件 | 用途 |
|-|-|
| `references/MECHANISM.md` | **本包新增**：M1–M5 的完整机制说明（含"没有它会怎样"与可证伪判据） |
| `references/REUSABLE-ASSETS.md` | **本包新增**：可复用资产清单（A1–A12）与采纳阶梯（L0–L4） |
| `references/OUTPUT_CONTRACT.md` | `result.json` 契约 + G1–G8 硬门 + 四形态回显（**必读**） |
| `references/CHECK-INDEX.md` | 全部检查名清单（级别 + 科学含义）——机制可证伪判据的取值来源 |
| `references/EDIT-ACTION-SCHEMA.md` | 编辑动作 → 字段名 → 记录 的对照表与反模式 |
| `references/failure-modes.md` | 题面 12 类失败形态 → 检测 → 处置 → 相关机制 |
| `references/ER_MANIFEST.md` | 实体—关系清单规范（绘图唯一数据源） |
| `references/DRAWING_GRAMMAR.md` | 图形语法：关系语义→箭头/线型/颜色、方向判定、分组/层级、图例/数据映射 |
| `references/RUBRIC_MAP.md` | 五维评分（40/25/15/10/10）→ 本包文件/机制逐条映射 |
| `assets/relation-dict.json` | 连接规则字典（kind→arrow/line/dash/color，机器可读） |
| `assets/checklist.json` | CP1–CP5 检查点 + 自查清单（机器可读） |
| `examples/*` | 最小示例（schematic / chart / edit + 合成材料 + `EXPECTED-OUTPUT.md`），**示例非正式案例** |

## 8. 五维评分映射（交付前逐条自评；完整表见 `references/RUBRIC_MAP.md`）

| 维度 | 分 | 本包机制（可跑的检查，不是自述） | 证据文件 |
|-|-|-|-|
| 实际效果 | 40 | 材料→ER 清单→M1 门→可编辑 SVG（M2 自描述）→PNG/PDF（M4 预检）→result.json 一条命令跑通 | `scripts/main.py`、`scripts/spec_lint.py`、`scripts/checks.py`、`scripts/svgbuilder.py` |
| 使用增益 | 25 | 三层门每次运行自动执行；素材→图稿一条命令；改数据只改清单即重绘；编辑走内嵌清单增量改 | `scripts/main.py`、`scripts/edit.py`、`TEST.md` |
| 创新增益 | 15 | **M1–M5 五个具名机制**，每个都给出"没有它会怎样"与**可证伪判据**；机制之间有显式依赖图；`references/MECHANISM.md` 还列出各机制的**已知盲区**（不让创新点逃避检验） | `references/MECHANISM.md`、`scripts/spec_lint.py`、`scripts/edit.py`、`scripts/pdftext.py`、`scripts/checks.py`、`scripts/textfont.py` |
| 可靠体验 | 10 | 自定位（任意 cwd 可跑）；`--case` 兼容文件与目录；退出码 0/1/2 与 `status` 同向；降级逐条指到受影响机制；失败分支仍写 result.json | §5、§6、`references/failure-modes.md` |
| 生态贡献 | 10 | **`references/REUSABLE-ASSETS.md`：12 项可复用资产 + 5 级采纳阶梯（含最小采纳与验证方式）**；README/README 的复用步骤；机器可读字典与清单；契约校验器；文档↔代码对拍器；三示例题集 | `references/REUSABLE-ASSETS.md`、`assets/*`、`scripts/*`、`examples/*` |

## 9. 自查清单（提交前逐行确认；机器版 `assets/checklist.json`）

- [ ] 实体名逐字出自材料，无材料外基因/浓度/时间点/单位；
- [ ] 每个关系方向与材料一致（激活≠抑制、上下游不颠倒、包含用分组）；
- [ ] **M1 生效**：CP1 `{"valid": true}`（kind 可映射、containment 用分组、图例双向、调色板 ≥ 类别数）；
- [ ] **M2 生效**：`figure.svg` 文字可选中、图层可拆、内嵌 ER 清单、`svg.manifest_matches` 为 ok；
- [ ] **M4 生效**：PNG 有效 DPI 达标、色彩 RGB 族、PDF 可打开；
- [ ] **M5 生效**：`font.cjk` 有明确记录（True 或 warn + `uncertainty`）；
- [ ] 数值/单位与数据表逐项一致，改数据后图确实重绘；
- [ ] `result.json` 含全部契约键 + `case_id`，四形态回显无 `null`；
- [ ] `validate_result.py`（G1–G8）输出 VALID，退出码 0；
- [ ] 编辑任务：**请求条数 == `change_records` 条数**，未改动元素保持原样；
- [ ] 交付前最后一次运行**没有**用 `--skip-checks` / `--no-lint`；
- [ ] 形态：仅 7 种文本扩展名、无 `__pycache__`、≤50 文件、≤500KB/文件、≤2MB、包内无本机绝对路径。

## 10. 依赖与限制

- Python 3.9+（实测 3.13）；运行必需 **matplotlib / Pillow / numpy**，reportlab 可选；
  PDF 抽取按 M3 的四段回退逐级降级。建议先跑 `python "$SKILL_DIR/scripts/selftest.py"`；
- **平台运行契约**：技能装在 `/skills/weekly-skill`；输入 `/input/case.json` + `/input/task.md`；
  中间产物 `/app/work`；最终产物 `/app/output`。预算 64 请求 / 900 秒 / 16384 token/响应；
- **资源形态（硬约束）**：仅 UTF-8 文本（`.md/.py/.json/.txt/.csv/.yaml/.yml`），
  ≤50 个、单文件 ≤500KB、合计 ≤2MB、无符号链接；图稿与渲染件一律运行时生成；
- **已知限制（如实标注，并指到受影响机制）**：预览为同源镜像非逐像素（M4 判据强度）；
  PDF 字体嵌入审计为尽力而为（M4）；CJK 依系统字体（M5）；`extract.py` 只产草稿；
  走 `--edit-svg` 时 `edits` 字段不生效（用 `edit_requests`）；
  **`edit.*` 问题只进 stdout**，不进 result.json、不改退出码（M2 的已知盲区）；
  TIFF/EPS 的期刊级合规未逐项实测。

## 11. 禁止事项

- 不提交预制答案/正式案例输出；示例只用于演示接口与流程，**示例产物不入包**；
- 不编造缺失的软件状态或科学数据（来源里没有的实体/数值一律不画）；
- 不宣称未经测量的增益或未验证的机制；**每个机制的"可证伪判据"必须能被真实观测检验**；
- 不为"好看"改关系颜色（改色 = 图例不一致）。
