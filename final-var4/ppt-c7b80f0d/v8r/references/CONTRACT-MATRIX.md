# CONTRACT-MATRIX.md — 契约四形态 × 边界值矩阵（**逐行实测**）

> 本文件由 `scripts/contract_matrix.py --emit-md` 从**真实运行**生成，不是手写表格。
> 每个单元 = 一份完整 `case.json`（只替换 `output_contract`）+ 一次**未经修改的**端到端运行（`scripts/main.py`）。
> 原始逐单元记录见 `references/contract-matrix-data.json`；修复前的对照记录见 `references/contract-matrix-before-fix.json`。

## 0. 运行命令与判据

```bash
python "$SKILL_DIR/scripts/contract_matrix.py" --out <探针目录> \
  --emit-md "$SKILL_DIR/references/CONTRACT-MATRIX.md"
```

| 退出码 | 含义 |
|-|-|
| 0 | 每个单元都写出 `result.json`，且**没有静默通过** |
| 1 | 存在静默通过（既没纠正、也没记录的契约违约） |
| 2 | 参数/输入错误 |
| 3 | 有单元让主流程崩溃（非零退出或无 `result.json`） |

每行的判据来自 `references/OUTPUT_CONTRACT.md` §2（四形态回显规则，禁止 null）与 §5（G2）；`期望` 列即按该规则推出的值。

## 1. 汇总（实测 28 个单元）

| 指标 | 实测 |
|-|-|
| exit 0 的单元 | 23 |
| 写出 result.json 的单元 | 28 |
| 内部自检 OK 的单元 | 23 |
| 契约回显符合期望（match） | 28 |
| 回显不符但**被记录/被门拦住**（mismatch-recorded） | 0 |
| 自检点名问题的单元（caught by gate） | 5 |
| 顶层契约面不完整的单元 | 5 |
| 崩溃（无 result.json） | 0 |
| **静默通过** | 0 |

## 2. 逐行实测

