# Graphical Abstract（图形摘要）Skill — 降级链优先版 · 使用说明

把研究材料做成一页图形摘要（研究问题 → 方法 → 核心结果 → 结论），同时交付
**可继续编辑的分层 SVG**、PNG/PDF 预览与字段完整的 `result.json`。

本版的重心是**缺依赖时的真实可用性**：随包附一条可执行判据 ——
`scripts/degrade_probe.py` 用**受控导入拦截**（每场景一个假包，写命中日志后 `raise ImportError`）
与 `PATH` 假 CLI，逐个模拟缺 `python-pptx` / `PIL` / `matplotlib` / `numpy` / `yaml` / `pypdf` / LibreOffice，
记录产物还剩什么、`status` 变什么、还写不写 `result.json`、退出码与 PDF 缺席原因。
实测 12 场景 / 12 ok / 0 crash、**12/12 都写出 `result.json`**，
逐场景表与「最小可用环境」清单见 [`references/DEGRADE-MATRIX.md`](references/DEGRADE-MATRIX.md)。

---

## 1. 环境与依赖

| 依赖 | 是否必需 | 缺了会怎样（实测见 [`references/DEGRADE-MATRIX.md`](references/DEGRADE-MATRIX.md)） |
|-|-|-|
| Python **3.9+** 标准库 | **必需** | 抽取、版面、SVG、audit、契约自查、复现判据全靠它 |
| `matplotlib` | 可选 | PNG 掉到 Pillow / 纯 Python；PDF 不产出（带 reason）；`status` 降 `partial` |
| `Pillow` | 可选 | 与 matplotlib 一起缺时文字退化为占位框（几何仍精确） |
| `pypdf` | 可选 | 仅影响**PDF 材料**的文本层；取不到就登记后跳过 |
| 系统 CJK 字体 | 可选 | 运行时按候选路径探测（`C:/Windows/Fonts`、`/usr/share/fonts`、`/System/Library/Fonts`）；找不到用默认字体并记录 |

包内**没有任何二进制资源**（无 `.png/.pdf/.svg/.ttf/.pptx`、无 `__pycache__`），
所有渲染件与源文件都是运行时生成的文本/图形产物。

## 2. 安装与自定位

```bash
cp -r graphical-abstract-7030fff2 /skills/weekly-skill
SKILL_DIR=/skills/weekly-skill
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/ga-out
```

`scripts/common.py` 用 `SCRIPT_DIR = dirname(abspath(__file__))` 解析技能根，
**cwd 不是技能根也能跑**；所有相对路径以 `case.json` / `--out` 为基准（这也是"换 cwd 产物不变"的原因）。

## 3. 参数（与 `scripts/` 的真实 CLI 逐字对应）

### `scripts/main.py` — 出图主入口

| 参数 | 默认 | 说明 |
|-|-|-|
| `--case` | 必填 | `case.json` 路径 |
| `--task` | `<case_dir>/task.md`（自动探测） | 任务说明 |
| `--material` | 取 `case.json.source_material` | 材料文件或目录（覆盖 case 声明） |
| `--out` | `<skill>/out` | 产物目录（官方运行时为 `/app/output`） |
| `--plan` | 无 | 设计方案 json（方案先行：`scaffold.py` 出骨架 → 定稿 → `spec_lint.py --lint-plan`） |
| `--raster-scale` | `constraints.raster_scale`（默认 2） | PNG 相对画布的倍数 |
| `--pdf` / `--no-pdf` | `constraints.pdf`（默认 true） | 是否产出 PDF 预览 |

退出码：`0` 完成（`success`/`partial`）；`1` 硬输入错误；`2` 环境或内部错误（输出目录不可用、`status=failed`）。

### 其余入口

| 脚本 | 参数 | 退出码 |
|-|-|-|
| `scripts/degrade_probe.py` | `--out`(必) `--case` `--only` `--fail-on strict\|silent\|none` `--keep` `--verbose` | `0` 达到等级 / `1` 未达到 / `2` 用法环境 |
| `scripts/scaffold.py` | `--case`(必) `--task` `--material` `--out`(必) | `0` / `1` |
| `scripts/spec_lint.py` | `--spec` `--content`（规格门）；`--lint-plan --plan`（方案门） | `0` 通过 / `1` 有 problems |
| `scripts/check_contract.py` | `--result`(必) `--case` | `0` 完整 / `1` 缺口 / `2` 文件不存在 |
| `scripts/fault_inject.py` | `--out`(必) `--only` `--fail-on silent\|strict\|none` `--keep` `--verbose` | `0` 无静默失败 / `1` 有 / `2` 环境 |
| `scripts/gain_harness.py` | `--out` `--case` `--material` `--label` `--json` `--compare` | `0` |

