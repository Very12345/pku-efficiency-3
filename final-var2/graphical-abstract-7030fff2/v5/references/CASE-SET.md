# CASE-SET.md — 可复跑题集（v5 轴）：逐案输入、期望结构、可接受区间、实测与失效边界

> **这些是合成案例，不是平台正式案例，也不代表任何正式成绩。** 平台的正式案例由组织方提供；
> 本文件的作用是让"这条出图链路"可以在**多个题材与多种材料形态**上被独立复跑与回归。
>
> 所有数字均为本机实测（Windows / Python 3.13.9 / matplotlib 3.10.6 / Pillow 12.3.0 /
> pypdf 6.14.2，2026-11-22），命令见 §5；**没有估计值**。
>
> 环境准备（**必须在包外**，包内跑脚本会留下 `__pycache__` 而破坏合规）：
> `PKG=$(mktemp -d) && cp -r "$SKILL_DIR" "$PKG" && cd "$PKG"`

---

## 1. 题集总览

| # | 案例 id | 题材 | 难度层 | 输入文件 | 关键输出 | 外部依赖 |
|-|-|-|-|-|-|-|
| 0 | `example-micelle-001` | 纳米医学：pH 响应聚合物胶束递送 DOX | **L1 基线** | `examples/{case.json,material.md,task.md}` | SVG + PNG + PDF + `result.json` | 无（可选 matplotlib/Pillow/pypdf） |
| 1 | `calab-perovskite-001` | 材料 / 能源器件：钙钛矿电池界面钝化与湿稳定性 | **L2 标准** | `examples/cases/calab-perovskite-001/{case.json,material.md,task.md}` | SVG + PNG + `result.json`（案例声明 `pdf=false`） | 同上 |
| 2 | `urban-heat-001` | 地球 / 环境科学：城市热岛地表能量平衡 | **L3 挑战** | `examples/cases/urban-heat-001/{case.json,material.md,task.md}` | 同上 | 同上 |

**难度层的划分理由**（不是按"图更复杂"，而是按**降级路径被触发的程度**）：

| 层 | 判据 | 本层期望 |
|-|-|-|
| **L1 基线** | 案例与材料完全一致：每个数值都能定位、无歧义、契约四形态齐备 | `status=success`，`uncertainty` 为空 |
| **L2 标准** | 题材与单位形态明显不同（含 `mA/cm2`、`cm-2`、`mm/day`、科学计数法 `3.1e11`），但材料自洽 | `status=success`；`missing_values` 与 `encoding_consistency.missing_from_canvas` 必须为空 |
| **L3 挑战** | 材料**故意**含两处异常：一个指标没有数值、同一指标出现两个互相矛盾的数值 | `status=partial`；两条异常都必须出现在 `uncertainty`，且**不得**用估计值补上 |

---

## 2. 逐案详表

### 2.1 `calab-perovskite-001`（L2 标准）

**输入**（`examples/cases/calab-perovskite-001/`）

| 文件 | 关键字段 |
|-|-|
| `case.json` | `case_id=calab-perovskite-001`；7 个实体（吸光层 / 钝化分子 / 电子传输层 / 界面缺陷态 / 水分子 / 钝化后器件 / 对照器件）；5 条关系（含 2 条 `kind=negative`）；7 个数据点（效率 23.7 %、V_oc 1.18 V、J_sc 25.4 mA/cm2、FF 81.2 %、缺陷密度 3.1e11 cm-2、T80 720 h、对照 21.2 %）；`figure_constraints{pdf:false, raster_scale:1}`；契约四形态齐备 |
| `material.md` | 6 小节实验记录：器件结构与工艺、光伏性能、缺陷与复合、湿稳定性、机制（5 行带箭头）、备注 |
| `task.md` | 含 `## 问题 / ## 方法 / ## 结果 / ## 结论` 四小节 + 交付要求（声明"缺值要占位"） |

**期望产出结构**

| 类别 | 期望 |
|-|-|
| `deliverables` | `editable_source/svg`（7 层 `layer:*`）、`layout_spec/json`、`preview/png`（`backend` 非空）、`preview/pdf`（`present:false` + `reason`，因为案例声明 `pdf=false`） |
| `result.json` 必出现字段 | 信封 18 键（`schema_version/skill/case_id/status/summary/task/deliverables/content_summary/provenance/sources/uncertainty/warnings/change_records/audit/generated_utc/output_contract_echo/plan/spec_lint`）+ 案例契约 8 字段 |
| `audit` | `entity_coverage.missing=[]`；`encoding_consistency.missing_from_canvas=[]`；`four_element_coverage.missing=[]`；`layer_naming.bad=[]` 且 `elements_without_src=0`；`bounds.outside_count=0` |

