# Graphical Abstract（图形摘要）Skill — 使用说明（v4 轴：失败注入与恢复演练）

从研究材料（`case.json` + `task.md` + 材料文件）产出**单页图形摘要**：可继续编辑的
**分层 SVG**、PNG/PDF 预览、以及字段完整的 `result.json`。所有数值必须能在材料里定位，
定位不到的一律进 `uncertainty` 并以「数值缺失」占位，**绝不编造**。

本版（v4）在同样的出图链路上增加一件事：**把失败真的造出来跑一遍**。
`scripts/fault_inject.py` 对输入 / 模板 / 依赖 / 契约四形态注入 23 条用例，每次都用子进程
跑真实主流程，抓回 `退出码 / status / uncertainty`，逐条判定是否**静默失败**。
逐行实测结果与"查出缺陷 → 纯增量修复 → 复跑验证"的对照见
[`references/FAULT-MATRIX.md`](references/FAULT-MATRIX.md)。

---

## 1. 适用范围与不适用

**适用**：研究描述、实验记录、论文草稿、图表数据 → 单页视觉摘要 / 机制图 / 通路图 / 流程图；
编辑已有图稿；要求"可继续修改的源文件"；要求验证这条链路在材料缺失、依赖缺失、契约异常下的行为。

**不适用**：论文正文写作、统计分析、实验设计、无 Q-M-R-C 叙事的纯数据可视化。
本 Skill 只对图面科学内容的表达、版式、可编辑性、导出质量与失败行为负责。

---

## 2. 依赖（全部可选，缺失即降级且如实记录）

| 依赖 | 用途 | 缺失时的行为 |
|-|-|-|
| Python **3.8+**（标准库） | 抽取、版面、SVG、audit、契约自查、注入演练 | 必需 |
| `matplotlib` | 首选栅格/矢量预览后端 | 回退 Pillow；`status` 降 `partial`，`render_log.backend` 如实记录 |
| `Pillow` | 第二级 PNG 后端（**注意：matplotlib 自身 `import PIL`**，装了 matplotlib 时它并非独立可达） | 与 matplotlib 一起缺失时落到第三级 |
| `pypdf` | 材料是 PDF 时抽取文本层 | 跳过该材料，`uncertainty` 写明"未取得可用文本层，数值不上画布" |
| 系统 CJK 字体 | 中文渲染 | 按候选路径探测（Windows/macOS/Linux）；找不到用默认字体，字体名如实记录 |

包内**不含任何二进制资源**（无 `.png/.pdf/.svg/.ttf/.pptx`），渲染件与 SVG 全部运行时生成。

## 3. 安装

把本目录整体复制到技能安装位置即可（官方评测容器为 `/skills/weekly-skill`）：

```bash
SKILL_DIR=/skills/weekly-skill          # 或本机任意解压目录
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/ga-out
```

脚本用 `scripts/common.py` 的 `SCRIPT_DIR = dirname(abspath(__file__))` 自定位技能根，
**不要求 cwd = 技能根**。

---

## 4. 参数（逐字对应 `scripts/` 里的真实 CLI）

### `scripts/main.py` — 出图主入口

| 参数 | 默认 | 说明 |
|-|-|-|
| `--case` | 必填 | `case.json` 路径 |
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

### `scripts/fault_inject.py` — 四形态失败注入（本轴新增）

| 参数 | 默认 | 说明 |
|-|-|-|
| `--out` | 必填 | 报告目录（**必须在包外**）：`fault_report.json` + 沙箱 |
| `--only` | 全部 | 只跑某一类（`input` / `template` / `dependency` / `contract`）或某一条（如 `F15`） |
| `--fail-on` | `silent` | `silent` 只把静默失败判 1；`strict` 任何不符期望即判 1；`none` 只出表 |
| `--keep` | 关 | 保留沙箱目录以便人工检查 |
| `--verbose` | 关 | 打印每条用例的 stdout/stderr 摘要 |

退出码：`0` = 全部符合期望；`1` = 有静默失败（或 `strict` 下有 mismatch）；`2` = 用法/环境错误。
**注入只发生在包外沙箱**：脚本把 `<skill>/scripts` 复制到临时目录再跑，
并设置 `PYTHONDONTWRITEBYTECODE=1`，包内不产生 `__pycache__`、不写任何文件。

---

## 5. 输出清单

| 文件 | 内容 |
|-|-|
| `<case_id>_graphical_abstract.svg` | 可编辑分层 SVG：7 层 `layer:*`、真 `<text>`、元素带 `data-src`/`data-entity-id`/`data-role` |
| `<case_id>_graphical_abstract.png` / `.pdf` | 渲染预览（后端与字体如实记录；PDF 不可用时 `present:false` + `reason`） |
| `result.json` | 唯一评分产物：信封 18 键 + 案例 `output_contract` 全字段回显（禁 null） |
| `spec.json` / `content.json` | 与 SVG 同一几何的规格与规范化抽取结果 |
| `audit.json` / `render_log.json` | 六项红线自查（覆盖率/编码一致性/越界/缺值/四要素/图层命名）+ 渲染日志 |

契约字段与硬性门 G1–G8 见 [`references/OUTPUT_CONTRACT.md`](references/OUTPUT_CONTRACT.md)。

---

## 6. 失败处理（六层判据，按顺序看）

1. **退出码**（`0/1/2`，见上表）
2. **`result.json.status`**：`partial` 就看 `uncertainty`；`failed` 看 `audit.checks`
3. **`audit.json` 六项红线**：`entity_coverage.missing`、`encoding_consistency.missing_from_canvas`、
   `bounds.outside_count`、`missing_values`、`four_element_coverage.missing`、`layer_naming.bad`
4. **`render_log.json`**：`backend` / `font` 与降级记录
5. **`check_contract.py` 退出码**：契约缺口与 null 违规
6. **`fault_inject.py --only <类>`**：怀疑输入/模板/依赖/契约行为时直接注入复现

`references/failure-modes.md` 给出「失败模式 ↔ 决策规则 D1–D20 ↔ 注入用例 F00–F22」的三者互查表。

---

## 7. 已知限制

- 渲染链真实可达的两级是「matplotlib → 纯 Python PNG」：matplotlib 自身依赖 PIL，
  屏蔽 Pillow 会连带 matplotlib 失效（矩阵 §3 记录）。三级都不可用时不会再降级，而是 `status=failed`。
- 材料抽取依赖文本结构与 PDF 文本层；扫描件（无文本层）会被跳过并如实记录，数值不上画布。
- 注入演练只覆盖本包可控的四类缺陷，**平台侧故障（挂载缺失、配额、容器超时）不在其内**。
- 四要素/图层/契约检查是结构判据，不代替领域科学判断；材料本身的结论真伪由人复核。
- 示例数据为合成示意，与平台正式案例无关。

## 8. 维护

- 新增图层：先在 `references/layer-naming.md` 登记，再同步 `scripts/audit.py` 的 `EXPECTED_LAYERS`。
- 新增契约字段：走"契约字段"通道（四形态之一），**不要塞进信封保留键**。
- 改动 `scripts/**` 后必须复跑：`python "$SKILL_DIR/scripts/fault_inject.py" --out /tmp/fi --fail-on strict`
  与 `TEST.md` 里的冒烟命令；`references/FAULT-MATRIX.md` 的行数用 `diff | grep -c` 复核。
- 规则编号（D1–D20 / F1–F9 / P1）在 `SKILL.md`、`references/failure-modes.md`、
  `references/FAULT-MATRIX.md` 三处必须一致。
