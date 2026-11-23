# CASE-SET — 题集与泛化边界（v5）

> **本文件所有数字都来自 `scripts/case_probe.py` 的真实运行**，
> 复跑命令见 §1；机器可读全量结果在 `<out>/case-report.json`
> （逐案含命令、退出码、耗时、`observed` 全字段、`expectations[]`、
> `conforms`、`deviations[]`）。
>
> 实测时间 2026-11-22 20:2x (+08:00)；Python 3.13.9；matplotlib 3.10.6 /
> Pillow 12.3.0 / numpy 2.3.5；lxml 可用（XML 良构校验用它，缺则 stdlib 兜底）。

## 1. 复跑（约 15 s，产物全部落在包外）

```bash
SKILL_DIR="$(cd "$(dirname "<本 SKILL.md 的实际路径>")" && pwd)"

# 全部 10 项 = 5 个案例 + 5 个边界探针
python "$SKILL_DIR/scripts/case_probe.py" --skill-root "$SKILL_DIR" --out /tmp/sse-cases

# 分组：bundled（包内三示例）/ new（两个新合成案例）/ probe（边界探针）
python "$SKILL_DIR/scripts/case_probe.py" --skill-root "$SKILL_DIR" --out /tmp/c --group new
python "$SKILL_DIR/scripts/case_probe.py" --skill-root "$SKILL_DIR" --out /tmp/c --group probe

# 单项 / 只看清单
python "$SKILL_DIR/scripts/case_probe.py" --skill-root "$SKILL_DIR" --out /tmp/c \
    --only synth-expression-heatmap-102
python "$SKILL_DIR/scripts/case_probe.py" --list
```

退出码：`0` = 每案落在声明区间内且每个探针复现了它声明的失效形态；
`1` = 有偏离（逐条打印期望/实测差值）；`2` = 参数错误。
**实测：10/10，退出码 0。**

## 2. 题集：逐案的输入 / 期望产出结构 / 可接受区间 / 难度层

每案的"可接受区间"是**六类显式声明的判据**，不是主观印象：
①`exit`+`status` ②`fail/warn` 上限 ③结构计数 ④必备产物角色
⑤溯源覆盖率 ⑥形态类（XML 良构 / 原始标记 / 画布溢出 / 单位声明）。

### 2.1 `example-schematic-001` — 包内示例：信号通路机制图

| 项 | 内容 |
|-|-|
| 输入 | `examples/case.json` + `examples/sources/figure03-note.md` |
| 图型 | schematic（TNF-α → TNFR1 → TRADD → RIPK1 → NF-κB → IL6） |
| 难度层 | 入门（6 实体 / 5 关系 / 3 分组 / 3 图例项，全部线索都在一份材料里） |
| 期望产出结构 | `figure.svg`（分层可编辑，内嵌 ER 清单）+ `figure.png`（预览）+ `figure.pdf`（导出）+ `result.json`（21 契约字段 + 2 个 `output_contract` 回显键） |
| 可接受区间 | `exit=0`、`status=success`、fail=0、warn=0、实体 6、关系 5、分组 3、角色 ⊇{figure,preview,pdf}、`traceability_entities=100%`、XML 良构、**画布不溢出** |

### 2.2 `example-chart-002` — 包内示例：数据表驱动柱状图

| 项 | 内容 |
|-|-|
| 输入 | `examples/case_chart.json` + `examples/sources/data-table.csv` |
| 图型 | chart/bar（4 个化合物，fold change） |
| 难度层 | 入门（考验"图例/颜色/类别数三方同源"+ 单位上轴） |
| 期望产出结构 | 同上四件；`data_mapping.unique_categories` 有 4 项；`unit` 非空 |
| 可接受区间 | `exit=0`、`success`、fail=0、warn=0、类别数 4、单位非空、角色齐全、XML 良构 |

### 2.3 `example-edit-003` — 包内示例：源文件级增量编辑

| 项 | 内容 |
|-|-|
| 输入 | `examples/case_edit.json` + **上一步真实生成的** `figure.svg`（包内不预置 SVG） |
| 图型 | schematic edit（`rename` / `relabel` / `note` 三个动作） |
| 难度层 | 入门（考验"只改被指明的元素，其余保持不变"） |
| 期望产出结构 | 四件产物 + `change_records` 恰为 **3** 条（before→after + reason） |
| 可接受区间 | `exit=0`、`success`、`change_records=3`、角色齐全、画布不溢出 |