**可接受区间**

| 判据 | 可接受 | 不可接受 |
|-|-|-|
| 进程退出码 | `0` | 非 0 |
| `status` | `success` 或 `partial` | `failed` |
| `missing_values` | 必须为 `[]`（材料里 7 个数值全都有） | 任何条目 |
| `encoding_consistency.missing_from_canvas` | 必须为 `[]`（**G6 硬性门**） | 任何条目 |
| `relations` 计数 | 5–9（5 条声明 + 材料中带箭头的机制行） | 显著超出（说明把散文行误判成关系） |
| `check_contract.py` | exit `0` | 非 0 |
| 两次运行 `determinism_probe.spec_sha16` | 相同 | 不同 |

**实测结果**

| 项目 | 实测值 |
|-|-|
| exit code | **0** |
| `status` | **success** |
| 顶层键数 | **26** |
| `content_summary` | entities 7 · relations **9** · data 7 · panels `{question:0, method:0, results:3, conclusion:3}` · reading_order 四面板齐 |
| `uncertainty` / `warnings` | `[]` / `[]` |
| `audit.missing_values` | `[]` |
| `entity_coverage` | 7/7，`missing=[]` |
| `encoding_consistency` | total 7，`missing_from_canvas=[]` |
| `four_element_coverage` | 4/4（conclusion/method/question/results） |
| `layer_naming` | `bad=[]`、`missing=[]`、`elements_without_src=0` |
| `bounds.outside_count` | 0 |
| `spec_lint` | `valid=true`，`spec_sha16=edc536d181044d69` |
| `check_contract.py` | exit **0** |
| PNG 后端 | `matplotlib` |
| 两次运行 `spec_sha16` | `8b1b2a88fc72eff3` / `8b1b2a88fc72eff3` → **一致** |
| 数值可定位自查 | case.json 的 7 个数值全部能在 `material.md` 中逐字找到；7 个实体名全部出现在材料里 |

### 2.2 `urban-heat-001`（L3 挑战，**故意含两处材料异常**）

**输入**（`examples/cases/urban-heat-001/`）

| 文件 | 关键字段 |
|-|-|
| `case.json` | 7 个实体（城市建成区 / 城郊过渡带 / 植被覆盖 / 不透水面 / 地表温度 / 热浪过程 / 城郊农田）；5 条关系（含 2 条负向）；7 个数据点，其中 **`夜间地表温度差` 故意不带 `value`**；契约四形态齐备 |
| `material.md` | 6 小节观测记录；**第 2 节明确写"夜间热岛强度尚未完成质量控制，暂不给出数值"**；**第 4 节给出同一指标的两处不同数值（0.14 / 0.19，口径不同）并保留一条裸记录行 `夏季平均反照率 = 0.19`** |
| `task.md` | 四小节 + 交付要求（"缺值必须占位，不得用文献值补"；"矛盾数值原样保留并说明"） |

**期望产出结构**：与 2.1 同构；`preview/pdf` 为 `present:false` + `reason`（案例声明 `pdf=false`）。

**可接受区间**

| 判据 | 可接受 | 不可接受 |
|-|-|-|
| exit code / `status` | `0` / `partial` | `failed`；或把缺值悄悄补上后报 `success` |
| `audit.missing_values` | **恰好** `['夜间地表温度差']` | 空（说明缺值被编造）或含其它指标 |
| `uncertainty` | **必须**同时出现：①「数值缺失」占位说明；②材料数值不一致说明（含两处 `src`） | 缺任一条 |
| 编码一致性 | `missing_from_canvas=[]` | 任何条目 |
| 其余 audit 判据 | 同 2.1 | — |

**实测结果**

