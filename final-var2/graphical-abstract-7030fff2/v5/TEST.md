# TEST.md — 本机实测记录（v5 轴：多案例泛化与题集）

> 所有数字都是本机在**包外临时副本**上真跑得到，没有估计值。
> 环境：Windows / Python **3.13.9** / matplotlib 3.10.6 / Pillow 12.3.0 / pypdf 6.14.2（2026-11-22）。
> **绝不在包内跑脚本**（会生成 `__pycache__`，直接导致合规验收 FAIL）。

```bash
SKILL_DIR=/abs/path/to/graphical-abstract-7030fff2
PKG=/tmp/ga-pkg && cp -r "$SKILL_DIR" "$PKG" && cd "$PKG"
```

---

## 1. 三个案例逐案冒烟（题集本体）

```bash
python scripts/main.py --case examples/case.json --out /tmp/ga-l1
python scripts/main.py --case examples/cases/calab-perovskite-001/case.json --out /tmp/ga-l2
python scripts/main.py --case examples/cases/urban-heat-001/case.json --out /tmp/ga-l3
```

| 项目 | L1 `example-micelle-001` | L2 `calab-perovskite-001` | L3 `urban-heat-001` |
|-|-|-|-|
| exit code | **0** | **0** | **0** |
| `result.json.status` | **success** | **success** | **partial** |
| 顶层键数 | **26** | **26** | **26** |
| entities / relations / data | 6 / 5 / 7 | 7 / **9** / 7 | 7 / **8** / 7 |
| `uncertainty` 条目 | 0 | 0 | **2**（缺值 + 数值矛盾） |
| `audit.missing_values` | `[]` | `[]` | `['夜间地表温度差']` |
| 实体覆盖 | 6/6 | 7/7 | 7/7 |
| 数值编码一致性 | 7/7 | 7/7 | 6/6 |
| 四要素覆盖 | 4/4 | 4/4 | 4/4 |
| 图层违规 / 无 src / 越界 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| `spec_lint.valid` | true | true | true |
| PNG 后端 | matplotlib | matplotlib | matplotlib |
| `preview/pdf` | `present:true` | `present:false` + reason | `present:false` + reason |

**L3 的 `uncertainty` 原文（两条都要有，缺一条即不合格）**：

```
以下数据点缺少可核验数值：夜间地表温度差（已在图上以“数值缺失”占位标记，未编造数值）
材料与 case.json 数值不一致（首见优先，未取平均）：夏季平均反照率：case.json 取 0.14，材料另给 0.19（两处 src=case.json[data] / material:35）
```

## 2. 契约门（逐案 exit code）

```bash
python scripts/check_contract.py --result /tmp/ga-l1/result.json --case examples/case.json
python scripts/check_contract.py --result /tmp/ga-l2/result.json --case examples/cases/calab-perovskite-001/case.json
python scripts/check_contract.py --result /tmp/ga-l3/result.json --case examples/cases/urban-heat-001/case.json
```

| 案例 | exit code | 信封键 | 契约字段 |
|-|-|-|-|
| L1 | **0** | 18/18 | 8/8 |
| L2 | **0** | 18/18 | 8/8 |
| L3 | **0** | 18/18 | 8/8 |

## 3. 确定性（逐案两次运行）

| 案例 | 第 1 次 `determinism_probe.spec_sha16` | 第 2 次 | 结论 |
|-|-|-|-|
| L1 | `9bcb54b29fe658d4` | `9bcb54b29fe658d4` | 一致 |
| L2 | `8b1b2a88fc72eff3` | `8b1b2a88fc72eff3` | 一致 |
| L3 | `d12251c822cf4141` | `d12251c822cf4141` | 一致 |

## 4. 数值可定位自查（题集的自检）

对三个案例逐个核对：`case.json` 里每个带值的指标都要能在同案 `material.md` 中逐字找到；
实体名也要出现在材料里。

| 案例 | 声明数据点 | 材料中找不到的数值 | 实体名出现在材料里 |
|-|-|-|-|
| L1 | 7 | `[]` | 6/6 |
| L2 | 7 | `[]` | 7/7 |
| L3 | 7（其中 1 条故意无值） | `[]` | 7/7 |

## 5. 题集暴露出的链路缺陷（已按纯增量修复）

v5 把案例从 1 个扩到 3 个，立刻暴露出**只在单一案例上跑不出来的问题**；这些都已修复并复跑：

| 现象（修复前实测） | 根因 | 修复后实测 |
|-|-|-|
| L2 的 `25.4 mA/cm2`、`3.1e11 cm-2` 被判「数值缺失」（`missing_values` 两条，值其实就在材料里） | 数值解析的单位字符类不含数字与 `-` `/` | L2 `missing_values=[]` |
| L2 的说明文字渲染成 `310000000000.0`，而 audit 按 `:g` 找 `3.1e+11` ⇒ **G6 硬门报"数值未上画布"** | 说明文字用原始 float，其它通道用 `:g` | L2 `encoding_consistency.missing_from_canvas=[]` |
| 材料行被整批误判成"关系"（L2 的 `relations` 被灌到 **25**，实际声明 5 条），**材料里的数值永远进不了数据通道** | 箭头正则的分隔符写成可选 `⇒?`，几乎任何一行都能匹配 | L2 `relations=9`；材料数值进入数据通道 |
| L3 材料里 0.14 / 0.19 两处数值，第二个被静默丢弃（`uncertainty` 无记录） | 材料事实与 case 声明同 id 时直接跳过，不比较数值 | L3 `uncertainty` 出现数值不一致条目（含两处 `src`） |

> 与 v4 轴的交叉：这四处之外，v4 的 23 条失败注入还查出 8 条静默失败与 1 处死代码
> （第三级纯 Python PNG 渲染器），详见 v4 包的 `references/FAULT-MATRIX.md`
> 与 `references/CASE-SET.md` §4。

## 6. 复现判据

1. 三个案例分别 `exit 0`，各产出 `result.json`（顶层 26 键）。
2. 三个案例的 `check_contract.py` 均 **exit 0**。
3. L1/L2 `status=success`；L3 `status=partial` 且 `uncertainty` 同时含"数值缺失"与"数值不一致"两条。
4. 每案两次运行 `determinism_probe.spec_sha16` 一致。
5. 包内 `grep -rn` 无本机绝对路径；无 `__pycache__`；文件数 ≤ 50、总字节 ≤ 2MB。

## 7. 未验证 / 边界（如实声明）

- 三个案例均为**合成示意**，不是平台正式案例；正式案例由组织方提供。
- 未覆盖"扫描件 PDF（无文本层）"的真实样本：本机用合成 PDF 字节流验证了"二进制 → 跳过 + 记录"
  与"可选 `pypdf` 文本层"两条路径，但没有真实扫描件的文本层质量记录。
- 未做跨机器对照（只有本机 python 3.13 + matplotlib 3.10 的记录）；后端与耗时会随环境变化，
  **结论性判据（覆盖为空、契约 exit 0、缺值留痕）不随环境变化**。
- 材料中带比较符/区间的写法（`≈13.6 µg/mL`、`0.8–1.2 mg/L`）不会被解析为数值，已在
  `references/CASE-SET.md` §4 列为失效边界。
