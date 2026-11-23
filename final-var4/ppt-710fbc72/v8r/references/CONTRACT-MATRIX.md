# CONTRACT-MATRIX — 契约四形态 × 边界值矩阵（逐行实测）

`references/OUTPUT_CONTRACT.md` 声称：case.json 里 `output_contract` 的**每一个键**
都会按声明的容器形态回显到 `result.json` 顶层，**绝不出现 `null` 占位**，并且
CP3 门 G3 会在不满足时判失败。本文件把这句话变成 26 个用例的实测记录：
每个用例只改契约的一处（一种容器形态，或一个边界值），跑真实管线，再跑**独立门**
`check_contract.py`，记录 exit / status / 回显键集合 / 实测容器类型 / 有没有 null /
result.json 顶层键数 / 产物落盘情况——**以及这次失败是"被谁发现"的**。

复核命令（`$RUN` 必须是包外可写目录；包内跑会留下 `__pycache__`，资源契约拒收）：

```bash
RUN=<包外目录>
python "$SKILL_DIR/scripts/contract_matrix.py" --skill "$SKILL_DIR" --run "$RUN"     --json "$RUN/contract_matrix_report.json" --markdown "$RUN/contract_matrix.md"
echo "exit=$?"        # 实测 exit 0
python "$SKILL_DIR/scripts/contract_matrix.py" --skill "$SKILL_DIR" --list   # 只看用例清单
```

---

## 1. 结论（实测）

| 判据 | 结果 |
|-|-|
| 用例总数 | **26**（A 容器形态 6 · B 边界值 14 · C 输入完整性 6） |
| 按声明通过 | **26** |
| **静默通过**（违规但 exit 0 + `success` + 独立门也 0） | **0** |
| 被独立门拦下 | 0 |
| 顶层出现 `null` 占位的用例 | **0**（26/26） |
| 契约键未回显的用例 | **0**（在契约本身是对象的 20 个用例中） |
| 脚本退出码 | **0** |

## 2. "静默通过"的判定口径

一个用例只有同时满足下面三条才算**静默通过**，否则不算：

1. 实测结果违反了该用例声明的判据（exit / status / 全键回显 / 无 null / 容器类型）；
2. 管线自己 **exit 0 且 `status=success`**（没承认有问题）；
3. **独立门 `check_contract.py` 也返回 0**（第二道防线也没拦住）。

任何一条不成立就分别记为 `被门拦下`（第 3 条不成立 = 验证器正常工作）或
`信封降级`（第 2 条不成立 = 管线承认失败）。这条口径是为了避免把"验证器抓到了"
误报成"缺陷"。

## 3. 容器形态（A 族）：6/6 按声明回显、类型不变

| 契约声明 | 类型 | 实测回显值 | 实测类型 | 结论 |
|-|-|-|-|-|
| `{"k_str": "hello"}` | string | `""` | str | 类型保持，取类型默认值 |
| `{"k_list": ["a","b"]}` | array | `[]` | list | 同上 |
| `{"k_obj": {"x": 1}}` | object | `{}` | dict | 同上 |
| `{"k_num": 7}` | number | `0` | int | 同上 |
| `{"k_bool": true}` | boolean | `false` | bool | 同上 |
| `{"k_nest": {"a": [{"b": 1}]}}` | nested | `{}` | dict | 按**顶层**声明类型填；不做深拷贝 |

**为什么要取类型默认值而不是把声明值原样抄下去**：抄下去会把"契约想让你交付什么"
伪装成"本次运行真的产出了什么"。类型默认值是**诚实的中性值**（空/0/false），而且
不是 `null`——所以既满足"无 null 占位"，也没有伪造产物。

## 4. 边界值（B 族）：14/14 按声明

