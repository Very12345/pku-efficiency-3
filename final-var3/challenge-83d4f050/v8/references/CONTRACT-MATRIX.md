# CONTRACT-MATRIX.md — 契约四形态 × 边界值：逐行实测矩阵（v8 轴）

> 本文件是 v8 的**轴文档**。权威测量器 = `scripts/contract_matrix.py`（只依赖标准库）；
> 机器可读结果 = 包根 `contract_matrix_report.json`（本机实跑，不是预置答案）。
> 契约字段语义与硬门以 `references/OUTPUT_CONTRACT.md` 为**唯一权威**，本文件不改契约，
> 只把它的 §3（四形态回显）与 §7（G1–G8）在**真实主流程**上逐行验一遍。

## 1. 怎么跑

```bash
export SKILL_DIR=/skills/weekly-skill
python3 "$SKILL_DIR/scripts/contract_matrix.py" --help

# 全矩阵（40 行）→ 报告写到包根
python3 "$SKILL_DIR/scripts/contract_matrix.py" \
    --work /tmp/cm --report /tmp/contract_matrix_report.json

# 只跑某几行（子串匹配）；--json 只输出机器可读结果
python3 "$SKILL_DIR/scripts/contract_matrix.py" --only struct-oc-list,edge-collide-internal
python3 "$SKILL_DIR/scripts/contract_matrix.py" --json > /tmp/cm.json
```

退出码：`0` = 矩阵跑完；`2` = **控制行**（不注入契约的原样 case）就不通 → 环境有问题、结论不可用；`4` = 参数错误。
行内出现 `silent_gap` **不会**让本脚本非零退出——它是**被测对象**（本包流水线）的行为。

每一行做三件事：① 造一份注入了契约的 `case.json`（真实案例目录实拷贝）；
② 跑**真实** `scripts/main.py`（`--case/--model-file/--out/--formats svg,png,pdf`，**不使用** `--materials-dir`）；
③ 再跑独立检查器 `scripts/check_contract.py --result … --case …`。

## 2. 三层判定（列的含义）

| 层 | 取值 | 来源 |
|-|-|-|
| L1 主流程 | `exit` / `status` / `g2` | `main.py` 退出码、`result.json.status`、`result.json.gates.g2_contract_echo.pass` |
| L2 独立检查器 | `cc` | `check_contract.py` 退出码与失败项 id（C01–C07） |
| L3 产物本身 | 回显 | 声明字段是否出现、回显值的 JSON 类型、顶层是否有 null、`uncertainty`/`change_records` 是否留痕 |

**分类规则**（与 `contract_matrix_report.json → classification_rules` 逐字一致）：

| 分类 | 判定 |
|-|-|
| `ok` | 声明键全出现 + 回显类型与声明形态一致（或无声明键） |
| `fill_documented` | 只有"空对象契约/文档允许的空填充"类问题，无形态违规 |
| `silent_gap` | 存在**形态违规**（键丢失 / 类型不符 / 契约容器非映射 / 无 result.json），而 **L1 与 L2 全 pass** |
| `flagged` | 同样的形态违规**被某一层抓到**（g2 fail / `check_contract` 非零 / status 降级） |
| `documented_but_untraced`（附加列） | 声明值被丢弃或压平（文档允许），但 `uncertainty` 与 `change_records` 里**没有任何留痕** |

## 3. 总览（40 行实测）

| 分类 | 行数 | 行 id |
|-|-|-|
| `ok` | **27** | `control-base` `form1-str-literal` `form1-str-empty` `form1-str-long` `form1-str-cjk` `form1-str-key-long` `form1-str-key-dot` `form2-list` `form2-list-empty` `form2-list-200` `form3-bool-true` `form3-bool-typed` `form4-num-int` `form4-num-zero` `form4-num-float` `form4-num-typed` `form4-dict-literal` `form4-dict-empty` `form4-dict-typed` `typed-str` `typed-list` `typed-list-annotated` `edge-nested` `edge-typed-empty-obj` `edge-collide-envelope` `edge-many-fields` `struct-oc-missing` |
| `fill_documented` | **1** | `edge-empty-contract` |
| **`silent_gap`** | **8** | `struct-oc-list` `struct-oc-str` `struct-oc-num` `struct-oc-bool` `struct-oc-null` `edge-null` `edge-typed-invalid` `edge-collide-caseid-typed` |
| `flagged` | **4** | `edge-collide-internal`（`cc=1`，C05 抓到） `struct-case-missing` `struct-case-notjson` `struct-case-notobject`（退出码 **1**） |
| 附加：`documented_but_untraced` | **15** | 见 §6 |

