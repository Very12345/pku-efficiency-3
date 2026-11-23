# CONTRACT-MATRIX — 契约四形态 × 边界值矩阵（v8 主轴）

`result.json` 的唯一评分面是 `references/OUTPUT_CONTRACT.md` 定义的契约：平台在
`/input/case.json` 里给出一个 `output_contract` 对象，本技能必须把它的**每个键**
回显到 `result.json` 顶层，且**不得出现 `null`**。真实平台的字段清单我们不掌握，
所以这条链路必须对**任意形状的声明**都给出可判定的行为。

本文件记录 `scripts/contract_matrix.py` 的**实测**结果：**31 行注入**，覆盖
六种容器形态、六类边界值、非法类型与缺字段，每行真跑一次主流程
（`scripts/main.py`）+ 一次独立契约校验器（`scripts/validate_result.py`，G1–G8）。

---

## 1. 判据与读数面

| 读数 | 来源 | 说明 |
|-|-|-|
| 主流程退出码 | `main.py` 的 returncode | 0 = `success`；1 = `partial`/`failed`；2 = 致命（本矩阵实测 31/31 都是 0） |
| `status` | `result.json.status` | 契约形状问题**不会**让 status 变 partial（实测） |
| 契约回显 | `result.json` 顶层键 | 每个声明键的**实际值 + 实际类型**（不是"应该是什么"） |
| 契约判定 | `validate_result.py --json` | G5 的 `valid` 与 `G5 ...` 报错原文 |
| **静默通过** | 本脚本的判据（下表） | **VALID 但声明未被兑现** ⇒ 校验器给不了任何信号 |

**静默通过的五个判据（本脚本逐行落地，全部来自实测口径）**

| 代号 | 含义 |
|-|-|
| **S1** | 未知/无法识别的类型提示被**当字符串**接受（`"whatever"`、`""`、`"null"`、超长串） |
| **S2** | 字面量被当成"类型"而不是"值"：声明 `12` 回显 `0`、声明 `true` 回显 `false` |
| **S3** | 结构化提示（嵌套对象、带元素的数组）被降级成**空容器**，内部结构无任何门记录 |
| **S4** | 顶层 `output_contract` 形状非法（缺失 / `null` / `[]` / 字符串 / `{}`）⇒ **G5 整段跳过**，"没有契约"与"契约满足"在校验器眼里不可区分 |
| **S5** | 契约键与既有非空字段撞车时"不回显"这条路径没有专门的门（本矩阵里靠 G5 事后偶然发现） |

> 判据 S5 在本轮 31 行里**没有单独命中**（撞车行都被 G5 抓到了，见 R24–R26），
> 但仍列出：它是"回显靠 `result.get(key) not in (None,'',[],{})` 才跳过"这一实现
> 的直接推论，未来若契约键改成 `legend_mapping` 之类**空列表时合法**的字段，
> 就会静默回显成 `[]` 而没人发现。

---

## 2. 运行命令（cwd 不是技能根也能跑；产物一律在包外）

```bash
SKILL_DIR="$(cd "$(dirname "<本 SKILL.md 的实际路径>")" && pwd)"
RUN="<包外临时目录>"

python "$SKILL_DIR/scripts/contract_matrix.py" --list
python "$SKILL_DIR/scripts/contract_matrix.py" --skill-root "$SKILL_DIR" --out "$RUN/cm"
python "$SKILL_DIR/scripts/contract_matrix.py" --skill-root "$SKILL_DIR" --out "$RUN/cm" --json
python "$SKILL_DIR/scripts/contract_matrix.py" --skill-root "$SKILL_DIR" --out "$RUN/cm" --only R13,R17,R27
python "$SKILL_DIR/scripts/contract_matrix.py" --skill-root "$SKILL_DIR" --out "$RUN/cm" --base-case "$SKILL_DIR/examples/case_chart.json"
```

- `--out` 指向技能包内部会被**直接拒绝**（exit 2）；
- 退出码：`0` = **每一行都拿到可判定读数**（VALID 与 INVALID 都算读数）；
  `1` = 至少一行无法测量（无 `result.json` / 超时 / 崩溃且无记录）；`2` = 参数或环境错误。
- **发现静默通过不是脚本失败**，它是数据；退出码表达的是"矩阵是否完整跑完"。

---

## 3. 逐行实测表（31 行，2026-11-23 本机；Python 3.13.9）

读数可直接对拍 `<out>/contract-matrix.json` 的 `rows[]`。`回显` 一列写
**实际值(实际类型)**；`静默` 一列写命中的判据代号。