| 边界 | 实测 | 关键结论 |
|-|-|-|
| 空串 `""` | 回显 `""` | 空串与"缺失"可区分（键仍在） |
| 空数组 `[]` | 回显 `[]` | 同上 |
| 空对象 `{}` | 回显 `{}` | 同上 |
| 数值 `0` | 回显 `0` | **falsy 值没有被 `if value:` 吞掉** |
| 布尔 `false` | 回显 `false` | 同上 |
| `null` | 回显 `""` | **契约自己声明了 null，顶层仍不出现 null** ——"禁止 null 占位"是硬约束 |
| 超长值（3000 字符） | 回显 `""`（不截断、不报错） | 无已知语义的键不会被塞进长文本；长值不引发异常 |
| 超长键名（256 字符） | 原样出现在顶层 | 键名长度不设限 |
| 非 ASCII 键（`契约字段`） | 原样出现（`ensure_ascii=False`） | 中文键名可往返 |
| case.json **无** `output_contract` | 回显 0 键，G3 `missing=[]` | 没有契约 ≠ 契约未满足 |
| `output_contract = {}` | 回显 0 键，G3 全过 | 空契约也不判失败 |
| 语义未覆盖的键名 | 取类型默认值，且**不**进 `contract_echo_derived` | "派生值"只登记真的派生出来的键 |
| 语义已知的键（`preview_png`/`notes_per_slide`） | 回显 `true`，**进** `contract_echo_derived` | 真值 ≠ 类型默认值，且来源可查 |
| `preview_png: false` | 回显 **`true`**（实际产出了预览），G8 `preview_required=False` | 见 §5：这是**有意**的，不是缺陷 |

## 5. 实测到的两处"值被改写"（有意行为，逐条说明）

### 5.1 `preview_png: false` 被改写成 `true`

实测（用例 `B14-preview-false`）：契约写 `false`，`result.json` 顶层是 `true`，
`contract_echo_derived` 记为 `{"preview_png": true}`；同一份 `result.json` 的
`verification.contract_gates` 里 **G8 的 detail 是
`preview_required=False cover_exists=True`**。

**为什么是有意的**：`_derive_contract_value()` 对"这次运行真的产出了预览"这类键取
**本次运行真值**。契约里的 `false` 表达的是"这次不需要预览"，而管线确实产出了预览
（预览是默认交付物之一）——把真值写成 `false` 才是撒谎。关键是**这个改写不是静默的**：
它同时写进 `contract_echo_derived`（可查"这个 true 从哪来"），G8 也按契约原值判定
（`preview_required=False`），两条互不矛盾。

### 5.2 `output_contract` 不是对象 → 诚实失败 + 信封降级

实测（`C03-contract-not-object` / `C04-contract-list`）：契约写成字符串或数组时，
`main.py` 的 `_echo_output_contract()` 直接对契约调用 `.items()`，抛
`AttributeError`；异常被 `main()` 捕获，于是：

- `exit=1`、`status=failed`、`uncertainty=[{"item":"pipeline","note":"AttributeError: 'str' object has no attribute 'items'"}]`
- 但**大部分中间产物已经落盘**（`--out` 下 10 个文件，含 deck 与两张 PNG），
  `result.json` 只剩**失败信封 14 个顶层键**（完整信封 28 键）
- 独立门对 failed 结果返回 1（`valid=false`），所以**没有静默通过**

**这不是我们想要的行为**，但它是**诚实的**失败：管线承认失败、写下原因、保留已生成
的产物。ENVELOPE 降级（14 键 vs 28 键）是这条路径的已知代价，列在 §6。

## 6. 未覆盖声明（别把它当成全覆盖）

1. **`task.md` 里的契约不被识别**：本矩阵只测 `case.json.output_contract`。把契约
   写在 `task.md` 里不属于已实现路径（实测未测）。
2. **契约值类型与"已知语义键"的交叉**：只测了 `preview_png`/`notes_per_slide` 两个
   已知语义键；`_derive_contract_value()` 覆盖的其它前缀（template/evidence/editable/
   slide_count/figure…）**未逐条实测**。
3. **深层嵌套契约**：只测了"顶层键"（G3 的判定粒度就是顶层键），没有测"契约对象的
   子键是否也要回显"——按契约原文，判定粒度是顶层。
4. **非对象契约的修复**：本包**未修** `_echo_output_contract()` 的 `.items()` 崩溃
   （既有脚本保持逐字节不变）。要修的话只有一行（入口加
   `contract = contract if isinstance(contract, dict) else {}`），但那是**改变既有脚本
   行为**，超出本轴范围，故只报告不修。
