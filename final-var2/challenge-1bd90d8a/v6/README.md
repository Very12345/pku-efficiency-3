# README.md — 科研数据图表生成与编辑 Skill（v6 全维合并版）

`challenge-1bd90d8a` · 玻尔产品周赛 · 北大专区 · 学术效率 · 第三期

把「科研数据表 / 生物源材料 → 可直接投稿的可编辑图稿」做成一条**可回溯、可校验、可复现、
可被机器接手**的链路；并把四条证据链收进同一个包：

| 证据链 | 落在哪个文件 | 一句话 |
|-|-|-|
| 执行决策 | `SKILL.md` §3 + `references/failure-modes.md` | 18 条决策规则，覆盖材料异常/契约四形态/状态一致性/失败分支 |
| 失败与恢复 | `references/EVIDENCE.md` 第一部分 + `scripts/fault_inject.py` | 23 条四形态故障注入**逐行实测**（含 8 处真实缺陷登记，1 处未修） |
| 增益可验证 | `references/MECHANISM.md` 第二部分 + `examples/{baseline_agent,measure_ab}.py` | 12 项机器可判定指标的 A/B 对照协议与实测（**不做"提升 x%"式声称**） |
| 机制与复用 | `references/MECHANISM.md` 第一/三部分 | 四个互相咬合的机制 + 资产清单与三条复用路径 |
| 跨案例泛化 | `references/EVIDENCE.md` 第二部分 + `examples/cases/**` | 两个**题材不同**的合成案例题集 + 九种图型探针 + 泛化边界 |

> **合并说明（透明）**：为守住"≤50 个文本文件"的硬门，本版把四份专题文档合并为
> `references/MECHANISM.md`（机制/增益/复用/增改四部分），两份实证文档合并为
> `references/EVIDENCE.md`（故障矩阵/案例题集两部分）。**只动编排，没有内容被删除。**

---

## 1. 依赖与安装

| 项 | 要求 |
|-|-|
| Python | 3.8+（开发与实测环境：CPython **3.13.9**） |
| 必需 | 标准库 |
| **强烈建议** | `Pillow`（渲染 PNG/PDF 预览）。**缺它时链路会降级失败**：渲染层能降级，但校验层会抛错（见 §7） |
| 对照实验需要 | `matplotlib`（**只有** `examples/baseline_agent.py` 用它构造"条件 A"；主链路不依赖） |
| 非必需 | `cairosvg` / `svgwrite` —— 本包不使用 |
| 网络 | **不需要**，脚本内不做网络访问 |
| 字体 | 运行时自动扫描常见字体目录；可用环境变量 `FONT_PATHS` 追加 |

```bash
pip install Pillow                      # 部署前务必确保生效
pip install matplotlib                  # 仅在复跑 A/B 对照时需要
python -c "import PIL, sys; print('Pillow', PIL.__version__, '| Python', sys.version.split()[0])"
```

**无需安装本包**：`scripts/` 是纯标准库模块，按路径直接调用即可。

---

## 2. 怎么调用

`$SKILL_DIR` = 本包所在目录的绝对路径（平台安装期为 `/skills/weekly-skill`）。
脚本用 `os.path.dirname(os.path.abspath(__file__))` 自定位资源，**cwd 与技能根不同也能跑**。

```bash
SKILL_DIR=/skills/weekly-skill

# ① 正式案例（运行期：/input/case.json → /app/output）
python "$SKILL_DIR/scripts/main.py" --case /input/case.json --out /app/output --work /app/work --style nature

# ② 四道复核
python "$SKILL_DIR/scripts/mapcheck.py"       --dir /app/output --case /input/case.json
python "$SKILL_DIR/scripts/figcheck.py"       --dir /app/output --case /input/case.json
python "$SKILL_DIR/scripts/verify_rerun.py"   --case /input/case.json --out /app/output
python "$SKILL_DIR/scripts/check_contract.py" --result /app/output/result.json --case /input/case.json

# ③ 题集两案（回归：案例 A 生态 / 案例 B 材料）
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/cases/lake-eutrophication/case.json" --out /tmp/outA
python "$SKILL_DIR/scripts/main.py" --case "$SKILL_DIR/examples/cases/mg-alloy-degradation/case.json" --out /tmp/outB

# ④ 故障注入（23 条，判据 cases=23 mismatch=0）
python "$SKILL_DIR/scripts/fault_inject.py" --src "$SKILL_DIR" --workdir /tmp/fw

# ⑤ A/B 增益对照（条件 A vs 条件 B）
python "$SKILL_DIR/examples/baseline_agent.py" --case "$SKILL_DIR/examples/case.json" --out /tmp/A
python "$SKILL_DIR/scripts/main.py"            --case "$SKILL_DIR/examples/case.json" --out /tmp/B --style nature
python "$SKILL_DIR/examples/measure_ab.py"     --a /tmp/A --b /tmp/B --case "$SKILL_DIR/examples/case.json"
```

