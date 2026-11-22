# DECISION-RULES.md — 三套编号的决策规则 union（D / H / M）+ 状态不变量

本包是 union 包：`v1` 把执行路径写成 **D01–D16**、`v2` 把异常处置写成 **H01–H14**、
`v3` 把回退链写成 **M01–M14**。三者**不是三套不同的规则**，而是同一批判断的三种切法：

| 切法 | 出处 | 组织方式 | 最适合什么时候读 |
|-|-|-|-|
| **D01–D16** | v1（决策规则版） | 触发条件 → 首选举措 → 失败时降级 → 记录与退出码 | 想知道"这一步出问题改成什么" |
| **H01–H14** | v2（增益可验证版） | 触发 → 首选 → 降级 → 记录；每条的降级都会影响增益断言 | 想知道"降级后还能不能声称更强" |
| **M01–M14** | v3（机制与复用版） | 触发 → 首选 → 降级路径 → 记录；按机制编号 | 想知道"哪一项机制失效了" |

`SKILL.md` §4 用的编号是 **D01–D19（D19 为本轮新增）**，也就是 D 表加一条。
本文件把三张表**逐字并置**，并给出对照与不变量，避免 union 之后丢内容。

## 0. 编号对照（同一情形在三种切法下的编号）

| 情形 | D | H | M |
|-|-|-|-|
| case.json 缺失/不可解析 | D01 / D02 | H01 | M01 |
| 材料路径不存在 / 不可读 | D03 / D04 | H02 | M02 |
| PDF 加密 / 无文本层 | （§2.1 处置） | H03 / H04 | M03 / M04 |
| 无 PDF 后端 | D05 | （§2.3） | （§2.3 / 链 A） |
| CP1/K1/Q1 lint 偏差 | D06（方案不可读）/ §6 | H05 | M05 |
| 模板缺席（正常分支） | D09 | H06 | M06 |
| 模板损坏 / 占位符不足 | D08 | H07 | M07 |
| 页数超限 | D10 | H08 | M08 |
| 图/表抽不出 | D11 | H09 | M09 |
| 重建图失败 | D12 | H10 | M10 |
| 缺 python-pptx | D13 | H11 | M11 |
| 缺字体 / Pillow | D14 | H12 | M12 |
| 有/无渲染引擎 | D17 | H13 | M13 |
| 契约四形态 / 未知字段 | D15 | H14 | M14 |
| 契约文档缺失 | D16 | （同 H14 门） | （同 M14） |
| 图文同页 | **D19（本轮新增）** | （H07 的同类） | （M07 的同类） |
| 任一降级后必须双写 | D18 | H14 兜底段 | 兜底段 |

> 编号是**索引**，不是三份真相。改规则时：先改 `SKILL.md` §4（D 表），
> 再同步 `references/failure-modes.md` 的同号条目，最后回本文件核对三表是否仍然一致。

## 1. D01–D16（v1：决策规则四列版）