5. **并发与超时**：未测多进程同时用同一 `--out`。
6. **`--out` 不可写**：该缺陷已由 `v4/v6` 的 `fault_inject.py` 覆盖（`d03`/`d04`），
   本矩阵不重复。

## 7. 与基线的差异（脚本层）

**`scripts/` 下既有脚本逐字节未改**（与基线同源）。本轴只新增
`scripts/contract_matrix.py`；CLI 参数、退出码语义一律未动。因此 §5.2 那条崩溃是
**基线已有的行为**，不是本轴引入的——本轴的贡献是把它**测出来并写清代价**。

---

# 附：实测报告原文

以下为 `contract_matrix.py` 的真实渲染输出（节），未做任何人工修改。

## 2. 逐用例实测（全部为真实运行）

| 用例 | 家族 | 实测 exit | 独立门 exit | 门 valid | 实测 status | 契约键 | 回显 | null | result 顶层键 | 判定 |
|-|-|-|-|-|-|-|-|-|-|-|
| `A01-string` | A | 0 | 0 | True | `success` | 1 | 1 | 0 | 25 | 按声明 |
| `A02-list` | A | 0 | 0 | True | `success` | 1 | 1 | 0 | 25 | 按声明 |
| `A03-object` | A | 0 | 0 | True | `success` | 1 | 1 | 0 | 25 | 按声明 |
| `A04-number` | A | 0 | 0 | True | `success` | 1 | 1 | 0 | 25 | 按声明 |
| `A05-boolean` | A | 0 | 0 | True | `success` | 1 | 1 | 0 | 25 | 按声明 |
| `A06-nested` | A | 0 | 0 | True | `success` | 1 | 1 | 0 | 25 | 按声明 |
| `B01-empty-string` | B | 0 | 0 | True | `success` | 1 | 1 | 0 | 25 | 按声明 |
| `B02-empty-list` | B | 0 | 0 | True | `success` | 1 | 1 | 0 | 25 | 按声明 |
| `B03-empty-object` | B | 0 | 0 | True | `success` | 1 | 1 | 0 | 25 | 按声明 |
| `B04-zero` | B | 0 | 0 | True | `success` | 1 | 1 | 0 | 25 | 按声明 |
| `B05-false` | B | 0 | 0 | True | `success` | 1 | 1 | 0 | 25 | 按声明 |
| `B06-null` | B | 0 | 0 | True | `success` | 1 | 1 | 0 | 25 | 按声明 |
| `B07-very-long` | B | 0 | 0 | True | `success` | 1 | 1 | 0 | 25 | 按声明 |
| `B08-very-long-key` | B | 0 | 0 | True | `success` | 1 | 1 | 0 | 25 | 按声明 |
| `B09-nonascii` | B | 0 | 0 | True | `success` | 1 | 1 | 0 | 25 | 按声明 |
| `B10-missing-key` | B | 0 | 0 | True | `success` | None | 0 | 0 | 24 | 按声明 |
| `B11-empty-contract` | B | 0 | 0 | True | `success` | 0 | 0 | 0 | 24 | 按声明 |
| `B12-unknown-prefix` | B | 0 | 0 | True | `success` | 1 | 1 | 0 | 25 | 按声明 |
| `B13-derived-known` | B | 0 | 0 | True | `success` | 2 | 2 | 0 | 26 | 按声明 |
| `B14-preview-false` | B | 0 | 0 | True | `success` | 1 | 1 | 0 | 25 | 按声明 |
| `C01-case-missing` | C | 1 | 1 | False | `failed` | None | 0 | 0 | 14 | 信封降级 |
| `C02-case-broken` | C | 1 | 1 | False | `failed` | None | 0 | 0 | 14 | 信封降级 |
| `C03-contract-not-object` | C | 1 | 1 | None | `failed` | None | 0 | 0 | 14 | 信封降级 |
| `C04-contract-list` | C | 1 | 1 | None | `failed` | None | 0 | 0 | 14 | 信封降级 |
| `C05-empty-case-object` | C | 0 | 0 | True | `partial` | None | 0 | 0 | 24 | 按声明 |
| `C06-case-is-directory` | C | 1 | 1 | False | `failed` | None | 0 | 0 | 14 | 信封降级 |

## 3. 契约回显逐键实测（容器形态有没有被改）

