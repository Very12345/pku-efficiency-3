# README.md — 科研数据图表生成与编辑 Skill（故障注入与恢复演练版）

`challenge-1bd90d8a` · 玻尔产品周赛 · 北大专区 · 学术效率 · 第三期

把「科研数据表 / 生物源材料 → 可直接投稿的可编辑图稿」做成一条可回溯、可校验、可复现的链路；
**并且把"异常处理到底生效了没有"做成一台可执行的实验台**（`scripts/fault_inject.py`），
23 条注入的逐行实测记录在 `references/FAULT-MATRIX.md`。

---

## 1. 依赖与安装

| 项 | 要求 |
|-|-|
| Python | 3.8+（开发与实测环境：CPython **3.13.9**） |
| 必需 | 标准库 |
| **强烈建议** | `Pillow` —— 渲染 PNG/PDF 预览；**缺它时链路会降级失败**（见 §5 与 FAULT-MATRIX §5-D2） |
| 非必需 | `matplotlib` / `cairosvg` / `svgwrite`（本包不使用） |
| 网络 | **不需要**，脚本内不做网络访问 |
| 字体 | 运行时自动扫描常见字体目录；可用环境变量 `FONT_PATHS` 追加 |

```bash
pip install Pillow        # 部署前请确保这条生效
```

**部署前自检（一条命令）**：

```bash
python -c "import PIL, sys; print('Pillow', PIL.__version__, '| Python', sys.version.split()[0])"
```

> 为什么把这条摆在最前面：注入实验（FAULT-MATRIX 用例 **D2**）实测发现，
> 缺 Pillow 时**渲染层**会优雅降级，但**校验层**（`figcheck.py`）会抛 `ImportError`，
> 把整次运行打成 `failed`，已经写出的 SVG 不会进入 `result.json.outputs`。
> 这条缺口**未修**（修它要改校验器语义），所以在这里明写，避免误以为"缺 Pillow 也没事"。

**无需安装本包**：`scripts/` 是纯标准库模块，按路径直接调用即可。本包**不写**安装目录之外的任何位置。

---

## 2. 怎么调用

`$SKILL_DIR` = 本包所在目录的绝对路径（平台安装期为 `/skills/weekly-skill`）。
脚本用 `os.path.dirname(os.path.abspath(__file__))` 自定位资源，**cwd 与技能根不同也能跑**。

```bash
SKILL_DIR=/skills/weekly-skill

# 主链路（CP1→CP6 一次跑完）
python "$SKILL_DIR/scripts/main.py" \
       --case /input/case.json --out /app/output --work /app/work --style nature

# 四道复核
python "$SKILL_DIR/scripts/mapcheck.py"       --dir /app/output --case /input/case.json
python "$SKILL_DIR/scripts/figcheck.py"       --dir /app/output --case /input/case.json
python "$SKILL_DIR/scripts/verify_rerun.py"   --case /input/case.json --out /app/output
python "$SKILL_DIR/scripts/check_contract.py" --result /app/output/result.json --case /input/case.json

# 故障注入实验台（本版特色；--src 指向本包，源包只读）
python "$SKILL_DIR/scripts/fault_inject.py" --src "$SKILL_DIR" --workdir /tmp/fault-work
```

---

## 3. 参数与退出码

`main.py` 参数：`--case`（必需）· `--out` · `--work` · `--task` · `--data` ·
`--style`（`default`/`nature`/`cell`/`prism`/`minimal`/`ppt`）· `--dpi` · `--note` ·
`--lang`（`zh`/`en`）· `--no-pdf`。

| 退出码 | 含义 | `result.json` |
|-|-|-|
| **0** | `completed` 且 G1–G8 全过 | 完整（实测 29 键，含契约字段） |
| **2** | `partial`：部分图失败 / 材料缺失 / 校验有缺口 | 完整，`failed_figures` 与 `uncertainty` 说明原因 |
| **1** | `failed`：case.json 不存在或不可解析、运行异常 | 6 键最小诚实信封（`case_id/status/error/uncertainty/sources/change_records`） |
| **1** | **`scripts/*.py` 缺失**（import 阶段失败） | **不存在**——import 早于兜底逻辑，见 §5 与 FAULT-MATRIX-N3 |

其余脚本：`spec_lint.py` 用 `0`=valid / `2`=有 error / `1`=用法错误；
`figcheck.py`、`mapcheck.py`、`verify_rerun.py`、`check_contract.py` 用 `0`=通过 / 非 0=有缺口；
`fault_inject.py` 用 `0`=实测与期望全一致 / `2`=有对不上的 / `1`=用法错误。