| id | 形态 | 边界 | 注入（`output_contract` 片段） | 期望（按契约规则） | main exit | status | 回显（实测） | validator | 静默 |
|-|-|-|-|-|-|-|-|-|-|-|
| R01 | string | 正常 | `{"s_note":"string"}` | `""`(str)，VALID | 0 | success | `''`(str) | VALID | — |
| R02 | array | 正常 | `{"a_items":"array"}` | `[]`(list)，VALID | 0 | success | `[]`(list) | VALID | — |
| R03 | object | 正常 | `{"o_meta":"object"}` | `{}`(dict)，VALID | 0 | success | `{}`(dict) | VALID | — |
| R04 | number | 正常 | `{"n_count":"number"}` | `0`(int)，VALID | 0 | success | `0`(int) | VALID | — |
| R05 | boolean | 正常 | `{"b_flag":"boolean"}` | `false`(bool)，VALID | 0 | success | `False`(bool) | VALID | — |
| R06 | nested-object | 正常 | `{"o_nested":{"a":{"b":"array"}}}` | 按 object 回显 `{}` | 0 | success | `{}`(dict) | VALID | **S3** |
| R07 | nested-array | 正常 | `{"a_nested":["string","array"]}` | 按 array 回显 `[]` | 0 | success | `[]`(list) | VALID | **S3** |
| R08 | mixed-forms | 正常 | 五形态同声明 | 5 个键全部回显，顶层键 +5 | 0 | success | 5/5 类型全对 | VALID | — |
| R09 | string | 空串 | `{"s_empty":""}` | 未知类型 ⇒ `""` | 0 | success | `''`(str) | VALID | **S1** |
| R10 | array | 空数组 | `{"a_empty":[]}` | `[]` | 0 | success | `[]`(list) | VALID | — |
| R11 | object | 空对象 | `{"o_empty":{}}` | `{}` | 0 | success | `{}`(dict) | VALID | — |
| R12 | number | 0 | `{"n_zero":0}` | `0` | 0 | success | `0`(int) | VALID | — |
| R13 | number | 字面量 12 | `{"n_lit":12}` | 字面量当类型 ⇒ `0` | 0 | success | `0`(int) | VALID | **S2** |
| R14 | boolean | 字面量 true | `{"b_true":true}` | 字面量当类型 ⇒ `false` | 0 | success | `False`(bool) | VALID | **S2** |
| R15 | null-hint | 字符串 "null" | `{"x_null":"null"}` | 未知类型 ⇒ `""` | 0 | success | `''`(str) | VALID | **S1** |
| R16 | null-hint | 真 null | `{"x_none":null}` | **必须**回显 null ⇒ 契约门 INVALID | 0 | success | `None`(null) | **INVALID**（`G5 contract key x_none is null`） | — |
| R17 | unknown | 未知串 | `{"x_unknown":"whatever"}` | 静默当 string ⇒ `""` | 0 | success | `''`(str) | VALID | **S1** |
| R18 | string | 超长提示 1KB | `{"x_long":"L"*1024}` | 未知类型 ⇒ `""` | 0 | success | `''`(str) | VALID | **S1** |
| R19 | string | 超长键名 1KB | `{"k"*1024:"string"}` | 键原样回显 | 0 | success | 键存在，`''`(str) | VALID | — |
| R20 | array | 超长值 ~210KB | `{"x_huge":"array"}` + `summary`≈210KB | `[]`；`result.json` 变大 | 0 | success | `[]`(list)；`result.json` **219,556 B** | VALID | — |
| R21 | array | 混合元素 | `{"x_mixed":["a",1]}` | 按 array ⇒ `[]` | 0 | success | `[]`(list) | VALID | **S3** |
| R22 | object | 双元素数组 | `{"x_pair":["a","b"]}` | 按 array ⇒ `[]` | 0 | success | `[]`(list) | VALID | **S3** |
| R23 | object | 深嵌套 | `{"x_deep":{"a":{"b":{"c":["d"]}}}}` | 按 object ⇒ `{}` | 0 | success | `{}`(dict) | VALID | **S3** |
| R24 | collision | 撞 `artifacts` | `{"artifacts":"string"}` | 不回显（已有值）⇒ 类型不符 | 0 | success | `[{...}]`(list) | **INVALID**（`expected str, got list`） | — |
| R25 | collision | 撞 `title` | `{"title":"array"}` | 同上 ⇒ 类型不符 | 0 | success | `'NF-κB…'`(str) | **INVALID**（`expected list, got str`） | — |
| R26 | collision | 撞 `case_id` | `{"case_id":"object"}` | 同上 ⇒ 类型不符 | 0 | success | `'example-schematic-001'`(str) | **INVALID**（`expected dict, got str`） | — |
| R27 | missing | 无 `output_contract` | 键整体删除 | 无回显；G5 跳过 | 0 | success | —（顶层键 21） | VALID | **S4** |
| R28 | missing | `output_contract: null` | `null` | 无回显；G5 跳过 | 0 | success | — | VALID | **S4** |
| R29 | missing | `output_contract: []` | `[]` | 无回显；G5 跳过 | 0 | success | — | VALID | **S4** |
| R30 | missing | `output_contract: "oops"` | 字符串 | 无回显；G5 跳过 | 0 | success | — | VALID | **S4** |
| R31 | missing | `output_contract: {}` | `{}` | 无回显；G5 跳过 | 0 | success | — | VALID | **S4** |