| 用例 | 键 | 契约声明类型 | 实测类型 | 实测值 | contract_echo_derived |
|-|-|-|-|-|-|
| `A01-string` | `k_str` | ? | str | `""` | 否 |
| `A02-list` | `k_list` | ? | list | `[]` | 否 |
| `A03-object` | `k_obj` | ? | dict | `{}` | 否 |
| `A04-number` | `k_num` | ? | int | `0` | 否 |
| `A05-boolean` | `k_bool` | ? | bool | `false` | 否 |
| `A06-nested` | `k_nest` | ? | dict | `{}` | 否 |
| `B01-empty-string` | `k_es` | ? | str | `""` | 否 |
| `B02-empty-list` | `k_el` | ? | list | `[]` | 否 |
| `B03-empty-object` | `k_eo` | ? | dict | `{}` | 否 |
| `B04-zero` | `k_z` | ? | int | `0` | 否 |
| `B05-false` | `k_f` | ? | bool | `false` | 否 |
| `B06-null` | `k_n` | ? | str | `""` | 否 |
| `B07-very-long` | `k_long` | ? | str | `""` | 否 |
| `B08-very-long-key` | `k_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` | ? | bool | `false` | 否 |
| `B09-nonascii` | `契约字段` | ? | str | `""` | 否 |
| `B12-unknown-prefix` | `zzz_unknown_field` | ? | bool | `false` | 否 |
| `B13-derived-known` | `preview_png` | ? | bool | `true` | 是 |
| `B13-derived-known` | `notes_per_slide` | ? | bool | `true` | 是 |
| `B14-preview-false` | `preview_png` | ? | bool | `true` | 是 |

## 4. 逐用例明细

#### `A01-string`（A-container）

- **注入**：output_contract = {k_str: "hello"}（字符串形态）
- **声明**：exit=0 / status=`success` / 全键回显=True / 无 null=True
- **实测**：exit=0；result.json 已写出；status=`success`；契约键 1；回显 1；缺键 无；null 占位 无；1.632s
- **G3 原文**：`True` — missing=[] null_placeholders=[]
- **产物**：deck 已落盘；`--out` 下文件 11 个；result.json 顶层键 **25**（完整信封 28 键）
- **判定**：按声明

#### `A02-list`（A-container）

- **注入**：output_contract = {k_list: ["a","b"]}（列表形态）
- **声明**：exit=0 / status=`success` / 全键回显=True / 无 null=True
- **实测**：exit=0；result.json 已写出；status=`success`；契约键 1；回显 1；缺键 无；null 占位 无；1.517s
- **G3 原文**：`True` — missing=[] null_placeholders=[]
- **产物**：deck 已落盘；`--out` 下文件 11 个；result.json 顶层键 **25**（完整信封 28 键）
- **判定**：按声明

#### `A03-object`（A-container）

- **注入**：output_contract = {k_obj: {"x": 1}}（对象形态）
- **声明**：exit=0 / status=`success` / 全键回显=True / 无 null=True
- **实测**：exit=0；result.json 已写出；status=`success`；契约键 1；回显 1；缺键 无；null 占位 无；1.379s
- **G3 原文**：`True` — missing=[] null_placeholders=[]
- **产物**：deck 已落盘；`--out` 下文件 11 个；result.json 顶层键 **25**（完整信封 28 键）
- **判定**：按声明

#### `A04-number`（A-container）

- **注入**：output_contract = {k_num: 7}（数值形态）
- **声明**：exit=0 / status=`success` / 全键回显=True / 无 null=True
- **实测**：exit=0；result.json 已写出；status=`success`；契约键 1；回显 1；缺键 无；null 占位 无；1.455s
- **G3 原文**：`True` — missing=[] null_placeholders=[]
- **产物**：deck 已落盘；`--out` 下文件 11 个；result.json 顶层键 **25**（完整信封 28 键）
- **判定**：按声明

#### `A05-boolean`（A-container）

- **注入**：output_contract = {k_bool: true}（布尔形态）
- **声明**：exit=0 / status=`success` / 全键回显=True / 无 null=True
- **实测**：exit=0；result.json 已写出；status=`success`；契约键 1；回显 1；缺键 无；null 占位 无；1.409s
- **G3 原文**：`True` — missing=[] null_placeholders=[]
- **产物**：deck 已落盘；`--out` 下文件 11 个；result.json 顶层键 **25**（完整信封 28 键）
- **判定**：按声明

