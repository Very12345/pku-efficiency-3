# TEST.md — 本机实测记录（v4 轴：失败注入与恢复演练）

> 口径：本文所有数字都是本机在**包外临时副本**上真跑得到，不是估计值。
> 环境：Windows 10 / Python **3.13.9** / matplotlib 3.10.6 / Pillow 12.3.0 / pypdf 6.14.2。
> **绝不在包内跑脚本**（会生成 `__pycache__`，直接导致合规验收 FAIL）。

```bash
# 一次性准备（包外沙箱）
SKILL_DIR=/abs/path/to/graphical-abstract-7030fff2
PKG=/tmp/ga-pkg && cp -r "$SKILL_DIR" "$PKG" && cd "$PKG"
```

---

## 1. 冒烟：示例案例跑通并产出 result.json

```bash
cd "$PKG"
python scripts/main.py --case examples/case.json --out /tmp/ga-out
```

| 项目 | 实测值 |
|-|-|
| exit code | **0** |
| `result.json` `status` | **success** |
| `result.json` 顶层键数 | **26**（信封 18 + 案例契约 8） |
| `deliverables` | `editable_source/svg`（7 层，元素 62）、`layout_spec/json`、`preview/png`（**backend=matplotlib**）、`preview/pdf`（`present:true`） |
| `audit.entity_coverage` | `{total: 6, on_canvas: 6, missing: []}` |
| `audit.missing_values` | `[]` |
| `audit.four_element_coverage.on_canvas` | `["conclusion","method","question","results"]`（4/4） |
| `audit.layer_naming.bad` / `elements_without_src` | `[]` / **0** |
| `audit.bounds.outside_count` | **0** |
| `audit.determinism_probe.spec_sha16` | **9bcb54b29fe658d4** |
| `spec_lint.valid` / `spec_sha16` | `true` / **92a22433141dc61a** |
| `uncertainty` / `warnings` / `change_records` | `[]` / `[]` / **4** 条 |
| 产物文件 | `result.json`、`spec.json`、`content.json`、`audit.json`、`render_log.json`、`*.svg`、`*.png`、`*.pdf` |

## 2. 契约自查

```bash
python scripts/check_contract.py --result /tmp/ga-out/result.json --case examples/case.json
```

| 项目 | 实测值 |
|-|-|
| exit code | **0** |
| `valid` | **true** |
| 信封键 | **18/18** |
| 案例契约字段 | **8/8** 全部在顶层覆盖（`contract_fields=8`，`covered=8`） |
| null 违规 | **0** |

## 3. 确定性（同输入重跑）

```bash
python scripts/main.py --case examples/case.json --out /tmp/ga-out2
```

| 运行 | `audit.determinism_probe.spec_sha16` |
|-|-|
| 第 1 次 | `9bcb54b29fe658d4` |
| 第 2 次 | `9bcb54b29fe658d4` |
| 结论 | **逐字符一致**（版面为纯函数，无时间戳/随机数进图面） |

## 4. 四形态失败注入演练（本轴核心）

```bash
python scripts/fault_inject.py --out /tmp/ga-fi --fail-on strict
```

| 项目 | 实测值 |
|-|-|
| exit code | **0**（`--fail-on strict` 下仍为 0） |
| `cases_run` | **23** |
| `ok` | **23** |
| `mismatch` | **0** |
| `silent_failure` | **0** |
| 总耗时 | **30.65 s**（23 次真实出图，含子进程启动） |
| 分类 | input 7 · template 6 · dependency 5 · contract 5 |

逐条结果（`fault_report.json` 的 `summary.by_kind` 与 `cases[].verdict`）：

| 类 | 用例 | 全部 verdict |
|-|-|-|
| 输入 | F00–F06 | `ok` ×7 |
| 模板 | F07–F12 | `ok` ×6 |
| 依赖 | F13–F17 | `ok` ×5 |
| 契约 | F18–F22 | `ok` ×5 |

**修复前（同源未改脚本）同一套用例的实测**：`ok` 10 / `mismatch` 5 / **`silent-failure` 8** ——
其中 F04 F05 F07 F09 F11 F13 F16 F18 八条都是"进程 exit 0 且 `status=success`，而注入的缺陷
在 `uncertainty` 里没有任何记录"。逐行对照见 `references/FAULT-MATRIX.md` 第 1 节。
修复（纯增量）后复跑同一套用例 → 23/23 `ok`、0 静默失败。

另有 5 处缺陷（G1–G5）不是注入用例查出的，而是**用 v5 的两个合成案例实跑时**暴露的：
材料里确实存在的 `25.4 mA/cm2` / `3.1e11 cm-2` 被判「数值缺失」、材料行被整批误判成"关系"
（案例 A 的 `relations` 被灌到 25）、材料与 case.json 的数值矛盾被静默丢弃。
修复后复跑：案例 A `relations` **9**、`missing_values` **[]**、`status=success`；
案例 B 的数字冲突出现在 `uncertainty` 里。明细见 FAULT-MATRIX §2 的 G1–G5。

## 5. 单条复现（排查用）

```bash
python scripts/fault_inject.py --out /tmp/ga-fi15 --only F15 --verbose   # 两级渲染后端都缺 → 纯 Python PNG
python scripts/fault_inject.py --out /tmp/ga-fidep --only dependency     # 依赖类 5 条
```

| 用例 | 实测 exit | 实测 status | 关键字段 |
|-|-|-|-|
| F15（matplotlib + PIL 都不可导入） | **0** | **partial** | `render_log.backend=pure-python-png`；`uncertainty[0]` 含 `matplotlib 渲染不可用，已回退到备用渲染器` |
| F16（pypdf 不可导入 + PDF 材料） | **0** | **partial** | `uncertainty` 含 `以下材料是二进制文件…未取得可用文本层，相关数值一律不上画布` |
| F18（契约字段声明为 null） | **0** | **success** | `uncertainty` 含 `案例 output_contract 声明为 null 的字段已归一化为空值：resolution_dpi`；顶层无 null |
| F17（`--out` 指向普通文件） | **2** | 无 `result.json` | stdout `{"status":"failed","error":"output directory not usable: …"}` |
| F08（`--plan` 非法 JSON） | **1** | 无 `result.json` | stdout `{"status":"failed","error":"plan.json unreadable: …"}` |

## 6. 复现判据（谁都能重跑）

1. `python scripts/main.py --case examples/case.json --out <tmp>` → **exit 0** 且 `<tmp>/result.json` 存在、
   `status ∈ {success, partial}`、顶层 **26** 键。
2. `python scripts/check_contract.py --result <tmp>/result.json --case examples/case.json` → **exit 0**。
3. `python scripts/fault_inject.py --out <tmp2> --fail-on strict` → **exit 0**，
   `fault_report.json.summary.silent_failure == 0`。
4. 同输入重跑两次，`audit.determinism_probe.spec_sha16` **逐字符一致**。
5. 包内 `grep -rn` 无本机绝对路径；无 `__pycache__`；文件数 ≤ 50、总字节 ≤ 2MB。

## 7. 未验证 / 边界（如实声明）

- 注入不覆盖**平台侧故障**（挂载缺失、配额、容器超时）与**材料内容错误**（数值矛盾的真伪判断）。
- F14 揭示的真实耦合：matplotlib 自身 `import PIL`，因此"Pillow 是独立第二级"只在没装
  matplotlib 的环境里成立；本机实测该情形直接落到第三级纯 Python PNG（`status=partial`）。
- 演练耗时随机器变化（本机 20.22 s）；**判定列（verdict / 是否静默）不随机器变化**。
- 示例数据为合成示意，不代表平台正式案例结果。
