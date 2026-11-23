# CONTRACT-MATRIX.md — 契约四形态 × 边界值：逐行实测（v8 轴）

> 下表每一行都是**真的注入了一份 case.json、真的跑了一遍主流程**之后的实测结果。
> 生成命令与机器可读原始证据见 §2 与同目录的 `contract_matrix_report.json`。
> 矩阵指纹 `matrix_digest = f4d21e46fff51c7e73886c42c0c5166965e9fc8beff2f897a13d58ff4faea2f0` —— 对「跑了哪些行、每行注入了什么」取 sha256，
> 换一批行它就会变，所以这份文档与那次运行是绑定的。

---

## 1. 为什么不能靠读代码确定

最终 `result.json` 的顶层形态由**三件事叠加**决定，任何一件单独看都会得出错误结论：

1. `apply_output_contract()` 的形态兼容逻辑（四形态 + 别名表 + 类型默认值）；
2. `if contract:` 的**真值语义** —— `{}` / `[]` / `0` / `null` 全都被当成「没有契约」；
3. `main.py` 在契约落地**之后**还会 `pop` 掉 `manifest_figures` / `warnings_collected` /
   `adjustments_collected` / `_pipeline` 四个内部瞬态键。

所以本台子把每一行都当成一次独立实验，并且**用两个独立校验器交叉判定**
（`figcheck.py` 的 G2 门、`check_contract.py` 的契约回显），避免「主流程说没问题 = 真没问题」。

## 2. 复跑命令

```bash
python "$SKILL_DIR/scripts/contract_matrix.py" \
    --case /input/case.json --workspace /app/work/cm \
    --out /app/work/cm/contract_matrix_report.json

# 定点复核某几行（编号见下表）
python "$SKILL_DIR/scripts/contract_matrix.py" --only A2,A4,D5,B1 --json
```

退出码：`0` = 全部行跑完且**无静默通过**；`2` = 存在静默通过；`1` = 用法或环境错误。
本次实测 exit **2**（存在静默通过，清单见 §7）；单次全矩阵耗时 70.49 秒
（38 行 × 每行 3 个子进程：主流程 + figcheck + check_contract）。

每一行落到一个 verdict：

| verdict | 含义 |
|-|-|
| `echo_complete` | 声明字段全部回显、非 null，容器类型也对得上 |
| `caught` | 有缺口，但被 main 退出码 / status / G2 / check_contract 任一捕获 |
| `silent_pass` | **有缺口却一路绿灯**：exit 0、status=completed、G2 通过、check_contract 通过，且 uncertainty 里没有一句关于契约的说明 |
| `no_contract` | 压根没有声明契约（缺键 / null / 假值 / 合法但零字段）—— 这是**合法**情形，不计入静默通过 |
| `run_error` | main.py 没产出可解析的 `result.json` |

本次判定分布：`{"echo_complete": 14, "silent_pass": 11, "caught": 5, "no_contract": 8}`

## 3. F 族：容器形态（四形态本身 + 等价写法）

| # | 注入的 `output_contract` | 形态合法 | 声明字段数 | main exit | status | applied | G2 | check_contract exit | 缺失字段 | 判定 | 分型 |
|-|-|-|-:|-|-|-|-|-|-:|-|-|
| **F1** | `["case_id", "status", "outputs", "editable_source"]` | ✅ | 4 | 0 | completed | True | True | 0 | 0 | `echo_complete` | - |
| **F2** | `{"alpha_s": "string", "beta_a": "array", "gamma_o": "object", "delt…` | ✅ | 5 | 0 | completed | True | True | 0 | 0 | `echo_complete` | - |
| **F3** | `{"fields": ["case_id", "sources", "field_mapping"]}` | ✅ | 3 | 0 | completed | True | True | 0 | 0 | `echo_complete` | - |
| **F4** | `{"fields": {"title": "string", "sources": "array", "gates": "object"}}` | ✅ | 3 | 0 | completed | True | True | 0 | 0 | `echo_complete` | - |
| **F5** | `{"fields": {"layer": {"type": "array"}}}` | ❌ | 1 | 0 | completed | True | True | 0 | 0 | `silent_pass` | `illegal_shape_tolerated` |
| **F6** | `["case_id", 123, null, {"x": 1}, true]` | ❌ | 1 | 0 | completed | True | True | 0 | 0 | `silent_pass` | `illegal_shape_tolerated` |
| **F7** | `{"fields": {"title": "string"}, "note": "extra"}` | ✅ | 1 | 0 | completed | True | True | 0 | 0 | `echo_complete` | - |

