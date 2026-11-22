# failure-modes.md — 失败模式 ↔ 决策规则 ↔ 注入用例（三者互查）

> 本文件是「可靠体验（10 分）」的落点，也是本项目**唯一一份把三者对齐**的文档：
> **失败模式**（会发生什么）↔ **决策规则 D1–D20**（该怎么处置）↔ **注入用例 F00–F22**
> （怎么证明它真的这样处置）。
>
> 每行末尾的证据用例都可以逐条复跑：
> `python "$SKILL_DIR/scripts/fault_inject.py" --out /tmp/fi --only F04 --verbose`
>
> **原则：任何降级都不允许静默成功。** 要么写进 `uncertainty` / `warnings` / `render_log.json`，
> 要么直接非零退出。**"静默失败"在这里有可判定定义**：进程 `exit 0` 且 `status=success`，
> 而注入的缺陷在 `uncertainty` 与相关字段里都没有任何记录。
>
> 本包修复前实测到 **8 条**静默失败（F04 F05 F07 F09 F11 F13 F16 F18），已按**纯增量**修好并
> 复跑为 0 条 —— 修复点、增删行数与触发用例见 [`FAULT-MATRIX.md`](FAULT-MATRIX.md) §2。

---

## 1. 退出码语义（脚本级硬契约，与实测一致）

| 脚本 | 退出码 | 含义 | 实测用例 |
|-|-|-|-|
| `scripts/main.py` | `0` | 运行完成，`status ∈ {success, partial}`，`result.json` 与产物已写出 | F00 F03 F04 F05 F09 F10 F11 F12 F13 F14 F15 F16 F18–F22 |
| `scripts/main.py` | `1` | **硬输入错误**：`case.json` 缺失/不可解析/抽取失败；`--plan` 不可解析 | F01 F02 F08 |
| `scripts/main.py` | `2` | **环境/内部错误**：输出目录不可用、版面或 SVG 失败、`status=failed` | F17（改前为未捕获 traceback + exit 1） |
| `scripts/scaffold.py` | `0` / `1` | 方案骨架生成成功 / `case.json` 缺失或抽取失败 | F09（骨架由它真实生成） |
| `scripts/spec_lint.py` | `0` / `1` | lint 通过 / 有 problems（**退出码即判据**） | F10（画布超界 → problems 非空） |
| `scripts/check_contract.py` | `0` / `1` / `2` | 契约全覆盖且无 null / 有缺口 / 用法或文件错误 | F18 F19 F20 F21 F22 |
| `scripts/fault_inject.py` | `0` / `1` / `2` | 全部符合期望 / 有静默失败（或 strict 下有 mismatch）/ 用法或环境错误 | 整轮演练 |

> `partial` 仍返回 `0`（产物完整、限制已记录）；**只有**读不到输入或产不出关键产物才是非零。

## 2. 五类失败模式 → 处置 → 记录位点 → 实测证据

### 2.1 材料异常

