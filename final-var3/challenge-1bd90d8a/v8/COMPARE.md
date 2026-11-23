# COMPARE.md — 对照方案（v8 契约四形态 × 边界值矩阵轴）

题面要求「使用增益」可验证。本文件说明本包提供的对照证据，以及哪些必须由平台提供。

## 1. 本包能提供的对照：同一份契约、三条判定路径

| 路径 | 命令 | 判定 |
|-|-|-|
| 主流程自报 | `main.py --case <case> --out <out>` | 退出码、`status`、`output_contract_applied` |
| 契约字段回显 | `check_contract.py --result <out>/result.json --case <case>` | `missing` / `null` / `contract_missing` |
| 交付硬门 | `figcheck.py --dir <out> --case <case>` | G2（声明字段全部出现且非 null） |

三条路径对同一份契约给出的结论**不总是一致** —— 这正是本版实测出来的东西：

| 现象 | 实测行数 | 含义 |
|-|-|-|
| 三条全绿但契约形态其实不在登记范围内 | 11/38 行 | 静默通过（分型见 `references/CONTRACT-MATRIX.md` §7） |
| `output_contract_applied=true` 但零字段回显 | 7/38 行 | 该布尔值**不能**当契约完整性用 |
| 主流程与校验器对同一份契约判断相反 | 1/38 行（B1 空字段名） | 口径分歧 |

⇒ 结论：**做契约对照时必须三条路径同时看**，任何一条单独用都会被上述三类情况骗过去。

## 2. 与「不加载 Skill 的基础 Agent」的对照口径（供组织方白板使用）

本包不提供自己的白板结果（题面禁止提交预制答案或正式案例输出）。它提供的是**可复用的判据**：

| 比较维度 | 可机器判定的量 | 来自 |
|-|-|-|
| 契约字段是否齐全 | `contract_missing` 列表 | `check_contract.py --json` |
| 契约门是否通过 | `gates.G2` | `figcheck.py --json` |
| 契约层是否有静默降级 | 注入矩阵的 verdict 分布 | `contract_matrix.py --json` |
| 输出信封是否诚实 | `status` 与 `gates.all_pass` 是否自洽（G8） | `figcheck.py --json` |

同一组命令对任何做法都成立，所以对照公平（同输入、同数据版本、同导出参数）。

## 3. 本包内部的三方对照（结构层面）

| 文件 | 角色 | 本版是否改动 |
|-|-|-|
| `scripts/*.py`（10 个既有入口） | 算法与 CLI 接口 | **逐字节不变** |
| `scripts/contract_matrix.py` | 本版新增的契约矩阵实测台 | 新增 |
| `references/*.md`（既有 6 份，含 `OUTPUT_CONTRACT.md`） | 契约、评分映射、失败模式等 | 逐字节不变（契约字段块逐字保留） |
| `references/CONTRACT-MATRIX.md` | 本版新增：38 行逐行实测 | 新增 |
| `contract_matrix_report.json` | 本版新增：机器可读实测证据（含矩阵指纹） | 新增 |

## 4. 诚实的边界

- 本包没有「不加载 Skill 的基础 Agent」的运行记录，也不伪造一份。
- 矩阵只覆盖自造字段与别名集合；真实平台案例的具体契约字段未知（未覆盖声明见
  `references/CONTRACT-MATRIX.md` §9）。
- 11 行静默通过是**登记在案的缺陷**，不是"已验证无问题"；本文件不掩饰这一点。
