# TEST.md — 本机实测记录（契约优先版）

> 全部数字来自**包外临时副本**上的真实运行。环境：Windows / Python **3.13.9**（2026-11-23）。
> **绝不在包内跑脚本**：入口会在 `scripts/` 下留 `__pycache__`，直接导致合规验收 FAIL。

```bash
SKILL_DIR=/abs/path/to/graphical-abstract-7030fff2
PKG=/tmp/ga-pkg && rm -rf "$PKG" && cp -r "$SKILL_DIR" "$PKG" && cd "$PKG"
```

---

## 1. 主链冒烟

```bash
python scripts/main.py --case examples/case.json --out /tmp/ga-l1
```

| 项目 | 实测值 |
|-|-|
| exit code | **0** |
| `status` | **success** |
| `result.json` 顶层键数 | **26** = 信封 18 + 案例契约 8 |
| `deliverables` | `svg / json(layout_spec) / png / pdf` |
| `audit.four_element_coverage` | 4/4 |
| `audit.layer_naming` | `bad=[]`、`elements_without_src=0` |
| `uncertainty` / `warnings` | `[]` / `[]` |
| 两次运行 `audit.determinism_probe.spec_sha16` | `9bcb54b29fe658d4`（一致） |

## 2. 契约门（独立工具）

```bash
python scripts/check_contract.py --result /tmp/ga-l1/result.json --case examples/case.json
```

| 项目 | 实测值 |
|-|-|
| exit code | **0** |
| `checked.envelope_keys` | **18** |
| `checked.contract_fields` | **8** |
| `contract_covered_top_level` | 8 个全部命中（`colorblind_safe, deliverable, layer_names, provenance_attr, require_legend, require_scale_bar, resolution_dpi, target_format`） |
| `contract_absent` / `contract_null` | `[]` / `[]` |

## 3. ★ 契约四形态 × 边界值矩阵（本轴主判据）

```bash
python scripts/contract_matrix.py --out /tmp/cm --fail-on strict     # 26 行，约 61 s
python scripts/contract_matrix.py --out /tmp/cm --only boundary      # 只跑 10 行边界值
python scripts/contract_matrix.py --out /tmp/cm --only C19 --keep --verbose
```

| 项目 | 实测值 |
|-|-|
| exit code | **0**（`--fail-on strict`） |
| `rows` / `ok` / `mismatch` / `silent` / `crash` | **26 / 26 / 0 / 0 / 0** |
| `by_class` | form 8 · boundary 10 · illegal 6 · combo 2（全 ok） |
| `nulls_in_result_top_level` | **0 行** |
| `nulls_in_contract_fields` | **0 行** |
| `rows_with_nested_null_only` | 26（无 `--plan` 时 `plan.hash=null`，属声明过的形态） |
| `check_contract_failures` | **0 行** |
| `seconds_total` | **61.3 s**（26 次真实出图） |

关键行（每行都是一次真实子进程出图）：

| 行 | 注入 | 实测 |
|-|-|-|
| C08 | 三层嵌套对象 | 顶层 `export` 为 dict，逐值相等 |
| C09 | 空串 `""` | 顶层 `annotation = ""`（**没有**变成 null） |
| C11 / C12 | `0` / `0.0` | 类型分别为 int / float，未被 falsy 吞掉 |
| C15 | 4096 字符 | 回显长度 **4096**（未截断） |
| C16 | 字段 `null` | 归一化为 `""`，`uncertainty` 1 条（含 `null`） |
| C17 | 整个 `output_contract` 删除 | exit 0、信封 18 键齐全 |
| C19 / C21 / C22 | 契约是 list / int / bool | exit 0 + `uncertainty` 1 条（点名形态，见 §4） |
| C23 | 保留键冲突 | 案例值进 `output_contract_echo`，顶层仍是信封值 |
| C24 | 保留键 + `null` | echo 值为 `""`，顶层信封值未被覆盖 |
| C25 | 六形态 + Unicode/emoji | 7 字段全部命中，顶层 **25 键** |
| C26 | 50 元素列表 | 长度 **50**、逐值相等 |

**判据两端都测过**（同一命令、不同等级）：

| 命令 | exit | 说明 |
|-|-|-|
| `--fail-on strict` | **0** | 26/26 全 `ok` |
| `--fail-on silent`（默认） | **0** | `silent = 0`、`crash = 0` |
| `--fail-on none` | **0** | 只采数据（用于与别的版本对照） |