| 情形 | 检测点 | 处置 | 记录位点 | 实测用例（修复后） |
|-|-|-|-|-|
| `case.json` 不存在 | `main.py` `os.path.isfile` | **exit 1** + `{"status":"failed","error":…}` | stdout | F01（1 / 无 result.json） |
| `case.json` 不是合法 JSON | `extract.load_json` | **exit 1**，不留半成品 | stdout | F02（1 / 无 result.json） |
| `case.json` 缺 `case_id` | 回退链 `case_id→id→case→文件名` | 用文件名兜底，`status` 可仍为 success（实体为空则 partial） | `result.case_id` | F03（0 / partial / `case_id=fi-f03`） |
| 声明的材料路径不存在 | `extract.run` 材料预检（**F1 新增**） | 继续用其余材料；**必须**在 uncertainty 点名缺失路径 | `uncertainty` | F04（0 / partial，`uncertainty[0]` 含"材料路径不存在"） |
| 材料是二进制 / PDF | 魔数 `%PDF-` 或 NUL 探测（**F1/F2 新增**） | 有 `pypdf` 则抽文本层并标 `material(pdf-text)`；无则跳过并声明"数值不上画布" | `uncertainty` + `provenance.source_files[].role` | F05（0 / success，含 PDF 文本层）、F16（0 / partial，pypdf 缺失） |
| 材料非 UTF-8（GBK/Latin-1） | 逐文件 UTF-8 探针（**F1 新增**） | 以替换字符读取，不中断，**记录下来** | `uncertainty` | F16 路径覆盖；F1 修复项 |
| 一条材料都没读到 | `extract.run` 末尾（**F3 新增**） | 面板只放要点文本；note 使 `status` 降 partial | `notes` → `warnings` | F04 F16 |
| 关键数值缺失 | `audit.missing_values` | 「数值缺失」占位，**绝不编造** | `audit.missing_values` + `uncertainty` | F10 F12 语境；v5 案例 B 实测 1 条（`夜间地表温度差`） |
| 数值单位含数字/`-`/`/`（G1/G3 修复） | `_parse_value` / `parse_fact_lines` 的宽松二次解析 | 不再把材料里存在的值误判为缺失 | `audit.missing_values` | v5 案例 A：`missing_values` 从 2 条降到 0 条 |
| 实体重名/歧义 | `normalize_entities` 同 id 首见优先 | 两项并列 + 说明歧义 | `uncertainty`（D5） | 见 D5 行 |
| 材料两处数值矛盾 | 首见优先 + **冲突留痕（G2 修复）** | 保留首见值，两处数值与各自 `src` 并列；**不取平均、不择优** | `uncertainty`（D7） | v5 案例 B 实测：`uncertainty` 出现「材料与 case.json 数值不一致（首见优先，未取平均）：…」 |
| 材料里的行被误判成"关系"（G5 修复） | 关系分支要求真实箭头记号 | 无箭头的行走「key = value」数据通道；行首项目符号剥除 | `content_summary.data/relations` | v5 案例 A：`relations` 从 25 降到 9 |
| `entities` 字段类型错（字符串） | `normalize_entities` 容错 | 以真实值为准继续，不崩 | `content_summary` | F06（0 / success） |

### 2.2 模板缺失 / 预制资源缺失

本包**不含任何二进制模板**（无 `.pptx/.png/.pdf/.svg/.ttf`），"模板"= 代码 + 文本规格 + 运行时生成。

| 情形 | 检测点 | 处置 | 记录位点 | 实测用例 |
|-|-|-|-|-|
| 预置渲染件不存在（本包本就不带） | 结构上不触发 | 由 `svgbuilder.py` / `preview.py` 运行时生成 | `deliverables[]` | F00（正向对照） |
| `--plan` 指向不存在的文件 | `main.py` 探针 | 方案门 `valid=false` ⇒ **status 降 partial**（**F5 修复**） | `result.plan.lint` | F07（0 / partial） |
| `--plan` 是非法 JSON | `main.py` 探针解析（**F4 新增**） | **exit 1** + `{"error":"plan.json unreadable: …"}`，不抛栈 | stdout | F08（1 / 无 result.json） |
| 方案是未定稿骨架（four_elements 空） | `spec_lint.lint_plan` | 方案门拦下 ⇒ **status 降 partial**（**F5 修复**） | `result.plan.lint.problems` | F09（0 / partial） |
| 方案画布超界（8000×8000） | `spec_lint.lint` 的 clamp [600,4000] | 规格门记录并降 partial | `result.spec_lint` + `uncertainty` | F10（0 / partial，problems 含 canvas） |
| 方案关系项缺 `src` | `lint_plan` 源定位检查 | 方案门报出 ⇒ 降 partial | `result.plan.lint` | F11（0 / partial） |
| 方案覆盖案例 constraints | `plan_overrides` | 设计决策以 plan 为准，**并写入 `change_records`**（**F9 修复**） | `result.change_records` | F12（0 / success，override 已留痕） |
| 字体文件不存在 | `PIXEL_FONT_CANDIDATES` 运行期探测 | 逐级回退到默认字体（CJK 尽量保住） | `render_log.font` | F13 F14 F15 语境 |

