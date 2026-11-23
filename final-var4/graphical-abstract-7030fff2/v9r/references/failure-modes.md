# failure-modes.md — 失败模式 ↔ 决策规则 ↔ 注入用例（三者互查，v6 合并版）

> 本文件是「可靠体验（10 分）」的落点，也是全包**唯一**把三者对齐的文档：
> **失败模式**（会发生什么）↔ **决策规则 D1–D20**（该怎么处置）↔ **注入用例 F00–F22**
> （怎么证明它真的这样处置）。每条证据都可以逐条复跑：
> `python "$SKILL_DIR/scripts/fault_inject.py" --out /tmp/fi --only F04 --verbose`
>
> **原则：任何降级都不允许静默成功。** 要么写进 `uncertainty` / `warnings` / `render_log.json`，
> 要么直接非零退出。
>
> **"静默失败"有可判定定义**：进程 `exit 0` 且 `status=success`，而缺陷在 `uncertainty`
> 与相关字段里都没有任何记录。本包修复前实测到 **8 条**，已按**纯增量**修好并复跑为 **0 条**
> —— 修复项、增删行数与触发用例见 [`FAULT-MATRIX.md`](FAULT-MATRIX.md) §2（F1–F9 / G1–G5 / P1）。

## 1. 退出码语义（脚本级硬契约，与实测一致）

| 脚本 | 退出码 | 含义 | 行为 |
|-|-|-|-|
| `scripts/main.py` | `0` | 运行完成，`status ∈ {success, partial}` | 已写出 `result.json` 与全部产物 |
| `scripts/main.py` | `1` | **硬输入错误**：`case.json` 缺失/不可解析、抽取失败、`--plan` 不可解析 | 打印 JSON 错误到 stdout，**不留半成品冒充成功** |
| `scripts/main.py` | `2` | **环境/内部错误**：输出目录不可用、版面或 SVG 失败、`status=failed` | 打印 JSON 错误 |
| `scripts/scaffold.py` | `0` / `1` | 骨架生成成功 / `case.json` 缺失或抽取失败 | `1` 时不写 plan |
| `scripts/spec_lint.py` | `0` / `1` | lint 通过 / 有 problems（**退出码即判据**） | problems 逐条打印 |
| `scripts/check_contract.py` | `0` / `1` / `2` | 契约全覆盖且无 null / 有缺口 / 用法或文件错误 | 缺口逐条打印 |
| `scripts/fault_inject.py` | `0` / `1` / `2` | 23 条注入全符合期望 / 有静默失败（或 strict 下 mismatch）/ 用法或环境错误 | 报告写 `--out/fault_report.json` |
| `scripts/gain_harness.py` | `0` | 只读测量完成 | 打印指标 JSON |

> `partial` 仍返回 `0`（产物完整、限制已记录）；**只有**读不到输入或产不出关键产物才是非零。

## 2. 五类失败模式 → 处置 → 记录位点 → 实测证据

### 2.1 材料异常

| 情形 | 检测点 | 处置 | 记录位点 | 实测用例 |
|-|-|-|-|-|
| `case.json` 不存在 | `os.path.isfile` | **exit 1** + `{"status":"failed","error":…}` | stdout | F01 |
| `case.json` 不可解析 | `load_json` | **exit 1**，不留半成品 | stdout | F02 |
| 缺 `case_id` | 回退链 `case_id→id→case→文件名` | 用文件名兜底，**不伪造** | `result.case_id` | F03 |
| 声明的材料路径不存在 | 材料预检 | 继续用其余材料，**点名缺失路径** | `uncertainty` | F04 |
| 材料是二进制 / PDF | 魔数 `%PDF-` 或 NUL 探测 | 有 `pypdf` 抽文本层（标 `material(pdf-text)`）；否则跳过并声明"数值不上画布" | `uncertainty` + `provenance.source_files[].role` | F05 / F16 |
| 材料非 UTF-8 | 逐文件 UTF-8 探针 | 替换字符读取、不中断、**记录下来** | `uncertainty` | 材料预检新增项 |
| 一条材料都没读到 | `extract.run()` 末尾 | 面板只放要点文本；note 使 `status` 降 `partial` | `notes` → `warnings` | F04 / F16 |
| 关键数值缺失 | `audit.missing_values` | 「数值缺失」占位，**绝不编造** | `audit.missing_values` + `uncertainty` | 题集 L3 实测（`夜间地表温度差`） |
| 材料同一指标两处数值矛盾 | 材料事实与 case 声明同 id 时比较数值 | 首见优先；两处数值与各自 `src` **并列**；不取平均、不择优 | `uncertainty` | 题集 L3 实测（0.14 / 0.19） |
| 实体重名 / 歧义 | 同 id 首见优先 | 两项都列出并说明歧义 | `uncertainty` | D6 |
| 材料行被误判成"关系" | 关系分支要求**真实箭头记号** | 无箭头的行走数据通道；行首项目符号剥除 | `content_summary.data/relations` | 题集 L2 实测（`relations` 25 → 9） |
| 数值单位含数字 / `-` / `/` | 数值解析的宽松二次解析 | 不再把材料里存在的值误判为缺失 | `audit.missing_values` | 题集 L2 实测（`missing_values` 2 → 0） |
| `entities` 字段类型错 | 归一化容错 | 以真实值为准继续，不崩 | `content_summary` | F06 |
| 散文里的数字 / 带比较符与区间的值 | 只认"独立行 + 数字单位" | **不抽取**（宁缺勿错） | `audit.missing_values` | `SKILL.md`「限制与边界」 |