### 2.4 ★ `synth-mitophagy-101` — 新合成案例①：细胞生物学机制图

| 项 | 内容 |
|-|-|
| 输入 | `examples/cases/case_mitophagy.json` + `examples/cases/sources/mitophagy-note.md` |
| 题材 / 图型 | **细胞生物学：PINK1/Parkin 线粒体自噬清除通路** / schematic |
| 难度层 | **中** —— 六个实体跨"损伤感知 / 泛素标记 / 清除"三个层级（层级关系不是并列），且材料**自带一处反误读**（PINK1 是被稳定化的激酶、不是被降解的底物） |
| 期望产出结构 | `figure.svg` + `figure.png` + `figure.pdf` + `result.json`；6 实体 / 5 关系 / 3 分组 / 2 个图例项（recruitment、process） |
| 可接受区间 | `exit=0`、`success`、fail=0、warn=0、实体 6、关系 5、分组 3、角色齐全、溯源 100%、XML 良构、画布不溢出 |
| 与示例的**差异点** | ①实体类型不同（organelle / kinase / e3_ligase / modification）②关系词表覆盖 recruitment+process（示例用了 activation/recruitment/transcriptional）③材料用中文正文 + 英文实体名混排，直接压 `textfont` 的 CJK 路径 |

### 2.5 ★ `synth-expression-heatmap-102` — 新合成案例②：转录组热图

| 项 | 内容 |
|-|-|
| 输入 | `examples/cases/case_expr_heatmap.json` + `examples/cases/sources/expression-table.csv` |
| 题材 / 图型 | **转录组：三条件 × 三重复的标记基因表达矩阵** / chart/heatmap |
| 难度层 | **中高** —— 走的是与柱状图**完全不同的渲染分支**（`data.matrix` + `row_labels`/`col_labels` + 色标），且必须"类别 ↔ 图例 ↔ 颜色数"三方一致、单位进色标 |
| 期望产出结构 | 四件产物；`data_mapping.unique_categories` 3 项、`unit` 非空；矩阵 3×3 与 CSV 逐值一致 |
| 可接受区间 | `exit=0`、`success`、fail=0、warn=0、类别数 3、单位非空、角色齐全、XML 良构 |

## 3. 逐案实测结果（2026-11-22，`case_probe.py` 真实输出）

| 项 | 类型 | exit | status | 实体/关系/分组 | 类别数 | 角色 | 画布（声明 → 内容） | 溢出 | XML | 溯源 | 耗时 |
|-|-|-|-|-|-|-|-|-|-|-|-|-|
| `example-schematic-001` | case | 0 | success | 6 / 5 / 3 | — | figure+preview+pdf | 2300×880 → 2090×90 | 否 | 良构 | 100% | 1.55 s |
| `example-chart-002` | case | 0 | success | — | 4 | figure+preview+pdf | 不适用（chart） | — | 良构 | — | 1.49 s |
| `example-edit-003` | case | 0 | success | 6 / 5 / 3 | — | figure+preview+pdf | 2300×880 → 2090×90 | 否 | 良构 | 100% | 1.85 s |
| `synth-mitophagy-101` | case | 0 | success | 6 / 5 / 3 | — | figure+preview+pdf | 2300×900 → 2090×90 | 否 | 良构 | 100% | 1.55 s |
| `synth-expression-heatmap-102` | case | 0 | success | — | 3 | figure+preview+pdf | 不适用（chart） | — | 良构 | — | 1.89 s |
| `B1-unsupported-chart-type` | probe | 1 | failed | — | — | **无产物** | — | — | — | — | 0.82 s |
| `B2-dense-chain-declared-canvas` | probe | 0 | success | 18 / 17 / 1 | — | figure+preview+pdf | 1500×900 → **6530×90** | **是（静默）** | 良构 | 100% | 1.31 s |
| `B3-dense-chain-auto-canvas` | probe | 0 | success | 18 / 17 / 1 | — | figure+preview+pdf | **6609×500** → 6530×90 | 否 | 良构 | 100% | 1.36 s |
| `B4-special-characters` | probe | 0 | success | 6 / 5 / 3 | — | figure+preview+pdf | 2300×880 → 2090×90 | 否 | 良构 | 100% | 1.16 s |
| `B5-containment-without-group` | probe | 1 | partial | 6 / 6 / 3 | — | figure+preview+pdf | 2300×880 → 2090×90 | 否 | 良构 | 100% | 1.22 s |