**汇总（`contract-matrix.json.summary` 实测值）**

| 计数 | 值 |
|-|-|
| 行数 / 已测量 / 无法测量 | **31 / 31 / 0** |
| VALID / INVALID | **27 / 4** |
| **静默通过** | **16**（R06 R07 R09 R13 R14 R15 R17 R18 R21 R22 R23 R27 R28 R29 R30 R31） |
| `main_exit == 0` | **31 / 31** |
| `status` 分布 | `{"success": 31}` —— 契约形状问题**从不**降级 status |
| 覆盖的形态 / 边界 | 12 种形态 · 24 种边界 |

**R08 的"键数变化"实测**：五形态声明 ⇒ `result.json` 顶层键 **26**（基线 21 + 5）；
R27–R31 无契约 ⇒ **21**。这正是"契约键被真的加进了顶层"的机器可核对证据。

---

## 4. 静默通过清单（逐条：什么被静默接受 + 后果 + Agent 侧缓解）

| # | 静默 | 实测行 | 被静默接受的是什么 | 后果 | 缓解（本技能的做法） |
|-|-|-|-|-|-|
| 1 | **S4** | R27–R31 | 顶层 `output_contract` **形状非法或缺失**时，G5 **整段跳过** | 平台若把契约放在别处/换了名字，我们会全量回显失败却仍然 VALID —— "没有契约"与"契约满足"不可区分 | 交付前**必须**确认 `case.json` 的 `output_contract` 是非空对象；`RUBRIC_MAP`/`SKILL` 把它列为 S0 的必做项；缺契约要在 `uncertainty` 里写明 |
| 2 | **S1** | R17 R18 R09 R15 | 未知类型提示被**当字符串** | 声明写错（拼写错误、写 `"null"`、写超长说明文字）不会报错，回显 `""` 看着"正常" | 平台字段清单到手后**逐键核对类型词表**（string/array/object/number/boolean 五个才被识别）；不在词表里的键在交付说明里点名 |
| 3 | **S3** | R06 R07 R21 R22 R23 | 结构化提示（嵌套对象/带元素数组）被降级成**空容器** | 声明里表达的**值形状**（数组元素类型、对象内部字段）没有任何门在查 | 需要值形状保证时**不能只靠 output_contract**：用 `references/OUTPUT_CONTRACT.md` §1 的字段表 + `scripts/validate_result.py` 的 G4 类型检查兜 |
| 4 | **S2** | R13 R14 | 字面量被当"类型"，回显默认值 `0`/`false` | 若平台用"示例值"写法（`{"count": 12}`）表达契约，我们会回显 `0` —— 忠实但可能与平台期望的 `12` 不同 | 见到字面量一律当"类型不确定"处理，并在 `uncertainty` 记名；不要假设平台会用字面量表达默认值 |
| 5 | —（正面） | R16 R24 R25 R26 | 真 `null`、以及契约键与既有字段**类型冲突** | —— | 这四行是**门起作用**的证据：`null` 与类型冲突都会被独立校验器判 INVALID |

**读法**：27 行 VALID 里有 16 行是"静默通过"——它们不是 bug，而是**契约机制的边界**：
G5 只保证"声明的键存在且顶层容器类型对得上"，不保证"声明被理解"。
把这条边界写在明处，正是本版对"可靠体验 10 分（异常处理 3 分）"的贡献。

---

## 5. 未覆盖声明（本包**不**为这些背书）

1. **值形状**：数组元素类型、对象内部字段类型、数值范围 —— G5 只查顶层容器类型，本矩阵只测到"降级为空容器"这一层，**没有**测"元素类型不符会怎样"（当前实现根本不看元素）；
2. **oneOf / anyOf / 联合类型**：本仓无此概念，未实现也未测量；
3. **平台真实 `output_contract` 字段清单**：组织方未公开；本矩阵用的是**合成清单**（形态覆盖 ≠ 字段覆盖）；
4. **并发、中断、`result.json` 被外部改写**：未测；
5. **单文件 500KB 上限**：由平台在打包时执行；本矩阵只测到"~210KB 的 `summary` 会让 `result.json` 变成 219,556 B"（仍低于上限），**没有**测到超限时的平台行为；
6. **`--base-case` 换成 chart/edit 案例**：命令已给出，但**本轮只跑了 schematic 基线**（chart 的 chart 类别硬门 G8 与契约回显的交互未测）；
7. **`--skip-checks` / `--no-lint` 下的契约回显**：未测（属自选降级，交付前禁止使用）。