#### `A06-nested`（A-container）

- **注入**：output_contract = {k_nest: {"a": [{"b": 1}]}}（嵌套对象）
- **声明**：exit=0 / status=`success` / 全键回显=True / 无 null=True
- **实测**：exit=0；result.json 已写出；status=`success`；契约键 1；回显 1；缺键 无；null 占位 无；1.53s
- **G3 原文**：`True` — missing=[] null_placeholders=[]
- **产物**：deck 已落盘；`--out` 下文件 11 个；result.json 顶层键 **25**（完整信封 28 键）
- **判定**：按声明

#### `B01-empty-string`（B-boundary）

- **注入**：边界：值为空串 ""
- **声明**：exit=0 / status=`success` / 全键回显=True / 无 null=True
- **实测**：exit=0；result.json 已写出；status=`success`；契约键 1；回显 1；缺键 无；null 占位 无；1.398s
- **G3 原文**：`True` — missing=[] null_placeholders=[]
- **产物**：deck 已落盘；`--out` 下文件 11 个；result.json 顶层键 **25**（完整信封 28 键）
- **判定**：按声明

#### `B02-empty-list`（B-boundary）

- **注入**：边界：值为空数组 []
- **声明**：exit=0 / status=`success` / 全键回显=True / 无 null=True
- **实测**：exit=0；result.json 已写出；status=`success`；契约键 1；回显 1；缺键 无；null 占位 无；1.557s
- **G3 原文**：`True` — missing=[] null_placeholders=[]
- **产物**：deck 已落盘；`--out` 下文件 11 个；result.json 顶层键 **25**（完整信封 28 键）
- **判定**：按声明

#### `B03-empty-object`（B-boundary）

- **注入**：边界：值为空对象 {}
- **声明**：exit=0 / status=`success` / 全键回显=True / 无 null=True
- **实测**：exit=0；result.json 已写出；status=`success`；契约键 1；回显 1；缺键 无；null 占位 无；1.498s
- **G3 原文**：`True` — missing=[] null_placeholders=[]
- **产物**：deck 已落盘；`--out` 下文件 11 个；result.json 顶层键 **25**（完整信封 28 键）
- **判定**：按声明

#### `B04-zero`（B-boundary）

- **注入**：边界：数值 0（falsy，容易被 `if value:` 吞掉）
- **声明**：exit=0 / status=`success` / 全键回显=True / 无 null=True
- **实测**：exit=0；result.json 已写出；status=`success`；契约键 1；回显 1；缺键 无；null 占位 无；1.393s
- **G3 原文**：`True` — missing=[] null_placeholders=[]
- **产物**：deck 已落盘；`--out` 下文件 11 个；result.json 顶层键 **25**（完整信封 28 键）
- **判定**：按声明

#### `B05-false`（B-boundary）

- **注入**：边界：布尔 false（falsy）
- **声明**：exit=0 / status=`success` / 全键回显=True / 无 null=True
- **实测**：exit=0；result.json 已写出；status=`success`；契约键 1；回显 1；缺键 无；null 占位 无；1.457s
- **G3 原文**：`True` — missing=[] null_placeholders=[]
- **产物**：deck 已落盘；`--out` 下文件 11 个；result.json 顶层键 **25**（完整信封 28 键）
- **判定**：按声明

#### `B06-null`（B-boundary）

- **注入**：边界：值为 null（契约自己声明了 null —— 容易把 null 传递到顶层）
- **声明**：exit=0 / status=`success` / 全键回显=True / 无 null=True
- **实测**：exit=0；result.json 已写出；status=`success`；契约键 1；回显 1；缺键 无；null 占位 无；1.462s
- **G3 原文**：`True` — missing=[] null_placeholders=[]
- **产物**：deck 已落盘；`--out` 下文件 11 个；result.json 顶层键 **25**（完整信封 28 键）
- **判定**：按声明

#### `B07-very-long`（B-boundary）