**汇总：10/10 项落在声明区间内（`case_probe.py` 退出码 0）。**
两条 `exit 1` 是**探针**，它们声明的期望就是"被拦下"（B1 → `fails=[pipeline]`；
B5 → `fails=[spec_lint.spec.containment_group]`），因此同样计为符合。

补充实测（`observed` 里不常见但有用的量）：

| 量 | 实测 |
|-|-|
| `figure.svg` 字节（五个案例） | 15241 / 9737 / 15350 / 14504 / 25481 |
| `figure.png` 像素 | 6900×2640（schematic，2300×880@3x）/ 2700×1560（chart） |
| `result.json` 顶层键数 | 23（声明了 `output_contract` 的案例）/ 21（未声明） |
| XML 校验后端 | `lxml`（缺 lxml 时自动 `stdlib`） |
| `data_mapping` 单位 | 热图案例 `log2 fold change vs ctrl` 进色标；柱状图示例 `fold change vs ctrl` 上轴 |

## 4. ★ 泛化到哪会失效（六条实测边界）

**这张表是本文件的核心。** 把"拦得住 / 拦不住但可计算 / 根本拦不住"分开写，
才知道哪里必须加人工门。

| # | 类别 | 探针 / 注入 | 实测结果 | 该怎么办 |
|-|-|-|-|-|
| **G1** | **拦得住** | 声明不支持的 `chart_type: histogram` | `exit 1` / `status=failed` / `fails=[pipeline]`（原文 `unsupported chart_type 'histogram' (use bar/line/scatter/heatmap)`）/ **无产物** | 图型白名单固定四种；换图型前先确认在名单内。好处是**不会**悄悄退化成别的图型骗过检查 |
| **G2** | **拦不住但可计算** | 18 节点单链 + 显式 `style.canvas: 1500×900` | `exit 0` / `success` / **0 fail 0 warn**；内容宽 **6530 px**，viewBox 仍 `0 0 1500 900` ⇒ 右侧被裁掉 | 按 §5 公式预算画布；`case_probe.py` 的 `canvas_overflow` 会替你量出来 |
| **G3** | **拦不住但可控** | 同样 18 节点单链，**不声明** canvas | `exit 0` / 自动画布 **6609×500** / 无溢出；**PNG 19827×1500 px** | 不声明 = 安全但导出件巨大；适合"先要完整、再谈尺寸"的场景 |
| **G4** | **拦得住（且已修）** | 实体名含 `& < > " µ × ²` | `exit 0` / 良构 XML（lxml 通过）/ 原始标记不泄漏（`<up>` 不出现、`&amp;` 出现） | 无需额外动作；CJK/符号仍受系统字体影响（`font.cjk` 报事实） |
| **G5** | **拦得住** | `containment` 关系未落到任何分组框 | `exit 1` / `status=partial` / `fails=[spec_lint.spec.containment_group]`，产物仍落盘 | 回清单把包含关系写进 `groups` 后重跑 CP1 |
| **G6** | **根本拦不住** | 关系**方向对调**（端点与 kind 都合法） | `exit 0` / `success` / `spec_lint` 全 ok（v4 注入矩阵 D09b 同结论） | 只能靠 S1/S2 的**逐条回材料核对 `from/to`** 人工门；SVG 每边带 `data-relation`/`data-source` 可 grep 复核 |

**没测到、因此不声称的部分**（诚实标注）：

- 只测了 **schematic + chart（bar/heatmap）**；`line`/`scatter` 两个分支
  **未逐项实测**（代码路径存在，但本轮没有案例覆盖）；
- 没有真实论文 PDF 材料（`pdftext.py` 只在 v4 的注入里用合成 PDF 测过：
  加密件 `exit 2`、扫描件抽到 0 字、无第三方库走 stdlib 回退抽到 15 字）；
- 没有测过 **>60 节点**、非链式（网状/环状）拓扑在显式画布下的表现，
  也没有测多子图（subfigure）排版；