**反模式（禁止）**：为让图"完整"给缺值项补一个看起来合理的数字；把材料里没有的实体画上画布。

> 上表 5 条标注「题集 L2/L3 实测」的行，来自 R2 三案例题集（`calab-perovskite-001` / `urban-heat-001`）；
> 该题集文件未随本包发送（≤50 文件预算），其原始录入与可复跑命令见本 Skill 的 R2 版本包。


### 2.2 模板缺失 / 预置资源缺失

本包**不含任何二进制模板**（无 `.pptx/.png/.pdf/.svg/.ttf`）——"模板"= 代码 + 文本规格 + 运行时生成。

| 情形 | 处置 | 记录位点 | 实测用例 |
|-|-|-|-|
| 预置渲染件不存在（本包本就不带） | 运行时生成（`svgbuilder.py` + `preview.py`） | `deliverables[]` | F00（正向对照） |
| `--plan` 不存在 | 方案门 `valid=false` ⇒ **`status` 降 `partial`** | `result.plan.lint` | F07 |
| `--plan` 非法 JSON | **exit 1** + `{"error":"plan.json unreadable: …"}`，不抛栈 | stdout | F08 |
| 方案是未定稿骨架 | 方案门拦下 ⇒ 降 `partial` | `result.plan.lint.problems` | F09 |
| 方案画布超界（8000×8000） | 规格门（clamp [600,4000]）记录并降 `partial` | `result.spec_lint` + `uncertainty` | F10 |
| 方案关系项缺 `src` | 方案门报出 ⇒ 降 `partial` | `result.plan.lint` | F11 |
| 方案覆盖案例 constraints | 以 plan 为准，**并写入 `change_records`** | `result.change_records` | F12 |
| `task.md` 缺失 | 面板要点改由材料小节标题映射；要点为空时不放填充句 | `warnings` | D3 |
| 字体文件不存在 | 运行期候选路径探测 → 逐级回退，字体名如实记录 | `render_log.font` | F13–F15 语境 |

**判定法**：若某文件缺失会导致"必须由作者本机补一份二进制"，那它就不该进包。

### 2.3 依赖缺失（逐级降级，禁止静默）

| 情形 | 处置 | 记录位点 | 实测用例 |
|-|-|-|-|
| `matplotlib` 不可导入 | 回退 Pillow；`status` 降 `partial` | `render_log.backend` + `uncertainty` | F13 |
| `Pillow` 不可导入 | **matplotlib 自身 `import PIL`，会连带失效** ⇒ 落到纯 Python PNG | 两级失败原文进 `render_log` + `uncertainty` | F14 |
| 两级都不可用 | 纯 Python PNG 仍出图（文字占位并注明） | `render_log.warnings` | F15（`backend=pure-python-png`） |
| `pypdf` 不可导入且材料是 PDF | 不抽文本层，**声明数值不上画布** | `uncertainty` | F16 |
| PDF 开关/后端不可用 | PNG 照常；PDF 条目 `present:false` + `reason` | `deliverables[format=pdf]` | 题集 L2/L3（`reason="disabled by constraints (pdf=false)"`） |
| 输出目录不可用（`--out` 是文件） | **exit 2** + `{"error":"output directory not usable: …"}` | stdout | F17 |

### 2.4 契约四形态

| 情形 | 形态 | 处置 | 记录位点 | 实测用例 |
|-|-|-|-|-|
| 字段无真实值 | ①类型提示 | 按类型给空值，**禁 null** | 顶层字段 + `uncertainty` | F18 |
| 字段声明为 `null` | ①类型提示 | 归一化为空值并记录 | 顶层字段 + `uncertainty` | F18 |
| 键与信封保留键冲突（`summary`） | 任意 | 顶层保留信封值，案例值移入 `output_contract_echo` | `result.output_contract_echo` | F19 |
| 声明数字、实值为字符串 | ①类型提示 | 以**真实值**为准写入 | 顶层字段 | F20 |
| 容器字段空值 | ②容器 | `[]` 是合法值，**不得**被 `null`/`""` 替换 | 顶层字段 | F22 |
| 布尔开关无真实值 | ③布尔 | 写 `false`（真布尔，不写 0/字符串） | 顶层字段 | `check_contract` 判据 |
| 字段清单无真实值 | ④字段清单 | 写 `[]`；有值时回显实际图层名 | 顶层字段 + `audit.layer_naming.found` | F22 |
| 案例完全没有 `output_contract` | — | 信封 18 键仍须齐全 | 顶层 18 键 | F21 |

