# README.md — 科研数据图表生成与编辑 Skill（多案例泛化与题集版）

`challenge-1bd90d8a` · 玻尔产品周赛 · 北大专区 · 学术效率 · 第三期

把「科研数据表 / 生物源材料 → 可直接投稿的可编辑图稿」做成一条可回溯、可校验、可复现的链路；
本版额外证明它**不是只在自己示例上跑通**：自带**两个题材不同**的合成案例组成题集
（`examples/cases/`），逐案给出输入、期望产出结构、可接受区间、难度层与**实测结果**，
并如实写明泛化边界（`references/CASE-SET.md`）。

---

## 1. 依赖与安装

| 项 | 要求 |
|-|-|
| Python | 3.8+（开发与实测环境：CPython **3.13.9**） |
| 必需 | 标准库 |
| **强烈建议** | `Pillow` —— 渲染 PNG/PDF 预览；**缺它时链路会降级失败**（见 §6） |
| 非必需 | `matplotlib` / `cairosvg` / `svgwrite`（本包不使用） |
| 网络 | **不需要**，脚本内不做网络访问 |
| 字体 | 运行时自动扫描常见字体目录；可用环境变量 `FONT_PATHS` 追加 |

```bash
pip install Pillow
python -c "import PIL, sys; print('Pillow', PIL.__version__, '| Python', sys.version.split()[0])"
```

**无需安装本包**：`scripts/` 是纯标准库模块，按路径直接调用即可。

---

## 2. 怎么调用

`$SKILL_DIR` = 本包所在目录的绝对路径（平台安装期为 `/skills/weekly-skill`）。
脚本用 `os.path.dirname(os.path.abspath(__file__))` 自定位资源，**cwd 与技能根不同也能跑**。

```bash
SKILL_DIR=/skills/weekly-skill

# ① 题集案例 A（生态学：湖泊中试 panel 图）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/cases/lake-eutrophication/case.json" \
       --out /tmp/outA --work /tmp/workA
# ② 题集案例 B（材料科学：scatter + 材料文本驱动的机制图）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/cases/mg-alloy-degradation/case.json" \
       --out /tmp/outB --work /tmp/workB
# ③ 平台正式案例（运行期为 /input/case.json → /app/output）
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output --work /app/work --style nature

# 四道复核（任一案例）
python "$SKILL_DIR/scripts/check_contract.py" --result /tmp/outA/result.json --case "$SKILL_DIR/examples/cases/lake-eutrophication/case.json"
python "$SKILL_DIR/scripts/figcheck.py"  --dir /tmp/outA --case "$SKILL_DIR/examples/cases/lake-eutrophication/case.json"
python "$SKILL_DIR/scripts/mapcheck.py"  --dir /tmp/outA --case "$SKILL_DIR/examples/cases/lake-eutrophication/case.json"
python "$SKILL_DIR/scripts/verify_rerun.py" --case "$SKILL_DIR/examples/cases/lake-eutrophication/case.json" --out /tmp/outA

# 四形态故障注入台（23 条；包外工作目录，源包只读）
python "$SKILL_DIR/scripts/fault_inject.py" --src "$SKILL_DIR" --workdir /tmp/fw
```

---

## 3. 参数与退出码

`main.py` 参数：`--case`（必需）· `--out` · `--work` · `--task` · `--data` ·
`--style`（`default`/`nature`/`cell`/`prism`/`minimal`/`ppt`）· `--dpi` · `--note` ·
`--lang`（`zh`/`en`）· `--no-pdf`。

| 退出码 | 含义 | `result.json` |
|-|-|-|
| **0** | `completed` 且 G1–G8 全过 | 完整（案例 A 实测 29 键 / 案例 B 27 键） |
| **2** | `partial`：部分图失败 / 材料缺失 / 校验缺口 | 完整，`failed_figures` 与 `uncertainty` 说明原因 |
| **1** | `failed`：case.json 不存在或不可解析、**案例没有任何图规格**、运行异常 | 6 键最小诚实信封或完整信封，`status=failed` |
| **1** | `scripts/*.py` 缺失（import 阶段失败） | **不存在**（import 早于兜底逻辑） |

其余脚本：`spec_lint.py` `0`=valid / `2`=有 error / `1`=用法错误；
`figcheck.py`/`mapcheck.py`/`verify_rerun.py`/`check_contract.py` `0`=通过 / 非 0=有缺口；
`fault_inject.py` `0`=实测与期望全一致 / `2`=有对不上的 / `1`=用法错误。

---

## 4. 目录说明