---

## 3. 参数与退出码

`main.py`：`--case`（必需）· `--out` · `--work` · `--task` · `--data` · `--style`
（`default`/`nature`/`cell`/`prism`/`minimal`/`ppt`）· `--dpi` · `--note` · `--lang`（`zh`/`en`）· `--no-pdf`。

| 退出码 | 含义 | `result.json` |
|-|-|-|
| **0** | `completed` 且 G1–G8 全过 | 完整（示例案例实测 29 键） |
| **2** | `partial`：部分图失败 / 材料缺失 / 校验缺口 | 完整，`failed_figures` + `uncertainty` 说明原因 |
| **1** | `failed`：case.json 不存在或不可解析、**案例没有任何图规格**、运行异常 | 6 键最小诚实信封，或完整信封 + `status=failed` |
| **1** | `scripts/*.py` 缺失（import 阶段失败） | **不存在**（import 早于兜底逻辑，须同时看退出码） |

其余脚本：`spec_lint.py` `0`=valid / `2`=有 error / `1`=用法错误；
`figcheck.py`/`mapcheck.py`/`verify_rerun.py`/`check_contract.py` `0`=通过 / 非 0=有缺口；
`fault_inject.py` `0`=实测与期望全一致 / `2`=有对不上的 / `1`=用法错误；
`measure_ab.py` `0`=对照跑完并出报告。

---

## 4. 目录说明

```
SKILL.md / README.md / TEST.md / GITHUB_URL.txt
scripts/       11 个脚本：主入口、渲染引擎、抽取、规格门、双校验、确定性、契约自查、
               故障注入台、字体、SVG 文本
templates/     4 份 JSON：样式预设 / 图规格 schema（仅文档）/ 结果信封 / 关系词表
references/    EVIDENCE.md（★ 故障矩阵 + 案例题集）
               MECHANISM.md（★ 机制 + 增益 + 复用 + 增改）
               OUTPUT_CONTRACT.md（契约，字段块逐字受保护）+ RUBRIC_MAP.md +
               failure-modes.md + audit-rules.md + encoding-spec.md +
               typesetting-presets.md + workorder-field-map.md
examples/      自带最小示例（case.json / data.csv / entities.json / material.md / task.md
               + EXPECTED-OUTPUT.md + output/*.json 真实运行产物）
               baseline_agent.py + measure_ab.py（A/B 对照工具）
               cases/lake-eutrophication/   ★ 案例 A：case.json / data.csv / task.md
               cases/mg-alloy-degradation/  ★ 案例 B：case.json / data.csv / material.md / task.md
```

**包内零二进制**：没有 `.png/.pdf/.svg/.pptx`、没有字体文件、没有 `__pycache__`。
所有图与预览由 `main.py` 运行时生成，因此包内不存在可被误当"预制答案"的成品图。

---

## 5. 已知行为一览（全部有实测出处）

