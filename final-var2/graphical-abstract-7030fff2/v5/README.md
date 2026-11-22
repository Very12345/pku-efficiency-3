# Graphical Abstract（图形摘要）Skill — 使用说明（v5 轴：多案例泛化与题集）

从研究材料（`case.json` + `task.md` + 材料文件）产出**单页图形摘要**：可继续编辑的**分层 SVG**、
PNG/PDF 预览、字段完整的 `result.json`。所有数值必须能在材料里定位，定位不到的进 `uncertainty`
并以「数值缺失」占位，**绝不编造**。

本版（v5）的重点是**泛化**：包内自带**三个不同题材**的可跑案例（纳米医学 / 材料能源 / 地球环境），
逐案给出输入、期望产出结构、可接受区间、难度层与实测结果，并把**这条链路在哪里会失效**
写成可复现的边界 —— 见 [`references/CASE-SET.md`](references/CASE-SET.md)。

---

## 1. 适用范围与不适用

**适用**：研究描述、实验记录、论文草稿、图表数据 → 单页视觉摘要 / 机制图 / 通路图 / 流程图；
编辑已有图稿；要求"可继续修改的源文件"；需要在多个题材上回归同一条链路。

**不适用**：论文正文写作、统计分析、实验设计、无 Q-M-R-C 叙事的纯数据可视化。
本 Skill 只对图面科学内容的表达、版式、可编辑性与导出质量负责。

---

## 2. 依赖（全部可选，缺失即降级且如实记录）

| 依赖 | 用途 | 缺失时的行为 |
|-|-|-|
| Python **3.8+**（标准库） | 抽取、版面、SVG、audit、契约自查 | 必需 |
| `matplotlib` | 首选栅格/矢量预览后端 | 回退 Pillow；`status` 降 `partial`，后端如实记录 |
| `Pillow` | 第二级 PNG 后端（**matplotlib 自身 `import PIL`**，装了 matplotlib 时它并非独立可达） | 与 matplotlib 一起缺失时落到纯 Python PNG |
| `pypdf` | 材料是 PDF 时抽取文本层 | 跳过该材料，`uncertainty` 写明"未取得可用文本层，数值不上画布" |
| 系统 CJK 字体 | 中文渲染 | 按候选路径探测（Windows/macOS/Linux）；找不到用默认字体，字体名如实记录 |

包内**不含任何二进制资源**（无 `.png/.pdf/.svg/.ttf/.pptx`），渲染件与 SVG 全部运行时生成。

## 3. 安装

把本目录整体复制到技能安装位置即可（官方评测容器为 `/skills/weekly-skill`）：

```bash
SKILL_DIR=/skills/weekly-skill
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/ga-out
```

脚本用 `scripts/common.py` 的 `SCRIPT_DIR = dirname(abspath(__file__))` 自定位技能根，
**不要求 cwd = 技能根**。

---

## 4. 参数（逐字对应 `scripts/` 里的真实 CLI）

### `scripts/main.py` — 出图主入口

| 参数 | 默认 | 说明 |
|-|-|-|
| `--case` | 必填 | `case.json` 路径（三个案例见 §6） |
| `--task` | `<case_dir>/task.md`（自动探测） | 任务说明 |
| `--material` | 取 `case.json.source_material` | 材料文件或目录（覆盖 case 声明） |
| `--out` | `<skill>/out` | 产物目录（官方运行时为 `/app/output`） |
| `--plan` | 无 | 设计方案 json（`scaffold.py` 出骨架 → 定稿 → 方案 lint） |
| `--raster-scale` | `constraints.raster_scale`（默认 2） | PNG 相对画布的倍数 |
| `--pdf` / `--no-pdf` | `constraints.pdf`（默认 true） | 是否产出 PDF 预览 |

退出码：`0` = 完成（`status ∈ {success, partial}`）；`1` = 硬输入错误（case/plan 读不了）；
`2` = 环境或内部错误（输出目录不可用、版面/SVG 失败、`status=failed`）。

### 其余脚本