控制行（原样 `examples/case.json`，不注入）：`exit=0` · `status=success` · `g2=true` · `check_contract exit=0`
⇒ 后面每一行的差异都只能归因于**注入本身**，不是"本来就这样"。

环境：CPython 3.13.9 / win32；`--formats svg,png,pdf` / `--dpi 150`。

## 4. 四形态 × 边界值逐行实测（摘录关键行）

`echo` 列格式：`回显类型(回显值)`；`声明`列是注入到 `case.json.output_contract` 的值。

| 行 id | 形态/边界 | 声明 | 实测回显 | L1 exit/status/g2 | L2 cc | 判定 |
|-|-|-|-|-|-|-|
| `control-base` | 控制组 | `{"custom_demo_field":"示例…","custom_list_field":["示例","列表"]}` | `str("")` · `array([])` | 0 / success / ✅ | 0 | ok（值未回显 → 附加列） |
| `form1-str-literal` | ① 标量 str | `{"c_str":"hello"}` | `str("")` | 0 / success / ✅ | 0 | ok |
| `form1-str-empty` | 边界 空串 | `{"c_str_empty":""}` | `str("")` | 0 / success / ✅ | 0 | ok |
| `form1-str-long` | 边界 超长 4096 | `{"c_str_long":"x"×4096}` | `str("")` | 0 / success / ✅ | 0 | ok |
| `form1-str-cjk` | 非 ASCII | `{"c_str_cjk":"机制图—通路 ✓"}` | `str("")` | 0 / success / ✅ | 0 | ok |
| `form1-str-key-long` | 边界 200 字符键名 | `{"k"×200:"v"}` | `str("")` | 0 / success / ✅ | 0 | ok |
| `form1-str-key-dot` | 键名含 `.` `[0]` | `{"a.b":"v","x[0]":"w"}` | `str("")`×2 | 0 / success / ✅ | 0 | ok |
| `form2-list` | ② 容器 list | `{"c_list":["a","b"]}` | `array([])` | 0 / success / ✅ | 0 | ok |
| `form2-list-empty` | 边界 空数组 | `{"c_list_empty":[]}` | `array([])` | 0 / success / ✅ | 0 | ok |
| `form2-list-200` | 边界 200 项 | `{"c_list_big":[0…199]}` | `array([])` | 0 / success / ✅ | 0 | ok |
| `form3-bool-true` | ③ 布尔 | `{"c_bool":true}` | `bool(false)` | 0 / success / ✅ | 0 | ok |
| `form3-bool-typed` | ③ typed bool | `{"c_bool_typed":{"type":"bool"}}` | `bool(false)` | 0 / success / ✅ | 0 | ok |
| `form4-num-int` | ④ 数值 | `{"c_num":150}` | `number(0)` | 0 / success / ✅ | 0 | ok |
| `form4-num-zero` | 边界 0 | `{"c_num_zero":0}` | `number(0)` | 0 / success / ✅ | 0 | ok |
| `form4-num-float` | 边界 浮点 | `{"c_num_float":1.5}` | `number(0)` | 0 / success / ✅ | 0 | ok |
| `form4-num-typed` | ④ typed number | `{"c_num_typed":{"type":"number"}}` | `number(0)` | 0 / success / ✅ | 0 | ok |
| `form4-dict-literal` | ④ 字典 | `{"c_obj":{"a":1}}` | `object({})` | 0 / success / ✅ | 0 | ok |
| `form4-dict-empty` | 边界 空对象 | `{"c_obj_empty":{}}` | `object({})` | 0 / success / ✅ | 0 | ok |
| `form4-dict-typed` | ④ typed dict | `{"c_obj_typed":{"type":"dict"}}` | `object({})` | 0 / success / ✅ | 0 | ok |
| `typed-str` / `typed-list` / `typed-list-annotated` | typed 声明 | `{"type":"str"}` / `{"type":"list"}` / `{"type":"list","note":"x"}` | `str("")` / `array([])` / `array([])` | 0 / success / ✅ | 0 | ok |
| `edge-many-fields` | 边界 60 个字段 | 60 × `{"c_00":0…}` | 全部出现（60/60，number） | 0 / success / ✅ | 0 | ok |
| `edge-nested` | 边界 嵌套声明 | `{"c_nested":{"a":{"b":1}}}` | `object({})`（嵌套被**压平**） | 0 / success / ✅ | 0 | ok（附加列：无留痕） |
| `edge-typed-empty-obj` | 边界 typed `{}` | `{"c_t_empty":{}}` | `object({})` | 0 / success / ✅ | 0 | ok |
| `edge-collide-envelope` | 键与信封同名 | `{"status":"CASE_WANTS_THIS"}` | `str("success")`（**真实值优先**） | 0 / success / ✅ | 0 | ok（附加列） |
| `struct-oc-missing` | 无 `output_contract` 键 | （键不存在） | 无要求 | 0 / success / ✅ | 0 | ok |
| `edge-empty-contract` | `output_contract = {}` | `{}` | 无要求 | 0 / success / ✅ | 0 | fill_documented |