| # | 触发条件 | 首选举措 | 失败时的降级 | 记录与退出码 |
|-|-|-|-|-|
| D01 | `case.json` 不存在或 JSON 不可解析 | 直接以 `status=failed` 收尾，不发明产物 | 输入完全不可读时不创建输出目录 | `case_unreadable`；**main.py → 3** |
| D02 | 材料路径不存在 / 不可读 | 只产出含元信息的 result，不构建 deck | 状态降 `failed`，语义字段按类型给空值 | `status=failed`、`material_status=unreadable`、`sources[].reason`；main.py → 0/1（以 self_check 为准） |
| D03 | PDF 报 encrypted | 先试空口令一次 | 改用外部导出的 `.txt`（`--materials`）并如实说明工具 | `uncertainty[]` + `sources[].tool`；assetkit → 2 |
| D04 | PDF 无文本层（`text_chars = 0`，扫描件） | 标注"图像型 PDF"，仍引用可抽取的图 | **不做 OCR 冒充**；必要时请用户补文本 | `uncertainty[]` + `sources[].tool`；assetkit → 2 |
| D05 | C1 lint 报偏差（bullet 超限 / 缺 evidence 且未标 gap / 缺 claim） | 先按报错逐条修 spec 再跑 C1 | 确属案例硬约束无法满足 → 构建继续但状态降 `partial`，偏差双写 | `spec_lint.problems` + `uncertainty[]` + `change_records[]`；spec_lint → 1 |
| D06 | 案例未提供模板（`resolve_template → builtin`） | 直接使用内置 16:9 学术版式 | 需要真实模板时跑 `make_template.py` 现场生成 | `deck.template.kind="builtin"`；make_template → 2（缺 python-pptx） |
| D07 | 声明了模板但文件不存在 / 打不开 / 占位符不足 | 回退内置版式并继续（**不是失败**） | 无 title/body/picture 占位符 → 名匹配→索引回退→补画文本框（登记命名） | `deck.template.kind/guard/error` + `layouts_used` + `uncertainty[]` |
| D08 | 页数超过 `slide_count` | 合并非证据页（封面/过渡/收尾优先） | **绝不静默丢弃证据页**；仍超限则如实标记 | `deck.page_budget_met=false` + `change_records[]` + `uncertainty[]` |
| D09 | 图/表抽不出（`images_extracted=0` 或损坏） | 该页保留显式占位框，文案注明"需补齐，非原图" | 引用与定位照留，图位空缺但不伪造 | `figure.placed=null` + `placeholder=true` + `uncertainty[]` |
| D10 | 重建图失败（无 matplotlib / 表格数据不全） | 跳过该图，保留表引用与数字 | 数字仍逐字来自原文，绝不估算补齐 | `charts[].chart.reason` + `run_meta.matplotlib_available=false` |
| D11 | `python-pptx` 缺失 | `deck=null`、状态降级，如实说明——**不生成假文件** | 仍写出契约完整的 result.json（含语义字段空值规则） | `deck_error` + `uncertainty[]` + `status` |
| D12 | 预览字体探测失败 / `Pillow` 缺失 | 降级 PIL 默认字体继续；deck 内仍写主题字体 + latin/ea 双写 | Pillow 完全缺失 → `previews=[]` 并降级说明 | `run_meta.preview_font`（可 null）+ `run_meta.rendered_with` + `uncertainty[]` |
| D13 | 检测到 LibreOffice / PowerPoint | `soffice --headless --convert-to pdf` 产出真 PDF 并改写记录 | 无引擎 → PIL 近似，三处标注 | `run_meta.rendered_with` + `previews[].kind=pil-approximation`；G8 为 warning |
| D14 | 输入不在 `/input`（环境变量/自定义路径） | 探测 `CASE_PATH`/`OUTPUT_DIR`/cwd 下 `case.json`，以可读文件为准 | 都不可读 → 按 D01 处置 | `run_meta.case_file` + `uncertainty[]` |
| D15 | `output_contract` 出现未知/无值字段（四形态任一） | 有真实值写真实值；否则按容器给 `""`/`[]`/`{}`，**禁止 null** | 形态无法判断（既非 dict 也非 list）→ 原样回显并记 uncertainty | `result.output_contract`；check_contract → 1（缺字段）/ 2（契约文档解析不出） |
| D16 | 任一降级发生后 | 同步写 `uncertainty[]`（发生了什么+影响）与 `change_records[]`（何时+为什么） | 两者只写其一会触发不变量 I5 违规 | `run_meta.self_check.ok=false` 时 **main.py → 1** |

## 2. H01–H14（v2：增益视角的异常处置）