| 脚本 | 参数 | 退出码 |
|-|-|-|
| `scripts/scaffold.py` | `--case`（必填）`--task` `--material` `--out`（必填） | `0` 成功 / `1` case 缺失或抽取失败 |
| `scripts/spec_lint.py` | `--spec` `--content`（规格门）；`--lint-plan --plan`（方案门） | `0` 通过 / `1` 有 problems |
| `scripts/check_contract.py` | `--result`（必填）`--case` | `0` 契约全覆盖且无 null / `1` 有缺口 / `2` 用法或文件错误 |

---

## 5. 输出清单

| 文件 | 内容 |
|-|-|
| `<case_id>_graphical_abstract.svg` | 可编辑分层 SVG：7 层 `layer:*`、真 `<text>`、元素带 `data-src`/`data-entity-id`/`data-role` |
| `<case_id>_graphical_abstract.png` / `.pdf` | 渲染预览（后端与字体如实记录；PDF 不可用时 `present:false` + `reason`） |
| `result.json` | 唯一评分产物：信封 18 键 + 案例 `output_contract` 全字段回显（禁 null） |
| `spec.json` / `content.json` | 与 SVG 同一几何的规格与规范化抽取结果 |
| `audit.json` / `render_log.json` | 六项红线自查 + 渲染日志 |

契约字段与硬性门 G1–G8 见 [`references/OUTPUT_CONTRACT.md`](references/OUTPUT_CONTRACT.md)。

---

## 6. 三个案例怎么跑（题集）

| 案例 | 命令（把 `$SKILL_DIR` 换成实际路径） |
|-|-|
| L1 纳米医学 | `python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/ga-l1` |
| L2 材料/能源 | `python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/cases/calab-perovskite-001/case.json" --out /tmp/ga-l2` |
| L3 地球/环境 | `python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/cases/urban-heat-001/case.json" --out /tmp/ga-l3` |

逐案的期望结构、可接受区间、难度层与实测结果在 [`references/CASE-SET.md`](references/CASE-SET.md)；
L3 是**故意构造**的"缺值 + 数值矛盾"案例，`status=partial` 是**正确**结果，不是失败。

---

## 7. 失败处理（六层判据，按顺序看）

1. **退出码**（`0/1/2`）
2. **`result.json.status`**：`partial` 就看 `uncertainty`；`failed` 看 `audit.checks`
3. **`audit.json` 六项红线**：`entity_coverage.missing`、`encoding_consistency.missing_from_canvas`、
   `bounds.outside_count`、`missing_values`、`four_element_coverage.missing`、`layer_naming.bad`
4. **`render_log.json`**：`backend` / `font` 与降级记录
5. **`check_contract.py` 退出码**：契约缺口与 null 违规
6. **换一个案例复跑**：同一现象在 L1 不出现、在 L2/L3 出现 ⇒ 多半是材料形态或单位写法的问题
   （对照 `references/CASE-SET.md` §4 的失效边界表）

---

## 8. 已知限制（摘；完整见 CASE-SET.md §4）

- 只有**独立成行**且形如 `键 = 数值 单位` 的行、以及**带真实箭头**（`->`/`→`）的行会被解析；
  散文里的数字、用"促进/抑制"连接的机制描述不会被自动抽取。
- 材料与 `case.json` 数值不一致时**不裁决**：首见优先，并把两处数值与各自 `src` 写进 `uncertainty`。
- 扫描件（无文本层）材料会被跳过并如实记录，**不会**从图片里编造数值。
- 带比较符/区间的值（`≈13.6 µg/mL`、`0.8–1.2 mg/L`）不会被解析为数值。
- 三个案例是合成示意，不是平台正式案例。

## 9. 维护

- 新增案例：按 `SKILL.md` §4 的"四件事"做（输入三件套 + 数值双向可定位 + 契约四形态 + 真跑记录），
  并把实测结果补进 `references/CASE-SET.md`。
- 新增图层：先在 `references/layer-naming.md` 登记，再同步 `scripts/audit.py` 的 `EXPECTED_LAYERS`。
- 新增契约字段：走"契约字段"通道（四形态之一），**不要塞进信封保留键**。
- 改动 `scripts/**` 后必须复跑三案冒烟 + `TEST.md` 的判据，并在 `TEST.md` 追加一行实测记录。