- **F1 形态①字段名列表 list[str]** — 期望：四字段全部回显；editable_source 走别名填充为 SVG 名列表；实测 `echo_complete`；result.json 顶层 26 键。
- **F2 形态②名称→类型 dict[str,str]** — 期望：五个未知名按声明类型给 ""/[]/{}/0/false，绝不为 null；实测 `echo_complete`；result.json 顶层 30 键。
- **F3 形态③嵌套 fields 列表** — 期望：与形态①等价；field_mapping 走别名给 "data_manifest.json"；实测 `echo_complete`；result.json 顶层 26 键。
- **F4 形态④嵌套 fields 映射** — 期望：三字段回显；gates 在契约落地时还是空对象，但最终被真实 gates 覆盖；实测 `echo_complete`；result.json 顶层 25 键。
- **F5 嵌套声明：类型位置写成对象** — 期望：类型不是字符串 → 落到默认 ""（实测确认，不是 []）；实测 `silent_pass`（`illegal_shape_tolerated`）；result.json 顶层 26 键。
- **F6 形态①混入非字符串/嵌套项** — 期望：非字符串项被忽略，只有 case_id 生效；不抛异常；实测 `silent_pass`（`illegal_shape_tolerated`）；result.json 顶层 25 键。
- **F7 形态④ + 顶层额外键** — 期望：额外的 note 键被忽略（fields 优先），只有 title 回显；实测 `echo_complete`；result.json 顶层 25 键。

## 4. B 族：边界值（空串 / 空数组 / 0 / 超长 / 非法类型 / null / 重复 / 怪键）

| # | 注入的 `output_contract` | 形态合法 | 声明字段数 | main exit | status | applied | G2 | check_contract exit | 缺失字段 | 判定 | 分型 |
|-|-|-|-:|-|-|-|-|-|-:|-|-|
| **B1** | `[""]` | ✅ | 1 | 2 | partial | True | False | 1 | 1 | `caught` | - |
| **B2** | `[]` | ✅ | 0 | 0 | completed | False | True | 0 | 0 | `no_contract` | - |
| **B3** | `["L0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef…` | ✅ | 1 | 0 | completed | True | True | 0 | 0 | `echo_complete` | - |
| **B4** | `{"n": 0}` | ❌ | 1 | 0 | completed | True | True | 0 | 0 | `silent_pass` | `illegal_shape_tolerated` |
| **B5** | `{"b": true}` | ❌ | 1 | 0 | completed | True | True | 0 | 0 | `silent_pass` | `illegal_shape_tolerated` |
| **B6** | `{"x": ["array"]}` | ❌ | 1 | 0 | completed | True | True | 0 | 0 | `silent_pass` | `illegal_shape_tolerated` |
| **B7** | `{"y": "数组"}` | ✅ | 1 | 0 | completed | True | True | 0 | 0 | `echo_complete` | - |
| **B8** | `[null, "case_id"]` | ❌ | 1 | 0 | completed | True | True | 0 | 0 | `silent_pass` | `illegal_shape_tolerated` |
| **B9** | `["case_id", "case_id"]` | ✅ | 2 | 0 | completed | True | True | 0 | 0 | `echo_complete` | - |
| **B10** | `{"title": "string", "sources": "array"}` | ✅ | 2 | 0 | completed | True | True | 0 | 0 | `echo_complete` | - |
| **B11** | `{"a.b/c": "string"}` | ✅ | 1 | 0 | completed | True | True | 0 | 0 | `echo_complete` | - |
| **B12** | `["figures"]` | ✅ | 1 | 0 | completed | True | True | 0 | 0 | `echo_complete` | - |