| # | 触发 | 首选 | 降级 | 记录 |
|-|-|-|-|-|
| H01 | `case.json` 缺失/不可解析 | 以 `status=failed` 收尾，不发明产物 | 完全不可读时不创建输出目录 | `case_unreadable`；`main.py` → 3 |
| H02 | 材料路径不存在 | 只产出元信息 result，不构建 deck | 状态降 `failed`，语义字段给类型空值 | `material_status=unreadable`、`sources[].reason` |
| H03 | PDF 加密 | 试空口令一次 | 改用外部 `.txt`（`--materials`），工具如实记 | `uncertainty[]` + `sources[].tool`；assetkit → 2 |
| H04 | PDF 无文本层（扫描件） | 标注"图像型 PDF"，仍引用可抽取的图 | **不做 OCR 冒充** | `uncertainty[]` + `sources[].tool` |
| H05 | Q1 lint 报偏差 | 按报错逐条修 spec 再跑 | 案例硬约束确实无法满足 → 继续构建但状态降 `partial`，偏差双写 | `spec_lint.problems` + `uncertainty[]` + `change_records[]` |
| H06 | 未提供模板 | 用内置 16:9 学术版式（正常分支） | 需要真模板时 `make_template.py` 现产 | `deck.template.kind="builtin"` + `uncertainty[]` |
| H07 | 模板不存在/损坏/占位符不足 | 回退内置版式并继续 | 名匹配 → 索引回退 → 补画文本框（登记命名） | `deck.template.kind/guard/error` + `layouts_used` |
| H08 | 页数超 `slide_count` | 合并非证据页（封面/过渡/收尾优先） | **绝不静默丢弃证据页**；仍超限如实标记 | `page_budget_met=false` + `change_records[]` |
| H09 | 图/表抽不出 | 保留显式占位框（注明"需补齐，非原图"） | 引用与定位照留，不伪造图片 | `figure.placed=null` + `placeholder=true` |
| H10 | 重建图失败 | 跳过图，保留表引用与原文数字 | **不估算补齐数字** | `charts[].chart.reason` + `run_meta.matplotlib_available` |
| H11 | 缺 `python-pptx` | `deck=null`、状态降级、如实说明 | **不生成假文件**；result.json 仍契约完整 | `deck_error` + `uncertainty[]` + `status` |
| H12 | 字体/Pillow 缺失 | 降级 PIL 默认字体继续；deck 内 latin+ea 双写 | Pillow 完全缺失 → `previews=[]` 并说明 | `run_meta.preview_font`（可 null）+ `rendered_with` |
| H13 | 有/无渲染引擎 | 有 `soffice` → 真 PDF；无 → PIL 近似 | 近似必须三处标注，不得称为真实渲染 | `run_meta.rendered_with` + `previews[].kind` |
| H14 | 输入不在 `/input`／契约出现未知字段 | 探测 `CASE_PATH`/`OUTPUT_DIR`/cwd；四形态回显，未知字段 `setdefault` | 都不可读 → H01；**任何声明字段禁止 null** | `run_meta.case_file` + `result.output_contract` |

## 3. M01–M14（v3：机制触发的回退链）

| # | 触发 | 首选 | 降级路径 | 记录 |
|-|-|-|-|-|
| M01 | `case.json` 缺失/不可解析 | `status=failed` 收尾，不发明产物 | 完全不可读时不建输出目录 | `case_unreadable`；`main.py` → 3 |
| M02 | 材料路径不存在 | 只产元信息 result，不构建 deck | 状态降 `failed`，语义字段给类型空值 | `material_status=unreadable` + `sources[].reason` |
| M03 | PDF 加密 | 试空口令一次 | 外部 `.txt`（`--materials`），工具如实记 | `uncertainty[]` + `sources[].tool` |
| M04 | PDF 无文本层（扫描件） | 标注"图像型 PDF"，仍引用可抽取的图 | **不做 OCR 冒充** | `uncertainty[]` + `sources[].tool` |
| M05 | K1 lint 报偏差 | 按报错逐条修 spec 再跑 K1 | 硬约束确实无法满足 → 继续构建，状态降 `partial`，偏差双写 | `spec_lint.problems` + `uncertainty[]` + `change_records[]` |
| M06 | 未提供模板 | 内置 16:9 学术版式（正常分支，M7 无二进制包袱） | 需要真模板时 `make_template.py` 现产 | `deck.template.kind="builtin"` + `uncertainty[]` |
| M07 | 模板不存在/损坏/占位符不足 | 回退内置版式并继续 | 名匹配 → 索引回退 → 补画文本框（登记命名，M6） | `deck.template.kind/guard/error` + `layouts_used` |
| M08 | 页数超 `slide_count` | 合并非证据页（封面/过渡/收尾优先） | **绝不静默丢弃证据页** | `page_budget_met=false` + `change_records[]` |
| M09 | 图/表抽不出 | 保留**显式占位框**（M4 的诚实语义） | 引用与定位照留，不伪造图片 | `figure.placed=null` + `placeholder=true` |
| M10 | 重建图失败 | 跳过图，保留表引用与原文数字 | 不估算补齐 | `charts[].chart.reason` + `run_meta.matplotlib_available` |
| M11 | 缺 `python-pptx` | `deck=null`、状态降级、如实说明 | **不生成假文件** | `deck_error` + `uncertainty[]` + `status` |
| M12 | 字体/Pillow 缺失 | 降级 PIL 默认字体继续；deck 内 latin+ea 双写（M5） | Pillow 全缺 → `previews=[]` 并说明 | `run_meta.preview_font`（可 null）+ `rendered_with` |
| M13 | 有/无渲染引擎 | 有 `soffice` → 真 PDF；无 → PIL 近似 | 近似三处标注，不得称为真实渲染 | `run_meta.rendered_with` + `previews[].kind` |
| M14 | 输入不在 `/input`／契约出现未知字段 | 探测 `CASE_PATH`/`OUTPUT_DIR`/cwd；四形态回显，未知字段 `setdefault` | 都不可读 → M01；**声明字段禁止 null** | `run_meta.case_file` + `result.output_contract` |