**守卫**：`--out` 指向包内目录 → exit **2**；基础 `--case` 不存在 → exit **2**；
`--only` 给不存在的类名/编号 → exit **2**（并列出可用 classes/ids）。

## 4. 静默通过：修复前 3 条 → 修复后 0 条

首轮实测（修复前）：C19/C21/C22 三行 `exit 0`、`status=success`、`uncertainty=[]`、`warnings=[]`
—— 非法契约被 `normalize_contract()` 归一化为 `{}`，**没有任何记录**。

修复（纯增量，`scripts/extract.py` **净 +7 行**（把 1 行 `normalize_contract(...)` 调用拆成 2 行 + 新增 1 个记录分支与 3 行注释；函数签名/CLI/退出码零改动））后实测：

```
case.json output_contract 形态非法（list）：已按空契约处理，字段不回显；契约应为对象或字符串。
case.json output_contract 形态非法（int）：已按空契约处理，字段不回显；契约应为对象或字符串。
case.json output_contract 形态非法（bool）：已按空契约处理，字段不回显；契约应为对象或字符串。
```

| 指标 | 修复前 | 修复后 |
|-|-|-|
| `ok` | 23 / 26 | **26 / 26** |
| `silent` | 3 | **0** |
| `mismatch` / `crash` | 0 / 0 | 0 / 0 |

## 5. 回归（不许因为修复而退化）

```bash
python scripts/fault_inject.py --out /tmp/fi --fail-on strict
```

| 项目 | 实测值 |
|-|-|
| exit code | **0** |
| `cases_run` / `ok` / `silent_failure` | **23 / 23 / 0** |
| 分类 | input 7 · template 6 · dependency 5 · contract 5 |

另外复核：`main.py` 冒烟仍 exit 0 / 26 键；`spec_lint.py` 两道门仍 exit 0。

## 6. 对照测量（只读）

```bash
python scripts/gain_harness.py --out /tmp/ga-l1 --case examples/case.json \
       --material examples/material.md --label A-skill
```

| 指标 | 实测值 |
|-|-|
| exit code | **0** |
| 分层 / 真文字节点 | 7 层 `layer:*` / 61 个真 `<text>` |
| 溯源覆盖 | **56 / 62 = 0.903** |
| 四要素覆盖 | 4/4 |
| 数值可定位 | 14 / 16（未定位 `001`、`6.5`） |
| 契约 | **8/8，verdict=complete**，顶层 26 键 |

## 7. 合规与体积

| 项目 | 实测值 | 上限 |
|-|-|-|
| 文件数 | **45** | 50 |
| 总字节 | **475,953** | 2 MB |
| 最大单文件 | `examples/output/spec.json` **42,984 B** | 500 KB |
| 扩展名 | `.md .py .json .txt` | 七种白名单 |
| 符号链接 / `__pycache__` / `.pyc` | 0 / 0 / 0 | 0 |
| 本机绝对路径 | **0 命中**（字体探测候选路径除外，见 `README.md` §1） | 0 |

## 8. 复现判据清单

1. `main.py` → exit 0，`result.json` 26 键。
2. `check_contract.py` → exit 0（18 信封 + 8 契约，无 null）。
3. **`contract_matrix.py --fail-on strict` → exit 0**，`ok=26`、`silent=0`、`crash=0`。
4. `fault_inject.py --fail-on strict` → exit 0（23/23）。
5. `gain_harness.py` → exit 0。
6. 包内无 `__pycache__`、无本机绝对路径；45 文件 / 475,953 B。

## 9. 未验证 / 边界（如实声明）

- 矩阵只覆盖"**声明 → 回显**"的形态与边界；**字段语义正确性**（如 `resolution_dpi=300`
  是否真的写进 SVG 画布）由 `audit.checks` / `spec_lint` 覆盖，不在本矩阵。
- **跨字段一致性**（声明了 `require_legend: true` 却没有图例）不在本矩阵范围。
- 最大只测到 4096 字符字符串与 50 元素列表；"契约本身几百 KB"未测。
- 并发、平台侧故障（挂载/配额/超时）不在本矩阵范围。
- 回显 ≠ 校验：Skill 忠实回显案例声明，不替案例判断声明是否合理（类型提示不符时以真实值为准）。
- 随包示例案例均为**合成示意**，不是平台正式案例，不代表正式成绩。
