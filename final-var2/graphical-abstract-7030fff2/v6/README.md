# Graphical Abstract（图形摘要）Skill — 全维合并版使用说明

一个入口出图：研究材料 → 单页图形摘要（问题 / 方法 / 结果 / 结论）→ **可编辑分层 SVG** +
PNG/PDF 预览 + 字段完整的 `result.json`。数值必须能追到材料；追不到的只进 `uncertainty`
并以「数值缺失」占位，**绝不编造**。

本包是五条轴的**并集**（决策显性化 / 增益可验证 / 机制与复用 / 失败注入 / 多案例泛化），
每条轴的增量都可独立复核，索引见 `SKILL.md` 顶部表格。

---

## 1. 依赖（全部可选，缺失即降级且如实记录）

| 依赖 | 用途 | 缺失时的行为 |
|-|-|-|
| Python **3.8+**（标准库） | 抽取、版面、SVG、audit、契约自查、注入演练、增益测量 | 必需 |
| `matplotlib` | 首选栅格/矢量预览后端 | 回退 Pillow；`status` 降 `partial`，后端如实记录 |
| `Pillow` | 第二级 PNG 后端（**matplotlib 自身 `import PIL`**，装了 matplotlib 时并非独立可达） | 与 matplotlib 一起缺失时落到纯 Python PNG |
| `pypdf` | 材料是 PDF 时抽文本层 | 跳过该材料，`uncertainty` 写明"未取得可用文本层，数值不上画布" |
| 系统 CJK 字体 | 中文渲染 | 按候选路径探测（Windows/macOS/Linux）；找不到用默认字体并如实记录 |

包内**无任何二进制资源**（无 `.png/.pdf/.svg/.ttf/.pptx`），渲染件与 SVG 全部运行时生成。

## 2. 安装

```bash
cp -r graphical-abstract-7030fff2 /skills/weekly-skill    # 官方评测容器位置
SKILL_DIR=/skills/weekly-skill
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/ga-out
```

脚本用 `scripts/common.py` 的 `SCRIPT_DIR = dirname(abspath(__file__))` 自定位技能根，
**不要求 cwd = 技能根**。

---

## 3. 参数（逐字对应 `scripts/` 里的真实 CLI）

### `scripts/main.py` — 出图主入口

| 参数 | 默认 | 说明 |
|-|-|-|
| `--case` | 必填 | `case.json` 路径 |
| `--task` | `<case_dir>/task.md`（自动探测） | 任务说明 |
| `--material` | 取 `case.json.source_material` | 材料文件或目录（覆盖 case 声明） |
| `--out` | `<skill>/out` | 产物目录（官方运行时为 `/app/output`） |
| `--plan` | 无 | 设计方案 json（方案先行；`scaffold.py` 出骨架） |
| `--raster-scale` | `constraints.raster_scale`（默认 2） | PNG 相对画布的倍数 |
| `--pdf` / `--no-pdf` | `constraints.pdf`（默认 true） | 是否产出 PDF 预览 |

退出码：`0` 完成（success/partial）；`1` 硬输入错误（case/plan 读不了）；`2` 环境或内部错误
（输出目录不可用、版面/SVG 失败、`status=failed`）。

### 其余脚本

| 脚本 | 参数 | 退出码 |
|-|-|-|
| `scripts/scaffold.py` | `--case`（必填）`--task` `--material` `--out`（必填） | `0` / `1` |
| `scripts/spec_lint.py` | `--spec` `--content`（规格门）；`--lint-plan --plan`（方案门） | `0` 通过 / `1` 有 problems |
| `scripts/check_contract.py` | `--result`（必填）`--case` | `0` / `1` / `2` |
| `scripts/fault_inject.py` | `--out`（必填）`--only` `--fail-on {silent,strict,none}` `--keep` `--verbose` | `0` 全符合期望 / `1` 有静默失败（或 strict 下 mismatch）/ `2` 用法错误 |
| `scripts/gain_harness.py` | `--out` `--case` `--material` `--label` `--json` `--compare DIR_A DIR_B` | `0` |