## 4. 状态一致性不变量 I1–I6（v1；交付前逐条断言）

| # | 不变量 | 违反后果 |
|-|-|-|
| I1 | 材料不可读 ⇒ **禁止** `status=completed` | `export_check` 判 error；必须降 `failed` |
| I2 | 存在显式 `evidence_gap` 或图片只有占位框 ⇒ `status ≤ partial`，且 `uncertainty` 点名页号 | C3 视为状态不一致 |
| I3 | C1 lint 有偏差且继续构建 ⇒ `status ≤ partial`，`spec_lint.problems` 与 `uncertainty` 同时保留 | 只留其一即违规 |
| I4 | `charts[].chart.note` 出现 `reconstructed_from_table` ⇒ 该图不得在页面或备注里被称为论文原图 | 触发诚实性硬约束（`OUTPUT_CONTRACT.md` §4.1） |
| I5 | 任一次降级 ⇒ `uncertainty[]` 与 `change_records[]` 同时有对应条目 | `run_meta.self_check.ok=false`，main.py → 1 |
| I6 | `uncertainty` 为空 ⇒ 仅当整条链路无任何降级；`previews[].kind` 为近似 ⇒ `rendered_with` 必须写明 | 空 uncertainty 需能在本次日志中举证 |

## 5. 检查点命名对照（三套叫法指的是同一件事）

| 位置 | 基线/ v4 叫法 | v1 叫法 | v2 叫法 | v3 叫法 |
|-|-|-|-|-|
| 写方案后的结构 lint | CP1 | C1 | Q1（闸门） | K1（关口） |
| 构建完成 | （main.py 内嵌） | P4 | Q2（闸门） | 阶段 5 |
| 交付前导出检查 | CP3 | C3 | Q3（闸门） | K3（关口） |
| 端到端入口 | `main.py` | P4 | Step 4 | 阶段 5 |

三套叫法在文档里都出现过；**实现只有一个**（`spec_lint.py` / `export_check.py` /
`main.py`），因此编号差异不影响行为，只影响你读哪一段。

## 6. 增益断言与降级的相容性（v2 的判据 + v3 的机制归因）

- v2 的判据（`references/GAIN-PROTOCOL.md` §4）：**声明了增益，就必须能指出降级**——
  一次 `partial` 运行的分数不能与 `completed` 混在一起比较；
- v3 的归因（`references/MECHANISM.md`）：`ablation` 臂只摘掉"Agent 写的页级方案 + K1 前置门"
  这一项机制（M2），其余机制（M1 契约同源、M4 占位诚实、M5 主题字体、M6 命名、M9 自定位）
  在消融臂里保持 19/19，因此差值可以归因到 M2；
- 两者的共同口径：**降级必须写进产物**，否则"更强"这句话没有基线可比。