- **B1 字段名 = 空串** — 期望：空字段名被跳过；result.json 不应出现空键；实测 `caught`；result.json 顶层 25 键；声明字段在最终产物里消失：``；★ `output_contract_applied=true` 但零回显；★ main 与校验器对声明字段口径不一致。
- **B2 空数组（声明 0 个字段）** — 期望：[] 为假值 → main.py 视同「没有契约」，output_contract_applied=False；实测 `no_contract`；result.json 顶层 25 键。
- **B3 超长字段名（4097 字符）** — 期望：要么回显要么报错，但不得静默 + 无诊断；实测 `echo_complete`；result.json 顶层 26 键。
- **B4 数值声明 {"n": 0}** — 期望：类型值是数字 0（不是类型名）→ 落到默认 ""（实测确认）；实测 `silent_pass`（`illegal_shape_tolerated`）；result.json 顶层 26 键。
- **B5 布尔声明 {"b": true}** — 期望：类型值是布尔 → 落到默认 ""（实测确认）；实测 `silent_pass`（`illegal_shape_tolerated`）；result.json 顶层 26 键。
- **B6 非法类型名（数组当类型）{"x":["array"]}** — 期望：非字符串类型 → 默认 ""；若静默则点名；实测 `silent_pass`（`illegal_shape_tolerated`）；result.json 顶层 26 键。
- **B7 未登记的中文类型名 {"y":"数组"}** — 期望：类型名不在映射表 → 默认 ""（测试「四形态+任意类型名」的边界）；实测 `echo_complete`；result.json 顶层 26 键。
- **B8 列表混入 null** — 期望：null 被忽略，case_id 仍回显；实测 `silent_pass`（`illegal_shape_tolerated`）；result.json 顶层 25 键。
- **B9 重复声明同一字段** — 期望：幂等：只有一个 case_id 键，值正确；实测 `echo_complete`；result.json 顶层 25 键。
- **B10 超长取值（title ≈ 3605 字符）** — 期望：长取值原样回显，result.json 变大但不得截断/丢失；实测 `echo_complete`；result.json 顶层 25 键。
- **B11 怪键名 {"a.b/c":"string"}** — 期望：非法标识但合法 JSON 键 → 回显为空串；实测 `echo_complete`；result.json 顶层 26 键。
- **B12 键与 case.json 已有字段重名（figures）** — 期望：result 顶层被塞进一个 "" 的 figures 键（小心：这可能与输入语义冲突）；实测 `echo_complete`；result.json 顶层 26 键。

## 5. A 族：别名与内部瞬态键（契约与内部实现的接缝）

| # | 注入的 `output_contract` | 形态合法 | 声明字段数 | main exit | status | applied | G2 | check_contract exit | 缺失字段 | 判定 | 分型 |
|-|-|-|-:|-|-|-|-|-|-:|-|-|
| **A1** | `["editable_source", "editable_sources", "rendered_preview", "render…` | ✅ | 22 | 0 | completed | True | True | 0 | 0 | `echo_complete` | - |
| **A2** | `["warnings_collected"]` | ✅ | 1 | 2 | partial | True | False | 1 | 1 | `caught` | - |
| **A3** | `["_pipeline"]` | ✅ | 1 | 2 | partial | True | False | 1 | 1 | `caught` | - |
| **A4** | `["manifest_figures"]` | ✅ | 1 | 2 | partial | True | False | 1 | 1 | `caught` | - |
| **A5** | `["adjustments_collected"]` | ✅ | 1 | 2 | partial | True | False | 1 | 1 | `caught` | - |
| **A6** | `["artifacts_sha256"]` | ✅ | 1 | 0 | completed | True | True | 0 | 0 | `echo_complete` | - |
| **A7** | `["output_contract_applied", "steps"]` | ✅ | 2 | 0 | completed | True | True | 0 | 0 | `echo_complete` | - |