`fault_inject.py` 与 `gain_harness.py` 都**只读本包**：前者把 `scripts/` 复制到包外沙箱再跑子进程
（并设 `PYTHONDONTWRITEBYTECODE=1`），后者只测量已有输出目录，不产生任何图。

---

## 4. 输出清单

| 文件 | 内容 |
|-|-|
| `<case_id>_graphical_abstract.svg` | 可编辑分层 SVG：7 层 `layer:*`、真 `<text>`、元素带 `data-src`/`data-entity-id`/`data-role` |
| `<case_id>_graphical_abstract.png` / `.pdf` | 渲染预览（后端/字体如实记录；PDF 不可用时 `present:false` + `reason`） |
| `result.json` | 唯一评分产物：信封 18 键 + 案例 `output_contract` 全字段回显（禁 null） |
| `spec.json` / `content.json` | 与 SVG 同一几何的规格与规范化抽取结果 |
| `audit.json` / `render_log.json` | 六项红线自查 + 渲染日志 |

契约与 G1–G8 硬性门：`references/OUTPUT_CONTRACT.md`。

---

## 5. 四条验收命令（判据都是退出码或字段）

```bash
# ① 出图（L1 最小示例）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/ga-l1
# ② 契约门
python "$SKILL_DIR/scripts/check_contract.py" --result /tmp/ga-l1/result.json --case "$SKILL_DIR/examples/case.json"
# ③ 失败注入（23 条，真跑；strict 判级）
python "$SKILL_DIR/scripts/fault_inject.py" --out /tmp/ga-fi --fail-on strict
# ④ 增益测量（只读）
python "$SKILL_DIR/scripts/gain_harness.py" --out /tmp/ga-l1 --case "$SKILL_DIR/examples/case.json" \
       --material "$SKILL_DIR/examples/material.md" --label A-skill
```

题集三案（L1 纳米医学 / L2 材料能源 / L3 地球环境）的命令见 `references/CASE-SET.md` §5。

---

## 6. 失败处理（六层判据，按顺序看）

1. **退出码**（`0/1/2`）
2. **`result.json.status`**：`partial` 查 `uncertainty`；`failed` 查 `audit.checks`
3. **`audit.json` 六项红线**：`entity_coverage.missing`、`encoding_consistency.missing_from_canvas`、
   `bounds.outside_count`、`missing_values`、`four_element_coverage.missing`、`layer_naming.bad`
4. **`render_log.json`**：`backend` / `font` 与降级记录
5. **`check_contract.py`**：契约缺口与 null 违规
6. **`fault_inject.py --only <类>`**：怀疑输入/模板/依赖/契约行为时直接注入复现

失败模式 ↔ 决策规则 D1–D20 ↔ 注入用例 F00–F22 的三者互查表在 `references/failure-modes.md` §3。

---

## 7. 已知限制

- 渲染链真实可达的是「matplotlib → 纯 Python PNG」：matplotlib 依赖 PIL，屏蔽 Pillow 会连带失效。
- 抽取只认独立成行的 `键 = 数值 单位` 与带真实箭头的机制行；散文里的数字不会抽取。
- 材料与 case 数值矛盾**不自动裁决**（首见优先 + 冲突留痕，两处 `src` 并列）。
- 扫描件（无文本层）跳过并记录，不编造数值；带比较符/区间的值（`≈`、`0.8–1.2`）不解析。
- 注入演练只覆盖本包可控的四类缺陷；平台侧故障不在其内。
- 三个示例案例为合成示意，不是平台正式案例，不代表正式成绩。

## 8. 维护

- 新增图层：先登记 `references/layer-naming.md`，再同步 `scripts/audit.py` 的 `EXPECTED_LAYERS`。
- 新增契约字段：走"契约字段"通道（四形态之一），**不要塞进信封保留键**。
- 改动 `scripts/**` 后必须复跑：`fault_inject.py --fail-on strict` + 三案冒烟 + `TEST.md` 判据，
  并把新的实测记录追加进 `TEST.md`。
- 编号一致性：D1–D20 在 `SKILL.md` §3、`references/failure-modes.md` §2/§3、注入用例表三处同步；
  F1–F9/G1–G5/P1 修复项在 `references/FAULT-MATRIX.md` §2 有唯一权威记录。