| 项目 | 实测值 |
|-|-|
| exit code | **0** |
| `status` | **partial**（限制已逐条记录） |
| 顶层键数 | **26** |
| `content_summary` | entities 7 · relations **8** · data 7 · panels `{question:0, method:0, results:4, conclusion:3}` |
| `uncertainty`（原文 2 条） | ①`以下数据点缺少可核验数值：夜间地表温度差（已在图上以“数值缺失”占位标记，未编造数值）` ②`材料与 case.json 数值不一致（首见优先，未取平均）：夏季平均反照率：case.json 取 0.14，材料另给 0.19（两处 src=case.json[data] / material:35）` |
| `audit.missing_values` | `['夜间地表温度差']` |
| `entity_coverage` | 7/7，`missing=[]` |
| `encoding_consistency` | total 6，`missing_from_canvas=[]` |
| `four_element_coverage` | 4/4 |
| `layer_naming` / `bounds` | `bad=[]`、`elements_without_src=0` / 0 |
| `spec_lint` | `valid=true`，`spec_sha16=5a7cbdc2847838ad` |
| `check_contract.py` | exit **0** |
| PNG 后端 | `matplotlib` |
| 两次运行 `spec_sha16` | `d12251c822cf4141` / `d12251c822cf4141` → **一致** |
| 数值可定位自查 | 6 个带值指标全部能在 `material.md` 中逐字找到（第 7 个即故意缺值项） |

> 这两处异常是**有意设计**：它们让题集覆盖"材料不完整"和"材料自相矛盾"两条降级路径 ——
> 正是基础做法最容易悄悄编造数值的地方。

---

## 3. 跨案例对照（三案并排）

| 判据 | L1 `example-micelle-001` | L2 `calab-perovskite-001` | L3 `urban-heat-001` |
|-|-|-|-|
| exit code | 0 | 0 | 0 |
| `status` | success | success | partial |
| 顶层键数 | 26 | 26 | 26 |
| entities / relations / data | 6 / 5 / 7 | 7 / 9 / 7 | 7 / 8 / 7 |
| `uncertainty` 条目 | 0 | 0 | 2 |
| `missing_values` | `[]` | `[]` | 1 条（构造） |
| 四要素覆盖 | 4/4 | 4/4 | 4/4 |
| `check_contract.py` | exit 0 | exit 0 | exit 0 |
| `determinism_probe.spec_sha16` | `9bcb54b29fe658d4`（两次一致） | `8b1b2a88fc72eff3`（两次一致） | `d12251c822cf4141`（两次一致） |

**单位形态覆盖**：`%`、`V`、`mA/cm2`、`cm-2`、`h`、`K`、`mm/day`、`d`、科学计数法 `3.1e11`、
无单位的纯小数 `0.14` —— 这些形态在实测中都被正确解析并上画布（见 §4 的成因说明）。

---

## 4. 泛化到哪会失效（如实写明；每条都有判据）

> 以下边界全部来自本次实测或代码事实，**不是想象**。每条给出"现象 → 判据 → 处置"。

1. **散落在散文里的数字不会被自动读进数据通道。**
   现象：材料中只有"**独立成行**且形如 `键 = 数值 单位`（或 `键: 数值`）"的行会被解析为数据点；
   写成"……在 85% RH 下衰减到原来的 80%"这种句子里的数字不会进 `data`。
   判据：把该行改成独立行后 `content_summary.data` 增加；不改则 `audit.missing_values` 里出现该指标。
   处置：要么在 `case.json` 里显式声明该指标，要么在材料里写成独立行。

2. **机制关系必须带真实箭头才会被识别。**
   现象：只有含 `->`、`→`、`==>`、`⇒` 的行才进入关系通道；用"促进 / 抑制"等中文动词连接、
   或写成表格两列的机制描述不会被解析成关系。
   判据：`content_summary.relations` 是否包含该条；`spec.json` 中是否存在 `role=relation:*` 元素。
   处置：机制行统一写成 `A -> B (label)`；负向关系在 label 里带"抑制/降低/阻断"等词（会被标 `kind=negative`）。

3. **材料与 case.json 数值不一致时，本 Skill 不判谁对。**
   现象：实测只做到"首见优先 + 冲突留痕"（`uncertainty` 里并列两处数值与各自 `src`）。
   判据：`uncertainty` 出现「材料与 case.json 数值不一致（首见优先，未取平均）」。
   处置：把口径写进材料（哪个是最终值），或在 `case.json` 里改成与材料一致的值；**不要指望自动裁决**。

4. **扫描件 / 纯图片材料无法读取。**
   现象：材料是二进制（PDF 或无文本层的图片）时，PDF 会尝试用可选依赖 `pypdf` 抽文本层；
   抽不到或没装 `pypdf` 时该材料被**跳过**，并在 `uncertainty` 写明"未取得可用文本层，数值不上画布"。
   判据：`uncertainty` 含"二进制文件"；`provenance.source_files[].role` 里没有该文件（或标 `material(pdf-text)`）。
   处置：提供文本材料，或先自行把 PDF 转文本；本 Skill **不会**从图片里编造数值。