| 单元 | 形态 | 边界值 | 注入内容（截断） | exit | 写出 result | status | 自检 | 契约面完整 | 契约回显 | 判定 |  静默通过 |
|-|-|-|-|-|-|-|-|-|-|-|-|
| A01 | ① 字段→类型提示 | 普通字符串提示 | `{"cell_title_hint": "字符串"}` | 0 | 是 | completed | OK | 是 | `{"title": "deck 标题（一行的字符串）", "main_claim": "全文一句话结论（字符串）", "slides": [` | match | 否 |
| A02 | ① 字段→类型提示 | 列表提示 | `{"cell_list_hint": ["每页 {page,title,claim}（列表）"]}` | 0 | 是 | completed | OK | 是 | `{"title": "deck 标题（一行的字符串）", "main_claim": "全文一句话结论（字符串）", "slides": [` | match | 否 |
| A03 | ① 字段→类型提示 | 对象（嵌套）提示 | `{"cell_obj_hint": {"a": "b"}}` | 0 | 是 | completed | OK | 是 | `{"title": "deck 标题（一行的字符串）", "main_claim": "全文一句话结论（字符串）", "slides": [` | match | 否 |
| A04 | ① 字段→类型提示 | **数值 0** | `{"cell_num_hint": 0}` | 0 | 是 | completed | OK | 是 | `{"title": "deck 标题（一行的字符串）", "main_claim": "全文一句话结论（字符串）", "slides": [` | match | 否 |
| A05 | ① 字段→类型提示 | 空串 | `{"cell_empty_str": ""}` | 0 | 是 | completed | OK | 是 | `{"title": "deck 标题（一行的字符串）", "main_claim": "全文一句话结论（字符串）", "slides": [` | match | 否 |
| A06 | ① 字段→类型提示 | 空数组 | `{"cell_empty_list": []}` | 0 | 是 | completed | OK | 是 | `{"title": "deck 标题（一行的字符串）", "main_claim": "全文一句话结论（字符串）", "slides": [` | match | 否 |
| A07 | ① 字段→类型提示 | **非法类型 null** | `{"cell_null": null}` | 0 | 是 | completed | OK | 是 | `{"title": "deck 标题（一行的字符串）", "main_claim": "全文一句话结论（字符串）", "slides": [` | match | 否 |
| A08 | ① 字段→类型提示 | 超长字符串（8000 字） | `{"cell_long": "长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长` | 0 | 是 | completed | OK | 是 | `{"title": "deck 标题（一行的字符串）", "main_claim": "全文一句话结论（字符串）", "slides": [` | match | 否 |
| A09 | ① 字段→类型提示 | 与真实键同名（status/deck） | `{"status": "字符串", "deck": "字符串"}` | 0 | 是 | completed | OK | 是 | `{"title": "deck 标题（一行的字符串）", "main_claim": "全文一句话结论（字符串）", "slides": [` | match | 否 |
| A10 | ① 字段→类型提示 | 语义字段（title/main_claim/slides/render_state） | `{"title": "字符串", "main_claim": "字符串", "slides": ["每页 {page,t` | 0 | 是 | completed | OK | 是 | `{"title": "字符串", "main_claim": "字符串", "slides": ["每页 {page,title,claim` | match | 否 |
| A11 | ① 字段→类型提示 | 布尔 true（未知字段名） | `{"cell_bool_true": true}` | 0 | 是 | completed | OK | 是 | `{"title": "deck 标题（一行的字符串）", "main_claim": "全文一句话结论（字符串）", "slides": [` | match | 否 |
| A12 | ① 字段→类型提示 | 布尔 false（未知字段名） | `{"cell_bool_false": false}` | 0 | 是 | completed | OK | 是 | `{"title": "deck 标题（一行的字符串）", "main_claim": "全文一句话结论（字符串）", "slides": [` | match | 否 |
| A13 | ① 字段→类型提示 | 布尔 true（语义字段 notes_separated） | `{"notes_separated": true}` | 0 | 是 | completed | OK | 是 | `{"title": "deck 标题（一行的字符串）", "main_claim": "全文一句话结论（字符串）", "slides": [` | match | 否 |
| A14 | ① 字段→类型提示 | 布尔 false（语义字段 notes_separated） | `{"notes_separated": false}` | 0 | 是 | completed | OK | 是 | `{"title": "deck 标题（一行的字符串）", "main_claim": "全文一句话结论（字符串）", "slides": [` | match | 否 |
| B01 | ② 字段→说明 | 普通说明文本 | `{"cell_desc": "渲染与版本记录（字符串或对象）"}` | 0 | 是 | completed | OK | 是 | `{"title": "deck 标题（一行的字符串）", "main_claim": "全文一句话结论（字符串）", "slides": [` | match | 否 |
| B02 | ② 字段→说明 | 非法类型（说明位写了数字） | `{"cell_desc_num": 123}` | 0 | 是 | completed | OK | 是 | `{"title": "deck 标题（一行的字符串）", "main_claim": "全文一句话结论（字符串）", "slides": [` | match | 否 |
| C01 | ③ 布尔开关 | 仅布尔字段 | `{"notes_separated": true}` | 0 | 是 | completed | OK | 是 | `{"title": "deck 标题（一行的字符串）", "main_claim": "全文一句话结论（字符串）", "slides": [` | match | 否 |
| D01 | ④ 字段清单 | 两个名称 | `["title", "main_claim", "slides", "render_state", "notes_sep` | 0 | 是 | completed | OK | 是 | `["title", "main_claim", "slides", "render_state", "notes_separated", "` | match | 否 |
| D02 | ④ 字段清单 | 空清单（只列语义字段） | `["title", "main_claim", "slides", "render_state", "notes_sep` | 0 | 是 | completed | OK | 是 | `["title", "main_claim", "slides", "render_state", "notes_separated"]` | match | 否 |
| D03 | ④ 字段清单 | **非法元素（数字/null 混入）** | `["title", "main_claim", "slides", "render_state", "notes_sep` | 0 | 是 | completed | OK | 是 | `["title", "main_claim", "slides", "render_state", "notes_separated", "` | match | 否 |
| D04 | ④ 字段清单 | 与真实键同名 | `["title", "main_claim", "slides", "render_state", "notes_sep` | 0 | 是 | completed | OK | 是 | `["title", "main_claim", "slides", "render_state", "notes_separated", "` | match | 否 |
| D05 | ④ 字段清单 | 重复名称 | `["title", "main_claim", "slides", "render_state", "notes_sep` | 0 | 是 | completed | OK | 是 | `["title", "main_claim", "slides", "render_state", "notes_separated", "` | match | 否 |
| D06 | ④ 字段清单 | 超长清单（200 个名称） | `["title", "main_claim", "slides", "render_state", "notes_sep` | 0 | 是 | completed | OK | 是 | `["title", "main_claim", "slides", "render_state", "notes_separated", "` | match | 否 |
| E01 | 契约容器 | **缺字段（无 output_contract 键）** | `null` | 1 | 是 | completed | ['output contract fields missing: title, mai | **否** | `{}` | match | 否 |
| E02 | 契约容器 | **非法容器（字符串）** | `"这是一段说明"` | 1 | 是 | completed | ['output contract fields missing: title, mai | **否** | `{}` | match | 否 |
| E03 | 契约容器 | 非法容器（null） | `null` | 1 | 是 | completed | ['output contract fields missing: title, mai | **否** | `{}` | match | 否 |
| E04 | 契约容器 | 空容器（{}） | `{}` | 1 | 是 | completed | ['output contract fields missing: title, mai | **否** | `{}` | match | 否 |
| E05 | 契约容器 | **声明不全（只声明 1 个未知字段）** | `{"cell_only_one": "字符串"}` | 1 | 是 | completed | ['output contract fields missing: title, mai | **否** | `{"cell_only_one": "字符串"}` | match | 否 |

## 3. 静默通过清单

**本版实测：0 条静默通过。**

修复前（对照记录 `contract-matrix-before-fix.json`）为 5 条，逐条如下：

- `A04`（① 字段→类型提示 / **数值 0**）：cell_num_hint 期望 number=0，实测 str=''
- `A11`（① 字段→类型提示 / 布尔 true（未知字段名））：cell_bool_true 期望 bool=True，实测 bool=False
- `A12`（① 字段→类型提示 / 布尔 false（未知字段名））：cell_bool_false 期望 bool=False，实测 str=''
- `B02`（② 字段→说明 / 非法类型（说明位写了数字））：cell_desc_num 期望 number=123，实测 str=''
- `D03`（④ 字段清单 / **非法元素（数字/null 混入）**）：清单中的非法元素（7/None）被静默丢弃

## 4. 单元级细节（逐 declared 字段）

### A01 · ① 字段→类型提示 · 普通字符串提示

- 注入：`{"cell_title_hint": "字符串"}`
- exit=`0`，写出 result.json=True，status=completed，顶层键数=20，result 字节=6181
- 契约回显：`{"title": "deck 标题（一行的字符串）", "main_claim": "全文一句话结论（字符串）", "slides": ["每页 {page,title,claim}（列表）"], "evidence_mapping": "页级证据映射描述（字符串或对象）", "render_state": "渲染与`
- 声明字段回显：cell_title_hint=str(非null)
- 不确定性条数=1（未提及任何声明字段）
- 顶层契约面：完整（19/19）
- 判定：**match**（与期望一致）

### A02 · ① 字段→类型提示 · 列表提示

- 注入：`{"cell_list_hint": ["每页 {page,title,claim}（列表）"]}`
- exit=`0`，写出 result.json=True，status=completed，顶层键数=20，result 字节=6221
- 契约回显：`{"title": "deck 标题（一行的字符串）", "main_claim": "全文一句话结论（字符串）", "slides": ["每页 {page,title,claim}（列表）"], "evidence_mapping": "页级证据映射描述（字符串或对象）", "render_state": "渲染与`
- 声明字段回显：cell_list_hint=list(非null)
- 不确定性条数=1（未提及任何声明字段）
- 顶层契约面：完整（19/19）
- 判定：**match**（与期望一致）

### A03 · ① 字段→类型提示 · 对象（嵌套）提示

- 注入：`{"cell_obj_hint": {"a": "b"}}`
- exit=`0`，写出 result.json=True，status=completed，顶层键数=20，result 字节=6188
- 契约回显：`{"title": "deck 标题（一行的字符串）", "main_claim": "全文一句话结论（字符串）", "slides": ["每页 {page,title,claim}（列表）"], "evidence_mapping": "页级证据映射描述（字符串或对象）", "render_state": "渲染与`
- 声明字段回显：cell_obj_hint=obj(非null)
- 不确定性条数=1（未提及任何声明字段）
- 顶层契约面：完整（19/19）
- 判定：**match**（与期望一致）

### A04 · ① 字段→类型提示 · **数值 0**

- 注入：`{"cell_num_hint": 0}`
- exit=`0`，写出 result.json=True，status=completed，顶层键数=20，result 字节=6166
- 契约回显：`{"title": "deck 标题（一行的字符串）", "main_claim": "全文一句话结论（字符串）", "slides": ["每页 {page,title,claim}（列表）"], "evidence_mapping": "页级证据映射描述（字符串或对象）", "render_state": "渲染与`
- 声明字段回显：cell_num_hint=number(非null)
- 不确定性条数=1（未提及任何声明字段）
- 顶层契约面：完整（19/19）
- 判定：**match**（与期望一致）

### A05 · ① 字段→类型提示 · 空串

- 注入：`{"cell_empty_str": ""}`
- exit=`0`，写出 result.json=True，status=completed，顶层键数=20，result 字节=6170
- 契约回显：`{"title": "deck 标题（一行的字符串）", "main_claim": "全文一句话结论（字符串）", "slides": ["每页 {page,title,claim}（列表）"], "evidence_mapping": "页级证据映射描述（字符串或对象）", "render_state": "渲染与`
- 声明字段回显：cell_empty_str=str(非null)
- 不确定性条数=1（未提及任何声明字段）
- 顶层契约面：完整（19/19）
- 判定：**match**（与期望一致）

### A06 · ① 字段→类型提示 · 空数组

- 注入：`{"cell_empty_list": []}`
- exit=`0`，写出 result.json=True，status=completed，顶层键数=20，result 字节=6172
- 契约回显：`{"title": "deck 标题（一行的字符串）", "main_claim": "全文一句话结论（字符串）", "slides": ["每页 {page,title,claim}（列表）"], "evidence_mapping": "页级证据映射描述（字符串或对象）", "render_state": "渲染与`
- 声明字段回显：cell_empty_list=list(非null)
- 不确定性条数=1（未提及任何声明字段）
- 顶层契约面：完整（19/19）
- 判定：**match**（与期望一致）

### A07 · ① 字段→类型提示 · **非法类型 null**

- 注入：`{"cell_null": null}`
- exit=`0`，写出 result.json=True，status=completed，顶层键数=20，result 字节=6162
- 契约回显：`{"title": "deck 标题（一行的字符串）", "main_claim": "全文一句话结论（字符串）", "slides": ["每页 {page,title,claim}（列表）"], "evidence_mapping": "页级证据映射描述（字符串或对象）", "render_state": "渲染与`
- 声明字段回显：cell_null=str(非null)
- 不确定性条数=1（未提及任何声明字段）
- 顶层契约面：完整（19/19）
- 判定：**match**（与期望一致）

### A08 · ① 字段→类型提示 · 超长字符串（8000 字）

- 注入：`{"cell_long": "长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长长`
- exit=`0`，写出 result.json=True，status=completed，顶层键数=20，result 字节=30160
- 契约回显：`{"title": "deck 标题（一行的字符串）", "main_claim": "全文一句话结论（字符串）", "slides": ["每页 {page,title,claim}（列表）"], "evidence_mapping": "页级证据映射描述（字符串或对象）", "render_state": "渲染与`
- 声明字段回显：cell_long=str(非null)
- 不确定性条数=1（未提及任何声明字段）
- 顶层契约面：完整（19/19）
- 判定：**match**（与期望一致）

### A09 · ① 字段→类型提示 · 与真实键同名（status/deck）

- 注入：`{"status": "字符串", "deck": "字符串"}`
- exit=`0`，写出 result.json=True，status=completed，顶层键数=19，result 字节=6172
- 契约回显：`{"title": "deck 标题（一行的字符串）", "main_claim": "全文一句话结论（字符串）", "slides": ["每页 {page,title,claim}（列表）"], "evidence_mapping": "页级证据映射描述（字符串或对象）", "render_state": "渲染与`
- 声明字段回显：status=str(非null); deck=obj(非null)
- 不确定性条数=1
- 顶层契约面：完整（19/19）
- 判定：**match**（与期望一致）

### A10 · ① 字段→类型提示 · 语义字段（title/main_claim/slides/render_state）

- 注入：`{"title": "字符串", "main_claim": "字符串", "slides": ["每页 {page,title,claim}（列表）"], "render_state": "说明"}`
- exit=`0`，写出 result.json=True，status=completed，顶层键数=19，result 字节=6028
- 契约回显：`{"title": "字符串", "main_claim": "字符串", "slides": ["每页 {page,title,claim}（列表）"], "evidence_mapping": "页级证据映射描述（字符串或对象）", "render_state": "说明", "notes_separated": `
- 声明字段回显：title=str(非null); main_claim=str(非null); slides=list(非null); render_state=obj(非null)
- 不确定性条数=1（未提及任何声明字段）
- 顶层契约面：完整（19/19）
- 判定：**match**（与期望一致）

### A11 · ① 字段→类型提示 · 布尔 true（未知字段名）

- 注入：`{"cell_bool_true": true}`
- exit=`0`，写出 result.json=True，status=completed，顶层键数=20，result 字节=6174
- 契约回显：`{"title": "deck 标题（一行的字符串）", "main_claim": "全文一句话结论（字符串）", "slides": ["每页 {page,title,claim}（列表）"], "evidence_mapping": "页级证据映射描述（字符串或对象）", "render_state": "渲染与`
- 声明字段回显：cell_bool_true=bool(非null)
- 不确定性条数=1（未提及任何声明字段）
- 顶层契约面：完整（19/19）
- 判定：**match**（与期望一致）

### A12 · ① 字段→类型提示 · 布尔 false（未知字段名）

- 注入：`{"cell_bool_false": false}`
- exit=`0`，写出 result.json=True，status=completed，顶层键数=20，result 字节=6178
- 契约回显：`{"title": "deck 标题（一行的字符串）", "main_claim": "全文一句话结论（字符串）", "slides": ["每页 {page,title,claim}（列表）"], "evidence_mapping": "页级证据映射描述（字符串或对象）", "render_state": "渲染与`
- 声明字段回显：cell_bool_false=bool(非null)
- 不确定性条数=1（未提及任何声明字段）
- 顶层契约面：完整（19/19）
- 判定：**match**（与期望一致）

### A13 · ① 字段→类型提示 · 布尔 true（语义字段 notes_separated）

- 注入：`{"notes_separated": true}`
- exit=`0`，写出 result.json=True，status=completed，顶层键数=19，result 字节=6120
- 契约回显：`{"title": "deck 标题（一行的字符串）", "main_claim": "全文一句话结论（字符串）", "slides": ["每页 {page,title,claim}（列表）"], "evidence_mapping": "页级证据映射描述（字符串或对象）", "render_state": "渲染与`
- 声明字段回显：notes_separated=bool(非null)
- 不确定性条数=1（未提及任何声明字段）
- 顶层契约面：完整（19/19）
- 判定：**match**（与期望一致）

### A14 · ① 字段→类型提示 · 布尔 false（语义字段 notes_separated）

- 注入：`{"notes_separated": false}`
- exit=`0`，写出 result.json=True，status=completed，顶层键数=19，result 字节=6121
- 契约回显：`{"title": "deck 标题（一行的字符串）", "main_claim": "全文一句话结论（字符串）", "slides": ["每页 {page,title,claim}（列表）"], "evidence_mapping": "页级证据映射描述（字符串或对象）", "render_state": "渲染与`
- 声明字段回显：notes_separated=bool(非null)
- 不确定性条数=1（未提及任何声明字段）
- 顶层契约面：完整（19/19）
- 判定：**match**（与期望一致）

### B01 · ② 字段→说明 · 普通说明文本

- 注入：`{"cell_desc": "渲染与版本记录（字符串或对象）"}`
- exit=`0`，写出 result.json=True，status=completed，顶层键数=20，result 字节=6205
- 契约回显：`{"title": "deck 标题（一行的字符串）", "main_claim": "全文一句话结论（字符串）", "slides": ["每页 {page,title,claim}（列表）"], "evidence_mapping": "页级证据映射描述（字符串或对象）", "render_state": "渲染与`
- 声明字段回显：cell_desc=str(非null)
- 不确定性条数=1（未提及任何声明字段）
- 顶层契约面：完整（19/19）
- 判定：**match**（与期望一致）

### B02 · ② 字段→说明 · 非法类型（说明位写了数字）

- 注入：`{"cell_desc_num": 123}`
- exit=`0`，写出 result.json=True，status=completed，顶层键数=20，result 字节=6170
- 契约回显：`{"title": "deck 标题（一行的字符串）", "main_claim": "全文一句话结论（字符串）", "slides": ["每页 {page,title,claim}（列表）"], "evidence_mapping": "页级证据映射描述（字符串或对象）", "render_state": "渲染与`
- 声明字段回显：cell_desc_num=number(非null)
- 不确定性条数=1（未提及任何声明字段）
- 顶层契约面：完整（19/19）
- 判定：**match**（与期望一致）

### C01 · ③ 布尔开关 · 仅布尔字段

- 注入：`{"notes_separated": true}`
- exit=`0`，写出 result.json=True，status=completed，顶层键数=19，result 字节=6120
- 契约回显：`{"title": "deck 标题（一行的字符串）", "main_claim": "全文一句话结论（字符串）", "slides": ["每页 {page,title,claim}（列表）"], "evidence_mapping": "页级证据映射描述（字符串或对象）", "render_state": "渲染与`
- 声明字段回显：notes_separated=bool(非null)
- 不确定性条数=1（未提及任何声明字段）
- 顶层契约面：完整（19/19）
- 判定：**match**（与期望一致）

### D01 · ④ 字段清单 · 两个名称

- 注入：`["title", "main_claim", "slides", "render_state", "notes_separated", "cell_a", "cell_b"]`
- exit=`0`，写出 result.json=True，status=completed，顶层键数=21，result 字节=4598
- 契约回显：`["title", "main_claim", "slides", "render_state", "notes_separated", "cell_a", "cell_b"]`
- 声明字段回显：title=list(非null); main_claim=list(非null); slides=list(非null); render_state=list(非null); notes_separated=list(非null); cell_a=list(非null) …(+1)
- 不确定性条数=1（未提及任何声明字段）
- 顶层契约面：完整（19/19）
- ④ 清单形态下语义字段的实际回显类型：`{"title": "list", "main_claim": "list", "slides": "list", "render_state": "list", "notes_separated": "list"}`
- 判定：**match**（与期望一致）

### D02 · ④ 字段清单 · 空清单（只列语义字段）

- 注入：`["title", "main_claim", "slides", "render_state", "notes_separated"]`
- exit=`0`，写出 result.json=True，status=completed，顶层键数=19，result 字节=4538
- 契约回显：`["title", "main_claim", "slides", "render_state", "notes_separated"]`
- 声明字段回显：title=list(非null); main_claim=list(非null); slides=list(非null); render_state=list(非null); notes_separated=list(非null)
- 不确定性条数=1（未提及任何声明字段）
- 顶层契约面：完整（19/19）
- ④ 清单形态下语义字段的实际回显类型：`{"title": "list", "main_claim": "list", "slides": "list", "render_state": "list", "notes_separated": "list"}`
- 判定：**match**（与期望一致）

### D03 · ④ 字段清单 · **非法元素（数字/null 混入）**

- 注入：`["title", "main_claim", "slides", "render_state", "notes_separated", "cell_c", 7, null]`
- exit=`0`，写出 result.json=True，status=completed，顶层键数=20，result 字节=4694
- 契约回显：`["title", "main_claim", "slides", "render_state", "notes_separated", "cell_c", 7, null]`
- 声明字段回显：title=list(非null); main_claim=list(非null); slides=list(非null); render_state=list(非null); notes_separated=list(非null); cell_c=list(非null)
- 不确定性条数=2（未提及任何声明字段）
  - 已记录：`output_contract name list contains 2 non-string entries (7, None) — skipped instead of being echoed`
- 顶层契约面：完整（19/19）
- ④ 清单形态下语义字段的实际回显类型：`{"title": "list", "main_claim": "list", "slides": "list", "render_state": "list", "notes_separated": "list"}`
- 判定：**match**（与期望一致）

### D04 · ④ 字段清单 · 与真实键同名

- 注入：`["title", "main_claim", "slides", "render_state", "notes_separated", "status", "case_id"]`
- exit=`0`，写出 result.json=True，status=completed，顶层键数=19，result 字节=4567
- 契约回显：`["title", "main_claim", "slides", "render_state", "notes_separated", "status", "case_id"]`
- 声明字段回显：title=list(非null); main_claim=list(非null); slides=list(非null); render_state=list(非null); notes_separated=list(非null); status=str(非null) …(+1)
- 不确定性条数=1（未提及任何声明字段）
- 顶层契约面：完整（19/19）
- ④ 清单形态下语义字段的实际回显类型：`{"title": "list", "main_claim": "list", "slides": "list", "render_state": "list", "notes_separated": "list"}`
- 判定：**match**（与期望一致）

### D05 · ④ 字段清单 · 重复名称

- 注入：`["title", "main_claim", "slides", "render_state", "notes_separated", "dup_name", "dup_name"]`
- exit=`0`，写出 result.json=True，status=completed，顶层键数=20，result 字节=4588
- 契约回显：`["title", "main_claim", "slides", "render_state", "notes_separated", "dup_name", "dup_name"]`
- 声明字段回显：title=list(非null); main_claim=list(非null); slides=list(非null); render_state=list(非null); notes_separated=list(非null); dup_name=list(非null) …(+1)
- 不确定性条数=1（未提及任何声明字段）
- 顶层契约面：完整（19/19）
- ④ 清单形态下语义字段的实际回显类型：`{"title": "list", "main_claim": "list", "slides": "list", "render_state": "list", "notes_separated": "list"}`
- 判定：**match**（与期望一致）

### D06 · ④ 字段清单 · 超长清单（200 个名称）

- 注入：`["title", "main_claim", "slides", "render_state", "notes_separated", "cell_bulk_000", "cell_bulk_001", "cell_bulk_002", "cell_bulk_003", "cell_bulk_004", "cell_bulk_005", "cell_bulk_006", "cell_bulk_0`
- exit=`0`，写出 result.json=True，status=completed，顶层键数=219，result 字节=13338
- 契约回显：`["title", "main_claim", "slides", "render_state", "notes_separated", "cell_bulk_000", "cell_bulk_001", "cell_bulk_002", "cell_bulk_003", "cell_bulk_004", "cell_`
- 声明字段回显：title=list(非null); main_claim=list(非null); slides=list(非null); render_state=list(非null); notes_separated=list(非null); cell_bulk_000=list(非null) …(+199)
- 不确定性条数=1（未提及任何声明字段）
- 顶层契约面：完整（19/19）
- ④ 清单形态下语义字段的实际回显类型：`{"title": "list", "main_claim": "list", "slides": "list", "render_state": "list", "notes_separated": "list"}`
- 判定：**match**（与期望一致）

### E01 · 契约容器 · **缺字段（无 output_contract 键）**

- 注入：`null`
- exit=`1`，写出 result.json=True，status=completed，顶层键数=14，result 字节=4458
- 契约回显：`{}`
- 不确定性条数=1（未提及任何声明字段）
- 顶层契约面：**不完整** —— 缺 ['title', 'main_claim', 'slides', 'render_state', 'notes_separated']，null []；自检问题：output contract fields missing: title, main_claim, slides, render_state, notes_separated
- 判定：**match**（与期望一致）

### E02 · 契约容器 · **非法容器（字符串）**

- 注入：`"这是一段说明"`
- exit=`1`，写出 result.json=True，status=completed，顶层键数=14，result 字节=4610
- 契约回显：`{}`
- 不确定性条数=2（未提及任何声明字段）
  - 已记录：`output_contract declared as str — not a field mapping (dict) or name list (list); echoed as an empty object and no declared field was honoured`
- 顶层契约面：**不完整** —— 缺 ['title', 'main_claim', 'slides', 'render_state', 'notes_separated']，null []；自检问题：output contract fields missing: title, main_claim, slides, render_state, notes_separated
- 判定：**match**（与期望一致）

### E03 · 契约容器 · 非法容器（null）

- 注入：`null`
- exit=`1`，写出 result.json=True，status=completed，顶层键数=14，result 字节=4611
- 契约回显：`{}`
- 不确定性条数=2（未提及任何声明字段）
  - 已记录：`output_contract declared as null — not a field mapping (dict) or name list (list); echoed as an empty object and no declared field was honoured`
- 顶层契约面：**不完整** —— 缺 ['title', 'main_claim', 'slides', 'render_state', 'notes_separated']，null []；自检问题：output contract fields missing: title, main_claim, slides, render_state, notes_separated
- 判定：**match**（与期望一致）

### E04 · 契约容器 · 空容器（{}）

- 注入：`{}`
- exit=`1`，写出 result.json=True，status=completed，顶层键数=14，result 字节=4458
- 契约回显：`{}`
- 不确定性条数=1（未提及任何声明字段）
- 顶层契约面：**不完整** —— 缺 ['title', 'main_claim', 'slides', 'render_state', 'notes_separated']，null []；自检问题：output contract fields missing: title, main_claim, slides, render_state, notes_separated
- 判定：**match**（与期望一致）

### E05 · 契约容器 · **声明不全（只声明 1 个未知字段）**

- 注入：`{"cell_only_one": "字符串"}`
- exit=`1`，写出 result.json=True，status=completed，顶层键数=15，result 字节=4517
- 契约回显：`{"cell_only_one": "字符串"}`
- 声明字段回显：cell_only_one=str(非null)
- 不确定性条数=1（未提及任何声明字段）
- 顶层契约面：**不完整** —— 缺 ['title', 'main_claim', 'slides', 'render_state', 'notes_separated']，null []；自检问题：output contract fields missing: title, main_claim, slides, render_state, notes_separated
- 判定：**match**（与期望一致）

## 5. 本版据此做的纯增量修复（逐条点名）

脚本改动**只发生在** `scripts/main.py` 的 `apply_output_contract()` 内，CLI 参数名/默认值/退出码语义未改；既有脚本其余部分逐字节不变。

| # | 位置 | 改动 | 依据（实测单元） | 风险控制 |
|-|-|-|-|-|
| F1 | `scripts/main.py: apply_output_contract()` | 未知字段名 + 布尔声明：由 `v is True -> semantic.get(k, False)` 改为 `isinstance(v, bool) -> 如实回显声明值` | 实测 A11 声明 true 却回显 false、A12 声明 false 却回显 ""，两者都不忠实 | 语义字段（notes_separated 等）仍优先取本次运行真实值：A13/A14 行为不变 |
| F2 | `scripts/main.py: apply_output_contract()` | 新增数值型声明的忠实回显分支（int/float，且明确排除 bool） | 实测 A04 声明 0 回显 ""、B02 声明 123 回显 ""，类型不符 | 只在“声明值本身是数字”时生效；str/list/dict/None 分支逻辑未改 |
| F3 | `scripts/main.py: apply_output_contract()` | ④ 清单形态中的非法元素与非法容器不再静默：写入 result['uncertainty'] | 实测 D03 的数字/null 元素、E02/E03 的非法容器此前完全无痕（静默通过） | 只在输入确实非法时追加一条 uncertainty，正常案例不触发 |

## 6. 未覆盖声明（如实列出）

- **只覆盖 `output_contract` 一个契约面**：题面要求的页级结构、模板、字体、页数上限等约束不在本矩阵内（它们由 `spec_lint` / `export_check` 覆盖）。
- **只测回显与门的状态，不测“语义是否合理”**：例如声明 200 个字段会全部回显，但“该不该声明这么多”不是矩阵能判的。
- **平台 3 个正式案例未在本地跑**：本矩阵用自带示例案例作基座（`examples/case.json`），正式案例的 `output_contract` 声明形态可能超出这 4 种（若出现，按同样方式加一行单元即可复测）。
- **未覆盖并发/中断**：单元按顺序单进程执行，不测运行期被中断时的契约回显。
- **未覆盖 `--demo` 分支与材料不可读分支的契约回显差异**（那两条分支由 `references/failure-modes.md` 的状态一致性条目覆盖）。
- **未做多次重复**：每个单元运行一次；重复运行的字节稳定性由本包另一条轴（`scripts/determinism.py`，见 v7 版说明）负责，两者互补。