| 情形 | 实测行为 | 出处 |
|-|-|-|
| 源数据表缺失/为空 | `partial` + exit 2，点名列名与路径；其余图照常产出 | EVIDENCE 第一部分 I3/I4 |
| **案例没有任何图规格** | `failed` + exit 1 + `uncertainty`，**不臆造占位图** | EVIDENCE 第一部分 I6（P8） |
| 列名写错 | 单图失败、其余继续，`partial` + exit 2 | EVIDENCE 第一部分 I7 |
| 样式模板缺失/损坏、`--style` 拼错 | 回退 `default` 并写 `uncertainty`（可用预设列在文案里） | EVIDENCE 第一部分 T1/T2/T5（P3） |
| 契约含非法项 / 形态非法 | 跳过非法项；形态非法时 `applied=false` + 说明 | EVIDENCE 第一部分 K1/K6（P1/P4） |
| **`heatmap` / `type:"auto"` / 只给 `material_file`** | **本版修好前全部不工作**，现均实测通过 | EVIDENCE 第一部分 P5–P7 |
| **缺 Pillow** | **FATAL → exit 1 / `failed`**，SVG 不进入 `outputs` | EVIDENCE 第一部分 D2（**未修，已登记**） |
| **`scripts/*.py` 缺失** | exit 1，**不写 `result.json`** | EVIDENCE 第一部分 D1/D4（N3） |
| `templates/figure_map.schema.json` 缺失 | 完全无影响（运行期不读取该文件） | EVIDENCE 第一部分 T4（N2） |

---

## 6. 与既有版本的差异（一表看完 v6 是哪些内容的并集）

| 来源 | 实质内容 | 在本包的落点 |
|-|-|-|
| 合规基线 | 全链路脚本、契约、模板、示例、G1–G8、审计规则、编码规范、排版预设、字段映射 | `scripts/`（10 个入口全在）、`references/`、`templates/`、`examples/` |
| v1 决策显性化 | D1–D16 触发→动作→降级 + FM 六族失败分支表 | `SKILL.md` §3/§4 + `failure-modes.md` |
| v2 增益可验证 | 12 项指标 + A/B 公平对照协议 + 实测记录 + `baseline_agent.py`/`measure_ab.py` | `SKILL.md` §5 + `MECHANISM.md` 第二部分 + `examples/*.py` |
| v3 机制与复用 | M1–M4 四机制（含"没有它会怎样"与边界对照表）+ 资产分级与三条复用路径 | `SKILL.md` §6/§7 + `MECHANISM.md` 第一/三部分 |
| v4 失败注入 | `fault_inject.py`（23 条四形态注入）+ 逐行实测矩阵 + P1–P4 修复 | `SKILL.md` §4 + `EVIDENCE.md` 第一部分 + `scripts/fault_inject.py` |
| v5 多案例题集 | 两个不同题材案例 + 可接受区间 + 九种图型探针 + 泛化边界 + P5–P8 修复 | `SKILL.md` §8 + `EVIDENCE.md` 第二部分 + `examples/cases/**` |
| **本版新增** | **按"输入→执行→失败→增益→机制→复用"重排的整合 SKILL.md**，并把每条证据索引到具体文件/部分 | `SKILL.md` 全文 |

---

## 7. 维护

- **改契约**：`references/OUTPUT_CONTRACT.md` 的 `REQUIRED-FIELDS` 块是**机器可读的**
  （`check_contract.py` 直接解析）。改契约必须**同时**改文档与脚本并重跑自查。
  **该字段块逐字受保护，不得改名/改结构。**
- **改脚本**：CLI 参数名、默认值、退出码语义**不得变**。本版相对基线的改动全部是**纯增量**且逐条点名：
  `main.py` +109/−7、`figcheck.py` +8/−4、`chartkit.py` +60/−4（含 P6/P7 与 PDF 元数据确定性归一化），
  其余脚本逐字节不变；新增 `scripts/fault_inject.py`。
- **每次改包后三件必做**：① `fault_inject.py` 全套（判据 `mismatch=0`）；
  ② 题集两案（判据都 `exit 0 / completed / G1–G8 全过`）；③ 九种图型探针。
  三者任一失败，要么修代码、要么更新文档声明，**不许放着不管**。
- **加案例**：放 `examples/cases/<name>/`（`case.json` + 数据 + 可选材料），
  在 `references/EVIDENCE.md` 第二部分补一节并填**真跑的实测**。
- **加期刊样式**：往 `templates/journal_styles.json` 加同名键即可，无需改代码。
- **换默认字体**：设 `FONT_PATHS`（分号分隔），无需改代码。