### 2.5 状态一致性

| 情形 | 处置 | 记录位点 | 实测用例 |
|-|-|-|-|
| 规格 lint 不过 | `status` 判 `partial`，**不做 success** | `result.spec_lint` + `uncertainty` | F10 |
| 方案 lint 不过 | 同上 | `result.plan.lint` | F07 / F09 / F11 |
| 渲染后端降级 | `status` 降 `partial` | `uncertainty` + `render_log` | F13–F15 |
| 存在缺值 / 实体缺失 / 越界 / 输入 notes | `status` 降 `partial` | `audit.*` + `warnings` | 题集 L3 |
| SVG 不良构 / PNG 无效 | `status=failed` + **exit 2**，已写出产物保留 | `audit.checks` + stderr | `_status()` 判据 |
| 方案覆盖决策未留痕 | 写入 `change_records` | `result.change_records` | F12 |
| 数值在画布上的文本形式与审计口径不一致 | 统一使用 `:g`（说明文字与其它通道一致） | `audit.encoding_consistency` | 题集 L2 实测（G6 门） |
| 重跑结构漂移 | 排查是否把时间戳/随机数带进图面 | `audit.determinism_probe.spec_sha16` | 三案两次一致 |

## 3. 失败模式 ↔ 规则号 ↔ 用例号 速查

| 规则 | 一句话 | 注入用例 / 实测来源 |
|-|-|-|
| D1 | `case.json` 缺失/不可解析 → exit 1 | F01 F02 |
| D2 | 缺 `case_id` → 回退链 | F03 |
| D3 | `task.md` 缺失 → 只用 case + 材料 | 规则表（无注入） |
| D4 | 材料路径缺失/为空 → 继续但记录 | F04 |
| D5 | 数值缺失 → 占位，不编造 | 题集 L3；F10/F12 语境 |
| D6 | 实体歧义 → 首见优先 + 并列 | 规则表（无注入） |
| D7 | 材料数值矛盾 → 首见优先 + 双 `src` | 题集 L3（0.14 / 0.19） |
| D8 | 非 UTF-8 → 替换字符 + 记录 | 材料预检新增项 |
| D9 | 二进制/PDF → 文本层或跳过 + 记录 | F05 F16 |
| D10 | 字体缺失 → 探测回退 + 记字体名 | F13–F15 语境 |
| D11 | 渲染后端缺失 → 三级回退 | F13 F14 F15 |
| D12 | PDF 不可用 → `present:false` + reason | 题集 L2/L3 |
| D13 | 文字溢出/越界 → 缩字号/夹紧 + 记录 | F10 语境 |
| D14 | 方案或规格 lint 不过 → 先修，修不动降 `partial` | F07 F09 F10 F11 |
| D15 | 契约无真实值 → `""`/`[]`/`false`/`{}`，禁 null | F18 |
| D16 | 契约键冲突 → `output_contract_echo` | F19 |
| D17 | 声明类型与实际不符 → 以真实值为准 + 说明 | F20 F06 |
| D18 | lint 不过仍想报成功 → 禁止 | F07 F09 F11 |
| D19 | 产物无效 → `status=failed` + exit 2 | F17（环境侧） |
| D20 | 重跑结构漂移 → 排查时间戳/随机数 | 三案确定性实测 |

## 4. 科学诚实性红线（优先于任何降级）

1. 材料里定位不到的数值**不得上画布**，只能进 `uncertainty` 并以「数值缺失」占位。
2. 两处数值矛盾**不取平均、不择优、不改写**，两处 `src` 并列交人判断。
3. 二进制 / 扫描件材料取不到文本时，**宁可少画也不编造**。
4. 任何降级都要留记录；**"静默成功"本身就是缺陷**（本包已修掉 8 处）。

## 5. 复现命令（全部在包外执行）

```bash
SKILL_DIR=/abs/path/to/graphical-abstract-7030fff2
PKG=$(mktemp -d) && cp -r "$SKILL_DIR" "$PKG" && cd "$PKG"

python scripts/main.py --case examples/case.json --out /tmp/o                     # exit 0 / 26 键
python scripts/check_contract.py --result /tmp/o/result.json --case examples/case.json   # exit 0
python scripts/fault_inject.py --out /tmp/fi --fail-on strict                      # exit 0 / 23 ok / 0 silent
python scripts/fault_inject.py --out /tmp/fi2 --only dependency                    # 单类复现
python scripts/fault_inject.py --out /tmp/fi3 --only F15 --verbose                  # 单条复现
python scripts/gain_harness.py --out /tmp/o --case examples/case.json --material examples/material.md
```

## 6. 表外情形怎么办（"先记后判"）

遇到规则表没列出的情形时：**先把观察写进 `uncertainty` / `warnings`，再判断是否可以继续。**
禁止"因为规则没写，所以静默忽略"。新增规则时必须在四处同步编号：`SKILL.md` §3、
本文件 §2/§3、`FAULT-MATRIX.md`（若可注入）、以及对应脚本的注释。