- **注入**：边界：超长值（单键 3000 字符）
- **声明**：exit=0 / status=`success` / 全键回显=True / 无 null=True
- **实测**：exit=0；result.json 已写出；status=`success`；契约键 1；回显 1；缺键 无；null 占位 无；1.504s
- **G3 原文**：`True` — missing=[] null_placeholders=[]
- **产物**：deck 已落盘；`--out` 下文件 11 个；result.json 顶层键 **25**（完整信封 28 键）
- **判定**：按声明

#### `B08-very-long-key`（B-boundary）

- **注入**：边界：超长键名（256 字符）
- **声明**：exit=0 / status=`success` / 全键回显=True / 无 null=True
- **实测**：exit=0；result.json 已写出；status=`success`；契约键 1；回显 1；缺键 无；null 占位 无；1.526s
- **G3 原文**：`True` — missing=[] null_placeholders=[]
- **产物**：deck 已落盘；`--out` 下文件 11 个；result.json 顶层键 **25**（完整信封 28 键）
- **判定**：按声明

#### `B09-nonascii`（B-boundary）

- **注入**：边界：非 ASCII 键名（中文键）
- **声明**：exit=0 / status=`success` / 全键回显=True / 无 null=True
- **实测**：exit=0；result.json 已写出；status=`success`；契约键 1；回显 1；缺键 无；null 占位 无；1.499s
- **G3 原文**：`True` — missing=[] null_placeholders=[]
- **产物**：deck 已落盘；`--out` 下文件 11 个；result.json 顶层键 **25**（完整信封 28 键）
- **判定**：按声明

#### `B10-missing-key`（B-boundary）

- **注入**：边界：case.json **完全没有** output_contract 键
- **声明**：exit=0 / status=`success` / 全键回显=True / 无 null=True
- **实测**：exit=0；result.json 已写出；status=`success`；契约键 None；回显 0；缺键 无；null 占位 无；1.529s
- **G3 原文**：`True` — missing=[] null_placeholders=[]
- **产物**：deck 已落盘；`--out` 下文件 11 个；result.json 顶层键 **24**（完整信封 28 键）
- **判定**：按声明

#### `B11-empty-contract`（B-boundary）

- **注入**：边界：output_contract = {}（空对象）
- **声明**：exit=0 / status=`success` / 全键回显=True / 无 null=True
- **实测**：exit=0；result.json 已写出；status=`success`；契约键 0；回显 0；缺键 无；null 占位 无；1.677s
- **G3 原文**：`True` — missing=[] null_placeholders=[]
- **产物**：deck 已落盘；`--out` 下文件 11 个；result.json 顶层键 **24**（完整信封 28 键）
- **判定**：按声明

#### `B12-unknown-prefix`（B-boundary）

- **注入**：边界：语义未覆盖的键名（`zzz_unknown_field`）
- **声明**：exit=0 / status=`success` / 全键回显=True / 无 null=True
- **实测**：exit=0；result.json 已写出；status=`success`；契约键 1；回显 1；缺键 无；null 占位 无；1.467s
- **G3 原文**：`True` — missing=[] null_placeholders=[]
- **产物**：deck 已落盘；`--out` 下文件 11 个；result.json 顶层键 **25**（完整信封 28 键）
- **判定**：按声明

#### `B13-derived-known`（B-boundary）

- **注入**：对照：语义已知的键（`preview_png` / `notes_per_slide`）
- **声明**：exit=0 / status=`success` / 全键回显=True / 无 null=True
- **实测**：exit=0；result.json 已写出；status=`success`；契约键 2；回显 2；缺键 无；null 占位 无；1.586s
- **G3 原文**：`True` — missing=[] null_placeholders=[]
- **运行期派生回显**：`{"preview_png": true, "notes_per_slide": true}`
- **产物**：deck 已落盘；`--out` 下文件 11 个；result.json 顶层键 **26**（完整信封 28 键）
- **判定**：按声明

#### `B14-preview-false`（B-boundary）