- **A1 20+ 别名一次性回显** — 期望：全部别名指向真实产物，不得有空串/null；实测 `echo_complete`；result.json 顶层 36 键。
- **A2 声明内部瞬态键 warnings_collected** — 期望：该键在契约落地后会被 main.py pop 掉 → G2 应当抓到；实测 `caught`；result.json 顶层 25 键；声明字段在最终产物里消失：`warnings_collected`。
- **A3 声明内部瞬态键 _pipeline** — 期望：同上（pop 名单：manifest_figures/warnings_collected/adjustments_collected/_pipeline）；实测 `caught`；result.json 顶层 25 键；声明字段在最终产物里消失：`_pipeline`。
- **A4 声明内部瞬态键 manifest_figures** — 期望：同上；实测 `caught`；result.json 顶层 25 键；声明字段在最终产物里消失：`manifest_figures`。
- **A5 声明内部瞬态键 adjustments_collected** — 期望：同上；实测 `caught`；result.json 顶层 25 键；声明字段在最终产物里消失：`adjustments_collected`。
- **A6 声明 artifacts_sha256（契约落地前已存在）** — 期望：已存在的真值不得被子默认覆盖 → 回显为真实哈希表；实测 `echo_complete`；result.json 顶层 25 键。
- **A7 声明 output_contract_applied / steps** — 期望：回显为真实布尔值与步骤流水；实测 `echo_complete`；result.json 顶层 25 键。

## 6. D 族：退化与非法形态（缺键 / null / 布尔 / 字符串 / 浮点 / fields 类型错 / 深嵌套）

| # | 注入的 `output_contract` | 形态合法 | 声明字段数 | main exit | status | applied | G2 | check_contract exit | 缺失字段 | 判定 | 分型 |
|-|-|-|-:|-|-|-|-|-|-:|-|-|
| **D1** | `"<deleted>"` | ❌ | 0 | 0 | completed | False | True | 0 | 0 | `no_contract` | - |
| **D2** | `null` | ❌ | 0 | 0 | completed | False | True | 0 | 0 | `no_contract` | - |
| **D3** | `{}` | ✅ | 0 | 0 | completed | False | True | 0 | 0 | `no_contract` | - |
| **D4** | `[]` | ✅ | 0 | 0 | completed | False | True | 0 | 0 | `no_contract` | - |
| **D5** | `true` | ❌ | 0 | 0 | completed | True | True | 0 | 0 | `silent_pass` | `illegal_shape_applied_true` |
| **D6** | `"case_id"` | ❌ | 0 | 0 | completed | True | True | 0 | 0 | `silent_pass` | `illegal_shape_applied_true` |
| **D7** | `0` | ❌ | 0 | 0 | completed | False | True | 0 | 0 | `no_contract` | - |
| **D8** | `{"fields": "case_id"}` | ❌ | 0 | 0 | completed | True | True | 0 | 0 | `silent_pass` | `illegal_shape_applied_true` |
| **D9** | `{"fields": {}}` | ✅ | 0 | 0 | completed | True | True | 0 | 0 | `no_contract` | - |
| **D10** | `{"fields": []}` | ✅ | 0 | 0 | completed | True | True | 0 | 0 | `no_contract` | - |
| **D11** | `{"fields": {"a": {"b": {"c": "array"}}}}` | ❌ | 1 | 0 | completed | True | True | 0 | 0 | `silent_pass` | `illegal_shape_tolerated` |
| **D12** | `3.14` | ❌ | 0 | 0 | completed | True | True | 0 | 0 | `silent_pass` | `illegal_shape_applied_true` |