5. **单位/数值形态的边界在于"能否被解析成数字 + 单位"。**
   现象：`25.4 mA/cm2`、`3.1e11 cm-2`、`1.8 mm/day`、`0.14`（无单位）实测均可解析；
   但带比较符或区间写法的值（如 `≈13.6 µg/mL`、`0.8–1.2 mg/L`）不会被解析为数值。
   判据：`audit.missing_values` 是否含该指标。
   处置：材料里给单一确定值；区间与近似值改写为独立"备注"行（不影响数值通道）。

6. **四要素面板必须有内容，否则 `status` 降级。**
   现象：`task.md` 缺 `问题/方法/结果/结论` 小节时，面板要点只能从材料小节标题推；
   推断不出内容时四要素仍会在画布上（结构在），但 `spec_lint`/`audit` 的覆盖判据会暴露内容缺失。
   判据：`audit.four_element_coverage.content_panels` 的计数。
   处置：`task.md` 保持四小节标题；或用 `--plan` 显式补 `four_elements` 一句话说明。

7. **契约字段没有真实值时按类型给空值，且禁 null。**
   现象：容器给 `[]`、布尔给 `false`、字符串给 `""`；`null` 会被归一化并记录。
   判据：`check_contract.py` exit 0 且 `result.json` 顶层无 null。
   处置：契约字段一律给出真实值；确实没有就显式写空值，不要写 `null`。

8. **确定性由"纯函数版面"保证，手工改动产物不在承诺范围内。**
   现象：两次运行的 `spec_sha16` 一致；但如果你手改了 SVG/PNG，第二次运行不会"记住"你的改动。
   判据：`audit.determinism_probe`。
   处置：把改动写成 case 的 `figure_constraints` 或 plan，而不是改产物。

---

## 5. 复现命令（逐字可跑；全部在**包外**执行）

```bash
SKILL_DIR=/abs/path/to/graphical-abstract-7030fff2
PKG=$(mktemp -d) && cp -r "$SKILL_DIR" "$PKG" && cd "$PKG"

# L1 基线案例
python scripts/main.py --case examples/case.json --out /tmp/ga-l1
# L2 材料 / 能源
python scripts/main.py --case examples/cases/calab-perovskite-001/case.json --out /tmp/ga-l2
# L3 地球 / 环境（含缺值 + 数值矛盾）
python scripts/main.py --case examples/cases/urban-heat-001/case.json --out /tmp/ga-l3

# 契约门（逐案 exit 0 才算通过）
for c in examples/case.json examples/cases/calab-perovskite-001/case.json examples/cases/urban-heat-001/case.json; do
  out=/tmp/ga-$(basename "$(dirname "$c")")
  python scripts/check_contract.py --result "$out/result.json" --case "$c"; echo "exit=$?"
done

# 确定性（同输入两次，比较 spec_sha16）
python scripts/main.py --case examples/cases/calab-perovskite-001/case.json --out /tmp/ga-l2b
python - <<'PY'
import json
a = json.load(open("/tmp/ga-l2/result.json", encoding="utf-8"))["audit"]["determinism_probe"]["spec_sha16"]
b = json.load(open("/tmp/ga-l2b/result.json", encoding="utf-8"))["audit"]["determinism_probe"]["spec_sha16"]
print("spec_sha16:", a, b, "same:", a == b)
PY

# 数值可定位自查（case.json 的每个数值都应能在同案 material.md 中逐字找到）
python - <<'PY'
import json, os, glob
for case_path in glob.glob("examples/cases/*/case.json") + ["examples/case.json"]:
    case = json.load(open(case_path, encoding="utf-8"))
    mat = open(os.path.join(os.path.dirname(case_path), "material.md"), encoding="utf-8").read()
    miss = [d["label"] for d in case.get("data", [])
            if d.get("value") and str(d["value"]).split()[0] not in mat]
    print(case["case_id"], "-> values not literal in material:", miss)
PY
```

## 6. 与平台正式案例的关系（必须读）

- 本文件的三个案例是**参赛者自建的合成题集**，用于回归与对照；**组织方会另外提供 3 个固定案例**，
  参赛者不需要、也不应该自带正式案例、白板或预生成答案。
- 三个案例里的数值、实体与结论均为**示意**，不来自任何真实论文或观测。
- 本文件中的 `status`、`spec_sha16`、计数等数字是**本机某一次运行的记录**，换机器可能变化的是
  后端与耗时；**结论性列（覆盖是否为空、契约是否通过、缺值是否留痕）不随机器变化**。