### 2.3 依赖缺失（逐级降级，禁止静默）

| 情形 | 检测点 | 处置 | 记录位点 | 实测用例 |
|-|-|-|-|-|
| `matplotlib` 不可导入 | `preview.render` 首段 try | 回退 Pillow；**status 降 partial**（**F7 修复**） | `render_log.backend` + `uncertainty` | F13（0 / partial / `backend=Pillow`） |
| `Pillow` 不可导入 | `_render_pil` 的 import | **matplotlib 自身 `import PIL`，会连带失效** ⇒ 落到纯 Python PNG（**P1 修复**，此前是死代码） | `render_log` 两级失败原文 + `uncertainty` | F14（0 / partial / `backend=pure-python-png`） |
| 两级后端都不可用 | 三级回退链 | 纯 Python PNG 仍出图，文字占位并注明 | `render_log.warnings` | F15（0 / partial） |
| `pypdf` 不可导入（材料是 PDF） | `_binary_material_text` 的可选导入 | 不抽文本层；**声明数值不上画布** | `uncertainty` | F16（0 / partial） |
| PDF 后端不可用 | `render_report.pdf.present` | PNG 照常；PDF 条目 `present:false` + `reason` | `deliverables[format=pdf]` | F12（pdf=false 时同样 `present:false` + reason） |
| 输出目录不可用（`--out` 是文件） | `main.py` makedirs 包装（**F8 新增**） | **exit 2** + `{"error":"output directory not usable: …"}` | stdout | F17（2 / 无 result.json） |

### 2.4 契约四形态

| 情形 | 形态 | 处置 | 记录位点 | 实测用例 |
|-|-|-|-|-|
| 字段声明无真实值（`null`） | ①类型提示 | 归一化为 `""` 并记录（**F6 修复**，此前原样回显 null） | 顶层字段 + `uncertainty` | F18（0 / success / `uncertainty` 含"null"） |
| 契约键与信封保留键冲突（`summary`） | 任意 | 顶层保留信封值，案例值移入 `output_contract_echo` | `result.output_contract_echo` | F19（0 / success） |
| 声明数字、实值为字符串（`"300"`） | ①类型提示 | 以**真实值**写入，类型偏差可被复核方看到 | 顶层字段 | F20（0 / success） |
| 案例完全没有 `output_contract` | — | 信封 18 键仍须齐全 | 顶层 18 键 | F21（0 / success） |
| 容器形态给空列表 | ②字段→容器 | 空列表是**合法值**，不得被 `null`/`""` 替换 | 顶层字段 | F22（0 / success） |
| 布尔开关无真实值 | ③布尔 | 写 `false`（真布尔，不写 0/字符串） | 顶层字段 | `check_contract.py` 判据覆盖 |
| 字段清单无真实值 | ④字段清单 | 写 `[]`；有值时回显实际图层名 | 顶层字段 | F22 + `audit.layer_naming.found` |

### 2.5 状态一致性

| 情形 | 检测点 | 处置 | 记录位点 | 实测用例 |
|-|-|-|-|-|
| 规格 lint 不过 | `spec_lint.lint` | `status` 直接判 partial，**不做 success** | `result.spec_lint` + `uncertainty` | F10 |
| 方案 lint 不过 | `spec_lint.lint_plan` | 同上（**F5 修复**） | `result.plan.lint` | F07 F09 F11 |
| 渲染后端降级 | `render_report.matplotlib_failed/pil_failed` | `status` 降 partial（**F7 修复**） | `uncertainty` + `render_log` | F13 F14 F15 |
| SVG 不良构 / PNG 无效 | `audit.checks.*` | `status=failed` + **exit 2**；已写出产物保留在原路径 | `audit.checks` + stderr | `_status()` 判据 |
| 方案覆盖决策未留痕 | `change_notes` | 写入 `change_records`（**F9 修复**） | `result.change_records` | F12 |
| 契约字段为 null | `check_contract.py` | 视为缺口（exit 1）；本包在写入前已归一化 | `check_contract` 输出 | F18 |
| 产物路径为绝对路径或指向不存在文件 | `deliverables[].path` 一律相对 | 复核三方一致（文件真实存在） | `deliverables[]` | F00 F12 |