## 4. 产物

| 文件 | 内容 |
|-|-|
| `<case>_graphical_abstract.svg` | **可编辑分层源文件**：7 层 `layer:*` 组、真 `<text>`、每个科学元素带 `data-src` |
| `<case>_graphical_abstract.png` | 栅格预览（`render_log.backend` 如实记录是哪一个后端） |
| `<case>_graphical_abstract.pdf` | 矢量预览；未产出时 `deliverables[format=pdf]` 为 `present:false` + **reason** |
| `result.json` | **唯一评分产物**：信封 18 键 + 案例契约回显 + 溯源（含 sha256）+ `uncertainty` + 全量 `audit` |
| `spec.json` / `content.json` / `audit.json` / `render_log.json` | 透明性中间产物：图面规格、抽取结果、自查报告、渲染日志 |

## 5. 适用范围

- 适用：论文/基金/汇报的单页图形摘要；机制图、流程图、示意图、通路图的**首稿生成与编辑**；
  需要"图能追到材料 + 源文件可继续编辑"的场景。
- 不适用：论文正文写作、统计分析、实验设计；把位图截图当交付物；需要照片级插画的场景。

## 6. 限制（完整版见 [`SKILL.md`](SKILL.md) §9 与 [`references/failure-modes.md`](references/failure-modes.md)）

- 抽取只认**独立成行的 `键 = 数值 单位`**与**带真实箭头的机制行**；散文里的数字不抽取（宁缺勿错）。
- 可复现性承诺是"**同机、同依赖版本、同输入**"的 L1 一致性；`.png` 像素受系统字体影响、
  `.pdf` 头受绘图库版本影响，**跨机器不承诺字节一致**。
- 渲染降级（无 matplotlib）时 PDF 不产出、文字可能变占位框 —— 一定伴随 `status=partial` 与记录。
- 四要素/图层/契约检查是结构判据，不代替领域科学判断；随包示例案例为合成示意，非平台正式案例。

## 7. 维护

- 版本：`scripts/common.py` 的 `SKILL_VERSION`（当前 `2.0.0`）与 `result.json.skill.version` 同源。
- 改动任何脚本后，**先跑 `degrade_probe.py --fail-on strict`**（约 40 s）确认 12/12 `ok`、
  0 `crash`、12/12 仍写出 `result.json`，再跑 `check_contract.py` 与 `fault_inject.py --fail-on strict`。
- 新增第三方依赖前先想清楚：本包的依赖地图（[`SKILL.md`](SKILL.md) §2）按"流水线导入点"
  逐条列明，多加一个可选依赖就要为它补一个降级场景。
- 契约字段（`references/OUTPUT_CONTRACT.md` 的字段块）**逐字冻结**：改契约 = 改接口，必须同步
  `check_contract.py` 的信封键表并重跑三套判据。
- 本版相对上一代引擎有 **2 处纯增量修复**（`extract.py` 非法契约记录、`main.py` PDF 缺席 reason），
  逐条点名见 [`SKILL.md`](SKILL.md) §9.1。

## 8. 一页速查

```bash
SKILL_DIR=/skills/weekly-skill && OUT=/app/output
python "$SKILL_DIR/scripts/main.py"       --case /input/case.json --task /input/task.md --out "$OUT"
python "$SKILL_DIR/scripts/check_contract.py" --result "$OUT/result.json" --case /input/case.json
python "$SKILL_DIR/scripts/degrade_probe.py"  --out /tmp/dg --fail-on strict                   # 降级 12 场景
python "$SKILL_DIR/scripts/fault_inject.py"   --out /tmp/fi --fail-on strict                  # 四形态注入
python "$SKILL_DIR/scripts/gain_harness.py"   --out "$OUT" --case /input/case.json            # 只读测量
```