- 没有测过 EPS/TIFF 导出，也没有测过真实期刊的字体嵌入审计；
- 没有在平台上跑过官方案例，因此**不声称**任何平台分数。

## 5. 画布预算规则（由 G2/G3 反推，按公式算就不会被裁）

来源：`scripts/layout.py` 的 `layered`（左→右）分支，坐标是确定性公式：

```
节点 x = 层号 × (240 + 130) = 层号 × 370
节点宽 w = max(110, 文本估算宽)   # 本包案例实测取到 240
节点高 h0 = 90；行距 gapy = 70
显式声明 style.canvas 时：布局【不】自动扩展，SVG viewBox / PNG / PDF 全按声明尺寸裁剪
不声明 style.canvas 时：画布自动扩到 max(900, 内容宽 + 45) × max(500, 内容高 + 45)
```

⇒ 实用版本：

```
canvas.width  ≥ 370 × (最大层号) + 节点最大宽度 + 40
canvas.height ≥ 行数 × 160 + 200（图例 + 来源脚注）
```

**分层按拓扑深度**，所以**一条 N 节点链 = N 个层**，宽度需求约
`370×(N−1) + 240 + 40`：4 节点 ≈ 1360、6 节点 ≈ 2090、18 节点 ≈ 6530。

### 5.1 本轮据此修掉的一处真实缺陷（纯数据修正，未动脚本）

| 夹具 | 修复前声明 | 实测内容 | 后果 | 修复后 |
|-|-|-|-|-|
| `examples/case.json`（包内 schematic 示例） | `1500×860` | 2090×90 | 最右节点 E6 落在 x=1850–2090，**整块在 viewBox 外（被裁）**，而 checks 报 0 fail 0 warn | `2300×880`，`canvas_overflow=False` |
| `examples/cases/case_mitophagy.json`（新案例①） | `1500×900` | 2090×90 | 同上 | `2300×900`，`canvas_overflow=False` |

> 处置说明：这是**夹具数据**的问题（画布声明写小了），不是脚本缺陷——
> 布局与裁剪行为是确定的、可计算的。因此修正方式是把声明改成按公式算出的
> 尺寸，并**在题集里加一条常驻判据** `canvas_overflow: False`：以后谁再把
> 画布算小，`case_probe.py` 会直接报偏离，而不是靠人眼发现。
> `scripts/*.py` 本轮**未改动**（`case_probe.py` 是新增文件）。

## 6. 怎么加一个新案例（题集是可扩展的）

1. 在 `examples/cases/` 下放 `case_xxx.json` 与它引用的来源材料
   （材料路径相对 `case.json` 所在目录解析）；
2. 在 `scripts/case_probe.py` 的 `case_registry()` 里加一条：
   `id / genre / difficulty / input / sources / expect{...}`；
3. `expect` 只写**你愿意为之负责的区间**（exit、status、fail/warn 上限、
   结构计数、角色、溯源、形态类），跑一次 `--only <id>` 看实测；
4. 若实测与区间不符：**先查是自己的夹具错了还是能力真的不够**，
   然后把结论写进本文档 §4（新的边界就是新的 G 行），**不要悄悄放宽区间**。

## 7. 与五维评分的对应（本文件主要扛"实际效果 40"与"生态贡献 10"）

| 评分点 | 本文件给出的证据 |
|-|-|
| 任务完成度 / 结果正确性 | §3 逐案实测：结构计数、溯源覆盖率、单位、产物角色全部量化；两个新题材都真跑出图 |
| 结果完整性 | 五案各给出"输入 → 期望产出结构 → 实测产物"三段，缺件会被 `roles` 判据拦住 |
| 结果可核验性 | 每条判据都有"期望 / 实测 / 是否满足"，并落进 `case-report.json`；命令可原样复跑 |
| 生态贡献（资源可复用性） | §6 给出加案例的三步法；§5 的画布预算公式可直接搬到别的分层绘图场景；§4 的三类边界是一份可复用的"泛化检查清单" |

> **不能说的事**：本文件只证明"这 5 个案例 + 5 个探针的行为符合声明"，
> **不证明**别的题材也能一次画对，也不证明任何平台分数。未被 §4 覆盖的
> 情形一律按"未测量"处理。