```
SKILL.md / README.md / TEST.md / COMPARE.md / GITHUB_URL.txt
scripts/       11 个脚本（主入口、渲染引擎、抽取、规格门、双校验、确定性、契约自查、
               故障注入台、字体、SVG 文本）
templates/     4 份 JSON（样式预设 / 图规格 schema（仅文档）/ 结果信封 / 关系词表）
references/    OUTPUT_CONTRACT（契约，逐字保护）+ RUBRIC_MAP + failure-modes +
               audit-rules + encoding-spec + typesetting-presets + workorder-field-map +
               CASE-SET.md（★ 题集）+ FAULT-MATRIX.md（★ 故障注入实测）
examples/      自带最小示例（肿瘤体积 bar+line + entities.json 机制图）
examples/cases/lake-eutrophication/      ★ 案例 A：case.json / data.csv / task.md
examples/cases/mg-alloy-degradation/     ★ 案例 B：case.json / data.csv / material.md / task.md
```

**包内零二进制**：没有 `.png/.pdf/.svg/.pptx`、没有字体文件、没有 `__pycache__`。
所有图与预览由 `main.py` 运行时生成，因此包内不存在可被误当"预制答案"的成品图。

---

## 5. 题集一览（细节与实测见 `references/CASE-SET.md`）

| 编号 | 题材 | 图型组合 | 难度 | 主要考察 | 实测 |
|-|-|-|-|-|-|
| A | 湖泊中试富营养化（生态/环境） | `panel`（bar + line） | 中 | 子面板按列过滤、多系列折线、**未引用列仍要记录** | exit 0 · 29 键 · 99 checked/0 mismatch · 1.4 s |
| B | Mg-Zn 合金体外降解（材料/生物材料） | `scatter` + `network` | 高 | **材料文本驱动的实体抽取**、**SD 与 SE 并存不得混用**、机制图 group 分层 | exit 0 · 27 键 · 74 checked/0 mismatch · 0.9 s |

> 案例 B 的**首轮实测是失败的**（`exit 2`，`通路图需要 entities（节点）列表。`）——
> 它暴露出"生成路径只认 `entities_file`(JSON)、材料文本解析器没接上"这个真实缺口（P5），
> 修好后才达到上表结果。这正是要放两个题材不同案例的理由。

---

## 6. 已知行为与限制

| 情形 | 实测行为 | 出处 |
|-|-|-|
| 源数据表缺失/为空 | `partial` + exit 2，点名列名与路径 | FAULT-MATRIX I3/I4 |
| **案例没有任何图规格** | `failed` + exit 1，`uncertainty` 说明，**不臆造图占位** | FAULT-MATRIX I6（P8） |
| 列名写错 | 单图失败、其余继续，`partial` + exit 2 | FAULT-MATRIX I7 |
| 样式模板缺失/损坏 / `--style` 拼错 | 回退 `default` 并写 `uncertainty` | FAULT-MATRIX T1/T2/T5（P3） |
| 契约含非法项 / 形态非法 | 跳过非法项；形态非法时 `applied=false` + 说明 | FAULT-MATRIX K1/K6（P1/P4） |
| **`heatmap` / `type:"auto"` / 只给 `material_file`** | **本轮修好前全部不工作**，现在均实测通过 | FAULT-MATRIX P5–P7 |
| **缺 Pillow** | **FATAL → exit 1 / `failed`，SVG 不进 `outputs`** | FAULT-MATRIX D2（**未修，已登记**） |
| **`scripts/*.py` 缺失** | exit 1，**不写 `result.json`** | FAULT-MATRIX D1/D4（N3） |

泛化边界的完整清单（含"仍然会失效/不适用"的 7 条）见 `references/CASE-SET.md` §4。

---

## 7. 维护

- **改契约**：`references/OUTPUT_CONTRACT.md` 的 `REQUIRED-FIELDS` 块是**机器可读的**，
  改契约必须同时改文档与脚本并重跑自查。**该字段块逐字受保护，不得改名/改结构。**
- **改脚本**：CLI 参数名、默认值、退出码语义**不得变**；本版对 `main.py`/`figcheck.py`/`chartkit.py`
  的改动全部是**纯增量**，逐条记录在 `references/FAULT-MATRIX.md` §5（P1–P8）。
- **加案例**：在 `examples/cases/<name>/` 放 `case.json` + 数据（+ 材料），
  然后在 `references/CASE-SET.md` 补一节（输入/期望结构/可接受区间/难度层/**真跑的实测**）。
- **加图型**：先在 `chartkit` 实现并在 `templates/figure_map.schema.json` 声明，
  然后**必须**在题集里加一个探针案例并记录实测——不许只改文档不改测试。
- **每次改包后**：题集两案 + 九种图型探针 + `fault_inject.py` 三样都要重跑。