## 5. 静默通过清单（8 行，**本次轴的核心发现**）

| 行 id | 注入 | 实测发生了什么 | L1 | L2 | 为什么叫"静默" |
|-|-|-|-|-|-|
| `struct-oc-list` | `output_contract = ["a","b"]` | **整个契约被忽略**（`apply_output_contract()` 对非映射直接 return；`_echo_missing` 因 `isinstance(oc,dict)` 为假也算空） | 0 / success / g2 ✅ | 0（C05 报"无 output_contract"或跳过） | 契约容器非法却**三层全绿**，没有任何一层报告"你的契约没生效" |
| `struct-oc-str` | `output_contract = "abc"` | 同上 | 0 / success / ✅ | 0 | 同上 |
| `struct-oc-num` | `output_contract = 0` | 同上（`0` 为假值，连 `if case_json.get(...)` 都不进） | 0 / success / ✅ | 0 | 同上 |
| `struct-oc-bool` | `output_contract = true` | 同上 | 0 / success / ✅ | 0 | 同上 |
| `struct-oc-null` | `output_contract = null`（键存在） | 同上；与"键不存在"在检查里**不可区分** | 0 / success / ✅ | 0 | 同上 |
| `edge-null` | `{"c_null": null}` | 回显 `""`（文档"禁止 null"允许） | 0 / success / ✅ | 0 | 声明的**是不存在**（null）却被静默改写成空串，无留痕 |
| `edge-typed-invalid` | `{"c_t_bad":{"type":"tuple"}}` | 回显 `""`（未知类型名落到 `EMPTY_BY_TYPE.get(..., "")`） | 0 / success / ✅ | 0 | 非法类型名被**静默吞掉**，不报错、不降级 |
| `edge-collide-caseid-typed` | `{"case_id": 12345}` | 回显 `str("example-egfr-mapk")`（信封真实值优先） | 0 / success / ✅ | 0（C05 只查**键是否存在**） | 声明类型与实际类型冲突，**没有任何检查器校验声明类型** |

> 归纳成一条可操作结论：**本包的三层检查都只校验"键是否存在"，不校验"契约容器是否合法"与"声明类型是否被满足"。**
> 因此契约轴上的静默通过集中在这两类上，而不是在"四形态本身"上（四形态 27 行全部 `ok`）。

## 6. 文档允许但无留痕（15 行，附加列）

`documented_but_untraced` = 声明值被按 `OUTPUT_CONTRACT.md §3` 的空值填充规则**替换**掉了
（`"hello"→""`、`["a","b"]→[]`、`150→0`、`{"a":1}→{}`、嵌套→`{}`），
而 `result.json.uncertainty` 与 `change_records` 里**没有**任何一条提到"契约/该字段"。

命中的 15 行：`control-base` `form1-str-literal` `form1-str-cjk` `form1-str-long` `form1-str-key-long`
`form1-str-key-dot` `form2-list` `form2-list-200` `form3-bool-true` `form4-num-int` `form4-num-float`
`form4-dict-literal` `edge-nested` `edge-collide-envelope` `edge-many-fields`。