- **D1 case.json 里没有 output_contract 键** — 期望：output_contract_applied=False；契约字段不要求回显（这是合法情形）；实测 `no_contract`；result.json 顶层 25 键。
- **D2 output_contract = null** — 期望：与 D1 等价；应记为未应用；实测 `no_contract`；result.json 顶层 25 键。
- **D3 output_contract = {}（空对象）** — 期望：{} 为假值 → 视同没有契约；★ 非法与否需实测；实测 `no_contract`；result.json 顶层 25 键。
- **D4 output_contract = []（空数组）** — 期望：同 B2/D3；实测 `no_contract`；result.json 顶层 25 键。
- **D5 output_contract = true（布尔）** — 期望：真值但非法形态 → ★ 重点看是否静默容忍；实测 `silent_pass`（`illegal_shape_applied_true`）；result.json 顶层 25 键；★ `output_contract_applied=true` 但零回显。
- **D6 output_contract = "case_id"（字符串）** — 期望：真值但非法形态 → ★ 重点看是否静默容忍；实测 `silent_pass`（`illegal_shape_applied_true`）；result.json 顶层 25 键；★ `output_contract_applied=true` 但零回显。
- **D7 output_contract = 0（假值数字）** — 期望：假值 → 视同没有契约；实测 `no_contract`；result.json 顶层 25 键。
- **D8 {"fields": "case_id"}（fields 是字符串）** — 期望：非法 → ★ 看是否有诊断；实测 `silent_pass`（`illegal_shape_applied_true`）；result.json 顶层 25 键；★ `output_contract_applied=true` 但零回显。
- **D9 {"fields": {}}（空映射）** — 期望：真值但声明 0 字段 → applied=True 且什么都不回显；实测 `no_contract`；result.json 顶层 25 键；★ `output_contract_applied=true` 但零回显。
- **D10 {"fields": []}（空列表）** — 期望：同 D9；实测 `no_contract`；result.json 顶层 25 键；★ `output_contract_applied=true` 但零回显。
- **D11 深嵌套 {"fields":{"a":{"b":{"c":"array"}}}}** — 期望：只取第一层键 a；a 的类型值是对象 → 默认 ""；实测 `silent_pass`（`illegal_shape_tolerated`）；result.json 顶层 26 键。
- **D12 output_contract = 3.14（浮点）** — 期望：真值但非法形态 → ★ 重点看是否静默容忍；实测 `silent_pass`（`illegal_shape_applied_true`）；result.json 顶层 25 键；★ `output_contract_applied=true` 但零回显。

## 7. 静默通过清单（本轴的核心产出）

共 **11/38** 行「一路绿灯但存在缺口」：

| # | 缺口是什么 | 分型 | 为什么算「静默」 |
|-|-|-|-|
| **F5** | 嵌套声明：类型位置写成对象 | `illegal_shape_tolerated` | 契约形态不在登记的四形态内（或含非法类型名），被**降级成默认值**而不是报错 |
| **F6** | 形态①混入非字符串/嵌套项 | `illegal_shape_tolerated` | 契约形态不在登记的四形态内（或含非法类型名），被**降级成默认值**而不是报错 |
| **B4** | 数值声明 {"n": 0} | `illegal_shape_tolerated` | 契约形态不在登记的四形态内（或含非法类型名），被**降级成默认值**而不是报错 |
| **B5** | 布尔声明 {"b": true} | `illegal_shape_tolerated` | 契约形态不在登记的四形态内（或含非法类型名），被**降级成默认值**而不是报错 |
| **B6** | 非法类型名（数组当类型）{"x":["array"]} | `illegal_shape_tolerated` | 契约形态不在登记的四形态内（或含非法类型名），被**降级成默认值**而不是报错 |
| **B8** | 列表混入 null | `illegal_shape_tolerated` | 契约形态不在登记的四形态内（或含非法类型名），被**降级成默认值**而不是报错 |
| **D5** | output_contract = true（布尔） | `illegal_shape_applied_true` | 契约形态完全非法，但 `output_contract_applied` 仍被写成 **true** |
| **D6** | output_contract = "case_id"（字符串） | `illegal_shape_applied_true` | 契约形态完全非法，但 `output_contract_applied` 仍被写成 **true** |
| **D8** | {"fields": "case_id"}（fields 是字符串） | `illegal_shape_applied_true` | 契约形态完全非法，但 `output_contract_applied` 仍被写成 **true** |
| **D11** | 深嵌套 {"fields":{"a":{"b":{"c":"array"}}}} | `illegal_shape_tolerated` | 契约形态不在登记的四形态内（或含非法类型名），被**降级成默认值**而不是报错 |
| **D12** | output_contract = 3.14（浮点） | `illegal_shape_applied_true` | 契约形态完全非法，但 `output_contract_applied` 仍被写成 **true** |

### 7.1 最需要点名的一条：`output_contract_applied` 不能当契约完整性用

实测有 **7** 行出现 `output_contract_applied = true` 但**一个声明字段都没回显**：
`B1`, `D5`, `D6`, `D8`, `D9`, `D10`, `D12`

也就是说：回放 Agent 若只看这一个布尔值就认为「契约已满足」，会被这几行骗过去。
正确做法是**同时**看 `check_contract.py` 的 `contract_missing` 与 `figcheck` 的 G2 ——
本包把这两条命令写进 SKILL.md 的验收步骤，正是为此。