## 3. 失败模式 ↔ 规则号 ↔ 用例号 速查

| 规则 | 一句话 | 注入用例 |
|-|-|-|
| D1 | `case.json` 缺失/不可解析 → exit 1 | F01 F02 |
| D2 | 缺 `case_id` → 回退链 | F03 |
| D3 | `task.md` 缺失 → 只用 case + 材料 | — |
| D4 | 材料路径缺失/为空 → 继续但记录 | F04 |
| D5 | 数值缺失 → 占位，不编造 | F10 F12 语境 |
| D6 | 实体歧义 → 首见优先 + 并列 | — |
| D7 | 材料数值矛盾 → 首见优先 + 双 `src` | v5 案例 B |
| D8 | 非 UTF-8 → 替换字符读取 + 记录 | F1 修复项 |
| D9 | 二进制/PDF 材料 → 文本层或跳过 + 记录 | F05 F16 |
| D10 | 字体缺失 → 探测回退 + 记字体名 | F13 F14 F15 语境 |
| D11 | 渲染后端缺失 → 三级回退 | F13 F14 F15 |
| D12 | PDF 不可用 → PNG 照常 + `present:false`+reason | F12 |
| D13 | 文字溢出/越界 → 缩字号/夹紧 + 记录 | F10 语境 |
| D14 | 方案或规格 lint 不过 → 先修，修不动降 partial | F07 F09 F10 F11 |
| D15 | 契约无真实值 → `""`/`[]`/`false`/`{}`，禁 null | F18 |
| D16 | 契约键冲突 → `output_contract_echo` | F19 |
| D17 | 声明类型与实际不符 → 以真实值为准 + 说明 | F20 F06 |
| D18 | lint 不过仍想报成功 → 禁止 | F07 F09 F11 |
| D19 | 产物无效 → `status=failed` + exit 2 | F17（环境侧） |
| D20 | 重跑结构漂移 → 排查时间戳/随机数 | TEST.md §3 确定性实测 |

## 4. 科学诚实性红线（优先于任何降级）

1. 材料里定位不到的数值**不得上画布**，只能进 `uncertainty` 并以「数值缺失」占位。
2. 两处数值矛盾**不取平均、不择优、不改写**，双 `src` 并列交人判断。
3. 二进制/扫描件材料取不到文本时，**宁可少画也不编造**（数值全部不上画布）。
4. 任何降级都必须留下记录；**"静默成功"本身就是缺陷**（本包已修掉 8 处）。

## 5. 复现命令（全部在包外执行）

```bash
SKILL_DIR=/abs/path/to/graphical-abstract-7030fff2
PKG=/tmp/ga-pkg && cp -r "$SKILL_DIR" "$PKG" && cd "$PKG"

python scripts/main.py --case examples/case.json --out /tmp/o            # exit 0 / 26 键
python scripts/check_contract.py --result /tmp/o/result.json --case examples/case.json   # exit 0
python scripts/fault_inject.py --out /tmp/fi --fail-on strict             # exit 0 / 23 ok / 0 silent
python scripts/fault_inject.py --out /tmp/fi4 --only input --verbose      # 单类复现
python scripts/fault_inject.py --out /tmp/fi15 --only F15 --verbose       # 单条复现
```

## 6. 表外情形怎么办（"先记后判"）

遇到规则表没列出的情形时：**先把观察写进 `uncertainty` / `warnings`，再判断是否可以继续。**
禁止的做法是"因为规则没写，所以静默忽略"。新增规则时必须在四处同步编号：
`SKILL.md` §7、本文件 §2/§3、`FAULT-MATRIX.md`（若可注入）、以及对应脚本的注释。