这是**设计而非 bug**（§3 明说"未命中 pipeline 真实值时按声明形态填空"），
但它有一个真实使用后果：**案例作者写进 `output_contract` 的字面量不会被当作"默认值"回显**，
只会回显该形态的空值（`""`/`[]`/`{}`/`0`/`false`），且不留痕。
⇒ 实践建议（写进 `references/failure-modes.md` FM-C 系列）：把 `output_contract` 里写的字面量当**类型声明**用，
不要期望它成为值；需要默认值就让 Skill 自己在 `result.json` 里写。

## 7. 被抓住的 4 行（说明"检查确实有效"，也给出边界）

| 行 id | 注入 | 实测 | 抓它的那一层 |
|-|-|-|-|
| `edge-collide-internal` | `{"_echo_missing": "declared"}`（与流水线内部临时键**同名**） | 字段在 `g2` 判定时存在 → `g2=true`；随后 `del result["_echo_missing"]` 把它删掉 → 最终 `result.json` **没有**这个字段 | **独立检查器**：`check_contract.py` 退出码 1，失败项 `C05`（"缺回显: _echo_missing"） |
| `struct-case-missing` | `--case` 指向不存在的文件 | 无 `result.json`；stderr = `未找到 case.json：请用 --case 指定…`；退出码 **1** | 退出码非 0（`flagged`） |
| `struct-case-notjson` | `case.json` 非法 JSON | 无 `result.json`；stderr 尾部 = `json.decoder.JSONDecodeError: Expecting property name enclosed in double quotes: line 1 column 3 (char 2)`；退出码 **1**，且**无 traceback 包装说明** | 同上 |
| `struct-case-notobject` | `case.json` 是数组 | 无 `result.json`；stderr 尾部 = `AttributeError: 'list' object has no attribute 'get'`；退出码 **1** | 同上 |

**`edge-collide-internal` 是本轴最有价值的一行**：它证明"主流程自带的门（`g2`）会漏，而独立检查器能补"。
⇒ 交付流程里 `check_contract.py` 不能省（它本来就在 `references/OUTPUT_CONTRACT.md §9` 的验收命令里）。

**未文档化的退出码**：`main.py` 的 docstring 只声明 `0/2/3`，而上述三行实测退出码 **1**
（`SystemExit(str)` 与未捕获异常都是 1）。矩阵把这点记在 `summary.undocumented_exit_codes = [1]`。
调用方若要区分"输入缺失"与"流水线降级"，**不能只看退出码**，必须看有没有 `result.json` 与 stderr。

## 8. 未覆盖声明（矩阵明确没测的，不要当成测过）

1. 非 UTF-8 编码的 `case.json`（`load_json` 固定 utf-8；行为等价于"非法 JSON"行，未单列）。
2. JSON **重复键**（解析器保留最后一个；矩阵不构造重复键）。
3. 平台固定**正式案例**的真实 `output_contract`（不可见，不猜测、不伪造）。
4. **CLI 参数轴**的边界（如 `--materials-dir` 传 list、`--formats` 空串）：属 CLI 轴，本矩阵只用
   `--case/--model-file/--out/--formats/--dpi`。
5. `result.json` **落盘之后**的消费者（平台评分器）如何解释这些字段：本矩阵只测本包的三层检查。
6. 并发写同一输出目录、磁盘写满、只读目录：属故障注入轴（`references/FAULT-MATRIX.md` 那类工作），不在契约轴内。
7. `output_contract` 的**键**不是字符串（JSON 语法上不可能）、键为超大集合（只测到 60 个字段）。

## 9. 复现本文件全部数字

```bash
export SKILL_DIR=/path/to/challenge-83d4f050
python3 "$SKILL_DIR/scripts/contract_matrix.py" \
    --work /tmp/cm --report /tmp/contract_matrix_report.json       # 退出码 0
python3 - <<'PY'
import json
d = json.load(open("/tmp/contract_matrix_report.json", encoding="utf-8"))
s = d["summary"]
print(s["control"], s["undocumented_exit_codes"])
for k in ("ok", "fill_documented", "silent_gap", "flagged"):
    print(k, len(s["by_verdict"][k]), s["by_verdict"][k])
print("untraced:", len(s["documented_but_untraced"]))
PY
```