## 8. 被校验器抓住的 5 行（反向证据：门是有效的）

| # | 注入 | main exit | status | G2 | check_contract exit | 缺失字段 |
|-|-|-|-|-|-|-|
| **B1** | 字段名 = 空串 | 2 | partial | False | 1 | `` |
| **A2** | 声明内部瞬态键 warnings_collected | 2 | partial | False | 1 | `warnings_collected` |
| **A3** | 声明内部瞬态键 _pipeline | 2 | partial | False | 1 | `_pipeline` |
| **A4** | 声明内部瞬态键 manifest_figures | 2 | partial | False | 1 | `manifest_figures` |
| **A5** | 声明内部瞬态键 adjustments_collected | 2 | partial | False | 1 | `adjustments_collected` |

两条重要结论：

1. **A2–A5 证明第 3 件事（契约落地之后 pop 内部键）确实会打穿契约**：
   声明 `warnings_collected` / `_pipeline` / `manifest_figures` / `adjustments_collected` 时，
   字段会从最终 `result.json` 里消失；**但 G2 与 check_contract 都抓住了** ——
   status 被降级为 `partial`、main 退出码 2。这是「门有效」的直接证据，不是缺陷被掩盖。
2. **B1（字段名 = 空串）暴露了 main.py 与校验器的口径分歧**：`apply_output_contract()` 里
   `if not f: continue` 会跳过空字段名，而 `figcheck._contract_fields()` 与
   `check_contract.contract_fields()` **不过滤空串**。同一份契约，main 认为「没什么要写的」，
   校验器认为「你少写了一个字段」⇒ 判 partial / exit 2 / exit 1。
   本台子把它单列为 `parser_disagreement`，实测只有这一行命中。

## 9. 未覆盖声明（不假装覆盖面很大）

- 真实平台案例的 output_contract 具体字段（未知，本台子用自造字段 + 别名集合覆盖）
- 契约字段**取值语义**是否正确（本台子只判存在性/容器类型/是否 null，不判数值科学含义）
- 契约声明的嵌套结构深度 > 2 的语义（本台子只测到 D11 的两层）
- 跨平台换行/编码（CRLF vs LF）对契约回显的影响
- 并发/重入场景下 apply_output_contract 的行为

## 10. 结论

- 共 38 行：{'echo_complete': 14, 'silent_pass': 11, 'caught': 5, 'no_contract': 8}
- 静默通过（一路绿灯但存在缺口）：F5, F6, B4, B5, B6, B8, D5, D6, D8, D11, D12
- 静默通过的分型：{"F5": "illegal_shape_tolerated", "F6": "illegal_shape_tolerated", "B4": "illegal_shape_tolerated", "B5": "illegal_shape_tolerated", "B6": "illegal_shape_tolerated", "B8": "illegal_shape_tolerated", "D5": "illegal_shape_applied_true", "D6": "illegal_shape_applied_true", "D8": "illegal_shape_applied_true", "D11": "illegal_shape_tolerated", "D12": "illegal_shape_applied_true"}
- ★ `output_contract_applied=true` 但一个声明字段都没回显的行（该标志不可当契约完整性用）：B1, D5, D6, D8, D9, D10, D12
- 契约形态非法却未触发任何红黄灯的行：F5, F6, B4, B5, B6, B8, D5, D6, D8, D11, D12
- main.py 与校验器对声明字段口径不一致的行：B1
- 声明字段在最终 result.json 里消失的行：B1, A2, A3, A4, A5
- 声明容器类型与实际值类型不符的行：无

一句话：**四形态与常见别名回显是正确的（14 行 `echo_complete`，其中 A1 一次回显 22 个字段）；
真正需要披露的是 11 行「一路绿灯但有缺口」，以及 7 行
`output_contract_applied=true` 却零回显 —— 后者会让只看布尔值的回放流程误判契约已满足。**

## 11. 未解决项

1. 这些「静默降级」本轮**只登记、不改脚本**（改 `apply_output_contract` 属于行为变更，
   会动到既有脚本语义）；要收敛，应在 main.py 里对非法形态追加一条 uncertainty 记录。
2. B1 的口径分歧未统一（涉及两个脚本的解析函数）。
3. §9 里列的未覆盖项都还没做。