---

## 4. 目录说明

```
SKILL.md           执行流程 + 决策规则 D1–D18 + 注入结论总览
README.md          本文件
TEST.md            真机实测记录（含 23 条注入的实测摘录 + 正常路径回归）
COMPARE.md         与"直接调通用绘图库"的对照方案
scripts/           10 个脚本：主入口、渲染引擎、抽取、规格门、双校验、确定性、契约自查、
                   **fault_inject.py（四形态故障注入台）**、字体、SVG 文本
templates/         4 份 JSON：样式预设 / 图规格 schema（仅文档）/ 结果信封 / 关系词表
references/        OUTPUT_CONTRACT（契约，逐字保护）+ RUBRIC_MAP + failure-modes +
                   audit-rules + encoding-spec + typesetting-presets + workorder-field-map +
                   **FAULT-MATRIX.md（23 条注入的逐行实测）**
examples/          合成示例输入（case.json / data.csv / entities.json / material.md / task.md）
                   + EXPECTED-OUTPUT.md（预期产物文字清单）+ output/（真实运行的契约 JSON）
```

**包内零二进制**：没有 `.png/.pdf/.svg/.pptx`、没有字体文件、没有 `__pycache__`。
所有图与预览由 `main.py` 运行时生成，因此包内也不存在可被误当"预制答案"的成品图。

---

## 5. 已知行为与限制（与注入实测一致）

| 情形 | 实测行为 | 出处 |
|-|-|-|
| 源数据表缺失/为空 | `partial` + exit 2，点名列名与路径；机制图仍照常出图 | FAULT-MATRIX I3/I4 |
| 案例没有任何图规格 | `partial` + exit 2，失败记录**同时**给出渲染层原因与"缺图规格" | FAULT-MATRIX I6（本版已修，P2） |
| 列名写错 | 该图失败、其余继续，`partial` + exit 2 | FAULT-MATRIX I7 |
| 样式模板缺失/损坏 | 回退 `default` 继续出图，**并在 `uncertainty` 点名** | FAULT-MATRIX T1/T2（本版已修，P3） |
| `--style` 拼错 | 回退 `default`，`uncertainty` 列出可用预设 | FAULT-MATRIX T5（本版已修，P3） |
| 契约含非法项（数字/空串） | 跳过非法项，其余照常回显，G2 仍通过 | FAULT-MATRIX K1（本版已修，P1） |
| 契约是四形态之外的形态 | `output_contract_applied=false` + 说明 | FAULT-MATRIX K6（本版已修，P4） |
| 契约声明不产出的字段 | 给容器类型空值 + 说明，**不做假映射** | FAULT-MATRIX K7 |
| **缺 Pillow** | **FATAL → exit 1 / `failed`，只留 6 键信封**（降级路径未生效） | FAULT-MATRIX D2（**未修，已登记**） |
| **`scripts/*.py` 缺失** | exit 1，**不写 `result.json`** | FAULT-MATRIX D1/D4（N3） |
| `templates/figure_map.schema.json` 缺失 | 完全无影响（运行期不读取该文件） | FAULT-MATRIX T4（N2） |

其余限制（不做统计推断、自动布局为启发式、PDF 为光栅预览、字体依赖运行环境、
词表扫描只是候选提示）见 `SKILL.md` §10。

---

## 6. 维护

- **改契约**：`references/OUTPUT_CONTRACT.md` 的 `REQUIRED-FIELDS` 块是**机器可读的**，
  `check_contract.py` 直接解析它。改契约必须**同时**改文档与脚本，并对 `result.json` 重跑自查。
  **该字段块逐字受保护，不得改名/改结构。**
- **改脚本**：CLI 参数名、默认值、退出码语义**不得变**；本版对 `main.py`/`figcheck.py`
  的改动全部是**纯增量**且逐条记录在 `references/FAULT-MATRIX.md` §5（P1–P4）。
- **每次改包后必须重跑注入台**：`fault_inject.py` 全绿（`mismatch=0`）才视为没把已有分支改坏；
  新出现的 mismatch 要么修代码、要么更新文档声明，**不许放着不管**。
- **加期刊样式**：往 `templates/journal_styles.json` 加同名键即可，无需改代码（D13）。
- **换默认字体**：设环境变量 `FONT_PATHS`（分号分隔），无需改代码。