- **注入**：边界：`preview_png: false`（G8 的预览要求随之关闭）
- **声明**：exit=0 / status=`success` / 全键回显=True / 无 null=True
- **实测**：exit=0；result.json 已写出；status=`success`；契约键 1；回显 1；缺键 无；null 占位 无；1.477s
- **G3 原文**：`True` — missing=[] null_placeholders=[]
- **运行期派生回显**：`{"preview_png": true}`
- **产物**：deck 已落盘；`--out` 下文件 11 个；result.json 顶层键 **25**（完整信封 28 键）
- **判定**：按声明

#### `C01-case-missing`（C-input）

- **注入**：输入缺陷：--case 指向不存在的文件
- **声明**：exit=1 / status=`failed` / 全键回显=False / 无 null=True
- **实测**：exit=1；result.json 已写出；status=`failed`；契约键 None；回显 0；缺键 无；null 占位 无；0.766s
- **G3 原文**：`True` — missing=[] null_placeholders=[]
- **stderr 末行**：`main FAILED: [Errno 2] No such file or directory: '<RUN>\\cases\\C01-case-missing\\input\\absent.json'`
- **产物**：deck 未落盘；`--out` 下文件 1 个；result.json 顶层键 **14**（完整信封 28 键）
- **判定**：信封降级（诚实失败）

#### `C02-case-broken`（C-input）

- **注入**：输入缺陷：case.json 被截断（非法 JSON）
- **声明**：exit=1 / status=`failed` / 全键回显=False / 无 null=True
- **实测**：exit=1；result.json 已写出；status=`failed`；契约键 None；回显 0；缺键 无；null 占位 无；0.814s
- **G3 原文**：`True` — missing=[] null_placeholders=[]
- **stderr 末行**：`main FAILED: Expecting value: line 1 column 32 (char 31)`
- **产物**：deck 未落盘；`--out` 下文件 1 个；result.json 顶层键 **14**（完整信封 28 键）
- **判定**：信封降级（诚实失败）

#### `C03-contract-not-object`（C-input）

- **注入**：输入缺陷：output_contract 是**非对象**（字符串 "oops"）
- **声明**：exit=1 / status=`failed` / 全键回显=False / 无 null=True
- **实测**：exit=1；result.json 已写出；status=`failed`；契约键 None；回显 0；缺键 无；null 占位 无；1.502s
- **stderr 末行**：`main FAILED: 'str' object has no attribute 'items'`
- **产物**：deck 未落盘；`--out` 下文件 10 个；result.json 顶层键 **14**（完整信封 28 键）
- **判定**：信封降级（诚实失败）

#### `C04-contract-list`（C-input）

- **注入**：输入缺陷：output_contract 是**数组** ["a","b"]
- **声明**：exit=1 / status=`failed` / 全键回显=False / 无 null=True
- **实测**：exit=1；result.json 已写出；status=`failed`；契约键 None；回显 0；缺键 无；null 占位 无；1.664s
- **stderr 末行**：`main FAILED: 'list' object has no attribute 'items'`
- **产物**：deck 未落盘；`--out` 下文件 10 个；result.json 顶层键 **14**（完整信封 28 键）
- **判定**：信封降级（诚实失败）

#### `C05-empty-case-object`（C-input）

- **注入**：输入缺陷：case.json = {}（完全空对象）
- **声明**：exit=0 / status=`partial` / 全键回显=True / 无 null=True
- **实测**：exit=0；result.json 已写出；status=`partial`；契约键 None；回显 0；缺键 无；null 占位 无；1.344s
- **G3 原文**：`True` — missing=[] null_placeholders=[]
- **产物**：deck 已落盘；`--out` 下文件 11 个；result.json 顶层键 **24**（完整信封 28 键）
- **判定**：按声明

#### `C06-case-is-directory`（C-input）

- **注入**：输入缺陷：--case 指向一个**目录**
- **声明**：exit=1 / status=`failed` / 全键回显=False / 无 null=True
- **实测**：exit=1；result.json 已写出；status=`failed`；契约键 None；回显 0；缺键 无；null 占位 无；0.925s
- **G3 原文**：`True` — missing=[] null_placeholders=[]
- **stderr 末行**：`main FAILED: [Errno 2] No such file or directory: '<RUN>\\cases\\C06-case-is-directory\\input'`
- **产物**：deck 未落盘；`--out` 下文件 1 个；result.json 顶层键 **14**（完整信封 28 键）
- **判定**：信封降级（诚实失败）

